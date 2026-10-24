"""Receiver clip sheet: blender -b -P render_receiver_sheet.py -- RX_PLAIN.glb OUTDIR   (input unpacked with gltfpack -noq -kn -ke -ac)
CPU Cycles, low samples, OIDN, no tiling. One PNG per (clip, time) -> assemble with PIL."""
import bpy, sys, math
from mathutils import Vector
A = sys.argv[sys.argv.index('--') + 1:]; SRC, OUT = A[0], A[1]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=SRC)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
paint = bpy.data.materials.get('SHM_Paint')
if paint:   # vertex colours drive the paint (as in-game)
    nt = paint.node_tree; bsdf = nt.nodes.get('Principled BSDF'); vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Color'
    nt.links.new(vc.outputs['Color'], bsdf.inputs['Base Color'])
bpy.ops.mesh.primitive_plane_add(size=60); g = bpy.context.object; gm = bpy.data.materials.new('g'); gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.32, 0.31, 0.29, 1); gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.95; g.data.materials.append(gm)
# Home -> Receive path markers on the ground (thin dark dots) to read foot placement
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 4.0; sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.06, 0.07, 0.09, 1)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16; sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.use_auto_tile = False; sc.view_settings.view_transform = 'AgX'; sc.render.resolution_x = 360; sc.render.resolution_y = 420; sc.render.fps = 30
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50
if arm.animation_data is None: arm.animation_data_create()
for tr in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(tr)
CL = {'walk_out': 4.0, 'guide': 2.0, 'check_in': 2.0, 'walk_back': 4.4}
for clip, dur in CL.items():
    act = next(a for a in bpy.data.actions if a.name.startswith(clip)); arm.animation_data.action = act
    close = clip in ('guide', 'check_in')
    for k in range(6):
        t = dur * k / 5; sc.frame_set(int(round(t * 30)))
        # Blender coords: glTF (x, y, z) -> (x, -z, y). Walks framed wide, guide/check_in close.
        tgt = Vector((-1.5, 0.75, 1.0)) if not close else Vector((0, 0, 1.15))
        d = 9.5 if not close else 4.2
        cam.location = tgt + Vector((math.sin(math.radians(25)), -math.cos(math.radians(25)), 0.32)).normalized() * d
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{OUT}/{clip}_{k}.png'; bpy.ops.render.render(write_still=True)
print('SHEET DONE')
