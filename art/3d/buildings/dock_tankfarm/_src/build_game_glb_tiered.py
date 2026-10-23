"""Cargo Space Dock + Tank Farm game GLB, tiered (adapted from life_support/_src/build_game_glb_tiered.py).
master .blend -> static base merged by material + named tier / moving-part nodes + empty markers.
usage: blender -b dock_tankfarm_master.blend -P build_game_glb_tiered.py -- --out raw.glb [--target 28000] [--tierratio 0.7]
then:  gltfpack -i raw.glb -o dock_tankfarm_game.glb -cc -kn -ke     (meshopt + quantization; keep named nodes, extras, animations)

Grouping comes from the master: every object carries ob['grp'] (default Base). Pivots + markers come from scene['game_nodes'].
Tier nodes Tier_03/05/08/12/20 carry extras {"tier": N, "hidden_by_default": true}; each is ONE draw (dominant SHM_ material,
other swatches kept as COLOR_0). Moving parts (one draw each, origin at the hinge / pivot):
  Crane_Gantry  - clip crane_gantry_move   (travels +4.5 m along the rails toward the hall and back, 6 s eased loop)
  Dock_Door     - clip dock_door_open      (rolling curtain, pivot at the drum line: scale Y(glTF) 1 -> 0.06 over 2.5 s)
  Beacon_Lights - clip Beacon_Lights_Blink (scale 1 -> 0.001, 0.3 s on / 1.2 s off, 1.5 s loop)
Markers (empties): Road_Entry, Crate_Drop, Container_Stack, Pipe_LaunchPad, Crew_Path_01..08."""
import bpy, bmesh, json, os, sys, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i][2:]: a[i + 1] for i in range(0, len(a) - 1, 2)}
OUT = A.get('out', '/tmp/dk_game_raw.glb'); TARGET = int(A.get('target', 28000))
HERE = os.path.dirname(os.path.abspath(__file__))

def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]
J = json.load(open(os.path.join(HERE, '..', '..', '_shared', 'shared_materials.json')))
SW, MERGED, S2M = J['materials'], J['merged_materials'], J['swatch_to_merged']
SH = {}
for n, d in MERGED.items():
    m = bpy.data.materials.new(n); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(d['base']); b.inputs['Metallic'].default_value = d['metal']; b.inputs['Roughness'].default_value = d['rough']
    if d.get('vertex_colors'):
        ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'; nt.links.new(ca.outputs['Color'], b.inputs['Base Color'])
    if 'emissive' in d:
        b.inputs['Emission Color'].default_value = lin(d['emissive']); b.inputs['Emission Strength'].default_value = d['emissive_strength']
    m.use_backface_culling = True; SH[n] = m
MAP = [  # master material name prefix -> shared swatch (SH_*), whose base colour becomes the vertex colour
    ('DK_RedLamp', 'SH_GlowRed'), ('DK_Red', 'SH_Red'), ('DK_InkWhite', 'SH_White'), ('DK_White', 'SH_White'),
    ('DK_Graphite', 'SH_Graphite'), ('DK_Rubber', 'SH_Graphite'), ('DK_Ink', 'SH_Graphite'), ('DK_Interior', 'SH_Graphite'),
    ('DK_Satin', 'SH_Steel'), ('DK_Chrome', 'SH_Steel'), ('DK_Platinum', 'SH_Steel'), ('DK_MLI', 'SH_Foil'),
    ('DK_Radiator', 'SH_Radiator'), ('DK_SolarCells', 'SH_Solar'), ('DK_Port', 'SH_Glass'),
    ('DK_Pad', 'SH_Rock'), ('DK_Road', 'SH_Rock'), ('M_Regolith', 'SH_Rock'),
    ('DK_Cyan', 'SH_GlowCyan'), ('DK_NeonBlue', 'SH_GlowCyan'), ('DK_He3', 'SH_GlowCyan'),
    ('DK_Lamp', 'SH_GlowWhite'), ('DK_StatusWhite', 'SH_GlowWhite'), ('DK_GreenLamp', 'SH_GlowWhite'),
]
def shared_for(m):
    sw = None
    if m is not None:
        for p, s_ in MAP:
            if m.name.startswith(p): sw = s_; break
    if sw is None:
        c = m.diffuse_color if m else (1, 1, 1, 1); sw = 'SH_White' if 0.3 * c[0] + 0.6 * c[1] + 0.1 * c[2] > 0.35 else 'SH_Graphite'
        print('UNMAPPED', m.name if m else None, '->', sw)
    mm = S2M[sw]
    return SH[mm], (lin(SW[sw]['base']) if MERGED[mm].get('vertex_colors') else [1, 1, 1, 1])

GN = json.loads(bpy.context.scene['game_nodes'])
rig = bpy.data.objects.get('DoorRig')
if rig: rig.scale = (1, 1, 1)                    # game rest pose: door closed
bpy.context.view_layer.update()

DROP_NAMES = ('st_', 'bolt', 'rivet', 'grate', 'nozzle', 'louver', 'lamp', 'seam', 'clamp', 'handle', 'rail_post', 'bracket', 'rib', 'casting',
              'rung', 'cage', 'spoke', 'tread', 'twistlock', 'axle', 'fin', 'flange', 'clip', 'rope', 'cable', 'pline', 'buffer', 'doorline', 'bar',
              'drop_box', 'lane_line', 'gauge', 'relief', 'insul', '_ins', 'yoke', 'wheel', 'hatch_port', 'brush_core', 'reel', 'diaphragm', 'window',
              'stw_rail', 'handrail', 'cw_rail', 'mat_rail', 'srail', 'erail', 'sleeper_cap', 'edge', 'pad_curb_cyan', 'conduit', 'brace', 'rake', 'manifold')
FORCE_KEEP = ('beacon_hall', 'beacon_mast', 'sign_neon', 'gc_wheel', 'door_cyan', 'gc_rope', 'jib_rope')
KEEP_SMALL = ('cyan', 'band', 'strip', 'beacon', 'neon', 'he3_core')
mine = [o for o in bpy.data.collections['Mine'].all_objects]
dg = bpy.context.evaluated_depsgraph_get()
keep, dropped = [], 0
for ob in mine:
    if ob.type not in ('MESH', 'CURVE', 'FONT'): continue
    nm = ob.name.lower()
    if any(nm.startswith(k) for k in FORCE_KEEP) and 'frame' not in nm:
        keep.append(ob); continue
    if ob.type == 'FONT' or nm.endswith('_t') or '_t.' in nm or nm.startswith('text'):
        dropped += 1; continue
    dims = ob.dimensions; big = max(dims)
    if any(nm.startswith(k) or ('_' + k) in nm for k in DROP_NAMES) and not any(k in nm for k in KEEP_SMALL):
        dropped += 1; continue
    if big < 0.3 and not any(k in nm for k in KEEP_SMALL):
        dropped += 1; continue
    if big < 1.2 and min(dims) < 0.05 and 'cyan' not in nm:   # wires / thin trims
        dropped += 1; continue
    keep.append(ob)
for ob in keep:                                  # game LOD: bevels off (silhouette-only at phone scale)
    for md in ob.modifiers:
        if md.type == 'BEVEL': md.show_viewport = False
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
print('KEEP', len(keep), 'DROP', dropped)
def bbc(ob):
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return Vector([(min(v[i] for v in bb) + max(v[i] for v in bb)) / 2 for i in range(3)])
TIERS = {'Tier_03': 3, 'Tier_05': 5, 'Tier_08': 8, 'Tier_12': 12, 'Tier_20': 20}
col = bpy.data.collections.new('Game'); bpy.context.scene.collection.children.link(col)
groups = {}
for ob in keep:
    e = ob.evaluated_get(dg); me = bpy.data.meshes.new_from_object(e, preserve_all_data_layers=False, depsgraph=dg)
    if me is None or len(me.polygons) == 0: continue
    me.transform(ob.matrix_world)
    if len(me.materials) == 0: me.materials.append(None)
    sm = [shared_for(m) for m in me.materials]
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        s = sm[min(poly.material_index, len(sm) - 1)]
        c_ = s[1] if s[0].name not in ('SHM_GlowCyan', 'SHM_GlowWhite') else lin(MERGED[s[0].name]['base'])
        for li in poly.loop_indices: ca.data[li].color = c_
    for i, (m_, _) in enumerate(sm): me.materials[i] = m_
    g = ob.get('grp', 'Base')
    no = bpy.data.objects.new('g_' + ob.name, me); col.objects.link(no); groups.setdefault(g, []).append(no)
for c in list(bpy.context.scene.collection.children):
    if c != col: bpy.context.scene.collection.children.unlink(c)
def tris(objs): return sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
def area_by_mat(o):
    a = {}
    for p in o.data.polygons:
        m = o.material_slots[p.material_index].material.name; a[m] = a.get(m, 0) + p.area
    return a
for g, objs in groups.items():
    for o in objs:
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.004)
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(4), verts=bm.verts, edges=bm.edges, delimit={'MATERIAL'})
        bm.to_mesh(o.data); bm.free()
T1 = {g: tris(o) for g, o in groups.items()}; print('TRIS after planar', T1, sum(T1.values()))
TR = float(A.get('tierratio', 0.7))
TS = sum(v for g, v in T1.items() if g != 'Base')
R = min(1.0, (TARGET - TS * TR) / T1['Base'])
print('BASE ratio', round(R, 4))
def join(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); return bpy.context.view_layer.objects.active
def decimate(o, tgt):
    for it in range(6):
        t = tris([o])
        if t <= tgt: break
        mod = o.modifiers.new('dec', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'; mod.ratio = tgt / t * 0.98; mod.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=mod.name)
def set_origin(o, p):
    o.data.transform(Matrix.Translation(-p)); o.location = p
root = bpy.data.objects.new('DockTankFarm', None); col.objects.link(root)
nodes = []
for g, objs in groups.items():
    J_ = join(objs)
    if T1[g] > 400: decimate(J_, int(T1[g] * (R if g == 'Base' else TR)))
    if g == 'Base':
        bpy.ops.object.material_slot_remove_unused()
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
        parts = [o for o in col.objects if o.type == 'MESH' and o.name.startswith('g_') and o.data.users and o in bpy.context.selected_objects]
        for o in parts:
            used = {p.material_index for p in o.data.polygons}
            o.name = o.material_slots[list(used)[0]].material.name.replace('SHM_', 'Base_')
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
            bpy.ops.object.material_slot_remove_unused(); bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
            o.parent = root; nodes.append(o); print('NODE', o.name, tris([o]))
        continue
    a = area_by_mat(J_); dom = max(a, key=a.get)
    if dom in ('SHM_GlowCyan', 'SHM_GlowWhite') and g != 'Beacon_Lights': dom = 'SHM_Paint'
    J_.data.materials.clear(); J_.data.materials.append(SH[dom])
    for p in J_.data.polygons: p.material_index = 0
    J_.name = g; J_.data.name = g + '_mesh'
    bpy.ops.object.select_all(action='DESELECT'); J_.select_set(True); bpy.context.view_layer.objects.active = J_
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    bb = [Vector(c) for c in J_.bound_box]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx = Vector([max(v[i] for v in bb) for i in range(3)])
    piv = Vector(GN['pivots'][g]) if g in GN['pivots'] else Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, 0.0))
    set_origin(J_, piv); J_.parent = root; nodes.append(J_)
    if g in TIERS: J_['tier'] = TIERS[g]; J_['hidden_by_default'] = True
    print('NODE', g, dom, tris([J_]), 'pivot', tuple(round(v, 3) for v in piv))
sc = bpy.context.scene; sc.render.fps = 30
def keys(ob, clip, path, frames, interp='BEZIER'):
    ob.animation_data_create(); act = bpy.data.actions.new(clip); ob.animation_data.action = act
    rest = tuple(getattr(ob, path))
    for f, v in frames:
        setattr(ob, path, v); ob.keyframe_insert(path, frame=f)
    for fc in act.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = interp
    setattr(ob, path, rest)
cg = bpy.data.objects.get('Crane_Gantry')
if cg:
    L0 = tuple(cg.location); L1 = (L0[0], L0[1] + 4.5, L0[2])
    keys(cg, 'crane_gantry_move', 'location', ((0, L0), (90, L1), (180, L0)))           # 6 s loop, eased
dd = bpy.data.objects.get('Dock_Door')
if dd: keys(dd, 'dock_door_open', 'scale', ((0, (1, 1, 1)), (75, (1, 1, 0.06))))       # 2.5 s, curtain rolls up into the drum
bl = bpy.data.objects.get('Beacon_Lights')
if bl: keys(bl, 'Beacon_Lights_Blink', 'scale', ((0, (1, 1, 1)), (9, (0.001,) * 3), (45, (0.001,) * 3)), 'CONSTANT')
for n, p in sorted(GN['markers'].items()):
    old = bpy.data.objects.get(n)          # e.g. the master's own Cam_Target empty: replace it so the marker keeps its exact name
    if old: bpy.data.objects.remove(old, do_unlink=True)
    e = bpy.data.objects.new(n, None); e.empty_display_type = 'ARROWS'; e.empty_display_size = 0.5; e.location = p; col.objects.link(e); e.parent = root
    for k, v in GN.get('marker_extras', {}).get(n, {}).items(): e[k] = v
print('NODES', sorted(o.name for o in root.children))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_extras=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True, export_optimize_animation_size=False,
                          export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False, export_vertex_color='ACTIVE', export_all_vertex_colors=False)
if A.get('blend'): bpy.ops.wm.save_as_mainfile(filepath=A['blend'], compress=True)
print('RAW', OUT, os.path.getsize(OUT))
