"""Fill / pour / rich proof renders of the GAME mesh in the Mine phone framing (Cam_Target extras).
  $B -b -P proof_fill.py -- --glb /tmp/mine4/raw_pruned.glb --out DIR [--ps 24]
(Blender's importer has no meshopt decoder: feed it the pruned raw GLB = mine_game.glb before gltfpack.)
Writes DIR/stage_XX_<pct>.png (393x852), pour.png, rich.png and closeup_{full,pour,rich}.png (1179x2556 phone scale, cropped)."""
import bpy, sys, math, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i].lstrip('-'): a[i + 1] for i in range(0, len(a) - 1, 2)}
OUT = A['out']; os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=A['glb'])
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = int(A.get('ps', 24)); sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'; sc.render.film_transparent = False
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.03, 0.035, 0.045, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 4.0; sd.angle = math.radians(3); s_ = bpy.data.objects.new('Sun', sd); sc.collection.objects.link(s_)
s_.rotation_euler = (math.radians(50), math.radians(-25), math.radians(35))
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, -0.06)); gp = bpy.context.active_object
gm = bpy.data.materials.new('Reg'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.16, 0.16, 0.165, 1); gp.data.materials.append(gm)
for m in bpy.data.materials:                       # glTF COLOR_0 multiplies base colour
    if not m.use_nodes or m == gm: continue
    nt = m.node_tree; bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs is None or bs.inputs['Base Color'].is_linked: continue
    ca = nt.nodes.new('ShaderNodeVertexColor'); mix = nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1
    mix.inputs[1].default_value = bs.inputs['Base Color'].default_value; nt.links.new(ca.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], bs.inputs['Base Color'])
    if bs.inputs['Emission Strength'].default_value > 0 and not bs.inputs['Emission Color'].is_linked: nt.links.new(mix.outputs[0], bs.inputs['Emission Color'])
ct = bpy.data.objects['Cam_Target']; W = ct['frame_w']; FOV = ct['fov_y_deg']; P = math.radians(ct['pitch_down_deg']); D = ct['distance_m']
T = ct.matrix_world.translation.copy()
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(FOV); cd.clip_end = 2000
cam.location = T + Vector((0, -D * math.cos(P), D * math.sin(P))); cam.rotation_euler = (T - cam.location).to_track_quat('-Z', 'Y').to_euler()
for o in bpy.data.objects:                         # tiers hidden by default (as in game)
    if o.get('hidden_by_default'): o.hide_render = True
arm = bpy.data.objects['Truck']; tm = next(o for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys and 'fill' in o.data.shape_keys.key_blocks)
kf = tm.data.shape_keys.key_blocks['fill']
for o in bpy.data.objects:
    if o.animation_data: o.animation_data.action = None
    if o.animation_data:
        for t in o.animation_data.nla_tracks: t.mute = True
def act(name, f):
    arm.animation_data_create(); arm.animation_data.action = next((x for x in bpy.data.actions if x.name.startswith(name)), None) if name else None
    for pb in arm.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    sc.frame_set(f)
from bpy_extras.object_utils import world_to_camera_view
def wt(pct): return math.sqrt(pct / 100.0)       # documented mapping: morph influence = sqrt(fill_pct / 100)
def bbox_px(rx, ry):
    q = world_to_camera_view(sc, cam, arm.matrix_world.translation + Vector((-1.6, 0, 2.5)))
    return q.x, q.y
def render(path, rx, ry, crop=None):
    sc.render.resolution_x, sc.render.resolution_y = rx, ry; sc.render.resolution_percentage = 100
    if crop:
        cx, cy = bbox_px(rx, ry); hw, hh = crop[0] / rx / 2, crop[1] / ry / 2
        sc.render.use_border = True; sc.render.use_crop_to_border = True
        sc.render.border_min_x, sc.render.border_max_x = cx - hw, cx + hw; sc.render.border_min_y, sc.render.border_max_y = cy - hh, cy + hh
    else: sc.render.use_border = False
    sc.render.filepath = path; bpy.ops.render.render(write_still=True); print('WROTE', path)
st = A.get('stages', '1') == '1'
if st:
    for i, pct in enumerate((0, 17, 33, 50, 67, 83, 100)):
        act(None, 0); kf.value = wt(pct); render(os.path.join(OUT, 'stage_%02d_%03d.png' % (i, pct)), 393, 852, crop=(150, 110))
    kf.value = wt(50); act('chute_pour', 7); render(os.path.join(OUT, 'pour.png'), 393, 852, crop=(150, 110))
    kf.value = wt(75); act('truck_load_rich', 12); render(os.path.join(OUT, 'rich.png'), 393, 852, crop=(150, 110))
    kf.value = 1.0; act(None, 0); render(os.path.join(OUT, 'frame_393x852_full.png'), 393, 852)
for nm, pct, clip, f in (('full', 100, None, 0), ('pour', 50, 'chute_pour', 7), ('rich', 75, 'truck_load_rich', 12), ('empty', 0, None, 0)):
    kf.value = wt(pct); act(clip, f); render(os.path.join(OUT, 'closeup_%s.png' % nm), 1179, 2556, crop=(480, 360))
