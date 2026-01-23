"""
AI Chat API 路由
处理前端的 AI 聊天请求
"""

import logging
from flask import Blueprint, request, jsonify
from flask_socketio import emit

from ..services.ai_chat_service import AIChatService, RobotCommandParser

logger = logging.getLogger(__name__)

ai_chat_bp = Blueprint('ai_chat', __name__, url_prefix='/api/ai')

# AI 服务实例（在应用初始化时配置）
ai_service: AIChatService = None


def init_ai_service(app_config: dict):
    """初始化 AI 服务"""
    global ai_service

    ai_config = app_config.get("ai_chat", {})

    if not ai_config.get("api_key"):
        logger.warning("AI Chat API Key 未配置，AI 功能将不可用")
        return

    ai_service = AIChatService(
        api_base_url=ai_config.get("api_base_url", ""),
        api_key=ai_config.get("api_key", ""),
        character=ai_config.get("character", "UGV_Assistant"),
        default_session=ai_config.get("default_session", "ugv-main"),
        enable_tts=ai_config.get("enable_tts", True),
        tts_voice=ai_config.get("tts_voice", "zh-CN-XiaoxiaoNeural")
    )

    logger.info(f"AI Chat 服务已初始化，角色: {ai_config.get('character')}")


@ai_chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    发送聊天消息

    请求体:
    {
        "message": "向前走一点",
        "session": "user-123",  // 可选
        "tts_mode": "auto"      // 可选: auto/always/never
    }
    """
    if not ai_service:
        return jsonify({
            "success": False,
            "error": "AI 服务未配置"
        }), 503

    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({
            "success": False,
            "error": "消息不能为空"
        }), 400

    try:
        response = ai_service.chat(
            message=message,
            session=data.get("session"),
            tts_mode=data.get("tts_mode", "auto")
        )

        # 构建响应
        result = {
            "success": True,
            "message": {
                "id": response.message_id,
                "content": response.content,
                "role": "assistant"
            },
            "session": {
                "name": response.session_name,
                "message_count": response.message_count
            },
            "commands": response.extracted_commands,
            "is_command_only": response.is_command_only
        }

        # 如果有 TTS 音频
        if response.tts_audio_base64:
            result["tts"] = {
                "audio_base64": response.tts_audio_base64,
                "format": response.tts_format
            }

        return jsonify(result)

    except Exception as e:
        logger.error(f"AI 聊天失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@ai_chat_bp.route('/sessions', methods=['GET'])
def get_sessions():
    """获取会话列表"""
    if not ai_service:
        return jsonify({"success": False, "error": "AI 服务未配置"}), 503

    # 注意：你的 API 可能需要调整这个端点
    return jsonify({
        "success": True,
        "sessions": []
    })


@ai_chat_bp.route('/sessions/<session_name>/history', methods=['GET'])
def get_session_history(session_name: str):
    """获取会话历史"""
    if not ai_service:
        return jsonify({"success": False, "error": "AI 服务未配置"}), 503

    limit = request.args.get("limit", 20, type=int)
    history = ai_service.get_session_history(session_name, limit)

    return jsonify({
        "success": True,
        "history": history
    })


@ai_chat_bp.route('/sessions/<session_name>', methods=['DELETE'])
def delete_session(session_name: str):
    """删除会话"""
    if not ai_service:
        return jsonify({"success": False, "error": "AI 服务未配置"}), 503

    success = ai_service.delete_session(session_name)

    return jsonify({
        "success": success
    })


@ai_chat_bp.route('/characters', methods=['GET'])
def get_characters():
    """获取可用角色列表"""
    if not ai_service:
        return jsonify({"success": False, "error": "AI 服务未配置"}), 503

    characters = ai_service.get_available_characters()

    return jsonify({
        "success": True,
        "characters": characters
    })


# WebSocket 事件处理（集成到现有的 SocketIO）
def register_ai_socket_events(socketio, base_controller=None):
    """注册 AI 相关的 WebSocket 事件"""

    @socketio.on('ai_chat')
    def handle_ai_chat(data):
        """
        处理 AI 聊天消息

        接收: { "message": "...", "session": "...", "tts_mode": "auto" }
        发送: { "type": "ai_response", "content": "...", "commands": [...], "tts": {...} }

        tts_mode:
          - "auto": 智能判断（命令不播报，对话播报）
          - "always": 总是播报
          - "never": 从不播报
        """
        if not ai_service:
            emit('ai_response', {
                "type": "error",
                "error": "AI 服务未配置"
            })
            return

        message = data.get("message", "").strip()
        if not message:
            emit('ai_response', {
                "type": "error",
                "error": "消息不能为空"
            })
            return

        try:
            response = ai_service.chat(
                message=message,
                session=data.get("session"),
                tts_mode=data.get("tts_mode", "auto")
            )

            # 发送 AI 回复
            result = {
                "type": "ai_response",
                "content": response.content,
                "message_id": response.message_id,
                "commands": response.extracted_commands,
                "is_command_only": response.is_command_only
            }

            if response.tts_audio_base64:
                result["tts"] = {
                    "audio_base64": response.tts_audio_base64,
                    "format": response.tts_format
                }

            emit('ai_response', result)

            # 如果有提取的命令，执行它们
            if response.extracted_commands and base_controller:
                for cmd in response.extracted_commands:
                    robot_cmd = RobotCommandParser.to_robot_format(cmd)
                    logger.info(f"执行机器人命令: {robot_cmd}")

                    # 发送命令到机器人
                    base_controller.send_command(robot_cmd)

                    # 通知前端命令已执行
                    emit('command_executed', {
                        "original": cmd,
                        "robot_format": robot_cmd
                    })

        except Exception as e:
            logger.error(f"AI 聊天处理失败: {e}")
            emit('ai_response', {
                "type": "error",
                "error": str(e)
            })

    @socketio.on('ai_stop')
    def handle_ai_stop(data):
        """紧急停止 - 立即停止机器人"""
        if base_controller:
            base_controller.send_command({"T": 1, "L": 0, "R": 0})
            emit('command_executed', {
                "original": {"type": "emergency_stop"},
                "robot_format": {"T": 1, "L": 0, "R": 0}
            })
