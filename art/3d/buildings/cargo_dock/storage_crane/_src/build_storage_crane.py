"""SC-1 storage crane for the Cargo Dock (layout v3). Writes storage_crane.glb (one skinned mesh, 3 materials = 3 draws).
Crane-local frame = glTF metres, origin = pillar base ground centre, +X = jib at rest, +Z = toward the road/camera.
Placed in layout v3 at world (384.6, 0, 8.5) yaw 0 (dock-local (24.6, 0, 16.5) of cargo_dock_compact_v3.glb with the dock at (360, 0, -8)).
Layout v2 used world (350.7, 0, 8.5) with the dock at (373, 0, -8); the crane-local slot/stop offsets are identical."""
import json, math, struct, sys, numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else 'storage_crane.glb'
CRANE_W = np.array([384.6, 0.0, 8.5])          # world placement used by layout v3
DOCK_W = np.array([360.0, 0.0, -8.0])
SLOTS = json.load(open(sys.argv[2]))['slots'] if len(sys.argv) > 2 else None
TRUCK_STOP_W = np.array([386.5, 0.0, 13.0])     # FB-05 origin at the dock stop (lane z 13, heading +X)
BED = {'A': np.array([-1.15, 1.9, 0.0]), 'B': np.array([-3.65, 1.9, 0.0])}   # FB-05 Bed_Slot_01 / _02 (box Base)
HOOKPT = 1.5                                     # CargoBox Hook_Point above Base
SLEW_Y, TROL_DY = 6.3, 0.5                       # Slew joint y; trolley joint above slew joint (jib underside = 6.8)
TROLLEY_Y = SLEW_Y + TROL_DY
R_REST, CARRY = 4.0, 5.6                         # rest radius; carry height of Hook_Attach (box Base 4.1 m)
FPS = 30

def srgb(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
WHITE, WHITE_LO = srgb('e2f0f0'), srgb('b8c6ca')
NAVY, NAVY_HI = srgb('30303f'), srgb('4a4f62')
METAL, METAL_LO = srgb('a8b4b6'), srgb('7c8688')
ORANGE, ORANGE_LO = srgb('f2b060'), srgb('d08a3e')
CYAN = srgb('30e0ff')
CONC, CONC_LO = srgb('9ea3aa'), srgb('8a8f96')

prims = {0: [], 1: [], 2: []}   # 0 SHM_Paint, 1 SHM_Metal, 2 SHM_GlowCyan
def lerp(a, b, t): return [a[i] + (b[i] - a[i]) * t for i in range(3)]

def add(mat, P, N, C, J, idx):
    prims[mat].append((np.array(P, 'f4'), np.array(N, 'f4'), np.array(C, 'f4'), np.array(J), np.array(idx, 'u4')))

def box(mat, lo, hi, joint, ctop, cbot=None, ytaper=None):
    """axis box with a vertical soft gradient (ctop at top, cbot at bottom). ytaper=(x_end, scale) shrinks y/z toward +x end."""
    cbot = cbot or ctop
    x0, y0, z0 = lo; x1, y1, z1 = hi
    faces = [((1, 0, 0), [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)]), ((-1, 0, 0), [(x0, y0, z1), (x0, y1, z1), (x0, y1, z0), (x0, y0, z0)]),
             ((0, 1, 0), [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)]), ((0, -1, 0), [(x0, y0, z1), (x0, y0, z0), (x1, y0, z0), (x1, y0, z1)]),
             ((0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]), ((0, 0, -1), [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)])]
    P, N, C, idx = [], [], [], []
    for n, vs in faces:
        b = len(P)
        for v in vs:
            v = list(v)
            if ytaper and v[0] == x1:    # taper the far end (keep the top flat)
                s = ytaper; v[1] = y1 - (y1 - v[1]) * s; v[2] = (z0 + z1) / 2 + (v[2] - (z0 + z1) / 2) * s
            t = 0 if y1 == y0 else (v[1] - y0) / (y1 - y0)
            P.append(v); N.append(n); C.append(lerp(cbot, ctop, t))
        idx += [b, b + 2, b + 1, b, b + 3, b + 2]
    # fix winding to outward normals
    P2 = np.array(P); idx2 = []
    for k in range(0, len(idx), 3):
        a, b2, c = idx[k:k + 3]; n = np.cross(P2[b2] - P2[a], P2[c] - P2[a])
        idx2 += [a, b2, c] if np.dot(n, N[a]) > 0 else [a, c, b2]
    if ytaper:   # recompute flat normals after taper
        for k in range(0, len(idx2), 6):
            a, b2, c = idx2[k:k + 3]; n = np.cross(P2[b2] - P2[a], P2[c] - P2[a]); n /= np.linalg.norm(n) + 1e-9
            for q in set(idx2[k:k + 6]): N[q] = tuple(n)
    add(mat, P, N, C, [joint] * len(P), idx2)

def cyl(mat, cx, cz, y0, y1, r, joint, ctop, cbot=None, n=10, r1=None):
    cbot = cbot or ctop; r1 = r if r1 is None else r1
    P, N, C, idx = [], [], [], []
    for i in range(n + 1):
        a = 2 * math.pi * i / n; ca, sa = math.cos(a), math.sin(a)
        P += [(cx + r * ca, y0, cz + sa * r), (cx + r1 * ca, y1, cz + sa * r1)]; N += [(ca, 0, sa)] * 2; C += [cbot, ctop]
    for i in range(n):
        b = 2 * i; idx += [b, b + 1, b + 3, b, b + 3, b + 2]
    for yy, rr, ny, col in ((y1, r1, 1, ctop), (y0, r, -1, cbot)):
        c0 = len(P); P.append((cx, yy, cz)); N.append((0, ny, 0)); C.append(col)
        for i in range(n + 1):
            a = 2 * math.pi * i / n; P.append((cx + rr * math.cos(a), yy, cz + rr * math.sin(a))); N.append((0, ny, 0)); C.append(col)
        for i in range(n):
            idx += [c0, c0 + 2 + i, c0 + 1 + i] if ny > 0 else [c0, c0 + 1 + i, c0 + 2 + i]
    add(mat, P, N, C, [joint] * len(P), idx)

def beam(mat, a, b, t, joint, col):
    """thin square beam from a to b (in the x-y plane, z thickness t)"""
    a, b = np.array(a, float), np.array(b, float); d = b - a; L = np.linalg.norm(d); u = d / L
    nrm = np.array([-u[1], u[0], 0.0]); zz = np.array([0, 0, 1.0])
    P, N, C, idx = [], [], [], []
    for (sn, sz) in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        pass
    corners = lambda p: [p + nrm * t / 2 + zz * t / 2, p - nrm * t / 2 + zz * t / 2, p - nrm * t / 2 - zz * t / 2, p + nrm * t / 2 - zz * t / 2]
    ca, cb = corners(a), corners(b); fn = [(nrm + zz), (-nrm + zz), (-nrm - zz), (nrm - zz)]
    for i in range(4):
        j = (i + 1) % 4; n = (fn[i] + fn[j]); n = n / np.linalg.norm(n); bb = len(P)
        P += [ca[i], ca[j], cb[j], cb[i]]; N += [n] * 4; C += [col] * 4
        q = [bb, bb + 1, bb + 2, bb, bb + 2, bb + 3]
        v = np.cross(P[bb + 1] - P[bb], P[bb + 2] - P[bb]); idx += q if np.dot(v, n) > 0 else [bb, bb + 2, bb + 1, bb, bb + 3, bb + 2]
    add(mat, [list(p) for p in P], [list(x) for x in N], C, [joint] * len(P), idx)

J_BASE, J_SLEW, J_TROL, J_HOOK = 0, 1, 2, 3
# --- static (SC_Base) ---
box(0, (-0.7, 0, -0.7), (0.7, 0.2, 0.7), J_BASE, CONC, CONC_LO)                       # footing pad (z 7.8..9.2 world)
box(0, (-0.72, 0.2, -0.72), (0.72, 0.24, 0.72), J_BASE, ORANGE, ORANGE_LO)            # hazard rim
cyl(0, 0, 0, 0.24, 0.55, 0.55, J_BASE, NAVY_HI, NAVY)                                 # flange
cyl(0, 0, 0, 0.55, 6.3, 0.34, J_BASE, WHITE, WHITE_LO, r1=0.28)                       # pillar (soft white gradient)
cyl(0, 0, 0, 2.6, 2.75, 0.36, J_BASE, NAVY_HI, NAVY)                                  # navy band
cyl(2, 0, 0, 2.75, 2.85, 0.35, J_BASE, CYAN)                                          # glow ring
# --- slewing (SC_Slew), built in world-rest coords (slew joint at y 6.3) ---
cyl(1, 0, 0, 6.3, 6.55, 0.5, J_SLEW, METAL, METAL_LO)                                 # slew ring
box(0, (-0.55, 6.55, -0.5), (0.6, 7.35, 0.5), J_SLEW, WHITE, WHITE_LO)                 # machinery head
box(0, (-0.56, 6.9, -0.51), (0.61, 7.05, 0.51), J_SLEW, NAVY_HI, NAVY)                 # head navy stripe
box(2, (0.61, 6.95, -0.3), (0.63, 7.2, 0.3), J_SLEW, CYAN)                             # sensor eye (jib side)
box(0, (0.6, 6.8, -0.24), (7.45, 7.3, 0.24), J_SLEW, WHITE, WHITE_LO, ytaper=0.7)      # jib (tapered)
box(0, (0.6, 6.78, -0.25), (7.3, 6.86, 0.25), J_SLEW, NAVY)                            # jib rail (trolley track)
box(0, (7.0, 7.08, -0.17), (7.46, 7.32, 0.17), J_SLEW, ORANGE, ORANGE_LO)               # tip cap
box(2, (7.18, 7.32, -0.08), (7.34, 7.46, 0.08), J_SLEW, CYAN)                           # tip beacon
box(0, (-2.5, 6.85, -0.22), (-0.55, 7.2, 0.22), J_SLEW, WHITE, WHITE_LO)               # counter-jib
box(0, (-2.6, 6.35, -0.42), (-1.65, 7.0, 0.42), J_SLEW, NAVY_HI, NAVY)                 # counterweight
box(0, (-2.61, 6.6, -0.43), (-1.64, 6.68, 0.43), J_SLEW, ORANGE)                        # counterweight stripe
box(0, (-0.1, 7.35, -0.1), (0.1, 8.35, 0.1), J_SLEW, WHITE, WHITE_LO)                  # A-mast
box(0, (-0.13, 8.3, -0.13), (0.13, 8.42, 0.13), J_SLEW, ORANGE)                         # mast cap
beam(1, (0.05, 8.3, 0), (6.9, 7.3, 0), 0.07, J_SLEW, METAL)                            # jib tie
beam(1, (-0.05, 8.3, 0), (-2.4, 7.2, 0), 0.07, J_SLEW, METAL)                          # counter tie
# --- trolley (SC_Trolley joint at (R_REST, 6.8, 0)) ---
box(1, (R_REST - 0.32, 6.45, -0.3), (R_REST + 0.32, 6.78, 0.3), J_TROL, METAL, METAL_LO)
box(0, (R_REST - 0.33, 6.6, -0.31), (R_REST + 0.33, 6.68, 0.31), J_TROL, ORANGE)
# --- rope: top on the trolley, bottom on the hook (stretches with skinning) ---
ry0, ry1 = CARRY + 0.6, 6.45
P, N, C, idx, JJ = [], [], [], [], []
t = 0.05
for k, (dx, dz, nx, nz) in enumerate(((1, 0, 1, 0), (0, 1, 0, 1), (-1, 0, -1, 0), (0, -1, 0, -1))):
    b = len(P); ex, ez = (-dz, dx)
    for (yy, jj) in ((ry0, J_HOOK), (ry1, J_TROL)):
        for s in (-1, 1):
            P.append((R_REST + dx * t + ex * t * s, yy, dz * t + ez * t * s)); N.append((nx, 0, nz)); C.append(NAVY); JJ.append(jj)
    q = [b, b + 1, b + 3, b, b + 3, b + 2]
    v = np.cross(np.subtract(P[b + 1], P[b]), np.subtract(P[b + 3], P[b])); idx += q if np.dot(v, (nx, 0, nz)) > 0 else [b, b + 3, b + 1, b, b + 2, b + 3]
add(1, P, N, C, JJ, idx)
# --- hook block (SC_Hook joint = Hook_Attach at (R_REST, CARRY, 0)) ---
box(0, (R_REST - 0.28, CARRY + 0.25, -0.2), (R_REST + 0.28, CARRY + 0.6, 0.2), J_HOOK, ORANGE, ORANGE_LO)
box(0, (R_REST - 0.29, CARRY + 0.36, -0.21), (R_REST + 0.29, CARRY + 0.44, 0.21), J_HOOK, NAVY)
box(1, (R_REST - 0.06, CARRY + 0.02, -0.06), (R_REST + 0.06, CARRY + 0.25, 0.06), J_HOOK, METAL, METAL_LO)
box(1, (R_REST - 0.16, CARRY, -0.05), (R_REST + 0.16, CARRY + 0.06, 0.05), J_HOOK, METAL_LO)

# ---------- poses / clips ----------
def to_local(w): return np.asarray(w, float) - CRANE_W
def aim(p):   # crane-local point -> (slew rad, radius)
    return math.atan2(-p[2], p[0]), math.hypot(p[0], p[2])
pick_pts = {k: to_local(TRUCK_STOP_W + v) for k, v in BED.items()}
slot_pts = [(s['name'], to_local(s['world'])) for s in SLOTS]
def ss(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def unwrap(a, ref):
    while a - ref > math.pi: a -= 2 * math.pi
    while a - ref < -math.pi: a += 2 * math.pi
    return a
T = dict(approach=(0.0, 1.0), lower=(1.0, 1.5), grab=(1.5, 1.65), hoist=(1.65, 2.15), swing=(2.15, 3.75), set=(3.75, 4.3), release=(4.3, 4.45), up=(4.45, 4.9), ret=(4.9, 6.0))
PICK_T, SET_T, DUR = 1.55, 4.35, 6.0
def clip_pose(pk, sl, t):
    tp, rp = aim(pk); ts, rs = aim(sl); tp = unwrap(tp, 0.0); ts = unwrap(ts, tp); tr = unwrap(0.0, ts)
    yp, ys = pk[1] + HOOKPT, sl[1] + HOOKPT
    seg = lambda n: ss((t - T[n][0]) / (T[n][1] - T[n][0]))
    if t <= T['approach'][1]: u = seg('approach'); th, r, y = tp * u, R_REST + (rp - R_REST) * u, CARRY
    elif t <= T['grab'][1]: th, r, y = tp, rp, CARRY + (yp - CARRY) * seg('lower')
    elif t <= T['hoist'][1]: th, r, y = tp, rp, yp + (CARRY - yp) * seg('hoist')
    elif t <= T['swing'][1]: u = seg('swing'); th, r, y = tp + (ts - tp) * u, rp + (rs - rp) * u, CARRY
    elif t <= T['release'][1]: th, r, y = ts, rs, CARRY + (ys - CARRY) * seg('set')
    elif t <= T['up'][1]: th, r, y = ts, rs, ys + (CARRY - ys) * seg('up')
    else: u = seg('ret'); th, r, y = ts + (tr - ts) * u, rs + (R_REST - rs) * u, CARRY
    return th, r, y
def quat_y(a): return [0.0, math.sin(a / 2), 0.0, math.cos(a / 2)]

# ---------- glTF assembly ----------
bin_ = bytearray(); views, accs = [], []
def push(arr, target=None, comp=5126, typ='VEC3', mm=False, count=None):
    while len(bin_) % 4: bin_.append(0)
    off = len(bin_); b = arr.tobytes(); bin_.extend(b)
    v = {'buffer': 0, 'byteOffset': off, 'byteLength': len(b)}
    if target: v['target'] = target
    views.append(v)
    a = {'bufferView': len(views) - 1, 'componentType': comp, 'count': count if count is not None else len(arr), 'type': typ}
    if mm: a['min'] = arr.min(0).tolist() if arr.ndim > 1 else [float(arr.min())]; a['max'] = arr.max(0).tolist() if arr.ndim > 1 else [float(arr.max())]
    accs.append(a); return len(accs) - 1
MATS = [{'name': 'SHM_Paint', 'pbrMetallicRoughness': {'metallicFactor': 0, 'roughnessFactor': 0.42}},
        {'name': 'SHM_Metal', 'pbrMetallicRoughness': {'metallicFactor': 0.85, 'roughnessFactor': 0.34}},
        {'name': 'SHM_GlowCyan', 'pbrMetallicRoughness': {'baseColorFactor': [0.02842604, 0.768151164, 1, 1], 'metallicFactor': 0, 'roughnessFactor': 0.5}, 'emissiveFactor': [0.02842604, 0.768151164, 1]}]
jointW = {J_BASE: np.zeros(3), J_SLEW: np.array([0, SLEW_Y, 0]), J_TROL: np.array([R_REST, TROLLEY_Y, 0]), J_HOOK: np.array([R_REST, CARRY, 0])}
primitives = []; ntri = 0
for m, parts in prims.items():
    P = np.concatenate([p[0] for p in parts]); N = np.concatenate([p[1] for p in parts]); C = np.concatenate([p[2] for p in parts])
    J = np.concatenate([p[3] for p in parts]); I = []; o = 0
    for p in parts: I.append(p[4] + o); o += len(p[0])
    I = np.concatenate(I).astype('u2' if o < 65535 else 'u4'); ntri += len(I) // 3
    N = N / np.linalg.norm(N, axis=1, keepdims=True)
    C4 = np.concatenate([C, np.ones((len(C), 1), 'f4')], 1).astype('f4')
    JO = np.zeros((len(J), 4), 'u1'); JO[:, 0] = J; WW = np.zeros((len(J), 4), 'f4'); WW[:, 0] = 1
    attrs = {'POSITION': push(P.astype('f4'), 34962, mm=True), 'NORMAL': push(N.astype('f4'), 34962), 'COLOR_0': push(C4, 34962, typ='VEC4'),
             'JOINTS_0': push(JO, 34962, comp=5121, typ='VEC4'), 'WEIGHTS_0': push(WW, 34962, typ='VEC4')}
    primitives.append({'attributes': attrs, 'indices': push(I, 34963, comp=5123 if I.dtype == np.uint16 else 5125, typ='SCALAR'), 'material': m})
ibm = np.zeros((4, 16), 'f4')
for j, w in jointW.items():
    M = np.eye(4); M[:3, 3] = -w; ibm[j] = M.T.reshape(-1)    # column-major
ibm_acc = push(ibm, typ='MAT4')
nodes = [
    {'name': 'StorageCrane', 'children': [1, 2], 'extras': {}},
    {'name': 'SC_Mesh', 'mesh': 0, 'skin': 0},
    {'name': 'SC_Base', 'children': [3]},
    {'name': 'SC_Slew', 'translation': [0, SLEW_Y, 0], 'children': [4]},
    {'name': 'SC_Trolley', 'translation': [R_REST, TROL_DY, 0], 'children': [5]},
    {'name': 'SC_Hook', 'translation': [0, CARRY - TROLLEY_Y, 0], 'children': [6]},
    {'name': 'Hook_Attach', 'extras': {'note': 'CargoBox Hook_Point goes here: parent the box with local offset (0, -1.5, 0), yaw 0'}},
]
def empty(name, pos, ex):
    nodes.append({'name': name, 'translation': [round(float(v), 4) for v in pos], 'extras': ex}); nodes[0]['children'].append(len(nodes) - 1)
empty('Truck_Stop_Dock', to_local(TRUCK_STOP_W), {'kind': 'flatbed_stop', 'note': 'FB-05 origin here, heading +X, on lane z 13 (world %.1f, 0, 13)' % TRUCK_STOP_W[0]})
for k, p in pick_pts.items(): empty('Pick_' + k, p, {'kind': 'pick', 'bed_slot': 'Bed_Slot_0' + ('1' if k == 'A' else '2'), 'note': 'CargoBox Base on the parked FB-05'})
slot_params = []
for name, p in slot_pts:
    th, r = aim(p)
    prm = {'slew_deg': round(math.degrees(th), 3), 'radius_m': round(r, 4), 'hook_y_m': round(p[1] + HOOKPT, 4), 'trolley_x_m': round(r, 4), 'hook_local_y_m': round(p[1] + HOOKPT - TROLLEY_Y, 4)}
    empty(name, p, {'kind': 'storage_slot', **prm, 'note': 'CargoBox Base here, yaw 0'}); slot_params.append({'name': name, 'base': [round(float(v), 4) for v in p], **prm})
pick_params = {k: {'slew_deg': round(math.degrees(aim(p)[0]), 3), 'radius_m': round(aim(p)[1], 4), 'hook_y_m': round(p[1] + HOOKPT, 4)} for k, p in pick_pts.items()}
# clips
anims = []
times = np.arange(0, round(DUR * FPS) + 1) / FPS
tacc = push(times.astype('f4'), mm=True, typ='SCALAR')
for k, pk in pick_pts.items():
    for name, sl in slot_pts:
        S = [clip_pose(pk, sl, t) for t in times]
        rs = np.array([quat_y(s[0]) for s in S], 'f4'); tr = np.array([[s[1], TROL_DY, 0] for s in S], 'f4')
        hk = np.array([[0, s[2] - TROLLEY_Y, 0] for s in S], 'f4'); hr = np.array([quat_y(-s[0]) for s in S], 'f4')
        outs = [push(rs, typ='VEC4'), push(tr), push(hk), push(hr, typ='VEC4')]
        samplers = [{'input': tacc, 'output': o, 'interpolation': 'LINEAR'} for o in outs]
        chans = [{'sampler': 0, 'target': {'node': 3, 'path': 'rotation'}}, {'sampler': 1, 'target': {'node': 4, 'path': 'translation'}},
                 {'sampler': 2, 'target': {'node': 5, 'path': 'translation'}}, {'sampler': 3, 'target': {'node': 5, 'path': 'rotation'}}]
        anims.append({'name': f'Store_{k}_{name}', 'samplers': samplers, 'channels': chans,
                      'extras': {'pick': 'Pick_' + k, 'slot': name, 'duration_s': DUR, 'pick_t': PICK_T, 'set_t': SET_T}})
nodes[0]['extras'] = {
    'prop': 'SC-1 Cargo Dock storage crane (layout v3)', 'origin': 'pillar base ground centre', 'place_world': CRANE_W.tolist(), 'place_dock_local': (CRANE_W - DOCK_W).tolist(), 'yaw_deg': 0,
    'joints': 'SC_Slew rotY = slew; SC_Trolley x = radius (y 0.5); SC_Hook y = hook_y - 6.8, rotY = -slew (box stays yaw 0); Hook_Attach = box Hook_Point',
    'rest': {'slew_deg': 0, 'radius_m': R_REST, 'hook_y_m': CARRY}, 'carry_hook_y_m': CARRY, 'trolley_y_m': TROLLEY_Y, 'radius_range_m': [1.9, 6.95],
    'timeline_s': {k: list(v) for k, v in T.items()}, 'pick_t': PICK_T, 'set_t': SET_T, 'duration_s': DUR, 'easing': 'smoothstep per segment',
    'pick': pick_params, 'slots': slot_params}
gl = {'asset': {'version': '2.0', 'generator': 'planet-stack build_storage_crane.py'}, 'scene': 0, 'scenes': [{'name': 'Scene', 'nodes': [0]}], 'nodes': nodes,
      'meshes': [{'name': 'SC_Mesh', 'primitives': primitives}], 'materials': MATS, 'skins': [{'name': 'SC_Rig', 'joints': [2, 3, 4, 5], 'skeleton': 2, 'inverseBindMatrices': ibm_acc}],
      'animations': anims, 'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': 0}]}
while len(bin_) % 4: bin_.append(0)
gl['buffers'][0]['byteLength'] = len(bin_)
js = json.dumps(gl, separators=(',', ':')).encode()
while len(js) % 4: js += b' '
glb = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(bin_), 0x004E4942) + bytes(bin_)
open(OUT, 'wb').write(glb)
print('wrote', OUT, len(glb), 'bytes; draws', len(primitives), 'tris', ntri, 'clips', len(anims))
print('pick', pick_params); print('slot r range', min(s['radius_m'] for s in slot_params), max(s['radius_m'] for s in slot_params))
