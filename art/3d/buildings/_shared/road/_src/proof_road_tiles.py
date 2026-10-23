"""Proof: Mine stub end -> 3 tiled (8 m) haul_road_seg copies -> Refinery road start (Cycles, shared M_ground on a flat plane).
usage: blender -b -P proof_road_tiles.py -- --mine mine_plain.glb --ref refinery_plain.glb --seg haul_road_seg_plain.glb --out proof.png
       [--w 1179 --h 663 --samples 48 --x0 26 --n 3 --cam x,y,z --tgt x,y,z --lens 24]
GLBs must be un-meshopt'd copies (gltfpack -noq): the Blender importer has no meshopt decoder. Coords below are Blender (glTF z = -Y)."""
import bpy, sys, os, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', 'mine_concepts', '_src')))
from mc_common import M_ground, setup_render, shoot, coll
a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i][2:]: a[i + 1] for i in range(0, len(a) - 1, 2)}
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
X0 = float(A.get('x0', 26.0)); N = int(A.get('n', 3)); TL = float(A.get('tl', 8.0)); REFX = X0 + TL * N + 48.0     # Refinery road starts at its local x -48
def imp(path, x):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path); new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None: o.location.x += x
    for o in new:
        if o.name.startswith(('Tier_', 'Truck_', 'Cam_Target')) and o.type == 'MESH': o.hide_render = True
    return new
imp(A['mine'], 0.0)
for k in range(N): imp(A['seg'], X0 + TL * k)
imp(A['ref'], REFX)
bpy.ops.mesh.primitive_plane_add(size=1, location=(X0 + TL / 2 * N, -4.5, 0.0)); g = bpy.context.active_object; g.name = 'Ground'
g.scale = (260, 160, 1); g.data.materials.append(M_ground())
_st = bpy.data.collections.new('Stage'); bpy.context.scene.collection.children.link(_st)
cam = setup_render(int(A.get('samples', 48)))
sun = bpy.data.lights.new('Sun', 'SUN'); sun.energy = 4.0; sun.angle = math.radians(1.0)
so = bpy.data.objects.new('Sun', sun); bpy.context.scene.collection.objects.link(so); so.rotation_euler = (math.radians(50), math.radians(-20), math.radians(-35))
w = bpy.context.scene.world or bpy.data.worlds.new('W'); bpy.context.scene.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.022, 0.026, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
tgt = tuple(float(v) for v in A.get('tgt', f'{X0 + TL / 2 * N},-4.5,0').split(','))
pos = tuple(float(v) for v in A.get('cam', f'{X0 + TL / 2 * N},-48,30').split(','))
bpy.context.scene.view_settings.look = 'AgX - Base Contrast'
shoot(cam, A['out'], tgt, pos, int(A.get('w', 1179)), int(A.get('h', 663)), lens=float(A.get('lens', 24)))
print('SEGS at x', [X0 + TL * k for k in range(N)], 'REF origin x', REFX)
