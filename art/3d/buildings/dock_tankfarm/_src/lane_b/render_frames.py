"""lane B light game-cam frames (Workbench only) at 375x667: Refinery, Dock, Pad, with FB-05 in each lane.
blender -b -t 4 -P render_frames.py -- OUTDIR"""
import bpy, sys, os, math, json
from mathutils import Vector
OUT = sys.argv[sys.argv.index('--') + 1]; os.makedirs(OUT, exist_ok=True); U = '/workspace/dockl/laneB'
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
def imp(path, loc, yaw=0.0, name=None):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path); new = [o for o in bpy.data.objects if o not in before]
    e = bpy.data.objects.new(name or os.path.basename(path), None); sc.collection.objects.link(e); e.location = loc; e.rotation_euler = (0, 0, yaw)
    for o in new:
        o.hide_render = False; o.hide_viewport = False
        if o.parent is None: o.parent = e
    return e
gl = lambda x, z, y=0.0: (x, -z, y)
imp(U + '/unpacked/refinery.glb', gl(320, 0)); imp(U + '/crane/crane_raw.glb', gl(311, 17.5)); imp(U + '/dock/raw.glb', gl(480, 0)); imp(U + '/unpacked/pad.glb', gl(640, 0))
for o in bpy.data.objects:   # cam targets / markers are empties: harmless
    pass
L = json.load(open(U + '/lanes_B.json'))
road = bpy.data.materials.new('road'); road.diffuse_color = (0.16, 0.16, 0.17, 1); spur = bpy.data.materials.new('spur'); spur.diffuse_color = (0.30, 0.26, 0.12, 1)
def strip(pts, w, mat, y=0.04):
    import bmesh; bm = bmesh.new(); vs = []
    for i, (x, z) in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]; tx, tz = b[0] - a[0], b[1] - a[1]; n = math.hypot(tx, tz) or 1; nx, nz = -tz / n, tx / n
        vs.append((bm.verts.new(gl(x + nx * w / 2, z + nz * w / 2, y)), bm.verts.new(gl(x - nx * w / 2, z - nz * w / 2, y))))
    for (a1, a2), (b1, b2) in zip(vs, vs[1:]): bm.faces.new((a1, a2, b2, b1))
    me = bpy.data.meshes.new('road'); bm.to_mesh(me); o = bpy.data.objects.new('ROAD', me); o.data.materials.append(mat); sc.collection.objects.link(o)
def arc(cx, cz, r, a0, a1, n=24): return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cz + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
def taper(x0, z0, x1, z1, n=16): return [(x0 + (x1 - x0) * i / n, z0 + (z1 - z0) * (1 - math.cos(math.pi * i / n)) / 2) for i in range(n + 1)]
strip([(295, 23), (641, 23)], 4.6, road); strip([(295, 32), (641, 32)], 4.6, road)
strip(taper(464, 23, 476, 19.4) + [(488, 19.4)] + taper(488, 19.4, 500, 23)[1:], 4.6, road)
strip(arc(295, 27.5, 4.5, math.pi / 2, 1.5 * math.pi), 4.6, road)
strip(taper(620.5, 23, 632.5, 19.75) + [(641, 19.75)] + arc(641, 25.875, 6.125, -math.pi / 2, math.pi / 2)[1:], 4.6, spur)   # AA2 spur + U-turn (proposed, AA2 builds)
TR = {'refinery': [(318, 23, 0), (313, 32, 1)], 'dock': [(480, 19.4, 0), (486, 32, 1)], 'pad': [(639.5, 19.75, 0), (630, 32, 1)]}
for k, ts in TR.items():
    for (x, z, back) in ts: imp(U + '/unpacked/fb05.glb', gl(x, z), math.pi if back else 0.0, 'FB05_' + k)
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_shadows = True; sh.shadow_intensity = 0.35; sh.show_cavity = True
w = bpy.data.worlds.new('W'); sc.world = w; w.color = (0.02, 0.022, 0.026); sc.view_settings.view_transform = 'Standard'
cd = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(cam); sc.camera = cam; cd.clip_end = 3000; cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(38)
CAMS = {'refinery': ((313.1, 2.08, 13.55), 37.5), 'dock': ((492, 1.5, 2), 66), 'pad': ((640, 4, -0.7), 78.25)}
W_, H_ = 375, 667; sc.render.resolution_x, sc.render.resolution_y = W_, H_
for k, (ct, fw) in CAMS.items():
    tgt = Vector(gl(ct[0], ct[2], ct[1])); d = fw / (2 * math.tan(math.radians(19)) * W_ / H_); e = math.radians(18)
    cam.location = tgt + Vector((0, -d * math.cos(e), d * math.sin(e))); cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, f'laneB_{k}_gamecam_375x667.png'); bpy.ops.render.render(write_still=True); print('FRAME', k, round(d, 2), flush=True)
print('FRAMES DONE')
