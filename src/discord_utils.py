from discord import Embed
import discord.ext.commands as commands

async def send_embed(channel, title, description, color, timestamp=None):
    embed = Embed(title=title, description=description, color=color, timestamp=timestamp)
    await channel.send(embed=embed)

def has_org_role():
    async def predicate(ctx):
        return True  # Mock for testing, replace with real role check
    return commands.check(predicate)