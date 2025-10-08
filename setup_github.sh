#!/bin/bash
# Setup script for GitHub Actions Visa Slot Monitor

echo "🚀 Setting up GitHub Actions Visa Slot Monitor"
echo "=============================================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please run 'git init' first."
    exit 1
fi

# Create .github/workflows directory if it doesn't exist
mkdir -p .github/workflows

echo "✅ Created .github/workflows directory"

# Check if workflow file exists
if [ -f ".github/workflows/slot-monitor.yml" ]; then
    echo "✅ Workflow file already exists"
else
    echo "❌ Workflow file not found. Please ensure slot-monitor.yml is in .github/workflows/"
fi

# Check if github_monitor.py exists
if [ -f "monitor.py" ]; then
    echo "✅ Monitor script exists"
else
    echo "❌ monitor.py not found"
fi

echo ""
echo "📋 Next steps:"
echo "1. Add your Telegram credentials as GitHub Secrets:"
echo "   - TELEGRAM_BOT_TOKEN"
echo "   - TELEGRAM_CHAT_ID"
echo ""
echo "2. Push to GitHub:"
echo "   git add ."
echo "   git commit -m 'Add GitHub Actions visa slot monitor'"
echo "   git push origin main"
echo ""
echo "3. Enable GitHub Actions in your repository settings"
echo ""
echo "4. Test the workflow:"
echo "   - Go to Actions tab in your GitHub repository"
echo "   - Click 'Visa Slot Monitor'"
echo "   - Click 'Run workflow'"
echo ""
echo "🎉 Your automated visa slot monitor will run every 5 minutes!"

# Check if .env file exists for local testing
if [ -f ".env" ]; then
    echo ""
echo "💡 Local testing:"
echo "   uv run monitor.py         # Run monitor"
fi
