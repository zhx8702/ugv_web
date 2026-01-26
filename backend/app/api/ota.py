"""
OTA API Routes
OTA升级API端点
"""
from flask import Blueprint, jsonify, request
from app.services.ota_service import get_ota_service
from app import socketio
import logging

logger = logging.getLogger(__name__)

ota_bp = Blueprint('ota', __name__, url_prefix='/api/ota')


@ota_bp.route('/version')
def get_version():
    """
    获取当前版本信息

    Returns:
        JSON: {
            'version': 'v2.0.0',
            'sbc_version': '2.0.0',
            'git_hash': 'abc1234',
            'git_branch': 'main',
            'last_update': '2026-01-20 10:30:00 +0800'
        }
    """
    ota = get_ota_service()
    return jsonify(ota.get_version_info())


@ota_bp.route('/check-update')
def check_update():
    """
    检查更新

    Returns:
        JSON: {
            'has_update': bool,
            'current_version': str,
            'latest_version': str,
            'commits_behind': int,
            'changelog': list  # 更新日志
        }
    """
    try:
        ota = get_ota_service()
        result = ota.check_update()

        # 如果有更新，获取 changelog
        if result.get('has_update'):
            commits = ota.get_update_log(limit=result.get('commits_behind', 5))
            result['changelog'] = [c['message'] for c in commits]
        else:
            result['changelog'] = []

        return jsonify(result)
    except Exception as e:
        logger.error(f'Check update error: {e}')
        return jsonify({'error': str(e)}), 500


@ota_bp.route('/update-log')
def get_update_log():
    """
    获取更新日志

    Query Params:
        limit: 获取commit数量 (默认10)

    Returns:
        JSON: {
            'commits': [
                {
                    'hash': 'abc123',
                    'author': 'Author',
                    'date': '2 days ago',
                    'message': 'Commit message'
                }
            ]
        }
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        ota = get_ota_service()
        commits = ota.get_update_log(limit)
        return jsonify({'commits': commits})
    except Exception as e:
        logger.error(f'Get update log error: {e}')
        return jsonify({'error': str(e)}), 500


@ota_bp.route('/perform-update', methods=['POST'])
def perform_update():
    """
    执行OTA更新

    Returns:
        JSON: {'success': bool, 'message': str}
    """
    try:
        ota = get_ota_service()

        if ota.updating:
            return jsonify({
                'success': False,
                'error': 'Update already in progress'
            }), 409

        # 定义进度回调函数（通过WebSocket发送）
        def progress_callback(step, progress, message):
            socketio.emit('ota_progress', {
                'step': step,
                'progress': progress,
                'message': message
            })

        # 启动更新
        success = ota.perform_update(progress_callback)

        if success:
            return jsonify({
                'success': True,
                'message': 'Update started'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to start update'
            }), 500

    except Exception as e:
        logger.error(f'Perform update error: {e}')
        return jsonify({'error': str(e)}), 500


@ota_bp.route('/backups')
def get_backups():
    """
    获取备份列表

    Returns:
        JSON: {
            'backups': [
                {
                    'name': 'backup-v2.0.0-20260121-143045',
                    'version': 'v2.0.0',
                    'date': '20260121',
                    'time': '143045',
                    'size': 150  // MB
                }
            ]
        }
    """
    try:
        ota = get_ota_service()
        backups = ota.get_backups()
        return jsonify({'backups': backups})
    except Exception as e:
        logger.error(f'Get backups error: {e}')
        return jsonify({'error': str(e)}), 500


@ota_bp.route('/rollback', methods=['POST'])
def rollback():
    """
    回滚到指定备份

    Request JSON:
        {
            "backup_name": "backup-v2.0.0-20260121-143045"
        }

    Returns:
        JSON: {'success': bool, 'message': str}
    """
    try:
        data = request.get_json()
        backup_name = data.get('backup_name')

        if not backup_name:
            return jsonify({
                'success': False,
                'error': 'backup_name required'
            }), 400

        ota = get_ota_service()
        result = ota.rollback(backup_name)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f'Rollback error: {e}')
        return jsonify({'error': str(e)}), 500


@ota_bp.route('/status')
def get_status():
    """
    获取OTA状态

    Returns:
        JSON: {
            'updating': bool,
            'current_version': str,
            'repo_dir': str,
            'service_name': str
        }
    """
    ota = get_ota_service()
    return jsonify(ota.get_status())
