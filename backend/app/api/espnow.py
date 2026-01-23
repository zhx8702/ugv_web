"""
ESP-NOW Multi-Robot Collaboration API
ESP-NOW多机协作API端点
"""
from flask import Blueprint, jsonify, request
from app.services.espnow_service import get_espnow_service
import logging

logger = logging.getLogger(__name__)

espnow_bp = Blueprint('espnow', __name__, url_prefix='/api/espnow')


@espnow_bp.route('/start', methods=['POST'])
def start_service():
    """
    启动ESP-NOW服务

    Returns:
        JSON: 启动结果
    """
    try:
        espnow = get_espnow_service()
        success = espnow.start()

        return jsonify({
            'success': success,
            'message': 'ESP-NOW service started' if success else 'Failed to start'
        })

    except Exception as e:
        logger.error(f'Start ESP-NOW error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@espnow_bp.route('/stop', methods=['POST'])
def stop_service():
    """
    停止ESP-NOW服务

    Returns:
        JSON: 停止结果
    """
    try:
        espnow = get_espnow_service()
        success = espnow.stop()

        return jsonify({
            'success': success,
            'message': 'ESP-NOW service stopped' if success else 'Service not running'
        })

    except Exception as e:
        logger.error(f'Stop ESP-NOW error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@espnow_bp.route('/status', methods=['GET'])
def get_status():
    """
    获取ESP-NOW服务状态

    Returns:
        JSON: 服务状态
    """
    try:
        espnow = get_espnow_service()
        status = espnow.get_status()

        return jsonify(status)

    except Exception as e:
        logger.error(f'Get ESP-NOW status error: {e}')
        return jsonify({'error': str(e)}), 500


@espnow_bp.route('/discover', methods=['POST'])
def discover():
    """
    发现其他机器人

    Returns:
        JSON: 发现请求结果
    """
    try:
        espnow = get_espnow_service()
        espnow.discover()

        return jsonify({
            'success': True,
            'message': 'Discovery message broadcasted'
        })

    except Exception as e:
        logger.error(f'Discovery error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@espnow_bp.route('/robots', methods=['GET'])
def get_robots():
    """
    获取所有已发现的机器人

    Returns:
        JSON: 机器人列表
    """
    try:
        espnow = get_espnow_service()
        robots = espnow.get_robots()

        return jsonify({
            'robots': robots,
            'count': len(robots)
        })

    except Exception as e:
        logger.error(f'Get robots error: {e}')
        return jsonify({'error': str(e)}), 500


@espnow_bp.route('/role', methods=['POST'])
def set_role():
    """
    设置机器人角色

    Request JSON:
        {
            "role": "standalone"|"leader"|"follower"
        }

    Returns:
        JSON: 设置结果
    """
    try:
        data = request.get_json()
        role = data.get('role')

        if not role:
            return jsonify({'success': False, 'error': 'Role is required'}), 400

        espnow = get_espnow_service()
        success = espnow.set_role(role)

        return jsonify({
            'success': success,
            'role': role if success else None,
            'message': f'Role set to {role}' if success else 'Invalid role'
        })

    except Exception as e:
        logger.error(f'Set role error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@espnow_bp.route('/command', methods=['POST'])
def broadcast_command():
    """
    广播控制命令（仅领导者）

    Request JSON:
        {
            "command": {
                "T": 1,
                "L": 0.5,
                "R": 0.5
            }
        }

    Returns:
        JSON: 广播结果
    """
    try:
        data = request.get_json()
        command = data.get('command')

        if not command:
            return jsonify({'success': False, 'error': 'Command is required'}), 400

        espnow = get_espnow_service()
        success = espnow.broadcast_command(command)

        return jsonify({
            'success': success,
            'message': 'Command broadcasted' if success else 'Only leader can broadcast commands'
        })

    except Exception as e:
        logger.error(f'Broadcast command error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@espnow_bp.route('/formation', methods=['POST'])
def set_formation():
    """
    设置编队类型

    Request JSON:
        {
            "formation_type": "line"|"triangle"|"square"|"circle",
            "spacing": 1.0  # 编队间距（米）
        }

    Returns:
        JSON: 设置结果
    """
    try:
        data = request.get_json()
        formation_type = data.get('formation_type')
        spacing = data.get('spacing', 1.0)

        if not formation_type:
            return jsonify({'success': False, 'error': 'Formation type is required'}), 400

        espnow = get_espnow_service()
        success = espnow.set_formation(formation_type, spacing)

        return jsonify({
            'success': success,
            'formation_type': formation_type if success else None,
            'spacing': spacing if success else None,
            'message': f'Formation set to {formation_type}' if success else 'Invalid formation type'
        })

    except Exception as e:
        logger.error(f'Set formation error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@espnow_bp.route('/heartbeat/interval', methods=['POST'])
def set_heartbeat_interval():
    """
    设置心跳间隔

    Request JSON:
        {
            "interval": 2.0  # 秒
        }

    Returns:
        JSON: 设置结果
    """
    try:
        data = request.get_json()
        interval = data.get('interval')

        if not interval or interval < 0.5 or interval > 60:
            return jsonify({
                'success': False,
                'error': 'Invalid interval (must be between 0.5 and 60 seconds)'
            }), 400

        espnow = get_espnow_service()
        espnow.heartbeat_interval = interval

        return jsonify({
            'success': True,
            'interval': interval,
            'message': f'Heartbeat interval set to {interval}s'
        })

    except Exception as e:
        logger.error(f'Set heartbeat interval error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500
