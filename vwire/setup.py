"""
Vwire IoT Python Library - Setup Configuration

For development installation:
    pip install -e .

For production installation:
    pip install vwire-iot
"""

from setuptools import setup, find_packages
import os

# Read README for long description
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="vwire-iot",
    version="3.1.0",
    author="Vwire IoT Team",
    author_email="support@vwireiot.com",
    description="Official Python client for Vwire IoT Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vwireiot/vwire-python",
    project_urls={
        "Documentation": "https://docs.vwireiot.com",
        "Dashboard": "https://vwireiot.com",
        "Bug Tracker": "https://github.com/vwireiot/vwire-python/issues",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Home Automation",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware",
        "Topic :: Scientific/Engineering",
    ],
    keywords=[
        "iot",
        "mqtt",
        "raspberry-pi",
        "esp32",
        "esp8266",
        "arduino",
        "home-automation",
        "sensors",
        "vwire",
    ],
    python_requires=">=3.8",
    install_requires=[
        "paho-mqtt>=2.0.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "raspberry-pi": [
            "RPi.GPIO>=0.7.0",
            "Adafruit-DHT>=1.4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "vwire-test=vwire.utils:get_version",
        ],
    },
)
