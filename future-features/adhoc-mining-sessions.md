# Adhoc Mining Sessions Feature

## Overview
Allow OrgMembers to create spontaneous mining sessions outside of scheduled Sunday mining operations. These sessions provide flexibility for smaller groups or off-schedule mining activities with manual participation validation.

## Feature Requirements

### User Flow
1. **Initiation**: OrgMember types `/mining adhoc` 
2. **Session Creation**: Choose "New Session" or "Load Existing"
3. **Auto-Join**: Bot joins the user's current voice channel
4. **Tracking**: Bot monitors all members in that voice channel
5. **Manual Validation**: On stop, user selects actual participants via checkboxes
6. **Session Logging**: Event remains open for later payroll processing

### Key Differences from Sunday Mining
- **Single Channel Focus**: Only tracks the initiator's current voice channel
- **Manual Participation Validation**: User confirms who actually participated
- **Flexible Timing**: Can be started anytime by any OrgMember
- **Persistent Sessions**: Events remain open until payroll is processed

## Technical Implementation Plan

### Phase 1: Core Adhoc Session Framework

#### 1.1 Command Structure Extension
```
/mining [action]
├── start        - Sunday mining (existing)
├── stop         - Stop current session (existing)
├── adhoc        - Adhoc mining operations (NEW)
│   ├── new      - Start new adhoc session
│   ├── load     - Resume existing adhoc session
│   └── list     - View your adhoc sessions
├── payroll      - All payroll operations (enhanced)
└── channels     - Channel management (existing plan)
```

#### 1.2 Database Schema Extensions
```sql
-- Add session_type to distinguish Sunday vs Adhoc sessions
ALTER TABLE events ADD COLUMN session_type VARCHAR(20) DEFAULT 'sunday';
ALTER TABLE events ADD COLUMN initiator_id BIGINT;
ALTER TABLE events ADD COLUMN status VARCHAR(20) DEFAULT 'active'; -- active, stopped, completed

-- Track detected vs validated participants
CREATE TABLE adhoc_participants (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(event_id),
    user_id BIGINT NOT NULL,
    detected_at TIMESTAMP DEFAULT NOW(),
    validated BOOLEAN DEFAULT NULL,
    validated_by BIGINT,
    validated_at TIMESTAMP
);
```

#### 1.3 New Components Required

**AdhocSessionView**
```python
class AdhocSessionView(discord.ui.View):
    """View for adhoc session management."""
    
    @discord.ui.select(placeholder="Choose adhoc action...")
    async def adhoc_action_select(self, interaction, select):
        # Handle: new, load, list
        pass
```

**ParticipantValidationView**
```python
class ParticipantValidationView(discord.ui.View):
    """Checkbox interface for validating participants."""
    
    def __init__(self, detected_users):
        super().__init__()
        # Create checkboxes for each detected user
        for user in detected_users:
            self.add_item(UserParticipationCheckbox(user))
```

### Phase 2: Enhanced Payroll Integration

#### 2.1 Payroll Command Enhancement
- **Current**: Only shows Sunday mining events
- **Enhanced**: Shows both Sunday and adhoc events
- **Filtering**: Option to filter by session type

#### 2.2 Event Selection Enhancement
```python
class EnhancedEventSelectionView(discord.ui.View):
    """Enhanced event selection with session type indicators."""
    
    def format_event_option(self, event):
        # Add session type badges: 📅 Sunday | 🎯 Adhoc
        session_badge = "📅" if event.session_type == "sunday" else "🎯"
        return f"{session_badge} {event.name} - {event.date}"
```

### Phase 3: Advanced Features

#### 3.1 Session Persistence
- Save/load adhoc sessions across bot restarts
- Resume interrupted sessions
- Session timeout handling

#### 3.2 Advanced Validation
- Time-based participation thresholds
- AFK detection and exclusion
- Participation percentage calculations

## Implementation Phases

### 🎯 Phase 1: Core Functionality (Week 1-2)
- [ ] Extend `/mining` command with `adhoc` subcommand
- [ ] Implement basic adhoc session creation
- [ ] Add participant detection and validation UI
- [ ] Database schema updates

### 🔧 Phase 2: Integration (Week 3)
- [ ] Integrate adhoc events with existing payroll system
- [ ] Enhanced event selection with session type filtering
- [ ] Session status management

### 🚀 Phase 3: Polish (Week 4)
- [ ] Session persistence and recovery
- [ ] Advanced validation features
- [ ] Comprehensive testing and documentation

## User Experience Examples

### Scenario 1: Quick Mining Run
```
User: /mining adhoc
Bot: 🎯 Adhoc Mining Session
     [New Session] [Load Existing] [List Sessions]

User: Clicks "New Session"
Bot: ✅ Created "Adhoc Mining - 2025-09-07 14:30"
     🎤 Joined voice channel "Mining Ops #3"
     👥 Tracking: @User1, @User2, @User3
     
User: /mining stop
Bot: 🛑 Session Stopped
     👥 Detected Participants:
     ☑️ @User1 (45 minutes)
     ☑️ @User2 (42 minutes) 
     ☐ @User3 (12 minutes) - AFK?
     
     [Confirm Participants]

User: Unchecks @User3, clicks Confirm
Bot: ✅ Session saved with 2 participants
     📊 Event #47 ready for payroll processing
```

### Scenario 2: Payroll Processing
```
User: /payroll calculate
Bot: 📋 Select Mining Event:
     📅 Sunday Mining - 2025-09-01 ✅ Completed
     🎯 Adhoc Mining - 2025-09-07 ⏳ Pending
     🎯 Adhoc Mining - 2025-09-05 ✅ Completed
```

## Technical Considerations

### Voice Channel Management
- **Single Channel**: Unlike Sunday mining (7 channels), adhoc focuses on one
- **Auto-Join**: Bot must detect user's current voice channel
- **Channel Validation**: Ensure channel is appropriate for mining operations

### Participation Validation
- **Detection**: All users in voice channel during session
- **Validation**: Manual checkbox selection by session initiator
- **Edge Cases**: Handle users joining/leaving mid-session

### Data Integrity
- **Session Ownership**: Only initiator can validate participants
- **Audit Trail**: Track who validated what and when
- **Conflict Resolution**: Handle multiple adhoc sessions simultaneously

## Future Enhancements

### Advanced Features (Post-MVP)
- **Team Management**: Support for team-based adhoc sessions
- **Automatic Validation**: ML-based participation detection
- **Integration**: Link with external mining tools/trackers
- **Analytics**: Detailed mining operation statistics

### UI/UX Improvements
- **Session Dashboard**: Web interface for session management
- **Mobile Optimization**: Mobile-friendly interaction flows
- **Notification System**: Alerts for session events

## Success Metrics

### Adoption Metrics
- Number of adhoc sessions created per week
- User participation rates in adhoc vs Sunday sessions
- Session completion rates

### Quality Metrics
- Accurate participation validation rates
- Session data integrity
- User satisfaction with adhoc flow

## Implementation Notes

### Integration Points
- **Existing Mining System**: Reuse payroll calculation logic
- **Voice Tracking**: Leverage existing voice tracking infrastructure
- **Database**: Extend current event/participation tables

### Development Approach
- **Incremental**: Build on existing mining command structure
- **Backward Compatible**: Don't break existing Sunday mining
- **Modular**: Keep adhoc functionality separate but integrated

## Conclusion

This adhoc mining session feature addresses the need for flexible, user-initiated mining operations while maintaining the structure and payroll capabilities of the existing Sunday mining system. The phased approach ensures we can deliver value incrementally while building toward a comprehensive mining management solution.

**Priority**: Medium-High (after voice tracking debugging is complete)
**Complexity**: Medium (leverages existing infrastructure)
**User Impact**: High (addresses real operational need)
