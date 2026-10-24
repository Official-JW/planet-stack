"""Planet Stack - crew boarding: build Art Assistant 2's pass-3 suit (local copy crew_pass3.py, snapshot md5 8016ecce...)
in the neutral 'stand' pose, split it into rigid bone groups, decimate each group to a game budget and dump the
triangles + rig joint positions to an .npz for build_boarding.py (pure numpy GLB writer).
blender -b -P extract_suit.py -- --variant A --out /tmp/suit_A.npz [--scale 1.0]
Coordinates are converted to glTF (x, z, -y): the suit faces +Z, feet on y = 0."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', '..', 'mine_concepts', '_src'))); sys.path.insert(0, HERE)
import bpy, bmesh, numpy as np
from mathutils import Vector
import mc_common
import crew_pass3 as CR

A = {}; av = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
for i in range(0, len(av), 2): A[av[i].lstrip('-')] = av[i + 1]
VAR = A.get('variant', 'A'); OUT = A.get('out', '/tmp/suit_%s.npz' % VAR); SCALE = float(A.get('budget', 1.0))
mc_common.reset()
root = CR.crew_member((0, 0, 0), 0.0, VAR, 'stand', name='Crew')
bpy.context.view_layer.update()

# ---------------- rig joint positions (same formulas as crew_member, 'stand' pose)
P = CR.suit_params(VAR); po = CR.POSES['stand']; h = P['h']
hipz = 0.935 * h; thigh, shin = 0.43 * h, 0.425 * h; legs = {}
for s in (1, -1):
    pt, bend = po['legs'][s]; hip = Vector((s * P['hip_w'], 0, hipz)); knee = hip + CR._limb_dir(pt) * thigh
    ank = knee + CR._limb_dir(pt - bend) * shin; legs[s] = [hip, knee, ank]
dz = -(min(l[2].z for l in legs.values()) - 0.082 * h)
for s in legs: legs[s] = [v + Vector((0, 0, dz)) for v in legs[s]]
org = Vector((0, 0, hipz + dz)); T = lambda z: (z - 0.935) * h
J = {'Root': Vector((0, 0, 0)), 'Hips': org.copy(), 'Spine': org + Vector((0, 0, T(1.07))), 'Chest': org + Vector((0, 0, T(1.2))),
     'Neck': org + Vector((0, 0, T(1.47))), 'Head': org + Vector((0, 0, T(1.475) + 0.06))}
HEADC = org + Vector((0, 0, T(1.475) + 0.168))
for s, sn in ((1, 'L'), (-1, 'R')):       # crew faces -Y (Blender) = +Z (glTF); +X is the crew's LEFT
    pt, ab, el = po['arms'][s]; sh = org + Vector((0, 0, T(1.415))) + Vector((s * P['sh_w'], 0, 0))
    ua = CR._limb_dir(pt, ab, s); elb = sh + ua * 0.3 * h; fa = CR._limb_dir(pt + el, ab * 0.6, s); hand = elb + fa * 0.255 * h
    J['UpperArm_' + sn] = sh; J['Forearm_' + sn] = elb; J['Hand_' + sn] = hand
    J['Thigh_' + sn], J['Shin_' + sn], J['Foot_' + sn] = legs[s]
    J['Toe_' + sn] = Vector((legs[s][2].x, legs[s][2].y - 0.26, 0.0))     # ball/toe marker (not a joint)
print('JOINTS', {k: tuple(round(c, 3) for c in v) for k, v in J.items()})

# ---------------- part -> bone group
def base(n): return n.split('.')[0]
CHEST = ('CuirassCore', 'ChestPlate', 'RibPlate', 'ChestAccent', 'ChestInset', 'RibVent', 'SidePlate', 'SternumRidge', 'CollarPlate', 'BackPlate',
         'Collar', 'ChestUnit', 'ChestUnitFrame', 'ChestScreen', 'ChestButton', 'ChestDial', 'Backpack', 'BackpackCore', 'BackpackTop', 'BackpackFin',
         'BackpackLight', 'BackpackBase', 'BackpackTank', 'BackpackTankCap', 'BackpackTankCapLow', 'BackpackTankBand', 'BackpackTankBand2', 'HarnessStrap', 'Hose')
HIPS = ('Belt', 'BeltTrim', 'BeltTrimLow', 'FauldFront', 'FauldFrontInner', 'Codpiece', 'CodpieceInset', 'RearPlate', 'RearPlateInner', 'HipPlate', 'HipPlateTrim', 'HipPlateLow', 'HipStripe')
UARM = ('ShoulderJoint', 'UpperArm', 'BicepPlate', 'PauldronUnder', 'Pauldron', 'PauldronLame', 'PauldronStripe')
FARM = ('Elbow', 'ElbowCop', 'Forearm', 'Gauntlet', 'GauntletLow', 'WristLight', 'Cuff')
THIGH = ('Thigh', 'ThighPlate', 'ThighPlateLow', 'ThighStripe', 'HamPlate')
SHIN = ('KneeJoint', 'KneeCap', 'KneeCapInlay', 'KneeSide', 'Shin', 'ShinGuard', 'ShinGuardLow', 'CalfPlate', 'BootShaft', 'BootCuff', 'BootCuffStripe')
def group_of(ob, cen):
    b = base(ob.name); sn = 'L' if cen.x > 0 else 'R'
    if ob.parent and base(ob.parent.name) == 'HelmetPivot': return 'Head'
    if b in ('NeckSeal', 'NeckSealRing', 'NeckSealLip'): return 'Neck'
    if b == 'TorsoUnder': return 'TorsoBlend'
    if b in CHEST: return 'Chest'
    if b == 'AbPlate': return 'Spine'
    if b in HIPS: return 'Hips'
    if b in UARM: return 'UpperArm_' + sn
    if b in FARM: return 'Forearm_' + sn
    if b.startswith('Glove'): return 'Hand_' + sn
    if b in THIGH: return 'Thigh_' + sn
    if b in SHIN: return 'Shin_' + sn
    if b.startswith('Boot'): return 'Foot_' + sn
    raise RuntimeError('unassigned part ' + ob.name)

CLS = {'C_SuitShell': 0, 'C_SuitGraphite': 1, 'C_SuitUnder': 2, 'C_Visor': 3, 'C_Accent_cyan': 4, 'C_Accent_pink': 4, 'C_CyanGlow': 5, 'C_PinkGlow': 5}
BUDGET = {'Head': 520, 'Neck': 60, 'TorsoBlend': 260, 'Chest': 900, 'Spine': 80, 'Hips': 220,
          'UpperArm': 170, 'Forearm': 150, 'Hand': 150, 'Thigh': 150, 'Shin': 190, 'Foot': 170}
dg = bpy.context.evaluated_depsgraph_get()
groups = {}
for ob in root.children_recursive:
    if ob.type != 'MESH': continue
    oe = ob.evaluated_get(dg); me = bpy.data.meshes.new_from_object(oe)
    me.transform(ob.matrix_world)
    cen = sum((v.co for v in me.vertices), Vector()) / max(1, len(me.vertices))
    g = group_of(ob, cen)
    cls = CLS[ob.material_slots[0].material.name.split('.')[0]] if ob.material_slots else 1
    groups.setdefault(g, []).append((me, cls))

out = {'P': [], 'N': [], 'C': [], 'G': []}; gnames = sorted(groups); stats = {}
for gi, g in enumerate(gnames):
    bm = bmesh.new()
    for me, cls in groups[g]:
        n0 = len(bm.faces); bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[n0:]: f.material_index = cls
        bpy.data.meshes.remove(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0004)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    me = bpy.data.meshes.new('G_' + g); bm.to_mesh(me); bm.free()
    for i in range(6): me.materials.append(None)
    ob = bpy.data.objects.new('G_' + g, me); bpy.context.scene.collection.objects.link(ob)
    n_raw = len(me.polygons); tgt = BUDGET[g.split('_')[0]] * SCALE
    if n_raw > tgt:
        md = ob.modifiers.new('Dec', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = tgt / n_raw; md.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get(); m2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bm = bmesh.new(); bm.from_mesh(m2); bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(m2); bm.free()
    for p in m2.polygons: p.use_smooth = True
    m2.set_sharp_from_angle(angle=math.radians(42))
    cn = np.zeros(len(m2.loops) * 3, np.float32); m2.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
    co = np.zeros(len(m2.vertices) * 3, np.float32); m2.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    lv = np.zeros(len(m2.loops), np.int32); m2.loops.foreach_get('vertex_index', lv)
    mi = np.zeros(len(m2.polygons), np.int32); m2.polygons.foreach_get('material_index', mi)
    tri_cls = np.repeat(mi, 3)
    out['P'].append(co[lv]); out['N'].append(cn); out['C'].append(tri_cls); out['G'].append(np.full(len(lv), gi, np.int32))
    stats[g] = (n_raw, len(m2.polygons))
cat = {k: np.concatenate(v) for k, v in out.items()}
cv = lambda a: np.stack([a[:, 0], a[:, 2], -a[:, 1]], 1)     # Blender -> glTF
jn = sorted(J); jp = np.array([cv(np.array([J[k]]))[0] for k in jn], np.float32)
np.savez(OUT, P=cv(cat['P']), N=cv(cat['N']), C=cat['C'], G=cat['G'], gnames=np.array(gnames), jnames=np.array(jn), jpos=jp,
         headc=cv(np.array([HEADC]))[0], height=np.float32(h))
print('STATS', stats, 'total tris', sum(v[1] for v in stats.values()), 'raw', sum(v[0] for v in stats.values()))
