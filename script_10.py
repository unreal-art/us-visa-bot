# Create a proper main.py without syntax errors
main_py_content = """#!/usr/bin/env python3
\"\"\"
Visa Slot Booking Automation - Main Entry Point
Usage: python main.py [options]
\"\"\"
import asyncio
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from config import VisaConfig
from visa_automation import VisaAutomationBot

console = Console()

def display_banner():
    \"\"\"Display application banner\"\"\"
    banner = Text()
    banner.append("🎯 VISA SLOT BOOKING AUTOMATION 🎯", style="bold blue")
    
    panel = Panel(
        banner,
        title="Advanced Automation System",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print(panel)
    console.print()

def display_config_info(config: VisaConfig):
    \"\"\"Display current configuration\"\"\"
    table = Table(title="📋 Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Country", config.country_code.upper())
    table.add_row("Consulate ID", config.consular_id)
    table.add_row("Username", config.username[:3] + "*" * (len(config.username) - 3))
    table.add_row("Retry Timeout", f"{config.retry_timeout}s")
    table.add_row("Max Retries", str(config.max_retries))
    table.add_row("Headless Mode", "Yes" if config.headless else "No")
    table.add_row("2Captcha", "Enabled" if config.use_2captcha else "Disabled")
    table.add_row("Telegram Notifications", "Enabled" if config.telegram_bot_token else "Disabled")
    
    console.print(table)
    console.print()

def setup_environment():
    \"\"\"Setup environment and check requirements\"\"\"
    console.print("🔧 Checking environment setup...", style="yellow")
    
    # Check for required files
    required_files = ['security_questions.json', '.env']
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        console.print(f"❌ Missing required files: {', '.join(missing_files)}", style="red")
        console.print("Please create these files before running the automation.", style="red")
        return False
    
    # Check environment variables
    required_env_vars = ['VISA_USERNAME', 'VISA_PASSWORD', 'APPLICATION_ID']
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        console.print(f"❌ Missing environment variables: {', '.join(missing_vars)}", style="red")
        console.print("Please set these in your .env file.", style="red")
        return False
    
    console.print("✅ Environment setup complete!", style="green")
    return True

def create_sample_env_file():
    \"\"\"Create a sample .env file\"\"\"
    env_content = '''# Visa Portal Credentials
VISA_USERNAME=your_email@example.com
VISA_PASSWORD=your_password

# Application Details
APPLICATION_ID=123456789
COUNTRY_CODE=in
CONSULAR_ID=122

# Automation Settings
RETRY_TIMEOUT=180
MAX_RETRIES=50
HEADLESS=false

# Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# CAPTCHA Service (Optional)
USE_2CAPTCHA=false
CAPTCHA_API_KEY=your_2captcha_api_key
'''
    
    with open('.env.example', 'w') as f:
        f.write(env_content)
    
    console.print("✅ Created .env.example file", style="green")
    console.print("📝 Please copy it to .env and fill in your details", style="yellow")

async def run_interactive_setup():
    \"\"\"Interactive setup for first-time users\"\"\"
    console.print("🛠️  Interactive Setup", style="bold blue")
    console.print("Let's configure your visa automation system...\\n")
    
    # Collect basic information
    username = console.input("📧 Enter your visa portal email: ")
    password = console.input("🔐 Enter your password: ", password=True)
    app_id = console.input("📋 Enter your application ID: ")
    
    console.print("\\n🏛️  Select your consulate:")
    console.print("122 - Chennai")
    console.print("123 - Hyderabad") 
    console.print("124 - Kolkata")
    console.print("125 - Mumbai")
    console.print("126 - New Delhi")
    
    consulate_id = console.input("Enter consulate ID (default: 122): ") or "122"
    
    # Create .env file
    env_content = f'''VISA_USERNAME={username}
VISA_PASSWORD={password}
APPLICATION_ID={app_id}
COUNTRY_CODE=in
CONSULAR_ID={consulate_id}
RETRY_TIMEOUT=180
MAX_RETRIES=50
HEADLESS=false
'''
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    console.print("✅ Configuration saved to .env file", style="green")
    return True

def parse_arguments():
    \"\"\"Parse command line arguments\"\"\"
    parser = argparse.ArgumentParser(
        description="Visa Slot Booking Automation System"
    )
    
    parser.add_argument('--setup', action='store_true', 
                       help='Run interactive setup')
    parser.add_argument('--headless', action='store_true',
                       help='Run browser in headless mode')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check for available slots, do not attempt booking')
    parser.add_argument('--consulate-id', type=str,
                       help='Override consulate ID from config')
    parser.add_argument('--timeout', type=int, default=180,
                       help='Override retry timeout (seconds)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    return parser.parse_args()

async def main():
    \"\"\"Main application entry point\"\"\"
    try:
        # Display banner
        display_banner()
        
        # Parse arguments
        args = parse_arguments()
        
        # Handle setup mode
        if args.setup:
            await run_interactive_setup()
            return
        
        # Check environment setup
        if not setup_environment():
            console.print("\\n💡 Run with --setup flag for interactive configuration", style="blue")
            create_sample_env_file()
            return
        
        # Load configuration
        config = VisaConfig()
        
        # Override config with command line arguments
        if args.headless:
            config.headless = True
        if args.consulate_id:
            config.consular_id = args.consulate_id
        if args.timeout:
            config.retry_timeout = args.timeout
        
        # Display configuration
        display_config_info(config)
        
        # Confirm start
        if not args.check_only:
            console.print("⚠️  This will attempt to automatically book visa appointments", style="yellow")
            console.print("⚠️  Make sure you have reviewed all settings carefully", style="yellow")
            
            if not console.input("\\n🚀 Start automation? (y/N): ").lower().startswith('y'):
                console.print("Automation cancelled.", style="red")
                return
        
        # Initialize and run automation
        console.print("\\n🚀 Starting visa slot automation...", style="green")
        bot = VisaAutomationBot(config)
        
        if args.check_only:
            # Only check for slots
            slots = await bot.slot_checker.check_available_slots()
            if slots:
                console.print(f"Found {len(slots)} available slots:", style="green")
                for slot in slots:
                    console.print(f"  📅 {slot}")
            else:
                console.print("No available slots found.", style="yellow")
        else:
            # Run full automation
            await bot.run_automation()
        
    except KeyboardInterrupt:
        console.print("\\n🛑 Automation stopped by user", style="yellow")
    except Exception as e:
        console.print(f"\\n❌ Error: {e}", style="red")
        if args.verbose:
            import traceback
            console.print(traceback.format_exc(), style="red")

if __name__ == "__main__":
    asyncio.run(main())
"""

with open('main.py', 'w') as f:
    f.write(main_py_content)

print("✅ Created main.py")