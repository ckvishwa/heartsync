"""HeartSync shell net rev F: 185 x 72.5 x 32.8, 3.12in SSD1322 bare panel, 1:1 (mm).
Model axes: X = length (+X right end), Y = width (+Y TOP edge), Z = thickness (+Z FRONT).
Z = 0 is the lid's inner face; back outer face Z = -3.0, front outer face Z = 29.8."""
import math

M = 16.0
L, W, T = 185.0, 72.5, 32.8
ZF, ZB = 29.8, -3.0
FX0, FX1 = M + T, M + T + L
TY0, TY1 = M + 10, M + 10 + T          # top strip (10 mm title band above)
FY0, FY1 = TY1, TY1 + W                # front
BY0, BY1 = FY1, FY1 + T                # bottom strip
KY0, KY1 = BY1, BY1 + W                # back
VW = 2 * M + 2 * T + L

def d(z): return ZF - z
def fx(X): return FX0 + X + L / 2
def front(X, Y): return fx(X), FY0 + W / 2 - Y
def back(X, Y): return fx(X), KY0 + Y + W / 2      # back seen from behind after unfolding down
def top(X, z): return fx(X), TY1 - d(z)
def bot(X, z): return fx(X), BY0 + d(z)
def lend(Y, z): return FX0 - d(z), FY0 + W / 2 - Y
def rend(Y, z): return FX1 + d(z), FY0 + W / 2 - Y

o = []
CUT = 'fill="none" stroke="#111" stroke-width="0.35"'
HOLE = 'fill="#111" stroke="#111" stroke-width="0.2"'
FOLD = 'fill="none" stroke="#5F5E5A" stroke-width="0.3" stroke-dasharray="2 1.2"'
ENGR = 'fill="none" stroke="#534AB7" stroke-width="0.35"'
INS = 'fill="none" stroke="#D85A30" stroke-width="0.3" stroke-dasharray="0.8 0.8"'
PH = 'fill="none" stroke="#185FA5" stroke-width="0.35" stroke-dasharray="3 1.5"'
WARN = '#A32D2D'


def rect(x0, y0, x1, y1, st, rx=0):
    x0, x1 = min(x0, x1), max(x0, x1); y0, y1 = min(y0, y1), max(y0, y1)
    r = f' rx="{rx}"' if rx else ''
    o.append(f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{x1-x0:.2f}" height="{y1-y0:.2f}"{r} {st}/>')
def circ(c, r, st): o.append(f'<circle cx="{c[0]:.2f}" cy="{c[1]:.2f}" r="{r:.2f}" {st}/>')
def line(a, b, st): o.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" {st}/>')
def text(p, s, size=2.4, anchor="middle", col="#2C2C2A", weight=400, rot=0):
    tr = f' transform="rotate({rot} {p[0]:.2f} {p[1]:.2f})"' if rot else ''
    o.append(f'<text x="{p[0]:.2f}" y="{p[1]:.2f}" font-size="{size}" text-anchor="{anchor}" fill="{col}" '
             f'font-weight="{weight}" font-family="IBM Plex Sans, Arial, sans-serif"{tr}>{s}</text>')
def tag(p, n, col="#D85A30"):
    circ(p, 1.9, f'fill="#fff" stroke="{col}" stroke-width="0.3"')
    text((p[0], p[1] + 0.85), str(n), 2.2, col=col, weight=600)
def tab(a, b, out):
    ox, oy = out; h = 7.0; k = 5.0
    ux, uy = b[0] - a[0], b[1] - a[1]; n = math.hypot(ux, uy); ux, uy = ux / n, uy / n
    p = [a, (a[0] + ox * h + ux * k, a[1] + oy * h + uy * k), (b[0] + ox * h - ux * k, b[1] + oy * h - uy * k), b]
    o.append('<polygon points="' + ' '.join(f'{x:.2f},{y:.2f}' for x, y in p) + '" fill="#E1F5EE" stroke="#111" stroke-width="0.35"/>')
def rrect_path(cx, cy, hx, hy, r):     # in screen coords, centre + half sizes
    return (f'M{cx-hx+r:.2f},{cy-hy:.2f} h{2*hx-2*r:.2f} a{r},{r} 0 0 1 {r},{r} v{2*hy-2*r:.2f} '
            f'a{r},{r} 0 0 1 {-r},{r} h{-(2*hx-2*r):.2f} a{r},{r} 0 0 1 {-r},{-r} v{-(2*hy-2*r):.2f} '
            f'a{r},{r} 0 0 1 {r},{-r} z')

# ---------------- faces + outline ----------------
FAB, PET = 'fill="#EADFCB"', 'fill="#F6F4EE"'
for (x0, y0, x1, y1), f in (((FX0, TY0, FX1, TY1), FAB), ((FX0, FY0, FX1, FY1), FAB), ((FX0, BY0, FX1, BY1), PET),
                            ((FX0, KY0, FX1, KY1), PET), ((FX0 - T, FY0, FX0, FY1), PET), ((FX1, FY0, FX1 + T, FY1), PET)):
    rect(x0, y0, x1, y1, f)
tab((FX0, TY0), (FX0, TY1), (-1, 0)); tab((FX1, TY1), (FX1, TY0), (1, 0))
tab((FX0, BY1), (FX0, BY0), (-1, 0)); tab((FX1, BY0), (FX1, BY1), (1, 0))
tab((FX0, KY1), (FX0, KY0), (-1, 0)); tab((FX1, KY0), (FX1, KY1), (1, 0))
tab((FX1, KY1), (FX0, KY1), (0, 1))
pts = [(FX0, TY0), (FX1, TY0), (FX1, FY0), (FX1 + T, FY0), (FX1 + T, FY1), (FX1, FY1), (FX1, KY1), (FX0, KY1),
       (FX0, FY1), (FX0 - T, FY1), (FX0 - T, FY0), (FX0, FY0)]
o.append('<polygon points="' + ' '.join(f'{x:.2f},{y:.2f}' for x, y in pts) + f'" {CUT}/>')
for a, b in (((FX0, FY0), (FX1, FY0)), ((FX0, FY1), (FX1, FY1)), ((FX0, BY1), (FX1, BY1)),
             ((FX0, FY0), (FX0, FY1)), ((FX1, FY0), (FX1, FY1))):
    line(a, b, FOLD)

# ---------------- FRONT (outside view) ----------------
# 3.12in bare panel 88 x 27.8 at X -76..12, Y -9.9..17.9 (inside); window 79.8 x 22.2 centred X -32, Y 4
rect(*front(-90.0, 17.9), *front(-2.0, -9.9), INS)
rect(*front(-86.9, 16.1), *front(-5.1, -8.1), ENGR)                      # lens pocket / tuck groove
rect(*front(-85.9, 15.1), *front(-6.1, -7.1), CUT)                       # window through
text(front(-46, 7.2), 'DISPLAY WINDOW 79.8 x 22.2 (through)', 3.0, weight=600)
text(front(-46, 3.6), '3.12in SSD1322 256x64 bare panel behind (88 x 27.8, dotted)', 2.0, col="#993C1D")
text(front(-46, 0.8), 'smoked PC lens 1.0 mm in an 81.8 x 24.2 pocket (purple), foam gasket round it', 2.0, col="#534AB7")
text(front(-46, -2.0), 'fabric tucks 1 mm into the groove; window centre X -46, Y +4', 2.0, col="#444441")
tag(front(-88.5, 12), 7)
rect(*front(-64, 30.5), *front(-24, 25.5), ENGR)
text(front(-44, 22.0), 'touch strip under the fabric, 40 x 5, 1.2 mm wall', 1.9, col="#534AB7"); tag(front(-21, 28), 16)
circ(front(-74.0, 29.5), 0.5, HOLE); text(front(-74.0, 32.4), 'mic 1.0', 1.7, weight=500); tag(front(-78.5, 29.5), 14)
circ(front(-69.5, 29.5), 1.0, HOLE); text(front(-68.5, 25.4), 'light 2.0', 1.7, weight=500); tag(front(-66.6, 32.6), 15)
# GNSS (moved right, clears speaker L by 3 mm)
rect(*front(-72, -21.0), *front(-56, -34.0), INS)
rect(*front(-70, -21.5), *front(-58, -33.5), 'fill="#FAECE7" stroke="#D85A30" stroke-width="0.3"')
text(front(-64, -26.4), 'GPS patch', 1.9, col="#993C1D", weight=600); text(front(-64, -29.0), '12x12 face-up', 1.6, col="#993C1D")
tag(front(-64, -17.5), 6)
# Wi-Fi FlexPIFA (shifted right 7 mm)
rect(*front(-52.0, -22.05), *front(-11.9, -33.05), 'fill="#FAEEDA" stroke="#BA7517" stroke-width="0.3" stroke-dasharray="0.8 0.8"')
text(front(-32, -26.6), 'Wi-Fi FlexPIFA, foam side to the wall', 1.9, col="#854F0B", weight=600)
text(front(-32, -29.4), 'cable end at LEFT (-X), 12 mm from the panel', 1.6, col="#854F0B")
tag(front(-32, -17.5), 3)
# Qi ring and coil
circ(front(45, 0), 28.0, ENGR); circ(front(45, 0), 27.0, ENGR)
circ(front(45, 0), 25.0, INS); circ(front(45, 0), 22.0, INS)
text(front(45, 8.5), 'Qi RING', 3.4, weight=600, col="#534AB7")
text(front(45, 4.8), 'raised 0.4 mm under the fabric, OD 56 / ID 54', 1.9, col="#534AB7")
text(front(45, 1.6), 'magnet ring 56/44 + 50 mm coil behind', 1.9, col="#993C1D")
text(front(45, -1.4), 'the 2.2 mm front wall (dotted)', 1.9, col="#993C1D")
text(front(45, -5.0), 'centre X +45, Y 0; 2 mm clear of speaker R', 1.8, col="#444441")
tag(front(45, -12), 12)
rect(*front(6.5, 36.25), *front(83.5, -36.25), PH)
text(front(8.0, 33.4), 'phone (77 wide, upright) covers X 6.5..83.5', 1.8, anchor="start", col="#185FA5")
text(front(8.0, -34.3), 'the window ends 12.6 mm before any phone', 1.6, anchor="start", col="#185FA5")
text(front(-89.5, -15.5), 'FRONT', 4.0, anchor='start', weight=600)
text(front(-89.5, -19.2), '185 x 72.5, fabric', 2.0, anchor='start', col="#444441")

# ---------------- TOP edge ----------------
text((fx(0), TY0 - 3.0), 'TOP EDGE: 185 x 32.8, fabric (seen from above, front edge at the bottom)', 2.4, weight=600)
BZ = 19.7
cyb = top(0, BZ)[1]
rect(fx(-74.2), cyb - 4.6, fx(-22.6), cyb + 4.6, 'fill="#2C2C2A" fill-opacity="0.12" stroke="#534AB7" stroke-width="0.4"', rx=3)
IC = 'fill="none" stroke="#2C2C2A" stroke-width="0.45" stroke-linecap="round"'
for i, name in enumerate(("MUTE", "PWR", "VOL-", "VOL+", "PLAY")):
    X = -68.0 + 9.8 * i; cx = fx(X)
    if name == "MUTE":
        rect(cx - 0.8, cyb - 1.8, cx + 0.8, cyb + 0.6, IC, rx=0.8); line((cx - 1.6, cyb + 1.6), (cx + 1.6, cyb - 1.6), IC)
    elif name == "PWR":
        o.append(f'<path d="M{cx-1.1:.2f},{cyb-1.0:.2f} A1.6,1.6 0 1 0 {cx+1.1:.2f},{cyb-1.0:.2f}" {IC}/>'); line((cx, cyb - 1.9), (cx, cyb - 0.2), IC)
    elif name == "VOL-":
        line((cx - 1.5, cyb), (cx + 1.5, cyb), IC)
    elif name == "VOL+":
        line((cx - 1.5, cyb), (cx + 1.5, cyb), IC); line((cx, cyb - 1.5), (cx, cyb + 1.5), IC)
    else:
        o.append(f'<path d="M{cx-1.6:.2f},{cyb-1.4:.2f} L{cx+0.2:.2f},{cyb:.2f} L{cx-1.6:.2f},{cyb+1.4:.2f} Z" {IC}/>'); line((cx + 0.9, cyb - 1.3), (cx + 0.9, cyb + 1.3), IC); line((cx + 1.7, cyb - 1.3), (cx + 1.7, cyb + 1.3), IC)
    text((cx, cyb + 7.2), name, 1.4, weight=600)
tag((fx(-48.4), top(0, 8)[1]), 17)
text((fx(-48.4), top(0, 8)[1] + 4.2), 'FLUSH button strip 51.6 x 9.2 (TPU, like a JBL): no caps sticking up,', 1.5)
text((fx(-48.4), top(0, 8)[1] + 6.2), 'raised 0.6 mm icons to find them by touch · 5 x PTS645 under it, 9.8 pitch', 1.5)
for XC in (52.75, 66.05):
    rect(*top(XC - 5.4, 16.05 + 2.1), *top(XC + 5.4, 16.05 - 2.1), CUT, rx=2.0)
rect(*top(38.5 - 6.85, 16.6 + 3.15), *top(38.5 + 6.85, 16.6 - 3.15), CUT, rx=0.6)
text((fx(38.5), top(0, 22.6)[1]), 'USB-A 13.7 x 6.3', 1.7, weight=600)
tag((fx(38.5), top(0, 8)[1]), 28)
text((fx(59.4), top(0, 22.6)[1]), '2 x USB-C 10.8 x 4.2', 1.7, weight=600)
text((fx(52.5), top(0, 25.4)[1]), 'centres X +38.5 / +52.75 / +66.05, 2.5 mm apart, Z 16', 1.5, col="#444441")
tag((fx(59.4), top(0, 8)[1]), 11)
rect(*top(-20, 27.3), *top(22, 11.9), 'fill="#FAEEDA" stroke="#BA7517" stroke-width="0.3" stroke-dasharray="0.8 0.8"')
text((fx(1), top(0, 21)[1]), 'LTE flex (inside, taped to the wall)', 1.8, col="#854F0B", weight=600)
text((fx(1), top(0, 17.6)[1]), 'X -20..+22; 9.6 mm from USB-A', 1.6, col="#854F0B")
tag((fx(26), top(0, 19.6)[1]), 4)

# ---------------- BOTTOM edge (dock) ----------------
text((fx(-40), BY1 - 3.0), 'BOTTOM EDGE: stands on the dock, bare PETG', 2.4, weight=600)
for X in (-12, -4, 4, 12):
    circ(bot(X, 13.8), 1.35, HOLE)
text((fx(0), bot(0, 13.8)[1] - 3.0), '4 pogo pads 2.7 (8 mm apart)', 1.8, weight=500); tag((fx(18), bot(0, 13.8)[1]), 20)
for X in (-70, -32, 32, 70):
    circ(bot(X, 7.0), 3.1, INS)
text((fx(-45), bot(0, 7.0)[1] - 4.2), 'magnets 6 x 2 (inside, 1.6 skin)', 1.6, col="#993C1D"); tag((fx(-78), bot(0, 7)[1]), 21)
rect(*bot(20.5, 27.6), *bot(25.5, 14.5), INS)
text((fx(27), bot(0, 23)[1]), 'haptic fin', 1.6, anchor="start", col="#993C1D"); tag((fx(38), bot(0, 20)[1]), 19)

# ---------------- BACK (seen from behind) ----------------
RUB = 'fill="#444441" fill-opacity="0.35" stroke="#534AB7" stroke-width="0.35"'
cx, cy = back(0, 0)
o.append(f'<path d="{rrect_path(cx, cy, 90.0, 33.75, 6.0)} {rrect_path(cx, cy, 86.0, 29.75, 2.0)}" fill-rule="evenodd" {RUB}/>')
for X, Y in ((-80, 31.7), (80, 31.7), (-80, -31.7), (80, -31.7)):
    circ(back(X, Y), 1.2, 'fill="#fff" stroke="#111" stroke-width="0.3"')
text(back(0, -25.0), 'TPU RING: 4 wide, 2.5 in from the edge, R6 corners, 1.5 proud', 2.1, col="#534AB7", weight=600)
text(back(0, -22.0), 'press-fit in a 1.0 mm channel; it hides the 4 lid screws (white circles)', 1.8, col="#534AB7")
tag(back(-84, 31.75 - 0.2), 22)
bx, by = -67.5, -21.5
gx, gy = back(bx, by)
o.append(f'<g transform="rotate(180 {gx:.2f} {gy:.2f})"><text x="{gx:.2f}" y="{gy + 2.2:.2f}" font-size="6.5" text-anchor="middle" '
         f'fill="#2C2C2A" font-weight="600" font-family="IBM Plex Sans, Arial, sans-serif">Rexi</text></g>')
text(back(-67.5, -12.6), '"Rexi" engraved 0.3 mm, 6.5 mm letters', 1.7, col="#534AB7")
text(back(0, 14), 'BACK: 185 x 72.5, bare PETG lid (3.0 mm)', 3.0, weight=600)
text(back(0, 10.4), 'the device lies on the ring when in use', 2.0, col="#444441")

# ---------------- ENDS: Marshall-inspired grille ----------------
GOLD = 'fill="none" stroke="#B8902F" stroke-width="0.9"'
n_holes = 0
for side, F in ((-1, lend), (1, rend)):
    ecx = (F(0, ZF)[0] + F(0, ZB)[0]) / 2
    text((ecx, FY0 - 1.2), 'LEFT END' if side < 0 else 'RIGHT END', 2.4, weight=600)
    rect(*F(30.4, 27.4), *F(-30.4, 0.6), GOLD, rx=1.5)
    rect(*F(29.2, 26.8), *F(-29.2, 1.2), 'fill="#1A1A1A" fill-opacity="0.08" stroke="#D85A30" stroke-width="0.3"')
    rect(*F(28.75, 23.3), *F(-28.75, 0.3), 'fill="none" stroke="#993C1D" stroke-width="0.3" stroke-dasharray="1.5 0.8"')
    k = 0
    for i in range(23):
        yc = (i - 11) * 2.5
        for j in range(10):
            zc = 2.5 + j * 2.5
            circ(F(yc, zc), 0.8, 'fill="#111"'); k += 1
    n_holes = k
    tag((ecx, FY1 + 3.5), 9 if side < 0 else 10)
    for ii, (t, c) in enumerate((('%d round holes Ø1.6, all through' % k, '#2C2C2A'), ('2.5 square grid, 0.9 webs', '#2C2C2A'),
                                 ('gold trim 0.6 proud (brass-tone)', '#B8902F'), ('ePTFE 58.4 x 25.6 (solid)', '#D85A30'),
                                 ('speaker behind (dash)', '#993C1D'), ('front edge = front-panel side', '#5F5E5A'))):
        text((ecx, FY1 + 8.0 + ii * 2.5), t, 1.6, col=c)
    sx = F(0, ZF)[0]
    text((sx + (-1.2 if side < 0 else 1.2), FY0 + 6), 'front', 1.5, col="#5F5E5A", rot=-90 if side < 0 else 90)

# ---------------- title, scale, legend ----------------
text((M, M), 'Rexi shell net, rev F, 1:1', 3.4, anchor="start", weight=600)
text((M, M + 4.2), '185 x 72.5 x 32.8 · 3.12in panel · 2 x USB-C + USB-A · 20 Nov 2026 · print at 100 % on A3', 2.2, anchor="start", col="#5F5E5A")
sy = KY1 + 10
rect(M, sy, M + 50, sy + 2, 'fill="#111"')
for i in range(6): line((M + 10 * i, sy - 1), (M + 10 * i, sy + 3), 'stroke="#111" stroke-width="0.25"')
text((M, sy + 7), '50 mm: measure this after printing', 2.3, anchor="start")
legend = [("#111", "solid", "hole / cut through the wall"), ("#5F5E5A", "dash", "fold line"),
          ("#534AB7", "solid", "groove, pocket, raised ring, engraving"), ("#D85A30", "dot", "part inside (fit reference)"),
          ("#185FA5", "dash", "phone footprint"), ("#EADFCB", "sw", "fabric"), ("#F6F4EE", "sw", "bare PETG")]
for i, (c, kind, s) in enumerate(legend):
    x = M + 70 + (i // 4) * 80; y = sy + 1 + (i % 4) * 4.2
    if kind == "sw": rect(x, y - 2.2, x + 7, y + 0.6, f'fill="{c}" stroke="#888780" stroke-width="0.2"')
    else: line((x, y - 0.8), (x + 7, y - 0.8), f'stroke="{c}" stroke-width="0.5"' +
               (' stroke-dasharray="2 1.2"' if kind == "dash" else ' stroke-dasharray="0.8 0.8"' if kind == "dot" else ''))
    text((x + 9, y), s, 2.2, anchor="start")
text((M + 70, sy + 18.5), 'Numbers in circles = BOM line. Corners drawn square (real R6).', 2.0, anchor="start", col="#5F5E5A")
VH = sy + 24

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{VW:.1f}mm" height="{VH:.1f}mm" viewBox="0 0 {VW:.1f} {VH:.1f}">'
       f'<rect width="{VW:.1f}" height="{VH:.1f}" fill="#fff"/>{"".join(o)}</svg>')
open('heartsync_net_revF.svg', 'w').write(svg)
print(VW, VH, n_holes)
