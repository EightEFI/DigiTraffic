"""Data coordinator for DigiTraffic."""
import logging
from datetime import timedelta
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import DigitraficClient
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class DigitraficDataCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Digitraffic data updates."""

    def __init__(self, hass: HomeAssistant, section_id: str, language: str = "fi"):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.section_id = section_id
        self.client = DigitraficClient(async_get_clientsession(hass))
        self.language = language
        _LOGGER.debug("Initialized coordinator for section: %s", section_id)

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Digitraffic API."""
        try:
            _LOGGER.debug("Updating data for section: %s", self.section_id)
            # If section_id looks like a numeric TMS id, fetch TMS-specific data
            data: Dict[str, Any]
            if str(self.section_id).isdigit():
                station = await self.client.async_get_tms_station(int(self.section_id))
                sensor_constants = await self.client.async_get_tms_sensor_constants(int(self.section_id))
                tms_data = await self.client.async_get_tms_station_data(int(self.section_id))

                measurements = {}\n                # Convert sensorValues list into a name -> value mapping for sensors\n                if tms_data and isinstance(tms_data, dict):\n                    _LOGGER.debug(\"TMS data keys: %s\", list(tms_data.keys()))\n                    sensor_values = tms_data.get(\"sensorValues\", [])\n                    _LOGGER.debug(\"Found %d sensor values for station %s\", len(sensor_values), self.section_id)\n                    \n                    for sv in sensor_values:\n                        name = sv.get(\"name\")\n                        value = sv.get(\"value\")\n                        if not name:\n                            continue\n                        _LOGGER.debug(\"Sensor: %s = %s (%s)\", name, value, sv.get(\"unit\"))\n                        measurements[name] = {\n                            \"id\": sv.get(\"id\"),\n                            \"value\": value,\n                            \"unit\": sv.get(\"unit\"),\n                            \"measuredTime\": sv.get(\"measuredTime\"),\n                            \"timeWindowStart\": sv.get(\"timeWindowStart\"),\n                            \"timeWindowEnd\": sv.get(\"timeWindowEnd\"),\n                        }

                if station is None and not measurements:
                    _LOGGER.warning("No TMS station data for id: %s", self.section_id)

                data = {
                    "tms_station": station,
                    "sensor_constants": sensor_constants,
                    "measurements": measurements,
                }
            else:
                conditions = await self.client.get_road_conditions(self.section_id, language=self.language)
                forecast = await self.client.get_forecast(self.section_id, language=self.language)
                
                if conditions is None:
                    _LOGGER.warning("No conditions data for section: %s", self.section_id)
                if forecast is None:
                    _LOGGER.warning("No forecast data for section: %s", self.section_id)
                
                data = {
                    "conditions": conditions,
                    "forecast": forecast,
                }
            
            _LOGGER.debug("Successfully updated data for section: %s", self.section_id)
            return data
            
        except Exception as err:
            _LOGGER.error("Error communicating with Digitraffic API: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with Digitraffic API: {err}") from err
