"""HeartSync dock, rev A, 1:1. Dock axes: X across (right +), Y depth (front 0 -> back 145), Z up (deck top 22).
Sheet 1: net (top deck + 4 faces). Sheet 2: inside layout, cradle section 1:1, docked front view 1:2."""
import math

DL, DD, DH = 250.0, 145.0, 22.0          # dock length, depth, base height
PH_C, BUD_C = (-40.0, 46.0), (85.0, 46.0)
CR_O = (-97.2, 96.0, 97.2, 139.6)        # cradle outer
CR_I = (-93.2, 100.0, 93.2, 135.6)       # slot inside (device 185 x 34.3 incl. ring, 0.7 clear)
POGO_Y, MAG_Y = 117.3, 124.1
POGO_X, MAG_X = (-12, -4, 4, 12), (-70, -32, 32, 70)
USB_IN_X, USB_OUT_Y = -45.0, 59.0
FONT = 'font-family="IBM Plex Sans, Arial, sans-serif"'
CUT = 'fill="none" stroke="#111" stroke-width="0.35"'
HOLE = 'fill="#111"'
FOLD = 'fill="none" stroke="#5F5E5A" stroke-width="0.3" stroke-dasharray="2 1.2"'
ENGR = 'fill="none" stroke="#534AB7" stroke-width="0.35"'
INS = 'fill="none" stroke="#D85A30" stroke-width="0.3" stroke-dasharray="0.8 0.8"'
PH = 'fill="none" stroke="#185FA5" stroke-width="0.35" stroke-dasharray="3 1.5"'


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
        s.circ(p, 1.9, f'fill="#fff" stroke="{col}" stroke-width="0.35"'); s.text((p[0], p[1] + 0.85), n, 2.0, col=col, weight=600)
    def save(s, name, w, h):
        open(name, 'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.1f}mm" height="{h:.1f}mm" viewBox="0 0 {w:.1f} {h:.1f}">'
                              f'<rect width="{w:.1f}" height="{h:.1f}" fill="#fff"/>{"".join(s.o)}</svg>')


# =========================== SHEET 1: NET ===========================
S = Sheet(); M = 16.0
X0 = M + DH + 8                      # left edge of top deck (left end face unfolds to the left)
Y0 = M + 14 + DH                     # top edge (= BACK) of top deck; back face unfolds above
VW1 = 2 * X0 + DL
def T(x, y): return X0 + DL / 2 + x, Y0 + DD - y                  # top deck, front at the bottom
def FR(x, z): return X0 + DL / 2 + x, Y0 + DD + (DH - z)          # front face unfolded down (z=22 at the fold)
def BK(x, z): return X0 + DL / 2 + x, Y0 - (DH - z)               # back face unfolded up (seen from outside: flipped L/R? see note)
def LE(y, z): return X0 - (DH - z), Y0 + DD - y                   # left end unfolded left
def RE(y, z): return X0 + DL + (DH - z), Y0 + DD - y              # right end unfolded right

FAB, PET = 'fill="#EADFCB"', 'fill="#F6F4EE"'
S.rect((X0, Y0), (X0 + DL, Y0 + DD), FAB)
for a, b in (((X0, Y0 + DD), (X0 + DL, Y0 + DD + DH)), ((X0, Y0 - DH), (X0 + DL, Y0)),
             ((X0 - DH, Y0), (X0, Y0 + DD)), ((X0 + DL, Y0), (X0 + DL + DH, Y0 + DD))):
    S.rect(a, b, PET)
S.poly([(X0, Y0 - DH), (X0 + DL, Y0 - DH), (X0 + DL, Y0), (X0 + DL + DH, Y0), (X0 + DL + DH, Y0 + DD), (X0 + DL, Y0 + DD),
        (X0 + DL, Y0 + DD + DH), (X0, Y0 + DD + DH), (X0, Y0 + DD), (X0 - DH, Y0 + DD), (X0 - DH, Y0), (X0, Y0)], CUT)
for a, b in (((X0, Y0), (X0 + DL, Y0)), ((X0, Y0 + DD), (X0 + DL, Y0 + DD)), ((X0, Y0), (X0, Y0 + DD)), ((X0 + DL, Y0), (X0 + DL, Y0 + DD))):
    S.line(a, b, FOLD)

# --- top deck: phone pad ---
S.rect(T(PH_C[0] - 81.5, PH_C[1] + 39), T(PH_C[0] + 81.5, PH_C[1] - 39), PH, rx=8)
S.circ(T(*PH_C), 28, ENGR); S.circ(T(*PH_C), 27, ENGR); S.circ(T(*PH_C), 25, INS)
S.text(T(PH_C[0], PH_C[1] + 6), 'PHONE PAD', 3.2, weight=600, col="#534AB7")
S.text(T(PH_C[0], PH_C[1] + 2.4), 'Qi ring raised 0.4 under the fabric, OD 56', 1.8, col="#534AB7")
S.text(T(PH_C[0], PH_C[1] - 0.8), 'magnetic Qi module 15 W behind 1.2 mm deck', 1.8, col="#993C1D")
S.text(T(PH_C[0], PH_C[1] - 4.2), 'centre X -40, Y 46', 1.8, col="#444441")
S.text(T(PH_C[0] - 79, PH_C[1] - 36), 'iPhone lies flat, landscape (163 x 78 dashed)', 1.7, anchor="start", col="#185FA5")
S.tag(T(PH_C[0] + 22, PH_C[1] - 18), "D3")
# --- buds pad ---
S.circ(T(*BUD_C), 31, ENGR); S.circ(T(*BUD_C), 21.5, INS)
S.text(T(BUD_C[0], BUD_C[1] + 5), 'BUDS PAD', 3.0, weight=600, col="#534AB7")
S.text(T(BUD_C[0], BUD_C[1] + 1.5), 'dish 62, 1.5 deep', 1.8, col="#534AB7")
S.text(T(BUD_C[0], BUD_C[1] - 1.8), '5 W Qi coil 43 behind', 1.8, col="#993C1D")
S.text(T(BUD_C[0], BUD_C[1] - 5.0), 'centre X +85, Y 46', 1.8, col="#444441")
S.tag(T(BUD_C[0] + 24, BUD_C[1] - 24), "D4")
# --- cradle ---
S.rect(T(CR_O[0], CR_O[3]), T(CR_O[2], CR_O[1]), 'fill="#D3D1C7" stroke="#111" stroke-width="0.35"', rx=3)
S.rect(T(CR_I[0], CR_I[3]), T(CR_I[2], CR_I[1]), 'fill="#F6F4EE" stroke="#111" stroke-width="0.35"', rx=1.5)
for x in POGO_X:
    S.circ(T(x, POGO_Y), 1.0, HOLE)
for x in MAG_X:
    S.circ(T(x, MAG_Y), 3.1, INS)
for x in (-88, 88):
    S.circ(T(x, 104), 1.0, 'fill="none" stroke="#111" stroke-width="0.3"')
S.text(T(0, 131.0), 'CRADLE: HeartSync stands here on its bottom edge, back (ring) to the rear wall', 2.1, weight=600)
S.text(T(0, 112.0), '4 spring pogo pins (2.5 mm, 8 apart), 18.3 mm in from the rear wall', 1.8)
S.text(T(-51, 127.6), '4 magnets 6 x 2 under the 1 mm floor (opposite pole to the device)', 1.6, col="#993C1D")
S.text(T(-88, 107.5), 'drain', 1.4, col="#444441"); S.text(T(88, 107.5), 'drain', 1.4, col="#444441")
S.text(T(0, 102.2), 'slot 186.4 x 35.6 · walls 4 · rear wall 20 high, front lip 10, ends 14', 1.6, col="#444441")
S.tag(T(20, POGO_Y), "D5"); S.tag(T(78, MAG_Y), "D6")
S.text(T(122, 3.5), 'TOP DECK 250 x 145, fabric (cradle bare PETG)', 2.4, anchor="end", weight=600)
# --- front face: LEDs ---
for x, lab in ((-20, 'device'), (0, 'phone'), (20, 'buds')):
    S.circ(FR(x, 11), 1.0, HOLE); S.text((FR(x, 11)[0], FR(x, 11)[1] + 4.6), lab, 1.6)
S.text((FR(-90, 11)[0], FR(-90, 11)[1] + 0.8), 'FRONT 250 x 22: 3 status light pipes, 2 mm', 2.0, anchor="start", weight=600)
S.tag((FR(32, 11)[0], FR(32, 11)[1]), "D9")
# --- back face (seen from outside, unfolded upward: left/right as seen from the FRONT) ---
S.rect(BK(USB_IN_X - 5.4, 9 + 2.1), BK(USB_IN_X + 5.4, 9 - 2.1), CUT, rx=2)
S.text((BK(USB_IN_X, 0)[0], BK(0, 18)[1]), 'USB-C IN, 65 W PD (X -45: on the right when seen from behind)', 1.7, weight=600)
S.tag((BK(USB_IN_X + 12, 9)[0], BK(0, 9)[1]), "D7")
S.text((BK(30, 0)[0], BK(0, 11)[1]), 'BACK 250 x 22 (rear wall of the cradle rises above this)', 2.0, weight=600)
# --- ends ---
S.rect(RE(USB_OUT_Y + 5.4, 9 + 2.1), RE(USB_OUT_Y - 5.4, 9 - 2.1), CUT, rx=2)
S.text(RE(USB_OUT_Y - 20, 15.5), 'USB-C OUT (tablet) 20 W', 1.7, rot=90, weight=600)
S.tag(RE(USB_OUT_Y + 12, 11), "D8")
S.text(RE(110, 11), 'RIGHT END', 2.0, rot=90, weight=600)
for i in range(6):
    S.rect(LE(40 + i * 8, 15), LE(44 + i * 8, 7), CUT, rx=0.8)
S.text(LE(100, 11), 'LEFT END: 6 vent slots 4 x 8', 2.0, rot=-90, weight=600)
# title + scale
S.text((M, M), 'HeartSync DOCK, net rev A, 1:1', 3.4, anchor="start", weight=600)
S.text((M, M + 4.4), '250 x 145 x 22 base + cradle · charges HeartSync (pogo), iPhone (15 W Qi), buds (5 W Qi), tablet (USB-C) · print 100 % on A3 landscape',
       2.1, anchor="start", col="#5F5E5A")
sy = Y0 + DD + DH + 10
S.rect((M, sy), (M + 50, sy + 2), 'fill="#111"')
for i in range(6): S.line((M + 10 * i, sy - 1), (M + 10 * i, sy + 3), 'stroke="#111" stroke-width="0.25"')
S.text((M, sy + 7), '50 mm: measure after printing', 2.2, anchor="start")
leg = [("#111", "solid", "hole / cut"), ("#5F5E5A", "dash", "fold"), ("#534AB7", "solid", "raised ring / dish / groove"),
       ("#D85A30", "dot", "part inside"), ("#185FA5", "dash", "phone footprint")]
for i, (c, k, t) in enumerate(leg):
    x = M + 70 + (i % 3) * 70; y = sy + 1 + (i // 3) * 4.4
    S.line((x, y - 0.8), (x + 7, y - 0.8), f'stroke="{c}" stroke-width="0.5"' + (' stroke-dasharray="2 1.2"' if k == "dash" else ' stroke-dasharray="0.8 0.8"' if k == "dot" else ''))
    S.text((x + 9, y), t, 2.1, anchor="start")
S.text((M + 70, sy + 12), 'D-numbers = dock BOM lines. Corners drawn square (real R8).', 2.0, anchor="start", col="#5F5E5A")
S.save('dock_net_revA.svg', VW1, sy + 16)
print('net', VW1, sy + 16)

# =========================== SHEET 2: INSIDE + SECTION + FRONT VIEW ===========================
S = Sheet(); VW2 = 420.0
IX0, IY0 = M, M + 16
def I(x, y): return IX0 + DL / 2 + x, IY0 + DD - y
S.text((M, M), 'HeartSync DOCK, inside layout rev A, 1:1', 3.4, anchor="start", weight=600)
S.text((M, M + 4.4), 'Seen from above with the top deck lifted off. Front at the bottom. Underside vents and feet dashed.', 2.1, anchor="start", col="#5F5E5A")
S.rect(I(-125, 145), I(125, 0), 'fill="#FBFAF7" stroke="#111" stroke-width="0.45"', rx=8)
S.rect(I(-122.5, 142.5), I(122.5, 2.5), 'fill="none" stroke="#888780" stroke-width="0.25"', rx=6)
def box(x0, y0, x1, y1, fc, sc, op=0.6, rx=0):
    S.rect(I(x0, y0), I(x1, y1), f'fill="{fc}" fill-opacity="{op}" stroke="{sc}" stroke-width="0.35"', rx)
G, Qc, RD, GR = ("#C0DD97", "#3B6D11"), ("#CECBF6", "#534AB7"), ("#F7C1C1", "#A32D2D"), ("#D3D1C7", "#444441")
# coils
for c, ro, ri, lab, n in ((PH_C, 28, 22, 'phone Qi coil 50 + ring 56/44', "D3"), (BUD_C, 21.5, 0, 'buds coil 43', "D4")):
    S.circ(I(*c), ro, f'fill="{Qc[0]}" fill-opacity="0.45" stroke="{Qc[1]}" stroke-width="0.4"')
    if ri: S.circ(I(*c), ri, 'fill="#fff" fill-opacity="0.5" stroke="#534AB7" stroke-width="0.3" stroke-dasharray="1 0.8"')
    S.text(I(c[0], c[1] + 1), lab, 1.8, col=Qc[1], weight=600)
    S.text(I(c[0], c[1] - 2.2), 'ferrite down, 1.2 mm under the deck', 1.5, col=Qc[1])
    S.tag(I(c[0], c[1] - 7), n, Qc[1])
box(-118, 100, -73, 70, G[0], G[1]); S.text(I(-95.5, 87), 'phone Qi driver', 1.8, col=G[1], weight=600); S.text(I(-95.5, 84), '45 x 30 (with D3)', 1.5, col=G[1])
box(92, 92, 122, 72, G[0], G[1]); S.text(I(107, 83.5), 'buds driver', 1.7, col=G[1], weight=600); S.text(I(107, 80.6), '30 x 20', 1.5, col=G[1])
box(-55, 140, 55, 100, G[0], G[1], 0.55)
S.text(I(0, 132), 'MAIN DOCK BOARD 110 x 40 (under the cradle)', 2.1, col=G[1], weight=600)
S.text(I(0, 128.6), 'USB-C PD sink 65 W → 20 V bus · fuse + TVS · 2 buck rails · PD source for the tablet', 1.6, col=G[1])
S.text(I(0, 125.8), 'pogo power switch (on only when the device is seated) · LED driver · NTC inputs', 1.6, col=G[1])
S.tag(I(-50, 104), "D1", G[1])
box(-17, 121, 17, 113.5, "#2C2C2A", "#2C2C2A", 0.85)
for x in POGO_X: S.circ(I(x, POGO_Y), 1.0, 'fill="#C9A227"')
S.text(I(0, 109.8), 'pogo board → up through the slot floor', 1.5, col="#2C2C2A"); S.tag(I(22, POGO_Y), "D5", GR[1])
for x in MAG_X: S.rect(I(x - 3, MAG_Y + 1), I(x + 3, MAG_Y - 1), 'fill="#5F5E5A"')
S.tag(I(70, MAG_Y - 5), "D6", GR[1])
box(USB_IN_X - 5.1, 145, USB_IN_X + 5.1, 137.2, "#2C2C2A", "#2C2C2A", 0.85); S.tag(I(USB_IN_X - 9, 139), "D7", GR[1])
box(113, 68, 125, 50, G[0], G[1], 0.7); box(117, USB_OUT_Y + 5.1, 125, USB_OUT_Y - 5.1, "#2C2C2A", "#2C2C2A", 0.85)
S.text(I(111, 59), 'tablet port board', 1.4, anchor="end", col=G[1]); S.tag(I(108, 50), "D8", G[1])
for x in (-20, 0, 20): S.circ(I(x, 3.5), 1.0, 'fill="#EF9F27"')
S.text(I(0, 7.2), 'light pipes D9', 1.4, col="#854F0B")
for x0 in (100, -122):
    box(x0, 135, x0 + 22, 105, GR[0], GR[1], 0.7)
S.text(I(-111, 120), 'steel', 1.5, weight=600); S.text(I(-111, 117.4), 'weight', 1.5); S.text(I(111, 120), 'steel', 1.5, weight=600); S.text(I(111, 117.4), 'weight', 1.5)
S.tag(I(111, 110), "D11", GR[1])
for x, y in ((-115, 10), (115, 10), (-115, 135), (115, 135)):
    S.circ(I(x, y), 5, 'fill="none" stroke="#444441" stroke-width="0.3" stroke-dasharray="1 0.8"')
for x, y in ((-118, 6), (118, 6), (-118, 139), (118, 139), (0, 6), (0, 92)):
    S.circ(I(x, y), 2.8, 'fill="#D3D1C7" stroke="#444441" stroke-width="0.3"'); S.circ(I(x, y), 1.6, 'fill="#fff"')
for c, w in ((PH_C, 40), (BUD_C, 30), ((-37, 112), 26), ((37, 112), 26)):
    for k in (-3, -2, 2, 3):
        S.rect(I(c[0] - w / 2, c[1] + k * 5 + 1), I(c[0] + w / 2, c[1] + k * 5 - 1), 'fill="none" stroke="#5F5E5A" stroke-width="0.25" stroke-dasharray="1 0.8"')
S.text(I(-118, 140.5), 'BACK', 1.8, anchor="start", col="#5F5E5A", weight=600)
S.text(I(-118, -4.5), 'FRONT · dashed slots = underside vents · dashed circles = rubber feet · grey = M3 screw bosses', 1.7, anchor="start", col="#5F5E5A")
# wiring hints
for a, b in (((-73, 85), (-55, 110)), ((92, 82), (55, 110)), ((113, 59), (55, 104))):
    S.line(I(*a), I(*b), 'stroke="#A32D2D" stroke-width="0.35" stroke-dasharray="1.5 0.8"')
S.text(I(-62, 96), 'power + NTC', 1.4, col="#A32D2D", rot=-50); S.text(I(75, 97.5), 'power + NTC', 1.4, col="#A32D2D", rot=40)

# --- cradle section 1:1 (Y-Z cut at X = 0), placed right ---
CX0, CZ0 = IX0 + DL + 24, IY0 + 4
def C(y, z): return CX0 + (y - 90), CZ0 + 104 - z
S.text((CX0, CZ0 - 3), 'CRADLE SECTION at X = 0, 1:1 (front left)', 2.4, anchor="start", weight=600)
S.rect(C(90, 22), C(145, 0), 'fill="#F6F4EE" stroke="#444441" stroke-width="0.3"')
S.rect(C(96, 32), C(100, 22), 'fill="#D3D1C7" stroke="#444441" stroke-width="0.3"')
S.rect(C(135.6, 42), C(139.6, 22), 'fill="#D3D1C7" stroke="#444441" stroke-width="0.3"')
S.rect(C(100, 22), C(135.6, 21), 'fill="#D3D1C7"')
S.rect(C(101.3, 94.5), C(134.1, 22), 'fill="#EADFCB" fill-opacity="0.6" stroke="#2C2C2A" stroke-width="0.35"')
S.rect(C(134.1, 92), C(135.6, 24.5), 'fill="#444441"')
S.text(C(117.7, 70), 'HeartSync', 2.0, weight=600, rot=-90); S.text(C(121, 70), 'standing, 72.5 tall', 1.5, rot=-90)
S.text(C(104, 60), 'FRONT (display)', 1.4, rot=-90, col="#444441")
S.rect(C(116.3, 25), C(118.3, 16), 'fill="#C9A227"'); S.rect(C(121.1, 21), C(127.1, 19), 'fill="#5F5E5A"')
S.rect(C(102, 14), C(134, 5), 'fill="#C0DD97" stroke="#3B6D11" stroke-width="0.3"'); S.text(C(118, 8.5), 'main board', 1.5, col="#3B6D11")
S.text(C(137.6, 45.5), 'rear 20', 1.5, col="#444441"); S.text(C(98, 35.5), 'lip 10', 1.5, col="#444441")
S.text(C(117.3, 13.2), 'pogo', 1.3, col="#854F0B"); S.text(C(129, 17.2), 'magnet', 1.3, col="#444441", anchor="start")
S.text(C(90, -5), 'deck 22 · slot floor 1.0 over the magnets', 1.5, anchor="start", col="#444441")
S.text(C(90, -8), 'back ring rests on the rear wall; 1.3 mm play at the front', 1.5, anchor="start", col="#444441")

# --- docked front view 1:2 ---
FX0, FZ0 = IX0, IY0 + DD + 26
def F(x, z): return FX0 + (x + 125) / 2 + DL / 4, FZ0 + 60 - z / 2
S.text((FX0, FZ0 - 2), 'DOCKED, front view, 1:2', 2.6, anchor="start", weight=600)
S.rect(F(-125, 22), F(125, 0), 'fill="#EADFCB" stroke="#444441" stroke-width="0.3"', rx=2)
S.rect(F(-92.5, 94.5), F(92.5, 22), 'fill="#2C2C2A" stroke="#111" stroke-width="0.3"', rx=3)
S.rect(F(-85.9, 22 + 36.25 + 15.1), F(-6.1, 22 + 36.25 - 7.1), 'fill="#050505" stroke="#5F5E5A" stroke-width="0.3"')
S.text(F(-46, 22 + 36.25 + 2), 'I miss you', 2.4, col="#EF9F27", weight=600)
S.circ(F(45, 58.25), 14, 'fill="none" stroke="#534AB7" stroke-width="0.3"')
for i in range(5): S.rect(F(-68 + 9.8 * i - 2.6, 96), F(-68 + 9.8 * i + 2.6, 94.5), 'fill="#CBBFAE"')
for xc, w in ((38.5, 13.7), (52.75, 10.8), (66.05, 10.8)): S.rect(F(xc - w / 2, 95), F(xc + w / 2, 94.5), 'fill="#888780"')
S.rect(F(-97.2, 32), F(97.2, 22), 'fill="#D3D1C7" stroke="#444441" stroke-width="0.3"')
S.text(F(0, 25), 'cradle lip 10', 1.4, col="#444441")
S.rect(F(-121.5, 30), F(41.5, 22), 'fill="#B5D4F4" stroke="#185FA5" stroke-width="0.3"', rx=2)
S.text(F(-40, 30 + 3), 'iPhone lying flat', 1.6, col="#185FA5")
S.rect(F(70, 45), F(100, 22), 'fill="#fff" stroke="#888780" stroke-width="0.3"', rx=4)
S.text(F(85, 48), 'buds case', 1.6, col="#444441")
for x in (-20, 0, 20): S.circ(F(x, 11), 0.6, 'fill="#EF9F27"')
S.text(F(-125, -8), 'Total height docked 94.5 mm · footprint 250 x 145', 1.8, anchor="start", col="#444441")

# legend + notes
ly = FZ0 + 76
for i, ((fc, sc), t) in enumerate(((G, 'boards'), (Qc, 'Qi coils'), (GR, 'mechanical'), (RD, 'wiring'))):
    x = M + i * 60
    S.rect((x, ly - 2.4), (x + 6, ly + 0.6), f'fill="{fc}" stroke="{sc}" stroke-width="0.3"'); S.text((x + 8, ly), t, 2.0, anchor="start")
S.save('dock_inside_revA.svg', VW2, ly + 6)
print('inside', VW2, ly + 6)
