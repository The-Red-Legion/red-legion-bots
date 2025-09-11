# Red Legion Bot Commands Reference v2.0.0

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

#### `/redpayroll calculate`
**Description**: Enhanced payroll calculation with donation system and editable UEX prices  
**Permissions**: Admin, OrgLeaders  
**Features**:
- Interactive event selection from recent mining sessions
- Voluntary donation system for participants
- Real-time UEX price integration with manual editing
- SCU quantity input with automatic value calculation
- PDF report generation with donation transparency

**Workflow**:
1. Select mining event from list
2. View current UEX ore prices with location data
3. Edit ore quantities and prices as needed
4. Select participants who wish to donate earnings
5. Choose donation recipients (prioritizes non-org members)
6. Generate final payroll with donation bonuses

#### `/redpayroll summary`
**Description**: View real-time participation summary without calculation  
**Permissions**: Admin, OrgLeaders  
**Features**:
- Current session participant list
- Real-time voice channel status
- Participation time tracking
- Organization member identification

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