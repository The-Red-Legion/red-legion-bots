# 💰 Payroll System Workflow Documentation

> **Red Legion Mining Bot - Complete Payroll Calculation Process**

## 🎯 Overview

The payroll system uses a modern 5-step workflow (including Step 2.5 Custom Pricing) with Discord UI components to calculate fair profit distribution based on participation time and user preferences.

---

## 🔄 Complete Workflow Visualization

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                       MINING PAYROLL WORKFLOW v3.0                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘

    User Types: /payroll calculate
              │
              ▼
┌─────────────────────────────────┐
│       SYSTEM INITIALIZATION     │
│                                 │
│ • Check permissions            │
│ • Query database for events   │
│ • Filter completed events     │
│ • Count pending calculations  │
└─────────────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────┐
        │   Events Found?  │
        └─────────┬───────┘
                  │
         ┌────────┴────────┐
         │ NO              │ YES
         ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│  "No Events"    │  │  Continue to    │
│   Message       │  │   Step 1        │
└─────────────────┘  └─────────┬───────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              STEP 1: EVENT SELECTION                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                        EVENT SELECTION DROPDOWN                             │    │
│  │                                                                             │    │
│  │  📅 sm-12345 - Sunday Mining Session (Sep 10, 2025)                       │    │
│  │     👥 15 participants • ⏱️ 3.2 hours • 📍 Daymar                          │    │
│  │                                                                             │    │
│  │  📅 sm-67890 - Weekend Mining Op (Sep 9, 2025)                            │    │
│  │     👥 22 participants • ⏱️ 4.1 hours • 📍 Lyria                           │    │
│  │                                                                             │    │
│  │  📅 sm-11111 - Mining Training (Sep 8, 2025)                              │    │
│  │     👥 8 participants • ⏱️ 2.5 hours • 📍 Aberdeen                         │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  User selects event → System loads event details → Proceeds to Step 2              │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              STEP 2: ORE QUANTITIES                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                        ORE QUANTITY ENTRY                                   │    │
│  │                                                                             │    │
│  │  Select which ores were collected:                                         │    │
│  │  ☐ Agricium     ☐ Aluminum      ☐ Beryl        ☐ Bexalite                 │    │
│  │  ☐ Borase       ☐ Copper        ☐ Diamond      ☐ Gold                     │    │
│  │  ☐ Hadanite     ☐ Hephaestanite ☐ Inert Mat.   ☐ Laranite                │    │
│  │  ☐ Quantanium   ☐ Taranite      ☐ Titanium     ☐ Tungsten                │    │
│  │                                                                             │    │
│  │  Then enter quantities for selected ores:                                  │    │
│  │  Quantanium (SCU Amount):     [_____________]  ← 1,247                     │    │
│  │  Laranite (SCU Amount):       [_____________]  ← 856                       │    │
│  │  Hadanite (SCU Amount):       [_____________]  ← 2,150                     │    │
│  │                                                                             │    │
│  │  💡 Enter total SCU collected for each ore type                            │    │
│  │                                                                             │    │
│  │                               [Continue]                                   │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Features:                                                                          │
│  • Enhanced UI with improved spacing and layout                                    │
│  • Alphabetical listing with better readability                                   │
│  • Supports unlimited ore types with continuation support                         │
│  • Input validation and error handling                                             │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         STEP 2.5: CUSTOM PRICING (NEW)                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                      CUSTOM PRICING OVERRIDE                                │    │
│  │                                                                             │    │
│  │  🆕 Override UEX Corp prices with custom values (optional):                │    │
│  │                                                                             │    │
│  │  💎 Quantanium: 17,500 aUEC  [🔧 Custom Price]                            │    │
│  │  💎 Laranite:   28,500 aUEC  [🔧 Custom Price]                            │    │
│  │  💎 Hadanite:    8,750 aUEC  [🔧 Custom Price]                            │    │
│  │                                                                             │    │
│  │  🔧 Custom prices: Green buttons with updated amounts                      │    │
│  │  💎 UEX prices: Gray buttons with current market rates                     │    │
│  │                                                                             │    │
│  │  💡 Leave at UEX prices or override with custom amounts                    │    │
│  │                                                                             │    │
│  │                        [Continue to Payout Management]                     │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Key Features:                                                                      │
│  • Override any ore price with custom values                                      │
│  • Visual indicators: 🔧 green for custom, 💎 gray for UEX                       │
│  • Button updates instantly after custom entry                                    │
│  • Session persistence for custom pricing data                                    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            STEP 3: PRICING REVIEW                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                         PRICING REVIEW                                      │    │
│  │                                                                             │    │
│  │  # Ore Collection Breakdown                                                 │    │
│  │                                                                             │    │
│  │  ```                                                                        │    │
│  │  💎 Quantanium:  1,247 SCU × 17,500 aUEC = 21,822,500 aUEC               │    │
│  │  💎 Laranite:      856 SCU × 28,500 aUEC = 24,396,000 aUEC               │    │
│  │  🔧 Hadanite:    2,150 SCU ×  3,000 aUEC =  6,450,000 aUEC (Custom)     │    │
│  │  ```                                                                        │    │
│  │                                                                             │    │
│  │  📊 Total Value: 52,668,500 aUEC                                          │    │
│  │  👥 Participants: 15 total                                                 │    │
│  │                                                                             │    │
│  │                        [Continue to Payout Management]                     │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Enhanced Features:                                                                 │
│  • Custom price integration with ore name mapping                                 │
│  • Enhanced formatting with markdown headers and code blocks                      │
│  • ANSI color support for better readability                                      │
│  • Visual distinction between UEX and custom pricing                              │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            STEP 4: PAYOUT MANAGEMENT                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                       DONATION SELECTION                                    │    │
│  │                                                                             │    │
│  │  Select participants who want to donate their share:                       │    │
│  │                                                                             │    │
│  │  Alice_Miner (156min) - Receiving [💰 Toggle Donate]                      │    │
│  │  Bob_Hauler (203min) - Receiving  [💰 Toggle Donate]                      │    │
│  │  Charlie_Pilot (89min) - Receiving [💰 Toggle Donate]                     │    │
│  │  Diana_Scout (178min) - Donating  [💝 Toggle Receive]                     │    │
│  │  Eve_Navigator (134min) - Receiving [💰 Toggle Donate]                     │    │
│  │  Frank_Gunner (221min) - Receiving [💰 Toggle Donate]                     │    │
│  │                                                                             │    │
│  │  💡 Donated shares redistribute equally to non-donors                      │    │
│  │                                                                             │    │
│  │                        [Calculate Final Payroll]                           │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Enhanced Features:                                                                 │
│  • Enhanced button text with participant names first                              │
│  • Color feedback: buttons refresh with different colors when toggling            │
│  • Longer username display (15 characters vs 11-12)                              │
│  • Clear donation status indicators                                               │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            FINAL CALCULATION RESULT                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                         🏆 PAYROLL COMPLETE                                 │    │
│  │                                                                             │    │
│  │  Event: sm-12345 • Total: 52,668,500 aUEC • Participants: 15             │    │
│  │                                                                             │    │
│  │  # Distribution Summary                                                     │    │
│  │  • Session Duration: 192 minutes                                           │    │
│  │  • Donated Re-distribution Amount: 6,890,000 aUEC                         │    │
│  │  • Payroll ID: pay_sm12345_20250910                                       │    │
│  │                                                                             │    │
│  │  ```                                                                        │    │
│  │  Frank_Gunner:     8,420,000 aUEC (221min)                               │    │
│  │  Bob_Hauler:       7,830,000 aUEC (203min)                               │    │
│  │  Diana_Scout:      DONATED 💝                                             │    │
│  │  Eve_Navigator:    5,170,000 aUEC (134min)                                │    │
│  │  Alice_Miner:      DONATED 💝                                             │    │
│  │  ```                                                                        │    │
│  │                                                                             │    │
│  │  Calculated by: PayrollOfficer_Jane                                        │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎛️ User Interface Components

### **Enhanced Step Navigation**
```
Progress Indicator:
[✅ Step 1] → [✅ Step 2] → [✅ Step 2.5] → [⏳ Step 3] → [⭕ Step 4]

Back Navigation:
[← Back: Change Prices] [Cancel Session] [Next: Payout Management →]
```

### **Error Handling Flow**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Input     │    │ Validation  │    │   Action    │
│   Error     │────│   Failed    │────│Show Error + │
│             │    │             │    │Allow Retry │
└─────────────┘    └─────────────┘    └─────────────┘

Examples:
• "❌ Invalid quantity: Must be a positive number"
• "❌ No ores selected: Please choose at least one ore type"  
• "❌ Price data unavailable: Using cached prices"
• "❌ Custom price must be positive"
```

---

## 🔧 Technical Architecture

### **Enhanced Command Structure**
```
/payroll calculate
        │
        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Thin Wrapper   │───▶│  Business Logic │───▶│   Database      │
│  commands/      │    │  modules/       │    │   Operations    │
│  payroll.py     │    │  payroll/       │    │   + Sessions    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Enhanced Data Flow**
```
Event Selection → Ore Quantities → Custom Pricing → Pricing Review → Payout Management → Storage

┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│    Event    │  │   Ore       │  │   Custom    │  │   Review    │  │   Payout    │  │   Store     │
│  Selection  │─▶│ Quantities  │─▶│  Pricing    │─▶│  Pricing    │─▶│ Management  │─▶│  Results    │
│             │  │             │  │ (Optional)  │  │             │  │             │  │             │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

---

## 💡 Key Features & Benefits

### **Modern UI/UX**
- ✅ **5-step workflow** - Including optional custom pricing step
- ✅ **Visual progress indicators** - Enhanced step navigation
- ✅ **Back navigation** - Easily fix mistakes without restarting
- ✅ **Enhanced layout** - Wider windows with better spacing and readability

### **Flexible & Powerful**
- ✅ **Custom pricing override** - Override UEX prices with custom values per ore
- ✅ **Individual donations** - Per-person choice with enhanced button feedback
- ✅ **Enhanced visual feedback** - Color-coded buttons and status indicators
- ✅ **Session persistence** - Custom pricing data survives across steps

### **Enhanced Error Recovery**
- ✅ **Step-by-step validation** - Catch issues early with better error messages
- ✅ **Graceful degradation** - Continue working even if APIs fail
- ✅ **Transaction safety** - Database rollback on failures
- ✅ **Clear visual feedback** - Users see immediate status updates

---

## 🎯 Comparison: v2.0 vs v3.0 System

| Feature | v2.0 System | v3.0 System |
|---------|-------------|-------------|
| **Workflow Steps** | 4-step process | 5-step process with custom pricing |
| **Custom Pricing** | UEX prices only | Step 2.5 custom pricing override |
| **Button Feedback** | Basic button text | Enhanced with names and color feedback |
| **Layout** | Standard Discord UI | Wider windows with enhanced spacing |
| **Terminology** | "Total Donated" | "Donated Re-distribution Amount" |
| **Pricing Integration** | Fixed UEX integration | Custom price integration with mapping |
| **Session Management** | Basic session storage | Enhanced with custom pricing persistence |
| **Visual Design** | Standard formatting | Markdown headers and code blocks |

---

## 🚀 New Features in v3.0

### **Step 2.5: Custom Pricing System**
- 🆕 **Override UEX Prices** - Set custom values for any ore type
- 🔧 **Visual Indicators** - Green buttons for custom, gray for UEX prices
- 💾 **Session Persistence** - Custom prices saved across workflow steps
- 🔄 **Real-time Updates** - Buttons update immediately after custom entry

### **Enhanced User Experience**
- 📏 **Better Layout** - Wider windows with improved spacing and text sizing
- 🎨 **Enhanced Visual Design** - Markdown formatting and ANSI color support
- 🏷️ **Better Button Text** - Participant names first with clear donation status
- 🎯 **Improved Terminology** - "Donated Re-distribution Amount" for clarity

### **New Lookup Command**
- 🔍 **`/payroll lookup`** - Comprehensive event history with full details
- 📊 **Complete Event Summary** - Date, time, duration, participants
- 💰 **Payout Breakdown** - Individual distributions with donation status
- 📋 **Ore Collection Data** - Quantities and pricing used

---

## 🚀 Future Enhancements

### **Planned Features**
- 📊 **Visual reports** - Graphical payout distributions
- 🎰 **Lottery integration** - Automatic entry based on participation  
- 📱 **Mobile optimization** - Responsive UI elements
- 🔄 **Batch processing** - Multiple events at once
- 📈 **Analytics dashboard** - Historical payout trends

### **Integration Points**
- 🎮 **Star Citizen API** - Real-time commodity prices
- 📊 **Organization tracking** - Member participation history
- 🏆 **Achievement system** - Recognition for consistent participation
- 📧 **Notification system** - Payout alerts and summaries

---

> **Created:** September 2025  
> **System Version:** Sunday Mining Enhancement v3.0  
> **Last Updated:** Documentation refresh for custom pricing features  

*This documentation reflects the complete 5-step payroll workflow with Step 2.5 Custom Pricing implemented in the feature/sunday-mining-enhancements branch.*