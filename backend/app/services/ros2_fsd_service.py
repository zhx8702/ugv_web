"""
ROS2 FSD (Full Self-Driving) Obstacle Avoidance Service

Reactive obstacle avoidance using LiDAR /scan data.
Subscribes to /scan, computes avoidance decisions, publishes /cmd_vel.
No SLAM or pre-built map required.
"""
import math
import time
import threading
import logging

logger = logging.getLogger(__name__)


class FSDService:
    """
    LiDAR-based reactive obstacle avoidance.

    Divides 360° scan into sectors, finds minimum distance per sector,
    and makes turn/speed decisions to avoid obstacles.
    """

    # Sector definitions: (name, start_angle_deg, end_angle_deg)
    # Angles: 0° = front, positive = left, negative = right
    SECTORS = [
        ('front',       -30,   30),
        ('front_left',   30,   70),
        ('front_right', -70,  -30),
        ('left',         70,  110),
        ('right',      -110,  -70),
        ('rear',        150,  210),
    ]

    def __init__(self, bridge):
        self.bridge = bridge

        # Tuneable parameters
        self.max_speed = 0.3        # m/s forward
        self.safe_distance = 0.40   # m — stop/turn threshold
        self.warn_distance = 0.80   # m — start slowing down
        self.turn_speed = 0.5       # rad/s turning rate

        # State
        self.running = False
        self._thread = None
        self._lock = threading.Lock()
        self._scan_data = None      # latest LaserScan msg
        self._obstacles = {}        # sector → min distance (m)
        self._current_cmd = {'linear_x': 0.0, 'angular_z': 0.0}
        self._decision = 'idle'
        self._subscription = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, config=None):
        """Start the avoidance loop."""
        if self.running:
            return False

        if config:
            self.max_speed = config.get('max_speed', self.max_speed)
            self.safe_distance = config.get('safe_distance', self.safe_distance)
            self.warn_distance = config.get('warn_distance', self.warn_distance)
            self.turn_speed = config.get('turn_speed', self.turn_speed)

        # Subscribe to /scan
        self._subscription = self.bridge.subscribe(
            '/scan', 'sensor_msgs/LaserScan',
            self._scan_callback, throttle_rate=100,  # 10 Hz
        )
        if self._subscription is None:
            logger.error("FSD: failed to subscribe to /scan")
            return False

        self.running = True
        self._thread = threading.Thread(target=self._control_loop, daemon=True)
        self._thread.start()
        logger.info("FSD started (max_speed=%.2f, safe=%.2f, warn=%.2f)",
                     self.max_speed, self.safe_distance, self.warn_distance)
        return True

    def stop(self):
        """Stop avoidance and send zero velocity."""
        if not self.running:
            return False

        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

        # Unsubscribe
        if self._subscription:
            self.bridge.unsubscribe('/scan', 'sensor_msgs/LaserScan')
            self._subscription = None

        # Stop the robot
        self._publish_cmd(0.0, 0.0)
        self._decision = 'stopped'
        logger.info("FSD stopped")
        return True

    def update_config(self, config):
        """Update parameters while running."""
        with self._lock:
            if 'max_speed' in config:
                self.max_speed = float(config['max_speed'])
            if 'safe_distance' in config:
                self.safe_distance = float(config['safe_distance'])
            if 'warn_distance' in config:
                self.warn_distance = float(config['warn_distance'])
            if 'turn_speed' in config:
                self.turn_speed = float(config['turn_speed'])

    def get_status(self):
        """Return current FSD state for the API/frontend."""
        with self._lock:
            return {
                'running': self.running,
                'decision': self._decision,
                'obstacles': dict(self._obstacles),
                'current_cmd': dict(self._current_cmd),
                'config': {
                    'max_speed': self.max_speed,
                    'safe_distance': self.safe_distance,
                    'warn_distance': self.warn_distance,
                    'turn_speed': self.turn_speed,
                },
            }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _scan_callback(self, msg):
        """Store latest scan message."""
        self._scan_data = msg

    def _control_loop(self):
        """Main avoidance loop running at ~10 Hz."""
        while self.running:
            if self._scan_data is not None:
                self._process_scan(self._scan_data)
            time.sleep(0.1)

    def _process_scan(self, msg):
        """Analyse scan data, decide, and publish cmd_vel."""
        angle_min = msg.get('angle_min', 0)
        angle_increment = msg.get('angle_increment', 0)
        range_min = msg.get('range_min', 0)
        range_max = msg.get('range_max', 0)
        ranges = msg.get('ranges', [])

        if not ranges or angle_increment == 0:
            return

        # Build per-sector minimum distances
        sector_mins = {name: float('inf') for name, _, _ in self.SECTORS}

        for i, r in enumerate(ranges):
            if r < range_min or r > range_max or math.isinf(r) or math.isnan(r):
                continue

            angle_deg = math.degrees(angle_min + i * angle_increment)
            # Normalise to -180..180
            angle_deg = ((angle_deg + 180) % 360) - 180

            for name, start, end in self.SECTORS:
                if start <= angle_deg < end:
                    if r < sector_mins[name]:
                        sector_mins[name] = r
                    break

        # Replace inf with a large number for JSON serialisation
        obstacles = {k: round(min(v, 99.0), 3) for k, v in sector_mins.items()}

        front = obstacles.get('front', 99)
        fl = obstacles.get('front_left', 99)
        fr = obstacles.get('front_right', 99)

        # Decision logic
        linear_x = 0.0
        angular_z = 0.0
        decision = 'cruise'

        if front < self.safe_distance:
            # Too close — must turn or reverse
            if fl > fr and fl > self.safe_distance:
                angular_z = self.turn_speed
                decision = 'turn_left'
            elif fr > fl and fr > self.safe_distance:
                angular_z = -self.turn_speed
                decision = 'turn_right'
            else:
                # Surrounded — reverse and spin
                linear_x = -self.max_speed * 0.5
                angular_z = self.turn_speed
                decision = 'reverse'
        else:
            # Front is clear — drive forward
            if front < self.warn_distance:
                # Slow down proportionally
                ratio = (front - self.safe_distance) / (self.warn_distance - self.safe_distance)
                linear_x = self.max_speed * max(0.15, ratio)
                decision = 'slow'
            else:
                linear_x = self.max_speed
                decision = 'cruise'

            # Gentle steering away from closer side
            if fl < self.warn_distance and fr > fl:
                angular_z = -self.turn_speed * 0.4
                decision = 'veer_right'
            elif fr < self.warn_distance and fl > fr:
                angular_z = self.turn_speed * 0.4
                decision = 'veer_left'

        self._publish_cmd(linear_x, angular_z)

        with self._lock:
            self._obstacles = obstacles
            self._current_cmd = {
                'linear_x': round(linear_x, 3),
                'angular_z': round(angular_z, 3),
            }
            self._decision = decision

    def _publish_cmd(self, linear_x, angular_z):
        """Publish Twist to /cmd_vel."""
        twist = {
            'linear':  {'x': linear_x, 'y': 0.0, 'z': 0.0},
            'angular': {'x': 0.0, 'y': 0.0, 'z': angular_z},
        }
        self.bridge.publish('/cmd_vel', 'geometry_msgs/Twist', twist)


# Singleton
_fsd_instance = None


def init_fsd_service(bridge):
    global _fsd_instance
    _fsd_instance = FSDService(bridge)
    return _fsd_instance


def get_fsd_service():
    return _fsd_instance
