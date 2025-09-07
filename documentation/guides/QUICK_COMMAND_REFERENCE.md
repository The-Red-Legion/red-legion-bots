# Red Legion Bot - Quick Command Reference

This document provides a comprehensive reference for all available commands in the Red Legion Discord Bot.

## 📋 Table of Contents
- [General Commands](#general-commands)
- [Mining Commands](#mining-commands)
- [Event Management](#event-management)
- [Market Commands](#market-commands)
- [Loan System](#loan-system)
- [Diagnostic Commands](#diagnostic-commands)
- [Administrative Commands](#administrative-commands)
- [Permission Levels](#permission-levels)

---

## 🔧 General Commands

### `/ping`
**Description:** Test bot responsiveness and check latency  
**Usage:** `/ping`  
**Permissions:** Anyone  
**Response:** Shows bot latency and online status

---

## ⛏️ Mining Commands

### `/sunday_mining_start`
**Description:** Start a Sunday mining session with voice tracking  
**Usage:** `/sunday_mining_start`  
**Permissions:** Organization members  
**Features:**
- Creates database event for tracking
- Starts voice channel monitoring
- Tracks participant join/leave times
- Generates session ID for reference

### `/sunday_mining_stop` 
**Description:** Stop the current Sunday mining session  
**Usage:** `/sunday_mining_stop`  
**Permissions:** Organization members  
**Features:**
- Ends voice tracking
- Finalizes participation records
- Prepares data for payroll calculation

### `/payroll`
**Description:** Calculate and manage Sunday mining payroll distribution  
**Usage:** `/payroll [action]`  
**Permissions:** Admin/OrgLeaders only  
**Options:**
- `Calculate Payroll` - Calculate earnings distribution with modal form
- `View Participation Summary` - Show participation statistics
- `Show Current Ore Prices` - Display live UEX market prices

**Features:**
- Interactive ore amount input form
- Real-time UEX price integration
- Participation-based profit sharing
- PDF report generation
- Voice time tracking integration

### `/log_mining_results` (Legacy)
**Description:** Log mining results for a specific event  
**Usage:** `/log_mining_results [event_id]`  
**Permissions:** Organization members  
**Note:** Legacy command, use new Sunday Mining system instead

---

## 📅 Event Management

### `/start_logging`
**Description:** Start logging participation for current voice channel  
**Usage:** `/start_logging`  
**Permissions:** Organization members  
**Features:**
- Tracks voice channel participants
- Records join/leave timestamps
- Creates event in database

### `/stop_logging`
**Description:** Stop logging participation for current voice channel  
**Usage:** `/stop_logging`  
**Permissions:** Organization members  
**Features:**
- Finalizes participation tracking
- Calculates total participation time

### `/pick_winner`
**Description:** Pick a random winner from current voice channel participants  
**Usage:** `/pick_winner`  
**Permissions:** Organization members  
**Features:**
- Random selection from active participants
- Fair winner selection system

### `/list_open_events`
**Description:** List all currently open/active events  
**Usage:** `/list_open_events`  
**Permissions:** Organization members  
**Features:**
- Shows active events
- Displays participant counts
- Event status information

---

## 🏪 Market Commands

### `/list_market`
**Description:** Display all items available in the organization market  
**Usage:** `/list_market`  
**Permissions:** Organization members  
**Features:**
- Shows item names and prices
- Displays available stock
- Organized display format

### `/add_market_item`
**Description:** Add a new item to the organization market  
**Usage:** `/add_market_item [name] [price] [stock]`  
**Permissions:** Organization members  
**Parameters:**
- `name` - Item name
- `price` - Price in credits
- `stock` - Available quantity
**Features:**
- Adds items to market database
- Validates input parameters

---

## 💰 Loan System

### `/request_loan`
**Description:** Request a loan from the organization  
**Usage:** `/request_loan [amount]`  
**Permissions:** Organization members  
**Parameters:**
- `amount` - Loan amount in credits (max 1,000,000)
**Features:**
- Validates loan amounts
- Calculates loan terms
- Records loan in database
- Automatic repayment tracking

---

## 🔍 Diagnostic Commands

### `/health`
**Description:** Check bot health and system status  
**Usage:** `/health`  
**Permissions:** Anyone  
**Information Displayed:**
- Bot uptime
- Guild count
- Memory usage
- System status

### `/test`
**Description:** Comprehensive bot health and connectivity test  
**Usage:** `/test`  
**Permissions:** Anyone  
**Features:**
- Complete system diagnostics
- Database connectivity check
- Discord API status
- Memory and CPU usage
- Guild and member statistics

### `/dbtest`
**Description:** Test database connectivity and operations  
**Usage:** `/dbtest`  
**Permissions:** Anyone  
**Features:**
- Database connection validation
- Basic query testing
- Connection pool status

### `/config_check`
**Description:** Verify bot configuration and settings  
**Usage:** `/config_check`  
**Permissions:** Anyone  
**Features:**
- Configuration validation
- Environment variable status
- Secret Manager connectivity

---

## ⚙️ Administrative Commands

### `/refresh_config`
**Description:** Refresh bot configuration from Secret Manager  
**Usage:** `/refresh_config`  
**Permissions:** Admin only  
**Features:**
- Reloads configuration from Google Cloud Secret Manager
- Updates database URLs and tokens
- Validates new configuration

### `/restart_red_legion_bot`
**Description:** Restart the bot process  
**Usage:** `/restart_red_legion_bot`  
**Permissions:** Admin only  
**Features:**
- Graceful bot restart
- Logs restart activity
- Preserves session data

### `/add_mining_channel`
**Description:** Add a voice channel to Sunday mining tracking  
**Usage:** `/add_mining_channel [channel] [description]`  
**Permissions:** Admin only  
**Parameters:**
- `channel` - Voice channel to add
- `description` - Optional channel description
**Features:**
- Configures channels for mining tracking
- Guild-specific channel management

### `/remove_mining_channel`
**Description:** Remove a voice channel from Sunday mining tracking  
**Usage:** `/remove_mining_channel [channel]`  
**Permissions:** Admin only  
**Parameters:**
- `channel` - Voice channel to remove

### `/list_mining_channels`
**Description:** List all configured mining channels  
**Usage:** `/list_mining_channels`  
**Permissions:** Admin only  
**Features:**
- Shows all tracked mining channels
- Displays channel configurations

### `/testdata`
**Description:** Manage test data for bot testing  
**Usage:** `/testdata [action]`  
**Permissions:** Admin only  
**Options:**
- `create` - Create comprehensive test data
- `show` - Display current test data
- `cleanup` - Remove all test data

**Test Data Created:**
- 3 mining events (Past Sunday, Current Session, Future Event)
- 75+ participation records across 7 channels
- Test participants with varying participation times
- Realistic mining scenarios for testing

---

## 🔐 Permission Levels

### **Anyone**
- Basic commands available to all Discord users
- Diagnostic and health check commands
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
- Channel management
- Test data operations
- Bot restart capabilities

---

## 📊 Mining System Details

### **Voice Tracking**
- Automatic participant detection in configured channels
- Real-time join/leave timestamp recording
- Participation time calculation
- Integration with payroll system

### **Payroll Calculation**
- Time-based participation shares
- UEX market price integration
- Interactive ore amount input
- Automated profit distribution
- PDF report generation

### **Configured Mining Channels**
```
Dispatch: 1385774416755163247
Alpha: 1386367354753257583
Bravo: 1386367395643449414
Charlie: 1386367464279478313
Delta: 1386368182421635224
Echo: 1386368221877272616
Foxtrot: 1386368253712375828
```

---

## 🚀 Quick Start for Testing

1. **Health Check:** `/health` - Verify bot is operational
2. **Start Mining:** `/sunday_mining_start` - Begin tracking session
3. **Test Data:** `/testdata create` - Generate test scenarios (Admin)
4. **Check Events:** `/list_open_events` - View active events
5. **Calculate Payroll:** `/payroll` - Process earnings (OrgLeaders+)
6. **Stop Mining:** `/sunday_mining_stop` - End session

---

## 📝 Notes

- All commands support Discord's slash command interface
- Commands with parameters show autocomplete where applicable
- Error handling provides detailed feedback for troubleshooting
- All mining data is persistently stored in PostgreSQL database
- Real-time integration with UEX market API for pricing
- PDF reports automatically generated for payroll calculations

For detailed testing procedures, see `TESTING_GUIDE.md`.
