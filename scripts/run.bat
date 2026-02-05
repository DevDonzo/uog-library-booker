@echo off
REM UoG Library Room Booker - Quick run script

REM Navigate to script directory
cd /d "%~dp0.."

REM Check if Python is available
where python >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install it first.
    exit /b 1
)

REM Check if requirements are installed
python -c "import selenium" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Run the booker
if "%1"=="check" (
    python library_booker.py --check
) else if "%1"=="dry-run" (
    python library_booker.py --dry-run
) else if "%1"=="schedule" (
    python scheduler.py --daemon
) else if "%1"=="test" (
    python test.py
) else (
    python library_booker.py %*
)
