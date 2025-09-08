# Red Legion Bot - Database Architecture Redesign

## 🎯 Objective
Complete redesign of the database architecture for the Red Legion Discord Bot, starting fresh with clean schemas, proper relationships, and modern best practices.

## 🗑️ Cleanup Tasks
- Remove all existing database schemas and legacy code
- Clean up outdated migration scripts
- Remove duplicate and backup database files

## 🏗️ New Database Architecture

### Core Design Principles
1. **Normalization**: Proper database normalization to reduce redundancy
2. **Relationships**: Clear foreign key relationships between entities
3. **Scalability**: Design for multiple guilds and concurrent operations
4. **Performance**: Optimized indexes and query patterns
5. **Maintainability**: Clear naming conventions and documentation

### Primary Entities

#### 1. Guilds
- Central entity for Discord server management
- All other entities reference guild_id

#### 2. Users
- Discord user management across guilds
- Role and permission tracking

#### 3. Mining Events
- Sunday mining sessions and other events
- Event lifecycle management (open, closed, payroll, etc.)

#### 4. Mining Participation
- User participation in mining events
- Voice channel tracking and duration calculation

#### 5. Mining Channels
- Approved voice channels for mining activities
- Per-guild channel configuration

#### 6. Materials & Economy
- Mining materials and their values
- Market pricing and trading

#### 7. Loans & Financial
- Loan system for organization members
- Financial transaction history

### Schema Structure

```sql
-- Core guild management
CREATE TABLE guilds (
    id BIGINT PRIMARY KEY,           -- Discord guild ID
    name TEXT NOT NULL,              -- Guild name
    settings JSONB DEFAULT '{}',     -- Guild-specific settings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User management across guilds
CREATE TABLE users (
    id BIGINT PRIMARY KEY,           -- Discord user ID
    username TEXT NOT NULL,          -- Current username
    display_name TEXT,               -- Display name
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Guild membership and roles
CREATE TABLE guild_memberships (
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    is_org_member BOOLEAN DEFAULT FALSE,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, user_id)
);

-- Mining events
CREATE TABLE mining_events (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    event_time TIMESTAMP NOT NULL,
    event_name TEXT DEFAULT 'Sunday Mining',
    status VARCHAR(20) DEFAULT 'planned',    -- planned, active, completed, cancelled
    total_participants INTEGER DEFAULT 0,
    total_value_auec DECIMAL(15,2) DEFAULT 0,
    payroll_processed BOOLEAN DEFAULT FALSE,
    pdf_generated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mining channels (approved voice channels)
CREATE TABLE mining_channels (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    channel_id BIGINT NOT NULL,      -- Discord voice channel ID
    channel_name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, channel_id)
);

-- Mining participation tracking
CREATE TABLE mining_participation (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES mining_events(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    channel_id BIGINT NOT NULL,
    session_start TIMESTAMP NOT NULL,
    session_end TIMESTAMP,
    duration_seconds INTEGER,
    is_org_member BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Materials and their current values
CREATE TABLE materials (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    category VARCHAR(50),            -- ore, refined, component, etc.
    base_value_auec DECIMAL(10,2),
    current_market_value DECIMAL(10,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mining session material yields
CREATE TABLE mining_yields (
    id SERIAL PRIMARY KEY,
    participation_id INTEGER REFERENCES mining_participation(id) ON DELETE CASCADE,
    material_id INTEGER REFERENCES materials(id) ON DELETE CASCADE,
    quantity_scu DECIMAL(10,2) NOT NULL,
    estimated_value DECIMAL(15,2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Loan system
CREATE TABLE loans (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    borrower_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    amount_auec DECIMAL(15,2) NOT NULL,
    interest_rate DECIMAL(5,4) DEFAULT 0.0000,
    status VARCHAR(20) DEFAULT 'active',     -- active, paid, defaulted
    issued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP,
    paid_date TIMESTAMP
);
```

## 📋 Implementation Plan

### Phase 1: Database Schema Creation
1. Create new schema files with proper structure
2. Implement database connection and initialization
3. Add migration system for schema updates

### Phase 2: Core Operations
1. Guild management operations
2. User and membership operations
3. Mining event lifecycle operations

### Phase 3: Mining System Integration
1. Channel management and validation
2. Participation tracking
3. Material yield recording

### Phase 4: Economy & Loans
1. Material pricing system
2. Loan management
3. Financial reporting

### Phase 5: Testing & Validation
1. Comprehensive unit tests
2. Integration tests
3. Performance optimization

## 🚀 Getting Started

This redesign will provide a clean, scalable, and maintainable database architecture for the Red Legion Bot, supporting current features while enabling future expansion.
