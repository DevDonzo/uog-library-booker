"""
Authentication handling for UoG Library Booker.
Handles Microsoft/UoG CAS login flows including 2FA.
"""

import logging
import os
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class AuthenticationHandler:
    """Handles all authentication flows for UoG library booking."""

    # CSS Selectors for common elements
    EMAIL_SELECTORS = [
        "input[type='email']",
        "input[name='loginfmt']",
        "input[name='username']",
        "input[name='email']",
        "input[id='username']",
        "input[id='email']",
        "input[id='i0116']",
    ]

    PASSWORD_SELECTORS = [
        "input[type='password']",
        "input[name='passwd']",
        "input[name='password']",
        "input[id='i0118']",
    ]

    SUBMIT_SELECTORS = [
        "input[type='submit']",
        "button[type='submit']",
        "input[value='Next']",
        "#idSIButton9",
        "input[id='idSIButton9']",
    ]

    TWO_FA_SELECTORS = [
        "input[name*='code']",
        "input[name*='otp']",
        "input[name*='token']",
        "input[type='tel']",
        "input[inputmode='numeric']",
        "input[id*='code']",
        "input[id*='otp']",
        "input[autocomplete='one-time-code']",
    ]

    def __init__(self, driver: webdriver.Chrome, wait: WebDriverWait, timeout: int = 180):
        """
        Initialize authentication handler.

        Args:
            driver: Selenium WebDriver instance
            wait: WebDriverWait instance
            timeout: Maximum time to wait for authentication (seconds)
        """
        self.driver = driver
        self.wait = wait
        self.timeout = timeout
        self._email: Optional[str] = None
        self._password: Optional[str] = None
        self._load_credentials()

    def _load_credentials(self) -> None:
        """Load credentials from environment variables."""
        self._email = os.getenv("UOG_EMAIL", "").strip() or None
        self._password = os.getenv("UOG_PASSWORD", "").strip() or None

    def _find_visible_element(self, selectors: list[str]) -> Optional[any]:
        """Find first visible element matching any of the selectors."""
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    return element
            except Exception:
                continue
        return None

    def _get_page_state(self) -> tuple[str, str]:
        """Get current URL and lowercase page source."""
        url = self.driver.current_url or ""
        source = (self.driver.page_source or "").lower()
        return url, source

    def is_on_auth_page(self) -> bool:
        """Check if currently on an authentication page."""
        url, source = self._get_page_state()
        indicators = [
            "login.microsoftonline.com" in url,
            "cas.uoguelph.ca" in url,
            "pick an account" in source,
            "sign in" in source and ("microsoft" in source or "uoguelph" in source),
            "verify your identity" in source,
        ]
        return any(indicators)

    def is_on_booking_page(self) -> bool:
        """Check if currently on the booking page."""
        url, _ = self._get_page_state()
        return "cal.lib.uoguelph.ca" in url

    def handle_pick_account(self) -> bool:
        """
        Handle 'Pick an account' page by selecting the configured email.

        Returns:
            True if handled successfully
        """
        if not self._email:
            logger.warning("No email configured for account picker")
            print("  ⚠ Please click on your account manually\n")
            return False

        logger.info(f"Looking for account: {self._email}")

        # Strategy 1: Find element containing the exact email
        try:
            email_elements = self.driver.find_elements(
                By.XPATH, f"//*[contains(text(), '{self._email}')]"
            )
            for elem in email_elements:
                if elem.is_displayed():
                    try:
                        elem.click()
                        logger.info(f"✓ Clicked on account: {self._email}")
                        print(f"  ✓ Selected account: {self._email}\n")
                        return True
                    except Exception:
                        # Try clicking parent element
                        parent = elem.find_element(By.XPATH, "..")
                        parent.click()
                        logger.info(f"✓ Clicked on account (parent): {self._email}")
                        print(f"  ✓ Selected account: {self._email}\n")
                        return True
        except Exception as e:
            logger.debug(f"Strategy 1 failed: {e}")

        # Strategy 2: Find by data-test-id or tile selectors
        try:
            account_tiles = self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-test-id*='account'], .table-row, .tile-container, [role='listitem']"
            )
            for tile in account_tiles:
                if self._email.lower() in tile.text.lower():
                    tile.click()
                    logger.info(f"✓ Clicked account tile: {self._email}")
                    print(f"  ✓ Selected account: {self._email}\n")
                    return True
        except Exception as e:
            logger.debug(f"Strategy 2 failed: {e}")

        # Strategy 3: Click first account option
        try:
            first_account = self.driver.find_element(
                By.CSS_SELECTOR,
                ".table-row, .tile, [data-test-id='account-tile'], .identity-credential"
            )
            if first_account.is_displayed():
                first_account.click()
                logger.info("✓ Clicked first account option")
                print("  ✓ Selected first account\n")
                return True
        except Exception as e:
            logger.debug(f"Strategy 3 failed: {e}")

        logger.warning("Could not auto-select account")
        print("  ⚠ Please click on your account manually\n")
        return False

    def handle_email_entry(self) -> bool:
        """
        Handle email/username entry page.

        Returns:
            True if handled successfully
        """
        if not self._email:
            logger.warning("No email configured")
            print("  ⚠ Please enter your email manually\n")
            return False

        email_field = self._find_visible_element(self.EMAIL_SELECTORS)
        if not email_field:
            logger.warning("Could not find email field")
            return False

        # Enter email
        email_field.click()
        time.sleep(0.3)
        email_field.clear()
        email_field.send_keys(self._email)
        logger.info(f"✓ Email entered: {self._email}")
        print(f"  ✓ Email entered: {self._email}\n")
        time.sleep(0.5)

        # Click Next button
        submit_btn = self._find_visible_element(self.SUBMIT_SELECTORS)
        if submit_btn:
            submit_btn.click()
            logger.info("✓ Clicked Next button")
            print("  ✓ Proceeding to next step...\n")
            return True

        # Fallback: press Enter
        email_field.send_keys(Keys.RETURN)
        logger.info("✓ Pressed Enter to proceed")
        return True

    def handle_password_entry(self) -> bool:
        """
        Handle password entry page.

        Returns:
            True if handled successfully
        """
        password_field = self._find_visible_element(self.PASSWORD_SELECTORS)
        if not password_field:
            logger.warning("Could not find password field")
            return False

        if self._password:
            password_field.click()
            time.sleep(0.3)
            password_field.clear()
            password_field.send_keys(self._password)
            logger.info("✓ Password entered from .env")
            print("  ✓ Password entered\n")
            time.sleep(0.5)

            # Submit
            password_field.send_keys(Keys.RETURN)
            logger.info("✓ Password submitted")
            return True
        else:
            # Click to trigger autofill
            password_field.click()
            logger.info("✓ Password field clicked - waiting for autofill")
            print("  → Password field ready. Press ENTER when autofill appears!\n")
            return True

    def has_password_field(self) -> bool:
        """Check if the current page has a visible password field."""
        return self._find_visible_element(self.PASSWORD_SELECTORS) is not None

    def handle_verify_identity(self) -> bool:
        """
        Handle 'Verify your identity' page - select Text option for SMS.

        Returns:
            True if handled successfully
        """
        logger.info("Handling verify identity page...")
        time.sleep(1)

        # Strategy 1: Microsoft auth data-value attributes
        try:
            text_options = self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-value='PhoneAppOTP'], [data-value='OneWaySMS'], [data-value='TwoWaySMS']"
            )
            for opt in text_options:
                if opt.is_displayed():
                    opt.click()
                    logger.info("✓ Clicked Text option (data-value)")
                    print("  ✓ Selected 'Text' method\n")
                    return True
        except Exception as e:
            logger.debug(f"Strategy 1 failed: {e}")

        # Strategy 2: Find elements containing "Text" and phone pattern
        try:
            options = self.driver.find_elements(
                By.XPATH, "//div[contains(., 'Text') and contains(., 'XX')]"
            )
            for opt in options:
                try:
                    if opt.is_displayed() and len(opt.text) < 100:
                        clickable = opt
                        for _ in range(3):
                            try:
                                clickable.click()
                                logger.info(f"✓ Clicked Text option: {opt.text[:50]}")
                                print("  ✓ Selected 'Text' method\n")
                                return True
                            except Exception:
                                clickable = clickable.find_element(By.XPATH, "..")
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Strategy 2 failed: {e}")

        # Strategy 3: Find tiles/options with text keywords
        try:
            tiles = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".tile, .row, [role='option'], [role='listitem'], [role='button']"
            )
            for tile in tiles:
                tile_text = tile.text.lower()
                if 'text' in tile_text and ('xx' in tile_text or 'sms' in tile_text or '+' in tile_text):
                    try:
                        tile.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", tile)
                    logger.info(f"✓ Clicked Text tile: {tile.text[:50]}")
                    print("  ✓ Selected 'Text' method\n")
                    return True
        except Exception as e:
            logger.debug(f"Strategy 3 failed: {e}")

        # Strategy 4: Click first verification method
        try:
            first_options = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".table .table-row, .tile-container .tile, [data-bind*='click']"
            )
            if first_options:
                first_opt = first_options[0]
                if first_opt.is_displayed():
                    self.driver.execute_script("arguments[0].click();", first_opt)
                    logger.info(f"✓ Clicked first verification option")
                    print("  ✓ Selected first verification method\n")
                    return True
        except Exception as e:
            logger.debug(f"Strategy 4 failed: {e}")

        logger.warning("Could not auto-click Text - please click manually")
        print("  ⚠ Please click 'Text' manually (waiting 30 seconds)\n")
        time.sleep(30)
        return False

    def handle_2fa_code_entry(self) -> bool:
        """
        Handle 2FA code entry page - click field to trigger autofill.

        Returns:
            True if handled successfully
        """
        logger.info("✓ 2FA code page detected")
        print("  ✓ SMS will be sent to your phone!")
        print("  → Look for the macOS autofill suggestion for the SMS code")
        print("  → Click on the code suggestion when it appears!\n")

        field = self._find_visible_element(self.TWO_FA_SELECTORS)
        if field:
            field.click()
            logger.info("✓ 2FA field clicked - macOS should show SMS code")
            return True

        logger.warning("Could not find 2FA input field")
        return False

    def handle_stay_signed_in(self) -> bool:
        """Handle 'Stay signed in' / 'Keep me signed in' prompt."""
        try:
            yes_btn = self.driver.find_element(
                By.CSS_SELECTOR,
                "#idSIButton9, input[type='submit'][value='Yes'], button[type='submit']"
            )
            yes_btn.click()
            logger.info("✓ Clicked 'Stay signed in' - Yes")
            return True
        except Exception:
            return False

    def run_authentication_flow(self) -> bool:
        """
        Run the complete authentication flow.

        Detects and handles all authentication screens automatically.

        Returns:
            True if authentication completed successfully
        """
        logger.info("Starting authentication flow handler")
        print("\n" + "=" * 70)
        print("  AUTHENTICATION FLOW")
        print("=" * 70)
        print("  The script will handle authentication screens automatically:")
        print("  • Pick an account → selects your email")
        print("  • Sign in → enters email")
        print("  • Password → enters password or waits for autofill")
        print("  • Verify identity → clicks 'Text' for SMS")
        print("  • 2FA code → you click the macOS autofill suggestion")
        print("=" * 70 + "\n")

        start_time = time.time()
        handled = {
            "pick_account": False,
            "email": False,
            "password": False,
            "verify": False,
            "2fa": False,
        }

        while time.time() - start_time < self.timeout:
            try:
                url, source = self._get_page_state()

                # Check if done
                if self.is_on_booking_page():
                    logger.info("✓ Authentication complete - back on booking page!")
                    print("  ✓ Authentication completed successfully!\n")
                    return True

                # Handle: Stay signed in
                if "stay signed in" in source or "keep me signed in" in source:
                    if self.handle_stay_signed_in():
                        time.sleep(2)
                        continue

                # Handle: Pick an account
                if not handled["pick_account"] and "pick an account" in source:
                    logger.info("Detected: Pick an account page")
                    print("  → Pick an account page detected\n")
                    if self.handle_pick_account():
                        handled["pick_account"] = True
                    time.sleep(2)
                    continue

                # Handle: Sign in (email entry)
                if not handled["email"] and ("sign in" in source or "enter your email" in source):
                    if not self.has_password_field():
                        logger.info("Detected: Email entry page")
                        print("  → Sign in page detected\n")
                        if self.handle_email_entry():
                            handled["email"] = True
                        time.sleep(2)
                        continue

                # Handle: Password entry
                if not handled["password"] and self.has_password_field():
                    if "verification code" not in source and "enter code" not in source:
                        logger.info("Detected: Password entry page")
                        print("  → Password page detected\n")
                        if self.handle_password_entry():
                            handled["password"] = True
                        time.sleep(2)
                        continue

                # Handle: Verify your identity
                if not handled["verify"] and "verify your identity" in source:
                    logger.info("Detected: Verify identity page")
                    print("  → Verify identity page detected\n")
                    if self.handle_verify_identity():
                        handled["verify"] = True
                    time.sleep(3)
                    continue

                # Handle: 2FA code entry
                two_fa_indicators = ['verification code', 'enter code', 'enter the code', 'code sent']
                if not handled["2fa"] and any(ind in source for ind in two_fa_indicators):
                    logger.info("Detected: 2FA code entry page")
                    print("  → 2FA code page detected\n")
                    if self.handle_2fa_code_entry():
                        handled["2fa"] = True

                time.sleep(1.5)

            except Exception as e:
                logger.debug(f"Auth flow check error: {e}")
                time.sleep(1.5)

        logger.error("Authentication timeout - flow did not complete in time")
        print("  ✗ Authentication timeout. Please try again.\n")
        return False
