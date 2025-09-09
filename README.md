# Red Legion Discord Bot

A comprehensive Discord bot for managing Sunday mining operations, voice tracking, payroll calculations, and community management for the Red Legion organization.

## 📚 Documentation

All documentation has been organized into the **[docs/](docs/)** folder with logical categories:

- **[📖 Complete Documentation Index](docs/INDEX.md)** - Organized access to all guides and references
- **[⛏️ Sunday Mining Operations Guide](docs/guides/SUNDAY_MINING_OPERATIONS.md)** - How mining operations and payroll work
- **[🚀 Quick Command Reference](docs/guides/QUICK_COMMAND_REFERENCE.md)** - All bot commands and usage
- **[🔧 Troubleshooting Guide](docs/troubleshooting/TROUBLESHOOTING_FIXES.md)** - Common issues and solutions

## ✨ Key Features

- **Sunday Mining Management**: Automated voice tracking and payroll calculations
- **Voice Participation Tracking**: Real-time tracking across multiple channels
- **UEX API Integration**: Live ore price data for accurate payroll
- **Administrative Commands**: Comprehensive server management tools
- **Modular Architecture**: Clean, maintainable codebase

## ⛏️ Sunday Mining System Workflow

### Starting a Mining Session
1. **`/redsundayminingstart`** - Creates database event and begins voice tracking
   - Automatically creates a mining event in the database with unique session ID
   - Activates voice participation tracking across all configured mining channels
   - Sets event status to 'active' for later payroll processing

### During Mining Operations
- Players join mining voice channels → Participation automatically tracked
- Bot monitors join/leave times and calculates duration
- All participation data linked to the active mining event

### Ending a Session
2. **`/redsundayminingstop`** - Stops tracking and shows session summary
   - Ends voice tracking across all channels
   - Displays participation summary with total miners and duration
   - Prompts payroll officer to use `/redpayroll calculate`

### Processing Payroll
3. **`/redpayroll calculate`** - Select event and calculate earnings distribution
   - Shows dropdown of available open/active mining events
   - Payroll officer selects the specific event to process
   - Auto-fetches current UEX ore prices for accurate calculations
   - Officer enters total ore amounts (SCU) → System auto-calculates total value
   - Generates payroll distribution based on participation time and org membership

## 🚀 Quick Start

1. **Installation**: See [Deployment Documentation](documentation/deployment/)
2. **Configuration**: Review configuration guides in [Development](documentation/development/)
3. **Commands**: Check [Quick Command Reference](documentation/guides/QUICK_COMMAND_REFERENCE.md)

## 🏗️ Project Structure

```text
red-legion-bots/
├── documentation/           # 📚 All documentation organized by category
│   ├── admin/              # Administrative guides
│   ├── architecture/       # System architecture docs
│   ├── deployment/         # Deployment and infrastructure
│   ├── development/        # Development guides and workflows
│   ├── features/           # Feature documentation
│   ├── guides/             # User guides and references
│   └── troubleshooting/    # Issues and solutions
├── src/                    # 🤖 Bot source code
│   ├── bot/               # Bot client and utilities
│   ├── commands/          # Command modules (mining, admin, etc.)
│   ├── config/            # Configuration management
│   ├── database/          # Database operations
│   ├── handlers/          # Event handlers (voice, core)
│   └── utils/             # Utility functions
├── tests/                 # 🧪 Test suite
├── scripts/               # 🔧 Utility scripts
└── ansible/               # 🚀 Deployment automation
```

## 📖 Support & Development

- **Documentation**: [Complete Documentation Index](documentation/INDEX.md)
- **Issues**: Create issues in this repository
- **Contributing**: See [Development Guidelines](documentation/development/)
- **Architecture**: Review [Architecture Documentation](documentation/architecture/)

---

*This bot is actively maintained and developed for the Red Legion organization in Star Citizen.*
