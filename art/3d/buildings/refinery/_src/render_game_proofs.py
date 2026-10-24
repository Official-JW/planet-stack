"""Game-asset proofs for the Refinery (what the game draws): refinery_game.glb + the shared HT-04 (art/3d/props/ht04/ht04_game.glb)
tipping at Truck_Dump, on a flat y-0 ground with the shared M_ground. Cycles CPU, OIDN, one full-frame tile (low samples).
  station : refinery_station_game_393x852.png, station camera from the GLB's Cam_Target extras (fov_y 38, pitch 18, frame_w)
  closeup : refinery_intake_truck_closeup.png (1600x1000), low oblique on RB-1 + the tipping truck, truck path markers as red balls
  top     : refinery_intake_truck_top.png (1600x1000), orthographic top view of the haul lanes, U-turn and intake
usage: blender -b -P render_game_proofs.py -- --game refinery_game.glb --ht04 ht04_game.glb --out DIR [--only station,closeup,top] [--s 24]"""
import bpy, sys, os, math, subprocess, json
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', '..', 'mine_concepts', '_src')))
from mc_common import M_ground, setup_render, shoot, coll
from place_ht04 import place_ht04, GLTFPACK
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i][2:]: a[i + 1] for i in range(0, len(a) - 1, 2)}
OUT = A['out']; os.makedirs(OUT, exist_ok=True); ONLY = A.get('only', 'station,closeup,top').split(','); SMP = int(A.get('s', 24))
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
_st = bpy.data.collections.new('Stage'); bpy.context.scene.collection.children.link(_st)
plain = '/tmp/rf_game_plain.glb'; subprocess.run([GLTFPACK, '-i', A['game'], '-o', plain, '-noq', '-kn', '-ke'], check=True, capture_output=True)
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=plain); new = [o for o in bpy.data.objects if o not in before]
CT = None; MK = {}
for o in new:
    p = o
    while p is not None:
        if p.name.startswith('Tier_'): o.hide_render = True        # the game hides tiers by default
        p = p.parent
    if o.name.startswith('Cam_Target'): CT = (o.matrix_world.translation.copy(), dict(o.items()))
    if o.name.startswith(('Truck_Path_', 'Truck_Dump', 'Truck_Exit')): MK[o.name] = o.matrix_world.translation.copy()
place_ht04(A['ht04'], _st)
bpy.ops.mesh.primitive_plane_add(size=1, location=(-10, 10, 0)); g = bpy.context.active_object; g.name = 'Ground'; g.scale = (4000, 4000, 1)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)   # M_ground uses Object coords: keep them = metres
g.data.materials.append(M_ground())
cam = setup_render(SMP); sc = bpy.context.scene; sc.cycles.use_auto_tile = False
sun = bpy.data.lights.new('Sun', 'SUN'); sun.energy = 4.0; sun.angle = math.radians(1.0)
so = bpy.data.objects.new('Sun', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), math.radians(-20), math.radians(-35))
w = sc.world or bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.022, 0.026, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
sc.view_settings.look = 'AgX - Base Contrast'
print('CAM_TARGET', CT[0][:] if CT else None, {k: v for k, v in (CT[1].items() if CT else [])}, 'MARKERS', {k: tuple(round(x, 2) for x in v) for k, v in MK.items()}, flush=True)
if 'station' in ONLY:
    t, ex = CT; fw = float(ex.get('frame_w', 30.8)); fov = float(ex.get('fov_y_deg', 38)); pitch = math.radians(float(ex.get('pitch_down_deg', 18)))
    for _wh in A.get('sizes', '393x852').split(','):
        W, H = map(int, _wh.split('x')); d = fw / (2.0 * math.tan(math.radians(fov / 2)) * (W / H))
        pos = t + Vector((0.0, -d * math.cos(pitch), d * math.sin(pitch)))
        cam.data.type = 'PERSP'; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(fov)
        cam.location = pos; cam.rotation_euler = (t - pos).to_track_quat('-Z', 'Y').to_euler()
        sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.filepath = os.path.join(OUT, f'refinery_station_game_{W}x{H}.png')
        print('STATION dist', round(d, 2), 'frame_w', fw, flush=True); bpy.ops.render.render(write_still=True)
    cam.data.sensor_fit = 'AUTO'
balls = []
if 'closeup' in ONLY or 'top' in ONLY:
    rm = bpy.data.materials.new('MarkerRed'); rm.use_nodes = True; bs = rm.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (0.6, 0.06, 0.03, 1); bs.inputs['Roughness'].default_value = 0.4
    for n, p in MK.items():
        if n == 'Truck_Dump': continue
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.32, location=(p.x, p.y, 0.6)); b = bpy.context.active_object; b.data.materials.append(rm); balls.append(b)
if 'closeup' in ONLY:
    cam.data.type = 'PERSP'
    _dd = bpy.data.objects.get('Dump_Dust')
    if _dd: _dd.scale = (1.1,) * 3; print('DUMP_DUST shown at clip frame ~15 (scale 1.1)', flush=True)   # rest = hidden (0.001)
    shoot(cam, os.path.join(OUT, 'refinery_intake_truck_closeup.png'), (1.2, -2.5, 1.4), (-8.5, -17.0, 7.5), 1600, 1000, lens=32)
if 'top' in ONLY:
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 30.0
    shoot(cam, os.path.join(OUT, 'refinery_intake_truck_top.png'), (-5.0, -4.5, 0.0), (-5.0, -4.501, 80.0), 1600, 1000)
