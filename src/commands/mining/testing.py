"""
Sunday Mining Start Command Testing and Verification Framework

This module provides comprehensive testing for the /redsundayminingstart command
including schema verification, voice channel testing, and debugging.
"""

import discord
from datetime import datetime
from config.channels import get_sunday_mining_channels
from handlers.voice_tracking import set_bot_instance, add_tracked_channel, join_voice_channel

class SundayMiningTester:
    """Comprehensive testing for Sunday Mining functionality."""
    
    def __init__(self, bot, guild=None):
        self.bot = bot
        self.guild = guild
        self.test_results = {}
    
    async def run_comprehensive_test(self, interaction: discord.Interaction):
        """Run all tests and return detailed results."""
        self.test_results = {}
        
        # Test 1: Database Schema Verification
        await self._test_database_schema()
        
        # Test 2: Voice Channel Configuration  
        await self._test_voice_channel_config(interaction.guild)
        
        # Test 3: Bot Voice Permissions
        await self._test_bot_voice_permissions(interaction.guild)
        
        # Test 4: Voice Channel Connection Test
        await self._test_voice_channel_connection()
        
        # Test 5: Guild Verification
        await self._test_guild_verification(interaction.guild)
        
        # Return comprehensive results
        return self._generate_test_report()
    
    async def _test_database_schema(self):
        """Test database schema completeness."""
        self.test_results['database'] = {
            'status': 'pending',
            'details': [],
            'errors': []
        }
        
        try:
            from config.settings import get_database_url
            from database.connection import DatabaseManager
            
            db_url = get_database_url()
            if not db_url:
                self.test_results['database']['status'] = 'failed'
                self.test_results['database']['errors'].append('No database URL configured')
                return
            
            # Test database connection
            db_manager = DatabaseManager(db_url)
            with db_manager.get_cursor() as cursor:
                
                # Check required tables exist
                required_tables = ['events', 'guilds', 'mining_channels', 'mining_participation']
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = ANY(%s)
                """, (required_tables,))
                
                existing_tables = [row[0] for row in cursor.fetchall()]
                missing_tables = set(required_tables) - set(existing_tables)
                
                if missing_tables:
                    self.test_results['database']['status'] = 'failed'
                    self.test_results['database']['errors'].append(f'Missing tables: {list(missing_tables)}')
                else:
                    self.test_results['database']['details'].append('All required tables exist')
                
                # Check events table has required columns
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'events' AND table_schema = 'public'
                """)
                events_columns = [row[0] for row in cursor.fetchall()]
                required_events_columns = ['id', 'guild_id', 'event_date', 'is_open']
                
                missing_cols = set(required_events_columns) - set(events_columns)
                if missing_cols:
                    self.test_results['database']['errors'].append(f'Events table missing columns: {list(missing_cols)}')
                else:
                    self.test_results['database']['details'].append('Events table has required columns')
                
                # Check mining_participation table structure
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'mining_participation' AND table_schema = 'public'
                """)
                participation_columns = [row[0] for row in cursor.fetchall()]
                required_participation_columns = ['event_id', 'member_id', 'username', 'channel_id', 'start_time']
                
                missing_part_cols = set(required_participation_columns) - set(participation_columns)
                if missing_part_cols:
                    self.test_results['database']['errors'].append(f'Mining_participation missing columns: {list(missing_part_cols)}')
                else:
                    self.test_results['database']['details'].append('Mining_participation table has required columns')
                
                if not self.test_results['database']['errors']:
                    self.test_results['database']['status'] = 'passed'
                    
        except Exception as e:
            self.test_results['database']['status'] = 'failed'
            self.test_results['database']['errors'].append(f'Database test error: {str(e)}')
    
    async def _test_voice_channel_config(self, guild):
        """Test voice channel configuration."""
        self.test_results['voice_config'] = {
            'status': 'pending',
            'details': [],
            'errors': [],
            'channels': {}
        }
        
        try:
            mining_channels = get_sunday_mining_channels(self.guild.id)
            
            if not mining_channels:
                self.test_results['voice_config']['status'] = 'failed'
                self.test_results['voice_config']['errors'].append('No mining channels configured')
                return
            
            self.test_results['voice_config']['details'].append(f'Found {len(mining_channels)} configured channels')
            
            # Check each channel exists and is accessible
            for channel_name, channel_id in mining_channels.items():
                channel_info = {
                    'exists': False,
                    'is_voice': False,
                    'bot_can_see': False,
                    'bot_can_join': False,
                    'name': 'unknown'
                }
                
                try:
                    channel_id_int = int(channel_id)
                    channel = guild.get_channel(channel_id_int)
                    
                    if channel:
                        channel_info['exists'] = True
                        channel_info['name'] = channel.name
                        channel_info['bot_can_see'] = True
                        
                        if isinstance(channel, discord.VoiceChannel):
                            channel_info['is_voice'] = True
                            
                            # Check bot permissions
                            bot_member = guild.get_member(self.bot.user.id)
                            if bot_member:
                                perms = channel.permissions_for(bot_member)
                                channel_info['bot_can_join'] = perms.connect and perms.speak
                    else:
                        channel_info['exists'] = False
                        self.test_results['voice_config']['errors'].append(f'{channel_name}: Channel {channel_id} not found')
                
                except ValueError:
                    self.test_results['voice_config']['errors'].append(f'{channel_name}: Invalid channel ID {channel_id}')
                
                self.test_results['voice_config']['channels'][channel_name] = channel_info
            
            # Check if dispatch channel is properly configured
            if 'dispatch' not in mining_channels:
                self.test_results['voice_config']['errors'].append('No dispatch channel configured')
            
            if not self.test_results['voice_config']['errors']:
                self.test_results['voice_config']['status'] = 'passed'
            else:
                self.test_results['voice_config']['status'] = 'failed'
                
        except Exception as e:
            self.test_results['voice_config']['status'] = 'failed'
            self.test_results['voice_config']['errors'].append(f'Voice config test error: {str(e)}')
    
    async def _test_bot_voice_permissions(self, guild):
        """Test bot voice permissions."""
        self.test_results['voice_permissions'] = {
            'status': 'pending',
            'details': [],
            'errors': []
        }
        
        try:
            bot_member = guild.get_member(self.bot.user.id)
            if not bot_member:
                self.test_results['voice_permissions']['status'] = 'failed'
                self.test_results['voice_permissions']['errors'].append('Bot member not found in guild')
                return
            
            # Check general voice permissions
            guild_perms = bot_member.guild_permissions
            
            voice_perms = {
                'connect': guild_perms.connect,
                'speak': guild_perms.speak,
                'use_voice_activation': guild_perms.use_voice_activation,
                'move_members': guild_perms.move_members
            }
            
            for perm, has_perm in voice_perms.items():
                if has_perm:
                    self.test_results['voice_permissions']['details'].append(f'Has {perm} permission')
                else:
                    self.test_results['voice_permissions']['errors'].append(f'Missing {perm} permission')
            
            if not self.test_results['voice_permissions']['errors']:
                self.test_results['voice_permissions']['status'] = 'passed'
            else:
                self.test_results['voice_permissions']['status'] = 'failed'
                
        except Exception as e:
            self.test_results['voice_permissions']['status'] = 'failed'
            self.test_results['voice_permissions']['errors'].append(f'Permission test error: {str(e)}')
    
    async def _test_voice_channel_connection(self):
        """Test actual voice channel connection."""
        self.test_results['voice_connection'] = {
            'status': 'pending',
            'details': [],
            'errors': []
        }
        
        try:
            # Set bot instance for voice operations
            set_bot_instance(self.bot)
            
            mining_channels = get_sunday_mining_channels(self.guild.id)
            dispatch_channel_id = mining_channels.get('dispatch')
            
            if not dispatch_channel_id:
                self.test_results['voice_connection']['status'] = 'failed'
                self.test_results['voice_connection']['errors'].append('No dispatch channel configured for testing')
                return
            
            # Test joining the dispatch channel
            try:
                success = await join_voice_channel(int(dispatch_channel_id))
                if success:
                    self.test_results['voice_connection']['status'] = 'passed'
                    self.test_results['voice_connection']['details'].append('Successfully joined dispatch channel')
                    
                    # Leave the channel after test
                    channel = self.bot.get_channel(int(dispatch_channel_id))
                    if channel and channel.guild.voice_client:
                        await channel.guild.voice_client.disconnect()
                        self.test_results['voice_connection']['details'].append('Successfully left dispatch channel after test')
                else:
                    self.test_results['voice_connection']['status'] = 'failed'
                    self.test_results['voice_connection']['errors'].append('Failed to join dispatch channel')
                    
            except Exception as e:
                self.test_results['voice_connection']['status'] = 'failed'
                self.test_results['voice_connection']['errors'].append(f'Voice connection error: {str(e)}')
                
        except Exception as e:
            self.test_results['voice_connection']['status'] = 'failed'
            self.test_results['voice_connection']['errors'].append(f'Voice test error: {str(e)}')
    
    async def _test_guild_verification(self, guild):
        """Test guild setup in database."""
        self.test_results['guild_verification'] = {
            'status': 'pending',
            'details': [],
            'errors': []
        }
        
        try:
            from config.settings import get_database_url
            from database.connection import DatabaseManager
            
            db_url = get_database_url()
            if not db_url:
                self.test_results['guild_verification']['status'] = 'failed'
                self.test_results['guild_verification']['errors'].append('No database URL configured')
                return
            
            # Check if guild exists in database
            db_manager = DatabaseManager(db_url)
            with db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM guilds WHERE id = %s", (guild.id,))
                guild_record = cursor.fetchone()
                
                if guild_record:
                    self.test_results['guild_verification']['status'] = 'passed'
                    self.test_results['guild_verification']['details'].append(f'Guild {guild.name} exists in database')
                else:
                    self.test_results['guild_verification']['status'] = 'failed'
                    self.test_results['guild_verification']['errors'].append(f'Guild {guild.name} ({guild.id}) not found in database')
                    self.test_results['guild_verification']['details'].append('Use: INSERT INTO guilds (id, name) VALUES (%s, %s) to fix')
                    
        except Exception as e:
            self.test_results['guild_verification']['status'] = 'failed'
            self.test_results['guild_verification']['errors'].append(f'Guild verification error: {str(e)}')
    
    def _generate_test_report(self):
        """Generate comprehensive test report embed."""
        # Count passed/failed tests
        passed = sum(1 for test in self.test_results.values() if test['status'] == 'passed')
        failed = sum(1 for test in self.test_results.values() if test['status'] == 'failed')
        total = len(self.test_results)
        
        # Determine overall status
        if failed == 0:
            color = 0x00ff00  # Green
            title = "✅ All Sunday Mining Tests Passed"
        elif passed == 0:
            color = 0xff0000  # Red
            title = "❌ All Sunday Mining Tests Failed"
        else:
            color = 0xffaa00  # Orange
            title = "⚠️ Sunday Mining Tests - Partial Pass"
        
        embed = discord.Embed(
            title=title,
            description=f"**Test Results:** {passed}/{total} tests passed",
            color=color,
            timestamp=datetime.now()
        )
        
        # Add detailed results for each test
        for test_name, results in self.test_results.items():
            status_emoji = "✅" if results['status'] == 'passed' else "❌"
            
            # Build field value
            field_lines = [f"{status_emoji} **Status:** {results['status'].title()}"]
            
            if results['details']:
                field_lines.append("**Details:**")
                for detail in results['details'][:3]:  # Limit to 3 details
                    field_lines.append(f"• {detail}")
            
            if results['errors']:
                field_lines.append("**Errors:**")
                for error in results['errors'][:3]:  # Limit to 3 errors
                    field_lines.append(f"• {error}")
            
            embed.add_field(
                name=f"🧪 {test_name.replace('_', ' ').title()}",
                value="\n".join(field_lines),
                inline=True
            )
        
        # Add voice channel details if available
        if 'voice_config' in self.test_results and 'channels' in self.test_results['voice_config']:
            channel_status = []
            for name, info in self.test_results['voice_config']['channels'].items():
                status = "✅" if info['exists'] and info['is_voice'] and info['bot_can_join'] else "❌"
                channel_status.append(f"{status} {name.title()}: {info['name']}")
            
            if channel_status:
                embed.add_field(
                    name="🎤 Voice Channel Status",
                    value="\n".join(channel_status[:6]),  # Limit to 6 channels
                    inline=False
                )
        
        embed.set_footer(text="Sunday Mining Diagnostic Report")
        
        return embed

# Add testing command to the mining commands
async def run_sunday_mining_diagnostics(interaction: discord.Interaction):
    """Run comprehensive Sunday Mining diagnostics."""
    await interaction.response.defer()
    
    tester = SundayMiningTester(interaction.client)
    report_embed = await tester.run_comprehensive_test(interaction)
    
    await interaction.followup.send(embed=report_embed)
