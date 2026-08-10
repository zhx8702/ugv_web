"""
ROS2 Motor Controller Service

Drop-in replacement for BaseController-based motor control.
Routes commands through rosbridge to ROS2 topics instead of
direct UART serial communication.

Topic mapping (matches ugv_driver.py):
  /cmd_vel            (geometry_msgs/Twist)          → motor speeds
  /ugv/joint_states   (sensor_msgs/JointState)       → gimbal pan/tilt
  /ugv/led_ctrl       (std_msgs/Float32MultiArray)   → LED lighting
"""
import math
import logging
import threading

logger = logging.getLogger(__name__)


class ROS2MotorController:
    """
    Motor controller that publishes to ROS2 topics via rosbridge.

    Provides the same public interface as MotorController so the
    Flask API layer needs no changes.
    """

    # Must match the robot URDF / ugv_driver.py expectations
    WHEEL_SEPARATION = 0.172  # meters between wheels

    def __init__(self, bridge):
        """
        Args:
            bridge: ROS2Bridge instance (already connected)
        """
        self.bridge = bridge

        # Local state mirrors
        self.left_speed = 0.0
        self.right_speed = 0.0
        self.pan_angle = 0.0
        self.tilt_angle = 0.0
        self.base_light_status = 0
        self.head_light_status = 0

        # Feedback data from ROS2 subscriptions
        self._feedback = {}
        self._feedback_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Motor control  →  /cmd_vel  (geometry_msgs/Twist)
    # ------------------------------------------------------------------

    def move(self, left, right):
        """
        Convert differential-drive (left, right) speeds to Twist and
        publish on /cmd_vel.

        The ugv_driver node converts Twist back to serial:
          {'T': '13', 'X': linear_x, 'Z': angular_z}

        Conversion:
          linear.x  = (left + right) / 2.0
          angular.z = (right - left) / wheel_separation
        """
        left = max(-1.3, min(1.3, float(left)))
        right = max(-1.3, min(1.3, float(right)))

        linear_x = (left + right) / 2.0
        angular_z = (right - left) / self.WHEEL_SEPARATION

        twist = {
            'linear': {'x': linear_x, 'y': 0.0, 'z': 0.0},
            'angular': {'x': 0.0, 'y': 0.0, 'z': angular_z},
        }

        self.bridge.publish('/cmd_vel', 'geometry_msgs/Twist', twist)

        self.left_speed = left
        self.right_speed = right

        return {'left': left, 'right': right}

    def stop(self):
        """Publish zero velocity."""
        return self.move(0, 0)

    def base_speed_ctrl(self, left, right):
        """Alias used by BaseController interface."""
        return self.move(left, right)

    # ------------------------------------------------------------------
    # Gimbal  →  /ugv/joint_states  (sensor_msgs/JointState)
    # ------------------------------------------------------------------

    def set_pan_tilt(self, pan, tilt):
        """
        Publish JointState to /ugv/joint_states.

        The ugv_driver node converts radians → degrees and sends:
          {'T': 134, 'X': deg, 'Y': deg, 'SX': 600, 'SY': 600}

        Args:
            pan:  pan angle in degrees (-180 ~ 180)
            tilt: tilt angle in degrees (-30 ~ 90)
        """
        pan_rad = math.radians(float(pan))
        tilt_rad = math.radians(float(tilt))

        joint_state = {
            'header': {
                'stamp': {'sec': 0, 'nanosec': 0},
                'frame_id': '',
            },
            'name': [
                'pt_base_link_to_pt_link1',
                'pt_link1_to_pt_link2',
            ],
            'position': [pan_rad, tilt_rad],
            'velocity': [],
            'effort': [],
        }

        self.bridge.publish(
            '/ugv/joint_states', 'sensor_msgs/JointState', joint_state
        )

        self.pan_angle = pan
        self.tilt_angle = tilt

        return {'pan': pan, 'tilt': tilt}

    def gimbal_ctrl(self, x, y, speed=200, acceleration=10):
        """Alias used by BaseController interface."""
        return self.set_pan_tilt(x, y)

    # ------------------------------------------------------------------
    # LED lighting  →  /ugv/led_ctrl  (std_msgs/Float32MultiArray)
    # ------------------------------------------------------------------

    def set_lights(self, base_pwm, head_pwm):
        """
        Publish LED control to /ugv/led_ctrl.

        The ugv_driver node sends:
          {'T': 132, 'IO4': base_pwm, 'IO5': head_pwm}
        """
        base_pwm = max(0, min(255, int(base_pwm)))
        head_pwm = max(0, min(255, int(head_pwm)))

        led_msg = {
            'data': [float(base_pwm), float(head_pwm)],
        }

        self.bridge.publish(
            '/ugv/led_ctrl', 'std_msgs/Float32MultiArray', led_msg
        )

        self.base_light_status = base_pwm
        self.head_light_status = head_pwm

        return {'base': base_pwm, 'head': head_pwm}

    def lights_ctrl(self, base_pwm, head_pwm):
        """Alias used by BaseController interface."""
        return self.set_lights(base_pwm, head_pwm)

    # ------------------------------------------------------------------
    # Emergency stop
    # ------------------------------------------------------------------

    def lock_motor(self):
        """Emergency stop: publish zero velocity."""
        self.stop()
        self.left_speed = 0
        self.right_speed = 0
        return {'locked': True}

    def gimbal_emergency_stop(self):
        """Alias used by BaseController interface."""
        return self.lock_motor()

    def unlock_motor(self):
        """Resume motor control."""
        self.stop()
        return {'locked': False}

    # ------------------------------------------------------------------
    # JSON command routing
    # ------------------------------------------------------------------

    def send_json_command(self, data):
        """
        Route a JSON command by its T-type to the appropriate ROS2 topic.

        This handles the same command format that the frontend sends:
          T=1   → motor control  → /cmd_vel
          T=133 → gimbal         → /ugv/joint_states
          T=132 → LED            → /ugv/led_ctrl
          T=0   → emergency stop → /cmd_vel (zero)
        """
        cmd_type = data.get('T')

        if cmd_type == 1:
            # Motor: {T:1, L:left, R:right}
            left = data.get('L', 0)
            right = data.get('R', 0)
            return self.move(left, right)

        elif cmd_type == 133 or cmd_type == 134:
            # Gimbal: {T:133, X:pan, Y:tilt, SPD:speed, ACC:acc}
            pan = data.get('X', 0)
            tilt = data.get('Y', 0)
            return self.set_pan_tilt(pan, tilt)

        elif cmd_type == 132:
            # LED: {T:132, IO4:base, IO5:head}
            base = data.get('IO4', 0)
            head = data.get('IO5', 0)
            return self.set_lights(base, head)

        elif cmd_type == 0:
            # Emergency stop
            return self.lock_motor()

        else:
            # Unknown command type – log and skip
            logger.warning(f"ROS2: unhandled JSON command T={cmd_type}: {data}")
            return {'executed': False, 'reason': f'unknown T={cmd_type}'}

    def base_json_ctrl(self, input_json):
        """Alias used by BaseController interface."""
        return self.send_json_command(input_json)

    # ------------------------------------------------------------------
    # Servo control (pass-through, not critical for ROS2)
    # ------------------------------------------------------------------

    def bus_servo_id_set(self, old_id, new_id):
        logger.info(f"ROS2: servo ID set not supported (old={old_id}, new={new_id})")

    def bus_servo_torque_lock(self, servo_id, status):
        logger.info(f"ROS2: servo torque lock not supported (id={servo_id})")

    def bus_servo_mid_set(self, servo_id):
        logger.info(f"ROS2: servo mid set not supported (id={servo_id})")

    # ------------------------------------------------------------------
    # Feedback (subscribe to ROS2 status topics)
    # ------------------------------------------------------------------

    def subscribe_feedback(self):
        """Subscribe to /odom and voltage topics for feedback."""
        # This will be called after bridge is connected
        pass

    def feedback_data(self):
        """Return latest feedback data (compatible with BaseController)."""
        with self._feedback_lock:
            return self._feedback.copy() if self._feedback else {
                'T': 0, 'L': 0, 'R': 0, 'v': 0, 'pan': 0, 'tilt': 0
            }

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self):
        return {
            'left_speed': self.left_speed,
            'right_speed': self.right_speed,
            'pan_angle': self.pan_angle,
            'tilt_angle': self.tilt_angle,
            'mode': 'ros2',
            'connected': self.bridge.connected,
        }
