"""
Main Application Entry Point
"""
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, socketio
import logging

# Create Flask application (read config from FLASK_ENV environment variable)
config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    config = app.config

    print("""
╔══════════════════════════════════════════════════════════╗
║     UGV Rover Web Control System - Backend v2.0         ║
╚══════════════════════════════════════════════════════════╝
    """)

    print(f"🚀 Starting server...")
    print(f"🌐 Host: {config['HOST']}:{config['PORT']}")
    print(f"🔧 Environment: {config['ENV']}")
    print(f"📁 Media Path: {config['MEDIA_PATH']}")
    print(f"🔌 WebSocket: Enabled (async_mode: {config['SOCKETIO_ASYNC_MODE']})")
    print(f"📊 CORS Origins: {config['CORS_ORIGINS']}")
    print(f"\n✅ Server is ready!")
    print(f"🌍 Frontend URL: http://localhost:3002")
    print(f"🔗 Backend URL: http://{config['HOST']}:{config['PORT']}\n")

    # Play startup sound
    try:
        from app.services.audio_service import get_audio_service
        audio_service = get_audio_service()
        audio_service.play_random('robot_started')
        print("🔊 Startup sound played")
    except Exception as e:
        logging.warning(f"Failed to play startup sound: {e}")

    try:
        # Run with SocketIO
        socketio.run(
            app,
            host=config['HOST'],
            port=config['PORT'],
            debug=config['DEBUG'],
            use_reloader=config['DEBUG']
        )
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        sys.exit(1)
