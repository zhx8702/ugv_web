"""
AI Chat Service - 集成外部角色扮演聊天 API
用于实现机器人的自然语言交互控制
"""

import re
import json
import logging
import requests
from typing import Optional, Dict, Any, Generator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChatResponse:
    """聊天响应数据结构"""
    content: str
    message_id: str
    session_name: str
    message_count: int
    tts_audio_base64: Optional[str] = None
    tts_format: str = "mp3"
    extracted_commands: list = None
    is_command_only: bool = False  # 是否只是命令（无需 TTS）

    def __post_init__(self):
        if self.extracted_commands is None:
            self.extracted_commands = []


class RobotCommandParser:
    """从 AI 回复中提取和验证机器人命令"""

    # 支持的命令类型及其参数验证
    VALID_COMMANDS = {
        # 运动控制
        "move": {"params": ["L", "R"], "description": "差速驱动"},
        "drive_on_heading": {"params": ["data"], "description": "前进"},
        "back_up": {"params": ["data"], "description": "后退"},
        "spin": {"params": ["data"], "description": "旋转"},
        "stop": {"params": [], "description": "停止"},

        # 云台控制
        "pan_tilt": {"params": ["pan", "tilt"], "description": "云台控制"},
        "look_at": {"params": ["direction"], "description": "看向方向"},

        # 灯光控制
        "light": {"params": ["mode"], "description": "灯光控制"},
        "headlight": {"params": ["brightness"], "description": "头灯"},

        # 视觉功能
        "detect": {"params": ["mode"], "description": "检测模式"},
        "take_photo": {"params": [], "description": "拍照"},
        "record_video": {"params": ["action"], "description": "录像"},

        # 音频
        "speak": {"params": ["text"], "description": "语音播报"},
        "play_sound": {"params": ["sound"], "description": "播放音效"},
    }

    # 命令提取的正则模式
    PATTERNS = [
        r"```json\s*(.*?)\s*```",           # Markdown JSON 代码块
        r"```\s*({\s*.*?\s*})\s*```",        # 普通代码块中的 JSON
        r"\[COMMAND\](.*?)\[/COMMAND\]",     # 自定义标记
        r"<command>(.*?)</command>",         # XML 风格标记
    ]

    @classmethod
    def extract_commands(cls, ai_response: str) -> list[Dict[str, Any]]:
        """从 AI 回复中提取命令"""
        commands = []

        for pattern in cls.PATTERNS:
            matches = re.findall(pattern, ai_response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    cmd = json.loads(match.strip())
                    if cls.validate_command(cmd):
                        commands.append(cmd)
                except json.JSONDecodeError:
                    logger.warning(f"无法解析命令 JSON: {match[:100]}")
                    continue

        return commands

    @classmethod
    def validate_command(cls, cmd: Dict[str, Any]) -> bool:
        """验证命令是否合法"""
        if not isinstance(cmd, dict):
            return False

        cmd_type = cmd.get("type") or cmd.get("T")
        if not cmd_type:
            return False

        # 安全检查：限制数值范围
        if "data" in cmd:
            data = cmd["data"]
            if isinstance(data, (int, float)):
                if abs(data) > 100:  # 限制最大值
                    logger.warning(f"命令数值超出范围: {data}")
                    return False

        return True

    @classmethod
    def is_command_response(cls, content: str, commands: list) -> bool:
        """
        判断回复是否主要是命令执行（不需要 TTS）

        规则：
        - 如果有命令，且纯文字部分很短（< 50字），认为是命令响应
        - 如果没有命令，则是对话，需要 TTS
        """
        if not commands:
            return False  # 没有命令 = 纯对话，需要 TTS

        # 移除代码块后的纯文字
        text_only = content
        for pattern in cls.PATTERNS:
            text_only = re.sub(pattern, '', text_only, flags=re.DOTALL | re.IGNORECASE)

        # 清理空白字符
        text_only = text_only.strip()

        # 短回复 + 有命令 = 命令响应，不需要 TTS
        return len(text_only) < 50

    @classmethod
    def to_robot_format(cls, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """将命令转换为机器人可执行的格式"""
        cmd_type = cmd.get("type", "")

        # 映射到 base_ctrl 的命令格式
        if cmd_type == "drive_on_heading":
            distance = cmd.get("data", 1)
            return {"T": 1, "L": 0.5, "R": 0.5, "duration": distance}

        elif cmd_type == "back_up":
            distance = cmd.get("data", 1)
            return {"T": 1, "L": -0.5, "R": -0.5, "duration": distance}

        elif cmd_type == "spin":
            angle = cmd.get("data", 0)
            direction = 1 if angle > 0 else -1
            return {"T": 1, "L": 0.3 * direction, "R": -0.3 * direction, "duration": abs(angle) / 30}

        elif cmd_type == "stop":
            return {"T": 1, "L": 0, "R": 0}

        elif cmd_type == "pan_tilt":
            # 云台控制: X=水平角度, Y=垂直角度, SPD=速度, ACC=加速度
            return {"T": 133, "X": cmd.get("pan", 0), "Y": cmd.get("tilt", 0), "SPD": 200, "ACC": 10}

        elif cmd_type == "light":
            # 灯光控制: T=132, IO4=底盘灯PWM, IO5=头灯PWM (0-255)
            mode = cmd.get("mode", 0)
            pwm = 255 if mode > 0 else 0
            return {"T": 132, "IO4": pwm, "IO5": pwm}

        elif cmd_type == "take_photo":
            return {"T": "photo"}

        # 默认直接返回
        return cmd


class AIChatService:
    """AI 聊天服务 - 与外部 API 交互"""

    def __init__(
        self,
        api_base_url: str,
        api_key: str,
        character: str = "UGV_Assistant",
        default_session: str = "ugv-main",
        enable_tts: bool = True,
        tts_voice: str = "zh-CN-XiaoxiaoNeural"
    ):
        self.api_base_url = api_base_url.rstrip("/")
        self.api_key = api_key
        self.character = character
        self.default_session = default_session
        self.enable_tts = enable_tts
        self.tts_voice = tts_voice

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 系统提示词 - 教会 AI 如何生成机器人命令
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一个智能机器人助手，可以理解用户的自然语言指令并控制机器人执行动作。

当用户发出移动、控制等指令时，你需要：
1. 理解用户意图
2. 用自然语言回复用户
3. 在回复末尾添加 JSON 格式的机器人命令

命令格式（放在 ```json ``` 代码块中）:
- 前进: {"T": 1, "type": "drive_on_heading", "data": 距离}
- 后退: {"T": 1, "type": "back_up", "data": 距离}
- 左转: {"T": 1, "type": "spin", "data": -角度}
- 右转: {"T": 1, "type": "spin", "data": 角度}
- 停止: {"T": 1, "type": "stop", "data": 0}
- 云台: {"T": 133, "type": "pan_tilt", "pan": 水平角度(-180~180), "tilt": 垂直角度(-30~90)}
- 拍照: {"T": "photo", "type": "take_photo"}
- 灯光: {"T": 132, "type": "light", "mode": 0关/1开}

示例回复:
用户: "向前走一点"
你: "好的，我来控制机器人向前移动一段距离。
```json
{"T": 1, "type": "drive_on_heading", "data": 2}
```"

注意：
- 距离单位大约是 0.5 米
- 角度单位是度数
- 如果用户只是闲聊，正常回复即可，不需要添加命令
- 保持回复简洁友好
"""

    def chat(
        self,
        message: str,
        session: Optional[str] = None,
        include_tts: Optional[bool] = None,
        tts_mode: str = "auto"
    ) -> ChatResponse:
        """
        发送聊天消息并获取回复

        Args:
            message: 用户消息
            session: 会话名称（可选）
            include_tts: 是否包含语音（可选，兼容旧参数）
            tts_mode: TTS 模式
                - "auto": 智能判断（命令不播报，对话播报）
                - "always": 总是播报
                - "never": 从不播报

        Returns:
            ChatResponse 对象
        """
        session = session or self.default_session

        # TTS 模式处理
        if include_tts is not None:
            # 兼容旧参数
            request_tts = include_tts
        elif tts_mode == "never":
            request_tts = False
        else:
            # auto 或 always 模式都先请求 TTS
            request_tts = self.enable_tts

        # 构建请求
        payload = {
            "character": self.character,
            "message": message,
            "session": session,
            "include_tts": request_tts,
        }

        if request_tts:
            payload["tts_provider"] = "edge"
            payload["tts_voice"] = self.tts_voice

        try:
            response = requests.post(
                f"{self.api_base_url}/api/external/v1/chat",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise Exception(f"API 返回失败: {data}")

            # 解析响应
            msg = data.get("message", {})
            sess = data.get("session", {})
            tts = data.get("tts", {})

            content = msg.get("content", "")

            # 提取机器人命令
            commands = RobotCommandParser.extract_commands(content)

            # 判断是否是纯命令响应
            is_command_only = RobotCommandParser.is_command_response(content, commands)

            # 根据 tts_mode 决定是否返回 TTS
            should_return_tts = False
            if tts_mode == "always":
                should_return_tts = request_tts
            elif tts_mode == "auto":
                # 自动模式：命令响应不返回 TTS，对话返回 TTS
                should_return_tts = request_tts and not is_command_only
            # never 模式不返回 TTS

            return ChatResponse(
                content=content,
                message_id=msg.get("id", ""),
                session_name=sess.get("name", session),
                message_count=sess.get("message_count", 0),
                tts_audio_base64=tts.get("audio_base64") if should_return_tts else None,
                tts_format=tts.get("format", "mp3"),
                extracted_commands=commands,
                is_command_only=is_command_only
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"API 请求失败: {e}")
            raise

    def chat_stream(
        self,
        message: str,
        session: Optional[str] = None
    ) -> Generator[str, None, ChatResponse]:
        """
        流式聊天（如果 API 支持）

        注意：根据你的 API 文档，似乎不支持流式响应
        这里提供一个模拟实现，实际使用时直接调用 chat() 即可
        """
        # 你的 API 不支持流式，直接调用普通接口
        response = self.chat(message, session, include_tts=False)

        # 模拟流式输出
        for char in response.content:
            yield char

        return response

    def get_session_history(
        self,
        session: str,
        limit: int = 20
    ) -> list[Dict[str, Any]]:
        """获取会话历史"""
        try:
            response = requests.get(
                f"{self.api_base_url}/api/external/v1/sessions/{session}/history",
                headers=self.headers,
                params={"character": self.character, "limit": limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"获取会话历史失败: {e}")
            return []

    def delete_session(self, session: str) -> bool:
        """删除会话"""
        try:
            response = requests.delete(
                f"{self.api_base_url}/api/external/v1/sessions/{session}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"删除会话失败: {e}")
            return False

    def get_available_characters(self) -> list[Dict[str, Any]]:
        """获取可用角色列表"""
        try:
            response = requests.get(
                f"{self.api_base_url}/api/external/v1/characters",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"获取角色列表失败: {e}")
            return []


# 使用示例
if __name__ == "__main__":
    # 初始化服务
    ai_service = AIChatService(
        api_base_url="https://your-server.com",
        api_key="sk-ext-xxxxx",
        character="UGV_Assistant",
        enable_tts=True
    )

    # 发送消息
    response = ai_service.chat("向前走两步")

    print(f"AI 回复: {response.content}")
    print(f"提取的命令: {response.extracted_commands}")

    if response.tts_audio_base64:
        print(f"收到语音数据，格式: {response.tts_format}")
