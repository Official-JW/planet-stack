"""Cargo Dock layout v2 (Refinery | Cargo Dock | Launch Pad ... Shipyard): top-down plan still + slot plan.
Inputs: wmap.bin/json from hmap.mjs (0.5 m max-height raster of the station GLBs placed at the proposed world positions).
python3 layout.py WMAP_PREFIX OUT.png SLOTS.json"""
import json, sys, math, numpy as np
from PIL import Image, ImageDraw, ImageFont
P, OUT, SJ = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(P + '.json')); NX, NZ, C, X0, Z0 = d['NX'], d['NZ'], d['C'], d['X0'], d['Z0']
raw = np.fromfile(P + '.bin', dtype=np.uint8)
H = np.frombuffer(raw[:NX * NZ * 4].tobytes(), dtype=np.float32).reshape(NZ, NX).copy()
ID = np.frombuffer(raw[NX * NZ * 4:].tobytes(), dtype=np.int16).reshape(NZ, NX)
INFO = {i['name']: i for i in d['info']}; NAMES = [i['name'] for i in d['info']]
COL = {'Refinery': (224, 214, 190), 'Bridge': (120, 200, 230), 'Crane': (240, 180, 90), 'Dock': (200, 225, 255), 'LaunchPad': (230, 230, 236), 'Shipyard': (215, 205, 235)}
F = lambda s, b=False: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if b else ''), s)
DOCK = (373.0, -8.0); PAD = (457.0, 0.0); REF = 320.0; SY = 960.0
S = json.load(open(SJ))

def shade(x0, x1, z0, z1, ppm):
    a, b, c, e = [int(round(v)) for v in ((x0 - X0) / C, (x1 - X0) / C, (z0 - Z0) / C, (z1 - Z0) / C)]
    h = H[c:e, a:b]; idd = ID[c:e, a:b]
    gy, gx = np.gradient(np.maximum(h, 0))
    lam = np.clip(0.75 - 0.35 * gx + 0.35 * gy, 0.35, 1.15)
    rgb = np.zeros(h.shape + (3,), np.float32); rgb[:] = (52, 56, 62)
    for k, n in enumerate(NAMES):
        m = (idd == k) & (h > 0.12); rgb[m] = np.array(COL[n], np.float32) * (0.55 + 0.45 * np.clip(h[m] / 15, 0, 1))[:, None]
        m2 = (idd == k) & (h > 0.02) & (h <= 0.12); rgb[m2] = (78, 82, 90)
    rgb *= lam[..., None]
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).resize((int((x1 - x0) * ppm), int((z1 - z0) * ppm)), Image.BILINEAR)
    return im

class Panel:
    def __init__(s, img, ox, oy, x0, z0, ppm): s.d = ImageDraw.Draw(img, 'RGBA'); s.ox, s.oy, s.x0, s.z0, s.k = ox, oy, x0, z0, ppm
    def p(s, x, z): return (s.ox + (x - s.x0) * s.k, s.oy + (z - s.z0) * s.k)
    def line(s, pts, col, w=2, dash=None):
        P_ = [s.p(*q) for q in pts]
        if not dash: s.d.line(P_, fill=col, width=w, joint='curve'); return
        for (a, b) in zip(P_, P_[1:]):
            L = math.dist(a, b); n = max(1, int(L / dash))
            for i in range(0, n, 2):
                t0, t1 = i / n, min(1, (i + 1) / n); s.d.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)], fill=col, width=w)
    def rect(s, x0, z0, x1, z1, col, fill=None, w=2):
        a, b = s.p(x0, z0), s.p(x1, z1); s.d.rectangle([min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])], outline=col, fill=fill, width=w)
    def text(s, x, z, t, col=(255, 255, 255), sz=16, b=False, anchor='mm', bg=(0, 0, 0, 150)):
        q = s.p(x, z); f = F(sz, b); bb = s.d.textbbox(q, t, font=f, anchor=anchor)
        if bg: s.d.rectangle([bb[0] - 3, bb[1] - 2, bb[2] + 3, bb[3] + 2], fill=bg)
        s.d.text(q, t, font=f, fill=col, anchor=anchor)

def arc(cx, cz, r, a0, a1, n=24): return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cz + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
W = 1720
A = dict(x0=288, x1=496, z0=-50, z1=30, k=8)
Bv = dict(x0=270, x1=1030, z0=-52, z1=52, k=2.2)
img = Image.new('RGB', (W, 1960), (24, 26, 30)); dr = ImageDraw.Draw(img)
dr.text((20, 14), 'Planet Stack - Cargo Dock layout v2 (proposal, top-down, world metres, +X right, camera side +Z = down)', font=F(26, True), fill=(255, 255, 255))
dr.text((20, 48), 'Order: ... Mine | Refinery | CARGO DOCK | LAUNCH PAD | Habitat | Shipyard.  Refinery x 320 (unchanged)  ->  Cargo Dock x 373, z -8  ->  Launch Pad x 457  ->  Shipyard x 960 (unchanged).', font=F(17), fill=(220, 225, 235))
# ---------- panel A
oy = 90; ia = shade(A['x0'], A['x1'], A['z0'], A['z1'], A['k']); img.paste(ia, (40, oy)); pa = Panel(img, 40, oy, A['x0'], A['z0'], A['k'])
for x in range(290, 497, 10): pa.d.line([pa.p(x, A['z1']), (pa.p(x, A['z1'])[0], pa.p(x, A['z1'])[1] + (8 if x % 50 == 0 else 4))], fill=(200, 200, 200), width=1)
for x in range(300, 497, 50): pa.text(x, A['z1'] + 2.2, 'x %d' % x, sz=13, bg=None, col=(190, 190, 200))
for z in range(-50, 31, 10): pa.text(A['x0'] - 0.2, z, 'z %d' % z, sz=12, anchor='rm', bg=None, col=(190, 190, 200))
# haul road (Mine -> Refinery, HT-04): lanes z 9 in / z 0 out from x 274, Refinery U-turn Truck_Path_03..07 r 4.5 about (316.5, 4.5)
HR = (255, 150, 60)
pa.line([(288, 9), (316.5, 9)], HR, 4); pa.line(arc(316.5, 4.5, 4.5, -math.pi / 2, math.pi / 2), HR, 4); pa.line([(316.5, 0), (288, 0)], HR, 4, dash=10)
pa.text(296, 4.5, 'HAUL ROAD (HT-04, Mine->Refinery) z 9 in / z 0 out, U-turn r4.5', col=HR, sz=13, anchor='lm')
# flatbed FB-05 route: lanes z 13 (loaded, east) / z 22 (empty, west), U-turns r 4.5 at x 295 and the pad Road_UTurn x 458
FBc = (90, 230, 120); ux = PAD[0] + 1
pa.line([(318, 13), (ux, 13)], FBc, 4); pa.line(arc(ux, 17.5, 4.5, -math.pi / 2, math.pi / 2), FBc, 4); pa.line([(ux, 22), (295, 22)], FBc, 4)
pa.line(arc(295, 17.5, 4.5, math.pi / 2, 1.5 * math.pi), FBc, 4); pa.line([(295, 13), (318, 13)], FBc, 4)
pa.d.rectangle([*pa.p(288, 10.2), *pa.p(496, 24.8)], outline=(90, 230, 120, 90), width=1)
pa.text(395, 17.5, 'FLATBED FB-05 route: z 13 east (loaded) / z 22 west (empty), road band z 10.2-24.8, tiles x 296-464 (21 x 8 m)', col=FBc, sz=13)
pa.text(318, 13, 'load x318', col=FBc, sz=12, bg=(0, 0, 0, 200)); pa.text(PAD[0] - 3.5, 13, 'Truck_Stop x453.5', col=FBc, sz=12, bg=(0, 0, 0, 200))
pa.text(ux + 6.5, 17.5, 'PAD U-TURN r4.5 @ x458', col=FBc, sz=12, anchor='lm')
# transport road start (pad right, far side)
TR = (255, 90, 200); pa.line([(PAD[0], -13), (496, -13)], TR, 5); pa.d.rectangle([*pa.p(PAD[0], -31), *pa.p(496, 5)], outline=(255, 90, 200, 160), width=2)
pa.text(489, -40, 'PLANNED TRANSPORT ROAD ->', col=TR, sz=13, anchor='rm'); pa.text(489, -36.5, 'ship axis z -13, 36 m corridor (ST-10)', col=TR, sz=12, anchor='rm')
# station labels + origins
def lab(x, z, t, sub): pa.text(x, z, t, sz=20, b=True, bg=(0, 0, 0, 170)); pa.text(x, z + 3.2, sub, sz=12, bg=(0, 0, 0, 170), col=(220, 220, 230))
lab(304, -40, 'REFINERY', 'origin x 320 (unchanged)'); lab(329, 27, 'BRIDGE bc081489', 'x 318.1-338.3, z 4.3-19.2')
lab(385, -40, 'CARGO DOCK', 'origin x 373, z -8 | x 348.3-421.0, z -44.3..8.9'); lab(457, -46, 'LAUNCH PAD', 'origin x 457 | x 427.6-486.4')
for (x, z) in ((320, 0), (DOCK[0], DOCK[1]), (PAD[0], 0)):
    q = pa.p(x, z); pa.d.ellipse([q[0] - 5, q[1] - 5, q[0] + 5, q[1] + 5], outline=(255, 255, 0), width=2)
# spacing dims
def dim(x0, x1, z, t):
    pa.line([(x0, z), (x1, z)], (255, 255, 0), 1); [pa.line([(x, z - 1.2), (x, z + 1.2)], (255, 255, 0), 1) for x in (x0, x1)]; pa.text((x0 + x1) / 2, z - 2.3, t, col=(255, 255, 0), sz=12, bg=(0, 0, 0, 180))
dim(338.25, 343.7, -1.5, '5.45 m'); dim(421.0, 427.6, -2, '6.6 m'); dim(320, 373, -48.5, 'origin spacing 53 m'); dim(373, 457, -48.5, '84 m')
# storage apron + slots
for s_ in S['slots']:
    x, y, z = s_['world']
    if s_['tier'] == 1: pa.rect(x - 1.2, z - 0.67, x + 1.2, z + 0.67, (255, 220, 60), fill=(255, 200, 40, 160), w=1)
for r in S['future_rows']:
    for x in S['col_x']: pa.rect(x + DOCK[0] - 1.2, r + DOCK[1] - 0.67, x + DOCK[0] + 1.2, r + DOCK[1] + 0.67, (255, 220, 60, 140), w=1)
ap = S['apron']; pa.rect(ap[0] + DOCK[0], ap[2] + DOCK[1], ap[1] + DOCK[0], ap[3] + DOCK[1], (255, 220, 60), w=2)
pa.text(350.7, -9.5, 'STORAGE APRON: 20 slots (5 x 2 x 2 high)', col=(255, 220, 60), sz=12); pa.text(350.7, -7.5, 'dashed = room for more rows', col=(255, 220, 60), sz=11)
# pipes
pa.line([(335.9, -18.62), (373 + 14.5, -8 - 12.6)], (120, 160, 255, 200), 2, dash=6); pa.line([(420, 0.1), (477.3, -9.6)], (120, 160, 255, 200), 2, dash=6)
pa.text(452, -27, 'buried fuel line dock->pad (57 m, under the pad)', col=(150, 180, 255), sz=11)
# ---------- panel B overview
oyb = oy + ia.size[1] + 70; ib = shade(Bv['x0'], Bv['x1'], Bv['z0'], Bv['z1'], Bv['k']); img.paste(ib, (40, oyb)); pb = Panel(img, 40, oyb, Bv['x0'], Bv['z0'], Bv['k'])
dr.text((40, oyb - 30), 'Overview x 270-1030: planned transport road (ST-10 ship transporter, 36 m corridor as in vehicles/ship_transporter build_road half=18)', font=F(16, True), fill=(255, 255, 255))
pb.line([(288, 13), (ux, 13)], FBc, 2); pb.line([(ux, 22), (288, 22)], FBc, 2); pb.line([(274, 9), (316, 9)], HR, 2); pb.line([(274, 0), (316, 0)], HR, 2)
TRP = [(457, -13), (700, -13)] + [(700 + 40 * t, -13 - 11 * (1 - math.cos(math.pi * t)) / 2) for t in [i / 10 for i in range(11)]] + [(830, -24)] + \
      [(830 + 55 * t, -24 + 36 * (1 - math.cos(math.pi * t)) / 2) for t in [i / 12 for i in range(13)]] + [(925, 12)] + arc(925, -4, 16, math.pi / 2, 0, 12)[1:]
TRP = TRP[:-1] + [(941, 8.4), (940.6, 4.9)]
for w_, col in ((36 * Bv['k'], (255, 90, 200, 60)), (4, TR)): pb.d.line([pb.p(*q) for q in TRP], fill=col, width=int(w_), joint='curve')
pb.rect(795.5, -4.5, 804.5, 4.5, (200, 200, 200), fill=(140, 140, 150, 255)); pb.text(800, 10, 'Habitat (gray placeholder 9x12x9 @ x800)', sz=11)
pb.text(320, -45, 'REFINERY', sz=13, b=True); pb.text(385, -48, 'CARGO DOCK', sz=13, b=True); pb.text(457, 35, 'LAUNCH PAD', sz=13, b=True); pb.text(965, -45, 'SHIPYARD (x 960)', sz=13, b=True)
pb.text(941, 30, 'Hall_Door (940.6, 4.9), opening 10.3 m', col=TR, sz=11); pb.text(640, -36, 'transport road: z -13 -> z -24 past Habitat -> z +12 -> Hall_Door', col=TR, sz=12)
# ---------- panel C slots
oyc = oyb + ib.size[1] + 70; k = 46; x0l, x1l, z0l, z1l = -30.5, -13.5, 0.0, 17.5
dr.text((40, oyc - 30), 'Slot plan (Dock-local metres; world = local + (373, 0, -8)). Slot_NN = box Base (bottom centre), box 2.4 x 1.34 x 1.5 m, long axis X. Lv1 cap 20.', font=F(16, True), fill=(255, 255, 255))
ic = shade(x0l + DOCK[0], x1l + DOCK[0], z0l + DOCK[1], z1l + DOCK[1], k); img.paste(ic, (40, oyc)); pc = Panel(img, 40, oyc, x0l, z0l, k)
pc.rect(ap[0], ap[2], ap[1], ap[3], (255, 220, 60), w=3)
for r in S['future_rows']:
    for x in S['col_x']: pc.rect(x - 1.2, r - 0.67, x + 1.2, r + 0.67, (255, 220, 60, 150), w=1)
pc.text(-22.3, S['future_rows'][-1] - 1.4, 'future rows (Director sets the max): +10 slots per row at 2 high', col=(255, 220, 60), sz=13)
for s_ in S['slots']:
    x, y, z = s_['local']
    if s_['tier'] == 1:
        pc.rect(x - 1.2, z - 0.67, x + 1.2, z + 0.67, (255, 230, 90), fill=(255, 190, 40, 190), w=2)
        top = [t for t in S['slots'] if t['tier'] == 2 and t['local'][0] == x and t['local'][2] == z][0]
        pc.text(x, z - 0.2, s_['name'][5:] + ' / ' + top['name'][5:], col=(20, 20, 20), sz=15, b=True, bg=None)
        pc.text(x, z + 0.33, 'low / high', col=(60, 40, 0), sz=10, bg=None)
pc.text(-22.3, 16.3, 'FRONT (camera side, +Z) - flatbed lane z 13 world is 6.5 m beyond', col=(255, 255, 255), sz=13)
for x in S['col_x']: pc.text(x, 2.0, 'x %.1f' % x, sz=11, bg=None, col=(200, 200, 210))
for z in sorted(set(t['local'][2] for t in S['slots'])): pc.text(-30.3, z, 'z %.2f' % z, sz=11, anchor='lm', bg=None, col=(200, 200, 210))
pc.text(-14.2, 9.5, 'yard pad /\nGC-1 rails ->', sz=12, anchor='lm', bg=None)
# legend
lx = 40 + ic.size[0] + 40; ly = oyc
for i, (c, t) in enumerate([(HR, 'haul road (HT-04)'), (FBc, 'flatbed FB-05 route + pad U-turn'), (TR, 'planned transport road (ST-10)'), ((255, 220, 60), 'storage apron / Slot_01-20'), ((150, 180, 255), 'buried fuel lines'), ((255, 255, 0), 'station origins / spacing')]):
    dr.rectangle([lx, ly + i * 30, lx + 34, ly + i * 30 + 14], fill=c[:3]); dr.text((lx + 44, ly + i * 30 - 3), t, font=F(15), fill=(230, 230, 235))
txt = ['Slot numbering:', ' Slot_01-05  front row, low tier, left->right', ' Slot_06-10  back row, low tier, left->right', ' Slot_11-15  front row, high tier (on 01-05)',
       ' Slot_16-20  back row, high tier (on 06-10)', ' Fill order 01 -> 20 (low tier first).', '', 'Dock GLB (future): 20 empties Slot_01..20 under', ' a Storage node; one shared CargoBox mesh', ' instanced per filled slot.',
       '', 'Models: Dock 882c8e27 (8ca81ac), Refinery 93c44166,', ' bridge bc081489, pad 82131aba, shipyard c0e9d54e.']
for i, t in enumerate(txt): dr.text((lx, ly + 200 + i * 22), t, font=F(14, i == 0 or t.startswith('Slot')), fill=(230, 230, 235))
img = img.crop((0, 0, W, oyc + ic.size[1] + 30)); img.save(OUT); print(OUT, img.size)
