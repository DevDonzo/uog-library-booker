#!/usr/bin/env python3
"""
University of Guelph Library Room Booker
Automatically books study rooms based on your preferences.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('booking.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LibraryBooker:
    """Automates booking of UoG library study rooms."""

    ROOM_CAPACITIES = {
        # 2-Person Study Rooms
        "603": 2, "604": 2,
        # 1-Person Study Rooms
        "315": 1, "316": 1, "322": 1, "323": 1, "324": 1, "325": 1,
        "326": 1, "327": 1, "328": 1, "329": 1, "330": 1, "331": 1, "332": 1
    }

    def __init__(self, config_path: str = "config.json"):
        """Initialize the booker with configuration."""
        self.config = self._load_config(config_path)
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
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

        # Use existing Chrome profile for saved login session
        chrome_profile = self.config.get("chrome_profile_path", "")
        use_profile = self.config.get("advanced", {}).get("use_chrome_profile", True)

        if use_profile:
            if chrome_profile:
                # User specified a custom profile path
                options.add_argument(f"user-data-dir={chrome_profile}")
                options.add_argument("--profile-directory=SeleniumProfile")
                logger.info(f"Using custom Chrome profile: {chrome_profile}")
            else:
                # Create a dedicated profile for automation to avoid conflicts
                project_dir = Path(__file__).parent
                automation_profile = project_dir / ".chrome_automation_profile"
                automation_profile.mkdir(exist_ok=True)
                options.add_argument(f"user-data-dir={automation_profile}")
                logger.info(f"Using automation profile: {automation_profile}")
                logger.info("Note: You'll need to log in the first time this profile is used")

        # Headless mode if configured
        if self.config.get("advanced", {}).get("headless_mode", False):
            options.add_argument("--headless=new")

        # Additional options for stability
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        # Prevent Chrome from showing "Chrome is being controlled by automated software"
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            self.driver = webdriver.Chrome(options=options)
            timeout = self.config.get("advanced", {}).get("wait_timeout", 10)
            self.wait = WebDriverWait(self.driver, timeout)
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise

    def _get_default_chrome_profile_paths(self) -> List[str]:
        """Get default Chrome profile paths based on OS."""
        home = Path.home()

        if sys.platform == "darwin":  # macOS
            return [
                str(home / "Library/Application Support/Google/Chrome"),
                str(home / "Library/Application Support/Google/Chrome/Default")
            ]
        elif sys.platform == "win32":  # Windows
            return [
                str(home / "AppData/Local/Google/Chrome/User Data"),
            ]
        else:  # Linux
            return [
                str(home / ".config/google-chrome"),
                str(home / ".config/chromium")
            ]

    def _get_target_date(self) -> datetime:
        """Calculate the target booking date."""
        days_advance = self.config.get("time_preferences", {}).get("days_in_advance", 2)
        target = datetime.now() + timedelta(days=days_advance)
        return target

    def _navigate_to_booking_page(self) -> bool:
        """Navigate to the room booking page."""
        try:
            url = self.config.get("booking_url")
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)

            # Wait for the page to load
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table, .s-lc-eq-avail"))
            )
            logger.info("Booking page loaded successfully")
            return True
        except TimeoutException:
            logger.error("Timeout waiting for booking page to load")
            return False

    def _check_authentication(self) -> bool:
        """Check if user is authenticated."""
        try:
            # Look for logout link which indicates logged in state
            logout_link = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Logout')]")
            if logout_link:
                logger.info("User is authenticated")
                return True

            # Check if we're on a CAS login page
            if "cas.uoguelph.ca" in self.driver.current_url:
                logger.warning("User needs to authenticate - on CAS login page")
                return False

            return True
        except Exception as e:
            logger.error(f"Error checking authentication: {e}")
            return False

    def _handle_cas_login(self, timeout: int = None) -> bool:
        """
        Handle UoG CAS login with autofill assistance.
        Helps automate the login process when password and 2FA are autofilled.
        """
        if timeout is None:
            timeout = self.config.get("advanced", {}).get("login_timeout", 180)

        logger.info("CAS login page detected - attempting to assist with login")
        print("\n" + "="*70)
        print("  CAS LOGIN - AUTOFILL ASSISTANCE")
        print("="*70)
        print("  The script will help automate the login steps:")
        print("  1. Click on password field to trigger autofill")
        print("  2. Wait for you to press Enter on password")
        print("  3. Automatically select 'Text' for SMS verification")
        print("  4. Detect 2FA page and wait for autofill")
        print("  5. You just need to click the macOS 2FA suggestion!")
        print("="*70 + "\n")

        start_time = time.time()

        try:
            # Step 1: Try to find and click the password field to trigger autofill
            try:
                logger.info("Looking for password field...")
                time.sleep(2)  # Wait for page to fully load

                password_field = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password'], input[name='password']"))
                )

                # Click the password field to trigger Chrome autofill
                password_field.click()
                logger.info("✓ Password field clicked - Chrome should show autofill")
                print("  → Password field is ready. Press ENTER when autofill appears!\n")

            except Exception as e:
                logger.warning(f"Could not find password field: {e}")
                print("  → Please log in manually\n")

            # Step 2: Wait for login to complete (either user presses Enter or submits)
            logger.info("Waiting for password submission...")

            # Track which stage we're at
            method_selected = False
            two_fa_detected = False

            # Check if we're still on CAS or if we moved to 2FA
            check_interval = 2
            while time.time() - start_time < timeout:
                current_url = self.driver.current_url

                # Check if we're back on the booking page (login complete)
                if "cal.lib.uoguelph.ca" in current_url:
                    logger.info("✓ Login successful!")
                    print("  ✓ Login completed successfully!\n")
                    return True

                # Check if we're on CAS pages
                if "cas.uoguelph.ca" in current_url or "aka.ms/mfasetup" in current_url:
                    page_source = self.driver.page_source.lower()

                    # Step 2a: Check for "Verify your identity" / method selection page
                    if "verify your identity" in page_source and not method_selected:
                        logger.info("✓ Password accepted! Method selection page detected")
                        print("  ✓ Password accepted!")
                        print("  → Selecting 'Text' for SMS verification...\n")

                        try:
                            # Look for the Text option - try multiple selectors
                            time.sleep(1)

                            # Try clicking by text content
                            text_button = None
                            try:
                                # Look for element containing "Text" and phone number
                                text_button = self.driver.find_element(
                                    By.XPATH,
                                    "//div[contains(text(), 'Text') and contains(text(), 'XXX')]"
                                )
                            except:
                                pass

                            if not text_button:
                                try:
                                    # Alternative: look for the text message icon area
                                    text_button = self.driver.find_element(
                                        By.XPATH,
                                        "//*[contains(text(), 'Text +')]"
                                    )
                                except:
                                    pass

                            if not text_button:
                                try:
                                    # Try finding by the icon area (first clickable option)
                                    clickable_divs = self.driver.find_elements(By.CSS_SELECTOR, "div[role='button'], div[onclick], a")
                                    for div in clickable_divs:
                                        if 'text' in div.text.lower():
                                            text_button = div
                                            break
                                except:
                                    pass

                            if text_button:
                                text_button.click()
                                logger.info("✓ Clicked 'Text' option")
                                print("  ✓ Selected 'Text' method\n")
                                method_selected = True
                                time.sleep(2)  # Wait for next page
                            else:
                                logger.warning("Could not find 'Text' button - may need manual selection")
                                print("  ⚠ Please click 'Text' manually\n")
                                method_selected = True  # Continue anyway

                        except Exception as e:
                            logger.warning(f"Error clicking Text option: {e}")
                            print("  ⚠ Please click 'Text' manually\n")
                            method_selected = True

                    # Step 2b: Look for 2FA code input page
                    if any(indicator in page_source for indicator in ['duo', 'two-factor', '2fa', 'verification code', 'authentication code', 'enter code']) and not two_fa_detected:
                        two_fa_detected = True
                        logger.info("✓ 2FA code page detected")
                        print("  ✓ SMS will be sent to your phone!")
                        print("  → Look for the macOS autofill suggestion for the SMS code")
                        print("  → Click on the code suggestion when it appears!\n")

                        # Try to find and click the 2FA input field
                        try:
                            # Wait a moment for the 2FA page to fully load
                            time.sleep(2)

                            # Common 2FA field selectors
                            two_fa_field = self.driver.find_element(
                                By.CSS_SELECTOR,
                                "input[name*='code'], input[name*='otp'], input[name*='token'], input[type='tel'], input[inputmode='numeric'], input[id*='code']"
                            )
                            two_fa_field.click()
                            logger.info("✓ 2FA field clicked - macOS should show SMS code")

                            # Give macOS time to detect SMS and show autofill (can take up to 10 seconds)
                            logger.info("Waiting for macOS SMS autofill to appear (up to 15 seconds)...")
                            time.sleep(3)  # Initial wait for SMS to arrive

                        except:
                            logger.debug("Could not auto-click 2FA field")

                time.sleep(check_interval)

            logger.error("Login timeout - user did not complete login in time")
            print("  ✗ Login timeout. Please try again.\n")
            return False

        except Exception as e:
            logger.error(f"Error during login assistance: {e}")
            return False

    def _wait_for_manual_login(self, timeout: int = None) -> bool:
        """Wait for user to manually log in with autofill assistance."""
        if timeout is None:
            timeout = self.config.get("advanced", {}).get("login_timeout", 180)

        if "cas.uoguelph.ca" in self.driver.current_url:
            return self._handle_cas_login(timeout)

        # Fallback for other login pages
        logger.info(f"Please log in manually. Waiting up to {timeout} seconds...")
        print("\n" + "="*50)
        print("MANUAL LOGIN REQUIRED")
        print("Please log in to the University of Guelph system")
        print("="*50 + "\n")

        start_time = time.time()
        while time.time() - start_time < timeout:
            if "cas.uoguelph.ca" not in self.driver.current_url:
                # Check if we're back on the booking page
                if "cal.lib.uoguelph.ca" in self.driver.current_url:
                    logger.info("Login successful!")
                    return True
            time.sleep(2)

        logger.error("Login timeout - user did not complete login in time")
        return False

    def _find_available_rooms(self) -> List[Dict[str, Any]]:
        """Find all available room slots matching preferences."""
        available_slots = []
        capacity_pref = self.config.get("room_preferences", {}).get("capacity", 1)
        preferred_rooms = self.config.get("room_preferences", {}).get("preferred_rooms", [])
        excluded_rooms = self.config.get("room_preferences", {}).get("excluded_rooms", [])
        preferred_times = self.config.get("time_preferences", {}).get("preferred_start_times", [])

        try:
            # Find all available time slot links
            available_links = self.driver.find_elements(
                By.XPATH, "//a[contains(@title, 'Available') and not(contains(@title, 'Unavailable'))]"
            )

            for link in available_links:
                title = link.get_attribute("title")
                if not title:
                    continue

                # Parse the title: "9:30pm Monday, February 2, 2026 - Room 315 - Available"
                try:
                    parts = title.split(" - ")
                    time_date = parts[0]
                    room_info = parts[1] if len(parts) > 1 else ""

                    # Extract room number
                    room_num = room_info.replace("Room ", "").strip()

                    # Check capacity preference
                    room_capacity = self.ROOM_CAPACITIES.get(room_num, 1)
                    if capacity_pref and room_capacity != capacity_pref:
                        continue

                    # Check excluded rooms
                    if room_num in excluded_rooms:
                        continue

                    # Check preferred rooms (if specified)
                    if preferred_rooms and room_num not in preferred_rooms:
                        continue

                    # Extract time
                    time_str = time_date.split()[0]  # e.g., "9:30pm"

                    # Check preferred times
                    if preferred_times:
                        time_24h = self._convert_to_24h(time_str)
                        if time_24h not in preferred_times:
                            continue

                    slot = {
                        "element": link,
                        "title": title,
                        "room": room_num,
                        "time": time_str,
                        "capacity": room_capacity
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

    def _convert_to_24h(self, time_str: str) -> str:
        """Convert 12-hour time string to 24-hour format."""
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
        except:
            return time_str

    def _navigate_to_target_date(self) -> bool:
        """Navigate to the target booking date."""
        target_date = self._get_target_date()
        logger.info(f"Target booking date: {target_date.strftime('%A, %B %d, %Y')}")

        try:
            # Click "Go To Date" button
            go_to_date_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Go To Date')]"))
            )
            go_to_date_btn.click()
            time.sleep(1)

            # A datepicker should appear - navigate to the target date
            # This may vary based on the LibCal implementation
            # For now, try using the Next button to advance days
            days_to_advance = self.config.get("time_preferences", {}).get("days_in_advance", 2)

            for _ in range(days_to_advance):
                try:
                    next_btn = self.driver.find_element(By.XPATH, "//button[contains(@title, 'Next')]")
                    next_btn.click()
                    time.sleep(0.5)
                except:
                    break

            return True
        except Exception as e:
            logger.warning(f"Could not navigate to target date: {e}")
            # Continue anyway - the default view might already show the target date
            return True

    def _select_time_slot(self, slot: Dict[str, Any]) -> bool:
        """Select a time slot for booking."""
        try:
            element = slot["element"]
            logger.info(f"Selecting slot: {slot['title']}")

            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)

            # Click the slot
            element.click()
            time.sleep(1)

            return True
        except ElementClickInterceptedException:
            # Try JavaScript click
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

            # Find the end time dropdown
            end_time_select = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select[id*='end'], select.s-lc-eq-to"))
            )

            select = Select(end_time_select)
            options = select.options

            # Try to select an option that gives us the desired duration
            # Each option is 30 minutes, so 2 hours = 4 options from current
            slots_needed = duration_hours * 2

            if len(options) > slots_needed:
                select.select_by_index(min(slots_needed, len(options) - 1))
            else:
                # Select the maximum available
                select.select_by_index(len(options) - 1)

            logger.info(f"Selected end time for ~{duration_hours} hour booking")
            return True
        except Exception as e:
            logger.warning(f"Could not select end time (using default): {e}")
            return True  # Continue with default

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
            # Wait for the booking form to load
            time.sleep(2)

            # Check if we need to log in
            if "cas.uoguelph.ca" in self.driver.current_url:
                if not self._wait_for_manual_login():
                    return False
                time.sleep(2)

            # Look for Continue button (Terms & Conditions page)
            try:
                continue_btn = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#btn-form-submit, .btn-primary"))
                )
                continue_btn.click()
                time.sleep(2)
                logger.info("Clicked Continue button")
            except:
                pass  # May already be on final form

            # Look for Submit my Booking button
            try:
                submit_btn = self.wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(text(), 'Submit my Booking')] | //input[@value='Submit my Booking']"
                    ))
                )

                # Final confirmation before submitting
                logger.info("Ready to submit booking - clicking Submit my Booking")
                submit_btn.click()
                time.sleep(3)

                return True
            except Exception as e:
                logger.error(f"Could not find Submit button: {e}")
                return False

        except Exception as e:
            logger.error(f"Error completing booking form: {e}")
            return False

    def _verify_booking_success(self) -> bool:
        """Verify that the booking was successful."""
        try:
            # Look for success indicators
            page_source = self.driver.page_source.lower()

            success_indicators = [
                "booking confirmed",
                "successfully booked",
                "confirmation",
                "your booking"
            ]

            for indicator in success_indicators:
                if indicator in page_source:
                    logger.info("Booking appears to be successful!")
                    return True

            # Check for error messages
            error_indicators = [
                "error",
                "failed",
                "unable to book",
                "already booked"
            ]

            for indicator in error_indicators:
                if indicator in page_source:
                    logger.warning(f"Possible booking error: found '{indicator}' in page")
                    return False

            # If no clear indicator, assume success if we're past the form
            if "booking details" not in page_source:
                logger.info("Booking may have succeeded (no confirmation page detected)")
                return True

            return False
        except Exception as e:
            logger.error(f"Error verifying booking: {e}")
            return False

    def _take_screenshot(self, name: str = "screenshot") -> None:
        """Take a screenshot for debugging."""
        if self.config.get("advanced", {}).get("screenshot_on_error", True):
            try:
                filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(filename)
                logger.info(f"Screenshot saved: {filename}")
            except Exception as e:
                logger.error(f"Could not save screenshot: {e}")

    def _send_notification(self, success: bool, message: str) -> None:
        """Send notification about booking result."""
        if not self.config.get("notifications", {}).get("enabled", False):
            return

        # Desktop notification
        if self.config.get("notifications", {}).get("desktop_notification", True):
            try:
                import platform
                if platform.system() == "Darwin":  # macOS
                    os.system(f"""osascript -e 'display notification "{message}" with title "Library Booker"'""")
                elif platform.system() == "Linux":
                    os.system(f'notify-send "Library Booker" "{message}"')
                elif platform.system() == "Windows":
                    # Windows toast notification would require additional library
                    pass
            except:
                pass

        # Email notification (placeholder - would need SMTP config)
        email = self.config.get("notifications", {}).get("email", "")
        if email:
            logger.info(f"Would send email to: {email}")
            # TODO: Implement email sending

    def book_room(self, dry_run: bool = False) -> bool:
        """
        Main booking method.

        Args:
            dry_run: If True, don't actually submit the booking

        Returns:
            True if booking was successful, False otherwise
        """
        try:
            logger.info("="*50)
            logger.info("Starting library room booking process")
            logger.info("="*50)

            # Initialize browser
            self._setup_driver()

            # Navigate to booking page
            if not self._navigate_to_booking_page():
                raise Exception("Failed to load booking page")

            # Navigate to target date
            self._navigate_to_target_date()
            time.sleep(2)

            # Find available rooms
            available_slots = self._find_available_rooms()

            if not available_slots:
                logger.warning("No available rooms matching preferences")
                self._take_screenshot("no_rooms")
                self._send_notification(False, "No rooms available matching your preferences")
                return False

            # Select the first available slot
            slot = available_slots[0]
            logger.info(f"Attempting to book: Room {slot['room']} at {slot['time']}")

            if not self._select_time_slot(slot):
                raise Exception("Failed to select time slot")

            # Select end time
            self._select_end_time()

            # Submit times
            if not self._submit_times():
                raise Exception("Failed to submit times")

            if dry_run:
                logger.info("DRY RUN - stopping before final submission")
                self._take_screenshot("dry_run")
                return True

            # Complete booking form
            if not self._complete_booking_form():
                raise Exception("Failed to complete booking form")

            # Verify success
            success = self._verify_booking_success()

            if success:
                self._take_screenshot("booking_success")
                message = f"Successfully booked Room {slot['room']} at {slot['time']}"
                logger.info(message)
                self._send_notification(True, message)
            else:
                self._take_screenshot("booking_failed")
                self._send_notification(False, "Booking may have failed - please check manually")

            return success

        except Exception as e:
            logger.error(f"Booking failed: {e}")
            self._take_screenshot("error")
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

            # Show target date
            target_date = self._get_target_date()
            print("\n" + "="*70)
            print(f"  CHECKING AVAILABILITY FOR: {target_date.strftime('%A, %B %d, %Y')}")
            print(f"  ({self.config.get('time_preferences', {}).get('days_in_advance', 2)} days in advance)")
            print("="*70)

            self._navigate_to_target_date()
            time.sleep(2)

            available = self._find_available_rooms()

            # Sort by time (convert to 24h for sorting)
            def time_sort_key(slot):
                time_24h = self._convert_to_24h(slot['time'])
                try:
                    hour, minute = time_24h.split(':')
                    return int(hour) * 60 + int(minute)
                except:
                    return 9999  # Put unparseable times at end

            available_sorted = sorted(available, key=time_sort_key)

            print("\n" + "="*70)
            print("AVAILABLE ROOMS (sorted by time)")
            print("="*70)

            if not available_sorted:
                print("  No rooms available matching your preferences")
            else:
                current_time = None
                for slot in available_sorted:
                    # Group by time for better readability
                    if slot['time'] != current_time:
                        if current_time is not None:
                            print()  # Blank line between time groups
                        current_time = slot['time']
                        time_24h = self._convert_to_24h(slot['time'])
                        print(f"  [{time_24h}] {slot['time']}")
                    print(f"    • Room {slot['room']} ({slot['capacity']}-person)")

            print("="*70)
            print(f"Total: {len(available_sorted)} rooms available")
            print("="*70 + "\n")

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
