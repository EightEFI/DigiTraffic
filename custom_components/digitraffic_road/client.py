"""Digitraffic API client for road conditions."""
import asyncio
import aiohttp
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://www.digitraffic.fi/api/v3/road-conditions"


class DigitraficClient:
    """Client to interact with Digitraffic API."""

    def __init__(self, session: aiohttp.ClientSession):
        """Initialize the client."""
        self.session = session

    async def get_road_sections(self) -> List[Dict[str, Any]]:
        """Fetch available road sections."""
        try:
            async with self.session.get(
                f"{BASE_URL}/road-sections",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("features", [])
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching road sections")
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching road sections: %s", err)
        return []

    async def get_road_conditions(self, section_id: str) -> Optional[Dict[str, Any]]:
        """Fetch current road conditions for a specific section."""
        try:
            async with self.session.get(
                f"{BASE_URL}/road-sections/{section_id}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    return await response.json()
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching road conditions for %s", section_id)
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching road conditions: %s", err)
        return None

    async def get_forecast(self, section_id: str) -> Optional[Dict[str, Any]]:
        """Fetch 12h forecast for a specific road section."""
        try:
            async with self.session.get(
                f"{BASE_URL}/road-sections/{section_id}/forecast",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    return await response.json()
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching forecast for %s", section_id)
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching forecast: %s", err)
        return None

    def parse_conditions(self, data: Dict[str, Any]) -> str:
        """Parse road conditions data into human-readable text."""
        if not data:
            return "Unknown"
        
        conditions = data.get("features", [])
        if not conditions:
            return "No data available"
        
        # Get the first (most relevant) condition
        feature = conditions[0]
        properties = feature.get("properties", {})
        
        condition_text = properties.get("condition", "Unknown")
        reliability = properties.get("reliability", "")
        
        # Format the response
        result = condition_text
        if reliability:
            result += f" (Reliability: {reliability}%)"
        
        return result

    def parse_forecast(self, data: Dict[str, Any]) -> str:
        """Parse forecast data into human-readable text."""
        if not data:
            return "No forecast data available"
        
        forecasts = data.get("features", [])
        if not forecasts:
            return "No forecast data available"
        
        # Build forecast text
        forecast_text = "12h Forecast:\n"
        for i, forecast in enumerate(forecasts[:12]):  # Limit to 12 hours
            properties = forecast.get("properties", {})
            time = properties.get("time", "Unknown")
            condition = properties.get("condition", "Unknown")
            forecast_text += f"{time}: {condition}\n"
        
        return forecast_text.strip()
