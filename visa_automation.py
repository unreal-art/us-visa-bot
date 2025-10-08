"""
Main visa appointment booking automation system using Selenium
Combines slot checking, CAPTCHA solving, and automated booking
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

from captcha_solver import SmartCaptchaHandler
from slot_checker import SlotChecker, SlotNotifier, VisaSlot
from config import VisaConfig, SECURITY_QUESTIONS

class VisaAutomationBot:
    """
    Comprehensive visa appointment booking automation using Selenium
    """

    def __init__(self, config: VisaConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.captcha_handler = SmartCaptchaHandler(
            use_2captcha=config.use_2captcha,
            api_key=config.captcha_api_key
        )
        self.slot_checker = SlotChecker(config)
        self.notifier = SlotNotifier(config)
        self.security_answers = self._load_security_answers()

        # Selenium WebDriver instance
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('visa_automation.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    def _load_security_answers(self) -> Dict[str, str]:
        """Load security question answers from environment or file"""
        answers = {}
        security_file = Path("security_questions.json")
        
        if security_file.exists():
            try:
                with open(security_file, 'r') as f:
                    answers = json.load(f)
                self.logger.info("Loaded security answers from file")
            except Exception as e:
                self.logger.warning(f"Could not load security answers: {e}")
        
        # Override with environment variables if available
        for question_key in SECURITY_QUESTIONS.values():
            env_value = os.getenv(question_key)
            if env_value:
                answers[question_key] = env_value
                
        return answers

    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        
        # Basic options
        if self.config.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent
        ua = UserAgent()
        chrome_options.add_argument(f"--user-agent={ua.chrome}")
        
        # Window size
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Try to find Chrome binary path
        import shutil
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
            "/usr/bin/google-chrome",  # Linux
            "/usr/bin/chromium-browser",  # Linux Chromium
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",  # Windows
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",  # Windows
        ]
        
        chrome_binary = None
        for path in chrome_paths:
            if shutil.which(path) or Path(path).exists():
                chrome_binary = path
                break
        
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
            self.logger.info(f"Using Chrome binary: {chrome_binary}")
        else:
            self.logger.warning("Chrome binary not found in standard locations")
        
        try:
            # Use webdriver-manager to automatically download ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver = driver
            self.wait = WebDriverWait(driver, 10)  # 10 second timeout
            
            self.logger.info("Chrome WebDriver initialized successfully")
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            self.logger.error("Please install Google Chrome browser:")
            self.logger.error("  macOS: brew install --cask google-chrome")
            self.logger.error("  Ubuntu: wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -")
            self.logger.error("  Windows: Download from https://www.google.com/chrome/")
            raise

    async def login_to_portal(self) -> bool:
        """Login to the Indian visa appointment portal (usvisascheduling.com)"""
        try:
            base_url = self.config.get_base_url()
            login_url = f"{base_url}login"
            
            self.logger.info(f"Navigating to login page: {login_url}")
            self.driver.get(login_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Fill login form - usvisascheduling.com uses different selectors
            email_selectors = [
                "input[name='email']",
                "input[type='email']", 
                "#email",
                "input[placeholder*='email' i]",
                "input[placeholder*='Email' i]"
            ]
            
            password_selectors = [
                "input[name='password']",
                "input[type='password']",
                "#password",
                "input[placeholder*='password' i]",
                "input[placeholder*='Password' i]"
            ]
            
            # Try to find email field
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not email_field:
                self.logger.error("Could not find email input field")
                return False
                
            # Try to find password field
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                self.logger.error("Could not find password input field")
                return False
            
            # Fill credentials
            email_field.clear()
            email_field.send_keys(self.config.username)
            time.sleep(1)
            
            password_field.clear()
            password_field.send_keys(self.config.password)
            time.sleep(1)
            
            # Find and click submit button
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                ".login-button",
                "button:contains('Login')",
                "button:contains('Sign In')",
                "input[value*='Login' i]",
                "input[value*='Sign In' i]"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not submit_button:
                self.logger.error("Could not find submit button")
                return False
            
            submit_button.click()
            self.logger.info("Login form submitted")
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            if "login" not in current_url.lower() and "dashboard" in current_url.lower():
                self.logger.info("Login successful")
                return True
            else:
                self.logger.error("Login failed - still on login page")
                return False
                
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False

    async def navigate_to_appointment_page(self) -> bool:
        """Navigate to the appointment scheduling page"""
        try:
            base_url = self.config.get_base_url()
            appointment_url = f"{base_url}appointment/schedule"
            
            self.logger.info(f"Navigating to appointment page: {appointment_url}")
            self.driver.get(appointment_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Check if we're on the correct page
            current_url = self.driver.current_url
            if "schedule" in current_url or "appointment" in current_url:
                self.logger.info("Successfully navigated to appointment page")
                return True
            else:
                self.logger.error(f"Failed to navigate to appointment page. Current URL: {current_url}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to navigate to appointment page: {e}")
            return False

    async def select_consulate_and_date(self, target_date: Optional[datetime] = None) -> bool:
        """Select consulate and preferred date"""
        try:
            # Select consulate
            consulate_selectors = [
                "select[name='consulate']",
                "select[name='consular_id']",
                "#consulate",
                "#consular_id",
                "select[class*='consulate']",
                "select[class*='consular']"
            ]
            
            consulate_dropdown = None
            for selector in consulate_selectors:
                try:
                    consulate_dropdown = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not consulate_dropdown:
                self.logger.error("Could not find consulate dropdown")
                return False
            
            # Select the configured consulate
            from selenium.webdriver.support.ui import Select
            consulate_select = Select(consulate_dropdown)
            consulate_select.select_by_value(self.config.consular_id)
            self.logger.info(f"Selected consulate: {self.config.consular_id}")
            
            time.sleep(2)
            
            # Select date if target_date is provided
            if target_date:
                date_selectors = [
                    "input[type='date']",
                    "input[name='date']",
                    "#date",
                    ".date-picker",
                    "input[placeholder*='date' i]"
                ]
                
                date_field = None
                for selector in date_selectors:
                    try:
                        date_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except NoSuchElementException:
                        continue
                
                if date_field:
                    date_str = target_date.strftime("%Y-%m-%d")
                    date_field.clear()
                    date_field.send_keys(date_str)
                    self.logger.info(f"Selected target date: {date_str}")
                    time.sleep(2)
            
            # Look for time slots
            time_slot_selectors = [
                ".time-slot",
                ".appointment-time",
                "input[type='radio'][name*='time']",
                ".slot-available",
                "button[class*='time']"
            ]
            
            available_slots = []
            for selector in time_slot_selectors:
                try:
                    slots = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    available_slots.extend(slots)
                except NoSuchElementException:
                    continue
            
            if available_slots:
                self.logger.info(f"Found {len(available_slots)} available time slots")
                # Select the first available slot
                available_slots[0].click()
                time.sleep(2)
                return True
            else:
                self.logger.warning("No available time slots found")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to select consulate and date: {e}")
            return False

    async def solve_captcha_if_present(self) -> bool:
        """Solve CAPTCHA if present on the page"""
        try:
            # Check for different types of CAPTCHAs
            captcha_selectors = [
                "iframe[src*='recaptcha']",
                ".g-recaptcha",
                "#recaptcha",
                "iframe[title*='reCAPTCHA']",
                ".captcha",
                "img[src*='captcha']"
            ]
            
            captcha_element = None
            for selector in captcha_selectors:
                try:
                    captcha_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not captcha_element:
                self.logger.info("No CAPTCHA found on page")
                return True
            
            self.logger.info("CAPTCHA detected, attempting to solve...")
            
            # Use the captcha handler
            success = await self.captcha_handler.solve_captcha(self.driver)
            
            if success:
                self.logger.info("CAPTCHA solved successfully")
                return True
            else:
                self.logger.error("Failed to solve CAPTCHA")
                return False
                
        except Exception as e:
            self.logger.error(f"Error solving CAPTCHA: {e}")
            return False

    async def book_appointment(self) -> bool:
        """Complete the appointment booking process"""
        try:
            # Look for booking confirmation button
            booking_selectors = [
                "button:contains('Book')",
                "button:contains('Confirm')",
                "button:contains('Schedule')",
                "input[type='submit'][value*='Book']",
                "input[type='submit'][value*='Confirm']",
                ".book-button",
                ".confirm-button"
            ]
            
            booking_button = None
            for selector in booking_selectors:
                try:
                    booking_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not booking_button:
                self.logger.error("Could not find booking confirmation button")
                return False
            
            booking_button.click()
            self.logger.info("Booking confirmation clicked")
            
            # Wait for confirmation
            time.sleep(5)
            
            # Check for success message
            success_selectors = [
                ".success-message",
                ".confirmation-message",
                "div:contains('success')",
                "div:contains('confirmed')",
                "div:contains('booked')"
            ]
            
            for selector in success_selectors:
                try:
                    success_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if success_element.is_displayed():
                        self.logger.info("Appointment booked successfully!")
                        return True
                except NoSuchElementException:
                    continue
            
            # Check URL for success indicators
            current_url = self.driver.current_url
            if "success" in current_url.lower() or "confirmation" in current_url.lower():
                self.logger.info("Appointment booking appears successful")
                return True
            
            self.logger.warning("Booking status unclear")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to book appointment: {e}")
            return False

    async def run_automation(self, target_date: Optional[datetime] = None) -> bool:
        """Run the complete automation process"""
        try:
            self.logger.info("Starting visa automation process...")
            
            # Setup WebDriver
            self._setup_driver()
            
            # Login
            if not await self.login_to_portal():
                return False
            
            # Navigate to appointment page
            if not await self.navigate_to_appointment_page():
                return False
            
            # Solve CAPTCHA if present
            if not await self.solve_captcha_if_present():
                return False
            
            # Select consulate and date
            if not await self.select_consulate_and_date(target_date):
                return False
            
            # Book appointment
            if not await self.book_appointment():
                return False
            
            self.logger.info("Automation completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Automation failed: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("WebDriver closed")

    async def monitor_and_book(self, target_date: Optional[datetime] = None) -> bool:
        """Monitor for available slots and automatically book when found"""
        try:
            self.logger.info("Starting slot monitoring and booking...")
            
            while True:
                # Check for available slots
                available_slots = await self.slot_checker.check_available_slots(target_date)
                
                if available_slots:
                    self.logger.info(f"Found {len(available_slots)} available slots!")
                    
                    # Send notification
                    await self.notifier.notify_slots_available(available_slots)
                    
                    # Attempt to book
                    success = await self.run_automation(target_date)
                    if success:
                        self.logger.info("Successfully booked appointment!")
                        return True
                    else:
                        self.logger.warning("Booking failed, continuing to monitor...")
                
                # Wait before next check
                await asyncio.sleep(self.config.retry_timeout)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
            return False
        except Exception as e:
            self.logger.error(f"Monitoring failed: {e}")
            return False

# Import os for environment variables
import os