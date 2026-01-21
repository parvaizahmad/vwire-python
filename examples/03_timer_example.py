"""
Timer Example - Scheduled Tasks with VwireTimer
================================================

This example demonstrates using VwireTimer for scheduled tasks,
similar to Arduino's BlynkTimer.

Timers allow you to:
- Send sensor data at regular intervals
- Check button states frequently
- Run background tasks without blocking

Hardware: Any Python environment (Raspberry Pi, PC, etc.)
Platform: Vwire IoT (https://vwireiot.com)

Usage:
    python 03_timer_example.py
"""

import random
from vwire import Vwire, VwireConfig, VwireTimer

# =============================================================================
# CONFIGURATION
# =============================================================================

AUTH_TOKEN = "your-device-auth-token-here"
config = VwireConfig()

# =============================================================================
# VWIRE CLIENT
# =============================================================================

device = Vwire(AUTH_TOKEN, config=config)

# The device has a built-in timer: device.timer
# You can also create standalone timers: timer = VwireTimer()

# =============================================================================
# SIMULATED SENSORS
# =============================================================================

def read_temperature():
    """Simulate temperature sensor reading."""
    return round(22 + random.gauss(0, 2), 1)

def read_humidity():
    """Simulate humidity sensor reading."""
    return round(55 + random.gauss(0, 5), 1)

def read_pressure():
    """Simulate pressure sensor reading."""
    return round(1013 + random.gauss(0, 3), 1)

def check_button():
    """Simulate button check (returns True 5% of the time)."""
    return random.random() < 0.05

# =============================================================================
# TIMER CALLBACKS
# =============================================================================

def send_temperature():
    """Send temperature reading to V0."""
    temp = read_temperature()
    device.virtual_write(0, temp)
    print(f"[TEMP]  Temperature: {temp}C → V0")

def send_humidity():
    """Send humidity reading to V1."""
    humidity = read_humidity()
    device.virtual_write(1, humidity)
    print(f"[HUM] Humidity: {humidity}% → V1")

def send_pressure():
    """Send pressure reading to V2."""
    pressure = read_pressure()
    device.virtual_write(2, pressure)
    print(f"[PRES] Pressure: {pressure} hPa → V2")

def check_buttons():
    """Check button states (runs frequently)."""
    if check_button():
        print("🔘 Button pressed!")
        device.virtual_write(5, "1")

def heartbeat():
    """Send heartbeat/uptime to server."""
    import time
    uptime = int(time.time())
    device.virtual_write(10, uptime)
    # Don't print to avoid spam

# =============================================================================
# EVENT HANDLERS
# =============================================================================

@device.on_connected
def on_connected():
    """Called when connected - setup timers here."""
    print("[OK] Connected!")
    print("Setting up timers...")
    
    # Schedule temperature reading every 5 seconds
    device.timer.set_interval(5000, send_temperature)
    
    # Schedule humidity reading every 7 seconds
    device.timer.set_interval(7000, send_humidity)
    
    # Schedule pressure reading every 10 seconds
    device.timer.set_interval(10000, send_pressure)
    
    # Check buttons every 100ms (fast polling)
    device.timer.set_interval(100, check_buttons)
    
    # Send heartbeat every 30 seconds
    device.timer.set_interval(30000, heartbeat)
    
    print(f"Active timers: {device.timer.get_num_timers()}")
    print()

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("Vwire IoT - Timer Example")
    print("=" * 60)
    print()
    print("This example demonstrates VwireTimer for scheduled tasks.")
    print("Similar to Arduino's BlynkTimer.")
    print()
    print("Timers configured:")
    print("  - Temperature: every 5 seconds → V0")
    print("  - Humidity: every 7 seconds → V1")
    print("  - Pressure: every 10 seconds → V2")
    print("  - Button check: every 100ms")
    print("  - Heartbeat: every 30 seconds → V10")
    print()
    
    # Connect
    print("Connecting...")
    if not device.connect():
        print("Failed to connect!")
        return
    
    print()
    print("Running... Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        # Run the event loop
        device.run()
        
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        device.timer.stop()
        device.disconnect()
        print("Disconnected.")


# =============================================================================
# STANDALONE TIMER EXAMPLE
# =============================================================================

def standalone_timer_example():
    """
    Example using VwireTimer independently.
    
    Useful when you need timers without the Vwire client.
    """
    from vwire import VwireTimer
    import time
    
    timer = VwireTimer()
    
    counter = [0]  # Use list to allow modification in closure
    
    def tick():
        counter[0] += 1
        print(f"Tick #{counter[0]}")
    
    def one_time_task():
        print("One-time task executed!")
    
    # Run every 1 second
    timer.set_interval(1000, tick)
    
    # Run once after 5 seconds
    timer.set_timeout(5000, one_time_task)
    
    print("Running standalone timer for 10 seconds...")
    
    # Manual loop
    start = time.time()
    while time.time() - start < 10:
        timer.run()
        time.sleep(0.01)  # Small delay
    
    print(f"Timer ran {counter[0]} times")


if __name__ == "__main__":
    main()
