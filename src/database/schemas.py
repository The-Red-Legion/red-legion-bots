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
                guild_id VARCHAR(20),
                user_id VARCHAR(20),
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
                guild_id VARCHAR(20),
                name VARCHAR(100) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Mining events table (enhanced for comprehensive event management)
            CREATE TABLE IF NOT EXISTS mining_events (
                event_id SERIAL PRIMARY KEY,
                guild_id VARCHAR(20),
                name VARCHAR(200) NOT NULL,
                event_date DATE NOT NULL,
                location VARCHAR(200),
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                -- Enhanced event management columns
                organizer_id VARCHAR(20),
                organizer_name VARCHAR(100),
                event_type VARCHAR(50) DEFAULT 'mining',
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                status VARCHAR(20) DEFAULT 'planned',
                total_value_auec BIGINT
            );
            
            -- Events table (for participation tracking and payroll)
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
                -- Legacy columns for backward compatibility
                event_id INTEGER GENERATED ALWAYS AS (id) STORED,
                channel_id TEXT,
                channel_name TEXT,
                start_time TEXT,
                end_time TEXT,
                total_value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Mining participation table (foreign keys added separately to avoid order issues)
            CREATE TABLE IF NOT EXISTS mining_participation (
                participation_id SERIAL PRIMARY KEY,
                event_id INTEGER,
                user_id VARCHAR(20),
                channel_id VARCHAR(20),
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
                participation_id INTEGER,
                material_id INTEGER,
                quantity DECIMAL(10,3) NOT NULL,
                quality_grade VARCHAR(10),
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Loans table
            CREATE TABLE IF NOT EXISTS loans (
                loan_id SERIAL PRIMARY KEY,
                user_id VARCHAR(20),
                guild_id VARCHAR(20),
                amount DECIMAL(15,2) NOT NULL,
                interest_rate DECIMAL(5,4) DEFAULT 0.0000,
                issued_date DATE NOT NULL,
                due_date DATE NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                paid_amount DECIMAL(15,2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Create indexes for performance (mining_participation indexes created separately)
            CREATE INDEX IF NOT EXISTS idx_guild_memberships_guild_user ON guild_memberships(guild_id, user_id);
            CREATE INDEX IF NOT EXISTS idx_loans_user_id ON loans(user_id);
            CREATE INDEX IF NOT EXISTS idx_mining_yields_participation ON mining_yields(participation_id);
            CREATE INDEX IF NOT EXISTS idx_events_guild_id ON events(guild_id);
            CREATE INDEX IF NOT EXISTS idx_events_event_date ON events(event_date);
            CREATE INDEX IF NOT EXISTS idx_events_is_open ON events(is_open);
            -- Enhanced mining_events indexes
            CREATE INDEX IF NOT EXISTS idx_mining_events_organizer ON mining_events(organizer_id);
            CREATE INDEX IF NOT EXISTS idx_mining_events_type ON mining_events(event_type);
            CREATE INDEX IF NOT EXISTS idx_mining_events_status ON mining_events(status);
            CREATE INDEX IF NOT EXISTS idx_mining_events_start_time ON mining_events(start_time);
            
            -- Event categories lookup table
            CREATE TABLE IF NOT EXISTS event_categories (
                category_id SERIAL PRIMARY KEY,
                category_name VARCHAR(50) UNIQUE NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Insert standard event categories
            INSERT INTO event_categories (category_name, display_name, description) 
            VALUES 
                ('mining', 'Mining Operations', 'Resource extraction and mining activities'),
                ('training', 'Training Sessions', 'Skills training and educational activities'),
                ('combat_operations', 'Combat Operations', 'Military operations and combat missions'),
                ('salvage', 'Salvage Operations', 'Salvage and recovery missions'),
                ('misc', 'Miscellaneous', 'Other organization events and activities')
            ON CONFLICT (category_name) DO NOTHING;
            
            -- Add constraints for data validation (done separately to handle existing data)
            DO $$
            BEGIN
                -- Add event type constraint if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                              WHERE constraint_name = 'chk_event_type') THEN
                    ALTER TABLE mining_events 
                    ADD CONSTRAINT chk_event_type 
                    CHECK (event_type IN ('mining', 'training', 'combat_operations', 'salvage', 'misc'));
                END IF;
                
                -- Add status constraint if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                              WHERE constraint_name = 'chk_status') THEN
                    ALTER TABLE mining_events 
                    ADD CONSTRAINT chk_status 
                    CHECK (status IN ('planned', 'active', 'completed', 'cancelled'));
                END IF;
            END $$;
            
            -- Market items table for red-market commands
            CREATE TABLE IF NOT EXISTS market_items (
                item_id SERIAL PRIMARY KEY,
                guild_id VARCHAR(20),
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price DECIMAL(15,2) NOT NULL CHECK (price > 0),
                stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
                category VARCHAR(50) DEFAULT 'general',
                seller_id VARCHAR(20),
                seller_name VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Bot configuration table for red-config commands
            CREATE TABLE IF NOT EXISTS bot_config (
                config_id SERIAL PRIMARY KEY,
                guild_id VARCHAR(20),
                config_key VARCHAR(100) NOT NULL,
                config_value TEXT,
                config_type VARCHAR(20) DEFAULT 'string',
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, config_key)
            );

            -- Command usage tracking for analytics
            CREATE TABLE IF NOT EXISTS command_usage (
                usage_id SERIAL PRIMARY KEY,
                guild_id VARCHAR(20),
                user_id VARCHAR(20),
                command_name VARCHAR(100) NOT NULL,
                command_type VARCHAR(20) DEFAULT 'slash',
                success BOOLEAN DEFAULT TRUE,
                execution_time_ms INTEGER,
                error_message TEXT,
                parameters JSON,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Admin actions log for red-admin commands
            CREATE TABLE IF NOT EXISTS admin_actions (
                action_id SERIAL PRIMARY KEY,
                guild_id VARCHAR(20),
                admin_id VARCHAR(20),
                admin_name VARCHAR(100),
                action_type VARCHAR(50) NOT NULL,
                target_resource VARCHAR(100),
                action_details JSON,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Additional indexes for new tables
            CREATE INDEX IF NOT EXISTS idx_market_items_guild ON market_items(guild_id);
            CREATE INDEX IF NOT EXISTS idx_market_items_active ON market_items(is_active);
            CREATE INDEX IF NOT EXISTS idx_bot_config_guild_key ON bot_config(guild_id, config_key);
            CREATE INDEX IF NOT EXISTS idx_command_usage_guild ON command_usage(guild_id);
            CREATE INDEX IF NOT EXISTS idx_command_usage_command ON command_usage(command_name);
            CREATE INDEX IF NOT EXISTS idx_admin_actions_guild ON admin_actions(guild_id);
            CREATE INDEX IF NOT EXISTS idx_admin_actions_type ON admin_actions(action_type);
            
            -- Foreign key constraints will be added separately after schema creation
            """
            
            # Drop ALL existing tables to ensure clean slate (order matters due to dependencies)
            print("🧹 Dropping all existing tables for clean recreation...")
            drop_tables = [
                "DROP TABLE IF EXISTS mining_yields CASCADE;",
                "DROP TABLE IF EXISTS mining_participation CASCADE;",
                "DROP TABLE IF EXISTS admin_actions CASCADE;", 
                "DROP TABLE IF EXISTS command_usage CASCADE;",
                "DROP TABLE IF EXISTS bot_config CASCADE;",
                "DROP TABLE IF EXISTS market_items CASCADE;",
                "DROP TABLE IF EXISTS loans CASCADE;",
                "DROP TABLE IF EXISTS materials CASCADE;",
                "DROP TABLE IF EXISTS events CASCADE;",
                "DROP TABLE IF EXISTS mining_events CASCADE;",
                "DROP TABLE IF EXISTS mining_channels CASCADE;",
                "DROP TABLE IF EXISTS guild_memberships CASCADE;",
                "DROP TABLE IF EXISTS guilds CASCADE;",
                "DROP TABLE IF EXISTS users CASCADE;"
            ]
            
            for drop_sql in drop_tables:
                try:
                    cursor.execute(drop_sql)
                    table_name = drop_sql.split("DROP TABLE IF EXISTS ")[1].split(" CASCADE")[0]
                    print(f"✅ Dropped table: {table_name}")
                except Exception as e:
                    print(f"Info: Drop table failed (may not exist): {e}")
            
            print("🧹 All tables dropped, creating fresh schema...")
            
            # Execute schema creation with better error handling
            print("🔧 Creating database schema...")
            try:
                cursor.execute(schema_sql)
                print("✅ Schema SQL executed successfully")
            except Exception as e:
                print(f"❌ Schema SQL execution failed: {e}")
                # Try to get more specific error information
                import traceback
                traceback.print_exc()
                raise
            
            # Add foreign key constraints with error handling
            fk_constraints = [
                # Guild memberships foreign keys
                ("fk_guild_memberships_guild", "ALTER TABLE guild_memberships ADD CONSTRAINT fk_guild_memberships_guild FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)"),
                ("fk_guild_memberships_user", "ALTER TABLE guild_memberships ADD CONSTRAINT fk_guild_memberships_user FOREIGN KEY (user_id) REFERENCES users(user_id)"),
                
                # Mining channels foreign keys
                ("fk_mining_channels_guild", "ALTER TABLE mining_channels ADD CONSTRAINT fk_mining_channels_guild FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)"),
                
                # Mining events foreign keys
                ("fk_mining_events_guild", "ALTER TABLE mining_events ADD CONSTRAINT fk_mining_events_guild FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)"),
                
                # Mining participation foreign keys (keeping existing ones)
                ("fk_mining_participation_event", "ALTER TABLE mining_participation ADD CONSTRAINT fk_mining_participation_event FOREIGN KEY (event_id) REFERENCES mining_events(event_id)"),
                ("fk_mining_participation_user", "ALTER TABLE mining_participation ADD CONSTRAINT fk_mining_participation_user FOREIGN KEY (user_id) REFERENCES users(user_id)"),
                ("fk_mining_participation_channel", "ALTER TABLE mining_participation ADD CONSTRAINT fk_mining_participation_channel FOREIGN KEY (channel_id) REFERENCES mining_channels(channel_id)"),
                
                # Mining yields foreign keys
                ("fk_mining_yields_participation", "ALTER TABLE mining_yields ADD CONSTRAINT fk_mining_yields_participation FOREIGN KEY (participation_id) REFERENCES mining_participation(participation_id)"),
                ("fk_mining_yields_material", "ALTER TABLE mining_yields ADD CONSTRAINT fk_mining_yields_material FOREIGN KEY (material_id) REFERENCES materials(material_id)"),
                
                # Loans foreign keys
                ("fk_loans_user", "ALTER TABLE loans ADD CONSTRAINT fk_loans_user FOREIGN KEY (user_id) REFERENCES users(user_id)"),
                ("fk_loans_guild", "ALTER TABLE loans ADD CONSTRAINT fk_loans_guild FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)"),
                
                # Market items foreign keys
                ("fk_market_items_guild", "ALTER TABLE market_items ADD CONSTRAINT fk_market_items_guild FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)"),
                
                # Bot configuration foreign keys
                ("fk_bot_config_guild", "ALTER TABLE bot_config ADD CONSTRAINT fk_bot_config_guild FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)"),
                
                # Command usage foreign keys
                ("fk_command_usage_guild", "ALTER TABLE command_usage ADD CONSTRAINT fk_command_usage_guild FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)"),
                ("fk_command_usage_user", "ALTER TABLE command_usage ADD CONSTRAINT fk_command_usage_user FOREIGN KEY (user_id) REFERENCES users(user_id)"),
                
                # Admin actions foreign keys
                ("fk_admin_actions_guild", "ALTER TABLE admin_actions ADD CONSTRAINT fk_admin_actions_guild FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)"),
                ("fk_admin_actions_admin", "ALTER TABLE admin_actions ADD CONSTRAINT fk_admin_actions_admin FOREIGN KEY (admin_id) REFERENCES users(user_id)")
            ]
            
            for constraint_name, constraint_sql in fk_constraints:
                try:
                    cursor.execute(constraint_sql)
                    print(f"✅ Added foreign key constraint: {constraint_name}")
                except Exception as e:
                    print(f"⚠️ Foreign key constraint {constraint_name} failed (may already exist): {e}")
                    # Continue with other constraints
            
            # Add mining_participation indexes separately
            mp_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_mining_participation_user_id ON mining_participation(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_mining_participation_event_id ON mining_participation(event_id)",
                "CREATE INDEX IF NOT EXISTS idx_mining_participation_join_time ON mining_participation(join_time)"
            ]
            
            for index_sql in mp_indexes:
                try:
                    cursor.execute(index_sql)
                    print(f"✅ Created mining_participation index")
                except Exception as e:
                    print(f"⚠️ Mining_participation index creation failed: {e}")
                    # Continue with other indexes
            
        print("✅ Database schema initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database schema initialization failed: {e}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        return False
