"""
Utility functions for visa automation system
"""
import os
import json
import logging
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from pathlib import Path

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('visa_automation.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def encrypt_data(data: str, key: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """Encrypt sensitive data"""
    if key is None:
        key = Fernet.generate_key()

    f = Fernet(key)
    encrypted_data = f.encrypt(data.encode())
    return encrypted_data, key

def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
    """Decrypt sensitive data"""
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_data)
    return decrypted_data.decode()

def hash_password(password: str) -> str:
    """Hash password for secure storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_consulate_name(consulate_id: str) -> str:
    """Get consulate name from ID"""
    consulates = {
        "122": "Chennai",
        "123": "Hyderabad", 
        "124": "Kolkata",
        "125": "Mumbai",
        "126": "New Delhi",
    }
    return consulates.get(consulate_id, f"Consulate {consulate_id}")

def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime object"""
    formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None

def save_json_file(data: Dict[str, Any], filename: str) -> bool:
    """Save data to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON file {filename}: {e}")
        return False

def load_json_file(filename: str) -> Optional[Dict[str, Any]]:
    """Load data from JSON file"""
    try:
        if not Path(filename).exists():
            return None

        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON file {filename}: {e}")
        return None

def create_backup(filename: str) -> bool:
    """Create backup of important files"""
    try:
        if not Path(filename).exists():
            return False

        backup_name = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with open(filename, 'rb') as src:
            with open(backup_name, 'wb') as dst:
                dst.write(src.read())

        logging.info(f"Backup created: {backup_name}")
        return True

    except Exception as e:
        logging.error(f"Error creating backup of {filename}: {e}")
        return False

def cleanup_old_logs(log_dir: str = ".", max_age_days: int = 7):
    """Clean up old log files"""
    try:
        log_files = Path(log_dir).glob("*.log")
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        for log_file in log_files:
            if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                log_file.unlink()
                logging.info(f"Deleted old log file: {log_file}")

    except Exception as e:
        logging.error(f"Error cleaning up logs: {e}")

def generate_user_agent() -> str:
    """Generate realistic user agent string"""
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36", 
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]

    import random
    return random.choice(agents)

class RateLimiter:
    """Simple rate limiter to avoid being blocked"""

    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        import asyncio

        now = datetime.now()

        # Remove old requests outside the time window
        self.requests = [req for req in self.requests 
                        if (now - req).seconds < self.time_window]

        # Check if we need to wait
        if len(self.requests) >= self.max_requests:
            oldest_request = min(self.requests)
            wait_time = self.time_window - (now - oldest_request).seconds

            if wait_time > 0:
                logging.info(f"Rate limit reached, waiting {wait_time} seconds")
                await asyncio.sleep(wait_time)

        # Add current request
        self.requests.append(now)

def validate_config(config) -> tuple[bool, list[str]]:
    """Validate configuration settings"""
    errors = []

    # Check required fields
    if not config.username:
        errors.append("Username is required")
    if not config.password:
        errors.append("Password is required")
    if not config.application_id:
        errors.append("Application ID is required")

    # Validate email format
    if config.username and not validate_email(config.username):
        errors.append("Invalid email format for username")

    # Validate numeric fields
    if config.retry_timeout <= 0:
        errors.append("Retry timeout must be positive")
    if config.max_retries <= 0:
        errors.append("Max retries must be positive")

    return len(errors) == 0, errors
