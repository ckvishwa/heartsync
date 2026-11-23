"""HeartSync shell net rev E: 157 x 72.5 x 32.8, 3.12in SSD1322 bare panel, 1:1 (mm).
Model axes: X = length (+X right end), Y = width (+Y TOP edge), Z = thickness (+Z FRONT).
Z = 0 is the lid's inner face; back outer face Z = -3.0, front outer face Z = 29.8."""
import math

M = 16.0
L, W, T = 157.0, 72.5, 32.8
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
rect(*front(-76.0, 17.9), *front(12.0, -9.9), INS)
rect(*front(-72.9, 16.1), *front(8.9, -8.1), ENGR)                      # lens pocket / tuck groove
rect(*front(-71.9, 15.1), *front(7.9, -7.1), CUT)                       # window through
text(front(-32, 7.2), 'DISPLAY WINDOW 79.8 x 22.2 (through)', 3.0, weight=600)
text(front(-32, 3.6), '3.12in SSD1322 256x64 bare panel behind (88 x 27.8, dotted)', 2.0, col="#993C1D")
text(front(-32, 0.8), 'smoked PC lens 1.0 mm in an 81.8 x 24.2 pocket (purple), foam gasket round it', 2.0, col="#534AB7")
text(front(-32, -2.0), 'fabric tucks 1 mm into the groove; window centre X -32, Y +4', 2.0, col="#444441")
tag(front(-74.5, 12), 7)
rect(*front(-50, 30.5), *front(-10, 25.5), ENGR)
text(front(-30, 22.0), 'touch strip under the fabric, 40 x 5, 1.2 mm wall', 1.9, col="#534AB7"); tag(front(-7, 28), 16)
circ(front(-60.0, 29.5), 0.5, HOLE); text(front(-60.0, 32.4), 'mic 1.0', 1.7, weight=500); tag(front(-64.5, 29.5), 14)
circ(front(-55.5, 29.5), 1.0, HOLE); text(front(-54.5, 25.4), 'light 2.0', 1.7, weight=500); tag(front(-52.6, 32.6), 15)
# GNSS (moved right, clears speaker L by 3 mm)
rect(*front(-58, -21.0), *front(-42, -34.0), INS)
rect(*front(-56, -21.5), *front(-44, -33.5), 'fill="#FAECE7" stroke="#D85A30" stroke-width="0.3"')
text(front(-50, -26.4), 'GPS patch', 1.9, col="#993C1D", weight=600); text(front(-50, -29.0), '12x12 face-up', 1.6, col="#993C1D")
tag(front(-50, -17.5), 6)
# Wi-Fi FlexPIFA (shifted right 7 mm)
rect(*front(-38.0, -22.05), *front(2.1, -33.05), 'fill="#FAEEDA" stroke="#BA7517" stroke-width="0.3" stroke-dasharray="0.8 0.8"')
text(front(-18, -26.6), 'Wi-Fi FlexPIFA, foam side to the wall', 1.9, col="#854F0B", weight=600)
text(front(-18, -29.4), 'cable end at LEFT (-X), 12 mm from the panel', 1.6, col="#854F0B")
tag(front(-18, -17.5), 3)
# Qi ring and coil
circ(front(45, 0), 28.0, ENGR); circ(front(45, 0), 27.0, ENGR)
circ(front(45, 0), 25.0, INS); circ(front(45, 0), 22.0, INS)
text(front(45, 8.5), 'Qi RING', 3.4, weight=600, col="#534AB7")
text(front(45, 4.8), 'raised 0.4 mm under the fabric, OD 56 / ID 54', 1.9, col="#534AB7")
text(front(45, 1.6), 'magnet ring 56/44 + 50 mm coil behind', 1.9, col="#993C1D")
text(front(45, -1.4), 'the 2.2 mm front wall (dotted)', 1.9, col="#993C1D")
text(front(45, -5.0), 'centre X +45, Y 0; 3.3 mm from the right wall', 1.8, col="#444441")
tag(front(45, -12), 12)
rect(*front(6.5, 36.25), *front(78.5, -36.25), PH)
text(front(8.0, 33.4), 'phone (77 wide, upright) covers X >= 6.5', 1.8, anchor="start", col="#185FA5")
text(front(8.0, -34.3), 'a 77 mm phone covers the last 1.4 mm of the window', 1.6, anchor="start", col=WARN)
text(front(-75.5, -15.5), 'FRONT', 4.0, anchor='start', weight=600)
text(front(-75.5, -19.2), '157 x 72.5, fabric', 2.0, anchor='start', col="#444441")

# ---------------- TOP edge ----------------
text((fx(0), TY0 - 3.0), 'TOP EDGE: 157 x 32.8, fabric (seen from above, front edge at the bottom)', 2.4, weight=600)
BZ = 19.7
for i, name in enumerate(("MUTE", "PWR", "VOL-", "VOL+", "PLAY")):
    X = -54.0 + 9.8 * i
    rect(*top(X - 2.6, BZ + 2.3), *top(X + 2.6, BZ - 2.3), CUT, rx=0.8)
    text((fx(X), top(X, BZ - 2.3)[1] - 1.2), name, 1.8, weight=600)
tag((fx(-34.4), top(0, 8)[1]), 17)
text((fx(-34.4), top(0, 8)[1] + 4.2), '5 x PTS645, 9.8 pitch, caps 5.2 x 4.6', 1.6)
text((fx(-34.4), top(0, 8)[1] + 6.4), 'X -54 / -44.2 / -34.4 / -24.6 / -14.8 (clear of speaker L)', 1.6)
rect(*top(52 - 5.4, 16.05 + 2.1), *top(52 + 5.4, 16.05 - 2.1), CUT, rx=2.0)
text((fx(52), top(0, 16.05 - 2.1)[1] - 1.4), 'USB-C 10.8 x 4.2, X +52', 1.8, weight=600)
tag((fx(61.5), top(0, 16.05)[1]), 11)
rect(*top(-6, 27.3), *top(36, 11.9), 'fill="#FAEEDA" stroke="#BA7517" stroke-width="0.3" stroke-dasharray="0.8 0.8"')
text((fx(15), top(0, 21)[1]), 'LTE flex (inside, taped to the wall)', 1.8, col="#854F0B", weight=600)
text((fx(15), top(0, 17.6)[1]), 'X -6..+36; 10.9 mm from USB-C', 1.6, col="#854F0B")
tag((fx(40), top(0, 19.6)[1]), 4)

# ---------------- BOTTOM edge (dock) ----------------
text((fx(-40), BY1 - 3.0), 'BOTTOM EDGE: stands on the dock, bare PETG', 2.4, weight=600)
for X in (-12, -4, 4, 12):
    circ(bot(X, 13.8), 1.35, HOLE)
text((fx(0), bot(0, 13.8)[1] - 3.0), '4 pogo pads 2.7 (8 mm apart)', 1.8, weight=500); tag((fx(18), bot(0, 13.8)[1]), 20)
for X in (-58, -32, 32, 58):
    circ(bot(X, 7.0), 3.1, INS)
text((fx(-45), bot(0, 7.0)[1] - 4.2), 'magnets 6 x 2 (inside, 1.6 skin)', 1.6, col="#993C1D"); tag((fx(-66), bot(0, 7)[1]), 21)
rect(*bot(20.5, 27.6), *bot(25.5, 14.5), INS)
text((fx(27), bot(0, 23)[1]), 'haptic fin', 1.6, anchor="start", col="#993C1D"); tag((fx(38), bot(0, 20)[1]), 19)

# ---------------- BACK (seen from behind) ----------------
RUB = 'fill="#444441" fill-opacity="0.35" stroke="#534AB7" stroke-width="0.35"'
cx, cy = back(0, 0)
o.append(f'<path d="{rrect_path(cx, cy, 76.0, 33.75, 6.0)} {rrect_path(cx, cy, 72.0, 29.75, 2.0)}" fill-rule="evenodd" {RUB}/>')
for X, Y in ((-66, 31.7), (66, 31.7), (-66, -31.7), (66, -31.7)):
    circ(back(X, Y), 1.2, 'fill="#fff" stroke="#111" stroke-width="0.3"')
text(back(0, -25.0), 'TPU RING: 4 wide, 2.5 in from the edge, R6 corners, 1.5 proud', 2.1, col="#534AB7", weight=600)
text(back(0, -22.0), 'press-fit in a 1.0 mm channel; it hides the 4 lid screws (white circles)', 1.8, col="#534AB7")
tag(back(-70, 31.75 - 0.2), 22)
bx, by = -53.5, -21.5
gx, gy = back(bx, by)
o.append(f'<g transform="rotate(180 {gx:.2f} {gy:.2f})"><rect x="{gx-13:.2f}" y="{gy-5.5:.2f}" width="26" height="11" rx="2" '
         f'fill="none" stroke="#534AB7" stroke-width="0.3"/>')
for dy, t, sz, w in ((-2.6, 'HeartSync', 2.4, 600), (0.6, '1 / 2', 2.4, 600), (3.6, 'made with love  2026', 1.6, 400)):
    o.append(f'<text x="{gx:.2f}" y="{gy + dy + 0.8:.2f}" font-size="{sz}" text-anchor="middle" fill="#2C2C2A" '
             f'font-weight="{w}" font-family="IBM Plex Sans, Arial, sans-serif">{t}</text>')
o.append('</g>')
text(back(-53.5, -12.6), 'ID block 26 x 11, 0.3 mm engraved', 1.7, col="#534AB7")
text(back(0, 14), 'BACK: 157 x 72.5, bare PETG lid (3.0 mm)', 3.0, weight=600)
text(back(0, 10.4), 'the device lies on the ring when in use', 2.0, col="#444441")

# ---------------- ENDS: honeycomb ----------------
HCR = 1.8 / math.sqrt(3)
COLDY = 2.6 * math.sqrt(3) / 2
ZC = 1.2 + 0.2 + (9 * 2.6 + 1.8) / 2
n_holes = 0
for side, F in ((-1, lend), (1, rend)):
    ecx = (F(0, ZF)[0] + F(0, ZB)[0]) / 2
    text((ecx, FY0 - 1.2), 'LEFT END' if side < 0 else 'RIGHT END', 2.4, weight=600)
    rect(*F(29.2, 26.8), *F(-29.2, 1.2), 'fill="none" stroke="#D85A30" stroke-width="0.35"')
    rect(*F(28.75, 23.3), *F(-28.75, 0.3), 'fill="none" stroke="#993C1D" stroke-width="0.3" stroke-dasharray="1.5 0.8"')
    k = 0
    for i in range(25):
        yc = (i - 12) * COLDY
        nz = 9 if i % 2 == 0 else 10
        for j in range(nz):
            zc = ZC + (j - (nz - 1) / 2) * 2.6
            p = []
            for a in range(6):
                ang = math.radians(60 * a)
                p.append(F(yc + HCR * math.cos(ang), zc + HCR * math.sin(ang)))
            o.append('<polygon points="' + ' '.join(f'{px:.2f},{py:.2f}' for px, py in p) + '" fill="#111"/>')
            k += 1
    n_holes = k
    tag((ecx, FY1 + 3.5), 9 if side < 0 else 10)
    for ii, (t, c) in enumerate((('%d hex holes, all through' % k, '#2C2C2A'), ('1.8 flats, 2.6 pitch', '#2C2C2A'),
                                 ('ePTFE 58.4 x 25.6 (solid)', '#D85A30'), ('speaker 57.5 x 23 (dash)', '#993C1D'),
                                 ('front edge is on the', '#5F5E5A'), ('front-panel side', '#5F5E5A'))):
        text((ecx, FY1 + 8.0 + ii * 2.5), t, 1.6, col=c)
    sx = F(0, ZF)[0]
    text((sx + (-1.2 if side < 0 else 1.2), FY0 + 6), 'front', 1.5, col="#5F5E5A", rot=-90 if side < 0 else 90)

# ---------------- title, scale, legend ----------------
text((M, M), 'HeartSync shell net, rev E, 1:1', 3.4, anchor="start", weight=600)
text((M, M + 4.2), '157 x 72.5 x 32.8 · 3.12in panel · 19 Nov 2026 · print at 100 % on A3', 2.2, anchor="start", col="#5F5E5A")
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
open('heartsync_net_revE.svg', 'w').write(svg)
print(VW, VH, n_holes)
