"""Planet Stack - SHIPYARD game GLB post-pass: SN-07 staged ship-build clips (python3 + numpy, no Blender).

  python3 post_ship_build.py IN_raw.glb OUT_raw2.glb            -> then: gltfpack -i OUT_raw2.glb -o shipyard_game.glb -cc -kn -ke
  python3 post_ship_build.py IN_raw.glb OUT_pose.glb --pose CLIP:T   (static GLB of one pose, morphs + jib angle baked; proof strips only)

Why a post-pass: every moving piece must stay inside the 15-draw budget, so the ship build is driven by MORPH TARGETS (core glTF 'weights'
animation: survives gltfpack, plays in three.js GLTFLoader/AnimationMixer with no extension) on the one Crane_Jib mesh, plus its node rotation.
  Crane_Jib primitives: SH_White (jib + hoist + SN-07 ring + lift frame + 3 orbital weld heads), SH_GlowWhite (sparks + hot bead), SH_GlowRed (cooling bead)
  morph targets (mesh.extras.targetNames, all deltas in the jib's local frame = jib angle 0, i.e. over the stack):
    load_low   ring + rigging + hoist end down to the yard floor (pick-up)      load_seat  ring down 13.2 m onto the stack (seated)
    hop        load 1 m up            sway_px/nx/pz/nz  1 m lateral pendulum offset of the load (+x/-x/+z/-z, hoist top fixed)
    sweep_p/n  weld heads + sparks 0.6 m along / against the seam tangent
    sparks_a/b two spark-quad sets grown from the torch tips                     bead_white / bead_red  seam bead tube 0 -> 0.16 / 0.14 m          stow  ring + frame + heads collapsed into the hook (jib_return only)
  Glow states are geometry (collapsed to zero-area at weight 0), NOT animated emissive: emissive_strength animation needs
  KHR_animation_pointer, which gltfpack drops and GLTFLoader (r169) does not play. Morph weights are core glTF and do both.
The hall-door leaves are merged into ONE mesh 'Hall_Door_Leaves' (morph 'open', same 3.6 s clip) to free the draw the glow needs.
"""
import json, struct, sys, math
import numpy as np

FPS = 30.0
TN = ['load_low', 'load_seat', 'hop', 'sway_px', 'sway_nx', 'sway_pz', 'sway_nz', 'sweep_p', 'sweep_n', 'sparks_a', 'sparks_b', 'bead_white', 'bead_red', 'stow']
# every weight stays in [0, 1]: gltfpack clamps animated morph weights to [0, 1] (negative keys -> 0), so signed motions use +/- target pairs
SHIP_LIFT = 13.2; SEAM_Y = 0.48 + 19.4            # world y of the open stack top (TOP + SHIP_CUT[0])
HANG = 1.0                                          # ring_lower stops HANG m above the seat; ring_settle does the last metre
PICK = 140.0                                        # jib angle (deg) of the pick-up spot (yard floor behind FAB-01, >= 7.9 m clear)
PAL = {'SH_GlowWhite': ('#eaf8ff', 3.0), 'SH_GlowRed': ('#f25f5c', 3.0)}

def ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def seg(t, t0, t1, a, b): return a + (b - a) * ease((t - t0) / (t1 - t0)) if t1 > t0 else (b if t >= t1 else a)

# ---------------------------------------------------------------- clips: name -> (duration, loop, f(t) -> (jib_deg, weights[9]))
SPARK_A = [(0.6, 0.5), (1.6, 0.4), (2.5, 0.7), (4.0, 0.5), (5.0, 0.3), (6.1, 0.6), (7.4, 0.4), (8.3, 0.6), (9.6, 0.5), (10.6, 0.4), (11.5, 0.7), (12.9, 0.4), (13.8, 0.6), (14.9, 0.5)]
SPARK_B = [(0.9, 0.4), (2.0, 0.6), (3.3, 0.5), (4.5, 0.4), (5.6, 0.7), (6.9, 0.3), (7.8, 0.5), (9.1, 0.4), (10.1, 0.6), (11.2, 0.3), (12.3, 0.5), (13.4, 0.4), (14.4, 0.6)]
def burst(t, lst, ramp=1.0 / FPS):
    v = 0.0
    for s, d in lst:
        if s - ramp <= t <= s + d + ramp:
            v = max(v, min(1.0, (t - (s - ramp)) / ramp, ((s + d + ramp) - t) / ramp))
    return max(0.0, v)
S1 = (SHIP_LIFT - HANG) / SHIP_LIFT
def W(**k):
    w = [0.0] * len(TN)
    for n, v in k.items():
        if n in ('sway_x', 'sway_z', 'sweep'):
            p, q = (n[:-1] + 'p' + n[-1], n[:-1] + 'n' + n[-1]) if n != 'sweep' else ('sweep_p', 'sweep_n')
            w[TN.index(p)] = max(v, 0.0); w[TN.index(q)] = max(-v, 0.0)
        else: w[TN.index(n)] = v
    assert all(0.0 <= x <= 1.0 + 1e-9 for x in w), (k, w)
    return w
def c_lift(t):    # 9.0 s: ring rises from the yard floor to hook height; pendulum sway grows and dies out
    u = t / 9.0; env = math.sin(math.pi * u)
    return PICK, W(load_low=1 - ease(u), sway_x=0.35 * env * math.sin(2 * math.pi * t / 3.0), sway_z=0.18 * env * math.sin(2 * math.pi * t / 4.5))
def c_swing(t):   # 8.0 s: jib 140 -> 0 deg (smoothstep, peak 26.25 deg/s); load lags the angular acceleration (tangential sway) + small hoist hop
    u = t / 8.0; lag = 0.45 * (1 - 2 * u) * math.sin(math.pi * u)
    hop = 0.8 * math.sin(math.pi * u)   # hoist takes up ~0.8 m mid-swing: ring clears the z30 IS-1 handrail by > 1.17 m (0 at both ends)
    return PICK * (1 - ease(u)), W(hop=hop, sway_x=lag * TAN[0], sway_z=lag * TAN[2])
def c_lower(t):   # 6.0 s: 12.2 m descent to 1 m above the seat, no sway (centred through the z30 / z21 platforms)
    return 0.0, W(load_seat=S1 * ease(t / 6.0))
def c_settle(t):  # 3.0 s: last metre, touch-down at 1.8 s, 4 cm damped rebound, small line-up nudge; arc strike (bead 0 -> 1) 2.5-3.0 s
    if t <= 1.8: s = seg(t, 0, 1.8, S1, 1.0)
    elif t <= 2.2: s = seg(t, 1.8, 2.2, 1.0, 1 - 0.04 / SHIP_LIFT)
    elif t <= 2.6: s = seg(t, 2.2, 2.6, 1 - 0.04 / SHIP_LIFT, 1.0)
    else: s = 1.0
    nud = 0.06 * math.sin(math.pi * min(1.0, t / 1.8)) * math.sin(2 * math.pi * t / 1.8)
    return 0.0, W(load_seat=s, sway_x=nud * TAN[0], sway_z=nud * TAN[2], bead_white=seg(t, 2.5, 3.0, 0.0, 1.0))
def c_weld(t):    # 16.0 s LOOP: heads sweep +-0.6 m along the seam (2 cycles), spark bursts A/B, white bead (slight pulse)
    return 0.0, W(load_seat=1.0, sweep=math.sin(2 * math.pi * t / 8.0), sparks_a=burst(t, SPARK_A), sparks_b=burst(t, SPARK_B),
                  bead_white=0.96 + 0.04 * math.cos(2 * math.pi * t / 2.0))
def c_cool(t):    # 6.0 s: white-hot -> red-orange (white tube shrinks inside-out) -> steel (red tube shrinks, bare seam frame left)
    return 0.0, W(load_seat=1.0, bead_white=seg(t, 0.3, 2.6, 1.0, 0.0), bead_red=seg(t, 0.0, 0.4, 0.0, 1.0) if t < 2.6 else seg(t, 2.6, 5.6, 1.0, 0.0))
def c_return(t):  # 13.0 s: after seam_cool the GAME reveals the installed ring (stage swap) and this clip hides the jib's copy on frame 1:
    #   stow collapses ring + lift frame + weld heads into the hook block; hook rises out of the stack (0.1-2.5 s), jib swings 0 -> 140 over 2.5-10.5 s (peak 26.25 deg/s),
    #   hook drops to the pick-up spot; last frame: stow 1 -> 0 = the next ring appears on the yard floor behind FAB-01 (== ring_lift t=0)
    st = 0.0 if t <= 0.0 or t >= 13.0 - 1e-6 else 1.0
    return PICK * ease((t - 2.5) / 8.0), W(load_seat=seg(t, 0.1, 2.5, 1.0, 0.0), load_low=seg(t, 10.5, 12.5, 0.0, 1.0), stow=st)
CLIPS = [('ring_lift', 9.0, c_lift), ('jib_swing_in', 8.0, c_swing), ('ring_lower', 6.0, c_lower), ('ring_settle', 3.0, c_settle),
         ('ring_weld', 16.0, c_weld), ('seam_cool', 6.0, c_cool), ('jib_return', 13.0, c_return)]
TAN = [0.0, 0.0, 0.0]

# ---------------------------------------------------------------- GLB io
def read(p):
    b = open(p, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]; J = json.loads(b[20:20 + L])
    o = 20 + L; BL = struct.unpack('<I', b[o:o + 4])[0]; return J, bytearray(b[o + 8:o + 8 + BL])
CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}; NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
def acc(J, B, i):
    a = J['accessors'][i]; v = J['bufferViews'][a['bufferView']]; dt = CT[a['componentType']]; n = NC[a['type']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0); assert 'byteStride' not in v or v['byteStride'] == n * np.dtype(dt).itemsize
    return np.frombuffer(bytes(B[off:off + a['count'] * n * np.dtype(dt).itemsize]), dtype=dt).reshape(a['count'], n) if n > 1 else np.frombuffer(bytes(B[off:off + a['count'] * np.dtype(dt).itemsize]), dtype=dt).copy()
def put(J, B, arr, typ, target=None, minmax=False):
    arr = np.ascontiguousarray(arr); ct = {np.dtype(np.float32): 5126, np.dtype(np.uint32): 5125, np.dtype(np.uint16): 5123}[arr.dtype]
    while len(B) % 4: B.append(0)
    off = len(B); B.extend(arr.tobytes()); bv = {'buffer': 0, 'byteOffset': off, 'byteLength': arr.nbytes}
    if target: bv['target'] = target
    J['bufferViews'].append(bv); a = {'bufferView': len(J['bufferViews']) - 1, 'componentType': ct, 'count': int(arr.shape[0]), 'type': typ}
    if minmax: a['min'] = [float(x) for x in np.atleast_1d(arr.min(0))]; a['max'] = [float(x) for x in np.atleast_1d(arr.max(0))]
    J['accessors'].append(a); return len(J['accessors']) - 1
def write(p, J, B):
    while len(B) % 4: B.append(0)
    J['buffers'] = [{'byteLength': len(B)}]; js = json.dumps(J, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
    out = b'glTF' + struct.pack('<II', 2, 12 + 8 + len(js) + 8 + len(B)) + struct.pack('<I', len(js)) + b'JSON' + js + struct.pack('<I', len(B)) + b'BIN\x00' + bytes(B)
    open(p, 'wb').write(out)
def hexlin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]; return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
def node(J, name): return next(i for i, n in enumerate(J['nodes']) if n.get('name') == name)
def mat(J, name):
    for i, m in enumerate(J['materials']):
        if m['name'] == name: return i
    base, st = PAL[name]; c = hexlin(base); mx = max(c)
    J['materials'].append({'doubleSided': True, 'name': name, 'emissiveFactor': [x / mx for x in c], 'extensions': {'KHR_materials_emissive_strength': {'emissiveStrength': st * mx}},
                           'pbrMetallicRoughness': {'baseColorFactor': c + [1], 'metallicFactor': 0, 'roughnessFactor': 0.5}})
    return len(J['materials']) - 1

# ---------------------------------------------------------------- geometry helpers (flat-shaded triangles: pos, nrm, idx)
def tri_soup(tris):
    P = np.array([v for t in tris for v in t], np.float32).reshape(-1, 3); N = np.zeros_like(P)
    for i in range(0, len(P), 3):
        n = np.cross(P[i + 1] - P[i], P[i + 2] - P[i]); l = np.linalg.norm(n); N[i:i + 3] = n / l if l > 1e-9 else (0, 1, 0)
    return P, N
def box_between(a, b, w, h, up=(0, 1, 0)):
    a, b = np.array(a, float), np.array(b, float); d = b - a; d /= np.linalg.norm(d); s = np.cross(d, up)
    if np.linalg.norm(s) < 1e-6: s = np.cross(d, (1, 0, 0))
    s /= np.linalg.norm(s); u = np.cross(s, d)
    c = [p + s * sx * w / 2 + u * sy * h / 2 for p in (a, b) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    F = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return [(c[f[0]], c[f[1]], c[f[2]]) for f in F] + [(c[f[0]], c[f[2]], c[f[3]]) for f in F]
def torus(C, R, r, nu=64, nv=6):
    """returns (centre-line pts, tube offset dirs) per vertex of a triangle soup; vertex = line + r * dir"""
    L, D = [], []
    for i in range(nu):
        for j in range(nv):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j), (i + 1, j + 1), (i, j + 1)]
            for (a, bb) in q:
                ph = 2 * math.pi * a / nu; th = 2 * math.pi * bb / nv
                e = np.array([math.cos(ph), 0, math.sin(ph)]); L.append(C + e * R); D.append(e * math.cos(th) + np.array([0, 1, 0]) * math.sin(th))
    return np.array(L, np.float32), np.array(D, np.float32)

def build(J, B):
    global TAN
    jn = node(J, 'Crane_Jib'); P0 = np.array(J['nodes'][jn]['translation']); S = np.array(J['nodes'][node(J, 'Stand_Center')]['translation'])
    H = S - P0; H[1] = 0.0                                              # stack axis in the jib-local frame (jib angle 0)
    tl = np.array([H[2], 0, -H[0]]); TAN = list(tl / np.linalg.norm(tl))  # swing tangent at the hook (d/dtheta of R_y(theta) H)
    me = J['meshes'][J['nodes'][jn]['mesh']]; assert len(me['primitives']) == 1
    pr = me['primitives'][0]; pos = acc(J, B, pr['attributes']['POSITION']).astype(np.float32); nrm = acc(J, B, pr['attributes']['NORMAL']).astype(np.float32)
    idx = acc(J, B, pr['indices']).astype(np.uint32)
    wy = pos[:, 1] + P0[1]; rr = np.hypot(pos[:, 0] - H[0], pos[:, 2] - H[2])
    load = (wy < 48.0) & (rr < 6.5); ymin = wy[load].min()
    print('load verts', int(load.sum()), 'of', len(pos), 'ring bottom y', round(float(ymin), 3), 'max r', round(float(rr[load].max()), 2))
    global NRZ_TOP; NRZ_TOP = ymin + 5.7 + 0.2                             # ring top + lugs: below this = stowed on jib_return
    seam = np.array([H[0], SEAM_Y - P0[1], H[2]])                          # local seam centre (seated)
    hang = seam + np.array([0, SHIP_LIFT, 0])
    # --- 3 orbital weld heads on the lift frame (SH_White; ride with the ring), torch tips at the seam
    ANG = [50.0, 130.0, 230.0]
    head_tris, tips, tdir = [], [], []
    for a in ANG:
        e = np.array([math.cos(math.radians(a)), 0, math.sin(math.radians(a))]); t = np.array([-e[2], 0, e[0]])
        c0 = hang + e * 4.75 + np.array([0, 0.95, 0])
        head_tris += box_between(c0 - np.array([0, 0.5, 0]), c0 + np.array([0, 0.5, 0]), 0.8, 0.6, up=tuple(e))
        head_tris += box_between(c0 + np.array([0, 0.5, 0]), hang + e * 4.1 + np.array([0, 1.6, 0]), 0.2, 0.2)   # hanger to the frame
        tip = hang + e * 4.22 + np.array([0, 0.04, 0])
        head_tris += box_between(c0 - np.array([0, 0.45, 0]) - e * 0.1, tip, 0.14, 0.14)
        tips.append(tip - np.array([0, SHIP_LIFT, 0])); tdir.append((e, t))
    hp, hn = tri_soup(head_tris)
    nH = len(hp)
    pos2 = np.vstack([pos, hp]); nrm2 = np.vstack([nrm, hn]); idx2 = np.concatenate([idx, np.arange(len(pos), len(pos) + nH, dtype=np.uint32)])
    loadm = np.concatenate([load, np.ones(nH, bool)]); headm = np.concatenate([np.zeros(len(pos), bool), np.ones(nH, bool)])
    T = {n: np.zeros_like(pos2) for n in TN}
    T['load_low'][loadm, 1] = (0.18 + 0.02) - ymin
    T['load_seat'][loadm, 1] = -SHIP_LIFT
    T['hop'][loadm, 1] = 1.0
    stw = loadm & ((pos2[:, 1] + P0[1]) < NRZ_TOP); T['stow'][stw] = (np.array([H[0], NRZ_TOP - 0.3 - P0[1], H[2]]) - pos2[stw])
    print('stow verts', int(stw.sum()))
    T['sway_px'][loadm, 0] = 1.0; T['sway_nx'][loadm, 0] = -1.0; T['sway_pz'][loadm, 2] = 1.0; T['sway_nz'][loadm, 2] = -1.0
    hk = np.where(headm)[0]; per = nH // 3
    for k in range(3): T['sweep_p'][hk[k * per:(k + 1) * per]] = tdir[k][1] * 0.6; T['sweep_n'][hk[k * per:(k + 1) * per]] = -tdir[k][1] * 0.6
    # --- SH_GlowWhite: sparks (2 sets x 3 heads x 7 quads) + hot bead; SH_GlowRed: cooling bead
    rng = np.random.default_rng(7); gw_base, gw_full, gw_set, gw_head = [], [], [], []
    for si in range(2):
        for k, tip in enumerate(tips):
            e, t = tdir[k]
            for q in range(7):
                d = e * rng.uniform(0.2, 1.0) + t * rng.uniform(-1, 1) + np.array([0, rng.uniform(-1.0, 0.5), 0]); d /= np.linalg.norm(d)
                L = rng.uniform(0.5, 1.1); w = 0.06; side = np.cross(d, (0, 1, 0)); side = side / (np.linalg.norm(side) + 1e-9) * w
                a0, a1, b0, b1 = tip - side, tip + side, tip + d * L + side * 0.3, tip + d * L - side * 0.3
                for tri in ((a0, a1, b0), (a0, b0, b1)):
                    for v in tri: gw_base.append(tip); gw_full.append(v); gw_set.append(si); gw_head.append(k)
    gw_base = np.array(gw_base, np.float32); gw_full = np.array(gw_full, np.float32)
    bl, bd = torus(seam, 4.10, 0.16)
    nS = len(gw_base)
    gpos = np.vstack([gw_base, bl]); gT = {n: np.zeros_like(gpos) for n in TN}
    sp = gw_full - gw_base
    for si, nm in ((0, 'sparks_a'), (1, 'sparks_b')):
        m = np.array(gw_set) == si; gT[nm][:nS][m] = sp[m]
    for k in range(3): gT['sweep_p'][:nS][np.array(gw_head) == k] = tdir[k][1] * 0.6; gT['sweep_n'][:nS][np.array(gw_head) == k] = -tdir[k][1] * 0.6
    gT['bead_white'][nS:] = bd * 0.16
    gN = np.zeros_like(gpos); gN[:nS] = (0, 1, 0); gN[nS:] = bd
    rl, rd = torus(seam, 4.10, 0.14); rT = {n: np.zeros_like(rl) for n in TN}; rT['bead_red'][:] = rd * 0.14
    def prim(P, N, I, Tm, m):
        return {'attributes': {'POSITION': put(J, B, P.astype(np.float32), 'VEC3', 34962, True), 'NORMAL': put(J, B, N.astype(np.float32), 'VEC3', 34962)},
                'indices': put(J, B, I.astype(np.uint32), 'SCALAR', 34963), 'material': m,
                'targets': [{'POSITION': put(J, B, Tm[n].astype(np.float32), 'VEC3', 34962, True)} for n in TN]}
    me['primitives'] = [prim(pos2, nrm2, idx2, T, pr['material']),
                        prim(gpos, gN, np.arange(len(gpos), dtype=np.uint32), gT, mat(J, 'SH_GlowWhite')),
                        prim(rl, rd, np.arange(len(rl), dtype=np.uint32), rT, mat(J, 'SH_GlowRed'))]
    me['weights'] = c_lift(0.0)[1]; me['extras'] = {'targetNames': TN}
    q = math.radians(PICK) / 2; J['nodes'][jn]['rotation'] = [0, math.sin(q), 0, math.cos(q)]
    # --- hall door: merge the two leaves into one mesh + morph 'open' (same clip name/timing)
    dl, dr, dp = node(J, 'Hall_Door_L'), node(J, 'Hall_Door_R'), node(J, 'Hall_Door')
    an = next(a for a in J['animations'] if a['name'] == 'hall_door_open')
    tr = {c['target']['node']: an['samplers'][c['sampler']] for c in an['channels']}
    tim = acc(J, B, tr[dl]['input']); xl = acc(J, B, tr[dl]['output'])[:, 0]; xr = acc(J, B, tr[dr]['output'])[:, 0]
    PP, NN, II, DD = [], [], [], []; base = 0
    for ni, xs in ((dl, xl), (dr, xr)):
        p_ = J['meshes'][J['nodes'][ni]['mesh']]['primitives'][0]; v = acc(J, B, p_['attributes']['POSITION']).astype(np.float32)
        v = v + np.array(J['nodes'][ni]['translation'], np.float32); d = np.zeros_like(v); d[:, 0] = xs.max() - xs.min() if xs[0] > 0 else -(xs.max() - xs.min())
        PP.append(v); NN.append(acc(J, B, p_['attributes']['NORMAL'])); II.append(acc(J, B, p_['indices']).astype(np.uint32) + base); DD.append(d); base += len(v)
        dm = p_['material']
    wdoor = (np.abs(xl - xl[0]) / (np.abs(xl).max() - np.abs(xl).min())).astype(np.float32)
    J['meshes'].append({'name': 'Hall_Door_Leaves', 'primitives': [{'attributes': {'POSITION': put(J, B, np.vstack(PP), 'VEC3', 34962, True), 'NORMAL': put(J, B, np.vstack(NN).astype(np.float32), 'VEC3', 34962)},
                        'indices': put(J, B, np.concatenate(II), 'SCALAR', 34963), 'material': dm, 'targets': [{'POSITION': put(J, B, np.vstack(DD), 'VEC3', 34962, True)}]}],
                        'weights': [0.0], 'extras': {'targetNames': ['open']}})
    J['nodes'][dl] = {'name': 'Hall_Door_Leaves', 'mesh': len(J['meshes']) - 1}
    J['nodes'][dr] = {'name': '_unused_leaf_R'}; J['nodes'][dp]['children'] = [dl]
    ti = put(J, B, tim.astype(np.float32), 'SCALAR', None, True); wo = put(J, B, wdoor, 'SCALAR')
    an['samplers'] = [{'input': ti, 'output': wo, 'interpolation': 'LINEAR'}]; an['channels'] = [{'sampler': 0, 'target': {'node': dl, 'path': 'weights'}}]
    print('door open dx', round(float(xl.max() - xl.min()), 3), 'keys', len(tim))
    # --- clips (30 Hz LINEAR, first key t=0, last key t=dur; ring_weld last key == first key exactly)
    J['animations'] = [a for a in J['animations'] if a['name'] != 'crane_jib_swing']
    for name, dur, f in CLIPS:
        n = int(round(dur * FPS)); ts = np.array([i / FPS for i in range(n + 1)], np.float32); ts[-1] = dur
        ang, wt = [], []
        for t in ts: a, w = f(float(t)); ang.append(a); wt.append(w)
        if name == 'ring_weld': ang[-1] = ang[0]; wt[-1] = wt[0]
        qs = np.array([[0, math.sin(math.radians(a) / 2), 0, math.cos(math.radians(a) / 2)] for a in ang], np.float32)
        ti = put(J, B, ts, 'SCALAR', None, True)
        J['animations'].append({'name': name, 'samplers': [{'input': ti, 'output': put(J, B, qs, 'VEC4'), 'interpolation': 'LINEAR'},
                                                           {'input': ti, 'output': put(J, B, np.array(wt, np.float32).reshape(-1), 'SCALAR'), 'interpolation': 'LINEAR'}],
                                'channels': [{'sampler': 0, 'target': {'node': jn, 'path': 'rotation'}}, {'sampler': 1, 'target': {'node': jn, 'path': 'weights'}}]})
    if 'KHR_materials_emissive_strength' not in J.get('extensionsUsed', []): J.setdefault('extensionsUsed', []).append('KHR_materials_emissive_strength')
    return jn

def bake_pose(J, B, jn, clip, t):
    """static proof GLB: Crane_Jib morphs + angle baked at (clip, t); morph targets / animations removed"""
    f = dict((c[0], c[2]) for c in CLIPS)[clip]; a, w = f(t)
    me = J['meshes'][J['nodes'][jn]['mesh']]
    for p in me['primitives']:
        P = acc(J, B, p['attributes']['POSITION']).astype(np.float32).copy()
        for k, tg in enumerate(p['targets']): P += w[k] * acc(J, B, tg['POSITION'])
        p['attributes']['POSITION'] = put(J, B, P, 'VEC3', 34962, True); del p['targets']
    me.pop('weights', None); me.pop('extras', None); q = math.radians(a) / 2; J['nodes'][jn]['rotation'] = [0, math.sin(q), 0, math.cos(q)]
    for m in J['meshes']:
        if m['name'] == 'Hall_Door_Leaves': [p.pop('targets', None) for p in m['primitives']]; m.pop('weights', None); m.pop('extras', None)
    J['animations'] = []

if __name__ == '__main__':
    J, B = read(sys.argv[1]); jn = build(J, B)
    if '--pose' in sys.argv:
        c, t = sys.argv[sys.argv.index('--pose') + 1].split(':'); bake_pose(J, B, jn, c, float(t))
    write(sys.argv[2], J, B); print('WROTE', sys.argv[2])
