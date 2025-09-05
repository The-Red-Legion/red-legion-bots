import discord
from discord.ext import commands
from .config import DATABASE_URL
from .database import init_db
from .event_handlers import (
    on_voice_state_update, log_members, start_logging, stop_logging, pick_winner,
    log_mining_results, list_open_events
)
from .market import list_items, add_item
from .loan import request_loan
from .discord_utils import has_org_role

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        init_db(DATABASE_URL)
    except Exception as e:
        print(f"Error during database initialization: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    await on_voice_state_update(member, before, after)

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.guild)
async def start_logging(ctx):
    await start_logging(bot, ctx)

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.guild)
async def stop_logging(ctx):
    await stop_logging(bot, ctx)

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.guild)
async def pick_winner(ctx):
    await pick_winner(bot, ctx)

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.guild)
@has_org_role()
async def list_market(ctx):
    await list_items(ctx)

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.guild)
@has_org_role()
async def add_market_item(ctx, name: str, price: int, stock: int):
    await add_item(ctx, name, price, stock)

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.guild)
@has_org_role()
async def request_loan(ctx, amount: int):
    await request_loan(ctx, amount)

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.guild)
@has_org_role()
async def log_mining_results(ctx, event_id: int):
    await log_mining_results(bot, ctx, event_id)

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.guild)
@has_org_role()
async def list_open_events(ctx):
    await list_open_events(bot, ctx)