"""
Red Legion Market/Trading System
Implements /red-market subcommand group for marketplace functionality
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timezone, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class RedMarketGroup(app_commands.Group):
    """Red Legion Market command group"""
    
    def __init__(self):
        super().__init__(name='redmarket', description='Organization marketplace and trading system')
    
    @app_commands.command(name='list', description='Browse marketplace listings')
    @app_commands.describe(
        category='Filter by item category',
        search='Search for specific items',
        sort_by='Sort listings by'
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name='All Categories', value='all'),
            app_commands.Choice(name='🚀 Ships & Vehicles', value='ships'),
            app_commands.Choice(name='⚙️ Ship Components', value='components'),
            app_commands.Choice(name='⚔️ Weapons & Equipment', value='weapons'),
            app_commands.Choice(name='📦 Cargo & Resources', value='cargo'),
            app_commands.Choice(name='🛠️ Services', value='services'),
            app_commands.Choice(name='🍃 Consumables', value='consumables'),
            app_commands.Choice(name='📋 Miscellaneous', value='misc')
        ],
        sort_by=[
            app_commands.Choice(name='Newest First', value='newest'),
            app_commands.Choice(name='Price: Low to High', value='price_asc'),
            app_commands.Choice(name='Price: High to Low', value='price_desc'),
            app_commands.Choice(name='Most Popular', value='popular')
        ]
    )
    async def list_market(self, interaction: discord.Interaction, category: app_commands.Choice[str] = None, search: str = None, sort_by: app_commands.Choice[str] = None):
        """Browse marketplace listings"""
        try:
            from ..database.database import Database
            
            db = Database()
            
            # Set defaults
            filter_category = category.value if category and category.value != 'all' else None
            sort_order = sort_by.value if sort_by else 'newest'
            
            # Get listings
            listings = await db.get_market_listings(
                str(interaction.guild_id),
                category=filter_category,
                search_term=search,
                sort_by=sort_order,
                limit=10
            )
            
            if not listings:
                embed = discord.Embed(
                    title="🏪 Marketplace",
                    description="No listings found matching your criteria.",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Add a Listing", value="Use `/redmarket add` to create a new listing", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create marketplace embed
            embed = discord.Embed(
                title="🏪 Red Legion Marketplace",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Add filter info
            filters = []
            if filter_category:
                category_names = {
                    'ships': '🚀 Ships & Vehicles',
                    'components': '⚙️ Ship Components',
                    'weapons': '⚔️ Weapons & Equipment',
                    'cargo': '📦 Cargo & Resources',
                    'services': '🛠️ Services',
                    'consumables': '🍃 Consumables',
                    'misc': '📋 Miscellaneous'
                }
                filters.append(f"Category: {category_names.get(filter_category, filter_category)}")
            
            if search:
                filters.append(f"Search: {search}")
            
            sort_names = {
                'newest': 'Newest First',
                'price_asc': 'Price: Low to High',
                'price_desc': 'Price: High to Low',
                'popular': 'Most Popular'
            }
            filters.append(f"Sort: {sort_names.get(sort_order, sort_order)}")
            
            if filters:
                embed.description = f"**Filters:** {' | '.join(filters)}"
            
            # Add listings
            for listing in listings:
                # Format price
                price_text = f"{listing['price_uec']:,} UEC"
                if listing.get('delivery_available') and listing.get('delivery_cost_uec', 0) > 0:
                    price_text += f" (+{listing['delivery_cost_uec']:,} delivery)"
                
                # Format location
                location_parts = []
                if listing.get('location_system'):
                    location_parts.append(listing['location_system'])
                if listing.get('location_planet'):
                    location_parts.append(listing['location_planet'])
                if listing.get('location_station'):
                    location_parts.append(listing['location_station'])
                location = " > ".join(location_parts) if location_parts else "Location not specified"
                
                # Create field value
                value = f"**Price:** {price_text}\n"
                value += f"**Quantity:** {listing['quantity'] - listing['quantity_sold']}\n"
                value += f"**Seller:** {listing['seller_name']}\n"
                value += f"**Location:** {location}"
                
                if listing.get('item_condition') and listing['item_condition'] != 'new':
                    value += f"\n**Condition:** {listing['item_condition'].title()}"
                
                # Add featured emoji
                title = listing['item_name']
                if listing.get('featured'):
                    title = f"⭐ {title}"
                
                embed.add_field(
                    name=title,
                    value=value,
                    inline=True
                )
            
            if len(listings) == 10:
                embed.set_footer(text="Showing first 10 results • Use more specific filters to narrow down")
            else:
                embed.set_footer(text=f"Found {len(listings)} listings")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in market list: {e}")
            await interaction.response.send_message(
                "❌ Error retrieving marketplace listings.",
                ephemeral=True
            )
    
    @app_commands.command(name='add', description='Create a new marketplace listing')
    @app_commands.describe(
        item_name='Name of the item',
        price='Price in UEC',
        category='Item category',
        quantity='Quantity available (default: 1)',
        description='Item description (optional)',
        condition='Item condition',
        location_system='System location',
        location_planet='Planet/Moon location (optional)',
        location_station='Station/Outpost location (optional)',
        delivery_available='Offer delivery service'
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name='🚀 Ships & Vehicles', value='ships'),
            app_commands.Choice(name='⚙️ Ship Components', value='components'),
            app_commands.Choice(name='⚔️ Weapons & Equipment', value='weapons'),
            app_commands.Choice(name='📦 Cargo & Resources', value='cargo'),
            app_commands.Choice(name='🛠️ Services', value='services'),
            app_commands.Choice(name='🍃 Consumables', value='consumables'),
            app_commands.Choice(name='📋 Miscellaneous', value='misc')
        ],
        condition=[
            app_commands.Choice(name='New', value='new'),
            app_commands.Choice(name='Used', value='used'),
            app_commands.Choice(name='Refurbished', value='refurbished'),
            app_commands.Choice(name='Damaged', value='damaged')
        ]
    )
    async def add_listing(self, interaction: discord.Interaction, item_name: str, price: int, category: app_commands.Choice[str], 
                         quantity: int = 1, description: str = None, condition: app_commands.Choice[str] = None,
                         location_system: str = None, location_planet: str = None, location_station: str = None,
                         delivery_available: bool = False):
        """Create a new marketplace listing"""
        try:
            from ..database.database import Database
            
            db = Database()
            
            # Validate inputs
            if price <= 0:
                await interaction.response.send_message("❌ Price must be greater than 0.", ephemeral=True)
                return
            
            if quantity <= 0:
                await interaction.response.send_message("❌ Quantity must be greater than 0.", ephemeral=True)
                return
            
            # Check user's listing limits
            settings = await db.get_market_settings(str(interaction.guild_id))
            max_listings = settings.get('max_listings_per_user', 10) if settings else 10
            
            user_listings = await db.get_user_active_listings_count(str(interaction.guild_id), str(interaction.user.id))
            if user_listings >= max_listings:
                await interaction.response.send_message(
                    f"❌ You've reached the maximum number of active listings ({max_listings}). "
                    f"Remove some existing listings before adding new ones.",
                    ephemeral=True
                )
                return
            
            # Check price limits
            min_price = settings.get('min_price_uec', 1) if settings else 1
            max_price = settings.get('max_price_uec', 10000000) if settings else 10000000
            
            if price < min_price or price > max_price:
                await interaction.response.send_message(
                    f"❌ Price must be between {min_price:,} and {max_price:,} UEC.",
                    ephemeral=True
                )
                return
            
            # Create listing data
            listing_data = {
                'guild_id': str(interaction.guild_id),
                'seller_id': str(interaction.user.id),
                'seller_name': interaction.user.display_name,
                'item_name': item_name,
                'item_description': description,
                'item_category': category.value,
                'item_condition': condition.value if condition else 'new',
                'price_uec': price,
                'quantity': quantity,
                'location_system': location_system,
                'location_planet': location_planet,
                'location_station': location_station,
                'delivery_available': delivery_available,
                'status': 'active'
            }
            
            # Create the listing
            listing_id = await db.create_market_listing(listing_data)
            
            # Create success embed
            embed = discord.Embed(
                title="✅ Listing Created Successfully!",
                description=f"Your item has been added to the marketplace.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="Listing ID", value=f"`{listing_id}`", inline=True)
            embed.add_field(name="Item", value=item_name, inline=True)
            embed.add_field(name="Price", value=f"{price:,} UEC", inline=True)
            
            embed.add_field(name="Category", value=category.name, inline=True)
            embed.add_field(name="Quantity", value=str(quantity), inline=True)
            embed.add_field(name="Condition", value=(condition.name if condition else 'New'), inline=True)
            
            if location_system:
                location = location_system
                if location_planet:
                    location += f" > {location_planet}"
                if location_station:
                    location += f" > {location_station}"
                embed.add_field(name="Location", value=location, inline=False)
            
            if delivery_available:
                embed.add_field(name="Delivery", value="✅ Available", inline=True)
            
            embed.add_field(
                name="Visibility",
                value="Your listing is now visible in `/red-market list`",
                inline=False
            )
            
            embed.set_footer(text="Red Legion Marketplace")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Post to market channel if configured
            await self._post_to_market_channel(interaction, listing_data, listing_id)
            
        except Exception as e:
            logger.error(f"Error creating listing: {e}")
            await interaction.response.send_message(
                "❌ Error creating marketplace listing. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name='remove', description='Remove one of your marketplace listings')
    @app_commands.describe(listing_id='The ID of the listing to remove')
    async def remove_listing(self, interaction: discord.Interaction, listing_id: int):
        """Remove a marketplace listing"""
        try:
            from ..database.database import Database
            
            db = Database()
            
            # Get listing details
            listing = await db.get_market_listing_by_id(listing_id)
            if not listing or listing['guild_id'] != str(interaction.guild_id):
                await interaction.response.send_message("❌ Listing not found.", ephemeral=True)
                return
            
            # Check ownership (unless user is admin/moderator)
            is_owner = listing['seller_id'] == str(interaction.user.id)
            is_moderator = any(role.name.lower() in ['admin', 'moderator', 'market moderator'] for role in interaction.user.roles)
            
            if not (is_owner or is_moderator):
                await interaction.response.send_message("❌ You can only remove your own listings.", ephemeral=True)
                return
            
            if listing['status'] != 'active':
                await interaction.response.send_message(f"❌ Listing is already {listing['status']}.", ephemeral=True)
                return
            
            # Remove the listing
            await db.remove_market_listing(listing_id, str(interaction.user.id), interaction.user.display_name)
            
            embed = discord.Embed(
                title="✅ Listing Removed",
                description=f"Marketplace listing has been removed.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="Item", value=listing['item_name'], inline=True)
            embed.add_field(name="Price", value=f"{listing['price_uec']:,} UEC", inline=True)
            embed.add_field(name="Removed By", value=interaction.user.display_name, inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error removing listing: {e}")
            await interaction.response.send_message(
                "❌ Error removing listing.",
                ephemeral=True
            )
    
    @app_commands.command(name='search', description='Search marketplace listings')
    @app_commands.describe(
        query='Search term',
        category='Filter by category',
        max_price='Maximum price filter',
        location='Location filter'
    )
    @app_commands.choices(category=[
        app_commands.Choice(name='All Categories', value='all'),
        app_commands.Choice(name='🚀 Ships & Vehicles', value='ships'),
        app_commands.Choice(name='⚙️ Ship Components', value='components'),
        app_commands.Choice(name='⚔️ Weapons & Equipment', value='weapons'),
        app_commands.Choice(name='📦 Cargo & Resources', value='cargo'),
        app_commands.Choice(name='🛠️ Services', value='services'),
        app_commands.Choice(name='🍃 Consumables', value='consumables'),
        app_commands.Choice(name='📋 Miscellaneous', value='misc')
    ])
    async def search_market(self, interaction: discord.Interaction, query: str, category: app_commands.Choice[str] = None, 
                           max_price: int = None, location: str = None):
        """Search marketplace listings with advanced filters"""
        try:
            from ..database.database import Database
            
            db = Database()
            
            filter_category = category.value if category and category.value != 'all' else None
            
            # Get search results
            listings = await db.search_market_listings(
                str(interaction.guild_id),
                search_term=query,
                category=filter_category,
                max_price=max_price,
                location=location,
                limit=10
            )
            
            if not listings:
                embed = discord.Embed(
                    title="🔍 Search Results",
                    description=f"No listings found for '{query}'.",
                    color=discord.Color.orange()
                )
                embed.add_field(name="Try:", value="• Different search terms\n• Broader categories\n• Remove price filters", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create search results embed
            embed = discord.Embed(
                title="🔍 Search Results",
                description=f"Found {len(listings)} listings for '{query}'",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Add filter info
            filters = [f"Query: {query}"]
            if filter_category:
                filters.append(f"Category: {category.name}")
            if max_price:
                filters.append(f"Max Price: {max_price:,} UEC")
            if location:
                filters.append(f"Location: {location}")
            
            embed.add_field(name="Search Filters", value=" | ".join(filters), inline=False)
            
            # Add listings
            for listing in listings:
                # Format price with delivery
                price_text = f"{listing['price_uec']:,} UEC"
                if listing.get('delivery_available') and listing.get('delivery_cost_uec', 0) > 0:
                    price_text += f" (+{listing['delivery_cost_uec']:,} delivery)"
                
                # Format location
                location_parts = []
                if listing.get('location_system'):
                    location_parts.append(listing['location_system'])
                if listing.get('location_planet'):
                    location_parts.append(listing['location_planet'])
                listing_location = " > ".join(location_parts) if location_parts else "Not specified"
                
                value = f"**Price:** {price_text}\n"
                value += f"**Seller:** {listing['seller_name']}\n"
                value += f"**Location:** {listing_location}\n"
                value += f"**Qty:** {listing['quantity'] - listing['quantity_sold']}"
                
                title = listing['item_name']
                if listing.get('featured'):
                    title = f"⭐ {title}"
                
                embed.add_field(
                    name=title,
                    value=value,
                    inline=True
                )
            
            embed.set_footer(text="Red Legion Marketplace • Use /red-market list for browsing")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in market search: {e}")
            await interaction.response.send_message(
                "❌ Error searching marketplace.",
                ephemeral=True
            )
    
    @app_commands.command(name='update', description='Update one of your marketplace listings')
    @app_commands.describe(
        listing_id='The ID of the listing to update',
        new_price='New price in UEC (optional)',
        new_quantity='New quantity (optional)',
        new_description='New description (optional)'
    )
    async def update_listing(self, interaction: discord.Interaction, listing_id: int, new_price: int = None, 
                            new_quantity: int = None, new_description: str = None):
        """Update an existing marketplace listing"""
        try:
            from ..database.database import Database
            
            db = Database()
            
            # Get listing details
            listing = await db.get_market_listing_by_id(listing_id)
            if not listing or listing['guild_id'] != str(interaction.guild_id):
                await interaction.response.send_message("❌ Listing not found.", ephemeral=True)
                return
            
            # Check ownership
            if listing['seller_id'] != str(interaction.user.id):
                await interaction.response.send_message("❌ You can only update your own listings.", ephemeral=True)
                return
            
            if listing['status'] != 'active':
                await interaction.response.send_message(f"❌ Cannot update {listing['status']} listing.", ephemeral=True)
                return
            
            # Validate new values
            if new_price is not None and new_price <= 0:
                await interaction.response.send_message("❌ Price must be greater than 0.", ephemeral=True)
                return
            
            if new_quantity is not None and new_quantity <= 0:
                await interaction.response.send_message("❌ Quantity must be greater than 0.", ephemeral=True)
                return
            
            # Check if anything is actually changing
            if new_price is None and new_quantity is None and new_description is None:
                await interaction.response.send_message("❌ Please specify at least one field to update.", ephemeral=True)
                return
            
            # Update the listing
            update_data = {}
            if new_price is not None:
                update_data['price_uec'] = new_price
            if new_quantity is not None:
                update_data['quantity'] = new_quantity
            if new_description is not None:
                update_data['item_description'] = new_description
            
            await db.update_market_listing(listing_id, update_data)
            
            # Create update confirmation
            embed = discord.Embed(
                title="✅ Listing Updated",
                description=f"Your marketplace listing has been updated.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="Item", value=listing['item_name'], inline=True)
            embed.add_field(name="Listing ID", value=f"`{listing_id}`", inline=True)
            embed.add_field(name="Status", value="Active", inline=True)
            
            # Show what changed
            changes = []
            if new_price is not None:
                changes.append(f"Price: {listing['price_uec']:,} → {new_price:,} UEC")
            if new_quantity is not None:
                changes.append(f"Quantity: {listing['quantity']} → {new_quantity}")
            if new_description is not None:
                changes.append(f"Description: Updated")
            
            if changes:
                embed.add_field(name="Changes Made", value="\n".join(changes), inline=False)
            
            embed.set_footer(text="Red Legion Marketplace")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error updating listing: {e}")
            await interaction.response.send_message(
                "❌ Error updating listing.",
                ephemeral=True
            )
    
    @app_commands.command(name='stats', description='View marketplace statistics')
    async def market_stats(self, interaction: discord.Interaction):
        """View marketplace statistics"""
        try:
            from ..database.database import Database
            
            db = Database()
            
            # Get market statistics
            stats = await db.get_market_statistics(str(interaction.guild_id))
            
            if not stats:
                embed = discord.Embed(
                    title="📊 Marketplace Statistics",
                    description="No marketplace data available yet.",
                    color=discord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create statistics embed
            embed = discord.Embed(
                title="📊 Marketplace Statistics",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Current listings
            embed.add_field(
                name="📈 Current Listings",
                value=f"**Active:** {stats.get('total_active_listings', 0):,}\n"
                      f"**Sellers:** {stats.get('unique_sellers', 0):,}\n"
                      f"**Featured:** {stats.get('featured_listings', 0):,}",
                inline=True
            )
            
            # Recent activity
            embed.add_field(
                name="🕒 Recent Activity",
                value=f"**Last 7 days:** {stats.get('listings_last_7_days', 0):,}\n"
                      f"**Last 30 days:** {stats.get('listings_last_30_days', 0):,}\n"
                      f"**Expiring soon:** {stats.get('expiring_soon', 0):,}",
                inline=True
            )
            
            # Price statistics
            if stats.get('average_price'):
                embed.add_field(
                    name="💰 Price Range",
                    value=f"**Average:** {float(stats['average_price']):,.0f} UEC\n"
                          f"**Minimum:** {float(stats.get('min_price', 0)):,.0f} UEC\n"
                          f"**Maximum:** {float(stats.get('max_price', 0)):,.0f} UEC",
                    inline=True
                )
            
            # Inventory
            if stats.get('total_items_available'):
                embed.add_field(
                    name="📦 Inventory",
                    value=f"**Total Items:** {stats['total_items_available']:,}\n"
                          f"**Categories:** Multiple\n"
                          f"**Locations:** Various",
                    inline=True
                )
            
            embed.set_footer(text="Red Legion Marketplace • Statistics updated in real-time")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error getting market stats: {e}")
            await interaction.response.send_message(
                "❌ Error retrieving marketplace statistics.",
                ephemeral=True
            )
    
    async def _post_to_market_channel(self, interaction: discord.Interaction, listing_data: dict, listing_id: int):
        """Post new listing to market channel if configured"""
        try:
            from ..database.database import Database
            
            db = Database()
            settings = await db.get_market_settings(str(interaction.guild_id))
            
            if not settings or not settings.get('market_channel_id'):
                return
            
            channel = interaction.guild.get_channel(int(settings['market_channel_id']))
            if not channel:
                return
            
            # Create market channel embed
            embed = discord.Embed(
                title="🆕 New Marketplace Listing",
                description=f"**{listing_data['item_name']}**",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="Price", value=f"{listing_data['price_uec']:,} UEC", inline=True)
            embed.add_field(name="Quantity", value=str(listing_data['quantity']), inline=True)
            embed.add_field(name="Seller", value=listing_data['seller_name'], inline=True)
            
            category_names = {
                'ships': '🚀 Ships & Vehicles',
                'components': '⚙️ Ship Components',
                'weapons': '⚔️ Weapons & Equipment',
                'cargo': '📦 Cargo & Resources',
                'services': '🛠️ Services',
                'consumables': '🍃 Consumables',
                'misc': '📋 Miscellaneous'
            }
            
            embed.add_field(
                name="Category", 
                value=category_names.get(listing_data['item_category'], listing_data['item_category']), 
                inline=True
            )
            
            if listing_data.get('item_condition') and listing_data['item_condition'] != 'new':
                embed.add_field(name="Condition", value=listing_data['item_condition'].title(), inline=True)
            
            if listing_data.get('delivery_available'):
                embed.add_field(name="Delivery", value="✅ Available", inline=True)
            
            if listing_data.get('item_description'):
                embed.add_field(name="Description", value=listing_data['item_description'][:100] + "..." if len(listing_data['item_description']) > 100 else listing_data['item_description'], inline=False)
            
            embed.add_field(
                name="Browse Marketplace",
                value="Use `/redmarket list` to see all listings",
                inline=False
            )
            
            embed.set_footer(text=f"Listing ID: {listing_id}")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error posting to market channel: {e}")

class MarketManagement(commands.Cog):
    """Market Management Cog using Discord subcommand groups."""
    
    def __init__(self, bot):
        self.bot = bot
    
    # Properly register the command group
    redmarket = RedMarketGroup()


async def setup(bot):
    """Setup function for discord.py extension loading."""
    print("🔧 Setting up Market Management with subcommand groups...")
    try:
        cog = MarketManagement(bot)
        await bot.add_cog(cog)
        print("✅ Market Management cog loaded with subcommand groups")
        print("✅ Available commands:")
        print("   • /redmarket list [category] [sort]")
        print("   • /redmarket add <item> <price> [details]")
    except Exception as e:
        print(f"❌ Error in setup function: {e}")
        import traceback
        traceback.print_exc()