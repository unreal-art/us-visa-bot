@echo off
REM Visa Slot Automation - Windows Installation Script

echo 🎯 Visa Slot Booking Automation - Windows Installation
echo =======================================================
echo.

REM Check if PowerShell is available
powershell -Command "Write-Host 'PowerShell is available'"
if errorlevel 1 (
    echo ERROR: PowerShell is required but not found
    pause
    exit /b 1
)

echo [INFO] Checking for uv package manager...
uv --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing uv package manager...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"

    REM Refresh PATH
    call refreshenv >nul 2>&1

    uv --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install uv
        pause
        exit /b 1
    )
    echo [SUCCESS] uv installed successfully
) else (
    echo [SUCCESS] uv is already installed
)

echo [INFO] Installing Python 3.13...
uv python install 3.13
if errorlevel 1 (
    echo [ERROR] Failed to install Python 3.13
    pause
    exit /b 1
)
echo [SUCCESS] Python 3.13 installed

echo [INFO] Installing FFmpeg...
winget install ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg installation failed
    echo [WARNING] Please install FFmpeg manually from https://ffmpeg.org/download.html
) else (
    echo [SUCCESS] FFmpeg installed
)

echo [INFO] Setting up Python virtual environment...
uv venv --python 3.13
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment created

echo [INFO] Installing Python dependencies...
.venv\Scripts\uv pip install playwright>=1.40.0
.venv\Scripts\uv pip install playwright-recaptcha>=0.3.0
.venv\Scripts\uv pip install requests>=2.31.0
.venv\Scripts\uv pip install python-dotenv>=1.0.0
.venv\Scripts\uv pip install pydub>=0.25.1
.venv\Scripts\uv pip install speechrecognition>=3.10.0
.venv\Scripts\uv pip install cryptography>=41.0.0
.venv\Scripts\uv pip install schedule>=1.2.0
.venv\Scripts\uv pip install colorama>=0.4.6
.venv\Scripts\uv pip install rich>=13.0.0
.venv\Scripts\uv pip install httpx>=0.25.0
.venv\Scripts\uv pip install fake-useragent>=1.4.0
.venv\Scripts\uv pip install python-telegram-bot>=20.0
echo [SUCCESS] Python dependencies installed

echo [INFO] Installing Playwright browsers...
.venv\Scripts\playwright install chromium
if errorlevel 1 (
    echo [ERROR] Failed to install browsers
    pause
    exit /b 1
)
echo [SUCCESS] Playwright browsers installed

echo [INFO] Creating configuration files...
if not exist .env (
    echo # Visa Portal Credentials > .env
    echo VISA_USERNAME=your_email@example.com >> .env
    echo VISA_PASSWORD=your_password >> .env
    echo. >> .env
    echo # Application Details >> .env
    echo APPLICATION_ID=123456789 >> .env
    echo COUNTRY_CODE=in >> .env
    echo CONSULAR_ID=122 >> .env
    echo. >> .env
    echo # Automation Settings >> .env
    echo RETRY_TIMEOUT=180 >> .env
    echo MAX_RETRIES=50 >> .env
    echo HEADLESS=false >> .env
    echo [SUCCESS] Created .env file
    echo [WARNING] Please edit .env with your credentials
) else (
    echo [SUCCESS] .env file already exists
)

if not exist security_questions.json (
    echo { > security_questions.json
    echo     "security_answers": { >> security_questions.json
    echo         "What is your mother's maiden name?": "YourMothersMaidenName", >> security_questions.json
    echo         "What was the name of your first pet?": "YourFirstPetName", >> security_questions.json
    echo         "What city were you born in?": "YourBirthCity" >> security_questions.json
    echo     } >> security_questions.json
    echo } >> security_questions.json
    echo [SUCCESS] Created security_questions.json
    echo [WARNING] Please edit security_questions.json with your answers
) else (
    echo [SUCCESS] security_questions.json already exists
)

echo [INFO] Running tests...
.venv\Scripts\python --version | find "3.13" >nul
if errorlevel 1 (
    echo [ERROR] Python 3.13 test failed
    pause
    exit /b 1
)
echo [SUCCESS] Python 3.13 is working

echo.
echo 🎉 Installation completed successfully!
echo.
echo 📋 Next Steps:
echo 1. Edit .env file with your visa portal credentials
echo 2. Edit security_questions.json with your security question answers
echo 3. Run the automation:
echo.
echo    REM Activate virtual environment
echo    .venv\Scripts\activate
echo.
echo    REM Run interactive setup
echo    python main.py --setup
echo.
echo    REM Or run directly
echo    python main.py
echo.
echo 📚 For more information, see README.md
echo.
echo ⚠️  Important: Review all settings before running automated booking!
echo.
pause
