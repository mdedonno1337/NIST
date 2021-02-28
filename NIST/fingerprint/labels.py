#!/usr/bin/python
# -*- coding: UTF-8 -*-

FINGER_POSITION_CODE = {
    0: "unknown finger",
    1: "right thumb",
    2: "right index",
    3: "right middle",
    4: "right ring",
    5: "right little",
    6: "left thumb",
    7: "left index",
    8: "left middle",
    9: "left ring",
    10: "left little",
    11: "plain right thumb",
    12: "plain left thumb",
    13: "plain right four fingers",
    14: "plain left four fingers",
    15: "left and right thumbs",
    16: "right extra finger",
    17: "left extra finger",
    18: "unknown friction ridge",
    19: "EJI or tip"
}

PALM_POSITION_CODE = {
    20: "unknown palm",
    21: "right full palm",
    22: "right writer's palm",
    23: "left full palm",
    24: "left writer's palm",
    25: "right lower palm",
    26: "right upper palm",
    27: "left lower palm",
    28: "left upper palm",
    29: "right other",
    30: "left other",
    31: "right interdigital",
    32: "right thenar",
    33: "right hypothenar",
    34: "left interdigital",
    35: "left thenar",
    36: "left hypothenar",
    37: "right grasp",
    38: "left grasp",
    81: "right carpal delta area",
    82: "left carpal delta area",
    83: "right full palm, including writer's palm",
    84: "left full palm, including writer's palm",
    85: "right wrist bracelet",
    86: "left wrist bracelet"
}

SEGMENTS_POSITION_CODE = dict( FINGER_POSITION_CODE, **PALM_POSITION_CODE )

