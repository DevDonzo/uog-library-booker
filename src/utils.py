"""
Utility functions for the Library Booker.
"""

import logging
import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# Room capacity mapping
ROOM_CAPACITIES = {
    # 2-Person Study Rooms
    "603": 2, "604": 2,
    # 1-Person Study Rooms
    "315": 1, "316": 1, "322": 1, "323": 1, "324": 1, "325": 1,
    "326": 1, "327": 1, "328": 1, "329": 1, "330": 1, "331": 1, "332": 1,
}


def convert_to_24h(time_str: str) -> str:
    """
    Convert 12-hour time string to 24-hour format.

    Args:
        time_str: Time string like "9:30pm" or "11:00am"

    Returns:
        24-hour format string like "21:30" or "11:00"
    """
    try:
        time_str = time_str.lower().strip()
        is_pm = "pm" in time_str
        time_str = time_str.replace("am", "").replace("pm", "").strip()

        if ":" in time_str:
            hour, minute = time_str.split(":")
        else:
            hour = time_str
            minute = "00"

        hour = int(hour)

        if is_pm and hour != 12:
            hour += 12
        elif not is_pm and hour == 12:
            hour = 0

        return f"{hour:02d}:{minute}"
    except Exception:
        return time_str


def time_to_minutes(time_str: str) -> int:
    """
    Convert time string to minutes since midnight for sorting.

    Args:
        time_str: Time in 12-hour or 24-hour format

    Returns:
        Minutes since midnight
    """
    time_24h = convert_to_24h(time_str)
    try:
        hour, minute = time_24h.split(':')
        return int(hour) * 60 + int(minute)
    except Exception:
        return 9999


def get_screenshots_dir() -> Path:
    """Get the screenshots directory path."""
    project_dir = Path(__file__).parent.parent
    screenshots_dir = project_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)
    return screenshots_dir


def get_logs_dir() -> Path:
    """Get the logs directory path."""
    project_dir = Path(__file__).parent.parent
    logs_dir = project_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def take_screenshot(driver, name: str = "screenshot") -> Optional[str]:
    """
    Take a screenshot for debugging.

    Args:
        driver: Selenium WebDriver instance
        name: Base name for the screenshot file

    Returns:
        Path to saved screenshot or None if failed
    """
    try:
        screenshots_dir = get_screenshots_dir()
        filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = screenshots_dir / filename
        driver.save_screenshot(str(filepath))
        logger.info(f"Screenshot saved: {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"Could not save screenshot: {e}")
        return None


def send_desktop_notification(title: str, message: str) -> None:
    """
    Send a desktop notification.

    Args:
        title: Notification title
        message: Notification message
    """
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            os.system(f"""osascript -e 'display notification "{message}" with title "{title}"'""")
        elif system == "Linux":
            os.system(f'notify-send "{title}" "{message}"')
        elif system == "Windows":
            # Would require additional library
            pass
    except Exception:
        pass


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Set up logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    """
    logs_dir = get_logs_dir()
    log_file = log_file or str(logs_dir / "booking.log")

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def get_chrome_profile_path() -> Path:
    """Get Chrome automation profile path."""
    project_dir = Path(__file__).parent.parent
    return project_dir / ".chrome_automation_profile"


def print_header(text: str, char: str = "=", width: int = 70) -> None:
    """Print a formatted header."""
    print("\n" + char * width)
    print(f"  {text}")
    print(char * width + "\n")
