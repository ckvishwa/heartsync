r"""
heartsync carrier: re-place parts on an EXISTING board (outline and pours already there).

Two ways to run it:
  - PCB editor scripting console (one line):
        exec(open(r"D:\SyncD\Hardware\heartsync_kicad\replace_parts.py").read())
  - Headless, with the board CLOSED in KiCad (it loads, edits and saves the file):
        "C:\Program Files\KiCad\10.0\bin\python.exe" replace_parts.py heartsync_carrier.kicad_pcb

It only moves and rotates parts (safe to run again), snaps U1 so its antenna end is flush with the
board top edge, sets the clearance rules (0.127 mm minimum, 0.15 mm default) and refills the zones.
Check the result with DRC (command in CLAUDE.md): zero courtyard, keepout and hole errors.
"""
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


# H1 sits on the left edge below the U1 antenna keepout (keepout ends at y 6.05; U1 body starts at x 5.75).
PLACE = [
    ("H1", 3, 9, 0),
    ("U1", 15.5, 12.75, 0), ("U2", 6, 33, 0), ("L1", 11.5, 33, 0), ("C4", 2.8, 30.5, 90),
    ("C5", 15.5, 30, 90), ("R3", 6, 36.5, 0), ("R4", 9.5, 36.5, 0), ("C1", 27.5, 22, 90),
    ("C2", 27.5, 18.5, 90), ("R1", 25.5, 27, 0), ("C3", 25.5, 29.5, 0), ("R2", 24.25, 31.5, 0),
    ("SW1", 30.25, 34.75, 0), ("SW2", 39, 34.75, 0), ("J1", 66, 15.75, 90), ("U3", 58.5, 15, 0),
    ("C6", 58.5, 19, 0), ("J3", 66, 5.25, 90), ("U9", 56.5, 4.75, 0), ("C16", 56.3, 8, 90),
    ("C17", 53, 4.5, 90), ("Q1", 60.5, 9, 0), ("R11", 56.5, 10.5, 0), ("R12", 60.5, 12, 0),
    ("U4", 52, 21.5, 0), ("C7", 47.5, 21.5, 90), ("C8", 52, 18.5, 0), ("R5", 48.5, 25, 0),
    ("U5", 52, 28.5, 0), ("C9", 47.5, 28.5, 90), ("C10", 52, 31.5, 0), ("R6", 48.5, 31.6, 0),
    ("R7", 52.5, 33.5, 0), ("J4", 66, 24.25, 90), ("J5", 66.25, 30.25, 90), ("U6", 55, 37, 0),
    ("C11", 55, 40, 0), ("C12", 50.75, 37, 90), ("J6", 46.5, 35.9, 0), ("U8", 59, 42, 0),
    ("C15", 55.5, 42.5, 0), ("J2", 66, 41, 0), ("U7", 36, 24, 0), ("C13", 36, 27, 0),
    ("C14", 39.5, 24, 90), ("R8", 40, 18, 0), ("R9", 40, 20, 0), ("R10", 43.5, 18, 0),
    ("R13", 43.5, 9, 0), ("R14", 42.5, 11, 0), ("C18", 47, 9, 0), ("R15", 30, 30, 0),
    ("R16", 33.5, 30, 0), ("C19", 37, 30, 0), ("J7", 36, 9.5, 180), ("J8", 45, 3.75, 180),
    ("J9", 52.5, 9.5, 180), ("J11", 18.5, 41.25, 0), ("J10", 29, 41.25, 0), ("J12", 37, 41.25, 0),
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


def snap_antenna():
    u1 = board.FindFootprintByReference("U1")
    tops, bots = [], []
    for g in u1.GraphicalItems():
        if g.GetLayer() == pcbnew.F_Fab:
            bb = g.GetBoundingBox()
            tops.append(bb.GetTop())
            bots.append(bb.GetBottom())
    if not tops:
        raise RuntimeError("no F.Fab outline on U1")
    h = pcbnew.ToMM(max(bots) - min(tops))
    if not 24.0 <= h <= 27.0:
        raise RuntimeError("U1 outline %.1f mm tall, expected about 25.5; not moved" % h)
    u1.Move(pcbnew.VECTOR2I(0, mm(Y0) - min(tops)))
    print("U1 origin at x=%.1f y=%.1f mm" % (pcbnew.ToMM(u1.GetPosition().x) - X0,
                                             pcbnew.ToMM(u1.GetPosition().y) - Y0))


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
step("U1 antenna to board edge", snap_antenna)
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
