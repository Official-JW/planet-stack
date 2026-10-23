"""Planet Stack - LIFE SUPPORT building, high-detail concept master (Blender 4.2 LTS, headless, Cycles).

blender -b -P build_life_support.py -- --out .. [--quick 1] [--only glb,blend,turn,hero] [--ks 0,1] [--hs 48] [--ts 32]

Blender coords: Z up, metres, front = -Y (toward the camera). Exported GLB: Y up, front +Z, origin at base centre on the ground.
Reuses the shared Mine-concept helpers (primitives, procedural paint, lunar stage, sun/sky, 1.8 m astronaut) from
art/3d/mine_concepts/_src/mc_common.py by import (not modified).

Systems (each readable from the front 3/4 hero):
  * two above-ground pressurized modules PM-1/PM-2 with thick white shield jackets (no domes, no burial), tunnel, airlock A1 with dust-cleaning porch
  * O2 extraction (left): ilmenite feed bin -> screw conveyor -> feed hopper -> H2-reduction reactor R-1 -> electrolysis
    unit EL-1 -> 2 spherical O2 storage tanks, slag skip, radiator array RAD-1
  * water recovery (right): ice feed hopper -> melt/sublimation vessel -> condenser -> filtration skid -> 3 recycling
    tanks H2O-1..3, radiator array RAD-2
  * CO2 scrubbing (front right): 4 swing beds, blower, 2 vent stacks, CO2 transfer line to the Tank Farm
  * power: switchgear SWG-1 where the reactor feeder lands; cable tray runs to a distant fission reactor behind a berm;
    2 solar arrays on tall masts as backup
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
MC = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'mine_concepts', '_src'))
sys.path.insert(0, MC)
import bpy, bmesh
from mathutils import Vector, Matrix, noise
from mc_common import *
from mc_common import _obj, _nodes

A = argv(); OUT = os.path.abspath(A.get('out', '/tmp/ls_out')); os.makedirs(OUT, exist_ok=True)
QUICK = A.get('quick') == '1'
reset(); rr = random.Random(77)
TAU = math.tau
NAME = 'life_support'

# ====================================================================== materials
def add_dust(m, top=1.3, amt=0.8, col='#8e8982', upamt=0.35):
    """height-based regolith dust (world Z) + dust settling on up-facing surfaces."""
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

# --- Mine-B 'sleek high-tech' palette: glossy white + graphite, satin metal, cyan light strips (weathered)
WHITE  = P_('LS_White', '#eceff2', rough=0.24, metal=0.0, coat=0.8, grime=0.26, grime_col='#a59f97', wear=0.14, wear_col='#9aa3ad', panel=0.8, bevel=0.03, dirt_scale=1.5)
WHITE_S = P_('LS_WhiteSmooth', '#eef1f4', rough=0.2, metal=0.0, coat=0.9, grime=0.2, grime_col='#a59f97', wear=0.1, wear_col='#9aa3ad', bevel=0.03)
PALE   = P_('LS_WhitePanel', '#e2e6eb', rough=0.26, metal=0.0, coat=0.7, grime=0.28, grime_col='#a59f97', wear=0.16, wear_col='#9aa3ad', panel=0.8, bevel=0.02)
GRAPH  = P_('LS_Graphite', '#2c3137', rough=0.3, metal=0.55, coat=0.5, grime=0.2, grime_col='#6b665f', wear=0.22, wear_col='#9aa0a6', panel=1.4, bevel=0.02)
GRAPH2 = P_('LS_Graphite2', '#30353c', rough=0.28, metal=0.6, coat=0.5, grime=0.22, grime_col='#6b665f', wear=0.2, wear_col='#9aa0a6', panel=1.6, bevel=0.02)
STEEL  = P_('LS_Satin', '#9aa3ad', rough=0.28, metal=1.0, grime=0.25, grime_col='#5a5650', wear=0.12, wear_col='#d0d5db', bevel=0.015)
STEELL = P_('LS_SatinLight', '#b9c0c8', rough=0.24, metal=1.0, grime=0.2, grime_col='#5a5650', wear=0.1, wear_col='#e0e4e8', bevel=0.01)
AMBER  = P_('LS_WhiteTrim', '#e9edf1', rough=0.22, metal=0.0, coat=0.8, grime=0.22, grime_col='#a59f97', wear=0.18, wear_col='#8f969e', bevel=0.02)
HAZ    = M_glow('LS_CyanStrip', '#2fe3ff', 7)
GREEN  = P_('LS_BandGraphite', '#2c3137', rough=0.3, metal=0.55, coat=0.5, grime=0.2, wear=0.2, bevel=0.01)
BLUE   = GREEN
RED    = P_('LS_Red', '#b8322c', rough=0.35, metal=0.1, coat=0.5, grime=0.2, wear=0.2)
FOIL   = P_('LS_MLI', '#c9ced6', rough=0.3, metal=0.9, grime=0.2, grime_col='#5b5650', bump_noise=0.5, bevel=0.01)
RUBBER = P_('LS_Rubber', '#1d2024', rough=0.8, metal=0.0, grime=0.3, grime_col='#6e6a64', bump_noise=0.3)
CHROME = M_paint('LS_Chrome', '#dfe3e9', rough=0.15, metal=1.0, bevel=0.005)
INK    = M_paint('LS_Ink', '#1f2329', rough=0.5, metal=0.0)
INKW   = M_paint('LS_InkWhite', '#f4f7fa', rough=0.4, metal=0.0)
GLASS  = M_glass('LS_Port', '#1b2a36', 0.04)
LAMP   = M_glow('LS_Lamp', '#f2fbff', 12)
AMBERL = M_glow('LS_StatusWhite', '#dff8ff', 9)
GREENL = M_glow('LS_GreenLamp', '#6ee08a', 7)
REDL   = M_glow('LS_RedLamp', '#f25f5c', 8)
HOT    = M_glow('LS_ReactorPort', '#ff8a3a', 4)
WATERL = M_glow('LS_SightGlass', '#7fe6ff', 2.6)
CYANL  = M_glow('LS_Cyan', '#2fe3ff', 10)
MATTEW = P_('LS_ShieldTile', '#e4e8ec', rough=0.62, metal=0.0, grime=0.3, grime_col='#a59f97', wear=0.15, wear_col='#9aa3ad', panel=0.8, bevel=0.03)
CYANS  = M_glow('LS_CyanSoft', '#2fe3ff', 4)
DARKH  = M_glow('LS_Void', '#000000', 0)
SLAG   = M_rock('LS_Slag', '#3e3c3a', '#5f5b57')
FEED   = M_rock('LS_Ilmenite', '#4f4d4b', '#7b7773')
ICE    = M_rock('LS_IceRegolith', '#8b9096', '#d9e2ea')

def M_sandbag(name='LS_Berm'):
    """regolith-filled bags on steep faces (brick rows, axis picked from the normal), loose regolith on top."""
    m = bpy.data.materials.new(name); nt, b = _nodes(m)
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sp = nt.nodes.new('ShaderNodeSeparateXYZ'); link(nt, geo.outputs['Position'], sp.inputs['Vector'])
    sn = nt.nodes.new('ShaderNodeSeparateXYZ'); link(nt, geo.outputs['Normal'], sn.inputs['Vector'])
    ax = nt.nodes.new('ShaderNodeMath'); ax.operation = 'ABSOLUTE'; link(nt, sn.outputs['X'], ax.inputs[0])
    ay = nt.nodes.new('ShaderNodeMath'); ay.operation = 'ABSOLUTE'; link(nt, sn.outputs['Y'], ay.inputs[0])
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; link(nt, ax.outputs[0], gt.inputs[0]); link(nt, ay.outputs[0], gt.inputs[1])
    c1 = nt.nodes.new('ShaderNodeCombineXYZ'); link(nt, sp.outputs['X'], c1.inputs['X']); link(nt, sp.outputs['Z'], c1.inputs['Y'])
    c2 = nt.nodes.new('ShaderNodeCombineXYZ'); link(nt, sp.outputs['Y'], c2.inputs['X']); link(nt, sp.outputs['Z'], c2.inputs['Y'])
    mv = nt.nodes.new('ShaderNodeMix'); mv.data_type = 'VECTOR'
    link(nt, gt.outputs[0], mv.inputs['Factor']); link(nt, c1.outputs[0], mv.inputs[4]); link(nt, c2.outputs[0], mv.inputs[5])
    br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.09; br.inputs['Mortar Smooth'].default_value = 1.0; br.inputs['Bias'].default_value = 0.0
    br.inputs['Brick Width'].default_value = 0.62; br.inputs['Row Height'].default_value = 0.24; br.offset = 0.5
    br.inputs['Color1'].default_value = hexc('#8a857c'); br.inputs['Color2'].default_value = hexc('#9c968b'); br.inputs['Mortar'].default_value = hexc('#55514c')
    link(nt, mv.outputs[1], br.inputs['Vector'])
    top = nt.nodes.new('ShaderNodeMapRange'); top.inputs['From Min'].default_value = -2.0; top.inputs['From Max'].default_value = -1.9
    link(nt, sn.outputs['Z'], top.inputs['Value'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.7; nz.inputs['Detail'].default_value = 10
    link(nt, geo.outputs['Position'], nz.inputs['Vector'])
    gr = nt.nodes.new('ShaderNodeValToRGB'); gr.color_ramp.elements[0].color = hexc('#6f6c69'); gr.color_ramp.elements[1].color = hexc('#959089')
    link(nt, nz.outputs['Fac'], gr.inputs['Fac'])
    # dust film over the bags (patchy)
    nz2 = nt.nodes.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 1.6; nz2.inputs['Detail'].default_value = 6
    link(nt, geo.outputs['Position'], nz2.inputs['Vector'])
    dr = nt.nodes.new('ShaderNodeMapRange'); dr.inputs['From Min'].default_value = 0.4; dr.inputs['From Max'].default_value = 0.7; dr.inputs['To Max'].default_value = 0.55
    link(nt, nz2.outputs['Fac'], dr.inputs['Value'])
    md = nt.nodes.new('ShaderNodeMix'); md.data_type = 'RGBA'; link(nt, dr.outputs[0], md.inputs['Factor'])
    link(nt, br.outputs['Color'], md.inputs[6]); md.inputs[7].default_value = hexc('#8b8780')
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    link(nt, top.outputs[0], mx.inputs['Factor']); link(nt, md.outputs[2], mx.inputs[6]); link(nt, gr.outputs['Color'], mx.inputs[7])
    link(nt, mx.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.95
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; link(nt, top.outputs[0], inv.inputs[1])
    st = nt.nodes.new('ShaderNodeMath'); st.operation = 'MULTIPLY'; st.inputs[1].default_value = 0.9; link(nt, inv.outputs[0], st.inputs[0])
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Distance'].default_value = 0.12; bump.invert = True
    link(nt, st.outputs[0], bump.inputs['Strength']); link(nt, br.outputs['Fac'], bump.inputs['Height'])
    bump2 = nt.nodes.new('ShaderNodeBump'); bump2.inputs['Strength'].default_value = 0.6; bump2.inputs['Distance'].default_value = 0.08
    n3 = nt.nodes.new('ShaderNodeTexNoise'); n3.inputs['Scale'].default_value = 9; n3.inputs['Detail'].default_value = 12
    link(nt, geo.outputs['Position'], n3.inputs['Vector']); link(nt, n3.outputs['Fac'], bump2.inputs['Height'])
    link(nt, bump2.outputs['Normal'], bump.inputs['Normal']); link(nt, bump.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = hexc('#8a857c'); return m
BERM = M_sandbag()
BAG = GRAPH   # canopy curbs: graphite precast

def M_radiator(name='LS_Radiator'):
    """white radiator: fine coolant-tube ribs (local X) + panel seams + light dust."""
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

def M_cells(name='LS_SolarCells'):
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

# ====================================================================== helpers
def lbox(name, size, loc, rot, mat, bevel=0.0):
    """box built in local space then placed via object transform (so Object coords are local)."""
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
    """vertical vessel profile: optional cone/dish bottom, straight shell, ellipsoidal head."""
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

def pipe(name, pts, r, mat, bend=0.35, res=3, c='Mine'):
    """polyline pipe with rounded elbows."""
    P = [Vector(p) for p in pts]; out = [P[0]]
    for i in range(1, len(P) - 1):
        a, b, c2 = P[i - 1], P[i], P[i + 1]
        d1 = (b - a); d2 = (c2 - b); rb = min(bend, d1.length * 0.45, d2.length * 0.45)
        p0 = b - d1.normalized() * rb; p2 = b + d2.normalized() * rb
        for k in range(6):
            t = k / 5; out.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t * t * p2)
    out.append(P[-1])
    ob = curve_tube(name, [tuple(p) for p in out], r, mat, c=c, res=res)
    # flanges at the ends
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

def stencil(name, body, loc, face, size, mat=INK, ex=0.006):
    rot = {'-y': (math.pi / 2, 0, 0), '+y': (math.pi / 2, 0, math.pi), '+x': (math.pi / 2, 0, math.pi / 2), '-x': (math.pi / 2, 0, -math.pi / 2)}[face]
    ob = text(name, body, loc, rot, size, mat, extrude=ex)
    ob.visible_shadow = False   # decals: no floating drop-shadows on curved hulls
    return ob

def plate(name, body, loc, face, w, h, size, bg=INK, fg=INKW, sub=None):
    off = {'-y': (0, -1), '+y': (0, 1), '+x': (1, 0), '-x': (-1, 0)}[face]
    sz = (w, 0.03, h) if face in ('-y', '+y') else (0.03, w, h)
    box(name, sz, loc, bg, bevel=0.008)
    p = (loc[0] + off[0] * 0.02, loc[1] + off[1] * 0.02, loc[2] + (h * 0.14 if sub else 0))
    stencil(name + '_t', body, p, face, size, fg)
    if sub: stencil(name + '_s', sub, (p[0], p[1], loc[2] - h * 0.24), face, size * 0.42, fg)

def lamp(name, loc, mat, r=0.09):
    cyl(name + '_base', r * 1.1, r * 0.9, (loc[0], loc[1], loc[2] - r * 0.9), GRAPH, segs=12)
    sphere(name, r, loc, mat, sub=2)

def radiator_array(name, x0, y0, y1, z0, h, n, axis='y'):
    """vertical double-sided radiator wing of n panels with coolant manifolds + truss posts.
    axis='y': runs along Y at x=x0 (faces +-X); axis='x': runs along X (y0..y1 are X limits) at y=x0 (faces +-Y)."""
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
        if z0 > 0.5: box(name + '_foot', (0.6, 0.6, 0.14), P(c, 0, 0.07), GRAPH, bevel=0.02)
        if k in (0, n):
            for s_ in (-1, 1):
                q = (x0 + s_ * 1.4, c, 0.03) if axis == 'y' else (c, x0 + s_ * 1.4, 0.03)
                beam(name + '_rake', q, P(c, 0, z0 + h * 0.6), 0.1, 0.1, STEEL)
    for zz in (z0 - 0.12, z0 + h + 0.12):
        rod(name + '_manifold', P(y0, 0, zz), P(y1, 0, zz), 0.09, STEELL, segs=12)

# ====================================================================== layout constants
BH, BTX, BY0, BY1, BRUN = 6.6, 3.2, -4.0, 9.0, 4.8     # berm: crest height, crest half-width, crest y-range, slope run
HWY = -5.2; HWX = 3.8                                   # legacy porch reference plane (canopy rear edge)

def g01(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def berm_z(x, y, notch=True):
    dx = max(abs(x) - BTX, 0.0); dy = max(BY0 - y, y - BY1, 0.0); d = math.hypot(dx, dy)
    z = BH * g01(1 - d / BRUN)
    if z > 0: z += 0.12 * noise.noise(Vector((x * 0.35, y * 0.35, 7.0))) * min(1, z)
    if notch and abs(x) < HWX and y < HWY: z = 0.0
    return max(z, 0.0)

# precast retaining panels (white, graphite plinth + cap, cyan reveal strip) on the headwall + notch wing walls
AL_Z, AL_R = 1.75, 1.42
def panel_wall(p0, p1, hfun, pw=1.5, skip_portal=False, thick=0.32):
    a, b = Vector(p0), Vector(p1); L = (b - a).length; u = (b - a).normalized(); ang = math.atan2(u.y, u.x)
    n = max(1, round(L / pw)); w = L / n
    for k in range(n):
        p = a + u * (w * (k + 0.5)); top = round(hfun(p) / 0.25) * 0.25
        if top < 0.5: continue
        z0 = 0.0
        if skip_portal and abs(p.x) < 1.75 + w / 2 - 0.05: z0 = AL_Z + AL_R + 0.35
        if top - z0 < 0.3: continue
        if z0 == 0.0:
            box('ret_plinth', (w - 0.02, thick + 0.08, 0.45), (p.x, p.y, 0.225), GRAPH, rot=(0, 0, ang), bevel=0.02); z0 = 0.45
        box('ret_panel', (w - 0.05, thick, top - z0 - 0.12), (p.x, p.y, (top + z0 - 0.12) / 2), WHITE, rot=(0, 0, ang), bevel=0.035, segs=2)
        box('ret_cap', (w - 0.01, thick + 0.1, 0.12), (p.x, p.y, top - 0.06), GRAPH2, rot=(0, 0, ang), bevel=0.02)
        if top - z0 > 1.4 and z0 < 1: box('ret_cyan', (w - 0.3, thick + 0.012, 0.035), (p.x, p.y, z0 + 0.9), CYANS, rot=(0, 0, ang))
# portal lintel (steel frame around the airlock where it passes the headwall)
# ====================================================================== PRESSURIZED MODULES (above ground, thick shielded hulls)
# two parallel horizontal modules on graphite cradles, joined by a pressurised tunnel. Each hull wears a jacket of
# white water-wall / polyethylene shield segments (radiation + micrometeoroid), seamed by graphite rings, with cyan strips.
MR, MZ = 2.3, 2.95                 # hull radius, axis height
MODS = ((-1.4, 4.6, 'PM-1', 'PROCESS / ECLSS'), (4.4, 4.2, 'PM-2', 'STORES / CONTROL'))
for (my, mhl, mid, msub) in MODS:
    rod(f'{mid}_core', (-mhl, my, MZ), (mhl, my, MZ), MR - 0.05, GRAPH, segs=56)
    nseg = int(round(2 * mhl / 1.5)); sw = 2 * mhl / nseg
    for k in range(nseg):
        x0 = -mhl + k * sw
        rod(f'{mid}_shield', (x0 + 0.04, my, MZ), (x0 + sw - 0.04, my, MZ), MR + 0.12, WHITE, segs=56, bevel=0.02)
    for k in range(nseg + 1):
        x0 = -mhl + k * sw; rod(f'{mid}_seam', (x0 - 0.05, my, MZ), (x0 + 0.05, my, MZ), MR + 0.15, GRAPH2, segs=56)
    for sx in (-1, 1):
        sphere(f'{mid}_cap', MR + 0.1, (sx * mhl, my, MZ), WHITE_S, scale=(0.5, 1, 1), sub=4)
        rod(f'{mid}_cap_ring', (sx * (mhl + 0.02), my, MZ), (sx * (mhl - 0.1), my, MZ), MR + 0.18, GRAPH2, segs=56)
        rod(f'{mid}_cyan', (sx * (mhl - 0.55), my, MZ), (sx * (mhl - 0.5), my, MZ), MR + 0.135, CYANL, segs=56)
        # end-cap service hatch + grab rails
        cyl(f'{mid}_endhatch', 0.55, 0.12, (sx * (mhl + MR * 0.5 + 0.05), my, MZ - 0.3), GRAPH2, rot=(0, math.pi / 2, 0), segs=28)
        for dz in (-0.75, 0.15): rod(f'{mid}_endgrab', (sx * (mhl + 0.9), my - 0.6, MZ + dz), (sx * (mhl + 0.9), my + 0.6, MZ + dz), 0.025, AMBER, segs=8)
    # cradles + footpads
    for cx in (-mhl * 0.62, mhl * 0.62):
        box(f'{mid}_cradle', (0.5, 2 * MR * 0.95, 0.75), (cx, my, 0.55), GRAPH, bevel=0.04)
        for sy in (-1, 1):
            beam(f'{mid}_cradle_leg', (cx, my + sy * MR * 0.8, 0.1), (cx, my + sy * MR * 0.55, 1.2), 0.18, 0.3, STEEL)
            box(f'{mid}_pad', (0.8, 0.8, 0.12), (cx, my + sy * MR * 0.8, 0.06), GRAPH2, bevel=0.02)
    # longitudinal handrail + cable tray along the flanks
    for sy in (-1, 1):
        rod(f'{mid}_rail', (-mhl + 0.4, my + sy * (MR + 0.32), MZ + 0.4), (mhl - 0.4, my + sy * (MR + 0.32), MZ + 0.4), 0.03, STEELL, segs=8)
        for k in range(int(mhl)): rod(f'{mid}_rail_post', (-mhl + 0.6 + k * 2, my + sy * (MR + 0.12), MZ + 0.4), (-mhl + 0.6 + k * 2, my + sy * (MR + 0.32), MZ + 0.4), 0.02, STEELL, segs=6)
    # hull stencils (on the tilted forward shoulder)
    th = 0.72; r_ = MR + 0.135
    stencil(f'st_{mid}', mid, (-2.6, my - r_ * math.cos(th), MZ + r_ * math.sin(th)), '-y', 0.5).rotation_euler = (math.pi / 2 - th, 0, 0)
    th2 = 0.42
    stencil(f'st_{mid}_s', msub, (-2.6, my - r_ * math.cos(th2), MZ + r_ * math.sin(th2)), '-y', 0.16).rotation_euler = (math.pi / 2 - th2, 0, 0)
# connecting tunnel M-1 <-> M-2
rod('tunnel', (0, -1.4, MZ), (0, 4.4, MZ), 1.15, WHITE, segs=40)
for y in (0.95, 2.05): rod('tunnel_ring', (0, y - 0.06, MZ), (0, y + 0.06, MZ), 1.22, GRAPH2, segs=40)
rod('tunnel_cyan', (0, 1.48, MZ), (0, 1.52, MZ), 1.18, CYANL, segs=40)
box('tunnel_cradle', (1.8, 0.5, MZ - 1.15), (0, 1.5, (MZ - 1.15) / 2), GRAPH, bevel=0.03)
# station ID on the front module shoulder (right of the porch)
th = 0.72; r_ = MR + 0.135
stencil('st_ls01', 'LS-01', (3.0, -1.4 - r_ * math.cos(th), MZ + r_ * math.sin(th)), '-y', 0.62).rotation_euler = (math.pi / 2 - th, 0, 0)
stencil('st_ls01s', 'LIFE SUPPORT', (3.0, -1.4 - r_ * math.cos(0.42), MZ + r_ * math.sin(0.42)), '-y', 0.2).rotation_euler = (math.pi / 2 - 0.42, 0, 0)

# ====================================================================== AIRLOCK A1 + dust-cleaning porch
AY0, AY1 = -2.8, -7.3
rod('airlock', (0, AY0, AL_Z), (0, AY1, AL_Z), AL_R, WHITE, segs=48)
for y in (AY0 - 0.9, -6.4, AY1 + 0.15):
    rod('al_ring', (0, y - 0.07, AL_Z), (0, y + 0.07, AL_Z), AL_R + 0.05, STEELL, segs=48)
sphere('al_head', AL_R, (0, AY1, AL_Z), WHITE_S, scale=(1, 0.28, 1), sub=4)
for sx in (-1, 1):   # saddles
    for y in (-6.0, -7.0):
        box('al_saddle', (0.35, 0.4, 0.55), (sx * 0.9, y, 0.27), GRAPH, bevel=0.03)
# outer hatch (rounded rectangle) on the head
HY = AY1 - AL_R * 0.28 - 0.02
box('hatch_frame', (1.25, 0.16, 1.75), (0, HY + 0.04, AL_Z - 0.05), STEELL, bevel=0.08, segs=3)
box('hatch_door', (1.02, 0.14, 1.52), (0, HY - 0.03, AL_Z - 0.05), PALE, bevel=0.07, segs=3)
cyl('hatch_port', 0.13, 0.05, (0, HY - 0.1, AL_Z + 0.42), GLASS, rot=(math.pi / 2, 0, 0), segs=24)
cyl('hatch_port_ring', 0.16, 0.04, (0, HY - 0.09, AL_Z + 0.42), STEELL, rot=(math.pi / 2, 0, 0), segs=24)
cyl('hatch_wheel_hub', 0.06, 0.12, (0, HY - 0.14, AL_Z - 0.1), CHROME, rot=(math.pi / 2, 0, 0), segs=12)
curve_tube('hatch_wheel', [(0.22 * math.cos(a), HY - 0.18, AL_Z - 0.1 + 0.22 * math.sin(a)) for a in [i / 24 * TAU for i in range(25)]], 0.018, CHROME)
for k in range(3):
    a = k / 3 * TAU; rod('hatch_spoke', (0, HY - 0.18, AL_Z - 0.1), (0.22 * math.cos(a), HY - 0.18, AL_Z - 0.1 + 0.22 * math.sin(a)), 0.012, CHROME, segs=6)
for z in (AL_Z + 0.45, AL_Z - 0.55):
    box('hatch_hinge', (0.12, 0.12, 0.22), (-0.62, HY - 0.06, z), STEEL, bevel=0.02)
box('hatch_haz', (1.27, 0.02, 0.04), (0, HY - 0.05, AL_Z - 0.95), HAZ)
stencil('st_al', 'AIRLOCK A1', (0, HY - 0.03, AL_Z + 0.95), '-y', 0.16)
lamp('al_lamp_g', (-0.35, HY - 0.05, AL_Z + 1.22), GREENL, 0.06); lamp('al_lamp_a', (0.35, HY - 0.05, AL_Z + 1.22), AMBERL, 0.06)
for sx in (-1, 1):   # grab handles beside the hatch
    rod('al_grab', (sx * 0.78, HY - 0.12, AL_Z - 0.5), (sx * 0.78, HY - 0.12, AL_Z + 0.4), 0.02, AMBER, segs=8)
# suitports on the left flank of the airlock (two docked suit backpacks)
for k, y in enumerate((-5.65, -6.75)):
    cyl('suitport_ring', 0.38, 0.12, (-AL_R - 0.02, y, AL_Z + 0.1), STEELL, rot=(0, math.pi / 2, 0), segs=32)
    box('suitport_pack', (0.3, 0.52, 0.72), (-AL_R - 0.2, y, AL_Z + 0.05), WHITE_S, bevel=0.07, segs=3)
    box('suitport_pack_lid', (0.05, 0.4, 0.5), (-AL_R - 0.37, y, AL_Z + 0.08), GRAPH, bevel=0.015)
    stencil(f'st_sp{k}', f'SP-{k + 1}', (-AL_R - 0.40, y, AL_Z + 0.5), '-x', 0.09)
# porch canopy (shield-panel roof: shade + micrometeoroid cover over the dust bay)
CZ = 3.85; CY0, CY1 = HWY - 0.4, -10.6
box('canopy_deck', (7.4, CY0 - CY1, 0.22), (0, (CY0 + CY1) / 2, CZ), GRAPH2, bevel=0.03)
for sx in (-1, 1):
    ibeam('canopy_girder', (sx * 3.55, CY0, CZ - 0.25), (sx * 3.55, CY1, CZ - 0.25), 0.25, 0.32, STEEL)
    box('canopy_col', (0.28, 0.28, CZ - 0.4), (sx * 3.4, CY1 + 0.25, (CZ - 0.4) / 2), STEEL, bevel=0.02)
    box('canopy_col_foot', (0.6, 0.6, 0.12), (sx * 3.4, CY1 + 0.25, 0.06), GRAPH, bevel=0.02)
    beam('canopy_knee', (sx * 3.4, CY1 + 0.25, CZ - 1.3), (sx * 3.4, CY1 + 1.3, CZ - 0.4), 0.14, 0.14, STEEL)
ibeam('canopy_front', (-3.6, CY1 + 0.25, CZ - 0.25), (3.6, CY1 + 0.25, CZ - 0.25), 0.25, 0.32, STEEL)
box('canopy_haz', (7.42, 0.02, 0.05), (0, CY1 - 0.01, CZ), HAZ)
for k in range(int((CY0 - CY1) / 1.0)):   # white shield-panel roof tiles over the dust bay
    box('canopy_tile', (7.0, 0.96, 0.16), (0, CY1 + 0.55 + k * 1.0, CZ + 0.19), MATTEW, bevel=0.03)
box('canopy_fascia', (7.5, 0.18, 0.42), (0, CY1 + 0.02, CZ + 0.12), GRAPH2, bevel=0.03)
for sx in (-1.6, 1.6):   # work floodlights under the canopy
    box('flood', (0.7, 0.3, 0.18), (sx, -9.4, CZ - 0.25), GRAPH, rot=(0.5, 0, 0), bevel=0.03)
    box('flood_lens', (0.6, 0.02, 0.12), (sx, -9.56, CZ - 0.3), LAMP, rot=(0.5, 0, 0))
# raised grated dust-mat walkway (steel grating over a regolith-catch pan)
GY0, GY1, GW = AY1 - 0.55, -10.9, 2.6
box('mat_pan', (GW + 0.2, GY0 - GY1 + 0.2, 0.16), (0, (GY0 + GY1) / 2, 0.08), GRAPH, bevel=0.02)
box('mat_pan_fill', (GW, GY0 - GY1, 0.05), (0, (GY0 + GY1) / 2, 0.14), SLAG, bevel=0.0)
for k in range(int(GW / 0.09)):
    x = -GW / 2 + 0.05 + k * 0.09; beam('grate', (x, GY0, 0.2), (x, GY1, 0.2), 0.014, 0.05, STEELL, bevel=0.0)
for k in range(int((GY0 - GY1) / 0.4) + 1):
    y = GY1 + k * 0.4; beam('grate_x', (-GW / 2, y, 0.2), (GW / 2, y, 0.2), 0.02, 0.05, STEEL, bevel=0.0)
box('mat_haz', (GW + 0.2, 0.05, 0.03), (0, GY1 - 0.05, 0.2), HAZ)
box('mat_ramp', (GW, 0.9, 0.08), (0, GY1 - 0.55, 0.14), GRAPH2, rot=(0.2, 0, 0), bevel=0.01)
rail('mat_rail', [(-GW / 2 - 0.15, GY1, 0.2), (-GW / 2 - 0.15, GY0 + 0.2, 0.2)], AMBER)
rail('mat_rail', [(GW / 2 + 0.15, GY1, 0.2), (GW / 2 + 0.15, -8.6, 0.2)], AMBER)
# air-shower arch (compressed-gas dust blow-off) with nozzle bar
ASY = -8.0
for sx in (-1, 1):
    box('shower_post', (0.18, 0.3, 2.5), (sx * 1.55, ASY, 1.45), GRAPH2, bevel=0.03)
    for k in range(6): cyl('nozzle', 0.035, 0.09, (sx * 1.45, ASY, 0.6 + k * 0.36), CHROME, rot=(0, math.pi / 2, 0), segs=8)
box('shower_head', (3.3, 0.34, 0.24), (0, ASY, 2.75), GRAPH2, bevel=0.03)
for k in range(8): cyl('nozzle_top', 0.035, 0.09, (-1.2 + k * 0.34, ASY, 2.6), CHROME, segs=8)
box('shower_haz', (3.32, 0.02, 0.05), (0, ASY - 0.18, 2.75), HAZ)
stencil('st_dust', 'DUST BAY  -  BRUSH  /  BLOW  /  STEP', (0, ASY - 0.19, 2.93), '-y', 0.1, INK)
box('blower', (0.9, 0.7, 0.8), (2.5, -8.0, 0.4), GRAPH2, bevel=0.04)
for k in range(5): box('blower_fin', (0.92, 0.02, 0.5), (2.5, -8.36, 0.45), STEELL) if k == 0 else None
pipe('blow_hose', [(2.5, -8.0, 0.8), (2.5, -8.0, 1.4), (1.64, ASY, 1.4)], 0.06, RUBBER, bend=0.3)
# boot/glove brush station (rotary brushes on a post pair), right of the mat
BX = 2.15
for sy in (-9.1, -10.2): box('brush_post', (0.14, 0.14, 1.4), (BX, sy, 0.7), STEEL, bevel=0.02)
for zz, rr_ in ((0.32, 0.17), (1.1, 0.14)):
    cyl('brush', rr_, 0.95, (BX, -9.65, zz), RUBBER, rot=(math.pi / 2, 0, 0), segs=20, bevel=0.0)
    cyl('brush_core', rr_ * 0.4, 1.12, (BX, -9.65, zz), CHROME, rot=(math.pi / 2, 0, 0), segs=12)
box('brush_motor', (0.25, 0.25, 0.25), (BX, -10.25, 1.1), AMBER, bevel=0.03)
# suit-tool rack & dust-cover hooks on the left
box('rack', (0.12, 1.6, 1.8), (-2.15, -9.3, 0.9), GRAPH2, bevel=0.02)
for k in range(4): rod('hook', (-2.15, -8.8 - k * 0.35, 1.5), (-2.0, -8.8 - k * 0.35, 1.55), 0.02, STEELL, segs=6)

# ====================================================================== POWER: switchgear SWG-1 + reactor feeder
SWX, SWY = -5.6, -9.2
box('swg_plinth', (3.0, 1.3, 0.25), (SWX, SWY, 0.125), GRAPH, bevel=0.03)
box('swg_body', (2.7, 1.0, 2.3), (SWX, SWY + 0.04, 1.4), WHITE_S, bevel=0.04)   # front face sits behind the doors (no z-fight)
box('swg_roof', (2.9, 1.2, 0.12), (SWX, SWY, 2.6), GRAPH2, bevel=0.02)
for k in range(3):
    x = SWX - 0.88 + k * 0.88
    box('swg_door', (0.82, 0.04, 2.0), (x, SWY - 0.51, 1.4), WHITE_S, bevel=0.015)
    box('swg_handle', (0.05, 0.05, 0.3), (x + 0.3, SWY - 0.55, 1.35), CHROME, bevel=0.01)
    cyl('swg_meter', 0.09, 0.03, (x - 0.1, SWY - 0.54, 2.05), INKW, rot=(math.pi / 2, 0, 0), segs=20)
    lamp(f'swg_lamp{k}', (x + 0.2, SWY - 0.55, 2.1), [GREENL, GREENL, AMBERL][k], 0.04)
    for j in range(5): box('swg_louver', (0.6, 0.03, 0.03), (x, SWY - 0.54, 0.7 + j * 0.08), GRAPH)
box('swg_haz', (2.72, 0.02, 0.05), (SWX, SWY - 0.53, 0.4), HAZ)
plate('swg_plate', 'SWG-1', (SWX - 0.88, SWY - 0.55, 1.6), '-y', 0.72, 0.4, 0.17, bg=INK, fg=INKW, sub='REACTOR FEED 1.2 kV')
# amber HV triangle (invented warning mark)
bm_ = bmesh.new(); t = [bm_.verts.new((SWX + 0.88 + 0.22 * math.cos(math.pi / 2 + k * TAU / 3), SWY - 0.555, 1.75 + 0.22 * math.sin(math.pi / 2 + k * TAU / 3))) for k in range(3)]
bm_.faces.new(t); _obj(bm_, 'swg_hv', AMBER, smooth=False)
stencil('st_hv', 'HV', (SWX + 0.88, SWY - 0.565, 1.71), '-y', 0.13, INK)
# cable trays on stanchions: feeder arrives from the reactor (far left), distribution goes into module M-1 + to the plants
def tray_run(name, pts, z=0.9, post=5.0, c='Mine', heightf=None, cables=('#1c1d1f', '#c8322a', '#1c1d1f')):
    P = [Vector(p) for p in pts]
    for a, b in zip(P, P[1:]):
        L = (Vector((b.x, b.y, 0)) - Vector((a.x, a.y, 0))).length; n = max(1, int(L / post))
        for i in range(n + 1):
            p = a.lerp(b, i / n); gz = heightf(p.x, p.y) if heightf else 0.0
            box(name + '_stanchion', (0.12, 0.12, z), (p.x, p.y, gz + z / 2), STEEL, bevel=0.01, c=c)
            box(name + '_foot', (0.4, 0.4, 0.08), (p.x, p.y, gz + 0.04), GRAPH, bevel=0.01, c=c)
            u = (b - a).normalized(); s = Vector((-u.y, u.x, 0))
            beam(name + '_arm', (p.x - s.x * 0.3, p.y - s.y * 0.3, gz + z), (p.x + s.x * 0.3, p.y + s.y * 0.3, gz + z), 0.08, 0.08, STEEL, c=c)
    # tray + cables follow the ground
    pts2 = []
    for a, b in zip(P, P[1:]):
        L = (b - a).length; n = max(1, int(L / 2.0))
        for i in range(n): p = a.lerp(b, i / n); pts2.append(Vector((p.x, p.y, (heightf(p.x, p.y) if heightf else 0.0) + z + 0.05)))
    pts2.append(Vector((P[-1].x, P[-1].y, (heightf(P[-1].x, P[-1].y) if heightf else 0.0) + z + 0.05)))
    for k, col in enumerate(cables):
        m = RUBBER if col == '#1c1d1f' else RED
        off = (k - (len(cables) - 1) / 2) * 0.12
        q = []
        for i, p in enumerate(pts2):
            j = min(i + 1, len(pts2) - 1); i0 = max(i - 1, 0); u = (pts2[j] - pts2[i0]).normalized(); s = Vector((-u.y, u.x, 0))
            q.append(tuple(p + s * off + Vector((0, 0, 0.06))))
        curve_tube(name + '_cable', q, 0.05, m, c=c, res=2)
    for a, b in zip(pts2, pts2[1:]):
        beam(name + '_tray', a, b, 0.5, 0.04, GRAPH2, c=c, bevel=0.0)
        for s in (-1, 1):
            u = (b - a).normalized(); sv = Vector((-u.y, u.x, 0)) * 0.25 * s
            beam(name + '_tray_lip', a + sv + Vector((0, 0, 0.06)), b + sv + Vector((0, 0, 0.06)), 0.02, 0.12, STEELL, c=c, bevel=0.0)
FEEDER_NEAR = [(SWX - 1.5, SWY, 0), (-12.0, -9.6, 0), (-19.0, -10.2, 0)]
tray_run('feeder', FEEDER_NEAR)
pipe('feeder_drop', [(SWX - 1.5, SWY, 1.0), (SWX - 1.5, SWY, 0.5), (SWX - 1.36, SWY, 0.5)], 0.09, RED, bend=0.2)
# distribution: conduit bundle up the headwall face into the module
for k, dx in enumerate((-0.15, 0.0, 0.15)):
    pipe('conduit', [(SWX + 1.2 + dx, SWY + 0.5, 2.2), (SWX + 1.2 + dx, SWY + 3.2, 2.2), (SWX + 1.2 + dx, -3.62, 2.3)], 0.05, [RUBBER, RED, RUBBER][k], bend=0.4)
box('conduit_clamp', (0.6, 0.2, 0.12), (SWX + 1.2, -5.0, 2.2), STEEL, bevel=0.01)
tray_run('dist_o2', [(SWX - 0.5, SWY + 0.6, 0), (-9.2, -6.0, 0), (-10.2, 2.6, 0)], z=0.75, post=3.5, cables=('#1c1d1f', '#c8322a'))
tray_run('dist_h2o', [(-3.9, -5.0, 0), (7.6, -5.0, 0), (8.6, -1.0, 0)], z=0.6, post=3.5, cables=('#1c1d1f',))

# ====================================================================== O2 EXTRACTION (left)
OX, OY = -12.6, -1.4     # reactor axis
# receiving bin for ilmenite-rich regolith (rover tips into it)
RBX, RBY = -15.6, -6.8
frustum('feed_bin', RBX, RBY, 0.0, 1.5, 0.75, 1.35, 0.1, AMBER)
for (a, b) in (((-1, -1), (1, -1)), ((-1, 1), (1, 1)), ((-1, -1), (-1, 1)), ((1, -1), (1, 1))):
    ibeam('bin_rim', (RBX + a[0] * 1.42, RBY + a[1] * 1.42, 1.55), (RBX + b[0] * 1.42, RBY + b[1] * 1.42, 1.55), 0.18, 0.18, GRAPH)
heap('feed_bin_heap', (RBX, RBY, 1.0), 0, 0.55, FEED, sq=(1.25, 1.25), seed=21)
box('bin_haz', (2.8, 0.02, 0.28), (RBX, RBY - 1.37, 1.15), HAZ, rot=(0.38, 0, 0))
stencil('st_feed', 'FEED  -  ILMENITE REGOLITH', (RBX, RBY - 1.03, 0.62), '-y', 0.13, INK).rotation_euler = (math.pi / 2 + 0.38, 0, 0)
box('bin_ramp', (2.6, 3.0, 0.1), (RBX, RBY - 2.6, 0.6), GRAPH2, rot=(-0.36, 0, 0), bevel=0.02)
# inclined screw conveyor bin -> feed hopper
S0 = Vector((RBX + 0.4, RBY + 0.9, 0.9)); S1 = Vector((OX - 0.6, OY - 0.9, 8.9))
rod('screw_tube', S0, S1, 0.34, AMBER, segs=28)
for t in range(1, 11):
    p = S0.lerp(S1, t / 11); dd = (S1 - S0).normalized(); rod('screw_flange', p - dd * 0.04, p + dd * 0.04, 0.42, GRAPH, segs=28)
rod('screw_motor', S1, S1 + (S1 - S0).normalized() * 0.7, 0.3, GRAPH, segs=20)
for t in (0.35, 0.7):
    p = S0.lerp(S1, t)
    for s in (-1, 1): beam('screw_leg', (p.x + s * 0.7, p.y - 0.2, 0.05), (p.x, p.y, p.z - 0.32), 0.14, 0.14, STEEL)
# feed hopper + lock-hopper valve on a 4-leg frame over the reactor
HZ0, HZ1 = 7.4, 9.2
frustum('o2_hopper', OX, OY, HZ0, HZ1, 0.45, 1.35, 0.08, WHITE)
heap('o2_hopper_fill', (OX, OY, HZ1 - 0.35), 0, 0.4, FEED, sq=(1.25, 1.25), seed=23)
box('o2_lockvalve', (0.75, 0.75, 0.6), (OX, OY, HZ0 - 0.3), GRAPH2, bevel=0.04)
piston('o2_valve_ram', (OX + 0.4, OY - 0.6, HZ0 - 0.1), (OX + 0.4, OY - 0.38, HZ0 - 0.5), 0.06, AMBER, CHROME)
for sx in (-1, 1):
    for sy in (-1, 1):
        box('o2_frame_leg', (0.22, 0.22, HZ0 + 0.2), (OX + sx * 1.75, OY + sy * 1.75, (HZ0 + 0.2) / 2), STEEL, bevel=0.02)
        box('o2_frame_foot', (0.6, 0.6, 0.12), (OX + sx * 1.75, OY + sy * 1.75, 0.06), GRAPH, bevel=0.02)
for zz in (HZ0 - 0.6 + 0.35, 4.0):
    for (a, b) in (((-1, -1), (1, -1)), ((-1, 1), (1, 1)), ((-1, -1), (-1, 1)), ((1, -1), (1, 1))):
        ibeam('o2_frame_girt', (OX + a[0] * 1.75, OY + a[1] * 1.75, zz), (OX + b[0] * 1.75, OY + b[1] * 1.75, zz), 0.2, 0.22, STEEL)
box('o2_deck', (3.7, 3.7, 0.08), (OX, OY, HZ0 - 0.2), GRAPH2, bevel=0.01)
rail('o2_deck_rail', [(OX - 1.8, OY - 1.8, HZ0 - 0.16), (OX + 1.8, OY - 1.8, HZ0 - 0.16), (OX + 1.8, OY + 1.8, HZ0 - 0.16)], AMBER, h=1.0)
ladder('o2_ladder', OX + 1.95, OY + 0.6, 0.0, HZ0 - 0.2, along='y')
# H2-reduction reactor R-1: insulated vertical vessel with cone bottom, flanged nozzles, hot inspection port
vvessel('o2_reactor', (OX, OY), 1.2, 1.6, 6.0, FOIL, bottom='cone', bdepth=0.9, dome=0.45, bands=(2.2, 3.4, 4.6, 5.7), band_mat=STEELL)
cyl('o2_reactor_flange', 1.3, 0.16, (OX, OY, 6.05), STEELL, segs=40)
cyl('o2_reactor_neck', 0.3, 0.9, (OX, OY, 6.8), STEELL, segs=20)
for k in range(16): sphere('o2_bolt', 0.04, (OX + 1.3 * math.cos(k * TAU / 16), OY + 1.3 * math.sin(k * TAU / 16), 6.14), CHROME, sub=1)
# hot sight port (amber-orange, hooded)
box('o2_port_hood', (0.55, 0.3, 0.45), (OX + 0.35, OY - 1.27, 3.95), GRAPH, bevel=0.03)
cyl('o2_port', 0.12, 0.05, (OX + 0.35, OY - 1.43, 3.9), HOT, rot=(math.pi / 2, 0, 0), segs=20)
cyl('o2_port_ring', 0.16, 0.05, (OX + 0.35, OY - 1.41, 3.9), STEELL, rot=(math.pi / 2, 0, 0), segs=20)
plate('o2_plate', 'R-1', (OX - 0.45, OY - 1.24, 3.0), '-y', 0.75, 0.42, 0.2, sub='H2 REDUCTION 900 C')
for k, a in enumerate((0.3, 2.2, 4.0)):   # induction heater leads
    pipe('o2_heater_lead', [(OX + 1.25 * math.cos(a), OY + 1.25 * math.sin(a), 2.8 + k * 0.5), (OX + 1.7 * math.cos(a), OY + 1.7 * math.sin(a), 2.8 + k * 0.5),
                            (OX + 1.7 * math.cos(a), OY + 1.7 * math.sin(a), 0.85)], 0.05, RED if k == 1 else RUBBER, bend=0.25)
# slag discharge -> skip
pipe('slag_chute', [(OX, OY, 0.75), (OX, OY - 1.6, 0.75), (OX, OY - 2.4, 0.55)], 0.2, STEEL, bend=0.4)
box('slag_skip', (2.0, 1.4, 0.8), (OX, OY - 3.2, 0.4), GRAPH2, bevel=0.04)
heap('slag_heap', (OX, OY - 3.2, 0.62), 0, 0.45, SLAG, sq=(0.9, 0.6), seed=27)
stencil('st_slag', 'SLAG', (OX, OY - 3.91, 0.45), '-y', 0.2, INKW)
# electrolysis unit EL-1 (cell stack cabinet + bus bars) behind the reactor
EX, EY = -12.4, 3.4
box('el_body', (3.4, 2.0, 2.3), (EX, EY, 1.35), PALE, bevel=0.05)
box('el_base', (3.7, 2.3, 0.2), (EX, EY, 0.1), GRAPH, bevel=0.02)
for k in range(14): box('el_cell', (0.1, 1.7, 1.6), (EX - 1.3 + k * 0.2, EY - 0.02, 1.3), GRAPH2 if k % 2 else STEELL, bevel=0.01)
box('el_top', (3.2, 1.8, 0.2), (EX, EY, 2.6), GRAPH2, bevel=0.03)
for sx in (-1.1, 1.1): rod('el_busbar', (EX + sx, EY - 1.0, 2.6), (EX + sx, EY - 1.0, 3.1), 0.05, AMBER, segs=10)
lamp('el_lamp', (EX + 1.4, EY - 1.02, 2.3), GREENL, 0.05)
stencil('st_el', 'EL-1  ELECTROLYSIS', (EX, EY - 1.03, 2.25), '-y', 0.16)
pipe('el_feedgas', [(OX, OY, 7.2), (OX, OY, 7.0), (OX - 1.1, OY, 7.0), (OX - 1.1, EY, 7.0), (OX - 1.1, EY, 2.9), (EX - 0.5, EY, 2.9), (EX - 0.5, EY, 2.7)], 0.1, STEELL, bend=0.4)
stencil('st_h2o_vap', 'H2O VAPOUR', (OX - 1.22, (OY + EY) / 2, 6.0), '-x', 0.12)
pipe('el_h2_return', [(EX + 0.8, EY, 2.7), (EX + 0.8, EY, 3.25), (OX + 0.9, OY + 1.3, 3.25), (OX + 0.9, OY + 0.95, 3.25)], 0.07, RED, bend=0.3)
# O2 storage: two spherical pressure vessels on legs + ring girder + manifold
O2T = [(-15.8, 7.0), (-12.3, 7.6)]
for k, (tx, ty) in enumerate(O2T):
    sphere('o2_tank', 1.4, (tx, ty, 2.6), WHITE_S, sub=4)
    cyl('o2_tank_band', 1.42, 0.22, (tx, ty, 2.6), GREEN, segs=48, bevel=0.01)
    cyl('o2_tank_girder', 1.48, 0.12, (tx, ty, 2.35), STEEL, segs=48, bevel=0.01)
    for j in range(4):
        a = j * TAU / 4 + 0.4; box('o2_tank_leg', (0.18, 0.18, 2.4), (tx + 1.42 * math.cos(a), ty + 1.42 * math.sin(a), 1.2), STEEL, bevel=0.02)
        box('o2_tank_pad', (0.5, 0.5, 0.1), (tx + 1.42 * math.cos(a), ty + 1.42 * math.sin(a), 0.05), GRAPH, bevel=0.01)
    stencil(f'st_o2_{k}', f'O2-{k + 1}', (tx + 0.3, ty - 1.37, 3.2), '-y', 0.34, INK).rotation_euler = (math.pi / 2 - 0.2, 0, 0.2)
    cyl('o2_tank_nozzle', 0.12, 0.35, (tx, ty, 4.1), STEELL, segs=12)
    cyl('o2_tank_valve', 0.16, 0.12, (tx, ty, 4.3), GREEN, segs=12)
pipe('o2_out', [(EX - 1.2, EY + 1.0, 1.9), (EX - 1.2, EY + 2.0, 1.9), (O2T[1][0], O2T[1][1] - 1.6, 1.9), (O2T[1][0], O2T[1][1] - 1.35, 2.2)], 0.07, GREEN, bend=0.3)
pipe('o2_cross', [(O2T[0][0], O2T[0][1], 4.3), (O2T[0][0], O2T[0][1], 4.7), (O2T[1][0], O2T[1][1], 4.7), (O2T[1][0], O2T[1][1], 4.3)], 0.06, GREEN, bend=0.25)
pipe('o2_to_module', [(O2T[1][0] + 1.2, O2T[1][1], 1.2), (-6.5, 7.6, 1.2), (-6.5, 7.6, 3.4)], 0.07, GREEN, bend=0.4)
# radiator array RAD-1 (reactor + electrolysis heat rejection), coolant loop
R1Y, R1Z, R1H = 10.6, 2.6, 5.0
radiator_array('rad1', R1Y, -19.4, -10.6, R1Z, R1H, 4, axis='x')
plate('rad1_plate', 'RAD-1', (-18.3, R1Y - 0.08, R1Z - 0.7), '-y', 0.8, 0.34, 0.19)
stencil('st_rad1', 'R-1 / EL-1 HEAT REJECTION', (-15.0, R1Y - 0.06, R1Z + R1H + 0.55), '-y', 0.2, INK)
for k, (xr, zr) in enumerate(((-17.75, 2.0), (-18.05, 1.0))):
    zm = R1Z - 0.12 if k else R1Z + R1H + 0.12
    pipe('rad1_loop', [(xr, R1Y, zm), (xr, R1Y - 0.35, zm), (xr, R1Y - 0.35, zr), (xr, OY, zr), (OX - 1.22, OY, zr)], 0.08, STEELL, bend=0.45)

# ====================================================================== WATER RECOVERY (right)
WX, WY = 11.0, -5.6
# ice-regolith feed hopper on frame + melt/sublimation vessel under it
frustum('ice_hopper', WX, WY, 5.3, 6.9, 0.4, 1.15, 0.08, WHITE)
heap('ice_fill', (WX, WY, 6.6), 0, 0.35, ICE, sq=(1.05, 1.05), seed=31)
stencil('st_ice', 'ICE FEED', (WX, WY - 0.88, 6.25), '-y', 0.2).rotation_euler = (math.pi / 2 + 0.44, 0, 0)
for sx in (-1, 1):
    for sy in (-1, 1):
        box('ice_leg', (0.18, 0.18, 5.5), (WX + sx * 1.45, WY + sy * 1.45, 2.75), STEEL, bevel=0.02)
        box('ice_foot', (0.5, 0.5, 0.1), (WX + sx * 1.45, WY + sy * 1.45, 0.05), GRAPH, bevel=0.01)
for (a, b) in (((-1, -1), (1, -1)), ((-1, 1), (1, 1)), ((-1, -1), (-1, 1)), ((1, -1), (1, 1))):
    ibeam('ice_girt', (WX + a[0] * 1.45, WY + a[1] * 1.45, 5.2), (WX + b[0] * 1.45, WY + b[1] * 1.45, 5.2), 0.18, 0.2, STEEL)
    beam('ice_brace', (WX + a[0] * 1.45, WY + a[1] * 1.45, 0.3), (WX + b[0] * 1.45, WY + b[1] * 1.45, 2.6), 0.08, 0.08, STEEL)
vvessel('ice_melter', (WX, WY), 1.0, 1.0, 4.0, WHITE, bottom='dish', dome=0.4, bands=(1.6, 2.5, 3.4), band_mat=BLUE)
cyl('ice_neck', 0.25, 0.6, (WX, WY, 4.6), GRAPH2, segs=16)
plate('ice_plate', 'M-1', (WX, WY - 1.02, 2.05), '-y', 0.7, 0.4, 0.2, sub='ICE MELT / SUBLIMATE')
lamp('ice_lamp', (WX + 0.55, WY - 0.88, 3.6), AMBERL, 0.05)
for k in range(4): box('ice_skirt', (0.15, 0.15, 0.6), (WX + 0.75 * math.cos(k * TAU / 4 + 0.78), WY + 0.75 * math.sin(k * TAU / 4 + 0.78), 0.45), GRAPH, bevel=0.01)
# condenser: finned horizontal shell, coolant to RAD-2
CDX, CDY, CDZ = 14.4, -3.4, 2.3
rod('cond_shell', (CDX - 1.6, CDY, CDZ), (CDX + 1.6, CDY, CDZ), 0.55, STEELL, segs=32)
for k in range(22): rod('cond_fin', (CDX - 1.45 + k * 0.138, CDY, CDZ), (CDX - 1.43 + k * 0.138, CDY, CDZ), 0.85, WHITE_S if k % 2 else STEELL, segs=32, bevel=0.0)
for sx in (-1, 1):
    box('cond_saddle', (0.3, 1.4, CDZ - 0.4), (CDX + sx * 1.3, CDY, (CDZ - 0.4) / 2), GRAPH, bevel=0.03)
plate('cond_plate', 'C-1', (CDX, CDY - 1.2, 0.95), '-y', 1.1, 0.44, 0.2, sub='CONDENSER')
for sx in (-0.45, 0.45): box('cond_plate_post', (0.06, 0.06, 0.75), (CDX + sx, CDY - 1.17, 0.37), STEEL)
pipe('vapour_line', [(WX, WY, 4.85), (WX, WY, 5.0), (CDX - 1.9, WY, 5.0), (CDX - 1.9, CDY, 5.0), (CDX - 1.9, CDY, CDZ), (CDX - 1.6, CDY, CDZ)], 0.11, FOIL, bend=0.4)
# filtration / polishing skid
FX, FY = 11.0, -0.9
box('filt_skid', (3.0, 1.6, 0.2), (FX, FY, 0.1), GRAPH, bevel=0.02)
for k in range(4):
    vvessel('filt_can', (FX - 1.1 + k * 0.73, FY), 0.26, 0.3, 1.55, WHITE_S, dome=0.6, segs=24, bands=(0.6, 1.3), band_mat=BLUE)
pipe('filt_hdr', [(FX - 1.4, FY - 0.45, 1.7), (FX + 1.4, FY - 0.45, 1.7)], 0.06, BLUE)
for k in range(4): pipe('filt_drop', [(FX - 1.1 + k * 0.73, FY - 0.45, 1.7), (FX - 1.1 + k * 0.73, FY - 0.45, 1.9), (FX - 1.1 + k * 0.73, FY, 1.9), (FX - 1.1 + k * 0.73, FY, 1.75)], 0.035, BLUE, bend=0.08)
pipe('cond_to_filt', [(CDX + 1.6, CDY, CDZ - 0.4), (CDX + 1.9, CDY, CDZ - 0.4), (CDX + 1.9, FY - 0.45, 1.7), (FX + 1.4, FY - 0.45, 1.7)], 0.06, BLUE, bend=0.3)
stencil('st_filt', 'FILTRATION  F-1..4', (FX, FY - 0.81, 0.55), '-y', 0.12, INKW)
# recycling / storage tanks H2O-1..3 with sight glasses, catwalk + ladder
HT = [(9.8, 3.4), (12.4, 3.4), (15.0, 3.4)]
for k, (tx, ty) in enumerate(HT):
    vvessel('h2o_tank', (tx, ty), 1.05, 0.5, 4.6, WHITE, dome=0.32, bands=(0.9, 2.6, 4.3), band_mat=BLUE)
    box('h2o_sight_bg', (0.16, 0.06, 3.0), (tx - 0.55, ty - 0.93, 2.35), GRAPH, rot=(0, 0, 0.5), bevel=0.01)
    box('h2o_sight', (0.08, 0.06, 2.0 - 0.4 * k), (tx - 0.56, ty - 0.97, 0.95 + (2.0 - 0.4 * k) / 2), WATERL, rot=(0, 0, 0.5))
    stencil(f'st_h2o_{k}', f'H2O-{k + 1}', (tx + 0.18, ty - 1.09, 3.3), '-y', 0.27, INK)
    for j in range(4):
        a = j * TAU / 4 + 0.78; box('h2o_leg', (0.16, 0.16, 0.5), (tx + 0.8 * math.cos(a), ty + 0.8 * math.sin(a), 0.25), GRAPH, bevel=0.02)
stencil('st_recyc', 'RECYCLED WATER  -  POTABLE', (12.4, 2.33, 1.35), '-y', 0.14, INK)
box('h2o_catwalk', (6.8, 0.9, 0.08), (12.4, 3.4, 5.15), GRAPH2, bevel=0.01)
for x in (9.0, 15.8):
    box('h2o_cw_post', (0.15, 0.15, 5.15), (x, 2.95, 2.57), STEEL, bevel=0.01)
rail('h2o_cw_rail', [(9.0, 2.95, 5.19), (15.8, 2.95, 5.19)], AMBER, h=1.0)
ladder('h2o_ladder', 16.05, 2.8, 0.0, 5.15, along='y')
pipe('filt_to_tank', [(FX + 1.4, FY + 0.45, 1.5), (FX + 1.8, FY + 0.45, 1.5), (FX + 1.8, 1.9, 1.5), (HT[1][0], 1.9, 1.5), (HT[1][0], 2.3, 1.5)], 0.06, BLUE, bend=0.3)
pipe('tank_hdr', [(HT[0][0], HT[0][1] + 1.2, 1.0), (HT[2][0], HT[2][1] + 1.2, 1.0)], 0.07, BLUE)
pipe('h2o_to_module', [(HT[0][0], HT[0][1] + 1.2, 1.0), (6.6, 4.6, 1.0), (6.6, 4.6, 3.4)], 0.07, BLUE, bend=0.4)
pipe('grey_return', [(6.4, 0.8, 3.0), (6.4, 0.8, 1.2), (FX - 1.6, FY + 0.45, 1.2), (FX - 1.4, FY + 0.45, 1.2)], 0.05, STEELL, bend=0.3)
stencil('st_grey', 'GREYWATER RETURN', (7.8, 0.66, 1.42), '-y', 0.1, INK)
# radiator array RAD-2
R2Y, R2Z, R2H = 7.6, 2.8, 4.8
radiator_array('rad2', R2Y, 8.6, 17.4, R2Z, R2H, 4, axis='x')
plate('rad2_plate', 'RAD-2', (16.4, R2Y - 0.08, R2Z - 0.7), '-y', 0.8, 0.34, 0.19)
for k, (xr, zr) in enumerate(((17.7, CDZ + 0.3), (18.0, CDZ - 0.3))):
    zm = R2Z + R2H + 0.12 if k == 0 else R2Z - 0.12
    pipe('rad2_loop', [(xr - 0.3, R2Y, zm), (xr, R2Y, zm), (xr, R2Y, zr), (xr, CDY, zr), (CDX + 1.6, CDY, zr)], 0.07, STEELL, bend=0.4)

# ====================================================================== CO2 SCRUBBING (front right)
SX, SY = 6.4, -8.4
box('co2_skid', (4.0, 2.6, 0.22), (SX, SY, 0.11), GRAPH, bevel=0.02)
box('co2_haz', (4.02, 0.02, 0.05), (SX, SY - 1.31, 0.3), HAZ)
for k in range(4):
    bx = SX - 1.35 + k * 0.9
    box('co2_bed', (0.72, 0.9, 2.1), (bx, SY + 0.25, 1.3), GRAPH2, bevel=0.05)
    for j in range(3): box('co2_bed_rib', (0.75, 0.93, 0.06), (bx, SY + 0.25, 0.6 + j * 0.7), STEEL, bevel=0.01)
    stencil(f'st_bed{k}', 'ABCD'[k], (bx, SY - 0.21, 1.75), '-y', 0.26, INKW)
    cyl('co2_valve', 0.11, 0.25, (bx, SY + 0.25, 2.5), STEELL, segs=12)
    box('co2_actuator', (0.26, 0.2, 0.2), (bx, SY + 0.25, 2.72), AMBER, bevel=0.03)
    lamp(f'co2_lamp{k}', (bx + 0.22, SY - 0.22, 2.2), GREENL if k % 2 == 0 else AMBERL, 0.035)
pipe('co2_hdr', [(SX - 1.6, SY + 0.25, 2.95), (SX + 1.6, SY + 0.25, 2.95)], 0.09, STEELL)
plate('co2_plate', 'CO2 SCRUB', (SX - 0.45, SY - 0.24, 0.72), '-y', 1.5, 0.36, 0.17, sub='4-BED SWING  /  VACUUM REGEN')
box('co2_blower', (1.0, 0.8, 0.9), (SX + 1.45, SY - 0.75, 0.67), PALE, bevel=0.04)
cyl('co2_blower_fan', 0.3, 0.06, (SX + 1.45, SY - 1.16, 0.7), GRAPH, rot=(math.pi / 2, 0, 0), segs=24)
# cabin-air ducts in from the module (insulated flex duct), to the beds
for k, dz in enumerate((0.0, 0.5)):
    pipe('cabin_duct', [(3.0, -3.6, 3.1 + dz), (3.0, -4.6, 3.1 + dz), (4.6, -4.6, 3.1 + dz), (4.6, SY + 1.2, 3.1 + dz), (SX - 1.1 + k * 1.8, SY + 1.2, 3.1 + dz), (SX - 1.1 + k * 1.8, SY + 0.7, 2.7)], 0.15, FOIL, bend=0.45)
# vent stacks (vacuum desorption / relief)
for k, (vx, vh) in enumerate(((SX + 1.0, 8.2), (SX + 1.6, 7.0))):
    rod('vent_stack', (vx, SY + 0.95, 0.22), (vx, SY + 0.95, vh), 0.16, STEELL, segs=20)
    rod('vent_tip', (vx, SY + 0.95, vh), (vx, SY + 0.95, vh + 0.35), 0.21, GRAPH, segs=20)
    cyl('vent_band', 0.17, 0.3, (vx, SY + 0.95, vh - 0.8), AMBER, segs=20)
    for j in range(3):
        a = j * TAU / 3 + 0.3; cable('vent_guy', (vx, SY + 0.95, vh - 1.6), (vx + 1.6 * math.cos(a), SY + 0.95 + 1.6 * math.sin(a), 0.22), 0.012, STEEL, sag=0.05, n=4)
    lamp(f'vent_lamp{k}', (vx, SY + 0.95, vh + 0.5), REDL, 0.07)
stencil('st_vent', 'VENT', (SX + 1.0, SY + 0.78, 4.6), '-y', 0.2, INK)
# CO2 transfer line to the Tank Farm (methane plant) on low pipe sleepers
CO2L = [(SX + 1.6, SY + 0.25, 2.95), (SX + 2.6, SY + 0.25, 2.95), (SX + 2.6, -9.9, 0.6), (19.0, -9.9, 0.6)]
pipe('co2_transfer', CO2L, 0.1, STEELL, bend=0.5)
for x in range(10, 19, 3): box('co2_sleeper', (0.3, 0.8, 0.5), (x, -9.9, 0.25), GRAPH, bevel=0.02)
plate('co2_tf', 'CO2  TO TANK FARM', (15.0, -10.0, 1.15), '-y', 1.6, 0.3, 0.14, bg=GRAPH, fg=INKW)
for x in (13.6, 16.4): box('co2_tf_post', (0.08, 0.08, 1.0), (x, -9.95, 0.5), STEEL)

# ====================================================================== hull crown: module radiator fin, vents, beacon, antenna
TOPZ = MZ + MR + 0.12   # hull crown
radiator_array('rad0', 4.4, -2.6, 2.6, TOPZ + 0.9, 3.4, 2, axis='x')
for k in range(3): box('rad0_footing', (1.0, 1.0, 0.5), (-2.6 + k * 2.6, 4.4, TOPZ + 0.1), GRAPH, bevel=0.03)
plate('rad0_plate', 'RAD-0  CABIN', (-1.3, 4.32, TOPZ + 0.62), '-y', 1.1, 0.3, 0.13)
for (x, y) in ((-1.6, -1.4), (1.6, -1.4)):
    cyl('hull_vent', 0.22, 1.2, (x, y, TOPZ + 0.5), STEELL, segs=16)
    cyl('hull_vent_cap', 0.3, 0.12, (x, y, TOPZ + 1.15), GRAPH, segs=16)
rod('beacon_mast', (-3.8, -1.4, TOPZ - 0.2), (-3.8, -1.4, TOPZ + 2.6), 0.06, STEEL, segs=10)
lamp('beacon', (-3.8, -1.4, TOPZ + 2.8), AMBERL, 0.16)
rod('ant_mast', (3.4, 4.4, TOPZ - 0.2), (3.4, 4.4, TOPZ + 3.5), 0.07, STEEL, segs=10)
sphere('ant_dish', 0.55, (3.4, 4.2, TOPZ + 3.6), WHITE_S, scale=(1, 0.3, 1), sub=3, rot=(0.5, 0, 0.6))

# ====================================================================== solar arrays on tall masts (backup power)
SUN = Vector((-0.55, -0.6, 0.58))
saz = math.atan2(SUN.y, SUN.x)
for k, (mx, my) in enumerate(((-7.6, 13.6), (7.6, 13.6))):
    MH = 15.0
    lathe('solar_mast', [(0.38, 0.0), (0.3, 1.0), (0.2, MH - 0.6), (0.2, MH)], (mx, my, 0), STEELL, segs=16)
    cyl('solar_base', 0.9, 0.5, (mx, my, 0.25), GRAPH, segs=16, bevel=0.03)
    cyl('solar_gimbal', 0.3, 0.6, (mx, my, MH + 0.2), GRAPH2, segs=16)
    rz = saz + math.pi / 2
    lbox('solar_panel', (6.4, 0.1, 9.0), (mx, my, MH - 4.4), (0, 0, rz), CELLS, bevel=0.0)
    lbox('solar_back', (6.3, 0.05, 8.9), (mx - 0.08 * math.sin(rz), my + 0.08 * math.cos(rz), MH - 4.4), (0, 0, rz), GRAPH2)
    lbox('solar_frame_v', (0.14, 0.18, 9.1), (mx, my, MH - 4.4), (0, 0, rz), STEEL)
    for zz in (MH - 8.9, MH + 0.05):
        lbox('solar_frame_h', (6.5, 0.16, 0.12), (mx, my, zz), (0, 0, rz), STEEL)
    pipe('solar_cable', [(mx, my, 1.0), (mx, my, 0.5), (mx * 0.62, my - 3.2, 0.4)], 0.05, RUBBER, bend=0.4)
    box('solar_combiner', (0.7, 0.5, 0.9), (mx * 0.62, my - 3.4, 0.45), PALE, bevel=0.03)
    stencil(f'st_sa{k}', f'SA-{k + 1}', (mx * 0.62, my - 3.66, 0.6), '-y', 0.16)

# ====================================================================== STAGE: ground, distant reactor + feeder run, astronaut
height = build_stage(keep_flat=((0, 1, 30),))
# remove stage rocks that would poke through the plant footprint
for ob in list(coll('Stage').objects):
    if ob.type == 'MESH' and ob.name.split('.')[0] in ('boulder', 'pebble'):
        vs_ = ob.data.vertices; c_ = sum((v.co for v in vs_), Vector()) / len(vs_)
        if -22 < c_.x < 22 and -12 < c_.y < 17: bpy.data.objects.remove(ob)
# far feeder run to the reactor (Stage, not exported)
RXR, RYR = -62.0, 26.0
FAR = [(-19.0, -10.2, 0), (-34.0, -3.0, 0), (-48.0, 10.0, 0), (RXR + 6.5, RYR - 4.5, 0)]
tray_run('feeder_far', FAR, z=0.9, post=7.0, c='Stage', heightf=height)
# fission reactor behind a ring berm with its own radiator wings
gz = height(RXR, RYR)
bm = bmesh.new(); n = 64; vr = {}
for i in range(n):
    for j in range(13):
        a = i / n * TAU; rad = 5.0 + j * 0.55; t = (j / 12)
        z = 4.2 * math.sin(math.pi * t) ** 0.8 + 0.15 * noise.noise(Vector((math.cos(a) * 3, math.sin(a) * 3, j * 0.3)))
        x, y = RXR + rad * math.cos(a), RYR + rad * math.sin(a)
        vr[i, j] = bm.verts.new((x, y, height(x, y) + max(z, 0) - 0.05))
for i in range(n):
    for j in range(12):
        bm.faces.new((vr[i, j], vr[(i + 1) % n, j], vr[(i + 1) % n, j + 1], vr[i, j + 1]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
_obj(bm, 'reactor_berm', BERM, c='Stage', smooth=True, angle=180)
rv = lathe('reactor_vessel', dome_prof(1.6, gz, gz + 3.2, dome=0.4), (RXR, RYR, 0), PALE, segs=32)
coll('Mine').objects.unlink(rv); coll('Stage').objects.link(rv)
for k in range(4):
    a = k * TAU / 4 + 0.35
    p0 = Vector((RXR + 1.7 * math.cos(a), RYR + 1.7 * math.sin(a), gz + 5.0)); p1 = Vector((RXR + 9.5 * math.cos(a), RYR + 9.5 * math.sin(a), gz + 5.0))
    beam('reactor_rad', p0, p1, 0.08, 4.2, RAD, c='Stage', up=Vector((0, 0, 1)))
    rod('reactor_rad_hdr', p0 + Vector((0, 0, 2.15)), p1 + Vector((0, 0, 2.15)), 0.08, STEELL, c='Stage')
cyl('reactor_mast', 0.5, 7.4, (RXR, RYR, gz + 3.7), STEEL, segs=16, c='Stage')
sphere('reactor_beacon', 0.3, (RXR, RYR, gz + 7.7), REDL, sub=2, c='Stage')
box('reactor_sign', (2.6, 0.08, 1.0), (RXR + 7.5, RYR - 8.5, height(RXR + 7.5, RYR - 8.5) + 1.2), INK, rot=(0, 0, 0.6), c='Stage')
text('reactor_sign_t', 'FPU-1  KEEP OUT 1 km', (RXR + 7.53, RYR - 8.56, height(RXR + 7.5, RYR - 8.5) + 1.2), (math.pi / 2, 0, 0.6), 0.22, INKW, c='Stage')
pipe('co2_transfer_far', [(19.0, -9.9, 0.6), (21.5, -9.9, 0.6), (34.0, -24.0, 0.6), (60.0, -30.0, 0.6)], 0.1, STEELL, bend=2.0, c='Stage')
for (p0, p1) in (((21.5, -9.9), (34.0, -24.0)), ((34.0, -24.0), (60.0, -30.0))):
    v0, v1 = Vector(p0), Vector(p1); n = int((v1 - v0).length / 4.5)
    for k in range(1, n):
        q = v0.lerp(v1, k / n); ang = math.atan2(v1.y - v0.y, v1.x - v0.x) + math.pi / 2
        box('co2_far_sleeper', (0.3, 0.8, 0.5), (q.x, q.y, height(q.x, q.y) + 0.25), GRAPH, rot=(0, 0, ang), bevel=0.02, c='Stage')
ld = bpy.data.lights.new('PorchLight', 'AREA'); ld.energy = 260; ld.size = 3.0; ld.color = hexc('#ffe9c8')[:3]
lo = bpy.data.objects.new('PorchLight', ld); coll('Stage').objects.link(lo); lo.location = (0, -8.6, CZ - 0.45)
world_and_sun(tuple(SUN), 5.5)
astro = astronaut((-0.7, -11.9, 0.0), rot_z=0.35)
convert_curves()
cam = setup_render(48 if not QUICK else 16)

# ====================================================================== stats + export
def tri_count(objs):
    dg = bpy.context.evaluated_depsgraph_get(); t = 0
    for ob in objs:
        if ob.type != 'MESH': continue
        me = ob.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); t += len(me.loop_triangles); ob.evaluated_get(dg).to_mesh_clear()
    return t
mine = [o for o in coll('Mine').all_objects]
dg = bpy.context.evaluated_depsgraph_get()
mn = Vector((1e9, 1e9, 1e9)); mxv = Vector((-1e9, -1e9, -1e9))
for ob in mine:
    if ob.type != 'MESH': continue
    for c_ in ob.bound_box:
        w = ob.matrix_world @ Vector(c_); mn = Vector(map(min, mn, w)); mxv = Vector(map(max, mxv, w))
CEN = Vector(((mn.x + mxv.x) / 2, (mn.y + mxv.y) / 2, 0))
print('STATS objects', len(mine), 'tris', tri_count(mine), 'bbox', tuple(round(v, 2) for v in mn), tuple(round(v, 2) for v in mxv), 'centre', tuple(round(v, 2) for v in CEN), flush=True)

ONLY = A.get('only', 'turn,hero')
if 'glb' in ONLY:
    root = bpy.data.objects.new('LifeSupport', None); coll('Mine').objects.link(root)
    for ob in mine:
        if ob.parent is None:
            ob.parent = root
    root.location = -CEN; bpy.context.view_layer.update()
    export_glb(os.path.join(OUT, f'{NAME}_master.glb'))
    root.location = (0, 0, 0)
    for ob in mine:
        if ob.parent == root:
            mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = mw
    bpy.data.objects.remove(root); bpy.context.view_layer.update()
if 'blend' in ONLY:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'{NAME}_master.blend'), compress=True)
TT = (0.0, 1.5, 4.0)
if 'turn' in ONLY:
    os.makedirs(os.path.join(OUT, 'turntable'), exist_ok=True)
    turntable(cam, os.path.join(OUT, 'turntable'), TT, 60, 22, size=1000 if not QUICK else 400, samples=int(A.get('ts', 40)) if not QUICK else 12)
if 'hero' in ONLY:
    w, h = (3840, 2160) if not QUICK else (960, 540)
    if A.get('res'): w, h = [int(v) for v in A['res'].split('x')]
    shoot(cam, os.path.join(OUT, 'hero.png'), (-1.5, -0.5, 4.0), (13.0, -29.5, 6.0), w, h, lens=24, samples=int(A.get('hs', 48)) if not QUICK else 16)
