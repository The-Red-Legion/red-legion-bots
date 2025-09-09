# Red Legion Discord Bot Documentation

Welcome to the Red Legion Discord Bot documentation! This bot is designed specifically for Star Citizen organizations to manage mining operations, events, loans, and member recruitment.

## 📁 Documentation Structure

### 🚀 [Getting Started](./guides/)
- [Quick Command Reference](./guides/QUICK_COMMAND_REFERENCE.md)
- Setup and installation guides

### 🏗️ [Architecture](./architecture/)
- System architecture overview
- Database design
- [Reorganization Summary](./architecture/REORGANIZATION_SUMMARY.md)

### 🔧 [Development](./development/)
- [Testing Guide](./development/TESTING_GUIDE.md)
- [Code Audit Report](./development/CODE_AUDIT_REPORT.md)
- [Workflow Updates](./development/WORKFLOW_UPDATES.md)
- Development plans and status

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

### ⛏️ Mining Operations
- Automated Sunday mining sessions
- Voice channel participation tracking
- Real-time payroll calculations
- UEX API integration for ore prices

### 📅 Event Management
- Create and manage mining events
- Track participant attendance
- Automated event scheduling

### 💰 Financial System
- Member loan management
- Marketplace for trading
- Automated payroll distribution

### 👥 Organization Management
- Member recruitment system
- Application processing
- Role management

## 🎮 Available Commands

### Subcommand Groups
- `/redevents` - Event management (create, list, view, delete)
- `/redmarket` - Marketplace system (list, add items)
- `/redloans` - Loan management (request, status)
- `/redjoin` - Organization recruitment (apply, status)

### Individual Commands
- `/redping` - Test bot responsiveness
- `/redhealth` - Health diagnostics
- `/redsundayminingstart` - Start mining session
- `/redpayroll` - Calculate and distribute payroll

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