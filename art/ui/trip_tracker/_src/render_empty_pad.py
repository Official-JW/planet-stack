"""Empty Launch Pad (ship away) through the game phone camera, for the trip tracker stills. Read-only on the blend.
flock /tmp/planet_stack_heavy.lock nice -n 19 blender -b art/3d/buildings/launch_pad/launch_pad_master.blend \
   -P art/ui/trip_tracker/_src/render_empty_pad.py -t 4 -- <out.png> <w> <h> <samples>"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
out, W, H, S = a[0], int(a[1]), int(a[2]), int(a[3])
hidden = 0
for o in bpy.data.objects:
    g = o.get('grp', '')
    if g in ('Ship', 'Hose_LOX', 'Hose_LCH4') or o.name.startswith('ship_ph'):
        o.hide_render = True; hidden += 1
for o in bpy.data.collections['Tiers'].all_objects: o.hide_render = False
# game phone camera (build_launch_pad.py GAME_NAMES['phone_cam'])
T = Vector((0.0, 0.7, 4.0)); pitch, fovy, fw = 18.0, 38.0, 78.25
half = math.radians(fovy / 2); asp = W / H
dd = (fw / 2) / (math.tan(half) * asp); el = math.radians(pitch)
C = T + Vector((0, -math.cos(el), math.sin(el))) * dd
sc = bpy.context.scene; cam = sc.camera
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
sc.cycles.samples = S; sc.cycles.use_denoising = True
cam.data.lens = 18.0 / math.tan(half); cam.data.dof.use_dof = False
cam.location = C; cam.rotation_euler = (T - C).to_track_quat('-Z', 'Y').to_euler()
sc.render.use_border = False; sc.render.filepath = out
print('HIDDEN', hidden, 'CAM', tuple(round(v, 2) for v in C), flush=True)
bpy.ops.render.render(write_still=True); print('RENDERED', out, flush=True)
