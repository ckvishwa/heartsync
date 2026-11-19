"""
heartsync - assembly: enclosure + internals (Fusion 360 script, Python)

Source: 3D/HeartsyncShell/HeartsyncStack/HeartsyncStack.py, trimmed.

Builds:
  * tray (front shell) with display window, ring groove, mic and
    light-sensor holes, touch-strip groove, USB-C cutout in the right end
    wall, speaker grille slots in both end walls, five button cutouts in the
    top wall, and a rib on the bottom wall that carries the haptic LRA
  * lid (back cover) with dock magnet pockets and pogo contact pads
  * internal parts with colour: Qi2 coil (ferrite, windings, magnet ring)
    centred at X = 0, graphite sheet between coil and cell, 10,000 mAh pouch
    cell (centred in X) + protection board + insulator sheet, power bank /
    USB-C PD board, Qi2 transmitter board, SIM7080G board with nano-SIM holder
    and U.FL connectors, GNSS patch antenna, LTE flex antenna, Wi-Fi FlexPIFA
    on the front wall, stereo end-firing speaker boxes, haptic LRA, OLED
    glass + flex cable, touch strip, mic, light sensor, button strip
    (PWR, VOL-, VOL+, PLAY + latching mic-mute button)
  * the real carrier board, imported from cad/heartsync_carrier.step
  * fit check (interference), antenna clearance report, then the bodies are
    grouped into components: shell, power, speakers, lte, wifi, ui, dock
  * wiring (off by default; endpoints are stale, from the old layout)

Not built (on purpose):
  * 500 mAh backup cell: dropped, tracking runs from a reserve on the main cell

Run from the Fusion MCP or Scripts and Add-ins. Prints a report; no dialogs.

EXPLODE = False -> normal stack with a fit (interference) check
EXPLODE = True  -> exploded view (layers pulled apart upward, no wires)

Sizes in mm. Part sizes are close to real parts but several are estimates -
replace them when the real parts arrive.
Axes: X = 152 length, Y = 72.5 width, Z = thickness. Front face is +Z.
"""
import adsk.core
import adsk.fusion
import math
import os

# ----------------------------------------------------------------------
# SETTINGS
# ----------------------------------------------------------------------
EXPLODE = False
EXPLODE_GAP = 25.0
WIRES = False

DISPLAY = "2.7"            # "2.7" or "3.12"

LENGTH, WIDTH = 152.0, 72.5
THICKNESS = 32.0           # tray + lid (31 was 0.1 mm short with the swell gap)
WALL = 2.2
LID = 2.2
CORNER_R = 6.0
SWELL = 1.2                # free space above the 10,000 mAh cell

RING_CX = 43.0             # decorative ring groove on the front (no longer over the coil)
RING_DIA = 56.0
COIL_CX = 0.0              # Qi2 coil on the back, centred in X under the cell

INSUL = 0.2                # insulator sheet on the cell top (below the swell gap)
GRAPHITE = 0.1             # graphite sheet between the coil ferrite and the cell
GROUP = True               # group the bodies into components after the checks
CARRIER = True             # import the real carrier board STEP
CARRIER_STEP = os.path.join(os.path.dirname(os.path.abspath(globals().get("__file__", "."))),
                            "..", "heartsync_carrier.step")
CARRIER_X0, CARRIER_Y1 = -36.0, 30.0   # board left edge, top edge (KiCad top = +Y)
# where kicad-cli puts the board in the STEP (board origin at (100, 100) in the .kicad_pcb)
STEP_BOARD_X0, STEP_BOARD_Y1, STEP_BOARD_Z0 = 100.0, -100.0, 0.0

SPK = (16.0, 30.0, 20.0)   # speaker box: depth (X), face width (Y), face height (Z)
SPK_CY, SPK_Z0 = 10.0, 4.0

# top-wall buttons: (name, centre X, body size). Latching mic mute is 7 x 7 mm.
BTN_ZC = 21.5
BUTTONS = [("mute", 38.5, 7.0), ("pwr", 46.0, 6.0), ("vol_dn", 53.5, 6.0),
           ("vol_up", 61.0, 6.0), ("play", 68.0, 6.0)]

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
ABOVE = Z_CELL + CELL_T + INSUL + SWELL  # board layer bottom (17.9)
PCB_T = 1.6
PCB_TOP = ABOVE + PCB_T
GLASS_Z = INNER - GLASS[2]
CELL_X0 = -50.0                          # cell + seal edge span X -50..50 (centred)
CAV_X = LENGTH / 2.0 - WALL              # inside face of the end walls (73.8)
CAV_Y = WIDTH / 2.0 - WALL               # inside face of the top/bottom walls (34.05)
USB_ZC = ABOVE + PCB_T + 3.26 / 2.0      # USB-C receptacle centre height
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
    "insul": (245, 235, 190), "speaker": (45, 45, 50), "flexpifa": (230, 140, 20),
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
    side_cuts(tray, plane, [(a, b)], depth)


def side_cuts(tray, plane, corners, depth=10.0):
    """Several rectangles, each (a, b) = opposite model-space corners on the side plane."""
    comp = G["comp"]
    sk = comp.sketches.add(plane)
    for a, b in corners:
        p1 = sk.modelToSketchSpace(P(*a))
        p2 = sk.modelToSketchSpace(P(*b))
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(p1.x, p1.y, 0), adsk.core.Point3D.create(p2.x, p2.y, 0))
    sk.isVisible = False
    ei = comp.features.extrudeFeatures.createInput(
        all_profiles(sk), adsk.fusion.FeatureOperations.CutFeatureOperation)
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
    front_cut("mic_hole", lambda s: s.sketchCurves.sketchCircles.addByCenterRadius(P(-64, 28.5), mm(0.5)), WALL * 1.5)
    front_cut("light_hole", lambda s: s.sketchCurves.sketchCircles.addByCenterRadius(P(-64, -28.5), mm(1.0)), WALL * 1.5)

    # USB-C on the right end wall (+X), at the PD board level
    try:
        px = side_plane(comp.yZConstructionPlane, LENGTH / 2.0, "x")
        side_cut(tray, px, (LENGTH / 2.0, -20.5 - 4.8, TZ + USB_ZC - 1.95),
                 (LENGTH / 2.0, -20.5 + 4.8, TZ + USB_ZC + 1.95))
    except Exception:
        G["fails"].append("cut_usb_c")

    # speaker grilles: 7 slots, 24 x 1.2 mm, in both end walls over the speaker faces
    zc = SPK_Z0 + SPK[2] / 2.0
    for side, name in ((1, "R"), (-1, "L")):
        try:
            pl = side_plane(comp.yZConstructionPlane, side * LENGTH / 2.0, "x")
            x = side * LENGTH / 2.0
            slots = [((x, SPK_CY - 12.0, TZ + zc + 2.4 * k - 0.6),
                      (x, SPK_CY + 12.0, TZ + zc + 2.4 * k + 0.6)) for k in range(-3, 4)]
            side_cuts(tray, pl, slots)
        except Exception:
            G["fails"].append("cut_grille_" + name)

    # top wall (+Y): PWR / VOL- / VOL+ / PLAY caps (4.4 mm holes) + 7 x 7 mm latching mute
    try:
        py = side_plane(comp.xZConstructionPlane, WIDTH / 2.0, "y")
        holes = []
        for name, x, size in BUTTONS:
            h = 7.0 if name == "mute" else 4.4
            holes.append(((x - h / 2.0, WIDTH / 2.0, TZ + BTN_ZC - h / 2.0),
                          (x + h / 2.0, WIDTH / 2.0, TZ + BTN_ZC + h / 2.0)))
        side_cuts(tray, py, holes)
    except Exception:
        G["fails"].append("cut_buttons")

    # haptic rib: ledge on the bottom wall (-Y), above the swell gap, joined to the tray
    try:
        sk = comp.sketches.add(plane_at(TZ + ABOVE + 0.1))
        y0, y1 = -CAV_Y - 0.5, -23.5          # 0.5 mm into the wall so it fuses
        sk.sketchCurves.sketchLines.addTwoPointRectangle(P(-16.0, y0), P(-4.0, y1))
        sk.isVisible = False
        rib = new_bodies(sk.profiles.item(0), 1.5, "shell_rib_lra", "shell", register=False)[0]
        coll = adsk.core.ObjectCollection.create()
        coll.add(rib)
        ci = comp.features.combineFeatures.createInput(tray, coll)
        ci.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        comp.features.combineFeatures.add(ci)
    except Exception:
        G["fails"].append("rib_lra")

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
        cyl("qi2_winding_%d" % (k + 1), L, "copper", COIL_CX, 0, 0.0, 2 * (ri + 1.6), 1.8, 2 * ri)
    cyl("qi2_magnet_ring", L, "magnet", COIL_CX, 0, 0.0, 55.0, 2.0, 47.0)
    cyl("qi2_ferrite", L, "ferrite", COIL_CX, 0, 2.0, 56.0, 0.8)
    # graphite heat spreader on the ferrite, under the cell
    block("graphite_sheet", L, "black", COIL_CX, 0, 2.8, 60.0, 60.0, GRAPHITE)


def build_power():
    L = 3
    # 10,000 mAh pouch: body, sealed edge, protection board, insulator on the top face
    block("cell_10000mAh", L, "cell", CELL_X0 + 47.5, 0, Z_CELL, 95.0, 60.0, CELL_T)
    block("cell_seal_edge", L, "cell_seal", CELL_X0 + 97.5, 0, Z_CELL + 5.5, 5.0, 60.0, 1.0)
    block("cell_protection_pcb", L, "pcb", CELL_X0 + 97.5, 0, Z_CELL + 6.5, 4.0, 40.0, 1.2)
    block("cell_insulator", L, "insul", CELL_X0 + 47.5, 0, Z_CELL + CELL_T, 95.0, 60.0, INSUL)
    # keep-out for the fit check: the swell gap over the whole cell outline must stay empty
    ko = block("keepout_swell_gap", L, "red", CELL_X0 + 50.0, 0, Z_CELL + CELL_T + INSUL,
               100.0, 60.0, SWELL)
    for b in ko:
        b.isLightBulbOn = False

    # power bank / USB-C PD board (IP5328P) in the board layer, USB-C out the right end wall
    z = ABOVE
    block("pd_board", L, "pcb", 53, -20.5, z, 35.0, 25.0, PCB_T)
    zt = z + PCB_T
    block("pd_usb_c", L, "metal", 75.3 - 3.675, -20.5, zt, 7.35, 8.94, 3.26)
    # hot parts and the battery JST sit right of X 50, off the cell outline (safety rules 1, 7)
    block("pd_ip5328p", L, "chip", 63, -22, zt, 5.0, 5.0, 0.9)
    block("pd_inductor", L, "ferrite", 57, -26, zt, 6.0, 6.0, 3.0)
    grid("pd_caps", L, "passive", zt, [(42, -27, 3.2, 1.6), (62, -14, 3.2, 1.6)], 1.6)
    block("pd_jst_main_cell", L, "conn", 53, -10, zt, 4.0, 3.0, 2.9)

    # Qi2 transmitter board in the board layer, right of the carrier (20 x 30, long side in Y)
    block("qi2_tx_board", L, "pcb", 46, 8, z, 20.0, 30.0, PCB_T)
    block("qi2_tx_controller", L, "chip", 53, 4, zt, 5.0, 5.0, 0.9)
    grid("qi2_tx_caps", L, "passive", zt, [(40, 16, 1.6, 3.2), (52, 16, 1.6, 3.2)], 1.6)


def build_electronics():
    """Boards beside the (real, imported) carrier board."""
    L = 2
    z = ABOVE

    # SIM7080G board (LTE-M + GNSS), left of the carrier, above the cell
    block("sim_board", L, "pcb", -54, -20.5, z, 32.0, 25.0, 1.0)
    block("sim7080g_module", L, "metal", -61, -18.5, z + 1.0, 17.6, 15.7, 2.3)
    block("nano_sim_holder", L, "metal", -44.5, -26.5, z + 1.0, 12.5, 13.0, 1.4)
    grid("ufl_connectors", L, "gold", z + 1.0, [(-47, -12.5, 2.0, 2.0), (-43, -12.5, 2.0, 2.0)], 1.2)

    # haptic LRA, glued to the rib on the bottom wall
    cyl("haptic_lra_10mm", L, "metal", -10, -28.5, ABOVE + 0.1 + 1.5, 10.0, 3.5)


def build_speakers():
    """Boxed rectangular stand-ins, firing out through the end-wall grilles."""
    L = 3
    d, w, h = SPK
    block("speaker_L", L, "speaker", -CAV_X + d / 2.0, SPK_CY, SPK_Z0, d, w, h)
    block("speaker_R", L, "speaker", CAV_X - d / 2.0, SPK_CY, SPK_Z0, d, w, h)


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

    # Wi-Fi: Ezurio FlexPIFA 001-0014 (40.1 x 11.0 x 2.5), on the front wall, element facing
    # out, ground plate toward the board, long axis along Y. Long sides >= 5 mm from metal in
    # the wall plane (GNSS patch 10, speaker_R 10.8). 100 mm MHF1 cable to U1's U.FL at
    # (-13.0, 27.0): leaves the X = 36 long side, crosses the carrier, about 55 mm used.
    block("wifi_flexpifa", L, "flexpifa", 41.5, 1.05, INNER - 2.5, 11.0, 40.1, 2.5)

    # button strip on the top wall: vertical PCB, tactile PWR/VOL-/VOL+/PLAY, latching mute
    block("button_strip_pcb", L, "pcb", 53.25, 27.5, BTN_ZC - 3.5, 36.5, 1.0, 7.0)
    for name, x, s in BUTTONS:
        if name == "mute":
            # 7 x 7 mm self-latching push button (body depth 5 mm assumed) + 6.4 mm cap
            block("btn_mute_body", L, "black", x, 30.5, BTN_ZC - 3.5, 7.0, 5.0, 7.0)
            block("btn_mute_cap", L, "mute", x, 34.875, BTN_ZC - 3.2, 6.4, 3.75, 6.4)
        else:
            block("btn_%s_body" % name, L, "black", x, 29.75, BTN_ZC - 3.0, s, 3.5, 6.0)
            block("btn_%s_cap" % name, L, "white", x, 34.125, BTN_ZC - 2.0, 4.0, 5.25, 4.0)


def build_wiring():
    W = []
    # main cell -> PD board
    W.append(("cell_plus", "red", [(CELL_X0 + 99.5, -15, 11.6), (30.5, -15, 11.6), (30.8, -11.5, 9.0), (35.4, -10, 8.6)]))
    W.append(("cell_minus", "black", [(CELL_X0 + 99.5, -16.5, 11.6), (30.5, -16.5, 11.6), (31.6, -12, 9.0), (36.6, -10, 8.6)]))
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


def occ_bodies(occ):
    """All bodies under an occurrence, as proxies in the root context."""
    out = [occ.bRepBodies.item(i) for i in range(occ.bRepBodies.count)]
    for i in range(occ.childOccurrences.count):
        out += occ_bodies(occ.childOccurrences.item(i))
    return out


def import_carrier(design):
    """Imports the carrier STEP into a component placed so the PCB sits at X0 = -36, top edge
    Y = 30, bottom Z = ABOVE. The wrapper occurrence is positioned before the import: moving
    the imported occurrence afterwards (transform + snapshot) left one nested part behind."""
    app = adsk.core.Application.get()
    root = design.rootComponent
    path = os.path.normpath(CARRIER_STEP)
    if not os.path.isfile(path):
        G["fails"].append("carrier_step (not found: %s)" % path)
        return None
    m = adsk.core.Matrix3D.create()
    m.translation = adsk.core.Vector3D.create(mm(CARRIER_X0 - STEP_BOARD_X0),
                                              mm(CARRIER_Y1 - STEP_BOARD_Y1),
                                              mm(ABOVE - STEP_BOARD_Z0))
    occ = root.occurrences.addNewComponent(m)
    occ.component.name = "carrier"
    opts = app.importManager.createSTEPImportOptions(path)
    opts.isViewFit = False
    app.importManager.importToTarget(opts, occ.component)
    G["carrier"] = occ
    # verify: the board body (70 x 45 footprint, 1.4..1.7 thick; KiCad exports the core only)
    bodies = occ_bodies(occ)
    pcb = [b for b in bodies
           if mm(1.4) < (b.boundingBox.maxPoint.z - b.boundingBox.minPoint.z) < mm(1.7)
           and (b.boundingBox.maxPoint.x - b.boundingBox.minPoint.x) > mm(60.0)]
    if len(pcb) != 1:
        G["fails"].append("carrier_step (found %d PCB bodies)" % len(pcb))
        return occ
    bb = pcb[0].boundingBox
    err = max(abs(bb.minPoint.x - mm(CARRIER_X0)), abs(bb.maxPoint.y - mm(CARRIER_Y1)),
              abs(bb.minPoint.z - mm(ABOVE)))
    if err > mm(0.05):
        G["fails"].append("carrier_step (PCB off target by %.2f mm: re-export the STEP with "
                          "the board origin at (100, 100) or update STEP_BOARD_*)" % (err * 10.0))
    lost = [b for b in bodies if b.boundingBox.minPoint.x > mm(LENGTH / 2.0)
            or b.boundingBox.maxPoint.x < -mm(LENGTH / 2.0)]
    if lost:
        G["fails"].append("carrier_step (%d bodies outside the shell)" % len(lost))
    return occ


def body_label(b):
    ctx = b.assemblyContext
    return "%s/%s" % (ctx.name, b.name) if ctx else b.name


def interference_report(design, tray, lid):
    ents = adsk.core.ObjectCollection.create()
    for b in G["parts"] + [tray, lid]:
        ents.add(b)
    carrier = occ_bodies(G["carrier"]) if G.get("carrier") else []
    for b in carrier:
        ents.add(b)
    res = design.analyzeInterference(design.createInterferenceInput(ents))
    ours = set(b.name for b in G["parts"]) | {tray.name, lid.name}
    lines, internal = [], 0
    for i in range(res.count):
        r = res.item(i)
        a, b = r.entityOne, r.entityTwo
        if a.name not in ours and b.name not in ours:
            # both from the carrier STEP (parts sitting on their own board): not a fit issue.
            # Results come back as native bodies, so the test is by name: ours are all named.
            internal += 1
            continue
        lines.append("%s x %s (%.2f mm3)" % (body_label(a), body_label(b),
                                             r.interferenceBody.volume * 1000.0))
    note = " (%d carrier-internal overlaps ignored)" % internal if internal else ""
    if not lines:
        return "Fit check: no interferences%s." % note
    return "Fit check: %d interferences%s:\n  %s" % (len(lines), note, "\n  ".join(lines))


ANTENNAS = ("wifi_flexpifa", "gnss_patch_ceramic", "lte_flex_antenna")
# metal (or lossy) neighbours checked against each antenna
NEIGHBOURS = ("cell_10000mAh", "cell_protection_pcb", "qi2_magnet_ring", "qi2_ferrite",
              "qi2_tx_board", "speaker_L", "speaker_R", "pd_board", "pd_usb_c", "pd_inductor",
              "sim7080g_module", "nano_sim_holder", "haptic_lra_10mm", "oled_glass",
              "touch_strip_pcb", "button_strip_pcb", "btn_mute_body", "btn_pwr_body",
              "btn_play_body") + ANTENNAS


def clearance_report(design):
    """Minimum distance (mm) from each antenna to its neighbours and to the carrier board."""
    mm_ = adsk.core.Application.get().measureManager
    root = design.rootComponent
    by_name = {}
    for b in G["parts"]:
        by_name.setdefault(b.name, b)
    carrier = occ_bodies(G["carrier"]) if G.get("carrier") else []
    out = ["Antenna clearances (minimum distance, mm):"]
    for a in ANTENNAS:
        ab = by_name.get(a)
        if ab is None:
            out.append("  %s: missing" % a)
            continue
        d = []
        for n in NEIGHBOURS:
            if n == a or n not in by_name:
                continue
            d.append((mm_.measureMinimumDistance(ab, by_name[n]).value * 10.0, n))
        best = None
        for b in carrier:
            v = mm_.measureMinimumDistance(ab, b).value * 10.0
            if best is None or v < best[0]:
                best = (v, body_label(b))
        if best:
            d.append((best[0], "carrier: " + best[1]))
        d.sort()
        out.append("  %s: %s" % (a, ", ".join("%s %.1f" % (n, v) for v, n in d)))
    return "\n".join(out)


def group(n):
    if n.startswith("shell_"):
        return "shell"
    if n.startswith(("cell_", "pd_", "qi2_", "graphite_", "keepout_")):
        return "power"
    if n.startswith("speaker_"):
        return "speakers"
    if n in ("sim_board", "sim7080g_module", "nano_sim_holder", "lte_flex_antenna") \
            or n.startswith(("ufl_connectors", "gnss_")):
        return "lte"
    if n.startswith("wifi_"):
        return "wifi"
    if n.startswith(("dock_magnet", "pogo_pad")):
        return "dock"
    return "ui"


def group_components(design):
    """Moves every root body into a component. Run after the checks (moving drops references)."""
    root = design.rootComponent
    I = adsk.core.Matrix3D.create()
    occs = {}
    for g in ("shell", "power", "speakers", "lte", "wifi", "ui", "dock"):
        o = root.occurrences.addNewComponent(I)
        o.component.name = g
        occs[g] = o
    while root.bRepBodies.count:
        b = root.bRepBodies.item(root.bRepBodies.count - 1)
        b.moveToComponent(occs[group(b.name)])
    return ", ".join("%s %d" % (g, o.component.bRepBodies.count) for g, o in occs.items())


# ----------------------------------------------------------------------
# RUN
# ----------------------------------------------------------------------
def run(context):
    """Builds the assembly, prints a report and returns it. Errors propagate."""
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

    tray = build_tray()
    lid = build_lid()
    build_coil()
    build_power()
    build_electronics()
    build_speakers()
    build_front()
    build_wiring()
    if CARRIER and not EXPLODE:
        import_carrier(design)

    report = ""
    if not EXPLODE:
        try:
            report = interference_report(design, tray, lid)
        except Exception as e:
            report = "Fit check could not run: %s" % e
        try:
            report += "\n" + clearance_report(design)
        except Exception as e:
            report += "\nClearance report could not run: %s" % e
    n_parts = len(G["parts"])
    n_carrier = len(occ_bodies(G["carrier"])) if G.get("carrier") else 0
    grouped = group_components(design) if GROUP else "off"

    app.activeViewport.fit()
    msg = ("heartsync %s (%s display)\n"
           "Shell %.1f x %.1f x %.1f mm, inside height %.1f mm, board layer Z %.1f\n"
           "Parts: %d bodies, carrier STEP: %s, wires: %d\n"
           "Components: %s\n"
           % ("EXPLODED VIEW" if EXPLODE else "STACK", DISPLAY,
              LENGTH, WIDTH, THICKNESS, INNER, ABOVE, n_parts,
              "%d bodies" % n_carrier if n_carrier else "not imported",
              G["wires"], grouped))
    if G["fails"]:
        msg += "Could not build: %s\n" % ", ".join(G["fails"])
    if not G["base_app"]:
        msg += "Colours skipped (no base appearance found).\n"
    msg += report
    print(msg)
    return msg
