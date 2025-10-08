# GitHub Actions Visa Slot Monitor

This repository includes a GitHub Actions workflow that automatically monitors Indian US visa slots every 5 minutes and sends Telegram notifications when main consulate slots become available.

## 🚀 Features

- **Automated Monitoring**: Runs every 5 minutes via cron schedule
- **Manual Trigger**: Can be triggered manually via GitHub Actions UI
- **Telegram Notifications**: Sends notifications only for main consulate slots (excludes VAC)
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **Artifact Upload**: Saves logs as GitHub Actions artifacts

## 📋 Setup Instructions

### 1. Repository Setup

1. Fork or clone this repository
2. Ensure the following files are present:
   - `.github/workflows/slot-monitor.yml`
   - `monitor.py`

### 2. GitHub Secrets Configuration

Go to your repository → Settings → Secrets and variables → Actions, and add:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 3. Telegram Bot Setup

1. **Create a Telegram Bot:**

   - Message @BotFather on Telegram
   - Use `/newbot` command
   - Get your bot token

2. **Get your Chat ID:**
   - Message your bot
   - Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Find your chat ID in the response

### 4. Workflow Configuration

The workflow is configured to:

- **Schedule**: Run every 5 minutes (`*/5 * * * *`)
- **Duration**: Monitor for 5 minutes per run
- **Interval**: Check slots every 30 seconds
- **Notifications**: Only for main consulates (Chennai, Mumbai, Hyderabad, Kolkata, Delhi)

## 🎮 Usage

### Automatic Monitoring

The workflow runs automatically every 5 minutes. No action required.

### Manual Trigger

1. Go to your repository → Actions tab
2. Select "Visa Slot Monitor" workflow
3. Click "Run workflow"
4. Optionally set custom interval (default: 30 seconds)
5. Click "Run workflow"

### Monitoring Behavior

**Terminal Output (GitHub Actions logs):**

- Shows all locations (main consulates + VAC)
- Displays slot counts for each consulate
- Logs check timestamps and results

**Telegram Notifications:**

- Only sent for main consulate slots
- Excludes all VAC locations
- 5-minute cooldown between notifications

## 📊 Workflow Details

### Schedule

```yaml
schedule:
  - cron: "*/5 * * * *" # Every 5 minutes
```

### Manual Trigger

```yaml
workflow_dispatch:
  inputs:
    interval:
      description: "Monitor interval in seconds"
      required: false
      default: "30"
      type: string
```

### Environment Variables

- `MONITOR_INTERVAL`: Check interval in seconds (default: 30)
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHAT_ID`: Your Telegram chat ID

## 🔍 Monitoring Locations

The monitor checks all Indian consulates:

- **Chennai** (main + VAC)
- **Mumbai** (main + VAC)
- **Hyderabad** (main + VAC)
- **Kolkata** (main + VAC)
- **New Delhi** (main + VAC)

## 📱 Telegram Notification Format

```
🎯 MAIN CONSULATE SLOTS AVAILABLE! (2 locations)

📍 Chennai: 5 slots
📍 Mumbai: 3 slots

⏰ Checked at: 2025-10-09 01:59:04

⚡ Book now at: https://www.usvisascheduling.com/
```

## 🛠️ Troubleshooting

### Common Issues

1. **No Telegram Notifications:**

   - Check if `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set correctly
   - Verify bot token and chat ID are valid
   - Check GitHub Actions logs for errors

2. **Workflow Not Running:**

   - Ensure the workflow file is in `.github/workflows/` directory
   - Check if the repository has Actions enabled
   - Verify cron schedule syntax

3. **API Errors:**
   - Check GitHub Actions logs for API response errors
   - Verify the API endpoint is accessible
   - Check if API key is still valid

### Logs and Artifacts

- **Live Logs**: Available in GitHub Actions run logs
- **Artifacts**: Logs are saved as artifacts for 7 days
- **Debugging**: Enable verbose logging by checking the workflow logs

## 🧪 Local Testing

Test the monitor locally using `uv`:

```bash
# Run the monitor
uv run monitor.py
```

## 🔧 Customization

### Change Monitoring Interval

Edit `.github/workflows/slot-monitor.yml`:

```yaml
schedule:
  - cron: "*/10 * * * *" # Every 10 minutes instead of 5
```

### Change Check Frequency

Set environment variable in workflow:

```yaml
env:
  MONITOR_INTERVAL: "60" # Check every 60 seconds
```

### Add More Consulates

Edit `monitor.py` and add to `all_consulate_mapping`:

```python
'NEW_CITY': 'New City',
'NEW_CITY VAC': 'New City VAC'
```

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This tool is for educational and automation purposes only. Users are responsible for:

- Complying with all applicable terms of service
- Using the software ethically and legally
- Understanding the risks of automated systems
- Maintaining the security of their credentials

The authors are not responsible for any misuse or consequences of using this software.
