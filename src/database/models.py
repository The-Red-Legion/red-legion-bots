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
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    
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
            event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
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
            event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
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
    
    conn.commit()
    conn.close()
    return True
