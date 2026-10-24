"""Top-down plan of the Lv10 ship transport road: Launch Pad (right side, far side) -> Shipyard assembly hall.
Pad-local metres (glTF): +X right (toward Shipyard), +Z toward the game camera (drawn DOWN). Inputs (read only):
stations_footprints.json (measure_stations.mjs: 2 m occupancy grids of the real station GLBs) and road_clearance.json (road_clearance.mjs).
Layout = Director's order: Refinery | 20-slot Cargo Dock | Launch Pad | Shipyard (pad + 160 m).
python3 road_plan.py  ->  ../proofs/transport_road_plan_topdown.png + ../proofs/transport_road_plan.json"""
import json, math, os
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, '..', 'proofs')
ST = json.load(open(os.path.join(H, 'stations_footprints.json')))
CL = json.load(open(os.path.join(H, 'road_clearance.json')))
F = '/usr/share/fonts/truetype/dejavu/'
def font(s, b=False): return ImageFont.truetype(F + ('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf'), s)
# ---- layout (pad-local x) ----
X = {'Refinery': -160, 'CargoDock': -80, 'LaunchPad': 0, 'Shipyard': 160}
SHIP = (0.0, -13.0)
ROAD_Z = -13.0; ROAD_HALF = 18.0; SHOULDER = 2.6; LANE = (9.7, 13.3)          # crawler lanes |dz|
TR = dict(x0=-13.4, x1=15.7, half=14.2)                                      # union of ST-10A / ST-10B footprints (ship axis = 0)
PAD_EDGE = 29.4
# Shipyard hall AH-1 from its measured door nodes (rot 10 deg): front wall through Hall_Door, 34 m wide, 26 m deep (toward -Z)
sy = ST['Shipyard']['nodes']; L, R_, D = sy['Hall_Door_L'], sy['Hall_Door_R'], sy['Hall_Door']
ux, uz = R_[0] - L[0], R_[2] - L[2]; n = math.hypot(ux, uz); ux, uz = ux / n, uz / n; nx, nz = uz, -ux   # n points to -Z (into hall)
if nz > 0: nx, nz = -nx, -nz
sx0 = X['Shipyard']
c = (D[0] + sx0, D[2])
HALL = [(c[0] - 17 * ux, c[1] - 17 * uz), (c[0] + 17 * ux, c[1] + 17 * uz), (c[0] + 17 * ux + 26 * nx, c[1] + 17 * uz + 26 * nz), (c[0] - 17 * ux + 26 * nx, c[1] - 17 * uz + 26 * nz)]
# west gable wall: segment HALL[0] -> HALL[3]; x where the road centreline z=-13 meets it
(ax, az), (bx, bz) = HALL[0], HALL[3]; t = (ROAD_Z - az) / (bz - az); WEST_X = ax + t * (bx - ax)
# ---- corridor occupancy at the Shipyard between apron and hall west wall (real grid) ----
g = ST['Shipyard']['grid']; blk = []
for k, h in g.items():
    i, j = map(int, k.split(',')); x, z = 2 * i + sx0, 2 * j
    if x + 2 > WEST_X - 30 and x < WEST_X - 0.5 and z + 2 > ROAD_Z - ROAD_HALF and z < ROAD_Z + ROAD_HALF and h > 0.5: blk.append((x, z, h))
# ---- numbers ----
APRON = (62.0, WEST_X - 1.0)
road_len_gate_to_door = WEST_X - PAD_EDGE
haul_len = WEST_X - TR['x0'] - SHIP[0] - 0  # ship axis travels from 0 to (door - front overhang); report axis travel to the hall threshold
axis_travel = WEST_X + 17 - SHIP[0]   # ship axis: pad centre -> hall centreline (west door + half hall width)
out = dict(units='m, pad-local glTF (+X right toward Shipyard, +Z toward camera). World = pad-local + Launch Pad origin (qa3d x=480).',
  layout_assumed="Director: Refinery | 20-slot Cargo Dock | Launch Pad | Shipyard = pad+160 m",
  centerline=[[0.0, ROAD_Z], [round(PAD_EDGE, 1), ROAD_Z], [round(WEST_X, 1), ROAD_Z]],
  turns=0, s_bends=0, running_width=2 * ROAD_HALF, graded_width_incl_shoulders=round(2 * (ROAD_HALF + SHOULDER), 1),
  crawler_lanes_abs_dz=list(LANE), cross_fall_pct=0.5, max_grade_pct=0.0,
  length_pad_edge_to_hall_west_door=round(road_len_gate_to_door, 1), ship_axis_travel_pad_centre_to_hall_centre=round(axis_travel, 1),
  refit_apron_x=[APRON[0], round(APRON[1], 1)], refit_apron_z=[ROAD_Z - 22, ROAD_Z + 22],
  hall_west_wall_x=round(WEST_X, 1), hall_corners=[[round(a, 2), round(b, 2)] for a, b in HALL],
  transporter_footprint=dict(length=TR['x1'] - TR['x0'], width=2 * TR['half']),
  shipyard_items_between_apron_and_west_wall=[dict(x=x, z=z, h=round(h, 1)) for x, z, h in sorted(blk)],
  pad_clearance_hits=CL['pad'], keep_out=dict(haul_road='Refinery left side (Road_Entry/Exit x=-206), >230 m away', flatbed_lanes='z +13 / +22, x -173..+1 (south of road edge z +5.6 by 7.4 m)',
     pad_uturn='x 1..8.3, z 10.2..24.8 (road edge z +5.6 -> 4.6 m clear)', cargo_dock='pad LEFT (x<-29), road is pad RIGHT: never adjacent'))
json.dump(out, open(os.path.join(P, 'transport_road_plan.json'), 'w'), indent=1)
# ================= drawing =================
W = 2400; BG = (11, 14, 22); INK = (220, 228, 240); DIM = (130, 140, 160)
CY = (58, 208, 255); AM = (255, 176, 32); RED = (255, 80, 70); GRN = (90, 220, 140)
img = Image.new('RGB', (W, 1980), BG); d = ImageDraw.Draw(img, 'RGBA')
d.text((40, 24), 'PLANET STACK  ·  Lv10 SHIP TRANSPORT ROAD  ·  top-down plan (proposal)', font=font(34, True), fill=INK)
d.text((40, 70), f'Straight, zero turns, zero S-bends · running width {2*ROAD_HALF:.0f} m (+{SHOULDER} m graded shoulders = {2*(ROAD_HALF+SHOULDER):.1f} m) · '
       f'pad edge -> hall west door {road_len_gate_to_door:.0f} m · ship travel pad centre -> hall centre {axis_travel:.0f} m · far side (-Z) of the pad, right side exit',
       font=font(20), fill=DIM)
PANEL = {}
def panel(ox, oy, pw, ph, x0, x1, z0, z1, title):
    global d
    s = min(pw / (x1 - x0), ph / (z1 - z0))
    d.text((ox, oy - 30), title, font=font(20, True), fill=INK)
    sub = Image.new('RGB', (int((x1 - x0) * s) + 1, int((z1 - z0) * s) + 1), (16, 20, 30))
    PANEL.update(img=sub, ox=ox, oy=oy, main=d); d = ImageDraw.Draw(sub, 'RGBA')
    T = lambda x, z: ((x - x0) * s, (z - z0) * s)
    for gx in range(int(math.ceil(x0 / 20) * 20), int(x1) + 1, 20):
        d.line([T(gx, z0), T(gx, z1)], fill=(255, 255, 255, 14))
    for gz in range(int(math.ceil(z0 / 20) * 20), int(z1) + 1, 20):
        d.line([T(x0, gz), T(x1, gz)], fill=(255, 255, 255, 14))
    return s, T
def end_panel():
    global d
    sub = PANEL['img']; ImageDraw.Draw(sub).rectangle([0, 0, sub.width - 1, sub.height - 1], outline=(50, 58, 76), width=2)
    img.paste(sub, (PANEL['ox'], PANEL['oy'])); d = PANEL['main']
def grid_fp(T, s, name, col):
    gx0 = X[name]
    for k, h in ST[name]['grid'].items():
        i, j = map(int, k.split(',')); x, z = 2 * i + gx0, 2 * j
        a = int(min(230, 60 + h * 9))
        d.rectangle([T(x, z), T(x + 2, z + 2)], fill=col + (a,))
    (bx0, _, bz0), (bx1, _, bz1) = ST[name]['all']
    d.rectangle([T(bx0 + gx0, bz0), T(bx1 + gx0, bz1)], outline=col + (200,), width=2)
def berm(T, s, gate=True, fill=(150, 140, 120, 150)):
    pts_o, pts_i = [], []
    for a in range(60, 301, 2):         # az from +Z toward +X; opening |az|<60 toward camera
        r = math.radians(a); pts_o.append((SHIP[0] + 29 * math.sin(r), SHIP[1] + 29 * math.cos(r))); pts_i.append((SHIP[0] + 22 * math.sin(r), SHIP[1] + 22 * math.cos(r)))
    d.polygon([T(*p) for p in pts_o + pts_i[::-1]], fill=fill)
def road(T, s, x_from, x_to, draw_lanes=True):
    d.rectangle([T(x_from, ROAD_Z - ROAD_HALF - SHOULDER), T(x_to, ROAD_Z + ROAD_HALF + SHOULDER)], fill=(92, 88, 82, 255))
    d.rectangle([T(x_from, ROAD_Z - ROAD_HALF), T(x_to, ROAD_Z + ROAD_HALF)], fill=(126, 120, 110, 255))
    if draw_lanes:
        for sg in (-1, 1):
            za, zb = ROAD_Z + sg * LANE[0], ROAD_Z + sg * LANE[1]
            d.rectangle([T(x_from, min(za, zb)), T(x_to, max(za, zb))], fill=(84, 80, 74, 255))
            if s > 6:
                x = x_from
                while x < x_to:   # crawler cleat marks every 0.62 m drawn every 1.24 m
                    d.line([T(x, min(za, zb) + 0.2), T(x, max(za, zb) - 0.2)], fill=(60, 57, 53, 255), width=1); x += 1.24
    for sg in (-1, 1):
        d.line([T(x_from, ROAD_Z + sg * ROAD_HALF), T(x_to, ROAD_Z + sg * ROAD_HALF)], fill=(235, 235, 225, 255), width=2)
        x = x_from + 6
        while x < x_to:
            px, pz = T(x, ROAD_Z + sg * (ROAD_HALF + 1.3)); d.ellipse([px - 3, pz - 3, px + 3, pz + 3], fill=CY if sg < 0 else AM); x += 12
def foot(T, cx, col, lab=None, dash=True):
    a, b = T(cx + TR['x0'], ROAD_Z - TR['half']), T(cx + TR['x1'], ROAD_Z + TR['half'])
    d.rectangle([a, b], outline=col, width=3)
    p = T(cx, ROAD_Z); r = 4.49 * (b[0] - a[0]) / (TR['x1'] - TR['x0'])
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=(200, 205, 215, 255), outline=(40, 40, 50))
    if lab: d.text((a[0] + 4, a[1] + 4), lab, font=font(15, True), fill=col)
def label(T, x, z, t, col=INK, sz=16, b=True, anchor='la'):
    d.text(T(x, z), t, font=font(sz, b), fill=col, anchor=anchor)
def scalebar(T, s, x, z, L=50):
    a, b = T(x, z), T(x + L, z); d.line([a, b], fill=INK, width=4)
    for k in range(0, L + 1, 10): p = T(x + k, z); d.line([p[0], p[1] - 6, p[0], p[1] + 6], fill=INK, width=2)
    d.text((a[0], a[1] + 10), f'0      {L} m', font=font(15), fill=INK)
# ---------- Panel 1: overview ----------
s1, T1 = panel(40, 150, 2320, 460, -215, 245, -62, 40, 'OVERVIEW  ·  Refinery  |  20-slot Cargo Dock  |  Launch Pad  |  Shipyard   (Director layout, 160 m station pitch)')
for nm, col in (('Refinery', (170, 150, 120)), ('CargoDock', (120, 170, 220)), ('LaunchPad', (200, 205, 215)), ('Shipyard', (180, 200, 150))):
    grid_fp(T1, s1, nm, col)
berm(T1, s1)
for zl in (13, 22): d.line([T1(-173, zl), T1(1, zl)], fill=AM + (230,), width=3)
d.line([T1(-206, 9), T1(-215, 9)], fill=(200, 120, 60), width=4); d.line([T1(-206, 0), T1(-215, 0)], fill=(200, 120, 60), width=4)
road(T1, s1, PAD_EDGE, WEST_X, draw_lanes=True)
foot(T1, 0, CY); foot(T1, APRON[0] + 15.5, CY)
label(T1, -176, -55, 'REFINERY', (230, 210, 170), 20); label(T1, -176, -49, 'x = pad-160 (qa3d 320)', DIM, 14, False)
label(T1, -100, -55, 'CARGO DOCK (20-slot)', (150, 200, 255), 20); label(T1, -100, -49, 'between Refinery and Pad', DIM, 14, False)
label(T1, -26, -57, 'LAUNCH PAD', INK, 20); label(T1, -26, -51, 'origin, qa3d x 480', DIM, 14, False)
label(T1, 112, -57, 'SHIPYARD', (200, 230, 160), 20); label(T1, 112, -51, 'x = pad+160', DIM, 14, False)
label(T1, -172, 25, 'flatbed route  Refinery <-> Dock <-> Pad   (lanes z +13 / +22)', AM, 15)
label(T1, -214, 3, 'haul road ->Mine', (220, 140, 80), 13)
label(T1, 34, -36, 'SHIP TRANSPORT ROAD (36 m, crawler track)', CY, 16)
scalebar(T1, s1, 170, 33, 50)
d.text(T1(232, -60), 'far side (-Z)', font=font(14), fill=DIM, anchor='ra'); d.text(T1(232, 38), 'camera side (+Z)', font=font(14), fill=DIM, anchor='rd')
end_panel()
# ---------- Panel 2: detail ----------
s2, T2 = panel(40, 680, 2320, 860, -44, 186, -58, 34, 'DETAIL  ·  Launch Pad right side  ->  Shipyard assembly hall AH-1   (8 px/m grid = 20 m)')
grid_fp(T2, s2, 'LaunchPad', (200, 205, 215)); grid_fp(T2, s2, 'Shipyard', (180, 200, 150))
berm(T2, s2)
# berm gate cut (required pad change)
gz0, gz1 = ROAD_Z - TR['half'] - 1.2, ROAD_Z + TR['half'] + 1.2
d.rectangle([T2(18.5, gz0), T2(PAD_EDGE, gz1)], fill=(255, 80, 70, 70), outline=RED, width=3)
road(T2, s2, PAD_EDGE, WEST_X)
d.rectangle([T2(APRON[0], ROAD_Z - 22), T2(APRON[1], ROAD_Z + 22)], outline=(235, 235, 225), width=2)
label(T2, APRON[0] + 1, ROAD_Z + 22.6, f'REFIT / HOLD APRON RA-1  {APRON[1]-APRON[0]:.0f} x 44 m', INK, 14)
# conflicts from real-vertex sweep (union A/B)
seen = []
for h in CL['pad']['A'] + CL['pad']['B']:
    if h['ymax'] < 0.5: continue
    box = (h['x0'], h['z0'], h['x1'], h['z1'])
    if any(abs(box[0] - b[0]) < 1.5 and abs(box[1] - b[1]) < 1.5 for b in seen): continue
    seen.append(box); d.rectangle([T2(box[0], box[1]), T2(box[2], box[3])], fill=(255, 80, 70, 110), outline=RED, width=2)
def tag(x, z, k):
    p = T2(x, z); d.ellipse([p[0] - 13, p[1] - 13, p[0] + 13, p[1] + 13], fill=RED, outline=(255, 255, 255)); d.text(p, str(k), font=font(16, True), fill=(255, 255, 255), anchor='mm')
tag(12.6, -30.0, 2); tag(14.2, 2.2, 3); tag(16.7, -20.5, 3); tag(23.55, -6.6, 4); tag(24.0, -29.8, 1)
CALL = ['1  berm gate G-1: cut 30.8 m in the right arc', '2  Tier_08 pump skid P-2 (5.2 m): move', '3  LOX / LCH4 cryo tanks (to 12 m): move (AA2)', '4  valve vault VV-1 riser 4.4 m: lower < 3 m', '   hoses LOX / LCH4: stow before transport']
for i, t in enumerate(CALL): label(T2, -42.5, -57 + 2.2 * i, t, RED, 14)
# pad furniture
d.ellipse([T2(1, 10.2), T2(8.3, 24.8)], outline=AM, width=3); label(T2, 9.5, 18.5, 'pad U-turn', AM, 14)
for zl in (13, 22): d.line([T2(-44, zl), T2(1, zl)], fill=AM, width=3)
label(T2, -43, 25, 'flatbed lanes (from Cargo Dock / Refinery)', AM, 14)
d.rectangle([T2(-10, 2), T2(-5, 7)], outline=(200, 205, 215), width=2); label(T2, -9.6, 7.6, 'cargo bay', DIM, 13, False)
d.rectangle([T2(-2.4, 12.4), T2(16.5, 16.1)], outline=(180, 185, 195), width=2); label(T2, 10, 10.6, 'crane PC-1', DIM, 13, False)
label(T2, -42.5, -44.6, '<- CARGO DOCK side (pad LEFT): road never goes here', (150, 200, 255), 15)
label(T2, -24, -39.5, 'blast berm (3.4 m)', (200, 190, 160), 13, False)
foot(T2, 0, CY, 'ST-10 pick-up (ship on transporter)')
foot(T2, APRON[0] + 15.5, (235, 235, 225), 'hold / turn-back')
# shipyard
d.polygon([T2(*p) for p in HALL], outline=(220, 240, 180), width=3)
cx_, cz_ = sum(p[0] for p in HALL) / 4, sum(p[1] for p in HALL) / 4
label(T2, cx_, cz_ - 1, 'ASSEMBLY HALL AH-1', (220, 240, 180), 16, anchor='mm'); label(T2, cx_, cz_ + 3, '34 x 26 m, 24 m tall', DIM, 13, False, 'mm')
dl, dr = (L[0] + sx0, L[2]), (R_[0] + sx0, R_[2]); d.line([T2(*dl), T2(*dr)], fill=AM, width=6)
label(T2, dl[0] - 1, dl[1] + 3.5, 'existing door 20.9 W x 20.6 H (faces camera, 10 m forecourt)', AM, 13, anchor='ra')
wa, wb = (WEST_X, ROAD_Z - 16), (WEST_X, ROAD_Z + 16)
d.line([T2(*wa), T2(*wb)], fill=GRN, width=7)
label(T2, WEST_X - 1, ROAD_Z - 21, 'ROAD END: proposed Lv10 west high-bay door', GRN, 15, anchor='ra')
label(T2, WEST_X - 1, ROAD_Z - 18.2, '>= 32 m W x 44 m H (hall high bay >= 46 m)', GRN, 13, False, 'ra')
for x, z, hgt in blk: d.rectangle([T2(x, z), T2(x + 2, z + 2)], outline=RED, width=1)
isx = (26 + sx0, 44 + sx0); d.rectangle([T2(isx[0], -26), T2(isx[1], -4)], outline=(220, 240, 180), width=2)
label(T2, isx[0] + 1, -3.4, 'IS-1 integration stand', DIM, 13, False)
# dims
yA = ROAD_Z + ROAD_HALF + SHOULDER + 4.5
d.line([T2(PAD_EDGE, yA), T2(WEST_X, yA)], fill=INK, width=2)
for xx in (PAD_EDGE, WEST_X): d.line([T2(xx, yA - 1.2), T2(xx, yA + 1.2)], fill=INK, width=2)
label(T2, (PAD_EDGE + WEST_X) / 2, yA + 0.6, f'{road_len_gate_to_door:.1f} m  pad edge -> hall west wall  (centreline z = -13, dead straight)', INK, 15, anchor='ma')
xw = 50
d.line([T2(xw, ROAD_Z - ROAD_HALF), T2(xw, ROAD_Z + ROAD_HALF)], fill=INK, width=2)
label(T2, xw + 0.6, ROAD_Z - 2.2, '36 m', INK, 15); label(T2, xw + 0.6, ROAD_Z + 0.6, 'running', DIM, 13, False)
label(T2, 33, ROAD_Z + LANE[1] + 0.3, 'crawler lane', (60, 50, 40), 12)
scalebar(T2, s2, 120, 29, 20)
end_panel()
# ---------- notes ----------
notes = [
 ('ROAD', INK, f'Centreline pad-local z = -13 (ship axis), from the pad edge x 29.4 to the Shipyard hall west wall x {WEST_X:.1f}: {road_len_gate_to_door:.1f} m, zero turns, flat 0% grade, 0.5% cross-fall.'),
 ('', DIM, f'Running width 36 m (transporter 28.5 m + 3.75 m each side) + 2.6 m graded shoulders = 41.2 m. Two darker sintered crawler lanes at |dz| 9.7-13.3 m with 0.62 m cleat imprints (no tyre trails). Cyan (far) / amber (near) reflector posts every 12 m.'),
 ('', DIM, 'Autonomous transporter runs both ways (no cab), so no turnaround loop is needed: in on the road, back out on the same road. Refit/hold apron RA-1 is the passing and staging pad.'),
 ('KEEP-OUT', GRN, 'Haul road: >230 m away (Refinery far left).  Flatbed lanes z +13/+22 and pad U-turn: road edge stays at z <= +5.6 (4.6 m clear of the U-turn, never crosses).  Cargo Dock: pad LEFT; road leaves pad RIGHT.'),
 ('PAD CHANGES', RED, 'Measured on real pad vertices (A and B swept volumes): cut berm gate G-1 in the right arc (z -28.4..+2.4); move LOX/LCH4 tanks (x 11.7-19, to 12 m) and Tier_08 pump skid P-2; lower the VV-1 riser (4.4 m); stow hoses. Lv1 edge lights 0.37 m are drive-over.'),
 ('SHIPYARD', AM, 'Loaded transporter is ~28.5 m wide x 41 m tall: it cannot reach the existing 20.9 x 20.6 m camera-side door (10 m forecourt, Tier_03 and W-2 alongside). Proposal: Lv10 west high-bay door on the gable the road meets.'),
 ('', AM, f'Fallback with no Shipyard change: road ends at apron RA-1 (x 62-{APRON[1]:.0f}) and the ship is rebuilt on its legs there under the Shipyard cranes. Items west of the hall in the road corridor: {len(blk)} cells (red outlines), for the Shipyard owner.'),
 ('LAYOUT FLAG', RED, 'qa3d STATIONS today: Refinery 320, Launch Pad 480, Cargo Space Dock 640, Habitat 800, Shipyard 960. Director order puts the Dock left of the pad and the Shipyard at pad+160. Under today\'s code the road would run +320 m behind Dock and Habitat.'),
]
y = 1580
for tag, col, t in notes:
    if tag: d.text((40, y), tag, font=font(17, True), fill=col)
    # wrap
    words, line, lines = t.split(), '', []
    for w in words:
        if d.textlength(line + ' ' + w, font=font(16)) > 2120: lines.append(line); line = w
        else: line = (line + ' ' + w).strip()
    lines.append(line)
    for ln in lines: d.text((230, y), ln, font=font(16), fill=INK if col != DIM else DIM); y += 22
    y += 4
img = img.crop((0, 0, W, min(1980, y + 20)))
img.save(os.path.join(P, 'transport_road_plan_topdown.png'))
print('WEST_X', round(WEST_X, 2), 'len', round(road_len_gate_to_door, 1), 'axis', round(axis_travel, 1), 'blk', len(blk), 'size', img.size)
