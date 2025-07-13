import logging
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    device_info = data.get("wallbox_device_info")
    last_ws_data = data.get("last_chargemode", {})

    entity1 = MinPvPowerQuota(
        client, device_info, last_ws_data.get("minpvpowerquota", 0), entry.entry_id
    )
    entity2 = MinChargingPowerQuota(
        client, device_info, last_ws_data.get("mincharginpowerquota", 0), entry.entry_id
    )

    # Live-Zugriff für WS-Listener ermöglichen
    hass.data[DOMAIN][entry.entry_id]["quota_entities"] = {
        "minpv": entity1,
        "mincharge": entity2,
    }

    async_add_entities([entity1, entity2])


class MinPvPowerQuota(NumberEntity):
    def __init__(self, client, device_info: DeviceInfo, initial, entry_id):
        self._entry_id = entry_id
        self._client = client
        self._attr_name = "Min PV Power"
        self._attr_unique_id = "ksem_minpvpowerquota"
        self._attr_device_info = device_info
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 10
        self._value = initial

    @property
    def native_value(self):
        return self._value

    async def async_set_native_value(self, value: float):
        await self._client.set_charge_mode(
            mode=None,
            minpvpowerquota=int(value),
            mincharginpowerquota=None,
            entry_id=self._entry_id,
        )
        self._value = int(value)
        self.async_write_ha_state()

    def update_value(self, value: int):
        self._value = value
        self.async_write_ha_state()


class MinChargingPowerQuota(NumberEntity):
    def __init__(self, client, device_info: DeviceInfo, initial, entry_id):
        self._entry_id = entry_id
        self._client = client
        self._attr_name = "Min Charging Power"
        self._attr_unique_id = "ksem_mincharginpowerquota"
        self._attr_device_info = device_info
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 25
        self._value = initial

    @property
    def native_value(self):
        return self._value

    async def async_set_native_value(self, value: float):
        await self._client.set_charge_mode(
            mode=None,
            mincharginpowerquota=int(value),
            minpvpowerquota=None,
            entry_id=self._entry_id,
        )
        self._value = int(value)
        self.async_write_ha_state()

    def update_value(self, value: int):
        self._value = value
        self.async_write_ha_state()
