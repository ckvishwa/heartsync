"""
heartsync - assembly: print-accurate enclosure + internals (Fusion 360 script, Python)

Use case
  * DOCKED: stands on its BOTTOM EDGE, charging through 4 pogo pads, held by 4 magnets.
  * IN USE: lies on its BACK on the TPU ring, front up. A phone snaps onto the FRONT Qi coil
    (transmit only) under the raised Qi marking ring.

Builds (one run, rebuildable), 157 x 72.5 (ADR 0014):
  * tray: FRONT wall (fabric) with a dead-front display window (VA + 0.5), smoked PC lens on a
    foam gasket flush with the fabric, fabric-tuck groove, Qi ring groove (+ raised ring),
    touch-strip pocket from the inside (1.2 wall left), mic and light holes; TOP edge (fabric)
    with USB-C (waterproof receptacle) and 5 keys (latching mute + PWR, VOL-, VOL+, PLAY); BOTTOM
    edge with 4 sealed pogo pads and 4 magnet pockets; both ENDS as a 237-hole honeycomb, thinned
    to 1.2 mm in front of the speaker, with an ePTFE membrane; front-board bosses; LRA fin;
    4 corner bosses for M2 heat-set inserts; pogo-board bosses
  * lid (3.0, bare PETG): 1.2 mm tongue (0.15 clearance, interrupted behind the speakers),
    continuous 1 mm gasket channel, screw pads and holes (low-head screws under the back ring),
    back-ring channel, engraved ID block (text from params.csv), cell ribs
  * back ring (TPU, own STL), keypad (TPU, own STL), carrier bracket (own STL), speaker cradles
  * display: bare 3.12 in SSD1322 panel (ADR 0015) with its FPC folded behind, foam ring,
    front board behind it (ADR 0016)
  * real parts from cad/models (see REAL) and our own boards (front board, power board, carrier
    rev B tab, mute board, button strip, pogo board, GNSS ground plane) as outlines with their
    main parts; stand-ins still: Qi coil + TX board, LRA
  * the real carrier board, imported from cad/heartsync_carrier.step (rev A; rev B adds the tab)
  * checks: fit (interference), clearance rules, layout rules, grille open area, stack; then
    grouping, side names and finishes, labels (hidden)

PHASE (env HS_PHASE, default 4) rebuilds an earlier stage of the 2026-11-19 pass.

Other entry points (call on the open design after run()):
  print_checks()      thin walls (ray test) and overhangs for the print orientation
  export_all()        cad/exports/: tray/lid 3MF + STL, bracket, cradles, ring, keypad STL, STEP
  make_net()          cad/net/heartsync_net.dxf + .pdf (FRONT + TOP fabric, linked to the model)
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
DISPLAY = "3.12 bare"      # bare SSD1322 256x64 panel, dead front (ADR 0015)
GROUP = True               # group bodies into components after the checks
CARRIER = True             # import the real carrier board STEP
DOC_NAME = "HeartSync v1"
# build stage of the 2026-11-19 full pass (1 size + front, 2 real parts, 3 safety + print,
# 4 custom boards). Default 4 = everything; the runner sets HS_PHASE to rebuild an earlier stage.
PHASE = int(os.environ.get("HS_PHASE", "4"))

# One place for the finishes (hex colours)
PALETTE = {
    "shell_fabric": "#CBBFAE",   # fabric on the FRONT and the TOP edge
    "front_panel": "#CBBFAE",    # FRONT finish = fabric
    "petg_bare": "#1A1A1A",      # BACK, BOTTOM edge, ENDS and inside faces (the tray filament)
    "oled_glass": "#050505",
    "lens": "#101012",           # smoked polycarbonate dead-front lens
    "ring_inlay": "#BFB3A2",     # Qi marking ring, raised under the fabric (no gold inlay)
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
RING_H = prm("ring_height", 1.0)

# display: bare 3.12 in SSD1322 panel behind a dead-front lens (FPC tail on the bottom edge)
PANEL = (prm("display_panel_l", 88.0), prm("display_panel_w", 27.8), prm("display_panel_t", 2.15))
VA = (prm("display_va_l", 78.78), prm("display_va_w", 21.18))
VA_OFF = (prm("display_va_x", 4.61), prm("display_va_y", 2.0))
DISP_LEFT = prm("display_left", 2.5)
DISP_CY = prm("display_cy", 4.0)
WIN_M = prm("window_margin", 0.5)
LENS_T = prm("lens_thickness", 1.0)
LENS_GW = prm("lens_gasket_w", 1.5)
LENS_GT = prm("lens_gasket_t", 0.4)
TUCK_W = prm("tuck_groove_w", 1.0)
TUCK_D = prm("tuck_groove_d", 1.0)
PANEL_FOAM = prm("panel_foam", 1.45)
TOUCH_WALL = prm("touch_wall", 1.2)
PHONE_W = prm("phone_width", 77.0)
VA_PHONE_GAP = prm("va_phone_gap", 2.0)
COIL_END_GAP = prm("coil_end_gap", 3.0)

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
    "coil": (47.95, 0.00),
    "carrier": (-36.00, 30.00),
    "pd_board": (45.25, 20.25),
    "usb_c": (46.00, 0.00),
    "qi2_tx": (51.80, -17.00),
    "sim_board": (-40.25, -24.25),
    "wifi": (-17.61, -27.55),
    "gnss": (-50.00, -27.50),
    "lte": (1.80, 19.50),
    "lra": (22.25, -29.00),
    "buttons": (-54.70, 0.00),
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
CELL_X0 = CELL_CX - CELL_L / 2.0            # PCM (seal) end here at -X from phase 3 (folded inside the length)
CELL_X1 = CELL_X0 + CELL_L

COIL_CX, COIL_CY = POS["coil"]
COIL_Z0 = INNER - 2.8                       # ferrite bottom (24.8)

# panel outline (glass against the front wall inner face), VA, window, lens, groove
PAN_X0 = -LENGTH / 2.0 + DISP_LEFT
PAN_X1 = PAN_X0 + PANEL[0]
PAN_Y0, PAN_Y1 = DISP_CY - PANEL[1] / 2.0, DISP_CY + PANEL[1] / 2.0
PAN_Z0 = INNER - PANEL[2]
VA_X0, VA_X1 = PAN_X0 + VA_OFF[0], PAN_X0 + VA_OFF[0] + VA[0]
VA_Y1 = PAN_Y1 - VA_OFF[1]                  # FPC edge is the bottom (-Y) edge
VA_Y0 = VA_Y1 - VA[1]
DCX, DCY = (VA_X0 + VA_X1) / 2.0, (VA_Y0 + VA_Y1) / 2.0
WIN = (VA[0] + 2 * WIN_M, VA[1] + 2 * WIN_M)
LENS = (WIN[0] + 2 * LENS_GW, WIN[1] + 2 * LENS_GW)
LENS_REC = (LENS[0] + 2 * 0.2, LENS[1] + 2 * 0.2)       # 0.2 fit round the lens
LENS_TOP = TRAY_H + FABRIC                  # lens outer face flush with the fabric
LENS_REC_FLOOR = LENS_TOP - LENS_T - LENS_GT
GROOVE = (LENS_REC[0] + 2 * TUCK_W, LENS_REC[1] + 2 * TUCK_W)
# touch strip in a pocket from the inside (TOUCH_WALL left under it); mic and light holes
TOUCH_C, TOUCH = (-19.0, 22.5), (40.0, 5.0)
TOUCH_T = TRAY_H - TOUCH_WALL - INNER       # pocket depth = strip PCB thickness (1.0)
MIC_C, LIGHT_C = (-48.0, 20.8), (-42.5, 20.8)
MIC_HOLE, LIGHT_HOLE = 1.0, 2.0
# panel FPC tail (WEX025664B drawing): 60 wide at the panel edge, 14.0 from the panel's left edge
FPC_X0, FPC_X1 = PAN_X0 + 14.0, PAN_X0 + 74.0
# front board (ours, ADR 0016): behind the panel, backs the foam ring; left edge clear of the
# left speaker cradle
FB_X0 = -58.0
FB_Z0 = 22.8                                # front board 0.8 FR4, Z 22.8..23.6 (panel foam above)
BRK_Z = (19.3, FB_Z0 - 0.1)                 # bracket bar A (H1-H2) under the front board
BRK_BAR_Z0 = 21.4                           # bars B and C: above the Wi-Fi cable (Z 20.3) and U1
FB_BOSS_D = 3.8                             # front-wall bosses for the front board's ears (M1.6, 1.25 wall)
FB_EARS = ((-55.0, -13.6), (12.5, -12.0), (9.5, 20.0))   # bottom-left, H4 (bottom-right), top-right

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
# buttons on the TOP edge, left to right: latching mute, PWR, VOL-, VOL+, PLAY (then the LTE flex
# and the USB-C). The keys (TPU keypad) start KEY_IN inside the wall; every actuator top sits there.
# * mute PS-7054DVB (12.4 deep released) on its own small board, PCB plane at KEY_IN - 12.4
# * PTS645 tactiles on the button strip, plunger top 4.3 above it. PWR/VOL-/VOL+ turned 90 deg
#   (terminals along Z, 6 wide in X, 6.8 pitch); PLAY flat (9 wide) because it sits over U1,
#   where the strip must stay above the module (Z 18.5)
BTN_ZC = 22.2
KEY_IN = CAV_Y - 0.6 - 0.3                  # keypad sheet 0.6 on the wall + 0.3 nub: 33.15
KEY_OUT = WIDTH / 2.0 + FABRIC + 0.5        # key tops 0.5 proud of the fabric
MUTE_X = POS["buttons"][0]                  # mute centre
MUTE_PCB_Y = KEY_IN - 12.4                  # mute board face (knob top released at KEY_IN)
STRIP_Y = KEY_IN - 4.3                      # button strip face (tactile seating plane)
BUTTONS = [("mute", MUTE_X, 7.0, False)]    # (name, centre X, body width in X, turned)
_x = MUTE_X + 2.0 + 0.8                     # strip starts right of the mute knob (4 wide); 1.4 web between holes
for _n, _turn in (("pwr", True), ("vol_dn", True), ("vol_up", True), ("play", False)):
    _w = 6.0 if _turn else 9.0
    BUTTONS.append((_n, _x + _w / 2.0, _w, _turn))
    _x += _w + 0.8
BTN_X0, BTN_X1 = MUTE_X + 2.8, _x - 0.8     # button strip X range
KEY = {"mute": (4.0, 4.0), "tact": (4.0, 4.0)}   # key section X x Z (holes + 0.2 per side)

# bottom edge (dock)
POGO_X = (-12.0, -4.0, 4.0, 12.0)
POGO_BOARD = (34.0, 6.0)                    # pogo board (ours) X 34 x Z 6, 1.0 thick, ears at X +-16
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
_wx, _wy = WIFI_C[0] - (40.685 - 20.06), WIFI_C[1] - (-1.0 - 5.5)     # cable stub end (model)
_wz = INNER - WIFI_TAPE - 0.565
WIFI_STUB = 12.0                            # cable inside the antenna STEP (across the end + 1 mm)
# route: leaves the thick end along +Y, an R 9 S-bend drops it under the panel's FPC bend and the
# front board to Z 20.3, an R 8 turn runs it +X below the bracket's H2 post, a second R 8 turn
# sends it +Y over U1 into the U.FL plug. Built from arcs and lines, sampled for the spline.
COAX_Z, COAX_R1, COAX_R2 = 20.3, 9.0, 8.0


def _coax_points():
    pts = []
    x0, y0, z0 = _wx, _wy, _wz
    dz = z0 - COAX_Z
    th = math.acos(1.0 - dz / (2.0 * COAX_R1))
    n = 14
    for k in range(n + 1):                  # first arc, centre below the start
        a = th * k / n
        pts.append((x0, y0 + COAX_R1 * math.sin(a), z0 - COAX_R1 * (1 - math.cos(a))))
    ym, zm = pts[-1][1], pts[-1][2]
    for k in range(1, n + 1):               # second arc, back to level
        a = th * (1 - k / float(n))
        pts.append((x0, ym + COAX_R1 * (math.sin(th) - math.sin(a)), COAX_Z + COAX_R1 * (1 - math.cos(a))))
    y1 = pts[-1][1]
    cx, cy = x0 + COAX_R2, y1
    for k in range(1, 11):                  # turn +Y -> +X
        a = math.pi - (math.pi / 2.0) * k / 10.0
        pts.append((cx + COAX_R2 * math.cos(a), cy + COAX_R2 * math.sin(a), COAX_Z))
    yr = cy + COAX_R2
    xt = UFL[0] - COAX_R2
    for k in range(1, 4):                   # straight +X
        pts.append((cx + (xt - cx) * k / 3.0, yr, COAX_Z))
    for k in range(1, 11):                  # turn +X -> +Y
        a = -math.pi / 2.0 + (math.pi / 2.0) * k / 10.0
        pts.append((xt + COAX_R2 * math.cos(a), yr + COAX_R2 + COAX_R2 * math.sin(a), COAX_Z))
    ys = yr + COAX_R2
    ye = UFL[1] - 0.4
    for k in range(1, 5):                   # straight +Y into the plug
        pts.append((UFL[0], ys + (ye - ys) * k / 4.0, COAX_Z))
    return pts


PHONE_X0 = COIL_CX - PHONE_W / 2.0         # upright 77 wide phone centred on the coil

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


def poly_block(name, color, z0, pts, t, register=True):
    """Closed polygon (model X/Y) extruded from z0 by t."""
    try:
        sk = G["comp"].sketches.add(plane_at(z0))
        sk.isComputeDeferred = True
        lines = sk.sketchCurves.sketchLines
        first = lines.addByTwoPoints(P(*pts[0]), P(*pts[1]))
        prev = first
        for q in pts[2:]:
            prev = lines.addByTwoPoints(prev.endSketchPoint, P(*q))
        lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
        sk.isComputeDeferred = False
        sk.isVisible = False
        best = max(sk.profiles, key=lambda pr: pr.areaProperties().area)
        return new_bodies(best, t, name, color, register)
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

    # dead front: window = VA + margin, lens recess (lens + gasket), fabric-tuck groove round it
    fcut("FRONT_window", lambda s: rect(s, DCX, DCY, WIN[0], WIN[1]), WALL * 1.5)
    def groove(s):
        rounded_rect(s, DCX, DCY, GROOVE[0], GROOVE[1], 1.0 + TUCK_W)
        rounded_rect(s, DCX, DCY, LENS_REC[0], LENS_REC[1], 1.0)
    fcut("FRONT_tuck_groove", groove, TUCK_D, smallest=True)
    fcut("FRONT_lens_recess", lambda s: rounded_rect(s, DCX, DCY, LENS_REC[0], LENS_REC[1], 1.0),
         TRAY_H - LENS_REC_FLOOR)
    # touch strip pocket from the inside: TOUCH_WALL of front wall left under the strip
    try:
        s = comp.sketches.add(plane_at(INNER))
        s.isVisible = False
        rect(s, TOUCH_C[0], TOUCH_C[1], TOUCH[0] + 0.4, TOUCH[1] + 0.4)
        cut_z(s, s.profiles.item(0), TOUCH_T, tray, "FRONT_touch_pocket", up=True)
    except Exception:
        G["fails"].append("FRONT_touch_pocket")

    def ring(s):
        c = s.sketchCurves.sketchCircles
        c.addByCenterRadius(P(COIL_CX, COIL_CY), mm(RING_OD / 2.0))
        c.addByCenterRadius(P(COIL_CX, COIL_CY), mm(RING_OD / 2.0 - RING_W))
    fcut("FRONT_qi2_ring_groove", ring, RING_DEPTH, smallest=True)
    fcut("FRONT_mic_hole", lambda s: s.sketchCurves.sketchCircles.addByCenterRadius(P(*MIC_C), mm(MIC_HOLE / 2)), WALL * 1.5)
    fcut("FRONT_light_hole", lambda s: s.sketchCurves.sketchCircles.addByCenterRadius(P(*LIGHT_C), mm(LIGHT_HOLE / 2)), WALL * 1.5)

    # TOP edge: USB-C, buttons, bracket slot
    ty = WIDTH / 2.0
    uw, uh = USB[0] + 2 * FIT_USB, USB[1] + 2 * FIT_USB
    side_cut("TOP_EDGE_usb_c", tray, "y", ty,
             [("rect", (USB_X - uw / 2, USB_ZC - uh / 2), (USB_X + uw / 2, USB_ZC + uh / 2))], 6.0)
    holes = []
    for name, x, w, turn in BUTTONS:
        kx, kz = KEY["mute" if name == "mute" else "tact"]
        hx, hz = kx + 2 * FIT_BTN, kz + 2 * FIT_BTN
        holes.append(("rect", (x - hx / 2, BTN_ZC - hz / 2), (x + hx / 2, BTN_ZC + hz / 2)))
    side_cut("TOP_EDGE_buttons", tray, "y", ty, holes, 6.0)

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

    # carrier: no bosses from the front wall any more (the panel covers H3 and H4); the bracket
    # frame holds all four holes and the front board clamps it (front-wall bosses for the board's
    # ears, phase 4)
    if PHASE >= 4:
        try:
            tools = [tool_cyl(x, y, FB_Z0 + 0.8, FB_BOSS_D, INNER - FB_Z0 - 0.8 + 0.5) for (x, y) in FB_EARS]
            join(tray, tools, "INSIDE_front_board_bosses")
            cut(tray, [tool_cyl(x, y, FB_Z0 + 0.7, 1.3, 3.0) for (x, y) in FB_EARS], "INSIDE_front_board_screw_holes")
        except Exception:
            G["fails"].append("front_board_bosses")

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

    # pogo board bosses on the bottom wall (M1.6 self-tapping), phase 3
    if PHASE >= 3:
        try:
            tools = [side_body("tool", None, "y", -CAV_Y + 0.45 - 0.05, [("circle", (sx * 16.0, POGO_Z), 3.4)], 1.0,
                               register=False)[0] for sx in (-1, 1)]
            join(tray, tools, "BOTTOM_EDGE_pogo_board_bosses")
        except Exception:
            G["fails"].append("pogo_board_bosses")

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
    # Qi marking: printed ring in the groove, RING_H - RING_DEPTH proud, under the fabric
    cyl("ring_inlay", "ring_inlay", COIL_CX, COIL_CY, TRAY_H - RING_DEPTH, RING_OD - 0.1, RING_H,
        inner=RING_OD - 2 * RING_W + 0.1)
    # dead front: smoked PC lens on an adhesive foam gasket in the recess, flush with the fabric
    try:
        s = G["comp"].sketches.add(plane_at(LENS_TOP - LENS_T))
        rounded_rect(s, DCX, DCY, LENS[0], LENS[1], 0.8)
        s.isVisible = False
        new_bodies(s.profiles.item(0), LENS_T, "dead_front_lens", "lens")
        s = G["comp"].sketches.add(plane_at(LENS_REC_FLOOR))
        rounded_rect(s, DCX, DCY, LENS[0], LENS[1], 0.8)
        rect(s, DCX, DCY, WIN[0], WIN[1])
        s.isVisible = False
        new_bodies(smallest_profile(s), LENS_GT, "lens_gasket", "foam")
    except Exception:
        G["fails"].append("dead_front_lens")
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
    # seals on the front holes (phase 3): clear PC window in the light hole, flush with the fabric;
    # ePTFE acoustic membrane on the inside over the mic hole
    if PHASE >= 3:
        cyl("light_window", "lens", LIGHT_C[0], LIGHT_C[1], INNER, LIGHT_HOLE - 0.05, TRAY_H + FABRIC - INNER)
        cyl("mic_membrane", "grille_mesh", MIC_C[0], MIC_C[1], INNER - 0.2, 3.0, 0.2)
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
    """Carrier bracket (printed, own STL): a frame between the carrier and the front board with
    drop posts and press-fit pins into all four carrier holes. Bar A runs H2-H1 (X -33), bar B
    H1-H3 above U1 and over the Wi-Fi cable, bar C H3-H4. The front board, screwed to its
    front-wall bosses, clamps it; the carrier hangs on the pins (nothing rests on the cell)."""
    zt = BRK_Z[1]
    try:
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = (HOLES[h] for h in ("H1", "H2", "H3", "H4"))
        r = BOSS_D / 2.0
        bar = block("carrier_bracket", "petg_bare", x1, (y2 - r + y1 + r) / 2.0, BRK_Z[0], 5.0, y1 - y2 + 2 * r,
                    zt - BRK_Z[0])[0]
        tools = [tool_block((x1 + x3) / 2.0, (y1 + y3) / 2.0 - 0.5, BRK_BAR_Z0, x3 - x1, 3.0, zt - BRK_BAR_Z0),
                 tool_block((x3 + x4) / 2.0, (y3 + y4) / 2.0, BRK_BAR_Z0, abs(x4 - x3) + 3.0, y3 - y4, zt - BRK_BAR_Z0)]
        for h in ("H1", "H2", "H3", "H4"):
            hx, hy = HOLES[h]
            tools.append(tool_cyl(hx, hy, PCB_TOP, BOSS_D, zt - PCB_TOP))
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
    # LiPol LP1160100 at its MAX envelope (101 x 60.5 x 11.3). From phase 3 the PCM (seal) end and
    # the leads face -X, so the PD board over the +X (folded) end does not overhang the seal end
    if PHASE >= 3:
        place_step("cell", "cell", ("X", "Y", "Z"), (0.0, 0.0, 0.0), (CELL_X0, CELL_CY, Z_CELL))
        build_cell_frame()
    else:
        place_step("cell", "cell", ("-X", "-Y", "Z"), (0.0, 0.0, 0.0), (CELL_X1, CELL_CY, Z_CELL))
    block("cell_insulator", "insul", CELL_CX, CELL_CY, CELL_TOP, CELL_L, CELL_W, INSUL)
    for b in block("keepout_swell_gap", "red", CELL_CX, CELL_CY, CELL_TOP + INSUL, CELL_L, CELL_W, SWELL):
        b.isLightBulbOn = False

    # Amphenol 124019572112A: mouth (+X in the file) toward the TOP wall, rim on the gasket
    place_step("usb_c", "usb_c", ("Y", "-X", "Z"), (-2.75, 13.0, 0.0), (USB_X, CAV_Y - 0.8, USB_ZC))
    if PHASE >= 4:
        build_power_board()
    else:
        # PD board stand-in top-right, USB-C on the TOP edge; hot parts off the cell (X > 46)
        px, py = POS["pd_board"]
        block("pd_board", "pcb", px, py, ABOVE, 21.5, 24.5, PCB_T)
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


# custom power board (ours, ADR 0016): IP5328P reference design shaped to its slot, USB-C in a
# cut-out (mid-mount), hot parts at X >= 48 (past the cell's folded end at 46.5)
PD_OUTLINE = [(34.5, 8.0), (56.0, 8.0), (56.0, 32.5), (52.3, 32.5), (52.3, 26.0), (39.7, 26.0),
              (39.7, 32.5), (34.5, 32.5)]
PD_PARTS = [  # name, colour, centre X, Y, size X, Y, Z (all on the top face)
    ("pd_ip5328p", "chip", 52.0, 19.2, 6.0, 6.0, 0.9),          # QFN40 6 x 6
    ("pd_inductor", "ferrite", 52.0, 11.8, 7.0, 7.0, 3.0),      # 2.2 uH, 7 x 7 x 3
    ("pd_sense_r", "passive", 49.0, 23.5, 2.0, 1.25, 0.6),      # 10 mOhm 0805
    ("pd_mosfet", "chip", 53.8, 24.0, 3.3, 3.3, 1.0),           # output switch, DFN 3.3
    ("pd_cap_in", "passive", 42.5, 14.5, 3.2, 1.6, 1.6),
    ("pd_cap_out1", "passive", 42.5, 17.5, 3.2, 1.6, 1.6),
    ("pd_cap_out2", "passive", 42.5, 20.5, 3.2, 1.6, 1.6),
    ("pd_sw_qi", "chip", 54.3, 28.0, 3.0, 3.0, 1.1),            # Qi TX load switch (input-fed), off the cell
    ("pd_sw_dock", "chip", 54.3, 31.0, 3.0, 2.6, 1.1),          # dock pad switch, reverse-blocking, off the cell
    ("pd_conn_cell", "conn", 37.25, 24.0, 4.5, 9.9, 4.8),       # JST PH S3B-PH-SM4-TB (SMD, side entry): no pins toward the cell
    ("pd_conn_carrier", "conn", 36.7, 13.5, 4.25, 10.0, 2.95),  # JST SH SM08B to carrier J1
    ("pd_conn_dock_qi", "conn", 43.8, 10.2, 8.0, 4.25, 2.95),   # JST SH SM04B: dock in, Qi TX out
]


def build_power_board():
    poly_block("pd_board", "pcb", ABOVE, PD_OUTLINE, PCB_T)
    for n, c, x, y, w, h, t in PD_PARTS:
        block(n, c, x, y, PCB_TOP, w, h, t)


CELL_FOAM, RIB_T = 1.5, 1.2
CELL_SIDE_X = ((-48.0, -38.0), (-10.0, 0.0), (14.0, 24.0))    # side pads and ribs (clear of magnets)
LEAD_Y = (15.5, 26.5)                       # lead notch at the PCM end (leads at Y 17 / 21 / 25)


def build_cell_frame():
    """Cell held in X and Y by 1.5 mm foam bearing on printed ribs that grow from the lid (no hard
    edge at the cell): full-width ribs at both ends (lead notch at the PCM end), short low ribs
    on the long sides with the lead and dock-wire channels above them. Z: foam pad below on
    stretch-release adhesive strips (no heat to open); the 1.2 swell gap above stays free."""
    yh = CELL_W / 2.0
    z1 = CELL_TOP
    ribs = []
    # ends: foam + rib, PCM end (-X) split round the lead notch
    for x_face, sgn in ((CELL_X0, -1), (CELL_X1, 1)):
        spans = [(-yh + 2.0, LEAD_Y[0]), (LEAD_Y[1], yh - 1.0)] if sgn < 0 else [(-yh + 2.0, yh - 2.0)]
        for k, (y0, y1) in enumerate(spans):
            xf = x_face + sgn * CELL_FOAM / 2.0
            block("cell_foam_end_%s%d" % ("L" if sgn < 0 else "R", k + 1), "foam", xf, (y0 + y1) / 2.0,
                  Z_CELL, CELL_FOAM - 0.05, y1 - y0, CELL_T)
            xr = x_face + sgn * (CELL_FOAM + RIB_T / 2.0)
            ribs.append(tool_block(xr, (y0 + y1) / 2.0, -0.1, RIB_T, y1 - y0, z1 + 0.1))
    # long sides: foam pads to full height, ribs only to Z 6 (wires run above them)
    for x0, x1 in CELL_SIDE_X:
        for sy in (-1, 1):
            block("cell_foam_side", "foam", (x0 + x1) / 2.0, sy * (yh + CELL_FOAM / 2.0), Z_CELL,
                  x1 - x0, CELL_FOAM - 0.05, CELL_T)
            ribs.append(tool_block((x0 + x1) / 2.0, sy * (yh + CELL_FOAM + RIB_T / 2.0), -0.1,
                                   x1 - x0, RIB_T, 6.1))
    G["cell_ribs"] = ribs


CAR_TAB = (-40.0, -5.5, -31.5, -15.05)      # carrier rev B tab (X0, X1, Y0, Y1), ADR 0016
CAR_TAB_PARTS = [  # name, colour, centre X, Y, size X, Y, Z (top face)
    ("sim7080g_module", "metal", -27.7, -23.35, 17.6, 15.7, 2.4),   # LCC module on the carrier
    ("nano_sim_holder", "metal", -11.8, -24.5, 12.5, 13.0, 1.4),    # push-push nano-SIM (1.8 V SIM)
    ("ufl_gnss", "gold", -38.3, -29.5, 3.0, 3.0, 1.25),
    ("ufl_lte", "gold", -7.0, -16.5, 3.0, 3.0, 1.25),
    ("sim_vbat_cap", "passive", -38.2, -18.8, 3.2, 2.6, 1.9),       # 100 uF at the VBAT pins
]


def build_lte_gnss():
    if PHASE >= 4:
        x0, x1, y0, y1 = CAR_TAB
        block("carrier_tab_revB", "pcb", (x0 + x1) / 2.0, (y0 + y1) / 2.0, ABOVE, x1 - x0, y1 - y0, PCB_T)
        for n, c, x, y, w, h, t in CAR_TAB_PARTS:
            block(n, c, x, y, PCB_TOP, w, h, t)
    else:
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
    # bare 3.12 in SSD1322 panel: glass on the front wall inner face behind the window
    build_display()
    block("touch_strip_pcb", "copper", TOUCH_C[0], TOUCH_C[1], INNER, TOUCH[0], TOUCH[1], TOUCH_T)
    if PHASE >= 4:
        build_front_board()
    else:
        # Adafruit 6049 (ICS-43434, bottom port): board underside toward the front-wall hole,
        # 0.3 foam gasket; mic centre on the hole
        place_step("mic", "mic", ("-X", "Y", "-Z"), (8.255, 7.11, 0.0), (MIC_C[0], MIC_C[1], INNER - 0.3))
        # Adafruit 5378 right-angle VEML7700: board at right angles to the front wall, sensor
        # (file +Y edge) looking out through the light hole
        place_step("light", "light", ("X", "Z", "-Y"), (12.69, 17.65, 2.82), (LIGHT_C[0], LIGHT_C[1], INNER - 0.1))

    build_buttons()

    # haptic LRA glued to the fin (disc in the YZ plane)
    lx, ly = POS["lra"]
    side_body("haptic_lra_10mm", "metal", "x", lx, [("circle", (ly, 21.0), 10.0)], 3.5)

    # Wi-Fi FlexPIFA 001-0014 on the FRONT wall: adhesive (element) face on the tape, foam end
    # and cable at -X (turned 180 deg about Z)
    place_step("wifi_flexpifa", "wifi", ("-X", "-Y", "Z"), (20.06, 5.5, 2.5), (WIFI_C[0], WIFI_C[1], INNER - WIFI_TAPE))
    block("wifi_tape", "white", WIFI_C[0], WIFI_C[1], WIFI_Z0 + WIFI[2], WIFI[0], WIFI[1], WIFI_TAPE)
    wifi_coax()


FB_OUTLINE = [(-58.0, -9.9), (-57.0, -9.9), (-57.0, -15.4), (-53.0, -15.4), (-53.0, -9.9), (10.5, -9.9),
              (10.5, -14.0), (14.5, -14.0), (14.5, -5.0), (12.0, -5.0), (12.0, 17.9), (11.5, 17.9),
              (11.5, 22.0), (7.5, 22.0), (7.5, 17.9), (-38.6, 17.9), (-38.6, 22.2), (-50.2, 22.2),
              (-50.2, 17.0), (-58.0, 17.0)]
FB_TOP = [  # name, colour, centre X, Y, size X, Y, Z (on the front face, toward the panel)
    ("fe_fpc_conn", "conn", -32.0, 6.35, 19.4, 3.5, 1.0),       # Hirose FH19C-30S-0.5SH class
    ("fe_boost_ic", "chip", -6.0, 9.0, 3.0, 3.0, 1.1),          # 12-15 V OLED VCC boost, SOT-23-6
    ("fe_boost_l", "ferrite", -1.5, 9.0, 2.5, 2.0, 1.2),        # 10 uH 2520
    ("fe_boost_c1", "passive", -6.0, 4.5, 2.0, 1.25, 1.0),
    ("fe_boost_c2", "passive", -1.5, 4.5, 2.0, 1.25, 1.0),
    ("fe_veml7700", "black", LIGHT_C[0], LIGHT_C[1], 6.8, 2.35, 3.0),   # top-looking, 6.8 x 2.35 x 3.0
]
FB_BACK = [  # on the back face (toward the carrier), hanging down from the board
    ("fe_ics43434", "chip", MIC_C[0], MIC_C[1], 3.5, 2.65, 0.98),      # bottom port through the board
    ("fe_carrier_conn", "conn", -3.0, 13.4, 13.0, 4.9, 2.0),          # 18-way 0.5 FPC to carrier J16
]


def build_front_board():
    """Front board (ours, ADR 0016), 0.8 FR4 behind the panel: backs the panel foam ring, takes
    the panel FPC, makes the OLED VCC, carries the mic and the light sensor behind their holes,
    and has one 18-way flex to the carrier (replaces J8, J10, J11). Screwed at three ears to
    front-wall bosses; it clamps the carrier bracket."""
    poly_block("front_board", "pcb", FB_Z0, FB_OUTLINE, 0.8)
    zt = FB_Z0 + 0.8
    for n, c, x, y, w, h, t in FB_TOP:
        block(n, c, x, y, zt, w, h, t)
    for n, c, x, y, w, h, t in FB_BACK:
        block(n, c, x, y, FB_Z0 - t, w, h, t)
    # mic port: foam tube from the board to the membrane on the wall; light: foam ring round the hole
    cyl("fe_mic_gasket", "foam", MIC_C[0], MIC_C[1], zt, 2.6, INNER - 0.2 - zt, inner=1.0)
    cyl("fe_light_gasket", "foam", LIGHT_C[0], LIGHT_C[1], zt + 3.0, 3.6, INNER - zt - 3.0 - 0.02, inner=2.2)


def build_buttons():
    """Latching mute on its own board, four PTS645 on the button strip, keys through the top wall
    (TPU keypad from phase 3 on). All actuator tops at KEY_IN."""
    zc = BTN_ZC
    for name, x, w, turn in BUTTONS:
        if name == "mute":
            # G-Switch PS-7054DVB-6PL: case 7, knob 4 x 3 to 12.4 (released), pins 3.5 below
            block("mute_board", "pcb", x + 0.2, MUTE_PCB_Y - 0.5, zc - 4.0, 7.4, 1.0, 8.0)
            place_step("btn_mute", "latch", ("X", "-Z", "Y"), (0.0, 0.0, 0.0), (x, MUTE_PCB_Y, zc))
        else:
            # C&K PTS645SM43SMTR92: plunger top 4.3 above the strip
            axes = ("Z", "X", "Y") if turn else ("X", "-Z", "Y")
            place_step("btn_" + name, "tact", axes, (0.0, 0.0, 0.0), (x, STRIP_Y, zc))
    # strip: stepped outline (taller where the turned switches sit, above U1 under PLAY)
    xp = BUTTONS[-1][1] - BUTTONS[-1][2] / 2.0 - 0.4        # step at the PLAY switch
    lo, hi = zc - 4.6, zc + 4.6
    lo2, hi2 = zc - 3.2, zc + 3.2
    side_body("button_strip_pcb", "pcb", "y", STRIP_Y - 0.4,
              [("poly", [(BTN_X0, lo), (xp, lo), (xp, lo2), (BTN_X1 + 0.2, lo2), (BTN_X1 + 0.2, hi2),
                         (xp, hi2), (xp, hi), (BTN_X0, hi)])], 0.8)
    if PHASE < 3:
        for name, x, w, turn in BUTTONS:
            kx, kz = KEY["mute" if name == "mute" else "tact"]
            block("btn_%s_cap" % name, "mute_cap" if name == "mute" else "buttons", x, (KEY_IN + KEY_OUT) / 2.0,
                  zc - kz / 2.0, kx, KEY_OUT - KEY_IN, kz)
        return
    # seal: one TPU keypad (own STL). A 0.6 sheet on the wall's inner face covers all five holes;
    # each key is a plug through its hole, 0.5 proud of the fabric, with a 0.3 nub on the inside
    # that the actuator pushes. The sheet perimeter is held on the wall by a PSA ring (peels off cold).
    sx0, sx1 = MUTE_X - 4.3, BTN_X1 + 1.5
    try:
        sheet = side_body("button_keypad_tpu", "buttons", "y", CAV_Y - 0.3,
                          [("rect", (sx0, zc - 4.0), (sx1, zc + 4.0))], 0.6)[0]
        tools = []
        for name, x, w, turn in BUTTONS:
            kx, kz = KEY["mute" if name == "mute" else "tact"]
            tools += side_body("tool", None, "y", (CAV_Y - 0.1 + KEY_OUT) / 2.0,
                               [("rect", (x - kx / 2.0, zc - kz / 2.0), (x + kx / 2.0, zc + kz / 2.0))],
                               KEY_OUT - CAV_Y + 0.1, register=False)
            tools += side_body("tool", None, "y", KEY_IN + 0.2,
                               [("rect", (x - 1.5, zc - 1.5), (x + 1.5, zc + 1.5))], 0.4, register=False)
        join(sheet, tools, "TOP_EDGE_keypad")
    except Exception:
        G["fails"].append("button_keypad_tpu")


def build_display():
    """Bare panel on the front wall inner face; foam ring behind it (compressed between the
    panel and the front board); a foam pad on the left speaker's top carries the panel's left
    end, which sits over the speaker."""
    cx, cy = (PAN_X0 + PAN_X1) / 2.0, DISP_CY
    if "panel" in REAL and os.path.isfile(os.path.join(MODELS, REAL["panel"][0])):
        # file frame: X 0..88, Y 0..27.8 with the FPC edge at Y 0, Z 0 = viewing face. File Z goes
        # to world -Z, so X flips to stay right-handed (the panel is symmetric in X)
        place_step("oled", "panel", ("-X", "Y", "-Z"), (0.0, 0.0, 0.0), (PAN_X1, PAN_Y0, INNER))
    else:
        block("oled", "oled_glass", cx, cy, PAN_Z0, PANEL[0], PANEL[1], PANEL[2])
    z0 = PAN_Z0 - PANEL_FOAM
    bx0, bx1 = FB_X0, PAN_X1                   # ring only where the front board backs the panel
    w = 2.5
    yt = PAN_Y1 - 0.9                          # top strip kept clear of the mute switch pins
    rects = [((bx0 + bx1) / 2.0, yt - w / 2.0, bx1 - bx0, w),
             (bx0 + w / 2.0, (PAN_Y0 + w + yt - w) / 2.0, w, yt - PAN_Y0 - 2 * w),
             (bx1 - w / 2.0, (PAN_Y0 + w + yt - w) / 2.0, w, yt - PAN_Y0 - 2 * w)]
    # bottom edge: only right of the FPC tail (the tail folds behind the panel there)
    fx1 = FPC_X1 + 0.5
    if bx1 - fx1 > 2.0:
        rects.append(((fx1 + bx1) / 2.0, PAN_Y0 + w / 2.0, bx1 - fx1, w))
    grid("panel_foam_ring", "foam", z0, rects, PANEL_FOAM)
    # foam pad on the left speaker top (panel back 25.05, speaker top 23.3)
    sz = SPK_Z0 + SPK_H
    if PAN_Z0 - sz > 0.3:
        x0, x1 = PAN_X0 + 0.5, -SPK_FACE_X + SPK_D - 0.5
        block("panel_foam_speaker", "foam", (x0 + x1) / 2.0, cy, sz + 0.05, x1 - x0, PANEL[1] - 6.0,
              PAN_Z0 - sz - 0.1)


def build_dock():
    # pogo target pads (flush with the BOTTOM face) and 6 x 2 magnets in their blind pockets
    for k, x in enumerate(POGO_X):
        place_step("pogo_pad_%d" % (k + 1), "pogo_pad", ("X", "-Z", "Y"), (0.0, 0.0, 0.0), (x, -WIDTH / 2.0, POGO_Z))
    y_lo = -CAV_Y + MAG_PAD_T - FIT_MAG - MAG_T
    for k, x in enumerate(MAG_X):
        place_step("dock_magnet_%d" % (k + 1), "magnet", ("X", "-Z", "Y"), (0.0, 0.0, 0.0), (x, y_lo, MAG_Z))
    if PHASE < 3:
        return
    # seals: silicone washer under each pad flange; the pogo board holds the pads by their tails
    for k, x in enumerate(POGO_X):
        w = side_body("pogo_seal_%d" % (k + 1), "usb_c", "y", -CAV_Y + 0.25,
                      [("circle", (x, POGO_Z), 3.9)], 0.5)
        if w:
            cut(w[0], side_body("tool", None, "y", -CAV_Y + 0.25, [("circle", (x, POGO_Z), 2.55)], 0.7,
                                register=False), "DOCK_pogo_seal_hole_%d" % (k + 1))
    ph = POGO_BOARD
    b = block("pogo_board", "pcb", 0.0, -CAV_Y + 0.9 + 0.5, POGO_Z - ph[1] / 2.0, ph[0], 1.0, ph[1])
    if b:
        cut(b[0], [side_body("tool", None, "y", -CAV_Y + 1.4, [("circle", (x, POGO_Z), 1.2)], 1.2,
                             register=False)[0] for x in POGO_X], "DOCK_pogo_board_holes")


def wifi_coax():
    comp = G["comp"]
    try:
        sk = comp.sketches.add(comp.xYConstructionPlane)
        pc = adsk.core.ObjectCollection.create()
        for p in _coax_points():
            pc.add(P(*p))
        spl = sk.sketchCurves.sketchFittedSplines.add(pc)
        sk.isVisible = False
        G["wifi_coax_mm"] = spl.length * 10.0
        try:
            ev = spl.worldGeometry.evaluator
            ok, t0, t1 = ev.getParameterExtents()
            kmax, at = 0.0, None
            for i in range(401):
                t = t0 + (t1 - t0) * i / 400.0
                okc, d, k = ev.getCurvature(t)
                if okc and k > kmax:
                    okp, pt = ev.getPointAtParameter(t)
                    kmax, at = k, pt
            G["wifi_coax_rmin"] = (10.0 / kmax if kmax > 0 else 1e9,
                                   (at.x * 10, at.y * 10, at.z * 10) if at else None)
        except Exception:
            pass
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
    "panel": ("oled_wex025664b_panel_312/wex025664b_panel_from_drawing.step", (0.0, -1.5, 0.0, 88.0, 27.8, 2.95)),
    "mic": ("mic_adafruit-6049_ics-43434/adafruit_6049_ics-43434.step", (0.0, 0.0, -0.07, 16.51, 12.70, 2.53)),
    "light": ("light_adafruit-5378_veml7700/adafruit_5378_veml7700.step", (0.0, 0.0, 0.0, 25.40, 17.78, 4.53)),
    "wifi": ("flexpifa_001-0014/flexpifa_001-0014_from_drawing.step", (0.0, -1.0, 0.0, 41.25, 11.0, 2.5)),
    "gnss": ("gnss_taoglas_sggp.12.4.a.02/sggp.12.4.a.02_from_drawing.step", (-6.0, -6.0, 0.0, 6.0, 6.0, 4.0)),
    "lte": ("lte_molex_212570-0100/212570-0100_cable_cut.step", (-0.21, -0.18, -15.21, 47.01, 1.40, 0.21)),
    "cell": ("cell_lipol_lp1160100/lp1160100_from_drawing.step", (-4.0, -30.25, 0.0, 101.0, 30.25, 11.3)),
    "pogo_pad": ("pogo_pad/pogo_pad_from_params.step", (-2.0, -2.0, 0.0, 2.0, 2.0, 4.6)),
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
EXPECTED = {("btn_mute", "mute_board"), ("fe_fpc_conn", "oled")}   # THT pins; FPC fingers in their connector
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
    # freed length (157): GNSS patch off the left speaker, PD and SIM boards off the speakers
    sim = "carrier_tab_revB" if PHASE >= 4 else "sim_board"
    rules += [("gnss_patch", "speaker_L", 3.0), ("pd_board", "speaker_cradle_R", 2.0),
              ("pd_board", "speaker_R", 2.0), (sim, "speaker_cradle_L", 2.0), (sim, "speaker_L", 2.0)]
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
    front = TRAY_H + FABRIC + (RING_H - RING_DEPTH)
    return ("Stack: lid %.1f + tray %.1f + front fabric %.1f + Qi ring %.1f under it + back ring %.1f proud = "
            "%.1f mm (limit 35; %.1f away from the ring). Cell (max %.1f) %.1f..%.1f, insulator to %.1f, swell gap "
            "%.1f to %.1f, board %.1f..%.1f, coil ferrite %.1f, front wall %.1f..%.1f, panel %.2f..%.1f, lens %.1f..%.1f "
            "(flush with the fabric). Lid: ring channel floor %.1f, gasket channel bottom %.1f -> %.1f between" % (
                LID, TRAY_H, FABRIC, RING_H - RING_DEPTH, BR_PROUD, front + LID + BR_PROUD,
                TRAY_H + FABRIC + LID + BR_PROUD, CELL_T, Z_CELL, CELL_TOP, CELL_TOP + INSUL, SWELL, ABOVE,
                ABOVE, PCB_TOP, COIL_Z0, INNER, TRAY_H, PAN_Z0, INNER, LENS_TOP - LENS_T, LENS_TOP,
                -LID + BR_CH, -GASKET_D, (-GASKET_D) - (-LID + BR_CH)))


def layout_report():
    """Front layout rules: display VA vs the phone zone, coil magnet ring vs the right end,
    left speaker vs the GNSS patch (in clearance_report), speaker_R magnet vs the coil ring."""
    ring_r = 55.0 / 2.0
    ring_x1 = COIL_CX + ring_r
    out = ["Layout:",
           "  panel X %.2f..%.2f (left edge %.2f from the left end), Y %.2f..%.2f; VA X %.2f..%.2f, Y %.2f..%.2f; "
           "window %.1f x %.1f; lens %.1f x %.1f x %.1f" % (PAN_X0, PAN_X1, PAN_X0 + LENGTH / 2.0, PAN_Y0, PAN_Y1,
                                                          VA_X0, VA_X1, VA_Y0, VA_Y1, WIN[0], WIN[1],
                                                          LENS[0], LENS[1], LENS_T),
           "  phone zone X >= %.2f (coil X %.2f, phone %.0f wide): VA ends %.2f before it (rule >= %.1f) %s" % (
               PHONE_X0, COIL_CX, PHONE_W, PHONE_X0 - VA_X1, VA_PHONE_GAP,
               "OK" if PHONE_X0 - VA_X1 >= VA_PHONE_GAP - 1e-6 else "FAIL"),
           "  coil magnet ring X %.2f..%.2f: %.2f to the right end outer face (rule >= %.1f) %s, %.2f to its inner face" % (
               COIL_CX - ring_r, ring_x1, LENGTH / 2.0 - ring_x1, COIL_END_GAP,
               "OK" if LENGTH / 2.0 - ring_x1 >= COIL_END_GAP - 1e-6 else "FAIL", CAV_X - ring_x1)]
    # speaker_R driver magnet: not in the STEP (closed box); the CMS-402008-18SP driver sits on the
    # front baffle, magnet about 6 mm behind the cone face, centred on the box
    mx, my, mz = SPK_FACE_X - 6.0, SPK_CY, SPK_Z0 + SPK_H / 2.0
    dx = max(0.0, abs(mx - COIL_CX) - ring_r) if abs(my) < 1e-6 else 0.0
    dz = (INNER - 2.0) - mz
    out.append("  speaker_R driver magnet (estimated at X %.1f, Z %.1f) to the coil magnet ring: %.1f mm" % (
        mx, mz, math.sqrt(dx * dx + dz * dz)))
    try:
        A = [b for b in G["parts"] if b.name == "qi2_magnet_ring"]
        B = imp_bodies("speaker_R")
        if A and B:
            out.append("  speaker_R box to the coil magnet ring (min): %.1f mm" % min(_dist(A[0], b) for b in B))
    except Exception:
        pass
    return "\n".join(out)


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
    if n.startswith(("back_ring", "screw_head", "usb_c_gasket", "dead_front_lens", "lens_gasket",
                     "light_window", "mic_membrane")):
        return "trim"
    if n == "cell" or n == "usb_c" or n.startswith(("cell_", "pd_", "qi2_", "keepout_")):
        return "power"
    if n.startswith(("speaker_", "grille_mesh")):
        return "speakers"
    if n in ("sim_board", "sim7080g_module", "nano_sim_holder", "lte_flex", "carrier_tab_revB", "sim_vbat_cap") \
            or n.startswith(("ufl_", "gnss_")):
        return "lte"
    if n.startswith("wifi_"):
        return "wifi"
    if n.startswith(("dock_magnet", "pogo_")):
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
           "cell": ("cell", "xy"), "usb_c": ("usb_c", "x"),
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
    lid = build_lid()
    build_trim()
    build_bracket()
    build_coil()
    build_power()
    if G.get("cell_ribs"):
        try:
            join(lid, G["cell_ribs"], "BACK_cell_ribs")
        except Exception:
            G["fails"].append("cell_ribs")
    build_lte_gnss()
    build_speakers()
    build_ui()
    build_dock()
    tag_anchors()
    if CARRIER:
        import_carrier(design)

    report = [stack_report(), layout_report(), grille_report()]
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
           "Wi-Fi cable: %.1f stub (in the antenna STEP) + %.1f routed = %.1f mm of 100; min bend radius %s\n"
           "Components: %s\nSides: %s; labels %d (hidden)\n"
           % (DISPLAY, DOCK_SIDE, LENGTH, WIDTH, THICKNESS, INNER, ABOVE, n_parts, len(G["imp"]), n_imp,
              n_carrier, WIFI_STUB, G.get("wifi_coax_mm", 0), WIFI_STUB + G.get("wifi_coax_mm", 0),
              ("%.1f mm at (%.1f, %.1f, %.1f) (rule >= 6)" % ((G["wifi_coax_rmin"][0],) + tuple(G["wifi_coax_rmin"][1]))
               if G.get("wifi_coax_rmin") and G["wifi_coax_rmin"][1] else "-"),
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
    for name, down in (("shell_tray", 1), ("shell_lid", -1), ("carrier_bracket", 0), ("speaker_cradle_L", 0),
                       ("button_keypad_tpu", 0)):
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
        # the engraved ID text: the ribs left between letters are 0.3 tall surface detail, not walls
        eng = [t for t in thin if name == "shell_lid" and abs(t[1] - ID_C[0]) <= ID_L / 2.0 + 0.1
               and abs(t[2] - ID_C[1]) <= ID_W / 2.0 + 0.1 and t[3] < -LID + ID_DEPTH + 0.5]
        thin = [t for t in thin if t not in eng]
        if eng:
            lines.append("%s: engraved ID text %d samples between letters, %.2f..%.2f mm (0.3 deep detail)" % (
                name, len(eng), min(e[0] for e in eng), max(e[0] for e in eng)))
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
                  ("speaker_cradle_R", "heartsync_speaker_cradle_R.stl"),
                  ("button_keypad_tpu", "heartsync_keypad_tpu.stl")):
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
    """Net primitives in mm: one piece, FRONT + tray TOP edge (fabric only there; back, bottom
    and ends are bare PETG). Seen from outside with the TOP strip below the FRONT panel: model +X
    is on the left. TOP strip: u = along the edge incl. the quarter-round corner wraps, v = z from
    the lid seam (0) to the top-front edge (TRAY_H, a fold). FRONT panel: u = L/2 - x,
    v = TRAY_H + W/2 - y. ("cut", pts), ("fold", pts), ("circle_cut", centre, r),
    ("mark", pts) (dashed, not cut), ("text", p, s, size)."""
    L, W, r = LENGTH, WIDTH, CORNER_R
    arc = math.pi / 2.0 * r
    prims = []

    def bu(x):
        return L / 2.0 - x

    def fv(y):
        return TRAY_H + W / 2.0 - y

    def arc_pts(c, a0, a1, rad, n=12):
        return [(c[0] + rad * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                 c[1] + rad * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]

    def rrect(cu, cv, w, h, rr):
        pts = []
        pts += arc_pts((cu + w / 2 - rr, cv - h / 2 + rr), -90, 0, rr)
        pts += arc_pts((cu + w / 2 - rr, cv + h / 2 - rr), 0, 90, rr)
        pts += arc_pts((cu - w / 2 + rr, cv + h / 2 - rr), 90, 180, rr)
        pts += arc_pts((cu - w / 2 + rr, cv - h / 2 + rr), 180, 270, rr)
        return pts + [pts[0]]

    u0, u1 = r - arc, L - r + arc            # strip incl. the corner wraps onto the ends
    H = TRAY_H
    outline = [(r, H), (u0, H), (u0, 0), (u1, 0), (u1, H), (L - r, H)]
    outline += arc_pts((L - r, H + r), -90, 0, r)[1:]
    outline += arc_pts((L - r, H + W - r), 0, 90, r)
    outline += arc_pts((r, H + W - r), 90, 180, r)
    outline += arc_pts((r, H + r), 180, 270, r)
    prims.append(("cut", outline))
    prims.append(("fold", [(r, H), (L - r, H)]))             # top-front edge
    prims.append(("fold", [(r, 0), (r, H)]))                 # corner tangent lines on the strip
    prims.append(("fold", [(L - r, 0), (L - r, H)]))

    def box(x, z, w, h):
        a, b = bu(x - w / 2), bu(x + w / 2)
        return [(a, z - h / 2), (b, z - h / 2), (b, z + h / 2), (a, z + h / 2), (a, z - h / 2)]
    prims.append(("cut", box(USB_X, USB_ZC, USB[0] + 2 * FIT_USB, USB[1] + 2 * FIT_USB)))
    for name, x, w, turn in BUTTONS:
        kx, kz = KEY["mute" if name == "mute" else "tact"]
        prims.append(("cut", box(x, BTN_ZC, kx + 2 * FIT_BTN, kz + 2 * FIT_BTN)))
    # FRONT: window opening (the fabric folds down the tuck groove's outer wall), mic and light
    # holes (sealed edges), Qi ring and touch strip as marks
    prims.append(("fold", rrect(bu(DCX), fv(DCY), GROOVE[0], GROOVE[1], 1.0 + TUCK_W)))
    prims.append(("cut", rrect(bu(DCX), fv(DCY), GROOVE[0] - 2 * TUCK_D, GROOVE[1] - 2 * TUCK_D,
                               max(1.0 + TUCK_W - TUCK_D, 0.3))))
    prims.append(("circle_cut", (bu(MIC_C[0]), fv(MIC_C[1])), MIC_HOLE / 2.0))
    prims.append(("circle_cut", (bu(LIGHT_C[0]), fv(LIGHT_C[1])), LIGHT_HOLE / 2.0))
    prims.append(("mark", arc_pts((bu(COIL_CX), fv(COIL_CY)), 0, 360, RING_OD / 2.0 - RING_W / 2.0, 72)))
    tx0, tx1 = bu(TOUCH_C[0] - TOUCH[0] / 2), bu(TOUCH_C[0] + TOUCH[0] / 2)
    ty0, ty1 = fv(TOUCH_C[1] - TOUCH[1] / 2), fv(TOUCH_C[1] + TOUCH[1] / 2)
    prims.append(("mark", [(tx0, ty0), (tx1, ty0), (tx1, ty1), (tx0, ty1), (tx0, ty0)]))
    prims.append(("text", (L / 2.0, H + W + 7), "HeartSync fabric: FRONT + TOP edge, one piece (outer face up)", 3.5))
    prims.append(("text", (L / 2.0, H + W + 2.5), "dashed: folds (top-front edge, groove) and marks (Qi ring, touch); seal hole edges", 2.5))
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
        if kind in ("cut", "fold", "mark"):
            for a, b in zip(pr[1], pr[1][1:]):
                ln = lines.addByTwoPoints(P(a[0], a[1]), P(b[0], b[1]))
                if kind != "cut":
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
        if pr[0] in ("cut", "fold", "mark"):
            xs += [p[0] for p in pr[1]]
            ys += [p[1] for p in pr[1]]
    m = 15.0
    x0, y0 = min(xs) - m, min(ys) - m
    wpt, hpt = (max(xs) - min(xs) + 2 * m) * k, (max(ys) - min(ys) + 2 * m) * k

    def tp(x, y):
        return (x - x0) * k, (y - y0) * k
    ops = ["0.35 w 0 0 0 RG 0 0 0 rg"]
    for pr in prims:
        if pr[0] in ("cut", "fold", "mark"):
            pts = [tp(*p) for p in pr[1]]
            ops.append({"cut": "[] 0 d ", "fold": "[4 2] 0 d ", "mark": "[1 2] 0 d "}[pr[0]] + "%.2f %.2f m " % pts[0] +
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
