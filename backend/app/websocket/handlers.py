# -*- coding: utf-8 -*-
"""
WebSocket Event Handlers
"""
from flask_socketio import emit
from flask import current_app
from app import socketio
from app.services.motor_control import MotorController
from app.services.system_monitor import SystemMonitor
from app.services.cv_service import get_cv_service
from app.services.audio_service import get_audio_service
import logging

# Initialize services
controller = MotorController()
monitor = SystemMonitor()
cv_service = get_cv_service()
audio_service = get_audio_service()

# Connected clients tracking
connected_clients = set()


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    from flask import request
    client_id = request.sid
    connected_clients.add(client_id)

    logging.info(f'Client connected: {client_id}')
    logging.info(f'Total connected clients: {len(connected_clients)}')

    # Send welcome message with config
    emit('config', {
        'robot_name': 'UGV Rover',
        'version': '2.0.0',
        'video_width': 640,
        'video_height': 480
    })

    # Send initial system status
    try:
        status = monitor.get_current_status()
        emit('feedback', status)
    except Exception as e:
        logging.error(f'Error sending initial status: {e}')

    # Play connection sound
    try:
        audio_service.play_random('connected')
        logging.info('Connection sound played')
    except Exception as e:
        logging.warning(f'Failed to play connection sound: {e}')


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    from flask import request
    client_id = request.sid

    if client_id in connected_clients:
        connected_clients.remove(client_id)

    logging.info(f'Client disconnected: {client_id}')
    logging.info(f'Total connected clients: {len(connected_clients)}')


@socketio.on('cmd_input')
def handle_cmd_input(data):
    """
    Handle code-based command input
    Data format: {
        'code': int,
        'val1': float,
        'val2': float
    }
    """
    try:
        code = data.get('code')
        val1 = data.get('val1', 0)
        val2 = data.get('val2', 0)

        logging.debug(f'Command received: code={code}, val1={val1}, val2={val2}')

        # CV模式命令 (10301-10309) 路由到 cv_service
        if 10301 <= code <= 10309:
            cv_service.set_mode(code)
            logging.info(f'CV mode set to: {code}')
            emit('cv_mode_changed', {
                'success': True,
                'mode': cv_service.cv_mode
            })
            return

        # CV反应模式命令 (10401-10403) 路由到 cv_service
        if 10401 <= code <= 10403:
            cv_service.set_reaction_mode(code)
            logging.info(f'CV reaction mode set to: {code}')
            emit('feedback', {
                'success': True,
                'code': code,
                'reaction_mode': cv_service.reaction_mode
            })
            return

        # 运动锁定命令 (10501=lock, 10502=unlock)
        if code == 10501:
            cv_service.set_motion_lock(True)
            logging.info('Motion lock enabled')
            emit('feedback', {'success': True, 'motion_lock': True})
            return
        if code == 10502:
            cv_service.set_motion_lock(False)
            logging.info('Motion lock disabled')
            emit('feedback', {'success': True, 'motion_lock': False})
            return

        # 其他命令发送到 motor controller
        result = controller.send_command(code, val1, val2)

        # Send feedback
        emit('feedback', {
            'success': True,
            'code': code,
            'result': result
        })

    except Exception as e:
        logging.error(f'Error handling cmd_input: {e}')
        emit('error', {'message': str(e)})


@socketio.on('json_cmd')
def handle_json_cmd(data):
    """
    Handle JSON command input
    Data format: {
        'T': int,      # Command type
        'L': float,    # Left motor
        'R': float,    # Right motor
        'X': float,    # Pan angle (optional)
        'Y': float,    # Tilt angle (optional)
        ...
    }
    """
    try:
        logging.debug(f'JSON command received: {data}')

        # Process command
        result = controller.send_json_command(data)

        # Send acknowledgement (optional)
        # emit('ack', {'success': True})

    except Exception as e:
        logging.error(f'Error handling json_cmd: {e}')
        emit('error', {'message': str(e)})


@socketio.on('ping')
def handle_ping():
    """Handle ping from client"""
    emit('pong')


@socketio.on('request_status')
def handle_request_status():
    """Handle status request from client"""
    try:
        status = monitor.get_current_status()
        emit('feedback', status)
    except Exception as e:
        logging.error(f'Error handling status request: {e}')
        emit('error', {'message': str(e)})


# ===================== CV视觉相关事件 =====================

@socketio.on('cv_mode')
def handle_cv_mode(data):
    """
    设置CV视觉模式
    Data format: {'mode': int}
    模式值:
        10301: CV_NONE
        10302: CV_MOTION
        10303: CV_FACE
        10304: CV_OBJECTS
        10305: CV_COLOR
        10306: MP_HAND
        10307: CV_AUTO
        10308: MP_FACE
        10309: MP_POSE
    """
    try:
        mode = data.get('mode')
        if mode is not None:
            cv_service.set_mode(int(mode))
            logging.info(f'CV mode set to: {mode}')
            emit('cv_mode_changed', {
                'success': True,
                'mode': cv_service.cv_mode
            })
        else:
            emit('error', {'message': 'Missing mode parameter'})
    except Exception as e:
        logging.error(f'Error setting CV mode: {e}')
        emit('error', {'message': str(e)})


@socketio.on('cv_motion_lock')
def handle_cv_motion_lock(data):
    """
    设置运动锁定（追踪开关）
    Data format: {'locked': bool}
    """
    try:
        locked = data.get('locked', True)
        cv_service.set_motion_lock(bool(locked))
        logging.debug(f'Motion lock set to: {locked}')
        emit('cv_motion_lock_changed', {
            'success': True,
            'motion_lock': cv_service.motion_lock
        })
    except Exception as e:
        logging.error(f'Error setting motion lock: {e}')
        emit('error', {'message': str(e)})


@socketio.on('cv_color_range')
def handle_cv_color_range(data):
    """
    设置颜色追踪的HSV范围
    Data format: {
        'lower': [h, s, v],
        'upper': [h, s, v]
    }
    """
    try:
        lower = data.get('lower')
        upper = data.get('upper')
        if lower and upper and len(lower) == 3 and len(upper) == 3:
            cv_service.set_color_range(lower, upper)
            logging.debug(f'Color range set: {lower} - {upper}')
            emit('cv_color_range_changed', {
                'success': True,
                'lower': cv_service.color_lower.tolist(),
                'upper': cv_service.color_upper.tolist()
            })
        else:
            emit('error', {'message': 'Invalid color range format'})
    except Exception as e:
        logging.error(f'Error setting color range: {e}')
        emit('error', {'message': str(e)})


@socketio.on('cv_reaction')
def handle_cv_reaction(data):
    """
    设置检测反应模式
    Data format: {'mode': int}
    模式值:
        10401: RE_NONE
        10402: RE_CAPTURE
        10403: RE_RECORD
    """
    try:
        mode = data.get('mode')
        if mode is not None:
            cv_service.set_reaction_mode(int(mode))
            logging.debug(f'Reaction mode set to: {mode}')
            emit('cv_reaction_changed', {
                'success': True,
                'reaction_mode': cv_service.reaction_mode
            })
        else:
            emit('error', {'message': 'Missing mode parameter'})
    except Exception as e:
        logging.error(f'Error setting reaction mode: {e}')
        emit('error', {'message': str(e)})


@socketio.on('cv_status')
def handle_cv_status():
    """获取CV服务状态"""
    try:
        status = cv_service.get_status()
        emit('cv_status', status)
    except Exception as e:
        logging.error(f'Error getting CV status: {e}')
        emit('error', {'message': str(e)})


# ===================== 音频相关事件 =====================

@socketio.on('audio_play')
def handle_audio_play(data):
    """
    播放音频文件
    Data format: {'file': str} 或 {'category': str}
    """
    try:
        filepath = data.get('file')
        category = data.get('category')

        if filepath:
            success = audio_service.play_file(filepath)
            emit('audio_play_result', {'success': success, 'file': filepath})
        elif category:
            success = audio_service.play_random(category)
            emit('audio_play_result', {'success': success, 'category': category})
        else:
            emit('error', {'message': 'Missing file or category parameter'})
    except Exception as e:
        logging.error(f'Error playing audio: {e}')
        emit('error', {'message': str(e)})


@socketio.on('audio_speak')
def handle_audio_speak(data):
    """
    TTS语音合成播放
    Data format: {'text': str}
    """
    try:
        text = data.get('text')
        if text:
            success = audio_service.speak(text)
            emit('audio_speak_result', {'success': success, 'text': text})
        else:
            emit('error', {'message': 'Missing text parameter'})
    except Exception as e:
        logging.error(f'Error speaking: {e}')
        emit('error', {'message': str(e)})


@socketio.on('audio_volume')
def handle_audio_volume(data):
    """
    设置音量
    Data format: {'volume': float} (0.0 - 1.0)
    """
    try:
        volume = data.get('volume')
        if volume is not None:
            success = audio_service.set_volume(float(volume))
            emit('audio_volume_changed', {
                'success': success,
                'volume': audio_service.volume
            })
        else:
            emit('error', {'message': 'Missing volume parameter'})
    except Exception as e:
        logging.error(f'Error setting volume: {e}')
        emit('error', {'message': str(e)})


@socketio.on('audio_stop')
def handle_audio_stop():
    """停止音频播放"""
    try:
        success = audio_service.stop()
        emit('audio_stop_result', {'success': success})
    except Exception as e:
        logging.error(f'Error stopping audio: {e}')
        emit('error', {'message': str(e)})


@socketio.on('audio_status')
def handle_audio_status():
    """获取音频服务状态"""
    try:
        status = audio_service.get_status()
        emit('audio_status', status)
    except Exception as e:
        logging.error(f'Error getting audio status: {e}')
        emit('error', {'message': str(e)})


def broadcast_system_status():
    """
    Broadcast system status to all connected clients
    This should be called periodically by a background task
    """
    if not connected_clients:
        return

    try:
        # Update FPS from video stream
        try:
            from app.services.video_stream import get_video_stream
            video_stream = get_video_stream()
            if video_stream and video_stream.running:
                monitor.update_fps(video_stream.fps)
        except Exception:
            pass

        # Update voltage from hardware controller
        try:
            from app.services.base_controller import get_base_controller
            base_ctrl = get_base_controller()
            if base_ctrl and not base_ctrl.mock_mode:
                feedback = base_ctrl.feedback_data()
                if feedback and 'v' in feedback:
                    # 下位机返回的电压单位是 cV (厘伏)，需要除以100转换为V
                    monitor.update_voltage(feedback['v'] / 100)
        except Exception:
            pass

        # Update RSSI from WiFi
        try:
            rssi = monitor.get_wifi_rssi()
            if rssi != 0:
                monitor.update_rssi(rssi)
        except Exception:
            pass

        status = monitor.get_feedback_array()
        # Use socketio.emit without broadcast parameter - it broadcasts by default
        socketio.emit('feedback', status)
    except Exception as e:
        logging.error(f'Error broadcasting system status: {e}')


def start_background_tasks(app):
    """
    Start background tasks for periodic updates
    """
    import threading
    import time

    def update_loop():
        """Background loop for sending system updates"""
        with app.app_context():
            while True:
                try:
                    if connected_clients:
                        broadcast_system_status()
                    time.sleep(0.1)  # Update every 100ms
                except Exception as e:
                    logging.error(f'Error in update loop: {e}')
                    time.sleep(1)

    # Start update thread
    update_thread = threading.Thread(target=update_loop, daemon=True)
    update_thread.start()
    logging.info('Background update task started')
