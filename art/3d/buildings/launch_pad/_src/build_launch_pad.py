"""Planet Stack - LAUNCH PAD Lv0 (PAD-01, "Takeoff & Landing"), concept master + game GLB (Blender 4.2 LTS, headless, Cycles).

blender -b -P build_launch_pad.py -- --out .. [--quick 1] [--only blend,glb,check | game | portrait | hero,turn]
       [--pw 1179 --ph 2556] [--tiers 1] [--hs 64] [--ts 48] [--hc x,y,z,tx,ty,tz] [--lens 28] [--pcam x,y,z,W] [--tris 27000]

Lv0 = NO launch tower (the tower is Lv1). Blender coords: Z up, metres, front = -Y (toward the game camera).
Exported GLB: Y up, front +Z, origin = station origin on the ground (glTF = (x, z, -y)). Layout 10/23 21:20 (Jacob): the pad is
built around its own centre and moved 13 m north, so the PAD CENTRE / ship axis is at pad-local glTF (0, 0, -13) = world (480, 0, -13);
the flatbed road (world z 10.2-24.8, to x 481) and the U-turn stay on plain ground >= 1 m clear of every pad mesh (the truck never drives on the pad).
Style: Mine concept B (glossy white + graphite, cyan light strips, weathered + dusty). Shared helpers + shared M_ground from
art/3d/mine_concepts/_src/mc_common.py by import (NOT modified); prop mesh builder from art/3d/props/_shared_src/propgeo.py (NOT modified).
Fuel = LOX + LCH4 (liquid methane) only. Station order (qa3d): Refinery on the LEFT (-X), Cargo Space Dock on the RIGHT (+X).
Systems (collection 'Mine' = exported building; 'Stage' = renders only). World placement: qa3d/main.js puts station i at (i * 160, 0, 0);
Takeoff & Landing is i = 3, so world = pad-local glTF + (480, 0, 0) (no rotation); Blender y = -glTF z.
  * sintered landing pad r 14 m + sintered service apron to r 21 m
  * blast berm r 22-29 m, 3.4 m high, precast sintered retaining blocks, 120 deg opening on the road side (210-330 deg)
  * station lanes (Director layout 10/23 20:34, shared haul-road cross-section): eastbound world z 13 (+X) and westbound
    world z 22 (-X), x -48 .. +1 (world 432 .. 481), joined by a right-hand U-turn r 4.5 about (x 1, z 17.5) (node Road_UTurn, road not pad);
    FB-05 stops at Truck_Stop (world 476.5, z 13) on road ground beside the pad
  * pad crane PC-1 at pad-local (x 0.6, z 7) (roadside apron, 20 m south of the ship axis, free 360 deg slew): hammerhead tower crane, one skinned mesh, joints Crane_Base / Slew / Trolley / Hoist / Hook
    (RC-1 convention, code-drivable; proof clips crane_lift / crane_swing / crane_lower / crane_lift_bay / crane_swing_hold / crane_lower_hold)
  * cargo bay CB-1: 12 slots (Bay_Slot_01..12, 0.3 m apart) for the 2.3 x 1.3 x 1.5 m cargo_box, at the roadside edge of the pad; Drop_Point / Pick_Point_Bay in the bay,
    Pick_Point (+ Pick_Point_02) on the parked FB-05. Boxes go FB-05 -> bay -> ship cargo-door shelf (Hold_Door) -> hold (Hold_01..10)
  * stand-alone white frosted cryo tanks on the apron: LOX (green bands) and LCH4 · LIQUID METHANE (red-orange bands). No LH2.
  * flexible fuel hoses Hose_LOX / Hose_LCH4 on hose stands from the tank fill valves to the ship's tail fuel ports (Fuel_Hookup)
  * the pad end of the BURIED Pipe_LaunchPad line from the Dock (+X): valve vault VV-1 riser / manifold = Pipe_LaunchPad_End
  * GRAY placeholder ship in the game GLB (starter-ship massing: 40.25 m, 8 m dia, 6 legs, 4 bells, caged crew ladder (no ramp),
    mid-hull cargo door Cargo_Door with clips cargo_door_open / cargo_door_close, hold Hold_01..10 = 2 decks of 5; fuel at the bottom)
  * power: solar mast SOL-1 behind the berm + PWR-01 junction + distant fission plant behind its own berm (Stage)
Tiers (extras {tier, hidden_by_default}): Tier_03 cargo pallet + cargo lift (west apron), Tier_05 solar mast SOL-2,
Tier_08 fuel-transfer pump skid P-2, Tier_12 pad edge lights, Tier_20 landing radar / comms mast LR-1.
"""
import sys, os, math, random, json
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
    'ship': 'Ship_Placeholder', 'door': 'Cargo_Door', 'crane': 'Crane', 'crane_mesh': 'Crane_Mesh',
    'markers': {'Ship_Center': 'Ship_Center', 'Fuel_Hookup': 'Fuel_Hookup', 'Pipe_End': 'Pipe_LaunchPad_End', 'Cam_Target': 'Cam_Target'},
    'crew_path': 'Crew_Path_%02d',
    # in-game phone camera (Game Coder spec): perspective, VERTICAL FOV 38 deg, pitched down 18 deg, no azimuth (camera on -Y looking +Y,
    # glTF looks down -Z), lookAt(Cam_Target); d = (frame_w/2) / (tan19 * aspect). Game Coder safe bands: 393x852 x 12-381, y 144-568
    # (A&A 21:49: now y 165-534); 375x667 x 12-363, y 144-383 (sheet top 417). 'target' in Blender coords.
    # Director 22:34 final: tightest frame with >= 5 px for every pad mesh, the truck at Truck_Stop + boxes, the crane reach over its targets,
    # the full-height ship and the receiver at Receiver_Spot; the U-turn may sit just off screen. Solved by measure_launch_pad_frame.mjs
    # = glTF Cam_Target (0, 4, -0.7), frame_w 78.25 (approved 22:45).
    'phone_cam': {'target': (0.0, 0.7, 4.0), 'pitch': 18.0, 'fov_y': 38.0, 'frame_w': 78.25},
}
SAFE = {(393, 852): (12, 381, 165, 534), (375, 667): (12, 363, 144, 383)}   # A&A 10/23 21:49: 393 band now y 165-534
SPARE = 5    # Director: >= 5 px spare inside both bands for every pad mesh, the parked truck, crane reach, ship, receiver (measure_launch_pad_frame.mjs is authoritative)
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
height = build_stage(keep_flat=((0, 0, 44), (0, 0, 44), (RXr, RYr, 24), (RXr, RYr, 24), (-16, 30, 14), (-34, -30.5, 16), (-50, -30.5, 16), (-62, -30.5, 12), (-14, -30.5, 14), (6, -30.5, 12)))
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

# ====================================================================== PAD r 14 (40 m ship, legs to r 8.2) + service apron to r 21
PAD_R = 14.0; TOP = 0.25; S = PAD_R / 10.8; APR = 21.0
SHIFT = 13.0     # Jacob 10/23 21:20: the pad sits fully NORTH of the flatbed road. Built around the pad centre, then moved +13 m in Blender y,
                 # so the pad centre ends at pad-local glTF (0, 0, -13) = world (480, 0, -13). Road lanes stay at world z 13 / 22.
GAP_ROAD = 1.0   # min plain ground between the road toes / U-turn and any pad mesh
# station truck lanes (shared road convention): Blender y = -glTF z. Inbound y -9 (+X), return y 0 (-X), U-turn about U_C (r 4.5)
# world = pad-local glTF + (480, 0, 0): qa3d/main.js places station i at (i * GAP, 0, 0), GAP 160, Takeoff & Landing = index 3
LANE_X0, U_X, U_R = -48.0, 1.0, 4.5            # stubs x -48 (world 432 = 54 x 8 m) .. x 1 (world 481), then the U-turn east of x 1
LANES = [('eastbound', -13.0 - SHIFT), ('westbound', -22.0 - SHIFT)]   # pad frame; final Blender y -13 / -22 = world z 13 (+X) / 22 (-X)
U_C = Vector((U_X, -17.5 - SHIFT, 0.0))
BAY_X0, BAY_X1, BAY_Y0, BAY_Y1 = -14.2, -3.2, -22.1, -13.9      # pad frame; final y -9.1 .. -0.9 (roadside edge, 1.1 m off the road toe)      # cargo bay CB-1 slab (12 slots, see CARGO BAY below)
BAY_Z = 0.30
CORR_Y0, CORR_Y1 = -24.8 - SHIFT, -10.2 - SHIFT   # pad frame: flatbed road toe-to-toe (world z 10.2 .. 24.8); road tiles run to x 1 (world 481)
CORR_UR = U_R + 2.8                      # U-turn outer toe radius about U_C
def in_corr(x, y, m=0.0):
    if x <= U_X + m and CORR_Y0 - m <= y <= CORR_Y1 + m: return True
    return x >= U_X and math.hypot(x - U_C.x, y - U_C.y) <= CORR_UR + m
def in_corr_w(x, y, m=0.0): return in_corr(x, y - SHIFT, m)      # same test in the final (shifted) frame
def on_road(x, y, m=0.3):
    # lanes, U-turn or the bay slab: rim tiles / edge lights skip these
    if BAY_X0 - m <= x <= BAY_X1 + m and BAY_Y0 - m <= y <= BAY_Y1 + m: return True
    if LANE_X0 - 1 <= x <= U_X + m and any(abs(y - yc) <= 2.8 + m for _, yc in LANES): return True
    d = math.hypot(x - U_C.x, y - U_C.y)
    return x >= U_X - m and U_R - 2.8 - m <= d <= U_R + 2.8 + m
def pad_surface(r):
    """top height of the pad slab / apron lathes at radius r (-1 outside)"""
    if r <= PAD_R - 0.5: return TOP
    if r <= PAD_R: return TOP + (0.08 - TOP) * (r - (PAD_R - 0.5)) / 0.5
    if r <= APR: return 0.1 + (0.08 - 0.1) * (r - (PAD_R - 0.2)) / (APR - (PAD_R - 0.2))
    if r <= APR + 0.6: return 0.08 + (0.02 - 0.08) * (r - APR) / 0.6
    if r <= APR + 0.8: return 0.02 + (-0.1 - 0.02) * (r - APR - 0.6) / 0.2
    return -1.0
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
text('stencil_pad', 'PAD-01', (0, -7.25, Z + 0.002), (0, 0, 0), 1.0 * S, PAINT, extrude=0.002)   # inside the 8.2 m ring (road cut starts at y -10.2)
text('stencil_pad_b', 'PAD-01', (0, 7.75 * S, Z + 0.002), (0, 0, math.pi), 1.25 * S, PAINT, extrude=0.002)
annulus('pad_strip', PAD_R - 1.2, PAD_R - 1.0, TOP + 0.005, CYAN, segs=192)
for k in range(64):
    a = TAU * (k + 0.5) / 64
    if on_road((PAD_R + 0.05) * math.cos(a), (PAD_R + 0.05) * math.sin(a), 0.8): continue
    box('rim_tile', (0.62, 1.3, 0.14), ((PAD_R + 0.05) * math.cos(a), (PAD_R + 0.05) * math.sin(a), 0.06), GRAPH, rot=(0, 0, a), bevel=0.03)
for k in range(4):
    a = TAU * k / 4
    box('flame_grate', (4.2, 1.3, 0.04), (4.4 * math.cos(a), 4.4 * math.sin(a), TOP + 0.01), GRAPH_S, rot=(0, 0, a), bevel=0.01)
# apron joint lines (sintered slabs)
for k in range(24):
    a = TAU * k / 24
    if math.radians(220) < a < math.radians(300): continue      # cargo bay + crane on the roadside (south) apron
    box('apron_joint', (APR - PAD_R - 0.6, 0.05, 0.01), ((PAD_R + APR) / 2 * math.cos(a), (PAD_R + APR) / 2 * math.sin(a), 0.105), GRAPH_S, rot=(0, 0, a), bevel=0)
annulus('apron_joint_r', 17.45, 17.5, 0.105, GRAPH_S, segs=160, a0=math.radians(-60), a1=math.radians(220))
_g12 = grp_begin()
for k in range(32):
    a = TAU * k / 32; x, y = (PAD_R - 0.6) * math.cos(a), (PAD_R - 0.6) * math.sin(a)
    if on_road(x, y, 0.6): continue
    rbox('edge_light', (0.4, 0.7, 0.12), (x, y, TOP + 0.04), GRAPH_S, rot=(0, 0, a), r=0.04, segs=2)
    box('edge_lens', (0.24, 0.5, 0.02), (x, y, TOP + 0.105), LAMP if k % 4 else AMBERG, rot=(0, 0, a), bevel=0)
grp_end(_g12, 'Tier_12')

# ====================================================================== BLAST BERM r 22-29 with the lane gap on the left (toward the Refinery)
B_IN, B_OUT, B_H = 22.0, 29.0, 3.4
GAP_C, GAP_W = math.radians(270), math.radians(60)      # 210..330 deg: open on the road side (the berm never reaches the road band)
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

# ====================================================================== STATION LANES (shared haul-road cross-section) + U-turn east of x 1
HALF = [(0, 0.02, 'track'), (1.1, 0, 'track'), (1.25, -0.02, 'mark'), (1.65, -0.02, 'mark'), (1.8, 0, 'track'), (2.0, 0, 'foot'),
        (2.35, 0.25, 'crest'), (2.8, -0.04, 'toe')]
RHEX = {'track': '#a4a7ac', 'mark': '#878a8f', 'foot': '#9da0a5', 'crest': '#939499', 'toe': '#82858a', 'wear': '#76797e', 'polish': '#adb0b5'}
def _prof():
    xs = sorted(set([h[0] for h in HALF] + [0.275, 0.55, 0.825, 1.45, 1.9, 2.175]))
    out = []
    for o in xs:
        for (a, da, ka), (b, db, kb) in zip(HALF, HALF[1:] + [HALF[-1]]):
            if a <= o <= b or (a == b == o):
                t = 0 if b == a else (o - a) / (b - a); out.append((o, da + (db - da) * t, ka if o < b or a == b else kb)); break
    full = [(-o, dz, k) for o, dz, k in reversed(out) if o > 0] + out
    return full
RPROF = _prof()
def _wear(x, ph):
    t = TAU * x / 8.0; return max(0.0, min(1.0, 0.5 + 0.35 * math.sin(t + ph) + 0.25 * math.sin(3 * t + 2 * ph)))
def _rl(hx): return Vector(hexc(hx)[:3])
def lane_base(x, y):
    if in_corr(x, y, 0.05): return 0.0         # the road corridor is carved down to the ground (y 0)
    r = math.hypot(x, y)
    if r <= APR + 0.8: return max(pad_surface(r), 0.0)
    return gz(x, y)
def lane_z(x, y): return lane_base(x, y)                    # road datum = ground (FB-05 root height, flatbed_road README)
def M_lane():
    m = bpy.data.materials.new('LP_LaneVC'); nt, b = _nodes(m)
    va = nt.nodes.new('ShaderNodeVertexColor'); va.layer_name = 'Color'; link(nt, va.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.85; m.diffuse_color = hexc('#a4a7ac'); return m
LANE_M = M_lane()
def ribbon(name, samples, li):
    """samples: [(centre Vector, normal Vector, s)] -> lane mesh with the shared profile + vertex colours."""
    bm = bmesh.new(); rows = []
    for c, nrm, s_ in samples:
        row = []
        for off, dz, k in RPROF:
            p = c + nrm * off; b = lane_base(p.x, p.y)
            z = b + dz if k == 'toe' else b + 0.045 + dz
            row.append((bm.verts.new((p.x, p.y, z)), off, k, s_))
        rows.append(row)
    faces = []
    for ra, rb in zip(rows, rows[1:]):
        for j in range(len(RPROF) - 1):
            vs = (ra[j], rb[j], rb[j + 1], ra[j + 1])          # wound so the normal points up
            faces.append((bm.faces.new([v[0] for v in vs]), vs))
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    ca = me.color_attributes.new('Color', 'BYTE_COLOR', 'CORNER')
    for p, (_, vs) in zip(me.polygons, faces):
        for li_, (_, off, k, s_) in zip(p.loop_indices, vs):
            c = _rl(RHEX[k])
            if k == 'mark': c = c.lerp(_rl(RHEX['wear']), 0.35 + 0.5 * _wear(s_, li * 1.7 + (0.9 if off > 0 else 0)))
            elif k == 'track' and abs(off) <= 1.1: c = c.lerp(_rl(RHEX['polish']), 0.5 * _wear(s_, li * 2.3 + 3.1))
            ca.data[li_].color = (c.x, c.y, c.z, 1.0)
    me.materials.append(LANE_M)
    for p in me.polygons: p.use_smooth = False
    ob = bpy.data.objects.new(name, me); coll('Mine' if name == 'lane_uturn' else 'Stage').objects.link(ob); ob['vc'] = 1; ob['grp'] = 'Road' if name == 'lane_uturn' else 'Base'
    return ob
def _xs(x0, x1):
    xs, x = [], x0
    while x < x1 - 1e-6:
        xs.append(x); x += 0.4 if -9.0 <= x <= 2.0 else 0.8
    return xs + [x1]
for li, (lname, yc) in enumerate(LANES):
    ribbon('lane_' + lname, [(Vector((x, yc, 0)), Vector((0, 1, 0)), x) for x in _xs(LANE_X0, U_X)], li)
_arc = []
for i in range(41):
    ph = math.radians(90 - 180 * i / 40); u = Vector((math.cos(ph), math.sin(ph), 0))
    _arc.append((U_C + u * U_R, u, U_X + U_R * math.pi * i / 40))
ribbon('lane_uturn', _arc, 2)
LANE_TOP = {nm: yc for nm, yc in LANES}
for x in (-6.0, -14.0, -22.0, -30.0, -38.0):      # delineator posts on the outer (camera-side) edge of the westbound lane
    p = (x, LANES[1][1] - 3.2); g = lane_base(*p)
    rbox('lane_post', (0.16, 0.16, 1.2), (p[0], p[1], g + 0.55), GRAPH_S, r=0.03, segs=1, c='Stage')
    box('lane_post_tip', (0.17, 0.17, 0.2), (p[0], p[1], g + 1.05), AMBERG, bevel=0, c='Stage')

# ====================================================================== FB-05 TRUCK STOP (eastbound lane, world z 13) + receiver spot
FB_BED1, FB_BED2, FB_DECK = -1.15, -3.65, 1.90           # FB-05 Bed_Slot_01/02 local x, deck top (fb05 README)
CR_X, CR_Y = 0.6, -20.0                                  # pad crane PC-1 (pad frame): due south of the ship on the roadside apron, 20 m off the ship axis
TS = Vector((-3.5, LANE_TOP['eastbound'], 0.0))         # FB-05 root on the z 13 lane; its nose (~+4.3 m) stays west of the road end x 1
assert TS.x + 4.3 <= U_X

# ====================================================================== CARGO BAY CB-1: 12 slots for the 3 x 2.4 x 2.4 m HELIUM-3 crate
BOX = (2.3, 1.3, 1.5)        # art/3d/props/cargo_box (md5 66a3a00c): 2.3 long (glTF x) x 1.3 deep (glTF z) x 1.5 high; Hook_Point y 1.5
BAY_COLS = [-10.1, -7.5, -4.9]; BAY_ROWS = [-19.65, -18.05, -16.45, -14.85]   # 2.6 m x 1.6 m pitch = 0.3 m between boxes, long axis along X (box yaw 0)
BAY_SLOTS = [Vector((x, y, BAY_Z)) for y in BAY_ROWS for x in BAY_COLS]
BED_MID = Vector((TS.x + (FB_BED1 + FB_BED2) / 2, TS.y, 0.0))      # middle of the FB-05 bed
RECV = Vector((BED_MID.x - 1.95, (BAY_Y0 + BAY_ROWS[0] - BOX[1] / 2) / 2, BAY_Z))   # Receive_Point: bay walkway, just west of the bed
RECV_YAW = math.atan2(BED_MID.x - RECV.x, -(BED_MID.y - RECV.y))   # glTF yaw about +Y (receiver faces local +Z)
HOME_OFF = (-3.0, -1.5); HOME_YAW_LOCAL = 1.107                    # receiver_game.glb Home_Point (x, z), yaw rad, relative to Receive_Point
_c, _s = math.cos(RECV_YAW), math.sin(RECV_YAW)
_hx, _hz = HOME_OFF[0] * _c + HOME_OFF[1] * _s, -HOME_OFF[0] * _s + HOME_OFF[1] * _c
HOME = Vector((RECV.x + _hx, RECV.y - _hz, BAY_Z)); HOME_YAW = RECV_YAW + HOME_YAW_LOCAL
assert BAY_Y0 + 0.5 < HOME.y < BAY_ROWS[0] - BOX[1] / 2 - 0.3 and BAY_X0 + 2.5 < HOME.x, tuple(HOME)
# airlock AL-2 (crew shelter the receiver walks out of): door on its east face, 0.45 m behind Receiver_Home
AL_W, AL_D, AL_H = 2.2, 1.3, 2.25
AL_C = Vector((HOME.x - 0.45 - AL_W / 2, (BAY_Y0 + BAY_ROWS[0] - BOX[1] / 2) / 2, BAY_Z))   # centred in the walkway
assert AL_C.y - AL_D / 2 > BAY_Y0 + 0.02 and AL_C.y + AL_D / 2 < BAY_ROWS[0] - BOX[1] / 2 - 0.05
rbox('airlock_al2', (AL_W, AL_D, AL_H), (AL_C.x, AL_C.y, BAY_Z + AL_H / 2), WHITE, r=0.12, segs=2)
box('airlock_al2_door', (0.06, 0.9, 1.9), (AL_C.x + AL_W / 2 + 0.01, AL_C.y, BAY_Z + 0.98), GRAPH, bevel=0.01)
box('airlock_al2_strip', (0.07, 1.0, 0.07), (AL_C.x + AL_W / 2 + 0.02, AL_C.y, BAY_Z + 2.0), CYAN, bevel=0)
box('airlock_al2_lamp', (0.1, 0.18, 0.12), (AL_C.x + AL_W / 2 + 0.03, AL_C.y - 0.62, BAY_Z + 1.95), AMBERG, bevel=0)
box('airlock_al2_band', (AL_W + 0.02, AL_D + 0.02, 0.12), (AL_C.x, AL_C.y, BAY_Z + AL_H - 0.35), GRAPH, bevel=0)
text('stencil_al2', 'AL-2', (AL_C.x, AL_C.y - AL_D / 2 - 0.01, BAY_Z + 1.5), (math.pi / 2, 0, 0), 0.42, INK, extrude=0.002)      # 01-03 front row (west -> east) ... 10-12 back row
rbox('bay_slab', (BAY_X1 - BAY_X0, BAY_Y1 - BAY_Y0, 0.3), ((BAY_X0 + BAY_X1) / 2, (BAY_Y0 + BAY_Y1) / 2, 0.15), BLOCK, r=0.06, segs=1)
box('bay_strip', (BAY_X1 - BAY_X0 - 0.4, 0.06, 0.06), ((BAY_X0 + BAY_X1) / 2, BAY_Y0 - 0.02, 0.22), CYAN, bevel=0)
for p in BAY_SLOTS:
    hx, hy = BOX[0] / 2 + 0.15, BOX[1] / 2 + 0.15
    for sx in (-1, 1):
        for sy in (-1, 1):   # corner marks
            box('bay_mark', (0.7, 0.1, 0.006), (p.x + sx * (hx - 0.35), p.y + sy * hy, BAY_Z + 0.003), PAINT, bevel=0)
            box('bay_mark', (0.1, 0.6, 0.006), (p.x + sx * hx, p.y + sy * (hy - 0.3), BAY_Z + 0.003), PAINT, bevel=0)
text('stencil_bay', 'CB-1', (BAY_X1 - 1.6, BAY_Y0 + 0.85, BAY_Z + 0.004), (0, 0, 0), 0.7, PAINT, extrude=0.002)

# ====================================================================== PAD CRANE PC-1 (hammerhead tower crane, RC-1 joint convention)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', '..', 'props', '_shared_src')))
from propgeo import MB, P as PP, lin as plin
CR_SLEW_Z, CR_JIB_Z = 19.0, 20.0
CR_SHEAVE = CR_JIB_Z - 0.35; CR_HOOK_DROP = 0.95
CR_JIB_L, CR_CJ_L = 15.0, 3.6          # counter-jib kept short: its tail stays 1 m clear of the hull when it swings past the ship
CR_TR_MIN, CR_TR_MAX = 2.6, CR_JIB_L - 0.8
CR_CABLE_MIN, CR_CABLE_MAX = 0.6, CR_SHEAVE - CR_HOOK_DROP - 0.4
def build_crane():
    W1, W2, G1, G2, ST = PP['white'], PP['white2'], PP['graph'], PP['graph2'], PP['steel']
    m = MB()
    m.box((3.0, 3.0, 0.5), (0, 0, 0.25), plin('#8d9096'))                         # footing (sits 0.25 proud of the pad)
    for sx in (-1, 1):
        for sy in (-1, 1): m.cyl((sx * 1.15, sy * 1.15, 0.5), (sx * 1.15, sy * 1.15, 0.62), 0.08, ST, segs=6)
    MW = 1.6; M0, M1 = 0.5, CR_SLEW_Z - 0.3
    for sx in (-1, 1):
        for sy in (-1, 1): m.box((0.2, 0.2, M1 - M0), (sx * MW / 2, sy * MW / 2, (M0 + M1) / 2), W1)
    NP = 11; ph = (M1 - M0) / NP
    for k in range(NP + 1):
        z = M0 + k * ph
        for s in (-1, 1):
            m.box((MW, 0.1, 0.1), (0, s * MW / 2, z), G1); m.box((0.1, MW, 0.1), (s * MW / 2, 0, z), G1)
        if k == NP: break
        dl = math.hypot(MW, ph); a = math.atan2(ph, MW)
        for s in (-1, 1):
            m.box((dl, 0.07, 0.07), (0, s * MW / 2, z + ph / 2), G1, rot=(0, -a * (1 if k % 2 else -1), 0))
            m.box((0.07, dl, 0.07), (s * MW / 2, 0, z + ph / 2), G1, rot=(a * (1 if k % 2 else -1), 0, 0))
    m.box((0.05, 0.02, M1 - M0 - 2.0), (MW / 2 + 0.12, -MW / 2 + 0.12, (M0 + M1) / 2 + 0.6), PP['cyan'], mat=1)
    m.box((0.2, 0.7, M1 - M0 - 1.0), (0, -MW / 2 - 0.05, (M0 + M1) / 2 + 0.3), PP['cable'])          # ladder cage
    m.box((1.0, 0.6, 1.4), (1.3, 1.3, 1.2), W1); m.box((0.6, 0.02, 0.04), (1.3, 0.99, 1.5), PP['cyan'], mat=1)   # power cabinet
    m.cyl((0, 0, CR_SLEW_Z - 0.3), (0, 0, CR_SLEW_Z), 1.1, G1, segs=12)
    B = 'Slew'; Z = CR_SLEW_Z; JZ = CR_JIB_Z
    m.cyl((0, 0, Z), (0, 0, Z + 0.25), 1.1, W1, segs=12, bone=B)
    m.box((1.8, 1.8, JZ - Z - 0.25), (0, 0, (Z + 0.25 + JZ) / 2), G1, bone=B)
    CZ = JZ - 0.9                                                                   # cab under the jib root (looks along the jib)
    m.box((1.8, 1.3, 1.5), (1.4, -1.45, CZ), W1, bone=B, taper=0.92)
    m.box((0.04, 1.1, 0.55), (2.31, -1.45, CZ + 0.15), plin('#0e1a24'), bone=B)
    m.box((1.6, 0.04, 0.5), (1.4, -2.11, CZ + 0.15), plin('#0e1a24'), bone=B)
    m.box((1.6, 0.02, 0.04), (1.4, -2.13, CZ - 0.2), PP['cyan'], mat=1, bone=B)
    HZ = JZ + 4.0
    for sy in (-1, 1):
        m.cyl((0.8, sy * 0.8, JZ + 0.8), (0, sy * 0.3, HZ), 0.08, W1, segs=6, bone=B)
        m.cyl((-0.8, sy * 0.8, JZ + 0.8), (0, sy * 0.3, HZ), 0.08, W1, segs=6, bone=B)
        m.cyl((0, sy * 0.3, HZ), (CR_JIB_L * 0.7, sy * 0.35, JZ + 0.85), 0.035, ST, segs=4, bone=B)
        m.cyl((0, sy * 0.3, HZ), (-CR_CJ_L + 0.4, sy * 0.35, JZ + 0.75), 0.035, ST, segs=4, bone=B)
    m.box((0.45, 0.9, 0.3), (0, 0, HZ), G1, bone=B)
    m.cyl((0, 0, HZ + 0.15), (0, 0, HZ + 0.7), 0.05, ST, segs=6, bone=B); m.cyl((0, 0, HZ + 0.7), (0, 0, HZ + 0.86), 0.12, PP['red'], segs=8, bone=B)
    JW, JH = 0.9, 0.85
    for sy in (-1, 1): m.box((CR_JIB_L, 0.12, 0.14), (CR_JIB_L / 2, sy * JW / 2, JZ + 0.07), W1, bone=B)
    m.box((CR_JIB_L, 0.14, 0.12), (CR_JIB_L / 2, 0, JZ + JH), W1, bone=B)
    NJ = 12; jp = CR_JIB_L / NJ
    for k in range(NJ):
        x0, x1 = k * jp, (k + 1) * jp
        for sy in (-1, 1): m.cyl((x0 if k % 2 == 0 else x1, sy * JW / 2, JZ + 0.09), (x1 if k % 2 == 0 else x0, 0, JZ + JH), 0.04, G1, segs=6, bone=B)
        m.box((0.07, JW, 0.07), (x1, 0, JZ + 0.07), G1, bone=B)
    for sy in (-1, 1): m.box((CR_JIB_L - 1.2, 0.02, 0.05), (CR_JIB_L / 2 + 0.4, sy * (JW / 2 + 0.07), JZ + 0.06), PP['cyan'], mat=1, bone=B)
    m.box((0.35, JW + 0.2, JH + 0.2), (CR_JIB_L + 0.1, 0, JZ + JH / 2), G1, bone=B)
    for k, x in enumerate((4.0, 7.5, 11.0)): m.box((0.6, 0.02, 0.2), (x, -JW / 2 - 0.08, JZ + 0.45), PP['amber'] if k == 1 else W2, bone=B)
    for sy in (-1, 1): m.box((CR_CJ_L, 0.14, 0.32), (-CR_CJ_L / 2, sy * 0.55, JZ + 0.16), W1, bone=B)
    m.box((CR_CJ_L - 0.3, 1.2, 0.05), (-CR_CJ_L / 2, 0, JZ + 0.34), G1, bone=B)
    for k in range(3): m.box((0.5, 1.7, 1.6), (-CR_CJ_L + 0.35 + k * 0.55, 0, JZ - 0.5), plin('#8d9096') if k != 1 else plin('#7d8086'), bone=B)
    m.box((1.4, 0.02, 0.05), (-CR_CJ_L + 0.9, -0.86, JZ - 0.1), PP['cyan'], mat=1, bone=B)
    m.box((1.0, 1.0, 0.8), (-1.2, 0, JZ + 0.75), W1, bone=B); m.cyl((-1.2, -0.4, JZ + 0.75), (-1.2, 0.4, JZ + 0.75), 0.32, G1, segs=10, bone=B)
    T = 'Trolley'
    m.box((1.1, JW + 0.34, 0.34), (0, 0, JZ - 0.17), G1, bone=T); m.box((1.0, JW + 0.36, 0.06), (0, 0, JZ - 0.35), W1, bone=T)
    for sx in (-1, 1): m.cyl((sx * 0.32, -JW / 2 - 0.17, JZ + 0.1), (sx * 0.32, JW / 2 + 0.17, JZ + 0.1), 0.1, ST, segs=6, bone=T)
    m.box((0.7, 0.02, 0.04), (0, -JW / 2 - 0.18, JZ - 0.17), PP['cyan'], mat=1, bone=T)
    m.cyl((0, -0.15, CR_SHEAVE), (0, 0.15, CR_SHEAVE), 0.16, ST, segs=8, bone=T)
    for sx in (-0.08, 0.08): m.cyl((sx, 0, CR_SHEAVE), (sx, 0, CR_SHEAVE - 1.0), 0.024, PP['cable'], segs=4, bone='Hoist', caps=False)
    H = 'Hook'; D = CR_HOOK_DROP; SX, SY = BOX[0] / 2 - 0.05, BOX[1] / 2 - 0.05      # spreader sized for the 2.3 x 1.3 cargo_box
    m.box((0.55, 0.4, 0.44), (0, 0, D - 0.22), plin('#ffb020'), bone=H)
    m.cyl((-0.16, 0, D - 0.1), (0.16, 0, D - 0.1), 0.18, G1, segs=8, bone=H)
    m.box((0.09, 0.09, 0.22), (0, 0, D - 0.55), ST, bone=H)
    for sx in (-1, 1):
        for sy in (-1, 1): m.cyl((0, 0, D - 0.64), (sx * SX, sy * SY, 0.13), 0.022, ST, segs=4, bone=H)
    for sy in (-1, 1): m.box((2 * SX + 0.14, 0.14, 0.13), (0, sy * SY, 0.065), G1, bone=H)
    for sx in (-1, 1): m.box((0.14, 2 * SY, 0.13), (sx * SX, 0, 0.065), G1, bone=H)
    m.box((2 * SX - 0.4, 0.02, 0.03), (0, -SY - 0.08, 0.07), PP['cyan'], mat=1, bone=H)
    for sx in (-1, 1):
        for sy in (-1, 1): m.box((0.18, 0.18, 0.08), (sx * SX, sy * SY, 0.02), plin('#ffb020'), bone=H)
    m.weather(seed=17, z0=0.0, z1=3.0, amt=0.45, noise=0.06)
    print('CRANE TRIS', m.tris(), flush=True)
    ad = bpy.data.armatures.new('Crane_Armature'); arm = bpy.data.objects.new(GAME_NAMES['crane'], ad); coll('Mine').objects.link(arm)
    arm.location = (CR_X, CR_Y, 0.0)
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='EDIT')
    def bone(n, head, parent=None):
        eb = ad.edit_bones.new(n); eb.head = head; eb.tail = Vector(head) + Vector((0, 0, 0.5)); eb.roll = 0
        if parent: eb.parent = ad.edit_bones[parent]
    bone('Crane_Base', (0, 0, 0)); bone('Slew', (0, 0, CR_SLEW_Z), 'Crane_Base')
    bone('Trolley', (CR_TR_MIN, 0, CR_JIB_Z), 'Slew'); bone('Hoist', (CR_TR_MIN, 0, CR_SHEAVE), 'Trolley')
    bone('Hook', (CR_TR_MIN, 0, CR_SHEAVE - 1.0 - CR_HOOK_DROP), 'Trolley')
    bpy.ops.object.mode_set(mode='OBJECT')
    ob = m.build(GAME_NAMES['crane_mesh'], coll('Mine'))
    REST = {'Trolley': Vector((CR_TR_MIN, 0, 0)), 'Hoist': Vector((CR_TR_MIN, 0, 0)), 'Hook': Vector((CR_TR_MIN, 0, CR_SHEAVE - 1.0 - CR_HOOK_DROP))}
    gi = {g.index: g.name for g in ob.vertex_groups}
    for v in ob.data.vertices:
        g = gi[v.groups[0].group]
        if g in REST: v.co += REST[g]
    if 'root' in ob.vertex_groups: ob.vertex_groups['root'].name = 'Crane_Base'
    ob.parent = arm; md = ob.modifiers.new('Armature', 'ARMATURE'); md.object = arm
    ob['grp'] = 'Crane'; arm['grp'] = 'Crane'; ob['vc'] = 1
    return arm, ob
CRANE, CRANE_MESH = build_crane()
def crane_solve(hook_world):
    """hook target (Blender world, spreader underside) -> (theta, r, L) in the RC-1 convention (theta = Blender azimuth = glTF atan2(-z, x))"""
    d = Vector(hook_world) - CRANE.location
    return math.atan2(d.y, d.x), math.hypot(d.x, d.y), CR_SHEAVE - d.z - CR_HOOK_DROP
def crane_pose(th, r, L, box_yaw):
    pb = CRANE.pose.bones
    for b in pb: b.rotation_mode = 'XYZ'
    pb['Slew'].rotation_euler = (0, th, 0); pb['Trolley'].location = (r - CR_TR_MIN, 0, 0)
    pb['Hoist'].scale = (1, L, 1); pb['Hook'].location = (0, 1.0 - L, 0); pb['Hook'].rotation_euler = (0, box_yaw - th, 0)
def crane_rest():
    for b in CRANE.pose.bones: b.rotation_mode = 'XYZ'; b.rotation_euler = (0, 0, 0); b.location = (0, 0, 0); b.scale = (1, 1, 1)
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
    t1 = text('decal_' + tag, big_lbl, (cx, cy - R - 0.012, z0 + H * 0.5 - 1.25), (math.pi / 2, 0, 0), R * 0.78, INK, extrude=0.01)
    wrap_text(t1, cx, cy, R)
    t2 = text('decal_' + tag + '_sub', sub_lbl, (cx, cy - R - 0.012, z0 + H * 0.5 - 2.45), (math.pi / 2, 0, 0), 0.3, INK, extrude=0.006)
    wrap_text(t2, cx, cy, R)
    return Vector((cx, cy, 0))
LOX_P = Vector((14.2, -9.6, 0)); LCH4_P = Vector((16.6, 3.4, 0))
LOX_R, LOX_H = 1.7, 8.2; LCH4_R, LCH4_H = 2.1, 9.0
cryo_tank('lox', LOX_P.x, LOX_P.y, LOX_R, LOX_H, LOXB, 'LOX', 'LIQUID OXYGEN')
cryo_tank('lch4', LCH4_P.x, LCH4_P.y, LCH4_R, LCH4_H, LCH4B, 'LCH4', 'LCH4 · LIQUID METHANE')

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
SHIP_PSI = math.radians(60.0)       # placeholder ship yaw vs the starter-ship frame: legs 0/60/../300, door (215 + 60 = 275) faces the camera, ladder 330
DOOR_A = math.radians(275.0); LAD_A = math.radians(330.0)
PORT_Z = TOP + 4.2
def _port(adeg): a = math.radians(adeg); return Vector(((SHIP_R + 0.45) * math.cos(a), (SHIP_R + 0.45) * math.sin(a), PORT_Z))
PORT = {'LOX': _port(15.0), 'LCH4': _port(40.0)}
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
    s1 = st.lerp(port, 0.62); s1.z = 0.8; s2 = st.lerp(port, 0.84); s2.z = 2.5
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
    u = Vector((PORT[tag].x, PORT[tag].y, 0)).normalized(); p = u * (SHIP_R + 1.35)
    rod('qd_stand', (p.x, p.y, TOP), (p.x, p.y, 1.45), 0.08, WHITE_S, segs=10)
    rbox('qd_stand_base', (0.7, 0.7, 0.12), (p.x, p.y, TOP + 0.06), GRAPH_S, r=0.03, segs=1)
    ring('qd_stand_glow', 0.09, (p.x, p.y, 1.2), 0.05, CYAN, w=0.02, segs=16)

# ====================================================================== Tier_03 CARGO pallet + cargo lift (behind the cargo bay CB-1)
_g3 = grp_begin()
CX, CY = -12.6, 5.2                                                  # behind the cargo bay
rot_c = 0.0
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
LX, LY = -18.0, 5.2; rl = 0.0
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
LR = Vector((-9.0, 16.5, 0))
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
JX, JY = -10.5, 9.0
rbox('pwr_junction', (1.4, 0.9, 1.7), (JX, JY, 0.95), WHITE, r=0.14, segs=3)
box('pwr_junction_strip', (1.0, 0.02, 0.06), (JX, JY - 0.46, 1.55), CYAN, bevel=0)
text('decal_pwr', 'PWR-01', (JX, JY - 0.46, 1.25), (math.pi / 2, 0, 0), 0.16, INK, extrude=0.003)
route = [Vector((-12.0, 30.4, 0)), Vector((-12.5, 22.5, 0)), Vector((-11.6, 14.0, 0)), Vector((JX, JY + 0.6, 0))]
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

# ====================================================================== STAINLESS STARTER SHIP (game weight; Jacob 10/23 23:43 replaced the gray placeholder)
# starter ship: 40.25 m tall, 8 m dia, 6 legs, 4 bells; fuel tanks at the bottom, cargo mid-hull (door), crew up top via a caged ladder
# geometry: lp_stainless_ship.py, built from the 46a9346 starter_ship_master.glb exterior (starter_ship_46a9346_exterior.glb via lp_extract_starter.py);
# node name stays Ship_Placeholder for qa3d/main.js; ladder, cage, airlock hatch and hatch deck keep the placeholder positions
_gs = grp_begin()
SZ0 = TOP + 2.65
SILL = TOP + 12.4; DOOR_H, DOOR_HW = 4.8, math.radians(23.8)
LU = Vector((math.cos(LAD_A), math.sin(LAD_A), 0)); LT = Vector((-LU.y, LU.x, 0))
LAD_TOP = TOP + 21.6
if HERE not in sys.path: sys.path.insert(0, HERE)
import lp_stainless_ship
_ship_names, SSM = lp_stainless_ship.build(globals())
LADDER_FOOT = Vector((LU.x * 5.2, LU.y * 5.2, TOP))
for o in [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - _gs]:
    o['grp'] = 'Ship'
# ---- cargo door (own node, origin on the hinge at the sill; opens outward + down into a shelf about local X)
_gd = grp_begin()
lathe('cargo_door_panel', [(SHIP_R + 0.02, SILL), (SHIP_R + 0.2, SILL), (SHIP_R + 0.2, SILL + DOOR_H), (SHIP_R + 0.02, SILL + DOOR_H), (SHIP_R + 0.02, SILL)],
      (0, 0, 0), SSM['B'], segs=10, a0=DOOR_A - DOOR_HW, a1=DOOR_A + DOOR_HW, smooth=False)
for zz in (0.25, DOOR_H - 0.25):
    lathe('cargo_door_rib', [(SHIP_R + 0.2, SILL + zz - 0.08), (SHIP_R + 0.26, SILL + zz - 0.08), (SHIP_R + 0.26, SILL + zz + 0.08), (SHIP_R + 0.2, SILL + zz + 0.08)],
          (0, 0, 0), SSM['band'], segs=10, a0=DOOR_A - DOOR_HW, a1=DOOR_A + DOOR_HW, smooth=False)
_door_parts = [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - _gd]
bpy.ops.object.select_all(action='DESELECT')
for o in _door_parts: o.select_set(True)
bpy.context.view_layer.objects.active = _door_parts[0]
for o in _door_parts:
    for md in list(o.modifiers): o.modifiers.remove(md)
if len(_door_parts) > 1: bpy.ops.object.join()
DOOR = bpy.context.active_object; DOOR.name = GAME_NAMES['door']
HINGE = Vector((math.cos(DOOR_A), math.sin(DOOR_A), 0)) * (SHIP_R + 0.11) + Vector((0, 0, SILL))
DOOR_ROT_Z = DOOR_A + math.pi / 2             # door local X = hinge tangent, local -Y = outward, Z = up
Mloc = (Matrix.Translation(HINGE) @ Matrix.Rotation(DOOR_ROT_Z, 4, 'Z'))
DOOR.data.transform(Mloc.inverted()); DOOR.matrix_world = Mloc; DOOR['grp'] = 'Door'
DOOR['clips'] = 'cargo_door_open (2 s: rotation about local +X 0 -> 90 deg, top swings out and down into a shelf) / cargo_door_close (2 s: 90 -> 0)'
DOOR['hinge'] = 'origin = hinge line at the sill (glTF y %.2f), node local +X = hinge axis' % SILL
# ---- hold: 10 slots for the 2.3 x 1.3 x 1.5 cargo_box, 2 decks of 5 (Hold_01-05 lower = door sill, Hold_06-10 upper), 0.3 m between boxes.
# Footprint per deck: 2 x 2 grid (2.6 m along the hinge x 1.6 m radial) + 1 box centred at the back; worst corner r 3.26 m vs hull r 4.0.
DU = Vector((math.cos(DOOR_A), math.sin(DOOR_A), 0)); DT = Vector((-DU.y, DU.x, 0))
BOX_YAW_HOLD = DOOR_A + math.pi / 2 - TAU    # 5 deg: crate long axis along the hinge (labels face out of the door)
HOLD = []
HOLD_DECK_DZ = (0.0, BOX[2] + 0.3 + 0.15)     # lower deck at the sill, upper deck 1.95 m higher (box top SILL + 3.55 < door top SILL + 4.8)
for dz in HOLD_DECK_DZ:
    for a, b in ((-2.4, 0.0), (-0.8, -1.3), (-0.8, 1.3), (0.8, -1.3), (0.8, 1.3)):
        c = DU * a + DT * b
        for sa in (-1, 1):
            for sb in (-1, 1): assert (c + DU * sa * BOX[1] / 2 + DT * sb * BOX[0] / 2).length <= SHIP_R - 0.35
        HOLD.append(c + Vector((0, 0, SILL + 0.1 + dz)))
HOLD = HOLD[:10]
_lift = (SHIP_R + 0.02 + 0.09) - math.sqrt((SHIP_R + 0.02) ** 2 - (BOX[0] / 2) ** 2)       # crate ends rest on the curved shelf
HOLD_DOOR = DU * (SHIP_R + 0.11 + 2.4) + Vector((0, 0, SILL + _lift))

# ====================================================================== MARKERS + CRANE CLIPS (proof clips; code drives the joints directly)
def mark(n, p, extras=None, yaw=0.0, size=0.5):
    e = bpy.data.objects.new(n, None); e.empty_display_size = size; e.location = tuple(p); e.rotation_euler = (0, 0, yaw)
    coll('Mine').objects.link(e); e['grp'] = 'Marker'
    for k, v in (extras or {}).items(): e[k] = v
    return e
def gl(p): return [round(p.x, 3), round(p.z, 3), round(-(p.y + SHIFT), 3)]     # final pad-local glTF
def target(n, base, yaw, extra=None, note=None):
    hk = Vector(base) + Vector((0, 0, BOX[2])); th, r, L = crane_solve(hk)
    assert CR_TR_MIN - 1e-6 <= r <= CR_TR_MAX + 1e-6 and CR_CABLE_MIN - 1e-6 <= L <= CR_CABLE_MAX + 1e-6, (n, r, L)
    ex = {'kind': 'crane_target', 'box_base': True, 'box_yaw_deg': round(math.degrees(yaw), 2),
          'crane_solve': {'slew_rad': round(th, 4), 'trolley_m': round(r, 3), 'hoist_m': round(L, 3), 'hook_yaw_rad': round(yaw - th, 4)},
          'note': note or 'box Base sits here; hook target = this + (0, box height, 0); crane_solve = joint values with the box hanging at rest here'}
    ex.update(extra or {})
    return mark(n, base, ex, yaw)
MK = []
TRUCK_YAW = 0.0
MK.append(mark('Truck_Stop', TS, {'kind': 'truck_pose', 'truck': 'FB-05', 'yaw_deg': 0, 'lane': 'eastbound world z 13',
          'note': 'FB-05 root here heading +X; then Bed_Slot_01 = Pick_Point, Bed_Slot_02 = Pick_Point_02'}))
PICK = Vector((TS.x + FB_BED1, TS.y, TS.z + FB_DECK)); PICK2 = Vector((TS.x + FB_BED2, TS.y, TS.z + FB_DECK))
MK.append(target('Pick_Point', PICK, 0.0, {'slot': 'FB-05 Bed_Slot_01'}))
MK.append(target('Pick_Point_02', PICK2, 0.0, {'slot': 'FB-05 Bed_Slot_02'}))
for i, p in enumerate(BAY_SLOTS):
    MK.append(target('Bay_Slot_%02d' % (i + 1), p, 0.0, {'bay': 'CB-1', 'slot_size_m': [BOX[0], BOX[2], BOX[1]]}))
DROP = BAY_SLOTS[0]; PICK_BAY = BAY_SLOTS[2]
MK.append(target('Drop_Point', DROP, 0.0, {'same_as': 'Bay_Slot_01', 'use': 'truck -> bay drop (code may use any free Bay_Slot)'}))
MK.append(target('Pick_Point_Bay', PICK_BAY, 0.0, {'same_as': 'Bay_Slot_03', 'use': 'bay -> ship pick (code may use any full Bay_Slot)'}))
MK.append(target('Hold_Door', HOLD_DOOR, BOX_YAW_HOLD, {'use': 'crane sets the box on the open cargo-door shelf; code then moves it to a Hold_NN',
                                                        'needs': 'cargo_door_open finished'}))
for i, p in enumerate(HOLD):
    MK.append(mark('Hold_%02d' % (i + 1), p, {'kind': 'hold_slot', 'box_base': True, 'box_yaw_deg': round(math.degrees(BOX_YAW_HOLD), 2),
                   'deck': i // 5}, BOX_YAW_HOLD))
MK.append(mark('Receiver_Spot', RECV, {'kind': 'crew_spot', 'rig': 'receiver_game.glb Receive_Point', 'yaw_deg': round(math.degrees(RECV_YAW), 2),
                   'faces': 'FB-05 bed middle %s' % gl(BED_MID), 'home': 'Receiver_Home', 'home_dist_m': round((HOME - RECV).length, 3),
                   'note': 'place the receiver root here with this yaw; walk_out ends / walk_back starts here'}, RECV_YAW))
MK.append(mark('Receiver_Home', HOME, {'kind': 'crew_spot', 'rig': 'receiver_game.glb Home_Point', 'yaw_deg': round(math.degrees(HOME_YAW), 2),
                   'airlock': 'AL-2 door (east face)', 'dist_to_receiver_spot_m': round((HOME - RECV).length, 3),
                   'note': 'Receiver_Spot + R(yaw) * (-3, 0, -1.5): matches the rig Home_Point, walk_out starts / walk_back ends here'}, HOME_YAW))
_route = [('Road_Entry', Vector((LANE_X0, LANES[0][1], lane_z(LANE_X0, LANES[0][1]))), 0.0),
          ('Turn_Start', Vector((U_X, LANES[0][1], lane_z(U_X, LANES[0][1]))), 0.0),
          ('Turn_End', Vector((U_X, LANES[1][1], lane_z(U_X, LANES[1][1]))), 180.0),
          ('Road_Exit', Vector((LANE_X0, LANES[1][1], lane_z(LANE_X0, LANES[1][1]))), 180.0)]
_nxt = {'Road_Entry': 'Truck_Stop', 'Truck_Stop': 'Turn_Start', 'Turn_Start': 'Turn_End', 'Turn_End': 'Road_Exit', 'Road_Exit': None}
for n, p, yd in _route:
    ex = {'kind': 'road_leg', 'yaw_deg': yd, 'next': _nxt[n], 'world_xz': [round(480 + p.x, 2), round(-(p.y + SHIFT), 2)]}
    if n == 'Turn_Start': ex['turn'] = {'center_gltf': gl(U_C), 'radius_m': U_R, 'dir': 'right (+X -> +Z -> -X)', 'deg': 180}
    MK.append(mark(n, p, ex, math.radians(yd)))
MK[0]['next'] = 'Turn_Start'; MK[0]['world_xz'] = [round(480 + TS.x, 2), round(-(TS.y + SHIFT), 2)]
MK.append(mark(GAME_NAMES['markers']['Ship_Center'], (0, 0, TOP), {'ship_yaw_deg_vs_starter_frame': round(math.degrees(SHIP_PSI), 1)}))
MK.append(mark(GAME_NAMES['markers']['Fuel_Hookup'], FUEL_HOOKUP, {'LOX': gl(PORT['LOX']), 'LCH4': gl(PORT['LCH4'])}))
MK.append(mark('Ladder_Foot', LADDER_FOOT, {'kind': 'crew_spot', 'note': 'crew climb the caged ladder to the hatch at y %.1f (no ramp)' % LAD_TOP}))
MK.append(mark('Crate_Drop', (CX, CY, 0.33), {'tier': 3, 'note': 'Tier_03 cargo pallet (shown when Tier_03 is on)'}))
MK.append(mark(GAME_NAMES['markers']['Pipe_End'], PIPE_END, {'from': 'Dock Pipe_LaunchPad (buried, +X)', 'line': 'Pipe_LaunchPad'}))
_crew = [HOME, RECV, Vector((-2.4, -15.2, 0.1)), Vector((3.2, -9.6, TOP)), LADDER_FOOT]
for i, p in enumerate(_crew):
    MK.append(mark(GAME_NAMES['crew_path'] % (i + 1), p, {'kind': 'crew_path'}))
# ---- crane clips (30 fps, smootherstep): code can ignore these and drive Slew / Trolley / Hoist / Hook itself
def smooth(t): t = min(max(t, 0.0), 1.0); return t * t * t * (t * (6 * t - 15) + 10)
TRAVEL_LO = BAY_Z + BOX[2] + 0.7 + BOX[2] + 0.4      # hook height when carrying over the truck / bay (crate clears stacked neighbours)
TRAVEL_HI = HOLD_DOOR.z + BOX[2] + 1.25               # hook height for the door shelf run
def hook_at(base, h): return Vector((base.x, base.y, h))
def st(base, h, yaw):
    th, r, L = crane_solve(hook_at(base, h)); return [th, r, L, yaw - th]
def unwrap(a, b, prefer=None):
    """slew from a to b without pointing into the ship: go the way that avoids the hull bearing"""
    if JIB_FREE:
        d = (b - a + math.pi) % TAU - math.pi; return a + d
    hull = math.atan2(-CR_Y, -CR_X)
    best = None
    for k in (-1, 0, 1):
        bb = b + k * TAU
        lo, hi = min(a, bb), max(a, bb)
        hits = any(lo <= hull + j * TAU <= hi for j in (-1, 0, 1))
        if not hits and (best is None or abs(bb - a) < abs(best - a)): best = bb
    assert best is not None, 'no hull-free slew path'
    return best
JIB_FREE = math.hypot(CR_X, CR_Y) >= CR_JIB_L + SHIP_R + 0.6
CLIPS = {}
PL, PH = st(PICK, PICK.z + BOX[2], 0.0), st(PICK, TRAVEL_LO, 0.0)
DH, DL = st(DROP, TRAVEL_LO, 0.0), st(DROP, DROP.z + BOX[2], 0.0)
BL, BH = st(PICK_BAY, PICK_BAY.z + BOX[2], 0.0), st(PICK_BAY, TRAVEL_HI, 0.0)
HH, HL = st(HOLD_DOOR, TRAVEL_HI, BOX_YAW_HOLD), st(HOLD_DOOR, HOLD_DOOR.z + BOX[2], BOX_YAW_HOLD)
def fix(s0, s1):
    th1 = unwrap(s0[0], s1[0]); d = th1 - s1[0]; return [th1, s1[1], s1[2], s1[3] - d]
CLIPS = {'crane_lift': (PL, PH, 2.0), 'crane_swing': (PH, fix(PH, DH), 3.0), 'crane_lower': (DH, DL, 2.0),
         'crane_lift_bay': (BL, BH, 3.0), 'crane_swing_hold': (BH, fix(BH, HH), 3.0), 'crane_lower_hold': (HH, HL, 1.5)}
POSES = {'pick_low': PL, 'pick_high': PH, 'drop_high': DH, 'drop_low': DL, 'bay_low': BL, 'bay_high': BH, 'hold_high': HH, 'hold_low': HL}
FPS = 30; bpy.context.scene.render.fps = FPS
CRANE.animation_data_create()
for cn, (s0, s1, dur) in CLIPS.items():
    act = bpy.data.actions.new(cn); CRANE.animation_data.action = act; nf = int(round(dur * FPS))
    for f in range(nf + 1):
        u = smooth(f / nf); s = [a + (b - a) * u for a, b in zip(s0, s1)]
        crane_pose(s[0], s[1], s[2], s[3] + s[0])
        for bn, path in (('Slew', 'rotation_euler'), ('Trolley', 'location'), ('Hoist', 'scale'), ('Hook', 'location'), ('Hook', 'rotation_euler')):
            CRANE.pose.bones[bn].keyframe_insert(path, frame=f)
    for fc in act.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    CRANE.animation_data.action = None
    tr = CRANE.animation_data.nla_tracks.new(); tr.name = cn; tr.strips.new(cn, 0, act); tr.mute = True
# verify: posed Hook head == solved target for every pose
for pn, s in POSES.items():
    crane_pose(s[0], s[1], s[2], s[3] + s[0]); bpy.context.view_layer.update()
    hw = CRANE.matrix_world @ CRANE.pose.bones['Hook'].head
    th, r, L = s[0], s[1], s[2]
    exp_ = CRANE.location + Vector((r * math.cos(th), r * math.sin(th), CR_SHEAVE - L - CR_HOOK_DROP))
    assert (hw - exp_).length < 1e-3, (pn, tuple(hw), tuple(exp_))
crane_rest(); bpy.context.view_layer.update()
DOOR.animation_data_create()
for cn, (a0, a1) in (('cargo_door_open', (0.0, math.pi / 2)), ('cargo_door_close', (math.pi / 2, 0.0))):
    act = bpy.data.actions.new(cn); DOOR.animation_data.action = act; nf = 60
    for f in range(nf + 1):
        DOOR.rotation_euler = (a0 + (a1 - a0) * smooth(f / nf), 0, DOOR_ROT_Z); DOOR.keyframe_insert('rotation_euler', frame=f)
    for fc in act.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    DOOR.animation_data.action = None
    tr = DOOR.animation_data.nla_tracks.new(); tr.name = cn; tr.strips.new(cn, 0, act); tr.mute = True
DOOR.rotation_euler = (0, 0, DOOR_ROT_Z)
# crane extras (glTF / crane-local metres; crane-local axes = world axes, origin = footing centre on the ground)
CRANE['prop'] = 'PC-1 pad crane (hammerhead tower crane, RC-1 joint convention)'
CRANE['origin'] = 'ground centre of the footing at pad-local glTF (x %.1f, z %.1f) = world (%.1f, 0, %.1f); jib points +X at Slew = 0' % (CR_X, -(CR_Y + SHIFT), 480 + CR_X, -(CR_Y + SHIFT))
for k, v in {'slew_min_rad': -math.pi, 'slew_max_rad': math.pi, 'trolley_min_m': CR_TR_MIN, 'trolley_max_m': CR_TR_MAX,
             'hoist_min_m': round(CR_CABLE_MIN, 3), 'hoist_max_m': round(CR_CABLE_MAX, 3), 'hook_drop_m': CR_HOOK_DROP,
             'sheave_y': CR_SHEAVE, 'slew_y': CR_SLEW_Z, 'jib_y': CR_JIB_Z, 'hook_rest_local_y': round(CR_SHEAVE - 1.0 - CR_HOOK_DROP - CR_JIB_Z, 4),
             'box_size_m': [BOX[0], BOX[2], BOX[1]], 'box_hook_offset_y': BOX[2]}.items(): CRANE[k] = v
_hb = math.atan2(-CR_Y, -CR_X); _hh = math.asin((SHIP_R + 0.6) / math.hypot(CR_X, CR_Y))
CRANE['slew_keep_out_rad'] = [] if JIB_FREE else [round(_hb - _hh, 4), round(_hb + _hh, 4)]
CRANE['slew_note'] = ('free 360 deg: crane is %.1f m from the ship axis, jib tip (15 m) stays %.1f m off the hull' % (math.hypot(CR_X, CR_Y), math.hypot(CR_X, CR_Y) - CR_JIB_L - SHIP_R)) if JIB_FREE else 'see slew_keep_out_rad'
CRANE['joints'] = ('Slew: rotation.y = theta (rad) about +Y, jib direction (cos theta, 0, -sin theta). Trolley: position.x = r (glTF rest value = trolley_min_m). '
                   'Hoist: scale.y = cable length L (m). Hook: position.y = hook_rest_local_y + 1 - L (Hook world y = sheave_y - L - hook_drop_m), rotation.y = box_yaw - theta. '
                   'Solve for a hook target (x, y, z) in crane space: theta = atan2(-z, x), r = hypot(x, z), L = sheave_y - y - hook_drop_m. '
                   'If slew_keep_out_rad is not empty, never slew through it.')
CRANE['poses'] = json.dumps({k: [round(x, 4) for x in v] for k, v in POSES.items()})   # [slew, trolley r, hoist L, hook yaw] per pose
CRANE['clips'] = ', '.join('%s %.1fs' % (k, v[2]) for k, v in CLIPS.items())
# ====================================================================== stage cleanup + lights + crew
EXCL = [((0, 0), 34.0)] + [((x, y), 4.0) for x, y, _, _ in SOL] + [((RXr, RYr), 18.0)] + [((x, -30.5), 10.0) for x in range(-30, -72, -6)] + [((x, -30.5), 10.0) for x in range(-24, 12, 6)]
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
astronaut((LADDER_FOOT.x + 0.9 * math.cos(LAD_A + 0.5), LADDER_FOOT.y + 0.9 * math.sin(LAD_A + 0.5), TOP), rot_z=0.4)   # at the ladder foot
astronaut((PORT['LOX'].x + 1.8, PORT['LOX'].y - 2.2, TOP), rot_z=-0.9)          # checking the LOX hose QD
astronaut((VV.x - 1.2, VV.y - 2.0, 0.1), rot_z=0.2)                             # at the valve vault
if A.get('dress') != '1': astronaut((RECV.x, RECV.y, BAY_Z), rot_z=RECV_YAW)                              # receiver in the bay walkway, facing the FB-05 bed
cam = setup_render(64 if not QUICK else 16)

# ====================================================================== MOVE THE PAD NORTH (+SHIFT) and prove it never touches the road
for o in bpy.data.objects:
    if o.parent is None and o.type not in ('CAMERA', 'LIGHT'): o.location.y += SHIFT
bpy.context.view_layer.update()
SH = Vector((0, SHIFT, 0))
def corr_hits(o, m=0.0):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg)
    try: me = oe.to_mesh()
    except RuntimeError: return 0, 0
    M = oe.matrix_world; n = 0; tot = len(me.vertices)
    for v in me.vertices:
        w = M @ v.co
        if in_corr_w(w.x, w.y, m): n += 1
    oe.to_mesh_clear(); return n, tot
_left = [(o.name, corr_hits(o, GAP_ROAD)[0]) for o in coll('Mine').all_objects if o.type in ('MESH', 'CURVE', 'FONT') and o.get('grp') != 'Road']
_left = [t for t in _left if t[1]]
print('ROAD_GAP_HITS', _left, flush=True)
assert not _left, _left
print('RECV', gl(RECV), 'yaw', round(math.degrees(RECV_YAW), 2), 'HOME', gl(HOME), 'yaw', round(math.degrees(HOME_YAW), 2), 'dist', round((HOME - RECV).length, 3), flush=True)

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
        M = oe.matrix_world; G.setdefault('Lanes' if o.name.startswith('lane_') else o.get('grp', 'Base'), []).extend([M @ v.co for v in me.vertices]); oe.to_mesh_clear()
    return G
if 'check' in ONLY:
    G = group_pts(); ok = True
    for (w, h), (x0, x1, y0, y1) in SAFE.items():
        T, C, dd, _ = phone_cam(w, h)
        print(f'CHECK {w}x{h} band x {x0}-{x1} y {y0}-{y1}  d {dd:.3f}  cam {tuple(round(v, 2) for v in C)}', flush=True)
        for g, pts in sorted(G.items()):
            pr = project(pts, w, h); xs = [p[0] for p in pr]; ys = [p[1] for p in pr]
            bad = min(xs) < x0 + SPARE or max(xs) > x1 - SPARE or min(ys) < y0 + SPARE or max(ys) > y1 - SPARE
            info = g == 'Lanes'      # Director 22:34 final: the U-turn / road may sit just off screen (info only)
            ok &= info or not bad
            print(f'   {g:10s} x {min(xs):6.1f}-{max(xs):6.1f}  y {min(ys):6.1f}-{max(ys):6.1f}  {("(road, info) " if info else "") + ("OUT" if bad else "ok")}', flush=True)
        sp = project([Vector((0, SHIFT, TOP + 40.25)), Vector((0, SHIFT, TOP))], w, h); print(f'   ship top y {sp[0][1]:.1f} (may run above), ship base y {sp[1][1]:.1f}', flush=True)
    print('CHECK_ALL', 'PASS' if ok else 'FAIL', flush=True)

if 'glb' in ONLY: export_glb(os.path.join(OUT, f'{NAME}_master.glb'))
if 'blend' in ONLY:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'{NAME}_master.blend'), compress=True)
assert not ('game' in ONLY and set(ONLY) & {'hero', 'turn', 'portrait', 'blend', 'glb'}), 'game step is destructive: run it on its own'
if 'game' in ONLY:   # game GLB: merged SHM_* materials (vertex colours), merged per node, <=30k tris, no textures; meshopt + quantization via gltfpack
    SHJ = os.path.normpath(os.path.join(HERE, '..', '..', '_shared', 'shared_materials.json'))
    MM = json.load(open(SHJ))['merged_materials']
    # local (not in the shared json, which has only SHM_Paint metal 0 and SHM_Metal metal 0.85): brushed stainless for the ship + cargo door,
    # metal 0.5 / rough 0.42 per the 10/24 spec. qa3d has no scene.environment, so the base stays light (~#d0d4d8 per-face swatches);
    # ss_fill: small constant emissive lift for the shadow side, #1e2125 approved by the art lead 10/24 ('--ss_fill none' turns it off)
    MM = dict(MM, SHM_Stainless={'base': '#ffffff', 'metal': float(A.get('ss_metal', 0.5)), 'rough': float(A.get('ss_rough', 0.42)), 'vertex_colors': True,
                                 **({'emissive': A.get('ss_fill', '#1e2125'), 'emissive_strength': 1.0} if A.get('ss_fill', '#1e2125') != 'none' else {})})
    def shm(n):
        if n in bpy.data.materials and bpy.data.materials[n].get('shm'): return bpy.data.materials[n]
        d = MM[n]; m = bpy.data.materials.get(n) or bpy.data.materials.new(n); m['shm'] = 1; m.use_nodes = True
        nt = m.node_tree; b = nt.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = hexc(d['base']); b.inputs['Metallic'].default_value = d['metal']; b.inputs['Roughness'].default_value = d['rough']
        if d.get('vertex_colors'):
            va = nt.nodes.new('ShaderNodeVertexColor'); va.layer_name = 'Color'; nt.links.new(va.outputs['Color'], b.inputs['Base Color'])
        if 'emissive' in d: b.inputs['Emission Color'].default_value = hexc(d['emissive']); b.inputs['Emission Strength'].default_value = d['emissive_strength']
        return m
    for n in MM: shm(n)
    # master material -> (merged material, sRGB swatch baked into COLOR_0)
    MT = {'LP_White': ('SHM_Paint', '#eceff2'), 'LP_WhiteSmooth': ('SHM_Paint', '#eef1f4'), 'LP_Radiator': ('SHM_Paint', '#f2f4f7'),
          'LP_Graphite': ('SHM_Paint', '#2c3137'), 'LP_GraphiteSmooth': ('SHM_Paint', '#30353c'), 'LP_Satin': ('SHM_Metal', '#9aa3ad'),
          'LP_Rubber': ('SHM_Paint', '#1d2024'), 'LP_MLI': ('SHM_Metal', '#c9ced6'), 'LP_PadPaint': ('SHM_Paint', '#d9dcdf'), 'LP_Ink': ('SHM_Paint', '#1f2329'),
          'LP_InkWhite': ('SHM_Paint', '#f4f7fa'), 'LP_Cyan': ('SHM_GlowCyan', '#2fe3ff'), 'LP_CyanSoft': ('SHM_GlowCyan', '#2fe3ff'),
          'LP_Lamp': ('SHM_GlowWhite', '#eaf8ff'), 'LP_AmberLamp': ('SHM_Paint', '#ffb020'), 'LP_Lens': ('SHM_Paint', '#1b2a36'),
          'LP_Regolith': ('SHM_Paint', '#75787c'), 'LP_Sintered': ('SHM_Paint', '#505055'), 'LP_SinterBlock': ('SHM_Paint', '#5c5b5d'),
          'LP_LoxBand': ('SHM_Paint', '#2f9e63'), 'LP_LCH4Band': ('SHM_Paint', '#c2442c'), 'LP_WhiteFrost': ('SHM_Paint', '#f1f4f7'),
          'LP_HoseFoil': ('SHM_Metal', '#b9bfc7'), 'LP_ShipPlaceholder': ('SHM_Paint', '#8a8d94'), 'LP_ApronSinter': ('SHM_Paint', '#4e5054'),
          'LP_SolarCell': ('SHM_Paint', '#152a4a'), 'LP_LaneVC': ('SHM_Paint', None), 'SHM_Paint': ('SHM_Paint', None), 'SHM_GlowCyan': ('SHM_GlowCyan', None),
          # stainless ship swatches (game): per-sheet tone A/B/C, welds, steel bands, heat-tinted aft, solar band, hold opening
          'LP_StainlessA': ('SHM_Stainless', A.get('ss_a', '#d0d4d8')), 'LP_StainlessB': ('SHM_Stainless', A.get('ss_b', '#d9dde1')),
          'LP_StainlessC': ('SHM_Stainless', A.get('ss_c', '#c6cacf')), 'LP_StainlessWeld': ('SHM_Stainless', A.get('ss_weld', '#8f959c')),
          'LP_SteelBand': ('SHM_Stainless', A.get('ss_band', '#b2b7bd')), 'LP_StainlessHeat': ('SHM_Stainless', '#77736f'),
          'LP_ShipDark': ('SHM_Stainless', A.get('ss_dark', '#6a7079')), 'LP_ShipBay': ('SHM_Stainless', '#2a2e33'), 'LP_ShipGlow': ('SHM_Stainless', '#2fe3ff')}
    # one material per node except Pad_Base (4) and Crane (2): forced node materials
    NODE_MAT = {'Hose_LOX': 'SHM_Metal', 'Hose_LCH4': 'SHM_Metal', 'Tier_03': 'SHM_Paint', 'Tier_05': 'SHM_Paint', 'Tier_08': 'SHM_Paint',
                'Tier_12': 'SHM_GlowWhite', 'Tier_20': 'SHM_Paint', 'Ship': 'SHM_Stainless', 'Door': 'SHM_Stainless', 'Road': 'SHM_Paint'}
    NODE_NAME = {'Road': 'Road_UTurn', 'Base': GAME_NAMES['base'], 'Ship': GAME_NAMES['ship'], 'Door': GAME_NAMES['door'], 'Crane': GAME_NAMES['crane_mesh']}
    NODE_NAME.update({g: v[0] for g, v in GAME_NAMES['hoses'].items()}); NODE_NAME.update({g: v[0] for g, v in GAME_NAMES['tiers'].items()})
    KEEP_TEXT = ('decal_lox', 'decal_lch4', 'stencil_pad', 'stencil_bay')            # big readable labels stay in the game GLB
    meshes = [o for o in coll('Mine').all_objects if o.type in ('MESH', 'CURVE', 'FONT')]
    for o in meshes:
        b = o.name.split('.')[0]
        if b.startswith(('decal_', 'stencil_')) and b not in KEEP_TEXT:
            bpy.data.objects.remove(o)
    meshes = [o for o in coll('Mine').all_objects if o.type in ('MESH', 'CURVE', 'FONT') and o is not CRANE_MESH]
    for o in meshes:
        for md in list(o.modifiers):
            if md.type == 'BEVEL': o.modifiers.remove(md)
        o.hide_set(False); o.hide_render = False
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.convert(target='MESH')
    meshes = [o for o in coll('Mine').all_objects if o.type == 'MESH' and o is not CRANE_MESH]
    rng = random.Random(5); DUST = Vector(hexc('#8a8d91')[:3])
    for o in meshes:
        o.data = o.data.copy(); me = o.data; g = o.get('grp', 'Base'); Mw = o.matrix_world
        ca = me.color_attributes.get('Color')
        if ca is None or ca.domain != 'CORNER' or not o.get('vc'):
            if ca is not None: me.color_attributes.remove(ca)
            ca = me.color_attributes.new('Color', 'BYTE_COLOR', 'CORNER')
            for p in me.polygons:
                mn = me.materials[p.material_index].name.split('.')[0] if me.materials else 'LP_White'
                hx = MT.get(mn, ('SHM_Paint', '#eceff2'))[1] or '#eceff2'
                if mn not in MT: print('UNMAPPED', o.name, mn)
                c = Vector(hexc(hx)[:3]); z = (Mw @ p.center).z
                if MT.get(mn, ('SHM_Paint',))[0] == 'SHM_Paint' and z < 1.4 and g not in ('Ship', 'Door'):   # dust creeping up from the ground
                    c = c.lerp(DUST, min(0.5, (1.4 - z) / 1.4 * 0.35 + rng.uniform(0, 0.05)))
                for li in p.loop_indices: ca.data[li].color = (c.x, c.y, c.z, 1.0)
        me.color_attributes.active_color = ca
        new = [shm(NODE_MAT.get(g) or MT.get(sl.material.name.split('.')[0] if sl.material else '', ('SHM_Paint',))[0]) for sl in o.material_slots]
        for sl, m in zip(o.material_slots, new): sl.link = 'DATA'; sl.material = m
    groups = {}
    for o in meshes: groups.setdefault(o.get('grp', 'Base'), []).append(o)
    groups.pop('Marker', None)
    nodes = {}
    for g, obs in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in obs: o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        if len(obs) > 1: bpy.ops.object.join()
        G = bpy.context.active_object; G.name = NODE_NAME[g]
        if g != 'Door':
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.001); bpy.ops.object.mode_set(mode='OBJECT')
        names = [sl.material.name for sl in G.material_slots]; uniq = sorted(set(names), key=names.index)
        idx = [uniq.index(n) for n in names]; pidx = [idx[p.material_index] for p in G.data.polygons]
        G.data.materials.clear()
        for n in uniq: G.data.materials.append(bpy.data.materials[n])
        for p, i in zip(G.data.polygons, pidx): p.material_index = i
        nodes[g] = G
    nodes['Crane'] = CRANE_MESH
    tri = lambda G: sum(len(p.vertices) - 2 for p in G.data.polygons)
    T0 = sum(tri(G) for G in nodes.values()); TGT = int(A.get('tris', 29900))
    def dec(G, ratio):
        bpy.ops.object.select_all(action='DESELECT'); G.select_set(True); bpy.context.view_layer.objects.active = G
        md = G.modifiers.new('Dec', 'DECIMATE'); md.ratio = max(0.03, min(1.0, ratio)); md.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=md.name)
    CAP = {'Road': 400, 'Hose_LOX': 900, 'Hose_LCH4': 900, 'Ship': int(A.get('ship_cap', 7900)), 'Door': 300}
    for g, G in nodes.items():
        cap = CAP.get(g, 1000 if g.startswith('Tier_') else None)
        if cap and tri(G) > cap: dec(G, cap / tri(G))
    B = nodes['Base']
    for it in range(6):
        rest = sum(tri(G) for g, G in nodes.items() if g != 'Base'); t = tri(B)
        if t + rest <= TGT: break
        dec(B, (TGT - rest) / t * 0.97)
    for g, G in nodes.items(): print('NODE', G.name, tri(G), [m.name for m in G.data.materials], flush=True)
    print('GAMETRIS', T0, '->', sum(tri(G) for G in nodes.values()), 'DRAWS', sum(len(G.data.materials) for G in nodes.values()), flush=True)
    for g, G in nodes.items():
        for k in ('grp', 'vc'):
            if k in G: del G[k]
        if g in GAME_NAMES['tiers']: G['tier'] = GAME_NAMES['tiers'][g][1]; G['hidden_by_default'] = True
        if g in GAME_NAMES['hoses']:
            h = HOSE_START[g.split('_')[1]] + SH; G.data.transform(Matrix.Translation(-h)); G.location = h
            G['fuel'] = GAME_NAMES['hoses'][g][1]; G['attach_to'] = GAME_NAMES['markers']['Fuel_Hookup']
        if g == 'Ship': G.data.transform(Matrix.Translation(-SH)); G.location = SH
        if g == 'Road': G['road'] = 'U-turn at the east end of the flatbed road (not pad surface): joins the road tiles at world x 481, centre world (481, 17.5), r 4.5'
        if g == 'Ship': G['ship'] = 'stainless starter ship, game weight (lp_stainless_ship.py from the 46a9346 starter_ship_master.glb); node keeps the Ship_Placeholder name for qa3d'; G['size_m'] = [8.0, 40.25, 8.0]
    if 'grp' in CRANE: del CRANE['grp']
    PC = GAME_NAMES['phone_cam']; T = Vector(PC['target'])
    cam_e = mark(GAME_NAMES['markers']['Cam_Target'], T, {'frame_w': PC['frame_w'], 'fov_y_deg': PC['fov_y'], 'pitch_down_deg': PC['pitch'],
                 'distance_m': {'%dx%d' % k: round(phone_cam(*k)[2], 3) for k in SAFE}, 'camera_side': '+Z (glTF)',
                 'note': 'lookAt(Cam_Target), d = (frame_w/2) / (tan(fov_y/2) * aspect)'})
    MKO = [o for o in coll('Mine').all_objects if o.type == 'EMPTY']
    for o in MKO:
        if 'grp' in o: del o['grp']
    bpy.context.scene.frame_set(0)
    bpy.ops.object.select_all(action='DESELECT')
    for o in list(nodes.values()) + MKO + [CRANE]: o.select_set(True)
    for o in list(nodes.values()):
        if o.animation_data is None: continue
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{NAME}_game_raw.glb'), export_format='GLB', use_selection=True, export_yup=True,
                              export_apply=False, export_extras=True, export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False,
                              export_materials='EXPORT', export_image_format='NONE', export_texcoords=False, export_normals=True,
                              export_vertex_color='ACTIVE', export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                              export_optimize_animation_size=False, export_anim_slide_to_zero=True, export_def_bones=False,
                              export_rest_position_armature=True, export_skins=True, export_morph=False)
    print('GAMEGLB', flush=True)
HC = A.get('hc')
def dress():
    """proof dressing (Stage only, never exported): FB-05 at Truck_Stop, HELIUM-3 crates (cargo_box scaled to 3 x 2.4 x 2.4), receiver rig"""
    PR = A.get('props', '/tmp/lp0/props')
    def imp(fn):
        before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(PR, fn)); new = [o for o in bpy.data.objects if o not in before]
        for o in new:
            for c in list(o.users_collection): c.objects.unlink(o)
            coll('Stage').objects.link(o)
        return [o for o in new if o.parent is None]
    tr = imp('fb05_game_raw.glb')
    for o in tr: o.location = (TS.x, TS.y + SHIFT, 0.0); o.rotation_euler = (math.pi / 2, 0, 0) if abs(o.rotation_euler.x - math.pi / 2) < 1e-3 else o.rotation_euler
    BS = (BOX[0] / 2.3, BOX[1] / 1.3, BOX[2] / 1.5)
    def crate(base, yaw):
        for o in imp('cargo_box_game_raw.glb'):
            o.location = tuple(base); o.rotation_euler = (o.rotation_euler.x, o.rotation_euler.y, yaw); o.scale = (o.scale.x * BS[0], o.scale.y * BS[1], o.scale.z * BS[2])
    crate(PICK2 + SH, 0.0)
    for i in (0, 1, 3, 4, 6, 7): crate(BAY_SLOTS[i] + SH, 0.0)
    s0, s1, _ = CLIPS['crane_swing']; u = float(A.get('swing_u', 0.55)); sp = [a + (b - a) * smooth(u) for a, b in zip(s0, s1)]
    crane_pose(sp[0], sp[1], sp[2], sp[3] + sp[0]); bpy.context.view_layer.update()
    hw = CRANE.matrix_world @ CRANE.pose.bones['Hook'].head; crate(hw - Vector((0, 0, BOX[2])), sp[3] + sp[0])
    for o in list(coll('Stage').objects):
        if o.name.startswith(('astro', 'helmet', 'visor')) and (o.matrix_world.translation - RECV).length < 1.0: bpy.data.objects.remove(o)
    for o in imp('receiver_game_raw.glb'): o.location = tuple(RECV + SH); o.rotation_euler = (o.rotation_euler.x, o.rotation_euler.y, RECV_YAW)
    print('DRESSED', 'hook', tuple(round(c, 2) for c in hw), flush=True)
if A.get('dress') == '1': dress()
if 'hero' in ONLY:
    w, h = (int(A.get('hw', 3840)), int(A.get('hh', 2160))) if not QUICK else (960, 540)
    tgt = (2.0, 6.0, 9.0); pos = (-38.0, -86.0, 26.0)       # new layout: pad centre at Blender y +13, road at y -13 / -22
    if HC: v = [float(t) for t in HC.split(',')]; pos, tgt = tuple(v[:3]), tuple(v[3:6])
    shoot(cam, os.path.join(OUT, A.get('pname', 'hero') + '.png'), tgt, pos, w, h, lens=float(A.get('lens', 30)), samples=int(A.get('hs', 64)) if not QUICK else 16)
if 'portrait' in ONLY:   # the game camera exactly: aimed at Cam_Target, 38 deg vertical FOV, 18 deg down, no azimuth, d from frame_w + aspect
    pw, ph = int(A.get('pw', 1179)), int(A.get('ph', 2556))
    T, C, dd, half = phone_cam(pw, ph)
    print('PHONECAM', pw, ph, 'target', tuple(round(v, 3) for v in T), 'cam', tuple(round(v, 3) for v in C), 'd', round(dd, 3), flush=True)
    cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 36.0
    shoot(cam, os.path.join(OUT, A.get('pname', 'portrait') + '.png'), tuple(T), tuple(C), pw, ph, lens=18.0 / math.tan(half), samples=int(A.get('hs', 64)) if not QUICK else 16)
    cam.data.sensor_fit = 'AUTO'
if 'turn' in ONLY:
    os.makedirs(os.path.join(OUT, 'turntable'), exist_ok=True)
    turntable(cam, os.path.join(OUT, 'turntable'), (0.0, 6.0, 9.0), 150, 22, size=1000 if not QUICK else 400, samples=int(A.get('ts', 48)) if not QUICK else 12)
