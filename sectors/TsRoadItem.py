from dataclasses import dataclass
from struct import Struct

from utils import StructDataClass


@dataclass
class TsRoadItem(StructDataClass):
    struct = Struct("<192xQQf")

    # road_flags: int  # u4
    # road_look: int  # u8 -> token
    # # TODO: Determine if below 8 attributes are ids or flags
    # right_lanes_variant: int  # u8 -> token?
    # left_lanes_variant: int  # u8 -> token?
    # right_tmpl_variant: int  # u8 -> token?
    # left_tmpl_variant: int  # u8 -> token?
    # right_edge_right: int  # u8 -> token?
    # right_edge_left: int  # u8 -> token?
    # left_edge_right: int  # u8 -> token?
    # left_edge_left: int  # u8 -> token?
    # right_profile: int  # u8 -> token
    # right_profile_coef: float  # f4
    # left_profile: int  # u8 -> token
    # left_profile_coef: float  # f4
    # right_tmpl_look: bytes  # 8B, id -> token?
    # left_tmpl_look: bytes  # 8B, id -> token?
    # road_material: bytes  # 8B, id -> token?
    # right_railing_1: bytes  # 8B, id -> token?
    # right_railing_1_offset: int  # s2, 100x editor value (e.g. 2320 is 23.2 in editor)
    # left_railing_1: bytes  # 8B, id -> token?
    # left_railing_1_offset: int  # s2, 100x editor value  (e.g. 2320 is 23.2 in editor)
    # right_railing_2: bytes  # 8B, id -> token?
    # right_railing_2_offset: int  # s2, 100x editor value (e.g. 2320 is 23.2 in editor)
    # left_railing_2: bytes  # 8B, id -> token?
    # left_railing_2_offset: int  # s2, 100x editor value  (e.g. 2320 is 23.2 in editor)
    # right_railing_3: bytes  # 8B, id -> token?
    # right_railing_3_offset: int  # s2, 100x editor value (e.g. 2320 is 23.2 in editor)
    # left_railing_3: bytes  # 8B, id -> token?
    # left_railing_3_offset: int  # s2, 100x editor value  (e.g. 2320 is 23.2 in editor)
    # right_road_height: int  # s4, 100x editor value  (e.g. 2320 is 23.2 in editor)
    # left_road_height: int  # s4, 100x editor value  (e.g. 2320 is 23.2 in editor)
    node0_uid: int  # u8
    node1_uid: int  # u8
    length: float  # f4
