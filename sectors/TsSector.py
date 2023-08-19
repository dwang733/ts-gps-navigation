from dataclasses import dataclass
from struct import Struct

from filesystem.TsFile import TsFile

_HEADER_STRUCT = Struct("<I8sII")


@dataclass
class Header:
    version: int  # u4
    game_id: bytes  # 8s, 61 04 75 converts to 'euro2'?
    game_map_version: int  # u4
    item_count: int  # u4

    def __post_init__(self):
        assert self.version == 898
        assert self.game_map_version == 3


class TsSector:
    def __init__(self, file: TsFile):
        bytes = file.read()
        header = Header(*_HEADER_STRUCT.unpack(bytes[: _HEADER_STRUCT.size]))
        ofs = _HEADER_STRUCT.size

        for _ in range(header.item_count):
            item_type = int.from_bytes(bytes[ofs : ofs + 4], "little", signed=False)
            assert item_type <= 48

            if item_type == 3:
                # Road
                pass
            elif item_type == 8:
                # Cut Plane
                ofs += 0x34 + 0x05
                node_count = int.from_bytes(
                    bytes[ofs : ofs + 4], "little", signed=False
                )
                ofs += 0x04 + (0x08 * node_count)
            else:
                raise ValueError(f"Unknown item type {item_type}")
