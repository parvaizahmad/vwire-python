# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-20

### Added
- **New `Vwire` class** - Main client with Arduino-compatible API
- **`VwireConfig` class** - Flexible configuration with presets for development, production, and WebSocket modes
- **`VwireTimer` class** - Timer functionality
  - `set_interval()` for periodic tasks
  - `set_timeout()` for one-time delayed tasks
  - Timer enable/disable/delete controls
- **TLS by default** - Secure MQTT connection on port 8883
- **WebSocket support** - MQTT over WebSocket for firewall-friendly connections
- **Context manager support** - Use `with Vwire(...) as device:`
- **Decorator-based handlers** - `@device.on_virtual_write(pin)` syntax
- **Connection event handlers** - `@device.on_connected` and `@device.on_disconnected`
- **Advanced features**:
  - `set_property()` for widget property control
  - `log_event()` for server-side logging
  - `send_notification()` and `send_email()` for alerts
  - `sync_virtual()` and `sync_all()` for pin synchronization
- **Comprehensive examples**:
  - Basic send
  - Receive commands
  - Timer usage
  - Weather station
  - Smart home controller
  - Raspberry Pi GPIO
  - HTTP API
  - Data logger

### Changed
- **Package renamed** from `iotech` to `vwire` for consistency with Arduino library
- **API redesigned** to match Arduino Vwire library patterns
- **Default connection** is now secure (MQTT over TLS on port 8883)
- **Improved error handling** with better logging

### Deprecated
- `iotech` package - Use `vwire` instead
- `IoTech` class - Use `Vwire` class
- `IoTechHTTP` class - Use `VwireHTTP` class

### Migration Guide

**Old API (v1.x):**
```python
from iotech import IoTech
device = IoTech(auth_token, server="localhost", mqtt_port=1883)
device.connect()
device.virtual_write(0, value)
```

**New API (v2.0):**
```python
from vwire import Vwire, VwireConfig
config = VwireConfig.development("localhost")
device = Vwire(auth_token, config=config)
device.connect()
device.virtual_write(0, value)
```

## [1.0.0] - 2025-06-15

### Added
- Initial release
- `IoTech` MQTT client class
- `IoTechHTTP` HTTP client class
- Virtual pin operations (V0-V255)
- Decorator-based event handlers
- Basic examples

[2.0.0]: https://github.com/vwireiot/vwire-python/releases/tag/v2.0.0
[1.0.0]: https://github.com/vwireiot/vwire-python/releases/tag/v1.0.0
