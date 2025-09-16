"""
Basic tests for the ZAP MCP Server.
"""

import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_import_config():
    """Test that config module can be imported."""
    try:
        import config

        assert hasattr(config, "ZAP_BASE")
        assert hasattr(config, "APIKEY")
        assert hasattr(config, "MCP_HOST")
        assert hasattr(config, "MCP_PORT")
    except ImportError as e:
        pytest.fail(f"Failed to import config: {e}")


def test_import_utils():
    """Test that utils module can be imported."""
    try:
        import utils

        assert hasattr(utils, "get_logger")
    except ImportError as e:
        pytest.fail(f"Failed to import utils: {e}")


def test_import_models():
    """Test that models module can be imported."""
    try:
        import models

        assert hasattr(models, "ScanResult")
    except ImportError as e:
        pytest.fail(f"Failed to import models: {e}")


def test_basic_functionality():
    """Test basic functionality."""
    # This is a placeholder test to ensure pytest runs successfully
    assert True


if __name__ == "__main__":
    pytest.main([__file__])
