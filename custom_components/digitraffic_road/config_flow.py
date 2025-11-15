"""Config flow for Digitraffic Road Conditions integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging

from .client import DigitraficClient
from .const import DOMAIN, CONF_ROAD_SECTION, CONF_ROAD_SECTION_ID

_LOGGER = logging.getLogger(__name__)


class DigitraficRoadConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Digitraffic Road Conditions."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        road_sections = []

        # Try to fetch road sections
        try:
            session = async_get_clientsession(self.hass)
            client = DigitraficClient(session)
            sections_data = await client.get_road_sections()
            
            # Extract road section names from GeoJSON features
            for feature in sections_data:
                properties = feature.get("properties", {})
                section_id = properties.get("id", "")
                section_name = properties.get("name", section_id)
                if section_id:
                    road_sections.append((section_id, section_name))
            
            road_sections.sort(key=lambda x: x[1])
        except Exception as err:
            _LOGGER.error("Error fetching road sections: %s", err)
            errors["base"] = "cannot_connect"

        if user_input is not None:
            section_id = user_input.get(CONF_ROAD_SECTION_ID)
            section_name = next(
                (name for sid, name in road_sections if sid == section_id),
                section_id
            )
            
            # Check if already configured
            await self.async_set_unique_id(section_id)
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=section_name,
                data={
                    CONF_ROAD_SECTION_ID: section_id,
                    CONF_ROAD_SECTION: section_name,
                },
            )

        if not road_sections:
            return self.async_abort(reason="cannot_connect")

        schema = vol.Schema(
            {
                vol.Required(CONF_ROAD_SECTION_ID): vol.In(
                    {section_id: section_name for section_id, section_name in road_sections}
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this integration."""
        return DigitraficRoadOptionsFlow(config_entry)


class DigitraficRoadOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Digitraffic Road Conditions."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))
