import logging
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from .modbus_map import SENSOR_DEFINITIONS

_LOGGER = logging.getLogger(__name__)


def group_register_blocks(sensor_defs, max_gap=2):
    sorted_addresses = sorted(sensor_defs.keys())
    blocks = []
    block = []
    last_end = None

    for addr in sorted_addresses:
        t = sensor_defs[addr]["type"]
        if t in ("uint16", "int16"):
            reg_size = 1
        elif t in ("uint32", "int32"):
            reg_size = 2
        else:
            reg_size = 4

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


class KsemModbusClient:
    def __init__(self, host: str, port: int = 502, unit_id: int = 1):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self._client = None

    async def connect(self):
        if not self._client:
            self._client = AsyncModbusTcpClient(self.host, port=self.port)
            await self._client.connect()
            _LOGGER.debug(
                "Modbus TCP verbunden mit %s:%s (Unit %s)",
                self.host,
                self.port,
                self.unit_id,
            )

    async def disconnect(self):
        if self._client:
            await self._client.close()
            self._client = None
            self._protocol = None
            _LOGGER.debug("Modbus TCP Verbindung getrennt")

    async def read_all(self):
        if not self._client:
            await self.connect()

        data = {}
        blocks = group_register_blocks(SENSOR_DEFINITIONS)

        for block in blocks:
            start = block[0][0]
            total_words = sum(size for _, size in block)

            try:
                result = await self._client.read_holding_registers(
                    address=start, count=total_words, slave=self.unit_id
                )

                if result.isError():
                    _LOGGER.warning(
                        "Modbus-Fehler beim Lesen von %s-%s", start, start + total_words
                    )
                    continue
                registers = result.registers
                # _LOGGER.debug("Gelesene Register (%s): %s", start, registers)

                offset = 0
                for addr, size in block:
                    spec = SENSOR_DEFINITIONS[addr]
                    raw_regs = registers[offset : offset + size]

                    try:
                        datatype_enum = getattr(
                            self._client.DATATYPE, spec["type"].upper()
                        )
                        val = self._client.convert_from_registers(
                            raw_regs,
                            data_type=datatype_enum,
                            # byteorder="big",
                            word_order="big",
                        )
                    except Exception as err:
                        _LOGGER.warning(
                            "Fehler beim Konvertieren von %s: %s", spec["name"], err
                        )
                        offset += size
                        continue

                    scaled_val = val * spec.get("scale", 1)
                    _LOGGER.debug(
                        "%s (%s): %s → skaliert: %s %s",
                        spec["name"],
                        addr,
                        val,
                        scaled_val,
                        spec["unit"],
                    )
                    data[spec["name"]] = scaled_val
                    offset += size

            except Exception as e:
                _LOGGER.exception("Fehler beim Modbus-Blocklesen: %s", e)

        _LOGGER.debug("Alle OBIS-Daten gelesen: %s", data)
        return data
