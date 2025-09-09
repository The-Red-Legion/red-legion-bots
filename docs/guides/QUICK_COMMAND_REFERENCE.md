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
**Description:** Start a Sunday mining session with enhanced voice tracking and database integration  
**Usage:** `/redsundayminingstart`  
**Permissions:** Organization members  
**Features:**
- Creates database event with prefixed Event ID (sm-YYYYMMDD-HHMMSS format)
- Starts real-time voice channel monitoring across all 7 configured mining channels
- Bot joins Dispatch/Main channel as visual activity indicator
- Tracks participant join/leave timestamps with 30-second minimum participation
- Enhanced member listing showing current voice channel occupancy
- Database event integration for seamless payroll calculation workflow
- Automatic channel detection for Dispatch/Main channel (supports both naming conventions)
- Comprehensive error reporting with specific channel ID validation

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
**Description:** Enhanced payroll calculation and management system with donation support  
**Usage:** `/redpayroll [action]`  
**Permissions:** Admin/OrgLeaders only  
**Options:**
- `Calculate Payroll` - Multi-step enhanced payroll calculation with donation system
- `View Participation Summary` - Show detailed participation statistics and time breakdown
- `Show Current Ore Prices` - Display live UEX market prices with consistent location data

**Enhanced Payroll Features:**
- **Step 1: Event Selection** - Choose from available Sunday Mining events with prefixed IDs (sm-)
- **Step 2: Donation Selection** - Interactive participant donation system allowing voluntary earnings donation
- **Step 3: Price Configuration** - Editable UEX ore prices with real-time market data integration
- **Step 4: Final Calculation** - Complete profit distribution with donation tracking and detailed breakdowns

**Advanced Features:**
- Participation-based time-weighted profit sharing calculations
- Voluntary donation system where participants can donate earnings back to organization
- Real-time UEX price integration with manual override capabilities
- PDF report generation with donation tracking and detailed participant breakdowns
- Voice channel time tracking integration across all 7 mining channels
- Cached price data with 24-hour refresh cycle for optimal performance
- Event ID prefix system integration (sm- for Sunday Mining events)

### `/redpricecheck`
**Description:** Check live ore prices and best selling locations from UEX API  
**Usage:** `/redpricecheck [category]`  
**Permissions:** Anyone  
**Options:**
- `ores` - Mineable ores (default) - Shows all 19 configured ore types
- `all` - All commodities  
- `high_value` - High value commodities only

**Features:**
- Live UEX market data with highest available prices
- Shows all configured mineable ores (Quantainium, Gold, Iron, etc.)
- Cached data updated every 24 hours for performance
- Clean formatting with commodity indicators and price statistics
- Displays UEX highest price information
- Comprehensive ore coverage including high, mid, and low value ores

### `/redpricerefresh`
**Description:** Force refresh UEX price data immediately bypassing 24-hour cache  
**Usage:** `/redpricerefresh [category]`  
**Permissions:** Admin/OrgLeaders only  
**Options:**
- `ores` - Refresh mineable ores (default)
- `all` - Refresh all commodities  
- `high_value` - Refresh high value commodities only

**Features:**
- Overrides normal 24-hour cache refresh cycle
- Shows before/after cache statistics
- Displays sample of updated prices after successful refresh  
- Detailed status reporting with cache age and validity
- Essential for getting fresh prices before payroll calculations
- Permission-controlled to prevent API abuse

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

### `/redeventdiagnostics`
**Description:** Comprehensive event system diagnostics and troubleshooting  
**Usage:** `/redeventdiagnostics`  
**Permissions:** Admin only  
**Features:**
- Complete database schema validation and table structure analysis
- Event ID system testing with prefix validation
- Database connection and query performance testing
- Mining channel configuration verification
- Voice channel accessibility and permission checks
- Event creation and management system testing
- Detailed error reporting with actionable troubleshooting steps
- Schema compatibility detection (integer vs VARCHAR event_id handling)
- Mining event history analysis and validation

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
**Description:** Manage test data for bot testing and development  
**Usage:** `/redtestmining [action]`  
**Permissions:** Admin only  
**Options:**
- `create` - Create comprehensive test data with prefixed event IDs
- `show` - Display current test data and event summary
- `delete` - Remove all test data with confirmation dialog

**Test Data Features:**
- Multiple mining events with proper prefixed IDs (sm-, op-, tr-, etc.)
- Participation records across all 7 configured mining channels  
- Test participants with realistic varying participation times (30s-3hrs)
- Complete mining scenarios including past, current, and future events
- Database schema compatibility testing for both integer and VARCHAR event_id
- Voice channel participation tracking simulation
- Payroll calculation test scenarios with multiple participant combinations

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