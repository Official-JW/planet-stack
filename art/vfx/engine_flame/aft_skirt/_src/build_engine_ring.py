# Parametric engine ring for the Planet Stack cargo ship (original design, Art & Animation 10/24/2026).
# python3 build_engine_ring.py <out_dir>  -> engine_ring_N06.glb .. engine_ring_N11.glb + layout.json
# One merged mesh (vertex colours, 1 material = 1 draw call) + Engine_Nozzle_0..N-1 marker nodes + layout in extras.
# Frame = ship-local glTF frame of the Lv1 hull build (Y up, origin = ship base on the pad, metres, true scale):
# hull R 4.0 (8.0 m dia), aft skirt R 4.18, Z_AFT 2.4, Z_BODY 3.4, legs at 0/60/../300 deg (build angle a: x=cos a, z=-sin a).
import json, math, struct, sys, os
import numpy as np
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
HULL_R, SKIRT_R, Z_AFT, Z_BODY = 4.0, 4.18, 2.4, 3.4
RING_R = 3.05            # one ring radius for every N; bells shrink a little when the chord gets tight
EXIT_R0, EXIT_Y = 0.84, 0.9
BELL_PROF = [(0.84, 0.9), (0.76, 1.35), (0.6, 1.9), (0.44, 2.4), (0.33, 2.78)]   # outer skin (Lv1 bell, starter_ship BELL_PROF)
PLATE_Y = 2.86
PAD_YAW = 60.0          # launch_pad_game.glb yaws Ship_Placeholder +60 deg about Y
def layout(N):
    chord = 2 * RING_R * math.sin(math.pi / N); er = min(EXIT_R0, 0.46 * chord)
    # clocking: the pad yaws the hull +60 deg and the station camera looks along -Z. Engine 0 sits at world angle 90 + (90/N if N even)
    # so no two bells line up front-to-back in the fixed camera (every plume gets its own column, diamonds don't stack).
    ph = 90.0 + (90.0 / N if N % 2 == 0 else 0.0) - PAD_YAW
    angs = [math.radians(ph + 360.0 * k / N) for k in range(N)]
    return dict(N=N, ring_r=RING_R, exit_r=round(er, 4), phase_deg=ph, chord_m=round(chord, 4),
                nozzles=[dict(name=f'Engine_Nozzle_{k}', pos=[round(RING_R * math.cos(a), 4), EXIT_Y, round(-RING_R * math.sin(a), 4)], dir=[0, -1, 0], exit_r=round(er, 4)) for k, a in enumerate(angs)])
P, Nn, C, I = [], [], [], []
def lathe(prof, cx, cz, col, segs, cap=False, flip=False):
    """revolve (r, y) profile around a vertical axis; per-ring colour list or single colour"""
    base = len(P); n = len(prof)
    for j, (r, y) in enumerate(prof):
        # normal from profile tangent
        r0, y0 = prof[max(j - 1, 0)]; r1, y1 = prof[min(j + 1, n - 1)]; tr, ty = r1 - r0, y1 - y0; nr, ny = ty, -tr; L = math.hypot(nr, ny) or 1; nr, ny = nr / L, ny / L
        if flip: nr, ny = -nr, -ny
        c = col[j] if isinstance(col, list) else col
        for i in range(segs + 1):
            a = 2 * math.pi * i / segs; ca, sa = math.cos(a), math.sin(a)
            P.append((cx + r * ca, y, cz + r * sa)); Nn.append((nr * ca, ny, nr * sa)); C.append(c)
    for j in range(n - 1):
        for i in range(segs):
            a = base + j * (segs + 1) + i; b = a + segs + 1
            I.extend((a, b, a + 1, a + 1, b, b + 1) if not flip else (a, a + 1, b, a + 1, b + 1, b))
def srgb(h): h = h.lstrip('#'); return tuple(((int(h[i:i + 2], 16) / 255) ** 2.2) for i in (0, 2, 4))
BELL_C, HOT_C, LIP_C, SKIRT_C, PLATE_C, GIMB_C = srgb('#6a6e75'), srgb('#9a7650'), srgb('#c4c9cf'), srgb('#585c64'), srgb('#34363c'), srgb('#80848b')
def build(N):
    P.clear(); Nn.clear(); C.clear(); I.clear(); L = layout(N); s = L['exit_r'] / EXIT_R0
    # skirt: graphite, slightly flared, wraps the ring (matches the hull's aft skirt R 4.18, overlaps Z_AFT..Z_BODY)
    lathe([(SKIRT_R + 0.06, Z_AFT - 0.25), (SKIRT_R + 0.06, Z_AFT + 0.7), (SKIRT_R + 0.02, Z_AFT + 0.9)], 0, 0, SKIRT_C, 96)   # sits 6 cm proud of the hull skirt (no z-fight)
    lathe([(SKIRT_R + 0.06, Z_AFT - 0.25), (SKIRT_R - 0.14, Z_AFT - 0.25)], 0, 0, LIP_C, 96)          # bright lip ring
    lathe([(SKIRT_R - 0.14, Z_AFT - 0.25), (SKIRT_R - 0.14, PLATE_Y)], 0, 0, SKIRT_C, 96, flip=True) # inner wall
    lathe([(SKIRT_R - 0.14, PLATE_Y), (0.0, PLATE_Y)], 0, 0, PLATE_C, 96)                             # thrust plate (closes the old engine bay)
    for nz in L['nozzles']:
        x, _, z = nz['pos']
        prof = [(r * s, EXIT_Y + (y - EXIT_Y) * (0.85 + 0.15 * s)) for r, y in BELL_PROF] + [(0.33 * s, PLATE_Y)]
        cols = [BELL_C, BELL_C, BELL_C, HOT_C, HOT_C, GIMB_C]
        lathe(prof, x, z, cols, 32)
        lathe([(p[0] - 0.035 * s, p[1]) for p in prof[:5]], x, z, [srgb('#101012')] * 5, 32, flip=True)   # inner wall (dark)
        lathe([(EXIT_R0 * s + 0.03, EXIT_Y + 0.07), (EXIT_R0 * s + 0.03, EXIT_Y - 0.005), (EXIT_R0 * s - 0.04, EXIT_Y - 0.005)], x, z, LIP_C, 32)   # lip
        lathe([(0.75 * s, 1.5), (0.70 * s, 1.56)], x, z, LIP_C, 32)                                              # band
        lathe([(0.0, 2.55), (0.30 * s, 2.56), (0.30 * s, 2.78)], x, z, srgb('#0c0c0e'), 24, flip=True)            # throat
    return L
def glb(path, L):
    pos = np.array(P, np.float32); nor = np.array(Nn, np.float32); nor /= np.linalg.norm(nor, axis=1, keepdims=True) + 1e-9
    col = np.concatenate([np.round(np.array(C) ** (1 / 2.2) * 255), np.full((len(C), 1), 255)], 1).astype(np.uint8); idx = np.array(I, np.uint16 if len(P) < 65535 else np.uint32)
    blobs = [pos.tobytes(), nor.tobytes(), col.tobytes(), idx.tobytes()]; offs = []; o = 0
    for b in blobs: offs.append(o); o += (len(b) + 3) & ~3
    bin_ = b''.join(b + b'\0' * (((len(b) + 3) & ~3) - len(b)) for b in blobs)
    nodes = [dict(name=f'Engine_Ring_N{L["N"]:02d}', mesh=0, extras=dict(role='engine_ring_mesh'))]
    for nz in L['nozzles']: nodes.append(dict(name=nz['name'], translation=nz['pos'], extras=dict(exit_r=nz['exit_r'], thrust_dir=nz['dir'])))
    root = dict(name=f'Engine_Ring_{L["N"]}', children=list(range(len(nodes))), extras=dict(engine_ring=L, frame='ship-local, Y up, origin = ship base (pad deck), m', hull_base_diameter_m=2 * HULL_R, skirt_r=SKIRT_R))
    nodes.append(root)
    gl = dict(asset=dict(version='2.0', generator='planet-stack build_engine_ring.py'), scene=0, scenes=[dict(nodes=[len(nodes) - 1], extras=dict(engine_ring=L))], nodes=nodes,
              meshes=[dict(name=f'Engine_Ring_N{L["N"]:02d}', primitives=[dict(attributes=dict(POSITION=0, NORMAL=1, COLOR_0=2), indices=3, material=0)])],
              materials=[dict(name='M_EngineRing', pbrMetallicRoughness=dict(baseColorFactor=[1, 1, 1, 1], metallicFactor=0.35, roughnessFactor=0.5))],
              buffers=[dict(byteLength=len(bin_))],
              bufferViews=[dict(buffer=0, byteOffset=offs[0], byteLength=len(blobs[0]), target=34962), dict(buffer=0, byteOffset=offs[1], byteLength=len(blobs[1]), target=34962),
                           dict(buffer=0, byteOffset=offs[2], byteLength=len(blobs[2]), target=34962), dict(buffer=0, byteOffset=offs[3], byteLength=len(blobs[3]), target=34963)],
              accessors=[dict(bufferView=0, componentType=5126, count=len(pos), type='VEC3', min=pos.min(0).tolist(), max=pos.max(0).tolist()),
                         dict(bufferView=1, componentType=5126, count=len(pos), type='VEC3'), dict(bufferView=2, componentType=5121, normalized=True, count=len(pos), type='VEC4'),
                         dict(bufferView=3, componentType=5123 if idx.dtype == np.uint16 else 5125, count=len(idx), type='SCALAR')])
    js = json.dumps(gl, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
    data = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(bin_), 0x004E4942) + bin_
    open(path, 'wb').write(data); return len(pos), len(idx) // 3, len(data)
allL = {}
for N in range(6, 12):
    L = build(N); v, t, b = glb(f'{OUT}/engine_ring_N{N:02d}.glb', L); L.update(verts=v, tris=t, bytes=b); allL[N] = L; print(N, v, t, b, L['exit_r'])
json.dump(allL, open(f'{OUT}/layout.json', 'w'), indent=1)
