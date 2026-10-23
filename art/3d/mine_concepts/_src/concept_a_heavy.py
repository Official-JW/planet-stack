"""Concept A - HEAVY INDUSTRIAL Mine A. blender -b -P concept_a_heavy.py -- --out DIR [--quick 1] [--only hero,turn,closeup]"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from mc_common import *
from mc_common import _obj

A = argv(); OUT = A.get('out', '/tmp/mc_a'); os.makedirs(OUT, exist_ok=True)
QUICK = A.get('quick') == '1'
reset(); rr = random.Random(21)

# ---------------- materials
YEL = M_paint('A_Yellow', '#f2b51d', rough=0.5, metal=0.1, grime=0.55, wear=0.45, wear_col='#8a8f95', bevel=0.02, dirt_scale=1.8)
HAZ = M_paint('A_Hazard', '#f2b51d', rough=0.5, metal=0.1, grime=0.45, wear=0.4, hazard=('#f2b51d', '#1b1d20'), hazard_scale=1.6)
STEEL = M_paint('A_Steel', '#59606a', rough=0.45, metal=0.75, grime=0.5, wear=0.3, wear_col='#b8bec6', bevel=0.015)
DARK = M_paint('A_DarkSteel', '#2b2e33', rough=0.55, metal=0.6, grime=0.35, wear=0.25, wear_col='#9aa0a6')
CHROME = M_paint('A_Chrome', '#e6e9ee', rough=0.12, metal=1.0, bevel=0.005)
RUBBER = M_paint('A_Rubber', '#1c1d1f', rough=0.85, metal=0.0, grime=0.4, grime_col='#5f5a54', bump_noise=0.3)
BELT = M_paint('A_Belt', '#222326', rough=0.9, metal=0.0, grime=0.5, grime_col='#6e6a64')
WHITE = M_paint('A_Stencil', '#f1f1ec', rough=0.6, metal=0.0)
BLACKT = M_paint('A_StencilDark', '#16181b', rough=0.6, metal=0.0)
RED = M_paint('A_Red', '#c8322a', rough=0.45, metal=0.1, grime=0.3)
GLASS = M_glass('A_Glass', '#7fa8b8', 0.08)
LAMP = M_glow('A_Lamp', '#fff1c8', 25)
AMBERL = M_glow('A_Amber', '#ff9a1a', 20)
CYANL = M_glow('A_Cyan', '#3ad0ff', 12)
HE3 = M_he3('A_He3'); PT = M_paint('A_Platinum', '#d8dde4', rough=0.18, metal=1.0, bevel=0.005)
ROCK = M_rock('A_OreRock', '#5d5a57', '#86827c', vein='#3ad0ff')
ORE_MIX = [(HE3, 4, 'he3'), (PT, 2, 'pt'), (ROCK, 5, 'rock')]

# ================= DRILL RIG =================
RX, RY = -7.5, 3.0
# heavy pad (steel deck plates on I-beam skid)
box('pad', (7.2, 7.2, 0.7), (RX, RY, 0.35), STEEL, bevel=0.06)
box('pad_haz_f', (7.24, 0.02, 0.32), (RX, RY - 3.61, 0.38), HAZ, bevel=0.0)
box('pad_haz_b', (7.24, 0.02, 0.32), (RX, RY + 3.61, 0.38), HAZ, bevel=0.0)
box('pad_haz_l', (0.02, 7.24, 0.32), (RX - 3.61, RY, 0.38), HAZ, bevel=0.0)
box('pad_haz_r', (0.02, 7.24, 0.32), (RX + 3.61, RY, 0.38), HAZ, bevel=0.0)
for i in range(6):   # deck plates
    for j in range(6):
        box('deckplate', (1.15, 1.15, 0.05), (RX - 2.9 + i * 1.16, RY - 2.9 + j * 1.16, 0.72), DARK, bevel=0.01)
bolts('pad_bolt', CHROME, [(RX - 3.4 + i * 0.45, RY - 3.62, 0.62) for i in range(16)], r=0.04, normal_rot=(math.pi / 2, 0, 0))
bolts('pad_bolt', CHROME, [(RX - 3.4 + i * 0.45, RY - 3.62, 0.12) for i in range(16)], r=0.04, normal_rot=(math.pi / 2, 0, 0))
# outrigger legs with hydraulic jacks
for sx in (-1, 1):
    for sy in (-1, 1):
        cx, cy = RX + sx * 3.0, RY + sy * 3.0
        fx, fy = RX + sx * 5.0, RY + sy * 5.0
        box('outrigger', (2.9, 0.7, 0.6), ((cx + fx) / 2 + sx * 0.2, (cy + fy) / 2 + sy * 0.2, 0.95), YEL, rot=(0, 0, math.atan2(sy, sx)), bevel=0.05)
        cyl('jack_body', 0.32, 1.2, (fx, fy, 1.1), YEL, segs=24, bevel=0.03)
        cyl('jack_rod', 0.18, 1.0, (fx, fy, 0.45), CHROME, segs=24)
        cyl('jack_foot', 0.85, 0.22, (fx, fy, 0.11), DARK, segs=10, bevel=0.03)
        cyl('jack_cap', 0.36, 0.12, (fx, fy, 1.76), DARK, segs=24)
        box('jack_haz', (0.02, 0.5, 0.25), (fx + 0.33 * (1 if sx > 0 else -1), fy, 1.2), HAZ, bevel=0)
# tower: 4 heavy box columns + X lattice
TW = 1.6; TOP = 16.5; Z0 = 0.75
cols = [(RX + sx * TW, RY + 0.6 + sy * TW) for sx in (-1, 1) for sy in (-1, 1)]
for (x, y) in cols:
    box('column', (0.5, 0.5, TOP - Z0), (x, y, (TOP + Z0) / 2), YEL, bevel=0.04)
    box('col_foot', (0.9, 0.9, 0.3), (x, y, Z0 + 0.15), DARK, bevel=0.04)
    bolts('col_bolt', CHROME, [(x + dx, y + dy, Z0 + 0.32) for dx in (-0.35, 0.35) for dy in (-0.35, 0.35)], r=0.05)
levels = [Z0 + 0.8 + i * 2.1 for i in range(8)]
faces = [((-1, -1), (1, -1)), ((-1, 1), (1, 1)), ((-1, -1), (-1, 1)), ((1, -1), (1, 1))]
for k, z in enumerate(levels):
    for (a, b) in faces:
        p0 = (RX + a[0] * TW, RY + 0.6 + a[1] * TW, z); p1 = (RX + b[0] * TW, RY + 0.6 + b[1] * TW, z)
        beam('girt', p0, p1, 0.32, 0.32, YEL, bevel=0.03)
    if k < len(levels) - 1:
        z1 = levels[k + 1]
        for fi, (a, b) in enumerate(faces):
            if fi == 0 and z < 9: continue   # front kept open low for the feed
            p0 = (RX + a[0] * TW, RY + 0.6 + a[1] * TW); p1 = (RX + b[0] * TW, RY + 0.6 + b[1] * TW)
            beam('brace', (*p0, z), (*p1, z1), 0.2, 0.2, YEL, bevel=0.02)
            beam('brace', (*p1, z), (*p0, z1), 0.2, 0.2, YEL, bevel=0.02)
            # gusset plates
            for p, zz in ((p0, z), (p1, z), (p0, z1), (p1, z1)):
                box('gusset', (0.42, 0.42, 0.42), (p[0], p[1], zz), DARK, bevel=0.03)
# ladder + cage on the right side
LX = RX + TW + 0.55
for dy in (-0.3, 0.3):
    box('ladder_rail', (0.06, 0.08, TOP - 1.2), (LX, RY + 0.6 + dy, (TOP + 1.2) / 2), STEEL, bevel=0.01)
for i in range(int((TOP - 1.6) / 0.35)):
    rod('rung', (LX, RY + 0.3, 1.4 + i * 0.35), (LX, RY + 0.9, 1.4 + i * 0.35), 0.022, STEEL, segs=8)
for i in range(10):
    z = 3.5 + i * 1.3
    curve_tube('cage', [(LX - 0.05, RY + 0.25, z)] + [(LX + 0.45 * math.sin(t / 8 * math.pi), RY + 0.6 - 0.35 * math.cos(t / 8 * math.pi), z) for t in range(9)] + [(LX - 0.05, RY + 0.95, z)], 0.025, STEEL)
# crown block with sheaves + catwalk
box('crown', (4.4, 4.4, 1.3), (RX, RY + 0.6, TOP + 0.65), YEL, bevel=0.08)
box('crown_haz', (4.44, 0.02, 0.45), (RX, RY + 0.6 - 2.21, TOP + 0.4), HAZ, bevel=0)
for dx in (-0.6, 0.6):
    cyl('sheave', 0.9, 0.3, (RX + dx, RY + 0.4, TOP + 1.9), DARK, rot=(0, math.pi / 2, 0), segs=36, bevel=0.03)
    cyl('sheave_hub', 0.3, 0.42, (RX + dx, RY + 0.4, TOP + 1.9), CHROME, rot=(0, math.pi / 2, 0), segs=24)
box('sheave_frame', (2.2, 0.35, 1.2), (RX, RY + 0.4, TOP + 1.7), YEL, bevel=0.04)
box('catwalk', (5.6, 5.6, 0.12), (RX, RY + 0.6, TOP + 1.36), DARK, bevel=0.01)
for (a, b) in faces:
    p0 = Vector((RX + a[0] * 2.8, RY + 0.6 + a[1] * 2.8, TOP + 2.4)); p1 = Vector((RX + b[0] * 2.8, RY + 0.6 + b[1] * 2.8, TOP + 2.4))
    rod('railing', p0, p1, 0.04, YEL, segs=8); rod('railing', p0 - Vector((0, 0, 0.5)), p1 - Vector((0, 0, 0.5)), 0.03, YEL, segs=8)
    for t in range(5):
        p = p0.lerp(p1, t / 4); rod('post', p, p - Vector((0, 0, 1.0)), 0.035, YEL, segs=8)
sphere('beacon', 0.22, (RX + 2.4, RY - 1.7, TOP + 2.6), AMBERL, sub=2)
cyl('beacon_base', 0.2, 0.2, (RX + 2.4, RY - 1.7, TOP + 2.4), DARK)
for dx in (-1.6, 1.6):   # floodlights
    box('flood', (0.6, 0.35, 0.4), (RX + dx, RY - 1.75, TOP + 1.0), DARK, rot=(0.5, 0, 0), bevel=0.04)
    box('flood_lens', (0.5, 0.02, 0.3), (RX + dx, RY - 1.95, TOP + 0.9), LAMP, rot=(0.5, 0, 0), bevel=0)
# carriage / rotary head
CZ = 9.6
box('head', (3.2, 2.4, 2.2), (RX, RY - 1.4, CZ), YEL, bevel=0.12, segs=3)
box('head_top', (2.6, 2.0, 0.5), (RX, RY - 1.4, CZ + 1.35), DARK, bevel=0.06)
for i in range(7):
    box('fin', (0.08, 1.9, 0.45), (RX - 1.2 + i * 0.4, RY - 1.4, CZ + 1.8), STEEL, bevel=0.01)
cyl('motor', 0.75, 1.2, (RX + 2.0, RY - 1.4, CZ + 0.2), DARK, rot=(0, math.pi / 2, 0), segs=32, bevel=0.03)
for i in range(10):
    cyl('motor_rib', 0.8, 0.05, (RX + 1.55 + i * 0.1, RY - 1.4, CZ + 0.2), STEEL, rot=(0, math.pi / 2, 0), segs=32, bevel=0)
cyl('gearbox', 1.1, 0.8, (RX, RY - 1.4, CZ - 1.4), DARK, segs=32, bevel=0.04)
bolts('gb_bolt', CHROME, [(RX + 1.05 * math.cos(a), RY - 1.4 + 1.05 * math.sin(a), CZ - 0.98) for a in [i * TAU / 16 for i in range(16)]], r=0.05)
box('head_haz', (3.24, 0.02, 0.5), (RX, RY - 2.61, CZ - 0.7), HAZ, bevel=0)
text('decal_a01', 'MINE A-01', (RX, RY - 2.62, CZ + 0.35), (math.pi / 2, 0, 0), 0.5, BLACKT, extrude=0.01)
text('decal_drill', 'DRILL 01  ·  12 MW', (RX, RY - 2.62, CZ - 0.15), (math.pi / 2, 0, 0), 0.2, BLACKT, extrude=0.01)
# guide shoes on columns
for sx in (-1, 1):
    box('shoe', (0.7, 1.2, 1.6), (RX + sx * 1.6, RY - 0.9, CZ), DARK, bevel=0.05)
    box('shoe_arm', (0.9, 0.5, 0.4), (RX + sx * 1.25, RY - 1.1, CZ), STEEL, bevel=0.03)
# feed pistons: pad -> head
for sx in (-1, 1):
    piston('feed', (RX + sx * 1.15, RY - 1.4, 1.0), (RX + sx * 1.15, RY - 1.4, CZ - 1.15), 0.28, YEL, CHROME, ext=0.5)
# giant auger (drill string + flights) into the ground
AXX, AXY = RX, RY - 1.4
cyl('kelly', 0.32, CZ - 1.8 - 3.0, (AXX, AXY, (CZ - 1.8 + 3.0) / 2), STEEL, segs=8, bevel=0.02)
cyl('core', 0.5, 3.3, (AXX, AXY, 1.55), STEEL, segs=24, bevel=0.02)
def helix(name, cx, cy, z0, z1, r_in, r_out, pitch, th, mat, spt=40):
    import bmesh
    n = int((z1 - z0) / pitch * spt); bm = bmesh.new(); rings = []
    for k in range(n + 1):
        a = TAU * k / spt; z = z0 + (z1 - z0) * k / n
        rings.append([bm.verts.new((cx + rr_ * math.cos(a), cy + rr_ * math.sin(a), z + dz)) for rr_, dz in ((r_in, -th / 2), (r_out, -th / 2), (r_out, th / 2), (r_in, th / 2))])
    for k in range(n):
        for i in range(4):
            j = (i + 1) % 4; bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
    bm.faces.new(rings[0]); bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(bm, name, mat, smooth=True, angle=45)
helix('auger', AXX, AXY, 0.2, 3.2, 0.48, 1.25, 1.0, 0.1, STEEL)
for k in range(6):
    a = k * TAU / 6
    box('tooth', (0.28, 0.14, 0.2), (AXX + 1.2 * math.cos(a), AXY + 1.2 * math.sin(a), 0.25), CHROME, rot=(0, 0, a), bevel=0.02)
for zz in (3.5, 5.2, 6.9):
    cyl('tooljoint', 0.42, 0.3, (AXX, AXY, zz), DARK, segs=8, bevel=0.03)
# collar spill ring + cuttings pile around the hole
cyl('collar', 1.75, 0.55, (AXX, AXY, 0.42), DARK, segs=40, bevel=0.04)
cyl('collar_hole', 1.42, 0.6, (AXX, AXY, 0.47), M_glow('A_HoleDark', '#000000', 0), segs=40, bevel=0)
heap('cuttings', (AXX - 0.3, AXY - 2.3, 0.0), 1.6, 0.45, ROCK, seed=7)
ore_chunks('cut', (AXX - 0.3, AXY - 2.4, 0.15), 1.4, 26, ORE_MIX, heap=0.3, size=(0.1, 0.24), seed=12)
# operator cab on the pad (back-left)
box('cab', (2.0, 1.8, 2.2), (RX - 2.2, RY + 2.2, 1.85), YEL, bevel=0.1, segs=3)
box('cab_win', (1.6, 0.04, 0.9), (RX - 2.2, RY + 1.29, 2.3), GLASS, bevel=0.02)
box('cab_win_s', (0.04, 1.2, 0.9), (RX - 3.21, RY + 2.2, 2.3), GLASS, bevel=0.02)
box('cab_roof', (2.3, 2.1, 0.18), (RX - 2.2, RY + 2.2, 3.03), DARK, bevel=0.03)
box('cab_haz', (2.04, 0.02, 0.3), (RX - 2.2, RY + 1.29, 0.95), HAZ, bevel=0)
box('ac_unit', (0.9, 0.7, 0.45), (RX - 2.0, RY + 2.4, 3.35), STEEL, bevel=0.04)
# power pack + hoses
box('powerpack', (2.4, 1.6, 1.6), (RX + 2.2, RY + 2.3, 1.55), DARK, bevel=0.08)
for i in range(9): box('grille', (0.04, 1.62, 1.0), (RX + 1.25 + i * 0.24, RY + 2.3, 1.6), STEEL, bevel=0)
text('decal_pp', 'HV  ⚡  600V', (RX + 2.2, RY + 1.48, 2.05), (math.pi / 2, 0, 0), 0.18, WHITE, extrude=0.008)
for k, (dx, col) in enumerate(((0.4, RUBBER), (0.7, RUBBER), (1.0, RED))):
    cable('hose', (RX + 1.2 + k * 0.2, RY + 1.5, 2.0), (RX + 1.2, RY - 0.4, CZ + 0.6), 0.07, col, sag=1.6, lateral=(0.6 + 0.2 * k, -0.3, 0))
# inclined screw conveyor: collar -> hopper
H_X, H_Y = -1.0, 3.0
S0 = Vector((AXX + 1.6, AXY + 0.2, 0.9)); S1 = Vector((H_X - 1.2, H_Y, 6.6))
rod('screw_tube', S0, S1, 0.55, YEL, segs=32)
for t in range(1, 9):
    p = S0.lerp(S1, t / 9); rod('screw_flange', p - (S1 - S0).normalized() * 0.06, p + (S1 - S0).normalized() * 0.06, 0.66, DARK, segs=32)
rod('screw_drive', S1, S1 + (S1 - S0).normalized() * 0.9, 0.42, DARK, segs=24)
box('screw_spout', (0.9, 0.9, 0.9), (H_X - 0.6, H_Y, 6.45), DARK, bevel=0.05)
for t in (0.33, 0.66):
    p = S0.lerp(S1, t); beam('screw_leg', (p.x, p.y - 0.6, 0.0), (p.x, p.y, p.z - 0.5), 0.25, 0.25, YEL); beam('screw_leg', (p.x, p.y + 0.6, 0.0), (p.x, p.y, p.z - 0.5), 0.25, 0.25, YEL)
# ================= HOPPER =================
import bmesh
def frustum(name, cx, cy, z0, z1, b, t, wall, mat):
    bm = bmesh.new()
    def ring(h, z): return [bm.verts.new((cx + sx * h, cy + sy * h, z)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    ob_, ot, it, ib = ring(b, z0), ring(t, z1), ring(t - wall, z1), ring(b - wall, z0 + wall)
    for A_, B_ in ((ob_, ot), (ot, it), (it, ib)):
        for i in range(4):
            j = (i + 1) % 4; bm.faces.new((A_[i], A_[j], B_[j], B_[i]))
    bm.faces.new(list(reversed(ob_))); bm.faces.new(ib)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(bm, name, mat, bevel=0.03)
HZ0, HZ1 = 4.0, 7.2
frustum('hopper', H_X, H_Y, HZ0, HZ1, 0.7, 2.3, 0.12, YEL)
for i in range(5):   # stiffener ribs on each face
    t = -1.6 + i * 0.8
    for sgn, ax in ((-1, 'y'), (1, 'y'), (-1, 'x'), (1, 'x')):
        if ax == 'y': p0 = (H_X + t * 0.7 / 2.3, H_Y + sgn * 0.75, HZ0 + 0.1); p1 = (H_X + t, H_Y + sgn * 2.33, HZ1 - 0.05)
        else: p0 = (H_X + sgn * 0.75, H_Y + t * 0.7 / 2.3, HZ0 + 0.1); p1 = (H_X + sgn * 2.33, H_Y + t, HZ1 - 0.05)
        beam('hop_rib', p0, p1, 0.1, 0.16, DARK, bevel=0.01)
for (a, b) in faces:
    ibeam('hop_rim', (H_X + a[0] * 2.4, H_Y + a[1] * 2.4, HZ1 + 0.1), (H_X + b[0] * 2.4, H_Y + b[1] * 2.4, HZ1 + 0.1), 0.3, 0.3, DARK)
for sx in (-1, 1):
    for sy in (-1, 1):
        ibeam('hop_leg', (H_X + sx * 1.6, H_Y + sy * 1.6, 0.0), (H_X + sx * 1.9, H_Y + sy * 1.9, HZ1 - 0.6), 0.36, 0.36, YEL)
        box('hop_foot', (0.9, 0.9, 0.25), (H_X + sx * 1.6, H_Y + sy * 1.6, 0.12), DARK, bevel=0.03)
for (a, b) in faces:
    beam('hop_brace', (H_X + a[0] * 1.68, H_Y + a[1] * 1.68, 1.4), (H_X + b[0] * 1.68, H_Y + b[1] * 1.68, 1.4), 0.2, 0.2, DARK)
box('hop_haz', (4.0, 0.02, 0.45), (H_X, H_Y - 2.2, HZ1 - 0.5), HAZ, rot=(-0.48, 0, 0), bevel=0)
text('decal_hop', 'HOPPER H-1', (H_X, H_Y - 2.08, HZ1 - 1.2), (math.pi / 2 - 0.48, 0, 0), 0.32, BLACKT, extrude=0.01)
box('hop_gate', (1.1, 1.1, 0.7), (H_X, H_Y, HZ0 - 0.35), DARK, bevel=0.05)
piston('gate_ram', (H_X - 0.4, H_Y - 1.0, HZ0 + 0.2), (H_X - 0.4, H_Y - 0.56, HZ0 - 0.4), 0.09, YEL, CHROME)
heap('hop_heap', (H_X, H_Y, HZ1 - 0.5), 2.1, 0.7, ROCK, sq=(2.15, 2.15), seed=4)
ore_chunks('hop', (H_X, H_Y, HZ1 - 0.25), 1.9, 70, ORE_MIX, heap=0.55, size=(0.14, 0.32), seed=5)
# ================= CONVEYOR (truss) =================
BIN_X, BIN_Y = 10.0, 4.5
C0 = Vector((H_X + 0.2, H_Y, HZ0 - 1.0)); C1 = Vector((BIN_X - 0.6, BIN_Y, 5.7))
d = (C1 - C0); L = d.length; u = d.normalized(); side = Vector((0, 0, 1)).cross(u).normalized(); up = u.cross(side).normalized()
W = 0.85
for s in (-1, 1):
    for hh in (0.0, 1.0):
        beam('chord', C0 + side * W * s + up * hh, C1 + side * W * s + up * hh, 0.16, 0.16, YEL, bevel=0.015)
    n = int(L / 1.2)
    for i in range(n + 1):
        p = C0 + u * (L * i / n) + side * W * s
        beam('vert', p, p + up * 1.0, 0.1, 0.1, YEL)
        if i < n:
            q = C0 + u * (L * (i + 1) / n) + side * W * s
            beam('diag', p + up * (0 if i % 2 else 1.0), q + up * (1.0 if i % 2 else 0), 0.09, 0.09, YEL)
nR = int(L / 0.55)
for i in range(nR + 1):
    p = C0 + u * (L * i / nR) + up * 0.25
    rod('roller', p - side * 0.7, p + side * 0.7, 0.08, STEEL, segs=12)
# belt (troughed look: center + 2 wings)
beam('belt', C0 + up * 0.35, C1 + up * 0.35, 1.1, 0.04, BELT, bevel=0.005)
for s in (-1, 1):
    a = C0 + up * 0.43 + side * 0.68 * s; b = C1 + up * 0.43 + side * 0.68 * s
    beam('belt_wing', a, b, 0.32, 0.04, BELT, up=(up + side * s * 0.0)).rotation_euler = (0, 0, 0)
# skirt boards
for s in (-1, 1):
    beam('skirt', C0 + up * 0.62 + side * 0.86 * s, C1 + up * 0.62 + side * 0.86 * s, 0.04, 0.4, DARK)
# ore riding on the belt
for i in range(55):
    t = rr.uniform(0.03, 0.97); p = C0 + u * (L * t) + up * 0.4 + side * rr.uniform(-0.4, 0.4)
    kind = rr.choices(['he3', 'pt', 'rock'], [4, 2, 4])[0]
    m = {'he3': HE3, 'pt': PT, 'rock': ROCK}[kind]
    ore_chunks('belt_ore', (p.x, p.y, p.z), 0.01, 1, [(m, 1, kind)], size=(0.15, 0.3), seed=i * 7 + 3)
# support towers
for t in (0.3, 0.68):
    p = C0 + u * (L * t)
    for s in (-1, 1):
        ibeam('conv_leg', (p.x + s * 0.0, p.y + s * 1.4, 0.0), (p.x, p.y + side.y * W * s, p.z - 0.05), 0.28, 0.28, DARK)
        box('conv_foot', (0.8, 0.8, 0.2), (p.x, p.y + s * 1.4, 0.1), DARK, bevel=0.03)
    beam('conv_tie', (p.x, p.y - 1.1, 1.6), (p.x, p.y + 1.1, 1.6), 0.18, 0.18, DARK)
# walkway handrail along the conveyor
for s in (1,):
    a = C0 + side * (W + 0.55) * s + up * 1.0; b = C1 + side * (W + 0.55) * s + up * 1.0
    beam('walkway', a - up * 0.05, b - up * 0.05, 0.6, 0.06, DARK)
    rod('hand', a + up * 1.0, b + up * 1.0, 0.035, YEL, segs=8)
    for i in range(int(L / 1.5) + 1):
        p = a.lerp(b, i / int(L / 1.5)); rod('hpost', p, p + up * 1.0, 0.03, YEL, segs=8)
# head pulley + drive
cyl('head_pulley', 0.45, 2.0, tuple(C1 + up * 0.3), DARK, rot=(math.pi / 2, 0, math.atan2(u.y, u.x)), segs=32)
box('drive', (0.9, 0.8, 0.8), tuple(C1 + side * 1.4 + up * 0.3), YEL, bevel=0.06)
cyl('discharge_chute', 0.75, 1.3, (C1.x + 0.35, C1.y, C1.z - 0.75), DARK, segs=24, r2=0.5)
box('chute_haz', (1.62, 0.04, 0.3), (C1.x + 0.35, C1.y - 0.76, C1.z - 0.35), HAZ, bevel=0)
# ================= ORE BIN =================
BW, BD, BH = 5.6, 4.6, 3.6
box('bin_floor', (BW, BD, 0.3), (BIN_X, BIN_Y, 0.15), DARK, bevel=0.03)
for sx in (-1, 1):
    box('bin_wall', (0.2, BD, BH), (BIN_X + sx * BW / 2, BIN_Y, BH / 2), YEL, bevel=0.04)
for sy in (-1, 1):
    box('bin_wall', (BW, 0.2, BH), (BIN_X, BIN_Y + sy * BD / 2, BH / 2), YEL, bevel=0.04)
for i in range(7):
    x = BIN_X - BW / 2 + 0.4 + i * (BW - 0.8) / 6
    box('bin_rib', (0.22, 0.2, BH), (x, BIN_Y - BD / 2 - 0.15, BH / 2), DARK, bevel=0.02)
    box('bin_rib', (0.22, 0.2, BH), (x, BIN_Y + BD / 2 + 0.15, BH / 2), DARK, bevel=0.02)
for i in range(5):
    y = BIN_Y - BD / 2 + 0.4 + i * (BD - 0.8) / 4
    box('bin_rib', (0.2, 0.22, BH), (BIN_X + BW / 2 + 0.15, y, BH / 2), DARK, bevel=0.02)
box('bin_rim', (BW + 0.5, 0.3, 0.3), (BIN_X, BIN_Y - BD / 2, BH + 0.1), DARK, bevel=0.03)
box('bin_rim', (BW + 0.5, 0.3, 0.3), (BIN_X, BIN_Y + BD / 2, BH + 0.1), DARK, bevel=0.03)
box('bin_rim', (0.3, BD, 0.3), (BIN_X + BW / 2, BIN_Y, BH + 0.1), DARK, bevel=0.03)
box('bin_rim', (0.3, BD, 0.3), (BIN_X - BW / 2, BIN_Y, BH + 0.1), DARK, bevel=0.03)
box('bin_haz', (BW + 0.1, 0.02, 0.5), (BIN_X, BIN_Y - BD / 2 - 0.27, 0.6), HAZ, bevel=0)
box('bin_plate', (2.6, 0.03, 1.0), (BIN_X, BIN_Y - BD / 2 - 0.27, 2.3), BLACKT, bevel=0.01)
text('decal_bin', 'ORE BIN 01', (BIN_X, BIN_Y - BD / 2 - 0.29, 2.45), (math.pi / 2, 0, 0), 0.42, WHITE, extrude=0.006)
text('decal_bin2', 'He-3 / Pt   MAX 40 t', (BIN_X, BIN_Y - BD / 2 - 0.29, 2.0), (math.pi / 2, 0, 0), 0.2, WHITE, extrude=0.006)
heap('bin_heap', (BIN_X, BIN_Y, BH - 0.6), 0, 1.3, ROCK, sq=(BW / 2 - 0.12, BD / 2 - 0.12), seed=9)
ore_chunks('bin', (BIN_X, BIN_Y, BH - 0.45), 2.0, 90, ORE_MIX, heap=1.2, size=(0.16, 0.36), seed=8)
# status mast with amber lamp on the bin corner
rod('bin_mast', (BIN_X + BW / 2, BIN_Y - BD / 2, BH), (BIN_X + BW / 2, BIN_Y - BD / 2, BH + 1.6), 0.06, DARK)
sphere('bin_lamp', 0.18, (BIN_X + BW / 2, BIN_Y - BD / 2, BH + 1.75), AMBERL, sub=2)

# ================= TRACKED ROVER =================
VX, VY = 1.6, -6.6
rov_parts = []
def P(o): rov_parts.append(o); return o
for sy in (-1, 1):
    ty = VY + sy * 1.55
    P(box('track_frame', (4.4, 0.7, 0.9), (VX, ty, 0.75), DARK, bevel=0.08, segs=3))
    for i, x in enumerate((-1.7, -0.85, 0.0, 0.85, 1.7)):
        P(cyl('roadwheel', 0.42 if i in (0, 4) else 0.34, 0.75, (VX + x, ty, 0.55 if i in (0, 4) else 0.42), STEEL, rot=(math.pi / 2, 0, 0), segs=24, bevel=0.03))
    P(cyl('sprocket', 0.55, 0.6, (VX - 2.05, ty, 0.95), YEL, rot=(math.pi / 2, 0, 0), segs=14, bevel=0.03))
    for (pos, ang) in stadium_path(VX, 0.7, 5.1, 0.62, 64):
        P(box('tread', (0.22, 0.84, 0.1), (pos[0], ty, pos[1]), RUBBER, rot=(0, ang, 0), bevel=0.02))
        P(box('grouser', (0.05, 0.84, 0.06), (pos[0] - 0.08 * math.cos(ang), ty, pos[1] + 0.08 * math.sin(ang) * 0), STEEL, rot=(0, ang, 0), bevel=0.0)) if False else None
P(box('chassis', (4.6, 2.4, 0.8), (VX, VY, 1.6), YEL, bevel=0.1, segs=3))
P(box('engine', (2.0, 2.3, 1.2), (VX - 1.3, VY, 2.6), YEL, bevel=0.12, segs=3))
for i in range(8): P(box('eng_grille', (0.04, 1.6, 0.7), (VX - 2.3 + i * 0.12, VY, 2.65), DARK, bevel=0))
P(cyl('exhaust', 0.12, 1.2, (VX - 1.0, VY + 0.8, 3.7), STEEL, segs=16))
P(box('cab', (1.6, 1.8, 1.6), (VX + 0.6, VY - 0.2, 2.8), YEL, bevel=0.12, segs=3))
P(box('cab_glass_f', (0.04, 1.4, 1.0), (VX + 1.41, VY - 0.2, 2.95), GLASS, bevel=0.02))
P(box('cab_glass_s', (1.1, 0.04, 0.9), (VX + 0.6, VY - 1.11, 2.95), GLASS, bevel=0.02))
for x in (VX - 0.25, VX + 1.45):
    for y in (VY - 1.15, VY + 0.75):
        P(rod('rops', (x, y, 2.0), (x, y, 3.85), 0.06, DARK, segs=10))
P(box('rops_top', (1.9, 2.1, 0.12), (VX + 0.6, VY - 0.2, 3.85), DARK, bevel=0.03))
for dy in (-0.6, 0.2):
    P(box('rov_light', (0.18, 0.3, 0.2), (VX + 1.5, VY + dy, 3.75), DARK, bevel=0.03))
    P(box('rov_lens', (0.02, 0.24, 0.14), (VX + 1.6, VY + dy, 3.75), LAMP, bevel=0))
P(sphere('rov_beacon', 0.13, (VX - 0.2, VY + 0.7, 4.0), AMBERL, sub=2))
P(box('rov_haz', (0.02, 2.44, 0.3), (VX + 2.31, VY, 1.55), HAZ, bevel=0))
P(text('decal_rov', 'R-07', (VX + 0.6, VY - 1.13, 2.2), (math.pi / 2, 0, 0), 0.32, BLACKT, extrude=0.008))
P(text('decal_rov2', 'MINE A-01', (VX - 1.3, VY - 1.17, 2.55), (math.pi / 2, 0, 0), 0.24, BLACKT, extrude=0.008))
# loader arms + bucket (digging into the deposit at +x)
BK = Vector((VX + 4.3, VY, 0.75))
for sy in (-1, 1):
    a = Vector((VX + 0.9, VY + sy * 1.15, 2.2)); b = Vector((BK.x - 0.4, VY + sy * 1.15, 1.3))
    P(beam('arm', a, (a + b) / 2 + Vector((0.4, 0, 0.55)), 0.3, 0.42, YEL, bevel=0.04))
    P(beam('arm', (a + b) / 2 + Vector((0.4, 0, 0.55)), b, 0.3, 0.42, YEL, bevel=0.04))
    P(piston('lift', (VX + 1.6, VY + sy * 1.3, 1.6), (BK.x - 1.6, VY + sy * 1.3, 2.05), 0.13, YEL, CHROME))
    P(piston('tilt', (VX + 2.1, VY + sy * 0.6, 2.3), (BK.x - 0.6, VY + sy * 0.6, 1.75), 0.1, YEL, CHROME))
P(rod('crossbar', (VX + 2.5, VY - 1.15, 2.2), (VX + 2.5, VY + 1.15, 2.2), 0.12, DARK))
P(box('bucket_back', (0.15, 2.8, 1.3), (BK.x - 0.6, VY, 1.15), YEL, rot=(0, -0.35, 0), bevel=0.04))
P(box('bucket_floor', (1.3, 2.8, 0.15), (BK.x, VY, 0.5), YEL, rot=(0, 0.12, 0), bevel=0.04))
for sy in (-1, 1): P(box('bucket_side', (1.4, 0.12, 1.0), (BK.x - 0.15, VY + sy * 1.4, 0.95), YEL, bevel=0.03))
for i in range(7): P(box('bucket_tooth', (0.35, 0.16, 0.12), (BK.x + 0.75, VY - 1.2 + i * 0.4, 0.42), CHROME, rot=(0, 0.2, 0), bevel=0.02))
ore_chunks('bucket', (BK.x - 0.05, VY, 0.75), 1.0, 22, ORE_MIX, heap=0.4, size=(0.16, 0.3), seed=31)
# deposit outcrop (glowing He-3 seam) the rover is digging
DX, DY = VX + 6.4, VY + 0.3
heap('deposit', (DX, DY, 0.0), 2.6, 1.4, ROCK, seed=12)
for k in range(16):
    a = rr.uniform(0, TAU); d = rr.uniform(0.2, 1.9); h = 1.4 * max(0, 1 - (d / 2.6) ** 2)
    sphere('seam_crystal', rr.uniform(0.15, 0.32), (DX + d * math.cos(a), DY + d * math.sin(a), h + 0.1), HE3, scale=(0.5, 0.5, 1.8), sub=1, jitter=0.2, smooth=False, seed=k, rot=(rr.uniform(-0.6, 0.6), rr.uniform(-0.6, 0.6), 0))
ore_chunks('spill', (DX - 2.0, DY, 0.0), 1.4, 30, ORE_MIX, size=(0.1, 0.25), seed=33)
# tire/track ruts behind the rover
for sy in ():
    box('rut', (14, 0.85, 0.04), (VX - 9.5, VY + sy * 1.55, 0.0), M_rock('A_Rut', '#55524f', '#6a6764'), bevel=0.0)

# ================= STAGE =================
height = build_stage(keep_flat=((1, 0, 22),))
world_and_sun((-0.55, -0.6, 0.58), 5.5)
astronaut((-1.6, -8.2, 0.0), rot_z=-0.5)
convert_curves()
cam = setup_render(48 if not QUICK else 16)

ONLY = A.get('only', 'turn,hero')
if 'glb' in ONLY: export_glb(os.path.join(OUT, 'a_heavy_industrial_master.glb'))
if 'blend' in ONLY:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'a_heavy_industrial_master.blend'), compress=True)
if 'turn' in ONLY:
    turntable(cam, OUT, (1.0, 0.5, 4.5), 50, 22, size=1000 if not QUICK else 400, samples=48 if not QUICK else 12)
if 'hero' in ONLY:
    w, h = (3840, 2160) if not QUICK else (960, 540)
    shoot(cam, os.path.join(OUT, 'hero.png'), (0.0, 1.5, 6.6), (10.0, -31.0, 5.0), w, h, lens=24, samples=int(A.get('hs', 64)) if not QUICK else 16)
