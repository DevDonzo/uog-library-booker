#!/bin/bash
# UoG Library Room Booker - Quick run script

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install it first."
    exit 1
fi

# Ensure PYTHONPATH includes current directory
export PYTHONPATH=$PYTHONPATH:.

# Run the modules
case "$1" in
    check)
        python3 -m src.booker --check
        ;;
    dry-run)
        python3 -m src.booker --dry-run
        ;;
    schedule)
        python3 -m src.scheduler --daemon
        ;;
    test)
        python3 tests/test_runner.py
        ;;
    *)
        python3 -m src.booker "$@"
        ;;
esac
