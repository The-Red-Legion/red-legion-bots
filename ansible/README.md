# Ansible Deployment for Participation Bot

This directory contains Ansible playbooks for deploying the Participation Bot to remote servers.

## Prerequisites

1. **Ansible** installed on the deployment machine
2. **SSH access** to the target server
3. **GitHub Secrets** configured (see below)

## Required GitHub Secrets

Add the following secrets to your GitHub repository:

- `BOT_SERVER_HOST`: IP address or hostname of the server
- `BOT_SERVER_USER`: SSH username for the server
- `BOT_SSH_PRIVATE_KEY`: Private SSH key for authentication
- `DISCORD_TOKEN`: Discord bot token
- `TEXT_CHANNEL_ID`: Discord text channel ID
- `DATABASE_URL`: PostgreSQL database connection string

## Directory Structure

```
ansible/
├── deploy.yml              # Main deployment playbook
├── inventory.ini           # Ansible inventory file
├── ansible.cfg            # Ansible configuration
├── tasks/                 # Individual task files
│   ├── install_gcloud.yml
│   ├── stop_bot.yml
│   ├── setup_environment.yml
│   ├── start_bot.yml
│   └── verify_bot.yml
└── templates/             # Jinja2 templates
    └── env.j2
```

## Usage

The Ansible playbook is automatically executed by the GitHub Actions workflow when a PR is labeled "Ok to Deploy".

## Manual Execution

To run the playbook manually:

```bash
# Set environment variables
export BOT_SERVER_HOST=your-server-host
export BOT_SERVER_USER=your-ssh-user
export BOT_SSH_KEY_PATH=~/.ssh/id_rsa
export DISCORD_TOKEN=your-discord-token
export TEXT_CHANNEL_ID=your-channel-id
export DATABASE_URL=your-database-url

# Run the playbook
ansible-playbook ansible/deploy.yml -v
```

## Features

- **Automated deployment**: Complete end-to-end deployment process
- **Health checks**: Verifies bot is running after deployment
- **Error handling**: Comprehensive error reporting and rollback
- **Environment management**: Secure environment variable handling
- **Process management**: Proper bot process lifecycle management
- **Google Cloud integration**: Automatic secret retrieval from GCP

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**: Check SSH key and server access
2. **Import Errors**: Verify Python dependencies are installed
3. **Bot Won't Start**: Check environment variables and database connection
4. **Permission Denied**: Ensure proper file permissions on the server

### Debug Mode

Run with increased verbosity:
```bash
ansible-playbook ansible/deploy.yml -vvv
```
