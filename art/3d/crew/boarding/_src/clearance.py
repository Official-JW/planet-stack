# Climber clearance from evaluated (three r186 skinned) vertices: python3 clearance.py POSE_PREFIX [--from T]
# Reports, over the dumped frames: min mesh-to-mesh distance between any two crew members (both visible),
# min boot (Foot_*/Shin_* verts of the upper climber) -> glove (Hand_* verts of the lower climber) distance, and where.
import sys, json, numpy as np
from scipy.spatial import cKDTree
pre = sys.argv[1]; m = json.load(open(pre + '.json')); V = m['nverts']; T = m['times']
P = np.memmap(pre + '_pos.bin', np.float32, 'r', shape=(len(T), 4, V, 3))
vj = np.array(m['vjoint']); boot = np.isin(vj, ['Foot_L', 'Foot_R', 'Shin_L', 'Shin_R']); glove = np.isin(vj, ['Hand_L', 'Hand_R'])
sub = np.arange(V)  # all verts
best = dict(mesh=(9, None), bootglove=(9, None))
per_t = []
for ti, t in enumerate(T):
    vis = [k for k in range(4) if m['visible'][ti][k]]
    X = np.asarray(P[ti]); mt = 9
    for a in vis:
        for b in vis:
            if b <= a: continue
            A, B = X[a], X[b]
            if np.linalg.norm(A.mean(0) - B.mean(0)) > 4.5: continue
            d, _ = cKDTree(B).query(A, k=1, distance_upper_bound=3.0); dm = float(d.min())
            mt = min(mt, dm)
            if dm < best['mesh'][0]: best['mesh'] = (dm, (t, a + 1, b + 1))
            up, lo = (a, b) if A[:, 1].mean() > B[:, 1].mean() else (b, a)
            d2, _ = cKDTree(X[lo][glove]).query(X[up][boot], k=1, distance_upper_bound=3.0); d2 = float(d2.min())
            if d2 < best['bootglove'][0]: best['bootglove'] = (d2, (t, up + 1, lo + 1))
    per_t.append(mt)
out = {'frames': len(T), 't_range': [T[0], T[-1]],
       'min_mesh_gap_m': round(best['mesh'][0], 3), 'min_mesh_gap_at_t_crewA_crewB': best['mesh'][1],
       'min_boot_to_glove_m': round(best['bootglove'][0], 3), 'min_boot_to_glove_at_t_upper_lower': best['bootglove'][1],
       'frames_under_10cm': int(sum(x < 0.10 for x in per_t)), 'frames_touching_under_2cm': int(sum(x < 0.02 for x in per_t))}
print(json.dumps(out))
