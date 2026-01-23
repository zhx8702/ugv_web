"""
Settings API Routes
配置管理 API 端点
"""
from flask import Blueprint, jsonify, request
from app.services.settings_service import get_settings_service
import logging

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')


@settings_bp.route('', methods=['GET'])
def get_settings():
    """
    获取所有配置

    Returns:
        JSON: {
            'base_config': {...},
            'args_config': {...},
            'video': {...},
            'user_preferences': {...}
        }
    """
    try:
        service = get_settings_service()
        settings = service.get_all()
        return jsonify(settings), 200
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({'error': str(e)}), 500


@settings_bp.route('', methods=['PUT'])
def update_settings():
    """
    更新所有配置

    Request JSON:
        {
            'base_config': {...},
            'args_config': {...},
            'video': {...},
            'user_preferences': {...}
        }

    Returns:
        JSON: {'success': bool}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        service = get_settings_service()
        success = service.update_all(data)

        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to save settings'}), 500
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/preferences', methods=['GET'])
def get_preferences():
    """
    获取用户偏好

    Returns:
        JSON: {
            'speed_mode': str,
            'head_light': str,
            'base_light': bool,
            ...
        }
    """
    try:
        service = get_settings_service()
        preferences = service.get_preferences()
        return jsonify(preferences), 200
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/preferences', methods=['PUT'])
def update_preferences():
    """
    更新用户偏好

    Request JSON:
        {
            'speed_mode': str,
            'head_light': str,
            ...
        }

    Returns:
        JSON: {'success': bool}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        service = get_settings_service()
        success = service.update_preferences(data)

        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to save preferences'}), 500
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/reset', methods=['POST'])
def reset_settings():
    """
    重置为默认配置

    Returns:
        JSON: {'success': bool}
    """
    try:
        service = get_settings_service()
        success = service.reset_to_defaults()

        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to reset settings'}), 500
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/video', methods=['GET'])
def get_video_config():
    """
    获取视频配置

    Returns:
        JSON: {
            'default_quality': int,
            'default_res_w': int,
            'default_res_h': int,
            'stream_type': str
        }
    """
    try:
        service = get_settings_service()
        video_config = service.get_video_config()
        return jsonify(video_config), 200
    except Exception as e:
        logger.error(f"Error getting video config: {e}")
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/speed', methods=['GET'])
def get_speed_config():
    """
    获取速度配置

    Returns:
        JSON: {
            'max_speed': float,
            'slow_speed': float,
            'mid_rate': float
        }
    """
    try:
        service = get_settings_service()
        speed_config = service.get_speed_config()
        return jsonify(speed_config), 200
    except Exception as e:
        logger.error(f"Error getting speed config: {e}")
        return jsonify({'error': str(e)}), 500
