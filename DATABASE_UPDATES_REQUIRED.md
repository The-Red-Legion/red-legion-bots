# Database Tables Update Guide for Slash Command Conversion

## Overview
After converting your Discord bot from prefix commands (`!commands`) to slash commands with "red-" prefix, several database tables need to be updated or created to support the new functionality.

## Required Database Updates

### 1. New Tables Needed

#### `market_items` - For red-market commands
```sql
CREATE TABLE IF NOT EXISTS market_items (
    item_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(15,2) NOT NULL CHECK (price > 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    category VARCHAR(50) DEFAULT 'general',
    seller_id VARCHAR(20),
    seller_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Stores Red Legion organization market items for the `red-market-list` and `red-market-add` commands.

#### `bot_config` - For red-config commands
```sql
CREATE TABLE IF NOT EXISTS bot_config (
    config_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT,
    config_type VARCHAR(20) DEFAULT 'string',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, config_key)
);
```

**Purpose**: Stores bot configuration settings for the `red-config-refresh` and other admin commands.

#### `command_usage` - For analytics and monitoring
```sql
CREATE TABLE IF NOT EXISTS command_usage (
    usage_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    user_id VARCHAR(20) REFERENCES users(user_id),
    command_name VARCHAR(100) NOT NULL,
    command_type VARCHAR(20) DEFAULT 'slash',
    success BOOLEAN DEFAULT TRUE,
    execution_time_ms INTEGER,
    error_message TEXT,
    parameters JSON,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Tracks usage of all slash commands for analytics and debugging.

#### `admin_actions` - For admin command logging
```sql
CREATE TABLE IF NOT EXISTS admin_actions (
    action_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    admin_id VARCHAR(20) REFERENCES users(user_id),
    admin_name VARCHAR(100),
    action_type VARCHAR(50) NOT NULL,
    target_resource VARCHAR(100),
    action_details JSON,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Logs all administrative actions performed through red-admin commands.

### 2. Existing Tables That Need Updates

#### `loans` table - For red-loan commands
Needs additional columns:
```sql
ALTER TABLE loans ADD COLUMN IF NOT EXISTS username VARCHAR(100);
ALTER TABLE loans ADD COLUMN IF NOT EXISTS issued_date_iso VARCHAR(30);
ALTER TABLE loans ADD COLUMN IF NOT EXISTS due_date_iso VARCHAR(30);
```

**Purpose**: Support the new `red-loan-request` and `red-loan-status` commands with proper date formatting.

#### `mining_events` table - Already updated
The event management columns were already added:
- `organizer_id`, `organizer_name`
- `event_type`, `start_time`, `end_time`
- `status`, `total_value_auec`

### 3. Migration Files Available

1. **`add_event_management_columns.sql`** (Current file) - Updates mining_events table
2. **`add_slash_command_tables.sql`** (New) - Creates all missing tables for slash commands

### 4. Command to Table Mapping

| Slash Command | Database Table(s) Used |
|---------------|------------------------|
| `red-market-list` | `market_items` |
| `red-market-add` | `market_items` |
| `red-loan-request` | `loans` |
| `red-loan-status` | `loans` |
| `red-events *` | `mining_events`, `event_categories` |
| `red-add-mining-channel` | `mining_channels` |
| `red-remove-mining-channel` | `mining_channels` |
| `red-list-mining-channels` | `mining_channels` |
| `red-config-refresh` | `bot_config` |
| All commands | `command_usage` (tracking) |
| Admin commands | `admin_actions` (logging) |

### 5. How to Apply Updates

#### Option 1: Run Migration Files
```bash
# Connect to your PostgreSQL database and run:
psql -d your_database_name -f src/database/migrations/add_event_management_columns.sql
psql -d your_database_name -f src/database/migrations/add_slash_command_tables.sql
```

#### Option 2: Use Database Initialization
The new tables are automatically created when you run the bot's database initialization:
```python
from database_init import init_database_for_deployment
init_database_for_deployment()
```

#### Option 3: Use the Updated Schema
The `src/database/schemas.py` file has been updated to include all new tables and will create them during bot startup.

### 6. Verification

After applying the updates, verify the tables exist:
```sql
-- Check if all required tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('market_items', 'bot_config', 'command_usage', 'admin_actions');

-- Check if loans table has new columns
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'loans' 
AND column_name IN ('username', 'issued_date_iso', 'due_date_iso');
```

### 7. Data Migration Notes

- **Existing Data**: All existing data is preserved
- **Default Values**: New columns have appropriate defaults
- **Constraints**: Added validation constraints for data integrity
- **Indexes**: Performance indexes added for all new tables

## Summary

The slash command conversion requires **4 new tables** and **3 new columns** in the existing loans table. All migration scripts are provided and the database schema has been updated to automatically create these tables during bot initialization.

The bot will function with the new slash commands once these database updates are applied.
