"""
Vwire Core Module

Main Vwire client class providing Arduino-compatible API for IoT communication.
Uses MQTT over TLS as the default secure communication protocol.
"""

import json
import time
import threading
import ssl
import logging
import struct
import sys
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass

try:
    import paho.mqtt.client as mqtt
    PAHO_V2 = hasattr(mqtt, 'CallbackAPIVersion')
except ImportError:
    raise ImportError(
        "paho-mqtt is required. Install it with: pip install paho-mqtt>=2.0.0"
    )

# Monkey-patch for paho-mqtt struct.error bug in Python 3.14+
# The bug is in _handle_suback where f-string format creates invalid struct format
if sys.version_info >= (3, 14) and PAHO_V2:
    _original_handle_suback = mqtt.Client._handle_suback
    
    def _patched_handle_suback(self):
        """Patched version of _handle_suback to handle Python 3.14 struct changes."""
        try:
            return _original_handle_suback(self)
        except struct.error:
            # Fallback: manually parse the SUBACK packet
            packet = self._in_packet['packet']
            if len(packet) >= 2:
                mid = struct.unpack("!H", packet[:2])[0]
                rest = packet[2:]
                
                # Import required items from paho
                from paho.mqtt.client import (
                    SUBACK, MQTTv5, Properties, ReasonCode
                )
                
                if self._protocol == MQTTv5:
                    properties = Properties(SUBACK >> 4)
                    props, props_len = properties.unpack(rest)
                    reasoncodes = [ReasonCode(SUBACK >> 4, identifier=c) for c in rest[props_len:]]
                else:
                    reasoncodes = [ReasonCode(SUBACK >> 4, identifier=c) for c in rest]
                    properties = Properties(SUBACK >> 4)
                
                with self._callback_mutex:
                    on_subscribe = self.on_subscribe
                
                if on_subscribe:
                    with self._in_callback_mutex:
                        try:
                            from paho.mqtt.client import CallbackAPIVersion
                            if self._callback_api_version == CallbackAPIVersion.VERSION2:
                                on_subscribe(self, self._userdata, mid, reasoncodes, properties)
                            else:
                                # VERSION1 callback
                                if self._protocol == MQTTv5:
                                    on_subscribe(self, self._userdata, mid, reasoncodes, properties)
                                else:
                                    granted_qos = tuple(rc.value for rc in reasoncodes)
                                    on_subscribe(self, self._userdata, mid, granted_qos)
                        except Exception as e:
                            self._easy_log(mqtt.MQTT_LOG_ERR, f"Subscribe callback error: {e}")
    
    mqtt.Client._handle_suback = _patched_handle_suback

from .config import VwireConfig, TransportMode
from .timer import VwireTimer

# Setup logger
logger = logging.getLogger("vwire")


class PinType(Enum):
    """Pin type enumeration."""
    VIRTUAL = "V"


class ConnectionState(Enum):
    """Connection state enumeration."""
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    RECONNECTING = 3


@dataclass
class PinValue:
    """Represents a pin value with metadata."""
    value: str
    timestamp: float
    pin_type: PinType
    pin_number: int


class Vwire:
    """
    Main Vwire client class for IoT communication.
    
    Provides an Arduino-compatible API for sending and receiving data
    to/from the Vwire IoT platform. Uses secure MQTT/TLS by default.
    
    API Compatibility:
        This class is designed to mirror the Arduino Vwire library API,
        making it easy to port code between platforms.
    
    Example - Basic Usage:
        from vwire import Vwire
        
        # Create client with auth token
        device = Vwire("your_auth_token")
        
        # Connect to server
        device.connect()
        
        # Write to virtual pin
        device.virtual_write(0, 25.5)
        
        # Read last known value
        value = device.virtual_read(0)
        
        # Disconnect
        device.disconnect()
    
    Example - Event Handlers:
        from vwire import Vwire
        
        device = Vwire("your_auth_token")
        
        # Handle virtual pin writes from dashboard
        @device.on(Vwire.VIRTUAL_WRITE, 0)
        def handle_v0(value):
            print(f"V0 changed to: {value}")
        
        # Alternative decorator syntax
        @device.on_virtual_write(0)
        def handle_v0_alt(value):
            print(f"V0: {value}")
        
        device.connect()
        device.run()  # Blocking event loop
    
    Example - With Timer:
        from vwire import Vwire
        
        device = Vwire("your_auth_token")
        
        def send_data():
            device.virtual_write(0, read_sensor())
        
        # Schedule to run every 2 seconds
        device.timer.set_interval(2000, send_data)
        
        device.connect()
        device.run()
    """
    
    # Event types (Arduino-compatible constants)
    VIRTUAL_WRITE = "vw"
    VIRTUAL_READ = "vr"
    
    # Pin constants
    LOW = 0
    HIGH = 1
    
    # Max pins
    MAX_VIRTUAL_PINS = 256
    
    def __init__(
        self,
        auth_token: str,
        config: Optional[VwireConfig] = None,
        server: Optional[str] = None,
        port: Optional[int] = None
    ):
        """
        Initialize the Vwire client.
        
        Args:
            auth_token: Device authentication token from Vwire dashboard
            config: Optional VwireConfig object for custom configuration
            server: Override server hostname (optional)
            port: Override MQTT port (optional)
            
        Example:
            # Default (secure TLS connection)
            device = Vwire("your_auth_token")
            
            # Custom server
            device = Vwire("your_auth_token", server="iot.mycompany.com")
            
            # Development mode
            from vwire import Vwire, VwireConfig
            config = VwireConfig.development("192.168.1.100")
            device = Vwire("your_auth_token", config=config)
        """
        # Validate token
        if not auth_token or len(auth_token) < 10:
            raise ValueError("Invalid auth token")
        
        self._auth_token = auth_token
        self._config = config or VwireConfig()
        
        # Override server/port if provided
        if server:
            self._config.server = server
        if port:
            self._config.mqtt_port = port
        
        # MQTT client setup
        self._setup_mqtt_client()
        
        # State management
        self._state = ConnectionState.DISCONNECTED
        self._pin_values: Dict[str, PinValue] = {}
        self._handlers: Dict[str, Dict[int, Callable]] = {
            self.VIRTUAL_WRITE: {},
            self.VIRTUAL_READ: {},
        }
        
        # Connected callback
        self._on_connected_callback: Optional[Callable] = None
        self._on_disconnected_callback: Optional[Callable] = None
        
        # Timer for scheduled tasks
        self._timer = VwireTimer()
        
        # Internal state
        self._reconnect_count = 0
        self._last_heartbeat = 0
        self._lock = threading.Lock()
        
        logger.debug(f"Vwire client initialized: {self._config}")
    
    def _setup_mqtt_client(self) -> None:
        """Setup MQTT client with appropriate settings."""
        transport = "websockets" if self._config.use_websocket else "tcp"
        client_id = f"vwire-py-{self._auth_token[-8:]}-{int(time.time())}"
        
        if PAHO_V2:
            self._mqtt = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=client_id,
                protocol=mqtt.MQTTv311,
                transport=transport
            )
        else:
            self._mqtt = mqtt.Client(
                client_id=client_id,
                protocol=mqtt.MQTTv311,
                transport=transport
            )
        
        # WebSocket path
        if self._config.use_websocket:
            self._mqtt.ws_set_options(path="/mqtt")
        
        # Authentication
        self._mqtt.username_pw_set(
            username=self._auth_token,
            password=self._auth_token
        )
        
        # TLS configuration
        if self._config.use_tls:
            self._setup_tls()
        
        # Callbacks
        self._mqtt.on_connect = self._on_connect
        self._mqtt.on_disconnect = self._on_disconnect
        self._mqtt.on_message = self._on_message
    
    def _setup_tls(self) -> None:
        """Configure TLS settings."""
        cert_reqs = ssl.CERT_REQUIRED if self._config.verify_ssl else ssl.CERT_NONE
        
        self._mqtt.tls_set(
            ca_certs=self._config.ca_certs,
            certfile=self._config.client_cert,
            keyfile=self._config.client_key,
            cert_reqs=cert_reqs,
            tls_version=ssl.PROTOCOL_TLS
        )
        
        if not self._config.verify_ssl:
            self._mqtt.tls_insecure_set(True)
    
    # ========== Connection Methods ==========
    
    def connect(self, timeout: int = 30) -> bool:
        """
        Connect to the Vwire server.
        
        Args:
            timeout: Connection timeout in seconds (default: 30)
            
        Returns:
            True if connected successfully, False otherwise
            
        Example:
            device = Vwire("your_token")
            if device.connect():
                print("Connected!")
            else:
                print("Connection failed")
        """
        if self._state == ConnectionState.CONNECTED:
            return True
        
        self._state = ConnectionState.CONNECTING
        logger.info(f"Connecting to {self._config.server}:{self._config.mqtt_port}...")
        
        try:
            self._mqtt.connect(
                self._config.server,
                self._config.mqtt_port,
                keepalive=self._config.keepalive
            )
            self._mqtt.loop_start()
            
            # Wait for connection
            start = time.time()
            while self._state == ConnectionState.CONNECTING:
                if (time.time() - start) > timeout:
                    logger.error("Connection timeout")
                    self._state = ConnectionState.DISCONNECTED
                    return False
                time.sleep(0.1)
            
            return self._state == ConnectionState.CONNECTED
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self._state = ConnectionState.DISCONNECTED
            return False
    
    def disconnect(self) -> None:
        """
        Disconnect from the Vwire server.
        
        Example:
            device.disconnect()
        """
        logger.info("Disconnecting...")
        self._timer.stop()
        self._mqtt.loop_stop()
        self._mqtt.disconnect()
        self._state = ConnectionState.DISCONNECTED
    
    def run(self, blocking: bool = True) -> None:
        """
        Run the event loop.
        
        Args:
            blocking: If True, blocks forever. If False, starts background thread.
            
        Example:
            # Blocking (main loop)
            device.run()
            
            # Non-blocking (background)
            device.run(blocking=False)
            # ... do other things ...
        """
        if not self._timer.is_running:
            self._timer.start()
        
        if blocking:
            try:
                self._mqtt.loop_forever()
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                self.disconnect()
        else:
            # loop_start already called in connect()
            pass
    
    @property
    def connected(self) -> bool:
        """Check if connected to server."""
        return self._state == ConnectionState.CONNECTED
    
    @property
    def timer(self) -> VwireTimer:
        """Get the built-in timer instance."""
        return self._timer
    
    # ========== Virtual Pin Operations ==========
    
    def virtual_write(self, pin: int, *values: Any) -> bool:
        """
        Write value(s) to a virtual pin.
        
        Args:
            pin: Virtual pin number (0-255)
            *values: One or more values to write
            
        Returns:
            True if successful
            
        Example:
            # Single value
            device.virtual_write(0, 25.5)
            
            # Multiple values (for widgets that accept arrays)
            device.virtual_write(1, lat, lon)  # Map widget
            device.virtual_write(2, 255, 128, 0)  # RGB values
        """
        if not 0 <= pin < self.MAX_VIRTUAL_PINS:
            logger.warning(f"Invalid virtual pin: V{pin}")
            return False
        
        # Format value(s)
        if len(values) == 1:
            payload = str(values[0])
        else:
            payload = "\0".join(str(v) for v in values)
        
        topic = f"vwire/{self._auth_token}/pin/V{pin}"
        result = self._mqtt.publish(topic, payload, qos=1)
        
        # Update local cache
        self._pin_values[f"V{pin}"] = PinValue(
            value=payload,
            timestamp=time.time(),
            pin_type=PinType.VIRTUAL,
            pin_number=pin
        )
        
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    def virtual_read(self, pin: int) -> Optional[str]:
        """
        Read the last known value of a virtual pin.
        
        Args:
            pin: Virtual pin number (0-255)
            
        Returns:
            Last known value as string, or None if not available
            
        Example:
            temp = device.virtual_read(0)
            if temp:
                print(f"Temperature: {temp}")
        """
        pin_value = self._pin_values.get(f"V{pin}")
        return pin_value.value if pin_value else None
    
    def sync_virtual(self, pin: int) -> bool:
        """
        Request sync of a virtual pin value from server.
        
        Args:
            pin: Virtual pin number
            
        Returns:
            True if request was sent
        """
        topic = f"vwire/{self._auth_token}/sync/V{pin}"
        result = self._mqtt.publish(topic, "", qos=1)
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    def sync_all(self) -> bool:
        """
        Request sync of all pin values from server.
        
        Returns:
            True if request was sent
        """
        topic = f"vwire/{self._auth_token}/sync"
        result = self._mqtt.publish(topic, "", qos=1)
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    # ========== Event Handlers ==========
    
    def on(self, event_type: str, pin: int):
        """
        Decorator to register an event handler.
        
        Args:
            event_type: Event type (VIRTUAL_WRITE, etc.)
            pin: Pin number
            
        Returns:
            Decorator function
            
        Example:
            @device.on(Vwire.VIRTUAL_WRITE, 0)
            def handle_v0(value):
                print(f"V0: {value}")
        """
        def decorator(func: Callable):
            self._handlers[event_type][pin] = func
            return func
        return decorator
    
    def on_virtual_write(self, pin: int):
        """
        Decorator for virtual pin write events.
        
        Example:
            @device.on_virtual_write(0)
            def handle_v0(value):
                print(f"V0 received: {value}")
        """
        return self.on(self.VIRTUAL_WRITE, pin)
    
    def on_connected(self, func: Callable):
        """
        Decorator for connection event.
        
        Example:
            @device.on_connected
            def connected_handler():
                print("Connected!")
                device.sync_all()
        """
        self._on_connected_callback = func
        return func
    
    def on_disconnected(self, func: Callable):
        """
        Decorator for disconnection event.
        
        Example:
            @device.on_disconnected
            def disconnected_handler():
                print("Disconnected!")
        """
        self._on_disconnected_callback = func
        return func
    
    # ========== Advanced Methods ==========
    
    def set_property(self, pin: int, property_name: str, value: Any) -> bool:
        """
        Set a widget property (advanced widget control).
        
        Args:
            pin: Virtual pin number
            property_name: Property name (color, label, isDisabled, etc.)
            value: Property value
            
        Returns:
            True if successful
            
        Example:
            # Change widget color to red
            device.set_property(0, "color", "#FF0000")
            
            # Change widget label
            device.set_property(0, "label", "Temperature")
            
            # Disable widget
            device.set_property(0, "isDisabled", True)
        """
        topic = f"vwire/{self._auth_token}/prop/V{pin}"
        payload = json.dumps({property_name: value})
        result = self._mqtt.publish(topic, payload, qos=1)
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    def log_event(self, event: str, description: str = "") -> bool:
        """
        Log an event to the server.
        
        Args:
            event: Event name/code
            description: Event description
            
        Returns:
            True if successful
            
        Example:
            device.log_event("BOOT", "Device started")
            device.log_event("SENSOR_ERROR", "Temperature sensor failed")
        """
        topic = f"vwire/{self._auth_token}/log"
        payload = json.dumps({
            "event": event,
            "description": description,
            "timestamp": time.time()
        })
        result = self._mqtt.publish(topic, payload, qos=1)
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    def send_notification(self, message: str) -> bool:
        """
        Send a push notification (if configured in dashboard).
        
        Args:
            message: Notification message
            
        Returns:
            True if successful
            
        Example:
            device.send_notification("Alert: Temperature too high!")
        """
        topic = f"vwire/{self._auth_token}/notify"
        result = self._mqtt.publish(topic, message, qos=1)
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    def send_email(self, subject: str, body: str) -> bool:
        """
        Send an email (if configured in dashboard).
        
        Args:
            subject: Email subject
            body: Email body
            
        Returns:
            True if successful
            
        Example:
            device.send_email("Alert", "Temperature exceeded threshold!")
        """
        topic = f"vwire/{self._auth_token}/email"
        payload = json.dumps({"subject": subject, "body": body})
        result = self._mqtt.publish(topic, payload, qos=1)
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    # ========== MQTT Callbacks ==========
    
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        """Handle MQTT connection."""
        # VERSION2 uses reason_code object, VERSION1 uses rc integer
        rc = reason_code.value if hasattr(reason_code, 'value') else reason_code
        
        if rc == 0:
            self._state = ConnectionState.CONNECTED
            self._reconnect_count = 0
            logger.info(f"Connected to {self._config.server}")
            
            # Subscribe to command topics (server sends commands to /cmd/)
            cmd_topic = f"vwire/{self._auth_token}/cmd/#"
            client.subscribe(cmd_topic, qos=1)
            logger.debug(f"Subscribed to {cmd_topic}")
            
            # Subscribe to property updates
            prop_topic = f"vwire/{self._auth_token}/prop/#"
            client.subscribe(prop_topic, qos=1)
            
            # Call user callback
            if self._on_connected_callback:
                try:
                    self._on_connected_callback()
                except Exception as e:
                    logger.error(f"Error in connected callback: {e}")
        else:
            self._state = ConnectionState.DISCONNECTED
            error_messages = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized",
            }
            logger.error(f"Connection failed: {error_messages.get(rc, f'Unknown error ({rc})')}")
    
    def _on_disconnect(self, client, userdata, reason_code, properties=None):
        """Handle MQTT disconnection."""
        # VERSION2 uses reason_code object, VERSION1 uses rc integer
        rc = reason_code.value if hasattr(reason_code, 'value') else reason_code
        
        self._state = ConnectionState.DISCONNECTED
        
        if rc != 0:
            logger.warning(f"Unexpected disconnection (code: {rc})")
            self._state = ConnectionState.RECONNECTING
        
        # Call user callback
        if self._on_disconnected_callback:
            try:
                self._on_disconnected_callback()
            except Exception as e:
                logger.error(f"Error in disconnected callback: {e}")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        try:
            # Parse topic: vwire/{token}/cmd/{pin}
            parts = msg.topic.split("/")
            
            if len(parts) >= 4 and parts[2] == "cmd":
                pin_str = parts[3]
                value = msg.payload.decode("utf-8")
                
                # Normalize pin format - add V prefix if just a number
                if pin_str.isdigit():
                    pin_str = f"V{pin_str}"
                
                # Only process virtual pins (V0-V255)
                if not pin_str.startswith("V"):
                    return
                
                try:
                    pin_num = int(pin_str[1:])
                except ValueError:
                    return
                
                self._pin_values[pin_str] = PinValue(
                    value=value,
                    timestamp=time.time(),
                    pin_type=PinType.VIRTUAL,
                    pin_number=pin_num
                )
                
                # Dispatch to handler
                self._dispatch_handler(pin_str, value)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _dispatch_handler(self, pin_str: str, value: str):
        """Dispatch value to appropriate handler."""
        try:
            if pin_str.startswith("V"):
                pin_num = int(pin_str[1:])
                handler = self._handlers[self.VIRTUAL_WRITE].get(pin_num)
                if handler:
                    handler(value)
                    
        except (ValueError, KeyError) as e:
            logger.debug(f"Handler dispatch error: {e}")
    
    # ========== Context Manager ==========

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
