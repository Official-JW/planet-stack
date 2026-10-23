"""Planet Stack - REFINERY (part of the Mine station), high-detail concept master (Blender 4.2 LTS, headless, Cycles).

blender -b -P build_refinery.py -- --out .. [--quick 1] [--only glb,blend,hero,phone,turn,diagram] [--hs 48] [--ts 40] [--ps 64]
                                   [--res WxH] [--pres WxH] [--hc x,y,z,tx,ty,tz] [--lens 24] [--ct x,y,z] [--fw W] [--mine 0|1]
                                   [--mineoff x,y] [--truckblend PATH]

Same pipeline as dock_tankfarm / life_support: Mine-B palette recipe (add_dust / P_ weathered paints), same helpers, the shared
stage from art/3d/mine_concepts/_src/mc_common.py (imported, not modified) with the shared ground material M_ground.

Blender coords: Z up, metres, front = -Y (toward the camera). Exported GLB: Y up, front +Z.
ORIGIN = Path_Dump = the HT-04 truck's centre at the dump spot. The truck reverses in along +X (cab toward -X) until its rear tyres
touch the wheel stop; its tail lip tips over the -X rim of the intake bin RB-1 (x 3.7..7.4).

Process (rows built in line coords, then placed by the compact relayout _rowM: He-3 row in front, fuel row behind, RS 0.85):
  intake bin RB-1 (grizzly, dust skirt) -> belt feeder BF-1 -> splitter SP-1 (VG-1 dropped) -> fuel: conveyor cv_fuel;
  He-3: bucket elevator BE-1 -> covered gallery cv_he3 over the fuel row
  He-3:  sieve SV-1 (<100 um) -> rotary kiln KN-1 (700 C, electric) -> gas hood + compressor CP-1 -> cold traps CT-1..4
         (H2O, CO2, N2, H2; H2 piped over the rack to the fuel line) -> cryo column DC-1 (He-3 / He-4) -> filling FS-1 -> canister rack;
         kiln tailings conveyor -> tailings pile
  fuel:  crusher CR-1 -> magnetic separator MS-1 (ilmenite) -> H2 reduction reactor RX-1 (950 C, FeTiO3 + H2 -> Fe + TiO2 + H2O)
         -> water condenser WC-1 -> electrolyzer EL-1 (H2 recycled to RX-1, O2 + extra H2 on) -> liquefier LQ-1 + RAD-1
         -> LOX-1 / LH2-1 -> header TO TANK FARM; slag / iron bin under RX-1
  support: control module CM-1 + airlock A-1 + dust shower, power masts, pipe rack + catwalk, switchgear
Review-only (Stage collection, never exported): ground, road, HT-04 truck in the dump pose (from concept_b_sleek.py --pose dump),
Mine B scene (MineB collection) beside the refinery, astronauts, Review_Cam_Target.
Game-GLB grouping: ob['grp'] (Tier_03/05/08/12/20, Kiln_Drum, Conveyor_He3, Conveyor_Fuel, Intake_Grate, Beacon_Lights; default Base);
pivots, conveyor run vectors and markers are stored as JSON in scene['game_nodes'] for _src/build_game_glb_tiered.py.
"""
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__))
MC = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'mine_concepts', '_src'))
sys.path.insert(0, MC)
import bpy, bmesh
from mathutils import Vector, Matrix, noise
from mc_common import *
from mc_common import _obj, _nodes

A = argv(); OUT = os.path.abspath(A.get('out', '/tmp/rf_out')); os.makedirs(OUT, exist_ok=True)
QUICK = A.get('quick') == '1'
reset(); rr = random.Random(57)
TAU = math.tau
NAME = 'refinery'

class grp:
    """tag every object created inside the block with ob['grp'] (game-GLB node)."""
    def __init__(s, g): s.g = g
    def __enter__(s): s.k = set(bpy.data.objects.keys()); return s
    def __exit__(s, *a):
        for n in set(bpy.data.objects.keys()) - s.k: bpy.data.objects[n]['grp'] = s.g

# ====================================================================== materials (Life Support / Dock recipe, RF_ names)
def add_dust(m, top=1.3, amt=0.8, col='#8a8c8f', upamt=0.35):
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

WHITE  = P_('RF_White', '#eceff2', rough=0.24, metal=0.0, coat=0.8, grime=0.28, grime_col='#9b9da0', wear=0.15, wear_col='#9aa3ad', panel=0.8, bevel=0.03, dirt_scale=1.5)
WHITE_S = P_('RF_WhiteSmooth', '#eef1f4', rough=0.2, metal=0.0, coat=0.9, grime=0.22, grime_col='#9b9da0', wear=0.12, wear_col='#9aa3ad', bevel=0.03)
PALE   = P_('RF_WhitePanel', '#e2e6eb', rough=0.26, metal=0.0, coat=0.7, grime=0.3, grime_col='#9b9da0', wear=0.17, wear_col='#9aa3ad', panel=0.8, bevel=0.02)
GRAPH  = P_('RF_Graphite', '#2c3137', rough=0.3, metal=0.55, coat=0.5, grime=0.22, grime_col='#6b6e72', wear=0.24, wear_col='#9aa0a6', panel=1.4, bevel=0.02)
GRAPH2 = P_('RF_Graphite2', '#30353c', rough=0.28, metal=0.6, coat=0.5, grime=0.24, grime_col='#6b6e72', wear=0.22, wear_col='#9aa0a6', panel=1.6, bevel=0.02)
STEEL  = P_('RF_Satin', '#9aa3ad', rough=0.28, metal=1.0, grime=0.25, grime_col='#5a5c60', wear=0.12, wear_col='#d0d5db', bevel=0.015)
STEELL = P_('RF_SatinLight', '#b9c0c8', rough=0.24, metal=1.0, grime=0.2, grime_col='#5a5c60', wear=0.1, wear_col='#e0e4e8', bevel=0.01)
TRIM   = P_('RF_WhiteTrim', '#e9edf1', rough=0.22, metal=0.0, coat=0.8, grime=0.22, grime_col='#9b9da0', wear=0.18, wear_col='#8f969e', bevel=0.02)
RED    = P_('RF_Red', '#b8322c', rough=0.35, metal=0.1, coat=0.5, grime=0.2, wear=0.2)
FOIL   = P_('RF_MLI', '#c9ced6', rough=0.3, metal=0.9, grime=0.2, grime_col='#5b5d60', bump_noise=0.5, bevel=0.01)
RUBBER = P_('RF_Rubber', '#1d2024', rough=0.8, metal=0.0, grime=0.3, grime_col='#6e7074', bump_noise=0.3)
PT     = P_('RF_Platinum', '#dcdfe4', rough=0.16, metal=1.0, grime=0.12, grime_col='#6a6d72', wear=0.05, wear_col='#f4f6f8', bevel=0.01)
DARKI  = P_('RF_Interior', '#25292e', rough=0.5, metal=0.3, grime=0.3, grime_col='#4a4d52', panel=0.6, bevel=0.01)
CHROME = M_paint('RF_Chrome', '#dfe3e9', rough=0.15, metal=1.0, bevel=0.005)
INK    = M_paint('RF_Ink', '#1f2329', rough=0.5, metal=0.0)
INKW   = M_paint('RF_InkWhite', '#f4f7fa', rough=0.4, metal=0.0)
GLASS  = M_glass('RF_Port', '#1b2a36', 0.04)
LAMP   = M_glow('RF_Lamp', '#f2fbff', 12)
AMBERL = M_glow('RF_StatusWhite', '#dff8ff', 9)
GREENL = M_glow('RF_GreenLamp', '#6ee08a', 7)
REDL   = M_glow('RF_RedLamp', '#f25f5c', 8)
CYANL  = M_glow('RF_Cyan', '#2fe3ff', 10)
CYANS  = M_glow('RF_CyanSoft', '#2fe3ff', 4)
NEON   = M_glow('RF_NeonBlue', '#3d8bff', 16)

def M_he3_glow(name='RF_He3'):
    """glowing blue He-3 core (no transmission): noisy blue emission."""
    m = bpy.data.materials.new(name); nt, b = _nodes(m)
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 5; nz.inputs['Detail'].default_value = 6
    link(nt, tc.outputs['Object'], nz.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = hexc('#0636c8'); ramp.color_ramp.elements[1].color = hexc('#1f9dff')
    link(nt, nz.outputs['Fac'], ramp.inputs['Fac'])
    link(nt, ramp.outputs['Color'], b.inputs['Base Color']); link(nt, ramp.outputs['Color'], b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value = 4.0; b.inputs['Roughness'].default_value = 0.15
    m.diffuse_color = hexc('#3ab0ff'); return m
HE3 = M_he3_glow()

def M_radiator(name='RF_Radiator'):
    m = bpy.data.materials.new(name); nt, b = _nodes(m)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    b.inputs['Base Color'].default_value = hexc('#e8edf5'); b.inputs['Roughness'].default_value = 0.42
    b.inputs['Coat Weight'].default_value = 0.3; b.inputs['Coat Roughness'].default_value = 0.15
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'; wv.inputs['Scale'].default_value = 1.6
    wv.wave_profile = 'SAW'; link(nt, tc.outputs['Object'], wv.inputs['Vector'])
    br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 1.0; br.inputs['Brick Width'].default_value = 1.0
    br.inputs['Row Height'].default_value = 1.5; br.inputs['Mortar Size'].default_value = 0.012; br.offset = 0.0
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); link(nt, tc.outputs['Object'], sep.inputs['Vector'])
    cx = nt.nodes.new('ShaderNodeCombineXYZ'); link(nt, sep.outputs['X'], cx.inputs['X']); link(nt, sep.outputs['Z'], cx.inputs['Y'])
    link(nt, cx.outputs[0], br.inputs['Vector'])
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'SUBTRACT'; link(nt, wv.outputs['Fac'], ad.inputs[0]); link(nt, br.outputs['Fac'], ad.inputs[1])
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35; bump.inputs['Distance'].default_value = 0.01
    link(nt, ad.outputs[0], bump.inputs['Height']); link(nt, bump.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = hexc('#e8edf5')
    return add_dust(m, top=1.6, amt=0.55, upamt=0.2)
RAD = M_radiator()

def M_cells(name='RF_SolarCells'):
    m = bpy.data.materials.new(name); nt, b = _nodes(m)
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); link(nt, tc.outputs['Object'], sep.inputs['Vector'])
    cx = nt.nodes.new('ShaderNodeCombineXYZ'); link(nt, sep.outputs['X'], cx.inputs['X']); link(nt, sep.outputs['Z'], cx.inputs['Y'])
    br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 1.0; br.inputs['Brick Width'].default_value = 0.5
    br.inputs['Row Height'].default_value = 0.5; br.inputs['Mortar Size'].default_value = 0.02; br.offset = 0.0
    br.inputs['Color1'].default_value = hexc('#1b2a4a'); br.inputs['Color2'].default_value = hexc('#22345a'); br.inputs['Mortar'].default_value = hexc('#9aa3b5')
    link(nt, cx.outputs[0], br.inputs['Vector']); link(nt, br.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Metallic'].default_value = 0.35; b.inputs['Roughness'].default_value = 0.22
    b.inputs['Coat Weight'].default_value = 0.6; b.inputs['Coat Roughness'].default_value = 0.05
    m.diffuse_color = hexc('#1b2a4a'); return m
CELLS = M_cells()

def M_pad(name='RF_Pad'):
    """sintered-regolith yard pad: 2 m grey tiles, dark joints, patchy dust (all neutral grey)."""
    m = bpy.data.materials.new(name); nt, b = _nodes(m); N = nt.nodes
    tc = N.new('ShaderNodeTexCoord')
    br = N.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 1.0; br.inputs['Brick Width'].default_value = 2.0
    br.inputs['Row Height'].default_value = 2.0; br.inputs['Mortar Size'].default_value = 0.02; br.offset = 0.5; br.inputs['Bias'].default_value = 0.0
    br.inputs['Color1'].default_value = hexc('#6b6d71'); br.inputs['Color2'].default_value = hexc('#7a7c80'); br.inputs['Mortar'].default_value = hexc('#3f4145')
    link(nt, tc.outputs['Object'], br.inputs['Vector'])
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.25; nz.inputs['Detail'].default_value = 8; link(nt, tc.outputs['Object'], nz.inputs['Vector'])
    mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.4; mr.inputs['From Max'].default_value = 0.7; mr.inputs['To Max'].default_value = 0.6
    link(nt, nz.outputs['Fac'], mr.inputs['Value'])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; link(nt, mr.outputs[0], mx.inputs['Factor']); link(nt, br.outputs['Color'], mx.inputs[6]); mx.inputs[7].default_value = hexc('#8b8d90')
    nz2 = N.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 3.0; nz2.inputs['Detail'].default_value = 10; link(nt, tc.outputs['Object'], nz2.inputs['Vector'])
    mr2 = N.new('ShaderNodeMapRange'); mr2.inputs['From Min'].default_value = 0.3; mr2.inputs['From Max'].default_value = 0.7; mr2.inputs['To Min'].default_value = 0.85; mr2.inputs['To Max'].default_value = 1.08
    link(nt, nz2.outputs['Fac'], mr2.inputs['Value'])
    mm = N.new('ShaderNodeMix'); mm.data_type = 'RGBA'; mm.blend_type = 'MULTIPLY'; mm.inputs['Factor'].default_value = 1.0
    link(nt, mx.outputs[2], mm.inputs[6]); cc = N.new('ShaderNodeCombineColor')
    for i in range(3): link(nt, mr2.outputs[0], cc.inputs[i])
    link(nt, cc.outputs[0], mm.inputs[7]); link(nt, mm.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.9
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.5; bump.inputs['Distance'].default_value = 0.02; bump.invert = True
    link(nt, br.outputs['Fac'], bump.inputs['Height']); link(nt, bump.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = hexc('#74767a'); return m
PADM = M_pad()
ROADM = M_rock('RF_Road', '#5d5f63', '#77797d')

# ====================================================================== helpers (Life Support helpers, same signatures)
def lbox(name, size, loc, rot, mat, bevel=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    ob = _obj(bm, name, mat, bevel=bevel); ob.location = loc; ob.rotation_euler = rot; return ob

def lathe(name, prof, loc, mat, segs=40, bevel=0.0):
    bm = bmesh.new(); rings = []
    for (r, z) in prof:
        if r < 1e-5: rings.append([bm.verts.new((loc[0], loc[1], loc[2] + z))])
        else: rings.append([bm.verts.new((loc[0] + r * math.cos(TAU * k / segs), loc[1] + r * math.sin(TAU * k / segs), loc[2] + z)) for k in range(segs)])
    for a, b2 in zip(rings, rings[1:]):
        for k in range(segs):
            k2 = (k + 1) % segs
            if len(a) == 1: bm.faces.new((a[0], b2[k], b2[k2]))
            elif len(b2) == 1: bm.faces.new((a[k], a[k2], b2[0]))
            else: bm.faces.new((a[k], a[k2], b2[k2], b2[k]))
    if len(rings[0]) > 1: bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(bm, name, mat, smooth=True, angle=50, bevel=bevel)

def dome_prof(r, z0, z1, n=8, dome=0.5, bottom='flat', bdepth=0.0):
    p = []
    if bottom == 'cone': p += [(0.18 * r, z0 - bdepth), (r, z0)]
    elif bottom == 'dish': p += [(0, z0 - r * dome)] + [(r * math.sin(a), z0 - r * dome * math.cos(a)) for a in [i / n * math.pi / 2 for i in range(1, n)]] + [(r, z0)]
    else: p += [(r, z0)]
    p += [(r, z1)] + [(r * math.cos(a), z1 + r * dome * math.sin(a)) for a in [i / n * math.pi / 2 for i in range(1, n)]] + [(0, z1 + r * dome)]
    return p

def vvessel(name, xy, r, z0, z1, mat, bottom='flat', bdepth=0.0, segs=40, dome=0.5, bands=(), band_mat=None):
    ob = lathe(name, dome_prof(r, z0, z1, dome=dome, bottom=bottom, bdepth=bdepth), (xy[0], xy[1], 0), mat, segs=segs)
    for zb in bands: cyl(name + '_band', r * 1.025, 0.12, (xy[0], xy[1], zb), band_mat or GRAPH, segs=segs, bevel=0.01)
    if bands: cyl(name + '_cyan', r * 1.012, 0.035, (xy[0], xy[1], bands[-1] + 0.16), CYANL, segs=segs)
    return ob

def pipe(name, pts, r, mat, bend=0.35, res=3, c='Mine', flanges=True):
    P = [Vector(p) for p in pts]; out = [P[0]]
    for i in range(1, len(P) - 1):
        a, b, c2 = P[i - 1], P[i], P[i + 1]
        d1 = (b - a); d2 = (c2 - b); rb = min(bend, d1.length * 0.45, d2.length * 0.45)
        p0 = b - d1.normalized() * rb; p2 = b + d2.normalized() * rb
        for k in range(6):
            t = k / 5; out.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t * t * p2)
    out.append(P[-1])
    ob = curve_tube(name, [tuple(p) for p in out], r, mat, c=c, res=res)
    if flanges:
        for p, q in ((P[0], P[1]), (P[-1], P[-2])):
            d = (q - p).normalized(); rod(name + '_flange', p + d * 0.02, p + d * 0.1, r * 1.45, STEEL, segs=16, c=c)
    return ob

def rail(name, pts, mat, h=1.05, post=1.4, c='Mine'):
    P = [Vector(p) for p in pts]
    for a, b in zip(P, P[1:]):
        up = Vector((0, 0, h)); rod(name, a + up, b + up, 0.03, mat, segs=8, c=c); rod(name, a + up * 0.5, b + up * 0.5, 0.022, mat, segs=8, c=c)
        n = max(1, int((b - a).length / post))
        for i in range(n + 1):
            p = a.lerp(b, i / n); rod(name + '_post', p, p + up, 0.028, mat, segs=8, c=c)

def ladder(name, x, y, z0, z1, along='x', mat=None, c='Mine'):
    mat = mat or STEELL; dx, dy = (0.22, 0) if along == 'x' else (0, 0.22)
    for s in (-1, 1): rod(name + '_rail', (x + s * dx, y + s * dy, z0), (x + s * dx, y + s * dy, z1 + 0.9), 0.025, mat, segs=8, c=c)
    for i in range(int((z1 - z0) / 0.3) + 1):
        z = z0 + 0.25 + i * 0.3
        if z < z1 + 0.1: rod(name + '_rung', (x - dx, y - dy, z), (x + dx, y + dy, z), 0.016, mat, segs=6, c=c)

def stencil(name, body, loc, face, size, mat=INK, ex=0.006):
    rot = {'-y': (math.pi / 2, 0, 0), '+y': (math.pi / 2, 0, math.pi), '+x': (math.pi / 2, 0, math.pi / 2), '-x': (math.pi / 2, 0, -math.pi / 2)}[face]
    ob = text(name, body, loc, rot, size, mat, extrude=ex)
    ob.visible_shadow = False
    return ob

def plate(name, body, loc, face, w, h, size, bg=INK, fg=INKW, sub=None):
    off = {'-y': (0, -1), '+y': (0, 1), '+x': (1, 0), '-x': (-1, 0)}[face]
    sz = (w, 0.03, h) if face in ('-y', '+y') else (0.03, w, h)
    box(name, sz, loc, bg, bevel=0.008)
    p = (loc[0] + off[0] * 0.02, loc[1] + off[1] * 0.02, loc[2] + (h * 0.14 if sub else 0))
    stencil('st_' + name + '_t', body, p, face, size, fg)
    if sub: stencil('st_' + name + '_s', sub, (p[0], p[1], loc[2] - h * 0.24), face, size * 0.42, fg)

def lamp(name, loc, mat, r=0.09):
    cyl(name + '_base', r * 1.1, r * 0.9, (loc[0], loc[1], loc[2] - r * 0.9), GRAPH, segs=12)
    sphere(name, r, loc, mat, sub=2)

def radiator_array(name, x0, y0, y1, z0, h, n, axis='y'):
    def P(a, b, z): return (x0, a, z) if axis == 'y' else (a, x0, z)
    L = (y1 - y0); w = L / n; rz = math.pi / 2 if axis == 'y' else 0.0
    for i in range(n):
        c = y0 + w * (i + 0.5)
        lbox(name + '_panel', (w - 0.12, 0.07, h), P(c, 0, z0 + h / 2), (0, 0, rz), RAD, bevel=0.01)
        for zz in (z0 + 0.03, z0 + h - 0.03):
            beam(name + '_edge', P(c - w / 2 + 0.06, 0, zz), P(c + w / 2 - 0.06, 0, zz), 0.1, 0.06, STEELL)
    for k in range(n + 1):
        c = y0 + w * k
        beam(name + '_post', P(c, 0, 0.0), P(c, 0, z0 + h + 0.25), 0.16, 0.16, STEEL)
        box(name + '_foot', (0.6, 0.6, 0.14), P(c, 0, 0.07), GRAPH, bevel=0.02)
        if k in (0, n):
            for s_ in (-1, 1):
                q = (x0 + s_ * 1.4, c, 0.03) if axis == 'y' else (c, x0 + s_ * 1.4, 0.03)
                beam(name + '_rake', q, P(c, 0, z0 + h * 0.6), 0.1, 0.1, STEEL)
    for zz in (z0 - 0.12, z0 + h + 0.12):
        rod(name + '_manifold', P(y0, 0, zz), P(y1, 0, zz), 0.09, STEELL, segs=12)

def handwheel(name, p, r=0.32, axis='z', mat=None):
    mat = mat or STEELL; p = Vector(p); A_ = [i / 24 * TAU for i in range(25)]
    if axis == 'z': pts = [(p.x + r * math.cos(a), p.y + r * math.sin(a), p.z) for a in A_]
    elif axis == 'y': pts = [(p.x + r * math.cos(a), p.y, p.z + r * math.sin(a)) for a in A_]
    else: pts = [(p.x, p.y + r * math.cos(a), p.z + r * math.sin(a)) for a in A_]
    curve_tube(name, pts, 0.022, mat)
    for k in range(3): rod(name + '_spoke', p, Vector(pts[k * 8]), 0.014, mat, segs=6)

def valve(name, p, axis='x', r=0.24, wheel=True, actuator=False):
    """cryo gate valve: body + extended bonnet + handwheel / actuator on top."""
    p = Vector(p); d = {'x': Vector((1, 0, 0)), 'y': Vector((0, 1, 0))}[axis]
    rod(name + '_body', p - d * r * 1.3, p + d * r * 1.3, r * 1.35, STEELL, segs=20)
    for s in (-1, 1): rod(name + '_flange', p + d * s * r * 1.3, p + d * s * r * 1.5, r * 1.6, STEEL, segs=20)
    rod(name + '_bonnet', p, p + Vector((0, 0, r + 0.9)), r * 0.42, WHITE_S, segs=14)
    cyl(name + '_yoke', r * 0.6, 0.18, (p.x, p.y, p.z + r + 0.95), GRAPH2, segs=14)
    if actuator:
        box(name + '_act', (0.36, 0.36, 0.42), (p.x, p.y, p.z + r + 1.25), TRIM, bevel=0.04)
        lamp(name + '_lamp', (p.x + 0.2, p.y - 0.2, p.z + r + 1.4), GREENL, 0.035)
    elif wheel: handwheel(name + '_wheel', (p.x, p.y, p.z + r + 1.1), 0.3)

def wrap_cyl(ob, cx, cy, r, gap=0.01):
    """bend a '-y' facing flat stencil (already a mesh) onto the front of a vertical cylinder of radius r."""
    mw = ob.matrix_world.copy(); iw = mw.inverted()
    ws = [mw @ v.co for v in ob.data.vertices]; plane = min(w.y for w in ws)
    for v, w in zip(ob.data.vertices, ws):
        dx = w.x - cx; y = cy - math.sqrt(max(r * r - dx * dx, 0.0)) - gap + (w.y - plane)
        v.co = iw @ Vector((w.x, y, w.z))

def to_mesh(ob):
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH'); return bpy.context.view_layer.objects.active

def tank_label(name, body, sub, x, y, r, z, size=0.78):
    t = to_mesh(stencil('st_' + name, body, (x, y - r - 0.02, z), '-y', size, INK, ex=0.008)); wrap_cyl(t, x, y, r)
    if sub:
        s = to_mesh(stencil('st_' + name + '_s', sub, (x, y - r - 0.02, z - size * 0.75), '-y', size * 0.28, INK, ex=0.006)); wrap_cyl(s, x, y, r)

def hprof(hw, wh, cr, n=18):
    """hall cross-section: vertical walls + elliptical shoulder roof (rounded, no dome / no glass)."""
    P = [(-hw, 0.0)]
    for i in range(n + 1):
        t = math.pi - math.pi * i / n; P.append((hw * math.cos(t), wh + (cr - wh) * math.sin(t)))
    P.append((hw, 0.0)); return P

def shell(name, P, t, y0, y1, mat, bevel=0.0):
    """hollow extrusion of an open (x,z) profile along Y; wall thickness t inward."""
    bm = bmesh.new(); n = len(P); Nn = []
    for i in range(n):
        acc = Vector((0.0, 0.0))
        for j in (i - 1, i):
            if 0 <= j < n - 1:
                dx = P[j + 1][0] - P[j][0]; dz = P[j + 1][1] - P[j][1]; L = math.hypot(dx, dz)
                if L > 1e-6: acc += Vector((dz / L, -dx / L))
        Nn.append(acc.normalized())
    Q = [(P[i][0] + Nn[i].x * t, P[i][1] + Nn[i].y * t) for i in range(n)]
    O = {y: [bm.verts.new((p[0], y, p[1])) for p in P] for y in (y0, y1)}
    I = {y: [bm.verts.new((q[0], y, q[1])) for q in Q] for y in (y0, y1)}
    for i in range(n - 1):
        bm.faces.new((O[y0][i], O[y0][i + 1], O[y1][i + 1], O[y1][i]))
        bm.faces.new((I[y0][i], I[y1][i], I[y1][i + 1], I[y0][i + 1]))
        for y in (y0, y1): bm.faces.new((O[y][i], I[y][i], I[y][i + 1], O[y][i + 1]))
    for i in (0, n - 1): bm.faces.new((O[y0][i], O[y1][i], I[y1][i], I[y0][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(bm, name, mat, smooth=True, angle=30, bevel=bevel)

def prism(name, poly, y0, y1, mat, bevel=0.03):
    bm = bmesh.new(); a = [bm.verts.new((x, y0, z)) for x, z in poly]; b = [bm.verts.new((x, y1, z)) for x, z in poly]
    bm.faces.new(a); bm.faces.new(list(reversed(b))); n = len(poly)
    for i in range(n):
        j = (i + 1) % n; bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(bm, name, mat, smooth=True, angle=30, bevel=bevel)

GAME = {'pivots': {}, 'markers': {}}
GAME['extras'] = {}
HOT    = M_glow('RF_HeatGlow', '#ff7a2a', 14)
HOTS   = M_glow('RF_HeatSoft', '#ff8a3a', 5)
FROST  = P_('RF_Frost', '#f4f8fc', rough=0.62, metal=0.0, coat=0.2, grime=0.12, grime_col='#c9d3dd', bump_noise=0.6, bevel=0.01)
H2OP   = P_('RF_PipeH2O', '#2f6fc0', rough=0.4, metal=0.1, coat=0.4, grime=0.18, wear=0.12)
O2P    = P_('RF_PipeO2', '#2f9e63', rough=0.4, metal=0.1, coat=0.4, grime=0.18, wear=0.12)
IRON   = P_('RF_Iron', '#4a4e54', rough=0.45, metal=0.9, grime=0.3, grime_col='#3a3c40', bump_noise=0.4)
ORE    = M_rock('RF_Ore', '#5d5f62', '#7f8185')
SLAG   = M_rock('RF_Slag', '#45474b', '#66686c')
TAIL   = M_rock('RF_Tailings', '#6a6c70', '#8a8c90')
PADM   = M_pad('RF_Pad'); ROADM = M_rock('RF_Road', '#5d5f63', '#77797d')
MOVING = ('Kiln_Drum', 'Conveyor_He3', 'Conveyor_Fuel', 'Intake_Grate', 'Beacon_Lights')

def tower(nm, x, y, z0, z1, w=0.9, mat=None):
    """4-post braced steel support tower."""
    mat = mat or STEEL
    for sx in (-1, 1):
        for sy in (-1, 1): box(nm + '_post', (0.14, 0.14, z1 - z0), (x + sx * w / 2, y + sy * w / 2, (z0 + z1) / 2), mat, bevel=0.01)
    for sx in (-1, 1):
        beam(nm + '_brace', (x + sx * w / 2, y - w / 2, z0 + 0.1), (x + sx * w / 2, y + w / 2, z1 - 0.1), 0.06, 0.06, mat)
    box(nm + '_foot', (w + 0.4, w + 0.4, 0.12), (x, y, z0 + 0.06), GRAPH, bevel=0.02)

def hood(name, p0, p1, a, b, r, mat, n=12):
    """half-pipe conveyor cover between fractions a..b of p0->p1 (radius r, sits on the stringers)."""
    A_, B_, L, Rm = frame_from(Vector(p0), Vector(p1)); M = Matrix.Translation(A_) @ Rm.to_4x4()
    bm = bmesh.new(); rings = []
    for x in (a * L, b * L):
        rings.append([bm.verts.new(M @ Vector((x, r * math.cos(math.pi * k / n), 0.06 + r * math.sin(math.pi * k / n)))) for k in range(n + 1)])
    for k in range(n): bm.faces.new((rings[0][k], rings[0][k + 1], rings[1][k + 1], rings[1][k]))
    ob = _obj(bm, name, mat, smooth=True, angle=40)
    md = ob.modifiers.new('sol', 'SOLIDIFY'); md.thickness = 0.04; md.offset = 1.0
    return ob

def conveyor(tag, p0, p1, w=0.8, cover=(0.08, 0.92), gaps=2, run_grp=None, pitch=0.7, legs=True, ore=True):
    """troughed belt conveyor p0 (tail) -> p1 (head): stringers, idlers, belt, return, covers with viewing gaps, trestles.
    run_grp: the moving cleats + riding ore go into this game node (clip translates them one pitch along the belt, loop)."""
    p0, p1 = Vector(p0), Vector(p1); A_, B_, L, Rm = frame_from(p0, p1); d = (p1 - p0).normalized(); s = Rm.col[1]; u = Rm.col[2]
    for sy in (-1, 1):
        beam(tag + '_stringer', p0 + s * sy * (w / 2 + 0.08), p1 + s * sy * (w / 2 + 0.08), 0.12, 0.24, GRAPH2, bevel=0.01)
        box(tag + '_strip_cyan', (0.04, 0.04, 0.04), tuple(p0), CYANL) if False else None
        beam(tag + '_cyan', p0 + s * sy * (w / 2 + 0.145) + d * 0.3, p1 + s * sy * (w / 2 + 0.145) - d * 0.3, 0.012, 0.04, CYANS, bevel=0.0)
    beam(tag + '_belt', p0 + u * 0.13, p1 + u * 0.13, 0.03 if False else w, 0.03, RUBBER, bevel=0.0) if False else None
    bb = beam(tag + '_belt', p0 + u * 0.13, p1 + u * 0.13, w, 0.035, RUBBER, bevel=0.0)
    beam(tag + '_return', p0 - u * 0.14, p1 - u * 0.14, w * 0.9, 0.025, RUBBER, bevel=0.0)
    for sy in (-1, 1): beam(tag + '_skirtb', p0 + u * 0.2 + s * sy * (w / 2 - 0.02), p1 + u * 0.2 + s * sy * (w / 2 - 0.02), 0.03, 0.14, RUBBER, bevel=0.0)
    n = max(2, int(L / 1.1))
    for i in range(n + 1):
        q = p0.lerp(p1, i / n)
        rod(tag + '_idler', q + u * 0.06 - s * w / 2, q + u * 0.06 + s * w / 2, 0.06, STEELL, segs=10)
    for q, rr_ in ((p0, 0.24), (p1, 0.28)):
        rod(tag + '_pulley', q - s * (w / 2 + 0.02), q + s * (w / 2 + 0.02), rr_, GRAPH, segs=24)
    m_ = p1 + s * (w / 2 + 0.35)
    rod(tag + '_motor', m_, m_ + s * 0.55, 0.2, WHITE_S, segs=18); box(tag + '_gearbox', (0.4, 0.3, 0.4), tuple(p1 + s * (w / 2 + 0.2)), GRAPH2, bevel=0.03)
    if cover:
        segs_ = []; a0, a1 = cover; k = gaps * 2 + 1
        for j in range(k):
            if j % 2 == 0: segs_.append((a0 + (a1 - a0) * j / k, a0 + (a1 - a0) * (j + 1) / k))
        for a, b in segs_:
            hood(tag + '_cover', p0, p1, a, b, w / 2 + 0.12, WHITE_S)
            for f in (a, b):
                q = p0.lerp(p1, f); rod(tag + '_cover_rib', q - d * 0.04, q + d * 0.04, w / 2 + 0.17, GRAPH, segs=20)
    if legs:
        nl = max(1, int(L / 3.2))
        for i in range(nl + 1):
            q = p0.lerp(p1, 0.06 + 0.88 * i / nl)
            if q.z < 0.7: continue
            for sy in (-1, 1): box(tag + '_leg', (0.12, 0.12, q.z - 0.15), tuple(q + s * sy * (w / 2 + 0.08) - Vector((0, 0, (q.z + 0.15) / 2))), STEEL, bevel=0.01)
            beam(tag + '_legx', q - s * (w / 2 + 0.08) - Vector((0, 0, q.z * 0.55)), q + s * (w / 2 + 0.08) - Vector((0, 0, 0.3)), 0.06, 0.06, STEEL)
            for sy in (-1, 1): box(tag + '_legfoot', (0.36, 0.36, 0.08), tuple(Vector((q.x, q.y, 0.04)) + s * sy * (w / 2 + 0.08)), GRAPH, bevel=0.01)
    if run_grp:
        before = set(bpy.data.objects.keys()); rs = random.Random(hash(tag) % 997)
        m = int((L - 0.6) / pitch)
        for i in range(m):
            q = p0 + d * (0.3 + i * pitch) + u * 0.15
            beam(tag + '_cleat', q - s * (w / 2 - 0.06), q + s * (w / 2 - 0.06), 0.05, 0.1, GRAPH, bevel=0.0, up=u)
            if ore:
                for j in range(2):
                    c_ = q - d * (0.2 + 0.25 * j) + s * rs.uniform(-w / 3, w / 3) + u * 0.1
                    sphere(tag + '_ore', rs.uniform(0.09, 0.15), tuple(c_), ORE, scale=(1, 0.85, 0.7), sub=1, jitter=0.3, smooth=False, seed=rs.random())
        for nme in set(bpy.data.objects.keys()) - before: bpy.data.objects[nme]['grp'] = run_grp
        GAME.setdefault('conveyors', {})[run_grp] = tuple(d * pitch)
        GAME['pivots'][run_grp] = tuple(p0)
    return d, s, u

def chute(name, top, bot, w, mat=None):
    beam(name, top, bot, w, w * 0.8, mat or GRAPH2, bevel=0.02)

def label(tag, body, sub, loc, w=None, size=0.26, face='-y', post=True):
    w = w or max(1.0, 0.62 * size * max(len(body), len(sub or '') * 0.42) + 0.3)
    h = size * (2.0 if sub else 1.45)
    plate(tag, body, loc, face, w, h, size, sub=sub)
    if post and loc[2] - h / 2 > 0.25:
        dy = 0.06 if face == '-y' else -0.06
        for dx in (-w / 2 + 0.12, w / 2 - 0.12):
            if face in ('-y', '+y'): box(tag + '_post', (0.06, 0.06, loc[2] - h / 2), (loc[0] + dx, loc[1] + dy, (loc[2] - h / 2) / 2), STEEL, bevel=0.0)

def pad(name, x0, x1, y0, y1, z=0.1):
    box(name, (x1 - x0, y1 - y0, z * 2), ((x0 + x1) / 2, (y0 + y1) / 2, 0.0), PADM, bevel=0.04)
    for (a, b) in (((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)), ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1))):
        beam(name + '_curb', (a[0], a[1], z + 0.04), (b[0], b[1], z + 0.04), 0.22, 0.14, GRAPH, bevel=0.02)
ZP = 0.1
# ---- COMPACT STATION LAYOUT. The Refinery must sit inside the Mine's W = 37 station frame (x 6-94 %, y 100-650 px on 393x852),
# south of the haul loop, west of the access road and east of the frame edge. The two process rows are still built below in their
# original line coordinates (He-3 line along y = HY, fuel line along y = FY, flow +X) and then placed by M_H / M_F:
# mirrored in X (flow runs east, away from the intake), scaled RS and dropped into the field. Crew-scale parts (intake bin, CM-1,
# airlock, catwalk, stair tower) and all station connectors are built 1:1 directly in station coords.
RS = 0.85
def _rowM(c, ty, y_ref, s=RS):
    M = Matrix.Identity(4); M[0][0] = -s; M[1][1] = s; M[2][2] = s; M[0][3] = c; M[1][3] = ty - s * y_ref
    return M
M_H = _rowM(11.1, -33.3, -15.0)    # He-3 row: front row (camera side)
M_F = _rowM(12.5, -10.9, 14.3)     # fuel row: back row, just south of the haul loop
def RH(p): return tuple(M_H @ Vector(p))
def RF(p): return tuple(M_F @ Vector(p))
_BLK = {'cur': 'misc', 'seen': set(o.name for o in bpy.data.objects)}
def _blk(name):
    for o in bpy.data.objects:
        if o.name not in _BLK['seen']: o['blk'] = _BLK['cur']; _BLK['seen'].add(o.name)
    _BLK['cur'] = name
_blk('pads')
pad('pad_intake', 3.6, 6.1, -2.6, 2.3)      # starts at the wheel stop: the truck itself stands on the Mine's haul road (ground level)
pad('pad_feed', 2.7, 5.55, -8.5, -2.62)
pad('pad_he3', 9.8, 36.0, -11.0, -4.6)
pad('pad_fuel', 9.8, 38.0, 4.6, 13.2)

# ====================================================================== 1. INTAKE: drive-up tipping bin RB-1, grizzly, belt feeder, vibrating grizzly, splitter
# Origin = Path_Dump = truck centre at the dump spot. Truck reverses in along +X (cab toward -X); its tail lip tips over the bin's -X rim.
BX0, BX1, BY, BRIM, BBOT = 3.72, 6.2, 1.92, 1.40, 0.55
# wheel stop (rear tyres touch it) + approach apron with cyan guide lines
box('rb_wheelstop', (0.32, 2.9, 0.36), (BX0 + 0.08, 0, ZP + 0.18), GRAPH, bevel=0.04)
for sy in (-1, 1): box('rb_wheelstop_cyan', (0.33, 0.5, 0.04), (BX0 + 0.08, sy * 1.1, ZP + 0.37), CYANS, bevel=0.0)
# hopper body: sloped steel walls, top rim, legs
bm = bmesh.new()
top = [(BX0, -BY), (BX1, -BY), (BX1, BY), (BX0, BY)]; bot = [(4.2, -0.55), (5.4, -0.55), (5.4, 0.55), (4.2, 0.55)]
vt = [bm.verts.new((x, y, BRIM)) for x, y in top]; vb = [bm.verts.new((x, y, BBOT)) for x, y in bot]
for i in range(4): j = (i + 1) % 4; bm.faces.new((vt[i], vt[j], vb[j], vb[i]))
ob = _obj(bm, 'rb_hopper', WHITE, smooth=True, angle=30)
md = ob.modifiers.new('sol', 'SOLIDIFY'); md.thickness = 0.08; md.offset = 1.0
for (a, b) in ((top[0], top[1]), (top[1], top[2]), (top[2], top[3]), (top[3], top[0])):
    beam('rb_rim', (a[0], a[1], BRIM + 0.08), (b[0], b[1], BRIM + 0.08), 0.24, 0.18, GRAPH, bevel=0.02)
for k in range(4):
    beam('rb_band', (BX0 + 0.05, -BY - 0.05 + 0.0, BRIM - 0.25 - k * 0.001), (BX1 - 0.05, -BY - 0.05, BRIM - 0.25), 0.03, 0.1, GRAPH2, bevel=0.0) if k == 0 else None
beam('rb_cyan', (BX0 + 0.2, -BY - 0.13, BRIM - 0.05), (BX1 - 0.2, -BY - 0.13, BRIM - 0.05), 0.02, 0.05, CYANL, bevel=0.0)
for x, y in ((BX0 + 0.15, -BY + 0.15), (BX1 - 0.15, -BY + 0.15), (BX0 + 0.15, BY - 0.15), (BX1 - 0.15, BY - 0.15)):
    box('rb_leg', (0.26, 0.26, BRIM - ZP), (x, y, (BRIM + ZP) / 2), GRAPH2, bevel=0.02)
    box('rb_legfoot', (0.5, 0.5, 0.1), (x, y, ZP + 0.05), GRAPH, bevel=0.02)
for sy in (1,): beam('rb_legx', (BX0 + 0.15, sy * (BY - 0.15), ZP + 0.2), (BX1 - 0.15, sy * (BY - 0.15), BRIM - 0.2), 0.1, 0.1, STEEL)
# dust skirt: frame on 3 sides (open toward the truck), rubber curtains, spray bar, back splash plate
for x, y in ((BX0 + 0.1, -BY - 0.1), (BX1 + 0.05, -BY - 0.1), (BX0 + 0.1, BY + 0.1), (BX1 + 0.05, BY + 0.1)):
    box('ds_post', (0.16, 0.16, 3.9 - BRIM), (x, y, (3.9 + BRIM) / 2), STEEL, bevel=0.01)
for sy in (-1, 1): beam('ds_toprail', (BX0 + 0.1, sy * (BY + 0.1), 3.9), (BX1 + 0.05, sy * (BY + 0.1), 3.9), 0.16, 0.22, WHITE_S, bevel=0.02)
beam('ds_toprail', (BX1 + 0.05, -BY - 0.1, 3.9), (BX1 + 0.05, BY + 0.1, 3.9), 0.16, 0.22, WHITE_S, bevel=0.02)
for sy in (-1, 1):
    for k in range(12):
        x = BX0 + 0.35 + k * (BX1 - BX0 - 0.5) / 11
        box('ds_curtain', (0.28, 0.025, 2.1), (x, sy * (BY + 0.12), 3.8 - 1.05), RUBBER, rot=(rr.uniform(-0.03, 0.03), 0, 0), bevel=0.0)
    beam('ds_curtain_bar', (BX0 + 0.1, sy * (BY + 0.14), 3.72), (BX1 + 0.05, sy * (BY + 0.14), 3.72), 0.05, 0.1, GRAPH2, bevel=0.0)
box('ds_splash', (0.08, 2 * BY + 0.2, 2.4), (BX1 + 0.1, 0, BRIM + 1.2), WHITE, bevel=0.02)
for k in range(6): box('ds_splash_rib', (0.12, 0.08, 2.3), (BX1 + 0.17, -BY + 0.3 + k * (2 * BY - 0.6) / 5, BRIM + 1.2), GRAPH2, bevel=0.01)
rod('ds_spraybar', (BX1 - 0.05, -BY, 3.55), (BX1 - 0.05, BY, 3.55), 0.05, STEELL, segs=10)
for k in range(8): cyl('ds_nozzle', 0.035, 0.08, (BX1 - 0.12, -BY + 0.25 + k * (2 * BY - 0.5) / 7, 3.5), STEEL, rot=(0, math.pi / 2, 0), segs=8)
pipe('ds_water', [(BX1 - 0.05, BY, 3.55), (BX1 - 0.05, BY + 0.5, 3.55), (BX1 + 0.22, BY + 0.5, 3.55), (BX1 + 0.22, BY + 0.5, 0.4)], 0.05, H2OP, bend=0.2)
lamp('ds_flood', (BX1 + 0.05, -BY - 0.1, 4.08), LAMP, 0.11)
label('rb_plate', 'RB-1  REFINERY INTAKE BIN', 'BACK IN  -  TIP AT STOP  -  40 t', (5.01, -BY - 0.25, 3.0), w=2.5, size=0.16, post=False)
box('rb_plate_bk', (2.6, 0.04, 0.42), (5.01, -BY - 0.21, 3.0), GRAPH2, bevel=0.0)
_blk('feeder')
# belt feeder BF-1 out of the bin bottom, south (toward the camera) onto the splitter
FE0, FE1 = Vector((4.6, 0.6, 0.7)), Vector((4.6, -5.35, 1.8))
conveyor('feeder', FE0, FE1, w=0.9, cover=(0.25, 0.9), gaps=1)
box('feeder_boot', (1.2, 1.6, 0.4), (4.6, 0.2, 0.45), GRAPH2, bevel=0.03)
label('fd_plate', 'BF-1  BELT FEEDER', None, (3.3, -3.3, 0.8), w=1.2, size=0.11)
_blk('vg')
# vibrating grizzly screen VG-1: spring-mounted inclined bar deck (Intake_Grate shakes it with the bin grizzly)
VX0, VX1, VZ0, VZ1, VW = 9.8, 12.5, 2.75, 2.35, 1.5
box('vg_base', (3.0, 2.2, 0.2), ((VX0 + VX1) / 2, 0, ZP + 0.1), GRAPH, bevel=0.02)
for x in (VX0 + 0.2, VX1 - 0.2):
    for sy in (-1, 1):
        z_ = VZ0 + (VZ1 - VZ0) * (x - VX0) / (VX1 - VX0) - 0.55
        box('vg_pier', (0.3, 0.3, z_ - 0.2), (x, sy * (VW / 2 + 0.2), (z_ + 0.2) / 2), GRAPH2, bevel=0.02)
        for k in range(6): cyl('vg_spring', 0.13, 0.04, (x, sy * (VW / 2 + 0.2), z_ + 0.04 + k * 0.07), STEELL, segs=12)
# undersize collection hopper under the deck -> splitter
bm = bmesh.new(); t_ = [(VX0 + 0.3, -0.75), (VX1, -0.75), (VX1, 0.75), (VX0 + 0.3, 0.75)]; b_ = [(11.2, -0.35), (11.9, -0.35), (11.9, 0.35), (11.2, 0.35)]
vt = [bm.verts.new((x, y, 1.75)) for x, y in t_]; vb = [bm.verts.new((x, y, 1.15)) for x, y in b_]
for i in range(4): j = (i + 1) % 4; bm.faces.new((vt[i], vt[j], vb[j], vb[i]))
ob = _obj(bm, 'vg_hopper', PALE, smooth=True, angle=30); md = ob.modifiers.new('sol', 'SOLIDIFY'); md.thickness = 0.05; md.offset = 1.0
with grp('Intake_Grate'):
    _blk('grate')
    # bin top grizzly (bars along X, cross bars)
    for k in range(13):
        y = -BY + 0.15 + k * (2 * BY - 0.3) / 12
        beam('igr_bar', (BX0 + 0.1, y, BRIM + 0.14), (BX1 - 0.1, y, BRIM + 0.14), 0.06, 0.12, GRAPH2, bevel=0.0)
    for k in range(4):
        x = BX0 + 0.3 + k * (BX1 - BX0 - 0.6) / 3
        beam('igr_cross', (x, -BY + 0.1, BRIM + 0.1), (x, BY - 0.1, BRIM + 0.1), 0.1, 0.12, STEEL, bevel=0.0)
    _blk('vg')
    # screen deck box + bars
    p0, p1 = Vector((VX0, 0, VZ0)), Vector((VX1, 0, VZ1))
    for sy in (-1, 1): beam('igr_side', p0 + Vector((0, sy * VW / 2, 0.15)), p1 + Vector((0, sy * VW / 2, 0.15)), 0.1, 0.7, WHITE, bevel=0.02)
    for sy in (-1, 1): beam('igr_cyan', p0 + Vector((0.2, sy * (VW / 2 + 0.06), 0.3)), p1 + Vector((-0.2, sy * (VW / 2 + 0.06), 0.3)), 0.02, 0.05, CYANL, bevel=0.0)
    for k in range(9):
        y = -VW / 2 + 0.15 + k * (VW - 0.3) / 8
        beam('igr_dbar', p0 + Vector((0.1, y, 0.0)), p1 + Vector((-0.05, y, 0.0)), 0.05, 0.1, STEEL, bevel=0.0)
    beam('igr_feedbox', p0 + Vector((-0.1, 0, 0.3)), p0 + Vector((0.5, 0, 0.3)), VW, 0.6, GRAPH2, bevel=0.02)
    rod('igr_exciter', p0.lerp(p1, 0.5) + Vector((0, -VW / 2 - 0.1, 0.55)), p0.lerp(p1, 0.5) + Vector((0, VW / 2 + 0.1, 0.55)), 0.18, GRAPH, segs=18)
    for sy in (-1, 1): cyl('igr_exciter_cap', 0.26, 0.2, tuple(p0.lerp(p1, 0.5) + Vector((0, sy * (VW / 2 + 0.18), 0.55))), WHITE_S, rot=(math.pi / 2, 0, 0), segs=20)
    ore_chunks('igr_ore', ((VX0 + VX1) / 2 - 0.4, 0, VZ0 - 0.05), 0.6, 18, [(ORE, 1, 'rock')], size=(0.12, 0.26), seed=44)
GAME['pivots']['Intake_Grate'] = (5.0, 0.0, BRIM + 0.14)
label('vg_plate', 'VG-1  VIBRATING GRIZZLY', None, ((VX0 + VX1) / 2, -VW / 2 - 0.45, 1.3), size=0.17)
# oversize skip at the end of the deck
box('os_skip', (1.1, 1.5, 0.9), (13.25, 0, ZP + 0.45), GRAPH2, bevel=0.05)
ore_chunks('os_rocks', (13.25, 0, ZP + 0.9), 0.5, 14, [(ORE, 1, 'rock')], size=(0.22, 0.4), heap=0.25, seed=45)
stencil('st_os', 'OVERSIZE', (13.25, -0.77, ZP + 0.5), '-y', 0.16, INKW)
_blk('splitter')
# splitter SP-1 (flop-gate diverter): two outlet chutes -> He-3 conveyor (-Y) and fuel conveyor (+Y)
SPX = 11.55
box('sp_body', (1.1, 1.1, 0.8), (SPX, 0, 0.95), WHITE_S, bevel=0.06)
box('sp_band', (1.12, 1.12, 0.1), (SPX, 0, 1.25), GRAPH, bevel=0.01)
box('sp_actuator', (0.3, 0.5, 0.3), (SPX + 0.65, 0, 1.15), GRAPH2, bevel=0.03)
rod('sp_ram', (SPX + 0.8, 0, 1.15), (SPX + 1.1, 0, 0.8), 0.05, STEELL, segs=10)
for sy in (-1, 1):     # both outlets on the south face: He-3 (east, cyan) and fuel (west, orange)
    chute('sp_chute', (SPX + sy * 0.28, -0.45, 0.8), (SPX + sy * 0.75, -1.25, 0.5), 0.45)
    box('sp_glow', (0.3, 0.03, 0.08), (SPX + sy * 0.3, -0.56, 1.1), CYANL if sy < 0 else HOTS, bevel=0.0)
for sy in (-1, 1): box('sp_leg', (0.12, 0.12, 0.6), (SPX + 0.4 * sy, -0.4 * sy, 0.35), STEEL, bevel=0.0)
label('sp_plate', 'SP-1  SPLITTER', 'He-3  |  FUEL', (SPX - 1.6, -0.75, 1.0), w=1.2, size=0.14)

# ====================================================================== 2. He-3 LINE (y = -7.5, cyan / blue accents)
HY = -7.5
_blk('cvhe3')
# He-3 branch (station coords): splitter -> bucket elevator BE-1 -> covered gallery over the fuel row -> sieve SV-1
SPN = Vector((4.6, -5.6, 0.0))      # splitter position in station coords
BEX, BEY, BEH = 3.3, -7.6, 7.6
box('be_boot', (1.0, 1.2, 0.8), (BEX, BEY, ZP + 0.4), GRAPH2, bevel=0.04)
box('be_casing', (0.62, 0.95, BEH - 0.8), (BEX, BEY, ZP + 0.8 + (BEH - 0.8) / 2), WHITE_S, bevel=0.03)
for k in range(4): box('be_band', (0.66, 0.99, 0.1), (BEX, BEY, ZP + 1.8 + k * 1.5), GRAPH, bevel=0.0)
box('be_cyan', (0.04, 0.03, BEH - 2.0), (BEX, BEY - 0.49, ZP + 1.0 + (BEH - 2.0) / 2), CYANL, bevel=0.0)
box('be_head', (1.0, 1.3, 0.9), (BEX, BEY, ZP + BEH + 0.2), WHITE, bevel=0.06)
box('be_head_band', (1.02, 1.32, 0.1), (BEX, BEY, ZP + BEH - 0.1), GRAPH, bevel=0.0)
rod('be_motor', (BEX + 0.5, BEY + 0.3, ZP + BEH + 0.25), (BEX + 1.0, BEY + 0.3, ZP + BEH + 0.25), 0.18, WHITE_S, segs=14)
chute('be_in', (SPN.x - 0.75, SPN.y - 1.25, 0.5), (BEX + 0.35, BEY + 0.35, 0.75), 0.4)
stencil('st_be', 'He-3', (BEX, BEY - 0.485, 5.3), '-y', 0.2, INK)
label('be_plate', 'BE-1  ELEVATOR', 'He-3 FEED', (BEX, BEY - 0.62, 0.62), w=1.0, size=0.1, post=False)
_blk('he3')
# a. sieve SV-1 (stacked vibrating sieve decks, fines < 100 um pass to the kiln)
SVX = SPX
box('sv_body', (2.2, 2.0, 2.0), (SVX, HY, 2.35), WHITE, bevel=0.1)
for k in range(3): box('sv_deck', (2.26, 2.06, 0.1), (SVX, HY, 1.6 + k * 0.55), GRAPH, bevel=0.01)
box('sv_cyan', (2.22, 0.03, 0.05), (SVX, HY - 1.02, 3.2), CYANL, bevel=0.0)
box('sv_inlet', (0.9, 0.9, 0.5), (SVX, HY + 0.4, 3.6), GRAPH2, bevel=0.04)
for sx in (-1, 1):
    for sy in (-1, 1):
        box('sv_leg', (0.16, 0.16, 1.35), (SVX + sx * 0.9, HY + sy * 0.8, 0.75), STEEL, bevel=0.01)
        for k in range(4): cyl('sv_spring', 0.1, 0.035, (SVX + sx * 0.9, HY + sy * 0.8, 1.32 + k * 0.05), STEELL, segs=10)
rod('sv_motor', (SVX - 1.1, HY - 0.3, 2.0), (SVX - 1.6, HY - 0.3, 2.0), 0.2, WHITE_S, segs=16)
label('sv_plate', 'SV-1  SIEVE', 'KEEPS FINES  < 100 \u00b5m', (SVX, HY - 1.06, 2.45), w=1.9, size=0.2, post=False)
# fines screw feeder -> kiln feed hood
rod('sv_screw', (SVX + 1.0, HY, 1.2), (13.5, HY, 2.6), 0.2, WHITE_S, segs=16)
for k in range(5): rod('sv_screw_band', Vector((SVX + 1.0, HY, 1.2)).lerp(Vector((13.5, HY, 2.6)), 0.1 + k * 0.2), Vector((SVX + 1.0, HY, 1.2)).lerp(Vector((13.5, HY, 2.6)), 0.13 + k * 0.2), 0.23, GRAPH, segs=16)
# b. rotary kiln KN-1 (sealed, electric heater jacket, ~700 C), c. gas collection hood + compressor
KZ, KR = 2.6, 0.95
def kiln(tag, ky, spin):
    X0, X1 = 13.6, 21.2
    for x in (14.35, 20.0):   # piers + trunnion rollers
        box(tag + '_pier', (0.9, 2.6, KZ - KR - 0.25), (x, ky, (KZ - KR - 0.25) / 2 + 0.05), GRAPH2, bevel=0.03)
        for sy in (-1, 1):
            cyl(tag + '_trunnion', 0.32, 0.36, (x, ky + sy * 0.78, KZ - KR - 0.2), STEELL, rot=(0, math.pi / 2, 0), segs=20)
            box(tag + '_bearing', (0.5, 0.3, 0.3), (x, ky + sy * 0.78, KZ - KR - 0.42), GRAPH, bevel=0.02)
    box(tag + '_feedhood', (0.8, 2.4, 2.6), (13.4, ky, KZ + 0.1), WHITE, bevel=0.08)
    box(tag + '_feedhood_cyan', (0.82, 0.03, 0.05), (13.4, ky - 1.21, KZ + 0.9), CYANL, bevel=0.0)
    box(tag + '_feedhood_leg', (0.6, 2.0, KZ - 1.2), (13.4, ky, (KZ - 1.2) / 2 + 0.05), GRAPH2, bevel=0.02)
    # heater jacket (stationary): octagonal insulated shell, glowing element slots
    jk = cyl(tag + '_jacket', KR + 0.42, 4.0, (17.2, ky, KZ), WHITE, rot=(0, math.pi / 2, 0), segs=8, bevel=0.04)
    for x in (15.35, 19.05): cyl(tag + '_jacket_band', KR + 0.48, 0.22, (x, ky, KZ), GRAPH, rot=(0, math.pi / 2, 0), segs=8, bevel=0.02)
    for k in range(5):
        x = 15.9 + k * 0.65
        box(tag + '_heatslot', (0.12, 0.04, 0.9), (x, ky - (KR + 0.42) * math.cos(math.pi / 8) - 0.01, KZ), HOT, bevel=0.0)
        box(tag + '_heatslot_frame', (0.26, 0.04, 1.05), (x, ky - (KR + 0.42) * math.cos(math.pi / 8) + 0.01, KZ), GRAPH, bevel=0.01)
    for x in (15.7, 18.7):
        box(tag + '_jacket_leg', (0.3, 2.2, KZ - KR - 0.5), (x, ky, (KZ - KR - 0.5) / 2 + 0.05), GRAPH2, bevel=0.02)
    box(tag + '_disch', (1.2, 2.6, 3.0), (21.5, ky, KZ + 0.2), WHITE, bevel=0.08)
    box(tag + '_disch_band', (1.22, 2.62, 0.14), (21.5, ky, KZ + 1.3), GRAPH, bevel=0.01)
    box(tag + '_disch_leg', (1.0, 2.2, KZ - 1.3), (21.5, ky, (KZ - 1.3) / 2 + 0.05), GRAPH2, bevel=0.02)
    # drive: girth gear on the drum, pinion + motor on the -Y side
    box(tag + '_drive_skid', (1.4, 1.0, 0.3), (14.85, ky - 1.65, 0.25), GRAPH, bevel=0.02)
    rod(tag + '_drive_motor', (14.4, ky - 1.65, 0.75), (15.3, ky - 1.65, 0.75), 0.3, WHITE_S, segs=20)
    box(tag + '_drive_gbox', (0.5, 0.6, 0.6), (14.85, ky - 1.25, 0.85), GRAPH2, bevel=0.04)
    before = set(bpy.data.objects.keys())
    cyl(tag + '_drum', KR, X1 - X0, ((X0 + X1) / 2, ky, KZ), STEEL, rot=(0, math.pi / 2, 0), segs=40, bevel=0.0)
    for x in (14.35, 20.0): cyl(tag + '_tyre', KR + 0.12, 0.34, (x, ky, KZ), STEELL, rot=(0, math.pi / 2, 0), segs=40, bevel=0.01)
    cyl(tag + '_gear', KR + 0.2, 0.18, (14.85, ky, KZ), GRAPH, rot=(0, math.pi / 2, 0), segs=48, bevel=0.0)
    for k in range(8):   # longitudinal shell straps (make the spin readable)
        a = k * TAU / 8
        for xa, xb in ((13.85, 14.15), (14.55, 14.7), (19.35, 19.8), (20.2, 20.95)):
            beam(tag + '_strap', (xa, ky + (KR + 0.03) * math.cos(a), KZ + (KR + 0.03) * math.sin(a)),
                 (xb, ky + (KR + 0.03) * math.cos(a), KZ + (KR + 0.03) * math.sin(a)), 0.16, 0.05, GRAPH if k % 2 else CYANS, bevel=0.0)
    if spin:
        for n in set(bpy.data.objects.keys()) - before: bpy.data.objects[n]['grp'] = 'Kiln_Drum'
        GAME['pivots']['Kiln_Drum'] = ((X0 + X1) / 2, ky, KZ)
    # gas collection hood duct off the discharge housing
    pipe(tag + '_gasduct', [(21.5, ky + 0.3, KZ + 1.7), (21.5, ky + 0.3, 6.0), (22.9, ky + 0.3, 6.0), (22.9, ky + 0.3, 3.6)], 0.28, WHITE_S, bend=0.5)
kiln('kn1', HY, True)
label('kn1_plate', 'KN-1  ROTARY KILN', 'SEALED  -  ELECTRIC  700 \u00b0C', (17.2, HY - 1.55, 4.35), w=3.2, size=0.26, post=False)
box('kn1_plate_bk', (3.3, 0.06, 0.62), (17.2, HY - 1.36, 4.35), GRAPH2, bevel=0.0) if False else None
for x in (15.8, 18.6): box('kn1_plate_post', (0.08, 0.08, 0.7), (x, HY - 1.5, 3.85), STEEL, bevel=0.0)
label('kn1_hood', 'GAS HOOD', None, (21.5, HY - 1.32, 3.45), size=0.18, post=False)
# compressor CP-1 skid
CPX = 23.3
box('cp_skid', (2.4, 2.2, 0.3), (CPX, HY, 0.25), GRAPH, bevel=0.02)
vvessel('cp_receiver', (CPX - 0.4, HY + 0.35), 0.55, 0.45, 3.1, WHITE_S, dome=0.5, segs=28, bands=(1.0, 2.4), band_mat=GRAPH2)
rod('cp_body', (CPX + 0.2, HY - 0.5, 0.9), (CPX + 1.1, HY - 0.5, 0.9), 0.38, GRAPH2, segs=20)
for j in range(6): rod('cp_fin', (CPX + 0.3 + j * 0.14, HY - 0.5, 0.9), (CPX + 0.34 + j * 0.14, HY - 0.5, 0.9), 0.45, STEEL, segs=20, bevel=0.0)
rod('cp_motor', (CPX - 0.6, HY - 0.5, 0.9), (CPX + 0.2, HY - 0.5, 0.9), 0.3, WHITE_S, segs=20)
label('cp_plate', 'CP-1  GAS COMPRESSOR', None, (CPX, HY - 1.2, 1.7), size=0.16)
# d. cryogenic cold-trap train CT-1..4 (strip H2O, CO2, N2, H2)
CTS = [('CT-1', 'H2O', '200 K'), ('CT-2', 'CO2', '120 K'), ('CT-3', 'N2', '60 K'), ('CT-4', 'H2', '20 K')]
for k, (tg, gas, tk) in enumerate(CTS):
    x = 25.0 + k * 1.45; zt = 3.6 + k * 0.25
    cyl(f'ct{k}_skirt', 0.48, 0.9, (x, HY, 0.55), GRAPH2, segs=24)
    vvessel(f'ct{k}', (x, HY), 0.55, 1.0, zt, FROST if k >= 1 else WHITE_S, dome=0.5, segs=28, bands=(1.4, zt - 0.4), band_mat=GRAPH)
    for j in range(3 + k): cyl(f'ct{k}_frost', 0.575, 0.1, (x, HY, 1.15 + j * 0.42), FROST, segs=28, bevel=0.0)
    t = to_mesh(stencil(f'st_ct{k}', gas, (x, HY - 0.57, 2.35), '-y', 0.26, INK, ex=0.006)); wrap_cyl(t, x, HY, 0.55)
    t = to_mesh(stencil(f'st_ct{k}_s', tk, (x, HY - 0.57, 2.0), '-y', 0.13, INK, ex=0.004)); wrap_cyl(t, x, HY, 0.55)
    t = to_mesh(stencil(f'st_ct{k}_t', tg, (x, HY - 0.57, 1.68), '-y', 0.11, INK, ex=0.004)); wrap_cyl(t, x, HY, 0.55)
    if k < 3: pipe(f'ct{k}_link', [(x, HY, zt + 0.25), (x, HY, zt + 0.7), (x + 1.45, HY, zt + 0.7), (x + 1.45, HY, zt + 0.5)], 0.08, FOIL, bend=0.2)
    lamp(f'ct{k}_lamp', (x + 0.3, HY - 0.45, zt + 0.15), CYANL, 0.05)
pipe('cp_to_ct', [(CPX - 0.4, HY + 0.35, 3.35), (CPX - 0.4, HY + 0.35, 4.0), (25.0, HY, 4.0), (25.0, HY, 3.85)], 0.1, FOIL, bend=0.3)
pipe('kiln_to_cp', [(22.9, HY + 0.3, 3.6), (22.9, HY + 0.3, 2.2), (CPX - 0.4, HY + 0.35, 2.2)], 0.2, WHITE_S, bend=0.3)
label('ct_plate', 'COLD TRAPS  CT-1..4', 'STRIP H2O > CO2 > N2 > H2', (27.2, HY - 1.25, 0.85), w=2.6, size=0.2)
# H2 from CT-4 -> pipe rack -> fuel line (liquefier)
CT4X = 25.0 + 3 * 1.45
# e. cryo distillation column DC-1 (splits He-3 from He-4)
DCX, DCY, DCR, DCH = 31.2, HY + 0.4, 0.62, 12.5
box('dc_coldbox', (2.4, 2.4, 2.2), (DCX, DCY, 1.2), WHITE, bevel=0.1)
box('dc_coldbox_cyan', (2.42, 0.03, 0.05), (DCX, DCY - 1.21, 2.0), CYANL, bevel=0.0)
vvessel('dc_col', (DCX, DCY), DCR, 2.3, DCH, WHITE_S, dome=0.6, segs=32, bands=(3.5, 6.0, 8.5, 11.0, DCH - 0.3), band_mat=GRAPH)
for z in (5.0, 9.5):
    cyl('dc_platform', DCR + 0.75, 0.08, (DCX, DCY, z), GRAPH2, segs=28, bevel=0.0)
    curve_tube('dc_ring_rail', [(DCX + (DCR + 0.72) * math.cos(a), DCY + (DCR + 0.72) * math.sin(a), z + 1.0) for a in [i / 28 * TAU for i in range(29)]], 0.025, TRIM)
    for k in range(8):
        a = k * TAU / 8; rod('dc_rail_post', (DCX + (DCR + 0.72) * math.cos(a), DCY + (DCR + 0.72) * math.sin(a), z), (DCX + (DCR + 0.72) * math.cos(a), DCY + (DCR + 0.72) * math.sin(a), z + 1.0), 0.022, TRIM, segs=6)
ladder('dc_ladder', DCX + DCR + 0.25, DCY, 2.3, 9.5, along='y')
vvessel('dc_cond', (DCX + 0.9, DCY + 0.6), 0.32, DCH - 1.5, DCH + 0.3, FROST, dome=0.5, segs=20)
pipe('dc_overhead', [(DCX, DCY, DCH + DCR * 0.6), (DCX, DCY, DCH + 1.0), (DCX + 0.9, DCY + 0.6, DCH + 1.0), (DCX + 0.9, DCY + 0.6, DCH + 0.45)], 0.09, FOIL, bend=0.25)
pipe('ct_to_dc', [(CT4X, HY, 4.35 + 0.25), (CT4X, HY, 5.0), (CT4X + 1.2, HY, 5.0), (CT4X + 1.2, HY, 1.5), (DCX - 1.25, HY, 1.5)], 0.08, FOIL, bend=0.3)
t = to_mesh(stencil('st_dc', 'DC-1', (DCX, DCY - DCR - 0.02, 7.3), '-y', 0.5, INK, ex=0.008)); wrap_cyl(t, DCX, DCY, DCR)
label('dc_plate', 'DC-1  CRYO COLUMN', 'SPLITS He-3 FROM He-4', (DCX, DCY - 1.25, 2.95), w=2.3, size=0.2, post=False)
with grp('Beacon_Lights'): sphere('beacon_dc', 0.16, (DCX, DCY, DCH + DCR * 0.6 + 0.25), REDL, sub=2)
# f. He-3 filling station FS-1 + canister rack (glowing blue canisters)
FSX = 33.4
box('fs_skid', (1.8, 1.6, 0.25), (FSX, HY + 0.6, 0.22), GRAPH, bevel=0.02)
box('fs_cab', (1.0, 0.9, 1.9), (FSX + 0.3, HY + 0.9, 1.3), WHITE, bevel=0.06)
box('fs_screen', (0.5, 0.03, 0.35), (FSX + 0.3, HY + 0.44, 1.75), CYANS, bevel=0.0)
pipe('dc_to_fs', [(DCX + 1.2, DCY, 1.1), (FSX - 0.5, DCY, 1.1), (FSX - 0.5, HY + 0.6, 1.1), (FSX - 0.5, HY + 0.6, 2.3), (FSX - 0.1, HY + 0.2, 2.3)], 0.06, FOIL, bend=0.2)
rod('fs_arm', (FSX - 0.1, HY + 0.2, 2.3), (FSX - 0.1, HY - 0.6, 1.35), 0.04, STEELL, segs=8)
box('fs_scale', (0.7, 0.7, 0.12), (FSX - 0.1, HY - 0.6, 0.3), STEEL, bevel=0.01)
def canister(nm, x, y, z, h=0.85, r=0.19):
    cyl(nm + '_core', r * 0.94, h - 0.2, (x, y, z + h / 2), HE3, segs=18, bevel=0.0)
    for zz in (z + 0.06, z + h - 0.06): cyl(nm + '_cap', r, 0.12, (x, y, zz), WHITE_S, segs=18, bevel=0.01)
    cyl(nm + '_band', r * 1.01, 0.05, (x, y, z + h / 2), GRAPH, segs=18, bevel=0.0)
    cyl(nm + '_valve', 0.05, 0.1, (x, y, z + h + 0.05), STEEL, segs=8)
canister('can_fill', FSX - 0.1, HY - 0.6, 0.36)
def rack(tag, x0, y0, cols=6, rows=2):
    W_ = cols * 0.5 + 0.2
    for sx in (0, 1):
        for sy in (-1, 1): box(tag + '_post', (0.1, 0.1, rows * 1.1 + 0.3), (x0 + sx * W_, y0 + sy * 0.32, (rows * 1.1 + 0.3) / 2 + ZP), STEEL, bevel=0.0)
    for r_ in range(rows + 1):
        box(tag + '_shelf', (W_ + 0.1, 0.7, 0.06), (x0 + W_ / 2, y0, ZP + 0.12 + r_ * 1.1), GRAPH2, bevel=0.0)
    box(tag + '_cyan', (W_ + 0.1, 0.03, 0.05), (x0 + W_ / 2, y0 - 0.36, ZP + 0.2 + rows * 1.1), CYANL, bevel=0.0)
    for r_ in range(rows):
        for c_ in range(cols): canister(f'{tag}_can', x0 + 0.35 + c_ * 0.5, y0, ZP + 0.15 + r_ * 1.1)
rack('rk1', 30.0, -9.9)
label('fs_plate', 'FS-1  He-3 FILLING', 'CANISTERS TO RACK  >  SHIP', (FSX + 0.4, HY - 1.6, 2.1), w=2.4, size=0.2)
with grp('Tier_03'): rack('rk2', 33.6, -9.9)
GAME['markers']['He3_Output'] = (31.6, -10.7, ZP)
# g. tailings conveyor out of the kiln discharge -> tailings pile
conveyor('cv_tail', (21.5, HY - 1.4, 0.55), (21.5, -11.4, 2.1), w=0.6, cover=None)
heap('tail_pile', (21.5, -12.9, 0.0), 2.0, 1.6, TAIL, seed=61)
ore_chunks('tail_ore', (21.5, -12.9, 0.0), 1.8, 24, [(TAIL, 1, 'rock')], size=(0.15, 0.32), heap=1.6, seed=62)
label('tail_plate', 'TAILINGS', 'SPENT REGOLITH', (18.9, -11.6, 0.9), w=1.4, size=0.2)
# Tier_08: second kiln KN-2 in parallel (behind KN-1)
with grp('Tier_08'):
    kiln('kn2', -3.9, False)
    chute('kn2_feed', (SVX + 1.0, HY + 1.0, 1.4), (13.4, -3.9, 2.4), 0.3)
# Tier_12: bigger column DC-2
with grp('Tier_12'):
    D2X, D2Y = 33.3, -5.0
    box('dc2_coldbox', (2.6, 2.6, 2.4), (D2X, D2Y, 1.3), WHITE, bevel=0.1)
    vvessel('dc2_col', (D2X, D2Y), 0.85, 2.5, 16.5, WHITE_S, dome=0.6, segs=32, bands=(4.0, 7.0, 10.0, 13.0, 16.2), band_mat=GRAPH)
    for z in (6.0, 11.5): cyl('dc2_platform', 1.65, 0.08, (D2X, D2Y, z), GRAPH2, segs=28, bevel=0.0)
    t = to_mesh(stencil('st_dc2', 'DC-2', (D2X, D2Y - 0.87, 9.0), '-y', 0.6, INK, ex=0.008)); wrap_cyl(t, D2X, D2Y, 0.85)
    pipe('dc2_feed', [(DCX + 1.2, DCY + 0.6, 1.6), (D2X - 1.3, D2Y, 1.6)], 0.08, FOIL, bend=0.2)
with grp('Beacon_Lights'): sphere('beacon_dc2', 0.16, (33.3, -5.0, 16.5 + 0.85 * 0.6 + 0.25), REDL, sub=2)

# ====================================================================== 3. FUEL LINE (y = +7.5, orange reactor glow, white LOX frost)
FY = 7.5
_blk('fuel')
# a. crusher CR-1 (cone crusher on a frame, feed hopper on top)
CRX = SPX + 0.6
box('cr_frame', (2.6, 2.6, 1.3), (CRX, FY, 0.75), GRAPH2, bevel=0.05)
lathe('cr_body', [(1.0, 1.4), (1.0, 2.5), (0.55, 3.2), (0.3, 3.3)], (CRX, FY, 0), WHITE, segs=32)
cyl('cr_band', 1.04, 0.16, (CRX, FY, 2.0), GRAPH, segs=32)
cyl('cr_hot', 1.05, 0.04, (CRX, FY, 2.25), HOTS, segs=32, bevel=0.0)
lathe('cr_hopper', [(0.35, 3.25), (0.95, 3.85), (0.98, 3.95)], (CRX, FY, 0), PALE, segs=24)
rod('cr_motor', (CRX + 1.3, FY - 0.9, 0.9), (CRX + 2.3, FY - 0.9, 0.9), 0.35, WHITE_S, segs=20)
box('cr_beltguard', (1.3, 0.2, 0.9), (CRX + 1.3, FY - 1.25, 1.0), GRAPH, bevel=0.04)
label('cr_plate', 'CR-1  CRUSHER', None, (CRX, FY - 1.38, 1.85), size=0.2, post=False)
# crushed ore -> magnetic separator
conveyor('cv_cr_ms', (CRX + 1.0, FY + 0.2, 0.6), (14.6, FY + 0.2, 2.75), w=0.6, cover=(0.15, 0.85), gaps=1)
# b. magnetic separator MS-1 (drum separator: ilmenite out one side, non-mag reject the other)
MSX = 15.6
box('ms_house', (2.0, 1.8, 1.4), (MSX, FY, 2.4), WHITE, bevel=0.08)
rod('ms_drum', (MSX, FY - 0.95, 2.3), (MSX, FY + 0.95, 2.3), 0.55, GRAPH2, segs=28)
for sy in (-1, 1): cyl('ms_drumcap', 0.6, 0.12, (MSX, FY + sy * 0.97, 2.3), RED, rot=(math.pi / 2, 0, 0), segs=28)
box('ms_band', (2.02, 1.82, 0.12), (MSX, FY, 2.95), GRAPH, bevel=0.01)
for sx in (-1, 1):
    for sy in (-1, 1): box('ms_leg', (0.14, 0.14, 1.7), (MSX + sx * 0.85, FY + sy * 0.75, 0.9), STEEL, bevel=0.0)
chute('ms_mag', (MSX + 0.7, FY, 1.7), (MSX + 1.3, FY, 0.9), 0.45)
chute('ms_nonmag', (MSX - 0.7, FY + 0.4, 1.7), (MSX - 0.9, FY + 1.6, 0.7), 0.45)
box('ms_reject', (1.2, 1.0, 0.7), (MSX - 0.9, FY + 2.1, ZP + 0.35), GRAPH2, bevel=0.04)
ore_chunks('ms_reject_ore', (MSX - 0.9, FY + 2.1, ZP + 0.7), 0.45, 10, [(ORE, 1, 'rock')], size=(0.1, 0.2), heap=0.15, seed=71)
label('ms_plate', 'MS-1  MAGNETIC SEPARATOR', 'PULLS OUT ILMENITE', (MSX, FY - 0.95, 1.35), w=2.5, size=0.17, post=False)
# ilmenite screw lift -> reactor top
RXX, RXR = 19.4, 1.2
rod('ms_lift', (MSX + 1.3, FY, 0.9), (RXX - 0.6, FY - 0.3, 8.2), 0.18, WHITE_S, segs=16)
for k in range(6):
    a_ = Vector((MSX + 1.3, FY, 0.9)).lerp(Vector((RXX - 0.6, FY - 0.3, 8.2)), 0.08 + k * 0.17)
    rod('ms_lift_band', a_, a_ + (Vector((RXX - 0.6, FY - 0.3, 8.2)) - Vector((MSX + 1.3, FY, 0.9))).normalized() * 0.1, 0.21, GRAPH, segs=16)
rod('ms_lift_motor', (RXX - 0.6, FY - 0.3, 8.2), (RXX - 0.6, FY - 0.3, 8.8), 0.16, GRAPH2, segs=14)
# c. H2-reduction reactor RX-1 (900-1000 C, glowing heater bands)
RZ0, RZ1 = 1.8, 7.0
cyl('rx_skirt', RXR * 0.85, RZ0 - 0.1, (RXX, FY, (RZ0 - 0.1) / 2 + 0.05), GRAPH2, segs=32)
vvessel('rx', (RXX, FY), RXR, RZ0, RZ1, WHITE, bottom='cone', bdepth=0.6, dome=0.45, segs=40, bands=(RZ0 + 0.3, RZ1 - 0.25), band_mat=GRAPH)
for k in range(4):   # heater bands: graphite jacket rings with glowing gaps
    z = 2.8 + k * 0.95
    cyl('rx_jacket', RXR + 0.06, 0.6, (RXX, FY, z), GRAPH2, segs=40, bevel=0.01)
    cyl('rx_heat', RXR + 0.03, 0.12, (RXX, FY, z + 0.4), HOT, segs=40, bevel=0.0)
for k in range(3):
    a = -math.pi / 2 + (k - 1) * 0.5
    cyl('rx_port', 0.14, 0.12, (RXX + (RXR + 0.06) * math.cos(a), FY + (RXR + 0.06) * math.sin(a), 6.55), HOT, rot=(math.pi / 2, 0, a + math.pi / 2), segs=14)
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    box('rx_leg', (0.22, 0.22, RZ0 + 1.0), (RXX + (RXR + 0.15) * math.cos(a), FY + (RXR + 0.15) * math.sin(a), (RZ0 + 1.0) / 2), STEEL, bevel=0.01)
t = to_mesh(stencil('st_rx', 'RX-1', (RXX, FY - RXR - 0.02, 6.1), '-y', 0.42, INK, ex=0.008)); wrap_cyl(t, RXX, FY, RXR + 0.0)
label('rx_plate', 'RX-1  H2 REDUCTION  950 \u00b0C', 'FeTiO3 + H2  ->  Fe + TiO2 + H2O', (RXX, FY - 1.75, 1.45), w=3.2, size=0.2)
ladder('rx_ladder', RXX - RXR - 0.3, FY, 0.2, RZ1, along='y')
box('rx_top_deck', (2.0, 2.0, 0.08), (RXX, FY, RZ1 + RXR * 0.45 + 0.2), GRAPH2, bevel=0.0)
with grp('Beacon_Lights'): sphere('beacon_rx', 0.14, (RXX + 0.8, FY + 0.8, RZ1 + RXR * 0.45 + 0.5), REDL, sub=2)
# h. slag + iron by-product bin
chute('rx_disch', (RXX, FY, RZ0 - 0.6), (RXX, FY + 2.6, 1.2), 0.4)
box('sl_bin', (2.4, 1.8, 1.1), (RXX, FY + 3.4, ZP + 0.55), GRAPH2, bevel=0.06)
box('sl_bin_band', (2.42, 1.82, 0.1), (RXX, FY + 3.4, ZP + 0.95), RED, bevel=0.0)
heap('sl_pile', (RXX - 0.4, FY + 3.4, ZP + 0.9), 0.75, 0.35, SLAG, seed=72, sq=(0.5, 0.7))
ore_chunks('sl_iron', (RXX + 0.55, FY + 3.4, ZP + 0.95), 0.55, 16, [(IRON, 1, 'pt')], size=(0.1, 0.18), heap=0.2, seed=73)
stencil('st_sl', 'SLAG / IRON', (RXX, FY + 3.4 - 0.92, ZP + 0.55), '-y', 0.2, INKW)
# d. water condenser WC-1 (horizontal shell-and-tube + knock-out drum)
WCX = 22.6
rod('wc_shell', (WCX - 1.6, FY, 1.9), (WCX + 1.6, FY, 1.9), 0.55, WHITE_S, segs=28)
for x in (WCX - 1.6, WCX + 1.6): rod('wc_head', (x, FY, 1.9), (x + (0.25 if x > WCX else -0.25), FY, 1.9), 0.6, GRAPH2, segs=28)
for x in (WCX - 1.0, WCX + 1.0): box('wc_saddle', (0.3, 1.1, 1.3), (x, FY, 0.75), GRAPH, bevel=0.02)
vvessel('wc_ko', (WCX + 0.9, FY + 1.5), 0.42, 0.4, 2.6, WHITE_S, dome=0.5, segs=24, bands=(1.0,), band_mat=GRAPH)
pipe('rx_to_wc', [(RXX, FY, RZ1 + RXR * 0.45), (RXX, FY, 8.6), (RXX + 1.6, FY, 8.6), (WCX - 1.85, FY, 3.0), (WCX - 1.85, FY, 2.2)], 0.17, FOIL, bend=0.5)
label('wc_plate', 'WC-1  WATER CONDENSER', None, (WCX, FY - 0.9, 0.95), size=0.17, post=False)
# e. electrolyzer EL-1 (cell stack) and gas/liquid separators; H2 recycled to RX-1, extra H2 + O2 to the liquefier
def electrolyzer(tag, x, y):
    box(tag + '_skid', (3.0, 1.8, 0.25), (x, y, 0.22), GRAPH, bevel=0.02)
    for k in range(17):
        box(tag + '_cell', (0.12, 1.3, 1.4), (x - 1.0 + k * 0.125, y, 1.1), WHITE_S if k % 2 else GRAPH2, bevel=0.01)
    for xe in (x - 1.15, x + 1.15): box(tag + '_endplate', (0.16, 1.5, 1.6), (xe, y, 1.1), GRAPH, bevel=0.02)
    for sy in (-1, 1):
        for sz in (-1, 1): rod(tag + '_tierod', (x - 1.25, y + sy * 0.62, 1.1 + sz * 0.62), (x + 1.25, y + sy * 0.62, 1.1 + sz * 0.62), 0.03, STEELL, segs=8)
    box(tag + '_cyan', (2.2, 0.03, 0.05), (x, y - 0.67, 1.85), CYANL, bevel=0.0)
    vvessel(tag + '_sepH2', (x - 0.6, y + 0.5), 0.3, 1.9, 3.0, WHITE_S, dome=0.5, segs=20)
    vvessel(tag + '_sepO2', (x + 0.6, y + 0.5), 0.3, 1.9, 3.0, O2P, dome=0.5, segs=20)
    box(tag + '_busbar', (0.2, 0.2, 2.5), (x - 1.35, y - 0.4, 1.6), RED, bevel=0.01)
ELX = 25.6
electrolyzer('el1', ELX, FY)
pipe('wc_to_el', [(WCX + 0.9, FY + 1.5, 0.6), (WCX + 0.9, FY + 1.5, 0.35), (ELX - 1.5, FY + 0.8, 0.35), (ELX - 1.5, FY + 0.8, 0.9)], 0.08, H2OP, bend=0.25)
label('el_plate', 'EL-1  ELECTROLYZER', '2 H2O  ->  2 H2 + O2', (ELX, FY - 1.0, 2.35), w=2.3, size=0.2, post=False)
for x in (ELX - 0.9, ELX + 0.9): box('el_plate_post', (0.06, 0.06, 2.0), (x, FY - 0.95, 1.1), STEEL, bevel=0.0)
pipe('el_h2_recycle', [(ELX - 0.6, FY + 0.5, 3.15), (ELX - 0.6, FY + 0.5, 9.2), (RXX + 0.4, FY + 0.5, 9.2), (RXX + 0.4, FY + 0.5, 0.6), (RXX + 0.4, FY, 0.6), (RXX + 0.4, FY, 1.0)], 0.09, WHITE_S, bend=0.4)
for k in range(5): rod('h2r_band', (RXX + 1.0 + k * 1.1, FY + 0.5, 9.2), (RXX + 1.15 + k * 1.1, FY + 0.5, 9.2), 0.105, CYANL, segs=12)
stencil('st_h2r', 'H2 RECYCLE', (RXX + 3.0, FY + 0.38, 9.55), '-y', 0.22, INK)
for x in (RXX + 1.3, ELX - 1.3): box('h2r_post', (0.14, 0.14, 9.1), (x, FY + 0.5, 4.55), STEEL, bevel=0.01)
# f. liquefier LQ-1 (O2 -> LOX 90 K, extra H2 -> LH2 20 K) with its own radiators
LQX = 29.0
box('lq_coldbox', (2.2, 2.2, 5.6), (LQX, FY, 2.9), WHITE, bevel=0.1)
for z in (1.0, 3.0, 5.0): box('lq_band', (2.22, 2.22, 0.12), (LQX, FY, z), GRAPH, bevel=0.01)
box('lq_frost', (2.24, 2.24, 0.9), (LQX, FY, 0.65), FROST, bevel=0.06)
box('lq_cyan', (2.24, 0.03, 0.05), (LQX, FY - 1.12, 5.4), CYANL, bevel=0.0)
box('lq_comp', (1.4, 1.2, 1.1), (LQX - 1.8, FY + 0.5, 0.75), GRAPH2, bevel=0.05)
for j in range(5): box('lq_comp_fin', (0.06, 1.24, 0.9), (LQX - 2.3 + j * 0.25, FY + 0.5, 0.8), STEEL, bevel=0.0)
pipe('el_o2_to_lq', [(ELX + 0.6, FY + 0.5, 3.15), (ELX + 0.6, FY + 0.5, 3.8), (LQX - 1.1, FY + 0.5, 3.8)], 0.08, O2P, bend=0.3)
pipe('el_h2_to_lq', [(ELX - 0.6, FY + 0.5, 3.15), (ELX - 0.6, FY + 0.9, 3.4), (ELX - 0.6, FY + 0.9, 4.4), (LQX - 1.1, FY + 0.9, 4.4)], 0.07, WHITE_S, bend=0.3)
label('lq_plate', 'LQ-1  LIQUEFIER', 'O2 > LOX  90 K   |   H2 > LH2  20 K', (LQX, FY - 1.14, 3.9), w=2.15, size=0.2, post=False)
radiator_array('lq_rad', 12.9, 22.0, 34.0, 1.8, 4.6, 4, axis='x')
pipe('lq_rad_loop', [(LQX + 0.6, FY + 1.1, 4.8), (LQX + 0.6, 12.9, 4.8), (LQX + 0.6, 12.9, 6.5)], 0.09, STEELL, bend=0.4)
label('rad_plate', 'RAD-1  HEAT REJECTION', None, (28.0, 12.82, 1.3), size=0.18, post=False)
# g. LOX + LH2 cryo tanks (frosted base), header out TO TANK FARM
def cryo_tank(tag, x, y, r, z1, label_, sub):
    z0 = 1.6
    cyl(tag + '_plinth', r + 0.25, 0.3, (x, y, 0.15 + ZP), GRAPH, segs=40, bevel=0.03)
    cyl(tag + '_skirt', r * 0.85, z0 - 0.3, (x, y, ZP + 0.3 + (z0 - 0.3) / 2 - 0.15), GRAPH2, segs=40)
    vvessel(tag, (x, y), r, z0, z1, WHITE, bottom='dish', dome=0.45, segs=40, bands=(z0 + 0.6, (z0 + z1) / 2, z1 - 0.4), band_mat=GRAPH)
    for j in range(3): cyl(tag + '_frost', r * 1.012, 0.28, (x, y, z0 + 0.15 + j * 0.34), FROST, segs=40, bevel=0.0)
    tank_label(tag, label_, sub, x, y, r, (z0 + z1) / 2 + 1.2, size=0.62)
    ladder(tag + '_ladder', x - r - 0.3, y, 0.2, z1 + 0.3, along='y')
    rod(tag + '_vent', (x + 0.4, y - 0.3, z1 + r * 0.4), (x + 0.4, y - 0.3, z1 + r * 0.45 + 1.2), 0.08, STEELL, segs=10)
    lamp(tag + '_lamp', (x - 0.5, y - 0.5, z1 + r * 0.42), AMBERL, 0.07)
    rod(tag + '_nozzle', (x, y - r + 0.1, z0 + 0.4), (x, y - r - 0.5, z0 + 0.4), 0.16, STEELL, segs=14)
cryo_tank('lox1', 32.4, FY, 1.45, 6.0, 'LOX-1', 'LIQUID OXYGEN  90 K')
cryo_tank('lh21', 36.0, FY, 1.85, 7.2, 'LH2-1', 'LIQUID HYDROGEN  20 K')
with grp('Beacon_Lights'): sphere('beacon_lh2', 0.15, (36.0, FY, 7.2 + 1.85 * 0.45 + 0.2), REDL, sub=2)
pipe('lq_to_lox', [(LQX + 1.1, FY - 0.3, 2.2), (31.0, FY - 0.3, 2.2), (31.0, FY - 1.9, 2.2), (32.4, FY - 1.9, 2.2), (32.4, FY - 1.95, 2.0)], 0.1, FOIL, bend=0.3)
pipe('lq_to_lh2', [(LQX + 1.1, FY + 0.4, 2.6), (34.0, FY + 0.4, 2.6), (34.0, FY - 2.3, 2.6), (36.0, FY - 2.3, 2.6), (36.0, FY - 2.35, 2.0)], 0.12, FOIL, bend=0.3)
for nm, (x, r, hy) in (('lox', (32.4, 1.45, 5.45)), ('lh2', (36.0, 1.85, 5.0))):
    pipe(f'tf_{nm}', [(x, FY - r - 0.5, 2.0), (x, hy, 2.0), (x, hy, 1.1), (38.3, hy, 1.1)], 0.13 if nm == 'lox' else 0.15, WHITE_S, bend=0.4)
    for k in range(3): rod(f'tf_{nm}_band', (36.8 + k * 0.5, hy, 1.1), (36.95 + k * 0.5, hy, 1.1), 0.16, GRAPH if nm == 'lox' else CYANS, segs=14)
    valve(f'tf_{nm}_v', (x, hy, 1.6), axis='y', r=0.14, wheel=False, actuator=True) if False else None
for x in (37.95,): box('tf_sleeper', (0.3, 1.0, 0.85), (x, 5.22, 0.5), GRAPH, bevel=0.02)
label('tf_plate', 'TO TANK FARM', 'LOX  /  LH2', (37.1, 4.72, 1.95), w=1.9, size=0.22)
GAME['markers']['Pipe_TankFarm'] = (38.4, 5.22, 1.1)
GAME['markers']['Fuel_Output'] = (34.2, 4.6, ZP)
with grp('Tier_05'):
    electrolyzer('el2', ELX, FY + 2.6)
    pipe('el2_h2o', [(ELX - 1.5, FY + 0.8, 0.35), (ELX - 1.5, FY + 2.6, 0.35)], 0.07, H2OP, bend=0.2)
with grp('Tier_20'):
    cryo_tank('lox2', 32.4, FY + 3.6, 1.45, 6.0, 'LOX-2', 'LIQUID OXYGEN  90 K')
    cryo_tank('lox3', 36.0, FY + 3.8, 1.45, 6.0, 'LOX-3', 'LIQUID OXYGEN  90 K')
    pipe('lox2_tie', [(32.4 + 1.5, FY + 3.6, 1.9), (34.4, FY + 3.6, 1.9), (34.4, FY + 0.4, 2.6)], 0.1, FOIL, bend=0.4)
    pipe('lox3_tie', [(36.0 - 1.5, FY + 3.6, 1.9), (34.4, FY + 3.6, 1.9)], 0.1, FOIL, bend=0.2)

_blk('conn')
# ====================================================================== station connectors (compact layout, station coords, 1:1)
# He-3 gallery: BE-1 head -> high over the fuel row (crusher end) -> sieve SV-1 at the He-3 row's west end
GA0 = Vector((BEX - 0.05, BEY - 0.75, ZP + BEH - 0.15)); GA1 = Vector(RH((SVX, HY + 0.55, 4.3)))
conveyor('cv_he3', GA0, GA1, w=0.8, cover=(0.04, 0.96), gaps=3, run_grp='Conveyor_He3', pitch=0.75, legs=False)
for k_, yt in enumerate((-10.0, -21.0)):
    q_ = GA0.lerp(GA1, (yt - GA0.y) / (GA1.y - GA0.y)); tower(f'gal_tower{k_}', q_.x, q_.y, ZP, q_.z - 0.32, w=0.9)
# fuel branch: splitter west outlet -> crusher CR-1 hopper (fuel row west end)
conveyor('cv_fuel', (SPN.x + 0.75, SPN.y - 1.3, 0.45), RF((CRX, FY + 0.45, 4.35)), w=0.8, cover=(0.1, 0.9), gaps=2, run_grp='Conveyor_Fuel', pitch=0.75)
# pipe rack + catwalk in the gap between the rows: H2 from CT-4 (He-3 row) crosses to the liquefier LQ-1 (fuel row)
RKX = -12.5
for y in (-24.0, -21.0, -18.8):
    for dx in (-0.6, 0.6): box('rk_col', (0.22, 0.22, 5.2), (RKX + dx, y, 2.6), STEEL, bevel=0.01)
    beam('rk_beam', (RKX - 0.7, y, 5.2), (RKX + 0.7, y, 5.2), 0.24, 0.3, GRAPH2, bevel=0.01)
    box('rk_foot', (1.8, 0.5, 0.12), (RKX, y, 0.06 + ZP), GRAPH, bevel=0.02)
for dx in (-0.6, 0.6): ibeam('rk_stringer', (RKX + dx, -24.2, 5.0), (RKX + dx, -18.6, 5.0), 0.16, 0.3, STEEL)
box('cw_deck', (1.2, 5.6, 0.08), (RKX, -21.4, 5.4), GRAPH2, bevel=0.0)
for dx in (-0.6, 0.6): rail('cw_rail', [(RKX + dx, -24.2, 5.44), (RKX + dx, -18.6, 5.44)], TRIM, post=1.8)
box('cw_cyan', (0.04, 5.4, 0.05), (RKX - 0.62, -21.4, 5.33), CYANL, bevel=0.0)
_c4 = RH((CT4X, HY, 4.6)); _lq = RF((LQX - 0.7, FY - 0.3, 5.7))
pipe('h2_to_fuel', [_c4, (_c4[0], _c4[1], 5.7), (_c4[0], -24.3, 5.7), (RKX + 0.3, -24.3, 5.7), (RKX + 0.3, _lq[1], 5.7), (_lq[0], _lq[1], 5.7), (_lq[0], _lq[1], 4.85)], 0.08, WHITE_S, bend=0.4)
for k in range(3): rod('h2x_band', (RKX + 0.3, -23.2 + k * 1.6, 5.7), (RKX + 0.3, -23.05 + k * 1.6, 5.7), 0.095, CYANL, segs=12)
stencil('st_h2x', 'H2 > FUEL', (RKX, -24.0 - 0.13, 5.2), '-y', 0.14, INK)
# stair tower beside the catwalk (in the gap)
TWX, TWY = RKX + 1.8, -21.0
for ux in (-1, 1):
    for uy in (-1, 1): box('stw_post', (0.14, 0.14, 6.3), (TWX + ux * 0.9, TWY + uy * 0.9, 3.15), STEEL, bevel=0.0)
for k in range(4):
    za, zb = k * 5.4 / 4, (k + 1) * 5.4 / 4
    if k < 3: box('stw_landing', (2.0, 2.0, 0.08), (TWX, TWY, zb), GRAPH2, bevel=0.0)
    off = -0.45 if k % 2 == 0 else 0.45
    ya, yb = (TWY - 0.8, TWY + 0.8) if k % 2 == 0 else (TWY + 0.8, TWY - 0.8)
    for sv in (-0.4, 0.4): beam('stw_stringer', (TWX + off + sv, ya, za), (TWX + off + sv, yb, zb), 0.05, 0.2, STEEL)
    for j in range(1, 9):
        q = Vector((TWX + off, ya, za)).lerp(Vector((TWX + off, yb, zb)), j / 9); box('stw_tread', (0.8, 0.18, 0.04), tuple(q), GRAPH2, bevel=0.0)
box('stw_top', (2.0, 2.0, 0.08), (TWX, TWY, 5.4), GRAPH2, bevel=0.0)
box('stw_bridge', (1.2, 1.0, 0.08), (TWX - 1.2, TWY, 5.4), GRAPH2, bevel=0.0)
for z in (1.35 * k for k in range(1, 5)): rod('stw_rail', (TWX - 0.9, TWY - 0.9, z + 1.0), (TWX + 0.9, TWY - 0.9, z + 1.0), 0.025, TRIM, segs=8)

# ====================================================================== 4. SUPPORT: control module CM-1 + airlock + dust shower, power masts
CMX, CMY = -2.4, -20.95     # in the gap between the fuel row (north) and the He-3 row (south)
pad('pad_cm', CMX - 7.1, CMX + 3.0, CMY - 1.7, CMY + 1.7)
box('cm_body', (5.2, 2.8, 3.0), (CMX, CMY, ZP + 1.7), WHITE, bevel=0.34, segs=4)
box('cm_plinth', (5.4, 3.0, 0.3), (CMX, CMY, ZP + 0.15), GRAPH, bevel=0.03)
for x in (CMX - 1.7, CMX, CMX + 1.7): box('cm_rib', (0.14, 2.88, 3.0), (x, CMY, ZP + 1.7), PALE, bevel=0.05)
box('cm_band', (5.24, 2.84, 0.22), (CMX, CMY, ZP + 2.55), GRAPH, bevel=0.03)
box('cm_cyan', (4.8, 0.03, 0.06), (CMX, CMY - 1.43, ZP + 2.32), CYANL, bevel=0.0)
for k in range(3): box('cm_screen', (0.8, 0.03, 0.45), (CMX + 0.9 + (k - 1) * 0.95, CMY - 1.41, ZP + 1.6), CYANS if k != 1 else HOTS, bevel=0.0)
label('cm_plate', 'CM-1  REFINERY CONTROL', 'He-3  +  FUEL PROCESS', (CMX + 0.3, CMY - 1.44, ZP + 2.95), w=3.2, size=0.22, post=False)
box('cm_roofbox', (1.6, 1.2, 0.6), (CMX + 1.6, CMY + 0.4, ZP + 3.5), GRAPH2, bevel=0.06)
rod('cm_mast', (CMX - 1.8, CMY + 0.6, ZP + 3.2), (CMX - 1.8, CMY + 0.6, ZP + 5.6), 0.05, STEELL, segs=8)
lathe('cm_dish', [(0, 0.0), (0.45, 0.12), (0.6, 0.25)], (CMX - 1.2, CMY + 0.8, ZP + 3.3), WHITE_S, segs=24)
with grp('Beacon_Lights'): sphere('beacon_cm', 0.13, (CMX - 1.8, CMY + 0.6, ZP + 5.72), REDL, sub=2)
# airlock (cylinder on the -X end) + dust shower booth in front of the hatch
AX = CMX - 2.6 - 1.0
cyl('al_tube', 1.15, 2.0, (AX, CMY, ZP + 1.45), WHITE_S, rot=(0, math.pi / 2, 0), segs=32, bevel=0.03)
for x in (AX - 0.95, AX + 0.95): cyl('al_ring', 1.22, 0.14, (x, CMY, ZP + 1.45), GRAPH, rot=(0, math.pi / 2, 0), segs=32)
box('al_hatch', (0.06, 0.9, 1.6), (AX - 1.03, CMY, ZP + 1.25), GRAPH2, bevel=0.05)
lamp('al_lamp', (AX - 1.06, CMY - 0.7, ZP + 2.3), GREENL, 0.05)
box('al_saddle', (1.6, 1.6, 0.4), (AX, CMY, ZP + 0.3), GRAPH, bevel=0.03)
DSX = AX - 2.0
for ux in (-1, 1):
    for uy in (-1, 1): box('dsh_post', (0.1, 0.1, 2.6), (DSX + ux * 0.75, CMY + uy * 0.75, ZP + 1.3), STEEL, bevel=0.0)
box('dsh_roof', (1.7, 1.7, 0.16), (DSX, CMY, ZP + 2.65), WHITE_S, bevel=0.03)
box('dsh_mat', (1.6, 1.6, 0.05), (DSX, CMY, ZP + 0.03), GRAPH2, bevel=0.0)
for uy in (-1, 1):
    rod('dsh_bar', (DSX - 0.7, CMY + uy * 0.72, ZP + 1.8), (DSX + 0.7, CMY + uy * 0.72, ZP + 1.8), 0.035, STEELL, segs=8)
    for k in range(5): cyl('dsh_nozzle', 0.03, 0.08, (DSX - 0.6 + k * 0.3, CMY + uy * 0.68, ZP + 1.8), STEEL, rot=(math.pi / 2, 0, 0), segs=6)
box('dsh_cyan', (1.72, 0.03, 0.05), (DSX, CMY - 0.86, ZP + 2.5), CYANL, bevel=0.0)
stencil('st_dsh', 'DUST SHOWER', (DSX, CMY - 0.87, ZP + 2.66), '-y', 0.13, INK)
stencil('st_al', 'AIRLOCK A-1', (AX, CMY - 1.18, ZP + 2.25), '-y', 0.16, INK)
GAME['markers']['Crew_Path_01'] = (AX - 1.3, CMY, ZP)
GAME['markers']['Crew_Path_02'] = (DSX, CMY, ZP)
GAME['markers']['Crew_Path_03'] = (TWX, TWY + 1.45, ZP)
GAME['markers']['Crew_Path_04'] = (RKX, -21.6, 5.45)
GAME['markers']['Crew_Path_05'] = (-17.1, -19.75, ZP)
GAME['markers']['Crew_Path_06'] = (CMX + 3.4, CMY + 0.6, ZP)
GAME['markers']['Crew_Path_07'] = (2.0, -5.0, ZP)
# power masts + lines (feed the kiln heater, electrolyzer, control module)
def power_mast(name, x, y, h=9.0):
    lathe(name, [(0.3, 0.0), (0.24, 1.0), (0.16, h - 0.4), (0.14, h)], (x, y, 0), GRAPH2, segs=14)
    cyl(name + '_base', 0.65, 0.4, (x, y, 0.2), GRAPH, segs=16, bevel=0.03)
    beam(name + '_arm', (x - 1.4, y, h - 0.5), (x + 1.4, y, h - 0.5), 0.16, 0.2, STEEL)
    cyl(name + '_cyan', 0.17, 0.06, (x, y, 2.6), CYANL, segs=14)
    pts = []
    for dx in (-1.2, 0.0, 1.2):
        cyl(name + '_ins', 0.08, 0.45, (x + dx, y, h - 0.2), FOIL, segs=10); pts.append((x + dx, y, h))
    return pts
MASTS = [(-15.0, -20.95), (-19.2, -20.95)]
PM = [power_mast(f'pmast{k}', x, y) for k, (x, y) in enumerate(MASTS)]
for a_, b_ in zip(PM, PM[1:]):
    for p, q in zip(a_, b_): cable('pline', p, q, 0.022, RUBBER, sag=0.5, n=18)
with grp('Beacon_Lights'):
    for k, (x, y) in enumerate(MASTS): sphere(f'beacon_mast{k}', 0.15, (x, y, 9.3), REDL, sub=2)
_kj = RH((17.2, HY + 1.4, 3.75)); _kj = (_kj[0], _kj[1], 3.55)
cable('pdrop_kiln', PM[0][2], (_kj[0], _kj[1], _kj[2] + 0.3), 0.03, RUBBER, sag=0.9, n=20)
box('kn_junction', (0.6, 0.4, 0.6), _kj, GRAPH2, bevel=0.03)
rod('kn_junction_post', (_kj[0], _kj[1], ZP), (_kj[0], _kj[1], _kj[2] - 0.3), 0.06, STEEL, segs=8)
cable('pdrop_el', PM[0][1], RF((ELX - 1.35, FY - 0.4, 2.85)), 0.035, RUBBER, sag=0.8, n=18)
cable('pdrop_cm', PM[0][0], (CMX + 1.6, CMY + 0.4, ZP + 3.8), 0.03, RUBBER, sag=0.8, n=18)
box('sw_cabinet', (1.4, 0.8, 2.0), (-17.1, -20.4, ZP + 1.0), PALE, bevel=0.05)
for j, m_ in enumerate((GREENL, GREENL, AMBERL)): lamp(f'sw_lamp{j}', (-17.4 + j * 0.3, -20.82, ZP + 1.8), m_, 0.04)
stencil('st_sw', 'SWG-R  480 V', (-17.1, -20.82, ZP + 1.35), '-y', 0.13, INK)

# ====================================================================== markers, pivots, bookkeeping
GAME['markers']['Path_Dump'] = (0.0, 0.0, 0.0)
GAME['markers']['Road_Entry'] = (-4.0, 0.0, 0.0)
GAME['extras']['root'] = {'origin': 'truck dump spot at the intake bin (Path_Dump)', 'truck_heading_at_dump': '-X (cab toward -X)',
                          'approach': 'along +X (reverses the last 4 m from Road_Entry = Mine Path_Dump_Approach)', 'anchor': 'REFINERY_ANCHOR'}

_blk('end')
# ---- apply the compact layout: row blocks -> M_H / M_F, splitter -> SPN; VG-1 is dropped (the bin grizzly does the scalping)
for o in list(coll('Mine').all_objects):
    if o.name.startswith('pad_he3'): o['blk'] = 'he3'
    elif o.name.startswith('pad_fuel'): o['blk'] = 'fuel'
for o in [o for o in coll('Mine').all_objects if o.get('blk') == 'vg']: bpy.data.objects.remove(o, do_unlink=True)
convert_curves()
_FLX0 = Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0)); _mv = []
for o in list(coll('Mine').all_objects):
    b_ = o.get('blk')
    M_ = M_H if b_ == 'he3' else M_F if b_ == 'fuel' else Matrix.Translation((SPN.x - SPX, SPN.y, 0.0)) if b_ == 'splitter' else None
    if M_ is None or o.parent is not None: continue
    mw = M_ @ o.matrix_world
    if o.name.startswith('st_'): mw = mw @ _FLX0
    o.matrix_world = mw; _mv.append(o)
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for o in _mv:
    if o.type == 'MESH': o.select_set(True)
bpy.context.view_layer.objects.active = [o for o in _mv if o.type == 'MESH'][0]
bpy.ops.object.make_single_user(object=True, obdata=True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
print('RELAYOUT moved', len(_mv), 'neg', sum(1 for o in _mv if o.matrix_world.determinant() < 0), flush=True)
GAME['pivots']['Kiln_Drum'] = RH(GAME['pivots']['Kiln_Drum'])
for n_, f_ in (('He3_Output', RH), ('Fuel_Output', RF), ('Pipe_TankFarm', RF)):
    p_ = f_(GAME['markers'][n_]); GAME['markers'][n_] = (p_[0], p_[1], GAME['markers'][n_][2] if n_ != 'Pipe_TankFarm' else p_[2])
if A.get('stopbody'):
    import json as _j
    _d=[]
    for o in coll('Mine').all_objects:
        if o.type not in ('MESH','CURVE','FONT'): continue
        bb=[o.matrix_world @ Vector(c) for c in o.bound_box]
        mn=[min(v[i] for v in bb) for i in range(3)]; mx=[max(v[i] for v in bb) for i in range(3)]
        _d.append((o.name, o.parent.name if o.parent else '', [round(v,2) for v in mn],[round(v,2) for v in mx]))
    _j.dump({'objs':_d,'game':GAME}, open(A['stopbody'],'w'), default=str); sys.exit(0)
# ====================================================================== MIRROR to station handedness
# The process was laid out with its stencils on the -Y faces. In the Mine station the camera looks from world -Y, which is
# refinery +Y once the truck at Path_Dump faces world +X. So mirror the whole refinery in Y, then flip every stencil
# about its own vertical axis so it reads correctly from the station camera. Bake the mirror into the meshes so no negative
# scales remain and the normals stay correct.
convert_curves()
MIR = Matrix.Diagonal((1.0, -1.0, 1.0, 1.0)); FLX = Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0))
_all = list(coll('Mine').all_objects)
for o in _all:
    if o.parent is None: o.matrix_world = MIR @ o.matrix_world
bpy.context.view_layer.update()
for o in _all:
    if o.name.startswith('st_'): o.matrix_world = o.matrix_world @ FLX
bpy.context.view_layer.update()
_neg = [o for o in _all if o.type == 'MESH' and o.matrix_world.determinant() < 0]
bpy.ops.object.select_all(action='DESELECT')
for o in _neg: o.select_set(True)
bpy.context.view_layer.objects.active = _neg[0]
bpy.ops.object.make_single_user(object=True, obdata=True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
print('MIRROR baked', len(_neg), 'stencils', sum(1 for o in _all if o.name.startswith('st_')), 'still-negative', sum(1 for o in _all if o.matrix_world.determinant() < 0), flush=True)
def F(p): return (p[0], -p[1], p[2])
for k_ in ('pivots', 'markers'):
    for n_, p_ in list(GAME[k_].items()): GAME[k_][n_] = F(tuple(p_))
for n_, p_ in list(GAME.get('conveyors', {}).items()): GAME['conveyors'][n_] = F(tuple(p_))
GAME['extras']['root']['mirrored_y'] = True
ANCHOR_X = 4.84      # REFINERY_ANCHOR in these coords is (4.84, 0, 0); Mine: Path_Dump (-9,-5.5) -> anchor (-13.84,-5.5)
GAME['anchor_x'] = ANCHOR_X

# ====================================================================== STAGE: shared ground (M_ground); review-only from here on
# Frame from now on = "final" refinery coords. World (Mine station, Blender) = (-9 - x, -5.5 - y): the truck at Path_Dump sits at
# the origin, the refinery runs along +X (= world -X, west of the rig), and the station camera side is +Y (= world -Y).
W2F = Matrix.Translation((-9.0, -5.5, 0.0)) @ Matrix.Rotation(math.pi, 4, 'Z')     # Mine world -> refinery final coords
# mc_common's stage puts its ridge backdrop at +Y; our camera side is +Y, so build it rotated: flat spots given in pre-rotation
# coords, then the whole stage turns 180 deg about Z (ridges end up behind the refinery, at -Y).
_h0 = build_stage(keep_flat=((7.0, -16.0, 31.0), (9.0, 1.5, 25.0)))
for ob in list(coll('Stage').objects):
    if ob.parent is None: ob.matrix_world = Matrix.Rotation(math.pi, 4, 'Z') @ ob.matrix_world
bpy.context.view_layer.update()
def height(x, y): return _h0(-x, -y)
for ob in list(coll('Stage').objects):
    if ob.type == 'MESH' and ob.name.split('.')[0] in ('boulder', 'pebble'):
        c_ = ob.location
        if (-48 < c_.x < 40 and -30 < c_.y < 44): bpy.data.objects.remove(ob)

def load_coll(path, cname):
    with bpy.data.libraries.load(path, link=False) as (src, dst): dst.collections = [cname]
    return dst.collections[0]
# ---- Mine B scene (approved concept B master), relaid with the Mine agent's own station layout (art/3d/buildings/mine/_src/mine_layout.py)
MINEB = None
if A.get('mine', '1') == '1':
    MINEB = load_coll(os.path.join(MC, '..', 'b_sleek_hightech', 'b_sleek_hightech_master.blend'), 'Mine')
    MINEB.name = 'MineB'; bpy.context.scene.collection.children.link(MINEB)
    before = set(bpy.data.objects)
    try:
        sys.path.insert(0, os.path.join(HERE, '..', '..', 'mine', '_src')); import mine_layout as ML
        if 'B_HaulRoad' not in bpy.data.materials: ROADM.copy().name = 'B_HaulRoad'
        ML.ground_fn = lambda: (lambda x, y: 0.0)       # ground is flat (keep_flat) around the station
        ML.apply()
    except Exception as ex_:
        print('MINE_LAYOUT failed, using the plain B master:', ex_, flush=True)
    new_ = [o for o in bpy.data.objects if o not in before]
    for o in new_:
        for c_ in list(o.users_collection):
            if c_.name == 'Mine': c_.objects.unlink(o); MINEB.objects.link(o)
    for o in set(MINEB.all_objects) | set(new_):
        if o.parent is None: o.matrix_world = W2F @ o.matrix_world
    bpy.context.view_layer.update()
    # mine_layout cut the ground under its roads in Mine coords; the Stage ground here is in refinery-final coords, so redo the cut
    from mathutils.bvhtree import BVHTree
    _roads = [o for o in bpy.data.objects if o.get('road')]; _g = bpy.data.objects.get('Ground')
    if _roads and _g:
        vs_, ps_ = [], []
        for o in _roads:
            b0 = len(vs_); vs_ += [o.matrix_world @ v.co for v in o.data.vertices]; ps_ += [tuple(b0 + i for i in p.vertices) for p in o.data.polygons]
        _rb = BVHTree.FromPolygons(vs_, ps_); _gi = _g.matrix_world.inverted(); _cut = 0
        _x0, _x1 = min(v.x for v in vs_) - 1, max(v.x for v in vs_) + 1; _y0, _y1 = min(v.y for v in vs_) - 1, max(v.y for v in vs_) + 1
        for v in _g.data.vertices:
            w = _g.matrix_world @ v.co
            if not (_x0 < w.x < _x1 and _y0 < w.y < _y1): continue
            hit = _rb.ray_cast(Vector((w.x, w.y, w.z + 5)), Vector((0, 0, -1)))
            if hit[0] is not None and w.z > hit[0].z - 0.03: v.co = _gi @ Vector((w.x, w.y, hit[0].z - 0.03)); _cut += 1
        _g.data.update(); print('ROADCUT', len(_roads), _cut, flush=True)
    print('MINEB', len(MINEB.all_objects), 'layout objs', len(new_), flush=True)
def show_mine(v):
    if MINEB:
        for o in MINEB.all_objects: o.hide_render = not v
        for o in bpy.data.objects:
            if o.name.startswith('haul_road'): o.hide_render = not v

# ---- HT-04 in the dump pose (concept_b_sleek.py --pose dump: bed up 50 deg at frame 37, arm parked, cascade off the tail lip)
TRUCK_BLEND = A.get('truckblend', '/tmp/rf_src/b_sleek_hightech_master.blend')
if not os.path.exists(TRUCK_BLEND):
    import subprocess
    subprocess.run([bpy.app.binary_path, '-b', '-P', os.path.join(MC, 'concept_b_sleek.py'), '--', '--out', os.path.dirname(TRUCK_BLEND), '--pose', 'dump', '--only', 'blend'], check=True)
tc = load_coll(TRUCK_BLEND, 'Mine')
troot = [o for o in tc.objects if o.name.startswith('Truck_HT04')][0]
def desc(o):
    for ch in o.children: yield ch; yield from desc(ch)
TRUCK = set([troot] + list(desc(troot))) | {o for o in tc.objects if o.name.startswith(('dump_slide', 'dump_fall'))}
st = coll('Stage')
for o in list(tc.objects):
    if o in TRUCK: st.objects.link(o)
for o in list(tc.objects):
    if o not in TRUCK: bpy.data.objects.remove(o, do_unlink=True)
bpy.data.collections.remove(tc)
bpy.context.scene.frame_set(37)
bpy.context.view_layer.update()
TW0 = troot.matrix_world.copy()
TGT = Matrix.Translation((0.0, 0.0, -0.0225)) @ Matrix.Rotation(math.pi, 4, 'Z')   # on the haul road, cab toward -X
XFm = TGT @ TW0.inverted()
for o in TRUCK:
    if o.parent is None or o.parent not in TRUCK:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = XFm @ mw
bpy.context.view_layer.update()
print('TRUCK', len(TRUCK), tuple(round(v, 2) for v in troot.matrix_world.translation), flush=True)
heap('rb_load', (5.0, 0.0, BRIM + 0.02), 1.0, 0.32, ORE, c='Stage', seed=81, sq=(0.9, 1.3))
ore_chunks('rb_load_ore', (5.0, 0.0, BRIM + 0.05), 1.0, 30, [(ORE, 5, 'rock'), (HE3, 2, 'he3')], size=(0.1, 0.24), heap=0.3, c='Stage', seed=82)
if not MINEB:   # short stretch of haul road for refinery-only renders
    bm = bmesh.new(); rows = []
    for k in range(15):
        x = -13.0 + k * 1.0
        rows.append([bm.verts.new((x, y, 0.035)) for y in (-1.6, -0.8, 0.0, 0.8, 1.6)])
    for a_, b_ in zip(rows, rows[1:]):
        for i in range(4): bm.faces.new((a_[i], a_[i + 1], b_[i + 1], b_[i]))
    for f in bm.faces:
        if f.normal.z < 0: f.normal_flip()
    _obj(bm, 'haul_road_stub', ROADM, c='Stage', smooth=True, angle=180)

# ====================================================================== lights, sun, review astronauts (Stage), render target
SUN = Vector((-0.55, 0.6, 0.58))      # station camera looks from +Y (world -Y)
world_and_sun(tuple(SUN), 5.5)
astronaut(F((AX - 1.5, CMY - 0.3, ZP)), rot_z=1.2 + math.pi)
astronaut(F((RKX, -21.8, 5.44)), rot_z=-1.4)
_a3 = RH((31.0, -11.6, 0.0)); astronaut(F((_a3[0], _a3[1], 0.0)), rot_z=2.8)
astronaut(F((3.0, -4.2, ZP)), rot_z=2.6)
for nm_, e_, s_ in (('GlowKiln', RH((17.2, HY - 2.4, 2.6)), 60), ('GlowRX', RF((RXX, FY - 2.2, 4.4)), 60)):
    ld = bpy.data.lights.new(nm_, 'POINT'); ld.energy = s_ * 10; ld.color = hexc('#ff8a3a')[:3]; ld.shadow_soft_size = 0.6
    lo = bpy.data.objects.new(nm_, ld); coll('Stage').objects.link(lo); lo.location = F(e_)
ld = bpy.data.lights.new('GlowRack', 'POINT'); ld.energy = 300; ld.color = hexc('#3ab0ff')[:3]; ld.shadow_soft_size = 0.8
lo = bpy.data.objects.new('GlowRack', ld); coll('Stage').objects.link(lo); lo.location = F(RH((32.0, -11.6, 1.6)))
# render-only camera target (the game GLB has NO Cam_Target: the Mine's Cam_Target frames Mine + Refinery)
CAM_TARGET = tuple(float(v) for v in A.get('ct', '-7.0,16.0,3.0').split(','))   # refinery-only review framing
FRAME_W = float(A.get('fw', 34.0))
# Mine station camera (art/3d/buildings/mine/README.md): Cam_Target glTF (-0.11, 2.65, 1.00) = Mine Blender (-0.11, -1.0, 2.65), frame_w 37
MINE_CT = tuple(round(v, 3) for v in (W2F @ Vector([float(v) for v in A.get('minect', '0.06,-1.0,-2.36').split(',')])))
MINE_W = float(A.get('minew', 37.0))
_ct = bpy.data.objects.new('Review_Cam_Target', None); _ct.empty_display_type = 'SPHERE'; _ct.empty_display_size = 0.5
_ct.location = CAM_TARGET; coll('Stage').objects.link(_ct); _ct['frame_w'] = FRAME_W
bpy.context.scene['game_nodes'] = json.dumps(GAME)
convert_curves()
cam = setup_render(48 if not QUICK else 16)

# ====================================================================== stats + export
def tri_count(objs):
    dg = bpy.context.evaluated_depsgraph_get(); t = 0
    for ob in objs:
        if ob.type != 'MESH': continue
        e = ob.evaluated_get(dg); me = e.to_mesh(); me.calc_loop_triangles(); t += len(me.loop_triangles); e.to_mesh_clear()
    return t
mine = [o for o in coll('Mine').all_objects]
mn = Vector((1e9, 1e9, 1e9)); mxv = Vector((-1e9, -1e9, -1e9))
for ob in mine:
    if ob.type != 'MESH': continue
    for c_ in ob.bound_box:
        w = ob.matrix_world @ Vector(c_); mn = Vector(map(min, mn, w)); mxv = Vector(map(max, mxv, w))
from collections import Counter
print('STATS objects', len(mine), 'tris', tri_count(mine), 'bbox', tuple(round(v, 2) for v in mn), tuple(round(v, 2) for v in mxv), flush=True)
print('GROUPS', dict(Counter(o.get('grp', 'Base') for o in mine)), flush=True)
low = [(o.name, round(min((o.matrix_world @ Vector(c)).z for c in o.bound_box), 3)) for o in mine if o.type == 'MESH' and min((o.matrix_world @ Vector(c)).z for c in o.bound_box) < -0.25]
print('BELOW_GROUND', low[:20], flush=True)

ONLY = A.get('only', 'hero')
def phone_cam(w, h, tgt, fw):
    asp = w / h; vt = math.tan(math.radians(19)); d = fw / (2.0 * vt * asp); e = math.radians(18)
    tgt = Vector(tgt); pos = tgt + Vector((0.0, d * math.cos(e), d * math.sin(e)))   # station camera side = +Y here (world -Y)
    cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(38); cam.data.dof.use_dof = False
    cam.location = pos; cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
    return d
if 'glb' in ONLY:
    show_mine(False)
    # GLB origin = REFINERY_ANCHOR: 4.84 m along +X from Path_Dump (the Mine's Path_Dump -> anchor distance); the line runs along
    # anchor-local +Y Blender (= glTF -Z) and the truck sits at glTF +Z 4.84, as the Mine README requires.
    ANCH = Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Translation((-ANCHOR_X, 0.0, 0.0))
    root = bpy.data.objects.new('Refinery', None); coll('Mine').objects.link(root)
    for ob in mine:
        if ob.parent is None: ob.matrix_world = ANCH @ ob.matrix_world; ob.parent = root
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for ob in coll('Mine').all_objects: ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{NAME}_master_raw.glb'), export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_extras=True,
                              export_animations=False, export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False)
    for ob in mine:
        if ob.parent == root:
            mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = ANCH.inverted() @ mw
    bpy.data.objects.remove(root); bpy.context.view_layer.update()
if 'blend' in ONLY:
    if MINEB:   # keep the master lean: the Mine B scene is a review-time import, not part of the refinery master
        for o in list(MINEB.all_objects): bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(MINEB); MINEB = None
        bpy.ops.outliner.orphans_purge(do_recursive=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'{NAME}_master.blend'), compress=True)
if 'turn' in ONLY:
    show_mine(False)
    os.makedirs(os.path.join(OUT, 'turntable'), exist_ok=True)
    tt = [float(v) for v in A.get('tt', '-7,15.5,3').split(',')]
    turntable(cam, os.path.join(OUT, 'turntable'), tuple(tt), float(A.get('td', 58)), 26, size=1000 if not QUICK else 400,
              samples=int(A.get('ts', 40)) if not QUICK else 12, lens=35)
if 'hero' in ONLY:
    show_mine(True)
    w, h = (3840, 2160) if not QUICK else (960, 540)
    if A.get('res'): w, h = [int(v) for v in A['res'].split('x')]
    hp = [float(v) for v in A.get('hc', '13,47,21,13,-1,1.5').split(',')]
    shoot(cam, os.path.join(OUT, f'{NAME}_hero_{w}x{h}.png'), tuple(hp[3:6]), tuple(hp[:3]), w, h, lens=float(A.get('lens', 24)), samples=int(A.get('hs', 48)) if not QUICK else 16)
for mode_ in [m_ for m_ in ('phone', 'phonefull') if m_ in ONLY.split(',')]:
    show_mine(True)
    tgt_, fw_, nm_ = (MINE_CT, MINE_W, 'phone') if mode_ == 'phone' else (CAM_TARGET, FRAME_W, 'phone_full')
    sc = bpy.context.scene
    sizes = [(393, 852), (1179, 2556)] if not QUICK else [(393, 852)]
    if A.get('pres'): sizes = [tuple(int(v) for v in A['pres'].split('x'))]
    for (w, h) in sizes:
        d = phone_cam(w, h, tgt_, fw_)
        sc.render.resolution_x, sc.render.resolution_y = w, h; sc.render.resolution_percentage = 100; sc.render.use_border = False
        sc.cycles.samples = int(A.get('ps', 64)) if not QUICK else 16
        sc.render.filepath = os.path.join(OUT, f'{NAME}_{nm_}_{w}x{h}.png'); print('PHONE', nm_, 'target', tgt_, 'dist', round(d, 3), 'frame_w', fw_, flush=True)
        from bpy_extras.object_utils import world_to_camera_view
        bpy.context.view_layer.update(); _px = []
        for ob in coll('Mine').all_objects:
            if ob.type != 'MESH' or ob.hide_render: continue
            for c_ in ob.data.vertices:
                v = world_to_camera_view(sc, cam, ob.matrix_world @ c_.co); _px.append((v.x * w, (1 - v.y) * h, ob.name))
        _tg = {}
        for ob in coll('Mine').all_objects:
            g_ = ob.get('grp', 'Base')
            if ob.type != 'MESH' or not str(g_).startswith('Tier_'): continue
            for c_ in ob.data.vertices:
                v = world_to_camera_view(sc, cam, ob.matrix_world @ c_.co); e_ = _tg.setdefault(g_, [1e9, -1e9, 1e9, -1e9])
                e_[0] = min(e_[0], v.x * w); e_[1] = max(e_[1], v.x * w); e_[2] = min(e_[2], (1 - v.y) * h); e_[3] = max(e_[3], (1 - v.y) * h)
        for g_, e_ in sorted(_tg.items()):
            ok_ = e_[0] >= 0.06 * w and e_[1] <= 0.94 * w and e_[2] >= 100 * h / 852 and e_[3] <= 650 * h / 852
            print('FIT_TIER %s x %.1f..%.1f y %.1f..%.1f %s' % (g_, e_[0], e_[1], e_[2], e_[3], 'OK' if ok_ else 'OUT'), flush=True)
        if A.get('norender'):
            _o = {}
            for p in _px:
                if p[0] < 0.06 * w or p[0] > 0.94 * w or p[1] > 650 * h / 852: _o[p[2]] = min(_o.get(p[2], 1e9), p[0]) if p[0] < w / 2 else max(_o.get(p[2], -1e9), p[0])
            print('FIT_OUT', sorted(_o.items(), key=lambda kv: kv[1])[:40], flush=True)
        print('FIT refinery px x %.1f..%.1f (%s / %s)  y %.1f..%.1f (%s / %s)  frame %dx%d  safe x %.0f..%.0f y %.0f..%.0f' % (
            min(_px)[0], max(_px)[0], min(_px)[2], max(_px)[2], min(p[1] for p in _px), max(p[1] for p in _px),
            min(_px, key=lambda p: p[1])[2], max(_px, key=lambda p: p[1])[2], w, h, 0.06 * w, 0.94 * w, 100 * h / 852, 650 * h / 852), flush=True)
        if A.get('norender'): continue
        bpy.ops.render.render(write_still=True)
    cam.data.sensor_fit = 'AUTO'
if 'diagram' in ONLY:
    # overhead orthographic plate for the process diagram; label anchors projected to pixels -> diagram_points.json
    show_mine(False)
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene; W_, H_ = (3000, 2000) if not QUICK else (1200, 800)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(A.get('os', 54.0)); cam.data.sensor_fit = 'AUTO'
    cx, cy = [float(v) for v in A.get('dc', '-7,14.0').split(',')]
    tilt = math.radians(float(A.get('tilt', 22)))
    cam.location = (cx, cy + 120 * math.sin(tilt), 120 * math.cos(tilt)); cam.rotation_euler = (tilt, 0, math.pi)
    sc.render.resolution_x, sc.render.resolution_y = W_, H_; sc.render.use_border = False
    sc.cycles.samples = int(A.get('ds', 32)) if not QUICK else 12
    bpy.context.view_layer.update()
    _MH, _MF = RH, RF
    PTS = {'truck': (-1.0, 0, 3.0), 'bin': (5.0, 0, 2.0), 'feeder': (5.1, -3.0, 1.6), 'splitter': (SPN.x, SPN.y, 1.2), 'elevator': (BEX, BEY, 6.0),
           'gallery': (2.4, -18.0, 5.4),
           'sieve': _MH((SVX, HY, 3.4)), 'kiln': _MH((17.2, HY, 3.6)), 'hood': _MH((CPX, HY, 3.0)), 'traps': _MH((27.2, HY, 4.0)), 'column': _MH((DCX, DCY, 8.0)),
           'fill': _MH((FSX, HY - 1.0, 1.5)), 'rack': _MH((31.6, -9.9, 2.4)), 'tailings': _MH((21.5, -12.9, 1.6)),
           'crusher': _MF((CRX, FY, 3.6)), 'magsep': _MF((MSX, FY, 3.0)), 'reactor': _MF((RXX, FY, 7.0)), 'condenser': _MF((WCX, FY, 2.4)),
           'electrolyzer': _MF((ELX, FY, 2.0)), 'liquefier': _MF((LQX, FY, 5.6)), 'lox': _MF((32.4, FY, 6.0)), 'lh2': _MF((36.0, FY, 7.2)),
           'tankfarm': _MF((38.3, 5.22, 1.1)), 'slag': _MF((RXX, FY + 3.4, 1.0)), 'h2x': (RKX, -21.4, 5.7), 'h2recycle': _MF((21.8, FY + 0.5, 9.2)),
           'control': (CMX, CMY, 3.2), 'radiators': _MF((28.0, 12.9, 6.0))}
    out = {}
    for k_, p_ in PTS.items():
        v = world_to_camera_view(sc, cam, Vector(F(p_))); out[k_] = (round(v.x * W_, 1), round((1 - v.y) * H_, 1))
    json.dump({'size': [W_, H_], 'pts': out}, open(os.path.join(OUT, 'diagram_points.json'), 'w'), indent=1)
    print('DIAGPTS', json.dumps(out), flush=True)
    if A.get('norender') != '1':
        sc.render.filepath = os.path.join(OUT, 'diagram_plate.png'); bpy.ops.render.render(write_still=True)
