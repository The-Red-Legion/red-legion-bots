# Full Redeploy Workflow

## Overview

The **Full Redeploy** workflow provides a complete codebase replacement deployment method as an alternative to the standard incremental rsync-based deployment. This workflow is designed for situations where a clean, complete refresh of the application is needed.

## When to Use Full Redeploy

### Use Cases:
- 🔧 **Clean Slate Deployment**: When you need to ensure no residual files from previous deployments
- 🐛 **Troubleshooting Deployment Issues**: When incremental deployment isn't working properly
- 📁 **File Structure Changes**: When significant directory restructuring has occurred
- 🔄 **Fresh Environment**: After major dependency updates or Python environment changes
- 🚨 **Emergency Recovery**: When the deployed application is in an inconsistent state

### Differences from Standard Deploy:

| Aspect | Standard Deploy | Full Redeploy |
|--------|----------------|---------------|
| **Method** | rsync (incremental) | Complete file copy |
| **Speed** | Faster (only changed files) | Slower (all files) |
| **File Handling** | Preserves existing files | Replaces everything |
| **Dependencies** | Incremental updates | Fresh installation |
| **Cache Cleanup** | Minimal | Complete cleanup |
| **Backup** | No backup | Creates backup |

## How to Trigger

### Via GitHub Actions Web Interface:
1. Navigate to your repository on GitHub
2. Go to **Actions** tab
3. Select **"Full Redeploy Bot (Complete Codebase Copy)"**
4. Click **"Run workflow"**
5. Optionally provide a reason for the deployment
6. Click **"Run workflow"** button

### Via GitHub CLI:
```bash
gh workflow run full-redeploy.yml --field reason="Manual full refresh after dependency updates"
```

## Workflow Process

### Phase 1: Infrastructure Setup
- ✅ Authenticates with GCP
- ✅ Tests VM connectivity
- ✅ Prepares SSH access
- ✅ Creates dynamic inventory

### Phase 2: Full Codebase Deployment
- 🛑 Stops existing bot process
- 📦 Creates backup of current deployment
- 🗑️ Completely removes existing app directory
- 📥 Copies entire codebase via tarball
- 🔧 Fresh dependency installation
- 🧹 Clears all Python caches

### Phase 3: Enhanced Health Verification
- 🔍 Extended process monitoring
- 🤖 Discord API connectivity check
- ⚡ Slash command registration verification
- 📊 Command count reporting

### Phase 4: Comprehensive Log Collection
- 📋 Detailed deployment status
- 📁 File structure verification
- 🔢 File count reporting
- 💾 System resource monitoring
- 🐍 Python environment validation

### Phase 5: Post-Deployment Actions
- ✅ Success/failure notifications
- 📝 Deployment summary
- 🧹 Cleanup operations

## Key Features

### Complete File Replacement
- **No incremental changes**: Every file is replaced fresh
- **Clean Python environment**: All `__pycache__` directories removed
- **Fresh dependencies**: Force reinstall of all Python packages

### Automatic Backup
- **Safety first**: Creates backup before replacement
- **Rollback capability**: Backup available for manual recovery
- **Auto-cleanup**: Removes backup on successful deployment

### Enhanced Monitoring
- **Extended health checks**: More comprehensive than standard deploy
- **Slash command verification**: Confirms Discord integration
- **Detailed logging**: Comprehensive deployment status

## Recovery Options

### If Deployment Fails:
1. **Check logs**: Review the comprehensive log output in Actions
2. **Manual recovery**: SSH to VM and restore from `/app_backup`
3. **Standard deploy**: Try incremental deployment instead
4. **VM restart**: Use the reboot workflow if needed

### Manual Backup Restoration:
```bash
# SSH to VM
ssh ubuntu@YOUR_VM_IP

# Stop bot
sudo systemctl stop red-legion-bot

# Restore from backup
sudo rm -rf /app
sudo mv /app_backup /app

# Start bot
sudo systemctl start red-legion-bot
```

## Best Practices

### Before Running:
- ✅ Ensure all changes are committed and pushed
- ✅ Verify tests are passing
- ✅ Document reason for full deployment
- ✅ Consider if incremental deploy would suffice

### After Running:
- ✅ Verify bot functionality in Discord
- ✅ Test key slash commands
- ✅ Monitor logs for any issues
- ✅ Confirm all features are working

### Troubleshooting:
- 📊 Check the enhanced health verification output
- 🔍 Review file count and structure logs
- 🤖 Verify Discord API connectivity
- 💾 Confirm system resources are adequate

## Comparison with Other Workflows

| Workflow | Use Case | Speed | Risk | Recovery |
|----------|----------|--------|------|----------|
| **Standard Deploy** | Regular updates | Fast | Low | Automatic |
| **Full Redeploy** | Clean refresh | Slow | Medium | Manual |
| **Force Redeploy Script** | Quick restart | Medium | Low | Automatic |
| **VM Reboot** | Infrastructure issues | Medium | High | Manual |

## Support

If you encounter issues with the Full Redeploy workflow:

1. **Check the Actions logs** for detailed error information
2. **Review the log collection phase** for system status
3. **Consider VM reboot** if infrastructure issues are suspected
4. **Use standard deploy** for routine updates

Remember: Full Redeploy is a powerful tool for complete refresh, but use it judiciously as it's more resource-intensive than incremental deployments.