"""Mine station - in-game build (phone renders + tiered game GLB) from approved concept B + HT-04.
usage (scene is rebuilt from the concept script first, arm stowed forward = 'park'):
  B=/opt/blender-4.2.3-linux-x64/blender; C=art/3d/mine_concepts/_src/concept_b_sleek.py; S=art/3d/buildings/mine/_src/build_mine.py
  $B -b -P $C -P $S -- --arm park --only none --out /tmp/mine/gen --mode phone --mout art/3d/buildings/mine [--ps 64]
  $B -b -P $C -P $S -- --arm park --only none --out /tmp/mine/gen --mode game  --mout /tmp/mine/raw.glb [--target 23500]
then pack_mine.sh (prune clip channels -> gltfpack -cc -kn -ke -> inspect)."""
import bpy, bmesh, json, os, sys, math
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', '..', 'mine_concepts', '_src')))
from mc_common import argv, box, rod, beam, sphere, frame_from, _obj
import mine_layout as ML
A = argv(); MODE = A.get('mode', 'game'); MOUT = A.get('mout', '/tmp/mine/raw.glb')
sc = bpy.context.scene; sc.frame_set(1)
LAY = ML.apply()
# Deposit clearance (10/23, Game Coder QA3D: the static heap read as a crater over the in-game Dep_01 glow). The game draws each
# deposit itself (glow disc + gem at Dep_01 / Dep_02, respawning), so the concept's static rock heaps and their seam crystals are
# removed from the station: nothing stands within 2.5 m of either marker. Done AFTER ML.apply(), so the road berms stay opened
# where the heaps stood (graded_roads flattens berms near station parts) and every marker, path and the camera fit are unchanged.
_DEP_ART = ('deposit', 'deposit_small', 'seam_crystal', 'seam_crystal_s', 'spill', 'spill_s')
def _wc(o): return o.matrix_world @ (sum((Vector(c) for c in o.bound_box), Vector()) / 8)
def _dd(o): return min(math.hypot(_wc(o).x - x, _wc(o).y - y) for (x, y) in (ML.DEP1, ML.DEP2))
_gone = [o.name for o in bpy.data.objects if o.type == 'MESH' and _dd(o) < 6.0 and (o.name.split('.')[0] in _DEP_ART
         or o.name.startswith('spill_'))]                     # spill_rock / spill_he3 / spill_pt / spill_s_* chips
_gone += [o.name for o in bpy.data.objects if o.type == 'MESH' and o.name.split('.')[0] == 'pebble' and _dd(o) < 2.8]
for _n in _gone: bpy.data.objects.remove(bpy.data.objects[_n], do_unlink=True)
print('DEPOSIT CLEAR removed', len(_gone), 'objects')
# 10/23 19:57 (Jacob via Director): no floating diamonds / crystals anywhere on the Mine - only the game's ground glow at Dep_01/02.
_he = [o for o in bpy.data.objects if o.type == 'MESH' and any(m and m.name.startswith('B_He3') for m in o.data.materials)]
_cr = [o.name for o in _he if o.name.split('.')[0].startswith(('seam_crystal', 'crystal', 'gem', 'shard', 'deposit', 'spill'))]
for _n in _cr: bpy.data.objects.remove(bpy.data.objects[_n], do_unlink=True)
print('CRYSTALS removed', len(_cr), '| remaining He-3 parts:', sorted({o.name.split('.')[0] for o in bpy.data.objects if o.type == 'MESH' and any(m and m.name.startswith('B_He3') for m in o.data.materials)}))
# 10/23 20:34 (Jacob via Director): still blinking highlights where the diamonds were. The GLB carries nothing glowing or animated at the
# deposits (no gem, glint, flare, emissive clip). The deposit ground patches are now plain ore-coloured rock in Base_Paint: 'dep_patch'
# meshes, material B_DepRock -> SH_Rock (no emission, no vein shader, no clip). Dep_01 / Dep_02 markers and their tap radii are unchanged.
import bmesh as _bmd, random as _rd
_mdr = bpy.data.materials.new('B_DepRock'); _mdr.use_nodes = True; _bsd = _mdr.node_tree.nodes['Principled BSDF']
_bsd.inputs['Base Color'].default_value = (0.050, 0.047, 0.044, 1.0); _bsd.inputs['Roughness'].default_value = 0.95
_bsd.inputs['Emission Strength'].default_value = 0.0; _mdr.diffuse_color = (0.090, 0.092, 0.096, 1.0)
_rr = _rd.Random(7)
_mdv = bpy.data.materials.new('B_DepVein'); _mdv.use_nodes = True; _bsv = _mdv.node_tree.nodes['Principled BSDF']
_bsv.inputs['Base Color'].default_value = (0.03, 0.30, 0.38, 1.0); _bsv.inputs['Emission Color'].default_value = (0.006, 0.14, 0.19, 1.0)
_bsv.inputs['Emission Strength'].default_value = 1.0; _mdv.diffuse_color = (0.03, 0.30, 0.38, 1.0)
for _k, ((_x, _y), _r) in enumerate(((ML.DEP1, 2.2), (ML.DEP2, 1.05))):
    _bm = _bmd.new(); _n = 16; _z0 = LAY['height'](_x, _y)
    _c = _bm.verts.new((_x, _y, _z0 + 0.035)); _ring = []; _base = []
    for _i in range(_n):
        _a = math.tau * _i / _n; _rad = _r * _rr.uniform(0.88, 1.08)
        _px, _py = _x + _rad * math.cos(_a), _y + _rad * math.sin(_a)
        _ring.append(_bm.verts.new((_px, _py, LAY['height'](_px, _py) + 0.03)))
        _base.append(_bm.verts.new((_x + (_rad + 0.12) * math.cos(_a), _y + (_rad + 0.12) * math.sin(_a), LAY['height'](_px, _py) - 0.04)))
    for _i in range(_n):
        _j = (_i + 1) % _n
        _bm.faces.new((_c, _ring[_i], _ring[_j])); _bm.faces.new((_ring[_i], _base[_i], _base[_j], _ring[_j]))
    for _f in _bm.faces:
        _f.normal_update()
        if _f.normal.z < 0: _f.normal_flip()
    _po = _obj(_bm, 'dep_patch', _mdr, c='Mine', smooth=False); _po['road'] = 1; _po['grp'] = 'Base'   # road flag: never decimated
    # 20:50 Director: faint cyan veins, low steady emissive (own material SHM_DepVein, no clip, no pulse), no ring / disc
    for _v in range(5 if _r > 1.5 else 3):
        _bv = _bmd.new(); _a0 = _rr.uniform(0, math.tau); _L = _r * _rr.uniform(1.0, 1.5); _n = 7
        _sx, _sy = _x + _r * 0.55 * math.cos(_a0) * _rr.uniform(-1, 1), _y + _r * 0.55 * math.sin(_a0) * _rr.uniform(-1, 1)
        _hd = _rr.uniform(0, math.tau); _pts = []
        for _i in range(_n + 1):
            _pts.append((_sx, _sy)); _hd += _rr.uniform(-0.5, 0.5); _sx += math.cos(_hd) * _L / _n; _sy += math.sin(_hd) * _L / _n
        _pts = [(px_, py_) for px_, py_ in _pts if math.hypot(px_ - _x, py_ - _y) < _r * 0.85]
        if len(_pts) < 3: continue
        _row = []
        for _i, (px_, py_) in enumerate(_pts):
            qa = _pts[max(0, _i - 1)]; qb = _pts[min(len(_pts) - 1, _i + 1)]; tx_, ty_ = qb[0] - qa[0], qb[1] - qa[1]; tl = math.hypot(tx_, ty_) or 1.0
            wv = 0.05 * (1.0 - abs(2 * _i / (len(_pts) - 1) - 1)) + 0.012
            zz = LAY['height'](px_, py_) + 0.05
            _row.append((_bv.verts.new((px_ - ty_ / tl * wv, py_ + tx_ / tl * wv, zz)), _bv.verts.new((px_ + ty_ / tl * wv, py_ - tx_ / tl * wv, zz))))
        for (a1, b1), (a2, b2) in zip(_row, _row[1:]): _bv.faces.new((a1, b1, b2, a2))
        for _f in _bv.faces:
            _f.normal_update()
            if _f.normal.z < 0: _f.normal_flip()
        _vo = _obj(_bv, 'dep_vein', _mdv, c='Mine', smooth=False); _vo['road'] = 1; _vo['grp'] = 'Base'
print('DEP PATCHES darker ore rock (B_DepRock #3f3d3b) + faint steady cyan veins (B_DepVein -> SHM_DepVein, no clip) at', ML.DEP1, ML.DEP2)
C0, C1, Lc, U, SIDE, UP = LAY['C0'], LAY['C1'], LAY['L'], LAY['u'], LAY['side'], LAY['up']
base = lambda o: o.name.split('.')[0]
TROOT = bpy.data.objects['Truck_HT04']; GZ = TROOT.matrix_world.translation.z
TORG = Vector((ML.TX, ML.TY, GZ))          # truck-local origin in world
# No scoop arm (Director 10/23, from Jacob): the HT-04 only fills under the conveyor chute at Path_Load, then drives off.
# The loading arm (pedestal, turret, shoulder, upper/fore arm, rams, hoses, scoop + its ore) is deleted from the truck before
# anything else reads the scene, so it is gone from the renders, the game mesh, the skin and the camera fit.
def _under(o, r):
    p = o.parent
    while p is not None:
        if p == r: return True
        p = p.parent
    return False
_arm = [o.name for o in bpy.data.objects if _under(o, TROOT) and o.name.split('.')[0].startswith(('arm_', 'scoop'))]
for _n in _arm: bpy.data.objects.remove(bpy.data.objects[_n], do_unlink=True)
print('ARM removed', len(_arm), 'objects')
# Fill + pour parts (Director 10/23, 3rd pass). Fill is code-driven by percent: ONE pile mesh (bed_heap, bone Truck_Load) carrying a
# morph target 'fill' on Truck_Mesh - cheaper than 7 stage meshes (0 extra draws). Official code remap (Director):
#   influence = 0.5 + 0.5 * (fill_pct / 100) ** 0.8   for fill_pct > 0;   influence = 0 for fill_pct == 0 (empty, after a dump)
# so the shapes are designed around it: Basis (0) = 2*MID - FULL, hidden below the bed rim from the station camera (empty look);
# influence 0.5 = MID, a real crowning heap ~0.18 m over the rim top; influence 1 = FULL, a conical heap 0.85 m over the rim top.
# Ore chunks are tiny specks buried in the bed floor at rest (invisible), skinned to their own bones, scaled up only while moving:
#  * Truck_Pour_01..07: rock / He-3 chunks of the looping chute_pour stream (chute mouth -> pile), Truck_Dust_01..04: landing puffs
#  * Truck_Rich_01..05: glowing cyan chunks of the 1 s truck_load_rich drop
_HEAP = next(o for o in bpy.data.objects if o.name.split('.')[0] == 'bed_heap')
_hb = [_HEAP.matrix_world @ Vector(c) for c in _HEAP.bound_box]
HEAP_C = Vector(((min(v.x for v in _hb) + max(v.x for v in _hb)) / 2, (min(v.y for v in _hb) + max(v.y for v in _hb)) / 2, min(v.z for v in _hb)))
HEAP_H = max(v.z for v in _hb) - HEAP_C.z
_dc = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.split('.')[0] == 'dis_chute']
CHUTE_Z = min((o.matrix_world @ Vector(c)).z for o in _dc for c in o.bound_box) if _dc else 4.35
# pile shapes (truck-local metres; heightfield over the bed interior, apex under the chute)
PILE_CX, PILE_AX, PILE_AY = HEAP_C.x - TORG.x, (ML.BX1 - ML.BX0) / 2 - 0.12, ML.BW - 0.16     # half extents 1.78 x 1.24 (bed interior)
RIM_TOP = ML.BTOP + 0.08                                  # top of the bed rim rail
FULL_APEX, FULL_EDGE = RIM_TOP + 0.85, ML.BTOP           # 100 %: conical heap 0.85 m over the rim top, flush with the rim at the walls
BASIS_APEX = 2.87                                         # station camera sight line over the near rim reaches 2.88 m at the bed centre
MID_APEX, MID_EDGE, MID_Q = (BASIS_APEX + FULL_APEX) / 2, 2.62, 1.2
PILE_SKIRT_Z = 1.95                                       # skirt ring tucked into the bed floor (closes the heightfield at the open tail)
def pile_r(x, y):
    u, v = abs(x - PILE_CX) / PILE_AX, abs(y) / PILE_AY
    return min(1.0, (u ** 2.2 + v ** 2.2) ** (1 / 2.2))
def pile_full(r): return FULL_EDGE + (FULL_APEX - FULL_EDGE) * (1 - r)
def pile_mid(r): return MID_EDGE + (MID_APEX - MID_EDGE) * (1 - r) ** MID_Q
def pile_basis(r): return 2 * pile_mid(r) - pile_full(r)
if MODE != 'phone':                                       # game build: replace the concept's static heap with the morphable heightfield
    import random as _rnd
    _rr = _rnd.Random(21); NXg, NYg = 17, 13
    bm_ = bmesh.new(); _g = {}
    _inv = _HEAP.matrix_world.inverted()
    for ix in range(NXg):
        for iy in range(NYg):
            x = PILE_CX - PILE_AX + 2 * PILE_AX * ix / (NXg - 1); y = -PILE_AY + 2 * PILE_AY * iy / (NYg - 1)
            r_ = pile_r(x, y); n_ = 0.035 * min(1.0, r_ / 0.25) * (_rr.random() * 2 - 1)
            _g[ix, iy] = bm_.verts.new(_inv @ (TORG + Vector((x, y, pile_basis(r_) + n_))))
    _ring = [(ix, 0) for ix in range(NXg)] + [(NXg - 1, iy) for iy in range(1, NYg)] + [(ix, NYg - 1) for ix in range(NXg - 2, -1, -1)] + [(0, iy) for iy in range(NYg - 2, 0, -1)]
    _sk = {k: bm_.verts.new(_inv @ (TORG + Vector(((_inv.inverted() @ _g[k].co) - TORG).xy[:] + (PILE_SKIRT_Z,)))) for k in _ring}
    for ix in range(NXg - 1):
        for iy in range(NYg - 1): bm_.faces.new((_g[ix, iy], _g[ix + 1, iy], _g[ix + 1, iy + 1], _g[ix, iy + 1]))
    for a_, b_ in zip(_ring, _ring[1:] + _ring[:1]):
        try: bm_.faces.new((_g[a_], _g[b_], _sk[b_], _sk[a_]))
        except ValueError: pass
    bmesh.ops.recalc_face_normals(bm_, faces=bm_.faces)
    _me = bpy.data.meshes.new('bed_heap_fill'); bm_.to_mesh(_me); bm_.free()
    for p_ in _me.polygons: p_.use_smooth = False
    _me.materials.append(_HEAP.data.materials[0] if _HEAP.data.materials else None); _HEAP.data = _me
ORE_SPECK = 0.02
POUR_N, RICH_N, DUST_N = 7, 5, 4
CHUNKS = [('Truck_Pour_%02d' % (k + 1), 'B_OreRock' if k % 2 == 0 else 'B_He3', r) for k, r in enumerate((0.34, 0.29, 0.36, 0.3, 0.33, 0.28, 0.35))]
CHUNKS += [('Truck_Rich_%02d' % (k + 1), 'B_He3', r) for k, r in enumerate((0.34, 0.3, 0.32, 0.29, 0.31))]
CHUNKS += [('Truck_Dust_%02d' % (k + 1), 'B_OreRock', r) for k, r in enumerate((0.3, 0.27, 0.32, 0.28))]
CH_REST = {}
for k, (bn, mn, _) in enumerate(CHUNKS):
    a_ = 2.39996 * k; rr_ = 0.12 + 0.03 * (k % 5)
    CH_REST[bn] = Vector((HEAP_C.x - TORG.x + rr_ * math.cos(a_), HEAP_C.y - TORG.y + rr_ * math.sin(a_), HEAP_C.z - TORG.z - 0.03))
    _sc = (1.25, 1.25, 0.6) if 'Dust' in bn else (1.2, 1.0, 0.85)
    ch_ = sphere('load_chunk', ORE_SPECK, tuple(TORG + CH_REST[bn]), bpy.data.materials[mn], scale=_sc, sub=1, smooth=False, jitter=0.0 if 'Dust' in bn else 0.25, seed=k)
    ch_.parent = TROOT; ch_.matrix_parent_inverse = TROOT.matrix_world.inverted(); ch_['keep_truck'] = 1; ch_['chunk_bone'] = bn; ch_.hide_render = True
print('LOAD parts: heap base', tuple(round(v, 3) for v in HEAP_C), 'h', round(HEAP_H, 3), 'chute mouth z', round(CHUTE_Z, 3))

# ---------------------------------------------------------------- camera (Game Coder spec, QA3D main.js)
# d = (frame_w / 2) / (tan(19 deg) * aspect), aimed at Cam_Target, 38 deg vertical FOV, 18 deg down, same formula at every aspect.
# 10/23 night (Coder's exact tier safe area): every tier vertex must land in y 144-568 on 393x852 AND y 144-383 on 375x667, with
# 0 px side margin. Solved AFTER the tiers are built, numerically (numpy pinhole = three.js PerspectiveCamera), smallest frame_w that fits.
FOV_Y, PITCH, PW, PH = 38.0, 18.0, 393, 852
TAN_H = math.tan(math.radians(FOV_Y / 2)) * PW / PH
SIZES = {(393, 852): (165, 534), (375, 667): (144, 383)}   # 10/23 20:58 Coder: iPhone insets -> 393x852 band y 165-534 for EVERYTHING (tiers + station + deposits + truck)
def cam_pose(tgt, W, pw=PW, ph=PH):
    d = (W / 2) / (math.tan(math.radians(FOV_Y / 2)) * pw / ph); p = math.radians(PITCH)
    pos = Vector(tgt) + Vector((0, -d * math.cos(p), d * math.sin(p)))
    return pos, d
import numpy as np
def proj_np(P, tgt, W, pw, ph):
    pos, d = cam_pose(tgt, W, pw, ph); pos = np.array(pos); t = np.array(tgt)
    f = t - pos; f /= np.linalg.norm(f); r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r); u = np.cross(r, f)
    v = P - pos; xc, yc, zc = v @ r, v @ u, v @ f; th = math.tan(math.radians(FOV_Y / 2)); asp = pw / ph
    return (xc / (zc * th * asp) + 1) / 2 * pw, (1 - yc / (zc * th)) / 2 * ph
def obj_pts(objs):
    return np.array([tuple(o.matrix_world @ v.co) for o in objs if o.type == 'MESH' for v in o.data.vertices])
def cam_fit(TP, FP, ZT=6.0, margin=3.0):
    """TP: tier vertices (Blender world), FP: base-station focus points. Returns (W, target, d, box)."""
    best = None
    for W in ([float(A['w'])] if 'w' in A else [22 + 0.2 * i for i in range(120)]):
        tgt = np.array([0.0, 0.0, ZT])
        for it in range(6):
            xs, _ = proj_np(np.vstack([TP, FP]), tgt, W, PW, PH)
            tgt[0] += ((xs.min() + xs.max()) / 2 - PW / 2) / PW * W
            lo, hi = -40.0, 40.0                    # feasible target y interval (screen y grows with target y for points in front)
            def ok_lo(ty):                          # tops: y >= band top on both sizes
                tg = tgt.copy(); tg[1] = ty
                return all(proj_np(np.vstack([TP, FP]), tg, W, pw, ph)[1].min() >= b0 + margin for (pw, ph), (b0, b1) in SIZES.items())
            def ok_hi(ty):
                tg = tgt.copy(); tg[1] = ty
                return all(proj_np(np.vstack([TP, FP]), tg, W, pw, ph)[1].max() <= b1 - margin for (pw, ph), (b0, b1) in SIZES.items())
            a_, b_ = -40.0, 40.0
            for _ in range(40):
                m = (a_ + b_) / 2; a_, b_ = (a_, m) if ok_lo(m) else (m, b_)
            ylo = b_
            a_, b_ = -40.0, 40.0
            for _ in range(40):
                m = (a_ + b_) / 2; a_, b_ = (m, b_) if ok_hi(m) else (a_, m)
            yhi = a_
            tgt[1] = (ylo + yhi) / 2
        xs, ys = proj_np(np.vstack([TP, FP]), tgt, W, PW, PH)
        fx = proj_np(TP, tgt, W, PW, PH)[0]; fx2 = proj_np(np.vstack([TP, FP]), tgt, W, 375, 667)[0]
        ok = ylo <= yhi and xs.min() >= 0 and xs.max() <= PW and fx2.min() >= 0 and fx2.max() <= 375
        print('FIT W %.1f tgt %s ylo %.2f yhi %.2f x %d..%d %s' % (W, np.round(tgt, 2), ylo, yhi, xs.min(), xs.max(), ok))
        if ok: best = (W, Vector(tuple(tgt)), cam_pose(Vector(tuple(tgt)), W)[1], (xs.min(), xs.max(), ys.min(), ys.max())); break
    return best

# ================================================================= GAME GLB
TARGET = int(A.get('target', 24600))
def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]
J = json.load(open(os.path.join(HERE, '..', '..', '_shared', 'shared_materials.json')))
SW, MERGED, S2M = J['materials'], J['merged_materials'], dict(J['swatch_to_merged'])
S2M['SH_Steel'] = S2M['SH_Foil'] = 'SHM_Paint'          # draw budget: metals ride in Paint as a steel vertex colour
SH = {}
for n, d in MERGED.items():
    if n == 'SHM_Metal': continue
    m = bpy.data.materials.new(n); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(d['base']); b.inputs['Metallic'].default_value = d['metal']; b.inputs['Roughness'].default_value = d['rough']
    if d.get('vertex_colors'):
        ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'; nt.links.new(ca.outputs['Color'], b.inputs['Base Color'])
    if 'emissive' in d:
        b.inputs['Emission Color'].default_value = lin(d['emissive']); b.inputs['Emission Strength'].default_value = d['emissive_strength']
    m.use_backface_culling = True; SH[n] = m
_m = bpy.data.materials.new('SHM_DepVein'); _m.use_nodes = True; _b = _m.node_tree.nodes['Principled BSDF']   # deposit veins: low STEADY emissive (no clip)
_b.inputs['Base Color'].default_value = lin('#1f7f91'); _b.inputs['Metallic'].default_value = 0.0; _b.inputs['Roughness'].default_value = 0.6
_b.inputs['Emission Color'].default_value = [c * 0.18 for c in lin('#2fe3ff')[:3]] + [1.0]; _b.inputs['Emission Strength'].default_value = 1.0
_m.use_backface_culling = True; SH['SHM_DepVein'] = _m
MAP = [('B_WhiteSmooth', 'SH_White'), ('B_White', 'SH_White'), ('B_GraphiteSmooth', 'SH_Graphite'), ('B_Graphite', 'SH_Graphite'),
       ('B_Satin', 'SH_Steel'), ('B_Platinum', 'SH_Steel'), ('B_Tire', 'SH_Graphite'), ('B_Belt', 'SH_Graphite'), ('B_InkWhite', 'SH_White'),
       ('B_Ink', 'SH_Graphite'), ('B_CyanSoft', 'SH_GlowCyan'), ('B_Cyan', 'SH_GlowCyan'), ('B_He3', 'SH_GlowCyan'), ('B_Lamp', 'SH_GlowWhite'),
       ('B_PlasmaCore', 'SH_GlowWhite'), ('B_Melt', 'SH_GlowWhite'), ('B_Visor', 'SH_Glass'), ('B_OreRock', 'SH_Rock'), ('B_DepRock', 'SH_Rock'), ('B_HaulRoad', 'SH_Graphite'),
       ('B_Radiator', 'SH_Radiator'), ('M_Regolith', 'SH_Rock')]
TIRE_COL = lin('#24272b')
def shared_for(m):
    sw = None
    if m is not None:
        for p, s_ in MAP:
            if m.name.startswith(p): sw = s_; break
    if m is not None and m.name.startswith('B_DepVein'): return SH['SHM_DepVein'], [1.0, 1.0, 1.0, 1.0]
    if m is not None and m.name.startswith('B_DepRock'): return SH['SHM_Paint'], lin('#3f3d3b')   # darker ore rock than SH_Rock
    if sw is None: sw = 'SH_Graphite'; print('UNMAPPED', m.name if m else None)
    mm = S2M[sw]
    col = lin(SW[sw]['base']) if MERGED[mm].get('vertex_colors') else lin(MERGED[mm]['base'])
    if m is not None and m.name.startswith('B_Tire'): col = TIRE_COL
    return SH[mm], col

# ---------------- groups
RIG = {'carriage', 'carriage_strip', 'bore_housing', 'bore_glow', 'bore_band', 'bore_window', 'bore_window_frame', 'nozzle', 'nozzle_glow', 'plasma_core'}
SILO = {'silo', 'silo_plinth', 'silo_band', 'silo_glow', 'silo_hatch', 'spine', 'fill_window_bg', 'fill_level', 'silo_beacon'}
DROP = ('decal', 'lug', 'ejecta', 'fall_ore', 'belt_ore', 'umbilical', 'arm_hose', 'cab_whip', 'plasma_halo', 'fill_tick', 'step', 'power_cable',
        'bed_ore', 'hop_he3', 'hop_rock', 'hop_pt', 'spill', 'melt_pool', 'leg_band', 'power_fin', 'grouser', 'flood_lens', 'axle', 'ant_tip',
        'tube_collar', 'hoop', 'cab_lamp_l', 'bed_liner', 'bed_rib', 'bed_hinge_lug', 'scoop_tooth', 'antenna', 'arm_ram', 'shock', 'door_window', 'cab_sidewin')
def is_truck(o):
    p = o.parent
    while p is not None:
        if p == TROOT: return True
        p = p.parent
    return False
mine = [o for o in bpy.data.collections['Mine'].all_objects] + [o for o in bpy.data.collections['Stage'].all_objects if base(o).startswith('haul_road')]

# ---------------- tiers (built here, hidden by default in game)
M_ = bpy.data.materials
WHITE, WHITE_S, GRAPH, GRAPH_S, CYAN, SATIN = M_['B_White'], M_['B_WhiteSmooth'], M_['B_Graphite'], M_['B_GraphiteSmooth'], M_['B_Cyan'], M_['B_Satin']
RADM = bpy.data.materials.new('B_Radiator')
def tag(objs, g):
    for o in objs: o['grp'] = g
    return objs
new = []
# Tier_03: conveyor light kit - cyan running lights on both trough walls + head/tail beacons
T03 = []
for i in range(1, 8):
    c = C0 + U * (Lc * i / 8)
    for s in (-1, 1):
        T03.append(beam('t03_light', c + SIDE * 0.86 * s + UP * 0.56 - U * 0.25, c + SIDE * 0.86 * s + UP * 0.56 + U * 0.25, 0.08, 0.1, CYAN, bevel=0))
T03.append(sphere('t03_beacon', 0.22, tuple(C1 + UP * 0.95 + U * 0.3), CYAN, sub=1))
T03.append(sphere('t03_beacon', 0.2, tuple(C0 - U * 0.2 + UP * 0.6), CYAN, sub=1))
tag(T03, 'Tier_03')
# Tier_05: second pod hopper (east of the first) + pneumatic feed tube onto the conveyor tail section
H2 = Vector((4.0, 4.2, 0)); OFF = H2 - Vector((ML.H_X, ML.H_Y, 0)); T05 = []
for o in list(bpy.data.objects):
    if o.type == 'MESH' and base(o) in ('hopper', 'hopper_in', 'hopper_rim', 'hopper_glow', 'hopper_band', 'hopper_spout_glow', 'hop_heap', 'hop_leg', 'hop_foot', 'hop_foot_glow', 'hop_knuckle'):
        n_ = o.copy(); n_.data = o.data.copy(); bpy.data.collections['Mine'].objects.link(n_); n_.matrix_world = Matrix.Translation(OFF) @ o.matrix_world; T05.append(n_)
pA = Vector((H2.x - 0.3, H2.y - 0.4, 3.3)); pB = C0 + U * (Lc * 0.3) + UP * 0.95
T05.append(rod('t05_feed', pA, pB, 0.26, WHITE_S, segs=20))
for t in (0.2, 0.5, 0.8): T05.append(rod('t05_collar', pA.lerp(pB, t - 0.03), pA.lerp(pB, t + 0.03), 0.3, GRAPH_S, segs=20))
T05.append(beam('t05_strip', pA + Vector((0, 0, 0.27)), pB + Vector((0, 0, 0.27)), 0.04, 0.03, CYAN, bevel=0))
tag(T05, 'Tier_05')
# Tier_08: radiator wing behind the rig power module (heat rejection for the plasma bore)
RWX, RWY = ML.RX - 5.2, ML.RY + 5.8; T08 = []
T08.append(rod('t08_mast', (RWX, RWY, 0.0), (RWX, RWY, 7.4), 0.2, GRAPH_S, r2=0.15, segs=16))
T08.append(box('t08_foot', (1.2, 1.2, 0.3), (RWX, RWY, 0.15), WHITE_S, bevel=0.05))
for k, z in enumerate((2.6, 4.2, 5.8)):
    for s in (-1, 1):
        T08.append(box('t08_panel', (2.6, 0.08, 1.3), (RWX + s * 1.55, RWY, z), RADM, bevel=0.0))
        T08.append(box('t08_edge', (2.6, 0.1, 0.06), (RWX + s * 1.55, RWY - 0.01, z + 0.66), GRAPH, bevel=0.0))
T08.append(box('t08_glow', (0.06, 0.12, 5.0), (RWX, RWY - 0.21, 4.2), CYAN, bevel=0))
T08.append(rod('t08_pipe', (RWX + 0.2, RWY - 0.2, 0.9), (ML.RX - 1.2, ML.RY + 3.0, 1.1), 0.12, WHITE_S, segs=12))
tag(T08, 'Tier_08')
# Tier_12: second ore silo (taller, behind the first) + transfer bridge
S2 = Vector((ML.BIN_X + 0.6, ML.BIN_Y + 5.6, 0)); T12 = []
for o in list(bpy.data.objects):
    if o.type == 'MESH' and base(o) in ('silo', 'silo_plinth', 'silo_band', 'silo_glow', 'silo_hatch'):
        n_ = o.copy(); n_.data = o.data.copy(); bpy.data.collections['Mine'].objects.link(n_)
        n_.matrix_world = Matrix.Translation(S2) @ Matrix.Diagonal((1, 1, 1.32, 1)) @ Matrix.Translation(Vector((-ML.BIN_X, -ML.BIN_Y, 0))) @ o.matrix_world; T12.append(n_)
T12.append(rod('t12_bridge', (ML.BIN_X, ML.BIN_Y + 0.6, 6.4), (S2.x, S2.y - 0.6, 8.5), 0.22, WHITE_S, segs=16))
T12.append(sphere('t12_beacon', 0.18, (S2.x + 1.4, S2.y - 1.2, 8.1), CYAN, sub=1))
tag(T12, 'Tier_12')
# Tier_20: Mk II bore crown - bigger crown housing + twin emitter pods + tall mast
RXc, RYc_ = ML.RX, ML.RYc; T20 = []
T20.append(box('t20_crown', (5.8, 2.6, 1.3), (RXc, RYc_, 17.45), WHITE, bevel=0.3, segs=3))
T20.append(box('t20_band', (5.86, 2.66, 0.12), (RXc, RYc_, 16.95), GRAPH, bevel=0.0))
T20.append(box('t20_strip', (5.0, 0.04, 0.12), (RXc, RYc_ - 1.32, 17.5), CYAN, bevel=0))
for s in (-1, 1):
    T20.append(sphere('t20_pod', 0.7, (RXc + s * 2.9, RYc_ - 0.2, 14.4), WHITE_S, scale=(0.8, 0.8, 1.25), sub=2))
    T20.append(sphere('t20_pod_glow', 0.35, (RXc + s * 2.9, RYc_ - 0.62, 14.1), CYAN, scale=(1, 0.5, 1), sub=1))
T20.append(rod('t20_mast', (RXc - 1.8, RYc_ + 0.5, 18.1), (RXc - 1.8, RYc_ + 0.5, 21.5), 0.09, GRAPH_S, segs=8))
T20.append(sphere('t20_tip', 0.18, (RXc - 1.8, RYc_ + 0.5, 21.6), CYAN, sub=1))
tag(T20, 'Tier_20')
# Conveyor node: evenly spaced ore lumps riding the belt (clip moves them one spacing along the belt and loops)
LUMP_S = 0.9; LUMP = []
import random; rl = random.Random(5)
nl = int((Lc - 0.6) / LUMP_S)
for i in range(nl):
    p = C0 + U * (0.3 + i * LUMP_S) + UP * 0.12 + SIDE * rl.uniform(-0.3, 0.3)
    LUMP.append(sphere('conv_lump', rl.uniform(0.16, 0.22), tuple(p), M_['B_OreRock'] if i % 3 else M_['B_He3'], scale=(1.2, 1, 0.7), sub=1, smooth=False))
tag(LUMP, 'Conveyor')
mine += T03 + T05 + T08 + T12 + T20 + LUMP

# focus = the base station (rig, hopper, conveyor, silo, roads in frame, truck at the bay) + every tier vertex
_FOC = []
for o in bpy.data.objects:
    if o.type != 'MESH' or is_truck(o): continue
    b = base(o)
    if b.startswith(('pad', 'crown', 'ant_tip', 'beacon', 'op_pod', 'hopper', 'silo', 'head_housing', 'dis_chute', 'head_col', 'tail_housing', 'spine', 'dep_patch', 'conv', 'rig', 'tower', 'chute')):
        _FOC += [tuple(o.matrix_world @ Vector(c)) for c in o.bound_box]
for x, y in ((ML.LX - 4.4, ML.LY), (ML.LX + 3.5, ML.LY + 2.0), (ML.U_X + 2.4, ML.LY - 2.0), (ML.U_X, -ML.R_T + ML.R_T + 2.0)):
    _FOC.append((x, y, 0.0))                       # truck at the bay (tail .. cab) + approach pose, kept on screen
FP = np.array(_FOC); TP = obj_pts(T03 + T05 + T08 + T12 + T20)
FIT = cam_fit(TP, FP); W, CAM_T, CAM_D, FIT_BOX = FIT
CAM_T = Vector((round(CAM_T.x, 2), round(CAM_T.y, 2), round(CAM_T.z, 2)))
print('CAMFIT W=%.1f target=%s d=%.2f box=%s' % (W, tuple(CAM_T), CAM_D, tuple(round(v) for v in FIT_BOX)))
for g, objs in (('Tier_03', T03), ('Tier_05', T05), ('Tier_08', T08), ('Tier_12', T12), ('Tier_20', T20)):
    P_ = obj_pts(objs)
    for (pw, ph), (b0, b1) in SIZES.items():
        xs, ys = proj_np(P_, np.array(CAM_T), W, pw, ph)
        print('TIERBOX %s %dx%d x %d..%d y %d..%d %s' % (g, pw, ph, xs.min(), xs.max(), ys.min(), ys.max(), 'inside' if xs.min() >= 0 and xs.max() <= pw and ys.min() >= b0 and ys.max() <= b1 else 'OUTSIDE'))
if MODE == 'phone':      # renders the 1179x2556 master; phone_downscale.py makes the 393x852 (Lanczos)
    cam = sc.camera; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(FOV_Y); cam.data.dof.use_dof = False
    pos, d = cam_pose(CAM_T, W); cam.location = pos; cam.rotation_euler = (CAM_T - pos).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = 1179, 2556; sc.render.resolution_percentage = int(A.get('pct', 100))
    sc.cycles.samples = int(A.get('ps', 64)); sc.render.use_border = False
    os.makedirs(MOUT, exist_ok=True)
    big = os.path.join(MOUT, 'mine_phone_1179x2556.png'); sc.render.filepath = big
    bpy.ops.render.render(write_still=True)
    print('PHONE done', big)
    raise SystemExit(0)
if MODE == 'tiers':      # Director rule: every tier part must land inside the station frame (393x852, y 100-650). Renders all tiers visible.
    from bpy_extras.object_utils import world_to_camera_view
    cam = sc.camera; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(FOV_Y); cam.data.dof.use_dof = False
    pos, d = cam_pose(CAM_T, W); cam.location = pos; cam.rotation_euler = (CAM_T - pos).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = PW, PH; sc.render.resolution_percentage = 100; bpy.context.view_layer.update()
    TR = {}
    for g, objs in (('Tier_03', T03), ('Tier_05', T05), ('Tier_08', T08), ('Tier_12', T12), ('Tier_20', T20)):
        pr = [world_to_camera_view(sc, cam, o.matrix_world @ v.co) for o in objs for v in o.data.vertices]
        xs = [q.x * PW for q in pr]; ys = [(1 - q.y) * PH for q in pr]
        TR[g] = [round(min(xs)), round(max(xs)), round(min(ys)), round(max(ys))]
        print('TIERBOX', g, 'x', TR[g][0], TR[g][1], 'y', TR[g][2], TR[g][3], 'inside' if min(xs) >= 0 and max(xs) <= PW and min(ys) >= 100 and max(ys) <= 650 else 'OUTSIDE')
    json.dump(TR, open(os.path.join(MOUT, 'tier_boxes.json'), 'w'))
    sc.cycles.samples = int(A.get('ps', 32)); sc.render.use_border = False
    os.makedirs(MOUT, exist_ok=True); sc.render.filepath = os.path.join(MOUT, 'mine_tiers_393x852.png'); bpy.ops.render.render(write_still=True)
    raise SystemExit(0)

# ---------------- cull + bake to world meshes
keep = []
for o in mine:
    if o.type not in ('MESH', 'CURVE'): continue
    b = base(o); nm = b.lower()
    if o.get('grp'): keep.append(o); continue
    if o.get('keep_truck'): keep.append(o); continue
    if nm.startswith(DROP): continue
    if 'Ram' in b and is_truck(o): keep.append(o); continue
    dims = o.dimensions; big = max(dims)
    glow = any(k in nm for k in ('glow', 'strip', 'beacon', 'eye', 'tip', 'lightbar'))
    if big < 0.25 and not glow: continue
    if big < 1.0 and min(dims) < 0.03 and not glow: continue
    keep.append(o)
for o in keep:
    for md in o.modifiers:
        if md.type == 'BEVEL': md.show_viewport = False
    if o.type == 'CURVE': o.data.bevel_resolution = min(o.data.bevel_resolution, 2); o.data.resolution_u = min(o.data.resolution_u, 6)
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
col = bpy.data.collections.new('Game'); sc.collection.children.link(col)

# truck bone assignment
AX = [(x, sy * 1.5) for sy in (1, -1) for x in ML.AXLES]   # left (+Y) rear->front, right (-Y) rear->front
WHEELN = ['HT04_Wheel_RL', 'HT04_Wheel_ML', 'HT04_Wheel_FL', 'HT04_Wheel_RR', 'HT04_Wheel_MR', 'HT04_Wheel_FR']   # F = front axle, M/R = rear tandem
def seg_dist(p, a, b):
    ab = b - a; t = max(0, min(1, (p - a).dot(ab) / ab.length_squared)); return (a + ab * t - p).length
def truck_bone(o, cl):
    b = base(o)
    if b in ('tire', 'rim', 'hub', 'hub_glow', 'hub_cap'):
        k = min(range(6), key=lambda i: (cl.x - AX[i][0]) ** 2 + (cl.y - AX[i][1]) ** 2); return WHEELN[k]
    if b.startswith('Ram'):
        side = 'R' if b[3] == 'L' else 'L'      # concept 'RamL' sits at -Y = the truck's right
        if 'Stage2' in b: return 'Truck_Ram_%s_Stage2' % side
        if 'Rod' in b: return 'Truck_Ram_%s_Rod' % side
        return 'Truck_Ram_%s' % side
    if b == 'bed_heap': return 'Truck_Load'
    if b == 'load_chunk': return o['chunk_bone']
    if o.parent and base(o.parent) == 'Bed_Pivot': return 'Truck_Bed'
    return 'Truck_Chassis'

groups = {}
for o in keep:
    road = bool(o.get('road'))
    e = o.evaluated_get(dg); me = bpy.data.meshes.new_from_object(e, preserve_all_data_layers=road, depsgraph=dg)
    if me is None or len(me.polygons) == 0: continue
    me.transform(o.matrix_world)
    if len(me.materials) == 0: me.materials.append(None)
    sm = [shared_for(m) for m in me.materials]
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        s = sm[min(poly.material_index, len(sm) - 1)]
        for li in poly.loop_indices: ca.data[li].color = s[1]
    if road and 'RoadCol' in me.color_attributes:      # graded road: keep its own track / tyre-mark / berm colours
        rc = me.color_attributes['RoadCol']
        for li in range(len(me.loops)): ca.data[li].color = rc.data[li].color
        me.color_attributes.remove(me.color_attributes['RoadCol'])
    me.color_attributes.active_color = me.color_attributes['Col']
    for i, (m_, _) in enumerate(sm): me.materials[i] = m_
    if base(o) == 'bed_heap':                          # ore pile: pale broken regolith (reads against the dark bed) with He-3 crystal flecks
        for j_, poly in enumerate(me.polygons):
            h_ = (j_ * 7919) % 100
            c_ = lin('#2fe3ff') if h_ < 16 else lin('#b4ada1') if h_ < 58 else lin('#9c958a') if h_ < 86 else lin('#c9c2b5')
            for li in poly.loop_indices: ca.data[li].color = c_
    if base(o) == 'load_chunk' and o['chunk_bone'].startswith('Truck_Rich'):   # rich ore: bright glow cyan, faceted
        for j_, poly in enumerate(me.polygons):
            c_ = lin('#5fe8ff') if j_ % 3 else lin('#c8fbff')
            for li in poly.loop_indices: ca.data[li].color = c_
    if base(o) == 'load_chunk' and o['chunk_bone'].startswith('Truck_Pour'):   # stream chunks: pale rock / bright He-3 (read in the chute shadow)
        he_ = int(o['chunk_bone'][-2:]) % 2 == 0
        for j_, poly in enumerate(me.polygons):
            c_ = (lin('#5fe8ff') if j_ % 3 else lin('#c8fbff')) if he_ else (lin('#cdc6b9') if j_ % 2 else lin('#aaa397'))
            for li in poly.loop_indices: ca.data[li].color = c_
    if base(o) == 'load_chunk' and o['chunk_bone'].startswith('Truck_Dust'):   # landing dust: pale regolith grey
        for j_, poly in enumerate(me.polygons):
            c_ = lin('#d8d3c8') if j_ % 2 else lin('#bdb7ab')
            for li in poly.loop_indices: ca.data[li].color = c_
    b = base(o)
    if is_truck(o):
        g = 'Truck'
        me.transform(Matrix.Translation(-TORG))
        cl = sum((v.co for v in me.vertices), Vector()) / len(me.vertices)
        bone = truck_bone(o, cl)
    else:
        g = o.get('grp') or ('Rig' if b in RIG else 'Silo' if b in SILO else 'Base'); bone = None
    no = bpy.data.objects.new('g_' + o.name, me); col.objects.link(no); groups.setdefault(g, []).append(no)
    if road: no['road'] = 1
    if bone:
        vg = no.vertex_groups.new(name=bone); vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE'); no['bone'] = bone
for c in list(sc.collection.children):
    if c != col: sc.collection.children.unlink(c)

FILL_BONES = {'Truck_Load'} | {bn for bn, _, _ in CHUNKS}
def tris(objs): return sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
for g, objs in groups.items():
    for o in objs:
        if o.get('road') or o.get('bone') in FILL_BONES: continue   # roads keep their profile columns; the fill pile + chunks keep their grids
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.004)
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(4), verts=bm.verts, edges=bm.edges, delimit={'MATERIAL'})
        bm.to_mesh(o.data); bm.free()
T1 = {g: tris(o) for g, o in groups.items()}; print('TRIS after planar', T1, sum(T1.values()))
BUD = {'Truck': int(A.get('truck', 3950)),   # HT-04 shared prop (art/3d/props/ht04): <= 4k tris, 1 draw
       'Rig': 650, 'Conveyor': 300, 'Silo': 800,
       'Tier_03': 260, 'Tier_05': 1400, 'Tier_08': 320, 'Tier_12': 700, 'Tier_20': 420}
BUD['Base'] = TARGET - sum(min(BUD[g], T1[g]) for g in T1 if g != 'Base') - (min(6000, T1['Truck']) - min(BUD['Truck'], T1['Truck']))   # the truck moved to its own prop: its saving comes off the Mine, not into the Base
print('BUDGET', BUD)
def join(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); return bpy.context.view_layer.objects.active
def decimate(o, tgt):
    for it in range(8):
        t = tris([o])
        if t <= tgt: break
        mod = o.modifiers.new('dec', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'; mod.ratio = tgt / t * 0.98; mod.use_collapse_triangulate = True
        if o.vertex_groups and False: mod.vertex_group = ''
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=mod.name)
def set_origin(o, p):
    o.data.transform(Matrix.Translation(-p)); o.location = p
def area_by_mat(o):
    a = {}
    for p in o.data.polygons:
        m = o.material_slots[p.material_index].material.name; a[m] = a.get(m, 0) + p.area
    return a
root = bpy.data.objects.new('Mine', None); col.objects.link(root)
TIERS = {'Tier_03': 3, 'Tier_05': 5, 'Tier_08': 8, 'Tier_12': 12, 'Tier_20': 20}
PIV = {'Rig': Vector((ML.RX, ML.RYc, 8.65)), 'Conveyor': C0.copy(), 'Silo': Vector((ML.BIN_X, ML.BIN_Y, 0.0))}
NODES = {}
truck_mesh = None
for g, objs in groups.items():
    if g == 'Truck':
        # decimate parts per bone so seams between rigid parts stay clean
        byb = {}
        for o in objs: byb.setdefault(o['bone'], []).append(o)
        tx_ = sum(tris(os_) for b_, os_ in byb.items() if b_ in FILL_BONES)   # pile + chunks are exempt: shrink the rest to fit
        tt = tris(objs); r = min(1.0, (BUD['Truck'] - tx_) / max(1, tt - tx_)); parts = []
        for bname, os_ in byb.items():
            j = join(os_) if len(os_) > 1 else os_[0]
            if tris([j]) > 60 and bname not in FILL_BONES: decimate(j, max(40, int(tris([j]) * r)))
            parts.append(j)
        truck_mesh = join(parts); truck_mesh.name = 'Truck_Mesh'; truck_mesh.data.name = 'Truck_Mesh'
        if 'bone' in truck_mesh: del truck_mesh['bone']
        continue
    if g == 'Base':                            # roads are exempt from decimation (it would smear the ruts and berms)
        rd = [o for o in objs if o.get('road')]; rest = [o for o in objs if not o.get('road')]; RT = tris(rd)
        J_ = join(rest); decimate(J_, BUD[g] - RT); J_ = join([J_] + rd); print('ROAD tris', RT, 'base rest', BUD[g] - RT)
    else:
        J_ = join(objs)
        decimate(J_, BUD[g])
    if g == 'Base':
        bpy.ops.object.material_slot_remove_unused()
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
        parts = [o for o in bpy.context.selected_objects if o.type == 'MESH']
        for o in parts:
            used = {p.material_index for p in o.data.polygons}
            o.name = o.material_slots[list(used)[0]].material.name.replace('SHM_', 'Base_'); o.data.name = o.name + '_mesh'
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
            bpy.ops.object.material_slot_remove_unused(); bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
            o.parent = root; NODES[o.name] = o
        continue
    a = area_by_mat(J_); dom = max(a, key=a.get)
    if g == 'Tier_03': dom = 'SHM_GlowCyan'
    elif dom != 'SHM_Paint': dom = 'SHM_Paint'
    J_.data.materials.clear(); J_.data.materials.append(SH[dom])
    for p in J_.data.polygons: p.material_index = 0
    J_.name = g; J_.data.name = g + '_mesh'
    bpy.ops.object.select_all(action='DESELECT'); J_.select_set(True); bpy.context.view_layer.objects.active = J_
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    bb = [Vector(c) for c in J_.bound_box]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx = Vector([max(v[i] for v in bb) for i in range(3)])
    piv = PIV.get(g, Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, 0.0)))
    set_origin(J_, piv); J_.parent = root; NODES[g] = J_
    if g in TIERS: J_['tier'] = TIERS[g]; J_['hidden_by_default'] = True

# ---------------- truck: single skinned mesh under the 'Truck' armature
tm = truck_mesh
tm.data.materials.clear(); tm.data.materials.append(SH['SHM_Paint'])
for p in tm.data.polygons: p.material_index = 0
bpy.ops.object.select_all(action='DESELECT'); tm.select_set(True); bpy.context.view_layer.objects.active = tm
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
ad = bpy.data.armatures.new('Truck_Armature'); arm = bpy.data.objects.new('Truck', ad); col.objects.link(arm)
arm.location = (ML.TX, ML.TY, 0.0); arm.parent = root
bpy.context.view_layer.objects.active = arm; bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
HINGE = ML.HINGE_T.copy(); BXc = (ML.BX0 + ML.BX1) / 2
RAM_B = {s: Vector((-1.0, sy * ML.RAM_Y, 1.42)) for s, sy in (('R', -1), ('L', 1))}
RAM_T = {s: Vector((0.05, sy * ML.RAM_Y, 1.74)) for s, sy in (('R', -1), ('L', 1))}
def ram_geo(s, ang):
    b = RAM_B[s]; t = HINGE + Matrix.Rotation(-ang, 3, 'Y') @ (RAM_T[s] - HINGE); d = t - b
    ext = d.length - ML.RAM_STAGE; return b, d.normalized(), (max(0.04, ext * 0.5), ext)
LOAD_C = Vector((BXc, 0, ML.BZ + 0.06))
BONES = [('Truck_Chassis', None, Vector((0, 0, 0))), ('Truck_Bed', 'Truck_Chassis', HINGE), ('Truck_Load', 'Truck_Bed', LOAD_C)]
for s in ('L', 'R'):
    b, u0, (o2, o3) = ram_geo(s, 0.0)
    BONES += [('Truck_Ram_%s' % s, 'Truck_Chassis', b), ('Truck_Ram_%s_Stage2' % s, 'Truck_Ram_%s' % s, b + u0 * o2), ('Truck_Ram_%s_Rod' % s, 'Truck_Ram_%s' % s, b + u0 * o3)]
RICH_C = HEAP_C - TORG                       # heap base centre (truck-local)
BONES += [(bn, 'Truck_Chassis', CH_REST[bn].copy()) for bn, _, _ in CHUNKS]
for i, (x, y) in enumerate(AX): BONES.append((WHEELN[i], 'Truck_Chassis', Vector((x, y, ML.WR))))
for n, par, h in BONES:
    eb = ad.edit_bones.new(n); eb.head = h; eb.tail = h + Vector((0, 0, 0.3)); eb.roll = 0.0
    if n in WHEELN: eb.align_roll(Vector((1, 0, 0)))   # wheel joint local +X = the axle, pointing to the truck's left (glTF -Z): + spin about local X rolls forward
    if par: eb.parent = ad.edit_bones[par]; eb.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
tm.parent = arm; tm.matrix_parent_inverse = Matrix.Identity(4); tm.location = (0, 0, 0)
mod = tm.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
for n, _, _ in BONES:
    if n not in tm.vertex_groups: tm.vertex_groups.new(name=n)    # empty groups keep joint order stable
tm.name = 'Truck_Mesh'
# fill morph: Basis = thin layer (fill 0 %), key 'fill' = the heaped-full pile (fill 100 %). Linear blend = the pile rises and spreads.
_gi = tm.vertex_groups['Truck_Load'].index
HEAPV = [v.index for v in tm.data.vertices if any(g.group == _gi and g.weight > 0.5 for g in v.groups)]
tm.shape_key_add(name='Basis', from_mix=False); kf = tm.shape_key_add(name='fill', from_mix=False)
for i in HEAPV:                                 # vertices sit on the Basis shape (+ rock noise); the key = FULL with the same noise
    c_ = tm.data.vertices[i].co.copy()
    if c_.z < PILE_SKIRT_Z + 0.02: continue      # skirt ring: identical in both shapes
    r_ = pile_r(c_.x, c_.y); kf.data[i].co = Vector((c_.x, c_.y, pile_full(r_) + (c_.z - pile_basis(r_))))
tm.data.shape_keys.use_relative = True; kf.value = 0.0
REMAP = 'influence = 0.5 + 0.5 * (fill_pct / 100) ** 0.8 for fill_pct > 0; influence = 0 at fill_pct 0 (empty, after a dump)'
FILL_INFO = {'mesh': 'Truck_Mesh', 'morph_target': 'fill', 'morph_index': 0, 'remap': REMAP, 'heap_verts': len(HEAPV),
             'rim_top_m': RIM_TOP, 'apex_m': {'0': BASIS_APEX, '0.5': MID_APEX, '1': FULL_APEX},
             'apex_over_rim_m': {'0.5': round(MID_APEX - RIM_TOP, 3), '1': round(FULL_APEX - RIM_TOP, 3)}}
tm['fill_morph'] = 'morphTargetInfluences[0] (target "fill"): ' + REMAP + '. 0.5 = crowning heap just over the rim, 1 = heaped full; truck_dump empties it via Truck_Load'
print('FILL morph verts', len(HEAPV))
bpy.context.view_layer.update()

# ---------------- truck clip posing (armature space == truck-local, bones Y-up == local +Z)
def Tm(v): return Matrix.Translation(v)
def about(c, R3): return Tm(c) @ R3.to_4x4() @ Tm(-c)
def ease(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
def bed_G(a): return about(HINGE, Matrix.Rotation(-a, 3, 'Y'))
def ram_G(s, a):
    b, u0, (o2r, o3r) = ram_geo(s, 0.0); _, u, (o2, o3) = ram_geo(s, a); R = u0.rotation_difference(u).to_matrix()
    Gb = about(b, R); G2 = Tm(b + u * o2) @ R.to_4x4() @ Tm(-(b + u0 * o2r)); G3 = Tm(b + u * o3) @ R.to_4x4() @ Tm(-(b + u0 * o3r))
    return Gb, G2, G3
def load_G(a, fill):
    sxy = 0.75 + 0.25 * fill; sz = max(0.02, fill)
    return bed_G(a) @ Tm(LOAD_C) @ Matrix.Diagonal((sxy, sxy, sz, 1)) @ Tm(-LOAD_C)
def wheel_G(i, th):
    x, y = AX[i]; return about(Vector((x, y, ML.WR)), Matrix.Rotation(th, 3, 'Y'))
ORDER = [n for n, _, _ in BONES]
def pose(Gs):
    """Gs: bone -> armature-space delta transform (applied to rest). Hierarchy order."""
    for n in ORDER:
        pb = arm.pose.bones[n]
        G = Gs.get(n, Matrix.Identity(4))
        pb.matrix = G @ arm.data.bones[n].matrix_local
        bpy.context.view_layer.update()
def rest_pose():
    for pb in arm.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()
def dump_pose(f, F=90):
    a = math.radians(50) * (ease(f / (F / 2)) if f <= F / 2 else ease((F - f) / (F / 2)))
    up = f <= F / 2
    fill = 1.0 if up and a < math.radians(18) else (max(0.0, 1 - (a - math.radians(18)) / math.radians(24)) if up else 0.0)
    G = {'Truck_Bed': bed_G(a), 'Truck_Load': load_G(a, fill)}
    for s in ('L', 'R'):
        Gb, G2, G3 = ram_G(s, a); G['Truck_Ram_%s' % s] = Gb; G['Truck_Ram_%s_Stage2' % s] = G2; G['Truck_Ram_%s_Rod' % s] = G3
    return G, a
# chute_pour (loop, 36 f = 1.2 s) and truck_load_rich (30 f = 1.0 s); truck parked at Path_Load (bed centre under the chute mouth)
POUR_F, RICH_F = 36, 30
CH_R = {bn: r for bn, _, r in CHUNKS}
MOUTH = Vector((HEAP_C.x - TORG.x, HEAP_C.y - TORG.y, CHUTE_Z - TORG.z - 0.1))
ZLAND = MID_APEX - 0.12                          # chunks sink into the pile top here (inside a fuller pile they vanish a little earlier)
def fall_G(bn, u, land, spin):
    """u 0..1 along the fall (accelerating); grows in at the mouth, shrinks to 0 on landing. u outside -> hidden at the mouth."""
    r0 = CH_REST[bn]
    if u < 0 or u > 1: return Tm(MOUTH) @ Matrix.Diagonal((0, 0, 0, 1)) @ Tm(-r0)
    p = Vector((MOUTH.x + land.x * u, MOUTH.y + land.y * u, MOUTH.z - (MOUTH.z - ZLAND) * (0.35 * u + 0.65 * u * u)))
    sc_ = CH_R[bn] / ORE_SPECK * min(1.0, u / 0.08, (1.0 - u) / 0.12)
    R_ = Matrix.Rotation(spin * u, 4, 'X') @ Matrix.Rotation(0.7 * spin * u, 4, 'Z')
    return Tm(p) @ R_ @ Matrix.Diagonal((sc_, sc_, sc_, 1)) @ Tm(-r0)
def puff_G(bn, u, d):
    """dust puff: grows fast at the landing spot, drifts up/out and shrinks to 0 (fade by scale). u outside 0..1 -> hidden."""
    r0 = CH_REST[bn]
    if u < 0 or u > 1: return Tm(Vector((MOUTH.x, MOUTH.y, ZLAND))) @ Matrix.Diagonal((0, 0, 0, 1)) @ Tm(-r0)
    p = Vector((MOUTH.x + d.x * (0.4 + 0.6 * u), MOUTH.y + d.y * (0.4 + 0.6 * u), ZLAND + 0.08 + 0.32 * u))
    sc_ = CH_R[bn] / ORE_SPECK * (min(1.0, u / 0.25) * (1.0 - max(0.0, (u - 0.35) / 0.65)) ** 1.2) * (0.6 + 0.6 * u)
    return Tm(p) @ Matrix.Diagonal((sc_, sc_, sc_, 1)) @ Tm(-r0)
POUR = [bn for bn, _, _ in CHUNKS if bn.startswith('Truck_Pour')]
RICH = [bn for bn, _, _ in CHUNKS if bn.startswith('Truck_Rich')]
DUST = [bn for bn, _, _ in CHUNKS if bn.startswith('Truck_Dust')]
POUR_FALL, DUST_LIFE = 24.0, 15.0                # frames: each chunk falls 0.8 s; a new one leaves the mouth every 36/7 f -> ~5 in the air
POUR_LAND = [Vector((0.3 * math.cos(2.4 * k), 0.22 * math.sin(2.4 * k))) for k in range(POUR_N)]
DUST_DIR = [Vector((0.55 * math.cos(1.1 + 1.6 * k), 0.4 * math.sin(1.1 + 1.6 * k))) for k in range(DUST_N)]
RICH_LAND = [Vector((0.3, 0.1)), Vector((-0.3, -0.15)), Vector((0.05, 0.3)), Vector((-0.1, -0.3)), Vector((0.2, -0.2))]
def pour_pose(f):
    f = f % POUR_F                                # every channel is periodic in 36 f -> frame 36 == frame 0, seamless loop
    G = {bn: fall_G(bn, (((f - POUR_F * k / POUR_N) % POUR_F) / POUR_FALL), POUR_LAND[k], 2.0 + k) for k, bn in enumerate(POUR)}
    G.update({bn: puff_G(bn, (((f - POUR_F * k / DUST_N - POUR_FALL + 2) % POUR_F) / DUST_LIFE), DUST_DIR[k]) for k, bn in enumerate(DUST)})
    return G
def rich_pose(f):
    return {bn: fall_G(bn, ((f - (0, 3, 5, 8, 10)[k]) / 18.0) if f > (0, 3, 5, 8, 10)[k] else -1, RICH_LAND[k], 2.5 + k) for k, bn in enumerate(RICH)}

def eval_parts(sel):
    """posed (skinned) truck mesh split into two polygon soups by bone predicate; returns (verts, polys, bone_of_poly) x2"""
    dg_ = bpy.context.evaluated_depsgraph_get(); e = tm.evaluated_get(dg_); me = e.to_mesh()
    gi = {g.index: g.name for g in tm.vertex_groups}
    vb = {v.index: (gi[v.groups[0].group] if len(v.groups) else 'Truck_Chassis') for v in tm.data.vertices}
    A_, B_ = ([], [], []), ([], [], [])
    vs = [v.co.copy() for v in me.vertices]
    for p in me.polygons:
        bn = vb[p.vertices[0]]; tgt = A_ if sel(bn) else B_
        b0 = len(tgt[0]); tgt[0].extend(vs[i] for i in p.vertices); tgt[1].append(tuple(range(b0, b0 + len(p.vertices)))); tgt[2].append(bn)
    e.to_mesh_clear()
    return A_, B_
def overlap(A_, B_, skip=lambda a, b: False):
    if not A_[1] or not B_[1]: return 0, 99.0, {}
    ta, tb = BVHTree.FromPolygons(A_[0], A_[1]), BVHTree.FromPolygons(B_[0], B_[1])
    pairs = {}
    for i, j in ta.overlap(tb):
        k = (A_[2][i], B_[2][j])
        if skip(*k): continue
        pairs[k] = pairs.get(k, 0) + 1
    md = min((tb.find_nearest(v)[3] for v in A_[0][::3]), default=99.0)
    return sum(pairs.values()), md, pairs
REPORT = {'arm': 'removed (no scoop arm on the HT-04)'}
rest_pose()

# ---------------- clips
sc.render.fps = 30
BAKED = {}
def bake(clip, frames, fn, bones):
    if clip in bpy.data.actions: bpy.data.actions[clip].name = '_concept_' + clip   # the concept file has its own 'truck_dump'
    act = bpy.data.actions.new(clip); arm.animation_data_create(); arm.animation_data.action = act; BAKED[clip] = act
    for f in frames:
        rest_pose(); pose(fn(f))
        for n in bones:
            pb = arm.pose.bones[n]
            pb.keyframe_insert('location', frame=f, group=n); pb.keyframe_insert('rotation_quaternion', frame=f, group=n); pb.keyframe_insert('scale', frame=f, group=n)
    for fc in act.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    arm.animation_data.action = None
    tr = arm.animation_data.nla_tracks.new(); tr.name = clip; st = tr.strips.new(clip, frames[0], act); tr.mute = True
    return act
RAMB = ['Truck_Ram_%s%s' % (s, x) for s in ('L', 'R') for x in ('', '_Stage2', '_Rod')]
bake('truck_dump', list(range(0, 91)), lambda f: dump_pose(f)[0], ['Truck_Bed', 'Truck_Load'] + RAMB)
# truck_drive: 1.0 s seamless body loop (bed rattle on the suspension). NO wheel spin in any clip: code spins HT04_Wheel_* about local X by distance / wheel_radius
bake('truck_drive', list(range(0, 31)), lambda f: {'Truck_Bed': Tm(Vector((0, 0, 0.012 * math.sin(2 * math.tau * f / 30) + 0.006 * math.sin(3 * math.tau * f / 30 + 1.0))))}, ['Truck_Bed'])
bake('chute_pour', list(range(0, POUR_F + 1)), pour_pose, POUR + DUST)
bake('truck_load_rich', list(range(0, RICH_F + 1)), rich_pose, RICH)

rest_pose()
def obj_keys(ob, clip, path, frames, interp='LINEAR'):
    ob.animation_data_create(); act = bpy.data.actions.new(clip); ob.animation_data.action = act
    rest = tuple(getattr(ob, path))
    for f, v in frames: setattr(ob, path, v); ob.keyframe_insert(path, frame=f)
    for fc in act.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = interp
    setattr(ob, path, rest)
rg = NODES['Rig']; L0 = rg.location.copy()
obj_keys(rg, 'dig', 'location', [(f, L0 + Vector((0, 0, -0.6 * (0.5 - 0.5 * math.cos(math.tau * f / 90))))) for f in range(0, 91, 3)])
cv = NODES['Conveyor']; Lv = cv.location.copy()
obj_keys(cv, 'conveyor_run', 'location', [(0, Lv), (30, Lv + U * LUMP_S)])

# ---------------- markers (empties). Truck-pose markers: position = Truck node position, yaw about +Y(glTF) = Truck heading.
def H(x, y): return round(LAY['height'](x, y), 3)
for o in list(bpy.data.objects):          # concept-B helper markers (Markers collection) - replaced by the game markers below
    if o.type == 'EMPTY' and base(o) in ('Dep_01', 'Dep_02', 'Cam_Target'): bpy.data.objects.remove(o, do_unlink=True)
def emp(name, loc, yaw_deg=0.0, extras=None):
    e = bpy.data.objects.new(name, None); e.empty_display_type = 'ARROWS'; e.empty_display_size = 0.8
    e.location = loc; e.rotation_euler = (0, 0, math.radians(yaw_deg)); col.objects.link(e); e.parent = root
    for k, v in (extras or {}).items(): e[k] = v
    return e
def gl(v): return [round(v[0], 3), round(v[2], 3), round(-v[1], 3)]
emp('Cam_Target', tuple(CAM_T), 0, {'frame_w': W, 'fov_y_deg': FOV_Y, 'pitch_down_deg': PITCH, 'distance_m': round(CAM_D, 2), 'camera_side': '+Z (glTF)'})
DIS = LAY['DIS']
BEDC_W = Vector((ML.LX + LOAD_C.x, ML.LY + LOAD_C.y, 0.0))      # bed centre with the truck root on Path_Load (heading +X)
print('LOADCHECK bed centre (world)', tuple(round(v, 3) for v in BEDC_W), 'chute DIS', tuple(round(v, 3) for v in DIS), 'dxy', round((BEDC_W.xy - DIS.xy).length, 4))
emp('Path_Load', ML.LOAD, 0, {'kind': 'truck_pose', 'yaw_deg': 0, 'chute_glTF': gl((DIS.x, DIS.y, 4.35)),
    'bed_centre_glTF': gl((BEDC_W.x, BEDC_W.y, LOAD_C.z)), 's_m': 0.0, 'next_leg': json.dumps({'type': 'straight', 'length_m': round(ML.REV, 3)}),
    'note': 'bed centre exactly under the chute mouth; reverse in 1.5 m from Path_Load_Approach, play chute_pour (loop) while code raises the fill morph 0->100 %, then drive off forward (+X glTF) dead straight along the outbound lane (glTF z 9): Path_Out_01 (= Road_Entry) -> Path_Out_02 at x 26'})
emp('Path_Load_Approach', (ML.U_X, ML.LY, 0.0), 0, {'kind': 'truck_pose', 'yaw_deg': 0, 'route': 'return (empty)', 'reverse_m': round(ML.REV, 3), 's_m': round(sum(lg[3] for lg in ML.RET_LEGS), 3),
    'next_leg': json.dumps({'type': 'straight', 'length_m': round(ML.REV, 3), 'reverse': True}),
    'note': 'on return: Path_Ret_01..03 end here heading +X (end of the U-turn); stop, then reverse 1.5 m straight along -X (glTF) to Path_Load'})
emp('Rich_Pop', (BEDC_W.x, BEDC_W.y, GZ + ML.BTOP + 1.6), 0, {'kind': 'fx_anchor', 'note': 'money pop for the rich load: spawn the +value pop here when truck_load_rich plays (truck parked at Path_Load)'})
FA = bpy.data.objects.new('Fill_Arc', None); col.objects.link(FA); FA.parent = arm; FA.location = (2.2, 0.0, 4.6)   # truck-local: 0.9 m over the cab light bar
FA['kind'] = 'ui_anchor'; FA['note'] = 'anchor for the slim cyan fill-% arc, child of the Truck root (truck-local glTF (2.2, 4.6, 0)): 0.9 m over the cab light bar'
emp('Operator_Deck', (-4.5, -6.5, 0.0), 0, {'kind': 'prop_anchor', 'prop': 'art/3d/props/mine_operator/mine_operator_game.glb', 'note': 'place the mine operator prop root here, rotation identity (deck front faces +Z glTF, toward the camera); scenery only'})
# haul way-points (10/23 PM): Path_Out_NN = loaded, Path_Load -> outbound lane (glTF z 9) -> x 26;
# Path_Ret_NN = empty, x 26 on the return lane (glTF z 0) -> U-turn -> Path_Load_Approach. One marker at the START of every leg;
# extras.next_leg says how to get to the next marker (straight, or an arc of radius 4.5 m about centre_glTF), so code can follow the
# eased curves exactly (or sample them) instead of cutting corners between markers.
SPEED = 100.0 / 12.0
def _tan(lg):
    if lg[0] == 'line': d = lg[2] - lg[1]
    else: a0, a1 = lg[2]; sg = 1 if a1 > a0 else -1; d = Vector((-math.sin(a0) * sg, math.cos(a0) * sg, 0))
    return math.degrees(math.atan2(d.y, d.x))
def _leg_x(lg):
    if lg[0] == 'line': return {'type': 'straight', 'length_m': round(lg[3], 3)}
    a0, a1 = lg[2]
    return {'type': 'arc', 'turn': 'left' if a1 > a0 else 'right', 'radius_m': ML.R_T, 'centre_glTF': gl(lg[1]), 'sweep_deg': round(abs(math.degrees(a1 - a0)), 1), 'length_m': round(lg[3], 3)}
def _yaw(v): v = (v + 180.0) % 360.0 - 180.0; return 180.0 if abs(v + 180.0) < 1e-6 else round(v, 2)
HAUL = {}
for pre, legs, first, last in (('Path_Out', ML.OUT_LEGS, 1, 'leaves the Mine at x 26 on the outbound lane (glTF z 9, heading +X) = the Refinery road strip inbound lane'),
                               ('Path_Ret', ML.RET_LEGS, 0, 'next: Path_Load_Approach, stop, reverse 1.5 m along -X to Path_Load')):
    s_ = sum(lg[3] for lg in legs[:first]); seq_ = []
    for k, lg in enumerate(legs[first:]):
        p = ML._pt(lg, 0.0); nm = '%s_%02d' % (pre, k + 1); y_ = _yaw(_tan(lg))
        emp(nm, (p.x, p.y, 0.0), y_, {'kind': 'truck_pose', 'yaw_deg': y_, 'route': 'out (loaded)' if pre == 'Path_Out' else 'return (empty)', 's_m': round(s_, 3), 'next_leg': json.dumps(_leg_x(lg))})
        seq_.append({'name': nm, 'glTF': gl(p), 'yaw_deg': y_, 's_m': round(s_, 3), 'next_leg': _leg_x(lg)}); s_ += lg[3]
    pe = ML._pt(legs[-1], 1.0)
    if pre == 'Path_Out':
        nm = 'Path_Out_%02d' % (len(legs) - first + 1)
        emp(nm, (pe.x, pe.y, 0.0), 0.0, {'kind': 'truck_pose', 'yaw_deg': 0.0, 'route': 'out (loaded)', 's_m': round(s_, 3), 'note': last,
                                         'next_leg': json.dumps({'type': 'handoff', 'to': 'haul_road_seg strip, inbound lane glTF z 9, heading +X (x 26 -> Refinery x -46)'})})
        seq_.append({'name': nm, 'glTF': gl(pe), 'yaw_deg': 0.0, 's_m': round(s_, 3)})
    HAUL[pre] = {'markers': seq_, 'length_m': round(s_, 3), 'time_s_at_8.33': round(s_ / SPEED, 2)}
import haul_times as HT                            # eased trip times (8.33 m/s straights, 4 m/s turns, accel 3 / brake 4 m/s2)
_vl = lambda lg: HT.V_STRAIGHT if lg[0] == 'line' else HT.V_TURN
_tr, _lr = HT.trip([('Path_Ret_%02d' % (k + 1), lg[3], _vl(lg)) for k, lg in enumerate(ML.RET_LEGS)], v0=HT.V_STRAIGHT, v1=0.0)
_tv, _lv = HT.trip([('reverse Path_Load_Approach -> Path_Load', ML.REV, HT.V_REV)])
_to, _lo = HT.trip([('Path_Load', ML.OUT_LEGS[0][3], HT.V_STRAIGHT)] + [('Path_Out_%02d' % (k + 1), lg[3], _vl(lg)) for k, lg in enumerate(ML.OUT_LEGS[1:])], v0=0.0, v1=HT.V_STRAIGHT)
HAUL['times'] = {'model': '8.33 m/s straights, 4.0 m/s turns, accel 3.0 / brake 4.0 m/s2, reverse <= 3.0 m/s (haul_times.py)',
                 'return_s': round(_tr + _tv, 2), 'return_legs': [(n, round(t, 2)) for n, t, _, _ in _lr + _lv],
                 'out_s': round(_to, 2), 'out_legs': [(n, round(t, 2)) for n, t, _, _ in _lo]}
print(HT.fmt('RETURN x26 -> Path_Load_Approach', _tr, _lr)); print(HT.fmt('REVERSE', _tv, _lv)); print(HT.fmt('OUT Path_Load -> x26', _to, _lo))
print('HAUL', json.dumps(HAUL))
# deposits + spur (scoop) poses
for nm, (x, y), r, lab in (('Dep_01', ML.DEP1, 2.2, 'main He-3 seam'), ('Dep_02', ML.DEP2, 1.05, 'tap deposit')):
    emp(nm, (x, y, H(x, y)), 0, {'kind': 'deposit', 'label': lab, 'radius_m': r, 'tap': 'the drill taps it: the next load comes down the chute rich -> play truck_load_rich at Path_Load', 'patch': 'dep_patch in Base_Paint: still, darker ore rock (#3f3d3b) + dep_vein faint cyan veins in Base_DepVein (SHM_DepVein, low steady emissive)', 'glow': 'baked in the GLB only: faint steady cyan veins, no animation / pulse / flicker, no ring or disc; the game draws nothing extra here'})
emp('Road_Entry', (ML.ROAD_ENTRY[0], ML.ROAD_ENTRY[1], 0.0), 0, {'kind': 'road_entry', 'note': 'where the return U-turn joins the outbound lane (= Path_Out_01 = Path_Load_Approach): the loaded lane runs dead straight +X (glTF) at z 9 off the right edge to x 26 (Refinery road strip). The empty return lane comes in at z 0 (Path_Ret_01, x 26).'})
CREW = [(-9.4, -0.2, 0.64), (-9.0, -1.9, 0.05), (-5.6, -2.7, 0.0), (-2.2, -2.3, 0.0), (1.0, -1.6, 0.0), (5.0, 0.2, 0.0), (8.6, 2.9, 0.0)]
for i, p in enumerate(CREW): emp('Crew_Path_%02d' % (i + 1), (p[0], p[1], p[2] if p[2] > 0.3 else H(p[0], p[1])), 0, {'kind': 'crew_path'})

# ---------------- export: the Mine GLB (no truck) and the shared HT-04 prop GLB (art/3d/props/ht04/ht04_game.glb, packed separately)
TRUCK_OBJS = [arm, tm, FA]
TOUT = A.get('tout', os.path.join(os.path.dirname(MOUT), 'ht04_raw.glb'))
GLTF_KW = dict(export_format='GLB', use_selection=True, export_apply=False, export_yup=True, export_extras=True,
               export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True, export_optimize_animation_size=False,
               export_anim_slide_to_zero=True, export_def_bones=False, export_rest_position_armature=True,
               export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False, export_vertex_color='ACTIVE',
               export_all_vertex_colors=False, export_skins=True, export_morph=True, export_morph_normal=True, export_morph_animation=False, export_texcoords=False)
TRUCK_TRIS = tris([tm])
bpy.ops.object.select_all(action='DESELECT')
for o in col.objects: o.select_set(o not in TRUCK_OBJS)
os.makedirs(os.path.dirname(MOUT), exist_ok=True)
_tr = [t for t in arm.animation_data.nla_tracks]                 # keep the truck clips off the Mine export
for t in _tr: arm.animation_data.nla_tracks.remove(t)
_truck_acts = ('truck_dump', 'truck_drive', 'chute_pour', 'truck_load_rich')
_saved = dict(BAKED)
bpy.ops.export_scene.gltf(filepath=MOUT, **GLTF_KW)
for n in _truck_acts:
    tr_ = arm.animation_data.nla_tracks.new(); tr_.name = n; tr_.strips.new(n, 0, _saved[n]); tr_.mute = True
# HT-04 prop: root 'Truck' at the origin = ground centre under the truck, forward +X (glTF yaw 0), up +Y
arm.parent = None; arm.matrix_world = Matrix.Identity(4); bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for o in TRUCK_OBJS: o.select_set(True)
arm['prop'] = 'HT-04 haul truck (shared Mine / Refinery prop)'; arm['origin'] = 'ground centre under the truck (between the axle groups), +X forward = yaw 0, +Y up'
arm['place'] = 'copy a truck_pose marker (Path_Load, Path_Load_Approach, Path_XX, Road_Entry ...): position = marker position, rotation = marker rotation (yaw about +Y)'
arm['fill_morph'] = tm['fill_morph']
_wg = {tm.vertex_groups[n].index: i for i, n in enumerate(WHEELN)}; _rr = []
for v in tm.data.vertices:
    for g in v.groups:
        if g.group in _wg and g.weight > 0.5: x_, _y = AX[_wg[g.group]]; _rr.append(math.hypot(v.co.x - x_, v.co.z - ML.WR))
WHEEL_R = round(max(_rr), 3); arm['wheel_radius'] = WHEEL_R; arm['wheel_axle_height'] = ML.WR
arm['wheels'] = 'HT04_Wheel_FL/FR (front axle x +2.4), HT04_Wheel_ML/MR (x -1.35), HT04_Wheel_RL/RR (x -2.7); track +-1.5 m; spin axis = joint local +X (points to the truck left, glTF -Z); forward roll = +angle, angle = distance / wheel_radius; no clip animates the wheels'
print('WHEEL_R', WHEEL_R, 'axle z', ML.WR, 'min tread r', round(min(_rr), 3))
bpy.ops.export_scene.gltf(filepath=TOUT, **GLTF_KW)
print('TRUCK RAW', TOUT, os.path.getsize(TOUT), 'TRIS', TRUCK_TRIS)
INFO = {'W': W, 'cam_target': list(CAM_T), 'cam_target_glTF': gl(CAM_T), 'cam_d': CAM_D, 'fit_box_px': FIT_BOX, 'tris': {o.name: tris([o]) for o in col.objects if o.type == 'MESH' and o != tm}, 'truck_tris': TRUCK_TRIS, 'truck_raw': TOUT,
        'clearance': REPORT, 'haul': HAUL, 'load': {'heap_base': list(HEAP_C), 'heap_h': HEAP_H, 'chute_mouth_z': CHUTE_Z, 'fill_morph': FILL_INFO},
        'markers': {o.name: {'glTF_pos': gl(o.location), 'yaw_deg': round(math.degrees(o.rotation_euler.z), 2), 'extras': {k: (v if isinstance(v, (int, float, str)) else list(v)) for k, v in o.items()}}
                    for o in col.objects if o.type == 'EMPTY' and o != root}}
json.dump(INFO, open(MOUT.replace('.glb', '_info.json'), 'w'), indent=1, default=str)
if A.get('blend'): bpy.ops.wm.save_as_mainfile(filepath=A['blend'], compress=True)
print('RAW', MOUT, os.path.getsize(MOUT), 'TRIS', sum(INFO['tris'].values()))
