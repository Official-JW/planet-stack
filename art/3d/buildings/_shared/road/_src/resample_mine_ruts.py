"""10/24 (Jacob: real tyre-track trails): resample ONLY the visible rut rows on the Mine road straights so the rows along the road are
<= 0.6 m apart, then paint_station_roads.py paints the same dark / light tread it uses on the U-turn. Works on Base_Paint of the
UNPACKED mine_game.glb (gltfpack -noq -kn -ke): every longitudinal edge (|ds| < 0.1 m, |du| > 0.6 m) whose two ends are road vertices on
a straight (out x 5.5-21, return x 12.5-21; x >= 21 is the seam ease and stays untouched) with |offset| 0.95-2.05 m (the rut columns and
their shoulders) is split at its midpoint; every triangle using a split edge is split conformingly (1/2/3 edges -> 2/3/4 tris), so there
are no T-junctions. New vertices = edge midpoints (position, normalised normal, colour), so the surface shape is unchanged. No new
material, primitive or draw; bounds unchanged (midpoints lie inside). Repeats until no edge is longer than 0.6 m.
usage: python3 resample_mine_ruts.py IN_plain.glb OUT_plain.glb  (then paint_station_roads.py mine OUT_plain.glb ...)"""
import sys, os, json, math, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'props', '_shared_src'))
from glbskin import GLB
SRC, OUT = sys.argv[1], sys.argv[2]
LANES = {'out': np.array([(5.5, 9.0), (26.0, 9.0)]), 'ret': np.array([(26.0, 0.0), (12.5, 0.0)])}   # the straights only
XMIN = {'out': 5.5, 'ret': 12.5}; XMAX = 21.0; MAXROW = 0.6
g = GLB(SRC); j = g.j; repl = {}
_o = g.acc; g.acc = lambda i: repl[i] if i in repl else _o(i)
nb = g.find('Base_Paint'); nb = nb if 'mesh' in j['nodes'][nb] else next(c for c in j['nodes'][nb].get('children', []) if 'mesh' in j['nodes'][c])
pr = j['meshes'][j['nodes'][nb]['mesh']]['primitives']; assert len(pr) == 1; pr = pr[0]; Wm = g.world(nb)
A = pr['attributes']; assert set(A) == {'POSITION', 'NORMAL', 'COLOR_0'}, A
P = g.acc(A['POSITION']).astype(np.float64); N = g.acc(A['NORMAL']).astype(np.float64); C = g.acc(A['COLOR_0']).astype(np.float64)
I = g.acc(pr['indices']).ravel().astype(np.int64).reshape(-1, 3)
def l2s(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
tri0 = len(I); added_v = 0
for it in range(4):
    W = P @ Wm[:3, :3].T + Wm[:3, 3]; xz = W[:, [0, 2]]
    S = l2s(C[:, :3] / 255.0)
    grey = (S[:, 2] - S[:, 0] > 0.012) & (S[:, 2] - S[:, 0] < 0.06) & (S[:, 0] > 0.38) & (S[:, 0] < 0.72)
    lane = np.full(len(P), -1); off = np.zeros(len(P)); u = np.zeros(len(P))
    for li, (nm, (a, b)) in enumerate(LANES.items()):
        d = b - a; L = np.linalg.norm(d); t = ((xz - a) @ d) / (L * L); q = a + np.clip(t, 0, 1)[:, None] * d; r = xz - q
        dist = np.linalg.norm(r, axis=1); sg = np.sign(d[0] * r[:, 1] - d[1] * r[:, 0])
        ok = (dist < 2.9) & (W[:, 0] >= XMIN[nm] - 0.05) & (W[:, 0] <= XMAX + 1.0) & (W[:, 1] > -0.1) & (W[:, 1] < 0.35) & grey
        lane[ok] = li; off[ok] = (sg * dist)[ok]; u[ok] = (t * L)[ok]
    E = np.sort(np.concatenate([I[:, [0, 1]], I[:, [1, 2]], I[:, [2, 0]]]), axis=1); E = np.unique(E, axis=0)
    a_, b_ = E[:, 0], E[:, 1]
    mark = ((lane[a_] >= 0) & (lane[a_] == lane[b_]) & (np.abs(off[a_] - off[b_]) < 0.1) & (np.abs(u[a_] - u[b_]) > MAXROW)
            & (np.abs(off[a_]) > 0.95) & (np.abs(off[a_]) < 2.05) & (np.minimum(W[a_, 0], W[b_, 0]) < XMAX))
    if not mark.any(): break
    ME = E[mark]; mid = {}
    nP, nN, nC = [P], [N], [C]; nv = len(P)
    for (x, y) in ME:
        mid[(x, y)] = nv; nv += 1
        nP.append(((P[x] + P[y]) / 2)[None]); n_ = N[x] + N[y]; nN.append((n_ / (np.linalg.norm(n_) + 1e-12))[None]); nC.append(((C[x] + C[y]) / 2)[None])
    P, N, C = np.vstack(nP), np.vstack(nN), np.vstack(nC); added_v += len(ME)
    def m(x, y): return mid.get((min(x, y), max(x, y)))
    out = []
    for t in I:
        a0, a1, a2 = t; e = [m(a0, a1), m(a1, a2), m(a2, a0)]; k = sum(v is not None for v in e)
        if k == 0: out.append(t); continue
        if k == 3:
            m01, m12, m20 = e; out += [(a0, m01, m20), (a1, m12, m01), (a2, m20, m12), (m01, m12, m20)]; continue
        # rotate so the split pattern starts at a fixed corner
        for r_ in range(3):
            v = [t[(r_ + q) % 3] for q in range(3)]; ee = [m(v[0], v[1]), m(v[1], v[2]), m(v[2], v[0])]
            if k == 1 and ee[0] is not None: out += [(v[0], ee[0], v[2]), (ee[0], v[1], v[2])]; break
            if k == 2 and ee[0] is not None and ee[1] is not None:
                # split edges v0v1 and v1v2: corner tri at v1 + quad (v0, m01, m12, v2) split on its shorter diagonal
                m01, m12 = ee[0], ee[1]; out.append((m01, v[1], m12))
                if np.linalg.norm(P[m01] - P[v[2]]) < np.linalg.norm(P[v[0]] - P[m12]): out += [(v[0], m01, v[2]), (m01, m12, v[2])]
                else: out += [(v[0], m01, m12), (v[0], m12, v[2])]
                break
    I = np.array(out, np.int64)
    print('pass', it, 'split edges', len(ME), 'tris', len(I))
# write back (float attributes, mesh in the same node / frame)
repl[A['POSITION']] = P.astype(np.float32); repl[A['NORMAL']] = N.astype(np.float32); repl[A['COLOR_0']] = np.clip(np.round(C), 0, 255).astype(np.uint8)
for k in ('POSITION', 'NORMAL'):
    a = j['accessors'][A[k]]; a['componentType'] = 5126; a.pop('normalized', None)
big = len(P) > 65535; repl[pr['indices']] = I.astype(np.uint32 if big else np.uint16).reshape(-1, 1); j['accessors'][pr['indices']]['componentType'] = 5125 if big else 5123
g.save(OUT, {})
print(json.dumps({'base_paint_tris_before': int(tri0), 'after': int(len(I)), 'added_tris': int(len(I) - tri0), 'added_verts': int(added_v)}))
