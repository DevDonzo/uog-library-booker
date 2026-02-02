#!/usr/bin/env python3
"""
Test script for the UoG Library Booker.
Runs through various test scenarios to verify the system works.
"""

import sys
import subprocess
import time
from pathlib import Path

def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"Testing: {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        success = result.returncode == 0
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"\n{status}\n")

        return success
    except subprocess.TimeoutExpired:
        print("✗ FAILED (timeout)\n")
        return False
    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print_header("Checking Dependencies")

    try:
        import selenium
        print(f"✓ selenium {selenium.__version__}")
    except ImportError:
        print("✗ selenium not installed")
        return False

    try:
        import webdriver_manager
        print(f"✓ webdriver-manager installed")
    except ImportError:
        print("✗ webdriver-manager not installed")
        return False

    return True

def check_config():
    """Check if config.json exists."""
    print_header("Checking Configuration")

    config_file = Path("config.json")
    if config_file.exists():
        print(f"✓ config.json found")
        return True
    else:
        print("✗ config.json not found")
        return False

def main():
    """Run all tests."""
    print_header("UoG Library Booker - Test Suite")

    tests = []

    # Check dependencies
    tests.append(("Dependencies", check_dependencies()))

    # Check config
    tests.append(("Configuration", check_config()))

    # Test availability check
    if tests[-1][1]:  # Only if config exists
        tests.append((
            "Availability Check",
            run_command(
                ["python3", "library_booker.py", "--check"],
                "Check room availability"
            )
        ))

    # Test dry run
    if tests[-1][1]:  # Only if previous test passed
        tests.append((
            "Dry Run Booking",
            run_command(
                ["python3", "library_booker.py", "--dry-run"],
                "Test booking process (dry run)"
            )
        ))

    # Print summary
    print_header("Test Summary")

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    for name, result in tests:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status:12} {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! The system is ready to use.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
