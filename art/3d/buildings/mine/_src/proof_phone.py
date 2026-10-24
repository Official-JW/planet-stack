"""Phone-frame proofs of the GAME mesh from the station camera (Cam_Target extras), HT-04 on a truck_pose marker.
  $B -b -P proof_phone.py -- --glb RAW_PRUNED.glb --truck HT04_RAW.glb --out DIR [--at Path_Load] [--fill 1] [--tiers 0|1]
        [--sizes 393x852,1179x2556] [--ps 16] [--name mine] [--clip truck_dump --frame 45]
        [--sclip dump_dust --sobj OBJ --sframe 20] [--suffix _x]
CPU Cycles, low samples, denoiser (OIDN) off, auto-tiling off (box rule). Blender has no meshopt decoder: feed the pruned raw GLB."""
import bpy, sys, math, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i].lstrip('-'): a[i + 1] for i in range(0, len(a) - 1, 2)}
OUT = A['out']; os.makedirs(OUT, exist_ok=True); NAME = A.get('name', 'mine')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=A['glb'])
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.animation_data:
        o.animation_data.action = None
        for t in o.animation_data.nla_tracks: t.mute = True
if A.get('truck'):
    bpy.ops.import_scene.gltf(filepath=A['truck']); bpy.context.view_layer.update()
    tr = bpy.data.objects['Truck']; tr.matrix_world = bpy.data.objects[A.get('at', 'Path_Load')].matrix_world.copy()
    for o in bpy.data.objects:
        if o.animation_data:
            o.animation_data.action = None
            for t in o.animation_data.nla_tracks: t.mute = True
    tm = next((o for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys and 'fill' in o.data.shape_keys.key_blocks), None)
    if tm: tm.data.shape_keys.key_blocks['fill'].value = float(A.get('fill', 1.0))
    for pb in tr.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    if A.get('clip'):
        act = next((x for x in bpy.data.actions if x.name.startswith(A['clip'])), None)
        tr.animation_data_create(); tr.animation_data.action = act; sc.frame_set(int(A.get('frame', 45)))
if A.get('sclip'):                          # one station clip posed at a frame: --sclip dump_dust --sobj Dust_Emitter --sframe 20
    act = next((x for x in bpy.data.actions if x.name.startswith(A['sclip'])), None); ob = bpy.data.objects[A['sobj']]
    ob.animation_data_create(); ob.animation_data.action = act; sc.frame_set(int(A.get('sframe', 20)))
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(A.get('ps', 16)); sc.cycles.use_denoising = False
sc.cycles.use_auto_tile = False; sc.render.threads_mode = 'AUTO'
sc.view_settings.view_transform = 'AgX'; sc.render.film_transparent = False
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.03, 0.035, 0.045, 1)
sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 4.0; sd.angle = math.radians(3); s_ = bpy.data.objects.new('Sun', sd); sc.collection.objects.link(s_)
s_.rotation_euler = (math.radians(50), math.radians(-25), math.radians(35))
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, -0.03)); gp = bpy.context.active_object
gm = bpy.data.materials.new('Reg'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.16, 0.16, 0.165, 1); gp.data.materials.append(gm)
for m in bpy.data.materials:                       # glTF COLOR_0 multiplies base colour
    if not m.use_nodes or m == gm: continue
    nt = m.node_tree; bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs is None or bs.inputs['Base Color'].is_linked: continue
    ca = nt.nodes.new('ShaderNodeVertexColor'); mix = nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1
    mix.inputs[1].default_value = bs.inputs['Base Color'].default_value; nt.links.new(ca.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], bs.inputs['Base Color'])
    if bs.inputs['Emission Strength'].default_value > 0 and not bs.inputs['Emission Color'].is_linked: nt.links.new(mix.outputs[0], bs.inputs['Emission Color'])
for o in bpy.data.objects:
    if o.get('hidden_by_default') or o.name.startswith('Tier_'): o.hide_render = A.get('tiers', '0') != '1'
ct = bpy.data.objects['Cam_Target']; W = ct['frame_w']; FOV = ct['fov_y_deg']; P = math.radians(ct['pitch_down_deg'])
T = ct.matrix_world.translation.copy()
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(FOV); cd.clip_end = 3000
for sz in A.get('sizes', '393x852,1179x2556').split(','):
    rx, ry = (int(v) for v in sz.split('x'))
    D = (W / 2) / (math.tan(math.radians(FOV / 2)) * rx / ry)         # QA3D: same formula at every aspect
    cam.location = T + Vector((0, -D * math.cos(P), D * math.sin(P))); cam.rotation_euler = (T - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = rx, ry; sc.render.resolution_percentage = 100
    path = os.path.join(OUT, '%s_%s%s.png' % (NAME, sz, A.get('suffix', ''))); sc.render.filepath = path
    bpy.ops.render.render(write_still=True); print('WROTE', path)
