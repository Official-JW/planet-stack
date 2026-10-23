"""Mine station layout for the in-game build (approved concept B + HT-04, Refinery now part of the station).
Imported by build_mine.py AFTER concept_b_sleek.py has built the B scene (run with --arm park so the arm is stowed forward
over the cab, clear of the tipping bed).

Edits vs the concept-B master (Blender coords, Z up, metres):
  * DUMP 01 receiving hopper + lift tube removed - trucks now dump into the Refinery intake bin (REFINERY_ANCHOR, west of the rig).
  * Head-end cantilever pylon + boom (stood in the new haul road) replaced by a column under the trough, north of the road.
  * Haul road re-laid: loop  load bay (x 4.7) -> east hairpin -> south straight -> west hairpin -> north line back to the bay,
    plus a dump stub running west past the rig to the Refinery intake.
  * Deposits moved inside the loop so the truck scoops them from the road (Dep_01 east-centre, Dep_02 south straight).
  * Astronaut removed (no astronauts in game assets)."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

# --- constants mirrored from concept_b_sleek.py
TX, TY = 4.7, -4.5                  # truck centre at the load bay (heading +X)
RX, RY = -7.5, 3.0; RYc = RY + 0.6  # bore rig
H_X, H_Y = -1.0, 3.0                # pod hopper
BIN_X, BIN_Y = 10.0, 4.5            # ore silo
SH_T = Vector((0.75, -0.92, 3.3))   # arm shoulder (truck-local)
L1, L2 = 1.3, 1.7
BX0, BX1, BW, BZ, BTOP = -3.5, 0.3, 1.4, 1.93, 3.3
HINGE_T = Vector((BX0 + 0.2, 0, 1.72))
RAM_Y, RAM_STAGE = 0.86, 1.0
AXLES = (-2.7, -1.35, 2.4); WR = 0.85
STOW_WRIST_T = Vector((2.15, -1.05, 4.35))   # 'park' pose = game stow (forward over the cab corner)
REACH_WRIST_T = Vector((0.2, -2.8, 1.45))    # scoop reach: 2.8 m to the truck right (-Y local), 1.45 m up (elbow stays raised)

def conveyor():
    BED_C = Vector((TX - 1.6, TY, 0))
    C0 = Vector((H_X + 0.15, H_Y - 0.35, 2.55)); DIS = Vector((BED_C.x, BED_C.y, 0)); C1 = Vector((DIS.x, DIS.y, 5.55))
    for _ in range(4):
        uh = Vector((C1.x - C0.x, C1.y - C0.y, 0)).normalized(); C1 = Vector((DIS.x - uh.x * 0.75, DIS.y - uh.y * 0.75, 5.55))
    d = C1 - C0; L = d.length; u = d.normalized(); side = Vector((0, 0, 1)).cross(u).normalized(); up = u.cross(side).normalized()
    return C0, C1, L, u, side, up, DIS

# --- station layout (world, Blender XY)
LOAD = (TX, TY, 0.0)                         # truck centre + yaw(deg) at the conveyor head
DUMP_APPROACH = (-5.0, -5.5, 0.0)            # stop here heading +X, then reverse 4 m west
DUMP = (-9.0, -5.5, 0.0)                     # truck centre when tipping (rear faces west, into the intake)
REFINERY = (-13.84, -5.5, 90.0)              # intake-bin centre on the ground; yaw 90 -> anchor local glTF +Z = truck heading (+X)
DEP1 = (8.65, -8.65); DEP1_PARK = (8.5, -4.5, 0.0)
DEP2 = (-1.2, -10.4); DEP2_PARK = (-1.0, -13.5, 180.0)
ROAD_W = 3.2

def _smooth(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
def north_y(x): return -5.5 + 1.0 * _smooth((x + 4.0) / 4.0)   # S-blend: y -5.5 west of x=-4, -4.5 east of x=0

def loop_points(step=0.5):
    """closed haul loop in driving order, starting at the west end of the north line (dump approach)."""
    P = []
    n = int(14 / step)
    for i in range(n): x = -5 + 14 * i / n; P.append(Vector((x, north_y(x), 0)))
    n = int(math.pi * 4.5 / step)
    for i in range(n): a = math.pi / 2 - math.pi * i / n; P.append(Vector((9 + 4.5 * math.cos(a), -9 + 4.5 * math.sin(a), 0)))
    n = int(14 / step)
    for i in range(n): P.append(Vector((9 - 14 * i / n, -13.5, 0)))
    n = int(math.pi * 4 / step)
    for i in range(n): a = 1.5 * math.pi - math.pi * i / n; P.append(Vector((-5 + 4 * math.cos(a), -9.5 + 4 * math.sin(a), 0)))
    return P

def ground_fn():
    g = bpy.data.objects['Ground']; me = g.data
    bvh = BVHTree.FromPolygons([g.matrix_world @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    def h(x, y):
        hit = bvh.ray_cast(Vector((x, y, 60)), Vector((0, 0, -1)))
        return hit[0].z if hit[0] is not None else 0.0
    return h

def _road(name, pts, w, closed, height, mat, cols=5):
    from mc_common import _obj
    n = len(pts); bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); rows = []; s_acc = 0.0
    for i, p in enumerate(pts):
        a = pts[(i - 1) % n] if (closed or i > 0) else p; b_ = pts[(i + 1) % n] if (closed or i < n - 1) else p
        t = (b_ - a); t.z = 0; t.normalize(); nn = Vector((-t.y, t.x, 0))
        if i: s_acc += (p - pts[i - 1]).length
        row = []
        for k in range(cols):
            q = p + nn * w * (k / (cols - 1) - 0.5); row.append((bm.verts.new((q.x, q.y, height(q.x, q.y) + 0.035)), k / (cols - 1), s_acc / w))
        rows.append(row)
    for i in (range(n) if closed else range(n - 1)):
        r0, r1 = rows[i], rows[(i + 1) % n]
        for k in range(cols - 1):
            f = bm.faces.new((r0[k][0], r0[k + 1][0], r1[k + 1][0], r1[k][0]))
            for lp, (vv, vk, vs) in zip(f.loops, (r0[k], r0[k + 1], r1[k + 1], r1[k])): lp[uvl].uv = (vs, vk)
    return _obj(bm, name, mat, c='Stage', smooth=True, angle=180)

def _del(pred):
    n = 0
    for o in list(bpy.data.objects):
        if pred(o):
            bpy.data.objects.remove(o, do_unlink=True); n += 1
    return n

def apply():
    from mc_common import rod
    from mc_common import beam, box, _obj
    import bmesh as _bm
    M = bpy.data.materials
    WHITE, WHITE_S, GRAPH, GRAPH_S, CYAN = M['B_White'], M['B_WhiteSmooth'], M['B_Graphite'], M['B_GraphiteSmooth'], M['B_Cyan']
    base = lambda o: o.name.split('.')[0]
    # 1) astronaut(s)
    astro = [o for o in bpy.data.objects if o.name.startswith('Astronaut')]
    for a in astro:
        for c in list(a.children_recursive): bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.objects.remove(a, do_unlink=True)
    # 2) DUMP 01 + lift tube, old head pylon/boom, old roads + spur marker
    gone = _del(lambda o: base(o).startswith(('dump_', 'lift_', 'decal_dump', 'head_pylon', 'head_boom', 'head_hanger', 'haul_road', 'Path_Spur')))
    print('LAYOUT removed', gone, 'objects')
    # 3) head-end support column under the trough, north of the road
    C0, C1, L, u, side, up, DIS = conveyor()
    f = 0.62; P = C0 + u * (L * f) - up * 0.2
    lathe_ = _lathe
    rod('head_col', (P.x, P.y, 0.0), (P.x, P.y, P.z - 0.15), 0.28, GRAPH_S, r2=0.2, segs=24)
    lathe_('head_col_foot', [(0, 0), (0.8, 0), (0.66, 0.17), (0, 0.21)], (P.x, P.y, 0), WHITE_S, segs=32)
    _ring('head_col_glow', 0.27, (P.x, P.y, 0.95), 0.06, CYAN, w=0.03, segs=32)
    beam('head_col_saddle', P - side * 0.75 - up * 0.08, P + side * 0.75 - up * 0.08, 0.32, 0.22, GRAPH_S, bevel=0.05)
    K = C0 + u * (L * 0.9) - up * 0.25                       # knee brace column -> head end underside
    beam('head_col_brace', Vector((P.x, P.y, P.z - 1.3)), K, 0.22, 0.26, WHITE, bevel=0.06)
    # 4) haul road loop + dump stub
    height = ground_fn(); ROADM = M['B_HaulRoad']
    _road('haul_road_loop', loop_points(0.5), ROAD_W, True, height, ROADM)
    stub = [Vector((x, -5.5, 0)) for x in [(-4.0 - 0.5 * i) for i in range(18)]]   # x -4 .. -12.5 (ends at the intake front)
    _road('haul_road_dump', stub, ROAD_W, False, height, ROADM)
    # 5) deposits inside the loop
    OLD1, OLD2 = Vector((11.2, -8.8, 0)), Vector((4.7 + 3.0, -4.5 - 3.6, 0))
    X1 = Matrix.Translation((DEP1[0], DEP1[1], 0)) @ Matrix.Diagonal((0.85, 0.85, 1.0, 1)) @ Matrix.Translation(-OLD1)
    X2 = Matrix.Translation((DEP2[0], DEP2[1], 0)) @ Matrix.Diagonal((1.0, 1.0, 1.3, 1)) @ Matrix.Translation(-OLD2)
    for o in list(bpy.data.objects):
        b = base(o)
        if b in ('deposit',) or (b.startswith('seam_crystal') and not b.startswith('seam_crystal_s')) or (b.startswith('spill') and not b.startswith('spill_s')):
            if o.parent is None: o.matrix_world = X1 @ o.matrix_world
        elif b in ('deposit_small',) or b.startswith(('seam_crystal_s', 'spill_s')):
            if o.parent is None: o.matrix_world = X2 @ o.matrix_world
    for nm, (x, y) in (('Dep_01', DEP1), ('Dep_02', DEP2)):
        e = bpy.data.objects.get(nm)
        if e: e.location = (x, y, height(x, y))
    bpy.context.view_layer.update()
    return dict(C0=C0, C1=C1, L=L, u=u, side=side, up=up, DIS=DIS, height=height, col=P)

# local copies of concept-B lathe/ring (they live in the concept script, not mc_common)
def _lathe(name, prof, loc, mat, segs=48, bevel=0.0, smooth=True):
    from mc_common import _obj
    TAU = math.tau; bm = bmesh.new(); rings = []
    for (r, z) in prof:
        if r < 1e-5: rings.append([bm.verts.new((loc[0], loc[1], loc[2] + z))])
        else: rings.append([bm.verts.new((loc[0] + r * math.cos(TAU * k / segs), loc[1] + r * math.sin(TAU * k / segs), loc[2] + z)) for k in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for k in range(segs):
            k2 = (k + 1) % segs
            if len(a) == 1: bm.faces.new((a[0], b[k], b[k2]))
            elif len(b) == 1: bm.faces.new((a[k], a[k2], b[0]))
            else: bm.faces.new((a[k], a[k2], b[k2], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(bm, name, mat, smooth=smooth, bevel=bevel, angle=50)

def _ring(name, r, loc, h, mat, w=0.06, segs=64):
    x, y, z = loc
    return _lathe(name, [(r - w, z - h / 2), (r, z - h / 2), (r, z + h / 2), (r - w, z + h / 2), (r - w, z - h / 2)], (x, y, 0), mat, segs=segs)
