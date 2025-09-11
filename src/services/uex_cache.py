"""
UEX API Caching Service for Red Legion Discord Bot

Provides cached UEX price data with automatic refresh mechanism to:
- Reduce API calls and improve performance
- Provide fallback data when API is unavailable
- Automatically refresh data at configurable intervals
- Handle API failures gracefully

Usage:
    from services.uex_cache import UEXCache
    
    cache = UEXCache()
    await cache.start_background_refresh()  # Start auto-refresh
    
    prices = await cache.get_ore_prices()  # Get cached or fresh data
"""

import asyncio
import aiohttp
import ssl
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import UEX_API_CONFIG


class UEXCache:
    """
    UEX API caching service with automatic refresh.
    
    Features:
    - In-memory cache with TTL
    - Background refresh task
    - Fallback to cached data on API failures
    - Configurable refresh intervals
    - Multiple data categories support
    """
    
    def __init__(self, 
                 default_ttl: int = 86400,  # 24 hours default TTL (matches UEX API refresh)
                 refresh_interval: int = 86400,  # 24 hours refresh interval
                 max_retries: int = 3):
        self.default_ttl = default_ttl
        self.refresh_interval = refresh_interval
        self.max_retries = max_retries
        
        # Cache storage
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._refresh_task: Optional[asyncio.Task] = None
        self._running = False
        
        print(f"🗄️ UEX Cache initialized (TTL: {default_ttl}s, Refresh: {refresh_interval}s)")
    
    async def start_background_refresh(self):
        """Start the background refresh task."""
        if self._refresh_task and not self._refresh_task.done():
            print("⚠️ Background refresh already running")
            return
        
        self._running = True
        self._refresh_task = asyncio.create_task(self._background_refresh_loop())
        print("🔄 Started UEX cache background refresh")
    
    async def stop_background_refresh(self):
        """Stop the background refresh task."""
        self._running = False
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        print("🛑 Stopped UEX cache background refresh")
    
    async def _background_refresh_loop(self):
        """Background task that refreshes cache data periodically."""
        print("🔄 UEX cache background refresh loop started")
        
        # Initial data fetch
        await self._refresh_all_cache_data()
        
        try:
            while self._running:
                await asyncio.sleep(self.refresh_interval)
                if self._running:  # Check again in case we were stopped
                    await self._refresh_all_cache_data()
        except asyncio.CancelledError:
            print("🔄 UEX cache refresh loop cancelled")
            raise
        except Exception as e:
            print(f"❌ Error in UEX cache refresh loop: {e}")
    
    async def _refresh_all_cache_data(self):
        """Refresh all cached data categories."""
        categories = ["ores", "high_value", "all"]
        
        for category in categories:
            try:
                await self._fetch_and_cache_prices(category)
            except Exception as e:
                print(f"⚠️ Failed to refresh {category} prices: {e}")
    
    async def get_ore_prices(self, category: str = "ores", force_refresh: bool = False) -> Optional[Dict]:
        """
        Get ore prices with caching.
        
        Args:
            category: Price category ("ores", "high_value", "all")
            force_refresh: Force API call even if cached data is valid
            
        Returns:
            Dictionary of ore prices or None if unavailable
        """
        cache_key = f"prices_{category}"
        
        # Check if we have valid cached data
        if not force_refresh and self._is_cache_valid(cache_key):
            print(f"📦 Using cached {category} prices")
            return self._cache[cache_key]["data"]
        
        # Try to fetch fresh data
        try:
            prices = await self._fetch_and_cache_prices(category)
            if prices:
                print(f"🔄 Fetched fresh {category} prices")
                return prices
        except Exception as e:
            print(f"❌ Failed to fetch fresh {category} prices: {e}")
        
        # Fallback to cached data even if expired
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            age = datetime.now() - cached_data["timestamp"]
            print(f"🔄 Using expired cache for {category} (age: {age.total_seconds():.0f}s)")
            return cached_data["data"]
        
        print(f"❌ No {category} price data available")
        return None
    
    async def _fetch_and_cache_prices(self, category: str) -> Optional[Dict]:
        """Fetch prices from UEX API and cache the result."""
        for attempt in range(self.max_retries):
            try:
                prices = await self._fetch_uex_api(category)
                if prices:
                    # Cache the data
                    cache_key = f"prices_{category}"
                    self._cache[cache_key] = {
                        "data": prices,
                        "timestamp": datetime.now(),
                        "ttl": self.default_ttl
                    }
                    print(f"✅ Cached {category} prices ({len(prices)} items)")
                    return prices
            except Exception as e:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"⚠️ UEX API attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait_time)
        
        return None
    
    async def _fetch_uex_api(self, category: str) -> Optional[Dict]:
        """Make actual API call to UEX."""
        try:
            print(f"🔍 Attempting UEX API call for category: {category}")
            print(f"🔍 API URL: {UEX_API_CONFIG['base_url']}")
            
            headers = {
                'Authorization': f'Bearer {UEX_API_CONFIG["bearer_token"]}',
                'Accept': 'application/json'
            }
            
            # SSL context (matching existing implementation)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                print(f"🌐 Making HTTP GET request to UEX API...")
                async with session.get(
                    UEX_API_CONFIG['base_url'], 
                    headers=headers,
                    timeout=UEX_API_CONFIG.get('timeout', 30)
                ) as response:
                    print(f"📡 UEX API response status: {response.status}")
                    
                    if response.status == 200:
                        print(f"✅ UEX API request successful, parsing JSON...")
                        data = await response.json()
                        print(f"🔍 Raw data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        
                        processed = self._process_uex_data(data, category)
                        print(f"✅ Processed {len(processed)} items for category {category}")
                        return processed
                    else:
                        print(f"❌ UEX API returned status {response.status}")
                        response_text = await response.text()
                        print(f"❌ Response body: {response_text[:200]}...")
                        return None
                        
        except asyncio.TimeoutError:
            print("⏰ UEX API request timed out")
            return None
        except aiohttp.ClientError as e:
            print(f"🌐 UEX API connection error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected UEX API error: {e}")
            return None
    
    def _process_uex_data(self, raw_data: Dict, category: str) -> Dict:
        """Process raw UEX API data into usable format."""
        processed = {}
        
        if not raw_data or 'data' not in raw_data:
            return processed
        
        commodities = raw_data['data']
        
        for item in commodities:
            try:
                # Extract commodity info
                name = item.get('name', 'Unknown')
                code = item.get('code', 'UNKNOWN')
                
                # DEBUG: Let's see what the API actually returns
                print(f"🔍 UEX API item structure for {code}: {list(item.keys())}")
                if len(processed) < 2:  # Only log first 2 items to avoid spam
                    print(f"🔍 Full item data for {code}: {item}")
                
                # Get price information directly from item (UEX API v2.0 structure)
                sell_price = item.get('price_sell', 0)
                buy_price = item.get('price_buy', 0)
                
                # Skip items with no sell price
                if sell_price <= 0:
                    continue
                
                # Filter by category
                if self._should_include_item(name, code, category):
                    # Look for actual location data in the API response
                    locations_data = []
                    
                    # Check various possible fields for location data
                    if 'locations' in item:
                        locations_data = item['locations']
                        print(f"🔍 Found 'locations' field for {code}: {locations_data}")
                    elif 'terminals' in item:
                        locations_data = item['terminals'] 
                        print(f"🔍 Found 'terminals' field for {code}: {locations_data}")
                    elif 'trades' in item:
                        locations_data = item['trades']
                        print(f"🔍 Found 'trades' field for {code}: {locations_data}")
                    elif 'prices' in item:
                        locations_data = item['prices']
                        print(f"🔍 Found 'prices' field for {code}: {locations_data}")
                    
                    # Process location data if found, otherwise use fallback
                    if locations_data and isinstance(locations_data, list) and len(locations_data) > 0:
                        processed_locations = []
                        for loc in locations_data:
                            if isinstance(loc, dict):
                                loc_name = loc.get('name', loc.get('location', loc.get('terminal', 'Unknown Location')))
                                loc_sell = loc.get('price_sell', loc.get('sell', sell_price))
                                loc_buy = loc.get('price_buy', loc.get('buy', buy_price))
                                processed_locations.append({
                                    'name': loc_name,
                                    'sell_price': loc_sell,
                                    'buy_price': loc_buy
                                })
                        locations_final = processed_locations if processed_locations else [{'name': 'UEX Best Price', 'sell_price': sell_price, 'buy_price': buy_price}]
                    else:
                        locations_final = [{'name': 'UEX Best Price', 'sell_price': sell_price, 'buy_price': buy_price}]
                    
                    processed[code] = {
                        'name': name,
                        'code': code,
                        'price_sell': sell_price,
                        'price_buy': buy_price,
                        'locations': locations_final,
                        'updated': datetime.now().isoformat()
                    }
                    
            except Exception as e:
                print(f"⚠️ Error processing UEX item {item}: {e}")
                continue
        
        return processed
    
    def _should_include_item(self, name: str, code: str, category: str) -> bool:
        """Determine if an item should be included based on category."""
        from config.settings import ORE_TYPES
        
        if category == "all":
            return True
        elif category == "ores":
            return code in ORE_TYPES
        elif category == "high_value":
            high_value_ores = ["QUANTAINIUM", "BEXALITE", "TARANITE", "GOLD", "BORASE"]
            return code in high_value_ores
        else:
            return True
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self._cache:
            return False
        
        cached_item = self._cache[cache_key]
        age = datetime.now() - cached_item["timestamp"]
        return age.total_seconds() < cached_item["ttl"]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        stats = {
            "running": self._running,
            "cache_entries": len(self._cache),
            "entries": {}
        }
        
        for key, item in self._cache.items():
            age = datetime.now() - item["timestamp"]
            stats["entries"][key] = {
                "age_seconds": age.total_seconds(),
                "valid": self._is_cache_valid(key),
                "item_count": len(item["data"]) if isinstance(item["data"], dict) else 0
            }
        
        return stats
    
    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        print("🗑️ UEX cache cleared")


# Global cache instance
_uex_cache: Optional[UEXCache] = None

def get_uex_cache() -> UEXCache:
    """Get the global UEX cache instance."""
    global _uex_cache
    if _uex_cache is None:
        _uex_cache = UEXCache()
    return _uex_cache

async def initialize_uex_cache():
    """Initialize and start the global UEX cache."""
    cache = get_uex_cache()
    await cache.start_background_refresh()
    return cache

async def shutdown_uex_cache():
    """Shutdown the global UEX cache."""
    global _uex_cache
    if _uex_cache:
        await _uex_cache.stop_background_refresh()
        _uex_cache = None