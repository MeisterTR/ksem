import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN
from .modbus_helper import MODBUS_WALLBOX_REGISTERS

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "CpuLoad": ("CPU Load", "%"),
    "CpuTemp": ("CPU Temperature", "°C"),
    "RamFree": ("RAM Free", "kB"),
    "RamTotal": ("RAM Total", "kB"),
    "FlashAppFree": ("Flash App Free", "B"),
    "FlashAppTotal": ("Flash App Total", "B"),
    "FlashDataFree": ("Flash Data Free", "B"),
    "FlashDataTotal": ("Flash Data Total", "B"),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    smart = data["smart_coordinator"]
    wallbox = data["wallbox_coordinator"]
    modbus = data["modbus_coordinator"]
    device_info = data["device_info"]
    serial = data["serial"]

    smartmeter_entities = [
        KsemSmartmeterSensor(smart, key, name, unit, device_info, serial)
        for key, (name, unit) in SENSOR_TYPES.items()
    ]

    wallbox_entities = []
    wallbox_device_info = None
    for wb in wallbox.data.get("evse", []):
        uuid = wb.get("uuid")
        label = wb.get("label", "Wallbox")
        model = wb.get("model", "")
        state = wb.get("state", "unbekannt")
        details = wb.get("details", {})
        serial = details.get("serial", uuid)
        version = details.get("version", "")

        wallbox_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"wallbox-{uuid}")},
            name=f"Wallbox {label}",
            model=model,
            serial_number=serial,
            sw_version=version,
            manufacturer="Kostal",
        )

        wallbox_entities.append(
            KsemWallboxSensor(uuid, f"{label} State", model, serial, version, state)
        )

    # Speichere device_info zur Weitergabe
    hass.data[DOMAIN][entry.entry_id]["wallbox_device_info"] = wallbox_device_info

    modbus_entities = [
        KsemWallboxModbusSensor(modbus, reg, wallbox_device_info)
        for reg in MODBUS_WALLBOX_REGISTERS
    ]

    async_add_entities(smartmeter_entities + wallbox_entities + modbus_entities)


class KsemSmartmeterSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, key, name, unit, device_info, serial):
        super().__init__(coordinator)
        self._sensor_key = key
        self._attr_name = f"KSEM {name}"
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{serial}_{key.lower()}"
        self._attr_device_info = device_info
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self.coordinator.data.get(self._sensor_key)


class KsemWallboxSensor(SensorEntity):
    def __init__(self, uuid, name, model, serial, version, value):
        self._attr_name = name
        self._attr_unique_id = f"{uuid}_state"
        self._uuid = uuid
        self._model = model
        self._serial = serial
        self._version = version
        self._state = value

    @property
    def state(self):
        return self._state

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def device_info(self) -> DeviceInfo:
        return {
            "identifiers": {(DOMAIN, f"wallbox-{self._uuid}")},
            "name": f"Wallbox {self._uuid[:6]}",
            "model": self._model,
            "serial_number": self._serial,
            "sw_version": self._version,
            "manufacturer": "Kostal",
        }


class KsemWallboxModbusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, reg, device_info):
        super().__init__(coordinator)
        self._reg = reg
        self._attr_name = reg["name"]
        self._attr_unique_id = f"modbus_{reg['address']}"
        self._attr_native_unit_of_measurement = reg.get("unit", "")
        self._attr_device_class = reg.get("device_class")
        self._attr_state_class = (
            SensorStateClass.MEASUREMENT
            if reg.get("state_class") == "measurement"
            else SensorStateClass.TOTAL_INCREASING
        )
        self._attr_device_info = device_info

    @property
    def native_value(self):
        return self.coordinator.data.get(self._reg["name"])
