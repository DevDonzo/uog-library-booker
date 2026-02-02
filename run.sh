#!/bin/bash
# Quick run script for Library Booker

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

case "$1" in
    "check")
        python library_booker.py --check
        ;;
    "dry-run")
        python library_booker.py --dry-run
        ;;
    "book")
        python library_booker.py
        ;;
    "schedule")
        python scheduler.py --daemon
        ;;
    "setup")
        python scheduler.py --setup
        ;;
    *)
        echo "University of Guelph Library Room Booker"
        echo ""
        echo "Usage: ./run.sh [command]"
        echo ""
        echo "Commands:"
        echo "  check     - Check room availability"
        echo "  dry-run   - Test booking without submitting"
        echo "  book      - Book a room now"
        echo "  schedule  - Start the scheduler daemon"
        echo "  setup     - Show cron/task scheduler setup"
        echo ""
        ;;
esac
