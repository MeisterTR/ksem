import logging
import datetime
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

from .const import DOMAIN
from .api import KsemClient
from .modbus_helper import ModbusWallboxClient

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "number", "select", "switch"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Setup entry %s", entry.entry_id)
    hass.data.setdefault(DOMAIN, {})

    host = entry.data["host"]
    password = entry.data["password"]
    client = KsemClient(hass, host, password)
    modbus_client = ModbusWallboxClient(host)

    async def _update_smartmeter():
        try:
            return await client.get_device_status()
        except Exception as err:
            raise UpdateFailed(f"Smartmeter-Fehler: {err}")

    async def _update_wallbox():
        try:
            evse_list = await client.get_evse_list()
            result = []

            for evse in evse_list:
                uuid = evse["uuid"]
                details = await client.get_evse_details(uuid)
                evse.update(details)
                result.append(evse)

            try:
                res = await client.get_phase_switching()
                phase_usage = res.get("phase_usage", 0)
            except Exception as err:
                _LOGGER.warning(
                    "Phasenumschaltung konnte nicht geladen werden: %s", err
                )
                phase_usage = 0
            try:
                config = await client.get_energyflow_config()
            except Exception as err:
                _LOGGER.warning(
                    "Energiefluss-Konfiguration konnte nicht geladen werdSen: %s",
                    err,
                )
                config = {}
            try:
                evse_state = await client.get_evse_state()
            except Exception as err:
                _LOGGER.warning("EVSE-Status konnte nicht geladen werden: %s", err)
                evse_state = {}
            return {
                "evse": result,
                "phase_usage_state": phase_usage,
                "energyflow_config": config,
                "evse_state": evse_state,
            }

        except Exception as err:
            raise UpdateFailed(
                f"Wallbox-Daten konnten nicht geladen werden: {err}"
            ) from err

    async def _update_modbus():
        try:
            return await modbus_client.read_all()
        except Exception as err:
            raise UpdateFailed(f"Modbus-Wallbox-Fehler: {err}")

    smart_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="ksem_smartmeter",
        update_method=_update_smartmeter,
        update_interval=datetime.timedelta(seconds=30),
    )
    wallbox_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="ksem_wallbox",
        update_method=_update_wallbox,
        update_interval=datetime.timedelta(seconds=30),
    )
    modbus_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="ksem_modbus_wallbox",
        update_method=_update_modbus,
        update_interval=datetime.timedelta(seconds=10),
    )

    await smart_coordinator.async_refresh()
    await wallbox_coordinator.async_refresh()
    await modbus_coordinator.async_refresh()

    info = await client.get_device_info()
    mac = info.get("Mac")
    serial = info.get("Serial")
    model = info.get("ProductName")
    fw = info.get("FirmwareVersion")
    hw = info.get("DeviceType")

    device_info = DeviceInfo(
        identifiers={(DOMAIN, serial)},
        connections={(CONNECTION_NETWORK_MAC, mac)},
        name="Smartmeter",
        manufacturer="Kostal",
        model=model,
        hw_version=hw,
        sw_version=fw,
        configuration_url=f"http://{host}",
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "smart_coordinator": smart_coordinator,
        "wallbox_coordinator": wallbox_coordinator,
        "modbus_coordinator": modbus_coordinator,
        "device_info": device_info,
        "serial": serial,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = all(
        [
            await hass.config_entries.async_forward_entry_unload(entry, platform)
            for platform in PLATFORMS
        ]
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
