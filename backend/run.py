#!/usr/bin/env python3
"""
Quick start script for UGV Rover Backend
"""
import sys
import os

# Load .env BEFORE anything else
from dotenv import load_dotenv
load_dotenv()

# Monkey patch for eventlet (must be done before any other imports)
if sys.platform != 'win32':
    try:
        import eventlet
        eventlet.monkey_patch()
        print("✓ Eventlet monkey patching applied")
    except ImportError:
        print("⚠ Eventlet not available, falling back to threading mode")

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
        log_output=True  # Show eventlet server logs
    )
