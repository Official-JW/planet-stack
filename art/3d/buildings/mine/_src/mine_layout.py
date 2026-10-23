"""Mine station layout for the in-game build (approved concept B + HT-04; the Refinery is its own station, one swipe right).
Imported by build_mine.py AFTER concept_b_sleek.py has built the B scene (--arm park; build_mine then deletes the truck's
scoop arm - the HT-04 only fills under the conveyor chute).

Edits vs the concept-B master (Blender coords, Z up, metres):
  * DUMP 01 receiving hopper + lift tube removed - trucks haul to the Refinery station (off the right edge) and dump there.
  * Head-end cantilever pylon + boom (stood in the new haul road) replaced by a column under the trough, north of the road.
  * Haul road re-laid as a GRADED regolith track (4 m running surface, low berms, tyre-mark ruts, RoadCol vertex colour):
    two lanes like the Refinery road strip: OUT (bay -> S-curve -> lane glTF z 9 -> +X off the right edge) and RET (lane glTF z 0
    from x 26 heading -X -> east of the operator deck -> south -> west -> U-turn round Dep_01 -> the bay heading +X).
  * Deposits moved inside the loop (Dep_01 east-centre, Dep_02 south straight); the drill taps them, the chute delivers the ore.
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
# (10/23 PM: the long west loop / south straight / west hairpin are gone - see HAUL below)
# (10/23: the dump stub west to the Refinery intake, Path_Dump / Path_Dump_Approach and REFINERY_ANCHOR are gone - the Refinery is
#  its own station, one swipe right; trucks leave the Mine at Road_Entry along the +X stub)
DEP1 = (8.65, -8.65)
DEP2 = (-1.2, -10.4)
ROAD_W = 4.0                                 # graded running surface (HT-04 is 3.82 m over the tyres)
ROAD_ENTRY = (16.794, -9.0)                  # end of the outbound S-curve: from here the loaded lane runs straight +X off the right edge

# --- haul network (10/23 PM, two lanes to match the Refinery road strip; Blender XY, glTF z = -Blender y):
#   OUT (loaded):  Path_Load (4.7,-4.5) -> +X along the bay -> S-curve (R 4.5, 2 x 60 deg) -> outbound lane y -9 (glTF z 9) -> x 26
#   RET (empty):   x 26 on the return lane y 0 (glTF z 0), heading -X -> left 90 (R 4.5, east of the Operator_Deck) -> south leg x 19.5
#                  (crosses the outbound lane) -> right 90 -> west on y -13.5 -> right U-turn (R 4.5) round Dep_01 -> bay heading +X
#                  -> Path_Load_Approach (9,-4.5) -> reverse 4.3 m to Path_Load.
R_T = 4.5
BAY_X0 = 0.0                                 # west end of the load bay (truck tail at Path_Load ~ x 1.2)
_S_DX = 2 * R_T * math.sin(math.radians(60))  # 7.794: S-curve length along x for a 4.5 m lateral offset
RET_X_LEG = 19.5                             # return south leg (x); berm toe 16.7 stays east of the deck (x <= 15.42)
U_X = 8.65                                   # centre x of the return U-turn (centre (8.65, -9)): directly over Dep_01 x, so the U clears its tap circle like the bay does
def _line(a, b): a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0)); return ('line', a, b, (b - a).length)
def _arcl(c, a0, a1): return ('arc', Vector((c[0], c[1], 0)), (math.radians(a0), math.radians(a1)), abs(math.radians(a1 - a0)) * R_T)
def _pt(leg, t):
    if leg[0] == 'line': return leg[1].lerp(leg[2], t)
    c, (a0, a1) = leg[1], leg[2]; a = a0 + (a1 - a0) * t; return Vector((c.x + R_T * math.cos(a), c.y + R_T * math.sin(a), 0))
OUT_LEGS = [_line((TX, TY), (9.0, TY)), _arcl((9.0, TY - R_T), 90, 30), _arcl((9.0 + _S_DX, TY), 210, 270), _line((9.0 + _S_DX, -9.0), (26.0, -9.0))]
RET_LEGS = [_line((26.0, 0.0), (RET_X_LEG + R_T, 0.0)), _arcl((RET_X_LEG + R_T, -R_T), 90, 180), _line((RET_X_LEG, -R_T), (RET_X_LEG, -9.0)),
            _arcl((RET_X_LEG - R_T, -9.0), 0, -90), _line((RET_X_LEG - R_T, -13.5), (U_X, -13.5)), _arcl((U_X, -9.0), -90, -180),
            _arcl((U_X, -9.0), 180, 90), _line((U_X, TY), (9.0, TY))]
def leg_rows(legs, d_line=1.0, d_arc=0.6):
    P = []
    for lg in legs:
        n = max(1, int(round(lg[3] / (d_line if lg[0] == 'line' else d_arc))))
        P += [_pt(lg, k / n) for k in range(n)]
    P.append(_pt(legs[-1], 1.0)); return P
def out_rows(): return [Vector((x, TY, 0)) for x in _seg(None, BAY_X0, TX, 1.0)] + leg_rows(OUT_LEGS)
def ret_rows(): return leg_rows(RET_LEGS[:-1])          # ends where the U-turn meets the bay (x 8.65); the bay strip carries the last 0.35 m

def ground_fn():
    g = bpy.data.objects['Ground']; me = g.data
    bvh = BVHTree.FromPolygons([g.matrix_world @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    def h(x, y):
        hit = bvh.ray_cast(Vector((x, y, 60)), Vector((0, 0, -1)))
        return hit[0].z if hit[0] is not None else 0.0
    return h

# --- graded regolith haul road (replaces the flat dark decal): cross-section, half-widths from the centre line (m).
# kind -> vertex colour; dz is height over the graded surface (toe is relative to the ground: it is buried so the berm grows out of it)
_HALF = [(0.0, 0.02, 'track'), (1.05, 0.0, 'track'), (1.25, -0.03, 'mark'), (1.65, -0.03, 'mark'), (1.85, 0.0, 'track'), (2.0, 0.0, 'foot'), (2.35, 0.25, 'crest'), (2.8, -0.04, 'toe')]   # worn tyre tracks 0.4 m wide at +-1.45 (HT-04 tyre centres)
PROFILE = [(-o, dz, k) for o, dz, k in reversed(_HALF[1:])] + _HALF
BERM_IN, BERM_OUT = 2.0, 2.8
ROAD_HEX = {'track': '#a4a7ac', 'mark': '#6c6f74', 'foot': '#9da0a5', 'crest': '#939499', 'toe': '#82858a'}
def _lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return Vector([x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c])
def _srgb(h): h = h.lstrip('#'); return Vector([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
ROAD_COL = {k: _srgb(v) for k, v in ROAD_HEX.items()}   # sRGB: bmesh BYTE_COLOR layers store sRGB bytes (attribute .color reads back linear)

def _seg(pts, a, b, step):
    n = max(1, int(round(abs(b - a) / step))); return [a + (b - a) * i / n for i in range(n)]
def _bez(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append(Vector(p0) * u ** 3 + Vector(p1) * 3 * u * u * t + Vector(p2) * 3 * u * t * t + Vector(p3) * t ** 3)
    return out
def _dense(pts, closed, step=0.2):
    out = []; n = len(pts)
    for i in range(n if closed else n - 1):
        a, b = pts[i], pts[(i + 1) % n]; k = max(1, int((b - a).length / step))
        out += [a.lerp(b, j / k) for j in range(k)]
    if not closed: out.append(pts[-1])
    return out
def _sm(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
_smooth = _sm

def graded_roads(height, mat):
    """builds haul_road_loop / haul_road_dump / haul_road_access: graded track + berms + tyre-mark ruts.
    Colour lives in the 'RoadCol' corner colour attribute (linear), read by the render material and copied into the game 'Col'.
    Berms open up where they cross another road (junctions) and where they would bury a station part (column feet, rig feet, deposits)."""
    from mathutils.kdtree import KDTree
    from mathutils import noise
    from mc_common import _obj
    roads = [('haul_road_out', out_rows(), False, 0.065), ('haul_road_return', ret_rows(), False, 0.045)]
    trees = []
    for nm, pts, cl, _ in roads:
        d = _dense(pts, cl); kd = KDTree(len(d))
        for i, q in enumerate(d): kd.insert((q.x, q.y, 0), i)
        kd.balance(); trees.append(kd)
    # obstacles: ground-contact points of station parts (not the truck, the ground, pebbles or roads)
    truck = bpy.data.objects.get('Truck_HT04'); tkids = set(truck.children_recursive) if truck else set()
    obs = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o in tkids: continue
        b = o.name.split('.')[0]
        if b in ('Ground',) or b.startswith(('haul_road', 'pebble', 'boulder', 'slope_boulder')): continue
        mw = o.matrix_world
        for v in o.data.vertices:
            w = mw @ v.co
            if abs(w.x) < 30 and abs(w.y) < 40 and w.z < height(w.x, w.y) + 0.6: obs.append((w.x, w.y))
    for (dx, dy) in (DEP1, DEP2):     # deposit clearance (10/23): berms fully open within 2.5 m of Dep_01 / Dep_02 (the game draws the glow there)
        for rr_ in (0.0, 0.6, 1.2, 1.8, 2.3):
            k_ = max(1, int(math.tau * rr_ / 0.3))
            for j_ in range(k_): obs.append((dx + rr_ * math.cos(math.tau * j_ / k_), dy + rr_ * math.sin(math.tau * j_ / k_)))
    okd = KDTree(max(1, len(obs)))
    for i, (x, y) in enumerate(obs): okd.insert((x, y, 0), i)
    okd.balance()
    made = []
    for ri, (nm, pts, closed, S) in enumerate(roads):
        n = len(pts); bm = bmesh.new(); rows = []
        for i, p in enumerate(pts):
            a = pts[(i - 1) % n] if (closed or i > 0) else p; b_ = pts[(i + 1) % n] if (closed or i < n - 1) else p
            t = (b_ - a); t.z = 0; t.normalize(); nn = Vector((-t.y, t.x, 0)); row = []
            for off, dz, kind in PROFILE:
                q = p + nn * off; g = height(q.x, q.y)
                f = 1.0
                if abs(off) > BERM_IN - 1e-6:
                    for rj, kd in enumerate(trees):          # junction: inside another road's graded surface -> no berm
                        if rj == ri: continue
                        dB = kd.find((q.x, q.y, 0))[2]
                        f = min(f, _sm((dB - (BERM_IN - 0.2)) / 1.0))
                    if obs:
                        dO = okd.find((q.x, q.y, 0))[2]; f = min(f, _sm((dO - 0.2) / 0.6))
                if kind == 'toe': z = g + S * (1 - f) + dz * f
                elif kind == 'crest': z = g + S + dz * f
                else: z = g + S + dz
                c = ROAD_COL['track'].lerp(ROAD_COL[kind], f) if abs(off) > BERM_IN - 1e-6 else ROAD_COL[kind].copy()
                c = c * (1.0 + 0.05 * noise.noise(Vector((q.x * 0.35, q.y * 0.35, 3.1 + ri))))
                row.append((bm.verts.new((q.x, q.y, z)), c))
            rows.append(row)
        cl_ = bm.loops.layers.color.new('RoadCol')
        for i in (range(n) if closed else range(n - 1)):
            r0, r1 = rows[i], rows[(i + 1) % n]
            for k in range(len(PROFILE) - 1):
                quad = (r0[k], r0[k + 1], r1[k + 1], r1[k])
                try: fc = bm.faces.new([v for v, _ in quad])
                except ValueError: continue
                for lp, (_, c) in zip(fc.loops, quad): lp[cl_] = (c.x, c.y, c.z, 1.0)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        if sum(f.normal.z for f in bm.faces) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
        o = _obj(bm, nm, mat, c='Stage', smooth=True, angle=180)
        me = o.data
        if 'RoadCol' in me.color_attributes: me.color_attributes.active_color = me.color_attributes['RoadCol']
        o['road'] = 1; made.append(o)
    # graded = cleared: drop pebbles / boulders lying on the road or its berms
    gone = 0
    for o in list(bpy.data.objects):
        b = o.name.split('.')[0]
        if b in ('pebble', 'boulder', 'slope_boulder'):
            w = o.matrix_world.translation; r = max(o.dimensions) / 2
            if min(kd.find((w.x, w.y, 0))[2] for kd in trees) < BERM_OUT + r: bpy.data.objects.remove(o, do_unlink=True); gone += 1
    # render terrain only: where the (displaced, 0.62 m grid) ground bulges above the road between road vertices, cut it 3 cm under
    # the road surface (a graded road is cut into the regolith). The ground material (shared M_ground) is untouched.
    g = bpy.data.objects['Ground']; gm = g.data; vs_, ps_ = [], []
    for o in made:
        b0 = len(vs_); vs_ += [o.matrix_world @ v.co for v in o.data.vertices]; ps_ += [tuple(b0 + i for i in p.vertices) for p in o.data.polygons]
    rb = BVHTree.FromPolygons(vs_, ps_); cut = 0; gi = g.matrix_world.inverted()
    for v in gm.vertices:
        w = g.matrix_world @ v.co
        if abs(w.x) > 40 or abs(w.y) > 45: continue
        hit = rb.ray_cast(Vector((w.x, w.y, w.z + 5)), Vector((0, 0, -1)))
        if hit[0] is not None and w.z > hit[0].z - 0.03:
            v.co = gi @ Vector((w.x, w.y, hit[0].z - 0.03)); cut += 1
    gm.update()
    print('ROADS', [(o.name, len(o.data.polygons)) for o in made], 'cleared rocks', gone, 'ground verts cut', cut)
    return made

def M_road_graded():
    """compacted regolith: the RoadCol vertex colour (track / tyre marks / berms) x fine gravel noise, rough, opaque."""
    m = bpy.data.materials.new('B_HaulRoadGraded'); m.use_nodes = True; nt = m.node_tree; N = nt.nodes
    b = N['Principled BSDF']; tc = N.new('ShaderNodeTexCoord')
    at = N.new('ShaderNodeAttribute'); at.attribute_type = 'GEOMETRY'; at.attribute_name = 'RoadCol'
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.3; mr.inputs['From Max'].default_value = 0.7
    mr.inputs['To Min'].default_value = 0.9; mr.inputs['To Max'].default_value = 1.06; nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    mul = N.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    nt.links.new(at.outputs['Color'], mul.inputs[6]); nt.links.new(mr.outputs[0], mul.inputs[7]); nt.links.new(mul.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.96; b.inputs['Specular IOR Level'].default_value = 0.3
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.25; bump.inputs['Distance'].default_value = 0.03
    n2 = N.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 9; n2.inputs['Detail'].default_value = 8
    nt.links.new(tc.outputs['Object'], n2.inputs['Vector']); nt.links.new(n2.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = (0.38, 0.39, 0.41, 1)
    return m

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
    height = ground_fn()
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
    # 4b) graded haul road (after the deposits moved, so the berms open around them)
    graded_roads(height, M_road_graded())      # loop + haul road stub (+X from ROAD_ENTRY, off the right edge)
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
