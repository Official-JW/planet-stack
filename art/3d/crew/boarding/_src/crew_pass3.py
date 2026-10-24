"""Planet Stack - Starter Ship crew: armored EVA suits (original design), reusable.
    from crew import crew_member
    crew_member(loc, rot_z, variant='A' | 'B', pose='stand' | 'wave' | 'walk' | 'climb' | 'tagline' | 'point', name=...)
Faces -Y at rot_z = 0, feet on z = loc.z, ~1.8 m tall human proportions (variant B, curvier female suit: ~1.74 m, same helmet).
Body (pass 2): sleek layered armor. Every plate is a thin, solidified, edge-bevelled shell sampled from a smooth tapered
body surface (spline-lofted superellipse sections), so plates curve with the body and overlap like shingles (each plate's
lower edge flares out over the next one). Graphite under-plates show through the panel seams. Cuirass = graphite core +
pec plates, sternum, rib plates, collar plate, back plate, segmented ab bands; layered 3-lame pauldrons; two-lame thigh,
shin (with a front keel) and forearm shells; domed kneecaps and elbow cops; flared cuffs; articulated gloves (palm,
knuckle plate, 3-joint fingers, thumb). Undersuit is a slim graphite fabric with a defined waist.
Built from ONE shared parametric base (suit_params) + a variant overlay, with only 7 materials
(shell, graphite, undersuit, visor, accent paint, accent glow, cyan glow) so a later game mesh can merge by material.
Weathering in the materials: edge wear (Bevel-node edge mask), visible scratches, crevice grime (local AO) and regolith
dust that builds up toward the boots (per-vertex 'ht' = height above the soles, written on every part).
Helmet (original design): full sculpted armored helmet with a flatter, tapered crown; one-piece wraparound gold-orange
'goggle band' visor whose top edge RISES toward the temples and whose lower edge is flat with a single angular chevron
point at the centre; split brow (two separate faceted plates with a gap), no crest/fin - a low graphite sensor ridge with
a small light runs back over the crown; angular cheek/jaw guards, ear/comms pods, short antenna, light strip, thick neck
seal. No markings or logos.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Euler
from mc_common import hexc, _nodes, _obj, coll, mat4, M_glow

C = 'Stage'
_M = {}
TAU = 2 * math.pi

# ------------------------------------------------------------------ materials (shared by all crew)
def _shell_mat(name, col, rough, coat, metal=0.0, bump=0.12, micro=90.0, dust=0.0, scratch=0.0, fabric=False,
               dust_col='#9a958c', scr_col='#8e939a', wear_col='#5d636b', wear=0.0, grime=0.35):
    """armor paint: clean glossy base + visible weathering:
       - edge wear: Bevel-node vs true normal -> chipped paint on plate rims (broken up by noise)
       - scratches: two families of thin streaks, darker/rougher, in patches
       - crevice grime: local AO in the seams / overlaps
       - regolith dust: patchy, rising toward the boots (vertex attribute 'ht' = height above the soles), caked near the soles."""
    m = bpy.data.materials.new(name); nt, b = _nodes(m); N, L = nt.nodes, nt.links
    b.inputs['Base Color'].default_value = hexc(col); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.04
    tc = N.new('ShaderNodeTexCoord'); P = tc.outputs['Object']
    def noise(vec, scale, detail=2.0, rough_=0.5, dist=0.0):
        n = N.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough_; n.inputs['Distortion'].default_value = dist; L.new(vec, n.inputs['Vector']); return n.outputs['Fac']
    def mrange(v, a_, b_, c0=0.0, c1=1.0):
        r = N.new('ShaderNodeMapRange'); r.inputs['From Min'].default_value = a_; r.inputs['From Max'].default_value = b_
        r.inputs['To Min'].default_value = c0; r.inputs['To Max'].default_value = c1; L.new(v, r.inputs['Value']); return r.outputs['Result']
    def op(o, x, y, clamp=False):
        n = N.new('ShaderNodeMath'); n.operation = o; n.use_clamp = clamp
        for i, v in enumerate((x, y)):
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L.new(v, n.inputs[i])
        return n.outputs[0]
    def mixc(f, c0, c1):
        n = N.new('ShaderNodeMix'); n.data_type = 'RGBA'
        if isinstance(f, (int, float)): n.inputs['Factor'].default_value = f
        else: L.new(f, n.inputs['Factor'])
        for idx, c in ((6, c0), (7, c1)):
            if isinstance(c, str): n.inputs[idx].default_value = hexc(c)
            else: L.new(c, n.inputs[idx])
        return n.outputs[2]
    def stretch(sx, sy, sz, rz):
        mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (sx, sy, sz); mp.inputs['Rotation'].default_value = (0.3, 0.2, rz)
        L.new(P, mp.inputs['Vector']); return mp.outputs['Vector']
    at = N.new('ShaderNodeAttribute'); at.attribute_name = 'ht'; ht = at.outputs['Fac']
    # dust: patchy everywhere (light), heavier and more continuous toward the boots, caked at the soles
    low = mrange(ht, 0.8, 0.05, 0.12, 1.0)
    patch = mrange(noise(P, 6.0, detail=5, rough_=0.62), 0.42, 0.68)
    dpat = op('MULTIPLY', patch, low)
    cake = op('MULTIPLY', mrange(ht, 0.36, 0.04, 0.0, 0.9), mrange(noise(P, 14.0, detail=4), 0.3, 0.6, 0.35, 1.0))
    dfac = op('MINIMUM', op('MULTIPLY', op('ADD', dpat, cake), dust), 0.92)
    if fabric:      # undersuit: fine woven bump + dust only
        h = noise(stretch(1, 1, 1, 0), micro, detail=4)
        bc = mixc(dfac, col, dust_col)
        L.new(bc, b.inputs['Base Color'])
        L.new(op('ADD', op('MULTIPLY', dfac, 0.3), rough), b.inputs['Roughness'])
    else:
        def line(v, w):       # thin contour line of a stretched noise = scratch streak
            d = op('ABSOLUTE', op('SUBTRACT', v, 0.5), 0.0); return mrange(d, 0.0, w, 1.0, 0.0)
        # long, nearly straight streaks: very low frequency along the streak, high across it, then chopped into dashes
        s1 = op('MULTIPLY', line(noise(stretch(0.22, 7.0, 0.22, 0.4), micro * 0.35, detail=0.0), 0.012),
                mrange(noise(stretch(9, 1, 9, 0.4), micro * 0.12, detail=1.0), 0.48, 0.55))
        s2 = op('MULTIPLY', line(noise(stretch(6.0, 0.25, 0.25, -0.7), micro * 0.33, detail=0.0), 0.011),
                mrange(noise(stretch(1, 9, 9, -0.7), micro * 0.12, detail=1.0), 0.48, 0.55))
        s3 = line(noise(stretch(0.3, 0.3, 5.0, 1.9), micro * 0.2, detail=0.0), 0.008)    # a few longer vertical gouges
        sm = op('MAXIMUM', op('MAXIMUM', s1, s2), s3)
        # edge wear: bevel normal vs. shading normal
        bv = N.new('ShaderNodeBevel'); bv.samples = 6; bv.inputs['Radius'].default_value = 0.0045
        geo = N.new('ShaderNodeNewGeometry')
        dp = N.new('ShaderNodeVectorMath'); dp.operation = 'DOT_PRODUCT'; L.new(bv.outputs['Normal'], dp.inputs[0]); L.new(geo.outputs['Normal'], dp.inputs[1])
        edge = mrange(dp.outputs['Value'], 0.985, 0.86)
        # scratches only where armor gets hit: a wide band along plate edges + a few sparse wear spots (more low down)
        bw = N.new('ShaderNodeBevel'); bw.samples = 6; bw.inputs['Radius'].default_value = 0.022
        dw = N.new('ShaderNodeVectorMath'); dw.operation = 'DOT_PRODUCT'; L.new(bw.outputs['Normal'], dw.inputs[0]); L.new(geo.outputs['Normal'], dw.inputs[1])
        ezone = mrange(dw.outputs['Value'], 0.995, 0.95)
        spots = mrange(noise(P, 3.2, detail=2), 0.6, 0.7)
        hit = op('MINIMUM', op('ADD', ezone, op('MULTIPLY', spots, op('ADD', op('MULTIPLY', low, 0.6), 0.4))), 1.0)
        hit = op('MULTIPLY', hit, mrange(noise(P, 9.0, detail=2), 0.42, 0.58))           # break the edge band into clusters
        scr = op('MULTIPLY', sm, hit)
        brk = mrange(noise(P, 38.0, detail=4, rough_=0.7), 0.38, 0.62)
        ew = op('MULTIPLY', op('MULTIPLY', edge, brk), op('ADD', op('MULTIPLY', low, wear * 0.6), wear))
        ew = op('MINIMUM', ew, 1.0)
        # crevice grime (seams, plate overlaps)
        ao = N.new('ShaderNodeAmbientOcclusion'); ao.only_local = True; ao.samples = 8; ao.inputs['Distance'].default_value = 0.035
        gr = op('MULTIPLY', mrange(ao.outputs['AO'], 0.95, 0.35), grime)
        c1 = mixc(op('MULTIPLY', scr, scratch), col, scr_col)
        c2 = mixc(ew, c1, wear_col)
        c3 = mixc(gr, c2, '#3a3936')
        c4 = mixc(dfac, c3, dust_col)
        L.new(c4, b.inputs['Base Color'])
        r = op('ADD', op('MULTIPLY', scr, scratch * 0.3), rough)
        r = op('ADD', op('MULTIPLY', ew, 0.35), r)
        r = op('ADD', op('MULTIPLY', dfac, 0.6), r)
        L.new(op('MINIMUM', r, 1.0), b.inputs['Roughness'])
        cw_ = op('MULTIPLY', op('SUBTRACT', 1.0, op('MAXIMUM', dfac, ew)), coat)       # dust / chips kill the clear coat
        L.new(cw_, b.inputs['Coat Weight'])
        h = op('ADD', op('MULTIPLY', scr, scratch), op('MULTIPLY', ew, 0.6))
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.0015
    bp.invert = not fabric; L.new(h, bp.inputs['Height']); L.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def mats(accent='cyan'):
    key = accent
    if key in _M: return _M[key]
    if 'shell' not in _M:
        _M['shell'] = _shell_mat('C_SuitShell', '#f2f4f7', 0.16, 1.0, bump=0.3, micro=60.0, dust=0.95, scratch=0.85,
                                 dust_col='#9b968d', scr_col='#8a9097', wear_col='#4f555d', wear=0.9)
        _M['graph'] = _shell_mat('C_SuitGraphite', '#2b3039', 0.3, 0.6, metal=0.45, bump=0.25, micro=70.0, dust=0.8, scratch=0.9,
                                 dust_col='#7c776f', scr_col='#8a9199', wear_col='#9aa1a8', wear=0.8, grime=0.2)
        _M['under'] = _shell_mat('C_SuitUnder', '#484d55', 0.7, 0.0, bump=0.3, micro=260.0, fabric=True, dust=0.85, dust_col='#77726a')
        v = bpy.data.materials.new('C_Visor'); nt, b = _nodes(v)
        b.inputs['Base Color'].default_value = hexc('#ffae2e'); b.inputs['Metallic'].default_value = 1.0; b.inputs['Roughness'].default_value = 0.04
        b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.02
        b.inputs['Emission Color'].default_value = hexc('#ff8a1e'); b.inputs['Emission Strength'].default_value = 0.18
        _M['visor'] = v
        _M['cyan'] = M_glow('C_CyanGlow', '#3ad0ff', 9)
    col = {'cyan': '#29c3f2', 'pink': '#ff4fa8'}[accent]
    paint = _shell_mat('C_Accent_' + accent, col, 0.22, 0.9, bump=0.2, micro=60.0, dust=0.6, scratch=0.7,
                       dust_col='#8f8a82', scr_col='#c9ccd0', wear_col='#e8eaed', wear=0.8)
    glow = _M['cyan'] if accent == 'cyan' else M_glow('C_PinkGlow', '#ff4fa8', 9)
    _M[key] = dict(shell=_M['shell'], graph=_M['graph'], under=_M['under'], visor=_M['visor'], paint=paint, glow=glow, cyan=_M['cyan'])
    return _M[key]

# ------------------------------------------------------------------ primitives (all parented to the member root)
class _B:
    def __init__(s, root): s.root = root; s.parts = []
    def add(s, ob): ob.parent = s.root; s.parts.append(ob); return ob

def _frame(p0, p1):
    a, b = Vector(p0), Vector(p1); z = b - a; Lz = z.length; z.normalize()
    up = Vector((0, -1, 0)) if abs(z.y) < 0.9 else Vector((1, 0, 0))
    x = up.cross(z).normalized(); y = z.cross(x).normalized()
    return a, Lz, Matrix((x, y, z)).transposed()

def ellip(B, name, center, radii, mat, rot=None, axis=None, sub=3, smooth=True):
    """ellipsoid; rot = Euler tuple or axis=(p0, p1) to align local Z with a segment (center = mid)."""
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    M = Matrix.Diagonal((*radii, 1))
    if axis is not None: _, _, R3 = _frame(*axis); M = R3.to_4x4() @ M
    elif rot is not None: M = Euler(rot).to_matrix().to_4x4() @ M
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(center)) @ M, verts=bm.verts)
    return B.add(_obj(bm, name, mat, C, smooth=smooth, angle=180 if smooth else 0))

def seg(B, name, p0, p1, r0, r1, mat, n=16, cap=True):
    a, Lz, R3 = _frame(p0, p1)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=n, radius1=r0, radius2=r1, depth=Lz)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(a) @ R3.to_4x4() @ Matrix.Translation((0, 0, Lz / 2)), verts=bm.verts)
    return B.add(_obj(bm, name, mat, C, smooth=True, angle=60))

def rbox(B, name, size, center, mat, rot=(0, 0, 0), bevel=0.02, segs=3):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.transform(bm, matrix=mat4(center, rot, size), verts=bm.verts)
    return B.add(_obj(bm, name, mat, C, bevel=bevel, segs=segs, angle=30))

# ------------------------------------------------------------------ smooth armor shells (pass 2)
def _herm(K, t):
    """piecewise cubic Hermite (Catmull-Rom tangents) through keys K = [(t, v1, v2, ...)] -> [v1, v2, ...] at t."""
    ts = [k[0] for k in K]; n = len(K)
    if t <= ts[0]: return list(K[0][1:])
    if t >= ts[-1]: return list(K[-1][1:])
    i = max(j for j in range(n - 1) if ts[j] <= t)
    h = ts[i + 1] - ts[i]; u = (t - ts[i]) / h; u2, u3 = u * u, u * u * u
    out = []
    for c in range(1, len(K[0])):
        def tan(j):
            if j == 0: return (K[1][c] - K[0][c]) / (ts[1] - ts[0])
            if j == n - 1: return (K[-1][c] - K[-2][c]) / (ts[-1] - ts[-2])
            return (K[j + 1][c] - K[j - 1][c]) / (ts[j + 1] - ts[j - 1])
        v0, v1, m0, m1 = K[i][c], K[i + 1][c], tan(i) * h, tan(i + 1) * h
        out.append((2 * u3 - 3 * u2 + 1) * v0 + (u3 - 2 * u2 + u) * m0 + (-2 * u3 + 3 * u2) * v1 + (u3 - u2) * m1)
    return out

def _spow(v, e): return math.copysign(abs(v) ** e, v)

def surf(org, X, Y, Z, keys, ex=2.3, kpow=8):
    """smooth tapered body surface: keys = [(t, w, d, yoff, xoff, keel, lobe)] (missing -> 0); section angle a: 0 = front (+Y),
    +pi/2 = +X side. keel adds a sharp ridge down the front. Returns F(t, a, off) -> Vector (off = outward offset in m)."""
    org, X, Y, Z = Vector(org), Vector(X), Vector(Y), Vector(Z)
    K = [tuple(k) + (0.0,) * (7 - len(k)) for k in keys]
    def F(t, a, off=0.0):
        w, d, yo, xo, kl, lb = _herm(K, t)
        sa, ca = math.sin(a), math.cos(a)
        x = (w + off) * _spow(sa, 2 / ex); y = (d + off) * _spow(ca, 2 / ex) + kl * max(0.0, ca) ** kpow
        if lb: y += lb * math.exp(-((abs(math.atan2(sa, ca)) - 0.52) / 0.34) ** 2)      # twin chest lobes (variant B)
        return org + Z * t + X * (xo + x) + Y * (yo + y)
    return F

def shell(B, name, F, t0, t1, a0, a1, mat, off=0.006, thick=0.006, nu=None, nv=None, bevel=0.0018, caps=False, smooth=True):
    """armor plate sampled from F over t in [t0, t1] and section angle [a0, a1]. off = outward offset, or (off@t0, off@t1)
    eased so a plate can flare out at one edge (shingle overlap). thick > 0 -> solidified inward + bevelled rims.
    t0 / t1 may be functions of the section angle a -> shaped plate edges (V points, swept cuts)."""
    full = abs((a1 - a0) - TAU) < 1e-6
    T0 = t0 if callable(t0) else (lambda a, v=t0: v); T1 = t1 if callable(t1) else (lambda a, v=t1: v)
    t0, t1 = T0((a0 + a1) / 2), T1((a0 + a1) / 2)
    if callable(off): OF = off
    else:
        o0, o1 = off if isinstance(off, (tuple, list)) else (off, off)
        OF = lambda t, a, u: o0 + (o1 - o0) * u * u
    nu = nu or max(3, int(abs(t1 - t0) / 0.01) + 2)
    nv = nv or max(4, int(abs(a1 - a0) / TAU * 44) + 2)
    bm = bmesh.new(); V = []
    for i in range(nu + 1):
        u = i / nu; row = []
        for j in range(nv if full else nv + 1):
            a = a0 + (a1 - a0) * j / nv; t = T0(a) + (T1(a) - T0(a)) * u; row.append(bm.verts.new(F(t, a, OF(t, a, u))))
        V.append(row)
    m_ = nv if full else nv + 1
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((V[i][j], V[i + 1][j], V[i + 1][(j + 1) % m_], V[i][(j + 1) % m_]))
    if full and caps:
        bm.faces.new(V[0]); bm.faces.new(list(reversed(V[-1])))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    else:   # orient outward: compare one face normal with the surface's outward direction
        i, j = nu // 2, nv // 2; t = t0 + (t1 - t0) * (i + 0.5) / nu; a = a0 + (a1 - a0) * (j + 0.5) / nv
        bm.faces.ensure_lookup_table(); f = bm.faces[i * nv + j]; f.normal_update()
        if f.normal.dot(F(t, a, 0.02) - F(t, a, 0.0)) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
    ob = _obj(bm, name, mat, C, smooth=smooth, angle=180 if smooth else 0)
    if thick > 0:
        md = ob.modifiers.new('Solid', 'SOLIDIFY'); md.thickness = thick; md.offset = -1.0; md.use_even_offset = True
        if bevel > 0:
            bv = ob.modifiers.new('Bevel', 'BEVEL'); bv.width = bevel; bv.segments = 2; bv.limit_method = 'ANGLE'
            bv.angle_limit = math.radians(40); bv.harden_normals = True; bv.use_clamp_overlap = True
    return B.add(ob)

def arc(center, half): return center - half, center + half

def bellows(base, zones, amp=0.0055, pitch=0.024):
    """offset function for a pressure-layer shell: soft rolled folds inside each zone (t0, t1), smooth elsewhere."""
    def f(t, a, u):
        o = base
        for (c0, c1) in zones:
            if c0 <= t <= c1:
                w = math.sin(math.pi * (t - c0) / (c1 - c0)) ** 0.7
                o += amp * w * (0.55 + 0.45 * math.cos(TAU * (t - c0) / pitch)) * (1.0 + 0.12 * math.sin(3 * a + 7 * t))
        return o
    return f

def hose(B, name, pts, r, mat, n=10, rib=0.0, per=0.012):
    """ribbed flexible hose along a Catmull-Rom path through pts."""
    P_ = [Vector(p) for p in pts]; P_ = [P_[0]] + P_ + [P_[-1]]
    path = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        m = max(4, int((p2 - p1).length / 0.006))
        for j in range(m):
            u = j / m; u2, u3 = u * u, u * u * u
            path.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3))
    path.append(P_[-2])
    bm = bmesh.new(); R = []; L_ = 0.0; up = Vector((0, 0, 1))
    for i, c in enumerate(path):
        tg = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        if i: L_ += (c - path[i - 1]).length
        x = tg.cross(up if abs(tg.dot(up)) < 0.95 else Vector((1, 0, 0))).normalized(); y = tg.cross(x)
        rr = r * (1 + rib * max(0.0, math.cos(TAU * L_ / per)) ** 2)
        R.append([bm.verts.new(c + (x * math.cos(TAU * k / n) + y * math.sin(TAU * k / n)) * rr) for k in range(n)])
    for r0, r1 in zip(R, R[1:]):
        for k in range(n): bm.faces.new((r0[k], r0[(k + 1) % n], r1[(k + 1) % n], r1[k]))
    bm.faces.new(R[0]); bm.faces.new(list(reversed(R[-1]))); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return B.add(_obj(bm, name, mat, C, smooth=True, angle=180))

# ------------------------------------------------------------------ helmet (shared by both variants)
HR = (0.158, 0.174, 0.168)      # helmet design half-extents (w, d, h) before HS
HS = 0.78                       # built scale: ~0.24 x 0.26 x 0.24 m, just over head size

def _dir(th, ph): return Vector((math.sin(th) * math.cos(ph), -math.cos(th) * math.cos(ph), math.sin(ph)))

def _hsurf(d):
    """sculpted helmet surface for unit direction d (front = -Y): boxy superellipsoid 'armored bucket' with a tapered,
    forward-pushed jaw, a FLAT, tapered crown (higher exponent above the brow, pulled down and in) and a fuller back."""
    d = Vector(d).normalized(); x, y, z = d
    a, b, c = HR
    nh = 5.0 if z > -0.2 else 3.2                       # boxier above the jaw line
    ez = 3.6 if z > 0 else 2.4                          # flat-topped crown, rounded jaw
    f = (abs(x) / a) ** nh + (abs(y) / b) ** nh
    f = f ** (ez / nh) + (abs(z) / c) ** ez
    r = f ** (-1 / ez)
    p = d * r
    if p.z < 0:                                          # jaw tapers in, chin pushed forward
        t = min(1.0, -p.z / c)
        p.x *= 1.0 - 0.2 * t ** 1.3
        if p.y < 0: p.y *= 1.0 + 0.12 * t
        else: p.y *= 1.0 - 0.1 * t
    else:
        t = min(1.0, p.z / c)
        p.z *= 0.84 + 0.04 * (1 - t)                     # lower, flatter crown
        p.x *= 1.0 - 0.27 * t ** 1.4                     # crown tapers in -> trapezoid front silhouette
        if p.y < 0: p.y *= 1.0 - 0.12 * t ** 1.6          # forehead slopes back
        else: p.y *= 1.0 - 0.1 * t ** 1.8                 # back of the crown tucks in too (narrower in 3/4)
    if p.y > 0: p.y *= 1.03
    return p

def _patch(B, name, th0, th1, ph0f, ph1f, scalef, mat, nu=28, nv=10, thick=0.008, smooth=True, bevel=0.0):
    bm = bmesh.new(); V = []
    for i in range(nu + 1):
        th = th0 + (th1 - th0) * i / nu; row = []
        for j in range(nv + 1):
            p0, p1 = ph0f(th), ph1f(th); ph = p0 + (p1 - p0) * j / nv
            row.append(bm.verts.new(_hsurf(_dir(th, ph)) * scalef(th, ph)))
        V.append(row)
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((V[i][j], V[i + 1][j], V[i + 1][j + 1], V[i][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _obj(bm, name, mat, C, smooth=smooth, angle=180 if smooth else 0)
    md = ob.modifiers.new('Solid', 'SOLIDIFY'); md.thickness = thick; md.offset = -1.0; md.use_even_offset = False
    ob.modifiers.move(len(ob.modifiers) - 1, 0)
    return B.add(ob)

def helmet(B, M, head, yaw=0.0, pitch=0.0):
    """builds the helmet at the origin under an empty placed at `head` (helmet centre)."""
    hp = bpy.data.objects.new('HelmetPivot', None); coll(C).objects.link(hp); B.add(hp)
    hp.location = head; hp.rotation_euler = (pitch, 0, yaw); hp.scale = (HS, HS, HS)
    HB = _B(hp)
    d2r = math.radians
    vt = lambda th: d2r(13) + d2r(7) * abs(th) / d2r(72)                                          # visor top: rises toward the temples
    vb = lambda th: d2r(-14) - d2r(11) * max(0.0, 1 - abs(th) / d2r(26))  # visor bottom: flat, one angular chevron point at centre
    # main shell (open at the bottom into the neck seal)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=56, v_segments=32, radius=1.0)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.82], context='VERTS')
    for v in bm.verts: v.co = _hsurf(v.co.normalized())
    HB.add(_obj(bm, 'HelmetShell', M['shell'], C, smooth=True, angle=180))
    # visor frame (graphite, slightly larger than the visor) + one-piece wraparound visor (bulges proud of the shell)
    _patch(HB, 'HelmetVisorFrame', d2r(-78), d2r(78), lambda t: vb(t) - d2r(5), lambda t: vt(t) + d2r(4), lambda t, p: 1.022, M['graph'], thick=0.01)
    _patch(HB, 'HelmetVisor', d2r(-72), d2r(72), vb, vt, lambda t, p: 1.035 + 0.035 * math.cos(t) ** 2 * math.cos(p * 2.5), M['visor'], nu=40, nv=14, thick=0.006)
    # split brow: two separate faceted plates with a centre gap (low lip, no big overhang) + low sensor ridge (no crest/fin)
    for s_ in (-1, 1):
        t0, t1 = (d2r(9), d2r(66)) if s_ > 0 else (-d2r(66), -d2r(9))
        _patch(HB, 'HelmetBrow', t0, t1, lambda t: vt(t) + d2r(2.5), lambda t: vt(t) + d2r(17),
               lambda t, p: 1.015 + 0.055 * max(0.0, 1 - (p - vt(t)) / d2r(17)), M['shell'], nu=8, nv=3, thick=0.025, smooth=False)
        _patch(HB, 'HelmetBrowEdge', t0, t1, lambda t: vt(t) + d2r(1), lambda t: vt(t) + d2r(2.5),
               lambda t, p: 1.07, M['graph'], nu=8, nv=1, thick=0.03, smooth=False)
    _patch(HB, 'HelmetSensorRidge', d2r(-3.5), d2r(3.5), lambda t: vt(t) + d2r(4), lambda t: d2r(62),
           lambda t, p: 1.0 + 0.022 * min(1.0, (p - d2r(17)) / d2r(6)) ** 0.5 if p > d2r(17) else 1.0, M['graph'], nu=2, nv=10, thick=0.012, smooth=False)
    ellip(HB, 'HelmetSensor', tuple(_hsurf(_dir(0.0, d2r(24))) * 1.03), (0.011, 0.006, 0.011), M['glow'], sub=1)
    # angular cheek / jaw guards (flat-shaded facets) + chin guard with breather slots
    for s in (-1, 1):
        _patch(HB, 'HelmetCheek', s * d2r(36) if s > 0 else -d2r(98), d2r(98) if s > 0 else -d2r(36), lambda t: d2r(-62), lambda t: vb(t) - d2r(6),
               lambda t, p: 1.03 + 0.11 * max(0.0, min(1.0, (p + d2r(62)) / d2r(50))), M['shell'], nu=5, nv=3, thick=0.03, smooth=False)
        _patch(HB, 'HelmetCheekTrim', s * d2r(98) if s > 0 else -d2r(104), d2r(104) if s > 0 else -d2r(98), lambda t: d2r(-60), lambda t: d2r(8),
               lambda t, p: 1.11, M['graph'], nu=1, nv=6, thick=0.02, smooth=False)
    _patch(HB, 'HelmetChin', d2r(-34), d2r(34), lambda t: d2r(-66), lambda t: vb(t) - d2r(7), lambda t, p: 1.11 + 0.04 * math.cos(t * 2.5),
           M['graph'], nu=8, nv=3, thick=0.02, smooth=False)
    for k in (-1, 0, 1):
        p = _hsurf(_dir(d2r(k * 9), d2r(-46))) * 1.16
        rbox(HB, 'HelmetBreather', (0.012, 0.012, 0.045), tuple(p), M['paint'] if k == 0 else M['shell'], rot=(d2r(25), 0, d2r(k * 9)), bevel=0.003, segs=1)
    # ear / comms pods + antenna + side light strips
    for s in (-1, 1):
        c = _hsurf(_dir(s * d2r(92), d2r(-4))) * 1.0
        n = Vector((s, 0, 0))
        a, Lz, R3 = _frame(c - n * 0.01, c + n * 0.055)
        seg(HB, 'HelmetEarPod', c - n * 0.01, c + n * 0.05, 0.058, 0.05, M['graph'], n=24)
        seg(HB, 'HelmetEarCap', c + n * 0.05, c + n * 0.062, 0.046, 0.038, M['shell'], n=24)
        seg(HB, 'HelmetEarLight', c + n * 0.062, c + n * 0.066, 0.03, 0.026, M['glow'], n=20)
        _patch(HB, 'HelmetLightStrip', s * d2r(100) if s > 0 else -d2r(142), d2r(142) if s > 0 else -d2r(100), lambda t: d2r(22), lambda t: d2r(26),
               lambda t, p: 1.035, M['glow'], nu=10, nv=1, thick=0.004)
    c = _hsurf(_dir(d2r(96), d2r(4))) + Vector((0.055, 0.02, 0.0))
    seg(HB, 'HelmetAntenna', c, c + Vector((0.012, 0.05, 0.2)), 0.006, 0.0035, M['graph'], n=8)
    ellip(HB, 'HelmetAntennaTip', tuple(c + Vector((0.012, 0.05, 0.205))), (0.01, 0.01, 0.01), M['glow'], sub=1)
    # rear electronics bump
    ellip(HB, 'HelmetRear', tuple(_hsurf(_dir(d2r(180), d2r(5))) * 0.96), (0.08, 0.035, 0.07), M['graph'], sub=2)
    return hp
# ------------------------------------------------------------------ body
def suit_params(variant):
    """one shared parametric base (A); variant B overrides a handful of numbers (same parts/topology)."""
    base = dict(h=1.0, sh_w=0.2, hip_w=0.1, pel=(0.162, 0.115), waist=(0.128, 0.098), ribs=(0.145, 0.11),
                chest=(0.162, 0.124), upch=(0.148, 0.11), limb=1.0, accent='cyan', female=False,
                paul=(0.082, 0.088, 1.0), bust=0.0, keel=0.011, lobe=0.012, tw=1.0)
    if variant == 'B':          # curvier female suit: narrower shoulders/waist, wider hips, shaped chest plate, slimmer limbs
        base.update(h=0.965, sh_w=0.178, hip_w=0.104, pel=(0.178, 0.122), waist=(0.1, 0.086), ribs=(0.124, 0.102),
                    chest=(0.138, 0.114), upch=(0.13, 0.102), limb=0.9, accent='pink', female=True,
                    paul=(0.068, 0.074, 0.88), bust=0.04, keel=0.004, lobe=0.03, tw=1.12)
    return base

POSES = {   # legs: side -> (pitch fwd, knee bend); arms: side -> (pitch fwd, abduct, elbow bend); lean fwd, head yaw/pitch
    'stand':   dict(legs={1: (0.02, 0.04), -1: (0.02, 0.04)}, arms={1: (0.12, 0.22, 0.35), -1: (0.12, 0.22, 0.35)}, lean=0.0, yaw=0.0, hp=0.0),
    'wave':    dict(legs={1: (0.0, 0.03), -1: (0.06, 0.08)}, arms={1: (0.2, 0.2, 0.5), -1: (0.4, 2.3, 1.1)}, lean=0.0, yaw=-0.25, hp=0.05),
    'point':   dict(legs={1: (-0.1, 0.05), -1: (0.15, 0.12)}, arms={1: (0.1, 0.18, 0.45), -1: (1.75, 0.35, 0.1)}, lean=0.02, yaw=-0.35, hp=-0.15),
    'walk':    dict(legs={1: (0.38, 0.12), -1: (-0.3, 0.45)}, arms={1: (-0.3, 0.15, 0.4), -1: (0.35, 0.15, 0.55)}, lean=0.06, yaw=0.15, hp=0.0),
    'climb':   dict(legs={1: (1.05, 1.75), -1: (0.15, 0.3)}, arms={1: (2.75, 0.18, 0.35), -1: (2.2, 0.18, 0.75)}, lean=0.05, yaw=-0.5, hp=0.2),
    'tagline': dict(legs={1: (0.25, 0.25), -1: (-0.25, 0.2)}, arms={1: (0.9, 0.1, 0.6), -1: (0.75, -0.05, 0.9)}, lean=-0.06, yaw=0.1, hp=-0.25),
}

def _rx(v, a): return Matrix.Rotation(a, 3, 'X') @ v
def _limb_dir(pitch, abduct=0.0, side=1):
    d = Vector((0, 0, -1))
    d = Matrix.Rotation(-abduct * side, 3, 'Y') @ d
    return _rx(d, -pitch)

def _lframe(p0, p1):
    a, Lz, R3 = _frame(p0, p1); return a, Lz, R3.col[0], R3.col[1], R3.col[2]

def _keys(Lz, rows): return [(f * Lz,) + tuple(r) for f, *r in rows]

def glove(B, M, hand, fa, s, k):
    """articulated armored glove (sized up to read at full-body distance): padded graphite palm, white back-of-hand +
    knuckle armor, 4 three-joint fingers with white caps on the first two phalanges, a relaxed opposed thumb with a
    padded base. Palm faces the body."""
    fa = Vector(fa).normalized()
    inward = Vector((-s, 0, 0)); npalm = inward - fa * inward.dot(fa)
    if npalm.length < 1e-3: npalm = Vector((0, 1, 0)) - fa * fa.y
    npalm.normalize()
    W = fa.cross(npalm).normalized()
    if W.dot(Vector((0, -1, 0))) < 0: W = -W           # +W = front = thumb / index side
    org = hand - fa * 0.012
    Lp = 0.098 * k
    PF = surf(org, npalm, W, fa, [(0.0, 0.025 * k, 0.04 * k), (0.05 * k, 0.024 * k, 0.048 * k), (Lp, 0.019 * k, 0.047 * k)], ex=3.0)
    shell(B, 'GlovePalm', PF, 0.0, Lp, 0, TAU, M['graph'], off=0.0, thick=0.0, caps=True, nv=28)
    shell(B, 'GloveBackPlate', PF, 0.004 * k, 0.062 * k, *arc(-math.pi / 2, 1.3), M['shell'], off=(0.004, 0.006), thick=0.006, nv=18)
    shell(B, 'GloveKnucklePlate', PF, 0.055 * k, Lp + 0.006, *arc(-math.pi / 2, 1.35), M['shell'], off=(0.007, 0.009), thick=0.006, nv=18)
    shell(B, 'GloveBackStripe', PF, 0.02 * k, 0.05 * k, *arc(-math.pi / 2, 0.16), M['paint'], off=0.0095, thick=0.004, nv=4)
    xs = (0.033, 0.011, -0.011, -0.032); Ls = (0.082, 0.092, 0.087, 0.07); fr = (0.45, 0.32, 0.23); curl = (0.2, 0.38, 0.3)
    for fi, (xi, Lf) in enumerate(zip(xs, Ls)):
        p = org + fa * (Lp + 0.002) + W * (xi * k) - npalm * 0.002
        ellip(B, 'GloveKnuckle', tuple(p - npalm * 0.021 * k - fa * 0.004), (0.0125 * k, 0.0125 * k, 0.009 * k), M['shell'], sub=2)
        ang = 0.0; base_dir = (fa + W * xi * 1.4).normalized(); r = 0.012 * k
        for si, (f_, c_) in enumerate(zip(fr, curl)):
            ang += c_
            dvec = (base_dir * math.cos(ang) + npalm * math.sin(ang)).normalized()
            q = p + dvec * (Lf * k * f_); r1 = r * 0.9
            seg(B, 'GloveFinger', p, q, r, r1, M['graph'], n=10)
            ellip(B, 'GloveFingerJoint', tuple(p), (r * 1.05,) * 3, M['graph'], sub=1)
            if si < 2:
                back = (npalm - dvec * npalm.dot(dvec)).normalized() * -1
                ellip(B, 'GloveFingerCap', tuple(p.lerp(q, 0.5) + back * r * 0.5), (r * 1.02, r * 1.02, (q - p).length * 0.44), M['shell'], axis=(p, q), sub=2)
            p = q; r = r1
        ellip(B, 'GloveFingertip', tuple(p), (r, r, r * 1.1), M['graph'], axis=(p - dvec * 0.01, p), sub=2)
    # thumb: padded base on the palm's front edge, relaxed, lying along the index finger and curling in
    tb = org + fa * (0.022 * k) + W * (0.036 * k) + npalm * (0.012 * k)
    ellip(B, 'GloveThumbPad', tuple(tb), (0.02 * k, 0.017 * k, 0.03 * k), M['graph'], axis=(tb - fa, tb + fa), sub=2)
    p = tb + fa * 0.012 * k
    dvec = (fa * 0.82 + W * 0.22 + npalm * 0.42).normalized(); r = 0.0135 * k
    for si, (Lt, c_) in enumerate(((0.042, 0.0), (0.034, 0.3))):
        dvec = (dvec * math.cos(c_) + (npalm * 0.8 - W * 0.2).normalized() * math.sin(c_)).normalized()
        q = p + dvec * Lt * k
        seg(B, 'GloveThumb', p, q, r, r * 0.9, M['graph'], n=10)
        ellip(B, 'GloveThumbJoint', tuple(p), (r * 1.05,) * 3, M['graph'], sub=1)
        back = (W - dvec * W.dot(dvec)).normalized()
        ellip(B, 'GloveThumbCap', tuple(p.lerp(q, 0.5) - npalm * r * 0.4 + back * r * 0.25), (r * 1.02, r * 1.02, Lt * k * 0.44), M['shell'], axis=(p, q), sub=2)
        p = q; r *= 0.9
    ellip(B, 'GloveThumbTip', tuple(p), (r, r, r * 1.1), M['graph'], axis=(p - dvec * 0.01, p), sub=2)

def boot(B, M, ank, gz, s, k, h):
    """armored moon boot: graphite boot body lofted heel->toe, white sculpted toe cap and heel counter, ankle guard discs,
    accent strap, thick rubber sole with tread lugs. Aligned to the ground (yaw only)."""
    X, Y, Z = Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0))      # section x = side, y = up, t = forward
    kw = 0.95 + 0.05 * k
    sole_t = 0.038
    org = Vector((ank.x, ank.y + 0.085, gz + sole_t))
    Lb = 0.31
    BF = surf(org, X, Y, Z, [(0.0, 0.052 * kw, 0.05, 0.045), (0.05, 0.06 * kw, 0.085, 0.075), (0.11, 0.063 * kw, 0.08, 0.07), (0.17, 0.064 * kw, 0.055, 0.045),
                             (0.24, 0.062 * kw, 0.042, 0.033), (0.29, 0.052 * kw, 0.033, 0.026), (Lb, 0.036 * kw, 0.024, 0.02)], ex=2.6)
    shell(B, 'Boot', BF, 0.0, Lb, 0, TAU, M['graph'], off=0.0, thick=0.0, caps=True, nv=30, nu=30)
    shell(B, 'BootToe', BF, lambda a: 0.185 + 0.035 * (1 - math.cos(a)), Lb + 0.004, *arc(0.0, 1.65), M['shell'], off=(0.004, 0.007), thick=0.007, nv=26)
    shell(B, 'BootToeRidge', BF, 0.2, 0.28, *arc(0.0, 0.1), M['paint'], off=0.009, thick=0.004, nv=3)
    shell(B, 'BootHeel', BF, -0.004, lambda a: 0.07 - 0.02 * (1 - math.cos(a)) * 0.5, *arc(0.0, 1.85), M['shell'], off=(0.008, 0.004), thick=0.007, nv=24)
    shell(B, 'BootStrap', BF, 0.13, 0.155, *arc(0.0, 1.9), M['paint'], off=0.005, thick=0.005, nv=20)
    for q in (1, -1):        # ankle guard discs
        c = Vector((ank.x + q * 0.064 * kw, ank.y + 0.01, gz + sole_t + 0.07))
        seg(B, 'BootAnkleGuard', c - X * q * 0.004, c + X * q * 0.012, 0.036, 0.03, M['shell'], n=24)
        seg(B, 'BootAnkleHub', c + X * q * 0.012, c + X * q * 0.017, 0.016, 0.013, M['graph'], n=16)
    SF_ = surf(Vector((ank.x, ank.y + 0.093, gz + sole_t * 0.5)), X, Y, Z,
               [(0.0, 0.056 * kw, sole_t * 0.5), (0.06, 0.066 * kw, sole_t * 0.5), (0.2, 0.07 * kw, sole_t * 0.5), (0.29, 0.066 * kw, sole_t * 0.5),
                (Lb + 0.012, 0.04 * kw, sole_t * 0.45)], ex=6.0)
    shell(B, 'BootSole', SF_, 0.0, Lb + 0.012, 0, TAU, M['graph'], off=0.0, thick=0.0, caps=True, nv=28, nu=20)
    for i in range(7):       # tread lugs
        ty = ank.y + 0.075 - i * 0.045
        for q in (1, -1):
            rbox(B, 'BootTread', (0.042 * kw, 0.028, 0.012), (ank.x + q * 0.027 * kw, ty, gz + 0.004), M['under'], rot=(0, 0, q * 0.25 * (1 if i % 2 else -1)), bevel=0.003, segs=1)

def crew_member(loc, rot_z=0.0, variant='A', pose='stand', name=None):
    P = suit_params(variant); M = mats(P['accent']); po = POSES[pose]; h = P['h']; k = P['limb']; fem = P['female']; tw = P['tw']
    root = bpy.data.objects.new(name or ('Crew' + variant), None); coll(C).objects.link(root)
    B = _B(root)
    PI, HP = math.pi, math.pi / 2
    kb = k * 1.12                       # pressure-suit bulk on every limb
    hipz = 0.935 * h; thigh, shin = 0.43 * h, 0.425 * h
    legs = {}
    for s in (1, -1):
        pt, bend = po['legs'][s]
        hip = Vector((s * P['hip_w'], 0, hipz)); knee = hip + _limb_dir(pt) * thigh
        sd = _limb_dir(pt - bend); ank = knee + sd * shin
        legs[s] = (hip, knee, ank, sd)
    dz = -(min(l[2].z for l in legs.values()) - 0.082 * h)       # lowest ankle at 8.2% h above the ground
    # ---------------- legs: thick pressure layer with knee folds, two-lame thigh shell, domed kneecap, keeled two-lame shin, boot
    for s in (1, -1):
        hip, knee, ank = [v + Vector((0, 0, dz)) for v in legs[s][:3]]
        gz = min(ank.z - 0.082 * h, ank.z - 0.075)
        a, Lz, X, Y, Z = _lframe(hip, knee)
        TF = surf(a, X, Y, Z, _keys(Lz, [(0.0, 0.086 * kb * tw, 0.08 * kb * tw, 0.0, s * 0.004), (0.28, 0.08 * kb * tw, 0.084 * kb * tw, 0.009, s * 0.007),
                                          (0.7, 0.06 * kb, 0.062 * kb, 0.005, s * 0.002), (1.0, 0.05 * kb, 0.054 * kb, 0.0)]), ex=2.2)
        shell(B, 'Thigh', TF, -0.02, Lz + 0.04, 0, TAU, M['under'], off=bellows(-0.004, [(0.8 * Lz, Lz + 0.04)]), thick=0.0, nv=26, nu=int(Lz / 0.004))
        shell(B, 'ThighPlate', TF, lambda a: Lz * (0.06 - 0.05 * math.cos(a - s * HP)), lambda a: Lz * (0.54 + 0.035 * math.cos(a)), *arc(s * 0.5, 2.2), M['shell'], off=(0.006, 0.012), thick=0.007)
        shell(B, 'ThighPlateLow', TF, lambda a: Lz * (0.47 + 0.03 * math.cos(a)), lambda a: Lz * (0.8 + 0.08 * max(0.0, math.cos(a)) ** 3), *arc(s * 0.3, 1.95), M['shell'], off=(0.005, 0.009), thick=0.006)
        shell(B, 'ThighStripe', TF, 0.14 * Lz, 0.42 * Lz, *arc(s * HP * 0.92, 0.11), M['paint'], off=(0.0115, 0.0145), thick=0.005, nv=4)
        shell(B, 'HamPlate', TF, 0.14 * Lz, 0.74 * Lz, *arc(PI, 1.0), M['graph'], off=0.004, thick=0.006)
        a2, Ls, X2, Y2, Z2 = _lframe(knee, ank)
        sk = [(0.0, 0.05 * kb, 0.052 * kb, 0.0), (0.24, 0.058 * kb, 0.06 * kb, -0.008), (0.62, 0.045 * kb, 0.047 * kb, -0.002), (1.0, 0.038 * kb, 0.042 * kb, 0.0)]
        SF = surf(a2, X2, Y2, Z2, _keys(Ls, sk), ex=2.2)
        SG = surf(a2, X2, Y2, Z2, _keys(Ls, [r + (0.0, P['keel'] + 0.006) for r in sk]), ex=2.2, kpow=10)
        shell(B, 'Shin', SF, -0.04, Ls, 0, TAU, M['under'], off=bellows(-0.004, [(-0.04, 0.16 * Ls)]), thick=0.0, nv=26, nu=int(Ls / 0.004))
        shell(B, 'ShinGuard', SG, lambda a: Ls * (0.13 - 0.08 * max(0.0, math.cos(a)) ** 4), lambda a: Ls * (0.52 + 0.03 * math.cos(a)), *arc(0.0, 2.0), M['shell'], off=(0.007, 0.012), thick=0.007)
        shell(B, 'ShinGuardLow', SG, lambda a: Ls * (0.47 + 0.03 * math.cos(a)), lambda a: Ls * (0.78 + 0.05 * max(0.0, math.cos(a)) ** 2), *arc(0.0, 1.85), M['shell'], off=(0.005, 0.009), thick=0.006)
        shell(B, 'CalfPlate', SF, 0.12 * Ls, 0.62 * Ls, *arc(PI, 1.15), M['graph'], off=0.004, thick=0.006)
        td, sdn = (knee - hip).normalized(), (ank - knee).normalized()
        ellip(B, 'KneeJoint', tuple(knee), (0.06 * kb, 0.06 * kb, 0.064 * kb), M['under'], axis=(knee - td, knee + sdn), sub=3)
        k0, k1 = knee - td * 0.08 * kb, knee + sdn * 0.09 * kb
        ka, Lk, KX, KY, KZ = _lframe(k0, k1)
        KF = surf(ka, KX, KY, KZ, _keys(Lk, [(0.0, 0.048 * kb, 0.042 * kb, 0.008), (0.3, 0.06 * kb, 0.052 * kb, 0.022, 0, 0.008), (0.62, 0.057 * kb, 0.052 * kb, 0.024, 0, 0.011),
                                              (1.0, 0.045 * kb, 0.04 * kb, 0.012, 0, 0.002)]), ex=2.0, kpow=6)
        shell(B, 'KneeCap', KF, 0.0, Lk, *arc(0.0, 1.5), M['shell'], off=(0.004, 0.006), thick=0.008, nv=26, nu=16)
        shell(B, 'KneeCapInlay', KF, 0.3 * Lk, 0.7 * Lk, *arc(0.0, 0.13), M['paint'], off=0.0085, thick=0.004, nv=4)
        for q in (1, -1):
            shell(B, 'KneeSide', KF, 0.25 * Lk, 0.8 * Lk, *arc(q * 1.8, 0.32), M['graph'], off=-0.002, thick=0.006, nv=6)
        # boot shaft: graphite pressure cuff + flared white boot cuff, then the armored boot
        shell(B, 'BootShaft', SF, 0.76 * Ls, Ls + 0.05, 0, TAU, M['graph'], off=(0.006, 0.012), thick=0.006, nv=28)
        shell(B, 'BootCuff', SF, 0.7 * Ls, 0.8 * Ls, 0, TAU, M['shell'], off=(0.01, 0.022), thick=0.007, nv=30)
        shell(B, 'BootCuffStripe', SF, 0.735 * Ls, 0.75 * Ls, *arc(0.0, 2.6), M['paint'], off=0.0185, thick=0.004, nv=26)
        boot(B, M, ank, gz, s, k, h)
    hipz += dz
    # ---------------- torso frame (lean)
    lean = po['lean']; X = Vector((1, 0, 0)); Z = Vector((0, -math.sin(lean), math.cos(lean))); Y = Z.cross(X) * -1   # Y = front (-Y)
    if Y.y > 0: Y = -Y
    org = Vector((0, 0, hipz)); up = Z
    pw, pd = P['pel']; ww, wd = P['waist']; rw, rd = P['ribs']; cw, cd = P['chest']; uw, ud = P['upch']; bst = P['bust']; kl = P['keel']; lb = P['lobe']
    T = lambda z: (z - 0.935) * h        # body height -> torso param
    TF = surf(org, X, Y, Z, [(T(0.84), pw * 0.8, pd * 0.84), (T(0.93), pw * 0.95, pd * 0.98), (T(0.99), pw * 0.97, pd), (T(1.07), ww, wd),
                             (T(1.17), rw * 0.97, rd * 0.97, 0, 0, kl * 0.4), (T(1.25), cw * 0.97, cd * 0.97 + bst * 0.1, bst * 0.05, 0, kl, lb * 0.33),
                             (T(1.32), cw * 1.0, cd * 1.0 + bst * 0.2, bst * 0.1, 0, kl, lb), (T(1.37), cw * 1.0, cd * 1.0 + bst * 0.15, bst * 0.08, 0, kl, lb * 0.73),
                             (T(1.42), uw * 0.97, ud * 0.98, 0, 0, kl * 0.5, lb * 0.15), (T(1.48), 0.104, 0.094, -0.004)], ex=2.25)
    shell(B, 'TorsoUnder', TF, T(0.84), T(1.5), 0, TAU, M['under'], off=bellows(0.0, [(T(1.035), T(1.16))], amp=0.006, pitch=0.026), thick=0.0, caps=True, nv=40, nu=120)
    # cuirass: graphite core + white plates overlapping like shingles; pecs meet on a sternum ridge (keel)
    shell(B, 'CuirassCore', TF, T(1.15), T(1.465), 0, TAU, M['graph'], off=0.004, thick=0.005, nv=40)
    for s in (1, -1):
        pa = (0.0, 1.42) if s > 0 else (-1.42, 0.0)
        shell(B, 'ChestPlate', TF, lambda a: T(1.25) + 0.03 * h * math.sin(a) ** 2, lambda a: T(1.438) - 0.012 * h * math.sin(a) ** 2, *pa, M['shell'], off=(0.0145, 0.0105), thick=0.008, nv=26, nu=24)
        ra = (0.0, 1.46) if s > 0 else (-1.46, 0.0)
        shell(B, 'RibPlate', TF, T(1.165), T(1.27), *ra, M['shell'], off=(0.0085, 0.0095), thick=0.006, nv=20)
        shell(B, 'ChestAccent', TF, T(1.34), T(1.415), *((1.12, 1.3) if s > 0 else (-1.3, -1.12)), M['paint'], off=0.0145, thick=0.004, nv=4)
        def _on_pec(t, a, u):       # follow the pec plate's eased offset so the small panel sits flush on it
            c0 = T(1.25) + 0.03 * h * math.sin(a) ** 2; c1 = T(1.438) - 0.012 * h * math.sin(a) ** 2
            up_ = min(1.0, max(0.0, (t - c0) / (c1 - c0))); return 0.0145 - 0.004 * up_ * up_ + 0.0016
        shell(B, 'ChestInset', TF, T(1.385), T(1.418), *((0.42, 0.86) if s > 0 else (-0.86, -0.42)), M['graph'], off=_on_pec, thick=0.0022, nv=10, bevel=0.0008)
        for v_ in range(3):          # rib vents
            z0 = 1.19 + v_ * 0.022
            shell(B, 'RibVent', TF, T(z0), T(z0 + 0.009), *((0.95, 1.25) if s > 0 else (-1.25, -0.95)), M['graph'], off=0.0108, thick=0.003, nv=5)
        shell(B, 'SidePlate', TF, T(1.2), T(1.38), *arc(s * 1.72, 0.24), M['graph'], off=0.009, thick=0.006, nv=5)
    shell(B, 'SternumRidge', TF, T(1.265), T(1.43), *arc(0.0, 0.05), M['shell'], off=(0.0162, 0.0122), thick=0.004, nv=4)
    shell(B, 'CollarPlate', TF, T(1.398), T(1.478), *arc(0.0, 1.32), M['shell'], off=(0.0165, 0.0125), thick=0.007, nv=24)
    shell(B, 'BackPlate', TF, T(1.18), T(1.45), 1.95, TAU - 1.95, M['shell'], off=(0.012, 0.01), thick=0.007, nv=16)
    for i, (z0, z1) in enumerate(((1.128, 1.168), (1.093, 1.135), (1.058, 1.1))):     # ab bands, each tucks under the one above
        shell(B, 'AbPlate', TF, T(z0), T(z1), *arc(0.0, 0.98 if not fem else 0.88), M['shell'], off=(0.0105 - 0.001 * i, 0.006 - 0.001 * i), thick=0.006, nv=18)
    shell(B, 'Belt', TF, T(0.985), T(1.04), 0, TAU, M['graph'], off=0.007, thick=0.006, nv=40)
    shell(B, 'BeltTrim', TF, T(1.028), T(1.04), 0, TAU, M['shell'], off=0.0085, thick=0.003, nv=40)
    shell(B, 'BeltTrimLow', TF, T(0.985), T(0.995), 0, TAU, M['shell'], off=0.0085, thick=0.003, nv=40)
    # hips: layered plates (graphite plate on a white trim plate) front + rear, two-lame side faulds
    shell(B, 'FauldFront', TF, T(0.935), T(0.99), *arc(0.0, 0.78), M['shell'], off=(0.0125, 0.009), thick=0.006, nv=18)
    shell(B, 'FauldFrontInner', TF, T(0.944), T(0.981), *arc(0.0, 0.7), M['graph'], off=(0.0145, 0.0115), thick=0.003, nv=16)
    shell(B, 'Codpiece', TF, lambda a: T(0.858) + 0.034 * h * abs(math.sin(a)), T(0.95), *arc(0.0, 0.5), M['shell'], off=(0.006, 0.0105), thick=0.007, nv=14)
    shell(B, 'CodpieceInset', TF, lambda a: T(0.885) + 0.03 * h * abs(math.sin(a)), T(0.928), *arc(0.0, 0.22), M['graph'], off=0.0108, thick=0.003, nv=8)
    shell(B, 'RearPlate', TF, T(0.875), T(0.99), *arc(PI, 0.95), M['shell'], off=(0.016, 0.01), thick=0.007, nv=14)
    shell(B, 'RearPlateInner', TF, T(0.888), T(0.978), *arc(PI, 0.85), M['graph'], off=(0.0185, 0.0125), thick=0.004, nv=12)
    for s in (1, -1):
        shell(B, 'HipPlate', TF, T(0.885), T(0.99), *arc(s * HP, 0.68 if not fem else 0.72), M['graph'], off=(0.032, 0.012), thick=0.007, nv=14)
        shell(B, 'HipPlateTrim', TF, T(0.885), T(0.9), *arc(s * HP, 0.7 if not fem else 0.74), M['shell'], off=0.0335, thick=0.004, nv=14)
        shell(B, 'HipPlateLow', TF, T(0.83), T(0.9), *arc(s * HP, 0.56 if not fem else 0.6), M['shell'], off=(0.046, 0.03), thick=0.006, nv=12)
        shell(B, 'HipStripe', TF, T(0.955), T(0.97), *arc(s * HP, 0.45), M['paint'], off=0.0245, thick=0.004, nv=8)
    # chest control unit (replaces the old strap plate): housing, screen, buttons, a dial
    cu = TF(T(1.205), 0.0, 0.014)
    rc = (-lean - 0.1, 0, 0)
    rbox(B, 'ChestUnit', (0.13 if not fem else 0.115, 0.05, 0.07), tuple(cu + Y * 0.012), M['graph'], rot=rc, bevel=0.01, segs=3)
    rbox(B, 'ChestUnitFrame', (0.138 if not fem else 0.123, 0.03, 0.078), tuple(cu + Y * 0.004), M['shell'], rot=rc, bevel=0.008, segs=2)
    rbox(B, 'ChestScreen', (0.06, 0.006, 0.03), tuple(cu + Y * 0.038 + Z * 0.01 - X * 0.015), M['glow'], rot=rc, bevel=0.0, segs=1)
    for bi in range(3):
        bpos = cu + Y * 0.037 - Z * 0.02 + X * (-0.035 + bi * 0.018)
        seg(B, 'ChestButton', bpos, bpos + Y * 0.006, 0.0055, 0.005, M['paint'] if bi == 0 else M['shell'], n=12)
    dpos = cu + Y * 0.037 + X * 0.042
    seg(B, 'ChestDial', dpos, dpos + Y * 0.01, 0.014, 0.012, M['shell'], n=20)
    # sealed neck ring: wide graphite bearing ring + accent band; the helmet sits down into it
    nk = org + Z * T(1.475)
    shell(B, 'Collar', TF, T(1.45), T(1.505), 0, TAU, M['shell'], off=(0.008, 0.014), thick=0.009, nv=40)
    seg(B, 'NeckSeal', nk - up * 0.005, nk + up * 0.052, 0.108, 0.098, M['graph'], n=40)
    seg(B, 'NeckSealRing', nk + up * 0.02, nk + up * 0.032, 0.111, 0.109, M['paint'], n=40)
    seg(B, 'NeckSealLip', nk + up * 0.046, nk + up * 0.056, 0.1, 0.094, M['shell'], n=40)
    head = nk + up * 0.168
    hp = helmet(B, M, tuple(head), yaw=po['yaw'], pitch=po['hp'])
    # ---------------- life-support backpack (reads in silhouette): main shell, side O2 tanks, top radiator hump, hoses
    bp = org + Z * T(1.28) - Y * (cd * 1.08 + 0.105)
    rot_bp = (-lean, 0, 0)
    bw_ = 0.4 if not fem else 0.36
    rbox(B, 'Backpack', (bw_, 0.18, 0.54), tuple(bp), M['shell'], rot=rot_bp, bevel=0.045, segs=4)
    rbox(B, 'BackpackCore', (bw_ * 0.62, 0.03, 0.36), tuple(bp - Y * 0.095), M['graph'], rot=rot_bp, bevel=0.01)
    rbox(B, 'BackpackTop', (bw_ * 0.8, 0.14, 0.07), tuple(bp + Z * 0.29 - Y * 0.01), M['graph'], rot=rot_bp, bevel=0.025, segs=3)
    for fi in range(5):
        rbox(B, 'BackpackFin', (bw_ * 0.72, 0.006, 0.03), tuple(bp + Z * 0.31 - Y * (0.06 - fi * 0.028)), M['shell'], rot=rot_bp, bevel=0.002, segs=1)
    rbox(B, 'BackpackLight', (0.14, 0.006, 0.014), tuple(bp - Y * 0.112 + Z * 0.15), M['glow'], rot=rot_bp, bevel=0.0, segs=1)
    rbox(B, 'BackpackBase', (bw_ * 0.9, 0.16, 0.05), tuple(bp - Z * 0.29), M['graph'], rot=rot_bp, bevel=0.015, segs=2)
    for s in (1, -1):
        tc_ = bp + X * (s * (bw_ / 2 + 0.03)) - Y * 0.0
        seg(B, 'BackpackTank', tc_ - Z * 0.22, tc_ + Z * 0.2, 0.046, 0.046, M['shell'], n=24)
        ellip(B, 'BackpackTankCap', tuple(tc_ + Z * 0.2), (0.046, 0.046, 0.028), M['shell'], sub=3)
        ellip(B, 'BackpackTankCapLow', tuple(tc_ - Z * 0.22), (0.046, 0.046, 0.028), M['shell'], sub=3)
        seg(B, 'BackpackTankBand', tc_ + Z * 0.1, tc_ + Z * 0.125, 0.049, 0.049, M['paint'], n=24)
        seg(B, 'BackpackTankBand2', tc_ - Z * 0.12, tc_ - Z * 0.1, 0.049, 0.049, M['graph'], n=24)
        a0 = bp + X * (s * 0.09) + Y * 0.09 + Z * 0.24; a1 = org + Z * T(1.47) + X * (s * 0.1)
        rbox(B, 'HarnessStrap', (0.04, 0.012, (a1 - a0).length + 0.03), tuple((a0 + a1) / 2), M['graph'],
             rot=((a1 - a0).to_track_quat('Z', 'X').to_euler()), bevel=0.004, segs=1)
        # ribbed umbilical hose: backpack base -> around the waist side -> chest unit
        h0 = bp + X * (s * bw_ * 0.32) - Z * 0.27 + Y * 0.02
        h1 = org + Z * T(1.1) + X * (s * (ww + 0.05)) - Y * 0.03
        h2 = org + Z * T(1.16) + X * (s * (rw * 0.75)) + Y * (rd + 0.04)
        h3 = cu + X * (s * 0.07) + Y * 0.02
        hose(B, 'Hose', [h0, h1, h2, h3], 0.0115, M['graph'], n=10, rib=0.18, per=0.014)
    # ---------------- arms: pressure layer with elbow folds, bicep shell, elbow cop, two-lame forearm + flared cuff,
    #                  articulated glove, 2-piece pauldron ON the shoulder (inner side open so it never covers the chest)
    for s in (1, -1):
        pt, ab, el = po['arms'][s]
        sh = org + Z * T(1.415) + X * (s * P['sh_w'])
        ua = _limb_dir(pt, ab, s); elb = sh + ua * 0.3 * h
        fa = _limb_dir(pt + el, ab * 0.6, s); hand = elb + fa * 0.255 * h
        ellip(B, 'ShoulderJoint', tuple(sh), (0.066 * kb, 0.066 * kb, 0.066 * kb), M['under'], sub=3)
        a, Lu, AX, AY, AZ = _lframe(sh, elb)
        UF = surf(a, AX, AY, AZ, _keys(Lu, [(0.0, 0.052 * kb, 0.052 * kb), (0.42, 0.053 * kb, 0.056 * kb, 0.003), (1.0, 0.043 * kb, 0.044 * kb)]), ex=2.2)
        shell(B, 'UpperArm', UF, 0.0, Lu + 0.035, 0, TAU, M['under'], off=bellows(-0.003, [(0.8 * Lu, Lu + 0.035)], amp=0.005), thick=0.0, nv=22, nu=int(Lu / 0.004))
        shell(B, 'BicepPlate', UF, 0.26 * Lu, 0.84 * Lu, *arc(s * HP * 0.8, 2.25), M['shell'], off=(0.005, 0.009), thick=0.006)
        ellip(B, 'Elbow', tuple(elb), (0.048 * kb, 0.048 * kb, 0.048 * kb), M['under'], sub=3)
        e0, e1 = elb - ua * 0.058 * kb, elb + fa * 0.062 * kb
        ea, Le, EX, EY, EZ = _lframe(e0, e1)
        EF = surf(ea, EX, EY, EZ, _keys(Le, [(0.0, 0.038 * kb, 0.034 * kb), (0.5, 0.05 * kb, 0.049 * kb, -0.013), (1.0, 0.039 * kb, 0.035 * kb)]), ex=2.0)
        shell(B, 'ElbowCop', EF, 0.0, Le, *arc(PI, 1.45), M['shell'], off=0.004, thick=0.007, nv=18, nu=12)
        b_, Lf, FX, FY, FZ = _lframe(elb, hand)
        FF = surf(b_, FX, FY, FZ, _keys(Lf, [(0.0, 0.046 * kb, 0.045 * kb), (0.28, 0.05 * kb, 0.048 * kb), (1.0, 0.036 * kb, 0.034 * kb)]), ex=2.2)
        shell(B, 'Forearm', FF, -0.03, Lf, 0, TAU, M['under'], off=bellows(-0.003, [(-0.03, 0.14 * Lf)], amp=0.005), thick=0.0, nv=22, nu=int(Lf / 0.004))
        shell(B, 'Gauntlet', FF, 0.12 * Lf, 0.58 * Lf, *arc(s * HP * 0.7, 2.4), M['shell'], off=(0.005, 0.009), thick=0.006)
        shell(B, 'GauntletLow', FF, 0.52 * Lf, 0.82 * Lf, *arc(s * HP * 0.7, 2.25), M['shell'], off=(0.004, 0.007), thick=0.006)
        shell(B, 'WristLight', FF, 0.79 * Lf, 0.83 * Lf, 0, TAU, M['glow'], off=0.006, thick=0.003, nv=24)
        shell(B, 'Cuff', FF, 0.83 * Lf, 1.0 * Lf, 0, TAU, M['shell'], off=(0.006, 0.016), thick=0.006, nv=28)
        glove(B, M, hand, fa, s, k * 1.16)
        pw_, pd_, pk = P['paul']
        a0 = sh + X * (s * 0.016) + Z * 0.006
        PZ = ua.normalized(); PY = Vector((s, 0, 0)); PY = (PY - PZ * PY.dot(PZ)).normalized(); PX = PY.cross(PZ).normalized()   # a = 0 -> outward
        PF = surf(a0, PX, PY, PZ, [(-0.108 * pk, pd_ * 0.16, pw_ * 0.14), (-0.092 * pk, pd_ * 0.64, pw_ * 0.6, 0, 0, 0.003), (-0.06 * pk, pd_ * 0.96, pw_ * 0.93, 0, 0, 0.006),
                                   (-0.02 * pk, pd_ * 1.05, pw_ * 1.04, 0, 0, 0.007), (0.03 * pk, pd_ * 1.02, pw_ * 1.0, 0, 0, 0.005), (0.08 * pk, pd_ * 0.9, pw_ * 0.88, 0, 0, 0.002)],
                  ex=2.0, kpow=6)
        shell(B, 'PauldronUnder', PF, -0.03 * pk, 0.085 * pk, *arc(0.0, 2.3), M['graph'], off=0.0, thick=0.005, nv=30)
        shell(B, 'Pauldron', PF, -0.108 * pk, 0.034 * pk, *arc(0.0, 2.35), M['shell'], off=(0.004, 0.019), thick=0.009, nv=38, nu=24)
        shell(B, 'PauldronLame', PF, 0.022 * pk, 0.08 * pk, *arc(0.0, 2.15), M['shell'], off=(0.006, 0.011), thick=0.007, nv=30)
        shell(B, 'PauldronStripe', PF, -0.004 * pk, 0.01 * pk, *arc(0.0, 1.3), M['paint'], off=0.0165, thick=0.005, nv=20)
    # per-vertex height above the soles (drives the boot-ward dust/scratch gradient in the materials)
    for ob in root.children_recursive:
        if ob.type != 'MESH': continue
        Mrel = ob.matrix_basis.copy()
        if ob.parent is not None and ob.parent != root: Mrel = ob.parent.matrix_basis @ Mrel
        me = ob.data; at = me.attributes.get('ht') or me.attributes.new('ht', 'FLOAT', 'POINT')
        at.data.foreach_set('value', [(Mrel @ v.co).z for v in me.vertices])
    root.location = loc; root.rotation_euler = (0, 0, rot_z)
    return root
