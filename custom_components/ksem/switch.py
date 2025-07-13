from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["wallbox_coordinator"]
    client = data["client"]
    device_info = data.get("wallbox_device_info")

    entity = BatteryUsageSwitch(coordinator, client, device_info)
    async_add_entities([entity])


class BatteryUsageSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, client, device_info: DeviceInfo):
        super().__init__(coordinator)
        self._client = client
        self._attr_name = "Battery Usage bei PV"
        self._attr_unique_id = "ksem_battery_usage"
        self._attr_device_info = device_info

    @property
    def is_on(self):
        config = self.coordinator.data.get("energyflow_config", {})
        return config.get("batteryusage", False)

    async def async_turn_on(self, **kwargs):
        await self._client.set_battery_usage(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self._client.set_battery_usage(False)
        await self.coordinator.async_request_refresh()
