"""Mine Lv10 concept stills (10/24/2026). Concept art only: nothing here is a game asset; the game GLB is untouched.
Builds on the CURRENT game Mine (mine_game.glb ef45f6f1, unpacked with gltfpack -noq; Blender has no meshopt decoder) + the HT-04 prop,
then adds the Lv10 kit for --variant A or B (--variant current = the current Mine, same lights/ground/camera, for comparison).
  $B -b -P lv10_concept.py -t 4 -- --mine mine_plain.glb --truck ht04_plain.glb --variant A|B|current --out DIR
        [--shots game,hero,mask] [--samples 96] [--frame 1]
game : 393x852 from the station camera exactly as qa3d-next frames the Mine (Cam_Target x/z, CAM_OVERRIDE y 5.6, frame_w 39.9, 38 deg vFOV, 18 deg down)
hero : 1920x1080 close-up, same 3/4 hero camera for current / A / B
mask : 393x852 unlit mask of everything standing > 0.45 m above the ground (buildings; ground, road, ruts and deposits drop out) for the 5 px edge check
Ground: flat grey lunar plane (same 0.16 grey as _src/proof_phone.py) with the pits cut in by booleans. Cycles CPU + OIDN, AgX, motion blur on spinning / moving parts."""
import bpy, sys, math, os, bmesh
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i].lstrip('-'): a[i + 1] for i in range(0, len(a) - 1, 2)}
SIZES = [tuple(int(x) for x in z.split('x')) for z in A.get('sizes', '393x852').split(',')]
V = A.get('variant', 'A'); OUT = A['out']; os.makedirs(OUT, exist_ok=True); SH = A.get('shots', 'game,hero').split(',')
FONT = '/usr/share/fonts/truetype/sand-box/google/Chakra Petch/ChakraPetch-Bold.ttf'
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; F0 = int(A.get('frame', 1)); sc.frame_set(F0)
# ---------------------------------------------------------------- current Mine + HT-04 (as proof_phone.py)
bpy.ops.import_scene.gltf(filepath=A['mine'])
def stop_anim():
    for o in bpy.data.objects:
        if o.animation_data:
            o.animation_data.action = None
            for t in o.animation_data.nla_tracks: t.mute = True
stop_anim()
for o in list(bpy.data.objects):
    if o.get('hidden_by_default') or o.name.startswith('Tier_'): o.hide_render = True
bpy.ops.import_scene.gltf(filepath=A['truck']); bpy.context.view_layer.update(); stop_anim()
tr = bpy.data.objects['Truck']; tr.matrix_world = bpy.data.objects['Path_Load'].matrix_world.copy()
tm = next((o for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys and 'fill' in o.data.shape_keys.key_blocks), None)
if tm: tm.data.shape_keys.key_blocks['fill'].value = 1.0
for pb in tr.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
for m in bpy.data.materials:                       # glTF COLOR_0 multiplies base colour (only where the mesh has vertex colours)
    if not m.use_nodes: continue
    nt = m.node_tree; bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs is None or bs.inputs['Base Color'].is_linked: continue
    if not any(o.data.color_attributes for o in bpy.data.objects if o.type == 'MESH' and m.name in [x.name for x in o.data.materials if x]): continue
    ca = nt.nodes.new('ShaderNodeVertexColor'); mix = nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1
    mix.inputs[1].default_value = bs.inputs['Base Color'].default_value; nt.links.new(ca.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], bs.inputs['Base Color'])
    if bs.inputs['Emission Strength'].default_value > 0 and not bs.inputs['Emission Color'].is_linked: nt.links.new(mix.outputs[0], bs.inputs['Emission Color'])
GAME_OBJS = [o for o in bpy.data.objects]
# ---------------------------------------------------------------- materials (Mine-B palette: white paint, graphite, cyan; weathered)
def mat(name, col, rough=0.5, metal=0.0, emit=None, es=0.0, dirt=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (*col, 1); bs.inputs['Roughness'].default_value = rough; bs.inputs['Metallic'].default_value = metal
    if emit: bs.inputs['Emission Color'].default_value = (*emit, 1); bs.inputs['Emission Strength'].default_value = es
    if dirt > 0:   # weathering: regolith dust that builds up toward the ground + mottled grime
        tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
        geo = nt.nodes.new('ShaderNodeNewGeometry'); sz = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Position'], sz.inputs[0])
        ramp = nt.nodes.new('ShaderNodeMapRange'); ramp.inputs['From Min'].default_value = 0.0; ramp.inputs['From Max'].default_value = 2.2
        ramp.inputs['To Min'].default_value = dirt; ramp.inputs['To Max'].default_value = 0.0; nt.links.new(sz.outputs['Z'], ramp.inputs['Value'])
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 8
        nt.links.new(geo.outputs['Position'], nz.inputs['Vector'])
        mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = dirt * 0.55; nt.links.new(nz.outputs['Fac'], mul.inputs[0])
        add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'; add.use_clamp = True; nt.links.new(ramp.outputs[0], add.inputs[0]); nt.links.new(mul.outputs[0], add.inputs[1])
        mx = nt.nodes.new('ShaderNodeMixRGB'); mx.inputs['Color1'].default_value = (*col, 1); mx.inputs['Color2'].default_value = (0.20, 0.19, 0.18, 1)
        nt.links.new(add.outputs[0], mx.inputs['Fac']); nt.links.new(mx.outputs[0], bs.inputs['Base Color'])
    return m
M = dict(
    white=mat('LV_White', (0.72, 0.73, 0.74), 0.42, dirt=0.35), white2=mat('LV_WhitePanel', (0.62, 0.63, 0.65), 0.5, dirt=0.3),
    graphite=mat('LV_Graphite', (0.035, 0.038, 0.045), 0.5, 0.3, dirt=0.15), steel=mat('LV_Steel', (0.25, 0.26, 0.28), 0.38, 0.85, dirt=0.2),
    cyan=mat('LV_Cyan', (0.02, 0.6, 0.8), 0.3, emit=(0.0284, 0.7681, 1.0), es=8.0), cyan_soft=mat('LV_CyanSoft', (0.02, 0.5, 0.7), 0.3, emit=(0.0284, 0.7681, 1.0), es=3.0),
    amber=mat('LV_Amber', (0.9, 0.45, 0.05), 0.4, emit=(1.0, 0.42, 0.05), es=6.0), red=mat('LV_Beacon', (0.8, 0.05, 0.03), 0.4, emit=(1.0, 0.05, 0.02), es=25.0),
    sign=mat('LV_SignFace', (0.9, 0.97, 1.0), 0.3, emit=(0.75, 0.95, 1.0), es=6.0), signback=mat('LV_SignPanel', (0.02, 0.025, 0.03), 0.6, 0.2),
    hazard=mat('LV_Hazard', (0.85, 0.55, 0.05), 0.55, dirt=0.25), ore=mat('LV_Ore', (0.19, 0.185, 0.178), 0.92), orerich=mat('LV_OreRich', (0.03, 0.4, 0.5), 0.6, emit=(0.0284, 0.6, 0.85), es=1.4),
    pitwall=mat('LV_PitWall', (0.125, 0.125, 0.13), 0.95), cable=mat('LV_Cable', (0.02, 0.02, 0.02), 0.6, 0.6), glass=mat('LV_Glass', (0.02, 0.05, 0.08), 0.08, 0.2, emit=(0.4, 0.75, 1.0), es=0.6),
    flood=mat('LV_Flood', (1, 1, 1), 0.2, emit=(1.0, 0.96, 0.9), es=30.0))
# hazard stripes
def stripes(m, scale=6.0):
    nt = m.node_tree; bs = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord'); w = nt.nodes.new('ShaderNodeTexWave'); w.inputs['Scale'].default_value = scale
    w.wave_profile = 'SAW'; w.bands_direction = 'DIAGONAL'; nt.links.new(tc.outputs['Object'], w.inputs['Vector'])
    st = nt.nodes.new('ShaderNodeMath'); st.operation = 'GREATER_THAN'; st.inputs[1].default_value = 0.5; nt.links.new(w.outputs['Fac'], st.inputs[0])
    mx = nt.nodes.new('ShaderNodeMixRGB'); mx.inputs['Color1'].default_value = (0.85, 0.55, 0.05, 1); mx.inputs['Color2'].default_value = (0.03, 0.03, 0.035, 1)
    nt.links.new(st.outputs[0], mx.inputs['Fac']); nt.links.new(mx.outputs[0], bs.inputs['Base Color'])
stripes(M['hazard'])
NEW = []
def _fin(o, m):
    if m: o.data.materials.append(m)
    NEW.append(o); return o
def box(loc, size, m, rot=(0, 0, 0), bev=0.0, name='lv_box'):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bev > 0: b = o.modifiers.new('b', 'BEVEL'); b.width = bev; b.segments = 2; b.limit_method = 'ANGLE'
    return _fin(o, m)
def cyl(loc, r, h, m, rot=(0, 0, 0), v=32, name='lv_cyl', r2=None):
    if r2 is None: bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=h, location=loc, rotation=rot)
    else: bpy.ops.mesh.primitive_cone_add(vertices=v, radius1=r, radius2=r2, depth=h, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; bpy.ops.object.shade_smooth(); return _fin(o, m)
def sph(loc, r, m, name='lv_sph', sc_=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=24, ring_count=12); o = bpy.context.active_object; o.scale = sc_; o.name = name
    bpy.ops.object.shade_smooth(); return _fin(o, m)
def beam(p, q, r, m, v=8, name='lv_beam'):
    p, q = Vector(p), Vector(q); d = q - p; L = d.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=L, location=(p + q) / 2); o = bpy.context.active_object; o.name = name
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y'); return _fin(o, m)
def sqbeam(p, q, w, m, name='lv_sq'):
    p, q = Vector(p), Vector(q); d = q - p; L = d.length
    bpy.ops.mesh.primitive_cube_add(size=1, location=(p + q) / 2); o = bpy.context.active_object; o.name = name; o.scale = (w, w, L)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y'); return _fin(o, m)
def text(s, loc, size, m, rot=(math.radians(90), 0, 0), ext=0.06, align='CENTER', name='lv_text', back=None):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = s; cu.font = bpy.data.fonts.load(FONT); cu.size = size; cu.extrude = ext
    cu.align_x = align; cu.align_y = 'CENTER'; o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = rot
    return _fin(o, m)
def lattice_tower(cx, cy, w0, w1, h, levels, m_leg, m_br, leg_r=0.22, br_r=0.08):
    """4-leg tapering lattice (legs + X bracing per level, rings) centred at cx, cy from z 0 to h, base half-width w0 -> top w1"""
    def c(k, z):
        t = z / h; hw = w0 + (w1 - w0) * t; sx, sy = [(-1, -1), (1, -1), (1, 1), (-1, 1)][k]; return Vector((cx + sx * hw, cy + sy * hw, z))
    for k in range(4): beam(c(k, 0), c(k, h), leg_r, m_leg, name='lv_leg')
    zs = [h * i / levels for i in range(levels + 1)]
    for i in range(levels):
        for k in range(4):
            k2 = (k + 1) % 4; beam(c(k, zs[i]), c(k2, zs[i + 1]), br_r, m_br); beam(c(k2, zs[i]), c(k, zs[i + 1]), br_r, m_br)
            beam(c(k, zs[i + 1]), c(k2, zs[i + 1]), br_r * 1.2, m_br)
def spin(o, axis, rate_deg_per_frame):   # motion cue: keyed rotation, rendered with motion blur
    o.rotation_mode = 'XYZ'; i = 'XYZ'.index(axis); r0 = o.rotation_euler[i]
    for f in (F0 - 1, F0 + 1):
        o.rotation_euler[i] = r0 + math.radians(rate_deg_per_frame) * (f - F0); o.keyframe_insert('rotation_euler', index=i, frame=f)
    for fc in o.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
def slide(o, d, frames=1.0):
    p0 = Vector(o.location)
    for f in (F0 - 1, F0 + 1): o.location = p0 + Vector(d) * (f - F0); o.keyframe_insert('location', frame=f)
    for fc in o.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
def wheel(loc, r, axis_rot, m_rim, m_spoke, m_glow, spokes=6, rate=30, w=0.35):
    em = bpy.data.objects.new('lv_wheel', None); sc.collection.objects.link(em); em.location = loc; em.rotation_euler = axis_rot
    parts = [cyl((0, 0, 0), r, w, m_rim, v=48), cyl((0, 0, 0), r * 0.92, w * 1.15, m_glow, v=48), cyl((0, 0, 0), r * 0.86, w * 1.3, m_rim, v=48), cyl((0, 0, 0), r * 0.18, w * 1.6, m_spoke, v=24)]
    for k in range(spokes):
        a_ = 2 * math.pi * k / spokes; parts.append(sqbeam((0, 0, 0), (r * 0.86 * math.cos(a_), r * 0.86 * math.sin(a_), 0), 0.12, m_spoke))
    for p in parts: p.parent = em
    # carve the glow ring into a rim band: a thin cyan tyre between the white rim and the inner face
    spin(em, 'Z', rate); return em
def conveyor(p, q, wdt, m_frame, m_belt, m_glow, legs=True, lumps=True, name='lv_conv'):
    p, q = Vector(p), Vector(q); d = q - p; L = d.length; n = d.normalized()
    side = n.cross(Vector((0, 0, 1))).normalized() if abs(n.z) < 0.99 else Vector((1, 0, 0))
    o = sqbeam(p, q, 1, m_frame, name=name); o.scale = (wdt, 0.5, L)   # (local x,y,z) -> width, depth, length
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    # belt top + glow rails
    up = (n.cross(side)).normalized();  up = up if up.z > 0 else -up
    belt = sqbeam(p + up * 0.27, q + up * 0.27, 1, m_belt); belt.scale = (wdt * 0.8, 0.06, L); belt.rotation_quaternion = d.to_track_quat('Z', 'Y')
    for s in (-1, 1):
        sqbeam(p + side * s * wdt * 0.5 + up * 0.3, q + side * s * wdt * 0.5 + up * 0.3, 0.07, m_glow)
    if legs:
        k = max(2, int(L / 5))
        for i in range(1, k):
            x = p + d * i / k
            if x.z > 0.8:
                for s in (-1, 1): beam(x + side * s * wdt * 0.4, Vector((x.x, x.y, 0)) + side * s * wdt * 0.5, 0.09, m_frame)
    if lumps:   # ore riding the belt (blurred = moving)
        k = int(L / 0.9)
        for i in range(k):
            x = p + d * (i + 0.5) / k + up * 0.42 + side * (((i * 37) % 7) / 7 - 0.5) * wdt * 0.4
            s_ = sph(x, 0.16 + 0.06 * ((i * 13) % 5) / 5, M['ore'] if i % 5 else M['orerich'], sc_=(1.2, 1.0, 0.7)); slide(s_, n * 0.35)
    # chevrons: moving lit arrows on the side skirt
    k = int(L / 2.2)
    for i in range(k):
        x = p + d * (i + 0.5) / k - up * 0.1 + side * wdt * 0.52
        c_ = box(x, (0.05, 0.5, 0.18), M['cyan']); c_.rotation_mode = 'QUATERNION'; c_.rotation_quaternion = d.to_track_quat('Y', 'Z'); slide(c_, n * 0.5)
    return o
# ---------------------------------------------------------------- ground + pits
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, -0.03)); G = bpy.context.active_object; G.name = 'Ground'
gm = mat('Reg', (0.16, 0.16, 0.165), 0.95); G.data.materials.append(gm)
CUT = []
def pit_terraced(cx, cy, rs, step, name='pit', sx=1.0, wall=0.7, floor_m=None):
    """open pit dug into the surface: lathed bench profile (rim -> sloped wall -> bench -> ... -> floor), a regolith berm round the rim,
    and a hole of the outer radius cut in the ground plane (boolean). rs = bench radii outer->inner, step = bench height"""
    prof = []; z = 0.0
    for i, r in enumerate(rs):
        prof.append((r, z)); z -= step; prof.append((max(r - wall, 0.2), z))
    prof.append((0.0, z))
    bm = bmesh.new(); vs = [bm.verts.new((r, 0, zz - 0.03)) for r, zz in prof]
    for i in range(len(vs) - 1): bm.edges.new((vs[i], vs[i + 1]))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), angle=math.radians(360), steps=64, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.location = (cx, cy, 0); o.scale = (sx, 1, 1); me.materials.append(M['pitwall']); NEW.append(o)
    for pg in me.polygons: pg.use_smooth = False
    bpy.ops.mesh.primitive_torus_add(major_radius=rs[0] + 0.55, minor_radius=0.55, location=(cx, cy, -0.18), major_segments=64, minor_segments=8)
    b = bpy.context.active_object; b.scale = (sx * (rs[0] + 0.55) / (rs[0] + 0.55), 1, 0.45); b.scale.x = sx; b.data.materials.append(gm); NEW.append(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=rs[0] - 0.01, depth=2.0, location=(cx, cy, -0.03)); c = bpy.context.active_object; c.scale.x = sx
    c.name = '%s_cut' % name; CUT.append(c)
    if floor_m: cyl((cx, cy, z - 0.01), max(rs[-1] - wall - 0.3, 0.3), 0.06, floor_m, v=48).scale.x = sx
    return z
def cut_ground():
    for c in CUT:
        md = G.modifiers.new(c.name, 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = c; md.solver = 'EXACT'; md.use_self = False
        c.hide_render = True; c.display_type = 'WIRE'
def rim_lights(cx, cy, r, n, m, z=0.12, sx=1.0, size=0.18):
    for i in range(n):
        a_ = 2 * math.pi * i / n; box((cx + r * sx * math.cos(a_), cy + r * math.sin(a_), z), (size, size, 0.16), m)
def floodlight(loc, target, energy=2500, spot=55, col=(1.0, 0.96, 0.9)):
    ld = bpy.data.lights.new('lv_flood', 'SPOT'); ld.energy = energy; ld.spot_size = math.radians(spot); ld.spot_blend = 0.6; ld.color = col; ld.shadow_soft_size = 0.3
    o = bpy.data.objects.new('lv_flood', ld); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); NEW.append(o)
    box(loc, (0.5, 0.5, 0.3), M['flood'])
def ptlight(loc, col, energy=150, r=0.2):
    ld = bpy.data.lights.new('lv_pt', 'POINT'); ld.energy = energy; ld.color = col; ld.shadow_soft_size = r
    o = bpy.data.objects.new('lv_pt', ld); sc.collection.objects.link(o); o.location = loc; NEW.append(o)
def beacon(loc, r=0.22):
    sph(loc, r, M['red']); ptlight(loc, (1, 0.08, 0.04), 60)
def sign_panel(s, loc, w, h, size, rot_z=0.0, sub=None, mast=None):
    """lit sign: graphite panel, cyan frame, emissive white letters (original name, no real logos)"""
    em = bpy.data.objects.new('lv_sign', None); sc.collection.objects.link(em); em.location = loc; em.rotation_euler = (0, 0, rot_z)
    ps = [box((0, 0, 0), (w, 0.3, h), M['signback'], bev=0.04), box((0, -0.16, h / 2 - 0.08), (w, 0.06, 0.12), M['cyan']), box((0, -0.16, -h / 2 + 0.08), (w, 0.06, 0.12), M['cyan'])]
    ps.append(text(s, (0, -0.2, (0.14 * h if sub else 0)), size, M['sign'], ext=0.03))
    if sub: ps.append(text(sub, (0, -0.2, -0.28 * h), size * 0.42, M['cyan'], ext=0.02))
    for p in ps: p.parent = em
    ptlight(em.matrix_world @ Vector((0, -2.0, 0)), (0.6, 0.9, 1.0), 400 * w / 6, 1.0)
    return em
# ---------------------------------------------------------------- Lv10 kits
def common_lv10():
    """both concepts: lit approach on the haul road, deposits kept, extra cyan trim on the existing plant"""
    for x in (13.5, 16.0):                      # road edge marker posts (outbound lane y -9, return lane y 0)
        for y in (-11.3, -6.7):
            box((x, y, 0.45), (0.14, 0.14, 0.9), M['graphite']); box((x, y, 0.95), (0.16, 0.16, 0.18), M['cyan'] if y > -9 else M['amber'])
def concept_A():
    # 1) Deep shaft headframe (back, centre): 34 m tapering lattice straddling a dug shaft, twin sheave wheels, lit vertical sign
    cx, cy = 1.5, 15.0
    pit_terraced(cx, cy, [3.4], 4.0, 'shaft', wall=0.15, floor_m=M['cyan_soft'])
    rim_lights(cx, cy, 4.6, 18, M['cyan'])
    
    lattice_tower(cx, cy, 3.2, 1.6, 30.0, 8, M['white'], M['steel'], leg_r=0.32, br_r=0.1)
    box((cx, cy, 30.6), (4.6, 4.6, 1.2), M['white'], bev=0.08); box((cx, cy, 31.3), (4.8, 4.8, 0.14), M['cyan'])
    box((cx, cy, 32.6), (5.4, 3.0, 2.4), M['graphite'], bev=0.1)                           # winder house on top
    for s in (-1, 1): wheel((cx + s * 1.75, cy - 2.6, 33.4), 1.55, (math.radians(90), 0, math.radians(s * 38)), M['white'], M['steel'], M['cyan'], rate=40)
    for s in (-1, 1): beam((cx + s * 1.75, cy - 2.6, 31.85), (cx + s * 0.6, cy, -2.0), 0.05, M['cable'])
    for s in (-1, 1): beam((cx + s * 1.6, cy + 1.6, 30.0), (cx + s * 3.0, cy + 14.0, 0.0), 0.3, M['white'])   # backstays
    for z in (8, 16, 24): beam((cx - 3.0 + 1.4 * z / 30, cy + 14.0 - 12.4 * z / 30, z), (cx + 3.0 - 1.4 * z / 30, cy + 14.0 - 12.4 * z / 30, z), 0.1, M['steel'])
    beam((cx, cy, 34.0), (cx, cy, 36.4), 0.08, M['steel']); beacon((cx, cy, 36.6), 0.3);
    for k, (sx_, sy_) in enumerate([(-1, -1), (1, -1)]):   # A identity: cyan light strips up the front legs
        beam((cx + sx_ * 3.2, cy + sy_ * 3.2 - 0.36, 0.3), (cx + sx_ * 1.6, cy + sy_ * 1.6 - 0.36, 29.6), 0.07, M['cyan'])
    beacon((cx + 2.3, cy - 2.3, 31.6)); beacon((cx - 2.3, cy - 2.3, 31.6))
    for z in (8, 15, 22): box((cx, cy - 3.1 + z * 0.053, z), (5.2 - z * 0.1, 0.12, 0.12), M['cyan'])
    sign_panel('TYCHO', (cx, cy - 4.6, 19.0), 8.0, 3.4, 2.6, sub='DEEPWORKS  ·  SHAFT 10')
    # skip cage mid-hoist (moving: blurred)
    cg = box((cx, cy - 0.2, 12.0), (1.4, 1.4, 2.2), M['white2'], bev=0.05); slide(cg, (0, 0, 0.6)); box((cx, cy - 0.95, 12.0), (1.0, 0.05, 1.4), M['glass'])
    # 2) Second pit: terraced open pit, front-left, with a haul ramp and a short incline conveyor into the existing hoppers
    px, py = -11.0, -10.5
    pit_terraced(px, py, [5.2, 3.9, 2.6], 1.0, 'pit2', sx=1.15)
    rim_lights(px, py, 6.0, 22, M['cyan'], sx=1.15); rim_lights(px, py, 3.85, 14, M['amber'], z=-0.92, sx=1.15, size=0.12)
    box((px + 0.0, py - 0.2, -2.75), (2.4, 1.2, 0.5), M['orerich'])                        # exposed He-3 seam at the bottom
    conveyor((px + 2.5, py + 1.5, -1.6), (-1.0, -3.0, 5.2), 1.0, M['graphite'], M['steel'], M['cyan'])
    box((-1.0, -3.0, 5.4), (1.8, 1.8, 1.0), M['white'], bev=0.06)
    # pit-side digger mast (small rig dropping into the pit)
    lattice_tower(px - 4.8, py + 3.4, 0.9, 0.5, 9.0, 4, M['white'], M['steel'], leg_r=0.12, br_r=0.05)
    box((px - 4.8, py + 3.4, 9.3), (1.6, 1.6, 0.6), M['graphite']); beacon((px - 4.8, py + 3.4, 9.8)); beam((px - 4.8, py + 3.4, 9.0), (px - 2.0, py + 1.0, -2.0), 0.08, M['steel'])
    # 3) Ore bay: three walled bays with ore piles on the right, behind the return lane
    for i in range(4): box((15.0 + i * 2.2, 6.0, 1.0), (0.3, 4.0, 2.0), M['white2'], bev=0.04)
    for i in range(3):
        sph((16.1 + i * 2.2, 6.1, 0.0), 1.0, M['ore'] if i != 1 else M['orerich'], sc_=(0.95, 1.7, 1.25))
        box((16.1 + i * 2.2, 3.95, 2.1), (1.6, 0.1, 0.12), M['amber'])
    box((18.3, 8.15, 1.2), (7.0, 0.3, 2.4), M['graphite'])
    text('BAY 1   BAY 2   BAY 3', (18.3, 3.8, 2.45), 0.36, M['sign'], ext=0.01)
    conveyor((9.0, 5.0, 6.2), (16.1, 6.1, 3.6), 0.9, M['graphite'], M['steel'], M['cyan'])
    # floodlights for glow pools
    floodlight((-6.0, -15.0, 6.0), (px, py, -2)); floodlight((8.0, -15.5, 7.0), (cx, cy, 8), 3000, 30); floodlight((20.0, -2.0, 6.0), (18, 6, 0), 1500, 60)
    common_lv10()
def concept_B():
    # 1) Twin rig: second drill derrick on the right (slim mast, drill string spinning) over its own pit
    rx, ry = 16.5, 11.0
    pit_terraced(rx, ry, [2.6, 1.8], 1.5, 'rig2pit', floor_m=M['cyan_soft'])
    rim_lights(rx, ry, 3.4, 14, M['cyan'])
    lattice_tower(rx, ry, 1.8, 0.7, 26.0, 7, M['white'], M['steel'], leg_r=0.24, br_r=0.08)
    box((rx, ry, 26.5), (2.4, 2.4, 1.0), M['graphite'], bev=0.06); beacon((rx, ry, 27.4), 0.28)
    ds = cyl((rx, ry, 9.0), 0.28, 18.0, M['steel'], v=16)
    for z in (2, 6, 10, 14): box((rx, ry, z), (0.7, 0.7, 0.25), M['amber'], name='lv_collar')
    td = cyl((rx, ry, 18.5), 1.1, 1.6, M['white'], v=24); spin(td, 'Z', 45); tb = box((1.0, 0, 0), (0.4, 0.6, 1.0), M['hazard'], name='lv_td_tab'); tb.parent = td
    for z in (9, 18): box((rx, ry - 1.45 + z * 0.042, z), (3.4 - z * 0.06, 0.1, 0.12), M['cyan'])
    # 2) Gantry: a lit portal frame spanning both haul lanes, carrying the long ore conveyor from rig 2 to the hoppers + the billboard
    gx = 14.0
    for y in (-12.6, 3.2):
        for x in (gx - 1.4, gx + 1.4): sqbeam((x, y, 0), (x, y, 9.2), 0.45, M['white'])
        box((gx, y, 0.3), (3.6, 1.2, 0.6), M['hazard'])
    box((gx, -4.7, 9.6), (3.6, 16.4, 0.8), M['graphite'], bev=0.05); box((gx, -4.7, 10.05), (3.7, 16.5, 0.1), M['cyan'])
    for y in (-11, -7, -2.4, 1.6): box((gx, y, 9.1), (0.8, 0.3, 0.2), M['flood'])
    sign_panel('ARGENT SEAM', (gx - 0.6, -12.9, 13.4), 8.6, 2.9, 1.65, sub='He-3 WORKS  ·  LEVEL 10')
    for x in (gx - 4.0, gx + 2.8): sqbeam((x, -12.9, 10.0), (x, -12.9, 11.95), 0.3, M['white'])
    conveyor((rx, ry - 2.0, 3.5), (gx, 3.2, 10.6), 1.0, M['graphite'], M['steel'], M['cyan'], legs=False)
    conveyor((gx - 0.6, 2.5, 10.6), (8.0, 1.0, 7.0), 1.0, M['graphite'], M['steel'], M['cyan'], legs=False)
    # 3) Covered ore bay (left-front): open-front shed, 3 glowing rich-ore piles, roof light bar, small loader
    bx, by = -13.0, -5.5
    box((bx, by + 2.5, 2.2), (8.4, 0.3, 4.4), M['white2'], bev=0.04)
    for x in (bx - 4.1, bx + 4.1): box((x, by, 2.2), (0.3, 5.0, 4.4), M['white2'], bev=0.04)
    rf = box((bx, by - 0.3, 4.6), (9.2, 6.0, 0.35), M['white'], bev=0.06); rf.rotation_euler = (math.radians(-6), 0, 0)
    box((bx, by - 3.2, 4.25), (9.0, 0.2, 0.2), M['cyan'])
    for i, x in enumerate((bx - 2.7, bx, bx + 2.7)):
        sph((x, by + 0.6, 0.0), 1.15, M['orerich'] if i == 1 else M['ore'], sc_=(1.0, 1.4, 1.2)); box((x, by + 2.3, 3.4), (1.6, 0.1, 0.5), M['amber'])
    text('ORE BAY', (bx, by + 2.3, 3.95), 0.55, M['sign'], ext=0.01)
    # 4) Second pit: wide shallow pit with a spiral bench, front-left of the bay, small excavator arm on the rim
    px, py = -9.5, -13.2
    pit_terraced(px, py, [4.4, 3.2, 2.0], 0.8, 'pit2', sx=1.35)
    rim_lights(px, py, 5.2, 20, M['amber'], sx=1.35)
    box((px + 0.6, py, -2.3), (2.0, 1.2, 0.3), M['orerich'])
    ex = box((px + 6.6, py + 1.6, 0.7), (2.4, 2.0, 1.2), M['white'], bev=0.08); box((px + 6.6, py + 0.55, 1.0), (1.2, 0.05, 0.6), M['glass'])
    beam((px + 6.0, py + 1.0, 1.3), (px + 3.6, py + 0.4, 3.4), 0.18, M['hazard']); beam((px + 3.6, py + 0.4, 3.4), (px + 2.2, py, -0.8), 0.15, M['hazard'])
    # 5) comms mast + dish, extra tank pair, beacons
    lattice_tower(-17.0, 10.0, 0.6, 0.3, 14.0, 5, M['white'], M['steel'], leg_r=0.1, br_r=0.04)
    dsh = sph((-17.0, 9.2, 14.6), 1.6, M['white'], sc_=(1, 0.35, 1)); dsh.rotation_euler = (math.radians(-25), 0, 0); beacon((-17.0, 10.0, 15.9))
    for i, x in enumerate((-3.0, 0.2)):
        cyl((x, 12.5, 4.0), 1.5, 8.0, M['white'], v=40); sph((x, 12.5, 8.0), 1.5, M['white'], sc_=(1, 1, 0.45)); cyl((x, 12.5, 6.6), 1.53, 0.18, M['cyan'], v=40)
    floodlight((-9.0, -18.0, 6.0), (bx, by, 1), 2500, 50); floodlight((18.0, -16.0, 7.0), (gx, -5, 9), 2500, 40); floodlight((18.5, 2.0, 6.0), (rx, ry, 4), 2000, 50)
    common_lv10()
if V == 'A': concept_A()
elif V == 'B': concept_B()
cut_ground()
# ---------------------------------------------------------------- lights / world / render (Cycles CPU, OIDN, AgX)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.03, 0.035, 0.045, 1)
sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 4.0; sd.angle = math.radians(3); s_ = bpy.data.objects.new('Sun', sd); sc.collection.objects.link(s_)
s_.rotation_euler = (math.radians(50), math.radians(-25), math.radians(35))
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(A.get('samples', 96)); sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
sc.cycles.use_auto_tile = False; sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.8
sc.render.film_transparent = False
ct = bpy.data.objects['Cam_Target']; FOV = ct['fov_y_deg']; P = math.radians(ct['pitch_down_deg']); T = ct.matrix_world.translation.copy()
W_ = 39.9; T.z = 5.6                                  # qa3d-next CAM_OVERRIDE ef45f6f1: Cam_Target y 5.6, frame_w 39.9
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam; cd.clip_end = 3000
def shoot_game(path, rx=393, ry=852):
    cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(FOV)
    D = (W_ / 2) / (math.tan(math.radians(FOV / 2)) * rx / ry)
    cam.location = T + Vector((0, -D * math.cos(P), D * math.sin(P))); cam.rotation_euler = (T - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = rx, ry; sc.render.resolution_percentage = 100; sc.render.filepath = path
    bpy.ops.render.render(write_still=True); print('WROTE', path)
def shoot_hero(path):
    cd.sensor_fit = 'HORIZONTAL'; cd.lens = float(A.get('lens', 26)); cd.sensor_width = 36
    loc = Vector([float(x) for x in A.get('hero_loc', '-32,-50,20').split(',')]); tg = Vector([float(x) for x in A.get('hero_tgt', '4,3,15.5').split(',')])
    cam.location = loc; cam.rotation_euler = (tg - loc).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080; sc.render.resolution_percentage = int(A.get('pct', 100)); sc.render.filepath = path
    bpy.ops.render.render(write_still=True); print('WROTE', path)
def shoot_mask(path, nm_):
    """unlit: white where world z > 0.45 m (standing structure), black elsewhere; no lights/motion blur"""
    sc.render.use_motion_blur = False; sc.cycles.samples = 4; sc.cycles.use_denoising = False; sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    mm = bpy.data.materials.new('MASK'); mm.use_nodes = True; nt = mm.node_tree; nt.nodes.clear(); out = nt.nodes.new('ShaderNodeOutputMaterial')
    geo = nt.nodes.new('ShaderNodeNewGeometry'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Position'], sep.inputs[0])
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.45; nt.links.new(sep.outputs['Z'], gt.inputs[0])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(gt.outputs[0], em.inputs['Strength']); em.inputs['Color'].default_value = (1, 1, 1, 1); nt.links.new(em.outputs[0], out.inputs['Surface'])
    for o in bpy.data.objects:
        if o.type in ('MESH', 'FONT', 'CURVE'):
            if o == G: o.hide_render = True; continue
            o.data.materials.clear() if o.type == 'MESH' else None
            if o.type == 'MESH': o.data.materials.append(mm)
            else: o.data.materials.clear(); o.data.materials.append(mm)
        if o.type == 'LIGHT': o.hide_render = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0, 0, 0, 1)
    for gw, gh in SIZES: shoot_game(os.path.join(path, 'mask_%s_%dx%d.png' % (nm_, gw, gh)), gw, gh)
nm = {'A': 'A', 'B': 'B', 'current': 'current'}[V]
if 'game' in SH:
    for gw, gh in SIZES: shoot_game(os.path.join(OUT, 'mine_lv10_%s_%dx%d.png' % (nm, gw, gh)), gw, gh)
if 'hero' in SH: shoot_hero(os.path.join(OUT, 'mine_lv10_%s_hero_1920x1080.png' % nm))
if 'mask' in SH: shoot_mask(OUT, nm)
def _hero_cam():
    cd.sensor_fit = 'HORIZONTAL'; cd.lens = float(A.get('lens', 26)); cd.sensor_width = 36
    loc = Vector([float(x) for x in A.get('hero_loc', '-32,-50,20').split(',')]); tg = Vector([float(x) for x in A.get('hero_tgt', '4,3,15.5').split(',')])
    cam.location = loc; cam.rotation_euler = (tg - loc).to_track_quat('-Z', 'Y').to_euler()
if 'proj' in SH or 'hproj' in SH:   # analytic edge check: project every evaluated vertex standing > 0.45 m into the 393x852 game frame
    from bpy_extras.object_utils import world_to_camera_view
    cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(FOV); rx, ry = SIZES[0]; sc.render.resolution_x, sc.render.resolution_y = rx, ry
    D = (W_ / 2) / (math.tan(math.radians(FOV / 2)) * rx / ry)
    cam.location = T + Vector((0, -D * math.cos(P), D * math.sin(P))); cam.rotation_euler = (T - cam.location).to_track_quat('-Z', 'Y').to_euler()
    if 'hproj' in SH: _hero_cam(); rx, ry = 1920, 1080; sc.render.resolution_x, sc.render.resolution_y = rx, ry
    dg = bpy.context.evaluated_depsgraph_get(); bpy.context.view_layer.update(); x0 = y0 = 1e9; x1 = y1 = -1e9; who = {}
    for o in bpy.data.objects:
        if o.type not in ('MESH', 'FONT') or o.hide_render or o == G: continue
        oe = o.evaluated_get(dg); me = oe.to_mesh(); mw = oe.matrix_world
        for v in me.vertices:
            p = mw @ v.co
            if p.z <= 0.45: continue
            c = world_to_camera_view(sc, cam, p); px_, py_ = c.x * rx, (1 - c.y) * ry
            if px_ < x0: x0 = px_; who['L'] = o.name
            if px_ > x1: x1 = px_; who['R'] = o.name
            if py_ < y0: y0 = py_; who['T'] = o.name
            if py_ > y1: y1 = py_; who['B'] = o.name
            if px_ > rx - 8 or px_ < 8: who.setdefault('edge', set()).add((o.name, tuple(round(x, 1) for x in p)))
        oe.to_mesh_clear()
    print('PROJ %s bbox x %.1f..%.1f  y %.1f..%.1f  margins L %.1f R %.1f T %.1f B %.1f  %s' % (V, x0, x1, y0, y1, x0, rx - x1, y0, ry - y1, who))
