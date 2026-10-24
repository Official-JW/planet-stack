"""Seam proof: Mine (world x 160) -> 11 tiled 8 m haul_road_seg copies at world x 186 + 8 i (Mine-local 26 + 8 i) -> Refinery (world x 320),
on the game's flat y-0 ground (shared M_ground). Renders 4 panels (Cycles CPU, no denoiser, one tile): top-down + low oblique of the Mine join
(world x 186) and of the Refinery join (world x 274 = Refinery-local -46). Tier_ nodes hidden (the game hides them by default).
usage: blender -b -P proof_seams.py -- --mine mine_plain.glb --ref refinery_plain.glb --seg seg_plain.glb --outdir DIR [--samples 24] [--w 1179 --h 663]
GLBs must be un-meshopt'd (gltfpack -noq -kn -ke): the Blender importer has no meshopt decoder. Blender coords: glTF z = -Y."""
import bpy, sys, os, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', 'mine_concepts', '_src')))
from mc_common import M_ground, setup_render, shoot
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i][2:]: a[i + 1] for i in range(0, len(a) - 1, 2)}
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
MX, RX, X0, N, TL = 160.0, 320.0, 186.0, 11, 8.0
def imp(path, x):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path); new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None: o.location.x += x
    for o in new:
        p = o
        while p is not None:
            if p.name.startswith('Tier_'): o.hide_render = True
            p = p.parent
    return new
imp(A['mine'], MX)
for k in range(N): imp(A['seg'], X0 + TL * k)
imp(A['ref'], RX)
bpy.ops.mesh.primitive_plane_add(size=1, location=(240.0, -4.5, 0.0)); g = bpy.context.active_object; g.name = 'Ground'
g.scale = (4000, 4000, 1); g.data.materials.append(M_ground())
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)   # M_ground uses Object coords: keep them = metres
_st = bpy.data.collections.new('Stage'); bpy.context.scene.collection.children.link(_st)
cam = setup_render(int(A.get('samples', 24)))
sc = bpy.context.scene; sc.cycles.use_auto_tile = False; sc.cycles.use_denoising = False   # box rule: OIDN off, one tile
sun = bpy.data.lights.new('Sun', 'SUN'); sun.energy = 4.0; sun.angle = math.radians(1.0)
so = bpy.data.objects.new('Sun', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), math.radians(-20), math.radians(-35))
w = sc.world or bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.022, 0.026, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
sc.view_settings.look = 'AgX - Base Contrast'
W, H = int(A.get('w', 1179)), int(A.get('h', 663)); OD = A['outdir']; os.makedirs(OD, exist_ok=True)
Y_MID = -4.5                                   # between the lanes (glTF z 4.5)
for nm, jx in (('mine', X0), ('ref', X0 + TL * N)):
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 26.0
    shoot(cam, os.path.join(OD, f'{nm}_top.png'), (jx, Y_MID, 0.0), (jx, Y_MID - 0.001, 60.0), W, H)
    cam.data.type = 'PERSP'
    side = -1 if nm == 'mine' else 1            # look along the road toward the join from the strip side, low and from the camera (+glTF z) side
    shoot(cam, os.path.join(OD, f'{nm}_low.png'), (jx, Y_MID, 0.0), (jx - side * 14.0, Y_MID - 20.0, 2.2), W, H, lens=30)
print('JOINS world x', X0, X0 + TL * N)
