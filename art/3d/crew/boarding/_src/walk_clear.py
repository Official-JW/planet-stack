# v4.1 hotfix check: lowest skinned-vertex clearance above the Pad_Base top (raw heightfield, terrain_hf.py) and above ground y 0,
# per crew and per walk section (nearest Crew_Path segment of the crew centroid), from a dump_poses.mjs prefix.
#   python3 walk_clear.py POSE_PREFIX /tmp/hf_grid.npz [out.json]
import sys, json, numpy as np
pre, hfp = sys.argv[1], sys.argv[2]; J = json.load(open(pre + '.json')); T = np.array(J['times']); V = J['nverts']
P = np.fromfile(pre + '_pos.bin', np.float32).reshape(len(T), 4, V, 3); vis = np.array(J['visible'])
D = np.load(hfp); H = D['H']; x0, z0, dx = float(D['x0']), float(D['z0']), float(D['dx'])
CP = np.array([(-11.19, 7.94), (-7.85, 8.20), (-2.40, 2.20), (3.20, -3.40), (4.50, -10.40)])
SEC = ['Crew_Path_01-02', 'Crew_Path_02-03', 'Crew_Path_03-04', 'Crew_Path_04-ladder']
def seg_of(p):
    best = (1e9, 0)
    for k in range(4):
        a, b = CP[k], CP[k + 1]; ab = b - a; u = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1); d = np.linalg.norm(p - (a + ab * u))
        if d < best[0]: best = (d, k)
    return best[1]
R = {s: {c: dict(pad=(9.0, None, None), ground=(9.0, None, None), sink_frames=0, n=0) for c in range(4)} for s in SEC}
for ti, t in enumerate(T):
    for c in range(4):
        if not vis[ti][c]: continue
        Q = P[ti, c]; low = Q[:, 1] < 1.0
        if not low.any() or Q[:, 1].min() > 1.5: continue     # on the ladder: not a walk sample
        q = Q[low]; i = np.clip(np.round((q[:, 0] - x0) / dx).astype(int), 0, H.shape[0] - 1); j = np.clip(np.round((q[:, 2] - z0) / dx).astype(int), 0, H.shape[1] - 1)
        cl = q[:, 1] - H[i, j]; k = int(np.argmin(cl)); s = SEC[seg_of(Q[:, [0, 2]].mean(0))]; r = R[s][c]; r['n'] += 1
        if cl[k] < r['pad'][0]: r['pad'] = (float(cl[k]), float(t), [round(float(x), 3) for x in q[k]])
        g = float(q[:, 1].min());
        if g < r['ground'][0]: r['ground'] = (g, float(t), None)
        if cl[k] < -0.005: r['sink_frames'] += 1
out = {s: {'Crew_%d' % (c + 1): dict(min_above_pad_base_m=round(R[s][c]['pad'][0], 4), pad_t_s=R[s][c]['pad'][1], pad_at=R[s][c]['pad'][2],
        min_above_ground_y0_m=round(R[s][c]['ground'][0], 4), ground_t_s=R[s][c]['ground'][1], samples=R[s][c]['n'], frames_sinking_over_5mm=R[s][c]['sink_frames'])
        for c in range(4) if R[s][c]['n']} for s in SEC}
print(json.dumps(out, indent=1))
if len(sys.argv) > 3: json.dump(out, open(sys.argv[3], 'w'), indent=1)
