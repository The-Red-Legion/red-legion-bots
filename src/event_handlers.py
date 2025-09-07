import discord
from discord.ext import tasks, commands
from datetime import datetime
import time
import random
import aiohttp
import psycopg2
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import send_embed, has_org_role
from database import (
    save_mining_participation, save_event, update_event_end_time, update_entries, get_entries,
    update_mining_results, get_open_events
)
from config import DISCORD_CONFIG, ORE_TYPES, get_database_url, UEX_API_CONFIG

# Extract commonly used values
ORG_ROLE_ID = DISCORD_CONFIG['ORG_ROLE_ID']
LOG_CHANNEL_ID = DISCORD_CONFIG['TEXT_CHANNEL_ID']
DATABASE_URL = get_database_url()
MINING_MATERIALS = ORE_TYPES  # Alias for compatibility
UEX_API_KEY = UEX_API_CONFIG.get('api_key', 'dummy-key')  # Fallback

active_voice_channels = {}
event_names = {}
member_times = {}
last_checks = {}

async def on_voice_state_update(member, before, after):
    try:
        for channel_id, active_channel in list(active_voice_channels.items()):
            if active_channel:
                current_time = time.time()
                if after.channel == active_channel and before.channel != active_channel:
                    last_checks.setdefault(channel_id, {})
                    last_checks[channel_id][member.id] = current_time
                    print(
                        f"Member {member.display_name} joined channel "
                        f"{active_channel.name} at {current_time}"
                    )
                elif before.channel == active_channel and after.channel != active_channel:
                    if member.id in last_checks.get(channel_id, {}):
                        duration = current_time - last_checks[channel_id][member.id]
                        member_times.setdefault(channel_id, {})
                        member_times[channel_id][member.id] = (
                            member_times.get(channel_id, {}).get(member.id, 0) + duration
                        )
                        print(
                            f"Member {member.display_name} left channel "
                            f"{active_channel.name}, adding {duration:.2f}s "
                            f"to total: {member_times[channel_id][member.id]:.2f}s"
                        )
                        del last_checks[channel_id][member.id]
    except Exception as e:
        print(f"ERROR in on_voice_state_update: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())

@tasks.loop(seconds=60)
async def log_members(bot):
    for channel_id, active_channel in list(active_voice_channels.items()):
        if active_channel and channel_id in event_names:
            current_time = time.time()
            try:
                for member_id in list(last_checks.get(channel_id, {}).keys()):
                    # Get member object from guild, not just user
                    guild = active_channel.guild
                    member = guild.get_member(member_id)
                    if member and member in active_channel.members:
                        duration = current_time - last_checks[channel_id][member_id]
                        member_times.setdefault(channel_id, {})
                        member_times[channel_id][member_id] = (
                            member_times.get(channel_id, {}).get(member_id, 0) +
                            duration
                        )
                        last_checks[channel_id][member_id] = current_time
                        print(
                            f"Update for {member.display_name} in "
                            f"{active_channel.name}: added {duration:.2f}s, "
                            f"total {member_times[channel_id][member_id]:.2f}s"
                        )
                        is_org_member = str(ORG_ROLE_ID) in [
                            str(role.id) for role in member.roles
                        ]
                        # Legacy participation tracking - consider updating to use event-based tracking
                        # For now, create a temporary event if none exists
                        try:
                            from datetime import datetime
                            current_time = datetime.now()
                            # Use channel_id as a temporary event_id for legacy compatibility
                            temp_event_id = 1  # Default event ID for legacy tracking
                            
                            save_mining_participation(
                                DATABASE_URL,
                                temp_event_id,  # event_id
                                member_id,
                                member.display_name,
                                channel_id,
                                active_channel.name,
                                current_time,  # start_time
                                current_time,  # end_time (will be updated)
                                int(member_times[channel_id][member_id]),  # duration_seconds
                                is_org_member
                            )
                        except Exception as save_error:
                            print(f"Error saving participation: {save_error}")
                            # Continue without failing the tracking
            except Exception as e:
                print(f"Error in log_members: {e}")
                import traceback
                print("Full traceback:")
                print(traceback.format_exc())

async def start_logging(bot, ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You must be in a voice channel to start logging.")
        return
    channel_id = ctx.author.voice.channel.id
    if channel_id in active_voice_channels:
        await ctx.send(f"Logging is already active for {ctx.author.voice.channel.name}.")
        return
    active_voice_channels[channel_id] = ctx.author.voice.channel
    await ctx.send("Please provide the event name for this logging session.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', check=check, timeout=60.0)
        event_name = msg.content.strip()
        if not event_name:
            await ctx.send("Event name cannot be empty. Please try again.")
            del active_voice_channels[channel_id]
            return
        event_names[channel_id] = event_name
        member_times[channel_id] = {}
        last_checks[channel_id] = {}
        current_time = time.time()
        for member in active_voice_channels[channel_id].members:
            last_checks[channel_id][member.id] = current_time
            member_times[channel_id][member.id] = 0
            print(
                f"Started tracking {member.display_name} in "
                f"{ctx.author.voice.channel.name} at {current_time}"
            )
        try:
            save_event(
                DATABASE_URL,
                channel_id,
                ctx.author.voice.channel.name,
                event_name,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            log_channel = bot.get_channel(int(LOG_CHANNEL_ID))
            if log_channel:
                await send_embed(
                    log_channel,
                    "Logging Started",
                    f"**Event**: {event_name}\n**Channel**: {active_voice_channels[channel_id].name}",
                    discord.Color.green(),
                    datetime.now()
                )
            else:
                await ctx.send(f"Text channel ID {LOG_CHANNEL_ID} not found")
            if not log_members.is_running():
                log_members.start(bot)
            await ctx.send(
                f"Bot is running and logging started for "
                f"{active_voice_channels[channel_id].name} "
                f"(Event: {event_name}, every minute)."
            )
        except Exception as e:
            await ctx.send(f"Failed to connect to database: {e}")
            del active_voice_channels[channel_id]
    except commands.errors.CommandInvokeError:
        await ctx.send("Timed out waiting for event name. Please try again.")
        del active_voice_channels[channel_id]

async def stop_logging(bot, ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You must be in a voice channel to stop logging.")
        return
    channel_id = ctx.author.voice.channel.id
    if channel_id not in active_voice_channels:
        await ctx.send("No logging is active for this channel.")
        return

    try:
        # Query open events for this channel
        open_events = get_open_events(DATABASE_URL, channel_id)

        if not open_events:
            await ctx.send("No open events found for this channel.")
            del active_voice_channels[channel_id]
            return

        # Create select menu for open events
        options = [
            discord.SelectOption(
                label=f"ID: {event_id} - {event_name}",
                value=str(event_id),
                description=f"Channel: {channel_name}, Started: {start_time}"
            )
            for event_id, event_name, channel_name, start_time in open_events
        ]
        select = discord.ui.Select(
            placeholder="Select an event to stop logging",
            options=options,
            custom_id=f"stop_logging_select_{channel_id}"
        )
        view = discord.ui.View()
        view.add_item(select)

        # Send embed with select menu
        embed = discord.Embed(
            title="Stop Logging - Select Event",
            description="Choose an event to stop logging.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        await ctx.send(embed=embed, view=view)

        # Handle select menu interaction
        async def select_callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("Only the command issuer can select.", ephemeral=True)
                return
            event_id = int(interaction.data['values'][0])
            event_name = next(e[1] for e in open_events if e[0] == event_id)

            current_time = time.time()
            current_month = datetime.now().strftime("%B-%Y")
            try:
                # Save final durations
                for member_id in list(member_times.get(channel_id, {}).keys()):
                    member = ctx.guild.get_member(member_id)
                    if member:
                        total_duration = member_times.get(channel_id, {}).get(member_id, 0)
                        if member.id in last_checks.get(channel_id, {}):
                            duration = current_time - last_checks[channel_id][member.id]
                            total_duration += duration
                            print(
                                f"Final update for {member.display_name} in "
                                f"{active_voice_channels[channel_id].name}: "
                                f"added {duration:.2f}s, total {total_duration:.2f}s"
                            )
                        is_org_member = str(ORG_ROLE_ID) in [
                            str(role.id) for role in member.roles
                        ]
                        # Legacy participation tracking - consider updating to use event-based tracking
                        try:
                            from datetime import datetime
                            current_time = datetime.now()
                            temp_event_id = 1  # Default event ID for legacy tracking
                            
                            save_mining_participation(
                                DATABASE_URL,
                                temp_event_id,  # event_id
                                member_id,
                                member.display_name,
                                channel_id,
                                active_voice_channels[channel_id].name,
                                current_time,  # start_time
                                current_time,  # end_time
                                int(total_duration),  # duration_seconds
                                is_org_member
                            )
                        except Exception as save_error:
                            print(f"Error saving final participation: {save_error}")
                            # Continue without failing
                        update_entries(DATABASE_URL, member_id, current_month)
                update_event_end_time(
                    DATABASE_URL,
                    channel_id,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                log_channel = bot.get_channel(int(LOG_CHANNEL_ID))
                if log_channel:
                    await send_embed(
                        log_channel,
                        "Logging Stopped",
                        f"**Event**: {event_name}\n**Channel**: {active_voice_channels[channel_id].name}",
                        discord.Color.red(),
                        datetime.now()
                    )
                del active_voice_channels[channel_id]
                del event_names[channel_id]
                del member_times[channel_id]
                del last_checks[channel_id]
                if not active_voice_channels:
                    log_members.stop()
                await interaction.response.send_message(
                    f"Successfully stopped logging for event ID {event_id} ({event_name}). "
                    f"Use !log_mining_results {event_id} to enter SCUs and prices next."
                )
            except Exception as e:
                await interaction.response.send_message(f"Failed to stop logging: {e}", ephemeral=True)

        select.callback = select_callback
        bot.add_view(view)  # Persist view for interactions

    except Exception as e:
        await ctx.send(f"Failed to connect to database: {e}")

async def pick_winner(bot, ctx):
    print(f"pick_winner invoked by {ctx.author.display_name} at {datetime.now()}")
    try:
        current_month = datetime.now().strftime("%B-%Y")
        entries = get_entries(DATABASE_URL, current_month)
        if not entries:
            await ctx.send("No entries available for this month.")
            return
        candidates = []
        weights = []
        for user_id, entry_count in entries:
            member = ctx.guild.get_member(int(user_id))
            if member and str(ORG_ROLE_ID) in [str(role.id) for role in member.roles]:
                candidates.append(user_id)
                weights.append(entry_count)
        if not candidates:
            await ctx.send("No org members with entries this month.")
            return
        winner_id = random.choices(candidates, weights=weights)[0]
        winner = await bot.fetch_user(int(winner_id))
        await ctx.send(
            f"TEST ONLY | Congratulations {winner.display_name}! "
            f"You are the winner for {current_month} org raffle!"
        )
    except Exception as e:
        await ctx.send(f"Failed to connect to database: {e}")

async def log_mining_results(bot, ctx, event_id: int):
    if not await has_org_role()(ctx):
        return
    try:
        # Pre-fetch UEX prices for pre-population
        price_cache = {}
        async with aiohttp.ClientSession() as session:
            for material in MINING_MATERIALS:
                try:
                    async with session.get(
                        f"https://api.uexcorp.space/commodities?code={material}",
                        headers={"api_key": UEX_API_KEY},
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            price_cache[material] = float(data.get('sell_price', 0)) or 0
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    price_cache[material] = 0  # Default to 0 on failure

        embed = discord.Embed(
            title=f"Log Mining Results (Event {event_id})",
            description="Enter SCUs and overwrite prices if needed. Use 0 or leave blank for materials not mined.",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        await ctx.send(embed=embed)

        # Split materials into two modals due to 20 materials
        first_half = MINING_MATERIALS[:10]  # Stileron to Agricium
        second_half = MINING_MATERIALS[10:]  # Hephaestanite to Silicon

        class MiningModal1(discord.ui.Modal, title="Enter SCUs and Prices (Part 1)"):
            def __init__(self, price_cache):
                super().__init__()
                self.price_cache = price_cache
                for material in first_half:
                    self.add_item(discord.ui.TextInput(
                        label=f"{material} SCUs",
                        placeholder="Enter SCUs (e.g., 1000) or 0",
                        custom_id=f"{material}_scu",
                        style=discord.TextStyle.short,
                        required=False,
                        default=""
                    ))
                    self.add_item(discord.ui.TextInput(
                        label=f"{material} Price",
                        placeholder=f"Default: {self.price_cache.get(material, 0)}",
                        custom_id=f"{material}_price",
                        style=discord.TextStyle.short,
                        required=False,
                        default=str(self.price_cache.get(material, 0))
                    ))

            async def on_submit(self, interaction):
                await process_mining_modal(interaction, first_half)

        class MiningModal2(discord.ui.Modal, title="Enter SCUs and Prices (Part 2)"):
            def __init__(self, price_cache):
                super().__init__()
                self.price_cache = price_cache
                for material in second_half:
                    self.add_item(discord.ui.TextInput(
                        label=f"{material} SCUs",
                        placeholder="Enter SCUs (e.g., 1000) or 0",
                        custom_id=f"{material}_scu",
                        style=discord.TextStyle.short,
                        required=False,
                        default=""
                    ))
                    self.add_item(discord.ui.TextInput(
                        label=f"{material} Price",
                        placeholder=f"Default: {self.price_cache.get(material, 0)}",
                        custom_id=f"{material}_price",
                        style=discord.TextStyle.short,
                        required=False,
                        default=str(self.price_cache.get(material, 0))
                    ))

            async def on_submit(self, interaction):
                await process_mining_modal(interaction, second_half)

        async def process_mining_modal(interaction, materials):
            try:
                materials_data = []
                total_value = 0

                async with aiohttp.ClientSession():
                    for material in MINING_MATERIALS:
                        scu_input = interaction.data.get('components', {}).get(
                            MINING_MATERIALS.index(material) * 2, {}).get('components', [{}])[0].get('value', '')
                        price_input = interaction.data.get('components', {}).get(
                            (MINING_MATERIALS.index(material) * 2) + 1, {}).get('components', [{}])[0].get('value', '')
                        scu_refined = int(scu_input) if scu_input.strip() else 0
                        price = float(price_input) if price_input.strip() else price_cache.get(material, 0)
                        if scu_refined < 0 or price < 0:
                            await interaction.response.send_message(f"SCUs and price for {material} must be non-negative.", ephemeral=True)
                            return
                        if scu_refined == 0:
                            continue

                        material_value = scu_refined * price
                        materials_data.append((material, scu_refined, material_value))
                        total_value += material_value

                if not materials_data:
                    await interaction.response.send_message("No materials with valid SCUs entered.", ephemeral=True)
                    return

                update_mining_results(DATABASE_URL, event_id, materials_data)

                # Get participation data from the enhanced mining_participation table
                conn = psycopg2.connect(DATABASE_URL)
                c = conn.cursor()
                c.execute(
                    """
                    SELECT member_id, SUM(duration_seconds) as total_duration
                    FROM mining_participation
                    WHERE event_id = %s
                    GROUP BY member_id
                    """,
                    (event_id,)
                )
                durations = {row[0]: row[1] for row in c.fetchall()}
                conn.close()

                if not durations:
                    await interaction.response.send_message("No participation data for this event.", ephemeral=True)
                    return

                total_duration = sum(durations.values())
                if total_duration == 0:
                    await interaction.response.send_message("No valid participation durations.", ephemeral=True)
                    return
                payroll = {user_id: (dur / total_duration) * total_value for user_id, dur in durations.items()}

                embed = discord.Embed(title=f"Payroll for Event {event_id}", color=discord.Color.gold())
                for user_id, amount in payroll.items():
                    user = await bot.fetch_user(int(user_id))
                    embed.add_field(name=user.display_name, value=f"{amount:.2f} credits", inline=False)
                for material, scu_refined, _ in materials_data:
                    embed.add_field(name=f"{material} (SCUs)", value=scu_refined, inline=True)
                embed.add_field(name="Total Value", value=f"{total_value:.2f} credits", inline=True)
                await send_embed(interaction.channel, embed.title, embed.description, embed.color, datetime.now())
                await interaction.response.send_message("Payroll calculated successfully.", ephemeral=True)

            except ValueError:
                await interaction.response.send_message("SCUs and prices must be numbers.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"Error processing payroll: {e}", ephemeral=True)

        # Send first modal with pre-fetched prices
        await ctx.interaction.response.send_modal(MiningModal1(price_cache))
        if second_half:
            await ctx.send("Please complete the second part of the modal when ready.")
            await ctx.interaction.followup.send_modal(MiningModal2(price_cache))

    except Exception as e:
        await ctx.send(f"Error initiating payroll: {e}")

async def list_open_events(bot, ctx):
    if not await has_org_role()(ctx):
        return
    try:
        # Use the proper async database function instead of direct psycopg2 calls
        open_events = get_open_events(DATABASE_URL, ctx.channel.id if hasattr(ctx, 'channel') else '0')
        
        if not open_events:
            await ctx.send("No open events found.")
            return

        embed = discord.Embed(title="Open Events", color=discord.Color.blue(), timestamp=datetime.now())
        for event_id, event_name, channel_name, start_time in open_events:
            embed.add_field(
                name=f"Event ID: {event_id} - {event_name}",
                value=f"Channel: {channel_name}\nStarted: {start_time}",
                inline=False
            )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error fetching open events: {e}")
        print(f"ERROR in list_open_events: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())


async def setup_event_handlers():
    """Set up event handlers - compatibility function for modular system."""
    # This function is kept for backwards compatibility
    # Most event handling is now done in the modular system
    print("✅ Event handlers setup (compatibility mode)")
    pass