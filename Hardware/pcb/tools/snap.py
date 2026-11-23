"""DRC (with zone refill + schematic parity) and placement snapshots for a board.
   python snap.py <board> [--no-drc]   -> <board>/fab/<board>_place_top.png / _bottom.png, <board>_DRC.rpt"""
import os
import re
import subprocess
import sys

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"


def cli(args, cwd):
    r = subprocess.run([CLI] + args, cwd=cwd, capture_output=True, text=True)
    return r.stdout + r.stderr


def drc(b):
    d = os.path.join(ROOT, b)
    cli(["pcb", "drc", "--severity-all", "--schematic-parity", "--refill-zones", "--save-board",
         "-o", b + "_DRC.rpt", b + ".kicad_pcb"], d)
    txt = open(os.path.join(d, b + "_DRC.rpt"), encoding="utf-8").read()
    counts = {}
    for m in re.finditer(r"^\[(\w+)\]", txt, re.M):
        counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    sev = {}
    for m in re.finditer(r"^\[(\w+)\].*\n.*\n\s+Rule.*; (\w+)", txt, re.M):
        pass
    return counts, txt


def shots(b, width_px=1800):
    d = os.path.join(ROOT, b)
    out = os.path.join(d, "fab")
    os.makedirs(out, exist_ok=True)
    res = []
    for side, layers in (("top", "Edge.Cuts,F.Cu,F.SilkS,F.Fab,F.CrtYd,User.Comments"),
                         ("bottom", "Edge.Cuts,B.Cu,B.SilkS,B.Fab,B.CrtYd")):
        svg = os.path.join(out, "%s_place_%s.svg" % (b, side))
        args = ["pcb", "export", "svg", "--layers", layers, "--exclude-drawing-sheet", "--page-size-mode", "2",
                "--mode-single", "-o", svg, b + ".kicad_pcb"]
        if side == "bottom":
            args.insert(3, "--mirror")
        cli(args, d)
        doc = pymupdf.open(svg)
        png = svg[:-4] + ".png"
        w_in = doc[0].rect.width / 72.0
        doc[0].get_pixmap(dpi=max(72, int(width_px / w_in))).save(png)
        os.remove(svg)
        res.append(png)
    return res


if __name__ == "__main__":
    b = sys.argv[1]
    print(shots(b))
    if "--no-drc" not in sys.argv:
        c, _ = drc(b)
        print(b, "DRC:", c)
