#!/usr/bin/env python3
"""ST-10A cradle / body clearance vs the Lv10 aft skirt (N06 + N11), gear legs (deployed, retracted, every 0.1 s of Gear_Retract and
Gear_Deploy), skirt band + gear doors, engine ring + nozzles, and the Lv2 hull. Light check: numpy + scipy KD-tree (upper bound 6 m), no renders; ~1-3 min single core.
Inputs (read-only): st10a raw geometry npz (build_st10a_game.py), /workspace/st10a/ship_skirt_measure.json (measure_ship.mjs: skinned
skirt verts per pose, from art/vfx/engine_flame/aft_skirt/aft_skirt_N06.glb + N11.glb, and the hull verts of art/3d/ship/ship_lv2/pad_lv2.glb).
Ship placement: ship root = Ship_Seat (0, 0.45, 0) when LOADED; module origin at ship-frame Y_M; yaw sweep. EMPTY = ship standing on the pad
(root y 0, gear deployed) while the transporter drives in through the open end (ship x offset -32 .. 0 m in transporter frame).
  python3 clearance_st10a.py geom.npz measure.json out.json"""
import json, math, sys
import numpy as np
from scipy.spatial import cKDTree
GEOM, MEAS, OUT = sys.argv[1:4]
H = 0.40    # transporter surface sampling step (m), edge-aware grid -> distances exact to about +-0.3 m (box hold: light check)
UB = 4.0    # distances >= UB reported as ">= 4" (KD upper bound keeps this a light check)
g = np.load(GEOM); d = json.load(open(MEAS))
def sample(P, I, lo, hi, h=H):
    T = P[I.reshape(-1, 3)]; keep = (T.max(1) >= lo).all(1) & (T.min(1) <= hi).all(1); T = T[keep]; out = [T.reshape(-1, 3)]
    for a, b, c in T:
        na, nc = int(math.ceil(np.linalg.norm(b - a) / h)), int(math.ceil(np.linalg.norm(c - a) / h))
        if na <= 1 and nc <= 1: continue
        u, v = np.meshgrid(np.linspace(0, 1, na + 1), np.linspace(0, 1, nc + 1)); m = u + v <= 1 + 1e-9; u, v = u[m], v[m]
        out.append(a + u[:, None] * (b - a) + v[:, None] * (c - a))
    return np.vstack(out)
def part(keys, lo, hi):
    return np.vstack([sample(g[k + '_P'].astype(float), g[k + '_I'], np.array(lo), np.array(hi)) for k in keys])
LO_S, HI_S = [-46, -1, -14], [14, 17.5, 14]          # region the skirt / gear can reach (loaded + 32 m drive-in) + UB margin
trees = {'body': cKDTree(part(['body', 'cyan', 'amber'], LO_S, HI_S)), 'cradle_loaded': cKDTree(part(['cl'], LO_S, HI_S)),
         'cradle_empty': cKDTree(part(['ce'], LO_S, HI_S))}
LO_H, HI_H = [-60, 0, -14], [14, 60, 14]
htrees = {'body': cKDTree(part(['body', 'cyan', 'amber'], LO_H, HI_H)), 'cradle_loaded': cKDTree(part(['cl'], LO_H, HI_H)),
          'cradle_empty': cKDTree(part(['ce'], LO_H, HI_H))}
print('samples', {k: t.n for k, t in trees.items()}, {k: t.n for k, t in htrees.items()}, flush=True)
def q(tree, X): return float(min(tree.query(X, k=1, distance_upper_bound=UB, workers=1)[0].min(), UB))
ship = np.array(d['ship']['pts']).reshape(-1, 3)
# hull envelope: per 0.25 m y-bin the max radius of the hull verts, swept as a dense circle (the hull mesh is sparse between rings)
hy = np.arange(0.0, ship[:, 1].max(), 0.25); hr = []
for y in hy:
    m = (ship[:, 1] >= y) & (ship[:, 1] < y + 0.25); hr.append(np.hypot(ship[m, 0], ship[m, 2]).max() if m.any() else np.nan)
hr = np.array(hr); ok = ~np.isnan(hr); hr = np.interp(hy, hy[ok], hr[ok])
ang = np.radians(np.arange(0, 360, 2.0))
HULL = np.vstack([np.c_[r * np.sin(ang), np.full_like(ang, y), r * np.cos(ang)] for y, r in zip(hy, hr) if y >= 6.9])   # above the skirt top (skirt covers below)
HULL_V = ship[ship[:, 1] >= 6.9]   # + real verts (ladder cage, hatch frame, cargo ring boxes)
def classify(bv, P):
    r = np.hypot(P[:, 0], P[:, 2]); cls = np.empty(len(bv), object)
    for i, b in enumerate(bv):
        if b.startswith('Gear_Door'): cls[i] = 'gear_doors'
        elif b.startswith(('Gear_Leg', 'Gear_Knee', 'Gear_Foot')): cls[i] = 'gear_legs'
        elif r[i] < 3.95 and P[i, 1] < 3.0: cls[i] = 'engine_ring_nozzles'
        else: cls[i] = 'skirt_band'
    return cls
def yawm(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
YAWS = [0, 15, 30, 45, 60, 75]    # gear 4-fold + transporter mirror-symmetric -> 0..90 covers it; 60 = pad yaw
YMS = {'feet_on_deck_0.492': 0.492, 'AA_Engine_Ring_Mount_3.45': 3.45}
worst = {}
def rec(key, dist, ctx):
    if key not in worst or dist < worst[key][0]: worst[key] = (float(dist), ctx)
STATIC = ('engine_ring_nozzles', 'skirt_band')     # skinned to Aft_Skirt_Root only: identical in every frame
for N in ('N06', 'N11'):
    D = d[N]; bv = D['bone_of_vertex']; rest = np.array(D['poses']['rest_deployed']).reshape(-1, 3); cls = classify(bv, rest)
    frames = [('rest_deployed', rest), ('retracted', np.array(D['poses']['retracted']).reshape(-1, 3)), ('deploy_end', np.array(D['poses']['deploy_end']).reshape(-1, 3))]
    for cn in ('Gear_Retract', 'Gear_Deploy'):
        for i, f in enumerate(D['sweep'][cn]): frames.append((f'{cn}@{i/10:.1f}s', np.array(f).reshape(-1, 3)))
    groups = {c: np.where(cls == c)[0] for c in ('engine_ring_nozzles', 'skirt_band', 'gear_doors', 'gear_legs')}
    for ymn, ym in YMS.items():
        for yaw in YAWS:
            R = yawm(yaw)
            for fi, (fn, F) in enumerate(frames):        # LOADED: ship on Ship_Seat; every 0.1 s of both gear clips
                W = (F + [0, ym, 0]) @ R.T + [0, 0.45, 0]
                for c, ix in groups.items():
                    if c in STATIC and fi > 0: continue
                    for tn in ('cradle_loaded', 'body'): rec(f'LOADED|{N}|{c}|vs_{tn}', q(trees[tn], W[ix]), dict(Y_M=ymn, yaw=yaw, frame=fn))
            W0 = (rest + [0, ym, 0]) @ R.T                 # EMPTY: ship standing (gear deployed), transporter drives in / out
            for dx in np.arange(-32, 0.01, 2.0):
                W = W0 + [dx, 0, 0]
                for c, ix in groups.items():
                    for tn in ('cradle_empty', 'body'): rec(f'EMPTY_DRIVE_IN|{N}|{c}|vs_{tn}', q(trees[tn], W[ix]), dict(Y_M=ymn, yaw=yaw, ship_dx=float(dx)))
    print(N, 'done', flush=True)
for ymn, ym in YMS.items():
    hull_off = ym - 0.492
    for yaw in YAWS:
        R = yawm(yaw)
        for nm, Hp in (('hull_envelope', HULL), ('hull_verts', HULL_V)):
            W = (Hp + [0, hull_off, 0]) @ R.T
            for tn in ('cradle_loaded', 'body'): rec(f'LOADED|hull|{nm}|vs_{tn}', q(htrees[tn], W + [0, 0.45, 0]), dict(Y_M=ymn, yaw=yaw))
            for dx in np.arange(-32, 0.01, 2.0):
                for tn in ('cradle_empty', 'body'): rec(f'EMPTY_DRIVE_IN|hull|{nm}|vs_{tn}', q(htrees[tn], W + [dx, 0, 0]), dict(Y_M=ymn, yaw=yaw, ship_dx=float(dx)))
table = [dict(check=k, min_clearance_m=round(v[0], 3), at=v[1]) for k, v in sorted(worst.items())]
def mn(pred): xs = [t for t in table if pred(t['check'])]; return min(xs, key=lambda t: t['min_clearance_m'])
summary = dict(
    loaded_skirt_gear_ring_vs_cradle=mn(lambda k: k.startswith('LOADED|N') and 'cradle' in k),
    loaded_skirt_gear_ring_vs_body=mn(lambda k: k.startswith('LOADED|N') and 'body' in k),
    empty_drive_in_skirt_gear_ring=mn(lambda k: k.startswith('EMPTY_DRIVE_IN|N')),
    empty_drive_in_hull=mn(lambda k: k.startswith('EMPTY_DRIVE_IN|hull')),
    loaded_hull_vs_cradle_contact=mn(lambda k: k.startswith('LOADED|hull') and 'cradle' in k),
    loaded_hull_vs_body=mn(lambda k: k.startswith('LOADED|hull') and 'body' in k))
json.dump(dict(sampling_m=H, upper_bound_m=UB, note='4.0 means >= 4 m', frames='rest, retracted, deploy_end + Gear_Retract/Gear_Deploy every 0.1 s (legs, doors); root-skinned skirt/ring static', yaws=YAWS, y_m=YMS, ship_seat_lift=0.45, ship_x_offsets='-32..0 step 2.0 (empty)', summary=summary, table=table,
               inputs=dict(skirt=['art/vfx/engine_flame/aft_skirt/aft_skirt_N06.glb', 'art/vfx/engine_flame/aft_skirt/aft_skirt_N11.glb'],
                           ship='art/3d/ship/ship_lv2/pad_lv2.glb (read-only)')), open(OUT, 'w'), indent=1)
for k, v in summary.items(): print(f'{k:38s} {v["min_clearance_m"]:7.3f}  {v["check"]}  {v["at"]}')
