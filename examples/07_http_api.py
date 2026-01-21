"""
HTTP API Example - Simple Data Sending Without MQTT
====================================================

This example demonstrates using the HTTP API for simple data sending
when you don't need persistent MQTT connections.

Use Cases:
    - Cron jobs that run periodically
    - Serverless functions (AWS Lambda, Google Cloud Functions)
    - Simple scripts that send data once
    - Environments where MQTT is blocked/unavailable
    - Quick testing

Advantages of HTTP:
    - No persistent connection needed
    - Simple request/response model
    - Works through most firewalls
    - Easy to debug

Disadvantages:
    - Can't receive real-time commands
    - Higher latency per message
    - More overhead for frequent sends

Usage:
    python 07_http_api.py
"""

import time
import random
from vwire import VwireHTTP

# =============================================================================
# CONFIGURATION
# =============================================================================

AUTH_TOKEN = "your-device-auth-token-here"

# Production server (default)
SERVER = "api.vwireiot.com"
PORT = 443
USE_SSL = True

# For local development:
# SERVER = "localhost"
# PORT = 3001
# USE_SSL = False

# =============================================================================
# HTTP CLIENT
# =============================================================================

client = VwireHTTP(
    auth_token=AUTH_TOKEN,
    server=SERVER,
    port=PORT,
    use_ssl=USE_SSL
)

# =============================================================================
# EXAMPLES
# =============================================================================

def example_single_write():
    """
    Example: Write a single value to a virtual pin.
    
    Simplest use case - send one value.
    """
    print("[SENT] Single Write Example")
    print("-" * 40)
    
    temperature = round(22 + random.uniform(-5, 5), 1)
    
    if client.virtual_write(0, temperature):
        print(f"[OK] Sent temperature: {temperature}C to V0")
    else:
        print("[ERROR] Failed to send data")
    
    print()


def example_multiple_writes():
    """
    Example: Write multiple values individually.
    
    Good when you need to send different types of data.
    """
    print("[SENT] Multiple Writes Example")
    print("-" * 40)
    
    # Simulate sensor readings
    temperature = round(22 + random.uniform(-5, 5), 1)
    humidity = round(55 + random.uniform(-10, 10), 1)
    pressure = round(1013 + random.uniform(-10, 10), 1)
    
    # Write to virtual pins
    success = True
    success &= client.virtual_write(0, temperature)
    success &= client.virtual_write(1, humidity)
    success &= client.virtual_write(2, pressure)
    
    if success:
        print(f"[OK] Sent: Temp={temperature}C, Humidity={humidity}%, "
              f"Pressure={pressure}hPa")
    else:
        print("[WARN]  Some writes failed")
    
    print()


def example_batch_write():
    """
    Example: Write multiple values in a batch.
    
    More efficient when sending multiple values at once.
    """
    print("[SENT] Batch Write Example")
    print("-" * 40)
    
    # Prepare batch data
    data = {
        "V0": round(22 + random.uniform(-5, 5), 1),    # Temperature
        "V1": round(55 + random.uniform(-10, 10), 1),  # Humidity
        "V2": round(1013 + random.uniform(-10, 10), 1),# Pressure
        "V3": random.randint(0, 100),                   # Light level %
        "V4": "Online",                                 # Status string
    }
    
    if client.write_batch(data):
        print("[OK] Batch data sent:")
        for pin, value in data.items():
            print(f"   {pin}: {value}")
    else:
        print("[ERROR] Batch write failed")
    
    print()


def example_periodic_logging():
    """
    Example: Periodic data logging.
    
    Typical pattern for data logger applications.
    """
    print("[SENT] Periodic Logging Example (5 readings)")
    print("-" * 40)
    
    for i in range(5):
        # Simulate sensor reading
        temp = round(22 + random.gauss(0, 2), 1)
        humidity = round(55 + random.gauss(0, 5), 1)
        
        # Send data
        success1 = client.virtual_write(0, temp)
        success2 = client.virtual_write(1, humidity)
        
        if success1 and success2:
            print(f"[{i+1}/5] [OK] Temp: {temp}C, Humidity: {humidity}%")
        else:
            print(f"[{i+1}/5] [ERROR] Send failed")
        
        if i < 4:  # Don't wait after last reading
            time.sleep(2)
    
    print()


def example_read_pin():
    """
    Example: Read pin value from server.
    
    Get the current stored value of a pin.
    """
    print("📥 Read Pin Example")
    print("-" * 40)
    
    value = client.virtual_read(0)
    
    if value is not None:
        print(f"[OK] V0 current value: {value}")
    else:
        print("[ERROR] Failed to read pin (or no value stored)")
    
    print()


def example_device_info():
    """
    Example: Get device information.
    
    Retrieve device metadata from server.
    """
    print("[INFO]  Device Info Example")
    print("-" * 40)
    
    info = client.get_device_info()
    
    if info:
        print("[OK] Device info:")
        for key, value in info.items():
            print(f"   {key}: {value}")
    else:
        print("[ERROR] Failed to get device info")
    
    print()


def example_connectivity_check():
    """
    Example: Check server connectivity.
    
    Useful before sending data to verify server is reachable.
    """
    print("[CONN] Connectivity Check")
    print("-" * 40)
    
    if client.ping():
        print("[OK] Server is reachable")
    else:
        print("[ERROR] Server is not reachable")
    
    print()


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("[DATA] Vwire IoT - HTTP API Example")
    print("=" * 60)
    print()
    print(f"Server: {SERVER}:{PORT}")
    print(f"SSL: {'Enabled' if USE_SSL else 'Disabled'}")
    print()
    
    # Run all examples
    example_connectivity_check()
    example_single_write()
    example_multiple_writes()
    example_batch_write()
    example_periodic_logging()
    example_read_pin()
    example_device_info()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
