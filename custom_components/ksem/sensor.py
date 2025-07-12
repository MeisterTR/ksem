import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "CpuLoad": ("CPU Load", "%"),
    "CpuTemp": ("CPU Temperature", "°C"),
    "RamFree": ("RAM Free", "MB"),
    "RamTotal": ("RAM Total", "MB"),
    "FlashAppFree": ("Flash App Free", "MB"),
    "FlashAppTotal": ("Flash App Total", "MB"),
    "FlashDataFree": ("Flash Data Free", "MB"),
    "FlashDataTotal": ("Flash Data Total", "MB"),
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    _LOGGER.debug("Setup sensors for %s", entry.entry_id)
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device_info = data["device_info"]
    serial = data["serial"]

    entities = [
        KsemSensor(coordinator, key, name, unit, device_info, serial)
        for key, (name, unit) in SENSOR_TYPES.items()
    ]
    async_add_entities(entities, update_before_add=True)

class KsemSensor(CoordinatorEntity, SensorEntity):
    """Generic sensor for KSEM metrics"""

    def __init__(self, coordinator, key, name, unit, device_info: DeviceInfo, serial: str):
        super().__init__(coordinator)
        self._sensor_key = key
        self._attr_name = f"KSEM {name}"
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{serial}_{key.lower()}"
        self._device_info = device_info

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return self._device_info

    @property
    def native_value(self):
        return self.coordinator.data.get(self._sensor_key)

    @property
    def available(self):
        return self.coordinator.last_update_success
