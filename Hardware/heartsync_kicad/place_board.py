"""
heartsync carrier v0.1 - board setup for the KiCad PCB editor (KiCad 8/9/10)

Use AFTER importing heartsync_carrier.net (File > Import > Netlist).
Run in the PCB editor: Tools > Scripting Console, then:
    exec(open(r"D:\\SyncD\\Hardware\\heartsync_kicad\\place_board.py").read())

It does:
  1. draws the 70 x 45 mm board outline (Edge.Cuts)
  2. adds four M2 mounting holes
  3. places every part in its area (connectors on the edges)
  4. adds GND copper pours on both layers and fills them
Then run replace_parts.py: it holds the final positions and checks U1's U.FL socket (ADR 0011).
RUN IT ONCE per import. It refuses to run twice (deleting things from the script corrupts KiCad's Python).
To redo: close the PCB editor without saving, reopen, re-import the netlist, run again.
It does NOT route tracks. Route by hand (or with the Freerouting plugin), then run DRC.
Each step is separate: if one fails, the console says which and the rest still run.
"""
import os
import pcbnew

X0, Y0 = 100.0, 100.0          # board top-left corner in the editor (mm)
W, H = 70.0, 45.0

if not hasattr(pcbnew, "FootprintLoad"):
    raise SystemExit("This console session is broken (pcbnew is not the module). "
                     "Close the scripting console, reopen it (Tools > Scripting Console), run this again.")
board = pcbnew.GetBoard()
report = []

if (any(d.GetLayer() == pcbnew.Edge_Cuts for d in board.GetDrawings())
        or len(board.Zones()) > 0 or board.FindFootprintByReference("H1") is not None):
    raise SystemExit("This board already has an outline, pours or holes: the script already ran. "
                     "Close the PCB editor WITHOUT saving, reopen it, re-import the netlist, run once.")


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(X0 + x), mm(Y0 + y))


def step(name, fn):
    try:
        fn()
        report.append("ok    " + name)
    except Exception as e:  # keep going, report at the end
        report.append("FAIL  %s: %s" % (name, e))


# ------------------------------------------------------------------ 1. outline
def outline():
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetStart(pt(0, 0))
    s.SetEnd(pt(W, H))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(mm(0.1))
    board.Add(s)


# ------------------------------------------------------------------ 2. mounting holes
def holes():
    lib = None
    for var in ("KICAD10_FOOTPRINT_DIR", "KICAD9_FOOTPRINT_DIR", "KICAD8_FOOTPRINT_DIR", "KICAD_FOOTPRINT_DIR"):
        d = os.environ.get(var)
        if d and os.path.isdir(os.path.join(d, "MountingHole.pretty")):
            lib = os.path.join(d, "MountingHole.pretty")
            break
    if not lib:
        raise RuntimeError("footprint folder not found; add 4x MountingHole_2.2mm_M2 by hand")
    for i, (x, y) in enumerate(((3.0, 9.0), (3.0, 26.0), (45.5, 14.0), (48.5, 42.0))):
        fp = pcbnew.FootprintLoad(lib, "MountingHole_2.2mm_M2")
        fp.SetReference("H%d" % (i + 1))
        fp.SetPosition(pt(x, y))
        board.Add(fp)


# ------------------------------------------------------------------ 3. placement
# (ref, x, y, rotation) in mm from the board top-left corner. Passives sit next to their chip.
PLACE = [
    ("U1", 15.5, 12.75, 0), ("U2", 6, 33, 0), ("L1", 11.5, 33, 0), ("C4", 3, 30, 90),
    ("C5", 15.5, 30, 90), ("R3", 6, 36.5, 0), ("R4", 9.5, 36.5, 0), ("C1", 27.5, 22, 90),
    ("C2", 27.5, 18.5, 90), ("R1", 25.5, 27, 0), ("C3", 25.5, 29.5, 0), ("R2", 25.5, 31.5, 0),
    ("SW1", 30.25, 34.75, 0), ("SW2", 39, 34.75, 0), ("J1", 66, 15.75, 90), ("U3", 58.5, 15, 0),
    ("C6", 58.5, 19, 0), ("J3", 66, 5.25, 90), ("U9", 56.5, 4.75, 0), ("C16", 56.5, 8, 0),
    ("C17", 53, 5, 90), ("Q1", 60.5, 9, 0), ("R11", 56.5, 10.5, 0), ("R12", 60.5, 12, 0),
    ("U4", 52, 21.5, 0), ("C7", 47.5, 21.5, 90), ("C8", 52, 18.5, 0), ("R5", 48.5, 25, 0),
    ("U5", 52, 28.5, 0), ("C9", 47.5, 28.5, 90), ("C10", 52, 31.5, 0), ("R6", 48.5, 32, 0),
    ("R7", 49, 33.75, 0), ("J4", 66, 24.25, 90), ("J5", 66.25, 30.25, 90), ("U6", 55, 37, 0),
    ("C11", 55, 40, 0), ("C12", 51.25, 37, 90), ("J6", 46.5, 36.75, 0), ("U8", 59, 42, 0),
    ("C15", 55.5, 42.5, 0), ("J2", 66, 41, 0), ("U7", 36, 24, 0), ("C13", 36, 27, 0),
    ("C14", 39.5, 24, 90), ("R8", 40, 18, 0), ("R9", 40, 20, 0), ("R10", 43.5, 18, 0),
    ("R13", 43.5, 9, 0), ("R14", 43.5, 11, 0), ("C18", 47, 9, 0), ("R15", 30, 30, 0),
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
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
    if missing:
        raise RuntimeError("not on the board (import the netlist first?): " + ", ".join(missing))


# ------------------------------------------------------------------ 4. GND pours
def pours():
    gnd = board.FindNet("GND")
    if gnd is None:
        raise RuntimeError("no GND net (import the netlist first)")
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.SetLocalClearance(mm(0.3))
        z.SetMinThickness(mm(0.25))
        o = z.Outline()
        o.NewOutline()
        for x, y in ((0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, H - 0.3), (0.3, H - 0.3)):
            o.Append(mm(X0 + x), mm(Y0 + y))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


step("board outline 70 x 45 mm", outline)
step("M2 mounting holes", holes)
step("place parts", place)
step("GND pours (both layers)", pours)
pcbnew.Refresh()
print("\n".join(report))
print("Next: route, then Inspect > Design Rules Checker.")
