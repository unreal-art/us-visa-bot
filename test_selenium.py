#!/usr/bin/env python3
"""
Test script for Selenium-based visa automation
"""
import asyncio
import logging
from config import VisaConfig
from visa_automation import VisaAutomationBot

async def test_selenium_automation():
    """Test the Selenium automation setup"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create config
    config = VisaConfig()
    
    # Create automation bot
    bot = VisaAutomationBot(config)
    
    try:
        logger.info("Testing Selenium WebDriver setup...")
        
        # Test WebDriver initialization
        driver = bot._setup_driver()
        logger.info("✅ WebDriver initialized successfully")
        
        # Test basic navigation
        logger.info("Testing basic navigation...")
        driver.get("https://www.google.com")
        logger.info("✅ Basic navigation works")
        
        # Test page title
        title = driver.title
        logger.info(f"✅ Page title retrieved: {title}")
        
        logger.info("🎉 Selenium automation test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
    finally:
        if bot.driver:
            bot.driver.quit()
            logger.info("WebDriver closed")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_selenium_automation())
    if success:
        print("\n✅ Selenium automation is ready!")
    else:
        print("\n❌ Selenium automation test failed!")
