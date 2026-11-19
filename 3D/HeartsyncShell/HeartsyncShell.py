"""
HeartsyncShell - Fusion 360 script (Python)

Builds the heartsync enclosure as two bodies:
  - tray : 152 x 72.5 mm footprint, hollow, open at the back, display window
           + decorative ring groove + touch-strip groove cut in the front wall
  - lid  : flat back cover (the Qi2 coil sits behind/inside this side)

Run: Utilities > Add-Ins > Scripts and Add-Ins > green "+" next to "My Scripts"
     > pick the folder "HeartsyncShell" > select it > Run.

Change DISPLAY below to switch layouts. All sizes are in mm.
Axes: X = 152 mm length, Y = 72.5 mm width, Z = thickness. Front face is +Z.
"""
import adsk.core
import adsk.fusion
import traceback

# ----------------------------------------------------------------------
# SETTINGS (mm)
# ----------------------------------------------------------------------
DISPLAY = "2.7"          # "2.7", "3.12", or "3.12x2"

LENGTH = 152.0           # ASUS 180W brick footprint
WIDTH = 72.5
THICKNESS = 31.0         # total tray + lid (brick is 23, our estimate is ~31)
WALL = 2.2               # side walls and front wall
LID = 2.2                # back cover thickness
CORNER_R = 6.0           # vertical corner radius

RING_DIA = 56.0          # Qi2 ring (decorative groove on the front)
RING_GROOVE_W = 1.0
RING_GROOVE_DEPTH = 0.6
STRIP_LEN = 40.0         # touch strip marker slot
STRIP_W = 5.0
STRIP_DEPTH = 0.6

# Display windows: (width, height, centre_x, centre_y) measured from the
# centre of the front face. +X = right, +Y = toward the top edge.
if DISPLAY == "2.7":
    # lit 61.4 x 30.7 mm, window a little bigger
    WINDOWS = [(63.0, 32.0, -34.5, 0.0)]
    RING_CX = 43.0
    STRIP_CX, STRIP_CY = -34.5, 28.0
elif DISPLAY == "3.12":
    # NHD-3.12-25664UCW2 viewing area 82 x 22 mm (module body 89.2 x 44 hides inside)
    WINDOWS = [(82.0, 22.0, -27.0, 0.0)]
    RING_CX = 46.0
    STRIP_CX, STRIP_CY = -27.0, 28.0
elif DISPLAY == "3.12x2":
    WINDOWS = [(82.0, 22.0, -27.0, 13.0), (82.0, 22.0, -27.0, -13.0)]
    RING_CX = 46.0
    STRIP_CX, STRIP_CY = -27.0, 31.0
else:
    raise ValueError("DISPLAY must be '2.7', '3.12' or '3.12x2'")

# Stand-in part blocks to check the stack (set False to skip). Sizes in mm.
PARTS = True
CELL = (100.0, 60.0, 12.0)       # 906090 LiPo, 10,000 mAh
COIL_DIA, COIL_T = 56.0, 4.5     # Qi2 coil + magnets
PCB = (70.0, 45.0, 6.0)          # main board with parts on it
SPK_DIA, SPK_T = 28.0, 8.0       # one 28 mm speaker
if DISPLAY == "2.7":
    MODULE = (73.0, 41.9, 3.0)   # bare glass; thickness is a guess
elif DISPLAY == "3.12":
    MODULE = (89.2, 44.0, 6.0)   # NHD-3.12-25664UCW2 body
else:
    MODULE = (89.2, 44.0, 6.0)

MM = 0.1  # Fusion works in cm internally


def mm(v):
    return v * MM


def vi(v_mm):
    return adsk.core.ValueInput.createByReal(mm(v_mm))


def pt(x, y, z=0.0):
    return adsk.core.Point3D.create(mm(x), mm(y), mm(z))


def fillet_vertical_edges(comp, body, radius_mm):
    edges = adsk.core.ObjectCollection.create()
    for e in body.edges:
        g = e.geometry
        if isinstance(g, adsk.core.Line3D):
            d = g.startPoint.vectorTo(g.endPoint)
            d.normalize()
            if abs(d.z) > 0.99:
                edges.add(e)
    if edges.count == 0:
        return
    fi = comp.features.filletFeatures
    inp = fi.createInput()
    inp.addConstantRadiusEdgeSet(edges, vi(radius_mm), True)
    fi.add(inp)


def rect_sketch(comp, plane, cx, cy, w, h):
    sk = comp.sketches.add(plane)
    sk.sketchCurves.sketchLines.addCenterPointRectangle(
        adsk.core.Point3D.create(mm(cx), mm(cy), 0),
        adsk.core.Point3D.create(mm(cx + w / 2.0), mm(cy + h / 2.0), 0),
    )
    return sk


def cut_down(comp, profile, depth_mm):
    """Cut from the sketch plane downward (-Z) by depth_mm."""
    ei = comp.features.extrudeFeatures.createInput(
        profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
    dist = adsk.fusion.DistanceExtentDefinition.create(vi(depth_mm))
    ei.setOneSideExtent(dist, adsk.fusion.ExtentDirections.NegativeExtentDirection)
    comp.features.extrudeFeatures.add(ei)


def plane_at(comp, z_mm):
    xy = comp.xYConstructionPlane
    if abs(z_mm) < 1e-6:
        return xy
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(xy, vi(z_mm))
    return comp.constructionPlanes.add(pi)


def add_block(comp, name, cx, cy, z0, w, h, t):
    sk = rect_sketch(comp, plane_at(comp, z0), cx, cy, w, h)
    ei = comp.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ei.setDistanceExtent(False, vi(t))
    b = comp.features.extrudeFeatures.add(ei).bodies.item(0)
    b.name = name
    return b


def add_cyl(comp, name, cx, cy, z0, dia, t):
    sk = comp.sketches.add(plane_at(comp, z0))
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(cx, cy), mm(dia / 2.0))
    ei = comp.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ei.setDistanceExtent(False, vi(t))
    b = comp.features.extrudeFeatures.add(ei).bodies.item(0)
    b.name = name
    return b


def build_parts(design, comp, tray, lid, inner_top):
    """Stack from the back (z=0) to the front wall (z=inner_top)."""
    parts = []
    z = 0.0
    parts.append(add_cyl(comp, "part_coil", RING_CX, 0, z, COIL_DIA, COIL_T))
    z += COIL_T
    cell_cx = -LENGTH / 2.0 + WALL + 2.0 + CELL[0] / 2.0
    parts.append(add_block(comp, "part_cell", cell_cx, 0, z, CELL[0], CELL[1], CELL[2]))
    parts.append(add_cyl(comp, "part_speaker", cell_cx + CELL[0] / 2.0 + 4.0 + SPK_DIA / 2.0,
                         0, z, SPK_DIA, SPK_T))
    z += CELL[2]
    parts.append(add_block(comp, "part_pcb", cell_cx, 0, z, PCB[0], PCB[1], PCB[2]))
    # display module(s) hang from the inside of the front wall
    zm = inner_top - MODULE[2]
    for i, (w, h, cx, cy) in enumerate(WINDOWS):
        parts.append(add_block(comp, "part_display_%d" % (i + 1), cx, cy, zm,
                               MODULE[0], MODULE[1], MODULE[2]))

    stack = COIL_T + CELL[2] + PCB[2] + MODULE[2]
    spare = inner_top - stack

    ents = adsk.core.ObjectCollection.create()
    for b in parts + [tray, lid]:
        ents.add(b)
    res = design.analyzeInterference(design.createInterferenceInput(ents))
    lines = []
    for i in range(res.count):
        r = res.item(i)
        lines.append("%s  x  %s  (%.1f mm3)" % (
            r.entityOne.name, r.entityTwo.name, r.interferenceBody.volume * 1000.0))
    msg = "Stack coil+cell+PCB+display = %.1f mm, room inside = %.1f mm -> %s%.1f mm\n" % (
        stack, inner_top, "SHORT by " if spare < 0 else "spare ", abs(spare))
    msg += ("Interferences (%d):\n  " % res.count) + "\n  ".join(lines) if lines else "No interferences."
    return msg


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("Open a Design workspace first.")
            return
        comp = design.rootComponent
        xy = comp.xYConstructionPlane

        tray_h = THICKNESS - LID

        # ---------------- tray: outer block ----------------
        sk = rect_sketch(comp, xy, 0, 0, LENGTH, WIDTH)
        ei = comp.features.extrudeFeatures.createInput(
            sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ei.setDistanceExtent(False, vi(tray_h))
        tray_feat = comp.features.extrudeFeatures.add(ei)
        tray = tray_feat.bodies.item(0)
        tray.name = "heartsync_tray"
        fillet_vertical_edges(comp, tray, CORNER_R)

        # ---------------- shell: open the back (lowest planar face) ----------------
        back = None
        for f in tray.faces:
            if isinstance(f.geometry, adsk.core.Plane):
                n = f.geometry.normal
                if abs(n.z) > 0.99:
                    if back is None or f.centroid.z < back.centroid.z:
                        back = f
        faces = adsk.core.ObjectCollection.create()
        faces.add(back)
        si = comp.features.shellFeatures.createInput(faces)
        si.insideThickness = vi(WALL)
        comp.features.shellFeatures.add(si)

        # ---------------- front-face plane ----------------
        pi = comp.constructionPlanes.createInput()
        pi.setByOffset(xy, vi(tray_h))
        front = comp.constructionPlanes.add(pi)
        front.name = "front_face"

        # ---------------- display windows (through the front wall) ----------------
        for (w, h, cx, cy) in WINDOWS:
            s = rect_sketch(comp, front, cx, cy, w, h)
            cut_down(comp, s.profiles.item(0), WALL * 1.5)

        # ---------------- decorative ring groove ----------------
        s = comp.sketches.add(front)
        c = s.sketchCurves.sketchCircles
        c.addByCenterRadius(pt(RING_CX, 0), mm(RING_DIA / 2.0))
        c.addByCenterRadius(pt(RING_CX, 0), mm(RING_DIA / 2.0 - RING_GROOVE_W))
        annulus = None
        for p in s.profiles:
            a = p.areaProperties().area
            if annulus is None or a < annulus[0]:
                annulus = (a, p)
        cut_down(comp, annulus[1], RING_GROOVE_DEPTH)

        # ---------------- touch strip marker ----------------
        s = rect_sketch(comp, front, STRIP_CX, STRIP_CY, STRIP_LEN, STRIP_W)
        cut_down(comp, s.profiles.item(0), STRIP_DEPTH)

        # ---------------- lid (new body, sits below the tray) ----------------
        sk = rect_sketch(comp, xy, 0, 0, LENGTH, WIDTH)
        ei = comp.features.extrudeFeatures.createInput(
            sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ei.setOneSideExtent(
            adsk.fusion.DistanceExtentDefinition.create(vi(LID)),
            adsk.fusion.ExtentDirections.NegativeExtentDirection)
        lid = comp.features.extrudeFeatures.add(ei).bodies.item(0)
        lid.name = "heartsync_lid"
        fillet_vertical_edges(comp, lid, CORNER_R)

        report = ""
        if PARTS:
            report = "\n\n" + build_parts(design, comp, tray, lid, tray_h - WALL)

        app.activeViewport.fit()
        ui.messageBox(
            "heartsync shell built (%s display).\n"
            "Tray %.1f x %.1f x %.1f mm + lid %.1f mm = %.1f mm thick.%s"
            % (DISPLAY, LENGTH, WIDTH, tray_h, LID, THICKNESS, report))

    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
