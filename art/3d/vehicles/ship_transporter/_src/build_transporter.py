"""Planet Stack - Lv10 SHIP TRANSPORTER concepts A + B (stills for approval; no animation yet). Blender 4.2, headless, Cycles CPU.

  blender -b -P build_transporter.py -- --concept A|B --loaded 1|0 --out DIR [--shot hero|side|plan|none] [--w 3840 --h 2160]
         [--samples 24] [--glb 1 (game-look preview GLB: flat palette materials, for the three.js game-camera proofs)]

Frame (Blender, Z up, metres): ship axis at the origin, transporter travels along X, OPEN end of the U at -X, cross member at +X,
camera side = -Y (glTF +Z). Ship = the 82131aba pad ship (Ship_Placeholder + Cargo_Door from launch_pad_game.glb, dequantized to
/tmp/st_work/pad_dq.glb by gltf-transform; read only). Its 6 legs reach r 9.26 m below 4 m (az 30/90/150/...), hull r 4.49 m:
both concepts keep every ground member at |y| >= 9.7 m and every cross member at x >= 11 m, so the U drives round the legs.
  A  'ST-10A' tracked crawler: 4 twin-track trucks, two box girders + a rear cross girder, two 31 m cradle towers with 3 clamp
     arms (8.5 / 20 / 29 m) and a swing gate that closes the open end.
  B  'ST-10B' multi-axle wheeled platform (SPMT-style): 2 x 7 steerable axle lines (2.5 m wheels), a rear portal arch, four
     hydraulic knuckle cradle arms (10 m) + an upper horseshoe stabiliser collar (24.5 m) on an A-frame from the portal.
House style: Mine concept B (white + graphite + cyan, stainless ship), shared helpers from mine_concepts/_src/mc_common.py (import only).
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', '..', 'mine_concepts', '_src')))
import bpy, bmesh
from mathutils import Vector, Matrix
from mc_common import *
from mc_common import _obj, _nodes

A = argv(); CON = A.get('concept', 'A'); LOADED = A.get('loaded', '1') == '1'
OUT = os.path.abspath(A.get('out', '/tmp/st_out')); os.makedirs(OUT, exist_ok=True)
SHOT = A.get('shot', 'hero'); W, H = int(A.get('w', 3840)), int(A.get('h', 2160)); SAMPLES = int(A.get('samples', 24))
PAD_DQ = A.get('pad', '/tmp/st_work/pad_dq.glb')
reset(); rr = random.Random(7)
LIFT = 0.45 if LOADED else 0.0          # cradle jacks raise the ship 0.45 m: leg pads clear the ground while carried
G_IN, TRK = 9.7, 3.6                     # inner half-gap (legs reach 8.92 incl. pads) / track band width
X0, X1 = -12.5, 15.5                     # transporter length 28 m, open end at X0, cross member x >= 11
GAME = {}                                # material name -> game-preview hex (no PBR metal in game: shaded sides stay readable)

def P_(name, col, game=None, **k):
    m = M_paint(name, col, **k); GAME[m.name] = game or col; return m
def G_(name, col, strength=6.0, game=None):
    m = M_glow(name, col, strength); GAME[m.name] = game or col; m['glow'] = 1; return m
WHITE = P_('ST_White', '#e8edf5', rough=0.42, metal=0.05, grime=0.22, grime_col='#a19b93', wear=0.08, wear_col='#9aa3ad', coat=0.15, panel=1.2, bevel=0.03)
PALE = P_('ST_Pale', '#c9d3e6', rough=0.5, metal=0.05, grime=0.18, grime_col='#9a948c', bevel=0.02)
GRAPH = P_('ST_Graphite', '#2a3245', game='#5d6880', rough=0.5, metal=0.3, grime=0.2, grime_col='#5b5650', bevel=0.02)
GRAPH2 = P_('ST_Graphite2', '#3a4258', game='#6b7690', rough=0.45, metal=0.35, bevel=0.02)
STEEL = P_('ST_Steel', '#8794ad', game='#97a3bb', rough=0.35, metal=0.7, grime=0.15, grime_col='#5b5650', bevel=0.01)
TRACK = P_('ST_Track', '#4a4f58', game='#7a808b', rough=0.62, metal=0.6, grime=0.55, grime_col='#7d7b79', dirt_scale=3.5, bevel=0.02)
TYRE = P_('ST_Tyre', '#3b3f46', game='#6e737c', rough=0.75, metal=0.2, grime=0.6, grime_col='#8b8987', dirt_scale=4.0, bevel=0.02)
CHROME = P_('ST_Rod', '#d9dee6', game='#c3cad6', rough=0.12, metal=1.0, bevel=0.005)
HAZ = P_('ST_Hazard', '#ffb020', hazard=('#ffb020', '#2a3245'), hazard_scale=1.6, rough=0.5, metal=0.1, bevel=0.01, game='#c99a3c')
PADM = P_('ST_PadRubber', '#252a33', game='#58606e', rough=0.85, metal=0.0, bevel=0.02)
CYAN = G_('ST_GlowCyan', '#3ad0ff', 7.0); AMB = G_('ST_GlowAmber', '#ffb020', 9.0); RED = G_('ST_GlowRed', '#f25f5c', 6.0)
INK = P_('ST_Ink', '#2a3245', rough=0.5, metal=0.0, bevel=0.0)
GLASS = M_glass('ST_Glass', '#7fdfff'); GAME[GLASS.name] = '#2d5d74'

def rbox(n, size, loc, mat, rot=(0, 0, 0), bev=0.06):
    return box(n, size, loc, mat, rot=rot, bevel=bev, segs=2)
def tag(n, body, loc, rot, size=0.5, mat=INK):
    return text(n, body, loc, rot, size, mat, extrude=0.01)

# ------------------------------------------------------------------ shared parts
def lidar(x, y, z):
    cyl('lidar_post', 0.12, 1.4, (x, y, z + 0.7), GRAPH, segs=10)
    cyl('lidar_head', 0.32, 0.36, (x, y, z + 1.55), WHITE, segs=16)
    cyl('lidar_band', 0.335, 0.08, (x, y, z + 1.55), CYAN, segs=16, bevel=0)
    sphere('beacon', 0.13, (x, y, z + 1.86), AMB, sub=2)
def handrail(x0, x1, y, z, h=1.1, step=2.0):
    n = max(2, int(abs(x1 - x0) / step) + 1)
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1); rod('rail_post', (x, y, z), (x, y, z + h), 0.035, STEEL, segs=8)
    rod('rail_top', (x0, y, z + h), (x1, y, z + h), 0.04, STEEL, segs=8); rod('rail_mid', (x0, y, z + h * 0.5), (x1, y, z + h * 0.5), 0.03, STEEL, segs=8)
def ladder(x, y, z0, z1, nrm=-1):
    for sx in (-0.3, 0.3): rod('lad_side', (x + sx, y, z0), (x + sx, y, z1), 0.035, STEEL, segs=8)
    k = z0 + 0.3
    while k < z1: rod('lad_rung', (x - 0.3, y, k), (x + 0.3, y, k), 0.025, STEEL, segs=6); k += 0.3
def hazard_plate(x, y, z, sx, sy, sz): box('haz', (sx, sy, sz), (x, y, z), HAZ, bevel=0.01)
def lamp_strip(p0, p1, w=0.08, mat=None): beam('strip', p0, p1, w, w, mat or CYAN, bevel=0)

def saddle(n, z, r_in, a_mid, a_span, depth=1.2, thick=0.35):
    """curved clamp pad hugging the hull (r_in) centred on azimuth a_mid (Blender angle from +X), rubber face + white backing + cyan edge"""
    for (r0, r1, mat, dz) in ((r_in, r_in + thick, PADM, depth), (r_in + thick, r_in + thick + 0.45, WHITE, depth * 1.1)):
        bm = bmesh.new(); seg = 14; vs = []
        for i in range(seg + 1):
            a = a_mid - a_span / 2 + a_span * i / seg
            for (r, h) in ((r0, -dz / 2), (r1, -dz / 2), (r1, dz / 2), (r0, dz / 2)):
                vs.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z + h)))
        for i in range(seg):
            for k in range(4):
                a0, a1 = 4 * i + k, 4 * i + (k + 1) % 4; b0, b1 = a0 + 4, a1 + 4
                bm.faces.new((vs[a0], vs[a1], vs[b1], vs[b0]))
        bm.faces.new([vs[k] for k in range(4)][::-1]); bm.faces.new([vs[4 * seg + k] for k in range(4)])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); _obj(bm, n, mat, bevel=0.02, angle=30)
    for s in (-1, 1):
        a = a_mid + s * a_span / 2; r = r_in + thick + 0.48
        cyl('pad_edge', 0.05, depth * 1.1, (r * math.cos(a), r * math.sin(a), z), CYAN, segs=8, bevel=0)

def track_unit(cx, cy, L, wdt, Ht, n_name='trk'):
    """one twin-track truck: two track loops (wdt each 1.65) with cleated shoes, sprocket/idler hubs, roller frame, white fairing"""
    for k, dy in enumerate((-wdt / 4 - 0.05, wdt / 4 + 0.05)):
        y = cy + dy; tw = wdt / 2 - 0.1; R = Ht / 2
        # track loop (stadium) as a ring of shoes
        per = 2 * (L - 2 * R) + 2 * math.pi * R; n = int(per / 0.62)
        for i in range(n):
            s = per * i / n; st = L - 2 * R
            if s < st: p = Vector((cx - st / 2 + s, y, Ht)); ang = 0
            elif s < st + math.pi * R: a = (s - st) / R; p = Vector((cx + st / 2 + R * math.sin(a), y, R + R * math.cos(a))); ang = a
            elif s < 2 * st + math.pi * R: p = Vector((cx + st / 2 - (s - st - math.pi * R), y, 0.0)); ang = math.pi
            else: a = (s - 2 * st - math.pi * R) / R; p = Vector((cx - st / 2 - R * math.sin(a), y, R - R * math.cos(a))); ang = math.pi + a
            nrm = Vector((math.sin(ang), 0, math.cos(ang)))
            box('shoe', (0.56, tw, 0.16), tuple(p - nrm * 0.0 + Vector((0, 0, 0.08 if ang == 0 else 0)) + nrm * 0.0), TRACK, rot=(0, -ang, 0), bevel=0.02)
            box('cleat', (0.14, tw, 0.14), tuple(p + nrm * 0.13), TRACK, rot=(0, -ang, 0), bevel=0.01)
        for xx in (cx - L / 2 + R, cx + L / 2 - R):
            cyl('sprocket', R - 0.25, tw * 0.7, (xx, y, R), GRAPH, rot=(math.pi / 2, 0, 0), segs=24)
            cyl('hub', 0.55, tw * 0.8, (xx, y, R), STEEL, rot=(math.pi / 2, 0, 0), segs=16)
        nr = int((L - 2 * R) / 1.1)
        for i in range(nr + 1):
            xx = cx - (L - 2 * R) / 2 + (L - 2 * R) * i / max(1, nr)
            cyl('roller', 0.38, tw * 0.6, (xx, y, 0.55), STEEL, rot=(math.pi / 2, 0, 0), segs=12)
        box('roller_frame', (L - 2 * R + 0.6, tw * 0.5, 1.0), (cx, y, 1.15), GRAPH, bevel=0.05)
    # truck frame / fairing over the twin tracks + leveling jacks to the girder
    rbox(n_name + '_frame', (L - 1.2, wdt + 0.3, 0.9), (cx, cy, Ht + 0.55), GRAPH2, bev=0.08)
    rbox(n_name + '_fair', (L - 2.4, wdt + 0.5, 0.35), (cx, cy, Ht + 1.12), WHITE, bev=0.1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            piston('jack', (cx + sx * (L / 2 - 2.2), cy + sy * (wdt / 2 - 0.4), Ht + 1.0), (cx + sx * (L / 2 - 2.2), cy + sy * (wdt / 2 - 0.4), Ht + 2.2), 0.28, GRAPH, CHROME, ext=0.5)
    hazard_plate(cx + L / 2 - 0.9, cy, Ht + 0.55, 0.12, wdt + 0.35, 0.6); hazard_plate(cx - L / 2 + 0.9, cy, Ht + 0.55, 0.12, wdt + 0.35, 0.6)

def wheel(x, y, z, R=1.25, wdt=0.75):
    """lunar wheel: graphite hub, open-mesh tyre with chevron grousers (no rubber, no logos)"""
    cyl('tyre', R, wdt, (x, y, z), TYRE, rot=(math.pi / 2, 0, 0), segs=40, bevel=0.06)
    n = 28
    for i in range(n):
        a = 2 * math.pi * i / n
        for s in (-1, 1):
            p = (x + (R + 0.03) * math.cos(a), y + s * wdt * 0.22, z + (R + 0.03) * math.sin(a))
            box('grouser', (0.1, wdt * 0.5, 0.08), p, TRACK, rot=(s * 0.45, -a + math.pi / 2, 0), bevel=0.0)
    cyl('rim', R * 0.62, wdt + 0.04, (x, y, z), STEEL, rot=(math.pi / 2, 0, 0), segs=24)
    cyl('hubcap', R * 0.32, wdt + 0.1, (x, y, z), GRAPH, rot=(math.pi / 2, 0, 0), segs=16)
    for i in range(6):
        a = 2 * math.pi * i / 6
        box('spoke', (R * 0.55, wdt + 0.06, 0.12), (x + R * 0.42 * math.cos(a), y, z + R * 0.42 * math.sin(a)), GRAPH2, rot=(0, -a, 0), bevel=0.01)

def astronaut_tender(loc, rot_z):
    a = astronaut(loc, rot_z=rot_z, c='Mine')
    # handheld controller tablet held in front (cyan screen)
    rot = Matrix.Rotation(rot_z, 4, 'Z')
    off = rot @ Vector((0, -0.42, 1.12))
    tb = box('tablet', (0.42, 0.04, 0.3), tuple(Vector(loc) + off), GRAPH, rot=(math.radians(55), 0, rot_z), bevel=0.01, c='Mine')
    sc = box('tablet_screen', (0.36, 0.01, 0.24), tuple(Vector(loc) + rot @ Vector((0, -0.44, 1.14))), CYAN, rot=(math.radians(55), 0, rot_z), bevel=0, c='Mine')
    for s in (-1, 1): rod('forearm', tuple(Vector(loc) + rot @ Vector((s * 0.3, -0.05, 1.0))), tuple(Vector(loc) + rot @ Vector((s * 0.17, -0.38, 1.08))), 0.075, bpy.data.materials['M_Suit'], segs=10, c='Mine')
    return a

# ------------------------------------------------------------------ CONCEPT A: tracked crawler + cradle towers
def concept_A():
    Ht = 3.4; GZ0, GZ1 = 4.2, 7.0                         # track height, box girder bottom/top
    for sy in (-1, 1):
        yc = sy * (G_IN + TRK / 2)
        for cx in (X0 + 5.25, X1 - 5.25): track_unit(cx, yc, 10.5, TRK, Ht)
        # box girder (side member): white, graphite belly, cyan pinstripe, walkway + rails
        rbox('girder', (X1 - X0, TRK + 0.4, GZ1 - GZ0), ((X0 + X1) / 2, yc, (GZ0 + GZ1) / 2), WHITE, bev=0.12)
        box('girder_belly', (X1 - X0 - 0.4, TRK + 0.2, 0.5), ((X0 + X1) / 2, yc, GZ0 + 0.05), GRAPH, bevel=0.04)
        lamp_strip((X0 + 0.3, yc + sy * (TRK / 2 + 0.21), GZ1 - 0.5), (X1 - 0.3, yc + sy * (TRK / 2 + 0.21), GZ1 - 0.5))
        lamp_strip((X0 + 0.3, yc - sy * (TRK / 2 + 0.21), GZ1 - 0.5), (X1 - 0.3, yc - sy * (TRK / 2 + 0.21), GZ1 - 0.5))
        for i in range(9):   # panel ribs on the outer face
            x = X0 + 1.5 + i * (X1 - X0 - 3) / 8; box('rib', (0.18, 0.08, GZ1 - GZ0 - 0.9), (x, yc + sy * (TRK / 2 + 0.22), (GZ0 + GZ1) / 2 + 0.1), PALE, bevel=0.02)
        handrail(X0 + 0.5, X1 - 0.5, yc + sy * (TRK / 2 - 0.1), GZ1)
        ladder(X0 + 1.2 + 6.0, yc + sy * (TRK / 2 + 0.35), 0.2, GZ1)
        hazard_plate(X0 + 0.05, yc, (GZ0 + GZ1) / 2, 0.14, TRK + 0.42, GZ1 - GZ0 - 0.4)
        tag('label', 'ST-10A', (X0 + 6.5, yc + sy * (TRK / 2 + 0.27), GZ0 + 1.25), (math.pi / 2, 0, 0 if sy < 0 else math.pi), 0.9)
        tag('label2', 'HEAVY TRANSPORT · AUTONOMOUS', (X0 + 14.0, yc + sy * (TRK / 2 + 0.27), GZ0 + 1.25), (math.pi / 2, 0, 0 if sy < 0 else math.pi), 0.42)
        # power / drive module on the girder top, rear half
        rbox('pwr', (6.0, TRK - 0.3, 1.6), (X1 - 5.0, yc, GZ1 + 0.8), GRAPH2, bev=0.1)
        for i in range(5): box('rad_fin', (0.12, TRK - 0.6, 1.3), (X1 - 7.4 + i * 1.2, yc, GZ1 + 2.15), WHITE, bevel=0.01)
        lamp_strip((X1 - 7.9, yc + sy * (TRK / 2 - 0.12), GZ1 + 1.3), (X1 - 2.1, yc + sy * (TRK / 2 - 0.12), GZ1 + 1.3))
        lidar(X0 + 0.8, yc + sy * 1.2, GZ1); lidar(X1 - 0.8, yc + sy * 1.2, GZ1)
        # cradle tower: two white plated legs + graphite bracing, 31 m
        TZ = 31.0
        for sx in (-1, 1):
            rbox('tower_leg', (1.3, 1.3, TZ - GZ1), (sx * 2.6, yc, (GZ1 + TZ) / 2), WHITE, bev=0.12)
            lamp_strip((sx * 2.6 + sx * 0.66, yc - sy * 0.66, GZ1 + 1.0), (sx * 2.6 + sx * 0.66, yc - sy * 0.66, TZ - 1.0), w=0.07)
        z = GZ1 + 1.0
        while z < TZ - 2.5:
            beam('tw_x', (-2.6, yc, z), (2.6, yc, z + 3.1), 0.32, 0.32, GRAPH, bevel=0.02); beam('tw_x', (2.6, yc, z), (-2.6, yc, z + 3.1), 0.32, 0.32, GRAPH, bevel=0.02)
            beam('tw_h', (-2.6, yc, z), (2.6, yc, z), 0.36, 0.4, GRAPH2, bevel=0.02); z += 3.1
        rbox('tower_cap', (6.8, 2.2, 1.2), (0, yc, TZ + 0.4), WHITE, bev=0.15); sphere('tw_beacon', 0.22, (0, yc, TZ + 1.25), RED, sub=2)
        ladder(2.6 + 0.95, yc, GZ1, TZ - 0.3)
        # clamp arms at 8.5 / 20 / 29 m: horizontal telescopic box arm + hydraulic + curved saddle on the hull
        for (zc, rh) in ((8.5, 4.49), (20.0, 4.49), (29.0, 4.06)):
            rin = rh + 0.02 if LOADED else rh + 1.6        # empty: arms retracted 1.6 m
            ya, yb = yc, sy * (rin + 0.78); ym = ya + (yb - ya) * 0.55
            rbox('arm_outer', (2.2, abs(ym - ya) + 0.6, 1.5), (0, (ya + ym) / 2, zc), WHITE, bev=0.1)
            rbox('arm_inner', (1.6, abs(yb - ym) + 0.6, 1.1), (0, (ym + yb) / 2, zc), STEEL, bev=0.06)
            piston('arm_cyl', (0, ya - sy * 0.8, zc + 1.25), (0, ym - sy * 0.2, zc + 0.85), 0.22, GRAPH, CHROME, ext=0.55)
            lamp_strip((-1.11, ya - sy * 0.8, zc + 0.3), (-1.11, ym, zc + 0.3), w=0.06)
            saddle('saddle', zc, rin, math.radians(90 if sy > 0 else -90), math.radians(70), depth=1.3)
    # rear cross girder (x 11 .. 15.5) + control / sensor head; no cab (autonomous)
    yy = G_IN + TRK
    rbox('cross', (X1 - 11.0, 2 * yy, GZ1 - GZ0 + 0.4), ((11.0 + X1) / 2, 0, (GZ0 + GZ1) / 2 + 0.2), WHITE, bev=0.12)
    box('cross_belly', (X1 - 11.2, 2 * G_IN - 0.2, 0.5), ((11.0 + X1) / 2, 0, GZ0 + 0.05), GRAPH, bevel=0.04)
    hazard_plate(11.0 - 0.02, 0, GZ0 + 0.55, 0.1, 2 * G_IN - 0.4, 0.7)
    rbox('ctl_pod', (2.6, 6.0, 1.8), (13.2, 0, GZ1 + 1.1), GRAPH2, bev=0.15)
    box('ctl_glass', (0.05, 5.0, 0.5), (14.53, 0, GZ1 + 1.35), CYAN, bevel=0)
    for s in (-1, 1): cyl('ant', 0.05, 2.5, (13.2, s * 2.2, GZ1 + 3.2), STEEL, segs=8); sphere('ant_tip', 0.1, (13.2, s * 2.2, GZ1 + 4.45), AMB, sub=2)
    handrail(11.3, 15.2, -yy + 0.3, GZ1); handrail(11.3, 15.2, yy - 0.3, GZ1)
    lamp_strip((X1 + 0.02, -yy + 0.3, GZ1 - 0.5), (X1 + 0.02, yy - 0.3, GZ1 - 0.5))
    tag('lbl_rear', 'ST-10A', (X1 + 0.03, 0, GZ0 + 1.0), (math.pi / 2, 0, math.pi / 2), 1.0)
    # swing gate across the open end (x X0): closed when loaded, swung open 90 deg when empty
    gL = 2 * G_IN
    if LOADED:
        rbox('gate', (1.2, gL, 1.6), (X0 - 0.2, 0, GZ1 - 0.6), WHITE, bev=0.1)
        hazard_plate(X0 - 0.82, 0, GZ1 - 0.6, 0.06, gL - 0.4, 0.7)
        for s in (-1, 1): cyl('gate_pin', 0.45, 2.2, (X0 - 0.2, s * (G_IN - 0.1), GZ1 - 0.6), GRAPH, segs=16)
        lamp_strip((X0 - 0.83, -G_IN + 0.4, GZ1 + 0.21), (X0 - 0.83, G_IN - 0.4, GZ1 + 0.21))
    else:
        rbox('gate', (gL, 1.2, 1.6), (X0 - 0.2 - gL / 2 + 0.6, -G_IN - 0.4, GZ1 - 0.6), WHITE, bev=0.1)
        hazard_plate(X0 - gL / 2, -G_IN - 1.02, GZ1 - 0.6, gL - 0.4, 0.06, 0.7)
        cyl('gate_pin', 0.45, 2.2, (X0 - 0.2, -(G_IN - 0.1), GZ1 - 0.6), GRAPH, segs=16)

# ------------------------------------------------------------------ CONCEPT B: multi-axle wheeled platform + hydraulic cradle arms
def concept_B():
    WR = 1.25; DZ0, DZ1 = 3.1, 4.4; BW = 4.2
    for sy in (-1, 1):
        yc = sy * (G_IN + BW / 2)
        rbox('deck', (X1 - X0, BW, DZ1 - DZ0), ((X0 + X1) / 2, yc, (DZ0 + DZ1) / 2), WHITE, bev=0.1)
        box('deck_skirt', (X1 - X0 - 0.3, BW - 0.3, 0.45), ((X0 + X1) / 2, yc, DZ0 - 0.1), GRAPH, bevel=0.04)
        lamp_strip((X0 + 0.3, yc + sy * (BW / 2 + 0.02), DZ1 - 0.25), (X1 - 0.3, yc + sy * (BW / 2 + 0.02), DZ1 - 0.25))
        lamp_strip((X0 + 0.3, yc - sy * (BW / 2 + 0.02), DZ1 - 0.25), (X1 - 0.3, yc - sy * (BW / 2 + 0.02), DZ1 - 0.25))
        for i in range(7):   # axle lines: turntable + pendulum axle + 2 dual-wheel sets + suspension cylinder
            x = X0 + 2.0 + i * (X1 - X0 - 4.0) / 6
            cyl('turntable', 0.9, 0.35, (x, yc, DZ0 - 0.4), GRAPH2, segs=20)
            box('pendulum', (0.7, BW - 0.6, 0.55), (x, yc, WR + 0.25), GRAPH, bevel=0.05)
            piston('susp', (x + 0.6, yc, DZ0 - 0.2), (x + 0.6, yc, WR + 0.55), 0.17, GRAPH, CHROME, ext=0.5)
            for dy in (-1.3, 1.3): wheel(x, yc + dy, WR, WR, 0.8)
            box('mudguard', (2.9, BW - 0.2, 0.12), (x, yc, 2 * WR + 0.35), PALE, bevel=0.03)
        for i in range(8):
            x = X0 + 0.9 + i * (X1 - X0 - 1.8) / 7; box('deck_rib', (0.16, 0.06, DZ1 - DZ0 - 0.3), (x, yc + sy * (BW / 2 + 0.03), (DZ0 + DZ1) / 2), PALE, bevel=0.01)
        hazard_plate(X0 - 0.02, yc, (DZ0 + DZ1) / 2, 0.12, BW + 0.02, DZ1 - DZ0 - 0.2)
        handrail(X0 + 0.4, X1 - 0.4, yc + sy * (BW / 2 - 0.15), DZ1)
        ladder(X0 + 4.0, yc + sy * (BW / 2 + 0.3), 0.2, DZ1)
        tag('label', 'ST-10B', (X0 + 6.0, yc + sy * (BW / 2 + 0.05), DZ0 - 0.1), (math.pi / 2, 0, 0 if sy < 0 else math.pi), 0.55)
        tag('label2', 'MODULAR CARRIER · AUTONOMOUS', (X0 + 13.5, yc + sy * (BW / 2 + 0.05), DZ0 - 0.1), (math.pi / 2, 0, 0 if sy < 0 else math.pi), 0.36)
        # power pack pods on the deck (white shells, cyan vents)
        for px in (X0 + 2.6, X1 - 6.0):
            rbox('pp', (3.4, BW - 0.8, 2.0), (px, yc, DZ1 + 1.0), WHITE, bev=0.25)
            box('pp_vent', (2.6, 0.04, 0.5), (px, yc + sy * (BW / 2 - 0.38), DZ1 + 1.2), GRAPH, bevel=0)
            lamp_strip((px - 1.3, yc + sy * (BW / 2 - 0.37), DZ1 + 1.6), (px + 1.3, yc + sy * (BW / 2 - 0.37), DZ1 + 1.6), w=0.06)
        lidar(X0 + 0.6, yc, DZ1); lidar(X1 - 0.6, yc + sy * 1.4, DZ1)
        # hydraulic knuckle cradle arms (2 per side): base on deck at x = +-6, boom up + knuckle in to a saddle on the hull at 10 m
        for sx in (-1, 1):
            bx = sx * 6.0; base = Vector((bx, yc - sy * 0.4, DZ1))
            a_mid = math.radians(90 + sx * -20) if sy > 0 else math.radians(-90 + sx * 20)
            rin = 4.49 + (0.02 if LOADED else 1.8); zc = 10.0
            pad = Vector((math.cos(a_mid) * (rin + 0.8), math.sin(a_mid) * (rin + 0.8), zc))
            knee = Vector((bx * 0.75, sy * (G_IN + 0.6), 11.6 if LOADED else 12.4))
            rbox('arm_base', (2.4, 2.4, 1.2), (base.x, base.y, DZ1 + 0.6), GRAPH2, bev=0.12)
            cyl('arm_slew', 1.0, 0.5, (base.x, base.y, DZ1 + 1.45), STEEL, segs=20)
            beam('boom', base + Vector((0, 0, 1.6)), knee, 1.1, 1.3, WHITE, bevel=0.1)
            beam('stick', knee, pad, 0.9, 1.0, WHITE, bevel=0.08)
            sphere('knuckle', 0.75, knee, GRAPH, sub=2)
            piston('boom_cyl', base + Vector((sx * -1.0, 0, 1.2)) + Vector((0, sy * 0.3, 0)), base.lerp(knee, 0.62) + Vector((0, sy * 0.7, 0.4)), 0.3, GRAPH, CHROME)
            piston('stick_cyl', base.lerp(knee, 0.7) + Vector((0, 0, 0.9)), knee.lerp(pad, 0.55) + Vector((0, 0, 0.75)), 0.24, GRAPH, CHROME)
            lamp_strip(base.lerp(knee, 0.15) + Vector((0, 0, 0.67)), base.lerp(knee, 0.9) + Vector((0, 0, 0.67)), w=0.07)
            saddle('saddle', zc, rin, a_mid, math.radians(50), depth=1.6)
    # rear portal arch (x 12.5..15.5, top 12 m) + A-frame stabiliser mast + horseshoe collar at 24.5 m
    yy = G_IN + BW
    for sy in (-1, 1):
        for xx in (12.6, 15.0):
            rbox('portal_post', (1.1, 1.3, 12.0 - DZ1), (xx, sy * (G_IN + 1.2), (DZ1 + 12.0) / 2), WHITE, bev=0.12)
        beam('portal_brace', (12.6, sy * (G_IN + 1.2), DZ1 + 0.5), (15.0, sy * (G_IN + 1.2), 11.0), 0.35, 0.35, GRAPH, bevel=0.02)
        lamp_strip((15.56, sy * (G_IN + 1.2), DZ1 + 0.5), (15.56, sy * (G_IN + 1.2), 11.4), w=0.07)
    rbox('portal_beam', (3.6, 2 * (G_IN + 1.85), 1.6), (13.8, 0, 12.4), WHITE, bev=0.15)
    box('portal_belly', (3.4, 2 * G_IN, 0.3), (13.8, 0, 11.55), GRAPH, bevel=0.03)
    hazard_plate(13.8, 0, 11.45, 3.0, 2 * G_IN - 1.0, 0.06)
    rbox('ctl_pod', (2.4, 5.0, 1.6), (13.8, 0, 14.0), GRAPH2, bev=0.15); box('ctl_glass', (0.05, 4.2, 0.45), (15.03, 0, 14.15), CYAN, bevel=0)
    tag('lbl_rear', 'ST-10B', (14.6, 0, 12.4), (math.pi / 2, 0, math.pi / 2), 0.9)
    zc = 24.5; rin = 4.17 + (0.02 if LOADED else 1.5)
    top = Vector((9.6 + (0 if LOADED else 1.5), 0, zc))
    for sy in (-1, 1): beam('mast', (14.2, sy * 3.2, 13.2), top + Vector((0, sy * 1.6, -0.6)), 0.9, 0.9, WHITE, bevel=0.08)
    beam('mast_x', (14.2, -3.2, 15.5), (14.2, 3.2, 15.5), 0.5, 0.5, GRAPH, bevel=0.03)
    piston('mast_cyl', (14.2, 0, 13.4), top + Vector((1.0, 0, -1.4)), 0.3, GRAPH, CHROME)
    # horseshoe collar: open toward -X so it slides on/off from the portal side
    for k in range(9):
        a0 = math.radians(-120 + 240 * k / 9); a1 = math.radians(-120 + 240 * (k + 1) / 9); r = rin + 1.1
        beam('collar', (r * math.cos(a0) + (0 if LOADED else 1.5), r * math.sin(a0), zc), (r * math.cos(a1) + (0 if LOADED else 1.5), r * math.sin(a1), zc), 1.2, 1.4, WHITE, bevel=0.08)
    lamp_strip((rin + 1.75 + (0 if LOADED else 1.5), -1.5, zc + 0.3), (rin + 1.75 + (0 if LOADED else 1.5), 1.5, zc + 0.3), w=0.07)
    for am in (-80, 0, 80):
        s = saddle('collar_pad', zc, rin, math.radians(am), math.radians(34), depth=1.0)
    if not LOADED:
        for o in [o for o in bpy.data.objects if o.name.startswith('collar_pad') or o.name.startswith('pad_edge')]:
            if o.location.z > 20 or True: pass
        # shift collar pads with the collar (built at the origin ring): move all objects named collar_pad* by +1.5 x
        for o in bpy.data.objects:
            if o.name.startswith('collar_pad'): o.location.x += 1.5
    hazard_plate(X1 - 0.02 + 0.0, 0, DZ0 + 0.7, 0.1, 2 * yy, 0.5) if False else None

# ------------------------------------------------------------------ ship (82131aba pad ship, read only) + road + ground
def import_ship():
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=PAD_DQ); new = [o for o in bpy.data.objects if o not in before]
    keep = [o for o in new if o.type == 'MESH' and any(p and p.name.split('.')[0] in ('Ship_Placeholder', 'Cargo_Door') for p in (o, o.parent, o.parent.parent if o.parent else None))]
    for o in keep:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o not in keep: bpy.data.objects.remove(o, do_unlink=True)
    ship = bpy.data.objects.new('Ship', None); coll('Mine').objects.link(ship)
    m = bpy.data.materials.new('ST_ShipVC'); nt, b = _nodes(m)
    vc = nt.nodes.new('ShaderNodeVertexColor'); nt.links.new(vc.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Metallic'].default_value = 0.45; b.inputs['Roughness'].default_value = 0.4
    for o in keep:
        for c in list(o.users_collection): c.objects.unlink(o)
        coll('Mine').objects.link(o)
        if o.data.color_attributes: vc.layer_name = o.data.color_attributes[0].name
        o.data.materials.clear(); o.data.materials.append(m)
        o.location.y -= 13.0; o.location.z += LIFT     # glTF z -13 -> Blender y +13: re-centre on the transporter axis
        o['ship'] = 1
    return keep

def road_material():
    """transport road: graded, sintered regolith with two crawler-track lanes (transverse cleat imprints), not tyre trails"""
    m = bpy.data.materials.new('ST_RoadCrawler'); nt, b = _nodes(m); N = nt.nodes
    tc = N.new('ShaderNodeTexCoord'); P = tc.outputs['Object']; sep = N.new('ShaderNodeSeparateXYZ'); nt.links.new(P, sep.inputs[0])
    def mr(v, a, b_, c0=0.0, c1=1.0):
        r = N.new('ShaderNodeMapRange'); r.inputs['From Min'].default_value = a; r.inputs['From Max'].default_value = b_
        r.inputs['To Min'].default_value = c0; r.inputs['To Max'].default_value = c1; nt.links.new(v, r.inputs['Value']); return r.outputs[0]
    def op(o, x, y):
        n = N.new('ShaderNodeMath'); n.operation = o
        for i, v in enumerate((x, y)):
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: nt.links.new(v, n.inputs[i])
        return n.outputs[0]
    ay = op('ABSOLUTE', sep.outputs['Y'], 0)
    lane = op('MULTIPLY', mr(ay, G_IN - 0.4, G_IN + 0.2), mr(ay, G_IN + TRK + 0.6, G_IN + TRK - 0.2))      # 1 inside a track lane
    cleat = op('GREATER_THAN', op('FRACT', op('MULTIPLY', sep.outputs['X'], 1 / 0.62), 0), 0.72)          # 0.62 m shoe pitch
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.6; nz.inputs['Detail'].default_value = 6; nt.links.new(P, nz.inputs['Vector'])
    fine = N.new('ShaderNodeTexNoise'); fine.inputs['Scale'].default_value = 9; fine.inputs['Detail'].default_value = 10; nt.links.new(P, fine.inputs['Vector'])
    base = N.new('ShaderNodeMix'); base.data_type = 'RGBA'; nt.links.new(nz.outputs['Fac'], base.inputs['Factor'])
    base.inputs[6].default_value = hexc('#7f7d7a'); base.inputs[7].default_value = hexc('#93918d')
    lanec = N.new('ShaderNodeMix'); lanec.data_type = 'RGBA'; nt.links.new(lane, lanec.inputs['Factor']); nt.links.new(base.outputs[2], lanec.inputs[6]); lanec.inputs[7].default_value = hexc('#6c6a67')
    groove = op('MULTIPLY', lane, cleat)
    gc = N.new('ShaderNodeMix'); gc.data_type = 'RGBA'; nt.links.new(op('MULTIPLY', groove, 0.55), gc.inputs['Factor']); nt.links.new(lanec.outputs[2], gc.inputs[6]); gc.inputs[7].default_value = hexc('#4f4d4b')
    edge = mr(ay, 17.2, 17.6)   # graded edge band
    ec = N.new('ShaderNodeMix'); ec.data_type = 'RGBA'; nt.links.new(op('MULTIPLY', edge, 0.6), ec.inputs['Factor']); nt.links.new(gc.outputs[2], ec.inputs[6]); ec.inputs[7].default_value = hexc('#a7a49f')
    nt.links.new(ec.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.92
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.8; bump.inputs['Distance'].default_value = 0.06
    nt.links.new(op('ADD', op('MULTIPLY', groove, -1.0), op('MULTIPLY', fine.outputs['Fac'], 0.25)), bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m

def build_road(x0=-140, x1=140, half=18.0):
    m = road_material(); bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=1); bmesh.ops.transform(bm, matrix=mat4(((x0 + x1) / 2, 0, 0.03), (0, 0, 0), ((x1 - x0) / 2, half, 1)), verts=bm.verts)
    o = _obj(bm, 'transport_road', m, c='Stage', smooth=False)
    for s in (-1, 1):   # low graded shoulders + reflector posts every 12 m (cyan / amber tops)
        box('shoulder', (x1 - x0, 2.6, 0.35), ((x0 + x1) / 2, s * (half + 1.1), 0.12), M_ground_ref, rot=(s * -0.12, 0, 0), bevel=0.4, c='Stage')
        x = x0
        while x < x1:
            cyl('post', 0.09, 1.1, (x, s * (half + 0.4), 0.55), GRAPH, segs=8, c='Stage'); cyl('post_top', 0.11, 0.18, (x, s * (half + 0.4), 1.1), CYAN if s < 0 else AMB, segs=8, bevel=0, c='Stage'); x += 12.0
    return o

M_ground_ref = M_ground()
def ground():
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=60, y_segments=60, size=300)
    for v in bm.verts:
        d = abs(v.co.y); v.co.z = -0.02 + (0 if d < 26 else min(1.2, (d - 26) * 0.02) * (0.5 + 0.5 * math.sin(v.co.x * 0.05 + v.co.y * 0.03)))
    _obj(bm, 'ground', M_ground_ref, c='Stage', smooth=True)

# ------------------------------------------------------------------ build
(concept_A if CON == 'A' else concept_B)()
ship = import_ship() if LOADED else []
# tender: walks alongside on the camera side near the front corner, tablet in hand, facing the direction of travel
astronaut_tender((X0 + 4.0, -(G_IN + TRK + 3.2), 0.0), rot_z=math.radians(-90))
for o in coll('Mine').all_objects:
    if o.type == 'MESH' and not o.get('ship'): o['part'] = 1

def tris(objs):
    dg = bpy.context.evaluated_depsgraph_get(); t = 0
    for o in objs:
        if o.type != 'MESH': continue
        e = o.evaluated_get(dg); me = e.to_mesh(); t += sum(len(p.vertices) - 2 for p in me.polygons); e.to_mesh_clear()
    return t
parts = [o for o in coll('Mine').all_objects if o.get('part') and not o.name.startswith(('Astronaut', 'leg', 'boot', 'knee', 'torso', 'belt', 'pack', 'chest', 'stripe', 'arm', 'glove', 'helmet', 'visor', 'ant', 'tablet', 'forearm'))]
mats = sorted({s.material.name for o in parts if o.type == 'MESH' for s in o.material_slots if s.material})
print('STATS', CON, 'loaded' if LOADED else 'empty', 'objects', len(parts), 'tris_master', tris(parts), 'materials', len(mats), mats, flush=True)
bb = [o.matrix_world @ Vector(c) for o in parts if o.type == 'MESH' for c in o.bound_box]
print('BBOX', [round(min(v[i] for v in bb), 2) for i in range(3)], [round(max(v[i] for v in bb), 2) for i in range(3)], flush=True)

if A.get('glb') == '1':
    # game-look preview GLB (glTF y-up, origin = ship axis on the ground): flat palette colours, metal 0, rough 0.7 (style guide sec. 7),
    # glows emissive; ship NOT included (the three.js proof places the pad's own Ship_Placeholder).
    simple = {}
    for nm, hx in GAME.items():
        g = bpy.data.materials.new('G' + nm[2:]); g.use_nodes = True; bs = g.node_tree.nodes['Principled BSDF']
        bs.inputs['Base Color'].default_value = hexc(hx); bs.inputs['Metallic'].default_value = 0.0; bs.inputs['Roughness'].default_value = 0.7
        if bpy.data.materials[nm].get('glow'): bs.inputs['Emission Color'].default_value = hexc(hx); bs.inputs['Emission Strength'].default_value = 2.5
        simple[nm] = g
    for o in coll('Mine').all_objects:
        if o.get('ship'): o.select_set(False); continue
        for s in o.material_slots:
            if s.material and s.material.name in simple: s.material = simple[s.material.name]
            elif s.material and s.material.name.startswith('M_'):   # astronaut suit parts
                g = bpy.data.materials.new('G_' + s.material.name); g.use_nodes = True; g.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = s.material.diffuse_color
                g.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0.0; s.material = g
    convert_curves()
    for o in list(coll('Mine').all_objects):
        if o.get('ship'): bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in coll('Mine').all_objects: o.select_set(True)
    p = os.path.join(OUT, f'st10{CON.lower()}_{"loaded" if LOADED else "empty"}_preview.glb')
    bpy.ops.export_scene.gltf(filepath=p, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_animations=False,
                              export_cameras=False, export_lights=False)
    print('GLB', p, flush=True)
    sys.exit(0)

if SHOT != 'none':
    ground(); build_road()
    world_and_sun(sun_dir=(-0.55, -0.6, 0.78), energy=5.0)
    cam = setup_render(SAMPLES); sc = bpy.context.scene
    sc.view_settings.exposure = 0.25
    # fill light from the camera side so the shaded faces stay readable (no env map in game either)
    fl = bpy.data.lights.new('Fill', 'AREA'); fl.energy = 60000; fl.size = 60; fl.color = hexc('#c9d3e6')[:3]
    fo = bpy.data.objects.new('Fill', fl); coll('Stage').objects.link(fo); fo.location = (40, -70, 30); fo.rotation_euler = (Vector((0, 0, 8)) - fo.location).to_track_quat('-Z', 'Y').to_euler()
    tgt = (0.5, 0, 16.0 if LOADED else 8.0)
    name = f'st10{CON.lower()}_{"loaded" if LOADED else "empty"}'
    if SHOT == 'hero':
        shoot(cam, os.path.join(OUT, f'{name}_hero_{W}x{H}.png'), tgt, (-58, -78, 30) if LOADED else (-50, -66, 22), W, H, lens=40 if LOADED else 38)
    elif SHOT == 'side':
        shoot(cam, os.path.join(OUT, f'{name}_34_{W}x{H}.png'), tgt, (-52, -72, 26) if LOADED else (-46, -62, 20), W, H, lens=36)
