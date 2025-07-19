import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN
from homeassistant.helpers.entity import EntityCategory
from .modbus_map import SENSOR_DEFINITIONS
from homeassistant.components.sensor import SensorDeviceClass

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

    obis_entities = []
    for addr, spec in SENSOR_DEFINITIONS.items():
        if spec["device"] == "smartmeter":
            info = device_info
        elif spec["device"] == "wallbox":
            info = wallbox_device_info
        else:
            info = device_info  # fallback
        obis_entities.append(KsemObisModbusSensor(modbus, addr, spec, info))

    # Speichere device_info zur Weitergabe
    hass.data[DOMAIN][entry.entry_id]["wallbox_device_info"] = wallbox_device_info

    evse_power_entity = KsemEvseAvailablePowerSensor(wallbox, wallbox_device_info)

    async_add_entities(
        smartmeter_entities + wallbox_entities + [evse_power_entity] + obis_entities
    )


class KsemEvseAvailablePowerSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, device_info):
        super().__init__(coordinator)
        self._attr_name = "Verfügbare Ladeleistung"
        self._attr_unique_id = "ksem_evse_available_power"
        self._attr_native_unit_of_measurement = "W"
        self._attr_device_info = device_info
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        state = self.coordinator.data.get("evse_state", {})
        try:
            curtail = state.get("CurtailmentSetpoint", {})
            total_ma = (
                curtail.get("l1", 0) + curtail.get("l2", 0) + curtail.get("l3", 0)
            )
            return round((total_ma / 1000) * 230)
        except Exception as e:
            _LOGGER.warning("Fehler bei Umrechnung der Ladeleistung: %s", e)
            return None

    @property
    def extra_state_attributes(self):
        state = self.coordinator.data.get("evse_state", {})
        attrs = {
            "Curtailment_L2": state.get("CurtailmentSetpoint", {}).get("l2", 0),
            "Curtailment_L3": state.get("CurtailmentSetpoint", {}).get("l3", 0),
            "Curtailment_total": state.get("CurtailmentSetpoint", {}).get("total", 0),
            "ChargingPower_L1": state.get("EvChargingPower", {}).get("l1", 0),
            "ChargingPower_L2": state.get("EvChargingPower", {}).get("l2", 0),
            "ChargingPower_L3": state.get("EvChargingPower", {}).get("l3", 0),
            "ChargingPower_total": state.get("EvChargingPower", {}).get("total", 0),
            "OverloadProtectionActive": state.get("OverloadProtectionActive"),
            "GridPowerLimit": state.get("GridPowerLimit", {}).get("Power"),
            "GridLimitActive": state.get("GridPowerLimit", {}).get("Active"),
            "PVPowerLimit": state.get("PVPowerLimit", {}).get("Power"),
            "PVLimitActive": state.get("PVPowerLimit", {}).get("Active"),
        }
        return attrs


class KsemSmartmeterSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, key, name, unit, device_info, serial):
        super().__init__(coordinator)
        self._sensor_key = key
        self._attr_name = f"{name}"
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{serial}_{key.lower()}"
        self._attr_device_info = device_info
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

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


class KsemObisModbusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, address, spec, device_info):
        super().__init__(coordinator)
        self._address = address
        self._key = spec["name"]
        self._mapping = spec.get("map")
        self._attr_name = f"{spec['name']}"
        self._attr_native_unit_of_measurement = spec["unit"]
        # ENUM-Erkennung
        if spec.get("device_class") == "enum":
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = list(self._mapping.values()) if self._mapping else []
            self._attr_native_unit_of_measurement = None
            self._attr_state_class = None
        else:
            self._attr_device_class = spec.get("device_class")
            if spec.get("device_class") == "energy" or spec.get("unit") in (
                "Wh",
                "kWh",
                "VAh",
                "varh",
            ):
                self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            elif spec.get("device_class") in (
                "power",
                "voltage",
                "current",
                "battery",
                "temperature",
                "frequency",
            ):
                self._attr_state_class = SensorStateClass.MEASUREMENT
            else:
                self._attr_state_class = None
        ident = next(iter(device_info["identifiers"]))[1]
        self._attr_unique_id = f"{ident}_obis_{address}"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        val = self.coordinator.data.get(self._key)
        if self._mapping:
            return self._mapping.get(int(val), f"Unbekannt ({val})")
        return val
