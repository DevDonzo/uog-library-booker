"""
Main Library Booker - Automates booking of UoG library study rooms.
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from .auth import AuthenticationHandler
from .utils import (
    ROOM_CAPACITIES,
    convert_to_24h,
    get_chrome_profile_path,
    print_header,
    send_desktop_notification,
    setup_logging,
    take_screenshot,
    time_to_minutes,
)

# Load environment variables
load_dotenv()

# Set up logging
import logging
logger = logging.getLogger(__name__)


class LibraryBooker:
    """Automates booking of UoG library study rooms."""

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the booker with configuration.

        Args:
            config_path: Path to the JSON configuration file
        """
        self.config = self._load_config(config_path)
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.auth_handler: Optional[AuthenticationHandler] = None

        # Set up logging based on config
        log_level = self.config.get("advanced", {}).get("log_level", "INFO")
        setup_logging(log_level)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        import json
        config_file = Path(config_path)
        if not config_file.exists():
            logger.error(f"Configuration file not found: {config_path}")
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, 'r') as f:
            config = json.load(f)

        logger.info("Configuration loaded successfully")
        return config

    def _setup_driver(self) -> None:
        """Set up Chrome WebDriver with profile for saved session."""
        options = Options()

        # Profile configuration
        use_profile = self.config.get("advanced", {}).get("use_chrome_profile", True)
        use_existing = self.config.get("advanced", {}).get("use_existing_chrome_profile", False)
        chrome_profile = self.config.get("chrome_profile_path", "")

        if use_profile:
            if use_existing:
                self._configure_existing_profile(options)
            elif chrome_profile:
                options.add_argument(f"user-data-dir={chrome_profile}")
                options.add_argument("--profile-directory=SeleniumProfile")
                logger.info(f"Using custom Chrome profile: {chrome_profile}")
            else:
                automation_profile = get_chrome_profile_path()
                automation_profile.mkdir(exist_ok=True)
                options.add_argument(f"user-data-dir={automation_profile}")
                logger.info(f"Using automation profile: {automation_profile}")

        # Headless mode
        if self.config.get("advanced", {}).get("headless_mode", False):
            options.add_argument("--headless=new")

        # Stability options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        # Disable automation banner
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            self.driver = webdriver.Chrome(options=options)
            timeout = self.config.get("advanced", {}).get("wait_timeout", 10)
            self.wait = WebDriverWait(self.driver, timeout)

            # Initialize authentication handler
            login_timeout = self.config.get("advanced", {}).get("login_timeout", 180)
            self.auth_handler = AuthenticationHandler(self.driver, self.wait, login_timeout)

            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise

    def _configure_existing_profile(self, options: Options) -> None:
        """Configure options to use existing Chrome profile."""
        home = Path.home()

        if sys.platform == "darwin":
            chrome_user_data = home / "Library/Application Support/Google/Chrome"
        elif sys.platform == "win32":
            chrome_user_data = home / "AppData/Local/Google/Chrome/User Data"
        else:
            chrome_user_data = home / ".config/google-chrome"

        options.add_argument(f"user-data-dir={chrome_user_data}")
        options.add_argument("--profile-directory=Default")
        logger.info(f"Using existing Chrome profile: {chrome_user_data}")

        print_header("WARNING: Using existing Chrome profile")
        print("  You MUST close all Chrome windows before running this script!")

    def _get_target_date(self) -> datetime:
        """Calculate the target booking date."""
        days_advance = self.config.get("time_preferences", {}).get("days_in_advance", 2)
        return datetime.now() + timedelta(days=days_advance)

    def _navigate_to_booking_page(self) -> bool:
        """Navigate to the room booking page."""
        try:
            url = self.config.get("booking_url")
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            time.sleep(2)
            logger.info("Navigation complete")
            return True
        except Exception as e:
            logger.error(f"Error navigating to booking page: {e}")
            return False

    def _ensure_on_booking_page(self) -> bool:
        """Ensure we're on the booking page, handling auth if needed."""
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                current_url = self.driver.current_url or ""

                # Already on booking page
                if "cal.lib.uoguelph.ca" in current_url:
                    try:
                        self.wait.until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, "table, .s-lc-eq-avail, .fc-view")
                            )
                        )
                        logger.info("Successfully on booking page")
                        return True
                    except TimeoutException:
                        logger.debug("Waiting for booking elements...")
                        time.sleep(2)
                        continue

                # On auth page
                if self.auth_handler.is_on_auth_page():
                    logger.info(f"Auth page detected (attempt {attempt + 1}/{max_attempts})")
                    if not self.auth_handler.run_authentication_flow():
                        logger.error("Authentication flow failed")
                        return False
                    time.sleep(2)
                    continue

                logger.debug(f"Unknown page state (attempt {attempt + 1}), waiting...")
                time.sleep(2)

            except Exception as e:
                logger.debug(f"Error in _ensure_on_booking_page: {e}")
                time.sleep(1)

        # Final check
        if "cal.lib.uoguelph.ca" in (self.driver.current_url or ""):
            logger.info("On booking page after auth handling")
            return True

        logger.error("Could not reach booking page after multiple attempts")
        take_screenshot(self.driver, "auth_failed")
        return False

    def _navigate_to_target_date(self) -> bool:
        """Navigate to the target booking date."""
        target_date = self._get_target_date()
        logger.info(f"Target booking date: {target_date.strftime('%A, %B %d, %Y')}")

        try:
            go_to_date_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Go To Date')]"))
            )
            go_to_date_btn.click()
            time.sleep(1)

            days_to_advance = self.config.get("time_preferences", {}).get("days_in_advance", 2)
            for _ in range(days_to_advance):
                try:
                    next_btn = self.driver.find_element(By.XPATH, "//button[contains(@title, 'Next')]")
                    next_btn.click()
                    time.sleep(0.5)
                except Exception:
                    break

            return True
        except Exception as e:
            logger.warning(f"Could not navigate to target date: {e}")
            return True  # Continue with default view

    def _find_available_rooms(self) -> List[Dict[str, Any]]:
        """Find all available room slots matching preferences."""
        available_slots = []
        prefs = self.config.get("room_preferences", {})
        capacity_pref = prefs.get("capacity", 1)
        preferred_rooms = prefs.get("preferred_rooms", [])
        excluded_rooms = prefs.get("excluded_rooms", [])
        preferred_times = self.config.get("time_preferences", {}).get("preferred_start_times", [])

        try:
            available_links = self.driver.find_elements(
                By.XPATH, "//a[contains(@title, 'Available') and not(contains(@title, 'Unavailable'))]"
            )

            for link in available_links:
                title = link.get_attribute("title")
                if not title:
                    continue

                try:
                    parts = title.split(" - ")
                    time_date = parts[0]
                    room_info = parts[1] if len(parts) > 1 else ""
                    room_num = room_info.replace("Room ", "").strip()

                    # Filter by capacity
                    room_capacity = ROOM_CAPACITIES.get(room_num, 1)
                    if capacity_pref and room_capacity != capacity_pref:
                        continue

                    # Filter by excluded rooms
                    if room_num in excluded_rooms:
                        continue

                    # Filter by preferred rooms
                    if preferred_rooms and room_num not in preferred_rooms:
                        continue

                    # Extract and filter by time
                    time_str = time_date.split()[0]
                    if preferred_times:
                        time_24h = convert_to_24h(time_str)
                        if time_24h not in preferred_times:
                            continue

                    slot = {
                        "element": link,
                        "title": title,
                        "room": room_num,
                        "time": time_str,
                        "capacity": room_capacity,
                    }
                    available_slots.append(slot)
                    logger.debug(f"Found available slot: {title}")

                except Exception as e:
                    logger.debug(f"Error parsing slot: {e}")
                    continue

            logger.info(f"Found {len(available_slots)} matching available slots")
            return available_slots

        except Exception as e:
            logger.error(f"Error finding available rooms: {e}")
            return []

    def _select_time_slot(self, slot: Dict[str, Any]) -> bool:
        """Select a time slot for booking."""
        try:
            element = slot["element"]
            logger.info(f"Selecting slot: {slot['title']}")

            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            element.click()
            time.sleep(1)
            return True

        except ElementClickInterceptedException:
            try:
                self.driver.execute_script("arguments[0].click();", slot["element"])
                time.sleep(1)
                return True
            except Exception as e:
                logger.error(f"Failed to click slot: {e}")
                return False
        except Exception as e:
            logger.error(f"Error selecting time slot: {e}")
            return False

    def _select_end_time(self) -> bool:
        """Select the end time for the booking."""
        try:
            duration_hours = self.config.get("time_preferences", {}).get("booking_duration_hours", 2)

            end_time_select = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select[id*='end'], select.s-lc-eq-to"))
            )

            select = Select(end_time_select)
            options = select.options
            slots_needed = duration_hours * 2  # 30-min increments

            if len(options) > slots_needed:
                select.select_by_index(min(slots_needed, len(options) - 1))
            else:
                select.select_by_index(len(options) - 1)

            logger.info(f"Selected end time for ~{duration_hours} hour booking")
            return True

        except Exception as e:
            logger.warning(f"Could not select end time (using default): {e}")
            return True

    def _submit_times(self) -> bool:
        """Click the Submit Times button."""
        try:
            submit_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "submit_times"))
            )
            submit_btn.click()
            time.sleep(2)
            logger.info("Times submitted")
            return True
        except Exception as e:
            logger.error(f"Error submitting times: {e}")
            return False

    def _complete_booking_form(self) -> bool:
        """Complete the booking form and submit."""
        try:
            time.sleep(3)

            # Check for authentication
            if self.auth_handler.is_on_auth_page():
                logger.info("Authentication required - starting auth flow")
                if not self.auth_handler.run_authentication_flow():
                    return False
                time.sleep(2)

            # Click Continue button
            try:
                continue_btn = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#btn-form-submit, .btn-primary"))
                )
                continue_btn.click()
                time.sleep(2)
                logger.info("Clicked Continue button")

                # Check auth again after Continue
                if self.auth_handler.is_on_auth_page():
                    logger.info("Authentication required after Continue")
                    if not self.auth_handler.run_authentication_flow():
                        return False
                    time.sleep(2)

            except Exception:
                logger.debug("No Continue button found")

            # Click Submit my Booking
            try:
                submit_btn = self.wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(text(), 'Submit my Booking')] | //input[@value='Submit my Booking']"
                    ))
                )
                logger.info("Ready to submit booking")
                submit_btn.click()
                time.sleep(3)
                return True

            except Exception as e:
                logger.error(f"Could not find Submit button: {e}")
                take_screenshot(self.driver, "no_submit_button")
                return False

        except Exception as e:
            logger.error(f"Error completing booking form: {e}")
            return False

    def _verify_booking_success(self) -> bool:
        """Verify that the booking was successful."""
        try:
            page_source = self.driver.page_source.lower()

            success_indicators = ["booking confirmed", "successfully booked", "confirmation", "your booking"]
            for indicator in success_indicators:
                if indicator in page_source:
                    logger.info("Booking appears to be successful!")
                    return True

            error_indicators = ["error", "failed", "unable to book", "already booked"]
            for indicator in error_indicators:
                if indicator in page_source:
                    logger.warning(f"Possible booking error: found '{indicator}' in page")
                    return False

            if "booking details" not in page_source:
                logger.info("Booking may have succeeded (no confirmation page detected)")
                return True

            return False

        except Exception as e:
            logger.error(f"Error verifying booking: {e}")
            return False

    def _send_notification(self, success: bool, message: str) -> None:
        """Send notification about booking result."""
        if not self.config.get("notifications", {}).get("enabled", False):
            return

        if self.config.get("notifications", {}).get("desktop_notification", True):
            send_desktop_notification("Library Booker", message)

        email = self.config.get("notifications", {}).get("email", "")
        if email:
            logger.info(f"Would send email to: {email}")

    def book_room(self, dry_run: bool = False) -> bool:
        """
        Main booking method.

        Args:
            dry_run: If True, don't actually submit the booking

        Returns:
            True if booking was successful
        """
        try:
            print_header("Starting library room booking process")

            self._setup_driver()

            if not self._navigate_to_booking_page():
                raise Exception("Failed to load booking page")

            if not self._ensure_on_booking_page():
                raise Exception("Could not complete authentication")

            self._navigate_to_target_date()
            time.sleep(2)

            available_slots = self._find_available_rooms()
            if not available_slots:
                logger.warning("No available rooms matching preferences")
                take_screenshot(self.driver, "no_rooms")
                self._send_notification(False, "No rooms available matching your preferences")
                return False

            slot = available_slots[0]
            logger.info(f"Attempting to book: Room {slot['room']} at {slot['time']}")

            if not self._select_time_slot(slot):
                raise Exception("Failed to select time slot")

            self._select_end_time()

            if not self._submit_times():
                raise Exception("Failed to submit times")

            if dry_run:
                logger.info("DRY RUN - stopping before final submission")
                take_screenshot(self.driver, "dry_run")
                return True

            if not self._complete_booking_form():
                raise Exception("Failed to complete booking form")

            success = self._verify_booking_success()

            if success:
                take_screenshot(self.driver, "booking_success")
                message = f"Successfully booked Room {slot['room']} at {slot['time']}"
                logger.info(message)
                self._send_notification(True, message)
            else:
                take_screenshot(self.driver, "booking_failed")
                self._send_notification(False, "Booking may have failed - please check manually")

            return success

        except Exception as e:
            logger.error(f"Booking failed: {e}")
            if self.driver:
                take_screenshot(self.driver, "error")
            self._send_notification(False, f"Booking failed: {str(e)}")
            return False

        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")

    def check_availability(self) -> List[Dict[str, Any]]:
        """
        Check room availability without booking.

        Returns:
            List of available slots
        """
        try:
            self._setup_driver()
            self._navigate_to_booking_page()

            if not self._ensure_on_booking_page():
                logger.error("Could not complete authentication")
                return []

            target_date = self._get_target_date()
            days_advance = self.config.get("time_preferences", {}).get("days_in_advance", 2)

            print_header(f"CHECKING AVAILABILITY FOR: {target_date.strftime('%A, %B %d, %Y')}")
            print(f"  ({days_advance} days in advance)")

            self._navigate_to_target_date()
            time.sleep(2)

            available = self._find_available_rooms()
            available_sorted = sorted(available, key=lambda s: time_to_minutes(s['time']))

            print_header("AVAILABLE ROOMS (sorted by time)")

            if not available_sorted:
                print("  No rooms available matching your preferences")
            else:
                current_time = None
                for slot in available_sorted:
                    if slot['time'] != current_time:
                        if current_time is not None:
                            print()
                        current_time = slot['time']
                        time_24h = convert_to_24h(slot['time'])
                        print(f"  [{time_24h}] {slot['time']}")
                    print(f"    • Room {slot['room']} ({slot['capacity']}-person)")

            print("=" * 70)
            print(f"Total: {len(available_sorted)} rooms available")
            print("=" * 70 + "\n")

            return available_sorted

        finally:
            if self.driver:
                self.driver.quit()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="University of Guelph Library Room Booker")
    parser.add_argument("--config", "-c", default="config.json", help="Path to config file")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Don't actually book, just test")
    parser.add_argument("--check", action="store_true", help="Only check availability")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    booker = LibraryBooker(config_path=args.config)

    if args.check:
        booker.check_availability()
    else:
        success = booker.book_room(dry_run=args.dry_run)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
