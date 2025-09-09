# Red Legion Discord Bot Documentation

Welcome to the Red Legion Discord Bot documentation! This bot is designed specifically for Star Citizen organizations to manage mining operations, events, loans, and member recruitment.

## 📁 Documentation Structure

### 🚀 [Getting Started](./guides/)
- [Quick Command Reference](./guides/QUICK_COMMAND_REFERENCE.md)
- Setup and installation guides

### 🔧 [Development](./development/)
- [Testing Guide](./development/TESTING_GUIDE.md)
- [Code Audit Report](./development/CODE_AUDIT_REPORT.md)
- [Workflow Updates](./development/WORKFLOW_UPDATES.md)
- [Verification Checklist](./development/VERIFICATION_CHECKLIST.md)
- Development procedures and validation

### 🚢 [Deployment](./deployment/)
- [Ansible Deployment](./deployment/ansible-deployment.md)
- [Infrastructure Migration](./deployment/INFRASTRUCTURE_MIGRATION.md)

### 🔍 [Troubleshooting](./troubleshooting/)
- [Troubleshooting Fixes](./troubleshooting/TROUBLESHOOTING_FIXES.md)
- Common issues and solutions

### 💡 [Features](./features/)
- [Slash Command Conversion](./features/slash-command-conversion.md)
- [Enhanced Mining System](./features/ENHANCED_MINING_SYSTEM.md)
- [Voice Tracking Enhancement](./features/VOICE_TRACKING_ENHANCEMENT.md)
- [Adhoc Mining Sessions](./features/adhoc-mining-sessions.md)

## 🤖 Bot Features

### ⛏️ Enhanced Mining Operations
- **Multi-Channel Voice Tracking**: Automatic participant detection across 7 mining channels
- **Smart Session Management**: Start/stop mining sessions with comprehensive participant summaries
- **Advanced Payroll System**: Time-based profit sharing with UEX market integration
- **Real-Time Price Data**: Live ore prices with best selling locations and intelligent caching
- **PDF Report Generation**: Automated payroll reports with detailed breakdowns
- **Visual Indicators**: Bot joins Dispatch channel during active sessions

### 📅 Comprehensive Event Management
- **Multi-Category Events**: Mining, Combat, Training, Salvage, Exploration events
- **Event Lifecycle**: Create, view, list, and delete with proper permission controls
- **Participant Tracking**: Integration with voice tracking for attendance
- **Filtering & Search**: Advanced event discovery with category and status filters

### 💰 Advanced Financial System
- **Loan Management**: Complete request, approval, and tracking system
- **Marketplace Integration**: Item listing and trading system
- **Automated Calculations**: Participation-based payroll distribution
- **Multi-Role Access**: Different permission levels for various financial operations

### 👥 Professional Recruitment System
- **Application Processing**: Streamlined member application workflow
- **Review System**: Officer tools for application management
- **Status Tracking**: Real-time application status updates
- **Integration**: Seamless connection with Discord role management

### 🗄️ Performance & Reliability
- **Intelligent Caching**: UEX API data cached with auto-refresh (4-minute intervals)
- **Comprehensive Diagnostics**: Multi-level health checks and system monitoring
- **Database v2.0.0**: Modern PostgreSQL architecture with proper relationships
- **CI/CD Integration**: GitHub Actions with automated testing and deployment

## 🎮 Available Commands

### Core Mining System
- `/redsundayminingstart` - Start mining session with voice tracking
- `/redsundayminingstop` - Stop mining session with participant summary
- `/redpayroll` - Calculate and distribute payroll with UEX integration
- `/redpricecheck` - Check live ore prices and best selling locations

### Subcommand Groups
- `/redevents` - Event management (create, list, view, delete)
- `/redmarket` - Marketplace system (list, add items)
- `/redloans` - Loan management (request, status, approve/deny)
- `/redjoin` - Organization recruitment (apply, status, review)

### Cache & Diagnostics
- `/redcachestatus` - UEX API cache status and statistics
- `/redcacherefresh` - Force refresh cached market data
- `/redhealth` - Simple health check
- `/redtest` - Comprehensive system diagnostics
- `/redping` - Test bot responsiveness

### Administrative Tools
- `/redconfigrefresh` - Refresh bot configuration
- `/redsyncommands` - Sync slash commands
- `/redtestmining` - Test data management
- `/redsundayminingtest` - Mining system diagnostics

## 📊 System Requirements

- Python 3.9+
- PostgreSQL database
- Google Cloud Platform (for production)
- Discord Bot Token with appropriate permissions

## 🛠️ Development

See the [Development](./development/) section for:
- Setting up development environment
- Running tests
- Contributing guidelines
- Code style and standards

## 📞 Support

For issues and support, check the [Troubleshooting](./troubleshooting/) section or contact the development team.