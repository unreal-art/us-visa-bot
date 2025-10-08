"""
Advanced CAPTCHA solver with audio support for visa booking automation using Selenium
Supports both free speech recognition and paid services like 2captcha
"""
import os
import tempfile
import asyncio
import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path

# Optional speech recognition - may not work on Python 3.13+
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Optional audio processing - may not work on Python 3.13+
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None

class AudioCaptchaSolver:
    """Intelligent audio CAPTCHA solver with multiple fallback methods"""

    def __init__(self, use_2captcha: bool = False, api_key: str = ""):
        self.use_2captcha = use_2captcha
        self.api_key = api_key
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None
        self.logger = logging.getLogger(__name__)

    async def solve_recaptcha_v2(self, driver) -> Optional[str]:
        """
        Solve reCAPTCHA v2 using audio challenge
        Returns the g-recaptcha-response token
        """
        try:
            # Find reCAPTCHA iframe
            recaptcha_iframe = None
            iframe_selectors = [
                "iframe[src*='recaptcha']",
                "iframe[title*='reCAPTCHA']",
                ".g-recaptcha iframe"
            ]
            
            for selector in iframe_selectors:
                try:
                    recaptcha_iframe = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not recaptcha_iframe:
                self.logger.warning("reCAPTCHA iframe not found")
                return None
            
            # Switch to reCAPTCHA iframe
            driver.switch_to.frame(recaptcha_iframe)
            
            # Click on "I'm not a robot" checkbox
            checkbox_selectors = [
                ".recaptcha-checkbox-border",
                ".recaptcha-checkbox",
                "#recaptcha-anchor"
            ]
            
            checkbox = None
            for selector in checkbox_selectors:
                try:
                    checkbox = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not checkbox:
                self.logger.error("Could not find reCAPTCHA checkbox")
                driver.switch_to.default_content()
                return None
            
            checkbox.click()
            self.logger.info("Clicked reCAPTCHA checkbox")
            time.sleep(2)
            
            # Check if audio challenge appears
            audio_challenge_selectors = [
                "#recaptcha-audio-button",
                ".rc-audiochallenge-tdownload-link",
                "button[title*='audio']"
            ]
            
            audio_button = None
            for selector in audio_challenge_selectors:
                try:
                    audio_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if audio_button:
                self.logger.info("Audio challenge detected, attempting to solve...")
                audio_button.click()
                time.sleep(2)
                
                # Download and solve audio
                audio_text = await self._solve_audio_challenge(driver)
                if audio_text:
                    # Enter the solution
                    input_selectors = [
                        "#audio-response",
                        ".rc-audiochallenge-response-field",
                        "input[type='text']"
                    ]
                    
                    input_field = None
                    for selector in input_selectors:
                        try:
                            input_field = driver.find_element(By.CSS_SELECTOR, selector)
                            break
                        except NoSuchElementException:
                            continue
                    
                    if input_field:
                        input_field.clear()
                        input_field.send_keys(audio_text)
                        time.sleep(1)
                        
                        # Submit the solution
                        verify_button = driver.find_element(By.CSS_SELECTOR, "#recaptcha-verify-button")
                        verify_button.click()
                        time.sleep(3)
            
            # Switch back to main content
            driver.switch_to.default_content()
            
            # Check if reCAPTCHA was solved
            response_token = driver.execute_script(
                "return document.querySelector('textarea[name=\"g-recaptcha-response\"]')?.value"
            )
            
            if response_token:
                self.logger.info("reCAPTCHA solved successfully")
                return response_token
            else:
                self.logger.warning("reCAPTCHA solution not found")
                return None
                
        except Exception as e:
            self.logger.error(f"Error solving reCAPTCHA: {e}")
            driver.switch_to.default_content()
            return None

    async def _solve_audio_challenge(self, driver) -> Optional[str]:
        """Solve audio CAPTCHA challenge"""
        try:
            # Find audio download link
            audio_link_selectors = [
                ".rc-audiochallenge-tdownload-link",
                "a[href*='audio']",
                "button[title*='download']"
            ]
            
            audio_link = None
            for selector in audio_link_selectors:
                try:
                    audio_link = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not audio_link:
                self.logger.error("Could not find audio download link")
                return None
            
            # Get audio URL
            audio_url = audio_link.get_attribute("href")
            if not audio_url:
                self.logger.error("Could not get audio URL")
                return None
            
            # Download audio file
            response = requests.get(audio_url)
            if response.status_code != 200:
                self.logger.error(f"Failed to download audio: {response.status_code}")
                return None
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_file.write(response.content)
                temp_audio_path = temp_file.name
            
            try:
                # Convert audio if needed
                if PYDUB_AVAILABLE:
                    audio = AudioSegment.from_mp3(temp_audio_path)
                    # Convert to WAV for better recognition
                    wav_path = temp_audio_path.replace(".mp3", ".wav")
                    audio.export(wav_path, format="wav")
                    audio_path = wav_path
                else:
                    audio_path = temp_audio_path
                
                # Use speech recognition
                if SPEECH_RECOGNITION_AVAILABLE and self.recognizer:
                    with sr.AudioFile(audio_path) as source:
                        audio_data = self.recognizer.record(source)
                    
                    # Try multiple recognition services
                    recognition_services = [
                        ("Google", self.recognizer.recognize_google),
                        ("Wit.ai", lambda audio: self.recognizer.recognize_wit(audio, key=os.getenv("WIT_AI_KEY", ""))),
                    ]
                    
                    for service_name, recognize_func in recognition_services:
                        try:
                            text = recognize_func(audio_data)
                            if text:
                                self.logger.info(f"Audio recognized using {service_name}: {text}")
                                return text.strip()
                        except Exception as e:
                            self.logger.warning(f"{service_name} recognition failed: {e}")
                            continue
                
                # Fallback to 2captcha if available
                if self.use_2captcha and self.api_key:
                    return await self._solve_with_2captcha(audio_url)
                
                self.logger.error("All audio recognition methods failed")
                return None
                
            finally:
                # Clean up temporary files
                try:
                    os.unlink(temp_audio_path)
                    if PYDUB_AVAILABLE and 'wav_path' in locals():
                        os.unlink(wav_path)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Error solving audio challenge: {e}")
            return None

    async def _solve_with_2captcha(self, audio_url: str) -> Optional[str]:
        """Solve CAPTCHA using 2captcha service"""
        try:
            if not self.api_key:
                self.logger.warning("2captcha API key not provided")
                return None
            
            # Submit CAPTCHA to 2captcha
            submit_data = {
                'key': self.api_key,
                'method': 'userrecaptcha',
                'googlekey': '6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-',  # Common reCAPTCHA site key
                'pageurl': audio_url,
                'json': 1
            }
            
            response = requests.post('http://2captcha.com/in.php', data=submit_data)
            result = response.json()
            
            if result.get('status') != 1:
                self.logger.error(f"2captcha submission failed: {result}")
                return None
            
            captcha_id = result.get('request')
            self.logger.info(f"CAPTCHA submitted to 2captcha, ID: {captcha_id}")
            
            # Wait for solution
            for _ in range(30):  # Wait up to 5 minutes
                await asyncio.sleep(10)
                
                check_data = {
                    'key': self.api_key,
                    'action': 'get',
                    'id': captcha_id,
                    'json': 1
                }
                
                response = requests.get('http://2captcha.com/res.php', params=check_data)
                result = response.json()
                
                if result.get('status') == 1:
                    solution = result.get('request')
                    self.logger.info(f"2captcha solution received: {solution}")
                    return solution
                elif result.get('error_text'):
                    self.logger.error(f"2captcha error: {result['error_text']}")
                    return None
            
            self.logger.error("2captcha timeout - no solution received")
            return None
            
        except Exception as e:
            self.logger.error(f"Error with 2captcha: {e}")
            return None

class SmartCaptchaHandler:
    """Smart CAPTCHA handler that tries multiple solving methods"""
    
    def __init__(self, use_2captcha: bool = False, api_key: str = ""):
        self.audio_solver = AudioCaptchaSolver(use_2captcha, api_key)
        self.logger = logging.getLogger(__name__)
    
    async def solve_captcha(self, driver) -> bool:
        """
        Solve any CAPTCHA present on the page
        Returns True if solved successfully, False otherwise
        """
        try:
            # Check for reCAPTCHA v2
            recaptcha_selectors = [
                "iframe[src*='recaptcha']",
                ".g-recaptcha",
                "#recaptcha"
            ]
            
            for selector in recaptcha_selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        self.logger.info("reCAPTCHA v2 detected")
                        token = await self.audio_solver.solve_recaptcha_v2(driver)
                        return token is not None
                except NoSuchElementException:
                    continue
            
            # Check for image CAPTCHA
            image_captcha_selectors = [
                "img[src*='captcha']",
                ".captcha img",
                "#captcha img"
            ]
            
            for selector in image_captcha_selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        self.logger.info("Image CAPTCHA detected")
                        # For image CAPTCHAs, we'd need OCR or manual solving
                        # This is a placeholder for future implementation
                        self.logger.warning("Image CAPTCHA solving not implemented yet")
                        return False
                except NoSuchElementException:
                    continue
            
            self.logger.info("No CAPTCHA detected on page")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in CAPTCHA solving: {e}")
            return False