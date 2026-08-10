"""
Flask Application Factory
"""
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import logging
import os

# Initialize SocketIO
socketio = SocketIO()


def create_app(config_name=None):
    """Create and configure Flask application"""
    # Default to FLASK_ENV environment variable, or 'development' if not set
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    # Get the backend root directory (parent of app/)
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_folder = os.path.join(backend_dir, 'static')

    # Create Flask app with static folder configuration
    app = Flask(__name__, static_folder=static_folder, static_url_path='')

    # Load configuration
    from config import get_config
    app.config.from_object(get_config(config_name))

    # Ensure required directories exist
    os.makedirs(app.config['MEDIA_PATH'], exist_ok=True)
    os.makedirs(app.config['PHOTOS_PATH'], exist_ok=True)
    os.makedirs(app.config['VIDEOS_PATH'], exist_ok=True)
    os.makedirs(os.path.dirname(app.config['LOG_FILE']), exist_ok=True)

    # Setup logging
    setup_logging(app)

    # Initialize extensions
    CORS(app, resources={r"/*": {"origins": app.config['CORS_ORIGINS']}})

    socketio.init_app(
        app,
        cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGINS'],
        async_mode=app.config['SOCKETIO_ASYNC_MODE'],
        ping_timeout=app.config['SOCKETIO_PING_TIMEOUT'],
        ping_interval=app.config['SOCKETIO_PING_INTERVAL']
    )

    # Register blueprints
    register_blueprints(app)

    # Register WebSocket handlers
    register_websocket_handlers()

    # Register error handlers
    register_error_handlers(app)

    # Start background tasks for real-time updates
    start_background_tasks(app)

    app.logger.info(f'Application created in {config_name} mode')

    return app


def setup_logging(app):
    """Setup application logging"""
    log_level = getattr(logging, app.config['LOG_LEVEL'])

    # File handler
    file_handler = logging.FileHandler(app.config['LOG_FILE'])
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))

    # Add handlers
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)


def register_blueprints(app):
    """Register Flask blueprints"""
    from app.api import system_bp, control_bp, media_bp, cv_bp, audio_bp
    from app.api.video import video_bp
    from app.api.ota import ota_bp
    from app.api.lidar import lidar_bp
    from app.api.espnow import espnow_bp
    from app.api.ros2 import ros2_bp
    from app.api.settings import settings_bp

    app.register_blueprint(system_bp, url_prefix='/api/system')
    app.register_blueprint(control_bp, url_prefix='/api/control')
    app.register_blueprint(media_bp, url_prefix='/api/media')
    app.register_blueprint(cv_bp, url_prefix='/api/cv')
    app.register_blueprint(audio_bp, url_prefix='/api/audio')
    app.register_blueprint(settings_bp)
    app.register_blueprint(video_bp)  # Already has /api/video prefix
    app.register_blueprint(ota_bp)  # Already has /api/ota prefix
    app.register_blueprint(lidar_bp)  # Already has /api/lidar prefix
    app.register_blueprint(espnow_bp)  # Already has /api/espnow prefix
    app.register_blueprint(ros2_bp)  # /api/ros2 prefix


def register_websocket_handlers():
    """Register WebSocket event handlers"""
    from app.websocket import handlers  # noqa


def start_background_tasks(app):
    """Start background tasks for periodic updates"""
    from app.websocket.handlers import start_background_tasks as start_bg_tasks
    start_bg_tasks(app)

    # 初始化 CV 服务
    from app.services.cv_service import init_cv_service, set_socketio
    cv_service = init_cv_service(app.config)
    set_socketio(socketio)
    app.logger.info("CV service initialized")

    # 初始化 ROS2 Bridge (if enabled)
    if app.config.get('ROS2_ENABLED', False):
        from app.services.ros2_bridge import init_ros2_bridge
        bridge = init_ros2_bridge(app.config)
        if bridge and bridge.connected:
            app.logger.info(f"ROS2 bridge connected to {app.config['ROS2_BRIDGE_HOST']}:{app.config['ROS2_BRIDGE_PORT']}")
            # 初始化 FSD 避障服务
            from app.services.ros2_fsd_service import init_fsd_service
            init_fsd_service(bridge)
            app.logger.info("FSD obstacle avoidance service initialized")
        else:
            app.logger.warning("ROS2 bridge enabled but not connected (will retry in background)")

    # 启动视频流 - 传递 Flask 配置确保路径一致
    from app.services.video_stream import get_video_stream
    video_config = {
        'camera_index': app.config.get('CAMERA_INDEX', 0),
        'width': app.config.get('VIDEO_WIDTH', 640),
        'height': app.config.get('VIDEO_HEIGHT', 480),
        'fps': app.config.get('VIDEO_FPS', 30),
        'quality': app.config.get('VIDEO_QUALITY', 20),
        'photos_path': app.config.get('PHOTOS_PATH'),
        'videos_path': app.config.get('VIDEOS_PATH'),
        'mock_mode': app.config.get('MOCK_MODE', False)
    }
    stream = get_video_stream(video_config)
    stream.set_cv_service(cv_service)  # 连接 CV 服务到视频流
    cv_service.set_video_stream(stream)
    stream.start()
    app.logger.info(f"Video stream started, photos_path: {app.config.get('PHOTOS_PATH')}")

    # Read a USB gamepad connected to the Raspberry Pi, if present.
    if app.config.get('GAMEPAD_ENABLED', True):
        from app.services.gamepad_service import start_gamepad_service
        start_gamepad_service(app.config)


def register_error_handlers(app):
    """Register error handlers"""
    from flask import send_from_directory, Response

    @app.route('/video_feed')
    def video_feed():
        """兼容旧的 /video_feed 路由"""
        from app.services.video_stream import get_video_stream
        stream = get_video_stream()
        return Response(
            stream.generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    @app.route('/')
    def serve_index():
        """Serve the frontend index.html"""
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        """Serve static files or fallback to index.html for SPA routes"""
        # Skip socket.io and api routes - let them be handled by their own handlers
        if path.startswith('socket.io') or path.startswith('api/'):
            return {'error': 'Not found'}, 404
        # Try to serve the static file
        static_file = os.path.join(app.static_folder, path)
        if os.path.isfile(static_file):
            return send_from_directory(app.static_folder, path)
        # Fallback to index.html for SPA client-side routing
        return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(404)
    def not_found(error):
        # For API routes, return JSON error
        from flask import request
        if request.path.startswith('/api/'):
            return {'error': 'Not found'}, 404
        # For other routes, serve index.html (SPA fallback)
        return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal error: {error}')
        return {'error': 'Internal server error'}, 500
