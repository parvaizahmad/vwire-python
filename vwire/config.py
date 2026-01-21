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


@dataclass
class VwireConfig:
    """
    Configuration for Vwire client.
    
    Provides secure defaults with MQTT over TLS as the primary communication method.
    
    Attributes:
        server: Server hostname (default: mqtt.vwireiot.com)
        mqtt_port: MQTT broker port (default: 8883 for TLS)
        http_port: HTTP API port for fallback (default: 443)
        transport: Transport mode (default: TCP_TLS)
        keepalive: MQTT keepalive interval in seconds (default: 60)
        reconnect_interval: Seconds between reconnection attempts (default: 5)
        max_reconnect_attempts: Maximum reconnection attempts, 0 for infinite (default: 0)
        verify_ssl: Verify SSL certificates (default: True for production)
        ca_certs: Path to CA certificates file (optional)
        client_cert: Path to client certificate file (optional)
        client_key: Path to client private key file (optional)
        heartbeat_interval: Heartbeat interval in seconds (default: 10)
        debug: Enable debug logging (default: False)
    
    Example:
        # Default configuration (secure, recommended)
        config = VwireConfig()
        
        # Custom server
        config = VwireConfig(server="iot.mycompany.com")
        
        # Development/local testing (insecure)
        config = VwireConfig.development("192.168.1.100")
        
        # WebSocket mode (useful when ports are blocked)
        config = VwireConfig.websocket()
    """
    
    server: str = "mqtt.vwireiot.com"
    mqtt_port: int = 8883
    http_port: int = 443
    transport: TransportMode = TransportMode.TCP_TLS
    keepalive: int = 60
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 0  # 0 = infinite
    verify_ssl: bool = True
    ca_certs: Optional[str] = None
    client_cert: Optional[str] = None
    client_key: Optional[str] = None
    heartbeat_interval: int = 10
    debug: bool = False
    
    @classmethod
    def development(cls, server: str = "localhost", port: int = 1883) -> "VwireConfig":
        """
        Create a development configuration (insecure, for local testing only).
        
        Args:
            server: Server hostname or IP (default: localhost)
            port: MQTT port (default: 1883)
            
        Returns:
            VwireConfig configured for local development
            
        Warning:
            Do NOT use in production! Data is transmitted unencrypted.
        """
        return cls(
            server=server,
            mqtt_port=port,
            http_port=3001,
            transport=TransportMode.TCP,
            verify_ssl=False,
            debug=True
        )
    
    @classmethod
    def websocket(cls, server: str = "mqtt.vwireiot.com", port: int = 443) -> "VwireConfig":
        """
        Create a WebSocket configuration (useful when MQTT ports are blocked).
        
        Uses MQTT over secure WebSocket (wss://) on port 443.
        
        Args:
            server: Server hostname (default: mqtt.vwireiot.com)
            port: WebSocket port (default: 443)
            
        Returns:
            VwireConfig configured for WebSocket transport
        """
        return cls(
            server=server,
            mqtt_port=port,
            transport=TransportMode.WEBSOCKET_TLS,
            verify_ssl=True
        )
    
    @classmethod
    def custom(
        cls,
        server: str,
        mqtt_port: int = 8883,
        use_tls: bool = True,
        use_websocket: bool = False,
        verify_ssl: bool = True
    ) -> "VwireConfig":
        """
        Create a custom configuration.
        
        Args:
            server: Server hostname
            mqtt_port: MQTT broker port
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
            mqtt_port=mqtt_port,
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
