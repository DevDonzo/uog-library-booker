#!/bin/bash
# UoG Library Room Booker - Quick run script

# Navigate to script directory
cd "$(dirname "$0")/.."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install it first."
    exit 1
fi

# Check if requirements are installed
if ! python3 -c "import selenium" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Run the booker
case "$1" in
    check)
        python3 library_booker.py --check
        ;;
    dry-run)
        python3 library_booker.py --dry-run
        ;;
    schedule)
        python3 scheduler.py --daemon
        ;;
    test)
        python3 test.py
        ;;
    *)
        python3 library_booker.py "$@"
        ;;
esac
