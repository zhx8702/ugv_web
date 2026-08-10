#!/usr/bin/env python3
"""
Quick start script for UGV Rover Backend
"""
import sys
import os

# Load .env early so ROS2_ENABLED is available
from dotenv import load_dotenv
load_dotenv()

# Monkey patch for eventlet (must be done before any other imports)
# Skip when ROS2 is enabled: eventlet conflicts with Twisted (used by roslibpy)
_ros2_enabled = os.getenv('ROS2_ENABLED', 'false').lower() == 'true'
if sys.platform != 'win32' and not _ros2_enabled:
    try:
        import eventlet
        eventlet.monkey_patch()
        print("✓ Eventlet monkey patching applied")
    except ImportError:
        print("⚠ Eventlet not available, falling back to threading mode")
elif _ros2_enabled:
    print("ℹ ROS2 enabled — using threading mode (skipping eventlet)")

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app, socketio

if __name__ == '__main__':
    # Print startup info
    print(f"🚀 Starting server on http://{app.config['HOST']}:{app.config['PORT']}")
    print(f"🔧 Mode: {'DEBUG' if app.config['DEBUG'] else 'PRODUCTION'}")

    # Run the application
    socketio.run(
        app,
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG'],
        use_reloader=False,  # 禁用 reloader，避免父子进程同时打开摄像头
        log_output=True,
        allow_unsafe_werkzeug=True
    )
