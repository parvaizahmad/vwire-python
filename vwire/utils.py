"""
Vwire Utility Functions

Common utilities and helper functions for the Vwire library.
"""

import socket
import logging
from typing import Optional

# Package version
__version__ = "2.0.0"


def get_version() -> str:
    """
    Get the library version string.
    
    Returns:
        Version string (e.g., "2.0.0")
    """
    return __version__


def get_local_ip() -> str:
    """
    Get the local machine's IP address (not localhost/127.0.0.1).
    
    Useful on Windows with WSL where localhost:1883 may be intercepted
    by WSL before Docker can handle it.
    
    Returns:
        Local IP address string, or "localhost" if detection fails
        
    Example:
        from vwire import get_local_ip
        
        # Use local IP instead of localhost
        config = VwireConfig.development(server=get_local_ip())
    """
    try:
        # Create a socket to determine the local IP that would route to the internet
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1.0)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def setup_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging for the Vwire library.
    
    Args:
        level: Logging level (default: INFO)
        format_string: Custom format string (optional)
        
    Returns:
        Configured logger instance
        
    Example:
        from vwire.utils import setup_logging
        import logging
        
        # Enable debug logging
        setup_logging(level=logging.DEBUG)
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(level=level, format=format_string)
    logger = logging.getLogger("vwire")
    logger.setLevel(level)
    
    return logger


def parse_pin(pin_str: str) -> tuple:
    """
    Parse a pin string into type and number.
    
    Args:
        pin_str: Pin string (e.g., "V0", "V1", "V255")
        
    Returns:
        Tuple of (pin_type, pin_number)
        
    Raises:
        ValueError: If pin string is invalid
        
    Example:
        pin_type, pin_num = parse_pin("V5")
        # pin_type = "V", pin_num = 5
    """
    if not pin_str or len(pin_str) < 2:
        raise ValueError(f"Invalid pin: {pin_str}")
    
    pin_type = pin_str[0].upper()
    if pin_type != "V":
        raise ValueError(f"Invalid pin type: {pin_type}. Only virtual pins (V) are supported.")
    
    try:
        pin_num = int(pin_str[1:])
    except ValueError:
        raise ValueError(f"Invalid pin number: {pin_str[1:]}")
    
    return (pin_type, pin_num)


def validate_auth_token(token: str) -> bool:
    """
    Validate an authentication token format.
    
    Args:
        token: Authentication token string
        
    Returns:
        True if token format is valid
        
    Note:
        This only validates format, not actual authentication.
    """
    if not token or not isinstance(token, str):
        return False
    
    # Token should be at least 20 characters
    if len(token) < 20:
        return False
    
    # Basic format check (alphanumeric with hyphens/underscores)
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    return all(c in allowed_chars for c in token)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between min and max bounds.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
        
    Example:
        # Clamp PWM value to 0-255
        pwm = clamp(sensor_value, 0, 255)
    """
    return max(min_val, min(max_val, value))


def map_range(
    value: float,
    in_min: float,
    in_max: float,
    out_min: float,
    out_max: float
) -> float:
    """
    Map a value from one range to another (like Arduino's map function).
    
    Args:
        value: Input value
        in_min: Input range minimum
        in_max: Input range maximum
        out_min: Output range minimum
        out_max: Output range maximum
        
    Returns:
        Mapped value
        
    Example:
        # Convert 0-1023 ADC reading to 0-100%
        percentage = map_range(adc_value, 0, 1023, 0, 100)
    """
    if in_max == in_min:
        return out_min
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
