"""
heartsync - parts modelled from datasheet drawings (Fusion 360 script, Python)

For bought parts whose maker publishes no STEP file. Each part is built from the dimensions
in its datasheet drawing (the PDF sits next to the STEP in cad/models/<part>/) and exported
as <part>_from_drawing.step. Every model here is flagged "verify on arrival": measure the
real part and fix the numbers below.

Run from the Fusion MCP or Scripts and Add-ins. The script opens its own new document,
builds, exports and closes it again without saving; it never touches the active document.
Sizes in mm. Frames are given per part below and in each part's README.
"""
import adsk.core
import adsk.fusion
import os

HERE = os.path.dirname(os.path.abspath(globals().get("__file__", ".")))
if not os.path.isdir(os.path.join(HERE, "flexpifa_001-0014")):
    HERE = "D:/SyncD/cad/models"          # when run as text through the MCP
IN = 25.4
G = {}


def cm(v):
    return v / 10.0


def P(x, y, z):
    return adsk.core.Point3D.create(cm(x), cm(y), cm(z))


def box(x0, y0, z0, x1, y1, z1):
    c = P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    ob = adsk.core.OrientedBoundingBox3D.create(
        c, adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0),
        cm(abs(x1 - x0)), cm(abs(y1 - y0)), cm(abs(z1 - z0)))
    return G["tbm"].createBox(ob)


def cyl(a, b, d, d2=None):
    """Cylinder (or cone frustum) from point a to point b, diameters d (at a) and d2 (at b)."""
    return G["tbm"].createCylinderOrCone(P(*a), cm(d) / 2, P(*b), cm(d if d2 is None else d2) / 2)


def sphere(c, d):
    return G["tbm"].createSphere(P(*c), cm(d) / 2)


def union(bodies):
    t = bodies[0]
    for b in bodies[1:]:
        G["tbm"].booleanOperation(t, b, adsk.fusion.BooleanTypes.UnionBooleanType)
    return t


def part(name, pieces):
    """pieces: [(body name, [temp bodies to unite])]. One component per part, exported."""
    occ = G["root"].occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = name
    for bname, tb in pieces:
        b = comp.bRepBodies.add(union(tb))
        b.name = bname
    folder, fname = G["targets"][name]
    path = os.path.join(HERE, folder, fname)
    em = G["design"].exportManager
    em.execute(em.createSTEPExportOptions(path, comp))
    bb = comp.boundingBox
    G["log"].append("%s -> %s/%s  size %.2f x %.2f x %.2f" % (
        name, folder, fname, (bb.maxPoint.x - bb.minPoint.x) * 10,
        (bb.maxPoint.y - bb.minPoint.y) * 10, (bb.maxPoint.z - bb.minPoint.z) * 10))


# ----------------------------------------------------------------------
# PARTS
# ----------------------------------------------------------------------
def flexpifa():
    """Ezurio FlexPIFA 001-0014 (right-hand), datasheet Figure 1.
    Frame: X along the 40.12 length, Y across the 11 width, Z thickness. Adhesive (element)
    face on +Z at Z 2.5; the 17 x 11 x 2.3 foam spacer hangs below the far (+X) end, which
    folds over at X 40.12..41.25. The MHF1 cable (dia 1.13) is soldered at that end and runs
    along -Y next to the fold, from the thick (foam) end; the model keeps it across the end and
    1.0 mm past the edge (the solder joint and strain relief), the assembly routes the rest."""
    L, W, T, FPC = 40.12, 11.0, 2.5, 0.152
    foam_x0 = L - 17.0
    pieces = [
        ("fpc", [box(0, 0, T - FPC, L, W, T)]),
        ("foam", [box(foam_x0, 0, T - FPC - 2.3, L, W, T - FPC)]),
        ("fold_solder", [box(L, 0, 0, 41.25, W, T)]),
        ("cable_stub", [cyl((41.25 - 0.565, W, T - 0.565), (41.25 - 0.565, -1.0, T - 0.565), 1.13)]),
    ]
    part("flexpifa_001-0014_from_drawing", pieces)


def shr(n):
    """JST SHR-0nV-S-B housing (with protrusions), eSH.pdf p2: body A+2 wide (A = n-1),
    2.8 deep, 5 long; protrusions make it A+4 wide. Frame: X across the circuits (centred),
    Y depth 0..2.8, Z along the wires: Z 0 = mating face, wires leave at Z 5. The protrusion
    size (1.0 x 2.0 x 1.1) is read off the drawing, not dimensioned: verify."""
    A = n - 1.0
    w = A + 2.0
    pieces = [("housing", [box(-w / 2, 0, 0, w / 2, 2.8, 5.0),
                           box(-w / 2 - 1.0, 0.4, 3.9, -w / 2, 2.4, 5.0),
                           box(w / 2, 0.4, 3.9, w / 2 + 1.0, 2.4, 5.0)])]
    part("shr-%02dv-s-b_from_drawing" % n, pieces)


def latch():
    """G-Switch PS-7054DVB-6PL, 7 x 7 mm self-latching DPDT, DIP (drawing PS-7054DVX-6PL).
    Frame: Z 0 = PCB top (seating plane), case 7 x 7 x 7, knob 4 (X) x 3 (Y) up to Z 12.4
    (released; latched it sits 1.3 lower, fully pressed 2.3). Pins 0.6 x 0.3, 3.5 long, on a
    2 mm pitch in X, rows 5 mm apart in Y."""
    pins = [box(x - 0.3, y - 0.15, -3.5, x + 0.3, y + 0.15, 0)
            for x in (-2.0, 0.0, 2.0) for y in (-2.5, 2.5)]
    pieces = [("case", [box(-3.5, -3.5, 0, 3.5, 3.5, 7.0)]),
              ("knob", [box(-2.0, -1.5, 7.0, 2.0, 1.5, 12.4)])]
    pieces += [("pin_%d" % (k + 1), [p]) for k, p in enumerate(pins)]
    part("ps-7054dvb-6pl_from_drawing", pieces)


def pogo():
    """Mill-Max 0906-2-15-20-75-14-11-0 spring-loaded pin, catalog p25 (inches, x 25.4).
    Frame: axis Z, Z 0 = underside of the .072 flange (board top), tip at A = .197 in
    (uncompressed). Plunger .042, barrel .059, collar .064 x .028 incl. flange, tail .017 x .069.
    Plunger shown out by the .055 max stroke; mid stroke .0275."""
    A = 0.197 * IN
    stroke = 0.055 * IN
    pieces = [("tail", [cyl((0, 0, -0.069 * IN), (0, 0, 0), 0.017 * IN)]),
              ("flange_barrel", [cyl((0, 0, 0), (0, 0, 0.016 * IN), 0.072 * IN),
                                 cyl((0, 0, 0.016 * IN), (0, 0, 0.028 * IN), 0.064 * IN),
                                 cyl((0, 0, 0.028 * IN), (0, 0, A - stroke), 0.059 * IN)]),
              ("plunger", [cyl((0, 0, A - stroke), (0, 0, A - 0.021 * IN), 0.042 * IN),
                           sphere((0, 0, A - 0.021 * IN), 0.042 * IN)])]
    part("0906-2-15-20-75-14-11-0_from_drawing", pieces)


def pogo_pad():
    """Device-side pogo target, our own part (no bought part chosen): dia 2.5 x 2.2 brass,
    gold plated, through the bottom-edge wall (params pogo_pad_d, wall_thickness); 0.2 x 45
    deg chamfer on the contact face. Inside the wall a 0.5 neck (through the silicone seal
    washer), a dia 4.0 x 0.4 flange that compresses the washer, and a dia 1.0 x 1.5 solder tail
    into the pogo board, which holds the pads. Frame: axis Z, contact face Z 0, wall inner face
    at Z 2.2, flange Z 2.7..3.1, tail end Z 4.6."""
    pieces = [("pad", [cyl((0, 0, 0), (0, 0, 0.2), 2.1, 2.5), cyl((0, 0, 0.2), (0, 0, 2.7), 2.5),
                       cyl((0, 0, 2.7), (0, 0, 3.1), 4.0), cyl((0, 0, 3.1), (0, 0, 4.6), 1.0)])]
    part("pogo_pad_from_params", pieces)


def magnet():
    """Disc magnet 6 x 2 mm, N45/N52, NiCuNi (supermagnete S-06-02-N / S-06-02-N52N class).
    0.2 x 45 deg edge chamfers (typical of sintered NdFeB discs; verify). Frame: axis Z,
    faces at Z 0 and Z 2."""
    c = 0.2
    pieces = [("magnet", [cyl((0, 0, 0), (0, 0, c), 6.0 - 2 * c, 6.0),
                          cyl((0, 0, c), (0, 0, 2.0 - c), 6.0),
                          cyl((0, 0, 2.0 - c), (0, 0, 2.0), 6.0, 6.0 - 2 * c)])]
    part("magnet_6x2_from_drawing", pieces)


def cell():
    """LiPol LP1160100 10,000 mAh pouch with PCM, drawing FD_0110_10 (2020-06-08), modelled at
    the MAXIMUM envelope for fit and swell checks: 100 +-1 x 60 +-0.5 x 11 +-0.3 -> 101 x 60.5
    x 11.3. The PCM is folded inside the length at one end (about 6 mm). Frame: X 0..101 with
    the PCM end at X 0..6, Y centred, Z 0..11.3. Two AWG22 UL1007 leads (dia 1.6) leave the PCM
    end at Y +21 / +25, mid-height, modelled as 4 mm stubs (the real leads are 100 mm, to be
    ordered with a JST connector). Lead positions are read off the drawing: verify. The 10 k NTC
    (ordered with the cell, wired to the charger's NTC input) leaves the same end at Y +17 as a
    thin AWG28 lead (dia 1.0)."""
    L, W, T, pcm = 101.0, 60.5, 11.3, 6.0
    pieces = [("pouch", [box(pcm, -W / 2, 0, L, W / 2, T)]),
              ("pcm_end", [box(0, -W / 2, 0, pcm, W / 2, T)]),
              ("lead_red", [cyl((0, 21.0, T / 2), (-4.0, 21.0, T / 2), 1.6)]),
              ("lead_black", [cyl((0, 25.0, T / 2), (-4.0, 25.0, T / 2), 1.6)]),
              ("lead_ntc", [cyl((0, 17.0, T / 2), (-4.0, 17.0, T / 2), 1.0)])]
    part("lp1160100_from_drawing", pieces)


def gnss():
    """Taoglas SGGP.12.4.A.02 SMD GNSS patch, datasheet SPE-15-8-034-D section 5: 12 x 12 x 4
    ceramic, silver top electrode with one cut corner, feed pad on the underside. Frame: X/Y
    centred, Z 0 = solder (bottom) face, top at Z 4. The electrode inset (1.2) and cut corner
    (2.0) are read off the drawing: verify."""
    s, t, e = 12.0, 4.0, 0.05
    a = s / 2 - 1.2
    elec = box(-a, -a, t - e, a, a, t)
    G["tbm"].booleanOperation(elec, box(a - 2.0, a - 2.0, t - e - 0.1, a + 0.1, a + 0.1, t + 0.1),
                              adsk.fusion.BooleanTypes.DifferenceBooleanType)
    pieces = [("ceramic", [box(-s / 2, -s / 2, 0, s / 2, s / 2, t - e)]),
              ("electrode", [elec])]
    part("sggp.12.4.a.02_from_drawing", pieces)


def panel_312():
    """Bare 3.12 in 256x64 SSD1322 OLED panel, Winstar WEX025664B drawing (88.0 x 27.8, VA 78.78 x
    21.18 at 4.61 / 2.0 from the left / top edge, polarizer 87.0 x 24.8, 30-pin FPC on the bottom
    edge, 60 wide at the panel and 14.0 from its left edge, tapering to the 15.5 + 1.0 finger
    width, 20.0 long). Thickness 2.15 (the drawing gives 2.05; the larger envelope is used).
    The FPC is modelled folded behind the panel, as in the drawing's side view: a 1.5 mm bend
    below the bottom edge, then 0.3 thick against the panel back, up to the 4.0 stiffened finger
    end (0.8 max). Frame: X 0..88 left to right, Y 0..27.8 with the FPC (bottom) edge at Y 0,
    Z 0 = viewing (front) face, panel toward +Z (Z 0..2.15), FPC behind it."""
    L, H, T = 88.0, 27.8, 2.15
    va_x, va_y, va_l, va_h = 4.61, 2.0, 78.78, 21.18
    e = 0.02
    va_y0 = H - va_y - va_h                       # VA measured from the top (non-FPC) edge
    fx0, fw = 14.0, 60.0
    cx = fx0 + fw / 2.0                           # FPC centre (44.0, the panel centre)
    ft, back = 0.3, T                            # FPC thickness; it lies on the panel back
    pieces = [
        ("glass", [box(0, 0, e, L, H, T)]),
        ("viewing_area", [box(va_x, va_y0, 0, va_x + va_l, va_y0 + va_h, e)]),
        ("fpc_bend", [box(fx0, -1.5, 0.6, fx0 + fw, 0, back + ft)]),
        ("fpc_tail", [box(fx0, 0, back, fx0 + fw, 2.0, back + ft),
                      box(cx - 20.0, 2.0, back, cx + 20.0, 9.5, back + ft),
                      box(cx - 8.25, 9.5, back, cx + 8.25, 12.0, back + ft)]),
        ("fpc_fingers", [box(cx - 8.25, 12.0, back, cx + 8.25, 16.0, back + 0.8)]),
    ]
    part("wex025664b_panel_from_drawing", pieces)


def run(_context):
    app = adsk.core.Application.get()
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
    G.update(design=design, root=design.rootComponent, log=[],
             tbm=adsk.fusion.TemporaryBRepManager.get())
    G["targets"] = {
        "flexpifa_001-0014_from_drawing": ("flexpifa_001-0014", "flexpifa_001-0014_from_drawing.step"),
        "ps-7054dvb-6pl_from_drawing": ("btn_latch_ps-7054dvb-6pl", "ps-7054dvb-6pl_from_drawing.step"),
        "0906-2-15-20-75-14-11-0_from_drawing": ("pogo_millmax_0906-2",
                                                  "0906-2-15-20-75-14-11-0_from_drawing.step"),
        "pogo_pad_from_params": ("pogo_pad", "pogo_pad_from_params.step"),
        "magnet_6x2_from_drawing": ("magnet_6x2", "magnet_6x2_from_drawing.step"),
    }
    G["targets"]["wex025664b_panel_from_drawing"] = ("oled_wex025664b_panel_312",
                                                     "wex025664b_panel_from_drawing.step")
    G["targets"]["lp1160100_from_drawing"] = ("cell_lipol_lp1160100", "lp1160100_from_drawing.step")
    G["targets"]["sggp.12.4.a.02_from_drawing"] = ("gnss_taoglas_sggp.12.4.a.02",
                                                     "sggp.12.4.a.02_from_drawing.step")
    for n in (2, 4, 5, 6, 7):
        G["targets"]["shr-%02dv-s-b_from_drawing" % n] = ("jst_sh", "shr-%02dv-s-b_from_drawing.step" % n)
    try:
        panel_312()
        cell()
        gnss()
        flexpifa()
        for n in (2, 4, 5, 6, 7):
            shr(n)
        latch()
        pogo()
        pogo_pad()
        magnet()
    finally:
        doc.close(False)
    msg = "\n".join(G["log"])
    print(msg)
    return msg
