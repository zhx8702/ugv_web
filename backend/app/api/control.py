"""
Robot Control API Endpoints
"""
from flask import jsonify, request, current_app
from app.api import control_bp
from app.services.motor_control import MotorController

# Initialize motor controller (singleton pattern)
controller = MotorController()


@control_bp.route('/command', methods=['POST'])
def send_command():
    """
    Send control command
    Body: {
        'code': int,
        'val1': float (optional),
        'val2': float (optional)
    }
    """
    try:
        data = request.get_json()
        code = data.get('code')
        val1 = data.get('val1', 0)
        val2 = data.get('val2', 0)

        if code is None:
            return jsonify({'error': 'Missing code parameter'}), 400

        result = controller.send_command(code, val1, val2)
        return jsonify({'success': True, 'result': result}), 200

    except Exception as e:
        current_app.logger.error(f"Error sending command: {e}")
        return jsonify({'error': str(e)}), 500


@control_bp.route('/json_command', methods=['POST'])
def send_json_command():
    """
    Send JSON control command
    Body: {
        'T': int,     # Command type
        'L': float,   # Left motor
        'R': float,   # Right motor
        ...
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Missing command data'}), 400

        result = controller.send_json_command(data)
        return jsonify({'success': True, 'result': result}), 200

    except Exception as e:
        current_app.logger.error(f"Error sending JSON command: {e}")
        return jsonify({'error': str(e)}), 500



@control_bp.route('/feedback', methods=['GET'])
def get_hardware_feedback():
    """Return the latest cached feedback without reading the UART again."""
    base = controller.base_controller
    feedback = base.base_data.copy() if base else {}
    voltage_cv = feedback.get('v')
    voltage = voltage_cv / 100 if isinstance(voltage_cv, (int, float)) and voltage_cv > 0 else None
    return jsonify({'success': True, 'feedback': feedback, 'voltage': voltage}), 200
@control_bp.route('/move', methods=['POST'])
def move_robot():
    """
    Move robot with left/right motor speeds
    Body: {
        'left': float,   # -1.0 to 1.0
        'right': float   # -1.0 to 1.0
    }
    """
    try:
        data = request.get_json()
        left = data.get('left', 0)
        right = data.get('right', 0)

        result = controller.move(left, right)
        return jsonify({'success': True, 'result': result}), 200

    except Exception as e:
        current_app.logger.error(f"Error moving robot: {e}")
        return jsonify({'error': str(e)}), 500


@control_bp.route('/stop', methods=['POST'])
def stop_robot():
    """Stop robot movement"""
    try:
        result = controller.stop()
        return jsonify({'success': True, 'result': result}), 200

    except Exception as e:
        current_app.logger.error(f"Error stopping robot: {e}")
        return jsonify({'error': str(e)}), 500


@control_bp.route('/pt', methods=['POST'])
def control_pan_tilt():
    """
    Control pan-tilt gimbal
    Body: {
        'pan': float,   # Pan angle
        'tilt': float   # Tilt angle
    }
    """
    try:
        data = request.get_json()
        pan = data.get('pan', 0)
        tilt = data.get('tilt', 0)

        result = controller.set_pan_tilt(pan, tilt)
        return jsonify({'success': True, 'result': result}), 200

    except Exception as e:
        current_app.logger.error(f"Error controlling PT: {e}")
        return jsonify({'error': str(e)}), 500


# ========== 灯光控制 ==========

@control_bp.route('/light', methods=['POST'])
def control_lights():
    """
    Control LED lights
    Body: {
        'base': int,   # Base light PWM (0-255)
        'head': int    # Head light PWM (0-255)
    }
    """
    try:
        data = request.get_json()
        base_pwm = data.get('base', 0)
        head_pwm = data.get('head', 0)

        result = controller.set_lights(base_pwm, head_pwm)
        return jsonify({'success': True, 'result': result}), 200

    except Exception as e:
        current_app.logger.error(f"Error controlling lights: {e}")
        return jsonify({'error': str(e)}), 500


@control_bp.route('/light/status', methods=['GET'])
def get_light_status():
    """Get current light status"""
    try:
        status = controller.get_light_status()
        return jsonify({'success': True, **status}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting light status: {e}")
        return jsonify({'error': str(e)}), 500


# ========== 电机锁定控制 ==========

@control_bp.route('/motor/lock', methods=['POST'])
def lock_motor():
    """Lock motors (emergency stop)"""
    try:
        result = controller.lock_motor()
        return jsonify({'success': True, 'locked': True}), 200

    except Exception as e:
        current_app.logger.error(f"Error locking motor: {e}")
        return jsonify({'error': str(e)}), 500


@control_bp.route('/motor/unlock', methods=['POST'])
def unlock_motor():
    """Unlock motors"""
    try:
        result = controller.unlock_motor()
        return jsonify({'success': True, 'locked': False}), 200

    except Exception as e:
        current_app.logger.error(f"Error unlocking motor: {e}")
        return jsonify({'error': str(e)}), 500


# ========== 舵机配置 ==========

@control_bp.route('/servo/id', methods=['POST'])
def set_servo_id():
    """
    Set servo ID
    Body: {
        'old_id': int,   # Current servo ID
        'new_id': int    # New servo ID
    }
    """
    try:
        data = request.get_json()
        old_id = data.get('old_id')
        new_id = data.get('new_id')

        if old_id is None or new_id is None:
            return jsonify({'error': 'Missing old_id or new_id'}), 400

        result = controller.set_servo_id(old_id, new_id)
        return jsonify({'success': True, 'result': result}), 200

    except Exception as e:
        current_app.logger.error(f"Error setting servo ID: {e}")
        return jsonify({'error': str(e)}), 500


@control_bp.route('/servo/torque', methods=['POST'])
def set_servo_torque():
    """
    Set servo torque lock
    Body: {
        'id': int,      # Servo ID
        'lock': bool    # True to lock, False to unlock
    }
    """
    try:
        data = request.get_json()
        servo_id = data.get('id')
        lock = data.get('lock', True)

        if servo_id is None:
            return jsonify({'error': 'Missing servo id'}), 400

        result = controller.set_servo_torque(servo_id, 1 if lock else 0)
        return jsonify({'success': True, 'result': result}), 200

    except Exception as e:
        current_app.logger.error(f"Error setting servo torque: {e}")
        return jsonify({'error': str(e)}), 500


@control_bp.route('/servo/mid', methods=['POST'])
def set_servo_mid():
    """
    Set servo middle position
    Body: {
        'id': int   # Servo ID
    }
    """
    try:
        data = request.get_json()
        servo_id = data.get('id')

        if servo_id is None:
            return jsonify({'error': 'Missing servo id'}), 400

        result = controller.set_servo_mid(servo_id)
        return jsonify({'success': True, 'result': result}), 200

    except Exception as e:
        current_app.logger.error(f"Error setting servo mid: {e}")
        return jsonify({'error': str(e)}), 500


@control_bp.route('/servo/release', methods=['POST'])
def release_servo():
    """
    Release servo (unlock torque for all servos)
    Body: {
        'id': int   # Servo ID (optional, release all if not provided)
    }
    """
    try:
        data = request.get_json() or {}
        servo_id = data.get('id')

        result = controller.release_servo(servo_id)
        return jsonify({'success': True, 'result': result}), 200

    except Exception as e:
        current_app.logger.error(f"Error releasing servo: {e}")
        return jsonify({'error': str(e)}), 500
