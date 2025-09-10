# Red Legion Database Migrations

## Unified Mining System (v2.0)

This directory contains the clean, unified database migration for the Red Legion Discord Bot v2.0.

### Migration Structure

- `10_unified_mining_system.sql` - Complete unified mining system schema
  - Drops all legacy tables (mining_yields, mining_participation, events, etc.)
  - Creates clean event-centric schema with event_id as primary identifier
  - Includes Sunday Mining, payroll, UEX pricing, and lottery systems

### Legacy Migrations

All previous migrations (00-08) have been archived to `/archive/` directory. The unified system represents a complete fresh start with optimized schema design.

### Deployment

Run the unified migration using the deployment script:

```bash
python3 run_unified_migration.py
```

Or via Ansible:

```yaml
- name: Apply unified database migration
  include_tasks: tasks/database_migrations.yml
```

### Key Features

- **Event-centric design**: All tables reference events.event_id as primary key
- **Prefixed event IDs**: `sm-a7k2m9`, `op-b3x8n4`, etc.
- **Unified participation tracking**: Single table for all event types
- **Comprehensive payroll system**: With donation support and audit trails
- **UEX Corp integration**: 12-hour refresh cycles with price snapshots
- **Member analytics**: Monthly stats and lottery eligibility tracking

### Schema Overview

#### Core Tables
- `events` - Universal event tracking (THE central table)
- `participation` - Individual participation records
- `payrolls` - Master payroll calculations with price snapshots
- `payouts` - Individual payout records
- `uex_prices` - Current UEX Corp pricing data
- `member_stats` - Analytics for leaderboards and lottery
- `lottery_events` - Org member reward system
- `lottery_entries` - Lottery participation tracking

#### Supporting Tables
- `guilds` - Discord server information
- `users` - User profiles
- `guild_memberships` - Member status tracking
- `schema_migrations` - Migration tracking

All tables include comprehensive indexes for performance and data integrity constraints.