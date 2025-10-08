"""
Configuration settings for visa slot automation
"""
import os
from typing import Dict, List
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class VisaConfig:
    """Configuration for visa booking automation"""

    # User credentials
    username: str = os.getenv("VISA_USERNAME", "")
    password: str = os.getenv("VISA_PASSWORD", "")

    # Application details
    application_id: str = os.getenv("APPLICATION_ID", "")
    country_code: str = os.getenv("COUNTRY_CODE", "in")  # India by default
    consular_id: str = os.getenv("CONSULAR_ID", "122")  # Chennai consulate

    # Automation settings
    retry_timeout: int = int(os.getenv("RETRY_TIMEOUT", "180"))  # 3 minutes
    max_retries: int = int(os.getenv("MAX_RETRIES", "50"))
    headless: bool = os.getenv("HEADLESS", "false").lower() == "true"

    # Notification settings
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # CAPTCHA settings
    use_2captcha: bool = os.getenv("USE_2CAPTCHA", "false").lower() == "true"
    captcha_api_key: str = os.getenv("CAPTCHA_API_KEY", "")

    # Visa portal URLs
    visa_urls = {
        "in": "https://ais.usvisa-info.com/en-in/niv/",
        "ca": "https://ais.usvisa-info.com/en-ca/niv/",
        "us": "https://ustraveldocs.com/",
    }

    def get_base_url(self) -> str:
        """Get base URL for the country"""
        return self.visa_urls.get(self.country_code, self.visa_urls["in"])

# Indian consulate IDs
INDIAN_CONSULATES = {
    "122": "Chennai",
    "123": "Hyderabad", 
    "124": "Kolkata",
    "125": "Mumbai",
    "126": "New Delhi",
}

# Common security questions and their potential answers
SECURITY_QUESTIONS = {
    "What is your mother's maiden name?": "MOTHER_MAIDEN_NAME",
    "What was the name of your first pet?": "FIRST_PET_NAME",
    "What city were you born in?": "BIRTH_CITY",
    "What is the name of your elementary school?": "ELEMENTARY_SCHOOL",
    "What street did you grow up on?": "CHILDHOOD_STREET",
}
