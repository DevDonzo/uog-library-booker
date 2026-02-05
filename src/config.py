"""
Configuration handling for the Library Booker.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RoomPreferences:
    """Room booking preferences."""
    capacity: int = 1
    preferred_rooms: List[str] = field(default_factory=list)
    excluded_rooms: List[str] = field(default_factory=list)


@dataclass
class TimePreferences:
    """Time-related preferences."""
    preferred_start_times: List[str] = field(default_factory=lambda: [
        "10:00", "11:00", "12:00", "13:00", "14:00"
    ])
    booking_duration_hours: int = 2
    days_in_advance: int = 2


@dataclass
class ScheduleSettings:
    """Scheduler settings."""
    enabled: bool = True
    run_time: str = "00:05"
    retry_on_failure: bool = True
    max_retries: int = 3


@dataclass
class NotificationSettings:
    """Notification settings."""
    enabled: bool = True
    email: str = ""
    desktop_notification: bool = True


@dataclass
class AdvancedSettings:
    """Advanced configuration settings."""
    headless_mode: bool = False
    wait_timeout: int = 10
    login_timeout: int = 180
    screenshot_on_error: bool = True
    log_level: str = "INFO"
    use_chrome_profile: bool = True
    use_existing_chrome_profile: bool = False


@dataclass
class Config:
    """Main configuration container."""
    booking_url: str = "https://cal.lib.uoguelph.ca/spaces?lid=1536&gid=0&c=0"
    chrome_profile_path: str = ""
    room_preferences: RoomPreferences = field(default_factory=RoomPreferences)
    time_preferences: TimePreferences = field(default_factory=TimePreferences)
    schedule: ScheduleSettings = field(default_factory=ScheduleSettings)
    notifications: NotificationSettings = field(default_factory=NotificationSettings)
    advanced: AdvancedSettings = field(default_factory=AdvancedSettings)

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create Config from dictionary."""
        return cls(
            booking_url=data.get("booking_url", cls.booking_url),
            chrome_profile_path=data.get("chrome_profile_path", ""),
            room_preferences=RoomPreferences(**data.get("room_preferences", {})),
            time_preferences=TimePreferences(**data.get("time_preferences", {})),
            schedule=ScheduleSettings(**data.get("schedule", {})),
            notifications=NotificationSettings(**data.get("notifications", {})),
            advanced=AdvancedSettings(**data.get("advanced", {})),
        )

    @classmethod
    def load(cls, config_path: str = "config.json") -> "Config":
        """Load configuration from JSON file."""
        path = Path(config_path)
        if not path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(path, 'r') as f:
            data = json.load(f)

        logger.info("Configuration loaded successfully")
        return cls.from_dict(data)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "booking_url": self.booking_url,
            "chrome_profile_path": self.chrome_profile_path,
            "room_preferences": {
                "capacity": self.room_preferences.capacity,
                "preferred_rooms": self.room_preferences.preferred_rooms,
                "excluded_rooms": self.room_preferences.excluded_rooms,
            },
            "time_preferences": {
                "preferred_start_times": self.time_preferences.preferred_start_times,
                "booking_duration_hours": self.time_preferences.booking_duration_hours,
                "days_in_advance": self.time_preferences.days_in_advance,
            },
            "schedule": {
                "enabled": self.schedule.enabled,
                "run_time": self.schedule.run_time,
                "retry_on_failure": self.schedule.retry_on_failure,
                "max_retries": self.schedule.max_retries,
            },
            "notifications": {
                "enabled": self.notifications.enabled,
                "email": self.notifications.email,
                "desktop_notification": self.notifications.desktop_notification,
            },
            "advanced": {
                "headless_mode": self.advanced.headless_mode,
                "wait_timeout": self.advanced.wait_timeout,
                "login_timeout": self.advanced.login_timeout,
                "screenshot_on_error": self.advanced.screenshot_on_error,
                "log_level": self.advanced.log_level,
                "use_chrome_profile": self.advanced.use_chrome_profile,
                "use_existing_chrome_profile": self.advanced.use_existing_chrome_profile,
            },
        }


def get_credentials() -> tuple[Optional[str], Optional[str]]:
    """Get UoG credentials from environment variables."""
    email = os.getenv("UOG_EMAIL", "").strip() or None
    password = os.getenv("UOG_PASSWORD", "").strip() or None
    return email, password
