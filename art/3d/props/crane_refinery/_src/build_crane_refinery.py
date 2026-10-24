"""Refinery loading crane RC-1: slewing jib crane on a pedestal (concept B: white / graphite, cyan strips, weathered).
One skinned mesh (SHM_Paint + SHM_GlowCyan = 2 draws). Code-driven joints: Slew (yaw about +Y), Trolley (translate local +X),
Hoist (cable: scale.y = cable length in m), Hook (translate local y = -(cable + HOOK_DROP)). The shipped GLB has NO clips (Coder drives the joints);
--proofclip bakes crane_load (6 s) into a proof-only file for the renders.
Includes the 8-box HELIUM-3 pallet on a 0.12 m concrete pad (both static, on Crane_Base) with Pallet_Slot_01..08.
blender -b -P build_crane_refinery.py -- OUT_RAW.glb [--proofclip]
Blender coords: Z up, jib rest direction +X. glTF = (x, z, -y)."""
import bpy, sys, os, math
from mathutils import Vector, Matrix, Euler, Quaternion
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '_shared_src'))
from propgeo import MB, P, lin, empty, export
ARGS = sys.argv[sys.argv.index('--') + 1:]; OUT = ARGS[0]; CLIP = '--proofclip' in ARGS
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 30

# ---------------------------------------------------------------- dimensions (m)
SLEW_Z = 1.8          # slewing ring height (Slew joint)
JIB_Z = 10.0          # jib bottom chord height (world)
SHEAVE_Z = JIB_Z - 0.35   # trolley sheave = Hoist joint (world z)
HOOK_DROP = 0.95      # hook block + spreader height: Hook (spreader underside, = box Hook_Point) sits HOOK_DROP below the cable end
JIB_L, CJ_L = 11.0, 4.6
TR_MIN, TR_MAX = 2.6, 10.3
CABLE_MIN, CABLE_MAX = 0.6, SHEAVE_Z - HOOK_DROP - 0.4
WHITE, WHITE2, GRAPH, GRAPH2, STEEL = P['white'], P['white2'], P['graph'], P['graph2'], P['steel']
m = MB()
# ---- static base (bone Crane_Base): pedestal footing, anchor bolts, column, power cabinet
for s in (-1, 1):
    m.box((3.4, 0.5, 0.5), (0, s * 1.2, 0.25), lin('#8d9096'))                 # sintered footing beams
    m.box((0.5, 3.4, 0.5), (s * 1.2, 0, 0.25), lin('#8d9096'))
m.box((2.2, 2.2, 0.35), (0, 0, 0.62), GRAPH)
for sx in (-1, 1):
    for sy in (-1, 1): m.cyl((sx * 0.9, sy * 0.9, 0.79), (sx * 0.9, sy * 0.9, 0.9), 0.07, STEEL, segs=6)
m.cyl((0, 0, 0.79), (0, 0, SLEW_Z - 0.12), 0.62, WHITE, segs=12)
m.cyl((0, 0, 1.2), (0, 0, 1.26), 0.635, P['cyan'], segs=12, mat=1)                # cyan ring on the column
m.cyl((0, 0, SLEW_Z - 0.12), (0, 0, SLEW_Z), 0.8, GRAPH, segs=12)                # lower slewing ring
m.box((0.8, 0.5, 1.1), (-1.1, 1.25, 0.55 + 0.6), WHITE)                          # power cabinet
m.box((0.5, 0.02, 0.04), (-1.1, 0.99, 1.45), P['cyan'], mat=1)
m.box((0.81, 0.51, 0.06), (-1.1, 1.25, 1.73), GRAPH)
m.box((0.3, 0.02, 0.06), (-1.1, 0.995, 1.0), P['amber'])
B = 'Slew'
# ---- slewing upper: turntable, lattice mast, cab, tower head, jib, counter-jib
m.cyl((0, 0, SLEW_Z), (0, 0, SLEW_Z + 0.25), 0.82, WHITE, segs=12, bone=B)
m.box((1.6, 1.6, 0.3), (0, 0, SLEW_Z + 0.4), GRAPH, bone=B)
MW = 1.1; M0, M1 = SLEW_Z + 0.55, JIB_Z
for sx in (-1, 1):
    for sy in (-1, 1): m.box((0.16, 0.16, M1 - M0), (sx * MW / 2, sy * MW / 2, (M0 + M1) / 2), WHITE, bone=B)
NP = 7; ph = (M1 - M0) / NP
for k in range(NP + 1):
    z = M0 + k * ph
    for s in (-1, 1):
        m.box((MW, 0.08, 0.08), (0, s * MW / 2, z), GRAPH, bone=B); m.box((0.08, MW, 0.08), (s * MW / 2, 0, z), GRAPH, bone=B)
    if k == NP: break
    dl = math.hypot(MW, ph); a = math.atan2(ph, MW)
    for s in (-1, 1):
        m.box((dl, 0.06, 0.06), (0, s * MW / 2, z + ph / 2), GRAPH, rot=(0, -a * (1 if k % 2 else -1), 0), bone=B)
        m.box((0.06, dl, 0.06), (s * MW / 2, 0, z + ph / 2), GRAPH, rot=(a * (1 if k % 2 else -1), 0, 0), bone=B)
m.box((0.16, 0.6, 3.0), (0, MW / 2 - 0.05, M0 + 1.6), P['cable'], bone=B)          # ladder cage strip
m.box((0.04, 0.02, M1 - M0 - 1.0), (MW / 2 + 0.09, -MW / 2 + 0.1, (M0 + M1) / 2), P['cyan'], mat=1, bone=B)   # mast LED strip
# operator cab at the jib root (looks along the jib)
CZ = JIB_Z - 1.0
m.box((1.7, 1.25, 1.5), (0.7, -1.25, CZ), WHITE, bone=B, taper=0.92)
m.box((0.04, 1.05, 0.55), (1.56, -1.25, CZ + 0.15), lin('#0e1a24'), bone=B)          # front glass
m.box((1.5, 0.04, 0.5), (0.7, -1.88, CZ + 0.15), lin('#0e1a24'), bone=B)
m.box((1.5, 0.02, 0.035), (0.7, -1.9, CZ - 0.18), P['cyan'], mat=1, bone=B)
m.box((1.75, 1.3, 0.1), (0.7, -1.25, CZ + 0.8), GRAPH, bone=B)
m.box((1.1, 0.8, 0.12), (0.4, -1.25, CZ - 0.81), GRAPH, bone=B)
# tower head (A-frame) + pendant ties
HZ = JIB_Z + 3.0
for sy in (-1, 1):
    m.cyl((MW / 2, sy * MW / 2, JIB_Z + 0.75), (0, sy * 0.25, HZ), 0.07, WHITE, segs=6, bone=B)
    m.cyl((-MW / 2, sy * MW / 2, JIB_Z + 0.75), (0, sy * 0.25, HZ), 0.07, WHITE, segs=6, bone=B)
m.box((0.4, 0.8, 0.3), (0, 0, HZ), GRAPH, bone=B)
m.cyl((0, 0, HZ + 0.15), (0, 0, HZ + 0.55), 0.04, STEEL, segs=6, bone=B)
m.cyl((0, 0, HZ + 0.55), (0, 0, HZ + 0.7), 0.11, P['red'], segs=8, bone=B)           # warning beacon (red paint)
for sy in (-1, 1):
    m.cyl((0, sy * 0.25, HZ), (JIB_L * 0.72, sy * 0.3, JIB_Z + 0.75), 0.03, STEEL, segs=4, bone=B)
    m.cyl((0, sy * 0.25, HZ), (-CJ_L + 0.4, sy * 0.3, JIB_Z + 0.65), 0.03, STEEL, segs=4, bone=B)
# jib: triangular truss (2 bottom chords + 1 top chord), white, cyan strip under the walkway side
JW, JH = 0.8, 0.75
def chord(a, b, r, col): m.cyl(a, b, r, col, segs=6, bone=B)
for sy in (-1, 1): m.box((JIB_L, 0.1, 0.12), (JIB_L / 2, sy * JW / 2, JIB_Z + 0.06), WHITE, bone=B)
m.box((JIB_L, 0.12, 0.1), (JIB_L / 2, 0, JIB_Z + JH), WHITE, bone=B)
NJ = 10; jp = JIB_L / NJ
for k in range(NJ):
    x0, x1 = k * jp, (k + 1) * jp
    for sy in (-1, 1):
        chord((x0 if k % 2 == 0 else x1, sy * JW / 2, JIB_Z + 0.08), (x1 if k % 2 == 0 else x0, 0, JIB_Z + JH), 0.035, GRAPH)
    m.box((0.06, JW, 0.06), (x1, 0, JIB_Z + 0.06), GRAPH, bone=B)
m.box((JIB_L - 1.0, 0.02, 0.04), (JIB_L / 2 + 0.3, -JW / 2 - 0.06, JIB_Z + 0.05), P['cyan'], mat=1, bone=B)
m.box((JIB_L - 1.0, 0.02, 0.04), (JIB_L / 2 + 0.3, JW / 2 + 0.06, JIB_Z + 0.05), P['cyan'], mat=1, bone=B)
m.box((0.3, JW + 0.2, JH + 0.15), (JIB_L + 0.1, 0, JIB_Z + JH / 2), GRAPH, bone=B)     # jib tip end stop
for k, x in enumerate((3.0, 5.5, 8.0)): m.box((0.5, 0.02, 0.18), (x, -JW / 2 - 0.06, JIB_Z + 0.4), P['amber'] if k == 1 else WHITE2, bone=B)
# counter-jib + counterweights + hoist winch
for sy in (-1, 1): m.box((CJ_L, 0.12, 0.3), (-CJ_L / 2, sy * 0.5, JIB_Z + 0.15), WHITE, bone=B)
m.box((CJ_L - 0.4, 1.1, 0.05), (-CJ_L / 2, 0, JIB_Z + 0.32), GRAPH, bone=B)             # walkway
for k in range(3): m.box((0.42, 1.5, 1.3), (-CJ_L + 0.3 + k * 0.46, 0, JIB_Z - 0.35), lin('#8d9096') if k != 1 else lin('#7d8086'), bone=B)
m.box((1.3, 0.02, 0.05), (-CJ_L + 0.76, -0.76, JIB_Z - 0.0), P['cyan'], mat=1, bone=B)
m.box((1.0, 0.9, 0.7), (-1.5, 0, JIB_Z + 0.7), WHITE, bone=B)                           # winch house
m.cyl((-1.5, -0.35, JIB_Z + 0.72), (-1.5, 0.35, JIB_Z + 0.72), 0.3, GRAPH, segs=10, bone=B)
for sy in (-1, 1): m.box((0.05, 0.05, 1.0), (-CJ_L + 0.05, sy * 0.55, JIB_Z + 0.8), lin('#ffb020'), bone=B)   # handrail posts
m.box((0.05, 1.15, 0.05), (-CJ_L + 0.05, 0, JIB_Z + 1.3), lin('#ffb020'), bone=B)
# ---- trolley (bone Trolley, origin at trolley centre on the jib bottom chord)
T = 'Trolley'
m.box((1.0, JW + 0.3, 0.32), (0, 0, JIB_Z - 0.16), GRAPH, bone=T)
m.box((0.9, JW + 0.32, 0.06), (0, 0, JIB_Z - 0.33), WHITE, bone=T)
for sx in (-1, 1):
    m.cyl((sx * 0.3, -JW / 2 - 0.15, JIB_Z + 0.1), (sx * 0.3, JW / 2 + 0.15, JIB_Z + 0.1), 0.1, STEEL, segs=6, bone=T)
m.box((0.6, 0.02, 0.04), (0, -JW / 2 - 0.16, JIB_Z - 0.16), P['cyan'], mat=1, bone=T)
m.cyl((0, -0.15, SHEAVE_Z), (0, 0.15, SHEAVE_Z), 0.16, STEEL, segs=8, bone=T)          # sheave
# ---- hoist cable (bone Hoist, 1 m long at rest, pointing down from the sheave; scale.y = cable length)
for sx in (-0.07, 0.07): m.cyl((sx, 0, SHEAVE_Z), (sx, 0, SHEAVE_Z - 1.0), 0.022, P['cable'], segs=4, bone='Hoist', caps=False)
# ---- hook block + rigid spreader (bone Hook; Hook joint = spreader underside = the box's Hook_Point)
H = 'Hook'
m.box((0.5, 0.36, 0.42), (0, 0, HOOK_DROP - 0.21), lin('#ffb020'), bone=H)                # amber hook block
m.cyl((-0.15, 0, HOOK_DROP - 0.1), (0.15, 0, HOOK_DROP - 0.1), 0.17, GRAPH, segs=8, bone=H)
m.box((0.08, 0.08, 0.22), (0, 0, HOOK_DROP - 0.53), STEEL, bone=H)
for sx in (-1, 1):
    for sy in (-1, 1):
        m.cyl((0, 0, HOOK_DROP - 0.62), (sx * 1.0, sy * 0.52, 0.12), 0.02, STEEL, segs=4, bone=H)
m.box((2.1, 0.14, 0.12), (0, -0.52, 0.06), GRAPH, bone=H); m.box((2.1, 0.14, 0.12), (0, 0.52, 0.06), GRAPH, bone=H)
m.box((0.14, 1.18, 0.12), (-1.0, 0, 0.06), GRAPH, bone=H); m.box((0.14, 1.18, 0.12), (1.0, 0, 0.06), GRAPH, bone=H)
m.box((1.6, 0.02, 0.03), (0, -0.6, 0.07), P['cyan'], mat=1, bone=H)
for sx in (-1, 1):
    for sy in (-1, 1): m.box((0.16, 0.16, 0.08), (sx * 1.0, sy * 0.52, 0.02), lin('#ffb020'), bone=H)   # twistlock pads
# ---- 8-box pallet (static, Crane_Base), east of the pedestal in the median: 2 x 2 footprint, stacked 2 high
PS = -1                                    # pallet side: -1 = west of the mast (crane-local -X), so the mast and pallet stay clear of FB-05 in the game camera
PAD_H = 0.12                               # concrete pad under the pallet (static, Crane_Base, SHM_Paint: no extra draw)
PAL_X = (PS * 4.8, PS * 7.3); PAL_Z = (-0.725, 0.725); PAL_TOP = PAD_H + 0.15; BOX_H_ = 1.5        # glTF slot centres, deck top (pallet sits on the pad)
PCX, PL, PW = PS * 6.05, 5.4, 3.2
# ---- concrete pad: 6.15 x 3.36 m slab, 0.12 m high, 0.04 m bevel, edge wear as per-face vertex colour (lighter chipped arrises, darker scuffs)
PX0, PX1, PY, BV = PS * 9.15, PS * 3.0, 1.68, 0.04          # x extents (crane-local, world 301.85..308.0 with the root at 311), half width (median is +-1.7), bevel
PXA, PXB = min(PX0, PX1), max(PX0, PX1)
CON, CON_TOP, CON_SIDE = lin('#a3a5a4'), lin('#aeb0ae'), lin('#8c8e8c')
WEAR_LO, WEAR_HI = lin('#c2c1ba'), lin('#7b7c78')
def pad_ring(x0, x1, y0, y1, z): return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
o = pad_ring(PXA, PXB, -PY, PY, 0.0); oh = pad_ring(PXA, PXB, -PY, PY, PAD_H - BV); it = pad_ring(PXA + BV, PXB - BV, -PY + BV, PY - BV, PAD_H)
m.quad(it, CON_TOP)                                                                             # top
for i in range(4):
    j = (i + 1) % 4
    m.quad([o[i], o[j], oh[j], oh[i]], CON_SIDE)                                                # vertical sides
    a0, a1, b0, b1 = Vector(oh[i]), Vector(oh[j]), Vector(it[i]), Vector(it[j])
    nseg = 4 if i in (0, 2) else 1                                                              # long sides split for wear variation
    wear = [CON, WEAR_LO, CON, WEAR_HI] if i == 0 else [WEAR_HI, CON, WEAR_LO, CON] if i == 2 else [WEAR_LO if i == 1 else CON]
    for k in range(nseg):
        t0, t1 = k / nseg, (k + 1) / nseg
        m.quad([a0.lerp(a1, t0), a0.lerp(a1, t1), b0.lerp(b1, t1), b0.lerp(b1, t0)], wear[k])  # bevel
for yb in (-1.1, 0.0, 1.1): m.box((PL, 0.32, 0.09), (PCX, yb, PAD_H + 0.045), GRAPH)                  # skids
m.box((PL, PW, 0.06), (PCX, 0, PAD_H + 0.12), lin('#8d9096'))                                           # deck plate
for xb in (PS * 3.6, PS * 6.05, PS * 8.5): m.box((0.1, PW + 0.02, 0.02), (xb, 0, PAD_H + 0.155), STEEL)             # deck straps
m.box((PL - 0.4, 0.02, 0.04), (PCX, -PW / 2 - 0.005, PAD_H + 0.10), P['cyan'], mat=1)                  # cyan edge strip (camera side, glTF +z)
for k in range(8): m.box((0.28, 0.02, 0.05), (PS * (3.6 + k * 0.66), PW / 2 + 0.005, PAD_H + 0.10), lin('#ffb020'))   # amber hazard dashes (back edge)
for sx in (PS * 3.45, PS * 8.65):
    for sy in (-1.5, 1.5):                                                                      # corner stacking guides (L posts)
        m.box((0.14, 0.05, 0.62), (sx, sy + (0.045 if sy > 0 else -0.045), PAD_H + 0.46), WHITE)
        m.box((0.05, 0.14, 0.62), (sx + (0.045 if abs(sx) > 6 else -0.045) * PS, sy, PAD_H + 0.46), WHITE)
        m.box((0.16, 0.16, 0.03), (sx, sy, PAD_H + 0.78), lin('#ffb020'))
m.weather(seed=11, z0=0.0, z1=3.0, amt=0.45, noise=0.06)
print('CRANE TRIS', m.tris())

# ---------------------------------------------------------------- armature (bones point +Z so glTF joint rest rotation = identity)
ad = bpy.data.armatures.new('Crane_Armature'); arm = bpy.data.objects.new('Crane_Refinery', ad); sc.collection.objects.link(arm)
sc.collection.objects.link  # noqa
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='EDIT')
def bone(n, head, parent=None):
    eb = ad.edit_bones.new(n); eb.head = head; eb.tail = Vector(head) + Vector((0, 0, 0.5)); eb.roll = 0
    if parent: eb.parent = ad.edit_bones[parent]
    return eb
bone('Crane_Base', (0, 0, 0)); bone('Slew', (0, 0, SLEW_Z), 'Crane_Base')
bone('Trolley', (TR_MIN, 0, JIB_Z), 'Slew'); bone('Hoist', (TR_MIN, 0, SHEAVE_Z), 'Trolley')
bone('Hook', (TR_MIN, 0, SHEAVE_Z - 1.0 - HOOK_DROP), 'Trolley')
bpy.ops.object.mode_set(mode='OBJECT')
ob = m.build('Crane_Mesh')
# geometry was modelled with trolley / hoist / hook parts at x 0 and the hook at z 0: move them to their rest joints
import bmesh
REST = {'Trolley': Vector((TR_MIN, 0, 0)), 'Hoist': Vector((TR_MIN, 0, 0)), 'Hook': Vector((TR_MIN, 0, SHEAVE_Z - 1.0 - HOOK_DROP))}
gi = {g.index: g.name for g in ob.vertex_groups}
for v in ob.data.vertices:
    g = gi[v.groups[0].group]
    if g in REST: v.co += REST[g]
if 'root' in ob.vertex_groups: ob.vertex_groups['root'].name = 'Crane_Base'
ob.parent = arm; md = ob.modifiers.new('Armature', 'ARMATURE'); md.object = arm

# ---------------------------------------------------------------- markers (glTF metres, crane-local; Blender (x, y, z) = glTF (x, -z, y))
def g2b(x, y, z): return (x, -z, y)
# Director layout (world): flatbed lanes z 13 (eastbound, +X) and z 22 (westbound); FB-05 loads at x 318 on z 13.
# Crane root at world (311, 0, 17.5) in the median: with the Refinery game camera (Cam_Target (314.1, 8.5, 3.36), frame_w 30.8) the mast
# then projects left of the FB-05 tail, so neither bed slot nor the cab is behind the mast (at x 318 the mast hid 27% of a box on Bed_Slot_01).
PSLOTS = [(x, PAL_TOP + lvl * BOX_H_, z) for lvl in (0, 1) for z in PAL_Z for x in PAL_X]     # 01-04 bottom, 05-08 top
PICK = PSLOTS[0]                  # Pick_Point = Pallet_Slot_01 (over the pallet); aim at any Pallet_Slot_NN the same way
PROOF_PICK = PSLOTS[4]            # proof clip cycle 1 lifts the top box over slot 01 (Pallet_Slot_05) onto Bed_Slot_01
PROOF_PICK2 = PSLOTS[5]           # cycle 2: Pallet_Slot_06 onto Bed_Slot_02
CRANE_WORLD = (311.0, 0.0, 17.5)
TRUCK = (318.0 - CRANE_WORLD[0], 0.0, 13.0 - CRANE_WORLD[2])   # glTF (7, 0, -4.5): FB-05 root at Truck_Park = world (318, 0, 13), heading +X
SLOTS = [(TRUCK[0] - 1.15, 1.9, TRUCK[2]), (TRUCK[0] - 3.65, 1.9, TRUCK[2])]
BOX_H = 1.5
def solve(x, y_hook, z):
    th = math.atan2(-z, x); r = math.hypot(x, z); cable = (SHEAVE_Z) - y_hook - HOOK_DROP
    return th, r, cable
empty('Pick_Point', g2b(*PICK), parent=arm, extras={'kind': 'crane_target', 'box_base': True, 'slot': 'Pallet_Slot_01',
      'note': 'over the pallet = Pallet_Slot_01; box Base sits here; hook target = slot + (0, box hook_offset_y 1.5, 0). Any Pallet_Slot_NN works the same way'})
for i, ps in enumerate(PSLOTS):
    empty('Pallet_Slot_%02d' % (i + 1), g2b(*ps), parent=arm, extras={'kind': 'pallet_slot', 'box_base': True, 'level': i // 4,
          'note': '01-04 bottom layer (y 0.27, pallet deck on the 0.12 m concrete pad), 05-08 top layer (y 1.77, sits on 01-04); fill 01..08, pick 08..01; box yaw 0 (long axis +X)'})
empty('Drop_Point', g2b(*SLOTS[0]), parent=arm, extras={'kind': 'crane_target', 'box_base': True, 'slot': 'Bed_Slot_01',
      'note': 'FB-05 Bed_Slot_01 when the truck is parked at Truck_Park (box Base lands here); Drop_Point_02 = Bed_Slot_02'})
empty('Drop_Point_02', g2b(*SLOTS[1]), parent=arm, extras={'kind': 'crane_target', 'box_base': True, 'slot': 'Bed_Slot_02'})
empty('Truck_Park', g2b(*TRUCK), parent=arm, extras={'kind': 'truck_pose', 'yaw_deg': 0, 'truck': 'FB-05',
      'note': 'FB-05 root pose while loading (heading +X); its Bed_Slot_01/02 then match Drop_Point / Drop_Point_02'})
LIM = {'slew_min_rad': -math.pi, 'slew_max_rad': math.pi, 'trolley_min_m': TR_MIN, 'trolley_max_m': TR_MAX,
       'hoist_min_m': round(CABLE_MIN, 3), 'hoist_max_m': round(CABLE_MAX, 3)}
arm['prop'] = 'RC-1 Refinery loading crane (slewing jib crane on a pedestal)'
arm['origin'] = 'ground centre of the pedestal, +Y up; jib points +X at Slew = 0'
arm['world_position'] = list(CRANE_WORLD); arm['world_yaw_deg'] = 0
arm['concrete_pad'] = {'min': [PXA, 0.0, -PY], 'max': [PXB, PAD_H, PY], 'note': 'static concrete pad under the pallet (crane-local glTF bbox, 0.04 m bevel); pallet deck sits on it, Pallet_Slot_* raised by PAD_H'}
arm['layout_note'] = ('place the root at world (311, 0, 17.5), yaw 0 (median of the flatbed road, lanes z 13 / z 22). FB-05 parks at world (318, 0, 13) = Truck_Park. '
                      'Pallet west of the mast (world x 302.25-307.65). Chosen so the Refinery game camera sees both bed slots and the cab clear of the mast')
arm.update(LIM) if hasattr(arm, 'update') else None
for k, v in LIM.items(): arm[k] = v
arm['hook_drop_m'] = HOOK_DROP; arm['sheave_y'] = SHEAVE_Z; arm['slew_y'] = SLEW_Z; arm['jib_y'] = JIB_Z
arm['joints'] = ('Slew: rotation.y = theta (rad) about +Y, jib direction (cos theta, 0, -sin theta). Trolley: position.x = r (m from the mast axis). '
                 'Hoist: scale.y = cable length L (m), cable hangs from the sheave. Hook: position.y = rest_y + 1 - L, i.e. Hook world y = sheave_y - L - hook_drop_m; '
                 'Hook.rotation.y = box_yaw - theta (hook rotator; box_yaw 0 keeps the box long axis on crane +X, as on Pick_Point and on FB-05 at Truck_Park). '
                 'Solve for a hook target (x, y, z) in crane space: theta = atan2(-z, x), r = hypot(x, z), L = sheave_y - y - hook_drop_m.')
arm['hook_rest_local_y'] = round(SHEAVE_Z - 1.0 - HOOK_DROP - JIB_Z, 4)

# ---------------------------------------------------------------- optional proof clip crane_load (6 s @ 30 fps, first key == last key)
def smooth(t): t = min(max(t, 0.0), 1.0); return t * t * t * (t * (6 * t - 15) + 10)
HOVER = 6.2
def cyc(t0, pick, drop, th_prev):
    Pth, Pr, _ = solve(pick[0], 0, pick[2]); Dth, Dr, _ = solve(drop[0], 0, drop[2])
    while Pth - th_prev > math.pi: Pth -= math.tau
    while th_prev - Pth > math.pi: Pth += math.tau
    while Dth - Pth > math.pi: Dth -= math.tau
    while Pth - Dth > math.pi: Dth += math.tau
    return [(t0 + 0.0, Pth, Pr, HOVER), (t0 + 0.9, Pth, Pr, pick[1] + BOX_H), (t0 + 1.3, Pth, Pr, pick[1] + BOX_H), (t0 + 2.1, Pth, Pr, HOVER),
            (t0 + 3.3, Dth, Dr, HOVER), (t0 + 4.1, Dth, Dr, drop[1] + BOX_H), (t0 + 4.5, Dth, Dr, drop[1] + BOX_H), (t0 + 5.0, Dth, Dr, HOVER)]
K1 = cyc(0.0, PROOF_PICK, SLOTS[0], 0.0); K2 = cyc(6.0, PROOF_PICK2, SLOTS[1], K1[-1][1])
KEYS = K1 + K2 + [(12.0,) + K1[0][1:]]
CLIP_S = 12.0
def state(t):
    for (t0, a0, r0, h0), (t1, a1, r1, h1) in zip(KEYS, KEYS[1:]):
        if t <= t1 + 1e-9:
            u = smooth((t - t0) / (t1 - t0)); return a0 + (a1 - a0) * u, r0 + (r1 - r0) * u, h0 + (h1 - h0) * u
    return KEYS[-1][1:]
if CLIP: arm['crane_load_schedule'] = ('proof-only clip (not in the shipped GLB), 12 s: cycle 1 (0-6 s) Pallet_Slot_05 -> Drop_Point (Bed_Slot_01), cycle 2 (6-12 s) '
                              'Pallet_Slot_06 -> Drop_Point_02 (Bed_Slot_02). Per cycle: 0.9 s down, 0.9-1.3 latch, 2.1 lifted, 3.3 over the slot, 4.1 landed, 4.1-4.5 release, 5.0 up; box attached 0.9-4.5 s')
def pose_at(t):
    th, r, hy = state(t); L = SHEAVE_Z - hy - HOOK_DROP
    pb = arm.pose.bones
    pb['Slew'].rotation_mode = 'XYZ'
    # bone local Y = world Z (up): yaw about up = rotation about bone Y
    pb['Slew'].rotation_euler = (0, th, 0)
    pb['Trolley'].location = (r - TR_MIN, 0, 0)        # bone local X = world X
    pb['Hoist'].scale = (1, L, 1)                       # bone local Y = world up
    pb['Hook'].location = (0, 1.0 - L, 0)
    pb['Hook'].rotation_mode = 'XYZ'; pb['Hook'].rotation_euler = (0, -th, 0)   # hook rotator: keeps the box at world yaw 0 (aligned with Pick pad + truck)
    return th, r, L
if CLIP:
    act = bpy.data.actions.new('crane_load'); arm.animation_data_create(); arm.animation_data.action = act
    for f in range(0, int(CLIP_S * 30) + 1):
        pose_at(f / 30.0)
        for bn, path in (('Slew', 'rotation_euler'), ('Trolley', 'location'), ('Hoist', 'scale'), ('Hook', 'location'), ('Hook', 'rotation_euler')):
            arm.pose.bones[bn].keyframe_insert(path, frame=f)
    sc.frame_start, sc.frame_end = 0, int(CLIP_S * 30)
    for fc in act.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    bpy.context.view_layer.update()
    arm.animation_data.action = None
    tr = arm.animation_data.nla_tracks.new(); tr.name = 'crane_load'; tr.strips.new('crane_load', 0, act)
for pb in arm.pose.bones: pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
sc.frame_set(0)
export(OUT, anim=CLIP)
print('WROTE', OUT, 'PICK', solve(PICK[0], PICK[1] + BOX_H, PICK[2]), 'DROP', solve(SLOTS[0][0], SLOTS[0][1] + BOX_H, SLOTS[0][2]))
