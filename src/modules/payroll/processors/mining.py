"""
Mining Payroll Processor

Handles ore collection data and converts to aUEC values using UEX Corp pricing.
Integrates with the UEX API for real-time pricing data.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
from decimal import Decimal
import aiohttp
import asyncio
import logging
import ssl

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config.settings import UEX_API_CONFIG, ORE_TYPES, get_database_url
from database.connection import get_cursor

logger = logging.getLogger(__name__)

class MiningProcessor:
    """
    Processes mining ore collections and converts to aUEC values.
    
    Features:
    - UEX Corp API integration for real-time ore prices
    - Price caching and fallback mechanisms
    - SCU volume calculations
    - Support for all 19+ mineable ores
    """
    
    def __init__(self):
        self.db_url = get_database_url()
    
    def get_collection_description(self) -> str:
        """Get description text for collection input UI."""
        return "ore collections (SCU amounts for each ore type)"
    
    async def get_current_prices(self, refresh: bool = False, allow_api_calls: bool = False) -> Dict[str, Dict]:
        """
        Get current ore prices from database cache or UEX Corp API.
        
        Args:
            refresh: Force refresh from API instead of using cache
            allow_api_calls: Allow API calls (set to False during Discord interactions)
            
        Returns:
            Dict mapping ore names to price data: {ore_name: {price, location, system}}
        """
        try:
            # Always check cache first
            cached_prices = await self._get_cached_prices()
            if cached_prices and not refresh:
                logger.info("Using cached ore prices")
                return cached_prices
            
            # Only make API calls if explicitly allowed (not during Discord interactions)
            if allow_api_calls and refresh:
                logger.info("Fetching ore prices from UEX Corp API")
                api_prices = await self._fetch_from_uex_api()
                
                if api_prices:
                    # Update cache
                    await self._update_price_cache(api_prices)
                    return api_prices
            
            # Use cached prices if available
            if cached_prices:
                logger.info("Using cached ore prices (API calls not allowed or failed)")
                return cached_prices
            else:
                logger.warning("No ore prices available in cache")
                # Return default prices to avoid blocking the UI
                return self._get_default_prices()
                    
        except Exception as e:
            logger.error(f"Error getting ore prices: {e}")
            # Return default prices to avoid blocking the UI
            return self._get_default_prices()
    
    async def calculate_total_value(
        self, 
        ore_collections: Dict[str, float], 
        prices: Dict[str, Dict]
    ) -> Tuple[Decimal, Dict]:
        """
        Calculate total aUEC value of ore collections.
        
        Args:
            ore_collections: {ore_name: scu_amount}
            prices: Price data from get_current_prices()
            
        Returns:
            Tuple of (total_value_auec, calculation_breakdown)
        """
        try:
            total_value = Decimal('0')
            breakdown = {}
            
            for ore_name, scu_amount in ore_collections.items():
                if scu_amount <= 0:
                    continue
                    
                # Get price data for this ore
                price_info = prices.get(ore_name.upper())
                if not price_info:
                    logger.warning(f"No price data found for ore: {ore_name}")
                    continue
                
                # Calculate value
                price_per_scu = Decimal(str(price_info['price']))
                scu_decimal = Decimal(str(scu_amount))
                ore_value = price_per_scu * scu_decimal
                
                total_value += ore_value
                
                breakdown[ore_name] = {
                    'scu_amount': float(scu_decimal),
                    'price_per_scu': float(price_per_scu),
                    'total_value': float(ore_value),
                    'best_location': price_info.get('location', 'Unknown'),
                    'system': price_info.get('system', 'Stanton')
                }
            
            return total_value, breakdown
            
        except Exception as e:
            logger.error(f"Error calculating ore value: {e}")
            return Decimal('0'), {}
    
    async def _get_cached_prices(self) -> Dict[str, Dict]:
        """Get cached ore prices from database."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT item_name, buy_price_per_scu, best_sell_location, system_location
                    FROM uex_prices 
                    WHERE item_category = 'ore' 
                    AND is_current = TRUE
                    AND fetched_at > NOW() - INTERVAL '12 hours'
                """)
                
                prices = {}
                for row in cursor.fetchall():
                    prices[row['item_name'].upper()] = {
                        'price': float(row['buy_price_per_scu']),
                        'location': row['best_sell_location'],
                        'system': row['system_location']
                    }
                
                return prices if prices else None
                
        except Exception as e:
            logger.error(f"Error getting cached prices: {e}")
            return None
    
    async def _fetch_from_uex_api(self) -> Dict[str, Dict]:
        """Fetch current ore prices from UEX Corp API."""
        try:
            url = UEX_API_CONFIG['base_url']
            headers = {
                'Authorization': f"Bearer {UEX_API_CONFIG['bearer_token']}",
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Fetching UEX data from: {url}")
            logger.info(f"Using bearer token: {UEX_API_CONFIG['bearer_token'][:10]}...")
            
            # Create SSL context to handle certificate issues
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            timeout = aiohttp.ClientTimeout(total=UEX_API_CONFIG['timeout'])
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers, connector=connector) as session:
                async with session.get(url) as response:
                    logger.info(f"UEX API response status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"UEX API returned {len(data) if isinstance(data, (list, dict)) else 'unknown'} items")
                        parsed_data = self._parse_uex_response(data)
                        logger.info(f"Parsed {len(parsed_data)} ore prices from UEX API")
                        return parsed_data
                    else:
                        response_text = await response.text()
                        logger.error(f"UEX API returned status {response.status}: {response_text[:200]}")
                        return {}
                        
        except asyncio.TimeoutError:
            logger.error("UEX API request timed out")
            return {}
        except Exception as e:
            logger.error(f"Error fetching from UEX API: {e}")
            return {}
    
    def _parse_uex_response(self, data: Dict) -> Dict[str, Dict]:
        """Parse UEX Corp API response into our price format."""
        try:
            prices = {}
            
            # Parse UEX data structure - based on actual API response
            if 'data' in data:
                commodities = data['data']
            else:
                commodities = data
                
            for item in commodities:
                # Extract ore information
                name = item.get('name', '').upper()
                
                # Only process refined ores (skip raw ores and non-refined items)
                is_refined = item.get('is_refined', 0) == 1
                is_raw = item.get('is_raw', 0) == 1
                
                if not is_refined or is_raw or '(ORE)' in name or '(RAW)' in name:
                    continue
                    
                # Check if this is a mineable ore we support
                is_supported_ore = (
                    name in ORE_TYPES.values() or
                    any(ore_name.upper() in name for ore_name in ORE_TYPES.values()) or
                    name in ['QUANTAINIUM', 'BEXALITE', 'LARANITE', 'AGRICIUM', 'GOLD', 
                            'BERYL', 'HEPHAESTANITE', 'BORASE', 'TUNGSTEN', 'TITANIUM', 
                            'IRON', 'COPPER', 'ALUMINUM', 'SILICON', 'CORUNDUM', 'QUARTZ',
                            'TARANITE', 'STILERON', 'RICCITE', 'TIN']
                )
                
                if not is_supported_ore:
                    continue
                
                # Get sell price from the UEX data structure
                sell_price = item.get('price_sell', 0)
                
                # Only include items with valid sell prices
                if sell_price > 0:
                    # Clean up ore name (remove parenthetical descriptions)
                    clean_name = name.split('(')[0].strip()
                    
                    prices[clean_name] = {
                        'price': float(sell_price),
                        'location': 'Best Available',  # UEX gives us the best sell price
                        'system': 'Stanton'
                    }
            
            logger.info(f"Parsed {len(prices)} ore prices from UEX API")
            return prices
            
        except Exception as e:
            logger.error(f"Error parsing UEX API response: {e}")
            return {}
    
    async def _update_price_cache(self, prices: Dict[str, Dict]):
        """Update cached ore prices in database."""
        try:
            with get_cursor() as cursor:
                # Mark old prices as not current
                cursor.execute("""
                    UPDATE uex_prices 
                    SET is_current = FALSE 
                    WHERE item_category = 'ore'
                """)
                
                # Insert new prices
                for ore_name, price_data in prices.items():
                    cursor.execute("""
                        INSERT INTO uex_prices (
                            item_name, buy_price_per_scu, best_sell_location,
                            system_location, item_category, fetched_at, is_current
                        ) VALUES (
                            %s, %s, %s, %s, 'ore', %s, TRUE
                        ) ON CONFLICT (item_name, item_category)
                        WHERE is_current = TRUE
                        DO UPDATE SET
                            buy_price_per_scu = EXCLUDED.buy_price_per_scu,
                            best_sell_location = EXCLUDED.best_sell_location,
                            system_location = EXCLUDED.system_location,
                            fetched_at = EXCLUDED.fetched_at
                    """, (
                        ore_name,
                        price_data['price'],
                        price_data['location'],
                        price_data['system'],
                        self._get_current_timestamp()
                    ))
                
                logger.info(f"Updated price cache with {len(prices)} ore prices")
                
        except Exception as e:
            logger.error(f"Error updating price cache: {e}")
    
    def _get_current_timestamp(self):
        """Get current timestamp for database storage."""
        from datetime import datetime
        return datetime.now()
    
    def get_supported_ores(self) -> List[str]:
        """Get list of supported ore types."""
        return list(ORE_TYPES.values())
    
    def _get_default_prices(self) -> Dict[str, Dict]:
        """Get default fallback prices when no data is available."""
        # These are conservative estimates to prevent the UI from breaking
        # when no price data is available (alphabetical order)
        default_prices = {
            'AGRICIUM': {'price': 24.8, 'location': 'Area18', 'system': 'Stanton'},
            'ALUMINUM': {'price': 1.2, 'location': 'Area18', 'system': 'Stanton'},
            'BERYL': {'price': 2.8, 'location': 'Area18', 'system': 'Stanton'},
            'BEXALITE': {'price': 4.2, 'location': 'Area18', 'system': 'Stanton'},
            'BORASE': {'price': 2.3, 'location': 'Area18', 'system': 'Stanton'},
            'COPPER': {'price': 1.5, 'location': 'Area18', 'system': 'Stanton'},
            'CORUNDUM': {'price': 1.8, 'location': 'Area18', 'system': 'Stanton'},
            'GOLD': {'price': 6.1, 'location': 'Area18', 'system': 'Stanton'},
            'HEPHAESTANITE': {'price': 2.5, 'location': 'Area18', 'system': 'Stanton'},
            'IRON': {'price': 1.8, 'location': 'Area18', 'system': 'Stanton'},
            'LARANITE': {'price': 28.0, 'location': 'Area18', 'system': 'Stanton'},
            'QUANTAINIUM': {'price': 8.5, 'location': 'Area18', 'system': 'Stanton'},
            'QUARTZ': {'price': 1.3, 'location': 'Area18', 'system': 'Stanton'},
            'RICCITE': {'price': 45.0, 'location': 'Pyro-System', 'system': 'Pyro'},
            'SILICON': {'price': 1.5, 'location': 'Area18', 'system': 'Stanton'},
            'STILERON': {'price': 42.0, 'location': 'Pyro-System', 'system': 'Pyro'},
            'TITANIUM': {'price': 8.0, 'location': 'Area18', 'system': 'Stanton'},
            'TUNGSTEN': {'price': 4.5, 'location': 'Area18', 'system': 'Stanton'},
        }
        
        logger.info("Using default fallback ore prices")
        return default_prices