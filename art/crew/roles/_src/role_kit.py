"""Planet Stack - modular crew role kits on the ONE shared crew suit.
    import role_kit as RK;  root = RK.role_member('miner', loc, rot_z)      (Blender 4.2, Z-up, crew faces -Y at rot_z = 0)
The suit is suit_base.py = verbatim copy of crew_pass3.py (Art Assistant 2's pass-3 crew.py snapshot, md5 8016ecce...).
suit_base is NOT edited; this module hooks it:
  * mats()        -> the role's accent paint replaces the cyan stripe paint; the cyan glow lights stay (shared cyan base)
  * glove()       -> the right hand gets a closed power grip around a handle and records the grip frame (GRIP)
  * POSES         -> a per-role 'hold' pose (right arm from roles_table.arm_r, left arm relaxed)
then adds the role kit: accent pauldron lames, helmet badges (both temples), tool in the right hand, extras.
Every kit part gets the 'ht' vertex attribute so the suit's dust/wear shaders treat it like the suit."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', '..', '3d', 'mine_concepts', '_src'))); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import suit_base as S
import roles_table as RT
from mc_common import hexc, _obj, coll, M_glow

TAU = 2 * math.pi
STRONG = os.environ.get('ROLES_STRONG', '1') == '1'   # v3 phone-size read: chest plate + upper-arm plates in role colour, less dust/wear on the paint
CUR = {}          # role being built
GRIP = {}         # grip frame of the tool hand (root space): c (handle centre), ax (handle axis, thumb side), fa, npalm, rh
TOOL_SIDE = -1    # -X = the crew member's RIGHT (faces -Y)
RH = 0.0175       # handle radius every tool uses at the grip

# ---------------------------------------------------------------- materials
_orig_mats = S.mats
def role_mats(key):
    if key in S._M: return S._M[key]
    if key not in RT.ROLES: return _orig_mats(key)
    base = _orig_mats('cyan'); acc = RT.ROLES[key]['accent']
    if STRONG:   # cleaner, saturated paint so the accent survives AgX + dust at 20 px
        paint = S._shell_mat('C_Accent_' + key, acc, 0.3, 0.9, bump=0.2, micro=60.0, dust=0.22, scratch=0.35,
                             dust_col='#8f8a82', scr_col='#c9ccd0', wear_col='#d8dadd', wear=0.25)
    else:
        paint = S._shell_mat('C_Accent_' + key, acc, 0.24, 0.9, bump=0.2, micro=60.0, dust=0.6, scratch=0.7,
                             dust_col='#8f8a82', scr_col='#c9ccd0', wear_col='#e8eaed', wear=0.8)
    S._M[key] = dict(base, paint=paint, glow=base['cyan'])
    return S._M[key]
S.mats = role_mats

def kit_mats(key):
    M = role_mats(key)
    if 'steel' not in S._M:
        S._M['steel'] = S._shell_mat('C_ToolSteel', '#9aa1a9', 0.28, 0.2, metal=0.85, bump=0.25, micro=80.0, dust=0.5, scratch=1.0,
                                     dust_col='#8a857d', scr_col='#d4d8dc', wear_col='#c8ccd0', wear=0.9, grime=0.4)
        S._M['rubber'] = S._shell_mat('C_ToolGrip', '#1b1e23', 0.65, 0.0, bump=0.4, micro=300.0, fabric=True, dust=0.5, dust_col='#6e6a63')
        S._M['screen'] = M_glow('C_ScreenGlow', '#59dcff', 3.5)
    if 'aglow_' + key not in S._M:
        S._M['aglow_' + key] = M_glow('C_AccentGlow_' + key, RT.ROLES[key]['accent'], 5.0)
    return dict(M, steel=S._M['steel'], rubber=S._M['rubber'], screen=S._M['screen'], aglow=S._M['aglow_' + key])

_orig_params = S.suit_params
def role_params(variant):
    P = _orig_params(variant)
    if CUR.get('key'): P['accent'] = CUR['key']
    return P
S.suit_params = role_params

# ---------------------------------------------------------------- closed power-grip glove (right hand)
_orig_glove = S.glove
def grip_glove(B, M, hand, fa, s, k):
    fa = Vector(fa).normalized()
    inward = Vector((-s, 0, 0)); npalm = (inward - fa * inward.dot(fa)).normalized()
    npalm = Matrix.Rotation(CUR.get('roll', 0.0), 3, fa) @ npalm          # wrist roll: leans the held tool out of the body silhouette
    W = fa.cross(npalm).normalized()
    ref = Vector((0, 0, 1)) if abs(fa.z) < 0.8 else Vector((0, -1, 0))
    if W.dot(ref) < 0: W = -W                      # +W = thumb side (up for a forward forearm)
    org = hand - fa * 0.012; Lp = 0.098 * k
    PF = S.surf(org, npalm, W, fa, [(0.0, 0.025 * k, 0.04 * k), (0.05 * k, 0.024 * k, 0.048 * k), (Lp, 0.019 * k, 0.047 * k)], ex=3.0)
    S.shell(B, 'GlovePalm', PF, 0.0, Lp, 0, TAU, M['graph'], off=0.0, thick=0.0, caps=True, nv=28)
    S.shell(B, 'GloveBackPlate', PF, 0.004 * k, 0.062 * k, *S.arc(-math.pi / 2, 1.3), M['shell'], off=(0.004, 0.006), thick=0.006, nv=18)
    S.shell(B, 'GloveKnucklePlate', PF, 0.055 * k, Lp + 0.006, *S.arc(-math.pi / 2, 1.35), M['shell'], off=(0.007, 0.009), thick=0.006, nv=18)
    S.shell(B, 'GloveBackStripe', PF, 0.02 * k, 0.05 * k, *S.arc(-math.pi / 2, 0.16), M['paint'], off=0.0095, thick=0.004, nv=4)
    # handle axis line: just past the palm's end, in front of the finger roots
    p_root = org + fa * (Lp + 0.002) - npalm * 0.002
    c = p_root + fa * 0.016 + npalm * 0.033
    xs = (0.033, 0.011, -0.011, -0.032); Ls = (0.082, 0.092, 0.087, 0.07); fr = (0.45, 0.32, 0.23)
    for xi, Lf in zip(xs, Ls):
        p = p_root + W * (xi * k)
        S.ellip(B, 'GloveKnuckle', tuple(p - npalm * 0.021 * k - fa * 0.004), (0.0125 * k, 0.0125 * k, 0.009 * k), M['shell'], sub=2)
        cf = c + W * (xi * k); r = 0.012 * k
        v = p - cf; phi = math.atan2(v.dot(npalm), v.dot(fa))
        for si, f_ in enumerate(fr):
            rho = RH + r * 0.92 + 0.0015
            phi += (Lf * k * f_) / rho
            q = cf + (fa * math.cos(phi) + npalm * math.sin(phi)) * rho
            r1 = r * 0.9
            S.seg(B, 'GloveFinger', p, q, r, r1, M['graph'], n=10)
            S.ellip(B, 'GloveFingerJoint', tuple(p), (r * 1.05,) * 3, M['graph'], sub=1)
            if si < 2:
                mid = p.lerp(q, 0.5); back = (mid - cf); back = (back - W * back.dot(W)).normalized()
                S.ellip(B, 'GloveFingerCap', tuple(mid + back * r * 0.5), (r * 1.02, r * 1.02, (q - p).length * 0.44), M['shell'], axis=(p, q), sub=2)
            p = q; r = r1
        S.ellip(B, 'GloveFingertip', tuple(p), (r, r, r * 1.1), M['graph'], sub=2)
    # thumb: padded base on the palm's thumb edge, wraps over the handle and rests on the index/middle fingers
    tb = org + fa * (0.03 * k) + W * (0.04 * k) + npalm * (0.014 * k)
    S.ellip(B, 'GloveThumbPad', tuple(tb), (0.02 * k, 0.017 * k, 0.03 * k), M['graph'], axis=(tb - fa, tb + fa), sub=2)
    rt = 0.0135 * k
    def around(phi_deg, w, extra): a = math.radians(phi_deg); return c + W * w + (fa * math.cos(a) + npalm * math.sin(a)) * (RH + extra)
    pts = [tb + fa * 0.01 * k, around(118, 0.05 * k, 0.03), around(80, 0.026 * k, 0.034)]
    for si in range(2):
        p, q = pts[si], pts[si + 1]
        S.seg(B, 'GloveThumb', p, q, rt, rt * 0.9, M['graph'], n=10)
        S.ellip(B, 'GloveThumbJoint', tuple(p), (rt * 1.05,) * 3, M['graph'], sub=1)
        mid = p.lerp(q, 0.5); back = (mid - c); back = (back - W * back.dot(W)).normalized()
        S.ellip(B, 'GloveThumbCap', tuple(mid + back * rt * 0.45), (rt * 1.02, rt * 1.02, (q - p).length * 0.44), M['shell'], axis=(p, q), sub=2)
        rt *= 0.9
    S.ellip(B, 'GloveThumbTip', tuple(pts[-1]), (rt, rt, rt * 1.1), M['graph'], sub=2)
    GRIP.update(c=c.copy(), ax=W.copy(), fa=fa.copy(), npalm=npalm.copy(), rh=RH)

def hooked_glove(B, M, hand, fa, s, k):
    if s == TOOL_SIDE and CUR.get('grip'): return grip_glove(B, M, hand, fa, s, k)
    return _orig_glove(B, M, hand, fa, s, k)
S.glove = hooked_glove

# ---------------------------------------------------------------- mesh helpers (root space, identity transforms)
class Kit:
    def __init__(s, root): s.root = root; s.parts = []
    def add(s, ob): ob.parent = s.root; s.parts.append(ob); return ob

def _frame_mat(o, X, Y, Z): return Matrix(((X.x, Y.x, Z.x, o.x), (X.y, Y.y, Z.y, o.y), (X.z, Y.z, Z.z, o.z), (0, 0, 0, 1)))

def kbox(K, name, size, center, mat, F, bevel=0.004, segs=2):
    """box of size (sx, sy, sz) centred at local `center` in tool frame F (4x4)."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.transform(bm, matrix=F @ Matrix.Translation(Vector(center)) @ Matrix.Diagonal((*size, 1)), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return K.add(_obj(bm, name, mat, 'Stage', bevel=bevel, segs=segs, angle=30))

def kcyl(K, name, p0, p1, r0, r1, mat, F, n=20, bevel=0.0):
    p0 = F @ Vector(p0); p1 = F @ Vector(p1)
    a, Lz, R3 = S._frame(p0, p1)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n, radius1=r0, radius2=r1, depth=Lz)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(a) @ R3.to_4x4() @ Matrix.Translation((0, 0, Lz / 2)), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return K.add(_obj(bm, name, mat, 'Stage', smooth=True, angle=50, bevel=bevel, segs=2))

def kprism(K, name, loops, h, mat, F, bevel=0.0015):
    """extrude 2D primitives (('fan', loop) / ('ring', outer, inner)) in the tool frame's XY plane from z=0 to z=h."""
    bm = bmesh.new()
    def wall(loop):
        b0 = [bm.verts.new(F @ Vector((u, v, 0))) for u, v in loop]; b1 = [bm.verts.new(F @ Vector((u, v, h))) for u, v in loop]
        for i in range(len(loop)):
            j = (i + 1) % len(loop); bm.faces.new((b0[i], b0[j], b1[j], b1[i]))
        return b0, b1
    for prim in loops:
        if prim[0] == 'fan':
            loop = prim[1]; b0, b1 = wall(loop)
            cu = sum(p[0] for p in loop) / len(loop); cv = sum(p[1] for p in loop) / len(loop)
            t1 = bm.verts.new(F @ Vector((cu, cv, h))); t0 = bm.verts.new(F @ Vector((cu, cv, 0)))
            for i in range(len(loop)):
                j = (i + 1) % len(loop); bm.faces.new((t1, b1[i], b1[j])); bm.faces.new((t0, b0[j], b0[i]))
        else:
            o0, o1 = wall(prim[1]); i0, i1 = wall(prim[2])
            for i in range(len(prim[1])):
                j = (i + 1) % len(prim[1]); bm.faces.new((o1[i], o1[j], i1[j], i1[i])); bm.faces.new((o0[j], o0[i], i0[i], i0[j]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _obj(bm, name, mat, 'Stage', smooth=False)
    if bevel:
        md = ob.modifiers.new('Bevel', 'BEVEL'); md.width = bevel; md.segments = 1; md.limit_method = 'ANGLE'; md.angle_limit = math.radians(40); md.use_clamp_overlap = True
    return K.add(ob)

def ktorus(K, name, R, r, mat, F, a0=0.0, a1=TAU, nu=48, nv=12):
    bm = bmesh.new(); full = abs(a1 - a0 - TAU) < 1e-6; rows = []
    nu_ = nu if full else nu + 1
    for i in range(nu_):
        a = a0 + (a1 - a0) * i / nu; cc = Vector((R * math.cos(a), R * math.sin(a), 0)); rd = Vector((math.cos(a), math.sin(a), 0))
        rows.append([bm.verts.new(F @ (cc + rd * r * math.cos(TAU * j / nv) + Vector((0, 0, r * math.sin(TAU * j / nv))))) for j in range(nv)])
    for i in range(nu if full else nu):
        if not full and i == nu: break
        r0, r1 = rows[i], rows[(i + 1) % nu_]
        if not full and i + 1 >= nu_: break
        for j in range(nv): bm.faces.new((r0[j], r1[j], r1[(j + 1) % nv], r0[(j + 1) % nv]))
    if not full:
        bm.faces.new(rows[0]); bm.faces.new(list(reversed(rows[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return K.add(_obj(bm, name, mat, 'Stage', smooth=True, angle=180))

def grip_frame():
    """tool frame at the grip: Z = handle axis (thumb side), X = finger direction (fa), Y = Z x X."""
    Z = GRIP['ax'].normalized(); X = (GRIP['fa'] - Z * GRIP['fa'].dot(Z)).normalized(); Y = Z.cross(X)
    return _frame_mat(GRIP['c'], X, Y, Z)

def grip_sleeve(K, M, F, z0=-0.075, z1=0.07, mat=None):
    """rubber grip sleeve that the closed fist wraps (radius RH), with end collars."""
    kcyl(K, 'ToolGrip', (0, 0, z0), (0, 0, z1), RH, RH, mat or M['rubber'], F, n=20)
    for z in (z0, z1):
        kcyl(K, 'ToolGripCollar', (0, 0, z - 0.007), (0, 0, z + 0.007), RH + 0.004, RH + 0.004, M['graph'], F, n=20, bevel=0.002)

# ---------------------------------------------------------------- tools (built in the grip frame; Z up the handle)
def tool_rock_pick(K, M, F):
    """Miner: long-haft rock pick. Graphite haft, rubber grip, steel head (long tapered pick spike forward, chisel adze back),
       accent collar band and a cyan status light on the head block."""
    grip_sleeve(K, M, F, -0.08, 0.08)
    kcyl(K, 'PickHaft', (0, 0, -0.30), (0, 0, 0.62), 0.0165, 0.0175, M['graph'], F, n=16)
    kcyl(K, 'PickHaftEnd', (0, 0, -0.33), (0, 0, -0.29), 0.022, 0.02, M['shell'], F, n=16, bevel=0.003)
    kcyl(K, 'PickCollar', (0, 0, 0.46), (0, 0, 0.56), 0.024, 0.024, M['paint'], F, n=20, bevel=0.002)
    Fh = F @ Matrix.Rotation(math.radians(-65), 4, 'Z')        # head yawed about the haft: spike points out to the side so it reads in silhouette
    kbox(K, 'PickBlock', (0.11, 0.062, 0.095), (0, 0, 0.625), M['shell'], Fh, bevel=0.01, segs=2)
    kbox(K, 'PickBlockPanel', (0.065, 0.066, 0.034), (0, 0, 0.625), M['graph'], Fh, bevel=0.003, segs=1)
    kbox(K, 'PickLight', (0.04, 0.068, 0.008), (0, 0, 0.61), M['glow'], Fh, bevel=0.0, segs=1)
    # forward spike: curved, tapering - chain of shrinking boxes along an arc
    for side, L, n, w0, drop in ((1, 0.36, 10, 0.056, 0.10), (-1, 0.17, 5, 0.06, 0.035)):
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            x0, x1 = side * (0.05 + L * t0), side * (0.05 + L * t1)
            z0_, z1_ = 0.625 - drop * t0 ** 2, 0.625 - drop * t1 ** 2
            w = w0 * (1 - 0.82 * t1) if side > 0 else w0 * (1 - 0.25 * t1)
            hgt = w * (0.95 if side > 0 else 0.45 + 0.2 * (1 - t1))
            ang = math.atan2(z1_ - z0_, x1 - x0)
            M4 = Fh @ Matrix.Translation(((x0 + x1) / 2, 0, (z0_ + z1_) / 2)) @ Matrix.Rotation(-ang, 4, 'Y')
            kbox(K, 'PickHead', (abs(x1 - x0) * 1.15, w * 0.8, hgt), (0, 0, 0), M['steel'], M4, bevel=0.003, segs=1)
    kbox(K, 'PickStripe', (0.07, 0.05, 0.014), (0.09, 0, 0.645), M['paint'], Fh, bevel=0.002, segs=1)

def tool_big_wrench(K, M, F):
    """Mechanic: oversized open-end wrench, flat face toward the front (frame X), jaw up, closed ring end below the fist."""
    grip_sleeve(K, M, F, -0.09, 0.09)
    T = 0.018
    # flat bar handle (graphite) from the ring end to the jaw
    kbox(K, 'WrenchBar', (0.018, 0.04, 0.50), (0, 0, 0.12), M['graph'], F, bevel=0.005, segs=2)
    kbox(K, 'WrenchBarInlay', (0.021, 0.012, 0.26), (0, 0, 0.21), M['paint'], F, bevel=0.002, segs=1)
    # open jaw head: thick C ring, opening points up (+frame Z), slightly canted
    Hj = F @ Matrix.Translation((0, 0, 0.43)) @ Matrix.Rotation(math.pi / 2, 4, 'Y') @ Matrix.Rotation(math.radians(15), 4, 'Z')
    a0, a1 = math.radians(-180 + 38), math.radians(180 - 38)
    n = 30; outer = [(0.085 * math.cos(a0 + (a1 - a0) * i / (n - 1)), 0.085 * math.sin(a0 + (a1 - a0) * i / (n - 1))) for i in range(n)]
    inner = [(0.042 * math.cos(a0 + (a1 - a0) * i / (n - 1)), 0.042 * math.sin(a0 + (a1 - a0) * i / (n - 1))) for i in range(n)]
    _band(K, 'WrenchJaw', outer, inner, T, M['steel'], Hj @ Matrix.Translation((0, 0, -T / 2)))
    _band(K, 'WrenchJawFace', [(x * 1.0, y * 1.0) for x, y in outer[3:-3]], [(x * 1.35, y * 1.35) for x, y in inner[3:-3]], T + 0.004, M['shell'], Hj @ Matrix.Translation((0, 0, -(T + 0.004) / 2)))
    # ring (box) end below the fist
    Hr = F @ Matrix.Translation((0, 0, -0.165)) @ Matrix.Rotation(math.pi / 2, 4, 'Y')
    kprism(K, 'WrenchRing', [('ring', S_circle(0.05, 36), S_circle(0.027, 36))], T, M['steel'], Hr @ Matrix.Translation((0, 0, -T / 2)))
    kprism(K, 'WrenchRingTeeth', [('ring', S_circle(0.03, 24, math.pi / 24), [(0.022 * math.cos(math.pi / 12 * i), 0.022 * math.sin(math.pi / 12 * i)) for i in range(24)])], T * 0.9, M['graph'], Hr @ Matrix.Translation((0, 0, -T * 0.45)))

def S_circle(r, n, a0=0.0): return [(r * math.cos(a0 + TAU * i / n), r * math.sin(a0 + TAU * i / n)) for i in range(n)]

def _band(K, name, outer, inner, h, mat, F):
    """open band between two polylines (same count) extruded 0..h (for C shapes)."""
    bm = bmesh.new()
    O0 = [bm.verts.new(F @ Vector((u, v, 0))) for u, v in outer]; O1 = [bm.verts.new(F @ Vector((u, v, h))) for u, v in outer]
    I0 = [bm.verts.new(F @ Vector((u, v, 0))) for u, v in inner]; I1 = [bm.verts.new(F @ Vector((u, v, h))) for u, v in inner]
    for i in range(len(outer) - 1):
        j = i + 1
        bm.faces.new((O1[i], O1[j], I1[j], I1[i])); bm.faces.new((O0[j], O0[i], I0[i], I0[j]))
        bm.faces.new((O0[i], O0[j], O1[j], O1[i])); bm.faces.new((I0[j], I0[i], I1[i], I1[j]))
    for a, b, c_, d in ((O0[0], O1[0], I1[0], I0[0]), (O0[-1], I0[-1], I1[-1], O1[-1])): bm.faces.new((a, b, c_, d))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _obj(bm, name, mat, 'Stage', smooth=False)
    md = ob.modifiers.new('Bevel', 'BEVEL'); md.width = 0.003; md.segments = 1; md.limit_method = 'ANGLE'; md.angle_limit = math.radians(40); md.use_clamp_overlap = True
    return K.add(ob)

def tool_drive_yoke(K, M, F):
    """Mine Driver: the truck's quick-release drive yoke (steering wheel), carried by its rim, hanging beside the leg.
       Rim passes through the fist; wheel plane = frame ZY (face toward the front); hub with cyan display + accent spokes."""
    R = 0.17
    # wheel centre: outward from the body (frame -Y = -npalm side... use the side away from the hip) and a little down
    Zf = Matrix.Rotation(math.pi / 2, 4, 'Y')                         # torus local XY -> frame ZY plane
    C0 = F @ Matrix.Translation((0, -R, 0)) @ Zf                      # rim passes through the grip centre (local point (0, R) -> frame Y=0)
    ktorus(K, 'YokeRim', R, RH, M['rubber'], C0, nu=64, nv=12)
    ktorus(K, 'YokeRimMark', R, RH + 0.003, M['paint'], C0, a0=math.radians(-100), a1=math.radians(-80), nu=6, nv=12)   # 12 o'clock marker (opposite the hand)
    for a in (0.0, math.pi, -math.pi / 2):      # T spokes: left, right, toward the marker (the hand side at +90 deg stays clear)
        kbox(K, 'YokeSpoke', (R * 0.92, 0.034, 0.014), (R * 0.46, 0, 0), M['graph'], C0 @ Matrix.Rotation(a, 4, 'Z'), bevel=0.004)
    kcyl(K, 'YokeHub', (0, 0, -0.025), (0, 0, 0.02), 0.052, 0.046, M['shell'], C0, n=28, bevel=0.003)
    kcyl(K, 'YokeHubRing', (0, 0, 0.018), (0, 0, 0.026), 0.04, 0.038, M['paint'], C0, n=28)
    kcyl(K, 'YokeDisplay', (0, 0, 0.024), (0, 0, 0.029), 0.028, 0.028, M['glow'], C0, n=24)
    kcyl(K, 'YokeShaft', (0, 0, -0.07), (0, 0, -0.02), 0.022, 0.026, M['steel'], C0, n=20, bevel=0.002)

def tool_drive_controller(K, M, F):
    """Mine Driver: compact handheld drive controller (remote rig for the mine truck). Held by its right grip; the body runs
       outward (frame -Y) to a twin grip. Front face (frame +X = finger side) carries a cyan screen; accent bumper + buttons."""
    W, Hh, T = 0.25, 0.10, 0.05                     # width (Y), height (Z), thickness (X)
    yc, zc = -W / 2 + 0.03, 0.085
    grip_sleeve(K, M, F, -0.075, 0.035)
    kcyl(K, 'CtrlGrip2', (0, yc * 2 + 0.0, -0.075), (0, yc * 2, 0.035), RH, RH, M['rubber'], F, n=20)
    kcyl(K, 'CtrlGrip2Cap', (0, yc * 2, -0.085), (0, yc * 2, -0.07), RH + 0.004, RH + 0.003, M['graph'], F, n=20, bevel=0.002)
    kbox(K, 'CtrlBody', (T, W + 0.035, Hh), (0, yc, zc), M['graph'], F, bevel=0.014, segs=3)
    kbox(K, 'CtrlFace', (0.008, W - 0.01, Hh - 0.022), (T / 2 + 0.001, yc, zc), M['shell'], F, bevel=0.004, segs=2)
    kbox(K, 'CtrlScreen', (0.006, 0.11, 0.05), (T / 2 + 0.005, yc, zc + 0.006), M['screen'], F, bevel=0.0, segs=1)
    kbox(K, 'CtrlBumper', (T + 0.008, W + 0.02, 0.016), (0, yc, zc + Hh / 2 + 0.002), M['paint'], F, bevel=0.005, segs=2)
    for yy in (yc + 0.085, yc - 0.085):
        kcyl(K, 'CtrlButton', (T / 2, yy, zc - 0.012), (T / 2 + 0.012, yy, zc - 0.012), 0.011, 0.01, M['paint'], F, n=14)
        kcyl(K, 'CtrlStick', (T / 2, yy, zc + 0.022), (T / 2 + 0.016, yy, zc + 0.022), 0.008, 0.012, M['rubber'], F, n=12)
    kcyl(K, 'CtrlAntenna', (0, yc - 0.09, zc + Hh / 2), (0, yc - 0.09, zc + Hh / 2 + 0.07), 0.005, 0.0035, M['graph'], F, n=8)
    S.ellip(K, 'CtrlAntennaTip', tuple(F @ Vector((0, yc - 0.09, zc + Hh / 2 + 0.074))), (0.007, 0.007, 0.007), M['aglow'], sub=1)

def tool_cargo_tablet(K, M, F):
    """Cargo Manager: rugged cargo tablet held by its armoured side grip, screen facing out (frame +X), cyan manifest UI with
       accent header bar; a bumper frame in white with graphite corners."""
    grip_sleeve(K, M, F, -0.085, 0.085, mat=M['graph'])
    Wt, Ht, Dt = 0.25, 0.18, 0.022
    # tablet body extends from the grip toward the body midline (frame +Y = npalm side) so the screen sits in front of the hips
    yc = RH + 0.012 + Wt / 2
    kbox(K, 'TabletBody', (Dt, Wt, Ht), (0.0, yc, 0.0), M['shell'], F, bevel=0.008, segs=2)
    kbox(K, 'TabletBezel', (0.006, Wt - 0.02, Ht - 0.02), (Dt / 2 + 0.001, yc, 0.0), M['graph'], F, bevel=0.002, segs=1)
    kbox(K, 'TabletScreen', (0.003, Wt - 0.04, Ht - 0.045), (Dt / 2 + 0.004, yc, -0.008), M['screen'], F, bevel=0.0, segs=1)
    kbox(K, 'TabletHeader', (0.004, Wt - 0.04, 0.016), (Dt / 2 + 0.005, yc, Ht / 2 - 0.022), M['aglow'], F, bevel=0.0, segs=1)
    for i in range(4):     # manifest rows (darker bars on the screen)
        kbox(K, 'TabletRow', (0.004, (Wt - 0.07) * (0.9 if i % 2 else 0.65), 0.009), (Dt / 2 + 0.0055, yc - 0.012 + (0.01 if i % 2 else -0.02), 0.035 - i * 0.026),
             M['graph'], F, bevel=0.0, segs=1)
    for sy in (-1, 1):
        for sz in (-1, 1):
            kbox(K, 'TabletCorner', (Dt + 0.008, 0.035, 0.035), (0.0, yc + sy * (Wt / 2 - 0.012), sz * (Ht / 2 - 0.012)), M['graph'], F, bevel=0.006, segs=2)
    # side grip arm joining the handle to the tablet edge
    kbox(K, 'TabletGripArm', (0.02, RH + 0.02, 0.05), (0.0, (RH + 0.02) / 2 + 0.004, 0.07), M['graph'], F, bevel=0.004)
    kbox(K, 'TabletGripArm', (0.02, RH + 0.02, 0.05), (0.0, (RH + 0.02) / 2 + 0.004, -0.07), M['graph'], F, bevel=0.004)

TOOLS = {'rock_pick': tool_rock_pick, 'drive_controller': tool_drive_controller, 'big_wrench': tool_big_wrench, 'drive_yoke': tool_drive_yoke, 'cargo_tablet': tool_cargo_tablet}

# ---------------------------------------------------------------- tier-2 tools (pass 2, art/crew/roles): same grip frame convention
def tool_flight_yoke(K, M, F):
    """Captain: detachable ship flight yoke carried by its right horn. Horn = the grip (frame Z); a crossbar runs outward
       (frame -Y, away from the hip) to the left horn; centre hub with cyan flight display + accent trim; short column stub."""
    grip_sleeve(K, M, F, -0.06, 0.07)
    Wy = 0.26
    kcyl(K, 'YokeHornTip', (0, 0, 0.07), (0, 0, 0.1), RH + 0.006, RH + 0.002, M['paint'], F, n=16, bevel=0.002)
    kcyl(K, 'YokeHorn2', (0, -Wy, -0.07), (0, -Wy, 0.07), RH, RH, M['rubber'], F, n=16)
    kcyl(K, 'YokeHorn2Tip', (0, -Wy, 0.07), (0, -Wy, 0.1), RH + 0.006, RH + 0.002, M['paint'], F, n=16, bevel=0.002)
    kbox(K, 'YokeBar', (0.034, Wy + 0.05, 0.04), (0, -Wy / 2, -0.085), M['shell'], F, bevel=0.012, segs=2)
    kbox(K, 'YokeBarStripe', (0.037, Wy - 0.06, 0.012), (0, -Wy / 2, -0.07), M['paint'], F, bevel=0.002, segs=1)
    kbox(K, 'YokeHub', (0.05, 0.11, 0.075), (0.004, -Wy / 2, -0.07), M['graph'], F, bevel=0.012, segs=2)
    kbox(K, 'YokeDisplay', (0.006, 0.075, 0.035), (0.031, -Wy / 2, -0.062), M['screen'], F, bevel=0.0, segs=1)
    kcyl(K, 'YokeColumn', (-0.02, -Wy / 2, -0.07), (-0.11, -Wy / 2, -0.07), 0.022, 0.02, M['steel'], F, n=16, bevel=0.002)
    for yy in (0.0, -Wy):
        kcyl(K, 'YokeButton', (0.012, yy, 0.05), (0.03, yy, 0.05), 0.007, 0.006, M['aglow'], F, n=10)

def tool_nav_scope(K, M, F):
    """Co-Captain: handheld nav scope (star sighting / range scope) held mid-tube, objective up the handle axis (frame +Z):
       white tube, graphite grip section, accent focus rings, cyan objective lens, small eyepiece below the fist."""
    grip_sleeve(K, M, F, -0.06, 0.06, mat=M['graph'])
    kcyl(K, 'ScopeTube', (0, 0, 0.06), (0, 0, 0.27), RH + 0.006, RH + 0.012, M['shell'], F, n=24, bevel=0.002)
    kcyl(K, 'ScopeObjective', (0, 0, 0.27), (0, 0, 0.32), RH + 0.02, RH + 0.024, M['graph'], F, n=24, bevel=0.003)
    kcyl(K, 'ScopeLens', (0, 0, 0.318), (0, 0, 0.324), RH + 0.017, RH + 0.017, M['screen'], F, n=24)
    for z in (0.11, 0.2):
        kcyl(K, 'ScopeRing', (0, 0, z), (0, 0, z + 0.022), RH + 0.014, RH + 0.016, M['paint'], F, n=24, bevel=0.002)
    kcyl(K, 'ScopeEyepiece', (0, 0, -0.06), (0, 0, -0.13), RH + 0.002, RH + 0.008, M['graph'], F, n=20, bevel=0.002)
    kcyl(K, 'ScopeEyecup', (0, 0, -0.13), (0, 0, -0.15), RH + 0.012, RH + 0.012, M['rubber'], F, n=20)
    kbox(K, 'ScopeRangefinder', (0.03, 0.03, 0.08), (RH + 0.016, 0, 0.15), M['graph'], F, bevel=0.006)
    kbox(K, 'ScopeRangeLight', (0.004, 0.012, 0.012), (RH + 0.032, 0, 0.175), M['aglow'], F, bevel=0.0, segs=1)

def tool_power_driver(K, M, F):
    """Engineer (ship builder): pistol-grip power driver. Handle = grip (frame Z), motor body on top running forward (frame +X),
       steel chuck + bit, battery pack under the fist; white body, accent side panel, cyan charge light."""
    grip_sleeve(K, M, F, -0.07, 0.06)
    kbox(K, 'DriverBody', (0.2, 0.06, 0.075), (0.04, 0, 0.1), M['shell'], F, bevel=0.02, segs=3)
    kbox(K, 'DriverPanel', (0.12, 0.064, 0.034), (0.03, 0, 0.1), M['paint'], F, bevel=0.006, segs=1)
    kbox(K, 'DriverVent', (0.04, 0.066, 0.05), (-0.04, 0, 0.1), M['graph'], F, bevel=0.006, segs=1)
    kcyl(K, 'DriverChuck', (0.14, 0, 0.1), (0.2, 0, 0.1), 0.026, 0.02, M['graph'], F, n=20, bevel=0.003)
    kcyl(K, 'DriverBit', (0.2, 0, 0.1), (0.29, 0, 0.1), 0.0055, 0.004, M['steel'], F, n=8)
    kbox(K, 'DriverTrigger', (0.02, 0.018, 0.035), (0.03, 0, 0.045), M['paint'], F, bevel=0.004, segs=1)
    kbox(K, 'DriverBattery', (0.1, 0.07, 0.05), (0.02, 0, -0.1), M['graph'], F, bevel=0.01, segs=2)
    kbox(K, 'DriverChargeLight', (0.05, 0.072, 0.008), (0.02, 0, -0.088), M['glow'], F, bevel=0.0, segs=1)

def tool_seed_case(K, M, F):
    """Botanist: seedling sample pod carried by a vertical handle; the pod sits on top of the fist (frame +Z): white base and cap,
       three graphite cage ribs around a glowing accent-green sprout, accent band on the base."""
    grip_sleeve(K, M, F, -0.07, 0.05)
    z0 = 0.06; Rp = 0.07; Hp = 0.15
    kcyl(K, 'PodBase', (0, 0, z0), (0, 0, z0 + 0.04), Rp, Rp, M['shell'], F, n=28, bevel=0.006)
    kcyl(K, 'PodBand', (0, 0, z0 + 0.012), (0, 0, z0 + 0.028), Rp + 0.003, Rp + 0.003, M['paint'], F, n=28)
    kcyl(K, 'PodCap', (0, 0, z0 + 0.04 + Hp), (0, 0, z0 + 0.065 + Hp), Rp, Rp * 0.8, M['shell'], F, n=28, bevel=0.006)
    for i in range(3):
        a = TAU * i / 3 + 0.5
        kcyl(K, 'PodRib', (Rp * 0.92 * math.cos(a), Rp * 0.92 * math.sin(a), z0 + 0.04), (Rp * 0.92 * math.cos(a), Rp * 0.92 * math.sin(a), z0 + 0.04 + Hp),
             0.007, 0.007, M['graph'], F, n=8)
    kcyl(K, 'PodSoil', (0, 0, z0 + 0.04), (0, 0, z0 + 0.06), Rp * 0.85, Rp * 0.85, M['rubber'], F, n=24)
    kcyl(K, 'PodStem', (0, 0, z0 + 0.06), (0, 0, z0 + 0.15), 0.006, 0.004, M['aglow'], F, n=8)
    for sgn in (-1, 1):
        S.ellip(K, 'PodLeaf', tuple(F @ Vector((sgn * 0.03, 0, z0 + 0.13 + 0.02 * (sgn > 0)))), (0.03, 0.012, 0.012), M['aglow'], sub=2)
    kcyl(K, 'PodFoot', (0, 0, -0.07), (0, 0, -0.09), RH + 0.006, RH + 0.01, M['graph'], F, n=16)

def tool_weld_torch(K, M, F):
    """Welder: MIG-style weld torch. Grip = frame Z; a swan-neck runs up and bends forward (frame +X) to a steel nozzle with a
       small glowing tip; graphite hose drops from the grip butt; accent trigger + neck collar."""
    grip_sleeve(K, M, F, -0.07, 0.07)
    kcyl(K, 'TorchCollar', (0, 0, 0.07), (0, 0, 0.1), RH + 0.007, RH + 0.004, M['paint'], F, n=18, bevel=0.002)
    pts = [F @ Vector(p) for p in ((0, 0, 0.1), (0.01, 0, 0.17), (0.05, 0, 0.22), (0.11, 0, 0.24))]
    S.hose(K, 'TorchNeck', pts, 0.011, M['graph'], n=10)
    kcyl(K, 'TorchNozzle', (0.105, 0, 0.24), (0.17, 0, 0.235), 0.016, 0.012, M['steel'], F, n=16, bevel=0.002)
    S.ellip(K, 'TorchTip', tuple(F @ Vector((0.176, 0, 0.234))), (0.008, 0.008, 0.008), M['glow'], sub=1)
    kbox(K, 'TorchTrigger', (0.018, 0.016, 0.04), (RH + 0.006, 0, 0.03), M['paint'], F, bevel=0.004, segs=1)
    hs = [F @ Vector(p) for p in ((0, 0, -0.07), (0.0, 0, -0.16), (-0.03, 0.02, -0.26), (-0.08, 0.05, -0.34))]
    S.hose(K, 'TorchHose', hs, 0.012, M['rubber'], n=10)

def tool_caliper(K, M, F):
    """Machinist: oversized vernier caliper. Flat steel beam up the grip axis (frame Z); fixed jaw at the top and sliding jaw
       (accent slider + cyan readout) both point forward (frame +X), so the tool reads as an 'F' in silhouette."""
    grip_sleeve(K, M, F, -0.07, 0.06, mat=M['graph'])
    T = 0.008
    kbox(K, 'CaliperBeam', (0.03, T, 0.42), (0.0, 0, 0.17), M['steel'], F, bevel=0.002, segs=1)
    kbox(K, 'CaliperScale', (0.012, T + 0.002, 0.26), (0.006, 0, 0.22), M['graph'], F, bevel=0.0, segs=1)
    kbox(K, 'CaliperJawFixed', (0.13, T, 0.03), (0.065, 0, 0.365), M['steel'], F, bevel=0.003, segs=1)
    kbox(K, 'CaliperSlider', (0.06, T + 0.014, 0.07), (0.01, 0, 0.21), M['paint'], F, bevel=0.006, segs=2)
    kbox(K, 'CaliperReadout', (0.03, T + 0.016, 0.022), (0.012, 0, 0.225), M['screen'], F, bevel=0.0, segs=1)
    kbox(K, 'CaliperJawSlide', (0.11, T, 0.026), (0.07, 0, 0.18), M['steel'], F, bevel=0.003, segs=1)
    kbox(K, 'CaliperEnd', (0.034, T + 0.006, 0.02), (0.0, 0, -0.075), M['shell'], F, bevel=0.004, segs=1)

TOOLS.update({'flight_yoke': tool_flight_yoke, 'nav_scope': tool_nav_scope, 'power_driver': tool_power_driver,
              'seed_case': tool_seed_case, 'weld_torch': tool_weld_torch, 'caliper': tool_caliper})

# ---------------------------------------------------------------- badges + extras
def _surface_hit(origin, direction, names=None):
    dg = bpy.context.evaluated_depsgraph_get()
    ok, loc, nrm, _, ob, _ = bpy.context.scene.ray_cast(dg, Vector(origin), Vector(direction).normalized())
    return (loc, nrm, ob) if ok else (None, None, None)

def badge(K, M, key, center, normal, up, R=0.04, name='Badge'):
    n = Vector(normal).normalized(); u = Vector(up); u = (u - n * u.dot(n)).normalized(); x = u.cross(n)
    F = _frame_mat(Vector(center), x, u, n)
    kcyl(K, name + 'Disc', (0, 0, -0.004), (0, 0, 0.004), R, R * 0.97, M['graph'], F, n=36, bevel=0.0015)
    kprism(K, name + 'Ring', [('ring', S_circle(R * 1.0, 40), S_circle(R * 0.86, 40))], 0.0065, M['paint'], F @ Matrix.Translation((0, 0, 0.0)))
    sym = [(p[0],) + tuple([(u_ * R * 0.74, v_ * R * 0.74) for u_, v_ in loop] for loop in p[1:]) for p in RT.BADGES[key]()]
    kprism(K, name + 'Symbol', sym, 0.0075, M['shell'], F @ Matrix.Translation((0, 0, 0.0)), bevel=0.0008)

SOLID_ACCENT = ('Pauldron', 'Backpack', 'BackpackTank', 'BackpackFin') + (('ChestPlate', 'BicepPlate') if STRONG else ())
ACCENT_TO_SHELL = ('PauldronLame', 'PauldronStripe', 'BackpackTankBand') + (('ChestAccent',) if STRONG else ())

def helmet_stripes(K, M, root):
    """twin role-colour stripes over the helmet crown, brow-top to the back of the neck (read from behind and above)."""
    hp = next(o for o in root.children if o.name.startswith('HelmetPivot')); Hm = hp.matrix_basis
    for sx in (-1, 1):
        pts = []
        for i in range(15):
            a = math.radians(62 + (208 - 62) * i / 14)
            d = Vector((sx * 0.30, -math.cos(a), math.sin(a))).normalized()
            pts.append(Hm @ (S._hsurf(d) * 1.012))
        S.hose(K, 'HelmetStripe', pts, 0.0105, M['paint'], n=10)

def helmet_badges(K, M, key, root):
    hp = next(o for o in root.children if o.name.startswith('HelmetPivot'))
    Hm = hp.matrix_basis
    for s in (-1, 1):
        th, ph = math.radians(s * 82), math.radians(40)
        d = Vector((math.sin(th) * math.cos(ph), -math.cos(th) * math.cos(ph), math.sin(ph)))
        tgt = Hm @ (S._hsurf(d))
        org = Hm @ (S._hsurf(d) * 2.2)
        loc, nrm, ob = _surface_hit(org, tgt - org)
        if loc is None: loc, nrm = tgt, (tgt - Hm.translation)
        badge(K, M, key, loc + Vector(nrm) * 0.003, nrm, (0, 0, 1), R=0.046, name='HelmetBadge')

def extra_accent_gloves(K, M, root, P):
    for ob in root.children_recursive:
        if ob.type == 'MESH' and ob.name.split('.')[0] in ('GloveBackPlate', 'GloveKnucklePlate', 'GloveFingerCap', 'GloveThumbCap'):
            ob.data.materials[0] = M['paint']

def extra_headset(K, M, root, P):
    """comms headset: accent ear-cup ring over the right ear pod + boom mic curving forward to the chin guard."""
    hp = next(o for o in root.children if o.name.startswith('HelmetPivot')); Hm = hp.matrix_basis; hs = S.HS
    c = Hm @ (S._hsurf(Vector((-1, 0, -0.07)).normalized()))
    n = (Hm.to_3x3() @ Vector((-1, 0, 0))).normalized()
    pod = c + n * 0.066 * hs
    F = _frame_mat(pod, Vector((0, 1, 0)), Vector((0, 0, 1)), n)
    kcyl(K, 'HeadsetCup', (0, 0, -0.012), (0, 0, 0.012), 0.05 * hs + 0.008, 0.05 * hs + 0.006, M['paint'], F, n=28, bevel=0.002)
    kcyl(K, 'HeadsetCap', (0, 0, 0.012), (0, 0, 0.018), 0.03, 0.026, M['graph'], F, n=24)
    tip = Hm @ (S._hsurf(Vector((-0.32, -1, -0.62)).normalized()) * 1.17)
    mid = pod + n * 0.012 + Vector((0, -0.07, -0.05))
    S.hose(K, 'HeadsetBoom', [pod + n * 0.015, mid, tip + Vector((-0.01, 0.0, 0.0))], 0.0055, M['graph'], n=8)
    S.ellip(K, 'HeadsetMic', tuple(tip), (0.014, 0.012, 0.012), M['paint'], sub=2)

def extra_shoulder_radio(K, M, root, P):
    """handheld radio clipped to the LEFT shoulder harness with a tall whip antenna (reads in silhouette)."""
    hit, nrm, _ = _surface_hit((0.13, -0.6, 1.36), (0, 1, 0))
    if hit is None: hit, nrm = Vector((0.13, -0.17, 1.36)), Vector((0, -1, 0))
    c = hit + Vector(nrm) * 0.03
    F = _frame_mat(c, Vector((1, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)))       # x, y = out (front), z up (det -1 -> normals recalculated)
    kbox(K, 'RadioBody', (0.06, 0.034, 0.105), (0, 0, 0), M['graph'], F, bevel=0.007)
    kbox(K, 'RadioFace', (0.046, 0.006, 0.05), (0, 0.018, 0.012), M['shell'], F, bevel=0.002, segs=1)
    kbox(K, 'RadioScreen', (0.032, 0.004, 0.016), (0, 0.022, 0.022), M['screen'], F, bevel=0.0, segs=1)
    kbox(K, 'RadioBand', (0.064, 0.038, 0.014), (0, 0, -0.03), M['paint'], F, bevel=0.002, segs=1)
    kcyl(K, 'RadioKnob', (0.018, 0, 0.052), (0.018, 0, 0.066), 0.008, 0.008, M['paint'], F, n=12)
    kcyl(K, 'RadioAntennaBase', (-0.016, 0, 0.05), (-0.016, 0, 0.075), 0.008, 0.0065, M['graph'], F, n=12)
    kcyl(K, 'RadioAntenna', (-0.016, 0, 0.075), (-0.016, 0.0, 0.30), 0.0035, 0.0025, M['graph'], F, n=8)
    S.ellip(K, 'RadioAntennaTip', tuple(F @ Vector((-0.016, 0.0, 0.305))), (0.007, 0.007, 0.007), M['aglow'], sub=1)
    kbox(K, 'RadioClip', (0.03, 0.03, 0.05), (0, -0.026, 0.0), M['graph'], F, bevel=0.003, segs=1)

def extra_tool_belt(K, M, root, P):
    """two utility pouches on the hips (graphite, white flap, accent tab)."""
    for sx in (-1, 1):
        hit, nrm, _ = _surface_hit((sx * 0.45, 0.06, 0.94), (-sx, 0, 0))
        if hit is None: continue
        c = hit + Vector(nrm) * 0.03
        F = _frame_mat(c, Vector((0, -sx, 0)), Vector((sx, 0, 0)), Vector((0, 0, 1)))     # x along the hip, y out, z up
        kbox(K, 'Pouch', (0.1, 0.05, 0.11), (0, 0, 0), M['graph'], F, bevel=0.01)
        kbox(K, 'PouchFlap', (0.104, 0.056, 0.035), (0, 0.003, 0.04), M['shell'], F, bevel=0.006)
        kbox(K, 'PouchTab', (0.02, 0.06, 0.03), (0, 0.004, 0.025), M['paint'], F, bevel=0.003, segs=1)

EXTRAS = {'headset': extra_headset, 'accent_gloves': extra_accent_gloves, 'shoulder_radio': extra_shoulder_radio, 'tool_belt': extra_tool_belt}

def _write_ht(root, parts):
    for ob in parts:
        if ob.type != 'MESH': continue
        me = ob.data; at = me.attributes.get('ht') or me.attributes.new('ht', 'FLOAT', 'POINT')
        at.data.foreach_set('value', [(ob.matrix_basis @ v.co).z for v in me.vertices])

# ---------------------------------------------------------------- public
def role_member(key, loc=(0, 0, 0), rot_z=0.0, variant='A', name=None, tool=True):
    R = RT.ROLES[key]
    pname = 'hold_' + key
    st = S.POSES['stand']
    S.POSES[pname] = dict(legs=dict(st['legs']), arms={1: st['arms'][1], -1: R['arm_r']}, lean=0.0, yaw=R.get('yaw', 0.0), hp=0.0)
    CUR.clear(); CUR.update(key=key, grip=tool and R['tool'] in TOOLS, roll=R.get('roll', 0.0)); GRIP.clear()
    root = S.crew_member((0, 0, 0), 0.0, variant, pname, name=name or ('Crew_' + key))
    M = kit_mats(key)
    # accent pauldron lames: the biggest accent read at phone size
    for ob in root.children_recursive:
        if ob.type != 'MESH': continue
        nm = ob.name.split('.')[0]
        if nm in SOLID_ACCENT: ob.data.materials[0] = M['paint']           # solid role colour: shoulder plates + backpack shell
        elif nm in ACCENT_TO_SHELL: ob.data.materials[0] = M['shell']      # trim on those plates flips to white so they still read as panels
    bpy.context.view_layer.update()
    K = Kit(root)
    helmet_badges(K, M, R['badge'], root)
    helmet_stripes(K, M, root)
    for ex in R['extras']:
        if ex in EXTRAS: EXTRAS[ex](K, M, root, R)
    if CUR['grip'] and GRIP:
        TOOLS[R['tool']](K, M, grip_frame())
    _write_ht(root, K.parts)
    CUR.clear()
    root.location = loc; root.rotation_euler = (0, 0, rot_z)
    return root
