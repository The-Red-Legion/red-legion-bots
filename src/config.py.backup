import os
from google.cloud import secretmanager
from dotenv import load_dotenv

load_dotenv()

def get_secret(secret_id, project_id=os.getenv('GOOGLE_CLOUD_PROJECT', 'rl-prod-471116')):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

# Sunday Mining Configuration
# Note: Channel IDs are now managed in the database
# Use get_sunday_mining_channels() to retrieve current channels
SUNDAY_MINING_CHANNELS_FALLBACK = {
    'dispatch': '1385774416755163247',
    'alpha': '1386367354753257583',
    'bravo': '1386367395643449414',
    'charlie': '1386367464279478313',
    'delta': '1386368182421635224',
    'echo': '1386368221877272616',
    'foxtrot': '1386368253712375828'
}

def get_sunday_mining_channels(guild_id=None):
    """
    Get Sunday mining channels from database for a specific guild.
    Falls back to hardcoded values if database is unavailable.
    """
    try:
        from .database import get_mining_channels_dict
        db_url = get_database_url()
        if db_url:
            channels = get_mining_channels_dict(db_url, guild_id)
            if channels:
                return channels
    except Exception as e:
        print(f"Warning: Could not get mining channels from database: {e}")
    
    # Fallback to hardcoded channels
    print("Using fallback mining channels")
    return SUNDAY_MINING_CHANNELS_FALLBACK

# 21 ore types for mining operations
ORES = {
    'QUANTANIUM': 'Quantanium',
    'TARANITE': 'Taranite',
    'BEXALITE': 'Bexalite',
    'BORASE': 'Borase',
    'LARANITE': 'Laranite',
    'BERYL': 'Beryl',
    'AGRICIUM': 'Agricium',
    'HEPHAESTANITE': 'Hephaestanite',
    'TUNGSTEN': 'Tungsten',
    'TITANIUM': 'Titanium',
    'COPPER': 'Copper',
    'CORUNDUM': 'Corundum',
    'ALUMINIUM': 'Aluminium',
    'IRON': 'Iron',
    'QUARTZ': 'Quartz',
    'SILICON': 'Silicon',
    'TIN': 'Tin',
    'GOLD': 'Gold',
    'RICCITE': 'Riccite',
    'STILERON': 'Stileron',
    'ICE': 'Ice'
}

# UEX API Configuration
UEX_API_BASE_URL = 'https://uexcorp.space/api/2.0/commodities'
UEX_BEARER_TOKEN = '4ae9c984f69da2ad759776529b37a3dabdf99db4'

MINING_MATERIALS = [
    "Stileron", "Quantainium", "Riccite", "Taranite", "Bexalite",
    "Gold", "Borase", "Laranite", "Beryl", "Agricium",
    "Hephaestanite", "Tungsten", "Titanium", "Iron", "Quartz",
    "Corundum", "Copper", "Tin", "Aluminum", "Silicon"
]

def get_config():
    # Get environment variables first, fallback to secrets only if needed
    discord_token = os.getenv('DISCORD_TOKEN')
    database_url = os.getenv('DATABASE_URL')
    
    # Only try to get secrets if environment variables are not available
    if not discord_token:
        try:
            discord_token = get_secret("discord-token")
        except Exception as e:
            print(f"Warning: Could not get discord-token from Secret Manager: {e}")
            discord_token = None
    
    if not database_url:
        try:
            database_url = get_secret("database-connection-string")
        except Exception as e:
            print(f"Warning: Could not get database URL from Secret Manager: {e}")
            database_url = None
    
    return {
        'TEXT_CHANNEL_ID': os.getenv('TEXT_CHANNEL_ID', '1187497620525023262'),
        'ORG_ROLE_ID': "1143413611184795658",
        'DISCORD_TOKEN': discord_token,
        'DATABASE_URL': database_url,
        'GITHUB_TOKEN': os.getenv('GITHUB_TOKEN', 'dummy-github-token'), #Fallback
        'WEBHOOK_URL': os.getenv('WEBHOOK_URL', 'https://default.webhook.url'), #Fallback
        'UEX_API_KEY': os.getenv('UEX_API_KEY', 'dummy-uex-api-key')  # Fallback
    }

config = get_config()
# Only validate essential configurations for bot operation
if not config['TEXT_CHANNEL_ID']:
    raise ValueError("TEXT_CHANNEL_ID not set or empty")
if not config['DISCORD_TOKEN']:
    raise ValueError("DISCORD_TOKEN not set")
if not config['DATABASE_URL']:
    raise ValueError("DATABASE_URL not set")

# Optional configurations - warn but don't fail
if not config['GITHUB_TOKEN'] or config['GITHUB_TOKEN'] == 'dummy-github-token':
    print("Warning: GITHUB_TOKEN not set or using dummy value")
if not config['WEBHOOK_URL'] or config['WEBHOOK_URL'] == 'https://default.webhook.url':
    print("Warning: WEBHOOK_URL not set or using default value")
if not config['UEX_API_KEY'] or config['UEX_API_KEY'] == 'dummy-uex-api-key':
    print("Warning: UEX_API_KEY not set or using dummy value")

def get_database_url():
    """Get current database URL, refreshing from Secret Manager if needed"""
    global DATABASE_URL
    if not DATABASE_URL:
        try:
            DATABASE_URL = get_secret("database-connection-string")
            print("Successfully refreshed DATABASE_URL from Secret Manager")
        except Exception as e:
            print(f"Failed to refresh DATABASE_URL: {e}")
            # Try getting from config again
            try:
                fresh_config = get_config()
                DATABASE_URL = fresh_config.get('DATABASE_URL')
            except Exception as e2:
                print(f"Failed to get DATABASE_URL from fresh config: {e2}")
    return DATABASE_URL

LOG_CHANNEL_ID = config['TEXT_CHANNEL_ID']
ORG_ROLE_ID = config['ORG_ROLE_ID']
DISCORD_TOKEN = config['DISCORD_TOKEN']
DATABASE_URL = config['DATABASE_URL']
GITHUB_TOKEN = config['GITHUB_TOKEN']
WEBHOOK_URL = config['WEBHOOK_URL']
UEX_API_KEY = config['UEX_API_KEY']