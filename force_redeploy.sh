#!/bin/bash
# Force redeploy script for Red Legion Discord Bot
# This script forces a full redeployment and restart

echo "🚀 Red Legion Bot - Force Redeploy"
echo "=================================="

# Set script directory and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "📁 Working directory: $(pwd)"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository. Please run from project root."
    exit 1
fi

# Show current git status
echo "📋 Current git status:"
git status --short

echo ""
echo "🔄 Performing force redeploy..."

# Add a dummy change to force deployment
echo "# Force redeploy at $(date)" >> .redeploy_marker
git add .redeploy_marker

# Commit the change
git commit -m "🚀 Force redeploy: Trigger bot restart and command sync

- Added redeploy marker to force GitHub Actions deployment  
- This will restart the bot and sync all slash commands
- Commands should appear in Discord within 1-10 minutes

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to trigger deployment
echo "⬆️ Pushing to remote to trigger deployment..."
git push

echo ""
echo "✅ Force redeploy completed!"
echo ""
echo "📝 Next steps:"
echo "1. Wait 2-3 minutes for GitHub Actions deployment"
echo "2. Check Discord - bot should reconnect automatically"
echo "3. Use /redsyncommands guild_only:true for immediate command sync"
echo "4. Test commands with /red to see available options"
echo ""
echo "🔍 Monitor deployment:"
echo "- GitHub Actions: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
echo "- Check bot logs on your VM after deployment completes"