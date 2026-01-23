"""
Data Logger Example - Production-Ready Logging Application
===========================================================

A complete data logging application suitable for production use.
Demonstrates best practices for reliable IoT data collection.

Features:
    - Configurable logging intervals
    - Multiple transport options (MQTT or HTTP)
    - Error handling and recovery
    - Local data buffering
    - Command-line configuration
    - CSV export option

Use Cases:
    - Environmental monitoring
    - Industrial sensor networks
    - Agricultural IoT
    - Energy monitoring

Usage:
    # Default MQTT mode
    python 08_data_logger.py
    
    # HTTP mode
    python 08_data_logger.py --mode http
    
    # Custom server
    python 08_data_logger.py --server 192.168.1.100 --port 8883
    
    # Development mode (insecure)
    python 08_data_logger.py --dev
"""

import time
import random
import argparse
import csv
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

# =============================================================================
# SENSOR SIMULATOR
# =============================================================================

@dataclass
class SensorReading:
    """Represents a sensor reading with timestamp."""
    timestamp: datetime
    temperature: float
    humidity: float
    pressure: float
    co2: int
    pm25: float
    noise_db: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "temperature": self.temperature,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "co2": self.co2,
            "pm25": self.pm25,
            "noise_db": self.noise_db
        }


class SensorSimulator:
    """
    Simulates various environmental sensors.
    
    In production, replace these with actual sensor readings.
    """
    
    def __init__(self):
        self.base_temp = 22.0
        self.base_humidity = 55.0
    
    def read(self) -> SensorReading:
        """Read all sensors and return a SensorReading."""
        return SensorReading(
            timestamp=datetime.now(),
            temperature=round(self.base_temp + random.gauss(0, 3), 2),
            humidity=round(self.base_humidity + random.gauss(0, 10), 2),
            pressure=round(1013 + random.gauss(0, 5), 2),
            co2=round(400 + random.gauss(0, 50)),
            pm25=round(max(0, 15 + random.gauss(0, 10)), 1),
            noise_db=round(40 + random.gauss(0, 10), 1)
        )


# =============================================================================
# DATA BUFFER (for offline storage)
# =============================================================================

class DataBuffer:
    """
    Buffers data locally when connection is lost.
    
    Stores readings in memory and optionally to CSV file.
    """
    
    def __init__(self, max_size: int = 1000, csv_path: Optional[str] = None):
        self.buffer: List[SensorReading] = []
        self.max_size = max_size
        self.csv_path = csv_path
        
        if csv_path and not os.path.exists(csv_path):
            self._init_csv()
    
    def _init_csv(self):
        """Initialize CSV file with headers."""
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'temperature', 'humidity', 'pressure',
                'co2', 'pm25', 'noise_db'
            ])
    
    def add(self, reading: SensorReading):
        """Add a reading to the buffer."""
        if len(self.buffer) >= self.max_size:
            self.buffer.pop(0)  # Remove oldest
        
        self.buffer.append(reading)
        
        if self.csv_path:
            self._append_to_csv(reading)
    
    def _append_to_csv(self, reading: SensorReading):
        """Append reading to CSV file."""
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                reading.timestamp.isoformat(),
                reading.temperature,
                reading.humidity,
                reading.pressure,
                reading.co2,
                reading.pm25,
                reading.noise_db
            ])
    
    def get_unsent(self, count: int = 10) -> List[SensorReading]:
        """Get readings that haven't been sent yet."""
        return self.buffer[:count]
    
    def mark_sent(self, count: int):
        """Mark readings as sent (remove from buffer)."""
        self.buffer = self.buffer[count:]
    
    @property
    def size(self) -> int:
        return len(self.buffer)


# =============================================================================
# MQTT DATA LOGGER
# =============================================================================

def run_mqtt_logger(auth_token: str, server: str, port: int, 
                    interval: int, use_tls: bool, buffer: DataBuffer):
    """Run data logger using MQTT transport."""
    from vwire import Vwire, VwireConfig
    
    # Configure connection
    if use_tls:
        config = VwireConfig.custom(server, port, use_tls=True)
    else:
        config = VwireConfig.development(server, port)
    
    device = Vwire(auth_token, config=config)
    sensors = SensorSimulator()
    
    # Pin mapping
    PIN_MAP = {
        "temperature": 0,
        "humidity": 1,
        "pressure": 2,
        "co2": 3,
        "pm25": 4,
        "noise_db": 5,
    }
    
    reading_count = 0
    
    def send_reading():
        nonlocal reading_count
        
        reading = sensors.read()
        reading_count += 1
        
        # Send to Vwire
        device.virtual_write(PIN_MAP["temperature"], reading.temperature)
        device.virtual_write(PIN_MAP["humidity"], reading.humidity)
        device.virtual_write(PIN_MAP["pressure"], reading.pressure)
        device.virtual_write(PIN_MAP["co2"], reading.co2)
        device.virtual_write(PIN_MAP["pm25"], reading.pm25)
        device.virtual_write(PIN_MAP["noise_db"], reading.noise_db)
        
        # Buffer locally
        buffer.add(reading)
        
        # Log to console
        ts = reading.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] #{reading_count} | "
              f"[TEMP] {reading.temperature}C | "
              f"[HUM] {reading.humidity}% | "
              f"[PRES] {reading.pressure}hPa | "
              f"CO2: {reading.co2}ppm | "
              f"PM2.5: {reading.pm25}ug/m3")
    
    @device.on_connected
    def on_connected():
        print("[OK] Connected to server!")
        device.timer.set_interval(interval * 1000, send_reading)
        send_reading()  # Send immediately
    
    @device.on_disconnected
    def on_disconnected():
        print("[WARN]  Disconnected! Data will be buffered locally.")
    
    # Connect and run
    print(f"Connecting to {server}:{port}...")
    if not device.connect(timeout=30):
        print("[ERROR] Failed to connect!")
        return
    
    try:
        device.run()
    except KeyboardInterrupt:
        print(f"\n\n[STATS] Total readings: {reading_count}")
        print(f"[FILE] Buffered readings: {buffer.size}")
    finally:
        device.disconnect()


# =============================================================================
# HTTP DATA LOGGER
# =============================================================================

def run_http_logger(auth_token: str, server: str, port: int,
                    interval: int, use_tls: bool, buffer: DataBuffer):
    """Run data logger using HTTP transport."""
    from vwire import VwireHTTP
    
    client = VwireHTTP(auth_token, server, port, use_tls)
    sensors = SensorSimulator()
    
    reading_count = 0
    
    print(f"HTTP Logger started - sending every {interval} seconds")
    print("-" * 60)
    
    try:
        while True:
            reading = sensors.read()
            reading_count += 1
            
            # Prepare batch data
            data = {
                "V0": reading.temperature,
                "V1": reading.humidity,
                "V2": reading.pressure,
                "V3": reading.co2,
                "V4": reading.pm25,
                "V5": reading.noise_db,
            }
            
            # Send via HTTP
            if client.write_batch(data):
                ts = reading.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{ts}] #{reading_count} [OK] Sent | "
                      f"[TEMP] {reading.temperature}C | "
                      f"[HUM] {reading.humidity}%")
            else:
                print(f"[#{reading_count}] [ERROR] Send failed - buffering locally")
                buffer.add(reading)
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n\n[STATS] Total readings: {reading_count}")
        print(f"[FILE] Buffered readings: {buffer.size}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Vwire IoT Data Logger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python 08_data_logger.py --token YOUR_TOKEN
    python 08_data_logger.py --token YOUR_TOKEN --mode http
    python 08_data_logger.py --token YOUR_TOKEN --dev --server localhost
        """
    )
    
    parser.add_argument("--token", "-t", 
                        default="your-device-auth-token-here",
                        help="Device auth token")
    parser.add_argument("--server", "-s", 
                        default="mqtt.vwire.io",
                        help="Server hostname")
    parser.add_argument("--port", "-p", 
                        type=int, default=None,
                        help="Server port (default: 8883 for MQTT, 443 for HTTP)")
    parser.add_argument("--mode", "-m", 
                        choices=["mqtt", "http"], default="mqtt",
                        help="Transport mode")
    parser.add_argument("--interval", "-i", 
                        type=int, default=10,
                        help="Logging interval in seconds")
    parser.add_argument("--csv", 
                        default=None,
                        help="CSV file path for local backup")
    parser.add_argument("--dev", 
                        action="store_true",
                        help="Development mode (no TLS)")
    
    args = parser.parse_args()
    
    # Determine port
    if args.port is None:
        if args.dev:
            args.port = 1883 if args.mode == "mqtt" else 3001
        else:
            args.port = 8883 if args.mode == "mqtt" else 443
    
    # Determine TLS
    use_tls = not args.dev
    
    # Initialize buffer
    buffer = DataBuffer(csv_path=args.csv)
    
    # Print configuration
    print("=" * 60)
    print("[STATS] Vwire IoT Data Logger")
    print("=" * 60)
    print(f"Server:   {args.server}:{args.port}")
    print(f"Mode:     {args.mode.upper()}")
    print(f"TLS:      {'Enabled' if use_tls else 'Disabled'}")
    print(f"Interval: {args.interval} seconds")
    if args.csv:
        print(f"CSV:      {args.csv}")
    print("=" * 60)
    print()
    
    # Run appropriate logger
    if args.mode == "mqtt":
        run_mqtt_logger(args.token, args.server, args.port, 
                       args.interval, use_tls, buffer)
    else:
        run_http_logger(args.token, args.server, args.port,
                       args.interval, use_tls, buffer)


if __name__ == "__main__":
    main()
