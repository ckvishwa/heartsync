"""
heartsync - detailed enclosure + internals (Fusion 360 script, Python)

Builds:
  * tray (front shell) with display window, ring groove, speaker grille, mic and
    light-sensor holes, touch-strip groove, USB-C and mute-switch cutouts
  * lid (back cover) with dock magnet pockets and pogo contact pads
  * every internal part with colour: Qi2 coil (ferrite, windings, magnet ring),
    10,000 mAh pouch cell + protection board, 500 mAh backup cell, power bank /
    USB-C PD board, Qi2 transmitter board, speaker, main PCB with an
    ESP32-S3-WROOM-1 module (shield can, antenna, pads), amp, haptic driver, IMU,
    connectors and passives, SIM7080G board with nano-SIM holder and U.FL
    connectors, GNSS patch antenna, LTE flex antenna, haptic LRA, OLED glass +
    flex cable, touch strip, mic, light sensor, mute switch
  * wiring as real round wires (and coax for the antennas)

EXPLODE = False -> normal stack with a fit (interference) check
EXPLODE = True  -> exploded view (layers pulled apart upward, no wires)

Sizes in mm. Part sizes are close to real parts but several are estimates -
replace them when the real parts arrive.
Axes: X = 152 length, Y = 72.5 width, Z = thickness. Front face is +Z.
"""
import adsk.core
import adsk.fusion
import traceback
import math

# ----------------------------------------------------------------------
# SETTINGS
# ----------------------------------------------------------------------
EXPLODE = False
EXPLODE_GAP = 25.0
WIRES = True

DISPLAY = "2.7"            # "2.7" or "3.12"

LENGTH, WIDTH = 152.0, 72.5
THICKNESS = 32.0           # tray + lid (31 was 0.1 mm short with the swell gap)
WALL = 2.2
LID = 2.2
CORNER_R = 6.0
SWELL = 1.2                # free space above the 10,000 mAh cell

RING_CX = 43.0             # decorative ring on the front, Qi2 coil behind it on the back
RING_DIA = 56.0
SPK_C = (47.0, 18.0)       # speaker centre (fires through the grille inside the ring)

if DISPLAY == "2.7":
    DCX = -34.5
    GLASS = (73.0, 41.9, 1.8)      # bare 2.7in 128x64 glass
    WIN = (63.0, 32.0)             # window over the 61.4 x 30.7 lit area
else:
    DCX = -27.0
    GLASS = (89.2, 44.0, 6.0)      # NHD-3.12-25664UCW2 module body
    WIN = (82.0, 22.0)
STRIP_C = (DCX, 28.0)

# ----------------------------------------------------------------------
# DERIVED
# ----------------------------------------------------------------------
TRAY_H = THICKNESS - LID
INNER = TRAY_H - WALL                    # inside face of the front wall
Z_CELL = 4.5                             # coil budget below the cell
CELL_T = 12.0
ABOVE = Z_CELL + CELL_T + SWELL          # main PCB bottom
PCB_T = 1.6
PCB_TOP = ABOVE + PCB_T
GLASS_Z = INNER - GLASS[2]
CELL_X0 = -LENGTH / 2.0 + WALL + 2.0     # left end of the cell
TZ = (5 * EXPLODE_GAP + 10.0) if EXPLODE else 0.0   # tray lift in exploded view

COL = {
    "shell": (235, 225, 230), "lid": (220, 205, 215),
    "pcb": (20, 110, 60), "pcb_dark": (25, 25, 30), "chip": (22, 22, 22),
    "metal": (190, 190, 195), "gold": (212, 175, 55), "copper": (200, 110, 50),
    "ferrite": (40, 40, 40), "magnet": (150, 150, 155), "cell": (70, 120, 200),
    "cell_seal": (170, 170, 175), "conn": (235, 232, 220), "passive": (200, 170, 120),
    "glass": (10, 10, 12), "fpc": (205, 125, 30), "ceramic": (210, 190, 150),
    "red": (200, 30, 30), "black": (25, 25, 25), "yellow": (230, 200, 40),
    "green": (40, 160, 60), "white": (240, 240, 240), "blue": (40, 90, 200),
    "coax": (120, 120, 120), "mic_pcb": (90, 40, 140), "als_pcb": (30, 60, 160),
    "mute": (230, 70, 30), "foam": (60, 60, 60),
}

MM = 0.1
G = {"fails": [], "parts": [], "wires": 0, "planes": {}, "apps": {}, "base_app": None}


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
    a = appearance(key)
    if a:
        try:
            body.appearance = a
        except Exception:
            pass


# ----------------------------------------------------------------------
# GEOMETRY HELPERS
# ----------------------------------------------------------------------
def shift(layer):
    """layer 1 = front group, 2 = electronics, 3 = power, 4 = coil, 5 = lid."""
    if not EXPLODE:
        return 0.0
    return {5: 0, 4: 1, 3: 2, 2: 3, 1: 4}[layer] * EXPLODE_GAP


def plane_at(z):
    comp = G["comp"]
    if abs(z) < 1e-6:
        return comp.xYConstructionPlane
    key = round(z, 3)
    if key not in G["planes"]:
        pi = comp.constructionPlanes.createInput()
        pi.setByOffset(comp.xYConstructionPlane, vi(z))
        pl = comp.constructionPlanes.add(pi)
        pl.isLightBulbOn = False
        G["planes"][key] = pl
    return G["planes"][key]


def side_plane(base, val, axis):
    comp = G["comp"]
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(base, vi(val))
    pl = comp.constructionPlanes.add(pi)
    o = pl.geometry.origin
    c = o.x if axis == "x" else o.y
    if c * val < 0:
        pl.deleteMe()
        pi = comp.constructionPlanes.createInput()
        pi.setByOffset(base, vi(-val))
        pl = comp.constructionPlanes.add(pi)
    pl.isLightBulbOn = False
    return pl


def rect(sk, cx, cy, w, h):
    sk.sketchCurves.sketchLines.addCenterPointRectangle(P(cx, cy), P(cx + w / 2.0, cy + h / 2.0))


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
    out = []
    for i in range(f.bodies.count):
        b = f.bodies.item(i)
        b.name = name if f.bodies.count == 1 else "%s_%d" % (name, i + 1)
        paint(b, color)
        if register:
            G["parts"].append(b)
        out.append(b)
    return out


def block(name, layer, color, cx, cy, z0, w, h, t):
    try:
        sk = G["comp"].sketches.add(plane_at(z0 + shift(layer)))
        rect(sk, cx, cy, w, h)
        sk.isVisible = False
        return new_bodies(sk.profiles.item(0), t, name, color)
    except Exception:
        G["fails"].append(name)
        return []


def cyl(name, layer, color, cx, cy, z0, dia, t, inner=0.0):
    try:
        sk = G["comp"].sketches.add(plane_at(z0 + shift(layer)))
        circ = sk.sketchCurves.sketchCircles
        circ.addByCenterRadius(P(cx, cy), mm(dia / 2.0))
        if inner > 0:
            circ.addByCenterRadius(P(cx, cy), mm(inner / 2.0))
            prof = smallest_profile(sk)
        else:
            prof = sk.profiles.item(0)
        sk.isVisible = False
        return new_bodies(prof, t, name, color)
    except Exception:
        G["fails"].append(name)
        return []


def grid(name, layer, color, z0, rects, t):
    """Many small disjoint rectangles in one feature (pads, passives, antenna)."""
    try:
        sk = G["comp"].sketches.add(plane_at(z0 + shift(layer)))
        for (cx, cy, w, h) in rects:
            rect(sk, cx, cy, w, h)
        sk.isVisible = False
        return new_bodies(all_profiles(sk), t, name, color)
    except Exception:
        G["fails"].append(name)
        return []


def wire(name, color, pts, dia=1.0):
    if EXPLODE or not WIRES:
        return
    comp = G["comp"]
    try:
        sk = comp.sketches.add(comp.xYConstructionPlane)
        pc = adsk.core.ObjectCollection.create()
        for p in pts:
            pc.add(P(*p))
        spl = sk.sketchCurves.sketchFittedSplines.add(pc)
        sk.isVisible = False
        path = comp.features.createPath(spl)
        pi = comp.features.pipeFeatures.createInput(
            path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        pi.sectionSize = vi(dia)
        f = comp.features.pipeFeatures.add(pi)
        for i in range(f.bodies.count):
            b = f.bodies.item(i)
            b.name = "wire_" + name
            paint(b, color)
        G["wires"] += 1
    except Exception:
        G["fails"].append("wire_" + name)


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


def cut_from_front(profiles, depth, tray):
    comp = G["comp"]
    ei = comp.features.extrudeFeatures.createInput(
        profiles, adsk.fusion.FeatureOperations.CutFeatureOperation)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(vi(depth)),
                        adsk.fusion.ExtentDirections.NegativeExtentDirection)
    ei.participantBodies = [tray]
    comp.features.extrudeFeatures.add(ei)


def side_cut(tray, plane, a, b, depth=10.0):
    """a, b = opposite model-space corners (mm) lying on the side plane."""
    comp = G["comp"]
    sk = comp.sketches.add(plane)
    p1 = sk.modelToSketchSpace(P(*a))
    p2 = sk.modelToSketchSpace(P(*b))
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(p1.x, p1.y, 0), adsk.core.Point3D.create(p2.x, p2.y, 0))
    sk.isVisible = False
    ei = comp.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
    ei.setSymmetricExtent(vi(depth), True)
    ei.participantBodies = [tray]
    comp.features.extrudeFeatures.add(ei)


# ----------------------------------------------------------------------
# SHELL
# ----------------------------------------------------------------------
def build_tray():
    comp = G["comp"]
    sk = comp.sketches.add(plane_at(TZ))
    rect(sk, 0, 0, LENGTH, WIDTH)
    sk.isVisible = False
    ei = comp.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ei.setDistanceExtent(False, vi(TRAY_H))
    tray = comp.features.extrudeFeatures.add(ei).bodies.item(0)
    tray.name = "shell_tray"
    fillet_vertical_edges(tray, CORNER_R)

    back = None
    for f in tray.faces:
        if isinstance(f.geometry, adsk.core.Plane) and abs(f.geometry.normal.z) > 0.99:
            if back is None or f.centroid.z < back.centroid.z:
                back = f
    faces = adsk.core.ObjectCollection.create()
    faces.add(back)
    si = comp.features.shellFeatures.createInput(faces)
    si.insideThickness = vi(WALL)
    comp.features.shellFeatures.add(si)

    front = plane_at(TZ + TRAY_H)

    def front_cut(name, fn, depth):
        try:
            s = comp.sketches.add(front)
            fn(s)
            s.isVisible = False
            cut_from_front(all_profiles(s) if name != "ring" else smallest_profile(s), depth, tray)
        except Exception:
            G["fails"].append("cut_" + name)

    front_cut("window", lambda s: rect(s, DCX, 0, WIN[0], WIN[1]), WALL * 1.5)
    front_cut("strip", lambda s: rect(s, STRIP_C[0], STRIP_C[1], 40.0, 5.0), 0.6)

    def ring(s):
        c = s.sketchCurves.sketchCircles
        c.addByCenterRadius(P(RING_CX, 0), mm(RING_DIA / 2.0))
        c.addByCenterRadius(P(RING_CX, 0), mm(RING_DIA / 2.0 - 1.0))
    front_cut("ring", ring, 0.6)

    def grille(s):
        c = s.sketchCurves.sketchCircles
        pitch = 2.6
        for j in range(-4, 5):
            for i in range(-4, 5):
                x = SPK_C[0] + i * pitch + (pitch / 2.0 if j % 2 else 0.0)
                y = SPK_C[1] + j * pitch * 0.866
                if math.hypot(x - SPK_C[0], y - SPK_C[1]) <= 7.0:
                    c.addByCenterRadius(P(x, y), mm(0.7))
    front_cut("grille", grille, WALL * 1.5)
    front_cut("mic_hole", lambda s: s.sketchCurves.sketchCircles.addByCenterRadius(P(-64, 28.5), mm(0.5)), WALL * 1.5)
    front_cut("light_hole", lambda s: s.sketchCurves.sketchCircles.addByCenterRadius(P(-64, -28.5), mm(1.0)), WALL * 1.5)

    # USB-C on the right end (+X), mute switch on the top edge (+Y)
    try:
        px = side_plane(comp.yZConstructionPlane, LENGTH / 2.0, "x")
        side_cut(tray, px, (LENGTH / 2.0, -20.5 - 4.8, TZ + 7.73 - 1.95),
                 (LENGTH / 2.0, -20.5 + 4.8, TZ + 7.73 + 1.95))
    except Exception:
        G["fails"].append("cut_usb_c")
    try:
        py = side_plane(comp.xZConstructionPlane, WIDTH / 2.0, "y")
        side_cut(tray, py, (-23.5, WIDTH / 2.0, TZ + 22.75), (-16.5, WIDTH / 2.0, TZ + 24.75))
    except Exception:
        G["fails"].append("cut_mute")

    paint(tray, "shell")
    return tray


def build_lid():
    comp = G["comp"]
    sk = comp.sketches.add(plane_at(shift(5)))
    rect(sk, 0, 0, LENGTH, WIDTH)
    sk.isVisible = False
    ei = comp.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(vi(LID)),
                        adsk.fusion.ExtentDirections.NegativeExtentDirection)
    lid = comp.features.extrudeFeatures.add(ei).bodies.item(0)
    lid.name = "shell_lid"
    fillet_vertical_edges(lid, CORNER_R)
    paint(lid, "lid")

    tools = []
    for (x, y) in ((-62, 26), (62, 26), (-62, -26), (62, -26)):
        tools += cyl("dock_magnet", 5, "magnet", x, y, -2.0, 6.0, 2.0)
    for x in (-12, -4, 4, 12):
        tools += cyl("pogo_pad", 5, "gold", x, -30, -LID, 2.5, LID)
    try:
        coll = adsk.core.ObjectCollection.create()
        for t in tools:
            coll.add(t)
        ci = comp.features.combineFeatures.createInput(lid, coll)
        ci.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        ci.isKeepToolBodies = True
        comp.features.combineFeatures.add(ci)
    except Exception:
        G["fails"].append("lid_pockets")
    return lid


# ----------------------------------------------------------------------
# PARTS
# ----------------------------------------------------------------------
def build_coil():
    L = 4
    # windings + magnet ring face the back (lid), ferrite shield on top
    for k in range(6):
        ri = 10.0 + 2.2 * k
        cyl("qi2_winding_%d" % (k + 1), L, "copper", RING_CX, 0, 0.0, 2 * (ri + 1.6), 1.8, 2 * ri)
    cyl("qi2_magnet_ring", L, "magnet", RING_CX, 0, 0.0, 55.0, 2.0, 47.0)
    cyl("qi2_ferrite", L, "ferrite", RING_CX, 0, 2.0, 56.0, 0.8)


def build_power():
    L = 3
    # 10,000 mAh pouch: body, sealed edge, protection board
    block("cell_10000mAh", L, "cell", CELL_X0 + 47.5, 0, Z_CELL, 95.0, 60.0, CELL_T)
    block("cell_seal_edge", L, "cell_seal", CELL_X0 + 97.5, 0, Z_CELL + 5.5, 5.0, 60.0, 1.0)
    block("cell_protection_pcb", L, "pcb", CELL_X0 + 97.5, 0, Z_CELL + 6.5, 4.0, 40.0, 1.2)

    # power bank / USB-C PD board (IP5328P), sits on the coil level
    z = Z_CELL
    block("pd_board", L, "pcb", 51, -20.5, z, 35.0, 25.0, PCB_T)
    zt = z + PCB_T
    block("pd_usb_c", L, "metal", 73.3 - 3.675, -20.5, zt, 7.35, 8.94, 3.26)
    block("pd_ip5328p", L, "chip", 45, -20, zt, 5.0, 5.0, 0.9)
    block("pd_inductor", L, "ferrite", 55, -26, zt, 6.0, 6.0, 3.0)
    grid("pd_caps", L, "passive", zt, [(40, -27, 3.2, 1.6), (60, -14, 3.2, 1.6)], 1.6)
    block("pd_jst_main_cell", L, "conn", 36, -10, zt, 4.0, 3.0, 2.9)
    block("pd_jst_backup_cell", L, "conn", 66, -10, zt, 4.0, 3.0, 2.9)

    # 500 mAh backup cell above the PD board
    block("backup_cell_500mAh", L, "cell", 51, -18, 9.5, 40.0, 30.0, 5.0)

    # Qi2 transmitter board above the backup cell
    block("qi2_tx_board", L, "pcb", 52, -18, 15.0, 30.0, 20.0, PCB_T)
    block("qi2_tx_controller", L, "chip", 48, -18, 15.0 + PCB_T, 5.0, 5.0, 0.9)
    grid("qi2_tx_caps", L, "passive", 15.0 + PCB_T, [(58, -14, 3.2, 1.6), (58, -22, 3.2, 1.6)], 1.6)

    # speaker, fires toward the front grille
    sx, sy = SPK_C
    cyl("speaker_magnet", L, "ferrite", sx, sy, Z_CELL, 14.0, 5.0)
    cyl("speaker_frame", L, "black", sx, sy, Z_CELL + 5.0, 28.0, 3.0, 24.0)
    cyl("speaker_cone", L, "coax", sx, sy, Z_CELL + 6.5, 24.0, 0.4)
    cyl("speaker_dust_cap", L, "black", sx, sy, Z_CELL + 6.9, 9.0, 0.8)


def build_main_pcb():
    L = 2
    z = ABOVE
    zt = PCB_TOP
    block("main_pcb", L, "pcb", -34.5, 0, z, 70.0, 45.0, PCB_T)

    # ESP32-S3-WROOM-1: 18 x 25.5 x 3.1 mm, antenna end toward the top edge
    mx, my = -55.0, 9.75
    block("esp32s3_module_pcb", L, "pcb_dark", mx, my, zt, 18.0, 25.5, 0.8)
    block("esp32s3_shield_can", L, "metal", mx, 6.3, zt + 0.8, 16.0, 17.6, 2.3)
    grid("esp32s3_antenna_trace", L, "gold", zt + 0.8,
         [(mx - 6.5 + 2.6 * i, 18.9, 0.5, 4.5) for i in range(6)], 0.05)
    pads = [(mx - 9.4, -2.0 + 1.27 * i, 0.8, 0.6) for i in range(14)]
    pads += [(mx + 9.4, -2.0 + 1.27 * i, 0.8, 0.6) for i in range(14)]
    pads += [(mx - 6.35 + 1.27 * i, my - 13.15, 0.6, 0.8) for i in range(11)]
    grid("esp32s3_pads", L, "gold", zt, pads, 0.05)

    # chips
    block("amp_max98357a", L, "chip", -20, 15, zt, 3.0, 3.0, 0.9)
    block("haptic_drv2605l", L, "chip", -12, 15, zt, 3.0, 3.0, 0.9)
    block("imu_bmi270", L, "chip", -15, -5, zt, 2.5, 3.0, 0.8)
    block("ldo_3v3", L, "chip", -8, -15, zt, 3.0, 3.0, 1.1)
    grid("passives", L, "passive", zt,
         [(-42 + 4 * i, -8 + 4 * j, 1.6, 0.8) for i in range(5) for j in range(5)], 0.45)

    # connectors (JST-SH style)
    for (n, x, y, w, h) in (("pwr", -2.5, -4.2, 4.0, 5.4), ("sim", -2.5, -12.2, 4.0, 5.4),
                            ("speaker", -2.5, 15.6, 4.0, 3.6), ("lra", -2.5, 20.5, 4.0, 3.6),
                            ("touch", -29.4, 21.0, 4.0, 3.0), ("mic", -41.6, 20.0, 7.2, 3.0),
                            ("light", -43.2, -21.0, 5.6, 3.0), ("mute", -17.4, 21.0, 3.6, 3.0)):
        block("conn_" + n, L, "conn", x, y, zt, w, h, 2.9)
    block("conn_display_fpc", L, "chip", DCX, -15, zt, 24.0, 5.0, 2.0)

    # SIM7080G board (LTE-M + GNSS) to the right of the main PCB, above the cell
    block("sim_board", L, "pcb", 18, -20, z, 32.0, 25.0, 1.0)
    block("sim7080g_module", L, "metal", 11, -18, z + 1.0, 17.6, 15.7, 2.3)
    block("nano_sim_holder", L, "metal", 27.5, -26, z + 1.0, 12.5, 13.0, 1.4)
    grid("ufl_connectors", L, "gold", z + 1.0, [(25, -12, 2.0, 2.0), (29, -12, 2.0, 2.0)], 1.2)

    # haptic LRA
    cyl("haptic_lra_10mm", L, "metal", 17, 28, z, 10.0, 3.5)


def build_front():
    L = 1
    block("oled_glass", L, "glass", DCX, 0, GLASS_Z, GLASS[0], GLASS[1], GLASS[2])
    # flex cable: folds under the glass, then down into the connector
    block("oled_fpc_flat", L, "fpc", DCX, -17.5, GLASS_Z - 0.3, 20.0, 7.0, 0.3)
    drop = (GLASS_Z - 0.3) - (PCB_TOP + 2.0)
    if drop > 0.2:
        block("oled_fpc_drop", L, "fpc", DCX, -15.0, PCB_TOP + 2.0, 20.0, 0.3, drop)

    block("touch_strip_pcb", L, "copper", STRIP_C[0], STRIP_C[1], INNER - 1.6, 40.0, 5.0, 1.6)

    block("mic_inmp441_pcb", L, "mic_pcb", -64, 28.5, INNER - 2.6, 10.0, 10.0, 1.6)
    block("mic_inmp441", L, "metal", -64, 28.5, INNER - 1.0, 4.0, 3.0, 1.0)
    block("light_veml7700_pcb", L, "als_pcb", -64, -28.5, INNER - 2.6, 10.0, 10.0, 1.6)
    block("light_veml7700", L, "white", -64, -28.5, INNER - 1.0, 3.0, 2.0, 1.0)

    block("gnss_patch_ceramic", L, "ceramic", 17, 5, INNER - 4.0, 18.0, 18.0, 3.95)
    block("gnss_patch_silver", L, "metal", 17, 5, INNER - 0.05, 14.0, 14.0, 0.05)
    cyl("gnss_feed_pin", L, "gold", 17, 5, INNER - 5.0, 1.2, 1.0)
    block("lte_flex_antenna", L, "black", 50, -30, INNER - 0.3, 40.0, 8.0, 0.3)

    block("mute_switch", L, "black", -20, 32, 22.0, 8.6, 3.6, 3.5)
    block("mute_switch_slider", L, "mute", -20, 35.4, 23.0, 1.5, 3.2, 1.5)


def build_wiring():
    W = []
    # main cell -> PD board
    W.append(("cell_plus", "red", [(CELL_X0 + 99.5, -15, 11.6), (30.5, -15, 11.6), (30.8, -11.5, 9.0), (35.4, -10, 8.6)]))
    W.append(("cell_minus", "black", [(CELL_X0 + 99.5, -16.5, 11.6), (30.5, -16.5, 11.6), (31.6, -12, 9.0), (36.6, -10, 8.6)]))
    # backup cell -> PD board (exits the right end)
    W.append(("backup_plus", "red", [(71.2, -14, 12.0), (72.6, -12.4, 11.0), (72.6, -11.6, 9.2), (66.6, -10, 8.6)]))
    W.append(("backup_minus", "black", [(71.2, -15.2, 12.0), (72.9, -13.4, 11.0), (72.9, -12.6, 9.2), (65.4, -10, 8.6)]))
    # PD board -> main PCB (5V, GND, USB D+, D-)
    for k, (n, c) in enumerate((("5v", "red"), ("gnd", "black"), ("usb_dp", "green"), ("usb_dm", "white"))):
        y = -6.0 + 1.2 * k
        W.append(("pd_main_" + n, c, [(34.0 + 1.0 * k, -8.6, 6.6), (30.5, y, 8.0), (30.5, y, 20.6), (5.0, y, 21.0), (-1.5, y, 20.6)]))
    # PD board -> Qi2 TX board
    for k, c in enumerate(("red", "black")):
        x = 71.5 - 1.2 * k
        W.append(("pd_tx_" + c, c, [(63.0 - 1.2 * k, -8.6, 6.6), (x, -1.5, 7.5), (x, -1.5, 17.5), (64.0 - 1.2 * k, -9.0, 17.2)]))
    # Qi2 coil -> TX board
    W.append(("coil_a", "copper", [(40, -20, 3.4), (33, -30, 3.4), (29.5, -32.5, 4.0), (29.5, -32.5, 16.0), (37.6, -26.0, 16.0)]))
    W.append(("coil_b", "copper", [(46, -20, 3.4), (34, -31.5, 3.4), (30.4, -33.3, 4.0), (30.4, -33.3, 16.0), (37.6, -24.8, 16.0)]))
    # dock pogo pads -> PD board
    W.append(("dock_plus", "red", [(-4, -30, 0.3), (-4, -30, 1.6), (20, -32.6, 1.6), (32.6, -33.3, 2.0), (32.6, -33.3, 5.5), (35.0, -31.5, 6.6)]))
    W.append(("dock_minus", "black", [(4, -30, 0.3), (4, -30, 1.6), (21, -31.4, 1.6), (32.6, -32.1, 2.0), (32.6, -32.1, 5.5), (36.2, -30.5, 6.6)]))
    # speaker -> main PCB (amp)
    for k, c in enumerate(("red", "black")):
        d = 1.2 * k
        W.append(("speaker_" + c, c, [(33.5, 20 + d, 10.5), (30.0, 20 + d, 10.5), (30.0, 20 + d, 20.6), (5.0, 17 + d, 21.0), (-1.5, 15.0 + d, 20.6)]))
    # haptic LRA -> main PCB
    for k, c in enumerate(("red", "black")):
        d = 1.6 * k
        W.append(("lra_" + c, c, [(12.2, 27 + d, 19.0), (5.0, 24 + d, 20.8), (-1.5, 19.9 + 1.2 * k, 20.6)]))
    # touch strip -> main PCB
    for k, c in enumerate(("yellow", "black")):
        x = -30 + 1.2 * k
        W.append(("touch_" + c, c, [(x, 26.5, INNER - 2.0), (x, 24.0, 22.5), (x, 21.0, PCB_TOP + 2.0)]))
    # mic (I2S) -> main PCB
    for k, c in enumerate(("red", "black", "yellow", "green", "blue")):
        W.append(("mic_%d" % (k + 1), c, [(-63 + 1.2 * k, 26.0, INNER - 3.0), (-52 + 1.2 * k, 24.5, 23.5), (-44 + 1.2 * k, 20.0, PCB_TOP + 2.0)]))
    # light sensor (I2C) -> main PCB
    for k, c in enumerate(("red", "black", "yellow", "blue")):
        W.append(("light_%d" % (k + 1), c, [(-63 + 1.2 * k, -26.0, INNER - 3.0), (-50 + 1.2 * k, -24.0, 23.5), (-45 + 1.2 * k, -21.0, PCB_TOP + 2.0)]))
    # mute switch -> main PCB
    for k, c in enumerate(("yellow", "black")):
        W.append(("mute_" + c, c, [(-20 - 1.2 * k, 30.4, 23.0), (-19 - 1.2 * k, 25.0, 22.5), (-18 + 1.2 * k, 21.0, PCB_TOP + 2.0)]))
    # SIM board UART + power -> main PCB
    for k, c in enumerate(("red", "black", "yellow", "green")):
        W.append(("sim_%d" % (k + 1), c, [(4 + 1.2 * k, -8.6, ABOVE + 1.3), (1.0, -12 + 0.9 * k, 20.4), (-1.5, -14.0 + 1.2 * k, 20.6)]))
    for n, c, pts in W:
        wire(n, c, pts)
    # coax to the antennas
    wire("coax_gnss", "coax", [(25, -12, ABOVE + 2.5), (25, -3, 22.0), (17, 5, INNER - 5.0)], 1.13)
    wire("coax_lte", "coax", [(29, -12, ABOVE + 2.5), (31, -24, 23.0), (32, -30, INNER - 0.6)], 1.13)


def interference_report(design, tray, lid):
    ents = adsk.core.ObjectCollection.create()
    for b in G["parts"] + [tray, lid]:
        ents.add(b)
    res = design.analyzeInterference(design.createInterferenceInput(ents))
    lines = []
    for i in range(min(res.count, 12)):
        r = res.item(i)
        lines.append("%s x %s (%.1f mm3)" % (r.entityOne.name, r.entityTwo.name,
                                            r.interferenceBody.volume * 1000.0))
    if res.count == 0:
        return "Fit check: no interferences."
    more = "\n  ...and %d more" % (res.count - 12) if res.count > 12 else ""
    return "Fit check: %d interferences:\n  %s%s" % (res.count, "\n  ".join(lines), more)


# ----------------------------------------------------------------------
# RUN
# ----------------------------------------------------------------------
def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("Open a Design workspace first.")
            return
        G["design"] = design
        G["comp"] = design.rootComponent
        try:
            G["base_app"] = find_base_appearance(app)
        except Exception:
            G["base_app"] = None

        tray = build_tray()
        lid = build_lid()
        build_coil()
        build_power()
        build_main_pcb()
        build_front()
        build_wiring()

        report = ""
        if not EXPLODE:
            try:
                report = interference_report(design, tray, lid)
            except Exception:
                report = "Fit check could not run."

        app.activeViewport.fit()
        msg = ("heartsync %s (%s display)\n"
               "Shell %.1f x %.1f x %.1f mm, inside height %.1f mm\n"
               "Parts: %d bodies, wires: %d\n"
               % ("EXPLODED VIEW" if EXPLODE else "STACK", DISPLAY,
                  LENGTH, WIDTH, THICKNESS, INNER, len(G["parts"]), G["wires"]))
        if G["fails"]:
            msg += "Could not build: %s\n" % ", ".join(G["fails"][:10])
        if not G["base_app"]:
            msg += "Colours skipped (no base appearance found).\n"
        msg += report
        ui.messageBox(msg)
    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
