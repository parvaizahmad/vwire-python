"""
Raspberry Pi GPIO Example - Real Hardware Control
==================================================

This example demonstrates using Vwire with real GPIO hardware
on a Raspberry Pi. Control LEDs, read buttons, and interface
with sensors.

Hardware Required:
    - Raspberry Pi (any model with GPIO)
    - LED + 220Ω resistor on GPIO 17
    - Button on GPIO 27 (with pull-down resistor)
    - Optional: DHT22 sensor on GPIO 4

Pin Mapping:
    GPIO 17 - LED output
    GPIO 27 - Button input
    GPIO 18 - PWM output (LED brightness)
    GPIO 4  - DHT22 sensor (optional)

Virtual Pin Mapping:
    V0 - LED control (from dashboard switch)
    V1 - PWM brightness (from dashboard slider)
    V2 - Temperature reading (to dashboard)
    V3 - Humidity reading (to dashboard)
    V4 - Button state (to dashboard)

Platform: Raspberry Pi OS
Requirements: 
    pip install vwire-iot RPi.GPIO

Usage:
    python 06_raspberry_pi_gpio.py
"""

import time
from vwire import Vwire, VwireConfig

# =============================================================================
# RASPBERRY PI GPIO SETUP
# =============================================================================

# Try to import GPIO library, use mock if not on Pi
try:
    import RPi.GPIO as GPIO
    ON_RASPBERRY_PI = True
except ImportError:
    print("[WARN]  RPi.GPIO not found. Running in simulation mode.")
    ON_RASPBERRY_PI = False
    
    # Mock GPIO for testing on non-Pi systems
    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT"
        IN = "IN"
        HIGH = 1
        LOW = 0
        PUD_DOWN = "PUD_DOWN"
        
        @staticmethod
        def setmode(mode): pass
        
        @staticmethod
        def setup(pin, mode, pull_up_down=None): 
            print(f"  GPIO {pin} configured as {mode}")
        
        @staticmethod
        def output(pin, value):
            print(f"  GPIO {pin} → {'HIGH' if value else 'LOW'}")
        
        @staticmethod
        def input(pin):
            import random
            return random.choice([0, 1])
        
        @staticmethod
        def cleanup(): pass
        
        class PWM:
            def __init__(self, pin, freq):
                self.pin = pin
                print(f"  PWM on GPIO {pin} at {freq}Hz")
            
            def start(self, duty): pass
            def ChangeDutyCycle(self, duty):
                print(f"  PWM duty cycle: {duty}%")
            def stop(self): pass
    
    GPIO = MockGPIO()

# =============================================================================
# CONFIGURATION
# =============================================================================

AUTH_TOKEN = "your-device-auth-token-here"
config = VwireConfig()

# GPIO Pin definitions
LED_PIN = 17
BUTTON_PIN = 27
PWM_PIN = 18
DHT_PIN = 4

# =============================================================================
# GPIO INITIALIZATION
# =============================================================================

def setup_gpio():
    """Initialize GPIO pins."""
    print("Setting up GPIO...")
    
    GPIO.setmode(GPIO.BCM)
    
    # LED output
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.output(LED_PIN, GPIO.LOW)
    
    # Button input with pull-down
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    # PWM for LED brightness
    GPIO.setup(PWM_PIN, GPIO.OUT)
    global pwm
    pwm = GPIO.PWM(PWM_PIN, 1000)  # 1kHz frequency
    pwm.start(0)
    
    print("GPIO setup complete!")

# =============================================================================
# SENSOR READING
# =============================================================================

def read_dht22():
    """
    Read DHT22 temperature/humidity sensor.
    
    Returns:
        Tuple of (temperature, humidity) or (None, None) if read fails
    """
    try:
        # Try to use Adafruit DHT library
        import Adafruit_DHT
        humidity, temperature = Adafruit_DHT.read_retry(
            Adafruit_DHT.DHT22, DHT_PIN
        )
        if humidity is not None and temperature is not None:
            return round(temperature, 1), round(humidity, 1)
    except ImportError:
        pass
    except Exception as e:
        print(f"DHT22 read error: {e}")
    
    # Return simulated values if sensor not available
    import random
    return round(22 + random.gauss(0, 2), 1), round(55 + random.gauss(0, 5), 1)

# =============================================================================
# VWIRE CLIENT
# =============================================================================

device = Vwire(AUTH_TOKEN, config=config)

# Device state
led_state = False
pwm_brightness = 0
last_button_state = 0

# =============================================================================
# COMMAND HANDLERS (Dashboard → Pi)
# =============================================================================

@device.on_virtual_receive(0)
def handle_led_control(value):
    """Control LED from dashboard switch widget."""
    global led_state
    led_state = (value == "1")
    
    GPIO.output(LED_PIN, GPIO.HIGH if led_state else GPIO.LOW)
    
    status = "ON 💡" if led_state else "OFF ⚫"
    print(f"LED: {status}")


@device.on_virtual_receive(1)
def handle_pwm_brightness(value):
    """Control LED brightness from dashboard slider (0-100)."""
    global pwm_brightness
    
    try:
        pwm_brightness = int(float(value))
        pwm_brightness = max(0, min(100, pwm_brightness))
        
        pwm.ChangeDutyCycle(pwm_brightness)
        print(f"PWM Brightness: {pwm_brightness}%")
        
    except ValueError:
        print(f"Invalid PWM value: {value}")

# =============================================================================
# SENSOR READING TASKS (Pi → Dashboard)
# =============================================================================

def send_sensor_data():
    """Read sensors and send to dashboard."""
    # Read DHT22
    temp, humidity = read_dht22()
    
    if temp is not None:
        device.virtual_send(2, temp)
        device.virtual_send(3, humidity)
        print(f"[TEMP]  Temp: {temp}C | [HUM] Humidity: {humidity}%")


def check_button():
    """Check button state and send changes."""
    global last_button_state
    
    current_state = GPIO.input(BUTTON_PIN)
    
    if current_state != last_button_state:
        last_button_state = current_state
        device.virtual_send(4, str(current_state))
        
        if current_state:
            print("🔘 Button PRESSED!")
        else:
            print("🔘 Button RELEASED")

# =============================================================================
# CONNECTION HANDLERS
# =============================================================================

@device.on_connected
def on_connected():
    """Setup timers when connected."""
    print("[OK] Connected to Vwire server!")
    
    # Read sensors every 5 seconds
    device.timer.set_interval(5000, send_sensor_data)
    
    # Check button every 50ms
    device.timer.set_interval(50, check_button)
    
    # Initial sensor read
    send_sensor_data()


@device.on_disconnected
def on_disconnected():
    """Handle disconnection."""
    print("[ERROR] Disconnected from server!")

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("🍓 Vwire IoT - Raspberry Pi GPIO Example")
    print("=" * 60)
    print()
    print(f"Running on: {'Raspberry Pi' if ON_RASPBERRY_PI else 'Simulation Mode'}")
    print()
    print("GPIO Configuration:")
    print(f"  LED Output:    GPIO {LED_PIN}")
    print(f"  Button Input:  GPIO {BUTTON_PIN}")
    print(f"  PWM Output:    GPIO {PWM_PIN}")
    print(f"  DHT22 Sensor:  GPIO {DHT_PIN}")
    print()
    print("Virtual Pins:")
    print("  V0: LED control (switch)")
    print("  V1: PWM brightness (slider 0-100)")
    print("  V2: Temperature (gauge)")
    print("  V3: Humidity (gauge)")
    print("  V4: Button state (LED)")
    print()
    
    # Setup GPIO
    setup_gpio()
    print()
    
    # Connect
    print("Connecting to Vwire server...")
    if not device.connect():
        print("[ERROR] Failed to connect!")
        GPIO.cleanup()
        return
    
    print()
    print("Running... Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        device.run()
        
    except KeyboardInterrupt:
        print("\n\n[STOP]  Stopping...")
    finally:
        # Cleanup
        pwm.stop()
        GPIO.cleanup()
        device.disconnect()
        print("[OK] GPIO cleaned up. Disconnected.")


if __name__ == "__main__":
    main()
