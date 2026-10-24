"""Receiving astronaut (Refinery cargo hand-off) -> raw glTF (GLB), pure Python + numpy.
Planet Stack, Art & Animation. Built on the Mine operator rig and suit (art/3d/props/mine_operator, commit 9209246):
same Op_* joints (minus Op_Chair), same geometry helpers, IK solver and GLB writer; the deck and chair are removed.
usage: python3 build_receiver.py OUT_RAW.glb   then gltfpack -cc -kn -ke -ac
glTF coords: +Y up, origin = Receive_Point on the ground, faces +Z while guiding. 2 primitives on one skin -> 2 draws."""
import sys, json, struct, math
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/rx/raw.glb'
FPS = 30
DH = 0.0                       # ground (the operator rig stood on a 2.2 m deck; the receiver stands on the regolith)
rng = np.random.default_rng(23)

def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return np.array([x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c])
WHITE, PALE, STEEL_L, STEEL, GRAPH2, GRAPH = '#e8edf5', '#c9d3e6', '#8794ad', '#5b667e', '#3a4258', '#2a3245'
AMBER, GOLD, ORANGE, SCREEN_INK = '#ffb020', '#c99a3a', '#e8701a', '#10202c'

# ------------------------------------------------------------------ skeleton (rest = identity rotations)
JOINTS = []          # (name, parent, local_rest_translation)
def J(name, parent, t): JOINTS.append((name, parent, np.array(t, float)))
J('Op_Root', None, (0, 0, 0))
J('Op_Body', 'Op_Root', (0, DH, 0))
J('Op_Pelvis', 'Op_Body', (0, 0.93, 0))
J('Op_Spine', 'Op_Pelvis', (0, 0.12, 0))
J('Op_Chest', 'Op_Spine', (0, 0.20, 0))
J('Op_Head', 'Op_Chest', (0, 0.27, 0))
for s, sx in (('L', 1), ('R', -1)):
    J('Op_UpperArm_' + s, 'Op_Chest', (sx * 0.21, 0.14, 0))
    J('Op_Forearm_' + s, 'Op_UpperArm_' + s, (0, -0.28, 0))
    J('Op_Hand_' + s, 'Op_Forearm_' + s, (0, -0.26, 0))
for s, sx in (('L', 1), ('R', -1)):
    J('Op_Thigh_' + s, 'Op_Pelvis', (sx * 0.11, -0.05, 0))
    J('Op_Shin_' + s, 'Op_Thigh_' + s, (0, -0.42, 0))
    J('Op_Foot_' + s, 'Op_Shin_' + s, (0, -0.38, 0))
JI = {n: i for i, (n, _, _) in enumerate(JOINTS)}
REST_W = {}
for n, p, t in JOINTS: REST_W[n] = t + (REST_W[p] if p else 0)
L_TH, L_SH, L_UA, L_FA = 0.42, 0.38, 0.28, 0.26

# ------------------------------------------------------------------ mesh building
class Mesh:
    def __init__(s): s.P, s.N, s.C, s.J, s.I = [], [], [], [], []
    def add(s, P, N, F, col, joint):
        b = len(s.P); s.P += list(P); s.N += list(N); s.C += list(col); s.J += [JI[joint]] * len(P)
        s.I += [b + i for f in F for i in f]
    @property
    def tris(s): return len(s.I) // 3
PAINT, GLOW = Mesh(), Mesh()

def shade(P, base, ao=0.22, noise=0.04, grime=0.0):
    """vertex colours: base gradient (part darker at its base), ground contact AO below 0.35 m, small noise, grime."""
    P = np.asarray(P); y = P[:, 1]; lo, hi = y.min(), y.max(); t = (y - lo) / max(hi - lo, 1e-6)
    f = 1 - ao * (1 - t)
    f *= np.where(y < 0.35, 0.82 + 0.18 * np.clip(y / 0.35, 0, 1), 1.0)
    f *= 1 + noise * rng.uniform(-1, 1, len(P))
    if grime: f *= 1 - grime * np.clip(rng.normal(0.4, 0.35, len(P)), 0, 1)
    c = np.outer(f, lin(base)) if isinstance(base, str) else np.outer(f, base)
    return np.clip(c, 0, 1)

def faces_to_mesh(polys, smooth_groups=None):
    """polys: list of vertex arrays (convex polygons, outward CCW). flat normals, fan triangulation."""
    P, N, F = [], [], []
    for poly in polys:
        poly = np.asarray(poly, float); n = np.cross(poly[1] - poly[0], poly[2] - poly[0])
        if np.linalg.norm(n) < 1e-12: n = np.cross(poly[2] - poly[0], poly[3] - poly[0]) if len(poly) > 3 else np.array([0, 1, 0.])
        n = n / (np.linalg.norm(n) + 1e-12); b = len(P)
        for v in poly: P.append(v); N.append(n)
        for k in range(1, len(poly) - 1): F.append((b, b + k, b + k + 1))
    return np.array(P), np.array(N), F

def orient(polys, centre):
    out = []
    for poly in polys:
        poly = np.asarray(poly, float); n = np.cross(poly[1] - poly[0], poly[2] - poly[0]); c = poly.mean(0)
        out.append(poly[::-1] if np.dot(n, c - centre) < 0 else poly)
    return out

def rotm(axis, a):
    axis = np.asarray(axis, float); axis /= np.linalg.norm(axis); x, y, z = axis; c, s = math.cos(a), math.sin(a); C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s], [y * x * C + z * s, c + y * y * C, y * z * C - x * s], [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])

def box(c, size, col, joint, R=None, ch=0.0, glow=False, **kw):
    hx, hy, hz = np.array(size) / 2; R = np.eye(3) if R is None else R; c = np.asarray(c, float)
    if ch <= 0:
        V = lambda sx, sy, sz: (sx * hx, sy * hy, sz * hz)
        polys = []
        for ax in range(3):
            for sg in (-1, 1):
                q = []
                for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    v = [0, 0, 0]; v[ax] = sg; o = [i for i in range(3) if i != ax]; v[o[0]] = a; v[o[1]] = b
                    q.append(V(*v))
                polys.append(q)
    else:
        ch = min(ch, hx * 0.9, hy * 0.9, hz * 0.9); H = (hx, hy, hz)
        def pt(s, ax):   # corner s, pushed fully along axis ax, inset on the others
            return tuple(s[i] * (H[i] if i == ax else H[i] - ch) for i in range(3))
        polys = []
        for ax in range(3):                      # main faces
            for sg in (-1, 1):
                o = [i for i in range(3) if i != ax]; q = []
                for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    s = [0, 0, 0]; s[ax] = sg; s[o[0]] = a; s[o[1]] = b; q.append(pt(s, ax))
                polys.append(q)
        for a1 in range(3):                      # edge bevels
            for a2 in range(a1 + 1, 3):
                a3 = 3 - a1 - a2
                for s1 in (-1, 1):
                    for s2 in (-1, 1):
                        q = []
                        for s3, ax in ((-1, a1), (1, a1), (1, a2), (-1, a2)):
                            s = [0, 0, 0]; s[a1] = s1; s[a2] = s2; s[a3] = s3; q.append(pt(s, ax))
                        polys.append(q)
        for sx in (-1, 1):                       # corner tris
            for sy in (-1, 1):
                for sz in (-1, 1):
                    s = (sx, sy, sz); polys.append([pt(s, 0), pt(s, 1), pt(s, 2)])
    polys = orient(polys, np.zeros(3))
    P, N, F = faces_to_mesh(polys)
    P = P @ R.T + c; N = N @ R.T
    emit(P, N, F, col, joint, glow, **kw)

def emit(P, N, F, col, joint, glow, **kw):
    if glow: GLOW.add(P, N, F, np.ones((len(P), 3)), joint)
    else: PAINT.add(P, N, F, shade(P, col, **kw), joint)

def cyl(p0, p1, r, col, joint, n=8, glow=False, caps=True, r1=None, **kw):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); ax = p1 - p0; L = np.linalg.norm(ax); ax /= L
    t = np.array([1, 0, 0.]) if abs(ax[0]) < 0.9 else np.array([0, 1, 0.]); u = np.cross(ax, t); u /= np.linalg.norm(u); v = np.cross(ax, u)
    r1 = r if r1 is None else r1
    P, N, F = [], [], []
    for i in range(n):
        a = 2 * math.pi * i / n; d = math.cos(a) * u + math.sin(a) * v
        P += [p0 + d * r, p1 + d * r1]; N += [d, d]
    for i in range(n):
        j = (i + 1) % n; F += [(2 * i, 2 * j, 2 * j + 1), (2 * i, 2 * j + 1, 2 * i + 1)]
    if caps:
        for end, rr, sg in ((p0, r, -1), (p1, r1, 1)):
            b = len(P)
            for i in range(n):
                a = 2 * math.pi * i / n; P.append(end + (math.cos(a) * u + math.sin(a) * v) * rr); N.append(ax * sg)
            for k in range(1, n - 1): F.append((b, b + k, b + k + 1) if sg > 0 else (b, b + k + 1, b + k))
    P, N = np.array(P), np.array(N)
    # fix side winding to outward
    F2 = []
    for f in F:
        a, b_, c = P[f[0]], P[f[1]], P[f[2]]; nn = np.cross(b_ - a, c - a)
        F2.append(f if np.dot(nn, N[f[0]] + N[f[1]] + N[f[2]]) >= 0 else (f[0], f[2], f[1]))
    emit(P, N, F2, col, joint, glow, **kw)

def sphere(c, r, col, joint, seg=10, rings=6, scale=(1, 1, 1), R=None, glow=False, cut=None, **kw):
    """UV sphere. cut=(axis_vec, min_dot): keep only the cap facing axis (for visors)."""
    c = np.asarray(c, float); sc = np.array(scale, float); R = np.eye(3) if R is None else R
    P, N, F = [], [], []
    grid = []
    for i in range(rings + 1):
        th = math.pi * i / rings; row = []
        for j in range(seg):
            ph = 2 * math.pi * j / seg; d = np.array([math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph)])
            row.append(len(P)); P.append(d * sc * r); N.append(d / sc / np.linalg.norm(d / sc))
        grid.append(row)
    for i in range(rings):
        for j in range(seg):
            a, b, cc, d = grid[i][j], grid[i][(j + 1) % seg], grid[i + 1][(j + 1) % seg], grid[i + 1][j]
            if i > 0: F.append((a, b, cc))
            if i < rings - 1: F.append((a, cc, d))
    P, N = np.array(P) @ R.T + c, np.array(N) @ R.T
    F2 = []
    for f in F:
        a, b_, cc = P[f[0]], P[f[1]], P[f[2]]; nn = np.cross(b_ - a, cc - a)
        if cut is not None and min(np.dot(N[k], cut[0]) for k in f) < cut[1]: continue
        F2.append(f if np.dot(nn, N[f[0]] + N[f[1]] + N[f[2]]) >= 0 else (f[0], f[2], f[1]))
    emit(P, N, F2, col, joint, glow, **kw)

def quad(c, w, h, R, col, joint='Op_Body'):   # single-sided quad facing local +Z (screen ink)
    q = np.array([[-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2, 0], [-w / 2, h / 2, 0]]) @ R.T + c
    P, N, F = faces_to_mesh([q]); emit(P, N, F, col, joint, False, ao=0.0, noise=0.0)

def strut(p0, p1, w, col, joint, **kw):      # square-section beam between two points
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); d = p1 - p0; L = np.linalg.norm(d); y = d / L
    t = np.array([0, 0, 1.]) if abs(y[2]) < 0.9 else np.array([1, 0, 0.]); x = np.cross(y, t); x /= np.linalg.norm(x); z = np.cross(x, y)
    box((p0 + p1) / 2, (w, L, w), col, joint, R=np.column_stack([x, y, z]), **kw)

# ------------------------------------------------------------------ operator (white/graphite suit, gold visor, cyan accents)
W_ = lambda n: REST_W[n]
pel, sp, chs, hd = W_('Op_Pelvis'), W_('Op_Spine'), W_('Op_Chest'), W_('Op_Head')
box(pel + (0, -0.02, 0), (0.34, 0.17, 0.25), GRAPH2, 'Op_Pelvis', ch=0.04, ao=0.1)                # hips
box(pel + (0, 0.07, 0), (0.36, 0.06, 0.26), GRAPH, 'Op_Pelvis', ao=0.0)                  # belt
box(pel + (0, 0.07, 0.132), (0.08, 0.04, 0.008), None, 'Op_Pelvis', glow=True)
box(sp + (0, 0.1, 0), (0.36, 0.22, 0.24), WHITE, 'Op_Spine', ch=0.05, ao=0.15)                     # abdomen
box(chs + (0, 0.11, 0), (0.46, 0.30, 0.30), WHITE, 'Op_Chest', ch=0.07, ao=0.15, grime=0.12)      # chest shell
box(chs + (0, 0.12, 0.152), (0.2, 0.12, 0.02), GRAPH, 'Op_Chest', ao=0.0)                 # chest unit
box(chs + (0, 0.155, 0.164), (0.15, 0.016, 0.006), None, 'Op_Chest', glow=True)
box(chs + (0, 0.105, 0.164), (0.15, 0.016, 0.006), None, 'Op_Chest', glow=True)
box(chs + (0, 0.19, 0), (0.465, 0.045, 0.305), GRAPH2, 'Op_Chest', ao=0.0)                          # collar band
box(chs + (0, 0.1, -0.26), (0.40, 0.48, 0.2), WHITE, 'Op_Chest', ch=0.05, ao=0.25, grime=0.12)     # life-support pack
box(chs + (0, 0.1, -0.362), (0.26, 0.36, 0.01), GRAPH, 'Op_Chest', ao=0.0)
box(chs + (0, 0.1, -0.369), (0.018, 0.30, 0.006), None, 'Op_Chest', glow=True)
cyl(chs + (0.15, 0.3, -0.3), chs + (0.15, 0.5, -0.3), 0.008, GRAPH, 'Op_Chest', n=4, caps=False)  # antenna
for s, sx in (('L', 1), ('R', -1)):
    sh = W_('Op_UpperArm_' + s); el = W_('Op_Forearm_' + s); wr = W_('Op_Hand_' + s)
    sphere(sh + (sx * 0.02, 0, 0), 0.1, WHITE, 'Op_UpperArm_' + s, seg=7, rings=4, ao=0.05)        # shoulder pad
    box(sh + (sx * 0.06, 0.02, 0), (0.06, 0.012, 0.12), None, 'Op_UpperArm_' + s, glow=True, R=rotm((0, 0, 1), sx * 0.5))
    cyl(sh, el + (0, 0.02, 0), 0.062, WHITE, 'Op_UpperArm_' + s, n=8, caps=False, ao=0.15)
    sphere(el, 0.064, GRAPH2, 'Op_Forearm_' + s, seg=6, rings=3, ao=0.0)
    cyl(el, wr + (0, 0.03, 0), 0.056, WHITE, 'Op_Forearm_' + s, n=8, r1=0.05, caps=False, ao=0.15)
    cyl(wr + (0, 0.09, 0), wr + (0, 0.035, 0), 0.06, GRAPH, 'Op_Forearm_' + s, n=8, caps=False, ao=0.0)       # cuff
    box(wr + (sx * 0.0, 0.07, 0.058), (0.05, 0.035, 0.008), None, 'Op_Forearm_' + s, glow=True)    # wrist display
    box(wr + (0, -0.06, 0.01), (0.07, 0.12, 0.10), GRAPH2, 'Op_Hand_' + s, ch=0.025, ao=0.05)      # glove
    box(wr + (0, -0.05, 0.065), (0.06, 0.05, 0.04), GRAPH2, 'Op_Hand_' + s, ao=0.0, R=rotm((1, 0, 0), 0.4))  # thumb
for s, sx in (('L', 1), ('R', -1)):
    hp = W_('Op_Thigh_' + s); kn = W_('Op_Shin_' + s); an = W_('Op_Foot_' + s)
    cyl(hp + (0, 0.03, 0), kn, 0.088, WHITE, 'Op_Thigh_' + s, n=8, r1=0.078, caps=False, ao=0.15)
    box(kn + (0, 0.0, 0.06), (0.13, 0.13, 0.06), GRAPH2, 'Op_Shin_' + s, ao=0.0)          # knee guard
    box(kn + (0, 0.0, 0.093), (0.07, 0.014, 0.006), None, 'Op_Shin_' + s, glow=True)
    cyl(kn, an + (0, 0.12, 0), 0.075, WHITE, 'Op_Shin_' + s, n=8, r1=0.07, caps=False, ao=0.15)
    box(an + (0, 0.05, 0.035), (0.135, 0.17, 0.25), GRAPH2, 'Op_Foot_' + s, ch=0.03, ao=0.1)        # boot upper
    box(an + (0, -0.05, 0.06), (0.14, 0.06, 0.30), GRAPH, 'Op_Foot_' + s, ao=0.0)          # sole (bottom at ankle -0.08)
HC = hd + (0, 0.12, 0.0)
sphere(HC, 0.19, WHITE, 'Op_Head', seg=10, rings=7, ao=0.12)                                        # helmet
sphere(HC + (0, -0.005, 0.03), 0.178, GOLD, 'Op_Head', seg=12, rings=8, scale=(0.98, 0.8, 1.0), cut=(np.array([0, 0, 1.0]), 0.25), ao=0.0, noise=0.02)   # gold visor (front cap)
box(HC + (0, 0.165, 0.02), (0.06, 0.05, 0.26), GRAPH2, 'Op_Head', ao=0.0)                # crest
for sx in (-1, 1):
    box(HC + (sx * 0.19, 0.0, 0.0), (0.04, 0.09, 0.09), GRAPH, 'Op_Head', ao=0.0)          # ear pods
    box(HC + (sx * 0.212, 0.0, 0.0), (0.006, 0.05, 0.05), None, 'Op_Head', glow=True)
box(hd + (0, -0.005, 0), (0.18, 0.05, 0.18), GRAPH, 'Op_Head', ao=0.0)                   # neck ring
OP_TRIS = PAINT.tris + GLOW.tris
# ------------------------------------------------------------------ pose solver
def yawm(a): return rotm((0, 1, 0), a)
def pitchm(a): return rotm((1, 0, 0), a)
def nrm(v): return v / (np.linalg.norm(v) + 1e-12)
def frame(Y, Z):
    Y = nrm(Y); Z = nrm(Z - np.dot(Z, Y) * Y); X = np.cross(Y, Z); return np.column_stack([X, Y, Z])
STRETCH = []
def ik2(A, C, l1, l2, pole):
    d = C - A; D = np.linalg.norm(d); STRETCH.append(D / (l1 + l2))
    D2 = min(max(D, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-4); u = d / D
    a = (l1 * l1 - l2 * l2 + D2 * D2) / (2 * D2); h = math.sqrt(max(l1 * l1 - a * a, 0))
    pp = nrm(pole - np.dot(pole, u) * u); B = A + a * u + h * pp; Cc = A + u * D2
    return B, Cc

def solve(S):
    """S: pose dict -> world rotation matrices + positions per joint (asset coords)."""
    Wr, Wp = {}, {}
    Wr['Op_Root'] = np.eye(3); Wp['Op_Root'] = np.zeros(3)
    by = yawm(S['yaw']); Wr['Op_Body'] = by; Wp['Op_Body'] = np.array([S['pos'][0], DH, S['pos'][1]])
    Wr['Op_Pelvis'] = by @ yawm(S.get('pel_yaw', 0)) @ rotm((0, 0, 1), S.get('pel_roll', 0)) @ pitchm(S['pel_pitch'])
    Wp['Op_Pelvis'] = Wp['Op_Body'] + by @ np.asarray(S['pel'])
    Wr['Op_Spine'] = Wr['Op_Pelvis'] @ pitchm(S['spine']); Wp['Op_Spine'] = Wp['Op_Pelvis'] + Wr['Op_Pelvis'] @ (0, 0.12, 0)
    Wr['Op_Chest'] = Wr['Op_Spine'] @ yawm(S.get('twist', 0)) @ pitchm(S['chest']); Wp['Op_Chest'] = Wp['Op_Spine'] + Wr['Op_Spine'] @ (0, 0.20, 0)
    Wr['Op_Head'] = Wr['Op_Chest'] @ yawm(S['head_yaw']) @ pitchm(S['head_pitch']); Wp['Op_Head'] = Wp['Op_Chest'] + Wr['Op_Chest'] @ (0, 0.27, 0)
    fwd = by @ (0, 0, 1.); left = by @ (1, 0, 0.)
    for s, sx in (('L', 1), ('R', -1)):
        hip = Wp['Op_Pelvis'] + Wr['Op_Pelvis'] @ (sx * 0.11, -0.05, 0); ank = np.asarray(S['foot_' + s][0], float)
        fy = yawm(S['foot_' + s][1]) @ pitchm(S['foot_' + s][2])
        pole = nrm(fy @ (0, 0, 1.) * 1.0 + left * sx * 0.15 + Wr['Op_Pelvis'] @ (0, 0, 1.) * 0.5)
        kn, an = ik2(hip, ank, L_TH, L_SH, pole)
        Wp['Op_Thigh_' + s], Wp['Op_Shin_' + s], Wp['Op_Foot_' + s] = hip, kn, an
        Wr['Op_Thigh_' + s] = frame(hip - kn, pole); Wr['Op_Shin_' + s] = frame(kn - an, pole); Wr['Op_Foot_' + s] = fy
        sh = Wp['Op_Chest'] + Wr['Op_Chest'] @ (sx * 0.21, 0.14, 0); hand = np.asarray(S['hand_' + s], float)
        cf = Wr['Op_Chest'] @ (0, 0, 1.); cl = Wr['Op_Chest'] @ (1, 0, 0.)
        epole = nrm(-cf * 1.0 + cl * sx * S.get('elbow_out', 0.6) - np.array([0, 1, 0.]) * 0.3)
        el, wr = ik2(sh, hand, L_UA, L_FA, epole)
        Wp['Op_UpperArm_' + s], Wp['Op_Forearm_' + s], Wp['Op_Hand_' + s] = sh, el, wr
        Wr['Op_UpperArm_' + s] = frame(sh - el, -epole); Wr['Op_Forearm_' + s] = frame(el - wr, -epole)
        Wr['Op_Hand_' + s] = Wr['Op_Forearm_' + s] @ pitchm(S.get('wrist', 0.0))
    return Wr, Wp

def mat2q(M):
    t = np.trace(M)
    if t > 0:
        s = math.sqrt(t + 1) * 2; return np.array([(M[2, 1] - M[1, 2]) / s, (M[0, 2] - M[2, 0]) / s, (M[1, 0] - M[0, 1]) / s, 0.25 * s])
    i = int(np.argmax(np.diag(M)))
    if i == 0:
        s = math.sqrt(1 + M[0, 0] - M[1, 1] - M[2, 2]) * 2; return np.array([0.25 * s, (M[0, 1] + M[1, 0]) / s, (M[0, 2] + M[2, 0]) / s, (M[2, 1] - M[1, 2]) / s])
    if i == 1:
        s = math.sqrt(1 + M[1, 1] - M[0, 0] - M[2, 2]) * 2; return np.array([(M[0, 1] + M[1, 0]) / s, 0.25 * s, (M[1, 2] + M[2, 1]) / s, (M[0, 2] - M[2, 0]) / s])
    s = math.sqrt(1 + M[2, 2] - M[0, 0] - M[1, 1]) * 2; return np.array([(M[0, 2] + M[2, 0]) / s, (M[1, 2] + M[2, 1]) / s, 0.25 * s, (M[1, 0] - M[0, 1]) / s])

def to_local(Wr, Wp):
    T, Q = {}, {}
    for n, p, t in JOINTS:
        if p is None: T[n], Q[n] = Wp[n], mat2q(Wr[n]); continue
        Rl = Wr[p].T @ Wr[n]; T[n] = Wr[p].T @ (Wp[n] - Wp[p]); Q[n] = mat2q(Rl)
    return T, Q
def ss(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def ss2(x): x = min(max(x, 0.0), 1.0); return x * x * x * (x * (6 * x - 15) + 10)    # smootherstep
def seg(t, a, b): return ss2((t - a) / (b - a))
def lerp(a, b, u): return np.asarray(a, float) + (np.asarray(b, float) - np.asarray(a, float)) * u
PI = math.pi
def body_pt(pos, yaw, local):          # body-local (x left, y up, z fwd) -> world
    return np.array([pos[0], DH, pos[1]]) + yawm(yaw) @ np.asarray(local, float)
def feet_at(pos, yaw, fwd=0.02, half=0.12):
    return {'L': (body_pt(pos, yaw, (half, 0.08, fwd)), yaw, 0.0), 'R': (body_pt(pos, yaw, (-half, 0.08, fwd)), yaw, 0.0)}
def bez(P, s):
    P = [np.asarray(p, float) for p in P]; u = 1 - s
    return u ** 3 * P[0] + 3 * u * u * s * P[1] + 3 * u * s * s * P[2] + s ** 3 * P[3]
def mix(A, B, u):
    """blend two pose dicts (positions linear, angles linear; feet/hands linear)."""
    O = {}
    for k in A:
        a, b = A[k], B[k]
        if k.startswith('foot_'): O[k] = (lerp(a[0], b[0], u), a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u)
        elif isinstance(a, (int, float)): O[k] = a + (b - a) * u
        else: O[k] = lerp(a, b, u)
    return O
def full(S):
    for k, v in (('twist', 0.0), ('pel_roll', 0.0), ('pel_yaw', 0.0), ('elbow_out', 0.6), ('wrist', 0.0)): S.setdefault(k, v)
    return S
def bake(fn, dur):
    n = int(round(dur * FPS)); ts = np.array([i / FPS for i in range(n + 1)]); ts[-1] = dur
    TT = {j[0]: [] for j in JOINTS}; QQ = {j[0]: [] for j in JOINTS}
    for t in ts:
        Wr, Wp = solve(full(fn(float(t)))); T, Q = to_local(Wr, Wp)
        for k in TT:
            q = Q[k]
            if QQ[k] and np.dot(QQ[k][-1], q) < 0: q = -q
            TT[k].append(T[k]); QQ[k].append(q)
    return ts, {k: np.array(v) for k, v in TT.items()}, {k: np.array(v) for k, v in QQ.items()}
# ------------------------------------------------------------------ write GLB
bin_ = bytearray(); views, accs = [], []
def addbuf(arr, comp, typ, target=None, minmax=False):
    arr = np.ascontiguousarray(arr); data = arr.tobytes()
    while len(bin_) % 4: bin_.append(0)
    off = len(bin_); bin_.extend(data)
    v = {'buffer': 0, 'byteOffset': off, 'byteLength': len(data)}
    if target: v['target'] = target
    views.append(v)
    a = {'bufferView': len(views) - 1, 'componentType': comp, 'count': int(arr.shape[0]), 'type': typ}
    if minmax: a['min'] = arr.min(0).tolist() if arr.ndim > 1 else [float(arr.min())]; a['max'] = arr.max(0).tolist() if arr.ndim > 1 else [float(arr.max())]
    accs.append(a); return len(accs) - 1
def prim(M, mat, colors):
    P = np.array(M.P, np.float32); N = np.array(M.N, np.float32); N /= np.linalg.norm(N, axis=1, keepdims=True)
    att = {'POSITION': addbuf(P, 5126, 'VEC3', 34962, True), 'NORMAL': addbuf(N, 5126, 'VEC3', 34962)}
    if colors: att['COLOR_0'] = addbuf(np.array(M.C, np.float32), 5126, 'VEC3', 34962)
    jj = np.zeros((len(M.P), 4), np.uint8); jj[:, 0] = M.J; ww = np.zeros((len(M.P), 4), np.float32); ww[:, 0] = 1
    att['JOINTS_0'] = addbuf(jj, 5121, 'VEC4', 34962); att['WEIGHTS_0'] = addbuf(ww, 5126, 'VEC4', 34962)
    return {'attributes': att, 'indices': addbuf(np.array(M.I, np.uint16 if len(M.P) < 65536 else np.uint32), 5123 if len(M.P) < 65536 else 5125, 'SCALAR', 34963), 'material': mat}
# ================================================================== receiver animation (new)
def relaxed_hands(pos, yaw, t=0.0, swing=0.0):
    return (body_pt(pos, yaw, (0.24, 0.87, 0.06 + swing)), body_pt(pos, yaw, (-0.24, 0.87, 0.06 - swing)))
HOME = np.array([-3.0, -1.5])        # Home_Point: door / airlock side, behind-left of Receive_Point (asset-local, x/z)
REC = np.array([0.0, 0.0])           # Receive_Point = asset origin; faces +Z while guiding
YAW_OUT = math.atan2(REC[0] - HOME[0], REC[1] - HOME[1])        # heading of the first leg (fwd = (sin yaw, 0, cos yaw))
PEL_H = 0.905

# normalise trap so the accel phase integrates exactly (computed numerically once)
_A = 0.22
def _acc(x): return x * x * (3 - 2 * x)                                        # velocity ramp 0..1
_UU = np.linspace(0, 1, 4001)
def _vel(u): return np.where(_UU < _A, _acc(np.clip(_UU / _A, 0, 1)), np.where(_UU > 1 - _A, _acc(np.clip((1 - _UU) / _A, 0, 1)), 1.0))
_V = _vel(_UU); _S = np.concatenate([[0], np.cumsum((_V[1:] + _V[:-1]) / 2 * np.diff(_UU))]); _S /= _S[-1]
def prog(u): return float(np.interp(min(max(u, 0.0), 1.0), _UU, _S))
def prog_inv(s): return float(np.interp(s, _S, _UU))

def blen(P, n=400):
    pts = [bez(P, i / n) for i in range(n + 1)]; return sum(np.linalg.norm(pts[i + 1] - pts[i]) for i in range(n))
def bez_arc(P):
    """arc-length parametrised bezier: returns f(s in 0..1) -> point, and tangent yaw."""
    n = 600; ss_ = np.linspace(0, 1, n + 1); pts = np.array([bez(P, s) for s in ss_])
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]); d /= d[-1]
    def f(s): t = float(np.interp(s, d, ss_)); return bez(P, t)
    def tan_yaw(s):
        t = float(np.interp(min(max(s, 1e-3), 1 - 1e-3), d, ss_)); q = bez(P, min(t + 1e-3, 1)) - bez(P, max(t - 1e-3, 0)); return math.atan2(q[0], q[1])
    return f, tan_yaw

def unwrap_to(a, ref):
    while a - ref > PI: a -= 2 * PI
    while a - ref < -PI: a += 2 * PI
    return a

class Walk:
    """footstep walk along a bezier. Pelvis follows prog(); feet plant on exact spots and never move while planted.
    nsteps alternate starting with `first`; the last two steps bring the feet side by side at the end."""
    def __init__(s, path, t0, t1, yaw0, yaw1, nsteps, first='L', start_feet=None, end_half=0.12, swing=0.42, lead=0.5):
        s.f, s.ty = bez_arc(path); s.t0, s.t1, s.y0, s.y1 = t0, t1, yaw0, yaw1; s.len = blen(path)
        s.start = start_feet; s.plants = {'L': [], 'R': []}; foot = first
        for k in range(1, nsteps + 1):
            st = min(k / (nsteps - 1), 1.0)
            sx = 1 if foot == 'L' else -1; y = s.yaw(st); p = s.f(st)
            spot = (body_pt(p, y, (sx * end_half, 0.08, 0.0)), y, 0.0)
            # land when the pelvis is `lead` of a step short of the spot (feet reach ahead of the body), final pair lands at the end
            s_land = max(st - lead / (nsteps - 1), 0.02) if k < nsteps - 1 else (0.97 if k == nsteps - 1 else 1.0)
            tb = t0 + (t1 - t0) * prog_inv(s_land); ta = tb - swing
            s.plants[foot].append((ta, tb, spot)); foot = 'R' if foot == 'L' else 'L'
        s.nsteps = nsteps
    def yaw(s, st): return s.y0 + (s.y1 - s.y0) * ss(st)
    def at(s, t):
        u = (t - s.t0) / (s.t1 - s.t0); st = prog(u); pos = s.f(st); yaw = s.yaw(st)
        feet = {}
        for foot in 'LR':
            cur = s.start[foot]
            for ta, tb, tgt in s.plants[foot]:
                if t >= tb: cur = tgt; continue
                if t > ta:
                    raw = (t - ta) / (tb - ta); w = ss2(raw)
                    p = lerp(cur[0], tgt[0], w) + (0, 0.07 * math.sin(PI * raw), 0)
                    cur = (p, cur[1] + (tgt[1] - cur[1]) * w, 0.22 * math.sin(PI * raw) * (1 - raw) - 0.10 * math.sin(PI * raw) * raw)
                break
            feet[foot] = cur
        # gait phase for bob + arm swing: 0 at each landing
        lands = sorted(tb for f_ in 'LR' for (_, tb, _) in s.plants[f_])
        w = seg(t, lands[0] - 0.45, lands[0] - 0.1) * (1 - seg(t, lands[-2], lands[-1]))
        # continuous gait phase: +1 at a right-foot landing (left arm forward), -1 at a left-foot landing, eased between
        ev = sorted((tb, 1.0 if f_ == 'R' else -1.0) for f_ in 'LR' for (_, tb, _) in s.plants[f_])
        T_ = [e[0] for e in ev]; A_ = [e[1] for e in ev]
        if t <= T_[0]: lead_l = A_[0] * ss((t - (T_[0] - 0.5)) / 0.5)
        elif t >= T_[-1]: lead_l = 0.0
        else:
            k = max(i for i in range(len(T_)) if T_[i] <= t); u = ss((t - T_[k]) / (T_[k + 1] - T_[k])); lead_l = A_[k] + (A_[k + 1] - A_[k]) * u
            if k + 1 == len(T_) - 1: lead_l *= 1 - u   # last landing brings the feet together: arms settle
        return pos, yaw, feet, w, lead_l

def stand(pos, yaw, feet=None, half=0.12, **kw):
    S = full(dict(pos=pos, yaw=yaw, pel=(0, PEL_H, 0.0), pel_pitch=0.03, spine=0.03, chest=0.02, head_yaw=0.0, head_pitch=-0.04))
    f = feet or feet_at(pos, yaw, 0.0, half); S['foot_L'], S['foot_R'] = f['L'], f['R']
    S['hand_L'], S['hand_R'] = relaxed_hands(pos, yaw); S['elbow_out'] = 0.6
    S.update(kw); return S

def walking(W, t):
    pos, yaw, feet, w, lead = W.at(t)
    S = stand(pos, yaw, feet)
    S['hand_L'], S['hand_R'] = relaxed_hands(pos, yaw, swing=0.14 * lead * w)    # left arm forward when the right foot leads
    S['pel'] = (0, PEL_H - w * 0.035, 0.0)                                         # slightly flexed knees while walking
    S['pel_yaw'] = -0.08 * lead * w; S['twist'] = 0.12 * lead * w; S['pel_roll'] = 0.0
    S['spine'] = 0.03 + 0.05 * w; S['head_pitch'] = -0.04 - 0.04 * w
    return S

# ---- guide (marshalling "come ahead" wave): arms raised, forearms beckon back toward the helmet. 2.0 s loop, 2 beckons per arm
G_DUR = 2.0
def guide_hands(pos, yaw, t):
    ph = 2 * PI * t / 1.0
    zl = 0.16 + 0.15 * (0.5 - 0.5 * math.cos(ph)); zr = 0.16 + 0.15 * (0.5 - 0.5 * math.cos(ph + 0.6))
    yl = 1.66 + 0.05 * math.sin(ph); yr = 1.66 + 0.05 * math.sin(ph + 0.6)
    return body_pt(pos, yaw, (0.36, yl, zl)), body_pt(pos, yaw, (-0.36, yr, zr))
def pose_guide(t, pos=REC, yaw=0.0):
    sway = 0.02 * math.sin(2 * PI * t / G_DUR)
    S = stand(pos, yaw, half=0.14, pel=(sway, PEL_H, 0.0), pel_roll=-sway * 1.2, spine=0.0, chest=-0.04, head_pitch=0.08,
              head_yaw=0.10 * math.sin(2 * PI * t / G_DUR), elbow_out=1.5, wrist=-0.5)
    S['hand_L'], S['hand_R'] = guide_hands(pos, yaw, t)
    return S

# ---- walk_out: Home_Point -> Receive_Point (turn to face +Z), then raise the arms into the guide pose
PATH_OUT = [HOME, HOME + 1.2 * np.array([math.sin(YAW_OUT), math.cos(YAW_OUT)]), REC + (0, -1.1), REC]
WO_WALK, WO_DUR = 3.4, 4.0
HOME_FEET = feet_at(HOME, YAW_OUT, 0.0, 0.12)
W_OUT = Walk(PATH_OUT, 0.0, WO_WALK, YAW_OUT, 0.0, 10, 'L', HOME_FEET, end_half=0.14)
def pose_walk_out(t):
    if t <= WO_WALK: return walking(W_OUT, t)
    u = seg(t, WO_WALK - 0.05, WO_DUR)
    A_ = walking(W_OUT, WO_WALK); B_ = full(pose_guide(0.0))
    S = mix(A_, B_, u); S['foot_L'], S['foot_R'] = A_['foot_L'], A_['foot_R']
    S['elbow_out'] = A_['elbow_out'] + (B_['elbow_out'] - A_['elbow_out']) * u
    # hands travel up on an arc out to the side (no clipping through the chest)
    mid = math.sin(PI * u)
    S['hand_L'] = S['hand_L'] + np.array([0.12 * mid, 0, 0.0])      # yaw is 0 here: +X = his left
    S['hand_R'] = S['hand_R'] + np.array([-0.12 * mid, 0, 0.0])
    return S

# ---- check_in (2.0 s): lower the arms, raise the left forearm, tap the left wrist pad twice with the right glove, lower to relaxed
CI_DUR = 2.0
PAD_N = None
def pad_world(S):
    """left wrist pad: 0.07 up the forearm from the wrist, 0.058 out along the pad normal. The normal is frozen from the hold pose
    (so the tap target can't flip with the elbow frame); the position follows the real wrist every frame."""
    Wr, Wp = solve(full(dict(S))); fy = nrm(Wp['Op_Forearm_L'] - Wp['Op_Hand_L'])
    return Wp['Op_Hand_L'] + fy * 0.07 + PAD_N * 0.058, PAD_N
def pose_check_in(t):
    global PAD_N
    if PAD_N is None:                               # pad normal from the hold pose (t = 1.0 s, arm fully up)
        PAD_N = np.array([0, 0, 1.0]); S1 = pose_check_in_arms(1.0); Wr, Wp = solve(full(dict(S1))); PAD_N = nrm(Wr['Op_Forearm_L'] @ np.array([0, 0, 1.0]))
    S = pose_check_in_arms(t)
    G = full(pose_guide(G_DUR)); R_ = stand(REC, 0.0, half=0.14); up = seg(t, 0.0, 0.5); down = seg(t, 1.5, 2.0)
    # right glove: to the pad, two taps (0.82 / 1.18 s), back down
    pad, n = pad_world(S)
    hover = pad + n * 0.11 + np.array([-0.06, 0.06, 0.03])
    tap = 0.0
    for tc in (0.82, 1.18): tap = max(tap, math.sin(PI * min(max((t - (tc - 0.12)) / 0.24, 0), 1)))
    tgt = hover - n * 0.065 * tap
    reach = seg(t, 0.15, 0.62) * (1 - seg(t, 1.38, 1.85))
    S['hand_R'] = lerp(lerp(G['hand_R'], R_['hand_R'], seg(t, 0.0, 0.45)), tgt, reach)
    return S
def pose_check_in_arms(t):
    G = full(pose_guide(G_DUR)); R_ = stand(REC, 0.0, half=0.14)
    up = seg(t, 0.0, 0.5); down = seg(t, 1.5, 2.0)
    S = mix(G, R_, seg(t, 0.0, 0.45))
    S['foot_L'], S['foot_R'] = G['foot_L'], G['foot_R']
    # left forearm across the chest, pad facing up/out toward the helmet
    hold_L = body_pt(REC, 0.0, (0.04, 1.30, 0.30))
    S['hand_L'] = lerp(lerp(G['hand_L'], hold_L, up), R_['hand_L'], down)
    S['elbow_out'] = (1.5 * (1 - up) + 0.9 * up) * (1 - down) + 0.6 * down
    S['wrist'] = -0.5 * (1 - seg(t, 0, 0.4))
    look = up * (1 - down); S['head_pitch'] = 0.08 * (1 - seg(t, 0, 0.4)) - 0.04 * seg(t, 0, 0.4) - 0.42 * look; S['chest'] = -0.04 * (1 - seg(t, 0, 0.4)) + 0.02 * seg(t, 0, 0.4) + 0.10 * look
    S['head_yaw'] = 0.12 * look
    S['hand_R'] = lerp(G['hand_R'], R_['hand_R'], seg(t, 0.0, 0.45))
    return S

# ---- walk_back: Receive_Point -> Home_Point, then a 3-step turn on the spot to face out again (== walk_out frame 0)
YAW_BACK = unwrap_to(math.atan2(HOME[0] - REC[0], HOME[1] - REC[1]), 0.0)
PATH_BACK = [REC, REC + 0.6 * np.array([math.sin(YAW_BACK), math.cos(YAW_BACK)]), HOME - 1.1 * np.array([math.sin(YAW_BACK), math.cos(YAW_BACK)]), HOME]
WB_WALK, WB_DUR = 3.4, 4.4
REC_FEET = feet_at(REC, 0.0, 0.0, 0.14)
W_BACK = Walk(PATH_BACK, 0.0, WB_WALK, 0.0, YAW_BACK, 10, 'R', REC_FEET, end_half=0.12)
YAW_END = unwrap_to(YAW_OUT, YAW_BACK - PI)     # turn the short way round to face out
TURN_STEPS = [('L', 1 / 3), ('R', 2 / 3), ('L', 1.0), ('R', 1.0)]
def pose_walk_back(t):
    if t <= WB_WALK: return walking(W_BACK, t)
    end_feet = W_BACK.at(WB_WALK)[2]
    u = seg(t, WB_WALK, WB_DUR); yaw = YAW_BACK + (YAW_END - YAW_BACK) * u
    feet = dict(end_feet)
    win = [(WB_WALK + 0.02, WB_WALK + 0.28), (WB_WALK + 0.30, WB_WALK + 0.56), (WB_WALK + 0.58, WB_WALK + 0.80), (WB_WALK + 0.80, WB_DUR - 0.02)]
    for (foot, st), (ta, tb) in zip(TURN_STEPS, win):
        y = YAW_BACK + (YAW_END - YAW_BACK) * st; sx = 1 if foot == 'L' else -1
        tgt = (body_pt(HOME, y, (sx * 0.12, 0.08, 0.0)), y, 0.0)
        if t >= tb: feet[foot] = tgt; continue
        if t > ta:
            raw = (t - ta) / (tb - ta); w = ss2(raw); cur = feet[foot]
            feet[foot] = (lerp(cur[0], tgt[0], w) + (0, 0.05 * math.sin(PI * raw), 0), cur[1] + (tgt[1] - cur[1]) * w, 0.0)
    S = stand(HOME, yaw, feet)
    return S

CLIPS = [('walk_out', WO_DUR, pose_walk_out), ('guide', G_DUR, pose_guide), ('check_in', CI_DUR, pose_check_in), ('walk_back', WB_DUR, pose_walk_back)]
CHAIN = [('walk_out', 'guide'), ('guide', 'guide'), ('guide', 'check_in'), ('check_in', 'walk_back'), ('walk_back', 'walk_out')]

# ================================================================== bake + checks
BAKED = [(n, *bake(f, d)) for n, d, f in CLIPS]
print('max leg/arm stretch', round(max(STRETCH), 3))
FN = {n: (d, f) for n, d, f in CLIPS}
def pose_vec(fn, t):
    Wr, Wp = solve(full(fn(t))); return np.concatenate([np.concatenate([Wp[n], Wr[n].ravel()]) for n, _, _ in JOINTS])
chk = []
for a, b in CHAIN:
    chk.append((a + ' end -> ' + b + ' start', float(np.abs(pose_vec(FN[a][1], FN[a][0]) - pose_vec(FN[b][1], 0.0)).max())))
for c in chk: print('CHECK', c)
# pops: largest per-frame joint jump in each clip (world position, m) -> should be small and smooth
pops, slide, lift = {}, {}, {}
for n, d, f in CLIPS:
    prevP = None; mx = 0.0; sl = 0.0; prevF = None; fl = 0.0
    for i in range(int(round(d * FPS)) + 1):
        Wr, Wp = solve(full(f(min(i / FPS, d))))
        P = np.array([Wp[j] for j, _, _ in JOINTS]); F = {s: Wp['Op_Foot_' + s] for s in 'LR'}
        if prevP is not None:
            mx = max(mx, float(np.abs(P - prevP).max()))
            for s in 'LR':
                if F[s][1] < 0.0805 and prevF[s][1] < 0.0805: sl = max(sl, float(np.linalg.norm((F[s] - prevF[s])[[0, 2]])))
        fl = max(fl, max(F['L'][1], F['R'][1]))
        prevP, prevF = P, F
    pops[n], slide[n], lift[n] = mx, sl, fl
print('max joint move per frame (m)', {k: round(v, 4) for k, v in pops.items()})
print('planted-foot max slide per frame (m)', slide)
print('max ankle height (m)', {k: round(v, 3) for k, v in lift.items()})
# boot never below ground: sole bottom = ankle - 0.08 (flat) -> ankle y >= 0.08 when planted
minank = min(float(solve(full(f(i / FPS)))[1]['Op_Foot_' + s][1]) for n, d, f in CLIPS for i in range(int(d * FPS) + 1) for s in 'LR')
print('min ankle y', round(minank, 4))

# ================================================================== write GLB
Wr0, Wp0 = solve(full(pose_guide(0.0))); T0, Q0 = to_local(Wr0, Wp0)
nodes = [{'name': 'Receiver', 'children': [], 'extras': {
    'asset': 'receiver', 'rig': 'Mine operator rig (props/mine_operator, commit 9209246): same Op_* joints minus Op_Chair, same suit',
    'origin': 'Receive_Point (ground), facing +Z while guiding; place the root so Receive_Point sits where he should stand',
    'home_point': [float(HOME[0]), 0.0, float(HOME[1])], 'home_yaw_rad': round(YAW_OUT, 5),
    'clip_chain': ['walk_out', 'guide (loop)', 'check_in', 'walk_back'], 'head_bone': 'Op_Head'}}]
jnode = {}
for n, p, t in JOINTS:
    jnode[n] = len(nodes)
    nd = {'name': n, 'translation': [float(x) for x in T0[n]], 'rotation': [float(x) for x in Q0[n]]}
    if n == 'Op_Head': nd['extras'] = {'look_at': 'yaw Op_Head about its local +Y toward the truck/crane (clamp about +-70 deg); rest look = body +Z'}
    nodes.append(nd)
for n, p, t in JOINTS:
    if p: nodes[jnode[p]].setdefault('children', []).append(jnode[n])
nodes[0]['children'].append(jnode['Op_Root'])
for nm, tr, ex in (('Receive_Point', [0.0, 0.0, 0.0], {'kind': 'marker', 'note': 'where he stands for guide + check_in (feet centred here, facing +Z); walk_out ends / walk_back starts here'}),
                   ('Home_Point', [float(HOME[0]), 0.0, float(HOME[1])], {'kind': 'marker', 'yaw_rad': round(YAW_OUT, 5), 'note': 'airlock/door spot: walk_out starts and walk_back ends here, facing Receive_Point'})):
    nodes[0]['children'].append(len(nodes)); nodes.append({'name': nm, 'translation': tr, 'extras': ex})
mesh_node = len(nodes); nodes.append({'name': 'Rx_Mesh', 'mesh': 0, 'skin': 0}); nodes[0]['children'].append(mesh_node)
ibm = np.zeros((len(JOINTS), 16), np.float32)
for i, (n, p, t) in enumerate(JOINTS):
    M = np.eye(4); M[:3, 3] = -REST_W[n]; ibm[i] = M.T.ravel()
skin = {'name': 'Rx_Skin', 'joints': [jnode[n] for n, _, _ in JOINTS], 'skeleton': jnode['Op_Root'], 'inverseBindMatrices': addbuf(ibm, 5126, 'MAT4')}
mesh = {'name': 'Rx_Mesh', 'primitives': [prim(PAINT, 1, True), prim(GLOW, 0, False)]}
anims = []
for name, ts, TT, QQ in BAKED:
    tin = addbuf(ts.astype(np.float32), 5126, 'SCALAR', None, True); ch, sm = [], []
    for n, _, _ in JOINTS:
        for path, arr in (('translation', TT[n]), ('rotation', QQ[n])):
            sm.append({'input': tin, 'output': addbuf(arr.astype(np.float32), 5126, 'VEC4' if path == 'rotation' else 'VEC3'), 'interpolation': 'LINEAR'})
            ch.append({'sampler': len(sm) - 1, 'target': {'node': jnode[n], 'path': path}})
    anims.append({'name': name, 'channels': ch, 'samplers': sm})
gl = {'asset': {'version': '2.0', 'generator': 'planet-stack build_receiver.py'}, 'scene': 0, 'scenes': [{'name': 'Scene', 'nodes': [0]}],
      'nodes': nodes, 'meshes': [mesh], 'skins': [skin], 'animations': anims,
      'materials': [{'name': 'SHM_GlowCyan', 'pbrMetallicRoughness': {'baseColorFactor': [0.02842604, 0.768151164, 1, 1], 'metallicFactor': 0, 'roughnessFactor': 0.5}, 'emissiveFactor': [0.02842604, 0.768151164, 1]},
                    {'name': 'SHM_Paint', 'pbrMetallicRoughness': {'metallicFactor': 0, 'roughnessFactor': 0.42}}],
      'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': len(bin_)}]}
js = json.dumps(gl, separators=(',', ':')).encode()
while len(js) % 4: js += b' '
while len(bin_) % 4: bin_.append(0)
out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(bin_), 0x004E4942) + bytes(bin_)
open(OUT, 'wb').write(out)
json.dump({'tris': PAINT.tris + GLOW.tris, 'paint': PAINT.tris, 'glow': GLOW.tris, 'checks': chk, 'max_move_per_frame': pops, 'slide': slide, 'max_stretch': max(STRETCH),
           'clips': [(n, float(ts[-1])) for n, ts, _, _ in BAKED]}, open(OUT.replace('.glb', '_report.json'), 'w'), indent=1)
print('wrote', OUT, len(out))
