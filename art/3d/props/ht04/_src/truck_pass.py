"""10/24 truck pass on an UNPACKED truck GLB (gltfpack -noq -kn -ke output), applied after detail_pass.py.
  --ore   (HT-04 only; Director 10/24: "the ore must not look like faceted cyan gems - crystals are the paid currency"):
          * bed heap (bone Truck_Load, the 'fill' morph mesh): recoloured to the Mine deposit rock (#3f3d3b = SHM_DepositRock COLOR_0)
            with darker / lighter regolith faces and ~5 % faint muted-cyan vein faces (no bright cyan);
          * ROCKS rounded, irregular matte regolith lumps (smooth-normal noisy icospheres) appended on the heap, skinned 100 % to
            Truck_Load, each vertex carrying the heap's own 'fill' delta at its x/z -> they ride the heap at every fill stage (0..1);
          * chute_pour (Truck_Pour_01..07) and truck_load_rich (Truck_Rich_01..05) chunks: the faceted 20-tri gems are replaced by
            rounded rock lumps of the same bind-pose size and centre on the same bones (the clips scale them up unchanged);
            no veins (10/24 00:50: no cyan / blue at all). Dust puffs (Truck_Dust_*) unchanged.
          * 10/24 00:50 pass 2: heap rebuilt as a 27x11 grid dumped pile (33 deg repose, rounded crown), colour = Mine deposit rock
            exactly, all load vertices clamped inside the bed walls at every fill (checked at 21 fill values).
  --merge-glass (HT-04 + FB-05; Director 10/24, station draw cap): the SHM_Glass primitive is merged into the SHM_Paint primitive as
          dark tinted vertex colour (glass base colour #182030-ish), SHM_Glass is dropped -> 1 draw per truck.
Every node, joint, IBM (re-based, see bake), clip, extras and the morph name stay the same.
usage: python3 truck_pass.py IN_plain.glb OUT_raw.glb [--ore] [--merge-glass]; then gltfpack -i OUT_raw.glb -o X_game.glb -cc -kn -ke"""
import sys, os, json, math, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '_shared_src'))
from glbskin import GLB
SRC, OUT = sys.argv[1], sys.argv[2]; ORE = '--ore' in sys.argv; MERGE = '--merge-glass' in sys.argv
g = GLB(SRC); j = g.j; mesh = j['meshes'][0]; prim = mesh['primitives'][0]; A = prim['attributes']; repl = {}
_o = g.acc; g.acc = lambda i: repl[i] if i in repl else _o(i)
def lin(h):
    h = h.lstrip('#'); c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def u8(c): return np.clip(np.round(np.r_[c, 1.0] * 255), 0, 255).astype(np.uint8)
# ---- bake the dequantisation transform of the mesh node into vertices + IBMs (as detail_pass.py), work in that space
mn = next(i for i, N in enumerate(j['nodes']) if N.get('mesh') == 0); T = g.node_local(mn); Ti = np.linalg.inv(T); sc = np.cbrt(np.linalg.det(T[:3, :3]))
for p in mesh['primitives']:
    ai = p['attributes']['POSITION']; repl[ai] = (g.acc(ai).astype(np.float64) @ T[:3, :3].T + T[:3, 3]).astype(np.float32)
    for t in p.get('targets', []):
        repl[t['POSITION']] = (g.acc(t['POSITION']) * sc).astype(np.float32)
        if 'NORMAL' in t: repl[t['NORMAL']] = g.acc(t['NORMAL']).astype(np.float32)
for p in mesh['primitives']:          # float everything we may extend
    for k in ('POSITION', 'NORMAL'):
        a = j['accessors'][p['attributes'][k]]; a['componentType'] = 5126; a.pop('normalized', None)
    for t in p.get('targets', []):
        for k, ai in t.items(): j['accessors'][ai]['componentType'] = 5126; j['accessors'][ai].pop('normalized', None)
skin = j['skins'][0]; ib = skin['inverseBindMatrices']; IB = g.acc(ib).reshape(-1, 4, 4).transpose(0, 2, 1)
repl[ib] = np.stack([(M @ Ti).T.reshape(16) for M in IB]).astype(np.float32)
for k in ('translation', 'rotation', 'scale', 'matrix'): j['nodes'][mn].pop(k, None)
names = [g.name(n) for n in skin['joints']]
def cur(p):
    a = p['attributes']; r = {k: g.acc(a[k]) for k in a}
    r['I'] = g.acc(p['indices']).ravel().astype(np.int64); r['T'] = [{k: g.acc(ai) for k, ai in t.items()} for t in p.get('targets', [])]; return r
def put(p, r):
    a = p['attributes']
    for k in a: repl[a[k]] = r[k]
    I = r['I']; big = I.max() > 65535; repl[p['indices']] = I.astype(np.uint32 if big else np.uint16).reshape(-1, 1)
    j['accessors'][p['indices']]['componentType'] = 5125 if big else 5123
    for t, tr in zip(p.get('targets', []), r['T']):
        for k, ai in t.items(): repl[ai] = tr[k].astype(np.float32)
R = cur(prim); stats = {}
def append(r, P, N, Cl, Jt, I, D=None):
    n0 = len(r['POSITION']); n = len(P)
    r['POSITION'] = np.vstack([r['POSITION'], P]).astype(np.float32); r['NORMAL'] = np.vstack([r['NORMAL'], N]).astype(np.float32)
    if 'COLOR_0' in r: r['COLOR_0'] = np.vstack([r['COLOR_0'], Cl]).astype(np.uint8)
    J8 = np.zeros((n, 4), r['JOINTS_0'].dtype); J8[:, 0] = Jt; W8 = np.zeros((n, 4), r['WEIGHTS_0'].dtype); W8[:, 0] = np.iinfo(W8.dtype).max if W8.dtype != np.float32 else 1.0
    r['JOINTS_0'] = np.vstack([r['JOINTS_0'], J8]); r['WEIGHTS_0'] = np.vstack([r['WEIGHTS_0'], W8])
    for tr in r['T']:
        for k in tr: tr[k] = np.vstack([tr[k], D if (D is not None and k == 'POSITION') else np.zeros((n, 3), np.float32)])
    r['I'] = np.concatenate([r['I'], I + n0])
# ---------------------------------------------------------------- ore
ICO = None
def icosphere():
    t = (1 + 5 ** 0.5) / 2
    V = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    V = [np.array(v, float) / np.linalg.norm(v) for v in V]; mid = {}
    def m(a, b):
        k = (min(a, b), max(a, b))
        if k not in mid: q = V[a] + V[b]; V.append(q / np.linalg.norm(q)); mid[k] = len(V) - 1
        return mid[k]
    F2 = []
    for a, b, c in F: ab, bc, ca = m(a, b), m(b, c), m(c, a); F2 += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
    return np.array(V), np.array(F2)
def rock(rng, centre, size, cut=None):
    """rounded irregular lump: noisy icosphere (42 v / 80 f), smooth normals; size = half extents (x, y, z) in mesh space"""
    V, F = icosphere(); ph = rng.uniform(0, 6.3, 6)
    k = 1 + 0.16 * np.sin(2.1 * V[:, 0] + ph[0]) * np.cos(1.7 * V[:, 1] + ph[1]) + 0.12 * np.sin(3.3 * V[:, 2] + ph[2]) + 0.07 * np.sin(5.1 * V[:, 1] + 2.3 * V[:, 0] + ph[3])
    U = V * k[:, None]
    th = rng.uniform(0, 6.3); c, s = math.cos(th), math.sin(th); Ry = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    U = U @ Ry.T * np.array(size) + centre
    if cut is not None:                # drop faces fully below the local plane y < cut (buried in the heap)
        F = F[~(U[F][:, :, 1] < cut).all(1)]
    N = np.zeros_like(U)
    for a, b, cc in F:
        n = np.cross(U[b] - U[a], U[cc] - U[a]); N[[a, b, cc]] += n
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    if np.dot(np.cross(U[F[0][1]] - U[F[0][0]], U[F[0][2]] - U[F[0][0]]), U[F[0][0]] - centre) < 0: F = F[:, ::-1]
    used = np.unique(F); remap = -np.ones(len(U), int); remap[used] = np.arange(len(used))
    return U[used], N[used], V[used], remap[F]
# 10/24 00:50 Director pass 2: (1) colour = the Mine deposit rock exactly (SHM_DepositRock: white base x COLOR_0 linear u8 (13, 12, 11),
# measured from mine_game.glb Deposit_01/02), small +-8 % shade steps only, NO cyan / blue anywhere (veins removed);
# (2) every heap + lump vertex clamped inside the bed walls at every fill (x/z fixed, the morph only moves y -> basis inside = all fills inside);
# (3) 'fill' reshaped into a dumped pile: slopes down to the walls at ~33 deg (angle of repose) with a rounded (soft-min) crown.
DEP = np.array((13, 12, 11)) / 255.0                       # linear, = Mine SHM_DepositRock COLOR_0
SHADES = (0.92, 0.97, 1.0, 1.0, 1.04, 1.09)
BED = dict(x0=-3.24, x1=0.04, z=1.21, floor=1.93, edge=3.20)   # inner bed box (walls x -3.30 / 0.10, z +-1.28, rim y 3.30-3.38, floor 1.90)
REPOSE = math.tan(math.radians(33.0)); SOFT = 0.22
def u8l(c): return np.clip(np.round(np.c_[c, np.ones(len(c))] * 255), 0, 255).astype(np.uint8)
def dwall(x, z):                                           # soft-min distance to the 4 inner walls -> rounded crown / corners
    d = np.stack([x - BED['x0'], BED['x1'] - x, BED['z'] - z, BED['z'] + z])
    return -SOFT * np.log(np.exp(-np.clip(d, 0, None) / SOFT).sum(0)) + SOFT * math.log(4) * 0   # (offset kept 0: edge = BED edge)
def h_full(x, z): return BED['edge'] + REPOSE * np.clip(dwall(x, z), 0, None)
def clampxz(Q, m=0.0):
    Q = Q.copy(); Q[:, 0] = np.clip(Q[:, 0], BED['x0'] + m, BED['x1'] - m); Q[:, 2] = np.clip(Q[:, 2], -BED['z'] + m, BED['z'] - m); return Q
if ORE:
    rng = np.random.default_rng(424)
    P, Jj = R['POSITION'], R['JOINTS_0'][:, 0]; D = R['T'][0]['POSITION']; I3 = R['I'].reshape(-1, 3)
    kl = names.index('Truck_Load'); hv = Jj == kl
    # old heap: basis heights (top grid) are kept as the fill-0 mound; its triangles are dropped and the heap is rebuilt as a grid
    HP = P[hv].astype(np.float64); top = HP[:, 1] > HP[:, 1].min() + 0.03
    key = np.round(HP[top][:, [0, 2]], 3); _, ui = np.unique(key, axis=0, return_index=True); TP = HP[top][ui]
    def h_basis(xz):
        d = np.linalg.norm(TP[None, :, [0, 2]] - xz[:, None, :], axis=2); nn = np.argsort(d, 1)[:, :4]; w = 1 / (np.take_along_axis(d, nn, 1) + 1e-4) ** 2
        w /= w.sum(1, keepdims=True); y = (TP[nn][:, :, 1] * w).sum(1)
        return np.minimum(np.maximum(y, BED['floor']), h_full(xz[:, 0], xz[:, 1]))
    old = hv[I3].all(1); R['I'] = I3[~old].ravel(); stats['old_heap_tris_dropped'] = int(old.sum())
    NX, NZ = 27, 11
    gx, gz = np.meshgrid(np.linspace(BED['x0'], BED['x1'], NX), np.linspace(-BED['z'], BED['z'], NZ), indexing='ij')
    gx, gz = gx.ravel(), gz.ravel(); xz = np.c_[gx, gz]
    y0 = h_basis(xz); y1 = h_full(gx, gz)
    edge = (np.isclose(gx, BED['x0']) | np.isclose(gx, BED['x1']) | np.isclose(np.abs(gz), BED['z']))
    y0[edge] = BED['floor']                                  # fill 0: the rim of the mound sits on the floor
    rr = np.random.default_rng(7); jit = rr.normal(0, 0.035, len(gx)) * (~edge)   # a little lumpy surface, not on the wall seam
    y0 = y0 + jit * 0.5; y1 = y1 + jit
    V0 = np.c_[gx, y0, gz]; V1 = np.c_[gx, y1, gz]
    F = []
    for i in range(NX - 1):
        for k in range(NZ - 1):
            a_, b_, c_, d_ = i * NZ + k, (i + 1) * NZ + k, (i + 1) * NZ + k + 1, i * NZ + k + 1
            F += [(a_, c_, b_), (a_, d_, c_)] if (i + k) % 2 else [(a_, d_, b_), (b_, d_, c_)]
    F = np.array(F)
    if np.cross(V1[F[0, 1]] - V1[F[0, 0]], V1[F[0, 2]] - V1[F[0, 0]])[1] < 0: F = F[:, ::-1]
    def vnorm(V):
        N = np.zeros_like(V)
        for t in F: N[t] += np.cross(V[t[1]] - V[t[0]], V[t[2]] - V[t[0]])
        return N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-12)
    N0, N1 = vnorm(V0), vnorm(V1)
    # flat-ish per-face shading steps on the deposit grey: unshare vertices per face so each face keeps one shade
    Vf0, Vf1 = V0[F].reshape(-1, 3), V1[F].reshape(-1, 3); Nf0, Nf1 = N0[F].reshape(-1, 3), N1[F].reshape(-1, 3)
    sh = np.array([SHADES[(t * 7919 + (t // 3) * 31) % len(SHADES)] for t in range(len(F))]).repeat(3)
    Cf = u8l(DEP[None, :] * sh[:, None])
    n0 = len(R['POSITION'])
    append(R, Vf0, Nf0, Cf, np.full(len(Vf0), kl), np.arange(len(Vf0)), (Vf1 - Vf0).astype(np.float32))
    R['T'][0]['NORMAL'][n0:] = (Nf1 - Nf0).astype(np.float32)
    stats['heap_grid_tris'] = int(len(F)); stats['heap_full_crown_y'] = round(float(y1.max()), 3); stats['heap_edge_y_full'] = BED['edge']
    def hd(Q):  # per-vertex fill delta at x/z
        return h_full(Q[:, 0], Q[:, 2]) - h_basis(Q[:, [0, 2]])
    # rocks: inside the walls with margin, rounded matte lumps riding the morph (per-vertex delta -> seated at every fill)
    pts = []; tries = 0
    while len(pts) < 26 and tries < 20000:
        tries += 1; r_ = rng.uniform(0.15, 0.26); m = r_ * 1.45 + 0.03
        q = np.array((rng.uniform(BED['x0'] + m, BED['x1'] - m), rng.uniform(-BED['z'] + m, BED['z'] - m)))
        if all(np.linalg.norm(q - p_[0]) > (r_ + p_[1]) * 0.95 for p_ in pts): pts.append((q, r_))
    nrock = 0; rt = 0
    for q, r_ in pts:
        yb = h_basis(q[None])[0]; ctr = np.array((q[0], yb - 0.2 * r_, q[1])); sz = (r_ * rng.uniform(0.9, 1.15), r_ * 0.7, r_ * rng.uniform(0.85, 1.1))
        U, N, Vu, Fr = rock(rng, ctr, sz, cut=yb - 0.3 * r_)
        U = clampxz(U); U[:, 1] = np.maximum(U[:, 1], BED['floor'])
        dd = np.zeros_like(U); dd[:, 1] = hd(U)
        cl = u8l(np.tile(DEP * SHADES[rng.integers(0, len(SHADES))], (len(U), 1)) * rng.uniform(0.95, 1.05, (len(U), 1)))
        append(R, U, N, cl, np.full(len(U), kl), Fr.ravel(), dd.astype(np.float32)); nrock += 1; rt += len(Fr)
    stats['heap_rocks'] = nrock; stats['heap_rock_tris'] = rt
    # chute / rich chunks: rounded grey rocks (same bind centre / size), no veins
    I3 = R['I'].reshape(-1, 3); Jj = R['JOINTS_0'][:, 0]; drop = np.zeros(len(I3), bool); ct = 0
    for nm in names:
        if not nm.startswith(('Truck_Pour', 'Truck_Rich')): continue
        k = names.index(nm); sel = Jj == k; tri = sel[I3].all(1); Q = R['POSITION'][np.unique(I3[tri])].astype(np.float64)
        ctr = (Q.min(0) + Q.max(0)) / 2; ext = (Q.max(0) - Q.min(0)) / 2 * np.array((0.95, 1.05, 1.0))
        drop |= tri
        U, N, Vu, Fr = rock(rng, ctr, ext)
        cl = u8l(np.tile(DEP * SHADES[rng.integers(0, len(SHADES))], (len(U), 1)) * rng.uniform(0.95, 1.05, (len(U), 1)))
        append(R, U, N, cl, np.full(len(U), k), Fr.ravel()); ct += len(Fr)
        I3 = R['I'].reshape(-1, 3); drop = np.r_[drop, np.zeros(len(I3) - len(drop), bool)]; Jj = R['JOINTS_0'][:, 0]
    R['I'] = R['I'].reshape(-1, 3)[~drop].ravel(); stats['chunk_tris_removed'] = int(drop.sum()); stats['chunk_tris_added'] = ct
    # verify: every Truck_Load vertex referenced by a triangle stays inside the bed box at fill 0..1 (21 samples)
    I3 = R['I'].reshape(-1, 3); Jj = R['JOINTS_0'][:, 0]; vs = np.unique(I3[(Jj == kl)[I3].all(1)])
    P0 = R['POSITION'][vs].astype(np.float64); DD = R['T'][0]['POSITION'][vs].astype(np.float64); bad = 0
    for f in np.linspace(0, 1, 21):
        Q = P0 + f * DD
        bad += int(((Q[:, 0] < BED['x0'] - 1e-4) | (Q[:, 0] > BED['x1'] + 1e-4) | (np.abs(Q[:, 2]) > BED['z'] + 1e-4) | (Q[:, 1] < BED['floor'] - 0.035)).sum())
    stats['clamp_check_violations_21_fills'] = bad; stats['load_verts_checked'] = int(len(vs))
    Cc = R['COLOR_0'][vs][:, :3].astype(int); stats['load_blue_excess_max'] = int((Cc[:, 2] - Cc[:, 0]).max())
# ---------------------------------------------------------------- glass -> paint
if MERGE and len(mesh['primitives']) > 1:
    gp = mesh['primitives'][1]; gm = j['materials'][gp['material']]
    assert gm['name'] == 'SHM_Glass', gm['name']
    G = cur(gp); gc = np.array(gm['pbrMetallicRoughness']['baseColorFactor'][:3]) * 1.25   # slightly lifted: paint roughness 0.42 reflects less than glass 0.1
    append(R, G['POSITION'], G['NORMAL'], np.tile(u8(gc), (len(G['POSITION']), 1)), G['JOINTS_0'][:, 0], G['I'],
           G['T'][0]['POSITION'] if G['T'] else None)
    stats['glass_tris_merged'] = len(G['I']) // 3
    mesh['primitives'] = [prim]; gi = gp['material']
    j['materials'].pop(gi)
    for p in [q for m in j['meshes'] for q in m['primitives']]:
        if p.get('material', -1) > gi: p['material'] -= 1
for k in ('POSITION', 'NORMAL', 'COLOR_0', 'JOINTS_0', 'WEIGHTS_0'):
    a = j['accessors'][A[k]]
    if k in ('POSITION',) and 'min' not in a: a['min'] = [0, 0, 0]; a['max'] = [0, 0, 0]
for t in prim.get('targets', []):
    a = j['accessors'][t['POSITION']]
    if 'min' not in a: a['min'] = [0, 0, 0]; a['max'] = [0, 0, 0]
put(prim, R)
# drop accessors no longer referenced (merged glass prim) by keeping them but emptying is not allowed -> rebuild accessor list
used = set()
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ('attributes',) or (isinstance(v, dict) and k not in ('extras',)): walk(v)
    return o
for m in j['meshes']:
    for p in m['primitives']:
        used |= set(p['attributes'].values()); used.add(p['indices'])
        for t in p.get('targets', []): used |= set(t.values())
for s in j['skins']: used.add(s['inverseBindMatrices'])
for a in j.get('animations', []):
    for s in a['samplers']: used |= {s['input'], s['output']}
order = sorted(used); newi = {o: n for n, o in enumerate(order)}
olda = j['accessors']; data = {o: g.acc(o) for o in order}
j['accessors'] = [olda[o] for o in order]; repl.clear(); repl.update({newi[o]: data[o] for o in order})
for m in j['meshes']:
    for p in m['primitives']:
        p['attributes'] = {k: newi[v] for k, v in p['attributes'].items()}; p['indices'] = newi[p['indices']]
        if 'targets' in p: p['targets'] = [{k: newi[v] for k, v in t.items()} for t in p['targets']]
for s in j['skins']: s['inverseBindMatrices'] = newi[s['inverseBindMatrices']]
for a in j.get('animations', []):
    for s in a['samplers']: s['input'] = newi[s['input']]; s['output'] = newi[s['output']]
g.acc = lambda i: repl[i]
for i, a in enumerate(j['accessors']): a['bufferView'] = 0
if not j['nodes'][mn].get('name'):     # mesh + skin back on the named parent (gltfpack rebuilds the original layout)
    par = next(k for k, M in enumerate(j['nodes']) if mn in M.get('children', []))
    j['nodes'][par]['mesh'] = j['nodes'][mn].pop('mesh'); j['nodes'][par]['skin'] = j['nodes'][mn].pop('skin')
g.save(OUT, {})
stats.update({'tris': int(sum(len(repl[newi[o]]) if False else 0 for o in [])), 'prims': len(mesh['primitives']), 'materials': [m['name'] for m in j['materials']]})
stats['tris'] = int(sum(j['accessors'][p['indices']]['count'] for p in mesh['primitives']) // 3)
print(json.dumps(stats))
