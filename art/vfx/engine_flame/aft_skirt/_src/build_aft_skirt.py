# Planet Stack - AFT SKIRT module: N-engine ring (6..11) + 4 folding landing legs in flush bays. Art & Animation 10/24/2026, original design.
# python3 build_aft_skirt.py <out_dir>  -> aft_skirt_N06.glb .. aft_skirt_N11.glb + aft_skirt_layout.json
# ONE skinned mesh, ONE material (vertex colours: hull-white / steel / graphite / bell palettes) = 1 draw call for ring + band + gear.
# Joints: Aft_Skirt_Root, Gear_Leg_k (hip), Gear_Knee_k, Gear_Foot_k (shock slide), Gear_Door_ka / Gear_Door_kb (k = 0..3).
# Markers: Engine_Nozzle_0..N-1 (bell exit, local -Y = thrust) + layout in extras. Clips: Gear_Retract, Gear_Deploy (30 fps, baked).
# Frame = the ship build frame in glTF axes (Y up, origin = ship base centre = Engine_Ring_Mount, x = cos a, z = -sin a), metres.
import json, math, struct, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import gear_pose as GP
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
HULL_R, Z_AFT, Z_BODY = 4.0, 2.4, 3.4
RING_R, EXIT_R0, EXIT_Y, PLATE_Y, PAD_YAW = 3.05, 0.84, 0.9, 2.86, 60.0
BAND_R, BAND_Y0, BAND_Y1, BAND_TOP = GP.BAND_R, 2.15, 6.45, 6.85
BELL_PROF = [(0.84, 0.9), (0.76, 1.35), (0.6, 1.9), (0.44, 2.4), (0.33, 2.78)]
def srgb(h): h = h.lstrip('#'); return tuple(((int(h[i:i + 2], 16) / 255) ** 2.2) for i in (0, 2, 4))
COL = dict(bell=srgb('#6a6e75'), hot=srgb('#9a7650'), lip=srgb('#c4c9cf'), plate=srgb('#34363c'), gimb=srgb('#80848b'), ink=srgb('#0c0c0e'), inner=srgb('#101012'),
           hull=srgb('#d9dcdf'), hull_s=srgb('#c3c7cc'), graph=srgb('#4a4d54'), liner=srgb('#1d1f24'), steel=srgb('#9ea4ab'), steel_d=srgb('#6c7178'),
           chrome=srgb('#d4d8dc'), amber=srgb('#d08a1c'), pad=srgb('#7d8289'))
def ring_layout(N):
    chord = 2 * RING_R * math.sin(math.pi / N); er = min(EXIT_R0, 0.46 * chord)
    ph = 90.0 + (90.0 / N if N % 2 == 0 else 0.0) - PAD_YAW
    angs = [math.radians(ph + 360.0 * k / N) for k in range(N)]
    return dict(N=N, ring_r=RING_R, exit_r=round(er, 4), phase_deg=ph, chord_m=round(chord, 4),
                nozzles=[dict(name=f'Engine_Nozzle_{k}', pos=[round(RING_R * math.cos(a), 4), EXIT_Y, round(-RING_R * math.sin(a), 4)], dir=[0, -1, 0], exit_r=round(er, 4)) for k, a in enumerate(angs)])
class Geo:
    def __init__(s): s.P, s.N, s.C, s.J, s.I = [], [], [], [], []
    def tri(s, a, b, c): s.I.extend((a, b, c))
    def lathe(s, prof, cx, cz, col, segs, j=0, flip=False, a0=0.0, a1=2 * math.pi):
        base = len(s.P); n = len(prof)
        for k, (r, y) in enumerate(prof):
            r0, y0 = prof[max(k - 1, 0)]; r1, y1 = prof[min(k + 1, n - 1)]; nr, ny = (y1 - y0), -(r1 - r0); L = math.hypot(nr, ny) or 1; nr, ny = nr / L, ny / L
            if flip: nr, ny = -nr, -ny
            c = col[k] if isinstance(col, list) else col
            for i in range(segs + 1):
                a = a0 + (a1 - a0) * i / segs; ca, sa = math.cos(a), -math.sin(a)
                s.P.append((cx + r * ca, y, cz + r * sa)); s.N.append((nr * ca, ny, nr * sa)); s.C.append(c); s.J.append(j)
        for k in range(n - 1):
            for i in range(segs):
                a = base + k * (segs + 1) + i; b = a + segs + 1
                if flip: s.I.extend((a, b, a + 1, a + 1, b, b + 1))      # (glTF x = cos a, z = -sin a: this order faces inward)
                else: s.I.extend((a, a + 1, b, a + 1, b + 1, b))
    def quad(s, p, col, j):    # p: 4 corners CCW seen from outside
        p = [np.array(q, float) for q in p]; n = np.cross(p[1] - p[0], p[2] - p[0]); n /= np.linalg.norm(n) + 1e-9; b = len(s.P)
        for q in p: s.P.append(tuple(q)); s.N.append(tuple(n)); s.C.append(col); s.J.append(j)
        s.I.extend((b, b + 1, b + 2, b, b + 2, b + 3))
    def box(s, c, ax, size, col, j):   # ax: 3 unit axes (u, v, w), size: half extents
        c = np.array(c, float); u, v, w = [np.array(a, float) for a in ax]; hu, hv, hw = size
        for sgn, A, B, C_, h1, h2, h3 in ((1, u, v, w, hu, hv, hw), (-1, u, w, v, hu, hw, hv), (1, v, w, u, hv, hw, hu), (-1, v, u, w, hv, hu, hw), (1, w, u, v, hw, hu, hv), (-1, w, v, u, hw, hv, hu)):
            f = c + sgn * A * h1; s.quad([f - B * h2 - C_ * h3, f + B * h2 - C_ * h3, f + B * h2 + C_ * h3, f - B * h2 + C_ * h3][::(1 if sgn > 0 else 1)], col, j)
    def tube(s, p0, p1, r, col, j, segs=12, r1=None):
        p0, p1 = np.array(p0, float), np.array(p1, float); d = p1 - p0; L = np.linalg.norm(d); d /= L
        a = np.array([1, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 0, 1]); u = np.cross(d, a); u /= np.linalg.norm(u); v = np.cross(d, u); b = len(s.P); r1 = r if r1 is None else r1
        for k, (pp, rr) in enumerate(((p0, r), (p1, r1))):
            for i in range(segs + 1):
                t = 2 * math.pi * i / segs; nn = u * math.cos(t) + v * math.sin(t); s.P.append(tuple(pp + nn * rr)); s.N.append(tuple(nn)); s.C.append(col); s.J.append(j)
        for i in range(segs): a_ = b + i; b_ = a_ + segs + 1; s.I.extend((a_, a_ + 1, b_, a_ + 1, b_ + 1, b_))
        for pp, sg in ((p0, -1), (p1, 1)):   # caps
            c0 = len(s.P); s.P.append(tuple(pp)); s.N.append(tuple(d * sg)); s.C.append(col); s.J.append(j); ring0 = b if sg < 0 else b + segs + 1
            for i in range(segs): s.I.extend((c0, ring0 + i + 1, ring0 + i) if sg < 0 else (c0, ring0 + i, ring0 + i + 1))
def build(N):
    g = Geo(); L = ring_layout(N); s = L['exit_r'] / EXIT_R0; legs = GP.legs()
    # ---- engines + thrust plate (joint 0)
    g.lathe([(HULL_R - 0.02, PLATE_Y), (0.0, PLATE_Y)], 0, 0, COL['plate'], 96)
    for nz in L['nozzles']:
        x, _, z = nz['pos']; prof = [(r * s, EXIT_Y + (y - EXIT_Y) * (0.85 + 0.15 * s)) for r, y in BELL_PROF] + [(0.33 * s, PLATE_Y)]
        g.lathe(prof, x, z, [COL['bell']] * 3 + [COL['hot']] * 2 + [COL['gimb']], 32)
        g.lathe([(p[0] - 0.035 * s, p[1]) for p in prof[:5]], x, z, COL['inner'], 32, flip=True)
        g.lathe([(EXIT_R0 * s + 0.03, EXIT_Y + 0.07), (EXIT_R0 * s + 0.03, EXIT_Y - 0.005), (EXIT_R0 * s - 0.04, EXIT_Y - 0.005)], x, z, COL['lip'], 32)
        g.lathe([(0.75 * s, 1.5), (0.70 * s, 1.56)], x, z, COL['lip'], 32)
        g.lathe([(0.0, 2.55), (0.30 * s, 2.56), (0.30 * s, 2.78)], x, z, COL['ink'], 24, flip=True)
    # ---- band (hull-white, graphite bottom): solid between bays, cut out at the 4 bays
    bays = [(lg['a'], GP.BAY_HW) for lg in legs]
    g.lathe([(BAND_R, BAND_Y0), (HULL_R - 0.02, BAND_Y0)], 0, 0, COL['graph'], 192)                       # bottom annulus
    g.lathe([(BAND_R + 0.03, BAND_Y0 - 0.02), (BAND_R + 0.03, BAND_Y0 + 0.12)], 0, 0, COL['lip'], 192)     # bright lip
    g.lathe([(BAND_R, GP.BAY_Y1), (BAND_R, BAND_Y1), (HULL_R + 0.02, BAND_TOP)], 0, 0, [COL['hull'], COL['hull'], COL['hull']], 192)   # top + chamfer
    g.lathe([(BAND_R, BAND_Y0), (BAND_R, GP.BAY_Y0)], 0, 0, COL['graph'], 192)                             # graphite base row
    # middle row with gaps (between bays)
    edges = sorted([(a - hw, a + hw) for a, hw in bays])
    for k in range(4):
        a0 = edges[k][1]; a1 = edges[(k + 1) % 4][0] + (2 * math.pi if k == 3 else 0)
        g.lathe([(BAND_R, GP.BAY_Y0), (BAND_R, GP.BAY_Y1)], 0, 0, COL['hull'], 48, a0=a0, a1=a1)
    # ---- per leg: bay liner + walls (joint 0), doors (joints), leg parts (joints)
    for k, lg in enumerate(legs):
        a, n, t = lg['a'], np.array(lg['n']), np.array(lg['t'])
        g.lathe([(GP.LINER_R, GP.BAY_Y0), (GP.LINER_R, GP.BAY_Y1)], 0, 0, COL['liner'], 6, a0=a + GP.BAY_HW, a1=a - GP.BAY_HW)   # faces outward
        for sg in (-1, 1):   # side walls
            aa = a + sg * GP.BAY_HW; e = np.array([math.cos(aa), 0, -math.sin(aa)])
            q = [e * GP.LINER_R + [0, GP.BAY_Y0, 0], e * BAND_R + [0, GP.BAY_Y0, 0], e * BAND_R + [0, GP.BAY_Y1, 0], e * GP.LINER_R + [0, GP.BAY_Y1, 0]]
            g.quad(q if sg > 0 else q[::-1], COL['liner'], 0)
        for yy, sg in ((GP.BAY_Y0, 1), (GP.BAY_Y1, -1)):   # sill / header
            pa, pb = [np.array([math.cos(x), 0, -math.sin(x)]) for x in (a - GP.BAY_HW, a + GP.BAY_HW)]
            q = [pa * GP.LINER_R + [0, yy, 0], pb * GP.LINER_R + [0, yy, 0], pb * BAND_R + [0, yy, 0], pa * BAND_R + [0, yy, 0]]
            g.quad(q if sg > 0 else q[::-1], COL['steel_d'], 0)
        # doors: two curved leaves, hinged on the bay's vertical edges, flush with the band (outer skin at BAND_R)
        for side, jn in (('a', lg['j_door_a']), ('b', lg['j_door_b'])):
            sg = -1 if side == 'a' else 1; ea, eb = (a + sg * GP.BAY_HW, a + sg * 0.003)
            lo, hi = min(ea, eb), max(ea, eb)
            # notch on the meeting edge where the locked upper strut passes the skin (y NOTCH_Y0..NOTCH_Y1), so the doors close round a deployed leg
            nlo, nhi = (lo, hi - GP.NOTCH_HW) if side == 'a' else (lo + GP.NOTCH_HW, hi)
            for (y0, y1, l0, l1) in ((GP.BAY_Y0 + 0.01, GP.NOTCH_Y0, lo, hi), (GP.NOTCH_Y0, GP.NOTCH_Y1, nlo, nhi), (GP.NOTCH_Y1, GP.BAY_Y1 - 0.01, lo, hi)):
                g.lathe([(BAND_R, y0), (BAND_R, y1)], 0, 0, COL['hull_s'], 8, j=jn, a0=l0, a1=l1)
                g.lathe([(BAND_R - 0.03, y1), (BAND_R - 0.03, y0)], 0, 0, COL['liner'], 8, j=jn, a0=l0, a1=l1)
            ec = nhi if side == 'a' else nlo; e = np.array([math.cos(ec), 0, -math.sin(ec)])
            q = [e * (BAND_R - 0.03) + [0, GP.NOTCH_Y0, 0], e * BAND_R + [0, GP.NOTCH_Y0, 0], e * BAND_R + [0, GP.NOTCH_Y1, 0], e * (BAND_R - 0.03) + [0, GP.NOTCH_Y1, 0]]
            g.quad(q if side == 'a' else q[::-1], COL['steel_d'], jn)   # notch edge
            for yy, (l0, l1) in ((GP.NOTCH_Y0, (nhi, hi) if side == 'a' else (lo, nlo)), (GP.NOTCH_Y1, (nhi, hi) if side == 'a' else (lo, nlo))):
                g.lathe([(BAND_R - 0.03, yy), (BAND_R, yy)] if yy < 5.4 else [(BAND_R, yy), (BAND_R - 0.03, yy)], 0, 0, COL['steel_d'], 2, j=jn, a0=l0, a1=l1)
            for yy in (GP.BAY_Y0 + 0.01, GP.BAY_Y1 - 0.01):
                g.lathe([(BAND_R, yy), (BAND_R - 0.03, yy)] if yy > 3 else [(BAND_R - 0.03, yy), (BAND_R, yy)], 0, 0, COL['hull_s'], 8, j=jn, a0=lo, a1=hi)
            g.lathe([(BAND_R + 0.004, GP.BAY_Y1 - 0.25), (BAND_R + 0.004, GP.BAY_Y1 - 0.18)], 0, 0, COL['amber'], 8, j=jn, a0=lo, a1=hi)   # hazard stripe
        # leg (authored in the rest pose = deployed, locked, shock compressed)
        H, K, F, off = np.array(lg['H']), np.array(lg['K']), np.array(lg['F']), np.array(lg['off'])
        jl, jk, jf = lg['j_leg'], lg['j_knee'], lg['j_foot']; d = (F - H) / np.linalg.norm(F - H)
        g.box(H, (t, n, np.cross(t, n)), (0.16, 0.09, 0.12), COL['steel_d'], jl)               # hip clevis
        g.tube(H, K - d * 0.05, GP.R_UP, COL['steel'], jl)                                     # upper strut
        g.tube(H + d * 0.4, H + d * 1.6, GP.R_UP + 0.02, COL['hull_s'], jl)                    # upper fairing sleeve
        g.box(K + off * 0.5, (t, d, np.cross(t, d)), (0.13 + 0.085, 0.10, 0.085), COL['steel_d'], jk)   # knee block (spans both struts)
        g.tube(K + off, K + off + d * 1.75, GP.R_LO, COL['steel'], jk)                        # lower outer tube (shock body)
        g.tube(K + off + d * 0.25, K + off + d * 0.45, GP.R_LO + 0.015, COL['amber'], jk)     # lock collar
        Ft = F + off; g.tube(K + off + d * 1.7, Ft + np.array([0, 0.10, 0]), GP.R_LO - 0.03, COL['chrome'], jf)   # shock piston (slides with the foot)
        g.lathe([(0.0, F[1] + 0.12), (GP.PAD_R * 0.55, F[1] + 0.12), (GP.PAD_R, F[1] + 0.04), (GP.PAD_R, F[1]), (0.0, F[1])], Ft[0], Ft[2], COL['pad'], 20, j=jf)   # foot pad
    return g, L, legs
def mat_t(p): m = np.eye(4); m[:3, 3] = p; return m
def glb(path, g, L, legs, anims):
    pos = np.array(g.P, np.float32); nor = np.array(g.N, np.float32); nor /= np.linalg.norm(nor, axis=1, keepdims=True) + 1e-9
    col = np.concatenate([np.round(np.array(g.C) ** (1 / 2.2) * 255), np.full((len(g.C), 1), 255)], 1).astype(np.uint8)
    jnt = np.zeros((len(g.J), 4), np.uint8); jnt[:, 0] = g.J; wts = np.zeros((len(g.J), 4), np.uint8); wts[:, 0] = 255
    idx = np.array(g.I, np.uint16 if len(g.P) < 65535 else np.uint32)
    # nodes: 0 root, then joints, then markers, then the skinned mesh node
    joints = GP.joint_list(legs)                      # [(name, parent_index_in_joints or -1, world_pos)]
    nodes = []; jn0 = 1
    for name, par, wp in joints:
        lp = np.array(wp) - (np.array(joints[par][2]) if par >= 0 else 0)
        nodes.append(dict(name=name, translation=[float(x) for x in lp], extras=dict(role='gear_joint' if name.startswith('Gear') else 'root_joint')))
    for i, (name, par, wp) in enumerate(joints):
        ch = [j + jn0 for j, (_, p, _) in enumerate(joints) if p == i]
        if ch: nodes[i]['children'] = ch
    mk0 = len(nodes) + 1
    for nz in L['nozzles']: nodes.append(dict(name=nz['name'], translation=nz['pos'], extras=dict(exit_r=nz['exit_r'], thrust_dir=nz['dir'])))
    meshnode = len(nodes) + 1; nodes.append(dict(name=f'Aft_Skirt_N{L["N"]:02d}_Mesh', mesh=0, skin=0))
    extras = dict(engine_ring=L, gear=GP.export_meta(legs), frame='ship build frame, Y up, origin = ship base centre (Engine_Ring_Mount), m', hull_base_diameter_m=2 * HULL_R)
    root = dict(name='Aft_Skirt', children=[jn0] + list(range(mk0, mk0 + L['N'])) + [meshnode], extras=extras)
    nodes = [root] + nodes
    # fix child indices (+1 for the root we just put in front) — joint children were already offset by jn0
    for i, n in enumerate(nodes[1:1 + len(joints)]):
        pass
    ibm = np.stack([np.linalg.inv(mat_t(wp)).T.reshape(-1) for _, _, wp in joints]).astype(np.float32)   # column-major
    blobs = [pos.tobytes(), nor.tobytes(), col.tobytes(), jnt.tobytes(), wts.tobytes(), idx.tobytes(), ibm.tobytes()]
    accessors = [dict(bufferView=0, componentType=5126, count=len(pos), type='VEC3', min=pos.min(0).tolist(), max=pos.max(0).tolist()),
                 dict(bufferView=1, componentType=5126, count=len(pos), type='VEC3'), dict(bufferView=2, componentType=5121, normalized=True, count=len(pos), type='VEC4'),
                 dict(bufferView=3, componentType=5121, count=len(pos), type='VEC4'), dict(bufferView=4, componentType=5121, normalized=True, count=len(pos), type='VEC4'),
                 dict(bufferView=5, componentType=5123 if idx.dtype == np.uint16 else 5125, count=len(idx), type='SCALAR'),
                 dict(bufferView=6, componentType=5126, count=len(joints), type='MAT4')]
    animations = []
    for aname, (times, chans) in anims.items():
        tb = np.array(times, np.float32); blobs.append(tb.tobytes()); ti = len(accessors)
        accessors.append(dict(bufferView=len(blobs) - 1, componentType=5126, count=len(tb), type='SCALAR', min=[float(tb.min())], max=[float(tb.max())]))
        samplers, channels = [], []
        for (jname, path_, vals) in chans:
            vb = np.array(vals, np.float32); blobs.append(vb.tobytes()); vi = len(accessors)
            accessors.append(dict(bufferView=len(blobs) - 1, componentType=5126, count=len(vb), type='VEC4' if path_ == 'rotation' else 'VEC3'))
            samplers.append(dict(input=ti, output=vi, interpolation='LINEAR')); node_i = 1 + [j[0] for j in joints].index(jname)
            channels.append(dict(sampler=len(samplers) - 1, target=dict(node=node_i, path=path_)))
        animations.append(dict(name=aname, samplers=samplers, channels=channels, extras=dict(fps=30, t0_note=GP.CLIP_NOTES[aname])))
    offs = []; o = 0
    for b in blobs: offs.append(o); o += (len(b) + 3) & ~3
    bin_ = b''.join(b + b'\0' * (((len(b) + 3) & ~3) - len(b)) for b in blobs)
    views = [dict(buffer=0, byteOffset=offs[i], byteLength=len(blobs[i])) for i in range(len(blobs))]
    for i in range(5): views[i]['target'] = 34962
    views[5]['target'] = 34963
    gl = dict(asset=dict(version='2.0', generator='planet-stack build_aft_skirt.py'), scene=0, scenes=[dict(nodes=[0], extras=extras)], nodes=nodes,
              skins=[dict(name='Aft_Skirt_Skin', joints=list(range(1, 1 + len(joints))), inverseBindMatrices=6, skeleton=1)],
              meshes=[dict(name=f'Aft_Skirt_N{L["N"]:02d}', primitives=[dict(attributes=dict(POSITION=0, NORMAL=1, COLOR_0=2, JOINTS_0=3, WEIGHTS_0=4), indices=5, material=0)])],
              materials=[dict(name='M_AftSkirt', pbrMetallicRoughness=dict(baseColorFactor=[1, 1, 1, 1], metallicFactor=0.35, roughnessFactor=0.5))],
              animations=animations, buffers=[dict(byteLength=len(bin_))], bufferViews=views, accessors=accessors)
    js = json.dumps(gl, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
    data = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(bin_), 0x004E4942) + bin_
    open(path, 'wb').write(data); return len(pos), len(idx) // 3, len(data)
allL = {}
for N in range(6, 12):
    g, L, legs = build(N); anims = GP.bake_clips(legs)
    v, t, b = glb(f'{OUT}/aft_skirt_N{N:02d}.glb', g, L, legs, anims); L.update(verts=v, tris=t, bytes=b); allL[N] = L; print(N, v, t, b)
json.dump(dict(rings=allL, gear=GP.export_meta(GP.legs())), open(f'{OUT}/aft_skirt_layout.json', 'w'), indent=1)
