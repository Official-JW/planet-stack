"""Proof renders for FB-05 / cargo box / Refinery crane (CPU Cycles, low samples, OIDN, no tiling).
Inputs are the SHIPPED GLBs unpacked (crane: the --proofclip build, same mesh/markers + proof-only crane_load clip) with `gltfpack -noq -kn -ke` (Blender has no meshopt decoder).
blender -b -P render_props_proof.py -- --view VIEW --out PNG --w W --h H --samples N --fb FB_PLAIN --box BOX_PLAIN --crane CRANE_PLAIN
   [--crane_at x,z] [--ref REF_PLAIN --ref_at x [--ref_tiers all]] [--road ROAD_PLAIN --road_tiles x0,n,z,tail] [--pallet N] [--rx RX_PLAIN --rx_at x,z,yaw --rx_clip C --rx_t S] [--t CLIP_TIME] [--cam az,el,dist,tx,ty,tz] (Blender coords) | [--phone tx,ty,tz,frame_w] (glTF coords)"""
import bpy, sys, math
from mathutils import Vector, Matrix, Euler
A = sys.argv[sys.argv.index('--') + 1:]
def arg(k, d=None): return A[A.index('--' + k) + 1] if '--' + k in A else d
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 30
def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]
def imp(path):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path); new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.name.startswith('Icosphere'): o.hide_render = True
        if o.type == 'MESH':
            for slot in o.material_slots:
                m = slot.material; m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); out = nt.nodes.new('ShaderNodeOutputMaterial')
                if 'Glow' in m.name:
                    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = lin('#2fe3ff'); em.inputs['Strength'].default_value = 6.0
                    nt.links.new(em.outputs[0], out.inputs['Surface'])
                else:
                    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); ca = nt.nodes.new('ShaderNodeVertexColor')
                    ca.layer_name = o.data.color_attributes[0].name if o.data.color_attributes else ''
                    nt.links.new(ca.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.42; b.inputs['Metallic'].default_value = 0.0
                    nt.links.new(b.outputs[0], out.inputs['Surface'])
    return new
def root_of(new, name): return next(o for o in new if o.name.split('.')[0] == name)
def g2b(v): return Vector((v[0], -v[2], v[1]))
def place_at(obj, M):  # obj world = M
    bpy.context.view_layer.update(); obj.matrix_world = M
# ---- stage: regolith ground, sun, dark sky
bpy.ops.mesh.primitive_plane_add(size=1600, location=(240, 0, -0.002)); gnd = bpy.context.object   # covers crane-local proofs and world-placed station scenes
gm = bpy.data.materials.new('ground'); gm.use_nodes = True; nt = gm.node_tree; b = nt.nodes['Principled BSDF']
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.6; nz.inputs['Detail'].default_value = 8
cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = lin('#6f7175'); cr.color_ramp.elements[1].color = lin('#9a9ca0')
nt.links.new(nz.outputs['Fac'], cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.95
gnd.data.materials.append(gm)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 4.5; sun.data.angle = math.radians(1.5); sun.rotation_euler = Euler((math.radians(52), 0, math.radians(-38)))
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.05, 0.06, 0.08, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(arg('samples', 32)); sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.use_auto_tile = False; sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.resolution_x = int(arg('w', 1200)); sc.render.resolution_y = int(arg('h', 900)); sc.render.resolution_percentage = 100
sc.render.film_transparent = False
# ---- assets
view = arg('view'); T = float(arg('t', 3.8))
crane = fb = None; boxes = []
if arg('crane'):
    cn = imp(arg('crane')); crane = root_of(cn, 'Crane_Refinery'); carm = next(o for o in cn if o.type == 'ARMATURE')
    if arg('crane_at'):   # world placement (glTF x,z); everything placed from crane markers (truck, pallet boxes) follows
        cx_, cz_ = (float(v) for v in arg('crane_at').split(',')); crane.location = g2b((cx_, 0, cz_)); bpy.context.view_layer.update()
    if carm.animation_data is None: carm.animation_data_create()
    act = next((a for a in bpy.data.actions if a.name.startswith('crane_load')), None)
    for tr in list(carm.animation_data.nla_tracks): carm.animation_data.nla_tracks.remove(tr)
    if act: carm.animation_data.action = act
    sc.frame_set(int(round(T * 30)))
if arg('fb'):
    fn = imp(arg('fb')); fb = root_of(fn, 'FB05')
    if crane:  # truck at the crane's Truck_Park pose
        bpy.context.view_layer.update(); fb.matrix_world = bpy.data.objects['Truck_Park'].matrix_world.copy()
        if fb.matrix_world.to_euler().x == 0: pass
def add_box(M):
    bn = imp(arg('box')); r = root_of(bn, 'CargoBox'); bpy.context.view_layer.update(); r.matrix_world = M; boxes.append(r); return r
bpy.context.view_layer.update()
def W(name):
    if name == 'Hook':   # bone: world position + jib yaw (spreader long axis follows the jib)
        pos = (carm.matrix_world @ carm.pose.bones['Hook'].matrix).translation; c = crane.matrix_world.translation
        return Matrix.Translation(pos)   # the clip's hook rotator holds the box at world yaw 0
    return bpy.data.objects[name].matrix_world.copy()
# proof-only crane_load (12 s): cycle 1 Pallet_Slot_05 -> Bed_Slot_01 (box on the hook 0.9-4.5 s), cycle 2 Pallet_Slot_06 -> Bed_Slot_02 (6.9-10.5 s)
if arg('box'):
    if crane and fb:
        on_hook = (0.9 <= T <= 4.5) or (6.9 <= T <= 10.5)
        if T > 4.5: add_box(W('Bed_Slot_01'))
        if T > 10.5: add_box(W('Bed_Slot_02'))
        if on_hook: add_box(W('Hook') @ Matrix.Translation((0, 0, -1.5)))   # box Hook_Point (top centre, 1.5 m) on the crane Hook
        npal = int(arg('pallet', 6))
        for i in range(1, npal + 1):
            n = 'Pallet_Slot_%02d' % i
            if (n == 'Pallet_Slot_05' and T >= 0.9) or (n == 'Pallet_Slot_06' and T >= 6.9): continue
            add_box(W(n))
    elif fb:
        add_box(W('Bed_Slot_01')); add_box(W('Bed_Slot_02'))
    else:
        add_box(Matrix.Identity(4))
if arg('ref'):    # --ref REFINERY_PLAIN --ref_at x : station GLB at world x, Tier_* and hidden_by_default nodes hidden (as in the game)
    rn = imp(arg('ref')); bpy.context.view_layer.update()
    for o in rn:
        if o.parent is None: o.location = o.location + g2b((float(arg('ref_at', 320)), 0, 0))
    def hide_tree(o):
        o.hide_render = True
        for c in o.children: hide_tree(c)
    for o in rn:
        if arg('ref_tiers') == 'all' and o.name.split('.')[0].startswith('Tier_'): continue   # --ref_tiers all: every Tier_* shown (end-game worst case)
        if o.name.split('.')[0].startswith('Tier_') or o.get('hidden_by_default'): hide_tree(o)
if arg('road'):   # --road_tiles x0,n,z,tail_scale (glTF, tile origin = west end, lane centres at tile z 0 and z +9)
    x0, n, rz, tail = (float(v) for v in arg('road_tiles', '-24,6,-9,0').split(','))
    xs = [(x0 + 8.0 * k, 1.0) for k in range(int(n))] + ([(x0 + 8.0 * int(n), tail)] if tail > 0 else [])
    for x, sx in xs:
        rn = imp(arg('road')); r = root_of(rn, 'HaulRoad_Seg'); bpy.context.view_layer.update()
        r.matrix_world = Matrix.Translation(g2b((x, 0, rz))) @ Matrix.Diagonal((sx, 1, 1, 1))
if arg('rx'):     # --rx RX_PLAIN --rx_at x,z,yaw_deg (glTF crane-local; yaw about +Y) --rx_clip NAME --rx_t SEC
    rn = imp(arg('rx')); rr = root_of(rn, 'Receiver'); rarm = next(o for o in rn if o.type == 'ARMATURE')
    x, z, yd = (float(v) for v in arg('rx_at', '0,0,0').split(','))
    bpy.context.view_layer.update(); rr.matrix_world = Matrix.Translation(g2b((x, 0, z))) @ Matrix.Rotation(math.radians(yd), 4, 'Z')
    if rarm.animation_data is None: rarm.animation_data_create()
    for tr in list(rarm.animation_data.nla_tracks): rarm.animation_data.nla_tracks.remove(tr)
    ract = next(a for a in bpy.data.actions if a.name.startswith(arg('rx_clip', 'guide')) and not a.name.startswith('crane_load'))
    rarm.animation_data.action = ract; print('RX ACTION', ract.name)
    sc.frame_set(int(round(T * 30)))
    if crane: carm.animation_data.action = act
    rarm.animation_data.action = ract
    # receiver clip time is independent: evaluate it by offsetting its action keys
    off = int(round(float(arg('rx_t', 0)) * 30)) - int(round(T * 30))
    for fc in ract.fcurves:
        for kp in fc.keyframe_points: kp.co.x += off; kp.handle_left.x += off; kp.handle_right.x += off
    sc.frame_set(int(round(T * 30)))
# ---- camera
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
if arg('phone'):
    tx, ty, tz, fw = (float(x) for x in arg('phone').split(','))
    asp = sc.render.resolution_x / sc.render.resolution_y; d = (fw / 2) / (math.tan(math.radians(19)) * asp)
    tgt = g2b((tx, ty, tz)); p = math.radians(18)
    cam.location = tgt + Vector((0, -d * math.cos(p), d * math.sin(p))); cam.rotation_euler = Euler((math.radians(90 - 18), 0, 0))
    cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(38); cam.data.clip_end = 2000
else:
    az, el, dist, tx, ty, tz = (float(x) for x in arg('cam').split(','))
    tgt = Vector((tx, ty, tz)); dirv = Vector((math.cos(math.radians(el)) * math.sin(math.radians(az)), -math.cos(math.radians(el)) * math.cos(math.radians(az)), math.sin(math.radians(el))))
    cam.location = tgt + dirv * dist; cam.data.lens = float(arg('lens', 50)); cam.data.clip_end = 2000
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    if arg('ortho'): cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(arg('ortho'))   # ortho_scale = frame width (m)
sc.render.filepath = arg('out'); bpy.ops.render.render(write_still=True); print('RENDERED', arg('out'))
