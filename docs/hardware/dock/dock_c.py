"""HeartSync dock rev B (compact, phone tower), 1:1.
Base axes: X across (right +), Y depth (front 0 -> back 115), Z up (deck top 22). Tower: s = distance up the front face."""
import math

DL, DD, DH = 200.0, 105.0, 20.0
CR_O = (-97.2, 3.0, 97.2, 46.6)          # cradle outer (front of the base)
CR_I = (-93.2, 7.0, 93.2, 42.6)          # slot: device front at Y 8.3, back ring on the rear wall (Y 42.6)
POGO_Y, MAG_Y = 42.6 - 18.3, 42.6 - 11.5
POGO_X, MAG_X = (-12, -4, 4, 12), (-70, -32, 32, 70)
TW = (-80.0, 62.0, -10.0, 102.0)         # tower footprint on the deck (70 x 40)
BUD_C = (50.0, 80.0)
USB_IN_X, USB_OUT_Y = 30.0, 60.0
TILT = 12.0
TL, TT, TWD = 130.0, 12.0, 70.0          # tower face length, thickness, width
COIL_S, LEDGE_S = 100.0, 20.0
FONT = 'font-family="IBM Plex Sans, Arial, sans-serif"'
CUT = 'fill="none" stroke="#111" stroke-width="0.35"'
HOLE = 'fill="#111"'
FOLD = 'fill="none" stroke="#5F5E5A" stroke-width="0.3" stroke-dasharray="2 1.2"'
ENGR = 'fill="none" stroke="#534AB7" stroke-width="0.35"'
INS = 'fill="none" stroke="#D85A30" stroke-width="0.3" stroke-dasharray="0.8 0.8"'
PHS = 'fill="none" stroke="#185FA5" stroke-width="0.35" stroke-dasharray="3 1.5"'
FAB, PET = 'fill="#EADFCB"', 'fill="#F6F4EE"'


class Sheet:
    def __init__(s): s.o = []
    def rect(s, a, b, st, rx=0):
        x0, x1 = sorted((a[0], b[0])); y0, y1 = sorted((a[1], b[1]))
        s.o.append(f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{x1-x0:.2f}" height="{y1-y0:.2f}"' + (f' rx="{rx}"' if rx else '') + f' {st}/>')
    def circ(s, c, r, st): s.o.append(f'<circle cx="{c[0]:.2f}" cy="{c[1]:.2f}" r="{r:.2f}" {st}/>')
    def line(s, a, b, st): s.o.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" {st}/>')
    def poly(s, pts, st): s.o.append('<polygon points="' + ' '.join(f'{x:.2f},{y:.2f}' for x, y in pts) + f'" {st}/>')
    def text(s, p, t, size=2.2, anchor="middle", col="#2C2C2A", weight=400, rot=0):
        tr = f' transform="rotate({rot} {p[0]:.2f} {p[1]:.2f})"' if rot else ''
        s.o.append(f'<text x="{p[0]:.2f}" y="{p[1]:.2f}" font-size="{size}" text-anchor="{anchor}" fill="{col}" font-weight="{weight}" {FONT}{tr}>{t}</text>')
    def tag(s, p, n, col="#D85A30"):
        s.circ(p, 1.9, f'fill="#fff" stroke="{col}" stroke-width="0.35"'); s.text((p[0], p[1] + 0.85), n, 1.9, col=col, weight=600)
    def save(s, name, w, h):
        open(name, 'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.1f}mm" height="{h:.1f}mm" viewBox="0 0 {w:.1f} {h:.1f}">'
                              f'<rect width="{w:.1f}" height="{h:.1f}" fill="#fff"/>{"".join(s.o)}</svg>')
    def scale(s, x, y):
        s.rect((x, y), (x + 50, y + 2), 'fill="#111"')
        for i in range(6): s.line((x + 10 * i, y - 1), (x + 10 * i, y + 3), 'stroke="#111" stroke-width="0.25"')
        s.text((x, y + 7), '50 mm: measure after printing', 2.2, anchor="start")


# ---------------- rev C: Belkin-style stem + landscape iPhone, buds pad, clip-on tablet rail ----------------
STEM = (-10.0, 78.0); BUD_C = (62.0, 75.5); USB_IN_X, USB_OUT_Y = -30.0, 82.0
PUCK_Z = 137.5

S = Sheet(); M = 16.0
X0 = M + DH + 8; Y0 = M + 16 + DH
VW1 = 2 * X0 + DL
def T(x, y): return X0 + DL / 2 + x, Y0 + DD - y
def FR(x, z): return X0 + DL / 2 + x, Y0 + DD + (DH - z)
def BK(x, z): return X0 + DL / 2 + x, Y0 - (DH - z)
def LE(y, z): return X0 - (DH - z), Y0 + DD - y
def RE(y, z): return X0 + DL + (DH - z), Y0 + DD - y
S.rect((X0, Y0), (X0 + DL, Y0 + DD), FAB)
for a, b in (((X0, Y0 + DD), (X0 + DL, Y0 + DD + DH)), ((X0, Y0 - DH), (X0 + DL, Y0)),
             ((X0 - DH, Y0), (X0, Y0 + DD)), ((X0 + DL, Y0), (X0 + DL + DH, Y0 + DD))):
    S.rect(a, b, PET)
S.poly([(X0, Y0 - DH), (X0 + DL, Y0 - DH), (X0 + DL, Y0), (X0 + DL + DH, Y0), (X0 + DL + DH, Y0 + DD), (X0 + DL, Y0 + DD),
        (X0 + DL, Y0 + DD + DH), (X0, Y0 + DD + DH), (X0, Y0 + DD), (X0 - DH, Y0 + DD), (X0 - DH, Y0), (X0, Y0)], CUT)
for a, b in (((X0, Y0), (X0 + DL, Y0)), ((X0, Y0 + DD), (X0 + DL, Y0 + DD)), ((X0, Y0), (X0, Y0 + DD)), ((X0 + DL, Y0), (X0 + DL, Y0 + DD))):
    S.line(a, b, FOLD)
S.rect(T(CR_O[0], CR_O[3]), T(CR_O[2], CR_O[1]), 'fill="#D3D1C7" stroke="#111" stroke-width="0.35"', rx=3)
S.rect(T(CR_I[0], CR_I[3]), T(CR_I[2], CR_I[1]), 'fill="#F6F4EE" stroke="#111" stroke-width="0.35"', rx=1.5)
for x in POGO_X: S.circ(T(x, POGO_Y), 1.0, HOLE)
for x in MAG_X: S.circ(T(x, MAG_Y), 3.1, INS)
for x in (-88, 88): S.circ(T(x, 10.5), 1.0, 'fill="none" stroke="#111" stroke-width="0.3"')
S.text(T(0, 38.4), 'CRADLE: HeartSync stands on its bottom edge, display to the front, back ring on the rear wall', 1.9, weight=600)
S.text(T(0, 20.2), 'pogo pins 2.5, 8 apart, 18.3 in from the rear wall · magnets 6 x 2 under a 1 mm floor', 1.6)
S.text(T(0, 10.0), 'slot 186.4 x 35.6 · front lip 10 high, rear wall 20 high, ends 14 · 2 drain holes', 1.5, col="#444441")
S.tag(T(18, POGO_Y), "D5"); S.tag(T(78, MAG_Y), "D6")
# stem foot
S.circ(T(*STEM), 20, 'fill="#CECBF6" fill-opacity="0.5" stroke="#534AB7" stroke-width="0.4"')
for dx in (-12, 12): S.circ(T(STEM[0] + dx, STEM[1]), 1.7, 'fill="#fff" stroke="#534AB7" stroke-width="0.3"')
S.rect(T(STEM[0] - 3, STEM[1] - 5), T(STEM[0] + 3, STEM[1] - 9), 'fill="#fff" stroke="#534AB7" stroke-width="0.3"')
S.text(T(STEM[0], STEM[1] + 6.5), 'PHONE STEM foot Ø40', 1.8, col="#534AB7", weight=600)
S.text(T(STEM[0], STEM[1] + 3.4), '2 x M3 from below', 1.4, col="#534AB7")
S.text(T(STEM[0], STEM[1] - 12.2), 'cable hole 6 x 4', 1.4, col="#534AB7")
S.tag(T(STEM[0] + 23, STEM[1] + 14), "D3", "#534AB7")
# buds pad (oval for a buds case lying flat)
o = S.o
cx, cy = T(*BUD_C)
o.append(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="33" ry="25.5" {ENGR}/>')
S.circ(T(*BUD_C), 21.5, INS)
S.text(T(BUD_C[0], BUD_C[1] + 3.5), 'BUDS PAD', 2.6, weight=600, col="#534AB7")
S.text(T(BUD_C[0], BUD_C[1]), 'oval 66 x 51, 1.5 deep', 1.6, col="#534AB7")
S.text(T(BUD_C[0], BUD_C[1] - 3.0), '5 W coil 43 behind 1.2', 1.6, col="#993C1D")
S.tag(T(BUD_C[0] + 30, BUD_C[1] - 22), "D4")
S.text(T(-98, 100.5), 'TOP DECK 200 x 105, fabric', 2.2, anchor="start", weight=600)
S.text(T(-98, 56), 'free: light weight inside', 1.5, anchor="start", col="#444441")
for x, lab in ((-20, 'device'), (0, 'phone'), (20, 'buds')):
    S.circ(FR(x, 10), 1.0, HOLE); S.text((FR(x, 10)[0], FR(x, 10)[1] + 4.2), lab, 1.5)
S.text((FR(-95, 10)[0], FR(-95, 10)[1] + 0.8), 'FRONT 200 x 20: 3 light pipes', 1.9, anchor="start", weight=600)
S.tag((FR(30, 10)[0], FR(30, 10)[1]), "D9")
S.rect(BK(USB_IN_X - 5.4, 8 + 2.1), BK(USB_IN_X + 5.4, 8 - 2.1), CUT, rx=2)
S.text((BK(USB_IN_X, 0)[0], BK(0, 16)[1]), 'USB-C IN 65 W', 1.6, weight=600)
S.tag((BK(USB_IN_X + 11, 8)[0], BK(0, 8)[1]), "D7")
for x in (-60, 60):
    S.rect(BK(x - 6 + 0.01, 14), BK(x + 6, 8), CUT, rx=0.6)
S.text((BK(0, 0)[0], BK(0, 12)[1]), 'BACK 200 x 20 · 2 slots 12 x 6 for the tablet-rail hooks (X ±60)', 1.7, weight=600)
S.rect(RE(USB_OUT_Y + 5.4, 8 + 2.1), RE(USB_OUT_Y - 5.4, 8 - 2.1), CUT, rx=2)
S.text(RE(USB_OUT_Y - 19, 14.5), 'USB-C OUT tablet', 1.6, rot=90, weight=600)
S.tag(RE(USB_OUT_Y - 30, 10), "D8")
S.text(RE(30, 10), 'RIGHT END', 1.9, rot=90, weight=600)
for i in range(5): S.rect(LE(50 + i * 8, 14), LE(54 + i * 8, 6), CUT, rx=0.8)
S.text(LE(20, 10), 'LEFT END: 5 vents', 1.9, rot=-90, weight=600)
S.text((M, M), 'HeartSync DOCK, base net rev C (stem + landscape iPhone), 1:1', 3.2, anchor="start", weight=600)
S.text((M, M + 4.4), '200 x 105 x 20 base · cradle front · phone stem + buds pad behind · tablet rail clips on the back (+18) · print 100 % on A3 landscape',
       2.0, anchor="start", col="#5F5E5A")
sy = Y0 + DD + DH + 10
S.scale(M, sy)
S.text((M + 66, sy + 1), 'Solid black = cut/hole · grey dash = fold · purple = raised ring, pad, stem foot · orange dots = part inside.', 2.0, anchor="start")
S.text((M + 66, sy + 5.4), 'D-numbers = dock BOM. Corners drawn square (real R6). Stem, puck and rail: sheet 2.', 2.0, anchor="start", col="#5F5E5A")
S.save('dock_net_revC.svg', VW1, sy + 12)
print('net', VW1, sy + 12)

# ======================= SHEET 2 =======================
S = Sheet(); VW2 = 420.0
IX0, IY0 = M, M + 16
def I(x, y): return IX0 + DL / 2 + x, IY0 + DD - y
S.text((M, M), 'HeartSync DOCK rev C: inside 1:1, stem + puck + rail parts 1:1, side view 1:2', 3.2, anchor="start", weight=600)
S.text((M, M + 4.4), 'Inside: seen from above with the deck lifted off, front at the bottom. Dashed = underside vents and feet.', 2.0, anchor="start", col="#5F5E5A")
S.rect(I(-100, 105), I(100, 0), 'fill="#FBFAF7" stroke="#111" stroke-width="0.45"', rx=6)
def box(x0, y0, x1, y1, fc, sc, op=0.6, rx=0):
    S.rect(I(x0, y0), I(x1, y1), f'fill="{fc}" fill-opacity="{op}" stroke="{sc}" stroke-width="0.35"', rx)
G, Qc, GR = ("#C0DD97", "#3B6D11"), ("#CECBF6", "#534AB7"), ("#D3D1C7", "#444441")
box(-55, 42, 55, 6, G[0], G[1], 0.55)
S.text(I(0, 37.4), 'MAIN DOCK BOARD 110 x 36 (under the cradle)', 1.9, col=G[1], weight=600)
S.text(I(0, 34.4), 'PD sink 65 W · fuse + TVS · buck rails · PD source (tablet) · pogo switch · LEDs', 1.5, col=G[1])
S.tag(I(-50, 10), "D1", G[1])
box(-17, POGO_Y + 3.7, 17, POGO_Y - 3.7, "#2C2C2A", "#2C2C2A", 0.85)
for x in POGO_X: S.circ(I(x, POGO_Y), 1.0, 'fill="#C9A227"')
S.tag(I(21, POGO_Y), "D5", GR[1])
for x in MAG_X: S.rect(I(x - 3, MAG_Y + 1), I(x + 3, MAG_Y - 1), 'fill="#5F5E5A"')
S.circ(I(*STEM), 20, 'fill="#CECBF6" fill-opacity="0.25" stroke="#534AB7" stroke-width="0.35" stroke-dasharray="1 0.8"')
box(-32.5, 92, 12.5, 62, G[0], G[1], 0.7)
S.text(I(-10, 79), 'phone Qi driver 45 x 30', 1.6, col=G[1], weight=600); S.text(I(-10, 76), 'under the stem (cable up the stem)', 1.4, col=G[1])
cx, cy = I(*BUD_C)
S.o.append(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="33" ry="25.5" fill="none" stroke="#534AB7" stroke-width="0.3" stroke-dasharray="1 0.8"/>')
S.circ(I(*BUD_C), 21.5, f'fill="{Qc[0]}" fill-opacity="0.5" stroke="{Qc[1]}" stroke-width="0.4"')
S.text(I(BUD_C[0], BUD_C[1]), 'buds coil 43', 1.6, col=Qc[1], weight=600); S.tag(I(BUD_C[0], BUD_C[1] - 6), "D4", Qc[1])
box(-95, 80, -65, 55, G[0], G[1], 0.7); S.text(I(-80, 68), 'buds driver', 1.5, col=G[1], weight=600)
box(-98, 102, -66, 84, GR[0], GR[1], 0.8); S.text(I(-82, 92), 'steel 32 x 18 x 8', 1.4, weight=600); S.tag(I(-62, 93), "D11", GR[1])
box(88, 92, 100, 72, G[0], G[1], 0.7); box(92, USB_OUT_Y + 5.1, 100, USB_OUT_Y - 5.1, "#2C2C2A", "#2C2C2A", 0.85); S.tag(I(84, 70), "D8", G[1])
box(USB_IN_X - 5.1, 105, USB_IN_X + 5.1, 97.2, "#2C2C2A", "#2C2C2A", 0.85); S.tag(I(USB_IN_X + 9, 100), "D7", GR[1])
for x, y in ((-94, 6), (94, 6), (-94, 99), (94, 99), (0, 50)):
    S.circ(I(x, y), 2.8, 'fill="#D3D1C7" stroke="#444441" stroke-width="0.3"'); S.circ(I(x, y), 1.6, 'fill="#fff"')
for x, y in ((-86, 12), (86, 12), (-86, 93), (86, 93)):
    S.circ(I(x, y), 5, 'fill="none" stroke="#444441" stroke-width="0.3" stroke-dasharray="1 0.8"')
for k in (-2, -1, 1, 2):
    S.rect(I(BUD_C[0] - 14, BUD_C[1] + k * 6 + 1), I(BUD_C[0] + 14, BUD_C[1] + k * 6 - 1), 'fill="none" stroke="#5F5E5A" stroke-width="0.25" stroke-dasharray="1 0.8"')
for x0 in (-45, 25):
    S.rect(I(x0, 24 + 1), I(x0 + 20, 24 - 1), 'fill="none" stroke="#5F5E5A" stroke-width="0.25" stroke-dasharray="1 0.8"')
for x in (-20, 0, 20): S.circ(I(x, 3), 0.9, 'fill="#EF9F27"')
S.text(I(-98, -4.5), 'FRONT · grey circles = M3 bosses · dashed circles = rubber feet', 1.6, anchor="start", col="#5F5E5A")
S.text(I(-98, 108.5), 'BACK', 1.7, anchor="start", col="#5F5E5A", weight=600)

# ---- parts (flat patterns), right column ----
PX, PY = IX0 + DL + 24, IY0 + 2
S.text((PX, PY), 'STEM, PUCK, RAIL: flat patterns 1:1', 2.4, anchor="start", weight=600)
# stem wrap: Ø23 avg x 112 tall -> 72.3 x 112 (fabric wrap or print as a tube)
S.rect((PX, PY + 6), (PX + 72.3, PY + 6 + 112), FAB); S.rect((PX, PY + 6), (PX + 72.3, PY + 6 + 112), CUT)
S.text((PX + 36, PY + 60), 'STEM WRAP', 2.2, weight=600); S.text((PX + 36, PY + 63.6), '72.3 x 112 (Ø23 tube)', 1.6, col="#444441")
S.text((PX + 36, PY + 66.8), 'seam at the back', 1.5, col="#444441")
S.tag((PX + 66, PY + 12), "D3", "#534AB7")
# foot disc + puck faces
fx = PX + 112
S.circ((fx, PY + 28), 20, PET + ' stroke="#111" stroke-width="0.35"'); S.text((fx, PY + 28.6), 'FOOT Ø40', 1.8, weight=600)
S.circ((fx + 2, PY + 82), 31, FAB + ' stroke="#111" stroke-width="0.35"'); S.circ((fx + 2, PY + 82), 28, ENGR); S.circ((fx + 2, PY + 82), 25, INS)
S.text((fx + 2, PY + 80), 'PUCK FRONT Ø62', 1.9, weight=600); S.text((fx + 2, PY + 83.4), 'fabric, raised ring OD 56', 1.5, col="#534AB7")
S.text((fx + 2, PY + 86.4), 'coil 50 + magnet ring behind', 1.5, col="#993C1D")
S.text((fx + 2, PY + 116), 'puck 9 deep, tilted back 10°, centre 137.5 up', 1.5, col="#444441")
# puck rim band
for k in range(2):
    S.rect((PX + k * 100, PY + 126), (PX + k * 100 + 97.4, PY + 135), PET); S.rect((PX + k * 100, PY + 126), (PX + k * 100 + 97.4, PY + 135), CUT)
    S.text((PX + k * 100 + 48.7, PY + 131.6), 'PUCK RIM half %d: 97.4 x 9' % (k + 1), 1.6, weight=600)
# tablet rail
ry = PY + 146
S.rect((PX, ry), (PX + 160, ry + 18), PET); S.rect((PX, ry), (PX + 160, ry + 18), CUT)
S.text((PX + 80, ry + 6.5), 'TABLET RAIL (clip-on), drawn at 160 of 200 long: full part 200 x 18 x 20', 1.6, weight=600)
S.text((PX + 80, ry + 10), 'slot 13 wide, 8 deep, leaning back 15° · 2 hooks into the base back slots (X ±60)', 1.5, col="#444441")
S.text((PX + 80, ry + 13.3), 'Tab A9 211 x 124.7 x 8 stands in landscape; cable from the right-end USB-C', 1.5, col="#444441")
S.tag((PX + 156, ry + 3), "D13", "#444441")

# ---- side view 1:2 ----
SX0, SZ0 = IX0, IY0 + DD + 12
def SV(y, z): return SX0 + 10 + y / 2, SZ0 + 96 - z / 2
S.text((SX0, SZ0 + 4), 'SIDE VIEW 1:2 (from the right, front left; all parts projected)', 2.4, anchor="start", weight=600)
S.rect(SV(0, 20), SV(105, 0), 'fill="#EADFCB" stroke="#444441" stroke-width="0.3"', rx=1)
S.rect(SV(105, 20), SV(123, 0), 'fill="#F6F4EE" stroke="#444441" stroke-width="0.3" stroke-dasharray="1 0.6"', rx=1)
S.rect(SV(3, 30), SV(7, 20), 'fill="#D3D1C7" stroke="#444441" stroke-width="0.25"')
S.rect(SV(42.6, 40), SV(46.6, 20), 'fill="#D3D1C7" stroke="#444441" stroke-width="0.25"')
S.rect(SV(8.3, 92.5), SV(41.1, 20), 'fill="#2C2C2A" stroke="#111" stroke-width="0.25"')
S.rect(SV(STEM[1] - 11.5, 136), SV(STEM[1] + 11.5, 20), 'fill="#CECBF6" stroke="#534AB7" stroke-width="0.3"')
a = math.radians(10)
def rot(dy, dz): return (72 + dy * math.cos(a) + dz * math.sin(a), PUCK_Z - dy * math.sin(a) + dz * math.cos(a))
pk = [rot(-4.5, -31), rot(4.5, -31), rot(4.5, 31), rot(-4.5, 31)]
S.poly([SV(*p) for p in pk], 'fill="#CECBF6" stroke="#534AB7" stroke-width="0.3"')
ph = [rot(-12.8, -39), rot(-4.5, -39), rot(-4.5, 39), rot(-12.8, 39)]
S.poly([SV(*p) for p in ph], 'fill="#B5D4F4" stroke="#185FA5" stroke-width="0.3"')
t = math.radians(15)
tb = [(110, 20), (118, 20), (118 - 124.7 * math.sin(t) * -1 * 0 + 124.7 * math.sin(t), 20 + 124.7 * math.cos(t)), (110 + 124.7 * math.sin(t), 20 + 124.7 * math.cos(t))]
S.poly([SV(*p) for p in tb], 'fill="#5F5E5A" fill-opacity="0.6" stroke="#2C2C2A" stroke-width="0.3"')
ptop = max(p[1] for p in ph); tbtop = tb[2][1]
for z, lab in ((ptop, 'iPhone top %.0f' % ptop), (tbtop, 'tablet top %.0f' % tbtop), (92.5, 'HeartSync 92.5'), (20, 'base 20')):
    S.line(SV(160, z), SV(168, z), 'stroke="#888780" stroke-width="0.2"'); S.text((SV(170, z)[0], SV(0, z)[1] + 0.7), lab, 1.6, anchor="start")
S.text((SV(0, 0)[0], SV(0, 0)[1] + 4), '105 deep (123 with the tablet rail)', 1.6, anchor="start", col="#444441")
S.scale(M + 130, IY0 + DD + 30)
S.text((M + 130, IY0 + DD + 48), 'Power: one 65 W USB-C adapter → device 18 W + phone 15 W + buds 5 W + tablet 15 W.', 2.0, anchor="start")
S.text((M + 130, IY0 + DD + 52.4), 'The iPhone sits landscape above the HeartSync (StandBy clock); its CG stays over the base.', 2.0, anchor="start", col="#444441")
S.save('dock_inside_revC.svg', VW2, SZ0 + 104)
print('inside', VW2, SZ0 + 104, 'phone top', round(ptop, 1), 'phone bottom', round(min(p[1] for p in ph), 1), 'tablet top', round(tbtop, 1))
