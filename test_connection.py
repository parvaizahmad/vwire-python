"""Simple connection test - no handlers, no sync"""
import time
import logging

logging.basicConfig(level=logging.DEBUG)

from vwire import Vwire, VwireConfig

AUTH_TOKEN = "iot_bLiNAWiSmOdCHf2yTrXHHgqudDgWszKm"

device = Vwire(AUTH_TOKEN)

print("Connecting...")
if device.connect():
    print("Connected! Waiting 30 seconds...")
    start = time.time()
    while time.time() - start < 30:
        time.sleep(1)
        if device.connected:
            print(f"  Still connected ({int(time.time() - start)}s)")
        else:
            print(f"  DISCONNECTED at {int(time.time() - start)}s")
            break
    print("Done")
    device.disconnect()
else:
    print("Failed to connect")
