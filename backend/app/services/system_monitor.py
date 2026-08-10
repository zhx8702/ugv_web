"""
System Monitoring Service
"""
import psutil
import time
import platform
import subprocess
import re
import socket
from collections import deque


class SystemMonitor:
    """
    System monitoring service for tracking CPU, RAM, temperature, etc.
    """

    def __init__(self, history_size=50):
        """
        Initialize system monitor

        Args:
            history_size: Number of historical data points to keep
        """
        self.history_size = history_size

        # Historical data
        self.cpu_history = deque(maxlen=history_size)
        self.ram_history = deque(maxlen=history_size)
        self.temp_history = deque(maxlen=history_size)
        self.voltage_history = deque(maxlen=history_size)

        # Current values (smoothed)
        self.voltage = None  # Populated only from valid hardware feedback.
        self.fps = 0
        self.rssi = -50
        self._cpu = 0
        self._ram = 0
        self._temp = 50

        # Smoothing factor (0-1, smaller = smoother)
        self.smoothing = 0.3

        # Start time
        self.start_time = time.time()

    def _smooth(self, old_val, new_val):
        """Apply exponential smoothing to reduce fluctuations"""
        if old_val == 0:
            return new_val
        return old_val + (new_val - old_val) * self.smoothing

    def get_cpu_usage(self):
        """Get current CPU usage percentage (smoothed)"""
        raw = psutil.cpu_percent(interval=None)  # Non-blocking
        self._cpu = self._smooth(self._cpu, raw)
        return self._cpu

    def get_ram_usage(self):
        """Get current RAM usage percentage (smoothed)"""
        raw = psutil.virtual_memory().percent
        self._ram = self._smooth(self._ram, raw)
        return self._ram

    def get_temperature(self):
        """
        Get CPU temperature in Celsius (smoothed)
        Returns default if unable to read (e.g., not on Raspberry Pi)
        """
        raw = 50.0  # Default
        try:
            # Try to read Raspberry Pi temperature
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                raw = float(f.read().strip()) / 1000.0
        except (FileNotFoundError, PermissionError):
            # Fallback for non-Raspberry Pi systems
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            raw = entries[0].current
                            break
            except AttributeError:
                pass

        self._temp = self._smooth(self._temp, raw)
        return self._temp

    def update_voltage(self, voltage):
        """Update measured battery voltage with smoothing."""
        if voltage > 0:
            self.voltage = voltage if self.voltage is None else self._smooth(self.voltage, voltage)

    def update_fps(self, fps):
        """Update FPS value (with smoothing)"""
        if fps >= 0:
            self.fps = self._smooth(self.fps, fps)

    def update_rssi(self, rssi):
        """Update RSSI value (with smoothing)"""
        if rssi != 0:
            self.rssi = self._smooth(self.rssi, rssi)

    def get_current_status(self):
        """
        Get current system status
        Returns: dict with current values
        """
        cpu = self.get_cpu_usage()
        ram = self.get_ram_usage()
        temp = self.get_temperature()

        # Update history
        self.cpu_history.append(cpu)
        self.ram_history.append(ram)
        self.temp_history.append(temp)
        self.voltage_history.append(self.voltage)

        return {
            'cpu': round(cpu, 1),
            'ram': round(ram, 1),
            'temperature': round(temp, 1),
            'voltage': round(self.voltage, 2) if self.voltage is not None else None,
            'fps': self.fps,
            'rssi': self.rssi,
            'timestamp': int(time.time())
        }

    def get_feedback_array(self):
        """
        Get feedback data in array format (compatible with original ugv_rpi format)
        Returns: Array with indices matching original format
        """
        status = self.get_current_status()

        # Create feedback array (indices match original ugv_rpi)
        feedback = [0] * 120  # Create array with 120 elements

        # Map values to specific indices (from original code)
        feedback[106] = status['cpu']           # CPU usage
        feedback[107] = status['temperature']   # Temperature
        feedback[108] = status['ram']           # RAM usage
        feedback[111] = status['rssi']          # RSSI
        feedback[112] = status['voltage'] or 0  # Voltage, 0 when unavailable
        feedback[113] = status['fps']           # FPS

        return feedback

    def get_historical_stats(self):
        """
        Get historical statistics
        Returns: dict with historical data arrays
        """
        return {
            'cpu_history': list(self.cpu_history),
            'ram_history': list(self.ram_history),
            'temp_history': list(self.temp_history),
            'voltage_history': list(self.voltage_history)
        }

    def get_system_info(self):
        """
        Get system information
        Returns: dict with system details
        """
        uptime = time.time() - self.start_time

        return {
            'hostname': platform.node(),
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'uptime': int(uptime),
            'uptime_formatted': self._format_uptime(uptime),
            'cpu_count': psutil.cpu_count(),
            'total_ram': psutil.virtual_memory().total // (1024 ** 3)  # GB
        }

    def _format_uptime(self, seconds):
        """Format uptime in human-readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)

        if days > 0:
            return f"{days} days, {hours} hours, {minutes} minutes"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes"
        else:
            return f"{minutes} minutes"

    def get_wifi_rssi(self):
        """
        Get WiFi signal strength (RSSI) in dBm
        Returns: int (negative value, closer to 0 is better)
        """
        try:
            # Try Linux (iwconfig)
            result = subprocess.run(['iwconfig'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                # Parse iwconfig output
                match = re.search(r'Signal level=(-?\d+) dBm', result.stdout)
                if match:
                    return int(match.group(1))

                # Alternative format
                match = re.search(r'Link Quality=(\d+)/(\d+)', result.stdout)
                if match:
                    quality = int(match.group(1))
                    max_quality = int(match.group(2))
                    # Convert to approximate dBm
                    return int(-100 + (quality / max_quality) * 100)

        except Exception as e:
            pass

        try:
            # Try reading /proc/net/wireless (Linux)
            with open('/proc/net/wireless', 'r') as f:
                lines = f.readlines()
                if len(lines) > 2:
                    # Third line contains wifi data
                    data = lines[2].split()
                    if len(data) > 3:
                        # Extract signal level (usually in dBm)
                        signal = data[3].replace('.', '')
                        return int(signal)
        except Exception:
            pass

        # Return mock value for development
        return -50

    def get_network_info(self):
        """
        Get network information
        Returns: dict with network details
        """
        network_info = {
            'mode': 'unknown',
            'ip_address': 'unknown',
            'ssid': 'unknown',
            'mac_address': 'unknown',
            'rssi': self.get_wifi_rssi()
        }

        try:
            # Get IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # Connect to external address (doesn't actually send data)
                s.connect(('8.8.8.8', 80))
                network_info['ip_address'] = s.getsockname()[0]
            finally:
                s.close()
        except Exception:
            # Try to get localhost IP
            try:
                network_info['ip_address'] = socket.gethostbyname(socket.gethostname())
            except:
                pass

        try:
            # Try to get SSID and mode (Linux)
            result = subprocess.run(['iwconfig'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                # Check if in AP mode
                if 'Mode:Master' in result.stdout:
                    network_info['mode'] = 'AP'
                elif 'Mode:Managed' in result.stdout or 'Mode:Auto' in result.stdout:
                    network_info['mode'] = 'STA'

                # Extract SSID
                match = re.search(r'ESSID:"([^"]*)"', result.stdout)
                if match:
                    network_info['ssid'] = match.group(1)
        except Exception:
            pass

        try:
            # Get MAC address
            interfaces = psutil.net_if_addrs()
            for interface_name, addresses in interfaces.items():
                if interface_name.startswith('wlan') or interface_name.startswith('wl'):
                    for addr in addresses:
                        if addr.family == psutil.AF_LINK:
                            network_info['mac_address'] = addr.address
                            break
        except Exception:
            pass

        return network_info
