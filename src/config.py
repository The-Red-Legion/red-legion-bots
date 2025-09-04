import os
from google.cloud import secretmanager
from dotenv import load_dotenv

load_dotenv()  # Load .env for local development

def get_secret(secret_id, project_id=os.getenv('GCP_PROJECT_ID')):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

# List of valid mining materials based on the provided list
MINING_MATERIALS = [
    "Stileron", "Quantainium", "Riccite", "Taranite", "Bexalite",
    "Gold", "Borase", "Laranite", "Beryl", "Agricium",
    "Hephaestanite", "Tungsten", "Titanium", "Iron", "Quartz",
    "Corundum", "Copper", "Tin", "Aluminum", "Silicon"
]

# Load secrets from Google Cloud Secret Manager (or .env for local dev)
LOG_CHANNEL_ID = os.getenv('TEXT_CHANNEL_ID') or get_secret("text-channel-id")
ORG_ROLE_ID = "1143413611184795658"
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN') or get_secret("discord-token")
DATABASE_URL = os.getenv('DATABASE_URL') or get_secret("database-url")
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN') or get_secret("github-token")
WEBHOOK_URL = os.getenv('WEBHOOK_URL') or get_secret("webhook-url")
UEX_API_KEY = os.getenv('UEX_API_KEY') or get_secret("uex-api-key")

# Validate required environment variables
if not LOG_CHANNEL_ID:
    raise ValueError("TEXT_CHANNEL_ID not set")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not set")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN not set")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL not set")
if not UEX_API_KEY:
    raise ValueError("UEX_API_KEY not set")