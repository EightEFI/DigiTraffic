#!/usr/bin/env python3
"""Test script for the section ID resolver."""

import asyncio
import aiohttp
import json
import sys

# Add custom_components to path
sys.path.insert(0, '/workspaces/Digitraffic-road-conditions')

from custom_components.digitraffic_road.client import DigitraficRoadClient

async def test_resolver():
    """Test the resolver with known section titles."""
    
    async with aiohttp.ClientSession() as session:
        client = DigitraficRoadClient(session)
        
        # Test cases
        test_cases = [
            "Tie 3: Valtatie 3 3.250",  # User's reported case
            "Valtatie 3 3.250",  # Without "Tie 3:" prefix
            "Valtatie 1 100",  # Another highway
            "Tie 4",  # Short form
        ]
        
        print("Testing resolver with known section titles:\n")
        
        for title in test_cases:
            print(f"Testing: '{title}'")
            resolved = await client.resolve_section_id(title)
            if resolved:
                print(f"  ✓ Resolved to: {resolved}")
                
                # Try to fetch real data with the resolved ID
                try:
                    conditions = await client.get_road_conditions(resolved, "fi")
                    if conditions:
                        obs = conditions.get("observation", {})
                        obs_time = obs.get("time", "N/A")
                        obs_condition = obs.get("condition", "N/A")
                        forecast_count = len(conditions.get("forecasts", []))
                        print(f"  Data: observation at {obs_time} = {obs_condition}, {forecast_count} forecasts")
                except Exception as e:
                    print(f"  Error fetching data: {e}")
            else:
                print(f"  ✗ Could not resolve")
            print()

if __name__ == "__main__":
    asyncio.run(test_resolver())
