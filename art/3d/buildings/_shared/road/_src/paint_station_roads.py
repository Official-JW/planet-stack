"""10/24 (Director): repaint the station roads (Mine stub + return U-turn, Refinery RD-1) inside the PACKED station GLBs in the look of
haul_road_seg.glb v2, vertex colour ONLY: no new vertices / triangles / images / draws, positions untouched (mesh node transforms are
baked like refinery/_src/patch_marker_posts.py so the repack does not stack a quantisation node; nothing is re-simplified).
Road vertices = Base_Paint vertices within 2.9 m of a lane centre line, y -0.1..0.35, in the grey road palette. Per vertex (from its
signed offset s to the nearest lane centre and its distance u along it): dark compacted wheel ruts on the rut columns, tyre-scuffed rut
shoulders, compacted crown polish, loose dust on the shoulders, dusty foot / berm crest / toe, low-frequency along-road variation, and a
dark / light tread alternation on the rut columns wherever the rows are <= 0.6 m apart (it aliases on coarser rows, so it is skipped there).
The edits fade out before each station's seam ease, so the joins to the 8 m strip keep exactly their current colours.
usage: python3 paint_station_roads.py mine|refinery IN_plain.glb OUT_raw.glb [--skin-merge NODE,NODE..]   (then gltfpack -cc -kn -ke)"""
import sys, os, json, math, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'props', '_shared_src'))
from glbskin import GLB
ST, SRC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
def arc(c, r, a0, a1, n, zsign=-1):   # Blender-angle arc -> glTF (x, z): z = cz - r sin a  (glTF z = -Blender y)
    return [(c[0] + r * math.cos(a), c[1] + zsign * r * math.sin(a)) for a in np.linspace(math.radians(a0), math.radians(a1), n)]
if ST == 'mine':     # mine_layout.py: OUT (5.5, z 9) -> (26, z 9); RET (26, z 0) -> (12.5, z 0) -> U-turn R 4.5 about (12.5, z 4.5) -> (12.5, z 9)
    LANES = {'out': [(5.5, 9.0), (26.0, 9.0)], 'ret': [(26.0, 0.0), (12.5, 0.0)] + arc((12.5, 4.5), 4.5, 90, 270, 72)}
    HALF = [0.0, 1.05, 1.25, 1.65, 1.85, 2.0, 2.35, 2.8]; RUT = (1.25, 1.65); FADE = lambda x: np.clip((21.0 - x) / 3.0, 0, 1)
else:                # build_refinery.py RD-1: IN (-46, z 9) -> (-3.5, z 9) -> U-turn R 4.5 about (-3.5, z 4.5) -> (-3.5, z 0); OUT (-46, z 0) -> (3.55, z 0)
    LANES = {'in': [(-46.0, 9.0), (-3.5, 9.0)] + arc((-3.5, 4.5), 4.5, -90, 90, 72), 'out': [(-46.0, 0.0), (3.55, 0.0)]}
    HALF = [0.0, 1.2, 1.5, 1.5, 1.8, 2.0, 2.35, 2.8]; RUT = (1.5, 1.5); FADE = lambda x: np.clip((x + 34.0) / 4.0, 0, 1)
HEX = {'track': '#a4a7ac', 'wear': '#76797e', 'rut_dark': '#5f6267', 'rut_lite': '#8e9196', 'dust': '#b7b8b9', 'crown': '#979a9f', 'polish': '#adb0b5'}
def srgbv(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
K = {k: srgbv(v) for k, v in HEX.items()}
def l2s(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
def s2l(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def project(pts, poly):
    """nearest point on polyline: (dist, signed offset (left of heading = +), arc length u)"""
    poly = np.array(poly); best = np.full(len(pts), np.inf); s_ = np.zeros(len(pts)); u_ = np.zeros(len(pts)); acc = 0.0
    for a, b in zip(poly[:-1], poly[1:]):
        d = b - a; L = np.linalg.norm(d)
        if L < 1e-9: continue
        t = np.clip(((pts - a) @ d) / (L * L), 0, 1); q = a + t[:, None] * d; r = pts - q
        dist = np.linalg.norm(r, axis=1); sg = np.sign(d[0] * r[:, 1] - d[1] * r[:, 0]); m = dist < best
        best[m] = dist[m]; s_[m] = (sg * dist)[m]; u_[m] = acc + t[m] * L; acc += L
    return best, s_, u_
def pn(u, s):  # smooth along-road noise -1..1
    return 0.5 * np.sin(u * 0.73 + s) * np.cos(u * 0.31 + 1.7 * s) + 0.3 * np.sin(u * 1.9 + 2.1 * s) + 0.2 * np.sin(u * 0.17 + s)
g = GLB(SRC); j = g.j; repl = {}
_o = g.acc; g.acc = lambda i: repl[i] if i in repl else _o(i)
par = {c: i for i, N in enumerate(j['nodes']) for c in N.get('children', [])}
def mesh_node(name):
    p = g.find(name)
    return p if 'mesh' in j['nodes'][p] else next(c for c in j['nodes'][p].get('children', []) if 'mesh' in j['nodes'][c])
nb = mesh_node('Base_Paint'); pr = j['meshes'][j['nodes'][nb]['mesh']]['primitives'][0]; Wm = g.world(nb)
P = g.acc(pr['attributes']['POSITION']).astype(np.float64) @ Wm[:3, :3].T + Wm[:3, 3]; C = g.acc(pr['attributes']['COLOR_0']); assert C.dtype == np.uint8
S = l2s(C[:, :3] / 255.0)
xz = P[:, [0, 2]]; best = np.full(len(P), np.inf); off = np.zeros(len(P)); u = np.zeros(len(P)); lane = np.zeros(len(P), int)
for li, (nm, poly) in enumerate(LANES.items()):
    d, s_, u_ = project(xz, poly); m = d < best; best[m] = d[m]; off[m] = s_[m]; u[m] = u_[m]; lane[m] = li
grey = (S[:, 2] - S[:, 0] > 0.012) & (S[:, 2] - S[:, 0] < 0.06) & (S[:, 0] > 0.38) & (S[:, 0] < 0.72)
road = (best < 2.9) & (P[:, 1] > -0.1) & (P[:, 1] < 0.35) & grey
a = np.abs(off); fade = FADE(P[:, 0]) * road
# row spacing per vertex: distance along the road to the nearest other road vertex on the same column (|s| within 3 cm)
rows = np.zeros(len(P)) + 9
idx = np.where(road)[0]
for i in idx:
    m = road & (lane == lane[i]) & (np.abs(off - off[i]) < 0.03); m[i] = False
    du = np.abs(u[m] - u[i]); du = du[du > 0.03]
    if len(du): rows[i] = du.min()
n = pn(u, lane * 3.1 + np.sign(off) * 0.7)
def lerp(c, t, w): return c * (1 - w[:, None]) + t * w[:, None]
new = S.copy(); r0, r1 = RUT
rut = (a > r0 - 0.08) & (a < r1 + 0.08)
sho = ((a > HALF[1] - 0.06) & (a < r0 - 0.08)) | ((a > r1 + 0.08) & (a < HALF[4] + 0.06))
crown = a < 0.08
loose = (a > 0.08) & (a < HALF[1] - 0.06)
foot = (a > HALF[4] + 0.06) & (a < 2.15); crest = (a >= 2.15) & (a < 2.6); toe = a >= 2.6
# tread: dark / light alternation by row parity along the rut, only where the rows are dense enough to carry it
par_ = (np.round(u / np.maximum(rows, 0.05)).astype(int) % 2 == 0)
dense = rows <= 0.6
rutc = np.where((dense & par_)[:, None], K['rut_dark'], np.where(dense[:, None], K['rut_lite'], (K['rut_dark'] + K['rut_lite']) / 2))
new = np.where(rut[:, None], lerp(S, rutc, np.where(dense, 0.75, 0.55) + 0.12 * n), new)
new = np.where(sho[:, None], lerp(S, K['wear'], 0.28 + 0.12 * n), new)
new = np.where(crown[:, None], lerp(S, K['crown'], 0.35 + 0.2 * n), new)
new = np.where(loose[:, None], lerp(S, K['dust'], 0.12 + 0.1 * n), new)
new = np.where(foot[:, None], lerp(S, K['dust'], 0.40 + 0.25 * n), new)
new = np.where(crest[:, None], lerp(S, K['dust'], 0.55 + 0.25 * n), new)
new = np.where(toe[:, None], lerp(S, K['dust'], 0.22 + 0.15 * n), new)
out = lerp(S, new, fade)
C2 = C.copy(); C2[:, :3] = np.clip(np.round(s2l(np.clip(out, 0, 1)) * 255), 0, 255).astype(np.uint8)
changed = int((np.abs(C2.astype(int) - C.astype(int)).max(1) > 0).sum())
repl[pr['attributes']['COLOR_0']] = C2
stats = {'station': ST, 'road_verts': int(road.sum()), 'changed_verts': changed, 'dense_rut_verts': int((road & rut & dense).sum()),
         'coarse_rut_verts': int((road & rut & ~dense).sum()), 'row_spacing_m_on_ruts': np.percentile(rows[road & rut], [0, 25, 50, 75, 100]).round(2).tolist()}
np.save(OUT + '.sel.npy', np.c_[P[:, [0, 2]], road, rows, a])
# ---- optional: merge rigid moving SHM_Paint parts into Base_Paint as ONE skinned mesh whose joints are the existing named nodes
#      (clips keep targeting the same nodes; Base_Paint itself is joint 0) -> -1 draw per merged part
SK = next((sys.argv[i + 1] for i, x in enumerate(sys.argv) if x == '--skin-merge'), None)
def bake_all():
    for i, N in enumerate(j['nodes']):
        if 'mesh' not in N or N.get('skin') is not None: continue
        Ti = g.node_local(i)
        if np.allclose(Ti, np.eye(4)): continue
        for p in j['meshes'][N['mesh']]['primitives']:
            ai = p['attributes']['POSITION']; repl[ai] = (g.acc(ai).astype(np.float64) @ Ti[:3, :3].T + Ti[:3, 3]).astype(np.float32)
            j['accessors'][ai]['componentType'] = 5126; j['accessors'][ai].pop('normalized', None)
            na = p['attributes'].get('NORMAL')
            if na is not None:
                Nn = g.acc(na).astype(np.float64)
                if j['accessors'][na].get('normalized'): Nn = Nn / {5120: 127, 5122: 32767}.get(j['accessors'][na]['componentType'], 1)
                repl[na] = Nn.astype(np.float32); j['accessors'][na]['componentType'] = 5126; j['accessors'][na].pop('normalized', None)
        for k in ('translation', 'rotation', 'scale', 'matrix'): N.pop(k, None)
bake_all()
if SK:
    parts = SK.split(','); base_named = g.find('Base_Paint'); joints = [base_named] + [g.find(p) for p in parts]
    bm = nb; bp = pr; B = {k: g.acc(v) for k, v in bp['attributes'].items()}; I = g.acc(bp['indices']).ravel().astype(np.int64)
    Pb = B['POSITION'].astype(np.float64); Nb = B['NORMAL'].astype(np.float64)
    # Base_Paint mesh positions are now in its mesh node's frame (transform baked) = Base_Paint's frame (identity under root?)
    Wb = g.world(bm); Js = [np.zeros(len(Pb), int)]; PP, NN, CC, II = [Pb], [Nb], [B['COLOR_0']], [I]; nv = len(Pb)
    for k, pn_ in enumerate(parts, start=1):
        mi = mesh_node(pn_); pp = j['meshes'][j['nodes'][mi]['mesh']]['primitives']; assert len(pp) == 1 and j['materials'][pp[0]['material']]['name'] == 'SHM_Paint'
        A_ = pp[0]['attributes']; Pp = g.acc(A_['POSITION']).astype(np.float64); Np = g.acc(A_['NORMAL']).astype(np.float64)
        # bind: vertex in Base_Paint mesh space so that J_k * IBM_k * v = W_part * v_part  ->  v = Wb^-1 W_part v_part
        M = np.linalg.inv(Wb) @ g.world(mi); PP.append(Pp @ M[:3, :3].T + M[:3, 3]); Nm = Np @ M[:3, :3].T; NN.append(Nm / np.linalg.norm(Nm, axis=1, keepdims=True))
        CC.append(g.acc(A_['COLOR_0'])); II.append(g.acc(pp[0]['indices']).ravel().astype(np.int64) + nv); Js.append(np.full(len(Pp), k)); nv += len(Pp)
        j['nodes'][mi].pop('mesh')
    Pn = np.vstack(PP); Nn = np.vstack(NN); Cn = np.vstack(CC); In = np.concatenate(II); Jn = np.concatenate(Js)
    J4 = np.zeros((len(Pn), 4), np.uint8); J4[:, 0] = Jn; W4 = np.zeros((len(Pn), 4), np.uint8); W4[:, 0] = 255
    # IBM_k = (J_k world)^-1 @ Wb  (rest pose of every joint)
    IBM = np.stack([(np.linalg.inv(g.world(n)) @ Wb).T.reshape(16) for n in joints]).astype(np.float32)
    def new_acc(arr, ct, typ, norm=False):
        a_ = {'componentType': ct, 'type': typ, 'count': len(arr), 'bufferView': 0}
        if norm: a_['normalized'] = True
        if typ == 'VEC3' and ct == 5126: a_['min'] = [0, 0, 0]; a_['max'] = [0, 0, 0]
        j['accessors'].append(a_); repl[len(j['accessors']) - 1] = arr; return len(j['accessors']) - 1
    bp['attributes'] = {'POSITION': new_acc(Pn.astype(np.float32), 5126, 'VEC3'), 'NORMAL': new_acc(Nn.astype(np.float32), 5126, 'VEC3'),
                        'COLOR_0': new_acc(Cn.astype(np.uint8), 5121, 'VEC4', True), 'JOINTS_0': new_acc(J4, 5121, 'VEC4'), 'WEIGHTS_0': new_acc(W4, 5121, 'VEC4', True)}
    bp['indices'] = new_acc(In.astype(np.uint32 if nv > 65535 else np.uint16).reshape(-1, 1), 5125 if nv > 65535 else 5123, 'SCALAR')
    j.setdefault('skins', []).append({'name': 'Base_Paint_Skin', 'joints': joints, 'inverseBindMatrices': new_acc(IBM.reshape(-1, 16), 5126, 'MAT4')})
    j['nodes'][bm]['skin'] = len(j['skins']) - 1
    stats['skin_merged'] = parts; stats['skin_tris'] = int(len(In) // 3)
# mesh nodes back onto their named parents (gltfpack rebuilds named -> unnamed(mesh) child)
for i, N in enumerate(j['nodes']):
    if 'mesh' in N and not N.get('name') and i in par:
        q = par[i]; j['nodes'][q]['mesh'] = N.pop('mesh')
        if 'skin' in N: j['nodes'][q]['skin'] = N.pop('skin')
# compact accessors (drop the merged parts' old ones)
used = set()
for m in j['meshes']:
    for p in m['primitives']:
        used |= set(p['attributes'].values()); used.add(p['indices'])
        for t in p.get('targets', []): used |= set(t.values())
for s in j.get('skins', []): used.add(s['inverseBindMatrices'])
for an in j.get('animations', []):
    for s in an['samplers']: used |= {s['input'], s['output']}
order = sorted(used); ni_ = {o: k for k, o in enumerate(order)}; data = {o: g.acc(o) for o in order}
j['accessors'] = [j['accessors'][o] for o in order]; repl.clear(); repl.update({ni_[o]: data[o] for o in order}); g.acc = lambda i: repl[i]
for m in j['meshes']:
    for p in m['primitives']:
        p['attributes'] = {k: ni_[v] for k, v in p['attributes'].items()}; p['indices'] = ni_[p['indices']]
        if 'targets' in p: p['targets'] = [{k: ni_[v] for k, v in t.items()} for t in p['targets']]
for s in j.get('skins', []): s['inverseBindMatrices'] = ni_[s['inverseBindMatrices']]
for an in j.get('animations', []):
    for s in an['samplers']: s['input'] = ni_[s['input']]; s['output'] = ni_[s['output']]
# drop meshes no node uses
usedm = sorted({N['mesh'] for N in j['nodes'] if 'mesh' in N}); mm = {o: k for k, o in enumerate(usedm)}
j['meshes'] = [j['meshes'][o] for o in usedm]
for N in j['nodes']:
    if 'mesh' in N: N['mesh'] = mm[N['mesh']]
for a_ in j['accessors']: a_['bufferView'] = 0; a_.pop('byteOffset', None)
g.save(OUT, {})
print(json.dumps(stats))
