# 🧪 Red Legion Bot Testing Guide

## Test Data Management & End-to-End Testing

This guide covers the complete testing workflow for the Red Legion Discord Bot, including test data management, mining system testing, and validation procedures.

---

## 📋 Table of Contents

1. [Test Data Management](#test-data-management)
2. [End-to-End Testing Workflow](#end-to-end-testing-workflow)
3. [Mining System Testing](#mining-system-testing)
4. [Validation & Cleanup](#validation--cleanup)
5. [Troubleshooting](#troubleshooting)

---

## 🎯 Test Data Management

### **`/testdata` Command Overview**

The `/testdata` command provides comprehensive test data management for the Red Legion mining system.

#### **Command Options:**

| Action | Description | What It Does |
|--------|-------------|--------------|
| `create` | **Create Full Test Dataset** | Populates database with realistic mining events, participants, and channels |
| `show` | **Show Current Test Data** | Displays overview of existing test data in the system |
| `cleanup` | **Clean Up All Test Data** | Safely removes all test data while preserving real operational data |

#### **Permissions Required:**
- ✅ **Administrator** role in Discord server
- ✅ **Database write access** 

---

### **Create Test Data (`/testdata create`)**

#### **What Gets Created:**

##### **🎤 Mining Channels**
```
• Mining Alpha   (ID: 111111111111111111)
• Mining Beta    (ID: 222222222222222222)  
• Mining Gamma   (ID: 333333333333333333)
• Mining Delta   (ID: 444444444444444444)
```

##### **📅 Mining Events**
- **Event 1**: Open/Active session (today)
  - Status: `OPEN` 
  - Participants: ~10 members
  - Payroll: Not calculated

- **Event 2**: Completed session (1 week ago)
  - Status: `CLOSED`
  - Participants: ~8 members
  - Payroll: ✅ Calculated (1,500,000 aUEC)
  - PDF: ✅ Generated

- **Event 3**: Payroll complete, PDF pending (2 weeks ago)
  - Status: `CLOSED`
  - Participants: ~12 members  
  - Payroll: ✅ Calculated (2,100,000 aUEC)
  - PDF: ❌ Pending

##### **👥 Test Participants**

**Red Legion Members (Org = True, 1.5x payroll multiplier):**
- CommanderSteel
- MinerMax42
- QuantumQueen
- RockCrusher_RL
- AsteroidAce
- OreMaster_RedLegion
- DigDeepDan
- CrystalHunter88

**Guest Miners (Org = False, 1.0x payroll multiplier):**
- GuestMiner_1
- NewbiePilot
- TrialMember_99
- FriendOfLegion

##### **⏱️ Participation Records**
- **Realistic durations**: 30 minutes to 3 hours per session
- **Channel switching**: Members join multiple channels
- **Varied participation**: Different activity levels per event
- **Org status weighting**: Proper payroll multiplier testing

#### **Expected Response:**
```
✅ Test Data Created Successfully
Complete test dataset has been generated for mining system testing

📊 Created Data
• 3 mining events
• 75+ participation records  
• 4 mining channels

🎯 Event States
• 1 OPEN event (current session)
• 1 COMPLETED event (with payroll & PDF)
• 1 PAYROLL DONE event (missing PDF)

🚀 Ready for Testing
You can now test:
• /mining session commands
• /mining payroll calculations
• Event lifecycle management
• PDF generation workflow
```

---

### **Show Test Data (`/testdata show`)**

Displays current test data status including:
- 📊 **Event count** and status breakdown
- 👥 **Participant count** across all events
- 🎤 **Channel count** and configuration
- 📈 **Recent activity** summary

#### **Sample Output:**
```
📊 Test Data Overview
Guild: Red Legion Test Server

📅 Events (Last 10)
┌─────────────┬──────────────┬─────────────┬────────────┬─────────┐
│ Date        │ Participants │ Payout      │ Status     │ PDF     │
├─────────────┼──────────────┼─────────────┼────────────┼─────────┤
│ 2025-09-06  │ 10           │ Pending     │ OPEN       │ ❌      │
│ 2025-08-30  │ 8            │ 1,500,000   │ CLOSED     │ ✅      │
│ 2025-08-23  │ 12           │ 2,100,000   │ CLOSED     │ ❌      │
└─────────────┴──────────────┴─────────────┴────────────┴─────────┘

👥 Participants: 85 total records
🎤 Channels: 4 configured mining channels
```

---

### **Cleanup Test Data (`/testdata cleanup`)**

#### **What Gets Deleted:**
- ✅ **Test events**: All events with test participants
- ✅ **Test participation**: All associated participation records
- ✅ **Test channels**: Mining channels created by test script
- ✅ **Test market items**: Sample market entries (if any)
- ✅ **Test loans**: Sample loan records (if any)

#### **What's Preserved:**
- ✅ **Real operational data**: Production mining events
- ✅ **Channel configuration**: Your hardcoded channel IDs in `SUNDAY_MINING_CHANNELS_FALLBACK`
- ✅ **User data**: Real Discord member records
- ✅ **Bot configuration**: Settings and permissions

#### **Safety Features:**
- 🔒 **Pattern matching**: Only deletes records with test identifiers
- 🔒 **Guild isolation**: Only affects current Discord server
- 🔒 **Foreign key handling**: Proper deletion order to maintain referential integrity
- 🔒 **Rollback on error**: Database transaction protection

---

## 🚀 End-to-End Testing Workflow

### **Phase 1: Environment Setup**

#### **1.1 Prerequisites**
```bash
# Verify bot configuration
cd /Users/jt/Devops/red-legion/red-legion-bots

# Check validation tests
python3 tests/test_validation.py

# Expected: 5/5 tests passed
```

#### **1.2 Database Preparation**
```bash
# Start with clean test environment
/testdata cleanup    # Clear any existing test data
/testdata create     # Generate fresh test dataset
/testdata show       # Verify test data creation
```

#### **1.3 Channel Verification**
```bash
# Verify your mining channels are configured
/list_mining_channels

# Expected: Shows your 7 channels from SUNDAY_MINING_CHANNELS_FALLBACK:
# - dispatch: 1385774416755163247
# - alpha: 1386367354753257583
# - bravo: 1386367395643449414
# - charlie: 1386367464279478313
# - delta: 1386368182421635224
# - echo: 1386368221877272616
# - foxtrot: 1386368253712375828
```

---

### **Phase 2: Basic System Testing**

#### **2.1 Health Checks**
```bash
# Basic connectivity
/ping                 # Expected: Response time < 100ms

# System health
/health_check         # Expected: All systems ✅

# Database connectivity  
/dbtest_command       # Expected: Database connection OK

# Configuration validation
/config_check         # Expected: All settings valid
```

#### **2.2 Admin Function Testing**
```bash
# Channel management
/add_mining_channel #test-channel Test Channel Description
/list_mining_channels  # Verify addition
/remove_mining_channel #test-channel  # Clean up
```

---

### **Phase 3: Mining System Testing**

#### **3.1 Session Lifecycle Testing**

##### **Start Mining Session**
```bash
/sunday_mining_start
```

**Expected Bot Behavior:**
- ✅ Creates database event record
- ✅ Joins all 7 mining voice channels
- ✅ Activates voice state tracking
- ✅ Displays success embed with session details

**Verification Steps:**
1. **Visual confirmation**: Bot appears in all mining voice channels
2. **Database check**: New event record created with `is_open = TRUE`
3. **Tracking active**: Voice join/leave events being recorded

##### **Simulate Mining Activity**
1. **Join mining channels**: Have test users join/leave voice channels
2. **Channel switching**: Test members moving between mining channels
3. **Duration tracking**: Verify accurate time recording
4. **Org status**: Test with both org members and guests

**What's Being Tracked:**
- ⏱️ **Join/leave timestamps**: Precise timing of voice state changes
- 🎤 **Channel attribution**: Which channels members spent time in
- 👥 **Member identification**: Discord IDs and display names
- 🏢 **Org membership**: Role-based org member detection
- 🔄 **Channel switching**: Multiple channel sessions per member

##### **Stop Mining Session**
```bash
/sunday_mining_stop
```

**Expected Bot Behavior:**
- ✅ Bot leaves all mining voice channels
- ✅ Stops voice state tracking
- ✅ Flushes remaining participation data to database
- ✅ Provides session summary

**Verification Steps:**
1. **Voice channels empty**: Bot no longer present in channels
2. **Data persistence**: All participation records saved to database
3. **Session summary**: Accurate duration and participant count

#### **3.2 Payroll Calculation Testing**

##### **Basic Payroll Flow**
```bash
/payroll calculate
```

**Process Flow:**
1. **Permission check**: Verifies Admin/OrgLeaders role
2. **Event selection**: Shows recent mining events
3. **UEX API call**: Fetches current ore prices
4. **Modal presentation**: Payroll calculation interface

##### **Payroll Modal Testing**

**Test Scenario 1: Automatic Calculation**
```
Input Ore Data: "Quantainium: 50, Laranite: 100, Gold: 75"
Expected: Auto-calculation using UEX API prices
```

**Test Scenario 2: Manual Value Entry**
```
Input Total Value: "2500000"
Expected: Uses manual value, bypasses ore calculation
```

**Test Scenario 3: Mixed Ore Types**
```
Input: "Quantainium: 25.5, InvalidOre: 50, Beryl: 100"
Expected: Processes valid ores, ignores invalid types
```

##### **Payroll Distribution Verification**

**Expected Calculations:**
- **Org Members**: Base time × 1.5 multiplier
- **Non-Org Members**: Base time × 1.0 multiplier
- **Proportional payout**: Based on weighted participation time
- **Database updates**: Event closed, payroll marked complete

**Sample Calculation:**
```
Member A (Org): 2 hours × 1.5 = 3.0 weighted hours
Member B (Guest): 2 hours × 1.0 = 2.0 weighted hours
Total weighted: 5.0 hours
Total value: 2,500,000 aUEC

Member A payout: (3.0/5.0) × 2,500,000 = 1,500,000 aUEC
Member B payout: (2.0/5.0) × 2,500,000 = 1,000,000 aUEC
```

#### **3.3 Event Management Testing**

##### **Event Status Checking**
```bash
/list_open_events     # Shows active mining sessions
```

**Expected Results:**
- ✅ Current open events with participant counts
- ✅ Event duration and status
- ✅ Recent activity summary

##### **Winner Selection Testing**
```bash
/pick_winner "Sunday Mining Test"
```

**Process Verification:**
- ✅ Queries recent event participants
- ✅ Applies org member weighting (1.5x chance)
- ✅ Random selection with bias toward org members
- ✅ Records winner selection in database

---

### **Phase 4: Advanced Testing Scenarios**

#### **4.1 Multi-User Concurrent Testing**

**Setup**: 5+ test users simultaneously
**Actions**:
1. All users join different mining channels
2. Users switch channels multiple times
3. Some users leave and rejoin
4. Stop session and calculate payroll

**Validation**:
- ✅ All participation accurately tracked
- ✅ No lost or duplicate records
- ✅ Correct payroll distribution
- ✅ Database consistency maintained

#### **4.2 Error Handling Testing**

**Database Connection Loss**
```bash
# Simulate database outage during active session
# Expected: Bot continues functioning, data buffered
```

**UEX API Failure**
```bash
# Test payroll calculation when UEX API is down
# Expected: Manual value entry still works
```

**Permission Denial**
```bash
# Test restricted commands as regular user
# Expected: Access denied with helpful error message
```

**Invalid Input Handling**
```bash
# Test malformed ore data in payroll modal
# Expected: Graceful error handling, user feedback
```

#### **4.3 Performance Testing**

**Large Session Testing**
- **Duration**: 4+ hour mining session
- **Participants**: 15+ concurrent users
- **Channel switching**: Frequent movement between channels
- **Validation**: Accurate tracking, no performance degradation

**Rapid Join/Leave Testing**
- **Pattern**: Users rapidly joining/leaving channels
- **Duration**: Sub-30-second sessions
- **Validation**: Minimum duration filtering, no spam records

---

### **Phase 5: Market & Loan System Testing**

#### **5.1 Market System**
```bash
# Add market items
/add_market_item "Quantainium Ore" 25000 50

# List market
/list_market

# Expected: Formatted market display with prices and stock
```

#### **5.2 Loan System**
```bash
# Request loan
/request_loan 1000000 "2025-12-31"

# Expected: Loan record created with due date tracking
```

---

### **Phase 6: Data Validation & Reporting**

#### **6.1 Database Integrity Checks**

**Participation Data Validation**
```sql
-- Check for orphaned participation records
SELECT COUNT(*) FROM mining_participation mp 
LEFT JOIN events e ON mp.event_id = e.id 
WHERE e.id IS NULL;

-- Expected: 0 orphaned records
```

**Event Consistency Validation**
```sql
-- Verify participant counts match
SELECT e.id, e.total_participants, COUNT(mp.id) as actual_participants
FROM events e 
LEFT JOIN mining_participation mp ON e.id = mp.event_id 
GROUP BY e.id, e.total_participants
HAVING e.total_participants != COUNT(mp.id);

-- Expected: No mismatches
```

#### **6.2 Payroll Accuracy Verification**

**Manual Calculation Check**
1. Export participation data for test event
2. Calculate weighted hours manually
3. Compare with bot-generated payroll
4. Verify within 1 aUEC accuracy

---

## 🧹 Validation & Cleanup

### **Post-Testing Validation**

#### **System State Check**
```bash
# Verify no active sessions
/sunday_mining_start  # Should show no active session

# Check test data status
/testdata show        # Review what was created/modified

# Validate channel configuration  
/list_mining_channels # Ensure channels match expectations
```

#### **Performance Metrics**
- ⚡ **Response times**: All commands < 3 seconds
- 💾 **Memory usage**: No memory leaks during extended testing
- 🔄 **Database connections**: Proper connection pooling
- 📊 **Data accuracy**: 100% participation tracking accuracy

### **Cleanup Procedures**

#### **Test Data Cleanup**
```bash
# Remove all test data
/testdata cleanup

# Verify cleanup
/testdata show        # Should show minimal/no test data
/list_open_events     # Should show no test events
```

#### **Channel Configuration Reset**
```bash
# Remove any test channels added during testing
/remove_mining_channel <test_channel_id>

# Verify final configuration matches production needs
/list_mining_channels
```

---

## 🔧 Troubleshooting

### **Common Issues & Solutions**

#### **Bot Not Joining Voice Channels**
```
Issue: Bot doesn't appear in mining channels after /sunday_mining_start
Solutions:
1. Check bot voice permissions in channels
2. Verify channel IDs in SUNDAY_MINING_CHANNELS_FALLBACK
3. Check bot connection status
4. Review error logs in terminal
```

#### **Participation Not Recording**
```
Issue: Users joining voice channels but no participation records
Solutions:
1. Verify mining session is active (/sunday_mining_start)
2. Check if channels are in tracked list (/list_mining_channels)
3. Ensure minimum duration threshold met (30+ seconds)
4. Verify database connectivity (/dbtest_command)
```

#### **Payroll Calculation Errors**
```
Issue: /payroll calculate fails or shows incorrect amounts
Solutions:
1. Check UEX API connectivity (network/bearer token)
2. Verify event has participation data
3. Validate ore input format (OreType: Amount, OreType: Amount)
4. Check for sufficient admin permissions
```

#### **Test Data Issues**
```
Issue: /testdata create fails or shows errors
Solutions:
1. Verify database write permissions
2. Check for existing data conflicts
3. Ensure sufficient database storage
4. Review foreign key constraints
```

### **Debug Information**

#### **Useful Commands for Debugging**
```bash
# System status
/health_check         # Overall system health
/config_check         # Configuration validation
/dbtest_command       # Database connectivity

# Data inspection
/testdata show        # Current test data status
/list_open_events     # Active sessions
/list_mining_channels # Channel configuration
```

#### **Log File Locations**
```bash
# Bot console output (when running locally)
python3 src/main.py

# Check for error patterns:
# - Database connection failures
# - Discord API rate limiting  
# - Voice channel permission issues
# - UEX API timeouts
```

---

## 📈 Success Criteria

### **Testing Complete When:**

- ✅ **All commands respond** within acceptable time limits
- ✅ **Voice tracking works** accurately across all mining channels
- ✅ **Payroll calculations** are mathematically correct
- ✅ **Database integrity** maintained throughout testing
- ✅ **Error handling** gracefully manages edge cases
- ✅ **Test data cleanup** restores system to production state
- ✅ **Performance metrics** meet operational requirements

### **Ready for Production When:**

- ✅ **End-to-end workflow** completes successfully
- ✅ **Multi-user testing** shows no conflicts or data loss
- ✅ **Extended session testing** demonstrates stability
- ✅ **Error recovery** handles network/database issues
- ✅ **Security validation** confirms proper permission enforcement
- ✅ **Documentation** covers all operational procedures

---

## 🎯 Quick Testing Checklist

```bash
# Phase 1: Setup
[ ] /testdata cleanup
[ ] /testdata create
[ ] /list_mining_channels

# Phase 2: Basic Functions  
[ ] /ping
[ ] /health_check
[ ] /dbtest_command

# Phase 3: Mining Session
[ ] /sunday_mining_start
[ ] Join/leave voice channels (test participation tracking)
[ ] /sunday_mining_stop
[ ] /payroll calculate

# Phase 4: Validation
[ ] /list_open_events
[ ] /testdata show
[ ] Verify database records

# Phase 5: Cleanup
[ ] /testdata cleanup
[ ] Final system check
```

---

**🎉 Happy Testing!** 

This comprehensive testing approach ensures the Red Legion Bot performs reliably under all operational conditions. For additional support or questions about specific testing scenarios, refer to the individual command documentation or consult the development team.
