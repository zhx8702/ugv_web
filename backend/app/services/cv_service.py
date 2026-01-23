# -*- coding: utf-8 -*-
"""
CV Vision Service
计算机视觉服务 - 支持多种检测模式和云台追踪
基于原ugv_rpi/cv_ctrl.py重构
"""
import cv2
import numpy as np
import threading
import logging
import math
import time
from collections import deque
from pathlib import Path

logger = logging.getLogger(__name__)


class CVService:
    """
    计算机视觉服务
    支持8种检测模式和云台追踪
    """

    # CV模式常量
    CV_NONE = 10301
    CV_MOTION = 10302
    CV_FACE = 10303
    CV_OBJECTS = 10304
    CV_COLOR = 10305
    MP_HAND = 10306
    CV_AUTO = 10307
    MP_FACE = 10308
    MP_POSE = 10309

    # 反应模式
    RE_NONE = 10401
    RE_CAPTURE = 10402
    RE_RECORD = 10403

    def __init__(self, config=None):
        """
        初始化CV服务

        Args:
            config: 配置字典，包含:
                - models_path: 模型文件路径
                - track_spd_rate: 追踪速度系数
                - track_acc_rate: 追踪加速度系数
                - aimed_error: 追踪目标误差阈值
                - mock_mode: Mock模式
        """
        self.config = config or {}
        self.mock_mode = self.config.get('mock_mode', False)

        # 当前模式
        self.cv_mode = self.CV_NONE
        self.reaction_mode = self.RE_NONE
        self.motion_lock = True  # True=锁定，不追踪

        # 云台角度
        self.pan_angle = 0
        self.tilt_angle = 0

        # 追踪参数
        self.track_spd_rate = self.config.get('track_spd_rate', 60)
        self.track_acc_rate = self.config.get('track_acc_rate', 0.4)
        self.aimed_error = self.config.get('aimed_error', 8)
        self.track_faces_iterate = self.config.get('track_faces_iterate', 0.045)
        self.track_color_iterate = self.config.get('track_color_iterate', 0.023)

        # 颜色检测参数
        self.color_lower = np.array([90, 160, 150])
        self.color_upper = np.array([105, 255, 255])
        self.min_radius = 12
        self.sampling_rad = 25
        self.color_points = deque(maxlen=32)

        # 巡线参数
        self.line_lower = np.array([25, 150, 70])
        self.line_upper = np.array([42, 255, 255])
        self.sampling_line_1 = 0.6
        self.sampling_line_2 = 0.9
        self.slope_impact = 1.5
        self.base_impact = 0.005
        self.line_track_speed = 0.3
        self.slope_on_speed = 0.1

        # 运动检测
        self.motion_avg = None

        # 叠加层
        self.overlay = None

        # 检测结果存储
        self.detections = []
        self.detection_count = 0
        self.detections_lock = threading.Lock()

        # 线程事件
        self.cv_event = threading.Event()
        self.cv_event.clear()

        # 外部控制器引用
        self.motor_controller = None
        self.video_stream = None

        # 模型路径
        models_path = Path(self.config.get('models_path', './models'))

        # 初始化检测器
        self._init_detectors(models_path)

        logger.info(f'CVService initialized (mock_mode={self.mock_mode})')

    def _init_detectors(self, models_path):
        """初始化各种检测器"""
        # 人脸检测 - Haar级联
        haar_path = models_path / 'haarcascade_frontalface_default.xml'
        if haar_path.exists():
            self.face_cascade = cv2.CascadeClassifier(str(haar_path))
            logger.info('Face cascade classifier loaded')
        else:
            self.face_cascade = None
            logger.warning(f'Face cascade not found: {haar_path}')

        # 物体检测 - MobileNet SSD
        prototxt_path = models_path / 'deploy.prototxt'
        caffemodel_path = models_path / 'mobilenet_iter_73000.caffemodel'
        if prototxt_path.exists() and caffemodel_path.exists():
            self.object_net = cv2.dnn.readNetFromCaffe(
                str(prototxt_path), str(caffemodel_path)
            )
            self.object_classes = [
                "background", "aeroplane", "bicycle", "bird", "boat",
                "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                "sofa", "train", "tvmonitor"
            ]
            logger.info('Object detection network loaded')
        else:
            self.object_net = None
            self.object_classes = []
            logger.warning('Object detection model not found')

        # MediaPipe 检测器
        self._init_mediapipe()

    def _init_mediapipe(self):
        """初始化MediaPipe检测器"""
        self.mp = None
        self.mp_draw = None
        self.mp_hands = None
        self.hands = None
        self.mp_face_detection = None
        self.face_detection = None
        self.mp_pose = None
        self.pose = None

        try:
            import mediapipe as mp

            # Check if solutions module exists (may not in some versions)
            if not hasattr(mp, 'solutions'):
                logger.warning('MediaPipe solutions module not available')
                return

            self.mp = mp
            self.mp_draw = mp.solutions.drawing_utils

            # Hand detection
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(max_num_hands=1)

            # Face detection
            self.mp_face_detection = mp.solutions.face_detection
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=0, min_detection_confidence=0.5
            )

            # Pose detection
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )

            logger.info('MediaPipe detectors initialized')
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f'MediaPipe not available: {e}')

    def set_motor_controller(self, controller):
        """设置电机控制器引用（用于云台追踪）"""
        self.motor_controller = controller

    def set_video_stream(self, stream):
        """设置视频流引用（用于拍照/录像反应）"""
        self.video_stream = stream

    def set_mode(self, mode: int):
        """设置CV模式"""
        if mode in [self.CV_NONE, self.CV_MOTION, self.CV_FACE, self.CV_OBJECTS,
                    self.CV_COLOR, self.MP_HAND, self.CV_AUTO, self.MP_FACE, self.MP_POSE]:
            self.cv_mode = mode
            self.overlay = None
            self.motion_avg = None
            # 切换模式时清除检测结果
            self.clear_detections()
            logger.info(f'CV mode set to {mode}')
        else:
            logger.warning(f'Invalid CV mode: {mode}')

    def set_reaction_mode(self, mode: int):
        """设置检测反应模式"""
        self.reaction_mode = mode
        logger.info(f'Reaction mode set to {mode}')

    def set_motion_lock(self, locked: bool):
        """设置运动锁定（追踪开关）"""
        self.motion_lock = locked
        if not locked:
            self.pan_angle = 0
            self.tilt_angle = 0
        logger.info(f'Motion lock set to {locked}')

    def set_color_range(self, lower: list, upper: list):
        """设置颜色检测范围"""
        self.color_lower = np.array(lower)
        self.color_upper = np.array(upper)
        logger.info(f'Color range set: {lower} - {upper}')

    def set_line_color(self, lower: list, upper: list):
        """设置巡线颜色范围"""
        self.line_lower = np.array(lower)
        self.line_upper = np.array(upper)
        logger.info(f'Line color set: {lower} - {upper}')

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        处理视频帧

        Args:
            frame: BGR格式的视频帧

        Returns:
            处理后的帧（带检测叠加）
        """
        if self.cv_mode == self.CV_NONE:
            return frame

        # 异步处理CV检测
        if not self.cv_event.is_set():
            self.cv_event.set()
            self._process_cv_async(frame.copy())

        # 叠加检测结果
        if self.overlay is not None:
            try:
                mask = self.overlay.astype(bool)
                frame[mask] = self.overlay[mask]
            except Exception as e:
                logger.error(f'Error applying overlay: {e}')

        return frame

    def _process_cv_async(self, frame: np.ndarray):
        """异步处理CV检测"""
        def process():
            try:
                mode_handlers = {
                    self.CV_MOTION: self._detect_motion,
                    self.CV_FACE: self._detect_faces,
                    self.CV_OBJECTS: self._detect_objects,
                    self.CV_COLOR: self._detect_color,
                    self.MP_HAND: self._detect_hand,
                    self.CV_AUTO: self._auto_drive,
                    self.MP_FACE: self._mediapipe_faces,
                    self.MP_POSE: self._mediapipe_pose,
                }
                handler = mode_handlers.get(self.cv_mode)
                if handler:
                    handler(frame)
            except Exception as e:
                logger.error(f'CV processing error: {e}')
            finally:
                self.cv_event.clear()

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    def gimbal_track(self, frame_x: float, frame_y: float,
                     target_x: float, target_y: float, iterate: float) -> float:
        """
        云台追踪

        Args:
            frame_x, frame_y: 画面中心坐标
            target_x, target_y: 目标坐标
            iterate: 迭代步长

        Returns:
            目标距离
        """
        distance = math.sqrt((frame_x - target_x) ** 2 + (target_y - frame_y) ** 2)

        self.pan_angle += (target_x - frame_x) * iterate
        self.tilt_angle += (frame_y - target_y) * iterate

        # 限制角度范围
        self.pan_angle = max(-180, min(180, self.pan_angle))
        self.tilt_angle = max(-30, min(90, self.tilt_angle))

        # 计算速度和加速度
        gimbal_spd = max(1, int(distance * self.track_spd_rate))
        gimbal_acc = max(1, int(distance * self.track_acc_rate))

        # 发送云台控制命令
        if self.motor_controller and not self.motion_lock:
            self.motor_controller.send_json_command({
                "T": 133,
                "X": self.pan_angle,
                "Y": self.tilt_angle,
                "SPD": gimbal_spd,
                "ACC": gimbal_acc
            })

        return distance

    # ============ 检测方法 ============

    def _detect_motion(self, frame: np.ndarray):
        """运动检测"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.motion_avg is None:
            self.motion_avg = gray.copy().astype("float")
            return

        cv2.accumulateWeighted(gray, self.motion_avg, 0.5)
        frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(self.motion_avg))

        thresh = cv2.threshold(frame_delta, 5, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        overlay = np.zeros_like(frame)
        # 构建检测结果
        detection_results = []
        motion_idx = 0
        for c in contours:
            area = cv2.contourArea(c)
            if area < 2000:
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(overlay, (x, y), (x + w, y + h), (128, 255, 0), 2)
            # 添加到检测结果
            detection_results.append({
                'id': f'motion_{motion_idx}',
                'label': 'Motion',
                'confidence': min(100, int(area / 100)),  # 根据面积估算置信度
                'bbox': [int(x), int(y), int(w), int(h)]
            })
            motion_idx += 1

        # 更新检测结果（线程安全）
        with self.detections_lock:
            self.detections = detection_results
            self.detection_count = len(detection_results)

        self.overlay = overlay

    def _detect_faces(self, frame: np.ndarray):
        """人脸检测（Haar级联）"""
        if self.face_cascade is None:
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=5, minSize=(20, 20)
        )

        overlay = np.zeros_like(frame)
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2

        max_area = 0
        max_face_center = (0, 0)

        # 构建检测结果
        detections = []
        for i, (x, y, w, h) in enumerate(faces):
            cv2.rectangle(overlay, (x, y), (x + w, y + h), (64, 128, 255), 2)
            face_area = w * h
            if face_area > max_area:
                max_area = face_area
                max_face_center = (x + w // 2, y + h // 2)
            # 添加到检测结果
            detections.append({
                'id': f'face_{i}',
                'label': 'Face',
                'confidence': 85,  # Haar 级联不提供置信度，使用默认值
                'bbox': [int(x), int(y), int(w), int(h)]
            })

        # 更新检测结果（线程安全）
        with self.detections_lock:
            self.detections = detections
            self.detection_count = len(faces)

        if len(faces) > 0 and not self.motion_lock:
            self.gimbal_track(center_x, center_y,
                              max_face_center[0], max_face_center[1],
                              self.track_faces_iterate)

        cv2.putText(overlay, f'Faces: {len(faces)}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        self.overlay = overlay

    def _detect_objects(self, frame: np.ndarray):
        """物体检测（MobileNet SSD）"""
        if self.object_net is None:
            return

        overlay = np.zeros_like(frame)
        h, w = frame.shape[:2]

        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5
        )
        self.object_net.setInput(blob)
        net_detections = self.object_net.forward()

        # 构建检测结果
        detection_results = []
        for i in range(net_detections.shape[2]):
            confidence = net_detections[0, 0, i, 2]
            if confidence > 0.2:
                idx = int(net_detections[0, 0, i, 1])
                box = net_detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                label = f"{self.object_classes[idx]}: {confidence * 100:.1f}%"
                cv2.rectangle(overlay, (startX, startY), (endX, endY), (0, 255, 0), 2)
                y = startY - 15 if startY - 15 > 15 else startY + 15
                cv2.putText(overlay, label, (startX, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # 添加到检测结果
                detection_results.append({
                    'id': f'obj_{i}',
                    'label': self.object_classes[idx],
                    'confidence': int(confidence * 100),
                    'bbox': [int(startX), int(startY), int(endX - startX), int(endY - startY)]
                })

        # 更新检测结果（线程安全）
        with self.detections_lock:
            self.detections = detection_results
            self.detection_count = len(detection_results)

        self.overlay = overlay

    def _detect_color(self, frame: np.ndarray):
        """颜色检测与追踪"""
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, self.color_lower, self.color_upper)
        mask = cv2.erode(mask, None, iterations=5)
        mask = cv2.dilate(mask, None, iterations=5)

        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        overlay = np.zeros_like(frame)
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2

        # 采样圆
        cv2.circle(overlay, (center_x, center_y), self.sampling_rad, (64, 255, 64), 1)

        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            if M["m00"] > 0:
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

                if radius > self.min_radius:
                    if not self.motion_lock:
                        distance = self.gimbal_track(center_x, center_y,
                                                     center[0], center[1],
                                                     self.track_color_iterate)
                        cv2.putText(overlay, f'Dist: {distance:.1f}', (10, 60),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                    cv2.circle(overlay, (int(x), int(y)), int(radius), (128, 255, 255), 2)
                    cv2.circle(overlay, center, 5, (128, 255, 255), -1)
                    cv2.line(overlay, center, (center_x, center_y), (0, 0, 255), 1)

                    self.color_points.appendleft(center)

        # 绘制轨迹
        for i in range(1, len(self.color_points)):
            if self.color_points[i - 1] is None or self.color_points[i] is None:
                continue
            cv2.line(overlay, self.color_points[i - 1], self.color_points[i], (255, 255, 128), 1)

        # 颜色范围信息显示在左下角上方，避免和底部控制栏重叠
        cv2.putText(overlay, f'HSV: {self.color_lower.tolist()} - {self.color_upper.tolist()}',
                    (10, height - 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        self.overlay = overlay

    def _detect_hand(self, frame: np.ndarray):
        """手势检测（MediaPipe）"""
        if self.hands is None:
            return

        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        overlay = np.zeros_like(frame)

        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                # 绘制关节点
                for lm in hand_lms.landmark:
                    cx, cy = int(lm.x * width), int(lm.y * height)
                    cv2.circle(overlay, (cx, cy), 5, (255, 0, 0), -1)

                # 绘制连接线
                self.mp_draw.draw_landmarks(overlay, hand_lms, self.mp_hands.HAND_CONNECTIONS)

                # 追踪食指尖
                target = hand_lms.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                if not self.motion_lock:
                    self.gimbal_track(center_x, center_y,
                                      width * target.x, height * target.y,
                                      self.track_faces_iterate)

        cv2.putText(overlay, 'Hand Detection', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        self.overlay = overlay

    def _auto_drive(self, frame: np.ndarray):
        """巡线自动驾驶"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2

        # 颜色掩码
        line_mask = cv2.inRange(hsv, self.line_lower, self.line_upper)
        line_mask = cv2.erode(line_mask, None, iterations=2)
        line_mask = cv2.dilate(line_mask, None, iterations=2)

        # 采样线位置
        sampling_h1 = int(height * self.sampling_line_1)
        sampling_h2 = int(height * self.sampling_line_2)

        get_sampling_1 = line_mask[sampling_h1]
        get_sampling_2 = line_mask[sampling_h2]

        sampling_width_1 = np.sum(get_sampling_1 == 255)
        sampling_width_2 = np.sum(get_sampling_2 == 255)

        sam_1 = sampling_width_1 > 0
        sam_2 = sampling_width_2 > 0

        line_index_1 = np.where(get_sampling_1 == 255)
        line_index_2 = np.where(get_sampling_2 == 255)

        sampling_1_center = 0
        sampling_2_center = 0

        if sam_1:
            sampling_1_left = line_index_1[0][0]
            sampling_1_right = line_index_1[0][sampling_width_1 - 1]
            sampling_1_center = int((sampling_1_left + sampling_1_right) / 2)
        if sam_2:
            sampling_2_left = line_index_2[0][0]
            sampling_2_right = line_index_2[0][sampling_width_2 - 1]
            sampling_2_center = int((sampling_2_left + sampling_2_right) / 2)

        line_slope = 0
        input_speed = 0
        input_turning = 0

        if sam_1 and sam_2:
            line_slope = (sampling_1_center - sampling_2_center) / abs(sampling_h1 - sampling_h2)
            impact_by_slope = self.slope_on_speed * abs(line_slope)
            input_speed = self.line_track_speed - impact_by_slope
            input_turning = -(line_slope * self.slope_impact + (sampling_2_center - center_x) * self.base_impact)
        elif not sam_1 and sam_2:
            input_speed = 0
            input_turning = (sampling_2_center - center_x) * self.base_impact
        elif sam_1 and not sam_2:
            input_speed = self.line_track_speed / 3
            input_turning = 0
        else:
            input_speed = -self.line_track_speed / 3
            input_turning = 0

        # 发送运动控制命令
        if self.motor_controller and not self.motion_lock:
            self.motor_controller.send_json_command({
                "T": 13,
                "X": input_speed,
                "Z": input_turning
            })

        # 绘制叠加层
        overlay = cv2.cvtColor(line_mask, cv2.COLOR_GRAY2BGR)

        cv2.putText(overlay, 'Line Following', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(overlay, f'Speed: {input_speed:.2f}, Turn: {input_turning:.2f}',
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.line(overlay, (0, sampling_h1), (width, sampling_h1), (255, 0, 0), 2)
        cv2.line(overlay, (0, sampling_h2), (width, sampling_h2), (255, 0, 0), 2)

        if sam_1:
            cv2.circle(overlay, (sampling_1_center, sampling_h1), 5, (0, 255, 0), -1)
        if sam_2:
            cv2.circle(overlay, (sampling_2_center, sampling_h2), 5, (0, 255, 0), -1)

        self.overlay = overlay

    def _mediapipe_faces(self, frame: np.ndarray):
        """MediaPipe人脸检测"""
        if self.face_detection is None:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb)

        overlay = np.zeros_like(frame)

        cv2.putText(overlay, 'MediaPipe Faces', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        if results.detections:
            for detection in results.detections:
                self.mp_draw.draw_detection(overlay, detection)

        self.overlay = overlay

    def _mediapipe_pose(self, frame: np.ndarray):
        """MediaPipe姿态检测"""
        if self.pose is None:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)

        overlay = np.zeros_like(frame)

        cv2.putText(overlay, 'MediaPipe Pose', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        if results.pose_landmarks:
            self.mp_draw.draw_landmarks(
                overlay, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS
            )

        self.overlay = overlay

    def get_status(self) -> dict:
        """获取CV服务状态"""
        # 线程安全地获取检测结果
        with self.detections_lock:
            detections_copy = self.detections.copy()
            detection_count = self.detection_count

        return {
            'mode': self.cv_mode,
            'reaction_mode': self.reaction_mode,
            'motion_lock': self.motion_lock,
            'pan_angle': self.pan_angle,
            'tilt_angle': self.tilt_angle,
            'color_lower': self.color_lower.tolist(),
            'color_upper': self.color_upper.tolist(),
            'mock_mode': self.mock_mode,
            'detections': detections_copy,
            'detection_count': detection_count
        }

    def clear_detections(self):
        """清除检测结果"""
        with self.detections_lock:
            self.detections = []
            self.detection_count = 0


# 全局单例实例
_cv_service_instance = None


def get_cv_service(config=None):
    """
    获取CVService单例实例

    Args:
        config: 配置字典

    Returns:
        CVService实例
    """
    global _cv_service_instance
    if _cv_service_instance is None:
        _cv_service_instance = CVService(config)
    return _cv_service_instance


def init_cv_service(app_config):
    """
    从Flask配置初始化CVService

    Args:
        app_config: Flask app.config对象
    """
    config = {
        'models_path': app_config.get('CV_MODELS_PATH', './models'),
        'track_spd_rate': app_config.get('CV_TRACK_SPD_RATE', 60),
        'track_acc_rate': app_config.get('CV_TRACK_ACC_RATE', 0.4),
        'aimed_error': app_config.get('CV_AIMED_ERROR', 8),
        'mock_mode': app_config.get('MOCK_MODE', False)
    }
    return get_cv_service(config)
