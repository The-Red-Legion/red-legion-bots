# Management Portal Integration

This document outlines the architectural changes made to integrate the Discord bot with the Red Legion Management Portal.

## Overview

As of this update, the Red Legion Discord Bot has transitioned from a standalone command-driven system to a hybrid architecture where:

- **Management Portal**: Handles all user-facing event management and payroll operations via web interface
- **Discord Bot**: Provides core voice tracking functionality and API endpoints for portal communication

## Changes Made

### Phase 1: Discord Command Deprecation

**Removed Commands:**
- `/mining start` and `/mining stop` - Event creation moved to portal
- `/payroll calculate` and `/payroll quick` - Payroll workflow moved to portal
- `/mining status` and `/payroll status` - Status displays moved to portal
- `/admin delete-event` and `/admin fix-event-durations` - Admin functions moved to portal

**Retained Commands:**
- `/diagnostics voice` and `/diagnostics channels` - Bot-specific diagnostics
- `/admin test-uex-api` and `/admin update-uex-prices` - System maintenance
- `/admin restart` - Bot management
- `/test-data create/delete/status` - Development tools

### Phase 2: API Endpoints

**New Bot API Server (Port 8001):**
```
POST /events/{event_id}/start-tracking    - Start voice tracking for portal-created events
POST /events/{event_id}/stop-tracking     - Stop voice tracking
GET  /events/{event_id}/participants      - Get current participants
GET  /prices/current                       - Get UEX ore prices
POST /prices/refresh                       - Force price refresh
GET  /bot/status                          - Bot health and connection status
GET  /health                              - Simple health check
```

### Phase 3: Architecture Integration

**Bot Responsibilities:**
- Real-time Discord voice channel monitoring
- Participant join/leave event tracking
- Voice state change detection
- UEX API price caching and retrieval
- Database participation record management
- API endpoints for portal communication

**Portal Responsibilities:**
- Event creation and configuration
- User interface for payroll calculation
- Ore quantity input and validation
- Payroll step-by-step workflow
- Event status monitoring and control
- Admin functions and reporting

## Benefits

1. **Superior User Experience**: Web interface provides better forms, validation, and workflow management
2. **Separation of Concerns**: Bot focuses on Discord-specific functionality, portal handles user interaction
3. **Scalability**: Web interface can support more complex workflows than Discord's limitations
4. **Maintainability**: Clear separation between voice tracking logic and user interface
5. **Mobile Friendly**: Portal works on mobile devices, Discord bot commands do not

## Integration Points

### Event Lifecycle
1. **Portal** creates event → calls bot API to start voice tracking
2. **Bot** monitors voice channels and records participation
3. **Portal** displays live participant data via API polling
4. **Portal** closes event → calls bot API to stop tracking
5. **Portal** handles payroll calculation using bot's processors

### Data Flow
- **Voice Tracking**: Bot → Database (real-time)
- **Event Management**: Portal → Database → Bot API (on-demand)
- **Price Data**: Bot → UEX API → Cache → Portal API (cached with refresh)
- **Payroll Calculation**: Portal → Bot processors → Database

## Deployment Considerations

**Dependencies Added:**
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
```

**Port Configuration:**
- Discord Bot: Normal Discord connection + Port 8001 (API)
- Management Portal: Port 8000 (web server)

**Backwards Compatibility:**
- Existing database schema unchanged
- Core voice tracking functionality preserved
- Diagnostic and admin commands remain functional
- API endpoints provide same data as Discord commands

## Development Workflow

**For Bot Development:**
- Focus on voice tracking accuracy and API reliability
- Test API endpoints independently
- Maintain Discord command compatibility for diagnostics

**For Portal Development:**
- Use bot API endpoints for real-time data
- Handle bot offline scenarios gracefully
- Implement proper error handling for API calls

## Migration Notes

This integration maintains full backwards compatibility with existing data while providing a foundation for enhanced user experience through the web portal. The bot's core competency (real-time Discord integration) is preserved while user-facing complexity is moved to a more suitable platform.