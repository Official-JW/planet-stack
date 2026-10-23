"""Concept B - SLEEK HIGH-TECH Mine A. blender -b -P concept_b_sleek.py -- --out DIR [--quick 1] [--only glb,blend,turn,hero]"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
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

# ================= UNDERGLOW CONVEYOR =================
BIN_X, BIN_Y = 10.0, 4.5
C0 = Vector((H_X + 0.4, H_Y, 2.55)); C1 = Vector((BIN_X - 0.4, BIN_Y, 7.15))
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
for i in range(46):
    t = rr.uniform(0.04, 0.96); p = C0 + u * (L * t) + up * 0.04 + side * rr.uniform(-0.45, 0.45)
    kind = rr.choices(['he3', 'pt', 'rock'], [5, 2, 3])[0]
    m = {'he3': HE3, 'pt': PT, 'rock': ROCK}[kind]
    ore_chunks('belt_ore', (p.x, p.y, p.z), 0.01, 1, [(m, 1, kind)], size=(0.15, 0.3), seed=i * 11 + 5)
for t in (0.33, 0.7):
    p = C0 + u * (L * t) - up * 0.2
    rod('conv_pylon', (p.x, p.y, 0.0), (p.x, p.y, p.z - 0.15), 0.26, GRAPH_S, r2=0.18, segs=24)
    lathe('conv_foot', [(0, 0), (0.75, 0), (0.62, 0.16), (0, 0.2)], (p.x, p.y, 0), WHITE_S, segs=32)
    ring('conv_pylon_glow', 0.25, (p.x, p.y, 0.9), 0.06, CYAN, w=0.03, segs=32)
    beam('conv_saddle', p - side * 0.7 - up * 0.08, p + side * 0.7 - up * 0.08, 0.3, 0.2, GRAPH_S, bevel=0.05)
rbox('head_housing', (1.6, 1.9, 1.1), tuple(C1 + up * 0.25 + u * 0.3), WHITE, r=0.35, segs=5)
rbox('tail_housing', (1.2, 1.8, 0.8), tuple(C0 - u * 0.2 + up * 0.05), WHITE, r=0.3, segs=5)

# ================= ORE SILO =================
lathe('silo_plinth', [(0, 0), (3.1, 0), (3.1, 0.35), (2.9, 0.5), (0, 0.5)], (BIN_X, BIN_Y, 0), GRAPH, segs=72)
lathe('silo', [(0, 0.5), (2.6, 0.5), (2.6, 5.0), (2.45, 5.55), (1.9, 6.05), (1.1, 6.3), (0, 6.35)], (BIN_X, BIN_Y, 0), WHITE, segs=72)
for z in (1.6, 3.3):
    ring('silo_band', 2.62, (BIN_X, BIN_Y, z), 0.12, GRAPH, w=0.06, segs=96)
ring('silo_glow', 2.62, (BIN_X, BIN_Y, 4.85), 0.07, CYAN, w=0.03, segs=96)
lathe('silo_hatch', [(0.95, 6.0), (0.95, 6.55), (0.8, 6.62), (0, 6.62)], (BIN_X, BIN_Y, 0), GRAPH_S, segs=48)
rod('silo_chute', tuple(C1 + up * 0.0 + u * 0.75 - up * 0.3), (BIN_X, BIN_Y, 6.6), 0.32, GRAPH_S, segs=32)
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

# ================= 6-WHEEL ROCKER-BOGIE ROVER =================
VX, VY = 1.6, -6.6
WR = 0.72
wheels = [(-2.0, 0.0), (0.05, 0.0), (2.0, 0.0)]
for sy in (-1, 1):
    wy = VY + sy * 1.95
    for (wx, _) in wheels:
        c = (VX + wx, wy, WR)
        cyl('tire', WR, 0.55, c, TIRE, rot=(math.pi / 2, 0, 0), segs=48, bevel=0.08)
        for g in range(18):   # grousers
            a = TAU * g / 18
            box('grouser', (0.07, 0.56, 0.06), (c[0] + (WR + 0.02) * math.cos(a), wy, WR + (WR + 0.02) * math.sin(a)), TIRE, rot=(0, -a, 0), bevel=0.01)
        cyl('rim', 0.48, 0.58, c, WHITE_S, rot=(math.pi / 2, 0, 0), segs=40, bevel=0.03)
        cyl('hub', 0.24, 0.66, c, GRAPH_S, rot=(math.pi / 2, 0, 0), segs=32, bevel=0.02)
        ring_c = (c[0], wy + sy * 0.3, WR)
        cyl('hub_glow', 0.3, 0.02, ring_c, CYAN, rot=(math.pi / 2, 0, 0), segs=40, bevel=0)
        cyl('hub_cap', 0.26, 0.03, (c[0], wy + sy * 0.31, WR), GRAPH_S, rot=(math.pi / 2, 0, 0), segs=40, bevel=0.005)
    # rocker: body pivot -> rear wheel and -> bogie pivot
    piv = Vector((VX - 0.4, VY + sy * 1.55, 2.1)); bog = Vector((VX + 1.05, VY + sy * 1.55, 1.45))
    rear = Vector((VX - 2.0, VY + sy * 1.55, WR)); midw = Vector((VX + 0.05, VY + sy * 1.55, WR)); fr = Vector((VX + 2.0, VY + sy * 1.55, WR))
    beam('rocker', piv, rear, 0.22, 0.3, GRAPH_S, bevel=0.08)
    beam('rocker', piv, bog, 0.22, 0.3, GRAPH_S, bevel=0.08)
    beam('bogie', bog, midw, 0.2, 0.26, WHITE_S, bevel=0.07)
    beam('bogie', bog, fr, 0.2, 0.26, WHITE_S, bevel=0.07)
    for p in (piv, bog): cyl('pivot', 0.2, 0.36, tuple(p), SATIN, rot=(math.pi / 2, 0, 0), segs=24)
    for p in (rear, midw, fr):
        rod('axle', p, (p.x, VY + sy * 1.68, p.z), 0.12, SATIN)
    beam('rocker_strip', piv + Vector((0, sy * 0.12, 0)), bog + Vector((0, sy * 0.12, 0)), 0.01, 0.05, CYAN, bevel=0)
# differential bar
rod('diff_bar', (VX - 0.4, VY - 1.4, 3.2), (VX - 0.4, VY + 1.4, 3.2), 0.07, SATIN)
for sy in (-1, 1): rod('diff_link', (VX - 0.4, VY + sy * 1.4, 3.2), (VX - 0.4, VY + sy * 1.55, 2.25), 0.05, SATIN)
# body
rbox('rov_body', (4.6, 2.7, 1.25), (VX, VY, 2.45), WHITE, r=0.4, segs=6)
rbox('rov_belly', (4.0, 2.2, 0.35), (VX, VY, 1.72), GRAPH, r=0.12, segs=3)
box('rov_strip_s', (3.8, 0.02, 0.07), (VX, VY - 1.351, 2.05), CYAN, bevel=0)
box('rov_strip_s2', (3.8, 0.02, 0.07), (VX, VY + 1.351, 2.05), CYAN, bevel=0)
rbox('rov_top', (3.0, 2.2, 0.35), (VX - 0.6, VY, 3.2), GRAPH, r=0.12, segs=3)
text('decal_rov', 'R-07', (VX - 0.9, VY - 1.36, 2.6), (math.pi / 2, 0, 0), 0.36, INK, extrude=0.006)
text('decal_rov2', 'MINE A-01', (VX + 0.9, VY - 1.36, 2.62), (math.pi / 2, 0, 0), 0.2, INK, extrude=0.006)
# cockpit / sensor head at the front
sphere('rov_head', 0.75, (VX + 1.7, VY + 0.55, 3.35), WHITE_S, scale=(0.9, 1.0, 0.55), sub=4)
sphere('rov_visor', 0.62, (VX + 1.98, VY + 0.55, 3.38), GLASS, scale=(0.75, 0.95, 0.38), sub=4)
box('rov_eye', (0.04, 0.9, 0.06), (VX + 2.42, VY + 0.55, 3.38), CYAN, bevel=0)
for dy in (-0.9, 0.9):
    rbox('rov_lamp', (0.2, 0.36, 0.2), (VX + 2.28, VY + dy, 2.55), GRAPH_S, r=0.06, segs=3)
    box('rov_lamp_l', (0.02, 0.28, 0.12), (VX + 2.39, VY + dy, 2.55), LAMP, bevel=0)
# rear sample bay with ore
rbox('bay', (1.6, 2.2, 0.55), (VX - 1.5, VY, 3.6), WHITE, r=0.12, segs=3)
box('bay_in', (1.4, 2.0, 0.1), (VX - 1.5, VY, 3.75), GRAPH, bevel=0)
ore_chunks('bay', (VX - 1.5, VY, 3.8), 0.75, 18, ORE_MIX, heap=0.15, size=(0.14, 0.26), seed=61)
# mast + antenna + solar wing
rod('mast', (VX + 1.0, VY - 0.9, 3.35), (VX + 1.0, VY - 0.9, 4.6), 0.07, SATIN)
rbox('mast_cam', (0.36, 0.5, 0.28), (VX + 1.05, VY - 0.9, 4.72), WHITE_S, r=0.08, segs=3)
box('mast_eye', (0.02, 0.32, 0.08), (VX + 1.24, VY - 0.9, 4.72), CYAN, bevel=0)
rod('whip', (VX - 2.0, VY + 0.9, 3.4), (VX - 2.2, VY + 0.9, 5.2), 0.025, SATIN)
sphere('whip_tip', 0.06, (VX - 2.2, VY + 0.9, 5.22), CYAN, sub=1)
# robotic arm reaching into the deposit
DX, DY = VX + 6.4, VY + 0.3
base = Vector((VX + 1.2, VY - 0.55, 3.15))
sh = base + Vector((0, 0, 0.55)); el = Vector((VX + 3.4, VY - 0.4, 5.0)); wr = Vector((VX + 4.75, VY - 0.2, 2.6)); tip = Vector((VX + 5.0, VY - 0.15, 1.35))
lathe('arm_base', [(0, 0), (0.45, 0), (0.42, 0.25), (0.3, 0.45), (0, 0.5)], tuple(base), GRAPH_S, segs=40)
ring('arm_base_glow', 0.43, (base.x, base.y, base.z + 0.12), 0.04, CYAN, w=0.02, segs=40)
sphere('j_sh', 0.32, tuple(sh), WHITE_S, sub=3)
beam('upper_arm', sh, el, 0.38, 0.42, WHITE, bevel=0.15)
beam('upper_arm_strip', sh + Vector((0, -0.2, 0.0)), el + Vector((0, -0.2, 0)), 0.02, 0.06, CYAN, bevel=0)
sphere('j_el', 0.28, tuple(el), GRAPH_S, sub=3)
beam('fore_arm', el, wr, 0.3, 0.34, WHITE, bevel=0.12)
sphere('j_wr', 0.22, tuple(wr), GRAPH_S, sub=3)
rod('tool', wr, tip + Vector((0, 0, 0.25)), 0.16, GRAPH_S, r2=0.1, segs=24)
ring('tool_glow', 0.17, (wr.x + (tip.x - wr.x) * 0.3, wr.y + (tip.y - wr.y) * 0.3, wr.z + (tip.z - wr.z) * 0.3), 0.05, CYAN, w=0.03, segs=24) if False else None
for a in (0, 2.1, 4.2):  # 3-finger gripper
    off = Vector((0.16 * math.cos(a), 0.16 * math.sin(a), 0))
    rod('finger', tip + Vector((0, 0, 0.35)) + off, tip + off * 1.4 - Vector((0, 0, 0.05)), 0.04, SATIN, segs=10)
sphere('arm_sample', 0.13, tuple(tip + Vector((0, 0, 0.12))), HE3, scale=(0.8, 0.8, 1.4), sub=1, jitter=0.2, smooth=False, seed=3)
for p0, p1 in ((sh, el), (el, wr)):
    cable('arm_hose', p0 + Vector((0, 0.3, 0)), p1 + Vector((0, 0.3, 0)), 0.035, GRAPH_S, sag=0.15)
# deposit outcrop (glowing He-3 seam)
heap('deposit', (DX, DY, 0.0), 2.6, 1.4, ROCK, seed=12)
for k in range(16):
    a = rr.uniform(0, TAU); dd = rr.uniform(0.2, 1.9); h = 1.4 * max(0, 1 - (dd / 2.6) ** 2)
    sphere('seam_crystal', rr.uniform(0.15, 0.32), (DX + dd * math.cos(a), DY + dd * math.sin(a), h + 0.1), HE3, scale=(0.5, 0.5, 1.8), sub=1, jitter=0.2, smooth=False, seed=k, rot=(rr.uniform(-0.6, 0.6), rr.uniform(-0.6, 0.6), 0))
ore_chunks('spill', (DX - 2.0, DY, 0.0), 1.4, 26, ORE_MIX, size=(0.1, 0.25), seed=34)

# ================= STAGE =================
height = build_stage(keep_flat=((1, 0, 22),))
world_and_sun((-0.55, -0.6, 0.58), 5.5)
astronaut((-1.6, -8.2, 0.0), rot_z=-0.5)
cam = setup_render(48 if not QUICK else 16)

ONLY = A.get('only', 'turn,hero')
if 'glb' in ONLY: export_glb(os.path.join(OUT, 'b_sleek_hightech_master.glb'))
if 'blend' in ONLY:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'b_sleek_hightech_master.blend'), compress=True)
if 'turn' in ONLY:
    turntable(cam, OUT, (1.0, 0.5, 4.5), 50, 22, size=1000 if not QUICK else 400, samples=48 if not QUICK else 12)
if 'hero' in ONLY:
    w, h = (3840, 2160) if not QUICK else (960, 540)
    shoot(cam, os.path.join(OUT, 'hero.png'), (0.0, 1.5, 6.6), (10.0, -31.0, 5.0), w, h, lens=24, samples=int(A.get('hs', 64)) if not QUICK else 16)
