import psycopg2
import time
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
        event_id SERIAL PRIMARY KEY,
        channel_id TEXT,
        channel_name TEXT,
        event_name TEXT,
        start_time TEXT,
        end_time TEXT,
        total_value REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS event_materials (
        event_id INTEGER,
        material_type TEXT,
        scu_refined INTEGER,
        material_value REAL,
        PRIMARY KEY (event_id, material_type),
        FOREIGN KEY (event_id) REFERENCES events(event_id)
    )''')
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
    conn.commit()
    conn.close()

@retry_db_operation()
def save_participation(database_url, channel_id, member_id, username, duration, is_org_member):
    conn = psycopg2.connect(database_url)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO participation (
            channel_id, member_id, username, duration, is_org_member
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (channel_id, member_id)
        DO UPDATE SET duration = EXCLUDED.duration,
                    username = EXCLUDED.username,
                    is_org_member = EXCLUDED.is_org_member
        """,
        (str(channel_id), str(member_id), username, duration, is_org_member)
    )
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