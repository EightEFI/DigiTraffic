#!/usr/bin/env python3
"""Simple test of the resolver logic without Home Assistant dependencies."""

import asyncio
import aiohttp
import re
import json
from typing import Optional, Dict, Any

# Mirror the resolver methods from client.py
FORECAST_SECTIONS_METADATA_URL = "https://tie.digitraffic.fi/api/weather/v1/forecast-sections"

def _normalize_string(s: str) -> str:
    """Normalize string for comparison: lowercase, remove punctuation, collapse spaces."""
    s = s.lower()
    s = re.sub(r'[^\w\s]', ' ', s)  # Replace punctuation with spaces
    s = re.sub(r'\s+', ' ', s).strip()  # Collapse multiple spaces
    return s

async def resolve_section_id(session, user_input: str) -> Optional[str]:
    """Resolve user-entered section title to API section ID via token overlap matching."""
    # If input already looks like an API ID, return as-is
    if re.match(r"^[0-9]{5}_\d+", user_input):
        return user_input
    
    try:
        async with session.get(FORECAST_SECTIONS_METADATA_URL) as resp:
            if resp.status != 200:
                print(f"Error: metadata endpoint returned {resp.status}")
                return None
            
            data = await resp.json()
            features = data.get("features", [])
            
            # Normalize user input for comparison
            normalized_input = _normalize_string(user_input)
            input_tokens = set(normalized_input.split())
            
            best_match = None
            best_score = 0
            
            for feature in features:
                props = feature.get("properties", {})
                description = props.get("description", "")
                
                # Normalize metadata description
                normalized_desc = _normalize_string(description)
                desc_tokens = set(normalized_desc.split())
                
                # Calculate token overlap score
                overlap = len(input_tokens & desc_tokens)
                if overlap > best_score:
                    best_score = overlap
                    best_match = props.get("id")
            
            if best_match and best_score > 0:
                print(f"Resolver: '{user_input}' matched with score {best_score}")
                return best_match
            
            return None
    except Exception as e:
        print(f"Error in resolver: {e}")
        return None

async def main():
    """Test the resolver with real API data."""
    async with aiohttp.ClientSession() as session:
        test_cases = [
            "Tie 3: Valtatie 3 3.250",
            "Valtatie 3 3.250",
            "Valtatie 1",
            "Tie 4",
        ]
        
        print("Testing resolver with real Digitraffic API metadata:\n")
        
        for title in test_cases:
            print(f"Input: '{title}'")
            resolved = await resolve_section_id(session, title)
            if resolved:
                print(f"  ✓ Resolved to API ID: {resolved}\n")
            else:
                print(f"  ✗ Could not resolve\n")

if __name__ == "__main__":
    asyncio.run(main())
