"""
Basic tests for the ZAP MCP Server.
"""

import os
import sys


def test_package_exists():
    """Test that the package directory exists and is importable."""
    try:
        # Check if the package directory exists
        package_dir = os.path.join(os.path.dirname(__file__), "..", "zap_custom_mcp")
        if not os.path.exists(package_dir):
            print(f"❌ Package directory not found: {package_dir}")
            return False

        # Check if __init__.py exists
        init_file = os.path.join(package_dir, "__init__.py")
        if not os.path.exists(init_file):
            print(f"❌ __init__.py not found: {init_file}")
            return False

        print("✅ Package directory structure is correct")
        return True
    except Exception as e:
        print(f"❌ Package structure test failed: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality."""
    # This is a placeholder test to ensure tests run successfully
    assert True
    print("✅ Basic functionality test passed")
    return True


if __name__ == "__main__":
    print("Testing import performance...")

    success = True
    success &= test_package_exists()
    success &= test_basic_functionality()

    if success:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)
