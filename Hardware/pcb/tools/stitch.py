"""GND stitching: grid vias in the pours + vias next to every GND pad, then prune the ones DRC objects to.
   "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" stitch.py <board> [pitch_mm]
Needs kicad-cli on the default install path (refills zones before every DRC pass)."""
import json
import os
import subprocess
import sys

import pcbnew as P

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
MM = P.FromMM
TAG = "stitch"


def drc_json(name):
    d = os.path.join(ROOT, name)
    out = os.path.join(d, name + "_drc.json")
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "--severity-all", "--refill-zones", "--save-board",
                    "-o", out, name + ".kicad_pcb"], cwd=d, capture_output=True, text=True)
    return json.load(open(out, encoding="utf-8"))


def add_via(board, gnd, x, y, dia=0.6, drill=0.3):
    v = P.PCB_VIA(board)
    v.SetPosition(P.VECTOR2I(int(x), int(y)))
    v.SetViaType(P.VIATYPE_THROUGH)
    v.SetWidth(MM(dia))
    v.SetDrill(MM(drill))
    v.SetNet(gnd)
    board.Add(v)
    return v


def main(name, pitch=4.0, extra=()):
    pcb = os.path.join(ROOT, name, name + ".kicad_pcb")
    board = P.LoadBoard(pcb)
    gnd = board.FindNet("GND")
    bb = board.GetBoardEdgesBoundingBox()
    vias = []
    nets_done = ("GND",) + tuple(extra)
    # grid
    x = bb.GetLeft() + MM(1.5)
    while x < bb.GetRight() - MM(1.0):
        y = bb.GetTop() + MM(1.5)
        while y < bb.GetBottom() - MM(1.0):
            vias.append(add_via(board, gnd, x, y))
            y += MM(pitch)
        x += MM(pitch)
    # next to GND pads
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNet() is None or pad.GetNetname() not in nets_done or pad.GetAttribute() != P.PAD_ATTRIB_SMD:
                continue
            ni = board.FindNet(pad.GetNetname())
            sz = pad.GetSize()
            c = pad.GetPosition()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                off = (sz.x / 2 + MM(0.25)) * dx if dx else 0
                offy = (sz.y / 2 + MM(0.25)) * dy if dy else 0
                vias.append(add_via(board, ni, c.x + off, c.y + offy))
    P.SaveBoard(pcb, board)
    for it in range(4):
        rep = drc_json(name)
        bad = set()
        for sec in ("violations", "unconnected_items"):
            for v in rep.get(sec, []):
                if v["type"] in ("unconnected_items", "starved_thermal", "isolated_copper"):
                    continue
                for itm in v.get("items", []):
                    if any(itm["description"].startswith("Via [%s]" % n) for n in nets_done):
                        bad.add((round(itm["pos"]["x"], 3), round(itm["pos"]["y"], 3)))
        board = P.LoadBoard(pcb)
        n = 0
        for t in list(board.GetTracks()):
            if t.Type() == P.PCB_VIA_T and t.GetNetname() in nets_done:
                p = t.GetPosition()
                if (round(P.ToMM(p.x) - 100.0 + 100.0, 3), round(P.ToMM(p.y), 3)) in bad or \
                        (round(P.ToMM(p.x), 3), round(P.ToMM(p.y), 3)) in bad:
                    board.Remove(t)
                    n += 1
        P.SaveBoard(pcb, board)
        print("pass", it, "removed", n, "vias")
        if n == 0:
            break
    rep = drc_json(name)
    cnt = {}
    for sec in ("violations", "unconnected_items"):
        for v in rep.get(sec, []):
            cnt[v["type"]] = cnt.get(v["type"], 0) + 1
    print(name, cnt)


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2][0].isdigit() else 4.0,
         tuple(a[7:] for a in sys.argv if a.startswith("--pads=")))
