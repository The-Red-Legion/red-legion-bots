#!/usr/bin/env python3
"""
Test UEX API connectivity and response.
"""

import asyncio
import aiohttp

async def test_uex_api():
    """Test the UEX API endpoint."""
    
    config = {
        'base_url': 'https://uexcorp.space/api/2.0/commodities',
        'bearer_token': '4ae9c984f69da2ad759776529b37a3dabdf99db4',
        'timeout': 30
    }
    
    headers = {
        'Authorization': f'Bearer {config["bearer_token"]}',
        'Accept': 'application/json'
    }
    
    print("🧪 Testing UEX API connection...")
    print(f"URL: {config['base_url']}")
    print(f"Token: {config['bearer_token'][:20]}...")
    
    try:
        timeout = aiohttp.ClientTimeout(total=config['timeout'])
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(config['base_url'], headers=headers) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ API call successful!")
                    print(f"Data keys: {list(data.keys()) if data else 'No data'}")
                    
                    if 'data' in data:
                        commodities = data['data']
                        print(f"Found {len(commodities)} commodities")
                        
                        # Look for ore types
                        ore_types = ['QUANTANIUM', 'LARANITE', 'BEXALITE', 'TARANITE', 'BORASE', 'HADANITE']
                        found_ores = []
                        
                        for commodity in commodities[:10]:  # Show first 10
                            name = commodity.get('name', '').upper()
                            if name in ore_types:
                                found_ores.append(name)
                                print(f"  Found ore: {name} - Max: {commodity.get('price_max', 0)} aUEC")
                        
                        print(f"Found {len(found_ores)} ore types from our list")
                    
                else:
                    text = await response.text()
                    print(f"❌ API call failed with status {response.status}")
                    print(f"Response: {text[:500]}")
                    
    except Exception as e:
        print(f"❌ Error testing UEX API: {e}")

if __name__ == "__main__":
    asyncio.run(test_uex_api())
