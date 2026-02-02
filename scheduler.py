#!/usr/bin/env python3
"""
Scheduler for the Library Room Booker.
Runs the booking script at configured times.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import signal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BookingScheduler:
    """Manages scheduled booking attempts."""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.running = True

        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Shutdown signal received")
        self.running = False

    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            sys.exit(1)

    def _get_next_run_time(self) -> datetime:
        """Calculate the next scheduled run time."""
        schedule = self.config.get("schedule", {})
        run_time_str = schedule.get("run_time", "00:05")

        # Parse the run time
        hour, minute = map(int, run_time_str.split(":"))

        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If we've passed today's run time, schedule for tomorrow
        if next_run <= now:
            next_run += timedelta(days=1)

        return next_run

    def _run_booking(self) -> bool:
        """Execute the booking script."""
        logger.info("Executing booking script...")

        script_path = Path(__file__).parent / "library_booker.py"
        max_retries = self.config.get("schedule", {}).get("max_retries", 3)
        retry_on_failure = self.config.get("schedule", {}).get("retry_on_failure", True)

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Booking attempt {attempt}/{max_retries}")

                result = subprocess.run(
                    [sys.executable, str(script_path), "--config", self.config_path],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )

                if result.returncode == 0:
                    logger.info("Booking completed successfully!")
                    return True
                else:
                    logger.warning(f"Booking attempt failed: {result.stderr}")

                    if not retry_on_failure:
                        break

                    if attempt < max_retries:
                        wait_time = 60 * attempt  # Increasing backoff
                        logger.info(f"Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)

            except subprocess.TimeoutExpired:
                logger.error("Booking script timed out")
            except Exception as e:
                logger.error(f"Error running booking script: {e}")

        logger.error("All booking attempts failed")
        return False

    def run_once(self) -> bool:
        """Run the booking script once immediately."""
        return self._run_booking()

    def run_scheduled(self):
        """Run the scheduler loop."""
        if not self.config.get("schedule", {}).get("enabled", True):
            logger.warning("Scheduling is disabled in config")
            return

        logger.info("Starting booking scheduler")
        logger.info(f"Configured run time: {self.config.get('schedule', {}).get('run_time', '00:05')}")

        while self.running:
            next_run = self._get_next_run_time()
            logger.info(f"Next booking attempt: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

            # Wait until the next run time
            while self.running and datetime.now() < next_run:
                # Check every minute
                time.sleep(60)

            if not self.running:
                break

            # Run the booking
            self._run_booking()

            # Wait a bit to avoid running twice in the same minute
            time.sleep(120)

        logger.info("Scheduler stopped")


def setup_system_scheduler():
    """Set up OS-level scheduling (cron/Task Scheduler)."""
    import platform

    script_path = Path(__file__).resolve()
    python_path = sys.executable
    working_dir = script_path.parent

    if platform.system() == "Darwin" or platform.system() == "Linux":
        # Create cron job
        cron_line = f"5 0 * * * cd {working_dir} && {python_path} {script_path} --run-once"

        print("\n" + "="*60)
        print("CRON SETUP INSTRUCTIONS")
        print("="*60)
        print("\nTo schedule daily booking at 12:05 AM, add this to your crontab:")
        print(f"\n  {cron_line}")
        print("\nTo edit crontab, run:")
        print("  crontab -e")
        print("\nOr to add automatically, run:")
        print(f'  (crontab -l 2>/dev/null; echo "{cron_line}") | crontab -')
        print("="*60 + "\n")

    elif platform.system() == "Windows":
        # Create Windows Task Scheduler command
        task_name = "UoGLibraryBooker"

        print("\n" + "="*60)
        print("WINDOWS TASK SCHEDULER SETUP")
        print("="*60)
        print("\nRun PowerShell as Administrator and execute:")
        print(f'''
$action = New-ScheduledTaskAction -Execute '"{python_path}"' -Argument '"{script_path}" --run-once' -WorkingDirectory '"{working_dir}"'
$trigger = New-ScheduledTaskTrigger -Daily -At 12:05AM
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun
Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -Settings $settings -Description "Automatically book UoG library rooms"
''')
        print("="*60 + "\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Library Booker Scheduler")
    parser.add_argument("--config", "-c", default="config.json", help="Path to config file")
    parser.add_argument("--run-once", action="store_true", help="Run booking once and exit")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (continuous scheduling)")
    parser.add_argument("--setup", action="store_true", help="Show OS scheduler setup instructions")

    args = parser.parse_args()

    if args.setup:
        setup_system_scheduler()
        return

    scheduler = BookingScheduler(config_path=args.config)

    if args.run_once:
        success = scheduler.run_once()
        sys.exit(0 if success else 1)
    elif args.daemon:
        scheduler.run_scheduled()
    else:
        # Default: show help
        parser.print_help()


if __name__ == "__main__":
    main()
