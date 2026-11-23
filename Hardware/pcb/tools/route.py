"""Autoroute a board with Freerouting (jar v2.1.0 in _vendor/freerouting, downloaded from the GitHub release). Run with KiCad's python:
   "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" route.py <board> [passes]
Existing tracks/vias (hand-routed RF/power, see handroute.py) are kept as fixed wires. GND is NOT autorouted:
it is poured on F / In1 / B and tied with stitching vias (stitch.py)."""
import os
import re
import subprocess
import sys

import pcbnew as P

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
FR = os.path.join(ROOT, "_vendor", "freerouting", "freerouting-2.1.0.jar")  # 2.5.0 CLI is broken, 2.3+ needs Java 25
SKIP = {"power": ("GND", "BAT_SW"), "carrier": ("GND",)}   # poured nets: not autorouted


def strip_net(txt, name):
    """remove the (net NAME ...) block of the network section and NAME from class net lists."""
    for pat in ('(net "%s"' % name, "(net %s" % name):
        i = txt.find(pat, txt.find("(network"))
        while i != -1:
            depth, j = 0, i
            while True:
                c = txt[j]
                depth += (c == "(") - (c == ")")
                j += 1
                if depth == 0:
                    break
            txt = txt[:i] + txt[j:]
            i = txt.find(pat, i)
    txt = re.sub(r'(\(class [^\n]*?)\s"%s"' % re.escape(name), r"\1", txt)
    txt = re.sub(r"(\(class [^\n]*?)\s%s(?=[\s)])" % re.escape(name), r"\1", txt)
    return txt


CLR = 150
WCAP = {"carrier": 300}
TIMEOUT = 2400


def main(name, passes=20, gnd=False):
    d = os.path.join(ROOT, name)
    pcb = os.path.join(d, name + ".kicad_pcb")
    board = P.LoadBoard(pcb)
    dsn = os.path.join(d, name + ".dsn")
    ses = os.path.join(d, name + ".ses")
    if not P.ExportSpecctraDSN(board, dsn):
        raise SystemExit("DSN export failed")
    txt = open(dsn, encoding="utf-8").read()
    for n in (() if gnd else SKIP.get(name, ("GND",))):
        txt = strip_net(txt, n)
    # KiCad writes smd_smd clearance as clearance/4 (37.5 um): restore it, and keep a margin on the rest
    txt = re.sub(r"\(clearance ([0-9.]+) \(type smd_smd\)\)", lambda m: "(clearance %s (type smd_smd))" % (CLR), txt)
    txt = re.sub(r"\(clearance (150|200)\)", lambda m: "(clearance %d)" % (int(m.group(1)) + 30), txt)
    cap = WCAP.get(name)
    if cap:   # fine-pitch ICs: wide power classes cannot escape, cap them (widen by pours/hand routing afterwards)
        txt = re.sub(r"\(rule(\s+)\(width (\d+)\)", lambda m: "(rule%s(width %d)" % (m.group(1), min(int(m.group(2)), cap)), txt)
    open(dsn, "w", encoding="utf-8").write(txt)
    if os.path.exists(ses):
        os.remove(ses)
    log = os.path.join(d, name + "_freerouting.log")
    with open(log, "w", encoding="utf-8") as lf:
        subprocess.run(["java", "-Djava.awt.headless=true", "-jar", FR, "-de", dsn, "-do", ses, "-mp", str(passes),
                        "-oit", "100"], stdout=lf, stderr=subprocess.STDOUT, timeout=TIMEOUT)
    print(open(log, encoding="utf-8", errors="replace").read().strip()[-600:])
    if not os.path.exists(ses):
        raise SystemExit("no SES written")
    if not P.ImportSpecctraSES(board, ses):
        raise SystemExit("SES import failed")
    P.SaveBoard(pcb, board)
    print("routed", name, "tracks:", len([t for t in board.GetTracks()]))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 20, "--gnd" in sys.argv)
