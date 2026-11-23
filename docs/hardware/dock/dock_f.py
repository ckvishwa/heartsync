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


# ======================= rev F: Belkin-style pod. Tray 150 x 82 x 14 (R20), stadium column 62 x 40 x 114 =======================
L, W, H, R = 150.0, 82.0, 14.0, 20.0
COL, CW, CD, CH = (-35.0, 60.0), 62.0, 40.0, 114.0
PUCK_Z, WATCH_Z = 97.5, 108.0
BUD = (38.0, 30.0)
PORTS = [('USB-A', 28.0, 13.7, 6.3), ('USB-C', 42.0, 10.8, 4.2), ('USB-C', 55.0, 10.8, 4.2)]
USB_IN_X = 30.0
S = Sheet(); M = 14.0; VW = 420.0; VH = 297.0
def rr(x0, y0, w, h, r, st): S.rect((x0, y0), (x0 + w, y0 + h), st, rx=r)
def ell(c, rx, ry, st): S.o.append(f'<ellipse cx="{c[0]:.2f}" cy="{c[1]:.2f}" rx="{rx}" ry="{ry}" {st}/>')
S.text((M, M), 'HeartSync DOCK rev F (Belkin-style pod): every part flat, 1:1', 3.2, anchor="start", weight=600)
S.text((M, M + 4.4), 'Tray 150 x 82 x 14 · column 62 x 40 x 114 · iPhone puck on the front (landscape or portrait) · watch puck on the back · buds pad · USB-A + 2 USB-C out · print 100 % on A3 landscape',
       1.9, anchor="start", col="#5F5E5A")
# ---- A: tray top (seen from above, front at the bottom) ----
AX, AY = M, 30.0
def T(x, y): return AX + L / 2 + x, AY + W - y
S.text((AX, AY - 3), 'A  TRAY TOP 150 x 82, R20 corners (fabric or bare)', 2.2, anchor="start", weight=600)
rr(AX, AY, L, W, R, FAB + ' stroke="#111" stroke-width="0.4"')
rr(T(COL[0] - CW / 2, 0)[0], T(0, COL[1] + CD / 2)[1], CW, CD, CD / 2, 'fill="#CECBF6" fill-opacity="0.55" stroke="#534AB7" stroke-width="0.4"')
for dx in (-18, 18): S.circ(T(COL[0] + dx, COL[1]), 1.7, 'fill="#fff" stroke="#534AB7" stroke-width="0.3"')
S.rect(T(COL[0] - 4, COL[1] + 3), T(COL[0] + 4, COL[1] - 3), 'fill="#fff" stroke="#534AB7" stroke-width="0.3"')
S.text(T(COL[0], COL[1] + 8), 'COLUMN footprint 62 x 40', 1.6, col="#534AB7", weight=600)
S.text(T(COL[0], COL[1] - 7), '2 x M3 from below · cable hole 8 x 6', 1.3, col="#534AB7")
ell(T(*BUD), 33, 25.5, ENGR); S.circ(T(*BUD), 21.5, INS)
S.text(T(BUD[0], BUD[1] + 2), 'BUDS PAD', 2.2, col="#534AB7", weight=600)
S.text(T(BUD[0], BUD[1] - 1.5), 'oval 66 x 51, 1.5 deep', 1.4, col="#534AB7"); S.text(T(BUD[0], BUD[1] - 4.2), '5 W coil behind 1.2', 1.4, col="#993C1D")
S.rect(T(COL[0] - 39, 32), T(COL[0] + 39, 24), PHS, rx=2)
S.text(T(COL[0], 20.6), 'iPhone above (portrait 78 wide dashed; landscape 163, overhangs left 41)', 1.3, col="#185FA5")
S.tag(T(COL[0] + 34, COL[1] + 18), "D3", "#534AB7"); S.tag(T(BUD[0] + 30, BUD[1] - 22), "D4")
# ---- B: tray inside ----
S1 = S; S = Sheet()
S.text((M, M), 'HeartSync DOCK rev F: tray inside 1:1 + side view 1:2', 3.0, anchor='start', weight=600)
BX, BY = M, 30.0
def I(x, y): return BX + L / 2 + x, BY + W - y
S.text((BX, BY - 3), 'B  TRAY INSIDE (deck lifted off), front at the bottom', 2.2, anchor="start", weight=600)
rr(BX, BY, L, W, R, 'fill="#FBFAF7" stroke="#111" stroke-width="0.4"')
def box(x0, y0, x1, y1, fc, sc, op=0.6, rx=0): S.rect(I(x0, y0), I(x1, y1), f'fill="{fc}" fill-opacity="{op}" stroke="{sc}" stroke-width="0.35"', rx)
G, Qc, GR = ("#C0DD97", "#3B6D11"), ("#CECBF6", "#534AB7"), ("#D3D1C7", "#444441")
rr(I(COL[0] - CW / 2, 0)[0], I(0, COL[1] + CD / 2)[1], CW, CD, CD / 2, 'fill="none" stroke="#534AB7" stroke-width="0.35" stroke-dasharray="1 0.8"')
box(-60, 34, 4, 6, G[0], G[1], 0.6); S.text(I(-28, 23), 'MAIN BOARD 64 x 28', 1.6, col=G[1], weight=600)
S.text(I(-28, 20), 'PD sink 100 W · fuse · bucks', 1.3, col=G[1]); S.text(I(-28, 17.6), '2-port PD + USB-A · LED · NTC', 1.3, col=G[1])
S.tag(I(-52, 10), "D1", G[1])
S.circ(I(*BUD), 21.5, f'fill="{Qc[0]}" fill-opacity="0.5" stroke="{Qc[1]}" stroke-width="0.4"'); S.text(I(*BUD), 'buds coil', 1.5, col=Qc[1], weight=600)
box(4, 78, 30, 58, G[0], G[1], 0.7); S.text(I(17, 68), 'buds driver', 1.3, col=G[1], weight=600)
box(61, 61, 73, 21, G[0], G[1], 0.7)
for typ, y, w, h in PORTS: box(75 - (14 if typ == 'USB-A' else 7.5), y + w / 2, 74.5, y - w / 2, "#2C2C2A", "#2C2C2A", 0.85)
S.tag(I(58, 64), "D8", G[1])
box(USB_IN_X - 5.1, 82, USB_IN_X + 5.1, 74.2, "#2C2C2A", "#2C2C2A", 0.85); S.tag(I(USB_IN_X - 9, 77), "D7", GR[1])
box(-71, 56, -62, 36, GR[0], GR[1], 0.8); S.text(I(-66.5, 46), 'steel', 1.3, weight=600, rot=-90); S.tag(I(-58, 50), "D11", GR[1])
for x, y in ((-60, 8), (60, 8), (0, 74)): S.circ(I(x, y), 2.6, 'fill="#D3D1C7" stroke="#444441" stroke-width="0.3"'); S.circ(I(x, y), 1.5, 'fill="#fff"')
S.circ(I(0, 1.5), 0.9, 'fill="#EF9F27"')
# ---- C: tray side band, 4 strips ----
S2 = S; S = S1
CX, CY = M + L + 18, 30.0
S.text((CX, CY - 3), 'C  TRAY SIDE, unrolled in 4 strips (14 tall, top edge = deck)', 2.2, anchor="start", weight=600)
strips = [('FRONT (straight 110)', 110.0), ('RIGHT END (arc 31.4 + 42 + arc 31.4)', 104.8), ('BACK (straight 110)', 110.0), ('LEFT END (arc + 42 + arc)', 104.8)]
for k, (name, ln) in enumerate(strips):
    x0, y0 = CX + (k % 2) * 118, CY + 2 + (k // 2) * 26
    S.rect((x0, y0), (x0 + ln, y0 + H), PET); S.rect((x0, y0), (x0 + ln, y0 + H), CUT)
    S.text((x0, y0 + H + 3.4), name, 1.5, anchor="start", weight=600)
    if k == 1:
        for a in (31.4, 73.4): S.line((x0 + a, y0), (x0 + a, y0 + H), FOLD)
        for typ, y, w, h in PORTS:
            s = 31.4 + (y - 20)
            S.rect((x0 + s - w / 2, y0 + 7 - h / 2), (x0 + s + w / 2, y0 + 7 + h / 2), CUT, rx=0.8 if typ == 'USB-A' else 2)
            S.text((x0 + s, y0 + 2.6), typ, 1.2, weight=600)
        S.tag((x0 + 92, y0 + 7), "D8")
    if k == 0:
        S.circ((x0 + 55, y0 + 7), 1.0, HOLE); S.text((x0 + 55, y0 + 3), 'status light', 1.2); S.tag((x0 + 66, y0 + 7), "D9")
    if k == 2:
        xs = x0 + 55 - USB_IN_X
        S.rect((xs - 5.4, y0 + 7 - 2.1), (xs + 5.4, y0 + 7 + 2.1), CUT, rx=2); S.text((xs, y0 + 3), 'USB-C IN 100 W', 1.2, weight=600); S.tag((xs + 11, y0 + 7), "D7")
        S.text((x0 + 80, y0 + 11.5), '(read from behind: left = X +30)', 1.1, col="#444441")
    if k == 3:
        for a in (31.4, 73.4): S.line((x0 + a, y0), (x0 + a, y0 + H), FOLD)
        for i in range(4): S.rect((x0 + 38 + i * 8, y0 + 4), (x0 + 42 + i * 8, y0 + 10), CUT, rx=0.8)
        S.text((x0 + 52, y0 + 2.6), 'vents', 1.2)
# ---- D: column band + cap ----
DX, DY = M, 132.0
PER = 2 * (CW - CD) + math.pi * CD
S.text((DX, DY - 3), 'D  COLUMN WRAP %.1f x 114 (stadium 62 x 40), seam at the back centre' % PER, 2.2, anchor="start", weight=600)
S.rect((DX, DY), (DX + PER, DY + CH), FAB); S.rect((DX, DY), (DX + PER, DY + CH), CUT)
# from the back centre: back half-flat 11, arc 62.8 (right end), front flat 22, arc 62.8 (left end), back half-flat 11
marks = [11, 11 + math.pi * 20, 11 + math.pi * 20 + 22, 11 + 2 * math.pi * 20 + 22]
for a in marks: S.line((DX + a, DY), (DX + a, DY + CH), FOLD)
fc = DX + 11 + math.pi * 20 + 11                     # front centre
def Zb(z): return DY + CH - (z - H)
S.circ((fc, Zb(PUCK_Z)), 31, 'fill="none" stroke="#534AB7" stroke-width="0.35" stroke-dasharray="1.5 0.8"')
S.rect((fc - 4, Zb(PUCK_Z) - 3), (fc + 4, Zb(PUCK_Z) + 3), CUT); 
for dx in (-12, 12): S.circ((fc + dx, Zb(PUCK_Z)), 1.4, HOLE)
S.text((fc, Zb(PUCK_Z) + 9), 'phone puck Ø62 mounts here', 1.4, col="#534AB7", weight=600)
S.text((fc, Zb(PUCK_Z) + 11.6), 'centre 97.5 up from the table', 1.3, col="#534AB7")
S.text((fc, DY + CH - 4), 'FRONT', 1.6, weight=600)
for bx in (DX, DX + PER):
    S.circ((bx + (6 if bx == DX else -6), Zb(WATCH_Z)), 3.5 if False else 0.01, 'fill="none"')
S.rect((DX, Zb(WATCH_Z) - 3), (DX + 4, Zb(WATCH_Z) + 3), CUT); S.rect((DX + PER - 4, Zb(WATCH_Z) - 3), (DX + PER, Zb(WATCH_Z) + 3), CUT)
S.text((DX + 2, Zb(WATCH_Z) - 5), 'watch puck', 1.3, anchor="start", col="#534AB7", weight=600)
S.text((DX + 2, Zb(WATCH_Z) - 2.8), '(back centre, 108 up)', 1.2, anchor="start", col="#534AB7")
S.text((DX + 2, DY + CH - 4), 'BACK', 1.5, anchor="start", weight=600); S.text((DX + PER - 2, DY + CH - 4), 'BACK', 1.5, anchor="end", weight=600)
S.text((DX + 11 + math.pi * 10, DY + 40), 'RIGHT', 1.5, weight=600); S.text((DX + 11 + math.pi * 30 + 22, DY + 40), 'LEFT', 1.5, weight=600)
S.tag((fc + 26, Zb(PUCK_Z) - 30), "D3", "#534AB7")
cx0 = DX + PER + 8
rr(cx0, DY, CW, CD, CD / 2, PET + ' stroke="#111" stroke-width="0.35"'); S.text((cx0 + CW / 2, DY + CD / 2 + 0.6), 'COLUMN TOP 62 x 40', 1.4, weight=600)
# ---- E: pucks ----
EX, EY = cx0 + 110, DY + 36
S.circ((EX, EY), 31, FAB + ' stroke="#111" stroke-width="0.35"'); S.circ((EX, EY), 28, ENGR); S.circ((EX, EY), 25, INS)
S.text((EX, EY - 1), 'E  PHONE PUCK Ø62 x 8', 1.6, weight=600); S.text((EX, EY + 2), 'raised ring OD 56 · coil 50', 1.3, col="#534AB7")
S.text((EX, EY + 4.4), '+ magnet ring 56/44 inside', 1.3, col="#534AB7")
S.circ((EX + 60, EY), 16, PET + ' stroke="#111" stroke-width="0.35"'); S.circ((EX + 60, EY), 13.8, 'fill="#fff" stroke="#534AB7" stroke-width="0.4"')
S.text((EX + 60, EY - 0.6), 'WATCH PUCK Ø32', 1.3, weight=600); S.text((EX + 60, EY + 1.8), 'recess Ø27.6', 1.2, col="#534AB7"); S.tag((EX + 79, EY - 12), "D12", "#534AB7")
for k in range(2):
    x0 = DX + k * 100; y0 = DY + CH + 8
    S.rect((x0, y0), (x0 + 97.4, y0 + 8), PET); S.rect((x0, y0), (x0 + 97.4, y0 + 8), CUT)
    S.text((x0 + 48.7, y0 + 5), 'PHONE PUCK RIM half %d: 97.4 x 8' % (k + 1), 1.4, weight=600)
# ---- F: side view 1:2 ----
S1 = S; S = S2
FX, FY = M + L + 22, 22.0
def SV(y, z): return FX + 8 + y / 2, FY + 96 - z / 2
S.text((FX, FY - 2), 'F  SIDE VIEW 1:2 (from the right, front left)', 2.2, anchor="start", weight=600)
S.rect(SV(0, H), SV(W, 0), 'fill="#EADFCB" stroke="#444441" stroke-width="0.3"', rx=2)
S.rect(SV(COL[1] - CD / 2, H + CH), SV(COL[1] + CD / 2, H), 'fill="#CECBF6" stroke="#534AB7" stroke-width="0.3"', rx=6)
fr = COL[1] - CD / 2
S.rect(SV(fr - 8, PUCK_Z + 31), SV(fr, PUCK_Z - 31), 'fill="#CECBF6" stroke="#534AB7" stroke-width="0.3"')
S.rect(SV(fr - 16.3, PUCK_Z + 81.5), SV(fr - 8, PUCK_Z - 81.5), 'fill="#B5D4F4" fill-opacity="0.45" stroke="#185FA5" stroke-width="0.3" stroke-dasharray="1.5 0.8"')
S.rect(SV(fr - 16.3, PUCK_Z + 39), SV(fr - 8, PUCK_Z - 39), 'fill="#B5D4F4" stroke="#185FA5" stroke-width="0.3"')
bk = COL[1] + CD / 2
S.rect(SV(bk, WATCH_Z + 16), SV(bk + 4, WATCH_Z - 16), 'fill="#CECBF6" stroke="#534AB7" stroke-width="0.3"')
S.rect(SV(bk + 4, WATCH_Z + 23), SV(bk + 15, WATCH_Z - 23), 'fill="#888780" stroke="#444441" stroke-width="0.3"', rx=2)
S.rect(SV(BUD[1] - 22.6, H + 21.7), SV(BUD[1] + 22.6, H), 'fill="#fff" stroke="#888780" stroke-width="0.3"', rx=4)
for z, lab in ((PUCK_Z + 81.5, 'portrait top 179'), (PUCK_Z + 39, 'landscape top 136.5'), (H + CH, 'column 128'), (PUCK_Z - 39, 'landscape bottom 58.5'), (H, 'tray 14')):
    S.line(SV(100, z), SV(108, z), 'stroke="#888780" stroke-width="0.2"'); S.text((SV(110, z)[0], SV(0, z)[1] + 0.7), lab, 1.4, anchor="start")
S.text((SV(0, 0)[0], SV(0, 0)[1] + 4), '82 deep (+15 with the watch on the back)', 1.4, anchor="start", col="#444441")
S2 = S; S = S1
S.scale(M, VH - 20)
S.text((M + 66, VH - 19), 'D-numbers = dock BOM · solid black = cut / hole · grey dash = fold · purple = mount / ring · orange dots = part inside', 1.6, anchor="start")
S.text((M + 66, VH - 15.4), 'Power: one 100 W USB-C adapter → phone 15 + buds 5 + watch 5 W + up to 45 W shared by the 3 ports.', 1.6, anchor="start", col="#444441")
S.save('dock_parts_revF.svg', VW, VH)
S2.save('dock_inside_revF.svg', 297.0, 128.0)
print('ok', PER)
