"""
ROS2 API Blueprint

REST endpoints for ROS2 bridge status, SLAM control,
navigation, and vision features.
"""
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

ros2_bp = Blueprint('ros2', __name__, url_prefix='/api/ros2')


def _get_bridge():
    """Get the ROS2 bridge singleton (may be None if disabled)."""
    try:
        from app.services.ros2_bridge import get_ros2_bridge
        return get_ros2_bridge()
    except Exception:
        return None


# ------------------------------------------------------------------
# Bringup (LiDAR + driver) management
# ------------------------------------------------------------------

_CONTAINER = 'ugv_rpi_ros_humble'
_ENV_SETUP = (
    'export UGV_MODEL=ugv_rover && export LDLIDAR_MODEL=ld19 && '
    'source /opt/ros/humble/setup.bash && '
    'source /home/ws/ugv_ws/install/setup.bash'
)


def _is_bringup_running():
    """Check if the base bringup (LiDAR + driver) is running."""
    import subprocess
    try:
        result = subprocess.run(
            ['docker', 'exec', _CONTAINER, 'bash', '-c',
             'ps aux | grep -q "[l]dlidar" && echo yes || echo no'],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() == 'yes'
    except Exception:
        return False


def _start_bringup():
    """Start bringup_lidar (LiDAR + driver + odom) if not already running."""
    if _is_bringup_running():
        logger.info("Bringup already running, skipping")
        return True
    import subprocess
    try:
        cmd = [
            'docker', 'exec', '-d', _CONTAINER,
            'bash', '-c',
            f'{_ENV_SETUP} && ros2 launch ugv_bringup bringup_lidar.launch.py'
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info("Bringup started (LiDAR + driver)")
        return True
    except Exception as e:
        logger.error(f"Failed to start bringup: {e}")
        return False


def _stop_bringup():
    """Stop all bringup nodes (LiDAR motor stops spinning)."""
    import subprocess
    try:
        # Kill all major bringup processes
        for proc in ('ldlidar', 'ugv_driver', 'ugv_bringup', 'base_node',
                     'rf2o_laser_odometry', 'joint_state_publisher',
                     'robot_state_publisher', 'robot_pose_publisher'):
            subprocess.run(
                ['docker', 'exec', _CONTAINER, 'bash', '-c', f'pkill -f {proc}'],
                capture_output=True, timeout=5
            )
        logger.info("Bringup stopped")
        return True
    except Exception as e:
        logger.error(f"Failed to stop bringup: {e}")
        return False


@ros2_bp.route('/bringup/start', methods=['POST'])
def bringup_start():
    """Start the base bringup (LiDAR + driver)."""
    ok = _start_bringup()
    return jsonify({'status': 'started' if ok else 'already_running'})


@ros2_bp.route('/bringup/stop', methods=['POST'])
def bringup_stop():
    """Stop the base bringup (LiDAR motor stops)."""
    ok = _stop_bringup()
    return jsonify({'status': 'stopped' if ok else 'failed'})


@ros2_bp.route('/bringup/status', methods=['GET'])
def bringup_status():
    """Check if bringup is running."""
    return jsonify({'running': _is_bringup_running()})


# ------------------------------------------------------------------
# Connection status
# ------------------------------------------------------------------

@ros2_bp.route('/status', methods=['GET'])
def get_status():
    """Return ROS2 bridge connection status."""
    bridge = _get_bridge()
    if bridge is None:
        return jsonify({
            'enabled': False,
            'connected': False,
            'message': 'ROS2 bridge not initialized',
        })

    status = bridge.get_status()
    status['enabled'] = True
    return jsonify(status)


@ros2_bp.route('/reconnect', methods=['POST'])
def reconnect():
    """Force reconnect to rosbridge."""
    bridge = _get_bridge()
    if bridge is None:
        return jsonify({'error': 'ROS2 bridge not initialized'}), 503

    bridge.disconnect()
    success = bridge.connect()
    return jsonify({
        'connected': bridge.connected,
        'message': 'Reconnected' if success else 'Reconnection initiated',
    })


# ------------------------------------------------------------------
# ROS2 topics (for debugging / frontend discovery)
# ------------------------------------------------------------------

@ros2_bp.route('/topics', methods=['GET'])
def list_topics():
    """List available ROS2 topics via rosbridge."""
    bridge = _get_bridge()
    if bridge is None or not bridge.connected:
        return jsonify({'error': 'Not connected'}), 503

    try:
        result = bridge.client.get_topics()
        return jsonify({'topics': result})
    except Exception as e:
        logger.error(f"Failed to list topics: {e}")
        return jsonify({'error': str(e)}), 500


# ------------------------------------------------------------------
# SLAM control
# ------------------------------------------------------------------

@ros2_bp.route('/slam/start', methods=['POST'])
def slam_start():
    """Start SLAM mapping via docker exec into the ROS2 container."""
    data = request.get_json(silent=True) or {}
    algorithm = data.get('algorithm', 'cartographer')

    if algorithm not in ('cartographer', 'gmapping'):
        return jsonify({'error': f'Unknown algorithm: {algorithm}'}), 400

    try:
        import subprocess

        # Auto-start bringup (LiDAR + driver) if not running
        _start_bringup()

        if algorithm == 'cartographer':
            slam_cmd = 'ros2 launch cartographer mapping.launch.py'
        else:
            slam_cmd = 'ros2 launch slam_gmapping mapping.launch.py'

        # Launch robot_pose_publisher + SLAM algorithm
        # 注意：必须在每个后台命令前都 source 环境，否则 & 的 bash 优先级会导致环境丢失
        combined_cmd = (
            f'{_ENV_SETUP} && '
            f'ros2 launch robot_pose_publisher robot_pose_publisher_launch.py & '
            f'{_ENV_SETUP} && '
            f'{slam_cmd}'
        )

        cmd = ['docker', 'exec', '-d', _CONTAINER, 'bash', '-c', combined_cmd]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"SLAM started: {algorithm}")
        return jsonify({'status': 'started', 'algorithm': algorithm})

    except Exception as e:
        logger.error(f"Failed to start SLAM: {e}")
        return jsonify({'error': str(e)}), 500


@ros2_bp.route('/slam/stop', methods=['POST'])
def slam_stop():
    """Stop SLAM mapping by killing the SLAM nodes in the container."""
    try:
        import subprocess

        # Kill known SLAM processes
        for proc in ('cartographer_node', 'slam_gmapping', 'cartographer_occupancy_grid_node',
                     'robot_pose_publisher'):
            subprocess.run(
                ['docker', 'exec', _CONTAINER, 'bash', '-c', f'pkill -f {proc}'],
                capture_output=True, timeout=5
            )

        # Auto-stop bringup (LiDAR motor) when SLAM is done
        _stop_bringup()

        logger.info("SLAM stopped (bringup stopped)")
        return jsonify({'status': 'stopped'})

    except Exception as e:
        logger.error(f"Failed to stop SLAM: {e}")
        return jsonify({'error': str(e)}), 500


@ros2_bp.route('/slam/save', methods=['POST'])
def slam_save():
    """Save the current map using ros2 map_saver."""
    data = request.get_json(silent=True) or {}
    map_name = data.get('map_name', 'my_map')

    try:
        import subprocess
        save_path = f'/home/ws/ugv_ws/maps/{map_name}'

        cmd = [
            'docker', 'exec', _CONTAINER,
            'bash', '-c',
            f'{_ENV_SETUP} && '
            f'mkdir -p /home/ws/ugv_ws/maps && '
            f'ros2 run nav2_map_server map_saver_cli -f {save_path} --ros-args -p save_map_timeout:=10.0'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            logger.info(f"Map saved: {save_path}")
            return jsonify({
                'status': 'saved',
                'map_name': map_name,
                'path': save_path,
            })
        else:
            logger.error(f"Map save failed: {result.stderr}")
            return jsonify({'error': result.stderr or 'Map save failed'}), 500

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Map save timed out'}), 504
    except Exception as e:
        logger.error(f"Failed to save map: {e}")
        return jsonify({'error': str(e)}), 500


# ------------------------------------------------------------------
# Navigation (Nav2) control
# ------------------------------------------------------------------

@ros2_bp.route('/nav/start', methods=['POST'])
def nav_start():
    """Start Nav2 navigation stack."""
    data = request.get_json(silent=True) or {}
    algorithm = data.get('algorithm', 'teb')

    try:
        import subprocess

        # Nav2 needs bringup for LiDAR + odom
        _start_bringup()

        launch_cmd = 'ros2 launch ugv_nav navigation.launch.py'
        if algorithm == 'dwa':
            launch_cmd += ' planner:=dwa'

        cmd = [
            'docker', 'exec', '-d', _CONTAINER,
            'bash', '-c',
            f'{_ENV_SETUP} && {launch_cmd}'
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"Nav2 started: algorithm={algorithm}")
        return jsonify({'status': 'started', 'algorithm': algorithm})

    except Exception as e:
        logger.error(f"Failed to start Nav2: {e}")
        return jsonify({'error': str(e)}), 500


@ros2_bp.route('/nav/stop', methods=['POST'])
def nav_stop():
    """Stop Nav2 navigation stack."""
    try:
        import subprocess

        for proc in ('bt_navigator', 'controller_server', 'planner_server',
                     'behavior_server', 'lifecycle_manager_navigation'):
            subprocess.run(
                ['docker', 'exec', _CONTAINER, 'bash', '-c', f'pkill -f {proc}'],
                capture_output=True, timeout=5
            )

        # Auto-stop bringup when Nav2 is done
        _stop_bringup()

        logger.info("Nav2 stopped (bringup stopped)")
        return jsonify({'status': 'stopped'})

    except Exception as e:
        logger.error(f"Failed to stop Nav2: {e}")
        return jsonify({'error': str(e)}), 500


@ros2_bp.route('/nav/cancel', methods=['POST'])
def nav_cancel():
    """Cancel current navigation goal."""
    bridge = _get_bridge()
    if bridge is None or not bridge.connected:
        return jsonify({'error': 'Not connected'}), 503

    try:
        # Publish empty goal to cancel (or use action cancel)
        bridge.publish(
            '/goal_pose', 'geometry_msgs/PoseStamped',
            {
                'header': {'stamp': {'sec': 0, 'nanosec': 0}, 'frame_id': 'map'},
                'pose': {
                    'position': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                    'orientation': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0},
                },
            }
        )
        logger.info("Navigation cancelled")
        return jsonify({'status': 'cancelled'})
    except Exception as e:
        logger.error(f"Failed to cancel navigation: {e}")
        return jsonify({'error': str(e)}), 500


@ros2_bp.route('/nav/goto', methods=['POST'])
def nav_goto():
    """Navigate to a specific pose via rosbridge."""
    data = request.get_json(silent=True) or {}
    x = data.get('x', 0.0)
    y = data.get('y', 0.0)
    theta = data.get('theta', 0.0)

    bridge = _get_bridge()
    if bridge is None or not bridge.connected:
        return jsonify({'error': 'Not connected'}), 503

    import math
    goal = {
        'header': {'stamp': {'sec': 0, 'nanosec': 0}, 'frame_id': 'map'},
        'pose': {
            'position': {'x': float(x), 'y': float(y), 'z': 0.0},
            'orientation': {
                'x': 0.0,
                'y': 0.0,
                'z': math.sin(float(theta) / 2),
                'w': math.cos(float(theta) / 2),
            },
        },
    }
    bridge.publish('/goal_pose', 'geometry_msgs/PoseStamped', goal)
    logger.info(f"Nav goal published: x={x}, y={y}, theta={theta}")
    return jsonify({'status': 'navigating', 'goal': {'x': x, 'y': y, 'theta': theta}})


@ros2_bp.route('/nav/points', methods=['GET'])
def nav_get_points():
    """Get saved navigation waypoints."""
    import json
    import os
    points_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'nav_points.json')
    try:
        if os.path.exists(points_file):
            with open(points_file, 'r') as f:
                points = json.load(f)
        else:
            points = {}
        return jsonify({'points': points})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ros2_bp.route('/nav/points', methods=['POST'])
def nav_save_points():
    """Save navigation waypoints."""
    import json
    import os
    data = request.get_json(silent=True) or {}
    points_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'nav_points.json')
    try:
        os.makedirs(os.path.dirname(points_file), exist_ok=True)
        with open(points_file, 'w') as f:
            json.dump(data.get('points', {}), f, indent=2)
        return jsonify({'status': 'saved'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ------------------------------------------------------------------
# Vision tracking
# ------------------------------------------------------------------

@ros2_bp.route('/vision/start', methods=['POST'])
def vision_start():
    """Start AprilTag vision tracking node."""
    data = request.get_json(silent=True) or {}
    mode = data.get('mode', 'simple')
    target_id = data.get('target_id', 0)

    try:
        import subprocess

        launch_cmd = f'ros2 launch ugv_vision apriltag_tracking.launch.py mode:={mode} target_id:={target_id}'

        cmd = [
            'docker', 'exec', '-d', _CONTAINER,
            'bash', '-c',
            f'{_ENV_SETUP} && {launch_cmd}'
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"Vision tracking started: mode={mode}, target_id={target_id}")
        return jsonify({'status': 'started', 'mode': mode, 'target_id': target_id})

    except Exception as e:
        logger.error(f"Failed to start vision tracking: {e}")
        return jsonify({'error': str(e)}), 500


@ros2_bp.route('/vision/stop', methods=['POST'])
def vision_stop():
    """Stop vision tracking nodes."""
    try:
        import subprocess

        for proc in ('apriltag_node', 'apriltag_tracking', 'tag_following'):
            subprocess.run(
                ['docker', 'exec', _CONTAINER, 'bash', '-c', f'pkill -f {proc}'],
                capture_output=True, timeout=5
            )

        logger.info("Vision tracking stopped")
        return jsonify({'status': 'stopped'})

    except Exception as e:
        logger.error(f"Failed to stop vision tracking: {e}")
        return jsonify({'error': str(e)}), 500


# ------------------------------------------------------------------
# Behavior action
# ------------------------------------------------------------------

@ros2_bp.route('/behavior', methods=['POST'])
def send_behavior():
    """Send a behavior action to the robot via ROS2 topic."""
    data = request.get_json(silent=True) or {}
    action = data.get('action', '')

    bridge = _get_bridge()
    if bridge is None or not bridge.connected:
        return jsonify({'error': 'Not connected'}), 503

    if not action:
        return jsonify({'error': 'No action specified'}), 400

    try:
        # Publish behavior command to a String topic
        bridge.publish(
            '/behavior_command', 'std_msgs/String',
            {'data': action}
        )
        logger.info(f"Behavior action sent: {action}")
        return jsonify({'status': 'sent', 'action': action})

    except Exception as e:
        logger.error(f"Failed to send behavior: {e}")
        return jsonify({'error': str(e)}), 500


# ------------------------------------------------------------------
# FSD obstacle avoidance
# ------------------------------------------------------------------

def _get_fsd():
    try:
        from app.services.ros2_fsd_service import get_fsd_service
        return get_fsd_service()
    except Exception:
        return None


@ros2_bp.route('/fsd/start', methods=['POST'])
def fsd_start():
    """Start FSD obstacle avoidance."""
    fsd = _get_fsd()
    if fsd is None:
        return jsonify({'error': 'FSD service not available'}), 503

    data = request.get_json(silent=True) or {}
    config = {}
    for key in ('max_speed', 'safe_distance', 'warn_distance', 'turn_speed'):
        if key in data:
            config[key] = float(data[key])

    # Auto-start bringup (LiDAR + driver) — FSD needs /scan topic
    _start_bringup()

    ok = fsd.start(config or None)
    if ok:
        logger.info("FSD started via API (bringup auto-started)")
        return jsonify({'status': 'started', 'config': fsd.get_status()['config']})
    return jsonify({'error': 'Already running or failed to subscribe'}), 409


@ros2_bp.route('/fsd/stop', methods=['POST'])
def fsd_stop():
    """Stop FSD obstacle avoidance."""
    fsd = _get_fsd()
    if fsd is None:
        return jsonify({'error': 'FSD service not available'}), 503

    fsd.stop()

    # Auto-stop bringup (LiDAR motor) when FSD is done
    _stop_bringup()

    logger.info("FSD stopped via API (bringup stopped)")
    return jsonify({'status': 'stopped'})


@ros2_bp.route('/fsd/status', methods=['GET'])
def fsd_status():
    """Get FSD status (obstacles, decision, cmd)."""
    fsd = _get_fsd()
    if fsd is None:
        return jsonify({'running': False, 'error': 'FSD service not available'})
    return jsonify(fsd.get_status())


@ros2_bp.route('/fsd/config', methods=['POST'])
def fsd_config():
    """Update FSD parameters while running."""
    fsd = _get_fsd()
    if fsd is None:
        return jsonify({'error': 'FSD service not available'}), 503

    data = request.get_json(silent=True) or {}
    fsd.update_config(data)
    return jsonify({'status': 'updated', 'config': fsd.get_status()['config']})
