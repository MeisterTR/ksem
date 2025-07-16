import logging
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from .modbus_obis_map import OBIS_SENSOR_DEFINITIONS

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
        "device_class": "current",
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

def group_register_blocks(sensor_defs, max_gap=2):
    sorted_addresses = sorted(sensor_defs.keys())
    blocks = []
    block = []
    last_end = None

    for addr in sorted_addresses:
        reg_size = 2 if sensor_defs[addr]["type"] in ("uint32", "int32") else 4
        if last_end is None or addr <= last_end + max_gap:
            block.append((addr, reg_size))
            last_end = addr + reg_size - 1
        else:
            blocks.append(block)
            block = [(addr, reg_size)]
            last_end = addr + reg_size - 1
    if block:
        blocks.append(block)

    _LOGGER.debug("Gruppierte Modbus-Registerblöcke: %s", blocks)
    return blocks


class ModbusSmartMeterClient:
    def __init__(self, host: str, port: int = 502, unit_id: int = 1):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self._client = None

    async def connect(self):
        if not self._client:
            self._client = AsyncModbusTcpClient(self.host, port=self.port)
            await self._client.connect()
            _LOGGER.debug("Modbus TCP verbunden mit %s:%s (Unit %s)", self.host, self.port, self.unit_id)

    async def disconnect(self):
        if self._client:
            await self._client.close()
            self._client = None
            _LOGGER.debug("Modbus TCP Verbindung getrennt")

    async def read_all(self):
        if not self._client:
            await self.connect()

        data = {}
        blocks = group_register_blocks(OBIS_SENSOR_DEFINITIONS)

        for block in blocks:
            start = block[0][0]
            total_words = sum(size for _, size in block)
            _LOGGER.debug("Lese Modbus-Block: Start=%s, Anzahl Register=%s", start, total_words)

            try:
                result = await self._client.read_holding_registers(
                    start, total_words, unit=self.unit_id
                )
                if result.isError():
                    _LOGGER.warning("Modbus-Fehler beim Lesen von %s-%s", start, start+total_words)
                    continue
                registers = result.registers
                _LOGGER.debug("Gelesene Register (%s): %s", start, registers)

                offset = 0
                for addr, size in block:
                    spec = OBIS_SENSOR_DEFINITIONS[addr]
                    decoder = BinaryPayloadDecoder.fromRegisters(
                        registers[offset:offset + size],
                        byteorder=Endian.BIG,
                        wordorder=Endian.BIG,
                    )
                    val = None
                    if spec["type"] == "uint32":
                        val = decoder.decode_32bit_uint()
                    elif spec["type"] == "int32":
                        val = decoder.decode_32bit_int()
                    elif spec["type"] == "uint64":
                        val = decoder.decode_64bit_uint()
                    else:
                        _LOGGER.warning("Unbekannter Typ: %s", spec["type"])
                        offset += size
                        continue

                    scaled_val = val * spec.get("scale", 1)
                    _LOGGER.debug("%s (%s): %s → skaliert: %s %s", spec["name"], addr, val, scaled_val, spec["unit"])
                    data[spec["name"]] = scaled_val
                    offset += size

            except Exception as e:
                _LOGGER.exception("Fehler beim Modbus-Blocklesen: %s", e)

        _LOGGER.debug("Alle OBIS-Daten gelesen: %s", data)
        return data