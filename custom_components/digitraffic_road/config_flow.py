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
        """Handle the initial step - search for road section."""
        errors = {}
        session = async_get_clientsession(self.hass)
        client = DigitraficClient(session)
        
        # If user submitted search query
        if user_input is not None:
            search_query = user_input.get("search_query", "").strip()
            
            if not search_query:
                errors["base"] = "empty_search"
            else:
                _LOGGER.debug("Searching for road sections: %s", search_query)
                
                # Search for matching road sections
                matching_sections = await client.search_road_sections(search_query)
                
                _LOGGER.debug("Found %d matching sections", len(matching_sections))
                
                if matching_sections:
                    # Store search results and go to selection step
                    self.search_results = matching_sections
                    return await self.async_step_select()
                else:
                    errors["base"] = "no_results"
        
        # Show search form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("search_query"): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "examples": "Search for road section (E4, E75 for instance), city, or area (Kemintie, Hämeentie)"
            },
        )

    async def async_step_select(self, user_input=None):
        """Select specific road section from search results."""
        if user_input is not None:
            section_id = user_input.get("road_section_id")
            
            # Find the selected section in results
            selected_section = next(
                (s for s in self.search_results if s["id"] == section_id),
                None
            )
            
            if selected_section:
                # Check if already configured
                await self.async_set_unique_id(section_id)
                self._abort_if_unique_id_configured()
                
                section_name = selected_section.get("name", section_id)
                _LOGGER.debug("Creating config entry for section: %s", section_id)
                
                return self.async_create_entry(
                    title=section_name,
                    data={
                        CONF_ROAD_SECTION_ID: section_id,
                        CONF_ROAD_SECTION: section_name,
                    },
                )
        
        # Build selection dictionary with full details
        section_choices = {}
        for section in self.search_results:
            section_id = section.get("id")
            name = section.get("name")
            road = section.get("road", "")
            km = section.get("km", "")
            location = section.get("location", "")
            description = section.get("description", "")
            
            # Build detailed display name
            display_name = f"{name}"
            if km:
                display_name += f" [{km}]"
            if description:
                display_name += f" - {description}"
            
            section_choices[section_id] = display_name
        
        schema = vol.Schema(
            {
                vol.Required("road_section_id"): vol.In(section_choices),
            }
        )
        
        return self.async_show_form(
            step_id="select",
            data_schema=schema,
            description_placeholders={
                "found_count": str(len(self.search_results))
            },
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
