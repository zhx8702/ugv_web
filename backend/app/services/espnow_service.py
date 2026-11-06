"""
ESP-NOW Multi-Robot Collaboration Service
ESP-NOW多机协作服务
"""
import socket
import json
import threading
import time
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class RobotRole(Enum):
    """机器人角色"""
    STANDALONE = "standalone"  # 独立模式
    LEADER = "leader"          # 领导者
    FOLLOWER = "follower"      # 跟随者


class MessageType(Enum):
    """消息类型"""
    HEARTBEAT = "heartbeat"           # 心跳
    COMMAND = "command"               # 控制命令
    STATUS = "status"                 # 状态更新
    DISCOVERY = "discovery"           # 发现请求
    DISCOVERY_RESPONSE = "discovery_response"  # 发现响应
    FORMATION = "formation"           # 编队命令


@dataclass
class RobotInfo:
    """机器人信息"""
    mac: str                          # MAC地址
    name: str                         # 名称
    role: str                         # 角色
    ip: str                           # IP地址
    last_seen: float                  # 最后心跳时间
    battery: float = 11.4             # 电池电压
    status: str = "idle"              # 状态
    position: Dict[str, float] = None # 位置信息 {x, y, heading}

    def __post_init__(self):
        if self.position is None:
            self.position = {'x': 0.0, 'y': 0.0, 'heading': 0.0}


class ESPNowService:
    """
    ESP-NOW多机协作服务

    支持机器人群组发现、编队控制、状态同步
    """

    def __init__(self, port=8888, broadcast_port=8889):
        """
        初始化ESP-NOW服务

        Args:
            port: UDP通信端口
            broadcast_port: 广播发现端口
        """
        self.port = port
        self.broadcast_port = broadcast_port

        # 本机信息
        self.local_mac = self._get_mac_address()
        self.local_name = f"UGV-{self.local_mac[-8:].replace(':', '')}"
        self.role = RobotRole.STANDALONE

        # 网络
        self.socket = None
        self.broadcast_socket = None
        self.running = False

        # 机器人群组
        self.robots: Dict[str, RobotInfo] = {}
        self.robots_lock = threading.Lock()

        # 跟随者列表（仅领导者使用）
        self.followers: List[str] = []

        # 领导者信息（仅跟随者使用）
        self.leader_mac: Optional[str] = None

        # 编队配置
        self.formation_type = "line"  # line, triangle, square
        self.formation_spacing = 1.0  # 米

        # 消息回调
        self.message_handlers: Dict[str, Callable] = {}

        # 线程
        self.receive_thread = None
        self.heartbeat_thread = None
        self.cleanup_thread = None

        # 配置
        self.heartbeat_interval = 2.0  # 秒
        self.timeout = 10.0  # 秒（超时时间）

        logger.info(f"ESP-NOW Service initialized: {self.local_name} ({self.local_mac})")

    def start(self) -> bool:
        """启动服务"""
        if self.running:
            logger.warning("ESP-NOW service already running")
            return False

        try:
            # 创建UDP套接字
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.settimeout(1.0)

            # 创建广播套接字
            self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            self.running = True

            # 启动线程
            self.receive_thread = threading.Thread(target=self._receive_worker, daemon=True)
            self.receive_thread.start()

            self.heartbeat_thread = threading.Thread(target=self._heartbeat_worker, daemon=True)
            self.heartbeat_thread.start()

            self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
            self.cleanup_thread.start()

            logger.info("ESP-NOW service started")
            return True

        except Exception as e:
            logger.error(f"Failed to start ESP-NOW service: {e}")
            return False

    def stop(self) -> bool:
        """停止服务"""
        if not self.running:
            return False

        self.running = False

        # 等待线程结束
        if self.receive_thread:
            self.receive_thread.join(timeout=2)
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=2)

        # 关闭套接字
        if self.socket:
            self.socket.close()
        if self.broadcast_socket:
            self.broadcast_socket.close()

        logger.info("ESP-NOW service stopped")
        return True

    def _get_mac_address(self) -> str:
        """获取MAC地址"""
        try:
            import uuid
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                           for elements in range(0, 2*6, 2)][::-1])
            return mac.upper()
        except Exception:
            return "00:00:00:00:00:00"

    def _receive_worker(self):
        """接收消息工作线程"""
        logger.info("ESP-NOW receive worker started")

        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)
                message = json.loads(data.decode('utf-8'))
                self._handle_message(message, addr)

            except socket.timeout:
                continue
            except Exception as e:
                logger.debug(f"Receive error: {e}")

        logger.info("ESP-NOW receive worker stopped")

    def _handle_message(self, message: dict, addr: tuple):
        """处理接收到的消息"""
        try:
            msg_type = message.get('type')
            sender_mac = message.get('from')

            if not msg_type or not sender_mac:
                return

            # 更新机器人信息
            if msg_type in [MessageType.HEARTBEAT.value, MessageType.STATUS.value]:
                self._update_robot_info(message, addr[0])

            # 处理不同类型的消息
            if msg_type == MessageType.COMMAND.value:
                self._handle_command(message)
            elif msg_type == MessageType.DISCOVERY.value:
                self._handle_discovery(message, addr)
            elif msg_type == MessageType.DISCOVERY_RESPONSE.value:
                self._handle_discovery_response(message, addr[0])
            elif msg_type == MessageType.FORMATION.value:
                self._handle_formation(message)

            # 调用自定义回调
            if msg_type in self.message_handlers:
                self.message_handlers[msg_type](message, addr)

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def _update_robot_info(self, message: dict, ip: str):
        """更新机器人信息"""
        mac = message.get('from')
        if not mac or mac == self.local_mac:
            return

        with self.robots_lock:
            if mac not in self.robots:
                self.robots[mac] = RobotInfo(
                    mac=mac,
                    name=message.get('name', f'UGV-{mac[-8:]}'),
                    role=message.get('role', RobotRole.STANDALONE.value),
                    ip=ip,
                    last_seen=time.time()
                )
                logger.info(f"New robot discovered: {self.robots[mac].name} ({mac})")
            else:
                robot = self.robots[mac]
                robot.last_seen = time.time()
                robot.battery = message.get('battery', robot.battery)
                robot.status = message.get('status', robot.status)
                robot.role = message.get('role', robot.role)

                if 'position' in message:
                    robot.position = message['position']

    def _heartbeat_worker(self):
        """心跳发送工作线程"""
        logger.info("ESP-NOW heartbeat worker started")

        while self.running:
            try:
                self._send_heartbeat()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

        logger.info("ESP-NOW heartbeat worker stopped")

    def _send_heartbeat(self):
        """发送心跳消息"""
        message = {
            'type': MessageType.HEARTBEAT.value,
            'from': self.local_mac,
            'name': self.local_name,
            'role': self.role.value,
            'timestamp': time.time(),
            'battery': self._current_battery(),
            'status': 'idle'
        }

        # 广播心跳
        self._broadcast(message)

    def _cleanup_worker(self):
        """清理超时机器人工作线程"""
        logger.info("ESP-NOW cleanup worker started")

        while self.running:
            try:
                current_time = time.time()
                with self.robots_lock:
                    expired = [mac for mac, robot in self.robots.items()
                             if current_time - robot.last_seen > self.timeout]

                    for mac in expired:
                        robot = self.robots.pop(mac)
                        logger.info(f"Robot timeout: {robot.name} ({mac})")

                        # 如果是跟随者掉线
                        if mac in self.followers:
                            self.followers.remove(mac)

                        # 如果是领导者掉线
                        if mac == self.leader_mac:
                            logger.warning("Leader lost, switching to standalone mode")
                            self.leader_mac = None
                            self.role = RobotRole.STANDALONE

                time.sleep(5.0)

            except Exception as e:
                logger.error(f"Cleanup error: {e}")

        logger.info("ESP-NOW cleanup worker stopped")

    def _broadcast(self, message: dict):
        """广播消息"""
        try:
            data = json.dumps(message).encode('utf-8')
            self.broadcast_socket.sendto(data, ('<broadcast>', self.port))
        except Exception as e:
            logger.error(f"Broadcast error: {e}")

    def _send_to(self, mac: str, message: dict):
        """发送消息到指定机器人"""
        with self.robots_lock:
            if mac not in self.robots:
                logger.warning(f"Robot not found: {mac}")
                return False

            robot = self.robots[mac]

        try:
            data = json.dumps(message).encode('utf-8')
            self.socket.sendto(data, (robot.ip, self.port))
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False

    def discover(self):
        """发现其他机器人"""
        message = {
            'type': MessageType.DISCOVERY.value,
            'from': self.local_mac,
            'name': self.local_name,
            'timestamp': time.time()
        }
        self._broadcast(message)
        logger.info("Discovery message sent")

    def _handle_discovery(self, message: dict, addr: tuple):
        """处理发现请求"""
        response = {
            'type': MessageType.DISCOVERY_RESPONSE.value,
            'from': self.local_mac,
            'name': self.local_name,
            'role': self.role.value,
            'timestamp': time.time()
        }

        try:
            data = json.dumps(response).encode('utf-8')
            self.socket.sendto(data, (addr[0], self.port))
        except Exception as e:
            logger.error(f"Discovery response error: {e}")

    def _handle_discovery_response(self, message: dict, ip: str):
        """处理发现响应"""
        self._update_robot_info(message, ip)

    def set_role(self, role: str) -> bool:
        """设置角色"""
        try:
            self.role = RobotRole(role)
            logger.info(f"Role changed to: {role}")

            if role == RobotRole.LEADER.value:
                self.followers.clear()
            elif role == RobotRole.FOLLOWER.value:
                self.leader_mac = None

            return True
        except ValueError:
            logger.error(f"Invalid role: {role}")
            return False

    def broadcast_command(self, command: dict) -> bool:
        """广播控制命令（领导者使用）"""
        if self.role != RobotRole.LEADER:
            logger.warning("Only leader can broadcast commands")
            return False

        message = {
            'type': MessageType.COMMAND.value,
            'from': self.local_mac,
            'command': command,
            'timestamp': time.time()
        }

        self._broadcast(message)
        return True

    def _handle_command(self, message: dict):
        """处理接收到的命令（跟随者）"""
        if self.role != RobotRole.FOLLOWER:
            return

        sender_mac = message.get('from')

        # 只接受领导者的命令
        if self.leader_mac and sender_mac != self.leader_mac:
            return

        # 如果还没有领导者，设置领导者
        if not self.leader_mac:
            self.leader_mac = sender_mac
            logger.info(f"Following leader: {sender_mac}")

        command = message.get('command', {})
        logger.info(f"Received command from leader: {command}")
        self._execute_leader_command(command)

    def _current_battery(self):
        """Read chassis voltage in volts, or 0 when unknown."""
        try:
            from app.services.base_controller import get_base_controller
            feedback = get_base_controller().feedback_data()
            raw = feedback.get('v') if feedback else 0
            if isinstance(raw, (int, float)) and raw > 0:
                return round(raw / 100.0, 2)
        except Exception as e:
            logger.debug(f"Battery read failed: {e}")
        return 0

    def _execute_leader_command(self, command):
        if not isinstance(command, dict):
            logger.warning("Leader command is not an object")
            return
        cmd_type = command.get('T')
        if not isinstance(cmd_type, int) or cmd_type < 0 or cmd_type > 600:
            logger.warning(f"Rejected leader command type: {cmd_type}")
            return
        try:
            from app.services.base_controller import get_base_controller
            get_base_controller().base_json_ctrl(command)
        except Exception as e:
            logger.error(f"Failed to execute leader command: {e}")

    def set_formation(self, formation_type: str, spacing: float = 1.0) -> bool:
        """设置编队类型"""
        valid_formations = ['line', 'triangle', 'square', 'circle']

        if formation_type not in valid_formations:
            logger.error(f"Invalid formation: {formation_type}")
            return False

        self.formation_type = formation_type
        self.formation_spacing = spacing

        logger.info(f"Formation set: {formation_type} (spacing: {spacing}m)")
        return True

    def _handle_formation(self, message: dict):
        """处理编队命令"""
        formation_type = message.get('formation_type')
        spacing = message.get('spacing', 1.0)

        self.set_formation(formation_type, spacing)

    def get_robots(self) -> List[dict]:
        """获取所有机器人信息"""
        with self.robots_lock:
            return [asdict(robot) for robot in self.robots.values()]

    def get_status(self) -> dict:
        """获取服务状态"""
        with self.robots_lock:
            robot_count = len(self.robots)
            follower_count = len(self.followers)

        return {
            'running': self.running,
            'local_mac': self.local_mac,
            'local_name': self.local_name,
            'role': self.role.value,
            'robot_count': robot_count,
            'follower_count': follower_count,
            'leader_mac': self.leader_mac,
            'formation_type': self.formation_type,
            'formation_spacing': self.formation_spacing
        }

    def register_handler(self, message_type: str, handler: Callable):
        """注册消息处理回调"""
        self.message_handlers[message_type] = handler


# 全局实例
_espnow_service_instance: Optional[ESPNowService] = None


def get_espnow_service(port=8888, broadcast_port=8889) -> ESPNowService:
    """
    获取ESP-NOW服务单例

    Args:
        port: UDP通信端口
        broadcast_port: 广播发现端口

    Returns:
        ESPNowService实例
    """
    global _espnow_service_instance
    if _espnow_service_instance is None:
        _espnow_service_instance = ESPNowService(port, broadcast_port)
    return _espnow_service_instance
