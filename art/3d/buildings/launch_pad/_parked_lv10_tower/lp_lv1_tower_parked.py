"""Launch Pad Lv1 ADD-ON mockup (A&A 10/24): launch tower LT-1 + crew lift + crew access arm + queue walkway + tidied tank farm.
Called from build_launch_pad.py with `--level 1` (default level 0 = Lv0, unchanged) after the Lv0 pad, ship and markers are built
(pad frame, before the +SHIFT move). Lv1 is an add-on inside the Lv0 look: the pad, ship and materials stay identical; only reused LP_*
master materials (they all map to the existing SHM_Paint / SHM_Metal / SHM_GlowCyan / SHM_Stainless game materials).

Frame: u along the 330 deg ladder axis LU from the ship centre, t = LT (left of u), z up (glTF y). Hatch landing deck top z = LAD_TOP (21.85).
Lv1 changes to Lv0 parts: ladder + cage removed (the lift replaces them), the ladder well is decked over flush (no well kerb / lid), the two
outer-edge gate rails of the landing are removed so the arm docks over the full deck width; LOX / LCH4 tanks, their feeds, hoses and the
P-2 pump lines are rebuilt in a tidy row (tank farm TF-1); the Tier_12 edge light under the walkway is dropped.
"""
import math, json, os
import bpy, bmesh
from mathutils import Vector

# ---- layout (metres, pad frame)
ARM_U0 = 5.47            # arm deck end (2 cm off the landing deck edge u 5.45)
DOOR_U = 14.40           # hoistway door face (lift doors face -u: toward the arm / ship)
TW_U0, TW_U1, TW_T = 14.40, 18.00, 1.80     # tower footprint (u 14.4-18.0, t +-1.8)
TW_COL_U, TW_COL_T, TW_COL_R = (14.55, 17.85), 1.65, 0.14
TW_TOP, HH_TOP = 25.20, 27.40               # lattice top, head-house roof
PL_U0, PL_U1, PL_T, PL_Z = 14.00, 18.40, 2.20, 0.31   # tower plinth, top z = walkway / car-floor level
WK_U0, WK_U1, WK_T = 7.00, 14.00, 0.80      # queue walkway deck (flat, top PL_Z), continues on the plinth to the door sill at DOOR_U
CREW_GAP, N_QUEUE = 1.5, 5
ARM_T, RAIL_T, RAIL_R, RAIL_H = 1.00, 0.93, 0.032, 1.05   # arm deck half width, rail centre |t|, top-rail radius, rail height
CAR_U0, CAR_DEPTH = 14.62, 1.50                           # car portal face, car depth (u)
CAB_T, CAB_U0, CAB_U1 = 0.70, 14.74, 15.94                # clear cab floor |t| <= 0.70 (1.40 m) x u 14.74-15.94 (1.20 m)
DOOR_T, DOOR_H = 0.70, 2.10                               # door opening |t| <= 0.70 (1.40 m) x 2.10 m
POCKET_T0, POCKET_T1 = 0.70, 1.20                          # door pockets each side (0.50 m) for a 2-panel stack 0.37 m
CREW_W = 0.70            # AA3 crew_boarding v4 rig: 0.67 x 0.70 m rest-pose footprint
TF_R, TF_A, TF_TN, TF_N, TF_HALF = 17.6, math.radians(13.0), 2.75, -0.50, (3.0, 5.45)   # tank farm TF-1 slab centre radius / bearing


def build(G):
    rod, box, rbox, cyl, sphere, text = G['rod'], G['box'], G['rbox'], G['cyl'], G['sphere'], G['text']
    WHITE, WHITE_S, GRAPH, GRAPH_S, SATIN = G['WHITE'], G['WHITE_S'], G['GRAPH'], G['GRAPH_S'], G['SATIN']
    CYAN, CYANS, AMBERG, RUBBER, INK, INKW = G['CYAN'], G['CYANS'], G['AMBERG'], G['RUBBER'], G['INK'], G['INKW']
    LOXB, LCH4B = G['LOXB'], G['LCH4B']
    LU, LT, LAD_A, TOP, LAD_TOP, SSM = G['LU'], G['LT'], G['LAD_A'], G['TOP'], G['LAD_TOP'], G['SSM']
    grp_begin, grp_end, gl, mark = G['grp_begin'], G['grp_end'], G['gl'], G['mark']
    P = lambda u, t, z: LU * u + LT * t + Vector((0, 0, z))
    UT = lambda p: (Vector(p).dot(LU), Vector(p).dot(LT))
    REP = {'removed': {}, 'tris': {}}

    def base(o): return o.name.split('.')[0]
    def tris(o):
        if o.type != 'MESH': return 0
        return sum(len(p.vertices) - 2 for p in o.data.polygons)
    def kill(pred, tag):
        n = 0; tr = 0
        for o in list(bpy.data.objects):
            if o.type in ('MESH', 'CURVE', 'FONT') and pred(o): tr += tris(o); bpy.data.objects.remove(o, do_unlink=True); n += 1
        REP['removed'][tag] = n; REP.setdefault('removed_tris_raw', {})[tag] = tr; return n
    def wverts(o): return [o.matrix_world @ v.co for v in o.data.vertices] if o.type == 'MESH' else []

    # ================================================================ 1. ship: ladder + cage out, well decked over, outer gate rails out
    t_ladder = sum(tris(o) for o in bpy.data.objects if base(o).startswith(('ship_ph_ladder', 'ship_ph_rung', 'ship_ph_cage')))
    assert kill(lambda o: base(o).startswith(('ship_ph_ladder', 'ship_ph_rung', 'ship_ph_cage')), 'ladder_cage') > 0
    kill(lambda o: base(o).startswith(('ship_ph_hatch_frame', 'ship_ph_hatch_lid', 'ship_ph_hatch_hinge', 'ship_ph_hatch_strut')), 'well_kerb_lid')
    def gate_rail(o):
        if not base(o).startswith('ship_ph_hatch_rail'): return False
        ut = [UT(v) for v in wverts(o)]; us = [a for a, _ in ut]; ts = [abs(b) for _, b in ut]
        return min(us) >= 5.30 and (max(ts) - min(ts) > 0.3 or sum(ts) / len(ts) < 1.0)
    assert kill(gate_rail, 'landing_gate_rails') == 6, REP
    s0 = grp_begin()
    bm = bmesh.new(); z0, z1 = LAD_TOP - 0.10, LAD_TOP
    poly = [(4.06, -0.62), (5.15, -0.62), (5.15, 0.62), (4.06, 0.62)]
    lo = [bm.verts.new(P(u, t, z0)) for u, t in poly]; hi = [bm.verts.new(P(u, t, z1)) for u, t in poly]
    bm.faces.new(hi); bm.faces.new(lo[::-1])
    for i in range(4): j = (i + 1) % 4; bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    G['_obj'](bm, 'ship_l1_well_plate', SSM['band'], smooth=False)
    grp_end(s0, 'Ship')
    REP['ship_tris_removed_raw'] = t_ladder

    # ================================================================ 2. tank farm TF-1: tidy row on one slab, parallel colour-coded lines
    kill(lambda o: base(o).startswith(('lox_', 'lch4_')) or base(o) in ('decal_lox', 'decal_lox_sub', 'decal_lch4', 'decal_lch4_sub'), 'lv0_tanks')
    kill(lambda o: base(o) in ('man_header', 'man_valve', 'man_wheel', 'man_stem', 'feed_pipe', 'feed_elbow', 'feed_collar', 'pipe_support',
                               'hose_valvebox', 'hose_valve') or o.get('grp') in ('Hose_LOX', 'Hose_LCH4'), 'lv0_feeds_hoses')
    kill(lambda o: base(o) == 'pump_line', 'lv0_pump_lines')
    nv = Vector((math.cos(TF_A), math.sin(TF_A), 0)); tv = Vector((-nv.y, nv.x, 0)); C = nv * TF_R
    Q = lambda n, tn, z=0.0: C + nv * n + tv * tn + Vector((0, 0, z))
    LOX_P, LCH4_P = Q(TF_N, -TF_TN), Q(TF_N, TF_TN)
    G['LOX_P'], G['LCH4_P'] = LOX_P, LCH4_P
    s_tf = set(bpy.data.objects.keys())
    rbox('tf_slab', (2 * TF_HALF[0], 2 * TF_HALF[1], 0.30), tuple(Q(0, 0, 0.25)), GRAPH, rot=(0, 0, TF_A), r=0.08, segs=2)
    for tag, p, R_, H_, band, l1, l2 in (('lox', LOX_P, G['LOX_R'], G['LOX_H'], LOXB, 'LOX', 'LIQUID OXYGEN'),
                                         ('lch4', LCH4_P, G['LCH4_R'], G['LCH4_H'], LCH4B, 'LCH4', 'LCH4 · LIQUID METHANE')):
        G['cryo_tank'](tag, p.x, p.y, R_, H_, band, l1, l2)
        for o in list(bpy.data.objects):
            if base(o) == tag + '_plinth' and o.name not in s_tf: bpy.data.objects.remove(o, do_unlink=True)   # the shared slab replaces it
    # bund kerb: outer long side + both ends (the ship side stays open for the hoses)
    kh, kw = 0.22, 0.16
    rbox('tf_kerb', (kw, 2 * TF_HALF[1], kh), tuple(Q(TF_HALF[0] - kw / 2, 0, 0.4 + kh / 2)), GRAPH_S, rot=(0, 0, TF_A), r=0.03, segs=1)
    box('tf_kerb_strip', (0.02, 2 * TF_HALF[1] - 0.4, 0.05), tuple(Q(TF_HALF[0] + 0.005, 0, 0.4 + kh * 0.6)), CYANS, rot=(0, 0, TF_A), bevel=0)
    for s in (-1, 1):
        rbox('tf_kerb', (2 * TF_HALF[0] - 0.6, kw, kh), tuple(Q(0.3, s * (TF_HALF[1] - kw / 2), 0.4 + kh / 2)), GRAPH_S, rot=(0, 0, TF_A), r=0.03, segs=1)
    text('decal_tf', 'TF-1', tuple(Q(-TF_HALF[0] + 0.6, -TF_HALF[1] + 0.9, 0.402)), (0, 0, TF_A - math.pi / 2), 0.5, INKW, extrude=0.002)
    # Dock line (buried, surfaces at PIPE_END) -> split -> two parallel colour-coded feed lines on common sleepers -> each tank's bottom inlet
    PE = G['PIPE_END']; MZ, LZ = 1.6, 0.85
    q0 = Vector((PE.x, -1.85, MZ))
    rod('tf_header', (PE.x, PE.y, MZ), tuple(q0), 0.2, WHITE_S, segs=16); sphere('tf_tee', 0.24, tuple(q0), WHITE_S, sub=2)
    lines = (('LOX', 2.2, -TF_TN, LOX_P, G['LOX_R'], LOXB), ('LCH4', 2.75, TF_TN, LCH4_P, G['LCH4_R'], LCH4B))
    for tag, n_, tn_end, tp, R_, band in lines:
        a = Q(n_, -TF_HALF[1] - 0.45, MZ); b = Q(n_, -TF_HALF[1] - 0.45, LZ)
        rod('tf_branch', tuple(q0), tuple(a), 0.15, WHITE_S, segs=14); sphere('tf_elbow', 0.16, tuple(a), WHITE_S, sub=2)
        cyl('tf_valve', 0.22, 0.45, tuple(a + Vector((0, 0, 0.05))), SATIN, segs=14)
        whl = [tuple(a + Vector((0.28 * math.cos(math.tau * k / 20), 0.28 * math.sin(math.tau * k / 20), 0.42))) for k in range(21)]
        G['curve_tube']('tf_wheel', whl, 0.03, band, res=2); rod('tf_stem', tuple(a), tuple(a + Vector((0, 0, 0.42))), 0.03, SATIN, segs=6)
        rod('tf_line', tuple(a), tuple(b), 0.13, WHITE_S, segs=12); sphere('tf_elbow', 0.14, tuple(b), WHITE_S, sub=2)
        c_ = Q(n_, tn_end, LZ); rod('tf_line', tuple(b), tuple(c_), 0.13, WHITE_S, segs=12); sphere('tf_elbow', 0.14, tuple(c_), WHITE_S, sub=2)
        inl = tp + nv * (0.55 * R_) + Vector((0, 0, LZ)); inl.z = LZ
        rod('tf_line', tuple(c_), tuple(inl), 0.13, WHITE_S, segs=12); sphere('tf_elbow', 0.14, tuple(inl), WHITE_S, sub=2)
        rod('tf_inlet', tuple(inl), tuple(inl + Vector((0, 0, 0.55))), 0.13, WHITE_S, segs=12)
        for f in (0.12, 0.5, 0.88):
            q = b.lerp(c_, f); d = (c_ - b).normalized(); rod('tf_collar', tuple(q - d * 0.1), tuple(q + d * 0.1), 0.15, band, segs=12)
    for k in range(7):   # common pipe sleepers under both lines
        tn = -TF_HALF[1] - 0.45 + k * (TF_HALF[1] + 0.45 + TF_TN) / 6.0
        rbox('tf_sleeper', (1.1, 0.3, 0.7 if tn < -TF_HALF[1] else 0.35), tuple(Q(2.48, tn, 0.45 if tn < -TF_HALF[1] else 0.57)), GRAPH_S, rot=(0, 0, TF_A), r=0.03, segs=1)
    tf_names = set(bpy.data.objects.keys()) - s_tf
    # flexible hoses to the ship tail ports (Lv0 hose(): same look, new start points)
    G['hose']('LOX', LOX_P, G['LOX_R'], G['PORT']['LOX'], LOXB); G['hose']('LCH4', LCH4_P, G['LCH4_R'], G['PORT']['LCH4'], LCH4B)
    # Tier_08 pump skid P-2 lines into the new LCH4 position
    s8 = grp_begin(); PS, tp_, np_ = G['PS'], G['tp_'], G['np_']
    for k in (-1, 1):
        q = PS + tp_ * (k * 0.9) + np_ * 1.1; q.z = 0.9
        d = Vector((q.x - LCH4_P.x, q.y - LCH4_P.y, 0)).normalized(); e = LCH4_P + d * (G['LCH4_R'] + 0.55) + tp_ * (k * 0.35); e.z = 0.9
        e2 = e + Vector((0, 0, 1.7)); e3 = LCH4_P + (e2 - LCH4_P - Vector((0, 0, e2.z - LCH4_P.z))).normalized() * (G['LCH4_R'] - 0.05); e3.z = e2.z
        rod('pump_line', tuple(q), tuple(e), 0.11, WHITE_S, segs=12); sphere('pump_elbow', 0.12, tuple(e), WHITE_S, sub=2)
        rod('pump_line', tuple(e), tuple(e2), 0.11, WHITE_S, segs=12); sphere('pump_elbow', 0.12, tuple(e2), WHITE_S, sub=2)
        rod('pump_line', tuple(e2), tuple(e3), 0.11, WHITE_S, segs=12); rod('pump_flange', tuple(e3 + (e2 - e3).normalized() * 0.12), tuple(e3 + (e2 - e3).normalized() * 0.2), 0.16, SATIN, segs=12)
    grp_end(s8, 'Tier_08')

    # ================================================================ 3. queue walkway (flat, 7 m deck + plinth to the door sill)
    s_w = grp_begin()
    n_pl = 7; L = (WK_U1 - WK_U0) / n_pl
    for i in range(n_pl):
        uc = WK_U0 + (i + 0.5) * L
        rbox('wk_plate', (L - 0.02, 2 * WK_T, PL_Z - 0.05), tuple(P(uc, 0, (PL_Z + 0.05) / 2)), GRAPH_S, rot=(0, 0, LAD_A), r=0.015, segs=1)
    for s in (-1, 1):
        box('wk_edge_glow', (WK_U1 - WK_U0 - 0.1, 0.03, 0.03), tuple(P((WK_U0 + WK_U1) / 2, s * (WK_T - 0.04), PL_Z + 0.004)), CYANS, rot=(0, 0, LAD_A), bevel=0)
    QUEUE = [DOOR_U - 0.60 - CREW_GAP * k for k in range(N_QUEUE)]
    for uq in QUEUE:
        box('wk_spot', (0.34, 0.56, 0.006), tuple(P(uq, 0, PL_Z + 0.003)), INKW, rot=(0, 0, LAD_A), bevel=0)
    grp_end(s_w, 'L1_Walkway')
    # Tier_12 edge lights / lenses under the walkway or the tower plinth
    def under(o, m=0.15):
        for v in wverts(o):
            u, t = UT(v)
            if (WK_U0 - m <= u <= WK_U1 + m and abs(t) <= WK_T + m) or (PL_U0 - m <= u <= PL_U1 + m and abs(t) <= PL_T + m): return True
        return False
    kill(lambda o: base(o) in ('edge_light', 'edge_lens') and under(o), 'tier12_edge_lights_under_walkway')

    # ================================================================ 4. launch tower LT-1 (white lattice, graphite girts, cyan bands) + head house
    s_t = grp_begin()
    rbox('lt_plinth', (PL_U1 - PL_U0, 2 * PL_T, PL_Z + 0.05), tuple(P((PL_U0 + PL_U1) / 2, 0, (PL_Z - 0.05) / 2)), GRAPH, rot=(0, 0, LAD_A), r=0.06, segs=2)
    box('lt_plinth_glow', (0.03, 2 * PL_T - 0.3, 0.04), tuple(P(PL_U0 - 0.005, 0, PL_Z - 0.06)), CYANS, rot=(0, 0, LAD_A), bevel=0)
    cols = [(u, s * TW_COL_T) for u in TW_COL_U for s in (-1, 1)]
    for u, t in cols:
        rbox('lt_col_foot', (0.6, 0.6, 0.3), tuple(P(u, t, PL_Z + 0.15)), GRAPH_S, rot=(0, 0, LAD_A), r=0.04, segs=1)
        rod('lt_col', tuple(P(u, t, PL_Z)), tuple(P(u, t, TW_TOP)), TW_COL_R, WHITE_S, segs=8)
    LV = [PL_Z + 0.3 + 3.0 * k for k in range(9)] + [TW_TOP - 0.1]
    faces = [((TW_COL_U[0], -TW_COL_T), (TW_COL_U[0], TW_COL_T), 'front'), ((TW_COL_U[1], -TW_COL_T), (TW_COL_U[1], TW_COL_T), 'back'),
             ((TW_COL_U[0], -TW_COL_T), (TW_COL_U[1], -TW_COL_T), 'side'), ((TW_COL_U[0], TW_COL_T), (TW_COL_U[1], TW_COL_T), 'side')]
    for z in LV:
        for a, b, _ in faces: rod('lt_girt', tuple(P(*a, z)), tuple(P(*b, z)), 0.07, GRAPH_S, segs=6)
    for i in range(len(LV) - 1):
        za, zb = LV[i], LV[i + 1]
        for a, b, kind in faces:
            if kind == 'front' and (za < 2.6 or za <= LAD_TOP < zb or za <= LAD_TOP + DOOR_H < zb): continue   # keep both door openings clear
            rod('lt_brace', tuple(P(*a, za)), tuple(P(*b, zb)), 0.045, SATIN, segs=6); rod('lt_brace', tuple(P(*b, za)), tuple(P(*a, zb)), 0.045, SATIN, segs=6)
    for z in (LV[4], TW_TOP - 0.35):   # cyan bands
        for a, b, _ in faces:
            pa, pb = Vector(a), Vector(b); d = (pb - pa).normalized(); off = Vector((-d.y, d.x)) * 0.0
            box('lt_cyan', ((pb - pa).length - 0.3, 0.03, 0.06), tuple(P((pa.x + pb.x) / 2, (pa.y + pb.y) / 2, z + 0.1)), CYAN,
                rot=(0, 0, LAD_A + (0 if abs(d.x) > 0.5 else math.pi / 2)), bevel=0)
    # lift shaft: guide rails, counterweight + rails, ground + top hoistway portals
    for s in (-1, 1):
        rod('lt_guide', tuple(P(15.32, s * 1.30, PL_Z)), tuple(P(15.32, s * 1.30, TW_TOP)), 0.045, SATIN, segs=6)
        rod('lt_cw_guide', tuple(P(17.35, s * 0.35, PL_Z)), tuple(P(17.35, s * 0.35, TW_TOP)), 0.03, SATIN, segs=6)
    rbox('lt_counterweight', (0.30, 0.62, 2.2), tuple(P(17.35, 0, 13.0)), GRAPH, rot=(0, 0, LAD_A), r=0.03, segs=1)
    for zs, open_ in ((PL_Z, True), (LAD_TOP, False)):
        for s in (-1, 1):
            box('lt_jamb', (0.16, 0.16, DOOR_H + 0.16), tuple(P(DOOR_U + 0.08, s * (DOOR_T + 0.08), zs + (DOOR_H + 0.16) / 2)), GRAPH, rot=(0, 0, LAD_A), bevel=0.01)
            box('lt_pocket', (0.10, POCKET_T1 - POCKET_T0, DOOR_H + 0.16), tuple(P(DOOR_U + 0.14, s * (POCKET_T0 + POCKET_T1) / 2 + s * 0.08, zs + (DOOR_H + 0.16) / 2)),
                WHITE, rot=(0, 0, LAD_A), bevel=0.01)
        box('lt_header', (0.16, 2 * DOOR_T + 0.32, 0.24), tuple(P(DOOR_U + 0.08, 0, zs + DOOR_H + 0.12)), GRAPH, rot=(0, 0, LAD_A), bevel=0.01)
        box('lt_door_glow', (0.02, 1.0, 0.05), tuple(P(DOOR_U - 0.005, 0, zs + DOOR_H + 0.12)), CYAN, rot=(0, 0, LAD_A), bevel=0)
        box('lt_sill', (0.24, 2 * DOOR_T, 0.04), tuple(P(DOOR_U + 0.11, 0, zs - 0.02)), SATIN, rot=(0, 0, LAD_A), bevel=0)
        if not open_:   # top landing doors closed (the car is at the ground stop): 4 panels across the opening
            for k in range(4):
                tc = -DOOR_T + (k + 0.5) * (2 * DOOR_T / 4)
                box('lt_landing_door', (0.03, 2 * DOOR_T / 4 + 0.02, DOOR_H), tuple(P(DOOR_U + 0.19 + 0.035 * (k in (1, 2)), tc, zs + DOOR_H / 2)), WHITE_S, rot=(0, 0, LAD_A), bevel=0.005)
    # head house (lift machine room) + roof + warning beacon
    hc = (TW_U0 + TW_U1) / 2
    rbox('lt_headhouse', (TW_U1 - TW_U0, 2 * TW_T, HH_TOP - TW_TOP), tuple(P(hc, 0, (TW_TOP + HH_TOP) / 2)), WHITE, rot=(0, 0, LAD_A), r=0.12, segs=2)
    rbox('lt_roof', (TW_U1 - TW_U0 + 0.16, 2 * TW_T + 0.16, 0.18), tuple(P(hc, 0, HH_TOP + 0.09)), GRAPH, rot=(0, 0, LAD_A), r=0.04, segs=1)
    rbox('lt_hh_band', (TW_U1 - TW_U0 + 0.02, 2 * TW_T + 0.02, 0.32), tuple(P(hc, 0, TW_TOP + 0.45)), GRAPH, rot=(0, 0, LAD_A), r=0.03, segs=1)
    box('lt_hh_glow', (0.02, 2 * TW_T - 0.6, 0.06), tuple(P(TW_U0 - 0.012, 0, TW_TOP + 0.85)), CYAN, rot=(0, 0, LAD_A), bevel=0)
    box('lt_hh_glow', (TW_U1 - TW_U0 - 0.6, 0.02, 0.06), tuple(P(hc, -TW_T - 0.012, TW_TOP + 0.85)), CYAN, rot=(0, 0, LAD_A), bevel=0)
    rbox('lt_hh_vent', (1.2, 0.04, 0.5), tuple(P(hc + 0.6, -TW_T - 0.02, TW_TOP + 1.5)), GRAPH_S, rot=(0, 0, LAD_A), r=0.01, segs=1)
    rod('lt_mast', tuple(P(hc + 1.2, -1.2, HH_TOP + 0.18)), tuple(P(hc + 1.2, -1.2, HH_TOP + 1.25)), 0.05, SATIN, segs=6)
    sphere('lt_beacon', 0.13, tuple(P(hc + 1.2, -1.2, HH_TOP + 1.32)), AMBERG, sub=2)
    text('decal_lt1', 'LT-1', tuple(P(hc - 0.6, -TW_T - 0.014, TW_TOP + 1.25)), (math.pi / 2, 0, LAD_A), 0.55, INK, extrude=0.004)
    text('decal_lift', 'CREW LIFT', tuple(P(hc - 0.1, -TW_T - 0.014, PL_Z + 2.9)), (math.pi / 2, 0, LAD_A), 0.22, INK, extrude=0.003)
    # arm hinge column on the tower front (-t corner)
    HINGE = P(DOOR_U - 0.12, -1.25, LAD_TOP)
    rod('lt_hinge_pin', tuple(HINGE + Vector((0, 0, -1.25))), tuple(HINGE + Vector((0, 0, 1.4))), 0.10, SATIN, segs=10)
    for dz in (-1.1, 1.25): cyl('lt_hinge_knuckle', 0.17, 0.22, tuple(HINGE + Vector((0, 0, dz))), GRAPH_S, segs=12)
    grp_end(s_t, 'L1_Tower')

    # ================================================================ 5. crew access arm CA-1 (swung in, docked at the hatch landing)
    s_a = grp_begin()
    A0, A1, ZD = ARM_U0, DOOR_U - 0.02, LAD_TOP
    rbox('ca_deck', (A1 - A0, 2 * ARM_T, 0.08), tuple(P((A0 + A1) / 2, 0, ZD - 0.04)), GRAPH_S, rot=(0, 0, LAD_A), r=0.01, segs=1)
    for s in (-1, 1):
        box('ca_glow', (A1 - A0 - 0.2, 0.02, 0.03), tuple(P((A0 + A1) / 2, s * (ARM_T + 0.01), ZD - 0.05)), CYAN, rot=(0, 0, LAD_A), bevel=0)
        box('ca_toe', (A1 - A0 - 0.3, 0.02, 0.10), tuple(P((A0 + A1) / 2 + 0.15, s * (RAIL_T + 0.04), ZD + 0.05)), GRAPH, rot=(0, 0, LAD_A), bevel=0)
        # Warren side truss under the deck edge
        zt_, zb_ = ZD - 0.12, ZD - 1.15
        rod('ca_chord', tuple(P(A0 + 0.1, s * 0.95, zt_)), tuple(P(A1, s * 0.95, zt_)), 0.07, WHITE_S, segs=6)
        rod('ca_chord', tuple(P(A0 + 0.6, s * 0.95, zb_)), tuple(P(A1, s * 0.95, zb_)), 0.07, WHITE_S, segs=6)
        nb = 8
        for k in range(nb):
            ua = A0 + 0.6 + (A1 - A0 - 0.6) * k / nb; ub = A0 + 0.6 + (A1 - A0 - 0.6) * (k + 1) / nb
            if k % 2 == 0: rod('ca_web', tuple(P(ua, s * 0.95, zb_)), tuple(P(ub, s * 0.95, zt_)), 0.045, SATIN, segs=6)
            else: rod('ca_web', tuple(P(ua, s * 0.95, zt_)), tuple(P(ub, s * 0.95, zb_)), 0.045, SATIN, segs=6)
        rod('ca_web', tuple(P(A0 + 0.1, s * 0.95, zt_)), tuple(P(A0 + 0.6, s * 0.95, zb_)), 0.045, SATIN, segs=6)
        # handrail: posts every ~1.5 m, top + mid rail, flare out to the landing's wing-end corner posts (u 5.40, |t| 1.34)
        n_p = 7
        for k in range(n_p):
            u = 5.75 + (A1 - 0.15 - 5.75) * k / (n_p - 1); rod('ca_rail_post', tuple(P(u, s * RAIL_T, ZD)), tuple(P(u, s * RAIL_T, ZD + RAIL_H)), 0.028, SATIN, segs=6)
        for h, r_ in ((RAIL_H, RAIL_R), (RAIL_H * 0.5, 0.024)):
            rod('ca_rail', tuple(P(5.75, s * RAIL_T, ZD + h)), tuple(P(A1 - 0.15, s * RAIL_T, ZD + h)), r_, SATIN, segs=6)
            rod('ca_rail_flare', tuple(P(5.75, s * RAIL_T, ZD + h)), tuple(P(5.40, s * 1.34, ZD + h)), r_, SATIN, segs=6)
    for k in range(5):
        u = A0 + 0.6 + (A1 - A0 - 0.6) * k / 4; rod('ca_cross', tuple(P(u, -0.95, ZD - 1.15)), tuple(P(u, 0.95, ZD - 1.15)), 0.05, GRAPH_S, segs=6)
    rbox('ca_bumper', (0.08, 2 * ARM_T, 0.16), tuple(P(A0 + 0.04, 0, ZD - 0.2)), RUBBER, rot=(0, 0, LAD_A), r=0.02, segs=1)
    rbox('ca_hinge_arm', (0.5, 0.5, 0.3), tuple(HINGE + Vector((0, 0, -0.25)) + LU * -0.25), GRAPH_S, rot=(0, 0, LAD_A), r=0.03, segs=1)
    grp_end(s_a, 'L1_Arm')

    # ================================================================ 6. lift car (at the ground stop, doors open) + door panels
    s_c = grp_begin(); zf = PL_Z
    cu0, cu1 = CAR_U0, CAR_U0 + CAR_DEPTH; cuc = (cu0 + cu1) / 2
    rbox('car_floor', (CAR_DEPTH, 1.56, 0.12), tuple(P(cuc, 0, zf - 0.06)), GRAPH_S, rot=(0, 0, LAD_A), r=0.01, segs=1)
    rbox('car_back', (0.08, 1.56, 2.40), tuple(P(cu1 - 0.04 - 0.1, 0, zf + 1.2)), WHITE, rot=(0, 0, LAD_A), r=0.01, segs=1)
    for s in (-1, 1):
        rbox('car_side', (CAB_U1 - CAB_U0 + 0.14, 0.08, 2.40), tuple(P((CAB_U0 + CAB_U1) / 2, s * (CAB_T + 0.04), zf + 1.2)), WHITE, rot=(0, 0, LAD_A), r=0.01, segs=1)
        rbox('car_pocket', (0.12, POCKET_T1 - POCKET_T0, 2.40), tuple(P(cu0 + 0.06, s * (POCKET_T0 + POCKET_T1) / 2, zf + 1.2)), WHITE, rot=(0, 0, LAD_A), r=0.01, segs=1)
        box('car_glow', (0.02, 0.03, 2.0), tuple(P(cu0 - 0.005, s * (DOOR_T + 0.03), zf + 1.1)), CYAN, rot=(0, 0, LAD_A), bevel=0)
        for k in range(2):   # open: 2 panels per side stacked in the pocket (2-speed bi-parting, 4 x 0.37 m)
            box('car_door', (0.025, 0.37, DOOR_H), tuple(P(cu0 + 0.13 + 0.035 * k, s * (POCKET_T0 + 0.05 + 0.37 / 2), zf + DOOR_H / 2)), WHITE_S, rot=(0, 0, LAD_A), bevel=0.004)
    rbox('car_header', (0.12, 2 * POCKET_T1, 0.30), tuple(P(cu0 + 0.06, 0, zf + DOOR_H + 0.15)), WHITE, rot=(0, 0, LAD_A), r=0.01, segs=1)
    rbox('car_roof', (CAR_DEPTH, 2 * POCKET_T1, 0.10), tuple(P(cuc, 0, zf + 2.45)), GRAPH, rot=(0, 0, LAD_A), r=0.01, segs=1)
    box('car_roof_glow', (CAR_DEPTH - 0.2, 0.02, 0.04), tuple(P(cuc, -(POCKET_T1 + 0.005), zf + 2.42)), CYAN, rot=(0, 0, LAD_A), bevel=0)
    for s in (-1, 1): rbox('car_shoe', (0.2, 0.2, 2.2), tuple(P(15.32, s * 1.20, zf + 1.2)), GRAPH_S, rot=(0, 0, LAD_A), r=0.02, segs=1)
    rbox('car_handrail', (0.04, 1.2, 0.04), tuple(P(CAB_U1 + 0.02, 0, zf + 0.95)), SATIN, rot=(0, 0, LAD_A), r=0.01, segs=1)
    grp_end(s_c, 'L1_Elevator')

    # ================================================================ 7. queue scale figures (1.8 m) + markers (spec only, nothing animated)
    s_q = grp_begin(); facing = LAD_A + math.radians(90)    # astronaut front is local -Y -> face +u (the car)
    for uq in QUEUE: G['astronaut'](tuple(P(uq, 0, PL_Z)), rot_z=facing, c='Mine')
    grp_end(s_q, 'L1_Queue')
    SPEC = {'ElevatorUp': {'s': 10.0, 'ease': 'smootherstep', 'from': 'Lift_Bottom', 'to': 'Lift_Top'},
            'ElevatorDown': {'s': 8.0, 'ease': 'smootherstep', 'from': 'Lift_Top', 'to': 'Lift_Bottom'},
            'DoorsOpen': {'s': 1.5, 'ease': 'smootherstep', 'panels': '4 x 0.37 m two-speed bi-parting, slide 0.50 m pockets each side'},
            'DoorsClose': {'s': 1.5, 'ease': 'smootherstep'}}
    MKL = []
    MKL.append(mark('Lift_Bottom', P(cuc, 0, PL_Z), {'kind': 'lift_stop', 'car_floor_y': PL_Z, 'doors_face': 'access arm (-u, toward the ship)', 'clips_spec': json.dumps(SPEC), 'animated': False}))
    MKL.append(mark('Lift_Top', P(cuc, 0, LAD_TOP), {'kind': 'lift_stop', 'car_floor_y': LAD_TOP, 'rise_m': round(LAD_TOP - PL_Z, 3), 'exit': 'CrewArm deck -> hatch landing'}))
    MKL.append(mark('Lift_Doors', P(CAR_U0, 0, PL_Z), {'kind': 'lift_doors', 'opening_m': [2 * DOOR_T, DOOR_H], 'facing': 'toward the access arm / ship (-u)'}))
    MKL.append(mark('Arm_Hinge', HINGE, {'kind': 'arm_hinge', 'axis': 'vertical (glTF +Y)', 'pose': 'swung in, docked', 'swing_out_note': 'spec later'}))
    MKL.append(mark('Arm_Dock', P(ARM_U0, 0, LAD_TOP), {'kind': 'arm_dock', 'landing': 'hatch landing outer edge u 5.45'}))
    for i, uq in enumerate(QUEUE):
        MKL.append(mark('Lift_Queue_%02d' % (i + 1), P(uq, 0, PL_Z), {'kind': 'crew_spot', 'facing': 'lift car (+u)', 'spacing_m': CREW_GAP}))
    MKL.append(mark('Walkway_Start', P(WK_U0, 0, PL_Z), {'kind': 'walkway', 'width_m': 2 * WK_T}))
    MKL.append(mark('Walkway_End', P(DOOR_U, 0, PL_Z), {'kind': 'walkway', 'note': 'door sill'}))
    for o in MKL: o.empty_display_size = 0.3
    if 'Ladder_Foot' in bpy.data.objects:
        bpy.data.objects['Ladder_Foot']['note'] = 'Lv1: no ladder - crew queue on the walkway (Lift_Queue_01..05) and ride the crew lift to the hatch landing'

    # ================================================================ 8. checks: queue fits the walkway, crew 2-abreast clearances, nothing crowds
    q_lo = QUEUE[-1] - CREW_W / 2; assert q_lo >= WK_U0, q_lo
    for a, b in zip(QUEUE, QUEUE[1:]): assert a - b - CREW_W >= 0.7, (a, b)
    arm_clear = 2 * (RAIL_T - RAIL_R); two_abreast = 2 * CREW_W + 0.10; rail_gap = (arm_clear - two_abreast) / 2
    assert rail_gap >= 0.03, rail_gap
    land_clear = 2 * (1.34 - 0.032)
    # real surface intersections (BVH triangle overlap, AABB pre-filter): every new Lv1 part vs every other Lv0 mesh (berm, tiers, ship, hoses ...)
    from mathutils.bvhtree import BVHTree
    new = {g: [o for o in bpy.data.objects if o.get('grp') == g] for g in ('L1_Tower', 'L1_Arm', 'L1_Elevator', 'L1_Walkway')}
    new['TF-1'] = [bpy.data.objects[n] for n in tf_names if n in bpy.data.objects]
    mine = set(o.name for o in G['coll']('Mine').all_objects)
    def bb(o):
        vs = wverts(o)
        if not vs: return None
        return (min(v.x for v in vs), max(v.x for v in vs), min(v.y for v in vs), max(v.y for v in vs), min(v.z for v in vs), max(v.z for v in vs))
    ign = ('pad_slab', 'pad_apron', 'apron_joint', 'apron_joint_r', 'target_ring', 'target_bar', 'target_tick', 'pad_strip', 'rim_tile', 'line_cover', 'flame_grate')
    newset = set(o.name for L_ in new.values() for o in L_)
    others = [(o, bb(o)) for o in bpy.data.objects if o.name in mine and o.type == 'MESH' and o.name not in newset and base(o) not in ign
              and o.get('grp') not in ('L1_Queue', 'Marker')]
    _bv = {}
    def bvh(o):
        if o.name not in _bv: _bv[o.name] = BVHTree.FromPolygons([tuple(v) for v in wverts(o)], [tuple(p.vertices) for p in o.data.polygons])
        return _bv[o.name]
    BY_DESIGN = {('tf_header', 'pl_elbow'), ('tf_header', 'pl_riser'), ('tf_slab', 'hose_valvebox'), ('tf_slab', 'hose_stand'), ('tf_slab', 'hose_collar')}
    hits, by_design = [], []
    for g, L_ in new.items():
        for o in L_:
            b1 = bb(o)
            if b1 is None: continue
            for o2, b2 in others:
                if b2 is None: continue
                if not (b1[0] < b2[1] and b2[0] < b1[1] and b1[2] < b2[3] and b2[2] < b1[3] and b1[4] < b2[5] and b2[4] < b1[5]): continue
                if bvh(o).overlap(bvh(o2)):
                    rec = (g, o.name, o2.name, o2.get('grp', 'Base'))
                    (by_design if (base(o), base(o2)) in BY_DESIGN or (g == 'L1_Arm' and o2.get('grp') == 'Ship') else hits).append(rec)
    REP['intersections'] = hits; REP['intersections_by_design'] = by_design
    # nearest gaps that matter (plan view, metres)
    def gap2d(A_, B_):
        va = [v for o in A_ for v in wverts(o)]; vb = [v for o in B_ for v in wverts(o)]
        return round(min(((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5 for a in va[::max(1, len(va) // 400)] for b in vb[::max(1, len(vb) // 400)]), 2)
    objs = lambda pred: [o for o in bpy.data.objects if o.type == 'MESH' and o.name in mine and pred(o)]
    REP['gaps_m'] = {'TF-1 slab - vault': gap2d(objs(lambda o: base(o) == 'tf_slab'), objs(lambda o: base(o).startswith('vault'))),
                     'TF-1 slab - berm blocks': gap2d(objs(lambda o: base(o) == 'tf_slab'), objs(lambda o: base(o) == 'berm_block')),
                     'TF-1 slab - pump skid P-2': gap2d(objs(lambda o: base(o) == 'tf_slab'), objs(lambda o: base(o) in ('pump_base', 'pump_skid'))),
                     'TF-1 slab - rim tiles': gap2d(objs(lambda o: base(o) == 'tf_slab'), objs(lambda o: base(o) == 'rim_tile')),
                     'tower plinth - vault': gap2d(objs(lambda o: base(o) == 'lt_plinth'), objs(lambda o: base(o).startswith('vault'))),
                     'tower plinth - TF-1 slab': gap2d(objs(lambda o: base(o) == 'lt_plinth'), objs(lambda o: base(o) == 'tf_slab')),
                     'walkway - ship legs': gap2d(objs(lambda o: o.get('grp') == 'L1_Walkway'), objs(lambda o: base(o) == 'ship_ss_legs')),
                     'walkway - hoses': gap2d(objs(lambda o: o.get('grp') == 'L1_Walkway'), objs(lambda o: o.get('grp') in ('Hose_LOX', 'Hose_LCH4'))),
                     'walkway - flame grates': gap2d(objs(lambda o: o.get('grp') == 'L1_Walkway'), objs(lambda o: base(o) == 'flame_grate'))}
    # walkway corridor (|t| <= 0.8, u 7.0-14.4, z 0.31-2.3) must be empty of everything but its own deck / figures
    blk = []
    for o in bpy.data.objects:
        if o.name not in mine or o.type != 'MESH' or o.get('grp') in ('L1_Walkway', 'L1_Queue', 'Marker'): continue
        if base(o) in ('pad_slab', 'pad_apron', 'pad_strip', 'apron_joint', 'apron_joint_r', 'rim_tile', 'lt_plinth', 'lt_plinth_glow', 'lt_sill'): continue
        for v in wverts(o):
            u, t = UT(v)
            if WK_U0 <= u <= DOOR_U - 0.02 and abs(t) <= WK_T and PL_Z + 0.01 < v.z < 2.3: blk.append(o.name); break
    REP['walkway_blockers'] = blk
    # crane: the free-360 jib (15 m at z 20) vs the tower
    cr = Vector((G['CR_X'], G['CR_Y'], 0)); tw_c = P((TW_U0 + TW_U1) / 2, 0, 0)
    d_cr = min((cr - P(u, t, 0)).length for u in (TW_U0, TW_U1) for t in (-TW_T, TW_T))
    bearing = math.degrees(math.atan2(tw_c.y - cr.y, tw_c.x - cr.x))
    REP['crane'] = {'nearest_tower_corner_m': round(d_cr, 2), 'jib_m': G['CR_JIB_L'], 'tower_bearing_deg': round(bearing, 1),
                    'operational_arc_deg': [90.1, 228.8], 'note': 'jib tip clears the tower by %.2f m at its closest bearing; keep-out recommended %.0f-%.0f deg' % (d_cr - G['CR_JIB_L'], bearing - 12, bearing + 12)}
    # tris (raw master geometry, before bevel modifiers / game decimation) per Lv1 part
    REP['tris'] = {g: sum(tris(o) for o in L_) for g, L_ in new.items()}
    REP['tris']['Hoses_rebuilt'] = sum(tris(o) for o in bpy.data.objects if o.get('grp') in ('Hose_LOX', 'Hose_LCH4'))
    REP['tris']['L1_Queue_proof_figures'] = sum(tris(o) for o in bpy.data.objects if o.get('grp') == 'L1_Queue')
    def mats(L_): return sorted(set(m.name.split('.')[0] for o in L_ if o.type == 'MESH' for m in o.data.materials if m))
    REP['materials'] = {g: mats(L_) for g, L_ in new.items()}
    S = Vector((0, G['SHIFT'], 0))
    REP['walkway'] = {'start_gltf': gl(P(WK_U0, 0, PL_Z)), 'end_door_sill_gltf': gl(P(DOOR_U, 0, PL_Z)), 'deck_end_gltf': gl(P(WK_U1, 0, PL_Z)),
                      'length_to_door_m': round(DOOR_U - WK_U0, 2), 'deck_m': round(WK_U1 - WK_U0, 2), 'plinth_run_m': round(DOOR_U - WK_U1, 2),
                      'width_m': 2 * WK_T, 'top_y': PL_Z, 'queue_spots_gltf': [gl(P(u, 0, PL_Z)) for u in QUEUE], 'spacing_m': CREW_GAP,
                      'last_crew_back_u': round(q_lo, 2), 'facing': 'lift car (+u, glTF (%.3f, 0, %.3f))' % (LU.x, -LU.y)}
    REP['arm'] = {'deck_u': [ARM_U0, round(A1, 2)], 'length_m': round(A1 - ARM_U0, 2), 'deck_top_y': LAD_TOP, 'deck_width_m': 2 * ARM_T,
                  'clear_between_rails_m': round(arm_clear, 3), 'two_crew_abreast_m': round(two_abreast, 2), 'gap_each_rail_m': round(rail_gap, 3),
                  'landing_clear_m': round(land_clear, 3), 'hatch_doorway_m': 1.30, 'hinge_gltf': gl(HINGE)}
    REP['cab'] = {'clear_floor_m': [2 * CAB_T, round(CAB_U1 - CAB_U0, 2)], 'clear_height_m': 2.3, 'door_opening_m': [2 * DOOR_T, DOOR_H],
                  'doors_face': 'the access arm: -u = toward the ship, glTF (%.3f, 0, %.3f)' % (-LU.x, LU.y), 'pocket_each_side_m': POCKET_T1 - POCKET_T0,
                  'panel_stack_m': 0.37 + 0.035, 'car_outer_m': [CAR_DEPTH, 2 * POCKET_T1, 2.50], 'shaft_clear_m': [round(2 * (TW_COL_T - TW_COL_R), 2), round(TW_COL_U[1] - TW_COL_U[0] - 2 * TW_COL_R, 2)],
                  'stops_y': [PL_Z, LAD_TOP], 'rise_m': round(LAD_TOP - PL_Z, 2), 'ride': 'ElevatorUp 10 s / ElevatorDown 8 s / DoorsOpen 1.5 s / DoorsClose 1.5 s, all eased (spec only)'}
    REP['tower'] = {'footprint_u_t': [[TW_U0, TW_U1], [-TW_T, TW_T]], 'top_y': HH_TOP + 1.45, 'centre_gltf': gl(tw_c), 'plinth_u_t': [[PL_U0, PL_U1], [-PL_T, PL_T]]}
    REP['tank_farm'] = {'LOX_gltf': gl(LOX_P), 'LCH4_gltf': gl(LCH4_P), 'slab_centre_gltf': gl(C), 'slab_m': [2 * TF_HALF[0], 2 * TF_HALF[1]], 'bearing_deg': math.degrees(TF_A)}
    G['LV1_NODES'] = {'L1_Tower': 'LaunchTower', 'L1_Arm': 'CrewArm', 'L1_Elevator': 'ElevatorCar', 'L1_Walkway': 'QueueWalkway', 'L1_Queue': 'QueueCrew_Proof'}
    G['LV1_REPORT'] = REP
    print('LV1REPORT', json.dumps(REP), flush=True)
    out = os.path.join(G['OUT'], 'lv1_layout.json'); json.dump(REP, open(out, 'w'), indent=1)
    return REP
