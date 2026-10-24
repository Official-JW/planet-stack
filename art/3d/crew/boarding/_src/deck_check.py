# Hatch-landing clearance from evaluated (three r186 skinned) vertices, pad-local u/t/z (same transform as AA2's landing_clear.mjs:
# u along the 330 deg ladder axis from Ship_Center, t sideways, z = glTF y).
#   python3 deck_check.py POSE_PREFIX PADTRIS.json [out.json]
# 1) AA2 landing solids (ported 1:1 from aa2_ref/landing_clear.mjs: wings, bridge, well kerb/frame, beams, braces, rails+posts, lid+hinge/ribs/struts)
# 2) hull r 4.0 (wall at sqrt(16-t^2)-0.03) outside the hatch opening |t| < 0.652, + the opening jambs
# 3) real WIP-pad triangles z 18-25 (ladder stiles/rungs, cage) sampled at 1 cm; gloves vs ladder are grips and are excluded
# 4) foot plants: a foot is PLANTED when it moves < 0.15 m/s with its sole < 3 cm above a surface; every plant at deck height must be on a wing
#    (|t| >= 0.68 outside the kerb, inside the deck) and never in the well (u 4.05-5.15, |t| < 0.62); reports each plant's sole box.
import sys, json, math, numpy as np
from scipy.spatial import cKDTree
pre, padf = sys.argv[1], sys.argv[2]; m = json.load(open(pre + '.json')); V = m['nverts']; T = np.array(m['times'])
P = np.memmap(pre + '_pos.bin', np.float32, 'r', shape=(len(T), 4, V, 3)); vj = np.array(m['vjoint']); dt = float(T[1] - T[0])
C = np.array([0, 0, -13.0]); LU = np.array([0.8660254, 0, 0.5]); LT = np.array([0.5, 0, -0.8660254])
TOP = 21.85; R = 4.0; hu = lambda t: math.sqrt(R * R - t * t) - 0.03
boxes = [('deck_wing', 'hull', 5.45, 0.62, 1.40, 21.75, TOP, 1), ('deck_bridge', 5.15, 5.45, -0.62, 0.62, 21.75, TOP, 0),
         ('frame_side', 'hull', 5.21, 0.62, 0.68, 21.66, 21.88, 1), ('frame_outer', 5.15, 5.21, -0.62, 0.62, 21.66, 21.88, 0),
         ('beam_outer', 5.38, 5.45, -1.40, 1.40, 21.61, 21.75, 0), ('beam_side', 'hull', 5.38, 1.33, 1.40, 21.61, 21.75, 1)]
OPEN = math.radians(100); HU = 5.21 + 0.035; HZ = 21.88 + 0.02; LL = 1.16; d = (math.cos(math.pi - OPEN), math.sin(math.pi - OPEN)); n = (d[1], -d[0])
at = lambda s, k=0: (HU + d[0] * s + n[0] * k, HZ + d[1] * s + n[1] * k)
caps = []
for sg in (-1, 1):
    caps.append(('brace', (5.41, sg * 1.36, 21.63), (hu(1.0) + 0.02, sg * 1.0, 20.50), 0.03))
    A, B, Cc = (4.15, sg * 1.34), (5.40, sg * 1.34), (5.40, sg * 0.76)
    for p in (A, ((A[0] + B[0]) / 2, A[1]), B, Cc): caps.append(('rail_post', (p[0], p[1], TOP), (p[0], p[1], TOP + 1.05), 0.028))
    for h, r in ((1.05, 0.032), (0.525, 0.024)):
        caps.append(('rail', (A[0], A[1], TOP + h), (B[0], B[1], TOP + h), r)); caps.append(('rail', (B[0], B[1], TOP + h), (Cc[0], Cc[1], TOP + h), r))
caps.append(('lid_hinge', (HU, -0.62, HZ), (HU, 0.62, HZ), 0.035))
for t in (-0.3, 0.3): a, b = at(0.08, 0.035), at(LL - 0.08, 0.035); caps.append(('lid_rib', (a[0], t, a[1]), (b[0], t, b[1]), 0.022))
for t in (-0.52, 0.52): b = at(0.62, 0.03); caps.append(('lid_strut', (5.40, t, TOP + 0.01), (b[0], t, b[1]), 0.018))
def sdbox(q, h):
    o = np.abs(q) - h; return np.linalg.norm(np.maximum(o, 0), axis=1) + np.minimum(o.max(1), 0)
def sdf(Q):
    u, t, z = Q[:, 0], Q[:, 1], Q[:, 2]; out = {}
    for nm, u0_, u1, t0, t1, z0, z1, sym in boxes:
        tt = np.abs(t) if sym else t
        u0 = np.sqrt(R * R - np.clip(tt, t0, t1) ** 2) - 0.03 if u0_ == 'hull' else np.full_like(u, u0_)
        s = sdbox(np.stack([u - (u0 + u1) / 2, tt - (t0 + t1) / 2, z - (z0 + z1) / 2], 1), np.stack([(u1 - u0) / 2, np.full_like(u, (t1 - t0) / 2), np.full_like(u, (z1 - z0) / 2)], 1))
        out[nm] = np.minimum(out.get(nm, 9), s)
    c = at(LL / 2); du = u - c[0]; dz = z - c[1]
    out['lid'] = sdbox(np.stack([du * d[0] + dz * d[1], t, du * n[0] + dz * n[1]], 1), np.array([LL / 2, 0.65, 0.025]))
    for nm, a, b, r in caps:
        a = np.array(a); b = np.array(b); ab = b - a; h = np.clip(((Q - a) @ ab) / (ab @ ab), 0, 1)
        out[nm] = np.minimum(out.get(nm, 9), np.linalg.norm(Q - (a + h[:, None] * ab), axis=1) - r)
    # hull wall (outside the hatch opening) and the opening jambs (|t| = 0.652 between u 3.80 and the hatch face 4.06), z 21.0-23.75
    rr = np.hypot(u, t); hz = (z > 21.0) & (z < 23.75)
    hull = np.where(hz & (np.abs(t) > 0.652), rr - (R - 0.03), 9.0)
    jam = np.where(hz & (u > 3.80) & (u < 4.06) & (np.abs(t) <= 0.652), 0.652 - np.abs(t), 9.0)
    out['hull'] = hull; out['hatch_jamb'] = jam
    return out
# real pad triangles (z 18-25 region): sample
D = json.load(open(padf)); pts = []; lab = []
for nm, tri in D['tris']:
    A, B, Cc = [np.array(x) for x in tri]; L = max(np.linalg.norm(B - A), np.linalg.norm(Cc - A), np.linalg.norm(Cc - B)); k = max(2, int(L / 0.01) + 1)
    for i in range(k + 1):
        for j in range(k + 1 - i):
            p = A + (B - A) * i / k + (Cc - A) * j / k; pts.append(p)
pts = np.array(pts); u_, t_, z_ = pts.T
ladder = (u_ > 4.40) & (u_ < 4.50) & (np.abs(t_) < 0.33) & (z_ < 21.86)
cage = (u_ > 4.6) & (u_ < 5.25) & (np.abs(t_) < 0.47) & (z_ < 21.86) & ~ladder
KL = cKDTree(pts[ladder]); KC = cKDTree(pts[cage])
WELL = (4.05, 5.15, 0.62); STAND = (4.3, 4.7, 0.75, 1.25)
res = dict(frames=len(T), dt=round(dt, 4), pad=padf, per_crew={}, per_part={})
import os
for k in [int(x) - 1 for x in os.environ.get('CREWS', '1,2,3,4').split(',')]:
    r = dict(min_m=9.0, at_s=None, part=None, climb_min_frame_side_m=9.0, hits=0, ladder_nonhand_min_m=9.0, ladder_at=None, ladder_part=None,
             cage_min_m=9.0, cage_at=None, cage_part=None, plants=[], plants_in_well=0, plants_on_kerb=0, sole_min_above_deck_m=9.0)
    cur = {'Foot_L': None, 'Foot_R': None}; prevQ = None
    for ti, t in enumerate(T):
        if not m['visible'][ti][k]: prevQ = None; continue
        X = np.asarray(P[ti, k], float) - C; Q = np.stack([X @ LU, X @ LT, X[:, 1]], 1)
        if Q[:, 2].max() > 19.8:
            sel = (Q[:, 0] > 3.4) & (Q[:, 0] < 6.2) & (np.abs(Q[:, 1]) < 2.2) & (Q[:, 2] > 19.8) & (Q[:, 2] < 24.5)
            if sel.any():
                o = sdf(Q[sel]); isfoot = np.isin(vj[sel], ['Foot_L', 'Foot_R'])
                for nm, s in o.items():
                    if nm in ('deck_wing', 'deck_bridge'):   # boot soles standing on the deck top are contact by design: count only non-sole intrusion
                        s = np.where(isfoot & (Q[sel][:, 2] > TOP - 0.03), 9.0, s)
                        if isfoot.any(): r['sole_min_above_deck_m'] = round(min(r['sole_min_above_deck_m'], float((Q[sel][isfoot, 2] - TOP)[o[nm][isfoot] < 0.05].min()) if (o[nm][isfoot] < 0.05).any() else 9.0), 3)
                    j = s.argmin(); sv = float(s[j])
                    pp = res['per_part'].setdefault(nm, dict(min_m=9.0, hits=0)); pp['min_m'] = round(min(pp['min_m'], sv), 3)
                    if sv < 0:
                        pp['hits'] += 1; r['hits'] += 1; hl = r.setdefault('hit_log', {}).setdefault(nm, [])
                        if not hl or t - hl[-1][1] > 0.2: hl.append([round(float(t), 2), round(float(t), 2), str(vj[sel][j]), round(sv, 3), [round(float(v), 3) for v in Q[sel][j]]])
                        else: hl[-1][1] = round(float(t), 2); hl[-1][3] = min(hl[-1][3], round(sv, 3))
                    if sv < r['min_m']: r['min_m'] = round(sv, 3); r['at_s'] = round(float(t), 2); r['part'] = nm + ':' + str(vj[sel][j])
                    if nm == 'frame_side' and Q[:, 2].min() < 21.0: r['climb_min_frame_side_m'] = round(min(r['climb_min_frame_side_m'], sv), 3)
            sel = (Q[:, 2] > 18) & (Q[:, 2] < 22.0) & (Q[:, 0] > 4.2) & (Q[:, 0] < 5.4) & (np.abs(Q[:, 1]) < 0.7)
            nh = sel & ~np.isin(vj, ['Hand_L', 'Hand_R'])
            if nh.any():
                dd, _ = KL.query(Q[nh]); j = dd.argmin()
                if dd[j] < r['ladder_nonhand_min_m']: r['ladder_nonhand_min_m'] = round(float(dd[j]), 3); r['ladder_at'] = round(float(t), 2); r['ladder_part'] = str(vj[nh][j])
            if sel.any():
                dd, _ = KC.query(Q[sel]); j = dd.argmin()
                if dd[j] < r['cage_min_m']: r['cage_min_m'] = round(float(dd[j]), 3); r['cage_at'] = round(float(t), 2); r['cage_part'] = str(vj[sel][j])
        # planted feet at deck height
        for fj in ('Foot_L', 'Foot_R'):
            fm = vj == fj; F = Q[fm]; sp = 9 if prevQ is None else np.linalg.norm(F.mean(0) - prevQ[fm].mean(0)) / dt
            sole = F[F[:, 2] < F[:, 2].min() + 0.02]
            on = sp < 0.15 and abs(F[:, 2].min() - TOP) < 0.03
            if on and cur[fj] is None:
                cur[fj] = dict(foot=fj, land_s=round(float(t), 2), u=[round(float(sole[:, 0].min()), 3), round(float(sole[:, 0].max()), 3)],
                               t=[round(float(sole[:, 1].min()), 3), round(float(sole[:, 1].max()), 3)], z=round(float(F[:, 2].min()), 3))
                tmin = float(np.abs(sole[:, 1]).min()); inw = ((sole[:, 0] > WELL[0]) & (sole[:, 0] < WELL[1]) & (np.abs(sole[:, 1]) < WELL[2])).any()
                kerb = ((np.abs(sole[:, 1]) >= 0.62) & (np.abs(sole[:, 1]) <= 0.68) & (sole[:, 0] > 3.9) & (sole[:, 0] < 5.21)).any()
                inside = bool((np.hypot(sole[:, 0], sole[:, 1]) < R - 0.03).all() and (np.abs(sole[:, 1]) < 0.652).all())
                in_stand = bool(((sole[:, 0] >= STAND[0]) & (sole[:, 0] <= STAND[1]) & (np.abs(sole[:, 1]) >= STAND[2]) & (np.abs(sole[:, 1]) <= STAND[3])).all())
                cur[fj].update(where='inside_hatch' if inside else ('WELL' if inw else 'KERB' if kerb else 'wing_stand_area' if in_stand else 'wing'),
                               min_abs_t=round(tmin, 3))
                r['plants'].append(cur[fj]); r['plants_in_well'] += int(inw); r['plants_on_kerb'] += int(kerb)
            elif not on: cur[fj] = None
        prevQ = Q
    res['per_crew']['Crew_%d' % (k + 1)] = r
res['min_m'] = min(v['min_m'] for v in res['per_crew'].values()); res['hits'] = sum(v['hits'] for v in res['per_crew'].values())
if len(sys.argv) > 3: json.dump(res, open(sys.argv[3], 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'per_crew'}))
for k, v in res['per_crew'].items():
    print(k, {a: b for a, b in v.items() if a != 'plants'})
    for p in v['plants']: print('   ', p)
