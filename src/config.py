import os
from google.cloud import secretmanager
from dotenv import load_dotenv

load_dotenv()

def get_secret(secret_id, project_id=os.getenv('GOOGLE_CLOUD_PROJECT', 'rl-prod-471116')):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

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

LOG_CHANNEL_ID = config['TEXT_CHANNEL_ID']
ORG_ROLE_ID = config['ORG_ROLE_ID']
DISCORD_TOKEN = config['DISCORD_TOKEN']
DATABASE_URL = config['DATABASE_URL']
GITHUB_TOKEN = config['GITHUB_TOKEN']
WEBHOOK_URL = config['WEBHOOK_URL']
UEX_API_KEY = config['UEX_API_KEY']