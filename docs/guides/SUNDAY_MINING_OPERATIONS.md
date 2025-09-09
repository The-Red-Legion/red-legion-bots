# Sunday Mining Operations Guide

## 🎯 Overview

The Red Legion Sunday Mining Operation is a collaborative mining session where org members work together across multiple mining channels and receive **equal pay distribution** based on participation time. This guide explains how the system works and how payments are calculated.

## ⛏️ How Sunday Mining Works

### **Step-by-Step Process**

1. **Session Start** - A leader uses `/redsundayminingstart`
   - Bot joins **Dispatch/Main** channel as visual indicator
   - Voice tracking begins across all 7 mining channels
   - Mining event is created in database

2. **Mining Operations** - Participants join voice channels
   - Voice tracking monitors participation across all channels
   - Participants can switch between channels freely
   - Minimum 30 seconds participation required for payment
   - System tracks total time spent across all channels

3. **Session End** - Leader uses `/redsundayminingstop`
   - Voice tracking ends, bot leaves channels
   - Participant summary is displayed
   - Session data is finalized for payroll

4. **Payroll Calculation** - Officer uses `/redpayroll calculate`
   - Enter total ore amounts collected
   - System calculates value using live UEX market prices
   - **Equal distribution** to all participants based on time
   - PDF report generated for records

## 💰 Payment System

### **Equal Pay Distribution**
- **All participants receive equal pay per hour** - no distinction between org members and guests
- Payment is **purely time-based**: `Individual Payout = (Your Time / Total Time) × Total Value`
- **Multi-channel support**: Time across all mining channels is aggregated
- **Fair switching**: No penalty for moving between mining areas

### **Example Calculation**
```
Total Mining Value: 1,000,000 aUEC
Total Participant Time: 10 hours

Participant A: 2 hours → 200,000 aUEC (20%)
Participant B: 3 hours → 300,000 aUEC (30%) 
Participant C: 5 hours → 500,000 aUEC (50%)
```

### **Payment Requirements**
- ✅ Minimum 30 seconds voice channel participation
- ✅ Must be present during active mining session
- ✅ Time is automatically tracked across all 7 mining channels
- ✅ No manual time entry required

## 🎤 Monitored Voice Channels

The system tracks participation across **7 mining channels**:

| Channel | Purpose | Channel ID |
|---------|---------|------------|
| **Dispatch/Main** | Coordination & Bot Indicator | `1385774416755163247` |
| **Alpha** | Mining Team 1 | `1386367354753257583` |
| **Bravo** | Mining Team 2 | `1386367395643449414` |
| **Charlie** | Mining Team 3 | `1386367464279478313` |
| **Delta** | Mining Team 4 | `1386368182421635224` |
| **Echo** | Mining Team 5 | `1386368221877272616` |
| **Foxtrot** | Mining Team 6 | `1386368253712375828` |

### **Channel Usage Patterns**
- **Dispatch/Main**: Coordination, logistics, refinery operations
- **Alpha-Foxtrot**: Active mining operations in different areas
- **Multi-Channel Operations**: Participants commonly switch between dispatch and mining channels
- **Total Time Tracking**: All time across channels is combined for fair payment

## 🤖 Bot Features

### **Visual Indicators**
- ✅ **Bot in Dispatch**: Confirms active mining session
- ✅ **Real-time Tracking**: Automatic join/leave detection
- ✅ **Session Summaries**: Complete participation breakdown

### **Advanced Tracking**
- **Channel Switching Support**: No lost time when moving between channels
- **Primary Channel Detection**: System identifies where most time was spent
- **Session Data**: Comprehensive participation analytics
- **Minimum Time Filter**: 30-second threshold prevents spam participation

## 💡 UEX Market Integration

### **Live Price Data**
- **Real-time Pricing**: Current market rates for all 21 ore types
- **Best Locations**: Shows where to sell each ore for maximum profit
- **Auto-calculation**: Payroll system automatically calculates ore values
- **4-minute Cache**: Intelligent caching for performance with auto-refresh

### **Ore Price Features**
- Use `/redpricecheck ores` to see current market prices
- Payroll modal shows live prices during calculation
- System uses highest available prices for fair valuation
- Location data helps optimize selling decisions

## 👥 Roles and Permissions

### **Anyone Can**
- View current ore prices (`/redpricecheck`)
- Check mining session status
- Participate in mining operations (voice tracking automatic)

### **Org Members Can**
- Start mining sessions (`/redsundayminingstart`)
- Stop mining sessions (`/redsundayminingstop`)
- View session summaries

### **OrgLeaders/Payroll Officers Can**
- Calculate payroll (`/redpayroll calculate`)
- View participation summaries (`/redpayroll summary`)
- Generate PDF reports
- Manage payroll distribution

### **Administrators Can**
- Manage mining channels (`/redlistminingchannels`)
- Run diagnostics (`/redsundayminingtest`)
- Access system configuration

## 📊 Participation Data

### **What Gets Tracked**
- **Join/Leave Times**: Precise timestamps for all channel activity
- **Total Duration**: Combined time across all mining channels
- **Primary Channel**: Channel where most time was spent
- **Session Association**: Links participation to specific mining events
- **Valid Participation**: Filters out very short visits (<30 seconds)

### **What Participants See**
- Real-time session status when bot joins Dispatch
- Complete participation summary when session ends
- Individual time breakdown across channels
- Payment calculations based on participation

## 🎮 Command Reference

### **Session Management**
```
/redsundayminingstart    # Start mining session (Org Members)
/redsundayminingstop     # End session with summary (Org Members)
```

### **Payroll Operations**
```
/redpayroll calculate    # Calculate and distribute payments (Officers)
/redpayroll summary      # View participation without calculating (Officers)
/redpayroll prices       # Show current ore prices with locations (Officers)
```

### **Information Commands**
```
/redpricecheck ores      # Current ore prices and best locations (Anyone)
/redhealth               # Bot status check (Anyone)
/redsundayminingtest     # Mining system diagnostics (Admin)
```

## ❓ Frequently Asked Questions

### **Q: Do org members get paid more than guests?**
**A: No.** All participants receive **equal pay per hour** regardless of org membership status. Payment is purely time-based.

### **Q: What if I switch between mining channels?**
**A: No problem.** The system tracks your time across **all channels** and combines it for payment calculation. You can freely move between Dispatch, Alpha, Bravo, etc.

### **Q: How long do I need to participate to get paid?**
**A: Minimum 30 seconds.** Very short visits are filtered out, but any meaningful participation (30+ seconds) qualifies for payment.

### **Q: How are ore values determined?**
**A: Live UEX market prices.** The system uses current market rates with 4-minute refresh intervals to ensure fair and accurate valuations.

### **Q: Can I see my participation time?**
**A: Yes.** When the session ends with `/redsundayminingstop`, you'll see a complete summary of all participants and their time breakdown.

### **Q: What if I'm in multiple channels at once?**
**A: Not possible.** Discord only allows one voice channel at a time. The system tracks when you switch between channels and aggregates all your time.

### **Q: How do I know if a session is active?**
**A: Look for the bot in Dispatch/Main channel.** When the bot is present in the Dispatch channel, it means voice tracking is active.

## 🚀 Best Practices

### **For Participants**
- Join voice channels during active mining operations
- Stay connected for meaningful participation periods
- Switch channels as needed for mining operations
- Check bot presence in Dispatch to confirm active session

### **For Session Leaders**
- Start sessions with `/redsundayminingstart` before operations begin
- Ensure bot joins Dispatch channel as confirmation
- End sessions with `/redsundayminingstop` when operations complete
- Review participant summary for completeness

### **For Payroll Officers**
- Use `/redpayroll prices` to check current market rates
- Calculate payroll promptly after session completion
- Review participation data before calculating payments
- Generate PDF reports for organization records

## 🔧 Technical Details

### **Voice Tracking System**
- **Multi-channel monitoring** across 7 configured channels
- **Real-time join/leave detection** with precise timestamps
- **Session-based aggregation** for comprehensive time tracking
- **Database persistence** with PostgreSQL v2.0.0 architecture

### **Market Price Integration**
- **UEX Corp API** integration with bearer token authentication
- **4-minute intelligent caching** with automatic refresh
- **21 ore types** with real-time pricing data
- **Location optimization** showing best selling locations

### **Payment Calculation**
- **Time-based distribution** with equal pay per hour
- **Automatic ore valuation** using live market prices
- **PDF report generation** with detailed breakdowns
- **Multi-channel aggregation** for fair time calculation

---

**Last Updated**: December 2024  
**System Version**: v2.0.0 Enhanced Mining System  

*This guide reflects the current Sunday Mining operation as implemented in the Red Legion Discord Bot v2.0.0 with enhanced multi-channel tracking and UEX market integration.*