"""Planet Stack - Starter Ship master (concept B look, original design, no real logos).
blender -b -P build_starter_ship.py -- --out DIR [--quick 1] [--only glb,blend,turn,hero,close] [--hs 128]
Imports the shared stage/sun/astronaut/render helpers from art/3d/mine_concepts/_src/mc_common.py (read-only).
Blender coords: Z-up, metres, front = -Y (exports as glTF +Y up, front +Z). Origin = base centre on the pad top.
Layout (bottom -> top): engines under the skirt | FUEL TANK section (LOX/CH4, plumbing, Tank Farm umbilical) |
CARGO BAY (drop-down door + davit hoist, 215 deg) | CREW DECK (4 sleep pods/ports + crew airlock with dust-off, 275 deg).
No bottom entry: crew use a caged ship-mounted ladder (rest platform ~10 m, top platform at the airlock sill).
Temporary until the Launch Pad adds an elevator/prep area (not modelled here).
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', 'mine_concepts', '_src')))
import bpy, bmesh
from mathutils import Vector, Matrix, Euler, noise
from mc_common import *
from mc_common import _obj, _nodes

A = argv(); OUT = A.get('out', HERE); os.makedirs(OUT, exist_ok=True)
QUICK = A.get('quick') == '1'
reset(); rr = random.Random(7)
TAU = math.tau
R = 4.0            # hull radius (8.0 m diameter), true scale
Z_AFT, Z_BODY, Z_NOSE, Z_TIP = 2.4, 3.4, 31.0, 40.0

# ================================================================ materials
# hull feature layout (shared by geometry + the weathering masks so streaks/soot fall below the real sources)
FRONT_A = -math.pi / 2
RCS_POS = []
for _k in range(4):
    _a = TAU * _k / 4 + 0.3
    RCS_POS.append((_a, 32.3))
    _b = _a + math.pi / 4
    RCS_POS.append((_b, 5.2 if abs(((_b - FRONT_A) + math.pi) % TAU - math.pi) > 0.7 else 9.9))
POD_ANG = [TAU * _k / 4 + math.pi / 4 for _k in range(4)]
VENTS = [(math.radians(d) + s * 0.16, 4.75) for d in (30, 110, 330) for s in (-1, 1)] + \
        [(math.radians(d) + s * 0.16, 21.0) for d in (150, 330) for s in (-1, 1)]
ENG_A = [math.pi / 4 + _k * math.pi / 2 for _k in range(4)]; ENG_R = 2.25
DUST_COL = '#56585b'      # neutral grey regolith

def _m(N, L, op, a, b=None, clamp=False):
    n = N.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: L.new(v, n.inputs[i])
    return n.outputs[0]
def _mr(N, L, v, f0, f1, t0=0.0, t1=1.0):
    n = N.new('ShaderNodeMapRange'); n.clamp = True
    n.inputs['From Min'].default_value = f0; n.inputs['From Max'].default_value = f1
    n.inputs['To Min'].default_value = t0; n.inputs['To Max'].default_value = t1; L.new(v, n.inputs['Value']); return n.outputs[0]
def _nz(N, L, vec, scale, detail=6, rough=0.6):
    n = N.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    if vec is not None: L.new(vec, n.inputs['Vector'])
    return n.outputs['Fac']

def ng_weather():
    """world-space masks: Grime (streaks running down from vents/RCS/pods), Soot (engine base, landing pods, RCS), Hull (near-hull mask)."""
    g = bpy.data.node_groups.new('NG_Weather', 'ShaderNodeTree')
    for nm in ('Grime', 'Soot', 'Hull'): g.interface.new_socket(nm, in_out='OUTPUT', socket_type='NodeSocketFloat')
    N, L = g.nodes, g.links
    out = N.new('NodeGroupOutput')
    geo = N.new('ShaderNodeNewGeometry'); sp = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Position'], sp.inputs[0])
    X, Y, Z = sp.outputs['X'], sp.outputs['Y'], sp.outputs['Z']
    ang = _m(N, L, 'ARCTAN2', Y, X)
    rxy = _m(N, L, 'SQRT', _m(N, L, 'ADD', _m(N, L, 'MULTIPLY', X, X), _m(N, L, 'MULTIPLY', Y, Y)))
    hull = _mr(N, L, rxy, R + 1.6, R + 0.9)
    cv = N.new('ShaderNodeCombineXYZ'); L.new(_m(N, L, 'MULTIPLY', ang, R * 3.2), cv.inputs['X']); L.new(_m(N, L, 'MULTIPLY', Z, 0.05), cv.inputs['Y'])
    streak = _mr(N, L, _nz(N, L, cv.outputs[0], 1.0, 8, 0.65), 0.36, 0.6)
    cv2 = N.new('ShaderNodeCombineXYZ'); L.new(_m(N, L, 'MULTIPLY', ang, R * 9.0), cv2.inputs['X']); L.new(_m(N, L, 'MULTIPLY', Z, 0.12), cv2.inputs['Y'])
    streak2 = _mr(N, L, _nz(N, L, cv2.outputs[0], 1.0, 6, 0.6), 0.42, 0.64)
    streaks = _m(N, L, 'MAXIMUM', streak, _m(N, L, 'MULTIPLY', streak2, 0.8))
    def src(a, zs, w, Lh, up=0.15, fade=0.0):
        d = _m(N, L, 'ABSOLUTE', _m(N, L, 'SUBTRACT', _m(N, L, 'FLOORED_MODULO', _m(N, L, 'ADD', _m(N, L, 'SUBTRACT', ang, a), math.pi), TAU), math.pi))
        h = _mr(N, L, _m(N, L, 'MULTIPLY', d, R), w, w * 0.3)
        dz = _m(N, L, 'SUBTRACT', zs, Z)
        v = _m(N, L, 'MULTIPLY', _mr(N, L, dz, -up, 0.0), _mr(N, L, dz, 0.0, Lh, 1.0, fade))
        return _m(N, L, 'MULTIPLY', h, v)
    def mx(lst):
        acc = lst[0]
        for s in lst[1:]: acc = _m(N, L, 'MAXIMUM', acc, s)
        return acc
    gsrc = [src(a, z - 0.3, 0.75, 9.0, 0.1, 0.1) for a, z in VENTS] + [src(a, z, 0.8, 11.0, 0.2, 0.15) for a, z in RCS_POS] + \
           [src(a, 25.3, 1.6, 14.0, 0.2, 0.2) for a in POD_ANG] + [src(a, 24.3, 0.9, 12.0, 0.0, 0.1) for a in (FRONT_A, 0.0, math.pi)] + \
           [src(a, 11.0, 0.9, 6.0, 0.0, 0.1) for a in (FRONT_A - 0.62, FRONT_A + 0.62, 0.0, math.pi)]
    grime = _m(N, L, 'ADD', _m(N, L, 'MULTIPLY', _m(N, L, 'MULTIPLY', mx(gsrc), streaks), 1.4), _m(N, L, 'MULTIPLY', streaks, 0.08), clamp=True)
    mott = _mr(N, L, _nz(N, L, geo.outputs['Position'], 0.25, 6, 0.6), 0.52, 0.72, 0.0, 0.12)          # broad uneven discolouration
    grime = _m(N, L, 'MAXIMUM', grime, mott)
    brk = _mr(N, L, _nz(N, L, None, 2.2, 8, 0.7), 0.35, 0.62, 0.35, 1.0)
    ssrc = [src(a, 25.6, 2.0, 7.0, 1.4, 0.0) for a in POD_ANG] + [src(a, z + 0.4, 0.75, 2.4, 0.9, 0.0) for a, z in RCS_POS]
    base = _m(N, L, 'POWER', _mr(N, L, Z, 2.4, 8.5, 1.0, 0.0), 1.6)
    soot = _m(N, L, 'MULTIPLY', mx(ssrc + [base]), brk, clamp=True)
    L.new(_m(N, L, 'MULTIPLY', grime, hull), out.inputs['Grime']); L.new(_m(N, L, 'MULTIPLY', soot, hull), out.inputs['Soot']); L.new(hull, out.inputs['Hull'])
    return g
NG_W = ng_weather()

def decorate(m, seams=None, dust=(0.0, 9.0, 1.0), top_dust=0.45, dust_col=DUST_COL, wear=0.0, wear_col='#2a3245', wear_metal=0.3,
             grime=1.0, soot=1.0, cavity=1.0):
    """Heavy weathering on an M_paint material: deep panel seams, edge wear, grime streaks, soot, height+cavity regolith dust."""
    nt = m.node_tree; N, L = nt.nodes, nt.links; b = N['Principled BSDF']
    col_link = next((l for l in nt.links if l.to_socket == b.inputs['Base Color']), None)
    col = col_link.from_socket if col_link else None
    if col is None:
        rgb = N.new('ShaderNodeRGB'); rgb.outputs[0].default_value = b.inputs['Base Color'].default_value; col = rgb.outputs[0]
    nrm_link = next((l for l in nt.links if l.to_socket == b.inputs['Normal']), None)
    nrm = nrm_link.from_socket if nrm_link else None
    def sock(name):
        s = next((l.from_socket for l in nt.links if l.to_socket == b.inputs[name]), None)
        if s is None:
            v = N.new('ShaderNodeValue'); v.outputs[0].default_value = b.inputs[name].default_value; s = v.outputs[0]
        return s
    metal, rough = sock('Metallic'), sock('Roughness')
    def mixc(f, a, c):
        n = N.new('ShaderNodeMix'); n.data_type = 'RGBA'; L.new(f, n.inputs['Factor']); L.new(a, n.inputs[6])
        if isinstance(c, str): n.inputs[7].default_value = hexc(c)
        else: L.new(c, n.inputs[7])
        return n.outputs[2]
    def mixf(f, a, v):
        n = N.new('ShaderNodeMix'); n.data_type = 'FLOAT'; L.new(f, n.inputs['Factor']); L.new(a, n.inputs[2])
        if isinstance(v, (int, float)): n.inputs[3].default_value = v
        else: L.new(v, n.inputs[3])
        return n.outputs[0]
    tc = N.new('ShaderNodeTexCoord'); geo = N.new('ShaderNodeNewGeometry')
    wps = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Position'], wps.inputs[0]); WZ = wps.outputs['Z']
    halo = None
    if seams:
        pw, ph, rad = seams
        sx = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sx.inputs[0])
        at = _m(N, L, 'ARCTAN2', sx.outputs['Y'], sx.outputs['X'])
        cb = N.new('ShaderNodeCombineXYZ'); L.new(_m(N, L, 'MULTIPLY', at, rad), cb.inputs['X']); L.new(sx.outputs['Z'], cb.inputs['Y'])
        def brick(mortar, smooth):
            br = N.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 1.0; br.offset = 0.5
            br.inputs['Brick Width'].default_value = pw; br.inputs['Row Height'].default_value = ph
            br.inputs['Mortar Size'].default_value = mortar; br.inputs['Mortar Smooth'].default_value = smooth
            for k in ('Color1', 'Color2'): br.inputs[k].default_value = (1, 1, 1, 1)
            br.inputs['Mortar'].default_value = (0, 0, 0, 1); L.new(cb.outputs[0], br.inputs['Vector']); return br.outputs['Fac']
        seam = brick(0.02, 0.15); halo = brick(0.07, 0.8)
        col = mixc(_m(N, L, 'MULTIPLY', halo, 0.12), col, '#4a4d52')        # grime collects along the seams
        col = mixc(_m(N, L, 'MULTIPLY', seam, 0.95), col, '#0c0d10')        # deep, dark panel lines
        bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 1.0; bump.inputs['Distance'].default_value = 0.03
        L.new(_m(N, L, 'SUBTRACT', 1.0, seam), bump.inputs['Height'])
        if nrm: L.new(nrm, bump.inputs['Normal'])
        nrm = bump.outputs['Normal']
        rough = mixf(seam, rough, 0.85)
    if wear > 0:   # edge wear from bevel-vs-true normal (works on thin panels) + chips around the seams
        bv = N.new('ShaderNodeBevel'); bv.inputs['Radius'].default_value = 0.045; bv.samples = 6
        dp = N.new('ShaderNodeVectorMath'); dp.operation = 'DOT_PRODUCT'; L.new(bv.outputs['Normal'], dp.inputs[0]); L.new(geo.outputs['Normal'], dp.inputs[1])
        edge = _mr(N, L, dp.outputs['Value'], 0.998, 0.95)
        chip = _mr(N, L, _nz(N, L, tc.outputs['Object'], 16.0, 10, 0.7), 0.42, 0.58)
        w = _m(N, L, 'MULTIPLY', _m(N, L, 'MULTIPLY', edge, chip), 1.6)
        if halo is not None:
            chip2 = _mr(N, L, _nz(N, L, tc.outputs['Object'], 22.0, 8, 0.7), 0.52, 0.6)
            w = _m(N, L, 'ADD', w, _m(N, L, 'MULTIPLY', _m(N, L, 'MULTIPLY', halo, chip2), 1.5))
        w = _m(N, L, 'MULTIPLY', w, wear, clamp=True)
        col = mixc(w, col, wear_col); metal = mixf(w, metal, wear_metal); rough = mixf(w, rough, 0.5)
    W = N.new('ShaderNodeGroup'); W.node_tree = NG_W
    if grime > 0:
        gf = _m(N, L, 'MULTIPLY', W.outputs['Grime'], 0.95 * grime, clamp=True)
        col = mixc(gf, col, '#34363a'); rough = mixf(gf, rough, 0.8)
    if dust:
        h0, h1, amt = dust
        zl = _m(N, L, 'ADD', WZ, _m(N, L, 'MULTIPLY', _m(N, L, 'SUBTRACT', _nz(N, L, geo.outputs['Position'], 0.6, 6, 0.6), 0.5), 5.0))   # ragged dust line
        hr = _m(N, L, 'MULTIPLY', _m(N, L, 'ADD', _mr(N, L, zl, h1 * 0.35, h1, 1.0, 0.0), _mr(N, L, WZ, 0.0, h1 * 1.6, 0.4, 0.0)), amt)
        brk = _mr(N, L, _nz(N, L, geo.outputs['Position'], 1.4, 10, 0.65), 0.3, 0.62, 0.6, 1.25)
        d1 = _m(N, L, 'MULTIPLY', hr, brk)
        ao = N.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = 0.5; ao.samples = 8
        cav = _m(N, L, 'SUBTRACT', 1.0, ao.outputs['AO'])
        cl = _mr(N, L, WZ, 0.0, 18.0, 1.8, 0.5)
        d3 = _m(N, L, 'MULTIPLY', _m(N, L, 'MULTIPLY', cav, cl), cavity)
        nsz = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Normal'], nsz.inputs[0])
        up = _mr(N, L, nsz.outputs['Z'], 0.45, 0.92, 0.0, top_dust)
        fine = _mr(N, L, _nz(N, L, geo.outputs['Position'], 6.0, 10, 0.7), 0.3, 0.7, 0.55, 1.1)
        d2 = _m(N, L, 'MULTIPLY', up, fine)
        ad = _m(N, L, 'ADD', _m(N, L, 'ADD', d1, d2), d3, clamp=True)
        col = mixc(ad, col, dust_col)
        metal = mixf(ad, metal, 0.0); rough = mixf(ad, rough, 0.96)
        cw = _m(N, L, 'SUBTRACT', b.inputs['Coat Weight'].default_value, _m(N, L, 'MULTIPLY', ad, 1.5), clamp=True)
        L.new(cw, b.inputs['Coat Weight'])
    if soot > 0:
        sf = _m(N, L, 'MULTIPLY', W.outputs['Soot'], soot, clamp=True)
        col = mixc(sf, col, '#141312'); rough = mixf(sf, rough, 0.9); metal = mixf(sf, metal, 0.0)
    L.new(col, b.inputs['Base Color']); L.new(metal, b.inputs['Metallic']); L.new(rough, b.inputs['Roughness'])
    if nrm: L.new(nrm, b.inputs['Normal'])
    return m

GRIME_C = '#7e8084'
STEEL = decorate(M_paint('S_Steel', '#c3c8ce', rough=0.42, metal=0.72, grime=0.5, grime_col='#55575b', bevel=0.02, dirt_scale=1.2),
                 seams=(1.9, 1.2, R), dust=(0.0, 10.0, 1.0), wear=0.6, wear_col='#e1e5ea', wear_metal=1.0)
STEEL_P = decorate(M_paint('S_SteelPlain', '#b2b7be', rough=0.4, metal=0.75, grime=0.3, grime_col='#55575b', bevel=0.01), dust=(0.0, 4.0, 1.0))
WHITE = decorate(M_paint('S_White', '#e8edf5', rough=0.26, metal=0.0, grime=0.3, grime_col=GRIME_C, coat=0.6, bevel=0.02, dirt_scale=1.6),
                 seams=(1.6, 1.1, R), dust=(0.0, 11.0, 1.05), wear=1.0, wear_col='#2c3342', wear_metal=0.35)
WHITE_P = decorate(M_paint('S_WhitePanel', '#e8edf5', rough=0.26, metal=0.0, grime=0.3, grime_col=GRIME_C, coat=0.6, bevel=0.01, dirt_scale=1.6),
                   seams=(1.6, 1.1, R), dust=(0.0, 11.0, 1.05), wear=1.0, wear_col='#2c3342', wear_metal=0.35)
GRAPH_P = decorate(M_paint('S_GraphitePanel', '#2a3245', rough=0.36, metal=0.3, grime=0.15, grime_col='#5f6166', coat=0.35, bevel=0.01),
                   seams=(0.62, 0.62, R), dust=(0.0, 7.0, 1.0), top_dust=0.6, wear=0.8, wear_col='#9aa1aa', wear_metal=1.0)
WHITE_S = decorate(M_paint('S_WhiteSmooth', '#e8edf5', rough=0.25, metal=0.0, grime=0.28, grime_col=GRIME_C, coat=0.6, bevel=0.015),
                   dust=(0.0, 6.0, 1.0), wear=1.0, wear_col='#2c3342', wear_metal=0.35)
GRAPH = decorate(M_paint('S_Graphite', '#2a3245', rough=0.36, metal=0.45, grime=0.15, grime_col='#5f6166', coat=0.35, bevel=0.015),
                 seams=(0.62, 0.62, R), dust=(0.0, 7.0, 1.0), top_dust=0.6, wear=0.8, wear_col='#9aa1aa', wear_metal=1.0)
GRAPH_S = decorate(M_paint('S_Graphite2', '#3a4258', rough=0.34, metal=0.5, grime=0.12, bevel=0.01), dust=(0.0, 6.0, 1.0), top_dust=0.6,
                   wear=0.8, wear_col='#a4abb4', wear_metal=1.0)
STEELD = decorate(M_paint('S_SteelDark', '#5b667e', rough=0.38, metal=0.8, grime=0.3, bevel=0.01), dust=(0.0, 6.0, 1.0), top_dust=0.6,
                  wear=0.7, wear_col='#b8bec6', wear_metal=1.0)
SATIN = decorate(M_paint('S_Satin', '#9aa3ad', rough=0.22, metal=1.0, bevel=0.005), dust=(0.0, 4.0, 1.0), grime=0.6)
NOZ = M_paint('S_Nozzle', '#35373a', rough=0.45, metal=1.0, grime=0.5, grime_col='#151515', bevel=0.005)
def M_bell():
    """engine bell: heat-tinted steel, blue/bronze temper bands toward the throat, sooty lip."""
    m = bpy.data.materials.new('S_EngineBell'); nt, b = _nodes(m); N, L = nt.nodes, nt.links
    geo = N.new('ShaderNodeNewGeometry'); sp = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Position'], sp.inputs[0])
    t = _mr(N, L, sp.outputs['Z'], 0.75, 3.0)
    ramp = N.new('ShaderNodeValToRGB'); el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = hexc('#1a1a1b'); el[1].position = 1.0; el[1].color = hexc('#8a7a62')
    e = el.new(0.12); e.color = hexc('#4a4c50'); e = el.new(0.45); e.color = hexc('#a4a8ae'); e = el.new(0.72); e.color = hexc('#4b5878')
    L.new(t, ramp.inputs['Fac'])
    nz = _mr(N, L, _nz(N, L, None, 6.0, 8, 0.6), 0.3, 0.7, 0.75, 1.1)
    c = N.new('ShaderNodeMix'); c.data_type = 'RGBA'; c.blend_type = 'MULTIPLY'; c.inputs['Factor'].default_value = 1.0
    L.new(ramp.outputs['Color'], c.inputs[6]); cc = N.new('ShaderNodeCombineColor'); L.new(nz, cc.inputs[0]); L.new(nz, cc.inputs[1]); L.new(nz, cc.inputs[2])
    L.new(cc.outputs[0], c.inputs[7]); L.new(c.outputs[2], b.inputs['Base Color'])
    b.inputs['Metallic'].default_value = 0.55; L.new(_mr(N, L, t, 0.0, 1.0, 0.7, 0.45), b.inputs['Roughness'])
    m.diffuse_color = hexc('#55585c'); return m
BELL = M_bell()
SOLAR = M_paint('S_Solar', '#2a3245', rough=0.45, metal=0.2, panel=3.0, coat=0.2, bevel=0.005)   # matte cells, no glossy glazing look
INK = M_paint('S_Ink', '#1f2329', rough=0.55, metal=0.0)
AMBER_HZ = decorate(M_paint('S_Hazard', '#ffb020', rough=0.5, hazard=('#ffb020', '#2a3245'), hazard_scale=3.0, grime=0.25, bevel=0.005),
                    dust=(0.0, 3.0, 0.8), top_dust=0.55, wear=0.9, wear_col='#3a4258')
HOSE = decorate(M_paint('S_FuelHose', '#2b2d31', rough=0.7, metal=0.0, grime=0.3, bevel=0.005), dust=(0.0, 2.0, 0.9), top_dust=0.7, grime=0.0, soot=0.0)
CYAN = M_glow('S_Cyan', '#3ad0ff', 16)
CYANS = M_glow('S_CyanSoft', '#3ad0ff', 5)
LAMP = M_glow('S_Lamp', '#fff4e4', 30)
WARM = M_glow('S_WarmGlow', '#ffc98a', 14)
GLASS = M_glass('S_PortGlass', '#c8e6ff', 0.02)
SENSOR = M_paint('S_SensorGlass', '#0d1420', rough=0.08, metal=0.0, coat=1.0, bevel=0.0)
# interior (crew deck + bay)
CABIN = M_paint('S_CabinWall', '#d9dde3', rough=0.6, metal=0.0, bevel=0.01, panel=2.5)
CABIN_W = M_paint('S_PodLining', '#efe0cc', rough=0.7, metal=0.0, bevel=0.01)
CABIN_D = M_paint('S_CabinTrim', '#3a4258', rough=0.5, metal=0.2, bevel=0.01)
FABRIC = M_paint('S_Mattress', '#7d8aa3', rough=0.9, metal=0.0, bevel=0.03, bump_noise=0.15)
BLANKET = M_paint('S_Blanket', '#e8701a', rough=0.85, metal=0.0, bevel=0.04, bump_noise=0.2)
PILLOW = M_paint('S_Pillow', '#eef1f5', rough=0.9, metal=0.0, bevel=0.05)
BRISTLE = M_paint('S_Bristle', '#1f2329', rough=0.95, metal=0.0, bevel=0.0, bump_noise=0.6)
FLOOR = M_paint('S_DeckFloor', '#5b667e', rough=0.55, metal=0.4, panel=3.0, bevel=0.005, grime=0.2)
# pad
def M_pad():
    m = bpy.data.materials.new('M_SinteredPad'); nt, b = _nodes(m); N, L = nt.nodes, nt.links; tc = N.new('ShaderNodeTexCoord')
    sx = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sx.inputs[0])
    vor = N.new('ShaderNodeTexVoronoi'); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = 0.55
    vor.inputs['Randomness'].default_value = 0.15; L.new(tc.outputs['Object'], vor.inputs['Vector'])
    seam = _mr(N, L, vor.outputs['Distance'], 0.0, 0.03, 1.0, 0.0)
    vc = N.new('ShaderNodeTexVoronoi'); vc.inputs['Scale'].default_value = 0.55; vc.inputs['Randomness'].default_value = 0.15
    L.new(tc.outputs['Object'], vc.inputs['Vector'])
    tile = N.new('ShaderNodeValToRGB'); tile.color_ramp.elements[0].color = hexc('#505254'); tile.color_ramp.elements[1].color = hexc('#6b6d70')
    L.new(vc.outputs['Color'], tile.inputs['Fac'])
    rad = N.new('ShaderNodeVectorMath'); rad.operation = 'LENGTH'; L.new(tc.outputs['Object'], rad.inputs[0]); r = rad.outputs['Value']
    ang = _m(N, L, 'ARCTAN2', sx.outputs['Y'], sx.outputs['X'])
    wob = _m(N, L, 'MULTIPLY_ADD', _nz(N, L, tc.outputs['Object'], 0.35, 8), 5.0); wob.node.inputs[2].default_value = -2.5
    rw = _m(N, L, 'ADD', r, wob)
    # radial blast rays (engines + landing thrusters) - streaky, uneven
    cr = N.new('ShaderNodeCombineXYZ'); L.new(_m(N, L, 'MULTIPLY', ang, 7.0), cr.inputs['X']); L.new(_m(N, L, 'MULTIPLY', r, 0.12), cr.inputs['Y'])
    rays = _mr(N, L, _nz(N, L, cr.outputs[0], 1.6, 6, 0.6), 0.34, 0.6, 0.6, 1.0)
    burn = _m(N, L, 'MULTIPLY', _m(N, L, 'POWER', _mr(N, L, rw, 4.0, 15.5, 1.0, 0.0), 0.45), rays)
    core = _mr(N, L, r, 4.2, 7.0, 1.0, 0.0)         # near-black under the engine bells
    spots = []
    for a in ENG_A:                                   # hard scorch rings right under each bell
        p = N.new('ShaderNodeCombineXYZ'); p.inputs['X'].default_value = ENG_R * math.cos(a); p.inputs['Y'].default_value = ENG_R * math.sin(a)
        dv = N.new('ShaderNodeVectorMath'); dv.operation = 'DISTANCE'; L.new(tc.outputs['Object'], dv.inputs[0]); L.new(p.outputs[0], dv.inputs[1])
        spots.append(_mr(N, L, dv.outputs['Value'], 0.7, 1.9, 1.0, 0.0))
    for a in POD_ANG:                                 # landing-thruster plume footprints
        for s in (-1, 1):
            p = N.new('ShaderNodeCombineXYZ'); p.inputs['X'].default_value = (R + 2.6) * math.cos(a + s * 0.12); p.inputs['Y'].default_value = (R + 2.6) * math.sin(a + s * 0.12)
            dv = N.new('ShaderNodeVectorMath'); dv.operation = 'DISTANCE'; L.new(tc.outputs['Object'], dv.inputs[0]); L.new(p.outputs[0], dv.inputs[1])
            spots.append(_mr(N, L, dv.outputs['Value'], 0.8, 4.4, 1.0, 0.0))
    acc = core
    for s in spots: acc = _m(N, L, 'MAXIMUM', acc, s)
    sc = _m(N, L, 'MAXIMUM', _m(N, L, 'MULTIPLY', acc, _mr(N, L, _nz(N, L, tc.outputs['Object'], 3.0, 8), 0.3, 0.6, 0.8, 1.0)), _m(N, L, 'MULTIPLY', burn, 0.97), clamp=True)
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; L.new(sc, mx.inputs['Factor'])
    L.new(tile.outputs['Color'], mx.inputs[6]); mx.inputs[7].default_value = hexc('#0c0c0d')
    # heat tint ring just outside the core (glassy, slightly bluish sinter)
    tint = _m(N, L, 'MULTIPLY', _mr(N, L, rw, 5.0, 7.5, 0.0, 1.0), _mr(N, L, rw, 7.5, 11.0, 1.0, 0.0))
    mxt = N.new('ShaderNodeMix'); mxt.data_type = 'RGBA'; L.new(_m(N, L, 'MULTIPLY', tint, 0.35), mxt.inputs['Factor'])
    L.new(mx.outputs[2], mxt.inputs[6]); mxt.inputs[7].default_value = hexc('#3b4150')
    # dust drift: lighter grey regolith blown toward the rim
    dd = _mr(N, L, rw, 13.0, 18.0, 0.0, 0.9)
    dn = _mr(N, L, _nz(N, L, tc.outputs['Object'], 1.6, 10), 0.35, 0.6, 0.0, 1.4)
    mx2 = N.new('ShaderNodeMix'); mx2.data_type = 'RGBA'; L.new(_m(N, L, 'MULTIPLY', dd, dn, clamp=True), mx2.inputs['Factor'])
    L.new(mxt.outputs[2], mx2.inputs[6]); mx2.inputs[7].default_value = hexc('#8a8c8f')
    mx3 = N.new('ShaderNodeMix'); mx3.data_type = 'RGBA'; L.new(seam, mx3.inputs['Factor'])
    L.new(mx2.outputs[2], mx3.inputs[6]); mx3.inputs[7].default_value = hexc('#1d1e20')
    L.new(mx3.outputs[2], b.inputs['Base Color']); L.new(_mr(N, L, sc, 0.0, 1.0, 0.85, 0.6), b.inputs['Roughness'])
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.5; bump.inputs['Distance'].default_value = 0.02
    hb = _m(N, L, 'MULTIPLY_ADD', _nz(N, L, tc.outputs['Object'], 14, 12), 0.4); L.new(_m(N, L, 'SUBTRACT', 1.0, seam), hb.node.inputs[2])
    L.new(hb, bump.inputs['Height']); L.new(bump.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = hexc('#5d5f62'); return m

# ================================================================ helpers
def lathe(name, prof, loc, mat, segs=96, bevel=0.0, smooth=True, angle=50, c='Mine'):
    bm = bmesh.new(); rings = []
    for (r, z) in prof:
        if r < 1e-5: rings.append([bm.verts.new((loc[0], loc[1], loc[2] + z))])
        else: rings.append([bm.verts.new((loc[0] + r * math.cos(TAU * k / segs), loc[1] + r * math.sin(TAU * k / segs), loc[2] + z)) for k in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for k in range(segs):
            k2 = (k + 1) % segs
            if len(a) == 1: bm.faces.new((a[0], b[k], b[k2]))
            elif len(b) == 1: bm.faces.new((a[k], a[k2], b[0]))
            else: bm.faces.new((a[k], a[k2], b[k2], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(bm, name, mat, c, smooth=smooth, bevel=bevel, angle=angle)

def ring(name, r, z, h, mat, w=0.04, segs=128, loc=(0, 0)):
    return lathe(name, [(r - w, z - h / 2), (r, z - h / 2), (r, z + h / 2), (r - w, z + h / 2), (r - w, z - h / 2)], (loc[0], loc[1], 0), mat, segs=segs)

def arc_panel(name, r, a0, a1, z0, z1, t, mat, segs=None, bevel=0.01):
    """curved solid hull panel from angle a0..a1 (rad), height z0..z1, thickness t outward from r."""
    segs = segs or max(4, int(abs(a1 - a0) / TAU * 128))
    bm = bmesh.new(); vs = []
    for i in range(segs + 1):
        a = a0 + (a1 - a0) * i / segs; ca, sa = math.cos(a), math.sin(a)
        vs.append([bm.verts.new((rad * ca, rad * sa, z)) for rad, z in ((r, z0), (r + t, z0), (r + t, z1), (r, z1))])
    for i in range(segs):
        for k in range(4):
            k2 = (k + 1) % 4; bm.faces.new((vs[i][k], vs[i + 1][k], vs[i + 1][k2], vs[i][k2]))
    bm.faces.new(list(reversed(vs[0]))); bm.faces.new(vs[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(bm, name, mat, bevel=bevel, segs=2, angle=60)

def polar(a, r, z): return Vector((r * math.cos(a), r * math.sin(a), z))
def radial_rot(a): return (math.pi / 2, 0, a + math.pi / 2)   # local +Z -> outward radial
def on_hull(name, size, a, z, mat, r=R, lift=0.0, bevel=0.02, segs=2):
    """box whose local Z points radially outward; size=(tangent, height, radial)."""
    p = polar(a, r + size[2] / 2 + lift, z)
    ob = box(name, (size[0], size[2], size[1]), p, mat, rot=(0, 0, a + math.pi / 2), bevel=bevel, segs=segs)
    return ob

def hull_bolts(a, z, w, h, nx=3, ny=3, inset=0.06, lift=0.035):
    for i in range(nx):
        for j in range(ny):
            if 0 < i < nx - 1 and 0 < j < ny - 1: continue
            dx = -w / 2 + inset + (w - 2 * inset) * i / (nx - 1); dz = -h / 2 + inset + (h - 2 * inset) * j / (ny - 1)
            sphere('Bolt', 0.022, tuple(polar(a + dx / R, R + lift, z + dz)), SATIN, sub=1)
def frame(name, a, z, w, h, t=0.07, depth=0.05, mat=None):
    mat = mat or STEELD
    on_hull(name, (w + t, t, depth), a, z + h / 2 + t / 2, mat, bevel=0.01)
    on_hull(name, (w + t, t, depth), a, z - h / 2 - t / 2, mat, bevel=0.01)
    on_hull(name, (t, h, depth), a + (w / 2 + t / 2) / R, z, mat, bevel=0.01)
    on_hull(name, (t, h, depth), a - (w / 2 + t / 2) / R, z, mat, bevel=0.01)

def apply_mods(ob):
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data; ob.modifiers.clear(); ob.data = me; bpy.data.meshes.remove(old)

def cut(ob, cutters, solidify=None):
    if solidify:
        s = ob.modifiers.new('Solid', 'SOLIDIFY'); s.thickness = solidify; s.offset = -1; s.use_even_offset = True
        apply_mods(ob)
    for c in cutters:
        md = ob.modifiers.new('Cut', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = c; md.solver = 'EXACT'
    apply_mods(ob)
    for p in ob.data.polygons: p.use_smooth = True

def light(name, kind, loc, energy, color='#ffc98a', size=0.2, rot=None, spot=None):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = hexc(color)[:3]
    if kind == 'AREA': ld.size = size
    elif kind in ('POINT', 'SPOT'): ld.shadow_soft_size = size
    if spot: ld.spot_size = spot; ld.spot_blend = 0.4
    ob = bpy.data.objects.new(name, ld); coll('Stage').objects.link(ob); ob.location = loc
    if rot: ob.rotation_euler = rot
    return ob

def aim(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()

CUTTERS = []
def cutter(o): o.hide_render = True; CUTTERS.append(o); return o

FRONT = -math.pi / 2
HULL_T = 0.12      # thick shielded hull wall
# ================================================================ HULL
# aft skirt (graphite, slightly flared) + aft dome + recessed engines
lathe('AftSkirt', [(R + 0.18, Z_AFT), (R + 0.18, Z_AFT + 0.35), (R + 0.05, Z_AFT + 0.6), (R + 0.05, Z_BODY), (R - 0.2, Z_BODY), (R - 0.2, Z_AFT + 0.05), (R - 0.05, Z_AFT)],
      (0, 0, 0), GRAPH, segs=128, smooth=True, angle=30)
lathe('AftDome', [(0, Z_AFT + 0.55), (1.8, Z_AFT + 0.6), (3.0, Z_AFT + 0.8), (R - 0.15, Z_AFT + 1.0)], (0, 0, 0), STEELD, segs=96)
ring('AftSkirtLip', R + 0.2, Z_AFT + 0.15, 0.16, STEELD, w=0.08, segs=128)
# 4 main engines: big bells hanging BELOW the skirt between the legs (exit plane ~0.9 m above the pad)
BELL_PROF = [(0.84, 0.9), (0.76, 1.35), (0.6, 1.9), (0.44, 2.4), (0.33, 2.78), (0.28, 2.78), (0.39, 2.4), (0.55, 1.9), (0.71, 1.35), (0.79, 0.93)]
for a in ENG_A:
    x, y = ENG_R * math.cos(a), ENG_R * math.sin(a)
    lathe('EngineBell', BELL_PROF, (x, y, 0), BELL, segs=56, angle=70)
    ring('EngineBellLip', 0.86, 0.93, 0.07, STEELD, w=0.04, segs=56, loc=(x, y))
    for zz in (1.5, 2.1):
        ring('EngineBellBand', 0.73 if zz < 2 else 0.53, zz, 0.05, STEELD, w=0.03, segs=56, loc=(x, y))
    cyl('EngineGimbal', 0.44, 0.5, (x, y, 3.0), STEELD, segs=24, bevel=0.03)
    lathe('EngineThroat', [(0, 2.7), (0.3, 2.72), (0.3, 2.8), (0, 2.8)], (x, y, 0), INK, segs=24)
    for q in range(3):   # gimbal actuators
        b = a + TAU * q / 3; d = Vector((math.cos(b), math.sin(b), 0))
        piston('EngineActuator', (x + d.x * 0.9, y + d.y * 0.9, 3.15), (x + d.x * 0.5, y + d.y * 0.5, 2.25), 0.045, GRAPH_S, SATIN, ext=0.5)

# main hull: thick white shielded skin over the steel tank structure.
# Vertical layout (bottom -> top): FUEL TANK section (3.4-11.8 m: LOX + CH4 tanks, common-dome band, feed plumbing,
# Tank Farm umbilical QD) | CARGO BAY (12-19 m: big drop-down cargo door + davit hoist) | CREW DECK (19.5-24.3 m:
# 4 sleep pods behind small ports + crew airlock with dust-off station, caged ladder down to the pad).
hull = lathe('Hull', [(R, Z_BODY), (R, Z_NOSE)], (0, 0, 0), WHITE, segs=192, angle=80)
AL_A = math.radians(275)     # crew airlock + ladder
CB_A = math.radians(215)     # cargo bay door + hoist
POD_C = math.radians(215)    # sleep-pod ports (directly above the cargo door, clear of the airlock chamber)
UA = math.radians(165)       # fuel umbilical (Tank Farm connection) at the tank section
def spin_new(before, ang):
    """rotate every top-level object created since `before` about the ship axis (blocks are modelled facing -Y)."""
    bpy.context.view_layer.update(); Rz = Matrix.Rotation(ang, 4, 'Z')
    for ob in list(bpy.data.objects):
        if ob.name not in before and ob.parent is None: ob.matrix_world = Rz @ ob.matrix_world
    bpy.context.view_layer.update()
def snap(): return set(o.name for o in bpy.data.objects)
DOOR_W, DOOR_Z0, DOOR_Z1 = 1.5, 20.45, 22.75
CB_W, CB_Z0, CB_Z1 = 3.4, 12.4, 17.2
_b = snap()
cutter(box('cut_door', (DOOR_W, 2.4, DOOR_Z1 - DOOR_Z0), (0, -R, (DOOR_Z0 + DOOR_Z1) / 2), INK, bevel=0.0))
spin_new(_b, AL_A - FRONT); _b = snap()
cutter(box('cut_cargo', (CB_W, 2.4, CB_Z1 - CB_Z0), (0, -R, (CB_Z0 + CB_Z1) / 2), INK, bevel=0.0))
spin_new(_b, CB_A - FRONT)
# crew deck: 4 sleep pods (2 columns x 2 rows), each behind its own small recessed, shuttered port
POD_A = [POD_C - 0.3, POD_C + 0.3]
POD_Z = [21.05, 22.25]
PORT_R = 0.24
PORTS = [(a, z - 0.1) for a in POD_A for z in POD_Z]   # ports sit just above mattress height
for (a, z) in PORTS:   # splayed reveal: 0.24 m at the skin, ~0.42 m at the pod face
    cutter(cyl('cut_port', 0.72, 1.2, polar(a, R - 0.2, z), INK, rot=radial_rot(a), segs=40, bevel=0.0, r2=0.01))
band = arc_panel('CrewBandPanel', R, POD_C - 0.55, POD_C + 0.55, 20.2, 23.3, 0.04, WHITE_P)
door_surround = arc_panel('DoorSurround', R, AL_A - 0.27, AL_A + 0.27, 20.25, 23.25, 0.05, GRAPH_P)
cargo_surround = arc_panel('CargoDoorSurround', R, CB_A - 0.55, CB_A + 0.55, 12.15, 17.5, 0.05, GRAPH_P)
cut(hull, CUTTERS, solidify=HULL_T)
cut(band, CUTTERS); cut(door_surround, CUTTERS); cut(cargo_surround, CUTTERS)
# exposed stainless structural bands + glow rings
for z0, z1 in ((3.4, 3.95), (7.55, 7.9), (11.0, 11.8), (18.9, 19.4), (24.4, 25.1), (30.4, 31.0)):   # tank skirt | common dome | tank top | bay/deck | deck top | nose
    arc_panel('SteelBand', R, 0, TAU, z0, z1, 0.03, STEEL, segs=192)
ring('SkirtGlow', R + 0.08, Z_BODY + 0.06, 0.06, CYAN, w=0.02, segs=192)
ring('DeckGlow', R + 0.06, 11.4, 0.06, CYAN, w=0.02, segs=192)
ring('BayGlow', R + 0.06, 19.15, 0.05, CYANS, w=0.02, segs=192)
ring('UpperGlow', R + 0.06, 24.75, 0.05, CYANS, w=0.02, segs=192)
# graphite body-mounted radiator tiles on the back half
arc_panel('RadiatorTiles', R, 0.35, math.pi - 0.35, 12.4, 23.8, 0.05, GRAPH_P)
arc_panel('AftTilesBack', R, 0.5, math.pi - 0.5, 4.1, 6.9, 0.04, GRAPH_P)
for z in (5.0, 6.9, 9.4, 18.45, 27.0, 29.0):   # (none across the cargo door / airlock openings)
    ring('WeldRing', R + 0.015, z, 0.04, STEEL_P, w=0.03, segs=192)
# raceways (vertical cable trays)
for a in (0.0, math.pi):
    for z0, z1 in ((4.0, 10.9), (11.9, 24.3), (25.2, 30.3)):
        on_hull('Raceway', (0.42, z1 - z0, 0.18), a, (z0 + z1) / 2, STEELD, bevel=0.04)
        on_hull('RacewayCap', (0.46, 0.1, 0.21), a, z1 - 0.06, GRAPH_S, bevel=0.01)
        for z in [z0 + 0.8 * i for i in range(1, int((z1 - z0) / 0.8))]:
            on_hull('RacewayClamp', (0.48, 0.06, 0.205), a, z, SATIN, bevel=0.008)
# deployable radiator wings on the back (stand-off panels on brackets, edge-on to the sun)
for a in (math.radians(62), math.radians(118)):
    n = Vector((math.cos(a), math.sin(a), 0)); t = Vector((-n.y, n.x, 0))
    for z in (13.6, 17.4, 21.2):
        rod('RadBracket', tuple(polar(a, R + 0.02, z)), tuple(polar(a, R + 0.7, z)), 0.06, STEELD, segs=10)
    c = polar(a, R + 0.75, 17.4)
    ob = box('RadiatorWing', (0.1, 2.4, 9.0), tuple(c), WHITE_S, rot=(0, 0, a), bevel=0.03)
    for i in range(7):
        box('RadiatorTube', (0.12, 0.04, 8.6), tuple(c + t * (-1.0 + i * 0.333)), GRAPH_S, rot=(0, 0, a), bevel=0.0)
    box('RadiatorHeader', (0.16, 2.44, 0.12), tuple(c + Vector((0, 0, 4.4))), GRAPH_S, rot=(0, 0, a), bevel=0.02)
    box('RadiatorHeader', (0.16, 2.44, 0.12), tuple(c + Vector((0, 0, -4.4))), GRAPH_S, rot=(0, 0, a), bevel=0.02)
    box('RadiatorGlow', (0.13, 0.03, 8.0), tuple(c + t * 1.21), CYANS, rot=(0, 0, a), bevel=0.0)
# solar band near the top
arc_panel('SolarBand', R, 0, TAU, 28.0, 29.5, 0.035, SOLAR, segs=192, bevel=0.003)
for k in range(40):
    on_hull('SolarMullion', (0.03, 1.5, 0.045), TAU * k / 40, 28.75, SATIN, bevel=0.0)
ring('SolarGlowLo', R + 0.05, 27.97, 0.05, CYAN, w=0.02, segs=192)
# nose (ogive) white with stainless cap
prof = []
for i in range(23):
    t = i / 22; z = Z_NOSE + t * (Z_TIP - 0.8 - Z_NOSE)
    prof.append((max(0.05, R * math.sqrt(max(0.0, 1 - t ** 1.6 * 0.93))), z))
lathe('Nose', prof + [(0, Z_TIP - 0.8)], (0, 0, 0), WHITE, segs=160, angle=60)
lathe('NoseCap', [(1.12, Z_TIP - 1.1), (0.95, Z_TIP - 0.55), (0.6, Z_TIP - 0.18), (0, Z_TIP - 0.05)], (0, 0, 0), STEEL_P, segs=64)
ring('NoseCapGlow', 1.13, Z_TIP - 1.08, 0.05, CYAN, w=0.02, segs=64)
sphere('NoseBeacon', 0.08, (0, 0, Z_TIP - 0.02), CYAN, sub=2)

# landing thrusters high on the body (plume stays off the regolith)
for k in range(4):
    a = TAU * k / 4 + math.pi / 4
    on_hull('LandingPod', (1.4, 2.6, 0.8), a, 26.2, WHITE_S, bevel=0.2, segs=4)
    on_hull('LandingPodBand', (1.44, 0.18, 0.84), a, 26.9, GRAPH_S, bevel=0.02)
    on_hull('LandingPodStrip', (0.05, 1.8, 0.85), a, 26.1, CYAN, bevel=0.0)
    for s in (-1, 1):
        p = polar(a + s * 0.1, R + 0.8, 25.0)
        lathe('LandingNozzle', [(0.0, 0.05), (0.18, 0.04), (0.28, -0.25), (0.38, -0.6), (0.34, -0.6), (0.24, -0.25), (0.14, 0.02)], (p.x, p.y, p.z), NOZ, segs=28)
        sphere('LandingNozzleHead', 0.18, (p.x, p.y, p.z + 0.14), STEELD, sub=2)

def rcs(a, z):
    on_hull('RCSBlock', (0.55, 0.55, 0.28), a, z, GRAPH_S, bevel=0.06, segs=3)
    base = polar(a, R + 0.28, z); t = Vector((-math.sin(a), math.cos(a), 0)); n = Vector((math.cos(a), math.sin(a), 0))
    for d in (t, -t, Vector((0, 0, 1)), Vector((0, 0, -1))):
        p0 = base + d * 0.2; rod('RCSNozzle', p0, p0 + d * 0.16, 0.045, NOZ, r2=0.08, segs=12)
    sphere('RCSLamp', 0.04, tuple(base + n * 0.02 + Vector((0, 0, 0.16))), CYAN, sub=1)
for k in range(4):
    a = TAU * k / 4 + 0.3
    rcs(a, 32.3); rcs(a + math.pi / 4, 5.2 if abs(((a + math.pi / 4) - FRONT + math.pi) % TAU - math.pi) > 0.7 else 9.9)

# antennas
DA = math.radians(150); rN = R * 0.88
on_hull('DishMount', (0.5, 0.6, 0.35), DA, 32.0, GRAPH_S, r=rN, bevel=0.06)
mp = polar(DA, rN + 0.35, 32.0); bp = polar(DA, rN + 1.5, 32.5)
rod('DishBoom', tuple(mp), tuple(bp), 0.06, SATIN)
dish = lathe('Dish', [(0, 0), (0.35, 0.05), (0.7, 0.2), (0.85, 0.3), (0.82, 0.33), (0.05, 0.07), (0, 0.07)], (0, 0, 0), WHITE_S, segs=48)
dish.location = bp; dish.rotation_euler = (0.9, 0, DA - math.pi / 2)
for a, z, L in ((math.radians(35), 34.0, 1.8), (math.radians(-140), 33.5, 1.4)):
    rz = R * math.sqrt(max(0.0, 1 - ((z - Z_NOSE) / (Z_TIP - 0.8 - Z_NOSE)) ** 1.6 * 0.93)) - 0.05
    p = polar(a, rz, z)
    rod('WhipAntenna', tuple(p), tuple(p + Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, L))), 0.015, SATIN, segs=8)
    sphere('WhipTip', 0.03, tuple(p + Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, L))), CYAN, sub=1)
for a in (math.radians(170), math.radians(-20)):
    on_hull('PhasedArray', (1.2, 1.6, 0.1), a, 14.5, GRAPH_S, bevel=0.02)
    on_hull('PhasedArrayFace', (1.1, 1.5, 0.11), a, 14.5, SOLAR, bevel=0.005)
    frame('PhasedArrayFrame', a, 14.5, 1.2, 1.6, t=0.06, depth=0.12, mat=STEELD); hull_bolts(a, 14.5, 1.3, 1.7, 3, 3, 0.03, 0.125)
for a in (0.0, math.pi):
    sphere('NavLamp', 0.07, tuple(polar(a + 0.12, R + 0.05, 11.4)), CYAN, sub=1)

# deliberate hull detail (no random squares): framed vent grilles, hinged access hatches, sensor window clusters
def vent(a, z, w=0.7, h=0.5):
    on_hull('VentBack', (w, h, 0.02), a, z, INK, bevel=0.0)
    for i in range(6):
        on_hull('VentSlat', (w - 0.04, 0.035, 0.05), a, z - h / 2 + 0.06 + i * (h - 0.12) / 5, STEELD, bevel=0.0)
    frame('VentFrame', a, z, w, h, t=0.06, depth=0.06); hull_bolts(a, z, w + 0.12, h + 0.12, 2, 2, 0.03, 0.065)
def hatch(a, z, w, h, hinge=-1):
    frame('HatchFrame', a, z, w, h, t=0.06, depth=0.045, mat=GRAPH_S)
    on_hull('AccessHatch', (w - 0.03, h - 0.03, 0.04), a, z, WHITE_S, bevel=0.015)
    for dz in (-h * 0.3, h * 0.3):
        p = polar(a + hinge * (w / 2 + 0.03) / R, R + 0.07, z + dz)
        cyl('HatchHinge', 0.035, 0.22, tuple(p), SATIN, segs=12, bevel=0.005)
    on_hull('HatchLatch', (0.06, 0.24, 0.06), a - hinge * (w / 2 - 0.12) / R, z, SATIN, lift=0.03, bevel=0.01)
    on_hull('HatchHazard', (w * 0.5, 0.06, 0.045), a, z + h / 2 - 0.12, AMBER_HZ, bevel=0.0)
    hull_bolts(a, z, w - 0.03, h - 0.03, 3, 3, 0.07, 0.045)
def sensors(a, z, n=3, step=0.36):
    w = step * n + 0.1
    on_hull('SensorBezel', (w, 0.36, 0.05), a, z, GRAPH_S, bevel=0.02)
    for i in range(n):
        da = (-step * (n - 1) / 2 + step * i) / R
        on_hull('SensorWindow', (0.22, 0.18, 0.055), a + da, z + 0.02, SENSOR, bevel=0.01)
        on_hull('SensorWindowRim', (0.26, 0.03, 0.058), a + da, z - 0.09, SATIN, bevel=0.0)
    sphere('SensorLamp', 0.03, tuple(polar(a + (w / 2 - 0.06) / R, R + 0.06, z + 0.13)), CYAN, sub=1)
    hull_bolts(a, z, w, 0.36, 2, 2, 0.04, 0.055)
for a, z in VENTS: vent(a, z)
for a, z, w, h, hg in ((math.radians(90), 5.5, 1.1, 1.4, -1), (math.radians(197), 6.1, 1.0, 1.2, 1),
                       (math.radians(300), 15.0, 1.0, 1.3, -1), (math.radians(315), 17.6, 1.0, 1.3, 1)):
    hatch(a, z, w, h, hg)
sensors(math.radians(300), 23.0); sensors(math.radians(170), 12.6, 2); sensors(math.radians(340), 12.6, 2)
# fuel-tank section: stencilled tank IDs + external feed / pressurisation plumbing with flanges and clamps
for z, lab in ((5.6, 'LOX'), (8.8, 'CH4')):
    a = math.radians(252)
    text('TankLabel', lab, tuple(polar(a, R + 0.015, z)), (math.pi / 2, 0, a + math.pi / 2), 0.42, INK, extrude=0.004)
for a, z0, z1, r_ in ((UA - 0.085, 5.25, 11.0, 0.075), (UA + 0.085, 5.25, 9.6, 0.06), (math.radians(224), 3.6, 11.0, 0.07), (math.radians(228), 3.6, 10.4, 0.055)):
    p0 = polar(a, R + 0.16, z0); p1 = polar(a, R + 0.16, z1)
    rod('TankFeedLine', tuple(p0), tuple(p1), r_, STEEL_P, segs=14)
    for z in [z0 + 0.15] + [z0 + 0.9 * i for i in range(1, int((z1 - z0) / 0.9))] + [z1 - 0.15]:
        on_hull('PipeClamp', (0.26, 0.07, 0.24), a, z, STEELD, bevel=0.01)
    for z in (z0 + (z1 - z0) * 0.33, z0 + (z1 - z0) * 0.7):
        rod('PipeFlange', tuple(polar(a, R + 0.16, z - 0.04)), tuple(polar(a, R + 0.16, z + 0.04)), r_ + 0.05, SATIN, segs=14)
    rod('PipeElbow', tuple(p1), tuple(polar(a, R + 0.02, z1)), r_, STEEL_P, segs=14)
on_hull('ValveManifold', (0.7, 0.8, 0.3), math.radians(226), 7.0, GRAPH_S, bevel=0.04)
on_hull('ValveManifoldGlow', (0.04, 0.6, 0.31), math.radians(226) + 0.06, 7.0, CYAN, bevel=0.0)

# ---------------------------------------------------------------- CREW AIRLOCK (crew deck level), modelled facing -Y then spun to AL_A
_b = snap()
dz = (DOOR_Z0 + DOOR_Z1) / 2
yf = -math.sqrt(R ** 2 - (DOOR_W / 2) ** 2)
for s in (-1, 1):
    box('DoorJamb', (0.16, 0.5, DOOR_Z1 - DOOR_Z0 + 0.16), (s * (DOOR_W / 2 + 0.08), yf - 0.06, dz), GRAPH_S, bevel=0.02)
    box('DoorJambGlow', (0.02, 0.03, DOOR_Z1 - DOOR_Z0 - 0.2), (s * (DOOR_W / 2 + 0.165), yf - 0.3, dz), CYAN, bevel=0.0)
    for j in range(7):   # air-knife nozzles in the outer jambs: blast dust off suits on the way in
        cyl('AirKnifeNozzle', 0.025, 0.06, (s * (DOOR_W / 2 + 0.005), yf - 0.22, DOOR_Z0 + 0.3 + j * 0.3), SATIN, rot=(0, math.pi / 2, 0), segs=10, bevel=0.0)
box('DoorHeader', (DOOR_W + 0.32, 0.6, 0.2), (0, yf - 0.06, DOOR_Z1 + 0.1), GRAPH_S, bevel=0.02)
box('DoorHeaderStripe', (DOOR_W + 0.1, 0.02, 0.1), (0, yf - 0.365, DOOR_Z1 + 0.1), AMBER_HZ, bevel=0.0)
box('DoorSill', (DOOR_W + 0.32, 0.6, 0.1), (0, yf - 0.06, DOOR_Z0 - 0.05), STEELD, bevel=0.01)
box('AirKnifeHeader', (DOOR_W - 0.1, 0.16, 0.1), (0, yf - 0.2, DOOR_Z1 - 0.06), SATIN, bevel=0.02)
# outer door leaf, slid aside on its track (open)
box('OuterDoorTrack', (DOOR_W * 2 + 0.4, 0.12, 0.08), (-DOOR_W * 0.5 - 0.1, yf - 0.42, DOOR_Z1 + 0.3), STEELD, bevel=0.01)
leaf_x = -(DOOR_W + 0.2)
box('OuterDoorLeaf', (DOOR_W + 0.06, 0.12, DOOR_Z1 - DOOR_Z0 + 0.06), (leaf_x, yf - 0.34, dz), WHITE_S, bevel=0.03)
box('OuterDoorWin', (0.32, 0.02, 0.32), (leaf_x, yf - 0.41, dz + 0.55), SENSOR, bevel=0.0)
box('OuterDoorHazard', (DOOR_W - 0.1, 0.02, 0.08), (leaf_x, yf - 0.41, DOOR_Z0 + 0.25), AMBER_HZ, bevel=0.0)
for s in (-1, 1):   # floods aimed down the ladder + onto the platform
    box('Floodlight', (0.34, 0.24, 0.2), (s * 0.62, yf - 0.55, DOOR_Z1 + 0.42), GRAPH_S, rot=(-0.9, 0, 0), bevel=0.03)
    box('FloodLens', (0.28, 0.02, 0.14), (s * 0.62, yf - 0.66, DOOR_Z1 + 0.33), LAMP, rot=(-0.9, 0, 0), bevel=0.0)
    rod('FloodArm', (s * 0.62, yf, DOOR_Z1 + 0.42), (s * 0.62, yf - 0.45, DOOR_Z1 + 0.42), 0.03, SATIN)
    sl = light('DoorFlood', 'SPOT', (s * 0.62, yf - 0.75, DOOR_Z1 + 0.3), 2500, '#f2f5ff', size=0.1, spot=math.radians(60))
    aim(sl, (s * 0.2, yf - 1.6, 0.0))
light('PlatformLight', 'POINT', (0, yf - 1.2, DOOR_Z1 + 0.2), 300, '#f2f5ff', size=0.2)
# airlock chamber with dust-off station (grated floor, air-shower arch, boot brushes, hand brush, suit lockers)
BX0, BX1, BY0, BY1, BZ0, BZ1 = -1.0, 1.0, yf - 0.1, yf + 2.4, DOOR_Z0 - 0.02, DOOR_Z1 + 0.3
BYc = (BY0 + BY1) / 2
box('BayFloorPit', (BX1 - BX0, BY1 - BY0, 0.06), (0, BYc, BZ0 - 0.1), INK, bevel=0.0)
for i in range(int((BY1 - BY0 - 0.2) / 0.09)):     # grated deck (dust falls through)
    box('BayGrate', (BX1 - BX0 - 0.1, 0.03, 0.05), (0, BY0 + 0.15 + i * 0.09, BZ0 - 0.025), STEELD, bevel=0.0)
for s in (-1, 1): box('BayGrateFrame', (0.08, BY1 - BY0, 0.08), (s * (BX1 - 0.04), BYc, BZ0 - 0.04), GRAPH_S, bevel=0.01)
box('BayCeil', (BX1 - BX0, BY1 - BY0, 0.06), (0, BYc, BZ1 + 0.03), CABIN, bevel=0.0)
box('BayBack', (BX1 - BX0, 0.06, BZ1 - BZ0 + 0.2), (0, BY1 + 0.03, (BZ0 + BZ1) / 2), CABIN, bevel=0.0)
AY = BY0 + 0.95
for s in (-1, 1):
    box('BayWall', (0.06, BY1 - BY0, BZ1 - BZ0 + 0.2), (s * (BX1 + 0.03), BYc, (BZ0 + BZ1) / 2), CABIN, bevel=0.0)
    box('BayFloorGlow', (0.03, BY1 - BY0 - 0.3, 0.01), (s * 0.85, BYc, BZ0 + 0.005), CYAN, bevel=0.0)
    box('AirShowerPillar', (0.2, 0.28, BZ1 - BZ0 - 0.2), (s * 0.84, AY, BZ0 + (BZ1 - BZ0 - 0.2) / 2), WHITE_S, bevel=0.04)
    for j in range(8):
        cyl('AirNozzle', 0.03, 0.08, (s * 0.72, AY, BZ0 + 0.35 + j * 0.26), SATIN, rot=(0, math.pi / 2, 0), segs=10, bevel=0.0)
    box('AirShowerGlow', (0.02, 0.04, BZ1 - BZ0 - 0.6), (s * 0.735, AY + 0.12, BZ0 + (BZ1 - BZ0 - 0.2) / 2), CYAN, bevel=0.0)
    box('BootBrush', (0.36, 0.5, 0.2), (s * 0.5, BY0 + 1.7, BZ0 + 0.1), GRAPH_S, bevel=0.03)
    box('BootBrushBristle', (0.3, 0.44, 0.1), (s * 0.5, BY0 + 1.7, BZ0 + 0.25), BRISTLE, bevel=0.02)
    box('BayLocker', (0.26, 0.6, 2.0), (s * 0.86, BY1 - 0.4, BZ0 + 1.0), CABIN_D, bevel=0.02)
    box('BayLockerGlow', (0.02, 0.5, 0.03), (s * 0.72, BY1 - 0.4, BZ0 + 1.8), CYAN, bevel=0.0)
box('AirShowerHeader', (1.88, 0.28, 0.2), (0, AY, BZ1 - 0.2), WHITE_S, bevel=0.04)
box('AirShowerHeaderGlow', (1.5, 0.02, 0.04), (0, AY - 0.15, BZ1 - 0.2), CYAN, bevel=0.0)
cyl('HoseReel', 0.18, 0.1, (0.82, BY0 + 1.45, BZ0 + 1.5), GRAPH_S, rot=(0, math.pi / 2, 0), segs=24, bevel=0.01)
cable('HandBrushHose', (0.76, BY0 + 1.45, BZ0 + 1.35), (0.55, BY0 + 1.7, BZ0 + 0.9), 0.02, INK, sag=0.25)
box('HandBrush', (0.08, 0.3, 0.08), (0.55, BY0 + 1.7, BZ0 + 0.86), BRISTLE, bevel=0.02)
box('BayCeilLight', (1.4, 0.8, 0.02), (0, BYc + 0.3, BZ1 - 0.01), WARM, bevel=0.0)
box('InnerHatch', (0.9, 0.05, 2.0), (0, BY1 - 0.01, BZ0 + 1.05), CABIN_D, bevel=0.03)
box('InnerHatchWin', (0.28, 0.06, 0.28), (0, BY1 - 0.02, BZ0 + 1.6), WARM, bevel=0.0)
box('InnerHatchLampOK', (0.08, 0.06, 0.08), (0.55, BY1 - 0.02, BZ0 + 1.9), M_glow('S_OkGreen', '#6ee08a', 10), bevel=0.0)
light('BayLight', 'AREA', (0, BYc + 0.3, BZ1 - 0.05), 200, '#ffd2a0', size=1.4)
light('BayFill', 'POINT', (0, BY0 + 0.6, BZ0 + 0.8), 30, '#7fe8ff', size=0.2)
spin_new(_b, AL_A - FRONT)


# ---------------------------------------------------------------- crew deck: 4 sleep pods behind the ports
POD_L, POD_H, POD_D = 1.95, 1.02, 0.95
for a in POD_A:
    for z in POD_Z:
        piv = bpy.data.objects.new('SleepPod', None); coll('Mine').objects.link(piv)
        piv.location = polar(a, R - 0.3, z); piv.rotation_euler = (0, 0, a + math.pi / 2)   # local -Y = outward
        def pb(name, size, loc, mat, bev=0.0):
            o = box(name, size, loc, mat, bevel=bev); o.parent = piv; return o
        pb('PodBack', (POD_L, 0.05, POD_H), (0, POD_D, 0), CABIN_W)
        pb('PodTop', (POD_L, POD_D, 0.05), (0, POD_D / 2, POD_H / 2), CABIN_W)
        pb('PodBottom', (POD_L, POD_D, 0.05), (0, POD_D / 2, -POD_H / 2), CABIN_D)
        for s in (-1, 1): pb('PodEnd', (0.05, POD_D, POD_H), (s * POD_L / 2, POD_D / 2, 0), CABIN_W)
        pb('PodFront', (POD_L + 0.05, 0.05, POD_H + 0.05), (0, 0.0, 0), CABIN_D)
        pb('Mattress', (POD_L - 0.1, POD_D - 0.12, 0.26), (0, POD_D / 2 + 0.02, -POD_H / 2 + 0.16), FABRIC, 0.05)
        pb('SleepingBag', (POD_L * 0.62, POD_D - 0.3, 0.2), (-0.25, POD_D / 2 + 0.04, -POD_H / 2 + 0.36), BLANKET, 0.08)
        pb('Pillow', (0.42, POD_D - 0.35, 0.14), (POD_L / 2 - 0.32, POD_D / 2 + 0.05, -POD_H / 2 + 0.36), PILLOW, 0.06)
        pb('PodLamp', (0.22, 0.06, 0.05), (POD_L / 2 - 0.35, POD_D - 0.05, POD_H / 2 - 0.12), WARM)
        pb('PodAccent', (POD_L - 0.2, 0.02, 0.02), (0, POD_D - 0.03, -POD_H / 2 + 0.5), CYAN)
        pb('PodShelf', (0.6, 0.18, 0.03), (-0.45, POD_D - 0.1, 0.15), CABIN_D, 0.01)
        pb('PodScreen', (0.32, 0.02, 0.2), (0.25, POD_D - 0.04, 0.12), CYANS)
        bpy.context.view_layer.update()
        lt = light('PodLight', 'POINT', (0, 0, 0), 45, '#ffb877', size=0.15)
        lt.location = piv.matrix_world @ Vector((0.2, POD_D * 0.55, 0.25))
bpy.context.view_layer.update()
for ob in [o for o in coll('Mine').objects if o.name.startswith('PodFront')]:
    mw = ob.matrix_world.copy(); ob.parent = None; ob.data.transform(mw); ob.matrix_world = Matrix.Identity(4)
    cut(ob, CUTTERS)
# recessed port hoods, half-closed sun shutters, glass set deep in the wall
for (a, z) in PORTS:
    ro = radial_rot(a); t = Vector((-math.sin(a), math.cos(a), 0))
    hood = lathe('PortHood', [(PORT_R - 0.01, -0.05), (PORT_R + 0.14, -0.05), (PORT_R + 0.14, 0.04), (PORT_R + 0.06, 0.18), (PORT_R - 0.01, 0.18), (PORT_R - 0.01, -0.05)], (0, 0, 0), GRAPH_S, segs=48)
    hood.location = polar(a, R + 0.02, z); hood.rotation_euler = ro
    gl = ring('PortGlow', PORT_R + 0.155, 0.0, 0.03, CYAN, w=0.015, segs=48); gl.location = polar(a, R + 0.06, z); gl.rotation_euler = ro
    rv = lathe('PortReveal', [(0.42, -0.30), (PORT_R + 0.01, -0.02)], (0, 0, 0), CABIN, segs=40); rv.location = polar(a, R, z); rv.rotation_euler = ro
    g = cyl('PortGlass', PORT_R + 0.02, 0.015, polar(a, R - 0.1, z), GLASS, rot=ro, segs=40, bevel=0.0); g.visible_shadow = False
    # shutter: rails either side + plate slid up (open), so it would cover the port in full sun
    for s in (-1, 1):
        on_hull('ShutterRail', (0.05, 1.05, 0.22), a + s * (PORT_R + 0.2) / R, z + 0.28, STEELD, bevel=0.01)
    on_hull('Shutter', (0.62, 0.5, 0.05), a, z + 0.58, GRAPH_S, lift=0.19, bevel=0.015)
    on_hull('ShutterLip', (0.62, 0.04, 0.07), a, z + 0.34, AMBER_HZ, lift=0.18, bevel=0.0)
for c in CUTTERS: bpy.data.objects.remove(c)

# ---------------------------------------------------------------- landing legs (6, clear of the ladder, hoist drop zone and umbilical)
LEG_A = [math.radians(d) for d in (0, 60, 120, 180, 240, 300)]
FOOT_R = 8.2
for k, a in enumerate(LEG_A):
    n = Vector((math.cos(a), math.sin(a), 0)); t = Vector((-n.y, n.x, 0))
    foot = n * FOOT_R + Vector((0, 0, 0.5))
    hip = n * (R + 0.25) + Vector((0, 0, 7.4))
    on_hull('LegFairing', (1.0, 1.9, 0.4), a, 7.25, WHITE_S, bevel=0.12, segs=3)
    on_hull('LegFairingGlow', (0.05, 1.3, 0.41), a, 7.2, CYAN, bevel=0.0)
    piston('LegStrut', tuple(hip), tuple(foot), 0.22, GRAPH_S, SATIN, ext=0.58)
    on_hull('LegKnuckle', (0.7, 0.55, 0.4), a, 2.9, STEELD, bevel=0.06)
    for s in (-1, 1):
        p0 = n * (R + 0.35) + t * (s * 0.4) + Vector((0, 0, 2.9))
        rod('LegBrace', tuple(p0), tuple(foot + Vector((0, 0, 0.02))), 0.09, STEELD, segs=12)
    lathe('LegPad', [(0, 0.0), (1.0, 0.0), (1.05, 0.07), (0.97, 0.16), (0.45, 0.34), (0.2, 0.42), (0, 0.42)], (foot.x, foot.y, 0), STEELD, segs=48)
    ring('LegPadRim', 1.06, 0.05, 0.07, AMBER_HZ, w=0.04, segs=48, loc=(foot.x, foot.y))
    sphere('LegPadBall', 0.24, tuple(foot), SATIN, sub=2)
    cable('LegHose', tuple(hip + Vector((0, 0, -0.4)) + t * 0.26), tuple(foot + Vector((0, 0, 0.7)) + t * 0.26), 0.025, GRAPH_S, sag=0.35)

# ---------------------------------------------------------------- CREW LADDER: ship-mounted caged ladder, airlock platform -> pad
# (temporary access until the Launch Pad adds its elevator + prep area). Modelled facing -Y, then spun to AL_A.
_b = snap()
LY = -(R + 0.32)                 # rung plane (rails stand off the skin on brackets)
LW = 0.25                        # half-width between rails
HC = LY - 0.38; HR = 0.4         # safety-cage hoop centre / radius
TOP = DOOR_Z0 - 0.02             # airlock platform deck
REST = [10.2]                    # rest platform(s): ~10 m spacing (pad -> 10.2 -> 20.4)
def caged(z): return z > 2.4 and not any(p + 0.05 < z < p + 2.25 for p in REST)
for s in (-1, 1):
    box('LadderRail', (0.065, 0.065, TOP + 1.1), (s * LW, LY, (TOP + 1.1) / 2), SATIN, bevel=0.01)
    for z in [0.9 + 1.8 * i for i in range(int(TOP / 1.8) + 1)]:
        box('LadderBracket', (0.05, 0.36, 0.05), (s * LW, LY + 0.17, z), STEELD, bevel=0.005)
for i in range(1, int(TOP / 0.3) + 1):
    z = 0.3 * i
    if z > TOP - 0.05: break
    rod('LadderRung', (-LW, LY, z), (LW, LY, z), 0.017, SATIN, segs=8)
box('LadderFootPlate', (1.2, 1.0, 0.04), (0, LY - 0.35, 0.02), AMBER_HZ, bevel=0.008)
for z in [2.4 + 0.9 * i for i in range(int((TOP + 1.0 - 2.4) / 0.9) + 1)]:
    if caged(z): ring('LadderHoop', HR, z, 0.05, STEELD, w=0.025, segs=36, loc=(0, HC))
for th in (205, 240, 270, 300, 335):    # vertical cage bars (outer side only), split at the rest-platform openings
    x, y = HR * math.cos(math.radians(th)), HC + HR * math.sin(math.radians(th))
    segs_ = [(2.4, REST[0] + 0.05), (REST[0] + 2.25, TOP + 1.0)]
    for z0, z1 in segs_:
        rod('LadderCageBar', (x, y, z0), (x, y, z1), 0.018, STEELD, segs=6)
def platform(name, x0, x1, y0, y1, z, rails_on=('x0', 'x1', 'y1'), deck=True):
    """grated platform (top at z) with toe boards + 2-rail guard rails + diagonal struts back to the skin."""
    if deck: box(name + 'Deck', (x1 - x0, y0 - y1, 0.06), ((x0 + x1) / 2, (y0 + y1) / 2, z - 0.03), STEELD, bevel=0.005)
    for i in range(int((y0 - y1) / 0.12) if deck else 0):
        box(name + 'Grate', (x1 - x0 - 0.04, 0.025, 0.03), ((x0 + x1) / 2, y0 - 0.06 - i * 0.12, z + 0.002), GRAPH_S, bevel=0.0)
    box(name + 'Frame', (x1 - x0, 0.08, 0.14), ((x0 + x1) / 2, y1, z - 0.04), GRAPH_S, bevel=0.01)
    edges = {'x0': ((x0, y0), (x0, y1)), 'x1': ((x1, y0), (x1, y1)), 'y1': ((x0, y1), (x1, y1))}
    for e in rails_on:
        (ax, ay), (bx, by) = edges[e]
        n_ = max(2, int(math.hypot(bx - ax, by - ay) / 0.7) + 1)
        for k in range(n_):
            t_ = k / (n_ - 1); px, py = ax + (bx - ax) * t_, ay + (by - ay) * t_
            rod(name + 'Post', (px, py, z), (px, py, z + 1.07), 0.025, SATIN, segs=8)
        for hz in (0.55, 1.07):
            rod(name + 'Rail', (ax, ay, z + hz), (bx, by, z + hz), 0.024, AMBER_HZ if hz > 1 else SATIN, segs=8)
        box(name + 'Toe', (abs(bx - ax) + 0.03 or 0.03, abs(by - ay) + 0.03 or 0.03, 0.12), ((ax + bx) / 2, (ay + by) / 2, z + 0.06), GRAPH_S, bevel=0.0)
    for x_ in (x0 + 0.15, x1 - 0.15):
        hy = -math.sqrt(max(0.0, R ** 2 - x_ ** 2))
        rod(name + 'Strut', (x_, y1 + 0.1, z - 0.06), (x_, hy - 0.02, z - 1.1), 0.04, STEELD, segs=8)
        box(name + 'StrutShoe', (0.16, 0.06, 0.2), (x_, hy - 0.02, z - 1.1), STEELD, bevel=0.01)
# rest platform: side-step landing beside the ladder (cage opens toward it)
for p in REST:
    platform('RestPlatform', -1.75, -LW - 0.1, -(R + 0.12), LY - 1.0, p, rails_on=('x0', 'y1'))
    sphere('RestLamp', 0.05, (-LW - 0.12, LY - 0.06, p + 1.2), LAMP, sub=1)
# airlock platform: floor opening where the ladder comes up through it, dust-off boot scraper + brush by the door
yI, yO = -(R + 0.02), LY - 1.25
box('TopDeckL', (1.15 - LW - 0.12, yI - yO, 0.06), (-(1.15 + LW + 0.12) / 2, (yI + yO) / 2, TOP - 0.03), STEELD, bevel=0.005)
box('TopDeckR', (1.15 - LW - 0.12, yI - yO, 0.06), ((1.15 + LW + 0.12) / 2, (yI + yO) / 2, TOP - 0.03), STEELD, bevel=0.005)
box('TopDeckIn', (2 * (LW + 0.12), yI - (LY + 0.2), 0.06), (0, (yI + LY + 0.2) / 2, TOP - 0.03), STEELD, bevel=0.005)
box('TopDeckOut', (2 * (LW + 0.12), (HC - HR - 0.05) - yO, 0.06), (0, (HC - HR - 0.05 + yO) / 2, TOP - 0.03), STEELD, bevel=0.005)
platform('TopPlatform', -1.15, 1.15, yI, yO, TOP + 0.0005, deck=False)
for s in (-1, 1):
    box('BootScraper', (0.5, 0.36, 0.08), (s * 0.72, yI - 0.35, TOP + 0.04), GRAPH, bevel=0.01)
    box('BootScraperBristle', (0.44, 0.3, 0.07), (s * 0.72, yI - 0.35, TOP + 0.1), BRISTLE, bevel=0.01)
box('TopHatchStripe', (2 * (LW + 0.12), 0.06, 0.01), (0, LY + 0.2, TOP + 0.006), AMBER_HZ, bevel=0.0)
for s in (-1, 1):   # grab-rail hoop over the ladder exit
    rod('LadderGrab', (s * LW, LY, TOP + 1.1), (s * LW, LY - 0.3, TOP + 1.25), 0.03, SATIN, segs=8)
rod('LadderGrabTop', (-LW, LY - 0.3, TOP + 1.25), (LW, LY - 0.3, TOP + 1.25), 0.03, SATIN, segs=8)
spin_new(_b, AL_A - FRONT)


# ---------------------------------------------------------------- kit crates (human scale): on the pad under the hoist, in the bay, on the hook
def crate(name, label, loc, rotz, size=(1.8, 1.2, 1.2)):
    root = bpy.data.objects.new(name, None); coll('Mine').objects.link(root); root.location = loc; root.rotation_euler = (0, 0, rotz)
    sx, sy, sz = size
    P = [box(name + '_Body', (sx, sy, sz - 0.08), (0, 0, sz / 2 + 0.04), WHITE_S, bevel=0.05, segs=3)]
    for s in (-1, 1):
        P.append(box(name + '_Band', (0.14, sy + 0.04, sz - 0.06), (s * (sx / 2 - 0.2), 0, sz / 2 + 0.03), GRAPH_S, bevel=0.02))
        P.append(box(name + '_Skid', (sx + 0.04, 0.14, 0.08), (0, s * (sy / 2 - 0.14), 0.04), GRAPH, bevel=0.015))
        P.append(box(name + '_Handle', (0.04, 0.34, 0.06), (s * (sx / 2 + 0.03), 0, sz * 0.65), SATIN, bevel=0.01))
    P.append(box(name + '_Lid', (sx + 0.03, sy + 0.03, 0.07), (0, 0, sz - 0.035), GRAPH_S, bevel=0.02))
    P.append(box(name + '_Glow', (sx - 0.6, 0.02, 0.03), (0, -sy / 2 - 0.005, sz - 0.16), CYAN, bevel=0.0))
    P.append(box(name + '_Plate', (sx - 0.6, 0.01, 0.4), (0, -sy / 2 - 0.004, sz * 0.5), GRAPH_S, bevel=0.0))
    P.append(text(name + '_Label', label, (0, -sy / 2 - 0.012, sz * 0.5), (math.pi / 2, 0, 0), 0.3 if len(label) < 6 else 0.2, CYANS, extrude=0.003))
    P.append(box(name + '_Hazard', (sx - 0.6, 0.01, 0.08), (0, -sy / 2 - 0.004, 0.24), AMBER_HZ, bevel=0.0))
    for p in P: p.parent = root
    return root

# ---------------------------------------------------------------- CARGO BAY (mid section): drop-down cargo door, partly open, + davit hoist
# modelled facing -Y, then spun to CB_A
_b = snap()
crate('CrateMine', 'MINE', (-1.7, -10.2, 0.0), 0.28)
crate('CrateSpares', 'SPARES', (-3.5, -9.3, 0.0), 0.55, size=(1.4, 1.1, 1.0))
yc = -math.sqrt(R ** 2 - (CB_W / 2) ** 2)
czc = (CB_Z0 + CB_Z1) / 2
# interior: lit bay with deck, racks, tie-down rails, stowed crates
box('CargoFloor', (CB_W + 0.4, 3.0, 0.12), (0, yc + 1.5, CB_Z0 - 0.06), FLOOR, bevel=0.0)
box('CargoBack', (CB_W + 0.4, 0.1, CB_Z1 - CB_Z0 + 0.3), (0, yc + 3.0, czc), CABIN, bevel=0.0)
box('CargoCeil', (CB_W + 0.4, 3.0, 0.1), (0, yc + 1.5, CB_Z1 + 0.1), CABIN, bevel=0.0)
for s in (-1, 1):
    box('CargoWall', (0.1, 3.0, CB_Z1 - CB_Z0 + 0.3), (s * (CB_W / 2 + 0.2), yc + 1.5, czc), CABIN, bevel=0.0)
    box('CargoRack', (0.5, 2.6, 0.06), (s * (CB_W / 2 - 0.15), yc + 1.6, CB_Z0 + 1.9), GRAPH_S, bevel=0.01)
    for yy in (yc + 0.5, yc + 2.7):
        box('CargoRackPost', (0.06, 0.06, CB_Z1 - CB_Z0), (s * (CB_W / 2 - 0.15), yy, czc), STEELD, bevel=0.0)
    box('CargoTieRail', (0.08, 2.8, 0.04), (s * 0.9, yc + 1.5, CB_Z0 + 0.02), SATIN, bevel=0.0)
    box('CargoWallGlow', (0.02, 2.6, 0.04), (s * (CB_W / 2 + 0.14), yc + 1.5, CB_Z1 - 0.3), CYAN, bevel=0.0)
box('CargoCeilLight', (CB_W - 0.6, 1.2, 0.02), (0, yc + 1.6, CB_Z1 + 0.04), WARM, bevel=0.0)
light('CargoLight', 'AREA', (0, yc + 1.6, CB_Z1 - 0.05), 450, '#ffd9b0', size=2.4)
crate('CrateStowA', 'SPARES', (0.5, yc + 2.0, CB_Z0), 0.0, size=(1.4, 1.1, 1.0))
crate('CrateStowB', 'HAB', (-0.9, yc + 2.1, CB_Z0), 0.0, size=(1.2, 1.0, 0.9))
# door frame: graphite jambs + header with hazard stripe, sill guards
for s in (-1, 1):
    box('CargoJamb', (0.22, 0.55, CB_Z1 - CB_Z0 + 0.2), (s * (CB_W / 2 + 0.11), yc - 0.05, czc), GRAPH_S, bevel=0.02)
    box('CargoJambGlow', (0.02, 0.03, CB_Z1 - CB_Z0 - 0.3), (s * (CB_W / 2 + 0.225), yc - 0.3, czc), CYAN, bevel=0.0)
box('CargoHeader', (CB_W + 0.44, 0.6, 0.24), (0, yc - 0.05, CB_Z1 + 0.12), GRAPH_S, bevel=0.02)
box('CargoHeaderStripe', (CB_W + 0.2, 0.02, 0.12), (0, yc - 0.355, CB_Z1 + 0.12), AMBER_HZ, bevel=0.0)
box('CargoSill', (CB_W + 0.44, 0.6, 0.14), (0, yc - 0.05, CB_Z0 - 0.07), STEELD, bevel=0.01)
# drop-down door: hinged at the sill, lowered 34 deg (partly open)
DOOR_OPEN = math.radians(34); DH = CB_Z1 - CB_Z0 - 0.04
piv = bpy.data.objects.new('CargoDoor', None); coll('Mine').objects.link(piv)
piv.location = (0, yc - 0.3, CB_Z0); piv.rotation_euler = (DOOR_OPEN, 0, 0)
def dp(name, size, loc, mat, bev=0.02):
    o = box(name, size, loc, mat, bevel=bev); o.parent = piv; return o
dp('CargoDoorPanel', (CB_W - 0.04, 0.14, DH), (0, 0, DH / 2), WHITE_S, 0.03)
dp('CargoDoorSkinBand', (CB_W - 0.02, 0.15, 0.3), (0, 0, DH * 0.62), STEEL, 0.01)
for z_ in (0.5, 1.6, 2.7, 3.8):   # inner-face ribs (seen from above while it is lowered)
    dp('CargoDoorRib', (CB_W - 0.3, 0.08, 0.1), (0, 0.1, z_), GRAPH_S, 0.01)
for x_ in (-1.1, 0.0, 1.1):
    dp('CargoDoorSpine', (0.1, 0.08, DH - 0.3), (x_, 0.1, DH / 2), GRAPH_S, 0.01)
dp('CargoDoorHazard', (CB_W - 0.3, 0.02, 0.12), (0, -0.08, DH - 0.18), AMBER_HZ, 0.0)
for s in (-1, 1):
    dp('CargoDoorHinge', (0.4, 0.22, 0.22), (s * (CB_W / 2 - 0.4), 0.05, 0.05), SATIN, 0.03)
    dp('CargoDoorLatch', (0.14, 0.1, 0.24), (s * (CB_W / 2 - 0.25), 0.1, DH - 0.25), SATIN, 0.01)
bpy.context.view_layer.update()
for s in (-1, 1):   # restraint cables from the jambs hold it at its partly-open angle
    p_door = piv.matrix_world @ Vector((s * (CB_W / 2 - 0.12), 0.08, DH - 0.15))
    cable('CargoDoorCable', (s * (CB_W / 2 + 0.12), yc - 0.3, CB_Z1 - 0.15), tuple(p_door), 0.018, INK, sag=0.06)
# davit hoist above the door: slewing housing + winch, kingpost + tie, boom with sheave head
HZ = CB_Z1 + 0.95; BOOM_R = 8.4; BTIP = Vector((0, -BOOM_R, HZ + 0.75))
box('HoistBasePlate', (1.3, 0.08, 1.5), (0, yc - 0.03, HZ - 0.05), STEELD, bevel=0.02)
hull_bolts_front = [(x_, z_) for x_ in (-0.55, 0.55) for z_ in (HZ - 0.7, HZ + 0.6)]
for x_, z_ in hull_bolts_front: cyl('HoistBolt', 0.04, 0.05, (x_, yc - 0.08, z_), SATIN, rot=(math.pi / 2, 0, 0), segs=8, bevel=0.0)
box('HoistHousing', (0.8, 0.7, 0.9), (0, yc - 0.42, HZ), WHITE_S, bevel=0.06)
box('HoistHousingBand', (0.82, 0.72, 0.12), (0, yc - 0.42, HZ + 0.3), AMBER_HZ, bevel=0.01)
cyl('HoistWinchDrum', 0.22, 0.6, (0, yc - 0.5, HZ - 0.62), GRAPH_S, rot=(0, math.pi / 2, 0), segs=24, bevel=0.01)
for s in (-1, 1): cyl('HoistWinchCheek', 0.28, 0.04, (s * 0.32, yc - 0.5, HZ - 0.62), STEELD, rot=(0, math.pi / 2, 0), segs=24, bevel=0.005)
b0 = Vector((0, yc - 0.75, HZ + 0.1))
beam('HoistBoom', b0, BTIP, 0.34, 0.42, WHITE_S, bevel=0.03)
beam('HoistBoomStripe', b0.lerp(BTIP, 0.82), BTIP + Vector((0, 0.15, 0)), 0.36, 0.44, AMBER_HZ, bevel=0.02)
kp = Vector((0, yc - 0.45, HZ + 2.2))
rod('HoistKingpost', (0, yc - 0.42, HZ + 0.45), tuple(kp), 0.09, STEELD, segs=12)
for s in (-1, 1): rod('HoistTie', tuple(kp + Vector((s * 0.08, 0, 0))), tuple(BTIP + Vector((s * 0.12, 0.35, 0.18))), 0.035, SATIN, segs=8)
cyl('HoistSheave', 0.26, 0.12, tuple(BTIP + Vector((0, -0.1, -0.1))), SATIN, rot=(0, math.pi / 2, 0), segs=24, bevel=0.01)
sphere('HoistTipLamp', 0.06, tuple(BTIP + Vector((0, -0.1, 0.32))), M_glow('S_AmberBeacon', '#ffb020', 25), sub=1)
cable('HoistRunline', tuple(b0 + Vector((0, 0.1, -0.6))), tuple(BTIP + Vector((0, 0.1, -0.25))), 0.015, INK, sag=0.05)
# load line down to the hook block, 4-leg sling to the REFINERY crate being lowered
HOOK = Vector((0, -BOOM_R, 6.2))
rod('HoistLoadLine', tuple(BTIP + Vector((0, -0.1, -0.35))), tuple(HOOK + Vector((0, 0, 0.35))), 0.016, INK, segs=6)
box('HoistHookBlock', (0.28, 0.2, 0.5), tuple(HOOK + Vector((0, 0, 0.15))), AMBER_HZ, bevel=0.04)
rod('HoistHook', tuple(HOOK + Vector((0, 0, -0.1))), tuple(HOOK + Vector((0, 0, -0.32))), 0.04, SATIN, segs=8)
CR_SZ = (2.0, 1.2, 1.2); CR_BOT = HOOK.z - 2.05
crate('CrateRefinery', 'REFINERY', (0.0, -BOOM_R, CR_BOT), 0.0, size=CR_SZ)
for sx in (-1, 1):
    for sy in (-1, 1):
        rod('HoistSling', tuple(HOOK + Vector((0, 0, -0.32))), (sx * (CR_SZ[0] / 2 - 0.2), -BOOM_R + sy * (CR_SZ[1] / 2 - 0.15), CR_BOT + CR_SZ[2] + 0.02), 0.012, INK, segs=6)
# tag line held by the ground crew
cable('HoistTagLine', (0.95, -BOOM_R - 0.5, CR_BOT + 0.15), (2.3, -BOOM_R - 1.6, 1.15), 0.01, AMBER_HZ, sag=0.3)
spin_new(_b, CB_A - FRONT)


# ---------------------------------------------------------------- pad lighting + power masts (outside the legs, inside the berm)
def mast(name, a, r, h=12.0, power=False):
    base = polar(a, r, 0.0); inward = (-base).normalized()
    root = bpy.data.objects.new(name, None); coll('Mine').objects.link(root)
    P = [box(name + '_Footing', (1.2, 1.2, 0.3), tuple(base + Vector((0, 0, 0.15))), GRAPH, bevel=0.04)]
    P.append(rod(name + '_Pole', tuple(base + Vector((0, 0, 0.3))), tuple(base + Vector((0, 0, h))), 0.14, WHITE_S, r2=0.1, segs=20))
    for k in range(4):
        q = TAU * k / 4 + 0.4; d = Vector((math.cos(q), math.sin(q), 0))
        P.append(rod(name + '_Guy', tuple(base + d * 0.5 + Vector((0, 0, 0.3))), tuple(base + Vector((0, 0, 2.2))), 0.035, STEELD, segs=8))
    P.append(box(name + '_Band', (0.34, 0.34, 0.12), tuple(base + Vector((0, 0, h * 0.5))), CYAN, bevel=0.0))
    arm_c = base + Vector((0, 0, h)) + inward * 0.35
    P.append(box(name + '_Crossarm', (1.8, 0.18, 0.18), tuple(arm_c), GRAPH_S, rot=(0, 0, math.atan2(inward.y, inward.x) + math.pi / 2), bevel=0.02))
    side = Vector((-inward.y, inward.x, 0))
    for s in (-0.6, 0.0, 0.6):
        p = arm_c + side * s + inward * 0.15 + Vector((0, 0, -0.12))
        P.append(box(name + '_Lamp', (0.4, 0.3, 0.22), tuple(p), GRAPH_S, rot=(0, 0, math.atan2(inward.y, inward.x) + math.pi / 2), bevel=0.03))
        P.append(box(name + '_Lens', (0.34, 0.02, 0.16), tuple(p + inward * 0.16), LAMP, rot=(0, 0, math.atan2(inward.y, inward.x) + math.pi / 2), bevel=0.0))
    lt = light(name + '_Flood', 'SPOT', tuple(arm_c + inward * 0.4), 9000 if not power else 7000, '#f2f5ff', size=0.3, spot=math.radians(55))
    aim(lt, (0, 0, 4.0))
    P.append(box(name + '_Junction', (0.6, 0.4, 0.9), tuple(base + inward * 0.75 + Vector((0, 0, 0.75))), WHITE_S, bevel=0.04))
    P.append(box(name + '_JunctionGlow', (0.04, 0.42, 0.06), tuple(base + inward * 1.05 + Vector((0, 0, 1.0))), CYAN, bevel=0.0))
    if power:   # power mast: insulators + cable run on low stanchions toward the ship
        P.append(box(name + '_Xfmr', (1.4, 1.0, 1.3), tuple(base - inward * 1.4 + Vector((0, 0, 0.65))), GRAPH_S, bevel=0.06))
        for k in range(6): P.append(box(name + '_XfmrFin', (0.05, 1.0, 1.1), tuple(base - inward * 1.4 + side * (-0.6 + 0.24 * k) + Vector((0, 0, 0.65))), STEELD, rot=(0, 0, math.atan2(inward.y, inward.x) + math.pi / 2), bevel=0.0))
        for k in range(3):
            P.append(cyl(name + '_Insulator', 0.08, 0.35, tuple(base + side * (-0.6 + 0.6 * k) + Vector((0, 0, h + 0.32))), WHITE_S, segs=12, bevel=0.01))
        pts = [base + inward * (1.2 + 2.2 * i) for i in range(4)]
        for p in pts:
            P.append(rod(name + '_Stanchion', tuple(p), tuple(p + Vector((0, 0, 0.6))), 0.04, STEELD, segs=8))
        for p0, p1 in zip(pts, pts[1:]):
            P.append(cable(name + '_Cable', tuple(p0 + Vector((0, 0, 0.6))), tuple(p1 + Vector((0, 0, 0.6))), 0.04, INK, sag=0.15))
        P.append(box(name + '_ShipPlug', (0.7, 0.5, 0.8), tuple(pts[-1] + inward * 0.5 + Vector((0, 0, 0.4))), WHITE_S, bevel=0.05))
    for p in P: p.parent = root
    return root
MASTS = [('LightMastA', math.radians(195), 16.5, 12.0, False), ('LightMastB', math.radians(330), 16.5, 12.0, False),
         ('LightMastC', math.radians(95), 16.5, 12.0, False), ('PowerMast', math.radians(145), 16.8, 14.0, True)]
for nm, a, r, h, pw in MASTS: mast(nm, a, r, h, pw)

# ---------------------------------------------------------------- fuel umbilical (Tank Farm connection): ground box -> supported hose run -> hull QD plate
def umbilical():
    root = bpy.data.objects.new('FuelUmbilical', None); coll('Mine').objects.link(root)
    n = Vector((math.cos(UA), math.sin(UA), 0)); t = Vector((-n.y, n.x, 0)); rz = UA + math.pi / 2
    P = []
    gb = n * 17.1
    P.append(box('UmbBox', (1.5, 1.1, 1.15), tuple(gb + Vector((0, 0, 0.6))), WHITE_S, rot=(0, 0, rz), bevel=0.06))
    P.append(box('UmbBoxPlinth', (1.8, 1.4, 0.06), tuple(gb + Vector((0, 0, 0.03))), GRAPH, rot=(0, 0, rz), bevel=0.02))
    P.append(box('UmbBoxBand', (1.54, 1.14, 0.14), tuple(gb + Vector((0, 0, 0.95))), GRAPH_S, rot=(0, 0, rz), bevel=0.02))
    P.append(box('UmbBoxHazard', (1.2, 0.02, 0.12), tuple(gb - n * 0.56 + Vector((0, 0, 0.3))), AMBER_HZ, rot=(0, 0, rz), bevel=0.0))
    P.append(box('UmbBoxGlow', (0.5, 0.02, 0.05), tuple(gb - n * 0.56 + Vector((0, 0, 0.78))), CYAN, rot=(0, 0, rz), bevel=0.0))
    for s_ in (-0.4, 0.4):   # valve wheels + inlet flanges toward the ship
        c = gb - n * 0.62 + t * s_ + Vector((0, 0, 0.55))
        P.append(rod('UmbFlange', tuple(c), tuple(c - n * 0.18), 0.13, STEELD, segs=20))
        P.append(rod('UmbValve', tuple(c - n * 0.18 + Vector((0, 0, 0.12))), tuple(c - n * 0.18 + Vector((0, 0, 0.36))), 0.03, SATIN, segs=8))
        P.append(cyl('UmbValveWheel', 0.14, 0.03, tuple(c - n * 0.18 + Vector((0, 0, 0.37))), AMBER_HZ, segs=20, bevel=0.005))
    # outgoing line toward the Tank Farm (runs off-pad, sits ON the ground)
    P.append(cable('UmbFeed', tuple(gb + n * 0.6 + Vector((0, 0, 0.35))), tuple(n * 20.2 + Vector((0, 0, 0.1))), 0.09, HOSE, sag=0.0))
    # hose run on cradle stanchions
    rs = [15.6, 13.4, 11.2, 9.0]; hz = 0.7
    pts = []
    for r_ in rs:
        p = n * r_
        P.append(box('UmbFooting', (0.5, 0.5, 0.12), tuple(p + Vector((0, 0, 0.06))), GRAPH, rot=(0, 0, rz), bevel=0.02))
        P.append(rod('UmbStanchion', tuple(p + Vector((0, 0, 0.12))), tuple(p + Vector((0, 0, hz - 0.12))), 0.05, STEELD, segs=10))
        P.append(box('UmbCradle', (0.5, 0.16, 0.08), tuple(p + Vector((0, 0, hz - 0.1))), STEELD, rot=(0, 0, rz), bevel=0.01))
        pts.append(p + Vector((0, 0, hz)))
    for s_, rr_ in ((-0.13, 0.09), (0.13, 0.05)):
        o = t * s_
        P.append(cable('UmbHose', tuple(gb - n * 0.8 + o + Vector((0, 0, 0.55))), tuple(pts[0] + o), rr_, HOSE, sag=0.08))
        for p0, p1 in zip(pts, pts[1:]):
            P.append(cable('UmbHose', tuple(p0 + o), tuple(p1 + o), rr_, HOSE, sag=0.12))
    # A-frame riser that lifts the hose up to the hull plate
    rp_ = n * 6.6
    for s_ in (-0.55, 0.55):
        P.append(rod('UmbRiserLeg', tuple(rp_ + t * s_ + n * 0.4), tuple(rp_ + Vector((0, 0, 3.9))), 0.07, STEELD, segs=12))
        P.append(box('UmbRiserFoot', (0.4, 0.4, 0.1), tuple(rp_ + t * s_ + n * 0.4 + Vector((0, 0, 0.05))), GRAPH, rot=(0, 0, rz), bevel=0.02))
    P.append(box('UmbRiserSaddle', (0.7, 0.3, 0.14), tuple(rp_ + Vector((0, 0, 3.95))), GRAPH_S, rot=(0, 0, rz), bevel=0.02))
    P.append(rod('UmbRiserBrace', tuple(rp_ + n * 0.4 + Vector((0, 0, 0.1))), tuple(rp_ + Vector((0, 0, 2.2))), 0.04, STEELD, segs=8))
    top = rp_ + Vector((0, 0, 4.05))
    qd = polar(UA, R + 0.42, 4.7)
    for s_, rr_ in ((-0.13, 0.09), (0.13, 0.05)):
        o = t * s_
        P.append(cable('UmbHose', tuple(pts[-1] + o), tuple(top + o), rr_, HOSE, sag=0.5))
        P.append(cable('UmbHose', tuple(top + o), tuple(qd + o), rr_, HOSE, sag=0.25))
    for p in P: p.parent = root
    # quick-disconnect plate on the hull (part of the ship)
    on_hull('QDPlate', (0.95, 0.95, 0.07), UA, 4.7, STEELD, bevel=0.02)
    frame('QDFrame', UA, 4.7, 0.95, 0.95, t=0.07, depth=0.09, mat=AMBER_HZ)
    hull_bolts(UA, 4.7, 0.85, 0.85, 3, 3, 0.05, 0.08)
    for s_ in (-1, 1):
        c0 = polar(UA + s_ * 0.13 / R, R + 0.07, 4.7)
        rod('QDCoupling', tuple(c0), tuple(polar(UA + s_ * 0.13 / R, R + 0.42, 4.7)), 0.12 if s_ < 0 else 0.08, SATIN, segs=20)
        rod('QDCollar', tuple(polar(UA + s_ * 0.13 / R, R + 0.3, 4.7)), tuple(polar(UA + s_ * 0.13 / R, R + 0.38, 4.7)), 0.15 if s_ < 0 else 0.11, AMBER_HZ, segs=20)
    sphere('QDLamp', 0.035, tuple(polar(UA, R + 0.1, 5.25)), CYAN, sub=1)
umbilical()

# astronauts (1.8 m): one climbing the caged ladder, one at the airlock dust-off station, one at the ladder foot,
# two ground crew at the hoist (one on the tag line)
RzA = Matrix.Rotation(AL_A - FRONT, 4, 'Z'); RzC = Matrix.Rotation(CB_A - FRONT, 4, 'Z')
def _w(Rz, x, y, z): v = Rz @ Vector((x, y, z)); return (v.x, v.y, v.z)
ASTRO = [(_w(RzA, 0.0, LY - 0.22, 14.7), math.pi + AL_A - FRONT),
         (_w(RzA, 0.72, -(R + 0.75), TOP), math.pi + AL_A - FRONT + 0.3),
         (_w(RzA, 1.0, LY - 1.3, 0.0), AL_A - FRONT + 0.5),
         (_w(RzC, 2.35, -10.2, 0.0), -2.19 + CB_A - FRONT),
         (_w(RzC, -0.2, -11.4, 0.0), 0.5 + CB_A - FRONT)]


# ================================================================ root + stage
convert_curves()
root = bpy.data.objects.new('StarterShip', None); coll('Mine').objects.link(root)
for ob in coll('Mine').objects:
    if ob is not root and ob.parent is None: ob.parent = root

PAD_R, PAD_T = 18.0, 0.2
height = build_stage(keep_flat=((0, 0, 44),))
gnd = bpy.data.objects['Ground']; gnd.location.z = -PAD_T          # level regolith; the pad slab sits ON it
GREY = gnd.data.materials[0]   # shared mc_common.M_ground() (cool grey regolith, broken strata; Director rule, 269e70f)
_br = bpy.data.materials['M_Boulder'].node_tree.nodes
for nd in _br:
    if nd.type == 'VAL_TO_RGB': nd.color_ramp.elements[0].color = hexc('#5b5d60'); nd.color_ramp.elements[-1].color = hexc('#8c8e91')
bpy.data.materials['M_Boulder'].diffuse_color = hexc('#6d6f72')
EXTRA_CRATERS = [(-62, 40, 7), (55, -48, 9), (-85, -30, 6), (70, 25, 5), (-50, -62, 10), (95, -10, 8), (-100, 45, 6.5), (30, -70, 7),
                 (-20, -80, 5.5), (110, 50, 6), (-75, 66, 5), (58, 58, 4), (-35, 55, 3.5), (48, -28, 3), (-55, 15, 4), (-110, -70, 9), (85, -85, 7)]
def gdelta(x, y, z):
    z0 = z; d0 = math.hypot(x, y)
    for cx, cy, r in EXTRA_CRATERS:
        d = math.hypot(x - cx, y - cy) / r
        if d < 1.6:
            z += (-0.3 * r * max(0, 1 - d * d) ** 1.2 if d < 1 else 0) + 0.11 * r * math.exp(-((d - 1.0) / 0.18) ** 2)
    if z > 0.8:   # irregular strata ledges on the slopes (uneven bed thickness, no repeating stripes)
        zw = z + 2.5 * noise.noise(Vector((x * 0.02, y * 0.02, 3.0)))
        tt = zw / 3.4 + 1.1 * noise.noise(Vector((zw * 0.13, 0.0, 7.0))) + 0.5 * noise.noise(Vector((x * 0.03, y * 0.03, 9.0)))
        f = tt - math.floor(tt)
        st = 0.0 if f < 0.8 else ((f - 0.8) / 0.2) ** 2 * (3 - 2 * (f - 0.8) / 0.2)
        z += 0.55 * (st - f) * min(1.0, (z - 0.8) / 2.0) * (0.5 + 0.5 * noise.noise(Vector((x * 0.04, y * 0.04, 13.0))))
    if d0 < 44: return 0.0
    if d0 < 46: return (z - z0) * (d0 - 44) / 2
    return z - z0
for v in gnd.data.vertices:
    v.co.z += gdelta(v.co.x, v.co.y, v.co.z)
gnd.data.update()
for ob in list(coll('Stage').objects):   # keep rocks sitting on the re-shaped ground
    if ob.type == 'MESH' and ob.name.startswith(('pebble', 'boulder', 'slope_boulder')):
        c = ob.matrix_world @ (sum((Vector(v) for v in ob.bound_box), Vector()) / 8)
        bz = ob.matrix_world @ Vector(min(ob.bound_box, key=lambda q: q[2]))
        ob.location.z += gdelta(c.x, c.y, bz.z)
for ob in list(coll('Stage').objects):   # clear pebbles/boulders from the pad + berm area
    if ob.name.startswith(('pebble', 'boulder')) and ob.type == 'MESH':
        c = sum((Vector(v) for v in ob.bound_box), Vector()) / 8
        if c.xy.length < 30: bpy.data.objects.remove(ob)
        else: ob.location.z -= PAD_T
lathe('LandingPadSintered', [(0, 0.0), (PAD_R - 0.4, 0.0), (PAD_R, -0.08), (PAD_R + 0.1, -PAD_T), (0, -PAD_T)], (0, 0, 0), M_pad(), segs=256, c='Stage', angle=20)
for k in range(36):   # recessed pad-edge lights
    a = TAU * k / 36
    box('PadEdgeLight', (0.3, 0.12, 0.03), tuple(polar(a, PAD_R - 0.7, 0.0)), CYAN if k % 3 else LAMP, rot=(0, 0, a + math.pi / 2), bevel=0.0, c='Stage')
# low blast berm: built-up regolith ring ABOVE the ground, faced with sintered blocks, open toward the access road
REGO = GREY
def berm(a0, a1, r0=21.0, r1=26.5, h=1.4, segs=160):
    prof = [(r0 - 0.1, -PAD_T - 0.05), (r0, h * 0.55), (r0 + 0.6, h), (r0 + 2.2, h * 1.02), (r1 - 1.2, h * 0.5), (r1, -PAD_T - 0.05)]
    bm = bmesh.new(); rings = []
    n = max(8, int(segs * (a1 - a0) / TAU))
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n; wob = 0.08 * math.sin(a * 7.0) + 0.05 * math.sin(a * 17.0)
        rings.append([bm.verts.new(((r + wob) * math.cos(a), (r + wob) * math.sin(a), z - PAD_T * 0 + (wob * 0.6 if 0 < z else 0))) for r, z in prof])
    for i in range(n):
        for k in range(len(prof) - 1):
            bm.faces.new((rings[i][k], rings[i + 1][k], rings[i + 1][k + 1], rings[i][k + 1]))
    for rg in (rings[0], rings[-1]): bm.faces.new(rg)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(bm, 'BlastBerm', REGO, 'Stage', smooth=True, angle=60)
GAP0, GAP1 = math.radians(226), math.radians(268)
berm(GAP1, GAP0 + TAU)
SINTER_BLK = M_paint('S_SinterBlock', '#58595b', rough=0.85, metal=0.0, bevel=0.03, grime=0.35, grime_col='#333436', bump_noise=0.3)
k = 0; a = GAP1 + 0.08
while a < GAP0 + TAU - 0.08:
    box('BermBlock', (2.6, 0.5, 0.75), tuple(polar(a, 20.8, 0.375 - PAD_T + 0.0)), SINTER_BLK, rot=(0, 0, a + math.pi / 2 + rr.uniform(-0.03, 0.03)), bevel=0.04, c='Stage')
    a += 2.75 / 20.8; k += 1
world_and_sun((-0.55, -0.62, 0.56), 5.5)
bpy.data.lights['Sun'].color = (1.0, 1.0, 1.0)          # neutral white sun (no warm cast)
bpy.data.objects.remove(bpy.data.objects['Earth'])          # brief: pure black sky, no Earth, no stars
wn = bpy.context.scene.world.node_tree
for l in list(wn.links):
    if l.to_node.type == 'MIX' and l.to_socket.name == 'Factor' and l.from_node.type == 'MATH': wn.links.remove(l)
for n in wn.nodes:
    if n.type == 'MIX' and n.inputs['Factor'].is_linked is False: n.inputs['Factor'].default_value = 0.0
for loc, rz in ASTRO: astronaut(loc, rot_z=rz)
cam = setup_render(48 if not QUICK else 16)
sc = bpy.context.scene; sc.cycles.max_bounces = 6; sc.cycles.transmission_bounces = 4; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.adaptive_threshold = 0.03

# stats
dg = bpy.context.evaluated_depsgraph_get(); tris = 0
mn = Vector((1e9,) * 3); mx_ = Vector((-1e9,) * 3); ship_mn = Vector((1e9,) * 3); ship_mx = Vector((-1e9,) * 3)
for ob in coll('Mine').all_objects:
    if ob.type != 'MESH' or ob.hide_render: continue
    me = ob.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); tris += len(me.loop_triangles)
    isship = not any(ob.name.startswith(p) for p in ('Crate', 'LightMast', 'PowerMast', 'Umb', 'FuelUmb'))
    for v in me.vertices:
        w = ob.matrix_world @ v.co; mn = Vector(map(min, mn, w)); mx_ = Vector(map(max, mx_, w))
        if isship: ship_mn = Vector(map(min, ship_mn, w)); ship_mx = Vector(map(max, ship_mx, w))
    ob.evaluated_get(dg).to_mesh_clear()
print(f'STATS tris={tris} all_min={tuple(round(x,2) for x in mn)} all_max={tuple(round(x,2) for x in mx_)} ship_min={tuple(round(x,2) for x in ship_mn)} ship_max={tuple(round(x,2) for x in ship_mx)}', flush=True)

ONLY = A.get('only', 'turn,hero')
if 'glb' in ONLY:
    bpy.ops.object.select_all(action='DESELECT')
    for ob in coll('Mine').all_objects: ob.select_set(True)
    for ob in coll('Stage').all_objects:
        if ob.name.startswith('Astronaut') or (ob.parent and ob.parent.name.startswith('Astronaut')): ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'starter_ship_master.glb'), export_format='GLB', use_selection=True, export_apply=True,
                              export_yup=True, export_animations=False, export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=True)
if 'blend' in ONLY:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'starter_ship_master.blend'), compress=True)
TGT = (0.0, -3.0, 18.5)
if 'turn' in ONLY:
    turntable(cam, os.path.join(OUT, 'turntable'), TGT, 60, 10, size=1100 if not QUICK else 400, samples=int(A.get('ts', 40)) if not QUICK else 12, lens=35)
def _pw(deg, r, z): v = polar(math.radians(deg), r, z); return (round(v.x, 3), round(v.y, 3), z)
CL_T, CL_P = _pw(248, 3.0, 11.6), _pw(254, 31.0, 7.4)      # ladder/airlock + cargo door/hoist + crates, full height
if 'close' in ONLY:
    shoot(cam, os.path.join(OUT, 'turntable', 'closeup.png'), CL_T, CL_P, 1600 if not QUICK else 640, 1000 if not QUICK else 400,
          lens=20, samples=int(A.get('cs', 96)) if not QUICK else 24)
if 'close4k' in ONLY:
    w, h = (3840, 2160) if not QUICK else (960, 540)
    shoot(cam, os.path.join(OUT, 'starter_ship_closeup_ladder_airlock_hoist_3840x2160.png'), CL_T, CL_P, w, h,
          lens=20, samples=int(A.get('c4s', 64)) if not QUICK else 24)
if 'ports' in ONLY:
    shoot(cam, os.path.join(OUT, 'turntable', 'ports.png'), _pw(215, 3.6, 21.55), _pw(210, 11.5, 21.3), 1200 if not QUICK else 600, 800 if not QUICK else 400, lens=50,
          samples=int(A.get('ps', 96)) if not QUICK else 24)
if 'hero' in ONLY:
    w, h = (3840, 2160) if not QUICK else (960, 540)
    shoot(cam, os.path.join(OUT, 'starter_ship_hero_3840x2160.png'), (0.5, -4.0, 18.0), (-23.0, -50.0, 9.5), w, h, lens=22,
          samples=int(A.get('hs', 64)) if not QUICK else 24)
