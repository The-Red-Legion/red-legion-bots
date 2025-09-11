# Archived Legacy Commands Structure

**Archived Date**: September 9, 2025  
**Reason**: Complete architecture refactor from /commands to /modules structure  
**Total Size**: Multiple large files with mixed concerns

## Archived Commands

### Core Command Files
- `admin.py` (11KB) - Administrative commands
- `diagnostics.py` (16KB) - System diagnostics  
- `cache_diagnostics.py` (7KB) - Cache management
- `general.py` (1KB) - General utility commands

### Subcommand Files  
- `events_subcommand.py` (22KB) - Event management commands
- `loans_subcommand.py` (28KB) - Loan system commands
- `market_subcommand.py` (32KB) - Market trading commands
- `join_subcommand.py` (21KB) - Organization joining commands

### Module Directories
- `events/` - Event-related command modules
- `mining/` - Mining commands (already archived separately)

### Small Files
- `loans.py`, `market.py` - Lightweight command wrappers
- `__init__.py` - Module initialization

## Why Archived

1. **Mixed Architecture**: Combination of direct files and subcommand patterns
2. **Monolithic Files**: Several 20-30KB files with multiple responsibilities  
3. **Legacy Command Structure**: Not aligned with new modular `/modules` approach
4. **Database Dependencies**: Built for old schema, incompatible with unified system

## Replacement Strategy

New `/modules` architecture with:
- Domain-driven module organization
- Shared services (payroll, events, etc.)
- Clean separation of concerns
- Unified database schema integration

## Reference Value

These files contain working Discord.py patterns for:
- Slash command implementations
- UI components (modals, views, buttons)
- Database integration patterns
- Error handling and user feedback

Useful for reference when building new modular system.