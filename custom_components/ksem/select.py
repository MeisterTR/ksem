import asyncio
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN
from aiohttp import ClientSession, WSMsgType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

MODE_MAP = {
    "lock": "Lock Mode",
    "grid": "Power Mode",
    "pv": "Solar Pure Mode",
    "hybrid": "Solar Plus Mode",
}
REVERSE_MODE_MAP = {v: k for k, v in MODE_MAP.items()}

PHASE_MAP = {0: "3 Phasen", 1: "1 Phase", 2: "Automatisch"}
REVERSE_PHASE_MAP = {v: k for k, v in PHASE_MAP.items()}


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    token = client.token.access_token
    device_info = data.get("wallbox_device_info")
    coordinator = data["wallbox_coordinator"]

    mode_entity = KsemChargeModeSelect(hass, entry.entry_id, client, token, device_info)

    phase_entity = KsemPhaseSwitchSelect(
        coordinator=coordinator,
        client=client,
        device_info=device_info,
    )

    async_add_entities([mode_entity, phase_entity])


class KsemPhaseSwitchSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, client, device_info: DeviceInfo):
        super().__init__(coordinator)
        self._client = client
        self._attr_name = "Phasenumschaltung"
        self._attr_unique_id = "ksem_phase_switch"
        self._attr_options = list(PHASE_MAP.values())
        self._attr_device_info = device_info

    @property
    def current_option(self):
        val = self.coordinator.data.get("phase_usage_state", 0)
        return PHASE_MAP.get(val)

    async def async_select_option(self, option: str):
        if option not in REVERSE_PHASE_MAP:
            _LOGGER.warning("Ungültige Auswahl: %s", option)
            return

        new_value = REVERSE_PHASE_MAP[option]
        await self._client.set_phase_switching(new_value)
        await self.coordinator.async_request_refresh()


class KsemChargeModeSelect(SelectEntity):
    def __init__(self, hass, entry_id, client, token, device_info):
        self._entry_id = entry_id
        self._client = client
        self._token = token
        self._attr_name = "Wallbox Charge Mode"
        self._attr_unique_id = "ksem_charge_mode"
        self._attr_options = list(MODE_MAP.values())
        self._api_mode = None
        self._attr_device_info = device_info
        self._hass = hass
        self._ws_task = hass.loop.create_task(self._listen_websocket())

    @property
    def current_option(self):
        return MODE_MAP.get(self._api_mode)

    async def async_select_option(self, option: str):
        mode = REVERSE_MODE_MAP.get(option)
        if mode:
            await self._client.set_charge_mode(
                mode=mode,
                minpvpowerquota=None,
                mincharginpowerquota=None,
                entry_id=self._entry_id,
            )
            self._api_mode = mode
            self.async_write_ha_state()

    async def _listen_websocket(self):
        url = f"ws://{self._client.host}/api/data-transfer/ws/json/json/local/config/e-mobility/chargemode"
        session = async_get_clientsession(self._hass)

        while True:
            try:
                async with session.ws_connect(
                    url, headers={"Authorization": f"Bearer {self._token}"}
                ) as ws:
                    await ws.send_str(f"Bearer {self._token}")
                    _LOGGER.info("WebSocket verbunden für Lademodus")

                    async for msg in ws:
                        if msg.type == WSMsgType.TEXT:
                            try:
                                import json

                                data = json.loads(msg.data)
                                if data.get("topic", "").endswith("chargemode"):
                                    msg_data = data.get("msg", {})
                                    mode = msg_data.get("mode")
                                    if mode != self._api_mode:
                                        _LOGGER.debug("WebSocket Update: mode=%s", mode)
                                        self._api_mode = mode
                                        self.async_write_ha_state()

                                    quotas = self._hass.data[DOMAIN][
                                        self._entry_id
                                    ].get("quota_entities", {})
                                    if (
                                        "minpv" in quotas
                                        and "minpvpowerquota" in msg_data
                                    ):
                                        quotas["minpv"].update_value(
                                            msg_data["minpvpowerquota"]
                                        )
                                    if (
                                        "mincharge" in quotas
                                        and "mincharginpowerquota" in msg_data
                                    ):
                                        quotas["mincharge"].update_value(
                                            msg_data["mincharginpowerquota"]
                                        )

                                    self._hass.data[DOMAIN][self._entry_id][
                                        "last_chargemode"
                                    ] = msg_data

                            except Exception as e:
                                _LOGGER.warning("WebSocket JSON decode error: %s", e)
                        elif msg.type == WSMsgType.ERROR:
                            _LOGGER.warning("WebSocket-Fehler: %s", msg)
                            break

            except Exception as err:
                _LOGGER.error("WebSocket-Verbindung fehlgeschlagen: %s", err)

            _LOGGER.info("WebSocket getrennt, versuche Neuverbindung in 30 Sekunden...")
            await asyncio.sleep(30)
