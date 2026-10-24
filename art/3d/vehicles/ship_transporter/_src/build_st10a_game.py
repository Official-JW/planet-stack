#!/usr/bin/env python3
"""ST-10A game GLB (Lv10 ship transporter, tracked straddle crawler) -- pure numpy, no Blender (box hold 10/24).
Director 2:31 PM: A picked over B. Same conditions as ST-10B: <= 8 draws incl. tender astronaut, meshopt, Loaded/Empty cradle,
Ship_Seat + Tender_Spot, no cab (autonomous), crawler tracks with a tread look, cradle clear of the aft skirt / gear / engine ring.

  python3 build_st10a_game.py --out raw.glb [--emis 0.09]     then   gltfpack -i raw.glb -o st10a_game.glb -c -kn -km

Frame: glTF metres, +X = travel (toward the Shipyard; cross girder at +X, OPEN end of the U at -X), +Y up, +Z toward the game camera.
Origin = ground under the ship axis. Ship_Seat (0, 0.45, 0) = ship root (Ship_Placeholder frame) when carried (cradle jacks +0.45 m).
Geometry follows concept A (build_transporter.py concept_A) except: clamp arms moved to 14.4 / 24.8 / 32.4 m onto clean hull rows of the
Lv2 hull (r 4.00-4.04, sector +-37 deg about +-Z), towers 34.5 m, so every arm/saddle sits >= 3 m above the aft skirt band.
Materials: ST10A_Paint (COLOR_0 game palette, rough 0.7, metal 0, emissive = sky tint 0x9fb4d8 x k) + ST10A_GlowCyan + ST10A_GlowAmber
(emissive 2.5). Cradle glows and astronaut glows are baked into COLOR_0 (as in ST-10B).
"""
import json, math, os, struct, sys
import numpy as np
H = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[1:]; A = {a[i][2:]: a[i + 1] for i in range(0, len(a) - 1, 2)}
OUT = A.get('out', '/workspace/st10a/st10a_raw.glb'); EMIS = float(A.get('emis', 0.09))

def s2l(h):
    h = h.lstrip('#'); c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
# game palette (same hexes as the ST-10B game build / concept GAME map)
C = {k: s2l(v) for k, v in dict(WHITE='#e8edf5', PALE='#c9d3e6', GRAPH='#5d6880', GRAPH2='#6b7690', STEEL='#97a3bb', CHROME='#c3cad6',
     HAZ='#c99a3c', PADM='#58606e', SHOE='#6e737c', CLEAT='#8a909a', GAP='#3e434b', SPROCKET='#4f586b', CYANB='#3ad0ff', AMBB='#ffb020').items()}

class Mesh:
    def __init__(s): s.P, s.N, s.C, s.I, s.n = [], [], [], [], 0
    def add(s, P, N, Cc, I):
        P = np.asarray(P, float); N = np.asarray(N, float); I = np.asarray(I, int)
        Cc = np.broadcast_to(np.asarray(Cc, float), P.shape)
        s.P.append(P); s.N.append(N); s.C.append(Cc); s.I.append(I + s.n); s.n += len(P)
    def quad(s, q, col, nrm=None):   # q: 4 points CCW seen from outside
        q = np.asarray(q, float); g = np.cross(q[2] - q[0], q[3] - q[1]); n = g if nrm is None else np.asarray(nrm, float)
        if np.dot(g, n) < 0: q = q[::-1]           # keep CCW winding consistent with the shading normal
        n = n / (np.linalg.norm(n) + 1e-12); s.add(q, [n] * 4, col, [0, 1, 2, 0, 2, 3])
    def tris(s): return sum(len(i) for i in s.I) // 3
    def arrays(s):
        return (np.concatenate(s.P).astype(np.float32), np.concatenate(s.N).astype(np.float32),
                np.concatenate(s.C).astype(np.float32), np.concatenate(s.I).astype(np.uint32))

def frame(d):
    d = np.asarray(d, float); d = d / np.linalg.norm(d); t = np.array([0, 1, 0.]) if abs(d[1]) < 0.9 else np.array([1, 0, 0.])
    u = np.cross(d, t); u /= np.linalg.norm(u); v = np.cross(d, u); return d, u, v
def box(m, c, size, col, R=None):
    c = np.asarray(c, float); hx, hy, hz = np.asarray(size, float) / 2; R = np.eye(3) if R is None else np.asarray(R)
    for ax in range(3):
        for sg in (-1, 1):
            n = np.zeros(3); n[ax] = sg; o = [i for i in range(3) if i != ax]; h = np.array([hx, hy, hz])
            corners = []
            for (p, q) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                v = np.zeros(3); v[ax] = sg * h[ax]; v[o[0]] = p * h[o[0]]; v[o[1]] = q * h[o[1]]; corners.append(v)
            cr = np.array(corners)
            m.quad(cr @ R.T + c, col, R @ n)
def beam(m, p0, p1, w, h, col):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); d, u, v = frame(p1 - p0)
    box(m, (p0 + p1) / 2, (np.linalg.norm(p1 - p0), w, h), col, R=np.stack([d, u, v], 1))
def cyl(m, c, r, L, axis, col, seg=12, caps=True, capcol=None):
    c = np.asarray(c, float); d, u, v = frame(axis); P, N = [], []
    for i in range(seg + 1):
        t = 2 * math.pi * i / seg; n = math.cos(t) * u + math.sin(t) * v
        P += [c - d * L / 2 + r * n, c + d * L / 2 + r * n]; N += [n, n]
    I = []
    for i in range(seg): I += [2 * i, 2 * i + 2, 2 * i + 1, 2 * i + 1, 2 * i + 2, 2 * i + 3]
    m.add(P, N, col, I)
    if caps:
        for sg in (-1, 1):
            ring = [c + sg * d * L / 2 + r * (math.cos(2 * math.pi * i / seg) * u + math.sin(2 * math.pi * i / seg) * v) for i in range(seg)]
            I = []
            for i in range(1, seg - 1): I += ([0, i, i + 1] if sg > 0 else [0, i + 1, i])
            m.add(ring, [sg * d] * seg, capcol if capcol is not None else col, I)
def piston(m, p0, p1, r, col_body, col_rod, ext=0.55, seg=8):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); L = np.linalg.norm(p1 - p0); d = (p1 - p0) / L; pm = p0 + d * L * ext
    cyl(m, (p0 + pm) / 2, r, L * ext, d, col_body, seg); cyl(m, (pm + p1) / 2, r * 0.55, L * (1 - ext), d, col_rod, seg)
def hazard(m, c, size, axis_long, n=6):
    """hazard plate as n alternating amber / graphite bands along axis_long (0 x, 1 y, 2 z)"""
    c = np.asarray(c, float); size = np.asarray(size, float)
    for i in range(n):
        s2 = size.copy(); s2[axis_long] = size[axis_long] / n; cc = c.copy(); cc[axis_long] += -size[axis_long] / 2 + (i + 0.5) * size[axis_long] / n
        box(m, cc, s2, C['HAZ'] if i % 2 == 0 else C['GRAPH'])
def track_loop(m, cx, zc, L, Ht, tw, pitch=0.78, thick=0.16, cleat=0.14):
    """crawler track belt: stadium loop in the XY plane (centre x cx, width tw along Z at zc) with shoe plates, transverse cleats and dark joints"""
    R = Ht / 2; st = L - 2 * R; per = 2 * st + 2 * math.pi * R; n = int(round(per / pitch)); pitch = per / n
    def at(s):
        p, nn = at0(s); return p + np.array([0, cleat]), nn
    def at0(s):
        s %= per
        if s < st: return np.array([cx + st / 2 - s, Ht]), np.array([0, 1.])                       # top run, moving -X
        s -= st
        if s < math.pi * R: a = s / R; return np.array([cx - st / 2 - R * math.sin(a), R + R * math.cos(a)]), np.array([-math.sin(a), math.cos(a)])
        s -= math.pi * R
        if s < st: return np.array([cx - st / 2 + s, 0.]), np.array([0, -1.])
        s -= st; a = s / R; return np.array([cx + st / 2 + R * math.sin(a), R - R * math.cos(a)]), np.array([math.sin(a), -math.cos(a)])
    # profile per shoe: joint gap | plate | cleat ramp up | cleat top | ramp down | plate
    U = [(0.00, 0, 'GAP'), (0.06, 0, 'SHOE'), (0.40, 0, 'SHOE'), (0.48, 1, 'CLEAT'), (0.70, 1, 'CLEAT'), (0.78, 0, 'SHOE')]
    pts, cols = [], []
    for i in range(n):
        for (u, h, col) in U:
            p, nn = at((i + u) * pitch); pts.append(p + nn * (h * cleat)); cols.append(C[col])
    pts.append(pts[0]); cols.append(cols[0]); pts = np.array(pts)
    z0, z1 = zc - tw / 2, zc + tw / 2
    for k in range(len(pts) - 1):   # outer surface quads (normal outward = left of travel direction in XY, since loop runs CCW seen from +Z)
        a2, b2 = pts[k], pts[k + 1]; e = b2 - a2; nrm = np.array([-e[1], e[0], 0.]) * -1
        q = [[a2[0], a2[1], z1], [b2[0], b2[1], z1], [b2[0], b2[1], z0], [a2[0], a2[1], z0]]
        m.quad(q, cols[k], nrm / (np.linalg.norm(nrm) + 1e-12))
    # side walls: belt band (base line -> base - thick) coarse per shoe, + cleat end caps
    for sg, z in ((1, z1), (-1, z0)):
        nz = np.array([0, 0, sg * 1.])
        for i in range(n):
            p0, n0 = at(i * pitch); p1, n1 = at((i + 1) * pitch)
            q = [[*(p0 - n0 * thick), z], [*(p1 - n1 * thick), z], [*p1, z], [*p0, z]]
            m.quad(q if sg > 0 else q[::-1], C['GAP'], nz)
            c0, cn0 = at((i + 0.40) * pitch); c1, cn1 = at((i + 0.78) * pitch); t0, tn0 = at((i + 0.48) * pitch); t1, tn1 = at((i + 0.70) * pitch)
            q = [[*c0, z], [*c1, z], [*(t1 + tn1 * cleat), z], [*(t0 + tn0 * cleat), z]]
            m.quad(q if sg > 0 else q[::-1], C['SHOE'], nz)
def saddle(m, y, rin, az_c, span, depth=1.3, thick=0.35, seg=10):
    """curved clamp pad (rubber face r rin..rin+thick, white backing to +0.45) centred on azimuth az_c (rad, from +X toward +Z) + cyan edge bars"""
    for (r0, r1, col, dz) in ((rin, rin + thick, C['PADM'], depth), (rin + thick, rin + thick + 0.45, C['WHITE'], depth * 1.1)):
        A_ = [az_c - span / 2 + span * i / seg for i in range(seg + 1)]
        P = lambda r, t, yy: [r * math.cos(t), yy, r * math.sin(t)]
        for i in range(seg):
            t0, t1 = A_[i], A_[i + 1]
            for (ra, rb, y0, y1, nrm) in ((r0, r0, y - dz / 2, y + dz / 2, -1), (r1, r1, y + dz / 2, y - dz / 2, 1)):   # inner / outer faces
                tm = (t0 + t1) / 2; n = np.array([math.cos(tm), 0, math.sin(tm)]) * nrm
                m.quad([P(ra, t0, y0), P(ra, t1, y0), P(rb, t1, y1), P(rb, t0, y1)], col, n)
            m.quad([P(r0, t0, y + dz / 2), P(r0, t1, y + dz / 2), P(r1, t1, y + dz / 2), P(r1, t0, y + dz / 2)], col, np.array([0, 1., 0]))
            m.quad([P(r0, t0, y - dz / 2), P(r1, t0, y - dz / 2), P(r1, t1, y - dz / 2), P(r0, t1, y - dz / 2)], col, np.array([0, -1., 0]))
        for t, sg in ((A_[0], -1), (A_[-1], 1)):
            tn = np.array([-math.sin(t), 0, math.cos(t)]) * sg
            m.quad([P(r0, t, y - dz / 2), P(r1, t, y - dz / 2), P(r1, t, y + dz / 2), P(r0, t, y + dz / 2)], col, tn)
    for t in (az_c - span / 2, az_c + span / 2):
        r = rin + thick + 0.48; box(m, (r * math.cos(t), y, r * math.sin(t)), (0.1, depth * 1.1, 0.1), C['CYANB'])

# ------------------------------------------------------------------ layout (concept A, glTF frame)
G_IN, TRK, X0, X1, HT, GZ0, GZ1 = 9.7, 3.6, -12.5, 15.5, 3.4, 4.2, 7.0
CLAMPS = [(14.4, 4.01), (24.8, 4.00), (32.4, 4.04)]     # (centre y, hull r in the +-37 deg sector over the saddle height): clean hull rows
TZ = 34.5; LIFT = 0.45; RUB = 0.03; RETRACT = 3.2   # empty saddles open 3.2 m: swept drive-in clears the hull ladder/box features (r 5.63 at y 24.5-26.8) at every ship yaw (saddle_yaw_check.py)
TENDER = (-8.57013226, 0.0, 16.5)
body, cyan, amber = Mesh(), Mesh(), Mesh()
for s in (-1, 1):
    zc = s * (G_IN + TRK / 2)
    for cx in (X0 + 5.25, X1 - 5.25):                       # twin-track trucks
        for dz in (-(TRK / 4 + 0.05), TRK / 4 + 0.05):
            tw = TRK / 2 - 0.1; R = HT / 2
            track_loop(body, cx, zc + dz, 10.5, HT, tw)
            for xx in (cx - 10.5 / 2 + R, cx + 10.5 / 2 - R):
                cyl(body, (xx, R + 0.14, zc + dz), R - 0.3, tw * 0.72, (0, 0, 1), C['SPROCKET'], seg=12, capcol=C['STEEL'])
            box(body, (cx, 1.29, zc + dz), (10.5 - 2 * R + 0.6, 1.0, tw * 0.5), C['GRAPH'])
        box(body, (cx, HT + 0.55, zc), (10.5 - 1.2, 0.9, TRK + 0.3), C['GRAPH2'])
        box(body, (cx, HT + 1.12, zc), (10.5 - 2.4, 0.35, TRK + 0.5), C['WHITE'])
        for sx in (-1, 1):
            for sz in (-1, 1):
                p = (cx + sx * 3.05, 0, zc + sz * 1.4); piston(body, (p[0], HT + 1.0, p[2]), (p[0], HT + 2.2, p[2]), 0.28, C['GRAPH'], C['CHROME'], 0.5, seg=6)
        for xe in (cx + 10.5 / 2 - 0.9, cx - 10.5 / 2 + 0.9): hazard(body, (xe, HT + 0.55, zc), (0.14, 0.6, TRK + 0.35), 2)
    # box girder + belly + ribs + rail + front hazard
    box(body, ((X0 + X1) / 2, (GZ0 + GZ1) / 2, zc), (X1 - X0, GZ1 - GZ0, TRK + 0.4), C['WHITE'])
    box(body, ((X0 + X1) / 2, GZ0 + 0.05, zc), (X1 - X0 - 0.4, 0.5, TRK + 0.2), C['GRAPH'])
    for i in range(9): box(body, (X0 + 1.5 + i * (X1 - X0 - 3) / 8, (GZ0 + GZ1) / 2 + 0.1, zc + s * (TRK / 2 + 0.22)), (0.18, GZ1 - GZ0 - 0.9, 0.08), C['PALE'])
    for zz in (zc + s * (TRK / 2 - 0.1), zc - s * (TRK / 2 - 0.1)): beam(body, (X0 + 0.5, GZ1 + 1.1, zz), (X1 - 0.5, GZ1 + 1.1, zz), 0.08, 0.08, C['STEEL'])
    hazard(body, (X0 - 0.02, (GZ0 + GZ1) / 2, zc), (0.14, GZ1 - GZ0 - 0.4, TRK + 0.42), 2, n=7)
    for zz in (zc + s * (TRK / 2 + 0.21), zc - s * (TRK / 2 + 0.21)): box(cyan, ((X0 + X1) / 2, GZ1 - 0.5, zz), (X1 - X0 - 0.6, 0.09, 0.09), C['CYANB'])
    # power / drive module + radiator fins
    box(body, (X1 - 5.0, GZ1 + 0.8, zc), (6.0, 1.6, TRK - 0.3), C['GRAPH2'])
    for i in range(5): box(body, (X1 - 7.4 + i * 1.2, GZ1 + 2.15, zc), (0.12, 1.3, TRK - 0.6), C['WHITE'])
    box(cyan, (X1 - 5.0, GZ1 + 1.3, zc + s * (TRK / 2 - 0.12)), (5.8, 0.08, 0.08), C['CYANB'])
    # cradle tower: two legs + bracing + cap + beacon
    for sx in (-1, 1):
        box(body, (sx * 2.6, (GZ1 + TZ) / 2, zc), (1.3, TZ - GZ1, 1.3), C['WHITE'])
        box(cyan, (sx * 3.26, (GZ1 + TZ) / 2, zc - s * 0.66), (0.07, TZ - GZ1 - 2.0, 0.07), C['CYANB'])
    y = GZ1 + 1.0
    while y < TZ - 2.5:
        beam(body, (-2.6, y, zc), (2.6, y + 3.1, zc), 0.32, 0.32, C['GRAPH']); beam(body, (2.6, y, zc), (-2.6, y + 3.1, zc), 0.32, 0.32, C['GRAPH'])
        beam(body, (-2.6, y, zc), (2.6, y, zc), 0.36, 0.4, C['GRAPH2']); y += 3.1
    box(body, (0, TZ + 0.4, zc), (6.8, 1.2, 2.2), C['WHITE']); box(amber, (0, TZ + 1.2, zc), (0.45, 0.4, 0.45), C['AMBB'])
# rear cross girder + autonomous control pod (no cab) + antennas
YY = G_IN + TRK
box(body, ((11.0 + X1) / 2, (GZ0 + GZ1) / 2 + 0.2, 0), (X1 - 11.0, GZ1 - GZ0 + 0.4, 2 * YY), C['WHITE'])
box(body, ((11.0 + X1) / 2, GZ0 + 0.05, 0), (X1 - 11.2, 0.5, 2 * G_IN - 0.2), C['GRAPH'])
hazard(body, (10.98, GZ0 + 0.55, 0), (0.1, 0.7, 2 * G_IN - 0.4), 2, n=9)
box(body, (13.2, GZ1 + 1.1, 0), (2.6, 1.8, 6.0), C['GRAPH2']); box(cyan, (14.53, GZ1 + 1.35, 0), (0.05, 0.5, 5.0), C['CYANB'])
for s in (-1, 1):
    cyl(body, (13.2, GZ1 + 3.2, s * 2.2), 0.05, 2.5, (0, 1, 0), C['STEEL'], seg=6); box(amber, (13.2, GZ1 + 4.45, s * 2.2), (0.2, 0.2, 0.2), C['AMBB'])
box(cyan, (X1 + 0.02, GZ1 - 0.5, 0), (0.05, 0.09, 2 * YY - 0.6), C['CYANB'])

def cradle(loaded):
    m = Mesh()
    for s in (-1, 1):
        za = s * (G_IN + TRK / 2)
        for (yc, rh) in CLAMPS:
            rin = rh + RUB if loaded else rh + RUB + RETRACT
            zb = s * (rin + 0.78); zm = za + (zb - za) * 0.55
            box(m, (0, yc, (za + zm) / 2), (2.2, 1.5, abs(zm - za) + 0.6), C['WHITE'])
            box(m, (0, yc, (zm + zb) / 2), (1.6, 1.1, abs(zb - zm) + 0.6), C['STEEL'])
            piston(m, (0, yc + 1.25, za - s * 0.8), (0, yc + 0.85, zm - s * 0.2), 0.22, C['GRAPH'], C['CHROME'], 0.55, seg=8)
            box(m, (-1.11, yc + 0.3, (za - s * 0.8 + zm) / 2), (0.06, 0.06, abs(zm - za + s * 0.8)), C['CYANB'])
            saddle(m, yc, rin, math.pi / 2 * s, math.radians(70))
    gL = 2 * G_IN
    if loaded:   # swing gate closed across the open end
        box(m, (X0 - 0.2, GZ1 - 0.6, 0), (1.2, 1.6, gL), C['WHITE']); hazard(m, (X0 - 0.82, GZ1 - 0.6, 0), (0.06, 0.7, gL - 0.4), 2, n=11)
        for s in (-1, 1): cyl(m, (X0 - 0.2, GZ1 - 0.6, s * (G_IN - 0.1)), 0.45, 2.2, (0, 1, 0), C['GRAPH'], seg=10)
        box(m, (X0 - 0.83, GZ1 + 0.21, 0), (0.06, 0.06, gL - 0.8), C['CYANB'])
    else:        # two leaves (hinged at the front inner girder corners) swung 90 deg back against the inner girder faces: no overhang
        for s in (-1, 1):
            zl = s * (G_IN - 0.2 - 0.6)
            box(m, (X0 - 0.2 + gL / 4, GZ1 - 0.6, zl), (gL / 2, 1.6, 1.2), C['WHITE'])
            hazard(m, (X0 + gL / 4, GZ1 - 0.6, zl - s * 0.62), (gL / 2 - 0.4, 0.7, 0.06), 0, n=7)
            cyl(m, (X0 - 0.2, GZ1 - 0.6, s * (G_IN - 0.1)), 0.45, 2.2, (0, 1, 0), C['GRAPH'], seg=10)
    return m
CL, CE = cradle(True), cradle(False)
ast = np.load(os.path.join(H, 'astronaut_tender_game.npz'))

# ------------------------------------------------------------------ write GLB
bin_, views, accs = bytearray(), [], []
def put(arr, target=None, minmax=False):
    global bin_
    while len(bin_) % 4: bin_ += b'\0'
    off = len(bin_); bin_ += arr.tobytes(); bv = dict(buffer=0, byteOffset=off, byteLength=arr.nbytes)
    if target: bv['target'] = target
    views.append(bv); ct = 5125 if arr.dtype == np.uint32 else 5126
    ac = dict(bufferView=len(views) - 1, componentType=ct, count=int(arr.shape[0]), type='SCALAR' if arr.ndim == 1 else 'VEC%d' % arr.shape[1])
    if minmax: ac['min'] = arr.min(0).tolist(); ac['max'] = arr.max(0).tolist()
    accs.append(ac); return len(accs) - 1
meshes, nodes, info = [], [], {}
def add_mesh(name, P, N, Cc, I, mat, t=None):
    prim = dict(attributes=dict(POSITION=put(P, 34962, True), NORMAL=put(N, 34962), COLOR_0=put(Cc, 34962)), indices=put(I, 34963), material=mat)
    meshes.append(dict(name=name, primitives=[prim])); nd = dict(name=name, mesh=len(meshes) - 1)
    if t is not None: nd['translation'] = [float(x) for x in t]
    nodes.append(nd); info[name] = dict(tris=int(len(I) // 3), verts=int(len(P)), material=['ST10A_Paint', 'ST10A_GlowCyan', 'ST10A_GlowAmber'][mat]); return len(nodes) - 1
kids = [add_mesh('Body_Paint', *body.arrays(), 0), add_mesh('Body_GlowCyan', *cyan.arrays(), 1), add_mesh('Body_GlowAmber', *amber.arrays(), 2),
        add_mesh('Cradle_Loaded', *CL.arrays(), 0), add_mesh('Cradle_Empty', *CE.arrays(), 0),
        add_mesh('Astronaut', ast['P'].astype(np.float32), ast['N'].astype(np.float32), ast['C'][:, :3].astype(np.float32), ast['I'].astype(np.uint32), 0, TENDER)]
nodes.append(dict(name='Ship_Seat', translation=[0, LIFT, 0], extras=dict(note='ship root (Ship_Placeholder frame) when carried: cradle jacks +0.45 m', lift_m=LIFT)))
kids.append(len(nodes) - 1)
nodes.append(dict(name='Tender_Spot', translation=list(TENDER), extras=dict(note='tender astronaut on foot, camera side, beside the front-left truck; no cab (autonomous)')))
kids.append(len(nodes) - 1)
sky = [round(0.3467 * EMIS, 5), round(0.4564 * EMIS, 5), round(0.6867 * EMIS, 5)]
mats = [dict(name='ST10A_Paint', pbrMetallicRoughness=dict(metallicFactor=0, roughnessFactor=0.7), emissiveFactor=sky, doubleSided=True),
        dict(name='ST10A_GlowCyan', pbrMetallicRoughness=dict(baseColorFactor=[0.0423, 0.6308, 1, 1], metallicFactor=0, roughnessFactor=0.7),
             emissiveFactor=[0.0423, 0.6308, 1], extensions=dict(KHR_materials_emissive_strength=dict(emissiveStrength=2.5)), doubleSided=True),
        dict(name='ST10A_GlowAmber', pbrMetallicRoughness=dict(baseColorFactor=[1, 0.4342, 0.0144, 1], metallicFactor=0, roughnessFactor=0.7),
             emissiveFactor=[1, 0.4342, 0.0144], extensions=dict(KHR_materials_emissive_strength=dict(emissiveStrength=2.5)), doubleSided=True)]
ex = dict(transporter='ST-10A tracked straddle crawler (Lv10), game build', cradle_states='show exactly one of Cradle_Loaded / Cradle_Empty',
          clamps_y=[c[0] for c in CLAMPS], saddle_r_loaded=[round(c[1] + RUB, 3) for c in CLAMPS], retract_m=RETRACT, paint_emissive_k=EMIS)
nodes.append(dict(name='ST10A', children=kids, extras=ex))
j = dict(asset=dict(version='2.0', generator='build_st10a_game.py (Planet Stack A&A)'), scene=0, scenes=[dict(nodes=[len(nodes) - 1])], nodes=nodes,
         meshes=meshes, materials=mats, accessors=accs, bufferViews=views, buffers=[dict(byteLength=len(bin_))], extensionsUsed=['KHR_materials_emissive_strength'])
while len(bin_) % 4: bin_ += b'\0'
j['buffers'][0]['byteLength'] = len(bin_)
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4)
glb = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(js) + 8 + len(bin_)) + struct.pack('<I4s', len(js), b'JSON') + js + struct.pack('<I4s', len(bin_), b'BIN\0') + bytes(bin_)
open(OUT, 'wb').write(glb)
vis = sum(info[k]['tris'] for k in ('Body_Paint', 'Body_GlowCyan', 'Body_GlowAmber', 'Cradle_Loaded', 'Astronaut'))
vis_e = vis - info['Cradle_Loaded']['tris'] + info['Cradle_Empty']['tris']
rep = dict(out=OUT, emis=EMIS, nodes=info, tris_visible_loaded=vis, tris_visible_empty=vis_e, tris_file=sum(v['tris'] for v in info.values()), clamps=CLAMPS, tz=TZ)
json.dump(rep, open(OUT.replace('.glb', '_build.json'), 'w'), indent=1)
# geometry dump for the clearance check (unpacked, exact)
np.savez_compressed(OUT.replace('.glb', '_geom.npz'), **{f'{k}_{x}': v for k, mm in (('body', body), ('cyan', cyan), ('amber', amber), ('cl', CL), ('ce', CE)) for x, v in zip('PNCI', mm.arrays())})
print('ST10A', json.dumps({k: v['tris'] for k, v in info.items()}), 'visible', vis, vis_e, 'file', rep['tris_file'], 'bytes', len(glb))
