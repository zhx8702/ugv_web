"""
Media Management Service
"""
import os
import time
from pathlib import Path
from flask import current_app
import logging
import cv2


class MediaManager:
    """
    Media file management service for photos and videos
    """

    def __init__(self):
        """Initialize media manager"""
        self.photos_path = None
        self.videos_path = None

    def _get_paths(self):
        """Get configured paths from app config"""
        if not self.photos_path:
            self.photos_path = current_app.config['PHOTOS_PATH']
            self.videos_path = current_app.config['VIDEOS_PATH']

    def get_photos(self):
        """
        Get list of all photos
        Returns: list of dicts with photo information
        """
        self._get_paths()
        photos = []

        try:
            if not os.path.exists(self.photos_path):
                return photos

            for filename in os.listdir(self.photos_path):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    filepath = os.path.join(self.photos_path, filename)
                    stat = os.stat(filepath)

                    photos.append({
                        'id': filename,
                        'name': filename,
                        'size': stat.st_size,
                        'created': time.ctime(stat.st_ctime),
                        'thumbnail': f'/api/media/photos/{filename}'
                    })

            # Sort by creation time (newest first)
            photos.sort(key=lambda x: x['created'], reverse=True)

        except Exception as e:
            logging.error(f'Error getting photos: {e}')

        return photos

    def delete_photo(self, photo_id):
        """
        Delete a photo

        Args:
            photo_id: Photo filename

        Returns:
            dict: Deletion result
        """
        self._get_paths()

        try:
            filepath = os.path.join(self.photos_path, photo_id)

            if not os.path.exists(filepath):
                raise FileNotFoundError(f'Photo not found: {photo_id}')

            os.remove(filepath)
            logging.info(f'Photo deleted: {photo_id}')

            return {'deleted': photo_id}

        except Exception as e:
            logging.error(f'Error deleting photo: {e}')
            raise

    def get_videos(self):
        """
        Get list of all videos
        Returns: list of dicts with video information
        """
        self._get_paths()
        videos = []

        try:
            if not os.path.exists(self.videos_path):
                return videos

            for filename in os.listdir(self.videos_path):
                if filename.lower().endswith(('.mp4', '.avi', '.h264')):
                    filepath = os.path.join(self.videos_path, filename)
                    stat = os.stat(filepath)

                    videos.append({
                        'id': filename,
                        'name': filename,
                        'size': stat.st_size,
                        'duration': self._get_video_duration(filepath),
                        'created': time.ctime(stat.st_ctime),
                        'url': f'/api/media/videos/{filename}',
                        'thumbnail': None  # TODO: Generate video thumbnail
                    })

            # Sort by creation time (newest first)
            videos.sort(key=lambda x: x['created'], reverse=True)

        except Exception as e:
            logging.error(f'Error getting videos: {e}')

        return videos

    def delete_video(self, video_id):
        """
        Delete a video

        Args:
            video_id: Video filename

        Returns:
            dict: Deletion result
        """
        self._get_paths()

        try:
            filepath = os.path.join(self.videos_path, video_id)

            if not os.path.exists(filepath):
                raise FileNotFoundError(f'Video not found: {video_id}')

            os.remove(filepath)
            logging.info(f'Video deleted: {video_id}')

            return {'deleted': video_id}

        except Exception as e:
            logging.error(f'Error deleting video: {e}')
            raise

    def get_storage_info(self):
        """
        Get storage usage information

        Returns:
            dict: Storage information
        """
        self._get_paths()

        try:
            # Get disk usage
            stat = os.statvfs(self.photos_path)
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bavail * stat.f_frsize
            used = total - free

            # Calculate photos and videos size
            photos_size = self._get_directory_size(self.photos_path)
            videos_size = self._get_directory_size(self.videos_path)

            return {
                'total': total,
                'used': used,
                'free': free,
                'photos_size': photos_size,
                'videos_size': videos_size,
                'photos_count': len(self.get_photos()),
                'videos_count': len(self.get_videos())
            }

        except Exception as e:
            logging.error(f'Error getting storage info: {e}')
            return {
                'total': 0,
                'used': 0,
                'free': 0,
                'photos_size': 0,
                'videos_size': 0,
                'photos_count': 0,
                'videos_count': 0
            }

    def _get_directory_size(self, directory):
        """Calculate total size of files in directory"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            logging.error(f'Error calculating directory size: {e}')
        return total_size

    def _get_video_duration(self, filepath):
        """
        Get video duration in seconds using OpenCV

        Args:
            filepath: Path to video file

        Returns:
            float: Duration in seconds, 0 if unable to determine
        """
        try:
            cap = cv2.VideoCapture(filepath)
            if not cap.isOpened():
                return 0

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()

            if fps > 0 and frame_count > 0:
                return round(frame_count / fps, 1)
            return 0
        except Exception as e:
            logging.error(f'Error getting video duration: {e}')
            return 0
