"""Flat preview of the GAME GLB (all tiers visible, door closed) from the in-game station camera and the hero angle.
usage: blender -b -P render_game_preview.py -- --glb raw.glb --out DIR [--hc -7,-47,17,12.5,5,5.5]
(uses the un-packed raw GLB from build_game_glb_tiered.py: Blender's importer has no meshopt decoder; geometry is identical.)
Prints the screen-space box of every Tier_* node in the 393x852 phone frame."""
import bpy, sys, os, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i][2:]: a[i + 1] for i in range(0, len(a) - 1, 2)}
OUT = A.get('out', '/tmp'); os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=A['glb'])
sc = bpy.context.scene
for ob in sc.objects: ob.hide_render = False; ob.hide_viewport = False
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_shadows = True; sh.shadow_intensity = 0.35; sh.show_cavity = True
sc.display.shading.background_type = 'WORLD'
w = bpy.data.worlds.new('W'); sc.world = w; w.color = (0.02, 0.022, 0.026)
sc.view_settings.view_transform = 'Standard'
cd = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(cam); sc.camera = cam; cd.clip_end = 3000
ct = bpy.data.objects['Cam_Target']; tgt = ct.matrix_world.translation.copy(); W = float(ct['frame_w'])
def phone(wpx, hpx):
    asp = wpx / hpx; d = W / (2 * math.tan(math.radians(19)) * asp); e = math.radians(18)
    cam.location = tgt + Vector((0, -d * math.cos(e), d * math.sin(e))); cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(38)
    sc.render.resolution_x, sc.render.resolution_y = wpx, hpx; bpy.context.view_layer.update(); return d
d = phone(393, 852)
print('CAM_TARGET', tuple(round(v, 3) for v in tgt), 'frame_w', W, 'dist', round(d, 2))
dg = bpy.context.evaluated_depsgraph_get()
for ob in sorted(sc.objects, key=lambda o: o.name):
    if ob.type != 'MESH' or not (ob.name.startswith('Tier_') or ob.name in ('Crane_Gantry', 'Dock_Door', 'Beacon_Lights')): continue
    xs, ys = [], []
    for v in ob.data.vertices:
        q = world_to_camera_view(sc, cam, ob.matrix_world @ v.co); xs.append(q.x * 393); ys.append((1 - q.y) * 852)
    print('TIERBOX', ob.name, 'x %.0f..%.0f  y %.0f..%.0f' % (min(xs), max(xs), min(ys), max(ys)), 'centre_world', tuple(round(c, 2) for c in (ob.matrix_world @ (sum((v.co for v in ob.data.vertices), Vector()) / len(ob.data.vertices)))))
sc.render.filepath = os.path.join(OUT, 'game_preview_393x852.png'); bpy.ops.render.render(write_still=True)
hc = [float(v) for v in A.get('hc', '-7,-47,17,12.5,5,5.5').split(',')]
cd.sensor_fit = 'AUTO'; cd.lens = 28; cam.location = hc[:3]; cam.rotation_euler = (Vector(hc[3:]) - Vector(hc[:3])).to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.filepath = os.path.join(OUT, 'game_preview_hero.png'); bpy.ops.render.render(write_still=True)
print('PREVIEWS DONE')
