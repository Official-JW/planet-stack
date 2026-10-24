# v4 gate category 15: crew vs crew.  Every pair of visible crew members must keep a >= 3 cm MESH gap on every frame of every clip
# (no exemptions).  Exact triangle-triangle distance (6 point-triangle + 9 edge-edge distances, 0 if any edge crosses the other
# triangle) on the skinned mesh as three r186 plays the shipped GLB.
#   NODE_PATH=... node dump_poses.mjs crew_boarding.glb /tmp/all --every 0.0333333 0 58.5      (every 1/30 s frame of all 3 clips)
#   python3 crew_vs_crew.py /tmp/all out.json [MIN_M=0.03 [T0 T1]]   (pairs whose bounding boxes stay > 8 cm apart report the box gap)
import json, sys, numpy as np
pre, outf = sys.argv[1], sys.argv[2]; MIN = float(sys.argv[3]) if len(sys.argv) > 3 else 0.03
m = json.load(open(pre + '.json')); V = m['nverts']; T = np.array(m['times']); NT = m['ntris']
P = np.memmap(pre + '_pos.bin', np.float32, 'r', shape=(len(T), 4, V, 3))
mb = np.fromfile(pre + '_mesh.bin', np.uint8); TRI = np.frombuffer(mb[:NT * 12].tobytes(), np.uint32).reshape(-1, 3).astype(np.int64)
VJ = m.get('vjoint'); JN = m.get('joint_names') or ['Root', 'Hips', 'Spine', 'Chest', 'Neck', 'Head', 'UpperArm_L', 'Forearm_L', 'Hand_L', 'UpperArm_R', 'Forearm_R', 'Hand_R', 'Thigh_L', 'Shin_L', 'Foot_L', 'Thigh_R', 'Shin_R', 'Foot_R']
vis = np.array(m['visible'], bool)
EPS = 1e-12
def dot(a, b): return np.einsum('ij,ij->i', a, b)
def pt_tri(p, a, b, c):   # closest distance point -> triangle (Ericson 5.1.5), vectorised
    ab = b - a; ac = c - a; ap = p - a
    d1 = dot(ab, ap); d2 = dot(ac, ap)
    bp = p - b; d3 = dot(ab, bp); d4 = dot(ac, bp)
    cp = p - c; d5 = dot(ab, cp); d6 = dot(ac, cp)
    vc = d1 * d4 - d3 * d2; vb = d5 * d2 - d1 * d6; va = d3 * d6 - d5 * d4
    den = va + vb + vc; den = np.where(np.abs(den) < EPS, EPS, den)
    v = vb / den; w = vc / den; q = a + ab * v[:, None] + ac * w[:, None]
    m_ = (va <= 0) & (d4 - d3 >= 0) & (d5 - d6 >= 0); ww = (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, EPS, (d4 - d3) + (d5 - d6)); q[m_] = (b + (c - b) * ww[:, None])[m_]
    m_ = (vb <= 0) & (d2 >= 0) & (d6 <= 0); ww = d2 / np.where(d2 - d6 == 0, EPS, d2 - d6); q[m_] = (a + ac * ww[:, None])[m_]
    m_ = (vc <= 0) & (d1 >= 0) & (d3 <= 0); vv = d1 / np.where(d1 - d3 == 0, EPS, d1 - d3); q[m_] = (a + ab * vv[:, None])[m_]
    q[(d6 >= 0) & (d5 <= d6)] = c[(d6 >= 0) & (d5 <= d6)]
    q[(d3 >= 0) & (d4 <= d3)] = b[(d3 >= 0) & (d4 <= d3)]
    q[(d1 <= 0) & (d2 <= 0)] = a[(d1 <= 0) & (d2 <= 0)]
    return np.linalg.norm(p - q, axis=1)
def seg_seg(p1, q1, p2, q2):   # closest distance between segments (Ericson 5.1.9), vectorised
    d1 = q1 - p1; d2 = q2 - p2; r = p1 - p2; a = dot(d1, d1); e = dot(d2, d2); f = dot(d2, r); c = dot(d1, r); b = dot(d1, d2)
    den = a * e - b * b
    s = np.where(den > EPS, np.clip((b * f - c * e) / np.where(den > EPS, den, 1), 0, 1), 0.0)
    t = (b * s + f) / np.where(e > EPS, e, 1)
    s = np.where(t < 0, np.clip(-c / np.where(a > EPS, a, 1), 0, 1), np.where(t > 1, np.clip((b - c) / np.where(a > EPS, a, 1), 0, 1), s)); t = np.clip(t, 0, 1)
    return np.linalg.norm((p1 + d1 * s[:, None]) - (p2 + d2 * t[:, None]), axis=1)
def seg_hits_tri(p, q, a, b, c):   # Moller-Trumbore on the segment p->q
    d = q - p; e1 = b - a; e2 = c - a; h = np.cross(d, e2); det = dot(e1, h); ok = np.abs(det) > 1e-14; inv = 1 / np.where(ok, det, 1)
    s = p - a; u = dot(s, h) * inv; qq = np.cross(s, e1); v = dot(d, qq) * inv; t = dot(e2, qq) * inv
    return ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t >= 0) & (t <= 1)
def tri_tri(A, B):   # A, B: (n,3,3) -> distance per pair
    D = np.full(len(A), np.inf)
    for i in range(3):
        D = np.minimum(D, pt_tri(A[:, i], B[:, 0], B[:, 1], B[:, 2])); D = np.minimum(D, pt_tri(B[:, i], A[:, 0], A[:, 1], A[:, 2]))
    E = [(0, 1), (1, 2), (2, 0)]
    for i, j in E:
        for k, l in E: D = np.minimum(D, seg_seg(A[:, i], A[:, j], B[:, k], B[:, l]))
        D = np.where(seg_hits_tri(A[:, i], A[:, j], B[:, 0], B[:, 1], B[:, 2]) | seg_hits_tri(B[:, i], B[:, j], A[:, 0], A[:, 1], A[:, 2]), 0.0, D)
    return D
def tri_joint(ti):
    if VJ is None: return '?'
    v = TRI[ti]; js = [VJ[int(x)] for x in v]; j = max(set(js), key=js.count); return JN[j] if isinstance(j, int) else str(j)
R = 0.08   # exact distances are computed for every triangle pair whose bounding spheres come within R; farther pairs are >= R apart
from scipy.spatial import cKDTree
F0 = float(sys.argv[4]) if len(sys.argv) > 4 else -1e9; F1 = float(sys.argv[5]) if len(sys.argv) > 5 else 1e9
pairs = {}; worst = None; under = 0; frames_checked = 0; close_frames = 0
for fi in range(len(T)):
    if not (F0 <= T[fi] <= F1): continue
    frames_checked += 1
    for i in range(4):
        if not vis[fi][i]: continue
        for j in range(i + 1, 4):
            if not vis[fi][j]: continue
            key = 'Crew_%d-Crew_%d' % (i + 1, j + 1); pr = pairs.setdefault(key, {'min_m': 9.0, 'frames_under_min': 0})
            A = np.asarray(P[fi, i], float); B = np.asarray(P[fi, j], float)
            lo = np.maximum(A.min(0), B.min(0)); hi = np.minimum(A.max(0), B.max(0))
            if (lo - hi > R).any():
                g = float(np.max(lo - hi))
                if g < pr['min_m']: pr.update(min_m=round(g, 4), at_s=round(float(T[fi]), 3), parts=['bbox', 'bbox'])
                continue
            close_frames += 1
            TA = A[TRI]; TB = B[TRI]
            cA = TA.mean(1); rA = np.linalg.norm(TA - cA[:, None], axis=2).max(1); cB = TB.mean(1); rB = np.linalg.norm(TB - cB[:, None], axis=2).max(1)
            tr = cKDTree(cB); rbm = rB.max(); ia = []; ib = []
            for a_, nb in enumerate(tr.query_ball_point(cA, rA + rbm + R)):
                if not nb: continue
                nb = np.array(nb); ok = np.linalg.norm(cB[nb] - cA[a_], axis=1) <= rA[a_] + rB[nb] + R
                ia.extend([a_] * int(ok.sum())); ib.extend(nb[ok].tolist())
            if not ia:
                continue
            ia = np.array(ia); ib = np.array(ib); D = tri_tri(TA[ia], TB[ib]); k = int(np.argmin(D)); g = float(D[k])
            if g < MIN: pr['frames_under_min'] += 1; under += 1
            if g < pr['min_m']:
                pr.update(min_m=round(g, 4), at_s=round(float(T[fi]), 3), parts=[tri_joint(ia[k]), tri_joint(ib[k])], where_glTF=[round(float(x), 3) for x in TA[ia[k]].mean(0)])
            if worst is None or g < worst[0]: worst = (g, key, float(T[fi]))
if worst is None:
    kk = min(pairs, key=lambda k: pairs[k]['min_m']); worst = (pairs[kk]['min_m'], kk, pairs[kk]['at_s'])
res = {'rule': 'every pair of visible crew, every dumped frame, exact triangle-triangle mesh gap >= %.3f m, no exemptions' % MIN,
       'frames': frames_checked, 't_range': [round(float(T[0]), 3), round(float(T[-1]), 3)], 'dt': round(float(T[1] - T[0]), 5) if len(T) > 1 else None,
       'pair_frames_within_25cm': close_frames, 'frames_under_min': under, 'pairs': pairs,
       'closest': ({'gap_m': round(worst[0], 4), 'pair': worst[1], 'at_s': round(worst[2], 3), 'parts': pairs[worst[1]].get('parts')} if worst else None)}
res['status'] = 'PASS' if under == 0 else 'FAIL'
json.dump(res, open(outf, 'w'), indent=1); print(res['status'], json.dumps(res['closest']), 'pairs', {k: (v['min_m'], v.get('at_s'), v.get('parts'), v['frames_under_min']) for k, v in pairs.items()})
