"""Bake the shared M_ground look (art/3d/mine_concepts/_src/mc_common.py @ 269e70f, + concept B's cool-grey ramp override)
into SEAMLESS fields for a real-time tiling ground. Every noise / voronoi is sampled on a flat torus embedded in 4D:
    (u, v) in [0,1)^2  ->  R*(cos 2pi u, sin 2pi u, cos 2pi v, sin 2pi v),  R = T / (2 pi)   (T = tile size in metres)
so the bake is exactly periodic (no mirror, no cross-fade seam) and locally isometric (1 m on the tile = 1 m of noise).
usage:
  B=/opt/blender-4.2.3-linux-x64/blender
  $B -b -P bake_ground.py -- --what detail --T 10 --res 1024 --out /tmp/ground/detail.npy
  $B -b -P bake_ground.py -- --what macro  --T 76 --res 256  --out /tmp/ground/macro.npy
then make_tiles.py (numpy: colour -> sRGB, macro normalise, height -> normal, PNG + KTX2)."""
import bpy, math, sys, os
import numpy as np
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'mine_concepts', '_src')))
from mc_common import hexc, argv
A = argv(); WHAT = A.get('what', 'detail'); T = float(A.get('T', 10)); RES = int(A.get('res', 1024)); OUT = A.get('out', '/tmp/ground/%s.npy' % WHAT)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = int(A.get('spp', 24)); sc.cycles.use_denoising = False
sc.cycles.pixel_filter_type = 'GAUSSIAN'; sc.cycles.filter_width = 1.2
sc.render.resolution_x = sc.render.resolution_y = RES; sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'Standard'; sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
sc.render.film_transparent = False
# plane larger than the frame (pixel filter reads past the border; the torus mapping is periodic anyway)
me = bpy.data.meshes.new('P'); me.from_pydata([(-0.2, -0.2, 0), (1.2, -0.2, 0), (1.2, 1.2, 0), (-0.2, 1.2, 0)], [], [(0, 1, 2, 3)])
ob = bpy.data.objects.new('P', me); sc.collection.objects.link(ob)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 1.0; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam)
cam.location = (0.5, 0.5, 5); sc.camera = cam
m = bpy.data.materials.new('Bake'); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; N.clear(); me.materials.append(m)
L = nt.links.new
def math_(op, a, b=None, clamp=False):
    n = N.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: L(v, n.inputs[i])
    return n.outputs[0]
def mr(v, a, b_, c0=0.0, c1=1.0, clamp=True):
    r = N.new('ShaderNodeMapRange'); r.clamp = clamp
    r.inputs['From Min'].default_value = a; r.inputs['From Max'].default_value = b_
    r.inputs['To Min'].default_value = c0; r.inputs['To Max'].default_value = c1; L(v, r.inputs['Value']); return r.outputs[0]
def cool(col, k=(0.93, 0.99, 1.10), gain=0.97):          # concept_b_sleek._cool: ramps -> cool grey (Jacob: no tan)
    Y = 0.2126 * col[0] + 0.7152 * col[1] + 0.0722 * col[2]; return (Y * k[0] * gain, Y * k[1] * gain, Y * k[2] * gain, 1.0)
def ramp(fac, stops, interp='EASE'):
    r = N.new('ShaderNodeValToRGB'); r.color_ramp.interpolation = interp; el = r.color_ramp.elements
    el[0].position, el[0].color = stops[0][0], cool(hexc(stops[0][1])); el[1].position, el[1].color = stops[-1][0], cool(hexc(stops[-1][1]))
    for pos, c_ in stops[1:-1]: el.new(pos).color = cool(hexc(c_))
    L(fac, r.inputs['Fac']); return r.outputs['Color']
def mix(f, c0, c1, blend='MIX'):
    x = N.new('ShaderNodeMix'); x.data_type = 'RGBA'; x.blend_type = blend
    for sock, v in ((x.inputs['Factor'], f), (x.inputs[6], c0), (x.inputs[7], c1)):
        if isinstance(v, (int, float)): sock.default_value = v
        elif isinstance(v, str): sock.default_value = hexc(v)
        elif isinstance(v, tuple): sock.default_value = v
        else: L(v, sock)
    return x.outputs[2]
# ---- torus coordinates
tc = N.new('ShaderNodeTexCoord'); sp = N.new('ShaderNodeSeparateXYZ'); L(tc.outputs['Object'], sp.inputs[0])
R = T / math.tau
def ang(s): return math_('MULTIPLY', s, math.tau)
cu, su = math_('MULTIPLY', math_('COSINE', ang(sp.outputs['X'])), R), math_('MULTIPLY', math_('SINE', ang(sp.outputs['X'])), R)
cv, sv = math_('MULTIPLY', math_('COSINE', ang(sp.outputs['Y'])), R), math_('MULTIPLY', math_('SINE', ang(sp.outputs['Y'])), R)
cmb = N.new('ShaderNodeCombineXYZ'); L(cu, cmb.inputs[0]); L(su, cmb.inputs[1]); L(cv, cmb.inputs[2])
P4 = (cmb.outputs[0], sv)
_off = [0]
def offs(P, k=None):
    """decorrelate calls: shift the 4D point by a fixed offset (still periodic)."""
    _off[0] += 1; o = (17.3 * _off[0], -9.1 * _off[0], 5.7 * _off[0]) if k is None else k
    va = N.new('ShaderNodeVectorMath'); va.operation = 'ADD'; L(P[0], va.inputs[0]); va.inputs[1].default_value = o
    return (va.outputs[0], math_('ADD', P[1], 3.3 * _off[0]))
def nz(P, scale, detail=4, rough=0.5, out='Fac'):
    P = offs(P); n = N.new('ShaderNodeTexNoise'); n.noise_dimensions = '4D'
    n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = rough
    L(P[0], n.inputs['Vector']); L(P[1], n.inputs['W']); return n.outputs[out]
def warp(P, scale, amp, ampw=None):
    c = nz(P, scale, 3, out='Color'); w = nz(P, scale, 3)
    va = N.new('ShaderNodeVectorMath'); va.operation = 'MULTIPLY_ADD'; va.inputs[1].default_value = (amp, amp, amp)
    L(c, va.inputs[0]); L(P[0], va.inputs[2])
    return (va.outputs[0], math_('ADD', P[1], math_('MULTIPLY', w, amp if ampw is None else ampw)))
def vor(P, scale, feature='F1'):
    v = N.new('ShaderNodeTexVoronoi'); v.voronoi_dimensions = '4D'; v.feature = feature; v.inputs['Scale'].default_value = scale
    L(P[0], v.inputs['Vector']); L(P[1], v.inputs['W']); return v.outputs['Distance']
emit = N.new('ShaderNodeEmission'); outn = N.new('ShaderNodeOutputMaterial'); L(emit.outputs[0], outn.inputs['Surface'])
if WHAT == 'detail':
    # ---- detail tile (T ~ 10 m): the parts of M_ground above ~1/3 m^-1. The M_ground octaves below that (base fbm 0.08,
    # patch_big 0.012, strata/patch masks 0.028-0.035) live in the macro tile, so nothing low-frequency repeats every 10 m.
    base = ramp(nz(P4, 0.32, 10, 0.6), ((0.3, '#646770'), (0.7, '#9a9da2')))       # M_ground base ramp, upper octaves only
    base = mix(0.45, base, cool(hexc('#7c7f84')))                                   # (contrast of the dropped octaves -> macro)
    # strata: domain-warped fbm beds (two warp octaves), uneven thickness, shown only in broken patches (as in M_ground)
    Pw = warp(warp(P4, 0.06, 2.4), 0.2, 0.9)
    beds = nz(Pw, 0.42, 5, 0.6)
    strata = ramp(beds, ((0.28, '#45484d'), (0.4, '#6c6f74'), (0.46, '#55585d'), (0.55, '#8b8e93'), (0.62, '#5e6166'), (0.74, '#a0a3a8')))
    # exposed rock patches on flat ground (M_ground: rock = steep|high x patch; flat tile -> a patchy exposure)
    rock = math_('MULTIPLY', mr(nz(P4, 0.21, 3), 0.40, 0.62, 0.0, 1.0), 0.55)
    smask = mr(nz(P4, 0.28, 3), 0.42, 0.62)
    face = mix(math_('MULTIPLY', math_('MULTIPLY', rock, smask), 0.6), base, strata)
    # voronoi rock: warped cells (tone) + fracture edges, M_ground scale 0.32 / warp 3.5
    Pv = warp(P4, 0.18, 3.5, 1.6)
    cell = mr(vor(Pv, 0.32), 0.0, 1.0, 0.86, 1.08)
    edge = vor(Pv, 0.32, 'DISTANCE_TO_EDGE')
    crack = math_('MULTIPLY', mr(edge, 0.0, 0.03, 1.0, 0.0), mr(nz(P4, 0.21, 3), 0.5, 0.66))     # sparse, broken fractures
    cc = N.new('ShaderNodeCombineColor')
    for i in range(3): L(cell, cc.inputs[i])
    face = mix(rock, face, cc.outputs[0], 'MULTIPLY')
    face = mix(math_('MULTIPLY', crack, math_('ADD', math_('MULTIPLY', rock, 0.35), 0.12)), face, cool(hexc('#3a3c40')))
    # height for the normal map: fine regolith grain + crack grooves + bed ledges on the rock (M_ground bump input)
    grain = nz(P4, 3.0, 8, 0.6)
    h = math_('ADD', grain, math_('MULTIPLY', math_('SUBTRACT', math_('MULTIPLY', beds, 0.8), math_('MULTIPLY', crack, 0.9)), math_('ADD', rock, 0.15)))
    PASSES = [('color', face), ('height', h)]
else:
    # ---- macro tile (T ~ 76 m): M_ground's low octaves -> one luminance field (normalised to mean 1 in make_tiles.py)
    a = nz(P4, 0.08, 3, 0.6); b = nz(P4, 0.024, 3, 0.5); c = nz(P4, 0.035, 3)
    cm = N.new('ShaderNodeCombineColor'); L(a, cm.inputs[0]); L(b, cm.inputs[1]); L(c, cm.inputs[2])
    PASSES = [('fields', cm.outputs[0])]
res = {}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
for nm, sock in PASSES:
    for l in list(emit.inputs['Color'].links): nt.links.remove(l)
    if sock.type == 'VALUE':
        cc = N.new('ShaderNodeCombineColor')
        for i in range(3): L(sock, cc.inputs[i])
        sock = cc.outputs[0]
    L(sock, emit.inputs['Color'])
    fp = OUT.replace('.npy', '_%s.exr' % nm); sc.render.filepath = fp; bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(fp); a_ = np.array(im.pixels[:], dtype=np.float32).reshape(RES, RES, 4)[::-1, :, :3]   # top row first
    res[nm] = a_; bpy.data.images.remove(im)
np.save(OUT, res, allow_pickle=True)
print('BAKED', WHAT, T, RES, {k: (float(v.mean()), float(v.min()), float(v.max())) for k, v in res.items()})
