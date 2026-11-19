"""
heartsync - assembly: print-accurate enclosure + internals (Fusion 360 script, Python)

Use case
  * DOCKED: stands on its BOTTOM EDGE, charging through 4 pogo pads, held by 4 magnets.
  * IN USE: lies on its BACK (rubber feet), front up. A phone snaps onto the FRONT Qi2
    coil (transmit only) behind the gold front ring.

Builds (one run, rebuildable):
  * tray: FRONT wall with OLED window, Qi2 ring groove (+ ring_inlay), touch-strip groove,
    mic and light holes; TOP edge with USB-C (waterproof receptacle), 5 buttons (latching
    mute + PWR, VOL-, VOL+, PLAY) and the bracket slot; BOTTOM edge with 4 pogo pads and 4
    magnet pockets (1.6 mm skin); both ENDS as a 237-hole honeycomb, thinned to 1.2 mm in
    front of the speaker, with an ePTFE membrane; carrier bosses H3/H4 with press-fit pins;
    LRA fin; Wi-Fi hook clips; 4 corner bosses for M2 heat-set inserts
  * lid (3.0, bare PETG): 1.2 mm tongue (0.15 clearance, interrupted behind the speakers),
    continuous 1 mm gasket channel, screw pads and holes (no counterbore: low-head heads sit
    under the back ring), back-ring channel, engraved ID block (text from params.csv)
  * back ring: continuous TPU ring (own STL) over the screws, 1.5 proud
  * bracket: separate clip-in part that holds the carrier at H1/H2 (under the OLED)
  * real parts imported from cad/models (see REAL): LP1160100 cell (max envelope), Amphenol
    waterproof USB-C, CES-571423-28PMB speakers (ears cut) in printed cradles with foam,
    NHD-2.7 OLED module, Adafruit ICS-43434 mic and VEML7700 boards, PTS645 tactiles,
    PS-7054 latching mute, FlexPIFA, SGGP GNSS patch, Molex 212570 LTE flex, pogo pads, magnets
  * stand-ins still (no part chosen or no model): front Qi2 coil + NTC, vertical Qi2 TX board,
    PD board, SIM7080G board, LRA, touch strip, button strip, GNSS ground-plane board
  * the real carrier board, imported from cad/heartsync_carrier.step
  * checks: fit (interference), clearance rules, grille open area, stack; then grouping,
    side names and finishes, labels (hidden)

Other entry points (call on the open design after run()):
  print_checks()      thin walls (ray test) and overhangs for the print orientation
  export_all()        cad/exports/: tray/lid 3MF + STL, bracket STL, full assembly STEP
  make_net()          cad/net/heartsync_net.dxf + .pdf (TOP + BACK fabric, linked to the model)
  make_renders()      cad/renders/_png/*.png (converted to JPG outside Fusion)
  save_doc()          saves as "HeartSync v1"
  sync_from_fusion()  reads moved anchor parts and rewrites the POS block in this file

Dimensions come from cad/params.csv (source of truth); part positions from the POS block.
Axes: X = length, Y = width (+Y = TOP edge), Z = thickness (+Z = FRONT). Sizes in mm.
"""
import adsk.core
import adsk.fusion
import csv
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(globals().get("__file__", ".")))
CAD = os.path.normpath(os.path.join(HERE, ".."))

# ----------------------------------------------------------------------
# SETTINGS
# ----------------------------------------------------------------------
DOCK_SIDE = "bottom"       # "bottom" (stands on the dock) or "back"; only "bottom" is built
DISPLAY = "2.7"            # "2.7" or "3.12"
GROUP = True               # group bodies into components after the checks
CARRIER = True             # import the real carrier board STEP
DOC_NAME = "HeartSync v1"

# One place for the finishes (hex colours)
PALETTE = {
    "shell_fabric": "#CBBFAE",   # fabric on TOP edge and BACK
    "front_panel": "#1A1A1A",    # FRONT, whole face, matte black
    "petg_bare": "#1A1A1A",      # BOTTOM edge, ENDS and inside faces (the tray filament)
    "oled_glass": "#050505",
    "ring_inlay": "#C9A227",     # front ring = Qi2 marking, satin gold
    "buttons": "#CBBFAE",        # soft-touch, shell colour
    "mute_cap": "#E24B4A",
    "grille_mesh": "#2E2E2E",    # ePTFE membrane behind the honeycomb
    "usb_c": "#111111",          # rubber gasket around the port
    "feet": "#202020",
}

# ----------------------------------------------------------------------
# PARAMETERS (cad/params.csv)
# ----------------------------------------------------------------------
PARAMS, PARAM_STR, PARAM_NOTES = {}, {}, []


def _load_params():
    path = os.path.join(CAD, "params.csv")
    try:
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    PARAMS[r["name"]] = float(r["value"])
                except (TypeError, ValueError):
                    PARAM_STR[r["name"]] = r["value"]
    except OSError:
        PARAM_NOTES.append("params.csv not found: all defaults used")


def prm(name, default):
    v = PARAMS.get(name)
    if v is None:
        PARAM_NOTES.append("%s missing: default %g" % (name, default))
        return default
    if v == 0:
        PARAM_NOTES.append("%s is 0 (unknown): placeholder %g" % (name, default))
        return default
    return v


def prm_str(name, default):
    v = PARAM_STR.get(name)
    if v is None:
        PARAM_NOTES.append("%s missing: default %r" % (name, default))
        return default
    return v


_load_params()

LENGTH = prm("body_length", 152.0)
WIDTH = prm("body_width", 72.5)
THICKNESS = prm("body_thickness", 32.8)
WALL = prm("wall_thickness", 2.2)
LID = prm("lid_thickness", 3.0)
CORNER_R = prm("corner_radius", 6.0)
FABRIC = prm("fabric_allowance", 0.6)
SWELL = prm("battery_swell_gap", 1.2)
INSUL = prm("cell_insulator_top", 0.2)
CELL_PAD = prm("cell_pad", 1.0)
CELL_L = prm("battery_length", 101.0)       # LP1160100 MAX envelope (100 +-1 x 60 +-0.5 x 11 +-0.3)
CELL_W = prm("battery_width", 60.5)
CELL_T = prm("battery_thickness", 11.3)
PCB_T = prm("pcb_thickness", 1.6)

LIP_W = prm("lip_width", 1.2)
LIP_H = prm("lip_height", 1.5)
LIP_CLR = prm("lip_clearance", 0.15)
GASKET_W = prm("gasket_width", 1.0)
GASKET_D = prm("gasket_depth", 0.8)

INSERT_D = prm("insert_hole_d", 3.2)
INSERT_DEPTH = prm("insert_hole_depth", 4.0)
BOSS_INS_D = prm("insert_boss_d", 5.6)
SCREW_D = prm("screw_clearance_d", 2.4)
SCREW_PAD = prm("screw_pad_h", 1.5)
SCREW_X = prm("screw_x", 66.0)
SCREW_Y = prm("screw_y", 31.6)
HEAD_D = prm("screw_head_d", 3.8)
HEAD_H = prm("screw_head_h", 1.3)

# back: continuous TPU ring in a channel (replaces the feet), engraved ID block
BR_W = prm("back_ring_width", 4.0)
BR_INSET = prm("back_ring_inset", 2.5)
BR_R = prm("back_ring_corner_r", 6.0)
BR_CH = prm("back_ring_channel", 1.0)
BR_PROUD = prm("back_ring_proud", 1.5)
BR_POCKET_D = prm("back_ring_pocket_d", 4.4)
BR_POCKET_H = prm("back_ring_pocket_h", 1.5)
ID_L = prm("id_block_length", 26.0)
ID_W = prm("id_block_width", 11.0)
ID_DEPTH = prm("id_text_depth", 0.3)
ID_TEXT = [prm_str("id_text_1", "HeartSync"), prm_str("id_text_2", "1 / 2"),
           prm_str("id_text_3", "made with love 2026")]
CRADLE_T = prm("speaker_cradle_wall", 1.5)
SPK_FOAM = prm("speaker_foam", 1.0)

FIT_BTN = prm("fit_button", 0.2)
FIT_USB = prm("fit_usb_c", 0.3)
FIT_POGO = prm("fit_pogo", 0.1)
FIT_MAG = prm("fit_magnet", 0.1)
MIN_WALL = prm("min_wall", 1.2)

RING_OD = prm("ring_od", 56.0)
RING_W = prm("ring_width", 1.0)
RING_DEPTH = prm("ring_depth", 0.6)

HC_HEX = prm("honeycomb_hex", 1.8)
HC_PITCH = prm("honeycomb_pitch", 2.6)
HC_WALL = prm("honeycomb_wall", 1.2)
MEMBRANE = prm("membrane_thickness", 0.2)
SPK_GASKET = prm("speaker_gasket", 1.0)
SPK_L = prm("speaker_length", 57.5)          # along Y
SPK_H = prm("speaker_height", 23.0)          # along Z
SPK_D = prm("speaker_depth", 14.85)          # along X

POGO_D = prm("pogo_pad_d", 2.5)
MAG_D = prm("dock_magnet_diameter", 6.0)
MAG_T = prm("dock_magnet_thickness", 2.0)
GNSS = prm("gnss_patch", 12.0)
GNSS_T = prm("gnss_patch_t", 4.0)

# ----------------------------------------------------------------------
# POSITIONS (anchors; sync_from_fusion() rewrites this block)
# ----------------------------------------------------------------------
# --- POS BEGIN ---
POS = {
    "cell": (-4.00, 0.00),
    "coil": (43.00, 0.00),
    "oled": (-32.50, 4.00),
    "carrier": (-36.00, 30.00),
    "pd_board": (46.38, 20.25),
    "usb_c": (46.00, 0.00),
    "qi2_tx": (51.80, -17.00),
    "sim_board": (-42.25, -24.25),
    "wifi": (-24.95, -27.55),
    "gnss": (-60.00, -27.50),
    "lte": (-8.00, 19.60),
    "lra": (22.25, -29.00),
    "buttons": (-70.00, 0.00),
}
# --- POS END ---

# ----------------------------------------------------------------------
# DERIVED
# ----------------------------------------------------------------------
TRAY_H = THICKNESS - LID
INNER = TRAY_H - WALL                       # inside face of the front wall (27.6)
CAV_X = LENGTH / 2.0 - WALL                 # inside face of the ends (73.8)
CAV_Y = WIDTH / 2.0 - WALL                  # inside face of TOP/BOTTOM walls (34.05)

Z_CELL = CELL_PAD
CELL_TOP = Z_CELL + CELL_T
ABOVE = CELL_TOP + INSUL + SWELL            # board layer bottom (13.7 with the max cell)
PCB_TOP = ABOVE + PCB_T

CELL_CX, CELL_CY = POS["cell"]
CELL_X0 = CELL_CX - CELL_L / 2.0            # PCM folded inside the length, at the +X end
CELL_X1 = CELL_X0 + CELL_L

COIL_CX, COIL_CY = POS["coil"]
COIL_Z0 = INNER - 2.8                       # ferrite bottom (24.8)

if DISPLAY == "2.7":
    GLASS = (73.0, 41.9, 1.8)
    WIN = (63.0, 32.0)
else:
    GLASS = (89.2, 44.0, 6.0)
    WIN = (82.0, 22.0)
DCX, DCY = POS["oled"]
GLASS_Z = INNER - GLASS[2]
STRIP_C = (DCX, 28.0)

# carrier (KiCad board 70 x 45, origin top-left; local x right, y down)
CAR_X0, CAR_Y1 = POS["carrier"]
STEP_BOARD_X0, STEP_BOARD_Y1, STEP_BOARD_Z0 = 100.0, -100.0, 0.0
HOLES_LOCAL = {"H1": (3.0, 9.0), "H2": (3.0, 26.0), "H3": (45.5, 14.0), "H4": (48.5, 42.0)}
HOLES = {k: (CAR_X0 + x, CAR_Y1 - y) for k, (x, y) in HOLES_LOCAL.items()}
UFL = (CAR_X0 + 23.0, CAR_Y1 - 2.96)
BOSS_D, PIN_D = 5.0, 2.1

# speakers: face against the foam gasket on the membrane in the thinned end wall
# flat-top hexes (flats face +-Z: 1 mm bridge + 60 deg sides when printed front-down),
# 25 columns along Y (2.25 apart) of 9/10 holes along Z (2.6 pitch) = 237 holes
HC_COLS = 25
HC_COL_DY = HC_PITCH * math.sqrt(3) / 2.0
HC_R = HC_HEX / math.sqrt(3)                # hex circumradius
POCKET_Y = 29.2
POCKET_Z = (1.2, 26.8)                      # 1.2 mm rim ledge below the thinned pocket
HC_ZC = POCKET_Z[0] + 0.2 + (9 * HC_PITCH + HC_HEX) / 2.0   # lowest hole 0.2 above the ledge
WALL_THIN_X = LENGTH / 2.0 - HC_WALL        # 74.8: inner face of the thinned wall
SPK_FACE_X = WALL_THIN_X - MEMBRANE - SPK_GASKET     # 73.6
SPK_Z0 = 0.3                                # below the honeycomb centre: the GNSS patch clears it
SPK_CY = 0.0

# top edge. Amphenol 124019572112A, mid-mount: front rim 10.2 x 3.6, PCB top 0.75 below its
# centreline (wing underside in the STEP). The rim sits on the inside gasket; the plug enters
# through the wall opening.
USB = (10.2, 3.6, 7.86)                     # receptacle front rim W x H, depth
USB_X = POS["usb_c"][0]
USB_ZC = PCB_TOP + 0.75
BTN_ZC = 19.7                               # strip bottom 16.2, above the carrier top (16.0)
BTN_X0 = POS["buttons"][0]
BTN_GAP = 0.8
BUTTONS = []                                # (name, centre X, body width)
_x = BTN_X0
for _n, _w in (("mute", 7.0), ("pwr", 6.0), ("vol_dn", 6.0), ("vol_up", 6.0), ("play", 6.0)):
    BUTTONS.append((_n, _x + _w / 2.0, _w))
    _x += _w + BTN_GAP
BTN_X1 = _x - BTN_GAP
SLOT_X, SLOT_DEPTH = HOLES["H1"][0], 1.0    # bracket tab slot in the top wall

# bottom edge (dock)
POGO_X = (-12.0, -4.0, 4.0, 12.0)
POGO_Z = (TRAY_H - LID) / 2.0               # 13.8: middle of the 32 mm face (Z -2.2..29.8)
MAG_X = (-58.0, -32.0, 32.0, 58.0)
MAG_Z = 7.0
MAG_PAD_D, MAG_PAD_T = 9.0, 1.5

# corner screws / inserts (outside the cell and the speakers), heads under the back ring
SCREWS = [(sx * SCREW_X, sy * SCREW_Y) for sx in (-1, 1) for sy in (-1, 1)]

# Wi-Fi FlexPIFA 001-0014: FPC 40.12 x 11, foam end 2.5 thick; turned 180 deg about Z so the
# folded end (and the cable) is at -X and the cable runs +Y toward the carrier
WIFI_C, WIFI = POS["wifi"], (40.12, 11.0, 2.5)
WIFI_TAPE = 0.2
WIFI_Z0 = INNER - WIFI_TAPE - WIFI[2]
_wx, _wy = WIFI_C[0] - (40.685 - 20.06), WIFI_C[1] - (-5.0 - 5.5)     # cable stub end (model)
_wz = INNER - WIFI_TAPE - 0.565
WIFI_STUB = 16.0                            # cable inside the antenna STEP (solder to stub end)
WIFI_COAX = [(_wx, _wy, _wz), (_wx + 0.4, _wy + 0.6, _wz - 2.2), (_wx + 1.5, _wy + 0.4, 21.2),
             (_wx + 4.5, _wy + 2.5, 20.3), (-40.0, -5.0, 20.3), (-25.0, -1.0, 20.3),
             (-16.0, 9.0, 20.3), (-13.6, 21.0, 19.6), (UFL[0], UFL[1] - 1.5, PCB_TOP + 2.6),
             (UFL[0], UFL[1], PCB_TOP + 1.9)]

PHONE_X0 = COIL_CX - 38.5                   # upright 77 x 163 phone on the ring covers X >= 4.5

COL = {
    "shell": (26, 26, 26), "pcb": (20, 110, 60), "chip": (22, 22, 22), "metal": (190, 190, 195),
    "gold": (212, 175, 55), "copper": (200, 110, 50), "ferrite": (40, 40, 40),
    "magnet": (150, 150, 155), "cell": (70, 120, 200), "cell_seal": (170, 170, 175),
    "conn": (235, 232, 220), "passive": (200, 170, 120), "fpc": (205, 125, 30),
    "ceramic": (210, 190, 150), "black": (25, 25, 25), "white": (240, 240, 240),
    "mic_pcb": (90, 40, 140), "als_pcb": (30, 60, 160), "insul": (245, 235, 190),
    "speaker": (45, 45, 50), "flexpifa": (230, 140, 20), "foam": (60, 60, 60),
    "red": (200, 30, 30), "coax": (120, 120, 120),
}


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


for _k, _v in PALETTE.items():
    COL[_k] = hex_rgb(_v)

MM = 0.1
G = {"fails": [], "parts": [], "planes": {}, "apps": {}, "base_app": None, "imp": {}, "imp_box": {}}


def mm(v):
    return v * MM


def vi(v):
    return adsk.core.ValueInput.createByReal(mm(v))


def P(x, y, z=0.0):
    return adsk.core.Point3D.create(mm(x), mm(y), mm(z))


# ----------------------------------------------------------------------
# APPEARANCES
# ----------------------------------------------------------------------
def find_base_appearance(app):
    names = ["Plastic - Matte (Yellow)", "Paint - Enamel Glossy (Yellow)",
             "Plastic - Glossy (Yellow)", "Paint - Enamel Glossy (Red)"]
    libs = [app.materialLibraries.item(i) for i in range(app.materialLibraries.count)]
    libs = [l for l in libs if "ppearance" in l.name] or libs
    for lib in libs:
        for n in names:
            a = lib.appearances.itemByName(n)
            if a:
                return a
    for lib in libs:
        for i in range(min(lib.appearances.count, 400)):
            a = lib.appearances.item(i)
            if color_prop(a):
                return a
    return None


def color_prop(a):
    props = a.appearanceProperties
    p = props.itemById("opaque_albedo")
    if p:
        return adsk.core.ColorProperty.cast(p)
    for i in range(props.count):
        c = adsk.core.ColorProperty.cast(props.item(i))
        if c:
            return c
    return None


def appearance(key):
    if key in G["apps"]:
        return G["apps"][key]
    a = None
    try:
        if G["base_app"]:
            design = G["design"]
            name = "hs_" + key
            a = design.appearances.itemByName(name)
            if not a:
                a = design.appearances.addByCopy(G["base_app"], name)
            r, g, b = COL[key]
            color_prop(a).value = adsk.core.Color.create(r, g, b, 255)
    except Exception:
        a = None
    G["apps"][key] = a
    return a


def paint(body, key):
    if not key:
        return
    a = appearance(key)
    if a:
        try:
            body.appearance = a
        except Exception:
            pass


# ----------------------------------------------------------------------
# GEOMETRY HELPERS
# ----------------------------------------------------------------------
def plane_at(z):
    comp = G["comp"]
    if abs(z) < 1e-6:
        return comp.xYConstructionPlane
    key = ("z", round(z, 3))
    if key not in G["planes"]:
        pi = comp.constructionPlanes.createInput()
        pi.setByOffset(comp.xYConstructionPlane, vi(z))
        pl = comp.constructionPlanes.add(pi)
        pl.isLightBulbOn = False
        G["planes"][key] = pl
    return G["planes"][key]


def side_plane(axis, val):
    """Construction plane x = val (axis 'x') or y = val (axis 'y'), model coordinates."""
    comp = G["comp"]
    key = (axis, round(val, 3))
    if key in G["planes"]:
        return G["planes"][key]
    base = comp.yZConstructionPlane if axis == "x" else comp.xZConstructionPlane
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(base, vi(val))
    pl = comp.constructionPlanes.add(pi)
    o = pl.geometry.origin
    c = o.x if axis == "x" else o.y
    if abs(val) > 1e-6 and c * val < 0:
        pl.deleteMe()
        pi = comp.constructionPlanes.createInput()
        pi.setByOffset(base, vi(-val))
        pl = comp.constructionPlanes.add(pi)
    pl.isLightBulbOn = False
    G["planes"][key] = pl
    return pl


def rect(sk, cx, cy, w, h):
    sk.sketchCurves.sketchLines.addCenterPointRectangle(P(cx, cy), P(cx + w / 2.0, cy + h / 2.0))


def rounded_rect(sk, cx, cy, w, h, r):
    """Closed rounded rectangle in an XY-offset sketch (model X/Y)."""
    lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    x0, x1, y0, y1 = cx - w / 2.0, cx + w / 2.0, cy - h / 2.0, cy + h / 2.0
    r = min(r, w / 2.0, h / 2.0)
    corners = ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180))
    seg = []
    for (ax, ay, sa) in corners:
        a0, a1 = math.radians(sa), math.radians(sa + 90)
        seg.append(((ax, ay), (ax + r * math.cos(a0), ay + r * math.sin(a0)),
                    (ax + r * math.cos(a1), ay + r * math.sin(a1))))
    for i, (c, s, e) in enumerate(seg):
        arcs.addByCenterStartSweep(P(*c), P(*s), math.radians(90))
        n = seg[(i + 1) % 4]
        if (abs(e[0] - n[1][0]) + abs(e[1] - n[1][1])) > 1e-6:
            lines.addByTwoPoints(P(*e), P(*n[1]))


def all_profiles(sk):
    c = adsk.core.ObjectCollection.create()
    for p in sk.profiles:
        c.add(p)
    return c


def smallest_profile(sk):
    best = None
    for p in sk.profiles:
        a = p.areaProperties().area
        if best is None or a < best[0]:
            best = (a, p)
    return best[1]


def new_bodies(profiles, t, name, color, register=True):
    comp = G["comp"]
    ei = comp.features.extrudeFeatures.createInput(
        profiles, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ei.setDistanceExtent(False, vi(t))
    f = comp.features.extrudeFeatures.add(ei)
    f.name = name
    out = []
    for i in range(f.bodies.count):
        b = f.bodies.item(i)
        b.name = name if f.bodies.count == 1 else "%s_%d" % (name, i + 1)
        paint(b, color)
        if register:
            G["parts"].append(b)
        out.append(b)
    return out


def block(name, color, cx, cy, z0, w, h, t, register=True):
    try:
        sk = G["comp"].sketches.add(plane_at(z0))
        rect(sk, cx, cy, w, h)
        sk.isVisible = False
        return new_bodies(sk.profiles.item(0), t, name, color, register)
    except Exception:
        G["fails"].append(name)
        return []


def cyl(name, color, cx, cy, z0, dia, t, inner=0.0, register=True):
    try:
        sk = G["comp"].sketches.add(plane_at(z0))
        circ = sk.sketchCurves.sketchCircles
        circ.addByCenterRadius(P(cx, cy), mm(dia / 2.0))
        if inner > 0:
            circ.addByCenterRadius(P(cx, cy), mm(inner / 2.0))
            prof = smallest_profile(sk)
        else:
            prof = sk.profiles.item(0)
        sk.isVisible = False
        return new_bodies(prof, t, name, color, register)
    except Exception:
        G["fails"].append(name)
        return []


def grid(name, color, z0, rects, t):
    try:
        sk = G["comp"].sketches.add(plane_at(z0))
        for (cx, cy, w, h) in rects:
            rect(sk, cx, cy, w, h)
        sk.isVisible = False
        return new_bodies(all_profiles(sk), t, name, color)
    except Exception:
        G["fails"].append(name)
        return []


def _side_extrude(axis, mid, shapes, length, name, color, register=True, op=None, participants=None):
    """Extrude closed shapes drawn on the plane axis = mid, symmetric, total `length`.
    shapes: ("rect", (a0, b0), (a1, b1)) | ("circle", (a, b), dia) | ("poly", [(a, b), ...])
    with (a, b) = (y, z) for axis 'x' and (x, z) for axis 'y'."""
    comp = G["comp"]
    pl = side_plane(axis, mid)
    sk = comp.sketches.add(pl)
    sk.isComputeDeferred = True

    def mp(a, b):
        p = P(mid, a, b) if axis == "x" else P(a, mid, b)
        q = sk.modelToSketchSpace(p)
        return adsk.core.Point3D.create(q.x, q.y, 0)

    lines = sk.sketchCurves.sketchLines
    for s in shapes:
        if s[0] == "rect":
            lines.addTwoPointRectangle(mp(*s[1]), mp(*s[2]))
        elif s[0] == "circle":
            sk.sketchCurves.sketchCircles.addByCenterRadius(mp(*s[1]), mm(s[2] / 2.0))
        else:
            pts = [mp(a, b) for (a, b) in s[1]]
            first = lines.addByTwoPoints(pts[0], pts[1])
            prev = first
            for p in pts[2:]:
                prev = lines.addByTwoPoints(prev.endSketchPoint, p)
            lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    sk.isComputeDeferred = False
    sk.isVisible = False
    new = op is None
    ei = comp.features.extrudeFeatures.createInput(
        all_profiles(sk), adsk.fusion.FeatureOperations.NewBodyFeatureOperation if new else op)
    ei.setSymmetricExtent(vi(length), True)
    if participants:
        ei.participantBodies = participants
    f = comp.features.extrudeFeatures.add(ei)
    f.name = name
    out = []
    if new:
        for i in range(f.bodies.count):
            b = f.bodies.item(i)
            b.name = name if f.bodies.count == 1 else "%s_%d" % (name, i + 1)
            paint(b, color)
            if register:
                G["parts"].append(b)
            out.append(b)
    return out


def side_body(name, color, axis, mid, shapes, length, register=True):
    try:
        return _side_extrude(axis, mid, shapes, length, name, color, register)
    except Exception:
        G["fails"].append(name)
        return []


def side_cut(name, body, axis, mid, shapes, length):
    try:
        _side_extrude(axis, mid, shapes, length, name, None,
                      op=adsk.fusion.FeatureOperations.CutFeatureOperation, participants=[body])
    except Exception:
        G["fails"].append(name)


def tool_block(cx, cy, z0, w, h, t):
    return block("tool", None, cx, cy, z0, w, h, t, register=False)[0]


def tool_cyl(cx, cy, z0, dia, t):
    return cyl("tool", None, cx, cy, z0, dia, t, register=False)[0]


def combine(target, tools, op, name, keep=False):
    comp = G["comp"]
    coll = adsk.core.ObjectCollection.create()
    for t in tools:
        coll.add(t)
    ci = comp.features.combineFeatures.createInput(target, coll)
    ci.operation = op
    ci.isKeepToolBodies = keep
    f = comp.features.combineFeatures.add(ci)
    f.name = name
    return f


def join(target, tools, name):
    return combine(target, tools, adsk.fusion.FeatureOperations.JoinFeatureOperation, name)


def cut(target, tools, name):
    return combine(target, tools, adsk.fusion.FeatureOperations.CutFeatureOperation, name)


def fillet_vertical_edges(body, r):
    comp = G["comp"]
    edges = adsk.core.ObjectCollection.create()
    for e in body.edges:
        g = e.geometry
        if isinstance(g, adsk.core.Line3D):
            d = g.startPoint.vectorTo(g.endPoint)
            d.normalize()
            if abs(d.z) > 0.99:
                edges.add(e)
    if edges.count:
        fi = comp.features.filletFeatures.createInput()
        fi.addConstantRadiusEdgeSet(edges, vi(r), True)
        comp.features.filletFeatures.add(fi)


def chamfer_edges_at_z(body, z, d):
    comp = G["comp"]
    edges = adsk.core.ObjectCollection.create()
    for e in body.edges:
        bb = e.boundingBox
        if abs(bb.minPoint.z - mm(z)) < 1e-4 and abs(bb.maxPoint.z - mm(z)) < 1e-4:
            edges.add(e)
    if edges.count:
        ci = comp.features.chamferFeatures.createInput2()
        ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, vi(d), True)
        comp.features.chamferFeatures.add(ci)


def cut_z(sk, profiles, depth, body, name, up=False):
    comp = G["comp"]
    ei = comp.features.extrudeFeatures.createInput(
        profiles, adsk.fusion.FeatureOperations.CutFeatureOperation)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(vi(depth)),
                        adsk.fusion.ExtentDirections.PositiveExtentDirection if up
                        else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    ei.participantBodies = [body]
    comp.features.extrudeFeatures.add(ei).name = name


def hex_points(yc, zc, r):
    """Flat-top hexagon (flats face +-Z, points along Y) in the (y, z) plane."""
    return [(yc + r * math.cos(math.radians(60 * k)), zc + r * math.sin(math.radians(60 * k)))
            for k in range(6)]


def honeycomb_centres():
    out = []
    for j in range(HC_COLS):
        y = SPK_CY + (j - (HC_COLS - 1) / 2.0) * HC_COL_DY
        n = 9 if j % 2 == 0 else 10
        for i in range(n):
            out.append((y, HC_ZC + (i - (n - 1) / 2.0) * HC_PITCH))
    return out


# ----------------------------------------------------------------------
# SHELL: TRAY
# ----------------------------------------------------------------------
def build_tray():
    comp = G["comp"]
    sk = comp.sketches.add(comp.xYConstructionPlane)
    rect(sk, 0, 0, LENGTH, WIDTH)
    sk.isVisible = False
    ei = comp.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ei.setDistanceExtent(False, vi(TRAY_H))
    f = comp.features.extrudeFeatures.add(ei)
    f.name = "SHELL_tray_block"
    tray = f.bodies.item(0)
    tray.name = "shell_tray"
    fillet_vertical_edges(tray, CORNER_R)
    back = min((fc for fc in tray.faces if isinstance(fc.geometry, adsk.core.Plane)
                and abs(fc.geometry.normal.z) > 0.99), key=lambda fc: fc.centroid.z)
    faces = adsk.core.ObjectCollection.create()
    faces.add(back)
    si = comp.features.shellFeatures.createInput(faces)
    si.insideThickness = vi(WALL)
    comp.features.shellFeatures.add(si).name = "SHELL_tray_shell"

    # FRONT: window, touch-strip groove, Qi2 ring groove, mic and light holes
    def fcut(name, fn, depth, smallest=False):
        try:
            s = comp.sketches.add(plane_at(TRAY_H))
            s.isVisible = False
            fn(s)
            cut_z(s, smallest_profile(s) if smallest else all_profiles(s), depth, tray, name)
        except Exception:
            G["fails"].append(name)

    fcut("FRONT_window", lambda s: rect(s, DCX, DCY, WIN[0], WIN[1]), WALL * 1.5)
    fcut("FRONT_touch_groove", lambda s: rect(s, STRIP_C[0], STRIP_C[1], 40.0, 5.0), 0.6)

    def ring(s):
        c = s.sketchCurves.sketchCircles
        c.addByCenterRadius(P(COIL_CX, COIL_CY), mm(RING_OD / 2.0))
        c.addByCenterRadius(P(COIL_CX, COIL_CY), mm(RING_OD / 2.0 - RING_W))
    fcut("FRONT_qi2_ring_groove", ring, RING_DEPTH, smallest=True)
    fcut("FRONT_mic_hole", lambda s: s.sketchCurves.sketchCircles.addByCenterRadius(P(-66.5, 29.5), mm(0.5)), WALL * 1.5)
    fcut("FRONT_light_hole", lambda s: s.sketchCurves.sketchCircles.addByCenterRadius(P(-58.5, 29.5), mm(1.0)), WALL * 1.5)

    # TOP edge: USB-C, buttons, bracket slot
    ty = WIDTH / 2.0
    uw, uh = USB[0] + 2 * FIT_USB, USB[1] + 2 * FIT_USB
    side_cut("TOP_EDGE_usb_c", tray, "y", ty,
             [("rect", (USB_X - uw / 2, USB_ZC - uh / 2), (USB_X + uw / 2, USB_ZC + uh / 2))], 6.0)
    holes = []
    for name, x, w in BUTTONS:
        h = (6.4 if name == "mute" else 4.0) + 2 * FIT_BTN
        holes.append(("rect", (x - h / 2, BTN_ZC - h / 2), (x + h / 2, BTN_ZC + h / 2)))
    side_cut("TOP_EDGE_buttons", tray, "y", ty, holes, 6.0)
    side_cut("TOP_EDGE_bracket_slot", tray, "y", CAV_Y + SLOT_DEPTH / 2.0,
             [("rect", (SLOT_X - 0.6, 19.3), (SLOT_X + 2.6, 23.2))], SLOT_DEPTH)   # off-centre: 3 mm to PLAY

    # BOTTOM edge: pogo pad holes, magnet pads + pockets (1.6 mm skin)
    side_cut("BOTTOM_EDGE_pogo_holes", tray, "y", -WIDTH / 2.0,
             [("circle", (x, POGO_Z), POGO_D + 2 * FIT_POGO) for x in POGO_X], 6.0)
    try:
        pads = side_body("tool", None, "y", -CAV_Y + (MAG_PAD_T - 0.5) / 2.0,
                         [("circle", (x, MAG_Z), MAG_PAD_D) for x in MAG_X], MAG_PAD_T + 0.5, register=False)
        join(tray, pads, "BOTTOM_EDGE_magnet_pads")
        pt = MAG_T + FIT_MAG
        side_cut("BOTTOM_EDGE_magnet_pockets", tray, "y", -CAV_Y + MAG_PAD_T - pt / 2.0,
                 [("circle", (x, MAG_Z), MAG_D + 2 * FIT_MAG) for x in MAG_X], pt)
    except Exception:
        G["fails"].append("BOTTOM_EDGE_magnets")

    # ENDS: thinned pocket + honeycomb, all holes through
    hc = honeycomb_centres()
    G["honeycomb_n"] = len(hc)
    for side, name in ((1, "RIGHT_END"), (-1, "LEFT_END")):
        side_cut(name + "_thin_pocket", tray, "x", side * (CAV_X + (WALL - HC_WALL) / 2.0),
                 [("rect", (-POCKET_Y, POCKET_Z[0]), (POCKET_Y, POCKET_Z[1]))], WALL - HC_WALL)
        side_cut(name + "_honeycomb", tray, "x", side * LENGTH / 2.0,
                 [("poly", hex_points(y, z, HC_R)) for (y, z) in hc], 4.0)

    # carrier bosses H3/H4 from the front wall + press-fit pins (flush with the board underside)
    try:
        tools = []
        for h in ("H3", "H4"):
            x, y = HOLES[h]
            tools.append(tool_cyl(x, y, PCB_TOP, BOSS_D, INNER - PCB_TOP + 0.5))
            tools.append(tool_cyl(x, y, ABOVE, PIN_D, PCB_T))
        join(tray, tools, "INSIDE_carrier_bosses_H3_H4")
    except Exception:
        G["fails"].append("carrier_bosses")

    # LRA fin: grows from the front wall and the bottom wall (no supports front-down)
    try:
        lx, ly = POS["lra"]
        y0, y1 = -CAV_Y - 0.5, ly + 5.0
        fin = tool_block(lx + 3.5 / 2.0 + 0.75, (y0 + y1) / 2.0, ABOVE + 0.1, 1.5, y1 - y0,
                         INNER - ABOVE - 0.1 + 0.5)
        join(tray, [fin], "INSIDE_lra_fin")
    except Exception:
        G["fails"].append("lra_fin")

    # Wi-Fi FlexPIFA: no clips. The real part is a 0.15 mm FPC with a foam end, held by its
    # 3M adhesive (datasheet); a hook would sit on the cable at the folded end.

    # corner bosses for M2 heat-set inserts, 45 deg chamfer toward the bed (front-down print)
    try:
        z0, z1 = SCREW_PAD, SCREW_PAD + 6.0
        tools = []
        for (x, y) in SCREWS:
            b = tool_cyl(x, y, z0, BOSS_INS_D, z1 - z0)
            chamfer_edges_at_z(b, z1, 2.0)
            tools.append(b)
        join(tray, tools, "INSIDE_insert_bosses")
        cut(tray, [tool_cyl(x, y, z0 - 0.1, INSERT_D, INSERT_DEPTH + 0.1) for (x, y) in SCREWS],
            "INSIDE_insert_holes")
    except Exception:
        G["fails"].append("insert_bosses")

    paint(tray, "petg_bare")
    return tray


# ----------------------------------------------------------------------
# SHELL: LID
# ----------------------------------------------------------------------
def build_lid():
    comp = G["comp"]
    sk = comp.sketches.add(comp.xYConstructionPlane)
    rect(sk, 0, 0, LENGTH, WIDTH)
    sk.isVisible = False
    ei = comp.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(vi(LID)),
                        adsk.fusion.ExtentDirections.NegativeExtentDirection)
    f = comp.features.extrudeFeatures.add(ei)
    f.name = "SHELL_lid_block"
    lid = f.bodies.item(0)
    lid.name = "shell_lid"
    fillet_vertical_edges(lid, CORNER_R)

    # tongue: 1.2 wide, inside the tray wall with 0.15 clearance, interrupted behind the speakers
    try:
        d0 = WALL + LIP_CLR
        s = comp.sketches.add(comp.xYConstructionPlane)
        rounded_rect(s, 0, 0, LENGTH - 2 * d0, WIDTH - 2 * d0, max(CORNER_R - d0, 0.5))
        rounded_rect(s, 0, 0, LENGTH - 2 * (d0 + LIP_W), WIDTH - 2 * (d0 + LIP_W),
                     max(CORNER_R - d0 - LIP_W, 0.5))
        s.isVisible = False
        tongue = new_bodies(smallest_profile(s), LIP_H, "lid_tongue", None, register=False)[0]
        cut(tongue, [tool_block(sx * (LENGTH / 2.0 - 3.0), 0, -0.1, 6.0, 2 * (POCKET_Y + 0.8), LIP_H + 0.2)
                     for sx in (-1, 1)], "BACK_lid_tongue_gaps")
        # the gaps split the tongue in two (top and bottom halves): join both to the lid
        halves = [b for b in comp.bRepBodies if b.name.startswith("lid_tongue")]
        join(lid, halves, "BACK_lid_tongue")
    except Exception:
        G["fails"].append("lid_tongue")

    # gasket channel under the tray wall: 1.2 land outside, 1.0 channel, 0.8 deep (continuous)
    try:
        s = comp.sketches.add(comp.xYConstructionPlane)
        a, b = WALL - GASKET_W, WALL
        rounded_rect(s, 0, 0, LENGTH - 2 * a, WIDTH - 2 * a, CORNER_R - a)
        rounded_rect(s, 0, 0, LENGTH - 2 * b, WIDTH - 2 * b, CORNER_R - b)
        s.isVisible = False
        cut_z(s, smallest_profile(s), GASKET_D, lid, "BACK_lid_gasket_channel")
    except Exception:
        G["fails"].append("lid_gasket_channel")

    # screw pads (D-shaped: clipped at the tray inner face and at the speaker) and clearance
    # holes. No counterbore: the low-head screw heads sit on the floor of the back-ring channel
    # and the ring covers them, so nothing thins the lid next to the gasket channel.
    try:
        pads = []
        for (x, y) in SCREWS:
            p = tool_cyl(x, y, 0.0, BOSS_INS_D, SCREW_PAD)
            sy = 1 if y > 0 else -1
            cut(p, [tool_block(x, sy * (CAV_Y - 0.05 + 2.0), -0.1, 8.0, 4.0, SCREW_PAD + 0.2),
                    tool_block(x, sy * (SPK_L / 2.0 + 0.25 - 2.0), -0.1, 8.0, 4.0, SCREW_PAD + 0.2)],
                "BACK_screw_pad_clip")
            pads.append(p)
        join(lid, pads, "BACK_screw_pads")
        cut(lid, [tool_cyl(x, y, -LID - 0.1, SCREW_D, LID + SCREW_PAD + 0.2) for (x, y) in SCREWS],
            "BACK_screw_holes")
    except Exception:
        G["fails"].append("lid_screws")

    # back-ring channel: continuous, BR_W wide, outer edge BR_INSET in from the outline
    try:
        s = comp.sketches.add(plane_at(-LID))
        rounded_rect(s, 0, 0, LENGTH - 2 * BR_INSET, WIDTH - 2 * BR_INSET, BR_R)
        rounded_rect(s, 0, 0, LENGTH - 2 * (BR_INSET + BR_W), WIDTH - 2 * (BR_INSET + BR_W),
                     max(BR_R - BR_W, 0.5))
        s.isVisible = False
        cut_z(s, smallest_profile(s), BR_CH, lid, "BACK_ring_channel", up=True)
    except Exception:
        G["fails"].append("ring_channel")

    # engraved ID block, bottom-right seen from behind (model -X, -Y), inside the ring
    try:
        engrave_id(lid)
    except Exception:
        G["fails"].append("id_block")

    paint(lid, "petg_bare")
    return lid


ID_C = (-LENGTH / 2.0 + BR_INSET + BR_W + 1.5 + ID_L / 2.0, -WIDTH / 2.0 + BR_INSET + BR_W + 1.5 + ID_W / 2.0)


def engrave_id(lid):
    """Frame (0.4 wide) and three text lines, ID_DEPTH deep into the back face, mirrored so
    they read from behind. Text comes from params.csv (id_text_1..3)."""
    comp = G["comp"]
    cx, cy = ID_C
    s = comp.sketches.add(plane_at(-LID))
    rect(s, cx, cy, ID_L, ID_W)
    rect(s, cx, cy, ID_L - 0.8, ID_W - 0.8)
    s.isVisible = False
    cut_z(s, smallest_profile(s), ID_DEPTH, lid, "BACK_id_frame", up=True)
    rows = ((ID_TEXT[0], 3.0, cy + 2.9), (ID_TEXT[1], 2.4, cy - 0.1), (ID_TEXT[2], 1.9, cy - 3.0))
    for k, (text, h, ry) in enumerate(rows):
        ts = comp.sketches.add(plane_at(-LID))
        ti = ts.sketchTexts.createInput2(text, mm(h))
        ti.setAsMultiLine(P(cx - ID_L / 2 + 0.8, ry - h / 2 - 0.2), P(cx + ID_L / 2 - 0.8, ry + h / 2 + 0.2),
                          adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                          adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
        txt = ts.sketchTexts.add(ti)
        try:
            txt.isHorizontalFlip = True      # reads correctly from the back
        except Exception:
            pass
        ts.isVisible = False
        ei = comp.features.extrudeFeatures.createInput(txt, adsk.fusion.FeatureOperations.CutFeatureOperation)
        ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(vi(ID_DEPTH)),
                            adsk.fusion.ExtentDirections.PositiveExtentDirection)
        ei.participantBodies = [lid]
        comp.features.extrudeFeatures.add(ei).name = "BACK_id_text_%d" % (k + 1)


def build_trim():
    comp = G["comp"]
    # front ring inlay fills the groove exactly
    cyl("ring_inlay", "ring_inlay", COIL_CX, COIL_CY, TRAY_H - RING_DEPTH, RING_OD, RING_DEPTH,
        inner=RING_OD - 2 * RING_W)
    # continuous TPU back ring (own STL): sits in the lid channel, BR_PROUD above the back face,
    # pockets in its underside over the low-head screw heads
    try:
        z0 = -LID + BR_CH - (BR_CH + BR_PROUD)
        s = comp.sketches.add(plane_at(z0))
        rounded_rect(s, 0, 0, LENGTH - 2 * BR_INSET - 0.2, WIDTH - 2 * BR_INSET - 0.2, BR_R - 0.1)
        rounded_rect(s, 0, 0, LENGTH - 2 * (BR_INSET + BR_W) + 0.2, WIDTH - 2 * (BR_INSET + BR_W) + 0.2,
                     max(BR_R - BR_W + 0.1, 0.5))
        s.isVisible = False
        ring = new_bodies(smallest_profile(s), BR_CH + BR_PROUD, "back_ring", "feet")[0]
        cut(ring, [tool_cyl(x, y, -LID + BR_CH - BR_POCKET_H, BR_POCKET_D, BR_POCKET_H + 0.1) for (x, y) in SCREWS],
            "BACK_ring_head_pockets")
    except Exception:
        G["fails"].append("back_ring")
    # M2 low-head screw heads on the channel floor (for the fit check)
    for k, (x, y) in enumerate(SCREWS):
        cyl("screw_head_%d" % (k + 1), "metal", x, y, -LID + BR_CH - HEAD_H, HEAD_D, HEAD_H)
    # USB-C rubber gasket on the inside of the top wall; the receptacle rim presses on it
    try:
        g = side_body("usb_c_gasket", "usb_c", "y", CAV_Y - 0.4,
                      [("rect", (USB_X - USB[0] / 2 - 2, USB_ZC - USB[1] / 2 - 2),
                        (USB_X + USB[0] / 2 + 2, USB_ZC + USB[1] / 2 + 2))], 0.8)
        hole = side_body("tool", None, "y", CAV_Y - 0.4,
                         [("rect", (USB_X - USB[0] / 2 + 0.4, USB_ZC - USB[1] / 2 + 0.4),
                           (USB_X + USB[0] / 2 - 0.4, USB_ZC + USB[1] / 2 - 0.4))], 1.0, register=False)
        cut(g[0], hole, "TOP_EDGE_usb_gasket_hole")
    except Exception:
        G["fails"].append("usb_c_gasket")


def build_bracket():
    """Clip-in bracket for H1/H2 (printed flat, own STL): bar under the OLED, drop bosses with
    press-fit pins, a web to the front wall beside the touch strip and a tab into the top wall."""
    x = HOLES["H1"][0]
    y_lo, y_hi = HOLES["H2"][1] - BOSS_D / 2.0, CAV_Y - 0.55
    try:
        bar = block("carrier_bracket", "petg_bare", x, (y_lo + y_hi) / 2.0, 19.5, 5.0, y_hi - y_lo, 3.5)[0]
        tab_y1 = CAV_Y + SLOT_DEPTH - 0.1
        tools = [tool_block(x, (30.7 + y_hi) / 2.0, 23.0, 5.0, y_hi - 30.7, INNER - 0.2 - 23.0),
                 tool_block(x + 1.0, (y_hi - 0.5 + tab_y1) / 2.0, 19.5, 2.8, tab_y1 - (y_hi - 0.5), 3.5)]
        for h in ("H1", "H2"):
            hx, hy = HOLES[h]
            tools.append(tool_cyl(hx, hy, PCB_TOP, BOSS_D, 19.5 - PCB_TOP + 0.5))
            tools.append(tool_cyl(hx, hy, ABOVE, PIN_D, PCB_T + 0.5))
        join(bar, tools, "BRACKET_join")
    except Exception:
        G["fails"].append("carrier_bracket")


# ----------------------------------------------------------------------
# PARTS
# ----------------------------------------------------------------------
def build_coil():
    """Front Qi2 TX coil: windings + magnet ring against the front wall, ferrite behind."""
    for k in range(6):
        ri = 10.0 + 2.2 * k
        cyl("qi2_winding_%d" % (k + 1), "copper", COIL_CX, COIL_CY, INNER - 1.8, 2 * (ri + 1.6), 1.8, 2 * ri)
    cyl("qi2_magnet_ring", "magnet", COIL_CX, COIL_CY, INNER - 2.0, 55.0, 2.0, 47.0)
    cyl("qi2_ferrite", "ferrite", COIL_CX, COIL_CY, COIL_Z0, 56.0, 0.8)
    cyl("qi2_ntc", "black", COIL_CX, COIL_CY, INNER - 1.0, 2.0, 1.0)


def build_power():
    block("cell_pad", "foam", CELL_CX, CELL_CY, 0.0, CELL_L, CELL_W, CELL_PAD)
    # LiPol LP1160100 at its MAX envelope (101 x 60.5 x 11.3), PCM end and leads at +X
    place_step("cell", "cell", ("-X", "-Y", "Z"), (0.0, 0.0, 0.0), (CELL_X1, CELL_CY, Z_CELL))
    block("cell_insulator", "insul", CELL_CX, CELL_CY, CELL_TOP, CELL_L, CELL_W, INSUL)
    for b in block("keepout_swell_gap", "red", CELL_CX, CELL_CY, CELL_TOP + INSUL, CELL_L, CELL_W, SWELL):
        b.isLightBulbOn = False

    # PD board (IP5328P) top-right, USB-C on the TOP edge; hot parts off the cell (X > 46)
    px, py = POS["pd_board"]
    block("pd_board", "pcb", px, py, ABOVE, 23.75, 24.5, PCB_T)
    # Amphenol 124019572112A: mouth (+X in the file) toward the TOP wall, rim on the gasket
    place_step("usb_c", "usb_c", ("Y", "-X", "Z"), (-2.75, 13.0, 0.0), (USB_X, CAV_Y - 0.8, USB_ZC))
    block("pd_ip5328p", "chip", px + 5.6, py + 4.0, PCB_TOP, 5.0, 5.0, 0.9)
    block("pd_inductor", "ferrite", px + 5.6, py - 6.0, PCB_TOP, 6.0, 6.0, 3.0)
    grid("pd_caps", "passive", PCB_TOP, [(px - 4.0, py - 8.0, 3.2, 1.6), (px - 4.0, py + 1.0, 3.2, 1.6)], 1.6)
    block("pd_jst_main_cell", "conn", px + 5.6, py - 10.0, ABOVE - 2.9, 4.0, 3.0, 2.9)   # underside

    # Qi2 TX board, vertical, 5 mm off the cell end, parts facing away from the cell
    tx, ty = POS["qi2_tx"]
    block("qi2_tx_board", "pcb", tx, ty, 2.0, PCB_T, 30.0, 20.0)
    block("qi2_tx_controller", "chip", tx + PCB_T / 2 + 0.45, ty, 9.5, 0.9, 5.0, 5.0)
    grid("qi2_tx_caps", "passive", 14.0, [(tx + PCB_T / 2 + 0.8, ty - 8, 1.6, 3.2),
                                         (tx + PCB_T / 2 + 0.8, ty + 8, 1.6, 3.2)], 1.6)


def build_lte_gnss():
    sx, sy = POS["sim_board"]
    block("sim_board", "pcb", sx, sy, ABOVE, 32.0, 17.5, 1.0)
    block("sim7080g_module", "metal", sx - 6.75, sy + 0.05, ABOVE + 1.0, 17.6, 15.7, 2.3)
    block("nano_sim_holder", "metal", sx + 9.25, sy - 1.75, ABOVE + 1.0, 12.5, 13.0, 1.4)
    grid("ufl_connectors", "gold", ABOVE + 1.0, [(sx + 3.75, sy + 6.75, 2.0, 2.0), (sx + 6.75, sy + 6.75, 2.0, 2.0)], 1.2)
    # GNSS: Taoglas SGGP.12.4.A.02 SMD patch on the FRONT wall (sky when lying on the back),
    # soldered to a small ground-plane board (our part, 16 x 13 x 1.0) behind it
    gx, gy = POS["gnss"]
    place_step("gnss_patch", "gnss", ("X", "Y", "Z"), (0.0, 0.0, GNSS_T), (gx, gy, INNER))
    block("gnss_board", "pcb", gx, -CAV_Y + 0.05 + 6.5, INNER - GNSS_T - 1.0, 16.0, 13.0, 1.0)
    # LTE: Molex 212570-0100 side-fed flex (40.4 x 15.4) on the TOP wall inner face, adhesive
    # side on the wall, cable leaving the +X end (STEP cropped 6.6 mm past the flex)
    lx, lz = POS["lte"]
    place_step("lte_flex", "lte", ("X", "-Y", "-Z"), (20.2, -0.18, -7.5), (lx, CAV_Y, lz))


def build_speakers():
    """CES-571423-28PMB enclosed speakers (ears cut off), cone face (file -Z) on the face gasket
    and membrane, long side along Y. Each is held by a printed cradle (own STL): a 1.5 mm back
    plate pressing a foam pad on the speaker back, and two arms that bear on the end wall beside
    the honeycomb pocket. The loop closes through the end wall, so nothing else holds it."""
    for side, tag in ((1, "R"), (-1, "L")):
        xf = side * SPK_FACE_X
        axes = ("-Y", "Z", "-X") if side > 0 else ("Y", "Z", "X")
        place_step("speaker_" + tag, "speaker", axes, (28.7, 11.5, 0.03), (xf, SPK_CY, SPK_Z0 + 11.5))
        y0, y1, z1 = SPK_CY - SPK_L / 2, SPK_CY + SPK_L / 2, SPK_Z0 + SPK_H
        xb = xf - side * SPK_D                       # speaker back face
        # foam pad on the back, then the cradle back plate (the four strips fill in) and arms
        side_body("speaker_foam_" + tag, "foam", "x", xb - side * SPK_FOAM / 2.0,
                  [("rect", (y0 + 1.5, SPK_Z0 + 1.0), (y1 - 1.5, z1 - 1.0))], SPK_FOAM - 0.1)
        xm = xb - side * (SPK_FOAM + CRADLE_T / 2.0)
        frame = side_body("speaker_cradle_" + tag, "petg_bare", "x", xm,
                          [("rect", (y0, SPK_Z0), (y1, SPK_Z0 + 3.0)), ("rect", (y0, z1 - 3.0), (y1, z1)),
                           ("rect", (y0, SPK_Z0 + 3.0), (y0 + 3.0, z1 - 3.0)),
                           ("rect", (y1 - 3.0, SPK_Z0 + 3.0), (y1, z1 - 3.0)),
                           ("rect", (y0 - 1.7, 8.0), (y0, 15.0)), ("rect", (y1, 8.0), (y1 + 1.7, 15.0))],
                          CRADLE_T)
        try:
            xa0, xa1 = xm - side * CRADLE_T / 2.0, side * (CAV_X - 0.05)
            arms = [tool_block((xa0 + xa1) / 2.0, sy * (SPK_L / 2.0 + 0.2 + 0.75), 8.0, abs(xa1 - xa0), 1.5, 7.0)
                    for sy in (-1, 1)]
            if len(frame) > 1:
                rest = frame[1:]
                G["parts"] = [b for b in G["parts"] if all(b != r for r in rest)]
                join(frame[0], rest, "SPEAKER_cradle_frame_" + tag)
            frame[0].name = "speaker_cradle_" + tag
            join(frame[0], arms, "SPEAKER_cradle_arms_" + tag)
        except Exception:
            G["fails"].append("speaker_cradle_" + tag)
        z0 = max(SPK_Z0, POCKET_Z[0])       # ring sits on the face, above the rim ledge
        side_body("speaker_gasket_" + tag, "foam", "x", xf + side * SPK_GASKET / 2.0,
                  [("rect", (y0, z0), (y1, z0 + 2)), ("rect", (y0, z1 - 2), (y1, z1)),
                   ("rect", (y0, z0 + 2), (y0 + 2, z1 - 2)), ("rect", (y1 - 2, z0 + 2), (y1, z1 - 2))],
                  SPK_GASKET)
        side_body("grille_mesh_" + tag, "grille_mesh", "x", side * (WALL_THIN_X - MEMBRANE / 2.0),
                  [("rect", (-POCKET_Y, POCKET_Z[0]), (POCKET_Y, POCKET_Z[1]))], MEMBRANE)


def build_ui():
    # Newhaven NHD-2.7-12864WDW3 module: glass face (file -Z) on the front wall inner face,
    # flex tail (file -Y edge) toward the carrier's bottom edge
    place_step("oled", "oled", ("-X", "Y", "-Z"), (33.85, 46.22, 54.23), (DCX, DCY, INNER))
    block("touch_strip_pcb", "copper", STRIP_C[0], STRIP_C[1], INNER - 1.6, 40.0, 5.0, 1.6)
    # Adafruit 6049 (ICS-43434, bottom port): board underside toward the front-wall hole,
    # 0.3 foam gasket; mic centre on the hole
    place_step("mic", "mic", ("-X", "Y", "-Z"), (8.255, 7.11, 0.0), (-66.5, 29.5, INNER - 0.3))
    # Adafruit 5378 right-angle VEML7700: board at right angles to the front wall, sensor
    # (file +Y edge) looking out through the light hole
    place_step("light", "light", ("X", "Z", "-Y"), (12.69, 17.65, 2.82), (-58.5, 29.5, INNER - 0.1))

    # button strip on the TOP wall (left): latching mute + PWR, VOL-, VOL+, PLAY, parts on the
    # +Y face of the strip (Y 29.8), actuators toward the top wall
    block("button_strip_pcb", "pcb", (BTN_X0 + BTN_X1) / 2.0, 29.4, BTN_ZC - 3.5, BTN_X1 - BTN_X0, 0.8, 7.0)
    for name, x, w in BUTTONS:
        if name == "mute":
            # G-Switch PS-7054DVB-6PL: case 7, knob to 12.4 (released); cap as before
            place_step("btn_mute", "latch", ("X", "-Z", "Y"), (0.0, 0.0, 0.0), (x, 29.8, BTN_ZC))
            block("btn_mute_cap", "mute_cap", x, (34.0 + 36.75) / 2.0, BTN_ZC - 3.2, 6.4, 2.75, 6.4)
        else:
            # C&K PTS645SM43SMTR92: plunger top 4.3 above the strip; cap starts on the plunger
            place_step("btn_" + name, "tact", ("X", "-Z", "Y"), (0.0, 0.0, 0.0), (x, 29.8, BTN_ZC))
            c0 = 29.8 + 4.3
            block("btn_%s_cap" % name, "buttons", x, (c0 + 36.75) / 2.0, BTN_ZC - 2.0, 4.0, 36.75 - c0, 4.0)

    # haptic LRA glued to the fin (disc in the YZ plane)
    lx, ly = POS["lra"]
    side_body("haptic_lra_10mm", "metal", "x", lx, [("circle", (ly, 21.0), 10.0)], 3.5)

    # Wi-Fi FlexPIFA 001-0014 on the FRONT wall: adhesive (element) face on the tape, foam end
    # and cable at -X (turned 180 deg about Z)
    place_step("wifi_flexpifa", "wifi", ("-X", "-Y", "Z"), (20.06, 5.5, 2.5), (WIFI_C[0], WIFI_C[1], INNER - WIFI_TAPE))
    block("wifi_tape", "white", WIFI_C[0], WIFI_C[1], WIFI_Z0 + WIFI[2], WIFI[0], WIFI[1], WIFI_TAPE)
    wifi_coax()


def build_dock():
    # pogo target pads (flush with the BOTTOM face) and 6 x 2 magnets in their blind pockets
    for k, x in enumerate(POGO_X):
        place_step("pogo_pad_%d" % (k + 1), "pogo_pad", ("X", "-Z", "Y"), (0.0, 0.0, 0.0), (x, -WIDTH / 2.0, POGO_Z))
    y_lo = -CAV_Y + MAG_PAD_T - FIT_MAG - MAG_T
    for k, x in enumerate(MAG_X):
        place_step("dock_magnet_%d" % (k + 1), "magnet", ("X", "-Z", "Y"), (0.0, 0.0, 0.0), (x, y_lo, MAG_Z))


def wifi_coax():
    comp = G["comp"]
    try:
        sk = comp.sketches.add(comp.xYConstructionPlane)
        pc = adsk.core.ObjectCollection.create()
        for p in WIFI_COAX:
            pc.add(P(*p))
        spl = sk.sketchCurves.sketchFittedSplines.add(pc)
        sk.isVisible = False
        G["wifi_coax_mm"] = spl.length * 10.0
        pi = comp.features.pipeFeatures.createInput(
            comp.features.createPath(spl), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        pi.sectionSize = vi(1.13)
        f = comp.features.pipeFeatures.add(pi)
        b = f.bodies.item(0)
        b.name = "wifi_coax"
        paint(b, "coax")
        G["parts"].append(b)
    except Exception:
        G["fails"].append("wifi_coax")


# ----------------------------------------------------------------------
# REAL PARTS (STEP files in cad/models)
# ----------------------------------------------------------------------
MODELS = os.path.join(CAD, "models")
AX = {"X": (1, 0, 0), "-X": (-1, 0, 0), "Y": (0, 1, 0), "-Y": (0, -1, 0), "Z": (0, 0, 1), "-Z": (0, 0, -1)}
# name: (STEP under cad/models, local bbox x0, y0, z0, x1, y1, z1 as measured in the file)
REAL = {
    "speaker": ("speaker_ces-571423-28pmb/ces-571423-28pmb_ears_cut.step", (-0.08, -0.02, 0.03, 57.48, 23.02, 14.92)),
    "usb_c": ("usbc_amphenol_124019572112a/124019572112a.step", (-9.76, 6.90, -2.15, -1.90, 19.10, 2.15)),
    "tact": ("btn_tact_pts645sm43smtr92/pts645sm43smtr92_kicad.step", (-4.5, -3.0, 0.0, 4.5, 3.0, 4.3)),
    "latch": ("btn_latch_ps-7054dvb-6pl/ps-7054dvb-6pl_from_drawing.step", (-3.5, -3.5, -3.5, 3.5, 3.5, 12.4)),
    "oled": ("oled_nhd-2.7-12864wdw3/nhd-2.7-12864wdx3.step", (-7.11, 21.90, 54.23, 74.89, 72.39, 60.98)),
    "mic": ("mic_adafruit-6049_ics-43434/adafruit_6049_ics-43434.step", (0.0, 0.0, -0.07, 16.51, 12.70, 2.53)),
    "light": ("light_adafruit-5378_veml7700/adafruit_5378_veml7700.step", (0.0, 0.0, 0.0, 25.40, 17.78, 4.53)),
    "wifi": ("flexpifa_001-0014/flexpifa_001-0014_from_drawing.step", (0.0, -5.0, 0.0, 41.25, 11.0, 2.5)),
    "gnss": ("gnss_taoglas_sggp.12.4.a.02/sggp.12.4.a.02_from_drawing.step", (-6.0, -6.0, 0.0, 6.0, 6.0, 4.0)),
    "lte": ("lte_molex_212570-0100/212570-0100_cable_cut.step", (-0.21, -0.18, -15.21, 47.01, 1.40, 0.21)),
    "cell": ("cell_lipol_lp1160100/lp1160100_from_drawing.step", (-4.0, -30.25, 0.0, 101.0, 30.25, 11.3)),
    "pogo_pad": ("pogo_pad/pogo_pad_from_params.step", (-1.25, -1.25, 0.0, 1.25, 1.25, 2.2)),
    "magnet": ("magnet_6x2/magnet_6x2_from_drawing.step", (-3.0, -3.0, 0.0, 3.0, 3.0, 2.0)),
}


def _rot(axes):
    return [AX[a] for a in axes]


def _apply(R, p):
    return tuple(sum(R[k][i] * p[k] for k in range(3)) for i in range(3))


def place_step(name, key, axes, local_ref, world_ref):
    """Imports cad/models/<REAL[key]> as component `name`. axes = world directions of the
    file's local X, Y, Z ("X", "-Y", ...); local_ref (file mm) lands on world_ref (model mm).
    The wrapper is placed before the import (moving it afterwards loses nested parts). Bodies
    are renamed "<name>|<body>" so the fit check can tell parts apart."""
    rel, lb = REAL[key]
    path = os.path.join(MODELS, rel)
    if not os.path.isfile(path):
        G["fails"].append("%s (STEP not found: %s)" % (name, rel))
        return None
    R = _rot(axes)
    rl = _apply(R, local_ref)
    t = [world_ref[i] - rl[i] for i in range(3)]
    m = adsk.core.Matrix3D.create()
    m.setWithCoordinateSystem(P(*t), adsk.core.Vector3D.create(*R[0]), adsk.core.Vector3D.create(*R[1]),
                              adsk.core.Vector3D.create(*R[2]))
    app = adsk.core.Application.get()
    occ = G["design"].rootComponent.occurrences.addNewComponent(m)
    occ.component.name = name
    opts = app.importManager.createSTEPImportOptions(path)
    opts.isViewFit = False
    app.importManager.importToTarget(opts, occ.component)
    comps = [occ.component] + [o.component for o in occ.component.allOccurrences]
    seen = set()
    for c in comps:
        if c.entityToken in seen:
            continue
        seen.add(c.entityToken)
        for i in range(c.bRepBodies.count):
            b = c.bRepBodies.item(i)
            b.name = "%s|%s" % (name, b.name)
    bodies = occ_bodies(occ)
    G["imp"][name] = (occ, bodies, rel)
    # placement check: world bbox against the transformed file bbox
    corners = [_apply(R, (x, y, z)) for x in (lb[0], lb[3]) for y in (lb[1], lb[4]) for z in (lb[2], lb[5])]
    exp_lo = [min(c[i] for c in corners) + t[i] for i in range(3)]
    exp_hi = [max(c[i] for c in corners) + t[i] for i in range(3)]
    if bodies:
        lo = [min(getattr(b.boundingBox.minPoint, a) for b in bodies) * 10 for a in "xyz"]
        hi = [max(getattr(b.boundingBox.maxPoint, a) for b in bodies) * 10 for a in "xyz"]
        err = max(max(abs(lo[i] - exp_lo[i]), abs(hi[i] - exp_hi[i])) for i in range(3))
        G["imp_box"][name] = (lo, hi)
        if err > 0.1:
            G["fails"].append("%s placed %.2f mm off the expected box" % (name, err))
    else:
        G["fails"].append("%s (no bodies imported)" % name)
    return occ


def imp_bodies(n):
    """Bodies of imported parts named n or n_<suffix>."""
    out = []
    for k, (occ, bodies, rel) in G["imp"].items():
        if k == n or k.startswith(n + "_"):
            out += bodies
    return out


# ----------------------------------------------------------------------
# CARRIER
# ----------------------------------------------------------------------
def occ_bodies(occ):
    out = [occ.bRepBodies.item(i) for i in range(occ.bRepBodies.count)]
    for i in range(occ.childOccurrences.count):
        out += occ_bodies(occ.childOccurrences.item(i))
    return out


def import_carrier(design):
    app = adsk.core.Application.get()
    root = design.rootComponent
    path = os.path.join(CAD, "heartsync_carrier.step")
    if not os.path.isfile(path):
        G["fails"].append("carrier_step (not found)")
        return None
    m = adsk.core.Matrix3D.create()
    m.translation = adsk.core.Vector3D.create(mm(CAR_X0 - STEP_BOARD_X0), mm(CAR_Y1 - STEP_BOARD_Y1),
                                              mm(ABOVE - STEP_BOARD_Z0))
    occ = root.occurrences.addNewComponent(m)
    occ.component.name = "carrier"
    opts = app.importManager.createSTEPImportOptions(path)
    opts.isViewFit = False
    app.importManager.importToTarget(opts, occ.component)
    G["carrier"] = occ
    pcb = [b for b in occ_bodies(occ)
           if mm(1.4) < (b.boundingBox.maxPoint.z - b.boundingBox.minPoint.z) < mm(1.7)
           and (b.boundingBox.maxPoint.x - b.boundingBox.minPoint.x) > mm(60.0)]
    if len(pcb) != 1:
        G["fails"].append("carrier_step (found %d PCB bodies)" % len(pcb))
        return occ
    bb = pcb[0].boundingBox
    err = max(abs(bb.minPoint.x - mm(CAR_X0)), abs(bb.maxPoint.y - mm(CAR_Y1)), abs(bb.minPoint.z - mm(ABOVE)))
    if err > mm(0.05):
        G["fails"].append("carrier_step (PCB off target by %.2f mm)" % (err * 10.0))
    try:
        pcb[0].nativeObject.attributes.add("heartsync", "anchor", json.dumps(
            {"pos": "carrier", "axes": "xy", "ref": [bb.minPoint.x * 10, bb.maxPoint.y * 10, 0],
             "corner": "x0y1"}))
    except Exception:
        pass
    return occ


# ----------------------------------------------------------------------
# CHECKS
# ----------------------------------------------------------------------
def body_label(b):
    ctx = b.assemblyContext
    return "%s/%s" % (ctx.name, b.name) if ctx else b.name


# pairs that touch by design (THT pins through a PCB that has no holes modelled)
EXPECTED = {("btn_mute", "button_strip_pcb")}
# parts whose bodies cannot go into one interference run together: the Amphenol USB-C shell
# (2457 faces) makes analyzeInterference return nothing against its own contacts. Pass 1
# checks the listed bodies, pass 2 the rest, both against everything else.
FIT_SPLIT = {"usb_c": ("Body1",)}


def _all_bodies(design):
    """(body proxy, owner) for every visible solid in the design. Owner: the imported part
    ("name|body"), "carrier" for anything under the carrier occurrence, else the body name."""
    root = design.rootComponent
    out = []
    for i in range(root.bRepBodies.count):
        b = root.bRepBodies.item(i)
        out.append((b, b.name.split("|")[0]))
    for oc in root.allOccurrences:
        if oc.component.name in ("labels", "net"):
            continue
        in_carrier = "carrier:" in oc.fullPathName
        for i in range(oc.bRepBodies.count):
            b = oc.bRepBodies.item(i)
            if not b.isSolid:
                continue
            n = b.name
            out.append((b, "carrier" if in_carrier and "|" not in n else n.split("|")[0]))
    return out


def fit_check(design=None):
    """Every overlap between different parts, with volume and the overlap box, on the design
    as it stands (rerun after moving parts by hand). Overlaps inside one imported part or
    inside the carrier STEP are ignored. Lines are kept in G["clashes"]."""
    if design is None:
        design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    found = _all_bodies(design)
    own = {b.entityToken: o for b, o in found}

    def sub(b, o):
        return b.name.split("|", 1)[1] if "|" in b.name else ""

    # pass 1 keeps only the listed bodies of a split part, pass 2 only the others
    passes = [[b for b, o in found if o not in FIT_SPLIT or sub(b, o) in FIT_SPLIT[o]],
              [b for b, o in found if o not in FIT_SPLIT or sub(b, o) not in FIT_SPLIT[o]]]
    results, seen = [], set()
    for bodies in passes:
        ents = adsk.core.ObjectCollection.create()
        for b in bodies:
            ents.add(b)
        res = design.analyzeInterference(design.createInterferenceInput(ents))
        if res is None:
            return "Fit check could not run (analyzeInterference returned nothing for %d bodies)." % len(bodies)
        for i in range(res.count):
            r = res.item(i)
            k = tuple(sorted((r.entityOne.entityToken, r.entityTwo.entityToken)))
            if k not in seen:
                seen.add(k)
                results.append(r)

    def owner(e):
        o = own.get(e.entityToken)
        if o:
            return o
        if "|" in e.name:
            return e.name.split("|")[0]
        # our bodies all have explicit names; generic STEP names belong to the carrier
        return "carrier" if re.match(r"^(Body\d+|.*:\d+)$", e.name) or e.name not in set(own.values()) else e.name

    pairs, internal, expected = {}, 0, 0
    for r in results:
        oa, ob = owner(r.entityOne), owner(r.entityTwo)
        if oa == ob:
            internal += 1
            continue
        key = tuple(sorted((oa, ob)))
        ib = r.interferenceBody
        v = ib.volume * 1000.0
        bb = ib.boundingBox
        lo, hi = bb.minPoint, bb.maxPoint
        near_ufl = abs((lo.x + hi.x) * 5 - UFL[0]) < 3.0 and abs((lo.y + hi.y) * 5 - UFL[1]) < 5.0
        if key in EXPECTED or tuple(reversed(key)) in EXPECTED or \
                (key == ("carrier", "wifi_coax") and near_ufl):      # cable into its U.FL plug
            expected += 1
            continue
        if key not in pairs:
            pairs[key] = [0.0, [lo.x, lo.y, lo.z], [hi.x, hi.y, hi.z], []]
        p = pairs[key]
        p[0] += v
        p[1] = [min(p[1][0], lo.x), min(p[1][1], lo.y), min(p[1][2], lo.z)]
        p[2] = [max(p[2][0], hi.x), max(p[2][1], hi.y), max(p[2][2], hi.z)]
        if oa == "carrier" or ob == "carrier":
            p[3].append(body_label(r.entityOne if oa == "carrier" else r.entityTwo))
    lines = []
    for (a, b), (v, lo, hi, cb) in sorted(pairs.items(), key=lambda kv: -kv[1][0]):
        d = [(hi[k] - lo[k]) * 10 for k in range(3)]
        what = " [%s]" % ", ".join(sorted(set(x.split("/")[-1] for x in cb))[:4]) if cb else ""
        lines.append("%s x %s%s: %.2f mm3, overlap %.2f x %.2f x %.2f at X %.1f..%.1f Y %.1f..%.1f Z %.1f..%.1f" % (
            a, b, what, v, d[0], d[1], d[2], lo[0] * 10, hi[0] * 10, lo[1] * 10, hi[1] * 10, lo[2] * 10, hi[2] * 10))
    G["clashes"] = lines
    note = " (%d bodies, %d same-part overlaps ignored, %d expected THT-pin contacts)" % (len(found), internal, expected)
    msg = ("Fit check: 0 clashes%s." % note) if not lines else \
        ("Fit check: %d clashing pairs%s:\n  %s" % (len(lines), note, "\n  ".join(lines)))
    print(msg)
    return msg


def _dist(a, b):
    return adsk.core.Application.get().measureManager.measureMinimumDistance(a, b).value * 10.0


def clearance_report():
    def named(n):
        return [b for b in G["parts"] if b.name == n or b.name.startswith(n + "_")] + imp_bodies(n)

    car = occ_bodies(G["carrier"]) if G.get("carrier") else []

    def d(a, b):
        A, B = named(a), named(b)
        if not A or not B:
            return None
        return min(_dist(x, y) for x in A for y in B)

    out = ["Clearances (minimum distance, mm):"]
    rules = [("lte_flex", x, 10.0) for x in ("usb_c", "pd_inductor", "qi2_ferrite",
                                             "qi2_magnet_ring", "qi2_winding", "pogo_pad", "dock_magnet")]
    rules += [("pd_inductor", a, 15.0) for a in ("wifi_flexpifa", "gnss_patch", "lte_flex")]
    rules += [("wifi_flexpifa", "oled", 5.0)]
    for a, b, lim in rules:
        v = d(a, b)
        out.append("  %-18s %-18s %6s  rule >= %2.0f  %s" % (a, b, "%.1f" % v if v is not None else "-", lim,
                                                         "OK" if v is not None and v >= lim else "FAIL"))
    report = [("wifi_flexpifa", ("cell", "qi2_ferrite", "gnss_patch", "sim7080g_module",
                                 "nano_sim_holder", "pogo_pad", "speaker_L", "lte_flex", "oled")),
              ("gnss_patch", ("cell", "oled", "speaker_L", "sim7080g_module",
                              "wifi_flexpifa", "dock_magnet", "mic")),
              ("lte_flex", ("cell", "touch_strip_pcb", "button_strip_pcb", "btn_play",
                            "qi2_ferrite", "usb_c", "pd_inductor", "oled")),
              ("speaker_R", ("qi2_tx_board", "qi2_ferrite", "qi2_magnet_ring", "cell", "pd_board")),
              ("speaker_L", ("cell", "gnss_patch", "gnss_board", "sim_board", "btn_mute", "oled")),
              ("qi2_ferrite", ("pd_board", "usb_c", "qi2_tx_board", "speaker_R"))]
    for a, others in report:
        parts = []
        for o in others:
            v = d(a, o)
            if v is not None:
                parts.append("%s %.1f" % (o, v))
        A = named(a)
        if A and car:
            parts.append("carrier %.1f" % min(_dist(A[0], b) for b in car))
        out.append("  %s: %s" % (a, ", ".join(parts)))
    W = named("wifi_flexpifa")
    if W:
        out.append("  wifi_flexpifa to phone footprint (X >= %.1f): %.1f"
                   % (PHONE_X0, PHONE_X0 - W[0].boundingBox.maxPoint.x * 10))
    return "\n".join(out)


def grille_report():
    n = G.get("honeycomb_n", 0)
    hole = math.sqrt(3) / 2.0 * HC_HEX ** 2
    cell = math.sqrt(3) / 2.0 * HC_PITCH ** 2
    cs = honeycomb_centres()
    w = (max(c[0] for c in cs) - min(c[0] for c in cs)) + 2 * HC_R
    h = (max(c[1] for c in cs) - min(c[1] for c in cs)) + HC_HEX
    return ("Grille: %d hex holes per end, %.1f AF at %.1f pitch (web %.1f), open %.1f %% of the "
            "%.1f x %.1f honeycomb (%.1f %% per cell), Z %.2f..%.2f" % (
                n, HC_HEX, HC_PITCH, HC_PITCH - HC_HEX, 100.0 * n * hole / (w * h), w, h,
                100.0 * hole / cell, HC_ZC - h / 2, HC_ZC + h / 2))


def stack_report():
    return ("Stack: shell %.1f (tray %.1f + lid %.1f) + back ring %.1f proud = %.1f mm (limit 35; back is bare "
            "PETG). Cell (max %.1f) %.1f..%.1f, insulator to %.1f, swell gap %.1f to %.1f, board %.1f..%.1f, "
            "coil ferrite %.1f, front wall %.1f..%.1f. Lid: ring channel floor %.1f, gasket channel bottom %.1f "
            "-> %.1f between" % (THICKNESS, TRAY_H, LID, BR_PROUD, THICKNESS + BR_PROUD, CELL_T, Z_CELL, CELL_TOP,
                                 CELL_TOP + INSUL, SWELL, ABOVE, ABOVE, PCB_TOP, COIL_Z0, INNER, TRAY_H,
                                 -LID + BR_CH, -GASKET_D, (-GASKET_D) - (-LID + BR_CH)))


# ----------------------------------------------------------------------
# GROUPING, SIDE NAMES, FINISHES, LABELS
# ----------------------------------------------------------------------
def group(n):
    if n in ("shell_tray", "ring_inlay"):
        return "tray"
    if n == "shell_lid":
        return "lid"
    if n == "carrier_bracket":
        return "bracket"
    if n.startswith(("back_ring", "screw_head", "usb_c_gasket")):
        return "trim"
    if n == "cell" or n == "usb_c" or n.startswith(("cell_", "pd_", "qi2_", "keepout_")):
        return "power"
    if n.startswith(("speaker_", "grille_mesh")):
        return "speakers"
    if n in ("sim_board", "sim7080g_module", "nano_sim_holder", "lte_flex") \
            or n.startswith(("ufl_connectors", "gnss_")):
        return "lte"
    if n.startswith("wifi_"):
        return "wifi"
    if n.startswith(("dock_magnet", "pogo_pad")):
        return "dock"
    return "ui"


def group_components(design):
    root = design.rootComponent
    I = adsk.core.Matrix3D.create()
    shell = root.occurrences.addNewComponent(I)
    shell.component.name = "shell"
    occs = {}
    for g in ("tray", "lid", "bracket"):
        o = shell.component.occurrences.addNewComponent(I)
        o.component.name = g
        occs[g] = o.createForAssemblyContext(shell)
    for g in ("trim", "power", "speakers", "lte", "wifi", "ui", "dock"):
        o = root.occurrences.addNewComponent(I)
        o.component.name = g
        occs[g] = o
    while root.bRepBodies.count:
        b = root.bRepBodies.item(root.bRepBodies.count - 1)
        b.moveToComponent(occs[group(b.name)])
    moved = 0
    for name, (occ, bodies, rel) in G["imp"].items():
        try:
            occ.moveToComponent(occs[group(name)])
            moved += 1
        except Exception:
            G["fails"].append("group %s" % name)
    return ", ".join("%s %d" % (g, o.component.bRepBodies.count) for g, o in occs.items()) + \
        "; %d imported parts moved into their groups" % moved


def find_body(design, name):
    root = design.rootComponent
    for oc in root.allOccurrences:
        for i in range(oc.bRepBodies.count):
            b = oc.bRepBodies.item(i)
            if b.name == name:
                return b
    return root.bRepBodies.itemByName(name)


def side_of(face, body_name):
    """Outer side name of a tray/lid face, or None (inside, holes, grooves)."""
    g = face.geometry
    bb = face.boundingBox
    lo, hi = bb.minPoint, bb.maxPoint
    hx, hy = mm(LENGTH / 2.0), mm(WIDTH / 2.0)
    if isinstance(g, adsk.core.Plane):
        n = g.normal
        if body_name == "shell_tray" and n.z > 0.99 and abs(hi.z - mm(TRAY_H)) < 1e-4:
            return "FRONT"
        if body_name == "shell_lid" and n.z < -0.99 and abs(lo.z + mm(LID)) < 1e-4:
            return "BACK"
        if abs(n.y) > 0.99 and abs(abs(lo.y) - hy) < 1e-4 and abs(abs(hi.y) - hy) < 1e-4:
            return "TOP_EDGE" if lo.y > 0 else "BOTTOM_EDGE"
        if abs(n.x) > 0.99 and abs(abs(lo.x) - hx) < 1e-4 and abs(abs(hi.x) - hx) < 1e-4:
            return "RIGHT_END" if lo.x > 0 else "LEFT_END"
    elif isinstance(g, adsk.core.Cylinder) and abs(g.radius - mm(CORNER_R)) < 1e-4:
        return "CORNER"
    return None


SIDE_FINISH = {"FRONT": "front_panel", "BACK": "petg_bare", "TOP_EDGE": "shell_fabric",
               "BOTTOM_EDGE": "petg_bare", "LEFT_END": "petg_bare", "RIGHT_END": "petg_bare",
               "CORNER": "petg_bare"}


def name_and_paint_sides(design):
    counts = {}
    for name in ("shell_tray", "shell_lid"):
        b = find_body(design, name)
        if b is None:
            continue
        nb = b.nativeObject or b
        paint(nb, "petg_bare")
        for f in nb.faces:
            s = side_of(f, name)
            if not s:
                continue
            try:
                f.attributes.add("heartsync", "side", s)
            except Exception:
                pass
            # fabric only on the tray's TOP edge: the lid (back and its edges) is bare PETG
            a = appearance("petg_bare" if name == "shell_lid" else SIDE_FINISH[s])
            if a:
                try:
                    f.appearance = a
                except Exception:
                    pass
            counts[s] = counts.get(s, 0) + 1
    return ", ".join("%s %d" % kv for kv in sorted(counts.items()))


def build_labels(design):
    root = design.rootComponent
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = "labels"
    specs = [("FRONT", "z", TRAY_H + 0.05), ("BACK", "z", -LID - 0.05),
             ("TOP_EDGE", "y", WIDTH / 2.0 + 0.05), ("BOTTOM_EDGE", "y", -WIDTH / 2.0 - 0.05),
             ("RIGHT_END", "x", LENGTH / 2.0 + 0.05), ("LEFT_END", "x", -LENGTH / 2.0 - 0.05)]
    made = 0
    for text, axis, off in specs:
        try:
            base = {"z": comp.xYConstructionPlane, "y": comp.xZConstructionPlane, "x": comp.yZConstructionPlane}[axis]
            pi = comp.constructionPlanes.createInput()
            pi.setByOffset(base, vi(off))
            pl = comp.constructionPlanes.add(pi)
            o = pl.geometry.origin
            if abs({"z": o.z, "y": o.y, "x": o.x}[axis] * 10 - off) > 0.01:
                pl.deleteMe()
                pi = comp.constructionPlanes.createInput()
                pi.setByOffset(base, vi(-off))
                pl = comp.constructionPlanes.add(pi)
            pl.isLightBulbOn = False
            sk = comp.sketches.add(pl)
            if axis == "z":
                a, b = P(-30, -3, off), P(30, 3, off)
            elif axis == "y":
                a, b = P(-30, off, 10), P(30, off, 16)
            else:
                a, b = P(off, -25, 10), P(off, 25, 16)
            pa, pb = sk.modelToSketchSpace(a), sk.modelToSketchSpace(b)
            ti = sk.sketchTexts.createInput2(text, mm(5.0))
            ti.setAsMultiLine(adsk.core.Point3D.create(min(pa.x, pb.x), min(pa.y, pb.y), 0),
                              adsk.core.Point3D.create(max(pa.x, pb.x), max(pa.y, pb.y), 0),
                              adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                              adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
            sk.sketchTexts.add(ti)
            sk.name = "label_" + text
            made += 1
        except Exception:
            G["fails"].append("label_" + text)
    occ.isLightBulbOn = False
    return made


ANCHORS = {"qi2_ferrite": ("coil", "xy"), "pd_board": ("pd_board", "xy"), "qi2_tx_board": ("qi2_tx", "xy"),
           "sim_board": ("sim_board", "xy"), "haptic_lra_10mm": ("lra", "xy"), "button_strip_pcb": ("buttons", "x"),
           # imported parts: the anchor sits on their largest body
           "cell": ("cell", "xy"), "oled": ("oled", "xy"), "usb_c": ("usb_c", "x"),
           "wifi_flexpifa": ("wifi", "xy"), "gnss_patch": ("gnss", "xy"), "lte_flex": ("lte", "xz")}


def tag_anchors():
    tagged = [b for b in G["parts"] if b.name in ANCHORS]
    for name, (occ, bodies, rel) in G["imp"].items():
        if name in ANCHORS and bodies:
            tagged.append((name, max(bodies, key=lambda b: b.volume)))
    for item in tagged:
        name, b = item if isinstance(item, tuple) else (item.name, item)
        key, axes = ANCHORS[name]
        bb = b.boundingBox
        try:
            nb = b.nativeObject or b
            nb.attributes.add("heartsync", "anchor", json.dumps(
                {"pos": key, "axes": axes, "ref": [bb.minPoint.x * 10, bb.minPoint.y * 10, bb.minPoint.z * 10]}))
        except Exception:
            pass


# ----------------------------------------------------------------------
# RUN
# ----------------------------------------------------------------------
def run(context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        print("Open a Design workspace first.")
        return "no design"
    G["design"] = design
    G["comp"] = design.rootComponent
    try:
        G["base_app"] = find_base_appearance(app)
    except Exception:
        G["base_app"] = None

    build_tray()
    build_lid()
    build_trim()
    build_bracket()
    build_coil()
    build_power()
    build_lte_gnss()
    build_speakers()
    build_ui()
    build_dock()
    tag_anchors()
    if CARRIER:
        import_carrier(design)

    report = [stack_report(), grille_report()]
    try:
        report.append(clearance_report())
    except Exception as e:
        report.append("Clearance report could not run: %s" % e)
    n_parts = len(G["parts"])
    n_carrier = len(occ_bodies(G["carrier"])) if G.get("carrier") else 0
    grouped = group_components(design) if GROUP else "off"
    try:
        report.insert(2, fit_check(design))
    except Exception as e:
        report.insert(2, "Fit check could not run: %s" % e)
    sides = name_and_paint_sides(design)
    labels = build_labels(design)

    app.activeViewport.fit()
    n_imp = sum(len(v[1]) for v in G["imp"].values())
    msg = ("heartsync STACK (%s display, dock %s)\n"
           "Shell %.1f x %.1f x %.1f, inside height %.1f, board layer Z %.1f\n"
           "Parts: %d bodies, %d real parts from cad/models (%d bodies), carrier STEP: %d bodies\n"
           "Wi-Fi cable: %.1f stub (in the antenna STEP) + %.1f routed = %.1f mm of 100\n"
           "Components: %s\nSides: %s; labels %d (hidden)\n"
           % (DISPLAY, DOCK_SIDE, LENGTH, WIDTH, THICKNESS, INNER, ABOVE, n_parts, len(G["imp"]), n_imp,
              n_carrier, WIFI_STUB, G.get("wifi_coax_mm", 0), WIFI_STUB + G.get("wifi_coax_mm", 0),
              grouped, sides, labels))
    if G["fails"]:
        msg += "Could not build: %s\n" % ", ".join(G["fails"])
    if PARAM_NOTES:
        msg += "Params: %s\n" % "; ".join(PARAM_NOTES)
    msg += "\n".join(report)
    print(msg)
    return msg


# ----------------------------------------------------------------------
# PRINT CHECKS (thin walls, overhangs) on the open design
# ----------------------------------------------------------------------
def print_checks():
    """Thin walls by inward rays from face sample points; overhangs > 45 deg for the print
    orientation (tray front face down, lid outside face down; bracket printed on its side)."""
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    lines = []
    for name, down in (("shell_tray", 1), ("shell_lid", -1), ("carrier_bracket", 0)):
        body = find_body(design, name)
        if body is None:
            continue
        thin, rays = [], 0
        for f in body.faces:
            ev = f.evaluator
            pts = [f.pointOnFace]
            rng = ev.parametricRange()
            pmin, pmax = rng.minPoint, rng.maxPoint
            if f.area > 0.5:
                for u in (0.25, 0.5, 0.75):
                    for v in (0.25, 0.5, 0.75):
                        pp = adsk.core.Point2D.create(pmin.x + (pmax.x - pmin.x) * u, pmin.y + (pmax.y - pmin.y) * v)
                        if ev.isParameterOnFace(pp):
                            okp, p3 = ev.getPointAtParameter(pp)
                            if okp:
                                pts.append(p3)
            for p in pts:
                okn, n = ev.getNormalAtPoint(p)
                if not okn:
                    continue
                d = n.copy()
                d.scaleBy(-1)
                o = p.copy()
                step = d.copy()
                step.scaleBy(1e-4)
                o.translateBy(step)
                hits = adsk.core.ObjectCollection.create()
                ents = root.findBRepUsingRay(o, d, adsk.fusion.BRepEntityTypes.BRepFaceEntityType, -1.0, False, hits)
                rays += 1
                best = None
                for i in range(ents.count):
                    if ents.item(i).body.name != name:
                        continue
                    t = o.distanceTo(hits.item(i)) * 10.0
                    if t > 0.02 and (best is None or t < best):
                        best = t
                if best is not None and best < MIN_WALL - 0.01:
                    thin.append((best, p.x * 10, p.y * 10, p.z * 10))
        thin.sort()
        web = [t for t in thin if abs(t[1]) > CAV_X - 0.5]
        thin = [t for t in thin if abs(t[1]) <= CAV_X - 0.5]
        if web:
            lines.append("%s: honeycomb webs %d samples, %.2f..%.2f mm (by spec)" % (
                name, len(web), min(w[0] for w in web), max(w[0] for w in web)))
        spots = {}
        for t, x, y, z in thin:
            spots.setdefault((round(x / 10), round(y / 10), round(z / 10)), (t, x, y, z))
        lines.append("%s: %d rays, %d thin samples (< %.1f mm)%s" % (
            name, rays, len(thin), MIN_WALL, ", thinnest %.2f" % thin[0][0] if thin else ""))
        for t, x, y, z in sorted(spots.values())[:12]:
            lines.append("    %.2f mm at (%.1f, %.1f, %.1f)" % (t, x, y, z))
        if down:
            bed = mm(TRAY_H) if down > 0 else -mm(LID)
            over = []
            for f in body.faces:
                okn, n = f.evaluator.getNormalAtPoint(f.pointOnFace)
                if not okn or n.z * down <= math.cos(math.radians(45)) + 1e-3:
                    continue
                if abs(f.pointOnFace.z - bed) < 1e-4:
                    continue
                over.append((f.area * 100.0, f.pointOnFace))
            over.sort(key=lambda t: -t[0])
            lines.append("  overhangs > 45 deg: %d faces, %.0f mm2 total" % (len(over), sum(a for a, _ in over)))
            for a, p in over[:10]:
                lines.append("    %.1f mm2 at (%.1f, %.1f, %.1f)" % (a, p.x * 10, p.y * 10, p.z * 10))
    msg = "\n".join(lines)
    print(msg)
    return msg


# ----------------------------------------------------------------------
# EXPORTS
# ----------------------------------------------------------------------
def _mesh_opts(o):
    try:
        o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementCustom
        o.surfaceDeviation = mm(0.01)
        o.normalDeviation = math.radians(5.0)
    except Exception:
        pass


def export_all():
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    em = design.exportManager
    out = os.path.join(CAD, "exports")
    os.makedirs(out, exist_ok=True)
    root = design.rootComponent
    done = []

    def occ_named(n):
        for oc in root.allOccurrences:
            if oc.component.name == n:
                return oc
        return None

    for comp_name, fn in (("tray", "heartsync_tray.3mf"), ("lid", "heartsync_lid.3mf")):
        occ = occ_named(comp_name)
        if occ:
            o = em.createC3MFExportOptions(occ, os.path.join(out, fn))
            _mesh_opts(o)
            em.execute(o)
            done.append(fn)
    for n, fn in (("shell_tray", "heartsync_tray.stl"), ("shell_lid", "heartsync_lid.stl"),
                  ("carrier_bracket", "heartsync_bracket.stl"), ("back_ring", "heartsync_back_ring_tpu.stl"),
                  ("speaker_cradle_L", "heartsync_speaker_cradle_L.stl"),
                  ("speaker_cradle_R", "heartsync_speaker_cradle_R.stl")):
        b = find_body(design, n)
        if b:
            o = em.createSTLExportOptions(b, os.path.join(out, fn))
            o.isBinaryFormat = True
            _mesh_opts(o)
            em.execute(o)
            done.append(fn)
    em.execute(em.createSTEPExportOptions(os.path.join(out, "heartsync_full_assembly.step"), root))
    done.append("heartsync_full_assembly.step")
    msg = "Exported: " + ", ".join(done)
    print(msg)
    return msg


# ----------------------------------------------------------------------
# FLAT NET (TOP + BACK fabric), linked to the model constants
# ----------------------------------------------------------------------
def net_geometry():
    """Net primitives in mm: one piece, the tray TOP edge (fabric only there; the back is bare
    PETG). Seen from outside the top edge with the FRONT up: model +X is on the left. u = along
    the edge incl. the quarter-round corner wraps, v = z from the lid seam (0) to the front edge.
    ("cut", pts), ("fold", pts), ("circle_cut", centre, r), ("text", p, s, size)."""
    L, r = LENGTH, CORNER_R
    arc = math.pi / 2.0 * r
    prims = []

    def bu(x):
        return L / 2.0 - x

    u0, u1 = r - arc, L - r + arc            # strip incl. the corner wraps onto the ends
    prims.append(("cut", [(u0, 0), (u1, 0), (u1, TRAY_H), (u0, TRAY_H), (u0, 0)]))
    prims.append(("fold", [(r, 0), (r, TRAY_H)]))           # corner tangent lines
    prims.append(("fold", [(L - r, 0), (L - r, TRAY_H)]))

    def box(x, z, w, h):
        a, b = bu(x - w / 2), bu(x + w / 2)
        return [(a, z - h / 2), (b, z - h / 2), (b, z + h / 2), (a, z + h / 2), (a, z - h / 2)]
    prims.append(("cut", box(USB_X, USB_ZC, USB[0] + 2 * FIT_USB, USB[1] + 2 * FIT_USB)))
    for name, x, w in BUTTONS:
        h = (6.4 if name == "mute" else 4.0) + 2 * FIT_BTN
        prims.append(("cut", box(x, BTN_ZC, h, h)))
    prims.append(("text", (L / 2.0, TRAY_H + 6), "TOP_EDGE fabric (tray, lid seam at the bottom edge, FRONT at the top)", 3.5))
    prims.append(("fold", [(0, -12), (50, -12)]))
    prims.append(("text", (25, -17), "50 mm check (print at 100 %)", 3.0))
    return prims


def make_net():
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    out_dir = os.path.join(CAD, "net")
    os.makedirs(out_dir, exist_ok=True)
    prims = net_geometry()
    occ = None
    for oc in root.occurrences:
        if oc.component.name == "net":
            occ = oc
    if occ is None:
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ.component.name = "net"
    comp = occ.component
    while comp.sketches.count:
        comp.sketches.item(0).deleteMe()
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "heartsync_net"
    sk.isComputeDeferred = True
    lines = sk.sketchCurves.sketchLines
    for pr in prims:
        kind = pr[0]
        if kind in ("cut", "fold"):
            for a, b in zip(pr[1], pr[1][1:]):
                ln = lines.addByTwoPoints(P(a[0], a[1]), P(b[0], b[1]))
                if kind == "fold":
                    ln.isConstruction = True
        elif kind == "circle_cut":
            sk.sketchCurves.sketchCircles.addByCenterRadius(P(pr[1][0], pr[1][1]), mm(pr[2]))
        elif kind == "text":
            p, s, size = pr[1], pr[2], pr[3]
            ti = sk.sketchTexts.createInput2(s, mm(size))
            ti.setAsMultiLine(P(p[0] - 45, p[1] - size), P(p[0] + 45, p[1] + size),
                              adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                              adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
            sk.sketchTexts.add(ti)
    sk.isComputeDeferred = False
    occ.isLightBulbOn = False
    dxf = os.path.join(out_dir, "heartsync_net.dxf")
    sk.saveAsDXF(dxf)
    pdf = os.path.join(out_dir, "heartsync_net.pdf")
    write_net_pdf(prims, pdf)
    msg = "Net: %s, %s" % (dxf, pdf)
    print(msg)
    return msg


def write_net_pdf(prims, path):
    """Minimal vector PDF at 1:1 (1 mm = 72/25.4 pt), one page sized to the net + 15 mm margin."""
    k = 72.0 / 25.4
    xs, ys = [], []
    for pr in prims:
        if pr[0] in ("cut", "fold"):
            xs += [p[0] for p in pr[1]]
            ys += [p[1] for p in pr[1]]
    m = 15.0
    x0, y0 = min(xs) - m, min(ys) - m
    wpt, hpt = (max(xs) - min(xs) + 2 * m) * k, (max(ys) - min(ys) + 2 * m) * k

    def tp(x, y):
        return (x - x0) * k, (y - y0) * k
    ops = ["0.35 w 0 0 0 RG 0 0 0 rg"]
    for pr in prims:
        if pr[0] in ("cut", "fold"):
            pts = [tp(*p) for p in pr[1]]
            ops.append(("[] 0 d " if pr[0] == "cut" else "[4 2] 0 d ") + "%.2f %.2f m " % pts[0] +
                       " ".join("%.2f %.2f l" % p for p in pts[1:]) + " S")
        elif pr[0] == "circle_cut":
            cx, cy = tp(*pr[1])
            r = pr[2] * k
            q = 0.5523 * r
            ops.append("[] 0 d %.2f %.2f m %.2f %.2f %.2f %.2f %.2f %.2f c %.2f %.2f %.2f %.2f %.2f %.2f c "
                       "%.2f %.2f %.2f %.2f %.2f %.2f c %.2f %.2f %.2f %.2f %.2f %.2f c S" % (
                           cx + r, cy, cx + r, cy + q, cx + q, cy + r, cx, cy + r, cx - q, cy + r, cx - r, cy + q,
                           cx - r, cy, cx - r, cy - q, cx - q, cy - r, cx, cy - r, cx + q, cy - r, cx + r, cy - q,
                           cx + r, cy))
        elif pr[0] == "text":
            px, py = tp(*pr[1])
            s, fs = pr[2], pr[3] * k
            ops.append("BT /F1 %.1f Tf %.2f %.2f Td (%s) Tj ET" % (fs, px - len(s) * fs * 0.28, py - fs * 0.35, s))
    stream = "\n".join(ops).encode("latin-1")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] /Contents 4 0 R "
             "/Resources << /Font << /F1 5 0 R >> >> >>" % (wpt, hpt)).encode(),
            b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    data = b"%PDF-1.4\n"
    offs = []
    for i, o in enumerate(objs):
        offs.append(len(data))
        data += b"%d 0 obj\n" % (i + 1) + o + b"\nendobj\n"
    xref = len(data)
    data += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs:
        data += b"%010d 00000 n \n" % o
    data += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    with open(path, "wb") as f:
        f.write(data)


# ----------------------------------------------------------------------
# RENDERS
# ----------------------------------------------------------------------
VIEWS = {   # name: (eye direction, up)
    "front": ((0, 0, 1), (0, 1, 0)), "back": ((0, 0, -1), (0, 1, 0)),
    "top": ((0, 1, 0), (0, 0, 1)), "bottom": ((0, -1, 0), (0, 0, 1)),
    "left": ((-1, 0, 0), (0, 0, 1)), "right": ((1, 0, 0), (0, 0, 1)),
    "iso-front": ((0.8, -0.9, 1.2), (0, 0, 1)), "iso-back": ((-0.8, 0.9, -1.2), (0, 0, 1)),
}


def _camera(vp, eye_dir, up):
    cam = vp.camera
    dist = 60.0
    n = math.sqrt(sum(c * c for c in eye_dir))
    cam.target = adsk.core.Point3D.create(0, 0, mm(13.8))
    cam.eye = adsk.core.Point3D.create(dist * eye_dir[0] / n, dist * eye_dir[1] / n, mm(13.8) + dist * eye_dir[2] / n)
    cam.upVector = adsk.core.Vector3D.create(*up)
    cam.isFitView = True
    vp.camera = cam
    adsk.doEvents()


def make_renders():
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    vp = app.activeViewport
    root = design.rootComponent
    out = os.path.join(CAD, "renders", "_png")
    os.makedirs(out, exist_ok=True)
    done = []
    for name, (eye, up) in VIEWS.items():
        _camera(vp, eye, up)
        vp.saveAsImageFile(os.path.join(out, name + ".png"), 1920, 1080)
        done.append(name)
    lab = [oc for oc in root.occurrences if oc.component.name == "labels"]
    if lab:
        lab[0].isLightBulbOn = True
        _camera(vp, *VIEWS["iso-front"])
        vp.saveAsImageFile(os.path.join(out, "labels.png"), 1920, 1080)
        lab[0].isLightBulbOn = False
        done.append("labels")
    # exploded: move groups apart along Z, capture, put them back
    offsets = {"trim": -12, "power": 12, "lte": 24, "wifi": 36, "carrier": 30, "ui": 48, "dock": -24}
    sub_off = {"tray": 64, "lid": -36, "bracket": 54}
    saved = []
    for oc in root.occurrences:
        targets = []
        if oc.component.name == "shell":
            targets = [(s, sub_off.get(s.component.name, 0)) for s in oc.childOccurrences]
        elif oc.component.name in offsets:
            targets = [(oc, offsets[oc.component.name])]
        for t, dz in targets:
            saved.append((t, t.transform2.copy()))
            m = t.transform2
            v = m.translation
            v.add(adsk.core.Vector3D.create(0, 0, mm(dz)))
            m.translation = v
            t.transform2 = m
    _camera(vp, (0.9, -1.0, 0.45), (0, 0, 1))
    vp.saveAsImageFile(os.path.join(out, "exploded.png"), 1920, 1080)
    done.append("exploded")
    for t, m in saved:
        t.transform2 = m
    try:
        if design.snapshots.hasPendingSnapshot:
            design.snapshots.revertPendingSnapshot()
    except Exception:
        pass
    _camera(vp, *VIEWS["iso-front"])
    msg = "Renders (PNG): " + ", ".join(done)
    print(msg)
    return msg


# ----------------------------------------------------------------------
# SAVE, SYNC
# ----------------------------------------------------------------------
def save_doc():
    app = adsk.core.Application.get()
    doc = app.activeDocument
    try:
        proj = app.data.activeProject
        proj.name
    except Exception:
        proj = None
    if proj is None:
        projs = [app.data.dataProjects.item(i) for i in range(app.data.dataProjects.count)]
        proj = next((p for p in projs if p.name == "Default Project"), projs[0] if projs else None)
    ok = doc.saveAs(DOC_NAME, proj.rootFolder, "heartsync assembly, built by heartsync_assembly.py", "")
    msg = "Saved as %s in %s: %s" % (DOC_NAME, proj.name, ok)
    print(msg)
    return msg


def sync_from_fusion():
    """Reads where the anchor parts are now (after manual moves in Fusion) and rewrites the POS
    block in this file. Moves only (X/Y, or X/Z for the LTE flex); rotations are not synced."""
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    pos = {k: list(v) for k, v in POS.items()}
    moved, notes = [], []
    idx = {"x": 0, "y": 1, "z": 2}
    for oc in root.allOccurrences:
        for i in range(oc.bRepBodies.count):
            b = oc.bRepBodies.item(i)
            nb = b.nativeObject or b
            at = nb.attributes.itemByName("heartsync", "anchor")
            if not at:
                continue
            info = json.loads(at.value)
            bb = b.boundingBox
            if info.get("corner") == "x0y1":
                now = [bb.minPoint.x * 10, bb.maxPoint.y * 10, 0]
            else:
                now = [bb.minPoint.x * 10, bb.minPoint.y * 10, bb.minPoint.z * 10]
            delta = [now[j] - info["ref"][j] for j in range(3)]
            if max(abs(d) for d in delta) < 0.01:
                continue
            key, axes = info["pos"], info["axes"]
            for slot, ax in enumerate(axes):
                pos[key][slot] = round(pos[key][slot] + delta[idx[ax]], 2)
            ignored = [a for a in "xyz" if a not in axes and abs(delta[idx[a]]) > 0.01]
            if ignored and info.get("corner") != "x0y1":
                notes.append("%s: %s move ignored (set by the stack)" % (key, "/".join(ignored)))
            moved.append("%s %s" % (key, ", ".join("%+.2f" % d for d in delta)))
    if not moved:
        msg = "sync_from_fusion: nothing moved"
        print(msg)
        return msg
    path = os.path.join(HERE, "heartsync_assembly.py")
    src = open(path, encoding="utf-8").read()
    body = "POS = {\n" + "".join('    "%s": (%s),\n' % (k, ", ".join("%.2f" % v for v in vals))
                                 for k, vals in pos.items()) + "}\n"
    src = re.sub(r"(# --- POS BEGIN ---\n).*?(# --- POS END ---)", lambda m: m.group(1) + body + m.group(2),
                 src, flags=re.S)
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    msg = "sync_from_fusion: updated %s%s" % ("; ".join(moved), ("; " + "; ".join(notes)) if notes else "")
    print(msg)
    return msg
