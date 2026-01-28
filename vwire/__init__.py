"""
Vwire Python Client Library
============================

Official Python client for the Vwire IoT Platform - send and receive data 
from your IoT devices with an API similar to the Arduino Vwire library.

This library provides a consistent API across platforms (Arduino, Python, etc.)
for seamless IoT development.

Quick Start:
    from vwire import Vwire
    
    # Initialize with auth token (uses secure MQTT/TLS by default)
    device = Vwire("your_auth_token")
    device.connect()
    
    # Write to virtual pins
    device.virtual_write(0, 25.5)
    device.virtual_write(1, 60)
    
    # Handle incoming commands
    @device.on(Vwire.VIRTUAL_WRITE, 0)
    def v0_handler(value):
        print(f"V0 received: {value}")
    
    # Run with timer support
    device.run()

Features:
    - MQTT over TLS (secure by default)
    - Virtual pin operations (V0-V255)
    - Timer support for periodic tasks
    - Event handlers for incoming commands
    - Automatic reconnection
    - HTTP fallback option
    - Compatible with Raspberry Pi, Linux, Windows, macOS

For more information, visit: https://vwireiot.com/docs/python

License: MIT
"""

from .core import Vwire
from .config import VwireConfig
from .timer import VwireTimer
from .http_client import VwireHTTP
from .utils import get_local_ip, get_version

__version__ = "3.1.0"
__all__ = [
    "Vwire",
    "VwireConfig", 
    "VwireTimer",
    "VwireHTTP",
    "get_local_ip",
    "get_version",
]

# Version info (aligned with Arduino library)
VERSION_MAJOR = 3
VERSION_MINOR = 1
VERSION_PATCH = 0
