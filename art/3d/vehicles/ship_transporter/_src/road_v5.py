#!/usr/bin/env python3
"""ST-10A transport road v5 (10/24 Coder order, staged tag d729465: Cargo Space Dock 480 | Launch Pad 640 | Shipyard 800, 160 m spacing).
Centreline (world glTF m, +X right, +Z toward the camera): pad pick-up = pad Ship_Center (640, -13) heading +X, straight out of the pad's RIGHT
side on the FAR side (z -13), ONE right-hand arc (R 100 m, 40 deg, no S-bend), straight into the Shipyard Road_Entry (754.871, 0.23, 17.604).
Swept-volume check on real triangles (sampled 0.5 m) of the GLBs qa3d-next loads (export_tris_v5.mjs): ST-10A body (track/girder bands
|w| >= 9.5 up to 9.5 m + towers, cross girder u >= 11 above 4.0 m, gate u <= -11.5 above 4.0 m, cradle arms) + the loaded ship (aft skirt /
landing gear r <= 6.6 m for y 0.6-8.0, hull r <= 5.7 m up to 44.6 m). Other roads: Refinery<->pad flatbed lanes z 23 / 32 (+-2.8 m toes) and
their pad U-turn (r 4.5, toe 2.8, east to x 648.3), the Mine<->Refinery haul road (x 186-274); Cargo Space Dock at 480.
  python3 road_v5.py <v5 dir with tris_*.bin> <out.json>      (light: numpy/scipy, ~1 min, single core)"""
import json, math, sys
import numpy as np
D, OUT = sys.argv[1].rstrip('/') + '/', sys.argv[2]
M = json.load(open(D + 'tris_meta.json'))
E = np.array([754.871, 17.604]); E_Y = 0.23; P0 = np.array([640.0, -13.0])
THETA, R = math.radians(40.0), 100.0
HALF_C, X0, X1 = 13.56, -13.36, 15.64                      # ST-10A footprint about the ship axis
MARGIN, SHOULDER = 3.75, 2.6; HALF_RUN = HALF_C + MARGIN; HALF_GR = HALF_RUN + SHOULDER   # 17.31 / 19.91
L = (E[1] - P0[1] - R * (1 - math.cos(THETA))) / math.sin(THETA); XA = E[0] - R * math.sin(THETA) - L * math.cos(THETA)
def centerline(step=0.25):
    P, H = [], []
    for x in np.arange(P0[0], XA, step): P.append((x, P0[1])); H.append(0.0)
    na = int(math.ceil(R * THETA / step))
    for i in range(na + 1): a = THETA * i / na; P.append((XA + R * math.sin(a), P0[1] + R * (1 - math.cos(a)))); H.append(a)
    A1 = np.array(P[-1]); n = int(math.ceil(L / step))
    for i in range(1, n + 1): P.append(tuple(A1 + L * i / n * np.array([math.cos(THETA), math.sin(THETA)]))); H.append(THETA)
    P = np.array(P); S = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; return P, np.array(H), S
CP, CH, CS = centerline()
def pts(n, h=0.5, ymin=0.32):
    T = np.fromfile(D + f'tris_{n}.bin', np.float32).reshape(-1, 3, 3).astype(float); N = np.fromfile(D + f'trin_{n}.bin', np.uint16)
    keep = T[:, :, 1].max(1) > ymin; T, N = T[keep], N[keep]; out, nm = [], []
    for t, k in zip(T, N):
        a, b, c = t; na = max(1, int(math.ceil(np.linalg.norm(b - a) / h))); nc = max(1, int(math.ceil(np.linalg.norm(c - a) / h)))
        u, v = np.meshgrid(np.linspace(0, 1, na + 1), np.linspace(0, 1, nc + 1)); m = u + v <= 1 + 1e-9
        Q = a + u[m][:, None] * (b - a) + v[m][:, None] * (c - a); Q = Q[Q[:, 1] > ymin]; out.append(Q); nm.append(np.full(len(Q), k))
    Q = np.vstack(out); K = np.concatenate(nm); Q = np.round(Q * 4) / 4; Q, ix = np.unique(Q, axis=0, return_index=True); return Q, K[ix]
def rel(c, psi, Q):
    d = Q[:, [0, 2]] - c; ca, sa = math.cos(psi), math.sin(psi); return d[:, 0] * ca + d[:, 1] * sa, -d[:, 0] * sa + d[:, 1] * ca
def vol_hit(u, w, y):
    aw = np.abs(w); inb = (u >= X0) & (u <= X1) & (aw <= HALF_C)
    crawler = inb & (((aw >= 9.5) & ((y <= 9.5) | (np.abs(u) <= 3.6))) | ((u >= 11.0) & (y > 4.0)) | ((u <= -11.5) & (y > 4.0)) |
                     ((np.abs(u) <= 1.2) & (y >= 13.5) & (y <= 33.5) & (aw >= 4.0)))
    r = np.hypot(u, w); ship = ((y >= 0.6) & (y <= 8.0) & (r <= 6.6)) | ((y > 8.0) & (y <= 44.6) & (r <= 5.7))
    return crawler, ship
def foot_gap(u, w):          # horizontal distance outside the 29.0 x 27.12 footprint (negative inside)
    du = np.maximum(np.maximum(X0 - u, u - X1), 0); dw = np.maximum(np.abs(w) - HALF_C, 0); g = np.hypot(du, dw)
    ins = (du == 0) & (dw == 0); g[ins] = -np.minimum(np.minimum(u - X0, X1 - u), HALF_C - np.abs(w))[ins]; return g
out = dict(version='v5', order='d729465: Cargo Space Dock 480 | Launch Pad 640 | Shipyard 800 (GAP 160)', inputs={k: dict(file=v['file'], md5=v['md5'], x0=v['x0']) for k, v in M.items()},
           centerline=dict(start_pickup=P0.tolist(), heading_start_deg=0, straight_to_x=round(XA, 2), arc=dict(radius_m=R, angle_deg=40.0, dir='right (+X turning toward +Z)',
           center=[round(XA, 2), round(P0[1] + R, 2)], start=[round(XA, 2), P0[1]], end=[round(XA + R * math.sin(THETA), 2), round(P0[1] + R * (1 - math.cos(THETA)), 2)]),
           final_straight_m=round(L, 2), end_road_entry=[E[0], E_Y, E[1]], heading_end_deg=40.0, turns=1, s_bends=0, length_m=round(float(CS[-1]), 2)))
# ---- obstacles per station along every pose (0.25 m)
POSE = range(0, len(CP), 2)
res = {}
for n in ('LaunchPad', 'CargoDock', 'Shipyard'):
    Q, K = pts(n); names = M[n]['names']
    if n == 'LaunchPad':
        skip = np.array([names[k] in ('Ship_Placeholder', 'Cargo_Door') for k in K]); Q, K = Q[~skip], K[~skip]
    near = (Q[:, 0] > CP[:, 0].min() - 40) & (Q[:, 0] < CP[:, 0].max() + 40) & (Q[:, 2] > CP[:, 1].min() - 40) & (Q[:, 2] < CP[:, 1].max() + 40)
    Qn, Kn = Q[near], K[near]; first_hit = None
    if len(Qn) == 0:
        res[n] = dict(pts=0, hits=[], first_hit_s=None, min_footprint_gap_m=None, gap_west_of_crawler_rear_at_pickup_m=round(float(P0[0] + X0 - Q[:, 0].max()), 2), mesh_x_max=round(float(Q[:, 0].max()), 2), note='no mesh within 40 m of the path bbox'); print(n, res[n], flush=True); continue
    hits = {}; mingap = 1e9; mingap_at = None
    for i in POSE:
        u, w = rel(CP[i], CH[i], Qn); y = Qn[:, 1]; c, s = vol_hit(u, w, y)
        for msk, kind in ((c, 'crawler'), (s, 'ship skirt/gear/hull')):
            for j in np.where(msk)[0]:
                key = (names[Kn[j]], kind); h = hits.setdefault(key, dict(node=names[Kn[j]], hit_by=kind, x=[1e9, -1e9], z=[1e9, -1e9], ymax=0, first_s=round(float(CS[i]), 2)))
                h['x'] = [min(h['x'][0], Qn[j, 0]), max(h['x'][1], Qn[j, 0])]; h['z'] = [min(h['z'][0], Qn[j, 2]), max(h['z'][1], Qn[j, 2])]; h['ymax'] = max(h['ymax'], Qn[j, 1])
        if (c.any() or s.any()) and first_hit is None: first_hit = i
        g = foot_gap(u, w).min()
        if g < mingap: mingap, mingap_at = g, i
    res[n] = dict(pts=int(len(Qn)), hits=[dict(h, x=[round(h['x'][0], 2), round(h['x'][1], 2)], z=[round(h['z'][0], 2), round(h['z'][1], 2)], ymax=round(h['ymax'], 2)) for h in hits.values()],
                  first_hit_s=None if first_hit is None else round(float(CS[first_hit]), 2), min_footprint_gap_m=round(float(mingap), 2), min_gap_at_s=round(float(CS[mingap_at]), 2))
    print(n, 'pts', len(Qn), 'hits', len(hits), 'first_hit_s', res[n]['first_hit_s'], 'min footprint gap', round(float(mingap), 2), '@s', res[n]['min_gap_at_s'], flush=True)
    for h in res[n]['hits']: print('   ', h, flush=True)
    if n == 'Shipyard': SYQ = Qn
out['obstacles'] = res
# ---- crawler stop pose at the Shipyard: last pose with >= 2 m footprint gap to the Shipyard (prism, every height > 0.32 m)
stop = None
for i in range(len(CP)):
    u, w = rel(CP[i], CH[i], SYQ)
    if foot_gap(u, w).min() < 2.0: break
    stop = i
u, w = rel(CP[stop], CH[stop], SYQ); g = float(foot_gap(u, w).min())
lead = CP[stop] + X1 * np.array([math.cos(CH[stop]), math.sin(CH[stop])])
out['crawler_stop'] = dict(rule='last pose with >= 2.0 m horizontal gap from the ST-10A footprint (29.0 x 27.12 m) to any Shipyard mesh above 0.32 m',
    ship_axis=[round(float(CP[stop][0]), 2), round(float(CP[stop][1]), 2)], heading_deg=round(math.degrees(CH[stop]), 1), s_m=round(float(CS[stop]), 2),
    gap_m=round(g, 2), leading_face_centre=[round(float(lead[0]), 2), round(float(lead[1]), 2)], short_of_road_entry_m=round(float(CS[-1] - CS[stop] - X1), 2))
print('stop', out['crawler_stop'], flush=True)
# ---- road surface (mesh) = graded band +-19.91 m from the pad's right edge (x 669.5, outside berm toe 669.4) to Road_Entry
PAD_EDGE_X = 669.5
i0 = int(np.argmax(CP[:, 0] >= PAD_EDGE_X)); RS = slice(i0, len(CP))
NRM = np.stack([-np.sin(CH), np.cos(CH)], 1)
def band(h): return CP[RS] - h * NRM[RS], CP[RS] + h * NRM[RS]       # (far / -Z edge, camera / +Z edge)
far_g, cam_g = band(HALF_GR); far_r, cam_r = band(HALF_RUN)
def seg_d(Pt, A):            # min distance from point(s) Pt to polyline A
    a, b = A[:-1], A[1:]; ab = b - a; t = np.clip(((Pt[:, None, :] - a[None]) * ab[None]).sum(-1) / (ab * ab).sum(-1)[None], 0, 1)
    return np.linalg.norm(Pt[:, None, :] - (a[None] + t[..., None] * ab[None]), axis=-1).min(1)
poly = np.vstack([far_g, cam_g[::-1]])
class _PIP:
    def __init__(s, V): s.V = V
    def contains_points(s, Q):
        V = s.V; x, z = Q[:, 0][:, None], Q[:, 1][:, None]; a, b = V[None, :, :], np.roll(V, -1, 0)[None, :, :]
        c = ((a[..., 1] > z) != (b[..., 1] > z)) & (x < (b[..., 0] - a[..., 0]) * (z - a[..., 1]) / (b[..., 1] - a[..., 1] + 1e-12) + a[..., 0])
        return (c.sum(1) % 2) == 1
MPth = _PIP(poly)
road = dict(mesh_start_s=round(float(CS[i0]), 2), mesh_start_center=CP[i0].round(2).tolist(), mesh_end_center=E.tolist(), mesh_length_m=round(float(CS[-1] - CS[i0]), 2),
            running_width_m=round(2 * HALF_RUN, 2), graded_width_m=round(2 * HALF_GR, 2), crawler_lanes_w=[9.7, 13.3])
# z range used near x 640 (pad, crawler path) and at the mesh start
road['z_near_x640'] = dict(crawler_footprint=[round(P0[1] - HALF_C, 2), round(P0[1] + HALF_C, 2)], ship_skirt_gear=[round(P0[1] - 6.6, 2), round(P0[1] + 6.6, 2)],
                           planned_running=[round(P0[1] - HALF_RUN, 2), round(P0[1] + HALF_RUN, 2)], planned_graded=[round(P0[1] - HALF_GR, 2), round(P0[1] + HALF_GR, 2)],
                           max_z_any_road_or_crawler_x600_700=round(float(max(cam_g[:, 1][(cam_g[:, 0] <= 700)].max(), P0[1] + HALF_GR)), 2))
# other roads
lanes = []
for zc, nm in ((23.0, 'flatbed OUT z 23'), (32.0, 'flatbed BACK z 32')):
    # lane strip x 296..641 (roadN, to the pad U-turn), toe +-2.8
    xs = np.linspace(296, 641, 1381); A = np.stack([xs, np.full_like(xs, zc)], 1)
    d = min(seg_d(cam_g, A).min(), seg_d(far_g, A).min()) - 2.8
    lanes.append(dict(road=nm, toe_z=[zc - 2.8, zc + 2.8], min_gap_graded_edge_m=round(float(d), 2), crosses=bool(MPth.contains_points(A).any())))
ang = np.linspace(-math.pi / 2, math.pi / 2, 181); U = np.stack([641 + 4.5 * np.cos(ang), 27.5 + 4.5 * np.sin(ang)], 1)
du = min(seg_d(cam_g, U).min(), seg_d(far_g, U).min()) - 2.8
lanes.append(dict(road='flatbed pad U-turn (centre 641, 27.5, r 4.5, toe 2.8 -> x <= 648.3, z 20.2-34.8)', min_gap_graded_edge_m=round(float(du), 2), crosses=bool(MPth.contains_points(U).any())))
# crawler on the pad vs the U-turn (pad portion of the path, footprint far edge z <= 0.56)
lanes.append(dict(road='flatbed U-turn vs crawler footprint on pad (z <= %.2f)' % (P0[1] + HALF_C), min_gap_m=round(20.2 - (P0[1] + HALF_C), 2)))
lanes.append(dict(road='Mine<->Refinery haul road (x 186-274)', min_gap_graded_edge_m=round(float(poly[:, 0].min() - 274 - 4.0), 2), crosses=False))
road['other_roads'] = lanes
dk = out['inputs'].get('CargoDock'); road['cargo_dock'] = dict(bbox_x=[461.85, 519.51], gap_to_road_mesh_m=round(float(poly[:, 0].min() - 519.51), 2),
    gap_to_crawler_on_pad_m=round(float(P0[0] + X0 - 519.51), 2), dock_road_entry=[480, 17.2], note='Dock is west of the pad; the road leaves east - never passes the Dock')
# Shipyard props inside the graded band (> 0.32 m)
inside = MPth.contains_points(SYQ[:, [0, 2]]) if len(SYQ) else np.zeros(0, bool)
road['shipyard_props_in_graded_band'] = dict(count_pts=int(inside.sum()), x=[round(float(SYQ[inside, 0].min()), 2), round(float(SYQ[inside, 0].max()), 2)] if inside.any() else None,
    z=[round(float(SYQ[inside, 2].min()), 2), round(float(SYQ[inside, 2].max()), 2)] if inside.any() else None, ymax=round(float(SYQ[inside, 1].max()), 2) if inside.any() else None)
out['road'] = road
print(json.dumps(road, indent=1), flush=True)
np.save(OUT.replace('.json', '_cl.npy'), np.c_[CP, CH, CS])
json.dump(dict(out, _cp=CP[::8].round(2).tolist()), open(OUT, 'w'), indent=1)
