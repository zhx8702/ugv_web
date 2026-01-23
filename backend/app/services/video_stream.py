# -*- coding: utf-8 -*-
"""
Video Stream Service
视频流服务 - 支持MJPEG流、拍照、录像
支持USB/CSI/OAK摄像头
基于原ugv_rpi/cv_ctrl.py重构
"""
import cv2
import numpy as np
import threading
import datetime
import time
import logging
import os
from pathlib import Path
import imageio

logger = logging.getLogger(__name__)

# 可选依赖 - CSI摄像头
try:
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    logger.info("Picamera2 not available (CSI camera disabled)")

# 可选依赖 - OAK摄像头
try:
    import depthai as dai
    DEPTHAI_AVAILABLE = True
except ImportError:
    DEPTHAI_AVAILABLE = False
    logger.info("DepthAI not available (OAK camera disabled)")


class VideoStream:
    """
    视频流服务
    支持多种摄像头（USB/CSI/OAK）和MJPEG流输出
    """

    def __init__(self, config=None):
        """
        初始化视频流

        Args:
            config: 配置字典，包含:
                - camera_index: 摄像头索引 (默认0)
                - width: 视频宽度 (默认640)
                - height: 视频高度 (默认480)
                - fps: 帧率 (默认30)
                - quality: JPEG质量 (默认20)
                - photos_path: 照片保存路径
                - videos_path: 视频保存路径
                - mock_mode: Mock模式（生成测试图像）
        """
        self.config = config or {}
        self.mock_mode = self.config.get('mock_mode', False)

        # 视频参数 - 优先从环境变量读取
        self.camera_index = self.config.get('camera_index', int(os.getenv('CAMERA_INDEX', 0)))
        self.width = self.config.get('width', int(os.getenv('VIDEO_WIDTH', 1280)))
        self.height = self.config.get('height', int(os.getenv('VIDEO_HEIGHT', 720)))
        self.target_fps = self.config.get('fps', int(os.getenv('VIDEO_FPS', 30)))
        self.quality = self.config.get('quality', int(os.getenv('VIDEO_QUALITY', 80)))

        # 路径
        self.photos_path = Path(self.config.get('photos_path', './media/photos'))
        self.videos_path = Path(self.config.get('videos_path', './media/videos'))
        self.photos_path.mkdir(parents=True, exist_ok=True)
        self.videos_path.mkdir(parents=True, exist_ok=True)

        # 状态
        self.camera = None
        self.camera_type = None  # 'usb', 'csi', 'oak', or 'mock'
        self.running = False
        self.frame_lock = threading.Lock()
        self.current_frame = None

        # 拍照/录像
        self.picture_capture_flag = False
        self.video_recording = False
        self.video_writer = None

        # 缩放
        self.scale_rate = 1  # 1x, 2x, 4x

        # FPS统计
        self.fps = 0
        self.fps_count = 0
        self.fps_start_time = time.time()

        # CSI摄像头相关
        self.picam2 = None

        # OAK摄像头相关
        self.oak_device = None
        self.oak_queue = None

        # CV服务引用
        self.cv_service = None

        # LiDAR服务引用
        self.lidar_service = None

        # 摄像头类型强制选择（通过环境变量）
        # 可选值: 'usb', 'csi', 'oak', 'auto' (默认)
        self.camera_prefer = os.getenv('CAMERA_TYPE', 'auto').lower()

        # 初始化摄像头
        self._init_camera()

        # 注册清理函数
        import atexit
        atexit.register(self._cleanup)

    def _cleanup(self):
        """进程退出时清理资源"""
        logger.info("VideoStream cleanup on exit")
        self.stop()

    def set_cv_service(self, cv_service):
        """设置CV服务引用"""
        self.cv_service = cv_service

    def set_lidar_service(self, lidar_service):
        """设置LiDAR服务引用"""
        self.lidar_service = lidar_service

    def _detect_usb_camera(self) -> bool:
        """检测是否有USB摄像头连接（通过lsusb命令，仅Linux）"""
        import sys
        if sys.platform == 'win32':
            # Windows 下跳过 lsusb 检测，直接返回 True 让后续尝试打开
            return True

        try:
            import subprocess
            lsusb_output = subprocess.check_output(["lsusb"], timeout=5).decode("utf-8")
            if "Camera" in lsusb_output:
                logger.info("USB Camera detected via lsusb")
                return True
            else:
                logger.debug("No USB Camera found in lsusb output")
                return False
        except Exception as e:
            logger.debug(f"lsusb detection failed: {e}")
            return False

    def _init_camera(self):
        """初始化摄像头（按优先级尝试）"""
        import sys

        if self.mock_mode:
            self.camera_type = 'mock'
            logger.warning("VideoStream running in MOCK mode")
            return

        # Windows 开发环境：直接尝试 USB 摄像头
        if sys.platform == 'win32':
            if self._try_usb_camera():
                return
            # Windows 下没有 CSI/OAK，直接降级
            logger.warning("No camera found on Windows, falling back to MOCK mode")
            self.camera_type = 'mock'
            self.mock_mode = True
            return

        # Linux 生产环境
        # 如果指定了摄像头类型，直接尝试该类型
        if self.camera_prefer == 'usb':
            logger.info("CAMERA_TYPE=usb, forcing USB camera")
            if self._try_usb_camera():
                return
            logger.warning("USB camera forced but not available")
        elif self.camera_prefer == 'csi':
            logger.info("CAMERA_TYPE=csi, forcing CSI camera")
            if self._try_csi_camera():
                return
            logger.warning("CSI camera forced but not available")
        elif self.camera_prefer == 'oak':
            logger.info("CAMERA_TYPE=oak, forcing OAK camera")
            if self._try_oak_camera():
                return
            logger.warning("OAK camera forced but not available")
        else:
            # auto 模式：按优先级尝试
            # 1. 先检测是否有USB摄像头
            usb_detected = self._detect_usb_camera()

            # 2. 如果检测到USB摄像头，尝试初始化
            if usb_detected and self._try_usb_camera():
                return

            # 3. 尝试CSI摄像头（树莓派）
            if self._try_csi_camera():
                return

            # 4. 尝试OAK摄像头
            if self._try_oak_camera():
                return

        # 降级到Mock模式
        logger.warning("No camera found, falling back to MOCK mode")
        self.camera_type = 'mock'
        self.mock_mode = True

    def _try_usb_camera(self) -> bool:
        """尝试初始化USB摄像头（尝试多个索引）"""
        for index in range(4):
            try:
                logger.info(f"Trying USB camera at index {index}")
                # 使用默认后端（和原代码一致）
                camera = cv2.VideoCapture(index)
                if camera.isOpened():
                    # 先设置 MJPEG 编码，再读取测试帧
                    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

                    # 读取一帧测试是否真正可用
                    ret, _ = camera.read()
                    if not ret:
                        logger.debug(f"Index {index} opened but can't read frame")
                        camera.release()
                        continue

                    self.camera = camera
                    self.camera_index = index

                    # 设置分辨率
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

                    # 设置帧率
                    self.camera.set(cv2.CAP_PROP_FPS, self.target_fps)

                    # 设置自动曝光（1=手动, 3=自动）
                    self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)

                    # 设置缓冲区大小为1，减少延迟
                    self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                    # 获取实际值
                    actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
                    actual_width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
                    actual_height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    fourcc = int(self.camera.get(cv2.CAP_PROP_FOURCC))
                    fourcc_str = ''.join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])

                    self.camera_type = 'usb'
                    logger.info(f"USB camera initialized at index {index}: {int(actual_width)}x{int(actual_height)} @ {actual_fps:.1f}fps, codec={fourcc_str}")
                    return True
                else:
                    logger.debug(f"Index {index} can't be opened")
                    camera.release()
            except Exception as e:
                logger.debug(f"USB camera index {index} not available: {e}")
        return False

    def _try_csi_camera(self) -> bool:
        """尝试初始化CSI摄像头（Picamera2）"""
        if not PICAMERA2_AVAILABLE:
            return False

        try:
            self.picam2 = Picamera2()
            config = self.picam2.create_video_configuration(
                main={"format": 'XRGB8888', "size": (self.width, self.height)}
            )
            self.picam2.configure(config)
            self.picam2.start()
            self.camera_type = 'csi'
            logger.info(f"CSI camera initialized: {self.width}x{self.height}")
            return True
        except Exception as e:
            logger.debug(f"CSI camera not available: {e}")
            self.picam2 = None
        return False

    def _try_oak_camera(self) -> bool:
        """尝试初始化OAK摄像头（DepthAI）"""
        if not DEPTHAI_AVAILABLE:
            return False

        try:
            pipeline = dai.Pipeline()

            cam_rgb = pipeline.createColorCamera()
            cam_rgb.setBoardSocket(dai.CameraBoardSocket.RGB)
            cam_rgb.setInterleaved(False)
            # IMX378/214 传感器只支持 1080P / 4K / 12MP，不支持 720P
            cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
            cam_rgb.setFps(self.target_fps)

            xout = pipeline.createXLinkOut()
            xout.setStreamName("video")
            cam_rgb.video.link(xout.input)

            self.oak_device = dai.Device(pipeline)
            self.oak_queue = self.oak_device.getOutputQueue(
                name="video", maxSize=4, blocking=False
            )
            self.camera_type = 'oak'
            logger.info(f"OAK camera initialized: 1080P @ {self.target_fps}fps")
            return True
        except Exception as e:
            logger.debug(f"OAK camera not available: {e}")
            self.oak_device = None
            self.oak_queue = None
        return False

    def start(self):
        """启动视频流"""
        if self.running:
            logger.warning("VideoStream already running")
            return

        self.running = True
        logger.info("VideoStream started")

    def stop(self):
        """停止视频流"""
        self.running = False

        # 停止录像
        if self.video_recording:
            self.stop_recording()

        # 释放摄像头
        if self.camera_type == 'usb' and self.camera:
            self.camera.release()
            logger.info("USB camera released")
        elif self.camera_type == 'csi' and self.picam2:
            self.picam2.stop()
            self.picam2.close()
            self.picam2 = None
            logger.info("CSI camera released")
        elif self.camera_type == 'oak' and self.oak_device:
            self.oak_device.close()
            self.oak_device = None
            self.oak_queue = None
            logger.info("OAK camera released")

        logger.info("VideoStream stopped")

    def _generate_mock_frame(self):
        """生成Mock测试帧"""
        frame = np.ones((self.height, self.width, 3), dtype=np.uint8) * 50

        # 添加文字
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, "MOCK CAMERA MODE", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, timestamp, (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(frame, f"Resolution: {self.width}x{self.height}", (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (20, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # 添加矩形和圆形（模拟检测框）
        cv2.rectangle(frame, (200, 150), (440, 330), (0, 255, 0), 2)
        cv2.circle(frame, (320, 240), 50, (0, 0, 255), 2)

        return frame

    def read_frame(self):
        """
        读取一帧图像

        Returns:
            numpy.ndarray: BGR格式的图像帧，如果失败返回None
        """
        if not self.running:
            return None

        try:
            if self.camera_type == 'usb':
                success, frame = self.camera.read()
                if not success:
                    logger.error("Failed to read from USB camera")
                    # 尝试重新连接
                    self.camera.release()
                    time.sleep(1)
                    self.camera = cv2.VideoCapture(self.camera_index)
                    return self._generate_mock_frame()
                # 确保帧大小与配置一致（摄像头可能不支持请求的分辨率）
                if frame.shape[:2] != (self.height, self.width):
                    frame = cv2.resize(frame, (self.width, self.height))
                return frame

            elif self.camera_type == 'csi':
                # CSI摄像头（Picamera2）
                frame = self.picam2.capture_array()
                # XRGB8888 -> BGR
                if frame.shape[2] == 4:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                # 确保帧大小与配置一致
                if frame.shape[:2] != (self.height, self.width):
                    frame = cv2.resize(frame, (self.width, self.height))
                return frame

            elif self.camera_type == 'oak':
                # OAK摄像头（DepthAI）
                in_frame = self.oak_queue.get()
                frame = in_frame.getCvFrame()
                # 调整大小
                if frame.shape[:2] != (self.height, self.width):
                    frame = cv2.resize(frame, (self.width, self.height))
                return frame

            elif self.camera_type == 'mock':
                return self._generate_mock_frame()

        except Exception as e:
            logger.error(f"Error reading frame: {e}")
            return self._generate_mock_frame()

        return None

    def process_frame(self, frame):
        """
        处理帧（添加CV处理、OSD、缩放等）

        Args:
            frame: 原始帧

        Returns:
            处理后的帧
        """
        if frame is None:
            return None

        # CV视觉处理
        if self.cv_service:
            frame = self.cv_service.process_frame(frame)

        # LiDAR叠加
        if self.lidar_service:
            frame = self.lidar_service.overlay_on_frame(frame)

        # 处理拍照
        if self.picture_capture_flag:
            self.picture_capture_flag = False
            self._save_photo(frame)

        # 处理录像
        if self.video_recording and self.video_writer:
            # 添加录制指示器
            cv2.circle(frame, (15, 15), 5, (0, 0, 255), -1)
            # 写入视频
            self.video_writer.append_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # 处理缩放
        if self.scale_rate > 1:
            frame = self._apply_zoom(frame)

        # 更新FPS
        self._update_fps()

        # 添加OSD信息
        frame = self._add_osd(frame)

        with self.frame_lock:
            self.current_frame = frame.copy()

        return frame

    def _add_osd(self, frame):
        """添加OSD信息到画面"""
        h, w = frame.shape[:2]

        # 时间戳
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        # FPS
        fps_text = f"FPS: {self.fps:.1f}"
        cv2.putText(frame, fps_text, (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

        # 分辨率
        res_text = f"{w}x{h}"
        cv2.putText(frame, res_text, (10, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

        # 摄像头类型
        cam_text = f"CAM: {self.camera_type.upper()}"
        cv2.putText(frame, cam_text, (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

        # 缩放倍率（如果不是1x）
        if self.scale_rate > 1:
            zoom_text = f"ZOOM: {self.scale_rate}x"
            cv2.putText(frame, zoom_text, (10, 125),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 165, 0), 1, cv2.LINE_AA)

        # 录制状态
        if self.video_recording:
            rec_text = "REC"
            cv2.putText(frame, rec_text, (w - 60, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.circle(frame, (w - 75, 20), 8, (0, 0, 255), -1)

        return frame

    def _apply_zoom(self, frame):
        """应用数字缩放"""
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2

        # 计算裁剪区域
        crop_w = w // self.scale_rate
        crop_h = h // self.scale_rate

        x1 = max(0, cx - crop_w // 2)
        y1 = max(0, cy - crop_h // 2)
        x2 = min(w, x1 + crop_w)
        y2 = min(h, y1 + crop_h)

        # 裁剪并放大
        cropped = frame[y1:y2, x1:x2]
        zoomed = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

        return zoomed

    def _update_fps(self):
        """更新FPS统计"""
        self.fps_count += 1
        elapsed = time.time() - self.fps_start_time

        if elapsed > 1.0:
            self.fps = self.fps_count / elapsed
            self.fps_count = 0
            self.fps_start_time = time.time()

    def generate_frames(self):
        """
        生成MJPEG流帧（Generator）

        Yields:
            bytes: JPEG编码的帧数据（multipart格式）
        """
        # 使用 eventlet 兼容的 sleep（如果可用）
        try:
            import eventlet
            sleep_func = eventlet.sleep
        except ImportError:
            sleep_func = time.sleep

        while self.running:
            frame = self.read_frame()
            if frame is None:
                sleep_func(0.1)
                continue

            # 处理帧
            frame = self.process_frame(frame)

            # JPEG编码
            ret, buffer = cv2.imencode('.jpg', frame,
                                       [int(cv2.IMWRITE_JPEG_QUALITY), self.quality])
            if not ret:
                continue

            frame_bytes = buffer.tobytes()

            # 生成multipart格式
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # 控制帧率 - 使用 eventlet 兼容的 sleep
            sleep_func(1.0 / self.target_fps)

    def capture_photo(self):
        """触发拍照"""
        self.picture_capture_flag = True
        logger.info("Photo capture triggered")

    def _save_photo(self, frame):
        """保存照片"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = self.photos_path / f"photo_{timestamp}.jpg"
            cv2.imwrite(str(filename), frame)
            logger.info(f"Photo saved: {filename}")
            return str(filename)
        except Exception as e:
            logger.error(f"Failed to save photo: {e}")
            return None

    def start_recording(self):
        """开始录像"""
        if self.video_recording:
            logger.warning("Already recording")
            return False

        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = self.videos_path / f"video_{timestamp}.mp4"

            # 使用imageio创建视频写入器
            # 使用 ffmpeg 参数确保浏览器兼容性
            self.video_writer = imageio.get_writer(
                str(filename),
                fps=self.target_fps,
                codec='libx264',
                pixelformat='yuv420p',  # 标准像素格式，确保浏览器兼容
                output_params=[
                    '-preset', 'fast',
                    '-crf', '23',
                    '-movflags', '+faststart',
                    '-s', f'{self.width}x{self.height}'  # 显式指定分辨率
                ]
            )

            self.video_recording = True
            logger.info(f"Recording started: {filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False

    def stop_recording(self):
        """停止录像"""
        if not self.video_recording:
            logger.warning("Not recording")
            return False

        try:
            # 先标记为停止录制，这样帧处理不会继续写入
            self.video_recording = False

            # 在后台线程中关闭 writer，避免阻塞帧处理
            if self.video_writer:
                writer = self.video_writer
                self.video_writer = None

                def close_writer():
                    try:
                        writer.close()
                        logger.info("Video writer closed successfully")
                    except Exception as e:
                        logger.error(f"Failed to close video writer: {e}")

                thread = threading.Thread(target=close_writer, daemon=True)
                thread.start()

            logger.info("Recording stopped")
            return True

        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return False

    def set_zoom(self, rate):
        """
        设置缩放倍率

        Args:
            rate: 缩放倍率 (1, 2, 4)
        """
        if rate in [1, 2, 4]:
            self.scale_rate = rate
            logger.info(f"Zoom set to {rate}x")
        else:
            logger.warning(f"Invalid zoom rate: {rate}")

    def set_quality(self, quality):
        """
        设置JPEG质量

        Args:
            quality: 质量 (1-100)
        """
        self.quality = max(1, min(100, quality))
        logger.info(f"Quality set to {self.quality}")

    def get_current_frame(self):
        """获取当前帧（线程安全）"""
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None

    def start_timelapse(self, speed, move_time, interval, loop_times):
        """
        开始延时摄影

        Args:
            speed: 移动速度 (0-1)
            move_time: 移动时间（秒）
            interval: 拍照间隔（秒）
            loop_times: 循环次数

        Returns:
            bool: 是否成功启动
        """
        if hasattr(self, 'timelapse_running') and self.timelapse_running:
            logger.warning("Timelapse already running")
            return False

        self.timelapse_running = True
        self.timelapse_stop_flag = False

        # 启动延时摄影线程
        thread = threading.Thread(
            target=self._timelapse_worker,
            args=(speed, move_time, interval, loop_times),
            daemon=True
        )
        thread.start()

        logger.info(f"Timelapse started: speed={speed}, move_time={move_time}, interval={interval}, loops={loop_times}")
        return True

    def stop_timelapse(self):
        """停止延时摄影"""
        if hasattr(self, 'timelapse_running'):
            self.timelapse_stop_flag = True
            self.timelapse_running = False
            logger.info("Timelapse stopped")
            return True
        return False

    def _timelapse_worker(self, speed, move_time, interval, loop_times):
        """延时摄影工作线程"""
        try:
            # 获取motor_controller（如果可用）
            from app.services.base_controller import get_base_controller
            try:
                motor = get_base_controller()
            except:
                motor = None
                logger.warning("Motor controller not available for timelapse")

            for i in range(loop_times):
                if self.timelapse_stop_flag:
                    break

                # 1. 前进
                if motor:
                    motor.send_json_command({"T": 1, "L": speed, "R": speed})
                time.sleep(move_time)

                # 2. 停止
                if motor:
                    motor.send_json_command({"T": 1, "L": 0, "R": 0})

                # 3. 等待一半间隔
                time.sleep(interval / 2)

                # 4. 打开灯光（如果可用）
                if motor:
                    try:
                        motor.send_json_command({"T": 132, "IO4": 255, "IO5": 255})  # 灯光控制命令
                    except:
                        pass

                time.sleep(0.01)

                # 5. 拍照
                self.capture_photo()

                # 6. 关闭灯光
                if motor:
                    try:
                        motor.send_json_command({"T": 132, "IO4": 0, "IO5": 0})
                    except:
                        pass

                # 7. 等待另一半间隔
                time.sleep(interval / 2)

                if self.timelapse_stop_flag:
                    break

            logger.info("Timelapse completed")

        except Exception as e:
            logger.error(f"Timelapse error: {e}")
        finally:
            self.timelapse_running = False

    def get_status(self):
        """获取视频流状态"""
        return {
            'running': self.running,
            'camera_type': self.camera_type,
            'resolution': f'{self.width}x{self.height}',
            'fps': round(self.fps, 1),
            'quality': self.quality,
            'zoom': self.scale_rate,
            'recording': self.video_recording,
            'mock_mode': self.mock_mode
        }


# 全局单例实例
_video_stream_instance = None


def get_video_stream(config=None):
    """
    获取VideoStream单例实例

    Args:
        config: 配置字典

    Returns:
        VideoStream实例
    """
    global _video_stream_instance
    if _video_stream_instance is None:
        _video_stream_instance = VideoStream(config)
    return _video_stream_instance


def init_video_stream(app_config):
    """
    从Flask配置初始化VideoStream

    Args:
        app_config: Flask app.config对象
    """
    config = {
        'camera_index': app_config.get('CAMERA_INDEX', 0),
        'width': app_config.get('VIDEO_WIDTH', 640),
        'height': app_config.get('VIDEO_HEIGHT', 480),
        'fps': app_config.get('VIDEO_FPS', 30),
        'quality': app_config.get('VIDEO_QUALITY', 20),
        'photos_path': app_config.get('PHOTOS_PATH'),
        'videos_path': app_config.get('VIDEOS_PATH'),
        'mock_mode': app_config.get('MOCK_MODE', False)
    }
    stream = get_video_stream(config)
    stream.start()
    return stream
