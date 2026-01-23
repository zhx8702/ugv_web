# -*- coding: utf-8 -*-
"""
CV Vision API Endpoints
计算机视觉API端点
"""
from flask import jsonify, request, current_app
from app.api import cv_bp
from app.services.cv_service import get_cv_service

# 获取CV服务单例
cv_service = get_cv_service()


@cv_bp.route('/mode', methods=['GET'])
def get_mode():
    """获取当前CV模式"""
    try:
        return jsonify({
            'success': True,
            'mode': cv_service.cv_mode
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting CV mode: {e}")
        return jsonify({'error': str(e)}), 500


@cv_bp.route('/mode', methods=['POST'])
def set_mode():
    """
    设置CV模式
    Body: { 'mode': int }
    模式值:
        10301: CV_NONE (无)
        10302: CV_MOTION (运动检测)
        10303: CV_FACE (人脸检测)
        10304: CV_OBJECTS (物体检测)
        10305: CV_COLOR (颜色追踪)
        10306: MP_HAND (手势识别)
        10307: CV_AUTO (巡线自动驾驶)
        10308: MP_FACE (MediaPipe人脸)
        10309: MP_POSE (MediaPipe姿态)
    """
    try:
        data = request.get_json()
        mode = data.get('mode')

        if mode is None:
            return jsonify({'error': 'Missing mode parameter'}), 400

        cv_service.set_mode(int(mode))
        return jsonify({
            'success': True,
            'mode': cv_service.cv_mode
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error setting CV mode: {e}")
        return jsonify({'error': str(e)}), 500


@cv_bp.route('/reaction', methods=['POST'])
def set_reaction():
    """
    设置检测反应模式
    Body: { 'mode': int }
    模式值:
        10401: RE_NONE (无反应)
        10402: RE_CAPTURE (拍照)
        10403: RE_RECORD (录像)
    """
    try:
        data = request.get_json()
        mode = data.get('mode')

        if mode is None:
            return jsonify({'error': 'Missing mode parameter'}), 400

        cv_service.set_reaction_mode(int(mode))
        return jsonify({
            'success': True,
            'reaction_mode': cv_service.reaction_mode
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error setting reaction mode: {e}")
        return jsonify({'error': str(e)}), 500


@cv_bp.route('/motion-lock', methods=['POST'])
def set_motion_lock():
    """
    设置运动锁定（追踪开关）
    Body: { 'locked': bool }
    locked=true: 锁定，不追踪
    locked=false: 解锁，启用追踪
    """
    try:
        data = request.get_json()
        locked = data.get('locked', True)

        cv_service.set_motion_lock(bool(locked))
        return jsonify({
            'success': True,
            'motion_lock': cv_service.motion_lock
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error setting motion lock: {e}")
        return jsonify({'error': str(e)}), 500


@cv_bp.route('/color-range', methods=['POST'])
def set_color_range():
    """
    设置颜色检测范围（HSV）
    Body: {
        'lower': [h, s, v],
        'upper': [h, s, v]
    }
    """
    try:
        data = request.get_json()
        lower = data.get('lower')
        upper = data.get('upper')

        if lower is None or upper is None:
            return jsonify({'error': 'Missing lower or upper parameter'}), 400

        if len(lower) != 3 or len(upper) != 3:
            return jsonify({'error': 'HSV values must be [h, s, v]'}), 400

        cv_service.set_color_range(lower, upper)
        return jsonify({
            'success': True,
            'color_lower': cv_service.color_lower.tolist(),
            'color_upper': cv_service.color_upper.tolist()
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error setting color range: {e}")
        return jsonify({'error': str(e)}), 500


@cv_bp.route('/line-color', methods=['POST'])
def set_line_color():
    """
    设置巡线颜色范围（HSV）
    Body: {
        'lower': [h, s, v],
        'upper': [h, s, v]
    }
    """
    try:
        data = request.get_json()
        lower = data.get('lower')
        upper = data.get('upper')

        if lower is None or upper is None:
            return jsonify({'error': 'Missing lower or upper parameter'}), 400

        if len(lower) != 3 or len(upper) != 3:
            return jsonify({'error': 'HSV values must be [h, s, v]'}), 400

        cv_service.set_line_color(lower, upper)
        return jsonify({
            'success': True,
            'line_lower': cv_service.line_lower.tolist(),
            'line_upper': cv_service.line_upper.tolist()
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error setting line color: {e}")
        return jsonify({'error': str(e)}), 500


@cv_bp.route('/track-params', methods=['POST'])
def set_track_params():
    """
    设置追踪参数
    Body: {
        'track_spd_rate': float,      # 追踪速度系数
        'track_acc_rate': float,      # 追踪加速度系数
        'aimed_error': float,         # 目标误差阈值
        'track_faces_iterate': float, # 人脸追踪步长
        'track_color_iterate': float  # 颜色追踪步长
    }
    """
    try:
        data = request.get_json()

        if 'track_spd_rate' in data:
            cv_service.track_spd_rate = float(data['track_spd_rate'])
        if 'track_acc_rate' in data:
            cv_service.track_acc_rate = float(data['track_acc_rate'])
        if 'aimed_error' in data:
            cv_service.aimed_error = float(data['aimed_error'])
        if 'track_faces_iterate' in data:
            cv_service.track_faces_iterate = float(data['track_faces_iterate'])
        if 'track_color_iterate' in data:
            cv_service.track_color_iterate = float(data['track_color_iterate'])

        return jsonify({
            'success': True,
            'track_spd_rate': cv_service.track_spd_rate,
            'track_acc_rate': cv_service.track_acc_rate,
            'aimed_error': cv_service.aimed_error,
            'track_faces_iterate': cv_service.track_faces_iterate,
            'track_color_iterate': cv_service.track_color_iterate
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error setting track params: {e}")
        return jsonify({'error': str(e)}), 500


@cv_bp.route('/line-params', methods=['POST'])
def set_line_params():
    """
    设置巡线参数
    Body: {
        'sampling_line_1': float,  # 采样线1位置 (0-1)
        'sampling_line_2': float,  # 采样线2位置 (0-1)
        'slope_impact': float,     # 斜率影响系数
        'base_impact': float,      # 基础影响系数
        'line_track_speed': float, # 巡线速度
        'slope_on_speed': float    # 斜率速度影响
    }
    """
    try:
        data = request.get_json()

        if 'sampling_line_1' in data:
            cv_service.sampling_line_1 = float(data['sampling_line_1'])
        if 'sampling_line_2' in data:
            val = float(data['sampling_line_2'])
            if val < cv_service.sampling_line_1:
                val = cv_service.sampling_line_1 + 0.1
            cv_service.sampling_line_2 = val
        if 'slope_impact' in data:
            cv_service.slope_impact = float(data['slope_impact'])
        if 'base_impact' in data:
            cv_service.base_impact = float(data['base_impact'])
        if 'line_track_speed' in data:
            cv_service.line_track_speed = float(data['line_track_speed'])
        if 'slope_on_speed' in data:
            cv_service.slope_on_speed = float(data['slope_on_speed'])

        return jsonify({
            'success': True,
            'sampling_line_1': cv_service.sampling_line_1,
            'sampling_line_2': cv_service.sampling_line_2,
            'slope_impact': cv_service.slope_impact,
            'base_impact': cv_service.base_impact,
            'line_track_speed': cv_service.line_track_speed,
            'slope_on_speed': cv_service.slope_on_speed
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error setting line params: {e}")
        return jsonify({'error': str(e)}), 500


@cv_bp.route('/status', methods=['GET'])
def get_status():
    """获取CV服务完整状态"""
    try:
        status = cv_service.get_status()
        return jsonify({
            'success': True,
            **status
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting CV status: {e}")
        return jsonify({'error': str(e)}), 500
