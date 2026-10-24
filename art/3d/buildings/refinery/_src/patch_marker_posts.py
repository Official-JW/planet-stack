"""10/23 PM (Jacob, via Director): PL-1 buried-pipeline marker posts plm0..plm6 red -> white with one cyan glow band near the top.
Game-GLB patch, so the other 29k decimated tris of the station stay byte-for-byte what they were (a full rebuild re-decimates Base):
  * recolours the 7 post boxes in Base_Paint (COLOR_0 = RF_Red 122,8,6) to the station white (SHM_Paint, no new material),
  * adds a 4-sided band (0.132 m square, y 0.66..0.73) around each post into Base_GlowCyan (SHM_GlowCyan) -> 0 extra draws, +56 tris,
  * bakes each mesh node's dequantisation transform into its vertices so the repack does not stack a second quantisation node.
build_refinery.py has the same change at the source (plm{k}_pole WHITE_S + plm{k}_band CYANL), so the next full rebuild matches.
usage: gltfpack -i refinery_game.glb -o ref_plain.glb -noq -kn -ke
       python3 patch_marker_posts.py ref_plain.glb ref_raw.glb && gltfpack -i ref_raw.glb -o refinery_game.glb -cc -kn -ke"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'props', '_shared_src'))
from glbskin import GLB
SRC, OUT = sys.argv[1], sys.argv[2]
g = GLB(SRC); j = g.j; repl = {}
def mesh_node(name):
    par = next(i for i, N in enumerate(j['nodes']) if N.get('name') == name)
    return next(c for c in j['nodes'][par].get('children', []) if 'mesh' in j['nodes'][c])
RED = (122, 8, 6)
# --- recolour
np_ = mesh_node('Base_Paint'); pr = j['meshes'][j['nodes'][np_]['mesh']]['primitives'][0]; T = g.node_local(np_)
P = g.acc(pr['attributes']['POSITION']).astype(np.float64); Pl = P @ T[:3, :3].T + T[:3, 3]; C = g.acc(pr['attributes']['COLOR_0'])
post = (C[:, 0] == RED[0]) & (C[:, 1] == RED[1]) & (C[:, 2] == RED[2]) & (Pl[:, 2] < -18.5) & (Pl[:, 2] > -18.75) & (Pl[:, 1] < 0.85)
whites = C[(C[:, 0] > 180) & (np.abs(C[:, 0].astype(int) - C[:, 2]) < 25)]
vals, cnt = np.unique(whites, axis=0, return_counts=True); WHITE = vals[cnt.argmax()]
cx = sorted(set(np.round(Pl[post, 0], 1)))
centres = []
for x in np.unique(np.round(Pl[post, 0] / 2) * 2):
    s = post & (np.abs(Pl[:, 0] - x) < 1.0); centres.append((Pl[s, 0].min() + Pl[s, 0].max()) / 2)
zc = (Pl[post, 2].min() + Pl[post, 2].max()) / 2; ytop = Pl[post, 1].max()
assert len(centres) == 7 and post.sum() == 168, (len(centres), post.sum())
C2 = C.copy(); C2[post] = WHITE; repl[pr['attributes']['COLOR_0']] = C2
# --- cyan bands into Base_GlowCyan
ng = mesh_node('Base_GlowCyan'); pg = j['meshes'][j['nodes'][ng]['mesh']]['primitives'][0]; Tg = g.node_local(ng)
Pg = g.acc(pg['attributes']['POSITION']).astype(np.float64); Pg = Pg @ Tg[:3, :3].T + Tg[:3, 3]; Ng = g.acc(pg['attributes']['NORMAL']).astype(np.float64)
Ig = g.acc(pg['indices']).ravel().astype(np.int64)
h = 0.066; y0, y1 = 0.66, 0.73
nv, nn, ni = [], [], []
for x in centres:
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = np.array((dx, 0, dz), float); t = np.array((-dz, 0, dx), float); c = np.array((x, 0, zc)) + n * h
        q = [c - t * h + (0, y0, 0), c + t * h + (0, y0, 0), c + t * h + (0, y1, 0), c - t * h + (0, y1, 0)]
        b = len(Pg) + len(nv); nv += q; nn += [n] * 4
        tri = [b, b + 1, b + 2, b, b + 2, b + 3]
        if np.dot(np.cross(q[1] - q[0], q[2] - q[0]), n) < 0: tri = [b, b + 2, b + 1, b, b + 3, b + 2]
        ni += tri
# --- bake every mesh node transform (positions; normals are unchanged by the uniform scale)
for i, N in enumerate(j['nodes']):
    if 'mesh' not in N: continue
    Ti = g.node_local(i)
    for p in j['meshes'][N['mesh']]['primitives']:
        ai = p['attributes']['POSITION']
        if i == ng: arr = np.vstack([Pg, np.array(nv)])
        else: arr = g.acc(ai).astype(np.float64) @ Ti[:3, :3].T + Ti[:3, 3]
        repl[ai] = arr.astype(np.float32); j['accessors'][ai]['componentType'] = 5126; j['accessors'][ai].pop('normalized', None)
        if 'min' not in j['accessors'][ai]: j['accessors'][ai]['min'] = [0, 0, 0]; j['accessors'][ai]['max'] = [0, 0, 0]
    for k in ('translation', 'rotation', 'scale', 'matrix'): N.pop(k, None)
na = pg['attributes']['NORMAL']; repl[na] = np.vstack([Ng, np.array(nn)]).astype(np.float32); j['accessors'][na]['componentType'] = 5126; j['accessors'][na].pop('normalized', None)
Ii = np.concatenate([Ig, np.array(ni)]); repl[pg['indices']] = Ii.astype(np.uint32 if Ii.max() > 65535 else np.uint16).reshape(-1, 1)
j['accessors'][pg['indices']]['componentType'] = 5125 if Ii.max() > 65535 else 5123
# put each mesh back on its named parent (as the Blender export had it) so gltfpack rebuilds the original named -> unnamed(mesh) layout
for i, N in enumerate(j['nodes']):
    if 'mesh' in N and not N.get('name'):
        par = next(k for k, M in enumerate(j['nodes']) if i in M.get('children', []))
        j['nodes'][par]['mesh'] = N.pop('mesh')
_o = g.acc; g.acc = lambda i: repl[i] if i in repl else _o(i)
g.save(OUT, {})
print(json.dumps({'posts': [round(c, 3) for c in centres], 'post_z': round(zc, 3), 'post_top_y': round(float(ytop), 3), 'recoloured_verts': int(post.sum()),
                  'white': WHITE.tolist(), 'band_tris': len(ni) // 3, 'band_y': [y0, y1]}))
