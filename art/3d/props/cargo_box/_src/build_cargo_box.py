"""HELIUM-3 cargo box = the starter ship's HELIUM-3 / ³He crate (art/3d/ship/starter_ship/build_starter_ship.py, crate() with
HE3_SZ 2.3 x 1.3 x 1.5, label 'HELIUM-3', badge '³He'; seen in the starter-ship crate close-up). Same layout, sizes and colours,
rebuilt at game LOD (unbevelled boxes, resolution-1 LED lettering, labelled on both long faces) + Base / Hook_Point empties.
blender -b -P build_cargo_box.py -- OUT_RAW.glb      Blender coords: Z up, front (label) = -Y = glTF +Z."""
import bpy, sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '_shared_src'))
from propgeo import MB, P, lin, empty, export
OUT = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
WHITE_S, GRAPH_S, GRAPH, SATIN, AMBER = lin('#e8edf5'), lin('#3a4258'), lin('#2a3245'), lin('#9aa3ad'), lin('#ffb020')
sx, sy, sz = 2.3, 1.3, 1.5
m = MB()
m.box((sx, sy, sz - 0.08), (0, 0, sz / 2 + 0.04), WHITE_S)                                   # _Body
for s in (-1, 1):
    m.box((0.14, sy + 0.04, sz - 0.06), (s * (sx / 2 - 0.2), 0, sz / 2 + 0.03), GRAPH_S)     # _Band
    m.box((sx + 0.04, 0.14, 0.08), (0, s * (sy / 2 - 0.14), 0.04), GRAPH)                   # _Skid
    m.box((0.04, 0.34, 0.06), (s * (sx / 2 + 0.03), 0, sz * 0.65), SATIN)                   # _Handle
m.box((sx + 0.03, sy + 0.03, 0.07), (0, 0, sz - 0.035), GRAPH_S)                             # _Lid
bz = (sz * 0.5 + 0.2 + sz - 0.175) / 2; bh = min(0.2, (sz - 0.175) - (sz * 0.5 + 0.2) - 0.03)
for f in (-1, 1):                                  # f = -1: front (-Y, glTF +Z, the ship crate's labelled face); f = +1: mirrored back face
    y = f * sy / 2; rz = 0 if f < 0 else math.pi
    m.box((sx - 0.6, 0.02, 0.03), (0, y + f * 0.005, sz - 0.16), P['cyan'], mat=1)           # _Glow strip
    m.box((sx - 0.6, 0.01, 0.4), (0, y + f * 0.004, sz * 0.5), GRAPH_S)                     # _Plate
    m.text('HELIUM-3', 0.3, (0, y + f * 0.011, sz * 0.5), (math.pi / 2, 0, rz), P['cyan'], mat=1)   # _Label
    m.box((0.62, 0.01, bh), (0, y + f * 0.004, bz), GRAPH_S)                               # _BadgePlate
    m.text('\u00b3He', bh * 0.8, (0, y + f * 0.011, bz), (math.pi / 2, 0, rz), P['cyan'], mat=1)    # _Badge
    for k in range(9):                                                                      # _Hazard band (amber / graphite chevrons)
        x0 = -(sx - 0.6) / 2 + k * (sx - 0.6) / 9; x1 = x0 + (sx - 0.6) / 9; yy = y + f * 0.009
        pts = [(x0, yy, 0.20), (x1, yy, 0.20), (x1, yy, 0.28), (x0, yy, 0.28)]
        m.quad(pts if f < 0 else pts[::-1], AMBER if k % 2 == 0 else GRAPH)
m.weather(seed=3, z0=0.0, z1=1.2, amt=0.35, noise=0.05)
print('BOX TRIS', m.tris())
root = bpy.data.objects.new('CargoBox', None); bpy.context.scene.collection.objects.link(root)
ob = m.build('CargoBox_Mesh'); ob.parent = root
empty('Base', (0, 0, 0), parent=root, extras={'kind': 'attach', 'note': 'bottom centre of the skids: put this on FB-05 Bed_Slot_0N or the Refinery Pick_Point'})
empty('Hook_Point', (0, 0, sz), parent=root, extras={'kind': 'attach', 'note': 'top centre of the lid (lifting eye of the 4-leg sling): crane Hook goes here'})
root['prop'] = 'HELIUM-3 cargo box (starter-ship HELIUM-3 / 3He crate, game LOD)'
root['size_m'] = [sx, sz, sy]; root['origin'] = 'Base = bottom centre; long axis +X, labelled faces +Z (front) and -Z'
root['hook_offset_y'] = sz
export(OUT); print('WROTE', OUT)
