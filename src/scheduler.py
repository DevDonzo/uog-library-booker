"""
Scheduler for the Library Room Booker.
Runs the booking script at configured times.
"""

import json
import logging
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .utils import get_logs_dir, print_header

logger = logging.getLogger(__name__)


class BookingScheduler:
    """Manages scheduled booking attempts."""

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the scheduler.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.running = True

        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Set up logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure scheduler-specific logging."""
        logs_dir = get_logs_dir()
        log_file = logs_dir / "scheduler.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(str(log_file)),
                logging.StreamHandler()
            ]
        )

    def _signal_handler(self, signum, frame) -> None:
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

        hour, minute = map(int, run_time_str.split(":"))
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if next_run <= now:
            next_run += timedelta(days=1)

        return next_run

    def _run_booking(self) -> bool:
        """Execute the booking script."""
        logger.info("Executing booking script...")

        # Use the src package booker
        src_dir = Path(__file__).parent
        max_retries = self.config.get("schedule", {}).get("max_retries", 3)
        retry_on_failure = self.config.get("schedule", {}).get("retry_on_failure", True)

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Booking attempt {attempt}/{max_retries}")

                result = subprocess.run(
                    [
                        sys.executable, "-m", "src.booker",
                        "--config", self.config_path
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                    cwd=src_dir.parent
                )

                if result.returncode == 0:
                    logger.info("Booking completed successfully!")
                    return True
                else:
                    logger.warning(f"Booking attempt failed: {result.stderr}")

                    if not retry_on_failure:
                        break

                    if attempt < max_retries:
                        wait_time = 60 * attempt
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

    def run_scheduled(self) -> None:
        """Run the scheduler loop."""
        if not self.config.get("schedule", {}).get("enabled", True):
            logger.warning("Scheduling is disabled in config")
            return

        run_time = self.config.get("schedule", {}).get("run_time", "00:05")
        logger.info("Starting booking scheduler")
        logger.info(f"Configured run time: {run_time}")

        while self.running:
            next_run = self._get_next_run_time()
            logger.info(f"Next booking attempt: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

            while self.running and datetime.now() < next_run:
                time.sleep(60)

            if not self.running:
                break

            self._run_booking()
            time.sleep(120)  # Avoid running twice in same minute

        logger.info("Scheduler stopped")


def get_system_scheduler_instructions() -> str:
    """Get OS-specific scheduler setup instructions."""
    import platform

    script_path = Path(__file__).resolve()
    python_path = sys.executable
    working_dir = script_path.parent.parent

    system = platform.system()
    instructions = []

    instructions.append("=" * 60)

    if system in ("Darwin", "Linux"):
        cron_line = f"5 0 * * * cd {working_dir} && {python_path} -m src.scheduler --run-once"

        instructions.append("CRON SETUP INSTRUCTIONS")
        instructions.append("=" * 60)
        instructions.append("\nTo schedule daily booking at 12:05 AM, add this to your crontab:\n")
        instructions.append(f"  {cron_line}")
        instructions.append("\nTo edit crontab, run:")
        instructions.append("  crontab -e")
        instructions.append("\nOr to add automatically, run:")
        instructions.append(f'  (crontab -l 2>/dev/null; echo "{cron_line}") | crontab -')

    elif system == "Windows":
        task_name = "UoGLibraryBooker"

        instructions.append("WINDOWS TASK SCHEDULER SETUP")
        instructions.append("=" * 60)
        instructions.append("\nRun PowerShell as Administrator and execute:\n")
        instructions.append(f"""
$action = New-ScheduledTaskAction -Execute '"{python_path}"' -Argument '"-m" "src.scheduler" "--run-once"' -WorkingDirectory '"{working_dir}"'
$trigger = New-ScheduledTaskTrigger -Daily -At 12:05AM
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun
Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -Settings $settings -Description "Automatically book UoG library rooms"
""")

    instructions.append("=" * 60)
    return "\n".join(instructions)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Library Booker Scheduler")
    parser.add_argument("--config", "-c", default="config.json", help="Path to config file")
    parser.add_argument("--run-once", action="store_true", help="Run booking once and exit")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (continuous scheduling)")
    parser.add_argument("--setup", action="store_true", help="Show OS scheduler setup instructions")

    args = parser.parse_args()

    if args.setup:
        print(get_system_scheduler_instructions())
        return

    scheduler = BookingScheduler(config_path=args.config)

    if args.run_once:
        success = scheduler.run_once()
        sys.exit(0 if success else 1)
    elif args.daemon:
        scheduler.run_scheduled()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
