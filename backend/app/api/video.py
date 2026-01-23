"""
Video API Routes
视频流API端点
"""
from flask import Blueprint, Response, jsonify, request, current_app
from app.services.video_stream import get_video_stream
from app.services.webrtc_service import get_webrtc_service
import logging
import asyncio
import threading

logger = logging.getLogger(__name__)

# 全局事件循环（用于 WebRTC）
_webrtc_loop = None
_webrtc_thread = None


def get_webrtc_loop():
    """获取或创建 WebRTC 事件循环"""
    global _webrtc_loop, _webrtc_thread

    if _webrtc_loop is None or not _webrtc_loop.is_running():
        _webrtc_loop = asyncio.new_event_loop()

        def run_loop():
            asyncio.set_event_loop(_webrtc_loop)
            _webrtc_loop.run_forever()

        _webrtc_thread = threading.Thread(target=run_loop, daemon=True)
        _webrtc_thread.start()
        logger.info("WebRTC event loop started in background thread")

    return _webrtc_loop

video_bp = Blueprint('video', __name__, url_prefix='/api/video')


@video_bp.route('/stream')
def video_stream():
    """
    MJPEG视频流端点

    Returns:
        Response: multipart/x-mixed-replace格式的MJPEG流
    """
    try:
        stream = get_video_stream()

        return Response(
            stream.generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        logger.error(f'Video stream error: {e}')
        return jsonify({'error': str(e)}), 500


@video_bp.route('/status')
def get_status():
    """
    获取视频流状态

    Returns:
        JSON: 视频流状态信息
    """
    stream = get_video_stream()
    return jsonify(stream.get_status())


@video_bp.route('/capture', methods=['POST'])
def capture_photo():
    """
    拍照

    Returns:
        JSON: 拍照结果
    """
    try:
        stream = get_video_stream()
        stream.capture_photo()
        return jsonify({'success': True, 'message': 'Photo captured'})
    except Exception as e:
        logger.error(f'Photo capture error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@video_bp.route('/recording/start', methods=['POST'])
def start_recording():
    """
    开始录像

    Returns:
        JSON: 录像开始结果
    """
    try:
        stream = get_video_stream()
        success = stream.start_recording()
        if success:
            return jsonify({'success': True, 'message': 'Recording started'})
        else:
            return jsonify({'success': False, 'error': 'Failed to start recording'}), 500
    except Exception as e:
        logger.error(f'Start recording error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@video_bp.route('/recording/stop', methods=['POST'])
def stop_recording():
    """
    停止录像

    Returns:
        JSON: 录像停止结果
    """
    try:
        stream = get_video_stream()
        success = stream.stop_recording()
        if success:
            return jsonify({'success': True, 'message': 'Recording stopped'})
        else:
            return jsonify({'success': False, 'error': 'Not recording'}), 400
    except Exception as e:
        logger.error(f'Stop recording error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@video_bp.route('/zoom', methods=['POST'])
def set_zoom():
    """
    设置缩放倍率

    Request JSON:
        {
            "rate": 1|2|4
        }

    Returns:
        JSON: 缩放设置结果
    """
    try:
        data = request.get_json()
        rate = data.get('rate', 1)

        if rate not in [1, 2, 4]:
            return jsonify({'success': False, 'error': 'Invalid zoom rate'}), 400

        stream = get_video_stream()
        stream.set_zoom(rate)

        return jsonify({'success': True, 'zoom': rate})
    except Exception as e:
        logger.error(f'Set zoom error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@video_bp.route('/quality', methods=['POST'])
def set_quality():
    """
    设置视频质量

    Request JSON:
        {
            "quality": 1-100
        }

    Returns:
        JSON: 质量设置结果
    """
    try:
        data = request.get_json()
        quality = data.get('quality', 20)

        stream = get_video_stream()
        stream.set_quality(quality)

        return jsonify({'success': True, 'quality': stream.quality})
    except Exception as e:
        logger.error(f'Set quality error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@video_bp.route('/webrtc/offer', methods=['POST'])
def webrtc_offer():
    """
    WebRTC Offer处理

    Request JSON:
        {
            "sdp": "...",
            "type": "offer"
        }

    Returns:
        JSON: WebRTC Answer {sdp, type}
    """
    try:
        # 获取offer数据
        data = request.get_json()

        if not data or 'sdp' not in data or 'type' not in data:
            return jsonify({'error': 'Invalid offer data'}), 400

        # 获取WebRTC服务
        video_stream = get_video_stream()
        webrtc = get_webrtc_service(video_stream)

        if not webrtc.is_available():
            return jsonify({
                'error': 'WebRTC not available',
                'message': 'Please install aiortc: pip install aiortc'
            }), 503

        # 处理offer（使用持久事件循环）
        loop = get_webrtc_loop()

        # 在事件循环中执行异步操作
        import concurrent.futures
        future = asyncio.run_coroutine_threadsafe(webrtc.handle_offer(data), loop)

        try:
            # 等待结果（超时30秒）
            answer = future.result(timeout=30)
            logger.info(f"WebRTC offer processed successfully")
            return jsonify(answer)
        except concurrent.futures.TimeoutError:
            logger.error("WebRTC offer processing timeout")
            return jsonify({'error': 'WebRTC offer timeout'}), 504

    except Exception as e:
        logger.error(f'WebRTC offer error: {e}')
        return jsonify({'error': str(e)}), 500


@video_bp.route('/webrtc/status', methods=['GET'])
def webrtc_status():
    """
    获取WebRTC状态

    Returns:
        JSON: WebRTC服务状态
    """
    try:
        webrtc = get_webrtc_service()
        return jsonify(webrtc.get_stats())
    except Exception as e:
        logger.error(f'WebRTC status error: {e}')
        return jsonify({'error': str(e)}), 500


@video_bp.route('/timelapse/start', methods=['POST'])
def start_timelapse():
    """
    开始延时摄影

    Request JSON:
        {
            "speed": 0.5,         # 移动速度 (0-1)
            "move_time": 2,       # 移动时间（秒）
            "interval": 5,        # 拍照间隔（秒）
            "loop_times": 10      # 循环次数
        }

    Returns:
        JSON: 启动结果
    """
    try:
        data = request.get_json()
        speed = data.get('speed', 0.3)
        move_time = data.get('move_time', 2)
        interval = data.get('interval', 5)
        loop_times = data.get('loop_times', 10)

        stream = get_video_stream()
        success = stream.start_timelapse(speed, move_time, interval, loop_times)

        return jsonify({
            'success': success,
            'message': 'Timelapse started' if success else 'Failed to start timelapse'
        })

    except Exception as e:
        logger.error(f'Start timelapse error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@video_bp.route('/timelapse/stop', methods=['POST'])
def stop_timelapse():
    """
    停止延时摄影

    Returns:
        JSON: 停止结果
    """
    try:
        stream = get_video_stream()
        success = stream.stop_timelapse()

        return jsonify({
            'success': success,
            'message': 'Timelapse stopped' if success else 'No timelapse running'
        })

    except Exception as e:
        logger.error(f'Stop timelapse error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500
