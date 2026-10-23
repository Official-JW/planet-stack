"""Refinery game GLB, tiered (adapted from dock_tankfarm/_src/build_game_glb_tiered.py).
master .blend -> static base merged by material + named tier / moving-part nodes + empty markers, in REFINERY_ANCHOR space.
usage: blender -b refinery_master.blend -P build_game_glb_tiered.py -- --out raw.glb [--target 23500] [--tierratio 0.55]
then:  gltfpack -i raw.glb -o refinery_game.glb -cc -kn -ke      (meshopt + quantization; keeps named nodes, extras, animations)

Space: GLB origin = the Mine's REFINERY_ANCHOR (place with refinery.position/quaternion = anchor world position/quaternion).
Local glTF +Z points at the truck: Path_Dump (the truck centre while tipping) is at glTF (0, 0, 4.84), and the intake-bin front lip
is 1.12 m along +Z. Compact layout: feeder/splitter toward local -X, then a fuel row (local x -11..-20) and a He-3 row
(local x -23..-29, camera side) that both flow toward local +Z (= Mine world +X).
Draw budget 13 with every tier showing:
  Base_Paint (SHM_Paint, all white/graphite/steel/foil/rock/pipe swatches as COLOR_0), Base_GlowCyan (SHM_GlowCyan: cyan strips,
  He-3 canisters, white lamps), Base_GlowRed (SH_GlowRed: reactor / kiln heat glow) = 3 draws
  + Kiln_Drum, Conveyor_He3, Conveyor_Fuel, Intake_Grate, Beacon_Lights (5) + Tier_03/05/08/12/20 (5) = 13.
Clips: kiln_spin (4 s loop, 1 turn), conveyor_he3_run / conveyor_fuel_run (1 s loop, one cleat pitch), intake_shake (0.6 s),
Beacon_Lights_Blink (1.2 s stepped scale)."""
import bpy, bmesh, json, os, sys, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i][2:]: a[i + 1] for i in range(0, len(a) - 1, 2)}
OUT = A.get('out', '/tmp/rf_game_raw.glb'); TARGET = int(A.get('target', 23500))
HERE = os.path.dirname(os.path.abspath(__file__))

def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]
J = json.load(open(os.path.join(HERE, '..', '..', '_shared', 'shared_materials.json')))
SW, MERGED, S2M = J['materials'], J['merged_materials'], J['swatch_to_merged']
SH = {}
def mk(n, d):
    m = bpy.data.materials.new(n); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(d['base']); b.inputs['Metallic'].default_value = d['metal']; b.inputs['Roughness'].default_value = d['rough']
    if d.get('vertex_colors'):
        ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'; nt.links.new(ca.outputs['Color'], b.inputs['Base Color'])
    if 'emissive' in d:
        b.inputs['Emission Color'].default_value = lin(d['emissive']); b.inputs['Emission Strength'].default_value = min(1.0, d['emissive_strength'])   # <= 1: no KHR_materials_emissive_strength (matches the Mine GLB)
    m.use_backface_culling = True; return m
for n in ('SHM_Paint', 'SHM_GlowCyan'): SH[n] = mk(n, MERGED[n])
SH['SH_GlowRed'] = mk('SH_GlowRed', SW['SH_GlowRed'])          # the shared red glow swatch, used as-is (heat glow + beacons)
# 3 base draws: metal swatches ride on SHM_Paint as vertex colours, white lamps ride on SHM_GlowCyan
TARGET_MAT = {'SHM_Paint': 'SHM_Paint', 'SHM_Metal': 'SHM_Paint', 'SHM_GlowCyan': 'SHM_GlowCyan', 'SHM_GlowWhite': 'SHM_GlowCyan'}
MAP = [  # master material prefix -> shared swatch
    ('RF_RedLamp', 'SH_GlowRed'), ('RF_HeatGlow', 'SH_GlowRed'), ('RF_HeatSoft', 'SH_GlowRed'), ('RF_Red', 'SH_Red'),
    ('RF_InkWhite', 'SH_White'), ('RF_White', 'SH_White'), ('RF_Frost', 'SH_White'), ('RF_StatusWhite', 'SH_GlowWhite'),
    ('RF_Graphite', 'SH_Graphite'), ('RF_Rubber', 'SH_Graphite'), ('RF_Ink', 'SH_Graphite'), ('RF_Interior', 'SH_Graphite'),
    ('RF_Satin', 'SH_Steel'), ('RF_Chrome', 'SH_Steel'), ('RF_Platinum', 'SH_Steel'), ('RF_Iron', 'SH_Steel'), ('RF_MLI', 'SH_Foil'),
    ('RF_Radiator', 'SH_Radiator'), ('RF_SolarCells', 'SH_Solar'), ('RF_Port', 'SH_Glass'),
    ('RF_PipeO2', 'SH_PipeO2'), ('RF_PipeH2O', 'SH_PipeH2O'),
    ('RF_Pad', 'SH_Rock'), ('RF_Road', 'SH_Rock'), ('RF_Ore', 'SH_Rock'), ('RF_Slag', 'SH_Rock'), ('RF_Tailings', 'SH_Rock'), ('M_Regolith', 'SH_Rock'),
    ('RF_Cyan', 'SH_GlowCyan'), ('RF_NeonBlue', 'SH_GlowCyan'), ('RF_He3', 'SH_GlowCyan'),
    ('RF_Lamp', 'SH_GlowWhite'), ('RF_GreenLamp', 'SH_GlowWhite'), ('RF_AmberLamp', 'SH_GlowWhite'),
]
def shared_for(m):
    sw = None
    if m is not None:
        for p, s_ in MAP:
            if m.name.startswith(p): sw = s_; break
    if sw is None:
        c = m.diffuse_color if m else (1, 1, 1, 1); sw = 'SH_White' if 0.3 * c[0] + 0.6 * c[1] + 0.1 * c[2] > 0.35 else 'SH_Graphite'
        print('UNMAPPED', m.name if m else None, '->', sw)
    if sw == 'SH_GlowRed': return SH['SH_GlowRed'], [1, 1, 1, 1]
    tm = TARGET_MAT[S2M[sw]]
    return SH[tm], (lin(SW[sw]['base']) if tm == 'SHM_Paint' else [1, 1, 1, 1])

GN = json.loads(bpy.context.scene['game_nodes'])
AX_ = GN.get('anchor_x', 4.84)
ANCH = Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Translation((-AX_, 0.0, 0.0))   # refinery final coords -> REFINERY_ANCHOR local
R3 = ANCH.to_3x3()
MOVING = ('Kiln_Drum', 'Conveyor_He3', 'Conveyor_Fuel', 'Intake_Grate', 'Beacon_Lights')
DROP_NAMES = ('st_', 'bolt', 'rivet', 'nozzle', 'louver', 'seam', 'clamp', 'handle', 'rail_post', 'bracket', 'rib', 'rung', 'cage', 'spoke',
              'tread', 'fin', 'flange', 'clip', 'cable', 'pdrop', 'gauge', 'yoke', 'wheel', 'window', 'handrail', 'rail', 'edge', 'conduit',
              'brace', 'idler', 'curtain', 'spring', 'post', 'ladder', 'hw_', 'valve', 'strap', 'bolt', 'stud', 'lamp_base', 'legx', 'plate_bk')
KEEP_SMALL = ('cyan', 'band', 'strip', 'beacon', 'neon', 'he3', 'can_', 'glow', 'hot', 'slot', 'canister')
mine = [o for o in bpy.data.collections['Mine'].all_objects]
keep, dropped = [], 0
for ob in mine:
    if ob.type not in ('MESH', 'CURVE', 'FONT'): continue
    nm = ob.name.lower(); g = ob.get('grp', 'Base')
    if ob.type == 'FONT' or nm.startswith('st_'): dropped += 1; continue
    dims = ob.dimensions; big = max(dims)
    if g in MOVING:                               # moving parts: keep everything but specks (grizzly bars, cleats, ore on the belt)
        if big < 0.12 and 'beacon' not in nm: dropped += 1; continue
        keep.append(ob); continue
    small_ok = any(k in nm for k in KEEP_SMALL)
    if any(nm.startswith(k) or ('_' + k) in nm for k in DROP_NAMES) and not small_ok: dropped += 1; continue
    if big < 0.35 and not small_ok: dropped += 1; continue
    if big < 1.2 and min(dims) < 0.05 and not small_ok: dropped += 1; continue
    keep.append(ob)
for ob in keep:
    for md in ob.modifiers:
        if md.type == 'BEVEL': md.show_viewport = False
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
print('KEEP', len(keep), 'DROP', dropped)
TIERS = {'Tier_03': 3, 'Tier_05': 5, 'Tier_08': 8, 'Tier_12': 12, 'Tier_20': 20}
col = bpy.data.collections.new('Game'); bpy.context.scene.collection.children.link(col)
groups = {}
for ob in keep:
    e = ob.evaluated_get(dg); me = bpy.data.meshes.new_from_object(e, preserve_all_data_layers=False, depsgraph=dg)
    if me is None or len(me.polygons) == 0: continue
    M = ANCH @ ob.matrix_world; me.transform(M)
    if M.determinant() < 0: me.flip_normals()
    if len(me.materials) == 0: me.materials.append(None)
    sm = [shared_for(m) for m in me.materials]
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        s = sm[min(poly.material_index, len(sm) - 1)]
        for li in poly.loop_indices: ca.data[li].color = s[1]
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
TR = float(A.get('tierratio', 0.55)); MR = float(A.get('movratio', 0.6))
RAT = {g: (MR if g in MOVING else TR) for g in T1 if g != 'Base'}
TS = sum(T1[g] * RAT[g] for g in RAT)
R = min(1.0, (TARGET - TS) / T1['Base'])
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
root = bpy.data.objects.new('Refinery', None); col.objects.link(root)
root['origin'] = 'REFINERY_ANCHOR (Mine station). Place with refinery.position/quaternion = anchor world position/quaternion.'
root['truck_dump'] = 'Path_Dump at local glTF (0, 0, 4.84): truck centre while tipping, rear toward -Z (the intake bin). Same spot as the Mine Path_Dump.'
root['layout'] = 'compact block south of the Mine haul loop, inside the Mine W=37 station frame: intake bin RB-1 at local +Z next to the origin, feeder + splitter run toward -X; fuel row (back, local x -11..-20) and He-3 row (front, camera side, local x -23..-29) both flow toward local +Z (world +X); process rows at 0.85 scale'
root['draws_all_tiers'] = 13
nodes = []
FORCE_DOM = {'Tier_03': 'SHM_GlowCyan', 'Beacon_Lights': 'SH_GlowRed'}
for g, objs in groups.items():
    J_ = join(objs)
    if T1[g] > 300: decimate(J_, int(T1[g] * (R if g == 'Base' else RAT[g])))
    if g == 'Base':
        bpy.ops.object.material_slot_remove_unused()
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
        parts = [o for o in col.objects if o.type == 'MESH' and o.name.startswith('g_') and o.data.users and o in bpy.context.selected_objects]
        for o in parts:
            used = {p.material_index for p in o.data.polygons}
            o.name = o.material_slots[list(used)[0]].material.name.replace('SHM_', 'Base_').replace('SH_', 'Base_')
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
            bpy.ops.object.material_slot_remove_unused(); bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
            o.parent = root; nodes.append(o); print('NODE', o.name, tris([o]))
        continue
    a_ = area_by_mat(J_); dom = FORCE_DOM.get(g) or max(a_, key=a_.get)
    if dom != 'SHM_Paint' and g not in FORCE_DOM: dom = 'SHM_Paint'
    J_.data.materials.clear(); J_.data.materials.append(SH[dom])
    for p in J_.data.polygons: p.material_index = 0
    J_.name = g; J_.data.name = g + '_mesh'
    bpy.ops.object.select_all(action='DESELECT'); J_.select_set(True); bpy.context.view_layer.objects.active = J_
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    bb = [Vector(c) for c in J_.bound_box]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx = Vector([max(v[i] for v in bb) for i in range(3)])
    piv = (ANCH @ Vector(GN['pivots'][g])) if g in GN['pivots'] else Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, 0.0))
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
kd = bpy.data.objects.get('Kiln_Drum')       # drum axis runs along anchor-local Y (Blender) = glTF Z
if kd: keys(kd, 'kiln_spin', 'rotation_euler', [(i * 30, (0.0, i * math.pi / 2, 0.0)) for i in range(5)], 'LINEAR')
for nm, clip in (('Conveyor_He3', 'conveyor_he3_run'), ('Conveyor_Fuel', 'conveyor_fuel_run')):
    cv = bpy.data.objects.get(nm)
    if cv:
        L0 = Vector(cv.location); dv = R3 @ Vector(GN['conveyors'][nm])
        keys(cv, clip, 'location', ((0, tuple(L0)), (30, tuple(L0 + dv))), 'LINEAR')   # belt moves one cleat pitch per second; loops seamlessly
ig = bpy.data.objects.get('Intake_Grate')
if ig:
    L0 = Vector(ig.location); sh = [Vector((0.03, 0.0, 0.012)), Vector((-0.03, 0.0, -0.008)), Vector((0.025, 0.0, 0.01)), Vector((-0.02, 0.0, -0.006)), Vector((0, 0, 0))]
    keys(ig, 'intake_shake', 'location', [(0, tuple(L0))] + [(3 + 3 * i, tuple(L0 + R3 @ v)) for i, v in enumerate(sh)], 'LINEAR')   # 0.6 s
bl = bpy.data.objects.get('Beacon_Lights')
if bl: keys(bl, 'Beacon_Lights_Blink', 'scale', ((0, (1, 1, 1)), (12, (0.001,) * 3), (36, (0.001,) * 3)), 'CONSTANT')   # 0.4 s on / 0.8 s off
MEX = {'Path_Dump': {'kind': 'truck_pose', 'note': 'HT-04 centre while tipping (rear toward -Z, into RB-1); matches the Mine Path_Dump'},
       'Road_Entry': {'kind': 'road', 'note': 'haul road joins here (Mine dump stub)'},
       'He3_Output': {'kind': 'output', 'product': 'He-3 canisters'}, 'Fuel_Output': {'kind': 'output', 'product': 'LOX + LH2'},
       'Pipe_TankFarm': {'kind': 'pipe_connection', 'lines': ['LOX', 'LH2'], 'note': 'TO TANK FARM header end'}}
for n, p in sorted(GN['markers'].items()):
    old = bpy.data.objects.get(n)
    if old: bpy.data.objects.remove(old, do_unlink=True)
    e = bpy.data.objects.new(n, None); e.empty_display_type = 'ARROWS'; e.empty_display_size = 0.5; e.location = ANCH @ Vector(p); col.objects.link(e); e.parent = root
    for k, v in MEX.get(n, {'kind': 'crew_path'} if n.startswith('Crew_Path') else {}).items(): e[k] = v
print('NODES', sorted(o.name for o in root.children))
print('MARKERS_GL', {n: tuple(round(v, 2) for v in (o.location.x, o.location.z, -o.location.y)) for n, o in [(c.name, c) for c in root.children if c.type == 'EMPTY']})
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_extras=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True, export_optimize_animation_size=False,
                          export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False, export_vertex_color='ACTIVE', export_all_vertex_colors=False)
print('TOTAL_TRIS', sum(tris([o]) for o in nodes))
print('RAW', OUT, os.path.getsize(OUT))
