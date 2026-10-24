"""HT-04 / FB-05 detail pass (10/23 night, Jacob: "the trucks lack detail; autonomous, but with cabs for manual driving").
Adds low-poly detail geometry to the SHIPPED skinned truck mesh without touching anything else: every node, joint, pivot,
inverse bind matrix, clip, extras and the 'fill' morph stay byte-for-byte the same; new vertices are appended (bound 100 % to
Truck_Chassis / FB05_Chassis or to their wheel joint, zero morph deltas).
- paint parts (vertex colours) go into the existing SHM_Paint primitive (no new draw)
- glazing (windshield, side + door windows, mirror glass, camera / lidar lenses) goes into ONE new primitive with SHM_Glass,
  a dark tinted glossy OPAQUE material (pbrMetallicRoughness only: no transmission / clearcoat / ior / images) -> +1 draw
usage:  python3 detail_pass.py ht04|fb05 IN_PLAIN.glb OUT_RAW.glb      (IN = gltfpack -noq -kn -ke unpack of the shipped GLB)
then:   gltfpack -i OUT_RAW.glb -o ../ht04_game.glb -cc -kn -ke
Coordinates below: Blender truck frame (X forward, Y = truck left = glTF -Z, Z up), metres, origin = ground centre."""
import sys, os, math, json, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '_shared_src'))
from glbskin import GLB

KIND, SRC, OUT = sys.argv[1:4]
PFX = 'HT04' if KIND == 'ht04' else 'FB05'; CH = 'Truck_Chassis' if KIND == 'ht04' else 'FB05_Chassis'
def srgb2lin(h):
    h = h.lstrip('#'); return tuple((c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4) for c in (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))
# concept B palette, linear (same values as the truck's existing COLOR_0 bytes / props propgeo.P)
C = dict(white=(0.79, 0.81, 0.85), white2=srgb2lin('#e8edf5'), graph=(0.02, 0.03, 0.04), graph2=srgb2lin('#3a4258'), graph1=srgb2lin('#2a3245'),
         steel=(0.39, 0.43, 0.48), satin=srgb2lin('#9aa3ad'), tyre=(0.022, 0.022, 0.024), tyre2=(0.035, 0.035, 0.038), cyan=(0.03, 0.77, 1.0),
         cyan_hi=(0.58, 0.96, 1.0), amber=srgb2lin('#ffb020'), red=(0.75, 0.04, 0.03), rubber=(0.012, 0.012, 0.014), lamp=(0.95, 0.96, 0.92),
         dust=(0.46, 0.42, 0.36))
F = []   # faces: (pts[n][3] blender coords, colour, 'paint'|'glass', bone)
def rot(rx=0, ry=0, rz=0):
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    X = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]); Y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]); Z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Z @ Y @ X
def box(size, c, col, R=None, mat='paint', bone=None, skip=(), taper=1.0):
    """skip: face keys to drop (hidden faces): '-x','+x','-y','+y','-z','+z' in the box's own frame"""
    sx, sy, sz = (s / 2 for s in size); R = np.eye(3) if R is None else R; c = np.array(c, float)
    V = []
    for z in (-sz, sz):
        k = taper if z > 0 else 1.0
        for x, y in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)): V.append(c + R @ np.array((x * k, y * k, z)))
    FS = {'-z': (0, 3, 2, 1), '+z': (4, 5, 6, 7), '-y': (0, 1, 5, 4), '+x': (1, 2, 6, 5), '+y': (2, 3, 7, 6), '-x': (3, 0, 4, 7)}
    for k, f in FS.items():
        if k not in skip: F.append(([V[i] for i in f], col, mat, bone or CH))
def cyl(p0, p1, r, col, segs=8, mat='paint', bone=None, cap0=True, cap1=True, r1=None):
    p0, p1 = np.array(p0, float), np.array(p1, float); d = p1 - p0; d /= np.linalg.norm(d); r1 = r if r1 is None else r1
    a = np.array((0, 0, 1.0)) if abs(d[2]) < 0.9 else np.array((1.0, 0, 0)); u = np.cross(d, a); u /= np.linalg.norm(u); v = np.cross(d, u)
    ring = lambda p, rr: [p + (u * math.cos(t) + v * math.sin(t)) * rr for t in (i * 2 * math.pi / segs for i in range(segs))]
    A, B = ring(p0, r), ring(p1, r1)
    for i in range(segs): j = (i + 1) % segs; F.append(([A[i], A[j], B[j], B[i]], col, mat, bone or CH))
    if cap0: F.append((A[::-1], col, mat, bone or CH))
    if cap1: F.append((B, col, mat, bone or CH))
def quad(pts, col, mat='paint', bone=None): F.append(([np.array(p, float) for p in pts], col, mat, bone or CH))
def chevrons(x, y0, y1, z0, z1, nx, n=6, ca=None, cb=None, slant=0.5):
    """hazard chevron plate on a face whose outward normal is +/-X (nx = +1 / -1), stripes slanting away from the centre (V)"""
    ca = ca or C['amber']; cb = cb or C['graph']; w = (y1 - y0) / n; h = z1 - z0
    quad([(x, y0, z0), (x, y0, z1), (x, y1, z1), (x, y1, z0)] if nx < 0 else [(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)], cb)
    xs = x + nx * 0.004; yc = (y0 + y1) / 2
    for k in range(-n, n + 1, 2):
        ya, yb = yc + k * w / 2, yc + (k + 1) * w / 2
        s = slant * h * (1 if (ya + yb) / 2 >= yc else -1)
        P = [(ya, z0), (yb, z0), (yb + s, z1), (ya + s, z1)]
        P = [(max(y0, min(y1, yy)), zz) for yy, zz in P]
        if abs(P[0][0] - P[1][0]) < 1e-4 and abs(P[2][0] - P[3][0]) < 1e-4: continue
        pts = [(xs, yy, zz) for yy, zz in P]
        quad(pts if nx > 0 else pts[::-1], ca)

TWIDE = 0.62; WR = 0.85; AX = [(-2.7, 'R'), (-1.35, 'M'), (2.4, 'F')]
# ------------------------------------------------------------------ wheels: chevron tread blocks, sidewall ring, hub, lugs
for wx, a in AX:
    for sy in (-1, 1):
        bone = '%s_Wheel_%s%s' % (PFX, a, 'L' if sy > 0 else 'R'); wy = sy * 1.5
        N = 14
        for i in range(N):
            t = 2 * math.pi * (i + 0.5 * (sy > 0)) / N
            for half in (-1, 1):   # two slanted blocks per pitch -> a V (directional chevron) tread
                ang = t + half * 0.07
                c = (wx + WR * math.cos(ang), wy + half * 0.16, WR + WR * math.sin(ang))
                box((0.03, 0.27, 0.15), c, C['tyre2'], R=rot(ry=-ang) @ rot(rx=half * 0.45), bone=bone, skip=('-x',))
        ho = sy * (TWIDE / 2 + 0.05)
        cyl((wx, wy + ho, WR), (wx, wy + ho + sy * 0.07, WR), 0.13, C['graph2'], segs=8, bone=bone, cap0=False)        # centre cap
        cyl((wx, wy + ho + sy * 0.07, WR), (wx, wy + ho + sy * 0.09, WR), 0.06, C['cyan_hi'], segs=8, bone=bone, cap0=False)  # cyan hub LED
        for k in range(6):   # lug nuts
            q = 2 * math.pi * k / 6
            box((0.06, 0.05, 0.06), (wx + 0.2 * math.cos(q), wy + ho + sy * 0.012, WR + 0.2 * math.sin(q)), C['satin'], R=rot(ry=-q), bone=bone, skip=('-y' if sy > 0 else '+y',))
# ------------------------------------------------------------------ cab (shared HT-04 / FB-05 cab: x 1.2..3.5, y +-1.25, z 1.85..3.62)
TA = 0.28; tn = math.tan(TA)
def wsx(z, off): return 3.487 - tn * (z - 2.98) + off           # x of the tilted windshield frame face at height z (+ offset)
Rw = rot(ry=-TA)
quad([(wsx(2.56, 0.022), -1.06, 2.56), (wsx(2.56, 0.022), 1.06, 2.56), (wsx(3.36, 0.022), 1.06, 3.36), (wsx(3.36, 0.022), -1.06, 3.36)], None, 'glass')   # windshield
for z in (2.53, 3.39): box((0.04, 2.2, 0.05), (wsx(z, 0.02), 0, z), C['graph'], R=Rw)                                             # frame top / bottom
for y in (-1.09, 1.09, 0.0): box((0.04, 0.05 if y else 0.035, 0.86), (wsx(2.96, 0.02), y, 2.96), C['graph'], R=Rw)                # A-pillars + centre post
for y in (-0.55, 0.55):   # wipers parked at the bottom, arm + blade
    box((0.02, 0.62, 0.025), (wsx(2.66, 0.04), y - 0.05, 2.66), C['graph'], R=Rw @ rot(rx=0.12))
    box((0.025, 0.04, 0.04), (wsx(2.58, 0.04), y + 0.27, 2.58), C['graph1'], R=Rw)
for sy in (-1, 1):
    ys = sy * 1.25
    yo = lambda d: ys + sy * d
    # side window + door with seams, window, handle; panel lines; grab handles; mirror
    quad([(2.55, yo(.009), 2.78), (3.12, yo(.009), 2.78), (3.12, yo(.009), 3.24), (2.55, yo(.009), 3.24)][::sy], None, 'glass')   # side window
    quad([(1.56, yo(.009), 2.74), (2.14, yo(.009), 2.74), (2.14, yo(.009), 3.1), (1.56, yo(.009), 3.1)][::sy], None, 'glass')     # door window
    for (x0, z0, x1, z1) in ((1.36, 2.08, 2.34, 2.105), (1.36, 3.17, 2.34, 3.195), (1.36, 2.08, 1.385, 3.195), (2.315, 2.08, 2.34, 3.195),   # door seams
                             (2.48, 2.72, 3.19, 2.74), (2.48, 3.26, 3.19, 3.28), (2.48, 2.72, 2.5, 3.28), (3.17, 2.72, 3.19, 3.28),       # side window gasket
                             (1.5, 2.7, 2.2, 2.72), (1.5, 3.12, 2.2, 3.14), (2.36, 2.42, 3.38, 2.435), (1.22, 2.42, 1.34, 2.435)):        # door window gasket, belt line
        box((x1 - x0, 0.012, z1 - z0), ((x0 + x1) / 2, yo(0.006), (z0 + z1) / 2), C['graph'], skip=('+y' if sy < 0 else '-y',))
    box((0.16, 0.03, 0.045), (2.16, yo(0.02), 2.6), C['graph'])                       # door handle
    box((0.12, 0.012, 0.03), (2.16, yo(0.036), 2.6), C['satin'])
    for hx, hz0, hz1 in ((1.29, 1.95, 3.0), (2.42, 2.15, 2.95)):                      # vertical grab handles beside the door
        cyl((hx, yo(0.075), hz0), (hx, yo(0.075), hz1), 0.022, C['amber'], segs=6)
        for hz in (hz0 + 0.04, hz1 - 0.04): box((0.035, 0.08, 0.035), (hx, yo(0.035), hz), C['graph'])
    box((1.9, 0.012, 0.03), (2.35, yo(0.006), 1.97), C['graph1'], skip=('+y' if sy < 0 else '-y',))    # lower panel line
    box((2.0, 0.014, 0.05), (2.3, yo(0.008), 3.45), C['white2'], skip=('+y' if sy < 0 else '-y',))     # edge-wear highlight on the roof edge
    # access ladder (behind the front wheel, under the door's rear edge)
    for k, z in enumerate((0.62, 1.05, 1.48)):
        box((0.42, 0.24, 0.045), (1.12, sy * 1.30, z), C['satin'])
        box((0.42, 0.02, 0.05), (1.12, sy * 1.43, z + 0.01), C['amber'])               # anti-slip nosing
    for dx in (-0.22, 0.22): box((0.04, 0.04, 1.2), (1.12 + dx, sy * 1.30, 1.15), C['graph'])
    box((0.05, 0.05, 0.35), (1.12, sy * 1.30, 1.72), C['graph'])
    # mirror: arm from the A-pillar, head with glass facing back
    cyl((3.28, yo(0.0), 3.15), (3.34, yo(0.42), 3.12), 0.025, C['graph'], segs=6)
    cyl((3.28, yo(0.0), 2.75), (3.34, yo(0.42), 2.9), 0.022, C['graph'], segs=6)
    box((0.08, 0.2, 0.42), (3.36, yo(0.5), 3.0), C['white'])
    box((0.02, 0.16, 0.36), (3.31, yo(0.5), 3.0), C['graph'])
    quad([(3.299, yo(0.42), 2.83), (3.299, yo(0.58), 2.83), (3.299, yo(0.58), 3.17), (3.299, yo(0.42), 3.17)][::-sy], None, 'glass')
    # corner lidar pucks (front upper cab corners) + side camera pods
    cyl((3.36, yo(-0.02), 3.62), (3.36, yo(-0.02), 3.70), 0.085, C['white'], segs=10, cap0=False)
    cyl((3.36, yo(-0.02), 3.70), (3.36, yo(-0.02), 3.74), 0.087, None, segs=10, mat='glass', cap0=False, cap1=False)
    cyl((3.36, yo(-0.02), 3.74), (3.36, yo(-0.02), 3.77), 0.08, C['graph'], segs=10, cap0=False)
    box((0.16, 0.1, 0.1), (1.6, yo(0.05), 3.48), C['graph'])                         # side-looking camera pod
    quad([(1.56, yo(0.101), 3.45), (1.64, yo(0.101), 3.45), (1.64, yo(0.101), 3.51), (1.56, yo(0.101), 3.51)][::sy], None, 'glass')
    # headlight surrounds + amber turn signal on the nose corners
    box((0.03, 0.34, 0.06), (3.69, sy * 0.95, 2.32), C['amber'])
    box((0.03, 0.24, 0.05), (3.69, sy * 0.95, 2.64), C['cyan_hi'])                    # cyan "autonomous" running light
# front bumper with hazard chevrons, tow hooks, forward lidar + radar
box((0.12, 2.5, 0.3), (3.62, 0, 1.4), C['graph1'])
chevrons(3.682, -1.2, 1.2, 1.28, 1.52, +1, n=10)
for sy in (-1, 1):
    box((0.1, 0.08, 0.12), (3.7, sy * 0.45, 1.18), C['satin'])
    cyl((3.62, sy * 1.12, 1.55), (3.62, sy * 1.12, 1.66), 0.07, C['white'], segs=10, cap0=False)
    cyl((3.62, sy * 1.12, 1.66), (3.62, sy * 1.12, 1.70), 0.072, None, segs=10, mat='glass', cap0=False, cap1=False)
    cyl((3.62, sy * 1.12, 1.70), (3.62, sy * 1.12, 1.72), 0.066, C['graph'], segs=10, cap0=False)
quad([(3.684, 0.3, 1.58), (3.684, -0.3, 1.58), (3.684, -0.3, 1.70), (3.684, 0.3, 1.70)], C['graph'])          # radar panel
quad([(3.687, 0.26, 1.6), (3.687, -0.26, 1.6), (3.687, -0.26, 1.68), (3.687, 0.26, 1.68)], None, 'glass')
# roof: sensor mast with spinning-lidar puck, camera bar, GNSS dome, antenna; cyan status light bar along the roof front edge
box((0.5, 0.5, 0.06), (1.75, 0, 3.65), C['graph'])
box((0.12, 0.12, 0.32), (1.75, 0, 3.84), C['white'])
box((0.14, 1.3, 0.08), (1.75, 0, 3.98), C['white'])
box((0.15, 1.2, 0.012), (1.75, 0, 4.025), C['graph2'])
cyl((1.75, 0, 4.02), (1.75, 0, 4.08), 0.17, C['white'], segs=12, cap0=False)
cyl((1.75, 0, 4.08), (1.75, 0, 4.14), 0.172, None, segs=12, mat='glass', cap0=False, cap1=False)
cyl((1.75, 0, 4.14), (1.75, 0, 4.17), 0.16, C['graph'], segs=12, cap0=False)
cyl((1.75, 0, 4.17), (1.75, 0, 4.18), 0.06, C['cyan_hi'], segs=8, cap0=False)
for sy in (-1, 1):
    box((0.16, 0.14, 0.12), (1.83, sy * 0.58, 3.98), C['graph'])                     # forward stereo cameras on the bar ends
    quad([(1.912, sy * 0.53, 3.95), (1.912, sy * 0.63, 3.95), (1.912, sy * 0.63, 4.01), (1.912, sy * 0.53, 4.01)][::-sy], None, 'glass')
cyl((1.35, 0.62, 3.62), (1.35, 0.62, 3.68), 0.09, C['white'], segs=10, cap0=False)    # GNSS dome
cyl((1.35, 0.62, 3.68), (1.35, 0.62, 3.72), 0.09, C['white2'], segs=10, cap0=False, r1=0.05)
cyl((1.32, -0.75, 3.62), (1.30, -0.75, 4.2), 0.012, C['graph'], segs=4, cap0=False)  # whip antenna
cyl((1.30, -0.75, 4.18), (1.30, -0.75, 4.21), 0.025, C['cyan_hi'], segs=6, cap0=False)
box((0.1, 2.1, 0.08), (3.24, 0, 3.64), C['graph'])                                   # status light bar housing
box((0.03, 1.9, 0.04), (3.30, 0, 3.64), C['cyan_hi'], skip=('-x',))
box((0.06, 1.9, 0.012), (3.24, 0, 3.685), C['cyan'], skip=('-z',))
for k in range(5): box((0.012, 0.02, 0.05), (3.315, -0.76 + 0.38 * k, 3.64), C['graph'])   # segment breaks
# roof panel lines + hatch
for (x0, x1, y0, y1) in ((1.3, 2.8, 0.98, 1.0), (1.3, 2.8, -1.0, -0.98), (2.22, 2.24, -0.98, 0.98)):
    box((x1 - x0, y1 - y0, 0.01), ((x0 + x1) / 2, (y0 + y1) / 2, 3.625), C['graph2'], skip=('-z',))
box((0.6, 0.6, 0.03), (2.55, -0.35, 3.63), C['graph1']); box((0.1, 0.12, 0.03), (2.55, -0.04, 3.66), C['amber'])
# ------------------------------------------------------------------ rear end + mud flaps (per truck)
if KIND == 'ht04':
    RX = -3.6
    box((0.14, 2.3, 0.24), (RX, 0, 1.12), C['graph1'])                                # rear under-run bar (below the tipping bed's sweep)
    chevrons(RX - 0.072, -1.1, 1.1, 1.02, 1.22, -1, n=10)
    for sy in (-1, 1):
        box((0.04, 0.2, 0.08), (RX - 0.08, sy * 0.95, 1.31), C['red'])               # tail lights
        cyl((RX, sy * 1.0, 1.24), (RX, sy * 1.0, 1.31), 0.06, C['white'], segs=10, cap0=False)   # rear corner lidar pucks
        cyl((RX, sy * 1.0, 1.31), (RX, sy * 1.0, 1.34), 0.062, None, segs=10, mat='glass', cap0=False, cap1=False)
        cyl((RX, sy * 1.0, 1.34), (RX, sy * 1.0, 1.36), 0.055, C['graph'], segs=10, cap0=False)
        box((0.035, 0.6, 0.78), (-3.68, sy * 1.5, 0.82), C['rubber'])               # mud flaps behind the rear tandem
        chevrons(-3.70, sy * 1.5 - 0.27, sy * 1.5 + 0.27, 0.5, 0.62, -1, n=4)
        box((0.06, 0.66, 0.06), (-3.66, sy * 1.5, 1.23), C['graph'])
        box((0.2, 0.06, 0.06), (-3.6, sy * 1.18, 1.23), C['graph'])
    box((0.04, 0.5, 0.12), (RX - 0.075, 0, 1.31), C['graph']); quad([(RX - 0.096, -0.12, 1.29), (RX - 0.096, 0.12, 1.29), (RX - 0.096, 0.12, 1.34), (RX - 0.096, -0.12, 1.34)], None, 'glass')   # reversing camera
else:
    chevrons(-5.075 - 0.012, -1.2, 1.2, 1.27, 1.45, -1, n=10)                          # replaces the look of the vertical blocks on the under-run bumper
    for sy in (-1, 1):
        cyl((-5.0, sy * 1.05, 1.45), (-5.0, sy * 1.05, 1.52), 0.06, C['white'], segs=10, cap0=False)
        cyl((-5.0, sy * 1.05, 1.52), (-5.0, sy * 1.05, 1.55), 0.062, None, segs=10, mat='glass', cap0=False, cap1=False)
        cyl((-5.0, sy * 1.05, 1.55), (-5.0, sy * 1.05, 1.57), 0.055, C['graph'], segs=10, cap0=False)
        chevrons(-3.80, sy * 1.5 - 0.27, sy * 1.5 + 0.27, 0.86, 0.98, -1, n=4)       # chevron band on the existing mud flaps
    box((0.05, 0.4, 0.1), (-4.97, 0, 1.6), C['graph'])
    quad([(-4.998, -0.1, 1.58), (-4.998, 0.1, 1.58), (-4.998, 0.1, 1.62), (-4.998, -0.1, 1.62)], None, 'glass')
    for sy in (-1, 1): box((1.6, 0.012, 0.03), (-1.8, sy * 1.47, 1.75), C['graph'])   # deck-side panel line
# ------------------------------------------------------------------ light weathering on the new paint parts
import random
rr = random.Random(7)
def weather(col, z):
    if col is None: return None
    t = max(0.0, min(1.0, (1.9 - z) / 1.6)) ** 1.6 * 0.33 + rr.uniform(0, 0.05)
    return tuple((np.array(col) * (1 - t) + np.array(C['dust']) * t) * rr.uniform(0.95, 1.03))
F = [(p, weather(c, float(np.mean([q[2] for q in p]))) if c not in (C['cyan_hi'], C['cyan'], C['amber'], C['red'], C['lamp']) else c, m, b) for p, c, m, b in F]

# ------------------------------------------------------------------ merge into the skinned primitive
g = GLB(SRC); j = g.j; mesh = j['meshes'][0]; prim = mesh['primitives'][0]; A = prim['attributes']
skin = j['skins'][0]; jn = {g.name(n): k for k, n, _ in g.skin_mats()}; Minv = {k: np.linalg.inv(M) for k, n, M in g.skin_mats()}
def b2g(p): return np.array((p[0], p[2], -p[1]))
def build(mat):
    P, N, Cc, Jt, idx = [], [], [], [], []
    for pts, col, m, bone in F:
        if m != mat: continue
        G = [b2g(p) for p in pts]
        n = np.cross(G[1] - G[0], G[2] - G[0])
        if np.linalg.norm(n) < 1e-12: n = np.cross(G[2] - G[0], G[3] - G[0]) if len(G) > 3 else np.array((0, 1.0, 0))
        n = n / (np.linalg.norm(n) + 1e-12); k = jn[bone]; Mi = Minv[k]
        base = len(P)
        for q in G: P.append((Mi @ np.append(q, 1))[:3]); N.append(Mi[:3, :3] @ n); Cc.append(col or (1, 1, 1)); Jt.append(k)
        for t in range(1, len(G) - 1): idx += [base, base + t, base + t + 1]
    N = np.array(N); N /= np.linalg.norm(N, axis=1, keepdims=True)
    return np.array(P), N, np.array(Cc), np.array(Jt), np.array(idx)
P0 = g.acc(A['POSITION']); N0 = g.acc(A['NORMAL']); C0 = g.acc(A['COLOR_0']); J0 = g.acc(A['JOINTS_0']); W0 = g.acc(A['WEIGHTS_0']); I0 = g.acc(prim['indices']).ravel()
P, N, Cc, Jt, idx = build('paint'); n0 = len(P0)
col8 = np.clip(np.round(np.c_[Cc, np.ones(len(Cc))] * 255), 0, 255).astype(np.uint8)
J8 = np.zeros((len(P), 4), np.uint8); J8[:, 0] = Jt; W8 = np.zeros((len(P), 4), np.uint8); W8[:, 0] = 255
repl = {A['POSITION']: np.vstack([P0, P]).astype(np.float32), A['NORMAL']: np.vstack([N0, N]).astype(np.float32),
        A['COLOR_0']: np.vstack([C0, col8]), A['JOINTS_0']: np.vstack([J0, J8]), A['WEIGHTS_0']: np.vstack([W0, W8]),
        prim['indices']: np.concatenate([I0, idx + n0]).astype(np.uint32 if n0 + len(P) > 65535 else np.uint16).reshape(-1, 1)}
if n0 + len(P) > 65535: j['accessors'][prim['indices']]['componentType'] = 5125
for t in prim.get('targets', []):
    for k, ai in t.items(): repl[ai] = np.vstack([g.acc(ai), np.zeros((len(P), 3), np.float32)])
# glass primitive
Pg, Ng, _, Jg, ig = build('glass')
def new_acc(arr, ct, typ, norm=False, mm=False):
    a = {'componentType': ct, 'type': typ, 'count': len(arr), 'bufferView': 0}
    if norm: a['normalized'] = True
    if mm: a['min'] = [0] * arr.shape[1]; a['max'] = [0] * arr.shape[1]
    j['accessors'].append(a); i = len(j['accessors']) - 1; repl[i] = arr; return i
Jg8 = np.zeros((len(Pg), 4), np.uint8); Jg8[:, 0] = Jg; Wg8 = np.zeros((len(Pg), 4), np.uint8); Wg8[:, 0] = 255
gp = {'attributes': {'POSITION': new_acc(Pg.astype(np.float32), 5126, 'VEC3', mm=True), 'NORMAL': new_acc(Ng.astype(np.float32), 5126, 'VEC3'),
                     'JOINTS_0': new_acc(Jg8, 5121, 'VEC4'), 'WEIGHTS_0': new_acc(Wg8, 5121, 'VEC4', norm=True)},
      'indices': new_acc(ig.astype(np.uint16).reshape(-1, 1), 5123, 'SCALAR'), 'mode': 4}
if prim.get('targets'): gp['targets'] = [{'POSITION': new_acc(np.zeros((len(Pg), 3), np.float32), 5126, 'VEC3', mm=True), 'NORMAL': new_acc(np.zeros((len(Pg), 3), np.float32), 5126, 'VEC3')} for _ in prim['targets']]
j['materials'].append({'name': 'SHM_Glass', 'pbrMetallicRoughness': {'baseColorFactor': [0.018, 0.03, 0.05, 1.0], 'metallicFactor': 0.0, 'roughnessFactor': 0.1}})
gp['material'] = len(j['materials']) - 1
mesh['primitives'].append(gp)
_orig_acc = g.acc
def acc2(i): return repl[i] if i in repl else _orig_acc(i)
g.acc = acc2
# bake the leftover dequantisation transform of the mesh node into the vertices + inverse bind matrices, so the repack does not stack
# a second quantisation node (world = J * IBM' * (T v) with IBM' = IBM * T^-1 -> identical rest pose and skinning)
mn = next(i for i, N in enumerate(j['nodes']) if N.get('mesh') == 0); T = g.node_local(mn); Ti = np.linalg.inv(T); sc = np.cbrt(np.linalg.det(T[:3, :3]))
for p in mesh['primitives']:
    ai = p['attributes']['POSITION']; P_ = g.acc(ai).astype(np.float64); repl[ai] = (P_ @ T[:3, :3].T + T[:3, 3]).astype(np.float32)
    for t in p.get('targets', []): repl[t['POSITION']] = (g.acc(t['POSITION']) * sc).astype(np.float32)
ib = skin['inverseBindMatrices']; IB = g.acc(ib).reshape(-1, 4, 4).transpose(0, 2, 1)
repl[ib] = np.stack([(M @ Ti).T.reshape(16) for M in IB]).astype(np.float32)
for k in ('translation', 'rotation', 'scale', 'matrix'): j['nodes'][mn].pop(k, None)
# put mesh + skin back on the named parent (Truck_Mesh / FB05 mesh node, as the Blender export had it) so gltfpack rebuilds the original layout
if not j['nodes'][mn].get('name'):
    par = next(k for k, M in enumerate(j['nodes']) if mn in M.get('children', []))
    j['nodes'][par]['mesh'] = j['nodes'][mn].pop('mesh'); j['nodes'][par]['skin'] = j['nodes'][mn].pop('skin')
g.save(OUT, {})
tri0 = len(I0) // 3; print(json.dumps({'kind': KIND, 'orig_tris': tri0, 'added_paint_tris': len(idx) // 3, 'glass_tris': len(ig) // 3, 'total_tris': tri0 + len(idx) // 3 + len(ig) // 3,
                  'added_verts': len(P) + len(Pg), 'faces': len(F)}))
