"""
Vwire Configuration Module

Provides configuration classes for the Vwire client, supporting multiple
communication modes (MQTT/TLS, MQTT/WebSocket, HTTP).
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class TransportMode(Enum):
    """Transport mode for MQTT connection."""
    TCP_TLS = "tcp_tls"      # MQTT over TCP with TLS (recommended, port 8883)
    TCP = "tcp"               # MQTT over TCP (insecure, port 1883)
    WEBSOCKET_TLS = "wss"    # MQTT over WebSocket with TLS (port 443)
    WEBSOCKET = "ws"          # MQTT over WebSocket (insecure)


# Default server and port constants (matching Arduino VwireConfig.h)
DEFAULT_SERVER = "mqtt.vwire.io"
DEFAULT_PORT_TCP = 1883
DEFAULT_PORT_TLS = 8883
DEFAULT_HEARTBEAT_INTERVAL = 30  # seconds (matches Arduino VWIRE_DEFAULT_HEARTBEAT_INTERVAL)
DEFAULT_RECONNECT_INTERVAL = 5   # seconds (matches Arduino VWIRE_DEFAULT_RECONNECT_INTERVAL)


@dataclass
class VwireConfig:
    """
    Configuration for Vwire client.
    
    Provides secure defaults with MQTT over TLS as the primary communication method.
    Server and port are treated as internal configuration (similar to Arduino where
    they are set via config() method and stored privately).
    
    Note:
        In Arduino, server/port are private members set via config(). Here they're
        accessible but prefixed with underscore convention to indicate internal use.
        Use the factory methods (development(), websocket(), custom()) for configuration.
    
    Attributes:
        server: Server hostname (default: mqtt.vwire.io) - internal
        port: MQTT broker port (default: 8883 for TLS) - internal  
        http_port: HTTP API port for fallback (default: 443)
        transport: Transport mode (default: TCP_TLS)
        keepalive: MQTT keepalive interval in seconds (default: 30)
        reconnect_interval: Seconds between reconnection attempts (default: 5)
        max_reconnect_attempts: Maximum reconnection attempts, 0 for infinite (default: 0)
        verify_ssl: Verify SSL certificates (default: True for production)
        ca_certs: Path to CA certificates file (optional)
        client_cert: Path to client certificate file (optional)
        client_key: Path to client private key file (optional)
        heartbeat_interval: Heartbeat interval in seconds (default: 30)
        debug: Enable debug logging (default: False)
    
    Example:
        # Default configuration (secure, recommended)
        config = VwireConfig()
        
        # Development/local testing (insecure)
        config = VwireConfig.development("192.168.1.100")
        
        # WebSocket mode (useful when ports are blocked)
        config = VwireConfig.websocket()
    """
    
    # Server configuration (internal - use factory methods to modify)
    # Named without underscore for dataclass compatibility but treated as internal
    server: str = DEFAULT_SERVER
    port: int = DEFAULT_PORT_TLS  # Renamed from mqtt_port to match Arduino 'port'
    http_port: int = 443
    transport: TransportMode = TransportMode.TCP_TLS
    keepalive: int = 30  # Match Arduino: 30 second keepalive
    reconnect_interval: int = DEFAULT_RECONNECT_INTERVAL
    max_reconnect_attempts: int = 0  # 0 = infinite
    verify_ssl: bool = True
    ca_certs: Optional[str] = None
    client_cert: Optional[str] = None
    client_key: Optional[str] = None
    heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL
    debug: bool = False
    
    # Backward compatibility alias
    @property
    def mqtt_port(self) -> int:
        """Alias for port (backward compatibility)."""
        return self.port
    
    @classmethod
    def development(cls, server: str = "localhost", mqtt_port: int = DEFAULT_PORT_TCP) -> "VwireConfig":
        """
        Create a development configuration (insecure, for local testing only).
        
        Args:
            server: Server hostname or IP (default: localhost)
            mqtt_port: MQTT port (default: 1883)
            
        Returns:
            VwireConfig configured for local development
            
        Warning:
            Do NOT use in production! Data is transmitted unencrypted.
        """
        return cls(
            server=server,
            port=mqtt_port,
            http_port=3001,
            transport=TransportMode.TCP,
            verify_ssl=False,
            debug=True
        )
    
    @classmethod
    def websocket(cls, server: str = DEFAULT_SERVER, mqtt_port: int = 443) -> "VwireConfig":
        """
        Create a WebSocket configuration (useful when MQTT ports are blocked).
        
        Uses MQTT over secure WebSocket (wss://) on port 443.
        
        Args:
            server: Server hostname (default: mqtt.vwire.io)
            mqtt_port: WebSocket port (default: 443)
            
        Returns:
            VwireConfig configured for WebSocket transport
        """
        return cls(
            server=server,
            port=mqtt_port,
            transport=TransportMode.WEBSOCKET_TLS,
            verify_ssl=True
        )
    
    @classmethod
    def custom(
        cls,
        server: str,
        mqtt_port: int = DEFAULT_PORT_TLS,
        use_tls: bool = True,
        use_websocket: bool = False,
        verify_ssl: bool = True
    ) -> "VwireConfig":
        """
        Create a custom configuration.
        
        Similar to Arduino's config(authToken, server, port) method.
        
        Args:
            server: Server hostname
            mqtt_port: MQTT broker port (default: 8883 for TLS, use 1883 for TCP)
            use_tls: Enable TLS encryption
            use_websocket: Use WebSocket transport
            verify_ssl: Verify SSL certificates
            
        Returns:
            VwireConfig with custom settings
        """
        if use_websocket:
            transport = TransportMode.WEBSOCKET_TLS if use_tls else TransportMode.WEBSOCKET
        else:
            transport = TransportMode.TCP_TLS if use_tls else TransportMode.TCP
        
        return cls(
            server=server,
            port=mqtt_port,
            transport=transport,
            verify_ssl=verify_ssl
        )
    
    @property
    def use_tls(self) -> bool:
        """Check if TLS is enabled."""
        return self.transport in (TransportMode.TCP_TLS, TransportMode.WEBSOCKET_TLS)
    
    @property
    def use_websocket(self) -> bool:
        """Check if WebSocket transport is enabled."""
        return self.transport in (TransportMode.WEBSOCKET, TransportMode.WEBSOCKET_TLS)
    
    def __str__(self) -> str:
        tls_status = "TLS" if self.use_tls else "insecure"
        ws_status = "WebSocket" if self.use_websocket else "TCP"
        return f"VwireConfig({self.server}:{self.mqtt_port}, {ws_status}, {tls_status})"
