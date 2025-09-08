# Slash Command Conversion Plan

## Overview
Convert all prefix commands (!) to modern slash commands (/) with organized dropdown choices, following the successful pattern of the `/payroll` command. Users prefer the discoverability and UX of slash commands over memorizing multiple prefix commands.

## Implementation Strategy

### Phase 1: Core Mining Commands (Priority 1)
**Objective**: Convert mining channel management to consolidated `/mining` command

**Current State**:
- ✅ `/sunday_mining_start` (already slash)
- ✅ `/sunday_mining_stop` (already slash) 
- ✅ `/payroll` (already slash with 3 choices: calculate, submit, view)
- ❌ `!add_mining_channel`
- ❌ `!remove_mining_channel`
- ❌ `!list_mining_channels`

**Target Implementation**:
```
/mining [action]
├── start        - Start Sunday mining session
├── stop         - Stop current mining session  
├── payroll      - Payroll operations (submenu)
│   ├── calculate - Calculate earnings
│   ├── submit   - Submit ore collections
│   └── view     - View last session
├── channels     - Channel management (submenu)
│   ├── list     - List mining channels
│   ├── add      - Add mining channel
│   └── remove   - Remove mining channel
```

### Phase 2: Admin/Diagnostics Commands (Priority 2)
**Objective**: Consolidate administrative and diagnostic commands

**Current State**:
- ❌ `!refresh_config`
- ❌ `!restart_red_legion_bot` 
- ❌ `!health`
- ❌ `!test`
- ❌ `!dbtest`
- ❌ `!config_check`

**Target Implementation**:
```
/admin [action]
├── diagnostics  - System diagnostics (submenu)
│   ├── health   - Bot health check
│   ├── database - Database connectivity test
│   ├── config   - Configuration validation
│   └── full     - Complete system test
├── system       - System management (submenu)
│   ├── restart  - Restart bot
│   ├── refresh  - Refresh configuration
│   └── status   - Current system status
└── testdata     - Test data management (already exists)
```

### Phase 3: Market System (Priority 3)
**Objective**: Create comprehensive marketplace with Star Citizen item categories and inventory management

**Current State**:
- ❌ `!list_market`
- ❌ `!add_market_item`

**Target Implementation**:
```
/market [action]
├── browse       - Browse marketplace (submenu)
│   ├── all      - Show all items
│   ├── weapons  - Weapons & attachments
│   ├── armor    - Personal armor & clothing
│   ├── ships    - Ships & vehicles
│   ├── components - Ship components & parts
│   ├── commodities - Trade commodities & cargo
│   ├── consumables - Food, medical, ammo
│   └── misc     - Miscellaneous items
├── sell         - List item for sale (submenu)
│   ├── weapon   - List weapon/attachment
│   ├── armor    - List armor/clothing
│   ├── ship     - List ship/vehicle
│   ├── component - List ship component
│   ├── commodity - List trade commodity
│   ├── consumable - List consumable item
│   └── misc     - List misc item
├── buy          - Purchase item from market
├── manage       - Seller management (submenu)
│   ├── inventory - View your listings
│   ├── edit     - Edit listing details
│   ├── remove   - Remove listing
│   └── sold     - View sales history
├── search       - Search marketplace
└── stats        - Market statistics
```

**Market Sub-phases**:
- **3a**: Basic market structure with categories
- **3b**: Star Citizen item database integration
- **3c**: Inventory management and transactions
- **3d**: Advanced features (analytics, escrow, pricing)

### Phase 4: Secondary Features (Priority 4)
**Objective**: Convert remaining command categories

**Finance Commands**:
```
/finance [action]
├── loan         - Loan operations (submenu)
│   ├── request  - Request a loan
│   ├── status   - Check loan status
│   └── repay    - Make loan payment
└── balance      - Check account balance
```

**Event Commands**:
```
/events [action]
├── logging      - Event logging (submenu)
│   ├── start    - Start event logging
│   └── stop     - Stop event logging
├── contest      - Contest management (submenu)
│   ├── winner   - Pick contest winner
│   └── list     - List open contests
└── schedule     - Event scheduling
```

**Utility Commands**:
```
/utility [action]
├── ping         - Bot latency test
├── info         - Bot information
└── help         - Command help
```

### Phase 5: Cleanup (Priority 5)
**Objective**: Remove legacy prefix commands
- Add deprecation warnings to old prefix commands
- Eventually remove old prefix commands after transition period
- Update documentation

## Technical Requirements

### Database Schema for Market System
```sql
-- Market listings table
CREATE TABLE market_listings (
    id SERIAL PRIMARY KEY,
    seller_id BIGINT NOT NULL,
    item_category VARCHAR(50) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    item_condition VARCHAR(20), -- New, Used, Damaged
    quantity INTEGER DEFAULT 1,
    price_per_unit INTEGER NOT NULL,
    description TEXT,
    location VARCHAR(100), -- Stanton, Pyro, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Purchase transactions table  
CREATE TABLE market_transactions (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER REFERENCES market_listings(id),
    buyer_id BIGINT NOT NULL,
    seller_id BIGINT NOT NULL,
    quantity INTEGER NOT NULL,
    total_price INTEGER NOT NULL,
    transaction_date TIMESTAMP DEFAULT NOW()
);

-- User inventory table
CREATE TABLE user_inventory (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    item_category VARCHAR(50) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    quantity INTEGER DEFAULT 1,
    acquired_from VARCHAR(20), -- 'purchase', 'mining', 'mission'
    acquired_date TIMESTAMP DEFAULT NOW()
);
```

### Star Citizen Item Categories
- **Personal Weapons**: Rifles, pistols, melee, attachments
- **Personal Armor**: Helmets, chest, arms, legs, undersuit
- **Ships**: Fighters, haulers, miners, exploration, luxury
- **Ship Components**: Quantum drives, shields, weapons, coolers, power plants
- **Trade Commodities**: Minerals, gases, food, medical supplies
- **Consumables**: Food, drinks, medical items, ammunition
- **Miscellaneous**: Tools, decorations, collectibles

## Benefits
1. **Discoverability** - Users can explore commands via autocomplete
2. **User-Friendly** - No need to memorize multiple commands
3. **Consistent UX** - Same great experience as `/payroll` command
4. **Modern Discord UX** - Follows Discord's recommended patterns
5. **Organized** - Related functions grouped logically
6. **Extensible** - Easy to add new features within existing categories

## Success Criteria
- All major command categories converted to slash commands with choices
- User adoption of new slash commands
- Reduced support questions about command syntax
- Improved user engagement with bot features
- Successful marketplace transactions and inventory management

---
**Implementation Status**: Planning Phase
**Last Updated**: September 7, 2025
**Next Action**: Begin Phase 1 - Mining command conversion
