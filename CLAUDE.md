# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a multi-project repository for the Red Legion Star Citizen organization, containing:

1. **red-legion-bots**: Discord bot for automated operations management (Python/Discord.py)
2. **red-legion-website**: Web interface for payroll management (FastAPI + Vue.js)
3. **red-legion-infra**: Infrastructure configuration and deployment

The main focus is the Discord bot which automates mining operations, payroll calculations, and member management for Star Citizen organizations.

## Development Commands

### Discord Bot (red-legion-bots/)

**Setup and Running:**
```bash
cd red-legion-bots/
pip install -r requirements.txt
python src/main.py
```

**Testing:**
```bash
cd red-legion-bots/
python -m pytest tests/
python test_discord_bot.py
python test_uex_api.py
python test_web_api.py
```

**Database Operations:**
```bash
cd red-legion-bots/
python database_migrations/deploy_unified_schema.py
python database_migrations/run_unified_migration.py
```

**Deployment:**
```bash
cd red-legion-bots/
ansible-playbook ansible/deploy.yml -i ansible/inventory.ini
```

### Website (red-legion-website/)

**Backend:**
```bash
cd red-legion-website/backend/
pip install -r requirements.txt
python main.py  # Runs on http://localhost:8000
```

**Frontend:**
```bash
cd red-legion-website/frontend/
npm install
npm run dev     # Runs on http://localhost:5173
npm run build   # Production build
```

## Architecture

### Discord Bot Architecture

The bot follows a modular architecture with clear separation of concerns:

**Core Components:**
- `src/main.py`: Entry point with logging and PID management
- `src/core/bot_setup.py`: Discord bot instance creation and configuration
- `src/database/`: Database models, schemas, and operations
- `src/config/settings.py`: Configuration management with Google Cloud Secret Manager
- `src/handlers/`: Event handlers (voice tracking, core events)

**Command Structure:**
- `src/commands/`: Thin command wrappers for Discord.py compatibility
- `src/modules/`: Business logic organized by feature area
  - `modules/mining/`: Sunday mining operations and events
  - `modules/payroll/`: Universal payroll system (mining/salvage/combat)
  - `modules/payroll/processors/`: Event-specific processors
  - `modules/payroll/ui/`: Discord UI components (views, modals)

**Key Features:**
- **Event System**: Unified event tracking with prefixed IDs (sm-, op-, tr-)
- **Payroll Calculator**: 5-step workflow with custom pricing and donation system
- **Voice Tracking**: Multi-channel participation monitoring
- **UEX Integration**: Real-time Star Citizen commodity pricing
- **Database**: PostgreSQL with async operations using asyncpg

### Database Schema

The system uses a unified PostgreSQL schema supporting multiple event types:

**Core Tables:**
- `events`: Universal event tracking (mining, salvage, combat)
- `participants`: Event participation records with time tracking
- `payroll_sessions`: Multi-step payroll calculation state
- `custom_prices`: User-defined pricing overrides
- `mining_channels`: Approved voice channels for tracking

**Key Models:** (see `src/database/models.py`)
- Event-centric design supports mining, salvage, combat operations
- Participation tracking with duration calculations
- Payroll session persistence for multi-step workflows

### Configuration Management

The bot uses a hybrid configuration approach:

1. **Environment Variables**: `DISCORD_TOKEN`, `DATABASE_URL`, `GUILD_ID`
2. **Google Cloud Secret Manager**: Production secrets with fallbacks
3. **Local Files**: `db_url.txt` for development
4. **Database-Driven**: Mining channels and dynamic configuration

**Important Files:**
- `src/config/settings.py`: Main configuration logic
- `ansible/inventory.ini`: Deployment configuration
- `.github/workflows/deploy.yml`: CI/CD pipeline

## Development Guidelines

### Testing

The repository includes multiple testing approaches:

**Active Tests:** (in `tests/`)
- `test_main.py`: Bot startup and configuration
- `test_database_v2.py`: Database operations
- `test_command_sync.py`: Discord command registration
- `test_validation.py`: Configuration validation

**Integration Tests:**
- `test_discord_bot.py`: End-to-end Discord bot functionality
- `test_uex_api.py`: UEX Corp API integration
- `test_web_api.py`: Web interface functionality

### Code Organization

**Command Pattern:**
Commands are thin wrappers in `src/commands/` that import business logic from `src/modules/`. This maintains Discord.py compatibility while keeping logic organized.

**Database Operations:**
Use the async database functions in `src/database/` and models in `src/database/models.py`. Connection management is handled centrally.

**Configuration:**
Always use `src/config/settings.py` functions rather than direct environment access. This ensures proper fallback handling and secret management.

### Deployment

The system uses GitHub Actions with Ansible for deployment:

1. **Infrastructure Setup**: VM provisioning and SSH configuration
2. **Full Codebase Deployment**: Complete code sync via Ansible
3. **Health Verification**: Discord API connectivity and process checks
4. **Log Collection**: System monitoring and troubleshooting

**Key Files:**
- `.github/workflows/deploy.yml`: Complete CI/CD pipeline
- `ansible/deploy.yml`: Ansible playbook for deployment
- `scripts/verify_deployment.py`: Post-deployment validation

## Common Tasks

**Adding New Commands:**
1. Create business logic in appropriate `src/modules/` subdirectory
2. Create thin wrapper in `src/commands/` that imports the module
3. Register in main bot setup

**Database Changes:**
1. Update models in `src/database/models.py`
2. Create migration in `database_migrations/`
3. Test with `test_database_v2.py`

**Configuration Changes:**
1. Update `src/config/settings.py`
2. Test with `scripts/validate_config.py`
3. Update Ansible variables if needed

**UEX API Integration:**
- Configuration in `UEX_API_CONFIG` (src/config/settings.py:92)
- Caching system with 24-hour refresh cycles
- Price data supports 19+ mineable ore types

## Important Notes

- The bot requires Discord intents for members, voice_states, and message_content
- Database URL encoding handles special characters in passwords automatically
- Mining operations use 7 dedicated voice channels for participation tracking
- Payroll calculations support custom pricing overrides and donation systems
- All sensitive configuration uses Google Cloud Secret Manager in production