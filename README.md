# 🤖 Red Legion Discord Bot

**The ultimate companion for Star Citizen organizations - streamlining operations, tracking participation, and building stronger communities.**

## 🌟 What is the Red Legion Bot?

The Red Legion Bot is a sophisticated Discord assistant designed specifically for Star Citizen organizations. Think of it as your organization's digital operations officer - it automatically tracks member participation, calculates fair payouts, manages events, and provides real-time game data to help your org operate more efficiently and fairly.

Whether you're running Sunday mining operations, organizing military missions, or planning social events, the Red Legion Bot handles the tedious administrative work so your members can focus on having fun and achieving your organization's goals.

## 🎯 What Does the Bot Do?

### 📊 **Sunday Mining Operations**
The bot's flagship feature is comprehensive Sunday Mining management:

- **🎤 Voice Channel Tracking**: Automatically tracks who participates and for how long
- **💰 Smart Payroll System**: Calculates fair earnings distribution based on participation time
- **🎁 Donation System**: Members can voluntarily donate their earnings to help others
- **💎 Live Price Data**: Pulls real-time ore prices from UEX Corp for accurate calculations
- **📋 Event Management**: Creates and tracks mining events with unique IDs (e.g., `sm-a7k2m9`)
- **👥 Member Listing**: Shows who's currently in each mining channel when sessions start
- **🤖 Visual Indicators**: Bot joins the dispatch channel to show when tracking is active

### 🎮 **Game Data Integration** 
- **🔍 Ore Price Checking**: Real-time Star Citizen commodity prices from UEX Corp
- **📈 Market Analysis**: Compare prices across different locations and ores
- **⚡ Smart Caching**: Efficient data retrieval that updates every 24 hours

### 🏛️ **Organization Management**
- **👑 Role-Based Access**: Admin and OrgLeader permissions for sensitive operations
- **🗃️ Member Database**: Tracks member participation history and statistics
- **📅 Event System**: Support for multiple event types with organized tracking

### 🧪 **Testing & Diagnostics**
- **🔧 Built-in Diagnostics**: Troubleshoot issues with comprehensive system checks
- **🧪 Test Data Creation**: Generate realistic test scenarios for training and validation
- **📊 Performance Monitoring**: Track bot health and database connectivity

## 🚀 Key Features & Capabilities

### **For Organization Leaders:**
- **Automated Payroll**: No more manual calculations or disputes over fair distribution
- **Participation Tracking**: See exactly who contributes and how much
- **Event Organization**: Plan and track multiple concurrent operations
- **Real-time Oversight**: Monitor active operations as they happen

### **For Members:**
- **Fair Compensation**: Earnings automatically calculated based on actual participation
- **Transparency**: See exactly how payroll is calculated and distributed  
- **Easy Participation**: Just join voice channels - the bot handles the rest
- **Donation Options**: Voluntarily share earnings with fellow org members

### **For Payroll Officers:**
- **One-Click Calculations**: Generate complete payroll reports instantly
- **Editable Pricing**: Adjust ore prices if needed before final distribution
- **Enhanced Reports**: Clear breakdown of base pay plus donation bonuses
- **Multi-Step Workflow**: Guided process from event selection to final payout

## 📱 How to Use the Bot

### **Starting a Sunday Mining Session:**
1. Run `/redsundayminingstart` 
2. Bot shows who's currently in each channel
3. Look for the bot in the dispatch channel (confirms tracking is active)
4. Members join voice channels and participate normally
5. Bot automatically tracks participation time

### **Calculating Payroll:**
1. Payroll officer runs `/redpayroll calculate`
2. Select which mining event to process
3. Choose members who want to donate earnings (optional)
4. Review/edit ore prices if needed
5. Enter total ore amounts collected
6. Bot calculates and displays final distribution

### **Getting Current Prices:**
- `/redpricecheck ores` - See all ore prices
- `/redpricecheck high_value` - High-value ores only
- `/redpricecheck all` - Complete commodity list

### **Testing & Diagnostics:**
- `/redeventdiagnostics` - Check event creation and database
- `/redtestmining create` - Generate test data for training
- `/reddiagnostics` - Comprehensive system health check

## 🏗️ Current Capabilities

### ✅ **Fully Operational:**
- ✅ Sunday Mining session management with voice tracking
- ✅ Automated payroll calculation with donation support
- ✅ Real-time UEX Corp price integration
- ✅ Event creation and management (with prefixed IDs)
- ✅ Member participation database
- ✅ Comprehensive diagnostics and testing tools
- ✅ Role-based permission system
- ✅ Enhanced UI with interactive Discord components

### 🔧 **Advanced Features:**
- ✅ Multi-step payroll workflow with donation redistribution
- ✅ Editable ore pricing during payroll calculation  
- ✅ Smart event ID system (`sm-` for mining, `op-` for operations, etc.)
- ✅ Real-time channel member display
- ✅ Automatic database event creation and tracking
- ✅ Flexible database schema support

## 🌈 Future Possibilities

### 🎯 **Planned Enhancements:**
- **📊 Advanced Analytics**: Detailed member performance reports and trends
- **🏆 Achievement System**: Recognize top contributors and milestones
- **📱 Mobile Integration**: Discord bot optimizations for mobile users
- **🔔 Smart Notifications**: Automated reminders for events and activities
- **💼 Multi-Event Support**: Simultaneous tracking of different operation types

### 🚀 **Potential Expansions:**
- **⚔️ Military Operations**: Combat mission tracking and after-action reports
- **🎓 Training Programs**: Structured learning paths and certification tracking
- **🏟️ Tournament Management**: Competition brackets and scoring systems
- **🗺️ Exploration Tracking**: Discovery logging and territory mapping
- **💰 Treasury Management**: Organization fund tracking and budget allocation
- **📈 Market Intelligence**: Predictive pricing and trade route optimization

### 🔮 **Advanced Integrations:**
- **🎮 Star Citizen API**: Direct game integration when available
- **📊 Business Intelligence**: Advanced reporting and data visualization
- **🤖 AI Assistant**: Natural language queries for data and operations
- **🌐 Web Dashboard**: Browser-based control panel for detailed management
- **📱 Custom Apps**: Dedicated mobile applications for org management

## 🛡️ Built for Organizations

The Red Legion Bot is specifically designed for Star Citizen organizations that value:

- **⚖️ Fairness**: Transparent, automated systems that eliminate favoritism
- **🤝 Community**: Tools that bring members together and encourage participation  
- **⚡ Efficiency**: Automation that reduces administrative overhead
- **📊 Growth**: Data and insights that help organizations improve and expand
- **🔒 Reliability**: Robust systems that work consistently when you need them

Whether you're a small mining collective or a large multi-division organization, the Red Legion Bot scales to meet your needs while maintaining the personal touch that makes Star Citizen communities special.

## 🎉 Getting Started

Ready to revolutionize your organization's operations? The Red Legion Bot is designed to be intuitive for all users:

1. **🎤 Join Voice Channels**: Participate in operations normally
2. **📊 Let the Bot Work**: Automatic tracking happens in the background  
3. **💰 Enjoy Fair Payouts**: Transparent, automated compensation
4. **📈 Watch Your Org Grow**: Better tools lead to stronger communities

*The Red Legion Bot - Where technology meets community in the Star Citizen universe.* ⭐

---

## 📚 Technical Documentation

For administrators and developers who need detailed technical information:

- **[📖 Complete Documentation Index](docs/INDEX.md)** - Organized access to all guides and references
- **[⛏️ Sunday Mining Operations Guide](docs/guides/SUNDAY_MINING_OPERATIONS.md)** - Technical workflow details
- **[🚀 Quick Command Reference](docs/guides/QUICK_COMMAND_REFERENCE.md)** - All bot commands and usage
- **[🔧 Troubleshooting Guide](docs/troubleshooting/TROUBLESHOOTING_FIXES.md)** - Common issues and solutions

## 🏗️ Project Structure

```text
red-legion-bots/
├── docs/                    # 📚 All documentation organized by category
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

## 📞 Support & Questions
For technical support or feature requests, contact your organization's administrators or check the bot's diagnostic commands for troubleshooting common issues.

## 🔧 Version Information
Current version includes Sunday Mining operations, payroll management, UEX price integration, and comprehensive event tracking with ongoing enhancements for expanded organizational management.

---

*This bot is actively maintained and developed for the Red Legion organization in Star Citizen.*