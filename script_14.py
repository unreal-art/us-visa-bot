# Create a test file to verify system functionality
test_automation_py = '''"""
Test suite for visa slot booking automation system
"""
import asyncio
import pytest
import os
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Test configuration loading
def test_config_loading():
    """Test that configuration loads correctly"""
    from config import VisaConfig
    
    config = VisaConfig()
    assert hasattr(config, 'username')
    assert hasattr(config, 'password')
    assert hasattr(config, 'application_id')
    assert hasattr(config, 'country_code')
    assert hasattr(config, 'consular_id')
    print("✅ Configuration loading test passed")

def test_security_questions_loading():
    """Test security questions file loading"""
    from visa_automation import VisaAutomationBot
    from config import VisaConfig
    
    config = VisaConfig()
    bot = VisaAutomationBot(config)
    
    # Test security question matching
    test_question = "What is your mother's maiden name?"
    answer = bot._find_security_answer(test_question)
    
    # Should find an answer or return None gracefully
    assert answer is None or isinstance(answer, str)
    print("✅ Security questions loading test passed")

def test_captcha_solver_initialization():
    """Test CAPTCHA solver initialization"""
    from captcha_solver import SmartCaptchaHandler
    
    handler = SmartCaptchaHandler()
    assert hasattr(handler, 'audio_solver')
    assert hasattr(handler, 'logger')
    print("✅ CAPTCHA solver initialization test passed")

def test_slot_checker_initialization():
    """Test slot checker initialization"""
    from slot_checker import SlotChecker
    from config import VisaConfig
    
    config = VisaConfig()
    checker = SlotChecker(config)
    
    assert hasattr(checker, 'config')
    assert hasattr(checker, 'base_urls')
    print("✅ Slot checker initialization test passed")

@pytest.mark.asyncio
async def test_browser_initialization():
    """Test browser initialization without actually launching"""
    from visa_automation import VisaAutomationBot
    from config import VisaConfig
    
    config = VisaConfig()
    bot = VisaAutomationBot(config)
    
    # Test that initialization method exists
    assert hasattr(bot, 'initialize_browser')
    print("✅ Browser initialization test passed")

def test_utility_functions():
    """Test utility functions"""
    from utils import validate_email, get_consulate_name, parse_date_string
    
    # Test email validation
    assert validate_email("test@example.com") == True
    assert validate_email("invalid-email") == False
    
    # Test consulate name lookup
    assert get_consulate_name("122") == "Chennai"
    assert get_consulate_name("999") == "Consulate 999"
    
    # Test date parsing
    test_date = parse_date_string("2024-12-25")
    assert test_date is not None
    assert test_date.year == 2024
    
    print("✅ Utility functions test passed")

def test_environment_setup():
    """Test environment setup"""
    required_files = ['pyproject.toml', 'config.py', 'main.py']
    
    for file in required_files:
        assert os.path.exists(file), f"Required file {file} not found"
    
    print("✅ Environment setup test passed")

def test_json_config_files():
    """Test JSON configuration files"""
    if os.path.exists('security_questions.json'):
        with open('security_questions.json', 'r') as f:
            data = json.load(f)
            assert 'security_answers' in data
            assert isinstance(data['security_answers'], dict)
    
    print("✅ JSON configuration files test passed")

def test_rate_limiter():
    """Test rate limiter functionality"""
    from utils import RateLimiter
    
    limiter = RateLimiter(max_requests=5, time_window=60)
    assert limiter.max_requests == 5
    assert limiter.time_window == 60
    assert len(limiter.requests) == 0
    
    print("✅ Rate limiter test passed")

@pytest.mark.asyncio
async def test_slot_data_parsing():
    """Test slot data parsing"""
    from slot_checker import SlotChecker
    from config import VisaConfig
    
    config = VisaConfig()
    checker = SlotChecker(config)
    
    # Test with mock data
    mock_data = {
        'available_dates': [
            {
                'date': '2024-12-25',
                'consulate': 'Chennai',
                'consulate_id': '122'
            }
        ]
    }
    
    slots = checker._parse_api_response(mock_data)
    assert len(slots) == 1
    assert slots[0].consulate == 'Chennai'
    
    print("✅ Slot data parsing test passed")

def run_all_tests():
    """Run all tests"""
    print("🧪 Running visa automation system tests...")
    print("=" * 50)
    
    try:
        test_config_loading()
        test_security_questions_loading()
        test_captcha_solver_initialization()
        test_slot_checker_initialization()
        test_utility_functions()
        test_environment_setup()
        test_json_config_files()
        test_rate_limiter()
        
        # Run async tests
        asyncio.run(test_browser_initialization())
        asyncio.run(test_slot_data_parsing())
        
        print("=" * 50)
        print("🎉 All tests passed successfully!")
        print("✅ System is ready for use")
        
    except Exception as e:
        print("=" * 50)
        print(f"❌ Test failed: {e}")
        print("❌ Please check your installation")
        return False
    
    return True

if __name__ == "__main__":
    run_all_tests()
'''

with open('test_automation.py', 'w') as f:
    f.write(test_automation_py)

print("✅ Created test_automation.py")