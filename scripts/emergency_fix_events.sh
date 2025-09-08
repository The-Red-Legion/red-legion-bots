#!/bin/bash
# Emergency fix for missing events table on production server
# This script can be run directly on the production server to fix the issue

echo "🔧 Red Legion Bot - Emergency Events Table Fix"
echo "=============================================="

# Check if we're on the production server
if [ ! -f "/app/red-legion-bots/src/main.py" ]; then
    echo "❌ This script should be run on the production server"
    exit 1
fi

cd /app/red-legion-bots

echo "🔍 Checking database connection..."

# Try to connect to database and create the table
python3 -c "
import sys
sys.path.insert(0, 'src')
from src.database.connection import initialize_database
from src.config.settings import get_database_url

try:
    db_url = get_database_url()
    if not db_url:
        print('❌ No database URL configured')
        sys.exit(1)
    
    print('🔧 Connecting to database...')
    db_manager = initialize_database(db_url)
    
    with db_manager.get_cursor() as cursor:
        print('🔍 Checking events table...')
        cursor.execute(\"\"\"
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'events'
            );
        \"\"\")
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            cursor.execute(\"\"\"
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'events' AND column_name = 'id' AND table_schema = 'public'
            \"\"\")
            
            has_id_column = cursor.fetchone() is not None
            
            if has_id_column:
                print('✅ Events table already exists with proper schema!')
                sys.exit(0)
            else:
                print('⚠️ Events table exists but missing id column, fixing...')
        
        print('🔧 Creating events table...')
        cursor.execute(\"\"\"
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                event_date DATE NOT NULL,
                event_time TIMESTAMP NOT NULL,
                event_name TEXT DEFAULT 'Sunday Mining',
                total_participants INTEGER DEFAULT 0,
                total_payout REAL,
                is_open BOOLEAN DEFAULT TRUE,
                payroll_calculated BOOLEAN DEFAULT FALSE,
                pdf_generated BOOLEAN DEFAULT FALSE,
                event_id INTEGER GENERATED ALWAYS AS (id) STORED,
                channel_id TEXT,
                channel_name TEXT,
                start_time TEXT,
                end_time TEXT,
                total_value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_events_guild_id ON events(guild_id);
            CREATE INDEX IF NOT EXISTS idx_events_event_date ON events(event_date);
            CREATE INDEX IF NOT EXISTS idx_events_is_open ON events(is_open);
        \"\"\")
        
        print('✅ Events table created successfully!')
        print('✅ /testdata command should now work properly')
        
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"

echo ""
echo "🎉 Events table fix completed!"
echo "You can now try the /testdata command again."
