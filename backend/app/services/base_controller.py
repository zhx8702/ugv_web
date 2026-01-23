"""
Hardware Base Controller Service
整合自原 ugv_rpi/base_ctrl.py
"""
import serial
import json
import queue
import threading
import time
import glob
import logging
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class ReadLine:
    """串口数据读取类 - 支持传感器和LiDAR"""

    def __init__(self, serial_port):
        self.buf = bytearray()
        self.s = serial_port

        # 传感器数据 (USB串口)
        self.sensor_data = []
        self.sensor_list = []
        self.sensor_data_ser = None
        self.sensor_data_max_len = 51

        # LiDAR数据 (ACM串口)
        self.lidar_ser = None
        self.ANGLE_PER_FRAME = 12
        self.HEADER = 0x54
        self.lidar_angles = []
        self.lidar_distances = []
        self.lidar_angles_show = []
        self.lidar_distances_show = []
        self.last_start_angle = 0

        # 尝试连接外部传感器
        self._init_sensor()
        self._init_lidar()

    def _init_sensor(self):
        """初始化外部传感器串口"""
        try:
            usb_ports = glob.glob('/dev/ttyUSB*')
            if usb_ports:
                self.sensor_data_ser = serial.Serial(usb_ports[0], 115200)
                logger.info(f"Sensor connected: {usb_ports[0]}")
        except Exception as e:
            logger.warning(f"Sensor not available: {e}")
            self.sensor_data_ser = None

    def _init_lidar(self):
        """初始化LiDAR串口"""
        try:
            acm_ports = glob.glob('/dev/ttyACM*')
            if acm_ports:
                self.lidar_ser = serial.Serial(acm_ports[0], 230400, timeout=1)
                logger.info(f"LiDAR connected: {acm_ports[0]}")
        except Exception as e:
            logger.warning(f"LiDAR not available: {e}")
            self.lidar_ser = None

    def readline(self):
        """从主串口读取一行数据"""
        i = self.buf.find(b"\n")
        if i >= 0:
            r = self.buf[:i+1]
            self.buf = self.buf[i+1:]
            return r
        while True:
            i = max(1, min(512, self.s.in_waiting))
            data = self.s.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.buf + data[:i+1]
                self.buf[0:] = data[i+1:]
                return r
            else:
                self.buf.extend(data)

    def clear_buffer(self):
        """清空输入缓冲区"""
        self.s.reset_input_buffer()

    def read_sensor_data(self):
        """读取外部传感器数据"""
        if self.sensor_data_ser is None:
            return

        try:
            buffer_clear = False
            while self.sensor_data_ser.in_waiting > 0:
                buffer_clear = True
                sensor_readline = self.sensor_data_ser.readline()
                if len(sensor_readline) <= self.sensor_data_max_len:
                    self.sensor_list.append(sensor_readline.decode('utf-8')[:-2])
                else:
                    self.sensor_list.append(sensor_readline.decode('utf-8')[:self.sensor_data_max_len])
                    self.sensor_list.append(sensor_readline.decode('utf-8')[self.sensor_data_max_len:-2])
            if buffer_clear:
                self.sensor_data = self.sensor_list.copy()
                self.sensor_list.clear()
                self.sensor_data_ser.reset_input_buffer()
        except Exception as e:
            logger.error(f"Read sensor data error: {e}")

    def parse_lidar_frame(self, data):
        """解析LiDAR数据帧"""
        start_angle = (data[5] << 8 | data[4]) * 0.01
        for i in range(0, self.ANGLE_PER_FRAME):
            offset = 6 + i * 3
            distance = data[offset+1] << 8 | data[offset]
            confidence = data[offset+2]
            self.lidar_angles.append(np.radians(start_angle + i * 0.83333 + 180))
            self.lidar_distances.append(distance)
        return start_angle

    def lidar_data_recv(self):
        """接收LiDAR数据"""
        if self.lidar_ser is None:
            return
        try:
            while True:
                self.header = self.lidar_ser.read(1)
                if self.header == b'\x54':
                    data = self.header + self.lidar_ser.read(46)
                    hex_data = [int(hex(byte), 16) for byte in data]
                    start_angle = self.parse_lidar_frame(hex_data)
                    if self.last_start_angle > start_angle:
                        break
                    self.last_start_angle = start_angle
                else:
                    self.lidar_ser.flushInput()

            self.last_start_angle = start_angle
            self.lidar_angles_show = self.lidar_angles.copy()
            self.lidar_distances_show = self.lidar_distances.copy()
            self.lidar_angles.clear()
            self.lidar_distances.clear()
        except Exception as e:
            logger.error(f"LiDAR data receive error: {e}")
            # 尝试重新连接
            try:
                acm_ports = glob.glob('/dev/ttyACM*')
                if acm_ports:
                    self.lidar_ser = serial.Serial(acm_ports[0], 230400, timeout=1)
            except:
                pass


class BaseController:
    """
    硬件基础控制器
    通过UART与ESP32下位机通信，控制电机、云台、LED等
    """

    def __init__(self, config=None):
        """
        初始化硬件控制器

        Args:
            config: 配置字典，包含:
                - uart_port: 串口路径 (默认自动检测)
                - baudrate: 波特率 (默认115200)
                - mock_mode: 是否Mock模式 (默认False)
                - use_lidar: 是否使用LiDAR
                - extra_sensor: 是否使用外部传感器
        """
        self.config = config or {}
        self.mock_mode = self.config.get('mock_mode', False)

        # 硬件状态
        self.base_light_status = 0
        self.head_light_status = 0
        self.base_data = {'T': 0, 'L': 0, 'R': 0, 'v': 0, 'pan': 0, 'tilt': 0}
        self.data_buffer = None

        # 外设支持
        self.use_lidar = self.config.get('use_lidar', False)
        self.extra_sensor = self.config.get('extra_sensor', False)

        # 串口和命令队列
        self.ser = None
        self.rl = None
        self.command_queue = queue.Queue()
        self.command_thread = None

        # 初始化硬件
        if not self.mock_mode:
            self._init_hardware()
        else:
            logger.warning("BaseController running in MOCK mode")

    def _init_hardware(self):
        """初始化硬件串口"""
        try:
            # 自动检测树莓派版本和串口
            uart_port = self.config.get('uart_port')

            if not uart_port:
                # 检测树莓派5或4
                uart_port = self._detect_uart_port()

            baudrate = self.config.get('baudrate', 115200)

            logger.info(f"Initializing UART: {uart_port} @ {baudrate}")
            self.ser = serial.Serial(uart_port, baudrate, timeout=1)
            self.rl = ReadLine(self.ser)

            # 启动命令处理线程
            self.command_thread = threading.Thread(target=self._process_commands, daemon=True)
            self.command_thread.start()

            # 发送初始化命令到下位机
            self._send_init_commands()

            logger.info("Hardware controller initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize hardware: {e}")
            logger.warning("Falling back to MOCK mode")
            self.mock_mode = True

    def _detect_uart_port(self):
        """自动检测UART端口"""
        try:
            # 检测是否是树莓派5
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'Model' in line and 'Raspberry Pi 5' in line:
                        return '/dev/ttyAMA0'
            # 默认树莓派4及以下
            return '/dev/serial0'
        except:
            return '/dev/serial0'

    def _send_init_commands(self):
        """发送初始化命令到下位机"""
        import time
        # 等待串口稳定
        time.sleep(0.5)

        # 模块类型: 0=无, 1=机械臂(RoArm-M2-S), 2=云台(Gimbal)
        module_type = self.config.get('module_type', 2)

        init_commands = [
            {"T": 142, "cmd": 50},      # 设置反馈间隔 (50ms)
            {"T": 131, "cmd": 1},       # 开启串口反馈流
            {"T": 143, "cmd": 0},       # 关闭串口回显
            {"T": 4, "cmd": module_type},  # 选择模块类型
        ]

        for cmd in init_commands:
            self.send_command(cmd)
            time.sleep(0.1)

        logger.info(f"Init commands sent, module_type={module_type}")

    def _process_commands(self):
        """命令队列处理线程"""
        while True:
            try:
                data = self.command_queue.get()
                if self.ser and not self.mock_mode:
                    cmd_str = json.dumps(data) + '\n'
                    self.ser.write(cmd_str.encode("utf-8"))
                    logger.debug(f"Sent command: {data}")
                else:
                    logger.debug(f"Mock command: {data}")
            except Exception as e:
                logger.error(f"Command processing error: {e}")

    def send_command(self, data):
        """发送命令到队列"""
        self.command_queue.put(data)
        logger.debug(f"Command queued: {data} (mock={self.mock_mode})")

    def base_json_ctrl(self, input_json):
        """发送JSON命令"""
        self.send_command(input_json)

    def feedback_data(self):
        """读取下位机反馈数据"""
        if self.mock_mode or not self.rl:
            return self.base_data

        try:
            while self.rl.s.in_waiting > 0:
                self.data_buffer = json.loads(self.rl.readline().decode('utf-8'))
                if 'T' in self.data_buffer:
                    self.base_data = self.data_buffer
                    self.data_buffer = None
                    if self.base_data["T"] == 1003:
                        logger.debug(f"Feedback: {self.base_data}")
                        return self.base_data
            self.rl.clear_buffer()
            self.data_buffer = json.loads(self.rl.readline().decode('utf-8'))
            self.base_data = self.data_buffer
            return self.base_data
        except Exception as e:
            self.rl.clear_buffer()
            logger.error(f"Feedback data error: {e}")
            return self.base_data

    # ========== 运动控制 ==========

    def gimbal_emergency_stop(self):
        """紧急停止"""
        data = {"T": 0}
        self.send_command(data)

    def base_speed_ctrl(self, left, right):
        """
        电机速度控制

        Args:
            left: 左轮速度 (-1.0 ~ 1.0)
            right: 右轮速度 (-1.0 ~ 1.0)
        """
        data = {"T": 1, "L": left, "R": right}
        self.send_command(data)

    def gimbal_ctrl(self, x, y, speed=200, acceleration=10):
        """
        云台控制

        Args:
            x: 水平角度 (-180 ~ 180), 负值向左，正值向右
            y: 垂直角度 (-30 ~ 90), 负值向下，正值向上
            speed: 速度
            acceleration: 加速度
        """
        data = {"T": 133, "X": x, "Y": y, "SPD": speed, "ACC": acceleration}
        self.send_command(data)

    def gimbal_base_ctrl(self, x, y, speed):
        """云台基础控制（简化版）"""
        data = {"T": 141, "X": x, "Y": y, "SPD": speed}
        self.send_command(data)

    # ========== OLED显示 ==========

    def base_oled(self, line_num, text):
        """
        OLED显示文本

        Args:
            line_num: 行号 (0-3)
            text: 显示文本
        """
        data = {"T": 3, "lineNum": line_num, "Text": text}
        self.send_command(data)

    def base_default_oled(self):
        """恢复OLED默认显示"""
        data = {"T": -3}
        self.send_command(data)

    # ========== 舵机控制 ==========

    def bus_servo_id_set(self, old_id, new_id):
        """设置总线舵机ID"""
        data = {"T": 501, "raw": old_id, "new": new_id}
        self.send_command(data)

    def bus_servo_torque_lock(self, servo_id, status):
        """舵机扭矩锁定"""
        data = {"T": 210, "id": servo_id, "cmd": status}
        self.send_command(data)

    def bus_servo_mid_set(self, servo_id):
        """设置舵机中位"""
        data = {"T": 502, "id": servo_id}
        self.send_command(data)

    # ========== LED灯光控制 ==========

    def lights_ctrl(self, base_pwm, head_pwm):
        """
        LED灯控制

        Args:
            base_pwm: 底盘灯PWM (0-255)
            head_pwm: 头灯PWM (0-255)
        """
        data = {"T": 132, "IO4": base_pwm, "IO5": head_pwm}
        self.send_command(data)
        self.base_light_status = base_pwm
        self.head_light_status = head_pwm

    def base_lights_ctrl(self):
        """切换底盘灯状态"""
        if self.base_light_status != 0:
            self.base_light_status = 0
        else:
            self.base_light_status = 255
        self.lights_ctrl(self.base_light_status, self.head_light_status)

    def breath_light(self, duration):
        """
        呼吸灯效果

        Args:
            duration: 持续时间（秒）
        """
        if self.mock_mode:
            logger.info(f"Mock breath light for {duration}s")
            return

        breath_start_time = time.time()
        while time.time() - breath_start_time < duration:
            for i in range(0, 128, 10):
                self.lights_ctrl(i, 128-i)
                time.sleep(0.1)
            for i in range(0, 128, 10):
                self.lights_ctrl(128-i, i)
                time.sleep(0.1)
        self.lights_ctrl(0, 0)

    # ========== 关闭 ==========

    def close(self):
        """关闭串口连接"""
        if self.ser:
            self.ser.close()
            logger.info("Hardware controller closed")

    def __del__(self):
        """析构函数"""
        self.close()


# 全局单例实例
_base_controller_instance = None


def get_base_controller(config=None):
    """
    获取BaseController单例实例

    Args:
        config: 配置字典

    Returns:
        BaseController实例
    """
    global _base_controller_instance
    if _base_controller_instance is None:
        _base_controller_instance = BaseController(config)
    return _base_controller_instance


def init_base_controller(app_config):
    """
    从Flask配置初始化BaseController

    Args:
        app_config: Flask app.config对象
    """
    config = {
        'uart_port': app_config.get('UART_PORT'),
        'baudrate': app_config.get('UART_BAUDRATE', 115200),
        'mock_mode': app_config.get('MOCK_MODE', False),
        'use_lidar': app_config.get('USE_LIDAR', False),
        'extra_sensor': app_config.get('EXTRA_SENSOR', False)
    }
    return get_base_controller(config)
