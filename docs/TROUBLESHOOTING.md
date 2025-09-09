# Red Legion Bot Troubleshooting Guide

This guide helps diagnose and resolve common issues with the Red Legion Discord Bot system.

## 🔍 Diagnostic Commands

Before troubleshooting, use these built-in diagnostic commands to gather information:

### System Health Checks
```bash
/redeventdiagnostics    # Check event system and database schema
/redapidebug           # Validate UEX API connectivity and data
/redchanneldiag        # Verify voice channel configuration
```

### Test Data Management
```bash
/redtestmining create   # Generate test data for debugging
/redtestmining status   # Check current test data
/redtestmining delete   # Clean up test data
```

## ❌ Common Issues and Solutions

### Sunday Mining Issues

#### Issue: Event Creation Fails
**Symptoms**: 
- `/redsundayminingstart` returns "Event creation failed"
- Database event creation test returns None
- No events appear in `/redpayroll calculate`

**Diagnosis**:
```bash
/redeventdiagnostics
```

**Common Causes & Solutions**:

1. **Database Schema Issues**
   - **Cause**: Missing columns in events table
   - **Solution**: Run database migrations
   ```bash
   ansible-playbook -i ansible/inventories/production.yml ansible/deploy.yml --tags migrations
   ```

2. **Guild Not in Database**
   - **Cause**: Guild record missing from guilds table
   - **Solution**: Migration 07 automatically creates guild records
   ```sql
   INSERT INTO guilds (guild_id, name, is_active) VALUES ('YOUR_GUILD_ID', 'Red Legion', true);
   ```

3. **TypeError in Event ID Generation**
   - **Cause**: Missing argument in string replace function
   - **Solution**: Ensure latest code is deployed with the fix

#### Issue: "Too Many Values to Unpack" Error in Payroll
**Symptoms**:
- `/redpayroll calculate` fails with unpacking error
- Events found but cannot be processed

**Diagnosis**:
Check if events are using the correct table and column format.

**Solution**:
Ensure all event queries consistently use the `events` table schema:
- `id` (not `event_id`)
- `guild_id` as BIGINT
- `name` and `event_name` columns
- `is_open` (not `status`)

#### Issue: No Participation Data
**Symptoms**:
- "No Participation Data" in payroll summary
- Test data shows 0 participation records

**Common Causes**:

1. **Foreign Key Constraint Violation**
   - **Cause**: `mining_participation.event_id` cannot reference `events.id`
   - **Diagnosis**: Check foreign key constraints
   ```sql
   SELECT constraint_name, table_name, column_name 
   FROM information_schema.key_column_usage 
   WHERE table_name = 'mining_participation';
   ```
   - **Solution**: Apply migration 05 to fix foreign key references

2. **Voice Tracking Not Working**
   - **Cause**: Bot lacks voice channel permissions
   - **Diagnosis**: Use `/redchanneldiag` to check permissions
   - **Solution**: Ensure bot has Connect, Speak, and Use Voice Activity permissions

### API and Pricing Issues

#### Issue: UEX API Errors
**Symptoms**:
- `/redpricecheck` returns "UEX API Error"
- Price data not updating

**Diagnosis**:
```bash
/redapidebug
```

**Common Causes & Solutions**:

1. **API Connection Issues**
   - Check internet connectivity
   - Verify UEX Corp API status
   - Check bearer token validity

2. **Location Data Missing**
   - **Cause**: API response format changed
   - **Solution**: Update location parsing logic

3. **Cache Issues**
   - **Solution**: Use `/redpricerefresh` to force cache refresh

### Voice Channel Issues

#### Issue: Voice Channels Not Found
**Symptoms**:
- Channel diagnostics show "Not Found" for mining channels
- Bot cannot join voice channels

**Diagnosis**:
```bash
/redchanneldiag
```

**Solutions**:

1. **Update Channel IDs**
   - Verify current Discord channel IDs
   - Update database with correct IDs using migration 06

2. **Check Bot Permissions**
   - Ensure bot has required voice permissions
   - Verify bot is in the Discord server

### Database Issues

#### Issue: Migration Failures
**Symptoms**:
- Deployment fails during migration phase
- Schema inconsistencies

**Common Solutions**:

1. **Missing Dependencies**
   - Install required Python packages
   ```bash
   pip install -r requirements.txt
   ```

2. **Permission Issues**
   - Ensure database user has CREATE, ALTER, DROP permissions
   - Check connection string format

3. **Schema Conflicts**
   - Review existing schema before applying migrations
   - Consider running specific migrations individually

## 🛠️ Manual Fixes

### Database Connection Issues

If automated migration fails, connect manually:

```bash
# Connect to VM
gcloud compute ssh INSTANCE_NAME --zone=ZONE --project=PROJECT_ID

# Check database connection
cd /app
PYTHONPATH=/app/src python3 -c "from config.settings import get_database_url; print(get_database_url())"

# Test connection
PYTHONPATH=/app/src python3 -c "
from config.settings import get_database_url
from database.connection import resolve_database_url
import psycopg2
conn = psycopg2.connect(resolve_database_url(get_database_url()))
print('✅ Database connection successful')
conn.close()
"
```

### Force Schema Reset (Use with Caution)

Only for development environments:

```sql
-- Reset events table to proper schema
DROP TABLE IF EXISTS events CASCADE;
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    name TEXT,
    event_name TEXT NOT NULL,
    event_date DATE NOT NULL,
    event_time TIMESTAMP,
    is_open BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    total_participants INTEGER DEFAULT 0,
    total_value REAL DEFAULT 0,
    payroll_calculated BOOLEAN DEFAULT false,
    pdf_generated BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes
CREATE INDEX idx_events_guild_id ON events(guild_id);
CREATE INDEX idx_events_name ON events(name);
CREATE INDEX idx_events_is_active ON events(is_active);
```

## 📊 Monitoring and Logging

### Log Analysis

Check bot logs for detailed error information:

```bash
# On VM
tail -f /app/bot.log

# Filter for errors
grep -i error /app/bot.log | tail -20

# Check specific component logs
grep -i "mining\|payroll\|api" /app/bot.log | tail -20
```

### Performance Monitoring

Monitor system resources:

```bash
# Check system resources
htop

# Monitor database connections
ps aux | grep postgres

# Check disk usage
df -h
```

## 🚨 Emergency Procedures

### Bot Not Responding

1. **Check Process Status**
   ```bash
   ps aux | grep python | grep main.py
   ```

2. **Restart Bot Service**
   ```bash
   sudo systemctl restart red-legion-bot
   ```

3. **Check Service Logs**
   ```bash
   sudo journalctl -u red-legion-bot -f
   ```

### Database Connection Lost

1. **Check Database Status**
   ```bash
   gcloud sql instances describe INSTANCE_NAME
   ```

2. **Restart Database Connection**
   ```bash
   # Restart bot to refresh connections
   sudo systemctl restart red-legion-bot
   ```

### Complete System Recovery

If all else fails:

1. **Redeploy from Scratch**
   ```bash
   ansible-playbook -i ansible/inventories/production.yml ansible/deploy.yml --force
   ```

2. **Restore from Backup**
   ```bash
   # Restore database backup
   gcloud sql backups restore BACKUP_ID --restore-instance=INSTANCE_NAME
   ```

## 📞 Getting Help

### Information to Gather

When seeking support, provide:

1. **Diagnostic Command Output**
   - `/redeventdiagnostics` results
   - `/redapidebug` results  
   - `/redchanneldiag` results

2. **Error Messages**
   - Full error text from Discord
   - Bot log excerpts
   - Database error messages

3. **System Information**
   - Bot version/commit hash
   - Deployment date
   - Recent changes made

4. **Steps to Reproduce**
   - Exact commands used
   - Expected vs actual behavior
   - Frequency of issue

### Support Channels

- GitHub Issues: Technical bugs and feature requests
- Discord: Real-time troubleshooting assistance
- Documentation: Reference guides and examples

Remember to always test fixes in a development environment before applying to production!