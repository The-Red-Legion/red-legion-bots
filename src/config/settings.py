"""
Core settings and configuration for Red Legion Discord Bot.
"""

import os
from google.cloud import secretmanager

def get_secret(secret_name, project_id="the-red-legion"):
    """Retrieve secret from Google Cloud Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": secret_path})
    return response.payload.data.decode("UTF-8")

def get_database_url():
    """Get database URL from environment or secret manager."""
    # Try environment first
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        return db_url
    
    # Try reading from file
    try:
        with open('db_url.txt', 'r') as f:
            db_url = f.read().strip()
            if db_url:
                return db_url
    except FileNotFoundError:
        pass
    
    # Try secret manager as fallback
    try:
        return get_secret("database-connection-string")
    except Exception as e:
        print(f"Warning: Could not get database URL: {e}")
        return None

# UEX API Configuration
UEX_API_CONFIG = {
    'base_url': 'https://uexcorp.space/api/2.0/commodities',
    'bearer_token': '4ae9c984f69da2ad759776529b37a3dabdf99db4',
    'timeout': 30
}

# Discord Configuration
def get_discord_config():
    """Get Discord configuration with fallbacks."""
    discord_token = os.getenv('DISCORD_TOKEN')
    
    # Try secret manager if no environment variable
    if not discord_token:
        try:
            discord_token = get_secret("discord-token")
        except Exception as e:
            print(f"Warning: Could not get discord-token from Secret Manager: {e}")
            discord_token = None
    
    return {
        'TOKEN': discord_token,
        'TEXT_CHANNEL_ID': os.getenv('TEXT_CHANNEL_ID', '1187497620525023262'),
        'ORG_ROLE_ID': "1143413611184795658",
        'GUILD_ID': os.getenv('GUILD_ID'),  # Optional, for single-guild deployment
    }

DISCORD_CONFIG = get_discord_config()

# Validate essential configurations
def validate_config():
    """Validate that required configuration is available."""
    if not DISCORD_CONFIG['TOKEN']:
        raise ValueError("DISCORD_TOKEN not set - required for bot operation")
    
    db_url = get_database_url()
    if not db_url:
        raise ValueError("DATABASE_URL not set - required for bot operation")
    
    return True

# Mining Materials List
ORE_TYPES = [
    "Stileron", "Quantainium", "Riccite", "Taranite", "Bexalite",
    "Gold", "Borase", "Laranite", "Beryl", "Agricium",
    "Hephaestanite", "Tungsten", "Titanium", "Iron", "Quartz",
    "Corundum", "Copper", "Tin", "Aluminum", "Silicon"
]
