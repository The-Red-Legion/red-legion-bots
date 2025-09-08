"""
User Operations

Database operations for Discord user management.
"""

from typing import Optional, List
import logging
from datetime import datetime

from ..connection import get_cursor
from ..models import User, GuildMembership

logger = logging.getLogger(__name__)

class UserOperations:
    """Database operations for Discord users."""
    
    @staticmethod
    def create_user(user_id: int, username: str, display_name: Optional[str] = None) -> bool:
        """
        Create or update a user record.
        
        Args:
            user_id: Discord user ID
            username: Username
            display_name: Optional display name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (id, username, display_name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        username = EXCLUDED.username,
                        display_name = EXCLUDED.display_name,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, username, display_name))
                
            logger.debug(f"User {user_id} ({username}) created/updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create user {user_id}: {e}")
            return False
    
    @staticmethod
    def get_user(user_id: int) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, username, display_name, created_at, updated_at
                    FROM users
                    WHERE id = %s
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return User(
                        id=row['id'],
                        username=row['username'],
                        display_name=row['display_name'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    @staticmethod
    def add_guild_membership(guild_id: int, user_id: int, is_org_member: bool = False) -> bool:
        """
        Add or update a user's guild membership.
        
        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID
            is_org_member: Whether user is an organization member
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO guild_memberships (guild_id, user_id, is_org_member)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (guild_id, user_id) DO UPDATE SET
                        is_org_member = EXCLUDED.is_org_member
                """, (guild_id, user_id, is_org_member))
                
            logger.debug(f"Guild membership added: user {user_id} in guild {guild_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add guild membership for user {user_id} in guild {guild_id}: {e}")
            return False
    
    @staticmethod
    def get_guild_membership(guild_id: int, user_id: int) -> Optional[GuildMembership]:
        """
        Get a user's guild membership.
        
        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID
            
        Returns:
            GuildMembership object if found, None otherwise
        """
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT guild_id, user_id, is_org_member, join_date
                    FROM guild_memberships
                    WHERE guild_id = %s AND user_id = %s
                """, (guild_id, user_id))
                
                row = cursor.fetchone()
                if row:
                    return GuildMembership(
                        guild_id=row['guild_id'],
                        user_id=row['user_id'],
                        is_org_member=row['is_org_member'],
                        join_date=row['join_date']
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to get guild membership for user {user_id} in guild {guild_id}: {e}")
            return None
    
    @staticmethod
    def get_guild_members(guild_id: int, org_members_only: bool = False) -> List[tuple]:
        """
        Get all members of a guild.
        
        Args:
            guild_id: Discord guild ID
            org_members_only: If True, only return organization members
            
        Returns:
            List of (User, GuildMembership) tuples
        """
        try:
            with get_cursor() as cursor:
                where_clause = "WHERE gm.guild_id = %s"
                params = [guild_id]
                
                if org_members_only:
                    where_clause += " AND gm.is_org_member = TRUE"
                
                cursor.execute(f"""
                    SELECT u.id, u.username, u.display_name, u.created_at, u.updated_at,
                           gm.guild_id, gm.user_id, gm.is_org_member, gm.join_date
                    FROM users u
                    INNER JOIN guild_memberships gm ON u.id = gm.user_id
                    {where_clause}
                    ORDER BY u.username
                """, params)
                
                result = []
                for row in cursor.fetchall():
                    user = User(
                        id=row['id'],
                        username=row['username'],
                        display_name=row['display_name'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    membership = GuildMembership(
                        guild_id=row['guild_id'],
                        user_id=row['user_id'],
                        is_org_member=row['is_org_member'],
                        join_date=row['join_date']
                    )
                    result.append((user, membership))
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get guild members for guild {guild_id}: {e}")
            return []
    
    @staticmethod
    def update_org_member_status(guild_id: int, user_id: int, is_org_member: bool) -> bool:
        """
        Update a user's organization member status.
        
        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID
            is_org_member: New organization member status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    UPDATE guild_memberships 
                    SET is_org_member = %s
                    WHERE guild_id = %s AND user_id = %s
                """, (is_org_member, guild_id, user_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"Updated org status for user {user_id} in guild {guild_id}: {is_org_member}")
                    return True
                else:
                    logger.warning(f"No membership found for user {user_id} in guild {guild_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update org status for user {user_id} in guild {guild_id}: {e}")
            return False
    
    @staticmethod
    def remove_guild_membership(guild_id: int, user_id: int) -> bool:
        """
        Remove a user's guild membership.
        
        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM guild_memberships 
                    WHERE guild_id = %s AND user_id = %s
                """, (guild_id, user_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"Removed guild membership: user {user_id} from guild {guild_id}")
                    return True
                else:
                    logger.warning(f"No membership found for user {user_id} in guild {guild_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to remove guild membership for user {user_id} in guild {guild_id}: {e}")
            return False
    
    @staticmethod
    def is_org_member(guild_id: int, user_id: int) -> bool:
        """
        Check if a user is an organization member in a guild.
        
        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID
            
        Returns:
            True if user is an org member, False otherwise
        """
        membership = UserOperations.get_guild_membership(guild_id, user_id)
        return membership.is_org_member if membership else False
