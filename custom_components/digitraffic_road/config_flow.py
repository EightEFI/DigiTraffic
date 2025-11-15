"""Config flow for DigiTraffic integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging

from .client import DigitraficClient
from .const import (
    DOMAIN,
    CONF_ROAD_SECTION,
    CONF_ROAD_SECTION_ID,
    CONF_LANGUAGE,
    CONF_MONITOR_TYPE,
    CONF_TMS_ID,
    MONITOR_CONDITIONS,
    MONITOR_TMS,
)

_LOGGER = logging.getLogger(__name__)


class DigitraficRoadConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DigiTraffic."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Initial step: ask preferred language, then proceed to section input."""
        errors = {}
        # If language selected, move to monitor type step
        if user_input is not None and "language" in user_input:
            self.language = user_input.get("language")
            return await self.async_step_monitor_type()

        # Show language selection form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("language", default="fi"): vol.In({"fi": "Suomi", "en": "English"}),
                }
            ),
        )

    async def async_step_monitor_type(self, user_input=None):
        """Ask whether to monitor driving conditions or a TMS/LAM station."""

        if user_input is not None and "monitor_type" in user_input:
            self.monitor_type = user_input.get("monitor_type")
            if self.monitor_type == MONITOR_TMS:
                return await self.async_step_tms()
            return await self.async_step_section()

        return self.async_show_form(
            step_id="monitor_type",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "monitor_type",
                        default=MONITOR_CONDITIONS,
                    ): vol.In({MONITOR_CONDITIONS: "Ajokeli / Driving conditions", MONITOR_TMS: "TMS / Traffic measuring station"}),
                }
            ),
        )

    async def async_step_section(self, user_input=None):
        """Handle the step - enter road section ID or title."""
        errors = {}

        # If user submitted input
        if user_input is not None:
            section_input = user_input.get("section_input", "").strip()

            if not section_input:
                errors["base"] = "empty_search"
            else:
                _LOGGER.debug("Road section input: %s", section_input)
                # Use the input as-is for the section ID (will be used to fetch conditions)
                section_id = section_input.replace(" ", "_").replace(":", "").replace(".", "_")
                section_name = section_input

                # Default monitor type to conditions if not set
                monitor_type = getattr(self, "monitor_type", MONITOR_CONDITIONS)

                # Create a unique id combining monitor type and normalized input
                unique_id = f"{monitor_type}_{section_id}"

                # Check if already configured
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                _LOGGER.debug("Creating config entry for section: %s", section_name)

                data = {
                    CONF_MONITOR_TYPE: monitor_type,
                    CONF_LANGUAGE: getattr(self, "language", "fi"),
                }

                if monitor_type == MONITOR_CONDITIONS:
                    data.update({
                        CONF_ROAD_SECTION_ID: section_input,
                        CONF_ROAD_SECTION: section_name,
                    })
                else:
                    # For other monitor types, store the raw input into tms id field as a fallback
                    data.update({CONF_TMS_ID: section_input, CONF_ROAD_SECTION: section_name})

                return self.async_create_entry(title=section_name, data=data)

        # Show input form
        return self.async_show_form(
            step_id="section",
            data_schema=vol.Schema(
                {
                    vol.Required("section_input", description={"suggested_value": "Tie 4: Kemintie 4.421"}): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "example": "Tie 4: Kemintie 4.421"
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this integration."""
        return DigitraficRoadOptionsFlow(config_entry)


class DigitraficRoadOptionsFlow(config_entries.OptionsFlow):
    """Handle options for DigiTraffic."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))
