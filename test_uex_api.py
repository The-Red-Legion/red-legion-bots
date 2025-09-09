#!/usr/bin/env python3
"""
Test script for UEX API integration
Tests the ore price fetching functionality
"""

import asyncio
import aiohttp
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config.settings import UEX_API_CONFIG, ORE_TYPES

async def test_uex_api():
    """Test UEX API integration and price fetching."""
    print("🧪 Testing UEX API Integration...")
    print(f"📡 API URL: {UEX_API_CONFIG['base_url']}")
    print(f"🔑 Bearer Token: {UEX_API_CONFIG['bearer_token'][:20]}...")
    print()
    
    try:
        headers = {
            'Authorization': f'Bearer {UEX_API_CONFIG["bearer_token"]}',
            'Accept': 'application/json'
        }
        
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                UEX_API_CONFIG['base_url'], 
                headers=headers,
                timeout=UEX_API_CONFIG.get('timeout', 30)
            ) as response:
                print(f"🌐 HTTP Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"📊 Total commodities in API: {len(data.get('data', []))}")
                    
                    # Process ore prices using same logic as bot
                    ore_prices = {}
                    processed_count = 0
                    
                    for commodity in data.get('data', []):
                        commodity_name = commodity.get('name', '').upper()
                        
                        # Only process mineral ores we care about
                        if (commodity.get('is_mineral') == 1 and 
                            commodity.get('is_extractable') == 1 and
                            commodity_name in ORE_TYPES):
                            
                            processed_count += 1
                            price = float(commodity.get('price_sell', 0))
                            
                            if price > 0:
                                # Keep highest price for each ore across all locations
                                if commodity_name not in ore_prices or price > ore_prices[commodity_name]['max_price']:
                                    ore_prices[commodity_name] = {
                                        'max_price': price,
                                        'display_name': ORE_TYPES[commodity_name],
                                        'code': commodity.get('code', ''),
                                        'kind': commodity.get('kind', ''),
                                        'location_info': f"{commodity.get('id')} - {commodity.get('name')}"
                                    }
                    
                    print(f"⛏️ Mineral ore entries processed: {processed_count}")
                    print(f"💰 Unique ores with prices: {len(ore_prices)}")
                    print()
                    
                    if ore_prices:
                        print("📋 **Top 10 Highest Value Ores:**")
                        sorted_ores = sorted(
                            ore_prices.items(),
                            key=lambda x: x[1]['max_price'],
                            reverse=True
                        )
                        
                        for i, (ore_key, price_data) in enumerate(sorted_ores[:10], 1):
                            print(f"{i:2}. {price_data['display_name']:15} - {price_data['max_price']:>8,.0f} aUEC/SCU ({price_data['code']})")
                        
                        print()
                        print("📊 **Price Statistics:**")
                        prices = [p['max_price'] for p in ore_prices.values()]
                        print(f"   Highest: {max(prices):>8,.0f} aUEC/SCU")
                        print(f"   Lowest:  {min(prices):>8,.0f} aUEC/SCU") 
                        print(f"   Average: {sum(prices)/len(prices):>8,.0f} aUEC/SCU")
                        
                        print()
                        print("🧮 **Example Payroll Calculation:**")
                        print("   If miners collected:")
                        example_ores = list(sorted_ores[:3])  # Top 3 ores
                        total_value = 0
                        
                        for ore_key, price_data in example_ores:
                            scu_amount = 25  # Example 25 SCU each
                            ore_value = scu_amount * price_data['max_price']
                            total_value += ore_value
                            print(f"   • {scu_amount:2} SCU {price_data['display_name']:15} = {ore_value:>9,.0f} aUEC")
                        
                        print(f"   {'':21}Total Value = {total_value:>9,.0f} aUEC")
                        print(f"   {'':21}Per miner (4) = {total_value/4:>9,.0f} aUEC each")
                        
                    else:
                        print("❌ No matching ore prices found!")
                        print("Available mineral ores in API:")
                        
                        minerals = []
                        for commodity in data.get('data', [])[:50]:  # Show first 50
                            if commodity.get('is_mineral') == 1:
                                minerals.append(f"- {commodity.get('name')} ({commodity.get('code', 'N/A')})")
                        
                        for mineral in minerals[:10]:
                            print(f"   {mineral}")
                        
                        if len(minerals) > 10:
                            print(f"   ... and {len(minerals)-10} more")
                else:
                    print(f"❌ API Error: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"Error details: {error_text[:500]}")
                    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("   RED LEGION UEX API INTEGRATION TEST")
    print("=" * 60)
    asyncio.run(test_uex_api())
    print("=" * 60)
