"""
Red Legion Organization Join/Application System
Implements /red-join subcommand group for organization recruitment
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)

class ApplicationFormModal(discord.ui.Modal, title='Red Legion Application'):
    """Modal form for organization applications"""
    
    def __init__(self, position: str):
        super().__init__()
        self.position = position
        
    sc_handle = discord.ui.TextInput(
        label='Star Citizen Handle',
        placeholder='Enter your SC handle (e.g., RedLegion_Pilot)',
        required=True,
        max_length=100
    )
    
    gaming_experience = discord.ui.TextInput(
        label='Gaming Experience',
        placeholder='Tell us about your gaming background and SC experience',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )
    
    why_join = discord.ui.TextInput(
        label='Why do you want to join Red Legion?',
        placeholder='What attracts you to our organization?',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )
    
    availability = discord.ui.TextInput(
        label='Availability',
        placeholder='What times/days are you usually available? (include timezone)',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )
    
    additional_info = discord.ui.TextInput(
        label='Additional Information',
        placeholder='Anything else you\'d like us to know? (optional)',
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle application submission"""
        try:
            # Import here to avoid circular imports
            from ..database.database import Database
            
            db = Database()
            
            # Generate unique application ID
            application_uid = await db.generate_application_uid()
            
            # Create application record
            application_data = {
                'guild_id': str(interaction.guild_id),
                'applicant_id': str(interaction.user.id),
                'applicant_name': interaction.user.display_name,
                'applicant_discriminator': interaction.user.discriminator,
                'application_uid': application_uid,
                'position_applied': self.position,
                'sc_handle': self.sc_handle.value,
                'gaming_experience': self.gaming_experience.value,
                'why_join_reason': self.why_join.value,
                'availability_info': self.availability.value,
                'additional_info': self.additional_info.value or None,
                'status': 'pending',
                'priority': 'normal'
            }
            
            application_id = await db.create_application(application_data)
            
            # Create success embed
            embed = discord.Embed(
                title="✅ Application Submitted Successfully!",
                description=f"Thank you for applying to Red Legion!",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="Application ID", value=f"`{application_uid}`", inline=True)
            embed.add_field(name="Position", value=self.position.title(), inline=True)
            embed.add_field(name="Status", value="Pending Review", inline=True)
            
            embed.add_field(
                name="🌐 Complete Your RSI Application",
                value=f"**REQUIRED:** Go to https://robertsspaceindustries.com/en/orgs/REDLEGN\n"
                      f"• Paste your Application ID: `{application_uid}`\n"
                      f"• Into the 'Your Application' box\n"
                      f"• Click Submit to complete the process",
                inline=False
            )
            
            embed.add_field(
                name="What's Next?",
                value="• Complete the RSI website application above\n"
                      "• Your application will be reviewed by our officers\n"
                      "• You'll be notified of any status changes\n"
                      "• Use `/redjoin status` to check your application\n"
                      "• Questions? Contact an officer directly",
                inline=False
            )
            
            embed.set_footer(text="Red Legion Recruitment System")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Notify officers in recruitment channel (if configured)
            await self._notify_officers(interaction, application_uid, application_data)
            
        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            await interaction.response.send_message(
                "❌ There was an error submitting your application. Please try again or contact an officer.",
                ephemeral=True
            )
    
    async def _notify_officers(self, interaction: discord.Interaction, app_uid: str, app_data: dict):
        """Notify officers of new application"""
        try:
            from ..database.database import Database
            
            db = Database()
            settings = await db.get_application_settings(str(interaction.guild_id))
            
            if not settings or not settings.get('recruitment_channel_id'):
                return
            
            channel = interaction.guild.get_channel(int(settings['recruitment_channel_id']))
            if not channel:
                return
            
            embed = discord.Embed(
                title="🆕 New Organization Application",
                description=f"**{app_data['applicant_name']}** has applied to join Red Legion",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="Application ID", value=f"`{app_uid}`", inline=True)
            embed.add_field(name="Position", value=app_data['position_applied'].title(), inline=True)
            embed.add_field(name="SC Handle", value=app_data['sc_handle'], inline=True)
            
            embed.add_field(
                name="Review Actions",
                value="Use `/redjoin review` to start the review process",
                inline=False
            )
            
            # Mention officer role if configured
            content = ""
            if settings.get('officer_notification_role_id'):
                content = f"<@&{settings['officer_notification_role_id']}>"
            
            await channel.send(content=content, embed=embed)
            
        except Exception as e:
            logger.error(f"Error notifying officers: {e}")

class RedJoinGroup(app_commands.Group):
    """Red Legion Join/Application command group"""
    
    def __init__(self):
        super().__init__(name='redjoin', description='Organization recruitment and application system')
    
    @app_commands.command(name='apply', description='Apply to join Red Legion organization')
    @app_commands.describe(position='The position you are applying for')
    @app_commands.choices(position=[
        app_commands.Choice(name='General Member', value='general'),
        app_commands.Choice(name='Pilot', value='pilot'),
        app_commands.Choice(name='Engineer', value='engineer'),
        app_commands.Choice(name='Trader', value='trader'),
        app_commands.Choice(name='Security Officer', value='security'),
        app_commands.Choice(name='Medical Officer', value='medic'),
        app_commands.Choice(name='Specialist Role', value='specialist')
    ])
    async def apply(self, interaction: discord.Interaction, position: app_commands.Choice[str]):
        """Submit an application to join the organization"""
        try:
            from ..database.database import Database
            
            db = Database()
            
            # Check if user already has a pending application
            existing = await db.get_user_pending_application(str(interaction.guild_id), str(interaction.user.id))
            if existing:
                embed = discord.Embed(
                    title="❌ Application Already Exists",
                    description=f"You already have a pending application: `{existing['application_uid']}`",
                    color=discord.Color.red()
                )
                embed.add_field(name="Status", value=existing['status'].title(), inline=True)
                embed.add_field(name="Use", value="`/redjoin status` to check progress", inline=True)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Show application form
            modal = ApplicationFormModal(position.value)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Error in apply command: {e}")
            await interaction.response.send_message(
                "❌ Error processing application. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name='status', description='Check your application status')
    async def status(self, interaction: discord.Interaction):
        """Check the status of your application"""
        try:
            from ..database.database import Database
            
            db = Database()
            application = await db.get_user_application_status(str(interaction.guild_id), str(interaction.user.id))
            
            if not application:
                embed = discord.Embed(
                    title="❌ No Application Found",
                    description="You don't have any applications on file.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Apply Now", value="Use `/redjoin apply` to submit an application", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create status embed
            status_colors = {
                'pending': discord.Color.yellow(),
                'reviewing': discord.Color.blue(),
                'interview_scheduled': discord.Color.purple(),
                'approved': discord.Color.green(),
                'denied': discord.Color.red(),
                'withdrawn': discord.Color.grey()
            }
            
            embed = discord.Embed(
                title="📋 Application Status",
                description=f"Application ID: `{application['application_uid']}`",
                color=status_colors.get(application['status'], discord.Color.blue()),
                timestamp=datetime.fromisoformat(str(application['submitted_date']))
            )
            
            embed.add_field(name="Position Applied", value=application['position_applied'].title(), inline=True)
            embed.add_field(name="Current Status", value=application['status'].replace('_', ' ').title(), inline=True)
            embed.add_field(name="Priority", value=application['priority'].title(), inline=True)
            
            if application['reviewed_by_name']:
                embed.add_field(name="Reviewed By", value=application['reviewed_by_name'], inline=True)
            
            if application['interview_scheduled_date']:
                embed.add_field(
                    name="Interview Scheduled",
                    value=f"<t:{int(datetime.fromisoformat(str(application['interview_scheduled_date'])).timestamp())}:F>",
                    inline=False
                )
            
            if application['decision_reason']:
                embed.add_field(name="Notes", value=application['decision_reason'], inline=False)
            
            # Add RSI reminder for pending applications
            if application['status'] in ['pending', 'reviewing']:
                embed.add_field(
                    name="🌐 RSI Application Required",
                    value=f"**Don't forget:** Complete your RSI application at\n"
                          f"https://robertsspaceindustries.com/en/orgs/REDLEGN\n"
                          f"Use Application ID: `{application['application_uid']}`",
                    inline=False
                )
            
            embed.set_footer(text="Submitted")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await interaction.response.send_message(
                "❌ Error retrieving application status.",
                ephemeral=True
            )
    
    @app_commands.command(name='withdraw', description='Withdraw your pending application')
    async def withdraw(self, interaction: discord.Interaction):
        """Withdraw your pending application"""
        try:
            from ..database.database import Database
            
            db = Database()
            application = await db.get_user_pending_application(str(interaction.guild_id), str(interaction.user.id))
            
            if not application:
                embed = discord.Embed(
                    title="❌ No Pending Application",
                    description="You don't have a pending application to withdraw.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Confirm withdrawal
            view = discord.ui.View(timeout=60)
            
            async def confirm_withdraw(confirm_interaction):
                await db.withdraw_application(application['application_id'])
                
                embed = discord.Embed(
                    title="✅ Application Withdrawn",
                    description=f"Your application `{application['application_uid']}` has been withdrawn.",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Reapply",
                    value="You can submit a new application anytime using `/red-join apply`",
                    inline=False
                )
                await confirm_interaction.response.edit_message(embed=embed, view=None)
            
            async def cancel_withdraw(cancel_interaction):
                embed = discord.Embed(
                    title="❌ Withdrawal Cancelled",
                    description="Your application remains active.",
                    color=discord.Color.blue()
                )
                await cancel_interaction.response.edit_message(embed=embed, view=None)
            
            confirm_button = discord.ui.Button(label='Confirm Withdrawal', style=discord.ButtonStyle.danger)
            cancel_button = discord.ui.Button(label='Cancel', style=discord.ButtonStyle.secondary)
            
            confirm_button.callback = confirm_withdraw
            cancel_button.callback = cancel_withdraw
            
            view.add_item(confirm_button)
            view.add_item(cancel_button)
            
            embed = discord.Embed(
                title="⚠️ Confirm Withdrawal",
                description=f"Are you sure you want to withdraw application `{application['application_uid']}`?",
                color=discord.Color.orange()
            )
            embed.add_field(name="This action cannot be undone", value="You'll need to reapply if you change your mind", inline=False)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in withdraw command: {e}")
            await interaction.response.send_message(
                "❌ Error processing withdrawal.",
                ephemeral=True
            )
    
    @app_commands.command(name='list', description='[OFFICER] List all applications')
    @app_commands.describe(
        status='Filter by status',
        position='Filter by position'
    )
    @app_commands.choices(status=[
        app_commands.Choice(name='Pending', value='pending'),
        app_commands.Choice(name='Reviewing', value='reviewing'),
        app_commands.Choice(name='Interview Scheduled', value='interview_scheduled'),
        app_commands.Choice(name='Approved', value='approved'),
        app_commands.Choice(name='Denied', value='denied'),
        app_commands.Choice(name='All', value='all')
    ])
    async def list_applications(self, interaction: discord.Interaction, status: app_commands.Choice[str] = None, position: str = None):
        """List all applications (officer command)"""
        try:
            # Check permissions
            if not any(role.name.lower() in ['officer', 'admin', 'leadership'] for role in interaction.user.roles):
                await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
                return
            
            from ..database.database import Database
            
            db = Database()
            
            filter_status = status.value if status and status.value != 'all' else None
            applications = await db.get_applications_list(str(interaction.guild_id), filter_status, position)
            
            if not applications:
                embed = discord.Embed(
                    title="📋 Applications List",
                    description="No applications found matching the criteria.",
                    color=discord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create paginated embed
            embed = discord.Embed(
                title="📋 Organization Applications",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Add filter info
            filters = []
            if filter_status:
                filters.append(f"Status: {filter_status.title()}")
            if position:
                filters.append(f"Position: {position.title()}")
            
            if filters:
                embed.description = f"**Filters:** {' | '.join(filters)}"
            
            # Add applications (limit to first 10)
            for app in applications[:10]:
                days_pending = (datetime.now(timezone.utc) - datetime.fromisoformat(str(app['submitted_date']))).days
                
                value = f"**Position:** {app['position_applied'].title()}\n"
                value += f"**Status:** {app['status'].replace('_', ' ').title()}\n"
                value += f"**Days Pending:** {days_pending}\n"
                if app['sc_handle']:
                    value += f"**SC Handle:** {app['sc_handle']}"
                
                embed.add_field(
                    name=f"{app['applicant_name']} | `{app['application_uid']}`",
                    value=value,
                    inline=True
                )
            
            if len(applications) > 10:
                embed.set_footer(text=f"Showing 10 of {len(applications)} applications")
            else:
                embed.set_footer(text=f"Total: {len(applications)} applications")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in list command: {e}")
            await interaction.response.send_message(
                "❌ Error retrieving applications list.",
                ephemeral=True
            )

class JoinManagement(commands.Cog):
    """Join Management Cog using Discord subcommand groups."""
    
    def __init__(self, bot):
        self.bot = bot
    
    # Properly register the command group
    redjoin = RedJoinGroup()


async def setup(bot):
    """Setup function for discord.py extension loading."""
    print("🔧 Setting up Join Management with subcommand groups...")
    try:
        cog = JoinManagement(bot)
        await bot.add_cog(cog)
        print("✅ Join Management cog loaded with subcommand groups")
        print("✅ Available commands:")
        print("   • /redjoin apply <position>")
        print("   • /redjoin status")
        print("   • /redjoin withdraw")
        print("   • /redjoin list [status] [position]")
    except Exception as e:
        print(f"❌ Error in setup function: {e}")
        import traceback
        traceback.print_exc()