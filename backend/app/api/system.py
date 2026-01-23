"""
System Monitoring API Endpoints
"""
from flask import jsonify, current_app
from app.api import system_bp
from app.services.system_monitor import SystemMonitor

# Initialize system monitor (singleton pattern)
monitor = SystemMonitor()


@system_bp.route('/status', methods=['GET'])
def get_status():
    """
    Get current system status
    Returns: {
        'cpu': float,
        'ram': float,
        'temperature': float,
        'voltage': float,
        'fps': int,
        'rssi': int,
        'timestamp': int
    }
    """
    try:
        status = monitor.get_current_status()
        return jsonify(status), 200
    except Exception as e:
        current_app.logger.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500


@system_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get historical system statistics
    Returns: {
        'cpu_history': [float],
        'ram_history': [float],
        'temp_history': [float],
        'voltage_history': [float]
    }
    """
    try:
        stats = monitor.get_historical_stats()
        return jsonify(stats), 200
    except Exception as e:
        current_app.logger.error(f"Error getting system stats: {e}")
        return jsonify({'error': str(e)}), 500


@system_bp.route('/info', methods=['GET'])
def get_info():
    """
    Get system information
    Returns: {
        'hostname': str,
        'platform': str,
        'python_version': str,
        'uptime': int
    }
    """
    try:
        info = monitor.get_system_info()
        return jsonify(info), 200
    except Exception as e:
        current_app.logger.error(f"Error getting system info: {e}")
        return jsonify({'error': str(e)}), 500


@system_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0',
        'service': 'ugv-rover-backend'
    }), 200


@system_bp.route('/network', methods=['GET'])
def get_network():
    """
    Get network information
    Returns: {
        'mode': 'AP'|'STA'|'unknown',
        'ip_address': str,
        'ssid': str,
        'mac_address': str,
        'rssi': int (dBm)
    }
    """
    try:
        network_info = monitor.get_network_info()
        return jsonify(network_info), 200
    except Exception as e:
        current_app.logger.error(f"Error getting network info: {e}")
        return jsonify({'error': str(e)}), 500


@system_bp.route('/uptime', methods=['GET'])
def get_uptime():
    """
    Get system uptime
    Returns: {
        'seconds': int,
        'formatted': str
    }
    """
    try:
        info = monitor.get_system_info()
        return jsonify({
            'seconds': info['uptime'],
            'formatted': info['uptime_formatted']
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting uptime: {e}")
        return jsonify({'error': str(e)}), 500
