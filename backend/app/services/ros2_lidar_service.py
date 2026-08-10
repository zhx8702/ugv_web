"""
ROS2 LiDAR Service

Subscribes to /scan (sensor_msgs/LaserScan) via rosbridge and
provides the same interface as LiDARService so the API layer
can swap transparently.
"""
import math
import threading
import logging
import cv2
import numpy as np
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class ROS2LiDARService:
    """
    LiDAR service backed by ROS2 /scan topic instead of direct serial.
    """

    def __init__(self, bridge):
        self.bridge = bridge

        # Data storage (same format as LiDARService)
        self.lidar_angles = []
        self.lidar_distances = []
        self.lidar_lock = threading.Lock()

        # Visualization config (same as LiDARService)
        self.overlay_enabled = False
        self.max_distance = 600  # cm
        self.point_color = (0, 255, 0)
        self.line_color = (0, 255, 255)

        self.running = False
        self._subscription = None

    def start(self):
        """Subscribe to /scan topic."""
        if self.running:
            return False

        self._subscription = self.bridge.subscribe(
            '/scan',
            'sensor_msgs/LaserScan',
            self._scan_callback,
            throttle_rate=100,  # max 10 Hz to frontend
        )

        if self._subscription is not None:
            self.running = True
            logger.info("ROS2 LiDAR started (subscribed to /scan)")
            return True

        logger.warning("Failed to subscribe to /scan")
        return False

    def stop(self):
        """Unsubscribe from /scan topic."""
        if not self.running:
            return False

        self.bridge.unsubscribe('/scan', 'sensor_msgs/LaserScan')
        self._subscription = None
        self.running = False
        logger.info("ROS2 LiDAR stopped")
        return True

    def _scan_callback(self, msg):
        """
        Convert LaserScan message to angles/distances arrays.

        LaserScan fields:
          angle_min, angle_max, angle_increment (radians)
          range_min, range_max (meters)
          ranges[] (meters)
        """
        try:
            angle_min = msg.get('angle_min', 0)
            angle_increment = msg.get('angle_increment', 0)
            range_min = msg.get('range_min', 0)
            range_max = msg.get('range_max', 0)
            ranges = msg.get('ranges', [])

            angles = []
            distances = []

            for i, r in enumerate(ranges):
                # Filter invalid readings
                if r < range_min or r > range_max or math.isinf(r) or math.isnan(r):
                    continue

                angle_deg = math.degrees(angle_min + i * angle_increment)
                distance_cm = r * 100.0  # meters → centimeters

                angles.append(angle_deg)
                distances.append(distance_cm)

            with self.lidar_lock:
                self.lidar_angles = angles
                self.lidar_distances = distances

        except Exception as e:
            logger.error(f"ROS2 LiDAR scan callback error: {e}")

    # ------------------------------------------------------------------
    # Same interface as LiDARService
    # ------------------------------------------------------------------

    def get_data(self) -> dict:
        with self.lidar_lock:
            return {
                'angles': self.lidar_angles.copy(),
                'distances': self.lidar_distances.copy(),
                'count': len(self.lidar_angles),
            }

    def enable_overlay(self, enabled: bool = True):
        self.overlay_enabled = enabled

    def overlay_on_frame(self, frame: np.ndarray) -> np.ndarray:
        """Draw LiDAR data on video frame (same as LiDARService)."""
        if not self.overlay_enabled:
            return frame

        height, width = frame.shape[:2]

        with self.lidar_lock:
            if not self.lidar_angles:
                return frame
            angles = self.lidar_angles.copy()
            distances = self.lidar_distances.copy()

        center_x = width // 2
        center_y = height - 50
        scale = min(width, height) / (2 * self.max_distance)

        for angle, distance in zip(angles, distances):
            if distance > self.max_distance:
                continue
            rad = math.radians(angle - 90)
            x = int(center_x + distance * scale * math.cos(rad))
            y = int(center_y - distance * scale * math.sin(rad))
            if 0 <= x < width and 0 <= y < height:
                cv2.circle(frame, (x, y), 3, self.point_color, -1)
                cv2.line(frame, (center_x, center_y), (x, y), self.line_color, 1)

        cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
        for dist in [100, 200, 300, 400, 500]:
            if dist <= self.max_distance:
                radius = int(dist * scale)
                cv2.circle(frame, (center_x, center_y), radius, (100, 100, 100), 1)

        cv2.putText(frame, f"LiDAR: {len(angles)} pts (ROS2)", (10, height - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return frame

    def get_status(self) -> dict:
        with self.lidar_lock:
            point_count = len(self.lidar_angles)
        return {
            'running': self.running,
            'overlay_enabled': self.overlay_enabled,
            'port': 'ros2:/scan',
            'baudrate': 0,
            'point_count': point_count,
            'connected': self.bridge.connected,
            'source': 'ros2',
        }

    def set_config(self, max_distance: Optional[int] = None,
                   point_color: Optional[Tuple[int, int, int]] = None,
                   line_color: Optional[Tuple[int, int, int]] = None):
        if max_distance is not None:
            self.max_distance = max_distance
        if point_color is not None:
            self.point_color = point_color
        if line_color is not None:
            self.line_color = line_color
