"""Planet Stack - launch crew boarding animation (Art Assistant 3).
Pure Python + numpy. Reads the decimated pass-3 suit (extract_suit.py -> suit_A.npz), builds an 18-joint game rig per crew member,
procedurally animates 4 crew (radio call -> walk to the Launch Pad -> staggered hand-over-hand climb of the ship ladder -> into the hatch)
with planted feet / hands, and writes a plain GLB (no extensions) for gltfpack.
python3 build_boarding.py SUIT.npz OUT_RAW.glb OUT_TIMING.json [--rung-pair-s 1.6]
All positions are Launch-Pad-local glTF (pad GLB root = identity): +Y up, the game camera looks from +Z.
Ladder / hatch numbers were measured read-only from launch_pad_game.glb (md5 816f18f3...): rungs y 0.65 + 0.6 i (i 0..34),
rails top / hatch deck y 21.85, ladder axis = Ship_Center (0, -13) + LU * 4.45 with LU = (0.866, 0, 0.5)."""
import sys, json, math, struct
import numpy as np

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
SOLE_LIFT = 0.005   # boot soles skin ~2-3 mm below the ankle target plane when the foot rolls: plant deck feet 5 mm high so no sole sinks into the wing deck
LAD_R = 4.45                                    # ladder plane radius from the ship axis
def lad(r, lat=0.0, y=0.0): return SHIP_C + LU * r + LT * lat + np.array([0, y, 0])
STAND = lad(4.95, 0.0, PAD_Y)                   # where a climber stands, facing the ladder (-LU), before mounting
DECK_U = 4.53                                   # deck foot spot (AA2: solid deck at t +/-0.9, u 4.3-4.7)
DECK_T = 0.92
SIDES = [float(x) for x in opt('--mantle-sides', '1,-1,1,-1').split(',')]   # mantle step-off side per climber (+1 = +t)
CLIMB_R = 4.74                                  # body (root) radius while on the ladder
# crew path markers in the pad GLB (Crew_Path_01..05): airlock AL-2 door -> receiver spot -> apron -> pad -> Ladder_Foot
CP = {1: (-11.19, 0.30, 7.94), 2: (-7.85, 0.30, 8.20), 3: (-2.40, 0.10, 2.20), 4: (3.20, 0.25, -3.40), 5: (4.50, 0.25, -10.40)}
# the straight Crew_Path_04 -> Ladder_Foot line crosses the ship-leg foot pad at (4.1, -5.9) (r 1.05), so the file goes round it on the outside
SHARED = [np.array(CP[2]), np.array(CP[3]), np.array((5.0, 0.25, -3.6)), np.array((6.15, 0.25, -5.9)), np.array((6.35, 0.25, -8.6))]
LEG_FEET = [np.array((4.10, 0.25, -5.90)), np.array((8.20, 0.25, -13.0))]

# ----------------------------------------------------------------------------- suit + rig
S = np.load(SUIT)
JP = {str(k): v.astype(float) for k, v in zip(S['jnames'], S['jpos'])}
HEADC = S['headc'].astype(float)
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
        yb0 = PAD_Y; ytop = 20.45                         # body (feet reference) height when the mantle starts
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
        W = {'hand': 0.42, 'foot': 0.45}
        TOPREL = {'hand': 1.85, 'foot': 0.78}                     # wrist / ankle height above y_b when the grip lands
        OFF = {'hand': -0.03, 'foot': 0.107}
        PAR = {'hand_R': 0, 'foot_L': 0, 'hand_L': 1, 'foot_R': 1}
        tg = np.arange(t0, t_end + 2.0, 0.002); yg = np.array([yb(t) for t in tg])
        moves = {k: [] for k in PAR}
        for k, par in PAR.items():
            kind, sd_ = k.split('_'); w = W[kind] * cyc
            top = 34 if kind == 'foot' else 35
            pre = None
            for idx in range(par, top + 1, 2) if kind == 'foot' else list(range(par, 35, 2)) + [35]:
                ry = (RUNG_Y[idx] if idx < 35 else DECK_Y + 0.02) + OFF[kind]
                need = ry - TOPREL[kind] - OFF[kind] + OFF[kind]
                need = (RUNG_Y[idx] if idx < 35 else DECK_Y + 0.02) - TOPREL[kind] + (0.107 if kind == 'foot' else -0.03)
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
            moves[k] = [tuple(m) for m in moves[k]]
        def limb_pos(kind, s, idx):
            if not isinstance(idx, (int, np.integer)): return np.asarray(idx, float)
            sd = SIDE[s]
            # the crew member faces -LU, so their left (+X local) is -LT ... left(yawL)
            lt = left(yawL)
            if kind == 'foot':
                return lad(LAD_R, 0, 0) + lt * 0.12 * sd + LU * 0.14 + np.array([0, RUNG_Y[idx] + 0.107, 0])
            if idx >= 35:   # rail tops / deck edge
                return lad(LAD_R, 0, 0) + lt * 0.27 * sd + LU * 0.05 + np.array([0, DECK_Y + 0.02, 0])
            return lad(LAD_R, 0, 0) + lt * 0.2 * sd + LU * 0.07 + np.array([0, RUNG_Y[idx] - 0.03, 0])
        for k, mv in moves.items():
            kind, s = k.split('_')
            if kind == 'foot':
                for a, b, idx in mv:
                    self.feet[s].append(dict(t0=a, t1=b, pos=limb_pos('foot', s, idx), yaw=yawL, kind='climb', arc=LU * 0.16 + np.array([0, 0.04, 0])))
        # mantle through the hatch-deck hole (AA2: hole u 4.05-5.15, t +/-0.62; decking to t +/-1.4 with a guard rail):
        # feet together on the top rung, lead hand to the hatch frame, trail hand pushes on the lead-side ladder rail top,
        # body rises and slides sideways, lead foot steps sideways onto solid deck (t = S*1.0), then the trail foot (t = S*0.78),
        # both at u = DECK_U, hands release, walk in along the solid deck and through the hatch.  S = +1 / -1 alternates per climber.
        tm = t_end; M = MANTLE_S; S = self.side
        lead = 'R' if S > 0 else 'L'; trail = 'L' if lead == 'R' else 'R'      # the climber faces -LU, so its right hand side is +t
        # v2 landing (AA2 option 1): open well u 4.05-5.15 |t| < 0.62, kerb |t| 0.62-0.68 (top z 21.88), wing stand area u 4.3-4.7 |t| 0.75-1.25.
        # Hands are on the stile tops when the climb ends. Lead hand to the hatch jamb; lead foot pulls back off rung 33, rises inside the
        # cage, then high-steps sideways over the kerb onto the wing; body hauls up and across; trail foot follows the same way off rung 34.
        MY = [(tm, ytop), (tm + 0.6 * M, ytop + 0.05), (tm + 1.0 * M, 20.75), (tm + 1.3 * M, 21.00), (tm + 1.9 * M, 21.12), (tm + 2.5 * M, 21.65), (tm + 2.9 * M, DECK_Y)]
        MR = [(tm, CLIMB_R), (tm + 0.6 * M, 4.70), (tm + 1.9 * M, 4.62), (tm + 2.9 * M, DECK_U)]
        MT = [(tm, 0.0), (tm + 1.3 * M, 0.0), (tm + 1.9 * M, S * 0.25), (tm + 2.5 * M, S * 0.65), (tm + 2.9 * M, S * DECK_T)]
        self.mantle = (MY, MR, MT)
        dk = lambda tt: lad(DECK_U, tt, DECK_Y + ANK + SOLE_LIFT)
        F = [(trail, tm + 0.05 * M, tm + 0.5 * M, limb_pos('foot', trail, 34), LU * 0.14 + np.array([0, 0.03, 0]), 0),
             (lead, tm + 0.55 * M, tm + 1.0 * M, lad(4.78, S * 0.14, 21.40), LU * 0.15, 0),                 # back off rung 33 and up inside the cage
             (lead, tm + 1.15 * M, tm + 1.85 * M, dk(S * (DECK_T + 0.10)), np.array([0, 0.40, 0]), 1),       # high step over the kerb onto the wing
             (trail, tm + 1.85 * M, tm + 2.15 * M, lad(4.76, 0.0, 21.70), LU * 0.06, 0),
             (trail, tm + 2.15 * M, tm + 2.7 * M, dk(S * (DECK_T - 0.10)), np.array([0, 0.25, 0]), 1)]
        self.deck_plants = []
        for s_, a_, b_, p_, arc_, dp_ in F:
            self.feet[s_].append(dict(t0=a_, t1=b_, pos=p_, yaw=yawL, kind='climb', arc=arc_))
            if dp_: self.deck_plants.append((s_, round(b_, 3), p_ - np.array([0, ANK, 0]), 'mantle'))
        HF = lambda tt, y: lad(4.13, tt, y)          # hatch jamb (outer face u 4.06, opening |t| 0.652)
        KG = lambda u_, y_: lad(u_, S * 0.65, y_)       # gloves on the well kerb top (|t| 0.62-0.68, top z 21.88) on the step-off side
        Hm = [(lead, tm + 1.6 * M, tm + 2.4 * M, lad(4.12, S * 0.76, 22.95))]   # lead glove: stile top -> flat on the hull beside the hatch
        for s_, a_, b_, p_ in Hm: moves['hand_' + s_].append((a_, b_, p_))
        tmd = tm + 3.3 * M
        # walk-in (AA2 option 1): no deck in front of the hatch.  Step toward the hull on the wing, shift the weight over the inner
        # foot, cross the outer foot behind it over the kerb and through the hatch (body |t| <= ~0.4 where it crosses the hull line),
        # then the inner foot follows.  Explicit plants (not the generic walk) so every deck plant stays on the wing.
        e0 = tmd; Lt = lambda u_, t_: lad(u_, S * t_, DECK_Y + ANK + SOLE_LIFT)
        yw = lambda v_: yawL + angdiff(yawL, yaw_of(v_))
        yd1 = yw(-LU * 0.9 - LT * S * 0.45); yd2 = yw(-LU * 0.75 - LT * S * 0.65); yin = yawL
        E = [(trail, e0, e0 + 0.5, Lt(4.15, 0.87), yd1, np.array([0, 0.10, 0])),
             (lead, e0 + 0.5, e0 + 0.95, Lt(4.23, 1.10), yd1, np.array([0, 0.10, 0])),
             (lead, e0 + 1.2, e0 + 1.75, Lt(3.80, 0.24), yd2, LU * 0.40 + np.array([0, 0.21, 0])),   # crossover behind the inner foot, over the kerb
             (trail, e0 + 1.75, e0 + 2.35, Lt(3.58, 0.08), yin, LU * 0.28 + np.array([0, 0.21, 0])),
             (lead, e0 + 2.6, e0 + 3.1, Lt(3.30, -0.02), yin, np.array([0, 0.10, 0]))]
        for s_, a_, b_, p_, y_, arc_ in E:
            self.feet[s_].append(dict(t0=a_, t1=b_, pos=p_, yaw=y_, kind='climb', arc=arc_))
            self.deck_plants.append((s_, round(b_, 3), p_ - np.array([0, ANK, 0]), 'walk_in'))
        MY += [(e0 + 1.2, DECK_Y), (e0 + 1.85, DECK_Y - 0.17), (e0 + 2.5, DECK_Y)]
        MR += [(e0 + 0.95, 4.25), (e0 + 1.4, 4.20), (e0 + 1.85, 4.10), (e0 + 2.45, 3.75), (e0 + 3.2, 3.40)]
        MT += [(e0 + 0.95, S * 0.86), (e0 + 1.4, S * 0.55), (e0 + 1.85, S * 0.26), (e0 + 2.45, S * 0.12), (e0 + 3.2, 0.0)]
        MW = [(tm, yawL), (e0, yawL), (e0 + 0.6, yd1), (e0 + 1.4, yd2), (e0 + 2.4, yin)]
        self.mantle = (MY, MR, MT, MW)
        tin = e0 + 3.2
        self.segs.append((t0, tin, 'climb', dict(yb=yb, yawL=yawL, moves=moves, limb_pos=limb_pos, tc=tc, t_end=t_end, tm=tm, tmd=tmd)))
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
        for e in ev:
            if t < e['t0']:
                # planted on prev; heel-rise before a walking lift-off (pivot on the toe)
                if e['kind'] == 'walk':
                    hr = 0.28 * Tri(t, e['t0'] - 0.16, e['t0'])
                    if hr > 0:
                        Rf = Ry(prev[1]); toe = prev[0] + Rf @ TOE
                        return toe + Rf @ Rx(hr) @ (-TOE), prev[1], hr
                return prev[0], prev[1], 0.0
            if t < e['t1']:
                u = (t - e['t0']) / (e['t1'] - e['t0'])
                p0 = prev[0]; y0 = prev[1]; pitch0 = 0.0
                if e['kind'] == 'walk':
                    pitch0 = 0.28; Rf = Ry(y0); toe = p0 + Rf @ TOE; p0 = toe + Rf @ Rx(0.28) @ (-TOE)
                h = sstep(u); p = p0 * (1 - h) + e['pos'] * h + e['arc'] * math.sin(math.pi * u) ** 1.2
                yw = y0 + angdiff(y0, e['yaw']) * s5(u)
                if e['kind'] == 'walk': pitch = pitch0 * (1 - sstep(u * 2.2)) - 0.22 * math.sin(math.pi * min(1, max(0, (u - 0.35) / 0.65))) * 0.9
                elif e['kind'] == 'climb': pitch = -0.25 * math.sin(math.pi * u)
                else: pitch = 0.0
                return p, yw, pitch
            prev = (e['pos'], e['yaw'])
        return prev[0], prev[1], 0.0

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
        lean = 0.02 * u + 0.18 * math.sin(math.pi * min(1, mm * 1.25)) - 0.02 * Tri(mm, 0.6, 1.0); hips_off = np.array([0, -0.03 * u, 0.0])
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
    if kind == 'climb':
        H = {}
        for s in 'LR':
            mv = D['moves']['hand_' + s]; lp = D['limb_pos']
            free = free_hands(c, t, R_c, G['Chest'], 0.0, Tri(t, D['tmd'] - 0.3, D['tmd'] + 0.6) if t >= D['tm'] else 0.0)[s][0]
            prev = None; p = None
            for (a, b, idx) in mv:
                tgt = lp('hand', s, idx)
                if t < a: p = prev if prev is not None else free; break
                if t < b:
                    src = prev if prev is not None else free
                    u = s5((t - a) / (b - a))
                    if prev is None:   # first reach from the relaxed pose: swing the hand out in front (Bezier), never past the shoulder
                        shp = G['Chest'] + R_c @ (BIND['UpperArm_' + s] - BIND['Chest'])
                        ctl = shp - LU * 0.62 + left(yawL) * SIDE[s] * 0.12 - np.array([0, 0.05, 0])
                        p = src * (1 - u) ** 2 + ctl * 2 * u * (1 - u) + tgt * u * u
                    else:
                        p = src * (1 - u) + tgt * u + (-LU * 0.04 + left(yawL) * SIDE[s] * 0.09) * math.sin(math.pi * u)
                    break
                prev = tgt
            if p is None: p = prev
            if t >= D['tm']:   # mantle: let go of the hatch frame once both boots are on the deck
                trail_ = s == ('L' if c.side > 0 else 'R')    # trail hand lets go of the kerb as the body stands up on the wing
                r = Tri(t, D['tm'] + (1.45 if trail_ else 2.55) * MANTLE_S, D['tm'] + (1.85 if trail_ else 3.0) * MANTLE_S); p = p * (1 - r) + free * r
            elat = 0.55 - (0.45 * Tri(t, D['tm'] + 1.1 * MANTLE_S, D['tm'] + 1.6 * MANTLE_S) if t >= D['tm'] else 0.0)   # mantle: tuck the elbows in, away from the deck rails
            pole = R_root @ np.array([SIDE[s] * elat, -1.0, 0.3])     # elbows down/in: keeps forearms inside the ladder cage
            fpole = R_c @ np.array([SIDE[s] * 0.55, -0.25, -1.0])
            wv = Tri(t, sg[0], sg[0] + 0.6) * (1 - (Tri(t, D['tm'] + 2.85 * MANTLE_S, D['tm'] + 3.3 * MANTLE_S) if t >= D['tm'] else 0))
            H[s] = (p, nrm(fpole * (1 - wv) + pole * wv))
        curl = -0.15 - 0.35 * Tri(t, sg[0], sg[0] + 0.6) * (1 - (Tri(t, D['tm'] + 2.85 * MANTLE_S, D['tm'] + 3.3 * MANTLE_S) if t >= D['tm'] else 0))
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
        if kind == 'climb': knee_dir = R_root @ np.array([SIDE[s] * 0.35, 0.2, 1.0])
        CTX.update(crew=c.k, t=round(t, 3), limb='leg' + s); R1, R2 = ik2(A, ap, L_TH[s], L_SH[s], knee_dir, IKB['leg' + s])
        G['Thigh_' + s] = A; Rg['Thigh_' + s] = R1; G['Shin_' + s] = A + R1 @ boff('Shin_' + s); Rg['Shin_' + s] = R2
        G['Foot_' + s] = G['Shin_' + s] + R2 @ boff('Foot_' + s); Rg['Foot_' + s] = Rf
        hp_, pole = H[s]
        Ash = G['Chest'] + R_c @ boff('UpperArm_' + s)
        CTX.update(crew=c.k, t=round(t, 3), limb='arm' + s); R1, R2 = ik2(Ash, hp_, L_UA[s], L_FA[s], pole, IKB['arm' + s])
        G['UpperArm_' + s] = Ash; Rg['UpperArm_' + s] = R1; G['Forearm_' + s] = Ash + R1 @ boff('Forearm_' + s); Rg['Forearm_' + s] = R2
        G['Hand_' + s] = G['Forearm_' + s] + R2 @ boff('Hand_' + s); Rg['Hand_' + s] = R2 @ Rx(curl)
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
            if np.linalg.norm(p1 - p0) < 1e-9:
                slide = max(slide, np.linalg.norm(foot_world(ci, f, s) - foot_world(ci, f - 1, s)))
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
P = S['P'].astype(float); N = S['N'].astype(float); C = S['C']; Gi = S['G']; gnames = [str(x) for x in S['gnames']]
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
        rung[k] = [[r3(a), r3(b), (int(i) if isinstance(i, (int, np.integer)) else ('ladder_rail_top' if np.asarray(i)[1] < 22.0 else 'hatch_frame'))] for a, b, i in mv]
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
# animations: one shared uniform time input per clip; the rate per clip is chosen by how fast the motion is
# (pack with gltfpack -af 0 so these keys are kept as authored). Every node keeps a track in every clip.
CLIP_STEP = {'crew_call': opt('--call-step', 2), 'crew_walk_to_pad': opt('--walk-step', 2), 'crew_climb': opt('--climb-step', 3)}   # in 30 fps frames
anims = []; nkeys = 0; DENSE = {}; LSQ_ON = '--no-lsq' not in ARGS
for name, a, b in CLIPS:
    f0 = int(round(a * FPS)); f1 = int(round(b * FPS)); fr = list(range(f0, f1 + 1, CLIP_STEP[name]))
    if fr[-1] != f1: fr.append(f1)
    tin = np.array([(f - f0) / FPS for f in fr], np.float32); ai = add(tin[:, None], 5126, 'SCALAR', None, True); nkeys += len(fr)
    samplers = []; channels = []
    # least-squares key values: the linear-interpolated curve that best fits every 30 fps frame (not just point samples)
    fall = np.arange(f0, f1 + 1); kf = np.array(fr, float); Am = np.zeros((len(fall), len(fr)))
    for r_, f in enumerate(fall):
        j = min(np.searchsorted(kf, f, 'right') - 1, len(kf) - 2); u = (f - kf[j]) / (kf[j + 1] - kf[j]); Am[r_, j] += 1 - u; Am[r_, j + 1] += u
    LSQ = np.linalg.solve(Am.T @ Am, Am.T) if LSQ_ON else None
    def chan(node, path, V, interp='LINEAR'):
        V = np.asarray(V, float)
        if LSQ_ON and interp == 'LINEAR':
            dense = np.array(DENSE[(node, path)], float); V = LSQ @ dense
            if path == 'rotation': V = V / np.linalg.norm(V, axis=1, keepdims=True)
        ao = add(np.asarray(V, np.float32), 5126, 'VEC4' if path == 'rotation' else 'VEC3')
        samplers.append({'input': ai, 'output': ao, 'interpolation': interp}); channels.append({'sampler': len(samplers) - 1, 'target': {'node': node, 'path': path}})
    for ci, c in enumerate(crew):
        jbase = 1 + ci * (len(JOINTS) + 2)
        for n in JOINTS:
            node = jbase + JOINTS.index(n)
            DENSE[(node, 'rotation')] = [frames[f][ci][0][n][1] for f in fall]
            if n == 'Root': DENSE[(node, 'translation')] = [frames[f][ci][0][n][0] for f in fall]
            chan(node, 'rotation', [frames[f][ci][0][n][1] for f in fr])
            if n == 'Root': chan(node, 'translation', [frames[f][ci][0][n][0] for f in fr])
            if n == 'Root': chan(node, 'scale', [[frames[f][ci][1]] * 3 for f in fr], 'STEP')
    anims.append({'name': name, 'samplers': samplers, 'channels': channels, 'extras': {'key_rate_hz': round(FPS / CLIP_STEP[name], 2)}})
print('keys per channel total', nkeys)
mat = {'name': 'SHM_Paint', 'pbrMetallicRoughness': {'metallicFactor': 0.0, 'roughnessFactor': 0.42}}
# Board_Focus: camera focus empty for the boarding camera push (no camera is baked). Default = mid-ladder point on the ladder axis.
_fs = opt('--focus', '')
BF = np.array([float(x) for x in _fs.split(',')]) if _fs else lad(LAD_R, 0, 0.5 * (PAD_Y + DECK_Y))
_bfx = json.loads(opt('--focus-extras', '{}'))
_bfx.update({'mid_ladder_point': [round(float(x), 3) for x in lad(LAD_R, 0, 0.5 * (PAD_Y + DECK_Y))], 'note': 'empty; aim the boarding camera here (38 deg vFOV, 18 deg look-down, game yaw). No camera in this GLB.'})
rootn['children'].append(len(nodes)); nodes.append({'name': 'Board_Focus', 'translation': [round(float(x), 4) for x in BF], 'extras': _bfx})
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
