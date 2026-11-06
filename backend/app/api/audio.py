# -*- coding: utf-8 -*-
"""
Audio API Endpoints
音频控制API端点
"""
from flask import jsonify, request, current_app
from app.api import audio_bp
from app.services.audio_service import get_audio_service


@audio_bp.route('/files', methods=['GET'])
def get_files():
    """
    获取音频文件列表
    Query params:
        category: 可选，指定类别 (robot_started, connected, others)
    """
    try:
        category = request.args.get('category')
        files = get_audio_service().get_files(category)
        return jsonify({
            'success': True,
            'files': files,
            'count': len(files)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting audio files: {e}")
        return jsonify({'error': str(e)}), 500


@audio_bp.route('/play', methods=['POST'])
def play_file():
    """
    播放音频文件
    Body: {
        'file': str,    # 文件路径 (相对路径，如 'connected/hello.mp3')
    }
    """
    try:
        data = request.get_json()
        filepath = data.get('file')

        if not filepath:
            return jsonify({'error': 'Missing file parameter'}), 400

        success = get_audio_service().play_file(filepath)
        return jsonify({
            'success': success,
            'file': filepath
        }), 200 if success else 500

    except Exception as e:
        current_app.logger.error(f"Error playing audio: {e}")
        return jsonify({'error': str(e)}), 500


@audio_bp.route('/play-random', methods=['POST'])
def play_random():
    """
    播放指定类别的随机音频
    Body: {
        'category': str,  # 类别名 (robot_started, connected, others)
        'force': bool     # 可选，是否强制播放
    }
    """
    try:
        data = request.get_json()
        category = data.get('category')
        force = data.get('force', False)

        if not category:
            return jsonify({'error': 'Missing category parameter'}), 400

        success = get_audio_service().play_random(category, force)
        return jsonify({
            'success': success,
            'category': category
        }), 200 if success else 500

    except Exception as e:
        current_app.logger.error(f"Error playing random audio: {e}")
        return jsonify({'error': str(e)}), 500


@audio_bp.route('/speak', methods=['POST'])
def speak():
    """
    TTS语音合成
    Body: {
        'text': str  # 要朗读的文本
    }
    """
    try:
        data = request.get_json()
        text = data.get('text')

        if not text:
            return jsonify({'error': 'Missing text parameter'}), 400

        audio_service = get_audio_service()
        interrupt = bool(data.get('interrupt', False))
        success = audio_service.speak(text, interrupt=interrupt)
        status = audio_service.get_status()
        if not success:
            reason = 'TTS not available' if not status.get('tts_available') else 'Audio queue full'
            return jsonify({
                'success': False,
                'text': text,
                'error': reason,
                'tts_available': status.get('tts_available'),
                'tts_engine': status.get('tts_engine')
            }), 503
        return jsonify({
            'success': True,
            'text': text,
            'queued': True,
            'tts_engine': status.get('tts_engine'),
            'queue_size': status.get('queue_size', 0)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in TTS: {e}")
        return jsonify({'error': str(e)}), 500


@audio_bp.route('/stop', methods=['POST'])
def stop():
    """停止当前播放"""
    try:
        success = get_audio_service().stop()
        return jsonify({'success': success}), 200

    except Exception as e:
        current_app.logger.error(f"Error stopping audio: {e}")
        return jsonify({'error': str(e)}), 500


@audio_bp.route('/volume', methods=['GET'])
def get_volume():
    """获取当前音量"""
    try:
        return jsonify({
            'success': True,
            'volume': get_audio_service().volume
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting volume: {e}")
        return jsonify({'error': str(e)}), 500


@audio_bp.route('/volume', methods=['POST'])
def set_volume():
    """
    设置音量
    Body: {
        'volume': float  # 音量值 (0.0-1.0)
    }
    """
    try:
        data = request.get_json()
        volume = data.get('volume')

        if volume is None:
            return jsonify({'error': 'Missing volume parameter'}), 400

        audio_service = get_audio_service()
        success = audio_service.set_volume(float(volume))
        return jsonify({
            'success': success,
            'volume': audio_service.volume
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error setting volume: {e}")
        return jsonify({'error': str(e)}), 500


@audio_bp.route('/status', methods=['GET'])
def get_status():
    """获取音频服务状态"""
    try:
        status = get_audio_service().get_status()
        return jsonify({
            'success': True,
            **status
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting audio status: {e}")
        return jsonify({'error': str(e)}), 500
