"""Life Support game GLB, tiered: master .blend -> static base merged by material + named tier / moving-part nodes + empty markers.
usage: blender -b life_support_master.blend -P build_game_glb_tiered.py -- --out raw.glb [--target 24000] [--tierratio 0.45]
then:  gltfpack -i raw.glb -o life_support_game.glb -cc -kn -ke     (meshopt + quantization; keep named nodes, extras, animations)
Same culling and SHM_* palette remap as build_game_glb.py. Tier nodes (Tier_03/05/08/12/20) carry extras
{"tier": N, "hidden_by_default": true}; each is ONE draw (dominant SHM_ material, other swatches kept as COLOR_0).
Fan_Scrubber spins (clip Fan_Scrubber_Spin, pivot at the hub, axis +X); Beacon_Lights blinks (clip Beacon_Lights_Blink, scale 1 -> 0.001).
Markers (empties): Airlock_Door, Crew_Path_01..05, Pipe_TankFarm, Cam_Target (extras {frame_w}: game camera aim point)."""
import bpy, bmesh, json, os, sys, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i][2:]: a[i + 1] for i in range(0, len(a) - 1, 2)}
OUT = A.get('out', '/tmp/ls_game_raw.glb'); TARGET = int(A.get('target', 24000))
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
    ('LS_RedLamp', 'SH_GlowRed'), ('LS_Red', 'SH_Red'), ('LS_White', 'SH_White'), ('LS_ShieldTile', 'SH_White'), ('LS_InkWhite', 'SH_White'),
    ('LS_Graphite', 'SH_Graphite'), ('LS_BandGraphite', 'SH_Graphite'), ('LS_Rubber', 'SH_Graphite'), ('LS_Ink', 'SH_Graphite'), ('LS_Void', 'SH_Graphite'),
    ('LS_Satin', 'SH_Steel'), ('LS_Chrome', 'SH_Steel'), ('LS_MLI', 'SH_Foil'), ('LS_Rad', 'SH_Radiator'), ('LS_SolarCells', 'SH_Solar'),
    ('LS_O2Band', 'SH_PipeO2'), ('LS_H2OBand', 'SH_PipeH2O'), ('LS_Slag', 'SH_Rock'), ('LS_Ilmenite', 'SH_Rock'), ('LS_IceRegolith', 'SH_Rock'), ('LS_Port', 'SH_Glass'),
    ('LS_CyanStrip', 'SH_GlowCyan'), ('LS_CyanSoft', 'SH_GlowCyan'), ('LS_Cyan', 'SH_GlowCyan'), ('LS_SightGlass', 'SH_GlowCyan'),
    ('LS_Lamp', 'SH_GlowWhite'), ('LS_StatusWhite', 'SH_GlowWhite'), ('LS_GreenLamp', 'SH_GlowWhite'), ('LS_ReactorPort', 'SH_GlowWhite'),
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

DROP_NAMES = ('st_', 'bolt', 'rivet', 'guy', 'grate', 'grating', 'nozzle', 'louver', 'lamp', 'cable_tie', 'tie_', 'weld', 'seam', 'clamp', 'hinge', 'handle', 'rail_post', 'bracket')
FORCE_KEEP = ('beacon', 'vent_lamp0', 'vent_lamp1')
KEEP_SMALL = ('haz', 'cyan', 'band', 'strip', 'beacon')
mine = [o for o in bpy.data.collections['Mine'].all_objects]
dg = bpy.context.evaluated_depsgraph_get()
keep, dropped = [], 0
for ob in mine:
    if ob.type not in ('MESH', 'CURVE', 'FONT'):
        continue
    nm = ob.name.lower()
    if ob.name in FORCE_KEEP:
        keep.append(ob); continue
    if ob.type == 'FONT' or nm.endswith('_t') or '_t.' in nm or nm.startswith('text'):
        dropped += 1; continue
    dims = ob.dimensions; big = max(dims)
    if any(nm.startswith(k) or ('_' + k) in nm for k in DROP_NAMES) and not any(k in nm for k in KEEP_SMALL):
        dropped += 1; continue
    if big < 0.22 and not any(k in nm for k in KEEP_SMALL):
        dropped += 1; continue
    if big < 1.0 and min(dims) < 0.03 and 'haz' not in nm and 'cyan' not in nm:   # wires / thin trims
        dropped += 1; continue
    keep.append(ob)

print('KEEP', len(keep), 'DROP', dropped)
def bbc(ob):
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return Vector([(min(v[i] for v in bb) + max(v[i] for v in bb)) / 2 for i in range(3)])
def near(ob, x, y, r):
    c = bbc(ob); return math.hypot(c.x - x, c.y - y) < r
def group_of(ob):
    n = ob.name
    if n == 'co2_blower_fan': return 'Fan_Scrubber'
    if n in FORCE_KEEP: return 'Beacon_Lights'
    if n.startswith('rad2_'): return 'Tier_03'                                   # third radiator wing (4 panels, posts, manifolds, loop)
    if n.startswith('o2_tank') and near(ob, -3.3, 28.6, 1.8): return 'Tier_05'   # second O2 storage sphere + legs/pads/band/girder
    if n.startswith(('co2_bed', 'co2_actuator', 'co2_valve')) and bbc(ob).x > 4.55: return 'Tier_08'  # scrubber beds 3 and 4
    if n.startswith('h2o_tank') and near(ob, 7.4, 23.4, 1.3): return 'Tier_12'   # third H2O tank
    if n.startswith('solar_'): return 'Tier_20'                                  # both solar masts + arrays
    return 'Base'
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
        c_ = s[1] if s[0].name not in ('SHM_GlowCyan', 'SHM_GlowWhite') else lin(MERGED[s[0].name]['base'])  # glow faces keep their hue if folded
        for li in poly.loop_indices: ca.data[li].color = c_
    for i, (m_, _) in enumerate(sm): me.materials[i] = m_
    g = group_of(ob)
    no = bpy.data.objects.new('g_' + ob.name, me); col.objects.link(no); groups.setdefault(g, []).append(no)
for c in list(bpy.context.scene.collection.children):
    if c != col: bpy.context.scene.collection.children.unlink(c)
def tris(objs):
    return sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
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
T1 = {g: tris(o) for g, o in groups.items()}; TT = sum(T1.values()); print('TRIS after planar', T1, TT)
TR = float(A.get('tierratio', 0.45))   # tiers/moving parts are small and read as silhouettes: decimate them less than the base
TS = sum(v for g, v in T1.items() if g != 'Base')
R = min(1.0, (TARGET - TS * TR) / T1['Base'])
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
root = bpy.data.objects.new('LifeSupport', None); col.objects.link(root)
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
            o.name = o.material_slots[list(used)[0]].material.name.replace('SHM_', 'LS_')
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
            bpy.ops.object.material_slot_remove_unused(); bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
            o.parent = root; nodes.append(o)
        continue
    # one draw per tier / moving part: dominant material wins, other faces keep their swatch colour in COLOR_0
    a = area_by_mat(J_); dom = max(a, key=a.get)
    if dom in ('SHM_GlowCyan', 'SHM_GlowWhite') and g != 'Beacon_Lights': dom = 'SHM_Paint'
    J_.data.materials.clear(); J_.data.materials.append(SH[dom])
    for p in J_.data.polygons: p.material_index = 0
    J_.name = g; J_.data.name = g + '_mesh'
    bpy.ops.object.select_all(action='DESELECT'); J_.select_set(True); bpy.context.view_layer.objects.active = J_
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    bb = [Vector(c) for c in J_.bound_box]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx = Vector([max(v[i] for v in bb) for i in range(3)])
    if g in ('Fan_Scrubber', 'Beacon_Lights'):
        piv = (mn + mx) / 2
        if g == 'Beacon_Lights':
            b = bpy.data.objects.get('beacon'); piv = bbc(b) if b else piv
    else:
        piv = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, 0.0))
    set_origin(J_, piv); J_.parent = root; nodes.append(J_)
    if g in TIERS: J_['tier'] = TIERS[g]; J_['hidden_by_default'] = True
    print('NODE', g, dom, tris([J_]), 'pivot', tuple(round(v, 3) for v in piv))
sc = bpy.context.scene; sc.render.fps = 30
fan = bpy.data.objects.get('Fan_Scrubber')
if fan:
    fan.rotation_mode = 'XYZ'; fan.animation_data_create(); act = bpy.data.actions.new('Fan_Scrubber_Spin'); fan.animation_data.action = act
    for k in range(5):
        fan.rotation_euler = (k * math.pi / 2, 0, 0); fan.keyframe_insert('rotation_euler', frame=k * 7.5)   # 1 rev / s about the hub's +X axis
    for fc in act.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
bl = bpy.data.objects.get('Beacon_Lights')
if bl:
    bl.animation_data_create(); act = bpy.data.actions.new('Beacon_Lights_Blink'); bl.animation_data.action = act
    for f, s in ((0, 1.0), (9, 0.001), (45, 0.001)):       # 0.3 s on, 1.2 s off, 1.5 s loop
        bl.scale = (s, s, s); bl.keyframe_insert('scale', frame=f)
    for fc in act.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    bl.scale = (1, 1, 1)
MK = {'Airlock_Door': (0.0, -7.86, 1.7),                 # outer face of the suitport hatch (centre), facing -Y (glTF +Z)
      'Crew_Path_01': (0.0, -8.4, 0.2), 'Crew_Path_02': (0.0, -9.6, 0.2), 'Crew_Path_03': (0.0, -11.4, 0.25),
      'Crew_Path_04': (0.0, -13.2, 0.0), 'Crew_Path_05': (0.0, -15.5, 0.0),
      'Pipe_TankFarm': (6.6, -11.8, 0.6)}                 # open flange at the end of the CO2 transfer line, facing -Y (toward the Tank Farm)
for n, p in MK.items():
    e = bpy.data.objects.new(n, None); e.empty_display_type = 'ARROWS'; e.empty_display_size = 0.5; e.location = p; col.objects.link(e); e.parent = root
# Cam_Target: empty only (no draw), extras {frame_w}; values written to the scene by build_life_support.py (PHONE_CAM)
_sc = bpy.context.scene; assert 'cam_target' in _sc and 'frame_w' in _sc, 'rebuild life_support_master.blend (needs scene cam_target / frame_w)'
ct = bpy.data.objects.new('Cam_Target', None); ct.empty_display_type = 'PLAIN_AXES'; ct.location = tuple(_sc['cam_target']); col.objects.link(ct); ct.parent = root
ct['frame_w'] = float(_sc['frame_w'])
print('NODES', sorted(o.name for o in root.children))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_extras=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True, export_optimize_animation_size=False,
                          export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False, export_vertex_color='ACTIVE', export_all_vertex_colors=False)
if A.get('blend'): bpy.ops.wm.save_as_mainfile(filepath=A['blend'], compress=True)
print('RAW', OUT, os.path.getsize(OUT))
