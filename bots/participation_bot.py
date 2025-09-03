   import discord
   from discord.ext import tasks, commands
   import datetime
   import time
   import os
   import psycopg2
   import random
   from functools import wraps

   intents = discord.Intents.default()
   intents.members = True
   intents.voice_states = True
   intents.message_content = True
   bot = commands.Bot(command_prefix='!', intents=intents)

   LOG_CHANNEL_ID = os.getenv('TEXT_CHANNEL_ID')
   if not LOG_CHANNEL_ID:
       raise ValueError("TEXT_CHANNEL_ID environment variable not set")

   ORG_ROLE_ID = "1143413611184795658"
   active_voice_channels = {}
   event_names = {}
   member_times = {}
   last_checks = {}


   # Retry decorator for database operations
   def retry_db_operation(max_attempts=3, delay=5):
       def decorator(func):
           @wraps(func)
           def wrapper(*args, **kwargs):
               attempts = 0
               while attempts < max_attempts:
                   try:
                       return func(*args, **kwargs)
                   except psycopg2.OperationalError as e:
                       attempts += 1
                       if attempts == max_attempts:
                           raise e
                       print(f"Database error: {e}. Retrying in {delay}s...")
                       time.sleep(delay)
               return wrapper
           return decorator


   # Custom check for role-based command permission
   def has_org_role():
       def predicate(ctx):
           role = discord.utils.get(ctx.author.roles, id=int(ORG_ROLE_ID))
           if not role:
               raise commands.MissingPermissions(
                   "You need the OrgMember role to use this command."
               )
           return True
       return commands.check(predicate)


   # Initialize database
   @retry_db_operation()
   def init_db():
       conn = psycopg2.connect(os.getenv("DATABASE_URL"))
       c = conn.cursor()
       c.execute('''CREATE TABLE IF NOT EXISTS entries (
           user_id TEXT,
           month_year TEXT,
           entry_count INTEGER DEFAULT 0,
           PRIMARY KEY (user_id, month_year)
       )''')
       c.execute('''CREATE TABLE IF NOT EXISTS events (
           event_id SERIAL PRIMARY KEY,
           channel_id TEXT,
           channel_name TEXT,
           event_name TEXT,
           start_time TEXT,
           end_time TEXT
       )''')
       c.execute('''CREATE TABLE IF NOT EXISTS participation (
           channel_id TEXT,
           member_id TEXT,
           username TEXT,
           duration REAL,
           is_org_member BOOLEAN,
           UNIQUE (channel_id, member_id)
       )''')
       conn.commit()
       conn.close()


   @bot.event
   async def on_ready():
       print(f'Logged in as {bot.user}')
       try:
           init_db()
       except Exception as e:
           print(f"Error during database initialization: {e}")


   @bot.event
   async def on_voice_state_update(member, before, after):
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
                           f"to total time: {member_times[channel_id][member.id]:.2f}s"
                       )
                       del last_checks[channel_id][member.id]


   @tasks.loop(seconds=60)
   async def log_members():
       for channel_id, active_channel in list(active_voice_channels.items()):
           if active_channel and channel_id in event_names:
               current_time = time.time()
               try:
                   conn = psycopg2.connect(os.getenv("DATABASE_URL"))
                   c = conn.cursor()
                   for member_id in list(last_checks.get(channel_id, {}).keys()):
                       member = bot.get_user(member_id)
                       if member in active_channel.members:
                           duration = current_time - last_checks[channel_id][member_id]
                           member_times.setdefault(channel_id, {})
                           member_times[channel_id][member_id] = (
                               member_times.get(channel_id, {}).get(member_id, 0) + duration
                           )
                           last_checks[channel_id][member_id] = current_time
                           print(
                               f"Periodic update for {member.display_name} in "
                               f"{active_channel.name}: added {duration:.2f}s, "
                               f"total {member_times[channel_id][member_id]:.2f}s"
                           )
                           is_org_member = str(ORG_ROLE_ID) in [
                               str(role.id) for role in member.roles
                           ]
                           c.execute(
                               """
                               INSERT INTO participation (
                                   channel_id, member_id, username, duration, is_org_member
                               )
                               VALUES (%s, %s, %s, %s, %s)
                               ON CONFLICT (channel_id, member_id)
                               DO UPDATE SET duration = EXCLUDED.duration,
                                            username = EXCLUDED.username,
                                            is_org_member = EXCLUDED.is_org_member
                               """,
                               (
                                   str(channel_id),
                                   str(member_id),
                                   member.display_name,
                                   member_times[channel_id][member_id],
                                   is_org_member
                               )
                           )
                   conn.commit()
                   conn.close()
               except psycopg2.OperationalError as e:
                   print(f"Database error in log_members: {e}")


   @bot.command()
   @has_org_role()
   async def start_logging(ctx):
       if ctx.author.voice and ctx.author.voice.channel:
           channel_id = ctx.author.voice.channel.id
           if channel_id in active_voice_channels:
               await ctx.send(
                   f"Logging is already active for {ctx.author.voice.channel.name}."
               )
               return
           active_voice_channels[channel_id] = ctx.author.voice.channel
           await ctx.send("Please provide the event name for this logging session.")
           def check(m):
               return m.author == ctx.author and m.channel == ctx.channel
           try:
               msg = await bot.wait_for('message', check=check, timeout=60.0)
               event_name = msg.content.strip()
               if event_name:
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
                       conn = psycopg2.connect(os.getenv("DATABASE_URL"))
                       c = conn.cursor()
                       c.execute(
                           "INSERT INTO events (channel_id, channel_name, event_name, start_time) "
                           "VALUES (%s, %s, %s, %s)",
                           (
                               str(channel_id),
                               ctx.author.voice.channel.name,
                               event_name,
                               datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                           )
                       )
                       conn.commit()
                       conn.close()
                   except psycopg2.OperationalError as e:
                       await ctx.send(f"Failed to connect to database: {e}")
                       del active_voice_channels[channel_id]
                       return
                   log_channel = bot.get_channel(int(LOG_CHANNEL_ID))
                   if log_channel:
                       try:
                           embed = discord.Embed(
                               title="Logging Started",
                               description=(
                                   f"**Event**: {event_name}\n"
                                   f"**Channel**: {active_voice_channels[channel_id].name}"
                               ),
                               color=discord.Color.green(),
                               timestamp=datetime.datetime.now()
                           )
                           await log_channel.send(embed=embed)
                       except discord.errors.Forbidden:
                           await ctx.send(
                               f"Error: Bot lacks permission to send messages "
                               f"to channel {LOG_CHANNEL_ID}"
                           )
                           return
                   else:
                       await ctx.send(f"Text channel ID {LOG_CHANNEL_ID} not found")
                   if not log_members.is_running():
                       log_members.start()
                   await ctx.send(
                       f"Bot is running and logging started for "
                       f"{active_voice_channels[channel_id].name} "
                       f"(Event: {event_name}, every minute)."
                   )
               else:
                   await ctx.send("Event name cannot be empty. Please try again.")
                   del active_voice_channels[channel_id]
           except discord.ext.commands.errors.CommandInvokeError:
               await ctx.send("Timed out waiting for event name. Please try again.")
               del active_voice_channels[channel_id]
       else:
           await ctx.send("You must be in a voice channel to start logging.")


   @bot.command()
   @has_org_role()
   async def stop_logging(ctx):
       if ctx.author.voice and ctx.author.voice.channel:
           channel_id = ctx.author.voice.channel.id
           print(f"Active channels: {active_voice_channels}")
           print(f"Channel ID: {channel_id}")
           if channel_id in active_voice_channels:
               current_time = time.time()
               current_month = datetime.datetime.now().strftime("%B-%Y")
               try:
                   conn = psycopg2.connect(os.getenv("DATABASE_URL"))
                   c = conn.cursor()
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
                           c.execute(
                               """
                               INSERT INTO participation (
                                   channel_id, member_id, username, duration, is_org_member
                               )
                               VALUES (%s, %s, %s, %s, %s)
                               ON CONFLICT (channel_id, member_id)
                               DO UPDATE SET duration = EXCLUDED.duration,
                                            username = EXCLUDED.username,
                                            is_org_member = EXCLUDED.is_org_member
                               """,
                               (
                                   str(channel_id),
                                   str(member_id),
                                   member.display_name,
                                   total_duration,
                                   is_org_member
                               )
                           )
                           print(
                               f"Saved {member.display_name} in "
                               f"{active_voice_channels[channel_id].name} with "
                               f"total duration {total_duration:.2f}s"
                           )
                           c.execute(
                               """
                               INSERT INTO entries (
                                   user_id, month_year, entry_count
                               )
                               VALUES (%s, %s, %s)
                               ON CONFLICT (user_id, month_year)
                               DO UPDATE SET entry_count = entries.entry_count + 1
                               """,
                               (str(member_id), current_month, 1)
                           )
                   c.execute(
                       "UPDATE events SET end_time = %s WHERE channel_id = %s::text AND end_time IS NULL",
                       (
                           datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           str(channel_id)
                       )
                   )
                   conn.commit()
                   conn.close()
               except psycopg2.OperationalError as e:
                   await ctx.send(f"Failed to connect to database: {e}")
                   return
               log_channel = bot.get_channel(int(LOG_CHANNEL_ID))
               if log_channel:
                   try:
                       embed = discord.Embed(
                           title="Logging Stopped",
                           description=(
                               f"**Event**: {event_names[channel_id]}\n"
                               f"**Channel**: {active_voice_channels[channel_id].name}"
                           ),
                           color=discord.Color.red(),
                           timestamp=datetime.datetime.now()
                       )
                       await log_channel.send(embed=embed)
                   except discord.errors.Forbidden:
                       await ctx.send(
                           f"Error: Bot lacks permission to send messages "
                           f"to channel {LOG_CHANNEL_ID}"
                       )
               del active_voice_channels[channel_id]
               del event_names[channel_id]
               del member_times[channel_id]
               del last_checks[channel_id]
               if not active_voice_channels:
                   log_members.stop()
               await ctx.send("Successfully stopped logging for this channel.")
           else:
               await ctx.send("No logging is active for this voice channel.")
       else:
           await ctx.send("You must be in a voice channel to stop logging.")


   @bot.command()
   @commands.cooldown(1, 30, commands.BucketType.guild)
   @has_org_role()
   async def pick_winner(ctx):
       print(
           f"pick_winner invoked by {ctx.author.display_name} "
           f"at {datetime.datetime.now()}"
       )
       try:
           conn = psycopg2.connect(os.getenv("DATABASE_URL"))
           c = conn.cursor()
           current_month = datetime.datetime.now().strftime("%B-%Y")
           c.execute(
               "SELECT user_id, entry_count FROM entries WHERE month_year = %s",
               (current_month,)
           )
           entries = c.fetchall()
           conn.close()
       except psycopg2.OperationalError as e:
           await ctx.send(f"Failed to connect to database: {e}")
           return
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

   bot.run(os.getenv('DISCORD_TOKEN'))