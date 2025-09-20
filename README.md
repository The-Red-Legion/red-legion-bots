# 🤖 Red Legion Discord Bot

> **⚠️ ARCHITECTURE UPDATE**: This bot now integrates with the [Red Legion Management Portal](../red-legion-management-portal) for user-facing operations. Most Discord commands have been deprecated in favor of a superior web interface. The bot retains core voice tracking and API functionality.

## What is this Bot?

The Red Legion Discord Bot is an **automated operations manager** for Star Citizen organizations. It eliminates manual administrative work by automatically tracking member participation, calculating fair payouts, and managing events.

**In Simple Terms**: 
- Members join voice channels during operations (mining, combat, etc.)
- The bot tracks who participated and for how long
- It automatically calculates fair earnings based on participation time
- Leaders get detailed reports and can distribute payouts instantly

**Core Purpose**: Replace spreadsheets, manual timekeeping, and disputed payouts with transparent, automated systems that build trust and fairness in your organization.

## 🚀 Core Features

### 📊 **Automated Sunday Mining Operations**
The bot's flagship feature - complete automation for mining sessions:

- **🎤 Voice Channel Tracking**: Automatically tracks who participates and for how long in 7 dedicated mining channels
- **💰 Smart Payroll System**: Calculates fair earnings distribution based on participation time
- **🎁 Voluntary Donation System**: Members can choose to donate earnings to help fellow miners
- **💎 Live UEX Corp Price Data**: Real-time ore prices with best selling locations
- **📋 Prefixed Event IDs**: Unique tracking IDs like `sm-a7k2m9` for each mining session
- **👥 Live Member Display**: Shows who's currently in each mining channel when sessions start
- **🤖 Visual Session Status**: Bot joins dispatch channel to indicate active tracking

**How it Works**: Start session → Members join voice channels → Bot tracks participation → Calculate payroll with real prices → Distribute earnings fairly

### 🎮 **Star Citizen Game Integration** 
- **🔍 Commodity Price Checking**: Live pricing for all 19 mineable ores from UEX Corp API
- **📈 Market Intelligence**: Compare prices across different star systems and locations  
- **⚡ Smart Caching**: 24-hour refresh cycles aligned with game data updates
- **🔄 Force Refresh**: Override cache when needed for immediate price updates

### 🏛️ **Organization Management Tools**
- **👑 Role-Based Permissions**: Admin and OrgLeader access controls for sensitive operations
- **🗃️ Member Database**: Complete participation history and statistics tracking
- **📅 Multi-Event Support**: Mining, combat, training, social events with category-specific IDs
- **📊 Analytics Dashboard**: Performance insights and participation metrics

### 🧪 **Testing & Diagnostics Suite**
- **🔧 Built-in Health Checks**: Comprehensive system diagnostics for troubleshooting
- **🧪 Test Data Generation**: Create realistic scenarios for training and validation
- **📊 Performance Monitoring**: Track bot health, database connectivity, and API status
- **🛠️ Admin Tools**: Database validation, schema checks, and migration status

## 👥 Benefits by Role

### **For Organization Leaders:**
- **Zero Administrative Overhead**: No more manual calculations or disputes over fair distribution
- **Complete Transparency**: See exactly who contributes and how much with detailed analytics
- **Multi-Operation Management**: Track mining, combat, training events simultaneously
- **Real-time Operations Dashboard**: Monitor active sessions as they happen

### **For Members:**
- **Guaranteed Fair Pay**: Earnings automatically calculated based on actual participation time
- **Full Transparency**: See exactly how payroll is calculated and distributed  
- **Effortless Participation**: Just join voice channels - the bot handles everything else
- **Community Support**: Voluntarily donate earnings to help fellow organization members

### **For Payroll Officers:**
- **Instant Report Generation**: Complete payroll calculations with one command
- **Price Flexibility**: Edit ore prices if needed before final distribution
- **Enhanced Reporting**: Clear breakdown showing base pay plus donation bonuses
- **Guided Workflow**: Step-by-step process from event selection to final payout

## 📱 Quick Start Guide

### **🎯 Sunday Mining Session (5 Simple Steps)**
1. **Start**: `/redsundayminingstart` - Bot shows current channel members and creates event ID like `sm-a7k2m9`
2. **Mine**: Members join voice channels and participate normally - bot tracks automatically
3. **Calculate**: `/redpayroll calculate` - Select your event, set donations, review prices
4. **Distribute**: Bot generates fair payroll based on participation time and current ore values
5. **Done**: Members get transparent breakdown of earnings and any donation bonuses

### **🔍 Essential Commands**
| Command | Purpose | Example |
|---------|---------|---------|
| `/redpricecheck ores` | Current ore prices with best locations | All 19 mineable ores |
| `/redpricerefresh` | Force update price cache | Override 24-hour cache |
| `/redeventdiagnostics` | System health check | Database, API, channels |
| `/redtestmining create` | Generate test data | Training and validation |

### **💡 Pro Tips**
- Bot joins dispatch channel when tracking is active (visual confirmation)
- Events get unique prefixed IDs: `sm-` (mining), `op-` (operations), `tr-` (training)
- Donation system is completely voluntary - no pressure on members
- All calculations are transparent with detailed breakdowns

## ✅ What's Ready Now

**Core Systems (Production Ready)**:
- 🎤 **Voice Channel Tracking** - Automatic participation monitoring across 7 mining channels
- 💰 **Smart Payroll System** - Fair distribution based on participation time with donation support
- 💎 **Live UEX Corp Integration** - Real-time ore prices with 19+ commodities and location data
- 📋 **Event Management** - Prefixed IDs (`sm-a7k2m9`), creation, tracking, and analytics
- 🔒 **Security & Permissions** - Role-based access with Admin/OrgLeader controls
- 🧪 **Testing & Diagnostics** - Comprehensive health checks and test data generation

**Advanced Features (Enhanced v2.0)**:
- 🎁 **Voluntary Donation System** - Members can share earnings with automatic redistribution
- ✏️ **Editable Pricing** - Adjust ore values during payroll calculation as needed
- 📊 **Interactive UI** - Discord buttons, modals, and multi-step workflows
- 🏷️ **Smart Event IDs** - Category prefixes for mining, operations, training, social events
- 📈 **Real-time Analytics** - Live participation tracking with detailed member statistics

## 🚀 Future Expansions

**On the Roadmap:**
- ⚔️ **Military Operations Tracking** - Combat missions with after-action reports  
- 🎓 **Training Program Management** - Structured learning paths and certifications
- 🏆 **Achievement System** - Recognition for top contributors and milestones
- 📊 **Advanced Analytics** - Deep insights into member performance and trends
- 🎮 **Direct Game Integration** - When Star Citizen APIs become available

*The foundation is built - the possibilities are endless.*

---

## 🎯 Why Choose Red Legion Bot?

**Built for Star Citizen Organizations That Value:**

✅ **Fairness** - Transparent, automated systems eliminate favoritism and disputes  
✅ **Community** - Tools that bring members together and encourage participation  
✅ **Efficiency** - Automation reduces administrative overhead dramatically  
✅ **Growth** - Data and insights help organizations improve and expand  
✅ **Reliability** - Robust systems that work consistently when you need them

## 🎉 Ready to Transform Your Organization?

**Getting started is simple:**

1. **🎤 Members join voice channels** during operations (just like normal)
2. **🤖 Bot handles everything automatically** - tracking, calculations, reporting
3. **💰 Everyone gets fair compensation** based on transparent participation metrics
4. **📈 Your organization grows stronger** with better tools and happier members

**The Red Legion Bot eliminates the spreadsheets, disputes, and administrative headaches** - so you can focus on what matters: building an amazing Star Citizen community.

*Where technology meets community in the Star Citizen universe.* ⭐

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