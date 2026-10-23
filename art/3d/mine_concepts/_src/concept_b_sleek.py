"""Concept B - SLEEK HIGH-TECH Mine A. blender -b -P concept_b_sleek.py -- --out DIR [--quick 1] [--only glb,blend,turn,hero]"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
from mc_common import *
from mc_common import _obj, _nodes

A = argv(); OUT = A.get('out', '/tmp/mc_b'); os.makedirs(OUT, exist_ok=True)
QUICK = A.get('quick') == '1'
reset(); rr = random.Random(42)
TAU = math.tau

# ---------------- materials
WHITE = M_paint('B_White', '#eceff2', rough=0.22, metal=0.0, grime=0.18, grime_col='#a59f97', panel=0.8, coat=0.8, bevel=0.03, dirt_scale=1.4)
WHITE_S = M_paint('B_WhiteSmooth', '#eef1f4', rough=0.2, metal=0.0, grime=0.12, grime_col='#a59f97', coat=0.9, bevel=0.03)
GRAPH = M_paint('B_Graphite', '#2c3137', rough=0.3, metal=0.55, grime=0.1, coat=0.5, bevel=0.02, panel=1.4)
GRAPH_S = M_paint('B_GraphiteSmooth', '#30353c', rough=0.28, metal=0.6, coat=0.5, bevel=0.02)
SATIN = M_paint('B_Satin', '#9aa3ad', rough=0.25, metal=1.0, bevel=0.01)
TIRE = M_paint('B_Tire', '#24272b', rough=0.7, metal=0.1, grime=0.35, grime_col='#7a756e', bump_noise=0.25)
BELT = M_paint('B_Belt', '#1d2024', rough=0.8, metal=0.0, grime=0.25, grime_col='#6e6a64')
INK = M_paint('B_Ink', '#1f2329', rough=0.5, metal=0.0)
INKW = M_paint('B_InkWhite', '#f4f7fa', rough=0.4, metal=0.0)
CYAN = M_glow('B_Cyan', '#2fe3ff', 16)
CYANS = M_glow('B_CyanSoft', '#2fe3ff', 5)
LAMP = M_glow('B_Lamp', '#f2fbff', 25)
GLASS = M_glass('B_Visor', '#1b2a36', 0.04)
HE3 = M_he3('B_He3'); PT = M_paint('B_Platinum', '#d8dde4', rough=0.16, metal=1.0, bevel=0.005)
ROCK = M_rock('B_OreRock', '#5d5a57', '#86827c', vein='#3ad0ff')
ORE_MIX = [(HE3, 4, 'he3'), (PT, 2, 'pt'), (ROCK, 5, 'rock')]

def M_plasma(name, color, strength, alpha):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
    mx = nt.nodes.new('ShaderNodeMixShader'); mt = nt.nodes.new('ShaderNodeMath'); mt.operation = 'MULTIPLY'
    em.inputs['Color'].default_value = hexc(color); em.inputs['Strength'].default_value = strength
    nt.links.new(lw.outputs['Facing'], mt.inputs[0]); mt.inputs[1].default_value = alpha
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(mt.outputs[0], inv.inputs[1])
    nt.links.new(inv.outputs[0], mx.inputs['Fac']); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface']); m.diffuse_color = hexc(color); m.blend_method = 'BLEND'
    return m
PLASMA_CORE = M_glow('B_PlasmaCore', '#e8fdff', 60)
PLASMA_HALO = M_plasma('B_PlasmaHalo', '#38dcff', 9, 0.0)

def lathe(name, prof, loc, mat, segs=48, bevel=0.0, scale=(1, 1, 1), smooth=True):
    """surface of revolution around Z. prof=[(r,z),...] bottom->top; r==0 points become poles."""
    bm = bmesh.new(); rings = []
    for (r, z) in prof:
        if r < 1e-5: rings.append([bm.verts.new((loc[0], loc[1], loc[2] + z))])
        else:
            rings.append([bm.verts.new((loc[0] + r * math.cos(TAU * k / segs) * scale[0], loc[1] + r * math.sin(TAU * k / segs) * scale[1], loc[2] + z)) for k in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for k in range(segs):
            k2 = (k + 1) % segs
            if len(a) == 1: bm.faces.new((a[0], b[k], b[k2]))
            elif len(b) == 1: bm.faces.new((a[k], a[k2], b[0]))
            else: bm.faces.new((a[k], a[k2], b[k2], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(bm, name, mat, smooth=smooth, bevel=bevel, angle=50)

def ring(name, r, z_or_loc, h, mat, w=0.06, segs=64):
    x, y, z = z_or_loc
    return lathe(name, [(r - w, z - h / 2), (r, z - h / 2), (r, z + h / 2), (r - w, z + h / 2), (r - w, z - h / 2)], (x, y, 0), mat, segs=segs, smooth=True)

def rbox(name, size, loc, mat, rot=(0, 0, 0), r=0.2, segs=5):
    return box(name, size, loc, mat, rot=rot, bevel=r, segs=segs)

def bez(p0, p1, p2, n):
    p0, p1, p2 = Vector(p0), Vector(p1), Vector(p2)
    return [((1 - t) ** 2) * p0 + 2 * (1 - t) * t * p1 + (t ** 2) * p2 for t in [i / n for i in range(n + 1)]]

# ================= PLASMA BORE RIG =================
RX, RY = -7.5, 3.0; RYc = RY + 0.6
lathe('pad', [(0, 0.0), (4.3, 0.0), (4.3, 0.35), (4.1, 0.6), (0, 0.6)], (RX, RY, 0), WHITE, segs=72, bevel=0.03)
ring('pad_glow', 4.32, (RX, RY, 0.22), 0.07, CYAN, w=0.03, segs=96)
lathe('pad_skirt', [(0, -0.05), (4.45, -0.05), (4.45, 0.1), (0, 0.1)], (RX, RY, 0), GRAPH, segs=72)
lathe('deck', [(0, 0.6), (3.7, 0.6), (3.7, 0.64), (0, 0.64)], (RX, RY, 0), GRAPH, segs=72)
# landing struts
for k in range(6):
    a = TAU * k / 6 + 0.26
    p0 = Vector((RX + 3.6 * math.cos(a), RY + 3.6 * math.sin(a), 0.45)); p1 = Vector((RX + 5.6 * math.cos(a), RY + 5.6 * math.sin(a), 0.22))
    rod('strut', p0, p1, 0.17, GRAPH_S, r2=0.12, segs=20)
    lathe('strut_foot', [(0, 0), (0.62, 0), (0.62, 0.06), (0.45, 0.16), (0, 0.18)], (p1.x, p1.y, 0), WHITE_S, segs=32)
    ring('foot_glow', 0.63, (p1.x, p1.y, 0.04), 0.03, CYAN, w=0.02, segs=32)
# arch legs
LEG_B, LEG_T, ZB, ZT = 2.6, 1.7, 0.6, 15.4
for s in (-1, 1):
    p0 = Vector((RX + s * LEG_B, RYc, ZB)); p1 = Vector((RX + s * LEG_T, RYc, ZT))
    beam('leg', p0, p1, 1.3, 0.9, WHITE, bevel=0.22)
    box('leg_foot', (1.4, 1.8, 0.5), (RX + s * LEG_B, RYc, 0.85), GRAPH, bevel=0.15, segs=4)
    inn = Vector((-s * 0.55, 0, 0))
    beam('rail', p0 + inn + Vector((0, 0, 0.3)), p1 + inn, 0.6, 0.25, GRAPH_S, bevel=0.05)
    beam('leg_strip', p0 + Vector((0, -0.66, 0.6)), p1 + Vector((0, -0.66, -0.4)), 0.03, 0.12, CYAN, bevel=0.0)
    beam('leg_strip_b', p0 + Vector((0, 0.66, 0.6)), p1 + Vector((0, 0.66, -0.4)), 0.03, 0.12, CYANS, bevel=0.0)
    for z in (3.0, 6.0, 9.0, 12.0):  # panel seams / sensor pods
        t = (z - ZB) / (ZT - ZB); x = RX + s * (LEG_B + (LEG_T - LEG_B) * t)
        box('leg_band', (0.95, 1.34, 0.08), (x, RYc, z), GRAPH, bevel=0.02, rot=(0, s * 0.06, 0))
crown_c = (RX, RYc, 16.1)
rbox('crown', (4.8, 2.0, 1.5), crown_c, WHITE, r=0.45, segs=6)
box('crown_strip', (4.2, 0.03, 0.1), (RX, RYc - 1.01, 16.1), CYAN, bevel=0)
box('crown_band', (4.84, 2.04, 0.12), (RX, RYc, 15.55), GRAPH, bevel=0.04)
text('decal_crown', 'BORE 01  ·  PLASMA', (RX, RYc - 1.005, 16.45), (math.pi / 2, 0, 0), 0.28, INK, extrude=0.004)
rod('antenna', (RX + 1.6, RYc + 0.4, 16.8), (RX + 1.6, RYc + 0.4, 19.0), 0.04, SATIN, segs=10)
sphere('ant_tip', 0.1, (RX + 1.6, RYc + 0.4, 19.05), CYAN, sub=2)
lathe('dish', [(0, 0), (0.55, 0.18), (0.6, 0.2), (0.05, 0.03)], (RX - 1.4, RYc + 0.3, 17.0), WHITE_S, segs=40)
rod('dish_post', (RX - 1.4, RYc + 0.3, 16.75), (RX - 1.4, RYc + 0.3, 17.02), 0.06, GRAPH_S)
sphere('beacon', 0.16, (RX, RYc, 16.95), CYAN, sub=2)
for s in (-1, 1):
    rbox('flood', (0.5, 0.4, 0.3), (RX + s * 1.9, RYc - 1.05, 15.2), GRAPH_S, r=0.08, segs=3, rot=(-0.4, 0, 0))
    box('flood_lens', (0.4, 0.02, 0.2), (RX + s * 1.9, RYc - 1.25, 15.12), LAMP, rot=(-0.4, 0, 0), bevel=0)
# carriage + enclosed bore head
rbox('carriage', (3.0, 1.7, 1.0), (RX, RYc, 8.65), WHITE, r=0.3, segs=5)
box('carriage_strip', (2.4, 0.03, 0.08), (RX, RYc - 0.86, 8.4), CYAN, bevel=0)
text('decal_mine', 'MINE A-01', (RX, RYc - 0.86, 8.85), (math.pi / 2, 0, 0), 0.32, INK, extrude=0.005)
prof = [(0, 8.15), (0.9, 8.15), (1.2, 7.9), (1.3, 7.4), (1.3, 4.2), (1.15, 3.3), (0.85, 2.75), (0.55, 2.5), (0.5, 2.45), (0, 2.45)]
lathe('bore_housing', prof, (RX, RYc, 0), WHITE, segs=64, bevel=0.0)
for z in (6.9, 5.2):
    ring('bore_glow', 1.315, (RX, RYc, z), 0.09, CYAN, w=0.04)
    ring('bore_band', 1.33, (RX, RYc, z + 0.18), 0.14, GRAPH, w=0.06)
# inspection window into the bore chamber
box('bore_window', (0.7, 0.05, 1.4), (RX, RYc - 1.3, 4.6), CYANS, bevel=0.02)
box('bore_window_frame', (0.86, 0.06, 1.56), (RX, RYc - 1.27, 4.6), GRAPH, bevel=0.03)
lathe('nozzle', [(0, 1.6), (0.18, 1.6), (0.34, 1.9), (0.5, 2.46), (0, 2.46)], (RX, RYc, 0), GRAPH_S, segs=48)
ring('nozzle_glow', 0.25, (RX, RYc, 1.72), 0.06, CYAN, w=0.03, segs=40)
# plasma beam into the bore collar
cyl('plasma_core', 0.07, 1.4, (RX, RYc, 0.95), PLASMA_CORE, segs=24, bevel=0)
cyl('plasma_halo', 0.45, 1.5, (RX, RYc, 0.95), PLASMA_HALO, segs=32, bevel=0, r2=0.18)
lathe('collar', [(0.55, 0.6), (1.2, 0.6), (1.2, 0.78), (1.05, 0.9), (0.6, 0.9), (0.55, 0.6)], (RX, RYc, 0), GRAPH_S, segs=64)
ring('collar_glow', 0.62, (RX, RYc, 0.8), 0.05, CYAN, w=0.03)
lathe('melt_pool', [(0, 0.66), (0.55, 0.66), (0, 0.67)], (RX, RYc, 0), M_glow('B_Melt', '#9ff1ff', 30), segs=40)
for k in range(10):   # sparks/ejecta
    a = rr.uniform(0, TAU); d = rr.uniform(0.7, 1.3)
    sphere('ejecta', rr.uniform(0.02, 0.05), (RX + d * math.cos(a), RYc + d * math.sin(a), 0.95 + rr.uniform(0, 0.5)), PLASMA_CORE, sub=1)
# plasma glow light + cross brace
pl = bpy.data.lights.new('PlasmaLight', 'POINT'); pl.energy = 220; pl.color = hexc('#5fe6ff')[:3]; pl.shadow_soft_size = 0.3
plo = bpy.data.objects.new('PlasmaLight', pl); coll('Mine').objects.link(plo); plo.location = (RX, RYc - 0.2, 1.2)
for zc in (12.6,):
    t = (zc - ZB) / (ZT - ZB); xx = LEG_B + (LEG_T - LEG_B) * t - 0.3
    rbox('cross_brace', (2 * xx, 1.0, 0.7), (RX, RYc, zc), WHITE, r=0.25, segs=4)
    box('cross_strip', (2 * xx - 0.6, 0.03, 0.08), (RX, RYc - 0.51, zc), CYAN, bevel=0)
    text('decal_brace', 'A-01', (RX, RYc - 0.505, zc + 0.08), (math.pi / 2, 0, 0), 0.26, INK, extrude=0.004) if False else None
# umbilicals crown -> carriage -> housing
for s, dy in ((-1, -0.4), (1, 0.4), (1, -0.1)):
    cable('umbilical', (RX + s * 0.9, RYc + dy, 15.35), (RX + s * 0.9, RYc + dy, 9.15), 0.08 if dy else 0.06, GRAPH_S, sag=0.0, lateral=(s * 0.6, 0, 0))
    cable('umbilical', (RX + s * 0.8, RYc + dy, 8.15), (RX + s * 0.6, RYc + dy, 7.6), 0.06, GRAPH_S, sag=0.0, lateral=(s * 0.25, 0, 0))
# operator pod + power module on the pad
OPX, OPY = RX - 2.3, RY - 2.0
sphere('op_pod', 1.0, (OPX, OPY, 1.55), WHITE_S, scale=(1.4, 1.05, 0.85), sub=4)
sphere('op_visor', 0.82, (OPX + 0.38, OPY - 0.35, 1.68), GLASS, scale=(1.1, 0.9, 0.55), sub=4)
ring('op_glow', 1.42, (OPX, OPY, 1.12), 0.05, CYAN, w=0.03)
lathe('op_base', [(0, 0.62), (0.7, 0.62), (0.55, 0.9), (0, 0.95)], (OPX, OPY, 0), GRAPH_S, segs=40)
rbox('power', (2.4, 1.2, 1.1), (RX, RY + 3.0, 1.2), WHITE, r=0.3, segs=5)
for i in range(6): box('power_fin', (0.05, 1.24, 0.6), (RX - 0.9 + i * 0.36, RY + 3.0, 1.35), GRAPH, bevel=0.01)
box('power_strip', (2.0, 0.02, 0.06), (RX, RY + 2.39, 0.85), CYAN, bevel=0)
cable('power_cable', (RX + 1.1, RY + 2.6, 0.9), (RX + 2.2, RYc + 0.2, 1.1), 0.07, GRAPH_S, sag=0.25)
# enclosed transfer tube: bore -> hopper
H_X, H_Y = -1.0, 3.0
rbox('cyclone', (1.3, 1.3, 1.3), (RX + 1.9, RY - 1.2, 1.3), WHITE, r=0.4, segs=5)
ring('cyclone_glow', 0.66, (RX + 1.9, RY - 1.2, 1.3), 0.05, CYAN, w=0.02, segs=48)
tube = bez((RX + 2.4, RY - 1.1, 1.7), (RX + 4.0, RY - 0.9, 10.5), (H_X - 0.2, H_Y, 8.4), 40)
curve_tube('transfer_tube', [tuple(p) for p in tube], 0.38, WHITE_S, res=6)
curve_tube('transfer_strip', [tuple(p + Vector((0, -0.36, 0.06))) for p in tube[1:-1]], 0.035, CYAN, res=2)
for i in range(4, 40, 5):
    a, b = tube[i], tube[i + 1]; d = (b - a)
    rod('tube_collar', a - d * 0.3, a + d * 0.3, 0.42, GRAPH_S, segs=32)
rod('tube_drop', (H_X - 0.2, H_Y, 8.45), (H_X - 0.2, H_Y, 7.0), 0.3, GRAPH_S, segs=32)
mid = tube[20]
rod('tube_pylon', (mid.x, mid.y, 0.0), (mid.x, mid.y, mid.z - 0.35), 0.22, GRAPH_S, r2=0.16, segs=24)
lathe('pylon_foot', [(0, 0), (0.7, 0), (0.6, 0.15), (0, 0.2)], (mid.x, mid.y, 0), WHITE_S, segs=32)
rod('pylon_saddle', (mid.x, mid.y - 0.45, mid.z - 0.45), (mid.x, mid.y + 0.45, mid.z - 0.45), 0.12, GRAPH_S)

# ================= HOPPER POD =================
HZ_TOP = 7.25
lathe('hopper', [(0.38, 3.1), (0.42, 3.6), (1.9, 5.5), (2.3, 6.15), (2.3, 7.05), (2.18, HZ_TOP)], (H_X, H_Y, 0), WHITE, segs=72, bevel=0.0)
lathe('hopper_in', [(2.12, HZ_TOP), (2.2, 7.0), (2.2, 6.2), (1.8, 5.55), (0.35, 3.62)], (H_X, H_Y, 0), GRAPH, segs=72)
ring('hopper_rim', 2.22, (H_X, H_Y, HZ_TOP), 0.08, GRAPH_S, w=0.12)
ring('hopper_glow', 2.31, (H_X, H_Y, 6.85), 0.08, CYAN, w=0.03, segs=96)
ring('hopper_band', 2.32, (H_X, H_Y, 6.25), 0.16, GRAPH, w=0.06, segs=96)
ring('hopper_spout_glow', 0.43, (H_X, H_Y, 3.45), 0.06, CYAN, w=0.03, segs=32)
text('decal_hopper', 'H-1', (H_X, H_Y - 2.30, 6.55), (math.pi / 2, 0, 0), 0.34, INK, extrude=0.02)
heap('hop_heap', (H_X, H_Y, 6.55), 2.05, 0.75, ROCK, seed=4)
ore_chunks('hop', (H_X, H_Y, 6.75), 1.7, 80, ORE_MIX, heap=0.6, size=(0.14, 0.32), seed=5)
for k in range(3):
    a = math.radians(90 + 120 * k)
    p0 = Vector((H_X + 2.0 * math.cos(a), H_Y + 2.0 * math.sin(a), 5.6)); p1 = Vector((H_X + 3.1 * math.cos(a), H_Y + 3.1 * math.sin(a), 0.15))
    rod('hop_leg', p0, p1, 0.2, GRAPH_S, r2=0.14, segs=24)
    lathe('hop_foot', [(0, 0), (0.6, 0), (0.5, 0.14), (0, 0.18)], (p1.x, p1.y, 0), WHITE_S, segs=32)
    ring('hop_foot_glow', 0.61, (p1.x, p1.y, 0.05), 0.03, CYAN, w=0.02, segs=32)
    sphere('hop_knuckle', 0.26, tuple(p0), WHITE_S, sub=3)

# ================= HAUL TRUCK LAYOUT (Jacob: B + dump truck) =================
# drill -> sealed tube -> pod hopper -> underglow conveyor -> HT-04 dump truck bed -> road loop -> raised dump hopper -> lift tube -> ore silo
ARM_POSE = A.get('arm', 'stow')          # 'stow' (hero/master) or 'reach' (truck close-up)
TX, TY = 4.7, -4.5                        # truck centre on the ground, heading +X (cab toward the silo side of the loop)
def T(x, y, z): return Vector((TX + x, TY + y, z))
BED_C = T(-1.6, 0, 0)                     # dump-bed centre (discharge lands here)

# ================= UNDERGLOW CONVEYOR (hopper -> truck bed) =================
BIN_X, BIN_Y = 10.0, 4.5
C0 = Vector((H_X + 0.15, H_Y - 0.35, 2.55))
DIS = Vector((BED_C.x, BED_C.y, 0))
C1 = Vector((DIS.x, DIS.y, 5.55))
for _ in range(4):   # head end so the discharge (0.75 m past C1) sits over the bed centre
    uh = Vector((C1.x - C0.x, C1.y - C0.y, 0)).normalized(); C1 = Vector((DIS.x - uh.x * 0.75, DIS.y - uh.y * 0.75, 5.55))
d = C1 - C0; L = d.length; u = d.normalized(); side = Vector((0, 0, 1)).cross(u).normalized(); up = u.cross(side).normalized()
beam('trough_floor', C0 - up * 0.1, C1 - up * 0.1, 1.5, 0.16, WHITE, bevel=0.05)
for s in (-1, 1):
    beam('trough_wall', C0 + side * 0.78 * s + up * 0.22, C1 + side * 0.78 * s + up * 0.22, 0.1, 0.62, WHITE, bevel=0.04)
    beam('trough_strip', C0 + side * 0.84 * s + up * 0.38 + u * 0.4, C1 + side * 0.84 * s + up * 0.38 - u * 0.4, 0.02, 0.06, CYAN, bevel=0)
beam('underglow', C0 - up * 0.19 + u * 0.4, C1 - up * 0.19 - u * 0.4, 0.5, 0.03, CYAN, bevel=0)
beam('belt', C0 + up * 0.0, C1 + up * 0.0, 1.3, 0.05, BELT, bevel=0.005)
nh = int(L / 1.4)
for i in range(1, nh):   # graphite hoops half-enclosing the belt
    c = C0 + u * (L * i / nh); pts = []
    for k in range(17):
        a = math.pi * k / 16
        pts.append(tuple(c + side * 0.83 * math.cos(a) + up * (0.5 + 0.55 * math.sin(a))))
    curve_tube('hoop', pts, 0.05, GRAPH_S, res=3)
for i in range(40):
    t = rr.uniform(0.04, 0.96); p = C0 + u * (L * t) + up * 0.04 + side * rr.uniform(-0.45, 0.45)
    kind = rr.choices(['he3', 'pt', 'rock'], [5, 2, 3])[0]
    m = {'he3': HE3, 'pt': PT, 'rock': ROCK}[kind]
    ore_chunks('belt_ore', (p.x, p.y, p.z), 0.01, 1, [(m, 1, kind)], size=(0.15, 0.3), seed=i * 11 + 5)
for t in (0.2,):   # tail pylon (outside the road loop)
    p = C0 + u * (L * t) - up * 0.2
    rod('conv_pylon', (p.x, p.y, 0.0), (p.x, p.y, p.z - 0.15), 0.26, GRAPH_S, r2=0.18, segs=24)
    lathe('conv_foot', [(0, 0), (0.75, 0), (0.62, 0.16), (0, 0.2)], (p.x, p.y, 0), WHITE_S, segs=32)
    ring('conv_pylon_glow', 0.25, (p.x, p.y, 0.9), 0.06, CYAN, w=0.03, segs=32)
    beam('conv_saddle', p - side * 0.7 - up * 0.08, p + side * 0.7 - up * 0.08, 0.3, 0.2, GRAPH_S, bevel=0.05)
rbox('head_housing', (1.6, 1.9, 1.1), tuple(C1 + up * 0.25 + u * 0.3), WHITE, r=0.35, segs=5)
rbox('tail_housing', (1.2, 1.8, 0.8), tuple(C0 - u * 0.2 + up * 0.05), WHITE, r=0.3, segs=5)
# discharge chute over the truck bed + falling ore
CH_TOP = C1 + u * 0.75 - up * 0.2; CH_Z = 4.35
rod('dis_chute', (DIS.x, DIS.y, CH_TOP.z), (DIS.x, DIS.y, CH_Z), 0.34, GRAPH_S, r2=0.3, segs=40)
ring('dis_chute_glow', 0.31, (DIS.x, DIS.y, CH_Z + 0.12), 0.06, CYAN, w=0.03, segs=40)
ring('dis_chute_lip', 0.33, (DIS.x, DIS.y, CH_Z + 0.02), 0.06, WHITE_S, w=0.08, segs=40)
for i in range(16):
    z = rr.uniform(3.25, CH_Z - 0.05); j = 0.05 + 0.12 * (CH_Z - z)
    kind = rr.choices(['he3', 'pt', 'rock'], [5, 2, 4])[0]; m = {'he3': HE3, 'pt': PT, 'rock': ROCK}[kind]
    ore_chunks('fall_ore', (DIS.x + rr.uniform(-j, j), DIS.y + rr.uniform(-j, j), z), 0.01, 1, [(m, 1, kind)], size=(0.1, 0.22), seed=700 + i)
# cantilever support for the head end, footed outside the road loop (west of the loading bay)
PF = Vector((-0.4, TY - 1.1, 0.0)); PTOP = Vector((PF.x, PF.y, C1.z + 1.25))
rod('head_pylon', PF, PTOP, 0.3, GRAPH_S, r2=0.22, segs=28)
lathe('head_pylon_foot', [(0, 0), (0.85, 0), (0.7, 0.18), (0, 0.22)], (PF.x, PF.y, 0), WHITE_S, segs=36)
ring('head_pylon_glow', 0.29, (PF.x, PF.y, 1.0), 0.06, CYAN, w=0.03, segs=32)
HB = C1 + up * 1.15 + u * 0.3
beam('head_boom', PTOP, Vector((HB.x, HB.y, PTOP.z)), 0.5, 0.42, WHITE, bevel=0.12)
_bd = Vector((HB.x - PTOP.x, HB.y - PTOP.y, 0)).normalized(); _bn = Vector((_bd.y, -_bd.x, 0)); _bn = _bn if _bn.y < 0 else -_bn
beam('head_boom_strip', PTOP + _bn * 0.26 + Vector((0, 0, -0.08)), Vector((HB.x, HB.y, PTOP.z - 0.08)) + _bn * 0.26, 0.02, 0.06, CYAN, bevel=0)
rod('head_hanger', (HB.x, HB.y, PTOP.z), tuple(C1 + up * 0.75 + u * 0.3), 0.09, SATIN, segs=16)

# ================= ORE SILO =================
lathe('silo_plinth', [(0, 0), (3.1, 0), (3.1, 0.35), (2.9, 0.5), (0, 0.5)], (BIN_X, BIN_Y, 0), GRAPH, segs=72)
lathe('silo', [(0, 0.5), (2.6, 0.5), (2.6, 5.0), (2.45, 5.55), (1.9, 6.05), (1.1, 6.3), (0, 6.35)], (BIN_X, BIN_Y, 0), WHITE, segs=72)
for z in (1.6, 3.3):
    ring('silo_band', 2.62, (BIN_X, BIN_Y, z), 0.12, GRAPH, w=0.06, segs=96)
ring('silo_glow', 2.62, (BIN_X, BIN_Y, 4.85), 0.07, CYAN, w=0.03, segs=96)
lathe('silo_hatch', [(0.95, 6.0), (0.95, 6.55), (0.8, 6.62), (0, 6.62)], (BIN_X, BIN_Y, 0), GRAPH_S, segs=48)
# service spine with He-3 fill window + decals
box('spine', (1.7, 0.45, 4.6), (BIN_X, BIN_Y - 2.55, 2.85), GRAPH, bevel=0.08, segs=3)
box('fill_window_bg', (0.56, 0.04, 3.4), (BIN_X - 0.4, BIN_Y - 2.78, 2.55), GLASS, bevel=0.01)
box('fill_level', (0.48, 0.05, 2.3), (BIN_X - 0.4, BIN_Y - 2.785, 2.0), HE3, bevel=0.01)
for i in range(7): box('fill_tick', (0.16, 0.05, 0.025), (BIN_X - 0.0, BIN_Y - 2.785, 1.0 + i * 0.5), INKW, bevel=0)
text('decal_bin', 'ORE BIN 01', (BIN_X + 0.42, BIN_Y - 2.785, 3.3), (math.pi / 2, 0, math.pi / 2 * 0), 0.2, INKW, extrude=0.004)
text('decal_bin_v', 'He-3 / Pt', (BIN_X + 0.42, BIN_Y - 2.785, 2.6), (math.pi / 2, 0, 0), 0.16, CYAN, extrude=0.004)
text('decal_bin_m', 'MAX 40 t', (BIN_X + 0.42, BIN_Y - 2.785, 2.25), (math.pi / 2, 0, 0), 0.14, INKW, extrude=0.004)
text('decal_mine_bin', 'MINE A-01', (BIN_X + 0.42, BIN_Y - 2.785, 1.2), (math.pi / 2, 0, 0), 0.14, INKW, extrude=0.004)
sphere('silo_beacon', 0.14, (BIN_X + 1.5, BIN_Y - 1.0, 6.05), CYAN, sub=2)
# ladder-free access ring
for k in range(5):
    a = math.radians(200 + k * 30)
    rod('silo_rung', (BIN_X + 2.62 * math.cos(a), BIN_Y + 2.62 * math.sin(a), 0.7), (BIN_X + 2.62 * math.cos(a), BIN_Y + 2.62 * math.sin(a), 0.55), 0.05, SATIN) if False else None

# ================= DUMP HOPPER (above ground) + LIFT TUBE -> SILO (truck drop-off) =================
# Jacob/Director rule: nothing underground - the receiving hopper is a raised station, only the bore digs in.
PX, PY = 5.8, 2.4
box('dump_plinth', (3.1, 2.7, 0.18), (PX, PY, 0.09), GRAPH, bevel=0.05)
rbox('dump_body', (2.8, 2.4, 1.2), (PX, PY, 0.78), WHITE, r=0.16, segs=4)
box('dump_lip', (2.9, 2.5, 0.12), (PX, PY, 1.42), GRAPH_S, bevel=0.04)
box('dump_grate_bg', (2.4, 2.0, 0.04), (PX, PY, 1.45), GRAPH, bevel=0)
for i in range(9): box('dump_grate', (0.05, 2.0, 0.06), (PX - 1.0 + i * 0.25, PY, 1.49), SATIN, bevel=0.005)
box('dump_glow', (2.4, 0.02, 0.06), (PX, PY - 1.205, 1.15), CYAN, bevel=0)
box('dump_band', (2.84, 2.44, 0.1), (PX, PY, 0.45), GRAPH, bevel=0.02)
text('decal_dump', 'DUMP 01', (PX - 0.62, PY - 1.207, 0.7), (math.pi / 2, 0, 0), 0.22, INK, extrude=0.004)
ore_chunks('dump_ore', (PX, PY, 1.52), 0.8, 14, ORE_MIX, size=(0.1, 0.22), seed=81)
LHX, LHY = PX + 0.2, PY + 1.65
rbox('lift_housing', (1.3, 1.1, 2.0), (LHX, LHY, 1.0), WHITE, r=0.3, segs=5)
box('lift_strip', (1.0, 0.02, 0.07), (LHX, LHY - 0.56, 1.55), CYAN, bevel=0)
lift = bez((LHX, LHY, 1.9), (LHX + 0.6, LHY + 0.6, 9.4), (BIN_X - 0.85, BIN_Y - 0.05, 6.75), 34)
curve_tube('lift_tube', [tuple(p) for p in lift], 0.32, WHITE_S, res=6)
curve_tube('lift_strip_t', [tuple(p + Vector((0, -0.3, 0.05))) for p in lift[2:-2]], 0.03, CYAN, res=2)
for i in range(4, 33, 5):
    a, b = lift[i], lift[i + 1]; dd = (b - a)
    rod('lift_collar', a - dd * 0.3, a + dd * 0.3, 0.36, GRAPH_S, segs=32)

# ================= HT-04 DUMP TRUCK (replaces the rover; also does the tap-deposit bonus run) =================
_truck_before = set(bpy.data.objects)
def boxm(name, size, M, mat, bevel=0.02, segs=2):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.transform(bm, matrix=M @ Matrix.Diagonal((*size, 1)), verts=bm.verts)
    return _obj(bm, name, mat, bevel=bevel, segs=segs)
WR, WW = 0.85, 0.62
AXLES = (-2.7, -1.35, 2.4)
for sy in (-1, 1):
    wy = sy * 1.5
    for wx in AXLES:
        c = T(wx, wy, WR)
        cyl('tire', WR, WW, tuple(c), TIRE, rot=(math.pi / 2, 0, 0), segs=56, bevel=0.09)
        for g in range(20):   # grousers
            a = TAU * g / 20
            box('grouser', (0.08, WW + 0.01, 0.06), (c.x + (WR + 0.02) * math.cos(a), c.y, WR + (WR + 0.02) * math.sin(a)), TIRE, rot=(0, -a, 0), bevel=0.01)
        cyl('rim', 0.56, WW + 0.03, tuple(c), WHITE_S, rot=(math.pi / 2, 0, 0), segs=48, bevel=0.03)
        cyl('hub', 0.28, WW + 0.1, tuple(c), GRAPH_S, rot=(math.pi / 2, 0, 0), segs=36, bevel=0.02)
        cyl('hub_glow', 0.36, 0.02, (c.x, c.y + sy * (WW / 2 + 0.025), WR), CYANS, rot=(math.pi / 2, 0, 0), segs=48, bevel=0)
        cyl('hub_cap', 0.31, 0.03, (c.x, c.y + sy * (WW / 2 + 0.035), WR), GRAPH_S, rot=(math.pi / 2, 0, 0), segs=48, bevel=0.005)
        for k in range(6):   # rim lug bolts
            a = TAU * k / 6
            sphere('lug', 0.035, (c.x + 0.2 * math.cos(a), c.y + sy * (WW / 2 + 0.06), WR + 0.2 * math.sin(a)), SATIN, sub=1)
        rod('axle', T(wx, sy * 0.55, WR), T(wx, sy * 1.2, WR), 0.12, SATIN)
    # rear walking bogie (rocker-bogie feel) + front swing arm
    b0, b1 = T(AXLES[0], sy * 1.02, WR), T(AXLES[1], sy * 1.02, WR); bp = (b0 + b1) / 2 + Vector((0, 0, 0.12))
    beam('bogie', b0, bp, 0.2, 0.3, WHITE_S, bevel=0.08); beam('bogie', bp, b1, 0.2, 0.3, WHITE_S, bevel=0.08)
    beam('bogie_strip', b0 + Vector((0, sy * 0.11, 0.02)), b1 + Vector((0, sy * 0.11, 0.02)), 0.01, 0.05, CYAN, bevel=0)
    cyl('bogie_pivot', 0.2, 0.34, tuple(bp), SATIN, rot=(math.pi / 2, 0, 0), segs=24)
    beam('bogie_hanger', bp, T(bp.x - TX, sy * 0.6, 1.3), 0.22, 0.26, GRAPH_S, bevel=0.06)
    fa0, fa1 = T(1.3, sy * 0.75, 1.3), T(AXLES[2], sy * 1.02, WR)
    beam('swing_arm', fa0, fa1, 0.2, 0.28, GRAPH_S, bevel=0.07)
    piston('shock', T(1.75, sy * 0.85, 1.72), T(AXLES[2] - 0.15, sy * 1.0, 1.05), 0.07, WHITE_S, SATIN)
    rbox('fender', (1.95, 0.78, 0.1), tuple(T(AXLES[2], wy, 1.83)), WHITE_S, r=0.04, segs=3)
    box('fender_glow', (1.6, 0.02, 0.03), tuple(T(AXLES[2], wy + sy * 0.4, 1.83)), CYANS, bevel=0)
# chassis
for sy in (-1, 1):
    box('frame_rail', (6.7, 0.3, 0.36), tuple(T(-0.2, sy * 0.55, 1.4)), GRAPH, bevel=0.05, segs=3)
for x in (-3.0, -0.9, 1.0, 3.0):
    box('cross_member', (0.22, 1.4, 0.22), tuple(T(x, 0, 1.4)), GRAPH_S, bevel=0.04)
rbox('belly_pack', (2.0, 1.0, 0.45), tuple(T(-0.2, 0, 1.05)), GRAPH_S, r=0.12, segs=3)
box('belly_glow', (1.7, 0.02, 0.04), tuple(T(-0.2, -0.51, 0.95)), CYANS, bevel=0)
# ---- cab
rbox('cab', (2.3, 2.5, 1.7), tuple(T(2.35, 0, 2.7)), WHITE, r=0.38, segs=6)
rbox('cab_roof', (1.6, 2.2, 0.12), tuple(T(2.05, 0, 3.56)), GRAPH, r=0.05, segs=3)
rbox('cab_windframe', (0.1, 2.3, 0.95), tuple(T(3.47, 0, 2.98)), GRAPH, rot=(0, -0.28, 0), r=0.12, segs=4)
rbox('cab_windshield', (0.06, 2.12, 0.78), tuple(T(3.52, 0, 2.99)), GLASS, rot=(0, -0.28, 0), r=0.1, segs=4)
for sy in (-1, 1): rbox('cab_sidewin', (0.6, 0.04, 0.5), tuple(T(2.83, sy * 1.255, 3.0)), GLASS, r=0.06, segs=3)
rbox('cab_nose', (0.45, 2.6, 0.55), tuple(T(3.45, 0, 2.05)), GRAPH, r=0.15, segs=4)
box('cab_eye', (0.03, 2.1, 0.06), tuple(T(3.68, 0, 2.2)), CYAN, bevel=0)
for dy in (-0.95, 0.95):
    rbox('cab_lamp', (0.22, 0.4, 0.2), tuple(T(3.55, dy, 2.48)), GRAPH_S, r=0.06, segs=3)
    box('cab_lamp_l', (0.02, 0.3, 0.12), tuple(T(3.665, dy, 2.48)), LAMP, bevel=0)
box('cab_lightbar', (0.08, 1.4, 0.07), tuple(T(2.8, 0, 3.66)), LAMP, bevel=0.01)
rbox('cab_lightbar_h', (0.18, 1.55, 0.12), tuple(T(2.72, 0, 3.66)), GRAPH_S, r=0.04, segs=2)
sphere('cab_beacon', 0.1, tuple(T(1.5, 0.75, 3.7)), CYAN, sub=2)
rod('cab_whip', T(1.45, -0.8, 3.6), T(1.3, -0.8, 5.0), 0.02, SATIN)
sphere('cab_whip_tip', 0.05, tuple(T(1.3, -0.8, 5.02)), CYAN, sub=1)
for sy in (-1, 1):
    box('cab_strip', (2.0, 0.02, 0.07), tuple(T(2.3, sy * 1.255, 2.05)), CYAN, bevel=0)
    rbox('door', (0.95, 0.03, 1.05), tuple(T(1.85, sy * 1.25, 2.62)), GRAPH_S, r=0.03, segs=2)
    box('door_window', (0.6, 0.02, 0.38), tuple(T(1.85, sy * 1.268, 2.9)), GLASS, bevel=0)
text('decal_cab', 'MINE A-01', (TX + 1.85, TY - 1.267, 2.42), (math.pi / 2, 0, 0), 0.12, INKW, extrude=0.003)
# access steps under the door (-Y side)
for sy in (-1,):
    for k, z in enumerate((0.55, 0.95, 1.35)):
        box('step', (0.55, 0.28, 0.05), tuple(T(1.85, sy * 1.36, z)), SATIN, bevel=0.01)
    for dx in (-0.3, 0.3):
        box('step_rail', (0.05, 0.05, 1.05), tuple(T(1.85 + dx, sy * 1.36, 1.0)), GRAPH_S, bevel=0.01)
# ---- tipping dump bed (hinged at the rear, hoist ram up front)
BX0, BX1, BW, BZ, BTOP = -3.5, 0.3, 1.4, 1.93, 3.3
bx = (BX0 + BX1) / 2; bl = BX1 - BX0
box('bed_floor', (bl, 2 * BW, 0.16), tuple(T(bx, 0, BZ)), GRAPH, bevel=0.03)
for sy in (-1, 1):
    box('bed_wall', (bl, 0.12, BTOP - BZ), tuple(T(bx, sy * (BW - 0.06), (BZ + BTOP) / 2)), WHITE, bevel=0.03)
    rbox('bed_rim', (bl + 0.1, 0.22, 0.12), tuple(T(bx, sy * (BW - 0.06), BTOP + 0.02)), GRAPH_S, r=0.04, segs=2)
    box('bed_rim_glow', (bl - 0.4, 0.02, 0.05), tuple(T(bx, sy * (BW + 0.005), BTOP - 0.16)), CYAN, bevel=0)
    for x in (BX0 + 0.12, -0.55, BX1 - 0.12):
        box('bed_rib', (0.13, 0.1, BTOP - BZ - 0.05), tuple(T(x, sy * (BW + 0.04), (BZ + BTOP) / 2 - 0.02)), GRAPH, bevel=0.02)
    box('bed_skirt', (bl, 0.14, 0.14), tuple(T(bx, sy * (BW - 0.02), BZ - 0.05)), GRAPH_S, bevel=0.03)
    box('bed_liner', (bl - 0.1, 0.03, BTOP - BZ - 0.15), tuple(T(bx, sy * (BW - 0.135), (BZ + BTOP) / 2 + 0.05)), GRAPH, bevel=0)
box('bed_front', (0.14, 2 * BW, BTOP - BZ + 0.3), tuple(T(BX1 - 0.07, 0, (BZ + BTOP + 0.3) / 2)), WHITE, bevel=0.03)
rbox('bed_front_cap', (0.24, 2 * BW + 0.1, 0.12), tuple(T(BX1 - 0.07, 0, BTOP + 0.32)), GRAPH_S, r=0.04, segs=2)
box('bed_front_glow', (0.02, 2 * BW - 0.4, 0.05), tuple(T(BX1 + 0.005, 0, BTOP + 0.15)), CYAN, bevel=0)
box('bed_tail', (0.7, 2 * BW - 0.24, 0.12), tuple(T(BX0 + 0.25, 0, BZ + 0.16)), GRAPH, rot=(0, -0.38, 0), bevel=0.02)
for sy in (-1, 1):
    box('bed_subframe', (bl - 0.2, 0.22, 0.1), tuple(T(bx, sy * 0.55, BZ - 0.13)), GRAPH_S, bevel=0.02)
    cyl('bed_hinge', 0.11, 0.42, tuple(T(BX0 + 0.2, sy * 0.55, 1.72)), SATIN, rot=(math.pi / 2, 0, 0), segs=20)
    box('bed_hinge_lug', (0.26, 0.08, 0.36), tuple(T(BX0 + 0.2, sy * 0.78, 1.72)), GRAPH, bevel=0.02)
piston('hoist', T(0.72, 0.55, 1.55), T(0.42, 0.55, 3.05), 0.13, GRAPH_S, SATIN, ext=0.5)
box('hoist_bracket', (0.18, 0.4, 0.3), tuple(T(0.38, 0.55, 3.05)), GRAPH, bevel=0.03)
text('decal_bed', 'HT-04', (TX - 2.0, TY - BW - 0.006, 2.55), (math.pi / 2, 0, 0), 0.62, INK, extrude=0.005)
text('decal_bed_s', 'He-3  ORE HAULER', (TX - 2.0, TY - BW - 0.004, 2.12), (math.pi / 2, 0, 0), 0.15, CYAN, extrude=0.003)
text('decal_bed_r', 'HT-04', (TX - 2.0, TY + BW + 0.006, 2.55), (math.pi / 2, 0, math.pi), 0.62, INK, extrude=0.005)
text('decal_cab_f', 'HT-04', (TX + 3.6, TY - 1.15, 1.95), (math.pi / 2, 0, math.pi / 2), 0.12, INKW, extrude=0.003) if False else None
# ore load in the bed (heaped under the discharge)
heap('bed_heap', tuple(T(bx, 0, BZ + 0.06)), 1.0, 1.15, ROCK, seed=21, sq=(bl / 2 - 0.12, BW - 0.16))
def bed_z(x, y):
    u_, v_ = (x - (TX + bx)) / (bl / 2 - 0.12), (y - TY) / (BW - 0.16)
    return BZ + 0.06 + 1.15 * max(0, 1 - max(abs(u_), abs(v_)) ** 2) - 0.04
ore_chunks('bed_ore', tuple(T(bx, 0, 0)), 1.35, 95, ORE_MIX, size=(0.12, 0.3), seed=63, zfun=bed_z)
# ---- compact loading arm behind the cab (B-styled: white/graphite, cyan accents, small scoop)
L1, L2 = 1.3, 1.7
SH = T(0.75, -0.92, 3.3)
lathe('arm_pedestal', [(0, 1.55), (0.36, 1.55), (0.34, 2.75), (0.28, 2.95), (0, 3.0)], (SH.x, SH.y, 0), GRAPH_S, segs=40)
ring('arm_pedestal_glow', 0.35, (SH.x, SH.y, 2.6), 0.05, CYAN, w=0.02, segs=40)
lathe('arm_turret', [(0, 2.95), (0.32, 2.95), (0.3, 3.18), (0, 3.22)], (SH.x, SH.y, 0), WHITE_S, segs=40)
def ik(S, Tg, l1, l2, upv=Vector((0, 0, 1))):
    dv = Tg - S; D = min(dv.length, l1 + l2 - 1e-3); dn = dv.normalized()
    a = (l1 * l1 - l2 * l2 + D * D) / (2 * D); h = math.sqrt(max(0.0, l1 * l1 - a * a))
    n = (upv - dn * upv.dot(dn)).normalized()
    return S + dn * a + n * h, S + dn * D
if ARM_POSE == 'reach':
    EL = SH + Vector((0.55, -0.45, 0.7)).normalized() * L1          # shoulder raised, swung out over the cab corner
    WRp = EL + Vector((0.38, -0.51, -0.77)).normalized() * L2      # forearm angled down toward the tap deposit
else:   # stowed: folded back along the bed's left rim, scoop parked on the rim
    EL, WRp = ik(SH, T(-1.75, -1.12, 3.6), L1, L2)
sphere('arm_shoulder', 0.25, tuple(SH), WHITE_S, sub=3)
beam('arm_upper', SH, EL, 0.3, 0.34, WHITE, bevel=0.11)
sphere('arm_elbow', 0.21, tuple(EL), GRAPH_S, sub=3)
beam('arm_fore', EL, WRp, 0.24, 0.28, WHITE, bevel=0.09)
sphere('arm_wrist', 0.16, tuple(WRp), GRAPH_S, sub=3)
_, _, _, Ru = frame_from(SH, EL); _, _, _, Rf = frame_from(EL, WRp)
for (p0, p1, Rm, w) in ((SH, EL, Ru, 0.35), (EL, WRp, Rf, 0.29)):
    zax = Rm.col[2]
    beam('arm_strip', p0 + zax * (w / 2 + 0.005) + (p1 - p0) * 0.15, p1 + zax * (w / 2 + 0.005) - (p1 - p0) * 0.15, 0.06, 0.012, CYAN, bevel=0)
yax = Ru.col[1]
piston('arm_ram', SH + Vector((0, 0, -0.35)) + yax * 0.22, SH + (EL - SH) * 0.6 + yax * 0.22, 0.06, GRAPH_S, SATIN)
cable('arm_hose', SH - yax * 0.22, EL - yax * 0.2, 0.03, GRAPH_S, sag=0.1)
cable('arm_hose', EL - yax * 0.18, WRp - yax * 0.15, 0.025, GRAPH_S, sag=0.08)
# scoop: opens along the forearm direction, mouth tilted down
fdir = (WRp - EL).normalized()
sdir = (fdir + Vector((0, 0, -0.9 if ARM_POSE == 'reach' else -0.25))).normalized()
_, _, _, Rs = frame_from(WRp, WRp + sdir); Ms = Matrix.Translation(WRp) @ Rs.to_4x4()
def S_(lx, ly, lz): return Ms @ Matrix.Translation((lx, ly, lz))
boxm('scoop_back', (0.06, 0.62, 0.42), S_(0.06, 0, 0.02), WHITE_S, bevel=0.02)
boxm('scoop_floor', (0.62, 0.62, 0.05), S_(0.36, 0, -0.18), GRAPH, bevel=0.015)
for sy in (-1, 1):
    boxm('scoop_side', (0.6, 0.05, 0.36), S_(0.36, sy * 0.31, -0.02), WHITE, bevel=0.015)
    boxm('scoop_side_glow', (0.42, 0.012, 0.03), S_(0.33, sy * 0.337, 0.06), CYAN, bevel=0)
for k in range(5):
    boxm('scoop_tooth', (0.12, 0.06, 0.04), S_(0.7, -0.24 + k * 0.12, -0.18), SATIN, bevel=0.01)
if ARM_POSE == 'reach':
    for k in range(5):
        pp = Ms @ Vector((0.3 + 0.07 * k, -0.15 + 0.08 * k, -0.1))
        ore_chunks('scoop_ore', (pp.x, pp.y, pp.z), 0.01, 1, [(HE3, 1, 'he3')] if k % 2 == 0 else [(ROCK, 1, 'rock')], size=(0.1, 0.18), seed=900 + k)
TRUCK_OBJS = [o for o in bpy.data.objects if o not in _truck_before]

# ================= GLOWING He-3 DEPOSITS (tap-a-deposit bonus run) =================
DX, DY = 11.2, -8.8
heap('deposit', (DX, DY, 0.0), 2.6, 1.4, ROCK, seed=12)
for k in range(16):
    a = rr.uniform(0, TAU); dd = rr.uniform(0.2, 1.9); h = 1.4 * max(0, 1 - (dd / 2.6) ** 2)
    sphere('seam_crystal', rr.uniform(0.15, 0.32), (DX + dd * math.cos(a), DY + dd * math.sin(a), h + 0.1), HE3, scale=(0.5, 0.5, 1.8), sub=1, jitter=0.2, smooth=False, seed=k, rot=(rr.uniform(-0.6, 0.6), rr.uniform(-0.6, 0.6), 0))
ore_chunks('spill', (DX - 2.0, DY + 0.4, 0.0), 1.4, 26, ORE_MIX, size=(0.1, 0.25), seed=34)
# small tap deposit beside the loading bay (the arm reaches into it in the truck close-up)
SDp = T(3.0, -3.6, 0)
heap('deposit_small', (SDp.x, SDp.y, 0.0), 1.05, 0.7, ROCK, seed=17)
for k in range(9):
    a = rr.uniform(0, TAU); dd = rr.uniform(0.1, 0.75); h = 0.7 * max(0, 1 - (dd / 1.05) ** 2)
    sphere('seam_crystal_s', rr.uniform(0.11, 0.22), (SDp.x + dd * math.cos(a), SDp.y + dd * math.sin(a), h + 0.05), HE3, scale=(0.5, 0.5, 1.8), sub=1, jitter=0.2, smooth=False, seed=40 + k, rot=(rr.uniform(-0.6, 0.6), rr.uniform(-0.6, 0.6), 0))
ore_chunks('spill_s', (SDp.x + 0.6, SDp.y + 0.9, 0.0), 0.6, 10, ORE_MIX, size=(0.08, 0.18), seed=44)

# ================= STAGE =================
height = build_stage(keep_flat=((1, 0, 22),))
world_and_sun((-0.55, -0.6, 0.58), 5.5)
# Jacob: cool gray rock ground, no tan - desaturate the shared stage/rock ramps to a slightly blue-gray (local override, mc_common untouched)
def _cool(mname, k=(0.93, 0.99, 1.10), gain=0.97):
    m = bpy.data.materials.get(mname)
    if not m: return
    def c(col):
        L = 0.2126 * col[0] + 0.7152 * col[1] + 0.0722 * col[2]
        return (L * k[0] * gain, L * k[1] * gain, L * k[2] * gain, 1.0)
    for n in m.node_tree.nodes:
        if n.type == 'VALTORGB':
            for e in n.color_ramp.elements: e.color = c(e.color)
    m.diffuse_color = c(m.diffuse_color)
for _m in ('M_Regolith', 'M_Boulder', 'B_OreRock'): _cool(_m)
# seat the truck on the regolith (tyres sink ~2 cm)
gz = min(height(TX + x, TY + sy * 1.5) for x in AXLES for sy in (-1, 1)) - 0.02
for o in TRUCK_OBJS:
    if o.parent is None: o.location.z += gz

# ---- compacted haul road: loop conveyor bay -> dump hopper/silo, with a spur to the deposits (Stage decal, not in GLB)
def M_road():
    m = bpy.data.materials.new('B_HaulRoad'); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes['Principled BSDF']; out = nt.nodes['Material Output']
    uv = nt.nodes.new('ShaderNodeUVMap'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(uv.outputs['UV'], sep.inputs['Vector'])
    tc = nt.nodes.new('ShaderNodeTexCoord')
    def band(c, w, k):   # 1 inside |v-c|<w, soft
        sub = nt.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'; nt.links.new(sep.outputs['Y'], sub.inputs[0]); sub.inputs[1].default_value = c
        ab = nt.nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; nt.links.new(sub.outputs[0], ab.inputs[0])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = w; mr.inputs['From Max'].default_value = w * k
        mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0; nt.links.new(ab.outputs[0], mr.inputs['Value'])
        return mr.outputs[0]
    edge = band(0.5, 0.3, 1.66)          # soft shoulders
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.6; nz.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    nm = nt.nodes.new('ShaderNodeMapRange'); nm.inputs['From Min'].default_value = 0.35; nm.inputs['From Max'].default_value = 0.65
    nm.inputs['To Min'].default_value = 0.55; nm.inputs['To Max'].default_value = 1.0; nt.links.new(nz.outputs['Fac'], nm.inputs['Value'])
    a = nt.nodes.new('ShaderNodeMath'); a.operation = 'MULTIPLY'; nt.links.new(edge, a.inputs[0]); nt.links.new(nm.outputs[0], a.inputs[1])
    a2 = nt.nodes.new('ShaderNodeMath'); a2.operation = 'MULTIPLY'; nt.links.new(a.outputs[0], a2.inputs[0]); a2.inputs[1].default_value = 0.95
    r1 = band(0.27, 0.06, 2.0); r2 = band(0.73, 0.06, 2.0)
    rs = nt.nodes.new('ShaderNodeMath'); rs.operation = 'ADD'; rs.use_clamp = True; nt.links.new(r1, rs.inputs[0]); nt.links.new(r2, rs.inputs[1])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = hexc('#33363a'); ramp.color_ramp.elements[1].color = hexc('#232528')
    nt.links.new(rs.outputs[0], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.9
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.12; bump.inputs['Distance'].default_value = 0.02
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 7; n2.inputs['Detail'].default_value = 8
    nt.links.new(tc.outputs['Object'], n2.inputs['Vector']); nt.links.new(n2.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(a2.outputs[0], mx.inputs['Fac']); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface']); m.diffuse_color = hexc('#33363a'); m.blend_method = 'BLEND'
    return m
ROADM = M_road()
def road(name, pts, w, closed=False):
    pts = [Vector(p) for p in pts]; n = len(pts); bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); rows = []; s_acc = 0.0
    for i, p in enumerate(pts):
        a = pts[(i - 1) % n] if (closed or i > 0) else p; b_ = pts[(i + 1) % n] if (closed or i < n - 1) else p
        t = (b_ - a); t.z = 0; t.normalize(); nn = Vector((-t.y, t.x, 0))
        if i: s_acc += (p - pts[i - 1]).length
        row = []
        for k in range(7):
            q = p + nn * w * (k / 6 - 0.5); row.append((bm.verts.new((q.x, q.y, height(q.x, q.y) + 0.035)), k / 6, s_acc / w))
        rows.append(row)
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        r0, r1 = rows[i], rows[(i + 1) % n]
        for k in range(6):
            f = bm.faces.new((r0[k][0], r0[k + 1][0], r1[k + 1][0], r1[k][0]))
            for lp, (vv, vk, vs) in zip(f.loops, (r0[k], r0[k + 1], r1[k + 1], r1[k])): lp[uvl].uv = (vs, vk)
    return _obj(bm, name, ROADM, c='Stage', smooth=True, angle=180)
LOOP_W = 3.2; LX0, LX1, LCY, LR = 2.0, 11.5, -2.5, 2.0
lp = []
for i in range(40): lp.append((LX0 + (LX1 - LX0) * i / 40, LCY - LR, 0))
for i in range(24): a = -math.pi / 2 + math.pi * i / 24; lp.append((LX1 + LR * math.cos(a), LCY + LR * math.sin(a), 0))
for i in range(40): lp.append((LX1 - (LX1 - LX0) * i / 40, LCY + LR, 0))
for i in range(24): a = math.pi / 2 + math.pi * i / 24; lp.append((LX0 + LR * math.cos(a), LCY + LR * math.sin(a), 0))
road('haul_road_loop', lp, LOOP_W, closed=True)
sp = bez((9.6, -4.4, 0), (10.4, -5.8, 0), (DX - 0.7, DY + 2.0, 0), 20)
road('haul_road_spur', [tuple(p) for p in sp], 2.8)
# ---- gameplay markers for later (empties + curve in a 'Markers' collection: saved in the .blend, not in the GLB)
MK = bpy.data.collections.new('Markers'); bpy.context.scene.collection.children.link(MK)
for i, (nm, loc, r) in enumerate((('main He-3 seam', (DX, DY, height(DX, DY)), 2.6), ('tap deposit', (SDp.x, SDp.y, height(SDp.x, SDp.y)), 1.05))):
    e = bpy.data.objects.new('Dep_%02d' % (i + 1), None); e.empty_display_type = 'CIRCLE'; e.empty_display_size = r
    e.location = loc; e['label'] = nm; e['radius_m'] = r; MK.objects.link(e)
cu = bpy.data.curves.new('Path_Spur', 'CURVE'); cu.dimensions = '3D'; spl = cu.splines.new('POLY'); spl.points.add(len(sp) - 1)
for k, q in enumerate(sp): spl.points[k].co = (q.x, q.y, height(q.x, q.y) + 0.05, 1)
po = bpy.data.objects.new('Path_Spur', cu); po['from'] = 'haul loop (south straight)'; po['to'] = 'Dep_01'; MK.objects.link(po)
astronaut((-1.6, -8.2, 0.0), rot_z=-0.5)
cam = setup_render(48 if not QUICK else 16)

ONLY = A.get('only', 'turn,hero')
if 'glb' in ONLY: export_glb(os.path.join(OUT, 'b_sleek_hightech_master.glb'))
if 'blend' in ONLY:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'b_sleek_hightech_master.blend'), compress=True)
if 'turn' in ONLY:
    turntable(cam, OUT, (1.0, 0.5, 4.5), 50, 22, size=1000 if not QUICK else 400, samples=48 if not QUICK else 12)
if 'closeup' in ONLY:   # truck beauty shot (run with --arm reach)
    w, h = (3840, 2160) if not QUICK else (960, 540)
    cv = [float(v) for v in A['cc'].split(',')] if 'cc' in A else [0.6, -1.6, 2.3, -9.0, -14.0, 4.6, 32]   # rear-left 3/4: arm reads in profile
    shoot(cam, os.path.join(OUT, 'b_dump_truck_closeup_3840x2160.png'), tuple(T(*cv[0:3])), tuple(T(*cv[3:6])), w, h, lens=cv[6], samples=int(A.get('hs', 64)) if not QUICK else 16)
if 'top' in ONLY:
    shoot(cam, os.path.join(OUT, 'top.png'), (4.0, -1.0, 0.0), (4.0, -1.01, 40.0), 1000, 1000, lens=35, samples=24)
if 'bedcrop' in ONLY:
    shoot(cam, os.path.join(OUT, 'bedcrop.png'), tuple(T(-1.6, -1.4, 2.6)), tuple(T(-1.0, -6.5, 3.0)), 800, 450, lens=35, samples=24)
if 'hero' in ONLY:
    w, h = (3840, 2160) if not QUICK else (960, 540)
    shoot(cam, os.path.join(OUT, 'hero.png'), (0.0, 1.5, 6.6), (10.0, -31.0, 5.0), w, h, lens=24, samples=int(A.get('hs', 64)) if not QUICK else 16)
