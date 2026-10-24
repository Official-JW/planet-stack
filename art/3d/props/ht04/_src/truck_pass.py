"""10/24 truck pass on an UNPACKED truck GLB (gltfpack -noq -kn -ke output), applied after detail_pass.py.
  --ore   (HT-04 only; Director 10/24: "the ore must not look like faceted cyan gems - crystals are the paid currency"):
          * bed heap (bone Truck_Load, the 'fill' morph mesh): recoloured to the Mine deposit rock (#3f3d3b = SHM_DepositRock COLOR_0)
            with darker / lighter regolith faces and ~5 % faint muted-cyan vein faces (no bright cyan);
          * ROCKS rounded, irregular matte regolith lumps (smooth-normal noisy icospheres) appended on the heap, skinned 100 % to
            Truck_Load, each vertex carrying the heap's own 'fill' delta at its x/z -> they ride the heap at every fill stage (0..1);
          * chute_pour (Truck_Pour_01..07) and truck_load_rich (Truck_Rich_01..05) chunks: the faceted 20-tri gems are replaced by
            rounded rock lumps of the same bind-pose size and centre on the same bones (the clips scale them up unchanged);
            He-3 / rich chunks get faint cyan veins only. Dust puffs (Truck_Dust_*) unchanged.
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
ROCK = [lin('#3f3d3b'), lin('#47443f'), lin('#373531'), lin('#504c46')]
VEIN = lin('#2f5a63'); VEIN_RICH = lin('#3a6f79')
def rock_cols(rng, Vu, base, veins, vein_col):
    C = np.tile(base, (len(Vu), 1)) * rng.uniform(0.9, 1.08, (len(Vu), 1))
    for _ in range(veins):
        n = rng.normal(size=3); n /= np.linalg.norm(n); d = Vu @ n - rng.uniform(-0.3, 0.3)
        w = np.clip(1 - np.abs(d) / 0.22, 0, 1)[:, None] * 0.85; C = C * (1 - w) + vein_col * w
    return np.stack([u8(c) for c in C])
if ORE:
    rng = np.random.default_rng(424)
    P, C, Jj = R['POSITION'], R['COLOR_0'], R['JOINTS_0'][:, 0]; D = R['T'][0]['POSITION']; I3 = R['I'].reshape(-1, 3)
    kl = names.index('Truck_Load'); hv = Jj == kl
    # heap recolour per face
    ht = np.where(hv[I3].all(1))[0]; C = C.copy()
    pal = [(ROCK[0], 0.42), (ROCK[1], 0.24), (ROCK[2], 0.17), (ROCK[3], 0.12), (VEIN, 0.05)]
    cum = np.cumsum([w for _, w in pal])
    for t in ht:
        h = ((t * 7919) % 1000) / 1000.0; c = pal[int(np.searchsorted(cum, h))][0] * (0.94 + 0.12 * ((t * 104729) % 97) / 97)
        C[I3[t]] = u8(c)
    R['COLOR_0'] = C
    # heap surface sampler (top grid only: skip the skirt = lowest verts)
    HP, HD = P[hv].astype(np.float64), D[hv].astype(np.float64); top = HP[:, 1] > HP[:, 1].min() + 0.03
    # unique top verts
    key = np.round(HP[top][:, [0, 2]], 3); _, ui = np.unique(key, axis=0, return_index=True); TP, TD = HP[top][ui], HD[top][ui]
    def sample(xz):
        d = np.linalg.norm(TP[None, :, [0, 2]] - xz[:, None, :], axis=2); nn = np.argsort(d, 1)[:, :4]; w = 1 / (np.take_along_axis(d, nn, 1) + 1e-4) ** 2
        w /= w.sum(1, keepdims=True); return (TP[nn][:, :, 1] * w).sum(1), (TD[nn] * w[:, :, None]).sum(1)
    cx, cz = (HP[:, 0].min() + HP[:, 0].max()) / 2, (HP[:, 2].min() + HP[:, 2].max()) / 2; ax, az = (HP[:, 0].max() - HP[:, 0].min()) / 2, (HP[:, 2].max() - HP[:, 2].min()) / 2
    pts = []
    while len(pts) < 26:
        u, v = rng.uniform(-1, 1, 2)
        if u * u + v * v > 0.78 ** 2: continue
        q = np.array((cx + u * ax, cz + v * az)); r_ = rng.uniform(0.15, 0.27)
        if all(np.linalg.norm(q - p_[0]) > (r_ + p_[1]) * 0.95 for p_ in pts): pts.append((q, r_))
    nrock = 0; rt = 0
    for q, r_ in pts:
        y0, _ = sample(q[None]); ctr = np.array((q[0], y0[0] - 0.12 * r_, q[1])); sz = (r_ * rng.uniform(0.9, 1.15), r_ * 0.72, r_ * rng.uniform(0.85, 1.1))
        U, N, Vu, F = rock(rng, ctr, sz, cut=y0[0] - 0.25 * r_)
        _, dd = sample(U[:, [0, 2]])
        base = ROCK[rng.integers(0, 4)]; cl = rock_cols(rng, Vu, base, 1 if rng.random() < 0.3 else 0, VEIN)
        append(R, U, N, cl, np.full(len(U), kl), F.ravel(), dd.astype(np.float32)); nrock += 1; rt += len(F)
    stats['heap_rocks'] = nrock; stats['heap_rock_tris'] = rt; stats['heap_faces_recoloured'] = int(len(ht))
    # chute / rich chunks: replace the gems
    I3 = R['I'].reshape(-1, 3); Jj = R['JOINTS_0'][:, 0]; drop = np.zeros(len(I3), bool); ct = 0
    for nm in names:
        if not nm.startswith(('Truck_Pour', 'Truck_Rich')): continue
        k = names.index(nm); sel = Jj == k; tri = sel[I3].all(1); Q = R['POSITION'][np.unique(I3[tri])].astype(np.float64)
        ctr = (Q.min(0) + Q.max(0)) / 2; ext = (Q.max(0) - Q.min(0)) / 2 * np.array((0.95, 1.05, 1.0))
        drop |= tri
        he = nm.startswith('Truck_Rich') or int(nm[-2:]) % 2 == 0
        U, N, Vu, F = rock(rng, ctr, ext)
        base = (lin('#4a4743') if not he else ROCK[0]) if nm.startswith('Truck_Pour') else ROCK[rng.integers(0, 2)]
        cl = rock_cols(rng, Vu, base, (2 if nm.startswith('Truck_Rich') else 1) if he else 0, VEIN_RICH if nm.startswith('Truck_Rich') else VEIN)
        R['I'] = R['I'][:]  # keep
        append(R, U, N, cl, np.full(len(U), k), F.ravel()); ct += len(F)
        I3 = R['I'].reshape(-1, 3); drop = np.r_[drop, np.zeros(len(I3) - len(drop), bool)]; Jj = R['JOINTS_0'][:, 0]
    R['I'] = R['I'].reshape(-1, 3)[~drop].ravel(); stats['chunk_tris_removed'] = int(drop.sum()); stats['chunk_tris_added'] = ct
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
