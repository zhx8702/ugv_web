"""
LiDAR Service
处理LiDAR数据读取和可视化
"""
import serial
import threading
import time
import logging
import math
import cv2
import numpy as np
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class LiDARService:
    """
    LiDAR数据处理服务

    从串口读取LiDAR数据并提供可视化功能
    """

    def __init__(self, port='/dev/ttyACM0', baudrate=230400):
        """
        初始化LiDAR服务

        Args:
            port: 串口设备路径
            baudrate: 波特率
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = False
        self.enabled = False

        # LiDAR数据存储
        self.lidar_angles = []  # 角度列表
        self.lidar_distances = []  # 距离列表（厘米）
        self.lidar_lock = threading.Lock()

        # 可视化配置
        self.overlay_enabled = False
        self.max_distance = 600  # 最大显示距离（厘米）
        self.point_color = (0, 255, 0)  # 绿色点
        self.line_color = (0, 255, 255)  # 黄色线

        # 读取线程
        self.read_thread = None

        logger.info(f"LiDAR Service initialized (port: {port})")

    def start(self):
        """启动LiDAR读取"""
        if self.running:
            logger.warning("LiDAR already running")
            return False

        try:
            # 打开串口
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )

            self.running = True
            self.read_thread = threading.Thread(target=self._read_worker, daemon=True)
            self.read_thread.start()

            logger.info("LiDAR started")
            return True

        except serial.SerialException as e:
            logger.error(f"Failed to open LiDAR port: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to start LiDAR: {e}")
            return False

    def stop(self):
        """停止LiDAR读取"""
        if not self.running:
            return False

        self.running = False

        if self.read_thread:
            self.read_thread.join(timeout=2)

        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

        logger.info("LiDAR stopped")
        return True

    def _read_worker(self):
        """LiDAR数据读取工作线程"""
        logger.info("LiDAR read worker started")

        while self.running:
            try:
                if not self.serial_conn or not self.serial_conn.is_open:
                    break

                # 读取一行数据
                line = self.serial_conn.readline()

                if not line:
                    continue

                # 解析数据
                try:
                    decoded = line.decode('utf-8').strip()
                    self._parse_lidar_line(decoded)
                except UnicodeDecodeError:
                    continue

            except Exception as e:
                logger.error(f"LiDAR read error: {e}")
                time.sleep(0.1)

        logger.info("LiDAR read worker stopped")

    def _parse_lidar_line(self, line: str):
        """
        解析LiDAR数据行

        格式: "angle1:distance1,angle2:distance2,..."
        例如: "0:150,15:200,30:180"

        Args:
            line: 数据行字符串
        """
        try:
            angles = []
            distances = []

            # 分割数据点
            points = line.split(',')

            for point in points:
                if ':' not in point:
                    continue

                angle_str, distance_str = point.split(':')
                angle = float(angle_str)
                distance = float(distance_str)

                # 过滤无效数据
                if 0 <= angle <= 360 and 0 < distance < 1000:
                    angles.append(angle)
                    distances.append(distance)

            # 更新数据
            if angles and distances:
                with self.lidar_lock:
                    self.lidar_angles = angles
                    self.lidar_distances = distances

        except Exception as e:
            logger.debug(f"Failed to parse LiDAR line: {e}")

    def get_data(self) -> dict:
        """
        获取当前LiDAR数据

        Returns:
            dict: {'angles': List[float], 'distances': List[float], 'count': int}
        """
        with self.lidar_lock:
            return {
                'angles': self.lidar_angles.copy(),
                'distances': self.lidar_distances.copy(),
                'count': len(self.lidar_angles)
            }

    def enable_overlay(self, enabled: bool = True):
        """启用/禁用视频叠加"""
        self.overlay_enabled = enabled
        logger.info(f"LiDAR overlay {'enabled' if enabled else 'disabled'}")

    def overlay_on_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        在视频帧上叠加LiDAR数据

        Args:
            frame: OpenCV图像帧

        Returns:
            叠加了LiDAR数据的帧
        """
        if not self.overlay_enabled:
            return frame

        height, width = frame.shape[:2]

        # 获取LiDAR数据
        with self.lidar_lock:
            if not self.lidar_angles or not self.lidar_distances:
                return frame

            angles = self.lidar_angles.copy()
            distances = self.lidar_distances.copy()

        # 计算中心点（底部中心）
        center_x = width // 2
        center_y = height - 50

        # 计算缩放比例
        scale = min(width, height) / (2 * self.max_distance)

        # 绘制LiDAR数据
        for angle, distance in zip(angles, distances):
            if distance > self.max_distance:
                continue

            # 转换极坐标到笛卡尔坐标
            # 角度0度为前方，逆时针旋转
            rad = math.radians(angle - 90)  # 转换为标准坐标系
            x = int(center_x + distance * scale * math.cos(rad))
            y = int(center_y - distance * scale * math.sin(rad))

            # 确保点在图像范围内
            if 0 <= x < width and 0 <= y < height:
                # 绘制点
                cv2.circle(frame, (x, y), 3, self.point_color, -1)

                # 绘制从中心到点的线
                cv2.line(frame, (center_x, center_y), (x, y), self.line_color, 1)

        # 绘制中心点
        cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

        # 绘制距离圈（100cm, 200cm, 300cm等）
        for dist in [100, 200, 300, 400, 500]:
            if dist <= self.max_distance:
                radius = int(dist * scale)
                cv2.circle(frame, (center_x, center_y), radius, (100, 100, 100), 1)

        # 显示数据点数量
        cv2.putText(frame, f"LiDAR: {len(angles)} points", (10, height - 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return frame

    def get_status(self) -> dict:
        """
        获取LiDAR状态

        Returns:
            dict: 状态信息
        """
        with self.lidar_lock:
            point_count = len(self.lidar_angles)

        return {
            'running': self.running,
            'overlay_enabled': self.overlay_enabled,
            'port': self.port,
            'baudrate': self.baudrate,
            'point_count': point_count,
            'connected': self.serial_conn is not None and self.serial_conn.is_open if self.serial_conn else False
        }

    def set_config(self, max_distance: Optional[int] = None,
                   point_color: Optional[Tuple[int, int, int]] = None,
                   line_color: Optional[Tuple[int, int, int]] = None):
        """
        设置可视化配置

        Args:
            max_distance: 最大显示距离（厘米）
            point_color: 点的颜色 (B, G, R)
            line_color: 线的颜色 (B, G, R)
        """
        if max_distance is not None:
            self.max_distance = max_distance
        if point_color is not None:
            self.point_color = point_color
        if line_color is not None:
            self.line_color = line_color

        logger.info(f"LiDAR config updated: max_dist={self.max_distance}")


# 全局实例
_lidar_service_instance: Optional[LiDARService] = None


def get_lidar_service(port='/dev/ttyACM0', baudrate=230400) -> LiDARService:
    """
    获取LiDAR服务单例

    Args:
        port: 串口设备路径
        baudrate: 波特率

    Returns:
        LiDARService实例
    """
    global _lidar_service_instance
    if _lidar_service_instance is None:
        _lidar_service_instance = LiDARService(port, baudrate)

        # 自动集成到video_stream
        try:
            from app.services.video_stream import get_video_stream
            video_stream = get_video_stream()
            video_stream.set_lidar_service(_lidar_service_instance)
            logger.info("LiDAR service integrated with video stream")
        except Exception as e:
            logger.warning(f"Could not integrate LiDAR with video stream: {e}")

    return _lidar_service_instance
