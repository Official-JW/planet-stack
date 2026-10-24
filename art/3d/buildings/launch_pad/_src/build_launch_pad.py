"""Planet Stack - LAUNCH PAD Lv0 (PAD-01), concept master + game GLB (Blender 4.2 LTS, headless, Cycles).

blender -b -P build_launch_pad.py -- --out .. [--quick 1] [--only blend,glb,check | game | portrait | hero,turn]
       [--pw 1179 --ph 2556] [--tiers 1] [--hs 64] [--ts 48] [--hc x,y,z,tx,ty,tz] [--lens 28]

Lv0 = NO launch tower (the tower is Lv1). Blender coords: Z up, metres, front = -Y (toward the game camera).
Exported GLB: Y up, front +Z, origin = pad centre on the ground (glTF = (x, z, -y)).
Style: Mine concept B (glossy white + graphite, cyan light strips, weathered + dusty). Shared helpers + shared M_ground from
art/3d/mine_concepts/_src/mc_common.py by import (NOT modified). Fuel = LOX + LCH4 (liquid methane) only.
Systems (collection 'Mine' = exported building; 'Stage' = renders only):
  * sintered landing pad r 14 m (glassy fused regolith, scorched centre, landing target, PAD-01 stencils) + sintered service apron to r 21 m
  * blast berm r 22-29 m, 3.4 m high, precast sintered retaining blocks, 44 deg road gap at the front-left (graded road R-1:
    crew, crates, haul truck)
  * stand-alone white frosted cryo tanks on the apron: LOX (green bands) and LCH4 · LIQUID METHANE (red-orange bands)
  * flexible fuel hoses Hose_LOX / Hose_LCH4 on hose stands from the tank fill valves to the ship's tail fuel ports (Fuel_Hookup)
  * the pad end of the BURIED Pipe_LaunchPad line from the Dock (Dock is at +X in the game, 160 m away): buried-line marker
    posts over the berm on the +X side, the line surfaces at valve vault VV-1 / manifold (Pipe_LaunchPad_End) feeding both tanks
  * power: solar mast SOL-1 behind the berm + distant fission plant behind its own berm (Stage)
  * gray 40 m placeholder ship + 1.8 m astronauts: Stage only (never in the game GLB)
Tiers (extras {tier, hidden_by_default}): Tier_03 cargo pallet + lift, Tier_05 solar mast SOL-2, Tier_08 fuel-transfer pump skid P-2
(re-purposed: was at the tower base), Tier_12 pad edge lights, Tier_20 landing radar / comms mast LR-1 (re-purposed: was the
control-station roof kit). Dropped with the tower: Arm_Crew / Arm_Cargo / Arm_Fuel and their clips.
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
# ---- game-GLB node / marker names: ONE mapping - rename here only
GAME_NAMES = {
    'base': 'Pad_Base',
    'hoses': {'Hose_LOX': ('Hose_LOX', 'LOX'), 'Hose_LCH4': ('Hose_LCH4', 'LCH4')},
    'tiers': {'Tier_03': ('Tier_03', 3), 'Tier_05': ('Tier_05', 5), 'Tier_08': ('Tier_08', 8), 'Tier_12': ('Tier_12', 12), 'Tier_20': ('Tier_20', 20)},
    'markers': {'Ship_Center': 'Ship_Center', 'Road_Entry': 'Road_Entry', 'Ramp_Foot': 'Ramp_Foot', 'Crate_Drop': 'Crate_Drop',
                'Fuel_Hookup': 'Fuel_Hookup', 'Pipe_LaunchPad_End': 'Pipe_LaunchPad_End', 'Cam_Target': 'Cam_Target'},
    'crew_path': 'Crew_Path_%02d',
    # in-game phone camera (Game Coder spec): perspective, VERTICAL FOV 38 deg, pitched down 18 deg, no azimuth (camera on -Y looking +Y,
    # glTF looks down -Z), lookAt(Cam_Target); d = (frame_w/2) / (tan19 * aspect). Game Coder safe bands: 393x852 x 12-381, y 144-568
    # (sheet top 602); 375x667 x 12-363, y 144-383 (sheet top 417). 'target' in Blender coords.
    'phone_cam': {'target': (0.0, -12.0, 0.0), 'pitch': 18.0, 'fov_y': 38.0, 'frame_w': 64.0},
}
SAFE = {(393, 852): (12, 381, 144, 568), (375, 667): (12, 363, 144, 383)}
_pc = A.get('pcam')   # --pcam x,y,z,W : framing override while tuning
if _pc:
    v = [float(t) for t in _pc.split(',')]; GAME_NAMES['phone_cam']['target'] = tuple(v[:3]); GAME_NAMES['phone_cam']['frame_w'] = v[3]

# ====================================================================== materials
def add_dust(m, top=1.2, amt=0.8, col='#8a8d91', upamt=0.3):
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

WHITE   = P_('LP_White', '#eceff2', rough=0.22, metal=0.0, coat=0.8, grime=0.22, grime_col='#9ea2a7', wear=0.12, wear_col='#9aa3ad', panel=0.8, bevel=0.03, dirt_scale=1.4)
WHITE_S = P_('LP_WhiteSmooth', '#eef1f4', rough=0.2, metal=0.0, coat=0.9, grime=0.16, grime_col='#9ea2a7', wear=0.1, wear_col='#9aa3ad', bevel=0.03)
RAD     = P_('LP_Radiator', '#f2f4f7', rough=0.3, metal=0.0, coat=0.4, grime=0.14, grime_col='#9ea2a7', panel=4.0, bevel=0.01)
GRAPH   = P_('LP_Graphite', '#2c3137', rough=0.3, metal=0.55, coat=0.5, grime=0.16, grime_col='#63676c', wear=0.2, wear_col='#9aa0a6', panel=1.4, bevel=0.02)
GRAPH_S = P_('LP_GraphiteSmooth', '#30353c', rough=0.28, metal=0.6, coat=0.5, grime=0.16, grime_col='#63676c', wear=0.18, wear_col='#9aa0a6', bevel=0.02)
SATIN   = P_('LP_Satin', '#9aa3ad', rough=0.25, metal=1.0, grime=0.2, grime_col='#55595e', wear=0.1, wear_col='#d0d5db', bevel=0.01)
RUBBER  = P_('LP_Rubber', '#1d2024', rough=0.8, metal=0.0, grime=0.3, grime_col='#676b70', bump_noise=0.3)
FOIL    = P_('LP_MLI', '#c9ced6', rough=0.3, metal=0.9, grime=0.2, grime_col='#565a5f', bump_noise=0.5, bevel=0.01)
PAINT   = P_('LP_PadPaint', '#e9ecef', rough=0.55, metal=0.0, grime=0.45, grime_col='#5a5e62', dirt_scale=0.6, upamt=0.0) if False else None
INK     = M_paint('LP_Ink', '#1f2329', rough=0.5, metal=0.0)
INKW    = M_paint('LP_InkWhite', '#f4f7fa', rough=0.4, metal=0.0)
CYAN    = M_glow('LP_Cyan', '#2fe3ff', 16)
CYANS   = M_glow('LP_CyanSoft', '#2fe3ff', 5)
LAMP    = M_glow('LP_Lamp', '#f2fbff', 25)
AMBERG  = M_glow('LP_AmberLamp', '#ffb020', 14)
GLASS   = M_glass('LP_Lens', '#1b2a36', 0.04)
REGO    = M_rock('LP_Regolith', '#63666a', '#8b8f93')

def M_pad_paint():
    m = bpy.data.materials.new('LP_PadPaint'); nt, b = _nodes(m)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 9
    link(nt, tc.outputs['Object'], nz.inputs['Vector'])
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].position = 0.42; rp.color_ramp.elements[1].position = 0.62
    rp.color_ramp.elements[0].color = hexc('#979a9e'); rp.color_ramp.elements[1].color = hexc('#e6e8ea')
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
    link(nt, m2.outputs[2], m3.inputs[6]); m3.inputs[7].default_value = hexc('#86898e')
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
BLOCK = P_('LP_SinterBlock', '#5c5b5d', rough=0.5, metal=0.0, grime=0.35, grime_col='#86898e', bump_noise=0.4, bevel=0.03, dirt_scale=1.0)

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



# fuel band colours (render = game swatch): LOX green (SH_PipeO2), LCH4 red-orange (SH_Red)
LOXB  = P_('LP_LoxBand', '#2f9e63', rough=0.3, metal=0.1, coat=0.5, grime=0.15)
LCH4B = P_('LP_LCH4Band', '#c2442c', rough=0.3, metal=0.1, coat=0.5, grime=0.15)
FROST = P_('LP_WhiteFrost', '#f1f4f7', rough=0.38, metal=0.0, coat=0.35, grime=0.18, grime_col='#a3a8ae', wear=0.08, wear_col='#c9d3dc', panel=1.2, bevel=0.02, bump_noise=0.25, dirt_scale=1.0)
HOSE  = P_('LP_HoseFoil', '#b9bfc7', rough=0.42, metal=0.85, grime=0.25, grime_col='#5a5e63', bump_noise=0.6, bevel=0.0)
SHIPG = M_paint('LP_ShipPlaceholder', '#8a8d94', rough=0.8, metal=0.05)
APRON = P_('LP_ApronSinter', '#4e5054', rough=0.6, metal=0.0, grime=0.4, grime_col='#83868a', bump_noise=0.35, bevel=0.0, dirt_scale=0.5)

TC = 'Tiers'   # upgrade tiers: child of 'Mine' (exported hidden_by_default); hidden in Lv0 renders unless --tiers 1
_tc = bpy.data.collections.new(TC); coll('Mine').children.link(_tc)
def grp_begin(): return set(bpy.data.objects.keys())
def grp_end(s0, g):
    for n in set(bpy.data.objects.keys()) - s0:
        o = bpy.data.objects[n]; o['grp'] = g
        if g.startswith('Tier_') and o.users_collection and o.users_collection[0].name == 'Mine':
            coll('Mine').objects.unlink(o); _tc.objects.link(o)

def wrap_text(o, cx, cy, R):
    """convert a FONT object facing -Y (rot x=90) into a mesh wrapped onto the cylinder (cx, cy, R)."""
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target='MESH'); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for v in o.data.vertices:
        dx = v.co.x - cx; dy = v.co.y - cy; rad = R - (dy + R)   # dy ~ -R on the face -> rad ~ R (extrude goes outward)
        rad = -dy; th = dx / R
        v.co.x = cx + rad * math.sin(th); v.co.y = cy - rad * math.cos(th)
    o.data.update(); return o

# ====================================================================== STAGE (shared mc_common stage + shared M_ground, unmodified)
RXr, RYr = -84.0, 70.0           # distant fission plant (Stage)
height = build_stage(keep_flat=((0, 0, 44), (0, 0, 44), (RXr, RYr, 24), (RXr, RYr, 24), (-16, 30, 14)))
def gz(x, y): return height(x, y)
def _ridge(x, y, o):
    return (1 - abs(noise.noise(Vector((x, y, o))))) ** 2
def hill_disp(x, y, z):
    if y < 48 or z < 0.2: return 0.0
    w = min(1.0, z / 3.5) * min(1.0, (y - 48) / 10)
    d = 3.2 * (_ridge(x * 0.028, y * 0.05, 7.3) - 0.3) + 1.6 * noise.noise(Vector((x * 0.07, y * 0.09, 3.1)))
    d += 0.9 * _ridge(x * 0.11, y * 0.16, 9.7) - 0.7 * _ridge(x * 0.19 + 0.3 * y * 0.02, y * 0.045, 12.2)
    return w * d
_g = bpy.data.objects['Ground']
for v in _g.data.vertices: v.co.z += hill_disp(v.co.x, v.co.y, v.co.z)
_g.data.update()   # ground material = the SHARED M_ground() assigned by mc_common.build_stage() (no local variant)
assert _g.data.materials[0].name.startswith('M_Regolith'), 'Ground must use mc_common.M_ground'
for ob in coll('Stage').objects:
    if ob.name.startswith('slope_boulder'):
        t = ob.matrix_world.translation; ob.location.z += hill_disp(t.x, t.y, t.z)
_bm = bpy.data.materials.get('M_Boulder')
if _bm:
    for nd in _bm.node_tree.nodes:
        if nd.type == 'VALTORGB': nd.color_ramp.elements[0].color = hexc('#5c5f63'); nd.color_ramp.elements[1].color = hexc('#85888c')
    _bm.diffuse_color = hexc('#5c5f63')

# ====================================================================== PAD r 14 (40 m ship, legs to r 7) + service apron to r 21
PAD_R = 14.0; TOP = 0.25; S = PAD_R / 10.8; APR = 21.0
lathe('pad_slab', [(0, -0.15), (PAD_R, -0.15), (PAD_R, 0.08), (PAD_R - 0.5, TOP), (0, TOP)], (0, 0, 0), SINTER, segs=160)
lathe('pad_apron', [(PAD_R - 0.2, -0.12), (APR, -0.12), (APR + 0.8, -0.1), (APR + 0.6, 0.02), (APR, 0.08), (PAD_R - 0.2, 0.1)], (0, 0, 0), APRON, segs=160)
Z = TOP + 0.004
for r0, r1 in ((6.3, 6.9), (2.7, 3.05), (8.6, 8.75)):
    annulus('target_ring', r0 * S, r1 * S, Z, PAINT, segs=160)
for k in range(4):
    a = TAU * k / 4 + math.pi / 4
    box('target_bar', (2.6 * S, 0.42 * S, 0.008), (4.75 * S * math.cos(a), 4.75 * S * math.sin(a), Z), PAINT, rot=(0, 0, a), bevel=0)
for k in range(12):
    a = TAU * k / 12
    box('target_tick', (0.9 * S, 0.14 * S, 0.008), (7.6 * S * math.cos(a), 7.6 * S * math.sin(a), Z), PAINT, rot=(0, 0, a), bevel=0)
text('stencil_pad', 'PAD-01', (0, -7.75 * S, Z + 0.002), (0, 0, 0), 1.25 * S, PAINT, extrude=0.002)
text('stencil_pad_b', 'PAD-01', (0, 7.75 * S, Z + 0.002), (0, 0, math.pi), 1.25 * S, PAINT, extrude=0.002)
annulus('pad_strip', PAD_R - 1.2, PAD_R - 1.0, TOP + 0.005, CYAN, segs=192)
for k in range(64):
    a = TAU * (k + 0.5) / 64
    box('rim_tile', (0.62, 1.3, 0.14), ((PAD_R + 0.05) * math.cos(a), (PAD_R + 0.05) * math.sin(a), 0.06), GRAPH, rot=(0, 0, a), bevel=0.03)
for k in range(4):
    a = TAU * k / 4
    box('flame_grate', (4.2, 1.3, 0.04), (4.4 * math.cos(a), 4.4 * math.sin(a), TOP + 0.01), GRAPH_S, rot=(0, 0, a), bevel=0.01)
# apron joint lines (sintered slabs)
for k in range(24):
    a = TAU * k / 24
    box('apron_joint', (APR - PAD_R - 0.6, 0.05, 0.01), ((PAD_R + APR) / 2 * math.cos(a), (PAD_R + APR) / 2 * math.sin(a), 0.105), GRAPH_S, rot=(0, 0, a), bevel=0)
annulus('apron_joint_r', 17.45, 17.5, 0.105, GRAPH_S, segs=160)
_g12 = grp_begin()
for k in range(32):
    a = TAU * k / 32; x, y = (PAD_R - 0.6) * math.cos(a), (PAD_R - 0.6) * math.sin(a)
    rbox('edge_light', (0.4, 0.7, 0.12), (x, y, TOP + 0.04), GRAPH_S, rot=(0, 0, a), r=0.04, segs=2)
    box('edge_lens', (0.24, 0.5, 0.02), (x, y, TOP + 0.105), LAMP if k % 4 else AMBERG, rot=(0, 0, a), bevel=0)
grp_end(_g12, 'Tier_12')

# ====================================================================== BLAST BERM r 22-29 with a road gap (front-left)
B_IN, B_OUT, B_H = 22.0, 29.0, 3.4
GAP_C, GAP_W = math.radians(-112), math.radians(22)
BA0, BA1 = GAP_C + GAP_W, GAP_C - GAP_W + TAU
berm('blast_berm', 0, 0, B_IN, B_OUT, B_H, BA0, BA1, REGO, seed=9, nseg=260, nrad=18, taper=0.28)
nblk = 96
for k in range(nblk + 1):
    a = BA0 + 0.2 + (BA1 - BA0 - 0.4) * k / nblk
    hgt = 2.5 + rr.uniform(-0.1, 0.1); r = B_IN + 0.3
    x, y = r * math.cos(a), r * math.sin(a)
    box('berm_block', (0.85, 1.48, hgt), (x, y, hgt / 2 - 0.05), BLOCK, rot=(rr.uniform(-0.03, 0.03), -0.12, a), bevel=0.05)
    if k % 2 == 0: box('berm_cap', (0.95, 1.46, 0.14), (x + 0.07 * math.cos(a), y + 0.07 * math.sin(a), hgt + 0.02), GRAPH, rot=(0, -0.12, a), bevel=0.03)
for a in (BA0 + 0.2, BA1 - 0.2):
    x, y = (B_IN + 0.3) * math.cos(a), (B_IN + 0.3) * math.sin(a)
    rbox('berm_endpost', (1.1, 1.1, 3.4), (x, y, 1.7), WHITE, rot=(0, 0, a), r=0.2, segs=3)
    box('berm_endstrip', (1.12, 1.12, 0.1), (x, y, 2.8), CYAN, rot=(0, 0, a), bevel=0)
    sphere('berm_beacon', 0.16, (x, y, 3.55), AMBERG, sub=2)

# ====================================================================== GRADED ACCESS ROAD R-1 through the gap (crew, crates, haul truck)
ROAD_A, ROAD_R0, ROAD_R1, ROAD_W = GAP_C, APR - 0.4, 33.0, 7.0
ROAD_U = Vector((math.cos(ROAD_A), math.sin(ROAD_A), 0)); ROAD_N = Vector((-ROAD_U.y, ROAD_U.x, 0))
def M_road():
    m = bpy.data.materials.new('LP_RoadGraded'); nt, b = _nodes(m)
    uv = nt.nodes.new('ShaderNodeUVMap'); tc = nt.nodes.new('ShaderNodeTexCoord')
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); link(nt, uv.outputs['UV'], sx.inputs['Vector'])
    ab = nt.nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; link(nt, sx.outputs['X'], ab.inputs[0])
    tr = nt.nodes.new('ShaderNodeMath'); tr.operation = 'SUBTRACT'; tr.inputs[1].default_value = 1.35; link(nt, ab.outputs[0], tr.inputs[0])
    ta = nt.nodes.new('ShaderNodeMath'); ta.operation = 'ABSOLUTE'; link(nt, tr.outputs[0], ta.inputs[0])
    tm = nt.nodes.new('ShaderNodeMapRange'); tm.inputs['From Min'].default_value = 0.42; tm.inputs['From Max'].default_value = 0.18
    tm.inputs['To Max'].default_value = 0.7; link(nt, ta.outputs[0], tm.inputs['Value'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.5; nz.inputs['Detail'].default_value = 8
    link(nt, tc.outputs['Object'], nz.inputs['Vector'])
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = hexc('#6f7276'); rp.color_ramp.elements[1].color = hexc('#8f9296')
    link(nt, nz.outputs['Fac'], rp.inputs['Fac'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; link(nt, tm.outputs[0], mx.inputs['Factor'])
    link(nt, rp.outputs['Color'], mx.inputs[6]); mx.inputs[7].default_value = hexc('#55585c')
    link(nt, mx.outputs[2], b.inputs['Base Color'])
    rr_ = nt.nodes.new('ShaderNodeMapRange'); rr_.inputs['To Min'].default_value = 0.92; rr_.inputs['To Max'].default_value = 0.7
    link(nt, tm.outputs[0], rr_.inputs['Value']); link(nt, rr_.outputs[0], b.inputs['Roughness'])
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.25; bump.inputs['Distance'].default_value = 0.03
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 4.0; n2.inputs['Detail'].default_value = 10
    link(nt, tc.outputs['Object'], n2.inputs['Vector']); link(nt, n2.outputs['Fac'], bump.inputs['Height']); link(nt, bump.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = hexc('#7f8286'); return m
ROAD = M_road()
def road():
    prof = [(-5.6, -0.08), (-4.6, 0.3), (-4.0, 0.12), (-3.5, 0.07), (0.0, 0.1), (3.5, 0.07), (4.0, 0.12), (4.6, 0.3), (5.6, -0.08)]
    n = int((ROAD_R1 - ROAD_R0) / 0.8); bm = bmesh.new(); uvl = bm.loops.layers.uv.new(); rows = []
    for i in range(n + 1):
        r = ROAD_R0 + (ROAD_R1 - ROAD_R0) * i / n; c = ROAD_U * r
        gc = 0.0 if r < B_OUT else sum(gz(c.x + ROAD_U.x * k, c.y + ROAD_U.y * k) for k in (-2, 0, 2)) / 3.0
        fade = min(1.0, (ROAD_R1 - r) / 3.0)          # road end feathers into the regolith (the inter-station road continues in game)
        row = []
        for (u, dz) in prof:
            p = c + ROAD_N * u; g = gc if r < B_OUT or abs(u) <= 4.0 else max(gc, gz(p.x, p.y))
            row.append(bm.verts.new((p.x, p.y, g + dz * fade - 0.06 * (1 - fade))))
        rows.append((row, r))
    for (ra, r0), (rb, r1) in zip(rows, rows[1:]):
        for j in range(len(prof) - 1):
            f = bm.faces.new((ra[j], ra[j + 1], rb[j + 1], rb[j]))
            for lp, (uu, vv) in zip(f.loops, ((prof[j][0], r0), (prof[j + 1][0], r0), (prof[j + 1][0], r1), (prof[j][0], r1))): lp[uvl].uv = (uu, vv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0: f.normal_flip()
    return _obj(bm, 'road_r1', ROAD, 'Mine', smooth=True, angle=40)
road()
rot_r = math.atan2(ROAD_U.y, ROAD_U.x)
for r in (24.0, 27.5, 31.0):
    for s in (-1, 1):
        p = ROAD_U * r + ROAD_N * 5.2 * s; g = 0.0
        rbox('road_post', (0.16, 0.16, 1.2), (p.x, p.y, g + 0.55), GRAPH_S, rot=(0, 0, rot_r), r=0.03, segs=1)
        box('road_post_tip', (0.17, 0.17, 0.2), (p.x, p.y, g + 1.05), AMBERG if s > 0 else CYANS, rot=(0, 0, rot_r), bevel=0)
text('stencil_road', 'R-1', tuple(ROAD_U * 23.5 + Vector((0, 0, 0.115))), (0, 0, rot_r - math.pi / 2), 1.3, PAINT, extrude=0.002)

# ====================================================================== CRYO TANKS on the apron (stand-alone, white frosted)
def cryo_tank(tag, cx, cy, R, H, band, big_lbl, sub_lbl):
    z0 = 1.3                                                         # skirt / leg height
    rbox(tag + '_plinth', (2 * R + 1.6, 2 * R + 1.6, 0.3), (cx, cy, 0.25), GRAPH, r=0.08, segs=2)
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4; p = Vector((cx + (R - 0.25) * math.cos(a), cy + (R - 0.25) * math.sin(a)))
        rod(tag + '_leg', (p.x, p.y, 0.4), (p.x, p.y, z0 + 0.6), 0.16, WHITE_S, segs=14)
        rbox(tag + '_legfoot', (0.55, 0.55, 0.12), (p.x, p.y, 0.44), GRAPH_S, r=0.03, segs=1)
    lathe(tag + '_shell', [(0, z0), (R * 0.55, z0 + 0.05), (R * 0.9, z0 + 0.3), (R, z0 + 0.75), (R, z0 + H - 0.75), (R * 0.9, z0 + H - 0.3),
                           (R * 0.55, z0 + H - 0.05), (0, z0 + H)], (cx, cy, 0), FROST, segs=56)
    for zb in (z0 + 1.2, z0 + H * 0.5, z0 + H - 1.2):
        cyl(tag + '_band', R * 1.025, 0.32, (cx, cy, zb), band, segs=56, bevel=0.02)
    cyl(tag + '_cyan', R * 1.012, 0.06, (cx, cy, z0 + H - 1.2 - 0.3), CYAN, segs=56)
    cyl(tag + '_belt', R * 1.018, 0.7, (cx, cy, z0 + H * 0.5 + 1.6), GRAPH, segs=56, bevel=0.02)
    # frost collar near the bottom (cryo): rough whiter ring
    cyl(tag + '_frost', R * 1.008, 0.9, (cx, cy, z0 + 0.95), FROST, segs=56, bevel=0.02)
    # top: relief valve + vent stack + rail ring
    zt = z0 + H
    rod(tag + '_vent', (cx + R * 0.35, cy, zt - 0.2), (cx + R * 0.35, cy, zt + 1.6), 0.09, SATIN, segs=12)
    cyl(tag + '_vent_cap', 0.16, 0.18, (cx + R * 0.35, cy, zt + 1.65), GRAPH_S, segs=12)
    cyl(tag + '_relief', 0.14, 0.4, (cx - R * 0.3, cy + 0.2, zt - 0.05), SATIN, segs=12)
    sphere(tag + '_beacon', 0.12, (cx - R * 0.3, cy + 0.2, zt + 0.25), AMBERG, sub=2)
    # side ladder (faces +X, away from the camera side)
    for s in (-0.25, 0.25):
        rod(tag + '_ladder', (cx + R + 0.25, cy + s, z0 + 0.4), (cx + R + 0.25, cy + s, zt - 0.4), 0.03, SATIN, segs=8)
    for i in range(int((H - 0.8) / 0.4)):
        rod(tag + '_rung', (cx + R + 0.25, cy - 0.25, z0 + 0.5 + i * 0.4), (cx + R + 0.25, cy + 0.25, z0 + 0.5 + i * 0.4), 0.018, SATIN, segs=6)
    # labels wrapped onto the camera-facing side
    t1 = text('decal_' + tag, big_lbl, (cx, cy - R - 0.012, z0 + H * 0.5 - 1.1), (math.pi / 2, 0, 0), min(1.05, R * 0.55), INK, extrude=0.01)
    wrap_text(t1, cx, cy, R)
    t2 = text('decal_' + tag + '_sub', sub_lbl, (cx, cy - R - 0.012, z0 + H * 0.5 - 2.0), (math.pi / 2, 0, 0), 0.24, INK, extrude=0.006)
    wrap_text(t2, cx, cy, R)
    return Vector((cx, cy, 0))
LOX_P = Vector((14.2, -9.6, 0)); LCH4_P = Vector((16.6, 3.4, 0))
LOX_R, LOX_H = 1.7, 8.2; LCH4_R, LCH4_H = 2.1, 9.0
cryo_tank('lox', LOX_P.x, LOX_P.y, LOX_R, LOX_H, LOXB, 'LOX', 'LIQUID OXYGEN · 90 K')
cryo_tank('lch4', LCH4_P.x, LCH4_P.y, LCH4_R, LCH4_H, LCH4B, 'LCH4', 'LCH4 · LIQUID METHANE · 112 K')

# ====================================================================== BURIED Pipe_LaunchPad LINE from the Dock (+X) -> valve vault VV-1 / manifold
VV = Vector((19.2, -3.4, 0))                                         # vault centre (inside the berm, between the tanks)
PL_A = math.radians(-2.0)                                            # Dock direction (Dock Pipe_LaunchPad is ~ +X, slightly toward the camera)
PL_U = Vector((math.cos(PL_A), math.sin(PL_A), 0))
rbox('vault_box', (3.4, 2.6, 0.9), (VV.x, VV.y, 0.45), GRAPH, r=0.1, segs=2)
rbox('vault_lid', (3.2, 2.4, 0.12), (VV.x, VV.y, 0.94), GRAPH_S, r=0.04, segs=1)
box('vault_strip', (3.42, 2.62, 0.06), (VV.x, VV.y, 0.72), CYANS, bevel=0)
# the buried line surfaces here: elbow out of the vault lid toward +X (where it comes in underground)
PIPE_END = Vector((VV.x + 1.1, VV.y, 0.95))
rod('pl_riser', (PIPE_END.x, PIPE_END.y, 0.9), (PIPE_END.x, PIPE_END.y, 1.6), 0.26, WHITE_S, segs=20)
sphere('pl_elbow', 0.27, (PIPE_END.x, PIPE_END.y, 1.6), WHITE_S, sub=2)
cyl('pl_flange', 0.38, 0.12, (PIPE_END.x, PIPE_END.y, 1.05), SATIN, segs=20)
# manifold header on the lid: LOX + LCH4 branches with handwheel valves
MAN_Z = 1.6
rod('man_header', (VV.x - 1.4, VV.y, MAN_Z), (PIPE_END.x, PIPE_END.y, MAN_Z), 0.2, WHITE_S, segs=18)
for s, (tp, R_, band) in ((-1, (LOX_P, LOX_R, LOXB)), (1, (LCH4_P, LCH4_R, LCH4B))):
    bx = VV.x - 0.7 + 0.0 * s
    j = Vector((bx + 0.5 * s, VV.y, MAN_Z))
    cyl('man_valve', 0.24, 0.5, tuple(j), SATIN, segs=16)
    whl = [(j.x + 0.28 * math.cos(TAU * k / 20), j.y + 0.28 * math.sin(TAU * k / 20), MAN_Z + 0.42) for k in range(21)]
    curve_tube('man_wheel', whl, 0.03, band, res=2)
    rod('man_stem', (j.x, j.y, MAN_Z), (j.x, j.y, MAN_Z + 0.42), 0.03, SATIN, segs=6)
    # rigid insulated feed to the tank's bottom inlet (on low pipe supports)
    tin = tp + (j - tp).normalized() * (R_ + 0.6); tin.z = 0.9
    a = Vector((j.x, j.y, MAN_Z)); b = Vector((j.x, tin.y * 0.5 + j.y * 0.5, 0.9))
    rod('feed_pipe', a, Vector((j.x, j.y, 0.9)), 0.13, WHITE_S, segs=14)
    rod('feed_pipe', Vector((j.x, j.y, 0.9)), tin, 0.13, WHITE_S, segs=14)
    sphere('feed_elbow', 0.14, (j.x, j.y, 0.9), WHITE_S, sub=2)
    rod('feed_pipe', tin, Vector((tp.x + (tin - tp).normalized().x * R_ * 0.6, tp.y + (tin - tp).normalized().y * R_ * 0.6, 0.9)), 0.13, WHITE_S, segs=14)
    for t in (0.3, 0.7):
        q = Vector((j.x, j.y, 0)).lerp(Vector((tin.x, tin.y, 0)), t)
        rbox('pipe_support', (0.3, 0.5, 0.75), (q.x, q.y, 0.45), GRAPH_S, r=0.03, segs=1)
    for t in (0.15, 0.85):
        q = Vector((j.x, j.y, 0.9)).lerp(tin, t); rod('feed_collar', q - (tin - j).normalized() * 0.1, q + (tin - j).normalized() * 0.1, 0.15, band, segs=14)
rbox('vault_plate', (1.3, 0.05, 0.42), (VV.x, VV.y - 1.31, 0.5), WHITE_S, r=0.02, segs=1)
text('decal_vault', 'VV-1', (VV.x, VV.y - 1.34, 0.6), (math.pi / 2, 0, 0), 0.16, INK, extrude=0.003)
text('decal_vault2', 'LINE FROM DOCK', (VV.x, VV.y - 1.34, 0.4), (math.pi / 2, 0, 0), 0.1, INK, extrude=0.003)
# buried-line route: graphite cover strip on the apron + marker posts over the berm toward the Dock
c0 = Vector((PIPE_END.x + 0.6, PIPE_END.y, 0)); c1 = c0 + PL_U * (APR - c0.x + 0.4)
d = c1 - c0; n = max(1, int(d.length / 1.0))
for i in range(n):
    p = c0 + d * ((i + 0.5) / n)
    box('line_cover', (0.92, 0.9, 0.05), (p.x, p.y, 0.12), GRAPH, rot=(0, 0, PL_A), bevel=0.015)
for r in (23.6, 25.6, 27.6):
    p = Vector((0, 0, 0)) + PL_U * r + Vector((0, PIPE_END.y, 0)); hz = berm_h(p.length, B_IN, B_OUT, B_H)
    rod('line_marker', (p.x, p.y, hz - 0.3), (p.x, p.y, hz + 0.9), 0.05, WHITE_S, segs=8)
    box('line_marker_tip', (0.12, 0.12, 0.16), (p.x, p.y, hz + 0.95), LCH4B, bevel=0)

# ====================================================================== FUEL HOSES (flexible, on hose stands) tank -> ship tail fuel ports
SHIP_R = 4.0
PORT = {'LOX': Vector((SHIP_R + 0.45, -1.3, 1.7)), 'LCH4': Vector((SHIP_R + 0.45, 1.3, 1.7))}
FUEL_HOOKUP = (PORT['LOX'] + PORT['LCH4']) / 2
HOSE_START = {}
def hose(tag, tp, R_, port, band):
    st = tp + (port - tp).normalized() * (R_ + 0.35); st.z = 1.0
    rbox('hose_valvebox', (0.6, 0.6, 0.8), (st.x, st.y, 0.55), GRAPH_S, r=0.05, segs=1)
    cyl('hose_valve', 0.2, 0.3, (st.x, st.y, 1.05), band, segs=14)
    HOSE_START[tag] = st.copy()
    s0 = grp_begin()
    # path: valve -> down to the ground -> lies on the apron/pad -> 2 hose stands -> up to the QD at the port
    g1 = st.lerp(port, 0.18); g1.z = 0.42; g2 = st.lerp(port, 0.45); g2.z = TOP + 0.18
    s1 = st.lerp(port, 0.68); s1.z = 0.75; s2 = st.lerp(port, 0.86); s2.z = 1.15
    q = port - (port - Vector((0, 0, port.z))).normalized() * 0.55
    ctrl = [st + Vector((0, 0, 0.0)), st.lerp(g1, 0.5) + Vector((0, 0, 0.1)), g1, g2, s1, s2, q, port]
    # smooth polyline (Catmull-Rom)
    pts = []
    P = [ctrl[0]] + ctrl + [ctrl[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(8):
            t = k / 8
            pts.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)))
    pts.append(tuple(port))
    curve_tube('hose_' + tag.lower(), pts, 0.13, HOSE, res=3)
    for sp in (s1, s2):   # hose stands: saddle on a tripod
        rod('hose_stand_post', (sp.x, sp.y, TOP), (sp.x, sp.y, sp.z - 0.14), 0.05, band, segs=8)
        for k in range(3):
            a = TAU * k / 3
            rod('hose_stand_leg', (sp.x + 0.4 * math.cos(a), sp.y + 0.4 * math.sin(a), TOP), (sp.x, sp.y, TOP + 0.35), 0.03, GRAPH_S, segs=6)
        rbox('hose_saddle', (0.36, 0.36, 0.08), (sp.x, sp.y, sp.z - 0.15), GRAPH_S, r=0.02, segs=1)
    for t in (0.25, 0.55, 0.8):
        i = int(t * (len(pts) - 1)); a_, b_ = Vector(pts[i]), Vector(pts[i + 1])
        rod('hose_collar', a_, a_ + (b_ - a_).normalized() * 0.22, 0.15, band, segs=12)
    rod('hose_qd', port - (port - Vector((0, 0, port.z))).normalized() * 0.5, port, 0.2, band, segs=16)
    cyl('hose_qd_ring', 0.24, 0.08, tuple(port - (port - Vector((0, 0, port.z))).normalized() * 0.1), SATIN, rot=(0, math.pi / 2, 0), segs=16)
    grp_end(s0, 'Hose_' + tag)
hose('LOX', LOX_P, LOX_R, PORT['LOX'], LOXB)
hose('LCH4', LCH4_P, LCH4_R, PORT['LCH4'], LCH4B)
# umbilical stand at the ship tail (holds the QDs when no ship is on the pad)
for tag in ('LOX', 'LCH4'):
    p = PORT[tag] + Vector((0.9, 0, 0))
    rod('qd_stand', (p.x, p.y, TOP), (p.x, p.y, 1.45), 0.08, WHITE_S, segs=10)
    rbox('qd_stand_base', (0.7, 0.7, 0.12), (p.x, p.y, TOP + 0.06), GRAPH_S, r=0.03, segs=1)
rbox('qd_stand_bar', (0.2, 3.1, 0.16), (PORT['LOX'].x + 0.9, 0, 1.5), GRAPH_S, r=0.04, segs=1)
box('qd_stand_strip', (0.02, 2.6, 0.05), (PORT['LOX'].x + 0.79, 0, 1.5), CYAN, bevel=0)

# ====================================================================== Tier_03 CARGO pallet + pad-edge cargo lift (inside the berm, left of the gap)
_g3 = grp_begin()
CA = math.radians(-148); CX, CY = 17.4 * math.cos(CA), 17.4 * math.sin(CA)
rot_c = CA + math.pi / 2
rbox('cargo_pallet', (5.4, 2.6, 0.22), (CX, CY, 0.21), GRAPH, rot=(0, 0, rot_c), r=0.05, segs=2)
tc_ = Vector((math.cos(rot_c), math.sin(rot_c), 0)); nc_ = Vector((-tc_.y, tc_.x, 0))
for i, (dx, h, lab) in enumerate(((-1.7, 1.6, 'CRG-04'), (0.0, 1.6, 'CRG-07'), (1.7, 1.6, 'CRG-11'))):
    p = Vector((CX, CY, 0)) + tc_ * dx
    rbox('cargo_pod', (1.55, 2.2, h), (p.x, p.y, 0.32 + h / 2), WHITE, rot=(0, 0, rot_c), r=0.22, segs=4)
    for zz in (0.55, 1.35):
        rbox('cargo_band', (1.6, 2.25, 0.1), (p.x, p.y, 0.32 + zz), GRAPH, rot=(0, 0, rot_c), r=0.04, segs=2)
    q = p - nc_ * 1.12
    box('cargo_strip', (1.1, 0.02, 0.05), (q.x, q.y, 0.32 + 1.1), CYAN, rot=(0, 0, rot_c), bevel=0)
    text('decal_cargo', lab, (q.x, q.y, 0.32 + 0.95), (math.pi / 2, 0, rot_c), 0.2, INK, extrude=0.004)
LA = math.radians(-168); LX, LY = 17.6 * math.cos(LA), 17.6 * math.sin(LA); rl = LA + math.pi / 2
tl_ = Vector((math.cos(rl), math.sin(rl), 0)); nl_ = Vector((-tl_.y, tl_.x, 0))
rbox('lift_base', (3.0, 2.4, 0.3), (LX, LY, 0.25), GRAPH, rot=(0, 0, rl), r=0.06, segs=2)
for s in (-1, 1):
    for side in (-0.9, 0.9):
        rod('lift_scissor', tuple(Vector((LX, LY, 0.4)) + tl_ * 1.2 * s + nl_ * side), tuple(Vector((LX, LY, 1.6)) - tl_ * 1.2 * s + nl_ * side), 0.07, SATIN, segs=10)
rbox('lift_deck', (3.0, 2.4, 0.2), (LX, LY, 1.7), WHITE, rot=(0, 0, rl), r=0.06, segs=2)
box('lift_strip', (3.02, 2.42, 0.04), (LX, LY, 1.62), CYAN, rot=(0, 0, rl), bevel=0)
for side in (-1, 1):
    handrail(Vector((LX, LY, 1.8)) + nl_ * 1.1 * side - tl_ * 1.4, Vector((LX, LY, 1.8)) + nl_ * 1.1 * side + tl_ * 1.4, h=1.0, n=3)
grp_end(_g3, 'Tier_03')

# ====================================================================== Tier_08 FUEL-TRANSFER PUMP SKID P-2 (behind the LCH4 tank, ties into the manifold)
_g8 = grp_begin()
PS = Vector((12.6, 11.6, 0)); rot_p = math.atan2(PS.y, PS.x) + math.pi / 2
tp_ = Vector((math.cos(rot_p), math.sin(rot_p), 0)); np_ = Vector((-tp_.y, tp_.x, 0))
rbox('pump_base', (4.2, 2.8, 0.25), (PS.x, PS.y, 0.22), GRAPH, rot=(0, 0, rot_p), r=0.05, segs=2)
rbox('pump_skid', (3.6, 2.2, 1.5), (PS.x, PS.y, 1.05), WHITE, rot=(0, 0, rot_p), r=0.3, segs=4)
box('pump_strip', (3.62, 2.22, 0.06), (PS.x, PS.y, 1.45), CYAN, rot=(0, 0, rot_p), bevel=0)
text('decal_pump', 'FUEL XFER P-2', tuple(PS - np_ * 1.12 + Vector((0, 0, 1.05))), (math.pi / 2, 0, rot_p), 0.2, INK, extrude=0.003)
for k in (-1, 1):
    c = PS + tp_ * (k * 1.2) + Vector((0, 0, 3.7))
    rod('rad_post', tuple(PS + tp_ * k * 1.2 + Vector((0, 0, 1.8))), tuple(c + Vector((0, 0, -1.5))), 0.08, SATIN, segs=10)
    box('pump_radiator', (0.07, 2.4, 3.0), tuple(c), RAD, rot=(0, 0, rot_p + math.pi / 2), bevel=0.01)
for k in (-1, 1):
    q = PS + tp_ * (k * 0.9) + np_ * 1.1
    rod('pump_line', (q.x, q.y, 0.9), (LCH4_P.x - 1.0 + k * 0.5, LCH4_P.y + LCH4_R + 0.2, 0.9), 0.11, WHITE_S, segs=12)
grp_end(_g8, 'Tier_08')

# ====================================================================== Tier_20 LANDING RADAR / COMMS MAST LR-1 (left apron)
_g20 = grp_begin()
LR = Vector((-17.2, 6.4, 0))
rbox('lr_base', (2.4, 2.4, 0.4), (LR.x, LR.y, 0.3), GRAPH, r=0.06, segs=2)
rod('lr_mast', (LR.x, LR.y, 0.5), (LR.x, LR.y, 7.8), 0.2, WHITE_S, r2=0.14, segs=18)
ring('lr_glow', 0.19, (LR.x, LR.y, 2.0), 0.06, CYAN, w=0.03, segs=24)
rbox('lr_head', (0.9, 0.9, 0.7), (LR.x, LR.y, 8.0), WHITE, r=0.12, segs=2)
lathe('lr_dish', [(0, 0), (1.3, 0.42), (1.38, 0.47), (0.08, 0.06)], (0, 0, 0), WHITE_S, segs=36)
_d = bpy.data.objects[[n for n in bpy.data.objects.keys() if n.startswith('lr_dish')][-1]]
_d.location = (LR.x + 0.4, LR.y - 0.3, 8.5); _d.rotation_euler = (math.radians(-55), 0, math.radians(-30))
rod('lr_feed', (LR.x + 0.4, LR.y - 0.3, 8.4), (LR.x + 0.9, LR.y - 1.2, 9.2), 0.04, SATIN, segs=6)
box('lr_radar', (1.8, 0.12, 0.5), (LR.x, LR.y, 9.6), GRAPH_S, rot=(0, 0, 0.4), bevel=0.02)
sphere('lr_beacon', 0.14, (LR.x, LR.y, 10.0), AMBERG, sub=2)
grp_end(_g20, 'Tier_20')

# ====================================================================== POWER: solar masts behind the berm (SOL-1 base, SOL-2 = Tier_05) + fission plant (Stage)
SUN = Vector((-0.55, -0.6, 0.58)).normalized()
def _cell():
    m = bpy.data.materials.new('LP_SolarCell'); nt, b = _nodes(m)
    b.inputs['Base Color'].default_value = hexc('#152a4a'); b.inputs['Metallic'].default_value = 0.4; b.inputs['Roughness'].default_value = 0.18
    b.inputs['Coat Weight'].default_value = 0.8; m.diffuse_color = hexc('#152a4a'); return m
M_cell = _cell()
def solar_mast(x, y, h=12.0, tag='SOL-1'):
    g = gz(x, y)
    lathe('sol_foot', [(0, 0), (1.2, 0), (1.0, 0.35), (0, 0.4)], (x, y, g - 0.05), GRAPH, segs=32)
    rod('sol_mast', (x, y, g + 0.3), (x, y, g + h), 0.22, WHITE_S, r2=0.14, segs=20)
    ring('sol_glow', 0.21, (x, y, g + 1.8), 0.06, CYAN, w=0.03, segs=24)
    rbox('sol_gimbal', (0.6, 0.6, 0.6), (x, y, g + h), GRAPH_S, r=0.1, segs=2)
    rot = facing(SUN); M = rot.to_matrix(); c = Vector((x, y, g + h + 0.45))
    box('sol_panel', (6.0, 3.8, 0.1), tuple(c), GRAPH_S, rot=tuple(rot), bevel=0.01)
    for i in range(4):
        for j in range(3):
            off = M @ Vector((-2.2 + i * 1.47, -1.22 + j * 1.22, 0.06))
            box('sol_cell', (1.38, 1.12, 0.02), tuple(c + off), M_cell, rot=tuple(rot), bevel=0)
    text('decal_sol', tag, (x, y - 0.23, g + 2.6), (math.pi / 2, 0, 0), 0.2, INK, extrude=0.003)
    rbox('sol_box', (0.7, 0.45, 0.9), (x, y - 0.45, g + 0.8), WHITE, r=0.08, segs=2)
SOL = [(-12.0, 31.0, 12.0, 'SOL-1'), (-20.0, 27.0, 11.0, 'SOL-2')]
solar_mast(*SOL[0])
# power junction PWR-01 on the left apron + cable over the berm on low stanchions
JX, JY = -18.6, -2.0
rbox('pwr_junction', (1.4, 0.9, 1.7), (JX, JY, 0.95), WHITE, r=0.14, segs=3)
box('pwr_junction_strip', (1.0, 0.02, 0.06), (JX, JY - 0.46, 1.55), CYAN, bevel=0)
text('decal_pwr', 'PWR-01', (JX, JY - 0.46, 1.25), (math.pi / 2, 0, 0), 0.16, INK, extrude=0.003)
route = [Vector((-12.0, 30.4, 0)), Vector((-13.5, 22.5, 0)), Vector((-17.0, 14.0, 0)), Vector((JX, JY + 0.6, 0))]
posts = []
for a, b in zip(route, route[1:]):
    L = (b - a).length; n = max(1, int(L / 4.5))
    for i in range(n): posts.append(a.lerp(b, i / n))
posts.append(route[-1])
def pz(p):
    r = p.length; return max(berm_h(r, B_IN, B_OUT, B_H), gz(p.x, p.y) if r > B_OUT else 0.0, 0.1 if r < APR else 0.0)
for p in posts[1:-1]:
    g = pz(p); rod('cable_post', (p.x, p.y, g - 0.1), (p.x, p.y, g + 0.8), 0.05, GRAPH_S, segs=8)
    box('cable_saddle', (0.22, 0.22, 0.07), (p.x, p.y, g + 0.8), SATIN, bevel=0.01)
for a, b in zip(posts, posts[1:]):
    cable('power_cable', (a.x, a.y, pz(a) + 0.85), (b.x, b.y, pz(b) + 0.85), 0.045, RUBBER, sag=0.25, n=10)
_g5 = grp_begin(); solar_mast(*SOL[1])
cable('sol_feed2', (SOL[1][0], SOL[1][1] - 0.45, gz(SOL[1][0], SOL[1][1]) + 0.5), (-12.6, 29.6, gz(-12.6, 29.6) + 0.6), 0.04, RUBBER, sag=0.3)
grp_end(_g5, 'Tier_05')
# fission plant (Stage) - far behind its own berm
mound('reactor_berm', RXr + 8.0, RYr - 9.0, 11.0, 1.4, 5.2, 5.0, REGO, c='Stage', seed=31)
lathe('reactor_vessel', [(0, 0), (3.0, 0), (3.0, 5.4), (2.3, 6.3), (0, 6.5)], (RXr, RYr, gz(RXr, RYr) - 0.1), WHITE, segs=48, c='Stage')
ring('reactor_band', 3.02, (RXr, RYr, 4.0), 0.24, GRAPH, w=0.06, segs=48, c='Stage')
ring('reactor_glow', 3.02, (RXr, RYr, 4.7), 0.1, CYAN, w=0.03, segs=48, c='Stage')
for s in (-1, 1):
    box('reactor_radiator', (10.0, 0.1, 7.0), (RXr + s * 8.5, RYr + 0.5, 6.0), RAD, rot=(0, 0, s * 0.15), bevel=0.01, c='Stage')
    rod('reactor_rad_boom', (RXr + s * 2.8, RYr + 0.5, 6.0), (RXr + s * 13.5, RYr + 0.5 + s * 1.6, 6.0), 0.14, GRAPH_S, c='Stage')
sphere('reactor_beacon', 0.35, (RXr, RYr, 6.8), AMBERG, sub=2, c='Stage')
fp = [Vector((RXr + 4.0, RYr - 6.0, 0)), Vector((-40.0, 46.0, 0)), Vector((-12.0, 31.6, 0))]
fposts = []
for a, b in zip(fp, fp[1:]):
    L = (b - a).length; n = max(1, int(L / 6.0))
    for i in range(n): fposts.append(a.lerp(b, i / n))
for p in fposts:
    g = gz(p.x, p.y); rod('cable_post_far', (p.x, p.y, g - 0.05), (p.x, p.y, g + 0.9), 0.05, GRAPH_S, segs=8, c='Stage')
for a, b in zip(fposts, fposts[1:] + [fp[-1]]):
    cable('power_cable_far', (a.x, a.y, gz(a.x, a.y) + 0.95), (b.x, b.y, gz(b.x, b.y) + 0.95), 0.05, RUBBER, sag=0.3, n=10, c='Stage')

# ====================================================================== GRAY PLACEHOLDER SHIP (Stage only: 40 m tall, 8 m wide, 4 legs, ramp toward -Y)
SC = 'Stage'; SZ0 = TOP + 2.6
lathe('ship_ph_body', [(0, SZ0), (SHIP_R, SZ0), (SHIP_R, 30.0), (SHIP_R * 0.9, 33.5), (SHIP_R * 0.62, 36.6), (SHIP_R * 0.3, 39.0), (0, TOP + 40.0)], (0, 0, 0), SHIPG, segs=64, c=SC)
for k in range(3):
    a = TAU * k / 3; p = (1.5 * math.cos(a), 1.5 * math.sin(a))
    lathe('ship_ph_bell', [(0.35, SZ0 + 0.05), (0.5, SZ0 - 0.6), (1.0, SZ0 - 2.0), (1.06, SZ0 - 2.05)], (p[0], p[1], 0), GRAPH, segs=32, c=SC)
for k in range(4):
    a = TAU * k / 4 + math.pi / 4; u = Vector((math.cos(a), math.sin(a), 0))
    top = u * (SHIP_R - 0.2) + Vector((0, 0, SZ0 + 4.5)); foot = u * 7.0 + Vector((0, 0, TOP + 0.3))
    rod('ship_ph_leg', top, foot, 0.32, SHIPG, segs=14, c=SC)
    rod('ship_ph_strut', u * (SHIP_R - 0.2) + Vector((0, 0, SZ0 + 0.3)), foot.lerp(top, 0.35), 0.18, SHIPG, segs=10, c=SC)
    lathe('ship_ph_foot', [(0, 0), (1.0, 0), (0.85, 0.3), (0, 0.35)], (foot.x, foot.y, TOP), SHIPG, segs=24, c=SC)
RAMP_FOOT = Vector((0, -9.6, TOP))
beam('ship_ph_ramp', Vector((0, -SHIP_R + 0.2, SZ0 + 1.4)), RAMP_FOOT + Vector((0, 0, 0.1)), 2.4, 0.2, SHIPG, bevel=0.03, c=SC, up=Vector((1, 0, 0)))
for z in (12.0, 22.0):
    ring('ship_ph_seam', SHIP_R + 0.01, (0, 0, z), 0.08, GRAPH, w=0.03, segs=64, c=SC)

# ====================================================================== stage cleanup + lights + crew
EXCL = [((0, 0), 34.0)] + [((x, y), 4.0) for x, y, _, _ in SOL] + [((RXr, RYr), 18.0)] + [((ROAD_U.x * r, ROAD_U.y * r), 7.0) for r in range(30, 40, 3)]
for ob in list(coll('Stage').objects):
    if ob.name.split('.')[0] in ('boulder', 'pebble', 'slope_boulder'):
        x, y = ob.matrix_world.translation.x, ob.matrix_world.translation.y
        if any(math.hypot(x - cx, y - cy) < r for (cx, cy), r in EXCL): bpy.data.objects.remove(ob); continue
        for a, b in zip(fposts, fposts[1:]):
            ab = b - a; t = max(0, min(1, (Vector((x, y, 0)) - a).dot(ab) / max(1e-6, ab.length_squared)))
            if (a + ab * t - Vector((x, y, 0))).length < 2.0: bpy.data.objects.remove(ob); break
for k in range(50):
    a = rr.uniform(0, TAU); dd = rr.uniform(B_OUT + 0.5, B_OUT + 6.0); s = rr.uniform(0.05, 0.18)
    if abs(((a - GAP_C + math.pi) % TAU) - math.pi) < GAP_W + 0.15: continue
    sphere('ejecta_pebble', s, (dd * math.cos(a), dd * math.sin(a), gz(dd * math.cos(a), dd * math.sin(a))), REGO, scale=(1.2, 1, 0.6), sub=1, jitter=0.4, smooth=False, seed=k, c='Stage')
world_and_sun((-0.55, -0.6, 0.58), 5.5)
astronaut((RAMP_FOOT.x + 1.6, RAMP_FOOT.y - 0.8, TOP), rot_z=0.4)              # at the ramp foot
astronaut((PORT['LOX'].x + 1.8, PORT['LOX'].y - 2.2, TOP), rot_z=-0.9)          # checking the LOX hose QD
astronaut((VV.x - 1.2, VV.y - 2.0, 0.1), rot_z=0.2)                             # at the valve vault
_ra = ROAD_U * 27.0 + ROAD_N * 1.4; astronaut((_ra.x, _ra.y, 0.1), rot_z=rot_r + math.pi / 2)   # walking in through the berm gap
cam = setup_render(64 if not QUICK else 16)

ONLY = A.get('only', 'hero').split(',')
SHOW_TIERS = A.get('tiers') == '1'
for o in coll(TC).all_objects: o.hide_render = not SHOW_TIERS

# ====================================================================== phone-camera projection (Game Coder camera) for checks
def phone_cam(w, h):
    PC = GAME_NAMES['phone_cam']; half = math.radians(PC['fov_y'] / 2); a = w / h
    dd = (PC['frame_w'] / 2) / (math.tan(half) * a); el = math.radians(PC['pitch'])
    T = Vector(PC['target']); C = T + Vector((0, -math.cos(el), math.sin(el))) * dd
    return T, C, dd, half
def project(pts, w, h):
    T, C, dd, half = phone_cam(w, h); el = math.radians(GAME_NAMES['phone_cam']['pitch'])
    f = Vector((0, math.cos(el), -math.sin(el))); r = Vector((1, 0, 0)); u = Vector((0, math.sin(el), math.cos(el))); t = math.tan(half); a = w / h
    out = []
    for p in pts:
        v = Vector(p) - C; z = v.dot(f)
        out.append(((1 + v.dot(r) / (z * t * a)) / 2 * w, (1 - v.dot(u) / (z * t)) / 2 * h))
    return out
def group_pts():
    dg = bpy.context.evaluated_depsgraph_get(); G = {}
    for o in coll('Mine').all_objects:
        if o.type not in ('MESH', 'CURVE', 'FONT') or o.name.split('.')[0].startswith(('decal_', 'stencil_')): continue
        oe = o.evaluated_get(dg)
        try: me = oe.to_mesh()
        except Exception: continue
        if me is None: continue
        M = oe.matrix_world; G.setdefault(o.get('grp', 'Base'), []).extend([M @ v.co for v in me.vertices]); oe.to_mesh_clear()
    return G
if 'check' in ONLY:
    G = group_pts(); ok = True
    for (w, h), (x0, x1, y0, y1) in SAFE.items():
        T, C, dd, _ = phone_cam(w, h)
        print(f'CHECK {w}x{h} band x {x0}-{x1} y {y0}-{y1}  d {dd:.3f}  cam {tuple(round(v, 2) for v in C)}', flush=True)
        for g, pts in sorted(G.items()):
            pr = project(pts, w, h); xs = [p[0] for p in pr]; ys = [p[1] for p in pr]
            bad = min(xs) < x0 or max(xs) > x1 or min(ys) < y0 or max(ys) > y1; ok &= not bad
            print(f'   {g:10s} x {min(xs):6.1f}-{max(xs):6.1f}  y {min(ys):6.1f}-{max(ys):6.1f}  {"OUT" if bad else "ok"}', flush=True)
        sp = project([Vector((0, 0, TOP + 40.0)), Vector((0, 0, TOP))], w, h); print(f'   ship top y {sp[0][1]:.1f} (may run above), ship base y {sp[1][1]:.1f}', flush=True)
    print('CHECK_ALL', 'PASS' if ok else 'FAIL', flush=True)

if 'glb' in ONLY: export_glb(os.path.join(OUT, f'{NAME}_master.glb'))
if 'blend' in ONLY:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'{NAME}_master.blend'), compress=True)
assert not ('game' in ONLY and set(ONLY) & {'hero', 'turn', 'portrait', 'blend', 'glb'}), 'game step is destructive: run it on its own'
if 'game' in ONLY:   # game-ready GLB: SH_* palette, merged by material, <=30k tris, no textures; meshopt + quantization via gltfpack -cc
    import json
    SHJ = os.path.normpath(os.path.join(HERE, '..', '..', '_shared', 'shared_materials.json'))
    pal = json.load(open(SHJ))['materials']
    def sh_mat(n):
        if n in bpy.data.materials: return bpy.data.materials[n]
        d = pal[n]; m = bpy.data.materials.new(n); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = hexc(d['base']); b.inputs['Metallic'].default_value = d['metal']; b.inputs['Roughness'].default_value = d['rough']
        if 'emissive' in d: b.inputs['Emission Color'].default_value = hexc(d['emissive']); b.inputs['Emission Strength'].default_value = d['emissive_strength']
        return m
    # Base 7 draws (Rock, White, Graphite, Steel, GlowCyan, PipeO2 = LOX bands, Red = LCH4 bands) + 2 hoses + tiers 6 (Tier_05 = 2) = 15 max
    RULES = [('lox', 'SH_PipeO2'), ('lch4', 'SH_Red'), ('cyan', 'SH_GlowCyan'), ('glow', 'SH_GlowCyan'), ('lamp', 'SH_GlowCyan'), ('amber', 'SH_GlowCyan'),
             ('glass', 'SH_Graphite'), ('lens', 'SH_Graphite'), ('solar', 'SH_Solar'), ('rad', 'SH_White'), ('foil', 'SH_Steel'), ('mli', 'SH_Steel'),
             ('sinter', 'SH_Rock'), ('apron', 'SH_Rock'), ('road', 'SH_Rock'), ('rego', 'SH_Rock'), ('block', 'SH_Rock'), ('rock', 'SH_Rock'),
             ('satin', 'SH_Steel'), ('graph', 'SH_Graphite'), ('rubber', 'SH_Graphite'), ('ink', 'SH_Graphite'), ('white', 'SH_White'), ('frost', 'SH_White'), ('paint', 'SH_White')]
    GROUP_MAT = {'Hose_LOX': 'SH_Foil', 'Hose_LCH4': 'SH_Foil', 'Tier_03': 'SH_White', 'Tier_08': 'SH_White', 'Tier_12': 'SH_GlowWhite', 'Tier_20': 'SH_White', 'Tier_05': None}
    def remap(m, g=None):
        n = (m.name if m else '').lower()
        if g in GROUP_MAT:
            if GROUP_MAT[g]: return GROUP_MAT[g]
            return 'SH_Solar' if 'solar' in n else 'SH_White'
        for k, v in RULES:
            if k in n: return 'SH_Graphite' if v == 'SH_Solar' else v   # base SOL-1 cells share Graphite (draw budget); SH_Solar only on Tier_05
        print('UNMAPPED', m.name if m else None); return 'SH_White'
    keep = [o for o in coll('Mine').all_objects if o.type in ('MESH', 'CURVE', 'FONT') and not o.name.split('.')[0].startswith(('decal_', 'stencil_'))]
    for o in list(coll('Mine').all_objects):
        if o not in keep: bpy.data.objects.remove(o)
    for o in keep: o.hide_set(False); o.hide_render = False
    bpy.ops.object.select_all(action='DESELECT')
    for o in keep: o.select_set(True)
    bpy.context.view_layer.objects.active = keep[0]
    bpy.ops.object.convert(target='MESH')
    allm = [o for o in coll('Mine').all_objects if o.type == 'MESH']
    groups = {}
    for o in allm:
        g = o.get('grp', 'Base'); groups.setdefault(g, []).append(o)
        o.data = o.data.copy()
        for sl in o.material_slots: sl.material = sh_mat(remap(sl.material, g))
    nodes = {}
    for g, obs in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in obs: o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        if len(obs) > 1: bpy.ops.object.join()
        G = bpy.context.active_object
        G.name = GAME_NAMES['base'] if g == 'Base' else (GAME_NAMES['hoses'][g][0] if g in GAME_NAMES['hoses'] else GAME_NAMES['tiers'][g][0])
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.001); bpy.ops.object.mode_set(mode='OBJECT')
        names = [sl.material.name for sl in G.material_slots]; uniq = sorted(set(names), key=names.index)
        idx = [uniq.index(n) for n in names]; pidx = [idx[p.material_index] for p in G.data.polygons]
        G.data.materials.clear()
        for n in uniq: G.data.materials.append(bpy.data.materials[n])
        for p, i in zip(G.data.polygons, pidx): p.material_index = i
        nodes[g] = G
    tri = lambda G: sum(len(p.vertices) - 2 for p in G.data.polygons)
    T0 = sum(tri(G) for G in nodes.values()); TGT = int(A.get('tris', 24000))
    def dec(G, ratio):
        bpy.ops.object.select_all(action='DESELECT'); G.select_set(True); bpy.context.view_layer.objects.active = G
        md = G.modifiers.new('Dec', 'DECIMATE'); md.ratio = max(0.03, min(1.0, ratio)); md.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=md.name)
    for g, G in nodes.items():
        cap = 1200 if g.startswith('Hose_') else 1000
        if g != 'Base' and tri(G) > cap: dec(G, cap / tri(G))
    B = nodes['Base']
    for it in range(6):
        rest = sum(tri(G) for g, G in nodes.items() if g != 'Base'); t = tri(B)
        if t + rest <= TGT: break
        dec(B, (TGT - rest) / t * 0.97)
    for g, G in nodes.items(): print('NODE', g, tri(G), [m.name for m in G.data.materials], flush=True)
    print('GAMETRIS', T0, '->', sum(tri(G) for G in nodes.values()), 'DRAWS', sum(len(G.data.materials) for G in nodes.values()), flush=True)
    for g, G in nodes.items():
        if 'grp' in G: del G['grp']
        if g in GAME_NAMES['tiers']: G['tier'] = GAME_NAMES['tiers'][g][1]; G['hidden_by_default'] = True
        if g in GAME_NAMES['hoses']:   # origin at the tank valve; code shows the hose attaching to Fuel_Hookup
            h = HOSE_START[g.split('_')[1]]; G.data.transform(Matrix.Translation(-h)); G.location = h
            G['fuel'] = GAME_NAMES['hoses'][g][1]; G['attach_to'] = GAME_NAMES['markers']['Fuel_Hookup']
    def mark(n, p):
        e = bpy.data.objects.new(n, None); e.empty_display_size = 0.5; e.location = tuple(p); coll('Mine').objects.link(e); return e
    MN = GAME_NAMES['markers']; re_ = ROAD_U * 32.0
    mk = [mark(MN['Ship_Center'], (0, 0, TOP)), mark(MN['Road_Entry'], (re_.x, re_.y, 0.1)), mark(MN['Ramp_Foot'], RAMP_FOOT),
          mark(MN['Crate_Drop'], (CX, CY, 0.33)), mark(MN['Fuel_Hookup'], FUEL_HOOKUP), mark(MN['Pipe_LaunchPad_End'], PIPE_END),
          mark(MN['Cam_Target'], GAME_NAMES['phone_cam']['target'])]
    mk[-1]['frame_w'] = GAME_NAMES['phone_cam']['frame_w']   # Cam_Target: empty only (no draw) + extras {frame_w}
    mk[5]['from'] = 'Dock Pipe_LaunchPad (buried, +X)'
    path = [re_, ROAD_U * 27.0, ROAD_U * 21.5, Vector((-3.0, -13.0, 0)), RAMP_FOOT]
    for i, p in enumerate(path):
        z = TOP if Vector((p.x, p.y, 0)).length < PAD_R else 0.1
        mk.append(mark(GAME_NAMES['crew_path'] % (i + 1), (p.x, p.y, z)))
    bpy.ops.object.select_all(action='DESELECT')
    for o in list(nodes.values()) + mk: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{NAME}_game_raw.glb'), export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                              export_animations=False, export_extras=True, export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False,
                              export_materials='EXPORT', export_image_format='NONE', export_texcoords=False)
    print('GAMEGLB', flush=True)
HC = A.get('hc')
if 'hero' in ONLY:
    w, h = (3840, 2160) if not QUICK else (960, 540)
    tgt = (2.0, 0.0, 9.0); pos = (-38.0, -92.0, 26.0)
    if HC: v = [float(t) for t in HC.split(',')]; pos, tgt = tuple(v[:3]), tuple(v[3:6])
    shoot(cam, os.path.join(OUT, 'hero.png'), tgt, pos, w, h, lens=float(A.get('lens', 30)), samples=int(A.get('hs', 64)) if not QUICK else 16)
if 'portrait' in ONLY:   # the game camera exactly: aimed at Cam_Target, 38 deg vertical FOV, 18 deg down, no azimuth, d from frame_w + aspect
    pw, ph = int(A.get('pw', 1179)), int(A.get('ph', 2556))
    T, C, dd, half = phone_cam(pw, ph)
    print('PHONECAM', pw, ph, 'target', tuple(round(v, 3) for v in T), 'cam', tuple(round(v, 3) for v in C), 'd', round(dd, 3), flush=True)
    cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 36.0
    shoot(cam, os.path.join(OUT, A.get('pname', 'portrait') + '.png'), tuple(T), tuple(C), pw, ph, lens=18.0 / math.tan(half), samples=int(A.get('hs', 64)) if not QUICK else 16)
    cam.data.sensor_fit = 'AUTO'
if 'turn' in ONLY:
    os.makedirs(os.path.join(OUT, 'turntable'), exist_ok=True)
    turntable(cam, os.path.join(OUT, 'turntable'), (2.0, 0.0, 9.0), 150, 22, size=1000 if not QUICK else 400, samples=int(A.get('ts', 48)) if not QUICK else 12)
