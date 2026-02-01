"""Examples configuration.

These are runnable examples, not part of the test suite.
Run explicitly: pytest examples/ -v

Note: pyproject.toml sets testpaths=["tests"] so `pytest` alone won't run these.
"""

import pytest


def pytest_configure(config):
    """Register custom markers for examples."""
    config.addinivalue_line("markers", "example: mark as example (not core test suite)")


def pytest_collection_modifyitems(config, items):
    """Mark all items in examples/ with the example marker."""
    for item in items:
        if "examples" in str(item.fspath):
            item.add_marker(pytest.mark.example)
