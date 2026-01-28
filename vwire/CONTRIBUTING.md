# Contributing to Vwire IoT Python Library

Thank you for your interest in contributing to the Vwire IoT Python library! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a welcoming and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/vwireiot/vwire-python/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS
   - Relevant code snippets or error messages

### Suggesting Features

1. Open an issue with the `enhancement` label
2. Describe the feature and its use case
3. Explain how it aligns with the Arduino library API (if applicable)

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest`
5. Run linting: `black . && flake8`
6. Commit with clear messages: `git commit -m 'Add amazing feature'`
7. Push to your fork: `git push origin feature/amazing-feature`
8. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/vwire-python.git
cd vwire-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -e ".[dev]"
```

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Maximum line length: 100 characters
- Use type hints for public APIs
- Write docstrings for all public methods

### Example

```python
def virtual_send(self, pin: int, value: Union[str, int, float]) -> bool:
    """
    Send a value to a virtual pin.
    
    Matches Arduino library Vwire.virtualSend().
    
    Args:
        pin: Virtual pin number (0-255)
        value: Value to send (will be converted to string)
        
    Returns:
        True if published successfully
        
    Example:
        device.virtual_send(0, 25.5)
    """
    ...
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=vwire --cov-report=html

# Run specific test file
pytest tests/test_core.py
```

## API Design Guidelines

The Python library should mirror the Arduino Vwire library API:

| Arduino | Python |
|---------|--------|
| `camelCase` methods | `snake_case` methods |
| `Vwire.virtualSend(V0, val)` | `device.virtual_send(0, val)` |
| `VWIRE_RECEIVE(V0)` handler | `@device.on_virtual_receive(0)` decorator |

When adding new features:

1. Check if equivalent exists in Arduino library
2. Use consistent naming conventions
3. Provide both decorator and method-based APIs where appropriate

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public methods
- Include examples in docstrings
- Update examples/ if API changes

## Release Process

1. Update version in `__init__.py` and `pyproject.toml`
2. Update CHANGELOG.md
3. Create a release PR
4. After merge, tag the release
5. Build and publish to PyPI

## Questions?

- Open a discussion on GitHub
- Email: support@vwireiot.com

Thank you for contributing! 🎉
