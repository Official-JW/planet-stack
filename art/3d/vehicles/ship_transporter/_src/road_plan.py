"""Lv10 ship transport road, top-down plan v4 (Director-approved road; Habitat moved east; v4 = re-based on the approved station table in WORLD
coordinates, road sized to the picked crawler ST-10A, AA2's Lv1 pad pipe end at the pad LEFT (430, 0.95, 2.6); see road_clearance.mjs v4). WORLD glTF metres: +X right, +Z toward the game camera (drawn DOWN).
Layout = cargo_dock/layout_v3 (cae8f39, dock compact_v3 9fb1ddbe) + v3 station order: Life Support 0 | Mine 160 | Refinery 320 | Cargo Dock 360 (z -8) | Launch Pad 457 |
Shipyard 960 | Habitat 1068 (moved from 800, east of the Shipyard) | Engineering 1120 (unchanged).
Inputs (read only): stations_footprints.json (measure_stations.mjs: 2 m max-height grids of the real GLBs) and road_clearance.json
(road_clearance.mjs: real pad vertices vs the ST-10A/B swept volumes). Director rulings: road leaves the pad's RIGHT side on the far
side (-Z), never crosses haul road / flatbed / U-turn, own crawler-track texture; Lv10 Shipyard gets a wider hall door (proposal only,
the Shipyard GLB is not edited); the pad fuel pipe end is at the pad's LEFT (430, 0.95, 2.6), so VV-1 is out of the corridor.
python3 road_plan.py [--no-png] -> ../proofs/transport_road_plan.json (+ ../proofs/transport_road_plan_topdown.png unless --no-png)"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, '..', 'proofs')
ST = json.load(open(os.path.join(H, 'stations_footprints.json'))); CL = json.load(open(os.path.join(H, 'road_clearance.json')))
F = '/usr/share/fonts/truetype/dejavu/'
def font(s, b=False): return ImageFont.truetype(F + ('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf'), s)
X = {'Refinery': (320, 0), 'CargoDock': (360, -8), 'LaunchPad': (457, 0), 'Shipyard': (960, 0)}
PADX = 457.0; SHIP = (PADX, -13.0)
HAB_OLD = dict(x0=795.5, x1=804.5, z0=-4.5, z1=4.5)                 # layout_v2 position: removed (was inside the road corridor)
SY_X1 = X['Shipyard'][0] + ST['Shipyard']['all'][1][0]                 # Shipyard east edge (real GLB bbox) 1021.9
ENG = dict(x0=1115.0, x1=1125.0, z0=-4.0, z1=4.0)                      # Engineering gray box 10 x 10 x 8 at 7*160 = 1120: unchanged
HAB_X = 1068.0; HAB = dict(x0=HAB_X - 4.5, x1=HAB_X + 4.5, z0=-4.5, z1=4.5)   # Habitat 9 x 12 x 9 gray box, z 0 (not moved toward camera)
STATION_X = [('Life Support', 0, 0.0, 'unchanged'), ('Mine', 160, 0.0, 'unchanged'), ('Refinery', 320, 0.0, 'unchanged'), ('Cargo Dock', 360, -8.0, 'cargo_dock/layout_v3 cae8f39 (was 373 in layout_v2)'),
             ('Launch Pad', 457, 0.0, 'layout_v2'), ('Shipyard', 960, 0.0, 'unchanged'), ('Habitat', HAB_X, 0.0, 'v3: moved from 800 (road corridor) to east of the Shipyard'),
             ('Engineering', 1120, 0.0, 'unchanged (checked: 42.5 m clear of the Habitat)')]
TR = dict(x0=-13.36, x1=15.64, half=13.56, height_loaded=44.55, tower_top=35.5)   # ST-10A game GLB (st10a_game.glb); ship top = Lv2 44.098 + 0.45 lift
ROAD_Z, SHOULDER, LANE, MARGIN = -13.0, 2.6, (9.7, 13.3), 3.75          # crawler lanes = ST-10A track bands
HALF = round(TR['half'] + MARGIN, 2)                                     # 17.31 -> running width 34.62 m (v3: 36 m for ST-10B 28.5 m)
PAD_EDGE = CL['road']['pad_edge_x']                                      # real pad bbox east edge (AA2 lv1door pad, road_clearance.mjs v4)
PIPE_END = tuple(CL['pipe_end']['given'])                                # AA2 Lv1 pad Pipe_LaunchPad_End, world (430, 0.95, 2.6) (not 430, -9.6)
G1 = dict(name='G-1', pad='Lv1 pad (AA2)', width=30.8, z=[-28.4, 2.4], changed=False,
          note='unchanged 30.8 m: ST-10A is 27.12 m wide (|dz| <= 13.56 about the ship axis z -13) and passes with 1.84 m each side')
G10 = dict(name='G-10', pad='Lv10 pad (owner: Lv10 pad / AA2)', width=round(2 * HALF, 1), z=[round(ROAD_Z - HALF, 2), round(ROAD_Z + HALF, 2)], changed=True,
           note='ONLY the Lv10 pad gate widens: to the crawler road running width (ST-10A 27.12 m + 3.75 m each side), centred on the road axis z -13')
# Shipyard hall AH-1: door centre from Hall_Door (both versions), hall 34 x 26 m, yaw from bcbd0934 Hall_Door_L/R (-24.61,5.81)/(-14.27,3.99)
SX = 960.0; D = ST['Shipyard']['nodes']['Hall_Door']
ux, uz = (-14.27 + 24.61), (3.99 - 5.81); n = math.hypot(ux, uz); ux, uz = ux / n, uz / n; nx, nz = uz, -ux
if nz > 0: nx, nz = -nx, -nz
c = (D[0] + SX, D[2])
HALL = [(c[0] - 17 * ux, c[1] - 17 * uz), (c[0] + 17 * ux, c[1] + 17 * uz), (c[0] + 17 * ux + 26 * nx, c[1] + 17 * uz + 26 * nz), (c[0] - 17 * ux + 26 * nx, c[1] - 17 * uz + 26 * nz)]
(ax, az), (bx, bz) = HALL[0], HALL[3]; t = (ROAD_Z - az) / (bz - az); WEST_X = ax + t * (bx - ax)
# Lv10 high bay HB-10 (proposal): west extension of AH-1 on the road axis, door D-10 facing the road
DOOR_W, DOOR_H, BAY_L, BAY_W, BAY_H = 34.0, 46.0, 40.0, 44.0, 52.0
BAY = (WEST_X - BAY_L, ROAD_Z - BAY_W / 2, WEST_X, ROAD_Z + BAY_W / 2); DOOR_X = BAY[0]
APRON = (DOOR_X - 44.0, DOOR_X)
# Shipyard cells (real grid) inside the bay + apron footprint: these must clear for HB-10 (Shipyard owner)
blk = []
for k, h in ST['Shipyard']['grid'].items():
    i, j = map(int, k.split(',')); x, z = 2 * i + SX, 2 * j
    if x + 2 > APRON[0] and x < WEST_X - 0.5 and z + 2 > BAY[1] and z < BAY[3] and h > 0.5: blk.append((x, z, round(h, 1)))
road_len = DOOR_X - PAD_EDGE; travel = (BAY[0] + BAY[2]) / 2 - SHIP[0]
hab_edge = ROAD_Z + HALF + SHOULDER
GAP_W = HAB['x0'] - SY_X1; GAP_E = ENG['x0'] - HAB['x1']
pad_hits = []
for h in CL['pad']['A_world']:                                           # world coordinates already (v4)
    if h['ymax'] < 0.5: continue
    b = (h['x0'], h['z0'], h['x1'], h['z1'], h['ymax'], h['node'])
    if not any(abs(b[0] - q[0]) < 1.5 and abs(b[1] - q[1]) < 1.5 for q in pad_hits): pad_hits.append(b)
APRON0 = DOOR_X - 44.0
fl_gap = 13.0 - (ROAD_Z + HALF + SHOULDER); ut_gap = 10.2 - (ROAD_Z + HALF + SHOULDER)
out = dict(version='v4', rebased='10/24 v4: world coordinates from the approved station table (pad 457, Cargo Dock (360, 0, -8), Shipyard 960); the old pad-local check (Shipyard at pad +160, i.e. pad 480 / Shipyard 640) is retired; road sized to ST-10A (B shelved)',
  crawler=dict(name='ST-10A', glb='game/st10a_game.glb', width=round(2 * TR['half'], 2), length=round(TR['x1'] - TR['x0'], 2), loaded_height=TR['height_loaded'], track_bands_abs_dz=list(LANE)),
  gates=dict(G1=G1, G10=G10), pipe_end=dict(world=list(PIPE_END), source='AA2 launch_pad_game_lv1door.glb Pipe_LaunchPad_End (pad-local -27, 0.95, 2.6), md5 ' + CL['pad_md5'],
     clear_of_crawler_at_pickup_m=CL['pipe_end']['clear_of_crawler_at_pickup_m'], old='(477.3, -9.6) VV-1 / (430, -9.6) in v3: both retired'),
  keep_out=dict(crossings_of_other_roads=[], haul_road=dict(x_max=321, gap_to_road_m=round(PAD_EDGE - 321, 1)),
     flatbed_lanes=dict(z=[13, 22], x=[296, 464], gap_m=round(fl_gap, 2)), pad_uturn=dict(x=[458, 465.3], z=[10.2, 24.8], gap_m=round(ut_gap, 2)),
     cargo_dock=dict(origin=[360, 0, -8], bbox_world=CL['cargo_dock']['bbox_world'], gap_to_road_m=CL['cargo_dock']['gap_to_road_m'], gap_to_crawler_path_m=CL['cargo_dock']['gap_to_crawler_path_m']),
     shipyard_first_vertex_in_corridor_x=CL['shipyard_in_corridor']['first_x'], apron_start_x=round(APRON0, 1),
     shipyard_corridor_clear_west_of_apron=CL['shipyard_in_corridor']['first_x'] is None or CL['shipyard_in_corridor']['first_x'] >= APRON0 - 0.05),
  units='world glTF m (+X right, +Z toward camera)',
  layout='cargo_dock/layout_v3 cae8f39 (compact_v3 9fb1ddbe) + v3 order: Life Support 0 | Mine 160 | Refinery 320 | Cargo Dock 360 z-8 | Launch Pad 457 | Shipyard 960 (shipyard_game.glb c0e9d54e) | Habitat 1068 | Engineering 1120',
  director='10/24 13:31: road v2, HB-10 + D-10 (7 cells), pad exit APPROVED; ST-10B picked; Habitat east of the Shipyard, no S-jog',
  centerline=[[SHIP[0], ROAD_Z], [round(PAD_EDGE, 1), ROAD_Z], [round(DOOR_X, 1), ROAD_Z], [round((BAY[0] + BAY[2]) / 2, 1), ROAD_Z]],
  turns=0, s_bends=0, running_width=round(2 * HALF, 2), graded_width=round(2 * (HALF + SHOULDER), 1), crawler_lanes_abs_dz=list(LANE), grade_pct=0.0, cross_fall_pct=0.5,
  length_pad_edge_to_D10=round(road_len, 1), ship_travel_pad_centre_to_bay_centre=round(travel, 1),
  apron_RA1_x=[round(APRON[0], 1), round(APRON[1], 1)],
  lv10_high_bay_HB10=dict(x=[round(BAY[0], 1), round(BAY[2], 1)], z=[BAY[1], BAY[3]], inner_height=BAY_H, door_D10=dict(x=round(DOOR_X, 1), width=DOOR_W, clear_height=DOOR_H, faces='-X (the road)'),
     sizing=f'ST-10A {2*TR["half"]:.2f} m wide + {(DOOR_W - 2*TR["half"])/2:.2f} m each side within {DOOR_W} m; loaded height {TR["height_loaded"]} m (Lv2 ship 43.85 m; no Lv10 height exists yet) -> {DOOR_H - TR["height_loaded"]:.2f} m under D-10 {DOOR_H} m (v3 margin 5.3 m with the Lv1 ship): FLAG'),
  existing_door='Hall_Door (940.6, 4.9) faces +Z: 10.3 m between Hall_Door_L/R (bcbd0934), 8-14 m forecourt: unusable for ST-10 (layout_v2 item 9)',
  shipyard_cells_to_clear=[dict(x=x, z=z, h=h) for x, z, h in sorted(blk)],
  habitat=dict(origin=[HAB_X, 0.0], footprint=HAB, size_whd=[9, 12, 9], was=dict(origin=[800.0, 0.0], footprint=HAB_OLD, note='inside the road corridor (z -33.6..+7.6): removed'),
     clear_to_shipyard_east_edge=round(GAP_W, 1), shipyard_east_edge_x=round(SY_X1, 1), clear_to_engineering=round(GAP_E, 1),
     road='no Habitat in the road path: the corridor x 486.4-880.1 is clear, z unchanged (0), no jog / no S-bend'),
  engineering=dict(origin=[1120.0, 0.0], footprint=ENG, size_whd=[10, 10, 8], changed=False),
  station_x_table=dict(note='Coder: replace origin = i*160 with this per-station table (index = v3 order). qa3d/main.js STATIONS order today is Life Support, Mine, Refinery, Takeoff & Landing, Cargo Space Dock, Habitat, Shipyard, Engineering; the v3 order swaps Pad/Dock and moves Habitat after the Shipyard (SIZES entries move with their names).',
     stations=[dict(index=i, name=n, x=x, z=z, note=nt) for i, (n, x, z, nt) in enumerate(STATION_X)]),
  pad_hits_world=[dict(x=[round(b[0], 1), round(b[2], 1)], z=[b[1], b[3]], h=b[4], node=b[5]) for b in pad_hits])
json.dump(out, open(os.path.join(P, 'transport_road_plan.json'), 'w'), indent=1)
print('JSON', 'pad_edge', PAD_EDGE, 'running', 2 * HALF, 'D10', round(DOOR_X, 1), 'len', round(road_len, 1), 'blk', len(blk), 'keep_out', json.dumps(out['keep_out']))
if '--no-png' in sys.argv: sys.exit(0)
# ===================== drawing =====================
W = 2400; BG = (11, 14, 22); INK = (220, 228, 240); DIM = (130, 140, 160)
CY = (58, 208, 255); AM = (255, 176, 32); RED = (255, 80, 70); GRN = (90, 220, 140); HABC = (190, 160, 220)
img = Image.new('RGB', (W, 2300), BG); d = ImageDraw.Draw(img, 'RGBA')
d.text((40, 24), 'PLANET STACK  ·  Lv10 SHIP TRANSPORT ROAD  ·  top-down plan v4 (road approved; world re-base, ST-10A)', font=font(34, True), fill=INK)
d.text((40, 70), f'One straight line, zero turns, zero S-bends · centreline z -13 (ship axis) · running width {2*HALF:.1f} m for ST-10A (+2.6 m shoulders = {2*(HALF+SHOULDER):.1f} m) · '
       f'pad edge -> Lv10 bay door D-10: {road_len:.0f} m · ship travel {travel:.0f} m', font=font(20), fill=DIM)
d.text((40, 98), 'Station X (v3 order): Life Support 0 | Mine 160 | Refinery 320 | Cargo Dock 360 | Launch Pad 457 | Shipyard 960 | Habitat 1068 | Engineering 1120. World metres, +Z (camera side) drawn down.', font=font(18), fill=DIM)
PANEL = {}
def panel(ox, oy, pw, ph, x0, x1, z0, z1, title, step=20):
    global d
    s = min(pw / (x1 - x0), ph / (z1 - z0))
    d.text((ox, oy - 28), title, font=font(19, True), fill=INK)
    sub = Image.new('RGB', (int((x1 - x0) * s) + 1, int((z1 - z0) * s) + 1), (16, 20, 30))
    PANEL.update(img=sub, ox=ox, oy=oy, main=d); d = ImageDraw.Draw(sub, 'RGBA')
    T = lambda x, z: ((x - x0) * s, (z - z0) * s)
    for gx in range(int(math.ceil(x0 / step) * step), int(x1) + 1, step): d.line([T(gx, z0), T(gx, z1)], fill=(255, 255, 255, 14))
    for gz in range(int(math.ceil(z0 / step) * step), int(z1) + 1, step): d.line([T(x0, gz), T(x1, gz)], fill=(255, 255, 255, 14))
    return s, T, sub.size
def end_panel():
    global d
    sub = PANEL['img']; ImageDraw.Draw(sub).rectangle([0, 0, sub.width - 1, sub.height - 1], outline=(50, 58, 76), width=2)
    img.paste(sub, (PANEL['ox'], PANEL['oy'])); d = PANEL['main']
def grid_fp(T, name, col):
    gx0, gz0 = X[name]
    for k, h in ST[name]['grid'].items():
        i, j = map(int, k.split(',')); x, z = 2 * i + gx0, 2 * j + gz0
        d.rectangle([T(x, z), T(x + 2, z + 2)], fill=col + (int(min(230, 60 + h * 9)),))
    (bx0, _, bz0), (bx1, _, bz1) = ST[name]['all']
    d.rectangle([T(bx0 + gx0, bz0 + gz0), T(bx1 + gx0, bz1 + gz0)], outline=col + (200,), width=2)
def berm(T):
    po, pi = [], []
    for a in range(60, 301, 2):
        r = math.radians(a); po.append((SHIP[0] + 29 * math.sin(r), SHIP[1] + 29 * math.cos(r))); pi.append((SHIP[0] + 22 * math.sin(r), SHIP[1] + 22 * math.cos(r)))
    d.polygon([T(*p) for p in po + pi[::-1]], fill=(150, 140, 120, 150))
def road(T, s, x_from, x_to):
    d.rectangle([T(x_from, ROAD_Z - HALF - SHOULDER), T(x_to, ROAD_Z + HALF + SHOULDER)], fill=(92, 88, 82, 255))
    d.rectangle([T(x_from, ROAD_Z - HALF), T(x_to, ROAD_Z + HALF)], fill=(126, 120, 110, 255))
    for sg in (-1, 1):
        za, zb = sorted((ROAD_Z + sg * LANE[0], ROAD_Z + sg * LANE[1]))
        d.rectangle([T(x_from, za), T(x_to, zb)], fill=(84, 80, 74, 255))
        if s > 5:
            x = x_from
            while x < x_to: d.line([T(x, za + 0.2), T(x, zb - 0.2)], fill=(60, 57, 53, 255), width=1); x += 1.24
        d.line([T(x_from, ROAD_Z + sg * HALF), T(x_to, ROAD_Z + sg * HALF)], fill=(235, 235, 225, 255), width=2)
        if s > 3:
            x = x_from + 6
            while x < x_to:
                px, pz = T(x, ROAD_Z + sg * (HALF + 1.3)); d.ellipse([px - 2.5, pz - 2.5, px + 2.5, pz + 2.5], fill=CY if sg < 0 else AM); x += 12
def foot(T, cx, col, lab=None):
    a, b = T(cx + TR['x0'], ROAD_Z - TR['half']), T(cx + TR['x1'], ROAD_Z + TR['half'])
    d.rectangle([a, b], outline=col, width=3); p = T(cx, ROAD_Z); r = 4.49 * (b[0] - a[0]) / (TR['x1'] - TR['x0'])
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=(200, 205, 215, 255), outline=(40, 40, 50))
    if lab: d.text((a[0] + 4, a[1] + 4), lab, font=font(14, True), fill=col)
def label(T, x, z, t, col=INK, sz=15, b=True, anchor='la'): d.text(T(x, z), t, font=font(sz, b), fill=col, anchor=anchor)
def scalebar(T, x, z, L, tick):
    a, b = T(x, z), T(x + L, z); d.line([a, b], fill=INK, width=4)
    for k in range(0, L + 1, tick): p = T(x + k, z); d.line([p[0], p[1] - 6, p[0], p[1] + 6], fill=INK, width=2)
    d.text((a[0], a[1] + 9), f'0   {L} m', font=font(14), fill=INK)
def dashed_rect(a, b, col, w=2, dash=5):
    (x0, y0), (x1, y1) = a, b
    for (p, q) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        L = math.hypot(q[0] - p[0], q[1] - p[1]); n = max(1, int(L / dash))
        for k in range(0, n, 2): t0, t1 = k / n, min(1, (k + 1) / n); d.line([(p[0] + (q[0] - p[0]) * t0, p[1] + (q[1] - p[1]) * t0), (p[0] + (q[0] - p[0]) * t1, p[1] + (q[1] - p[1]) * t1)], fill=col, width=w)
def hab(T, ghost=True):
    if ghost: dashed_rect(T(HAB_OLD['x0'], HAB_OLD['z0']), T(HAB_OLD['x1'], HAB_OLD['z1']), RED)
    d.rectangle([T(HAB['x0'], HAB['z0']), T(HAB['x1'], HAB['z1'])], fill=(190, 160, 220, 210), outline=HABC, width=2)
    d.rectangle([T(ENG['x0'], ENG['z0']), T(ENG['x1'], ENG['z1'])], fill=(150, 160, 175, 210), outline=(200, 205, 215), width=2)
def hall(T):
    d.polygon([T(*p) for p in HALL], outline=(220, 240, 180), width=3)
    dl = (-24.61 + SX, 5.81); dr = (-14.27 + SX, 3.99); d.line([T(*dl), T(*dr)], fill=AM, width=5)
    d.rectangle([T(BAY[0], BAY[1]), T(BAY[2], BAY[3])], fill=(90, 220, 140, 45), outline=GRN, width=3)
    d.line([T(DOOR_X, ROAD_Z - DOOR_W / 2), T(DOOR_X, ROAD_Z + DOOR_W / 2)], fill=GRN, width=8)
# ---------- overview ----------
s1, T1, sz1 = panel(40, 165, 2320, 420, 262, 1165, -62, 42, 'OVERVIEW  ·  Refinery | Cargo Dock | Launch Pad  ->  transport road  ->  Shipyard | Habitat | Engineering', step=50)
for nm, col in (('Refinery', (170, 150, 120)), ('CargoDock', (120, 170, 220)), ('LaunchPad', (200, 205, 215)), ('Shipyard', (180, 200, 150))): grid_fp(T1, nm, col)
berm(T1)
for zl in (13, 22): d.line([T1(296, zl), T1(464, zl)], fill=AM + (230,), width=3)
d.line([T1(274, 9), T1(262, 9)], fill=(220, 140, 80), width=4); d.line([T1(274, 0), T1(262, 0)], fill=(220, 140, 80), width=4)
road(T1, s1, PAD_EDGE, DOOR_X); hab(T1); hall(T1); foot(T1, SHIP[0], CY)
for nm, x, col, sub_ in (('REFINERY', 296, (230, 210, 170), 'x 320'), ('CARGO DOCK', 340, (150, 200, 255), 'x 360, 20 slots'), ('LAUNCH PAD', 436, INK, 'x 457'),
                        ('SHIPYARD', 918, (200, 230, 160), 'x 960'), ('HABITAT', 1052, HABC, 'x 1068'), ('ENGINEERING', 1098, (200, 205, 215), 'x 1120')):
    label(T1, x, -58, nm, col, 17); label(T1, x, -51.5, sub_, DIM, 13, False)
label(T1, 760, 9.5, 'old Habitat x 800: removed', RED, 12, False)
label(T1, 520, -38, f'SHIP TRANSPORT ROAD · {2*HALF:.1f} m · crawler-track surface · {road_len:.0f} m straight', CY, 16)
label(T1, 296, 26, 'flatbed route + pad U-turn (z +13 / +22)', AM, 13); label(T1, 263, 3, 'haul rd', (220, 140, 80), 12)
scalebar(T1, 560, 30, 100, 20)
end_panel()
# ---------- detail 1: pad exit ----------
y2 = 165 + sz1[1] + 60
s2, T2, sz2 = panel(40, y2, 900, 560, 418, 566, -60, 32, 'A · PAD RIGHT-SIDE EXIT (AA2 Lv1 pad; pipe end at the pad LEFT (430, 2.6))', step=10)
grid_fp(T2, 'LaunchPad', (200, 205, 215)); berm(T2)
gz0, gz1 = ROAD_Z - TR['half'] - 1.2, ROAD_Z + TR['half'] + 1.2
d.rectangle([T2(PADX + 18.5, gz0), T2(PAD_EDGE, gz1)], fill=(255, 80, 70, 70), outline=RED, width=3)
road(T2, s2, PAD_EDGE, 566)
for b in pad_hits: d.rectangle([T2(b[0], b[1]), T2(b[2], b[3])], fill=(255, 80, 70, 110), outline=RED, width=2)
d.ellipse([T2(458, 10.2), T2(465.3, 24.8)], outline=AM, width=3); label(T2, 466, 18, 'pad U-turn', AM, 13)
for zl in (13, 22): d.line([T2(418, zl), T2(458, zl)], fill=AM, width=3)
fh = T2(460.85, -15.0); d.ellipse([fh[0] - 6, fh[1] - 6, fh[0] + 6, fh[1] + 6], outline=AM, width=3)
pe = T2(PIPE_END[0], PIPE_END[2]); d.ellipse([pe[0] - 6, pe[1] - 6, pe[0] + 6, pe[1] + 6], fill=GRN); label(T2, PIPE_END[0] + 1.5, PIPE_END[2] + 1.2, f'pipe end (430, 0.95, 2.6): {CL["pipe_end"]["clear_of_crawler_at_pickup_m"]:.1f} m clear', GRN, 12)
for zz in G1['z']: d.line([T2(PAD_EDGE - 3, zz), T2(PAD_EDGE + 1, zz)], fill=AM, width=4)
label(T2, PAD_EDGE + 1.5, G1['z'][1] + 1.0, 'G-1 30.8 m (unchanged)', AM, 12)
ov = T2(477.3, -9.6); d.line([ov[0] - 6, ov[1] - 6, ov[0] + 6, ov[1] + 6], fill=GRN, width=3); d.line([ov[0] - 6, ov[1] + 6, ov[0] + 6, ov[1] - 6], fill=GRN, width=3)
foot(T2, SHIP[0], CY, 'ST-10 pick-up')
def tag(T, x, z, k):
    p = T(x, z); d.ellipse([p[0] - 12, p[1] - 12, p[0] + 12, p[1] + 12], fill=RED, outline=(255, 255, 255)); d.text(p, str(k), font=font(15, True), fill=(255, 255, 255), anchor='mm')
tag(T2, PAD_EDGE - 1.5, -31.0, 1); tag(T2, 444.4, -5.6, 2); tag(T2, 460.85, -19.5, 3); tag(T2, 452.0, 2.6, 4)
for i, t_ in enumerate(['1 gate G-1 30.8 m (z -28.4..+2.4): unchanged; ST-10A 27.1 m passes, 1.84 m each side',
                        '2 Pad_Base item 9.3 m (443.6-445.1, -3.4..-2.7) + Tier_08 1.5 m (445.0-445.3, -0.8..-0.6):',
                        '   inside the crawler front-left at pick-up (front x 443.6): move >= 1 m west (AA2)',
                        '3 Fuel_Hookup (460.85,-15): disconnect + retract before lift', '4 Tier_12 edge lights 0.37 m: drive-over',
                        'Lv10 pad gate G-10 widens to 34.6 m (road width); Lv1 G-1 does not', 'x VV-1 (477.3,-9.6) and old (430,-9.6) pipe end: retired']):
    label(T2, 419.5, -59 + 2.6 * i, t_, RED if i < 4 else (AM if i < 6 else GRN), 13)
scalebar(T2, 530, 28, 20, 5)
end_panel()
# ---------- detail 2: habitat ----------
s3, T3, sz3 = panel(980, y2, 520, 560, 1000, 1140, -55, 50, 'B · HABITAT EAST OF SHIPYARD (x 1068)', step=10)
grid_fp(T3, 'Shipyard', (180, 200, 150)); hab(T3, ghost=False)
for xa, xb, zz, t_ in ((SY_X1, HAB['x0'], 8.5, f'{GAP_W:.1f} m'), (HAB['x1'], ENG['x0'], 8.5, f'{GAP_E:.1f} m')):
    d.line([T3(xa, zz), T3(xb, zz)], fill=INK, width=2)
    for xe in (xa, xb): d.line([T3(xe, zz - 1.5), T3(xe, zz + 1.5)], fill=INK, width=2)
    label(T3, (xa + xb) / 2, zz + 2.2, t_, INK, 13, anchor='ma')
d.line([T3(SY_X1, -50), T3(SY_X1, 48)], fill=(180, 200, 150, 160), width=1)
label(T3, HAB_X, -6.5, 'HABITAT', HABC, 13, anchor='md'); label(T3, 1120, -6, 'ENGINEERING', (200, 205, 215), 12, anchor='md')
label(T3, 1005, -53, f'Shipyard east edge x {SY_X1:.1f}', (200, 230, 160), 12, False)
label(T3, 1026, 20, 'Habitat 9 x 12 x 9 m at (1068, 0): z unchanged,', HABC, 12, False)
label(T3, 1026, 23, 'not toward the camera; HB-10 is on the', HABC, 12, False)
label(T3, 1026, 26, 'Shipyard WEST side, so it is not crowded.', HABC, 12, False)
label(T3, 1026, 31, 'Engineering (1120, 0): unchanged.', (200, 205, 215), 12, False)
label(T3, 1026, 36, 'Old x 800 spot removed: road corridor clear,', GRN, 12, False)
label(T3, 1026, 39, 'no jog, no S-bend.', GRN, 12, False)
scalebar(T3, 1100, 41, 20, 5)
end_panel()
# ---------- detail 3: shipyard ----------
s4, T4, sz4 = panel(1540, y2, 820, 560, 820, 1000, -60, 40, 'C · SHIPYARD END: Lv10 HIGH BAY HB-10 + DOOR D-10 (proposal)', step=10)
grid_fp(T4, 'Shipyard', (180, 200, 150)); road(T4, s4, 820, DOOR_X)
d.rectangle([T4(APRON[0], ROAD_Z - 22), T4(APRON[1], ROAD_Z + 22)], outline=(235, 235, 225), width=2)
hall(T4)
for x, z, h in blk: d.rectangle([T4(x, z), T4(x + 2, z + 2)], outline=RED, width=1)
foot(T4, (BAY[0] + BAY[2]) / 2, CY, 'ST-10 inside HB-10')
label(T4, DOOR_X - 1, ROAD_Z + DOOR_W / 2 + 1.5, f'D-10  {DOOR_W:.0f} m W x {DOOR_H:.0f} m H', GRN, 15, anchor='ra')
label(T4, BAY[0] + 1, BAY[1] - 4.5, f'HB-10 {BAY_L:.0f} x {BAY_W:.0f} m, {BAY_H:.0f} m tall', GRN, 14)
label(T4, APRON[0] + 1, ROAD_Z + 22.8, 'apron RA-1 44 x 44 m', INK, 13)
hx, hz = sum(p[0] for p in HALL) / 4, sum(p[1] for p in HALL) / 4
label(T4, hx, hz, 'AH-1 (24 m)', (220, 240, 180), 14, anchor='mm')
label(T4, 925, 15.5, 'existing door 10.3 m, faces camera,', AM, 12); label(T4, 925, 18, '8-14 m forecourt: not used', AM, 12)
scalebar(T4, 940, 35, 20, 5)
end_panel()
# ---------- door elevation ----------
y5 = y2 + 600
s5, T5, sz5 = panel(40, y5, 900, 330, -26, 26, -52, 2, 'D · DOOR D-10 ELEVATION (looking east from the road, Lv2-height ship loaded on ST-10A)', step=10)
E = lambda x, h: T5(x, -h)
d.rectangle([E(-DOOR_W / 2, DOOR_H), E(DOOR_W / 2, 0)], outline=GRN, width=4)
d.rectangle([E(-TR['half'], TR['tower_top']), E(TR['half'], 0)], outline=CY, width=2)
d.polygon([E(-4.0, 0.7), E(4.0, 0.7), E(4.0, 36.5), E(3.0, 41.5), E(0, TR['height_loaded']), E(-3.0, 41.5), E(-4.0, 36.5)], fill=(200, 205, 215, 200))
d.line([E(-6.6, 0.45), E(6.6, 0.45)], fill=(200, 205, 215), width=4)
d.rectangle([E(-26, 0), E(26, -1.5)], fill=(92, 88, 82))
label(T5, -DOOR_W / 2 + 0.5, -DOOR_H + 1, f'{DOOR_W:.0f} m clear width', GRN, 14); label(T5, DOOR_W / 2 + 0.5, -DOOR_H / 2, f'{DOOR_H:.0f} m', GRN, 14)
label(T5, -13.4, -36.5, f'ST-10A {2*TR["half"]:.1f} m', CY, 12); label(T5, 4.6, -TR['height_loaded'] + 0.5, f'ship top {TR["height_loaded"]} m (Lv2 43.85 m, lifted 0.45): {DOOR_H - TR["height_loaded"]:.2f} m under D-10', RED, 12); label(T5, -6.6, -2.6, 'Lv10 gear R 6.6 m', DIM, 12, False)
end_panel()
# ---------- notes ----------
notes = [
 ('ROAD', INK, f'Centreline world z -13 (the pad ship axis) from the pad edge x {PAD_EDGE:.1f} to door D-10 at x {DOOR_X:.1f}: {road_len:.1f} m, one straight, 0 turns, 0% grade, 0.5% cross-fall. {2*HALF:.1f} m running (ST-10A 27.1 m + 3.75 m each side) + 2.6 m graded shoulders = {2*(HALF+SHOULDER):.1f} m. Sintered surface with two darker crawler lanes (|dz| 9.7-13.3 m, 0.62 m cleat imprints), no tyre trails; cyan (far) / amber (near) reflector posts every 12 m.'),
 ('', DIM, 'Autonomous and cab-less, ST-10 runs both ways on the same road (out loaded, back loaded after the rebuild): no turnaround loop. Apron RA-1 in front of D-10 is the staging and passing pad.'),
 ('KEEP-OUT', GRN, f'Haul road: Refinery left side (x <= 321), {PAD_EDGE - 321:.0f} m away. Flatbed lanes z +13/+22 and the pad U-turn (x 458-465, z 10-25): road shoulder edge stays at z <= {ROAD_Z + HALF + SHOULDER:+.1f} ({fl_gap:.1f} m from the flatbed lane, {ut_gap:.1f} m from the U-turn) and starts at the pad edge x {PAD_EDGE:.1f}: crosses no road. Cargo Dock compact_v3 at (360, 0, -8) (bbox x {CL["cargo_dock"]["bbox_world"][0][0]:.1f}-{CL["cargo_dock"]["bbox_world"][1][0]:.1f}) is LEFT of the pad: {CL["cargo_dock"]["gap_to_road_m"]:.1f} m from the road start, {CL["cargo_dock"]["gap_to_crawler_path_m"]:.1f} m from the crawler at pick-up. Pipe end (430, 0.95, 2.6) is {CL["pipe_end"]["clear_of_crawler_at_pickup_m"]:.1f} m clear.'),
 ('(a) PAD', RED, f'Pad owner (AA2), not edited here. Lv1 pad gate G-1 stays 30.8 m (z -28.4..+2.4): ST-10A passes with 1.84 m each side. Only the Lv10 pad gate G-10 widens, to the road running width {2*HALF:.1f} m (z {ROAD_Z-HALF:.1f}..{ROAD_Z+HALF:+.1f}). Open item: a 9.3 m Pad_Base item (443.6-445.1, -3.4..-2.7) and a 1.5 m Tier_08 skid (445.0-445.3, -0.8..-0.6) sit inside the crawler front-left at pick-up: move >= 1 m west. Fuel_Hookup: disconnect + retract before lift. Pipe_LaunchPad_End is at the pad LEFT (430, 0.95, 2.6). Edge lights 0.37 m are drive-over.'),
 ('(b) HABITAT', HABC, f'Station order Life Support, Mine, Refinery, Cargo Dock, Launch Pad, Shipyard, Habitat, Engineering (Director). Habitat gray box moves from x 800 (inside the corridor) to x {HAB_X:.0f}, z 0: {GAP_W:.1f} m clear of the Shipyard east edge (x {SY_X1:.1f}) and {GAP_E:.1f} m clear of Engineering (x 1120, unchanged). The road path is clear end to end; the S-jog fallback is withdrawn. Per-station X table for Coder: transport_road_plan.json station_x_table.'),
 ('(c) SHIPYARD', AM, f'Existing door: 10.3 m, faces the camera, 8-14 m forecourt. Proposal (Director ruling): Lv10 high bay HB-10 {BAY_L:.0f} x {BAY_W:.0f} x {BAY_H:.0f} m on the west gable of AH-1, door D-10 {DOOR_W:.0f} m W x {DOOR_H:.0f} m H facing the road, on the road axis.'),
 ('', AM, f'D-10 sizing: ST-10A 27.1 m wide, {(DOOR_W - 2*TR["half"])/2:.2f} m each side. Height FLAG: with the Lv2 ship (43.85 m; no Lv10 height exists yet) the loaded top is {TR["height_loaded"]} m, {DOOR_H - TR["height_loaded"]:.2f} m under D-10 {DOOR_H:.0f} m (v3 assumed the Lv1 ship at 40.7 m). {len(blk)} Shipyard cells (red) inside HB-10 + RA-1 must clear. This is a Shipyard model change, so it is flagged to the Shipyard owner. The Shipyard GLB is not edited here.'),
]
y = y5 + 400
for tg, col, t_ in notes:
    if tg: d.text((40, y), tg, font=font(17, True), fill=col)
    words, line, lines = t_.split(), '', []
    for w in words:
        if d.textlength(line + ' ' + w, font=font(16)) > 2120: lines.append(line); line = w
        else: line = (line + ' ' + w).strip()
    lines.append(line)
    for ln in lines: d.text((230, y), ln, font=font(16), fill=INK if col != DIM else DIM); y += 22
    y += 5
img = img.crop((0, 0, W, y + 20)); img.save(os.path.join(P, 'transport_road_plan_topdown.png'))
print('WEST_X', round(WEST_X, 1), 'DOOR_X', round(DOOR_X, 1), 'len', round(road_len, 1), 'travel', round(travel, 1), 'blk', len(blk), 'size', img.size)
