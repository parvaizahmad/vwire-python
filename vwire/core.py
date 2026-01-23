"""
Vwire Core Module - Main client implementation

This module provides the core Vwire client class following the same
architecture as the Arduino Vwire library: single-threaded with explicit
loop() calls for MQTT processing.
"""

import ssl
import time
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum

import paho.mqtt.client as mqtt

from .config import VwireConfig
from .timer import VwireTimer

# Setup logging
logger = logging.getLogger("vwire")

# Type aliases
PinValue = Union[int, float, str, List[Any]]
PinHandler = Callable[[Any], None]

# Check paho-mqtt version for API compatibility
PAHO_V2 = hasattr(mqtt, 'CallbackAPIVersion')


class ConnectionState(Enum):
    """Connection state enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"


class Vwire:
    """
    Vwire IoT Platform Client.
    
    Single-threaded implementation matching Arduino library architecture.
    Call run() in your main loop to process MQTT messages and timers.
    
    Example:
        device = Vwire("your_auth_token")
        
        @device.on_virtual_write(0)
        def handle_v0(value):
            print(f"V0 = {value}")
        
        if device.connect():
            device.run()  # Blocks forever, or use run_once() in your own loop
    """
    
    # Event types
    VIRTUAL_WRITE = "virtual_write"
    VIRTUAL_READ = "virtual_read"
    
    def __init__(self, auth_token: str, config: Optional[VwireConfig] = None):
        """
        Initialize Vwire client.
        
        Args:
            auth_token: Device authentication token from dashboard
            config: Optional configuration (uses secure defaults if not provided)
        """
        self._auth_token = auth_token
        self._config = config or VwireConfig()
        
        # Setup logging
        if self._config.debug:
            logging.basicConfig(level=logging.DEBUG)
            logger.setLevel(logging.DEBUG)
        
        # Create MQTT client
        self._setup_mqtt_client()
        
        # State management
        self._state = ConnectionState.DISCONNECTED
        self._pin_values: Dict[str, PinValue] = {}
        self._handlers: Dict[str, Dict[int, Callable]] = {
            self.VIRTUAL_WRITE: {},
            self.VIRTUAL_READ: {},
        }
        
        # Callbacks
        self._on_connected_callback: Optional[Callable] = None
        self._on_disconnected_callback: Optional[Callable] = None
        
        # Timer for scheduled tasks (runs in main thread via run())
        self._timer = VwireTimer()
        
        # Internal state
        self._reconnect_count = 0
        self._last_reconnect_attempt = 0.0
        self._stop_requested = False
        self._last_disconnect_time = 0.0
        self._disconnects_in_window = 0
        
        logger.debug(f"Vwire client initialized: {self._config}")
    
    def _setup_mqtt_client(self) -> None:
        """Setup MQTT client matching Arduino library approach."""
        transport = "websockets" if self._config.use_websocket else "tcp"
        
        # Client ID: "vwire-{auth_token}" like Arduino library
        client_id = f"vwire-{self._auth_token}"
        
        if PAHO_V2:
            self._mqtt = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
                client_id=client_id,
                protocol=mqtt.MQTTv311,
                transport=transport,
                clean_session=True
            )
        else:
            self._mqtt = mqtt.Client(
                client_id=client_id,
                protocol=mqtt.MQTTv311,
                transport=transport,
                clean_session=True
            )
        
        # WebSocket path
        if self._config.use_websocket:
            self._mqtt.ws_set_options(path="/mqtt")
        
        # Authentication (token as both username and password like Arduino)
        self._mqtt.username_pw_set(
            username=self._auth_token,
            password=self._auth_token
        )
        
        # TLS configuration
        if self._config.use_tls:
            self._setup_tls()

        # Last will so dashboard reflects offline state if connection drops
        will_topic = f"vwire/{self._auth_token}/status"
        self._mqtt.will_set(will_topic, payload='{"status":"offline"}', qos=1, retain=True)
        
        # Callbacks
        self._mqtt.on_connect = self._on_connect
        self._mqtt.on_disconnect = self._on_disconnect
        self._mqtt.on_message = self._on_message
    
    def _setup_tls(self) -> None:
        """Configure TLS settings."""
        cert_reqs = ssl.CERT_REQUIRED if self._config.verify_ssl else ssl.CERT_NONE
        
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = self._config.verify_ssl
        ssl_context.verify_mode = cert_reqs
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        if self._config.ca_certs:
            ssl_context.load_verify_locations(cafile=self._config.ca_certs)
        else:
            ssl_context.load_default_certs()
        
        if self._config.client_cert and self._config.client_key:
            ssl_context.load_cert_chain(
                certfile=self._config.client_cert,
                keyfile=self._config.client_key
            )
        
        self._mqtt.tls_set_context(ssl_context)
    
    # ========== Connection Methods ==========
    
    def connect(self, timeout: int = 30) -> bool:
        """
        Connect to the Vwire server.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if connected successfully
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
            
            # Poll until connected or timeout (like Arduino)
            start = time.time()
            while self._state == ConnectionState.CONNECTING:
                self._mqtt.loop(timeout=0.1)
                if (time.time() - start) > timeout:
                    logger.error("Connection timeout")
                    self._state = ConnectionState.DISCONNECTED
                    return False
            
            return self._state == ConnectionState.CONNECTED
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self._state = ConnectionState.DISCONNECTED
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the Vwire server."""
        if self._state == ConnectionState.DISCONNECTED:
            return
        
        logger.info("Disconnecting...")
        self._stop_requested = True
        self._timer.stop()
        
        try:
            status_topic = f"vwire/{self._auth_token}/status"
            self._mqtt.publish(status_topic, '{"status":"offline"}', qos=1, retain=True)
            self._mqtt.disconnect()
            self._mqtt.loop(timeout=0.5)
        except Exception:
            pass
        
        self._state = ConnectionState.DISCONNECTED
    
    def run(self) -> None:
        """
        Main loop - blocks forever, processing MQTT and timers.
        
        This matches the Arduino pattern where you call run() in loop().
        """
        self._stop_requested = False
        
        try:
            while not self._stop_requested:
                self._run_once()
                time.sleep(0.01)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.disconnect()
    
    def _run_once(self) -> None:
        """
        Single iteration - process MQTT and timers once.
        
        Like Arduino's Vwire.run() which is called in loop().
        """
        # If connected, process MQTT and timers
        if self._mqtt.is_connected():
            self._mqtt.loop(timeout=0.01)
            self._timer.run()
            return
        
        # Handle disconnection state change
        if self._state == ConnectionState.CONNECTED:
            self._state = ConnectionState.DISCONNECTED
            logger.warning("Connection lost")
            if self._on_disconnected_callback:
                try:
                    self._on_disconnected_callback()
                except Exception as e:
                    logger.error(f"Error in disconnect callback: {e}")
        
        # Auto reconnect (like Arduino)
        if self._config.max_reconnect_attempts == 0 or \
           self._reconnect_count < self._config.max_reconnect_attempts:
            now = time.time()
            if now - self._last_reconnect_attempt >= self._config.reconnect_interval:
                self._last_reconnect_attempt = now
                self._reconnect_count += 1
                logger.info(f"Reconnecting (attempt {self._reconnect_count})...")
                if self.connect(timeout=10):
                    self._reconnect_count = 0
    
    @property
    def connected(self) -> bool:
        """Check if connected to server."""
        return self._state == ConnectionState.CONNECTED and self._mqtt.is_connected()
    
    @property
    def timer(self) -> VwireTimer:
        """Get the built-in timer instance."""
        return self._timer
    
    # ========== Virtual Pin Operations ==========
    
    def virtual_write(self, pin: int, *values: Any) -> bool:
        """
        Write value(s) to a virtual pin.
        
        Matches Arduino library: publishes raw value to vwire/{token}/pin/V{pin}
        with comma-separated payloads for multiple values.
        """
        if not self.connected:
            logger.warning("Cannot write: not connected")
            return False

        if len(values) == 0:
            logger.warning("Cannot write: no values provided")
            return False

        if len(values) == 1:
            payload = self._format_value(values[0])
        else:
            payload = ",".join(self._format_value(v) for v in values)

        topic = f"vwire/{self._auth_token}/pin/V{pin}"
        # Use QoS 1 for reliable delivery (guaranteed at least once)
        result = self._mqtt.publish(topic, payload, qos=1)
        return result.rc == mqtt.MQTT_ERR_SUCCESS

    def _format_value(self, value: Any) -> str:
        """Format value similar to Arduino VirtualPin: bool->1/0, numbers->string."""
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, float):
            text = f"{value:.4f}".rstrip("0").rstrip(".")
            return text or "0"
        return str(value)
    
    def virtual_read(self, pin: int) -> Optional[PinValue]:
        """Get the last known value of a virtual pin."""
        return self._pin_values.get(f"V{pin}")
    
    def sync_virtual(self, pin: int) -> bool:
        """Request sync of a virtual pin value from server."""
        if not self.connected:
            return False
        
        topic = f"vwire/{self._auth_token}/sync/V{pin}"
        result = self._mqtt.publish(topic, "", qos=1)
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    def sync_all(self) -> bool:
        """Request sync of all pin values from server."""
        if not self.connected:
            return False
        
        topic = f"vwire/{self._auth_token}/sync"
        result = self._mqtt.publish(topic, "", qos=1)
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    # ========== Event Handlers ==========
    
    def on_virtual_write(self, pin: int) -> Callable:
        """
        Decorator to register a virtual write handler.
        
        Example:
            @device.on_virtual_write(0)
            def handle_v0(value):
                print(f"V0 changed to: {value}")
        """
        def decorator(func: PinHandler) -> PinHandler:
            self._handlers[self.VIRTUAL_WRITE][pin] = func
            return func
        return decorator
    
    def on_virtual_read(self, pin: int) -> Callable:
        """Decorator to register a virtual read handler."""
        def decorator(func: PinHandler) -> PinHandler:
            self._handlers[self.VIRTUAL_READ][pin] = func
            return func
        return decorator
    
    @property
    def on_connected(self) -> Callable:
        """Decorator to register connection handler."""
        def decorator(func: Callable) -> Callable:
            self._on_connected_callback = func
            return func
        return decorator
    
    @property
    def on_disconnected(self) -> Callable:
        """Decorator to register disconnection handler."""
        def decorator(func: Callable) -> Callable:
            self._on_disconnected_callback = func
            return func
        return decorator
    
    # ========== MQTT Callbacks ==========
    
    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            self._state = ConnectionState.CONNECTED
            self._reconnect_count = 0
            logger.info(f"Connected to {self._config.server}")
            
            # Subscribe to command topics
            cmd_topic = f"vwire/{self._auth_token}/cmd/#"
            client.subscribe(cmd_topic, qos=1)

            # Publish retained online status so dashboard reflects availability
            status_topic = f"vwire/{self._auth_token}/status"
            client.publish(status_topic, '{"status":"online"}', qos=1, retain=True)
            
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
            logger.error(f"Connection failed: {error_messages.get(rc, f'Unknown ({rc})')}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection."""
        if self._state == ConnectionState.DISCONNECTED:
            return
        
        self._state = ConnectionState.DISCONNECTED
        
        if rc != 0:
            reason = mqtt.error_string(rc)
            now = time.time()
            # Count rapid disconnects to surface likely token collision (server kicks old client)
            if now - self._last_disconnect_time <= 10:
                self._disconnects_in_window += 1
            else:
                self._disconnects_in_window = 1
            self._last_disconnect_time = now

            msg = f"Unexpected disconnection: {reason} (code: {rc})"
            if self._disconnects_in_window >= 2:
                msg += " | Hint: Broker enforces one active connection per device token. If another device (e.g., Arduino) uses the same token, it will kick this client. Create a separate device/token for each client."
            logger.warning(msg)
        
        if self._on_disconnected_callback:
            try:
                self._on_disconnected_callback()
            except Exception as e:
                logger.error(f"Error in disconnected callback: {e}")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        try:
            parts = msg.topic.split("/")
            
            if len(parts) >= 4 and parts[2] == "cmd":
                pin_str = parts[3]
                value = msg.payload.decode("utf-8")
                
                if pin_str.isdigit():
                    pin_str = f"V{pin_str}"
                
                if pin_str.upper().startswith("V"):
                    pin = int(pin_str[1:])
                    self._pin_values[f"V{pin}"] = value
                    
                    handler = self._handlers[self.VIRTUAL_WRITE].get(pin)
                    if handler:
                        try:
                            handler(value)
                        except Exception as e:
                            logger.error(f"Error in handler for V{pin}: {e}")
                            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    # ========== Context Manager ==========
    
    def __enter__(self) -> "Vwire":
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
