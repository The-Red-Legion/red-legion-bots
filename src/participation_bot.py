import discord
from discord.ext import commands
from .config import DATABASE_URL
from .database import init_db
from .event_handlers import (
    on_voice_state_update, start_logging, stop_logging, pick_winner,
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

# Dynamically register event handler
async def setup_event_handlers():
    bot.add_listener(on_voice_state_update, 'on_voice_state_update')

# Dynamically register commands
def setup_commands():
    # Command without role restriction
    bot.command(name="start_logging")(lambda ctx: start_logging(bot, ctx))
    bot.command(name="stop_logging")(lambda ctx: stop_logging(bot, ctx))
    bot.command(name="pick_winner")(lambda ctx: pick_winner(bot, ctx))

    # Commands with role restriction
    @has_org_role()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def wrapped_list_market(ctx):
        await list_items(ctx)
    bot.add_command(wrapped_list_market)

    @has_org_role()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def wrapped_add_market_item(ctx, name: str, price: int, stock: int):
        await add_item(ctx, name, price, stock)
    bot.add_command(wrapped_add_market_item)

    @has_org_role()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def wrapped_request_loan(ctx, amount: int):
        await request_loan(ctx, amount)
    bot.add_command(wrapped_request_loan)

    @has_org_role()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def wrapped_log_mining_results(ctx, event_id: int):
        await log_mining_results(bot, ctx, event_id)
    bot.add_command(wrapped_log_mining_results)

    @has_org_role()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def wrapped_list_open_events(ctx):
        await list_open_events(bot, ctx)
    bot.add_command(wrapped_list_open_events)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        init_db(DATABASE_URL)
        await setup_event_handlers()  # Register event handler
        setup_commands()  # Register commands
    except Exception as e:
        print(f"Error during setup: {e}")