# Create requirements.txt file
requirements_txt = '''# Core automation and browser control
playwright>=1.40.0
playwright-recaptcha>=0.3.0

# HTTP requests and async support
requests>=2.31.0
httpx>=0.25.0

# Configuration and environment
python-dotenv>=1.0.0
cryptography>=41.0.0

# Audio processing for CAPTCHA solving
pydub>=0.25.1
speechrecognition>=3.10.0
pyaudio>=0.2.11

# Task scheduling and automation
schedule>=1.2.0

# User interface and logging  
colorama>=0.4.6
rich>=13.0.0

# Utilities
fake-useragent>=1.4.0
python-telegram-bot>=20.0

# Development and testing
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Optional: For enhanced functionality
# opencv-python>=4.8.0  # For advanced image processing
# pillow>=10.0.0        # For image manipulation
# numpy>=1.24.0         # For numerical operations
'''

with open('requirements.txt', 'w') as f:
    f.write(requirements_txt)

print("✅ Created requirements.txt")