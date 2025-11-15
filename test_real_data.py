#!/usr/bin/env python3
"""Verify real road condition data for resolved sections."""

import asyncio
import aiohttp
import json

FORECAST_SECTIONS_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections/forecasts"

async def fetch_conditions(session, section_id: str):
    """Fetch road conditions for a section."""
    try:
        async with session.get(FORECAST_SECTIONS_URL) as resp:
            if resp.status != 200:
                print(f"Error: {resp.status}")
                return None
            
            data = await resp.json()
            for fs in data.get("forecastSections", []):
                if fs.get("id") == section_id:
                    obs = fs.get("observation", {})
                    forecasts = fs.get("forecasts", [])
                    
                    print(f"  Observation:")
                    print(f"    Time: {obs.get('time', 'N/A')}")
                    print(f"    Condition: {obs.get('condition', 'N/A')}")
                    
                    print(f"  Forecasts (next 5):")
                    for i, f in enumerate(forecasts[:5]):
                        if f.get("type") == "FORECAST":
                            print(f"    {i+1}. {f.get('time', 'N/A')}: {f.get('forecastConditionReason', {}).get('roadCondition', f.get('overallRoadCondition', 'N/A'))}")
                    
                    return True
            
            print("  Section not found in API")
            return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

async def main():
    async with aiohttp.ClientSession() as session:
        test_cases = [
            ("Tie 3: Valtatie 3 3.250", "00003_250_00000_1_0"),
            ("Valtatie 1", "00001_033_00000_1_0"),
            ("Tie 4", "00004_101_03169_2_0"),
        ]
        
        print("Fetching real road condition data for resolved sections:\n")
        
        for title, section_id in test_cases:
            print(f"'{title}' → {section_id}")
            await fetch_conditions(session, section_id)
            print()

if __name__ == "__main__":
    asyncio.run(main())
