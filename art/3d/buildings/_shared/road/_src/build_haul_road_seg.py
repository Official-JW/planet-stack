"""Planet Stack shared haul-road segment (Mine -> Refinery haul road). v2 10/23 PM: packed-regolith tyre-track trail.
One 8.0 m tileable piece along +X with the two Refinery lanes: inbound (to the Refinery) centre glTF z +9, outbound (to the Mine) z 0.
The cross-section heights are unchanged from v1 (= the station roads' mine_layout._HALF / refinery _RHALF), so the joins stay flush:
4 m graded running surface (crown +2 cm), tyre ruts 1.25..1.65 m either side (-2 cm), foot at 2.0, berm crest +25 cm at 2.35, toe buried -4 cm at 2.8.
v2 look (vertex colour + a few flat pebbles, no textures):
  * two dark compacted wheel ruts per lane with tread chevrons: rut rows every 0.19 m (= HT-04 tread pitch / 2), alternating dark / light,
    the rut centre row shifted 0.09 m so each band reads as a V pointing the lane's heading (inbound +X, outbound -X);
  * dusty, lighter scuffed berms and shoulders, darker compacted crown polish between the ruts, low-frequency vertex-colour variation;
  * scattered low pebbles (<= 7 cm proud, every top y <= 0.30) on the shoulders, foot and berms, kept off the ruts and 0.4 m clear of both ends.
All colour variation is 8 m periodic and the x 0 / x 8 rows carry exactly the v1 end colours (the station roads ease into those), so copies at
x = x0 + 8 k and both station joins stay seamless.
usage: blender -b -P build_haul_road_seg.py -- --out raw.glb
then:  gltfpack -i raw.glb -o haul_road_seg.glb -cc -kn -ke -vpf   (meshopt + quantization (float positions: ends exactly at x 0 / 8.0), no Draco)"""
import bpy, bmesh, sys, math, random
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i][2:]: a[i + 1] for i in range(0, len(a) - 1, 2)}
OUT = A.get('out', '/tmp/haul_road_seg_raw.glb')
L = 8.0
NR = 42                                              # rut rows: 42 spans = 0.1905 m (half the HT-04 tread pitch 0.38)
NC = 8                                               # coarse rows elsewhere: 1.0 m
LANES = [('inbound', 9.0, 0.045, +1), ('outbound', 0.0, 0.045, -1)]   # (name, glTF z of the centre line, surface y, heading sign)
HALF = [(0.0, 0.02, 'track'), (1.1, 0.0, 'track'), (1.25, -0.02, 'mark'), (1.65, -0.02, 'mark'), (1.8, 0.0, 'track'), (2.0, 0.0, 'foot'), (2.35, 0.25, 'crest'), (2.8, -0.04, 'toe')]
HEX = {'track': '#a4a7ac', 'mark': '#878a8f', 'foot': '#9da0a5', 'crest': '#939499', 'toe': '#82858a', 'wear': '#76797e', 'polish': '#adb0b5',
       'rut_dark': '#5f6267', 'rut_lite': '#8e9196', 'dust': '#b7b8b9', 'crown': '#979a9f', 'peb_a': '#6b6e72', 'peb_b': '#8a8c8f', 'peb_c': '#55585c'}
def srgb(h): h = h.lstrip('#'); return Vector([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
bm = bmesh.new(); cl = bm.loops.layers.color.new('Col')
TAU = 2 * math.pi
def wear(x, ph):   # v1: 8 m periodic rut wear (0..1)
    t = TAU * x / L
    return max(0.0, min(1.0, 0.5 + 0.35 * math.sin(t + ph) + 0.25 * math.sin(3 * t + 2 * ph)))
def v1col(off, kind, x, li):   # the exact v1 colour of a profile vertex (used verbatim on the end rows)
    c = srgb(HEX[kind])
    if kind == 'mark': c = c.lerp(srgb(HEX['wear']), 0.35 + 0.5 * wear(x, li * 1.7 + (0.9 if off > 0 else 0.0)))
    if kind == 'track' and abs(off) < 0.01: c = c.lerp(srgb(HEX['polish']), 0.5 * wear(x, li * 2.3 + 3.1))
    return c
def pn(x, s):      # periodic noise, exactly 0 at x 0 / 8 (sum of sin(2 pi k x / L))
    t = TAU * x / L
    return 0.5 * math.sin(t * 1 + s) * math.sin(t * 0.5) * 2 / 1.0 * 0.5 + 0.35 * math.sin(t * 2) * math.cos(t * 3 + s) + 0.25 * math.sin(t * 5) * math.cos(1.7 * s + t)
def col_at(off, kind, x, li, end):
    c = v1col(off, kind, x, li)
    if end: return c
    a = abs(off); n = pn(x, li * 3.1 + a * 2.3 + (0.7 if off > 0 else 0))
    if kind == 'track' and a < 0.01: c = c.lerp(srgb(HEX['crown']), 0.35 + 0.25 * n)            # compacted crown between the ruts
    elif kind == 'track' and a > 1.7: c = c.lerp(srgb(HEX['dust']), 0.30 + 0.25 * n)           # loose dust outside the ruts
    elif kind == 'track': c = c.lerp(srgb(HEX['wear']), 0.15 + 0.15 * n)                        # rut shoulder, tyre-scuffed
    elif kind == 'foot': c = c.lerp(srgb(HEX['dust']), 0.40 + 0.3 * n)
    elif kind == 'crest': c = c.lerp(srgb(HEX['dust']), 0.55 + 0.3 * n)                         # dusty raised berm
    elif kind == 'toe': c = c.lerp(srgb(HEX['dust']), 0.20 + 0.2 * n)
    return c
VERTS = {}
def V(x, y, z):
    k = (round(x, 5), round(y, 5), round(z, 5))
    if k not in VERTS: VERTS[k] = bm.verts.new(k)
    return VERTS[k]
def tri(p, c):
    vs = [V(*q) for q in p]
    if len(set(vs)) < 3: return
    try: f = bm.faces.new(vs)
    except ValueError: return
    if f.normal.z < 0: f.normal_flip()     # colours are looked up per vertex position below, so the flip keeps them
    for lp in f.loops:
        q = tuple(round(t, 5) for t in lp.vert.co); cc = c[[tuple(round(t, 5) for t in pp) for pp in p].index(q)]
        lp[cl] = (cc.x, cc.y, cc.z, 1.0)
def zipper(A_, B_):
    """strip between two columns given as [(pos, col)] sorted by x, with the same first/last x: triangulate without T-junctions"""
    i = j = 0
    while i < len(A_) - 1 or j < len(B_) - 1:
        adv_a = j >= len(B_) - 1 or (i < len(A_) - 1 and A_[i + 1][0][0] <= B_[j + 1][0][0])
        if adv_a: tri((A_[i][0], A_[i + 1][0], B_[j][0]), [A_[i][1], A_[i + 1][1], B_[j][1]]); i += 1
        else: tri((A_[i][0], B_[j + 1][0], B_[j][0]), [A_[i][1], B_[j + 1][1], B_[j][1]]); j += 1
rnd = random.Random(23)
stats = {'pebbles': 0}
for li, (nm, zc, ys, hd) in enumerate(LANES):
    yb = -zc                                         # Blender Y = -glTF Z
    # lateral columns (offset, dz, kind, fine?, shift): ruts get a centre column at +-1.45 with the chevron shift
    cols = []
    for side in (-1, 1):
        H = HALF[1:] if side < 0 else HALF
        seq = [(side * o, dz, k) for o, dz, k in (reversed(H) if side < 0 else H)]
        cols += seq
    prof = []
    for off, dz, k in cols:
        prof.append((off, dz, k, k == 'mark' or (k == 'track' and abs(abs(off) - 1.1) < 1e-6) or (k == 'track' and abs(abs(off) - 1.8) < 1e-6), 0.0))
        pass
    # insert rut centre columns between the two 'mark' columns of each side
    P2 = []
    for c0, c1 in zip(prof, prof[1:] + [None]):
        P2.append(c0)
        if c1 and c0[2] == 'mark' and c1[2] == 'mark':
            P2.append(((c0[0] + c1[0]) / 2, -0.02, 'rutc', True, 0.09 * hd))
    prof = P2
    def column(off, dz, kind, fine, shift):
        n = NR if fine else NC; out = []
        for i in range(n + 1):
            x = L * i / n
            if 0 < i < n: x = min(L - 0.02, max(0.02, x + shift))
            end = i in (0, n)
            z = dz if kind == 'toe' else ys + dz
            if kind in ('mark', 'rutc'):
                if kind == 'rutc':
                    m0 = [p for p in HALF if p[2] == 'mark']
                    cb = (v1col(-1.25 if off < 0 else 1.25, 'mark', x, li) + v1col(-1.65 if off < 0 else 1.65, 'mark', x, li)) * 0.5
                else: cb = v1col(off, 'mark', x, li)
                if end: c = cb
                else:
                    tone = srgb(HEX['rut_dark']) if i % 2 == 0 else srgb(HEX['rut_lite'])
                    c = cb.lerp(tone, (0.75 if kind == 'rutc' else 0.55) + 0.2 * pn(x, off))
            elif fine and not end and kind == 'track':     # rut lips: tread bands fade out across the lip
                cb = col_at(off, kind, x, li, False)
                c = cb.lerp(srgb(HEX['rut_dark'] if i % 2 == 0 else HEX['rut_lite']), 0.18)
            else: c = col_at(off, kind, x, li, end)
            out.append(((x, yb + off, z), c))
        return out
    C = [column(*p) for p in prof]
    for c0, c1 in zip(C, C[1:]): zipper(c0, c1)
    # pebbles: low 4-sided pyramids (<= 7 cm proud) on shoulders / foot / berm flanks, never on the ruts
    def surf_h(o):
        a = abs(o); pts = HALF
        for (o0, d0, k0), (o1, d1, k1) in zip(pts, pts[1:]):
            if o0 <= a <= o1:
                t = (a - o0) / (o1 - o0); y0 = d0 if k0 == 'toe' else ys + d0; y1 = d1 if k1 == 'toe' else ys + d1
                return y0 + t * (y1 - y0)
        return 0.0
    bands = [(1.8, 2.05, 7), (2.05, 2.3, 6), (2.4, 2.75, 7), (0.25, 0.9, 3)]
    for side in (-1, 1):
        for lo, hi, n in bands:
            for _ in range(n):
                x = rnd.uniform(0.4, L - 0.4); o = side * rnd.uniform(lo, hi); r = rnd.uniform(0.04, 0.11 if lo > 1 else 0.06)
                hgt = min(0.07, r * rnd.uniform(0.45, 0.8)); yg = surf_h(o) - 0.01
                if yg + hgt > 0.30: hgt = 0.30 - yg
                if hgt < 0.012: continue
                rot = rnd.uniform(0, TAU); cx, cy = x, yb + o
                base = [(cx + r * math.cos(rot + q * TAU / 4) * (1 + 0.3 * (q % 2)), cy + r * math.sin(rot + q * TAU / 4) * (1 + 0.3 * (q % 2)), yg) for q in range(4)]
                top = (cx + r * 0.15, cy - r * 0.1, yg + hgt)
                pc = srgb(HEX[rnd.choice(['peb_a', 'peb_b', 'peb_c'])])
                ct = pc.lerp(srgb(HEX['dust']), 0.25)
                for q in range(4): tri((base[q], base[(q + 1) % 4], top), [pc, pc, ct])
                stats['pebbles'] += 1
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    if f.normal.z < 0: f.normal_flip()
me = bpy.data.meshes.new('HaulRoad_Seg_mesh'); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
me.color_attributes.active_color = me.color_attributes['Col']
m = bpy.data.materials.new('SHM_Paint'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
b.inputs['Metallic'].default_value = 0.0; b.inputs['Roughness'].default_value = 0.42; m.use_backface_culling = True
ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'; nt.links.new(ca.outputs['Color'], b.inputs['Base Color'])
me.materials.append(m)
ob = bpy.data.objects.new('HaulRoad_Seg', me); bpy.context.scene.collection.objects.link(ob)
ob['tile_len_m'] = L; ob['axis'] = '+X'; ob['origin'] = 'segment start (x 0) on the ground, inbound lane centre at z +9, outbound at z 0'
ob['lanes'] = 'inbound z +9 heading +X (Mine -> Refinery), outbound z 0 heading -X (Refinery -> Mine); 4 m running surface, 5.6 m berm toe to toe'
ob['tiling'] = 'place copies at position.x = x0 + 8*k, y 0, z 0, no rotation; ends match exactly (see README)'
ob['surface_y'] = 0.045
ob['style'] = 'v2 packed-regolith trail: dark compacted tyre ruts with tread chevrons, dusty berms, low pebbles (max y 0.30); vertex colour only'
print('TRIS', sum(len(p.vertices) - 2 for p in me.polygons), 'VERTS', len(me.vertices), 'PEBBLES', stats['pebbles'])
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_extras=True,
                          export_animations=False, export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False,
                          export_vertex_color='ACTIVE', export_all_vertex_colors=False)
print('RAW', OUT)
