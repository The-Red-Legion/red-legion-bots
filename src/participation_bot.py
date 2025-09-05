import discord
from discord.ext import commands
from .config import DATABASE_URL
from .database import init_db, add_market_item, get_market_items, issue_loan
from .event_handlers import (
    on_voice_state_update, start_logging, stop_logging, pick_winner,
    log_mining_results, list_open_events
)
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
        items = get_market_items(DATABASE_URL)
        if not items:
            await ctx.send("No market items available.")
            return
        
        embed = discord.Embed(title="Market Items", color=discord.Color.blue())
        for item_id, name, price, stock in items:
            embed.add_field(name=f"{name} (ID: {item_id})", value=f"Price: {price} credits\nStock: {stock}", inline=False)
        await ctx.send(embed=embed)
    bot.add_command(wrapped_list_market)

    @has_org_role()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def wrapped_add_market_item(ctx, name: str, price: int, stock: int):
        try:
            add_market_item(DATABASE_URL, name, price, stock)
            await ctx.send(f"Added {name} to market for {price} credits (Stock: {stock})")
        except Exception as e:
            await ctx.send(f"Failed to add market item: {e}")
    bot.add_command(wrapped_add_market_item)

    @has_org_role()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def wrapped_request_loan(ctx, amount: int):
        try:
            from datetime import datetime, timedelta
            issued_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            issue_loan(DATABASE_URL, ctx.author.id, amount, issued_date, due_date)
            await ctx.send(f"Loan request submitted for {amount} credits. Due date: {due_date}")
        except Exception as e:
            await ctx.send(f"Failed to request loan: {e}")
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