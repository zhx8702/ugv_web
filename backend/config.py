"""
Backend Configuration
"""
import os
import sys
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    AUTH_USER = os.getenv('AUTH_USER', 'ws')
    AUTH_PASSWORD = os.getenv('AUTH_PASSWORD', '')
    AUTH_ENABLED = os.getenv(
        'AUTH_ENABLED',
        'true' if os.getenv('AUTH_PASSWORD') else 'false'
    ).lower() == 'true'
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.getenv('SESSION_LIFETIME', 60 * 60 * 24 * 7)))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Server
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5080))

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    # Hardware - BaseController
    UART_PORT = os.getenv('UART_PORT')  # None = auto-detect
    UART_BAUDRATE = int(os.getenv('UART_BAUDRATE', 115200))
    MOCK_MODE = os.getenv('MOCK_MODE', 'false').lower() == 'true'
    USE_LIDAR = os.getenv('USE_LIDAR', 'false').lower() == 'true'
    EXTRA_SENSOR = os.getenv('EXTRA_SENSOR', 'false').lower() == 'true'

    # Locally connected USB gamepad
    GAMEPAD_ENABLED = os.getenv('GAMEPAD_ENABLED', 'true').lower() == 'true'
    GAMEPAD_DEVICE = os.getenv('GAMEPAD_DEVICE', '/dev/input/js0')
    GAMEPAD_DEADZONE = float(os.getenv('GAMEPAD_DEADZONE', 0.12))
    GAMEPAD_MAX_SPEED = float(os.getenv('GAMEPAD_MAX_SPEED', 1.3))
    GAMEPAD_GIMBAL_SPEED = float(os.getenv('GAMEPAD_GIMBAL_SPEED', 45.0))

    # Legacy compatibility
    SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/serial0')
    SERIAL_BAUDRATE = int(os.getenv('SERIAL_BAUDRATE', 115200))

    # Video
    CAMERA_TYPE = os.getenv('CAMERA_TYPE', 'auto')  # 'usb', 'csi', 'oak', 'auto'
    CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', 0))
    VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', 640))
    VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', 480))
    VIDEO_FPS = int(os.getenv('VIDEO_FPS', 30))
    VIDEO_QUALITY = int(os.getenv('VIDEO_QUALITY', 70))

    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MEDIA_PATH = os.getenv('MEDIA_PATH', os.path.join(BASE_DIR, 'media'))
    PHOTOS_PATH = os.getenv('PHOTOS_PATH', os.path.join(MEDIA_PATH, 'photos'))
    VIDEOS_PATH = os.getenv('VIDEOS_PATH', os.path.join(MEDIA_PATH, 'videos'))
    SOUNDS_PATH = os.getenv('SOUNDS_PATH', os.path.join(BASE_DIR, 'sounds'))

    # CV Vision Configuration
    CV_MODELS_PATH = os.getenv('CV_MODELS_PATH', os.path.join(BASE_DIR, 'models'))
    CV_DEFAULT_MODE = int(os.getenv('CV_DEFAULT_MODE', 10301))  # CV_NONE
    CV_TRACK_SPD_RATE = float(os.getenv('CV_TRACK_SPD_RATE', 60))
    CV_TRACK_ACC_RATE = float(os.getenv('CV_TRACK_ACC_RATE', 0.4))
    CV_AIMED_ERROR = float(os.getenv('CV_AIMED_ERROR', 8))
    CV_TRACK_FACES_ITERATE = float(os.getenv('CV_TRACK_FACES_ITERATE', 0.045))
    CV_TRACK_COLOR_ITERATE = float(os.getenv('CV_TRACK_COLOR_ITERATE', 0.023))

    # Audio Configuration
    AUDIO_PATH = os.getenv('AUDIO_PATH', os.path.join(BASE_DIR, 'sounds'))
    AUDIO_DEFAULT_VOLUME = float(os.getenv('AUDIO_DEFAULT_VOLUME', 0.5))
    AUDIO_TTS_RATE = int(os.getenv('AUDIO_TTS_RATE', 150))
    AUDIO_TTS_ENGINE = os.getenv('AUDIO_TTS_ENGINE', 'auto')  # auto | edge | espeak | pyttsx3
    AUDIO_TTS_VOICE = os.getenv('AUDIO_TTS_VOICE', 'zh-CN-XiaoxiaoNeural')
    AUDIO_MIN_TIME_BETWEEN = float(os.getenv('AUDIO_MIN_TIME_BETWEEN', 0.5))

    # ROS2 Bridge
    ROS2_ENABLED = os.getenv('ROS2_ENABLED', 'false').lower() == 'true'
    # When true, joystick/motion goes to /cmd_vel. Keep false while UART still owns the chassis.
    ROS2_DRIVE = os.getenv('ROS2_DRIVE', 'false').lower() == 'true'
    ROS2_BRIDGE_HOST = os.getenv('ROS2_BRIDGE_HOST', 'localhost')
    ROS2_BRIDGE_PORT = int(os.getenv('ROS2_BRIDGE_PORT', 5001))
    ROS2_WHEEL_SEPARATION = float(os.getenv('ROS2_WHEEL_SEPARATION', 0.172))
    ROS2_VIDEO_PORT = int(os.getenv('ROS2_VIDEO_PORT', 8080))
    ROS2_VIDEO_TOPIC = os.getenv('ROS2_VIDEO_TOPIC', '/camera/image_raw')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', os.path.join(BASE_DIR, 'logs', 'app.log'))

    # SocketIO — threading avoids eventlet conflicts with pygame/OpenCV/roslibpy
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = '*'  # Allow all origins for WebSocket
    SOCKETIO_PING_TIMEOUT = 60
    SOCKETIO_PING_INTERVAL = 25

    # AI Chat Configuration
    AI_CHAT_API_URL = os.getenv('AI_CHAT_API_URL', '')
    AI_CHAT_API_KEY = os.getenv('AI_CHAT_API_KEY', '')
    AI_CHAT_CHARACTER = os.getenv('AI_CHAT_CHARACTER', 'UGV_Assistant')
    AI_CHAT_DEFAULT_SESSION = os.getenv('AI_CHAT_DEFAULT_SESSION', 'ugv-main')
    AI_CHAT_ENABLE_TTS = os.getenv('AI_CHAT_ENABLE_TTS', 'true').lower() == 'true'
    AI_CHAT_TTS_VOICE = os.getenv('AI_CHAT_TTS_VOICE', 'zh-CN-XiaoxiaoNeural')

    @classmethod
    def get_ai_config(cls):
        """获取 AI 聊天配置字典"""
        return {
            "api_base_url": cls.AI_CHAT_API_URL,
            "api_key": cls.AI_CHAT_API_KEY,
            "character": cls.AI_CHAT_CHARACTER,
            "default_session": cls.AI_CHAT_DEFAULT_SESSION,
            "enable_tts": cls.AI_CHAT_ENABLE_TTS,
            "tts_voice": cls.AI_CHAT_TTS_VOICE
        }


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = 'development'
    # 开发环境默认启用Mock模式（如果环境变量未明确指定）
    MOCK_MODE = os.getenv('MOCK_MODE', 'true').lower() == 'true'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = 'production'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
