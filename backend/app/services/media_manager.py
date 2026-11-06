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

                    meta = self._probe_video(filepath)
                    videos.append({
                        'id': filename,
                        'name': filename,
                        'size': stat.st_size,
                        'duration': meta['duration'],
                        'resolution': meta['resolution'],
                        'created': time.ctime(stat.st_ctime),
                        'url': f'/api/media/videos/{filename}',
                        'thumbnail': meta['thumbnail']
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
            thumb = self._thumb_path(filepath)
            if os.path.exists(thumb):
                os.remove(thumb)
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
                'photos_count': self._count_files(self.photos_path, ('.jpg', '.jpeg', '.png')),
                'videos_count': self._count_files(self.videos_path, ('.mp4', '.avi', '.h264'))
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

    def _count_files(self, directory, suffixes):
        count = 0
        try:
            if not os.path.isdir(directory):
                return 0
            for filename in os.listdir(directory):
                if filename.lower().endswith(suffixes):
                    count += 1
        except Exception as e:
            logging.error(f'Error counting files in {directory}: {e}')
        return count

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

    def _thumb_dir(self):
        path = os.path.join(self.videos_path, '.thumbs')
        os.makedirs(path, exist_ok=True)
        return path

    def _thumb_path(self, filepath):
        name = Path(filepath).stem + '.jpg'
        return os.path.join(self._thumb_dir(), name)

    def thumbnail_file(self, video_id):
        """Return cached thumbnail path, generating it if needed."""
        self._get_paths()
        filepath = os.path.join(self.videos_path, video_id)
        if not os.path.isfile(filepath):
            return None
        self._ensure_thumbnail(filepath)
        thumb = self._thumb_path(filepath)
        return thumb if os.path.isfile(thumb) else None

    def _ensure_thumbnail(self, filepath):
        thumb = self._thumb_path(filepath)
        if os.path.isfile(thumb) and os.path.getmtime(thumb) >= os.path.getmtime(filepath):
            return thumb
        try:
            cap = cv2.VideoCapture(filepath)
            if not cap.isOpened():
                return None
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            target = 30 if frame_count <= 0 else min(int(frame_count * 0.1), int(frame_count) - 1)
            if target > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(target, 0))
            ok, frame = cap.read()
            if not ok:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = cap.read()
            cap.release()
            if not ok or frame is None:
                return None
            height, width = frame.shape[:2]
            if width > 320:
                scale = 320 / float(width)
                frame = cv2.resize(frame, (320, max(1, int(height * scale))))
            cv2.imwrite(thumb, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 72])
            return thumb
        except Exception as e:
            logging.error(f'Error generating thumbnail for {filepath}: {e}')
            return None

    def _probe_video(self, filepath):
        duration = 0
        resolution = ''
        try:
            cap = cv2.VideoCapture(filepath)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS) or 0
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
                cap.release()
                if fps > 0 and frame_count > 0:
                    duration = round(frame_count / fps, 1)
                if width and height:
                    resolution = f'{width}x{height}'
        except Exception as e:
            logging.error(f'Error probing video {filepath}: {e}')
        self._ensure_thumbnail(filepath)
        thumb_url = None
        if os.path.isfile(self._thumb_path(filepath)):
            thumb_url = f'/api/media/videos/{os.path.basename(filepath)}/thumbnail'
        return {
            'duration': duration,
            'resolution': resolution,
            'thumbnail': thumb_url
        }
