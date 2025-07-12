import logging
import datetime
from typing import Union
from aiohttp import ClientResponse
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .helper import bearer_header

_LOGGER = logging.getLogger(__name__)

class Tokens:
    """Hält Access-Token und Ablaufdatum"""

    def __init__(self, access_token: str, token_type: str, expires_in: int):
        self.access_token = access_token
        self.expire_date = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
        _LOGGER.debug("Token erstellt, gültig bis %s", self.expire_date)

class InvalidAuth(Exception):
    """Fehlerhafte Authentifizierung"""

class KsemClient:
    """Client für REST-Aufrufe an die KSEM API mit Token-Refresh"""

    def __init__(self, hass, host: str, password: str) -> None:
        self.hass = hass
        self.host = host.rstrip("/")
        self.password = password
        self.token: Tokens | None = None
        _LOGGER.debug("KsemClient initialisiert für Host %s", self.host)

    async def _auth(self, session):
        url = f"http://{self.host}/api/web-login/token"
        data = {
            "grant_type": "password",
            "client_id": "emos",
            "client_secret": "56951025",
            "username": "admin",
            "password": self.password,
        }
        _LOGGER.debug("Auth POST %s", url)
        resp = await session.post(url, data=data)
        resp.raise_for_status()
        token_data = await resp.json()
        if "error" in token_data:
            raise InvalidAuth("Unauthorized")
        self.token = Tokens(token_data["access_token"], token_data.get("token_type", ""), token_data.get("expires_in", 0))

    async def _get(self, path: str) -> Union[dict, list]:
        session = async_get_clientsession(self.hass)
        if not self.token or datetime.datetime.now() > self.token.expire_date:
            await self._auth(session)
        url = f"http://{self.host}{path}"
        headers = bearer_header(self.token.access_token)
        _LOGGER.debug("GET %s", url)
        resp: ClientResponse = await session.get(url, headers=headers)
        if resp.status in (401, 500):
            _LOGGER.debug("Status %s, re-authenticating", resp.status)
            await self._auth(session)
            headers = bearer_header(self.token.access_token)
            resp = await session.get(url, headers=headers)
        resp.raise_for_status()
        data = await resp.json()
        _LOGGER.debug("Daten erhalten: %s", data)
        return data

    async def get_device_status(self) -> dict:
        _LOGGER.info("Hole Gerätestatus")
        return await self._get("/api/device-settings/deviceusage")

    async def get_device_info(self) -> dict:
        _LOGGER.info("Hole Geräteinformationen")
        return await self._get("/api/device-settings")
