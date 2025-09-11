# Red Legion Bot Commands Reference v3.0.0

Complete reference guide for all available Discord slash commands in the Red Legion Bot system.

## 🎯 Sunday Mining Operations

### Core Mining Commands

#### `/redsundayminingstart`
**Description**: Initialize advanced mining session with multi-channel voice tracking  
**Permissions**: Admin, OrgLeaders  
**Features**: 
- Starts tracking across 7 dedicated mining channels
- Creates database event with prefixed ID (sm-xxxxx)
- Monitors voice channel participation in real-time
- Automatic organization member detection

**Usage Example**:
```
/redsundayminingstart
```

#### `/redsundayminingstop`
**Description**: End mining session and generate detailed participation summary  
**Permissions**: Admin, OrgLeaders  
**Features**:
- Comprehensive participation analytics
- Channel-by-channel breakdown
- Session duration statistics
- Preparation for payroll calculation

## 💰 Payroll System Commands

### Core Payroll Commands

#### `/payroll calculate`
**Description**: Modern event-driven payroll calculation with enhanced UI and custom pricing  
**Permissions**: Admin, OrgLeaders  
**Features**:
- Interactive event selection from completed mining/salvage/combat sessions
- **Step 1**: Event Selection - Choose from completed events with participant preview
- **Step 2**: Ore Quantities - Enter collected quantities with continuation support  
- **Step 2.5**: Custom Pricing - Override UEX Corp prices with custom values per ore
- **Step 3**: Pricing Review - Verify calculations with custom price integration
- **Step 4**: Payout Management - Individual donation controls with visual feedback
- **Enhanced UI**: Improved spacing, larger text, and better readability
- **Donation System**: "Donated Re-distribution Amount" terminology for equal distribution

**Enhanced Workflow**:
1. Select completed event from dropdown menu
2. Enter ore quantities with improved UI and continuation support
3. Optional custom pricing with per-ore override buttons showing status
4. Review pricing with custom price integration and enhanced formatting  
5. Manage individual payouts with improved button text and color feedback
6. Generate final payroll with participation time display

#### `/payroll resume`
**Description**: Resume your active payroll calculation session  
**Permissions**: Admin, OrgLeaders  
**Features**:
- Automatically detects and resumes interrupted sessions
- Preserves all entered data and custom pricing
- Returns to the exact step where you left off
- Session timeout protection (30 minutes)

#### `/payroll status`
**Description**: View payroll system status and recent activity  
**Permissions**: Admin, OrgLeaders  
**Features**:
- Recent payroll calculations summary
- Pending events by type (mining, salvage, combat)
- System health overview
- Quick action shortcuts

#### `/payroll lookup`
**Description**: **NEW** - Look up detailed information for past payroll events  
**Permissions**: Admin, OrgLeaders  
**Parameters**: `event_id` - Event ID to look up (e.g., sm-abc123)
**Features**:
- Complete event summary with date, time, duration
- Event organizer and location information
- Full participant list with participation time
- Ore collection breakdown and quantities
- Individual payout distributions with donation status
- Financial summary and calculation details
- Works with both calculated and uncalculated events

#### `/payroll quick`
**Description**: Quick mining payroll calculation with command parameters  
**Permissions**: Admin, OrgLeaders  
**Parameters**:
- `event_id`: Mining event ID (e.g., sm-abc123)
- `quantanium`, `laranite`, `agricium`, `hadanite`, `beryl`: SCU amounts
- `donation`: Donation percentage (0, 5, 10, 15, 20 - default: 10)
**Features**:
- Bypass UI for rapid calculations
- Direct parameter input for known quantities
- Automatic UEX price integration

### Price and Market Commands

#### `/redpricecheck [category]`
**Description**: Get current commodity prices with location data from UEX Corp API  
**Parameters**:
- `ores`: Mineable ores only (default)
- `all`: All commodities
- `high_value`: High-value commodities only

**Features**:
- Real-time pricing from UEX Corp API v2.0
- Best selling location for each commodity
- 24-hour intelligent caching
- Support for all 19 configured mineable ores

#### `/redpricerefresh [category]`
**Description**: Force refresh UEX price data bypassing 24-hour cache  
**Permissions**: Admin, OrgLeaders  
**Parameters**:
- `ores`: Refresh mineable ores (default)
- `all`: Refresh all commodities
- `high_value`: Refresh high-value commodities

## 🔧 Diagnostics and Testing

### System Diagnostics

#### `/redeventdiagnostics`
**Description**: Comprehensive event system health check  
**Permissions**: Admin, OrgLeaders  
**Features**:
- Database schema validation
- Event creation testing
- Table structure analysis
- Prefixed event ID compatibility check
- Recent events analysis

#### `/redapidebug`
**Description**: UEX API connection and data validation  
**Permissions**: Admin, OrgLeaders  
**Features**:
- API connection testing
- Data structure validation
- Location data verification
- Cache status analysis

#### `/redchanneldiag`
**Description**: Voice channel configuration verification  
**Permissions**: Admin, OrgLeaders  
**Features**:
- Mining channel detection
- Bot permission validation
- Channel accessibility testing
- Configuration status report

### Testing Commands

#### `/redtestmining create [participants] [hours_ago]`
**Description**: Generate comprehensive test mining data for development  
**Permissions**: Administrator only  
**Parameters**:
- `participants`: Number of test participants (1-20, default: 5)
- `hours_ago`: Session start time in hours ago (0-24, default: 2)

**Features**:
- Creates realistic test mining event
- Generates test user accounts
- Creates participation records
- Simulates multi-channel activity

#### `/redtestmining delete`
**Description**: Clean up all test data  
**Permissions**: Administrator only  
**Features**:
- Removes all test events from events table
- Cleans up test participation records
- Deletes test user accounts
- Removes test mining channels

#### `/redtestmining status`
**Description**: View current test data status  
**Permissions**: Administrator only

## 👥 Member Management

### Application System

#### `/redjoin apply`
**Description**: Submit application to join Red Legion with enhanced tracking  
**Features**:
- Interactive application form
- Automatic status tracking
- Admin notification system
- Application history management

#### `/redjoin status`
**Description**: Check application status with detailed progress  
**Features**:
- Current application status
- Processing timeline
- Next steps information
- Contact information for follow-up

### Loan System

#### `/redloans request [amount] [duration]`
**Description**: Apply for organization loan with automated processing  
**Parameters**:
- `amount`: Requested loan amount in aUEC
- `duration`: Loan duration in days

**Features**:
- Automated eligibility checking
- Interest rate calculation
- Repayment schedule generation
- Admin approval workflow

#### `/redloans status`
**Description**: View current loan obligations and payment schedule  
**Features**:
- Active loan details
- Payment history
- Remaining balance
- Due date notifications

## 🛒 Marketplace System

#### `/redmarket list [category]`
**Description**: Browse available items with enhanced filtering  
**Parameters**:
- `category`: Filter by item category (optional)

**Features**:
- Category-based filtering
- Price sorting and comparison
- Seller information
- Stock availability

#### `/redmarket add [name] [price] [stock] [description]`
**Description**: List item for sale with automated pricing  
**Permissions**: Authorized sellers only  
**Features**:
- Automated price validation
- Stock management
- Category assignment
- Sales tracking

## 🎪 Event Management

### Multi-Category Events

#### `/redevents create [name] [description] [category] [date] [time]`
**Description**: Schedule new organization event with category support  
**Permissions**: Event organizers  
**Categories**:
- `mining`: Mining operations and expeditions
- `combat`: PvP combat and fleet operations  
- `training`: Skill development and practice
- `social`: Community building activities
- `tournament`: Competitive events
- `expedition`: Exploration missions

#### `/redevents list [category] [upcoming_only]`
**Description**: View events with filtering and search  
**Parameters**:
- `category`: Filter by event category
- `upcoming_only`: Show only future events

#### `/redevents delete [event_id]`
**Description**: Cancel event with notification system  
**Permissions**: Event organizers, Admin

### Specialized Event Creation

#### `/redcombatcreate [name] [description] [combat_type] [date] [time]`
**Description**: Create combat/PvP events with specialized options  
**Permissions**: Combat organizers  
**Combat Types**:
- `pvp`: Player vs Player combat
- `fleet`: Large fleet operations
- `training`: Combat training exercises
- `tournament`: Competitive tournaments

#### `/redtrainingcreate [name] [description] [training_type] [date] [time]`
**Description**: Create training events with skill tracking  
**Permissions**: Training organizers  
**Training Types**:
- `flight`: Flight training and maneuvers
- `combat`: Combat skills development
- `mining`: Mining technique training
- `navigation`: Navigation and exploration
- `fps`: First-person shooter training

## 🔐 Permission Levels

### Admin (Administrator Role)
- Full access to all commands
- System diagnostics and testing
- User management capabilities
- Critical system operations

### OrgLeaders (Organization Leader Role)  
- Sunday Mining operations management
- Event creation and management
- Member application review
- Financial transaction oversight

### Authorized Sellers
- Marketplace item management
- Sales analytics access
- Inventory management

### Members
- Personal account management
- Event participation
- Application status checking
- Market browsing

## 📊 Enhanced Features

### Smart Automation
- **Intelligent Caching**: 24-hour API refresh cycles aligned with data updates
- **Auto-Detection**: Organization member status and permissions
- **Real-Time Updates**: Live voice channel monitoring and participation tracking
- **Error Recovery**: Comprehensive error handling with graceful fallbacks

### Analytics and Reporting
- **Participation Metrics**: Detailed mining session analytics
- **Financial Tracking**: Complete audit trails for all transactions
- **Performance Insights**: Mining efficiency and participant engagement
- **Automated Reporting**: PDF generation with comprehensive data

### User Experience
- **Interactive Interfaces**: Modal-based forms and selection menus
- **Real-Time Feedback**: Live status updates and progress indicators
- **Contextual Help**: Built-in tooltips and usage guidance
- **Accessibility**: Screen reader compatible and keyboard navigable

This reference guide covers all major functionality in the Red Legion Bot v2.0.0 system. For additional technical documentation, see the deployment guides and API documentation.