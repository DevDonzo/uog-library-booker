#!/usr/bin/env python3
"""
Test script for the UoG Library Booker.
Runs through various test scenarios to verify the system works.
"""

import subprocess
import sys
from pathlib import Path


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def run_command(cmd: list, description: str) -> bool:
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


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    print_header("Checking Dependencies")

    all_good = True

    try:
        import selenium
        print(f"✓ selenium {selenium.__version__}")
    except ImportError:
        print("✗ selenium not installed")
        all_good = False

    try:
        import webdriver_manager
        print("✓ webdriver-manager installed")
    except ImportError:
        print("✗ webdriver-manager not installed")
        all_good = False

    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv installed")
    except ImportError:
        print("✗ python-dotenv not installed")
        all_good = False

    return all_good


def check_config() -> bool:
    """Check if config.json exists."""
    print_header("Checking Configuration")

    config_file = Path("config.json")
    if config_file.exists():
        print("✓ config.json found")
        return True
    else:
        print("✗ config.json not found")
        print("  → Copy config.example.json to config.json and configure it")
        return False


def check_env() -> bool:
    """Check if .env exists."""
    print_header("Checking Environment")

    env_file = Path(".env")
    if env_file.exists():
        print("✓ .env found")
        return True
    else:
        print("⚠ .env not found (optional)")
        print("  → Copy .env.example to .env for credential storage")
        return True  # Not required


def check_project_structure() -> bool:
    """Check if project structure is correct."""
    print_header("Checking Project Structure")

    required_files = [
        "src/__init__.py",
        "src/booker.py",
        "src/auth.py",
        "src/config.py",
        "src/utils.py",
        "src/scheduler.py",
        "library_booker.py",
        "scheduler.py",
        "requirements.txt",
    ]

    all_good = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} missing")
            all_good = False

    return all_good


def main() -> int:
    """Run all tests."""
    print_header("UoG Library Booker - Test Suite")

    tests = []

    # Check project structure
    tests.append(("Project Structure", check_project_structure()))

    # Check dependencies
    tests.append(("Dependencies", check_dependencies()))

    # Check config
    tests.append(("Configuration", check_config()))

    # Check env
    tests.append(("Environment", check_env()))

    # Test availability check (only if config exists)
    if all(result for name, result in tests if name in ("Dependencies", "Configuration")):
        tests.append((
            "Availability Check",
            run_command(
                ["python3", "library_booker.py", "--check"],
                "Check room availability"
            )
        ))

        # Test dry run
        if tests[-1][1]:
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
