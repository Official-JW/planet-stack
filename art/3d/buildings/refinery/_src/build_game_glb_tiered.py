"""Refinery game GLB, tiered (adapted from dock_tankfarm/_src/build_game_glb_tiered.py). Own station (Jacob 10/23: Mine, Refinery, Dock).
master .blend -> static base merged by material + named tier / moving-part nodes + empty markers + Cam_Target, in the station frame.
usage: blender -b refinery_master.blend -P build_game_glb_tiered.py -- --out raw.glb [--target 27000] [--tierratio 0.55] [--ct x,y,z --fw W]
then:  gltfpack -i raw.glb -o refinery_game.glb -cc -kn -ke      (meshopt + quantization; keeps named nodes, extras, animations)

Space: GLB origin = Truck_Dump (HT-04 centre while tipping); no rotation; the game camera sits on +Z looking down -Z. RB-1 is at +X of
the origin, the process rows run behind it (-Z), the haul road comes in from the left (-X) edge. --ct/--fw override Cam_Target (Blender
coords) / frame_w; the script prints FIT393 screen boxes (393x852) per node, for the bin + tipping truck and TIERDIST per tier.
Draw budget 13 with every tier showing (station budget <= 30k tris, <= 15 draws):
  Base_Paint (SHM_Paint, all white/graphite/steel/foil/rock/pipe swatches + the RD-1 haul road as COLOR_0), Base_GlowCyan
  (SHM_GlowCyan: cyan strips, He-3 canisters, white lamps), Base_GlowRed (SH_GlowRed: kiln / reactor heat glow + static red lamps) = 3
  + Kiln_Drum, Conveyor_He3, Conveyor_Fuel, Intake_Grate, Beacon_Lights (SH_GlowRed) (5) + Tier_03/05/08/12/20 (5) = 13.
RD-1 road (rd_haul_road, ob['roadcol']): keeps its RoadCol corner colours (Mine road palette) and is never decimated.
Clips: kiln_spin (4 s loop, 1 turn), conveyor_he3_run / conveyor_fuel_run (1 s loop, one cleat pitch), intake_shake (0.5 s),
Beacon_Lights_Blink (1.2 s stepped scale)."""
import bpy, bmesh, json, os, sys, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i][2:]: a[i + 1] for i in range(0, len(a) - 1, 2)}
OUT = A.get('out', '/tmp/rf_game_raw.glb'); TARGET = int(A.get('target', 27000))
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
    if sw == 'SH_GlowRed':   # (material, fold colour): Base keeps SH_GlowRed as its own emissive draw (white vertex colour)
        return SH['SH_GlowRed'], lin(HOT_PAINT.get(next((k for k in HOT_PAINT if m is not None and m.name.startswith(k)), ''), '#e8402a'))
    tm = TARGET_MAT[S2M[sw]]
    return SH[tm], (lin(SW[sw]['base']) if tm == 'SHM_Paint' else [1, 1, 1, 1])

HOT_PAINT = {'RF_HeatGlow': '#ff7a33', 'RF_HeatSoft': '#e8703c', 'RF_RedLamp': '#e8402a'}   # red glow folded into a tier / moving node's SHM_Paint
GN = json.loads(bpy.context.scene['game_nodes'])
# own station (10/23): the GLB frame IS the master's final coords (origin = Truck_Dump, camera on -Y = glTF +Z), no rotation
ANCH = Matrix.Identity(4) if GN.get('station_frame') == 'identity' else Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Translation((-GN.get('anchor_x', 4.84), 0.0, 0.0))
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
    e = ob.evaluated_get(dg); me = bpy.data.meshes.new_from_object(e, preserve_all_data_layers=bool(ob.get('roadcol')), depsgraph=dg)
    if me is None or len(me.polygons) == 0: continue
    M = ANCH @ ob.matrix_world; me.transform(M)
    if M.determinant() < 0: me.flip_normals()
    if len(me.materials) == 0: me.materials.append(None)
    g = ob.get('grp', 'Base')
    sm = [shared_for(m) for m in me.materials]
    if g == 'Base': sm = [((m_, [1, 1, 1, 1]) if m_ == SH['SH_GlowRed'] else (m_, c_)) for m_, c_ in sm]   # kiln / reactor heat + red lamps: real emissive draw
    elif g != 'Beacon_Lights': sm = [((SH['SHM_Paint'], c_) if m_ == SH['SH_GlowRed'] else (m_, c_)) for m_, c_ in sm]
    rc = me.color_attributes.get('RoadCol') if ob.get('roadcol') else None
    rcol = [tuple(d.color) for d in rc.data] if rc else None
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        s = sm[min(poly.material_index, len(sm) - 1)]
        for li in poly.loop_indices: ca.data[li].color = rcol[li] if rcol else s[1]
    if rc: me.color_attributes.remove(me.color_attributes['RoadCol']); sm = [(SH['SHM_Paint'], None) for _ in sm]
    for i, (m_, _) in enumerate(sm): me.materials[i] = m_
    if ob.get('roadcol'): g = 'Road'
    no = bpy.data.objects.new('g_' + ob.name, me); col.objects.link(no); groups.setdefault(g, []).append(no)
TRUCKPTS = []
if 'Stage' in bpy.data.collections:
    for o in bpy.data.collections['Stage'].all_objects:
        if o.type != 'MESH' or o.name.startswith(('Ground', 'pebble', 'boulder', 'slope', 'haul', 'astro', 'rd_')): continue
        c_ = o.matrix_world.translation
        if -7 < c_.x < 7.5 and -3 < c_.y < 3:
            for v in list(o.data.vertices)[::max(1, len(o.data.vertices) // 200)]:
                w_ = o.matrix_world @ v.co
                if -5 < w_.x < 8 and abs(w_.y) < 2.5 and w_.z < 6: TRUCKPTS.append(ANCH @ w_)
print('TRUCK proxy pts', len(TRUCKPTS))
for c in list(bpy.context.scene.collection.children):
    if c != col: bpy.context.scene.collection.children.unlink(c)
def tris(objs): return sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
def area_by_mat(o):
    a = {}
    for p in o.data.polygons:
        m = o.material_slots[p.material_index].material.name; a[m] = a.get(m, 0) + p.area
    return a
ROAD = groups.pop('Road', [])
for g, objs in groups.items():
    for o in objs:
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.004)
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(4), verts=bm.verts, edges=bm.edges, delimit={'MATERIAL'})
        bm.to_mesh(o.data); bm.free()
T1 = {g: tris(o) for g, o in groups.items()}; RTRIS = tris(ROAD); print('TRIS after planar', T1, sum(T1.values()), 'road', RTRIS)
TR = float(A.get('tierratio', 0.55)); MR = float(A.get('movratio', 0.6))
RAT = {g: (MR if g in MOVING else TR) for g in T1 if g != 'Base'}
TS = sum(T1[g] * RAT[g] for g in RAT)
R = min(1.0, (TARGET - RTRIS - TS) / T1['Base'])
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
root['origin'] = 'Truck_Dump (HT-04 centre while tipping into RB-1), on the ground. Own station: place at the Refinery slot (Mine, Refinery, Dock; 160 m apart) with no rotation.'
root['truck_dump'] = ('Truck_Dump at the origin: HT-04 centre while tipping, cab -X, rear +X into RB-1. Route: in from the left edge on the '
                     'inbound lane (glTF z +9), Truck_Path_01..06 forward, r 4.5 m U-turn in front of the intake, stop at Truck_Path_07 heading -X, reverse '
                     '4.0 m straight (~1.5 s) to Truck_Dump, tip, then forward -X along the z 0 lane to Truck_Exit off the left edge.')
root['layout'] = 'own station, camera on +Z: intake bin RB-1 + bucket elevator in front at the right (x 3.7..7.4), process rows behind (-Z), haul road + U-turn in front at the left; process rows at 0.85 scale'
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
        if ROAD:   # RD-1 haul road joins Base_Paint after decimation (keeps its berm profile and tyre ruts)
            pp = [o for o in parts if o.material_slots[o.data.polygons[0].material_index].material.name == 'SHM_Paint']
            tgt = pp[0]
            bpy.ops.object.select_all(action='DESELECT')
            for r_ in ROAD: r_.select_set(True)
            tgt.select_set(True); bpy.context.view_layer.objects.active = tgt; bpy.ops.object.join()
            print('ROAD joined into', tgt.name, 'road tris', RTRIS)
            for o in parts: o.select_set(True)
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
if kd: keys(kd, 'kiln_spin', 'rotation_euler', [(i * 30, ((i * math.pi / 2, 0.0, 0.0) if ANCH == Matrix.Identity(4) else (0.0, i * math.pi / 2, 0.0))) for i in range(5)], 'LINEAR')   # drum axis = Blender X (glTF X)
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
MEX = {'Road_Entry': {'kind': 'road', 'note': 'inbound lane at the left edge (glTF z +9), = Truck_Path_01'},
       'He3_Output': {'kind': 'output', 'product': 'He-3 canisters'}, 'Fuel_Output': {'kind': 'output', 'product': 'LOX + LH2'},
       'Pipe_TankFarm': {'kind': 'pipe_connection', 'lines': ['LOX', 'LH2'], 'note': 'TO TANK FARM header end'}}
for n, p in sorted(GN['markers'].items()):
    old = bpy.data.objects.get(n)
    if old: bpy.data.objects.remove(old, do_unlink=True)
    e = bpy.data.objects.new(n, None); e.empty_display_type = 'ARROWS'; e.empty_display_size = 0.5; e.location = ANCH @ Vector(p); col.objects.link(e); e.parent = root
    for k, v in (GN.get('marker_extras', {}).get(n) or MEX.get(n, {'kind': 'crew_path'} if n.startswith('Crew_Path') else {})).items(): e[k] = v
CT = GN.get('cam_target')
if CT:
    ctp = Vector([float(v) for v in A['ct'].split(',')]) if A.get('ct') else Vector(CT['pos']); FW = float(A.get('fw', CT['frame_w']))
    VT = math.tan(math.radians(19)); E = math.radians(18)
    ce = bpy.data.objects.new('Cam_Target', None); ce.empty_display_type = 'SPHERE'; ce.empty_display_size = 0.5; ce.location = ANCH @ ctp; col.objects.link(ce); ce.parent = root
    ce['frame_w'] = FW; ce['fov_y_deg'] = 38; ce['pitch_down_deg'] = 18; ce['distance_m_393x852'] = round(FW / (2 * VT * 393 / 852), 2)
    ce['note'] = 'station camera look-at (empty, no draws): camera looks down glTF -Z from +Z, 18 deg down, 38 deg vFOV, d = (frame_w/2)/(tan 19 deg * aspect)'
    def proj(pw, w=393, h=852):
        d = FW / (2 * VT * w / h); pos = ctp + Vector((0, -d * math.cos(E), d * math.sin(E))); f = Vector((0, math.cos(E), -math.sin(E))); u = Vector((0, math.sin(E), math.cos(E)))
        v = pw - pos; z = v.dot(f); k = (h / 2) / VT
        return (w / 2 + k * v.x / z, h / 2 - k * v.dot(u) / z)
    def sbox(pts):
        s_ = [proj(p) for p in pts]; return (min(a for a, _ in s_), max(a for a, _ in s_), min(b for _, b in s_), max(b for _, b in s_))
    FIT = {}
    for o in nodes:
        FIT[o.name] = sbox([o.matrix_world @ v.co for v in o.data.vertices])
    allp = [o.matrix_world @ v.co for o in nodes for v in o.data.vertices]
    FIT['ALL'] = sbox(allp)
    FIT['ALL_no_road'] = sbox([p for p in allp if not (p.x < -9.5 and p.y < 3.0 and p.z < 0.4)])
    binp = [p for o in nodes if o.name.startswith('Base') for p in [o.matrix_world @ v.co for v in o.data.vertices] if 3.3 < p.x < 7.8 and -2.6 < p.y < 2.6]
    if TRUCKPTS: FIT['TRUCK_dump_pose'] = sbox(TRUCKPTS)
    FIT['BIN_RB1'] = sbox(binp); FIT['BIN_plus_TRUCK'] = sbox(binp + TRUCKPTS)
    for k_, b_ in FIT.items(): print('FIT393 %-16s x %6.1f..%6.1f  y %6.1f..%6.1f  cy %.1f' % (k_, b_[0], b_[1], b_[2], b_[3], (b_[2] + b_[3]) / 2))
    for o in nodes:
        if o.name in TIERS:
            c_ = Vector(o.location); print('TIERDIST %s pivot flat %.1f m, farthest vertex flat %.1f m (frame_w %.0f)' % (o.name, math.hypot(c_.x - ctp.x, c_.y - ctp.y),
                  max(math.hypot((o.matrix_world @ v.co).x - ctp.x, (o.matrix_world @ v.co).y - ctp.y) for v in o.data.vertices), FW))
    print('CAM_TARGET glTF (%.2f, %.2f, %.2f) frame_w %.1f d %.2f' % (ctp.x, ctp.z, -ctp.y, FW, ce['distance_m_393x852']))
print('NODES', sorted(o.name for o in root.children))
print('MARKERS_GL', {n: tuple(round(v, 2) for v in (o.location.x, o.location.z, -o.location.y)) for n, o in [(c.name, c) for c in root.children if c.type == 'EMPTY']})
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_extras=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True, export_optimize_animation_size=False,
                          export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False, export_vertex_color='ACTIVE', export_all_vertex_colors=False)
print('TOTAL_TRIS', sum(tris([o]) for o in nodes))
print('RAW', OUT, os.path.getsize(OUT))
