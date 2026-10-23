"""Mine operator deck + skinned operator -> raw glTF (GLB), pure Python + numpy.
Planet Stack, Art & Animation. Original design (concept B look: white/graphite hulls, cyan strips).
usage: python3 build_mine_operator.py OUT_RAW.glb   then  pack_mine_operator.sh
glTF coords: +Y up, +Z = front (camera side), 1 unit = 1 m, origin = ground centre under the deck.
2 primitives (SHM_Paint with COLOR_0, SHM_GlowCyan), both skinned to one skin -> 2 draws."""
import sys, json, struct, math
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/op/raw.glb'
FPS = 30
DH = 2.2                       # deck top height (m)
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
J('Op_Chair', 'Op_Root', (0.45, DH, -0.35))
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

def quad(c, w, h, R, col, joint='Op_Root'):   # single-sided quad facing local +Z (screen ink)
    q = np.array([[-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2, 0], [-w / 2, h / 2, 0]]) @ R.T + c
    P, N, F = faces_to_mesh([q]); emit(P, N, F, col, joint, False, ao=0.0, noise=0.0)

def strut(p0, p1, w, col, joint, **kw):      # square-section beam between two points
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); d = p1 - p0; L = np.linalg.norm(d); y = d / L
    t = np.array([0, 0, 1.]) if abs(y[2]) < 0.9 else np.array([1, 0, 0.]); x = np.cross(y, t); x /= np.linalg.norm(x); z = np.cross(x, y)
    box((p0 + p1) / 2, (w, L, w), col, joint, R=np.column_stack([x, y, z]), **kw)

# ------------------------------------------------------------------ deck (static, Op_Root)
R0 = 'Op_Root'
XA, ZA = 1.3, 1.05                      # deck half extents
box((0, DH - 0.09, 0), (2 * XA, 0.18, 2 * ZA), WHITE, R0, ch=0.04, ao=0.25)              # deck slab (white hull)
box((0, DH + 0.006, 0), (2 * XA - 0.16, 0.02, 2 * ZA - 0.16), GRAPH2, R0, ao=0.0, grime=0.25)  # tread plate
box((0, DH - 0.2, ZA - 0.02), (2 * XA - 0.1, 0.05, 0.04), GRAPH, R0, ao=0.0)            # fascia hazard band backing
for k in range(9):                                                                        # diagonal amber hazard strips (geometry)
    x0 = -XA + 0.18 + k * 0.29
    q = np.array([[x0, DH - 0.175, ZA + 0.001], [x0 + 0.12, DH - 0.175, ZA + 0.001], [x0 + 0.20, DH - 0.035, ZA + 0.001], [x0 + 0.08, DH - 0.035, ZA + 0.001]])
    Pq, Nq, Fq = faces_to_mesh([q]); emit(Pq, Nq, Fq, AMBER, R0, False, ao=0.05, grime=0.2)
for sx in (-1, 1):                                                                        # side cyan strips under the slab edge
    box((sx * (XA + 0.004), DH - 0.13, 0), (0.012, 0.03, 2 * ZA - 0.3), None, R0, glow=True)
box((0, DH - 0.215, ZA + 0.002), (2 * XA - 0.3, 0.02, 0.012), None, R0, glow=True)        # front strip under the hazard band
# legs, footings, braces
LEGS = [(-1.12, -0.88), (1.12, -0.88), (-1.12, 0.88), (1.12, 0.88)]
for x, z in LEGS:
    box((x, (DH - 0.18) / 2 - 0.05, z), (0.16, DH - 0.08, 0.16), STEEL_L, R0, ao=0.3)
    box((x, 0.03, z), (0.36, 0.14, 0.36), GRAPH2, R0, ao=0.1)                   # footing pad (sinks 8 cm)
for z in (-0.88, 0.88):                                                                   # X braces on the long faces
    strut((-1.06, 0.25, z), (1.06, DH - 0.3, z), 0.06, STEEL, R0)
    strut((1.06, 0.25, z), (-1.06, DH - 0.3, z), 0.06, STEEL, R0)
for x in (-1.12, 1.12):
    strut((x, 0.25, -0.82), (x, DH - 0.3, 0.82), 0.06, STEEL, R0)
# under-deck power unit
box((0.35, 0.45, -0.1), (0.9, 0.8, 0.6), WHITE, R0, ao=0.3, grime=0.15)
box((0.35, 0.62, 0.205), (0.7, 0.05, 0.012), None, R0, glow=True)
box((0.35, 0.3, 0.2), (0.78, 0.16, 0.02), GRAPH, R0)
cyl((-0.1, 0.75, -0.1), (-1.06, 1.6, -0.82), 0.035, GRAPH, R0, n=6, caps=False)          # conduit up to the deck

# rails: posts, top rail, mid rail, kick plate. back side has the stair gap at x -1.3..-0.7
RY, RM = 1.05, 0.55
def rail_run(a, b, posts=True):
    a, b = np.asarray(a, float), np.asarray(b, float)
    cyl(a + (0, DH + RY, 0), b + (0, DH + RY, 0), 0.03, WHITE, R0, n=6, caps=False, ao=0.0)
    cyl(a + (0, DH + RM, 0), b + (0, DH + RM, 0), 0.02, STEEL_L, R0, n=6, caps=False, ao=0.05)
    m = (a + b) / 2; L = np.linalg.norm(b - a); d = (b - a) / L
    Rr = np.column_stack([d, [0, 1, 0], np.cross(d, [0, 1, 0])])
    box(m + (0, DH + 0.06, 0), (L, 0.12, 0.02), STEEL, R0, R=Rr, ao=0.2, grime=0.2)
    if posts:
        for k in range(int(round(L / 0.85)) + 1):
            p = a + (b - a) * k / max(int(round(L / 0.85)), 1)
            box(p + (0, DH + RY / 2, 0), (0.05, RY, 0.05), GRAPH2, R0, ao=0.15)
e = 0.05
rail_run((-XA + e, 0, ZA - e), (XA - e, 0, ZA - e))                  # front (camera side, watch rail)
rail_run((-XA + e, 0, -ZA + e), (-XA + e, 0, ZA - e))                # west
rail_run((XA - e, 0, -ZA + e), (XA - e, 0, ZA - e))                  # east
rail_run((-0.62, 0, -ZA + e), (XA - e, 0, -ZA + e))                  # back (gap at the stair head)
box((0, DH + RY - 0.045, ZA - e - 0.03), (2 * XA - 0.3, 0.014, 0.012), None, R0, glow=True)   # cyan strip under the front top rail

# stair along the back: ground at x +1.3 -> deck height at x -0.7, z -1.75..-1.05; landing x -1.3..-0.7
SZ0, SZ1, SX0, SX1 = -1.75, -1.07, 1.35, -0.66
for z in (SZ0, SZ1):
    strut((SX0 + 0.05, 0.0, z), (SX1, DH - 0.12, z), 0.07, GRAPH2, R0, ao=0.1)
NST = 8
for k in range(1, NST + 1):
    t = k / (NST + 1); x = SX0 + (SX1 - SX0) * t; y = DH * t
    box((x, y - 0.02, (SZ0 + SZ1) / 2), (0.19, 0.04, SZ1 - SZ0 - 0.08), STEEL_L, R0, ao=0.1, grime=0.3)
box((-0.98, DH - 0.06, (SZ0 + SZ1) / 2), (0.62, 0.12, SZ1 - SZ0), WHITE, R0, ch=0.02, ao=0.2)   # landing
box((-1.24, (DH - 0.12) / 2, SZ0 + 0.06), (0.1, DH - 0.12, 0.1), STEEL_L, R0, ao=0.3)          # landing column
box((-1.24, 0.03, SZ0 + 0.06), (0.26, 0.12, 0.26), GRAPH2, R0, ao=0.1)
cyl((SX0, 1.0, SZ0 + 0.02), (SX1, DH + RY, SZ0 + 0.02), 0.025, STEEL_L, R0, n=6, ao=0.05)      # stair handrail
cyl((SX1, DH + RY, SZ0 + 0.02), (-1.25, DH + RY, SZ0 + 0.02), 0.025, STEEL_L, R0, n=6, ao=0.05)
for x, y0 in ((SX0, 0.0), (0.33, DH * (SX0 - 0.33) / (SX0 - SX1)), (SX1, DH), (-1.25, DH)):
    box((x, y0 + (1.0 if x == SX0 else RY) / 2 + 0.0, SZ0 + 0.02), (0.04, 1.0 if x == SX0 else RY, 0.04), GRAPH2, R0)
cyl((SX1, DH + RY - 0.05, SZ0 + 0.045), (-1.2, DH + RY - 0.05, SZ0 + 0.045), 0.01, None, R0, n=4, glow=True, caps=False)

# console: desk on two pedestals, keyboard, main monitor, side screen
DZ0, DZ1, DY = -1.0, -0.66, 0.75
box((0.45, DH + DY - 0.025, (DZ0 + DZ1) / 2), (1.22, 0.05, DZ1 - DZ0), WHITE, R0, ch=0.015, ao=0.1)
for x in (-0.11, 1.01):
    box((x, DH + (DY - 0.05) / 2, (DZ0 + DZ1) / 2), (0.08, DY - 0.05, DZ1 - DZ0 - 0.04), GRAPH, R0, ao=0.25)
box((0.45, DH + 0.42, DZ0 + 0.03), (1.06, 0.5, 0.04), GRAPH2, R0, ao=0.2)                    # modesty panel
box((0.45, DH + DY + 0.012, -0.77), (0.46, 0.022, 0.17), GRAPH, R0, ao=0.0)        # keyboard
box((0.45, DH + DY + 0.025, -0.77), (0.40, 0.004, 0.012), None, R0, glow=True)                # key backlight strip
box((0.78, DH + DY + 0.008, -0.77), (0.13, 0.012, 0.11), GRAPH2, R0, ao=0.0)                 # trackpad
cyl((0.45, DH + DY, -0.93), (0.45, DH + 0.96, -0.93), 0.025, GRAPH2, R0, n=6, caps=False)    # monitor stand
box((0.45, DH + DY + 0.008, -0.93), (0.22, 0.016, 0.12), GRAPH2, R0)
tilt = rotm((1, 0, 0), math.radians(-10))
MC = np.array((0.45, DH + 1.17, -0.92))
box(MC, (0.70, 0.45, 0.05), GRAPH, R0, R=tilt, ch=0.015, ao=0.1)                                # monitor housing
box(MC + tilt @ (0, 0, 0.027), (0.64, 0.39, 0.004), None, R0, R=tilt, glow=True)                 # screen glow
for (cx, cy, w, h) in ((0, 0.155, 0.6, 0.02), (-0.18, -0.02, 0.2, 0.008), (-0.18, 0.06, 0.2, 0.008), (-0.18, -0.10, 0.2, 0.008),
                       (0.12, 0.04, 0.30, 0.008), (0.12, -0.13, 0.30, 0.008), (-0.03, -0.045, 0.008, 0.18), (0.27, -0.045, 0.008, 0.18),
                       (0.21, 0.04, 0.035, 0.035)):
    quad(MC + tilt @ (cx, cy, 0.0295), w, h, tilt, SCREEN_INK if w != 0.035 else AMBER)   # UI ink: haul-loop map + truck dot
side = rotm((0, 1, 0), math.radians(-35)) @ rotm((1, 0, 0), math.radians(-12))
SC = np.array((-0.0, DH + 1.02, -0.86))
box(SC, (0.34, 0.24, 0.04), GRAPH, R0, R=side, ao=0.1)
box(SC + side @ (0, 0, 0.022), (0.3, 0.2, 0.004), None, R0, R=side, glow=True)
for cy in (0.05, -0.02, -0.07):
    quad(SC + side @ (0.0, cy, 0.0245), 0.24, 0.012, side, SCREEN_INK)
cyl((0.0, DH + DY, -0.86), (0.0, DH + 0.92, -0.86), 0.018, GRAPH2, R0, n=6, caps=False)
# mast + beacon at the front-east corner
cyl((XA - 0.12, DH, -ZA + 0.12), (XA - 0.12, DH + 2.0, -ZA + 0.12), 0.03, STEEL_L, R0, n=6)
box((XA - 0.12, DH + 2.0, -ZA + 0.12), (0.12, 0.06, 0.12), GRAPH, R0)
sphere((XA - 0.12, DH + 2.08, -ZA + 0.12), 0.05, None, R0, seg=8, rings=4, glow=True)
box((XA - 0.12, DH + 1.6, -ZA + 0.2), (0.34, 0.22, 0.02), GRAPH2, R0, R=rotm((1, 0, 0), 0.35))   # dish/antenna panel

# chair: base star + post on Op_Root (static); seat + lumbar pad on Op_Chair (swivels)
CH = REST_W['Op_Chair']
for k in range(5):
    a = 2 * math.pi * k / 5 + 0.3; d = np.array([math.cos(a), 0, math.sin(a)])
    strut(CH + (0, 0.06, 0), CH + d * 0.27 + (0, 0.04, 0), 0.04, GRAPH, R0, ao=0.0)
cyl(CH + (0, 0.06, 0), CH + (0, 0.34, 0), 0.03, STEEL_L, R0, n=6, caps=False)
CJ = 'Op_Chair'
box(CH + (0, 0.36, 0), (0.08, 0.05, 0.08), GRAPH, CJ)
box(CH + (0, 0.405, 0.02), (0.46, 0.07, 0.44), GRAPH2, CJ, ch=0.025, ao=0.1)
box(CH + (0, 0.44, 0.02), (0.40, 0.004, 0.38), GRAPH, CJ, ao=0.0)
strut(CH + (0, 0.38, -0.2), CH + (0, 0.62, -0.25), 0.04, GRAPH, CJ)
box(CH + (0, 0.62, -0.26), (0.36, 0.14, 0.05), WHITE, CJ)
box(CH + (0, 0.62, -0.288), (0.28, 0.012, 0.006), None, CJ, glow=True)
DECK_TRIS = PAINT.tris + GLOW.tris

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
OP_TRIS = PAINT.tris + GLOW.tris - DECK_TRIS
print('tris deck', DECK_TRIS, 'operator', OP_TRIS, 'total', PAINT.tris + GLOW.tris, 'paint', PAINT.tris, 'glow', GLOW.tris)

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
    Wr['Op_Chair'] = yawm(S['chair_yaw']); Wp['Op_Chair'] = np.array([S['chair'][0], DH, S['chair'][1]])
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

# ------------------------------------------------------------------ animation design
def ss(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def ss2(x): x = min(max(x, 0.0), 1.0); return x * x * x * (x * (6 * x - 15) + 10)    # smootherstep
def seg(t, a, b): return ss2((t - a) / (b - a))
def lerp(a, b, u): return np.asarray(a, float) + (np.asarray(b, float) - np.asarray(a, float)) * u
PI = math.pi
S_POS = np.array([0.45, -0.35])        # chair centre = seated body position
T_POS = np.array([0.20, -0.35])        # standing spot beside the desk (facing -X)
R_POS = np.array([-0.60, 0.60])        # watch spot at the front rail (facing +Z, the south haul road)
KEY_Y, KEY_Z = DH + DY + 0.055, -0.775
RAIL_Y, RAIL_Z = DH + RY + 0.02, ZA - e - 0.07
def body_pt(pos, yaw, local):          # body-local (x left, y up, z fwd) -> world
    return np.array([pos[0], DH, pos[1]]) + yawm(yaw) @ np.asarray(local, float)
def feet_at(pos, yaw, fwd=0.02, half=0.12):
    return {'L': (body_pt(pos, yaw, (half, 0.08, fwd)), yaw, 0.0), 'R': (body_pt(pos, yaw, (-half, 0.08, fwd)), yaw, 0.0)}

def seated(yaw, t_type=None, head_yaw=0.0):
    """seated in the chair at S_POS, body yaw `yaw`. desk-facing when yaw == PI."""
    S = dict(pos=S_POS, yaw=yaw, chair=S_POS, chair_yaw=yaw - PI, pel=(0, 0.585, 0.0), pel_pitch=0.0, spine=0.10, chest=0.06,
             head_yaw=head_yaw, head_pitch=-0.05)
    S['foot_L'] = (body_pt(S_POS, yaw, (0.13, 0.08, 0.40)), yaw, 0.0); S['foot_R'] = (body_pt(S_POS, yaw, (-0.13, 0.08, 0.40)), yaw, 0.0)
    return S
def typing_hands(t, mouse=0.0):
    # facing -Z: character left = -X
    bobL = 0.012 * max(0, math.sin(2 * PI * 4 * t)); bobR = 0.012 * max(0, math.sin(2 * PI * 4 * t + PI))
    hl = np.array([0.45 - 0.12, KEY_Y + bobL, KEY_Z]); hr = np.array([0.45 + 0.12, KEY_Y + bobR * (1 - mouse), KEY_Z])
    hr = lerp(hr, (0.78, DH + DY + 0.05, -0.77), mouse)
    return hl, hr

def pose_sit_type(t):        # 4.0 s loop
    S = seated(PI)
    look = seg(t, 1.4, 1.9) * (1 - seg(t, 2.9, 3.4))               # glance at the side screen (haul map) and back
    mouse = seg(t, 1.5, 1.9) * (1 - seg(t, 2.8, 3.2))
    S['head_yaw'] = 0.42 * look; S['twist'] = 0.08 * look; S['head_pitch'] = -0.05 - 0.06 * look
    S['spine'] = 0.10 + 0.02 * math.sin(2 * PI * t / 4.0)
    S['hand_L'], S['hand_R'] = typing_hands(t, mouse); S['wrist'] = 0.25; S['elbow_out'] = 0.8
    return S

def rail_pose(t=0.0, head_yaw=0.0, sway=0.0):
    S = dict(pos=R_POS, yaw=2 * PI, chair=S_POS, chair_yaw=1.5 * PI - PI, pel=(sway, 0.905, 0.0), pel_pitch=0.04, spine=0.06, chest=0.06,
             head_yaw=head_yaw, head_pitch=-0.22, pel_roll=-sway * 1.5, elbow_out=0.7, wrist=-0.3)
    f = feet_at(R_POS, 2 * PI, 0.0, 0.13); S['foot_L'], S['foot_R'] = f['L'], f['R']
    S['hand_L'] = np.array([R_POS[0] + 0.23, RAIL_Y, RAIL_Z]); S['hand_R'] = np.array([R_POS[0] - 0.23, RAIL_Y, RAIL_Z])
    return S

def pose_watch(t):           # 3.0 s loop; Op_Head yaw = look direction (code may override toward the truck)
    hy = 0.62 * seg(t, 0.25, 1.05) - 1.15 * seg(t, 1.35, 2.25) + 0.53 * seg(t, 2.35, 2.95)
    S = rail_pose(t, head_yaw=hy, sway=0.025 * math.sin(2 * PI * t / 3.0))
    S['twist'] = 0.25 * hy * 0.3
    S['hand_L'] = S['hand_L'] + (0, 0.0, 0.0); S['hand_R'] = S['hand_R'] + (0, 0.02 * math.sin(PI * seg(t, 1.0, 2.2)), 0)
    return S

def bez(P, s):
    P = [np.asarray(p, float) for p in P]; u = 1 - s
    return u ** 3 * P[0] + 3 * u * u * s * P[1] + 3 * u * s * s * P[2] + s ** 3 * P[3]
def walk(t, t0, t1, path, yaw0, yaw1, steps, start_feet, end_half=0.13, end_fwd=0.0):
    """footstep walk. steps: list of (foot, s_target, ta, tb). planted feet never move (no sliding)."""
    yaw_s = lambda s: yaw0 + (yaw1 - yaw0) * ss(s)
    plants = {'L': [(-1e9, start_feet['L'])], 'R': [(-1e9, start_feet['R'])]}
    for foot, s_t, ta, tb in steps:
        sx = 1 if foot == 'L' else -1; y = yaw_s(s_t); p = bez(path, s_t)
        half = end_half if s_t >= 1 else 0.12; fwd = end_fwd if s_t >= 1 else 0.0
        plants[foot].append(((ta, tb), (body_pt(p, y, (sx * half, 0.08, fwd)), y, 0.0)))
    feet = {}
    for foot in 'LR':
        cur = plants[foot][0][1]
        for (win, tgt) in plants[foot][1:]:
            ta, tb = win
            if t >= tb: cur = tgt; continue
            if t > ta:
                u = ss((t - ta) / (tb - ta)); raw = (t - ta) / (tb - ta)
                p = lerp(cur[0], tgt[0], u) + (0, 0.075 * math.sin(PI * raw), 0)
                cur = (p, cur[1] + (tgt[1] - cur[1]) * u, 0.25 * math.sin(PI * raw) * (1 - raw) - 0.1 * math.sin(PI * raw) * raw)
            break
        feet[foot] = cur
    sb = ss2((t - t0) / (t1 - t0)); pos = bez(path, sb)
    # keep the pelvis between the feet laterally (weight shift toward the planted foot)
    return pos, yaw_s(sb), feet

STAND_FEET = feet_at(T_POS, 1.5 * PI, 0.02, 0.12)
def seated_swivel(yaw_now, yaw_desk_w):
    """seated with chair yaw = body yaw; feet blend from desk spots (w=1) to stand spots (w=0), lifted mid-way."""
    S = seated(yaw_now)
    fd = {'L': body_pt(S_POS, yaw_now, (0.13, 0.08, 0.40)), 'R': body_pt(S_POS, yaw_now, (-0.13, 0.08, 0.40))}
    fs = {'L': body_pt(S_POS, yaw_now, (0.12, 0.08, 0.27)), 'R': body_pt(S_POS, yaw_now, (-0.12, 0.08, 0.27))}
    lift = 0.06 * math.sin(PI * yaw_desk_w)
    for s in 'LR': S['foot_' + s] = (lerp(fs[s], fd[s], yaw_desk_w) + (0, lift, 0), yaw_now, 0.0)
    return S

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

def relaxed_hands(pos, yaw, t=0.0, swing=0.0):
    return (body_pt(pos, yaw, (0.24, 0.87, 0.06 + swing)), body_pt(pos, yaw, (-0.24, 0.87, 0.06 - swing)))

WALK_A = [T_POS, T_POS + (-0.45, 0.0), R_POS + (0.0, -0.5), R_POS]
def pose_stand_walk(t):      # 1.6 s: swivel (0-0.35) -> stand (0.35-0.75) -> walk to the rail (0.75-1.6)
    if t <= 0.35:
        u = seg(t, 0.0, 0.35); y = PI + 0.5 * PI * u
        S = full(seated_swivel(y, 1 - u)); S0 = full(pose_sit_type(0.0))
        hl, hr = S0['hand_L'], S0['hand_R']
        kl = body_pt(S_POS, y, (0.2, DH * 0 + 0.66, 0.25)); kr = body_pt(S_POS, y, (-0.2, 0.66, 0.25))  # hands to knees
        S['hand_L'], S['hand_R'] = lerp(hl, kl, ss(u * 1.3)), lerp(hr, kr, ss(u * 1.3))
        S['wrist'] = 0.25 * (1 - u); S['elbow_out'] = 0.8 - 0.2 * u; S['head_pitch'] = -0.05
        return S
    if t <= 0.75:
        u = seg(t, 0.35, 0.75); y = 1.5 * PI
        A_ = full(seated_swivel(y, 0.0)); A_['hand_L'] = body_pt(S_POS, y, (0.2, 0.66, 0.25)); A_['hand_R'] = body_pt(S_POS, y, (-0.2, 0.66, 0.25)); A_['elbow_out'] = 0.6
        B_ = full(dict(pos=T_POS, yaw=y, chair=S_POS, chair_yaw=y - PI, pel=(0, 0.905, 0.0), pel_pitch=0.04, spine=0.04, chest=0.03,
                       head_yaw=0.0, head_pitch=-0.05, foot_L=STAND_FEET['L'], foot_R=STAND_FEET['R']))
        B_['hand_L'], B_['hand_R'] = relaxed_hands(T_POS, y)
        S = mix(A_, B_, u)
        S['pos'] = lerp(S_POS, T_POS, u); S['chair'] = S_POS
        lean = math.sin(PI * min(u * 1.15, 1.0)); S['spine'] += 0.45 * lean; S['chest'] += 0.15 * lean; S['pel_pitch'] += 0.3 * lean
        S['pel'] = (0, A_['pel'][1] + (0.905 - A_['pel'][1]) * ss(u), -0.08 * lean)
        S['head_pitch'] = -0.05 - 0.25 * lean
        S['foot_L'], S['foot_R'] = STAND_FEET['L'], STAND_FEET['R']
        return S
    steps = [('L', 0.36, 0.78, 1.00), ('R', 0.70, 0.98, 1.20), ('L', 1.0, 1.14, 1.34), ('R', 1.0, 1.30, 1.52)]
    pos, yaw, feet = walk(t, 0.75, 1.52, WALK_A, 1.5 * PI, 2 * PI, steps, STAND_FEET, 0.13, 0.0)
    R_ = full(rail_pose(0.0)); u = seg(t, 0.75, 1.6)
    ph = (t - 0.75) / 0.8
    sw = 0.14 * math.sin(2 * PI * ph * 1.2) * (1 - seg(t, 1.3, 1.5))
    hl, hr = relaxed_hands(pos, yaw, swing=sw)
    g = seg(t, 1.36, 1.6)
    S = full(dict(pos=pos, yaw=yaw, chair=S_POS, chair_yaw=0.5 * PI, pel=(0, 0.905 - (0.035 + 0.01 * math.cos(2 * PI * ph * 2.5)) * seg(t, 0.75, 0.95) * (1 - g), 0.0),
                  pel_pitch=0.04, spine=0.04 + 0.02 * g, chest=0.03 + 0.03 * g, head_yaw=0.0, head_pitch=-0.05 - 0.17 * seg(t, 1.0, 1.5),
                  foot_L=feet['L'], foot_R=feet['R'], hand_L=lerp(hl, R_['hand_L'], g), hand_R=lerp(hr, R_['hand_R'], g),
                  elbow_out=0.6 + 0.1 * g, wrist=-0.3 * g))
    return S

WALK_B = [R_POS, R_POS + (0.25, -0.35), T_POS + (-0.45, 0.1), T_POS]
def pose_walk_back(t):       # 1.6 s: walk back (0-0.85) -> sit (0.85-1.25) -> swivel to the desk (1.25-1.6)
    if t <= 0.85:
        rf = feet_at(R_POS, 2 * PI, 0.0, 0.13)
        steps = [('L', 0.30, 0.04, 0.26), ('R', 0.62, 0.24, 0.46), ('L', 1.0, 0.42, 0.62), ('R', 1.0, 0.56, 0.78)]
        pos, yaw, feet = walk(t, 0.0, 0.80, WALK_B, 2 * PI, 3.5 * PI, steps, rf, 0.12, 0.02)
        R_ = full(rail_pose(0.0)); g = 1 - seg(t, 0.0, 0.25)
        ph = t / 0.8; sw = 0.14 * math.sin(2 * PI * ph * 1.2) * seg(t, 0.1, 0.3) * (1 - seg(t, 0.6, 0.8))
        hl, hr = relaxed_hands(pos, yaw, swing=sw)
        S = full(dict(pos=pos, yaw=yaw, chair=S_POS, chair_yaw=0.5 * PI, pel=(0, 0.905 - (0.035 + 0.01 * math.cos(2 * PI * ph * 2.5)) * (1 - g) * (1 - seg(t, 0.62, 0.85)), 0.0),
                      pel_pitch=0.04, spine=0.04 + 0.02 * g, chest=0.03 + 0.03 * g, head_yaw=0.0, head_pitch=-0.05 - 0.17 * g,
                      foot_L=feet['L'], foot_R=feet['R'], hand_L=lerp(hl, R_['hand_L'], g), hand_R=lerp(hr, R_['hand_R'], g),
                      elbow_out=0.6 + 0.1 * g, wrist=-0.3 * g))
        return S
    if t <= 1.25:   # sit = time-reverse of the stand-up, with yaw 3.5*PI (== 1.5*PI)
        S = pose_stand_walk(0.35 + 0.75 - (0.35 + (t - 0.85)))   # maps 0.85..1.25 -> 0.75..0.35
        S['yaw'] += 2 * PI; S['chair_yaw'] += 2 * PI
        for s in 'LR': S['foot_' + s] = (S['foot_' + s][0], S['foot_' + s][1] + 2 * PI, S['foot_' + s][2])
        return S
    S = pose_stand_walk(0.35 - (t - 1.25))                       # swivel back: reverse of 0..0.35
    S['yaw'] += 2 * PI; S['chair_yaw'] += 2 * PI
    for s in 'LR': S['foot_' + s] = (S['foot_' + s][0], S['foot_' + s][1] + 2 * PI, S['foot_' + s][2])
    return S

CLIPS = [('op_sit_type', 4.0, pose_sit_type), ('op_stand_walk_to_rail', 1.6, pose_stand_walk),
         ('op_watch_rail', 3.0, pose_watch), ('op_walk_back_sit', 1.6, pose_walk_back)]
def pose_cycle(t):
    for n, d, f in CLIPS:
        if t <= d + 1e-9: return f(t)
        t -= d
    return CLIPS[-1][2](CLIPS[-1][1])
CYCLE_LEN = sum(d for _, d, _ in CLIPS)

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

BAKED = [(n, *bake(f, d)) for n, d, f in CLIPS] + [('op_cycle', *bake(pose_cycle, CYCLE_LEN))]
print('max leg/arm stretch', round(max(STRETCH), 3))

# boundary checks: neighbouring clips start/end on the same pose
def pose_vec(fn, t):
    Wr, Wp = solve(full(fn(t))); return np.concatenate([np.concatenate([Wp[n], Wr[n].ravel()]) for n, _, _ in JOINTS])
chk = []
for i, (n, d, f) in enumerate(CLIPS):
    nn, dn, fn_ = CLIPS[(i + 1) % 4]
    chk.append((n + ' end -> ' + nn + ' start', float(np.abs(pose_vec(f, d) - pose_vec(fn_, 0.0)).max())))
for n, d, f in CLIPS: chk.append((n + ' loop (start vs end)', float(np.abs(pose_vec(f, 0.0) - pose_vec(f, d)).max())))
for c in chk: print('CHECK', c)

# foot-slide check: planted foot (height < 0.085 above deck, and on the floor in the previous frame) must not move horizontally
slide = {}
for n, d, f in CLIPS:
    mx = 0.0; prev = None
    for i in range(int(d * FPS) + 1):
        Wr, Wp = solve(full(f(i / FPS)))
        cur = {s: Wp['Op_Foot_' + s] for s in 'LR'}
        if prev:
            for s in 'LR':
                if cur[s][1] - DH < 0.0805 and prev[s][1] - DH < 0.0805:
                    mx = max(mx, float(np.linalg.norm((cur[s] - prev[s])[[0, 2]])))
        prev = cur
    slide[n] = mx
print('planted-foot max slide per frame (m)', slide)

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

# node TRS default = first frame of op_sit_type (so a static load shows him seated at the desk)
Wr0, Wp0 = solve(full(pose_sit_type(0.0))); T0, Q0 = to_local(Wr0, Wp0)
nodes = [{'name': 'MineOperator', 'children': [], 'extras': {'asset': 'mine_operator', 'place_at': 'Operator_Deck (Mine glTF coords)', 'deck_top_y': DH,
          'clip_chain': ['op_sit_type', 'op_stand_walk_to_rail', 'op_watch_rail', 'op_walk_back_sit'], 'head_bone': 'Op_Head'}}]
jnode = {}
for n, p, t in JOINTS:
    jnode[n] = len(nodes)
    nd = {'name': n, 'translation': [float(x) for x in T0[n]], 'rotation': [float(x) for x in Q0[n]]}
    if n == 'Op_Head': nd['extras'] = {'look_at': 'yaw Op_Head about its local +Y toward the truck (clamp about +-70 deg); rest look = body +Z'}
    nodes.append(nd)
for n, p, t in JOINTS:
    if p: nodes[jnode[p]].setdefault('children', []).append(jnode[n])
nodes[0]['children'].append(jnode['Op_Root'])
mesh_node = len(nodes); nodes.append({'name': 'Op_Mesh', 'mesh': 0, 'skin': 0}); nodes[0]['children'].append(mesh_node)
ibm = np.zeros((len(JOINTS), 16), np.float32)
for i, (n, p, t) in enumerate(JOINTS):
    M = np.eye(4); M[:3, 3] = -REST_W[n]; ibm[i] = M.T.ravel()
skin = {'name': 'Op_Skin', 'joints': [jnode[n] for n, _, _ in JOINTS], 'skeleton': jnode['Op_Root'], 'inverseBindMatrices': addbuf(ibm, 5126, 'MAT4')}
mesh = {'name': 'Op_Mesh', 'primitives': [prim(PAINT, 1, True), prim(GLOW, 0, False)]}
anims = []
for name, ts, TT, QQ in BAKED:
    tin = addbuf(ts.astype(np.float32), 5126, 'SCALAR', None, True); ch, sm = [], []
    for n, _, _ in JOINTS:
        for path, arr in (('translation', TT[n]), ('rotation', QQ[n])):
            sm.append({'input': tin, 'output': addbuf(arr.astype(np.float32), 5126, 'VEC4' if path == 'rotation' else 'VEC3'), 'interpolation': 'LINEAR'})
            ch.append({'sampler': len(sm) - 1, 'target': {'node': jnode[n], 'path': path}})
    anims.append({'name': name, 'channels': ch, 'samplers': sm})
gl = {'asset': {'version': '2.0', 'generator': 'planet-stack build_mine_operator.py'}, 'scene': 0, 'scenes': [{'name': 'Scene', 'nodes': [0]}],
      'nodes': nodes, 'meshes': [mesh], 'skins': [skin], 'animations': anims,
      'materials': [{'name': 'SHM_GlowCyan', 'pbrMetallicRoughness': {'baseColorFactor': [0.02842604, 0.768151164, 1, 1], 'metallicFactor': 0, 'roughnessFactor': 0.5}, 'emissiveFactor': [0.02842604, 0.768151164, 1]},
                    {'name': 'SHM_Paint', 'pbrMetallicRoughness': {'metallicFactor': 0, 'roughnessFactor': 0.42}}],
      'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': len(bin_)}]}
js = json.dumps(gl, separators=(',', ':')).encode()
while len(js) % 4: js += b' '
while len(bin_) % 4: bin_.append(0)
out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(bin_), 0x004E4942) + bytes(bin_)
open(OUT, 'wb').write(out)
json.dump({'tris_deck': DECK_TRIS, 'tris_operator': OP_TRIS, 'tris_total': PAINT.tris + GLOW.tris, 'checks': chk, 'slide': slide, 'max_stretch': max(STRETCH),
           'clips': [(n, float(ts[-1])) for n, ts, _, _ in BAKED]}, open(OUT.replace('.glb', '_report.json'), 'w'), indent=1)
print('wrote', OUT, len(out))
