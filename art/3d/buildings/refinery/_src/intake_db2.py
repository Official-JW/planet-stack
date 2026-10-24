"""DB-2 dump bay + RB-2 intake upgrade (10/23 PM, Jacob: "upgrade the dump location and pre conveyor, keep everything else the same").
exec'd by build_refinery.py right after the DB-1 dump bay block (final station coords: origin = Truck_Dump, Blender Z up, camera on -Y,
truck reverses along +X, cab -X, rear into the hopper). Replaces ONLY: the dump bay (apron, paint, walls, wheel stop), the RB-1 bin,
its dust skirt / spray bar, the grizzly, the BF-1 belt feeder and pad_intake. Everything else (splitter SP-1 onward, the markers,
Dump_Dust, the Cam_Target, tiers) is untouched. Chain: HT-04 tips over the armoured lip -> grizzly (Intake_Grate) -> RB-2 hopper ->
AF-1 inclined apron feeder (+X) -> SZ-1 primary sizer (flywheel = node Sizer_Flywheel, clip sizer_spin) -> covered transfer chute ->
CV-0 tail (pulley housing + guards) -> CV-0 back up to the SP-1 splitter at the old BF-1 head point (4.6, 5.35, 1.8).
Nothing new on the haul road: every part sits at x >= 3.6 (the old bin line) or is flush paint on the apron (z <= 0.1)."""
_OLD = ('rb_', 'ds_', 'feeder_', 'fd_plate', 'st_rb_', 'st_fd_', 'db_', 'igr_', 'pad_intake')
_gone = 0
for _o in list(coll('Mine').all_objects):
    if _o.name.startswith(_OLD) and not _o.name.startswith('dust_puff'):
        bpy.data.objects.remove(_o, do_unlink=True); _gone += 1
print('DB2 removed old intake objects', _gone, flush=True)
V = Vector
ARMOR = P_('RF_ArmorSteel', '#7f8790', rough=0.34, metal=1.0, grime=0.38, grime_col='#4a4c50', wear=0.32, wear_col='#d6dbe0', bevel=0.012)
TYRE = P_('RF_TyreWear', '#8f8b84', dust=False, rough=0.92, metal=0.0, grime=0.5, grime_col='#6c6a66')
LENSA = M_paint('RF_LensAmber', '#8a5f17', rough=0.25, metal=0.0)
LENSR = M_paint('RF_LensRed', '#5e1d1b', rough=0.25, metal=0.0)
GRATE = P_('RF_GraphiteGrate', '#3a3f46', rough=0.4, metal=0.7, grime=0.3, grime_col='#6b6e72', wear=0.3, wear_col='#a5abb1', bevel=0.005)
CONC2 = P_('RF_Concrete', '#c8c4ba', rough=0.85, metal=0.0, grime=0.32, grime_col='#8e9094', wear=0.25, wear_col='#a9a59c') if False else CONC
BX0, BX1, BY, BRIM = 3.72, 6.2, 1.92, 1.40
def _v(*a): return V(a)

# ---------------------------------------------------------------- 1. approach apron (sloped concrete, joints, tyre wear, markings)
_bm = bmesh.new(); _AX0, _AX1, _AY = -2.0, 3.6, 2.8
def _az(x): return 0.05 + 0.04 * (x - _AX0) / (_AX1 - _AX0)       # rises 4 cm toward the stop (drains away from the hopper mouth)
_g = [[_bm.verts.new((_AX0 + (_AX1 - _AX0) * i / 16, -_AY + 2 * _AY * j / 8, 0.0)) for j in range(9)] for i in range(17)]
for i in range(16):
    for j in range(8): _bm.faces.new((_g[i][j], _g[i + 1][j], _g[i + 1][j + 1], _g[i][j + 1]))
for v in _bm.verts:
    edge = abs(v.co.x - _AX0) < 1e-6 or abs(abs(v.co.y) - _AY) < 1e-6
    v.co.z = 0.0 if edge else _az(v.co.x)
_obj(_bm, 'db_apron', CONC, c='Mine', smooth=False)
def decal(name, pts, mat, lift):   # flat single-sided paint quad(s) following the apron slope (no thin boxes: they flip under decimation)
    bm = bmesh.new()
    for poly in pts:
        vs = [bm.verts.new((x, y, _az(x) + lift)) for x, y in poly]; bm.faces.new(vs)
    return _obj(bm, name, mat, c='Mine', smooth=False)
def rect(cx, cy, sx, sy, a=0.0):
    c, s_ = math.cos(a), math.sin(a)
    return [(cx + c * dx - s_ * dy, cy + s_ * dx + c * dy) for dx, dy in ((-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2))]
decal('db_joint', [rect(_x, 0, 0.03, 2 * _AY - 0.5) for _x in (-0.6, 0.8, 2.2)] + [rect((_AX0 + _AX1) / 2, 0.0, _AX1 - _AX0 - 0.4, 0.03)], TYRE, 0.012)
_rs = random.Random(907); _tw = []
for _sy in (-1, 1):                                                                  # tyre-worn tracks (dual rears), patchy, non-overlapping
    for _k in range(7):
        _x0 = _AX0 + 0.25 + _k * 0.78
        _tw.append(rect(_x0 + 0.38, _sy * (1.12 + _rs.uniform(-0.05, 0.05)), 0.74, 0.62 + _rs.uniform(-0.08, 0.1), _rs.uniform(-0.02, 0.02)))
decal('db_tyrewear', _tw, TYRE, 0.024)
decal('db_paint_cyan', [rect(0.6, 0.0, 5.0, 0.09)], CYANS, 0.036)                  # cyan centre guide line (glow strip)
decal('db_paint_guide', [rect(0.75, _sy * 1.62, 5.2, 0.12) for _sy in (-1, 1)] + [rect(3.36, 0.0, 0.24, 3.4)], HAZ, 0.036)
decal('db_paint_edge', [rect(0.75, _sy * 2.55, 5.4, 0.08) for _sy in (-1, 1)], INKW, 0.036)
_ch = []
for _sy in (-1, 1):                                                                   # chevrons pointing into the bay (+X)
    for _x in (-1.4, -0.2, 1.0):
        _c = (_x, _sy * 2.08)
        for _m in (1, -1):
            _ch.append([(_c[0] + 0.26, _c[1]), (_c[0] + 0.26 - 0.2, _c[1]), (_c[0] - 0.24, _c[1] + _m * 0.3), (_c[0] - 0.04, _c[1] + _m * 0.3)][::(1 if _m == -1 else -1)])
decal('db_paint_chev', _ch, HAZ, 0.036)
_tip = text('db_paint_tip', 'TIP', (2.25, -2.12, _az(2.25) + 0.034), (0, 0, 0), 0.62, HAZ, extrude=0.002)
_tip = to_mesh(_tip); _tip.name = 'db_paint_tip'
_bay = text('db_paint_bay', 'BAY 1', (-1.25, -2.12, _az(-1.25) + 0.034), (0, 0, 0), 0.32, INKW, extrude=0.002)
_bay = to_mesh(_bay); _bay.name = 'st_db_bay'   # master only (game drops st_)
# ---------------------------------------------------------------- 2. wheel-stop curb + bump rail (same footprint as RB-1's: x 3.64..3.96)
box('rb2_wheelstop', (0.32, 3.3, 0.34), (3.80, 0, 0.17 + 0.06), CONC, bevel=0.04)
box('rb2_wheelstop_cap', (0.34, 3.32, 0.04), (3.80, 0, 0.42), ARMOR, bevel=0.01)
rod('rb2_bumprail', (3.6, -1.6, 0.27), (3.6, 1.6, 0.27), 0.065, ARMOR, segs=14)
for _y in (-1.45, -0.5, 0.5, 1.45): box('rb2_bumprail_mount', (0.1, 0.12, 0.16), (3.66, _y, 0.27), GRAPH2, bevel=0.01)
for _k in range(8):                                                                    # chevron blocks on the curb face
    box('db_paint_curbstripe', (0.012, 0.38, 0.12), (3.63, -1.47 + _k * 0.42, 0.13), HAZ if _k % 2 == 0 else GRAPH, bevel=0.0)
for _sy in (-1, 1): box('rb2_wheelstop_cyan', (0.33, 0.45, 0.02), (3.80, _sy * 1.15, 0.445), CYANL, bevel=0.0)
# ---------------------------------------------------------------- 3. concrete plinth + RB-2 hopper (reinforced, lined, armoured lip)
box('rb2_plinth', (2.75, 4.55, 0.12), (4.98, 0.0, 0.06), CONC, bevel=0.03)
for _x, _y in ((3.9, -1.75), (6.05, -1.75), (3.9, 1.75), (6.05, 1.75)):
    box('rb2_pier', (0.42, 0.42, 0.62), (_x, _y, 0.43), CONC, bevel=0.03)
    box('rb2_leg', (0.26, 0.26, BRIM - 0.74), (_x, _y, (BRIM + 0.74) / 2), GRAPH2, bevel=0.02)
    box('rb2_legfoot', (0.48, 0.48, 0.06), (_x, _y, 0.77), GRAPH, bevel=0.01)
_top = [(BX0, -BY), (BX1, -BY), (BX1, BY), (BX0, BY)]; _bot = [(4.3, -0.62), (5.55, -0.62), (5.55, 0.62), (4.3, 0.62)]; _BZ = 0.66
_bm = bmesh.new(); _vt = [_bm.verts.new((x, y, BRIM)) for x, y in _top]; _vb = [_bm.verts.new((x, y, _BZ)) for x, y in _bot]
for i in range(4): j = (i + 1) % 4; _bm.faces.new((_vt[i], _vt[j], _vb[j], _vb[i]))
_ob = _obj(_bm, 'rb2_hopper', WHITE, smooth=True, angle=30)
_md = _ob.modifiers.new('sol', 'SOLIDIFY'); _md.thickness = 0.1; _md.offset = 1.0
def _wallpt(i, a, b):   # point on hopper wall i (top edge i..i+1), a along the edge 0..1, b down the wall 0 (rim)..1 (bottom)
    t0, t1 = V(_top[i] + (BRIM,)), V(_top[(i + 1) % 4] + (BRIM,)); b0, b1 = V(_bot[i] + (_BZ,)), V(_bot[(i + 1) % 4] + (_BZ,))
    return t0.lerp(t1, a).lerp(b0.lerp(b1, a), b)
for _i in range(4):                                                                    # wear liner plates inside (bolted, worn edges)
    for _a in (0.2, 0.5, 0.8):
        p0, p1 = _wallpt(_i, _a, 0.06), _wallpt(_i, _a, 0.9)
        _n = (V((_top[_i][0], _top[_i][1], 0)) - V((5.0, 0, 0))); _n.z = 0; _n.normalize()
        beam('rb2_liner', p0 - _n * 0.0, p1, 0.62 if _i % 2 == 0 else 0.7, 0.03, ARMOR, bevel=0.005, up=-_n)
for _i, _cnt in ((0, 5), (2, 5), (1, 3)):                                              # external stiffener ribs (-Y, +Y, +X faces)
    _n = (V((_top[_i][0] + _top[(_i + 1) % 4][0], _top[_i][1] + _top[(_i + 1) % 4][1], 0)) / 2 - V((4.96, 0, 0))); _n.z = 0; _n.normalize()
    for _k in range(_cnt):
        _a = (_k + 0.5) / _cnt; p0, p1 = _wallpt(_i, _a, 0.0) + _n * 0.12, _wallpt(_i, _a, 0.97) + _n * 0.12
        beam('rb2_stiff', p0, p1, 0.07, 0.16, GRAPH2, bevel=0.01, up=_n)
    beam('rb2_hband', _wallpt(_i, 0.0, 0.45) + _n * 0.14, _wallpt(_i, 1.0, 0.45) + _n * 0.14, 0.04, 0.12, GRAPH2, bevel=0.0, up=_n)
beam('rb2_cyan', _wallpt(0, 0.08, 0.3) + V((0, -0.2, 0)), _wallpt(0, 0.92, 0.3) + V((0, -0.2, 0)), 0.02, 0.05, CYANL, bevel=0.0)
for (a, b) in ((_top[1], _top[2]), (_top[2], _top[3]), (_top[3], _top[0]), (_top[0], _top[1])):    # box-section rim, top z 1.55
    beam('rb2_rim', (a[0], a[1], BRIM + 0.06), (b[0], b[1], BRIM + 0.06), 0.24, 0.18, GRAPH, bevel=0.02)
    beam('rb2_rimarmor', (a[0], a[1], BRIM + 0.16), (b[0], b[1], BRIM + 0.16), 0.26, 0.02, ARMOR, bevel=0.004)
# armoured tipping lip on the truck side (x 3.60..3.84, top z 1.57 < HT-04 tail lip z 1.63)
box('rb2_lip', (0.24, 2 * BY + 0.3, 0.27), (3.72, 0, 1.435), ARMOR, bevel=0.025)
box('rb2_lip_wear', (0.06, 2 * BY + 0.3, 0.05), (3.62, 0, 1.545), STEELL, bevel=0.01)
for _k in range(10):
    box('db_paint_lipstripe', (0.012, 0.4, 0.17), (3.591, -BY + 0.02 + _k * 0.41, 1.41), HAZ if _k % 2 == 0 else GRAPH, bevel=0.0)
for _y in (-1.6, -0.55, 0.55, 1.6): box('rb2_lip_gusset', (0.08, 0.06, 0.5), (3.68, _y, 1.12), GRAPH2, bevel=0.01)
# guard walls: +Y full concrete wall, -Y low wall (keeps the hopper readable from the station camera) + bollards
box('rb2_wall_n', (2.6, 0.26, 1.75), (5.15, BY + 0.34, 0.875), CONC, bevel=0.03)
box('rb2_wall_n_cap', (2.62, 0.3, 0.06), (5.15, BY + 0.34, 1.78), HAZ, bevel=0.01)
box('rb2_wall_s', (2.6, 0.26, 0.95), (5.15, -BY - 0.34, 0.475), CONC, bevel=0.03)
box('rb2_wall_s_cap', (2.62, 0.3, 0.06), (5.15, -BY - 0.34, 0.98), HAZ, bevel=0.01)
for _k in range(5): box('db_paint_wallstripe', (0.3, 0.012, 0.22), (4.05 + _k * 0.55, -BY - 0.479, 0.82), HAZ if _k % 2 == 0 else GRAPH, bevel=0.0)
for _x in (3.85, 5.15, 6.45):
    cyl('db_bollard', 0.12, 1.05, (_x, -2.72, 0.525), WHITE_S, segs=16)
    cyl('rb2_bollard_ring', 0.125, 0.12, (_x, -2.72, 0.78), GRAPH, segs=16)
    cyl('db_bollard_cyan', 0.127, 0.04, (_x, -2.72, 0.93), CYANL, segs=16)
    cyl('rb2_bollard_cap', 0.13, 0.05, (_x, -2.72, 1.07), GRAPH2, segs=16)
    cyl('rb2_bollard_foot', 0.2, 0.06, (_x, -2.72, 0.03), CONC, segs=16)
# ---------------------------------------------------------------- 4. back splash wall, +Y dust skirt, dust-suppression spray bars
for _x, _y in ((6.32, -2.05), (6.32, 2.05), (3.85, 2.05)):
    box('rb2_post', (0.18, 0.18, 3.1), (_x, _y, 1.55 + 0.02), STEEL, bevel=0.015)
    box('rb2_postbase', (0.34, 0.34, 0.05), (_x, _y, 0.04), GRAPH, bevel=0.01)
box('rb2_splash', (0.1, 4.0, 1.75), (6.36, 0, BRIM + 0.875 + 0.05), WHITE, bevel=0.02)
box('rb2_splash_armor', (0.04, 3.9, 0.7), (6.29, 0, BRIM + 0.45), ARMOR, bevel=0.005)
for _k in range(7): box('rb2_splash_rib', (0.12, 0.08, 1.7), (6.45, -1.8 + _k * 0.6, BRIM + 0.9), GRAPH2, bevel=0.01)
beam('rb2_splash_cyan', (6.42, -1.9, BRIM + 1.55), (6.42, 1.9, BRIM + 1.55), 0.02, 0.05, CYANL, bevel=0.0)
beam('rb2_toprail', (6.32, -2.05, 3.08), (6.32, 2.05, 3.08), 0.16, 0.2, WHITE_S, bevel=0.02)
beam('rb2_toprail', (3.85, 2.05, 3.08), (6.32, 2.05, 3.08), 0.16, 0.2, WHITE_S, bevel=0.02)
for _k in range(11):
    _x = BX0 + 0.35 + _k * (BX1 - BX0 - 0.45) / 10
    box('rb2_curtain', (0.26, 0.025, 1.4), (_x, BY + 0.14, 2.92 - 0.7), RUBBER, rot=(_rs.uniform(-0.04, 0.04), 0, 0), bevel=0.0)
beam('rb2_curtain_bar', (3.9, BY + 0.16, 2.93), (6.3, BY + 0.16, 2.93), 0.05, 0.1, GRAPH2, bevel=0.0)
for (_a, _b) in (((6.2, -1.9, 2.86), (6.2, 1.9, 2.86)), ((3.95, 1.95, 2.86), (6.15, 1.95, 2.86))):
    rod('rb2_spraybar', _a, _b, 0.045, STEELL, segs=12)
    _n = 8 if _a[0] == _b[0] else 6
    for _k in range(_n):
        p = V(_a).lerp(V(_b), (_k + 0.5) / _n)
        rot = (0, -math.pi / 2 - 0.6, 0) if _a[0] == _b[0] else (math.pi / 2 + 0.6, 0, 0)
        cyl('rb2_spray_nozzle', 0.03, 0.1, tuple(p + V((-0.05, 0, -0.05)) if _a[0] == _b[0] else p + V((0, -0.05, -0.05))), STEEL, rot=rot, segs=8)
pipe('rb2_spray_water', [(6.2, 1.9, 2.86), (6.2, 2.25, 2.86), (6.55, 2.25, 2.86), (6.55, 2.25, 0.35), (6.55, 2.6, 0.35), (9.9, 2.6, 0.35)], 0.05, H2OP, bend=0.2)
rod('rb2_spray_valve', (6.55, 2.25, 1.08), (6.55, 2.25, 1.32), 0.085, STEELL, segs=14)
rod('rb2_spray_valve_stem', (6.55, 2.25, 1.2), (6.55, 2.05, 1.2), 0.02, STEEL, segs=8)
cyl('rb2_spray_valve_wheel', 0.1, 0.03, (6.55, 2.04, 1.2), RED, rot=(math.pi / 2, 0, 0), segs=16)
# ---------------------------------------------------------------- 5. lights: status stack (green / amber / red) + flood lights on short posts
cyl('db_status_post', 0.07, 2.45, (6.6, -2.3, 1.225), GRAPH2, segs=12)
cyl('rb2_status_foot', 0.18, 0.05, (6.6, -2.3, 0.025), GRAPH, segs=12)
for _k, _m in enumerate((GREENL, LENSA, LENSR)):
    cyl('db_status_lens', 0.1, 0.17, (6.6, -2.3, 2.56 + _k * 0.19), _m, segs=16)
    cyl('rb2_status_ring', 0.108, 0.025, (6.6, -2.3, 2.465 + _k * 0.19), GRAPH, segs=16)
cyl('rb2_status_cap', 0.11, 0.05, (6.6, -2.3, 3.11), GRAPH, segs=16)
box('db_status_visor', (0.22, 0.04, 0.6), (6.6, -2.2, 2.75), GRAPH2, bevel=0.005) if False else None
for (_p, _aim) in (((4.1, -3.05), (1.0, 0.0)), ((6.75, 2.85), (2.5, 0.4))):
    _x, _y = _p; cyl('db_floodpost', 0.07, 3.0, (_x, _y, 1.5), GRAPH2, segs=12)
    cyl('rb2_floodpost_foot', 0.2, 0.06, (_x, _y, 0.03), CONC, segs=12)
    _d = V((_aim[0] - _x, _aim[1] - _y, 0)).normalized()
    beam('rb2_flood_arm', (_x, _y, 2.95), (_x + _d.x * 0.35, _y + _d.y * 0.35, 2.95), 0.06, 0.06, GRAPH2, bevel=0.0)
    _hc = V((_x + _d.x * 0.5, _y + _d.y * 0.5, 2.9)); _yaw = math.atan2(_d.y, _d.x)
    box('db_flood_head', (0.22, 0.46, 0.3), tuple(_hc), GRAPH, rot=(0, 0.55, _yaw), bevel=0.02)
    box('db_flood_lens', (0.02, 0.4, 0.24), tuple(_hc + _d * 0.11 + V((0, 0, -0.06))), LAMP, rot=(0, 0.55, _yaw), bevel=0.0)
    box('db_flood_cyan', (0.23, 0.47, 0.025), tuple(_hc + V((0, 0, 0.14))), CYANL, rot=(0, 0.55, _yaw), bevel=0.0)
# ---------------------------------------------------------------- 6. grizzly over the hopper (Intake_Grate: shakes on intake_shake)
with grp('Intake_Grate'):
    for _k in range(13):
        _y = -BY + 0.16 + _k * (2 * BY - 0.32) / 12
        beam('igr_bar', (BX0 + 0.14, _y, BRIM + 0.13), (BX1 - 0.08, _y, BRIM + 0.13), 0.07, 0.12, GRATE, bevel=0.0)
        beam('igr_barcap', (BX0 + 0.14, _y, BRIM + 0.195), (BX1 - 0.08, _y, BRIM + 0.195), 0.075, 0.012, ARMOR, bevel=0.0)
    for _k in range(4):
        _x = BX0 + 0.32 + _k * (BX1 - BX0 - 0.6) / 3
        beam('igr_cross', (_x, -BY + 0.08, BRIM + 0.08), (_x, BY - 0.08, BRIM + 0.08), 0.12, 0.12, GRAPH2, bevel=0.0)
    beam('igr_frame', (BX0 + 0.1, -BY + 0.05, BRIM + 0.09), (BX0 + 0.1, BY - 0.05, BRIM + 0.09), 0.1, 0.1, GRAPH, bevel=0.0)
# ---------------------------------------------------------------- 7. AF-1 inclined apron feeder (+X, out of the hopper's outlet to SZ-1)
AF0, AF1 = V((4.7, 0.0, 0.48)), V((8.05, 0.0, 1.86)); _A, _B, _L, _R = frame_from(AF0, AF1); _d = (AF1 - AF0).normalized(); _s = _R.col[1]; _u = _R.col[2]
for _sy in (-1, 1):
    beam('af_frame', AF0 + _s * _sy * 0.62 - _u * 0.12, AF1 + _s * _sy * 0.62 - _u * 0.12, 0.12, 0.42, GRAPH2, bevel=0.01, up=_u)
    beam('af_skirt', AF0 + _d * 1.2 + _s * _sy * 0.52 + _u * 0.3, AF1 + _s * _sy * 0.52 + _u * 0.3, 0.05, 0.42, WHITE, bevel=0.01, up=_u)
    beam('af_cyan', AF0 + _d * 1.4 + _s * _sy * 0.555 + _u * 0.42, AF1 - _d * 0.3 + _s * _sy * 0.555 + _u * 0.42, 0.012, 0.04, CYANS, bevel=0.0, up=_u)
    for _k in range(5):
        _q = AF0 + _d * (1.5 + _k * (_L - 1.8) / 4)
        beam('af_skirtrib', _q + _s * _sy * 0.56 + _u * 0.1, _q + _s * _sy * 0.56 + _u * 0.5, 0.05, 0.06, GRAPH2, bevel=0.0, up=_d)
_np = int(_L / 0.24)
for _k in range(_np):                                                                  # manganese apron pans
    _q = AF0 + _d * (0.12 + _k * 0.24) + _u * 0.05
    beam('af_pan', _q - _d * 0.11, _q + _d * 0.11, 1.0, 0.07, GRATE if _k % 2 else ARMOR, bevel=0.006, up=_u)
rod('af_tailshaft', AF0 - _s * 0.75, AF0 + _s * 0.75, 0.2, GRAPH, segs=20)
rod('af_headshaft', AF1 - _s * 0.8, AF1 + _s * 0.8, 0.26, GRAPH, segs=20)
ore_chunks('af_ore', tuple(AF0 + _d * 1.9 + _u * 0.2), 0.45, 10, [(ORE, 3, 'rock'), (HE3, 1, 'he3')], size=(0.1, 0.22), seed=611)
# drive on the camera (-Y) side of the head: gearbox, coupling, motor housing with fins + cyan band, torque arm
_gp = AF1 - _s * 1.05 - _d * 0.15
box('af_gearbox', (0.62, 0.45, 0.55), tuple(_gp), GRAPH2, bevel=0.04)
_mp = _gp - _d * 0.78 - _u * 0.05
rod('af_motor', _mp - _d * 0.4, _mp + _d * 0.35, 0.24, WHITE_S, segs=22)
for _k in range(6): rod('af_motor_fin', _mp + _d * (-0.32 + _k * 0.12), _mp + _d * (-0.3 + _k * 0.12), 0.27, GRAPH2, segs=22)
rod('af_motor_cyan', _mp + _d * 0.22, _mp + _d * 0.26, 0.255, CYANL, segs=22)
rod('af_coupling', _mp + _d * 0.35, _gp - _d * 0.31, 0.11, STEEL, segs=14)
box('af_torquearm', (0.12, 0.08, 0.9), tuple(_gp + V((0, 0, -0.6))), GRAPH, bevel=0.01)
# head hood + inlet into SZ-1, legs
box('af_headhood', (0.9, 1.4, 0.55), tuple(AF1 + V((0.15, 0, 0.2))), WHITE_S, rot=(0, -math.atan2(_d.z, math.hypot(_d.x, _d.y)) * 0.5, 0), bevel=0.05)
box('af_headhood_band', (0.92, 1.42, 0.06), tuple(AF1 + V((0.15, 0, 0.42))), GRAPH, rot=(0, -math.atan2(_d.z, math.hypot(_d.x, _d.y)) * 0.5, 0), bevel=0.01)
for _f in (0.42, 0.72, 0.97):
    _q = AF0.lerp(AF1, _f)
    for _sy in (-1, 1):
        box('af_leg', (0.16, 0.16, _q.z - 0.3), tuple(_q + _s * _sy * 0.62 - V((0, 0, (_q.z + 0.3) / 2 - 0.0))), GRAPH2, bevel=0.01)
        box('af_legfoot', (0.4, 0.4, 0.07), (_q.x, _sy * 0.62, 0.035), GRAPH, bevel=0.01)
    beam('af_legx', _q - _s * 0.62 - V((0, 0, _q.z * 0.6)), _q + _s * 0.62 - V((0, 0, 0.35)), 0.06, 0.06, STEEL)
label('af_plate', 'AF-1  APRON FEEDER', None, tuple(AF0.lerp(AF1, 0.62) - _s * 0.6 + V((0, -0.02, 0.05))), w=1.3, size=0.1, post=False)
# ---------------------------------------------------------------- 8. SZ-1 primary sizer (twin-shaft), hatch, vents, flywheel drive
SZC = V((8.72, 0.0, 1.32)); SZS = V((1.3, 1.7, 0.9))
box('sz_body', tuple(SZS), tuple(SZC), WHITE, bevel=0.05)
for _sx in (-1, 1):
    for _sy in (-1, 1):
        box('sz_corner', (0.12, 0.12, SZS.z + 0.04), tuple(SZC + V((_sx * SZS.x / 2, _sy * SZS.y / 2, 0))), GRAPH, bevel=0.015)
for _z in (-0.45, 0.45): 
    box('sz_frameband', (SZS.x + 0.06, SZS.y + 0.06, 0.08), tuple(SZC + V((0, 0, _z))), GRAPH, bevel=0.01)
for _x in (-0.22, 0.22):                                                                # panel lines on the camera face
    box('sz_panelline', (0.015, 0.01, SZS.z - 0.16), tuple(SZC + V((_x, -SZS.y / 2 - 0.005, 0))), GRAPH2, bevel=0.0)
box('sz_cyan', (SZS.x - 0.2, 0.012, 0.035), tuple(SZC + V((0, -SZS.y / 2 - 0.008, 0.33))), CYANL, bevel=0.0)
# inspection hatch (hinged, dogged), left of the flywheel
_hp = SZC + V((-0.38, -SZS.y / 2 - 0.03, -0.02))
box('sz_hatch', (0.42, 0.04, 0.48), tuple(_hp), GRAPH2, bevel=0.012)
for _z in (-0.16, 0.16): cyl('sz_hatch_hinge', 0.025, 0.09, tuple(_hp + V((-0.22, -0.02, _z))), STEEL, segs=10)
box('sz_hatch_handle', (0.04, 0.05, 0.16), tuple(_hp + V((0.15, -0.04, 0))), STEELL, bevel=0.005)
for _x in (-0.14, 0.14): box('sz_hatch_dog', (0.06, 0.04, 0.04), tuple(_hp + V((_x, -0.03, 0.27))), STEEL, bevel=0.005)
box('sz_hatch_stripe', (0.4, 0.008, 0.035), tuple(_hp + V((0, -0.024, -0.2))), HAZ, bevel=0.0)
# vents (louvres) on the top rear + side
box('sz_vent', (0.55, 0.9, 0.2), tuple(SZC + V((0.3, 0.25, SZS.z / 2 + 0.1))), GRAPH2, bevel=0.02)
for _k in range(6): box('sz_vent_louvre', (0.5, 0.06, 0.04), tuple(SZC + V((0.3, -0.12 + _k * 0.15, SZS.z / 2 + 0.215))), STEEL, rot=(0.5, 0, 0), bevel=0.0)
for _k in range(5): box('sz_sidevent', (0.012, 0.06 if False else 0.9, 0.035), tuple(SZC + V((SZS.x / 2 + 0.006, 0, -0.25 + _k * 0.09))), GRAPH2, bevel=0.0)
# inlet hood joining AF-1's head
box('sz_inlet', (0.85, 1.25, 0.42), tuple(SZC + V((-0.3, 0, SZS.z / 2 + 0.2))), WHITE_S, bevel=0.04)
box('sz_inlet_band', (0.87, 1.27, 0.05), tuple(SZC + V((-0.3, 0, SZS.z / 2 + 0.05))), GRAPH, bevel=0.01)
# stand
for _sx in (-1, 1):
    for _sy in (-1, 1):
        box('sz_leg', (0.18, 0.18, SZC.z - SZS.z / 2), (SZC.x + _sx * (SZS.x / 2 - 0.1), _sy * (SZS.y / 2 - 0.1), (SZC.z - SZS.z / 2) / 2), GRAPH2, bevel=0.015)
        box('sz_legfoot', (0.42, 0.42, 0.06), (SZC.x + _sx * (SZS.x / 2 - 0.1), _sy * (SZS.y / 2 - 0.1), 0.03), GRAPH, bevel=0.01)
box('sz_skid', (SZS.x + 0.5, SZS.y + 0.4, 0.1), (SZC.x, 0, 0.05), CONC, bevel=0.02)
label('sz_plate', 'SZ-1  PRIMARY SIZER', None, tuple(SZC + V((0.1, -SZS.y / 2 - 0.03, 0.62))), w=1.25, size=0.1, post=False)
# flywheel drive on the camera face: motor on a bracket + V-belt; the flywheel itself is the moving node
FWC = SZC + V((0.3, -SZS.y / 2 - 0.16, -0.02)); FWR = 0.36
rod('sz_shaft', FWC + V((0, 0.16, 0)), FWC - V((0, 0.06, 0)), 0.06, STEEL, segs=12)
box('sz_bearing', (0.2, 0.12, 0.16), tuple(FWC + V((0, 0.1, 0))), GRAPH, bevel=0.01)
_mc = V((FWC.x - 0.05, FWC.y + 0.02, 0.42))
box('sz_motorbase', (0.7, 0.42, 0.08), (_mc.x, _mc.y, 0.12), GRAPH, bevel=0.01)
rod('sz_motor', _mc + V((-0.28, 0, 0)), _mc + V((0.25, 0, 0)), 0.17, WHITE_S, segs=20)
for _k in range(5): rod('sz_motor_fin', _mc + V((-0.24 + _k * 0.1, 0, 0)), _mc + V((-0.22 + _k * 0.1, 0, 0)), 0.19, GRAPH2, segs=20)
rod('sz_motor_cyan', _mc + V((0.18, 0, 0)), _mc + V((0.21, 0, 0)), 0.18, CYANL, segs=20)
cyl('sz_motor_pulley', 0.1, 0.08, tuple(_mc + V((0.05, -0.2, 0))), GRAPH, rot=(math.pi / 2, 0, 0), segs=18)
for _sx in (-1, 1):
    beam('sz_vbelt', _mc + V((0.05 + _sx * 0.09, -0.21, 0)), FWC + V((_sx * (FWR - 0.04), -0.05, 0)), 0.03, 0.03, RUBBER, bevel=0.0)
with grp('Sizer_Flywheel'):
    cyl('sz_fly_rim', FWR, 0.12, tuple(FWC), GRAPH, rot=(math.pi / 2, 0, 0), segs=32)
    cyl('sz_fly_web', FWR - 0.06, 0.06, tuple(FWC + V((0, 0.01, 0))), GRAPH2, rot=(math.pi / 2, 0, 0), segs=32)
    cyl('sz_fly_hub', 0.1, 0.16, tuple(FWC - V((0, 0.02, 0))), STEELL, rot=(math.pi / 2, 0, 0), segs=16)
    for _k in range(6):
        _a = _k * math.tau / 6
        beam('sz_fly_spoke', FWC + V((math.cos(_a) * 0.1, -0.035, math.sin(_a) * 0.1)), FWC + V((math.cos(_a) * (FWR - 0.06), -0.035, math.sin(_a) * (FWR - 0.06))), 0.07, 0.05, STEEL, bevel=0.0, up=V((0, 1, 0)))
    box('sz_fly_cyan', (0.18, 0.02, 0.04), tuple(FWC + V((0, -0.065, FWR - 0.03))), CYANL, bevel=0.0)       # one cyan tick so the spin reads
    box('sz_fly_mark', (0.04, 0.02, 0.14), tuple(FWC + V((0, -0.07, -(FWR - 0.1)))), HAZ, bevel=0.0)
GAME['pivots']['Sizer_Flywheel'] = tuple(FWC)
# belt guard (open mesh frame, keeps the flywheel visible)
for _z in (FWC.z + FWR + 0.06, 0.3):
    beam('sz_guardrail', (FWC.x - 0.55, FWC.y - 0.16, _z), (FWC.x + 0.45, FWC.y - 0.16, _z), 0.03, 0.04, HAZ, bevel=0.0)
for _x in (FWC.x - 0.55, FWC.x + 0.45): beam('sz_guardpost', (_x, FWC.y - 0.16, 0.12), (_x, FWC.y - 0.16, FWC.z + FWR + 0.06), 0.04, 0.04, HAZ, bevel=0.0)
# ---------------------------------------------------------------- 9. covered transfer chute -> CV-0 tail (pulley housing + guards) -> SP-1
CT0 = V((8.9, 0.75, 0.42)); CH = V((4.6, 5.35, 1.8))
box('tc_chute', (0.95, 0.9, 0.5), (8.85, 0.45, 0.62), WHITE_S, rot=(0.25, 0, 0), bevel=0.04)
box('tc_chute_band', (0.97, 0.92, 0.05), (8.85, 0.45, 0.8), GRAPH, rot=(0.25, 0, 0), bevel=0.01)
box('tc_chute_door', (0.02, 0.4, 0.3), (9.335, 0.45, 0.62), GRAPH2, bevel=0.005)
_cd, _cs, _cu = conveyor('cv0', CT0, CH, w=0.9, cover=(0.3, 0.9), gaps=1)
_cL = (CH - CT0).length
box('cv0_loadskirt', (1.5, 1.08, 0.36), tuple(CT0 + _cd * 0.9 + _cu * 0.33), WHITE_S, rot=(0, -math.asin(_cd.z), math.atan2(_cd.y, _cd.x)), bevel=0.04)
box('cv0_loadskirt_cyan', (1.3, 1.1, 0.03), tuple(CT0 + _cd * 0.9 + _cu * 0.47), CYANS, rot=(0, -math.asin(_cd.z), math.atan2(_cd.y, _cd.x)), bevel=0.0)
for _k in range(3): rod('cv0_impactidler', CT0 + _cd * (0.5 + _k * 0.3) + _cu * 0.06 - _cs * 0.45, CT0 + _cd * (0.5 + _k * 0.3) + _cu * 0.06 + _cs * 0.45, 0.07, GRAPH, segs=12)
# tail pulley housing: side guard panels (frame + mesh), end guard, take-up screws, plinth
for _sy in (-1, 1):
    _gc = CT0 + _cs * _sy * 0.68 - _cd * 0.05
    box('cv0_tailguard', (1.1, 0.04, 0.62), tuple(_gc + V((0, 0, 0.0))), GRATE, rot=(0, 0, math.atan2(_cd.y, _cd.x)), bevel=0.01)
    box('cv0_tailguard_frame', (1.14, 0.06, 0.06), tuple(_gc + V((0, 0, 0.31))), HAZ, rot=(0, 0, math.atan2(_cd.y, _cd.x)), bevel=0.005)
    box('cv0_tailguard_frame', (1.14, 0.06, 0.06), tuple(_gc + V((0, 0, -0.29))), HAZ, rot=(0, 0, math.atan2(_cd.y, _cd.x)), bevel=0.005)
    rod('cv0_takeup', _gc - _cd * 0.5 + V((0, 0, 0.05)), _gc + _cd * 0.4 + V((0, 0, 0.05)), 0.025, STEELL, segs=8)
    box('cv0_takeup_block', (0.2, 0.12, 0.2), tuple(_gc + V((0, 0, 0.05)) - _cs * _sy * 0.06), GRAPH2, rot=(0, 0, math.atan2(_cd.y, _cd.x)), bevel=0.01)
box('cv0_tailend', (0.04, 1.4, 0.6), tuple(CT0 - _cd * 0.6), GRATE, rot=(0, 0, math.atan2(_cd.y, _cd.x)), bevel=0.01)
box('cv0_tailplinth', (1.4, 1.6, 0.12), tuple(V((CT0.x, CT0.y, 0.06)) - _cd * 0.05), CONC, rot=(0, 0, math.atan2(_cd.y, _cd.x)), bevel=0.02)
label('cv0_plate', 'CV-0  TO SP-1', None, tuple(CT0 - _cs * 0.72 + _cd * 0.0 + V((0, -0.04, 0.0))), w=0.9, size=0.09, post=False) if False else None
# ---------------------------------------------------------------- 10. inspection walkway (+Y side of AF-1 / SZ-1) + stairs, control box, pipe + cable runs
WZ = 1.5; WY0, WY1, WX0, WX1 = 1.05, 1.8, 6.75, 9.65
box('wk_deck', (WX1 - WX0, WY1 - WY0, 0.06), ((WX0 + WX1) / 2, (WY0 + WY1) / 2, WZ), GRATE, bevel=0.005)
for _y in (WY0, WY1): box('wk_toeplate', (WX1 - WX0, 0.02, 0.12), ((WX0 + WX1) / 2, _y, WZ + 0.08), HAZ, bevel=0.0)
box('wk_toeplate', (0.02, WY1 - WY0, 0.12), (WX0, (WY0 + WY1) / 2, WZ + 0.08), HAZ, bevel=0.0)
for _x in (WX0 + 0.1, (WX0 + WX1) / 2, WX1 - 0.1):
    for _y in (WY0 + 0.08, WY1 - 0.08):
        if _x < 8.0 and _y < 1.3: continue
        box('wk_column', (0.12, 0.12, WZ), (_x, _y, WZ / 2), GRAPH2, bevel=0.01)
box('wk_beam', (WX1 - WX0, 0.14, 0.18), ((WX0 + WX1) / 2, WY1 - 0.08, WZ - 0.12), GRAPH2, bevel=0.01)
rail('wk_handrail', [(WX0, WY0, WZ), (WX0, WY1, WZ), (WX1 - 0.75, WY1, WZ)], STEELL, h=1.05, post=1.2)
rail('wk_handrail', [(WX0, WY0, WZ), (8.0, WY0, WZ)], STEELL, h=1.05, post=1.2)
_ns = 6; _sx0, _sx1 = WX1 - 0.72, WX1
for _k in range(_ns):                                                                   # stairs down (+Y) to grade
    _y = WY1 + 0.32 * (_k + 0.5); _z = WZ - (WZ / (_ns + 0)) * (_k + 1)
    box('wk_stairtread', (_sx1 - _sx0 - 0.08, 0.28, 0.04), ((_sx0 + _sx1) / 2, _y, _z + 0.02), GRATE, bevel=0.003)
    box('wk_stairnose', (_sx1 - _sx0 - 0.08, 0.03, 0.02), ((_sx0 + _sx1) / 2, _y - 0.13, _z + 0.045), HAZ, bevel=0.0)
for _x in (_sx0, _sx1):
    beam('wk_stringer', (_x, WY1, WZ), (_x, WY1 + 0.32 * _ns + 0.1, 0.0), 0.05, 0.2, GRAPH2, bevel=0.005)
    rail('wk_handrail', [(_x, WY1, WZ), (_x, WY1 + 0.32 * _ns, 0.05)], STEELL, h=1.0, post=1.0)
# control box CB-1 (lit screen faces the camera) on a post by the walkway foot
CB = V((7.55, -1.62, 1.25))
box('cb_post', (0.12, 0.12, CB.z - 0.35), (CB.x, CB.y + 0.12, (CB.z - 0.35) / 2), GRAPH2, bevel=0.01)
box('cb_body', (0.62, 0.3, 0.76), tuple(CB), GRAPH2, bevel=0.03)
box('cb_door', (0.56, 0.03, 0.7), tuple(CB + V((0, -0.165, 0))), WHITE_S, bevel=0.01)
box('cb_screen', (0.34, 0.012, 0.22), tuple(CB + V((-0.05, -0.208, 0.14))), CYANS, bevel=0.0)
box('cb_screenframe', (0.4, 0.02, 0.28), tuple(CB + V((-0.05, -0.19, 0.14))), INK, bevel=0.0)
for _k, _m in enumerate((GREENL, REDL, AMBERL)):
    cyl('cb_button', 0.03, 0.03, tuple(CB + V((-0.15 + _k * 0.1, -0.19, -0.12))), _m, rot=(math.pi / 2, 0, 0), segs=10)
box('cb_estop', (0.08, 0.04, 0.08), tuple(CB + V((0.2, -0.195, -0.12))), REDL, bevel=0.01)
box('cb_hood', (0.7, 0.36, 0.05), tuple(CB + V((0, -0.02, 0.41))), GRAPH, rot=(-0.12, 0, 0), bevel=0.01)
box('cb_cyan', (0.56, 0.012, 0.025), tuple(CB + V((0, -0.19, 0.33))), CYANL, bevel=0.0)
# cable tray from CB-1 to the AF-1 and SZ-1 drives, conduits up the flood / status posts; water line along the north side (section 4)
_tz = 0.32
for (_a, _b) in (((7.55, -1.5, _tz), (7.55, -1.0, _tz)), ((6.75, -1.0, _tz), (8.95, -1.0, _tz)), ((6.75, -1.0, _tz), (6.75, -2.15, _tz))):
    beam('cb_tray', _a, _b, 0.22, 0.06, GRAPH, bevel=0.005)
    beam('cb_tray_cyan', V(_a) + V((0, 0, 0.035)), V(_b) + V((0, 0, 0.035)), 0.05, 0.012, CYANS, bevel=0.0)
pipe('cb_cable', [(8.95, -1.0, _tz), (8.95, -1.0, 0.62), (8.75, -0.98, 0.62)], 0.025, RUBBER, bend=0.08)
pipe('cb_cable', [(7.25, -1.0, _tz), (7.25, -1.05, 1.2), (7.35, -1.05, 1.35)], 0.025, RUBBER, bend=0.08)
pipe('cb_cable', [(6.75, -2.15, _tz), (6.62, -2.28, 0.4), (6.62, -2.28, 2.4)], 0.02, RUBBER, bend=0.06)
# plate on the low guard wall (reads from the station camera)
label('rb2_plate', 'RB-2  TIPPING HOPPER', 'BACK IN  -  TIP AT STOP  -  40 t', (5.15, -BY - 0.49, 0.62), w=2.3, size=0.13, post=False)
print('DB2 dump bay + intake built', flush=True)
