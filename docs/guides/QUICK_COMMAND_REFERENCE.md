# Red Legion Bot - Quick Command Reference

This document provides a comprehensive reference for all available commands in the Red Legion Discord Bot.

## 📋 Table of Contents
- [General Commands](#general-commands)
- [Mining Commands](#mining-commands)
- [Event Management](#event-management)
- [Market Commands](#market-commands)
- [Loan System](#loan-system)
- [Recruitment System](#recruitment-system)
- [Cache & Diagnostics](#cache--diagnostics)
- [Administrative Commands](#administrative-commands)
- [Permission Levels](#permission-levels)

---

## 🔧 General Commands

### `/redping`
**Description:** Test bot responsiveness and check latency  
**Usage:** `/redping`  
**Permissions:** Anyone  
**Response:** Shows bot latency and online status

---

## ⛏️ Mining Commands

### `/redsundayminingstart`
**Description:** Start a Sunday mining session with voice tracking  
**Usage:** `/redsundayminingstart`  
**Permissions:** Organization members  
**Features:**
- Creates database event for tracking
- Starts voice channel monitoring across 7 mining channels
- Bot joins Dispatch/Main channel as visual indicator
- Tracks participant join/leave times
- Generates session ID and event ID for reference

### `/redsundayminingstop` 
**Description:** Stop the current Sunday mining session  
**Usage:** `/redsundayminingstop`  
**Permissions:** Organization members  
**Features:**
- Ends voice tracking for all channels
- Displays complete participant summary with time breakdown
- Shows session duration and participant count
- Prepares data for payroll calculation
- Bot leaves all voice channels

### `/redpayroll`
**Description:** Calculate and manage Sunday mining payroll distribution  
**Usage:** `/redpayroll [action]`  
**Permissions:** Admin/OrgLeaders only  
**Options:**
- `Calculate Payroll` - Calculate earnings distribution with modal form
- `View Participation Summary` - Show participation statistics
- `Show Current Ore Prices` - Display live UEX market prices with best locations

**Features:**
- Interactive ore amount input form with current market prices
- Real-time UEX price integration with location data
- Participation-based profit sharing calculations
- PDF report generation for record keeping
- Voice time tracking integration
- Cached price data for performance

### `/redpricecheck`
**Description:** Check live ore prices and best selling locations from UEX API  
**Usage:** `/redpricecheck [category]`  
**Permissions:** Anyone  
**Options:**
- `ores` - Mineable ores (default)
- `all` - All commodities  
- `high_value` - High value commodities only

**Features:**
- Live UEX market data with location information
- Shows highest price per SCU and best selling location
- Cached data for improved performance
- Clean formatting with commodity indicators
- Price statistics and market overview

### `/redsundayminingtest`
**Description:** Run diagnostics for Sunday Mining voice channel issues  
**Usage:** `/redsundayminingtest [test_type]`  
**Permissions:** Admin only  
**Options:**
- `all` - Run all diagnostic tests
- `database` - Database schema validation
- `voice` - Voice channel connectivity tests
- `permissions` - Bot permission checks
- `connection` - Voice connection tests
- `guild` - Guild configuration validation

---

## 📅 Event Management

### `/redevents`
**Description:** Complete event management system using subcommands  
**Permissions:** Various (see individual commands)

#### `/redevents create`
**Usage:** `/redevents create [category] [name] [description]`  
**Permissions:** Organization members  
**Categories:** Mining Operations, Combat Training, Flight Training, Salvage Operations, Exploration, Miscellaneous

#### `/redevents list`
**Usage:** `/redevents list [category] [status]`  
**Permissions:** Anyone  
**Features:** Filter by category and status, shows up to 10 events with pagination

#### `/redevents view`
**Usage:** `/redevents view [event_id]`  
**Permissions:** Anyone  
**Features:** Detailed event information including organizer and timing

#### `/redevents delete`
**Usage:** `/redevents delete [event_id]`  
**Permissions:** Admin only  
**Features:** Confirmation dialog, removes event and participation records

---

## 🏪 Market Commands

### `/redmarket`
**Description:** Organization marketplace system using subcommands  
**Permissions:** Organization members

#### `/redmarket list`
**Usage:** `/redmarket list [category] [sort]`  
**Features:** Browse all marketplace listings with filtering and sorting

#### `/redmarket add`
**Usage:** `/redmarket add [item] [price] [details]`  
**Features:** Add new items to marketplace with descriptions

---

## 💰 Loan System

### `/redloans`
**Description:** Complete loan management system using subcommands  
**Permissions:** Organization members

#### `/redloans request`
**Usage:** `/redloans request [amount] [purpose] [repayment_plan]`  
**Features:** Request organization loans with detailed applications

#### `/redloans status`
**Usage:** `/redloans status`  
**Features:** Check your current loan status and details

#### `/redloans approve` / `/redloans deny`
**Usage:** `/redloans approve [request_id]` or `/redloans deny [request_id]`  
**Permissions:** Finance officers  
**Features:** Process loan applications with notifications

---

## 👥 Recruitment System

### `/redjoin`
**Description:** Organization recruitment and application system  
**Permissions:** Various (see individual commands)

#### `/redjoin apply`
**Usage:** `/redjoin apply [position]`  
**Features:** Submit application to join Red Legion organization

#### `/redjoin status`
**Usage:** `/redjoin status`  
**Features:** Check your application status and progress

#### `/redjoin review`
**Usage:** `/redjoin review [application_id]`  
**Permissions:** Officers  
**Features:** Review and process member applications

---

## 🗄️ Cache & Diagnostics

### `/redcachestatus`
**Description:** Show UEX cache status and statistics  
**Usage:** `/redcachestatus`  
**Permissions:** Anyone  
**Features:**
- Cache hit/miss statistics
- Data freshness indicators
- Performance metrics
- Auto-refresh status

### `/redcacherefresh`
**Description:** Force refresh of UEX cache data  
**Usage:** `/redcacherefresh`  
**Permissions:** Anyone  
**Features:** Manual cache refresh with progress feedback

### `/redcacheclear`
**Description:** Clear all cached data  
**Usage:** `/redcacheclear`  
**Permissions:** Admin only  
**Features:** Complete cache reset for troubleshooting

### `/redhealth`
**Description:** Simple health check for bot monitoring  
**Usage:** `/redhealth`  
**Permissions:** Anyone  
**Features:** Quick status check with uptime and basic metrics

### `/redtest`
**Description:** Comprehensive bot health and system status  
**Usage:** `/redtest`  
**Permissions:** Anyone  
**Features:**
- **🤖 Bot Status**: Online status, uptime, guilds, total members
- **💻 System Resources**: Memory usage, CPU usage, process status  
- **🗄️ Services**: Database connectivity, Discord API status, voice tracking
- **📊 Performance**: Latency, command responsiveness, event status
- **🧪 Function Tests**: Guild access, voice channels count, user permissions
- **Enhanced Display**: Professional embed with comprehensive diagnostics

### `/reddbtest`
**Description:** Test database connectivity and operations  
**Usage:** `/reddbtest`  
**Permissions:** Admin only  
**Features:**
- Database connection validation
- Query performance testing
- Connection pool status
- Schema validation

### `/redconfig`
**Description:** Check bot configuration status  
**Usage:** `/redconfig`  
**Permissions:** Admin only  
**Features:**
- Configuration validation
- Environment variable status
- Secret Manager connectivity

---

## ⚙️ Administrative Commands

### `/redconfigrefresh`
**Description:** Refresh bot configuration from Secret Manager  
**Usage:** `/redconfigrefresh`  
**Permissions:** Admin only  
**Features:**
- Reloads configuration from Google Cloud Secret Manager
- Updates database URLs and tokens
- Validates new configuration

### `/redrestart`
**Description:** Restart the bot process  
**Usage:** `/redrestart`  
**Permissions:** Admin only  
**Features:**
- Graceful bot restart
- Logs restart activity
- Preserves session data

### `/redlistminingchannels`
**Description:** List all configured mining channels  
**Usage:** `/redlistminingchannels`  
**Permissions:** Admin only  
**Features:**
- Shows all tracked mining channels
- Displays channel configurations
- Guild-specific channel management

### `/redsyncommands`
**Description:** Force sync Discord slash commands  
**Usage:** `/redsyncommands`  
**Permissions:** Admin only  
**Features:**
- Manually sync commands with Discord
- Useful after bot updates
- Shows sync results

### `/redtestmining`
**Description:** Manage test data for bot testing  
**Usage:** `/redtestmining [action]`  
**Permissions:** Admin only  
**Options:**
- `create` - Create comprehensive test data
- `show` - Display current test data
- `delete` - Remove all test data (requires confirmation)

**Test Data Created:**
- Multiple mining events (past, current, future)
- Participation records across all 7 mining channels
- Test participants with varying participation times
- Realistic mining scenarios for testing

---

## 🔐 Permission Levels

### **Anyone**
- Basic commands available to all Discord users
- Diagnostic and health check commands
- Price checking and cache status
- No organization membership required

### **Organization Members**
- Users with the Red Legion organization role
- Mining, event, market, and loan commands
- Most bot functionality available

### **OrgLeaders**
- Organization leadership role
- Payroll calculation access
- Event management privileges

### **Admin**
- Full bot administration access
- Configuration management
- Cache management
- Test data operations
- Bot restart capabilities

---

## 📊 Mining System Details

### **Enhanced Voice Tracking**
- Automatic participant detection in 7 configured channels
- Real-time join/leave timestamp recording
- Multi-channel session tracking with channel switching support
- Participation time calculation with 30-second minimum
- Integration with payroll system
- Bot visual presence in Dispatch channel during active sessions

### **Advanced Payroll Calculation**
- Time-based participation shares across all channels
- Live UEX market price integration with location data
- Interactive ore amount input with current market prices
- Automated profit distribution calculations
- PDF report generation with detailed breakdowns
- Cached price data for improved performance

### **UEX API Integration**
- Real-time market price data with auto-refresh every 4 minutes
- Best selling location information for all commodities
- Cached data with TTL for performance optimization
- Manual refresh capabilities
- Comprehensive price statistics and market overview

### **Configured Mining Channels**
```
Dispatch/Main: 1385774416755163247
Alpha: 1386367354753257583
Bravo: 1386367395643449414
Charlie: 1386367464279478313
Delta: 1386368182421635224
Echo: 1386368221877272616
Foxtrot: 1386368253712375828
```

---

## 🚀 Quick Start Guide

1. **Health Check:** `/redhealth` - Verify bot is operational
2. **Price Check:** `/redpricecheck ores` - View current market prices
3. **Start Mining:** `/redsundayminingstart` - Begin tracking session
4. **Check Cache:** `/redcachestatus` - View API cache status  
5. **Calculate Payroll:** `/redpayroll calculate` - Process earnings (OrgLeaders+)
6. **Stop Mining:** `/redsundayminingstop` - End session and view summary

---

## 🔧 CI/CD Integration

### **GitHub Actions Workflows**
- **Test Workflow**: Runs on PR creation, adds `Tests Good` and `Ready To Deploy` labels on success
- **Deploy Workflow**: Triggers when `deploy` label is added to PR with `Ready To Deploy` label
- **Merge Workflow**: Handles PR merging after successful deployment

### **Deployment Process**
1. Create PR → Tests run automatically
2. Tests pass → `Tests Good` and `Ready To Deploy` labels added
3. Add `deploy` label → Full codebase deployment triggered  
4. Deployment success → `ready to merge` label added
5. Add `merge` label → PR merged to main branch

---

## 📝 Current System Status

- **Database**: PostgreSQL v2.0.0 with modern architecture
- **Voice Tracking**: Enhanced multi-channel support with bot presence indicators
- **API Integration**: UEX Corp market data with intelligent caching
- **Event Management**: Complete subcommand group system
- **Deployment**: Full codebase deployment with Ansible automation
- **Testing**: Comprehensive offline and online test suites
- **Documentation**: Updated command references and deployment guides

---

**Last Updated**: December 2024  
**Bot Version**: v2.0.0 Enhanced Mining System  
**Database Version**: v2.0.0 Modern PostgreSQL Architecture

For detailed development guides, see the `/docs/development/` folder.