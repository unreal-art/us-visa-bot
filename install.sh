#!/bin/bash
# Visa Slot Automation - Installation Script
# For Unix-like systems (Linux, macOS)

set -e

echo "🎯 Visa Slot Booking Automation - Installation Script"
echo "====================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on supported system
check_system() {
    print_status "Checking system compatibility..."

    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        print_success "Detected Linux system"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos" 
        print_success "Detected macOS system"
    else
        print_error "Unsupported operating system: $OSTYPE"
        print_error "This script supports Linux and macOS only"
        exit 1
    fi
}

# Install uv if not present
install_uv() {
    print_status "Checking for uv package manager..."

    if command -v uv &> /dev/null; then
        print_success "uv is already installed"
        uv --version
    else
        print_status "Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh

        # Add to PATH for current session
        export PATH="$HOME/.local/bin:$PATH"

        if command -v uv &> /dev/null; then
            print_success "uv installed successfully"
        else
            print_error "Failed to install uv"
            exit 1
        fi
    fi
}

# Install Python 3.13
install_python() {
    print_status "Installing Python 3.13..."

    uv python install 3.13

    if uv python list | grep -q "3.13"; then
        print_success "Python 3.13 installed successfully"
    else
        print_error "Failed to install Python 3.13"
        exit 1
    fi
}

# Install FFmpeg
install_ffmpeg() {
    print_status "Checking for FFmpeg..."

    if command -v ffmpeg &> /dev/null; then
        print_success "FFmpeg is already installed"
        return
    fi

    print_status "Installing FFmpeg..."

    if [[ "$OS" == "linux" ]]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y ffmpeg
        elif command -v yum &> /dev/null; then
            sudo yum install -y ffmpeg
        elif command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm ffmpeg
        else
            print_warning "Could not install FFmpeg automatically"
            print_warning "Please install FFmpeg manually"
        fi
    elif [[ "$OS" == "macos" ]]; then
        if command -v brew &> /dev/null; then
            brew install ffmpeg
        else
            print_warning "Homebrew not found. Please install FFmpeg manually"
            print_warning "Visit: https://ffmpeg.org/download.html"
        fi
    fi

    if command -v ffmpeg &> /dev/null; then
        print_success "FFmpeg installed successfully"
    else
        print_warning "FFmpeg installation may have failed"
        print_warning "Audio CAPTCHA solving may not work properly"
    fi
}

# Setup Python virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."

    uv venv --python 3.13

    print_success "Virtual environment created"
    print_status "Activating virtual environment..."

    source .venv/bin/activate

    print_success "Virtual environment activated"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."

    uv pip install playwright>=1.40.0
    uv pip install playwright-recaptcha>=0.3.0
    uv pip install requests>=2.31.0
    uv pip install python-dotenv>=1.0.0
    uv pip install pydub>=0.25.1
    uv pip install speechrecognition>=3.10.0
    uv pip install cryptography>=41.0.0
    uv pip install schedule>=1.2.0
    uv pip install colorama>=0.4.6
    uv pip install rich>=13.0.0
    uv pip install httpx>=0.25.0
    uv pip install fake-useragent>=1.4.0
    uv pip install python-telegram-bot>=20.0

    print_success "Python dependencies installed"
}

# Install Playwright browsers
install_browsers() {
    print_status "Installing Playwright browsers..."

    .venv/bin/playwright install chromium

    print_success "Playwright browsers installed"
}

# Create configuration files if they don't exist
setup_config() {
    print_status "Setting up configuration files..."

    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            print_success "Created .env from template"
            print_warning "Please edit .env with your credentials"
        else
            cat > .env << EOF
# Visa Portal Credentials
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
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# CAPTCHA Service (Optional)
USE_2CAPTCHA=false
CAPTCHA_API_KEY=
EOF
            print_success "Created .env file"
            print_warning "Please edit .env with your credentials"
        fi
    else
        print_success ".env file already exists"
    fi

    if [[ ! -f "security_questions.json" ]]; then
        cat > security_questions.json << EOF
{
    "security_answers": {
        "What is your mother's maiden name?": "YourMothersMaidenName",
        "What was the name of your first pet?": "YourFirstPetName", 
        "What city were you born in?": "YourBirthCity",
        "What is the name of your elementary school?": "YourElementarySchool",
        "What street did you grow up on?": "YourChildhoodStreet"
    },
    "instructions": {
        "setup": "Replace the values above with your actual security question answers",
        "encryption": "These answers will be encrypted when stored",
        "usage": "The system will automatically match questions and provide answers during booking"
    }
}
EOF
        print_success "Created security_questions.json"
        print_warning "Please edit security_questions.json with your answers"
    else
        print_success "security_questions.json already exists"
    fi
}

# Run tests
run_tests() {
    print_status "Running basic tests..."

    # Test Python installation
    if .venv/bin/python --version | grep -q "3.13"; then
        print_success "Python 3.13 is working"
    else
        print_error "Python 3.13 test failed"
        return 1
    fi

    # Test uv
    if uv --version &> /dev/null; then
        print_success "uv is working"
    else
        print_error "uv test failed"
        return 1
    fi

    # Test FFmpeg
    if ffmpeg -version &> /dev/null; then
        print_success "FFmpeg is working"
    else
        print_warning "FFmpeg test failed - audio CAPTCHA may not work"
    fi

    # Test Python imports
    if .venv/bin/python -c "import playwright; import speechrecognition; import requests" &> /dev/null; then
        print_success "Python dependencies are working"
    else
        print_error "Python dependencies test failed"
        return 1
    fi

    print_success "All tests passed!"
}

# Display final instructions
show_instructions() {
    echo ""
    echo "🎉 Installation completed successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Edit .env file with your visa portal credentials"
    echo "2. Edit security_questions.json with your security question answers"
    echo "3. Run the automation:"
    echo ""
    echo "   # Activate virtual environment"
    echo "   source .venv/bin/activate"
    echo ""
    echo "   # Run interactive setup"
    echo "   python main.py --setup"
    echo ""
    echo "   # Or run directly"
    echo "   python main.py"
    echo ""
    echo "📚 For more information, see README.md"
    echo ""
    print_warning "Important: Review all settings before running automated booking!"
}

# Main installation flow
main() {
    check_system
    install_uv
    install_python
    install_ffmpeg
    setup_venv
    install_dependencies
    install_browsers
    setup_config
    run_tests
    show_instructions
}

# Run main function
main
