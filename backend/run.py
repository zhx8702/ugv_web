#!/usr/bin/env python3
"""
Quick start script for UGV Rover Backend
"""
import sys
import os

# Load .env early so ROS2_ENABLED is available
from dotenv import load_dotenv
load_dotenv()

# Eventlet monkey-patching fights pygame, OpenCV and roslibpy on the Pi.
# Always use threading for the onboard service.
print("ℹ Using threading mode for SocketIO")

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
