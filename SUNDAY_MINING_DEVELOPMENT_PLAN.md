# Sunday Mining Module Development Plan

## 🎯 Objective
Enhance and stabilize the Sunday Mining system with focus on reliability, new adhoc mining capabilities, and improved user experience.

## 📋 Current Status Assessment

### ✅ **What's Working Well**
- Core Sunday mining start/stop commands
- Voice channel tracking infrastructure
- UEX API integration for live ore prices
- PDF report generation
- Database-driven mining channel configuration
- Comprehensive test suite

### ⚠️ **Known Issues to Address**
- Voice tracking reliability issues
- Database schema validation gaps
- Error handling in edge cases
- Event creation and selection UX
- Bot voice connection stability

### 🚀 **New Features to Implement**
- Adhoc mining sessions for flexible operations
- Enhanced participant validation
- Improved diagnostic tools
- Better session persistence

## 🗓️ Development Phases

### **Phase 1: Stability & Fixes (Week 1)**
**Goal**: Ensure existing Sunday mining is rock-solid

#### 1.1 Voice Tracking Reliability
- [ ] Fix bot voice connection issues
- [ ] Improve channel join/leave handling
- [ ] Add connection retry logic
- [ ] Enhance voice state change tracking

#### 1.2 Database Schema Validation
- [ ] Verify all required tables exist
- [ ] Validate column structure matches expectations
- [ ] Add migration scripts for schema updates
- [ ] Implement schema health checks

#### 1.3 Error Handling Enhancement
- [ ] Add comprehensive try-catch blocks
- [ ] Implement graceful degradation
- [ ] Improve error messages for users
- [ ] Add logging for debugging

### **Phase 2: Adhoc Mining Sessions (Week 2)**
**Goal**: Implement flexible, user-initiated mining sessions

#### 2.1 Core Adhoc Framework
- [ ] Add `/mining adhoc` command structure
- [ ] Implement single-channel tracking mode
- [ ] Create adhoc session management
- [ ] Add participant validation UI

#### 2.2 Session Management
- [ ] Session creation and loading
- [ ] Persistent session storage
- [ ] Session timeout handling
- [ ] Integration with existing payroll system

#### 2.3 User Experience
- [ ] Intuitive command flow
- [ ] Clear status indicators
- [ ] Participant checkbox validation
- [ ] Session status dashboard

### **Phase 3: UX & Polish (Week 3)**
**Goal**: Improve overall user experience and add advanced features

#### 3.1 Enhanced Payroll Flow
- [ ] Better event selection interface
- [ ] Improved calculation modal
- [ ] Enhanced error messages
- [ ] Payroll calculation validation

#### 3.2 Diagnostic & Testing Tools
- [ ] Comprehensive system health checks
- [ ] Voice channel diagnostics
- [ ] Database connectivity tests
- [ ] Performance monitoring

#### 3.3 Documentation & Help
- [ ] In-Discord help commands
- [ ] User guides and tutorials
- [ ] Admin documentation
- [ ] Troubleshooting guides

## 🛠️ Technical Implementation Details

### New Command Structure
```
/mining [action]
├── start         - Sunday mining (existing)
├── stop          - Stop current session (existing)
├── adhoc         - Adhoc mining operations (NEW)
│   ├── new       - Start new adhoc session
│   ├── load      - Resume existing adhoc session
│   └── list      - View your adhoc sessions
├── payroll       - All payroll operations (enhanced)
├── status        - View current session status (NEW)
└── diagnostics   - System health checks (NEW)
```

### Database Extensions
```sql
-- Adhoc session support
ALTER TABLE events ADD COLUMN session_type VARCHAR(20) DEFAULT 'sunday';
ALTER TABLE events ADD COLUMN creator_id VARCHAR(50);
ALTER TABLE events ADD COLUMN target_channel_id VARCHAR(50);

-- Session persistence
CREATE TABLE IF NOT EXISTS adhoc_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    creator_id VARCHAR(50) NOT NULL,
    guild_id VARCHAR(50) NOT NULL,
    channel_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Key Components to Develop

#### 1. AdhocMiningSession Class
```python
class AdhocMiningSession:
    """Manages adhoc mining sessions with single-channel focus."""
    
    def __init__(self, creator_id, guild_id, channel_id):
        self.creator_id = creator_id
        self.guild_id = guild_id
        self.target_channel_id = channel_id
        self.participants = {}
        self.status = 'active'
    
    async def start_tracking(self):
        """Start tracking the target voice channel."""
        
    async def stop_tracking(self):
        """Stop tracking and validate participants."""
        
    async def validate_participants(self, interaction):
        """Show participant validation UI."""
```

#### 2. Enhanced Voice Tracking
```python
class VoiceTracker:
    """Enhanced voice tracking with reliability improvements."""
    
    async def join_channel_with_retry(self, channel_id, max_retries=3):
        """Join voice channel with retry logic."""
        
    async def handle_connection_error(self, channel_id, error):
        """Handle voice connection errors gracefully."""
        
    async def validate_voice_permissions(self, channel):
        """Check if bot has required voice permissions."""
```

#### 3. System Diagnostics
```python
class MiningDiagnostics:
    """Comprehensive system health checking."""
    
    async def check_voice_connectivity(self):
        """Test voice channel connections."""
        
    async def validate_database_schema(self):
        """Verify database structure."""
        
    async def test_uex_api_connection(self):
        """Validate UEX API connectivity."""
```

## 🎯 Success Criteria

### Phase 1 Success Metrics
- [ ] 99% successful voice channel connections
- [ ] Zero database schema-related errors
- [ ] All existing Sunday mining commands work reliably

### Phase 2 Success Metrics
- [ ] Adhoc sessions can be created and managed
- [ ] Single-channel tracking works accurately
- [ ] Participant validation is intuitive and reliable

### Phase 3 Success Metrics
- [ ] User satisfaction with payroll flow
- [ ] Comprehensive diagnostic coverage
- [ ] Clear documentation and help resources

## 🚀 Testing Strategy

### Unit Tests
- Voice tracking components
- Database operations
- Session management
- UEX API integration

### Integration Tests
- End-to-end session workflows
- Multi-user scenarios
- Error condition handling
- Performance under load

### User Acceptance Testing
- Real mining session simulations
- Payroll calculation accuracy
- User interface intuitiveness
- Error message clarity

## 📝 Implementation Notes

### Development Approach
- **Incremental**: Build on existing infrastructure
- **Backward Compatible**: Don't break existing functionality
- **Modular**: Keep new features separate but integrated
- **Test-Driven**: Write tests before implementation

### Risk Mitigation
- Extensive testing in development environment
- Gradual rollout with feature flags
- Rollback plan for each phase
- Monitoring and alerting for production issues

---

**Branch**: `feature/sunday-mining-module`  
**Target Completion**: 3 weeks  
**Priority**: High (Core mining functionality)  
**Dependencies**: Database v2.0.0 (✅ Complete)
