"""
ROS2 Bridge Service - roslibpy connection manager

Manages the WebSocket connection to rosbridge_server running in
the ROS2 Docker container. Provides publisher/subscriber/action
abstractions for the rest of the backend.
"""
import threading
import logging
import time

logger = logging.getLogger(__name__)

try:
    import roslibpy
    HAS_ROSLIBPY = True
except ImportError:
    HAS_ROSLIBPY = False
    logger.warning("roslibpy not installed - ROS2 bridge unavailable")


class ROS2Bridge:
    """
    Singleton manager for the roslibpy connection to rosbridge.

    Features:
    - Cached publishers (one per topic)
    - Background reconnect loop
    - Thread-safe connection state
    """

    def __init__(self, host='localhost', port=5001):
        self.host = host
        self.port = port
        self.client = None
        self._connected = False
        self._lock = threading.Lock()
        self._publishers = {}
        self._subscribers = {}
        self._reconnect_thread = None
        self._should_reconnect = True

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    @property
    def connected(self):
        return self._connected and self.client is not None and self.client.is_connected

    def connect(self):
        """Connect to rosbridge. Starts a background reconnect loop."""
        if not HAS_ROSLIBPY:
            logger.error("Cannot connect: roslibpy not installed")
            return False

        if self.connected:
            return True

        try:
            self._do_connect()
        except Exception as e:
            logger.warning(f"Initial rosbridge connection failed: {e}")

        # Start reconnect thread if not already running
        if self._reconnect_thread is None or not self._reconnect_thread.is_alive():
            self._should_reconnect = True
            self._reconnect_thread = threading.Thread(
                target=self._reconnect_loop, daemon=True
            )
            self._reconnect_thread.start()

        return self.connected

    def _do_connect(self):
        """Internal: create client and connect."""
        with self._lock:
            if self.connected:
                return

            self._publishers.clear()
            self._subscribers.clear()

            self.client = roslibpy.Ros(host=self.host, port=self.port)
            self.client.on_ready(self._on_ready)

            # Start the Twisted event loop in a background thread
            self._run_thread = threading.Thread(target=self.client.run, daemon=True)
            self._run_thread.start()

            # Wait for connection
            deadline = time.time() + 8.0
            while time.time() < deadline and not self.client.is_connected:
                time.sleep(0.2)

            if self.client.is_connected:
                self._connected = True
                logger.info(f"Connected to rosbridge at {self.host}:{self.port}")
            else:
                self._connected = False
                raise ConnectionError("Timeout connecting to rosbridge")

    def _on_ready(self):
        self._connected = True
        logger.info("rosbridge ready")

    def _reconnect_loop(self):
        """Background loop that re-establishes connection when lost."""
        while self._should_reconnect:
            time.sleep(5)
            if not self.connected and self._should_reconnect:
                try:
                    self._do_connect()
                except Exception:
                    pass  # Will retry next iteration

    def disconnect(self):
        """Gracefully close connection."""
        self._should_reconnect = False
        with self._lock:
            if self.client is not None:
                try:
                    self.client.terminate()
                except Exception:
                    pass
            self._connected = False
            self._publishers.clear()
            self._subscribers.clear()
            logger.info("Disconnected from rosbridge")

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------

    def get_publisher(self, topic, msg_type):
        """
        Get or create a cached roslibpy.Topic for publishing.

        Args:
            topic: ROS2 topic name (e.g. '/cmd_vel')
            msg_type: ROS2 message type (e.g. 'geometry_msgs/Twist')

        Returns:
            roslibpy.Topic or None if not connected
        """
        if not self.connected:
            return None

        key = (topic, msg_type)
        if key not in self._publishers:
            self._publishers[key] = roslibpy.Topic(
                self.client, topic, msg_type
            )
        return self._publishers[key]

    def publish(self, topic, msg_type, message):
        """
        Publish a message to a ROS2 topic.

        Args:
            topic: ROS2 topic name
            msg_type: ROS2 message type string
            message: dict payload
        """
        pub = self.get_publisher(topic, msg_type)
        if pub is None:
            logger.warning(f"Cannot publish to {topic}: not connected")
            return False
        try:
            pub.publish(roslibpy.Message(message))
            return True
        except Exception as e:
            logger.error(f"Publish error on {topic}: {e}")
            self._connected = False
            return False

    # ------------------------------------------------------------------
    # Subscribing
    # ------------------------------------------------------------------

    def subscribe(self, topic, msg_type, callback, throttle_rate=0):
        """
        Subscribe to a ROS2 topic via rosbridge.

        Args:
            topic: ROS2 topic name
            msg_type: ROS2 message type string
            callback: function(msg_dict) called for each message
            throttle_rate: minimum interval between messages in ms (0=no throttle)
        """
        if not self.connected:
            logger.warning(f"Cannot subscribe to {topic}: not connected")
            return None

        key = (topic, msg_type)
        if key in self._subscribers:
            return self._subscribers[key]

        t = roslibpy.Topic(self.client, topic, msg_type,
                           throttle_rate=throttle_rate)
        t.subscribe(callback)
        self._subscribers[key] = t
        logger.info(f"Subscribed to {topic} [{msg_type}]")
        return t

    def unsubscribe(self, topic, msg_type):
        """Unsubscribe from a topic."""
        key = (topic, msg_type)
        t = self._subscribers.pop(key, None)
        if t is not None:
            t.unsubscribe()

    # ------------------------------------------------------------------
    # Service calls
    # ------------------------------------------------------------------

    def call_service(self, name, service_type, request=None, timeout=5):
        """
        Call a ROS2 service synchronously.

        Returns:
            dict response or None on error
        """
        if not self.connected:
            return None
        try:
            service = roslibpy.Service(self.client, name, service_type)
            req = roslibpy.ServiceRequest(request or {})
            result = service.call(req, timeout=timeout)
            return result
        except Exception as e:
            logger.error(f"Service call {name} failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self):
        """Return connection status dict for API consumption."""
        return {
            'connected': self.connected,
            'host': self.host,
            'port': self.port,
            'publishers': len(self._publishers),
            'subscribers': len(self._subscribers),
        }


# ======================================================================
# Singleton
# ======================================================================

_bridge_instance = None
_bridge_lock = threading.Lock()


def get_ros2_bridge(host=None, port=None):
    """
    Get or create the global ROS2Bridge singleton.

    Args:
        host: rosbridge host (only used on first call)
        port: rosbridge port (only used on first call)
    """
    global _bridge_instance
    with _bridge_lock:
        if _bridge_instance is None:
            _bridge_instance = ROS2Bridge(
                host=host or 'localhost',
                port=port or 5001,
            )
        return _bridge_instance


def init_ros2_bridge(app_config):
    """
    Initialize the ROS2 bridge from Flask app config.
    Call this once during app startup.
    """
    if not app_config.get('ROS2_ENABLED', False):
        logger.info("ROS2 bridge disabled (ROS2_ENABLED=false)")
        return None

    if not HAS_ROSLIBPY:
        logger.warning("ROS2_ENABLED is set but roslibpy is not installed; skipping ROS2 bridge")
        return None

    host = app_config.get('ROS2_BRIDGE_HOST', 'localhost')
    port = app_config.get('ROS2_BRIDGE_PORT', 5001)

    bridge = get_ros2_bridge(host, port)
    bridge.connect()
    return bridge
