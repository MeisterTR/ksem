import logging
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

_LOGGER = logging.getLogger(__name__)

MODBUS_WALLBOX_REGISTERS = [
    {
        "name": "Enector_Ladeleistung",
        "address": 49246,
        "unit": "W",
        "device_class": "power",
        "state_class": "measurement",
        "scale": 0.001,
        "type": "uint64",
    },
    {
        "name": "Enector_status",
        "address": 49206,
        "unit": "",
        "scale": 1,
        "type": "uint64",
    },
    {
        "name": "Enector_L1",
        "address": 49218,
        "unit": "A",
        "device_class": "power",
        "state_class": "measurement",
        "scale": 0.001,
        "type": "uint32",
    },
    {
        "name": "Enector_geladene_Energie",
        "address": 49254,
        "unit": "Wh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "scale": 0.001,
        "type": "uint64",
    },
]


class ModbusWallboxClient:
    def __init__(self, host: str, port: int = 502, unit_id: int = 1):
        self._host = host
        self._port = port
        self._unit = unit_id
        self._client = None

    async def connect(self):
        self._client = AsyncModbusTcpClient(self._host, self._port)
        await self._client.connect()

    async def disconnect(self):
        if self._client:
            await self._client.close()

    async def read_all(self):
        data = {}
        if not self._client or not self._client.connected:
            await self.connect()
        for reg in MODBUS_WALLBOX_REGISTERS:
            address = reg["address"]
            count = 4 if "64" in reg["type"] else 2
            rr = await self._client.read_holding_registers(
                address, count, unit=self._unit
            )
            if rr.isError():
                _LOGGER.warning("Modbus read error at address %s", address)
                continue
            decoder = BinaryPayloadDecoder.fromRegisters(
                rr.registers, byteorder=Endian.BIG, wordorder=Endian.BIG
            )
            if reg["type"] == "uint64":
                value = decoder.decode_64bit_uint()
            elif reg["type"] == "uint32":
                value = decoder.decode_32bit_uint()
            else:
                value = decoder.decode_16bit_uint()
            value = value * reg.get("scale", 1)
            data[reg["name"]] = value
        return data
