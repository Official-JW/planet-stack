"""Planet Stack - Mine A concept masters: shared Blender 4.2 helpers (Z-up, camera looks from -Y = front)."""
import bpy, bmesh, math, random, os, sys
from mathutils import Vector, Matrix, Euler, noise

R = random.Random(11)
TAU = 2 * math.pi

def hexc(h, a=1.0):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c) + (a,)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for n in ('Mine', 'Stage'):
        c = bpy.data.collections.new(n); sc.collection.children.link(c)
    return sc

def coll(name): return bpy.data.collections[name]

# ------------------------------------------------------------------ materials
def _nodes(m):
    m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; return nt, b

def link(nt, a, b): nt.links.new(a, b)

def M_paint(name, color, rough=0.45, metal=0.2, grime=0.0, grime_col='#2a2622', wear=0.0, wear_col='#9aa0a6',
            hazard=None, hazard_scale=2.0, panel=None, coat=0.0, bevel=0.015, bump_noise=0.0, dirt_scale=2.5):
    m = bpy.data.materials.new(name); nt, b = _nodes(m)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    base = nt.nodes.new('ShaderNodeRGB'); base.outputs[0].default_value = hexc(color)
    col_out = base.outputs[0]
    if hazard:   # diagonal stripes
        wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'DIAGONAL'
        wv.inputs['Scale'].default_value = hazard_scale
        link(nt, tc.outputs['Object'], wv.inputs['Vector'])
        ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation = 'CONSTANT'
        ramp.color_ramp.elements[0].color = hexc(hazard[0]); ramp.color_ramp.elements[1].position = 0.5
        ramp.color_ramp.elements[1].color = hexc(hazard[1])
        link(nt, wv.outputs['Fac'], ramp.inputs['Fac']); col_out = ramp.outputs['Color']
    nrm = None
    bv = nt.nodes.new('ShaderNodeBevel'); bv.inputs['Radius'].default_value = bevel; nrm = bv.outputs['Normal']
    if grime > 0:
        ao = nt.nodes.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = 0.6; ao.samples = 8
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = dirt_scale; nz.inputs['Detail'].default_value = 8
        link(nt, tc.outputs['Object'], nz.inputs['Vector'])
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
        link(nt, ao.outputs['AO'], inv.inputs[1])
        mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
        link(nt, inv.outputs[0], mul.inputs[0]); link(nt, nz.outputs['Fac'], mul.inputs[1])
        r2 = nt.nodes.new('ShaderNodeMapRange'); r2.inputs['From Min'].default_value = 0.0; r2.inputs['From Max'].default_value = 0.35
        r2.inputs['To Max'].default_value = grime
        link(nt, mul.outputs[0], r2.inputs['Value'])
        nz2 = nt.nodes.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = dirt_scale * 4; nz2.inputs['Detail'].default_value = 10
        link(nt, tc.outputs['Object'], nz2.inputs['Vector'])
        r3 = nt.nodes.new('ShaderNodeMapRange'); r3.inputs['From Min'].default_value = 0.55; r3.inputs['From Max'].default_value = 0.75
        r3.inputs['To Max'].default_value = grime * 0.6; link(nt, nz2.outputs['Fac'], r3.inputs['Value'])
        add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'; add.use_clamp = True
        link(nt, r2.outputs[0], add.inputs[0]); link(nt, r3.outputs[0], add.inputs[1])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        link(nt, add.outputs[0], mx.inputs['Factor']); link(nt, col_out, mx.inputs[6]); mx.inputs[7].default_value = hexc(grime_col)
        col_out = mx.outputs[2]
        rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = rough; rr.inputs['To Max'].default_value = min(1, rough + 0.35)
        link(nt, add.outputs[0], rr.inputs['Value']); link(nt, rr.outputs[0], b.inputs['Roughness'])
    else:
        b.inputs['Roughness'].default_value = rough
    if wear > 0:   # convex edge wear -> bare steel
        ao2 = nt.nodes.new('ShaderNodeAmbientOcclusion'); ao2.inside = True; ao2.inputs['Distance'].default_value = 0.05; ao2.samples = 8
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 18; nz.inputs['Detail'].default_value = 6
        link(nt, tc.outputs['Object'], nz.inputs['Vector'])
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
        link(nt, ao2.outputs['AO'], inv.inputs[1])
        mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; link(nt, inv.outputs[0], mul.inputs[0]); link(nt, nz.outputs['Fac'], mul.inputs[1])
        st = nt.nodes.new('ShaderNodeMapRange'); st.inputs['From Min'].default_value = 0.25 * (1 - wear); st.inputs['From Max'].default_value = 0.3 * (1 - wear) + 0.05
        link(nt, mul.outputs[0], st.inputs['Value'])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        link(nt, st.outputs[0], mx.inputs['Factor']); link(nt, col_out, mx.inputs[6]); mx.inputs[7].default_value = hexc(wear_col)
        col_out = mx.outputs[2]
        mm = nt.nodes.new('ShaderNodeMapRange'); mm.inputs['To Min'].default_value = metal; mm.inputs['To Max'].default_value = 1.0
        link(nt, st.outputs[0], mm.inputs['Value']); link(nt, mm.outputs[0], b.inputs['Metallic'])
    else:
        b.inputs['Metallic'].default_value = metal
    link(nt, col_out, b.inputs['Base Color'])
    if panel or bump_noise:
        bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Distance'].default_value = 0.02
        link(nt, nrm, bump.inputs['Normal'])
        if panel:
            br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = panel
            br.inputs['Mortar Size'].default_value = 0.012; br.offset = 0.0; br.inputs['Bias'].default_value = 0
            br.inputs['Brick Width'].default_value = 1.0; br.inputs['Row Height'].default_value = 0.5
            br.inputs['Color1'].default_value = (1, 1, 1, 1); br.inputs['Color2'].default_value = (1, 1, 1, 1); br.inputs['Mortar'].default_value = (0, 0, 0, 1)
            link(nt, tc.outputs['Object'], br.inputs['Vector'])
            link(nt, br.outputs['Fac'], bump.inputs['Height']); bump.invert = True
            bump.inputs['Strength'].default_value = 0.6
        else:
            nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 40; nz.inputs['Detail'].default_value = 10
            link(nt, tc.outputs['Object'], nz.inputs['Vector']); link(nt, nz.outputs['Fac'], bump.inputs['Height'])
            bump.inputs['Strength'].default_value = bump_noise
        nrm = bump.outputs['Normal']
    link(nt, nrm, b.inputs['Normal'])
    if coat:
        b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.08
    m.diffuse_color = hexc(color)
    return m

def M_glow(name, color, strength=8.0):
    m = bpy.data.materials.new(name); nt, b = _nodes(m)
    b.inputs['Base Color'].default_value = hexc(color); b.inputs['Emission Color'].default_value = hexc(color)
    b.inputs['Emission Strength'].default_value = strength; m.diffuse_color = hexc(color)
    return m

def M_glass(name, tint='#9fdcff', rough=0.03):
    m = bpy.data.materials.new(name); nt, b = _nodes(m)
    b.inputs['Base Color'].default_value = hexc(tint); b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = rough; b.inputs['IOR'].default_value = 1.45
    return m

def M_he3(name='M_He3'):
    """glowing blue Helium-3 crystal with inner variation"""
    m = bpy.data.materials.new(name); nt, b = _nodes(m)
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6
    link(nt, tc.outputs['Object'], nz.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = hexc('#0b5cff'); ramp.color_ramp.elements[1].color = hexc('#47d8ff')
    link(nt, nz.outputs['Fac'], ramp.inputs['Fac'])
    link(nt, ramp.outputs['Color'], b.inputs['Base Color']); link(nt, ramp.outputs['Color'], b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value = 2.6; b.inputs['Roughness'].default_value = 0.1
    b.inputs['Transmission Weight'].default_value = 0.3
    m.diffuse_color = hexc('#3ad0ff'); return m

def M_rock(name, c1='#686a6d', c2='#8c8e91', vein=None):
    m = bpy.data.materials.new(name); nt, b = _nodes(m)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3; nz.inputs['Detail'].default_value = 10
    link(nt, tc.outputs['Object'], nz.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = hexc(c1); ramp.color_ramp.elements[1].color = hexc(c2)
    link(nt, nz.outputs['Fac'], ramp.inputs['Fac']); link(nt, ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.9
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.5
    nz2 = nt.nodes.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 12; nz2.inputs['Detail'].default_value = 12
    link(nt, tc.outputs['Object'], nz2.inputs['Vector']); link(nt, nz2.outputs['Fac'], bump.inputs['Height']); link(nt, bump.outputs['Normal'], b.inputs['Normal'])
    if vein:   # sparse glowing seams: thin voronoi edges, warped, masked to ~25% of the surface
        warp = nt.nodes.new('ShaderNodeTexNoise'); warp.inputs['Scale'].default_value = 1.2; warp.inputs['Detail'].default_value = 3
        link(nt, tc.outputs['Object'], warp.inputs['Vector'])
        vm = nt.nodes.new('ShaderNodeVectorMath'); vm.operation = 'MULTIPLY_ADD'; vm.inputs[1].default_value = (0.6, 0.6, 0.6)
        link(nt, warp.outputs['Color'], vm.inputs[0]); link(nt, tc.outputs['Object'], vm.inputs[2])
        v = nt.nodes.new('ShaderNodeTexVoronoi'); v.feature = 'DISTANCE_TO_EDGE'; v.inputs['Scale'].default_value = 1.6
        link(nt, vm.outputs[0], v.inputs['Vector'])
        r = nt.nodes.new('ShaderNodeMapRange'); r.inputs['From Min'].default_value = 0.012; r.inputs['From Max'].default_value = 0.0
        r.inputs['To Max'].default_value = 2.2
        link(nt, v.outputs['Distance'], r.inputs['Value'])
        mk = nt.nodes.new('ShaderNodeTexNoise'); mk.inputs['Scale'].default_value = 0.9; mk.inputs['Detail'].default_value = 2
        link(nt, tc.outputs['Object'], mk.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.52; mr.inputs['From Max'].default_value = 0.62
        link(nt, mk.outputs['Fac'], mr.inputs['Value'])
        mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
        link(nt, r.outputs[0], mul.inputs[0]); link(nt, mr.outputs[0], mul.inputs[1])
        b.inputs['Emission Color'].default_value = hexc(vein); link(nt, mul.outputs[0], b.inputs['Emission Strength'])
    m.diffuse_color = hexc(c1); return m

def M_ground():
    """cool grey lunar regolith/rock. Flat ground = fine regolith; slopes = fractured rock with faint, BROKEN strata.
    (The old version drove a Wave BANDS texture straight up Z: one sine frequency -> evenly spaced horizontal stripes.
    Now the strata are an fbm sampled along a domain-warped height, with uneven bed thickness, beds that pinch out
    along the ridge, patchy masking, and voronoi rock fractures on top.)"""
    m = bpy.data.materials.new('M_Regolith'); nt, b = _nodes(m); N = nt.nodes
    tc = N.new('ShaderNodeTexCoord'); P = tc.outputs['Object']
    def nz(vec, scale, detail=4, rough=0.5, out='Fac'):
        n = N.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough; link(nt, vec, n.inputs['Vector']); return n.outputs[out]
    def mr(v, a, b_, c0=0.0, c1=1.0, clamp=True):
        r = N.new('ShaderNodeMapRange'); r.clamp = clamp
        r.inputs['From Min'].default_value = a; r.inputs['From Max'].default_value = b_
        r.inputs['To Min'].default_value = c0; r.inputs['To Max'].default_value = c1; link(nt, v, r.inputs['Value']); return r.outputs[0]
    def math_(op, x, y, clamp=False):
        n = N.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate((x, y)):
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: link(nt, v, n.inputs[i])
        return n.outputs[0]
    def ramp(fac, stops, interp='EASE'):
        r = N.new('ShaderNodeValToRGB'); r.color_ramp.interpolation = interp; el = r.color_ramp.elements
        el[0].position, el[0].color = stops[0][0], hexc(stops[0][1]); el[1].position, el[1].color = stops[-1][0], hexc(stops[-1][1])
        for pos, c_ in stops[1:-1]: el.new(pos).color = hexc(c_)
        link(nt, fac, r.inputs['Fac']); return r.outputs['Color']
    def mix(f, c0, c1, blend='MIX'):
        x = N.new('ShaderNodeMix'); x.data_type = 'RGBA'; x.blend_type = blend
        for sock, v in ((x.inputs['Factor'], f), (x.inputs[6], c0), (x.inputs[7], c1)):
            if isinstance(v, (int, float)): sock.default_value = v
            elif isinstance(v, str): sock.default_value = hexc(v)
            else: link(nt, v, sock)
        return x.outputs[2]
    sp = N.new('ShaderNodeSeparateXYZ'); link(nt, P, sp.inputs[0])
    geo = N.new('ShaderNodeNewGeometry'); sn = N.new('ShaderNodeSeparateXYZ'); link(nt, geo.outputs['Normal'], sn.inputs[0])
    # base regolith: cool neutral grey, large soft patches + mid-scale mottling
    base = ramp(nz(P, 0.08, 12, 0.6), ((0.3, '#646770'), (0.7, '#9a9da2')))
    patch_big = mr(nz(P, 0.012, 3, 0.5), 0.35, 0.65)
    base = mix(math_('MULTIPLY', patch_big, 0.35), base, '#7c7f84')
    # strata: domain-warped height (two octaves of warp) -> 1-D fbm => beds of uneven thickness/spacing
    w1 = mr(nz(P, 0.02, 3), 0.0, 1.0, -4.0, 4.0, clamp=False)
    w2 = mr(nz(P, 0.07, 4), 0.0, 1.0, -1.6, 1.6, clamp=False)
    dip = math_('MULTIPLY', sp.outputs['X'], 0.035)                               # gentle dip so beds aren't level
    zz = math_('ADD', math_('ADD', math_('ADD', sp.outputs['Z'], w1), w2), dip)
    cz = N.new('ShaderNodeCombineXYZ'); link(nt, math_('MULTIPLY', zz, 0.23), cz.inputs['Z']); link(nt, math_('MULTIPLY', sp.outputs['X'], 0.045), cz.inputs['X'])   # beds break up laterally every ~20 m
    link(nt, math_('ADD', math_('MULTIPLY', sp.outputs['Y'], 0.045), mr(nz(P, 0.015, 2), 0.0, 1.0, 0.0, 2.2)), cz.inputs['Y'])   # + drift: beds pinch out
    beds = nz(cz.outputs[0], 1.0, 5, 0.6)
    strata = ramp(beds, ((0.28, '#45484d'), (0.4, '#6c6f74'), (0.46, '#55585d'), (0.55, '#8b8e93'), (0.62, '#5e6166'), (0.74, '#a0a3a8')))
    # fractured rock: voronoi cells (tone) + cracks (dark edges), warped so cells aren't round
    wv = N.new('ShaderNodeVectorMath'); wv.operation = 'MULTIPLY_ADD'; wv.inputs[1].default_value = (3.5, 3.5, 1.6)
    link(nt, nz(P, 0.18, 3, out='Color'), wv.inputs[0]); link(nt, P, wv.inputs[2])
    vc = N.new('ShaderNodeTexVoronoi'); vc.inputs['Scale'].default_value = 0.32; link(nt, wv.outputs[0], vc.inputs['Vector'])
    ve = N.new('ShaderNodeTexVoronoi'); ve.feature = 'DISTANCE_TO_EDGE'; ve.inputs['Scale'].default_value = 0.32; link(nt, wv.outputs[0], ve.inputs['Vector'])
    crack = math_('MULTIPLY', mr(ve.outputs['Distance'], 0.0, 0.03, 1.0, 0.0), mr(nz(P, 0.07, 3), 0.5, 0.66))   # sparse, broken fractures
    cell = mr(vc.outputs['Distance'], 0.0, 1.0, 0.86, 1.08)
    # where the rock shows: steep faces and higher ground, patchy (bare regolith drapes between outcrops)
    steep = mr(sn.outputs['Z'], 0.97, 0.80)
    high = mr(sp.outputs['Z'], 1.0, 6.0, 0.0, 0.5)
    patch = mr(nz(P, 0.035, 3), 0.36, 0.58, 0.25, 1.0)
    rock = math_('MULTIPLY', math_('MAXIMUM', steep, high), patch, clamp=True)
    smask = mr(nz(P, 0.028, 3), 0.42, 0.62)                                        # strata only show in broken patches
    face = mix(math_('MULTIPLY', math_('MULTIPLY', rock, smask), 0.6), base, strata)   # subtle (max ~60%)
    cc = N.new('ShaderNodeCombineColor')
    for i in range(3): link(nt, cell, cc.inputs[i])
    face = mix(rock, face, cc.outputs[0], 'MULTIPLY')
    face = mix(math_('MULTIPLY', crack, math_('MULTIPLY', rock, 0.35)), face, '#3a3c40')
    link(nt, face, b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.97
    # bump: fine regolith grain everywhere + crack grooves and bed ledges on the rock faces (hard sun shadows)
    h = math_('ADD', nz(P, 3.0, 14, 0.6), math_('MULTIPLY', math_('SUBTRACT', math_('MULTIPLY', beds, 0.8), math_('MULTIPLY', crack, 0.9)), rock))
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.4; bump.inputs['Distance'].default_value = 0.08
    link(nt, h, bump.inputs['Height']); link(nt, bump.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = hexc('#7c7f84')
    return m

# ------------------------------------------------------------------ mesh helpers
def _obj(bm, name, mat, c='Mine', smooth=True, bevel=0.0, segs=2, angle=35, parent=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); coll(c).objects.link(ob)
    if mat: me.materials.append(mat)
    if bevel > 0:
        md = ob.modifiers.new('Bevel', 'BEVEL'); md.width = bevel; md.segments = segs
        md.limit_method = 'ANGLE'; md.angle_limit = math.radians(angle); md.harden_normals = True
        md.use_clamp_overlap = True
    elif smooth:
        md = ob.modifiers.new('Smooth', 'NODES') if False else None
        for p in me.polygons: p.use_smooth = True
        _sharp(me, angle)
    if parent: ob.parent = parent
    return ob

def _sharp(me, angle):
    bm = bmesh.new(); bm.from_mesh(me)
    for e in bm.edges:
        if (not e.is_manifold) or e.calc_face_angle(0) > math.radians(angle): e.smooth = False
    bm.to_mesh(me); bm.free()

def mat4(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    return Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*scale, 1))

def box(name, size, loc, mat, rot=(0, 0, 0), bevel=0.02, segs=2, c='Mine'):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.transform(bm, matrix=mat4(loc, rot, size), verts=bm.verts)
    return _obj(bm, name, mat, c, bevel=bevel, segs=segs)

def cyl(name, r, depth, loc, mat, rot=(0, 0, 0), segs=24, bevel=0.01, r2=None, c='Mine', caps=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    bmesh.ops.transform(bm, matrix=mat4(loc, rot), verts=bm.verts)
    return _obj(bm, name, mat, c, bevel=bevel, segs=2, angle=40)

def sphere(name, r, loc, mat, scale=(1, 1, 1), sub=3, jitter=0.0, c='Mine', smooth=True, seed=None, rot=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    if jitter:
        rr = random.Random(seed if seed is not None else R.random())
        off = Vector((rr.random() * 50, rr.random() * 50, rr.random() * 50))
        for v in bm.verts: v.co *= 1 + jitter * noise.noise(v.co * 2.2 / r + off)
    bmesh.ops.transform(bm, matrix=mat4(loc, rot, scale), verts=bm.verts)
    ob = _obj(bm, name, mat, c, smooth=smooth, angle=180 if smooth else 0)
    return ob

def frame_from(p0, p1, up=Vector((0, 0, 1))):
    a, b = Vector(p0), Vector(p1); x = (b - a); L = x.length; x.normalize()
    if abs(x.dot(up)) > 0.97: up = Vector((1, 0, 0)) if abs(x.x) < 0.9 else Vector((0, 1, 0))
    y = up.cross(x).normalized(); z = x.cross(y).normalized()
    return a, b, L, Matrix((x, y, z)).transposed()

def beam(name, p0, p1, w, h, mat, bevel=0.01, c='Mine', up=Vector((0, 0, 1))):
    a, b, L, Rm = frame_from(p0, p1, up)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ Rm.to_4x4() @ Matrix.Diagonal((L, w, h, 1)), verts=bm.verts)
    return _obj(bm, name, mat, c, bevel=bevel)

def rod(name, p0, p1, r, mat, segs=16, bevel=0.005, c='Mine', r2=None):
    a, b, L, Rm = frame_from(p0, p1)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=L)
    # cone axis is Z -> map to X of frame
    M = Matrix.Translation((a + b) / 2) @ Rm.to_4x4() @ Matrix.Rotation(math.pi / 2, 4, 'Y')
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return _obj(bm, name, mat, c, bevel=bevel, angle=40)

def ibeam(name, p0, p1, w, h, mat, c='Mine', t=None):
    """I-beam section: web + 2 flanges, joined."""
    t = t or max(0.03, w * 0.18)
    a, b, L, Rm = frame_from(p0, p1)
    bm = bmesh.new()
    for (sz, off) in (((L, t, h), (0, 0, 0)), ((L, w, t), (0, 0, h / 2 - t / 2)), ((L, w, t), (0, 0, -h / 2 + t / 2))):
        tmp = bmesh.ops.create_cube(bm, size=1)
        bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ Rm.to_4x4() @ Matrix.Translation(off) @ Matrix.Diagonal((*sz, 1)), verts=tmp['verts'])
    return _obj(bm, name, mat, c, bevel=0.006)

def piston(name, p0, p1, r, mat_body, mat_rod, ext=0.55, c='Mine'):
    """hydraulic cylinder from p0 (body) to p1 (rod end)."""
    a, b = Vector(p0), Vector(p1); d = b - a
    mid = a + d * ext
    o1 = rod(name + '_body', a, mid, r, mat_body, c=c)
    o2 = rod(name + '_rod', mid - d.normalized() * 0.1, b, r * 0.5, mat_rod, c=c)
    o3 = rod(name + '_gland', mid - d.normalized() * 0.06, mid + d.normalized() * 0.04, r * 1.12, mat_body, c=c)
    for p in (a, b):
        sphere(name + '_eye', r * 0.9, p, mat_body, sub=2, c=c)
    return [o1, o2, o3]

def curve_tube(name, pts, r, mat, c='Mine', res=4, closed=False):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    sp.use_cyclic_u = closed
    ob = bpy.data.objects.new(name, cu); coll(c).objects.link(ob); cu.materials.append(mat)
    return ob

def cable(name, p0, p1, r, mat, sag=0.4, n=24, c='Mine', lateral=(0, 0, 0)):
    a, b = Vector(p0), Vector(p1); pts = []
    for i in range(n + 1):
        t = i / n; p = a.lerp(b, t)
        p.z -= sag * 4 * t * (1 - t); p += Vector(lateral) * math.sin(math.pi * t)
        pts.append(tuple(p))
    return curve_tube(name, pts, r, mat, c)

def text(name, body, loc, rot, size, mat, extrude=0.004, c='Mine', align='CENTER'):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.size = size; cu.extrude = extrude
    cu.align_x = align; cu.align_y = 'CENTER'
    ob = bpy.data.objects.new(name, cu); coll(c).objects.link(ob); ob.location = loc; ob.rotation_euler = rot
    cu.materials.append(mat); return ob

def instance(src, name, loc, rot=(0, 0, 0), scale=(1, 1, 1), c='Mine'):
    ob = bpy.data.objects.new(name, src.data); coll(c).objects.link(ob)
    ob.location = loc; ob.rotation_euler = rot; ob.scale = scale
    for m in src.modifiers:
        nm = ob.modifiers.new(m.name, m.type)
        for k in ('width', 'segments', 'limit_method', 'angle_limit', 'harden_normals', 'use_clamp_overlap'):
            if hasattr(m, k): setattr(nm, k, getattr(m, k))
    return ob

def bolts(name, mat, pts, r=0.03, normal_rot=(0, 0, 0), c='Mine'):
    src = cyl(name + '_src', r, r * 0.8, (0, 0, -100), mat, segs=6, bevel=0.0, c=c)
    src.rotation_euler = normal_rot
    out = [instance(src, name, p, normal_rot, c=c) for p in pts]
    bpy.data.objects.remove(src)
    return out

def stadium_path(cx, cz, length, radius, n):
    """points along a stadium (track) loop in the X-Z plane, returns (pos, angle)."""
    straight = length - 2 * radius; per = 2 * straight + TAU * radius; out = []
    for i in range(n):
        s = per * i / n
        if s < straight: out.append(((cx - straight / 2 + s, cz + radius), 0))
        elif s < straight + math.pi * radius:
            a = (s - straight) / radius; out.append(((cx + straight / 2 + radius * math.sin(a), cz + radius * math.cos(a)), -a))
        elif s < 2 * straight + math.pi * radius:
            s2 = s - straight - math.pi * radius; out.append(((cx + straight / 2 - s2, cz - radius), -math.pi))
        else:
            a = (s - 2 * straight - math.pi * radius) / radius; out.append(((cx - straight / 2 - radius * math.sin(a), cz - radius * math.cos(a)), -math.pi - a))
    return out

# ------------------------------------------------------------------ ore
def ore_chunks(prefix, center, radius, count, mats, height=0.0, size=(0.12, 0.3), heap=0.0, c='Mine', seed=1, zfun=None):
    """mats: list of (material, weight, kind) kind in he3/pt/rock"""
    rr = random.Random(seed); out = []
    tot = sum(w for _, w, _ in mats)
    for i in range(count):
        a = rr.uniform(0, TAU); d = radius * math.sqrt(rr.random())
        x, y = center[0] + d * math.cos(a), center[1] + d * math.sin(a)
        z = center[2] + height + heap * (1 - (d / radius) ** 2) if zfun is None else zfun(x, y)
        pick = rr.uniform(0, tot)
        for m, w, kind in mats:
            pick -= w
            if pick <= 0: break
        s = rr.uniform(*size)
        if kind == 'he3':
            ob = sphere(f'{prefix}_he3', s * 0.55, (x, y, z + s * 0.4), m, scale=(0.7, 0.7, 1.6), sub=1, jitter=0.25, smooth=False,
                        seed=rr.random(), rot=(rr.uniform(-0.6, 0.6), rr.uniform(-0.6, 0.6), rr.uniform(0, TAU)), c=c)
        else:
            ob = sphere(f'{prefix}_{kind}', s * 0.5, (x, y, z + s * 0.2), m, scale=(1, 0.85, 0.7), sub=1, jitter=0.35,
                        smooth=(kind == 'pt'), seed=rr.random(), rot=(rr.random(), rr.random(), rr.random()), c=c)
        out.append(ob)
    return out

def heap(name, center, radius, h, mat, c='Mine', seed=3, sq=None):
    """mound mesh (round or square footprint sq=(hx,hy))."""
    bm = bmesh.new(); n = 24
    rr = random.Random(seed); off = Vector((rr.random() * 9, rr.random() * 9, 0))
    verts = {}
    for i in range(n + 1):
        for j in range(n + 1):
            u, v = -1 + 2 * i / n, -1 + 2 * j / n
            if sq: x, y = u * sq[0], v * sq[1]; dd = max(abs(u), abs(v))
            else:
                x, y = u * radius, v * radius; dd = math.hypot(u, v)
                if dd > 1: x, y = x / dd, y / dd; dd = 1
            z = h * max(0, 1 - dd ** 2) + (0.12 * h * noise.noise(Vector((x, y, 0)) * 1.7 + off) if dd < 1 else 0)
            verts[i, j] = bm.verts.new((center[0] + x, center[1] + y, center[2] + z))
    for i in range(n):
        for j in range(n):
            bm.faces.new((verts[i, j], verts[i + 1, j], verts[i + 1, j + 1], verts[i, j + 1]))
    bmesh.remove_doubles if False else None
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    return _obj(bm, name, mat, c, smooth=True, angle=180)

# ------------------------------------------------------------------ stage: ground, craters, strata, sky, sun, astronaut
def build_stage(keep_flat=((0, 0, 16),), seed=5):
    c = 'Stage'; rr = random.Random(seed)
    size, n = 260.0, 420
    craters = [(-30, 96, 6), (26, 101, 8), (62, 90, 5), (-72, 108, 9), (4, 119, 7), (-48, 84, 3.5), (88, 112, 6.5), (-96, 92, 4.5),
               (-26, -14, 6.5), (30, -8, 9), (-40, 22, 12), (18, 34, 7), (44, 30, 5), (-12, -40, 8), (34, -36, 11), (-58, -6, 7),
               (8, -26, 3.2), (-20, 16, 2.6), (24, 14, 2.4), (-30, 0, 3.0), (14, -20, 2.0)]
    def fbm(x, y, oct=4, o=0.0):
        a, f, t = 1.0, 1.0, 0.0
        for _ in range(oct):
            t += a * noise.noise(Vector((x * f, y * f, o))); a *= 0.5; f *= 2.03
        return t
    def ridged(x, y, o=0.0):
        return (1 - abs(noise.noise(Vector((x, y, o))))) ** 2
    def hills(x, y):
        edge = 70 + 16 * fbm(x * 0.012, 0.3, 3, 11) + 5 * noise.noise(Vector((x * 0.07, 2.2, 4)))
        ys = y - edge
        if ys <= -4: return 0.0
        width = 20 + 12 * fbm(x * 0.02, 1.7, 2, 21)            # slope run varies along the ridge
        peak = 9 + 9 * fbm(x * 0.016, 5.1, 3, 31) + 6 * ridged(x * 0.022, 0.4, 41)  # uneven summit heights
        t = max(0.0, (ys + 4) / max(8.0, width))
        t += 0.10 * noise.noise(Vector((x * 0.09, y * 0.09, 51)))  # broken, wandering slope
        t = min(max(t, 0.0), 1.6)
        rise = smooth01(min(t, 1.0), 0.5)
        # one or two irregular benches where the slope breaks (not evenly spaced)
        b1 = 0.35 + 0.16 * noise.noise(Vector((x * 0.03, 61, 0)))
        rise += 0.09 * math.tanh((t - b1) * 14) * max(0.0, 0.3 + 0.7 * noise.noise(Vector((x * 0.05, 71, 0))))  # bench fades in/out
        z = peak * max(rise, 0.0)
        # rolling secondary ridges beyond the crest
        if t > 0.8:
            z += (t - 0.8) * 10 * (0.5 * ridged(x * 0.03, y * 0.03, 81) + 0.4 * fbm(x * 0.04, y * 0.04, 3, 91))
        # soft erosion gullies running downslope + small-scale roughness
        g = ridged(x * 0.22, y * 0.035, 101) * math.sin(math.pi * min(t, 1.0))
        z -= 1.1 * g
        z += 0.5 * fbm(x * 0.12, y * 0.12, 3, 111) * min(t, 1.0)
        # rocky buttresses / outcrops so the face isn't a smooth curtain
        z += 1.2 * ridged(x * 0.08, y * 0.05, 121) * math.sin(math.pi * min(t, 1.0)) * (0.5 + 0.5 * noise.noise(Vector((x * 0.02, 131, 0))))
        return max(z, 0.0) if ys > -4 else 0.0
    def height(x, y):
        z = 0.35 * noise.noise(Vector((x * 0.03, y * 0.03, 0.5))) + 0.08 * noise.noise(Vector((x * 0.2, y * 0.2, 1.5)))
        for cx, cy, r in craters:
            d = math.hypot(x - cx, y - cy) / r
            if d < 1.6:
                bowl = -0.28 * r * max(0, 1 - d * d) ** 1.2 if d < 1 else 0
                rim = 0.1 * r * math.exp(-((d - 1.0) / 0.18) ** 2)
                z += bowl + rim
        # irregular lunar ridgeline behind the mine: uneven heights/spacing, broken slopes, soft erosion
        z += hills(x, y)
        for kx, ky, kr in keep_flat:
            d = math.hypot(x - kx, y - ky)
            if d < kr: z *= (d / kr) ** 3
        return z
    bm = bmesh.new(); vs = {}
    for i in range(n + 1):
        for j in range(n + 1):
            x = -size / 2 + size * i / n; y = -size / 2 + size * j / n
            vs[i, j] = bm.verts.new((x, y, height(x, y)))
    for i in range(n):
        for j in range(n):
            bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
    g = _obj(bm, 'Ground', M_ground(), c, smooth=True, angle=180)
    # boulders
    rockm = M_rock('M_Boulder')
    for k in range(70):
        a = rr.uniform(0, TAU); d = rr.uniform(17, 70); s = rr.uniform(0.15, 1.3) * (1 if rr.random() < 0.85 else 2.2)
        x, y = d * math.cos(a), d * math.sin(a) * 0.9
        sphere('boulder', s, (x, y, height(x, y) + s * 0.15), rockm, scale=(1.2, 1, 0.65), sub=2, jitter=0.4, smooth=False,
               seed=rr.random(), rot=(0, 0, rr.uniform(0, TAU)), c=c)
    for k in range(46):   # scattered boulders on the distant slopes
        x = rr.uniform(-115, 125); y = rr.uniform(74, 124); s = rr.uniform(0.6, 2.4)
        sphere('slope_boulder', s, (x, y, height(x, y) + s * 0.1), rockm, scale=(1.3, 1, 0.7), sub=2, jitter=0.45, smooth=False,
               seed=rr.random(), rot=(rr.uniform(-0.3, 0.3), rr.uniform(-0.3, 0.3), rr.uniform(0, TAU)), c=c)
    for k in range(160):   # pebbles near mine
        a = rr.uniform(0, TAU); d = rr.uniform(4, 22); s = rr.uniform(0.04, 0.16)
        x, y = d * math.cos(a), d * math.sin(a)
        sphere('pebble', s, (x, y, height(x, y)), rockm, scale=(1.2, 1, 0.6), sub=1, jitter=0.4, smooth=False, seed=rr.random(), c=c)
    return height

def smooth01(t, sharp):
    t = max(0, min(1, (t - sharp) / (1 - sharp))); return t * t * (3 - 2 * t)

def world_and_sun(sun_dir=(-0.5, -0.65, 0.58), energy=5.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.new('Space'); sc.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes['Background']
    lp = nt.nodes.new('ShaderNodeLightPath')
    tc = nt.nodes.new('ShaderNodeTexCoord'); vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 260
    nt.links.new(tc.outputs['Generated'], vor.inputs['Vector'])
    st = nt.nodes.new('ShaderNodeMapRange'); st.inputs['From Min'].default_value = 0.035; st.inputs['From Max'].default_value = 0.0
    st.inputs['To Max'].default_value = 0.9; nt.links.new(vor.outputs['Distance'], st.inputs['Value'])
    msk = nt.nodes.new('ShaderNodeMath'); msk.operation = 'GREATER_THAN'; msk.inputs[1].default_value = 0.93
    nt.links.new(vor.outputs['Color'], msk.inputs[0])
    star = nt.nodes.new('ShaderNodeMath'); star.operation = 'MULTIPLY'; nt.links.new(st.outputs[0], star.inputs[0]); nt.links.new(msk.outputs[0], star.inputs[1])
    sky = nt.nodes.new('ShaderNodeMix'); sky.data_type = 'RGBA'
    sky.inputs[6].default_value = (0, 0, 0, 1); sky.inputs[7].default_value = (1, 1, 1, 1)
    nt.links.new(star.outputs[0], sky.inputs['Factor'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    mx.inputs[6].default_value = hexc('#2b3445')   # fill (bounce-ish) for non-camera rays
    nt.links.new(lp.outputs['Is Camera Ray'], mx.inputs['Factor']); nt.links.new(sky.outputs[2], mx.inputs[7])
    nt.links.new(mx.outputs[2], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.6
    sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = energy; sd.angle = math.radians(0.35); sd.color = hexc('#fff3e2')[:3]
    so = bpy.data.objects.new('Sun', sd); coll('Stage').objects.link(so)
    so.rotation_euler = (-Vector(sun_dir)).to_track_quat('-Z', 'Y').to_euler()
    # a small Earth in the black sky
    em = bpy.data.materials.new('M_EarthGlow'); nt2, b2 = _nodes(em)
    tc2 = nt2.nodes.new('ShaderNodeTexCoord'); nz = nt2.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.22; nz.inputs['Detail'].default_value = 4
    nt2.links.new(tc2.outputs['Object'], nz.inputs['Vector'])
    rp = nt2.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = hexc('#1d4fb8'); rp.color_ramp.elements[1].color = hexc('#e8f2ff')
    rp.color_ramp.elements[0].position = 0.5; rp.color_ramp.elements[1].position = 0.68
    e = rp.color_ramp.elements.new(0.54); e.color = hexc('#4f7f3e'); e = rp.color_ramp.elements.new(0.6); e.color = hexc('#8a7a52')
    e = rp.color_ramp.elements.new(0.63); e.color = hexc('#d9e6f5'); rp.color_ramp.interpolation = 'CONSTANT'
    nt2.links.new(nz.outputs['Fac'], rp.inputs['Fac']); nt2.links.new(rp.outputs['Color'], b2.inputs['Base Color'])
    nt2.links.new(rp.outputs['Color'], b2.inputs['Emission Color']); b2.inputs['Emission Strength'].default_value = 0.35
    sphere('Earth', 8, (-160, 520, 150), em, sub=4, c='Stage')
    return so

def astronaut(loc, rot_z=0.0, c='Stage'):
    suit = M_paint('M_Suit', '#eef1f5', rough=0.6, metal=0, grime=0.25, grime_col='#8d8780', bevel=0.02)
    dark = M_paint('M_SuitDark', '#2f3644', rough=0.5, metal=0.3)
    visor = bpy.data.materials.new('M_Visor'); nt, b = _nodes(visor)
    b.inputs['Base Color'].default_value = hexc('#c99a3a'); b.inputs['Metallic'].default_value = 1; b.inputs['Roughness'].default_value = 0.05
    orange = M_paint('M_SuitOrange', '#e8701a', rough=0.5)
    root = bpy.data.objects.new('Astronaut', None); coll(c).objects.link(root)
    P = []
    P += [cyl('leg', 0.12, 0.8, (sx * 0.13, 0, 0.5), suit, segs=16, bevel=0.03, c=c) for sx in (-1, 1)]
    P += [box('boot', (0.2, 0.32, 0.14), (sx * 0.13, -0.04, 0.07), dark, bevel=0.04, c=c) for sx in (-1, 1)]
    P += [cyl('knee', 0.13, 0.08, (sx * 0.13, 0, 0.5), dark, segs=16, c=c) for sx in (-1, 1)]
    P.append(box('torso', (0.56, 0.36, 0.6), (0, 0, 1.18), suit, bevel=0.1, segs=3, c=c))
    P.append(box('belt', (0.54, 0.36, 0.08), (0, 0, 0.9), dark, bevel=0.03, c=c))
    P.append(box('pack', (0.48, 0.24, 0.62), (0, 0.29, 1.22), suit, bevel=0.06, segs=3, c=c))
    P.append(box('chest', (0.22, 0.06, 0.14), (0, -0.2, 1.22), dark, bevel=0.02, c=c))
    P.append(box('stripe', (0.57, 0.37, 0.05), (0, 0, 1.36), orange, bevel=0.01, c=c))
    for sx in (-1, 1):
        P.append(rod('arm', (sx * 0.33, 0, 1.38), (sx * 0.4, -0.08, 0.95), 0.085, suit, c=c))
        P.append(sphere('glove', 0.08, (sx * 0.41, -0.09, 0.9), dark, sub=2, c=c))
    P.append(sphere('helmet', 0.21, (0, -0.02, 1.62), suit, sub=3, c=c))
    P.append(sphere('visor', 0.18, (0, -0.07, 1.62), visor, scale=(1, 0.85, 0.85), sub=3, c=c))
    P.append(cyl('ant', 0.01, 0.25, (0.17, 0.3, 1.6), dark, segs=6, c=c))
    for p in P: p.parent = root
    root.location = loc; root.rotation_euler = (0, 0, rot_z)
    return root

# ------------------------------------------------------------------ rendering + export
def setup_render(samples=64):
    sc = bpy.context.scene; r = sc.render; r.engine = 'CYCLES'
    sc.cycles.device = 'CPU'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.cycles.max_bounces = 6; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.02
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
    r.image_settings.file_format = 'PNG'; r.image_settings.color_depth = '8'
    cd = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cd); coll('Stage').objects.link(cam); sc.camera = cam
    cd.clip_end = 2000
    return cam

def shoot(cam, path, target, pos, w, h, lens=50, samples=None, dof=None):
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = w, h
    if samples: sc.cycles.samples = samples
    cam.data.lens = lens; cam.location = pos
    cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    if dof:
        cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (Vector(target) - Vector(pos)).length; cam.data.dof.aperture_fstop = dof
    else:
        cam.data.dof.use_dof = False
    bd = argv().get('border')
    if bd and w > 2000:   # render one horizontal band (ymin,ymax) to <path>_band_<ymin>.png; stitched later
        y0, y1 = [float(v) for v in bd.split(',')]
        sc.render.use_border = True; sc.render.use_crop_to_border = False
        sc.render.border_min_x, sc.render.border_max_x, sc.render.border_min_y, sc.render.border_max_y = 0, 1, y0, y1
        sc.render.film_transparent = False
        path = path.replace('.png', f'_band_{y0:.2f}.png')
    else:
        sc.render.use_border = False
    sc.render.filepath = path; bpy.ops.render.render(write_still=True); print('RENDERED', path, flush=True)

def turntable(cam, outdir, target, dist, elev, size=1000, samples=48, lens=50):
    ks = argv().get('ks')
    for k in (range(8) if not ks else [int(x) for x in ks.split(',')]):
        a = math.radians(k * 45)
        pos = (target[0] - dist * math.sin(a) * math.cos(math.radians(elev)),
               target[1] - dist * math.cos(a) * math.cos(math.radians(elev)),
               target[2] + dist * math.sin(math.radians(elev)))
        shoot(cam, os.path.join(outdir, f'turn_{k * 45:03d}.png'), target, pos, size, size, lens, samples)

def convert_curves():
    for ob in list(coll('Mine').all_objects):
        if ob.type in ('CURVE', 'FONT'):
            bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
            bpy.ops.object.convert(target='MESH')

def export_glb(path):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in coll('Mine').all_objects: ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                              export_animations=False, export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=True)
    print('GLB', path, flush=True)

def argv():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    d = {}
    for i, k in enumerate(a):
        if k.startswith('--'): d[k[2:]] = a[i + 1] if i + 1 < len(a) and not a[i + 1].startswith('--') else '1'
    return d
