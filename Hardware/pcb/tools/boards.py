"""Board outlines, holes, keep-outs and placement (DEVICE mm: origin = device centre, +X right end,
+Y top edge, seen from the front; F.Cu faces the front wall on every board).
place: ref -> (x, y, KiCad rotation deg, side F/B). Rotation for JST SH / FH12: 0 = cable enters
from device -Y (bottom), 90 = from +X, 180 = from +Y, 270 = from -X. USB-C footprint: 180 = mates
towards +Y (top edge). Parts not listed are auto-placed next to the part they share signals with.
"""

# ------------------------------------------------------------------ fit-map keep-outs (rev G)
RF_ZONES = {
    "wifi_flexpifa": (-52.0, -34.8, -11.9, -23.8),
    "gps_patch": (-72.0, -35.75, -56.0, -22.75),
    "lte_flex_top_wall": (-14.0, 35.8, 28.0, 36.5),
}
LID_BOSSES = [(37.5, 33.45), (45.0, -33.45)]  # boss OD 5.6, keep 3 mm clear -> r 5.8


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


CARRIER = {
    "title": "Ansonia carrier rev A",
    "layers": 4, "thickness": 1.0,
    "comments": ["4-layer 1.0 mm: F.Cu sig | In1 GND | In2 PWR/sig | B.Cu sig+GND",
                 "Device coordinates: origin (100,100), +Y up in the device = -Y in KiCad"],
    "outline": [rect(-62.0, -17.5, 28.0, 30.0)],
    "holes": {"H1": (-41.0, 20.5), "H2": (-41.0, 4.0), "H3": (-9.0, 16.0), "H4": (9.0, -12.5)},
    "place": {
        "U2": (-23.5, 19.5, 0),        # ESP32-S3-WROOM-1U, U.FL at the top edge
        "U7": (5.5, 19.6, 0),          # SIM7080G
        "J15": (18.5, 27.0, 0),        # U.FL LTE (top edge, under the LTE flex)
        "J16": (-6.5, 27.0, 0),        # U.FL GNSS
        "J14": (20.5, -9.5, 0),        # nano-SIM, card enters from the bottom edge
        "J1": (24.6, 12.5, 90),        # link to the power board (right edge, cable +X)
        "U1": (17.0, 4.0, 0),          # TPS63001 3V3
        "U10": (-54.0, 6.0, 0),        # EWM104 Bluetooth, ANT pin 46 on its top edge
        "J17": (-50.0, 19.0, 0),       # U.FL BT
        "J8": (-56.0, 26.6, 180),      # front sensor board (cable up)
        "J7": (-46.5, 26.6, 180),      # touch strip
        "J12": (-38.35, 26.6, 180),    # buttons
        "J4": (-58.7, -7.0, 270),      # speaker L (left edge)
        "J9": (-58.7, -13.5, 270),     # mute LED
        "J6": (-50.0, -14.2, 0),       # haptic LRA (bottom edge)
        "J11": (-25.5, -13.4, 0),      # SSD1322 panel FPC (bottom edge)
        "J13": (-4.0, -13.4, 0),       # e-paper FPC (DNP)
        "U3": (-33.0, -2.0, 0), "U4": (-25.0, -2.0, 0), "U5": (-17.0, -2.0, 0),
        "U6": (-43.0, -7.0, 0),        # DRV2605L
        "U8": (-4.0, 6.0, 0),          # TXB0104
        "U9": (11.0, -5.0, 0),         # SIM ESD
        "U11": (-9.5, -4.0, 0),        # TPS61040 12 V
    },
    "near": {},
    "keepouts": [],
    "power_nets": ["GND", "+3V3", "VSYS"],
}

# power board: rectangular notch for the top lid boss, USB-C board cut-outs come from the footprints
_P_TOP = 33.0
POWER = {
    "title": "Ansonia power board rev A",
    "layers": 4, "thickness": 1.6,
    "comments": ["4-layer 1.6 mm, 2 oz outer copper", "Lid boss notch X<=43.3, Y>=27.65 (boss (37.5,33.45) r2.8 + 3)"],
    "outline": [[(30.0, -16.0), (66.5, -16.0), (66.5, -1.0), (73.0, -1.0), (73.0, _P_TOP),
                 (71.35, _P_TOP), (60.75, _P_TOP), (58.05, _P_TOP), (47.45, _P_TOP), (43.3, _P_TOP),
                 (43.3, 27.6), (30.0, 27.6)]],
    "outline_gaps": [((71.35, _P_TOP), (60.75, _P_TOP)), ((58.05, _P_TOP), (47.45, _P_TOP))],
    "holes": {},
    "place": {
        "J2": (52.75, _P_TOP - 5.65, 180),   # USB-C port 1 (in/out)
        "J3": (66.05, _P_TOP - 5.65, 180),   # USB-C port 2 (out)
        "U5": (52.75, 23.0, 0), "U6": (66.05, 23.0, 0),
        "U1": (49.5, 13.0, 0),              # PD IC placeholder (14 x 14 reserved)
        "U3": (58.9, 9.0, 0),               # TAS5805M
        "J7": (68.0, 9.0, 90),              # speaker R
        "U2": (54.0, -3.0, 0),              # TPS61088
        "L1": (53.0, -11.5, 0),             # 2.2 uH
        "J6": (63.4, -9.5, 90),             # Qi TX driver (cable +X)
        "J1": (33.3, 6.5, 270),             # link to carrier (cable -X)
        "J4": (35.0, -11.5, 270),           # cell (PH 2.0)
        "TP1": (43.3, -13.5, 0), "TP2": (43.3, -9.3, 0),
        "J5": (41.0, 23.8, 180),            # NTC lead
        "U4": (35.0, 22.0, 0),              # 3V3 LDO
    },
    "near": {},
    # Amphenol's land pattern puts the B-row pads 0.2 mm from the mid-mount cut-out (by design)
    "dru": "\n".join(["(rule usbc_cutout_edge",
                      "  (condition \"A.memberOfFootprint('J2') || A.memberOfFootprint('J3') || B.memberOfFootprint('J2') || B.memberOfFootprint('J3')\")",
                      "  (constraint edge_clearance (min 0.1mm)))", ""]),
    "no_parts": [{"pts": rect(43.0, 6.5, 55.8, 19.5), "side": "F"},
                 {"pts": rect(47.4, 30.6, 58.1, 33.0)}, {"pts": rect(60.7, 30.6, 71.4, 33.0)}],
    "keepouts": [],
    "power_nets": ["GND", "+3V3", "VSYS", "BAT_SW", "PVDD", "PVDD_AMP"],
}

FRONT_SENSOR = {
    "title": "Ansonia front sensor board rev A",
    "layers": 2, "thickness": 0.8,
    "comments": ["F.Cu faces the front wall (APDS-9960 window side); mic + connector on B.Cu",
                 "Mic port hole at device (-69.5, 31.25)"],
    "outline": [rect(-72.5, 23.5, -59.2, 35.3)],
    "holes": {},
    "place": {
        "U2": (-64.0, 31.25, 0, "F"),
        "U1": (-68.79, 31.25, 90, "B"),   # port hole lands on (-69.5, 31.25)
        "J1": (-65.85, 26.65, 180, "B"),
    },
    "power_nets": ["GND", "+3V3"],
    "gap": 0.2,
}

FRONT_TOUCH = {
    "title": "Ansonia touch strip rev A",
    "layers": 2, "thickness": 0.8,
    "comments": ["Sense pad on F.Cu (front), hatched GND ring on F.Cu, B.Cu clear under the pad"],
    "outline": [[(-56.0, 27.25), (-23.0, 27.25), (-23.0, 21.0), (-16.0, 21.0), (-16.0, 32.25), (-56.0, 32.25)]],
    "holes": {},
    "place": {"E1": (-37.0, 29.75, 0, "F"), "J1": (-19.5, 24.2, 0, "B"), "TP1": (-19.5, 29.75, 0, "B")},
    "no_default_pour": True,
    "pours": [{"net": "GND", "layer": "F.Cu", "pts": [(-56.0, 27.25), (-23.0, 27.25), (-23.0, 21.0), (-16.0, 21.0),
                                                      (-16.0, 32.25), (-56.0, 32.25)],
               "clearance": 1.0, "hatch": True},
              {"net": "GND", "layer": "B.Cu", "pts": rect(-23.0, 21.0, -16.0, 32.25), "clearance": 0.3}],
    "keepouts": [{"name": "touch_pad_back", "pts": rect(-54.5, 27.6, -19.5, 31.9), "layers": ["B.Cu"]}],
    "power_nets": ["GND"],
}

BOARDS = {"carrier": CARRIER, "power": POWER, "front_sensor": FRONT_SENSOR, "front_touch": FRONT_TOUCH}
