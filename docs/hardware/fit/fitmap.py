"""HeartSync inside fit map, rev E, 1:1. Plan seen from the FRONT (front wall removed), X right, +Y = TOP edge up.
Then a section along the length at Y = 0, FRONT up. Model coordinates as heartsync_assembly.py, length 157."""
import math

L, W = 157.0, 72.5
WALL, TOPW = 2.2, 2.2
M = 18.0
VW = 254.6
OX = (VW - L) / 2 + L / 2          # screen x of model X = 0
PY0 = 30.0                          # top of plan outline (screen)
PCY = PY0 + W / 2                   # screen y of model Y = 0
def P(X, Y): return OX + X, PCY - Y
def S(X, Z): return OX + X, SY0 + (29.8 - Z)  # SY0 set later

o = []
def rect(a, b, st, rx=0):
    x0, x1 = sorted((a[0], b[0])); y0, y1 = sorted((a[1], b[1]))
    r = f' rx="{rx}"' if rx else ''
    o.append(f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{x1-x0:.2f}" height="{y1-y0:.2f}"{r} {st}/>')
def circ(c, r, st): o.append(f'<circle cx="{c[0]:.2f}" cy="{c[1]:.2f}" r="{r:.2f}" {st}/>')
def line(a, b, st): o.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" {st}/>')
def text(p, s, size=2.0, anchor="middle", col="#2C2C2A", weight=400, rot=0):
    tr = f' transform="rotate({rot} {p[0]:.2f} {p[1]:.2f})"' if rot else ''
    o.append(f'<text x="{p[0]:.2f}" y="{p[1]:.2f}" font-size="{size}" text-anchor="{anchor}" fill="{col}" '
             f'font-weight="{weight}" font-family="IBM Plex Sans, Arial, sans-serif"{tr}>{s}</text>')
def tag(p, n, col):
    circ(p, 1.9, f'fill="#fff" stroke="{col}" stroke-width="0.35"')
    text((p[0], p[1] + 0.85), str(n), 2.2, col=col, weight=600)
def box(X0, Y0, X1, Y1, fill, stroke, op=0.55, dash=False, f=P, rx=0):
    st = f'fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="0.35"' + (' stroke-dasharray="1 0.8"' if dash else '')
    rect(f(X0, Y0), f(X1, Y1), st, rx)

# layer colours: A back (cell) blue, B board layer green, C front-wall layer amber/purple, D walls gray
A = ("#B5D4F4", "#185FA5"); B = ("#C0DD97", "#3B6D11"); C = ("#FAC775", "#854F0B"); RF = ("#F7C1C1", "#A32D2D")
D = ("#D3D1C7", "#444441"); Q = ("#CECBF6", "#534AB7")

text((M, 12), 'HeartSync inside fit map, rev E (157 mm), 1:1', 3.4, anchor="start", weight=600)
text((M, 16.4), 'Seen from the FRONT with the front wall lifted off. Top edge up, left end left. '
     'Numbers = BOM lines. Fit in the order A → B → C → D.', 2.1, anchor="start", col="#5F5E5A")
text((M, 20.4), 'Not yet confirmed by the CAD fit check (the 157 / 3.12 rebuild is pending): dry-fit and tape, no glue.', 2.1, anchor="start", col="#A32D2D")

VIEWS = [("A", "LAYER A: on the lid (fit first)", "cell, foam pad, insulator; lid screws + inserts in the corners"),
         ("B", "LAYER B: board layer, Z 13.7 (fit second)", "carrier on the bracket (H1/H2) + bosses (H3/H4); SIM, power and Qi driver boards; plug every cable now"),
         ("C", "LAYER C: on the inside of the front wall (fit last, then close)", "display, lens, Qi coil, Wi-Fi + GPS antennas, touch strip, mic/light board")]
PH = W + 30
def plan(view, y0):
    global PCY
    PCY = y0 + W / 2
    # shell outline + inner walls
    rect(P(-L / 2, W / 2), P(L / 2, -W / 2), 'fill="#FBFAF7" stroke="#111" stroke-width="0.45"', rx=6)
    rect(P(-L / 2 + WALL, W / 2 - TOPW), P(L / 2 - WALL, -W / 2 + TOPW), 'fill="none" stroke="#888780" stroke-width="0.25"', rx=4)
    for X, Y in ((-66, 31.7), (66, 31.7), (-66, -31.7), (66, -31.7)):
        circ(P(X, Y), 2.8, 'fill="#D3D1C7" stroke="#444441" stroke-width="0.3"'); circ(P(X, Y), 1.6, 'fill="#fff" stroke="#444441" stroke-width="0.25"')
    tag(P(-66, 40.2), 23, D[1])

    # ---- D: walls ----
    for sx in (-1, 1):
        x0, x1 = (-76.1, -61.25) if sx < 0 else (61.25, 76.1)
        box(x0, 28.75, x1, -28.75, D[0], D[1], 0.8)
        cx = (x0 + x1) / 2
        text(P(cx, 4), 'SPEAKER ' + ('L' if sx < 0 else 'R'), 1.9, col="#2C2C2A", weight=600, rot=-90)
        text(P(cx + 2.6, 4), 'face to the end wall', 1.4, col="#2C2C2A", rot=-90)
        rc = x1 if sx < 0 else x0
        rect(P(rc, 28.75), P(rc + (1.5 if sx < 0 else -1.5), -28.75), 'fill="#888780"')
        rect(P(sx * 76.3, 29.2), P(sx * 76.1, -29.2), 'fill="#D85A30"')
        tag(P(cx, -24), 9 if sx < 0 else 10, D[1])
    text(P(-56, 25.0), 'cradle', 1.3, col="#444441")
    for i in range(5):
        X = -54.0 + 9.8 * i
        rect(P(X - 3.1, 34.05), P(X + 3.1, 28.6), 'fill="#2C2C2A" fill-opacity="0.85" stroke="none"', rx=0.6)
    tag(P(-34.4, 40.2), 17, D[1])
    box(-6, 34.05, 36, 33.25, RF[0], RF[1], 0.9)
    text(P(15, 31.3), 'LTE flex on the top wall (RF) · cable → SIM board', 1.5, col=RF[1], weight=600)
    tag(P(15, 40.2), 4, RF[1])
    for X in (-12, -4, 4, 12):
        circ(P(X, -34.8), 1.25, 'fill="#C9A227" stroke="#444441" stroke-width="0.2"')
    tag(P(0, -40.4), 20, D[1])
    for X in (-58, -32, 32, 58):
        rect(P(X - 3, -33.0), P(X + 3, -34.05), 'fill="#5F5E5A"')
    tag(P(32, -40.4), 21, D[1])
    circ(P(22.25, -29), 3.5, 'fill="#D3D1C7" stroke="#444441" stroke-width="0.3"'); tag(P(27.4, -26.5), 19, D[1])
    text(P(-77.6, 0), 'LEFT END', 2.0, col="#5F5E5A", weight=600, rot=-90)
    text(P(79.6, 0), 'RIGHT END', 2.0, col="#5F5E5A", weight=600, rot=90)
    text(P(78.5, 38.6), 'TOP EDGE: buttons · LTE · USB-C', 2.0, anchor='end', col="#5F5E5A", weight=600)
    text(P(78.5, -39.6), 'BOTTOM EDGE: pogo pads + dock magnets', 2.0, anchor='end', col="#5F5E5A", weight=600)

    if view == 'A':
        # ---- A: cell (back layer) ----
        box(-54.5, 30.25, 46.5, -30.25, A[0], A[1], 0.35)
        text(P(-4, -5.5), 'A  CELL LP1160100, 101 x 60.5 x 11.3 (max), on the lid', 2.4, col=A[1], weight=600)
        text(P(-4, -8.6), '1 mm foam under, 0.2 insulator + 1.2 mm swell gap above. PCM end at +X. NTC + JST lead to the power board', 1.8, col=A[1])
        tag(P(-50, -27), 13, A[1])
    if view == 'B':
        # ---- B: board layer Z 13.7 ----
        box(-36, 30, 34, -15, B[0], B[1], 0.6)
        text(P(-1, 3.0), 'B  CARRIER 70 x 45', 2.4, col=B[1], weight=600)
        text(P(-1, 0.0), 'component side to the front, sits on the bracket (H1/H2) + bosses (H3/H4)', 1.6, col=B[1])
        tag(P(31, -12.5), 1, B[1])
        box(-28, 29.5, -10, 10.3, "#2C2C2A", "#2C2C2A", 0.85)
        text(P(-19, 21.5), 'ESP32-S3', 2.0, col="#fff", weight=600); text(P(-19, 18.6), 'WROOM-1U', 2.0, col="#fff", weight=600)
        circ(P(-13, 27.04), 0.9, 'fill="#E24B4A" stroke="#fff" stroke-width="0.2"')
        text(P(-19, 13.4), 'U.FL at top edge', 1.6, col="#fff")
        tag(P(-7.5, 12.0), 2, B[1])
        for n, (X, Y) in {"H1": (-33, 21), "H2": (-33, 4), "H3": (9.5, 16), "H4": (12.5, -12)}.items():
            circ(P(X, Y), 1.1, 'fill="#fff" stroke="#3B6D11" stroke-width="0.3"'); text(P(X + 2, Y - 0.7), n, 1.5, anchor="start", col=B[1])
        for n, (X, Y), lab in (("J1", (30, 14.25), "power"), ("J2", (30, -11), "cell sense"), ("J3", (30, 24.75), "SIM"),
                               ("J4", (-32.25, 12.5), "spk L"), ("J5", (30.25, -0.25), "spk R"), ("J6", (10.5, -5.9), "haptic"),
                               ("J7", (15.55, 18.7), "touch"), ("J8", (9, 26.25), "mic"), ("J9", (16.6, 26.25), "mute"),
                               ("J10", (-7, -11.25), "light"), ("J11", (-17.5, -11.25), "display"), ("J12", (1, -11.25), "buttons")):
            rect(P(X - 1.6, Y + 1.0), P(X + 1.6, Y - 1.0), 'fill="#F1EFE8" stroke="#3B6D11" stroke-width="0.25"')
            text(P(X, Y - 0.55), n, 1.2, col="#173404", weight=600)
            text(P(X + (2.2 if X < 28 else -2.2), Y - 0.55), lab, 1.3, anchor="start" if X < 28 else "end", col="#27500A")
        box(-58.25, -15.5, -26.25, -33, B[0], B[1], 0.6)
        text(P(-42.25, -20.2), 'SIM7080G board 32 x 17.5', 1.8, col=B[1], weight=600)
        text(P(-42.25, -22.8), '+ nano-SIM (rev B: onto the carrier)', 1.5, col=B[1])
        tag(P(-55.5, -18.2), 5, B[1])
        box(37, 32.5, 60.8, 8, B[0], B[1], 0.6)
        text(P(48.9, 17), 'POWER board', 1.9, col=B[1], weight=600); text(P(48.9, 14.4), 'IP5328P, 23.8 x 24.5', 1.6, col=B[1])
        text(P(48.9, 11.8), 'hot parts past X 47', 1.5, col="#A32D2D")
        tag(P(39.5, 10.5), 18, B[1])
        box(53.5, -2, 55.1, -32, B[0], B[1], 0.9)
        text(P(52.6, -17), 'Qi driver (vertical, 30 x 20)', 1.5, col=B[1], rot=-90)
        # USB-C on the power board, in the top wall
        box(46.9, 36.25, 57.1, 28.4, "#2C2C2A", "#2C2C2A", 0.85)
        text(P(52, 31.6), 'USB-C', 1.6, col="#fff", weight=600)
        tag(P(59.3, 31), 11, D[1])
    if view == 'C':
        # ---- C: front-wall layer (Z 22.6..27.6), drawn as outlines ----
        box(-76, 17.9, 12, -9.9, C[0], C[1], 0.45)
        rect(P(-71.9, 15.1), P(7.9, -7.1), 'fill="none" stroke="#854F0B" stroke-width="0.35" stroke-dasharray="2 1"')
        text(P(-32, 9.0), 'C  DISPLAY 3.12in SSD1322, 88 x 27.8 x 2.15', 2.2, col=C[1], weight=600)
        text(P(-32, 6.0), 'glass to the lens, FPC tail at the BOTTOM edge → J11 · foam ring behind', 1.6, col=C[1])
        text(P(-32, 3.4), 'left edge 2.5 mm from the left end · dashed = window', 1.6, col=C[1])
        tag(P(-73.5, 15.3), 7, C[1])
        circ(P(45, 0), 28, 'fill="#CECBF6" fill-opacity="0.35" stroke="#534AB7" stroke-width="0.4"')
        circ(P(45, 0), 22, 'fill="#fff" fill-opacity="0.6" stroke="#534AB7" stroke-width="0.3" stroke-dasharray="1 0.8"')
        circ(P(45, 0), 25, 'fill="none" stroke="#534AB7" stroke-width="0.25" stroke-dasharray="1 0.8"')
        text(P(45, 4.2), 'C  Qi COIL 50 mm', 2.2, col=Q[1], weight=600)
        text(P(45, 1.0), '+ magnet ring 56/44 (outer)', 1.7, col=Q[1])
        text(P(45, -1.8), 'centre X +45, Y 0', 1.7, col=Q[1])
        text(P(45, -4.6), 'ferrite to the front wall', 1.7, col=Q[1])
        tag(P(45, -8.5), 12, Q[1])
        box(-38, -22.05, 2.1, -33.05, RF[0], RF[1], 0.6)
        text(P(-18, -26.0), 'C  Wi-Fi FlexPIFA 40 x 11 (RF)', 1.9, col=RF[1], weight=600)
        text(P(-18, -28.7), 'foam side taped to the front wall · cable end LEFT', 1.5, col=RF[1])
        text(P(-18, -31.1), 'coax → U.FL on the module, bend radius ≥ 6', 1.5, col=RF[1])
        tag(P(4.8, -27.5), 3, RF[1])
        o.append(f'<path d="M{P(-37, -24)[0]:.2f},{P(-37, -24)[1]:.2f} C{P(-40, -10)[0]:.2f},{P(-40, -10)[1]:.2f} '
                 f'{P(-32, 22)[0]:.2f},{P(-32, 22)[1]:.2f} {P(-13, 27.04)[0]:.2f},{P(-13, 27.04)[1]:.2f}" fill="none" stroke="#A32D2D" '
                 f'stroke-width="0.45" stroke-dasharray="1.6 0.8"/>')
        box(-58, -21, -42, -34, RF[0], RF[1], 0.6)
        rect(P(-56, -21.5), P(-44, -33.5), 'fill="none" stroke="#A32D2D" stroke-width="0.3"')
        text(P(-50, -26.4), 'GPS patch', 1.7, col=RF[1], weight=600); text(P(-50, -28.8), 'face to the front', 1.4, col=RF[1])
        tag(P(-60.2, -27.5), 6, RF[1])
        box(-50, 30.5, -10, 25.5, C[0], C[1], 0.45)
        text(P(-30, 27.3), 'touch strip 40 x 5 → J7', 1.6, col=C[1], weight=600); tag(P(-7.6, 28), 16, C[1])
        box(-62.5, 33, -52.5, 26, C[0], C[1], 0.45)
        circ(P(-60, 29.5), 0.6, 'fill="#2C2C2A"'); circ(P(-55.5, 29.5), 1.0, 'fill="#2C2C2A"')
        text(P(-57.5, 27.0), 'mic+light', 1.2, col=C[1], weight=600)
        tag(P(-60, 23.0), 14, C[1]); tag(P(-55, 23.0), 15, C[1])
for i, (v, t1, t2) in enumerate(VIEWS):
    y0 = PY0 + 8 + i * PH
    text((M, y0 - 5.5), t1, 2.8, anchor="start", weight=600)
    text((M, y0 - 2.0), t2, 1.9, anchor="start", col="#5F5E5A")
    plan(v, y0)
SY0 = PY0 + 8 + 3 * PH + 8
# ---------------- SECTION along the length (Y = 0), FRONT up ----------------
text((M, SY0 - 9), 'SIDE VIEW along the length, every part projected (FRONT up, back down), 1:1', 2.8, anchor="start", weight=600)
rect(S(-78.5, 29.8), S(78.5, 27.6), 'fill="#EADFCB" stroke="#444441" stroke-width="0.3"')            # front wall
rect(S(-78.5, 30.4), S(78.5, 29.8), 'fill="#C9B79C"')                                               # fabric
rect(S(-78.5, 0), S(78.5, -3.0), 'fill="#F6F4EE" stroke="#444441" stroke-width="0.3"')              # lid
rect(S(-76.0, -3.0), S(76.0, -4.5), 'fill="#444441"')                                               # ring proud
for sx in (-1, 1):
    rect(S(sx * 78.5, 27.6), S(sx * 76.3, 0), 'fill="#F6F4EE" stroke="#444441" stroke-width="0.3"')
    x0, x1 = (-76.1, -61.25) if sx < 0 else (61.25, 76.1)
    box(x0, 23.3, x1, 0.3, D[0], D[1], 0.85, f=S)
    text(S((x0 + x1) / 2, 12), 'spk ' + ('L' if sx < 0 else 'R'), 1.7, weight=600)
box(-54.5, 12.3, 46.5, 1.0, A[0], A[1], 0.6, f=S)
text(S(-4, 6.0), 'A  cell 11.3 (Z 1.0..12.3)', 2.0, col=A[1], weight=600)
rect(S(-54.5, 1.0), S(46.5, 0), 'fill="#888780"'); rect(S(-54.5, 12.5), S(46.5, 12.3), 'fill="#EF9F27"')
text(S(-53.5, 13.0), 'swell gap 1.2', 1.3, anchor="start", col="#A32D2D")
box(-36, 15.3, 34, 13.7, B[0], B[1], 0.9, f=S)
box(-28, 18.5, -10, 15.3, "#2C2C2A", "#2C2C2A", 0.85, f=S)
text(S(-19, 20.2), 'ESP32 module', 1.5, col="#2C2C2A")
text(S(0, 16.6), 'B  carrier Z 13.7', 1.6, col=B[1], weight=600)
box(37, 15.3, 60.8, 13.7, B[0], B[1], 0.9, f=S); text(S(49, 16.6), 'power', 1.5, col=B[1])
box(53.5, 22, 55.1, 2, B[0], B[1], 0.9, f=S)
box(-76, 27.6, 12, 25.45, C[0], C[1], 0.8, f=S); rect(S(-76, 25.45), S(12, 24.45), 'fill="#5F5E5A" fill-opacity="0.5"')
text(S(-32, 23.0), 'C  panel 2.15 + foam 1.0 (Z 24.45..27.6)', 1.6, col=C[1], weight=600)
rect(S(-72.9, 29.8), S(8.9, 28.8), 'fill="#2C2C2A"'); text(S(-32, 31.5), 'smoked lens 1.0 in the window', 1.5, col="#2C2C2A")
box(20, 27.6, 70, 24.8, Q[0], Q[1], 0.8, f=S)
text(S(45, 23.0), 'C  Qi coil + ferrite (Z 24.8..27.6)', 1.6, col=Q[1], weight=600)
text(S(60, 31.5), 'Qi ring raised 0.4 under fabric', 1.5, col=Q[1])
dims = [(-3.0, 0, 'lid 3.0'), (0, 1.0, 'pad 1.0'), (1.0, 12.3, 'cell 11.3'), (12.3, 13.7, 'gap 1.4'),
        (13.7, 15.3, 'PCB 1.6'), (15.3, 24.45, 'parts ≤ 9'), (24.45, 27.6, 'panel'), (27.6, 29.8, 'wall 2.2')]
for z0, z1, lab in dims:
    a, b = S(81.5, z0), S(81.5, z1)
    line(a, b, 'stroke="#444441" stroke-width="0.25"'); line((a[0] - 0.8, a[1]), (a[0] + 0.8, a[1]), 'stroke="#444441" stroke-width="0.25"')
    text((a[0] + 1.6, (a[1] + b[1]) / 2 + 0.6), lab, 1.4, anchor="start", col="#444441")
text(S(81.5, 33.5), 'stack 34.3 incl. ring', 1.6, anchor="start", weight=600)

# legend
ly = SY0 + 41
for i, ((fc, sc), s) in enumerate(((A, 'A  back layer: cell'), (B, 'B  board layer: carrier, SIM, power, Qi driver'),
                                   (C, 'C  front-wall layer: display, touch, mic/light'), (Q, 'C  Qi coil + magnet ring'),
                                   (RF, 'RF: antennas + GPS (keep metal, cells, cables off them)'), (D, 'D  walls: speakers, buttons, pogo, magnets'))):
    x = M + (i % 3) * 76; y = ly + (i // 3) * 5
    rect((x, y - 2.4), (x + 6, y + 0.6), f'fill="{fc}" stroke="{sc}" stroke-width="0.3"')
    text((x + 8, y), s, 1.9, anchor="start")
VH = ly + 12
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{VW:.1f}mm" height="{VH:.1f}mm" viewBox="0 0 {VW:.1f} {VH:.1f}">'
       f'<rect width="{VW:.1f}" height="{VH:.1f}" fill="#fff"/>{"".join(o)}</svg>')
open('heartsync_fitmap_revE.svg', 'w').write(svg)
print(VW, VH)
