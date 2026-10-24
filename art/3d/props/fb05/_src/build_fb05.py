"""FB-05 flatbed (sibling of the shared HT-04): HT-04 cab, chassis, wheels and SHM_Paint reused from the packed HT-04 GLB
(unpacked with gltfpack -noq), dump body / rams / heap / chunks removed, flatbed deck added.
blender -b -P build_fb05.py -- HT04_PLAIN.glb OUT_RAW.glb
Blender coords: X forward, Y = truck left (glTF -Z), Z up."""
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '_shared_src'))
from propgeo import MB, P, empty, export

SRC, OUT = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
arm = bpy.data.objects['Truck']; tm = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == arm and o.data.attributes.get('Color'))
for pb in arm.pose.bones: pb.custom_shape = None
for n in ('Fill_Arc', 'Truck_Mesh'):
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n])
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
if arm.animation_data: arm.animation_data_clear()
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
if tm.data.shape_keys: tm.shape_key_clear()
KEEP = {'Truck_Chassis'} | {'HT04_Wheel_' + s for s in ('FL', 'FR', 'ML', 'MR', 'RL', 'RR')}
gi = {g.index: g.name for g in tm.vertex_groups}
import bmesh
bm = bmesh.new(); bm.from_mesh(tm.data); dl = bm.verts.layers.deform.active; kill = []
for v in bm.verts:
    d = v[dl]; g = gi[max(d.items(), key=lambda kv: kv[1])[0]] if len(d) else 'Truck_Chassis'
    if g not in KEEP: kill.append(v)
bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(tm.data); bm.free()
for g in list(tm.vertex_groups):
    if g.name not in KEEP: tm.vertex_groups.remove(g)
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='EDIT')
for eb in list(arm.data.edit_bones):
    if eb.name not in KEEP: arm.data.edit_bones.remove(eb)
bpy.ops.object.mode_set(mode='OBJECT')
for b in arm.data.bones:
    nn = b.name.replace('HT04_', 'FB05_').replace('Truck_Chassis', 'FB05_Chassis')
    if tm.vertex_groups.get(b.name): tm.vertex_groups[b.name].name = nn
    b.name = nn
arm.name = 'FB05'; arm.data.name = 'FB05_Armature'; tm.name = 'FB05_Mesh'; tm.data.name = 'FB05_Mesh'
print('KEPT TRIS', sum(len(p.vertices) - 2 for p in tm.data.polygons), 'ARM', tuple(arm.matrix_world.to_translation()), tuple(arm.matrix_world.to_euler()))

# ---------------------------------------------------------------- flatbed body
B = 'FB05_Chassis'; m = MB()
X0, X1, W, ZT = -4.95, 0.30, 2.80, 1.90          # deck rear / front, width, deck top
XC, L = (X0 + X1) / 2, X1 - X0
SLOT = (-1.15, -3.65)                            # Bed_Slot_01 (front, behind the headboard), Bed_Slot_02 (rear)
m.box((L, W, 0.14), (XC, 0, ZT - 0.07), P['steel'], bone=B)                              # deck plate (worn steel)
for s in (-1, 1):
    m.box((L, 0.08, 0.22), (XC, s * (W / 2 + 0.02), ZT - 0.09), P['white'], bone=B)       # white side rub rail
    m.box((L - 0.7, 0.02, 0.035), (XC - 0.1, s * (W / 2 + 0.065), ZT - 0.13), P['cyan'], bone=B)   # cyan LED strip
    m.box((L - 0.3, 0.22, 0.24), (XC - 0.1, s * 0.55, ZT - 0.26), P['graph'], bone=B)     # main beams
    m.box((L, 0.03, 0.025), (XC, s * 0.62, ZT + 0.012), P['graph'], bone=B)               # L-track tie-down rails in the deck
    for x in (-4.85, -3.65, -2.45, -1.25, -0.05):                                         # stake posts in edge pockets
        m.box((0.1, 0.1, 0.55), (x, s * (W / 2 - 0.02), ZT + 0.27), P['graph'], bone=B)
        m.box((0.115, 0.115, 0.05), (x, s * (W / 2 - 0.02), ZT + 0.565), P['white'], bone=B)
    for sx in SLOT:                                                                         # tie-down D-rings at each crate's corners
        for dx in (-1.0, 1.0):
            m.box((0.18, 0.12, 0.025), (sx + dx, s * 1.22, ZT + 0.012), P['steel'], bone=B)
            m.box((0.13, 0.03, 0.08), (sx + dx, s * 1.22, ZT + 0.06), P['satin'], bone=B)
    m.box((0.035, 0.6, 0.75), (-3.78, s * 1.5, 1.12), P['tyre'], bone=B)                  # mudflaps behind the rear tandem
    m.box((0.70, 0.46, 0.46), (-4.4, s * 1.13, 1.43), P['white'], bone=B)                 # side toolbox under the overhang
    m.box((0.5, 0.02, 0.03), (-4.4, s * 1.365, 1.55), P['cyan'], bone=B)
    m.box((0.04, 0.24, 0.1), (-5.06, s * 0.98, 1.36), P['red'], bone=B)                   # tail lights
    m.box((0.08, 0.04, 0.06), (-2.0, s * 1.47, ZT - 0.13), P['amber'], bone=B)           # side marker
for x in (-4.6, -3.95, -3.3):                                                              # cross members under the overhang
    m.box((0.14, 1.32, 0.16), (x, 0, ZT - 0.30), P['graph'], bone=B)
m.box((0.08, W + 0.12, 0.22), (X0 - 0.04, 0, ZT - 0.09), P['white'], bone=B)              # rear rail + strip
m.box((0.02, W - 0.6, 0.035), (X0 - 0.09, 0, ZT - 0.13), P['cyan'], bone=B)
m.box((0.14, 2.4, 0.18), (-5.0, 0, 1.36), P['graph'], bone=B)                             # rear under-run bumper
for k in range(6): m.box((0.02, 0.3, 0.16), (-5.08, -1.0 + 0.4 * k, 1.36), P['amber'] if k % 2 == 0 else P['graph'], bone=B)
for s in (-1, 1): m.box((0.1, 0.1, 0.42), (-4.92, s * 0.9, 1.56), P['graph'], bone=B)
# headboard / cab guard
HX = 0.20
for s in (-1, 1): m.box((0.12, 0.12, 1.32), (HX, s * 1.34, ZT + 0.66), P['graph'], bone=B)
m.box((0.07, 2.56, 1.02), (HX, 0, ZT + 0.56), P['white'], bone=B)
m.box((0.16, 2.8, 0.12), (HX, 0, ZT + 1.30), P['graph'], bone=B)
m.box((0.02, 2.3, 0.04), (HX - 0.09, 0, ZT + 1.30), P['cyan'], bone=B)
for y in (-0.6, 0.6): m.box((0.09, 0.08, 1.02), (HX - 0.01, y, ZT + 0.56), P['graph2'], bone=B)
m.text('FB-05', 0.26, (HX - 0.04, 0, ZT + 0.82), (math.pi / 2, 0, -math.pi / 2), P['graph'], mat=0, bone=B)
m.weather(seed=5, z0=0.4, z1=2.3, amt=0.38, noise=0.06)
print('FLATBED TRIS', m.tris())
fb = m.build('fb_tmp')
fb.parent = arm; mod = fb.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
bpy.ops.object.select_all(action='DESELECT'); fb.select_set(True); tm.select_set(True); bpy.context.view_layer.objects.active = tm
bpy.ops.object.join()
tm.data.materials.pop(index=[i for i, mm in enumerate(tm.data.materials) if mm.name.startswith('SHM_GlowCyan')][0]) if any(mm.name.startswith('SHM_GlowCyan') for mm in tm.data.materials) else None
print('TOTAL TRIS', sum(len(p.vertices) - 2 for p in tm.data.polygons), 'MATS', [mm.name for mm in tm.data.materials])

# ---------------------------------------------------------------- markers + extras
for i, sx in enumerate(SLOT):
    empty('Bed_Slot_%02d' % (i + 1), (sx, 0, ZT), parent=arm, extras={
        'kind': 'cargo_slot', 'order': i + 1, 'deck_y': ZT,
        'note': 'cargo box Base goes here (box root = this transform, yaw 0 = box long axis along the truck, HELIUM-3 face on the truck right / +Z)'})
for o in (arm, tm, arm.data, tm.data):
    for k in list(o.keys()):
        if not k.startswith('_'): del o[k]
arm['prop'] = 'FB-05 flatbed (HT-04 sibling: same cab, chassis, wheels, SHM_Paint)'
arm['origin'] = 'ground centre under the truck (between the axle groups), +X forward = yaw 0, +Y up, left = -Z'
arm['wheel_radius'] = 0.853; arm['wheel_axle_height'] = 0.85
arm['wheels'] = 'FB05_Wheel_FL/FR/ML/MR/RL/RR: spin about local +X, positive = roll forward; angle += distance / wheel_radius; no baked spin'
arm['bed_slots'] = ['Bed_Slot_01', 'Bed_Slot_02']; arm['deck_top_y'] = ZT; arm['capacity_boxes'] = 2
export(OUT)
print('WROTE', OUT)
