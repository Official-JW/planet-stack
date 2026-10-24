"""10/24 (Director): the conveyor ore lumps (cyan #07c4ff faces of the Conveyor mesh, 11 hex lumps) become plain grey regolith that matches
the HT-04 ore and the deposit rock: COLOR_0 = Mine SHM_DepositRock linear (13, 12, 11) with one +-8 % shade per lump, no cyan / blue,
no veins. Vertex colour only (no geometry / material / draw change). Works on the UNPACKED GLB.
usage: python3 recolour_conveyor_lumps.py IN_plain.glb OUT_plain.glb"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'props', '_shared_src'))
from glbskin import GLB
g = GLB(sys.argv[1]); j = g.j; repl = {}
n = g.find('Conveyor'); n = n if 'mesh' in j['nodes'][n] else next(c for c in j['nodes'][n]['children'] if 'mesh' in j['nodes'][c])
p = j['meshes'][j['nodes'][n]['mesh']]['primitives'][0]; ci = p['attributes']['COLOR_0']; C = g.acc(ci).copy(); P = g.acc(p['attributes']['POSITION']).astype(float)
cy = (C[:, 2] > 100) & (C[:, 0] < 60)
# one shade per lump: cluster cyan vertices by position (lumps are ~0.4 m, > 1 m apart)
idx = np.where(cy)[0]; W = g.world(n); Q = P[idx] @ W[:3, :3].T + W[:3, 3]; lab = -np.ones(len(idx), int); k = 0
for i in range(len(idx)):
    if lab[i] >= 0: continue
    st = [i]; lab[i] = k
    while st:
        a = st.pop(); nb = np.where((lab < 0) & (np.linalg.norm(Q - Q[a], axis=1) < 0.3))[0]; lab[nb] = k; st += list(nb)
    k += 1
SH = (0.92, 1.0, 1.04, 0.97, 1.09, 1.0)
for L in range(k):
    C[idx[lab == L], :3] = np.clip(np.round(np.array((13, 12, 11)) * SH[L % len(SH)]), 0, 255).astype(np.uint8)
repl[ci] = C; _o = g.acc; g.acc = lambda i: repl[i] if i in repl else _o(i)
g.save(sys.argv[2], {})
print(json.dumps({'lump_verts_recoloured': int(cy.sum()), 'lumps': k, 'cyan_left_in_Conveyor': int(((C[:, 2] > 100) & (C[:, 0] < 60)).sum())}))
