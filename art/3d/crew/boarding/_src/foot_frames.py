# v4.1 per-frame foot check (Coder's acceptance): lowest vertex of each foot (Foot_L / Foot_R skinned verts) vs the Pad_Base top under it
# (raw heightfield of launch_pad_82131aba.glb, terrain_hf.py), every dumped frame while the crew member is on the ground (foot < 1 m).
# sink = most negative gap (all frames); float = largest gap while the foot is planted (< 0.15 m/s). Board time = crew time + 2.0 s (BD.pre).
#   python3 foot_frames.py POSE_PREFIX /tmp/hf_grid.npz [out.json]
import sys, json, numpy as np
pre, hfp = sys.argv[1], sys.argv[2]; J = json.load(open(pre + '.json')); T = np.array(J['times']); V = J['nverts']; vj = np.array(J['vjoint'])
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
gap = lambda q: q[:, 1] - H[np.clip(np.round((q[:, 0] - x0) / dx).astype(int), 0, H.shape[0] - 1), np.clip(np.round((q[:, 2] - z0) / dx).astype(int), 0, H.shape[1] - 1)]
out = {'crew': {}, 'sections': {s: {} for s in SEC}, 'dt_s': float(T[1] - T[0]), 'crew_t_range': [float(T[0]), float(T[-1])]}
for c in range(4):
    W = dict(sink=(9, None, None), float=(-9, None, None), frames=0); prev = {}
    for ti, t in enumerate(T):
        if not vis[ti][c]: continue
        for s in 'LR':
            q = P[ti, c][vj == 'Foot_' + s]
            if q[:, 1].min() > 1.0: prev.pop(s, None); continue
            g = gap(q); g = g[g < 0.9]   # cells off Pad_Base (z > 9.1, the airlock apron: not in the pad GLB) give gap > 1 m: skipped
            if not len(g): continue
            k = int(np.argmin(g)); m = float(g[k])
            sp = np.linalg.norm(q.mean(0) - prev[s]) / (T[1] - T[0]) if s in prev else 9.0; prev[s] = q.mean(0)
            W['frames'] += 1; sec = SEC[seg_of(P[ti, c][:, [0, 2]].mean(0))]; R = out['sections'][sec].setdefault('Crew_%d' % (c + 1), dict(min_gap_m=9.0, t=None, foot=None, max_planted_float_m=-9.0, ft=None))
            if m < W['sink'][0]: W['sink'] = (m, float(t), s)
            if m < R['min_gap_m']: R.update(min_gap_m=round(m, 4), t=round(float(t) + 2.0, 2), foot='Foot_' + s)
            if sp < 0.15:
                if m > W['float'][0]: W['float'] = (m, float(t), s)
                if m > R['max_planted_float_m']: R.update(max_planted_float_m=round(m, 4), ft=round(float(t) + 2.0, 2))
    out['crew']['Crew_%d' % (c + 1)] = dict(worst_sink_m=round(min(0.0, W['sink'][0]), 4), min_gap_m=round(W['sink'][0], 4), sink_board_t=round(W['sink'][1] + 2.0, 2), sink_foot='Foot_' + W['sink'][2],
        worst_planted_float_m=round(W['float'][0], 4), float_board_t=round(W['float'][1] + 2.0, 2), float_foot='Foot_' + W['float'][2], foot_frames=W['frames'])
print(json.dumps(out, indent=1))
if len(sys.argv) > 3: json.dump(out, open(sys.argv[3], 'w'), indent=1)
