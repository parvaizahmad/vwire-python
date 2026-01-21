"""
Basic Example - Send Sensor Data to Vwire IoT Platform
=======================================================

This example demonstrates the basic usage of the Vwire Python library,
showing how to connect to the platform and send sensor data.

The API is similar to the Arduino Vwire library for consistency across platforms.

Hardware: Any Python environment (Raspberry Pi, PC, etc.)
Platform: Vwire IoT (https://vwireiot.com)

Requirements:
    pip install vwire-iot

Usage:
    python 01_basic_send.py
"""

import time
import random
from vwire import Vwire, VwireConfig

# =============================================================================
# CONFIGURATION
# =============================================================================

# Get your auth token from the Vwire dashboard:
# 1. Log in at https://vwireiot.com
# 2. Create a new device or select existing one
# 3. Copy the Auth Token
AUTH_TOKEN = "yourtokenhere"

# Server configuration (default uses secure TLS connection)
# For local development, use: config = VwireConfig.development("localhost")
config = VwireConfig()  # Default: mqtt.vwireiot.com:8883 with TLS

# =============================================================================
# MAIN CODE
# =============================================================================

def main():
    """Main function demonstrating basic Vwire usage."""
    
    print("=" * 60)
    print("Vwire IoT - Basic Send Example")
    print("=" * 60)
    print(f"Server: {config.server}:{config.mqtt_port}")
    print(f"Transport: {'TLS' if config.use_tls else 'Insecure'}")
    print()
    
    # Create Vwire client
    device = Vwire(AUTH_TOKEN, config=config)
    
    # Connect to server
    print("Connecting to Vwire server...")
    if not device.connect():
        print("❌ Failed to connect! Check your auth token and network.")
        return
    
    print("✅ Connected successfully!")
    print()
    print("Sending sensor data every 2 seconds...")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        while True:
            # Simulate sensor readings
            # In a real application, read from actual sensors
            temperature = round(20 + random.uniform(-5, 10), 1)
            humidity = round(50 + random.uniform(-20, 30), 1)
            light_level = random.randint(0, 1023)
            
            # Send data to virtual pins (like Arduino Vwire.virtualWrite)
            device.virtual_write(0, temperature)    # V0 = Temperature
            device.virtual_write(1, humidity)       # V1 = Humidity
            device.virtual_write(2, light_level)    # V2 = Light level
            
            # Print status
            print(f"📤 Sent - Temp: {temperature}°C | Humidity: {humidity}% | Light: {light_level}")
            
            # Wait before next reading
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping...")
    finally:
        device.disconnect()
        print("✅ Disconnected.")


# =============================================================================
# ALTERNATIVE: Using Context Manager
# =============================================================================

def example_with_context_manager():
    """Alternative approach using Python context manager."""
    
    # Using 'with' statement automatically handles connect/disconnect
    with Vwire(AUTH_TOKEN, config=config) as device:
        for i in range(5):
            device.virtual_write(0, random.uniform(20, 30))
            print(f"Sent reading {i+1}/5")
            time.sleep(1)
    
    print("Automatically disconnected!")


# =============================================================================
# ALTERNATIVE: Quick Send (No Persistent Connection)
# =============================================================================

def example_quick_send():
    """Quick send without creating persistent connection."""
    from vwire import VwireHTTP
    
    # HTTP client for simple one-off sends
    http_client = VwireHTTP(
        AUTH_TOKEN,
        server="api.vwireiot.com",
        port=443
    )
    
    # Send single value
    http_client.virtual_write(0, 25.5)
    
    # Send multiple values at once
    http_client.write_batch({
        "V0": 25.5,
        "V1": 60,
        "V2": 1013
    })
    
    print("Data sent via HTTP!")


if __name__ == "__main__":
    main()
