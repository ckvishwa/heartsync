"""Hand-routed lines (device mm), drawn after pcb_build and before route.py (Freerouting keeps them fixed).
   "C:\Program Files\KiCad\10.0\bin\python.exe" handroute.py carrier
RF50: 50 ohm CPWG on F.Cu over the In1 GND plane. RF_W is an ESTIMATE (0.2 mm): recompute with the JLCPCB impedance
calculator for the real 1.0 mm 4-layer stack-up before ordering (the pour clearance of the RF50 class is the CPW gap)."""
import os
import sys

import pcbnew as P

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
MM = P.FromMM
RF_W = 0.2

ROUTES = {
    "carrier": [
        ("LTE_RF", "F.Cu", RF_W, [(13.2, 24.55), (15.19, 24.55)]),
        ("LTE_UFL", "F.Cu", RF_W, [(16.21, 24.55), (16.97, 24.55), (16.97, 27.0)]),
        ("GNSS_RF", "F.Cu", RF_W, [(1.3, 25.9), (1.3, 27.0), (0.2, 27.0), (0.2, 29.2), (-4.49, 29.2)]),
        ("GNSS_UFL", "F.Cu", RF_W, [(-5.51, 29.2), (-10.0, 29.2), (-10.0, 26.0), (-8.03, 26.0)]),
        ("BT_RF", "F.Cu", RF_W, [(-50.5, 15.0), (-50.5, 16.2), (-52.09, 16.2)]),
        ("BT_UFL", "F.Cu", RF_W, [(-53.11, 16.2), (-53.8, 16.2), (-53.8, 19.0), (-51.52, 19.0)]),
    ],
    "power": [],
}


def main(name):
    path = os.path.join(ROOT, name, name + ".kicad_pcb")
    board = P.LoadBoard(path)
    for net, layer, w, pts in ROUTES.get(name, []):
        ni = board.FindNet(net)
        for a, b in zip(pts, pts[1:]):
            t = P.PCB_TRACK(board)
            t.SetStart(P.VECTOR2I(MM(100 + a[0]), MM(100 - a[1])))
            t.SetEnd(P.VECTOR2I(MM(100 + b[0]), MM(100 - b[1])))
            t.SetWidth(MM(w))
            t.SetLayer(getattr(P, layer.replace(".", "_")))
            t.SetNet(ni)
            board.Add(t)
    P.SaveBoard(path, board)
    print("hand-routed", name, sum(len(p) - 1 for _, _, _, _, p in [(0, 0, 0, 0, r[3]) for r in ROUTES.get(name, [])]), "segments")


if __name__ == "__main__":
    main(sys.argv[1])
