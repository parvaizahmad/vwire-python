"""
Weather Station Example - Complete IoT Sensor Station
======================================================

A comprehensive example simulating a weather station that sends
multiple environmental readings to the Vwire IoT platform.

This example demonstrates:
- Multiple sensor readings
- Realistic data simulation with daily cycles
- Proper data formatting
- Status messages

Pin Mapping:
    V0 - Temperature (C)
    V1 - Humidity (%)
    V2 - Pressure (hPa)
    V3 - Wind Speed (km/h)
    V4 - Wind Direction (degrees)
    V5 - Rain (mm)
    V6 - UV Index
    V7 - Light Level (lux)
    V10 - Status message

Hardware: Any Python environment (Raspberry Pi, PC, etc.)
Platform: Vwire IoT (https://vwireiot.com)

Dashboard Setup:
    Create widgets for each pin:
    - Gauges for temperature, humidity, pressure
    - Value displays for wind, rain, UV
    - Chart/graph widgets for historical data

Usage:
    python 04_weather_station.py
"""

import time
import math
import random
from datetime import datetime
from vwire import Vwire, VwireConfig

# =============================================================================
# CONFIGURATION
# =============================================================================

AUTH_TOKEN = "your-device-auth-token-here"
config = VwireConfig()

# Data send interval (milliseconds)
SEND_INTERVAL = 5000

# =============================================================================
# WEATHER SIMULATOR
# =============================================================================

class WeatherSimulator:
    """
    Simulates realistic weather sensor readings.
    
    In a real application, replace these methods with actual sensor readings
    from DHT22, BMP280, wind sensor, rain gauge, UV sensor, etc.
    """
    
    def __init__(self):
        self.base_temp = 20.0
        self.base_humidity = 50.0
        self.base_pressure = 1013.25
        self.wind_direction = 180
        self.time_offset = random.random() * 1000
    
    def temperature(self) -> float:
        """
        Get temperature with realistic daily cycle.
        Peaks around 14:00, lowest around 05:00.
        """
        hour = datetime.now().hour
        daily_variation = 5 * math.sin((hour - 5) * math.pi / 12)
        noise = random.gauss(0, 0.5)
        return round(self.base_temp + daily_variation + noise, 1)
    
    def humidity(self) -> float:
        """
        Get humidity (inversely related to temperature).
        """
        temp = self.temperature()
        base = self.base_humidity - (temp - self.base_temp) * 2
        noise = random.gauss(0, 3)
        return max(20, min(95, round(base + noise, 1)))
    
    def pressure(self) -> float:
        """
        Get atmospheric pressure with slow variations.
        """
        variation = 10 * math.sin(time.time() / 3600 + self.time_offset)
        noise = random.gauss(0, 0.5)
        return round(self.base_pressure + variation + noise, 1)
    
    def wind_speed(self) -> float:
        """
        Get wind speed with occasional gusts.
        """
        base = 10 + 5 * math.sin(time.time() / 600)
        gust = random.expovariate(0.3) if random.random() < 0.1 else 0
        return round(max(0, base + gust + random.gauss(0, 2)), 1)
    
    def wind_direction(self) -> int:
        """
        Get slowly changing wind direction in degrees.
        """
        self.wind_direction += random.gauss(0, 5)
        self.wind_direction = self.wind_direction % 360
        return round(self.wind_direction)
    
    def rain(self) -> float:
        """
        Get rain amount (usually 0, occasional rain events).
        """
        if random.random() < 0.05:
            return round(random.expovariate(0.5), 1)
        return 0.0
    
    def uv_index(self) -> float:
        """
        Get UV index based on time of day.
        """
        hour = datetime.now().hour
        if 6 <= hour <= 18:
            peak = 8 * math.sin((hour - 6) * math.pi / 12)
            return round(max(0, peak + random.gauss(0, 0.5)), 1)
        return 0.0
    
    def light_level(self) -> int:
        """
        Get light level in lux.
        """
        hour = datetime.now().hour
        if 6 <= hour <= 20:
            peak = 50000 * math.sin((hour - 6) * math.pi / 14)
            noise = random.gauss(0, 1000)
            return max(0, round(peak + noise))
        return random.randint(0, 10)


# =============================================================================
# VWIRE CLIENT & WEATHER STATION
# =============================================================================

device = Vwire(AUTH_TOKEN, config=config)
weather = WeatherSimulator()

def send_weather_data():
    """Send all weather readings to Vwire."""
    
    # Read all sensors
    temp = weather.temperature()
    humidity = weather.humidity()
    pressure = weather.pressure()
    wind_speed = weather.wind_speed()
    wind_dir = weather.wind_direction()
    rain = weather.rain()
    uv = weather.uv_index()
    light = weather.light_level()
    
    # Send to virtual pins
    device.virtual_write(0, temp)
    device.virtual_write(1, humidity)
    device.virtual_write(2, pressure)
    device.virtual_write(3, wind_speed)
    device.virtual_write(4, wind_dir)
    device.virtual_write(5, rain)
    device.virtual_write(6, uv)
    device.virtual_write(7, light)
    
    # Send status message
    timestamp = datetime.now().strftime("%H:%M:%S")
    device.virtual_write(10, f"Updated at {timestamp}")
    
    # Print to console
    print(f"[{timestamp}] [TEMP] {temp:5.1f}C | [HUM] {humidity:4.1f}% | "
          f"[PRES] {pressure:6.1f}hPa | [WIND] {wind_speed:4.1f}km/h @ {wind_dir:3d}deg | "
          f"🌧️ {rain:3.1f}mm | ☀️ UV:{uv:3.1f} | 💡 {light:5d}lux")


@device.on_connected
def on_connected():
    """Setup timer when connected."""
    print("[OK] Connected to Vwire server!")
    
    # Send data every 5 seconds
    device.timer.set_interval(SEND_INTERVAL, send_weather_data)
    
    # Send initial data immediately
    send_weather_data()


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("🌤️  Vwire IoT Weather Station")
    print("=" * 80)
    print()
    print("Pin Mapping:")
    print("  V0: Temperature (C)")
    print("  V1: Humidity (%)")
    print("  V2: Pressure (hPa)")
    print("  V3: Wind Speed (km/h)")
    print("  V4: Wind Direction (deg)")
    print("  V5: Rain (mm)")
    print("  V6: UV Index")
    print("  V7: Light Level (lux)")
    print()
    print(f"Server: {config.server}:{config.mqtt_port}")
    print(f"Update interval: {SEND_INTERVAL/1000} seconds")
    print()
    
    # Connect
    print("Connecting...")
    if not device.connect():
        print("[ERROR] Failed to connect!")
        return
    
    print()
    print("Sending weather data... Press Ctrl+C to stop")
    print("-" * 80)
    
    try:
        device.run()
        
    except KeyboardInterrupt:
        print("\n\n[STOP]  Stopping weather station...")
    finally:
        device.disconnect()
        print("[OK] Disconnected.")


if __name__ == "__main__":
    main()
