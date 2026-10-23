"""Planet Stack - CARGO SPACE DOCK + TANK FARM (CSD-01 / TF-1), high-detail concept master (Blender 4.2 LTS, headless, Cycles).

blender -b -P build_dock_tankfarm.py -- --out .. [--quick 1] [--only glb,blend,hero,phone,turn] [--hs 48] [--ts 40] [--ps 48]
                                        [--res WxH] [--pres WxH] [--door 0.5] [--hc x,y,z,tx,ty,tz] [--lens 28] [--td 100]

Follows the Life Support pattern (art/3d/buildings/life_support/_src/build_life_support.py): same Mine-B palette recipe
(add_dust / P_ weathered paints), same helpers (lathe, vvessel, pipe, rail, ladder, stencil, plate, lamp, radiator_array),
same station-camera phone shot and the shared stage from art/3d/mine_concepts/_src/mc_common.py (imported, not modified),
which uses the shared ground material M_ground (cool grey rock with the hill-stripe fix).

Blender coords: Z up, metres, front = -Y (toward the camera). Exported GLB: Y up, front +Z. Origin = station focus
(centre of the container-yard lane); the game camera looks here.

Systems:
  * cargo hall CH-1: white shield-jacketed hall (no glass, no domes), big rolling door (Dock_Door), CARGO SPACE DOCK neon sign
  * container yard on a sintered pad, gantry crane GC-1 on rails (Crane_Gantry), stacked containers, He-3 canister, armored Pt crate
  * airlock A2 with dust shower, grated mat and brush station
  * power: switchgear SWG-2, power line on masts, solar masts, radiator wing RAD-1
  * Tank Farm TF-1 beside it behind a low L-berm: cryo tanks LOX-1/2, LCH4-1/2, HE3-1, pump skid PS-1, catwalk + stair tower,
    insulated lines with valves running TO LAUNCH PAD
Game-GLB grouping: objects carry ob['grp'] (Tier_03/05/08/12/20, Crane_Gantry, Dock_Door, Beacon_Lights; default Base);
pivots + markers are stored as JSON in scene['game_nodes'] for _src/build_game_glb_tiered.py.
"""
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__))
MC = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'mine_concepts', '_src'))
sys.path.insert(0, MC)
import bpy, bmesh
from mathutils import Vector, Matrix, noise
from mc_common import *
from mc_common import _obj, _nodes

A = argv(); OUT = os.path.abspath(A.get('out', '/tmp/dk_out')); os.makedirs(OUT, exist_ok=True)
QUICK = A.get('quick') == '1'
reset(); rr = random.Random(91)
TAU = math.tau
NAME = 'dock_tankfarm'

class grp:
    """tag every object created inside the block with ob['grp'] (game-GLB node)."""
    def __init__(s, g): s.g = g
    def __enter__(s): s.k = set(bpy.data.objects.keys()); return s
    def __exit__(s, *a):
        for n in set(bpy.data.objects.keys()) - s.k: bpy.data.objects[n]['grp'] = s.g

# ====================================================================== materials (Life Support recipe, DK_ names)
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

WHITE  = P_('DK_White', '#eceff2', rough=0.24, metal=0.0, coat=0.8, grime=0.28, grime_col='#9b9da0', wear=0.15, wear_col='#9aa3ad', panel=0.8, bevel=0.03, dirt_scale=1.5)
WHITE_S = P_('DK_WhiteSmooth', '#eef1f4', rough=0.2, metal=0.0, coat=0.9, grime=0.22, grime_col='#9b9da0', wear=0.12, wear_col='#9aa3ad', bevel=0.03)
PALE   = P_('DK_WhitePanel', '#e2e6eb', rough=0.26, metal=0.0, coat=0.7, grime=0.3, grime_col='#9b9da0', wear=0.17, wear_col='#9aa3ad', panel=0.8, bevel=0.02)
GRAPH  = P_('DK_Graphite', '#2c3137', rough=0.3, metal=0.55, coat=0.5, grime=0.22, grime_col='#6b6e72', wear=0.24, wear_col='#9aa0a6', panel=1.4, bevel=0.02)
GRAPH2 = P_('DK_Graphite2', '#30353c', rough=0.28, metal=0.6, coat=0.5, grime=0.24, grime_col='#6b6e72', wear=0.22, wear_col='#9aa0a6', panel=1.6, bevel=0.02)
STEEL  = P_('DK_Satin', '#9aa3ad', rough=0.28, metal=1.0, grime=0.25, grime_col='#5a5c60', wear=0.12, wear_col='#d0d5db', bevel=0.015)
STEELL = P_('DK_SatinLight', '#b9c0c8', rough=0.24, metal=1.0, grime=0.2, grime_col='#5a5c60', wear=0.1, wear_col='#e0e4e8', bevel=0.01)
TRIM   = P_('DK_WhiteTrim', '#e9edf1', rough=0.22, metal=0.0, coat=0.8, grime=0.22, grime_col='#9b9da0', wear=0.18, wear_col='#8f969e', bevel=0.02)
RED    = P_('DK_Red', '#b8322c', rough=0.35, metal=0.1, coat=0.5, grime=0.2, wear=0.2)
FOIL   = P_('DK_MLI', '#c9ced6', rough=0.3, metal=0.9, grime=0.2, grime_col='#5b5d60', bump_noise=0.5, bevel=0.01)
RUBBER = P_('DK_Rubber', '#1d2024', rough=0.8, metal=0.0, grime=0.3, grime_col='#6e7074', bump_noise=0.3)
PT     = P_('DK_Platinum', '#dcdfe4', rough=0.16, metal=1.0, grime=0.12, grime_col='#6a6d72', wear=0.05, wear_col='#f4f6f8', bevel=0.01)
DARKI  = P_('DK_Interior', '#25292e', rough=0.5, metal=0.3, grime=0.3, grime_col='#4a4d52', panel=0.6, bevel=0.01)
CHROME = M_paint('DK_Chrome', '#dfe3e9', rough=0.15, metal=1.0, bevel=0.005)
INK    = M_paint('DK_Ink', '#1f2329', rough=0.5, metal=0.0)
INKW   = M_paint('DK_InkWhite', '#f4f7fa', rough=0.4, metal=0.0)
GLASS  = M_glass('DK_Port', '#1b2a36', 0.04)
LAMP   = M_glow('DK_Lamp', '#f2fbff', 12)
AMBERL = M_glow('DK_StatusWhite', '#dff8ff', 9)
GREENL = M_glow('DK_GreenLamp', '#6ee08a', 7)
REDL   = M_glow('DK_RedLamp', '#f25f5c', 8)
CYANL  = M_glow('DK_Cyan', '#2fe3ff', 10)
CYANS  = M_glow('DK_CyanSoft', '#2fe3ff', 4)
NEON   = M_glow('DK_NeonBlue', '#3d8bff', 16)

def M_he3_glow(name='DK_He3'):
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

def M_radiator(name='DK_Radiator'):
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

def M_cells(name='DK_SolarCells'):
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

def M_pad(name='DK_Pad'):
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
ROADM = M_rock('DK_Road', '#5d5f63', '#77797d')

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

# ====================================================================== YARD PAD (sintered; everything in the yard sits at ZP)
ZP = 0.12
box('yard_pad', (26.0, 20.6, 0.42), (-0.5, -6.6, ZP - 0.21), PADM, bevel=0.05)
for x in (-13.0, 12.0):
    box('pad_curb', (0.3, 20.6, 0.3), (x + (0.15 if x < 0 else -0.15), -6.6, ZP + 0.05), GRAPH, bevel=0.03)
box('pad_curb', (26.0, 0.3, 0.3), (-0.5, -16.75, ZP + 0.05), GRAPH, bevel=0.03)
for k in range(13):
    x = -12.0 + k * 2.0
    if abs(x) > 3.2: box('pad_cyan', (0.5, 0.04, 0.06), (x, -16.92, ZP + 0.12), CYANS)
for sx in (-1, 1): box('lane_line', (0.14, 18.0, 0.012), (sx * 2.65, -7.4, ZP + 0.006), INKW, bevel=0.0)
for (a, b) in (((-1.6, -7.6), (1.6, -7.6)), ((-1.6, -4.4), (1.6, -4.4)), ((-1.6, -7.6), (-1.6, -4.4)), ((1.6, -7.6), (1.6, -4.4))):
    beam('drop_box', (a[0], a[1], ZP + 0.006), (b[0], b[1], ZP + 0.006), 0.12, 0.012, CYANS, bevel=0.0)

# ====================================================================== CARGO HALL CH-1 (above ground, shield-jacketed, rounded shoulders)
HW, WALLH, CROWN = 11.0, 10.0, 13.2
HY0, HY1 = 4.0, 22.0
FY0, FY1 = HY0 - 0.5, HY0 + 0.12
DW2, DH = 4.6, 7.4
shell('hall_core', hprof(HW - 0.35, WALLH, CROWN - 0.35), 0.3, HY0, HY1, DARKI)
nseg = 6; sw = (HY1 - HY0 - 0.1) / nseg
for k in range(nseg):
    y0 = HY0 + 0.1 + k * sw
    shell('hall_shield', hprof(HW, WALLH, CROWN), 0.36, y0 + 0.07, y0 + sw - 0.07, WHITE, bevel=0.03)
for k in range(nseg + 1):
    y0 = HY0 + 0.1 + k * sw
    shell('hall_seam', hprof(HW + 0.07, WALLH, CROWN + 0.07), 0.3, y0 - 0.08, y0 + 0.08, GRAPH2)
for sx in (-1, 1):
    box('hall_cyan', (0.04, HY1 - HY0 - 0.4, 0.07), (sx * (HW + 0.09), (HY0 + HY1) / 2, 3.2), CYANL, bevel=0.0)
    box('hall_plinth', (0.5, HY1 - HY0, 0.6), (sx * (HW + 0.05), (HY0 + HY1) / 2, 0.3), GRAPH, bevel=0.03)
    for k in range(nseg):
        y = HY0 + 0.1 + (k + 0.5) * sw
        if k % 2 == 0: box('hall_hatch', (0.08, 1.2, 1.6), (sx * (HW + 0.02), y, 1.6), PALE, bevel=0.03)
        else:
            box('hall_vent', (0.1, 1.4, 0.7), (sx * (HW + 0.03), y, 7.2), GRAPH2, bevel=0.02)
            for j in range(5): box('hall_louver', (0.12, 1.3, 0.04), (sx * (HW + 0.05), y, 6.95 + j * 0.12), STEEL, bevel=0.0)
prism('hall_back', hprof(HW + 0.07, WALLH, CROWN + 0.07), HY1, HY1 + 0.4, WHITE_S)
box('hall_back_door', (3.0, 0.1, 3.4), (-5.0, HY1 + 0.42, 1.7), PALE, bevel=0.03)
pw = HW + 0.15 - (DW2 + 0.6)
for sx in (-1, 1):
    box('fac_pier', (pw, FY1 - FY0, WALLH), (sx * (DW2 + 0.6 + pw / 2), (FY0 + FY1) / 2, WALLH / 2), WHITE, bevel=0.04)
    box('fac_jamb', (0.6, FY1 - FY0 + 0.24, 8.0), (sx * (DW2 + 0.3), (FY0 + FY1) / 2 - 0.08, 4.0), GRAPH2, bevel=0.04)
    box('fac_jamb_cyan', (0.07, 0.04, 7.0), (sx * (DW2 + 0.3), FY0 - 0.22, 3.8), CYANL, bevel=0.0)
    box('fac_bumper', (0.5, 0.5, 1.2), (sx * (DW2 + 0.35), FY0 - 0.35, 0.6), GRAPH, bevel=0.06)
    box('fac_pier_cyan', (pw - 0.6, 0.04, 0.07), (sx * (DW2 + 0.6 + pw / 2), FY0 - 0.02, 3.2), CYANL, bevel=0.0)
box('fac_lintel', (2 * (DW2 + 0.6), FY1 - FY0, WALLH - 8.0), (0, (FY0 + FY1) / 2, 9.0), WHITE, bevel=0.04)
prism('fac_arch', hprof(HW + 0.15, WALLH, CROWN + 0.15)[1:-1], FY0, FY1, WHITE)
box('fac_header', (2 * (DW2 + 0.6), FY1 - FY0 + 0.24, 0.6), (0, (FY0 + FY1) / 2 - 0.08, 7.7), GRAPH2, bevel=0.04)
box('door_drum', (2 * DW2 + 1.0, 0.95, 0.9), (0, FY0 - 0.5, 7.9), GRAPH, bevel=0.06)
for sx in (-1, 1): cyl('door_drum_cap', 0.4, 0.12, (sx * (DW2 + 0.55), FY0 - 0.5, 7.9), STEELL, rot=(0, math.pi / 2, 0), segs=20)
box('door_drum_cyan', (2 * DW2 + 0.6, 0.04, 0.06), (0, FY0 - 0.99, 7.62), CYANL, bevel=0.0)
box('door_sill', (2 * DW2 + 0.2, 0.7, 0.06), (0, FY0 + 0.2, 0.03), STEEL, bevel=0.01)
# rolling door (Dock_Door): slatted curtain under the drum; pivot at the top of the opening (curtain rolls up = scale Z)
DOOR_Y = FY0 + 0.22
rig = bpy.data.objects.new('DoorRig', None); coll('Mine').objects.link(rig); rig.location = (0, DOOR_Y, DH)
with grp('Dock_Door'):
    ns = 25; pitch = DH / ns
    for k in range(ns):
        z = k * pitch + pitch / 2
        m_ = GRAPH2 if k == 0 else (WHITE if (k // 4) % 2 == 0 else PALE)
        box('door_slat', (2 * DW2 + 0.1, 0.12 if k else 0.2, pitch - 0.03), (0, DOOR_Y, z), m_, bevel=0.015)
    box('door_cyan', (2 * DW2 - 0.2, 0.04, 0.06), (0, DOOR_Y - 0.12, pitch * 0.5), CYANL, bevel=0.0)
    for sx in (-1, 1): box('door_grip', (0.5, 0.08, 0.12), (sx * 2.5, DOOR_Y - 0.1, pitch * 1.3), STEELL, bevel=0.02)
    for k in range(3): box('door_window', (1.1, 0.04, 0.3), (-3.0 + k * 3.0, DOOR_Y - 0.07, 4.6), GRAPH, bevel=0.0)
bpy.context.view_layer.update()
for ob in [o for o in coll('Mine').objects if o.get('grp') == 'Dock_Door']:
    ob.parent = rig; ob.matrix_parent_inverse = rig.matrix_world.inverted()
GAME['pivots']['Dock_Door'] = (0.0, DOOR_Y, DH)
box('hall_floor', (2 * HW - 0.8, HY1 - HY0 - 0.2, 0.1), (0, (HY0 + HY1) / 2, 0.05), DARKI, bevel=0.0)
for k in range(4):
    for sx in (-1, 1): box('hall_lightbar', (0.3, 3.2, 0.08), (sx * 4.0, HY0 + 3.0 + k * 4.2, 10.6), LAMP, bevel=0.0)
for sx in (-1, 1): box('hall_floor_cyan', (0.12, HY1 - HY0 - 1.0, 0.012), (sx * 3.2, (HY0 + HY1) / 2, 0.106), CYANS, bevel=0.0)
# signage: CARGO SPACE DOCK in blue neon on a graphite backing above the door
SZ = 11.9
box('sign_back', (10.6, 0.22, 1.34), (0, FY0 - 0.14, SZ), GRAPH, bevel=0.04)
for sx in (-4.6, 0.0, 4.6): box('sign_bracket', (0.12, 0.3, 0.12), (sx, FY0 - 0.05, SZ + 0.6), STEEL, bevel=0.01)
sg = text('sign_neon', 'CARGO SPACE DOCK', (0, FY0 - 0.28, SZ - 0.02), (math.pi / 2, 0, 0), 0.86, NEON, extrude=0.045)
sg.data.resolution_u = 4; sg.data.space_character = 1.06
curve_tube('sign_neon_frame', [(-5.15, FY0 - 0.27, SZ - 0.58), (5.15, FY0 - 0.27, SZ - 0.58), (5.15, FY0 - 0.27, SZ + 0.58), (-5.15, FY0 - 0.27, SZ + 0.58)], 0.035, NEON, closed=True, res=2)
stencil('st_csd', 'CSD-01  -  CARGO HALL CH-1', (-8.0, FY0 - 0.01, 8.9), '-y', 0.28, INK)
stencil('st_csd2', 'RECEIVING  /  LOADING', (8.0, FY0 - 0.01, 8.9), '-y', 0.28, INK)
stencil('st_door', 'BAY 1   -   KEEP CLEAR', (0, FY0 - 0.99, 7.92), '-y', 0.22, INKW)
# roof: crown walkway, vents, comm dish, beacons (Beacon_Lights)
def roofz(x): return WALLH + (CROWN - WALLH) * math.sin(math.acos(min(1.0, abs(x) / HW)))
box('roof_walk', (1.1, HY1 - HY0 - 1.0, 0.1), (0, (HY0 + HY1) / 2, CROWN + 0.08), GRAPH2, bevel=0.01)
for y in (8.0, 13.0, 18.0):
    for sx in (-2.6, 2.6):
        zr = roofz(sx)
        cyl('roof_vent', 0.32, 1.0, (sx, y, zr + 0.4), STEELL, segs=16); cyl('roof_vent_cap', 0.42, 0.12, (sx, y, zr + 0.95), GRAPH, segs=16)
zr = roofz(6.0)
rod('ant_mast', (6.0, 18.0, zr - 0.2), (6.0, 18.0, zr + 3.0), 0.08, STEEL, segs=10)
sphere('ant_dish', 0.8, (6.0, 17.8, zr + 3.2), WHITE_S, scale=(1, 0.3, 1), sub=3, rot=(0.5, 0, 0.6))
BEAC = []
for sx in (-1, 1):
    bx = sx * 9.2; zr = roofz(9.2)
    rod('beacon_mast', (bx, HY0 + 0.9, zr - 0.3), (bx, HY0 + 0.9, zr + 1.5), 0.07, STEEL, segs=10)
    with grp('Beacon_Lights'): sphere('beacon_hall', 0.2, (bx, HY0 + 0.9, zr + 1.7), AMBERL, sub=2)
    cyl('beacon_hall_base', 0.22, 0.18, (bx, HY0 + 0.9, zr + 1.45), GRAPH, segs=12)
    BEAC.append((bx, HY0 + 0.9, zr + 1.7))
GAME['pivots']['Beacon_Lights'] = BEAC[0]
# switchgear SWG-2 at the left pier, where the power line lands
SWX, SWY = -8.4, FY0 - 0.6
box('swg_plinth', (2.8, 1.2, 0.2), (SWX, SWY, ZP + 0.1), GRAPH, bevel=0.03)
box('swg_body', (2.5, 0.9, 2.2), (SWX, SWY + 0.05, ZP + 1.3), WHITE_S, bevel=0.04)
box('swg_roof', (2.7, 1.1, 0.12), (SWX, SWY, ZP + 2.46), GRAPH2, bevel=0.02)
for k in range(3):
    x = SWX - 0.8 + k * 0.8
    box('swg_door', (0.74, 0.04, 1.9), (x, SWY - 0.42, ZP + 1.3), WHITE_S, bevel=0.015)
    box('swg_handle', (0.05, 0.05, 0.3), (x + 0.27, SWY - 0.46, ZP + 1.25), CHROME, bevel=0.01)
    lamp(f'swg_lamp{k}', (x + 0.2, SWY - 0.46, ZP + 2.0), [GREENL, GREENL, AMBERL][k], 0.04)
    for j in range(5): box('swg_louver', (0.55, 0.03, 0.03), (x, SWY - 0.45, ZP + 0.6 + j * 0.08), GRAPH)
box('swg_cyan', (2.52, 0.02, 0.05), (SWX, SWY - 0.46, ZP + 0.35), CYANL, bevel=0.0)
plate('swg_plate', 'SWG-2', (SWX - 0.8, SWY - 0.47, ZP + 1.55), '-y', 0.7, 0.38, 0.16, sub='DOCK FEED 1.2 kV')
for k, dx in enumerate((-0.15, 0.0, 0.15)):
    pipe('swg_conduit', [(SWX + 0.6 + dx, SWY + 0.4, ZP + 2.4), (SWX + 0.6 + dx, SWY + 0.4, 6.4), (SWX + 0.6 + dx, FY0 - 0.02, 6.6)], 0.05, [RUBBER, RED, RUBBER][k], bend=0.3, flanges=False)
for sx in (-7.6, 7.6):
    box('flood', (0.8, 0.35, 0.22), (sx, FY0 - 0.25, 8.2), GRAPH, rot=(0.5, 0, 0), bevel=0.03)
    box('flood_lens', (0.7, 0.02, 0.14), (sx, FY0 - 0.43, 8.13), LAMP, rot=(0.5, 0, 0))

# ====================================================================== AIRLOCK A2 + dust shower (right pier)
AX, AZ, AR = 9.25, 1.95, 1.3
AY1 = 0.7
rod('airlock', (AX, FY0 + 0.05, AZ), (AX, AY1, AZ), AR, WHITE, segs=48)
for y in (FY0 - 0.6, 1.9, AY1 + 0.15): rod('al_ring', (AX, y - 0.07, AZ), (AX, y + 0.07, AZ), AR + 0.05, STEELL, segs=48)
rod('al_cyan', (AX, 1.35, AZ), (AX, 1.4, AZ), AR + 0.02, CYANL, segs=48)
sphere('al_head', AR, (AX, AY1, AZ), WHITE_S, scale=(1, 0.28, 1), sub=4)
for sx in (-1, 1):
    for y in (1.2, 2.6): box('al_saddle', (0.35, 0.4, AZ - AR + 0.25), (AX + sx * 0.8, y, ZP + (AZ - AR + 0.25) / 2 - 0.05), GRAPH, bevel=0.03)
HYH = AY1 - AR * 0.28 - 0.02
box('hatch_frame', (1.2, 0.16, 1.7), (AX, HYH + 0.04, AZ - 0.05), STEELL, bevel=0.08, segs=3)
box('hatch_door', (0.98, 0.14, 1.48), (AX, HYH - 0.03, AZ - 0.05), PALE, bevel=0.07, segs=3)
cyl('hatch_port', 0.12, 0.05, (AX, HYH - 0.1, AZ + 0.42), GRAPH, rot=(math.pi / 2, 0, 0), segs=24)
cyl('hatch_port_ring', 0.15, 0.04, (AX, HYH - 0.09, AZ + 0.42), STEELL, rot=(math.pi / 2, 0, 0), segs=24)
handwheel('hatch_wheel', (AX, HYH - 0.18, AZ - 0.1), 0.2, axis='y', mat=CHROME)
box('hatch_cyan', (1.22, 0.02, 0.04), (AX, HYH - 0.05, AZ - 0.92), CYANL, bevel=0.0)
stencil('st_al', 'AIRLOCK A2', (AX, HYH - 0.03, AZ + 0.93), '-y', 0.15)
lamp('al_lamp_g', (AX - 0.35, HYH - 0.05, AZ + 1.2), GREENL, 0.06); lamp('al_lamp_a', (AX + 0.35, HYH - 0.05, AZ + 1.2), AMBERL, 0.06)
GY0, GY1, GW = HYH - 0.65, -3.0, 2.4
MZ = ZP + 0.2
box('al_step', (1.3, 0.6, AZ - 0.85 - MZ), (AX, HYH - 0.35, MZ + (AZ - 0.85 - MZ) / 2), GRAPH2, bevel=0.02)
box('mat_pan', (GW + 0.2, GY0 - GY1 + 0.2, 0.16), (AX, (GY0 + GY1) / 2, ZP + 0.08), GRAPH, bevel=0.02)
for k in range(int(GW / 0.09)):
    x = AX - GW / 2 + 0.05 + k * 0.09; beam('grate', (x, GY0, MZ - 0.025), (x, GY1, MZ - 0.025), 0.014, 0.05, STEELL, bevel=0.0)
for k in range(int((GY0 - GY1) / 0.4) + 1):
    y = GY1 + k * 0.4; beam('grate_x', (AX - GW / 2, y, MZ - 0.025), (AX + GW / 2, y, MZ - 0.025), 0.02, 0.05, STEEL, bevel=0.0)
box('mat_slab', (GW, GY0 - GY1, 0.05), (AX, (GY0 + GY1) / 2, MZ - 0.06), GRAPH2, bevel=0.0)
box('mat_cyan', (GW + 0.2, 0.05, 0.03), (AX, GY1 - 0.05, MZ - 0.02), CYANL, bevel=0.0)
box('mat_ramp', (GW, 0.8, 0.06), (AX, GY1 - 0.45, ZP + 0.07), GRAPH2, rot=(0.2, 0, 0), bevel=0.01)
rail('mat_rail', [(AX - GW / 2 - 0.02, GY1, MZ), (AX - GW / 2 - 0.02, -1.25, MZ)], TRIM)
ASY = -1.0
for sx in (-1, 1):
    box('shower_post', (0.18, 0.3, 2.5), (AX + sx * 1.45, ASY, MZ + 1.25), GRAPH2, bevel=0.03)
    for k in range(6): cyl('nozzle', 0.035, 0.09, (AX + sx * 1.35, ASY, MZ + 0.4 + k * 0.36), CHROME, rot=(0, math.pi / 2, 0), segs=8)
box('shower_head', (3.1, 0.34, 0.24), (AX, ASY, MZ + 2.55), GRAPH2, bevel=0.03)
for k in range(8): cyl('nozzle_top', 0.035, 0.09, (AX - 1.15 + k * 0.33, ASY, MZ + 2.4), CHROME, segs=8)
box('shower_cyan', (3.12, 0.02, 0.05), (AX, ASY - 0.18, MZ + 2.55), CYANL, bevel=0.0)
stencil('st_dust', 'DUST SHOWER  -  BLOW / BRUSH / STEP', (AX, ASY - 0.19, MZ + 2.73), '-y', 0.09, INK)
box('blower', (0.7, 0.7, 0.8), (AX + 1.95, ASY + 0.5, ZP + 0.4), GRAPH2, bevel=0.04)
pipe('blow_hose', [(AX + 1.95, ASY + 0.5, ZP + 0.8), (AX + 1.95, ASY + 0.5, MZ + 1.3), (AX + 1.54, ASY, MZ + 1.3)], 0.06, RUBBER, bend=0.3)
for sy in (-1.7, -2.7): box('brush_post', (0.14, 0.14, 1.4), (AX + 1.75, sy, ZP + 0.7), STEEL, bevel=0.02)
for zz, rr_ in ((0.32, 0.17), (1.1, 0.14)):
    cyl('brush', rr_, 0.9, (AX + 1.75, -2.2, ZP + zz), RUBBER, rot=(math.pi / 2, 0, 0), segs=20, bevel=0.0)
    cyl('brush_core', rr_ * 0.4, 1.05, (AX + 1.75, -2.2, ZP + zz), CHROME, rot=(math.pi / 2, 0, 0), segs=12)

# ====================================================================== GANTRY CRANE GC-1 on rails (Crane_Gantry)
GX, YG = 7.2, -9.0
RY0, RY1 = -14.6, 2.7
RT = ZP + 0.2                       # rail top
for sx in (-1, 1):
    X = sx * GX
    box('rail_bed', (0.9, RY1 - RY0, 0.06), (X, (RY0 + RY1) / 2, ZP + 0.03), GRAPH, bevel=0.01)
    beam('rail', (X, RY0, ZP + 0.13), (X, RY1, ZP + 0.13), 0.16, 0.14, STEELL, bevel=0.005)
    for k in range(int((RY1 - RY0) / 1.2) + 1): box('rail_clip', (0.5, 0.14, 0.05), (X, RY0 + 0.2 + k * 1.2, ZP + 0.085), STEEL, bevel=0.0)
    for y, s_ in ((RY0, 1), (RY1, -1)):
        box('rail_stop', (0.8, 0.5, 0.8), (X, y + 0.25 * s_, ZP + 0.4), GRAPH2, bevel=0.04)
        box('rail_stop_cyan', (0.82, 0.04, 0.06), (X, y + 0.5 * s_ + 0.0, ZP + 0.62), CYANL, bevel=0.0)
        box('rail_buffer', (0.36, 0.3, 0.36), (X, y + 0.65 * s_, ZP + 0.45), RUBBER, bevel=0.04)
TX = 4.0; SPZ = 8.6
with grp('Crane_Gantry'):
    WR = 0.36; WZ = RT + WR
    GZ = 10.6
    for sx in (-1, 1):
        X = sx * GX
        for px in (-0.32, 0.32): box('gc_bogie_plate', (0.1, 5.0, 0.95), (X + px, YG, WZ + 0.1), GRAPH2, bevel=0.02)
        box('gc_bogie_top', (0.9, 5.2, 0.45), (X, YG, WZ + 0.75), GRAPH, bevel=0.04)
        for wy in (-1.9, -0.7, 0.7, 1.9):
            cyl('gc_wheel', WR, 0.26, (X, YG + wy, WZ), STEEL, rot=(0, math.pi / 2, 0), segs=24, bevel=0.01)
            cyl('gc_axle', 0.08, 0.76, (X, YG + wy, WZ), CHROME, rot=(0, math.pi / 2, 0), segs=10)
        box('gc_bogie_cyan', (0.92, 5.0, 0.05), (X, YG, WZ + 0.52), CYANL, bevel=0.0)
        for sy in (-1, 1): box('gc_buffer', (0.4, 0.3, 0.4), (X, YG + sy * 2.75, WZ + 0.5), RUBBER, bevel=0.04)
        for sy in (-1, 1):
            beam('gc_leg', (X, YG + sy * 2.0, WZ + 0.9), (X, YG + sy * 0.75, GZ - 0.6), 0.72, 0.72, WHITE, bevel=0.04)
            beam('gc_leg_cyan', (X - sx * 0.37, YG + sy * 1.95, WZ + 1.3), (X - sx * 0.37, YG + sy * 0.8, GZ - 1.0), 0.05, 0.08, CYANL, bevel=0.0)
        beam('gc_tie', (X, YG - 1.45, 5.6), (X, YG + 1.45, 5.6), 0.36, 0.5, GRAPH2, bevel=0.02)
        beam('gc_brace', (X, YG - 1.6, WZ + 1.6), (X, YG + 1.0, 5.35), 0.18, 0.18, STEEL, bevel=0.01)
        beam('gc_brace', (X, YG + 1.6, WZ + 1.6), (X, YG - 1.0, 5.35), 0.18, 0.18, STEEL, bevel=0.01)
        box('gc_endcar', (1.3, 3.0, 1.7), (X, YG, GZ), GRAPH2, bevel=0.06)
        box('gc_endcar_cyan', (1.32, 0.05, 0.06), (X, YG - 1.51, GZ - 0.4), CYANL, bevel=0.0)
    for gy in (-0.85, 0.85):
        box('gc_girder', (2 * GX + 1.4, 0.75, 1.45), (0, YG + gy, GZ + 0.05), WHITE, bevel=0.05)
        box('gc_girder_cyan', (2 * GX + 0.6, 0.05, 0.06), (0, YG + gy + (-0.4 if gy < 0 else 0.4), GZ - 0.5), CYANL, bevel=0.0)
        beam('gc_trolley_rail', (-GX + 0.6, YG + gy, GZ + 0.83), (GX - 0.6, YG + gy, GZ + 0.83), 0.14, 0.12, STEELL, bevel=0.005)
    for k in range(7): box('gc_diaphragm', (0.12, 1.0, 0.3), (-GX + 1.0 + k * 2.2, YG, GZ + 0.62), GRAPH2, bevel=0.01)
    stencil('st_gc', 'GC-1   40 t', (-2.0, YG - 1.24, GZ + 0.05), '-y', 0.55, INK)
    box('gc_trolley', (2.8, 2.7, 0.62), (TX, YG, GZ + 1.2), GRAPH2, bevel=0.05)
    box('gc_house', (2.0, 2.2, 0.32), (TX, YG, GZ + 1.62), WHITE_S, bevel=0.06)
    box('gc_house_cyan', (2.82, 0.04, 0.06), (TX, YG - 1.36, GZ + 1.2), CYANL, bevel=0.0)
    for j in range(3): box('gc_house_louver', (0.6, 0.04, 0.04), (TX + 0.6, YG - 1.37, GZ + 1.02 + j * 0.1), GRAPH)
    rod('gc_drum', (TX - 1.1, YG, GZ + 0.62), (TX + 1.1, YG, GZ + 0.62), 0.32, STEEL, segs=24)
    for dx in (-0.9, 0.9):
        for dy in (-0.5, 0.5): rod('gc_rope', (TX + dx, YG + dy, GZ + 0.9), (TX + dx * 1.2, YG + dy * 4.6, SPZ + 0.2), 0.03, STEEL, segs=6)
    box('gc_spreader', (2.5, 6.2, 0.38), (TX, YG, SPZ), GRAPH, bevel=0.03)
    box('gc_spreader_beam', (0.6, 6.4, 0.3), (TX, YG, SPZ + 0.3), TRIM, bevel=0.03)
    box('gc_spreader_cyan', (2.52, 0.05, 0.06), (TX, YG - 3.11, SPZ), CYANL, bevel=0.0)
    for ux in (-1, 1):
        for uy in (-1, 1): box('gc_twistlock', (0.2, 0.2, 0.3), (TX + ux * 1.1, YG + uy * 2.9, SPZ - 0.3), STEELL, bevel=0.02)
    box('gc_cab', (1.7, 1.7, 1.8), (GX - 1.6, YG - 1.45, GZ - 1.55), WHITE_S, bevel=0.08)
    box('gc_cab_win', (1.4, 0.04, 0.8), (GX - 1.6, YG - 2.31, GZ - 1.35), GRAPH, bevel=0.0)
    box('gc_cab_win_glow', (1.3, 0.02, 0.06), (GX - 1.6, YG - 2.34, GZ - 1.0), LAMP, bevel=0.0)
    box('gc_cab_roof', (1.9, 1.9, 0.12), (GX - 1.6, YG - 1.45, GZ - 0.6), GRAPH2, bevel=0.02)
    box('gc_cab_cyan', (1.72, 0.04, 0.05), (GX - 1.6, YG - 2.32, GZ - 1.85), CYANL, bevel=0.0)
    ladder('gc_ladder', GX + 0.6, YG, WZ + 1.0, GZ - 0.9, along='y')
    cyl('gc_reel', 0.7, 0.4, (-GX - 0.75, YG + 1.4, WZ + 1.4), GRAPH2, rot=(0, math.pi / 2, 0), segs=24)
    for sx in (-1, 1): lamp(f'gc_warn{sx}', (sx * GX, YG - 1.55, GZ + 0.95), AMBERL, 0.1)
GAME['pivots']['Crane_Gantry'] = (0.0, YG, RT)

# ====================================================================== CONTAINERS (6.06 x 2.44 x 2.59, long axis along Y)
CL, CW, CH = 6.06, 2.44, 2.59
def container(cx, cy, z0, mat, ident='PSCU 204417', tag='cont', strip=True):
    sx, sy = CW, CL; zc = z0 + CH / 2
    box(tag + '_body', (sx - 0.1, sy - 0.1, CH - 0.14), (cx, cy, zc), mat, bevel=0.03)
    for ux in (-1, 1):
        for uy in (-1, 1):
            box(tag + '_post', (0.17, 0.17, CH), (cx + ux * (sx / 2 - 0.085), cy + uy * (sy / 2 - 0.085), zc), GRAPH2, bevel=0.015)
            for zz in (z0 + 0.09, z0 + CH - 0.09): box(tag + '_casting', (0.2, 0.2, 0.18), (cx + ux * (sx / 2 - 0.1), cy + uy * (sy / 2 - 0.1), zz), GRAPH, bevel=0.01)
    for zz in (z0 + 0.07, z0 + CH - 0.07):
        for u in (-1, 1):
            box(tag + '_srail', (0.12, sy - 0.2, 0.14), (cx + u * (sx / 2 - 0.06), cy, zz), GRAPH2, bevel=0.01)
            box(tag + '_erail', (sx - 0.2, 0.12, 0.14), (cx, cy + u * (sy / 2 - 0.06), zz), GRAPH2, bevel=0.01)
    for k in range(10):
        t = -CL / 2 + 0.45 + k * (CL - 0.9) / 9
        for u in (-1, 1): box(tag + '_rib', (0.05, 0.16, CH - 0.4), (cx + u * (sx / 2 - 0.03), cy + t, zc), mat, bevel=0.0)
    ey = cy - sy / 2 + 0.02
    for dx in (-0.75, -0.3, 0.3, 0.75): rod(tag + '_bar', (cx + dx, ey - 0.06, z0 + 0.25), (cx + dx, ey - 0.06, z0 + CH - 0.25), 0.025, STEELL, segs=8)
    box(tag + '_doorline', (0.03, 0.02, CH - 0.3), (cx, ey - 0.02, zc), GRAPH, bevel=0.0)
    if strip: box(tag + '_cyan', (sx - 0.5, 0.03, 0.06), (cx, ey - 0.03, z0 + CH - 0.35), CYANS, bevel=0.0)
    ink = INKW if mat in (GRAPH, GRAPH2) else INK
    stencil('st_' + tag, ident, (cx, ey - 0.04, z0 + CH - 0.62), '-y', 0.2, ink)
    for u in (-1, 1): stencil('st_' + tag + '_side', ident, (cx + u * (sx / 2 + 0.01), cy - 1.2, z0 + CH - 0.55), '+x' if u > 0 else '-x', 0.24, ink)
CMATS = [WHITE, PALE, GRAPH, WHITE_S]
def stack(cx, cy, levels, seed):
    r_ = random.Random(seed)
    for lv in levels:
        m_ = CMATS[r_.randrange(len(CMATS))]
        container(cx, cy, ZP + lv * CH, m_, ident=f'PSCU {r_.randrange(100000, 999999)}')
stack(-4.0, -3.0, (0, 1), 11); stack(-4.0, -9.6, (0, 1), 12)
stack(4.0, -3.0, (0, 1), 13); stack(4.0, -9.6, (0,), 14)
with grp('Tier_03'):
    stack(-4.0, -3.0, (2,), 21); stack(4.0, -9.6, (1,), 22); stack(-4.0, -9.6, (2,), 23)
with grp('Crane_Gantry'):
    container(TX, YG, SPZ - 0.19 - CH, WHITE, ident='PSCU 771203', tag='gc_cont')
GAME['markers']['Container_Stack'] = (-4.0, -3.0, ZP + 2 * CH)
GAME['markers']['Crate_Drop'] = (0.0, -6.0, ZP)
container(-3.2, 10.0, 0.1, PALE, ident='PSCU 310055', tag='cin')
container(3.4, 12.5, 0.1, GRAPH, ident='PSCU 310071', tag='cin')
container(3.4, 12.5, 0.1 + CH, WHITE, ident='PSCU 310072', tag='cin')

# ---- glowing blue Helium-3 canister on its cradle
def he3_canister(cx, cy):
    z0 = ZP
    box('he3_pallet', (3.3, 1.6, 0.18), (cx, cy, z0 + 0.09), GRAPH, bevel=0.02)
    for dx in (-1.0, 1.0): box('he3_saddle', (0.32, 1.3, 0.55), (cx + dx, cy, z0 + 0.18 + 0.275), GRAPH2, bevel=0.03)
    zc = z0 + 0.18 + 0.55 + 0.3
    rod('he3_core', (cx - 1.25, cy, zc), (cx + 1.25, cy, zc), 0.48, HE3, segs=32)
    for k in range(8):
        a = k * TAU / 8 + TAU / 16
        rod('he3_cage', (cx - 1.3, cy + 0.58 * math.cos(a), zc + 0.58 * math.sin(a)), (cx + 1.3, cy + 0.58 * math.cos(a), zc + 0.58 * math.sin(a)), 0.05, GRAPH2, segs=8)
    for dx in (-1.3, -0.45, 0.45, 1.3): rod('he3_ring', (cx + dx - 0.07, cy, zc), (cx + dx + 0.07, cy, zc), 0.64, WHITE_S if abs(dx) > 1 else GRAPH2, segs=32)
    for s in (-1, 1):
        sphere('he3_cap', 0.62, (cx + s * 1.42, cy, zc), WHITE_S, scale=(0.36, 1, 1), sub=3)
        rod('he3_cap_cyan', (cx + s * 1.36, cy, zc), (cx + s * 1.39, cy, zc), 0.635, CYANL, segs=32)
    rod('he3_valve', (cx + 1.62, cy, zc), (cx + 1.85, cy, zc), 0.12, STEELL, segs=12)
    handwheel('he3_wheel', (cx + 1.9, cy, zc), 0.16, axis='x')
    box('he3_gauge', (0.25, 0.08, 0.25), (cx - 1.2, cy - 0.66, zc + 0.35), INKW, bevel=0.02)
    plate('he3_plate', 'HE-3', (cx, cy - 0.8, z0 + 0.42), '-y', 0.9, 0.3, 0.2, sub='CRYO CANISTER  -  FRAGILE')
he3_canister(1.35, -13.4)
# ---- armored platinum crate
def pt_crate(cx, cy):
    z0 = ZP + 0.15; W_, D_, H_ = 1.7, 1.3, 1.15
    for dy in (-0.45, 0.45): box('pt_skid', (W_ + 0.1, 0.22, 0.15), (cx, cy + dy, ZP + 0.075), GRAPH, bevel=0.02)
    box('pt_body', (W_, D_, H_), (cx, cy, z0 + H_ / 2), GRAPH2, bevel=0.05)
    for i in (-1, 1):
        for j in (-1, 1):
            for fy in (-1, 1): box('pt_armor', (W_ / 2 - 0.1, 0.05, H_ / 2 - 0.1), (cx + i * W_ / 4, cy + fy * (D_ / 2 + 0.02), z0 + H_ / 2 + j * H_ / 4), STEEL, bevel=0.02)
            for fx in (-1, 1): box('pt_armor', (0.05, D_ / 2 - 0.1, H_ / 2 - 0.1), (cx + fx * (W_ / 2 + 0.02), cy + i * D_ / 4, z0 + H_ / 2 + j * H_ / 4), STEEL, bevel=0.02)
    box('pt_lid', (W_ + 0.06, D_ + 0.06, 0.1), (cx, cy, z0 + H_ + 0.02), STEEL, bevel=0.02)
    for dx in (-0.5, 0.5): box('pt_strap', (0.12, D_ + 0.1, H_ + 0.14), (cx + dx, cy, z0 + H_ / 2), PT, bevel=0.01)
    for ux in (-1, 1):
        for uy in (-1, 1): box('pt_corner', (0.2, 0.2, H_ + 0.08), (cx + ux * W_ / 2, cy + uy * D_ / 2, z0 + H_ / 2), GRAPH, bevel=0.03)
    box('pt_lock', (0.3, 0.08, 0.3), (cx, cy - D_ / 2 - 0.07, z0 + H_ * 0.6), PT, bevel=0.02)
    lamp('pt_lock_lamp', (cx, cy - D_ / 2 - 0.12, z0 + H_ * 0.6 + 0.08), GREENL, 0.03)
    box('pt_cyan', (W_ - 0.2, 0.03, 0.04), (cx, cy - D_ / 2 - 0.06, z0 + 0.15), CYANL, bevel=0.0)
    stencil('st_pt', 'PT  -  ARMORED', (cx, cy - D_ / 2 - 0.06, z0 + H_ * 0.86), '-y', 0.13, INKW)
pt_crate(-1.4, -12.9)
for k, (dx, h) in enumerate(((-0.4, 0.6), (0.35, 0.6), (0.0, 0.5))):
    box('crate_small', (0.7, 0.9, h), (-0.3 + dx, -9.0, ZP + 0.14 + (0.6 if k == 2 else 0) + h / 2), [PALE, WHITE_S, GRAPH2][k], bevel=0.03)
box('crate_pallet', (1.8, 1.2, 0.14), (-0.3, -9.0, ZP + 0.07), GRAPH, bevel=0.01)
GAME['markers']['Road_Entry'] = (0.0, -17.2, ZP)

# ====================================================================== RADIATOR WING RAD-1 + power line on masts + solar masts
radiator_array('rad1', -14.6, 6.0, 20.0, 2.2, 4.6, 4, axis='y')
plate('rad1_plate', 'RAD-1', (-14.6, 5.85, 1.5), '-y', 0.8, 0.34, 0.19)
for k, zz in enumerate((2.08, 6.92)):
    pipe('rad1_loop', [(-14.6, 20.0 - 0.4 * k, zz), (-13.0, 20.0 - 0.4 * k, zz), (-HW - 0.2, 20.0 - 0.4 * k, zz)], 0.08, STEELL, bend=0.4)
with grp('Tier_20'):
    radiator_array('rad2', 21.4, -15.4, -11.6, 2.2, 4.6, 2, axis='x')
    pipe('rad2_loop', [(-13.2, 21.4, 2.08), (-13.2, 20.0, 2.08)], 0.08, STEELL, bend=0.3)
def power_mast(name, x, y, h=10.0, c='Mine'):
    lathe(name, [(0.34, 0.0), (0.26, 1.0), (0.17, h - 0.4), (0.15, h)], (x, y, 0), GRAPH2, segs=14)
    cyl(name + '_base', 0.75, 0.45, (x, y, 0.22), GRAPH, segs=16, bevel=0.03, c=c)
    beam(name + '_arm', (x, y - 1.6, h - 0.6), (x, y + 1.6, h - 0.6), 0.18, 0.22, STEEL, c=c)
    cyl(name + '_cyan', 0.18, 0.06, (x, y, 3.0), CYANL, segs=14, c=c)
    pts = []
    for dy in (-1.4, 0.0, 1.4):
        cyl(name + '_ins', 0.09, 0.5, (x, y + dy, h - 0.25), FOIL, segs=10, c=c); pts.append((x, y + dy, h))
    return pts
PMX = -17.4   # feeder mast just left of RAD-1 (was -24: kept the dock inside the phone frame)
P1 = power_mast('pmast', PMX, 11.0)
with grp('Beacon_Lights'): sphere('beacon_mast', 0.17, (PMX, 11.0, 10.35), REDL, sub=2)
wall = [(-HW - 0.75, 11.0 + dy, 8.4) for dy in (-0.6, 0.0, 0.6)]
for a, b in zip(P1, wall): cable('pline', a, b, 0.025, RUBBER, sag=0.5, n=20)
box('pline_bushing', (0.5, 1.8, 0.4), (-HW - 0.25, 11.0, 8.4), GRAPH2, bevel=0.03)
for k in range(3): cyl('pline_ins', 0.08, 0.45, (-HW - 0.55, 11.0 + (k - 1) * 0.6, 8.4), FOIL, rot=(0, math.pi / 2, 0), segs=10)
SUN = Vector((-0.55, -0.6, 0.58)); saz = math.atan2(SUN.y, SUN.x)
for k, (mx, my) in enumerate(((-6.5, 34.0), (6.5, 34.0))):
    MH = 15.0
    lathe('solar_mast', [(0.38, 0.0), (0.3, 1.0), (0.2, MH - 0.6), (0.2, MH)], (mx, my, 0), STEELL, segs=16)
    cyl('solar_base', 0.9, 0.5, (mx, my, 0.25), GRAPH, segs=16, bevel=0.03)
    cyl('solar_gimbal', 0.3, 0.6, (mx, my, MH + 0.2), GRAPH2, segs=16)
    rz = saz + math.pi / 2
    lbox('solar_panel', (6.4, 0.1, 9.0), (mx, my, MH - 4.4), (0, 0, rz), CELLS, bevel=0.0)
    lbox('solar_back', (6.3, 0.05, 8.9), (mx - 0.08 * math.sin(rz), my + 0.08 * math.cos(rz), MH - 4.4), (0, 0, rz), GRAPH2)
    lbox('solar_frame_v', (0.14, 0.18, 9.1), (mx, my, MH - 4.4), (0, 0, rz), STEEL)
    for zz in (MH - 8.9, MH + 0.05): lbox('solar_frame_h', (6.5, 0.16, 0.12), (mx, my, zz), (0, 0, rz), STEEL)
    pipe('solar_cable', [(mx, my, 1.0), (mx, my, 0.5), (mx * 0.62, my - 3.2, 0.4)], 0.05, RUBBER, bend=0.4, flanges=False)
    box('solar_combiner', (0.7, 0.5, 0.9), (mx * 0.62, my - 3.4, 0.45), PALE, bevel=0.03)

# ====================================================================== TANK FARM TF-1 (beside the dock, behind a low L-berm)
TR, TZ0, TZ1, TD = 2.4, 1.9, 10.0, 0.45
TOPZ = TZ1 + TR * TD
def cryo_tank(tag, x, y, label, sub, band=GRAPH, R=None, Z1=None, lz=None, Z0=None, belt=None):
    R = TR if R is None else R; Z1 = TZ1 if Z1 is None else Z1; TZ0 = globals()['TZ0'] if Z0 is None else Z0
    TOP = Z1 + R * TD
    cyl(tag + '_plinth', R + 0.3, 0.4, (x, y, 0.2), GRAPH, segs=40, bevel=0.03)
    cyl(tag + '_skirt', R * 0.86, TZ0 - 0.4, (x, y, 0.4 + (TZ0 - 0.4) / 2), GRAPH2, segs=40 if R < 3 else 48)
    box(tag + '_skirt_door', (0.8, 0.12, 1.0), (x, y - R * 0.86 - 0.02, 0.95), PALE, bevel=0.02)
    if R < 3:
        vvessel(tag, (x, y), R, TZ0, Z1, WHITE, bottom='dish', dome=TD, segs=40, bands=(TZ0 + 0.9, (TZ0 + Z1) / 2 + 0.6, Z1 - 0.5), band_mat=band)
    else:   # big LCH4 tank: thick stiffener bands + a wide MLI insulation belt (graphite, cyan pinstripes)
        vvessel(tag, (x, y), R, TZ0, Z1, WHITE, bottom='dish', dome=TD, segs=48, bands=(), band_mat=band)
        for zb in (TZ0 + 0.9, Z1 - 0.6):
            cyl(tag + '_band', R * 1.035, 0.34, (x, y, zb), band, segs=48, bevel=0.03)
        cyl(tag + '_cyan', R * 1.016, 0.05, (x, y, Z1 - 0.6 + 0.26), CYANL, segs=48)
        bz, bh = belt
        cyl(tag + '_belt', R * 1.045, bh, (x, y, bz), band, segs=48, bevel=0.04)
        for dz in (-bh / 2 - 0.06, bh / 2 + 0.06): cyl(tag + '_belt_cyan', R * 1.016, 0.05, (x, y, bz + dz), CYANL, segs=48)
    for k in range(16):
        a = k * TAU / 16; cyl(tag + '_bolt', 0.05, 0.1, (x + (R + 0.18) * math.cos(a), y + (R + 0.18) * math.sin(a), 0.44), STEEL, segs=6)
    tank_label(tag, label, sub, x, y, R, (TZ0 + Z1) / 2 + 2.2 if lz is None else lz, size=0.78 if R < 3 else 1.0)
    ladder(tag + '_ladder', x - R - 0.3, y, 0.4, Z1 + 0.6, along='y')
    for z in range(3, int(Z1) + 1):
        curve_tube(tag + '_cage', [(x - R - 0.3 + 0.42 * math.cos(a), y + 0.42 * math.sin(a), z) for a in [math.pi / 2 + i / 10 * math.pi for i in range(11)]], 0.018, STEELL)
    rod(tag + '_nozzle', (x, y - R + 0.2, TZ0 + 0.5), (x, y - R - 0.55, TZ0 + 0.5), 0.2, STEELL, segs=16)
    rod(tag + '_nozzle_fl', (x, y - R - 0.5, TZ0 + 0.5), (x, y - R - 0.62, TZ0 + 0.5), 0.3, STEEL, segs=16)
    GX = R + (0.12 if R < 3 else 0.3)
    rod(tag + '_gauge', (x + GX, y - 0.4, TZ0 + 0.4), (x + GX, y - 0.4, Z1 - 0.2), 0.06, STEELL, segs=8)
    box(tag + '_gauge_cyan', (0.04, 0.04, (Z1 - TZ0) * 0.55), (x + GX + 0.07, y - 0.4, TZ0 + 0.5 + (Z1 - TZ0) * 0.275), CYANL, bevel=0.0)
    for dx in (-0.6, 0.6):
        cyl(tag + '_relief', 0.12, 0.6, (x + dx, y + 0.5, TOP - 0.05), STEELL, segs=12)
        cyl(tag + '_relief_cap', 0.16, 0.1, (x + dx, y + 0.5, TOP + 0.25), GRAPH, segs=12)
    rod(tag + '_vent', (x + 0.4, y - 0.9, TOP - 0.3), (x + 0.4, y - 0.9, TOP + 1.6), 0.09, STEELL, segs=10)
    lamp(tag + '_lamp', (x - 0.8, y - 0.6, TOP - 0.12), AMBERL, 0.08)
HDR = {'LOX': (3.0, 1.15, 0.24), 'LCH4': (3.7, 1.15, 0.26), 'HE3': (4.4, 1.3, 0.16)}   # header (y, z, r)
ROWA_Y, ROWB_Y = 8.0, 15.6
# Fuel is methalox: LOX + liquid methane (LCH4, ~112 K). LOX tanks r 2.4 / shell 1.9-10.0 m (pi*2.4^2*(8.1+0.6*2.4) ~ 173 m3).
# The big LCH4 tanks keep the earlier 'bigger tank' pass: r 3.6 (1.5x LOX) on a taller skirt / shell 4.0-14.6 m (~520 m3 each).
# (A methalox load needs only ~0.8x the LOX volume of LCH4; the extra is buffer storage and keeps the methane row readable.)
# They stand in row B behind the gaps of the shorter row A (LOX-1, LOX-2, HE3-1), so every tank (and every tier) reads on the phone.
LCH4R, LCH4Z0, LCH4Z1 = 3.6, 4.0, 14.6
LCH4BELT = (8.4, 1.3)   # wide insulation belt (centre z, height)
TANKS = {'LOX-1': (16.6, ROWA_Y), 'LOX-2': (23.0, ROWA_Y), 'HE3-1': (19.8, -0.3), 'LCH4-1': (19.4, ROWB_Y), 'LCH4-2': (27.8, ROWB_Y)}
GAPX = {'LCH4-1': 19.8, 'LCH4-2': 26.25}   # where the LCH4 drop lines pass between the row-A tanks
cryo_tank('lox1', *TANKS['LOX-1'], 'LOX-1', 'LIQUID OXYGEN  90 K', lz=8.7)
cryo_tank('lch41', *TANKS['LCH4-1'], 'LCH4-1', 'LIQUID METHANE  112 K', R=LCH4R, Z1=LCH4Z1, Z0=LCH4Z0, belt=LCH4BELT, lz=13.0)
with grp('Tier_05'): cryo_tank('lox2', *TANKS['LOX-2'], 'LOX-2', 'LIQUID OXYGEN  90 K', lz=8.7)
with grp('Tier_20'): cryo_tank('lch42', *TANKS['LCH4-2'], 'LCH4-2', 'LIQUID METHANE  112 K', R=LCH4R, Z1=LCH4Z1, Z0=LCH4Z0, belt=LCH4BELT, lz=13.0)
with grp('Tier_12'):   # He-3 cryo sphere (cyan = He-3)
    hx, hy = TANKS['HE3-1']; HR = 3.1; HZ = 4.6
    sphere('he3t', HR, (hx, hy, HZ), WHITE_S, sub=5)
    cyl('he3t_band', HR * 1.01, 0.3, (hx, hy, HZ), GRAPH, segs=56, bevel=0.01)
    for dz in (-0.9, 0.9): cyl('he3t_cyan', math.sqrt(HR * HR - dz * dz) * 1.006, 0.06, (hx, hy, HZ + dz), CYANL, segs=56)
    for j in range(6):
        a = j * TAU / 6 + 0.3; lx, ly = hx + HR * 0.97 * math.cos(a), hy + HR * 0.97 * math.sin(a)
        box('he3t_leg', (0.24, 0.24, HZ), (lx, ly, HZ / 2), STEEL, bevel=0.02)
        box('he3t_pad', (0.6, 0.6, 0.14), (lx, ly, 0.07), GRAPH, bevel=0.02)
        beam('he3t_brace', (lx, ly, 0.3), (hx + HR * 0.97 * math.cos(a + TAU / 6), hy + HR * 0.97 * math.sin(a + TAU / 6), HZ - 0.9), 0.08, 0.08, STEEL)
    cyl('he3t_nozzle', 0.2, 0.7, (hx, hy, HZ + HR + 0.2), STEELL, segs=14)
    cyl('he3t_valve', 0.26, 0.2, (hx, hy, HZ + HR + 0.6), GRAPH2, segs=14)
    t = to_mesh(stencil('st_he3t', 'HE3-1', (hx, hy - HR - 0.02, HZ + 0.52), '-y', 0.5, INK, ex=0.008)); wrap_cyl(t, hx, hy, math.sqrt(HR * HR - 0.52 ** 2) + 0.02)   # between the equator band and the upper cyan ring
    pipe('he3t_line', [(hx, hy, HZ + HR + 0.7), (hx, hy, HZ + HR + 1.2), (hx + 1.2, hy + 1.2, HZ + HR + 1.2), (hx + 1.2, HDR['HE3'][0], HZ + HR + 1.2), (hx + 1.2, HDR['HE3'][0], HDR['HE3'][1])], 0.13, WHITE_S, bend=0.6)
# catwalk across the row-A tank tops + stair tower
CWZ = TOPZ + 0.45; SX0 = 12.6; CWX1 = TANKS['LOX-2'][0] + 1.0
box('cw_deck', (CWX1 - SX0, 1.1, 0.1), ((SX0 + CWX1) / 2, ROWA_Y, CWZ), GRAPH2, bevel=0.01)
for sy in (-1, 1):
    ibeam('cw_stringer', (SX0, ROWA_Y + sy * 0.5, CWZ - 0.25), (CWX1, ROWA_Y + sy * 0.5, CWZ - 0.25), 0.18, 0.36, STEEL)
    rail('cw_rail', [(SX0 + 1.2, ROWA_Y + sy * 0.55, CWZ + 0.05), (CWX1, ROWA_Y + sy * 0.55, CWZ + 0.05)], TRIM, post=2.0)
box('cw_cyan', (CWX1 - SX0 - 0.5, 0.04, 0.05), ((SX0 + CWX1) / 2, ROWA_Y - 0.57, CWZ - 0.05), CYANL, bevel=0.0)
def cw_posts(x, y):
    for dx in (-0.7, 0.7): box('cw_post', (0.16, 0.9, CWZ - 0.4 - (TOPZ - 0.6)), (x + dx, y, (TOPZ - 0.6 + CWZ - 0.4) / 2), STEEL, bevel=0.01)
cw_posts(*TANKS['LOX-1'])
with grp('Tier_05'): cw_posts(*TANKS['LOX-2'])
TWX, TWY = SX0, ROWA_Y
for ux in (-1, 1):
    for uy in (-1, 1): box('stw_post', (0.18, 0.18, CWZ + 1.1), (TWX + ux * 1.1, TWY + uy * 1.1, (CWZ + 1.1) / 2), STEEL, bevel=0.01)
for k in range(4):
    za, zb = k * CWZ / 4, (k + 1) * CWZ / 4
    if k < 3: box('stw_landing', (2.4, 2.4, 0.08), (TWX, TWY, zb), GRAPH2, bevel=0.01)
    off = -0.55 if k % 2 == 0 else 0.55
    ya, yb = (TWY - 1.0, TWY + 1.0) if k % 2 == 0 else (TWY + 1.0, TWY - 1.0)
    for s in (-0.5, 0.5): beam('stw_stringer', (TWX + off + s * 0.9, ya, za), (TWX + off + s * 0.9, yb, zb), 0.06, 0.22, STEEL)
    for j in range(1, 12):
        q = Vector((TWX + off, ya, za)).lerp(Vector((TWX + off, yb, zb)), j / 12); box('stw_tread', (0.9, 0.2, 0.04), tuple(q), GRAPH2, bevel=0.0)
    rod('stw_handrail', (TWX + off + 0.48, ya, za + 1.0), (TWX + off + 0.48, yb, zb + 1.0), 0.03, TRIM, segs=8)
for z in (CWZ / 4, CWZ / 2, 3 * CWZ / 4, CWZ):
    for (a, b) in (((-1, -1), (1, -1)), ((-1, 1), (1, 1)), ((-1, -1), (-1, 1))):
        rod('stw_rail', (TWX + a[0] * 1.1, TWY + a[1] * 1.1, z + 1.0), (TWX + b[0] * 1.1, TWY + b[1] * 1.1, z + 1.0), 0.025, TRIM, segs=8)
box('stw_top', (2.4, 2.4, 0.08), (TWX, TWY, CWZ), GRAPH2, bevel=0.01)
box('stw_cyan', (2.4, 0.04, 0.05), (TWX, TWY - 1.22, CWZ - 0.05), CYANL, bevel=0.0)
plate('tf_plate', 'TF-1  TANK FARM', (TWX, TWY - 1.25, 2.2), '-y', 1.9, 0.42, 0.2, sub='CRYOGENIC  -  NO OPEN FLAME')
# insulated headers, tie-ins with valves, pump skid, line out TO LAUNCH PAD
HDR = {'LOX': (3.0, 1.15, 0.24), 'LCH4': (3.7, 1.15, 0.26), 'HE3': (4.4, 1.3, 0.16)}
HX0, HX1 = 15.0, 35.0
VLX, VLY = HX1 + 2.7, -7.3   # buried-line vault where the launch-pad line goes underground
for nm, (hy_, hz_, hr_) in HDR.items():
    xe = HX1 + 2.0 + (hy_ - 3.0)
    pipe('hdr_' + nm.lower(), [(HX0, hy_, hz_), (xe, hy_, hz_), (xe, -6.7, hz_), (xe, -6.7, 0.55)], hr_, WHITE_S, bend=1.0)
    for k in range(int((HX1 - HX0) / 1.8)):
        x = HX0 + 0.9 + k * 1.8; rod('hdr_band', (x - 0.1, hy_, hz_), (x + 0.1, hy_, hz_), hr_ * 1.07, GRAPH if nm != 'HE3' else CYANL, segs=16)
for x in range(16, int(HX1) + 1, 3):
    box('hdr_sleeper', (0.3, 2.2, 0.9), (x, 3.7, 0.45), GRAPH, bevel=0.02)
    beam('hdr_sleeper_cap', (x, 2.6, 0.92), (x, 4.8, 0.92), 0.36, 0.08, STEEL)
for y in (-1.0, -4.0): box('hdr_sleeper', (2.6, 0.3, 1.2), (VLX, y, 0.3), GRAPH, bevel=0.02)
box('bpl_vault', (3.6, 2.2, 0.6), (VLX, VLY, 0.3), GRAPH2, bevel=0.05)
box('bpl_vault_lid', (3.2, 1.8, 0.08), (VLX, VLY, 0.62), STEEL, bevel=0.02)
box('bpl_vault_cyan', (3.62, 0.03, 0.05), (VLX, VLY - 1.11, 0.45), CYANL, bevel=0.0)
def tie(nm):
    x, y = TANKS[nm]; hy_, hz_, hr_ = HDR['LOX' if nm.startswith('LOX') else 'LCH4']; tag = nm.lower().replace('-', '')
    if nm.startswith('LCH4'):   # row B: out of the nozzle, sideways to the row-A gap, then forward between the front tanks
        gx = GAPX[nm]; ys = y - LCH4R - 0.62; yv = ROWA_Y - TR - 1.2
        nz = LCH4Z0 + 0.5
        pipe(tag + '_drop', [(x, ys, nz), (x, ys - 0.5, nz), (gx, ys - 0.5, nz), (gx, yv, nz), (gx, yv, hz_ + 0.7), (gx, hy_, hz_ + 0.7), (gx, hy_, hz_)], 0.17, FOIL, bend=0.35)
        valve(tag + '_v', (gx, (yv + ys - 0.5) / 2, nz), axis='y', r=0.2); return
    pipe(tag + '_drop', [(x, y - TR - 0.62, TZ0 + 0.5), (x, y - TR - 1.2, TZ0 + 0.5), (x, y - TR - 1.2, hz_ + 0.7), (x, hy_, hz_ + 0.7), (x, hy_, hz_)], 0.17, FOIL, bend=0.35)
    valve(tag + '_v', (x, y - TR - 1.2, 1.55), axis='y', r=0.2)
tie('LOX-1'); tie('LCH4-1')
with grp('Tier_05'): tie('LOX-2')
with grp('Tier_20'): tie('LCH4-2')
for i, x in enumerate((21.4, 32.8, 34.6)):
    for nm, (hy_, hz_, hr_) in HDR.items():
        if nm == 'HE3' and i < 2: continue
        valve(f'hdr_v_{nm}_{i}', (x, hy_, hz_), axis='x', r=hr_ * 0.85, wheel=(i != 2), actuator=(i == 2))
PSX, PSY = 28.2, -0.4
box('ps_skid', (7.4, 2.6, 0.26), (PSX, PSY, 0.13), GRAPH, bevel=0.03)
box('ps_cyan', (7.42, 0.03, 0.05), (PSX, PSY - 1.31, 0.2), CYANL, bevel=0.0)
for k, px in enumerate((PSX - 2.2, PSX + 0.4)):
    vvessel(f'ps_pump{k}', (px, PSY + 0.2), 0.5, 0.45, 1.9, WHITE_S, dome=0.4, segs=28, bands=(0.8, 1.6), band_mat=GRAPH2)
    rod(f'ps_motor{k}', (px + 0.6, PSY + 0.2, 0.95), (px + 1.8, PSY + 0.2, 0.95), 0.38, GRAPH2, segs=24)
    for j in range(7): rod(f'ps_fin{k}', (px + 0.75 + j * 0.15, PSY + 0.2, 0.95), (px + 0.79 + j * 0.15, PSY + 0.2, 0.95), 0.44, STEEL, segs=24, bevel=0.0)
    box(f'ps_mount{k}', (1.5, 0.9, 0.18), (px + 1.2, PSY + 0.2, 0.35), GRAPH2, bevel=0.02)
    box(f'ps_mount{k}', (0.9, 0.5, 0.36), (px + 1.2, PSY + 0.2, 0.55), GRAPH2, bevel=0.02)
    pipe(f'ps_suction{k}', [(px, PSY + 0.2, 2.15), (px, PSY + 0.2, 2.5), (px, HDR['LOX'][0], 2.5), (px, HDR['LOX'][0], HDR['LOX'][1] + 0.3)], 0.12, FOIL, bend=0.3)
    plate(f'ps_tag{k}', f'P-{k + 1}', (px, PSY - 0.33, 1.3), '-y', 0.42, 0.24, 0.13)
box('ps_cab', (1.1, 0.8, 2.0), (PSX + 2.9, PSY + 0.4, 1.26), PALE, bevel=0.04)
for j, m_ in enumerate((GREENL, GREENL, AMBERL)): lamp(f'ps_lamp{j}', (PSX + 2.6 + j * 0.3, PSY - 0.03, 2.05), m_, 0.04)
box('ps_screen', (0.6, 0.03, 0.4), (PSX + 2.9, PSY - 0.01, 1.5), CYANS, bevel=0.0)
plate('ps_plate', 'PS-1', (PSX - 1.0, PSY - 1.0, 0.8), '-y', 1.2, 0.36, 0.16, sub='CRYO TRANSFER PUMPS')
for x in (PSX - 1.6, PSX - 0.4): box('ps_plate_post', (0.06, 0.06, 0.62), (x, PSY - 0.98, 0.31), STEEL)
plate('tlp_plate', 'TO LAUNCH PAD', (VLX, VLY - 1.6, 1.5), '-y', 2.2, 0.4, 0.22, bg=GRAPH, fg=INKW, sub='BURIED LINE  LOX / LCH4 / HE-3')
for x in (VLX - 0.8, VLX + 0.8): box('tlp_post', (0.08, 0.08, 1.4), (x, VLY - 1.55, 0.7), STEEL)
GAME['markers']['Pipe_LaunchPad'] = (VLX, VLY, 0.66)   # top of the buried-line vault: the launch-pad line goes underground here
# fuel arrives from the Refinery (to the left) by buried pipeline: it surfaces in a riser vault between the hall and the tank farm
RVX, RVY = 14.5, 12.6
box('rfl_vault', (2.4, 1.6, 0.6), (RVX, RVY, 0.3), GRAPH2, bevel=0.04)
box('rfl_vault_cyan', (2.42, 0.03, 0.05), (RVX, RVY - 0.81, 0.45), CYANL, bevel=0.0)
pipe('rfl_lox', [(14.0, 12.3, 0.6), (14.0, 12.3, 1.4), (14.0, 11.1, 1.4), (16.6, 11.1, 1.4), (16.6, 10.2, 1.4)], 0.15, FOIL, bend=0.3)
pipe('rfl_lch4', [(15.1, 12.9, 0.6), (15.1, 12.9, 2.2), (15.1, 15.6, 2.2), (16.2, 15.6, 2.2)], 0.17, FOIL, bend=0.3)
valve('rfl_v_lox', (14.0, 11.7, 1.4), axis='y', r=0.15)
plate('rfl_plate', 'FROM REFINERY', (RVX, RVY - 0.82, 1.05), '-y', 1.5, 0.34, 0.15, sub='BURIED LINE  LOX / LCH4')
for x in (RVX - 0.6, RVX + 0.6): box('rfl_post', (0.06, 0.06, 0.9), (x, RVY - 0.8, 0.7), STEEL)
GAME['markers']['Pipe_Refinery'] = (RVX, RVY, 0.6)

# ====================================================================== STAGE: shared ground (M_ground), berm, road, far lines
height = build_stage(keep_flat=((10, 6, 46), (30, 8, 26)))
gm = bpy.data.materials['M_Regolith']
for ob in list(coll('Stage').objects):
    if ob.type == 'MESH' and ob.name.split('.')[0] in ('boulder', 'pebble'):
        c_ = ob.location if ob.location.length > 0 else sum((v.co for v in ob.data.vertices), Vector()) / len(ob.data.vertices)
        if (-27 < c_.x < 52 and -20 < c_.y < 40) or (-6 < c_.x < 6 and c_.y < -16): bpy.data.objects.remove(ob)
def g01(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def seg_d(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared)); return (a + ab * t - p).length
BERM = [Vector((12.6, 2.6)), Vector((12.6, -5.6)), Vector((33.4, -5.6))]
BH_, BC, BRN = 1.5, 0.35, 1.15
def berm_z(x, y):
    p = Vector((x, y)); d = min(seg_d(p, a, b) for a, b in zip(BERM, BERM[1:]))
    z = BH_ * g01(1 - max(d - BC, 0) / BRN)
    if z > 0: z += (0.16 * noise.noise(Vector((x * 0.3, y * 0.3, 3.3))) + 0.05 * noise.noise(Vector((x * 1.3, y * 1.3, 9.1)))) * min(1, z)
    return max(z, 0.0)
bm = bmesh.new(); st = 0.35; vv = {}
xs = [10.5 + i * st for i in range(int((45.5 - 10.5) / st) + 1)]; ys = [-7.0 + j * st for j in range(int((29.0 + 7.0) / st) + 1)]
Z = {(i, j): berm_z(x, y) for i, x in enumerate(xs) for j, y in enumerate(ys)}
for i in range(len(xs) - 1):
    for j in range(len(ys) - 1):
        q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        if all(Z[k] <= 0.0 for k in q): continue
        vs = []
        for k in q:
            if k not in vv: vv[k] = bm.verts.new((xs[k[0]], ys[k[1]], height(xs[k[0]], ys[k[1]]) + Z[k] - (0.05 if Z[k] <= 0 else 0.0)))
            vs.append(vv[k])
        bm.faces.new(vs)
for f in bm.faces:
    if f.normal.z < 0: f.normal_flip()
_obj(bm, 'tf_berm', gm, c='Mine', smooth=True, angle=180)
# the headers cross the berm: a graphite culvert box where the pipes pass
pass   # (no culvert: the launch-pad line now goes underground before the berm end)
# graded access road from the south into the yard (Stage) with cyan reflector posts
bm = bmesh.new(); rows = []
for k in range(41):
    y = -16.9 - k * 1.5
    rows.append([bm.verts.new((x, y, height(x, y) + 0.04)) for x in (-3.2, -1.6, 0.0, 1.6, 3.2)])
for a, b in zip(rows, rows[1:]):
    for i in range(4): bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
for f in bm.faces:
    if f.normal.z < 0: f.normal_flip()
_obj(bm, 'road', ROADM, c='Stage', smooth=True, angle=180)
for k in range(12):
    y = -19.0 - k * 4.5
    for sx in (-1, 1):
        gz_ = height(sx * 3.6, y)
        box('road_post', (0.14, 0.14, 0.9), (sx * 3.6, y, gz_ + 0.45), GRAPH, c='Stage', bevel=0.01)
        box('road_post_cyan', (0.15, 0.15, 0.12), (sx * 3.6, y, gz_ + 0.78), CYANL, c='Stage', bevel=0.0)
prev = P1
for k, (x, y) in enumerate(((-36.0, 9.0), (-48.0, 6.0), (-60.0, 2.5))):
    before = set(bpy.data.objects.keys())
    pts = power_mast(f'pmast_far{k}', x, y)
    for n in set(bpy.data.objects.keys()) - before:
        ob = bpy.data.objects[n]; coll('Mine').objects.unlink(ob); coll('Stage').objects.link(ob)
    gz_ = height(x, y)
    for n in set(bpy.data.objects.keys()) - before: bpy.data.objects[n].location.z += gz_
    pts = [(p[0], p[1], p[2] + gz_) for p in pts]
    sphere('beacon_far', 0.17, (x, y, 10.35 + gz_), REDL, sub=2, c='Stage')
    for a, b in zip(prev, pts): cable('pline_far', a, b, 0.025, RUBBER, sag=0.7, n=20, c='Stage')
    prev = pts
for k in range(14):   # buried launch-pad line: marker posts with cyan caps along its route (Stage only)
    t = k / 13
    p = Vector((VLX, -10.0)).lerp(Vector((VLX + 22.0, -32.0)), t * 2) if t < 0.5 else Vector((VLX + 22.0, -32.0)).lerp(Vector((VLX + 60.0, -48.0)), (t - 0.5) * 2)
    gz_ = height(p.x, p.y)
    box('bpl_post', (0.16, 0.16, 1.0), (p.x, p.y, gz_ + 0.5), GRAPH, c='Stage', bevel=0.01)
    box('bpl_post_cyan', (0.17, 0.17, 0.12), (p.x, p.y, gz_ + 0.9), CYANL, c='Stage', bevel=0.0)

# ====================================================================== Tier_08: pedestal jib crane JC-2 at the front-left of the yard
with grp('Tier_08'):
    JX, JY = -11.6, 1.7
    cyl('jib_base', 1.3, 0.5, (JX, JY, ZP + 0.25), GRAPH, segs=28, bevel=0.03)
    lathe('jib_pedestal', [(0.85, 0.0), (0.75, 1.0), (0.62, 7.0)], (JX, JY, ZP + 0.5), WHITE, segs=28)
    cyl('jib_cyan', 0.78, 0.06, (JX, JY, ZP + 1.6), CYANL, segs=28)
    cyl('jib_slew', 1.0, 0.6, (JX, JY, ZP + 7.8), GRAPH2, segs=28, bevel=0.03)
    box('jib_house', (2.0, 2.0, 1.6), (JX + 0.2, JY - 0.2, ZP + 8.9), WHITE_S, bevel=0.08)
    box('jib_house_cyan', (2.02, 0.04, 0.06), (JX + 0.2, JY - 1.21, ZP + 8.5), CYANL, bevel=0.0)
    box('jib_counter', (1.4, 1.4, 1.2), (JX - 0.9, JY + 1.4, ZP + 8.6), GRAPH2, bevel=0.05)
    B0 = Vector((JX + 0.5, JY - 0.6, ZP + 8.6)); B1 = Vector((-6.1, -1.4, 12.8))
    beam('jib_boom', B0, B1, 0.6, 0.7, WHITE, bevel=0.04)
    beam('jib_boom_cyan', B0 + Vector((0, -0.33, -0.2)), B1 + Vector((0, -0.33, -0.2)), 0.04, 0.05, CYANL, bevel=0.0)
    rod('jib_ram', (JX + 0.4, JY - 0.5, ZP + 6.2), tuple(B0.lerp(B1, 0.35) - Vector((0, 0, 0.35))), 0.16, STEELL, segs=12)
    rod('jib_rope', tuple(B1 - Vector((0, 0, 0.3))), (B1.x, B1.y, 8.2), 0.03, STEEL, segs=6)
    box('jib_hook', (0.5, 0.4, 0.7), (B1.x, B1.y, 7.9), GRAPH2, bevel=0.05)
    cyl('jib_sheave', 0.3, 0.2, tuple(B1), STEEL, rot=(0, math.pi / 2, 0), segs=16)
    plate('jib_plate', 'JC-2  12 t', (JX + 0.6, JY - 0.6, ZP + 3.4), '-y', 0.9, 0.3, 0.18)
with grp('Tier_20'):
    stack(-10.4, -2.4, (0, 1), 31); stack(-10.4, -9.0, (0,), 32)

# ====================================================================== lights, sun, review astronauts (Stage), markers
ld = bpy.data.lights.new('HallLight', 'AREA'); ld.energy = 2600; ld.size = 14.0; ld.color = hexc('#e8f4ff')[:3]
lo = bpy.data.objects.new('HallLight', ld); coll('Stage').objects.link(lo); lo.location = (0, 12.0, 10.0)
ld = bpy.data.lights.new('PorchLight', 'AREA'); ld.energy = 160; ld.size = 2.0; ld.color = hexc('#e8f4ff')[:3]
lo = bpy.data.objects.new('PorchLight', ld); coll('Stage').objects.link(lo); lo.location = (AX, -1.0, MZ + 2.3)
world_and_sun(tuple(SUN), 5.5)
# soft fill over the hall's cast shadow between the dock and the tank farm (the old hero read it as a hard black wedge / hole)
ld = bpy.data.lights.new('GapFill', 'AREA'); ld.energy = float(A.get('fill', 2200)); ld.size = 18.0; ld.color = hexc('#dfe8f5')[:3]
ld.use_shadow = False
lo = bpy.data.objects.new('GapFill', ld); coll('Stage').objects.link(lo); lo.location = (16.0, 2.0, 16.0)
astronaut((2.9, -14.75, ZP), rot_z=0.4)
astronaut((AX - 0.3, -2.2, MZ), rot_z=-0.2)
astronaut((22.2, ROWA_Y, CWZ + 0.05), rot_z=-1.4)
for nm, p in (('Crew_Path_01', (AX, HYH - 0.6, MZ)), ('Crew_Path_02', (AX, -1.6, MZ)), ('Crew_Path_03', (AX, -3.7, ZP)),
              ('Crew_Path_04', (AX - 0.6, -6.0, ZP)), ('Crew_Path_05', (5.6, -14.3, ZP)), ('Crew_Path_06', (2.3, -11.9, ZP)),
              ('Crew_Path_07', (0.0, -6.0, ZP)), ('Crew_Path_08', (0.0, FY0 - 1.4, ZP))):
    GAME['markers'][nm] = p
# station camera look-at: the phone shots and the game camera aim here (empty, no geometry / no draws).
# 4 m in front of the origin at the game's lookY 2.5 so the focus sits between the HUD (y~100) and the sheet (y~650) on 393x852.
CAM_TARGET = tuple(float(v) for v in A.get('ct', '12.0,-2.0,6.0').split(','))
GAME['markers']['Cam_Target'] = CAM_TARGET
_ct = bpy.data.objects.new('Cam_Target', None); _ct.empty_display_type = 'SPHERE'; _ct.empty_display_size = 0.5
_ct.location = CAM_TARGET; coll('Mine').objects.link(_ct)
FRAME_W = float(A.get('fw', 64.0))      # metres of station that span the screen width at Cam_Target (game camera spec)
_ct['frame_w'] = FRAME_W; GAME['marker_extras'] = {'Cam_Target': {'frame_w': FRAME_W}}
bpy.context.scene['game_nodes'] = json.dumps(GAME)
print('HEIGHTS', [round(height(x, y), 3) for x, y in ((0, -16), (21.5, 7.5), (47, -8), (-24, 11), (0, 20), (31.5, 15.5))], flush=True)

DOOR_OPEN = float(A.get('door', 0.5))
convert_curves()
rig.scale = (1, 1, max(0.06, 1 - DOOR_OPEN))
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

ONLY = A.get('only', 'hero')
if A.get('notile') == '1': bpy.context.scene.cycles.use_auto_tile = False   # one full-frame tile (faster on CPU when RAM allows)
if 'glb' in ONLY:
    root = bpy.data.objects.new('DockTankFarm', None); coll('Mine').objects.link(root)
    for ob in mine:
        if ob.parent is None: ob.parent = root
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for ob in coll('Mine').all_objects: ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{NAME}_master_raw.glb'), export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_extras=True,
                              export_animations=False, export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False)
    for ob in mine:
        if ob.parent == root:
            mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = mw
    bpy.data.objects.remove(root); bpy.context.view_layer.update()
if 'blend' in ONLY:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'{NAME}_master.blend'), compress=True)
if 'turn' in ONLY:
    os.makedirs(os.path.join(OUT, 'turntable'), exist_ok=True)
    tt = [float(v) for v in A.get('tt', '12,6,4').split(',')]
    turntable(cam, os.path.join(OUT, 'turntable'), tuple(tt), float(A.get('td', 100)), 24, size=1000 if not QUICK else 400,
              samples=int(A.get('ts', 40)) if not QUICK else 12, lens=50)
if 'hero' in ONLY:
    w, h = (3840, 2160) if not QUICK else (960, 540)
    if A.get('res'): w, h = [int(v) for v in A['res'].split('x')]
    hp = [float(v) for v in A.get('hc', '-7,-47,17,12.5,5,5.5').split(',')]
    shoot(cam, os.path.join(OUT, 'hero.png'), tuple(hp[3:6]), tuple(hp[:3]), w, h, lens=float(A.get('lens', 28)), samples=int(A.get('hs', 48)) if not QUICK else 16)
def phone_cam(w, h):
    # in-game station camera spec: perspective, vertical fov 38, 18 deg down, aimed at Cam_Target;
    # distance so exactly Cam_Target['frame_w'] metres span the screen width at Cam_Target
    sc = bpy.context.scene
    asp = w / h; vt = math.tan(math.radians(19))
    d = float(bpy.data.objects['Cam_Target']['frame_w']) / (2.0 * vt * asp); e = math.radians(18)
    tgt = bpy.data.objects['Cam_Target'].matrix_world.translation.copy(); pos = tgt + Vector((0.0, -d * math.cos(e), d * math.sin(e)))
    cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(38); cam.data.dof.use_dof = False
    cam.location = pos; cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = w, h; sc.render.resolution_percentage = 100
    bpy.context.view_layer.update()
    return d
def proj_report(w, h):
    """screen-space (px, y down) bounding box of each game group under the phone camera (all tiers visible)."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get(); B = {}
    for ob in mine:
        if ob.type != 'MESH': continue
        g = ob.get('grp', 'Base'); e = ob.evaluated_get(dg); me = e.to_mesh()
        gs = [g] + (['TankRow'] if ob.name.startswith(('lox1', 'lox2', 'lch41', 'lch42', 'he3t')) else []) + (['Hall'] if ob.name.startswith(('hall', 'csd')) else [])
        vs_ = list(me.vertices)
        for v in vs_[::max(1, len(vs_) // 400)]:
            q = world_to_camera_view(sc, cam, e.matrix_world @ v.co); px, py = q.x * w, (1 - q.y) * h
            for g_ in gs:
                b = B.setdefault(g_, [1e9, 1e9, -1e9, -1e9]); b[0] = min(b[0], px); b[1] = min(b[1], py); b[2] = max(b[2], px); b[3] = max(b[3], py)
        e.to_mesh_clear()
    for g, b in sorted(B.items()): print('PROJ', g, 'x %.0f..%.0f  y %.0f..%.0f' % (b[0], b[2], b[1], b[3]), 'of', w, 'x', h, flush=True)
if 'proj' in ONLY:
    convert_curves()
    def _bb(o):
        cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
        return [min(c[i] for c in cs) for i in range(3)], [max(c[i] for c in cs) for i in range(3)]
    if A.get('overlap'):
        tags = A['overlap'].split(',')
        obs = [o for o in mine if o.type == 'MESH']
        for t in tags:
            for o in obs:
                if not o.name.startswith(t): continue
                lo, hi = _bb(o)
                for o2 in obs:
                    if o2.name.startswith(t): continue
                    lo2, hi2 = _bb(o2)
                    ov = [min(hi[i], hi2[i]) - max(lo[i], lo2[i]) for i in range(3)]
                    if min(ov) > 0.02: print('OVERLAP', o.name, o2.name, [round(v, 2) for v in ov], flush=True)
    CFG = [None] if not A.get('ctlist') else [tuple(float(v) for v in c.split(',')) for c in A['ctlist'].split(';')]
    for cfg in CFG:
        if cfg:
            bpy.data.objects['Cam_Target'].location = cfg[:3]; bpy.data.objects['Cam_Target']['frame_w'] = cfg[3]; bpy.context.view_layer.update(); print('CFG', cfg, flush=True)
        for (w, h) in ((393, 852),):
            d = phone_cam(w, h); print('PHONE dist', round(d, 3), 'frame_w', bpy.data.objects['Cam_Target']['frame_w'], 'cam', tuple(round(v, 2) for v in cam.location), flush=True); proj_report(w, h)
if 'phone' in ONLY:
    sc = bpy.context.scene
    w, h = (1179, 2556) if not QUICK else (393, 852)
    if A.get('pres'): w, h = [int(v) for v in A['pres'].split('x')]
    d = phone_cam(w, h)
    sc.cycles.samples = int(A.get('ps', 64)) if not QUICK else 16
    sc.render.filepath = os.path.join(OUT, f'phone_{w}x{h}.png'); print('PHONE dist', round(d, 3), 'frame_w', FRAME_W, 'width at target', round(2 * d * math.tan(math.radians(19)) * w / h, 3), flush=True)
    proj_report(w, h)
    bpy.ops.render.render(write_still=True)
    cam.data.sensor_fit = 'AUTO'
