"""Planet Stack - Starter Ship master (concept B look, original design, no real logos).
blender -b -P build_starter_ship.py -- --out DIR [--quick 1] [--only glb,blend,turn,hero,close] [--hs 128]
Imports the shared stage/sun/astronaut/render helpers from art/3d/mine_concepts/_src/mc_common.py (read-only).
Blender coords: Z-up, metres, front = -Y (exports as glTF +Y up, front +Z). Origin = base centre on the pad top.
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', 'mine_concepts', '_src')))
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
from mc_common import *
from mc_common import _obj, _nodes

A = argv(); OUT = A.get('out', HERE); os.makedirs(OUT, exist_ok=True)
QUICK = A.get('quick') == '1'
reset(); rr = random.Random(7)
TAU = math.tau
R = 4.0            # hull radius (8.0 m diameter), true scale
Z_AFT, Z_BODY, Z_NOSE, Z_TIP = 2.4, 3.4, 31.0, 40.0

# ================================================================ materials
def decorate(m, seams=None, dust=(0.0, 4.5, 0.75), top_dust=0.35, dust_col='#7d7871', soot=None):
    """Inject cylindrical panel seams + regolith dust (world-height gradient + up-facing) into an M_paint material."""
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    col_link = next((l for l in nt.links if l.to_socket == b.inputs['Base Color']), None)
    col = col_link.from_socket if col_link else None
    if col is None:
        rgb = nt.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = b.inputs['Base Color'].default_value; col = rgb.outputs[0]
    nrm_link = next((l for l in nt.links if l.to_socket == b.inputs['Normal']), None)
    nrm = nrm_link.from_socket if nrm_link else None
    tc = nt.nodes.new('ShaderNodeTexCoord'); geo = nt.nodes.new('ShaderNodeNewGeometry')
    if seams:
        pw, ph, rad = seams
        sx = nt.nodes.new('ShaderNodeSeparateXYZ'); link(nt, tc.outputs['Object'], sx.inputs[0])
        at = nt.nodes.new('ShaderNodeMath'); at.operation = 'ARCTAN2'; link(nt, sx.outputs['Y'], at.inputs[0]); link(nt, sx.outputs['X'], at.inputs[1])
        ml = nt.nodes.new('ShaderNodeMath'); ml.operation = 'MULTIPLY'; ml.inputs[1].default_value = rad; link(nt, at.outputs[0], ml.inputs[0])
        cb = nt.nodes.new('ShaderNodeCombineXYZ'); link(nt, ml.outputs[0], cb.inputs['X']); link(nt, sx.outputs['Z'], cb.inputs['Y'])
        br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 1.0
        br.inputs['Brick Width'].default_value = pw; br.inputs['Row Height'].default_value = ph
        br.inputs['Mortar Size'].default_value = 0.012; br.inputs['Mortar Smooth'].default_value = 0.3; br.offset = 0.5
        for k in ('Color1', 'Color2'): br.inputs[k].default_value = (1, 1, 1, 1)
        br.inputs['Mortar'].default_value = (0, 0, 0, 1)
        link(nt, cb.outputs[0], br.inputs['Vector'])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; link(nt, br.outputs['Fac'], inv.inputs[1])
        f = nt.nodes.new('ShaderNodeMath'); f.operation = 'MULTIPLY'; f.inputs[1].default_value = 0.0
        # darken seams 55%
        mxs = nt.nodes.new('ShaderNodeMix'); mxs.data_type = 'RGBA'
        sf = nt.nodes.new('ShaderNodeMath'); sf.operation = 'MULTIPLY'; sf.inputs[1].default_value = 0.6; link(nt, br.outputs['Fac'], sf.inputs[0])
        link(nt, sf.outputs[0], mxs.inputs['Factor']); link(nt, col, mxs.inputs[6]); mxs.inputs[7].default_value = hexc('#34373c')
        col = mxs.outputs[2]
        bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.7; bump.inputs['Distance'].default_value = 0.01
        link(nt, inv.outputs[0], bump.inputs['Height'])
        if nrm: link(nt, nrm, bump.inputs['Normal'])
        nrm = bump.outputs['Normal']
    if soot:   # darker burn tint above a height band (thruster soot)
        pass
    if dust:
        h0, h1, amt = dust
        ps = nt.nodes.new('ShaderNodeSeparateXYZ'); link(nt, geo.outputs['Position'], ps.inputs[0])
        hr = nt.nodes.new('ShaderNodeMapRange'); hr.inputs['From Min'].default_value = h0; hr.inputs['From Max'].default_value = h1
        hr.inputs['To Min'].default_value = amt; hr.inputs['To Max'].default_value = 0.0; link(nt, ps.outputs['Z'], hr.inputs['Value'])
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.5; nz.inputs['Detail'].default_value = 10; nz.inputs['Roughness'].default_value = 0.65
        link(nt, tc.outputs['Object'], nz.inputs['Vector'])
        nr = nt.nodes.new('ShaderNodeMapRange'); nr.inputs['From Min'].default_value = 0.3; nr.inputs['From Max'].default_value = 0.65
        nr.inputs['To Min'].default_value = 0.25; link(nt, nz.outputs['Fac'], nr.inputs['Value'])
        d1 = nt.nodes.new('ShaderNodeMath'); d1.operation = 'MULTIPLY'; link(nt, hr.outputs[0], d1.inputs[0]); link(nt, nr.outputs[0], d1.inputs[1])
        nsz = nt.nodes.new('ShaderNodeSeparateXYZ'); link(nt, geo.outputs['Normal'], nsz.inputs[0])
        up = nt.nodes.new('ShaderNodeMapRange'); up.inputs['From Min'].default_value = 0.55; up.inputs['From Max'].default_value = 0.95
        up.inputs['To Max'].default_value = top_dust; link(nt, nsz.outputs['Z'], up.inputs['Value'])
        d2 = nt.nodes.new('ShaderNodeMath'); d2.operation = 'MULTIPLY'; link(nt, up.outputs[0], d2.inputs[0]); link(nt, nr.outputs[0], d2.inputs[1])
        ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'; ad.use_clamp = True; link(nt, d1.outputs[0], ad.inputs[0]); link(nt, d2.outputs[0], ad.inputs[1])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        link(nt, ad.outputs[0], mx.inputs['Factor']); link(nt, col, mx.inputs[6]); mx.inputs[7].default_value = hexc(dust_col)
        col = mx.outputs[2]
        # dust kills metal + gloss
        for sock, tgt in (('Metallic', 0.0), ('Roughness', 0.95)):
            src = next((l.from_socket for l in nt.links if l.to_socket == b.inputs[sock]), None)
            mr = nt.nodes.new('ShaderNodeMix'); mr.data_type = 'FLOAT'
            link(nt, ad.outputs[0], mr.inputs['Factor'])
            if src: link(nt, src, mr.inputs[2])
            else: mr.inputs[2].default_value = b.inputs[sock].default_value
            mr.inputs[3].default_value = tgt; link(nt, mr.outputs[0], b.inputs[sock])
        cw = nt.nodes.new('ShaderNodeMath'); cw.operation = 'SUBTRACT'; cw.inputs[0].default_value = b.inputs['Coat Weight'].default_value
        link(nt, ad.outputs[0], cw.inputs[1]); cw.use_clamp = True; link(nt, cw.outputs[0], b.inputs['Coat Weight'])
    link(nt, col, b.inputs['Base Color'])
    if nrm: link(nt, nrm, b.inputs['Normal'])
    return m

STEEL = decorate(M_paint('S_Steel', '#c3c8ce', rough=0.42, metal=0.72, grime=0.45, grime_col='#5d5750', bevel=0.02, dirt_scale=1.2),
                 seams=(1.9, 1.2, R), dust=(0.0, 8.0, 0.95))
STEEL_P = decorate(M_paint('S_SteelPlain', '#b2b7be', rough=0.4, metal=0.75, grime=0.25, grime_col='#5d5750', bevel=0.01), dust=(0.0, 3.0, 0.85))
WHITE = decorate(M_paint('S_White', '#e8edf5', rough=0.26, metal=0.0, grime=0.22, grime_col='#9e978e', wear=0.35, wear_col='#8a9098', coat=0.6, bevel=0.02, dirt_scale=1.6),
                 seams=(1.6, 1.1, R), dust=(0.0, 8.0, 0.8))
WHITE_P = decorate(M_paint('S_WhitePanel', '#e8edf5', rough=0.26, metal=0.0, grime=0.22, grime_col='#9e978e', coat=0.6, bevel=0.01, dirt_scale=1.6),
                   seams=(1.6, 1.1, R), dust=(0.0, 8.0, 0.8))
GRAPH_P = decorate(M_paint('S_GraphitePanel', '#2a3245', rough=0.36, metal=0.3, grime=0.15, grime_col='#6e6a64', coat=0.35, bevel=0.01),
                   seams=(0.62, 0.62, R), dust=(0.0, 5.0, 0.85), top_dust=0.5)
WHITE_S = decorate(M_paint('S_WhiteSmooth', '#e8edf5', rough=0.25, metal=0.0, grime=0.2, grime_col='#9e978e', wear=0.4, coat=0.6, bevel=0.015), dust=(0.0, 4.0, 0.7))
GRAPH = decorate(M_paint('S_Graphite', '#2a3245', rough=0.36, metal=0.45, grime=0.15, grime_col='#6e6a64', wear=0.3, wear_col='#8794ad', coat=0.35, bevel=0.015),
                 seams=(0.62, 0.62, R), dust=(0.0, 5.0, 0.85), top_dust=0.5)
GRAPH_S = decorate(M_paint('S_Graphite2', '#3a4258', rough=0.34, metal=0.5, grime=0.12, wear=0.35, wear_col='#8794ad', bevel=0.01), dust=(0.0, 3.5, 0.9), top_dust=0.5)
STEELD = decorate(M_paint('S_SteelDark', '#5b667e', rough=0.38, metal=0.8, grime=0.25, bevel=0.01), dust=(0.0, 3.5, 0.9), top_dust=0.5)
SATIN = decorate(M_paint('S_Satin', '#9aa3ad', rough=0.22, metal=1.0, bevel=0.005), dust=(0.0, 2.5, 0.9))
NOZ = M_paint('S_Nozzle', '#3b332f', rough=0.45, metal=1.0, grime=0.4, grime_col='#1a1816', bevel=0.005)
SOLAR = M_paint('S_Solar', '#2a3245', rough=0.45, metal=0.2, panel=3.0, coat=0.2, bevel=0.005)   # matte cells, no glossy glazing look
INK = M_paint('S_Ink', '#1f2329', rough=0.55, metal=0.0)
AMBER_HZ = decorate(M_paint('S_Hazard', '#ffb020', rough=0.5, hazard=('#ffb020', '#2a3245'), hazard_scale=3.0, grime=0.25, wear=0.4, bevel=0.005),
                    dust=(0.0, 3.0, 0.6), top_dust=0.4)
CYAN = M_glow('S_Cyan', '#3ad0ff', 16)
CYANS = M_glow('S_CyanSoft', '#3ad0ff', 5)
LAMP = M_glow('S_Lamp', '#fff4e4', 30)
WARM = M_glow('S_WarmGlow', '#ffc98a', 14)
GLASS = M_glass('S_PortGlass', '#c8e6ff', 0.02)
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
    m = bpy.data.materials.new('M_SinteredPad'); nt, b = _nodes(m); tc = nt.nodes.new('ShaderNodeTexCoord')
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); link(nt, tc.outputs['Object'], sx.inputs[0])
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = 0.55
    vor.inputs['Randomness'].default_value = 0.15
    link(nt, tc.outputs['Object'], vor.inputs['Vector'])
    seam = nt.nodes.new('ShaderNodeMapRange'); seam.inputs['From Min'].default_value = 0.0; seam.inputs['From Max'].default_value = 0.025
    link(nt, vor.outputs['Distance'], seam.inputs['Value'])
    vc = nt.nodes.new('ShaderNodeTexVoronoi'); vc.inputs['Scale'].default_value = 0.55; vc.inputs['Randomness'].default_value = 0.15
    link(nt, tc.outputs['Object'], vc.inputs['Vector'])
    tile = nt.nodes.new('ShaderNodeValToRGB'); tile.color_ramp.elements[0].color = hexc('#55524e'); tile.color_ramp.elements[1].color = hexc('#6d6965')
    link(nt, vc.outputs['Color'], tile.inputs['Fac'])
    # scorch: radial darkening toward centre
    ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; link(nt, tc.outputs['Object'], ln.inputs[0])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.4; nz.inputs['Detail'].default_value = 8
    link(nt, tc.outputs['Object'], nz.inputs['Vector'])
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 4.0; ad.inputs[2].default_value = -2.0
    link(nt, nz.outputs['Fac'], ad.inputs[0])
    dl = nt.nodes.new('ShaderNodeMath'); dl.operation = 'ADD'; link(nt, ln.outputs['Value'], dl.inputs[0]); link(nt, ad.outputs[0], dl.inputs[1])
    sc_ = nt.nodes.new('ShaderNodeMapRange'); sc_.inputs['From Min'].default_value = 3.0; sc_.inputs['From Max'].default_value = 13.0
    sc_.inputs['To Min'].default_value = 0.75; sc_.inputs['To Max'].default_value = 0.0; link(nt, dl.outputs[0], sc_.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; link(nt, sc_.outputs[0], mx.inputs['Factor'])
    link(nt, tile.outputs['Color'], mx.inputs[6]); mx.inputs[7].default_value = hexc('#24211f')
    # dust drift: lighter regolith toward the rim
    dd = nt.nodes.new('ShaderNodeMapRange'); dd.inputs['From Min'].default_value = 14.0; dd.inputs['From Max'].default_value = 18.5
    dd.inputs['To Max'].default_value = 0.85; link(nt, dl.outputs[0], dd.inputs['Value'])
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 1.6; n2.inputs['Detail'].default_value = 10
    link(nt, tc.outputs['Object'], n2.inputs['Vector'])
    m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; m2.use_clamp = True; link(nt, dd.outputs[0], m2.inputs[0])
    n2r = nt.nodes.new('ShaderNodeMapRange'); n2r.inputs['From Min'].default_value = 0.35; n2r.inputs['From Max'].default_value = 0.6; n2r.inputs['To Max'].default_value = 1.4
    link(nt, n2.outputs['Fac'], n2r.inputs['Value']); link(nt, n2r.outputs[0], m2.inputs[1])
    mx2 = nt.nodes.new('ShaderNodeMix'); mx2.data_type = 'RGBA'; link(nt, m2.outputs[0], mx2.inputs['Factor'])
    link(nt, mx.outputs[2], mx2.inputs[6]); mx2.inputs[7].default_value = hexc('#8b8987')
    mx3 = nt.nodes.new('ShaderNodeMix'); mx3.data_type = 'RGBA'; link(nt, seam.outputs[0], mx3.inputs['Factor'])
    mx3.inputs[6].default_value = hexc('#2b2927'); link(nt, mx2.outputs[2], mx3.inputs[7])
    link(nt, mx3.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.82
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.45; bump.inputs['Distance'].default_value = 0.02
    n3 = nt.nodes.new('ShaderNodeTexNoise'); n3.inputs['Scale'].default_value = 14; n3.inputs['Detail'].default_value = 12
    link(nt, tc.outputs['Object'], n3.inputs['Vector'])
    hb = nt.nodes.new('ShaderNodeMath'); hb.operation = 'MULTIPLY_ADD'; link(nt, n3.outputs['Fac'], hb.inputs[0]); hb.inputs[1].default_value = 0.4
    link(nt, seam.outputs[0], hb.inputs[2]); link(nt, hb.outputs[0], bump.inputs['Height']); link(nt, bump.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = hexc('#5f5b57'); return m

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
for k in range(3):
    a = TAU * k / 3 + 0.5; x, y = 1.7 * math.cos(a), 1.7 * math.sin(a)
    lathe('EngineBell', [(0.85, Z_AFT + 0.1), (0.76, Z_AFT + 0.35), (0.52, Z_AFT + 0.7), (0.32, Z_AFT + 0.95), (0.29, Z_AFT + 0.95), (0.49, Z_AFT + 0.7), (0.73, Z_AFT + 0.35), (0.82, Z_AFT + 0.1)],
          (x, y, 0), NOZ, segs=48)
    ring('EngineBellLip', 0.86, Z_AFT + 0.12, 0.06, SATIN, w=0.03, segs=48, loc=(x, y))
    lathe('EngineThroat', [(0, Z_AFT + 0.88), (0.34, Z_AFT + 0.9), (0.34, Z_AFT + 1.0), (0, Z_AFT + 1.0)], (x, y, 0), CYANS, segs=24)

# main hull: thick white shielded skin over the steel tank structure, with door + ports cut
hull = lathe('Hull', [(R, Z_BODY), (R, Z_NOSE)], (0, 0, 0), WHITE, segs=192, angle=80)
DOOR_W, DOOR_Z0, DOOR_Z1 = 2.6, 3.5, 6.3
cutter(box('cut_door', (DOOR_W, 2.4, DOOR_Z1 - DOOR_Z0), (0, -R, (DOOR_Z0 + DOOR_Z1) / 2), INK, bevel=0.0))
# crew deck: 4 sleep pods (2 columns x 2 rows), each behind its own small recessed, shuttered port
POD_A = [FRONT - 0.3, FRONT + 0.3]
POD_Z = [7.75, 8.95]
PORT_R = 0.24
PORTS = [(a, z - 0.1) for a in POD_A for z in POD_Z]   # ports sit just above mattress height
for (a, z) in PORTS:   # splayed reveal: 0.24 m at the skin, ~0.42 m at the pod face
    cutter(cyl('cut_port', 0.72, 1.2, polar(a, R - 0.2, z), INK, rot=radial_rot(a), segs=40, bevel=0.0, r2=0.01))
band = arc_panel('CrewBandPanel', R, FRONT - 0.62, FRONT + 0.62, 7.0, 10.0, 0.04, WHITE_P)
door_surround = arc_panel('DoorSurround', R, FRONT - 0.5, FRONT + 0.5, 3.4, 6.85, 0.05, GRAPH_P)
cut(hull, CUTTERS, solidify=HULL_T)
cut(band, CUTTERS); cut(door_surround, CUTTERS)
# exposed stainless structural bands + glow rings
for z0, z1 in ((3.4, 3.95), (11.0, 11.8), (24.4, 25.1), (30.4, 31.0)):
    arc_panel('SteelBand', R, 0, TAU, z0, z1, 0.03, STEEL, segs=192)
ring('SkirtGlow', R + 0.08, Z_BODY + 0.06, 0.06, CYAN, w=0.02, segs=192)
ring('DeckGlow', R + 0.06, 11.4, 0.06, CYAN, w=0.02, segs=192)
ring('UpperGlow', R + 0.06, 24.75, 0.05, CYANS, w=0.02, segs=192)
# graphite body-mounted radiator tiles on the back half
arc_panel('RadiatorTiles', R, 0.35, math.pi - 0.35, 12.4, 23.8, 0.05, GRAPH_P)
arc_panel('AftTilesBack', R, 0.5, math.pi - 0.5, 4.1, 6.9, 0.04, GRAPH_P)
for z in (5.0, 7.0, 10.3, 13.8, 16.6, 19.4, 22.2, 27.0, 29.0):
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
for a in (math.radians(200), math.radians(-20)):
    on_hull('PhasedArray', (1.2, 1.6, 0.1), a, 14.5, GRAPH_S, bevel=0.02)
    on_hull('PhasedArrayFace', (1.1, 1.5, 0.11), a, 14.5, SOLAR, bevel=0.005)
for a in (0.0, math.pi):
    sphere('NavLamp', 0.07, tuple(polar(a + 0.12, R + 0.05, 11.4)), CYAN, sub=1)

# greebles: vents, service panels, hatches, handholds
for a, z in ((0.9, 4.6), (2.2, 4.6), (3.7, 5.0), (5.3, 4.7), (1.6, 8.6), (2.6, 9.3), (3.9, 8.4), (0.25, 20.0), (2.9, 19.0), (3.6, 22.5), (5.0, 15.5), (4.4, 18.2)):
    on_hull('ServicePanel', (0.9, 0.65, 0.04), a, z, GRAPH_S, bevel=0.01)
    for i in range(6):
        on_hull('VentSlat', (0.74, 0.04, 0.06), a, z - 0.22 + i * 0.088, STEELD, bevel=0.0)
for k in range(18):
    a = rr.uniform(0, TAU); z = rr.uniform(12.5, 23.5)
    if abs(((a - FRONT) + math.pi) % TAU - math.pi) > 2.2: continue    # keep the back radiators clean
    on_hull('Greeble', (rr.uniform(0.25, 0.7), rr.uniform(0.2, 0.5), rr.uniform(0.06, 0.15)), a, z, rr.choice([GRAPH_S, STEELD, WHITE_S]), bevel=0.015)
for a in (math.radians(25), math.radians(205)):
    on_hull('ServiceHatch', (1.1, 1.4, 0.04), a, 5.6, WHITE_S, bevel=0.03, segs=3)
    on_hull('ServiceHatchFrame', (1.2, 1.5, 0.025), a, 5.6, GRAPH_S, bevel=0.01)
    on_hull('HatchHandle', (0.3, 0.06, 0.07), a, 5.2, SATIN, bevel=0.01)
for z in (3.9, 4.5, 5.1, 5.7):
    for s in (-1, 1):
        a = FRONT + s * 0.43
        p0 = polar(a, R + 0.04, z); p1 = polar(a, R + 0.14, z)
        for dz in (-0.1, 0.1):
            rod('Handhold', tuple(p0 + Vector((0, 0, dz))), tuple(p1 + Vector((0, 0, dz))), 0.015, SATIN, segs=8)
        rod('Handhold', tuple(p1 + Vector((0, 0, -0.1))), tuple(p1 + Vector((0, 0, 0.1))), 0.015, SATIN, segs=8)

# door frame + floodlights
dz = (DOOR_Z0 + DOOR_Z1) / 2
yf = -math.sqrt(R ** 2 - (DOOR_W / 2) ** 2)
for s in (-1, 1):
    box('DoorJamb', (0.18, 0.6, DOOR_Z1 - DOOR_Z0 + 0.18), (s * (DOOR_W / 2 + 0.09), yf - 0.08, dz), GRAPH_S, bevel=0.02)
    box('DoorJambGlow', (0.02, 0.03, DOOR_Z1 - DOOR_Z0 - 0.2), (s * (DOOR_W / 2 + 0.185), yf - 0.36, dz), CYAN, bevel=0.0)
box('DoorHeader', (DOOR_W + 0.36, 0.7, 0.2), (0, yf - 0.08, DOOR_Z1 + 0.1), GRAPH_S, bevel=0.02)
box('DoorHeaderStripe', (DOOR_W + 0.1, 0.02, 0.1), (0, yf - 0.435, DOOR_Z1 + 0.1), AMBER_HZ, bevel=0.0)
for s in (-1, 1):
    box('Floodlight', (0.4, 0.26, 0.22), (s * 1.0, yf - 0.6, DOOR_Z1 + 0.42), GRAPH_S, rot=(-0.5, 0, 0), bevel=0.03)
    box('FloodLens', (0.32, 0.02, 0.15), (s * 1.0, yf - 0.73, DOOR_Z1 + 0.35), LAMP, rot=(-0.5, 0, 0), bevel=0.0)
    rod('FloodArm', (s * 1.0, yf, DOOR_Z1 + 0.42), (s * 1.0, yf - 0.5, DOOR_Z1 + 0.42), 0.035, SATIN)
    sl = light('DoorFlood', 'SPOT', (s * 1.0, yf - 0.8, DOOR_Z1 + 0.3), 1500, '#fff4e4', size=0.1, spot=math.radians(70))
    aim(sl, (s * 0.4, -11.0, 0.0))

# ---------------------------------------------------------------- airlock at the top of the ramp, with dust-off station
BX0, BX1, BY0, BY1, BZ0, BZ1 = -1.6, 1.6, yf - 0.1, yf + 3.4, DOOR_Z0 - 0.02, DOOR_Z1 + 0.3
BYc = (BY0 + BY1) / 2
box('BayFloorPit', (BX1 - BX0, BY1 - BY0, 0.06), (0, BYc, BZ0 - 0.1), INK, bevel=0.0)
for i in range(int((BY1 - BY0 - 0.2) / 0.09)):     # grated deck (dust falls through)
    box('BayGrate', (BX1 - BX0 - 0.1, 0.03, 0.05), (0, BY0 + 0.15 + i * 0.09, BZ0 - 0.025), STEELD, bevel=0.0)
for s in (-1, 1): box('BayGrateFrame', (0.08, BY1 - BY0, 0.08), (s * (BX1 - 0.04), BYc, BZ0 - 0.04), GRAPH_S, bevel=0.01)
box('BayCeil', (BX1 - BX0, BY1 - BY0, 0.06), (0, BYc, BZ1 + 0.03), CABIN, bevel=0.0)
box('BayBack', (BX1 - BX0, 0.06, BZ1 - BZ0 + 0.2), (0, BY1 + 0.03, (BZ0 + BZ1) / 2), CABIN, bevel=0.0)
for s in (-1, 1):
    box('BayWall', (0.06, BY1 - BY0, BZ1 - BZ0 + 0.2), (s * (BX1 + 0.03), BYc, (BZ0 + BZ1) / 2), CABIN, bevel=0.0)
    box('BayFloorGlow', (0.03, BY1 - BY0 - 0.3, 0.01), (s * 1.35, BYc, BZ0 + 0.005), CYAN, bevel=0.0)
    # air-shower arch: nozzle columns + header
    AY = BY0 + 1.3
    box('AirShowerPillar', (0.24, 0.3, BZ1 - BZ0 - 0.2), (s * 1.25, AY, BZ0 + (BZ1 - BZ0 - 0.2) / 2), WHITE_S, bevel=0.04)
    for j in range(8):
        cyl('AirNozzle', 0.03, 0.08, (s * 1.11, AY, BZ0 + 0.35 + j * 0.28), SATIN, rot=(0, math.pi / 2, 0), segs=10, bevel=0.0)
    box('AirShowerGlow', (0.02, 0.04, BZ1 - BZ0 - 0.6), (s * 1.125, AY + 0.12, BZ0 + (BZ1 - BZ0 - 0.2) / 2), CYAN, bevel=0.0)
    # boot brushes (bristle blocks) + hand-brush on a hose
    box('BootBrush', (0.5, 0.7, 0.22), (s * 0.95, BY0 + 2.3, BZ0 + 0.11), GRAPH_S, bevel=0.03)
    box('BootBrushBristle', (0.42, 0.62, 0.12), (s * 0.95, BY0 + 2.3, BZ0 + 0.28), BRISTLE, bevel=0.02)
    box('BayLocker', (0.4, 0.7, 2.0), (s * 1.38, BY1 - 0.5, BZ0 + 1.0), CABIN_D, bevel=0.02)
    box('BayLockerGlow', (0.02, 0.6, 0.03), (s * 1.17, BY1 - 0.5, BZ0 + 1.8), CYAN, bevel=0.0)
box('AirShowerHeader', (2.74, 0.3, 0.22), (0, AY, BZ1 - 0.2), WHITE_S, bevel=0.04)
box('AirShowerHeaderGlow', (2.3, 0.02, 0.04), (0, AY - 0.16, BZ1 - 0.2), CYAN, bevel=0.0)
cyl('HoseReel', 0.22, 0.12, (1.2, BY0 + 2.0, BZ0 + 1.5), GRAPH_S, rot=(0, math.pi / 2, 0), segs=24, bevel=0.01)
cable('HandBrushHose', (1.13, BY0 + 2.0, BZ0 + 1.35), (0.9, BY0 + 2.3, BZ0 + 0.9), 0.02, INK, sag=0.25)
box('HandBrush', (0.08, 0.3, 0.08), (0.9, BY0 + 2.3, BZ0 + 0.86), BRISTLE, bevel=0.02)
box('BayCeilLight', (2.2, 1.0, 0.02), (0, BYc + 0.3, BZ1 - 0.01), WARM, bevel=0.0)
box('InnerHatch', (1.0, 0.05, 2.0), (0, BY1 - 0.01, BZ0 + 1.05), CABIN_D, bevel=0.03)
box('InnerHatchWin', (0.3, 0.06, 0.3), (0, BY1 - 0.02, BZ0 + 1.6), WARM, bevel=0.0)
box('InnerHatchLampOK', (0.08, 0.06, 0.08), (0.65, BY1 - 0.02, BZ0 + 1.9), M_glow('S_OkGreen', '#6ee08a', 10), bevel=0.0)
light('BayLight', 'AREA', (0, BYc + 0.3, BZ1 - 0.05), 260, '#ffd2a0', size=2.0)
light('BayFill', 'POINT', (0, BY0 + 0.7, BZ0 + 0.8), 40, '#7fe8ff', size=0.2)

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

# ---------------------------------------------------------------- landing legs (6, clear of the ramp)
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

# ---------------------------------------------------------------- deployed ramp (pivot empty at the hinge = "Ramp")
RAMP_A = math.radians(18.0); RAMP_T = 0.18; RAMP_W = 2.5
RAMP_L = (DOOR_Z0 - RAMP_T * math.cos(RAMP_A)) / math.sin(RAMP_A)
hinge = Vector((0, yf - 0.1, DOOR_Z0))
ramp = bpy.data.objects.new('Ramp', None); coll('Mine').objects.link(ramp)
ramp.location = hinge; ramp.rotation_euler = (RAMP_A, 0, 0)
def rp(name, size, loc, mat, bev=0.01, rot=(0, 0, 0)):
    o = box(name, size, loc, mat, bevel=bev, rot=rot); o.parent = ramp; return o
rp('RampDeck', (RAMP_W, RAMP_L, RAMP_T), (0, -RAMP_L / 2, -RAMP_T / 2), WHITE, 0.03)
rp('RampUnder', (RAMP_W - 0.1, RAMP_L - 1.4, 0.08), (0, -(RAMP_L - 1.4) / 2, -RAMP_T - 0.03), GRAPH, 0.01)
for i in range(int(RAMP_L / 0.36)):
    rp('RampCleat', (RAMP_W - 0.4, 0.06, 0.035), (0, -0.35 - i * 0.36, 0.017), STEELD, 0.008)
for s in (-1, 1):
    rp('RampRail', (0.14, RAMP_L, 0.18), (s * (RAMP_W / 2 - 0.02), -RAMP_L / 2, 0.07), GRAPH_S, 0.02)
    rp('RampEdgeGlow', (0.02, RAMP_L - 0.3, 0.025), (s * (RAMP_W / 2 - 0.12), -RAMP_L / 2, 0.012), CYAN, 0.0)
    rp('RampHinge', (0.36, 0.24, 0.24), (s * 0.9, -0.06, -0.12), SATIN, 0.03)
    for j in range(7):
        y = -0.6 - j * (RAMP_L - 1.0) / 6
        rp('RailPost', (0.045, 0.045, 1.0), (s * (RAMP_W / 2 - 0.02), y - 0.5 * math.sin(RAMP_A), 0.5 * math.cos(RAMP_A) + 0.14), SATIN, 0.01, rot=(-RAMP_A, 0, 0))
    rp('Handrail', (0.05, RAMP_L - 0.9, 0.05), (s * (RAMP_W / 2 - 0.02), -0.6 - (RAMP_L - 1.0) / 2 - math.sin(RAMP_A), math.cos(RAMP_A) + 0.14), SATIN, 0.02)
rp('RampSillStripe', (RAMP_W - 0.4, 0.35, 0.01), (0, -0.3, 0.004), AMBER_HZ, 0.0)
rp('RampFootStripe', (RAMP_W - 0.4, 0.4, 0.01), (0, -RAMP_L + 0.35, 0.004), AMBER_HZ, 0.0)
bpy.context.view_layer.update()
RW = ramp.matrix_world
foot_w = RW @ Vector((0, -RAMP_L, 0)); foot_y = foot_w.y
box('RampToe', (RAMP_W, 0.5, 0.04), (0, foot_y - 0.2, 0.02), AMBER_HZ, bevel=0.008)   # flat toe plate on the pad
for s in (-1, 1):   # hydraulic rams
    p0 = Vector((s * 1.48, yf + 0.15, DOOR_Z0 + 2.1)); p1 = RW @ Vector((s * (RAMP_W / 2 + 0.08), -3.2, -0.08))
    piston('RampRam', tuple(p0), tuple(p1), 0.09, GRAPH_S, SATIN, ext=0.5)
    box('RampRamMount', (0.2, 0.36, 0.36), (s * 1.48, yf + 0.08, DOOR_Z0 + 2.1), STEELD, bevel=0.03)
print('RAMP length', RAMP_L, 'foot y', foot_y, flush=True)

# ---------------------------------------------------------------- kit crates at the ramp foot (human scale)
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
crate('CrateMine', 'MINE', (-2.4, foot_y - 0.9, 0.0), 0.18)
crate('CrateRefinery', 'REFINERY', (2.5, foot_y - 0.6, 0.0), -0.22, size=(2.0, 1.2, 1.2))

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
    lt = light(name + '_Flood', 'SPOT', tuple(arm_c + inward * 0.4), 9000 if not power else 7000, '#fff1dc', size=0.3, spot=math.radians(55))
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

# astronauts (1.8 m) beside the ramp/crates and one walking down the ramp
ASTRO = [((0.6, foot_y - 2.2, 0.0), 0.35), ((-4.0, foot_y - 0.6, 0.0), -0.9), ((3.9, foot_y - 2.0, 0.0), 0.6)]
p_on = RW @ Vector((-0.45, -RAMP_L * 0.55, 0.0)); ASTRO.append(((p_on.x, p_on.y, p_on.z), 0.0))

# ================================================================ root + stage
convert_curves()
root = bpy.data.objects.new('StarterShip', None); coll('Mine').objects.link(root)
for ob in coll('Mine').objects:
    if ob is not root and ob.parent is None: ob.parent = root

PAD_R, PAD_T = 18.0, 0.2
height = build_stage(keep_flat=((0, 0, 44),))
gnd = bpy.data.objects['Ground']; gnd.location.z = -PAD_T          # level regolith; the pad slab sits ON it
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
REGO = bpy.data.materials['M_Regolith']
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
SINTER_BLK = M_paint('S_SinterBlock', '#5a5652', rough=0.85, metal=0.0, bevel=0.03, grime=0.3, grime_col='#3a3735', bump_noise=0.3)
k = 0; a = GAP1 + 0.08
while a < GAP0 + TAU - 0.08:
    box('BermBlock', (2.6, 0.5, 0.75), tuple(polar(a, 20.8, 0.375 - PAD_T + 0.0)), SINTER_BLK, rot=(0, 0, a + math.pi / 2 + rr.uniform(-0.03, 0.03)), bevel=0.04, c='Stage')
    a += 2.75 / 20.8; k += 1
world_and_sun((-0.55, -0.62, 0.56), 5.5)
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
    isship = not any(ob.name.startswith(p) for p in ('Crate', 'LightMast', 'PowerMast'))
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
if 'close' in ONLY:
    shoot(cam, os.path.join(OUT, 'turntable', 'closeup.png'), (0.0, -8.5, 4.6), (-9.5, -27.0, 3.6), 1600 if not QUICK else 640, 1000 if not QUICK else 400,
          lens=38, samples=int(A.get('cs', 96)) if not QUICK else 24)
if 'ports' in ONLY:
    shoot(cam, os.path.join(OUT, 'turntable', 'ports.png'), (0.0, -4.0, 8.25), (-1.6, -11.5, 8.0), 1200 if not QUICK else 600, 800 if not QUICK else 400, lens=55,
          samples=int(A.get('ps', 96)) if not QUICK else 24)
if 'hero' in ONLY:
    w, h = (3840, 2160) if not QUICK else (960, 540)
    shoot(cam, os.path.join(OUT, 'starter_ship_hero_3840x2160.png'), (0.5, -4.0, 18.0), (-23.0, -50.0, 9.5), w, h, lens=22,
          samples=int(A.get('hs', 64)) if not QUICK else 24)
