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
C0, C1, Lc, U, SIDE, UP = LAY['C0'], LAY['C1'], LAY['L'], LAY['u'], LAY['side'], LAY['up']
base = lambda o: o.name.split('.')[0]
TROOT = bpy.data.objects['Truck_HT04']; GZ = TROOT.matrix_world.translation.z
TORG = Vector((ML.TX, ML.TY, GZ))          # truck-local origin in world

# ---------------------------------------------------------------- camera (Game Coder spec)
FOV_Y, PITCH, PW, PH = 38.0, 18.0, 393, 852
CY = float(A.get('cy', 380))     # focus-box centre on 393x852 (Mine + Refinery footprint; 380 keeps Mine Tier_20 on top and the Refinery front above y 650)
TAN_H = math.tan(math.radians(FOV_Y / 2)) * PW / PH
def cam_pose(tgt, W):
    d = (W / 2) / TAN_H; p = math.radians(PITCH)
    pos = Vector(tgt) + Vector((0, -d * math.cos(p), d * math.sin(p)))
    return pos, d
def focus_points():
    P = []
    rig = ('pad', 'strut_foot', 'leg', 'leg_foot', 'crown', 'ant_tip', 'beacon', 'op_pod', 'power', 'cyclone')
    head = ('head_housing', 'dis_chute', 'head_col', 'head_col_foot')
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        b = base(o)
        if b in rig or b in head or o.parent == TROOT or (o.parent and o.parent.parent == TROOT):
            P += [o.matrix_world @ Vector(c) for c in o.bound_box]
    rx, ry = ML.REFINERY[0], ML.REFINERY[1]     # intake bin envelope (refinery side, ~3 x 3 m, 3 m tall incl. hood)
    for dx in (-1.6, 1.6):
        for dy in (-1.6, 1.6):
            for z in (0, 3.0): P.append(Vector((rx + dx, ry + dy, z)))
    # Refinery (Director ruling 10/23: the station camera frames the rig and the Refinery together, every tier in frame).
    # Convex-hull points of refinery_game.glb (all tiers), refinery-local Blender coords, placed at REFINERY_ANCHOR (+90 deg about Z).
    RHULL = [(-2.6, 1.26, -0.1), (2.3, 1.26, -0.1), (2.3, -1.24, -0.1), (-8.5, 0.71, -0.1), (-29.99, -2.07, 0.06), (-29.9, -24.43, 0.06), (-19.15, -24.64, -0.08), (-19.15, -0.58, 0.06), (-11.84, -24.73, 0.18), (-1.92, 1.48, 1.39), (2.1, -1.02, 4.01), (-2.02, 1.49, 3.79), (2.02, 1.49, 4.01), (-8.25, -1.04, 8.35), (-6.95, -2.04, 8.35), (-27.77, -2.62, 2.85), (-33.2, -12.24, -0), (-26.56, -2.26, 3.86), (-7.04, 1.03, 0.56), (-19.25, -14.34, -0.1), (-22.65, -14.34, -0.1), (-22.65, -4.24, -0.1), (-21.03, -25.44, 8.6), (-29.28, -25.06, 2.15), (-24.8, -22.76, 14.09), (-12.98, -24.08, 5.1), (-13.67, -23.34, 6.67)]
    for hx, hy, hz in RHULL: P.append(Vector((rx - hy, ry + hx, hz)))
    for x, y in ((9.0 + 4.5 + ML.ROAD_W / 2, -9.0), (9.0, -13.5 - ML.BERM_OUT), (-5.0, -13.5 - ML.BERM_OUT), (13.0, -4.0)):
        P.append(Vector((x, y, 0.0)))   # haul loop: graded edge at the east apex (the berm is open there: access road), south berm toes
    for o in bpy.data.objects:                       # silo + beacon tops stay in frame
        if o.type == 'MESH' and 'silo' in base(o).lower(): P += [o.matrix_world @ Vector(c) for c in o.bound_box]
    return P
def cam_fit():
    from bpy_extras.object_utils import world_to_camera_view
    cd = bpy.data.cameras.new('FitCam'); cam = bpy.data.objects.new('FitCam', cd); bpy.context.scene.collection.objects.link(cam)
    cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(FOV_Y); cd.clip_end = 3000
    sc.render.resolution_x, sc.render.resolution_y = PW, PH
    P = focus_points(); best = None
    for W in ([float(A['w'])] if 'w' in A else [30 + 0.5 * i for i in range(21)]):
        tgt = Vector((-2.5, -1.0, 4.0))
        for it in range(12):
            pos, d = cam_pose(tgt, W); cam.location = pos
            cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler(); bpy.context.view_layer.update()
            pr = [world_to_camera_view(sc, cam, p) for p in P]
            xs = [q.x * PW for q in pr]; ys = [(1 - q.y) * PH for q in pr]
            mx = (min(xs) + max(xs)) / 2; my = (min(ys) + max(ys)) / 2
            tgt.x += (mx - PW / 2) / PW * W
            tgt.z -= (my - CY) / PW * W / math.cos(math.radians(PITCH))
        ok = min(xs) >= 0.04 * PW and max(xs) <= 0.96 * PW and min(ys) >= 100 and max(ys) <= 650
        print('FIT W', W, 'x', round(min(xs)), round(max(xs)), 'y', round(min(ys)), round(max(ys)), ok)
        if ok: best = (W, tgt.copy(), d, (min(xs), max(xs), min(ys), max(ys))); break
    bpy.data.objects.remove(cam, do_unlink=True)
    return best
FIT = cam_fit(); W, CAM_T, CAM_D, FIT_BOX = FIT
CAM_T = Vector((round(CAM_T.x, 2), round(CAM_T.y, 2), round(CAM_T.z, 2)))
print('CAMFIT W=%.1f target=%s d=%.2f box=%s' % (W, tuple(CAM_T), CAM_D, tuple(round(v) for v in FIT_BOX)))

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
MAP = [('B_WhiteSmooth', 'SH_White'), ('B_White', 'SH_White'), ('B_GraphiteSmooth', 'SH_Graphite'), ('B_Graphite', 'SH_Graphite'),
       ('B_Satin', 'SH_Steel'), ('B_Platinum', 'SH_Steel'), ('B_Tire', 'SH_Graphite'), ('B_Belt', 'SH_Graphite'), ('B_InkWhite', 'SH_White'),
       ('B_Ink', 'SH_Graphite'), ('B_CyanSoft', 'SH_GlowCyan'), ('B_Cyan', 'SH_GlowCyan'), ('B_He3', 'SH_GlowCyan'), ('B_Lamp', 'SH_GlowWhite'),
       ('B_PlasmaCore', 'SH_GlowWhite'), ('B_Melt', 'SH_GlowWhite'), ('B_Visor', 'SH_Glass'), ('B_OreRock', 'SH_Rock'), ('B_HaulRoad', 'SH_Graphite'),
       ('B_Radiator', 'SH_Radiator'), ('M_Regolith', 'SH_Rock')]
TIRE_COL = lin('#24272b')
def shared_for(m):
    sw = None
    if m is not None:
        for p, s_ in MAP:
            if m.name.startswith(p): sw = s_; break
    if sw is None: sw = 'SH_Graphite'; print('UNMAPPED', m.name if m else None)
    mm = S2M[sw]
    col = lin(SW[sw]['base']) if MERGED[mm].get('vertex_colors') else lin(MERGED[mm]['base'])
    if m is not None and m.name.startswith('B_Tire'): col = TIRE_COL
    return SH[mm], col

# ---------------- groups
RIG = {'carriage', 'carriage_strip', 'bore_housing', 'bore_glow', 'bore_band', 'bore_window', 'bore_window_frame', 'nozzle', 'nozzle_glow', 'plasma_core'}
SILO = {'silo', 'silo_plinth', 'silo_band', 'silo_glow', 'silo_hatch', 'spine', 'fill_window_bg', 'fill_level', 'silo_beacon'}
DROP = ('decal', 'lug', 'ejecta', 'fall_ore', 'belt_ore', 'umbilical', 'arm_hose', 'cab_whip', 'plasma_halo', 'fill_tick', 'step', 'power_cable',
        'bed_ore', 'hop_he3', 'hop_rock', 'hop_pt', 'spill', 'melt_pool', 'leg_band', 'power_fin', 'grouser', 'flood_lens', 'dish_post', 'axle',
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
SH_T = ML.SH_T
def ik(S, Tg, l1, l2, upv=Vector((0, 0, 1))):
    dv = Tg - S; D = min(dv.length, l1 + l2 - 1e-3); dn = dv.normalized()
    a = (l1 * l1 - l2 * l2 + D * D) / (2 * D); h = math.sqrt(max(0.0, l1 * l1 - a * a))
    n = (upv - dn * upv.dot(dn)).normalized()
    return S + dn * a + n * h, S + dn * D
EL_S, WR_S = ik(SH_T, ML.STOW_WRIST_T, ML.L1, ML.L2)
AX = [(x, sy * 1.5) for sy in (1, -1) for x in ML.AXLES]   # Wheel_01..03 left (+Y) rear->front, 04..06 right (-Y) rear->front
def seg_dist(p, a, b):
    ab = b - a; t = max(0, min(1, (p - a).dot(ab) / ab.length_squared)); return (a + ab * t - p).length
def truck_bone(o, cl):
    b = base(o)
    if b in ('tire', 'rim', 'hub', 'hub_glow', 'hub_cap'):
        k = min(range(6), key=lambda i: (cl.x - AX[i][0]) ** 2 + (cl.y - AX[i][1]) ** 2); return 'Truck_Wheel_%02d' % (k + 1)
    if b.startswith('Ram'):
        side = 'R' if b[3] == 'L' else 'L'      # concept 'RamL' sits at -Y = the truck's right
        if 'Stage2' in b: return 'Truck_Ram_%s_Stage2' % side
        if 'Rod' in b: return 'Truck_Ram_%s_Rod' % side
        return 'Truck_Ram_%s' % side
    if b == 'bed_heap': return 'Truck_Load'
    if o.parent and base(o.parent) == 'Bed_Pivot': return 'Truck_Bed'
    if b.startswith('scoop'): return 'Truck_Arm_Scoop'
    if b in ('arm_elbow', 'arm_fore', 'arm_wrist'): return 'Truck_Arm_Fore'
    if b == 'arm_strip': return 'Truck_Arm' if seg_dist(cl, SH_T, EL_S) < seg_dist(cl, EL_S, WR_S) else 'Truck_Arm_Fore'
    if b.startswith(('arm_upper', 'arm_shoulder', 'arm_ram')): return 'Truck_Arm'
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

def tris(objs): return sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
for g, objs in groups.items():
    for o in objs:
        if o.get('road'): continue            # roads keep their profile columns (tyre marks / berms) - no planar dissolve
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.004)
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(4), verts=bm.verts, edges=bm.edges, delimit={'MATERIAL'})
        bm.to_mesh(o.data); bm.free()
T1 = {g: tris(o) for g, o in groups.items()}; print('TRIS after planar', T1, sum(T1.values()))
BUD = {'Truck': int(A.get('truck', 6000)), 'Rig': 650, 'Conveyor': 300, 'Silo': 800,
       'Tier_03': 260, 'Tier_05': 1400, 'Tier_08': 320, 'Tier_12': 700, 'Tier_20': 420}
BUD['Base'] = TARGET - sum(min(BUD[g], T1[g]) for g in T1 if g != 'Base')
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
        tt = tris(objs); r = min(1.0, BUD['Truck'] / tt); parts = []
        for bname, os_ in byb.items():
            j = join(os_) if len(os_) > 1 else os_[0]
            if tris([j]) > 60: decimate(j, max(40, int(tris([j]) * r)))
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
BONES += [('Truck_Arm', 'Truck_Chassis', SH_T.copy()), ('Truck_Arm_Fore', 'Truck_Arm', EL_S.copy()), ('Truck_Arm_Scoop', 'Truck_Arm_Fore', WR_S.copy())]
for i, (x, y) in enumerate(AX): BONES.append(('Truck_Wheel_%02d' % (i + 1), 'Truck_Chassis', Vector((x, y, ML.WR))))
for n, par, h in BONES:
    eb = ad.edit_bones.new(n); eb.head = h; eb.tail = h + Vector((0, 0, 0.3)); eb.roll = 0.0
    if par: eb.parent = ad.edit_bones[par]; eb.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
tm.parent = arm; tm.matrix_parent_inverse = Matrix.Identity(4); tm.location = (0, 0, 0)
mod = tm.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
for n, _, _ in BONES:
    if n not in tm.vertex_groups: tm.vertex_groups.new(name=n)    # empty groups keep joint order stable
tm.name = 'Truck_Mesh'
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
def scoop_R(EL, WR, k):
    fdir = (WR - EL).normalized(); sdir = (fdir + Vector((0, 0, k))).normalized()
    return frame_from(WR, WR + sdir)[3]
R_U0 = frame_from(SH_T, EL_S)[3]; R_F0 = frame_from(EL_S, WR_S)[3]; R_S0 = scoop_R(EL_S, WR_S, -0.25)
def arm_G(P, k):
    EL, WR = ik(SH_T, P, ML.L1, ML.L2)
    Gu = about(SH_T, frame_from(SH_T, EL)[3] @ R_U0.transposed())
    Gf = Tm(EL) @ (frame_from(EL, WR)[3] @ R_F0.transposed()).to_4x4() @ Tm(-EL_S)
    Gs = Tm(WR) @ (scoop_R(EL, WR, k) @ R_S0.transposed()).to_4x4() @ Tm(-WR_S)
    return Gu, Gf, Gs, EL, WR
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
REACH = ML.REACH_WRIST_T
def scoop_pose(f):
    """36 frames @30fps = 1.2 s: 0-14 reach out+down, 14-20 curl (scoop fills), 20-36 back to stow (ends on rest)."""
    if f <= 14:
        t = ease(f / 14); P = WR_S.lerp(REACH, t) + Vector((0, 0, 0.55 * math.sin(math.pi * t))); k = -0.25 + (-0.9 + 0.25) * t
    elif f <= 20:
        t = ease((f - 14) / 6); P = REACH + Vector((0, 0, 0.25 * t)); k = -0.9 + 1.15 * t
    else:
        t = ease((f - 20) / 16); P = (REACH + Vector((0, 0, 0.25))).lerp(WR_S, t) + Vector((0, 0, 0.55 * math.sin(math.pi * t))); k = 0.25 + (-0.25 - 0.25) * t
    Gu, Gf, Gs, EL, WR = arm_G(P, k)
    return {'Truck_Arm': Gu, 'Truck_Arm_Fore': Gf, 'Truck_Arm_Scoop': Gs}

# ---------------- clearance checks, played on the real skinned mesh
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
REPORT = {}
is_arm = lambda b: b.startswith('Truck_Arm')
for deg in (0, 25, 50):
    a = math.radians(deg); G = {'Truck_Bed': bed_G(a), 'Truck_Load': load_G(a, 1.0)}
    for s in ('L', 'R'):
        Gb, G2, G3 = ram_G(s, a); G['Truck_Ram_%s' % s] = Gb; G['Truck_Ram_%s_Stage2' % s] = G2; G['Truck_Ram_%s_Rod' % s] = G3
    rest_pose(); pose(G)
    arm_p, _ = eval_parts(is_arm)
    bed_p, _ = eval_parts(lambda b: b in ('Truck_Bed', 'Truck_Load'))
    n, md, pr = overlap(arm_p, bed_p)
    REPORT['stow_vs_bed_%d' % deg] = {'overlaps': n, 'min_gap_m': round(md, 3)}
    print('CLEAR stow vs bed @%ddeg overlaps=%d min_gap=%.3f' % (deg, n, md))
worst = []
# the shoulder ball sits in the chassis turret by design: arm faces whose centroid is within 0.4 m of the shoulder are the joint, not a clip
for f in range(0, 37, 2):
    rest_pose(); pose(scoop_pose(f))
    arm_p, oth = eval_parts(is_arm)
    tb = BVHTree.FromPolygons(oth[0], oth[1]); hits = {}; md = 99.0; mdq = None
    for pi, p in enumerate(arm_p[1]):               # sample every arm face; skip samples within 0.45 m of the shoulder (joint)
        vv = [arm_p[0][k] for k in p]
        for (w0, w1) in ((0.33, 0.33), (0.1, 0.1), (0.8, 0.1), (0.1, 0.8), (0.5, 0.0), (0.0, 0.5), (0.5, 0.5)):
            q = vv[0] * (1 - w0 - w1) + vv[1] * w0 + vv[2] * w1
            if (q - SH_T).length < 0.45: continue
            loc, nrm, j, dist = tb.find_nearest(q)
            if loc is None: continue
            inside = (q - loc).dot(nrm) < 0 and dist < 0.15
            if dist < md: md = dist; mdq = (tuple(round(c, 2) for c in q), arm_p[2][pi], oth[2][j])
            if inside or dist < 0.005:
                k = '%s|%s' % (arm_p[2][pi], oth[2][j]); hits[k] = hits.get(k, 0) + 1
    n, pr = sum(hits.values()), hits
    lo = min(v.z for v in arm_p[0])
    worst.append((f, n, round(md, 3), round(lo, 2), pr, mdq))
print('CLEAR scoop frames (frame, overlaps, min gap m, lowest arm z):', worst)
REPORT['scoop'] = worst
rest_pose()

# ---------------- clips
sc.render.fps = 30
def bake(clip, frames, fn, bones):
    act = bpy.data.actions.new(clip); arm.animation_data_create(); arm.animation_data.action = act
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
bake('truck_scoop', list(range(0, 37)), scoop_pose, ['Truck_Arm', 'Truck_Arm_Fore', 'Truck_Arm_Scoop'])
bake('truck_drive', list(range(0, 31)), lambda f: {('Truck_Wheel_%02d' % (i + 1)): wheel_G(i, math.tau * f / 30) for i in range(6)}, ['Truck_Wheel_%02d' % (i + 1) for i in range(6)])
bake('truck_load', list(range(0, 25)), lambda f: {'Truck_Load': load_G(0.0, max(0.02, ease(f / 24)))}, ['Truck_Load'])
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
emp('Path_Load', ML.LOAD, 0, {'kind': 'truck_pose', 'yaw_deg': 0, 'chute_glTF': gl((DIS.x, DIS.y, 4.35))})
emp('Path_Dump_Approach', ML.DUMP_APPROACH, 0, {'kind': 'truck_pose', 'yaw_deg': 0, 'note': 'stop, then reverse 4 m along -X(glTF) to Path_Dump'})
emp('Path_Dump', ML.DUMP, 0, {'kind': 'truck_pose', 'yaw_deg': 0, 'note': 'truck rear faces REFINERY_ANCHOR; play truck_dump here'})
emp('REFINERY_ANCHOR', (ML.REFINERY[0], ML.REFINERY[1], 0.0), ML.REFINERY[2], {'kind': 'refinery_origin', 'intake_front_offset_m': 1.2,
    'note': 'Refinery GLB origin; local +Z(glTF) points at the truck (truck heading at Path_Dump = +X glTF)'})
# haul loop way-points in driving order: Path_Load -> east hairpin -> south straight -> west hairpin -> Path_Dump_Approach
lp = ML.loop_points(0.25); n = len(lp)
def yaw_at(i): t = lp[(i + 1) % n] - lp[i - 1]; return math.degrees(math.atan2(t.y, t.x))
i0 = min(range(n), key=lambda i: (lp[i] - Vector((ML.TX + 0.0, ML.TY, 0))).length)
seq = [lp[(i0 + k) % n] for k in range(n)]; idx = [(i0 + k) % n for k in range(n)]
s_acc, picks, last = 0.0, [], None
end = min(range(n), key=lambda k: (seq[k] - Vector(ML.DUMP_APPROACH)).length)
for k in range(1, end):
    if last is None or (seq[k] - last).length >= 3.0: picks.append(k); last = seq[k]
PATHS = []
for j, k in enumerate(picks):
    p = seq[k]; e = emp('Path_%02d' % (j + 1), (p.x, p.y, 0.0), yaw_at(idx[k]), {'kind': 'truck_pose', 'yaw_deg': round(yaw_at(idx[k]), 1)}); PATHS.append(e)
# deposits + spur (scoop) poses
for nm, (x, y), r, park, lab in (('Dep_01', ML.DEP1, 2.2, ML.DEP1_PARK, 'main He-3 seam'), ('Dep_02', ML.DEP2, 1.05, ML.DEP2_PARK, 'tap deposit')):
    emp(nm, (x, y, H(x, y)), 0, {'kind': 'deposit', 'label': lab, 'radius_m': r, 'scoop_from': 'Path_Spur_%s' % nm[-2:], 'glow': 'drawn by the game (no deposit mesh in the GLB; clear ground within 2.5 m)'})
emp('Path_Spur_01', (ML.DEP1_PARK[0], ML.DEP1_PARK[1], 0.0), ML.DEP1_PARK[2], {'kind': 'truck_pose', 'yaw_deg': ML.DEP1_PARK[2], 'deposit': 'Dep_01', 'note': 'stop here, play truck_scoop (reaches to the truck right)'})
emp('Path_Spur_02', (ML.DEP2_PARK[0], ML.DEP2_PARK[1], 0.0), ML.DEP2_PARK[2], {'kind': 'truck_pose', 'yaw_deg': ML.DEP2_PARK[2], 'deposit': 'Dep_02', 'note': 'stop here, play truck_scoop (reaches to the truck right)'})
emp('Road_Entry', (13.5, -9.0, 0.0), -90, {'kind': 'road_entry', 'note': 'east apex of the haul loop; the graded access road (haul_road_access) joins here and leaves heading +Z (toward the camera)'})
CREW = [(-9.4, -0.2, 0.64), (-9.0, -1.9, 0.05), (-5.6, -2.7, 0.0), (-2.2, -2.3, 0.0), (1.6, 0.2, 0.0), (5.6, 1.0, 0.0), (8.6, 1.4, 0.0)]
for i, p in enumerate(CREW): emp('Crew_Path_%02d' % (i + 1), (p[0], p[1], p[2] if p[2] > 0.3 else H(p[0], p[1])), 0, {'kind': 'crew_path'})

# ---------------- export
for o in col.objects: o.select_set(False)
bpy.ops.object.select_all(action='DESELECT')
for o in col.objects: o.select_set(True)
os.makedirs(os.path.dirname(MOUT), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=MOUT, export_format='GLB', use_selection=True, export_apply=False, export_yup=True, export_extras=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True, export_optimize_animation_size=False,
                          export_anim_slide_to_zero=True, export_def_bones=False, export_rest_position_armature=True,
                          export_cameras=False, export_lights=False, export_draco_mesh_compression_enable=False, export_vertex_color='ACTIVE',
                          export_all_vertex_colors=False, export_skins=True, export_morph=False, export_texcoords=False)
INFO = {'W': W, 'cam_target': list(CAM_T), 'cam_target_glTF': gl(CAM_T), 'cam_d': CAM_D, 'fit_box_px': FIT_BOX, 'tris': {o.name: tris([o]) for o in col.objects if o.type == 'MESH'},
        'clearance': REPORT, 'stow_wrist_T': list(WR_S), 'stow_elbow_T': list(EL_S),
        'markers': {o.name: {'glTF_pos': gl(o.location), 'yaw_deg': round(math.degrees(o.rotation_euler.z), 2), 'extras': {k: (v if isinstance(v, (int, float, str)) else list(v)) for k, v in o.items()}}
                    for o in col.objects if o.type == 'EMPTY' and o != root}}
json.dump(INFO, open(MOUT.replace('.glb', '_info.json'), 'w'), indent=1, default=str)
if A.get('blend'): bpy.ops.wm.save_as_mainfile(filepath=A['blend'], compress=True)
print('RAW', MOUT, os.path.getsize(MOUT), 'TRIS', sum(INFO['tris'].values()))
