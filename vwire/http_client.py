"""
Vwire HTTP Client Module

Provides HTTP-based communication with the Vwire platform for simple
request/response operations without persistent MQTT connections.
"""

import json
import requests
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger("vwire")


class VwireHTTP:
    """
    HTTP-based client for Vwire platform.
    
    Use this for simple request/response operations without persistent connection.
    Ideal for:
    - Scripts that run periodically (cron jobs, scheduled tasks)
    - Serverless functions (AWS Lambda, Google Cloud Functions)
    - Simple one-off data sends
    - Environments where MQTT is not available
    
    Example:
        from vwire import VwireHTTP
        
        # Create client
        client = VwireHTTP("your_auth_token")
        
        # Write to virtual pin
        client.virtual_write(0, 25.5)
        
        # Write multiple values at once
        client.write_batch({
            "V0": 25.5,
            "V1": 60,
            "V2": 1013
        })
    """
    
    def __init__(
        self,
        auth_token: str,
        server: str = "api.vwireiot.com",
        port: int = 443,
        use_ssl: bool = True,
        timeout: int = 10
    ):
        """
        Initialize HTTP client.
        
        Args:
            auth_token: Device authentication token from Vwire dashboard
            server: Server hostname (default: api.vwireiot.com)
            port: HTTP API port (default: 443)
            use_ssl: Use HTTPS (default: True)
            timeout: Request timeout in seconds (default: 10)
            
        Example:
            # Production (default)
            client = VwireHTTP("your_token")
            
            # Local development
            client = VwireHTTP("your_token", server="localhost", port=3001, use_ssl=False)
        """
        self._auth_token = auth_token
        self._server = server
        self._port = port
        self._use_ssl = use_ssl
        self._timeout = timeout
        
        protocol = "https" if use_ssl else "http"
        self._base_url = f"{protocol}://{server}:{port}/api/v1"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._auth_token}",
            "X-Auth-Token": self._auth_token
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make HTTP request to server."""
        url = f"{self._base_url}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    timeout=self._timeout
                )
            else:
                response = requests.post(
                    url,
                    headers=self._get_headers(),
                    json=data,
                    timeout=self._timeout
                )
            
            response.raise_for_status()
            return response.json() if response.text else {}
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout: {url}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None
    
    # ========== Pin Operations ==========
    
    def write_pin(self, pin: str, value: Union[str, int, float]) -> bool:
        """
        Write a value to a pin.
        
        Args:
            pin: Pin identifier (e.g., "V0", "V1", "V2")
            value: Value to write
            
        Returns:
            True if successful, False otherwise
            
        Example:
            client.write_pin("V0", 25.5)
            client.write_pin("V1", "Online")
        """
        url = f"{self._base_url}/webhooks/device/{self._auth_token}"
        payload = {"pin": pin, "value": str(value)}
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self._timeout
            )
            return response.status_code == 200
        except requests.RequestException as e:
            logger.error(f"Error writing to pin {pin}: {e}")
            return False
    
    def virtual_write(self, pin: int, value: Union[str, int, float]) -> bool:
        """
        Write to a virtual pin.
        
        Args:
            pin: Virtual pin number (0-255)
            value: Value to write
            
        Returns:
            True if successful
            
        Example:
            client.virtual_write(0, 25.5)
            client.virtual_write(1, "Hello")
        """
        return self.write_pin(f"V{pin}", value)
    
    def write_batch(self, data: Dict[str, Any]) -> bool:
        """
        Write multiple pin values at once.
        
        Args:
            data: Dictionary mapping pin names to values
                  e.g., {"V0": 25.5, "V1": 60, "V2": "ON"}
            
        Returns:
            True if all writes successful
            
        Example:
            client.write_batch({
                "V0": 25.5,      # Temperature
                "V1": 60,        # Humidity
                "V2": 1013,      # Pressure
                "V3": "Online",  # Status
            })
        """
        success = True
        for pin, value in data.items():
            if not self.write_pin(pin, value):
                success = False
                logger.warning(f"Failed to write to pin {pin}")
        return success
    
    def read_pin(self, pin: str) -> Optional[str]:
        """
        Read the current value of a pin from server.
        
        Args:
            pin: Pin identifier (e.g., "V0", "V1")
            
        Returns:
            Pin value as string, or None if failed
            
        Example:
            value = client.read_pin("V0")
        """
        result = self._make_request("GET", f"device/{self._auth_token}/pin/{pin}")
        if result:
            return result.get("value")
        return None
    
    def virtual_read(self, pin: int) -> Optional[str]:
        """
        Read a virtual pin value from server.
        
        Args:
            pin: Virtual pin number
            
        Returns:
            Value as string, or None
            
        Example:
            temp = client.virtual_read(0)
        """
        return self.read_pin(f"V{pin}")
    
    # ========== Utility Methods ==========
    
    def get_device_info(self) -> Optional[Dict]:
        """
        Get device information from server.
        
        Returns:
            Dictionary with device info, or None if failed
            
        Example:
            info = client.get_device_info()
            print(f"Device: {info['name']}")
        """
        return self._make_request("GET", f"device/{self._auth_token}/info")
    
    def ping(self) -> bool:
        """
        Check if server is reachable.
        
        Returns:
            True if server responds
            
        Example:
            if client.ping():
                print("Server is online")
        """
        try:
            response = requests.get(
                f"{self._base_url}/health",
                timeout=self._timeout
            )
            return response.status_code == 200
        except Exception:
            return False


def quick_write(
    auth_token: str,
    pin: str,
    value: Any,
    server: str = "api.vwireiot.com",
    port: int = 443
) -> bool:
    """
    Quick utility to write a value to a pin without creating a client instance.
    
    Args:
        auth_token: Device authentication token
        pin: Pin identifier (e.g., "V0", "V1")
        value: Value to write
        server: Server hostname
        port: HTTP port
        
    Returns:
        True if successful
        
    Example:
        from vwire import quick_write
        
        quick_write("your_token", "V0", 25.5)
    """
    client = VwireHTTP(auth_token, server, port)
    return client.write_pin(pin, value)
