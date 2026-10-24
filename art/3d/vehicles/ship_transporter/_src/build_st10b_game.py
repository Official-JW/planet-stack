"""ST-10B game GLB (Director pick 10/24). Blender 4.2 headless, no render:
  blender -b -t 4 -P build_st10b_game.py -- --loaded st10b_loaded_preview.glb --empty st10b_empty_preview.glb --out raw.glb [--lift 0.0]
then: gltfpack -i raw.glb -o st10b_game.glb -c -kn -km   (meshopt + quantization only; no simplification, no textures)
Inputs = the concept preview GLBs written by build_transporter.py --glb 1 (same builder, flat game palette).
Nodes (glTF, y up, origin = ship axis on the ground, travel along +X, open end -X):
  ST10B (root) > Body_Paint (vertex colour) / Body_GlowCyan / Body_GlowAmber (emissive), Cradle_Loaded, Cradle_Empty (one visible at a time),
                 Astronaut (tender, vertex colour, feet at its origin), markers Ship_Seat (0, 0.45, 0) and Tender_Spot.
Cradle split: objects whose vertices differ between the loaded and empty builds (arms, saddles, collar, mast); everything else is Body.
Reduction: drop grousers / text labels / ladder rungs / rail posts / deck ribs / pad edges; wheels rebuilt as 12-side tyre + 8-side hub;
then quadric collapse per group to its budget. Colours: per-material game hex baked to COLOR_0 (optional sRGB lift toward white for the
shaded-side target; lighting is never changed)."""
import bpy, bmesh, sys, re, math, json
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i][2:]: a[i + 1] for i in range(0, len(a) - 1, 2)}
LIFT = float(A.get('lift', 0.0)); OUT = A['out']
BUD = dict(Body=8600, Cradle=2700, Astronaut=900)
DROP = {'grouser', 'spoke', 'rim', 'hubcap', 'label', 'label2', 'lbl_rear', 'lad_rung', 'rail_post', 'deck_rib', 'pad_edge', 'susp_eye', 'boom_cyl_eye',
        'stick_cyl_eye', 'mast_cyl_eye', 'pp_vent', 'susp_gland', 'boom_cyl_gland', 'stick_cyl_gland', 'mast_cyl_gland', 'lidar_band'}
ASTRO_N = ('tablet', 'tablet_screen', 'forearm')
bpy.ops.wm.read_factory_settings(use_empty=True)
base = lambda n: re.sub(r'\.\d+$', '', n.split('|')[-1])
def imp(p, tag):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new: o.name = tag + '|' + o.name
    return {o.name.split('|', 1)[1]: o for o in new if o.type == 'MESH'}
E = imp(A['empty'], 'E'); L = imp(A['loaded'], 'L')
bpy.context.view_layer.update()
def wverts(o): return [o.matrix_world @ v.co for v in o.data.vertices]
def s2l(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def l2s(c): return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
def mcol(m):
    bs = m.node_tree.nodes.get('Principled BSDF') if m and m.use_nodes else None
    c = list(bs.inputs['Base Color'].default_value)[:3] if bs else [0.5] * 3
    glow = bool(bs and bs.inputs['Emission Strength'].default_value > 0 and max(bs.inputs['Emission Color'].default_value[:3]) > 0)
    return c, glow
def lift(c): return [s2l(1 - (1 - l2s(x)) * (1 - LIFT)) for x in c]
# ---- classify
groups = {'Body': [], 'Cradle_Loaded': [], 'Cradle_Empty': [], 'Astronaut': []}; wheels = []; stats = dict(dropped=0)
for n, o in L.items():
    b = base(n); mat = o.material_slots[0].material if o.material_slots else None
    is_astro = (mat and mat.name.startswith('G_M_')) or b in ASTRO_N
    if b == 'tyre':
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]; ctr = sum(bb, Vector()) / 8
        wheels.append((ctr, (max(v.z for v in bb) - min(v.z for v in bb)) / 2, (max(v.y for v in bb) - min(v.y for v in bb)))); continue
    if b in DROP: stats['dropped'] += 1; continue
    if is_astro: groups['Astronaut'].append(o); continue
    e = E.get(n); same = e is not None and len(e.data.vertices) == len(o.data.vertices) and all((p - q).length < 2e-3 for p, q in zip(wverts(o), wverts(e)))
    if same: groups['Body'].append(o)
    else:
        groups['Cradle_Loaded'].append(o)
        if e is not None: groups['Cradle_Empty'].append(e)
print('CLASS', {k: len(v) for k, v in groups.items()}, 'wheels', len(wheels), stats, flush=True)
# ---- rebuilt wheels (12-side tyre + 8-side hub), Body
TYRE_C = mcol(bpy.data.materials.get('G_Tyre'))[0]; HUB_C = mcol(bpy.data.materials.get('G_Steel'))[0]
def cyl_obj(name, r, depth, segs, loc, col):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r, depth=depth)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X')); bmesh.ops.translate(bm, verts=bm.verts, vec=loc)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o['col'] = list(col); return o
for i, (c, r, w) in enumerate(wheels):
    groups['Body'].append(cyl_obj(f'wheel{i}', r, w, 12, c, TYRE_C)); groups['Body'].append(cyl_obj(f'hub{i}', r * 0.62, w + 0.06, 8, c, HUB_C))
# ---- bake colour, split glow, join per group
def bake(o, glow_ok):
    """returns 'paint' | 'cyan' | 'amber'; writes COLOR_0 (linear float) per corner"""
    m = o.material_slots[0].material if o.material_slots else None
    if 'col' in o: c, glow = o['col'], False
    else: c, glow = mcol(m)
    if glow and glow_ok:
        hx = m.name.lower(); return 'amber' if ('amber' in hx or 'red' in hx) else 'cyan'
    cc = c if glow else lift(c)
    me = o.data; at = me.color_attributes.get('Col') or me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    for d in at.data: d.color = (cc[0], cc[1], cc[2], 1.0)
    return 'paint'
def join(objs, name):
    if not objs: return None
    for o in objs:
        o.data = o.data.copy(); o.data.transform(o.matrix_world); o.parent = None; o.matrix_world = Matrix.Identity(4)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        if o.name not in bpy.context.scene.collection.objects:
            for c in list(o.users_collection): c.objects.unlink(o)
            bpy.context.scene.collection.objects.link(o)
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); j = bpy.context.view_layer.objects.active; j.name = name; j.data.name = name
    j.data.materials.clear(); return j
def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)
def decimate(o, target):
    t0 = tris(o)
    if t0 > target:
        md = o.modifiers.new('dec', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = target / t0; md.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier='dec')
    return t0, tris(o)
PAINT = bpy.data.materials.new('ST10B_Paint'); PAINT.use_nodes = True; nt = PAINT.node_tree; bs = nt.nodes['Principled BSDF']
ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'; nt.links.new(ca.outputs['Color'], bs.inputs['Base Color'])
bs.inputs['Metallic'].default_value = 0.0; bs.inputs['Roughness'].default_value = 0.7
def glow_mat(name, hx):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']; c = [s2l(int(hx[i:i + 2], 16) / 255) for i in (1, 3, 5)]
    b.inputs['Base Color'].default_value = (*c, 1); b.inputs['Emission Color'].default_value = (*c, 1); b.inputs['Emission Strength'].default_value = 2.5; b.inputs['Roughness'].default_value = 0.7; return m
CYAN, AMBER = glow_mat('ST10B_GlowCyan', '#3ad0ff'), glow_mat('ST10B_GlowAmber', '#ffb020')
root = bpy.data.objects.new('ST10B', None); bpy.context.scene.collection.objects.link(root)
info = {}
def finish(o, mat, parent, budget=None):
    if o is None: return
    o.data.materials.append(mat)
    t0, t1 = decimate(o, budget) if budget else (tris(o), tris(o))
    bpy.context.view_layer.objects.active = o; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    o.parent = parent; info[o.name] = dict(tris_in=t0, tris=t1, verts=len(o.data.vertices), material=mat.name)
for g, objs in groups.items():
    glow_ok = g == 'Body'
    buckets = {'paint': [], 'cyan': [], 'amber': []}
    for o in objs: buckets[bake(o, glow_ok)].append(o)
    if g == 'Body':
        pj = join(buckets['paint'], 'Body_Paint'); cj = join(buckets['cyan'], 'Body_GlowCyan'); aj = join(buckets['amber'], 'Body_GlowAmber')
        glow_t = sum(tris(x) for x in (cj, aj) if x)
        finish(pj, PAINT, root, BUD['Body'] - glow_t); finish(cj, CYAN, root); finish(aj, AMBER, root)
    elif g.startswith('Cradle'):
        finish(join(buckets['paint'], g), PAINT, root, BUD['Cradle'])
    else:
        j = join(buckets['paint'], 'Astronaut')
        if j:   # origin at the feet
            mn = Vector((min(v.co.x for v in j.data.vertices), min(v.co.y for v in j.data.vertices), min(v.co.z for v in j.data.vertices)))
            mx = Vector((max(v.co.x for v in j.data.vertices), max(v.co.y for v in j.data.vertices), 0))
            feet = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z)); j.data.transform(Matrix.Translation(-feet)); j.location = feet
        finish(j, PAINT, root, BUD['Astronaut'])
for nm, loc in (('Ship_Seat', (0, 0, 0.45)), ('Tender_Spot', tuple(bpy.data.objects['Astronaut'].location) if 'Astronaut' in bpy.data.objects else (0, 0, 0))):
    e = bpy.data.objects.new(nm, None); bpy.context.scene.collection.objects.link(e); e.location = loc; e.parent = root
# remove leftovers
keep = {root} | set(root.children)
for o in list(bpy.data.objects):
    if o not in keep: bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in keep: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_animations=False,
                          export_cameras=False, export_lights=False, export_vertex_color='MATERIAL', export_normals=True, export_texcoords=False)
vis = sum(v['tris'] for k, v in info.items() if k != 'Cradle_Empty')
json.dump(dict(lift=LIFT, nodes=info, tris_visible_loaded=vis, tris_file=sum(v['tris'] for v in info.values()), wheels=len(wheels), class_counts={k: len(v) for k, v in groups.items()}),
          open(OUT.replace('.glb', '_build.json'), 'w'), indent=1)
print('GAMEGLB', OUT, json.dumps(info), 'visible', vis, flush=True)
