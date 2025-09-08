import psycopg2
import time
from datetime import datetime
from functools import wraps

def retry_db_operation(max_attempts=3, delay=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except psycopg2.OperationalError as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise e
                    print(f"Database error: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
            return func(*args, **kwargs)
        return wrapper
    return decorator

@retry_db_operation()
def init_db(database_url):
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS entries (
        user_id TEXT,
        month_year TEXT,
        entry_count INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, month_year)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS events (
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
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS event_materials (
        event_id INTEGER,
        material_type TEXT,
        scu_refined INTEGER,
        material_value REAL,
        PRIMARY KEY (event_id, material_type),
        FOREIGN KEY (event_id) REFERENCES events(event_id)
    )''')
    # Legacy participation table - use mining_participation instead
    c.execute('''CREATE TABLE IF NOT EXISTS participation (
        channel_id TEXT,
        member_id TEXT,
        username TEXT,
        duration REAL,
        is_org_member BOOLEAN,
        UNIQUE (channel_id, member_id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS market_items (
        item_id SERIAL PRIMARY KEY,
        name TEXT,
        price INTEGER,
        stock INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS loans (
        loan_id SERIAL PRIMARY KEY,
        user_id TEXT,
        amount INTEGER,
        issued_date TEXT,
        due_date TEXT,
        repaid BOOLEAN DEFAULT FALSE
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS mining_channels (
        id SERIAL PRIMARY KEY,
        guild_id BIGINT NOT NULL,
        channel_id BIGINT NOT NULL,
        channel_name TEXT NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(guild_id, channel_id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS mining_participation (
        id SERIAL PRIMARY KEY,
        event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
        member_id BIGINT NOT NULL,
        username TEXT NOT NULL,
        channel_id BIGINT NOT NULL,
        channel_name TEXT NOT NULL,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        duration_seconds INTEGER NOT NULL,
        is_org_member BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        -- Legacy columns for compatibility
        session_duration INTEGER GENERATED ALWAYS AS (duration_seconds) STORED,
        total_session_time INTEGER,
        primary_channel_id BIGINT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

@retry_db_operation()
def save_event(database_url, channel_id, channel_name, event_name, start_time):
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO events (
            channel_id, channel_name, event_name, start_time
        )
        VALUES (%s, %s, %s, %s)
        """,
        (str(channel_id), channel_name, event_name, start_time)
    )
    conn.commit()
    conn.close()

@retry_db_operation()
def update_event_end_time(database_url, channel_id, end_time):
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute(
        """
        UPDATE events SET end_time = %s
        WHERE channel_id = %s::text AND end_time IS NULL
        """,
        (end_time, str(channel_id))
    )
    conn.commit()
    conn.close()

@retry_db_operation()
def create_mining_event(database_url, guild_id, event_date=None, event_name="Sunday Mining"):
    """Create a new mining event and return the event_id."""
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    
    # Use provided date or current date
    if event_date is None:
        event_date = datetime.now().date()
    
    # Set event time to 2 PM on the event date
    event_time = datetime.combine(event_date, datetime.min.time().replace(hour=14))
    
    c.execute(
        """
        INSERT INTO events (
            guild_id, event_date, event_time, event_name, is_open, 
            total_participants, payroll_calculated, pdf_generated
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (guild_id, event_date, event_time, event_name, True, 0, False, False)
    )
    event_id = c.fetchone()[0]
    conn.commit()
    conn.close()
    return event_id

@retry_db_operation()
def close_mining_event(database_url, event_id, total_value=None):
    """Close a mining event and mark payroll as calculated."""
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute(
        """
        UPDATE events SET 
            is_open = FALSE,
            payroll_calculated = TRUE,
            total_payout = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (total_value, event_id)
    )
    conn.commit()
    conn.close()

@retry_db_operation()
def mark_pdf_generated(database_url, event_id):
    """Mark that PDF has been generated for an event."""
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute(
        """
        UPDATE events SET 
            pdf_generated = TRUE,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (event_id,)
    )
    conn.commit()
    conn.close()

@retry_db_operation()
def get_open_mining_events(database_url, guild_id=None):
    """Get all open mining events, optionally filtered by guild."""
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    if guild_id:
        c.execute(
            """
            SELECT id, event_name, event_time, event_date, total_participants
            FROM events 
            WHERE guild_id = %s AND is_open = TRUE 
               AND (event_name ILIKE '%mining%' OR event_name ILIKE '%sunday%')
            ORDER BY event_date DESC, event_time DESC
            """,
            (guild_id,)
        )
    else:
        c.execute(
            """
            SELECT id, event_name, event_time, event_date, total_participants
            FROM events 
            WHERE is_open = TRUE 
               AND (event_name ILIKE '%mining%' OR event_name ILIKE '%sunday%')
            ORDER BY event_date DESC, event_time DESC
            """
        )
    events = c.fetchall()
    conn.close()
    return events

@retry_db_operation()
def get_mining_events(database_url, guild_id, event_date=None):
    """Get mining events for a guild, optionally filtered by date."""
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    if event_date:
        c.execute(
            """
            SELECT id, event_name, event_time, event_date, total_participants, 
                   total_payout, is_open, payroll_calculated, pdf_generated
            FROM events 
            WHERE guild_id = %s AND event_date = %s
               AND (event_name ILIKE '%mining%' OR event_name ILIKE '%sunday%')
            ORDER BY event_time DESC
            """,
            (guild_id, event_date)
        )
    else:
        c.execute(
            """
            SELECT id, event_name, event_time, event_date, total_participants,
                   total_payout, is_open, payroll_calculated, pdf_generated
            FROM events 
            WHERE guild_id = %s
               AND (event_name ILIKE '%mining%' OR event_name ILIKE '%sunday%')
            ORDER BY event_date DESC, event_time DESC
            LIMIT 10
            """,
            (guild_id,)
        )
    events = c.fetchall()
    conn.close()
    return events

@retry_db_operation()
def update_entries(database_url, member_id, month_year):
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO entries (
            user_id, month_year, entry_count
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, month_year)
        DO UPDATE SET entry_count = entries.entry_count + 1
        """,
        (str(member_id), month_year, 1)
    )
    conn.commit()
    conn.close()

@retry_db_operation()
def get_entries(database_url, month_year):
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute(
        """
        SELECT user_id, entry_count FROM entries
        WHERE month_year = %s
        """,
        (month_year,)
    )
    entries = c.fetchall()
    conn.close()
    return entries

@retry_db_operation()
def add_market_item(database_url, name, price, stock):
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO market_items (name, price, stock)
        VALUES (%s, %s, %s)
        """,
        (name, price, stock)
    )
    conn.commit()
    conn.close()

@retry_db_operation()
def get_market_items(database_url):
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute("SELECT item_id, name, price, stock FROM market_items")
    items = c.fetchall()
    conn.close()
    return items

@retry_db_operation()
def issue_loan(database_url, user_id, amount, issued_date, due_date):
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO loans (user_id, amount, issued_date, due_date)
        VALUES (%s, %s, %s, %s)
        """,
        (str(user_id), amount, issued_date, due_date)
    )
    conn.commit()
    conn.close()

@retry_db_operation()
def update_mining_results(database_url, event_id, materials):
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    total_value = 0
    for material_type, scu_refined, material_value in materials:
        if scu_refined > 0:
            c.execute(
                """
                INSERT INTO event_materials (event_id, material_type, scu_refined, material_value)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (event_id, material_type)
                DO UPDATE SET scu_refined = EXCLUDED.scu_refined, material_value = EXCLUDED.material_value
                """,
                (event_id, material_type, scu_refined, material_value)
            )
        total_value += material_value
    c.execute(
        """
        UPDATE events
        SET total_value = %s
        WHERE event_id = %s
        """,
        (total_value, event_id)
    )
    conn.commit()
    conn.close()

@retry_db_operation()
def get_events(database_url, limit=10):
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute(
        """
        SELECT event_id, event_name, channel_name, start_time, end_time, total_value
        FROM events
        ORDER BY start_time DESC
        LIMIT %s
        """,
        (limit,)
    )
    events = c.fetchall()
    conn.close()
    return events

@retry_db_operation()
def get_open_events(database_url, channel_id):
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute(
        """
        SELECT event_id, event_name, channel_name, start_time
        FROM events
        WHERE channel_id = %s AND end_time IS NULL
        ORDER BY start_time DESC
        """,
        (str(channel_id),)
    )
    events = c.fetchall()
    conn.close()
    return events

# Mining Channel Management Functions
@retry_db_operation()
def add_mining_channel(database_url, guild_id, channel_id, channel_name, description=None):
    """Add a new mining channel to the database."""
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO mining_channels (guild_id, channel_id, channel_name, description, is_active)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (guild_id, channel_id)
        DO UPDATE SET 
            channel_name = EXCLUDED.channel_name,
            description = EXCLUDED.description,
            is_active = EXCLUDED.is_active,
            updated_at = CURRENT_TIMESTAMP
        """,
        (guild_id, int(channel_id), channel_name, description, True)
    )
    conn.commit()
    conn.close()

@retry_db_operation()
def remove_mining_channel(database_url, guild_id, channel_id):
    """Remove a mining channel from the database."""
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute(
        """
        UPDATE mining_channels 
        SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
        WHERE guild_id = %s AND channel_id = %s
        """,
        (guild_id, int(channel_id))
    )
    rows_affected = c.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

@retry_db_operation()
def get_mining_channels(database_url, guild_id=None, active_only=True):
    """Get all mining channels from the database."""
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    
    if guild_id:
        if active_only:
            c.execute(
                """
                SELECT channel_id, channel_name, description, created_at
                FROM mining_channels
                WHERE guild_id = %s AND is_active = TRUE
                ORDER BY channel_name
                """,
                (guild_id,)
            )
        else:
            c.execute(
                """
                SELECT channel_id, channel_name, description, is_active, created_at
                FROM mining_channels
                WHERE guild_id = %s
                ORDER BY channel_name
                """,
                (guild_id,)
            )
    else:
        if active_only:
            c.execute(
                """
                SELECT channel_id, channel_name, description, created_at
                FROM mining_channels
                WHERE is_active = TRUE
                ORDER BY channel_name
                """
            )
        else:
            c.execute(
                """
                SELECT channel_id, channel_name, description, is_active, created_at
                FROM mining_channels
                ORDER BY channel_name
                """
            )
    
    channels = c.fetchall()
    conn.close()
    return channels

@retry_db_operation()
def get_mining_channels_dict(database_url, guild_id=None):
    """Get mining channels as a dictionary for easy lookup."""
    channels = get_mining_channels(database_url, guild_id, active_only=True)
    return {
        channel[1].lower().replace(' ', '_'): channel[0]  # channel_name: channel_id
        for channel in channels
    }

@retry_db_operation()
def save_mining_participation(database_url, event_id, member_id, username, channel_id, channel_name, start_time, end_time, duration_seconds, is_org_member):
    """Save enhanced mining participation data with event linkage."""
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO mining_participation (
            event_id, member_id, username, channel_id, channel_name, 
            start_time, end_time, duration_seconds, is_org_member
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (event_id, int(member_id), username, int(channel_id), channel_name, 
         start_time, end_time, duration_seconds, is_org_member)
    )
    conn.commit()
    conn.close()

@retry_db_operation()
def get_mining_session_participants(database_url, event_id=None, hours_back=8):
    """Get mining participants with aggregated time data."""
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    
    if event_id:
        # Get participants for a specific event
        c.execute(
            """
            SELECT 
                member_id,
                username,
                SUM(duration_seconds) as total_time,
                channel_id as primary_channel_id,
                MAX(created_at) as last_activity,
                is_org_member
            FROM mining_participation 
            WHERE event_id = %s
            GROUP BY member_id, username, channel_id, is_org_member
            ORDER BY total_time DESC
            """,
            (event_id,)
        )
    else:
        # Get recent participants across all events
        c.execute(
            """
            SELECT 
                member_id,
                username,
                SUM(duration_seconds) as total_time,
                channel_id as primary_channel_id,
                MAX(created_at) as last_activity,
                is_org_member
            FROM mining_participation 
            WHERE created_at >= NOW() - INTERVAL '%s hours'
            GROUP BY member_id, username, channel_id, is_org_member
            ORDER BY total_time DESC
            """,
            (hours_back,)
        )
    
    participants = c.fetchall()
    conn.close()
    return participants