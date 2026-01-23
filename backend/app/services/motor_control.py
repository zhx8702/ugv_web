"""
Motor Control Service
"""
import logging
from .base_controller import get_base_controller


class MotorController:
    """
    Motor and robot control service
    集成真实的BaseController硬件控制
    """

    def __init__(self, config=None):
        """Initialize motor controller"""
        self.left_speed = 0
        self.right_speed = 0
        self.pan_angle = 0
        self.tilt_angle = 0
        self.speed_mode = 'mid'

        # 获取BaseController实例
        self.base_controller = get_base_controller(config)

        if self.base_controller.mock_mode:
            logging.info('Motor controller initialized (mock mode)')
        else:
            logging.info('Motor controller initialized with hardware')

    def initialize_hardware(self, serial_port, baudrate):
        """
        Initialize hardware controller (for Raspberry Pi deployment)
        注意：硬件在__init__时已自动初始化，此方法保留用于兼容性

        Args:
            serial_port: Serial port path (e.g., /dev/serial0)
            baudrate: Baud rate (e.g., 115200)
        """
        logging.info(f'Hardware already initialized: {serial_port} @ {baudrate}')

    def send_command(self, code, val1=0, val2=0):
        """
        Send code-based command

        Args:
            code: Command code
            val1: First value
            val2: Second value

        Returns:
            dict: Result of command execution
        """
        logging.debug(f'Command: code={code}, val1={val1}, val2={val2}')

        # 发送到硬件控制器
        cmd_data = {'code': code, 'val1': val1, 'val2': val2}
        self.base_controller.send_command(cmd_data)

        return {
            'code': code,
            'val1': val1,
            'val2': val2,
            'executed': True
        }

    def send_json_command(self, data):
        """
        Send JSON command

        Args:
            data: dict with command data (T, L, R, X, Y, etc.)

        Returns:
            dict: Result of command execution
        """
        cmd_type = data.get('T')
        logging.debug(f'JSON command: T={cmd_type}, data={data}')

        # 直接发送到BaseController
        self.base_controller.base_json_ctrl(data)

        # 更新本地状态（用于状态查询）
        if cmd_type == 1:  # Movement control
            self.left_speed = data.get('L', 0)
            self.right_speed = data.get('R', 0)
        elif cmd_type == 133:  # Pan-tilt control
            self.pan_angle = data.get('X', 0)
            self.tilt_angle = data.get('Y', 0)

        return {'executed': True, 'data': data}

    def move(self, left, right):
        """
        Move robot with motor speeds

        Args:
            left: Left motor speed (-1.0 to 1.0)
            right: Right motor speed (-1.0 to 1.0)

        Returns:
            dict: Movement result
        """
        self.left_speed = max(-1.0, min(1.0, left))
        self.right_speed = max(-1.0, min(1.0, right))

        logging.debug(f'Move: L={self.left_speed:.2f}, R={self.right_speed:.2f}')

        # 发送到硬件
        self.base_controller.base_speed_ctrl(self.left_speed, self.right_speed)

        return {
            'left': self.left_speed,
            'right': self.right_speed
        }

    def stop(self):
        """Stop robot movement"""
        return self.move(0, 0)

    def set_pan_tilt(self, pan, tilt):
        """
        Set pan-tilt angles

        Args:
            pan: Pan angle in degrees (-180 ~ 180)
            tilt: Tilt angle in degrees (-30 ~ 90)

        Returns:
            dict: PT result
        """
        self.pan_angle = pan
        self.tilt_angle = tilt

        logging.debug(f'PT: pan={pan}°, tilt={tilt}°')

        # 发送到硬件
        self.base_controller.gimbal_ctrl(pan, tilt)

        return {
            'pan': self.pan_angle,
            'tilt': self.tilt_angle
        }

    def get_status(self):
        """Get controller status"""
        return {
            'left_speed': self.left_speed,
            'right_speed': self.right_speed,
            'pan_angle': self.pan_angle,
            'tilt_angle': self.tilt_angle,
            'speed_mode': self.speed_mode
        }

    # ========== 灯光控制 ==========

    def set_lights(self, base_pwm, head_pwm):
        """
        Set LED lights

        Args:
            base_pwm: Base light PWM (0-255)
            head_pwm: Head light PWM (0-255)

        Returns:
            dict: Light control result
        """
        logging.debug(f'Lights: base={base_pwm}, head={head_pwm}')
        self.base_controller.lights_ctrl(base_pwm, head_pwm)
        return {'base': base_pwm, 'head': head_pwm}

    def get_light_status(self):
        """Get current light status"""
        return {
            'base': self.base_controller.base_light_status,
            'head': self.base_controller.head_light_status
        }

    # ========== 电机锁定控制 ==========

    def lock_motor(self):
        """Lock motors (emergency stop)"""
        logging.info('Motor locked')
        self.base_controller.gimbal_emergency_stop()
        self.left_speed = 0
        self.right_speed = 0
        return {'locked': True}

    def unlock_motor(self):
        """Unlock motors"""
        logging.info('Motor unlocked')
        # 发送解锁命令 (发送一个小的移动命令来解锁)
        self.base_controller.base_speed_ctrl(0, 0)
        return {'locked': False}

    # ========== 舵机配置 ==========

    def set_servo_id(self, old_id, new_id):
        """
        Set servo ID

        Args:
            old_id: Current servo ID
            new_id: New servo ID

        Returns:
            dict: Result
        """
        logging.info(f'Set servo ID: {old_id} -> {new_id}')
        self.base_controller.bus_servo_id_set(old_id, new_id)
        return {'old_id': old_id, 'new_id': new_id}

    def set_servo_torque(self, servo_id, status):
        """
        Set servo torque lock

        Args:
            servo_id: Servo ID
            status: 1 to lock, 0 to unlock

        Returns:
            dict: Result
        """
        logging.debug(f'Servo torque: id={servo_id}, status={status}')
        self.base_controller.bus_servo_torque_lock(servo_id, status)
        return {'id': servo_id, 'locked': status == 1}

    def set_servo_mid(self, servo_id):
        """
        Set servo middle position

        Args:
            servo_id: Servo ID

        Returns:
            dict: Result
        """
        logging.info(f'Set servo mid: id={servo_id}')
        self.base_controller.bus_servo_mid_set(servo_id)
        return {'id': servo_id}

    def release_servo(self, servo_id=None):
        """
        Release servo (unlock torque)

        Args:
            servo_id: Servo ID (optional, release pan and tilt if not provided)

        Returns:
            dict: Result
        """
        if servo_id is not None:
            logging.info(f'Release servo: id={servo_id}')
            self.base_controller.bus_servo_torque_lock(servo_id, 0)
            return {'id': servo_id, 'released': True}
        else:
            # 释放 pan (id=1) 和 tilt (id=2) 舵机
            logging.info('Release all servos (pan & tilt)')
            self.base_controller.bus_servo_torque_lock(1, 0)
            self.base_controller.bus_servo_torque_lock(2, 0)
            return {'released': True, 'ids': [1, 2]}
