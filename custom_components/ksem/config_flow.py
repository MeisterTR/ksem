import logging
import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN
from .api import KsemClient, InvalidAuth

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required("host"): str,
    vol.Required("password"): str,
})

class KsemConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for KSEM."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        _LOGGER.debug("Starte Config-Flow mit Input: %s", user_input)
        if user_input:
            client = KsemClient(self.hass, user_input["host"], user_input["password"])
            try:
                await client.get_device_info()
            except InvalidAuth:
                errors["base"] = "auth"
            except Exception as e:
                _LOGGER.error("API Fehler: %s", e)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=user_input["host"], data=user_input)
        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)
