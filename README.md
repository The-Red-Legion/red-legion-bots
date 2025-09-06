# Star Citizen Event Participation Bot

This Discord bot tracks participant activity in voice channels during Star Citizen events, logging usernames and total participation time every 30 minutes to a dedicated text channel. It's designed for deployment on Google Cloud Platform using Ansible automation.

## Overview

**Purpose**: Automates participation tracking for Star Citizen events, replacing manual screenshots.

**Features**:
- Logs members in a specified voice channel with total time spent
- Prompts for an event name on startup for log identification
- Confirms bot status after setup
- Runs every 30 minutes, posting to a Discord text channel
- Automated deployment using Ansible
- Health monitoring and error reporting

**Hosting**: Deployed on Google Cloud Platform with automated CI/CD pipelines.

## Prerequisites

- A Discord server with appropriate permissions
- Google Cloud Platform account with Compute Engine access
- GitHub account for repository management
- Python 3.9+ environment for local testing (optional)

## Setup Instructions

### 1. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application", name it (e.g., "StarCitizenEventBot"), and create
3. In the "Bot" tab, click "Add Bot", confirm, and copy the token (keep it secure)
4. Enable the following intents:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
5. Go to "OAuth2 > URL Generator", select "bot" scope, and check permissions:
   - View Channels
   - Send Messages
   - Read Message History
6. Copy the generated URL, paste in a browser, select your server, and authorize

### 2. Configure the Server

1. Create a dedicated text channel (e.g., `event-logs`) for logs
2. Enable Developer Mode (User Settings > Appearance)
3. Right-click `event-logs`, copy ID
4. Ensure the bot has these permissions in the channel:
   - View Channels
   - Send Messages
   - Read Message History

### 3. Set Up Google Cloud Platform

1. Create a GCP project or use existing one
2. Enable required APIs:
   - Compute Engine API
   - Secret Manager API
3. Create a service account with necessary permissions
4. Store secrets in Secret Manager:
   - `discord-token`: Your Discord bot token
   - `text-channel-id`: The event-logs channel ID
   - `database-url`: PostgreSQL connection string

### 4. Configure GitHub Secrets

Add these secrets to your GitHub repository:

**Existing Secrets**:
- `GCP_CREDENTIALS`: Service account JSON key
- `DISCORD_TOKEN`: Discord bot token
- `TEXT_CHANNEL_ID`: Discord channel ID
- `DATABASE_URL`: Database connection string

**New Secrets for Ansible**:
- `BOT_SERVER_HOST`: GCP instance IP/hostname
- `BOT_SERVER_USER`: SSH username (usually `ubuntu`)
- `BOT_SSH_PRIVATE_KEY`: Private SSH key for instance access

### 5. Deploy Using GitHub Actions

1. Create a pull request with your changes
2. Run tests (automatically triggered)
3. When tests pass, add the "Ok to Deploy" label
4. Ansible will automatically deploy to your GCP instance
5. Monitor deployment logs in the Actions tab

## Usage

### Start Logging

1. Join the voice channel to monitor (e.g., "Event Voice")
2. In a text channel with bot permissions, type:
   ```
   !start_logging
   ```
3. Reply with the event name (e.g., "Star Citizen Race") within 60 seconds
4. Expected response: "Bot is running and logging started for Event Voice (Event: Star Citizen Race, every 30 minutes). Everything is set up correctly!"

### View Logs

Logs appear in the `event-logs` channel every 30 minutes, e.g.:
```
2025-08-31 16:03:00 - Event: Star Citizen Race (Channel: Event Voice)
Participants:
  Player1#1234: 0h 30m 0s
  Player2#5678: 0h 15m 45s
```

### Stop Logging

Type:
```
!stop_logging
```

Expected response: "Participation logging stopped."

## Deployment Architecture

The bot uses a modern CI/CD pipeline:

- **Testing**: Automated unit tests and integration tests
- **Deployment**: Ansible playbooks for infrastructure as code
- **Infrastructure**: Google Cloud Platform with automated scaling
- **Monitoring**: Health checks and error reporting
- **Security**: Secrets management with GCP Secret Manager

## Troubleshooting

### Bot Not Responding
- Check GitHub Actions deployment logs for errors
- Verify environment variables are set correctly
- Check Discord bot permissions

### No Logs Appearing
- Verify `TEXT_CHANNEL_ID` is correct
- Ensure bot has proper permissions in the Discord channel
- Check bot health in deployment logs

### Deployment Failures
- Check Ansible playbook execution logs
- Verify SSH access to GCP instance
- Ensure all required secrets are configured

### Database Connection Issues
- Verify `DATABASE_URL` format and credentials
- Check PostgreSQL server connectivity
- Review database permissions

## Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DISCORD_TOKEN=your_token
export TEXT_CHANNEL_ID=your_channel_id
export DATABASE_URL=your_db_url

# Run the bot
python -m src.participation_bot
```

### Code Quality

The project uses:
- **Ruff**: Python linter and formatter
- **Pytest**: Unit testing framework
- **GitHub Actions**: CI/CD pipeline

## Contributing

1. Fork this repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
6. Wait for automated tests to pass
7. Add "Ok to Deploy" label for deployment

## License

MIT License