"""Build/refresh a board from <board>.netlist.json + boards.py (outline, holes, keep-outs, placement).
Run with KiCad's python, board CLOSED in KiCad:
   "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" pcb_build.py carrier [--keep-placement]
Coordinates in boards.py are DEVICE mm (origin = device centre, +X right end, +Y top edge, seen
from the front). KiCad shows them with Y flipped around the board origin (100, 100).
"""
import json
import math
import os
import sys

import pcbnew as P

import boards

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
KFP = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
ALIB = os.path.join(ROOT, "lib", "ansonia.pretty")
MM = P.FromMM
OX, OY = 100.0, 100.0


def dev(x, y):
    return P.VECTOR2I(MM(OX + x), MM(OY - y))


def load_fp(fpid):
    lib, name = fpid.split(":", 1)
    path = ALIB if lib == "ansonia" else os.path.join(KFP, lib + ".pretty")
    fp = P.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError("footprint not found: " + fpid)
    fp.SetFPID(P.LIB_ID(lib, name))
    return fp


def outline(board, polys, width=0.1, gaps=()):
    gaps = {tuple(sorted(g)) for g in gaps}
    for poly in polys:
        n = len(poly)
        for i in range(n):
            if tuple(sorted((tuple(poly[i]), tuple(poly[(i + 1) % n])))) in gaps:
                continue
            s = P.PCB_SHAPE(board)
            s.SetShape(P.SHAPE_T_SEGMENT)
            s.SetLayer(P.Edge_Cuts)
            s.SetStart(dev(*poly[i]))
            s.SetEnd(dev(*poly[(i + 1) % n]))
            s.SetWidth(MM(width))
            board.Add(s)


def rule_area(board, pts, layers, name, tracks=True, vias=True, pour=True, footprints=False, pads=False):
    z = P.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowZoneFills(pour)
    z.SetDoNotAllowFootprints(footprints)
    z.SetDoNotAllowPads(pads)
    ls = P.LSET()
    for l in layers:
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(dev(x, y).x, dev(x, y).y)
    board.Add(z)
    return z


def pour(board, net, layer, polys, priority=0, clearance=0.25, min_w=0.2, hatch=False):
    z = P.ZONE(board)
    z.SetLayer(layer)
    z.SetNetCode(net.GetNetCode())
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(MM(clearance))
    z.SetMinThickness(MM(min_w))
    z.SetPadConnection(P.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.35))
    if hatch:
        z.SetFillMode(P.ZONE_FILL_MODE_HATCH_PATTERN)
        z.SetHatchThickness(MM(0.3))
        z.SetHatchGap(MM(0.7))
    ol = z.Outline()
    for poly in polys:
        ol.NewOutline()
        for x, y in poly:
            v = dev(x, y)
            ol.Append(v.x, v.y)
    board.Add(z)
    return z


def ring(cx, cy, r, n=24):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def setup_board(board, spec):
    ds = board.GetDesignSettings()
    board.SetCopperLayerCount(spec["layers"])
    ds.SetBoardThickness(MM(spec["thickness"]))
    ds.m_TrackMinWidth = MM(0.127)
    ds.m_MinClearance = MM(0.127)
    ds.m_ViasMinSize = MM(0.45)
    ds.m_MinThroughDrill = MM(0.3)
    ds.m_ViasMinAnnularWidth = MM(0.075)
    ds.m_CopperEdgeClearance = MM(0.3)
    ds.m_HoleClearance = MM(0.2)
    ds.m_HoleToHoleMin = MM(0.25)
    ds.m_SilkClearance = MM(0.0)
    ds.SetAuxOrigin(dev(0, 0))
    ds.SetGridOrigin(dev(0, 0))
    tb = board.GetTitleBlock()
    tb.SetTitle(spec["title"])
    tb.SetRevision("A")
    tb.SetCompany("Ansonia")
    tb.SetDate("2026-11-23")
    for i, c in enumerate(spec.get("comments", [])):
        tb.SetComment(i, c)


def build(name, keep=False):
    spec = boards.BOARDS[name]
    bdir = os.path.join(ROOT, name)
    js = json.load(open(os.path.join(bdir, name + ".netlist.json")))
    path = os.path.join(bdir, name + ".kicad_pcb")
    old = {}
    if keep and os.path.exists(path):
        ob = P.LoadBoard(path)
        for fp in ob.GetFootprints():
            old[fp.GetReference()] = (fp.GetPosition(), fp.GetOrientationDegrees(), fp.IsFlipped())
    board = P.NewBoard(path)
    setup_board(board, spec)
    # exact KiCad net names (incl. unconnected-(...) for no-connect pins) from kicad-cli's netlist export
    padnet = {}
    import kisexp
    tree = kisexp.parse(open(os.path.join(bdir, name + ".net"), encoding="utf-8").read())
    for n in kisexp.find(kisexp.first(tree, "nets"), "net"):
        nname = kisexp.first(n, "name")[1].lstrip("/")
        for nd in kisexp.find(n, "node"):
            padnet[(kisexp.first(nd, "ref")[1], kisexp.first(nd, "pin")[1])] = nname
    nets = {}
    for n in sorted(set(padnet.values()) | set(js["nets"])):
        ni = P.NETINFO_ITEM(board, n)
        board.Add(ni)
        nets[n] = ni
    outline(board, spec["outline"], gaps=spec.get("outline_gaps", ()))
    for poly in spec.get("cutouts", []):
        outline(board, [poly])

    fps = {}
    for part in js["parts"]:
        fp = load_fp(part["footprint"])
        fp.SetParent(board)
        fp.SetReference(part["ref"])
        fp.SetValue(part["value"])
        fp.SetPath(P.KIID_PATH("/%s/%s" % (part["sheet_uuid"], part["sym_uuid"])))
        fp.SetSheetname(part["sheet"])
        fp.SetSheetfile(part["sheet"] + ".kicad_sch")
        for k, v in part["fields"].items():
            fp.SetField(k, v)
            f = fp.GetField(k)
            if f is not None:
                f.SetVisible(False)
        for fname, key in (("Datasheet", "datasheet"), ("Description", "description")):
            f = fp.GetField(fname)
            if f is not None:
                f.SetText(part.get(key, ""))
        if part["dnp"]:
            fp.SetDNP(True)
        if not part.get("in_bom", True):
            fp.SetExcludedFromBOM(True)
            fp.SetExcludedFromPosFiles(True)
        else:
            fp.SetExcludedFromBOM(False)
        pins = part["pins"]
        for pad in fp.Pads():
            num = pad.GetNumber()
            net = padnet.get((part["ref"], num))
            if net:
                pad.SetNet(nets[net])
        board.Add(fp)
        fps[part["ref"]] = (fp, part)

    # keep-outs
    for ko in spec.get("keepouts", []):
        layers = [getattr(P, l.replace(".", "_")) for l in ko.get("layers", ["F.Cu", "B.Cu"])]
        rule_area(board, ko["pts"], layers, ko["name"], footprints=ko.get("footprints", False))

    # mounting holes
    for ref, (x, y) in spec.get("holes", {}).items():
        spec["place"].setdefault(ref, (x, y, 0))

    # placement
    placed = []
    for ref, (fp, part) in fps.items():
        if keep and ref in old:
            pos, rot, flip = old[ref]
            if flip:
                fp.Flip(fp.GetPosition(), P.FLIP_DIRECTION_LEFT_RIGHT)
            fp.SetPosition(pos)
            fp.SetOrientationDegrees(rot)
            placed.append(ref)
        elif ref in spec["place"]:
            v = list(spec["place"][ref])
            x, y, rot = v[:3]
            side = v[3] if len(v) > 3 else "F"
            if side == "B":
                fp.Flip(fp.GetPosition(), P.FLIP_DIRECTION_LEFT_RIGHT)
            fp.SetPosition(dev(x, y))
            fp.SetOrientationDegrees(rot)
            placed.append(ref)
    autoplace(board, spec, fps, placed, js)

    # acoustic port: NPTH under a bottom-port MEMS mic + ring-gasket outline on F.Fab
    apt = spec.get("acoustic_port")
    if apt:
        host = fps[apt["host"]][0]
        have = [p for p in host.Pads() if p.GetAttribute() == P.PAD_ATTRIB_NPTH]
        if have:
            print("  acoustic port: footprint already has NPTH d=%.3f mm" % P.ToMM(have[0].GetDrillSize().x))
            apt = dict(apt, host=None)
    if apt and apt.get("host"):
        pad = P.PAD(host)
        pad.SetAttribute(P.PAD_ATTRIB_NPTH)
        pad.SetShape(P.PAD_SHAPE_CIRCLE)
        dd = MM(apt["drill"])
        pad.SetSize(P.VECTOR2I(dd, dd))
        pad.SetDrillShape(P.PAD_DRILL_SHAPE_CIRCLE)
        pad.SetDrillSize(P.VECTOR2I(dd, dd))
        ls = P.LSET()
        for l in (P.F_Cu, P.B_Cu, P.F_Mask, P.B_Mask):
            ls.AddLayer(l)
        pad.SetLayerSet(ls)
        pad.SetPosition(dev(*apt["at"]))
        host.Add(pad)
    if apt:
        for r in (apt["gasket_od"] / 2, apt["gasket_id"] / 2):
            c = P.PCB_SHAPE(board)
            c.SetShape(P.SHAPE_T_CIRCLE)
            c.SetLayer(P.F_Fab)
            c.SetCenter(dev(*apt["at"]))
            c.SetEnd(P.VECTOR2I(dev(*apt["at"]).x + MM(r), dev(*apt["at"]).y))
            c.SetWidth(MM(0.1))
            board.Add(c)
        t = P.PCB_TEXT(board)
        t.SetText("acoustic gasket ring OD%.1f ID%.1f, port hole = wall hole (-69.5, 31.25)" % (apt["gasket_od"], apt["gasket_id"]))
        t.SetLayer(P.F_Fab)
        t.SetPosition(dev(apt["at"][0] + 3.4, apt["at"][1] - 5.2))
        t.SetTextSize(P.VECTOR2I(MM(0.6), MM(0.6)))
        board.Add(t)

    # copper pours
    gnd = nets.get("GND")
    if gnd and not spec.get("no_default_pour"):
        layers = [P.F_Cu, P.B_Cu] + ([P.In1_Cu] if spec["layers"] >= 4 else [])
        for l in layers:
            pour(board, gnd, l, spec["outline"], priority=0)
    for z in spec.get("pours", []):
        pour(board, nets[z["net"]], getattr(P, z["layer"].replace(".", "_")), [z["pts"]],
             priority=z.get("priority", 1), clearance=z.get("clearance", 0.25), hatch=z.get("hatch", False))
    for t in spec.get("texts", []):
        tx = P.PCB_TEXT(board)
        tx.SetText(t[0])
        tx.SetPosition(dev(t[1], t[2]))
        tx.SetLayer(getattr(P, t[3].replace(".", "_")))
        tx.SetTextSize(P.VECTOR2I(MM(t[4]), MM(t[4])))
        tx.SetTextThickness(MM(t[4] * 0.15))
        if t[3].startswith("B."):
            tx.SetMirrored(True)
        board.Add(tx)
    filler = P.ZONE_FILLER(board) if False else None
    pass  # zones are filled by kicad-cli drc --refill-zones (snap.py)
    P.SaveBoard(path, board)
    dru = spec.get("dru")
    if dru:
        with open(os.path.join(bdir, name + ".kicad_dru"), "w", newline=chr(10)) as f:
            f.write("(version 1)" + chr(10) + dru)


# ------------------------------------------------------------------ auto placement
def _bbox_local(fp):
    """courtyard bbox (mm) relative to the footprint origin at its current orientation/side."""
    layer = P.B_CrtYd if fp.IsFlipped() else P.F_CrtYd
    cy = fp.GetCourtyard(layer)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    p = fp.GetPosition()
    return (P.ToMM(bb.GetLeft() - p.x), P.ToMM(bb.GetTop() - p.y), P.ToMM(bb.GetRight() - p.x),
            P.ToMM(bb.GetBottom() - p.y))


def _inside(poly, x, y):
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def autoplace(board, spec, fps, placed, js):
    gap = spec.get("gap", 0.25)
    outl = [[(OX + x, OY - y) for x, y in poly] for poly in spec["outline"]]
    cut = [[(OX + x, OY - y) for x, y in poly] for poly in spec.get("cutouts", [])]
    blocked = []
    for ko in spec.get("keepouts", []) + spec.get("no_parts", []):
        xs = [OX + p[0] for p in ko["pts"]]
        ys = [OY - p[1] for p in ko["pts"]]
        side = ko.get("side", "FB")
        if "layers" in ko:
            side = "".join(sorted({l[0] for l in ko["layers"]}))
        blocked.append((min(xs), min(ys), max(xs), max(ys), side))
    for (x, y) in spec.get("holes", {}).values():
        blocked.append((OX + x - 2.4, OY - y - 2.4, OX + x + 2.4, OY - y + 2.4, "FB"))
    rects = []
    for ref in placed:
        fp = fps[ref][0]
        l, t, r, b = _bbox_local(fp)
        p = fp.GetPosition()
        thru = any(pd.GetAttribute() in (P.PAD_ATTRIB_PTH, P.PAD_ATTRIB_NPTH) for pd in fp.Pads())
        rects.append((P.ToMM(p.x) + l, P.ToMM(p.y) + t, P.ToMM(p.x) + r, P.ToMM(p.y) + b,
                      "FB" if thru else ("B" if fp.IsFlipped() else "F")))

    def free(x0, y0, x1, y1, side):
        for poly in outl:
            if all(_inside(poly, px, py) for px, py in ((x0 - .3, y0 - .3), (x1 + .3, y0 - .3), (x1 + .3, y1 + .3),
                                                         (x0 - .3, y1 + .3), ((x0 + x1) / 2, (y0 + y1) / 2))):
                break
        else:
            return False
        for poly in cut:
            for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1), ((x0 + x1) / 2, (y0 + y1) / 2)):
                if _inside(poly, px, py):
                    return False
        for a in rects + blocked:
            if side not in a[4]:
                continue
            if x0 < a[2] + gap and x1 > a[0] - gap and y0 < a[3] + gap and y1 > a[1] - gap:
                return False
        return True

    power = set(spec.get("power_nets", ["GND", "+3V3", "VSYS"]))
    anchors = {r: v for r, v in fps.items() if r in placed}
    todo = [r for r in fps if r not in placed]
    # bigger parts first
    def area(r):
        l, t, rr, b = _bbox_local(fps[r][0])
        return -(rr - l) * (b - t)
    todo.sort(key=area)
    for ref in todo:
        fp, part = fps[ref]
        my = {n for n in part["pins"].values() if n}
        best = None
        hint = spec.get("near", {}).get(ref)
        if hint:
            best = hint if isinstance(hint, str) else None
        if best is None:
            score = {}
            for ar, (afp, ap) in anchors.items():
                shared = my & {n for n in ap["pins"].values() if n}
                sig = shared - power
                if sig:
                    score[ar] = score.get(ar, 0) + 10 * len(sig) + (5 if ap["sheet"] == part["sheet"] else 0)
                elif shared and ap["sheet"] == part["sheet"]:
                    score[ar] = score.get(ar, 0) + 1
            if score:
                best = max(score, key=lambda r: (score[r], -len(fps[r][1]["pins"])))
        if best is None or best not in anchors:
            same = [r for r in anchors if fps[r][1]["sheet"] == part["sheet"]]
            best = same[0] if same else next(iter(anchors))
        afp = anchors[best][0]
        side = "B" if afp.IsFlipped() else "F"
        if side == "B":
            fp.Flip(fp.GetPosition(), P.FLIP_DIRECTION_LEFT_RIGHT)
        ap = afp.GetPosition()
        ax, ay = P.ToMM(ap.x), P.ToMM(ap.y)
        def search(side):
            for rad in [i * 0.25 for i in range(4, 160)]:
                steps = max(8, int(2 * math.pi * rad / 0.5))
                for k in range(steps):
                    ang = 2 * math.pi * k / steps
                    x, y = ax + rad * math.cos(ang), ay + rad * math.sin(ang)
                    x, y = round(x * 4) / 4, round(y * 4) / 4
                    for rot in (0, 90):
                        fp.SetOrientationDegrees(rot)
                        fp.SetPosition(P.VECTOR2I(MM(x), MM(y)))
                        l, t, r, b = _bbox_local(fp)
                        if free(x + l, y + t, x + r, y + b, side):
                            rects.append((x + l, y + t, x + r, y + b, side))
                            return True
            return False

        done = search(side)
        if not done and spec.get("allow_back") and ref.rstrip("0123456789") in ("C", "R", "FB", "D"):
            fp.Flip(fp.GetPosition(), P.FLIP_DIRECTION_LEFT_RIGHT)
            side = "B" if side == "F" else "F"
            done = search(side)
            if not done:
                fp.Flip(fp.GetPosition(), P.FLIP_DIRECTION_LEFT_RIGHT)
        if not done:
            print("  !! could not place", ref, "near", best)
            fp.SetPosition(P.VECTOR2I(MM(OX - 60), MM(OY)))
        anchors[ref] = (fp, part)


if __name__ == "__main__":
    keep = "--keep-placement" in sys.argv
    for n in [a for a in sys.argv[1:] if not a.startswith("--")]:
        build(n, keep)
