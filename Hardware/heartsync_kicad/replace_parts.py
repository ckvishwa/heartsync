r"""
heartsync carrier: re-place parts on an EXISTING board (outline and pours already there).

Two ways to run it:
  - PCB editor scripting console (one line):
        exec(open(r"D:\SyncD\Hardware\heartsync_kicad\replace_parts.py").read())
  - Headless, with the board CLOSED in KiCad (it loads, edits and saves the file):
        "C:\Program Files\KiCad\10.0\bin\python.exe" replace_parts.py heartsync_carrier.kicad_pcb

It only moves and rotates parts (safe to run again), checks that U1's U.FL socket faces a board edge
with 3 mm clear around it, sets the clearance rules (0.127 mm minimum, 0.15 mm default) and refills
the zones. Check the result with DRC (command in CLAUDE.md): zero courtyard, keepout and hole errors.
"""
import math
import sys

import pcbnew

X0, Y0 = 100.0, 100.0
board = pcbnew.GetBoard()
HEADLESS = board is None
if HEADLESS:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python.exe replace_parts.py <board.kicad_pcb>")
    BOARD_PATH = sys.argv[1]
    board = pcbnew.LoadBoard(BOARD_PATH)
report = []


def mm(v):
    return pcbnew.FromMM(v)


def step(name, fn):
    try:
        fn()
        report.append("ok    " + name)
    except Exception as e:
        report.append("FAIL  %s: %s" % (name, e))


# U1 is an ESP32-S3-WROOM-1U (ADR 0011): no PCB antenna, so no keepout. Its U.FL socket (top right of
# the module) faces the board top edge; module top edge 0.5 mm inside the board edge.
# JST-SH rotation = cable entry: 0 down, 90 right, 180 up, 270 left. J4 (left speaker) is on the left
# edge between H1 and H2, J5 (right speaker) on the right edge, so neither speaker cable crosses the
# device. U1 sits 1.5 mm right of its old spot to leave J4 room beside it.
# J7 is off-edge (open item) with its cable facing right.
PLACE = [
    ("H1", 3, 9, 0),
    ("U1", 17.0, 10.1, 0), ("U2", 6, 33, 0), ("L1", 11.5, 33, 0), ("C4", 2.8, 30.5, 90),
    ("C5", 15.5, 30, 90), ("R3", 6, 36.5, 0), ("R4", 9.5, 36.5, 0), ("C1", 28.0, 22, 90),
    ("C2", 28.0, 18.5, 90), ("R1", 25.5, 27, 0), ("C3", 25.5, 29.5, 0), ("R2", 24.25, 31.5, 0),
    ("SW1", 30.25, 34.75, 0), ("SW2", 39, 34.75, 0), ("J1", 66, 15.75, 90), ("U3", 58.5, 15, 0),
    ("C6", 58.5, 19, 0), ("J3", 66, 5.25, 90), ("U9", 59.6, 4.0, 0), ("C16", 59.6, 6.3, 0),
    ("C17", 59.6, 1.5, 0), ("Q1", 60.5, 9, 0), ("R11", 56.5, 10.5, 0), ("R12", 60.5, 12, 0),
    ("U4", 52, 21.5, 0), ("C7", 47.5, 21.5, 90), ("C8", 52, 18.5, 0), ("R5", 48.5, 25, 0),
    ("U5", 52, 28.5, 0), ("C9", 47.5, 28.5, 90), ("C10", 52, 31.5, 0), ("R6", 48.5, 31.6, 0),
    ("R7", 52.5, 33.5, 0), ("J4", 3.75, 17.5, 270), ("J5", 66.25, 30.25, 90), ("U6", 55, 37, 0),
    ("C11", 55, 40, 0), ("C12", 50.75, 37, 90), ("J6", 46.5, 35.9, 0), ("U8", 59, 42, 0),
    ("C15", 55.5, 42.5, 0), ("J2", 66, 41, 0), ("U7", 36, 24, 0), ("C13", 36, 27, 0),
    ("C14", 39.5, 24, 90), ("R8", 40, 18, 0), ("R9", 40, 20, 0), ("R10", 43.5, 18, 0),
    ("R13", 43.5, 9, 0), ("R14", 42.5, 11, 0), ("C18", 47.3, 9, 90), ("R15", 30, 30, 0),
    ("R16", 33.5, 30, 0), ("C19", 37, 30, 0), ("J7", 51.55, 11.3, 90), ("J8", 45, 3.75, 180),
    ("J9", 52.6, 3.75, 180), ("J11", 18.5, 41.25, 0), ("J10", 29, 41.25, 0), ("J12", 37, 41.25, 0),
    ("TP1", 2.5, 39, 0), ("TP2", 5, 39, 0), ("TP3", 7.5, 39, 0), ("TP4", 10, 39, 0),
    ("TP5", 2.5, 42.5, 0), ("TP6", 5, 42.5, 0), ("TP7", 7.5, 42.5, 0),
]


def place():
    missing = []
    for ref, x, y, rot in PLACE:
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            missing.append(ref)
            continue
        fp.SetPosition(pcbnew.VECTOR2I(mm(X0 + x), mm(Y0 + y)))
        fp.SetOrientationDegrees(rot)
    if missing:
        raise RuntimeError("not on the board: " + ", ".join(missing))


# U.FL socket on the WROOM-1U footprint, in footprint coordinates (mm): its F.Fab square.
UFL_LOCAL = (4.7, -8.44, 7.3, -5.84)
UFL_CLEAR = 3.0
BOARD_W, BOARD_H = 70.0, 45.0


def ufl_rect():
    """U.FL socket outline on the board (x0, y0, x1, y1 in board mm, origin at the board corner)."""
    u1 = board.FindFootprintByReference("U1")
    if "WROOM-1U" not in u1.GetFPID().GetLibItemName().wx_str():
        raise RuntimeError("U1 is %s, not a WROOM-1U" % u1.GetFPID().GetLibItemName().wx_str())
    pos, ang = u1.GetPosition(), u1.GetOrientation()
    t = math.radians(ang.AsDegrees())  # positive = counter-clockwise on screen (y points down)
    px, py = pcbnew.ToMM(pos.x) - X0, pcbnew.ToMM(pos.y) - Y0
    pts = []
    for lx, ly in ((UFL_LOCAL[0], UFL_LOCAL[1]), (UFL_LOCAL[2], UFL_LOCAL[3])):
        pts.append((px + lx * math.cos(t) + ly * math.sin(t), py - lx * math.sin(t) + ly * math.cos(t)))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def check_ufl():
    """U.FL socket must face a board edge and have UFL_CLEAR mm free of other parts around it."""
    x0, y0, x1, y1 = ufl_rect()
    edges = {"top": y0, "bottom": BOARD_H - y1, "left": x0, "right": BOARD_W - x1}
    edge, dist = min(edges.items(), key=lambda kv: kv[1])
    if dist > UFL_CLEAR:
        raise RuntimeError("U.FL socket %.1f mm from the nearest (%s) edge; want <= %.1f" % (dist, edge, UFL_CLEAR))
    cx0, cy0 = mm(X0 + x0 - UFL_CLEAR), mm(Y0 + y0 - UFL_CLEAR)
    clear = pcbnew.BOX2I(pcbnew.VECTOR2I(cx0, cy0),
                         pcbnew.VECTOR2L(mm(x1 - x0 + 2 * UFL_CLEAR), mm(y1 - y0 + 2 * UFL_CLEAR)))
    hits = []
    for fp in board.GetFootprints():
        if fp.GetReference() == "U1":
            continue
        bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else fp.GetBoundingBox(False)
        if bb.Intersects(clear):
            hits.append(fp.GetReference())
    if hits:
        raise RuntimeError("inside the %.0f mm U.FL clearance: %s" % (UFL_CLEAR, ", ".join(sorted(hits))))
    print("U.FL socket centre x=%.2f y=%.2f mm (board origin), %.1f mm from the %s edge"
          % ((x0 + x1) / 2, (y0 + y1) / 2, dist, edge))


def rules():
    ds = board.GetDesignSettings()
    ds.m_MinClearance = mm(0.127)
    ds.m_TrackMinWidth = mm(0.127)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(mm(0.15))
    nc.SetTrackWidth(mm(0.2))


def refill():
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


step("place parts", place)
step("U1 U.FL socket at an edge, 3 mm clear", check_ufl)
step("clearance rules 0.127 / 0.15 mm", rules)
step("refill zones", refill)
if HEADLESS:
    step("save " + BOARD_PATH, lambda: pcbnew.SaveBoard(BOARD_PATH, board))
else:
    pcbnew.Refresh()
print("\n".join(report))
if HEADLESS:
    if any(r.startswith("FAIL") for r in report):
        sys.exit(1)
else:
    print("Next: Inspect > Design Rules Checker > Run DRC.")
