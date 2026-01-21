"""
Smart Home Controller Example - Bidirectional IoT Communication
================================================================

A comprehensive example demonstrating bidirectional communication
for a smart home scenario. The device both:
- Receives commands from the dashboard (control lights, thermostat)
- Sends sensor data to the dashboard (temperature, motion, door status)

This shows the full power of Vwire for IoT applications.

Pin Mapping:
    OUTPUTS (controlled by dashboard):
    V0  - Living Room Light (switch)
    V1  - Bedroom Light (switch)
    V2  - Thermostat Target (slider)
    V3  - Fan Speed (slider 0-3)
    
    INPUTS (sent to dashboard):
    V10 - Current Temperature (gauge)
    V11 - Motion Detected (LED indicator)
    V12 - Door Status (LED indicator)
    V13 - Status Message (value display)
    V14 - HVAC State (value display)

Hardware: Any Python environment (Raspberry Pi, PC, etc.)
Platform: Vwire IoT (https://vwireiot.com)

Usage:
    python 05_smart_home.py
"""

import time
import random
import threading
from datetime import datetime
from vwire import Vwire, VwireConfig

# =============================================================================
# CONFIGURATION
# =============================================================================

AUTH_TOKEN = "your-device-auth-token-here"
config = VwireConfig()

# =============================================================================
# SMART HOME STATE
# =============================================================================

class SmartHomeState:
    """
    Holds the state of all smart home devices.
    
    In a real application, these would be connected to actual hardware:
    - Relays for lights
    - HVAC system
    - PIR motion sensors
    - Door/window sensors
    """
    
    def __init__(self):
        # Controllable outputs
        self.living_room_light = False
        self.bedroom_light = False
        self.thermostat_target = 22.0
        self.fan_speed = 0  # 0=off, 1=low, 2=medium, 3=high
        
        # Sensor states
        self.current_temp = 21.0
        self.motion_detected = False
        self.door_open = False
        self.hvac_running = False
        self.hvac_mode = "idle"  # idle, heating, cooling


home = SmartHomeState()

# =============================================================================
# VWIRE CLIENT
# =============================================================================

device = Vwire(AUTH_TOKEN, config=config)

# =============================================================================
# COMMAND HANDLERS (Dashboard → Device)
# =============================================================================

@device.on_virtual_write(0)
def handle_living_room_light(value):
    """Control living room light from dashboard switch."""
    home.living_room_light = (value == "1")
    
    # In real application: GPIO.output(LIVING_ROOM_RELAY, home.living_room_light)
    
    status = "ON 💡" if home.living_room_light else "OFF ⚫"
    print(f"🏠 Living Room Light: {status}")
    
    # Send feedback
    device.virtual_write(13, f"Living room {status}")


@device.on_virtual_write(1)
def handle_bedroom_light(value):
    """Control bedroom light from dashboard switch."""
    home.bedroom_light = (value == "1")
    
    status = "ON 💡" if home.bedroom_light else "OFF ⚫"
    print(f"🛏️  Bedroom Light: {status}")
    
    device.virtual_write(13, f"Bedroom {status}")


@device.on_virtual_write(2)
def handle_thermostat(value):
    """Set thermostat target from dashboard slider."""
    try:
        home.thermostat_target = float(value)
        home.thermostat_target = max(16, min(30, home.thermostat_target))
        
        print(f"🌡️  Thermostat set to: {home.thermostat_target}°C")
        device.virtual_write(13, f"Target: {home.thermostat_target}°C")
        
    except ValueError:
        print(f"Invalid thermostat value: {value}")


@device.on_virtual_write(3)
def handle_fan_speed(value):
    """Set fan speed from dashboard slider (0-3)."""
    try:
        home.fan_speed = int(float(value))
        home.fan_speed = max(0, min(3, home.fan_speed))
        
        speed_names = ["OFF", "LOW", "MEDIUM", "HIGH"]
        print(f"🌀 Fan speed: {speed_names[home.fan_speed]}")
        device.virtual_write(13, f"Fan: {speed_names[home.fan_speed]}")
        
    except ValueError:
        print(f"Invalid fan speed: {value}")


# =============================================================================
# SENSOR SIMULATION (Device → Dashboard)
# =============================================================================

def simulate_hvac():
    """Simulate HVAC system controlling temperature."""
    diff = home.thermostat_target - home.current_temp
    
    if abs(diff) > 0.5:
        home.hvac_running = True
        if diff > 0:
            home.hvac_mode = "heating"
            home.current_temp += 0.1
        else:
            home.hvac_mode = "cooling"
            home.current_temp -= 0.1
    else:
        home.hvac_running = False
        home.hvac_mode = "idle"
    
    # Add environmental noise
    home.current_temp += random.gauss(0, 0.02)
    home.current_temp = round(home.current_temp, 1)


def simulate_motion():
    """Simulate motion sensor events."""
    # Random motion detection (5% chance per check)
    if random.random() < 0.05:
        home.motion_detected = True
        return True
    home.motion_detected = False
    return False


def simulate_door():
    """Simulate door sensor events."""
    # Random door state change (1% chance)
    if random.random() < 0.01:
        home.door_open = not home.door_open
        return True
    return False


motion_cooldown = 0

def send_sensor_data():
    """Send all sensor readings to dashboard."""
    global motion_cooldown
    
    # Simulate HVAC
    simulate_hvac()
    
    # Simulate motion with cooldown
    if motion_cooldown > 0:
        motion_cooldown -= 1
    elif simulate_motion():
        motion_cooldown = 10  # Keep motion active for 10 cycles
        print("🚶 Motion detected!")
    
    # Simulate door
    if simulate_door():
        status = "OPENED 🚪" if home.door_open else "CLOSED 🔒"
        print(f"🚪 Door {status}")
    
    # Send to dashboard
    device.virtual_write(10, home.current_temp)
    device.virtual_write(11, "1" if home.motion_detected else "0")
    device.virtual_write(12, "1" if home.door_open else "0")
    
    # Send HVAC status
    hvac_status = f"{home.hvac_mode.upper()}" if home.hvac_running else "IDLE"
    device.virtual_write(14, hvac_status)


def print_status():
    """Print home status to console."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print()
    print(f"{'='*50}")
    print(f"🏠 Smart Home Status - {timestamp}")
    print(f"{'='*50}")
    print(f"  Living Room: {'💡 ON' if home.living_room_light else '⚫ OFF'}")
    print(f"  Bedroom:     {'💡 ON' if home.bedroom_light else '⚫ OFF'}")
    print(f"  Temperature: 🌡️  {home.current_temp}°C (target: {home.thermostat_target}°C)")
    print(f"  HVAC:        {'🔥' if home.hvac_mode == 'heating' else '❄️' if home.hvac_mode == 'cooling' else '⏸️'} {home.hvac_mode.upper()}")
    print(f"  Fan:         🌀 {['OFF', 'LOW', 'MED', 'HIGH'][home.fan_speed]}")
    print(f"  Motion:      {'🚶 DETECTED' if home.motion_detected else '✅ Clear'}")
    print(f"  Door:        {'🚪 OPEN' if home.door_open else '🔒 Closed'}")
    print(f"{'='*50}")
    print()


# =============================================================================
# CONNECTION HANDLERS
# =============================================================================

@device.on_connected
def on_connected():
    """Setup when connected."""
    print("✅ Connected to Vwire server!")
    
    # Send sensor data every 2 seconds
    device.timer.set_interval(2000, send_sensor_data)
    
    # Print status every 15 seconds
    device.timer.set_interval(15000, print_status)
    
    # Send initial status
    device.virtual_write(13, "Smart Home Online")
    send_sensor_data()


@device.on_disconnected
def on_disconnected():
    """Handle disconnection."""
    print("❌ Disconnected from server!")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("🏠 Vwire IoT - Smart Home Controller")
    print("=" * 60)
    print()
    print("Dashboard Controls (V0-V3):")
    print("  V0: Living Room Light (switch)")
    print("  V1: Bedroom Light (switch)")
    print("  V2: Thermostat Target (slider, 16-30°C)")
    print("  V3: Fan Speed (slider, 0-3)")
    print()
    print("Sensor Data (V10-V14):")
    print("  V10: Current Temperature (gauge)")
    print("  V11: Motion Detected (LED)")
    print("  V12: Door Status (LED)")
    print("  V13: Status Message")
    print("  V14: HVAC State")
    print()
    print(f"Server: {config.server}:{config.mqtt_port}")
    print()
    
    # Connect
    print("Connecting...")
    if not device.connect():
        print("❌ Failed to connect!")
        return
    
    print()
    print("Smart home controller running... Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        device.run()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Shutting down smart home...")
    finally:
        device.disconnect()
        print("✅ Disconnected.")


if __name__ == "__main__":
    main()
