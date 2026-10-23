"""Clip contact sheet: renders 6 frames of each of the 4 chain clips from the raw GLB on a lunar stage.
blender -b -P render_sheet.py -- RAW.glb OUTDIR [samples] [size]"""
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import op_blender_common as C
a = sys.argv[sys.argv.index('--') + 1:]; RAW, OUT = a[0], a[1]; SAMP = int(a[2]) if len(a) > 2 else 24; SZ = int(a[3]) if len(a) > 3 else 720
VIEW = a[4] if len(a) > 4 else 'front'
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = SAMP; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
sc.render.resolution_x = sc.render.resolution_y = SZ
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = C.lin('#2b3a5e'); bg.inputs[1].default_value = 0.6
bpy.ops.mesh.primitive_plane_add(size=60); g = bpy.context.object
mg = bpy.data.materials.new('Ground'); mg.use_nodes = True; bb = mg.node_tree.nodes['Principled BSDF']; bb.inputs['Base Color'].default_value = C.lin('#7d7b79'); bb.inputs['Roughness'].default_value = 0.95; g.data.materials.append(mg)
sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 4.0; sd.color = C.lin('#fff4e4')[:3]; sd.angle = math.radians(0.6)
sun = bpy.data.objects.new('Sun', sd); sc.collection.objects.link(sun)
d = Vector((-0.55, -0.6, 0.78)).normalized(); sun.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
root, arm, new = C.import_operator(RAW)
cd = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.lens = 50
# glTF (x,y,z) -> Blender (x,-z,y). Deck centre top = (0, 0, 2.2 + 0.9)
tgt = Vector((-0.05, 0.0, 3.0))
pos = {'front': Vector((3.4, -6.4, 5.2)), 'side': Vector((-6.6, -3.0, 5.0))}[VIEW]
cam.location = pos; cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler(); cd.lens = 55
CLIPS = [('op_sit_type', 4.0), ('op_stand_walk_to_rail', 1.6), ('op_watch_rail', 3.0), ('op_walk_back_sit', 1.6)]
os.makedirs(OUT, exist_ok=True)
for clip, dur in CLIPS:
    C.set_clip(arm, clip)
    for k in range(6):
        t = dur * k / 5; f = t * 30
        sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
        sc.render.filepath = os.path.join(OUT, f'{clip}_{k}.png')
        if os.path.exists(sc.render.filepath) and not os.environ.get('OP_FORCE'): continue   # resume
        bpy.ops.render.render(write_still=True)
        print('RENDERED', clip, k, flush=True)
