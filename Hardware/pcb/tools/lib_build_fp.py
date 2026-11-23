"""Build Hardware/pcb/lib/ansonia.pretty. Run with KiCad's python:
   "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" lib_build_fp.py
Every footprint here records its source in the description. See lib/README.md.
"""
import os
import shutil
import pcbnew as P

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "lib", "ansonia.pretty")
VENDOR = os.path.join(ROOT, "_vendor")
KFP = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
MM = P.FromMM
IO = P.PCB_IO_MGR.FindPlugin(P.PCB_IO_MGR.KICAD_SEXP)


def V(x, y):
    return P.VECTOR2I(MM(x), MM(y))


def tmp_load(path):
    d = os.path.join(HERE, "_tmp.pretty")
    os.makedirs(d, exist_ok=True)
    shutil.copy(path, os.path.join(d, "x.kicad_mod"))
    fp = P.FootprintLoad(d, "x")
    shutil.rmtree(d)
    return fp


def save(fp, name, descr):
    fp.SetFPID(P.LIB_ID("ansonia", name))
    fp.SetLibDescription(descr)
    fp.SetValue(name)
    IO.FootprintSave(OUT, fp)
    print("saved", name)


def add_line(fp, layer, a, b, w=0.1):
    s = P.PCB_SHAPE(fp)
    s.SetShape(P.SHAPE_T_SEGMENT)
    s.SetLayer(layer)
    s.SetStart(a)
    s.SetEnd(b)
    s.SetWidth(MM(w))
    fp.Add(s)


def add_rect(fp, layer, x0, y0, x1, y1, w=0.05):
    for a, b in [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]:
        add_line(fp, layer, V(*a), V(*b), w)


def keepout(fp, pts, layers=("F.Cu",), tracks=True, vias=True, pour=True, pads=False):
    z = P.ZONE(fp)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowZoneFills(pour)
    z.SetDoNotAllowPads(pads)
    z.SetDoNotAllowFootprints(False)
    ls = P.LSET()
    for l in layers:
        ls.AddLayer(LAYER[l])
    z.SetLayerSet(ls)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(MM(x), MM(y))
    fp.Add(z)


LAYER = {"F.Cu": P.F_Cu, "B.Cu": P.B_Cu, "In1.Cu": P.In1_Cu, "In2.Cu": P.In2_Cu}


def smd_pad(fp, num, x, y, w, h, shape=P.PAD_SHAPE_RECT, mask=True):
    p = P.PAD(fp)
    p.SetNumber(num)
    p.SetAttribute(P.PAD_ATTRIB_SMD)
    p.SetShape(shape)
    p.SetSize(V(w, h))
    p.SetPosition(V(x, y))
    ls = P.LSET()
    ls.AddLayer(P.F_Cu)
    ls.AddLayer(P.F_Paste)
    ls.AddLayer(P.F_Mask)
    p.SetLayerSet(ls)
    fp.Add(p)
    return p


def pth_oval(fp, num, x, y, pw, ph, dw, dh):
    p = P.PAD(fp)
    p.SetNumber(num)
    p.SetAttribute(P.PAD_ATTRIB_PTH)
    p.SetShape(P.PAD_SHAPE_OVAL)
    p.SetSize(V(pw, ph))
    p.SetDrillShape(P.PAD_DRILL_SHAPE_OBLONG)
    p.SetDrillSize(V(dw, dh))
    p.SetPosition(V(x, y))
    p.SetLayerSet(P.PAD.PTHMask())
    fp.Add(p)
    return p


def sim7080g():
    fp = tmp_load(os.path.join(VENDOR, "SIM7080G.kicad_mod"))
    for p in fp.Pads():
        n = int(p.GetNumber())
        pos = p.GetPosition()
        x, y = P.ToMM(pos.x), P.ToMM(pos.y)
        if 1 <= n <= 12 or 22 <= n <= 33:  # left / right edge pads
            p.SetSize(V(1.3, 0.6))
            p.SetPosition(V(7.70 if x > 0 else -7.70, y))
        elif 13 <= n <= 21 or 34 <= n <= 42:  # bottom / top edge pads
            p.SetSize(V(0.6, 1.3))
            p.SetPosition(V(x, 8.65 if y > 0 else -8.65))
    # SIMCom "forbidden area" (Y7080E/SIM7080G HD fig. 4, read off the drawing): no copper on top
    keepout(fp, [(4.7, -7.9), (6.9, -7.9), (6.9, -2.45), (4.7, -2.45)], layers=("F.Cu",))
    save(fp, "SIM7080G", "SIMCom SIM7080G LGA-77, 15.7x17.6 mm. Source: Accelerando SIM7080G.kicad_mod; edge pads "
         "trimmed to SIMCom's 16.70/18.60 outer extents and forbidden-area keepout added (SIM7080G/Y7080E "
         "Hardware Design fig. 4). Pitches, inner pads and centre GND pads match the SIMCom drawing.")


def ewm104():
    import kisexp
    src = os.path.join(VENDOR, "ewm104", "pcb", "EWM104-BT5125-PCB", "EWM104-BT5125(KiCAD).kicad_mod")
    tree = kisexp.parse(open(src, encoding="utf-8").read())
    tree = [x for x in tree if not (isinstance(x, list) and x and x[0] == "pad" and x[2] == "thru_hole")]
    tmpf = os.path.join(HERE, "_ewm.kicad_mod")
    txt = kisexp.dump(tree)
    # vendor export put the pads on B.* and the module outline on Edge.Cuts: pin numbering is the
    # top view (Ebyte manual 2.2), so move everything to the top side and the outline to F.Fab
    txt = txt.replace('"Edge.Cuts"', '"F.Fab"').replace('"B.Cu"', '"F.Cu"').replace('"B.Paste"', '"F.Paste"')
    txt = txt.replace('"B.Mask"', '"F.Mask"').replace('"B.SilkS"', '"F.SilkS"').replace('"B.Fab"', '"F.Fab"')
    txt = txt.replace('"B.CrtYd"', '"F.CrtYd"').replace('"B.Courtyard"', '"F.Courtyard"')
    open(tmpf, "w", encoding="utf-8").write(txt)
    fp = tmp_load(tmpf)
    os.remove(tmpf)
    save(fp, "EWM104-BT5125", "Ebyte EWM104-BT5125 13x18 stamp-hole module, 54 pads 1.00 mm pitch. Source: Ebyte "
         "official EWM104-BT5125(KiCAD).kicad_mod (cdebyte.com pdf-down id 3632); the vendor's duplicate "
         "thru-hole pads (drill larger than pad) were removed so the carrier gets no holes. SMD pads unchanged.")


def esp32():
    src = os.path.normpath(os.path.join(ROOT, "..", "heartsync_kicad", "heartsync.pretty"))
    fp = P.FootprintLoad(src, "ESP32-S3-WROOM-1U_NoVias")
    save(fp, "ESP32-S3-WROOM-1U_NoVias", "ESP32-S3-WROOM-1U; KiCad stock footprint with 0.3 mm thermal vias "
         "(copied from Hardware/heartsync_kicad/heartsync.pretty, ADR 0010/0011).")


def tas5805m():
    fp = P.FootprintLoad(os.path.join(KFP, "Package_SO.pretty"),
                         "TSSOP-28-1EP_4.4x9.7mm_P0.65mm_EP3.4x9.7mm_Mask3.1x4.05mm_ThermalVias")
    n = 0
    for p in fp.Pads():
        if p.GetAttribute() == P.PAD_ATTRIB_PTH:
            p.SetDrillSize(V(0.3, 0.3))
            p.SetSize(V(0.55, 0.55))
            n += 1
    save(fp, "TI_PWP0028M_HTSSOP-28_ThermalVias_0.3", "TI PWP0028M PowerPAD TSSOP-28 (TAS5805M): 3.4x9.7 metal, "
         "3.1x4.05 mask opening per TI example board layout (datasheet p.100). KiCad stock footprint with the "
         "thermal-via drill raised from 0.2 to 0.3 mm (JLCPCB minimum); %d vias." % n)


def usbc():
    """Amphenol 124019572112A mid-mount USB-C, from drawing C 12401957 sheet 2 'Recommended PCB layout'
    (read on screen; CDN blocks scripted download). Origin = connector centreline at the A-row pad top edge.
    +Y points to the PCB edge (mating face)."""
    fp = P.FOOTPRINT(None)
    a = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11", "A12"]
    ax = [-3.15, -2.65, -2.15, -1.65, -0.75, -0.25, 0.25, 0.75, 1.65, 2.15, 2.65, 3.15]
    for n, x in zip(a, ax):
        smd_pad(fp, n, x, 0.4, 0.3, 0.8)
    b = ["B12", "B11", "B10", "B9", "B8", "B7", "B6", "B5", "B4", "B3", "B2", "B1"]
    bx = [-2.95, -2.45, -1.95, -1.45, -0.95, -0.45, 0.45, 0.95, 1.45, 1.95, 2.45, 2.95]
    for n, x in zip(b, bx):
        smd_pad(fp, n, x, 1.6, 0.3, 0.8)
    for x in (-4.875, 4.875):  # shell hooks (drawn L-shaped; modelled as straight slots, verify)
        pth_oval(fp, "SH", x, 0.95, 0.9, 1.9, 0.5, 1.5)
    for x in (-6.0, 6.0):  # rear shell legs at the board edge
        pth_oval(fp, "SH", x, 4.6, 0.9, 1.5, 0.5, 1.1)
    # board cut-out for the mid-mount body: 10.6 wide from Y 2.2 to the PCB edge. Amphenol puts the edge at
    # Y 5.40 (legs 0.05 from it); here the edge is at Y 5.65 so the legs keep 0.3 mm (port sits 0.25 further in)
    ec = P.Edge_Cuts
    add_line(fp, ec, V(-5.3, 5.65), V(-5.3, 2.5))
    add_line(fp, ec, V(5.3, 2.5), V(5.3, 5.65))
    arc = P.PCB_SHAPE(fp)
    arc.SetShape(P.SHAPE_T_ARC)
    arc.SetLayer(ec)
    arc.SetArcGeometry(V(-5.3, 2.5), V(-5.3 + 0.3 - 0.3 * 0.7071, 2.2 + 0.3 - 0.3 * 0.7071), V(-5.0, 2.2))
    arc.SetWidth(MM(0.1))
    fp.Add(arc)
    add_line(fp, ec, V(-5.0, 2.2), V(5.0, 2.2))
    arc = P.PCB_SHAPE(fp)
    arc.SetShape(P.SHAPE_T_ARC)
    arc.SetLayer(ec)
    arc.SetArcGeometry(V(5.0, 2.2), V(5.0 + 0.3 * 0.7071, 2.2 + 0.3 - 0.3 * 0.7071), V(5.3, 2.5))
    arc.SetWidth(MM(0.1))
    fp.Add(arc)
    add_rect(fp, P.F_CrtYd, -6.55, -0.5, 6.55, 5.65)
    add_rect(fp, P.F_Fab, -4.47, -0.3, 4.47, 7.0)  # receptacle shell 8.94 wide, protrudes past the edge
    add_rect(fp, P.F_SilkS, -6.5, -0.6, 6.5, 0.9, 0.12)
    fp.Reference().SetText("J**")
    fp.Reference().SetPosition(V(0, -1.6))
    fp.Reference().SetLayer(P.F_SilkS)
    fp.SetAttributes(P.FP_SMD)
    # 3D: cad/models/usbc_amphenol_124019572112a/124019572112a.step has an off-centre origin; transform TBD
    save(fp, "USB_C_Amphenol_124019572112A", "Amphenol 124019572112A USB 3.2 Type-C receptacle, mid-mount, "
         "IPX7/8. Built from Amphenol drawing C 12401957 sheet 2 (recommended PCB layout, tol +-0.05) read "
         "on screen; shell hooks simplified to straight slots. VERIFY against the drawing before fab.")


def placeholder_pdic():
    fp = P.FootprintLoad(os.path.join(KFP, "Package_DFN_QFN.pretty"), "QFN-40-1EP_6x6mm_P0.5mm_EP4.6x4.6mm")
    add_rect(fp, P.F_Fab, -9, -9, 9, 9, 0.1)
    t = P.PCB_TEXT(fp)
    t.SetText("PD/charger IC TBD: reserve 18x18 incl. inductor")
    t.SetLayer(P.F_Fab)
    t.SetPosition(V(0, -8))
    fp.Add(t)
    save(fp, "PLACEHOLDER_PDIC_QFN40_6x6", "Placeholder for the not-yet-chosen power-bank/PD IC (QFN-40 6x6 "
         "land, DNP). Pads carry labelled nets only; replace with the real part's footprint.")


def sh22():
    """JST SH SM22B-SRSS-TB (22 pin) is not in the KiCad library: extend the SM20B by two pads (1.0 mm pitch)."""
    fp = P.FootprintLoad(os.path.join(KFP, "Connector_JST.pretty"),
                         "JST_SH_SM20B-SRSS-TB_1x20-1MP_P1.00mm_Horizontal")
    dx = MM(1.0)

    def sh_x(x):
        return x + dx if x > 0 else x - dx

    for g in fp.GraphicalItems():
        if not hasattr(g, "GetStart"):
            continue
        a, b = g.GetStart(), g.GetEnd()
        g.SetStart(P.VECTOR2I(sh_x(a.x), a.y))
        g.SetEnd(P.VECTOR2I(sh_x(b.x), b.y))
    pads = {p.GetNumber(): p for p in fp.Pads()}
    for n in (21, 22):
        q = pads["20"].Duplicate()
        q.SetNumber(str(n))
        fp.Add(q)
        pads[str(n)] = q
    for i in range(1, 23):
        p = pads[str(i)]
        p.SetPosition(P.VECTOR2I(MM(i - 11.5), p.GetPosition().y))
    for p in fp.Pads():
        if p.GetNumber() == "MP":
            pos = p.GetPosition()
            p.SetPosition(P.VECTOR2I(sh_x(pos.x), pos.y))
    fp.Models().clear()
    save(fp, "JST_SH_SM22B-SRSS-TB_1x22-1MP_P1.00mm_Horizontal",
         "JST SH 22-pin side-entry SMD, made from KiCad's SM20B by adding two 1.0 mm pitch pads (JST SM22B-SRSS-TB). "
         "Verify against the JST drawing.")


def wirepads(n, pitch, pw=1.0, ph=2.0):
    """n SMD pads in a row for hand-soldered wires (no paste)."""
    fp = P.FOOTPRINT(None)
    x0 = -(n - 1) * pitch / 2.0
    for i in range(n):
        p = smd_pad(fp, str(i + 1), x0 + i * pitch, 0, pw, ph)
        ls = P.LSET()
        ls.AddLayer(P.F_Cu)
        ls.AddLayer(P.F_Mask)
        p.SetLayerSet(ls)
    w = (n - 1) * pitch / 2.0 + pw / 2 + 0.3
    add_rect(fp, P.F_CrtYd, -w, -ph / 2 - 0.3, w, ph / 2 + 0.3)
    fp.Reference().SetText("W**")
    fp.Reference().SetLayer(P.F_Fab)
    fp.SetAttributes(P.FP_SMD | P.FP_EXCLUDE_FROM_BOM | P.FP_EXCLUDE_FROM_POS_FILES)
    name = "WirePads_1x%02d_P%.2fmm" % (n, pitch)
    save(fp, name, "%d solder pads %.2f mm pitch (%.1f x %.1f) for hand-soldered wires, no paste." % (n, pitch, pw, ph))


def mr30():
    """Amass MR30PW-M (3-pole, 15 A, right angle): holes read from Amass spec sheet 'mounting hole' drawing.
    Origin = middle pin; pins on the row y=0, body toward -y (mating face at y -12)."""
    fp = P.FOOTPRINT(None)
    for i, x in enumerate((-3.5, 0.0, 3.5)):
        p = P.PAD(fp)
        p.SetNumber(str(i + 1))
        p.SetAttribute(P.PAD_ATTRIB_PTH)
        p.SetShape(P.PAD_SHAPE_CIRCLE)
        p.SetSize(V(3.1, 3.1))
        p.SetDrillShape(P.PAD_DRILL_SHAPE_CIRCLE)
        p.SetDrillSize(V(1.9, 1.9))
        p.SetPosition(V(x, 0))
        p.SetLayerSet(P.PAD.PTHMask())
        fp.Add(p)
    for x in (-6.5, 6.5):
        p = P.PAD(fp)
        p.SetNumber("")
        p.SetAttribute(P.PAD_ATTRIB_NPTH)
        p.SetShape(P.PAD_SHAPE_CIRCLE)
        p.SetSize(V(1.0, 1.0))
        p.SetDrillShape(P.PAD_DRILL_SHAPE_CIRCLE)
        p.SetDrillSize(V(1.0, 1.0))
        p.SetPosition(V(x, -10.0))
        ls = P.LSET()
        for l in (P.F_Cu, P.B_Cu, P.F_Mask, P.B_Mask):
            ls.AddLayer(l)
        p.SetLayerSet(ls)
        fp.Add(p)
    add_rect(fp, P.F_CrtYd, -8.0, -12.5, 8.0, 2.2)
    add_rect(fp, P.F_Fab, -7.65, -12.0, 7.65, 1.5, 0.1)
    fp.Reference().SetText("J**")
    fp.Reference().SetLayer(P.F_Fab)
    fp.SetAttributes(P.FP_THROUGH_HOLE)
    save(fp, "Amass_MR30PW-M_1x03_P3.50mm_Horizontal",
         "Amass MR30PW-M 3-pole 15 A right-angle PCB plug. Holes from the Amass spec sheet (3 x d1.9 at 3.5 mm, 2 x d1.0 at 13.0 mm). "
         "Body outline/locating-hole row (y -10) read from the drawing: VERIFY before fab. No 3D model.")


def touchpad():
    fp = P.FOOTPRINT(None)
    p = smd_pad(fp, "1", 0, 0, 34.0, 3.0)
    ls = P.LSET()
    ls.AddLayer(P.F_Cu)
    p.SetLayerSet(ls)  # copper only: solder mask stays over the pad
    add_rect(fp, P.F_CrtYd, -17.25, -1.75, 17.25, 1.75)
    add_rect(fp, P.F_Fab, -17, -1.5, 17, 1.5)
    fp.Reference().SetText("E**")
    fp.Reference().SetLayer(P.F_Fab)
    fp.SetAttributes(P.FP_SMD | P.FP_EXCLUDE_FROM_BOM | P.FP_EXCLUDE_FROM_POS_FILES)
    save(fp, "TouchPad_34x3", "Capacitive touch sense pad 34 x 3 mm, F.Cu under solder mask.")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sim7080g()
    ewm104()
    esp32()
    tas5805m()
    usbc()
    placeholder_pdic()
    touchpad()
    sh22()
    wirepads(8, 1.2)
    wirepads(2, 1.6)
    mr30()
