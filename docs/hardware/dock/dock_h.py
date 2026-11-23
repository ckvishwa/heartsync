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


# ======================= rev H: HeartSync landing strip in front (magnets + pogo, no walls) + Belkin-style pod behind =======================
L, W, H, R, RF = 195.0, 124.0, 14.0, 20.0, 8.0
COL, CW, CD, CH = (-35.0, 102.0), 62.0, 40.0, 146.0
PUCK_Z = 132.0
BAY, BAYW, BAYD, BAYH = (36.0, 111.0), 50.0, 24.0, 26.0
BUD = (38.0, 72.0)
PORTS = [('USB-A', 60.0, 13.7, 6.3), ('USB-C', 74.0, 10.8, 4.2), ('USB-C', 88.0, 10.8, 4.2)]
USB_IN_X = 70.0
DBACK, RING, DT = 40.0, 1.5, 32.8
POGO_Y, MAG_Y = DBACK - RING - 16.8, DBACK - RING - 10.0
POGO_X, MAG_X = (-12, -4, 4, 12), (-70, -32, 32, 70)
M = 14.0
def ell(S, c, rx, ry, st): S.o.append(f'<ellipse cx="{c[0]:.2f}" cy="{c[1]:.2f}" rx="{rx}" ry="{ry}" {st}/>')
def rr(S, x0, y0, w, h, r, st): S.rect((x0, y0), (x0 + w, y0 + h), st, rx=r)
def tray(S, x0, y0, st):   # screen: back at the top (R), front at the bottom (RF)
    w, h = L, W
    S.o.append(f'<path d="M{x0+R:.2f},{y0:.2f} H{x0+w-R:.2f} A{R},{R} 0 0 1 {x0+w:.2f},{y0+R:.2f} V{y0+h-RF:.2f} A{RF},{RF} 0 0 1 {x0+w-RF:.2f},{y0+h:.2f} '
               f'H{x0+RF:.2f} A{RF},{RF} 0 0 1 {x0:.2f},{y0+h-RF:.2f} V{y0+R:.2f} A{R},{R} 0 0 1 {x0+R:.2f},{y0:.2f} Z" {st}/>')

# ======================= SHEET 1: every part flat =======================
S = Sheet(); VW, VH = 420.0, 297.0
S.text((M, M), 'HeartSync DOCK rev H: HeartSync lands in front on magnets + pogo pins (no cradle), pod behind. Every part flat, 1:1', 2.9, anchor="start", weight=600)
S.text((M, M + 4.2), 'Tray 195 x 124 x 14 · landing strip (0.8 mm recess, no walls) · column 62 x 40 x 146 · iPhone puck 132 up (above the HeartSync) · buds pad · band bay · USB-A + 2 USB-C · print 100 % on A3 landscape',
       1.7, anchor="start", col="#5F5E5A")
AX, AY = M, 28.0
def T(x, y): return AX + L / 2 + x, AY + W - y
S.text((AX, AY - 2.5), 'A  TRAY TOP 195 x 124 (front corners R8, back R20)', 2.1, anchor="start", weight=600)
tray(S, AX, AY, FAB + ' stroke="#111" stroke-width="0.4"')
# landing strip
S.rect(T(-93.5, DBACK), T(93.5, 3.0), 'fill="#D3D1C7" fill-opacity="0.7" stroke="#534AB7" stroke-width="0.4"', rx=2)
S.rect(T(-92.5, DBACK - RING), T(92.5, DBACK - RING - DT), 'fill="none" stroke="#2C2C2A" stroke-width="0.3" stroke-dasharray="2 1"', rx=4)
for x in POGO_X: S.circ(T(x, POGO_Y), 1.25, HOLE)
for x in MAG_X: S.circ(T(x, MAG_Y), 3.1, INS)
S.text(T(0, 34.5), 'LANDING STRIP 187 x 37, 0.8 mm deep: the HeartSync stands here on its bottom edge, display to the front, back ring to the pod', 1.4, weight=600, col="#534AB7")
S.text(T(0, 11.5), 'no walls · 4 magnets 6 x 2 under 1 mm (opposite pole) pull it in · 4 spring pogo pins 2.5 rise 1 mm · dashed = device footprint', 1.3, col="#444441")
S.tag(T(20, POGO_Y), "D5"); S.tag(T(80, MAG_Y), "D6")
# column, buds, bay
rr(S, T(COL[0] - CW / 2, 0)[0], T(0, COL[1] + CD / 2)[1], CW, CD, CD / 2, 'fill="#CECBF6" fill-opacity="0.55" stroke="#534AB7" stroke-width="0.4"')
for dx in (-18, 18): S.circ(T(COL[0] + dx, COL[1]), 1.7, 'fill="#fff" stroke="#534AB7" stroke-width="0.3"')
S.rect(T(COL[0] - 4, COL[1] + 3), T(COL[0] + 4, COL[1] - 3), 'fill="#fff" stroke="#534AB7" stroke-width="0.3"')
S.text(T(COL[0], COL[1] + 8), 'COLUMN 62 x 40', 1.5, col="#534AB7", weight=600); S.text(T(COL[0], COL[1] - 7), '2 x M3 below · cable hole', 1.2, col="#534AB7")
S.tag(T(COL[0] + 34, COL[1] + 16), "D3", "#534AB7")
ell(S, T(*BUD), 33, 25.5, ENGR); S.circ(T(*BUD), 21.5, INS)
S.text(T(BUD[0], BUD[1] + 2), 'BUDS PAD', 2.0, col="#534AB7", weight=600); S.text(T(BUD[0], BUD[1] - 1.5), 'oval 66 x 51 · 5 W coil', 1.3, col="#534AB7")
S.tag(T(BUD[0] + 30, BUD[1] - 22), "D4")
S.rect(T(BAY[0] - BAYW / 2, BAY[1] + BAYD / 2), T(BAY[0] + BAYW / 2, BAY[1] - BAYD / 2), 'fill="#CECBF6" fill-opacity="0.55" stroke="#534AB7" stroke-width="0.4"', rx=2)
S.text(T(BAY[0], BAY[1] + 2), 'BAND BAY 50 x 24', 1.4, col="#534AB7", weight=600); S.text(T(BAY[0], BAY[1] - 3), 'USB-C pigtail hole', 1.2, col="#534AB7")
S.tag(T(BAY[0] + 29, BAY[1] + 6), "D12", "#534AB7")
# ---- C: tray side strips (stacked) ----
CX, CY = M + L + 18, 28.0
S.text((CX, CY - 2.5), 'C  TRAY SIDE, unrolled (14 tall, top edge = deck)', 2.1, anchor="start", weight=600)
FL, BL, EL = L - 2 * RF, L - 2 * R, W - RF - R
ARC, ARCF = math.pi * R / 2, math.pi * RF / 2
strips = [('FRONT (straight %.0f)' % FL, FL, 'front'), ('RIGHT END (arc %.1f + %.0f + arc %.1f)' % (ARCF, EL, ARC), ARCF + EL + ARC, 'right'),
          ('BACK (straight %.0f)' % BL, BL, 'back'), ('LEFT END (arc %.1f + %.0f + arc %.1f)' % (ARC, EL, ARCF), ARCF + EL + ARC, 'left')]
for k, (name, ln, kind) in enumerate(strips):
    x0, y0 = CX, CY + 2 + k * 23
    S.rect((x0, y0), (x0 + ln, y0 + H), PET); S.rect((x0, y0), (x0 + ln, y0 + H), CUT)
    S.text((x0, y0 + H + 3.2), name, 1.4, anchor="start", weight=600)
    if kind == 'right':
        for a in (ARCF, ARCF + EL): S.line((x0 + a, y0), (x0 + a, y0 + H), FOLD)
    if kind == 'left':
        for a in (ARC, ARC + EL): S.line((x0 + a, y0), (x0 + a, y0 + H), FOLD)
    if kind == 'front':
        S.circ((x0 + ln / 2, y0 + 7), 1.0, HOLE); S.text((x0 + ln / 2, y0 + 3), 'status light', 1.1); S.tag((x0 + ln / 2 + 10, y0 + 7), "D9")
    if kind == 'right':
        for typ, y, w, h in PORTS:
            s = ARCF + (y - RF)
            S.rect((x0 + s - w / 2, y0 + 7 - h / 2), (x0 + s + w / 2, y0 + 7 + h / 2), CUT, rx=0.8 if typ == 'USB-A' else 2)
            S.text((x0 + s, y0 + 2.6), typ, 1.1, weight=600)
        S.tag((x0 + ln - 12, y0 + 7), "D8")
    if kind == 'back':
        xs = x0 + ln / 2 - USB_IN_X
        S.rect((xs - 5.4, y0 + 7 - 2.1), (xs + 5.4, y0 + 7 + 2.1), CUT, rx=2); S.text((xs, y0 + 3), 'USB-C IN 100 W', 1.1, weight=600); S.tag((xs + 11, y0 + 7), "D7")
        S.text((x0 + ln - 2, y0 + 12), 'read from behind: left = X +70', 1.0, anchor="end", col="#444441")
    if kind == 'left':
        for i in range(5): S.rect((x0 + ARC + 22 + i * 8, y0 + 4), (x0 + ARC + 26 + i * 8, y0 + 10), CUT, rx=0.8)
        S.text((x0 + ARC + 40, y0 + 2.6), 'vents', 1.1)
# ---- D: column wrap ----
DX, DY = CX, 128.0
PER = 2 * (CW - CD) + math.pi * CD
S.text((DX, DY - 2.5), 'D  COLUMN WRAP %.1f x %.0f, seam at the back centre' % (PER, CH), 2.1, anchor="start", weight=600)
S.rect((DX, DY), (DX + PER, DY + CH), FAB); S.rect((DX, DY), (DX + PER, DY + CH), CUT)
for a in (11, 11 + math.pi * 20, 11 + math.pi * 20 + 22, 11 + 2 * math.pi * 20 + 22): S.line((DX + a, DY), (DX + a, DY + CH), FOLD)
fc = DX + 11 + math.pi * 20 + 11
def Zb(z): return DY + CH - (z - H)
S.circ((fc, Zb(PUCK_Z)), 31, 'fill="none" stroke="#534AB7" stroke-width="0.35" stroke-dasharray="1.5 0.8"')
S.rect((fc - 4, Zb(PUCK_Z) - 3), (fc + 4, Zb(PUCK_Z) + 3), CUT)
for dx in (-12, 12): S.circ((fc + dx, Zb(PUCK_Z)), 1.4, HOLE)
S.text((fc, Zb(PUCK_Z) + 9), 'phone puck Ø62 mounts here', 1.3, col="#534AB7", weight=600)
S.text((fc, Zb(PUCK_Z) + 11.4), 'centre 132 up from the table', 1.2, col="#534AB7")
S.text((fc, DY + CH - 4), 'FRONT', 1.5, weight=600)
S.text((DX + 2, DY + CH - 4), 'BACK', 1.4, anchor="start", weight=600); S.text((DX + PER - 2, DY + CH - 4), 'BACK', 1.4, anchor="end", weight=600)
S.text((DX + 11 + math.pi * 10, DY + 50), 'RIGHT', 1.4, weight=600); S.text((DX + 11 + math.pi * 30 + 22, DY + 50), 'LEFT', 1.4, weight=600)
S.tag((fc + 26, Zb(PUCK_Z) - 30), "D3", "#534AB7")
# ---- E: small parts, bottom-left ----
EX0, EY0 = M, AY + W + 12
S.text((EX0, EY0 - 2.5), 'E  COLUMN TOP, PHONE PUCK, BAND BAY', 2.1, anchor="start", weight=600)
rr(S, EX0, EY0, CW, CD, CD / 2, PET + ' stroke="#111" stroke-width="0.35"'); S.text((EX0 + CW / 2, EY0 + CD / 2 + 0.6), 'COLUMN TOP 62 x 40', 1.3, weight=600)
pc = (EX0 + CW + 38, EY0 + 31)
S.circ(pc, 31, FAB + ' stroke="#111" stroke-width="0.35"'); S.circ(pc, 28, ENGR); S.circ(pc, 25, INS)
S.text((pc[0], pc[1] - 1), 'PHONE PUCK Ø62 x 8', 1.5, weight=600); S.text((pc[0], pc[1] + 2), 'raised ring OD 56 · coil 50', 1.2, col="#534AB7")
S.text((pc[0], pc[1] + 4.4), '+ magnet ring 56/44 inside', 1.2, col="#534AB7")
fl = (EX0 + CW + 76, EY0 + 2)
S.rect(fl, (fl[0] + 46, fl[1] + 20), 'fill="#5F5E5A" fill-opacity="0.35" stroke="#111" stroke-width="0.35"', rx=1.5)
S.text((fl[0] + 23, fl[1] + 9.5), 'BAY FLOOR 46 x 20', 1.2, weight=600); S.text((fl[0] + 23, fl[1] + 12.2), 'rubber, cable hole', 1.1)
S.text((fl[0], fl[1] + 26), 'Bay insert (print one):', 1.2, anchor="start", weight=600)
S.text((fl[0], fl[1] + 29), '• WHOOP PowerPack 43 x 36 x 20', 1.1, anchor="start")
S.text((fl[0], fl[1] + 31.6), '• WHOOP Basic Charger', 1.1, anchor="start")
S.text((fl[0], fl[1] + 34.2), '• Fitbit Charge 6 clip cable', 1.1, anchor="start")
by0 = EY0 + 68
S.text((EX0, by0 - 2), 'BAND BAY walls unrolled 148 x 26 (front 18)', 1.4, anchor="start", weight=600)
xx = EX0
for nm, w, h in (('back 50', 50, 26), ('right 24', 24, 26), ('front 50', 50, 18), ('left 24', 24, 26)):
    S.rect((xx, by0 + 26 - h), (xx + w, by0 + 26), PET); S.rect((xx, by0 + 26 - h), (xx + w, by0 + 26), CUT)
    S.text((xx + w / 2, by0 + 26 - h / 2 + 0.5), nm, 1.1, weight=600); xx += w
for x in (EX0 + 50, EX0 + 74, EX0 + 124): S.line((x, by0 + 8), (x, by0 + 26), FOLD)
S.tag((EX0 + 152, by0 + 12), "D12", "#534AB7")
for k in range(2):
    x0, y0 = EX0 + k * 100, by0 + 34
    S.rect((x0, y0), (x0 + 97.4, y0 + 8), PET); S.rect((x0, y0), (x0 + 97.4, y0 + 8), CUT)
    S.text((x0 + 48.7, y0 + 5), 'PHONE PUCK RIM half %d: 97.4 x 8' % (k + 1), 1.3, weight=600)
S.scale(EX0, VH - 14)
S.text((EX0 + 60, VH - 13), 'D-numbers = dock BOM · black = cut / hole · grey dash = fold · purple = mount / ring / strip · orange dots = part inside', 1.4, anchor="start")
S.save('dock_parts_revH.svg', VW, VH)

# ======================= SHEET 2: inside + side view =======================
S = Sheet(); VW2, VH2 = 380.0, 168.0
S.text((M, M), 'HeartSync DOCK rev H: tray inside 1:1 + side view 1:2', 2.9, anchor="start", weight=600)
BX, BY = M, 30.0
def I(x, y): return BX + L / 2 + x, BY + W - y
S.text((BX, BY - 2.5), 'B  TRAY INSIDE (deck lifted off), front at the bottom', 2.0, anchor="start", weight=600)
tray(S, BX, BY, 'fill="#FBFAF7" stroke="#111" stroke-width="0.4"')
def box(x0, y0, x1, y1, fc, sc, op=0.6, rx=0): S.rect(I(x0, y0), I(x1, y1), f'fill="{fc}" fill-opacity="{op}" stroke="{sc}" stroke-width="0.35"', rx)
G, Qc, GR = ("#C0DD97", "#3B6D11"), ("#CECBF6", "#534AB7"), ("#D3D1C7", "#444441")
box(-62, 46, 2, 8, G[0], G[1], 0.55)
S.text(I(-30, 40), 'MAIN BOARD 64 x 38', 1.6, col=G[1], weight=600)
S.text(I(-30, 37), 'PD sink 100 W · fuse · bucks · 2-port PD + USB-A', 1.2, col=G[1])
S.text(I(-30, 34.6), 'pogo power switch (on only when the HeartSync sits) · LED · NTC', 1.2, col=G[1])
S.tag(I(-56, 12), "D1", G[1])
box(-17, POGO_Y + 3.7, 17, POGO_Y - 3.7, "#2C2C2A", "#2C2C2A", 0.85)
for x in POGO_X: S.circ(I(x, POGO_Y), 1.0, 'fill="#C9A227"')
S.tag(I(21, POGO_Y), "D5", GR[1])
for x in MAG_X: S.rect(I(x - 3, MAG_Y + 1), I(x + 3, MAG_Y - 1), 'fill="#5F5E5A"')
S.tag(I(78, MAG_Y), "D6", GR[1])
rr(S, I(COL[0] - CW / 2, 0)[0], I(0, COL[1] + CD / 2)[1], CW, CD, CD / 2, 'fill="none" stroke="#534AB7" stroke-width="0.35" stroke-dasharray="1 0.8"')
S.text(I(COL[0], COL[1]), 'column above (phone Qi driver inside it)', 1.2, col="#534AB7")
S.circ(I(*BUD), 21.5, f'fill="{Qc[0]}" fill-opacity="0.5" stroke="{Qc[1]}" stroke-width="0.4"'); S.text(I(*BUD), 'buds coil', 1.4, col=Qc[1], weight=600)
box(8, 100, 30, 82, G[0], G[1], 0.7); S.text(I(19, 91), 'buds driver', 1.2, col=G[1], weight=600)
box(40, 120, 62, 102, G[0], G[1], 0.7); S.text(I(51, 112), 'bay USB-C', 1.2, col=G[1], weight=600); S.tag(I(51, 106), "D12", G[1])
box(83, 100, 95, 50, G[0], G[1], 0.7)
for typ, y, w, h in PORTS: box(97.5 - (14 if typ == 'USB-A' else 7.5), y + w / 2, 97, y - w / 2, "#2C2C2A", "#2C2C2A", 0.85)
S.tag(I(80, 48), "D8", G[1])
box(USB_IN_X - 5.1, 124, USB_IN_X + 5.1, 116.2, "#2C2C2A", "#2C2C2A", 0.85); S.tag(I(USB_IN_X - 9, 119), "D7", GR[1])
box(-94, 104, -80, 60, GR[0], GR[1], 0.8); S.text(I(-87, 82), 'steel', 1.3, weight=600, rot=-90); S.tag(I(-76, 64), "D11", GR[1])
for x, y in ((-80, 8), (80, 8), (-75, 116), (80, 116), (10, 60)): S.circ(I(x, y), 2.6, 'fill="#D3D1C7" stroke="#444441" stroke-width="0.3"'); S.circ(I(x, y), 1.5, 'fill="#fff"')
S.circ(I(0, 1.5), 0.9, 'fill="#EF9F27"')
# side view 1:2
FX, FY = M + L + 22, 14.0
def SV(y, z): return FX + 8 + y / 2, FY + 116 - z / 2
S.text((FX, FY + 6), 'F  SIDE VIEW 1:2 (from the right, front left)', 2.0, anchor="start", weight=600)
S.rect(SV(0, H), SV(W, 0), 'fill="#EADFCB" stroke="#444441" stroke-width="0.3"', rx=2)
S.rect(SV(DBACK - RING - DT, H + 72.5), SV(DBACK - RING, H), 'fill="#2C2C2A" stroke="#111" stroke-width="0.3"', rx=2)
S.rect(SV(DBACK - RING, H + 69), SV(DBACK, H + 3.5), 'fill="#444441"')
S.rect(SV(COL[1] - CD / 2, H + CH), SV(COL[1] + CD / 2, H), 'fill="#CECBF6" stroke="#534AB7" stroke-width="0.3"', rx=6)
fr = COL[1] - CD / 2
S.rect(SV(fr - 8, PUCK_Z + 31), SV(fr, PUCK_Z - 31), 'fill="#CECBF6" stroke="#534AB7" stroke-width="0.3"')
S.rect(SV(fr - 16.3, PUCK_Z + 81.5), SV(fr - 8, PUCK_Z - 81.5), 'fill="#B5D4F4" fill-opacity="0.45" stroke="#185FA5" stroke-width="0.3" stroke-dasharray="1.5 0.8"')
S.rect(SV(fr - 16.3, PUCK_Z + 39), SV(fr - 8, PUCK_Z - 39), 'fill="#B5D4F4" stroke="#185FA5" stroke-width="0.3"')
S.rect(SV(BAY[1] - BAYD / 2, H + BAYH), SV(BAY[1] + BAYD / 2, H), 'fill="#CECBF6" fill-opacity="0.6" stroke="#534AB7" stroke-width="0.3"')
S.rect(SV(BUD[1] - 22.6, H + 21.7), SV(BUD[1] + 22.6, H), 'fill="#fff" stroke="#888780" stroke-width="0.3"', rx=4)
for z, lab in ((PUCK_Z + 81.5, 'portrait top 213'), (PUCK_Z + 39, 'landscape top 171'), (H + CH, 'column 160'), (PUCK_Z - 39, 'landscape bottom 93'), (H + 72.5, 'HeartSync 86.5'), (H, 'tray 14')):
    S.line(SV(130, z), SV(138, z), 'stroke="#888780" stroke-width="0.2"'); S.text((SV(140, z)[0], SV(0, z)[1] + 0.6), lab, 1.3, anchor="start")
S.text((SV(0, 0)[0], SV(0, 0)[1] + 4), '124 deep · HeartSync front, pod behind', 1.3, anchor="start", col="#444441")
S.text((M, VH2 - 6), 'Power: one 100 W USB-C adapter → HeartSync 18 (pogo) + phone 15 + buds 5 + band 5 W + up to 45 W shared by the 3 ports.', 1.5, anchor="start", col="#444441")
S.save('dock_inside_revH.svg', VW2, VH2)
print('ok')
