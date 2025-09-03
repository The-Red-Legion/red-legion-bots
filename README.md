Star Citizen Event Participation Bot
This Discord bot tracks participant activity in voice channels during Star Citizen events, logging usernames and total participation time every 30 minutes to a dedicated text channel. It’s designed for easy deployment on Render and supports dynamic event naming for clear log identification.
Overview

Purpose: Automates participation tracking for Star Citizen events, replacing manual screenshots.
Features:
Logs members in a specified voice channel with total time spent.
Prompts for an event name on startup for log identification.
Confirms bot status after setup.
Runs every 30 minutes, posting to a Discord text channel.


Hosting: Deployed on Render with environment variables for security.

Prerequisites

A Discord server with appropriate permissions.
A Render account (free tier available).
GitHub account for repository management.
Python 3.x environment for local testing (optional).

Setup Instructions
1. Create a Discord Bot

Go to Discord Developer Portal.
Click New Application, name it (e.g., "StarCitizenEventBot"), and create.
In the Bot tab, click Add Bot, confirm, and copy the token (keep it secure).
Enable Presence Intent, Server Members Intent, and Message Content Intent.
Go to OAuth2 > URL Generator, select bot scope, and check permissions:
View Channels
Send Messages
Read Message History


Copy the generated URL, paste in a browser, select your server, and authorize.

2. Configure the Server

Create a dedicated text channel (e.g., event-logs) for logs.
Enable Developer Mode (User Settings > Appearance), right-click event-logs, copy ID.
Ensure the bot has View Channels, Send Messages, and Read Message History permissions in this channel.

3. Prepare the Repository

Clone this repo locally:git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name


Ensure participation_bot.py is present (with environment variable setup).
Create requirements.txt with:discord.py


Commit and push changes:git add .
git commit -m "Initial setup"
git push origin main



4. Deploy on Render

Sign up at render.com and connect your GitHub account.
Click New > Web Service, select your repository.
Configure:
Name: e.g., StarCitizenEventBot
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: python participation_bot.py
Environment Variables:
DISCORD_TOKEN: Your bot token
TEXT_CHANNEL_ID: The event-logs channel ID




Select Free tier (750 hours/month) or a paid plan ($7/month) for continuous uptime.
Click Create Web Service and verify deployment in the Events tab.

Usage

Start Logging:

Join the voice channel to monitor (e.g., Event Voice).
In a text channel with bot permissions, type:!start_logging


Reply with the event name (e.g., Star Citizen Race) within 60 seconds.
Expect: “Bot is running and logging started for Event Voice (Event: Star Citizen Race, every 30 minutes). Everything is set up correctly!”


View Logs:

Logs appear in the event-logs channel every 30 minutes, e.g.:2025-08-31 16:03:00 - Event: Star Citizen Race (Channel: Event Voice)
Participants:
  Player1#1234: 0h 30m 0s
  Player2#5678: 0h 15m 45s
  None




Stop Logging:

Type:!stop_logging


Expect: “Participation logging stopped.”



Troubleshooting

Bot Not Responding: Check Render logs (Events tab) for errors (e.g., missing environment variables).
No Logs: Verify TEXT_CHANNEL_ID and bot permissions in Discord.
Free Tier Pause: Upgrade to a paid plan on Render for 24/7 uptime.

Contributing
Feel free to fork this repo, modify the script, and submit pull requests for enhancements (e.g., multiple voice channels).
License
MIT License (or specify your preferred license).