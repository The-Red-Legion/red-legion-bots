"""
Database Schemas for Red Legion Bot v2.0.0

This module contains SQL schema definitions and initialization functions
for the complete database architecture.
"""

from .connection import DatabaseManager

def init_database(database_url=None):
    """
    Initialize the database with the complete schema.
    
    Args:
        database_url (str, optional): PostgreSQL connection URL.
                                     If not provided, will try to get from config.
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if database_url is None:
            # Try to get from environment or config
            import os
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                try:
                    from config.settings import get_database_url
                    database_url = get_database_url()
                except ImportError:
                    pass
            
            if not database_url:
                raise ValueError("No database URL provided and none found in configuration")
        
        # Initialize the global database manager first
        from .connection import initialize_database
        db_manager = initialize_database(database_url)
        
        with db_manager.get_cursor() as cursor:
            # Create schema SQL
            schema_sql = """
            -- Users table
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(20) PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                display_name VARCHAR(100),
                first_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Guilds table
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                owner_id VARCHAR(20),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Guild memberships table
            CREATE TABLE IF NOT EXISTS guild_memberships (
                membership_id SERIAL PRIMARY KEY,
                guild_id VARCHAR(20) REFERENCES guilds(guild_id),
                user_id VARCHAR(20) REFERENCES users(user_id),
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                left_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                roles TEXT[],
                nickname VARCHAR(100),
                UNIQUE(guild_id, user_id)
            );
            
            -- Mining channels table
            CREATE TABLE IF NOT EXISTS mining_channels (
                channel_id VARCHAR(20) PRIMARY KEY,
                guild_id VARCHAR(20) REFERENCES guilds(guild_id),
                name VARCHAR(100) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Mining events table
            CREATE TABLE IF NOT EXISTS mining_events (
                event_id SERIAL PRIMARY KEY,
                guild_id VARCHAR(20) REFERENCES guilds(guild_id),
                name VARCHAR(200) NOT NULL,
                event_date DATE NOT NULL,
                location VARCHAR(200),
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Mining participation table
            CREATE TABLE IF NOT EXISTS mining_participation (
                participation_id SERIAL PRIMARY KEY,
                event_id INTEGER REFERENCES mining_events(event_id),
                user_id VARCHAR(20) REFERENCES users(user_id),
                channel_id VARCHAR(20) REFERENCES mining_channels(channel_id),
                join_time TIMESTAMP NOT NULL,
                leave_time TIMESTAMP,
                duration_minutes INTEGER DEFAULT 0,
                is_valid BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Materials table
            CREATE TABLE IF NOT EXISTS materials (
                material_id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                category VARCHAR(50),
                base_value DECIMAL(10,2),
                rarity VARCHAR(20),
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Mining yields table
            CREATE TABLE IF NOT EXISTS mining_yields (
                yield_id SERIAL PRIMARY KEY,
                participation_id INTEGER REFERENCES mining_participation(participation_id),
                material_id INTEGER REFERENCES materials(material_id),
                quantity DECIMAL(10,3) NOT NULL,
                quality_grade VARCHAR(10),
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Loans table
            CREATE TABLE IF NOT EXISTS loans (
                loan_id SERIAL PRIMARY KEY,
                user_id VARCHAR(20) REFERENCES users(user_id),
                guild_id VARCHAR(20) REFERENCES guilds(guild_id),
                amount DECIMAL(15,2) NOT NULL,
                interest_rate DECIMAL(5,4) DEFAULT 0.0000,
                issued_date DATE NOT NULL,
                due_date DATE NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                paid_amount DECIMAL(15,2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_mining_participation_user_id ON mining_participation(user_id);
            CREATE INDEX IF NOT EXISTS idx_mining_participation_event_id ON mining_participation(event_id);
            CREATE INDEX IF NOT EXISTS idx_mining_participation_join_time ON mining_participation(join_time);
            CREATE INDEX IF NOT EXISTS idx_guild_memberships_guild_user ON guild_memberships(guild_id, user_id);
            CREATE INDEX IF NOT EXISTS idx_loans_user_id ON loans(user_id);
            CREATE INDEX IF NOT EXISTS idx_mining_yields_participation ON mining_yields(participation_id);
            """
            
            cursor.execute(schema_sql)
            
        print("✅ Database schema initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database schema initialization failed: {e}")
        return False
