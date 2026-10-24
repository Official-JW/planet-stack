# v4.1 hotfix proof: side view (375x667, Workbench) of one crew member's feet at the Pad_Base deck lip before Crew_Path_03.
# blender -b -t 4 -P lip_still.py -- POSE_PREFIX PAD_PLAIN.glb TIME_INDEX CREW_INDEX OUT.png [LABEL]
import bpy, sys, json, math, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; pre, pad, ti, ci, out = a[0], a[1], int(a[2]), int(a[3]), a[4]; label = a[5] if len(a) > 5 else ''
meta = json.load(open(pre + '.json')); V = meta['nverts']; T = meta['times']
P = np.fromfile(pre + '_pos.bin', np.float32).reshape(len(T), 4, V, 3)
mb = np.fromfile(pre + '_mesh.bin', np.uint8); tri = np.frombuffer(mb[:meta['ntris'] * 12].tobytes(), np.uint32).reshape(-1, 3)
col = np.frombuffer(mb[meta['ntris'] * 12:].tobytes(), np.float32).reshape(-1, 3)
g2b = lambda p: np.stack([p[..., 0], -p[..., 2], p[..., 1]], -1)
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=pad)
for o in list(sc.objects):
    if o.type in ('CAMERA', 'LIGHT'): bpy.data.objects.remove(o)
for k in range(4):
    if not meta['visible'][ti][k]: continue
    me = bpy.data.meshes.new('Crew_%d' % (k + 1)); me.from_pydata(g2b(P[ti, k]).tolist(), [], tri.tolist())
    at = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT'); at.data.foreach_set('color', np.c_[col, np.ones(len(col))].ravel().astype(np.float32))
    sc.collection.objects.link(bpy.data.objects.new('Crew_%d' % (k + 1), me))
Q = P[ti, ci]; feet = Q[Q[:, 1] < 0.6]; c = feet.mean(0)
d = np.array([-2.40 - -7.85, 2.20 - 8.20]); d /= np.linalg.norm(d); side = np.array([d[1], -d[0]])   # walk dir CP2->CP3 (x,z) and its normal
SG = float(a[6]) if len(a) > 6 else 1.0; cg = np.array([c[0], 0.42, c[2]]); eye = np.array([c[0], 0.55, c[2]]) + np.array([side[0], 0, side[1]]) * float(a[7] if len(a) > 7 else 2.4) * SG
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(38)
cam.location = Vector(g2b(eye).tolist()); cam.rotation_euler = (Vector(g2b(cg).tolist()) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_shadows = True; sh.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 375, 667; sc.render.resolution_percentage = 100; sc.render.filepath = out
bpy.ops.render.render(write_still=True); print('LIP_STILL', out, T[ti], ci + 1)
