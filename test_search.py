#!/usr/bin/env python3
"""Demo script showing the road section search functionality."""

import asyncio
import sys
sys.path.insert(0, '/workspaces/Digitraffic-road-conditions/custom_components/digitraffic_road')

from client import DigitraficClient
import aiohttp


async def demo_search():
    """Demonstrate the search functionality."""
    print("=" * 70)
    print("DIGITRAFFIC ROAD CONDITIONS - SEARCH FUNCTIONALITY DEMO")
    print("=" * 70)
    
    async with aiohttp.ClientSession() as session:
        client = DigitraficClient(session)
        
        # Example search queries
        test_queries = [
            "E18",
            "VT4",
            "Perämerentie",
            "Hämeentie",
            "Helsinki",
            "Tampere",
            "v",
            "st",
        ]
        
        for query in test_queries:
            print(f"\n📍 Searching for: '{query}'")
            print("-" * 70)
            
            results = await client.search_road_sections(query)
            
            if results:
                print(f"✓ Found {len(results)} result(s):\n")
                for i, section in enumerate(results, 1):
                    road = section.get("road", "N/A")
                    name = section.get("name", "N/A")
                    location = section.get("location", "N/A")
                    km = section.get("km", "N/A")
                    description = section.get("description", "N/A")
                    section_id = section.get("id", "N/A")
                    
                    print(f"  {i}. {name}")
                    print(f"     Road: {road}")
                    print(f"     Location: {location}")
                    print(f"     KM: {km}")
                    print(f"     Description: {description}")
                    print(f"     ID: {section_id}")
                    print()
            else:
                print("✗ No results found")
        
        print("\n" + "=" * 70)
        print("All available road sections:")
        print("=" * 70)
        
        all_sections = await client.get_road_sections()
        for section in all_sections:
            props = section.get("properties", {})
            print(f"  • {props.get('name')} ({props.get('road')}): {props.get('location')} [{props.get('km')}]")


if __name__ == "__main__":
    asyncio.run(demo_search())
