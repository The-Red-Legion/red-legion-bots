"""
Database Operations for Red Legion Bot v2.0.0

This module provides CRUD operations and business logic for database entities.
Includes both new architecture classes and legacy compatibility functions.
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import random
import string

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import DatabaseManager, resolve_database_url
from database.models import User, Guild, MiningEvent, MiningParticipation

# Event ID Prefix Configuration
EVENT_ID_PREFIXES = {
    'mining': 'sm',        # Sunday Mining
    'operation': 'op',     # Military Operations  
    'training': 'tr',      # Training Events
    'social': 'sc',        # Social Events
    'tournament': 'tm',    # Tournaments
    'expedition': 'ex',    # Exploration Expeditions
    'test': 'test'         # Test Events
}

def generate_prefixed_event_id(event_type: str = 'mining', length: int = 6) -> str:
    """
    Generate a prefixed event ID based on event type.
    
    Args:
        event_type: Type of event ('mining', 'operation', 'training', etc.)
        length: Length of random suffix (default: 6)
        
    Returns:
        Prefixed event ID (e.g., 'sm-a7k2m9', 'op-b3x8n4')
    """
    prefix = EVENT_ID_PREFIXES.get(event_type, 'ev')  # Default to 'ev' if unknown
    
    # Generate random alphanumeric suffix (excluding confusing characters)
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    chars = chars.replace('o', '').replace('0', '').replace('l', '').replace('1')  # Remove confusing chars
    
    suffix = ''.join(random.choice(chars) for _ in range(length))
    
    return f"{prefix}-{suffix}"

def validate_event_id_format(event_id: str) -> bool:
    """
    Validate that an event ID follows the expected prefix format.
    
    Args:
        event_id: Event ID to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not event_id or '-' not in event_id:
        return False
    
    prefix, suffix = event_id.split('-', 1)
    
    # Check if prefix is known
    if prefix not in EVENT_ID_PREFIXES.values():
        return False
        
    # Check suffix format (alphanumeric, reasonable length)
    if not suffix.isalnum() or len(suffix) < 4 or len(suffix) > 10:
        return False
        
    return True

def get_event_type_from_id(event_id: str) -> str:
    """
    Extract event type from prefixed event ID.
    
    Args:
        event_id: Prefixed event ID (e.g., 'sm-a7k2m9')
        
    Returns:
        Event type string ('mining', 'operation', etc.) or 'unknown'
    """
    if not event_id or '-' not in event_id:
        return 'unknown'
    
    prefix = event_id.split('-')[0]
    
    # Find event type by prefix
    for event_type, type_prefix in EVENT_ID_PREFIXES.items():
        if type_prefix == prefix:
            return event_type
    
    return 'unknown'

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

# Utility function for legacy database connections
def get_legacy_connection(database_url):
    """Get a database connection with URL resolution for legacy functions."""
    import psycopg2
    resolved_url = resolve_database_url(database_url)
    return psycopg2.connect(resolved_url)

# Legacy functions - these will be properly implemented later
def init_db(database_url):
    """Legacy function - initialize database"""
    from .schemas import init_database
    return init_database(database_url)

def get_market_items(database_url):
    """Get all active market items from the database"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Connect using utility function with URL resolution
        conn = get_legacy_connection(database_url)
            
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
        
        # Connect using utility function with URL resolution
        conn = get_legacy_connection(database_url)
            
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
        
        # Connect using utility function with URL resolution
        conn = get_legacy_connection(database_url)
            
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

def get_user_loans(database_url, user_id, guild_id=None):
    """
    Get all loans for a specific user.
    
    Args:
        database_url: Database connection string
        user_id: Discord user ID
        guild_id: Optional guild ID to filter by
    
    Returns:
        List of tuples: (loan_id, amount, issued_date, due_date, status, paid_amount, interest_rate)
    """
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Use utility function with URL resolution
        conn = get_legacy_connection(database_url)
        
        with conn.cursor() as cursor:
            if guild_id:
                cursor.execute("""
                    SELECT loan_id, amount, issued_date, due_date, status, paid_amount, interest_rate
                    FROM loans 
                    WHERE user_id = %s AND guild_id = %s AND status IN ('active', 'overdue', 'pending')
                    ORDER BY issued_date DESC
                """, (str(user_id), str(guild_id)))
            else:
                cursor.execute("""
                    SELECT loan_id, amount, issued_date, due_date, status, paid_amount, interest_rate
                    FROM loans 
                    WHERE user_id = %s AND status IN ('active', 'overdue', 'pending')
                    ORDER BY issued_date DESC
                """, (str(user_id),))
            
            loans = cursor.fetchall()
            print(f"✅ Found {len(loans)} loans for user {user_id}")
            return loans
            
    except Exception as e:
        print(f"❌ Error getting user loans: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def get_mining_channels_dict(database_url, guild_id):
    """Get mining channels as a dictionary for a specific guild."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Connect directly to database (no proxy needed with shared VPC)
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

def issue_loan(database_url, user_id, guild_id, amount, issued_date, due_date, interest_rate=0.0):
    """
    Issue a loan to a user.
    
    Args:
        database_url: Database connection string
        user_id: Discord user ID
        guild_id: Discord guild ID
        amount: Loan amount
        issued_date: Date when loan is issued
        due_date: Date when loan is due
        interest_rate: Interest rate (default 0.0)
    
    Returns:
        int: Loan ID if successful, None if failed
    """
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Use utility function with URL resolution
        conn = get_legacy_connection(database_url)
        
        with conn.cursor() as cursor:
            # Insert new loan
            cursor.execute("""
                INSERT INTO loans (user_id, guild_id, amount, interest_rate, issued_date, due_date, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'active')
                RETURNING loan_id
            """, (str(user_id), str(guild_id), amount, interest_rate, issued_date, due_date))
            
            loan_id = cursor.fetchone()[0]
            conn.commit()
            
            print(f"✅ Issued loan {loan_id} for {amount} aUEC to user {user_id}")
            return loan_id
            
    except Exception as e:
        print(f"❌ Error issuing loan: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def save_mining_participation(database_url, event_id, user_id, username, channel_id, channel_name, join_time, leave_time, duration_minutes, is_org_member):
    """
    Save mining participation data to the database.
    
    Args:
        database_url: Database connection string
        event_id: Mining event ID
        user_id: Discord user ID
        username: Discord username
        channel_id: Discord channel ID
        channel_name: Discord channel name
        join_time: Timestamp when user joined
        leave_time: Timestamp when user left
        duration_minutes: Duration in minutes
        is_org_member: Whether user is an org member
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Use utility function with URL resolution
        conn = get_legacy_connection(database_url)
        
        with conn.cursor() as cursor:
            # First ensure the user exists in users table
            cursor.execute("""
                INSERT INTO users (user_id, username, display_name, last_seen)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    username = EXCLUDED.username,
                    display_name = EXCLUDED.display_name,
                    last_seen = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """, (str(user_id), username, username))
            
            # Save mining participation
            cursor.execute("""
                INSERT INTO mining_participation (
                    event_id, user_id, channel_id, join_time, leave_time, 
                    duration_minutes, is_valid, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, true, CURRENT_TIMESTAMP
                )
            """, (
                event_id,
                str(user_id),
                str(channel_id),
                join_time,
                leave_time,
                duration_minutes
            ))
            
            conn.commit()
            print(f"✅ Saved mining participation: User {user_id} for {duration_minutes} minutes in event {event_id}")
            return True
            
    except Exception as e:
        print(f"❌ Error saving mining participation: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def add_mining_channel(database_url, guild_id, channel_id, channel_name, description=None):
    """Add a mining channel to the database."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Use utility function with URL resolution
        conn = get_legacy_connection(database_url)
        
        with conn.cursor() as cursor:
            # Check if channel already exists
            cursor.execute("""
                SELECT channel_id FROM mining_channels 
                WHERE guild_id = %s AND channel_id = %s
            """, (str(guild_id), str(channel_id)))
            
            if cursor.fetchone():
                print(f"⚠️ Mining channel {channel_id} already exists for guild {guild_id}")
                return False
            
            # Insert new mining channel
            cursor.execute("""
                INSERT INTO mining_channels (guild_id, channel_id, channel_name, description, is_active)
                VALUES (%s, %s, %s, %s, true)
            """, (str(guild_id), str(channel_id), channel_name, description))
            
            conn.commit()
            print(f"✅ Added mining channel {channel_name} ({channel_id}) for guild {guild_id}")
            return True
            
    except Exception as e:
        print(f"❌ Error adding mining channel: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def remove_mining_channel(database_url, guild_id, channel_id):
    """Remove a mining channel from the database."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Use utility function with URL resolution
        conn = get_legacy_connection(database_url)
        
        with conn.cursor() as cursor:
            # Check if channel exists
            cursor.execute("""
                SELECT channel_name FROM mining_channels 
                WHERE guild_id = %s AND channel_id = %s AND is_active = true
            """, (str(guild_id), str(channel_id)))
            
            result = cursor.fetchone()
            if not result:
                print(f"⚠️ Mining channel {channel_id} not found or already inactive for guild {guild_id}")
                return False
            
            channel_name = result[0]
            
            # Set channel as inactive instead of deleting (preserve historical data)
            cursor.execute("""
                UPDATE mining_channels 
                SET is_active = false, updated_at = CURRENT_TIMESTAMP 
                WHERE guild_id = %s AND channel_id = %s
            """, (str(guild_id), str(channel_id)))
            
            conn.commit()
            print(f"✅ Removed mining channel {channel_name} ({channel_id}) from guild {guild_id}")
            return True
            
    except Exception as e:
        print(f"❌ Error removing mining channel: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

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

def get_mining_session_participants(database_url, hours_back=None, event_id=None):
    """
    Get mining session participants.
    
    Args:
        database_url: Database connection string
        hours_back: Get participants from sessions in the last N hours
        event_id: Get participants from a specific event
    
    Returns:
        List of tuples: (member_id, username, total_time_seconds, primary_channel_id, last_activity, is_org_member)
    """
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Use utility function with URL resolution
        conn = get_legacy_connection(database_url)
        
        with conn.cursor() as cursor:
            if event_id:
                # Get participants for a specific event
                query = """
                SELECT 
                    u.user_id,
                    u.username,
                    COALESCE(SUM(mp.duration_minutes * 60), 0) as total_time_seconds,
                    MIN(mp.channel_id) as primary_channel_id,
                    MAX(mp.leave_time) as last_activity,
                    COALESCE(gm.is_org_member, false) as is_org_member
                FROM mining_participation mp
                JOIN users u ON mp.user_id = u.user_id
                LEFT JOIN guild_memberships gm ON mp.user_id = gm.user_id
                WHERE mp.event_id = %s 
                  AND mp.is_valid = true
                  AND mp.duration_minutes > 0
                GROUP BY u.user_id, u.username, gm.is_org_member
                ORDER BY total_time_seconds DESC
                """
                cursor.execute(query, (event_id,))
                
            elif hours_back:
                # Get participants from recent sessions
                query = """
                SELECT 
                    u.user_id,
                    u.username,
                    COALESCE(SUM(mp.duration_minutes * 60), 0) as total_time_seconds,
                    MIN(mp.channel_id) as primary_channel_id,
                    MAX(mp.leave_time) as last_activity,
                    COALESCE(gm.is_org_member, false) as is_org_member
                FROM mining_participation mp
                JOIN users u ON mp.user_id = u.user_id
                LEFT JOIN guild_memberships gm ON mp.user_id = gm.user_id
                WHERE mp.join_time >= NOW() - INTERVAL '%s hours'
                  AND mp.is_valid = true
                  AND mp.duration_minutes > 0
                GROUP BY u.user_id, u.username, gm.is_org_member
                ORDER BY total_time_seconds DESC
                """
                cursor.execute(query, (hours_back,))
            else:
                # Default: get all recent participants (last 24 hours)
                query = """
                SELECT 
                    u.user_id,
                    u.username,
                    COALESCE(SUM(mp.duration_minutes * 60), 0) as total_time_seconds,
                    MIN(mp.channel_id) as primary_channel_id,
                    MAX(mp.leave_time) as last_activity,
                    COALESCE(gm.is_org_member, false) as is_org_member
                FROM mining_participation mp
                JOIN users u ON mp.user_id = u.user_id
                LEFT JOIN guild_memberships gm ON mp.user_id = gm.user_id
                WHERE mp.join_time >= NOW() - INTERVAL '24 hours'
                  AND mp.is_valid = true
                  AND mp.duration_minutes > 0
                GROUP BY u.user_id, u.username, gm.is_org_member
                ORDER BY total_time_seconds DESC
                """
                cursor.execute(query)
            
            results = cursor.fetchall()
            print(f"✅ Found {len(results)} mining session participants")
            return results
            
    except Exception as e:
        print(f"❌ Error getting mining session participants: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def create_mining_event(database_url, guild_id, event_date=None, event_name="Sunday Mining"):
    """
    Create a standard mining event.
    
    Args:
        database_url: Database connection string
        guild_id: Discord guild ID
        event_date: Event date (defaults to today)
        event_name: Name of the event
    
    Returns:
        int: Event ID if successful, None if failed
    """
    try:
        import psycopg2
        from urllib.parse import urlparse
        from datetime import date, datetime
        
        if event_date is None:
            event_date = date.today()
        
        # Use utility function with URL resolution
        conn = get_legacy_connection(database_url)
        
        with conn.cursor() as cursor:
            # Check if event already exists for this date and guild
            cursor.execute("""
                SELECT event_id FROM mining_events 
                WHERE guild_id = %s AND event_date = %s AND is_active = true
                LIMIT 1
            """, (str(guild_id), event_date))
            
            existing_event = cursor.fetchone()
            if existing_event:
                print(f"✅ Found existing mining event {existing_event[0]} for {event_date}")
                return existing_event[0]
            
            # Generate prefixed event ID
            prefixed_event_id = generate_prefixed_event_id('mining')
            
            # Ensure ID is unique by checking database
            max_attempts = 10
            for attempt in range(max_attempts):
                cursor.execute("SELECT COUNT(*) FROM mining_events WHERE event_id = %s", (prefixed_event_id,))
                if cursor.fetchone()[0] == 0:
                    break  # ID is unique
                prefixed_event_id = generate_prefixed_event_id('mining')
                if attempt == max_attempts - 1:
                    print(f"❌ Could not generate unique event ID after {max_attempts} attempts")
                    return None
            
            # Create new event - using flexible column structure
            print(f"🔍 Attempting to create event with guild_id={guild_id}, event_id='{prefixed_event_id}', name='{event_name}', date={event_date}")
            
            # Skip the prefixed ID approach since database uses integer event_id
            # Go directly to the working schema based on diagnostics
            try:
                print(f"🔄 Creating event using current database schema (integer event_id)")
                cursor.execute("""
                    INSERT INTO mining_events (
                        guild_id, name, event_date, event_type, status, 
                        start_time, is_active, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, 'mining', 'active', 
                        %s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    ) RETURNING event_id
                """, (
                    str(guild_id), 
                    event_name, 
                    event_date,
                    datetime.now()
                ))
                integer_event_id = cursor.fetchone()[0]
                # Convert to prefixed format for display consistency
                returned_event_id = f"sm-{integer_event_id:06d}"
                print(f"✅ Created event using current schema, integer_id: {integer_event_id} -> display_id: {returned_event_id}")
                
            except Exception as schema_error:
                print(f"⚠️ New schema with prefixed ID failed: {schema_error}")
                print(f"🔄 Trying legacy schema with integer ID...")
                
                # Fallback to legacy schema format (auto-incrementing integer id)
                # This will return an integer ID instead of prefixed string
                try:
                    print(f"🔄 Attempting legacy schema INSERT...")
                    cursor.execute("""
                        INSERT INTO mining_events (
                            guild_id, name, event_date, event_type, status, 
                            start_time, is_active, created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, 'mining', 'active', 
                            %s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        ) RETURNING event_id
                    """, (
                        str(guild_id), 
                        event_name, 
                        event_date,
                        datetime.now()
                    ))
                    legacy_event_id = cursor.fetchone()[0]
                    
                    # Convert integer ID to prefixed format for consistency
                    returned_event_id = f"sm-{legacy_event_id:06d}"  # sm-000001 format
                    print(f"✅ Created event using legacy schema format, id: {legacy_event_id} -> prefixed: {returned_event_id}")
                    
                except Exception as legacy_error:
                    print(f"❌ Both new and legacy schema formats failed")
                    print(f"New schema error: {schema_error}")
                    print(f"Legacy schema error: {legacy_error}")
                    # Try one more fallback - very basic insert
                    try:
                        print(f"🔄 Attempting basic schema INSERT as final fallback...")
                        cursor.execute("""
                            INSERT INTO mining_events (guild_id, name, event_date, status, is_active)
                            VALUES (%s, %s, %s, 'active', true)
                            RETURNING event_id
                        """, (str(guild_id), event_name, event_date))
                        basic_event_id = cursor.fetchone()[0]
                        returned_event_id = f"sm-{basic_event_id:06d}"
                        print(f"✅ Created event using basic schema, id: {basic_event_id} -> prefixed: {returned_event_id}")
                    except Exception as basic_error:
                        print(f"❌ All schema formats failed:")
                        print(f"  - New schema: {schema_error}")
                        print(f"  - Legacy schema: {legacy_error}")
                        print(f"  - Basic schema: {basic_error}")
                        return None
            
            conn.commit()
            
            print(f"✅ Created mining event {returned_event_id} for guild {guild_id} on {event_date}")
            return returned_event_id
            
    except Exception as e:
        print(f"❌ Error creating mining event: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

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
        from .connection import resolve_database_url
        
        # Use standardized database connection approach
        resolved_url = resolve_database_url(database_url)
        conn = psycopg2.connect(resolved_url)
        
        cursor = conn.cursor()
        
        if guild_id:
            # Get open events for specific guild
            cursor.execute("""
                SELECT event_id, guild_id, event_date, start_time, name, status,
                       0 as total_participants, total_value_auec, 
                       false as payroll_processed, false as pdf_generated,
                       created_at, updated_at
                FROM mining_events 
                WHERE guild_id = %s AND status IN ('planned', 'active') AND is_active = true
                ORDER BY start_time DESC
            """, (str(guild_id),))
        else:
            # Get all open events
            cursor.execute("""
                SELECT event_id, guild_id, event_date, start_time, name, status,
                       0 as total_participants, total_value_auec,
                       false as payroll_processed, false as pdf_generated,
                       created_at, updated_at
                FROM mining_events 
                WHERE status IN ('planned', 'active') AND is_active = true
                ORDER BY start_time DESC
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

# ================================
# Event Management Functions
# ================================

async def create_event(name: str, description: str, category: str, date: str, time: str, 
                      created_by: int, subcategory: str = None, guild_id: str = None) -> int:
    """
    Create a new event in the mining_events table.
    
    Args:
        name: Event name
        description: Event description  
        category: Event category (mining, combat, training, etc.)
        date: Event date (YYYY-MM-DD format)
        time: Event time (HH:MM format)
        created_by: Discord user ID who created the event
        subcategory: Optional subcategory for more specific event types
        guild_id: Guild ID (optional, can be derived from context)
        
    Returns:
        int: The created event ID
    """
    try:
        # Use global db manager
        from config.settings import get_database_url
        database_url = get_database_url()
        
        # Combine date and time into a datetime
        datetime_str = f"{date} {time}:00"
        start_time = datetime.fromisoformat(datetime_str)
        
        # Default guild_id if not provided - this should not happen now
        if guild_id is None:
            raise ValueError("guild_id is required for event creation")
        
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Insert into mining_events table (works for all event types)
        cursor.execute("""
            INSERT INTO mining_events 
            (guild_id, name, description, event_type, start_time, organizer_id, status, event_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING event_id
        """, (guild_id, name, description, category, start_time, str(created_by), 'planned', start_time.date()))
        
        event_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        return event_id
        
    except Exception as e:
        print(f"Error creating event: {e}")
        raise

async def get_all_events(category: str = None, guild_id: str = None) -> List[Dict]:
    """
    Get all events, optionally filtered by category.
    
    Args:
        category: Optional category filter
        guild_id: Guild ID (required)
        
    Returns:
        List of event dictionaries
    """
    try:
        from config.settings import get_database_url
        database_url = get_database_url()
        
        # Guild ID is required now
        if guild_id is None:
            raise ValueError("guild_id is required for event operations")
        
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT event_id, name, description, event_type, start_time, event_date, 
                       status, organizer_id, organizer_name
                FROM mining_events 
                WHERE guild_id = %s AND event_type = %s AND is_active = true
                ORDER BY start_time ASC
            """, (guild_id, category))
        else:
            cursor.execute("""
                SELECT event_id, name, description, event_type, start_time, event_date,
                       status, organizer_id, organizer_name
                FROM mining_events 
                WHERE guild_id = %s AND is_active = true
                ORDER BY start_time ASC
            """, (guild_id,))
        
        events = []
        for row in cursor.fetchall():
            event_dict = {
                'event_id': row[0],  # Fixed: use 'event_id' instead of 'id'
                'id': row[0],        # Keep both for compatibility
                'name': row[1],
                'description': row[2],
                'event_type': row[3],    # Fixed: use 'event_type' to match database schema
                'category': row[3],      # Keep both for compatibility
                'start_time': row[4],
                'date': row[5].strftime('%Y-%m-%d') if row[5] else None,
                'time': row[4].strftime('%H:%M') if row[4] else None,
                'status': row[6],
                'organizer_id': row[7],
                'organizer_name': row[8]
            }
            events.append(event_dict)
        
        conn.close()
        return events
        
    except Exception as e:
        print(f"Error getting events: {e}")
        return []

async def delete_event(event_id: int, guild_id: str = None) -> bool:
    """
    Delete an event by setting is_active to false.
    
    Args:
        event_id: Event ID to delete
        guild_id: Guild ID (required)
        
    Returns:
        bool: True if successful
    """
    try:
        from config.settings import get_database_url
        database_url = get_database_url()
        
        # Guild ID is required now
        if guild_id is None:
            raise ValueError("guild_id is required for event operations")
        
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE mining_events 
            SET is_active = false, updated_at = CURRENT_TIMESTAMP
            WHERE event_id = %s AND guild_id = %s
        """, (event_id, guild_id))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error deleting event: {e}")
        return False

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
    'create_adhoc_mining_event',
    'get_open_mining_events',
    'save_event',
    'update_event_end_time',
    'get_mining_events',
    'update_entries',
    'get_entries',
    # Event management functions
    'create_event',
    'get_all_events',
    'delete_event',
]
