"""
Guild Operations

Database operations for Discord guild management.
"""

from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from ..connection import get_cursor
from ..models import Guild, GuildMembership

logger = logging.getLogger(__name__)

class GuildOperations:
    """Database operations for Discord guilds."""
    
    @staticmethod
    def create_guild(guild_id: int, name: str, settings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create or update a guild record.
        
        Args:
            guild_id: Discord guild ID
            name: Guild name
            settings: Optional guild settings
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO guilds (id, name, settings)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        settings = EXCLUDED.settings,
                        updated_at = CURRENT_TIMESTAMP
                """, (guild_id, name, settings or {}))
                
            logger.info(f"Guild {guild_id} ({name}) created/updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create guild {guild_id}: {e}")
            return False
    
    @staticmethod
    def get_guild(guild_id: int) -> Optional[Guild]:
        """
        Get a guild by ID.
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            Guild object if found, None otherwise
        """
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, settings, created_at, updated_at
                    FROM guilds
                    WHERE id = %s
                """, (guild_id,))
                
                row = cursor.fetchone()
                if row:
                    return Guild(
                        id=row['id'],
                        name=row['name'],
                        settings=row['settings'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to get guild {guild_id}: {e}")
            return None
    
    @staticmethod
    def update_guild_settings(guild_id: int, settings: Dict[str, Any]) -> bool:
        """
        Update guild settings.
        
        Args:
            guild_id: Discord guild ID
            settings: New settings dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    UPDATE guilds 
                    SET settings = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (settings, guild_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"Guild {guild_id} settings updated")
                    return True
                else:
                    logger.warning(f"Guild {guild_id} not found for settings update")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update guild {guild_id} settings: {e}")
            return False
    
    @staticmethod
    def get_guild_setting(guild_id: int, setting_key: str, default=None):
        """
        Get a specific guild setting.
        
        Args:
            guild_id: Discord guild ID
            setting_key: Setting key to retrieve
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        guild = GuildOperations.get_guild(guild_id)
        if guild and guild.settings:
            return guild.settings.get(setting_key, default)
        return default
    
    @staticmethod
    def set_guild_setting(guild_id: int, setting_key: str, setting_value: Any) -> bool:
        """
        Set a specific guild setting.
        
        Args:
            guild_id: Discord guild ID
            setting_key: Setting key to set
            setting_value: Setting value
            
        Returns:
            True if successful, False otherwise
        """
        guild = GuildOperations.get_guild(guild_id)
        if guild:
            settings = guild.settings.copy()
            settings[setting_key] = setting_value
            return GuildOperations.update_guild_settings(guild_id, settings)
        return False
    
    @staticmethod
    def list_all_guilds() -> List[Guild]:
        """
        Get all guilds.
        
        Returns:
            List of Guild objects
        """
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, settings, created_at, updated_at
                    FROM guilds
                    ORDER BY name
                """)
                
                return [Guild(
                    id=row['id'],
                    name=row['name'],
                    settings=row['settings'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to list guilds: {e}")
            return []
    
    @staticmethod
    def delete_guild(guild_id: int) -> bool:
        """
        Delete a guild and all associated data.
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_cursor() as cursor:
                cursor.execute("DELETE FROM guilds WHERE id = %s", (guild_id,))
                
                if cursor.rowcount > 0:
                    logger.info(f"Guild {guild_id} deleted")
                    return True
                else:
                    logger.warning(f"Guild {guild_id} not found for deletion")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to delete guild {guild_id}: {e}")
            return False
