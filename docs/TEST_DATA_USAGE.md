# Test Data Generation for Payroll Testing

The Red Legion Bot includes a comprehensive test data generation system that allows administrators to create dummy mining events and participation data for testing the payroll module.

## 🧪 Test Data Commands

All test data commands are admin-only and use the `/test-data` command group.

### Create Test Data

```
/test-data create [participants] [hours_ago] [location]
```

**Parameters:**
- `participants` (1-50): Number of test participants to generate (default: 10)
- `hours_ago` (0-48): How many hours ago the mining session started (default: 4)
- `location` (optional): Mining location name (random if not specified)

**What it creates:**
- ✅ A closed mining event with prefixed ID (e.g., `sm-a7k2m9`)
- ✅ Test users with realistic usernames (`TestMiner001`, `TestMiner002`, etc.)
- ✅ Multiple participation sessions per user (1-4 sessions each)
- ✅ Random participation durations (15 minutes to 3 hours)
- ✅ Mixed org membership status for realistic payroll testing
- ✅ Proper event timing within the specified window

### Delete Test Data

```
/test-data delete DELETE
```

**Parameters:**
- `confirm`: Must type exactly `DELETE` to confirm deletion

**What it removes:**
- 🗑️ All test participation records
- 🗑️ All test payroll records 
- 🗑️ All test events created by the command
- 🗑️ All test users
- 🗑️ Cleans database completely of test data

### Check Test Data Status

```
/test-data status
```

**Shows:**
- 📊 Current count of test users, events, participation records
- 📊 List of recent test events with IDs and locations
- 📊 Cleanup recommendations if test data exists

## 🚀 Testing Workflow

### 1. Create Test Event
```
/test-data create participants:15 hours_ago:6 location:Daymar
```

This creates a mining event that happened 6 hours ago with 15 participants mining on Daymar.

### 2. Test Payroll Calculation
```
/payroll mining
```

Use the event ID provided by the create command to calculate payroll for the test event.

### 3. Verify Results
- Check that payroll calculations are correct
- Verify fair distribution based on participation time
- Test different event scenarios (short vs long sessions)

### 4. Clean Up
```
/test-data delete DELETE
```

Always clean up test data when finished testing.

## 🎯 Test Scenarios

### Small Team Test
```
/test-data create participants:5 hours_ago:2
```
Good for testing basic payroll functionality with a small group.

### Large Operation Test  
```
/test-data create participants:30 hours_ago:8
```
Tests performance and accuracy with larger participation groups.

### Historical Event Test
```
/test-data create participants:12 hours_ago:24
```
Creates an event from yesterday to test date handling.

### Multi-Session Test
The command automatically creates multiple participation sessions per user to test:
- Users joining and leaving multiple times
- Overlapping participation periods  
- Varying session lengths
- Realistic mining patterns

## 📋 Database Integration

The test data command works with the unified mining system database schema:

- **Events Table**: Creates proper mining events with `event_type='mining'` and `status='closed'`
- **Participation Table**: Generates realistic participation patterns with proper timing
- **Users Table**: Creates test users that don't interfere with real users
- **Unified Schema**: Compatible with the new modules architecture

## ⚠️ Important Notes

1. **Admin Only**: All test data commands require administrator permissions
2. **Test Prefix**: All test users use `test_user_` prefix to avoid conflicts
3. **Auto Cleanup**: The delete command only removes test data, never real data
4. **Event IDs**: Generated event IDs follow the real format (`sm-xxxxxx`)
5. **Closed Events**: Test events are created as "closed" so payroll can be calculated immediately

## 🔍 Troubleshooting

**Command not available?**
- Ensure the bot has been restarted after adding the test data commands
- Check that you have administrator permissions
- Verify the bot loaded the `commands.test_data` extension

**Import errors?**
- The command uses the new unified database schema
- Ensure all database migrations have been applied
- Check database connection in bot logs

**No test data showing?**
- Test data is automatically cleaned after 7 days for safety
- Use `/test-data status` to check current state
- Verify you're looking in the correct guild/server

This test data system provides a comprehensive way to validate the payroll module without affecting real mining operations or data.