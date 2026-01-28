# Vwire IoT Python Library

[![Python Version](https://img.shields.io/badge/python-3.8--3.13-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Official Python client library for the **Vwire IoT Platform** - enabling seamless communication between your Python applications and IoT devices.

The API is designed to be **consistent with the Arduino Vwire library**, making it easy to port code between platforms.

> **Note:** Python 3.14+ has a known incompatibility with the paho-mqtt library. Please use Python 3.8-3.13.

## Library Update (v2.0)

The library has been completely restructured with a new `vwire` package for better consistency with the Arduino library and improved features.

### New Package Location

The main library is now in the `vwire/` directory with:
- 🔒 **Secure by Default** - MQTT over TLS
- ⏱️ **Built-in Timer** - Like Arduino's BlynkTimer
- 🐍 **Pythonic API** - Decorator-based handlers
- 📦 **Modern Packaging** - pyproject.toml

## Installation

Install from Source

Clone the repository:

```bash
# Navigate to the vwire package directory
cd Libraries/python/vwire

# Install in development/editable mode
pip install -e .
```

### Verify Installation

```bash
python -c "from vwire import Vwire; print('✅ Vwire installed successfully!')"
```

### Dependencies

The library requires:
- **Python 3.8-3.13** (Python 3.14+ has paho-mqtt compatibility issues)
- `paho-mqtt>=2.0.0`
- `requests>=2.28.0`

These are automatically installed when using pip.

## Quick Start

```python
from vwire import Vwire

# Create client (uses secure MQTT/TLS by default)
device = Vwire("your-auth-token")

# Connect to server
device.connect()

# Send data to virtual pins
device.virtual_send(0, 25.5)  # Temperature to V0
device.virtual_send(1, 60)    # Humidity to V1

# Handle incoming commands from dashboard
@device.on_virtual_receive(0)
def handle_slider(value):
    print(f"Received: {value}")

# Run event loop
device.run()
```

## Using Timers (Like Arduino BlynkTimer)

```python
from vwire import Vwire

device = Vwire("your-auth-token")

def send_sensor_data():
    temp = read_temperature()
    device.virtual_send(0, temp)

# Send data every 5 seconds
device.timer.set_interval(5000, send_sensor_data)

device.connect()
device.run()
```

## Examples

All examples are in the `examples/` directory:

| Example | Description |
|---------|-------------|
| `01_basic_send.py` | Basic data sending |
| `02_receive_commands.py` | Handle dashboard commands |
| `03_timer_example.py` | Using VwireTimer |
| `04_weather_station.py` | Complete weather station |
| `05_smart_home.py` | Bidirectional smart home |
| `06_raspberry_pi_gpio.py` | Real GPIO with Raspberry Pi |
| `07_http_api.py` | HTTP API usage |
| `08_data_logger.py` | Production data logger |

### Running Examples

```bash
cd examples
python 01_basic_send.py
```

## API Comparison: Arduino vs Python

| Arduino | Python |
|---------|--------|
| `Vwire.virtualSend(V0, value)` | `device.virtual_send(0, value)` |
| `Vwire.virtualRead(V0)` | `device.virtual_read(0)` |
| `VWIRE_RECEIVE(V0) { ... }` | `@device.on_virtual_receive(0)` |
| `timer.setInterval(1000, func)` | `device.timer.set_interval(1000, func)` |
| `Vwire.begin(auth)` | `device.connect()` |
| `Vwire.run()` | `device.run()` |

## Configuration Options

```python
from vwire import Vwire, VwireConfig

# Default: Secure TLS connection
device = Vwire("token")

# Development mode (insecure, for local testing)
config = VwireConfig.development("localhost", 1883)
device = Vwire("token", config=config)

# WebSocket mode (works through firewalls)
config = VwireConfig.websocket()
device = Vwire("token", config=config)
```

## Full Documentation

See [vwire/README.md](vwire/README.md) for complete API documentation.

## Legacy Support

The old `iotech/` package is still available for backwards compatibility but is **deprecated**.
Please migrate to the new `vwire` package.

### Migration Guide

**Old (deprecated):**
```python
from iotech import IoTech
device = IoTech(auth_token, server="localhost", mqtt_port=1883)
```

**New (recommended):**
```python
from vwire import Vwire, VwireConfig
config = VwireConfig.development("localhost")
device = Vwire(auth_token, config=config)
```

## License

MIT License - See [vwire/LICENSE](vwire/LICENSE)

---

Made with love by the Vwire IoT Team
