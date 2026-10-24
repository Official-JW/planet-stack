"""Proof renders for FB-05 / cargo box / Refinery crane (CPU Cycles, low samples, OIDN, no tiling).
Inputs are the SHIPPED GLBs unpacked with `gltfpack -noq -kn -ke` (Blender has no meshopt decoder).
blender -b -P render_props_proof.py -- --view VIEW --out PNG --w W --h H --samples N --fb FB_PLAIN --box BOX_PLAIN --crane CRANE_PLAIN
   [--road ROAD_PLAIN] [--t CLIP_TIME] [--cam az,el,dist,tx,ty,tz] (Blender coords) | [--phone tx,ty,tz,frame_w] (glTF coords)"""
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
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, -0.002)); gnd = bpy.context.object
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
if arg('box'):
    if crane and fb:
        lift = 0.9 <= T <= 4.5
        add_box(W('Bed_Slot_02'))                                   # earlier load already strapped on slot 02
        if lift:
            add_box(W('Hook') @ Matrix.Translation((0, 0, -1.5)))          # box Hook_Point (top centre, 1.5 m) on the crane Hook
        else: add_box(W('Pick_Point') if T < 0.9 else W('Bed_Slot_01'))
        if T < 0.9 or T > 4.5: add_box(W('Pick_Point') @ Matrix.Translation((0, 0, 0)) if T > 4.5 else W('Pick_Point'))
    elif fb:
        add_box(W('Bed_Slot_01')); add_box(W('Bed_Slot_02'))
    else:
        add_box(Matrix.Identity(4))
if arg('road'):
    for k in range(-3, 3):
        rn = imp(arg('road')); r = root_of(rn, 'HaulRoad_Seg'); bpy.context.view_layer.update()
        r.matrix_world = Matrix.Translation(g2b((8.0 * k, 0, (6.0 - 9.0) if crane else -9.0)))
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
sc.render.filepath = arg('out'); bpy.ops.render.render(write_still=True); print('RENDERED', arg('out'))
