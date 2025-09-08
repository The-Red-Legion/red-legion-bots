"""
Database Operations for Red Legion Bot v2.0.0

This module provides CRUD operations and business logic for database entities.
Includes both new architecture classes and legacy compatibility functions.
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import DatabaseManager
from database.models import User, Guild, MiningEvent, MiningParticipation

class BaseOperations:
    """Base class for database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

class UserOperations(BaseOperations):
    """User-related database operations."""
    
    def create_user(self, user: User) -> bool:
        """Create a new user."""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (user_id, username, display_name, first_seen, last_seen, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    display_name = EXCLUDED.display_name,
                    last_seen = EXCLUDED.last_seen,
                    updated_at = CURRENT_TIMESTAMP
            """, (user.user_id, user.username, user.display_name, 
                  user.first_seen, user.last_seen, user.is_active))
            return True
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                return User(**row)
            return None

class GuildOperations(BaseOperations):
    """Guild-related database operations."""
    
    def create_guild(self, guild: Guild) -> bool:
        """Create a new guild."""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO guilds (guild_id, name, owner_id, is_active)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (guild_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    owner_id = EXCLUDED.owner_id,
                    updated_at = CURRENT_TIMESTAMP
            """, (guild.guild_id, guild.name, guild.owner_id, guild.is_active))
            return True
    
    def get_guild(self, guild_id: str) -> Optional[Guild]:
        """Get a guild by ID."""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute("SELECT * FROM guilds WHERE guild_id = %s", (guild_id,))
            row = cursor.fetchone()
            if row:
                return Guild(**row)
            return None

# Legacy functions - these will be properly implemented later
def init_db(database_url):
    """Legacy function - initialize database"""
    from database import init_database
    return init_database()

def get_market_items(database_url):
    """Get all active market items from the database"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Handle database connection with proxy fallback
        parsed = urlparse(database_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            proxy_url = database_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
            except psycopg2.OperationalError:
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)
            
        cursor = conn.cursor()
        cursor.execute("""
            SELECT item_id, name, price, stock, category, description
            FROM market_items 
            WHERE is_active = TRUE 
            ORDER BY category, name
        """)
        
        items = cursor.fetchall()
        conn.close()
        return items
        
    except Exception as e:
        print(f"Error getting market items: {e}")
        return []

def add_market_item(database_url, name, price, stock, guild_id=None, seller_name="Red Legion"):
    """Add a new market item to the database"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Handle database connection with proxy fallback
        parsed = urlparse(database_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            proxy_url = database_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
            except psycopg2.OperationalError:
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)
            
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO market_items (guild_id, name, price, stock, seller_name, category)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING item_id
        """, (guild_id, name, price, stock, seller_name, 'general'))
        
        item_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return item_id
        
    except Exception as e:
        print(f"Error adding market item: {e}")
        raise

def issue_loan(database_url, user_id, username, amount, issued_date_iso, due_date_iso):
    """Issue a new loan to a user"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Handle database connection with proxy fallback
        parsed = urlparse(database_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            proxy_url = database_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
            except psycopg2.OperationalError:
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)
            
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO loans (user_id, username, amount, issued_date_iso, due_date_iso, status, interest_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING loan_id
        """, (user_id, username, amount, issued_date_iso, due_date_iso, 'active', 0.05))
        
        loan_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return loan_id
        
    except Exception as e:
        print(f"Error issuing loan: {e}")
        raise

def get_user_loans(database_url, user_id):
    """Get all loans for a specific user"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Handle database connection with proxy fallback
        parsed = urlparse(database_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            proxy_url = database_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
            except psycopg2.OperationalError:
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)
            
        cursor = conn.cursor()
        cursor.execute("""
            SELECT loan_id, amount, issued_date_iso, due_date_iso, status
            FROM loans 
            WHERE user_id = %s AND status IN ('active', 'overdue')
            ORDER BY issued_date_iso DESC
        """, (user_id,))
        
        loans = cursor.fetchall()
        conn.close()
        return loans
        
    except Exception as e:
        print(f"Error getting user loans: {e}")
        return []

def get_mining_channels_dict(database_url, guild_id):
    """Get mining channels as a dictionary for a specific guild."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Convert database_url to use proxy if running locally
        parsed = urlparse(database_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            # Try proxy first on port 5433
            proxy_url = database_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
            except psycopg2.OperationalError:
                # If proxy fails, try original URL
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)
            
        c = conn.cursor()
        
        # Query mining channels for the guild
        c.execute('''
            SELECT channel_name, channel_id 
            FROM mining_channels 
            WHERE guild_id = %s AND is_active = TRUE
            ORDER BY channel_name
        ''', (guild_id,))
        
        rows = c.fetchall()
        channels_dict = {}
        
        for channel_name, channel_id in rows:
            # Use channel names as-is since they're already in the correct format
            channels_dict[channel_name] = str(channel_id)
        
        conn.close()
        return channels_dict
        
    except Exception as e:
        # If database fails, return empty dict to fall back to hardcoded values
        return {}

def issue_loan(database_url, user_id, amount, issued_date, due_date):
    """Legacy function - issue loan"""
    pass

def save_mining_participation(database_url, *args, **kwargs):
    """Legacy function - save mining participation"""
    pass

def add_mining_channel(database_url, guild_id, channel_id, channel_name, description=None):
    """Legacy function - add mining channel"""
    pass

def remove_mining_channel(database_url, guild_id, channel_id):
    """Legacy function - remove mining channel"""
    return True

def get_mining_channels(database_url, guild_id, active_only=True):
    """Get mining channels as a list for a specific guild."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Convert database_url to use proxy if running locally
        parsed = urlparse(database_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            # Try proxy first on port 5433
            proxy_url = database_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
            except:
                # Fallback to original URL
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)
            
        c = conn.cursor()
        
        # Query mining channels for the guild
        where_clause = "WHERE guild_id = %s"
        params = [guild_id]
        
        if active_only:
            where_clause += " AND is_active = TRUE"
            
        c.execute(f'''
            SELECT channel_id, channel_name, is_active, created_at
            FROM mining_channels 
            {where_clause}
            ORDER BY channel_name
        ''', params)
        
        rows = c.fetchall()
        conn.close()
        return rows
        
    except Exception as e:
        print(f"Error getting mining channels from database: {e}")
        return []

def migrate_schema(database_url):
    """Legacy function - migrate schema"""
    pass

def delete_mining_event(database_url, event_id):
    """Delete a mining event and all related participation records."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Convert database_url to use proxy if running locally
        parsed = urlparse(database_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            proxy_url = database_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
            except psycopg2.OperationalError:
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)
        
        cursor = conn.cursor()
        
        # First, delete related participation records (CASCADE should handle this, but being explicit)
        cursor.execute("DELETE FROM mining_participation WHERE event_id = %s", (event_id,))
        participation_deleted = cursor.rowcount
        
        # Then delete the event itself
        cursor.execute("DELETE FROM mining_events WHERE id = %s", (event_id,))
        event_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if event_deleted > 0:
            print(f"✅ Deleted mining event {event_id} and {participation_deleted} participation records")
            return True
        else:
            print(f"⚠️ No event found with ID {event_id}")
            return False
        
    except Exception as e:
        print(f"❌ Error deleting mining event {event_id}: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def delete_mining_event(database_url, event_id):
    """Delete a mining event and all related participation records."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Convert database_url to use proxy if running locally
        parsed = urlparse(database_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            proxy_url = database_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
            except psycopg2.OperationalError:
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)
        
        cursor = conn.cursor()
        
        # First, delete related participation records (CASCADE should handle this, but being explicit)
        cursor.execute("DELETE FROM mining_participation WHERE event_id = %s", (event_id,))
        participation_deleted = cursor.rowcount
        
        # Then delete the event itself
        cursor.execute("DELETE FROM mining_events WHERE id = %s", (event_id,))
        event_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if event_deleted > 0:
            print(f"✅ Deleted mining event {event_id} and {participation_deleted} participation records")
            return True
        else:
            print(f"⚠️ No event found with ID {event_id}")
            return False
        
    except Exception as e:
        print(f"❌ Error deleting mining event {event_id}: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def close_mining_event(database_url, event_id, total_value=None):
    """Close a mining event and update its status to completed."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Convert database_url to use proxy if running locally
        parsed = urlparse(database_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            proxy_url = database_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
            except psycopg2.OperationalError:
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)
        
        cursor = conn.cursor()
        
        # Update the event status to completed
        if total_value is not None:
            cursor.execute("""
                UPDATE mining_events 
                SET status = 'completed', total_value_auec = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (total_value, event_id))
        else:
            cursor.execute("""
                UPDATE mining_events 
                SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (event_id,))
        
        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        if rows_updated > 0:
            print(f"✅ Closed mining event {event_id}" + (f" with total value {total_value}" if total_value else ""))
            return True
        else:
            print(f"⚠️ No event found with ID {event_id}")
            return False
        
    except Exception as e:
        print(f"❌ Error closing mining event {event_id}: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def mark_pdf_generated(database_url, event_id):
    """Legacy function - mark PDF generated"""
    pass

def get_mining_session_participants(database_url, *args, **kwargs):
    """Legacy function - get mining session participants"""
    return []

def create_adhoc_mining_event(database_url, guild_id, organizer_id, organizer_name, event_name, description=None, start_time=None):
    """Create an adhoc mining event."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        from datetime import datetime, timezone
        
        # Convert database_url to use proxy if running locally
        parsed = urlparse(database_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            proxy_url = database_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
            except psycopg2.OperationalError:
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)
        
        cursor = conn.cursor()
        
        # Use provided start_time or current time
        if start_time is None:
            start_time = datetime.now(timezone.utc)
        
        cursor.execute("""
            INSERT INTO mining_events (
                guild_id, organizer_id, organizer_name, event_name, event_type,
                description, start_time, status, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            guild_id, organizer_id, organizer_name, event_name, 'adhoc',
            description, start_time, 'active', 
            datetime.now(timezone.utc), datetime.now(timezone.utc)
        ))
        
        event_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        print(f"✅ Created adhoc mining event '{event_name}' with ID {event_id}")
        return event_id
        
    except Exception as e:
        print(f"❌ Error creating adhoc mining event: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None

def get_open_mining_events(database_url, guild_id=None):
    """Get open/active mining events from the database."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Convert database_url to use proxy if running locally
        parsed = urlparse(database_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            proxy_url = database_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
            except psycopg2.OperationalError:
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)
        
        cursor = conn.cursor()
        
        if guild_id:
            # Get open events for specific guild
            cursor.execute("""
                SELECT id, guild_id, event_date, event_time, event_name, status,
                       total_participants, total_value_auec, payroll_processed, pdf_generated,
                       created_at, updated_at
                FROM mining_events 
                WHERE guild_id = %s AND status IN ('planned', 'active')
                ORDER BY event_time DESC
            """, (guild_id,))
        else:
            # Get all open events
            cursor.execute("""
                SELECT id, guild_id, event_date, event_time, event_name, status,
                       total_participants, total_value_auec, payroll_processed, pdf_generated,
                       created_at, updated_at
                FROM mining_events 
                WHERE status IN ('planned', 'active')
                ORDER BY event_time DESC
            """)
        
        events = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries for easier handling
        event_list = []
        for event in events:
            event_list.append({
                'id': event[0],
                'guild_id': event[1],
                'event_date': event[2],
                'event_time': event[3],
                'event_name': event[4],
                'status': event[5],
                'total_participants': event[6],
                'total_value_auec': event[7],
                'payroll_processed': event[8],
                'pdf_generated': event[9],
                'created_at': event[10],
                'updated_at': event[11]
            })
        
        print(f"✅ Retrieved {len(event_list)} open mining events" + (f" for guild {guild_id}" if guild_id else ""))
        return event_list
        
    except Exception as e:
        print(f"❌ Error getting open mining events: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return []

def save_event(database_url, channel_id, channel_name, event_name, start_time):
    """Legacy function - save event"""
    pass

def update_event_end_time(database_url, channel_id, end_time):
    """Legacy function - update event end time"""
    pass

def get_mining_events(database_url, guild_id, event_date=None):
    """Get mining events from the database."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        from datetime import date
        
        # Convert database_url to use proxy if running locally
        parsed = urlparse(database_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            proxy_url = database_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
            except psycopg2.OperationalError:
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)
        
        cursor = conn.cursor()
        
        if event_date:
            # Get events for specific date
            cursor.execute("""
                SELECT id, guild_id, event_date, event_time, event_name, status,
                       total_participants, total_value_auec, payroll_processed, pdf_generated,
                       created_at, updated_at
                FROM mining_events 
                WHERE guild_id = %s AND event_date = %s
                ORDER BY event_time DESC
            """, (guild_id, event_date))
        else:
            # Get recent events (last 30 days)
            cursor.execute("""
                SELECT id, guild_id, event_date, event_time, event_name, status,
                       total_participants, total_value_auec, payroll_processed, pdf_generated,
                       created_at, updated_at
                FROM mining_events 
                WHERE guild_id = %s AND event_date >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY event_time DESC
            """, (guild_id,))
        
        events = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries for easier handling
        event_list = []
        for event in events:
            event_list.append({
                'id': event[0],
                'guild_id': event[1],
                'event_date': event[2],
                'event_time': event[3],
                'event_name': event[4],
                'status': event[5],
                'total_participants': event[6],
                'total_value_auec': event[7],
                'payroll_processed': event[8],
                'pdf_generated': event[9],
                'created_at': event[10],
                'updated_at': event[11]
            })
        
        print(f"✅ Retrieved {len(event_list)} mining events for guild {guild_id}")
        return event_list
        
    except Exception as e:
        print(f"❌ Error getting mining events: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return []

def update_entries(database_url, member_id, month_year):
    """Legacy function - update entries"""
    pass

def get_entries(database_url, month_year):
    """Legacy function - get entries"""
    return []

__all__ = [
    'init_db',
    'get_market_items',
    'add_market_item',
    'get_mining_channels_dict',
    'issue_loan',
    'get_user_loans',
    'save_mining_participation',
    'add_mining_channel',
    'remove_mining_channel',
    'get_mining_channels',
    'migrate_schema',
    'close_mining_event',
    'mark_pdf_generated',
    'get_mining_session_participants',
    'create_mining_event',
    'get_open_mining_events',
    'save_event',
    'update_event_end_time',
    'get_mining_events',
    'update_entries',
    'get_entries',
]
