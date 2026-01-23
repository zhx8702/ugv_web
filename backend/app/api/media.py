"""
Media Management API Endpoints
"""
from flask import jsonify, send_from_directory, request, current_app
from app.api import media_bp
from app.services.media_manager import MediaManager
import os

# Initialize media manager
manager = MediaManager()


@media_bp.route('/photos', methods=['GET'])
def get_photos():
    """
    Get list of photos
    Returns: [{
        'id': str,
        'name': str,
        'size': int,
        'created': str,
        'thumbnail': str
    }]
    """
    try:
        photos = manager.get_photos()
        return jsonify(photos), 200
    except Exception as e:
        current_app.logger.error(f"Error getting photos: {e}")
        return jsonify({'error': str(e)}), 500


@media_bp.route('/photos/<photo_id>', methods=['GET'])
def get_photo(photo_id):
    """Serve photo file"""
    try:
        photos_path = current_app.config['PHOTOS_PATH']
        return send_from_directory(photos_path, photo_id)
    except Exception as e:
        current_app.logger.error(f"Error serving photo: {e}")
        return jsonify({'error': 'Photo not found'}), 404


@media_bp.route('/photos/<photo_id>', methods=['DELETE'])
def delete_photo(photo_id):
    """Delete photo"""
    try:
        result = manager.delete_photo(photo_id)
        return jsonify({'success': True, 'result': result}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting photo: {e}")
        return jsonify({'error': str(e)}), 500


@media_bp.route('/videos', methods=['GET'])
def get_videos():
    """
    Get list of videos
    Returns: [{
        'id': str,
        'name': str,
        'size': int,
        'duration': float,
        'created': str,
        'thumbnail': str
    }]
    """
    try:
        videos = manager.get_videos()
        return jsonify(videos), 200
    except Exception as e:
        current_app.logger.error(f"Error getting videos: {e}")
        return jsonify({'error': str(e)}), 500


@media_bp.route('/videos/<video_id>', methods=['GET'])
def get_video(video_id):
    """Serve video file"""
    try:
        videos_path = current_app.config['VIDEOS_PATH']
        return send_from_directory(videos_path, video_id)
    except Exception as e:
        current_app.logger.error(f"Error serving video: {e}")
        return jsonify({'error': 'Video not found'}), 404


@media_bp.route('/videos/<video_id>', methods=['DELETE'])
def delete_video(video_id):
    """Delete video"""
    try:
        result = manager.delete_video(video_id)
        return jsonify({'success': True, 'result': result}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting video: {e}")
        return jsonify({'error': str(e)}), 500


@media_bp.route('/storage', methods=['GET'])
def get_storage_info():
    """
    Get storage usage information
    Returns: {
        'total': int,
        'used': int,
        'free': int,
        'photos_size': int,
        'videos_size': int
    }
    """
    try:
        info = manager.get_storage_info()
        return jsonify(info), 200
    except Exception as e:
        current_app.logger.error(f"Error getting storage info: {e}")
        return jsonify({'error': str(e)}), 500
