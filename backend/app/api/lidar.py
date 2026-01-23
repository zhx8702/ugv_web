"""
LiDAR API Routes
LiDAR控制和数据API端点
"""
from flask import Blueprint, jsonify, request
from app.services.lidar_service import get_lidar_service
import logging

logger = logging.getLogger(__name__)

lidar_bp = Blueprint('lidar', __name__, url_prefix='/api/lidar')


@lidar_bp.route('/start', methods=['POST'])
def start_lidar():
    """
    启动LiDAR读取

    Returns:
        JSON: 启动结果
    """
    try:
        lidar = get_lidar_service()
        success = lidar.start()

        return jsonify({
            'success': success,
            'message': 'LiDAR started' if success else 'Failed to start LiDAR'
        })

    except Exception as e:
        logger.error(f'Start LiDAR error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@lidar_bp.route('/stop', methods=['POST'])
def stop_lidar():
    """
    停止LiDAR读取

    Returns:
        JSON: 停止结果
    """
    try:
        lidar = get_lidar_service()
        success = lidar.stop()

        return jsonify({
            'success': success,
            'message': 'LiDAR stopped' if success else 'LiDAR not running'
        })

    except Exception as e:
        logger.error(f'Stop LiDAR error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@lidar_bp.route('/status', methods=['GET'])
def get_status():
    """
    获取LiDAR状态

    Returns:
        JSON: 状态信息
    """
    try:
        lidar = get_lidar_service()
        status = lidar.get_status()

        return jsonify(status)

    except Exception as e:
        logger.error(f'Get LiDAR status error: {e}')
        return jsonify({'error': str(e)}), 500


@lidar_bp.route('/data', methods=['GET'])
def get_data():
    """
    获取LiDAR数据

    Returns:
        JSON: {
            'angles': [float],
            'distances': [float],
            'count': int
        }
    """
    try:
        lidar = get_lidar_service()
        data = lidar.get_data()

        return jsonify(data)

    except Exception as e:
        logger.error(f'Get LiDAR data error: {e}')
        return jsonify({'error': str(e)}), 500


@lidar_bp.route('/overlay', methods=['POST'])
def set_overlay():
    """
    设置视频叠加

    Request JSON:
        {
            "enabled": true|false
        }

    Returns:
        JSON: 设置结果
    """
    try:
        data = request.get_json()
        enabled = data.get('enabled', True)

        lidar = get_lidar_service()
        lidar.enable_overlay(enabled)

        return jsonify({
            'success': True,
            'overlay_enabled': enabled
        })

    except Exception as e:
        logger.error(f'Set overlay error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@lidar_bp.route('/config', methods=['POST'])
def set_config():
    """
    设置LiDAR可视化配置

    Request JSON:
        {
            "max_distance": 600,        # 最大显示距离（厘米）
            "point_color": [0, 255, 0], # BGR格式
            "line_color": [0, 255, 255] # BGR格式
        }

    Returns:
        JSON: 设置结果
    """
    try:
        data = request.get_json()

        max_distance = data.get('max_distance')
        point_color = data.get('point_color')
        line_color = data.get('line_color')

        # 转换颜色格式
        if point_color and isinstance(point_color, list) and len(point_color) == 3:
            point_color = tuple(point_color)
        else:
            point_color = None

        if line_color and isinstance(line_color, list) and len(line_color) == 3:
            line_color = tuple(line_color)
        else:
            line_color = None

        lidar = get_lidar_service()
        lidar.set_config(
            max_distance=max_distance,
            point_color=point_color,
            line_color=line_color
        )

        return jsonify({
            'success': True,
            'message': 'Config updated'
        })

    except Exception as e:
        logger.error(f'Set config error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500
