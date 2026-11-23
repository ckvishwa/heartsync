"""Fab exports per board: schematic PDF, Gerbers + drill (zip), JLCPCB BOM and CPL, 3D renders.
   python export.py <board> [<board> ...]      (zones are refilled by the DRC run first: run snap.py/stitch.py before)"""
import csv
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
LAYERS4 = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
LAYERS2 = "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"


def cli(args, cwd):
    r = subprocess.run([CLI] + args, cwd=cwd, capture_output=True, text=True)
    return r.stdout + r.stderr


def one(b):
    d = os.path.join(ROOT, b)
    fab = os.path.join(d, "fab")
    os.makedirs(fab, exist_ok=True)
    js = json.load(open(os.path.join(d, b + ".netlist.json"), encoding="utf-8"))
    four = b in ("carrier", "power")
    # schematic PDF
    cli(["sch", "export", "pdf", "-o", os.path.join(fab, b + "_schematic.pdf"), b + ".kicad_sch"], d)
    # refill + refresh DRC report is done by snap.py; gerbers + drill
    gdir = os.path.join(fab, "gerber")
    shutil.rmtree(gdir, ignore_errors=True)
    os.makedirs(gdir)
    cli(["pcb", "export", "gerbers", "--layers", LAYERS4 if four else LAYERS2, "--subtract-soldermask",
         "-o", gdir + os.sep, b + ".kicad_pcb"], d)
    cli(["pcb", "export", "drill", "--format", "excellon", "--drill-origin", "absolute", "--excellon-separate-th",
         "-o", gdir + os.sep, b + ".kicad_pcb"], d)
    zp = os.path.join(fab, b + "_gerber")
    shutil.make_archive(zp, "zip", gdir)
    # CPL (JLCPCB columns)
    pos = os.path.join(fab, b + "_pos_raw.csv")
    cli(["pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "--exclude-dnp",
         "-o", pos, b + ".kicad_pcb"], d)
    rows = list(csv.DictReader(open(pos, encoding="utf-8")))
    with open(os.path.join(fab, b + "_cpl.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in rows:
            w.writerow([r["Ref"], r["PosX"] + "mm", r["PosY"] + "mm", "Top" if r["Side"] == "top" else "Bottom", r["Rot"]])
    os.remove(pos)
    # BOM (JLCPCB columns), grouped
    groups = {}
    for p in js["parts"]:
        if p["dnp"] or not p.get("in_bom", True) or p["ref"].startswith("H"):
            continue
        key = (p["value"], p["footprint"].split(":")[-1], p["fields"].get("LCSC", ""), p["fields"].get("MPN", ""))
        groups.setdefault(key, []).append(p["ref"])
    with open(os.path.join(fab, b + "_bom.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "MPN", "Qty"])
        for (val, fp, lcsc, mpn), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
            w.writerow([val, ",".join(sorted(refs)), fp, lcsc, mpn, len(refs)])
    # renders
    for side in ("top", "bottom"):
        cli(["pcb", "render", "--side", side, "--quality", "basic", "--width", "1600", "--height", "900",
             "--background", "opaque", "-o", os.path.join(fab, "%s_3d_%s.png" % (b, side)), b + ".kicad_pcb"], d)
    print(b, "exported:", sorted(os.listdir(fab)))


if __name__ == "__main__":
    for b in sys.argv[1:]:
        one(b)
