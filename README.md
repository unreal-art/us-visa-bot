# 🎯 Visa Slot Booking Automation System

An intelligent, automated system for booking US visa appointments in India using Python 3.13, uv package manager, Playwright browser automation, and advanced audio CAPTCHA solving.

## ✨ Features

- **🤖 Intelligent Automation**: Fully automated visa slot booking with advanced anti-detection measures
- **🔊 Audio CAPTCHA Solving**: Advanced audio CAPTCHA recognition using multiple AI services
- **📊 Real-time Monitoring**: Integration with checkvisaslots.com API for real-time slot availability
- **🔔 Smart Notifications**: Telegram notifications when slots become available
- **🛡️ Anti-Bot Protection**: Stealth browser settings and human-like behavior simulation
- **⚙️ Configurable**: Flexible configuration for different consulates and preferences
- **📝 Security Questions**: Automated handling of security questions during booking
- **💾 Backup & Logging**: Comprehensive logging and backup systems

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- uv package manager
- FFmpeg (for audio processing)

### Installation

1. **Install uv (if not already installed):**

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. **Clone or create the project:**

```bash
mkdir visa-slot-automation
cd visa-slot-automation
```

3. **Install Python 3.13 and dependencies:**

```bash
uv python install 3.13
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

4. **Install Playwright browsers:**

```bash
playwright install chromium
```

5. **Install FFmpeg (for audio CAPTCHA):**

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
winget install ffmpeg
```

### Configuration

1. **Run interactive setup:**

```bash
python main.py --setup
```

2. **Or manually create `.env` file:**

```env
# Visa Portal Credentials
VISA_USERNAME=your_email@example.com
VISA_PASSWORD=your_password

# Application Details
APPLICATION_ID=123456789
COUNTRY_CODE=in
CONSULAR_ID=122

# Optional: Notifications
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Optional: 2Captcha Service
USE_2CAPTCHA=false
CAPTCHA_API_KEY=your_api_key
```

3. **Configure security questions in `security_questions.json`:**

```json
{
  "security_answers": {
    "What is your mother's maiden name?": "YourAnswer",
    "What city were you born in?": "YourBirthCity"
  }
}
```

## 🎮 Usage

### Basic Usage

```bash
# Check for available slots only
python main.py --check-only

# Run full automation
python main.py

# Run in headless mode
python main.py --headless

# Use specific consulate
python main.py --consulate-id 125
```

### Advanced Options

```bash
# Interactive setup
python main.py --setup

# Custom timeout
python main.py --timeout 300

# Verbose logging
python main.py --verbose

# Headless with custom consulate
python main.py --headless --consulate-id 126
```

## 🏛️ Indian Consulate IDs

| Consulate | ID  |
| --------- | --- |
| Chennai   | 122 |
| Hyderabad | 123 |
| Kolkata   | 124 |
| Mumbai    | 125 |
| New Delhi | 126 |

## 🔧 Configuration Details

### Environment Variables

| Variable             | Description                           | Required |
| -------------------- | ------------------------------------- | -------- |
| `VISA_USERNAME`      | Your visa portal email                | Yes      |
| `VISA_PASSWORD`      | Your visa portal password             | Yes      |
| `APPLICATION_ID`     | Your visa application ID              | Yes      |
| `COUNTRY_CODE`       | Country code (default: in)            | No       |
| `CONSULAR_ID`        | Consulate ID                          | No       |
| `RETRY_TIMEOUT`      | Seconds between checks (default: 180) | No       |
| `MAX_RETRIES`        | Maximum retry attempts (default: 50)  | No       |
| `HEADLESS`           | Run browser in headless mode          | No       |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token                    | No       |
| `TELEGRAM_CHAT_ID`   | Telegram chat ID                      | No       |
| `USE_2CAPTCHA`       | Enable 2captcha service               | No       |
| `CAPTCHA_API_KEY`    | 2captcha API key                      | No       |

### Audio CAPTCHA Methods

The system uses multiple methods for solving audio CAPTCHAs:

1. **Google Speech Recognition** (Free) - Primary method
2. **Wit.ai** (Free with API key) - Backup method
3. **2captcha Service** (Paid) - Most reliable fallback
4. **playwright-recaptcha** - Automated reCAPTCHA v2 solver

## 📱 Telegram Notifications

1. **Create a Telegram Bot:**

   - Message @BotFather on Telegram
   - Use `/newbot` command
   - Get your bot token

2. **Get your Chat ID:**

   - Message your bot
   - Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Find your chat ID in the response

3. **Add to `.env`:**

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHI...
TELEGRAM_CHAT_ID=123456789
```

## 🛡️ Security Features

- **Encrypted Storage**: Sensitive data is encrypted at rest
- **Anti-Detection**: Browser fingerprinting protection
- **Rate Limiting**: Automatic rate limiting to avoid blocks
- **Stealth Mode**: Human-like browsing behavior
- **Session Management**: Secure session handling

## 📊 Monitoring & Logging

The system provides comprehensive logging:

- **Real-time Status**: Console output with rich formatting
- **File Logging**: Detailed logs saved to `visa_automation.log`
- **Slot Tracking**: Historical slot availability data
- **Error Tracking**: Detailed error logging and recovery

## 🚨 Important Notes

### Legal and Ethical Considerations

- ⚠️ **Use Responsibly**: This tool should only be used for legitimate visa applications
- ⚠️ **Terms of Service**: Ensure compliance with visa portal terms of service
- ⚠️ **Rate Limits**: The system includes built-in rate limiting to be respectful
- ⚠️ **No Guarantees**: This tool does not guarantee successful bookings

### Technical Limitations

- **Portal Changes**: Visa portals may change and break automation
- **CAPTCHA Difficulty**: Some CAPTCHAs may be unsolvable automatically
- **Network Issues**: Connection problems may affect performance
- **Browser Detection**: Advanced anti-bot measures may block access

## 🔧 Troubleshooting

### Common Issues

1. **FFmpeg Not Found**

```bash
# Install FFmpeg and ensure it's in PATH
which ffmpeg  # Should show path
```

2. **Playwright Browser Issues**

```bash
playwright install --force
```

3. **Audio CAPTCHA Failures**

```bash
# Check audio processing
pip install speechrecognition pydub
```

4. **Login Failures**

- Verify credentials in `.env`
- Check for 2FA requirements
- Try headless=false for debugging

5. **No Slots Found**

- Verify consulate ID
- Check checkvisaslots.com manually
- Adjust retry timeout

### Debug Mode

```bash
# Run with maximum verbosity
python main.py --verbose --check-only

# Run without headless for visual debugging
python main.py --verbose
```

## 🏗️ Project Structure

```
visa-slot-automation/
├── main.py                    # CLI entry point and main application
├── config.py                  # Configuration management and settings
├── visa_automation.py         # Core automation engine with browser control
├── captcha_solver.py          # Advanced audio CAPTCHA solving system
├── slot_checker.py            # Real-time slot monitoring and API integration
├── utils.py                   # Utility functions and helper classes
├── test_automation.py         # Comprehensive test suite
├── security_questions.json    # Security question answers template
├── pyproject.toml            # uv project configuration (Python 3.13)
├── requirements.txt          # Package dependencies
├── install.sh                # Unix/Linux/macOS installer script
├── install.bat               # Windows installer script
└── README.md                 # This documentation
```

### Core Components

- **`main.py`**: Command-line interface with rich console output and interactive setup
- **`visa_automation.py`**: Main automation engine with Playwright browser control and anti-detection
- **`captcha_solver.py`**: Multi-method audio CAPTCHA solver (Google Speech, Wit.ai, 2captcha)
- **`slot_checker.py`**: Real-time slot monitoring via checkvisaslots.com API
- **`config.py`**: Centralized configuration management with environment variables
- **`utils.py`**: Helper functions for encryption, validation, and rate limiting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is provided for educational and automation purposes. Users are responsible for:

- Complying with all applicable terms of service
- Using the software ethically and legally
- Understanding the risks of automated systems
- Maintaining the security of their credentials

The authors are not responsible for any misuse or consequences of using this software.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) - Browser automation framework
- [playwright-recaptcha](https://pypi.org/project/playwright-recaptcha/) - reCAPTCHA solving
- [checkvisaslots.com](https://checkvisaslots.com) - Visa slot monitoring API
- [uv](https://astral.sh/uv/) - Fast Python package manager

---

**⚡ Built with Python 3.13, uv, and intelligent automation**
