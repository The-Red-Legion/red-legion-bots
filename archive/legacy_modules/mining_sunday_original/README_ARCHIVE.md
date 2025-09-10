# Archived Sunday Mining Module (Legacy)

**Archived Date**: September 9, 2025  
**Reason**: Complete refactor for unified mining system  
**Original Size**: 138KB core module + supporting files

## Archived Files

- `core.py` - Main Sunday Mining commands (138KB)
  - `SundayMiningCommands` class with hardcoded Sunday references
  - Legacy commands: `/redsundayminingstart`, `/redsundayminingstop`
  - Uses old database schema (`mining_events`, `mining_participation`)

- `testing.py` - Mining test utilities (18KB)
- `test_mining.py` - Command testing module (18KB)  
- `mining.py` - Events mining integration (6KB)
- `__init__.py` - Module initialization

## Why Archived

1. **Command Structure**: Used Sunday-specific naming instead of flexible `/mining` commands
2. **Database Schema**: Built for legacy table structure, incompatible with unified schema
3. **Code Size**: Single 138KB file was too monolithic for maintainability
4. **Hardcoded Logic**: Too many Sunday-specific assumptions throughout codebase

## Replacement

New unified mining system with:
- Clean command structure (`/mining start`, `/payroll mining`)
- Event-centric database design using unified schema
- Modular architecture with separated concerns
- Flexible for any day mining operations, not just Sunday

## Reference Value

This archived code contains working implementations of:
- Voice channel tracking logic
- UEX API ore price integration  
- Payroll calculation algorithms
- Discord UI components (modals, views)

These patterns can be referenced when building the new unified system.