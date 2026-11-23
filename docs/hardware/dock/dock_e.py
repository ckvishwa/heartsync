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


# ======================= rev E: no cradle; phone on a round puck (landscape or portrait); buds pad; watch/band side stand =======================
DL, DD, DH = 160.0, 95.0, 18.0
STEM, PUCK_Y, PUCK_Z, TILT = (-35.0, 58.0), 52.0, 110.0, 10.0
BUD_C, WATCH = (40.0, 28.0), (62.0, 76.0)
USB_IN_X = -40.0
PORTS = [('USB-A', 20.0, 13.7, 6.3), ('USB-C', 37.0, 10.8, 4.2), ('USB-C', 52.0, 10.8, 4.2)]
LEDS = ((-15, 'phone'), (0, 'buds'), (15, 'watch'))

S = Sheet(); M = 16.0
X0 = M + DH + 8; Y0 = M + 16 + DH
VW1 = 2 * X0 + DL + 40
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
# phone footprints (above the deck)
S.rect(T(STEM[0] - 39, 43), T(STEM[0] + 39, 36), PHS, rx=2)
S.text(T(STEM[0], 31.5), 'phone above: portrait 78 wide (dash) · landscape 163 wide, overhangs the left end 36', 1.5, col="#185FA5")
# stem foot
S.circ(T(*STEM), 20, 'fill="#CECBF6" fill-opacity="0.5" stroke="#534AB7" stroke-width="0.4"')
for dx in (-12, 12): S.circ(T(STEM[0] + dx, STEM[1]), 1.7, 'fill="#fff" stroke="#534AB7" stroke-width="0.3"')
S.rect(T(STEM[0] - 3, STEM[1] - 5), T(STEM[0] + 3, STEM[1] - 9), 'fill="#fff" stroke="#534AB7" stroke-width="0.3"')
S.text(T(STEM[0], STEM[1] + 6.5), 'PHONE STEM Ø40', 1.8, col="#534AB7", weight=600)
S.text(T(STEM[0], STEM[1] + 3.4), '2 x M3 from below', 1.4, col="#534AB7")
S.text(T(STEM[0], STEM[1] - 12.2), 'cable hole 6 x 4', 1.4, col="#534AB7")
S.tag(T(STEM[0] + 22, STEM[1] + 14), "D3", "#534AB7")
cx, cy = T(*BUD_C)
S.o.append(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="33" ry="25.5" {ENGR}/>')
S.circ(T(*BUD_C), 21.5, INS)
S.text(T(BUD_C[0], BUD_C[1] + 3.5), 'BUDS PAD', 2.4, weight=600, col="#534AB7")
S.text(T(BUD_C[0], BUD_C[1]), 'oval 66 x 51, 1.5 deep', 1.5, col="#534AB7")
S.text(T(BUD_C[0], BUD_C[1] - 3.0), '5 W coil 43 behind 1.2', 1.5, col="#993C1D")
S.tag(T(BUD_C[0] - 30, BUD_C[1] - 20), "D4")
S.rect(T(WATCH[0] - 12, WATCH[1] + 12), T(WATCH[0] + 12, WATCH[1] - 12), 'fill="#CECBF6" fill-opacity="0.5" stroke="#534AB7" stroke-width="0.4"', rx=3)
for dy in (-7, 7): S.circ(T(WATCH[0] + 7, WATCH[1] + dy), 1.4, 'fill="#fff" stroke="#534AB7" stroke-width="0.3"')
S.rect(T(WATCH[0] - 8, WATCH[1] + 3), T(WATCH[0] - 2, WATCH[1] - 3), 'fill="#fff" stroke="#534AB7" stroke-width="0.3"')
S.text(T(WATCH[0], WATCH[1] + 15), 'WATCH STAND 24 x 24', 1.6, col="#534AB7", weight=600)
S.text(T(WATCH[0] - 16, WATCH[1] - 1), 'cable slot', 1.3, anchor="end", col="#534AB7")
S.tag(T(WATCH[0] + 16, WATCH[1] - 14), "D12", "#534AB7")
S.text(T(-78, 89), 'TOP DECK 160 x 95, fabric', 2.1, anchor="start", weight=600)
for x, lab in LEDS:
    S.circ(FR(x, 8), 1.0, HOLE); S.text((FR(x, 8)[0], FR(x, 8)[1] + 4.2), lab, 1.5)
S.text((FR(-77, 8)[0], FR(-77, 8)[1] + 0.8), 'FRONT 160 x 18', 1.8, anchor="start", weight=600)
S.tag((FR(25, 8)[0], FR(25, 8)[1]), "D9")
S.rect(BK(USB_IN_X - 5.4, 8 + 2.1), BK(USB_IN_X + 5.4, 8 - 2.1), CUT, rx=2)
S.text((BK(USB_IN_X, 0)[0], BK(0, 14.5)[1]), 'USB-C IN 100 W PD', 1.5, weight=600)
S.tag((BK(USB_IN_X + 11, 8)[0], BK(0, 8)[1]), "D7")
S.text((BK(30, 0)[0], BK(0, 10)[1]), 'BACK 160 x 18', 1.8, weight=600)
for typ, y, w, h in PORTS:
    S.rect(RE(y + w / 2, 8 + h / 2), RE(y - w / 2, 8 - h / 2), CUT, rx=0.8 if typ == 'USB-A' else 2)
    S.text(RE(y, 14.5), typ, 1.4, rot=90, weight=600)
S.text(RE(78, 9), 'RIGHT END: 3 ports', 1.7, rot=90, weight=600)
S.tag(RE(8, 8), "D8")
for i in range(4): S.rect(LE(35 + i * 8, 12), LE(39 + i * 8, 5), CUT, rx=0.8)
S.text(LE(80, 9), 'LEFT END: vents', 1.7, rot=-90, weight=600)
S.text((M, M), 'HeartSync DOCK, base net rev E (no cradle, phone both ways, watch stand), 1:1', 3.0, anchor="start", weight=600)
S.text((M, M + 4.4), '160 x 95 x 18 base · iPhone puck (landscape or portrait) · buds pad · watch/band stand · USB-A + 2 USB-C out · print 100 % on A4 landscape',
       1.9, anchor="start", col="#5F5E5A")
sy = Y0 + DD + DH + 10
S.scale(M, sy)
S.text((M + 66, sy + 1), 'Solid black = cut/hole · grey dash = fold · purple = ring, pad, stand feet · orange dots = part inside · blue dash = phone.', 1.8, anchor="start")
S.text((M + 66, sy + 5.2), 'D-numbers = dock BOM. Corners drawn square (real R6). Stem, puck, watch stand: sheet 2.', 1.8, anchor="start", col="#5F5E5A")
S.save('dock_net_revE.svg', VW1 + 4, sy + 12)
print('net', VW1 + 4, sy + 12)

# ======================= SHEET 2 =======================
S = Sheet(); VW2 = 420.0
IX0, IY0 = M + 10, M + 16
def I(x, y): return IX0 + DL / 2 + x, IY0 + DD - y
S.text((M, M), 'HeartSync DOCK rev E: inside 1:1, stem / puck / watch-stand parts 1:1, side view 1:2', 3.0, anchor="start", weight=600)
S.text((M, M + 4.4), 'Inside: seen from above with the deck lifted off, front at the bottom. Dashed = underside vents and feet.', 1.9, anchor="start", col="#5F5E5A")
S.rect(I(-80, 95), I(80, 0), 'fill="#FBFAF7" stroke="#111" stroke-width="0.45"', rx=6)
def box(x0, y0, x1, y1, fc, sc, op=0.6, rx=0):
    S.rect(I(x0, y0), I(x1, y1), f'fill="{fc}" fill-opacity="{op}" stroke="{sc}" stroke-width="0.35"', rx)
G, Qc, GR = ("#C0DD97", "#3B6D11"), ("#CECBF6", "#534AB7"), ("#D3D1C7", "#444441")
box(-75, 32, 0, 5, G[0], G[1], 0.55)
S.text(I(-37.5, 22), 'MAIN BOARD 75 x 27', 1.8, col=G[1], weight=600)
S.text(I(-37.5, 18.8), 'PD sink 100 W · fuse + TVS · bucks', 1.4, col=G[1])
S.text(I(-37.5, 16.2), '2-port PD + USB-A · LEDs · NTC', 1.4, col=G[1])
S.tag(I(-71, 9), "D1", G[1])
S.circ(I(*STEM), 20, 'fill="#CECBF6" fill-opacity="0.25" stroke="#534AB7" stroke-width="0.35" stroke-dasharray="1 0.8"')
box(-56, 72, -14, 42, G[0], G[1], 0.7)
S.text(I(-35, 59), 'phone Qi driver', 1.5, col=G[1], weight=600); S.text(I(-35, 56.4), 'cable up the stem', 1.3, col=G[1])
S.circ(I(*BUD_C), 21.5, f'fill="{Qc[0]}" fill-opacity="0.5" stroke="{Qc[1]}" stroke-width="0.4"')
S.text(I(BUD_C[0], BUD_C[1]), 'buds coil 43', 1.5, col=Qc[1], weight=600); S.tag(I(BUD_C[0], BUD_C[1] - 6), "D4", Qc[1])
box(-10, 88, 14, 62, G[0], G[1], 0.7); S.text(I(2, 75), 'buds driver', 1.4, col=G[1], weight=600)
box(20, 92, 48, 60, GR[0], GR[1], 0.35, rx=2); S.text(I(34, 77), 'watch cable', 1.4, weight=600); S.text(I(34, 74.6), 'bay (coils up)', 1.3)
box(48, 86, 70, 64, G[0], G[1], 0.7); box(53, 80, 65, 74, "#2C2C2A", "#2C2C2A", 0.85)
S.text(I(59, 83.5), 'internal USB', 1.3, col=G[1], weight=600); S.tag(I(59, 68), "D12", G[1])
box(64, 62, 80, 10, G[0], G[1], 0.7)
for typ, y, w, h in PORTS: box(80 - (14 if typ == 'USB-A' else 7.5), y + w / 2, 80, y - w / 2, "#2C2C2A", "#2C2C2A", 0.85)
S.tag(I(66, 6), "D8", G[1])
box(-78, 93, -60, 76, GR[0], GR[1], 0.8); S.text(I(-69, 84), 'steel', 1.4, weight=600); S.tag(I(-56, 80), "D11", GR[1])
box(USB_IN_X - 5.1, 95, USB_IN_X + 5.1, 87.2, "#2C2C2A", "#2C2C2A", 0.85); S.tag(I(USB_IN_X + 9, 90), "D7", GR[1])
for x, y in ((-74, 6), (74, 6), (-74, 89), (74, 89), (5, 48)):
    S.circ(I(x, y), 2.8, 'fill="#D3D1C7" stroke="#444441" stroke-width="0.3"'); S.circ(I(x, y), 1.6, 'fill="#fff"')
for x, y in ((-66, 12), (66, 12), (-66, 83), (66, 83)):
    S.circ(I(x, y), 5, 'fill="none" stroke="#444441" stroke-width="0.3" stroke-dasharray="1 0.8"')
for k in (-2, -1, 1, 2):
    S.rect(I(BUD_C[0] - 14, BUD_C[1] + k * 6 + 1), I(BUD_C[0] + 14, BUD_C[1] + k * 6 - 1), 'fill="none" stroke="#5F5E5A" stroke-width="0.25" stroke-dasharray="1 0.8"')
for x, _ in LEDS: S.circ(I(x, 3), 0.9, 'fill="#EF9F27"')
S.text(I(-78, -4.5), 'FRONT · grey circles = M3 bosses · dashed circles = rubber feet', 1.5, anchor="start", col="#5F5E5A")
S.text(I(-78, 98.5), 'BACK', 1.6, anchor="start", col="#5F5E5A", weight=600)

# ---- parts ----
PX, PY = IX0 + DL + 22, IY0 + 2
S.text((PX, PY), 'PARTS: flat patterns 1:1', 2.3, anchor="start", weight=600)
SH = PUCK_Z - 6 - (DH + 4)
S.rect((PX, PY + 6), (PX + 72.3, PY + 6 + SH), FAB); S.rect((PX, PY + 6), (PX + 72.3, PY + 6 + SH), CUT)
S.text((PX + 36, PY + 6 + SH / 2), 'STEM WRAP', 2.0, weight=600)
S.text((PX + 36, PY + 9.6 + SH / 2), '72.3 x %.0f (Ø23 tube)' % SH, 1.5, col="#444441"); S.tag((PX + 66, PY + 12), "D3", "#534AB7")
fx = PX + 112
S.circ((fx, PY + 26), 20, PET + ' stroke="#111" stroke-width="0.35"'); S.text((fx, PY + 26.6), 'STEM FOOT Ø40', 1.6, weight=600)
S.circ((fx + 54, PY + 38), 31, FAB + ' stroke="#111" stroke-width="0.35"'); S.circ((fx + 54, PY + 38), 28, ENGR); S.circ((fx + 54, PY + 38), 25, INS)
S.text((fx + 54, PY + 36), 'PHONE PUCK Ø62', 1.8, weight=600); S.text((fx + 54, PY + 39.4), 'round: phone turns', 1.4, col="#534AB7")
S.text((fx + 54, PY + 42), 'landscape or portrait', 1.4, col="#534AB7")
S.text((fx + 54, PY + 72), 'centre 110 up, tilted back 10°', 1.4, col="#444441")
for k in range(2):
    S.rect((PX + k * 100, PY + 96), (PX + k * 100 + 97.4, PY + 105), PET); S.rect((PX + k * 100, PY + 96), (PX + k * 100 + 97.4, PY + 105), CUT)
    S.text((PX + k * 100 + 48.7, PY + 101.4), 'PUCK RIM half %d: 97.4 x 9' % (k + 1), 1.5, weight=600)
# watch post net: front 18x56 centre, sides 14, back, top
wx, wy = PX, PY + 116
S.text((wx, wy - 2), 'WATCH STAND post 18 x 14 x 56 (leans back 15°) + holder Ø34', 1.8, anchor="start", weight=600)
xs = [wx, wx + 14, wx + 32, wx + 46, wx + 64]
for i, (a, b) in enumerate(zip(xs[:-1], xs[1:])):
    S.rect((a, wy + 14), (b, wy + 70), FAB if i == 1 else PET)
S.rect((xs[1], wy), (xs[2], wy + 14), PET)
S.poly([(xs[1], wy), (xs[2], wy), (xs[2], wy + 14), (xs[4], wy + 14), (xs[4], wy + 70), (xs[0], wy + 70), (xs[0], wy + 14), (xs[1], wy + 14)], CUT)
for x in xs[1:4]: S.line((x, wy + 14), (x, wy + 70), FOLD)
S.line((xs[1], wy + 14), (xs[2], wy + 14), FOLD)
S.text(((xs[1] + xs[2]) / 2, wy + 44), 'FRONT', 1.5, weight=600, rot=-90)
S.rect((xs[1] + 6, wy + 20), (xs[1] + 12, wy + 66), 'fill="none" stroke="#534AB7" stroke-width="0.3" stroke-dasharray="1 0.6"')
S.text(((xs[3] + xs[4]) / 2, wy + 44), 'BACK', 1.5, weight=600, rot=-90)
hx = wx + 92
S.circ((hx, wy + 30), 17, FAB + ' stroke="#111" stroke-width="0.35"'); S.circ((hx, wy + 30), 13.8, 'fill="#fff" stroke="#534AB7" stroke-width="0.4"')
S.text((hx, wy + 29), 'puck recess', 1.4, col="#534AB7", weight=600); S.text((hx, wy + 31.6), 'Ø27.6 x 7', 1.4, col="#534AB7")
S.text((hx, wy + 52), 'Apple Watch puck', 1.4, col="#444441"); S.text((hx, wy + 54.6), 'or band clip insert', 1.4, col="#444441")
S.text(((xs[1] + xs[2]) / 2 + 30, wy + 76), 'cable channel down the front (dashed) into the base', 1.4, col="#534AB7")
S.tag((hx + 21, wy + 14), "D12", "#534AB7")

# ---- side view 1:2 ----
SX0, SZ0 = M, IY0 + DD + 14
def SV(y, z): return SX0 + 12 + y / 2, SZ0 + 100 - z / 2
S.text((SX0, SZ0 + 2), 'SIDE VIEW 1:2 (from the right, front left; all parts projected)', 2.2, anchor="start", weight=600)
S.rect(SV(0, DH), SV(DD, 0), 'fill="#EADFCB" stroke="#444441" stroke-width="0.3"', rx=1)
S.rect(SV(STEM[1] - 11.5, PUCK_Z - 6), SV(STEM[1] + 11.5, DH), 'fill="#CECBF6" stroke="#534AB7" stroke-width="0.3"')
a = math.radians(TILT)
def rot(dy, dz): return (PUCK_Y + dy * math.cos(a) + dz * math.sin(a), PUCK_Z - dy * math.sin(a) + dz * math.cos(a))
S.poly([SV(*rot(*p)) for p in ((-4.5, -31), (4.5, -31), (4.5, 31), (-4.5, 31))], 'fill="#CECBF6" stroke="#534AB7" stroke-width="0.3"')
S.poly([SV(*rot(*p)) for p in ((-12.8, -81.5), (-4.5, -81.5), (-4.5, 81.5), (-12.8, 81.5))], 'fill="#B5D4F4" fill-opacity="0.5" stroke="#185FA5" stroke-width="0.3" stroke-dasharray="1.5 0.8"')
S.poly([SV(*rot(*p)) for p in ((-12.8, -39), (-4.5, -39), (-4.5, 39), (-12.8, 39))], 'fill="#B5D4F4" stroke="#185FA5" stroke-width="0.3"')
b = math.radians(15); wy0 = WATCH[1]
post = [(wy0 - 7, DH + 4), (wy0 + 7, DH + 4), (wy0 + 7 + 56 * math.sin(b), DH + 4 + 56 * math.cos(b)), (wy0 - 7 + 56 * math.sin(b), DH + 4 + 56 * math.cos(b))]
S.poly([SV(*p) for p in post], 'fill="#CECBF6" stroke="#534AB7" stroke-width="0.3"')
S.rect(SV(BUD_C[1] - 22.6, DH + 21.7), SV(BUD_C[1] + 22.6, DH), 'fill="#fff" stroke="#888780" stroke-width="0.3"', rx=4)
ptop = rot(-4.5, 81.5)[1]; pbot = rot(-12.8, -81.5)[1]; ltop = rot(-4.5, 39)[1]
for z, lab in ((ptop, 'portrait top %.0f' % ptop), (ltop, 'landscape top %.0f' % ltop), (DH + 4 + 56 * math.cos(b), 'watch stand %.0f' % (DH + 4 + 56 * math.cos(b))), (pbot, 'portrait bottom %.0f' % pbot), (DH, 'base 18')):
    S.line(SV(100, z), SV(110, z), 'stroke="#888780" stroke-width="0.2"'); S.text((SV(112, z)[0], SV(0, z)[1] + 0.7), lab, 1.5, anchor="start")
S.text((SV(0, 0)[0], SV(0, 0)[1] + 4), '95 deep · solid = landscape, dashed = portrait', 1.5, anchor="start", col="#444441")
S.scale(M + 120, IY0 + DD + 40)
S.text((PX, wy + 86), 'Power: one 100 W USB-C adapter → phone 15 + buds 5 + watch 5 W, plus up to 45 W shared by the 3 ports.', 1.9, anchor="start")
S.text((PX, wy + 90.4), 'The HeartSync charges from one of the USB-C ports (no cradle).', 1.9, anchor="start", col="#444441")
S.save('dock_inside_revE.svg', VW2, SZ0 + 108)
print('inside', VW2, SZ0 + 108, 'portrait top', round(ptop, 1), 'bottom', round(pbot, 1), 'landscape top', round(ltop, 1))
