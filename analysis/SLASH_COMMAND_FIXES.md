# Slash Command Issues & Fixes

## 🚨 Critical Issues Preventing Commands from Appearing

### 1. **Invalid Command Names**
Discord slash command names CANNOT contain hyphens or uppercase letters.

**❌ Current Names (Invalid):**
- `red-events` 
- `red-ping`
- `red-market`
- `red-health`

**✅ Fixed Names (Valid):**
- `redevents`
- `redping` 
- `redmarket`
- `redhealth`

### 2. **Incorrect Group Registration**
Your command groups are not being registered properly.

**❌ Current Method in `events_subcommand.py`:**
```python
class EventManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.red_events = RedEventsGroup()
        self.add_app_command(self.red_events)  # THIS DOESN'T WORK
```

**✅ Correct Method:**
```python
class EventManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Add the group directly to the command tree
    redevents = app_commands.Group(name='redevents', description='Red Legion event management')
    
    @redevents.command(name='create', description='Create a new event')
    async def create(self, interaction: discord.Interaction):
        pass
```

## 🔧 Required File Changes

### 1. Fix `src/commands/events_subcommand.py`
```python
class RedEventsGroup(app_commands.Group):
    def __init__(self):
        super().__init__(
            name="redevents",  # CHANGED: removed hyphen
            description="Red Legion event management system"
        )
```

### 2. Fix `src/commands/general.py`  
```python
@app_commands.command(name="redping", description="Test Red Legion bot responsiveness")
async def ping_cmd(self, interaction: discord.Interaction):
```

### 3. Fix All Command Files
Replace ALL command names:
- `red-*` → `red*`
- Remove hyphens from ALL slash command names

### 4. Add Debug Logging
In `handlers/core.py`, add after sync:
```python
# Log what actually got synced
print("🔍 Commands synced to Discord:")
for cmd in synced:
    print(f"  - /{cmd.name}")
```

## 🎯 Expected Results After Fixes

After fixing the command names, you should see:
- `/redevents create` 
- `/redevents list`
- `/redevents view`
- `/redevents delete`
- `/redping`
- `/redmarket`

## 📋 Testing Checklist

1. ✅ Fix all command names (remove hyphens)
2. ✅ Update command group registration
3. ✅ Deploy and test sync
4. ✅ Verify commands appear in Discord
5. ✅ Test command functionality

## ⚠️ Important Notes

- Command name changes are **breaking changes**
- Update any documentation/help text
- Inform users about new command names
- Global commands take up to 1 hour to sync
- Guild commands sync instantly for testing