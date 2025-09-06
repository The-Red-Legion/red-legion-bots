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
    print("Registering basic commands...")
    
    # Command without role restriction - fix lambda issues
    @bot.command(name="start_logging")
    async def start_logging_cmd(ctx):
        await start_logging(bot, ctx)
    
    @bot.command(name="stop_logging")
    async def stop_logging_cmd(ctx):
        await stop_logging(bot, ctx)
    
    @bot.command(name="pick_winner")
    async def pick_winner_cmd(ctx):
        await pick_winner(bot, ctx)
    
    print("Basic commands registered")
    print("Registering role-restricted commands...")

    # Commands with role restriction
    @bot.command(name="list_market")
    @has_org_role()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def list_market(ctx):
        items = get_market_items(DATABASE_URL)
        if not items:
            await ctx.send("No market items available.")
            return
        
        embed = discord.Embed(title="Market Items", color=discord.Color.blue())
        for item_id, name, price, stock in items:
            embed.add_field(name=f"{name} (ID: {item_id})", value=f"Price: {price} credits\nStock: {stock}", inline=False)
        await ctx.send(embed=embed)

    @bot.command(name="add_market_item")
    @has_org_role()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def add_market_item_cmd(ctx, name: str, price: int, stock: int):
        try:
            add_market_item(DATABASE_URL, name, price, stock)
            await ctx.send(f"Added {name} to market for {price} credits (Stock: {stock})")
        except Exception as e:
            await ctx.send(f"Failed to add market item: {e}")

    @bot.command(name="request_loan")
    @has_org_role()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def request_loan(ctx, amount: int):
        try:
            from datetime import datetime, timedelta
            issued_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            issue_loan(DATABASE_URL, ctx.author.id, amount, issued_date, due_date)
            await ctx.send(f"Loan request submitted for {amount} credits. Due date: {due_date}")
        except Exception as e:
            await ctx.send(f"Failed to request loan: {e}")

    @bot.command(name="log_mining_results")
    @has_org_role()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def log_mining_results_cmd(ctx, event_id: int):
        await ctx.send("⚠️ Mining results logging is temporarily disabled due to implementation issues.")
        # await log_mining_results(bot, ctx, event_id)

    @bot.command(name="list_open_events")
    @has_org_role()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def list_open_events_cmd(ctx):
        await list_open_events(bot, ctx)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'Bot is ready and connected to {len(bot.guilds)} servers')
    
    # Log guild information
    for guild in bot.guilds:
        print(f'Connected to guild: {guild.name} (ID: {guild.id})')
    
    try:
        print("Initializing database...")
        # Run database init in a thread to avoid blocking the event loop
        import asyncio
        import functools
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, functools.partial(init_db, DATABASE_URL))
        print("Database initialized successfully")
        
        print("Setting up event handlers...")
        await setup_event_handlers()  # Register event handler
        print("Event handlers registered successfully")
        
        print("Setting up commands...")
        setup_commands()  # Register commands
        print("Commands registered successfully")
        
        print("Bot setup completed successfully!")
        print("Bot is fully operational and ready to receive commands")
        
        # Add a simple heartbeat to ensure bot stays alive
        print("✅ Bot startup sequence completed - bot should remain running")
        
    except Exception as e:
        print(f"CRITICAL ERROR during setup: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        print("Bot will attempt to continue running despite setup errors...")
        # Don't re-raise the exception - let the bot continue running

@bot.event
async def on_error(event, *args, **kwargs):
    print(f'DISCORD EVENT ERROR in event {event}')
    print(f'Args: {args}')
    print(f'Kwargs: {kwargs}')
    import traceback
    print("Full traceback:")
    print(traceback.format_exc())

# Add a disconnect handler to log when bot disconnects
@bot.event
async def on_disconnect():
    print("⚠️  Bot disconnected from Discord!")

# Add a resumed handler to log reconnections
@bot.event
async def on_resumed():
    print("✅ Bot resumed connection to Discord!")

if __name__ == "__main__":
    from .config import DISCORD_TOKEN
    print("Starting Discord bot...")
    print(f"Discord token length: {len(DISCORD_TOKEN) if DISCORD_TOKEN else 'None'}")
    print(f"Database URL configured: {'Yes' if DATABASE_URL else 'No'}")
    
    try:
        print("Calling bot.run()...")
        bot.run(DISCORD_TOKEN)
        print("bot.run() returned - this should not happen unless bot stops")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to start bot: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
    finally:
        print("Bot execution finished")