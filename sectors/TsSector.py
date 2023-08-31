import io
from dataclasses import dataclass
from enum import Enum
from struct import Struct
from typing import BinaryIO

from filesystem.TsFile import TsFile
from sectors.TsRoadItem import TsRoadItem
from utils import StructDataClass

# u32 item_type
# u64 uid
# kdop array_float minimums (u4, len 5)
# kdop array_float maximums (u4, len 5)
# u32 flags
# u8 view_dist
_ITEM_HEADER_SIZE = 0x30 + 0x05


class TsItemEnum(Enum):
    TERRAIN = 1
    BUILDING = 2
    ROAD = 3
    PREFAB = 4
    MODEL = 5
    COMPANY = 6
    SERVICE = 7
    CUT_PLANE = 8
    MOVER = 9
    NO_WEATHER = 11
    CITY = 12
    HINGE = 13
    MAP_OVERLAY = 18
    FERRY = 19
    SOUND = 21
    GARAGE = 22
    CAMERA_POINT = 23
    TRIGGER = 34
    FUEL_PUMP = 35  # services
    ROAD_SIDE_ITEM = 36  # sign
    BUS_STOP = 37
    TRAFFIC_RULE = 38  # traffic_area
    BEZIER_PATCH = 39
    COMPOUND = 40
    TRAJECTORY_ITEM = 41
    MAP_AREA = 42
    FAR_MODEL = 43
    CURVE = 44
    CAMERA = 45
    CUTSCENE = 46
    VISIBILITY_AREA = 48


@dataclass
class _SectorHeader(StructDataClass):
    struct = Struct("<I8sII")

    version: int  # u4
    game_id: bytes  # 8s?, 61 04 75 converts to 'euro2'?
    game_map_version: int  # u4
    item_count: int  # u4

    def __post_init__(self):
        assert self.version == 898
        assert self.game_map_version == 3


class TsSector:
    def __init__(self, file: TsFile):
        f = io.BytesIO(file.read())

        roads: list[TsRoadItem] = []
        try:
            header = _SectorHeader.parse(f)

            # Parse items.
            for _ in range(header.item_count):
                item_type_int = int.from_bytes(f.read(4), "little", signed=False)
                if item_type_int > 48:
                    raise ValueError(f"Unrecognized item type '{item_type_int}'")
                item_type = TsItemEnum(item_type_int)

                f.seek(_ITEM_HEADER_SIZE, io.SEEK_CUR)
                # print(f"Parsing item type '{item_type}'...")
                # print(f"Pos after item header: {hex(f.tell())}")
                if item_type == TsItemEnum.TERRAIN:
                    f.seek(0xEA, io.SEEK_CUR)
                    veg_sphere_count = int.from_bytes(f.read(4), "little", signed=False)
                    f.seek(0x14 * veg_sphere_count, io.SEEK_CUR)
                    self._parse_quad_info(f)
                    self._parse_quad_info(f)
                    f.seek(0x20, io.SEEK_CUR)
                elif item_type == TsItemEnum.BUILDING:
                    f.seek(0x2C, io.SEEK_CUR)
                    building_offset_count = int.from_bytes(
                        f.read(4), "little", signed=False
                    )
                    f.seek(0x04 * building_offset_count, io.SEEK_CUR)
                elif item_type == TsItemEnum.ROAD:
                    road = TsRoadItem.parse(f)
                    roads.append(road)
                elif item_type == TsItemEnum.PREFAB:
                    f.seek(0x08 + 0x08, io.SEEK_CUR)
                    additional_parts_count = int.from_bytes(
                        f.read(4), "little", signed=True
                    )
                    f.seek(0x08 * additional_parts_count, io.SEEK_CUR)
                    node_count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek(0x08 * node_count, io.SEEK_CUR)
                    connected_item_count = int.from_bytes(
                        f.read(4), "little", signed=True
                    )
                    f.seek((0x08 * connected_item_count) + 0x08, io.SEEK_CUR)
                    f.seek(0x02 + (0x0C * node_count) + 0x08, io.SEEK_CUR)
                elif item_type == TsItemEnum.MODEL:
                    f.seek(0x18, io.SEEK_CUR)
                    add_parts_count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek((0x08 * add_parts_count) + 0x24, io.SEEK_CUR)
                elif item_type == TsItemEnum.COMPANY:
                    f.seek(0x08 + 0x08 + 0x08 + 0x08, io.SEEK_CUR)
                    count = int.from_bytes(f.read(4), "little", signed=True)
                    for _ in range(5):
                        f.seek(0x08 * count, io.SEEK_CUR)
                        count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek(0x08 * count, io.SEEK_CUR)
                elif item_type == TsItemEnum.SERVICE:
                    f.seek(0x10, io.SEEK_CUR)
                    sub_item_uid_count = int.from_bytes(
                        f.read(4), "little", signed=True
                    )
                    f.seek(0x08 * sub_item_uid_count, io.SEEK_CUR)
                elif item_type == TsItemEnum.CUT_PLANE:
                    node_count = int.from_bytes(f.read(4), "little", signed=False)
                    f.seek(0x08 * node_count, io.SEEK_CUR)
                elif item_type == TsItemEnum.CITY:
                    f.seek(0x08 + 0x04 + 0x04 + 0x08, io.SEEK_CUR)
                elif item_type == TsItemEnum.MAP_OVERLAY:
                    f.seek(0x08 + 0x08, io.SEEK_CUR)
                elif item_type == TsItemEnum.FERRY:
                    f.seek(0x08 + 0x08 + 0x08 + 0x0C, io.SEEK_CUR)
                elif item_type == TsItemEnum.GARAGE:
                    f.seek(0x1C, io.SEEK_CUR)
                    sub_item_uid_count = int.from_bytes(
                        f.read(4), "little", signed=True
                    )
                    f.seek(0x08 * sub_item_uid_count, io.SEEK_CUR)
                elif item_type == TsItemEnum.TRIGGER:
                    tag_count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek(0x08 * tag_count, io.SEEK_CUR)
                    node_count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek(0x08 * node_count, io.SEEK_CUR)
                    trigger_action_count = int.from_bytes(
                        f.read(4), "little", signed=True
                    )
                    for _ in range(trigger_action_count):
                        f.seek(0x08, io.SEEK_CUR)
                        has_override = int.from_bytes(f.read(4), "little", signed=True)
                        if has_override < 0:
                            continue
                        f.seek(0x04 * has_override, io.SEEK_CUR)
                        parameter_count = int.from_bytes(
                            f.read(4), "little", signed=True
                        )
                        for _ in range(parameter_count):
                            param_length = int.from_bytes(
                                f.read(4), "little", signed=True
                            )
                            f.seek(0x04 + param_length, io.SEEK_CUR)
                        target_tag_count = int.from_bytes(
                            f.read(4), "little", signed=True
                        )
                        f.seek((0x08 * target_tag_count) + 0x08, io.SEEK_CUR)
                    if node_count == 1:
                        f.seek(0x04, io.SEEK_CUR)
                elif item_type == TsItemEnum.FUEL_PUMP:
                    f.seek(0x10, io.SEEK_CUR)
                    sub_item_uid_count = int.from_bytes(
                        f.read(4), "little", signed=True
                    )
                    f.seek(0x08 * sub_item_uid_count, io.SEEK_CUR)
                elif item_type == TsItemEnum.ROAD_SIDE_ITEM:
                    f.seek(0x20, io.SEEK_CUR)
                    board_count = int.from_bytes(f.read(1), "little", signed=True)
                    f.seek(0x18 * board_count, io.SEEK_CUR)
                    override_template_length = int.from_bytes(
                        f.read(4), "little", signed=True
                    )
                    if override_template_length > 0:
                        f.seek(0x04 + override_template_length, io.SEEK_CUR)
                    sign_override_count = int.from_bytes(
                        f.read(4), "little", signed=True
                    )
                    for _ in range(sign_override_count):
                        f.seek(0x0C, io.SEEK_CUR)
                        attribute_count = int.from_bytes(
                            f.read(4), "little", signed=True
                        )
                        for _ in range(attribute_count):
                            road_side_item_type = int.from_bytes(
                                f.read(2), "little", signed=True
                            )
                            f.seek(0x04, io.SEEK_CUR)
                            if road_side_item_type == 0x05:
                                text_length = int.from_bytes(
                                    f.read(4), "little", signed=True
                                )
                                f.seek(0x04 + text_length, io.SEEK_CUR)
                            elif road_side_item_type == 0x06:
                                f.seek(0x08, io.SEEK_CUR)
                            elif road_side_item_type == 0x01:
                                f.seek(0x01, io.SEEK_CUR)
                            else:
                                f.seek(0x04, io.SEEK_CUR)
                elif item_type == TsItemEnum.BUS_STOP:
                    # Note: mismatch from dariowouters ts-map
                    f.seek(0x08 + 0x08 + 0x08, io.SEEK_CUR)
                elif item_type == TsItemEnum.TRAFFIC_RULE:
                    tag_count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek(0x08 * tag_count, io.SEEK_CUR)
                    node_count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek(0x08 * node_count + 0x0C, io.SEEK_CUR)
                elif item_type == TsItemEnum.BEZIER_PATCH:
                    f.seek(0xF1, io.SEEK_CUR)
                    veg_sphere_count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek(0x14 * veg_sphere_count, io.SEEK_CUR)
                    self._parse_quad_info(f)
                elif item_type == TsItemEnum.TRAJECTORY_ITEM:
                    node_count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek((0x08 * node_count) + 0x08, io.SEEK_CUR)
                    route_rule_count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek(0x1C * route_rule_count, io.SEEK_CUR)
                    checkpoint_count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek(0x10 * checkpoint_count, io.SEEK_CUR)
                    tag_count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek(0x08 * tag_count, io.SEEK_CUR)
                elif item_type == TsItemEnum.MAP_AREA:
                    node_count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek((0x08 * node_count) + 0x04, io.SEEK_CUR)
                elif item_type == TsItemEnum.CURVE:
                    f.seek(0x6C, io.SEEK_CUR)
                    height_offset_count = int.from_bytes(
                        f.read(4), "little", signed=True
                    )
                    f.seek(0x04 * height_offset_count, io.SEEK_CUR)
                elif item_type == TsItemEnum.CUTSCENE:
                    tag_count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek((0x08 * tag_count) + 0x08, io.SEEK_CUR)
                    action_count = int.from_bytes(f.read(4), "little", signed=True)
                    for _ in range(action_count):
                        num_param_count = int.from_bytes(
                            f.read(4), "little", signed=True
                        )
                        f.seek(0x04 * num_param_count, io.SEEK_CUR)
                        string_param_count = int.from_bytes(
                            f.read(4), "little", signed=True
                        )
                        for _ in range(string_param_count):
                            text_length = int.from_bytes(
                                f.read(4), "little", signed=True
                            )
                            f.seek(0x04 + text_length, io.SEEK_CUR)
                        target_tag_count = int.from_bytes(
                            f.read(4), "little", signed=True
                        )
                        f.seek((0x08 * target_tag_count) + 0x08, io.SEEK_CUR)
                elif item_type == TsItemEnum.VISIBILITY_AREA:
                    f.seek(0x10, io.SEEK_CUR)
                    children_count = int.from_bytes(f.read(4), "little", signed=True)
                    f.seek(0x08 * children_count, io.SEEK_CUR)
                else:
                    raise ValueError(f"Unknown item type {item_type}")

            # Parse nodes.
            node_count = int.from_bytes(f.read(4), "little", signed=False)
            print(node_count)
        finally:
            f.close()

    def _parse_quad_info(self, f: BinaryIO):
        material_count = int.from_bytes(f.read(2), "little", signed=False)
        f.seek(0x0A * material_count, io.SEEK_CUR)
        color_count = int.from_bytes(f.read(2), "little", signed=False)
        f.seek(0x04 * color_count + 0x04, io.SEEK_CUR)
        storage_count = int.from_bytes(f.read(4), "little", signed=False)
        f.seek(0x04 * storage_count, io.SEEK_CUR)
        offset_count = int.from_bytes(f.read(4), "little", signed=False)
        f.seek(0x10 * offset_count, io.SEEK_CUR)
        normal_count = int.from_bytes(f.read(4), "little", signed=False)
        f.seek(0x10 * normal_count, io.SEEK_CUR)
