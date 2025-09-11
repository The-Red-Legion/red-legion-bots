#!/usr/bin/env python3
"""
Quick UEX API test script to see current ore prices
"""

import asyncio
import aiohttp
import json
import sys
import ssl
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config.settings import UEX_API_CONFIG

async def test_uex_api():
    """Test UEX API and show all ore prices"""
    print("🔍 Testing UEX API...")
    print(f"URL: {UEX_API_CONFIG['base_url']}")
    print(f"Token: {UEX_API_CONFIG['bearer_token'][:10]}...")
    print("="*50)
    
    try:
        headers = {
            'Authorization': f"Bearer {UEX_API_CONFIG['bearer_token']}",
            'Content-Type': 'application/json'
        }
        
        # Create SSL context that doesn't verify certificates for testing
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers, connector=connector) as session:
            async with session.get(UEX_API_CONFIG['base_url']) as response:
                print(f"Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse the response
                    if 'data' in data:
                        commodities = data['data']
                    else:
                        commodities = data
                    
                    print(f"Total items in API: {len(commodities)}")
                    print("="*50)
                    
                    # Find all ore-related items
                    ore_items = []
                    for item in commodities:
                        name = item.get('name', '')
                        if any(ore in name.upper() for ore in ['QUANTANIUM', 'QUANTAINIUM', 'RICCITE', 'STILERON', 'AGRICIUM', 'LARANITE', 'BEXALITE']):
                            ore_items.append({
                                'name': name,
                                'code': item.get('code', ''),
                                'price_buy': item.get('price_buy', 0),
                                'price_sell': item.get('price_sell', 0),
                                'is_refined': item.get('is_refined', 0),
                                'is_raw': item.get('is_raw', 0),
                                'is_mineral': item.get('is_mineral', 0)
                            })
                    
                    # Sort by name
                    ore_items.sort(key=lambda x: x['name'])
                    
                    print("🪨 ORE PRICES FROM UEX API:")
                    print("="*50)
                    for item in ore_items:
                        refined_status = "✅ REFINED" if item['is_refined'] else "❌ RAW" if item['is_raw'] else "❓ OTHER"
                        print(f"{item['name']:<20} | Buy: {item['price_buy']:>6} | Sell: {item['price_sell']:>6} | {refined_status}")
                    
                    print("="*50)
                    print("🎯 FILTERED REFINED ORES (what payroll should use):")
                    print("="*50)
                    
                    refined_ores = []
                    for item in ore_items:
                        # Apply same filtering logic as the payroll system
                        name = item['name'].upper()
                        is_refined = item['is_refined'] == 1
                        is_raw = item['is_raw'] == 1
                        
                        if not is_refined or is_raw or '(ORE)' in name or '(RAW)' in name:
                            continue
                            
                        # Check if supported ore
                        supported_ores = ['QUANTAINIUM', 'BEXALITE', 'LARANITE', 'AGRICIUM', 'GOLD', 
                                        'BERYL', 'HEPHAESTANITE', 'BORASE', 'TUNGSTEN', 'TITANIUM', 
                                        'IRON', 'COPPER', 'ALUMINUM', 'SILICON', 'CORUNDUM', 'QUARTZ',
                                        'TARANITE', 'STILERON', 'RICCITE', 'TIN']
                        
                        if name in supported_ores or any(ore in name for ore in supported_ores):
                            if item['price_sell'] > 0:
                                clean_name = name.split('(')[0].strip()
                                refined_ores.append({
                                    'name': clean_name,
                                    'price': item['price_sell']
                                })
                    
                    for ore in sorted(refined_ores, key=lambda x: x['name']):
                        print(f"{ore['name']:<20} | {ore['price']:>6.1f} aUEC per SCU")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ API Error {response.status}: {error_text[:200]}")
                    
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_uex_api())