"""Planet Stack - LAUNCH PAD (PAD-01), high-detail concept master (Blender 4.2 LTS, headless, Cycles).

blender -b -P build_launch_pad.py -- --out .. [--quick 1] [--only glb,game,blend,hero,turn,close] [--dec 0.7]
       [--hs 64] [--ts 48] [--hc x,y,z,tx,ty,tz] [--lens 28]

Blender coords: Z up, metres, front = -Y (toward the camera). Exported GLB: Y up, front +Z, origin = pad centre on the ground.
Style: Mine concept B (sleek high-tech): glossy white + graphite panels, satin metal, cyan light strips, weathered + dusty.
Reuses the shared helpers in art/3d/mine_concepts/_src/mc_common.py by import (not modified).
True scale: 1.8 m astronauts, 40 m starter ship (appended read-only from art/3d/ship/starter_ship, Stage, not exported), 44 m service tower.

Systems (collection 'Mine' = exported building):
  * sintered regolith landing pad, r 21 m (fused glassy-grey slab tiles, scorched centre), painted landing target,
    PAD-01 stencils, 48 recessed edge lights + cyan perimeter strip, 4 flame-trench grates
  * blast berm r 27.5-36 m, 4.6 m high, with precast sintered retaining blocks, open toward the control station
  * service tower ST-01 (44 m lattice, decks, stairs, elevator) with crew (28 m), cargo (20 m) and fuel (7 m) access arms
    reaching the ship hull; pump skid with white radiators, LOX / CH4 lines in a covered trench through the berm
  * cargo handling: 3 cargo pods on a pallet + a pad-edge cargo lift (raises ship cargo capacity)
  * pad control station: ABOVE GROUND on 8 legs (2.4 m deck), two thick white shielded modules (HAB-1, OPS-1) with
    viewports, control cab PC-01, roof radiators RAD-P1, sensor mast + dish, airlock A1 with hatch + 2 suitports,
    dust-off porch (air-knife arch, boot brushes, grated deck), stair + handrails everywhere
  * power: cable run on low stanchions from a distant fission reactor behind its own berm (Stage), plus 2 solar
    arrays on tall masts (SOL-1, SOL-2) and junction PWR-01
Outputs: launch_pad_master.glb (full detail), launch_pad_game.glb (SH_* palette, merged by material, <=30k tris, meshopt, <=0.9 MB), .blend, hero, turntable.
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
MC = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'mine_concepts', '_src'))
sys.path.insert(0, MC)
import bpy, bmesh
from mathutils import Vector, Matrix, noise
from mc_common import *
from mc_common import _obj, _nodes

A = argv(); OUT = os.path.abspath(A.get('out', '/tmp/lp_out')); os.makedirs(OUT, exist_ok=True)
QUICK = A.get('quick') == '1'
reset(); rr = random.Random(101)
TAU = math.tau
NAME = 'launch_pad'

# ====================================================================== materials
def add_dust(m, top=1.2, amt=0.8, col='#8e8982', upamt=0.3):
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; inp = b.inputs['Base Color']
    if inp.links: src = inp.links[0].from_socket
    else:
        rgb = nt.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = tuple(inp.default_value); src = rgb.outputs[0]
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sp = nt.nodes.new('ShaderNodeSeparateXYZ'); link(nt, geo.outputs['Position'], sp.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = top
    mr.inputs['To Min'].default_value = amt; mr.inputs['To Max'].default_value = 0.0; link(nt, sp.outputs['Z'], mr.inputs['Value'])
    sn = nt.nodes.new('ShaderNodeSeparateXYZ'); link(nt, geo.outputs['Normal'], sn.inputs['Vector'])
    ur = nt.nodes.new('ShaderNodeMapRange'); ur.inputs['From Min'].default_value = 0.6; ur.inputs['From Max'].default_value = 0.98
    ur.inputs['To Max'].default_value = upamt; link(nt, sn.outputs['Z'], ur.inputs['Value'])
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'; link(nt, mr.outputs[0], ad.inputs[0]); link(nt, ur.outputs[0], ad.inputs[1])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 8
    link(nt, geo.outputs['Position'], nz.inputs['Vector'])
    nr = nt.nodes.new('ShaderNodeMapRange'); nr.inputs['From Min'].default_value = 0.35; nr.inputs['From Max'].default_value = 0.65
    nr.inputs['To Min'].default_value = 0.35; link(nt, nz.outputs['Fac'], nr.inputs['Value'])
    mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.use_clamp = True
    link(nt, ad.outputs[0], mu.inputs[0]); link(nt, nr.outputs[0], mu.inputs[1])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    link(nt, mu.outputs[0], mx.inputs['Factor']); link(nt, src, mx.inputs[6]); mx.inputs[7].default_value = hexc(col)
    link(nt, mx.outputs[2], inp)
    return m

def P_(name, color, dust=True, **kw):
    m = M_paint(name, color, **kw)
    return add_dust(m) if dust else m

WHITE   = P_('LP_White', '#eceff2', rough=0.22, metal=0.0, coat=0.8, grime=0.22, grime_col='#a59f97', wear=0.12, wear_col='#9aa3ad', panel=0.8, bevel=0.03, dirt_scale=1.4)
WHITE_S = P_('LP_WhiteSmooth', '#eef1f4', rough=0.2, metal=0.0, coat=0.9, grime=0.16, grime_col='#a59f97', wear=0.1, wear_col='#9aa3ad', bevel=0.03)
RAD     = P_('LP_Radiator', '#f2f4f7', rough=0.3, metal=0.0, coat=0.4, grime=0.14, grime_col='#a59f97', panel=4.0, bevel=0.01)
GRAPH   = P_('LP_Graphite', '#2c3137', rough=0.3, metal=0.55, coat=0.5, grime=0.16, grime_col='#6b665f', wear=0.2, wear_col='#9aa0a6', panel=1.4, bevel=0.02)
GRAPH_S = P_('LP_GraphiteSmooth', '#30353c', rough=0.28, metal=0.6, coat=0.5, grime=0.16, grime_col='#6b665f', wear=0.18, wear_col='#9aa0a6', bevel=0.02)
SATIN   = P_('LP_Satin', '#9aa3ad', rough=0.25, metal=1.0, grime=0.2, grime_col='#5a5650', wear=0.1, wear_col='#d0d5db', bevel=0.01)
RUBBER  = P_('LP_Rubber', '#1d2024', rough=0.8, metal=0.0, grime=0.3, grime_col='#6e6a64', bump_noise=0.3)
FOIL    = P_('LP_MLI', '#c9ced6', rough=0.3, metal=0.9, grime=0.2, grime_col='#5b5650', bump_noise=0.5, bevel=0.01)
PAINT   = P_('LP_PadPaint', '#e9ecef', rough=0.55, metal=0.0, grime=0.45, grime_col='#5e5b58', dirt_scale=0.6, upamt=0.0) if False else None
INK     = M_paint('LP_Ink', '#1f2329', rough=0.5, metal=0.0)
INKW    = M_paint('LP_InkWhite', '#f4f7fa', rough=0.4, metal=0.0)
LOXB    = P_('LP_LoxBand', '#2f7fe0', rough=0.3, metal=0.1, coat=0.5, grime=0.15)
CH4B    = P_('LP_Ch4Band', '#e8701a', rough=0.3, metal=0.1, coat=0.5, grime=0.15)
CYAN    = M_glow('LP_Cyan', '#2fe3ff', 16)
CYANS   = M_glow('LP_CyanSoft', '#2fe3ff', 5)
LAMP    = M_glow('LP_Lamp', '#f2fbff', 25)
AMBERG  = M_glow('LP_AmberLamp', '#ffb020', 14)
GLASS   = M_glass('LP_Lens', '#1b2a36', 0.04)
REGO    = M_rock('LP_Regolith', '#6f6c69', '#958f89')

def M_pad_paint():
    m = bpy.data.materials.new('LP_PadPaint'); nt, b = _nodes(m)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 9
    link(nt, tc.outputs['Object'], nz.inputs['Vector'])
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].position = 0.42; rp.color_ramp.elements[1].position = 0.62
    rp.color_ramp.elements[0].color = hexc('#9c9893'); rp.color_ramp.elements[1].color = hexc('#e6e8ea')
    link(nt, nz.outputs['Fac'], rp.inputs['Fac']); link(nt, rp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.6
    m.diffuse_color = hexc('#e6e8ea'); return m
PAINT = M_pad_paint()

def M_sinter(name='LP_Sintered'):
    """fused glassy-grey regolith slab: tile cracks, glassy sheen, scorched centre, dust drifting in from the edge."""
    m = bpy.data.materials.new(name); nt, b = _nodes(m)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.9; nz.inputs['Detail'].default_value = 10
    link(nt, tc.outputs['Object'], nz.inputs['Vector'])
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = hexc('#3b3c40'); rp.color_ramp.elements[1].color = hexc('#66666a')
    link(nt, nz.outputs['Fac'], rp.inputs['Fac'])
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 0.42
    link(nt, tc.outputs['Object'], vo.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeMapRange'); cr.inputs['From Min'].default_value = 0.012; cr.inputs['From Max'].default_value = 0.0
    link(nt, vo.outputs['Distance'], cr.inputs['Value'])
    vc = nt.nodes.new('ShaderNodeTexVoronoi'); vc.inputs['Scale'].default_value = 0.42; link(nt, tc.outputs['Object'], vc.inputs['Vector'])
    bw = nt.nodes.new('ShaderNodeRGBToBW'); link(nt, vc.outputs['Color'], bw.inputs['Color'])
    tint = nt.nodes.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.inputs['Factor'].default_value = 0.35
    link(nt, rp.outputs['Color'], tint.inputs[6]); link(nt, bw.outputs['Val'], tint.inputs[7])
    vl = nt.nodes.new('ShaderNodeVectorMath'); vl.operation = 'LENGTH'; link(nt, tc.outputs['Object'], vl.inputs[0])
    sc = nt.nodes.new('ShaderNodeMapRange'); sc.inputs['From Min'].default_value = 1.5; sc.inputs['From Max'].default_value = 7.5
    sc.inputs['To Min'].default_value = 0.75; sc.inputs['To Max'].default_value = 0.0; link(nt, vl.outputs['Value'], sc.inputs['Value'])
    sn = nt.nodes.new('ShaderNodeTexNoise'); sn.inputs['Scale'].default_value = 0.7; sn.inputs['Detail'].default_value = 4
    link(nt, tc.outputs['Object'], sn.inputs['Vector'])
    sm = nt.nodes.new('ShaderNodeMath'); sm.operation = 'MULTIPLY'; link(nt, sc.outputs[0], sm.inputs[0]); link(nt, sn.outputs['Fac'], sm.inputs[1])
    sm2 = nt.nodes.new('ShaderNodeMath'); sm2.operation = 'MULTIPLY'; sm2.inputs[1].default_value = 1.6; sm2.use_clamp = True
    link(nt, sm.outputs[0], sm2.inputs[0])
    m1 = nt.nodes.new('ShaderNodeMix'); m1.data_type = 'RGBA'; link(nt, sm2.outputs[0], m1.inputs['Factor'])
    link(nt, tint.outputs[2], m1.inputs[6]); m1.inputs[7].default_value = hexc('#1c1b1d')
    m2 = nt.nodes.new('ShaderNodeMix'); m2.data_type = 'RGBA'; link(nt, cr.outputs[0], m2.inputs['Factor'])
    link(nt, m1.outputs[2], m2.inputs[6]); m2.inputs[7].default_value = hexc('#17171a')
    # dust drifts in from the rim
    dr = nt.nodes.new('ShaderNodeMapRange'); dr.inputs['From Min'].default_value = 8.0; dr.inputs['From Max'].default_value = 11.0
    dr.inputs['To Max'].default_value = 0.8; link(nt, vl.outputs['Value'], dr.inputs['Value'])
    dn = nt.nodes.new('ShaderNodeTexNoise'); dn.inputs['Scale'].default_value = 1.3; dn.inputs['Detail'].default_value = 8
    link(nt, tc.outputs['Object'], dn.inputs['Vector'])
    dnr = nt.nodes.new('ShaderNodeMapRange'); dnr.inputs['From Min'].default_value = 0.4; dnr.inputs['From Max'].default_value = 0.6
    dnr.inputs['To Min'].default_value = 0.25; link(nt, dn.outputs['Fac'], dnr.inputs['Value'])
    dm = nt.nodes.new('ShaderNodeMath'); dm.operation = 'MULTIPLY'; link(nt, dr.outputs[0], dm.inputs[0]); link(nt, dnr.outputs[0], dm.inputs[1])
    m3 = nt.nodes.new('ShaderNodeMix'); m3.data_type = 'RGBA'; link(nt, dm.outputs[0], m3.inputs['Factor'])
    link(nt, m2.outputs[2], m3.inputs[6]); m3.inputs[7].default_value = hexc('#8a8782')
    link(nt, m3.outputs[2], b.inputs['Base Color'])
    rg = nt.nodes.new('ShaderNodeMapRange'); rg.inputs['To Min'].default_value = 0.16; rg.inputs['To Max'].default_value = 0.5
    link(nt, nz.outputs['Fac'], rg.inputs['Value'])
    ra = nt.nodes.new('ShaderNodeMath'); ra.operation = 'ADD'; ra.use_clamp = True; link(nt, rg.outputs[0], ra.inputs[0]); link(nt, dm.outputs[0], ra.inputs[1])
    link(nt, ra.outputs[0], b.inputs['Roughness'])
    b.inputs['Coat Weight'].default_value = 0.35; b.inputs['Coat Roughness'].default_value = 0.12
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.5; bump.inputs['Distance'].default_value = 0.02
    bump.invert = True; link(nt, cr.outputs[0], bump.inputs['Height']); link(nt, bump.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = hexc('#505055'); return m
SINTER = M_sinter()
BLOCK = P_('LP_SinterBlock', '#5c5b5d', rough=0.5, metal=0.0, grime=0.35, grime_col='#8a8782', bump_noise=0.4, bevel=0.03, dirt_scale=1.0)

# ====================================================================== helpers
def lathe(name, prof, loc, mat, segs=48, bevel=0.0, smooth=True, c='Mine', a0=0.0, a1=None):
    bm = bmesh.new(); rings = []
    full = a1 is None; n = segs if full else segs + 1
    for (r, z) in prof:
        if r < 1e-5: rings.append([bm.verts.new((loc[0], loc[1], loc[2] + z))])
        else:
            rings.append([bm.verts.new((loc[0] + r * math.cos(a0 + (TAU if full else a1 - a0) * k / segs),
                                        loc[1] + r * math.sin(a0 + (TAU if full else a1 - a0) * k / segs), loc[2] + z)) for k in range(n)])
    for a, b in zip(rings, rings[1:]):
        for k in range(segs):
            k2 = (k + 1) % n
            if len(a) == 1: bm.faces.new((a[0], b[k], b[k2]))
            elif len(b) == 1: bm.faces.new((a[k], a[k2], b[0]))
            else: bm.faces.new((a[k], a[k2], b[k2], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(bm, name, mat, c, smooth=smooth, bevel=bevel, angle=50)

def ring(name, r, loc, h, mat, w=0.06, segs=64, c='Mine'):
    x, y, z = loc
    return lathe(name, [(r - w, z - h / 2), (r, z - h / 2), (r, z + h / 2), (r - w, z + h / 2), (r - w, z - h / 2)], (x, y, 0), mat, segs=segs, c=c)

def annulus(name, r0, r1, z, mat, segs=96, c='Mine', a0=0.0, a1=None):
    return lathe(name, [(r0, z), (r1, z)], (0, 0, 0), mat, segs=segs, c=c, a0=a0, a1=a1, smooth=False)

def rbox(name, size, loc, mat, rot=(0, 0, 0), r=0.2, segs=5, c='Mine'):
    return box(name, size, loc, mat, rot=rot, bevel=r, segs=segs, c=c)

def handrail(p0, p1, h=1.05, n=None, mat=None, c='Mine', r=0.03):
    """posts + top rail + mid rail between two ground points (z given in p)."""
    mat = mat or SATIN; a, b = Vector(p0), Vector(p1); L = (b - a).length; n = n or max(2, int(L / 1.4) + 1)
    for i in range(n):
        p = a.lerp(b, i / (n - 1)); rod('rail_post', p, p + Vector((0, 0, h)), r, mat, segs=10, c=c)
    rod('rail_top', a + Vector((0, 0, h)), b + Vector((0, 0, h)), r * 1.1, mat, segs=10, c=c)
    rod('rail_mid', a + Vector((0, 0, h * 0.5)), b + Vector((0, 0, h * 0.5)), r * 0.8, mat, segs=8, c=c)

def mound(name, cx, cy, hx, hy, H, slope, mat, c='Mine', seed=3, step=0.35):
    rr2 = random.Random(seed); off = Vector((rr2.random() * 50, rr2.random() * 50, 0))
    ex, ey = hx + slope, hy + slope; nx, ny = int(2 * ex / step), int(2 * ey / step)
    bm = bmesh.new(); vs = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = -ex + 2 * ex * i / nx; y = -ey + 2 * ey * j / ny
            dx = max(0.0, abs(x) - hx); dy = max(0.0, abs(y) - hy); d = math.hypot(dx, dy) / slope
            t = max(0.0, 1 - d); z = H * (t * t * (3 - 2 * t)) ** 0.85
            z += 0.18 * noise.noise(Vector((x, y, 0)) * 0.6 + off) * min(1, t * 3) + 0.05 * noise.noise(Vector((x, y, 0)) * 2.5 + off)
            vs[i, j] = bm.verts.new((cx + x, cy + y, z - 0.06))
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
    return _obj(bm, name, mat, c, smooth=True, angle=180)

def berm(name, cx, cy, r_in, r_out, H, a0, a1, mat, c='Mine', seed=7, nseg=220, nrad=18, taper=0.32, peak=0.32):
    rr2 = random.Random(seed); off = Vector((rr2.random() * 50, rr2.random() * 50, 0))
    bm = bmesh.new(); vs = {}
    for i in range(nseg + 1):
        a = a0 + (a1 - a0) * i / nseg
        te = max(0.0, min(1.0, (a - a0) / taper, (a1 - a) / taper)); te = te * te * (3 - 2 * te)
        for j in range(nrad + 1):
            r = r_in - 0.4 + (r_out - r_in + 0.8) * j / nrad; u = (r - r_in) / (r_out - r_in)
            if u <= 0 or u >= 1: h = 0.0
            elif u < peak: h = math.sin(u / peak * math.pi / 2) ** 0.7
            else: h = math.cos((u - peak) / (1 - peak) * math.pi / 2) ** 1.3
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            hh = H * h * te * (1 + 0.12 * noise.noise(Vector((x * 0.15, y * 0.15, 0)) + off))
            hh += 0.08 * noise.noise(Vector((x, y, 0)) * 1.4 + off) * min(1, h * 4)
            vs[i, j] = bm.verts.new((x, y, hh - 0.06))
    for i in range(nseg):
        for j in range(nrad):
            bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0: f.normal_flip()
    return _obj(bm, name, mat, c, smooth=True, angle=180)

def berm_h(r, r_in, r_out, H, peak=0.32):
    u = (r - r_in) / (r_out - r_in)
    if u <= 0 or u >= 1: return 0.0
    return H * (math.sin(u / peak * math.pi / 2) ** 0.7 if u < peak else math.cos((u - peak) / (1 - peak) * math.pi / 2) ** 1.3)

def facing(v):
    return Vector(v).normalized().to_track_quat('Z', 'Y').to_euler()

def lin(a, b): return Vector(a).lerp(Vector(b), 0.5)

# ====================================================================== STAGE FIRST (so legs / feet can follow the ground)
SX, SY = -36.0, -31.0            # crew / pad-control station centre (above ground)
RXr, RYr = -82.0, 52.0           # distant fission plant
height = build_stage(keep_flat=((0, 0, 54), (0, 0, 54), (SX, SY, 22), (SX, SY, 22), (RXr, RYr, 24), (RXr, RYr, 24)))
def gz(x, y): return height(x, y)

# ====================================================================== PAD (sized for a ~40 m ship)
PAD_R = 21.0; TOP = 0.25; S = PAD_R / 10.8
lathe('pad_slab', [(0, -0.15), (PAD_R, -0.15), (PAD_R, 0.08), (PAD_R - 0.6, TOP), (0, TOP)], (0, 0, 0), SINTER, segs=192)
lathe('pad_apron', [(PAD_R - 0.2, -0.12), (PAD_R + 3.2, -0.12), (PAD_R + 3.2, 0.0), (PAD_R + 2.6, 0.05), (PAD_R - 0.2, 0.08)], (0, 0, 0), REGO, segs=192)
Z = TOP + 0.004
for r0, r1 in ((6.3, 6.9), (2.7, 3.05), (8.6, 8.75)):
    annulus('target_ring', r0 * S, r1 * S, Z, PAINT, segs=192)
for k in range(4):
    a = TAU * k / 4 + math.pi / 4
    box('target_bar', (2.6 * S, 0.42 * S, 0.008), (4.75 * S * math.cos(a), 4.75 * S * math.sin(a), Z), PAINT, rot=(0, 0, a), bevel=0)
for k in range(12):
    a = TAU * k / 12
    box('target_tick', (0.9 * S, 0.14 * S, 0.008), (7.6 * S * math.cos(a), 7.6 * S * math.sin(a), Z), PAINT, rot=(0, 0, a), bevel=0)
text('stencil_pad', 'PAD-01', (0, -7.75 * S, Z + 0.002), (0, 0, 0), 1.25 * S, PAINT, extrude=0.002)
text('stencil_pad_b', 'PAD-01', (0, 7.75 * S, Z + 0.002), (0, 0, math.pi), 1.25 * S, PAINT, extrude=0.002)
annulus('pad_strip', PAD_R - 1.6, PAD_R - 1.4, TOP + 0.005, CYAN, segs=256)
for k in range(48):
    a = TAU * k / 48; x, y = (PAD_R - 0.85) * math.cos(a), (PAD_R - 0.85) * math.sin(a)
    rbox('edge_light', (0.4, 0.7, 0.12), (x, y, TOP + 0.04), GRAPH_S, rot=(0, 0, a), r=0.04, segs=2)
    box('edge_lens', (0.24, 0.5, 0.02), (x, y, TOP + 0.105), LAMP if k % 4 else AMBERG, rot=(0, 0, a), bevel=0)
for k in range(80):
    a = TAU * (k + 0.5) / 80
    box('rim_tile', (0.7, 1.62, 0.16), ((PAD_R + 0.08) * math.cos(a), (PAD_R + 0.08) * math.sin(a), 0.03), GRAPH, rot=(0, 0, a), bevel=0.03)
# flame-trench grates under the engines
for k in range(4):
    a = TAU * k / 4
    box('flame_grate', (5.5, 1.6, 0.04), (5.2 * math.cos(a), 5.2 * math.sin(a), TOP + 0.01), GRAPH_S, rot=(0, 0, a), bevel=0.01)

# ====================================================================== BLAST BERM (open toward the station / access road)
B_IN, B_OUT, B_H = 27.5, 36.0, 4.6
GAP_C, GAP_W = math.radians(-128), math.radians(26)
BA0, BA1 = GAP_C + GAP_W, GAP_C - GAP_W + TAU
berm('blast_berm', 0, 0, B_IN, B_OUT, B_H, BA0, BA1, REGO, seed=9, nseg=300, nrad=22)
nblk = 120
for k in range(nblk + 1):
    a = BA0 + 0.22 + (BA1 - BA0 - 0.44) * k / nblk
    hgt = 3.3 + rr.uniform(-0.12, 0.12); r = B_IN + 0.35
    x, y = r * math.cos(a), r * math.sin(a)
    box('berm_block', (0.9, 1.5, hgt), (x, y, hgt / 2 - 0.05), BLOCK, rot=(rr.uniform(-0.03, 0.03), -0.12, a), bevel=0.05)
    if k % 2 == 0: box('berm_cap', (1.0, 1.48, 0.16), (x + 0.08 * math.cos(a), y + 0.08 * math.sin(a), hgt + 0.02), GRAPH, rot=(0, -0.12, a), bevel=0.03)
for a in (BA0 + 0.22, BA1 - 0.22):
    x, y = (B_IN + 0.35) * math.cos(a), (B_IN + 0.35) * math.sin(a)
    rbox('berm_endpost', (1.2, 1.2, 4.2), (x, y, 2.1), WHITE, rot=(0, 0, a), r=0.22, segs=3)
    box('berm_endstrip', (1.22, 1.22, 0.1), (x, y, 3.4), CYAN, rot=(0, 0, a), bevel=0)
    sphere('berm_beacon', 0.18, (x, y, 4.35), AMBERG, sub=2)

# ====================================================================== STARTER SHIP (real model, appended read-only from art/3d/ship/starter_ship) - Stage
SR = 4.0; SC = 'Stage'   # hull radius of the real ship (8 m dia, 40 m tall, 6 legs at 0/60/.., ramp toward -Y)
SHIP_BLEND = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'ship', 'starter_ship', 'starter_ship_master.blend'))
with bpy.data.libraries.load(SHIP_BLEND, link=False) as (src, dst):
    dst.collections = [n for n in src.collections if n == 'Mine']
ship_c = dst.collections[0]; ship_c.name = 'StarterShip'
coll(SC).children.link(ship_c)
for ob in ship_c.all_objects:
    if ob.parent is None: ob.location.z += TOP        # stand on the sintered pad top
UA = math.radians(30)    # tower azimuth: midway between the ship legs at 0 deg and 60 deg

# ====================================================================== SERVICE TOWER (~44 m) with access arms
TD = 13.5
u_t = Vector((math.cos(UA), math.sin(UA), 0)); TX, TY = u_t.x * TD, u_t.y * TD
inward = -u_t; tang = Vector((-u_t.y, u_t.x, 0)); rot_u = math.atan2(inward.y, inward.x)
TW, TH = 5.0, 44.0
rbox('tower_plinth', (8.0, 8.0, 0.9), (TX, TY, 0.42), GRAPH, rot=(0, 0, rot_u), r=0.15, segs=3)
box('tower_plinth_strip', (8.02, 8.02, 0.08), (TX, TY, 0.7), CYANS, rot=(0, 0, rot_u), bevel=0)
corners = [Vector((TX, TY, 0)) + inward * (TW / 2) * sx + tang * (TW / 2) * sy for sx in (-1, 1) for sy in (-1, 1)]
for c in corners:
    rbox('tower_column', (0.75, 0.75, TH), (c.x, c.y, 0.85 + TH / 2), WHITE, rot=(0, 0, rot_u), r=0.12, segs=3)
LV = [0.85 + 5.5 * i for i in range(9)]
faces = [(0, 1), (1, 3), (3, 2), (2, 0)]
for zi, z in enumerate(LV):
    for i, j in faces:
        a, b = corners[i] + Vector((0, 0, z)), corners[j] + Vector((0, 0, z))
        beam('tower_girt', a, b, 0.45, 0.45, GRAPH, bevel=0.06)
        if zi < len(LV) - 1:   # X bracing
            a2, b2 = corners[i] + Vector((0, 0, LV[zi + 1])), corners[j] + Vector((0, 0, LV[zi + 1]))
            beam('tower_brace', a, b2, 0.22, 0.22, GRAPH_S, bevel=0.03); beam('tower_brace', b, a2, 0.22, 0.22, GRAPH_S, bevel=0.03)
    if zi in (2, 4, 6, 8):   # service decks with handrails
        rbox('tower_deck', (TW + 1.6, TW + 1.6, 0.25), (TX, TY, z + 0.3), GRAPH_S, rot=(0, 0, rot_u), r=0.05, segs=2)
        for i, j in faces:
            a = corners[i] + (corners[i] - Vector((TX, TY, 0))).normalized() * 1.1 + Vector((0, 0, z + 0.42))
            b = corners[j] + (corners[j] - Vector((TX, TY, 0))).normalized() * 1.1 + Vector((0, 0, z + 0.42))
            handrail(a, b, h=1.1, n=4, r=0.035)
# elevator core + cyan strip
rbox('tower_core', (2.0, 2.0, TH - 1.0), (TX, TY, 0.85 + (TH - 1.0) / 2), WHITE_S, rot=(0, 0, rot_u), r=0.2, segs=3)
box('tower_core_strip', (0.04, 0.2, TH - 4.0), tuple(Vector((TX, TY, 0.85 + TH / 2)) + inward * 1.01), CYAN, rot=(0, 0, rot_u), bevel=0)
# stair flights zig-zag on the outward face (lowest 3 bays)
for i in range(3):
    z0, z1 = LV[i], LV[i + 1]; s = 1 if i % 2 == 0 else -1
    a = Vector((TX, TY, z0 + 0.3)) - inward * (TW / 2 + 0.9) - tang * 1.9 * s
    b = Vector((TX, TY, z1 + 0.3)) - inward * (TW / 2 + 0.9) + tang * 1.9 * s
    beam('tower_stair', a, b, 1.1, 0.18, GRAPH_S, bevel=0.03)
    for k in range(14):
        p = a.lerp(b, (k + 0.5) / 14) + Vector((0, 0, 0.1)); box('stair_tread', (0.3, 1.0, 0.04), tuple(p), SATIN, rot=(0, 0, rot_u + math.pi / 2), bevel=0)
    rod('stair_rail', a - inward * 0.55 + Vector((0, 0, 1.0)), b - inward * 0.55 + Vector((0, 0, 1.0)), 0.035, SATIN, segs=8)
    rbox('stair_landing', (1.6, 4.6, 0.2), tuple(Vector((TX, TY, z1 + 0.2)) - inward * (TW / 2 + 0.9) + tang * 1.9 * s), GRAPH_S, rot=(0, 0, rot_u), r=0.04, segs=1)
TOPZ = 0.85 + TH
rbox('tower_cap', (TW + 1.2, TW + 1.2, 1.4), (TX, TY, TOPZ + 0.7), WHITE, rot=(0, 0, rot_u), r=0.3, segs=4)
box('tower_cap_strip', (TW + 1.22, TW + 1.22, 0.08), (TX, TY, TOPZ + 0.3), CYAN, rot=(0, 0, rot_u), bevel=0)
text('decal_tower', 'ST-01', tuple(Vector((TX, TY, TOPZ + 0.85)) + inward * (TW / 2 + 0.61)), (math.pi / 2, 0, rot_u + math.pi / 2), 0.8, INK, extrude=0.01)
rod('tower_mast', (TX, TY, TOPZ + 1.4), (TX, TY, TOPZ + 6.0), 0.12, SATIN, segs=10)
sphere('tower_beacon', 0.3, (TX, TY, TOPZ + 6.1), AMBERG, sub=2)
for s in (-1, 1):
    rbox('tower_flood', (0.8, 0.5, 0.5), tuple(Vector((TX, TY, TOPZ - 0.4)) + inward * (TW / 2 + 0.4) + tang * 1.8 * s), GRAPH_S, rot=(-0.0, 0.0, rot_u), r=0.08, segs=2)
# access arms: crew (z 31), cargo (z 22), fuel (z 7)
reach = TD - SR - TW / 2 - 0.05
def arm(z, w, h, label, mat=WHITE, tunnel=False):
    a0 = Vector((TX, TY, z)) + inward * (TW / 2 - 0.2); a1 = Vector((TX, TY, z)) + inward * (TD - SR - 0.15)
    beam('arm_' + label, a0, a1, w, h, mat, bevel=0.2)
    beam('arm_strip', a0 + Vector((0, 0, -h / 2 - 0.01)) + inward * 0.5, a1 + Vector((0, 0, -h / 2 - 0.01)) - inward * 0.4, 0.2, 0.02, CYAN, bevel=0)
    for s in (-1, 1):
        beam('arm_truss', a0 + Vector((0, 0, -h / 2)) + tang * (w / 2) * s, a0 + inward * 2.6 + Vector((0, 0, -h / 2 - 2.2)) * 0 + Vector((0, 0, -h / 2)) + tang * (w / 2) * s, 0.15, 0.15, GRAPH_S) if False else None
    q = a0.lerp(a1, 0.35)
    beam('arm_kneebrace', Vector((TX, TY, z - 4.0)) + inward * (TW / 2), q + Vector((0, 0, -h / 2)), 0.35, 0.35, GRAPH_S, bevel=0.05)
    return a0, a1
c0, c1 = arm(28.0, 2.4, 2.6, 'crew', tunnel=True)
rbox('crew_seal', (1.0, 3.0, 3.0), tuple(c1), GRAPH_S, rot=(0, 0, rot_u), r=0.3, segs=3)
for k in range(3):
    p = c0.lerp(c1, 0.25 + k * 0.25) + tang * 1.21
    rbox('crew_arm_port', (0.9, 0.06, 0.5), tuple(p + Vector((0, 0, 0.3))), GLASS, rot=(0, 0, rot_u), r=0.08, segs=2)
text('decal_crew', 'CREW ACCESS', tuple(c0.lerp(c1, 0.5) - tang * 1.21 + Vector((0, 0, 0.6))), (math.pi / 2, 0, rot_u + math.pi), 0.32, INK, extrude=0.004)
g0, g1 = arm(20.0, 1.4, 1.2, 'cargo', mat=WHITE)
for s in (-1, 1): handrail(g0 + tang * 0.65 * s + Vector((0, 0, 0.6)), g1 + tang * 0.65 * s + Vector((0, 0, 0.6)) - inward * 0.4, h=1.0, n=4)
rbox('cargo_hoist', (1.0, 1.2, 1.0), tuple(g1 - inward * 0.6 + Vector((0, 0, -1.0))), GRAPH_S, rot=(0, 0, rot_u), r=0.12, segs=2)
f0, f1 = arm(7.0, 1.2, 1.0, 'fuel', mat=WHITE)
for s, mat in ((-1, LOXB), (1, CH4B)):
    st = f0 + tang * 0.4 * s + Vector((0, 0, -0.6)); en = f1 + tang * 0.4 * s + Vector((0, 0, -0.6))
    cable('fuel_hose', st, en, 0.14, FOIL, sag=0.6, n=24)
    rod('fuel_qd', en - inward * 0.1, en + inward * 0.4, 0.2, mat, segs=16)
# pump skid with white radiators at the tower base (makes heat)
PS = Vector((TX, TY, 0)) - tang * 6.5 - inward * 1.0
rbox('pump_skid', (3.6, 2.4, 1.6), (PS.x, PS.y, 0.85), WHITE, rot=(0, 0, rot_u), r=0.3, segs=4)
rbox('pump_base', (4.0, 2.8, 0.25), (PS.x, PS.y, 0.12), GRAPH, rot=(0, 0, rot_u), r=0.05, segs=2)
text('decal_pump', 'FUEL XFER P-2', tuple(PS + inward * 1.23 + Vector((0, 0, 1.0))), (math.pi / 2, 0, rot_u - math.pi / 2), 0.22, INK, extrude=0.003)
for k in (-1, 1):
    c = PS + tang * (k * 1.3) + Vector((0, 0, 4.2))
    rod('rad_post', tuple(PS + tang * k * 1.3 + Vector((0, 0, 1.6))), tuple(c + Vector((0, 0, -1.7))), 0.09, SATIN, segs=10)
    box('pump_radiator', (0.07, 2.6, 3.4), tuple(c), RAD, rot=(0, 0, rot_u + math.pi / 2), bevel=0.01)
    for zz in (-1.72, 1.72):
        rod('rad_manifold', tuple(c + Vector((0, 0, zz)) + inward * 1.3), tuple(c + Vector((0, 0, zz)) - inward * 1.3), 0.06, GRAPH_S, segs=10)
tr0 = PS - inward * 1.6; tr1 = Vector((40.0 * math.cos(UA - 0.18), 40.0 * math.sin(UA - 0.18), 0))
d = (tr1 - tr0); n = int(d.length / 1.2)
for i in range(n):
    p = tr0 + d * ((i + 0.5) / n); hz = berm_h(p.length, B_IN, B_OUT, B_H)
    box('trench_cover', (1.08, 1.5, 0.08), (p.x, p.y, max(hz, 0.0) + 0.03), GRAPH, rot=(0, 0, math.atan2(d.y, d.x)), bevel=0.02)

# ====================================================================== CARGO (raises ship cargo capacity)
CA = math.radians(-100); CX, CY = (PAD_R + 1.6) * math.cos(CA), (PAD_R + 1.6) * math.sin(CA)
rot_c = CA + math.pi / 2
rbox('cargo_pallet', (5.4, 2.6, 0.22), (CX, CY, 0.11), GRAPH, rot=(0, 0, rot_c), r=0.05, segs=2)
tc_ = Vector((math.cos(rot_c), math.sin(rot_c), 0)); nc_ = Vector((-tc_.y, tc_.x, 0))
for i, (dx, h, lab) in enumerate(((-1.7, 1.6, 'CRG-04'), (0.0, 1.6, 'CRG-07'), (1.7, 1.6, 'CRG-11'))):
    p = Vector((CX, CY, 0)) + tc_ * dx
    rbox('cargo_pod', (1.55, 2.2, h), (p.x, p.y, 0.22 + h / 2), WHITE, rot=(0, 0, rot_c), r=0.22, segs=4)
    for zz in (0.55, 1.35):
        rbox('cargo_band', (1.6, 2.25, 0.1), (p.x, p.y, 0.22 + zz), GRAPH, rot=(0, 0, rot_c), r=0.04, segs=2)
    q = p - nc_ * 1.12
    box('cargo_strip', (1.1, 0.02, 0.05), (q.x, q.y, 0.22 + 1.1), CYAN, rot=(0, 0, rot_c), bevel=0)
    text('decal_cargo', lab, (q.x, q.y, 0.22 + 0.95), (math.pi / 2, 0, rot_c), 0.2, INK, extrude=0.004)
LA = math.radians(-70); LX, LY = (PAD_R + 1.8) * math.cos(LA), (PAD_R + 1.8) * math.sin(LA); rl = LA + math.pi / 2
tl_ = Vector((math.cos(rl), math.sin(rl), 0)); nl_ = Vector((-tl_.y, tl_.x, 0))
rbox('lift_base', (3.0, 2.4, 0.3), (LX, LY, 0.15), GRAPH, rot=(0, 0, rl), r=0.06, segs=2)
for s in (-1, 1):
    for side in (-0.9, 0.9):
        rod('lift_scissor', tuple(Vector((LX, LY, 0.3)) + tl_ * 1.2 * s + nl_ * side), tuple(Vector((LX, LY, 1.5)) - tl_ * 1.2 * s + nl_ * side), 0.07, SATIN, segs=10)
rbox('lift_deck', (3.0, 2.4, 0.2), (LX, LY, 1.6), WHITE, rot=(0, 0, rl), r=0.06, segs=2)
box('lift_strip', (3.02, 2.42, 0.04), (LX, LY, 1.52), CYAN, rot=(0, 0, rl), bevel=0)
for side in (-1, 1):
    handrail(Vector((LX, LY, 1.7)) + nl_ * 1.1 * side - tl_ * 1.4, Vector((LX, LY, 1.7)) + nl_ * 1.1 * side + tl_ * 1.4, h=1.0, n=3)

# ====================================================================== CREW / PAD-CONTROL STATION (above ground, on a raised deck)
DH = 2.4                     # deck height
DW, DL = 18.0, 9.0           # deck size (x, y)
for ix in range(4):
    for iy in (-1, 1):
        x = SX - DW / 2 + 1.2 + ix * (DW - 2.4) / 3; y = SY + iy * (DL / 2 - 1.0); g = gz(x, y)
        lathe('st_foot', [(0, 0), (0.8, 0), (0.7, 0.25), (0, 0.3)], (x, y, g - 0.05), GRAPH, segs=24)
        rod('st_leg', (x, y, g + 0.2), (x, y, DH - 0.2), 0.22, WHITE_S, segs=20)
        ring('st_leg_glow', 0.225, (x, y, g + 1.1), 0.06, CYAN, w=0.03, segs=24)
        if ix < 3: rod('st_leg_brace', (x, y, g + 0.4), (x + (DW - 2.4) / 3, y, DH - 0.4), 0.07, SATIN, segs=8)
rbox('st_deck', (DW, DL, 0.4), (SX, SY, DH), GRAPH, r=0.08, segs=2)
box('st_deck_strip', (DW + 0.02, DL + 0.02, 0.06), (SX, SY, DH - 0.12), CYANS, bevel=0)
# perimeter handrail (gap at the front stair)
dz = DH + 0.2
handrail((SX - DW / 2 + 0.2, SY + DL / 2 - 0.2, dz), (SX + DW / 2 - 0.2, SY + DL / 2 - 0.2, dz), n=10)
handrail((SX - DW / 2 + 0.2, SY - DL / 2 + 0.2, dz), (SX - DW / 2 + 0.2, SY + DL / 2 - 0.2, dz), n=5)
handrail((SX + DW / 2 - 0.2, SY - DL / 2 + 0.2, dz), (SX + DW / 2 - 0.2, SY + DL / 2 - 0.2, dz), n=5)
handrail((SX - DW / 2 + 0.2, SY - DL / 2 + 0.2, dz), (SX + 1.0, SY - DL / 2 + 0.2, dz), n=6)
handrail((SX + 6.6, SY - DL / 2 + 0.2, dz), (SX + DW / 2 - 0.2, SY - DL / 2 + 0.2, dz), n=2)
# 2 thick white shielded hab modules (horizontal) on saddles, joined by a node
MR, ML, MZ = 2.1, 7.0, DH + 0.2 + 2.3
for i, mx in enumerate((SX - 4.6, SX + 4.6)):
    cyl('st_module', MR, ML, (mx, SY + 0.6, MZ), WHITE, rot=(0, math.pi / 2, 0), segs=64, bevel=0.06)
    for ex in (-1, 1):
        cyl('st_endcap', MR + 0.12, 0.35, (mx + ex * (ML / 2 - 0.1), SY + 0.6, MZ), GRAPH, rot=(0, math.pi / 2, 0), segs=64, bevel=0.06)
    for xx in (-2.2, 0.0, 2.2):
        ring_x = mx + xx
        cyl('st_hoop', MR + 0.05, 0.22, (ring_x, SY + 0.6, MZ), GRAPH, rot=(0, math.pi / 2, 0), segs=64, bevel=0.03)
    for xx in (-2.5, 2.5):
        rbox('st_saddle', (0.7, 3.2, 1.0), (mx + xx, SY + 0.6, DH + 0.7), GRAPH_S, r=0.1, segs=2)
    box('st_mod_strip', (ML - 1.0, 0.03, 0.08), (mx, SY + 0.6 - MR - 0.005, MZ - 0.6), CYAN, bevel=0)
    for k in range(3):   # small recessed viewports (no domes)
        px = mx - 2.2 + 1.1 + k * 1.1 - 1.1 + 1.1 * (k > 0) * 0
        px = mx - 1.1 + k * 1.1
        p = (px, SY + 0.6 - MR * math.cos(0.32) - 0.02, MZ + MR * math.sin(0.32))
        rbox('st_port_frame', (0.75, 0.22, 0.55), p, GRAPH_S, rot=(-0.32, 0, 0), r=0.1, segs=2)
        rbox('st_port', (0.55, 0.24, 0.36), (p[0], p[1] - 0.02, p[2]), GLASS, rot=(-0.32, 0, 0), r=0.08, segs=2)
    text('decal_mod', ('HAB-1' if i == 0 else 'OPS-1'), (mx - 2.4, SY + 0.6 - MR * math.cos(-0.28) - 0.03, MZ + MR * math.sin(-0.28)), (math.pi / 2 - 0.28, 0, 0), 0.34, INK, extrude=0.004)
rbox('st_node', (2.4, 3.2, 3.6), (SX, SY + 0.6, MZ), WHITE, r=0.5, segs=4)
rbox('st_node_band', (2.5, 3.3, 0.2), (SX, SY + 0.6, MZ + 1.2), GRAPH, r=0.06, segs=2)
# pad-control cab on top of the node, viewport band facing the pad
rbox('st_cab', (3.6, 3.0, 2.0), (SX, SY + 0.9, MZ + 2.9), WHITE, r=0.4, segs=4)
for k in range(4):
    rbox('st_cab_port', (0.6, 0.2, 0.45), (SX - 1.05 + k * 0.7, SY + 0.9 + 1.5, MZ + 3.05), GLASS, r=0.07, segs=2)
    rbox('st_cab_port_f', (0.7, 0.18, 0.55), (SX - 1.05 + k * 0.7, SY + 0.9 + 1.48, MZ + 3.05), GRAPH_S, r=0.08, segs=2)
for k in range(3):
    rbox('st_cab_port', (0.6, 0.2, 0.45), (SX - 0.7 + k * 0.7, SY + 0.9 - 1.5, MZ + 3.05), GLASS, r=0.07, segs=2)
    rbox('st_cab_port_f', (0.7, 0.18, 0.55), (SX - 0.7 + k * 0.7, SY + 0.9 - 1.48, MZ + 3.05), GRAPH_S, r=0.08, segs=2)
box('st_cab_strip', (3.62, 3.02, 0.06), (SX, SY + 0.9, MZ + 2.15), CYAN, bevel=0)
text('decal_cab', 'PAD CONTROL · PC-01', (SX, SY + 0.9 - 1.51, MZ + 3.6), (math.pi / 2, 0, 0), 0.2, INK, extrude=0.003)
rod('st_mast', (SX + 1.2, SY + 1.6, MZ + 3.9), (SX + 1.2, SY + 1.6, MZ + 7.4), 0.08, SATIN, segs=10)
sphere('st_mast_tip', 0.12, (SX + 1.2, SY + 1.6, MZ + 7.45), CYAN, sub=2)
lathe('st_dish', [(0, 0), (0.8, 0.28), (0.86, 0.31), (0.06, 0.04)], (SX - 1.1, SY + 1.3, MZ + 4.0), WHITE_S, segs=36)
rod('st_dish_post', (SX - 1.1, SY + 1.3, MZ + 3.85), (SX - 1.1, SY + 1.3, MZ + 4.05), 0.08, GRAPH_S)
# radiators on the roof masts of the hab modules (edge to the sun)
for mx in (SX - 4.6, SX + 4.6):
    rod('st_rad_mast', (mx, SY + 0.6, MZ + MR - 0.05), (mx, SY + 0.6, MZ + MR + 1.4), 0.1, SATIN, segs=10)
    box('st_radiator', (6.2, 0.08, 2.6), (mx, SY + 0.6, MZ + MR + 2.75), RAD, bevel=0.01)
    for zz in (-1.32, 1.32): rod('st_rad_manifold', (mx - 3.15, SY + 0.6, MZ + MR + 2.75 + zz), (mx + 3.15, SY + 0.6, MZ + MR + 2.75 + zz), 0.06, GRAPH_S, segs=12)
text('decal_rad', 'RAD-P1', (SX - 4.6 - 2.2, SY + 0.6 - 0.05, MZ + MR + 3.8), (math.pi / 2, 0, 0), 0.24, INK, extrude=0.003)
# airlock A1 (front of the OPS module) with suitports + dust-off porch on the deck
AX = SX + 3.8; AYf = SY - DL / 2 + 2.0
rbox('airlock_body', (2.8, 2.8, 2.9), (AX, SY - 1.3, DH + 0.2 + 1.45), WHITE, r=0.4, segs=4)
rbox('airlock_band', (2.9, 2.9, 0.18), (AX, SY - 1.3, DH + 0.2 + 2.4), GRAPH, r=0.05, segs=2)
FY = SY - 1.3 - 1.41
rbox('hatch_frame', (1.6, 0.14, 2.25), (AX, FY - 0.04, DH + 0.2 + 1.2), GRAPH_S, r=0.3, segs=5)
rbox('hatch_door', (1.3, 0.1, 1.95), (AX, FY - 0.1, DH + 0.2 + 1.2), WHITE_S, r=0.26, segs=5)
HZ = DH + 0.2 + 1.05
cyl('hatch_port', 0.17, 0.04, (AX, FY - 0.16, HZ + 0.65), GLASS, rot=(math.pi / 2, 0, 0), segs=24)
cyl('hatch_port_rim', 0.21, 0.03, (AX, FY - 0.15, HZ + 0.65), GRAPH_S, rot=(math.pi / 2, 0, 0), segs=24)
whl = [(AX + 0.26 * math.cos(TAU * k / 24), FY - 0.24, HZ + 0.26 * math.sin(TAU * k / 24)) for k in range(25)]
curve_tube('hatch_wheel', whl, 0.022, SATIN, res=2)
cyl('hatch_wheel_hub', 0.06, 0.12, (AX, FY - 0.2, HZ), SATIN, rot=(math.pi / 2, 0, 0), segs=16)
for k in range(3):
    a = TAU * k / 3
    rod('hatch_spoke', (AX, FY - 0.24, HZ), (AX + 0.26 * math.cos(a), FY - 0.24, HZ + 0.26 * math.sin(a)), 0.014, SATIN, segs=6)
sphere('hatch_lamp', 0.06, (AX + 0.95, FY - 0.08, DH + 2.6), CYAN, sub=2)
for s in (-1, 1):
    x = AX + s * 1.1
    rod('grab_rail', (x, FY - 0.24, DH + 0.7), (x, FY - 0.24, DH + 2.3), 0.028, SATIN, segs=10)
    for zz in (DH + 0.75, DH + 2.25): rod('grab_standoff', (x, FY, zz), (x, FY - 0.25, zz), 0.022, SATIN, segs=8)
text('decal_airlock', 'AIRLOCK A1', (AX, FY - 0.03, DH + 2.75), (math.pi / 2, 0, 0), 0.18, INK, extrude=0.003)
# suitports on the airlock's side wall (2 rear-entry ports)
for k, zz in enumerate((DH + 1.55, DH + 1.55)):
    y = SY - 1.3 - 0.6 + k * 1.2; x = AX + 1.41
    cyl('suitport_ring', 0.42, 0.14, (x + 0.05, y, zz), GRAPH_S, rot=(0, math.pi / 2, 0), segs=32)
    cyl('suitport_hatch', 0.34, 0.1, (x + 0.1, y, zz), WHITE_S, rot=(0, math.pi / 2, 0), segs=32)
    sphere('suitport_lamp', 0.04, (x + 0.12, y, zz + 0.52), CYAN, sub=1)
text('decal_suitport', 'SUITPORT', (AX + 1.42, SY - 1.3, DH + 2.35), (math.pi / 2, 0, math.pi / 2), 0.15, INK, extrude=0.003)
# dust-off porch: grate, air-knife arch, boot brushes
PZ = DH + 0.2
for i in range(12): box('porch_grate', (2.8, 0.05, 0.03), (AX, FY - 0.25 - i * 0.12, PZ + 0.015), SATIN, bevel=0)
AYa = FY - 0.9
for s in (-1, 1):
    rbox('arch_post', (0.3, 0.45, 2.7), (AX + s * 1.5, AYa, PZ + 1.35), WHITE, r=0.1, segs=3)
    box('arch_post_strip', (0.02, 0.32, 2.0), (AX + s * 1.34, AYa, PZ + 1.2), CYANS, bevel=0)
    for zz in (0.5, 1.0, 1.5, 2.0): cyl('air_knife_nozzle', 0.04, 0.08, (AX + s * 1.32, AYa - 0.1, PZ + zz), GRAPH_S, rot=(0, math.pi / 2, 0), segs=10)
    rbox('boot_brush', (0.45, 0.7, 0.2), (AX + s * 0.8, AYa - 0.1, PZ + 0.1), RUBBER, r=0.05, segs=2)
rbox('arch_top', (3.3, 0.45, 0.34), (AX, AYa, PZ + 2.85), WHITE, r=0.12, segs=3)
box('arch_strip', (2.8, 0.28, 0.02), (AX, AYa, PZ + 2.67), CYAN, bevel=0)
text('decal_arch', 'DUST-OFF', (AX, AYa - 0.23, PZ + 2.85), (math.pi / 2, 0, 0), 0.18, INK, extrude=0.003)
# main stair: deck front edge -> ground, with handrails
s0 = Vector((SX + 3.8, SY - DL / 2, DH + 0.2)); s1 = Vector((SX + 3.8, SY - DL / 2 - 4.2, gz(SX + 3.8, SY - DL / 2 - 4.2) + 0.05))
beam('st_stair', s0 + Vector((0, 0, -0.15)), s1 + Vector((0, 0, 0.05)), 2.2, 0.25, GRAPH_S, bevel=0.03, up=Vector((1, 0, 0)))
for k in range(13):
    p = s0.lerp(s1, (k + 0.5) / 13); box('st_tread', (2.0, 0.28, 0.05), (p.x, p.y, p.z + 0.02), SATIN, bevel=0)
for s in (-1, 1):
    handrail(s0 + Vector((s * 1.05, 0, 0)), s1 + Vector((s * 1.05, 0, 0)), h=1.0, n=4)
rbox('st_stair_pad', (3.0, 1.6, 0.12), (s1.x, s1.y - 0.7, s1.z), GRAPH, r=0.03, segs=1)
# power junction (cable from the fission plant + solar lands here) + cable trench to the pad
JX, JY = SX - DW / 2 - 2.0, SY - 1.5
rbox('pwr_junction', (1.4, 0.9, 1.7), (JX, JY, gz(JX, JY) + 0.85), WHITE, r=0.14, segs=3)
box('pwr_junction_strip', (1.0, 0.02, 0.06), (JX, JY - 0.46, gz(JX, JY) + 1.45), CYAN, bevel=0)
text('decal_pwr', 'PWR-01', (JX, JY - 0.46, gz(JX, JY) + 1.15), (math.pi / 2, 0, 0), 0.16, INK, extrude=0.003)
cable('jx_feed', (JX + 0.7, JY, 1.0), (SX - DW / 2 + 0.5, SY, DH - 0.3), 0.07, GRAPH_S, sag=0.4)
p0 = Vector((SX + DW / 2 + 0.5, SY + 1.0, 0)); pa = (PAD_R + 2.5); p1 = Vector((pa * math.cos(GAP_C), pa * math.sin(GAP_C), 0))
d = p1 - p0; n = int(d.length / 1.05)
for i in range(n):
    p = p0 + d * ((i + 0.5) / n)
    box('cable_cover', (0.96, 0.6, 0.06), (p.x, p.y, gz(p.x, p.y) + 0.03), GRAPH, rot=(0, 0, math.atan2(d.y, d.x)), bevel=0.015)

# ====================================================================== POWER: solar masts + distant fission plant behind a berm
SUN = Vector((-0.55, -0.6, 0.58)).normalized()
from mathutils import Euler
def _cell():
    m = bpy.data.materials.new('LP_SolarCell'); nt, b = _nodes(m)
    b.inputs['Base Color'].default_value = hexc('#152a4a'); b.inputs['Metallic'].default_value = 0.4; b.inputs['Roughness'].default_value = 0.18
    b.inputs['Coat Weight'].default_value = 0.8; m.diffuse_color = hexc('#152a4a'); return m
M_cell = _cell()
def solar_mast(x, y, h=16.0, tag='SOL-1'):
    g = gz(x, y)
    lathe('sol_foot', [(0, 0), (1.2, 0), (1.0, 0.35), (0, 0.4)], (x, y, g - 0.05), GRAPH, segs=32)
    rod('sol_mast', (x, y, g + 0.3), (x, y, g + h), 0.22, WHITE_S, r2=0.14, segs=20)
    ring('sol_glow', 0.21, (x, y, g + 1.8), 0.06, CYAN, w=0.03, segs=24)
    rbox('sol_gimbal', (0.6, 0.6, 0.6), (x, y, g + h), GRAPH_S, r=0.1, segs=2)
    rot = facing(SUN); M = rot.to_matrix(); c = Vector((x, y, g + h + 0.45))
    box('sol_panel', (7.0, 4.4, 0.1), tuple(c), GRAPH_S, rot=tuple(rot), bevel=0.01)
    for i in range(5):
        for j in range(3):
            off = M @ Vector((-2.8 + i * 1.4, -1.45 + j * 1.45, 0.06))
            box('sol_cell', (1.3, 1.35, 0.02), tuple(c + off), M_cell, rot=tuple(rot), bevel=0)
    text('decal_sol', tag, (x, y - 0.23, g + 2.6), (math.pi / 2, 0, 0), 0.2, INK, extrude=0.003)
    rbox('sol_box', (0.7, 0.45, 0.9), (x, y - 0.45, g + 0.8), WHITE, r=0.08, segs=2)
SOL = [(-54.0, -20.0, 17.0, 'SOL-1'), (-50.0, -3.0, 15.0, 'SOL-2')]
for x, y, h, t in SOL: solar_mast(x, y, h, t)
# fission plant (Stage) - far behind its own berm, radiators poking over
mound('reactor_berm', RXr + 8.0, RYr - 9.0, 11.0, 1.4, 5.2, 5.0, REGO, c='Stage', seed=31)
lathe('reactor_vessel', [(0, 0), (3.0, 0), (3.0, 5.4), (2.3, 6.3), (0, 6.5)], (RXr, RYr, gz(RXr, RYr) - 0.1), WHITE, segs=48, c='Stage')
ring('reactor_band', 3.02, (RXr, RYr, 4.0), 0.24, GRAPH, w=0.06, segs=48, c='Stage')
ring('reactor_glow', 3.02, (RXr, RYr, 4.7), 0.1, CYAN, w=0.03, segs=48, c='Stage')
for s in (-1, 1):
    box('reactor_radiator', (10.0, 0.1, 7.0), (RXr + s * 8.5, RYr + 0.5, 6.0), RAD, rot=(0, 0, s * 0.15), bevel=0.01, c='Stage')
    rod('reactor_rad_boom', (RXr + s * 2.8, RYr + 0.5, 6.0), (RXr + s * 13.5, RYr + 0.5 + s * 1.6, 6.0), 0.14, GRAPH_S, c='Stage')
    for xx in (4.5, 12.5): rod('reactor_rad_leg', (RXr + s * xx, RYr + 0.5 + s * 0.15 * (xx - 2.8), -0.1), (RXr + s * xx, RYr + 0.5 + s * 0.15 * (xx - 2.8), 2.5), 0.12, GRAPH_S, c='Stage')
sphere('reactor_beacon', 0.35, (RXr, RYr, 6.8), AMBERG, sub=2, c='Stage')
# cable run on low stanchions: fission plant -> PWR-01
route = [Vector((RXr + 4.0, RYr - 4.0, 0)), Vector((RXr + 20.0, RYr - 14.0, 0)), Vector((-58.0, 12.0, 0)), Vector((-52.0, -10.0, 0)), Vector((JX - 0.8, JY, 0))]
posts = []
for a, b in zip(route, route[1:]):
    L = (b - a).length; n = max(1, int(L / 6.0))
    for i in range(n): posts.append(a.lerp(b, i / n))
posts.append(route[-1])
for p in posts:
    cc = 'Stage' if p.y > 0 else 'Mine'; g = gz(p.x, p.y)
    rod('cable_post', (p.x, p.y, g - 0.05), (p.x, p.y, g + 0.9), 0.05, GRAPH_S, segs=8, c=cc)
    box('cable_saddle', (0.24, 0.24, 0.08), (p.x, p.y, g + 0.9), SATIN, bevel=0.01, c=cc)
for a, b in zip(posts, posts[1:]):
    cc = 'Stage' if a.y > 0 else 'Mine'
    cable('power_cable', (a.x, a.y, gz(a.x, a.y) + 0.95), (b.x, b.y, gz(b.x, b.y) + 0.95), 0.05, RUBBER, sag=0.3, n=10, c=cc)
cable('sol_feed1', (-54.0, -20.45, gz(-54, -20) + 0.5), (JX - 0.7, JY - 0.3, gz(JX, JY) + 0.4), 0.04, RUBBER, sag=0.2)
cable('sol_feed2', (-50.0, -3.45, gz(-50, -3) + 0.5), (-52.0, -10.0, gz(-52, -10) + 0.9), 0.04, RUBBER, sag=0.3)

# ====================================================================== STAGE cleanup + lights + crew
EXCL = [((0, 0), 40.0), ((SX, SY), 16.0), ((SX + 3.8, SY - 9), 5.0)] + [((x, y), 3.5) for x, y, _, _ in SOL] + [((RXr, RYr), 18.0)]
for ob in list(coll('Stage').objects):
    if ob.name.split('.')[0] in ('boulder', 'pebble', 'slope_boulder'):
        x, y = ob.matrix_world.translation.x, ob.matrix_world.translation.y
        if any(math.hypot(x - cx, y - cy) < r for (cx, cy), r in EXCL): bpy.data.objects.remove(ob); continue
        for a, b in zip(posts, posts[1:]):
            ab = b - a; t = max(0, min(1, (Vector((x, y, 0)) - a).dot(ab) / max(1e-6, ab.length_squared)))
            if (a + ab * t - Vector((x, y, 0))).length < 2.0: bpy.data.objects.remove(ob); break
for k in range(60):
    a = rr.uniform(0, TAU); dd = rr.uniform(PAD_R + 3.4, B_IN - 0.4); s = rr.uniform(0.05, 0.16)
    if abs(((a - GAP_C + math.pi) % TAU) - math.pi) < GAP_W + 0.1: continue
    sphere('ejecta_pebble', s, (dd * math.cos(a), dd * math.sin(a), 0.0), REGO, scale=(1.2, 1, 0.6), sub=1, jitter=0.4, smooth=False, seed=k, c='Stage')
world_and_sun((-0.55, -0.6, 0.58), 5.5)
astronaut((AX + 0.2, AYa - 0.05, PZ), rot_z=-0.3)                        # in the dust-off arch
astronaut((CX + 2.6, CY - 1.6, 0.0), rot_z=0.5)                         # pad edge, beside the cargo pods
astronaut((s1.x + 1.8, s1.y - 1.2, s1.z - 0.05), rot_z=-0.8)             # foot of the station stair
astronaut(tuple(g0.lerp(g1, 0.55) + Vector((0, 0, 0.6))), rot_z=rot_u)    # on the cargo access arm (20 m up)
cam = setup_render(64 if not QUICK else 16)

ONLY = A.get('only', 'hero')
if 'glb' in ONLY: export_glb(os.path.join(OUT, f'{NAME}_master.glb'))
if 'blend' in ONLY:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'{NAME}_master.blend'), compress=True)
assert not ('game' in ONLY and set(ONLY) & {'hero', 'turn', 'close'}), 'game step is destructive: run it without render modes'
if 'game' in ONLY:   # game-ready GLB per Game Coder rules: SH_* shared palette, merge by material, <=30k tris, no textures,
    # no Draco (meshopt + quantization via gltfpack -cc afterwards, see _src/pack_game_glb.sh); ship + astronauts live in Stage -> excluded
    import json
    SHJ = os.path.normpath(os.path.join(HERE, '..', '..', '_shared', 'shared_materials.json'))
    pal = json.load(open(SHJ))['materials']
    def sh_mat(n):
        if n in bpy.data.materials: return bpy.data.materials[n]
        d = pal[n]; m = bpy.data.materials.new(n); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = hexc(d['base']); b.inputs['Metallic'].default_value = d['metal']; b.inputs['Roughness'].default_value = d['rough']
        if 'emissive' in d: b.inputs['Emission Color'].default_value = hexc(d['emissive']); b.inputs['Emission Strength'].default_value = d['emissive_strength']
        return m
    RULES = [('cyan', 'SH_GlowCyan'), ('glow', 'SH_GlowCyan'), ('lamp', 'SH_GlowWhite'), ('amber', 'SH_GlowRed'), ('glass', 'SH_Glass'), ('lens', 'SH_Glass'),
             ('solar', 'SH_Solar'), ('pv', 'SH_Solar'), ('rad', 'SH_Radiator'), ('foil', 'SH_Foil'), ('mli', 'SH_Foil'), ('lox', 'SH_PipeH2O'), ('ch4', 'SH_Red'),
             ('sinter', 'SH_Rock'), ('rego', 'SH_Rock'), ('block', 'SH_Rock'), ('rock', 'SH_Rock'), ('ground', 'SH_Rock'), ('satin', 'SH_Steel'),
             ('steel', 'SH_Steel'), ('graph', 'SH_Graphite'), ('rubber', 'SH_Graphite'), ('ink', 'SH_Graphite'), ('white', 'SH_White'), ('paint', 'SH_White')]
    def remap(m):
        n = (m.name if m else '').lower()
        for k, v in RULES:
            if k in n: return v
        print('UNMAPPED', m.name if m else None); return 'SH_White'
    keep = [o for o in coll('Mine').all_objects if o.type in ('MESH', 'CURVE', 'FONT') and not o.name.split('.')[0].startswith(('decal_', 'stencil_'))
            and 'astro' not in o.name.lower()]
    for o in list(coll('Mine').all_objects):
        if o not in keep: bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in keep: o.select_set(True)
    bpy.context.view_layer.objects.active = keep[0]
    bpy.ops.object.convert(target='MESH')
    sel = [o for o in bpy.context.selected_objects if o.type == 'MESH']
    for o in sel:
        o.data = o.data.copy()
        for sl in o.material_slots: sl.material = sh_mat(remap(sl.material))
    bpy.ops.object.join(); G = bpy.context.active_object; G.name = 'launch_pad_game'
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.001); bpy.ops.object.mode_set(mode='OBJECT')
    import collections as _c
    print('SLOTS', len(G.material_slots), _c.Counter(p.material_index for p in G.data.polygons).most_common(8), flush=True)
    # merge duplicate SH slots (same material in several slots)
    names = [sl.material.name for sl in G.material_slots]; uniq = sorted(set(names), key=names.index)
    idx = [uniq.index(n) for n in names]
    pidx = [idx[p.material_index] for p in G.data.polygons]
    G.data.materials.clear()
    for n in uniq: G.data.materials.append(bpy.data.materials[n])
    for p, i in zip(G.data.polygons, pidx): p.material_index = i
    print('MERGED', uniq, _c.Counter(p.material_index for p in G.data.polygons), flush=True)
    tri = lambda: sum(len(p.vertices) - 2 for p in G.data.polygons)
    T0 = tri(); TGT = int(A.get('tris', 28000))
    for it in range(6):
        t = tri()
        if t <= TGT: break
        md = G.modifiers.new('Dec', 'DECIMATE'); md.ratio = max(0.02, TGT / t * 0.97); md.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=md.name)
    print('GAMETRIS', T0, '->', tri(), 'MATS', len(G.data.materials), flush=True)
    bpy.ops.object.select_all(action='DESELECT'); G.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{NAME}_game_raw.glb'), export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                              export_animations=False, export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False,
                              export_materials='EXPORT', export_image_format='NONE', export_texcoords=False)
    print('GAMEGLB', flush=True)
HC = A.get('hc')
if 'hero' in ONLY:
    w, h = (3840, 2160) if not QUICK else (960, 540)
    tgt = (-12.0, -6.0, 15.0); pos = (8.0, -108.0, 20.0)
    if HC: v = [float(t) for t in HC.split(',')]; pos, tgt = tuple(v[:3]), tuple(v[3:6])
    shoot(cam, os.path.join(OUT, 'hero.png'), tgt, pos, w, h, lens=float(A.get('lens', 28)), samples=int(A.get('hs', 64)) if not QUICK else 16)
if 'turn' in ONLY:
    os.makedirs(os.path.join(OUT, 'turntable'), exist_ok=True)
    turntable(cam, os.path.join(OUT, 'turntable'), (-10.0, -8.0, 14.0), 150, 22, size=1000 if not QUICK else 400, samples=int(A.get('ts', 48)) if not QUICK else 12)
if 'close' in ONLY:
    for nm, pos, tgt in (('close_station', (SX + 16.0, SY - 26.0, 8.0), (SX + 1.0, SY - 2.0, 4.0)),
                         ('close_tower', (31.0, -26.0, 26.0), (5.4, 4.5, 22.0)),
                         ('close_airlock', (AX + 5.0, FY - 9.0, PZ + 2.5), (AX, FY - 0.6, PZ + 1.3))):
        shoot(cam, os.path.join(OUT, nm + '.png'), tgt, pos, 960, 540, lens=35, samples=16)
