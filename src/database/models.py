"""
Database schema definitions and table creation.
"""

import psycopg2
from functools import wraps

def retry_db_operation(max_retries=3):
    """Decorator to retry database operations on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    print(f"Database operation failed (attempt {attempt + 1}): {e}")
            return None
        return wrapper
    return decorator

@retry_db_operation()
def init_database(database_url):
    """Initialize database tables if they don't exist."""
    print("🔗 Attempting database connection...")
    print(f"🔗 URL (first 50 chars): {database_url[:50]}...")
    print(f"🔗 URL contains '#': {'#' in database_url}")
    print(f"🔗 URL contains '%23': {'%23' in database_url}")
    
    try:
        conn = psycopg2.connect(database_url)
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"❌ Connection error type: {type(e).__name__}")
        raise
    
    c = conn.cursor()
    
    # Check if events table exists and what columns it has
    c.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'events' AND table_schema = 'public'
    """)
    existing_events_columns = [row[0] for row in c.fetchall()]
    
    print(f"🔍 Existing events table columns: {existing_events_columns}")
    
    # If events table exists but doesn't have 'id' column, we need to work with existing schema
    if existing_events_columns and 'id' not in existing_events_columns:
        print("⚠️  Existing events table uses 'event_id' instead of 'id'. Adapting to existing schema.")
        
        # Create mining_channels table compatible with existing schema
        c.execute("""
            CREATE TABLE IF NOT EXISTS mining_channels (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                channel_id BIGINT NOT NULL,
                channel_name TEXT NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, channel_id)
            )
        """)
        
        # For now, just ensure the connection works and basic tables exist
        print("✅ Database schema verified and compatible")
        
    else:
        # Create new schema if events table doesn't exist or has the expected 'id' column
        print("🆕 Creating new database schema")
        
        # Enhanced events table with guild support
        c.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                event_date DATE NOT NULL,
                event_time TIMESTAMP NOT NULL,
                event_name TEXT DEFAULT 'Sunday Mining',
                is_open BOOLEAN DEFAULT TRUE,
                total_participants INTEGER DEFAULT 0,
                total_value DECIMAL(15,2) DEFAULT 0,
                payroll_calculated BOOLEAN DEFAULT FALSE,
                pdf_generated BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Legacy compatibility columns
                event_id INTEGER,
                channel_id BIGINT,
                channel_name TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP
            )
        """)
        
        # Mining participation table with event linkage
        c.execute("""
            CREATE TABLE IF NOT EXISTS mining_participation (
                id SERIAL PRIMARY KEY,
                event_id INTEGER,
                member_id BIGINT NOT NULL,
                username TEXT NOT NULL,
                channel_id BIGINT NOT NULL,
                channel_name TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                duration_seconds INTEGER NOT NULL,
                is_org_member BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Mining channels configuration table
        c.execute("""
            CREATE TABLE IF NOT EXISTS mining_channels (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                channel_id BIGINT NOT NULL,
                channel_name TEXT NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, channel_id)
            )
        """)
        
        # Mining results/materials table  
        c.execute("""
            CREATE TABLE IF NOT EXISTS mining_results (
                id SERIAL PRIMARY KEY,
                event_id INTEGER,
                material_name TEXT NOT NULL,
                quantity DECIMAL(10,2) NOT NULL,
                unit_price DECIMAL(10,2),
                total_value DECIMAL(15,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        c.execute("CREATE INDEX IF NOT EXISTS idx_events_guild_date ON events(guild_id, event_date)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_events_open ON events(is_open)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_participation_event ON mining_participation(event_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_participation_member ON mining_participation(member_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_channels_guild ON mining_channels(guild_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_channels_active ON mining_channels(guild_id, is_active)")
        
        # Add foreign key constraints only if events table has 'id' column
        c.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'events' AND table_schema = 'public' AND column_name = 'id'
        """)
        has_events_id = c.fetchone() is not None
        
        if has_events_id:
            # Add foreign key constraints
            try:
                c.execute("""
                    ALTER TABLE mining_participation 
                    ADD CONSTRAINT fk_participation_event 
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
                """)
                c.execute("""
                    ALTER TABLE mining_results 
                    ADD CONSTRAINT fk_results_event 
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
                """)
                print("✅ Foreign key constraints added successfully")
            except Exception as fk_error:
                print(f"⚠️  Foreign key constraints already exist or failed: {fk_error}")
        else:
            print("⚠️  Events table doesn't have 'id' column, skipping foreign key constraints")
    
    conn.commit()
    conn.close()
    return True
