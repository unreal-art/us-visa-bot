# Create the main visa automation script
visa_automation_py = '''"""
Main visa appointment booking automation system
Combines slot checking, CAPTCHA solving, and automated booking
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from fake_useragent import UserAgent

from captcha_solver import SmartCaptchaHandler
from slot_checker import SlotChecker, SlotNotifier, VisaSlot
from config import VisaConfig, SECURITY_QUESTIONS

class VisaAutomationBot:
    """
    Comprehensive visa appointment booking automation
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
        
        # Browser and page instances
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
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
        """Load security question answers from file"""
        try:
            with open('security_questions.json', 'r') as f:
                data = json.load(f)
                return data.get('security_answers', {})
        except Exception as e:
            self.logger.warning(f"Could not load security answers: {e}")
            return {}
    
    async def initialize_browser(self):
        """Initialize Playwright browser with stealth settings"""
        self.logger.info("🚀 Initializing browser...")
        
        playwright = await async_playwright().start()
        
        # Launch browser with stealth settings
        self.browser = await playwright.chromium.launch(
            headless=self.config.headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions-except=',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Faster loading
            ]
        )
        
        # Create browser context with human-like settings
        ua = UserAgent()
        self.context = await self.browser.new_context(
            user_agent=ua.random,
            viewport={'width': 1366, 'height': 768},
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        # Add stealth scripts
        await self.context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        self.page = await self.context.new_page()
        
        # Set additional page properties
        await self.page.route('**/*', lambda route: route.continue_())
        
        self.logger.info("✅ Browser initialized successfully")
    
    async def login_to_portal(self) -> bool:
        """Login to the visa appointment portal"""
        try:
            self.logger.info("🔑 Attempting to login to visa portal...")
            
            base_url = self.config.get_base_url()
            login_url = f"{base_url}users/sign_in"
            
            await self.page.goto(login_url, wait_until='networkidle')
            await self.page.wait_for_timeout(2000)
            
            # Fill login form
            await self.page.fill('input[name="user[email]"], input[type="email"]', self.config.username)
            await self.page.fill('input[name="user[password]"], input[type="password"]', self.config.password)
            
            # Handle CAPTCHA if present
            captcha_solved = await self.captcha_handler.handle_captcha(self.page)
            if not captcha_solved:
                self.logger.warning("⚠️ CAPTCHA detected but not solved")
            
            # Submit login form
            await self.page.click('input[type="submit"], button[type="submit"]')
            await self.page.wait_for_timeout(3000)
            
            # Check if login was successful
            if await self._is_logged_in():
                self.logger.info("✅ Login successful")
                return True
            else:
                self.logger.error("❌ Login failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Login error: {e}")
            return False
    
    async def _is_logged_in(self) -> bool:
        """Check if user is logged in"""
        try:
            # Look for elements that indicate successful login
            indicators = [
                'a[href*="sign_out"]',
                '.user-menu',
                'text="Dashboard"',
                'text="My Profile"'
            ]
            
            for indicator in indicators:
                element = await self.page.query_selector(indicator)
                if element:
                    return True
            
            # Check URL
            current_url = self.page.url
            if 'sign_in' not in current_url and 'login' not in current_url:
                return True
                
        except Exception as e:
            self.logger.error(f"Error checking login status: {e}")
            
        return False
    
    async def navigate_to_appointment_page(self) -> bool:
        """Navigate to the appointment scheduling page"""
        try:
            self.logger.info("📅 Navigating to appointment page...")
            
            # Navigate to schedule appointment page
            base_url = self.config.get_base_url()
            appointment_url = f"{base_url}schedule/{self.config.application_id}/appointment"
            
            await self.page.goto(appointment_url, wait_until='networkidle')
            await self.page.wait_for_timeout(2000)
            
            # Check if we're on the right page
            if 'appointment' in self.page.url.lower():
                self.logger.info("✅ Successfully navigated to appointment page")
                return True
            else:
                self.logger.error("❌ Failed to reach appointment page")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Navigation error: {e}")
            return False
    
    async def select_consulate_and_date(self, target_slot: VisaSlot) -> bool:
        """Select consulate and date for appointment"""
        try:
            self.logger.info(f"🏛️ Selecting consulate and date: {target_slot}")
            
            # Select consulate
            consulate_dropdown = await self.page.query_selector('select[name*="consulate"], #appointments_consulate_appointment_facility_id')
            if consulate_dropdown:
                await consulate_dropdown.select_option(value=target_slot.consulate_id)
                await self.page.wait_for_timeout(2000)
            
            # Select date
            date_element = await self.page.query_selector(f'a[data-date="{target_slot.date.strftime("%Y-%m-%d")}"]')
            if date_element:
                await date_element.click()
                await self.page.wait_for_timeout(1000)
            else:
                # Try alternative date selection method
                await self._select_date_alternative(target_slot.date)
            
            # Select time slot (usually the first available)
            time_slots = await self.page.query_selector_all('.time-slot, a[data-time]')
            if time_slots:
                await time_slots[0].click()
                await self.page.wait_for_timeout(1000)
            
            self.logger.info("✅ Date and time selected")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Date selection error: {e}")
            return False
    
    async def _select_date_alternative(self, target_date: datetime):
        """Alternative method for date selection"""
        try:
            # Try clicking on calendar widget
            calendar_input = await self.page.query_selector('input[type="date"], .date-input')
            if calendar_input:
                await calendar_input.fill(target_date.strftime('%Y-%m-%d'))
            
            # Try clicking on specific date link
            date_links = await self.page.query_selector_all(f'text="{target_date.day}"')
            for link in date_links:
                await link.click()
                break
                
        except Exception as e:
            self.logger.warning(f"Alternative date selection failed: {e}")
    
    async def handle_security_questions(self) -> bool:
        """Handle security questions during booking"""
        try:
            self.logger.info("🔒 Checking for security questions...")
            
            # Wait for potential security question page
            await self.page.wait_for_timeout(2000)
            
            # Look for security question elements
            question_element = await self.page.query_selector('.question, label[for*="security"], text*="security question"')
            
            if question_element:
                question_text = await question_element.inner_text()
                self.logger.info(f"🔍 Found security question: {question_text}")
                
                # Find matching answer
                answer = self._find_security_answer(question_text)
                
                if answer:
                    # Fill in the answer
                    answer_input = await self.page.query_selector('input[type="text"], input[type="password"]')
                    if answer_input:
                        await answer_input.fill(answer)
                        self.logger.info("✅ Security question answered")
                        return True
                else:
                    self.logger.error(f"❌ No answer found for question: {question_text}")
                    
        except Exception as e:
            self.logger.error(f"❌ Security question handling error: {e}")
            
        return False
    
    def _find_security_answer(self, question_text: str) -> Optional[str]:
        """Find answer for a security question"""
        question_text = question_text.lower().strip()
        
        for q, answer in self.security_answers.items():
            if q.lower() in question_text or any(word in question_text for word in q.lower().split()):
                return answer
        
        # Try partial matching
        for q, answer in self.security_answers.items():
            question_words = set(q.lower().split())
            text_words = set(question_text.split())
            
            if len(question_words.intersection(text_words)) >= 2:
                return answer
        
        return None
    
    async def confirm_appointment(self) -> bool:
        """Confirm the appointment booking"""
        try:
            self.logger.info("✅ Confirming appointment...")
            
            # Handle any final CAPTCHAs
            await self.captcha_handler.handle_captcha(self.page)
            
            # Look for confirmation button
            confirm_buttons = [
                'button[type="submit"]',
                'input[type="submit"]',
                'text="Confirm"',
                'text="Book Appointment"',
                'text="Schedule Appointment"'
            ]
            
            for button_selector in confirm_buttons:
                button = await self.page.query_selector(button_selector)
                if button:
                    await button.click()
                    await self.page.wait_for_timeout(3000)
                    break
            
            # Check for success indicators
            success_indicators = [
                'text="Appointment confirmed"',
                'text="Successfully scheduled"',
                '.success-message',
                '.confirmation'
            ]
            
            for indicator in success_indicators:
                element = await self.page.query_selector(indicator)
                if element:
                    self.logger.info("🎉 Appointment booking successful!")
                    return True
            
            self.logger.warning("⚠️ Booking confirmation unclear")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Appointment confirmation error: {e}")
            return False
    
    async def attempt_booking(self, target_slot: VisaSlot) -> bool:
        """Attempt to book a specific slot"""
        try:
            self.logger.info(f"🎯 Attempting to book slot: {target_slot}")
            
            # Navigate to appointment page
            if not await self.navigate_to_appointment_page():
                return False
            
            # Select consulate and date
            if not await self.select_consulate_and_date(target_slot):
                return False
            
            # Handle security questions
            await self.handle_security_questions()
            
            # Handle any CAPTCHAs
            await self.captcha_handler.handle_captcha(self.page)
            
            # Confirm appointment
            return await self.confirm_appointment()
            
        except Exception as e:
            self.logger.error(f"❌ Booking attempt failed: {e}")
            return False
    
    async def run_automation(self):
        """Main automation loop"""
        try:
            self.logger.info("🚀 Starting visa slot booking automation")
            
            # Initialize browser
            await self.initialize_browser()
            
            # Login to portal
            if not await self.login_to_portal():
                return
            
            # Set up slot monitoring callback
            async def slot_callback(available_slots: List[VisaSlot]):
                """Callback when slots become available"""
                # Get the earliest available slot
                earliest_slot = self.slot_checker.get_earliest_available_slot(available_slots)
                
                if earliest_slot:
                    # Notify about available slot
                    await self.notifier.notify_slot_available([earliest_slot])
                    
                    # Attempt to book the slot
                    booking_success = await self.attempt_booking(earliest_slot)
                    
                    if booking_success:
                        self.logger.info("🎉 BOOKING SUCCESSFUL! 🎉")
                        # Send success notification
                        await self.notifier.notify_slot_available([earliest_slot])
                        return True  # Stop monitoring
                    else:
                        self.logger.warning("⚠️ Booking attempt failed, continuing monitoring...")
                
                return False  # Continue monitoring
            
            # Start continuous slot monitoring
            await self.slot_checker.monitor_slots_continuously(callback=slot_callback)
            
        except KeyboardInterrupt:
            self.logger.info("🛑 Automation stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Automation error: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            self.logger.info("🧹 Browser cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
'''

with open('visa_automation.py', 'w') as f:
    f.write(visa_automation_py)

print("✅ Created visa_automation.py")