@echo off
REM UoG Library Room Booker - Quick run script

REM Navigate to project root
cd /d "%~dp0.."

REM Run the modules
if "%1"=="check" (
    python -m src.booker --check
) else if "%1"=="dry-run" (
    python -m src.booker --dry-run
) else if "%1"=="schedule" (
    python -m src.scheduler --daemon
) else if "%1"=="test" (
    python tests/test_runner.py
) else (
    python -m src.booker %*
)
