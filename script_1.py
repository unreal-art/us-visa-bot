# Create the pyproject.toml file for uv package management with Python 3.13
pyproject_toml = '''[project]
name = "visa-slot-automation"
version = "1.0.0"
description = "Automated US Visa Slot Booking System with Audio CAPTCHA Solving"
requires-python = ">=3.13"
authors = [
    { name = "Visa Automation Bot", email = "automation@example.com" }
]
readme = "README.md"
license = { text = "MIT" }

dependencies = [
    "playwright>=1.40.0",
    "playwright-recaptcha>=0.3.0",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "pydub>=0.25.1",
    "speechrecognition>=3.10.0",
    "pyaudio>=0.2.11",
    "cryptography>=41.0.0",
    "schedule>=1.2.0",
    "colorama>=0.4.6",
    "rich>=13.0.0",
    "httpx>=0.25.0",
    "fake-useragent>=1.4.0",
    "python-telegram-bot>=20.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.5.0",
]

[project.scripts]
visa-automation = "src.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
python-version = "3.13"

[tool.black]
line-length = 88
target-version = ['py313']

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
'''

with open('pyproject.toml', 'w') as f:
    f.write(pyproject_toml)

print("✅ Created pyproject.toml")