# Create the captcha solver with audio CAPTCHA support
captcha_solver_py = '''"""
Advanced CAPTCHA solver with audio support for visa booking automation
Supports both free speech recognition and paid services like 2captcha
"""
import os
import tempfile
import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path

import speech_recognition as sr
import requests
from pydub import AudioSegment
from playwright.async_api import Page, ElementHandle
from playwright_recaptcha import recaptchav2

class AudioCaptchaSolver:
    """Intelligent audio CAPTCHA solver with multiple fallback methods"""
    
    def __init__(self, use_2captcha: bool = False, api_key: str = ""):
        self.use_2captcha = use_2captcha
        self.api_key = api_key
        self.recognizer = sr.Recognizer()
        self.logger = logging.getLogger(__name__)
        
    async def solve_recaptcha_v2(self, page: Page) -> Optional[str]:
        """
        Solve reCAPTCHA v2 using audio challenge
        Returns the g-recaptcha-response token
        """
        try:
            # Use playwright-recaptcha for automated solving
            async with recaptchav2.AsyncSolver(page) as solver:
                token = await solver.solve_recaptcha()
                self.logger.info("✅ reCAPTCHA v2 solved successfully")
                return token
        except Exception as e:
            self.logger.error(f"❌ Failed to solve reCAPTCHA v2: {e}")
            return None
    
    async def solve_audio_captcha_custom(self, page: Page) -> Optional[str]:
        """
        Custom audio CAPTCHA solver with advanced techniques
        """
        try:
            # Look for audio CAPTCHA button
            audio_button = await page.query_selector('button[title*="audio"], button[aria-label*="audio"]')
            if audio_button:
                await audio_button.click()
                await page.wait_for_timeout(2000)
            
            # Find audio element
            audio_element = await page.query_selector('audio source, audio')
            if not audio_element:
                self.logger.warning("No audio element found")
                return None
            
            # Get audio URL
            audio_src = await audio_element.get_attribute('src')
            if not audio_src:
                self.logger.warning("No audio source URL found")
                return None
            
            # Download and process audio
            audio_text = await self._process_audio_file(audio_src, page)
            
            if audio_text:
                # Fill in the CAPTCHA response
                text_input = await page.query_selector('input[type="text"]')
                if text_input:
                    await text_input.fill(audio_text)
                    
                # Submit the CAPTCHA
                submit_button = await page.query_selector('button[type="submit"], input[type="submit"]')
                if submit_button:
                    await submit_button.click()
                
                self.logger.info(f"✅ Audio CAPTCHA solved with text: {audio_text}")
                return audio_text
            
        except Exception as e:
            self.logger.error(f"❌ Custom audio CAPTCHA solving failed: {e}")
            return None
    
    async def _process_audio_file(self, audio_url: str, page: Page) -> Optional[str]:
        """Download and transcribe audio file"""
        try:
            # Download audio file
            audio_data = await self._download_audio(audio_url, page)
            if not audio_data:
                return None
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                # Convert to WAV format if needed
                audio = AudioSegment.from_file(temp_path)
                audio = audio.set_frame_rate(16000).set_channels(1)
                wav_path = temp_path.replace('.wav', '_converted.wav')
                audio.export(wav_path, format='wav')
                
                # Transcribe using multiple methods
                text = await self._transcribe_audio_multiple_methods(wav_path)
                return text
                
            finally:
                # Cleanup temporary files
                for path in [temp_path, wav_path]:
                    if os.path.exists(path):
                        os.unlink(path)
                        
        except Exception as e:
            self.logger.error(f"❌ Audio processing failed: {e}")
            return None
    
    async def _download_audio(self, audio_url: str, page: Page) -> Optional[bytes]:
        """Download audio file from URL"""
        try:
            # Use page context to maintain cookies and headers
            response = await page.request.get(audio_url)
            if response.status == 200:
                return await response.body()
            else:
                self.logger.error(f"Failed to download audio: HTTP {response.status}")
                return None
        except Exception as e:
            self.logger.error(f"Error downloading audio: {e}")
            return None
    
    async def _transcribe_audio_multiple_methods(self, audio_path: str) -> Optional[str]:
        """Try multiple transcription methods for better accuracy"""
        
        # Method 1: Google Speech Recognition (Free)
        try:
            with sr.AudioFile(audio_path) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data, language='en-US')
                self.logger.info(f"Google Speech Recognition result: {text}")
                if text.strip():
                    return text.strip().lower()
        except Exception as e:
            self.logger.warning(f"Google Speech Recognition failed: {e}")
        
        # Method 2: Wit.ai (if API key available)
        try:
            wit_api_key = os.getenv('WIT_API_KEY')
            if wit_api_key:
                with sr.AudioFile(audio_path) as source:
                    audio_data = self.recognizer.record(source)
                    text = self.recognizer.recognize_wit(audio_data, key=wit_api_key)
                    self.logger.info(f"Wit.ai result: {text}")
                    if text.strip():
                        return text.strip().lower()
        except Exception as e:
            self.logger.warning(f"Wit.ai recognition failed: {e}")
        
        # Method 3: 2captcha service (if enabled and API key available)
        if self.use_2captcha and self.api_key:
            try:
                result = await self._solve_with_2captcha(audio_path)
                if result:
                    return result
            except Exception as e:
                self.logger.warning(f"2captcha service failed: {e}")
        
        return None
    
    async def _solve_with_2captcha(self, audio_path: str) -> Optional[str]:
        """Use 2captcha service to solve audio CAPTCHA"""
        try:
            # Upload audio file to 2captcha
            with open(audio_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'key': self.api_key,
                    'method': 'audio',
                    'lang': 'en'
                }
                
                response = requests.post('http://2captcha.com/in.php', files=files, data=data)
                
                if response.text.startswith('OK|'):
                    captcha_id = response.text.split('|')[1]
                    
                    # Wait for solution
                    for _ in range(30):  # Wait up to 5 minutes
                        await asyncio.sleep(10)
                        
                        result_response = requests.get(
                            f'http://2captcha.com/res.php?key={self.api_key}&action=get&id={captcha_id}'
                        )
                        
                        if result_response.text.startswith('OK|'):
                            solution = result_response.text.split('|')[1]
                            self.logger.info(f"2captcha solution: {solution}")
                            return solution
                        elif result_response.text == 'CAPCHA_NOT_READY':
                            continue
                        else:
                            break
                            
        except Exception as e:
            self.logger.error(f"2captcha service error: {e}")
            
        return None

class SmartCaptchaHandler:
    """
    Smart CAPTCHA handler that automatically detects and solves various CAPTCHA types
    """
    
    def __init__(self, use_2captcha: bool = False, api_key: str = ""):
        self.audio_solver = AudioCaptchaSolver(use_2captcha, api_key)
        self.logger = logging.getLogger(__name__)
    
    async def handle_captcha(self, page: Page) -> bool:
        """
        Automatically detect and solve CAPTCHA on the page
        Returns True if CAPTCHA was solved successfully
        """
        try:
            # Check for reCAPTCHA v2
            recaptcha_frame = await page.query_selector('iframe[src*="recaptcha"]')
            if recaptcha_frame:
                self.logger.info("🔍 Detected reCAPTCHA v2")
                token = await self.audio_solver.solve_recaptcha_v2(page)
                return token is not None
            
            # Check for audio CAPTCHA elements
            audio_elements = await page.query_selector_all('audio, button[title*="audio"]')
            if audio_elements:
                self.logger.info("🔍 Detected audio CAPTCHA")
                result = await self.audio_solver.solve_audio_captcha_custom(page)
                return result is not None
                
            # Check for other CAPTCHA indicators
            captcha_indicators = [
                'div[class*="captcha"]',
                'img[alt*="captcha"]',
                'canvas[id*="captcha"]'
            ]
            
            for indicator in captcha_indicators:
                element = await page.query_selector(indicator)
                if element:
                    self.logger.info(f"🔍 Detected CAPTCHA element: {indicator}")
                    # Add specific handling based on CAPTCHA type
                    break
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ CAPTCHA handling failed: {e}")
            return False
'''

with open('captcha_solver.py', 'w') as f:
    f.write(captcha_solver_py)

print("✅ Created captcha_solver.py")