"""Planet Stack - launch crew boarding animation (Art Assistant 3).
Pure Python + numpy. Reads the decimated pass-3 suit (extract_suit.py -> suit_A.npz), builds an 18-joint game rig per crew member,
procedurally animates 4 crew (radio call -> walk to the Launch Pad -> staggered hand-over-hand climb of the ship ladder -> into the hatch)
with planted feet / hands, and writes a plain GLB (no extensions) for gltfpack.
python3 build_boarding.py SUIT.npz OUT_RAW.glb OUT_TIMING.json [--rung-pair-s 1.6]
All positions are Launch-Pad-local glTF (pad GLB root = identity): +Y up, the game camera looks from +Z.
Ladder / hatch numbers were measured read-only from launch_pad_game.glb (md5 816f18f3...): rungs y 0.65 + 0.6 i (i 0..34),
rails top / hatch deck y 21.85, ladder axis = Ship_Center (0, -13) + LU * 4.45 with LU = (0.866, 0, 0.5)."""
import sys, json, math, struct, os
import numpy as np
from scipy.interpolate import PchipInterpolator

ARGS = sys.argv[1:]
def opt(k, d):
    return type(d)(ARGS[ARGS.index(k) + 1]) if k in ARGS else d
SUIT, OUT, TIMING = ARGS[0], ARGS[1], ARGS[2]
RUNG_PAIR_S = opt('--rung-pair-s', 1.6)
FPS = 30
TAU = 2 * math.pi

# ----------------------------------------------------------------------------- pad geometry (read-only measurements)
SHIP_C = np.array([0.0, 0.0, -13.0])
LU = np.array([0.8660254, 0.0, 0.5])            # ladder outward (from the hull toward the climber)
LT = np.array([0.5, 0.0, -0.8660254])           # ladder lateral
PAD_Y = 0.25
RUNG_Y = [0.65 + 0.6 * i for i in range(35)]
DECK_Y = 21.85
SOLE_LIFT = float(os.environ.get('SOLE_LIFT', 0.0015))   # v4: 1.5 mm (AA2: standing soles 0-3 mm above the deck top); v3: 5 mm. boot soles skin ~2-3 mm below the ankle target plane when the foot rolls: plant deck feet 5 mm high so no sole sinks into the wing deck
LAD_R = 4.45                                    # ladder plane radius from the ship axis
def lad(r, lat=0.0, y=0.0): return SHIP_C + LU * r + LT * lat + np.array([0, y, 0])
STAND = lad(4.95, 0.0, PAD_Y)                   # where a climber stands, facing the ladder (-LU), before mounting
DECK_U = 4.53                                   # deck foot spot (AA2: solid deck at t +/-0.9, u 4.3-4.7)
DECK_T = 0.89                                   # v3: 3 cm in from 0.92 (lead-side arm clears the guard rail by >= 3 cm)
TRAIL_U = 4.60                                  # v3: trail (inner) boot plants a little aft so the outer boot can step past it to the hull side
WALKIN_U = 4.22                                 # v3: outer boot's spot on the wing beside the hull before the doorway step
SIDES = [float(x) for x in opt('--mantle-sides', '1,-1,1,-1').split(',')]   # mantle step-off side per climber (+1 = +t)
ELAT_K = float(os.environ.get('ELAT_K', 0.36)); ELBOW_Z = float(os.environ.get('ELBOW_Z', -1.2)); KNEE_V = [float(x) for x in os.environ.get('KNEE_V', '1.0,0.1,0.0').split(',')]
FOOT_BACK = 0.13; HAND_BACK = 0.11
FOOT_DU = float(os.environ.get('FOOT_DU', 0.20)); FOOT_T = 0.12; HAND_T = float(os.environ.get('HAND_T', 0.12))
FOL_U = float(os.environ.get('FOL_U', 4.70)); FOL_T = float(os.environ.get('FOL_T', 0.11)); FOL_L = float(os.environ.get('FOL_L', 0.80)); FOL_A = float(os.environ.get('FOL_A', 0.025)); FOL_K = float(os.environ.get('FOL_K', 0.0)); FOL_P = float(os.environ.get('FOL_P', 1.0)); FOL_T0 = 0.25; FOL_BL = 0.9
YTOP = float(os.environ.get('YTOP', 20.10))
MANT_Y = float(os.environ.get('MANT_Y', 20.93)); RAIL_TOPG = float(os.environ.get('RAIL_TOPG', 21.79)); REL_BK = float(os.environ.get('REL_BK', 0.12))     # mantle press height (y_b) while the lead boot steps over
MK = [float(x) for x in os.environ.get('MK', '-1.0,0.5,0.0').split(',')]
MKT = [float(x) for x in os.environ.get('MKT', '-0.8,0.5,0.0').split(',')]; KW = [float(os.environ.get('KW', 0.6))]
RAIL_EL = float(os.environ.get('RAIL_EL', -0.4))
FOL_MU = float(os.environ.get('FOL_MU', 0.06))
MANT_STAND = float(os.environ.get('MANT_STAND', 5.0))
PATH_PF = float(os.environ.get('PATH_PF', 0.85))
L34_Y = float(os.environ.get('L34_Y', 19.55))
LF_U = float(os.environ.get('LF_U', 4.52)); LF_T = float(os.environ.get('LF_T', 0.80))
CLIMB_R = 4.69                                  # body (root) radius while on the ladder (v3: the suit pack fits the 0.75 m cage only at 4.69-4.71)
# crew path markers in the pad GLB (Crew_Path_01..05): airlock AL-2 door -> receiver spot -> apron -> pad -> Ladder_Foot
CP = {1: (-11.19, 0.30, 7.94), 2: (-7.85, 0.30, 8.20), 3: (-2.40, 0.10, 2.20), 4: (3.20, 0.25, -3.40), 5: (4.50, 0.25, -10.40)}
# the straight Crew_Path_04 -> Ladder_Foot line crosses the ship-leg foot pad at (4.1, -5.9) (r 1.05), so the file goes round it on the outside
SHARED = [np.array(CP[2]), np.array(CP[3]), np.array((5.0, 0.25, -3.6)), np.array((6.15, 0.25, -5.9)), np.array((6.35, 0.25, -8.6))]
LEG_FEET = [np.array((4.10, 0.25, -5.90)), np.array((8.20, 0.25, -13.0))]

# ----------------------------------------------------------------------------- suit + rig
S = np.load(SUIT)
JP = {str(k): v.astype(float) for k, v in zip(S['jnames'], S['jpos'])}
HEADC = S['headc'].astype(float)

# ---- v3 grip glove (my copy of the suit only; AA2/ship crew.py untouched).  The pass-3 glove is 5 closed pieces + 42 zero-thickness flaps,
# so any rod through the hand crosses skin.  Replace each glove with a closed, thick hook: a C-shaped finger wrap (inner r 37 mm,
# outer r 60 mm, 204 deg, 100 mm wide) on a palm block.  In the grip frame (body axes: +x left, +y up, +z toward the ladder; wrist at 0)
# the wrap centre is GRIP_C and the opening faces straight down, so a rung (50 mm box, 35.4 mm half-diagonal) drops into the wrap with
# 0-2 mm contact and its axis never crosses the glove skin.  Bind-space glove = GRIP_RG^T * grip-space, so a hand bone set to
# R_root @ GRIP_RG puts the wrap exactly on the rung.
GRIP_RG = None   # filled below once Rx exists
GRIP_C = np.array([0.0, -0.03, float(os.environ.get("GRIP_Z", 0.12))]); GRIP_RI, GRIP_RO, GRIP_W = 0.037, 0.060, 0.05
def _glove_tris():
    import math as _m
    T = []
    def quad(a, b, c, d, out):
        n = np.cross(b - a, c - a)
        if n @ out < 0: a, b, c, d = a, d, c, b
        T.extend([(a, b, c), (a, c, d)])
    al = [_m.radians(-12 + 204 * k / 10) for k in range(11)]
    P_ = lambda r, a, x: GRIP_C + np.array([x, r * _m.sin(a), r * _m.cos(a)])
    rad = lambda a: np.array([0, _m.sin(a), _m.cos(a)])
    for a0, a1 in zip(al[:-1], al[1:]):
        am = (a0 + a1) / 2
        quad(P_(GRIP_RO, a0, -GRIP_W), P_(GRIP_RO, a1, -GRIP_W), P_(GRIP_RO, a1, GRIP_W), P_(GRIP_RO, a0, GRIP_W), rad(am))
        quad(P_(GRIP_RI, a0, -GRIP_W), P_(GRIP_RI, a1, -GRIP_W), P_(GRIP_RI, a1, GRIP_W), P_(GRIP_RI, a0, GRIP_W), -rad(am))
        for x in (-GRIP_W, GRIP_W):
            quad(P_(GRIP_RI, a0, x), P_(GRIP_RI, a1, x), P_(GRIP_RO, a1, x), P_(GRIP_RO, a0, x), np.array([np.sign(x), 0, 0]))
    for a_, sg in ((al[0], -1), (al[-1], 1)):
        tg = np.array([0, _m.cos(a_), -_m.sin(a_)]) * sg
        quad(P_(GRIP_RI, a_, -GRIP_W), P_(GRIP_RO, a_, -GRIP_W), P_(GRIP_RO, a_, GRIP_W), P_(GRIP_RI, a_, GRIP_W), tg)
    lo, hi = np.array([-0.048, -0.045, -0.035]), np.array([0.048, 0.022, GRIP_C[2] - 0.045])   # palm / back-of-hand block (wrist cuff side)
    cn = lambda i, j, k: np.array([(lo, hi)[i][0], (lo, hi)[j][1], (lo, hi)[k][2]])
    for ax in range(3):
        for sd in (0, 1):
            idx = [(i, j, k) for i in (0, 1) for j in (0, 1) for k in (0, 1) if (i, j, k)[ax] == sd]
            a, b, d, c = [cn(*q) for q in idx]
            o = np.zeros(3); o[ax] = 1 if sd else -1; quad(a, b, c, d, o)
    return np.array(T)
SU = {k: S[k] for k in S.files}
def _swap_gloves(SU):
    gn = [str(x) for x in SU['gnames']]; G0 = SU['G']; keep = np.ones(len(G0), bool)
    for h in ('Hand_L', 'Hand_R'): keep &= np.array(gn)[G0] != h
    Pn, Nn, Cn, Gn = [SU['P'][keep]], [SU['N'][keep]], [SU['C'][keep]], [G0[keep]]
    tri = _glove_tris(); RGt = GRIP_RG.T
    for h in ('Hand_L', 'Hand_R'):
        w = JP[h]; V = tri.reshape(-1, 3) @ RGt.T + w
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n = n / np.linalg.norm(n, axis=1, keepdims=True); n = np.repeat(n @ RGt.T, 3, 0)
        Pn.append(V.astype(SU['P'].dtype)); Nn.append(n.astype(SU['N'].dtype)); Cn.append(np.full(len(V), 1, SU['C'].dtype)); Gn.append(np.full(len(V), gn.index(h), G0.dtype))
    SU.update(P=np.concatenate(Pn), N=np.concatenate(Nn), C=np.concatenate(Cn), G=np.concatenate(Gn))
JOINTS = ['Root', 'Hips', 'Spine', 'Chest', 'Neck', 'Head', 'UpperArm_L', 'Forearm_L', 'Hand_L', 'UpperArm_R', 'Forearm_R', 'Hand_R',
          'Thigh_L', 'Shin_L', 'Foot_L', 'Thigh_R', 'Shin_R', 'Foot_R']
PARENT = {'Root': None, 'Hips': 'Root', 'Spine': 'Hips', 'Chest': 'Spine', 'Neck': 'Chest', 'Head': 'Neck',
          'UpperArm_L': 'Chest', 'Forearm_L': 'UpperArm_L', 'Hand_L': 'Forearm_L', 'UpperArm_R': 'Chest', 'Forearm_R': 'UpperArm_R', 'Hand_R': 'Forearm_R',
          'Thigh_L': 'Hips', 'Shin_L': 'Thigh_L', 'Foot_L': 'Shin_L', 'Thigh_R': 'Hips', 'Shin_R': 'Thigh_R', 'Foot_R': 'Shin_R'}
JI = {n: i for i, n in enumerate(JOINTS)}
BIND = {n: JP[n].copy() for n in JOINTS}
def boff(n): return BIND[n] - (BIND[PARENT[n]] if PARENT[n] else 0)
SIDE = {'L': 1.0, 'R': -1.0}                     # +X = the crew member's left (they face +Z)
L_TH = {s: np.linalg.norm(BIND['Shin_' + s] - BIND['Thigh_' + s]) for s in 'LR'}
L_SH = {s: np.linalg.norm(BIND['Foot_' + s] - BIND['Shin_' + s]) for s in 'LR'}
L_UA = {s: np.linalg.norm(BIND['Forearm_' + s] - BIND['UpperArm_' + s]) for s in 'LR'}
L_FA = {s: np.linalg.norm(BIND['Hand_' + s] - BIND['Forearm_' + s]) for s in 'LR'}
ANK = BIND['Foot_L'][1]                          # ankle height above the sole (0.082)
TOE = np.array([0.0, -ANK, 0.20])                # ball of the foot, ankle-relative (foot space)
HIP_H = BIND['Hips'][1]

# ----------------------------------------------------------------------------- small math
def nrm(v): n = np.linalg.norm(v); return v / n if n > 1e-9 else v
def Rx(a): c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def Ry(a): c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def Rz(a): c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def yaw_of(d): return math.atan2(d[0], d[2])
def fwd(yaw): return np.array([math.sin(yaw), 0, math.cos(yaw)])
def left(yaw): return np.array([math.cos(yaw), 0, -math.sin(yaw)])
def angdiff(a, b): return (b - a + math.pi) % TAU - math.pi
def sstep(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def s5(x): x = min(max(x, 0.0), 1.0); return x * x * x * (x * (6 * x - 15) + 10)
def frame(a, n):
    a = nrm(a); n = nrm(n - a * (n @ a)); return np.stack([a, n, np.cross(a, n)], 1)
GRIP_RG = Rx(-1.0)
if os.environ.get('OLD_GLOVE') is None: _swap_gloves(SU)
# v3 (my suit copy): the trouser cuff ring sits inside the boot 3.1 cm above the sole; on a planted boot it came within 3 cm of the
# wing deck (AA2 'shins over the deck').  Pull the hidden Shin-group verts below CUFF_Y up to CUFF_Y (still inside the boot shell).
CUFF_Y = float(os.environ.get('CUFF_Y', 0.13))
for _h in ('Shin_L', 'Shin_R'):
    _m = SU['G'] == [str(x) for x in SU['gnames']].index(_h); _P = SU['P'].copy(); _P[_m, 1] = np.maximum(_P[_m, 1], CUFF_Y); SU['P'] = _P
def mat2q(M):
    t = np.trace(M)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2; w = 0.25 * s; x = (M[2, 1] - M[1, 2]) / s; y = (M[0, 2] - M[2, 0]) / s; z = (M[1, 0] - M[0, 1]) / s
    elif M[0, 0] > M[1, 1] and M[0, 0] > M[2, 2]:
        s = math.sqrt(1.0 + M[0, 0] - M[1, 1] - M[2, 2]) * 2; w = (M[2, 1] - M[1, 2]) / s; x = 0.25 * s; y = (M[0, 1] + M[1, 0]) / s; z = (M[0, 2] + M[2, 0]) / s
    elif M[1, 1] > M[2, 2]:
        s = math.sqrt(1.0 + M[1, 1] - M[0, 0] - M[2, 2]) * 2; w = (M[0, 2] - M[2, 0]) / s; x = (M[0, 1] + M[1, 0]) / s; y = 0.25 * s; z = (M[1, 2] + M[2, 1]) / s
    else:
        s = math.sqrt(1.0 + M[2, 2] - M[0, 0] - M[1, 1]) * 2; w = (M[1, 0] - M[0, 1]) / s; x = (M[0, 2] + M[2, 0]) / s; y = (M[1, 2] + M[2, 1]) / s; z = 0.25 * s
    q = np.array([x, y, z, w]); return q / np.linalg.norm(q)

def ik_bind(a, b, c, pole):
    u = nrm(c - a); v = nrm(pole - u * (pole @ u)); n = nrm(np.cross(u, v))
    return frame(b - a, n), frame(c - b, n)
IKB = {}
for s in 'LR':
    IKB['leg' + s] = ik_bind(BIND['Thigh_' + s], BIND['Shin_' + s], BIND['Foot_' + s], np.array([0, 0, 1.0]))
    e = BIND['Forearm_' + s]; sh = BIND['UpperArm_' + s]; hd = BIND['Hand_' + s]
    IKB['arm' + s] = ik_bind(sh, e, hd, e - (sh + hd) / 2)
STRETCH = {'max': 0.0}; CTX = {}
def ik2(A, T, l1, l2, pole, bind):
    d = T - A; L = np.linalg.norm(d); u = d / L
    Lmax = (l1 + l2) * 0.9995
    if L > Lmax:
        rr = L / (l1 + l2)
        if rr > STRETCH['max']: STRETCH['where'] = dict(CTX, A=[round(float(x), 2) for x in A], T=[round(float(x), 2) for x in T])
        STRETCH['max'] = max(STRETCH['max'], rr); L = Lmax
        if rr > 1.02: STRETCH['n'] = STRETCH.get('n', 0) + 1; STRETCH.setdefault('list', []).append((CTX.get('crew'), CTX.get('t'), CTX.get('limb'), round(rr, 3)))
    L = max(L, abs(l1 - l2) + 1e-3)
    v = nrm(pole - u * (pole @ u)); n = nrm(np.cross(u, v))
    ca = (l1 * l1 + L * L - l2 * l2) / (2 * l1 * L); sa = math.sqrt(max(0.0, 1 - ca * ca))
    K = A + l1 * (ca * u + sa * v); E = A + u * L
    R1 = frame(K - A, n) @ bind[0].T; R2 = frame(E - K, n) @ bind[1].T
    return R1, R2

# ----------------------------------------------------------------------------- paths
def chaikin(P, it=4):
    P = [np.asarray(p, float) for p in P]
    for _ in range(it):
        Q = [P[0]]
        for a, b in zip(P[:-1], P[1:]): Q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        Q.append(P[-1]); P = Q
    return np.array(P)
class Path:
    def __init__(self, pts, smooth=True):
        self.P = chaikin(pts) if smooth and len(pts) > 2 else np.array([np.asarray(p, float) for p in pts])
        seg = np.linalg.norm(np.diff(self.P[:, [0, 2]], axis=0), axis=1); self.s = np.concatenate([[0], np.cumsum(seg)]); self.L = self.s[-1]
    def at(self, s):
        s = min(max(s, 0.0), self.L); i = min(np.searchsorted(self.s, s, 'right') - 1, len(self.s) - 2)
        f = (s - self.s[i]) / max(1e-9, self.s[i + 1] - self.s[i]); return self.P[i] * (1 - f) + self.P[i + 1] * f
    def yaw(self, s, w=0.35):
        a = self.at(s - w); b = self.at(s + w)
        if np.linalg.norm((b - a)[[0, 2]]) < 1e-6: a = self.at(0); b = self.at(self.L)
        return yaw_of(b - a)

# ----------------------------------------------------------------------------- crew timeline model
WALK = dict(Ls=0.55, Tst=0.40, sw=0.80, lift=0.11, hip=-0.065)
class Crew:
    def __init__(self, k, name, pos, yaw):
        self.k = k; self.name = name; self.segs = []           # (t0, t1, kind, data)
        self.feet = {s: [] for s in 'LR'}                       # plants: dict(t0 lift, t1 land, pos ankle, yaw, kind, arc)
        self.init_plant = {s: (np.array(pos, float) + left(yaw) * 0.11 * SIDE[s] + np.array([0, ANK, 0]), yaw) for s in 'LR'}
        self.pos = np.array(pos, float); self.yaw = yaw; self.t = 0.0; self.events = {}
        self.look = []                                          # (t0, t1, target point or None)
    # ---- current feet (for continuing segments)
    def last_plant(self, s):
        return (self.feet[s][-1]['pos'], self.feet[s][-1]['yaw']) if self.feet[s] else self.init_plant[s]
    def idle(self, t1, look=None):
        if t1 > self.t: self.segs.append((self.t, t1, 'idle', dict(pos=self.pos.copy(), yaw=self.yaw, look=look))); self.t = t1
    def turn(self, yaw1, dur=0.75, look=None):
        d = angdiff(self.yaw, yaw1)
        if abs(d) < 0.12: return
        t0 = self.t; y0 = self.yaw; first = 'L' if d > 0 else 'R'; second = 'R' if first == 'L' else 'L'
        for i, s in enumerate((first, second)):
            a = t0 + i * dur * 0.45; b = a + dur * 0.5
            p = self.pos + left(yaw1) * 0.11 * SIDE[s] + np.array([0, ANK, 0])
            self.feet[s].append(dict(t0=a, t1=b, pos=p, yaw=yaw1, kind='turn', arc=np.array([0, 0.06, 0])))
        self.segs.append((t0, t0 + dur, 'turn', dict(pos=self.pos.copy(), y0=y0, y1=y0 + d, look=look)))
        self.yaw = yaw1; self.t = t0 + dur
    def walk(self, pts, look=None, Ls=None):
        pts = [self.pos] + [np.asarray(p, float) for p in pts]
        path = Path(pts); Ls0 = Ls or WALK['Ls']
        y1 = path.yaw(0.0, 0.5); self.turn(y1)
        N = max(1, int(math.ceil(path.L / Ls0))); Ls_ = path.L / N; Tst = WALK['Tst'] * (Ls_ / Ls0) ** 0.5; Tsw = WALK['sw'] * Tst
        t0 = self.t
        # who leads: the foot that is behind / or L
        order = ['L', 'R']
        st = [0.0] + [j * Ls_ for j in range(1, N + 1)] + [path.L]
        steps = []
        for j in range(1, N + 2):
            s = order[(j - 1) % 2]; a = t0 + (j - 1) * Tst; b = a + Tsw
            sj = st[j]; yj = path.yaw(sj) if j <= N else path.yaw(path.L, 0.6)
            if j == N + 1: yj = path.yaw(path.L - 0.3, 0.3)
            p = path.at(sj) + left(yj) * 0.11 * SIDE[s] + np.array([0, ANK, 0])
            self.feet[s].append(dict(t0=a, t1=b, pos=p, yaw=yj, kind='walk', arc=np.array([0, WALK['lift'], 0])))
            steps.append((a, b, s, sj))
        t1 = t0 + N * Tst + Tsw
        self.segs.append((t0, t1, 'walk', dict(path=path, steps=steps, Tst=Tst, Tsw=Tsw, look=look)))
        self.pos = path.at(path.L).copy(); self.yaw = steps[-1] and path.yaw(path.L - 0.3, 0.3); self.t = t1
        return t1
    def climb(self):
        """mount at STAND facing the ladder, hand-over-hand climb (RUNG_PAIR_S per 2 rungs), mantle onto the deck, walk into the hatch."""
        t0 = self.t; yawL = yaw_of(-LU)
        cyc = RUNG_PAIR_S; v = 1.2 / cyc
        mount = 0.9; ramp = 0.8
        yb0 = PAD_Y; ytop = YTOP                         # body (feet reference) height when the mantle starts
        # body height y_b(t): rest during the mount, accelerate over `ramp`, constant v, decelerate into ytop
        dist = ytop - yb0; tc = t0 + mount
        Tconst = (dist - v * ramp) / v                            # accel + decel each cover v*ramp/2
        t_end = tc + ramp + Tconst + ramp
        def yb(t):
            if t <= tc: return yb0
            x = t - tc
            if x < ramp: return yb0 + v * x * x / (2 * ramp)
            if x < ramp + Tconst: return yb0 + v * ramp / 2 + v * (x - ramp)
            if x < 2 * ramp + Tconst: u = x - ramp - Tconst; return yb0 + v * ramp / 2 + v * Tconst + v * (u - u * u / (2 * ramp))
            return ytop
        # limb moves, derived from the body trajectory so every grip lands at the same height relative to the body:
        # diagonal pairs (right hand + left foot, then left hand + right foot), each limb moves 2 rungs per cycle.
        # v3: the body sits 0.25 m behind the rungs (pack vs cage), so a bent knee would reach the rungs: the arms do the climbing
        # (2 rungs per reach) and the legs stay long, knees turned out inside the cage, boots tapping every other rung (toes on the rung top).
        W = {'hand': float(os.environ.get('W_HAND', 0.62)), 'foot': float(os.environ.get('W_FOOT', 0.92))}
        TOPREL = {'hand': float(os.environ.get('TR_HAND', 1.70)), 'foot': float(os.environ.get('TR_FOOT', 0.155))}   # wrist / ankle height above y_b when the grip lands
        OFF = {'hand': 0.03, 'foot': 0.025 + ANK + 0.001}
        PAR = {'hand_R': 0, 'foot_L': 0, 'hand_L': 1, 'foot_R': 1}
        tg = np.arange(t0, t_end + 2.0, 0.002); yg = np.array([yb(t) for t in tg])
        moves = {k: [] for k in PAR}
        for k, par in PAR.items():
            kind, sd_ = k.split('_'); w = W[kind] * cyc
            top = 34 if kind == 'foot' else 35
            pre = None
            for idx in range(par, top + 1, 2) if kind == 'foot' else list(range(par, 35, 2)):
                ry = (RUNG_Y[idx] if idx < 35 else DECK_Y + 0.02) + OFF[kind]
                need = ry - TOPREL[kind] - OFF[kind] + OFF[kind]
                need = (RUNG_Y[idx] if idx < 35 else DECK_Y + 0.02) - TOPREL[kind] + OFF[kind]
                if need <= yb0 + 1e-6:
                    pre = idx; continue
                if need > ytop + 1e-6: break
                bt = float(tg[np.searchsorted(yg, need)])
                moves[k].append([bt - w, bt, idx])
            if pre is not None and (kind == 'hand' or moves[k] == [] or True):
                # initial grip / first rung taken during the mount
                st = t0 + (0.15 if k == 'hand_R' else 0.35 if k == 'hand_L' else 0.55 if k == 'foot_L' else 0.75)
                moves[k].insert(0, [st, st + 0.45, pre])
            # top of the ladder: the decel ramp spreads the last move away from the previous one (limb left behind -> stretch);
            # pull the final move in to <= 0.55 cycle after the previous one ends (also keeps the hands alternating onto the stile tops)
            if kind == 'foot' and len(moves[k]) >= 2:
                pa, pb, _ = moves[k][-2]; a_, b_, i_ = moves[k][-1]
                if a_ > pb + 0.55 * cyc: moves[k][-1] = [pb + 0.55 * cyc, pb + 0.55 * cyc + (b_ - a_), i_]
            # keep moves of one limb sequential
            for i in range(1, len(moves[k])):
                if moves[k][i][0] < moves[k][i - 1][1] + 0.05:
                    moves[k][i][0] = moves[k][i - 1][1] + 0.05
                    moves[k][i][1] = max(moves[k][i][1], moves[k][i][0] + 0.3)
            if k == 'hand_L' and moves[k] and moves[k][-1][2] == 33:
                # v3: YTOP is low, so the left glove on rung 33 would be dragged off it (arm over-stretched): it joins the right one on rung 34
                bt = float(tg[np.searchsorted(yg, L34_Y)]); a_ = max(moves[k][-1][1] + 0.05, bt - 0.5)
                moves[k].append([a_, max(bt, a_ + 0.45), 34])
            moves[k] = [tuple(m) for m in moves[k]]
        def hand_frame(s, idx):   # glove frame (columns = glove x / y / z in the world); rungs: the root frame (wrap axis along the rung)
            if isinstance(idx, tuple) and idx[0] == 'rail':
                rs = -SIDE[s]; return np.column_stack([-rs * np.array([0, 1.0, 0]), -rs * LT, -LU])   # wrap axis vertical, opening outward
            return Ry(yawL)
        def limb_pos(kind, s, idx):
            if isinstance(idx, tuple) and idx[0] == 'rail':
                return lad(LAD_R, 0.28 * -SIDE[s], idx[1]) - hand_frame(s, idx) @ GRIP_C
            if not isinstance(idx, (int, np.integer)): return np.asarray(idx, float)
            sd = SIDE[s]
            # the crew member faces -LU, so their left (+X local) is -LT ... left(yawL)
            lt = left(yawL)
            if kind == 'foot':   # toes on the rung top: ball/toe (0.17-0.22 ahead of the ankle) over the 50 mm rung, sole 1 mm above it
                return lad(LAD_R, 0, 0) + lt * FOOT_T * sd + LU * FOOT_DU + np.array([0, RUNG_Y[idx] + OFF['foot'], 0])
            # glove wrap centred on the rung axis (GRIP_C in the grip frame): wrist sits behind and just above the rung
            return lad(LAD_R, 0, 0) + lt * HAND_T * sd + np.array([0, RUNG_Y[idx], 0]) - Ry(yawL) @ GRIP_C
        # v3 (AA2 gate: a boot within 3 cm of a rung must be still, i.e. set down / lifted at < 9 cm/s, which a 1.2 m/s climb
        # cannot give; and the 0.75 m cage leaves no room for a bent knee): the boots trail under the body, toes pointed down,
        # >= 3 cm behind the rungs, and the arms do the climbing.  foot_at() reads self.follow between the mount and the mantle.
        lt_ = left(yawL)
        def follow(s, t):
            if t >= t_end and getattr(self, 'mantle', None) is not None:
                y0_, r0_, tl0_ = kpw(self.mantle[0], t), kpw(self.mantle[1], t), kpw(self.mantle[2], t)
            else: y0_, r0_, tl0_ = yb(t), CLIMB_R, 0.0
            if t >= t_end: r0_ = r0_ + FOL_MU * sstep((t - t_end) / (1.0 * float(os.environ.get('MW_K', 0.6))))
            yh = y0_ + BIND['Hips'][1] - 0.03
            ph_ = math.sin(TAU * (t - tc) / cyc + (0.0 if s == 'L' else math.pi))
            Lf = FOL_L + FOL_A * ph_
            return lad(FOL_U + r0_ - CLIMB_R, tl0_, 0) + lt_ * FOL_T * SIDE[s] + LU * (FOL_K * ph_) + np.array([0, yh - Lf, 0])
        self.follow = dict(t0=t0 + FOL_T0, fn=follow, yaw=yawL, pitch=FOL_P, tb={})
        # ---------------------------------------------------------------- v3 mantle + walk-in (AA2 v3 gate)
        # Hands may only touch rungs / rails, so the climb ends low (y_b YTOP) with the gloves on rungs 33/34; they move up onto the
        # stiles (C wrap round the vertical rail, opening outward) and the climber presses up.  The lead boot leaves its trailing
        # pose, goes out through the cage side opening (between the stile and the side bar, above the top hoop), over the kerb and
        # is SET DOWN on the wing (last 3.5 cm at <= 2.6 mm / frame: AA2's 'still sole' rule); the body rises over the stile tops
        # and slides onto the wing, the trail boot follows the same way.  Walk-in: every wing boot is lifted the same slow way,
        # crosses the kerb >= 3 cm high and well clear of the jamb, and lands in the doorway (no surface within 3 cm there).
        S = self.side; lead = 'R' if S > 0 else 'L'; trail = 'L' if lead == 'R' else 'R'
        tm = t_end
        Tc_old = (20.45 - yb0 - v * ramp) / v; tin = tc + 2 * ramp + Tc_old + 6.17       # v2 'inside' time (per-crew PH i) kept
        Mt = tin - tm
        # v4 (Art & Animation option b): the top-of-ladder move is ~2 s shorter so the next climber (3.4 s / 4.08 m behind) never reaches
        # the upper climber's boots.  Authored v3 key times x (s after climb top) are warped: x <= MANT_STAND -> x * MW_K (absolute slow
        # set-down / lift durations stay as they are), then a MW_P pause on the wing and the walk-in stretched to end at the same tin.
        MW_K = float(os.environ.get('MW_K', 0.6)); MW_P = float(os.environ.get('MW_P', 0.5)); MW_S = float(os.environ.get('MW_S', 1.3))
        _xs = MANT_STAND * MW_K + MW_P
        def o(x):
            if x <= MANT_STAND: return tm + x * MW_K
            return tm + _xs + (x - MANT_STAND) * MW_S
        MS = MANT_STAND
        ow = lambda x: tm + MS + (x - 4.15) * (Mt - MS) / (6.46 - 4.15)        # walk-in keys stretched to end at tin
        STAND_Y = DECK_Y + ANK + SOLE_LIFT
        BODY_DECK = float(os.environ.get('BODY_DECK', 21.81))   # v4: knees soft on the wing so the trail boot (u 4.74, t 0.92) is reached without stretch
        Lp = lambda u_, t_, y_: lad(u_, S * t_, y_)
        # body keys (y_b, root u, root t)
        BK = [(o(0.0), YTOP, CLIMB_R, 0.0), (o(0.70), YTOP + 0.16, CLIMB_R, 0.0), (o(1.10), YTOP + 0.24, CLIMB_R, 0.0), (o(1.45), YTOP + 0.34, CLIMB_R, 0.0),
              (o(1.80), YTOP + 0.43, CLIMB_R, 0.01), (o(2.15), YTOP + 0.50, 4.69, 0.01), (o(2.60), MANT_Y, 4.68, 0.02), (o(3.60 + float(os.environ.get('BODY_DT', 0.0))), MANT_Y + 0.02, 4.67, 0.06),
              (o(4.00), 21.25, 4.62, 0.40), (o(4.45), 21.70, 4.56, 0.66), (o(MS), BODY_DECK, 4.54, 0.82),
              (o(5.50), 21.80, 4.46, 0.70), (o(5.88), 21.70, 4.30, 0.26), (o(6.12), 21.64, 4.05, 0.16), (o(6.32), 21.66, 3.75, 0.10),
              (o(6.46), 21.75, 3.42, 0.0), (tin, 21.75, 3.42, 0.0)]   # v4: walk-in at the authored pace, then wait in the doorway until tin
        MY = [(k[0], k[1]) for k in BK]; MR = [(k[0], k[2]) for k in BK]; MT = [(k[0], S * k[3]) for k in BK]
        MW = [(tm, yawL), (tin, yawL)]
        self.mantle = (MY, MR, MT, MW)
        # hands: rung -> stile, stile -> higher on the stile, then let go (slide off inward) as the body crosses to the wing
        hR = {lead: o(3.15), trail: o(3.30)}
        for s_, a_, b_, idx_ in [('L', o(0.0), o(0.40), ('rail', 21.30)), ('R', o(0.30), o(0.70), ('rail', 21.30)), ('L', o(0.75), o(1.10), ('rail', 21.55)),
                                 ('R', o(1.10), o(1.45), ('rail', 21.65)), ('L', o(1.45), o(1.80), ('rail', RAIL_TOPG)), ('R', o(1.80), o(2.15), ('rail', RAIL_TOPG)),
                                 (lead, hR[lead], o(3.55), ('free',)), (trail, hR[trail], o(3.70), ('free',))]:
            le_ = max([m[1] for m in moves['hand_' + s_]] + [-1e9])
            if le_ > a_ - 0.02:
                print('WARN shift', self.k, s_, round(a_ - tm, 3), 'last climb move ends', round(le_ - tm, 3)) if os.environ.get('DBGMV') else None
                d_ = le_ + 0.02 - a_; a_, b_ = a_ + d_, b_ + d_
            moves['hand_' + s_].append((a_, b_, idx_))
        for k_ in moves: moves[k_].sort(key=lambda m: m[0])
        # feet: PCHIP key paths (None = start from the trailing pose); 'slow' = the last / first 3.5 cm at <= 2.6 mm per frame
        DN = float(os.environ.get('DN', 0.034)); SL = float(os.environ.get('SL', 0.57))   # v3 gate: a sole within 3 cm of the deck must be still (< 3 mm per 1/30 s): 2.8 cm in 0.47 s = 2.0 mm per frame
        # set-downs: the last key sits 3.6 cm up (so the fast swing ends outside the 3 cm band), then 3.1 cm down in 0.70 s = 1.5 mm per frame
        DND = float(os.environ.get('DND', 0.033)); SLD = float(os.environ.get('SLD', 1.0))
        SL_L = float(os.environ.get('SL_L', 0.70)); DN_L = float(os.environ.get('DN_L', 0.034))   # lead lift: 2.7 cm in 0.56 s = 1.6 mm per frame
        SLD_T = float(os.environ.get('SLD_T', 1.0))   # trail set-down: 2.9 cm in 0.95 s = 1.0 mm per frame (10-bit rotation noise is up to ~2 mm per frame on the boot)
        def add_path(s_, keys, land=None, lift=None, tag=None, sld=None):
            sld = SLD if sld is None else sld
            self.feet[s_].append(dict(t0=keys[0][0], t1=keys[-1][0] + (sld if land is not None else 0.0), pos=(land if land is not None else keys[-1][1]),
                                      yaw=yawL, kind='path', arc=np.zeros(3), keys=keys, land=land, lift=lift))
            if land is not None and tag: self.deck_plants.append((s_, round(keys[-1][0] + sld, 3), land - np.array([0, ANK, 0]), tag))
        self.deck_plants = []
        LF = Lp(LF_U, LF_T, STAND_Y); TF = Lp(4.74, 0.92, STAND_Y)
        add_path(lead, [(o(2.20), None), (o(2.40), Lp(4.70, 0.24, 21.30)), (o(2.55), Lp(4.70, 0.43, 21.50)), (o(2.80), Lp(4.62, 0.52, 22.02)), (o(2.95), Lp(LF_U + 0.06, LF_T - 0.08, 22.06)),
                        (o(3.05), LF + np.array([0, DND, 0]))], land=LF, tag='mantle')
        TDT = float(os.environ.get('TR_DT', -0.15))   # v4: the trail boot leaves the shaft column earlier (crew vs crew: the next climber's head rises under it)
        add_path(trail, [(o(3.62 + TDT), None), (o(3.90 + TDT), Lp(4.74, 0.36, 21.97)), (o(4.04 + TDT), Lp(4.70, 0.66, 22.08)), (o(4.13 + TDT), TF + np.array([0, float(os.environ.get('DND_T', 0.032)), 0]))], land=TF, tag='mantle', sld=SLD_T)
        # walk-in
        D1 = Lp(3.93, 0.30, STAND_Y); D2 = Lp(3.66, 0.06, STAND_Y); D3 = Lp(3.40, -0.04, STAND_Y)   # v3: D1 u 3.98 -> 3.93 so the doorway sole box (ankle + 0.09) stays off the well edge (u 4.05)
        # v3: after the slow lift the boot rises clear of the kerb top (21.88) before it moves in over it
        add_path(trail, [(o(5.10), TF), (o(5.10) + SL, TF + np.array([0, DN, 0])), (o(5.10) + SL + 0.06, Lp(4.70, 0.88, STAND_Y + 0.10)), (o(5.74), Lp(4.44, 0.62, 22.04)), (o(5.88), D1)], lift=True)
        add_path(lead, [(o(5.52), LF), (o(5.52) + SL_L, LF + np.array([0, DN_L, 0])), (o(5.52) + SL_L + 0.05, LF + np.array([0, 0.10, 0]) - LT * 0.0), (o(6.14), Lp(4.34, 0.55, 22.06)), (o(6.21), Lp(4.26, 0.30, 22.02)), (o(6.32), D2)], lift=True)
        add_path(trail, [(o(6.33), D1), (o(6.40), Lp(3.70, 0.12, 22.00)), (o(6.45), D3)])
        for p_ in (D1, D2, D3): pass
        self.walk_in_plants = [(trail, o(5.88), D1), (lead, o(6.32), D2), (trail, o(6.45), D3)]
        for s_ in 'LR': self.follow['tb'][s_] = min([e['t0'] for e in self.feet[s_] if e['t0'] >= tm - 1e-6] + [1e9])
        tmd = o(MS); yin = yawL
        self.segs.append((t0, tin, 'climb', dict(yb=yb, yawL=yawL, moves=moves, limb_pos=limb_pos, hand_frame=hand_frame, tc=tc, t_end=t_end, tm=tm, tmd=tmd, o=o)))
        self.events.update(mount=t0, climb_start=tc, climb_top=t_end, on_deck=tmd, moves=moves)
        self.pos = lad(3.42, 0.0, DECK_Y); self.yaw = yin; self.t = tin
        self.events['inside'] = self.t
        self.segs.append((self.t, 1e9, 'hidden', dict(pos=self.pos.copy(), yaw=self.yaw)))
        self.t_hide = self.t

    # ------------------------------------------------------------------ evaluation
    def seg_at(self, t):
        for sg in self.segs:
            if sg[0] <= t < sg[1]: return sg
        return self.segs[-1] if t >= self.segs[-1][0] else self.segs[0]
    def foot_at(self, s, t):
        """ankle world position + foot yaw + pitch (+ = toe down)."""
        ev = self.feet[s]; prev = self.init_plant[s]; pk = None
        fo = getattr(self, 'follow', None)
        if fo is not None and t >= fo['t0']:
            tb = fo['tb'].get(s, 1e9)
            if t < tb:
                pf = fo['fn'](s, t); w = Tri(t, fo['t0'], fo['t0'] + FOL_BL)
                if w < 1:
                    p0, y0, pt0 = self._foot_ev(s, t)
                    return p0 * (1 - w) + pf * w, y0 + angdiff(y0, fo['yaw']) * w, pt0 * (1 - w) + fo['pitch'] * w
                return pf, fo['yaw'], fo['pitch']
        return self._foot_ev(s, t)
    def _path_at(self, s, e, t):
        ks = e['keys']; fo = self.follow
        if '_pc' not in e:
            P0 = ks[0][1] if ks[0][1] is not None else fo['fn'](s, ks[0][0])
            K = [(ks[0][0], np.asarray(P0, float))] + [(a, np.asarray(p, float)) for a, p in ks[1:]]
            e['_K'] = K; i0 = 1 if e.get('lift') else 0
            tt = [k[0] for k in K[i0:]]; pp = np.array([k[1] for k in K[i0:]])
            e['_pc'] = PchipInterpolator(tt, pp, axis=0) if len(tt) >= 3 else None
            e['_i0'] = i0
        K = e['_K']; i0 = e['_i0']; tl = K[-1][0]
        if e.get('lift') and t < K[1][0]:
            w = (t - K[0][0]) / (K[1][0] - K[0][0]); p = K[0][1] * (1 - w) + K[1][1] * w      # slow linear lift-off
        elif t >= tl:
            w = min(1.0, (t - tl) / (e['t1'] - tl)) if e['t1'] > tl else 1.0; p = K[-1][1] * (1 - w) + e['pos'] * w   # slow linear set-down
        elif e['_pc'] is not None: p = e['_pc'](t)
        else:
            a_, b_ = K[i0], K[-1]; w = s5((t - a_[0]) / (b_[0] - a_[0])); p = a_[1] * (1 - w) + b_[1] * w
        pitch = 0.0
        if ks[0][1] is None: pitch = fo['pitch'] * (1 - s5((t - K[0][0]) / (PATH_PF * (tl - K[0][0]))))
        return np.asarray(p, float), e['yaw'], pitch
    def _foot_ev(self, s, t):
        ev = self.feet[s]; prev = self.init_plant[s]; pk = None
        fo = getattr(self, 'follow', None)
        for e in ev:
            if t < e['t0']:
                # planted on prev; heel-rise before a walking lift-off (pivot on the toe)
                if e['kind'] == 'walk':
                    hr = 0.28 * Tri(t, e['t0'] - 0.16, e['t0'])
                    if hr > 0:
                        Rf = Ry(prev[1]); toe = prev[0] + Rf @ TOE
                        return toe + Rf @ Rx(hr) @ (-TOE), prev[1], hr
                return prev[0], prev[1], 0.0
            if t < e['t1'] and e.get('keys') is not None:
                return self._path_at(s, e, t)
            if t < e['t1']:
                u = (t - e['t0']) / (e['t1'] - e['t0'])
                p0 = prev[0]; y0 = prev[1]; pitch0 = 0.0; folp = False
                if fo is not None and e['t0'] >= fo['tb'].get(s, 1e9) - 1e-6 and fo['t0'] <= e['t0'] and e is next(x for x in ev if x['t0'] >= fo['tb'][s] - 1e-6):
                    p0 = fo['fn'](s, e['t0']); pitch0 = fo['pitch']; folp = True   # first move after the trailing window starts where the boot hangs
                if e['kind'] == 'walk':
                    pitch0 = 0.28; Rf = Ry(y0); toe = p0 + Rf @ TOE; p0 = toe + Rf @ Rx(0.28) @ (-TOE)
                h = sstep(u); p = p0 * (1 - h) + e['pos'] * h + e['arc'] * math.sin(math.pi * u) ** 1.2
                if e.get('rung'):   # v3 rung-to-rung: lift off the rung top, back away from the ladder, up, in over the target rung, set down
                    up_ = 0.035; dy = e['pos'][1] - p0[1]
                    y_ = p0[1] + up_ * sstep(u / 0.12) + dy * sstep((u - 0.08) / 0.74) - up_ * sstep((u - 0.86) / 0.14)
                    bk = FOOT_BACK * sstep((u - 0.08) / 0.16) * (1 - sstep((u - 0.66) / 0.18))
                    hh = sstep((u - 0.08) / 0.74); p = p0 * (1 - hh) + e['pos'] * hh + LU * bk; p[1] = y_
                if e.get('via') is not None:   # v3: quadratic Bezier through `via` at mid-swing (steers the boot round the kerb / door jambs)
                    cv = 2 * e['via'] - 0.5 * (p0 + e['pos']); p = p0 * (1 - h) ** 2 + cv * 2 * h * (1 - h) + e['pos'] * h * h
                yw = y0 + angdiff(y0, e['yaw']) * s5(u)
                if e['kind'] == 'walk': pitch = pitch0 * (1 - sstep(u * 2.2)) - 0.22 * math.sin(math.pi * min(1, max(0, (u - 0.35) / 0.65))) * 0.9
                elif e['kind'] == 'climb': pitch = 0.0 if e.get('rung') else -0.25 * math.sin(math.pi * u)
                else: pitch = 0.0
                if folp: pitch += pitch0 * (1 - s5(u))
                return p, yw, pitch
            prev = (e['pos'], e['yaw'])
        return prev[0], prev[1], 0.0

def kpw(K, t):   # smoothstep between (time, value) keys
    if t <= K[0][0]: return K[0][1]
    if t >= K[-1][0]: return K[-1][1]
    for (ta, va), (tb, vb) in zip(K[:-1], K[1:]):
        if t < tb: return va + (vb - va) * sstep((t - ta) / (tb - ta))
def Tri(t, a, b):   # 0 before a, ramps to 1 at b
    return 0.0 if t <= a else (1.0 if t >= b else sstep((t - a) / (b - a)))

# ----------------------------------------------------------------------------- the scene: who does what
CREW_NAMES = ['Cargo Manager', 'Crew 2', 'Crew 3', 'Crew 4']
CM_POS = (-7.55, 0.30, 7.45)
STARTS = [(CM_POS, yaw_of(np.array([-1, 0, 0.35]))),
          ((-10.25, 0.30, 9.05), yaw_of(np.array([0.2, 0, 1.0]))),
          ((-10.05, 0.30, 6.35), yaw_of(np.array([0.7, 0, -0.6]))),
          ((-9.05, 0.30, 10.35), yaw_of(np.array([-0.3, 0, -1.0])))]
crew = [Crew(i + 1, CREW_NAMES[i], p, y) for i, (p, y) in enumerate(STARTS)]
for i, c in enumerate(crew): c.side = SIDES[i]
T_CALL = 3.0
FILE_GAP = 1.55            # s between walkers in the file (~2.1 m)
CLIMB_GAP = opt('--climb-gap', 5.5)
MANTLE_S = opt('--mantle-scale', 1.0)
QUEUE_LEAD = opt('--queue-lead', 2.8)   # s before its mount that a queued climber starts walking to the ladder foot
# per-crew lead (crew 2,3,4): each arrives at the ladder foot just as its slot opens, so nobody stands under the boots of the climber above
QUEUE_LEADS = [None] + [float(x) for x in (sys.argv[sys.argv.index('--queue-leads') + 1].split(',') if '--queue-leads' in sys.argv else '1.85,2.4,2.85'.split(','))]
QUEUE = [None, lad(5.65, 0.75, PAD_Y), lad(6.55, -0.85, PAD_Y), lad(7.35, 0.35, PAD_Y)]
JOIN = [None, np.array((-6.35, 0.28, 6.85)), np.array((-6.9, 0.29, 7.6)), np.array((-6.6, 0.29, 7.9))]
look_cm = lambda: crew[0].pos + np.array([0, 1.6, 0])
# crew_call: CM radios (hand to the helmet), the others turn to her and acknowledge
cm = crew[0]
cm.idle(T_CALL)
for c in crew[1:]:
    c.idle(0.55)
    c.turn(yaw_of(np.array(CM_POS) - c.pos), dur=0.8)
    c.idle(T_CALL)
# crew_walk_to_pad: CM leads; the others fall in behind her (join points), single file along the shared route
cm.walk(SHARED[1:] + [lad(6.9, 0.0, PAD_Y), STAND])
for i, c in enumerate(crew[1:], 1):
    c.idle(T_CALL + FILE_GAP * i - 0.9)
    route = [JOIN[i]] + SHARED[1:] + [lad(6.9, 0.0, PAD_Y) if i != 3 else lad(7.6, 0.0, PAD_Y), QUEUE[i]]
    c.walk(route)
T_WALK_END = cm.t
# crew_climb: staggered climbs; queued crew step up to STAND when their slot comes
cm.idle(cm.t + opt('--cm-wait', 0.8))   # CM checks the ladder while the file closes up
cm.climb()
mount_t = [cm.events['mount']]
for i, c in enumerate(crew[1:], 1):
    tm = mount_t[-1] + CLIMB_GAP          # chained: a late arrival never shortens the next gap
    # face the ladder while waiting
    c.turn(yaw_of(STAND - c.pos), dur=max(0.25, 0.7 * abs(angdiff(c.yaw, yaw_of(STAND - c.pos))) / (math.pi / 2)))
    tw = tm - (QUEUE_LEADS[i] if '--queue-lead' not in sys.argv else QUEUE_LEAD)
    c.idle(max(c.t, tw))
    c.walk([STAND])
    c.turn(yaw_of(-LU), dur=0.6)
    if c.t > tm: print('WARN crew', c.k, 'late by', round(c.t - tm, 2))
    c.idle(max(c.t, tm))
    c.climb(); mount_t.append(c.events['mount'])
T_END = max(c.t_hide for c in crew) + 0.5
for c in crew:
    c.segs[-1] = (c.segs[-1][0], T_END + 1, 'hidden', c.segs[-1][3])

# ----------------------------------------------------------------------------- per-frame pose
def free_hands(c, t, R_chest, chest_pos, swing, tuck=0.0):
    """relaxed arms: hands at the hip sides, swinging fore/aft opposite to the legs. tuck 0..1 pulls them in to the thighs
    (walking in along the hull to the hatch, so no glove passes into the hull wall)."""
    out = {}
    for s in 'LR':
        sd = SIDE[s]; sh = chest_pos + R_chest @ (BIND['UpperArm_' + s] - BIND['Chest'])
        loc = np.array([sd * (0.075 - 0.09 * tuck), -0.50, 0.10 - 0.14 * tuck + swing * (-sd) * 0.17])
        loc[1] += 0.04 * abs(swing)
        out[s] = (sh + R_chest @ loc, R_chest @ np.array([sd * 0.55, -0.25, -1.0]))
    return out

def pose(c, t):
    sg = c.seg_at(t); kind = sg[2]; D = sg[3]
    hid = kind == 'hidden'
    if hid: t = sg[0]          # frozen once inside the hatch (constant tracks pack to almost nothing)
    # ---- root (ground point under the pelvis) and yaw
    look = None; swing = 0.0; hips_off = np.array([0, -0.012, 0.0]); lean = 0.04; twist = 0.0; roll = 0.0
    breathe = 0.012 * math.sin(TAU * t / 3.4 + c.k)
    if kind in ('idle', 'hidden'):
        pos, yaw = D['pos'], D['yaw']; look = D.get('look')
    elif kind == 'turn':
        u = s5((t - sg[0]) / (sg[1] - sg[0])); pos, yaw = D['pos'], D['y0'] + (D['y1'] - D['y0']) * u
    elif kind == 'walk':
        P = D['path']; Tst = D['Tst']; steps = D['steps']
        # body follows the centre of support (mean of the two feet along the path), smoothed by the gait
        ss = []
        for s in 'LR':
            sv = 0.0
            for (a, b, fs, sj) in steps:
                if fs != s: continue
                if t >= b: sv = sj
                elif t > a:
                    sv = sv + (sj - sv) * s5((t - a) / (b - a)); break
                else: break
            ss.append(sv)
        sb = (ss[0] + ss[1]) / 2
        pos = P.at(sb); yaw = P.yaw(sb)
        x = (t - sg[0]) / Tst; amp = Tri(t, sg[0], sg[0] + Tst * 1.2) * (1 - Tri(t, sg[1] - Tst * 1.2, sg[1]))
        hips_off = np.array([0.0, -0.012 + (WALK['hip'] + 0.012 + 0.016 * math.sin(math.pi * x) ** 2) * amp, 0.0])
        swing = math.sin(math.pi * x) * amp * (1 if int(x) % 2 == 0 else -1)
        swing = math.cos(math.pi * x - math.pi / 2) * amp
        twist = 0.10 * swing; lean = 0.04 + 0.06 * amp; roll = 0.025 * swing
    elif kind == 'climb':
        yawL = D['yawL']; yb = D['yb'](t)
        u = Tri(t, sg[0], sg[0] + 0.7)
        base = STAND * (1 - u) + lad(CLIMB_R, 0, 0) * u; base[1] = yb if t < D['tm'] else D['yb'](t)
        if t >= D['tm']:   # mantle
            MY, MR, MT, MW = c.mantle
            def pw(K, t):
                if t >= K[-1][0]: return K[-1][1]
                for (ta, va), (tb, vb) in zip(K[:-1], K[1:]):
                    if t < tb: return va + (vb - va) * sstep((t - ta) / (tb - ta))
            base = lad(pw(MR, t), pw(MT, t), 0); base[1] = pw(MY, t)
        pos, yaw = base, (pw(c.mantle[3], t) if t >= D['tm'] else yawL)
        mm = (t - D['tm']) / (D['tmd'] - D['tm']) if t >= D['tm'] else 0.0
        lean = 0.18 * math.sin(math.pi * min(1, mm * 1.25)) - 0.02 * Tri(mm, 0.6, 1.0); hips_off = np.array([0, -0.03 * u, 0.0])
    R_root = Ry(yaw)
    # head look target
    G = {}; Rg = {}
    Rg['Root'] = R_root; G['Root'] = pos
    R_h = R_root @ Ry(twist * -0.5) @ Rz(roll) @ Rx(lean * 0.5)
    G['Hips'] = pos + R_root @ (boff('Hips') + hips_off); Rg['Hips'] = R_h
    R_s = R_h @ Ry(twist * 0.6) @ Rx(lean * 0.3 + breathe * 0.3); G['Spine'] = G['Hips'] + R_h @ boff('Spine'); Rg['Spine'] = R_s
    R_c = R_s @ Ry(twist * 0.6) @ Rx(lean * 0.2 - breathe); G['Chest'] = G['Spine'] + R_s @ boff('Chest'); Rg['Chest'] = R_c
    G['Neck'] = G['Chest'] + R_c @ boff('Neck')
    # ---- hands
    GW = {'L': 0.0, 'R': 0.0}; GF = {}
    if kind == 'climb':
        H = {}
        FH = free_hands(c, t, R_c, G['Chest'], 0.0, Tri(t, D['o'](3.0), D['o'](4.0)) if t >= D['tm'] else 0.0)
        isfree = lambda i_: isinstance(i_, tuple) and i_[0] == 'free'
        israil = lambda i_: isinstance(i_, tuple) and i_[0] == 'rail'
        for s in 'LR':
            mv = D['moves']['hand_' + s]; lp = D['limb_pos']; hfr = D['hand_frame']
            free = FH[s][0]; rs = -SIDE[s]; IN = -LT * rs
            prev = None; prevG = None; prevI = None; p = None; Gc = None; gw = 0.0
            idx_c = None
            for (a, b, idx) in mv:
                idx_c = idx
                if isfree(idx): tgt, Gt = free, prevG
                else: tgt, Gt = lp('hand', s, idx), hfr(s, idx)
                if t < a:
                    if prev is None: p, Gc, gw = free, Gt, 0.0
                    else: p, Gc, gw = (free, prevG, 0.0) if isfree(prevI) else (prev, prevG, 1.0)
                    break
                if t < b:
                    src = prev if prev is not None else free
                    ur = (t - a) / (b - a); u = s5(ur); Gc = Gt; gw = 1.0
                    if prev is None:   # first reach from the relaxed pose: up and over, the wrap drops onto the rung from above
                        # v3: same path as rung-to-rung: rise to a point back from and above the rung (wrist turned on the way),
                        # come forward over the rung while still above it, then drop straight on
                        pre1 = tgt + LU * 0.09 + np.array([0, 0.06, 0]); pre2 = tgt + np.array([0, 0.06, 0])
                        if ur < 0.55: p = src + (pre1 - src) * sstep(ur / 0.55)
                        elif ur < 0.74: p = pre1 + (pre2 - pre1) * sstep((ur - 0.55) / 0.19)
                        else: p = pre2 + (tgt - pre2) * sstep((ur - 0.74) / 0.26)
                        gw = sstep(ur / 0.55)
                    elif isinstance(idx, (int, np.integer)):   # rung to rung: lift the wrap off, back, up, forward over the rung, drop on
                        up_ = 0.07; dy = tgt[1] - src[1]
                        hh = sstep((ur - 0.10) / 0.70); p = src * (1 - hh) + tgt * hh
                        p[1] = src[1] + up_ * sstep(ur / 0.14) + dy * hh - up_ * sstep((ur - 0.84) / 0.16)
                        p = p + LU * HAND_BACK * sstep((ur - 0.10) / 0.15) * (1 - sstep((ur - 0.64) / 0.20))
                    elif israil(idx) and not israil(prevI):   # rung -> stile: lift off the rung, turn the wrap, slide out onto the stile
                        lifted = src + np.array([0, 0.12, 0]); pre = tgt + IN * 0.10
                        if ur < 0.2: p = src + (lifted - src) * sstep(ur / 0.2)
                        elif ur < 0.75: p = lifted + (pre - lifted) * sstep((ur - 0.2) / 0.55)
                        else: p = pre + (tgt - pre) * sstep((ur - 0.75) / 0.25)
                        wq = sstep((ur - 0.22) / 0.5); Gc = prevG * (1 - wq) + Gt * wq
                    elif israil(idx):   # up the stile: slide in off it, up, back out onto it
                        off = src + IN * 0.10; pre = tgt + IN * 0.10
                        if ur < 0.25: p = src + (off - src) * sstep(ur / 0.25)
                        elif ur < 0.75: p = off + (pre - off) * sstep((ur - 0.25) / 0.5)
                        else: p = pre + (tgt - pre) * sstep((ur - 0.75) / 0.25)
                    elif isfree(idx):   # let go: slide in off the stile, then the relaxed (tucked) arm
                        off = src + IN * 0.10 + np.array([0, -0.03, 0]); Gc = prevG
                        bk = off + (LU * REL_BK if isinstance(prevI, tuple) and prevI[0] == 'rail' else 0.0)   # clear the stile in u before the wrist turns
                        if ur < 0.30: p = src + (off - src) * sstep(ur / 0.30)
                        elif ur < 0.55: p = off + (bk - off) * sstep((ur - 0.30) / 0.25)
                        else: p = bk + (free - bk) * sstep((ur - 0.55) / 0.45)
                        gw = 1.0 - sstep((ur - 0.55) / 0.35)
                    else:
                        p = src * (1 - u) + tgt * u
                    break
                prev, prevG, prevI = tgt, Gt, idx
            else:
                p, Gc, gw = (free, prevG, 0.0) if isfree(prevI) else (prev, prevG, 1.0)
            rw = 1.0 if (israil(prevI) or (p is not None and israil(idx_c))) else 0.0
            pole = R_root @ np.array([SIDE[s] * 0.55 * (ELAT_K * (1 - rw) + RAIL_EL * rw), -1.0, ELBOW_Z])     # v3: elbows down and back, inside the cage, off the rails
            fpole = R_c @ np.array([SIDE[s] * 0.55, -0.25, -1.0])
            H[s] = (p, nrm(fpole * (1 - gw) + pole * gw)); GW[s] = gw; GF[s] = Gc if Gc is not None else R_root
        curl = -0.15
    else:
        H = free_hands(c, t, R_c, G['Chest'], swing); curl = -0.15
    # call gestures
    if c.k == 1 and t < T_CALL + 0.4:
        g = Tri(t, 0.2, 0.8) * (1 - Tri(t, 2.3, 2.95))
        ear = G['Neck'] + R_c @ (HEADC - BIND['Neck'] + np.array([0.15, -0.02, 0.02]))
        H['L'] = (H['L'][0] * (1 - g) + ear * g + R_c @ np.array([0.2, 0, 0.2]) * math.sin(math.pi * g), nrm(H['L'][1] * (1 - g) + R_c @ np.array([1.0, -0.3, -0.2]) * g))
        pg = Tri(t, 1.35, 2.0) * (1 - Tri(t, 2.5, 3.1))     # right arm points toward the pad
        dirp = nrm(np.array([1.0, 0.0, -1.0])); dirp = nrm(dirp + np.array([0, 0.35, 0])); sh = G['Chest'] + R_c @ (BIND['UpperArm_R'] - BIND['Chest'])
        H['R'] = (H['R'][0] * (1 - pg) + (sh + dirp * 0.5) * pg + R_c @ np.array([-0.15, 0, 0.2]) * math.sin(math.pi * pg), nrm(H['R'][1] * (1 - pg) + np.array([0, -1.0, 0]) * pg))
    if c.k > 1 and t < T_CALL:
        g = Tri(t, 1.2 + 0.15 * c.k, 1.7 + 0.15 * c.k) * (1 - Tri(t, 2.45, 2.98))   # acknowledge: raise the right hand
        sh = G['Chest'] + R_c @ (BIND['UpperArm_R'] - BIND['Chest'])
        H['R'] = (H['R'][0] * (1 - g) + (sh + R_c @ np.array([-0.18, 0.42, 0.12])) * g + R_c @ np.array([-0.2, 0, 0.22]) * math.sin(math.pi * g), nrm(H['R'][1] * (1 - g) + R_c @ np.array([-1.0, -0.6, -0.2]) * g))
    # ---- head: look target
    if kind == 'climb': tgt = G['Neck'] + R_root @ np.array([0, 1.0, 0.6])
    elif t < T_CALL and c.k > 1: tgt = look_cm() if t > 0.4 else None
    elif kind == 'idle' and t > T_CALL and c.k > 1:   # queued: watch the ladder / the climber above
        tgt = lad(LAD_R, 0, 6.0)
    else: tgt = None
    if c.k == 1 and t < T_CALL: tgt = crew[1].pos * 0.5 + crew[2].pos * 0.5 + np.array([0, 1.6, 0])
    Rn = R_c
    if tgt is not None:
        d = np.linalg.inv(R_c) @ (tgt - G['Neck']); hy = max(-1.0, min(1.0, math.atan2(d[0], d[2]))); hp = max(-0.35, min(0.45, math.atan2(d[1] - 0.06, math.hypot(d[0], d[2]))))
        Rhd = R_c @ Ry(hy) @ Rx(-hp)
    else: Rhd = R_c @ Rx(-lean * 0.6)
    Rg['Neck'] = R_c @ np.linalg.inv(R_c) @ (Rhd if False else R_c)   # neck follows chest
    Rg['Neck'] = R_c @ ( (np.linalg.inv(R_c) @ Rhd) * 0 + np.eye(3))
    # split head rotation 35% neck / 65% head
    Rrel = np.linalg.inv(R_c) @ Rhd
    q = mat2q(Rrel); ang = 2 * math.acos(min(1, abs(q[3]))); ax = nrm(q[:3]) if ang > 1e-6 else np.array([1, 0, 0])
    if q[3] < 0: ax = -ax
    def axang(a, th):
        a = nrm(a); K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]]); return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K
    Rg['Neck'] = R_c @ axang(ax, ang * 0.35); G['Head'] = G['Neck'] + Rg['Neck'] @ boff('Head'); Rg['Head'] = Rhd
    # ---- legs (IK to ankle targets) + feet
    for s in 'LR':
        A = G['Hips'] + R_h @ boff('Thigh_' + s)
        ap, fy, fp = c.foot_at(s, t)
        Rf = Ry(fy) @ Rx(fp)
        knee_dir = Ry(fy) @ np.array([SIDE[s] * 0.12, 0, 1.0])
        if kind == 'climb':
            kc = np.array([SIDE[s] * KNEE_V[0], KNEE_V[1], KNEE_V[2]]); S_ = c.side; ld_ = s == ('R' if S_ > 0 else 'L'); MKs = MK if ld_ else MKT
            km = np.array([-S_ * MKs[0], MKs[1], MKs[2]]); kw = np.array([S_ * KW[0], 0.0, 1.0])
            if t >= D['tm']:
                oo = D['o']; TDT_ = float(os.environ.get('TR_DT', -0.15)); TW1_ = float(os.environ.get('TW1', -0.3)); w1 = Tri(t, oo(2.0), oo(2.4)) if ld_ else Tri(t, oo(3.9 + TDT_ + TW1_), oo(4.2 + TDT_ + TW1_)); w2 = Tri(t, oo(MANT_STAND - 0.2), oo(MANT_STAND + 0.3))
                w3 = Tri(t, oo(3.0), oo(3.4)) if ld_ else Tri(t, oo(4.5 + TDT_), oo(4.9 + TDT_))
                kc = kc * (1 - w1) + km * w1; kc = kc * (1 - w3) + np.array([0.0, 1.0, 0.0]) * w3; kc = kc * (1 - w2) + kw * w2
            knee_dir = R_root @ nrm(kc)   # v3: knees turned out inside the cage, never toward the rungs
        CTX.update(crew=c.k, t=round(t, 3), limb='leg' + s); R1, R2 = ik2(A, ap, L_TH[s], L_SH[s], knee_dir, IKB['leg' + s])
        G['Thigh_' + s] = A; Rg['Thigh_' + s] = R1; G['Shin_' + s] = A + R1 @ boff('Shin_' + s); Rg['Shin_' + s] = R2
        G['Foot_' + s] = G['Shin_' + s] + R2 @ boff('Foot_' + s); Rg['Foot_' + s] = Rf
        hp_, pole = H[s]
        Ash = G['Chest'] + R_c @ boff('UpperArm_' + s)
        CTX.update(crew=c.k, t=round(t, 3), limb='arm' + s); R1, R2 = ik2(Ash, hp_, L_UA[s], L_FA[s], pole, IKB['arm' + s])
        G['UpperArm_' + s] = Ash; Rg['UpperArm_' + s] = R1; G['Forearm_' + s] = Ash + R1 @ boff('Forearm_' + s); Rg['Forearm_' + s] = R2
        G['Hand_' + s] = G['Forearm_' + s] + R2 @ boff('Hand_' + s); Rg['Hand_' + s] = R2 @ Rx(curl)
        if GW[s] > 0:   # v3: on the ladder the glove holds the grip frame (wrap opening down) whatever the forearm does
            Mb = Rg['Hand_' + s] * (1 - GW[s]) + (GF[s] @ GRIP_RG) * GW[s]; U_, _, Vt_ = np.linalg.svd(Mb); Rg['Hand_' + s] = U_ @ Vt_
    # ---- local TRS
    out = {}
    for n in JOINTS:
        p = PARENT[n]
        if p is None: T_ = G[n] + R_root @ hips_off; Rl = Rg[n]     # hips offset folded into the root (Root's only child is Hips)
        else: Rl = Rg[p].T @ Rg[n]; T_ = boff(n)
        out[n] = (np.array(T_, float), mat2q(Rl))
    sc = 1e-4 if hid else 1.0
    return out, sc, G

# ----------------------------------------------------------------------------- bake
NF = int(math.ceil(T_END * FPS)) + 1
T_WALK_END = math.ceil(T_WALK_END * FPS) / FPS; T_END = math.ceil(T_END * FPS) / FPS
CLIPS = [('crew_call', 0.0, T_CALL), ('crew_walk_to_pad', T_CALL, T_WALK_END), ('crew_climb', T_WALK_END, T_END)]
frames = []
for f in range(NF):
    t = f / FPS; fr = []
    for c in crew: fr.append(pose(c, t))
    frames.append(fr)
# fix quaternion sign continuity
for ci in range(4):
    for n in JOINTS:
        prev = None
        for f in range(NF):
            T_, q = frames[f][ci][0][n]
            if prev is not None and q @ prev < 0: q = -q; frames[f][ci][0][n] = (T_, q)
            prev = q
# smooth head / neck (look-at switches) - nothing touches a contact there
def gsmooth(Q, sig):
    k = np.arange(-3 * sig, 3 * sig + 1); w = np.exp(-0.5 * (k / sig) ** 2); w /= w.sum()
    out = np.zeros_like(Q)
    for i in range(len(Q)):
        idx = np.clip(i + k, 0, len(Q) - 1); out[i] = (Q[idx] * w[:, None]).sum(0)
    return out / np.linalg.norm(out, axis=1, keepdims=True)
for ci in range(4):
    for n in ('Neck', 'Head'):
        Q = np.array([frames[f][ci][0][n][1] for f in range(NF)]); Q = gsmooth(Q, 5)
        for f in range(NF): frames[f][ci][0][n] = (frames[f][ci][0][n][0], Q[f])
# ---- checks: foot slide (planted ankles), hand slip while gripping, joint pops
def foot_world(ci, f, s): return frames[f][ci][2]['Foot_' + s]
chk = {'ik_max_stretch': round(STRETCH['max'], 4), 'ik_stretch_at': STRETCH.get('where'), 'ik_evals_over_1.02': STRETCH.get('n', 0)}
slide = 0.0; step = 0.0
for ci in range(4):
    for s in 'LR':
        for f in range(1, NF):
            a = foot_world(ci, f - 1, s); b = foot_world(ci, f, s)
            if np.allclose(b, a, atol=1e-9): continue
    # planted = target unchanged over 2 frames -> IK foot must not move
    for f in range(1, NF):
        t = f / FPS; c = crew[ci]
        for s in 'LR':
            p0 = c.foot_at(s, t - 1 / FPS)[0]; p1 = c.foot_at(s, t)[0]
            if np.linalg.norm(p1 - p0) < 1e-9 and frames[f][ci][1] > 0.5 and frames[f - 1][ci][1] > 0.5:   # visible frames only
                sl_ = np.linalg.norm(foot_world(ci, f, s) - foot_world(ci, f - 1, s))
                if sl_ > slide: slide = sl_; chk['planted_foot_slide_at'] = dict(crew=ci + 1, foot=s, t=round(t, 3))
                if sl_ > 0.005: chk.setdefault('source_slides_over_5mm', []).append((ci + 1, s, round(t, 3), round(float(sl_), 4)))
        if frames[f][ci][1] > 0.5 and frames[f - 1][ci][1] > 0.5:
            step = max(step, max(np.linalg.norm(frames[f][ci][2][n] - frames[f - 1][ci][2][n]) for n in JOINTS if n not in ('Root',)))
chk['planted_foot_slide_max_m'] = round(float(slide), 5); chk['max_joint_step_per_frame_m'] = round(float(step), 3)
# climber separation: min vertical gap between consecutive climbers (upper boots vs lower gloves) while both are on the ladder
gap = 1e9; GAPAT = [0, 0, 0]
for f in range(NF):
    t = f / FPS; on = []
    for c in crew:
        sg = c.seg_at(t)
        if sg[2] == 'climb' and t > c.events['climb_start']: on.append(c)
    on_idx = [crew.index(c) for c in on]
    for i in on_idx:
        for j in on_idx:
            if i < j:
                Gi = frames[f][i][2]; Gj = frames[f][j][2]
                low_i = min(Gi['Foot_L'][1], Gi['Foot_R'][1]) - ANK; top_j = max(Gj['Hand_L'][1], Gj['Hand_R'][1], Gj['Head'][1] + 0.25)
                if low_i - top_j < gap: gap = low_i - top_j; GAPAT[:] = [t, i + 1, j + 1]
chk['min_gap_upper_boots_to_lower_gloves_m'] = round(float(gap), 3); chk['min_gap_at'] = [round(GAPAT[0], 2), GAPAT[1], GAPAT[2]]
print('CHECKS', chk); print('STRETCHLIST', STRETCH.get('list', [])[:400])

# ----------------------------------------------------------------------------- mesh -> vertices (one shared mesh, 1 material)
def lin(hx):
    h = hx.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return np.array([x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c])
PAL = [lin('#eef1f6'), lin('#2b3039'), lin('#4a4f58'), lin('#f0a22a'), lin('#29c3f2'), lin('#8ff6ff')]
P = SU['P'].astype(float); N = SU['N'].astype(float); C = SU['C']; Gi = SU['G']; gnames = [str(x) for x in SU['gnames']]
key = np.concatenate([np.round(P * 2000), np.round(N * 64), C[:, None]], 1)
uk, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
nv = len(uk); VP = np.zeros((nv, 3)); VN = np.zeros((nv, 3)); VC = np.zeros(nv, int); VG = np.zeros(nv, int)
VP[inv] = P; VN[inv] = N; VC[inv] = C; VG[inv] = Gi
VN = VN / np.linalg.norm(VN, axis=1, keepdims=True)
IDX = inv.astype(np.uint32)
# vertex colours: material palette + light weathering (dust rising toward the boots, mottling, darker undersides)
h = np.sin(VP @ np.array([12.9898, 78.233, 37.719]) * 43758.5453) * 0.5 + 0.5
mott = 0.93 + 0.07 * np.sin(VP[:, 0] * 23.0 + VP[:, 1] * 17.0) * np.cos(VP[:, 2] * 19.0 + VP[:, 1] * 11.0)
col = np.array([PAL[c] for c in VC])
dusty = np.isin(VC, [0, 1, 2, 4])
dust = np.clip((0.55 - VP[:, 1]) / 0.5, 0, 1) ** 1.4 * 0.5 + 0.08 * (h > 0.82)
dc = lin('#9b968d')
col[dusty] = col[dusty] * (1 - dust[dusty, None]) + dc * dust[dusty, None]
col[dusty] *= (mott[dusty] * (0.9 + 0.1 * np.clip(VN[dusty, 1] + 0.6, 0, 1)))[:, None]
VCOL = np.clip(col, 0, 1)
# skin: rigid per group, torso undersuit blended hips / spine / chest by height
JW = np.zeros((nv, 4), np.uint8); WW = np.zeros((nv, 4), np.float32)
for gi, g in enumerate(gnames):
    sel = VG == gi
    if g == 'TorsoBlend':
        y = VP[sel, 1]; a = np.clip((y - 0.99) / 0.12, 0, 1); a = a * a * (3 - 2 * a); cc = np.clip((y - 1.13) / 0.14, 0, 1); cc = cc * cc * (3 - 2 * cc)
        JW[sel] = [JI['Hips'], JI['Spine'], JI['Chest'], 0]
        WW[sel, 0] = (1 - cc) * (1 - a); WW[sel, 1] = (1 - cc) * a; WW[sel, 2] = cc
    else:
        JW[sel, 0] = JI[g]; WW[sel, 0] = 1.0

# ---- optional fast pose dump (iteration only; the shipped checks re-skin the packed GLB in three r186 with dump_poses.mjs / dp.mjs):
#   FASTDUMP=prefix,T0,T1 writes the same prefix.json / prefix_pos.bin layout, skinned here in numpy from the 30 fps source frames
if os.environ.get('FASTDUMP'):
    _pre, _a, _b = os.environ['FASTDUMP'].split(','); _a, _b = float(_a), float(_b)
    def _q2m(q):
        x, y, z, w = q; return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    _fs = [f for f in range(NF) if _a - 1e-6 <= f / FPS <= _b + 1e-6]
    _pos = np.zeros((len(_fs), 4, nv, 3), np.float32); _vis = []
    _vj = [JOINTS[JW[i, int(np.argmax(WW[i]))]] for i in range(nv)]
    for _i, f in enumerate(_fs):
        _v = []
        for ci in range(4):
            out, sc, _G = frames[f][ci]; Mg = {}
            for n in JOINTS:
                T_, q = out[n]; R = _q2m(q); pa = PARENT[n]
                if pa is None: Mg[n] = (R * sc, np.asarray(T_, float))
                else: Rp, tp = Mg[pa]; Mg[n] = (Rp @ R, tp + Rp @ np.asarray(T_, float))
            X = np.zeros((nv, 3))
            for c_ in range(4):
                w = WW[:, c_]; m = w > 0
                if not m.any(): continue
                for ji in np.unique(JW[m, c_]):
                    mm = m & (JW[:, c_] == ji); R, tt = Mg[JOINTS[ji]]
                    X[mm] += w[mm, None] * ((VP[mm] - BIND[JOINTS[ji]]) @ R.T + tt)
            _pos[_i, ci] = X; _v.append(1 if sc > 0.01 else 0)
        _vis.append(_v)
    _pos.tofile(_pre + '_pos.bin')
    json.dump({'vjoint': _vj, 'times': [round(f / FPS, 4) for f in _fs], 'nverts': int(nv), 'visible': _vis}, open(_pre + '.json', 'w'))
    print('FASTDUMP', _pre, len(_fs), 'frames')
    for c in crew: print('EV', c.i if hasattr(c, 'i') else '', 'tm %.3f on_deck %.3f inside %.3f side %d' % (c.events['climb_top'], c.events['on_deck'], c.events['inside'], c.side))
    if os.environ.get('FASTONLY'): sys.exit(0)

# ----------------------------------------------------------------------------- GLB writer
buf = bytearray(); views = []; accs = []
def add(arr, ctype, typ, target=None, minmax=False):
    arr = np.ascontiguousarray(arr)
    while len(buf) % 4: buf.append(0)
    bv = {'buffer': 0, 'byteOffset': len(buf), 'byteLength': arr.nbytes}
    if target: bv['target'] = target
    buf.extend(arr.tobytes()); views.append(bv)
    a = {'bufferView': len(views) - 1, 'componentType': ctype, 'count': int(arr.shape[0]), 'type': typ}
    if minmax:
        a['min'] = [float(x) for x in np.atleast_1d(arr.min(0))]; a['max'] = [float(x) for x in np.atleast_1d(arr.max(0))]
    accs.append(a); return len(accs) - 1
aP = add(VP.astype(np.float32), 5126, 'VEC3', 34962, True); aN = add(VN.astype(np.float32), 5126, 'VEC3', 34962)
aC = add(VCOL.astype(np.float32), 5126, 'VEC3', 34962); aJ = add(JW, 5121, 'VEC4', 34962); aW = add(WW, 5126, 'VEC4', 34962)
aI = add(IDX, 5125, 'SCALAR', 34963)
ibm = np.stack([np.linalg.inv(np.block([[np.eye(3), BIND[n][:, None]], [np.zeros((1, 3)), np.ones((1, 1))]])).T for n in JOINTS]).astype(np.float32)
aIBM = add(ibm.reshape(-1, 16), 5126, 'MAT4')
nodes = []; skins = []; scene_nodes = []
timing = {'fps': FPS, 'rung_pair_s': RUNG_PAIR_S, 'climb_gap_s': CLIMB_GAP, 'clips': {n: [round(a, 3), round(b, 3)] for n, a, b in CLIPS}, 'crew': []}
rootn = {'name': 'CrewBoarding', 'children': [], 'extras': {}}
nodes.append(rootn)
for ci, c in enumerate(crew):
    base = len(nodes); jidx = {}
    for n in JOINTS:
        jidx[n] = len(nodes)
        T_, q = frames[0][ci][0][n]
        nodes.append({'name': 'C%d_%s' % (c.k, n), 'translation': [float(x) for x in T_], 'rotation': [float(x) for x in q]})
    for n in JOINTS:
        kids = [jidx[m] for m in JOINTS if PARENT[m] == n]
        if kids: nodes[jidx[n]]['children'] = kids
    skins.append({'name': 'Crew_%d_Skin' % c.k, 'joints': [jidx[n] for n in JOINTS], 'inverseBindMatrices': aIBM, 'skeleton': jidx['Root']})
    mn = len(nodes); nodes.append({'name': 'Crew_%d_Mesh' % c.k, 'mesh': ci, 'skin': ci})
    grp = len(nodes); nodes.append({'name': 'Crew_%d' % c.k, 'children': [jidx['Root'], mn],
                                    'extras': {'role': c.name, 'note': 'Crew_%d_Mesh is skinned to C%d_* joints; C%d_Root carries root motion in pad-local glTF' % (c.k, c.k, c.k)}})
    rootn['children'].append(grp)
    ev = c.events
    def r3(x): return round(float(x), 2)
    walk_segs = [s for s in c.segs if s[2] == 'walk']
    first_walk = next(s for s in walk_segs if s[0] >= T_CALL - 1)
    rung = {}
    for k, mv in ev['moves'].items():
        rung[k] = [[r3(a), r3(b), (int(i) if isinstance(i, (int, np.integer)) else (('rail_z_%.2f' % i[1]) if isinstance(i, tuple) and i[0] == 'rail' else ('release' if isinstance(i, tuple) else ('ladder_rail_top' if np.asarray(i)[1] < 22.0 else 'hatch_frame'))))] for a, b, i in mv]
    def utz(p_): q = np.asarray(p_, float) - SHIP_C; return [round(float(q @ LU), 3), round(float(q @ LT), 3), round(float(q[1]), 3)]
    mantle = {'side': '+t' if c.side > 0 else '-t', 'lead_foot': 'Foot_R' if c.side > 0 else 'Foot_L', 'mantle_start_climb_top': r3(ev['climb_top']),
              'hands_released': r3(ev['on_deck']), 'walk_in_end_inside_hatch': r3(ev['inside']),
              'deck_foot_plants': [{'foot': 'Foot_' + s_, 'land_t': r3(t_), 'sole_center_utz': utz(p_), 'phase': ph_} for s_, t_, p_, ph_ in sorted(c.deck_plants, key=lambda x: x[1])]}
    timing['crew'].append({'crew': c.k, 'role': c.name, 'node': 'Crew_%d' % c.k,
        'call': [0.0, T_CALL], 'walk_start': r3(first_walk[0]), 'arrive_ladder_or_queue': r3(first_walk[1]),
        'mount': r3(ev['mount']), 'climb_start': r3(ev['climb_start']), 'climb_top': r3(ev['climb_top']), 'on_deck': r3(ev['on_deck']), 'inside_hatch': r3(ev['inside']),
        'mantle': mantle, 'rung_moves': rung})
rootn['extras'] = {'clips': timing['clips'], 'note': 'pad-local glTF: put this root at the Launch Pad root. Clips play back to back: crew_call -> crew_walk_to_pad -> crew_climb. Crew_k root scale drops to 1e-4 once inside the hatch (hide the node then).',
                   'inside_hatch_s': {('Crew_%d' % t['crew']): t['inside_hatch'] for t in timing['crew']}}
# ---- adaptive shared key times (--key-tol metres): from each key, extend the next key as far as possible (<= KEY_MAXGAP frames) while
# every skipped 30 fps frame, rebuilt the way three.js plays it (slerp rotations, lerp translation), stays within KEY_TOL of the
# authored pose on a sample of skinned vertices of every visible crew member.  Contact-critical frames therefore get dense keys.
KEY_TOL = opt('--key-tol', 0.0); KEY_MAXGAP = int(opt('--key-maxgap', 4)); KEY_LOOSE = opt('--key-loose', 0.04); KEY_CLIPS = opt('--key-clips', 'crew_climb').split(',')
def _q2m_(q):
    x, y, z, w = q; return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
def _slerp(q0, q1, u):
    d = float(q0 @ q1)
    if d < 0: q1, d = -q1, -d
    if d > 0.9995: q = q0 + (q1 - q0) * u; return q / np.linalg.norm(q)
    th = np.arccos(min(d, 1.0)); return (np.sin((1 - u) * th) * q0 + np.sin(u * th) * q1) / np.sin(th)
_KS = np.arange(len(VP))
_KPTS = opt('--key-pts', '')
if KEY_TOL > 0 and _KPTS:
    from scipy.spatial import cKDTree
    _KTREE = cKDTree(np.fromfile(_KPTS, np.float32).reshape(-1, 3).astype(float))
_FOOTV = np.array([JOINTS[JW[i, int(np.argmax(WW[i]))]].startswith('Foot') for i in range(len(VP))]); KEY_TOL_FOOT = opt('--key-tol-foot', 0.0003)   # dense keys on a boot near the deck (lifts need them)
def _utz(X):
    Y = X - np.array([0.0, 0.0, -13.0]); return np.stack([Y @ LU, Y @ LT, Y[:, 1]], 1)
_ALW = {}
def _allow(f, ci):   # per-vertex allowed interpolation error: tight near the ship, loose in open air
    k = (f, ci)
    if k not in _ALW:
        if not _KPTS: _ALW[k] = KEY_TOL
        else:
            d, _ = _KTREE.query(_utz(_skin_f(f, ci)), distance_upper_bound=0.2); d = np.minimum(d, 0.2)
            # v4 (crew vs crew gate, 3 cm): another visible crew member counts as a surface too
            Xc = _skin_f(f, ci); lo_, hi_ = Xc.min(0) - 0.2, Xc.max(0) + 0.2
            for cj in range(4):
                if cj == ci or frames[f][cj][1] < 0.01 or frames[f][ci][1] < 0.01: continue
                Xo = _skin_f(f, cj)
                if ((Xo.max(0) < lo_) | (Xo.min(0) > hi_)).any(): continue
                d = np.minimum(d, np.minimum(cKDTree(Xo).query(Xc, distance_upper_bound=0.2)[0], 0.2))
            a_ = np.clip(0.6 * (d - 0.04), KEY_TOL, KEY_LOOSE)
            Z = _utz(_skin_f(f, ci)); near_deck = _FOOTV & (np.abs(Z[:, 2] - DECK_Y) < 0.045) & (np.abs(Z[:, 1]) > 0.55)
            a_ = np.where(near_deck, KEY_TOL_FOOT, a_); _ALW[k] = a_
    return _ALW[k]
def _skin(out, sc):
    Mg = {}
    for n in JOINTS:
        T_, q = out[n]; R = _q2m_(q); pa = PARENT[n]
        if pa is None: Mg[n] = (R * sc, np.asarray(T_, float))
        else: Rp, tp = Mg[pa]; Mg[n] = (Rp @ R, tp + Rp @ np.asarray(T_, float))
    X = np.zeros((len(_KS), 3)); vp = VP[_KS]
    for c_ in range(4):
        w = WW[_KS, c_]; jw = JW[_KS, c_]
        for ji in np.unique(jw[w > 0]):
            mm = (w > 0) & (jw == ji); R, tt = Mg[JOINTS[ji]]; X[mm] += w[mm, None] * ((vp[mm] - BIND[JOINTS[ji]]) @ R.T + tt)
    return X
_SKC = {}
def _skin_f(f, ci):
    k = (f, ci)
    if k not in _SKC: _SKC[k] = _skin(frames[f][ci][0], frames[f][ci][1])
    return _SKC[k]
# ---- v4: two key groups per crew per clip, each with its own key-time input: LEGS (Root incl. translation / hide scale, Hips, Thigh /
# Shin / Foot) and UPPER (Spine .. Head, arms).  Per-vertex tolerances: a PLANTED boot (foot target unchanged) is locked to PLANT_TOL,
# a boot in the walk to FOOT_WALK_TOL, everything else in the call / walk clips to WALK_TOL (upper body may skip up to UP_MAXGAP_WALK
# frames), and near the ship the v3 pad-distance tolerance (_allow) applies.  The UPPER keys are chosen against the LEGS curve as it
# will be played back (interpolated on the LEGS keys), so their error is the full skinned error.  Identical / near-identical poses
# simply merge into one long segment (the error test passes), which drops near-duplicate keys.
LEG_J = ['Root', 'Hips', 'Thigh_L', 'Shin_L', 'Foot_L', 'Thigh_R', 'Shin_R', 'Foot_R']; UP_J = [n for n in JOINTS if n not in LEG_J]
_VDOM = np.array([JOINTS[JW[i, int(np.argmax(WW[i]))]] for i in range(len(VP))])
_GV = {'legs': np.where(np.isin(_VDOM, LEG_J))[0], 'upper': np.where(~np.isin(_VDOM, LEG_J))[0]}
PLANT_TOL = opt('--plant-tol', 0.005); FOOT_WALK_TOL = opt('--foot-walk-tol', 0.06); WALK_TOL = opt('--walk-tol', 0.06); UP_WALK_TOL = opt('--up-walk-tol', 0.04); HIP_K = opt('--hip-k', 0.0)
LEG_MAXGAP = opt('--leg-maxgap', 10); LEG_MAXGAP_CLIMB = opt('--leg-maxgap-climb', 6); UP_MAXGAP_WALK = opt('--up-maxgap-walk', 16); UP_MAXGAP_CLIMB = opt('--up-maxgap-climb', 4)
_PLF = {}
def _planted(f, ci, s):
    k = (f, ci, s)
    if k not in _PLF:
        c = crew[ci]; t = f / FPS; p = c.foot_at(s, t)[0]
        _PLF[k] = (f > 0 and np.linalg.norm(p - c.foot_at(s, t - 1 / FPS)[0]) < 1e-9) or (f < NF - 1 and np.linalg.norm(p - c.foot_at(s, t + 1 / FPS)[0]) < 1e-9)
    return _PLF[k]
_GTOL = {}
def _gtol(f, ci, g, walkish):
    k = (f, ci, g, walkish)
    if k not in _GTOL:
        idx = _GV[g]; a_ = np.asarray(_allow(f, ci), float)
        a_ = (np.full(len(VP), a_) if a_.ndim == 0 else a_.copy())[idx]
        if walkish: a_ = np.minimum(a_, WALK_TOL if g == 'legs' else UP_WALK_TOL)
        if g == 'legs':
            if walkish and HIP_K > 0:   # the upper body hangs on Root / Hips: pelvis vertices carry the upper-body tolerance
                m_ = np.isin(_VDOM[idx], ['Root', 'Hips']); a_[m_] = np.minimum(a_[m_], UP_WALK_TOL * HIP_K)
            for s_ in 'LR':
                m_ = _VDOM[idx] == 'Foot_' + s_
                a_[m_] = np.minimum(a_[m_], PLANT_TOL if _planted(f, ci, s_) else (FOOT_WALK_TOL if walkish else np.inf))
        _GTOL[k] = a_
    return _GTOL[k]
def _skin_sub(out, sc, idx):
    Mg = {}
    for n in JOINTS:
        T_, q = out[n]; R = _q2m_(q); pa = PARENT[n]
        if pa is None: Mg[n] = (R * sc, np.asarray(T_, float))
        else: Rp, tp = Mg[pa]; Mg[n] = (Rp @ R, tp + Rp @ np.asarray(T_, float))
    X = np.zeros((len(idx), 3)); vp = VP[idx]
    for c_ in range(4):
        w = WW[idx, c_]; jw = JW[idx, c_]
        for ji in np.unique(jw[w > 0]):
            mm = (w > 0) & (jw == ji); R, tt = Mg[JOINTS[ji]]; X[mm] += w[mm, None] * ((vp[mm] - BIND[JOINTS[ji]]) @ R.T + tt)
    return X
def _interp(ci, f, keys, names, out):   # joints `names` as three.js plays them between the surrounding keys
    j = max(0, min(np.searchsorted(keys, f, 'right') - 1, len(keys) - 2)); a, b = keys[j], keys[j + 1]; u = (f - a) / (b - a) if b > a else 0.0
    for n in names:
        Ta, qa = frames[a][ci][0][n]; Tb, qb = frames[b][ci][0][n]
        out[n] = (np.asarray(Ta, float) * (1 - u) + np.asarray(Tb, float) * u, _slerp(np.asarray(qa, float), np.asarray(qb, float), u))
    return (frames[a][ci][1] if u < 1 else frames[b][ci][1]) if 'Root' in names else None
_EX = {}
def _exact_sub(f, ci, idx_key):
    k = (f, ci, idx_key)
    if k not in _EX: _EX[k] = _skin_sub(frames[f][ci][0], frames[f][ci][1], _GV[idx_key])
    return _EX[k]
def _seg_ok_g(a, b, ci, g, walkish, leg_keys=None):
    if frames[a][ci][1] < 0.01 and frames[b][ci][1] < 0.01: return True
    names = LEG_J if g == 'legs' else UP_J; idx = _GV[g]
    for f in range(a + 1, b):
        u = (f - a) / (b - a); out = {n: frames[f][ci][0][n] for n in JOINTS}
        for n in names:
            Ta, qa = frames[a][ci][0][n]; Tb, qb = frames[b][ci][0][n]
            out[n] = (np.asarray(Ta, float) * (1 - u) + np.asarray(Tb, float) * u, _slerp(np.asarray(qa, float), np.asarray(qb, float), u))
        sc = frames[a][ci][1] if u < 1 else frames[b][ci][1]
        if g == 'upper' and leg_keys is not None: sc = _interp(ci, f, leg_keys, LEG_J, out)
        if sc < 0.01: continue
        if (np.linalg.norm(_skin_sub(out, sc, idx) - _exact_sub(f, ci, g), axis=1) > _gtol(f, ci, g, walkish)).any(): return False
    return True
def adaptive_keys_g(f0, f1, ci, g, maxgap, walkish, leg_keys=None):
    ks = [f0]; a = f0
    vis = lambda f: frames[f][ci][1] > 0.01
    while a < f1:
        b = min(a + 1, f1)
        for gg in range(2, maxgap + 1):
            if a + gg > f1 or any(vis(a + k) != vis(a) for k in range(1, gg)) or not _seg_ok_g(a, a + gg, ci, g, walkish, leg_keys): break
            b = a + gg
        ks.append(b); a = b
    return ks
# animations: one shared uniform time input per clip; the rate per clip is chosen by how fast the motion is
# (pack with gltfpack -af 0 so these keys are kept as authored). Every node keeps a track in every clip.
CLIP_STEP = {'crew_call': opt('--call-step', 2), 'crew_walk_to_pad': opt('--walk-step', 2), 'crew_climb': opt('--climb-step', 3)}   # in 30 fps frames
anims = []; nkeys = 0; DENSE = {}; LSQ_ON = '--no-lsq' not in ARGS
for name, a, b in CLIPS:
    f0 = int(round(a * FPS)); f1 = int(round(b * FPS)); fr = list(range(f0, f1 + 1, CLIP_STEP[name]))
    if fr[-1] != f1: fr.append(f1)
    ADP = KEY_TOL > 0 and name in KEY_CLIPS
    WK = name != 'crew_climb'
    FRL = [adaptive_keys_g(f0, f1, ci, 'legs', LEG_MAXGAP if WK else LEG_MAXGAP_CLIMB, WK) if ADP else fr for ci in range(4)]                       # LEGS key times per crew
    FRU = [adaptive_keys_g(f0, f1, ci, 'upper', UP_MAXGAP_WALK if WK else UP_MAXGAP_CLIMB, WK, FRL[ci]) if ADP else fr for ci in range(4)]   # UPPER key times per crew
    AIC = []; AIU = []
    for ci in range(4):
        tin = np.array([(f - f0) / FPS for f in FRL[ci]], np.float32); AIC.append(add(tin[:, None], 5126, 'SCALAR', None, True)); nkeys += len(FRL[ci])
        tin = np.array([(f - f0) / FPS for f in FRU[ci]], np.float32); AIU.append(add(tin[:, None], 5126, 'SCALAR', None, True)); nkeys += len(FRU[ci])
    FRC = FRL
    CUR = [0]
    samplers = []; channels = []
    # least-squares key values: the linear-interpolated curve that best fits every 30 fps frame (not just point samples)
    fall = np.arange(f0, f1 + 1); kf = np.array(fr, float); Am = np.zeros((len(fall), len(fr)))
    for r_, f in enumerate(fall):
        j = min(np.searchsorted(kf, f, 'right') - 1, len(kf) - 2); u = (f - kf[j]) / (kf[j + 1] - kf[j]); Am[r_, j] += 1 - u; Am[r_, j + 1] += u
    LSQ = np.linalg.solve(Am.T @ Am, Am.T) if LSQ_ON else None
    def chan(node, path, V, interp='LINEAR', up=False):
        V = np.asarray(V, float); ai = (AIU if up else AIC)[CUR[0]]
        if LSQ_ON and interp == 'LINEAR':
            dense = np.array(DENSE[(node, path)], float); V = LSQ @ dense
            if path == 'rotation': V = V / np.linalg.norm(V, axis=1, keepdims=True)
        ao = add(np.asarray(V, np.float32), 5126, 'VEC4' if path == 'rotation' else 'VEC3')
        samplers.append({'input': ai, 'output': ao, 'interpolation': interp}); channels.append({'sampler': len(samplers) - 1, 'target': {'node': node, 'path': path}})
    for ci, c in enumerate(crew):
        jbase = 1 + ci * (len(JOINTS) + 2); fr = FRL[ci]; CUR[0] = ci
        for n in JOINTS:
            node = jbase + JOINTS.index(n)
            DENSE[(node, 'rotation')] = [frames[f][ci][0][n][1] for f in fall]
            if n == 'Root': DENSE[(node, 'translation')] = [frames[f][ci][0][n][0] for f in fall]
            frn = FRU[ci] if n in UP_J else FRL[ci]
            chan(node, 'rotation', [frames[f][ci][0][n][1] for f in frn], up=n in UP_J)
            if n == 'Root': chan(node, 'translation', [frames[f][ci][0][n][0] for f in fr])
            if n == 'Root': chan(node, 'scale', [[frames[f][ci][1]] * 3 for f in fr], 'STEP')
    anims.append({'name': name, 'samplers': samplers, 'channels': channels, 'extras': ({'keys_per_crew_legs': [len(x) for x in FRL], 'keys_per_crew_upper': [len(x) for x in FRU], 'key_tol_m': KEY_TOL, 'plant_tol_m': PLANT_TOL, 'keys': 'adaptive per crew, two groups (legs / upper body) with their own key times: planted boots locked, dense wherever the crew is near the ship'} if ADP else {'key_rate_hz': round(FPS / CLIP_STEP[name], 2)})})
print('keys per channel total', nkeys)
mat = {'name': 'SHM_Paint', 'pbrMetallicRoughness': {'metallicFactor': 0.0, 'roughnessFactor': 0.42}}
# Board_Focus + Board_Focus_Top: camera focus empties for the boarding camera (no camera is baked). Positions, frame_w and the height trigger
# come from board_focus_extras.json (written from cam_fit_v3.py + focus_trigger.mjs); the nodes are fixed, not fitted.
_fj = json.load(open(opt('--focus-json', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'board_focus_extras.json'))))
for _nm in ('Board_Focus', 'Board_Focus_Top'):
    _e = dict(_fj[_nm]['extras']); _e['mid_ladder_point'] = [round(float(x), 3) for x in lad(LAD_R, 0, 0.5 * (PAD_Y + DECK_Y))]
    rootn['children'].append(len(nodes)); nodes.append({'name': _nm, 'translation': [round(float(x), 4) for x in _fj[_nm]['translation']], 'extras': _e})
gl = {'asset': {'version': '2.0', 'generator': 'planet-stack crew boarding (Art Assistant 3)'}, 'scene': 0, 'scenes': [{'name': 'Scene', 'nodes': [0]}],
      'nodes': nodes, 'skins': skins, 'materials': [mat],
      'meshes': [{'name': 'CrewSuit_%d' % (i + 1), 'primitives': [{'attributes': {'POSITION': aP, 'NORMAL': aN, 'COLOR_0': aC, 'JOINTS_0': aJ, 'WEIGHTS_0': aW}, 'indices': aI, 'material': 0}]} for i in range(4)],
      'animations': anims, 'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': len(buf)}]}
while len(buf) % 4: buf.append(0)
gl['buffers'][0]['byteLength'] = len(buf)
js = json.dumps(gl, separators=(',', ':')).encode()
while len(js) % 4: js += b' '
with open(OUT, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(buf))); f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
    f.write(struct.pack('<II', len(buf), 0x004E4942)); f.write(bytes(buf))
timing['checks'] = chk; timing['tris_per_crew'] = int(len(IDX) // 3); timing['verts'] = int(nv); timing['total_s'] = round(T_END, 2)
json.dump(timing, open(TIMING, 'w'), indent=1)
# reference contacts for the three.js verifier: per 30 fps frame, crew, [Foot_L, Foot_R, Hand_L, Hand_R] world pos + planted / gripping flags
REF = TIMING.replace('.json', '_ref.npz')
cj = ['Foot_L', 'Foot_R', 'Hand_L', 'Hand_R']
RP = np.array([[[frames[f][ci][2][n] for n in cj] for ci in range(4)] for f in range(NF)], np.float32)
PL = np.zeros((NF, 4, 4), bool)
for ci, c in enumerate(crew):
    for f in range(1, NF):
        t = f / FPS
        for k, sd in enumerate('LR'):
            PL[f, ci, k] = np.linalg.norm(c.foot_at(sd, t)[0] - c.foot_at(sd, t - 1 / FPS)[0]) < 1e-9 and frames[f][ci][1] > 0.5
for k in (2, 3):   # hands gripping: reference hand target unchanged across the frame
    PL[1:, :, k] = (np.linalg.norm(RP[1:, :, k] - RP[:-1, :, k], axis=-1) < 1e-6) & (np.array([[frames[f][ci][1] for ci in range(4)] for f in range(1, NF)]) > 0.5)
np.savez(REF, P=RP, planted=PL, fps=FPS)
print('WROTE', OUT, 'tris', len(IDX) // 3, 'verts', nv, 'T_END', round(T_END, 2), 'clips', timing['clips'])
for tc in timing['crew']: print({k: v for k, v in tc.items() if k != 'rung_moves'})
