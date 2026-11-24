"""
Ansonia rev G - digital clone of the device (Fusion 360, direct modelling, Python API).

190 x 76 x 35.5, Dayton CE70-30P-8 end speakers, 2 x USB-C on the top edge, e-paper in the lid, no screws
(gasket + 8 snap clips + a hook at each end). Built to catch clashes before printing.

Sources (the truth): docs/hardware/fit/ansonia_net_revG (outside), ansonia_fitmap_revG (inside),
bom_revG.md (parts + positions), Hardware/pcb/* (boards, exported by export_boards.sh to cad/boards/*.step).
Dimensions: cad/params_revG.csv (falls back to D below and lists every missing row).

Axes: origin = device centre, +X right end, +Y TOP edge, Z 0 = lid inner face, front outer face Z 32.5,
back outer face Z -3.0. Sizes in mm.

Entry points (call on a NEW empty design; the runner run_revG.py does this and writes reports to files):
  build(report)        whole model + every check -> report file (text)
  exports(out_dir)     3MF per printable part (oriented for the Bambu A1), assembly STEP, .f3d
  screenshots(out_dir) exploded, section through the middle, section through speaker L, back with the e-paper
The board STEPs are imported as they are: rerun export_boards.sh after a placement change, then build() again.
"""
import adsk.core
import adsk.fusion
import csv
import json
import math
import os
import time
import traceback

HERE = os.path.dirname(os.path.abspath(globals().get("__file__", ".")))
CAD = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(CAD, ".."))
MODELS = os.path.join(CAD, "models")
BOARDS = os.path.join(CAD, "boards")

# ----------------------------------------------------------------------------------------------- params
D = {
    "length": 190.0, "width": 76.0, "z_front": 32.0, "z_inner": 30.3, "lid_t": 3.0, "wall": 2.2, "corner_r": 6.0,
    "fit": 0.2,
    # front
    "win_x0": -68.9, "win_x1": 10.9, "win_y0": -7.1, "win_y1": 15.1,
    "lens_pocket_margin": 1.0, "lens_pocket_d": 0.8, "tuck_w": 1.0, "tuck_d": 1.0, "lens_t": 1.0, "fabric": 0.6,
    "qi_x": 43.5, "qi_ring_od": 56.0, "qi_ring_id": 54.0, "qi_ring_h": 0.4,
    "mic_x": -69.5, "mic_y": 31.25, "mic_d": 1.0, "gest_x": -64.0, "gest_y": 31.25, "gest_w": 5.0, "gest_h": 3.5,
    "touch_x0": -56.0, "touch_x1": -16.0, "touch_y0": 27.25, "touch_y1": 32.25, "touch_wall": 1.2,
    # ends
    "grille_d": 1.6, "grille_pitch": 2.5, "grille_ny": 27, "grille_nz": 11, "grille_z0": 2.8,
    "grille_wall": 1.2, "eptfe_y": 68.8, "eptfe_z": 29.6, "eptfe_t": 0.2,
    "trim_y_out": 71.2, "trim_z0": -0.3, "trim_z1": 30.9, "trim_y_in": 68.8, "trim_zi0": 0.5, "trim_zi1": 30.1, "trim_t": 0.6,
    # top edge
    "strip_x0": -70.2, "strip_x1": -18.6, "strip_zc": 21.0, "strip_h": 9.2, "strip_pocket_d": 0.8, "icon_h": 0.6,
    "key_x0": -64.0, "key_pitch": 9.8, "rib_w": 2.0, "win_inset": 1.5,
    "usb1_x": 52.75, "usb2_x": 66.05, "usb_zc": 16.05, "usb_open_w": 10.8, "usb_open_h": 4.2, "usb_inset": 0.25,
    # bottom edge
    "pogo_z": 13.8, "pogo_hole_d": 2.7, "mag_z": 7.0, "mag_skin": 1.6, "mag_d": 6.0, "mag_t": 2.0,
    # lid
    "tongue_h": 2.5, "tongue_w": 2.0, "groove_w": 1.6, "groove_d": 0.95, "groove_z0": 0.45, "cord_d": 1.5,
    "clip_w": 6.0, "clip_t": 1.2, "clip_y_in": 32.0, "clip_h": 5.0, "hook_h": 1.0, "hook_out": 0.8,
    "ledge_z0": 2.7, "ledge_z1": 4.0, "ledge_y_in": 33.4,
    "end_hook_x0": 90.8, "end_hook_x1": 92.6, "end_hook_y": 4.0, "end_hook_h": 5.0,
    "pry_x0": 89.0, "pry_x1": 91.5, "pry_y0": 9.0, "pry_y1": 15.0, "pry_floor": -1.0,
    "ep_x0": -60.3, "ep_x1": 36.32, "ep_y": 56.24, "ep_t": 0.92, "ep_pocket_d": 1.1, "ep_aa_x": 86.4, "ep_aa_y": 51.84,
    "ep_cover_t": 0.5, "ep_cover_margin": 1.5,
    "plate_x0": 68.0, "plate_x1": 86.0, "plate_y": 52.0, "plate_t": 0.8, "plate_r": 2.0,
    "ring_w": 4.0, "ring_inset": 2.5, "ring_r": 6.0, "ring_channel": 1.0, "ring_proud": 1.5,
    # stack
    "cell_x0": -54.5, "cell_x1": 46.5, "cell_w": 60.5, "cell_t": 11.3, "cell_pad": 1.0, "insul": 0.2, "swell": 1.2,
    "board_z": 13.7,
    # speakers (Dayton CE70-30P-8: 70 x 30 x 19.5, flange / basket / magnet from a typical racetrack drawing: VERIFY)
    "spk_face_x": 92.8, "spk_back_x": 73.3, "spk_l": 70.0, "spk_h": 30.0, "spk_z0": 0.25, "spk_flange_t": 2.0,
    "spk_basket_l": 60.0, "spk_basket_h": 20.0, "spk_basket_x": 80.0, "spk_magnet_d": 24.0, "spk_hole_d": 3.2,
    "spk_hole_y": 29.0, "spk_hole_dz": 8.0,
    "box_y": 33.4, "box_wall": 1.2, "box_back": 1.5, "box_gasket": 1.0, "box_open_l": 62.0, "box_open_h": 22.0,
    # Qi
    "qi_mag_t": 1.0, "qi_mag_od": 56.0, "qi_mag_id": 44.0, "qi_coil_d": 50.0, "qi_coil_id": 20.0, "qi_coil_t": 1.0,
    "qi_ferrite_t": 0.8, "qi_tx_x": 67.5, "qi_tx_t": 2.0, "qi_tx_y0": -32.0, "qi_tx_y1": 0.0, "qi_tx_z0": 2.0, "qi_tx_z1": 26.0,
    # haptic (Vybronics VLV101040A: 10 x 10 x 4.0 per vybronics.com; brief said 10 x 40 x 10)
    "lra_x0": -70.0, "lra_x1": -60.0, "lra_w": 10.0, "lra_t": 4.0,
    # antennas
    "wifi_x0": -52.0, "wifi_x1": -11.9, "wifi_y0": -34.8, "wifi_y1": -23.8,
    "gnss_x0": -72.0, "gnss_x1": -56.0, "gnss_y0": -35.75, "gnss_y1": -22.75, "gnss_gnd_t": 0.8,
    "lte_x0": -14.0, "lte_x1": 28.0, "lte_z0": 11.9, "lte_z1": 30.0, "lte_t": 0.3,
    "bt_x0": 38.0, "bt_x1": 64.0, "bt_z0": 15.0, "bt_z1": 28.0, "bt_t": 0.3,
    # front boards
    "fs_z": 28.15, "touch_z": 30.0,
    # buttons
    "btn_pcb_y": 30.6, "btn_pcb_t": 0.8, "sw_body": 6.0, "sw_body_h": 3.5, "sw_h": 4.3, "sw_plunger_d": 3.5, "nub_d": 3.0,
    # carrier bracket
    "post_d": 5.0, "bar_w": 4.0, "bar_z0": 25.6, "bar_z1": 27.0, "short_post_z1": 27.0,
    "screw_head_d": 3.8, "screw_head_h": 1.3, "screw_d": 2.0, "screw_l": 6.0,
    # power-board posts on the lid
    "ppost_d": 4.0,
}
PARAM_NOTES = []


def _load():
    p = os.path.join(CAD, "params_revG.csv")
    vals = {}
    if os.path.isfile(p):
        with open(p, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    vals[row["name"].strip()] = float(row["value"])
                except (KeyError, ValueError):
                    PARAM_NOTES.append("bad row %r" % row)
    else:
        PARAM_NOTES.append("params_revG.csv missing: using the defaults in ansonia_revG.py")
    for k in D:
        if k not in vals:
            if os.path.isfile(p):
                PARAM_NOTES.append("%s not in params_revG.csv (default %g)" % (k, D[k]))
            vals[k] = D[k]
    return vals


Q = _load()
L2, W2 = Q["length"] / 2.0, Q["width"] / 2.0          # 95, 38
ZF, ZI, LT, WALL, R = Q["z_front"], Q["z_inner"], Q["lid_t"], Q["wall"], Q["corner_r"]
IX, IY = L2 - WALL, W2 - WALL                         # 92.8, 35.8 inner faces
IR = R - WALL                                          # 3.8 inner corner radius
KEYS = [Q["key_x0"] + Q["key_pitch"] * i for i in range(5)]
CLIP_X = (-50.0, -10.0, 20.0, 50.0)
POGO_X = (-12.0, -4.0, 4.0, 12.0)
MAG_X = (-70.0, -32.0, 32.0, 70.0)
HOLES = {"H1": (-41.0, 20.5), "H2": (-41.0, 4.0), "H3": (-9.0, 16.0), "H4": (9.0, -12.5)}
PPOSTS = ((50.0, 10.0), (64.5, -1.0), (69.5, 30.0), (56.0, 31.0))     # clear of the MR30 pocket and back-side parts
# Option B (2026-11-23): sealed back-box chambers in the free layer above the boards, glued + gasketed to each
# speaker box's back wall. outer/inner = (x0, x1, y0, y1); inner boxes overlap so the cavity is one volume and
# run 1 mm past the open end. 5 mm from all antennas, 0.5 under the Qi ferrite, clear of the OLED FPC drop.
CH_WALL = 1.2
CH = {
    "L": dict(z=(18.9, 27.05), joint_x=-71.3,
              outer=[(-71.3, -37.0, -17.0, 22.5), (-37.0, -26.0, -8.5, 22.5)],
              inner=[(-72.3, -38.2, -15.8, 21.3), (-39.0, -27.2, -7.3, 21.3)],
              joint=(-15.8, 21.3), joint_outer=(-17.0, 22.5),
              pillars=[(-62.0, -6.0), (-62.0, 9.0), (-50.0, -6.0), (-50.0, 9.0), (-32.0, 3.0), (-32.0, 15.0)],
              bosses=["H1", "H2"]),
    "R": dict(z=(19.3, 27.0), joint_x=71.3,
              outer=[(29.0, 71.3, 0.5, 30.4), (33.0, 70.1, 30.4, 35.4), (29.0, 67.0, -30.3, 0.5)],
              inner=[(30.2, 72.3, 1.7, 29.2), (34.2, 68.9, 29.0, 34.2), (30.2, 65.8, -29.1, 2.0)],
              joint=(1.7, 29.2), joint_outer=(0.5, 30.4),
              pillars=[(40.0, 9.0), (52.0, 9.0), (64.0, 9.0), (40.0, 21.0), (52.0, 21.0), (64.0, 21.0),
                       (40.0, -9.0), (52.0, -9.0), (40.0, -21.0), (52.0, -21.0), (62.0, -15.0)],
              bosses=[]),
}
# board parts changed in CAD only (the PCB change is for the board session): MR30 J4 off the power board,
# J7 PH -> JST SH 2-pin (SM02B-SRSS-TB body 6.0 x 4.25 x 2.95, cable +X)
OVERRIDE = {("power", "J4"): None,
            ("power", "J7"): dict(x0=64.85, x1=69.1, y0=6.0, y1=12.0, h=2.95, side="F")}
# mated MR30 pair (battery male + pigtail female) in the pocket beside the cell, along Y: 16 x 26.5 x 8 assumed (verify)
MR30_PAIR = (51.0, 67.0, -30.0, -3.5, 0.5, 8.5)
BOARD_T = {"carrier": 1.0, "power": 1.6, "front_sensor": 0.8, "front_touch": 0.8}
BOARD_Z = {"carrier": Q["board_z"], "power": Q["board_z"], "front_sensor": Q["fs_z"], "front_touch": Q["touch_z"]}

# real STEP files: (path under cad/models, local bbox x0, y0, z0, x1, y1, z1)
REAL = {
    "usb_c": ("usbc_amphenol_124019572112a/124019572112a.step", (-9.76, 6.90, -2.15, -1.90, 19.10, 2.15)),
    "panel": ("oled_wex025664b_panel_312/wex025664b_panel_from_drawing.step", (0.0, -1.5, 0.0, 88.0, 27.8, 2.95)),
    "wifi": ("flexpifa_001-0014/flexpifa_001-0014_from_drawing.step", (0.0, -1.0, 0.0, 41.25, 11.0, 2.5)),
    "gnss": ("gnss_taoglas_sggp.12.4.a.02/sggp.12.4.a.02_from_drawing.step", (-6.0, -6.0, 0.0, 6.0, 6.0, 4.0)),
    "cell": ("cell_lipol_lp1160100/lp1160100_from_drawing.step", (-4.0, -30.25, 0.0, 101.0, 30.25, 11.3)),
    "pogo_pad": ("pogo_pad/pogo_pad_from_params.step", (-2.0, -2.0, 0.0, 2.0, 2.0, 4.6)),
    "magnet": ("magnet_6x2/magnet_6x2_from_drawing.step", (-3.0, -3.0, 0.0, 3.0, 3.0, 2.0)),
}
AX = {"X": (1, 0, 0), "-X": (-1, 0, 0), "Y": (0, 1, 0), "-Y": (0, -1, 0), "Z": (0, 0, 1), "-Z": (0, 0, -1)}

# material per part (component name prefix) -> (density g/cm3, colour, printable material or None)
MAT = {
    "front_shell": (1.27, "#EFEBE3", "PETG"), "lid": (1.27, "#E4DED3", "PETG"), "speaker_box": (1.27, "#9C978C", "PETG"),
    "bracket": (1.27, "#A9C48A", "PETG"), "button_strip": (1.21, "#2C2C2A", "TPU"), "back_ring": (1.21, "#3A3A38", "TPU"),
    "trim": (1.24, "#B8902F", "PLA silk (brass tone)"), "sig_plate": (1.24, "#C9A227", "PLA silk (brass tone) or 0.8 brass sheet"),
    "lens": (1.20, "#1A1A1A", None), "ir_window": (1.20, "#5A3E6B", None), "epaper_cover": (1.20, "#D8ECF3", None),
    "gasket_cord": (1.10, "#2F7F6F", None), "eptfe": (0.45, "#F1F1F1", None), "foam": (0.10, "#555555", None),
    "insulator": (1.40, "#C98A2B", None), "speaker": (None, "#3C3C3C", None), "qi_magnet": (7.5, "#8E8E8E", None),
    "qi_coil": (4.0, "#B87333", None), "qi_ferrite": (4.8, "#2E2E2E", None), "qi_tx": (1.85, "#2F6E3B", None),
    "lra": (None, "#7A7A7A", None), "epaper": (2.5, "#F4F4EE", None), "epaper_fpc": (1.4, "#C98A2B", None),
    "lte": (1.4, "#C98A2B", None), "bt_ant": (1.4, "#C98A2B", None), "gnss_gnd": (1.85, "#2F6E3B", None),
    "btn_pcb": (1.85, "#2F6E3B", None), "switch": (2.0, "#BFBFBF", None), "screw": (7.85, "#7F7F7F", None),
    "mr30_pair": (1.6, "#E8C547", None), "bat_lead": (3.0, "#B22222", None), "pigtail": (3.0, "#B22222", None),
    "spk_chamber": (1.27, "#8FA6B8", "PETG"), "gasket_chamber": (1.10, "#2F7F6F", None), "standin": (2.2, "#5B5B5B", None),
    "cable_exit": (None, "#E05050", None),
}

MM = 0.1
TB = adsk.fusion.TemporaryBRepManager.get()
G = {"log": [], "fails": [], "occ": {}, "bodies": {}, "app": {}, "t0": time.time(), "notes": []}


def log(s):
    G["log"].append("[%5.1fs] %s" % (time.time() - G["t0"], s))


def P(x, y, z=0.0):
    return adsk.core.Point3D.create(x * MM, y * MM, z * MM)


def Vec(x, y, z):
    return adsk.core.Vector3D.create(x, y, z)


# ----------------------------------------------------------------------------------------------- TBM solids
def box(x0, x1, y0, y1, z0, z1):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    obb = adsk.core.OrientedBoundingBox3D.create(P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), Vec(1, 0, 0), Vec(0, 1, 0),
                                                 (x1 - x0) * MM, (y1 - y0) * MM, (z1 - z0) * MM)
    return TB.createBox(obb)


def bar(p0, p1, w, z0, z1):
    """Box from p0 to p1 (XY), width w, Z z0..z1."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy)
    obb = adsk.core.OrientedBoundingBox3D.create(P((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (z0 + z1) / 2),
                                                 Vec(dx / ln, dy / ln, 0), Vec(-dy / ln, dx / ln, 0), ln * MM, w * MM, (z1 - z0) * MM)
    return TB.createBox(obb)


def cyl(p0, p1, d):
    return TB.createCylinderOrCone(P(*p0), d / 2 * MM, P(*p1), d / 2 * MM)


def cylz(cx, cy, z0, z1, d):
    return cyl((cx, cy, z0), (cx, cy, z1), d)


def U(a, *bs):
    for b in bs:
        if b is not None:
            TB.booleanOperation(a, b, adsk.fusion.BooleanTypes.UnionBooleanType)
    return a


def Dif(a, *bs):
    for b in bs:
        if b is not None:
            TB.booleanOperation(a, b, adsk.fusion.BooleanTypes.DifferenceBooleanType)
    return a


def union_all(bs):
    a = None
    for b in bs:
        if a is None:
            a = b
        else:
            U(a, b)
    return a


def rbox(x0, x1, y0, y1, z0, z1, r):
    """Box with its four vertical (Z) edges rounded r."""
    r = min(r, (x1 - x0) / 2 - 1e-3, (y1 - y0) / 2 - 1e-3)
    if r <= 0.01:
        return box(x0, x1, y0, y1, z0, z1)
    a = box(x0 + r, x1 - r, y0, y1, z0, z1)
    U(a, box(x0, x1, y0 + r, y1 - r, z0, z1))
    for cx in (x0 + r, x1 - r):
        for cy in (y0 + r, y1 - r):
            U(a, cylz(cx, cy, z0, z1, 2 * r))
    return a


def rring(xo, yo, xi, yi, z0, z1, ro, ri):
    """Rounded rectangular ring centred on the origin: outer +-xo/+-yo r ro, inner +-xi/+-yi r ri."""
    return Dif(rbox(-xo, xo, -yo, yo, z0, z1, ro), rbox(-xi, xi, -yi, yi, z0, z1, ri))


def track_x(x0, x1, yc, zc, ly, hz):
    """Racetrack prism along X: length ly along Y, height hz along Z, semicircular ends (r = hz/2)."""
    r = hz / 2.0
    a = box(x0, x1, yc - ly / 2 + r, yc + ly / 2 - r, zc - r, zc + r)
    for sy in (-1, 1):
        U(a, cyl((x0, yc + sy * (ly / 2 - r), zc), (x1, yc + sy * (ly / 2 - r), zc), hz))
    return a


def rect_ring_x(x0, x1, yo, z0o, z1o, yi, z0i, z1i):
    return Dif(box(x0, x1, -yo, yo, z0o, z1o), box(x0 - 1, x1 + 1, -yi, yi, z0i, z1i))


def mirror_x(body):
    b = TB.copy(body)
    m = adsk.core.Matrix3D.create()
    m.setCell(0, 0, -1.0)
    TB.transform(b, m)
    return b


# ----------------------------------------------------------------------------------------------- design objects
def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _base_appearance():
    app = adsk.core.Application.get()
    for i in range(app.materialLibraries.count):
        lib = app.materialLibraries.item(i)
        for n in ("Plastic - Matte (Yellow)", "Paint - Enamel Glossy (Yellow)", "Plastic - Glossy (Yellow)"):
            try:
                a = lib.appearances.itemByName(n)
            except Exception:
                a = None
            if a:
                return a
    return None


def appearance(colour):
    if colour in G["app"]:
        return G["app"][colour]
    a = None
    try:
        base = G.get("base_app")
        if base:
            name = "ag_" + colour.lstrip("#")
            a = G["design"].appearances.itemByName(name) or G["design"].appearances.addByCopy(base, name)
            props = a.appearanceProperties
            p = props.itemById("opaque_albedo")
            cp = adsk.core.ColorProperty.cast(p) if p else None
            if cp is None:
                for i in range(props.count):
                    cp = adsk.core.ColorProperty.cast(props.item(i))
                    if cp:
                        break
            r, g, b = hex_rgb(colour)
            cp.value = adsk.core.Color.create(r, g, b, 255)
    except Exception:
        a = None
    G["app"][colour] = a
    return a


def mat_of(name):
    best = ""
    for k in MAT:
        if name.startswith(k) and len(k) > len(best):
            best = k
    return MAT.get(best, (None, "#888888", None))


def comp(name):
    """New top-level component (identity transform)."""
    if name in G["occ"]:
        return G["occ"][name].component
    occ = G["design"].rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    G["occ"][name] = occ
    return occ.component


def add(name, tbody, comp_name=None, colour=None):
    """Adds a temporary body as a real body in component comp_name (default: its own component)."""
    if tbody is None:
        G["fails"].append(name + " (no geometry)")
        return None
    c = comp(comp_name or name)
    try:
        b = c.bRepBodies.add(tbody)
    except Exception as e:
        G["fails"].append("%s (%s)" % (name, e))
        return None
    b.name = name
    a = appearance(colour or mat_of(comp_name or name)[1])
    if a:
        try:
            b.appearance = a
        except Exception:
            pass
    G["bodies"][name] = b
    return b.createForAssemblyContext(G["occ"][comp_name or name])


# ----------------------------------------------------------------------------------------------- STEP import
def _rot(axes):
    return [AX[a] for a in axes]


def _apply(R, p):
    return tuple(sum(R[k][i] * p[k] for k in range(3)) for i in range(3))


def import_step(name, path, axes=("X", "Y", "Z"), local_ref=(0, 0, 0), world_ref=(0, 0, 0), lbox=None):
    """Imports a STEP file as component `name`; file axes -> world axes; local_ref lands on world_ref.
    The wrapper transform is set before the import. With lbox (local bbox) the placed box is checked."""
    if not os.path.isfile(path):
        G["fails"].append("%s (STEP not found: %s)" % (name, os.path.relpath(path, ROOT)))
        return None
    Rm = _rot(axes)
    rl = _apply(Rm, local_ref)
    t = [world_ref[i] - rl[i] for i in range(3)]
    m = adsk.core.Matrix3D.create()
    m.setWithCoordinateSystem(P(*t), Vec(*Rm[0]), Vec(*Rm[1]), Vec(*Rm[2]))
    app = adsk.core.Application.get()
    occ = G["design"].rootComponent.occurrences.addNewComponent(m)
    occ.component.name = name
    opts = app.importManager.createSTEPImportOptions(path)
    opts.isViewFit = False
    app.importManager.importToTarget(opts, occ.component)
    G["occ"][name] = occ
    seen = set()
    for c in [occ.component] + [o.component for o in occ.component.allOccurrences]:
        if c.entityToken in seen:
            continue
        seen.add(c.entityToken)
        for i in range(c.bRepBodies.count):
            b = c.bRepBodies.item(i)
            if not b.name.startswith(name + "|"):
                b.name = "%s|%s" % (name, b.name)
    bodies = occ_bodies(occ)
    if not bodies:
        G["fails"].append("%s (no bodies imported)" % name)
    elif lbox:
        corners = [_apply(Rm, (x, y, z)) for x in (lbox[0], lbox[3]) for y in (lbox[1], lbox[4]) for z in (lbox[2], lbox[5])]
        lo = [min(c[i] for c in corners) + t[i] for i in range(3)]
        hi = [max(c[i] for c in corners) + t[i] for i in range(3)]
        blo, bhi = bbox_of(bodies)
        err = max(max(abs(blo[i] - lo[i]), abs(bhi[i] - hi[i])) for i in range(3))
        if err > 0.15:
            G["fails"].append("%s placed %.2f mm off its expected box" % (name, err))
    log("imported %s: %d bodies" % (name, len(bodies)))
    return occ


def occ_bodies(occ):
    out = [occ.bRepBodies.item(i) for i in range(occ.bRepBodies.count)]
    for i in range(occ.childOccurrences.count):
        out += occ_bodies(occ.childOccurrences.item(i))
    return [b for b in out if b.isSolid]


def bbox_of(bodies):
    lo = [min(getattr(b.boundingBox.minPoint, a) for b in bodies) * 10 for a in "xyz"]
    hi = [max(getattr(b.boundingBox.maxPoint, a) for b in bodies) * 10 for a in "xyz"]
    return lo, hi


def real(name, key, axes, local_ref, world_ref):
    rel, lb = REAL[key]
    return import_step(name, os.path.join(MODELS, rel), axes, local_ref, world_ref, lb)


# ================================================================================================ SHELL
def grille_centres():
    out = []
    for i in range(int(Q["grille_ny"])):
        for j in range(int(Q["grille_nz"])):
            out.append(((i - (Q["grille_ny"] - 1) / 2.0) * Q["grille_pitch"], Q["grille_z0"] + j * Q["grille_pitch"]))
    return out


def build_front_shell():
    s = Dif(rbox(-L2, L2, -W2, W2, 0, ZF, R), rbox(-IX, IX, -IY, IY, -1, ZI, IR))
    # display window, lens pocket, tuck groove
    wx0, wx1, wy0, wy1 = Q["win_x0"], Q["win_x1"], Q["win_y0"], Q["win_y1"]
    m = Q["lens_pocket_margin"]
    px0, px1, py0, py1 = wx0 - m, wx1 + m, wy0 - m, wy1 + m
    t = Q["tuck_w"]
    Dif(s, box(wx0, wx1, wy0, wy1, ZI - 1, ZF + 1))
    Dif(s, box(px0, px1, py0, py1, ZF - Q["lens_pocket_d"], ZF + 1))
    groove = Dif(box(px0 - t, px1 + t, py0 - t, py1 + t, ZF - Q["tuck_d"], ZF + 1), box(px0, px1, py0, py1, ZF - 5, ZF + 2))
    Dif(s, groove)
    # Qi marking ring (raised 0.4 under the fabric)
    U(s, Dif(cylz(Q["qi_x"], 0, ZF - 0.01, ZF + Q["qi_ring_h"], Q["qi_ring_od"]),
             cylz(Q["qi_x"], 0, ZF - 1, ZF + 1, Q["qi_ring_id"])))
    # mic hole, gesture window, touch pocket (from inside, 1.2 wall left)
    Dif(s, cylz(Q["mic_x"], Q["mic_y"], ZI - 1, ZF + 1, Q["mic_d"]))
    gw, gh = Q["gest_w"], Q["gest_h"]
    Dif(s, box(Q["gest_x"] - gw / 2, Q["gest_x"] + gw / 2, Q["gest_y"] - gh / 2, Q["gest_y"] + gh / 2, ZI - 1, ZF + 1))
    tw = ZF - Q["touch_wall"]
    Dif(s, box(Q["touch_x0"] - 0.2, Q["touch_x1"] + 0.2, Q["touch_y0"] - 0.2, Q["touch_y1"] + 0.2, ZI - 1, tw))
    # ends: membrane pocket from inside, round-hole grille, trim channel (outside)
    yo, zg0, zg1 = 35.2, -0.5, ZI
    for sx in (-1, 1):
        Dif(s, box(sx * (IX - 0.5), sx * (L2 - Q["grille_wall"]), -yo, yo, zg0, zg1))
        holes = [cyl((sx * (L2 - Q["grille_wall"] - 0.3), y, z), (sx * (L2 + 0.5), y, z), Q["grille_d"]) for y, z in grille_centres()]
        Dif(s, union_all(holes))
        ty, tyi = Q["trim_y_out"] / 2 + 0.05, Q["trim_y_in"] / 2 - 0.05
        ch = Dif(box(sx * (L2 - Q["trim_t"]), sx * (L2 + 1), -ty, ty, Q["trim_z0"] - 0.05, Q["trim_z1"] + 0.05),
                 box(sx * (L2 - 2), sx * (L2 + 2), -tyi, tyi, Q["trim_zi0"] + 0.05, Q["trim_zi1"] - 0.05))
        Dif(s, ch)
    # top edge: strip pocket, two windows (rib between VOL- and VOL+), two USB-C openings
    zc, h = Q["strip_zc"], Q["strip_h"]
    Dif(s, box(Q["strip_x0"], Q["strip_x1"], W2 - Q["strip_pocket_d"], W2 + 1, zc - h / 2, zc + h / 2))
    rib = (KEYS[2] + KEYS[3]) / 2.0
    ins = Q["win_inset"]
    for a, b in ((Q["strip_x0"] + ins, rib - Q["rib_w"] / 2), (rib + Q["rib_w"] / 2, Q["strip_x1"] - ins)):
        Dif(s, box(a, b, IY - 1, W2, zc - h / 2 + ins, zc + h / 2 - ins))
    G["strip_windows"] = ((Q["strip_x0"] + ins, rib - Q["rib_w"] / 2), (rib + Q["rib_w"] / 2, Q["strip_x1"] - ins))
    for ux in (Q["usb1_x"], Q["usb2_x"]):
        Dif(s, usb_opening(ux, IY - 1, W2 + 1))
    # bottom edge: pogo holes, magnet bosses + blind pockets (1.6 skin)
    for x in POGO_X:
        Dif(s, cyl((x, -W2 - 1, Q["pogo_z"]), (x, -IY + 1, Q["pogo_z"]), Q["pogo_hole_d"]))
    yb = -W2 + Q["mag_skin"]
    for x in MAG_X:
        U(s, cyl((x, -IY - 0.1, Q["mag_z"]), (x, yb + Q["mag_t"] + 0.4, Q["mag_z"]), Q["mag_d"] + 3.0))
        Dif(s, cyl((x, yb, Q["mag_z"]), (x, yb + Q["mag_t"] + 0.5, Q["mag_z"]), Q["mag_d"] + 0.2))
    # clip ledges on both long walls
    cw = Q["clip_w"] / 2.0
    for x in CLIP_X:
        for sy in (-1, 1):
            U(s, box(x - cw, x + cw, sy * Q["ledge_y_in"], sy * (IY + 0.1), Q["ledge_z0"], Q["ledge_z1"]))
    # stiffening ribs on the 1.7 front wall, where its inner face is free (2.0 deep, 1.5 wide)
    rz0 = ZI - 2.0
    U(s, box(-70.0, 13.0, 19.2, 20.6, rz0, ZI + 0.01))           # above the OLED, below the front sensor
    U(s, box(-70.0, 5.0, -13.6, -12.2, rz0, ZI + 0.01))          # below the OLED FPC fold, above the Wi-Fi
    ring = Dif(cylz(Q["qi_x"], 0, rz0, ZI + 0.01, 60.0), cylz(Q["qi_x"], 0, rz0 - 1, ZI + 1, 57.0))
    Dif(ring, box(-100, 15.5, -40, 40, -1, 40), box(71.3, 100, -40, 40, -1, 40))
    U(s, ring)                                                    # round the Qi magnet ring, cut at the OLED / box R
    add("front_shell", s)


def usb_opening(ux, y0, y1):
    w, h = Q["usb_open_w"], Q["usb_open_h"]
    r = h / 2.0
    zc = Q["usb_zc"]
    a = box(ux - w / 2 + r, ux + w / 2 - r, y0, y1, zc - h / 2, zc + h / 2)
    for sx in (-1, 1):
        U(a, cyl((ux + sx * (w / 2 - r), y0, zc), (ux + sx * (w / 2 - r), y1, zc), h))
    return a


def build_lid():
    lid = rbox(-L2, L2, -W2, W2, -LT, 0, R)
    f = Q["fit"]
    to_x, to_y = IX - f, IY - f                         # tongue outer 92.6 / 35.6
    ti_x, ti_y = to_x - Q["tongue_w"], to_y - Q["tongue_w"]
    g0, g1 = Q["groove_z0"], Q["groove_z0"] + Q["groove_w"]
    gd = Q["groove_d"]
    # --- cuts into the plate first
    # e-paper: pocket inside, through window (active area, centred: offset unverified), cover recess outside
    ex0, ex1, ey = Q["ep_x0"], Q["ep_x1"], Q["ep_y"] / 2
    ecx = (ex0 + ex1) / 2
    Dif(lid, box(ex0 - 0.1, ex1 + 0.1, -ey - 0.1, ey + 0.1, -Q["ep_pocket_d"], 1))
    ax, ay = Q["ep_aa_x"] / 2, Q["ep_aa_y"] / 2
    Dif(lid, box(ecx - ax, ecx + ax, -ay, ay, -LT - 1, 0))
    cm = Q["ep_cover_margin"]
    Dif(lid, box(ecx - ax - cm, ecx + ax + cm, -ay - cm, ay + cm, -LT - 1, -LT + Q["ep_cover_t"]))
    # FPC groove in the lid face (pocket edge -> past the cell edge)
    Dif(lid, box(-11.0, 3.0, -ey + 0.5, -31.4, -0.4, 1))
    # back ring channel, signature plate recess, pry notch
    ri, rw = Q["ring_inset"], Q["ring_w"]
    Dif(lid, rring(L2 - ri, W2 - ri, L2 - ri - rw, W2 - ri - rw, -LT - 1, -LT + Q["ring_channel"], Q["ring_r"], max(Q["ring_r"] - rw, 0.5)))
    py = Q["plate_y"] / 2
    Dif(lid, rbox(Q["plate_x0"], Q["plate_x1"], -py, py, -LT - 1, -LT + Q["plate_t"], Q["plate_r"]))
    Dif(lid, box(Q["pry_x0"], Q["pry_x1"], Q["pry_y0"], Q["pry_y1"], -LT - 1, Q["pry_floor"]))
    # trim channel on the lid's end faces (the frame's bottom bar reaches Z -0.3)
    for sx in (-1, 1):
        ty = Q["trim_y_out"] / 2 + 0.05
        Dif(lid, box(sx * (L2 - Q["trim_t"]), sx * (L2 + 1), -ty, ty, Q["trim_z0"] - 0.05, 0.001))
    # --- tongue with the gasket groove in its outer face
    tongue = rring(to_x, to_y, ti_x, ti_y, -0.01, Q["tongue_h"], IR - f, IR - f - Q["tongue_w"])
    Dif(tongue, rring(to_x + 1, to_y + 1, to_x - gd, to_y - gd, g0, g1, IR + 1, IR - f - gd))
    U(lid, tongue)
    # 8 snap clips (arm + outward hook over the wall ledge)
    cw, ct, yin = Q["clip_w"] / 2, Q["clip_t"], Q["clip_y_in"]
    for x in CLIP_X:
        for sy in (-1, 1):
            U(lid, box(x - cw, x + cw, sy * yin, sy * (yin + ct), -0.01, Q["clip_h"]))
            U(lid, box(x - cw, x + cw, sy * (yin + ct - 0.01), sy * (yin + ct + Q["hook_out"]),
                       Q["clip_h"] - Q["hook_h"], Q["clip_h"]))
    # end hooks (as drawn: X 90.8..92.6, Y +-4) into the speaker boxes
    for sx in (-1, 1):
        U(lid, box(sx * Q["end_hook_x0"], sx * Q["end_hook_x1"], -Q["end_hook_y"], Q["end_hook_y"], -0.01, Q["end_hook_h"]))
    # LRA pad + U clip (rigid rib on the lid)
    lx0, lx1 = Q["lra_x0"], Q["lra_x1"]
    hw = Q["lra_w"] / 2
    U(lid, box(lx0 - 1, lx1 + 1, -hw - 1.2, hw + 1.2, -0.01, Q["cell_pad"]))
    for sy in (-1, 1):
        U(lid, box(lx0 + 1, lx1 - 1, sy * (hw + 0.1), sy * (hw + 1.3), Q["cell_pad"] - 0.01, Q["cell_pad"] + Q["lra_t"] - 0.5))
    # power-board posts (the board has no holes: it rests on these)
    for x, y in PPOSTS:
        U(lid, cylz(x, y, -0.01, Q["board_z"], Q["ppost_d"]))
    add("lid", lid)
    # gasket cord (compressed section in the groove)
    add("gasket_cord", rring(IX - 0.05, IY - 0.05, to_x - gd, to_y - gd, g0 + 0.05, g1 - 0.05, IR - 0.05, IR - f - gd))


def build_lid_parts():
    # back ring (TPU), signature plate, e-paper cover
    ri, rw, f = Q["ring_inset"], Q["ring_w"], 0.05
    add("back_ring", rring(L2 - ri - f, W2 - ri - f, L2 - ri - rw + f, W2 - ri - rw + f,
                           -LT - Q["ring_proud"], -LT + Q["ring_channel"], Q["ring_r"] - f, max(Q["ring_r"] - rw, 0.5) + f))
    py = Q["plate_y"] / 2
    add("sig_plate", rbox(Q["plate_x0"] + 0.1, Q["plate_x1"] - 0.1, -py + 0.1, py - 0.1, -LT, -LT + Q["plate_t"], Q["plate_r"] - 0.1))
    ex0, ex1 = Q["ep_x0"], Q["ep_x1"]
    ecx = (ex0 + ex1) / 2
    ax, ay, cm = Q["ep_aa_x"] / 2, Q["ep_aa_y"] / 2, Q["ep_cover_margin"]
    add("epaper_cover", box(ecx - ax - cm + 0.1, ecx + ax + cm - 0.1, -ay - cm + 0.1, ay + cm - 0.1, -LT, -LT + Q["ep_cover_t"]))
    ey = Q["ep_y"] / 2
    add("epaper_panel", box(ex0, ex1, -ey, ey, -Q["ep_pocket_d"] + 0.1, -Q["ep_pocket_d"] + 0.1 + Q["ep_t"]))
    # e-paper FPC (assumed: leaves the bottom edge at X -10.5..2.5, 0.15 thick) -> carrier J13 (-4, -13.4)
    fx0, fx1, ft = -10.5, 2.5, 0.15
    yv = -31.25
    seg = U(box(fx0, fx1, -ey, yv, -0.35, -0.35 + ft),
            box(fx0, fx1, yv, yv + ft, -0.35, 15.35),
            box(fx0, fx1, yv, -15.6, 15.2, 15.35))
    add("epaper_fpc", seg)
    G["fpc_len"] = (abs(yv - (-ey))) + (15.35 + 0.35) + abs(-15.6 - yv)
    # cell foam (EVA) + insulator on the cell
    cy = Q["cell_w"] / 2
    add("foam_cell", box(Q["cell_x0"], Q["cell_x1"], -cy, cy, 0, Q["cell_pad"]))
    ct = Q["cell_pad"] + Q["cell_t"]
    add("insulator", box(Q["cell_x0"], Q["cell_x1"], -cy, cy, ct, ct + Q["insul"]))


def build_signature(design):
    """Engraves the placeholder text 0.3 deep into the plate's outer face (reads from behind)."""
    try:
        c = G["occ"]["sig_plate"].component
        plate = G["bodies"]["sig_plate"]
        pi = c.constructionPlanes.createInput()
        pi.setByOffset(c.xYConstructionPlane, adsk.core.ValueInput.createByReal(-LT * MM))
        pl = c.constructionPlanes.add(pi)
        pl.isLightBulbOn = False
        sk = c.sketches.add(pl)
        cx = (Q["plate_x0"] + Q["plate_x1"]) / 2
        for txt, y, h in (("made with", 12.0, 2.6), ("love", 8.0, 2.6), ("signature", -8.0, 2.8)):
            ti = sk.sketchTexts.createInput2(txt, h * MM)
            ti.setAsMultiLine(P(cx - 8.4, y - h, 0), P(cx + 8.4, y + h, 0),
                              adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                              adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
            ti.isHorizontalFlip = True
            st = sk.sketchTexts.add(ti)
            ei = c.features.extrudeFeatures.createInput(st, adsk.fusion.FeatureOperations.CutFeatureOperation)
            ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(0.3 * MM)),
                                adsk.fusion.ExtentDirections.PositiveExtentDirection)
            ei.participantBodies = [plate]
            c.features.extrudeFeatures.add(ei)
        sk.isVisible = False
    except Exception as e:
        G["fails"].append("signature text (%s)" % e)


def build_front_parts():
    wx0, wx1, wy0, wy1 = Q["win_x0"], Q["win_x1"], Q["win_y0"], Q["win_y1"]
    m = Q["lens_pocket_margin"]
    floor = ZF - Q["lens_pocket_d"]
    lens_top = ZF + Q["fabric"]
    lens_bot = lens_top - Q["lens_t"]
    add("lens", box(wx0 - m + 0.2, wx1 + m - 0.2, wy0 - m + 0.2, wy1 + m - 0.2, lens_bot, lens_top))
    add("foam_lens", Dif(box(wx0 - m + 0.2, wx1 + m - 0.2, wy0 - m + 0.2, wy1 + m - 0.2, floor, lens_bot),
                         box(wx0, wx1, wy0, wy1, floor - 1, lens_bot + 1)))
    gw, gh = Q["gest_w"] - 0.1, Q["gest_h"] - 0.1
    add("ir_window", box(Q["gest_x"] - gw / 2, Q["gest_x"] + gw / 2, Q["gest_y"] - gh / 2, Q["gest_y"] + gh / 2, ZI, ZF))
    # mic port gasket ring between the front sensor board and the wall
    add("foam_mic", Dif(cylz(Q["mic_x"], Q["mic_y"], Q["fs_z"] + 0.8, ZI, 3.6), cylz(Q["mic_x"], Q["mic_y"], 0, 40, 1.6)))
    # ePTFE sheets
    for sx, tag in ((-1, "L"), (1, "R")):
        x0 = sx * (L2 - Q["grille_wall"])
        add("eptfe_" + tag, box(x0, x0 - sx * Q["eptfe_t"], -Q["eptfe_y"] / 2, Q["eptfe_y"] / 2,
                                15.15 - Q["eptfe_z"] / 2, 15.15 + Q["eptfe_z"] / 2))
    # brass-tone trim frames
    for sx, tag in ((-1, "L"), (1, "R")):
        ty, tyi = Q["trim_y_out"] / 2, Q["trim_y_in"] / 2
        add("trim_" + tag, Dif(box(sx * (L2 - Q["trim_t"]), sx * L2, -ty, ty, Q["trim_z0"], Q["trim_z1"]),
                               box(sx * (L2 - 2), sx * (L2 + 1), -tyi, tyi, Q["trim_zi0"], Q["trim_zi1"])))


def build_speakers():
    """Dayton CE70-30P-8 (modelled from a typical racetrack drawing, VERIFY) + sealed printed back box."""
    zc = Q["spk_z0"] + Q["spk_h"] / 2
    fx, bx, ft = Q["spk_face_x"], Q["spk_back_x"], Q["spk_flange_t"]
    for sx, tag in ((-1, "L"), (1, "R")):
        X = lambda v: sx * v
        flange = track_x(X(fx), X(fx - ft), 0, zc, Q["spk_l"], Q["spk_h"])
        for yy in (-Q["spk_hole_y"], Q["spk_hole_y"]):
            for dz in (-Q["spk_hole_dz"], Q["spk_hole_dz"]):
                Dif(flange, cyl((X(fx + 1), yy, zc + dz), (X(fx - ft - 1), yy, zc + dz), Q["spk_hole_d"]))
        basket = track_x(X(fx - ft), X(Q["spk_basket_x"]), 0, zc, Q["spk_basket_l"], Q["spk_basket_h"])
        magnet = cyl((X(Q["spk_basket_x"]), 0, zc), (X(bx), 0, zc), Q["spk_magnet_d"])
        add("speaker_" + tag, U(flange, basket, magnet))
        # foam pad between the driver face and the ePTFE (in the end-wall pocket)
        add("foam_spk_face_" + tag, Dif(track_x(X(fx), X(fx + 0.8), 0, zc, Q["spk_l"], Q["spk_h"]),
                                        track_x(X(fx - 1), X(fx + 2), 0, zc, Q["box_open_l"], Q["box_open_h"])))
        # foam gasket flange -> box, then the box
        by, bw = Q["box_y"], Q["box_wall"]
        bz0, bz1 = Q["spk_z0"] + 0.05, Q["spk_z0"] + Q["spk_h"] - 0.05
        gx0, gx1 = fx - ft, fx - ft - Q["box_gasket"]
        opening = track_x(X(gx0 + 1), X(gx1 - bw - 1), 0, zc, Q["box_open_l"], Q["box_open_h"])
        add("foam_spk_box_" + tag, Dif(box(X(gx0), X(gx1), -by, by, bz0, bz1), TB.copy(opening)))
        outer = box(X(gx1), X(bx - Q["box_back"]), -by, by, bz0, bz1)
        cav = box(X(gx1 - bw), X(bx), -by + bw, by - bw, bz0 + bw, bz1 - bw)
        cav_v = cav.volume
        mag_v = math.pi * (Q["spk_magnet_d"] / 2 * MM) ** 2 * (abs(Q["spk_basket_x"] - bx) * MM)
        bxb = Dif(outer, cav, opening)
        Dif(bxb, cyl((X(bx + 1), 0, 26.0), (X(bx - Q["box_back"] - 1), 0, 26.0), 2.5))       # sealed wire hole
        c = CH[tag]
        iz0, iz1 = c["z"][0] + CH_WALL, c["z"][1] - CH_WALL
        hole = box(X(bx + 0.1), X(bx - Q["box_back"] - 0.1), c["joint"][0], c["joint"][1], iz0, iz1)
        G.setdefault("vol", {})[tag] = {"cavity": cav_v, "magnet": mag_v, "hole": hole.volume}
        Dif(bxb, hole)                                                                          # into the chamber
        add("speaker_box_" + tag, bxb)


def build_qi():
    x = Q["qi_x"]
    z = ZI
    add("qi_magnet", Dif(cylz(x, 0, z - Q["qi_mag_t"], z, Q["qi_mag_od"]), cylz(x, 0, 0, 40, Q["qi_mag_id"])))
    z -= Q["qi_mag_t"]
    add("qi_coil", Dif(cylz(x, 0, z - Q["qi_coil_t"], z, Q["qi_coil_d"]), cylz(x, 0, 0, 40, Q["qi_coil_id"])))
    z -= Q["qi_coil_t"]
    add("qi_ferrite", cylz(x, 0, z - Q["qi_ferrite_t"], z, Q["qi_coil_d"]))
    add("qi_tx", box(Q["qi_tx_x"], Q["qi_tx_x"] + Q["qi_tx_t"], Q["qi_tx_y0"], Q["qi_tx_y1"], Q["qi_tx_z0"], Q["qi_tx_z1"]))


def build_misc_parts():
    # haptic LRA (real size 10 x 10 x 4)
    hw = Q["lra_w"] / 2
    add("lra", box(Q["lra_x0"], Q["lra_x1"], -hw, hw, Q["cell_pad"], Q["cell_pad"] + Q["lra_t"]))
    # antennas without a STEP: LTE flex (Linx ANT-5GLFPC1), BT FPC
    add("lte_flex", box(Q["lte_x0"], Q["lte_x1"], IY - Q["lte_t"], IY - 0.01, Q["lte_z0"], Q["lte_z1"]))
    add("bt_ant", box(Q["bt_x0"], Q["bt_x1"], -IY + 0.01, -IY + Q["bt_t"], Q["bt_z0"], Q["bt_z1"]))
    # GNSS ground board behind the patch
    add("gnss_gnd", box(Q["gnss_x0"], Q["gnss_x1"], Q["gnss_y0"], Q["gnss_y1"], ZI - 4.0 - Q["gnss_gnd_t"], ZI - 4.0))
    # button PCB + 5 tact switches (C&K PTS645, 6 x 6, 4.3 to the plunger top) + TPU strip
    zc = Q["strip_zc"]
    y0 = Q["btn_pcb_y"]
    y1 = y0 + Q["btn_pcb_t"]
    add("btn_pcb", box(Q["strip_x0"] + 0.2, Q["strip_x1"] - 0.2, y0, y1, zc - 4.4, zc + 4.4))
    s = Q["sw_body"] / 2
    for i, x in enumerate(KEYS):
        sw = U(box(x - s, x + s, y1, y1 + Q["sw_body_h"], zc - s, zc + s),
               cyl((x, y1 + Q["sw_body_h"] - 0.01, zc), (x, y1 + Q["sw_h"], zc), Q["sw_plunger_d"]))
        add("switch_%d" % (i + 1), sw, "switches")
    sx0, sx1, h = Q["strip_x0"] + 0.1, Q["strip_x1"] - 0.1, Q["strip_h"] - 0.2
    top = W2 + Q["fabric"]
    strip = box(sx0, sx1, W2 - Q["strip_pocket_d"], top, zc - h / 2, zc + h / 2)
    ih = Q["icon_h"]
    for i, x in enumerate(KEYS):
        U(strip, cyl((x, W2 - Q["strip_pocket_d"] + 0.01, zc), (x, y1 + Q["sw_h"] + 0.1, zc), Q["nub_d"]))
        if i == 0:      # MUTE: mic body + slash
            U(strip, box(x - 0.8, x + 0.8, top - 0.01, top + ih, zc - 1.2, zc + 1.2), bar_y(x - 1.6, zc + 1.6, x + 1.6, zc - 1.6, top, ih))
        elif i == 1:    # PWR: ring + bar
            U(strip, Dif(cyl((x, top - 0.01, zc), (x, top + ih, zc), 3.6), cyl((x, top - 1, zc), (x, top + 1, zc), 2.6)),
              box(x - 0.45, x + 0.45, top - 0.01, top + ih, zc, zc + 2.2))
        elif i == 2:    # VOL-
            U(strip, box(x - 1.6, x + 1.6, top - 0.01, top + ih, zc - 0.45, zc + 0.45))
        elif i == 3:    # VOL+
            U(strip, box(x - 1.6, x + 1.6, top - 0.01, top + ih, zc - 0.45, zc + 0.45),
              box(x - 0.45, x + 0.45, top - 0.01, top + ih, zc - 1.6, zc + 1.6))
        else:           # PLAY/PAUSE: triangle (3 bars) + 2 bars
            U(strip, bar_y(x - 1.8, zc - 1.5, x - 1.8, zc + 1.5, top, ih), bar_y(x - 1.8, zc - 1.5, x + 0.2, zc, top, ih),
              bar_y(x - 1.8, zc + 1.5, x + 0.2, zc, top, ih), box(x + 0.7, x + 1.2, top - 0.01, top + ih, zc - 1.3, zc + 1.3),
              box(x + 1.6, x + 2.1, top - 0.01, top + ih, zc - 1.3, zc + 1.3))
    add("button_strip", strip)
    # carrier bracket: posts at H1..H4 (H1/H4 to the front wall, H2/H3 under the panel), bars
    pd = Q["post_d"]
    z0 = Q["board_z"] + BOARD_T["carrier"]
    parts = []
    for k in ("H3", "H4"):
        x, y = HOLES[k]
        z1 = ZI if k == "H4" else Q["short_post_z1"]
        parts.append(cylz(x, y, z0, z1, pd))
    parts.append(bar(HOLES["H3"], HOLES["H4"], Q["bar_w"], Q["bar_z0"], Q["bar_z1"]))
    br = union_all(parts)
    for k in ("H3", "H4"):
        x, y = HOLES[k]
        Dif(br, cylz(x, y, z0 - 1, z0 + Q["screw_l"] - 1.0 + 0.5, 1.6))
    add("bracket", br)
    # M2 screws from the back (head under the carrier, in the cell swell gap)
    for k, (x, y) in HOLES.items():
        zb = Q["board_z"]
        add("screw_" + k, U(cylz(x, y, zb - Q["screw_head_h"], zb, Q["screw_head_d"]), cylz(x, y, zb - 0.01, zb + Q["screw_l"] - 1.0, 1.6)), "screws")
    build_battery_pocket()


def _path(pts, d):
    segs = [cyl(pts[i], pts[i + 1], d) for i in range(len(pts) - 1)]
    for q in pts[1:-1]:
        segs.append(TB.createSphere(P(*q), d / 2 * MM))
    ln = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    return union_all(segs), ln


def build_battery_pocket():
    """MR30 off the power board: pigtail (2 x 18 AWG, one dia 2.0 bundle) from TP1/TP2 (46.8, -13/-8, top side) round
    the board's bottom edge to a female MR30 in the pocket beside the cell; the cell's male MR30 on its own leads."""
    x0, x1, y0, y1, z0, z1 = MR30_PAIR
    add("mr30_pair", box(x0, x1, y0, y1, z0, z1))
    zt = Q["board_z"] + BOARD_T["power"] + 1.3
    pig, ln = _path([(46.8, -10.5, zt), (48.8, -10.5, zt), (48.8, -18.5, zt), (48.8, -18.5, 10.3), (48.8, -1.5, 10.3),
                     (59.0, -1.5, 10.3), (59.0, -1.5, 4.5), (59.0, y1, 4.5)], 2.0)
    add("pigtail", pig)
    lead, ln2 = _path([(49.0, -23.0, 6.6), (49.0, -31.5, 6.6), (59.0, -31.5, 6.6), (59.0, y0, 6.6)], 2.6)
    add("bat_leads", lead)
    G["pigtail_len"], G["batlead_len"] = ln, ln2


def build_chambers():
    """Sealed back-box chambers (option B) + their gaskets; back volume before/after per side."""
    zc = Q["board_z"] + BOARD_T["carrier"]
    for tag, c in CH.items():
        z0, z1 = c["z"]
        w = CH_WALL
        outer = union_all([box(a, b, cc, d, z0, z1) for a, b, cc, d in c["outer"]])
        vo = outer.volume
        inner = union_all([box(a, b, cc, d, z0 + w, z1 - w) for a, b, cc, d in c["inner"]])
        body = Dif(outer, inner)
        for x, y in c["pillars"]:
            U(body, cylz(x, y, z0 + w - 0.01, z1 - w + 0.01, 3.0))
        for k in c["bosses"]:
            x, y = HOLES[k]
            U(body, cylz(x, y, z0 + w - 0.01, z1 - w + 0.01, 5.0))
        air = vo - body.volume
        for k in c["bosses"]:                      # bosses down to the carrier replace the bracket posts H1/H2
            x, y = HOLES[k]
            U(body, cylz(x, y, zc, z0 + 0.01, Q["post_d"]))
            Dif(body, cylz(x, y, zc - 1, zc + Q["screw_l"] - 1.0 + 0.5, 1.6))
        add("spk_chamber_" + tag, body)
        sx = 1 if tag == "R" else -1
        jo, ji = c["joint_outer"], c["joint"]
        g = Dif(box(sx * 71.3, sx * 71.8, jo[0], jo[1], z0, z1), box(sx * 70, sx * 73, ji[0], ji[1], z0 + w, z1 - w))
        add("gasket_chamber_" + tag, g)
        v = G["vol"][tag]
        before = v["cavity"] + 0.17 - v["magnet"] - 1.0          # cc: + plate opening air, - magnet, - basket frame (est.)
        v.update(before=before, chamber=air, after=before + air + v["hole"])


def bar_y(x0, z0, x1, z1, top, ih, w=0.5):
    """Raised icon stroke on the top-edge strip: XZ segment, Y top..top+ih."""
    dx, dz = x1 - x0, z1 - z0
    ln = math.hypot(dx, dz)
    obb = adsk.core.OrientedBoundingBox3D.create(P((x0 + x1) / 2, top + ih / 2 - 0.005, (z0 + z1) / 2), Vec(dx / ln, 0, dz / ln),
                                                 Vec(0, 1, 0), ln * MM, (ih + 0.01) * MM, w * MM)
    return TB.createBox(obb)


def build_standins():
    """Boxes for board parts without a KiCad 3D model (cad/boards/standins.json, courtyard x datasheet height)."""
    p = os.path.join(BOARDS, "standins.json")
    if not os.path.isfile(p):
        G["fails"].append("standins.json missing (run board_standins.py)")
        return
    for s in json.load(open(p)):
        if s["ref"] in ("J2", "J3") and s["board"] == "power":
            continue
        key = (s["board"], s["ref"])
        if key in OVERRIDE:
            if OVERRIDE[key] is None:
                continue
            s = dict(s, **OVERRIDE[key])
        z0 = BOARD_Z[s["board"]] + (BOARD_T[s["board"]] if s["side"] == "F" else 0)
        z1 = z0 + s["h"] if s["side"] == "F" else z0 - s["h"]
        add("standin_%s_%s" % (s["board"], s["ref"]), box(s["x0"], s["x1"], s["y0"], s["y1"], z0, z1), "standins")


def build_cable_exits():
    """Space a mated plug + wire bend needs beyond each cable connector (JST SH/PH, MR30 is modelled):
    3.0 long past the courtyard edge in the cable direction, 2.95 high. Checked as cable-route items, not part clashes."""
    p = os.path.join(BOARDS, "standins.json")
    exits = {("carrier", "J8"): "+Y", ("carrier", "J7"): "+Y", ("carrier", "J12"): "+Y", ("carrier", "J4"): "-X",
             ("carrier", "J9"): "-X", ("carrier", "J6"): "-Y", ("carrier", "J1"): "+X", ("carrier", "J11"): "-Y",
             ("carrier", "J13"): "-Y", ("power", "J1"): "-X", ("power", "J5"): "+Y", ("power", "J6"): "+X", ("power", "J7"): "+X"}
    G["exits"] = exits


# ================================================================================================ REAL PARTS
def build_real():
    bz = Q["board_z"]
    for b in ("carrier", "power", "front_sensor", "front_touch"):
        import_step("board_" + b, os.path.join(BOARDS, b + ".step"), ("X", "Y", "Z"), (0, 0, 0), (0, 0, BOARD_Z[b]))
    real("cell", "cell", ("-X", "-Y", "Z"), (0.0, 0.0, 0.0), (Q["cell_x1"], 0.0, Q["cell_pad"]))
    real("oled", "panel", ("-X", "Y", "-Z"), (0.0, 0.0, 0.0), (15.0, -9.9, ZI))
    wcx, wcy = (Q["wifi_x0"] + Q["wifi_x1"]) / 2, (Q["wifi_y0"] + Q["wifi_y1"]) / 2
    real("wifi_flexpifa", "wifi", ("-X", "-Y", "Z"), (20.06, 5.5, 2.5), (wcx, wcy, ZI - 0.1))
    gx, gy = (Q["gnss_x0"] + Q["gnss_x1"]) / 2, (Q["gnss_y0"] + Q["gnss_y1"]) / 2
    real("gnss_patch", "gnss", ("X", "Y", "Z"), (0.0, 0.0, 4.0), (gx, gy, ZI))
    for i, ux in enumerate((Q["usb1_x"], Q["usb2_x"])):
        real("usb_c%d" % (i + 1), "usb_c", ("Y", "-X", "Z"), (-2.75, 13.0, 0.0), (ux, IY - 0.8 - Q["usb_inset"], Q["usb_zc"]))
    for k, x in enumerate(POGO_X):
        real("pogo_pad_%d" % (k + 1), "pogo_pad", ("X", "-Z", "Y"), (0.0, 0.0, 0.0), (x, -W2, Q["pogo_z"]))
    for k, x in enumerate(MAG_X):
        real("dock_magnet_%d" % (k + 1), "magnet", ("X", "-Z", "Y"), (0.0, 0.0, 0.0), (x, -W2 + Q["mag_skin"], Q["mag_z"]))


# ================================================================================================ CHECKS
def owner_of(b):
    """Top-level component name the body belongs to."""
    if "|" in b.name:
        return b.name.split("|", 1)[0]
    ctx = b.assemblyContext
    if ctx is None:
        return b.parentComponent.name
    path = ctx.fullPathName.split("+")
    return path[0].split(":")[0]


def all_bodies():
    out = []
    own = G.setdefault("own", {})
    for occ in G["design"].rootComponent.occurrences:
        bs = occ_bodies(occ)
        for b in bs:
            own[b.entityToken] = occ.component.name
        out += bs
    return out


def interference(bodies, ignore_same=True):
    ents = adsk.core.ObjectCollection.create()
    for b in bodies:
        ents.add(b)
    res = G["design"].analyzeInterference(G["design"].createInterferenceInput(ents))
    out = []
    if res is None:
        return None
    for i in range(res.count):
        r = res.item(i)
        oa, ob = owner_of(r.entityOne), owner_of(r.entityTwo)
        if ignore_same and oa == ob:
            continue
        ib = r.interferenceBody
        v = ib.volume * 1000.0
        bb = ib.boundingBox
        out.append((oa, ob, r.entityOne.name, r.entityTwo.name, v,
                    [bb.minPoint.x * 10, bb.minPoint.y * 10, bb.minPoint.z * 10],
                    [bb.maxPoint.x * 10, bb.maxPoint.y * 10, bb.maxPoint.z * 10]))
    return out


def _bb(b):
    bb = b.boundingBox
    return (bb.minPoint.x * 10, bb.minPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.x * 10, bb.maxPoint.y * 10, bb.maxPoint.z * 10)


def _ovl(a, b, tol=0.01):
    return all(a[i] <= b[i + 3] + tol and b[i] <= a[i + 3] + tol for i in range(3))


def _merge(bbs):
    return tuple(min(b[i] for b in bbs) for i in range(3)) + tuple(max(b[i + 3] for b in bbs) for i in range(3))


EXPECTED = {("board_power", "usb_c1"): "mid-mount USB-C legs/pads in the board cut-out",
            ("board_power", "usb_c2"): "mid-mount USB-C legs/pads in the board cut-out",
            ("board_carrier", "epaper_fpc"): "FPC inserted in J13",
            ("bat_leads", "cell"): "lead continues the cell's lead stub",
            ("board_carrier", "spk_chamber_L"): "H1/H2 bosses seated on the carrier",
            ("screws", "spk_chamber_L"): "screws in the H1/H2 bosses"}


def fit_check():
    """Interference between every two parts whose boxes overlap (one analyzeInterference call per part pair:
    a single call over all ~600 bodies returns nothing because of the Amphenol USB-C shell). Same-part overlaps
    are ignored; overlaps under 0.001 mm3 are counted as touching, not clashes."""
    bodies = [b for b in all_bodies() if not owner_of(b).startswith("cable_exit")]
    by = {}
    for b in bodies:
        by.setdefault(owner_of(b), []).append((b, _bb(b)))
    obox = {o: _merge([x[1] for x in v]) for o, v in by.items()}
    owners = sorted(by)
    log("interference: %d bodies, %d parts" % (len(bodies), len(owners)))
    res_all, calls, fallback = [], 0, 0
    for i, a in enumerate(owners):
        for b in owners[i + 1:]:
            if not _ovl(obox[a], obox[b]):
                continue
            A = [x for x, bb in by[a] if _ovl(bb, obox[b])]
            B = [x for x, bb in by[b] if _ovl(bb, obox[a])]
            if not A or not B:
                continue
            calls += 1
            res = interference(A + B)
            if res is None:
                fallback += 1
                res = []
                for x in A:
                    for y in B:
                        if _ovl(_bb(x), _bb(y)):
                            r = interference([x, y])
                            res += r or []
            res_all += res
    pairs, touch, expected, detail = {}, set(), {}, []
    for oa, ob, na, nb, v, lo, hi in res_all:
        key = tuple(sorted((oa, ob)))
        if v < 0.001:
            touch.add(key)
            continue
        detail.append(dict(a=oa, b=ob, body_a=na, body_b=nb, vol=round(v, 4), lo=[round(x, 2) for x in lo], hi=[round(x, 2) for x in hi]))
        if key in EXPECTED:
            expected[key] = expected.get(key, 0.0) + v
            continue
        p = pairs.setdefault(key, [0.0, lo[:], hi[:], set(), 0])
        p[0] += v
        p[1] = [min(p[1][i], lo[i]) for i in range(3)]
        p[2] = [max(p[2][i], hi[i]) for i in range(3)]
        p[3].update((na if oa == key[0] else nb, nb if oa == key[0] else na))
        p[4] += 1
    rows = []
    for (a, b), (v, lo, hi, names, n) in sorted(pairs.items(), key=lambda kv: -kv[1][0]):
        d = [hi[i] - lo[i] for i in range(3)]
        rows.append(dict(a=a, b=b, vol=v, n=n, lo=lo, hi=hi, size=d, names=sorted(names)[:6]))
    G["clashes"] = rows
    G["clash_detail"] = sorted(detail, key=lambda d: -d["vol"])
    G["touch"] = sorted(touch - set(pairs) - set(expected))
    lines = ["%s x %s: %.3f mm3 (%d body pairs), overlap %.2f x %.2f x %.2f at X %.2f..%.2f Y %.2f..%.2f Z %.2f..%.2f  [%s]" % (
        r["a"], r["b"], r["vol"], r["n"], r["size"][0], r["size"][1], r["size"][2], r["lo"][0], r["hi"][0], r["lo"][1], r["hi"][1],
        r["lo"][2], r["hi"][2], ", ".join(r["names"])) for r in rows]
    msg = ("INTERFERENCE: %d bodies in %d parts, %d part pairs checked (%d needed body-by-body), %d clashing pairs, "
           "%d touching pairs (0 volume)\n  %s\n  touching: %s\n  expected contacts (not clashes): %s" % (
               len(bodies), len(owners), calls, fallback, len(rows), len(G["touch"]), "\n  ".join(lines),
               ", ".join("%s/%s" % t for t in G["touch"]),
               "; ".join("%s/%s %.3f mm3 (%s)" % (k[0], k[1], v, EXPECTED[k]) for k, v in expected.items())))
    return msg, rows


def dist(a, b):
    return adsk.core.Application.get().measureManager.measureMinimumDistance(a, b).value * 10.0


def box_gap(a, b):
    """Gap between two bounding boxes (mm), 0 if they overlap."""
    ga = [max(a.minPoint.x - b.maxPoint.x, b.minPoint.x - a.maxPoint.x, 0),
          max(a.minPoint.y - b.maxPoint.y, b.minPoint.y - a.maxPoint.y, 0),
          max(a.minPoint.z - b.maxPoint.z, b.minPoint.z - a.maxPoint.z, 0)]
    return math.sqrt(sum(g * g for g in ga)) * 10.0


METAL_OWNERS = ("board_", "cell", "oled", "usb_c", "pogo_pad", "dock_magnet", "speaker_L", "speaker_R", "qi_magnet", "qi_coil",
                "qi_ferrite", "qi_tx", "screws", "lra", "standins", "epaper_panel", "gnss_gnd", "btn_pcb", "switches", "bat_leads",
                "mr30_plug", "wifi_flexpifa", "gnss_patch", "lte", "bt_ant")


def antenna_check(limit=5.0):
    ants = {"Wi-Fi FlexPIFA": ["wifi_flexpifa"], "GNSS patch": ["gnss_patch", "gnss_gnd"], "LTE flex": ["lte_flex"],
            "BT FPC": ["bt_ant"]}
    bodies = all_bodies()
    out = ["ANTENNA CLEARANCE (copper/metal within %.0f mm; the antenna's own feed board/cable excluded)" % limit]
    for label, owners in ants.items():
        mine = [b for b in bodies if owner_of(b) in owners]
        others = [b for b in bodies if owner_of(b) not in owners and owner_of(b).startswith(METAL_OWNERS)
                  and not (label == "GNSS patch" and owner_of(b) in ("gnss_patch", "gnss_gnd"))]
        hits = {}
        for a in mine:
            for o in others:
                if box_gap(a.boundingBox, o.boundingBox) > limit:
                    continue
                d = dist(a, o)
                if d < limit:
                    k = owner_of(o) + "/" + o.name
                    hits[k] = min(d, hits.get(k, 99))
        worst = sorted(hits.items(), key=lambda kv: kv[1])
        out.append("  %s: %s" % (label, "OK, nothing within %.0f mm" % limit if not worst else
                                 "%d items within %.0f mm: %s" % (len(worst), limit, "; ".join("%s %.2f" % kv for kv in worst[:12]))))
    return "\n".join(out)


def power_back_check():
    occ = G["occ"].get("board_power")
    if not occ:
        return "POWER BOARD BACK SIDE: board not imported"
    bz = Q["board_z"]
    rows = []
    for b in occ_bodies(occ):
        bb = b.boundingBox
        if bb.maxPoint.z * 10 <= bz + 0.05 and bb.minPoint.z * 10 < bz - 0.05:
            rows.append((bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10, bb.minPoint.z * 10, b.name))
    bad = [r for r in rows if r[0] < 47.0]
    cell_top = Q["cell_pad"] + Q["cell_t"]
    lines = ["POWER BOARD BACK SIDE (rule: nothing on the back at X < 47, the cell + 1.2 swell gap is under it)",
             "  back-side bodies: %d, of them at X < 47: %d" % (len(rows), len(bad))]
    for r in sorted(bad)[:20]:
        lines.append("    %s X %.2f..%.2f Y %.2f..%.2f bottom Z %.2f (cell top %.1f, gap left %.2f)" % (r[5], r[0], r[1], r[2], r[3], r[4], cell_top, r[4] - cell_top - Q["insul"]))
    if rows:
        lowest = min(rows, key=lambda r: r[4])
        lines.append("  lowest back-side part: %s bottom Z %.2f at X %.1f..%.1f" % (lowest[5], lowest[4], lowest[0], lowest[1]))
    return "\n".join(lines)


def pair_dist(a_owner, b_owner):
    bodies = all_bodies()
    A = [b for b in bodies if owner_of(b) == a_owner or b.name == a_owner]
    B = [b for b in bodies if owner_of(b) == b_owner or b.name == b_owner]
    best = (99.0, None, None)
    for a in A:
        for b in B:
            if box_gap(a.boundingBox, b.boundingBox) > best[0]:
                continue
            d = dist(a, b)
            if d < best[0]:
                best = (d, a.name, b.name)
    return best


def clearance_checks():
    out = ["CLEARANCES (minimum distance, mm; 0 = touching or overlapping)"]
    pairs = [
        ("board_power", "speaker_box_R", "power board vs speaker box R"),
        ("board_carrier", "speaker_box_L", "carrier vs speaker box L"),
        ("qi_tx", "speaker_box_R", "Qi TX board vs speaker box R"),
        ("qi_magnet", "speaker_box_R", "Qi magnet ring vs speaker box R"),
        ("qi_tx", "board_power", "Qi TX board vs power board"),
        ("usb_c2", "speaker_box_R", "USB-C 2 vs speaker box R"),
        ("standins", "speaker_box_R", "power-board stand-ins (J7 PH, L3...) vs speaker box R"),
        ("btn_pcb", "speaker_box_L", "button PCB vs speaker box L"),
        ("lid", "dock_magnet_1", "lid (clips) vs magnet X -70"),
        ("lid", "dock_magnet_2", "lid (clips) vs magnet X -32"),
        ("lid", "dock_magnet_3", "lid (clips) vs magnet X +32"),
        ("lid", "dock_magnet_4", "lid (clips) vs magnet X +70"),
        ("lid", "pogo_pad_1", "lid (clip X -10) vs pogo pad X -12"),
        ("lid", "pogo_pad_2", "lid vs pogo pad X -4"),
        ("epaper_fpc", "cell", "e-paper FPC vs cell"),
        ("epaper_fpc", "lid", "e-paper FPC vs lid (clips/tongue)"),
        ("epaper_fpc", "board_carrier", "e-paper FPC vs carrier"),
        ("screws", "insulator", "carrier screw heads vs cell insulator"),
        ("screws", "cell", "carrier screw heads vs cell"),
        ("bracket", "oled", "bracket vs OLED panel/FPC"),
        ("lra", "speaker_box_L", "LRA vs speaker box L"),
        ("lra", "cell", "LRA vs cell"),
        ("mr30_pair", "cell", "MR30 pair vs cell"),
        ("mr30_pair", "board_power", "MR30 pair vs power board (back-side parts)"),
        ("mr30_pair", "lid", "MR30 pair vs lid (posts, clips)"),
        ("mr30_pair", "qi_tx", "MR30 pair vs Qi TX board"),
        ("mr30_pair", "bt_ant", "MR30 pair vs BT antenna"),
        ("mr30_pair", "dock_magnet_4", "MR30 pair vs magnet X +70"),
        ("pigtail", "cell", "pigtail vs cell"),
        ("pigtail", "board_power", "pigtail vs power board"),
        ("pigtail", "mr30_pair", "pigtail vs MR30 pair (enters its +Y end)"),
        ("bat_leads", "lid", "battery leads vs lid (clip X +50)"),
        ("bat_leads", "mr30_pair", "battery leads vs MR30 pair (enter its -Y end)"),
        ("spk_chamber_L", "wifi_flexpifa", "chamber L vs Wi-Fi PIFA"),
        ("spk_chamber_L", "gnss_patch", "chamber L vs GNSS patch"),
        ("spk_chamber_L", "gnss_gnd", "chamber L vs GNSS ground board"),
        ("spk_chamber_L", "lte_flex", "chamber L vs LTE flex"),
        ("spk_chamber_L", "oled", "chamber L vs OLED (incl. folded FPC)"),
        ("spk_chamber_L", "board_carrier", "chamber L vs carrier parts (bosses seated)"),
        ("spk_chamber_L", "front_shell", "chamber L vs shell (ribs, walls)"),
        ("spk_chamber_R", "lte_flex", "chamber R vs LTE flex"),
        ("spk_chamber_R", "bt_ant", "chamber R vs BT antenna"),
        ("spk_chamber_R", "wifi_flexpifa", "chamber R vs Wi-Fi PIFA"),
        ("spk_chamber_R", "qi_ferrite", "chamber R vs Qi ferrite"),
        ("spk_chamber_R", "qi_coil", "chamber R vs Qi coil"),
        ("spk_chamber_R", "qi_magnet", "chamber R vs Qi magnet ring"),
        ("spk_chamber_R", "qi_tx", "chamber R vs Qi TX board"),
        ("spk_chamber_R", "board_power", "chamber R vs power board parts"),
        ("spk_chamber_R", "standins", "chamber R vs stand-ins (inductors, SH)"),
        ("spk_chamber_R", "usb_c1", "chamber R vs USB-C 1"),
        ("spk_chamber_R", "front_shell", "chamber R vs shell (ribs, walls)"),
        ("usb_c1", "front_shell", "USB-C 1 vs shell opening"),
        ("usb_c2", "front_shell", "USB-C 2 vs shell opening"),
        ("speaker_L", "front_shell", "speaker L vs shell (corners)"),
        ("cell", "board_power", "cell vs power board"),
    ]
    G["clear"] = {}
    for a, b, label in pairs:
        try:
            d, na, nb = pair_dist(a, b)
            G["clear"][label] = d
            out.append("  %-58s %6.2f  (%s / %s)" % (label, d, na, nb))
        except Exception as e:
            out.append("  %-58s could not measure (%s)" % (label, e))
    return "\n".join(out)


def cable_exit_check():
    """Puts the cable-exit envelopes in, runs interference against the rest, reports, deletes them."""
    p = os.path.join(BOARDS, "standins.json")
    pcbn = os.path.join(BOARDS, "connectors.json")
    if not os.path.isfile(pcbn):
        return "CABLE EXITS: connectors.json missing (board_standins.py writes it)"
    conns = json.load(open(pcbn))
    made = []
    for c in conns:
        key = (c["board"], c["ref"])
        if OVERRIDE.get(key):
            c = dict(c, **OVERRIDE[key])
        d = G["exits"].get(key)
        if not d:
            continue
        z0 = BOARD_Z[c["board"]] + BOARD_T[c["board"]]
        x0, y0, x1, y1 = c["x0"], c["y0"], c["x1"], c["y1"]
        ln = 3.0
        if d == "+Y":
            bb = (x0, x1, y1, y1 + ln)
        elif d == "-Y":
            bb = (x0, x1, y0 - ln, y0)
        elif d == "+X":
            bb = (x1, x1 + ln, y0, y1)
        else:
            bb = (x0 - ln, x0, y0, y1)
        b = add("cable_exit_%s_%s" % key, box(bb[0], bb[1], bb[2], bb[3], z0, z0 + 2.95), "cable_exit_%s_%s" % key)
        if b:
            made.append(b)
    others = [b for b in all_bodies() if not owner_of(b).startswith("cable_exit")]
    lines = ["CABLE EXITS (plug + 3 mm wire bend past each cable connector, 2.95 high)"]
    for b in made:
        tgt = [o for o in others if box_gap(o.boundingBox, b.boundingBox) < 0.01]
        hits = []
        if tgt:
            res = interference([b] + tgt)
            for oa, ob, na, nb, v, lo, hi in (res or []):
                if v < 0.001:
                    continue
                other = ob if oa.startswith("cable_exit") else oa
                if (b.name.endswith("J13") and other == "epaper_fpc") or (b.name.endswith("J11") and other == "oled"):
                    continue
                hits.append("%s %.2f mm3" % (other + "/" + (nb if oa.startswith("cable_exit") else na), v))
        lines.append("  %-30s %s" % (b.name[11:], "clear" if not hits else "BLOCKED by " + "; ".join(hits[:5])))
    for b in made:
        occ = G["occ"].pop(owner_of(b), None)
        if occ:
            occ.deleteMe()
    return "\n".join(lines)


def haptic_envelope_check():
    hw = 20.0
    t = box(Q["lra_x0"], Q["lra_x1"], -hw, hw, Q["cell_pad"], Q["cell_pad"] + 10.0)
    b = add("haptic_envelope", t)
    if not b:
        return "HAPTIC ENVELOPE: could not build"
    others = [o for o in all_bodies() if owner_of(o) not in ("haptic_envelope", "lra") and box_gap(o.boundingBox, b.boundingBox) < 0.01]
    res = interference([b] + others) if others else []
    hits = ["%s %.2f mm3" % (oa if ob == "haptic_envelope" else ob, v) for oa, ob, na, nb, v, lo, hi in (res or [])
            if v > 0.001 and "haptic_envelope" in (oa, ob)]
    G["occ"].pop("haptic_envelope").deleteMe()
    return "HAPTIC: modelled at the Vybronics size 10 x 10 x 4; the brief's 10 x 40 x 10 envelope (X -70..-60, Y +-20, Z 1..11) %s" % (
        "is clear" if not hits else "clashes with " + "; ".join(hits))


def mass_estimate():
    known = {"cell": (160.0, "given"), "speaker_L": (28.0, "estimate, Dayton weight not found"),
             "speaker_R": (28.0, "estimate, Dayton weight not found"), "lra": (2.0, "estimate")}
    rows, tot = [], 0.0
    for name, occ in sorted(G["occ"].items()):
        if name in known:
            g, src = known[name]
        else:
            bodies = occ_bodies(occ)
            vol = sum(b.volume for b in bodies)                    # cm3
            dens = mat_of(name)[0]
            if name.startswith("board_"):
                dens, src = 2.2, "STEP volume x 2.2 (FR4 + parts)"
            elif name in ("oled",):
                dens, src = 2.5, "volume x 2.5 (glass)"
            elif name.startswith(("usb_c", "pogo_pad")):
                dens, src = 4.0, "volume x 4.0 (metal + LCP)"
            elif name.startswith("dock_magnet"):
                dens, src = 7.5, "NdFeB"
            elif name in ("wifi_flexpifa", "gnss_patch"):
                dens, src = 2.0 if name == "wifi_flexpifa" else 3.5, "volume x density (estimate)"
            else:
                src = "volume x %.2f" % (dens or 0)
            if dens is None:
                dens = 1.5
            g = vol * dens
        rows.append((name, g, src))
        tot += g
    lines = ["MASS ESTIMATE: %.0f g total (fabric, glue, wires not included: add about 10 g)" % tot]
    for n, g, src in sorted(rows, key=lambda r: -r[1]):
        if g >= 0.5:
            lines.append("  %-22s %7.1f g  %s" % (n, g, src))
    G["mass"] = tot
    return "\n".join(lines)


def volume_report():
    lines = ["BACK VOLUME per speaker (cc; air behind the cone: box cavity + plate opening - magnet - basket frame 1.0 est.)"]
    for tag in ("L", "R"):
        v = G.get("vol", {}).get(tag)
        if not v or "after" not in v:
            lines.append("  %s: not computed" % tag)
            continue
        lines.append("  %s: before %.1f cc; chamber %.1f cc + back-wall opening %.1f cc; after %.1f cc (x%.2f)" % (
            tag, v["before"], v["chamber"], v["hole"], v["after"], v["after"] / v["before"]))
    return "\n".join(lines)


def routes_report():
    ey = Q["ep_y"] / 2
    fpc = G.get("fpc_len", 0)
    lines = [
        "ROUTES (lengths along the modelled path, mm)",
        "  e-paper FPC (24 p, 0.5 pitch, assumed 13 wide at X -10.5..2.5): panel edge Y %.2f -> lid groove (0.4 deep) to Y -31.25 "
        "(0.85 past the cell side, 0.75 inside the clip arm at X -10) -> up the cell side to Z 15.35 -> over the carrier to J13 "
        "(Y -15.6): %.0f mm. To open the lid it needs a service loop: lid travel to clear the clips and tongue is about 5 mm, "
        "laying the lid flat beside the shell needs about 40 mm more -> order a 24 p 0.5 mm FPC extension of 60-80 mm, or "
        "use a 24 p FFC jumper with a ZIF on the lid side." % (-ey, fpc),
        "  speaker L: box back-wall hole (-71.8, 0, 26) -> carrier J4 (-58.7, -7) left edge: about 13 X + 7 Y + 11 Z = ~31 mm + slack",
        "  speaker R: box back-wall hole (71.8, 0, 26) -> power J7 (68, 9), cable +X: about 4 X + 9 Y + 9 Z = ~22 mm",
        "  haptic: LRA pads (-65, 0, 3) -> carrier J6 (-50, -14.2), cable -Y: about 15 X + 14 Y + 12 Z = ~41 mm, round the carrier's left-bottom corner",
        "  buttons: button PCB (X -70..-19, Y 30.6) -> carrier J12 (-38.35, 26.6), cable +Y: about 4 Y + 5 Z = ~10 mm (see the cable-exit result)",
        "  front sensor: wire pads (-66.2, 25.4, Z 28.15) -> carrier J8 (-56, 26.6): about 10 X + 13 Z = ~25 mm",
        "  touch strip: pads (-17.8, 29.75, Z 30.5) -> carrier J7 (-46.5, 26.6): about 29 X + 3 Y + 15 Z = ~47 mm",
        "  battery: MR30 off the power board. Pigtail 2 x 18 AWG from TP1/TP2 (46.8, -13/-8, top side) over the board's bottom "
        "edge (Y -16) and back under the board (Z 10.3) into the female MR30's +Y end: %.0f mm. Cell leads (AWG22 on the "
        "drawing) from the PCM end (X 46.5..50.5, Y -21/-25) round the pair's -Y end into the male MR30: %.0f mm of the 100 mm "
        "leads (coil the rest beside the pair). Mated pair %s assumed 16 x 26.5 x 8: verify." % (
            G.get("pigtail_len", 0), G.get("batlead_len", 0), "X %.1f..%.1f Y %.1f..%.1f Z %.1f..%.1f" % MR30_PAIR),
    ]
    return "\n".join(lines)


def dims_report():
    w = Q["usb_open_w"]
    h = Q["usb_open_h"]
    # Amphenol shell: 8.94 x 3.26 nominal (USB-C receptacle shell)
    lines = [
        "KEY NUMBERS",
        "  stack: lid %.1f + interior %.1f + front wall %.1f = %.1f; + fabric 0.6 + Qi ring 0.4 + back ring 1.5 proud = %.1f overall" % (
            LT, ZI, ZF - ZI, LT + ZF, LT + ZF + 0.6 + 0.4 + Q["ring_proud"]),
        "  front wall %.1f: lens pocket floor Z %.2f leaves %.2f under the lens ledge; tuck groove floor Z %.2f leaves %.2f; "
        "touch pocket %.2f deep (wall over the strip %.1f), strip %.2f proud inside" % (
            ZF - ZI, ZF - Q["lens_pocket_d"], ZF - Q["lens_pocket_d"] - ZI, ZF - Q["tuck_d"], ZF - Q["tuck_d"] - ZI,
            max(ZF - Q["touch_wall"] - ZI, 0), Q["touch_wall"], ZI - Q["touch_z"]),
        "  cell Z %.1f..%.1f, insulator to %.1f, board layer Z %.1f: swell gap %.2f" % (
            Q["cell_pad"], Q["cell_pad"] + Q["cell_t"], Q["cell_pad"] + Q["cell_t"] + Q["insul"], Q["board_z"],
            Q["board_z"] - Q["cell_pad"] - Q["cell_t"] - Q["insul"]),
        "  USB-C openings %.1f x %.1f (R %.1f) centred Z %.2f; receptacle mating face %.2f inside the wall's inner face "
        "(%.2f below the outer face, %.2f below the fabric)" % (w, h, h / 2, Q["usb_zc"], 0.2 + Q["usb_inset"],
                                                               WALL + 0.2 + Q["usb_inset"], WALL + 0.2 + Q["usb_inset"] + Q["fabric"]),
        "  grille: %d holes per end" % len(grille_centres()),
    ]
    return "\n".join(lines)


# ================================================================================================ BUILD
def build(report=None):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
    G["design"] = design
    G["base_app"] = _base_appearance()
    design.attributes.add("ansonia", "build", "revG")
    out = []
    try:
        build_front_shell(); log("front shell")
        build_lid(); log("lid")
        build_lid_parts(); log("lid parts")
        build_signature(design); log("signature")
        build_front_parts(); log("front parts")
        build_speakers(); log("speakers")
        build_chambers(); log("chambers")
        build_qi(); log("qi")
        build_misc_parts(); log("misc")
        build_standins(); log("standins")
        build_cable_exits()
        build_real(); log("real parts")
        app.activeViewport.fit()
        out.append(dims_report())
        msg, rows = fit_check(); log("fit check")
        out.append(msg)
        out.append(power_back_check()); log("power back")
        out.append(clearance_checks()); log("clearances")
        out.append(antenna_check()); log("antennas")
        out.append(cable_exit_check()); log("cable exits")
        out.append(haptic_envelope_check()); log("haptic")
        out.append(volume_report())
        out.append(routes_report())
        out.append(mass_estimate()); log("mass")
    except Exception:
        out.append("BUILD STOPPED:\n" + traceback.format_exc())
    head = "ANSONIA rev G build, %d components, %.0f s\n" % (len(G["occ"]), time.time() - G["t0"])
    if G["fails"]:
        head += "Could not build / warnings: %s\n" % "; ".join(G["fails"])
    if PARAM_NOTES:
        head += "Params: %s\n" % "; ".join(PARAM_NOTES)
    text = head + "\n\n".join(out) + "\n\nLOG\n" + "\n".join(G["log"])
    if report:
        with open(report, "w", encoding="utf-8") as f:
            f.write(text)
        if G.get("clashes") is not None:
            with open(os.path.splitext(report)[0] + "_clashes.json", "w") as f:
                json.dump({"pairs": G["clashes"], "bodies": G.get("clash_detail", [])}, f, indent=1)
    return text


# ================================================================================================ EXPORTS
PRINT = {   # component -> (file, rotation spec, supports note)
    "front_shell": ("ansonia_front_shell_PETG.3mf", "flipZ", "front face on the plate; no supports (the clip ledges print as 2.4 mm overhangs, bridges over the USB-C and button windows)"),
    "lid": ("ansonia_lid_PETG.3mf", "none", "back face on the plate; no supports; bridges: ring channel 4 mm, plate recess 18 mm, cover-recess ledge 1.5 mm"),
    "speaker_box_L": ("ansonia_speaker_box_L_PETG.3mf", "boxL", "back wall on the plate; no supports (front plate prints as a 2-3 mm inward ledge, chamfer advised)"),
    "speaker_box_R": ("ansonia_speaker_box_R_PETG.3mf", "boxR", "back wall on the plate; no supports (front plate as a 2-3 mm inward ledge)"),
    "bracket": ("ansonia_carrier_bracket_PETG.3mf", "none", "carrier side on the plate; bars print as bridges 16-34 mm at 11 mm height (add supports under the bars if they sag)"),
    "button_strip": ("ansonia_button_strip_TPU.3mf", "stripUp", "icons up; tree supports from the plate under the strip (nubs 1.5 mm hang below it)"),
    "back_ring": ("ansonia_back_ring_TPU.3mf", "none", "flat; no supports"),
    "trim_L": ("ansonia_trim_L_PLA-silk.3mf", "endL", "flat; no supports"),
    "trim_R": ("ansonia_trim_R_PLA-silk.3mf", "endR", "flat; no supports"),
    "sig_plate": ("ansonia_signature_plate_PLA-silk.3mf", "flipZ", "text face up; no supports"),
    "spk_chamber_L": ("ansonia_spk_chamber_L_PETG.3mf", "flipZ", "top face down, H1/H2 bosses up; the floor bridges <= 15 mm between the inner pillars; no supports (sealed)"),
    "spk_chamber_R": ("ansonia_spk_chamber_R_PETG.3mf", "flipZ", "top face down; the floor bridges <= 15 mm between the inner pillars; no supports (sealed)"),
}


def _orient(body, spec):
    b = TB.copy(body)
    m = adsk.core.Matrix3D.create()
    if spec == "flipZ":          # 180 deg about X
        m.setToRotation(math.pi, Vec(1, 0, 0), P(0, 0, 0))
    elif spec == "boxL":         # back wall (+X side of box L) down: +X -> -Z
        m.setToRotation(math.pi / 2, Vec(0, 1, 0), P(0, 0, 0))
    elif spec == "boxR":         # back wall (-X side) down: -X -> -Z
        m.setToRotation(-math.pi / 2, Vec(0, 1, 0), P(0, 0, 0))
    elif spec == "stripUp":      # +Y (outer face) -> +Z
        m.setToRotation(math.pi / 2, Vec(1, 0, 0), P(0, 0, 0))
    elif spec == "endL":         # outer face (-X) up
        m.setToRotation(math.pi / 2, Vec(0, 1, 0), P(0, 0, 0))
    elif spec == "endR":
        m.setToRotation(-math.pi / 2, Vec(0, 1, 0), P(0, 0, 0))
    TB.transform(b, m)
    bb = b.boundingBox
    t = adsk.core.Matrix3D.create()
    t.translation = Vec(-(bb.minPoint.x + bb.maxPoint.x) / 2, -(bb.minPoint.y + bb.maxPoint.y) / 2, -bb.minPoint.z)
    TB.transform(b, t)
    return b


def exports(out_dir):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    G["design"] = design
    em = design.exportManager
    os.makedirs(out_dir, exist_ok=True)
    root = design.rootComponent
    done = []
    tmp_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    tmp_occ.component.name = "_print_tmp"
    try:
        for cname, (fn, spec, note) in PRINT.items():
            occ = next((o for o in root.occurrences if o.component.name == cname), None)
            if not occ or occ.component.bRepBodies.count == 0:
                done.append("%s: missing" % cname)
                continue
            b = tmp_occ.component.bRepBodies.add(_orient(occ.component.bRepBodies.item(0), spec))
            b.name = cname
            o = em.createC3MFExportOptions(b, os.path.join(out_dir, fn))
            try:
                o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            except Exception:
                pass
            em.execute(o)
            bb = b.boundingBox
            done.append("%s: %s, %.1f x %.1f x %.1f on the plate; %s" % (
                fn, cname, (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10, (bb.maxPoint.z - bb.minPoint.z) * 10, note))
            b.deleteMe()
    finally:
        tmp_occ.deleteMe()
    em.execute(em.createSTEPExportOptions(os.path.join(out_dir, "ansonia_revG_assembly.step"), root))
    done.append("ansonia_revG_assembly.step")
    try:
        em.execute(em.createFusionArchiveExportOptions(os.path.join(out_dir, "ansonia_revG.f3d"), root))
        done.append("ansonia_revG.f3d")
    except Exception as e:
        done.append("f3d failed: %s" % e)
    text = "\n".join(done)
    with open(os.path.join(out_dir, "exports.txt"), "w") as f:
        f.write(text)
    return text


# ================================================================================================ SCREENSHOTS
def _cam(vp, eye, target, up):
    cam = vp.camera
    cam.isSmoothTransition = False
    cam.target = P(*target)
    cam.eye = P(*eye)
    cam.upVector = Vec(*up)
    cam.isFitView = True
    vp.camera = cam
    adsk.doEvents()


def _plane(axis, val):
    root = G["design"].rootComponent
    base = {"x": root.yZConstructionPlane, "y": root.xZConstructionPlane, "z": root.xYConstructionPlane}[axis]
    pi = root.constructionPlanes.createInput()
    pi.setByOffset(base, adsk.core.ValueInput.createByReal(val * MM))
    pl = root.constructionPlanes.add(pi)
    pl.isLightBulbOn = False
    return pl


def _section(axis, val, flip=False):
    root = G["design"].rootComponent
    base = {"x": root.yZConstructionPlane, "y": root.xZConstructionPlane, "z": root.xYConstructionPlane}[axis]
    sa = G["design"].analyses.sectionAnalyses
    si = sa.createInput(base, val * MM)
    try:
        si.isHatchShown = True
    except Exception:
        pass
    s = sa.add(si)
    if flip:
        s.flip()
    return s


def screenshots(out_dir):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    G["design"] = design
    vp = app.activeViewport
    root = design.rootComponent
    os.makedirs(out_dir, exist_ok=True)
    done = []
    W, H = 2400, 1350
    # 1 exploded: lid parts down, shell up, front parts further up
    off = {"front_shell": 60, "lens": 75, "foam_lens": 70, "ir_window": 70, "trim_L": 60, "trim_R": 60, "eptfe_L": 45, "eptfe_R": 45,
           "button_strip": 60, "lid": -45, "gasket_cord": -30, "back_ring": -70, "sig_plate": -62, "epaper_cover": -62,
           "epaper_panel": -38, "epaper_fpc": -38, "foam_cell": -20, "oled": 42, "front_touch": 50, "board_front_touch": 50,
           "board_front_sensor": 42, "foam_mic": 42, "qi_magnet": 42, "qi_coil": 38, "qi_ferrite": 34, "wifi_flexpifa": 42,
           "gnss_patch": 42, "gnss_gnd": 38, "bracket": 22, "board_carrier": 10, "screws": 4, "board_power": 10, "standins": 10,
           "usb_c1": 10, "usb_c2": 10, "mr30_plug": 10, "bat_leads": 10, "insulator": -8, "cell": -15, "lra": -30}
    xoff = {"speaker_L": -30, "speaker_box_L": -22, "foam_spk_face_L": -36, "foam_spk_box_L": -26,
            "speaker_R": 30, "speaker_box_R": 22, "foam_spk_face_R": 36, "foam_spk_box_R": 26}
    saved = []
    for oc in root.occurrences:
        n = oc.component.name
        dz, dx = off.get(n, 0), xoff.get(n, 0)
        if dz or dx:
            saved.append((oc, oc.transform2.copy()))
            m = oc.transform2
            v = m.translation
            v.add(Vec(dx * MM, 0, dz * MM))
            m.translation = v
            oc.transform2 = m
    _cam(vp, (260, -330, 170), (0, 0, 14), (0, 0, 1))
    vp.saveAsImageFile(os.path.join(out_dir, "revG_exploded.png"), W, H)
    done.append("revG_exploded.png")
    for oc, m in saved:
        oc.transform2 = m
    try:
        if design.snapshots.hasPendingSnapshot:
            design.snapshots.revertPendingSnapshot()
    except Exception:
        pass
    # 2 section through the middle (Y = 0), seen from -Y
    for fn, axis, val, eye, up, flip in (("revG_section_middle_Y0.png", "y", 0.0, (0, -400, 14), (0, 0, 1), True),
                                         ("revG_section_speaker_L_X-82.png", "x", -82.0, (400, -60, 14), (0, 0, 1), False)):
        try:
            s = _section(axis, val, flip)
            _cam(vp, eye, (0 if axis == "y" else val, 0, 14), up)
            vp.saveAsImageFile(os.path.join(out_dir, fn), W, H)
            s.deleteMe()
            done.append(fn)
        except Exception as e:
            done.append("%s failed: %s" % (fn, e))
    # 4 back with the e-paper (from behind), iso front
    _cam(vp, (0, 0, -400), (0, 0, 0), (0, 1, 0))
    vp.saveAsImageFile(os.path.join(out_dir, "revG_back_epaper.png"), W, H)
    done.append("revG_back_epaper.png")
    _cam(vp, (230, -260, 300), (0, 0, 14), (0, 0, 1))
    vp.saveAsImageFile(os.path.join(out_dir, "revG_iso_front.png"), W, H)
    done.append("revG_iso_front.png")
    text = "\n".join(done)
    with open(os.path.join(out_dir, "screenshots.txt"), "w") as f:
        f.write(text)
    return text
