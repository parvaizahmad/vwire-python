# Vwire IoT Python Library

[![Python Version](https://img.shields.io/badge/python-3.8--3.13-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI Version](https://img.shields.io/pypi/v/vwire-iot.svg)](https://pypi.org/project/vwire-iot/)
[![Arduino Compatible](https://img.shields.io/badge/Arduino-v3.1.0-teal.svg)](https://github.com/parvaizahmad/vwire)

Official Python client library for the **Vwire IoT Platform** - enabling seamless communication between your Python applications and IoT devices.

The API is designed to be **consistent with the Arduino Vwire library**, making it easy to port code between platforms and maintain a unified development experience.

### Arduino ↔ Python Method Mapping

| Arduino | Python | Description |
|---------|--------|-------------|
| `Vwire.config(token)` | `Vwire(token)` | Initialize client |
| `Vwire.begin(ssid, pass)` | `connect()` | Connect to server |
| `Vwire.run()` | `run()` | Process messages |
| `Vwire.connected()` | `connected` | Check connection |
| `Vwire.virtualSend(pin, v)` | `virtual_send(pin, v)` | Send data |
| `VWIRE_RECEIVE(pin)` | `@on_virtual_receive(pin)` | Receive data |
| `Vwire.syncVirtual(pin)` | `sync_virtual(pin)` | Sync pin value |
| `Vwire.syncAll()` | `sync_all()` | Sync all pins |
| `Vwire.notify(msg)` | `notify(msg)` | Push notification |
| `Vwire.email(s, b)` | `email(s, b)` | Send email |
| `Vwire.log(msg)` | `log(msg)` | Send log message |

> **Note:** Python 3.14+ has a known incompatibility with the paho-mqtt library. Please use Python 3.8-3.13.

## Features

- Secure by Default - MQTT over TLS (port 8883) for encrypted communication
- Real-time Communication - Bidirectional data flow with MQTT
- Built-in Timer - Schedule tasks
- Multiple Transports - MQTT, MQTT over WebSocket, HTTP fallback
- Pythonic API - Clean, decorator-based event handling
- Cross-Platform - Works on Raspberry Pi, Linux, Windows, macOS
- Minimal Dependencies - Only requires `paho-mqtt` and `requests`

## Installation

### From PyPI (Recommended)

```bash
pip install vwire-iot
```

### From Source

```bash
git clone https://github.com/vwireiot/vwire-python.git
cd vwire-python
pip install -e .
```

### Dependencies

```bash
pip install paho-mqtt>=2.0.0 requests>=2.28.0
```

## Quick Start

### 1. Get Your Auth Token

1. Create an account at [vwireiot.com](https://vwireiot.com)
2. Create a new project
3. Add a device and copy the **Auth Token**

### 2. Basic Usage

```python
from vwire import Vwire

# Create client with your auth token
device = Vwire("your-auth-token-here")

# Connect to server (uses secure TLS by default)
device.connect()

# Send data to virtual pins
device.virtual_send(0, 25.5)  # Temperature
device.virtual_send(1, 60)    # Humidity

# Disconnect when done
device.disconnect()
```

### 3. Receiving Commands

```python
from vwire import Vwire

device = Vwire("your-auth-token-here")

# Handle commands from dashboard widgets
@device.on_virtual_receive(0)
def handle_slider(value):
    print(f"Slider value: {value}")
    # Control your hardware here

@device.on_virtual_receive(1)
def handle_button(value):
    if value == "1":
        print("Button pressed!")

# Connect and run event loop
device.connect()
device.run()
```

### 4. Using Timers

```python
from vwire import Vwire

device = Vwire("your-auth-token-here")

def send_sensor_data():
    temp = read_temperature()  # Your sensor reading
    device.virtual_send(0, temp)

# Send data every 5 seconds
device.timer.set_interval(5000, send_sensor_data)

device.connect()
device.run()
```

## API Reference

### Vwire Class

The main client class for IoT communication.

#### Constructor

```python
Vwire(auth_token, config=None, server=None, port=None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `auth_token` | str | Device authentication token from dashboard |
| `config` | VwireConfig | Optional configuration object |
| `server` | str | Override server hostname |
| `port` | int | Override MQTT port |

#### Connection Methods

| Method | Description |
|--------|-------------|
| `connect(timeout=30)` | Connect to server. Returns `True` if successful. |
| `disconnect()` | Disconnect from server. |
| `run(blocking=True)` | Run event loop. Set `blocking=False` for background mode. |
| `connected` | Property: `True` if connected. |

#### Virtual Pin Operations

| Method | Description |
|--------|-------------|
| `virtual_send(pin, value)` | Send value to virtual pin V0-V255. |
| `virtual_send(pin, v1, v2, ...)` | Send multiple values (for arrays). |
| `virtual_read(pin)` | Read last known value of virtual pin. |
| `sync_virtual(pin)` | Request sync of specific pin from server. |
| `sync_all()` | Request sync of all pins from server. |

#### Event Handlers

```python
# Decorator syntax (matches Arduino VWIRE_RECEIVE macro)
@device.on_virtual_receive(pin)
def handler(value):
    pass

# Generic syntax
@device.on(Vwire.VIRTUAL_RECEIVE, pin)
def handler(value):
    pass
```

#### Notifications & Logging

These methods match the Arduino library API. **Note:** `notify()` and `email()` are only available for paid plans (PRO, PRO+, ENTERPRISE).

| Method | Arduino Equivalent | Description |
|--------|-------------------|-------------|
| `notify(message)` | `Vwire.notify(msg)` | Send push notification to device owner |
| `email(subject, body)` | `Vwire.email(s, b)` | Send email to device owner |
| `log(message)` | `Vwire.log(msg)` | Send log message to server |

```python
# Send notifications (paid plans only)
device.notify("Temperature alert: exceeded 30°C!")

# Send email (paid plans only)
device.email(
    "Sensor Alert", 
    "Temperature has exceeded the configured threshold of 30°C."
)

# Send log message for debugging
device.log("Sensor initialized successfully")
```

### VwireConfig Class

Configuration for the Vwire client.

```python
from vwire import VwireConfig

# Default (secure TLS connection)
config = VwireConfig()

# Development mode (for local testing)
config = VwireConfig.development("localhost", 1883)

# WebSocket mode (when MQTT ports are blocked)
config = VwireConfig.websocket()

# Custom configuration
config = VwireConfig.custom(
    server="iot.mycompany.com",
    mqtt_port=8883,
    use_tls=True
)
```

### VwireTimer Class

Timer for scheduling periodic tasks.

```python
from vwire import VwireTimer

timer = VwireTimer()

# Run every 5 seconds
timer_id = timer.set_interval(5000, my_function)

# Run once after 10 seconds
timer.set_timeout(10000, one_time_function)

# Control timers
timer.enable_timer(timer_id)
timer.disable_timer(timer_id)
timer.delete_timer(timer_id)
timer.change_interval(timer_id, 3000)  # Change to 3 seconds

# In manual loop
while True:
    timer.run()
    time.sleep(0.01)

# Or start background thread
timer.start()
```

### VwireHTTP Class

HTTP client for simple operations without persistent connection.

```python
from vwire import VwireHTTP

client = VwireHTTP("your-auth-token")

# Send to pins
client.virtual_send(0, 25.5)
client.virtual_send(1, 60)

# Batch send
client.write_batch({
    "V0": 25.5,
    "V1": 60,
    "V2": 1013
})

# Read from server
value = client.virtual_read(0)
```

## Configuration Options

### Transport Modes

| Mode | Port | Description |
|------|------|-------------|
| TCP + TLS | 8883 | **Default.** Secure MQTT connection. |
| TCP | 1883 | Insecure. Development only. |
| WebSocket + TLS | 443 | Secure. Works through most firewalls. |
| WebSocket | 80 | Insecure. Development only. |

### Server Configuration

```python
from vwire import Vwire, VwireConfig

# Production (default)
device = Vwire("token")  # Uses mqtt.vwire.io:8883

# Custom server
device = Vwire("token", server="iot.mycompany.com")

# Development
config = VwireConfig.development("192.168.1.100")
device = Vwire("token", config=config)
```

## Examples

The `examples/` directory contains comprehensive examples:

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

## Comparison with Arduino Library

The Python library mirrors the Arduino Vwire library API:

| Arduino | Python |
|---------|--------|
| `Vwire.virtualSend(V0, value)` | `device.virtual_send(0, value)` |
| `Vwire.virtualRead(V0)` | `device.virtual_read(0)` |
| `VWIRE_RECEIVE(V0) { ... }` | `@device.on_virtual_receive(0)` |
| `timer.setInterval(1000, func)` | `device.timer.set_interval(1000, func)` |
| `Vwire.begin(auth)` | `device.connect()` |
| `Vwire.run()` | `device.run()` |

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Raspberry Pi | Full | GPIO support with RPi.GPIO |
| Linux | Full | All features |
| Windows | Full | All features |
| macOS | Full | All features |
| Docker | Full | Great for microservices |

## Troubleshooting

### Connection Issues

**"Not authorized" error:**
- Verify your auth token is correct
- Check that the device exists in dashboard
- Ensure the token hasn't been regenerated

**"Connection timeout":**
- Check network connectivity
- Verify server address and port
- Check firewall settings (port 8883 for MQTT)

**On Windows with WSL/Docker:**
If localhost connections fail, use your machine's IP:
```python
from vwire import get_local_ip
config = VwireConfig.development(get_local_ip())
```

### SSL Certificate Issues

For self-signed certificates:
```python
config = VwireConfig.custom(
    server="your-server.com",
    use_tls=True,
    verify_ssl=False  # Not recommended for production
)
```

### Debug Logging

Enable debug output:
```python
from vwire.utils import setup_logging
import logging

setup_logging(level=logging.DEBUG)
```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **Documentation:** [docs.vwireiot.com](https://docs.vwireiot.com)
- **Dashboard:** [vwireiot.com](https://vwireiot.com)
- **GitHub:** [github.com/vwireiot/vwire-python](https://github.com/vwireiot/vwire-python)
- **PyPI:** [pypi.org/project/vwire-iot](https://pypi.org/project/vwire-iot)
- **Support:** support@vwireiot.com

---

Made with ❤️ by the Vwire IoT Team
