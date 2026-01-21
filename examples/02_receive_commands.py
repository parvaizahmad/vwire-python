"""
Receive Commands Example - Handle Commands from Vwire Dashboard
================================================================

This example demonstrates how to receive and handle commands from the
Vwire dashboard. When users interact with widgets (buttons, sliders, etc.),
your device receives the values.

The API mirrors the Arduino library's VWIRE_WRITE() handlers.

Hardware: Any Python environment (Raspberry Pi, PC, etc.)
Platform: Vwire IoT (https://vwireiot.com)

Dashboard Setup:
    1. Create a project in the Vwire dashboard
    2. Add widgets and link them to virtual pins:
       - V0: Switch widget (for LED control)
       - V1: Slider widget (for motor speed, 0-255)
       - V2: Color picker (for RGB)
       - V3: Button widget (momentary action)

Usage:
    python 02_receive_commands.py
"""

from vwire import Vwire, VwireConfig

# =============================================================================
# CONFIGURATION
# =============================================================================

AUTH_TOKEN = "your-device-auth-token-here"

# Use secure connection (default)
config = VwireConfig()

# For local development:
# config = VwireConfig.development("localhost")

# =============================================================================
# DEVICE STATE (Simulated Hardware)
# =============================================================================

# In a real application, these would control actual hardware
class DeviceState:
    led_on = False
    motor_speed = 0
    rgb_color = "#ffffff"
    servo_angle = 90

state = DeviceState()

# =============================================================================
# VWIRE CLIENT
# =============================================================================

device = Vwire(AUTH_TOKEN, config=config)

# =============================================================================
# EVENT HANDLERS - Similar to Arduino VWIRE_WRITE(pin)
# =============================================================================

@device.on_virtual_write(0)
def handle_led(value):
    """
    Handle LED control from Switch widget.
    
    Similar to Arduino:
        VWIRE_WRITE(V0) {
            int value = param.asInt();
            digitalWrite(LED_PIN, value);
        }
    """
    state.led_on = (value == "1")
    status = "ON 💡" if state.led_on else "OFF ⚫"
    print(f"LED: {status}")
    
    # Send feedback to dashboard
    device.virtual_write(10, f"LED is {status}")


@device.on_virtual_write(1)
def handle_motor_speed(value):
    """
    Handle motor speed from Slider widget.
    
    Dashboard slider sends values 0-255.
    """
    try:
        state.motor_speed = int(float(value))
        print(f"⚙️  Motor speed: {state.motor_speed}")
        
        # In real application: analogWrite(MOTOR_PIN, state.motor_speed)
        
    except ValueError:
        print(f"Invalid motor value: {value}")


@device.on_virtual_write(2)
def handle_rgb_color(value):
    """
    Handle RGB color from Color Picker widget.
    
    Color picker sends hex color string like "#FF5500".
    """
    state.rgb_color = value
    print(f"🎨 RGB Color: {state.rgb_color}")
    
    # Parse RGB values if needed
    if value.startswith("#") and len(value) == 7:
        r = int(value[1:3], 16)
        g = int(value[3:5], 16)
        b = int(value[5:7], 16)
        print(f"   R={r}, G={g}, B={b}")


@device.on_virtual_write(3)
def handle_button_press(value):
    """
    Handle momentary button press.
    
    Button sends "1" when pressed.
    """
    if value == "1":
        print("🔘 Button PRESSED!")
        
        # Trigger some action
        print("   → Triggering action...")
        device.virtual_write(10, "Action triggered!")
        
        # Example: toggle LED
        state.led_on = not state.led_on
        device.virtual_write(0, "1" if state.led_on else "0")


@device.on_virtual_write(4)
def handle_servo(value):
    """
    Handle servo angle from Slider widget (0-180).
    """
    try:
        state.servo_angle = int(float(value))
        state.servo_angle = max(0, min(180, state.servo_angle))
        print(f"🔧 Servo angle: {state.servo_angle}°")
        
    except ValueError:
        print(f"Invalid servo value: {value}")


# Digital pin handler example
@device.on_digital_write(13)
def handle_digital_pin(value):
    """
    Handle digital pin write from dashboard.
    
    Similar to Arduino's direct pin control.
    """
    print(f"📍 Digital pin 13: {'HIGH' if value else 'LOW'}")


# =============================================================================
# CONNECTION EVENT HANDLERS
# =============================================================================

@device.on_connected
def on_connected():
    """Called when device connects to server."""
    print("✅ Connected to Vwire server!")
    print("   Syncing pin values...")
    device.sync_all()


@device.on_disconnected
def on_disconnected():
    """Called when device disconnects from server."""
    print("❌ Disconnected from server!")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("Vwire IoT - Receive Commands Example")
    print("=" * 60)
    print(f"Server: {config.server}:{config.mqtt_port}")
    print()
    print("This device will respond to dashboard widget interactions.")
    print("Configure widgets on these pins:")
    print("  V0 - Switch (LED control)")
    print("  V1 - Slider (Motor speed, 0-255)")
    print("  V2 - Color Picker (RGB color)")
    print("  V3 - Button (Trigger action)")
    print("  V4 - Slider (Servo angle, 0-180)")
    print()
    
    # Connect to server
    print("Connecting...")
    if not device.connect():
        print("Failed to connect!")
        return
    
    print()
    print("Waiting for commands... Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        # Run event loop (blocks forever)
        device.run()
        
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        device.disconnect()
        print("Disconnected.")


if __name__ == "__main__":
    main()
