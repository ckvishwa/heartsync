"""HeartSync dock rev B (compact, phone tower), 1:1.
Base axes: X across (right +), Y depth (front 0 -> back 115), Z up (deck top 22). Tower: s = distance up the front face."""
import math

DL, DD, DH = 200.0, 115.0, 22.0
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


# ======================= SHEET 1: BASE NET =======================
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
# cradle (front)
S.rect(T(CR_O[0], CR_O[3]), T(CR_O[2], CR_O[1]), 'fill="#D3D1C7" stroke="#111" stroke-width="0.35"', rx=3)
S.rect(T(CR_I[0], CR_I[3]), T(CR_I[2], CR_I[1]), 'fill="#F6F4EE" stroke="#111" stroke-width="0.35"', rx=1.5)
for x in POGO_X: S.circ(T(x, POGO_Y), 1.0, HOLE)
for x in MAG_X: S.circ(T(x, MAG_Y), 3.1, INS)
for x in (-88, 88): S.circ(T(x, 10.5), 1.0, 'fill="none" stroke="#111" stroke-width="0.3"')
S.text(T(0, 38.4), 'CRADLE: HeartSync stands on its bottom edge, display to the front, back ring on the rear wall', 1.9, weight=600)
S.text(T(0, 20.2), 'pogo pins 2.5, 8 apart, 18.3 in from the rear wall · magnets 6 x 2 under a 1 mm floor', 1.6)
S.text(T(0, 10.0), 'slot 186.4 x 35.6 · front lip 10 high, rear wall 20 high, ends 14 · 2 drain holes', 1.5, col="#444441")
S.tag(T(18, POGO_Y), "D5"); S.tag(T(78, MAG_Y), "D6")
# tower footprint
S.rect(T(TW[0], TW[3]), T(TW[2], TW[1]), 'fill="#CECBF6" fill-opacity="0.5" stroke="#534AB7" stroke-width="0.4"', rx=3)
for x in (-65, -25): S.circ(T(x, 82), 1.7, 'fill="#fff" stroke="#534AB7" stroke-width="0.3"')
S.rect(T(-48, 70), T(-42, 66), 'fill="#fff" stroke="#534AB7" stroke-width="0.3"')
S.text(T(-45, 93), 'PHONE TOWER footprint 70 x 40', 1.9, col="#534AB7", weight=600)
S.text(T(-45, 89.6), '2 x M3 from below (circles)', 1.5, col="#534AB7")
S.text(T(-45, 74.2), 'coil cable hole 6 x 4', 1.5, col="#534AB7")
S.tag(T(-14, 66), "D3", "#534AB7")
# buds pad
S.circ(T(*BUD_C), 31, ENGR); S.circ(T(*BUD_C), 21.5, INS)
S.text(T(BUD_C[0], BUD_C[1] + 3.5), 'BUDS PAD', 2.6, weight=600, col="#534AB7")
S.text(T(BUD_C[0], BUD_C[1]), 'dish 62, 1.5 deep', 1.6, col="#534AB7")
S.text(T(BUD_C[0], BUD_C[1] - 3.0), '5 W coil 43 behind 1.2', 1.6, col="#993C1D")
S.tag(T(BUD_C[0] + 26, BUD_C[1] - 22), "D4")
S.text(T(98, 109.5), 'TOP DECK 200 x 115, fabric', 2.2, anchor="end", weight=600)
# faces
for x, lab in ((-20, 'device'), (0, 'phone'), (20, 'buds')):
    S.circ(FR(x, 11), 1.0, HOLE); S.text((FR(x, 11)[0], FR(x, 11)[1] + 4.4), lab, 1.5)
S.text((FR(-95, 11)[0], FR(-95, 11)[1] + 0.8), 'FRONT 200 x 22: 3 light pipes', 1.9, anchor="start", weight=600)
S.tag((FR(30, 11)[0], FR(30, 11)[1]), "D9")
S.rect(BK(USB_IN_X - 5.4, 9 + 2.1), BK(USB_IN_X + 5.4, 9 - 2.1), CUT, rx=2)
S.text((BK(USB_IN_X, 0)[0], BK(0, 18)[1]), 'USB-C IN 65 W (on the left seen from behind)', 1.6, weight=600)
S.tag((BK(USB_IN_X + 11, 9)[0], BK(0, 9)[1]), "D7")
S.text((BK(-60, 0)[0], BK(0, 11)[1]), 'BACK 200 x 22', 2.0, weight=600)
S.rect(RE(USB_OUT_Y + 5.4, 9 + 2.1), RE(USB_OUT_Y - 5.4, 9 - 2.1), CUT, rx=2)
S.text(RE(USB_OUT_Y - 19, 15.5), 'USB-C OUT tablet', 1.6, rot=90, weight=600)
S.tag(RE(USB_OUT_Y + 11, 11), "D8")
S.text(RE(100, 11), 'RIGHT END', 1.9, rot=90, weight=600)
for i in range(5): S.rect(LE(55 + i * 8, 15), LE(59 + i * 8, 7), CUT, rx=0.8)
S.text(LE(20, 11), 'LEFT END: 5 vents', 1.9, rot=-90, weight=600)
S.text((M, M), 'HeartSync DOCK, base net rev B (compact, phone tower), 1:1', 3.2, anchor="start", weight=600)
S.text((M, M + 4.4), '200 x 115 x 22 base · cradle at the front · phone tower + buds pad behind · print 100 % on A3 landscape',
       2.0, anchor="start", col="#5F5E5A")
sy = Y0 + DD + DH + 10
S.scale(M, sy)
S.text((M + 66, sy + 1), 'Solid black = cut/hole · grey dash = fold · purple = raised ring, dish, tower · orange dots = part inside.', 2.0, anchor="start")
S.text((M + 66, sy + 5.4), 'D-numbers = dock BOM. Corners drawn square (real R6). The tower is a separate print: net on sheet 2.', 2.0, anchor="start", col="#5F5E5A")
S.save('dock_net_revB.svg', VW1, sy + 12)
print('net', VW1, sy + 12)

# ======================= SHEET 2: INSIDE + TOWER NET + SIDE VIEW =======================
S = Sheet(); VW2 = 420.0
IX0, IY0 = M, M + 16
def I(x, y): return IX0 + DL / 2 + x, IY0 + DD - y
S.text((M, M), 'HeartSync DOCK rev B: inside layout 1:1, tower net 1:1, side view 1:2', 3.2, anchor="start", weight=600)
S.text((M, M + 4.4), 'Inside: seen from above with the deck lifted off, front at the bottom. Dashed = underside vents, feet.', 2.0, anchor="start", col="#5F5E5A")
S.rect(I(-100, 115), I(100, 0), 'fill="#FBFAF7" stroke="#111" stroke-width="0.45"', rx=6)
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
box(TW[0], TW[3], TW[2], TW[1], Qc[0], Qc[1], 0.25, rx=3)
box(-78, 92, -33, 62, G[0], G[1], 0.7)
S.text(I(-55.5, 79), 'phone Qi driver 45 x 30', 1.6, col=G[1], weight=600); S.text(I(-55.5, 76), 'under the tower', 1.4, col=G[1])
S.circ(I(*BUD_C), 21.5, f'fill="{Qc[0]}" fill-opacity="0.5" stroke="{Qc[1]}" stroke-width="0.4"')
S.text(I(BUD_C[0], BUD_C[1]), 'buds coil 43', 1.6, col=Qc[1], weight=600); S.tag(I(BUD_C[0], BUD_C[1] - 6), "D4", Qc[1])
box(-8, 109, 22, 89, G[0], G[1], 0.7); S.text(I(7, 99), 'buds driver', 1.5, col=G[1], weight=600)
box(88, 70, 100, 50, G[0], G[1], 0.7); box(92, USB_OUT_Y + 5.1, 100, USB_OUT_Y - 5.1, "#2C2C2A", "#2C2C2A", 0.85)
S.tag(I(84, 52), "D8", G[1])
box(USB_IN_X - 5.1, 115, USB_IN_X + 5.1, 107.2, "#2C2C2A", "#2C2C2A", 0.85); S.tag(I(USB_IN_X + 9, 110), "D7", GR[1])
for x0, y0, x1, y1 in ((-98, 103, -82, 55), (82, 103, 98, 74)):
    box(x0, y0, x1, y1, GR[0], GR[1], 0.8)
S.text(I(-90, 82), 'steel', 1.4, weight=600, rot=-90); S.text(I(90, 93), 'steel', 1.4, weight=600, rot=-90); S.tag(I(78, 82), "D11", GR[1])
for x, y in ((-94, 6), (94, 6), (-94, 109), (94, 109), (0, 50)):
    S.circ(I(x, y), 2.8, 'fill="#D3D1C7" stroke="#444441" stroke-width="0.3"'); S.circ(I(x, y), 1.6, 'fill="#fff"')
for x, y in ((-86, 12), (86, 12), (-86, 103), (86, 103)):
    S.circ(I(x, y), 5, 'fill="none" stroke="#444441" stroke-width="0.3" stroke-dasharray="1 0.8"')
for k in (-2, -1, 1, 2):
    S.rect(I(BUD_C[0] - 14, BUD_C[1] + k * 6 + 1), I(BUD_C[0] + 14, BUD_C[1] + k * 6 - 1), 'fill="none" stroke="#5F5E5A" stroke-width="0.25" stroke-dasharray="1 0.8"')
    S.rect(I(-70, 77 + k * 6 + 1), I(-40, 77 + k * 6 - 1), 'fill="none" stroke="#5F5E5A" stroke-width="0.25" stroke-dasharray="1 0.8"')
for x0 in (-45, 25):
    S.rect(I(x0, 24 + 1), I(x0 + 20, 24 - 1), 'fill="none" stroke="#5F5E5A" stroke-width="0.25" stroke-dasharray="1 0.8"')
for x in (-20, 0, 20): S.circ(I(x, 3), 0.9, 'fill="#EF9F27"')
S.text(I(-98, -4.5), 'FRONT · grey circles = M3 bosses · dashed circles = rubber feet', 1.6, anchor="start", col="#5F5E5A")
S.text(I(-98, 118.5), 'BACK', 1.7, anchor="start", col="#5F5E5A", weight=600)

# ---- tower net (front face centre, sides, back, top) ----
NX0, NY0 = IX0 + DL + 30, IY0 + 4
def TF(u, s): return NX0 + TT + TWD / 2 + u, NY0 + TT + TL - s          # front face, u across (-35..35), s up
FX0 = NX0 + TT
S.text((NX0, NY0 - 3), 'PHONE TOWER net, 1:1 (separate print, PETG)', 2.4, anchor="start", weight=600)
S.rect((FX0, NY0 + TT), (FX0 + TWD, NY0 + TT + TL), FAB)
S.rect((FX0 - TT, NY0 + TT), (FX0, NY0 + TT + TL), PET); S.rect((FX0 + TWD, NY0 + TT), (FX0 + TWD + TT, NY0 + TT + TL), PET)
S.rect((FX0, NY0), (FX0 + TWD, NY0 + TT), PET)
S.rect((FX0 + TWD + TT, NY0 + TT), (FX0 + 2 * TWD + TT, NY0 + TT + TL), PET)
S.poly([(FX0, NY0), (FX0 + TWD, NY0), (FX0 + TWD, NY0 + TT), (FX0 + 2 * TWD + TT, NY0 + TT), (FX0 + 2 * TWD + TT, NY0 + TT + TL),
        (FX0 - TT, NY0 + TT + TL), (FX0 - TT, NY0 + TT), (FX0, NY0 + TT)], CUT)
for a, b in (((FX0, NY0 + TT), (FX0 + TWD, NY0 + TT)), ((FX0, NY0 + TT), (FX0, NY0 + TT + TL)), ((FX0 + TWD, NY0 + TT), (FX0 + TWD, NY0 + TT + TL)),
             ((FX0 + TWD + TT, NY0 + TT), (FX0 + TWD + TT, NY0 + TT + TL))):
    S.line(a, b, FOLD)
S.circ(TF(0, COIL_S), 28, ENGR); S.circ(TF(0, COIL_S), 27, ENGR); S.circ(TF(0, COIL_S), 25, INS)
S.text(TF(0, COIL_S + 3), 'Qi ring', 2.4, col="#534AB7", weight=600)
S.text(TF(0, COIL_S - 0.5), 'raised 0.4, OD 56', 1.6, col="#534AB7")
S.text(TF(0, COIL_S - 3.6), 'coil + magnet ring', 1.6, col="#993C1D")
S.text(TF(0, COIL_S - 6.4), 'centre 100 up the face', 1.5, col="#444441")
S.rect(TF(-35, LEDGE_S), TF(35, LEDGE_S - 3), 'fill="#534AB7" fill-opacity="0.5"')
S.text(TF(0, LEDGE_S - 6.5), 'phone ledge 70 x 6 x 3, 20 up', 1.6, col="#534AB7")
S.text(TF(0, 50), 'FRONT', 2.4, weight=600); S.text(TF(0, 46.5), '70 x 130, fabric', 1.6, col="#444441")
S.text((FX0 + TWD + TT + TWD / 2, NY0 + TT + 66), 'BACK 70 x 130', 2.2, weight=600)
S.text((FX0 + TWD + TT + TWD / 2, NY0 + TT + 62), 'bare PETG', 1.6, col="#444441")
S.text((FX0 - TT / 2, NY0 + TT + 66), 'SIDE 12', 1.6, rot=-90, weight=600); S.text((FX0 + TWD + TT / 2, NY0 + TT + 66), 'SIDE 12', 1.6, rot=-90, weight=600)
S.text((FX0 + TWD / 2, NY0 + 7.4), 'TOP 70 x 12', 1.6, weight=600)
S.text((FX0 + TWD / 2, NY0 + TT + TL + 4.5), 'bottom edge cut at 12°: the tower leans back 12°', 1.6, col="#444441")
S.text((FX0 + TWD / 2, NY0 + TT + TL + 7.5), 'coil cable runs down inside to the driver in the base', 1.6, col="#444441")
S.tag(TF(30, COIL_S + 24), "D3", "#534AB7")

# ---- side view 1:2 (from the right, front on the left) ----
SX0, SZ0 = IX0, IY0 + DD + 18
def SV(y, z): return SX0 + y / 2, SZ0 + 110 - z / 2
S.text((SX0, SZ0 + 4), 'SIDE VIEW 1:2 (from the right, front left)', 2.4, anchor="start", weight=600)
S.rect(SV(0, 22), SV(115, 0), 'fill="#EADFCB" stroke="#444441" stroke-width="0.3"', rx=1)
S.rect(SV(3, 32), SV(7, 22), 'fill="#D3D1C7" stroke="#444441" stroke-width="0.25"')
S.rect(SV(42.6, 42), SV(46.6, 22), 'fill="#D3D1C7" stroke="#444441" stroke-width="0.25"')
S.rect(SV(8.3, 94.5), SV(41.1, 22), 'fill="#2C2C2A" stroke="#111" stroke-width="0.25"')
S.rect(SV(41.1, 92), SV(42.6, 24.5), 'fill="#444441"')
tn = math.tan(math.radians(TILT)); cs = math.cos(math.radians(TILT)); sn = math.sin(math.radians(TILT))
fy0 = 66.0
tower = [(fy0, 22), (fy0 + TL * sn, 22 + TL * cs), (fy0 + TL * sn + TT, 22 + TL * cs), (fy0 + TT + 4, 22)]
S.poly([SV(*p) for p in tower], 'fill="#CECBF6" stroke="#534AB7" stroke-width="0.3"')
p0 = (fy0 + LEDGE_S * sn, 22 + LEDGE_S * cs); p1 = (fy0 + (LEDGE_S + 163) * sn, 22 + (LEDGE_S + 163) * cs)
S.poly([SV(p0[0] - 8, p0[1]), SV(*p0), SV(*p1), SV(p1[0] - 8, p1[1])], 'fill="#B5D4F4" stroke="#185FA5" stroke-width="0.3"')
cc = (fy0 + COIL_S * sn, 22 + COIL_S * cs); S.circ(SV(*cc), 1.6, 'fill="none" stroke="#534AB7" stroke-width="0.5"')
for z, lab in ((p1[1], 'phone top %.0f' % p1[1]), (22 + TL * cs, 'tower %.0f' % (22 + TL * cs)), (94.5, 'HeartSync 94.5'), (22, 'base 22')):
    S.line(SV(118, z), SV(126, z), 'stroke="#888780" stroke-width="0.2"'); S.text((SV(128, z)[0], SV(0, z)[1] + 0.7), lab, 1.6, anchor="start")
S.text((SV(0, 0)[0], SV(0, 0)[1] + 4), '115 deep', 1.6, anchor="start", col="#444441")
S.scale(M + 110, IY0 + DD + 30)
S.text((M + 110, IY0 + DD + 48), 'Power: one 65 W USB-C adapter → device 18 W + phone 15 W + buds 5 W + tablet 15 W.', 2.0, anchor="start")
S.text((M + 110, IY0 + DD + 52.4), 'Weights (D11) are needed now: the phone sits 200 mm up.', 2.0, anchor="start", col="#A32D2D")
S.save('dock_inside_revB.svg', VW2, SZ0 + 118)
print('inside', VW2, SZ0 + 118, 'phone top', round(p1[1], 1), 'tower top', round(22 + TL * cs, 1), 'tower back y', round(fy0 + TL * sn + TT, 1))
