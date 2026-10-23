"""Planet Stack - SHIPYARD (SY-01), high-detail concept master (Blender 4.2 LTS, headless, Cycles).

blender -b -P build_shipyard.py -- --out .. [--quick 1] [--only glb,blend,game,hero,turn] [--tris 18000] [--hs 64] [--ts 48]
       [--hc x,y,z,tx,ty,tz] [--lens 26] [--tiers 1 (render upgrade tiers)] [--only portrait]
Game GLB names: GAME_NAMES dict below (one place).

Blender coords: Z up, metres, front = -Y (toward the camera). Exported GLB: Y up, front +Z, origin = yard centre on the ground.
Style: Mine concept B (sleek high-tech): glossy white + graphite panels, satin metal, cyan light strips, weathered + dusty.
Reuses the shared helpers in art/3d/mine_concepts/_src/mc_common.py by import (not modified); cool-grey ground as the launch pad.
True scale: 1.8 m astronauts; the IS-1 stack is a starter-class hull UNDER CONSTRUCTION (modelled here, exported with the building).

Systems (collection 'Mine' = exported building), all ABOVE GROUND on a sintered yard slab:
  * assembly hall AH-1 (34 x 26 x 24 m, 1.2 m shielded white walls, 20 m door open to -Y), bridge crane, hull barrel on a cradle,
    engine-skirt section, roof radiators, interior work lights
  * welding bay W-2: barrel section on turning rolls, 4 robot welders, weld screens, power unit with white radiators
  * integration stand IS-1: sintered pad r 15 m, 46 m tower with C-shaped work platforms around a part-built stack (2 skinned rings,
    open-bay ring with exposed frames / stringers / tank dome); the tower jib crane holds the next ring over the open top
  * foundry FAB-01 (metals foundry: refinery leftovers -> hull parts): 3 furnace columns, LOX + LH2 spheres, pipe rack, radiator bank, furnace F-1, slag hopper + conveyor,
    propellant line to the stand
  * yard control YC-1: above-ground hab on legs, airlock A1 + suitports, dust-off arch, stair
  * power: 2 solar masts + cable run from a distant fission plant behind a berm (Stage)
Outputs: shipyard_master.glb, shipyard_game.glb (SH_* palette, merged by material, <=30k tris, meshopt), .blend, hero, turntable.
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
MC = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'mine_concepts', '_src'))
sys.path.insert(0, MC)
import bpy, bmesh
from mathutils import Vector, Matrix, noise
from mc_common import *
from mc_common import _obj, _nodes

A = argv(); OUT = os.path.abspath(A.get('out', '/tmp/sy_out')); os.makedirs(OUT, exist_ok=True)
QUICK = A.get('quick') == '1'
reset(); rr = random.Random(202)
TAU = math.tau
NAME = 'shipyard'
# ---- game-GLB node / clip / marker names: ONE mapping (pad + Life Support pattern) - rename here only
GAME_NAMES = {
    'base': 'shipyard_base',
    'tiers': {'Tier_03': ('Tier_03', 3), 'Tier_05': ('Tier_05', 5), 'Tier_08': ('Tier_08', 8), 'Tier_12': ('Tier_12', 12), 'Tier_20': ('Tier_20', 20)},
    'moving': {'Crane_Jib': ('Crane_Jib', 'crane_jib_swing'), 'Hall_Door': ('Hall_Door', 'hall_door_open'), 'Beacon_Lights': ('Beacon_Lights', 'Beacon_Lights_Blink')},
    'door_leaves': ('Hall_Door_L', 'Hall_Door_R'),     # mesh children of the Hall_Door pivot empty
    'markers': {'Stand_Center': 'Stand_Center', 'Hall_Door_Front': 'Hall_Door_Front', 'Road_Entry': 'Road_Entry', 'Crate_Drop': 'Crate_Drop', 'Cam_Target': 'Cam_Target'},
    'crew_path': 'Crew_Path_%02d',
    # in-game phone camera (Game Coder spec): perspective, VERTICAL FOV 38 deg (sensor_fit VERTICAL), pitched down 18 deg, lookAt(Cam_Target),
    # azimuth -86 deg (camera toward -Y, slightly +X). Cam_Target extras {'frame_w': W}; d = (W/2) / (tan(19 deg) * 393/852) ~= 3.148 * W.
    # Framing rule on 393x852 (x3 on 1179x2556): focus (hall door + SN-07 + crane) whole inside y 100..650; HUD above, sheet from y 674.
    # Blender Z-up coords; glTF Y-up = (x, z, -y).
    'phone_cam': {'target': (8.5, 4.5, 16.5), 'az': -100.0, 'pitch': 18.0, 'fov_y': 38.0, 'frame_w': 55.0},   # W 55: SN-07 + whole IS-1 stand pad in x 181-386, y 359-561 of 852; hall door's left half crops
}

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

WHITE   = P_('SY_White', '#eceff2', rough=0.22, metal=0.0, coat=0.8, grime=0.22, grime_col='#9ea2a7', wear=0.12, wear_col='#9aa3ad', panel=0.8, bevel=0.03, dirt_scale=1.4)
WHITE_S = P_('SY_WhiteSmooth', '#eef1f4', rough=0.2, metal=0.0, coat=0.9, grime=0.16, grime_col='#9ea2a7', wear=0.1, wear_col='#9aa3ad', bevel=0.03)
RAD     = P_('SY_Radiator', '#f2f4f7', rough=0.3, metal=0.0, coat=0.4, grime=0.14, grime_col='#9ea2a7', panel=4.0, bevel=0.01)
GRAPH   = P_('SY_Graphite', '#2c3137', rough=0.3, metal=0.55, coat=0.5, grime=0.16, grime_col='#63676c', wear=0.2, wear_col='#9aa0a6', panel=1.4, bevel=0.02)
GRAPH_S = P_('SY_GraphiteSmooth', '#30353c', rough=0.28, metal=0.6, coat=0.5, grime=0.16, grime_col='#63676c', wear=0.18, wear_col='#9aa0a6', bevel=0.02)
SATIN   = P_('SY_Satin', '#9aa3ad', rough=0.25, metal=1.0, grime=0.2, grime_col='#55595e', wear=0.1, wear_col='#d0d5db', bevel=0.01)
RUBBER  = P_('SY_Rubber', '#1d2024', rough=0.8, metal=0.0, grime=0.3, grime_col='#676b70', bump_noise=0.3)
FOIL    = P_('SY_MLI', '#c9ced6', rough=0.3, metal=0.9, grime=0.2, grime_col='#565a5f', bump_noise=0.5, bevel=0.01)
PAINT   = P_('SY_PadPaint', '#e9ecef', rough=0.55, metal=0.0, grime=0.45, grime_col='#5a5e62', dirt_scale=0.6, upamt=0.0) if False else None
INK     = M_paint('SY_Ink', '#1f2329', rough=0.5, metal=0.0)
INKW    = M_paint('SY_InkWhite', '#f4f7fa', rough=0.4, metal=0.0)
LOXB    = P_('SY_LoxBand', '#2f7fe0', rough=0.3, metal=0.1, coat=0.5, grime=0.15)
LH2B    = P_('SY_LH2Band', '#e8701a', rough=0.3, metal=0.1, coat=0.5, grime=0.15)
CYAN    = M_glow('SY_Cyan', '#2fe3ff', 16)
CYANS   = M_glow('SY_CyanSoft', '#2fe3ff', 5)
LAMP    = M_glow('SY_Lamp', '#f2fbff', 25)
AMBERG  = M_glow('SY_AmberLamp', '#ffb020', 14)
GLASS   = M_glass('SY_Lens', '#1b2a36', 0.04)
REGO    = M_rock('SY_Regolith', '#63666a', '#8b8f93')

def M_pad_paint():
    m = bpy.data.materials.new('SY_PadPaint'); nt, b = _nodes(m)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 9
    link(nt, tc.outputs['Object'], nz.inputs['Vector'])
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].position = 0.42; rp.color_ramp.elements[1].position = 0.62
    rp.color_ramp.elements[0].color = hexc('#979a9e'); rp.color_ramp.elements[1].color = hexc('#e6e8ea')
    link(nt, nz.outputs['Fac'], rp.inputs['Fac']); link(nt, rp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.6
    m.diffuse_color = hexc('#e6e8ea'); return m
PAINT = M_pad_paint()

def M_sinter(name='SY_Sintered'):
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
BLOCK = P_('SY_SinterBlock', '#5c5b5d', rough=0.5, metal=0.0, grime=0.35, grime_col='#86898e', bump_noise=0.4, bevel=0.03, dirt_scale=1.0)

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


# ====================================================================== STAGE FIRST (cool-grey from the start)
SHX, SHY = 22.0, 8.0             # integration stand / starter ship
HX, HY, HW, HD, HH = -20.0, 12.0, 34.0, 26.0, 24.0   # assembly hall AH-1
WX, WY = -27.0, -21.0            # welding bay W-2
RFX, RFY = 50.0, -16.0           # foundry FAB-01 (relabelled; ex-REF-01 geometry)
CSX, CSY = 4.0, -38.0            # yard control YC-1
RXr, RXy = -82.0, 52.0           # distant fission plant
height = build_stage(keep_flat=((5, -4, 62), (5, -4, 62), (RFX, RFY, 28), (RFX, RFY, 28), (CSX, CSY, 18), (-50, -16, 18), (RXr, RXy, 24), (RXr, RXy, 24)))
def gz(x, y): return height(x, y)
RYr = RXy
# ---------------------------------------------------------------------- far-hill geometry break-up (material: shared mc_common.M_ground)
def _ridge(x, y, o):
    return (1 - abs(noise.noise(Vector((x, y, o))))) ** 2
def hill_disp(x, y, z):
    """break up the shared stage's benches: irregular ridges / spurs / gullies on the far hills only."""
    if y < 48 or z < 0.2: return 0.0
    w = min(1.0, z / 3.5) * min(1.0, (y - 48) / 10)
    d = 3.2 * (_ridge(x * 0.028, y * 0.05, 7.3) - 0.3) + 1.6 * noise.noise(Vector((x * 0.07, y * 0.09, 3.1)))
    d += 0.9 * _ridge(x * 0.11, y * 0.16, 9.7) - 0.7 * _ridge(x * 0.19 + 0.3 * y * 0.02, y * 0.045, 12.2)
    return w * d
_g = bpy.data.objects['Ground']
for v in _g.data.vertices: v.co.z += hill_disp(v.co.x, v.co.y, v.co.z)
_g.data.update()   # ground material = the SHARED M_ground() that mc_common.build_stage() already assigned (mc_common @269e70f, no local variant)
assert _g.data.materials[0].name.startswith('M_Regolith'), 'Ground must use mc_common.M_ground'
for ob in coll('Stage').objects:
    if ob.name.startswith('slope_boulder'):
        t = ob.matrix_world.translation; ob.location.z += hill_disp(t.x, t.y, t.z)
_bm = bpy.data.materials.get('M_Boulder')
if _bm:
    for nd in _bm.node_tree.nodes:
        if nd.type == 'VALTORGB': nd.color_ramp.elements[0].color = hexc('#5c5f63'); nd.color_ramp.elements[1].color = hexc('#85888c')
    _bm.diffuse_color = hexc('#5c5f63')


YTOP = 0.18
HALLW = P_('SY_HallWhite', '#e4e7ea', rough=0.48, metal=0.0, coat=0.12, grime=0.25, grime_col='#9ea2a7', wear=0.1, wear_col='#9aa3ad', panel=0.8, bevel=0.03, dirt_scale=1.4)
YARD = P_('SY_YardSinter', '#56595d', rough=0.7, metal=0.0, grime=0.4, grime_col='#8a8d91', bump_noise=0.35, bevel=0.0, dirt_scale=0.5)
def tag(o, g):
    o['grp'] = g; return o
def grp_begin(): return set(bpy.data.objects.keys())
def grp_end(s0, g):
    for n in set(bpy.data.objects.keys()) - s0: bpy.data.objects[n]['grp'] = g
TC = 'Tiers'   # upgrade tiers: own collection, hidden in hero / turntable / master GLB, exported (hidden_by_default) in the game GLB
_tc = bpy.data.collections.new(TC); bpy.context.scene.collection.children.link(_tc)
# ====================================================================== YARD SLAB (sintered, everything sits above ground)
rbox('yard_slab', (112.0, 66.0, 0.7), (8.0, -6.0, YTOP - 0.35), YARD, r=0.25, segs=2)
for x0, x1, y in ((-48.0, 64.0, -39.1), (-48.0, 64.0, 27.1)):
    box('yard_edge_strip', (x1 - x0, 0.12, 0.05), ((x0 + x1) / 2, y, YTOP + 0.01), CYANS, bevel=0)
for k in range(15):   # painted lane lines between work areas
    box('yard_lane', (3.0, 0.22, 0.01), (-40.0 + k * 7.0, -9.5, YTOP + 0.003), PAINT, bevel=0)
for k in range(8):
    box('yard_lane', (0.22, 3.0, 0.01), (6.0, -34.0 + k * 7.0, YTOP + 0.003), PAINT, bevel=0)
text('stencil_yard', 'SY-01', (-4.0, -14.0, YTOP + 0.004), (0, 0, 0), 2.2, PAINT, extrude=0.002)

# ====================================================================== INTEGRATION STAND IS-1 (pad + tower + C-platforms) - ship in Stage
PAD_R = 15.0; TOP = YTOP + 0.3
lathe('is_pad', [(0, YTOP - 0.1), (PAD_R, YTOP - 0.1), (PAD_R, YTOP + 0.1), (PAD_R - 0.5, TOP), (0, TOP)], (SHX, SHY, 0), SINTER, segs=160)
ring('is_pad_strip', PAD_R - 0.9, (SHX, SHY, TOP + 0.01), 0.04, CYAN, w=0.18, segs=160)
for k in range(32):
    a = TAU * k / 32; x, y = SHX + (PAD_R - 0.4) * math.cos(a), SHY + (PAD_R - 0.4) * math.sin(a)
    rbox('is_edge_light', (0.35, 0.6, 0.1), (x, y, TOP + 0.03), GRAPH_S, rot=(0, 0, a), r=0.03, segs=1)
    box('is_edge_lens', (0.2, 0.42, 0.02), (x, y, TOP + 0.09), LAMP if k % 4 else AMBERG, rot=(0, 0, a), bevel=0)
text('stencil_is', 'IS-1', (SHX, SHY - 11.0, TOP + 0.003), (0, 0, 0), 1.8, PAINT, extrude=0.002)
SR = 4.0
UA = math.radians(30); TD = 13.5; TW, TH = 5.0, 46.0
u_t = Vector((math.cos(UA), math.sin(UA), 0)); TX, TY = SHX + u_t.x * TD, SHY + u_t.y * TD
inward = -u_t; tang = Vector((-u_t.y, u_t.x, 0)); rot_u = math.atan2(inward.y, inward.x)
# ---------------------------------------------------------------------- UNDER-CONSTRUCTION STACK (replaces the finished starter ship)
SC = Vector((SHX, SHY, 0))
def shell(name, r0, z0, z1, mat, t=0.14, a0=0.0, a1=None, segs=72, c='Mine'):
    return lathe(name, [(r0 - t, z0), (r0, z0), (r0, z1), (r0 - t, z1), (r0 - t, z0)], (SHX, SHY, 0), mat, segs=segs, a0=a0, a1=a1, smooth=True, c=c)
def frame_ring(name, z, r0=SR, mat=None, c='Mine'):
    return lathe(name, [(r0 - 0.45, z - 0.16), (r0 + 0.05, z - 0.16), (r0 + 0.05, z + 0.16), (r0 - 0.45, z + 0.16), (r0 - 0.45, z - 0.16)], (SHX, SHY, 0), mat or GRAPH, segs=72, smooth=False, c=c)
def stringers(z0, z1, n=24, skip=(), mat=None, ctr=SC, c='Mine'):
    for k in range(n):
        if k in skip: continue
        a = TAU * k / n
        box('stk_stringer', (0.14, 0.26, z1 - z0), (ctr.x + (SR - 0.3) * math.cos(a), ctr.y + (SR - 0.3) * math.sin(a), (z0 + z1) / 2), mat or SATIN, rot=(0, 0, a), bevel=0, c=c)
# launch mount: graphite ring beam on 6 pedestals, stack sits on hold-down clamps
for k in range(6):
    a = TAU * k / 6 + 0.26; p = SC + Vector((math.cos(a), math.sin(a), 0)) * 5.3
    rbox('stk_pedestal', (1.3, 1.3, 2.6), (p.x, p.y, TOP + 1.3), GRAPH, rot=(0, 0, a), r=0.12, segs=2)
    rbox('stk_clamp', (0.7, 0.9, 0.9), tuple(SC + Vector((math.cos(a), math.sin(a), 0)) * 4.4 + Vector((0, 0, TOP + 3.0))), GRAPH_S, rot=(0, 0, a), r=0.08, segs=1)
lathe('stk_mount_ring', [(4.3, TOP + 2.55), (6.0, TOP + 2.55), (6.0, TOP + 3.1), (4.3, TOP + 3.1), (4.3, TOP + 2.55)], (SHX, SHY, 0), GRAPH, segs=72, smooth=False)
ring('stk_mount_strip', 6.02, (SHX, SHY, TOP + 2.8), 0.08, CYAN, w=0.03, segs=72)
# aft skirt + thrust structure + 3 engine bells (installed, nozzles covered by white caps)
Z_AFT = TOP + 3.1
lathe('stk_aft_skirt', [(SR - 0.15, Z_AFT), (SR + 0.25, Z_AFT), (SR, Z_AFT + 2.6), (SR - 0.14, Z_AFT + 2.6), (SR - 0.15, Z_AFT)], (SHX, SHY, 0), WHITE, segs=72)
lathe('stk_thrust_puck', [(0, Z_AFT + 1.6), (SR - 0.3, Z_AFT + 1.6), (SR - 0.3, Z_AFT + 2.0), (0, Z_AFT + 2.3)], (SHX, SHY, 0), GRAPH, segs=48, smooth=False)
for k in range(3):
    a = TAU * k / 3 + 0.5; p = SC + Vector((math.cos(a), math.sin(a), 0)) * 1.7
    lathe('stk_engine_bell', [(0.0, Z_AFT - 1.9), (1.05, Z_AFT - 1.9), (1.0, Z_AFT - 1.7), (0.5, Z_AFT + 0.6), (0.38, Z_AFT + 1.6), (0, Z_AFT + 1.6)], (p.x, p.y, 0), GRAPH_S, segs=32)
    lathe('stk_nozzle_cap', [(0, Z_AFT - 2.0), (1.08, Z_AFT - 2.0), (1.08, Z_AFT - 1.75), (0, Z_AFT - 1.75)], (p.x, p.y, 0), WHITE_S, segs=32, smooth=False)
RH = 5.75; Z1 = Z_AFT + 2.6                       # ring height = tower girt pitch
RZ = [Z1 + RH * i for i in range(4)]             # ring bottoms: 2 closed, 1 open-bay, top edge open
# ring 1 + 2: skinned (ring 2 with two panel bays still open)
shell('stk_ring1', SR, RZ[0], RZ[1], WHITE)
gap2 = [(math.radians(200), math.radians(228)), (math.radians(286), math.radians(306))]
segs2 = [(math.radians(228), math.radians(286)), (math.radians(306), math.radians(560))]
for a0, a1 in segs2: shell('stk_ring2', SR, RZ[1], RZ[2], WHITE, a0=a0, a1=a1, segs=max(8, int(72 * (a1 - a0) / TAU)))
stringers(RZ[1], RZ[2], n=24, skip=[k for k in range(24) if not any(g0 <= (TAU * k / 24 if TAU * k / 24 >= math.radians(200) else TAU * k / 24 + TAU) <= g1 for g0, g1 in gap2)])
# ring 3: frames + stringers up, only some skin panels hung, exposed tank dome inside
for a0, a1 in ((math.radians(20), math.radians(95)), (math.radians(140), math.radians(170)), (math.radians(250), math.radians(300))):
    shell('stk_ring3_panel', SR, RZ[2], RZ[2] + RH * (0.55 if a0 > 2 else 1.0), WHITE, a0=a0, a1=a1, segs=max(6, int(72 * (a1 - a0) / TAU)))
stringers(RZ[2], RZ[3], n=24)
lathe('stk_tank_dome', [(0, RZ[2] + 3.2), (1.8, RZ[2] + 2.9), (3.0, RZ[2] + 2.0), (3.6, RZ[2] + 0.6), (3.62, RZ[2] - 0.2), (0, RZ[2] - 0.2)], (SHX, SHY, 0), WHITE_S, segs=56)
lathe('stk_dome_weld', [(3.0, RZ[2] + 2.0), (3.08, RZ[2] + 2.0), (3.08, RZ[2] + 2.12), (3.0, RZ[2] + 2.12)], (SHX, SHY, 0), SATIN, segs=56, smooth=False)
for z in (RZ[0], RZ[1], RZ[2], RZ[2] + RH / 2, RZ[3]): frame_ring('stk_frame', z)
ring('stk_ring_strip', SR + 0.01, (SHX, SHY, RZ[1] - 0.6), 0.1, CYAN, w=0.02, segs=72)
for k in range(4):    # active weld spots on the open top joint
    a = TAU * k / 4 + 0.7; sphere('stk_weld_lamp', 0.09, (SHX + (SR + 0.06) * math.cos(a), SHY + (SR + 0.06) * math.sin(a), RZ[2] + 0.02), LAMP, sub=2)
# loose panels waiting on the 21 m platform, stencils
text('stencil_stk', 'SN-07 · STACK IN WORK', (SHX + SR * math.cos(-1.9) * 1.003, SHY + SR * math.sin(-1.9) * 1.003, RZ[0] + 2.4), (math.pi / 2, 0, -1.9 + math.pi / 2), 0.42, INK, extrude=0.004)
STACK_TOP = RZ[3]
rbox('ist_plinth', (8.0, 8.0, 0.9), (TX, TY, TOP + 0.3), GRAPH, rot=(0, 0, rot_u), r=0.15, segs=3)
corners = [Vector((TX, TY, 0)) + inward * (TW / 2) * sx + tang * (TW / 2) * sy for sx in (-1, 1) for sy in (-1, 1)]
Z0 = TOP + 0.75
for c in corners:
    rbox('ist_column', (0.75, 0.75, TH), (c.x, c.y, Z0 + TH / 2), WHITE, rot=(0, 0, rot_u), r=0.12, segs=3)
LV = [Z0 + 5.75 * i for i in range(9)]
faces = [(0, 1), (1, 3), (3, 2), (2, 0)]
for zi, z in enumerate(LV):
    for i, j in faces:
        a, b = corners[i] + Vector((0, 0, z)), corners[j] + Vector((0, 0, z))
        beam('ist_girt', a, b, 0.45, 0.45, GRAPH, bevel=0.06)
        if zi < len(LV) - 1:
            a2, b2 = corners[i] + Vector((0, 0, LV[zi + 1])), corners[j] + Vector((0, 0, LV[zi + 1]))
            beam('ist_brace', a, b2, 0.22, 0.22, GRAPH_S, bevel=0.03); beam('ist_brace', b, a2, 0.22, 0.22, GRAPH_S, bevel=0.03)
rbox('ist_core', (2.0, 2.0, TH - 1.0), (TX, TY, Z0 + (TH - 1.0) / 2), WHITE_S, rot=(0, 0, rot_u), r=0.2, segs=3)
box('ist_core_strip', (0.04, 0.2, TH - 4.0), tuple(Vector((TX, TY, Z0 + TH / 2)) + inward * 1.01), CYAN, rot=(0, 0, rot_u), bevel=0)
rbox('ist_cap', (TW + 1.2, TW + 1.2, 1.4), (TX, TY, Z0 + TH + 0.7), WHITE, rot=(0, 0, rot_u), r=0.3, segs=4)
box('ist_cap_strip', (TW + 1.22, TW + 1.22, 0.08), (TX, TY, Z0 + TH + 0.3), CYAN, rot=(0, 0, rot_u), bevel=0)
text('decal_ist', 'IS-1', tuple(Vector((TX, TY, Z0 + TH + 0.85)) + inward * (TW / 2 + 0.61)), (math.pi / 2, 0, rot_u + math.pi / 2), 0.9, INK, extrude=0.01)
rod('ist_mast', (TX, TY, Z0 + TH + 1.4), (TX, TY, Z0 + TH + 6.0), 0.12, SATIN, segs=10)
_gb = grp_begin()   # Beacon_Lights: mast-top beacon + 4 cap-corner obstruction lights, one cluster (scale-blink pivot = cluster centre)
sphere('ist_beacon', 0.3, (TX, TY, Z0 + TH + 6.1), AMBERG, sub=2)
for sx in (-1, 1):
    for sy in (-1, 1):
        sphere('ist_beacon_corner', 0.22, tuple(Vector((TX, TY, Z0 + TH + 1.62)) + inward * (TW / 2 + 0.3) * sx + tang * (TW / 2 + 0.3) * sy), AMBERG, sub=2)
grp_end(_gb, 'Beacon_Lights')
BEACON_C = Vector((TX, TY, Z0 + TH + 1.62))
# top jib crane: swings about the tower axis, holding the next hull ring over the open stack
JZ = Z0 + TH + 1.4
_gj = grp_begin()
beam('ist_jib', Vector((TX, TY, JZ + 0.6)) - inward * 4.0, Vector((TX, TY, JZ + 0.6)) + inward * 16.5, 1.0, 1.2, WHITE, bevel=0.1)
box('ist_jib_strip', (20.5, 0.04, 0.12), tuple(Vector((TX, TY, JZ + 0.05)) + inward * 6.25), CYAN, rot=(0, 0, rot_u), bevel=0)
rbox('ist_jib_cw', (2.4, 2.0, 1.6), tuple(Vector((TX, TY, JZ + 0.4)) - inward * 3.6), GRAPH, rot=(0, 0, rot_u), r=0.15, segs=2)
rbox('ist_slew', (2.6, 2.6, 0.7), (TX, TY, JZ + 0.0), GRAPH_S, rot=(0, 0, rot_u), r=0.12, segs=2)
hk = Vector((TX, TY, JZ)) + inward * TD          # trolley right over the stack axis
rbox('ist_trolley', (1.4, 1.4, 0.7), tuple(hk), GRAPH_S, rot=(0, 0, rot_u), r=0.1, segs=2)
NRZ = STACK_TOP + 4.2                            # next ring hangs 4.2 m above the open top
SPZ = NRZ + RH + 2.2
rod('ist_hoist', tuple(hk), (hk.x, hk.y, SPZ + 0.9), 0.05, SATIN, segs=8)
rbox('ist_hook', (0.6, 0.6, 0.8), (hk.x, hk.y, SPZ + 0.5), LH2B, r=0.1, segs=2)
beam('ist_spreader', Vector((hk.x, hk.y, SPZ)) - tang * 4.2, Vector((hk.x, hk.y, SPZ)) + tang * 4.2, 0.5, 0.6, LH2B, bevel=0.05)
beam('ist_spreader2', Vector((hk.x, hk.y, SPZ)) - inward * 4.2, Vector((hk.x, hk.y, SPZ)) + inward * 4.2, 0.5, 0.6, LH2B, bevel=0.05)
NC = Vector((hk.x, hk.y, 0))
for k in range(4):
    a = TAU * k / 4 + rot_u; e = Vector((math.cos(a), math.sin(a), 0))
    rod('ist_sling', tuple(Vector((hk.x, hk.y, SPZ - 0.3)) + e * 4.0), tuple(NC + e * (SR - 0.2) + Vector((0, 0, NRZ + RH + 0.15))), 0.04, SATIN, segs=6)
    rbox('ist_lug', (0.3, 0.3, 0.4), tuple(NC + e * (SR - 0.2) + Vector((0, 0, NRZ + RH + 0.1))), GRAPH_S, rot=(0, 0, a), r=0.04, segs=1)
lathe('ist_next_ring', [(SR - 0.14, NRZ), (SR, NRZ), (SR, NRZ + RH), (SR - 0.14, NRZ + RH), (SR - 0.14, NRZ)], (hk.x, hk.y, 0), WHITE, segs=72, a0=math.radians(-60), a1=math.radians(250))
for z in (NRZ, NRZ + RH / 2, NRZ + RH):
    lathe('ist_next_frame', [(SR - 0.45, z - 0.16), (SR + 0.05, z - 0.16), (SR + 0.05, z + 0.16), (SR - 0.45, z + 0.16), (SR - 0.45, z - 0.16)], (hk.x, hk.y, 0), GRAPH, segs=72, smooth=False)
stringers(NRZ, NRZ + RH, n=24, ctr=NC)
ring('ist_next_strip', SR + 0.01, (hk.x, hk.y, NRZ + 0.6), 0.1, CYAN, w=0.02, segs=72)
grp_end(_gj, 'Crane_Jib')
# C-shaped work platforms hugging the hull (tower side), handrail on the outer edge
for z in (12.0, 21.0, 30.0):
    z = TOP + z; a0, a1 = UA - math.radians(62), UA + math.radians(62)
    lathe('ist_platform', [(SR + 0.7, z), (SR + 3.2, z), (SR + 3.2, z + 0.3), (SR + 0.7, z + 0.3), (SR + 0.7, z)], (SHX, SHY, 0), GRAPH_S, segs=40, a0=a0, a1=a1, smooth=False)
    lathe('ist_platform_edge', [(SR + 3.15, z - 0.05), (SR + 3.3, z - 0.05), (SR + 3.3, z + 0.05), (SR + 3.15, z + 0.05)], (SHX, SHY, 0), CYANS, segs=40, a0=a0, a1=a1, smooth=False)
    for k in range(9):
        a = a0 + (a1 - a0) * k / 8; p = Vector((SHX + (SR + 3.05) * math.cos(a), SHY + (SR + 3.05) * math.sin(a), z + 0.3))
        rod('rail_post', tuple(p), tuple(p + Vector((0, 0, 1.1))), 0.035, SATIN, segs=8)
    lathe('ist_platform_rail', [(SR + 3.0, z + 1.38), (SR + 3.1, z + 1.38), (SR + 3.1, z + 1.44), (SR + 3.0, z + 1.44)], (SHX, SHY, 0), SATIN, segs=40, a0=a0, a1=a1, smooth=False)
    # cantilever from the tower
    for s in (-1, 1):
        p0 = Vector((TX, TY, z - 0.3)) + inward * (TW / 2) + tang * 1.6 * s
        p1 = Vector((SHX, SHY, z - 0.3)) + (Vector((TX, TY, 0)) - Vector((SHX, SHY, 0))).normalized() * (SR + 3.2) + tang * 1.6 * s
        p1.z = z - 0.1
        beam('ist_cantilever', p0, p1, 0.5, 0.7, WHITE, bevel=0.06)
        beam('ist_knee', Vector((TX, TY, z - 4.0)) + inward * (TW / 2) + tang * 1.6 * s, p0.lerp(p1, 0.6), 0.3, 0.3, GRAPH_S, bevel=0.04)
# propellant + power umbilical mast at the stand edge
UMX, UMY = SHX - 10.5, SHY + 7.0
rbox('is_umb_mast', (1.2, 1.2, 9.0), (UMX, UMY, TOP + 4.5), WHITE, r=0.15, segs=3)
for s, mat in ((-1, LOXB), (1, LH2B)):
    cable('is_umb_hose', (UMX + 0.6, UMY + 0.3 * s, TOP + 8.2), (SHX - SR * 0.78, SHY + SR * 0.6 + 0.3 * s, TOP + 7.0), 0.13, FOIL, sag=0.9, n=20)
    rod('is_umb_qd', (SHX - SR * 0.8 - 0.3, SHY + SR * 0.6 + 0.3 * s, TOP + 7.0), (SHX - SR * 0.8, SHY + SR * 0.6 + 0.3 * s, TOP + 7.0), 0.2, mat, segs=14)
text('decal_umb', 'UMB-1', (UMX, UMY - 0.62, TOP + 6.5), (math.pi / 2, 0, 0), 0.25, INK, extrude=0.003)

# ====================================================================== ASSEMBLY HALL AH-1 (thick shielded white walls, door open to -Y)
WT = 1.2; FRY = HY - HD / 2; BKY = HY + HD / 2; DWd, DHd = 20.0, 20.0
LEAF_W = DWd / 2 + 0.6; LEAF_OPEN = DWd / 2 + LEAF_W / 2 + 0.2; LEAF_CLOSED = LEAF_W / 2 - 0.05   # leaf centre offsets from HX
rbox('ah_wall_back', (HW, WT, HH), (HX, BKY - WT / 2, YTOP + HH / 2), HALLW, r=0.3, segs=3)
for s in (-1, 1):
    rbox('ah_wall_side', (WT, HD, HH), (HX + s * (HW / 2 - WT / 2), HY, YTOP + HH / 2), HALLW, r=0.3, segs=3)
    rbox('ah_pier', ((HW - DWd) / 2, WT, HH), (HX + s * (DWd / 2 + (HW - DWd) / 4), FRY + WT / 2, YTOP + HH / 2), HALLW, r=0.3, segs=3)
    _gd = grp_begin()
    rbox('ah_door_leaf', (LEAF_W, 0.7, DHd + 0.4), (HX + s * LEAF_OPEN, FRY - 0.45, YTOP + (DHd + 0.4) / 2), HALLW, r=0.12, segs=2)
    for k in range(4):
        box('ah_leaf_rib', (LEAF_W - 0.1, 0.12, 0.25), (HX + s * LEAF_OPEN, FRY - 0.85, YTOP + 3.0 + k * 5.0), GRAPH_S, bevel=0.02)
    grp_end(_gd, 'Hall_Door_L' if s < 0 else 'Hall_Door_R')
    box('ah_pier_strip', (0.12, 0.04, HH - 6), (HX + s * (DWd / 2 + 0.25), FRY - 0.02, YTOP + HH / 2), CYAN, bevel=0)
rbox('ah_header', (DWd + 0.2, WT, HH - DHd), (HX, FRY + WT / 2, YTOP + DHd + (HH - DHd) / 2), HALLW, r=0.3, segs=3)
beam('ah_door_track', Vector((HX - DWd / 2 - LEAF_W - 0.8, FRY - 0.9, YTOP + DHd + 0.7)), Vector((HX + DWd / 2 + LEAF_W + 0.8, FRY - 0.9, YTOP + DHd + 0.7)), 0.5, 0.6, GRAPH_S, bevel=0.05)
rbox('ah_roof', (HW + 0.8, HD + 0.8, 1.5), (HX, HY, YTOP + HH + 0.75), WHITE_S, r=0.4, segs=3)
box('ah_roof_strip', (HW + 0.82, HD + 0.82, 0.1), (HX, HY, YTOP + HH + 0.2), CYAN, bevel=0)
box('ah_base_strip', (HW + 0.05, HD + 0.05, 0.1), (HX, HY, YTOP + 1.1), CYANS, bevel=0)
text('decal_ah', 'ASSEMBLY HALL · AH-1', (HX, FRY - 0.02, YTOP + DHd + 2.0), (math.pi / 2, 0, 0), 1.25, INK, extrude=0.01)
text('decal_ah2', 'CRANE 60 T · KEEP CLEAR OF DOOR TRACK', (HX, FRY - 0.02, YTOP + DHd + 0.95), (math.pi / 2, 0, 0), 0.38, INK, extrude=0.005)
# structural ribs (graphite) on the outside walls
for k in range(9):
    x = HX - HW / 2 + 2.0 + k * (HW - 4.0) / 8
    box('ah_rib', (0.5, 0.45, HH - 0.6), (x, BKY + 0.2, YTOP + HH / 2), GRAPH, bevel=0.05)
for s in (-1, 1):
    for k in range(7):
        y = HY - HD / 2 + 1.8 + k * (HD - 3.6) / 6
        box('ah_rib', (0.45, 0.5, HH - 0.6), (HX + s * (HW / 2 + 0.2), y, YTOP + HH / 2), GRAPH, bevel=0.05)
    for zz in (8.0, 16.0):
        box('ah_band', (0.3, HD + 0.2, 0.3), (HX + s * (HW / 2 + 0.1), HY, YTOP + zz), GRAPH_S, bevel=0.03)
# personnel door + small airlock on the left side wall (crew don't use the big door)
PDX = HX - HW / 2 - 1.5; PDY = HY - 6.0
rbox('ah_airlock', (3.0, 3.2, 3.2), (PDX, PDY, YTOP + 1.6), WHITE, r=0.35, segs=3)
rbox('ah_airlock_hatch', (0.14, 1.4, 2.1), (PDX - 1.55, PDY, YTOP + 1.25), GRAPH_S, r=0.25, segs=3)
sphere('ah_airlock_lamp', 0.07, (PDX - 1.6, PDY + 0.9, YTOP + 2.6), CYAN, sub=2)
text('decal_ahal', 'AIRLOCK A2', (PDX - 1.58, PDY, YTOP + 2.75), (math.pi / 2, 0, -math.pi / 2), 0.2, INK, extrude=0.003)
for i in range(8): box('ah_al_grate', (0.05, 2.2, 0.03), (PDX - 1.9 - i * 0.12, PDY, YTOP + 0.02), SATIN, bevel=0)
for s in (-1, 1):
    rbox('ah_al_arch', (0.4, 0.3, 2.6), (PDX - 2.6, PDY + s * 1.25, YTOP + 1.3), WHITE, r=0.08, segs=2)
rbox('ah_al_arch_top', (0.4, 2.8, 0.3), (PDX - 2.6, PDY, YTOP + 2.7), WHITE, r=0.08, segs=2)
box('ah_al_arch_strip', (0.25, 2.2, 0.02), (PDX - 2.6, PDY, YTOP + 2.53), CYAN, bevel=0)
text('decal_ahdo', 'DUST-OFF', (PDX - 2.82, PDY, YTOP + 2.7), (math.pi / 2, 0, -math.pi / 2), 0.16, INK, extrude=0.003)
# roof radiators (the hall's welders / crane drives make heat) - white panels edge-on to the sun
for k in range(4):
    x = HX - 12.0 + k * 8.0
    rod('ah_rad_mast', (x, HY + 4.0, YTOP + HH + 1.5), (x, HY + 4.0, YTOP + HH + 3.0), 0.14, SATIN, segs=10)
    box('ah_radiator', (6.4, 0.1, 3.4), (x, HY + 4.0, YTOP + HH + 4.8), RAD, bevel=0.01)
    for zz in (-1.72, 1.72): rod('ah_rad_manifold', (x - 3.25, HY + 4.0, YTOP + HH + 4.8 + zz), (x + 3.25, HY + 4.0, YTOP + HH + 4.8 + zz), 0.07, GRAPH_S, segs=10)
text('decal_ahrad', 'RAD-H1', (HX - 12.0, HY + 3.93, YTOP + HH + 6.9), (math.pi / 2, 0, 0), 0.35, INK, extrude=0.004)
# interior: sintered floor, work lights, bridge crane, hull barrel on a cradle, engine skirt
box('ah_floor', (HW - 2 * WT, HD - WT, 0.1), (HX, HY + WT / 2, YTOP + 0.05), SINTER, bevel=0)
for i in range(3):
    for j in range(2):
        box('ah_worklight', (3.0, 0.6, 0.15), (HX - 10.0 + i * 10.0, HY - 4.0 + j * 9.0, YTOP + HH - 0.15), LAMP, bevel=0)
CRZ = YTOP + 19.5
for s in (-1, 1):
    beam('ah_crane_rail', Vector((HX + s * (HW / 2 - WT - 0.5), FRY + 1.5, CRZ)), Vector((HX + s * (HW / 2 - WT - 0.5), BKY - 1.5, CRZ)), 0.7, 0.9, GRAPH, bevel=0.06)
CBY = HY + 1.0
beam('ah_crane_bridge', Vector((HX - HW / 2 + WT + 0.6, CBY, CRZ + 1.0)), Vector((HX + HW / 2 - WT - 0.6, CBY, CRZ + 1.0)), 1.6, 1.6, WHITE, bevel=0.12)
box('ah_crane_stripe', (HW - 2 * WT - 2, 0.04, 0.3), (HX, CBY - 0.82, CRZ + 1.0), LH2B, bevel=0)
rbox('ah_crane_trolley', (2.6, 2.4, 1.4), (HX, CBY, CRZ + 0.1), GRAPH_S, r=0.15, segs=2)
for s in (-1, 1):
    rod('ah_crane_rope', (HX + s * 0.6, CBY, CRZ - 0.6), (HX + s * 0.6, CBY, YTOP + 11.6), 0.05, SATIN, segs=8)
beam('ah_spreader', Vector((HX - 4.5, CBY, YTOP + 11.3)), Vector((HX + 4.5, CBY, YTOP + 11.3)), 0.5, 0.6, LH2B, bevel=0.05)
for s in (-1, 1): rod('ah_sling', (HX + s * 4.2, CBY, YTOP + 11.0), (HX + s * 3.0, CBY, YTOP + 9.6), 0.04, SATIN, segs=8)
# hull barrel (axis along y, open end faces the door) on a cradle
BR, BL, BZ = 4.0, 11.0, YTOP + 5.4
hb = lathe('ah_hull_barrel', [(BR - 0.22, -BL / 2), (BR, -BL / 2), (BR, BL / 2), (BR - 0.22, BL / 2), (BR - 0.22, -BL / 2)], (0, 0, 0), WHITE, segs=72)
hb.rotation_euler = (math.pi / 2, 0, 0); hb.location = (HX, CBY, BZ)
for yy in (-BL / 2, -BL / 6, BL / 6, BL / 2):
    r_ = lathe('ah_hull_frame', [(BR - 0.6, -0.15), (BR + 0.04, -0.15), (BR + 0.04, 0.15), (BR - 0.6, 0.15), (BR - 0.6, -0.15)], (0, 0, 0), GRAPH, segs=72)
    r_.rotation_euler = (math.pi / 2, 0, 0); r_.location = (HX, CBY + yy, BZ)
for k in range(12):   # internal stringers (visible through the open end)
    a = TAU * k / 12
    box('ah_stringer', (0.18, BL - 0.3, 0.3), (HX + (BR - 0.35) * math.cos(a), CBY, BZ + (BR - 0.35) * math.sin(a)), SATIN, rot=(0, -a, 0), bevel=0)
for yy in (-3.6, 3.6):
    rbox('ah_cradle', (8.4, 1.2, 1.8), (HX, CBY + yy, YTOP + 0.9), GRAPH, r=0.12, segs=2)
    rbox('ah_cradle_pad', (6.0, 1.3, 0.25), (HX, CBY + yy, YTOP + 1.85), RUBBER, r=0.05, segs=1)
text('decal_hull', 'SEC-03 · LOX TANK', (HX - BR - 0.03, CBY, BZ + 0.6), (math.pi / 2, 0, -math.pi / 2), 0.45, INK, extrude=0.004)
# engine skirt section standing at the back + scaffold
EKX, EKY = HX + 10.0, HY + 7.5
lathe('ah_engine_skirt', [(0, YTOP), (4.0, YTOP), (4.0, YTOP + 2.0), (3.6, YTOP + 6.0), (3.4, YTOP + 6.2), (0, YTOP + 6.2)], (EKX, EKY, 0), WHITE, segs=64)
ring('ah_skirt_band', 3.62, (EKX, EKY, YTOP + 5.6), 0.3, GRAPH, w=0.05, segs=64)
for k in range(4):
    a = TAU * k / 4 + 0.4
    lathe('ah_engine_bell', [(0.0, 0), (1.1, 0), (0.55, 1.6), (0.4, 2.2), (0, 2.2)], (EKX + 2.0 * math.cos(a), EKY + 2.0 * math.sin(a), YTOP + 0.15), GRAPH_S, segs=32) if False else None
for s in (-1, 1):
    for z in (2.0, 4.0, 6.0):
        rbox('ah_scaffold_deck', (1.2, 9.0, 0.15), (EKX + s * 5.0, EKY, YTOP + z), GRAPH_S, r=0.03, segs=1)
    for yy in (-4.2, 4.2):
        rod('ah_scaffold_post', (EKX + s * 5.0, EKY + yy, YTOP), (EKX + s * 5.0, EKY + yy, YTOP + 7.2), 0.06, SATIN, segs=8)
# parts rack along the left wall
for k in range(4):
    rbox('ah_crate', (2.2, 1.6, 1.4), (HX - HW / 2 + WT + 1.6, HY - 8.0 + k * 2.0, YTOP + 0.7), WHITE, r=0.18, segs=3)
    box('ah_crate_strip', (0.02, 1.2, 0.05), (HX - HW / 2 + WT + 0.49, HY - 8.0 + k * 2.0, YTOP + 1.0), CYAN, bevel=0)

# ====================================================================== WELDING BAY W-2 (barrel on turning rolls, robot welders, screens, power unit)
rbox('wb_apron', (20.0, 14.0, 0.12), (WX, WY, YTOP + 0.06), GRAPH, r=0.04, segs=1)
box('wb_apron_strip', (20.02, 14.02, 0.03), (WX, WY, YTOP + 0.1), CYANS, bevel=0)
WB_R, WB_L, WB_Z = 4.0, 9.0, YTOP + 5.1
wb = lathe('wb_barrel', [(WB_R - 0.2, -WB_L / 2), (WB_R, -WB_L / 2), (WB_R, WB_L / 2), (WB_R - 0.2, WB_L / 2), (WB_R - 0.2, -WB_L / 2)], (0, 0, 0), WHITE, segs=72)
wb.rotation_euler = (0, math.pi / 2, 0); wb.location = (WX, WY, WB_Z)
for xx in (-WB_L / 2, 0.0, WB_L / 2):
    r_ = lathe('wb_weld_seam', [(WB_R - 0.05, -0.12), (WB_R + 0.05, -0.12), (WB_R + 0.05, 0.12), (WB_R - 0.05, 0.12)], (0, 0, 0), GRAPH if xx else SATIN, segs=72)
    r_.rotation_euler = (0, math.pi / 2, 0); r_.location = (WX + xx, WY, WB_Z)
for xx in (-3.0, 3.0):
    for s in (-1, 1):
        rbox('wb_roll_stand', (1.2, 1.6, 1.1), (WX + xx, WY + s * 2.6, YTOP + 0.55), GRAPH, r=0.1, segs=2)
        cyl('wb_roller', 0.55, 0.9, (WX + xx, WY + s * 2.6, YTOP + 1.3), RUBBER, rot=(0, math.pi / 2, 0), segs=24, bevel=0.04)
    rbox('wb_roll_beam', (1.0, 6.4, 0.4), (WX + xx, WY, YTOP + 0.2), GRAPH_S, r=0.05, segs=1)
def robot(x, y, face, reach_to):
    lathe('wb_robot_base', [(0, 0), (0.75, 0), (0.7, 0.5), (0.5, 0.9), (0, 0.9)], (x, y, YTOP), GRAPH, segs=28)
    cyl('wb_robot_turret', 0.5, 0.8, (x, y, YTOP + 1.3), WHITE_S, segs=28, bevel=0.06)
    sh = Vector((x, y, YTOP + 1.7)); tgt = Vector(reach_to)
    el = sh.lerp(tgt, 0.5) + Vector((0, 0, 2.6))
    beam('wb_robot_upper', sh, el, 0.55, 0.6, WHITE, bevel=0.12)
    beam('wb_robot_fore', el, tgt + (el - tgt).normalized() * 0.5, 0.4, 0.42, WHITE, bevel=0.1)
    sphere('wb_robot_joint', 0.42, tuple(el), GRAPH_S, sub=2)
    box('wb_robot_strip', (0.03, 0.03, 0.03), tuple(el), CYAN, bevel=0)
    rod('wb_torch', tuple(tgt + (el - tgt).normalized() * 0.55), tuple(tgt + (el - tgt).normalized() * 0.05), 0.08, SATIN, segs=10)
    sphere('wb_arc', 0.11, tuple(tgt), LAMP, sub=2)
    sphere('wb_arc_halo', 0.22, tuple(tgt), CYANS, sub=1)
for s in (-1, 1):
    for xx in (-WB_L / 2, WB_L / 2):
        a = math.radians(35); tgt = (WX + xx, WY + s * (WB_R + 0.05) * math.cos(a), WB_Z + (WB_R + 0.05) * math.sin(a))
        robot(WX + xx + (1.2 if xx < 0 else -1.2), WY + s * 6.2, 0, tgt)
# weld screens (U around the bay, opening toward +x)
for x0, y0, x1, y1 in ((WX - 10.0, WY - 7.0, WX + 4.0, WY - 7.0), (WX - 10.0, WY + 7.0, WX + 4.0, WY + 7.0), (WX - 10.0, WY - 7.0, WX - 10.0, WY + 7.0)):
    L = math.hypot(x1 - x0, y1 - y0); n = max(1, int(L / 3.4))
    for k in range(n):
        t0 = (k + 0.5) / n; px, py = x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0
        ang = math.atan2(y1 - y0, x1 - x0)
        box('wb_screen', (L / n - 0.25, 0.06, 2.4), (px, py, YTOP + 1.5), GRAPH_S, rot=(0, 0, ang), bevel=0.01)
        rod('wb_screen_post', (px + math.cos(ang) * (L / n / 2 - 0.1), py + math.sin(ang) * (L / n / 2 - 0.1), YTOP), (px + math.cos(ang) * (L / n / 2 - 0.1), py + math.sin(ang) * (L / n / 2 - 0.1), YTOP + 2.8), 0.05, SATIN, segs=8)
text('decal_wb', 'WELD BAY W-2 · ARC ZONE', (WX - 3.0, WY - 7.05, YTOP + 2.2), (math.pi / 2, 0, 0), 0.32, INKW, extrude=0.003)
# weld power unit with white radiators
PUX, PUY = WX + 6.5, WY - 8.5
rbox('wb_power', (3.6, 2.4, 1.8), (PUX, PUY, YTOP + 0.9), WHITE, r=0.3, segs=4)
box('wb_power_strip', (2.8, 0.02, 0.06), (PUX, PUY - 1.21, YTOP + 1.5), CYAN, bevel=0)
text('decal_wbp', 'WELD PWR · 400 KW', (PUX, PUY - 1.22, YTOP + 1.15), (math.pi / 2, 0, 0), 0.2, INK, extrude=0.003)
for s in (-1, 1):
    c = Vector((PUX + s * 1.3, PUY, YTOP + 4.2))
    rod('rad_post', (c.x, c.y, YTOP + 1.8), (c.x, c.y, c.z - 1.7), 0.09, SATIN, segs=10)
    box('wb_radiator', (0.08, 2.6, 3.4), tuple(c), RAD, bevel=0.01)
    for zz in (-1.72, 1.72): rod('rad_manifold', (c.x, c.y - 1.3, c.z + zz), (c.x, c.y + 1.3, c.z + zz), 0.06, GRAPH_S, segs=10)
for s in (-1, 1):
    cable('wb_cable', (PUX - 1.8, PUY + 0.4 * s, YTOP + 0.3), (WX - WB_L / 2 + 1.2, WY + s * 6.2, YTOP + 0.3), 0.06, RUBBER, sag=-0.05, n=12)

# ====================================================================== FOUNDRY FAB-01 (furnace columns, LOX/LH2 spheres, pipe rack, radiators, furnace F-1, slag hopper)
def column(x, y, r, h, tag_=None, c='Mine', sg=48):
    lathe('rf_column', [(0, YTOP), (r + 0.45, YTOP), (r + 0.45, YTOP + 0.7), (r, YTOP + 0.8), (r, YTOP + h), (r * 0.75, YTOP + h + r * 0.45), (0, YTOP + h + r * 0.6)], (x, y, 0), WHITE, segs=sg, c=c)
    for z in range(4, int(h), 4): ring('rf_col_band', r + 0.03, (x, y, YTOP + z), 0.25, GRAPH, w=0.05, segs=sg, c=c)
    ring('rf_col_glow', r + 0.035, (x, y, YTOP + 2.2), 0.08, CYAN, w=0.03, segs=sg, c=c)
    for z in range(6, int(h) - 1, 6):
        lathe('rf_col_deck', [(r + 0.1, YTOP + z), (r + 1.3, YTOP + z), (r + 1.3, YTOP + z + 0.15), (r + 0.1, YTOP + z + 0.15)], (x, y, 0), GRAPH_S, segs=min(40, sg), smooth=False, c=c)
        ring('rf_col_rail', r + 1.25, (x, y, YTOP + z + 1.2), 0.05, SATIN, w=0.04, segs=min(40, sg), c=c)
    a = -math.pi / 2 - 0.5; lx, ly = x + (r + 0.35) * math.cos(a), y + (r + 0.35) * math.sin(a)
    for s in (-0.25, 0.25):
        rod('rf_ladder', (lx + s * math.sin(a), ly - s * math.cos(a), YTOP + 0.8), (lx + s * math.sin(a), ly - s * math.cos(a), YTOP + h), 0.03, SATIN, segs=6, c=c)
    if tag_: text('decal_rf', tag_, (x, y - r - 0.02, YTOP + 3.2), (math.pi / 2, 0, 0), 0.5, INK, extrude=0.004, c=c)
column(RFX - 6.0, RFY + 6.0, 1.6, 22.0, 'FAB-01')
column(RFX - 1.5, RFY + 8.0, 1.3, 17.0)
column(RFX + 3.0, RFY + 5.5, 1.1, 13.0)
def sph_tank(x, y, r, band, tag_):
    for k in range(6):
        a = TAU * k / 6
        rod('rf_tank_leg', (x + r * 0.8 * math.cos(a), y + r * 0.8 * math.sin(a), YTOP), (x + r * 0.95 * math.cos(a), y + r * 0.95 * math.sin(a), YTOP + r + 0.6), 0.16, GRAPH_S, segs=12)
    sphere('rf_tank', r, (x, y, YTOP + r + 1.2), WHITE_S, sub=4)
    ring('rf_tank_band', r + 0.02, (x, y, YTOP + r + 1.2), 0.45, band, w=0.05, segs=64)
    ring('rf_tank_glow', r + 0.025, (x, y, YTOP + r + 0.6), 0.07, CYAN, w=0.02, segs=64)
    text('decal_tank', tag_, (x, y - r - 0.06, YTOP + r + 1.95), (math.pi / 2, 0, 0), 0.55, INK, extrude=0.004)
sph_tank(RFX + 7.0, RFY - 7.0, 3.6, LOXB, 'LOX-T1')
sph_tank(RFX - 2.0, RFY - 8.0, 3.2, LH2B, 'LH2-T2')
# furnace F-1 (makes heat) + radiator bank
rbox('rf_reactor', (6.0, 4.0, 4.4), (RFX + 9.5, RFY + 6.0, YTOP + 2.2), WHITE, r=0.5, segs=4)
rbox('rf_reactor_band', (6.1, 4.1, 0.3), (RFX + 9.5, RFY + 6.0, YTOP + 3.4), GRAPH, r=0.08, segs=2)
box('rf_reactor_strip', (5.0, 0.02, 0.08), (RFX + 9.5, RFY + 3.99, YTOP + 1.2), CYAN, bevel=0)
text('decal_rfr', 'FURNACE F-1 · HULL STOCK', (RFX + 9.5, RFY + 3.97, YTOP + 2.5), (math.pi / 2, 0, 0), 0.28, INK, extrude=0.003)
for k in range(5):
    x = RFX + 4.0 + k * 2.6
    for s in (-1, 1): rod('rf_rad_post', (x, RFY + 14.0 + s * 3.6, YTOP), (x, RFY + 14.0 + s * 3.6, YTOP + 2.0), 0.1, SATIN, segs=10)
    box('rf_radiator', (0.1, 8.0, 5.0), (x, RFY + 14.0, YTOP + 4.6), RAD, bevel=0.01)
    for zz in (-2.52, 2.52): rod('rf_rad_manifold', (x, RFY + 10.0, YTOP + 4.6 + zz), (x, RFY + 18.0, YTOP + 4.6 + zz), 0.07, GRAPH_S, segs=10)
text('decal_rfrad', 'RAD-F1', (RFX + 3.92, RFY + 14.0, YTOP + 7.4), (math.pi / 2, 0, -math.pi / 2), 0.4, INK, extrude=0.004)
# pipe rack
PRY = RFY - 1.0
for k in range(7):
    x = RFX - 10.0 + k * 3.5
    for s in (-1, 1): rod('rf_rack_post', (x, PRY + s * 1.1, YTOP), (x, PRY + s * 1.1, YTOP + 5.2), 0.12, GRAPH, segs=10)
    for z in (3.4, 5.2): beam('rf_rack_beam', Vector((x, PRY - 1.3, YTOP + z)), Vector((x, PRY + 1.3, YTOP + z)), 0.2, 0.25, GRAPH_S, bevel=0.02)
for i, (dy, z, r, m) in enumerate(((-0.8, 3.65, 0.18, LOXB), (-0.3, 3.65, 0.18, LH2B), (0.3, 3.65, 0.24, FOIL), (0.8, 3.65, 0.14, SATIN), (-0.5, 5.45, 0.2, FOIL), (0.5, 5.45, 0.16, SATIN))):
    rod('rf_pipe', (RFX - 10.4, PRY + dy, YTOP + z), (RFX + 11.4, PRY + dy, YTOP + z), r, m, segs=14)
# regolith hopper + conveyor from a raw-feed pile
HPX, HPY = RFX - 14.0, RFY - 10.0
for k in range(4):
    a = TAU * k / 4 + math.pi / 4
    rod('rf_hopper_leg', (HPX + 2.2 * math.cos(a), HPY + 2.2 * math.sin(a), YTOP), (HPX + 2.0 * math.cos(a), HPY + 2.0 * math.sin(a), YTOP + 5.0), 0.14, GRAPH_S, segs=10)
lathe('rf_hopper', [(0.5, YTOP + 4.6), (0.6, YTOP + 4.6), (2.8, YTOP + 7.4), (2.8, YTOP + 8.4), (2.6, YTOP + 8.4), (2.6, YTOP + 7.45), (0.5, YTOP + 4.7)], (HPX, HPY, 0), WHITE, segs=40)
ring('rf_hopper_glow', 2.81, (HPX, HPY, YTOP + 8.0), 0.08, CYAN, w=0.03, segs=40)
text('decal_hop', 'FEED H-1', (HPX, HPY - 2.83, YTOP + 7.9), (math.pi / 2, 0, 0), 0.3, INK, extrude=0.003)
mound('rf_feed_pile', HPX - 9.0, HPY - 9.0, 2.0, 1.6, 2.6, 4.0, REGO, seed=17)
c0_ = Vector((HPX - 7.0, HPY - 7.0, YTOP + 0.6)); c1_ = Vector((HPX - 1.2, HPY - 1.2, YTOP + 8.6))
beam('rf_conveyor', c0_, c1_, 1.1, 0.35, GRAPH_S, bevel=0.04)
beam('rf_conveyor_belt', c0_ + Vector((0, 0, 0.2)), c1_ + Vector((0, 0, 0.2)), 0.9, 0.05, RUBBER, bevel=0)
for t in (0.3, 0.6):
    p = c0_.lerp(c1_, t); rod('rf_conv_leg', (p.x, p.y, YTOP), (p.x, p.y, p.z - 0.15), 0.1, SATIN, segs=8)
# propellant transfer line (LOX + LH2) on low stanchions: tank farm -> umbilical mast UMB-1
route = [Vector((RFX - 5.0, RFY - 4.0, 0)), Vector((36.0, -6.0, 0)), Vector((36.0, 16.0, 0)), Vector((UMX + 1.0, UMY + 8.0, 0)), Vector((UMX, UMY + 0.8, 0))]
for a, b in zip(route, route[1:]):
    L = (b - a).length; n = max(1, int(L / 4.0)); ang = math.atan2(b.y - a.y, b.x - a.x)
    for i in range(n + 1):
        p = a.lerp(b, i / n)
        rod('pl_post', (p.x, p.y, YTOP), (p.x, p.y, YTOP + 0.8), 0.05, GRAPH_S, segs=8)
        box('pl_saddle', (0.3, 0.7, 0.08), (p.x, p.y, YTOP + 0.8), SATIN, rot=(0, 0, ang), bevel=0.01)
    for dy, m in ((-0.18, LOXB), (0.18, LH2B)):
        o = Vector((-math.sin(ang), math.cos(ang), 0)) * dy
        rod('pl_pipe', (a.x + o.x, a.y + o.y, YTOP + 0.95), (b.x + o.x, b.y + o.y, YTOP + 0.95), 0.11, FOIL, segs=10)
        rod('pl_band', tuple(a.lerp(b, 0.5) + o + Vector((0, 0, YTOP + 0.95)) - (b - a).normalized() * 0.3), tuple(a.lerp(b, 0.5) + o + Vector((0, 0, YTOP + 0.95)) + (b - a).normalized() * 0.3), 0.12, m, segs=10)

# ====================================================================== YARD CONTROL YC-1 (above ground on legs, airlock + suitports + dust-off)
DH = 2.4; DW, DL = 13.0, 7.0
for ix in range(3):
    for iy in (-1, 1):
        x = CSX - DW / 2 + 1.2 + ix * (DW - 2.4) / 2; y = CSY + iy * (DL / 2 - 0.9)
        lathe('st_foot', [(0, 0), (0.8, 0), (0.7, 0.25), (0, 0.3)], (x, y, YTOP - 0.02), GRAPH, segs=24)
        rod('st_leg', (x, y, YTOP + 0.2), (x, y, DH - 0.2), 0.22, WHITE_S, segs=20)
        ring('st_leg_glow', 0.225, (x, y, YTOP + 1.1), 0.06, CYAN, w=0.03, segs=24)
rbox('st_deck', (DW, DL, 0.4), (CSX, CSY, DH), GRAPH, r=0.08, segs=2)
box('st_deck_strip', (DW + 0.02, DL + 0.02, 0.06), (CSX, CSY, DH - 0.12), CYANS, bevel=0)
dz = DH + 0.2
handrail((CSX - DW / 2 + 0.2, CSY + DL / 2 - 0.2, dz), (CSX + DW / 2 - 0.2, CSY + DL / 2 - 0.2, dz), n=8)
handrail((CSX - DW / 2 + 0.2, CSY - DL / 2 + 0.2, dz), (CSX - DW / 2 + 0.2, CSY + DL / 2 - 0.2, dz), n=4)
handrail((CSX + DW / 2 - 0.2, CSY - DL / 2 + 0.2, dz), (CSX + DW / 2 - 0.2, CSY + DL / 2 - 0.2, dz), n=4)
handrail((CSX - DW / 2 + 0.2, CSY - DL / 2 + 0.2, dz), (CSX + 1.0, CSY - DL / 2 + 0.2, dz), n=5)
MR, ML, MZ = 2.1, 9.0, DH + 0.2 + 2.3
cyl('st_module', MR, ML, (CSX - 1.0, CSY + 1.0, MZ), WHITE, rot=(0, math.pi / 2, 0), segs=64, bevel=0.06)
for ex in (-1, 1):
    cyl('st_endcap', MR + 0.12, 0.35, (CSX - 1.0 + ex * (ML / 2 - 0.1), CSY + 1.0, MZ), GRAPH, rot=(0, math.pi / 2, 0), segs=64, bevel=0.06)
for xx in (-2.6, 0.0, 2.6):
    cyl('st_hoop', MR + 0.05, 0.22, (CSX - 1.0 + xx, CSY + 1.0, MZ), GRAPH, rot=(0, math.pi / 2, 0), segs=64, bevel=0.03)
for xx in (-3.0, 3.0): rbox('st_saddle', (0.7, 3.2, 1.0), (CSX - 1.0 + xx, CSY + 1.0, DH + 0.7), GRAPH_S, r=0.1, segs=2)
box('st_mod_strip', (ML - 1.0, 0.03, 0.08), (CSX - 1.0, CSY + 1.0 - MR - 0.005, MZ - 0.6), CYAN, bevel=0)
for k in range(4):
    px = CSX - 1.0 - 1.65 + k * 1.1; p = (px, CSY + 1.0 - MR * math.cos(0.32) - 0.02, MZ + MR * math.sin(0.32))
    rbox('st_port_frame', (0.75, 0.22, 0.55), p, GRAPH_S, rot=(-0.32, 0, 0), r=0.1, segs=2)
    rbox('st_port', (0.55, 0.24, 0.36), (p[0], p[1] - 0.02, p[2]), GLASS, rot=(-0.32, 0, 0), r=0.08, segs=2)
text('decal_mod', 'YARD CONTROL · YC-1', (CSX - 1.0, CSY + 1.0 - MR * math.cos(-0.28) - 0.03, MZ + MR * math.sin(-0.28)), (math.pi / 2 - 0.28, 0, 0), 0.3, INK, extrude=0.004)
rod('st_rad_mast', (CSX - 1.0, CSY + 1.0, MZ + MR - 0.05), (CSX - 1.0, CSY + 1.0, MZ + MR + 1.4), 0.1, SATIN, segs=10)
box('st_radiator', (6.2, 0.08, 2.6), (CSX - 1.0, CSY + 1.0, MZ + MR + 2.75), RAD, bevel=0.01)
for zz in (-1.32, 1.32): rod('st_rad_manifold', (CSX - 4.15, CSY + 1.0, MZ + MR + 2.75 + zz), (CSX + 2.15, CSY + 1.0, MZ + MR + 2.75 + zz), 0.06, GRAPH_S, segs=12)
rod('st_mast', (CSX - 4.6, CSY + 1.6, MZ + MR), (CSX - 4.6, CSY + 1.6, MZ + MR + 4.5), 0.08, SATIN, segs=10)
sphere('st_mast_tip', 0.12, (CSX - 4.6, CSY + 1.6, MZ + MR + 4.55), CYAN, sub=2)
AX = CSX + 4.6; FY = CSY - 1.3 - 1.41
rbox('airlock_body', (2.8, 2.8, 2.9), (AX, CSY - 1.3, DH + 0.2 + 1.45), WHITE, r=0.4, segs=4)
rbox('airlock_band', (2.9, 2.9, 0.18), (AX, CSY - 1.3, DH + 0.2 + 2.4), GRAPH, r=0.05, segs=2)
rbox('hatch_frame', (1.6, 0.14, 2.25), (AX, FY - 0.04, DH + 0.2 + 1.2), GRAPH_S, r=0.3, segs=5)
rbox('hatch_door', (1.3, 0.1, 1.95), (AX, FY - 0.1, DH + 0.2 + 1.2), WHITE_S, r=0.26, segs=5)
HZ = DH + 0.2 + 1.05
cyl('hatch_port', 0.17, 0.04, (AX, FY - 0.16, HZ + 0.65), GLASS, rot=(math.pi / 2, 0, 0), segs=24)
whl = [(AX + 0.26 * math.cos(TAU * k / 24), FY - 0.24, HZ + 0.26 * math.sin(TAU * k / 24)) for k in range(25)]
curve_tube('hatch_wheel', whl, 0.022, SATIN, res=2)
sphere('hatch_lamp', 0.06, (AX + 0.95, FY - 0.08, DH + 2.6), CYAN, sub=2)
for s in (-1, 1): rod('grab_rail', (AX + s * 1.1, FY - 0.24, DH + 0.7), (AX + s * 1.1, FY - 0.24, DH + 2.3), 0.028, SATIN, segs=10)
text('decal_airlock', 'AIRLOCK A1', (AX, FY - 0.03, DH + 2.75), (math.pi / 2, 0, 0), 0.18, INK, extrude=0.003)
for k in range(2):
    y = CSY - 1.3 - 0.6 + k * 1.2; x = AX + 1.41; zz = DH + 1.55
    cyl('suitport_ring', 0.42, 0.14, (x + 0.05, y, zz), GRAPH_S, rot=(0, math.pi / 2, 0), segs=32)
    cyl('suitport_hatch', 0.34, 0.1, (x + 0.1, y, zz), WHITE_S, rot=(0, math.pi / 2, 0), segs=32)
text('decal_suitport', 'SUITPORT', (AX + 1.42, CSY - 1.3, DH + 2.35), (math.pi / 2, 0, math.pi / 2), 0.15, INK, extrude=0.003)
PZ = DH + 0.2
for i in range(8): box('porch_grate', (2.8, 0.05, 0.03), (AX, FY - 0.25 - i * 0.12, PZ + 0.015), SATIN, bevel=0)
AYa = FY - 0.75
for s in (-1, 1):
    rbox('arch_post', (0.3, 0.45, 2.7), (AX + s * 1.5, AYa, PZ + 1.35), WHITE, r=0.1, segs=3)
    box('arch_post_strip', (0.02, 0.32, 2.0), (AX + s * 1.34, AYa, PZ + 1.2), CYANS, bevel=0)
    rbox('boot_brush', (0.45, 0.7, 0.2), (AX + s * 0.8, AYa - 0.1, PZ + 0.1), RUBBER, r=0.05, segs=2)
rbox('arch_top', (3.3, 0.45, 0.34), (AX, AYa, PZ + 2.85), WHITE, r=0.12, segs=3)
box('arch_strip', (2.8, 0.28, 0.02), (AX, AYa, PZ + 2.67), CYAN, bevel=0)
text('decal_arch', 'DUST-OFF', (AX, AYa - 0.23, PZ + 2.85), (math.pi / 2, 0, 0), 0.18, INK, extrude=0.003)
s0 = Vector((CSX + 1.6, CSY - DL / 2, DH + 0.2)); s1 = Vector((CSX + 1.6, CSY - DL / 2 - 4.2, YTOP + 0.05))
beam('st_stair', s0 + Vector((0, 0, -0.15)), s1 + Vector((0, 0, 0.05)), 2.2, 0.25, GRAPH_S, bevel=0.03, up=Vector((1, 0, 0)))
for k in range(13):
    p = s0.lerp(s1, (k + 0.5) / 13); box('st_tread', (2.0, 0.28, 0.05), (p.x, p.y, p.z + 0.02), SATIN, bevel=0)
for s in (-1, 1): handrail(s0 + Vector((s * 1.05, 0, 0)), s1 + Vector((s * 1.05, 0, 0)), h=1.0, n=4)

# ====================================================================== POWER: solar masts + distant fission plant behind a berm
SUN = Vector((-0.55, -0.6, 0.58)).normalized()
def _cell():
    m = bpy.data.materials.new('SY_SolarCell'); nt, b = _nodes(m)
    b.inputs['Base Color'].default_value = hexc('#152a4a'); b.inputs['Metallic'].default_value = 0.4; b.inputs['Roughness'].default_value = 0.18
    b.inputs['Coat Weight'].default_value = 0.8; m.diffuse_color = hexc('#152a4a'); return m
M_cell = _cell()
def solar_mast(x, y, h=16.0, tag='SOL-1'):
    g = YTOP
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
SOL = [(-44.0, -30.0, 17.0, 'SOL-1'), (-44.0, -16.0, 15.0, 'SOL-2')]
for x, y, h, t in SOL: solar_mast(x, y, h, t)
JX, JY = -44.0, -4.0
rbox('pwr_junction', (1.4, 0.9, 1.7), (JX, JY, YTOP + 0.85), WHITE, r=0.14, segs=3)
box('pwr_junction_strip', (1.0, 0.02, 0.06), (JX, JY - 0.46, YTOP + 1.45), CYAN, bevel=0)
text('decal_pwr', 'PWR-Y1', (JX, JY - 0.46, YTOP + 1.15), (math.pi / 2, 0, 0), 0.16, INK, extrude=0.003)
cable('sol_feed1', (-44.0, -30.45, YTOP + 0.5), (JX, JY - 0.4, YTOP + 0.4), 0.04, RUBBER, sag=-0.1, n=16)
cable('jx_feed_hall', (JX + 0.7, JY, YTOP + 1.0), (HX - HW / 2 - 0.1, HY - 10.0, YTOP + 2.0), 0.07, GRAPH_S, sag=0.4)
mound('reactor_berm', RXr + 8.0, RYr - 9.0, 11.0, 1.4, 5.2, 5.0, REGO, c='Stage', seed=31)
lathe('reactor_vessel', [(0, 0), (3.0, 0), (3.0, 5.4), (2.3, 6.3), (0, 6.5)], (RXr, RYr, gz(RXr, RYr) - 0.1), WHITE, segs=48, c='Stage')
ring('reactor_band', 3.02, (RXr, RYr, 4.0), 0.24, GRAPH, w=0.06, segs=48, c='Stage')
for s in (-1, 1):
    box('reactor_radiator', (10.0, 0.1, 7.0), (RXr + s * 8.5, RYr + 0.5, 6.0), RAD, rot=(0, 0, s * 0.15), bevel=0.01, c='Stage')
sphere('reactor_beacon', 0.35, (RXr, RYr, 6.8), AMBERG, sub=2, c='Stage')
route = [Vector((RXr + 4.0, RYr - 4.0, 0)), Vector((RXr + 20.0, RYr - 14.0, 0)), Vector((-56.0, 14.0, 0)), Vector((-49.0, -2.0, 0)), Vector((JX - 0.8, JY, 0))]
posts = []
for a, b in zip(route, route[1:]):
    L = (b - a).length; n = max(1, int(L / 6.0))
    for i in range(n): posts.append(a.lerp(b, i / n))
posts.append(route[-1])
for p in posts:
    inyard = abs(p.x - 8.0) < 56 and abs(p.y + 6.0) < 33
    cc = 'Stage' if p.y > 30 or p.x < -50 else 'Mine'; g = YTOP if inyard else gz(p.x, p.y)
    rod('cable_post', (p.x, p.y, g - 0.05), (p.x, p.y, g + 0.9), 0.05, GRAPH_S, segs=8, c=cc)
for a, b in zip(posts, posts[1:]):
    cc = 'Stage' if a.y > 30 or a.x < -50 else 'Mine'
    ga = YTOP if (abs(a.x - 8.0) < 56 and abs(a.y + 6.0) < 33) else gz(a.x, a.y); gb = YTOP if (abs(b.x - 8.0) < 56 and abs(b.y + 6.0) < 33) else gz(b.x, b.y)
    cable('power_cable', (a.x, a.y, ga + 0.95), (b.x, b.y, gb + 0.95), 0.05, RUBBER, sag=0.3, n=10, c=cc)


# ====================================================================== UPGRADE TIERS (collection 'Tiers': final positions, hidden by default in game)
def lattice_tower(nm, cx, cy, w, h, pitch, rot, c=TC, braces=True, col_w=0.6):
    u = Vector((math.cos(rot), math.sin(rot), 0)); v = Vector((-u.y, u.x, 0))
    cs = [Vector((cx, cy, 0)) + u * (w / 2) * sx + v * (w / 2) * sy for sx in (-1, 1) for sy in (-1, 1)]
    for p in cs: box(nm + '_col', (col_w, col_w, h), (p.x, p.y, YTOP + h / 2), WHITE, rot=(0, 0, rot), bevel=0, c=c)
    lv = [YTOP + pitch * i for i in range(1, int(h / pitch) + 1)]
    for zi, z in enumerate(lv):
        for i, j in ((0, 1), (1, 3), (3, 2), (2, 0)):
            beam(nm + '_girt', cs[i] + Vector((0, 0, z)), cs[j] + Vector((0, 0, z)), 0.35, 0.35, GRAPH, bevel=0, c=c)
            if braces and (i, j) in ((0, 1), (3, 2)):
                beam(nm + '_brace', cs[i] + Vector((0, 0, z - pitch)), cs[j] + Vector((0, 0, z)), 0.2, 0.2, GRAPH_S, bevel=0, c=c)
    return cs
# Tier_03 - second jib crane (free-standing yard crane between the hall door and W-2)
_t = grp_begin()
C2X, C2Y, C2H = -1.0, -6.0, 30.0
rbox('t3_crane_base', (4.4, 4.4, 1.2), (C2X, C2Y, YTOP + 0.6), GRAPH, r=0.1, segs=1, c=TC)
lattice_tower('t3_mast', C2X, C2Y, 2.0, C2H, 5.0, 0.0)
ja = math.atan2(-0.6, -1.0); ju = Vector((math.cos(ja), math.sin(ja), 0))
rbox('t3_slew_cab', (2.6, 2.6, 2.0), (C2X, C2Y, YTOP + C2H + 1.0), WHITE, rot=(0, 0, ja), r=0.15, segs=1, c=TC)
beam('t3_jib', Vector((C2X, C2Y, YTOP + C2H + 2.4)) - ju * 7.0, Vector((C2X, C2Y, YTOP + C2H + 2.4)) + ju * 22.0, 0.9, 1.1, WHITE, bevel=0, c=TC)
rbox('t3_cw', (2.2, 1.8, 1.6), tuple(Vector((C2X, C2Y, YTOP + C2H + 1.4)) - ju * 6.0), GRAPH, rot=(0, 0, ja), r=0.1, segs=1, c=TC)
th = Vector((C2X, C2Y, YTOP + C2H + 1.8)) + ju * 16.0
rbox('t3_trolley', (1.2, 1.2, 0.6), tuple(th), GRAPH_S, rot=(0, 0, ja), r=0.08, segs=1, c=TC)
rod('t3_hoist', tuple(th), tuple(th - Vector((0, 0, 12.0))), 0.05, SATIN, segs=6, c=TC)
rbox('t3_hook', (0.6, 0.6, 0.8), tuple(th - Vector((0, 0, 12.4))), LH2B, r=0.08, segs=1, c=TC)
grp_end(_t, 'Tier_03')
# Tier_05 - second FAB-01 furnace column (tied into the pipe rack); x = RFX-8.5 keeps it within one frame_w (55 m) of Cam_Target
_t = grp_begin()
T5X = RFX - 8.5
column(T5X, RFY + 14.0, 1.5, 20.0, 'FURNACE 2', c=TC, sg=32)
rod('t5_feed', (T5X, RFY + 12.3, YTOP + 3.65), (T5X, PRY + 1.2, YTOP + 3.65), 0.2, SATIN, segs=10, c=TC)
for t_ in (0.35, 0.7):
    p_ = Vector((T5X, RFY + 12.3 + (PRY + 1.2 - RFY - 12.3) * t_, 0)); rod('t5_feed_post', (p_.x, p_.y, YTOP), (p_.x, p_.y, YTOP + 3.45), 0.1, GRAPH_S, segs=8, c=TC)
grp_end(_t, 'Tier_05')
# Tier_08 - welding bay extension on the assembly hall (annex on the +x wall, own door + roof radiators)
_t = grp_begin()
AXx0, AXx1, AXy0, AXy1, AXh = HX + HW / 2 + 0.4, HX + HW / 2 + 6.0, HY - 11.0, HY + 9.0, 13.0
rbox('t8_annex', (AXx1 - AXx0, AXy1 - AXy0, AXh), ((AXx0 + AXx1) / 2, (AXy0 + AXy1) / 2, YTOP + AXh / 2), HALLW, r=0.25, segs=2, c=TC)
rbox('t8_door', (4.2, 0.4, 6.0), ((AXx0 + AXx1) / 2, AXy0 - 0.15, YTOP + 3.0), GRAPH_S, r=0.08, segs=1, c=TC)
for k in range(5):
    box('t8_rib', (0.4, 0.4, AXh - 0.4), (AXx1 + 0.15, AXy0 + 1.5 + k * (AXy1 - AXy0 - 3.0) / 4, YTOP + AXh / 2), GRAPH, bevel=0, c=TC)
for k in range(2):
    y_ = AXy0 + 5.0 + k * 10.0
    rod('t8_rad_mast', ((AXx0 + AXx1) / 2, y_, YTOP + AXh), ((AXx0 + AXx1) / 2, y_, YTOP + AXh + 1.2), 0.12, SATIN, segs=8, c=TC)
    box('t8_radiator', (0.1, 6.0, 2.8), ((AXx0 + AXx1) / 2, y_, YTOP + AXh + 2.6), RAD, bevel=0, c=TC)
box('t8_strip', (0.04, AXy1 - AXy0 - 1.0, 0.1), (AXx1 + 0.37, (AXy0 + AXy1) / 2, YTOP + 1.1), CYAN, bevel=0, c=TC)
grp_end(_t, 'Tier_08')
# Tier_12 - bigger stand: second service tower opposite IS-1 with 2 work platforms + umbilical mast UMB-2
_t = grp_begin()
T2a = UA + math.pi; T2X, T2Y = SHX + math.cos(T2a) * TD, SHY + math.sin(T2a) * TD
rbox('t12_plinth', (6.0, 6.0, 0.8), (T2X, T2Y, TOP + 0.3), GRAPH, rot=(0, 0, T2a), r=0.1, segs=1, c=TC)
lattice_tower('t12_tower', T2X, T2Y, 4.0, 32.0, 5.75, T2a)
rbox('t12_cap', (5.0, 5.0, 1.0), (T2X, T2Y, YTOP + 32.5), WHITE, rot=(0, 0, T2a), r=0.15, segs=1, c=TC)
for z in (12.0, 21.0):
    z = TOP + z; a0, a1 = T2a - math.radians(55), T2a + math.radians(55)
    lathe('t12_platform', [(SR + 0.7, z), (SR + 3.0, z), (SR + 3.0, z + 0.3), (SR + 0.7, z + 0.3), (SR + 0.7, z)], (SHX, SHY, 0), GRAPH_S, segs=16, a0=a0, a1=a1, smooth=False, c=TC)
    p0 = Vector((T2X, T2Y, z - 0.3)) - Vector((math.cos(T2a), math.sin(T2a), 0)) * 2.0; p1 = Vector((SHX, SHY, z - 0.3)) + Vector((math.cos(T2a), math.sin(T2a), 0)) * (SR + 3.0)
    beam('t12_cantilever', p0, p1, 0.6, 0.7, WHITE, bevel=0, c=TC)
U2X, U2Y = SHX + 4.0, SHY - 10.5
rbox('t12_umb_mast', (1.2, 1.2, 10.0), (U2X, U2Y, TOP + 5.0), WHITE, r=0.12, segs=1, c=TC)
for s_ in (-1, 1):
    cable('t12_umb_hose', (U2X - 0.3 * s_, U2Y + 0.6, TOP + 9.2), (SHX + 1.4 + 0.3 * s_, SHY - SR * 0.93, TOP + 8.0), 0.13, FOIL, sag=0.9, n=12, c=TC)
grp_end(_t, 'Tier_12')
# Tier_20 - tall Mars-class stand (pad + 72 m tower + jib) on a new sintered pad north of IS-1, past the yard edge
#           (within one frame_w of Cam_Target; 13 m pad with a skirt down to the bare ground so it sits on the regolith)
_t = grp_begin()
MSX, MSY = 6.0, 35.5
lathe('t20_pad', [(0, -0.35), (13.0, -0.35), (13.0, YTOP), (12.5, YTOP + 0.4), (0, YTOP + 0.4)], (MSX, MSY, 0), SINTER, segs=48, smooth=False, c=TC)
MTa = math.radians(45); MTX, MTY = MSX + math.cos(MTa) * 9.0, MSY + math.sin(MTa) * 9.0
lattice_tower('t20_tower', MTX, MTY, 5.0, 72.0, 8.0, MTa, col_w=0.8)
rbox('t20_cap', (6.4, 6.4, 1.4), (MTX, MTY, YTOP + 72.7), WHITE, rot=(0, 0, MTa), r=0.15, segs=1, c=TC)
mu = -Vector((math.cos(MTa), math.sin(MTa), 0))
beam('t20_jib', Vector((MTX, MTY, YTOP + 74.0)) - mu * 5.0, Vector((MTX, MTY, YTOP + 74.0)) + mu * 12.0, 1.1, 1.3, WHITE, bevel=0, c=TC)
for z in (20.0, 36.0, 52.0):
    a0, a1 = MTa - math.radians(60), MTa + math.radians(60)
    lathe('t20_platform', [(5.4, YTOP + z), (7.6, YTOP + z), (7.6, YTOP + z + 0.3), (5.4, YTOP + z + 0.3), (5.4, YTOP + z)], (MSX, MSY, 0), GRAPH_S, segs=14, a0=a0, a1=a1, smooth=False, c=TC)
for k in range(4):
    a = TAU * k / 4 + 0.4; p = Vector((MSX, MSY, 0)) + Vector((math.cos(a), math.sin(a), 0)) * 6.2
    rbox('t20_pedestal', (1.4, 1.4, 3.0), (p.x, p.y, YTOP + 1.9), GRAPH, rot=(0, 0, a), r=0.1, segs=1, c=TC)
grp_end(_t, 'Tier_20')

# ====================================================================== STAGE cleanup + lights + crew
for ob in list(coll('Stage').objects):
    if ob.name.split('.')[0] in ('boulder', 'pebble', 'slope_boulder'):
        x, y = ob.matrix_world.translation.x, ob.matrix_world.translation.y
        if (abs(x - 8.0) < 60 and abs(y + 6.0) < 37) or math.hypot(x - RXr, y - RYr) < 18 or any(math.hypot(x - p.x, y - p.y) < 2.0 for p in posts):
            bpy.data.objects.remove(ob)
world_and_sun((-0.55, -0.6, 0.58), 5.5)
ld = bpy.data.lights.new('ah_interior', 'AREA'); ld.energy = 15000; ld.size = 22; ld.color = (0.92, 0.97, 1.0)
lo = bpy.data.objects.new('ah_interior', ld); lo.location = (HX, HY, YTOP + HH - 1.0); coll('Stage').objects.link(lo)
astronaut((HX + 5.0, FRY - 4.0, YTOP), rot_z=0.4)                    # at the hall door
astronaut((HX - 6.0, CBY - 5.0, YTOP), rot_z=-0.6)                   # under the hull barrel
astronaut((WX + 2.0, WY - 5.0, YTOP + 0.12), rot_z=0.9)              # weld bay
astronaut((PDX - 3.6, PDY - 1.0, YTOP), rot_z=-1.2)                  # at dust-off A2
astronaut((s1.x + 1.8, s1.y - 1.2, YTOP), rot_z=-0.8)                # foot of YC-1 stair
astronaut((AX + 0.2, AYa - 0.05, PZ), rot_z=-0.3)                    # in the YC-1 dust-off arch
pp = Vector((SHX, SHY, 0)) + (Vector((TX, TY, 0)) - Vector((SHX, SHY, 0))).normalized() * (SR + 2.0)
astronaut((pp.x, pp.y, TOP + 21.3), rot_z=rot_u)                     # on the 21 m work platform
astronaut((RFX - 6.0 + 2.6, RFY + 6.0 - 1.2, YTOP + 12.15), rot_z=0.2)   # column deck
astronaut((RFX - 10.0, RFY - 4.0, YTOP), rot_z=0.6)
cam = setup_render(64 if not QUICK else 16)

ONLY = A.get('only', 'hero').split(',')
SHOW_TIERS = A.get('tiers') == '1'          # --tiers 1: preview every upgrade tier in a render
for o in coll(TC).all_objects: o.hide_render = not SHOW_TIERS; o.hide_set(not SHOW_TIERS)
if SHOW_TIERS:   # tier preview: clear stage rocks off the Tier_20 pad (stage is never in the game GLB; hero / turntable unchanged)
    for ob in [o for o in coll('Stage').objects if o.name.split('.')[0] in ('boulder', 'pebble', 'slope_boulder')]:
        if math.hypot(ob.matrix_world.translation.x - MSX, ob.matrix_world.translation.y - MSY) < 16.0: bpy.data.objects.remove(ob, do_unlink=True)
if 'glb' in ONLY: export_glb(os.path.join(OUT, f'{NAME}_master.glb'))
if 'blend' in ONLY:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'{NAME}_master.blend'), compress=True)
assert not ('game' in ONLY and set(ONLY) & {'hero', 'turn', 'close', 'portrait'}), 'game step is destructive: run it without render modes'
if 'game' in ONLY:   # game-ready GLB: SH_* shared palette, merge by group + material, <=30k tris, no textures, no Draco (gltfpack -cc -kn -ke after)
    import json
    SHJ = os.path.normpath(os.path.join(HERE, '..', '..', '_shared', 'shared_materials.json'))
    pal = json.load(open(SHJ))['materials']
    def sh_mat(n):
        if n in bpy.data.materials: return bpy.data.materials[n]
        d = pal[n]; m = bpy.data.materials.new(n); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = hexc(d['base']); b.inputs['Metallic'].default_value = d['metal']; b.inputs['Roughness'].default_value = d['rough']
        if 'emissive' in d: b.inputs['Emission Color'].default_value = hexc(d['emissive']); b.inputs['Emission Strength'].default_value = d['emissive_strength']
        return m
    # draw budget (every tier visible): base 6 + Crane_Jib 1 + Hall_Door_L/R 2 + Beacon_Lights 1 + 5 tiers x 1 = 15
    RULES = [('cyan', 'SH_GlowCyan'), ('glow', 'SH_GlowCyan'), ('lamp', 'SH_GlowCyan'), ('amber', 'SH_GlowCyan'), ('glass', 'SH_Graphite'), ('lens', 'SH_Graphite'),
             ('solar', 'SH_Solar'), ('rad', 'SH_White'), ('foil', 'SH_Steel'), ('mli', 'SH_Steel'), ('lox', 'SH_Steel'), ('lh2', 'SH_White'),
             ('sinter', 'SH_Rock'), ('yard', 'SH_Rock'), ('rego', 'SH_Rock'), ('block', 'SH_Rock'), ('rock', 'SH_Rock'), ('ground', 'SH_Rock'), ('satin', 'SH_Steel'),
             ('steel', 'SH_Steel'), ('graph', 'SH_Graphite'), ('rubber', 'SH_Graphite'), ('ink', 'SH_Graphite'), ('white', 'SH_White'), ('paint', 'SH_White')]
    GROUP_MAT = {'Crane_Jib': 'SH_White', 'Hall_Door_L': 'SH_White', 'Hall_Door_R': 'SH_White', 'Beacon_Lights': 'SH_GlowRed',
                 'Tier_03': 'SH_White', 'Tier_05': 'SH_White', 'Tier_08': 'SH_White', 'Tier_12': 'SH_White', 'Tier_20': 'SH_White'}
    CAP = {'Crane_Jib': 2400, 'Hall_Door_L': 400, 'Hall_Door_R': 400, 'Beacon_Lights': 600,
           'Tier_03': 1400, 'Tier_05': 1400, 'Tier_08': 900, 'Tier_12': 1600, 'Tier_20': 1800}
    def remap(m, g=None):
        if g in GROUP_MAT: return GROUP_MAT[g]
        n = (m.name if m else '').lower()
        for k, v in RULES:
            if k in n: return v
        print('UNMAPPED', m.name if m else None); return 'SH_White'
    src = list(coll('Mine').all_objects) + list(coll(TC).all_objects)
    keep = [o for o in src if o.type in ('MESH', 'CURVE', 'FONT') and not o.name.split('.')[0].startswith(('decal_', 'stencil_')) and 'astro' not in o.name.lower()]
    for o in src:
        if o not in keep: bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in keep: o.hide_set(False); o.hide_viewport = False; o.select_set(True)
    bpy.context.view_layer.objects.active = keep[0]
    bpy.ops.object.convert(target='MESH')
    groups = {}
    for o in [o for o in list(coll('Mine').all_objects) + list(coll(TC).all_objects) if o.type == 'MESH']:
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
        if G.users_collection[0] != coll('Mine'):
            for c_ in list(G.users_collection): c_.objects.unlink(G)
            coll('Mine').objects.link(G)
        G.name = (GAME_NAMES['base'] if g == 'Base' else GAME_NAMES['tiers'][g][0] if g in GAME_NAMES['tiers'] else
                  GAME_NAMES['moving'][g][0] if g in GAME_NAMES['moving'] else GAME_NAMES['door_leaves'][0 if g.endswith('_L') else 1])
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
        if g != 'Base' and tri(G) > CAP[g]: dec(G, CAP[g] / tri(G))
    B = nodes['Base']
    for it in range(6):
        rest = sum(tri(G) for g, G in nodes.items() if g != 'Base'); t = tri(B)
        if t + rest <= TGT: break
        dec(B, (TGT - rest) / t * 0.97)
    for G in nodes.values(): G.data.validate(clean_customdata=False); G.data.update()
    for g, G in nodes.items(): print('NODE', g, tri(G), [m.name for m in G.data.materials], flush=True)
    print('GAMETRIS', T0, '->', sum(tri(G) for G in nodes.values()), 'DRAWS', sum(len(G.data.materials) for G in nodes.values()), flush=True)
    sc = bpy.context.scene; sc.render.fps = 25; F1 = round(1.2 * sc.render.fps)
    def set_origin(G, h):
        G.data.transform(Matrix.Translation(-Vector(h))); G.location = Vector(h)
    def ease(act):
        for fc in act.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.easing = 'EASE_IN_OUT'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
    def push(G, act):
        tr = G.animation_data.nla_tracks.new(); tr.name = act.name.split('|')[0]; tr.strips.new(tr.name, 0, act); G.animation_data.action = None
    MV = GAME_NAMES['moving']
    # Crane_Jib: pivot = slewing ring on the tower axis; rest = swung +90 deg out over the yard (pick-up), clip swings it in over the stack
    SWING = math.radians(90)
    G = nodes['Crane_Jib']; set_origin(G, (TX, TY, JZ))
    G.animation_data_create(); act = bpy.data.actions.new(MV['Crane_Jib'][1]); G.animation_data.action = act
    G.rotation_euler = (0, 0, SWING); G.keyframe_insert('rotation_euler', index=2, frame=0)
    G.rotation_euler = (0, 0, 0.0); G.keyframe_insert('rotation_euler', index=2, frame=F1)
    ease(act); G.rotation_euler = (0, 0, SWING); push(G, act)
    # Hall_Door: pivot empty on the door track centre (floor level); leaves slide closed (rest) -> open
    D = bpy.data.objects.new(MV['Hall_Door'][0], None); D.empty_display_size = 1.0; D.location = (HX, FRY - 0.45, YTOP); coll('Mine').objects.link(D)
    for g, sx in (('Hall_Door_L', -1), ('Hall_Door_R', 1)):
        G = nodes[g]; set_origin(G, (HX + sx * LEAF_OPEN, FRY - 0.45, YTOP))
        G.parent = D; G.location = Vector((sx * LEAF_CLOSED, 0, 0))
        G.animation_data_create(); act = bpy.data.actions.new(MV['Hall_Door'][1] + '|' + g); G.animation_data.action = act
        G.location = Vector((sx * LEAF_CLOSED, 0, 0)); G.keyframe_insert('location', index=0, frame=0)
        G.location = Vector((sx * LEAF_OPEN, 0, 0)); G.keyframe_insert('location', index=0, frame=F1)
        ease(act); G.location = Vector((sx * LEAF_CLOSED, 0, 0)); push(G, act)
    # Beacon_Lights: node SCALE blink about the cluster centre (core glTF TRS -> survives gltfpack and every runtime; emissive anim would need
    # KHR_animation_pointer). Looping 1.0 s clip, STEP: on 0-0.5 s, off (scale 0.001) 0.5-1.0 s
    G = nodes['Beacon_Lights']; set_origin(G, BEACON_C)
    G.animation_data_create(); act = bpy.data.actions.new(MV['Beacon_Lights'][1]); G.animation_data.action = act
    for f, sv in ((0, 1.0), (12, 1.0), (13, 0.001), (24, 0.001), (25, 1.0)):
        G.scale = (sv, sv, sv); G.keyframe_insert('scale', frame=f)
    for fc in act.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    G.scale = (1, 1, 1); push(G, act)
    for g, G in nodes.items():
        for k in list(G.keys()): del G[k]
        if g in GAME_NAMES['tiers']: G['tier'] = GAME_NAMES['tiers'][g][1]; G['hidden_by_default'] = True
    sc.frame_set(0)
    def mark(n, p):
        e = bpy.data.objects.new(n, None); e.empty_display_size = 0.5; e.location = tuple(p); coll('Mine').objects.link(e); return e
    MN = GAME_NAMES['markers']
    stf = Vector((s1.x, s1.y - 0.8, YTOP + 0.05)); hdf = Vector((HX, FRY - 4.0, YTOP + 0.05))
    mk = [mark(MN['Stand_Center'], (SHX, SHY, TOP)), mark(MN['Hall_Door_Front'], hdf), mark(MN['Road_Entry'], (-47.5, -9.5, YTOP + 0.05)),
          mark(MN['Crate_Drop'], (HX + 8.5, FRY - 7.0, YTOP + 0.05)), mark(MN['Cam_Target'], GAME_NAMES['phone_cam']['target'])]
    mk[-1]['frame_w'] = GAME_NAMES['phone_cam']['frame_w']   # Cam_Target: empty only (no draw) + extras {frame_w}   # Cam_Target: empty only, no draw
    path = [stf, Vector((6.0, -30.0, YTOP + 0.05)), Vector((6.0, -12.0, YTOP + 0.05)), Vector((-8.0, -6.5, YTOP + 0.05)), hdf,
            Vector((2.0, -2.0, YTOP + 0.05)), Vector((SHX - 6.0, SHY - 12.0, TOP)), Vector((TX - 3.0, TY - 7.0, TOP))]
    for i, p in enumerate(path): mk.append(mark(GAME_NAMES['crew_path'] % (i + 1), p))
    bpy.ops.object.select_all(action='DESELECT')
    for o in list(nodes.values()) + [D] + mk: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{NAME}_game_raw.glb'), export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                              export_animations=True, export_animation_mode='NLA_TRACKS', export_force_sampling=True, export_extras=True,
                              export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False,
                              export_materials='EXPORT', export_image_format='NONE', export_texcoords=False)
    print('GAMEGLB', flush=True)
HC = A.get('hc')
if 'hero' in ONLY:
    w, h = (3840, 2160) if not QUICK else (960, 540)
    tgt = (6.0, -2.0, 13.0); pos = (14.0, -122.0, 30.0)
    if HC: v = [float(t) for t in HC.split(',')]; pos, tgt = tuple(v[:3]), tuple(v[3:6])
    shoot(cam, os.path.join(OUT, 'hero.png'), tgt, pos, w, h, lens=float(A.get('lens', 26)), samples=int(A.get('hs', 64)) if not QUICK else 16)
if 'portrait' in ONLY:   # in-game camera: 18 deg pitch, portrait 1179x2556 master (393x852 downscale made with PIL)
    PC = GAME_NAMES['phone_cam']   # same camera as the game: aimed at Cam_Target, 38 deg vertical FOV, distance from frame_w
    half = math.radians(PC['fov_y'] / 2); pw, ph = (1179, 2556) if not QUICK else (393, 852)
    dd = (PC['frame_w'] / 2) / (math.tan(half) * pw / ph)
    pt = Vector(PC['target']); az = math.radians(PC['az']); el = math.radians(PC['pitch'])
    pp = pt + Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * dd
    print('PHONECAM target', tuple(round(v, 3) for v in pt), 'cam', tuple(round(v, 3) for v in pp), 'd', round(dd, 3), flush=True)
    cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 36.0
    shoot(cam, os.path.join(OUT, 'portrait.png'), tuple(pt), tuple(pp), pw, ph, lens=18.0 / math.tan(half), samples=int(A.get('hs', 64)) if not QUICK else 16)
    cam.data.sensor_fit = 'AUTO'
if 'turn' in ONLY:
    os.makedirs(os.path.join(OUT, 'turntable'), exist_ok=True)
    turntable(cam, os.path.join(OUT, 'turntable'), (6.0, -2.0, 12.0), 175, 22, size=1000 if not QUICK else 400, samples=int(A.get('ts', 48)) if not QUICK else 12)
