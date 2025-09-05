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
    return {
        'TEXT_CHANNEL_ID': os.getenv('TEXT_CHANNEL_ID', '1187497620525023262'),
        'ORG_ROLE_ID': "1143413611184795658",
        'DISCORD_TOKEN': os.getenv('DISCORD_TOKEN', get_secret("discord-token")),
        'DATABASE_URL': os.getenv('DATABASE_URL', get_secret("database-connection-string")),
        'GITHUB_TOKEN': os.getenv('GITHUB_TOKEN', get_secret("github-token")),
        'WEBHOOK_URL': os.getenv('WEBHOOK_URL', get_secret("webhook-url")),
        'UEX_API_KEY': os.getenv('UEX_API_KEY', get_secret("uex-api-key"))
    }

config = get_config()
if not config['TEXT_CHANNEL_ID']:
    raise ValueError("TEXT_CHANNEL_ID not set or empty")
if not config['DISCORD_TOKEN']:
    raise ValueError("DISCORD_TOKEN not set")
if not config['DATABASE_URL']:
    raise ValueError("DATABASE_URL not set")
if not config['GITHUB_TOKEN']:
    raise ValueError("GITHUB_TOKEN not set")
if not config['WEBHOOK_URL']:
    raise ValueError("WEBHOOK_URL not set")
if not config['UEX_API_KEY']:
    raise ValueError("UEX_API_KEY not set")

LOG_CHANNEL_ID = config['TEXT_CHANNEL_ID']
ORG_ROLE_ID = config['ORG_ROLE_ID']
DISCORD_TOKEN = config['DISCORD_TOKEN']
DATABASE_URL = config['DATABASE_URL']
GITHUB_TOKEN = config['GITHUB_TOKEN']
WEBHOOK_URL = config['WEBHOOK_URL']
UEX_API_KEY = config['UEX_API_KEY']