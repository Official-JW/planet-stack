"""Crew walk-blocker fitter: raster (raster.mjs) -> oriented boxes (+ convex hulls for round things) with 0.3 m padding, walk gaps, checks.
nice -n 19 python3 fit.py RASTER_DIR  -> ../colliders.json  (world glTF metres, +X right, +Z toward camera, Y up)"""
import json, math, sys, os, hashlib
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull
H = os.path.dirname(os.path.abspath(__file__)); R = sys.argv[1]
M = json.load(open(os.path.join(R, 'meta.json'))); C = M['cell']; PAD = 0.3
CFG = json.load(open(os.path.join(H, 'cfg.json')))
def disk(r):
    k = int(math.ceil(r)); y, x = np.mgrid[-k:k + 1, -k:k + 1]; return (x * x + y * y) <= r * r + 1e-6
def min_rect(pts):
    h = pts[ConvexHull(pts).vertices]; best = None
    for i in range(len(h)):
        e = h[(i + 1) % len(h)] - h[i]; L = np.hypot(*e)
        if L < 1e-9: continue
        u = e / L; v = np.array([-u[1], u[0]]); a = h @ u; b = h @ v
        A = (a.max() - a.min()) * (b.max() - b.min())
        if best is None or A < best[0] - 1e-9: best = (A, u, v, a.min(), a.max(), b.min(), b.max())
    A, u, v, a0, a1, b0, b1 = best; c = u * (a0 + a1) / 2 + v * (b0 + b1) / 2
    hu, hv = (a1 - a0) / 2, (b1 - b0) / 2
    if hv > hu: u, v, hu, hv = v, -u, hv, hu            # local X = long axis
    return c, u, hu, hv, A, h
def corners(ij, X0, Z0):
    i, j = ij[:, 1].astype(float), ij[:, 0].astype(float); x0 = X0 + i * C; z0 = Z0 + j * C
    return np.concatenate([np.stack([x0, z0], 1), np.stack([x0 + C, z0], 1), np.stack([x0, z0 + C], 1), np.stack([x0 + C, z0 + C], 1)])
def split(ij, X0, Z0, depth=0):
    pts = corners(ij, X0, Z0); c, u, hu, hv, A, _ = min_rect(pts); area = len(ij) * C * C; fill = area / A
    if fill >= (0.78 if area > 20 else 0.70) or area < 3.0 or depth >= 9: return [ij]
    v = np.array([-u[1], u[0]]); cen = np.stack([X0 + (ij[:, 1] + .5) * C, Z0 + (ij[:, 0] + .5) * C], 1)
    best = None
    for ax in (u, v):
        p = cen @ ax; lo, hi = p.min(), p.max()
        for t in np.linspace(lo, hi, 34)[1:-1]:
            s = 0
            for m in (p < t, p >= t):
                q = cen[m]
                if len(q) == 0: s = 1e18; break
                a = q @ u; b = q @ v; s += (np.ptp(a) + C) * (np.ptp(b) + C)
            if best is None or s < best[0]: best = (s, ax, t)
    if best is None: return [ij]
    s, ax, t = best; p = cen @ ax; out = []
    for m in (p < t, p >= t):
        sub = ij[m]; g = np.zeros((sub[:, 0].max() + 3, sub[:, 1].max() + 3), bool); g[sub[:, 0], sub[:, 1]] = True
        lab, n = ndi.label(g, np.ones((3, 3)))
        for k in range(1, n + 1): out += split(np.argwhere(lab == k), X0, Z0, depth + 1)
    return out
def cr2(a, b): return a[0] * b[1] - a[1] * b[0]
def pad_hull(h, r):
    a = np.linspace(0, 2 * math.pi, 16, endpoint=False); ring = np.stack([np.cos(a), np.sin(a)], 1) * r
    P = (h[:, None, :] + ring[None]).reshape(-1, 2); hh = P[ConvexHull(P).vertices]
    while len(hh) > 24:                                   # drop the vertex whose removal loses the least area
        n = len(hh); ar = [abs(cr2(hh[i] - hh[i - 1], hh[(i + 1) % n] - hh[i - 1])) for i in range(n)]; hh = np.delete(hh, int(np.argmin(ar)), 0)
    return hh
def yaw_of(u): y = math.degrees(math.atan2(-u[1], u[0])); y = (y + 90) % 180 - 90; return round(y, 2)
items = {it['id']: it for it in M['items']}; cfgi = {it['id']: it for it in CFG['items']}
colliders = []
for iid, it in items.items():
    NX, NZ, X0, Z0 = it['NX'], it['NZ'], it['X0'], it['Z0']
    G = np.fromfile(os.path.join(R, iid + '.bin'), np.uint8).reshape(NZ, NX); Y = np.fromfile(os.path.join(R, iid + '_y.bin'), np.float32)
    LO, HI = Y[:NX * NZ].reshape(NZ, NX), Y[NX * NZ:].reshape(NZ, NX)
    B = G > 0; B = ndi.binary_closing(B, np.ones((3, 3)), border_value=0) | B
    enc = ndi.binary_fill_holes(B) & ~B                           # enclosed cells: solid when their lowest geometry is above the band (inside a closed volume:
    B |= enc & (LO >= M['band'][1]) & (LO < 1e8)                  # building interior with no floor, berm crest, tank top); floors at walking level stay open
    hl, nh = ndi.label(ndi.binary_fill_holes(B) & ~B)
    for h in range(1, nh + 1):
        m = hl == h
        if m.sum() * C * C < 4.0 or float((HI[m] >= M['band'][1]).mean()) >= 0.6: B |= m   # unreachable crannies < 4 m2, or roofed interiors (hall, stack, airlock)
    grp, n = ndi.label(ndi.binary_dilation(B, disk(PAD / C)), np.ones((3, 3)))
    k = 0
    for g in range(1, n + 1):
        ij = np.argwhere(B & (grp == g))
        if len(ij) == 0: continue
        leaves = split(ij, X0, Z0); gid = f'{iid}_g{g:02d}'
        for lf in leaves:
            k += 1; pts = corners(lf, X0, Z0); c, u, hu, hv, A, hull = min_rect(pts); area = len(lf) * C * C
            lo = LO[lf[:, 0], lf[:, 1]]; hi = HI[lf[:, 0], lf[:, 1]]; okc = hi > -1e8
            ymin = float(lo[okc].min()) if okc.any() else 0.0; ymax = float(hi[okc].max()) if okc.any() else 0.0
            holes = float((G[lf[:, 0], lf[:, 1]] == 2).mean()); hull_fill = area / ConvexHull(pts).volume; fill = area / A
            asp = hu / max(hv, 1e-6)
            hp = ConvexHull(pts); circ = hp.area ** 2 / (4 * math.pi * hp.volume)
            kind = 'pit' if holes > 0.5 else 'round' if (hull_fill >= 0.88 and 0.70 <= fill <= 0.86 and asp < 1.3 and circ < 1.12) else 'linear' if asp > 5 else 'structure' if area >= 30 else 'prop'
            if abs(abs(yaw_of(u)) - 90) < 1e-6: u, hu, hv = np.array([1.0, 0.0]), hv, hu       # a +-90 deg box = a 0 deg box with swapped halves
            e = dict(id=f'{iid}_{k:02d}_{kind}', station=it['station'], item=iid, group=gid, kind=kind,
                     src_glb=os.path.relpath(os.path.join(H, it['file']), os.path.join(H, '..', '..', '..', '..')), src_md5=it['md5'], pos_src=cfgi[iid]['pos_src'],
                     box=dict(cx=round(float(c[0]), 3), cz=round(float(c[1]), 3), hx=round(hu + PAD, 3), hz=round(hv + PAD, 3), yaw_deg=yaw_of(u),
                              y_min=round(min(ymin, 0.0) if kind != 'pit' else ymin, 3), y_max=round(ymax, 3)),
                     raw_half=[round(hu, 3), round(hv, 3)], fill_box=round(fill, 3))
            if fill < 0.86 and hull_fill >= 0.85 and len(lf) >= 12:
                e['hull'] = [[round(float(x), 3), round(float(z), 3)] for x, z in pad_hull(hull, PAD)]; e['fill_hull'] = round(hull_fill, 3)
            if dynamic := cfgi[iid].get('dynamic'): e['dynamic'] = dynamic
            colliders.append(e)
# --- placeholders (no GLB yet) ---
for sid, st, (cx, cz), (w, d), h in [('habitat', 'Habitat', (1068.0, 0.0), (9, 9), 12), ('engineering', 'Engineering', (1120.0, 0.0), (10, 8), 8)]:
    colliders.append(dict(id=f'{sid}_01_placeholder', station=st, item=sid, group=f'{sid}_g01', kind='placeholder', src_glb=None, src_md5=None,
        pos_src=f'road plan 1df3e3d transport_road_plan.json {sid} footprint (= qa3d-next SIZES gray box {w}x{h}x{d}); NO GLB yet',
        box=dict(cx=cx, cz=cz, hx=w / 2 + PAD, hz=d / 2 + PAD, yaw_deg=0.0, y_min=0.0, y_max=float(h)), raw_half=[w / 2, d / 2], fill_box=1.0, unresolved=True))
# --- geometry tests ---
def obb_poly(e, extra=0.0):
    b = e['box']; t = math.radians(b['yaw_deg']); u = np.array([math.cos(t), -math.sin(t)]); v = np.array([-u[1], u[0]]); c = np.array([b['cx'], b['cz']])
    return np.array([c + sx * (b['hx'] + extra) * u + sz * (b['hz'] + extra) * v for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
def shape(e): return np.array(e['hull']) if 'hull' in e else obb_poly(e)
def inside(poly, P):                                       # convex poly (either winding), P (n,2) -> bool
    s = None
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]; cr = (b[0] - a[0]) * (P[:, 1] - a[1]) - (b[1] - a[1]) * (P[:, 0] - a[0])
        s = (cr >= 0) if s is None else s
        if i == 0: pos = cr >= -1e-9; neg = cr <= 1e-9
        else: pos &= cr >= -1e-9; neg &= cr <= 1e-9
    return pos | neg
SH = [(e, shape(e)) for e in colliders]
def blockers_at(P, station=None):
    hit = np.zeros(len(P), bool); ids = set()
    for e, poly in SH:
        bx = e['box']
        if station and e['station'] != station: continue
        m = inside(poly, P)
        if m.any(): hit |= m; ids.add(e['id'])
    return hit, ids
def rect_pts(cx, cz, ux, uz, a0, a1, hw, step=0.1):
    u = np.array([ux, uz]); v = np.array([-uz, ux]); A, Bv = np.meshgrid(np.arange(a0, a1 + 1e-9, step), np.arange(-hw, hw + 1e-9, step))
    return np.array([cx, cz]) + A.reshape(-1, 1) * u + Bv.reshape(-1, 1) * v
def rect_rec(gid, st, kind, cx, cz, ux, uz, a0, a1, hw, note):
    u = np.array([ux, uz]); mid = np.array([cx, cz]) + u * (a0 + a1) / 2; yaw = math.degrees(math.atan2(-uz, ux))
    _, ids = blockers_at(rect_pts(cx, cz, ux, uz, a0, a1, hw), st)
    return dict(id=gid, station=st, kind=kind, cx=round(float(mid[0]), 3), cz=round(float(mid[1]), 3), hx=round((a1 - a0) / 2, 3), hz=round(hw, 3), yaw_deg=round(yaw, 2), cuts=sorted(ids), note=note)
def corridor(gid, st, x, z, w, note, back=0.5, hint=None):
    best = None
    for a in ([hint] if hint is not None else np.arange(0, 360, 5.0)):
        u = (math.cos(math.radians(a)), math.sin(math.radians(a)))
        for t in np.arange(0, 10.01, 0.1):
            hit, _ = blockers_at(rect_pts(x, z, *u, t, t + 0.8, w / 2), st)
            if not hit.any():
                if best is None or t < best[0]: best = (t, u)
                break
    if best is None: return dict(id=gid, station=st, kind='corridor', x=x, z=z, unresolved=True, note=note + ' | NO clear exit within 10 m')
    t, u = best; r = rect_rec(gid, st, 'corridor', x, z, u[0], u[1], -back, t + 0.4, w / 2, note + (f' | exit direction fixed: {hint} deg (atan2 z, x)' if hint is not None else ' | exit direction: shortest of 72 searched')); r['marker_xz'] = [round(x, 3), round(z, 3)]; r['clear_from_m'] = round(float(t), 2); return r
mk = {iid: it['markers'] for iid, it in items.items()}
gaps = []
GAPDEF = [('gap_ls_airlock', 'Life Support', mk['life_support']['Airlock_Door'], 1.6, 'Airlock_Door: crew door at the back of the covered entrance porch (railings x +-1.5, roof y 4.1, steps to z 11.6)', 90),
          ('gap_mine_operator_deck', 'Mine', mk['mine']['Operator_Deck'], 1.2, 'Operator_Deck (operator crew spot)', None),
          ('gap_dock_door', 'Cargo Dock', mk['cargo_dock']['Dock_Door'], 2.0, 'Dock_Door (hall front, faces +Z toward the gantry yard)', 90),
          ('gap_pad_ladder_foot', 'Launch Pad', mk['launch_pad']['Ladder_Foot'], 1.2, 'Ladder_Foot: caged ladder to the hatch at y 21.9 (ship on pad)', None),
          ('gap_pad_receiver_home', 'Launch Pad', mk['launch_pad']['Receiver_Home'], 1.2, 'Receiver_Home at the AL-2 airlock door (east face)', 0),
          ('gap_pad_receiver_spot', 'Launch Pad', mk['launch_pad']['Receiver_Spot'], 1.2, 'Receiver_Spot (faces the FB-05 bed)', None),
          ('gap_shipyard_hall_door', 'Shipyard', mk['shipyard']['Hall_Door'], 2.0, 'Hall_Door (AH-1 hall, faces +Z)', 90),
          ('gap_shipyard_hall_door_front', 'Shipyard', mk['shipyard']['Hall_Door_Front'], 2.0, 'Hall_Door_Front (forecourt)', None)]
for gid, st, m, w, note, hint in GAPDEF: gaps.append(corridor(gid, st, m[0], m[2], w, note, hint=hint))
# truck cab doors (HT-04 / FB-05 share the cab: truck-local +X forward, cab door at local x ~2.6, body half-width 2.0): 1.2 x 1.2 m step-out pad each side
TRUCKS = [('mine_load', 'Mine', 'HT-04', mk['mine']['Path_Load']), ('refinery_dump', 'Refinery', 'HT-04', mk['refinery']['Truck_Dump']),
          ('refinery_rc1_park', 'Refinery', 'FB-05', mk['crane_rc1']['Truck_Park']), ('dock_sc1_stop', 'Cargo Dock', 'FB-05', mk['crane_sc1']['Truck_Stop_Dock']),
          ('pad_stop', 'Launch Pad', 'FB-05', mk['launch_pad']['Truck_Stop'])]
for tid, st, tr, m in TRUCKS:
    yaw = math.radians(m[3]); fx, fz = math.cos(yaw), -math.sin(yaw); sx, sz = -fz, fx
    for side, sg in (('L', -1), ('R', 1)):
        cx, cz = m[0] + 2.6 * fx + sg * 2.6 * sx, m[2] + 2.6 * fz + sg * 2.6 * sz
        r = rect_rec(f'gap_cab_{tid}_{side}', st, 'cab_door', cx, cz, fx, fz, -0.6, 0.6, 0.6, f'{tr} cab door step-out at its stop pose ({m[0]}, {m[2]}) yaw {m[3]}')
        r['truck_pose'] = dict(x=m[0], z=m[2], yaw_deg=m[3]); gaps.append(r)
# roads must stay walkable: haul / flatbed / transporter road bands (approved layout) vs colliders
ROADS = [('transporter road ST-10 (graded 41.2 m)', 486.4, 880.1, -13 - 20.6, -13 + 20.6), ('flatbed lane E z 13', 296, 464, 10.2, 15.8), ('flatbed lane W z 22', 296, 464, 19.2, 24.8)]
road_hits = []
for name, x0, x1, z0, z1 in ROADS:
    xs, zs = np.meshgrid(np.arange(x0, x1, 0.25), np.arange(z0, z1, 0.25)); P = np.stack([xs.ravel(), zs.ravel()], 1)
    for e, poly in SH:
        m = inside(poly, P)
        if m.any(): road_hits.append(dict(road=name, collider=e['id'], kind=e['kind'], area_m2=round(float(m.sum()) * 0.0625, 2), y_max=e['box']['y_max']))
for e in colliders:
    e.pop('raw_half', None)
    if e['item'] in items:                                   # nearest named marker of the same GLB, for a human-readable hint
        b = e['box']; best = min(((math.hypot(v[0] - b['cx'], v[2] - b['cz']), k) for k, v in items[e['item']]['markers'].items()), default=None)
        if best and best[0] < 12: e['near'] = f'{best[1]} ({best[0]:.1f} m)'
STN = ['Life Support', 'Mine', 'Refinery', 'Cargo Dock', 'Launch Pad', 'Shipyard', 'Habitat', 'Engineering']
out = dict(version=1, units='world glTF metres: +X right, +Z toward the game camera, Y up (Lv1: Tier_* hidden)',
  method=f'triangles sampled at <= {C/2} m, a {C} m cell blocks when any sample lies in the crew body band y {M["band"][0]}..{M["band"][1]} m (lower = steps/slabs/roads you walk on, '
         f'higher = overhead: bridge deck, jibs, pipe racks) or when the cell only has geometry below -{M["hole"]} m (pit). Closing 3x3 + hole fill (thin walls / enclosures -> solid), '
         f'objects < 0.6 m apart grouped, groups split until each oriented box is >= 70% filled; every box/hull padded by {PAD} m. Vehicles (HT-04, FB-05), crew (Receiver, operator), '
         'moving crane hooks/hoists and the bridge boxes are NOT colliders.',
  box_convention='box = oriented rectangle: centre (cx, cz), half-extents hx (local X) / hz (local Z) INCLUDING the 0.3 m pad, yaw_deg = three.js rotation.y (local +X -> world (cos yaw, -sin yaw)), y_min..y_max = geometry height range over the footprint',
  hull_convention='hull (optional, use instead of the box when present) = convex polygon [x, z] world, padding included; given for round tanks/columns where the box is a poor fit',
  walkable_rule='a point is walkable unless inside a collider (hull if present, else box) - EXCEPT inside any walk_gaps rectangle (same box convention, no extra pad), which is always walkable',
  pad_m=PAD, band_m=M['band'], cell_m=C,
  sources=dict(stations='art/3d/vehicles/ship_transporter/proofs/transport_road_plan.json @ 1df3e3d (road v2 approved, v3 station table; 3c7df36 still had the Habitat at x 800)',
               cargo_dock='art/3d/buildings/cargo_dock/layout_v3 @ cae8f39 (dock x 360 z -8, SC-1, RC-1, flatbed lanes)', glbs='as listed per entry (md5 = of the file read)'),
  stations=STN, count=len(colliders), groups=len({e['group'] for e in colliders}), count_by_station={st: sum(e['station'] == st for e in colliders) for st in STN}, colliders=colliders, walk_gaps=gaps, road_overlaps=road_hits,
  unresolved=['Habitat: no GLB, collider = road-plan gray box placeholder (1068, 0) 9 x 12 x 9', 'Engineering: no GLB, collider = gray box placeholder (1120, 0) 10 x 10 x 8',
              'Launch Pad Lv1 elevator tower / launch_pad_game_lv1door.glb is uncommitted (other agent): pad uses the committed launch_pad_game.glb 82131aba; its ladder is the ship-side caged ladder (Ladder_Foot gap)',
              'qa3d-next still loads Shipyard bcbd0934 and the old dock_tankfarm (7959ae74): colliders follow the approved layout GLBs (Shipyard c0e9d54e per the road plan, Dock compact_v3 9fb1ddbe)',
              'HB-10 Lv10 high bay (road plan proposal) has no GLB and is not Lv1: no collider'])
json.dump(out, open(os.path.join(H, '..', 'colliders.json'), 'w'), indent=1)
from collections import Counter
print('colliders', len(colliders), Counter(e['station'] for e in colliders), Counter(e['kind'] for e in colliders))
for g in gaps: print(g['id'], g.get('clear_from_m'), g.get('cuts'), g.get('unresolved', ''))
for r in road_hits: print('ROAD', r)
