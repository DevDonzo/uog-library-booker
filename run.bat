@echo off
REM Quick run script for Library Booker (Windows)

cd /d "%~dp0"

if "%1"=="check" (
    python library_booker.py --check
) else if "%1"=="dry-run" (
    python library_booker.py --dry-run
) else if "%1"=="book" (
    python library_booker.py
) else if "%1"=="schedule" (
    python scheduler.py --daemon
) else if "%1"=="setup" (
    python scheduler.py --setup
) else (
    echo University of Guelph Library Room Booker
    echo.
    echo Usage: run.bat [command]
    echo.
    echo Commands:
    echo   check     - Check room availability
    echo   dry-run   - Test booking without submitting
    echo   book      - Book a room now
    echo   schedule  - Start the scheduler daemon
    echo   setup     - Show task scheduler setup
    echo.
)
