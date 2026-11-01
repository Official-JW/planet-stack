"""Cockpit window band CW-1 for the stainless pad ship (Director 10/24 13:54; Lv1 ship file launch_pad_game_lv1ship.glb).
Used when build_launch_pad.py runs with --cockpit 1 (default 0, so launch_pad_game.glb / lv1door builds are unchanged).
4 panes on the two hull facets that carry the cargo door (DOOR_A 275 deg pad frame, faces the game camera at ~270 deg),
in the top clear hull course: above the UpperGlow ring / steel band (pad z 24.9..25.6) and below the course weld at pad z 27.48;
the only course directly under the nose (pad z 30.0..30.9, between solar band and top band) is 0.9 m tall -> pane < 4 px at 375x667.
  frame  LP_ShipGraphite #2b2f35, 7 cm wide, front 2.5 cm PROUD of the hull facet          (ship node)
  glass  LP_CockpitGlow  #ffb46a warm interior glow (--cockpit_glow 1, default) or LP_CockpitGlass #141b22 dark glass (--cockpit_glow 0),
         front 0.5 cm proud, i.e. recessed 2 cm inside the frame                             (ship node, +0 draws)
Runtime toggle (+0 draws): empty node Cockpit_Window (child of Ship_Placeholder) lists the glass boxes in Ship-node-local glTF;
recolour COLOR_0 of Ship vertices inside them (on #ffb46a / off #141b22), or swap to a 1-primitive mesh node with --cockpit_node 1 (+1 draw).
"""
import math
import bmesh
from mathutils import Vector

FW, PROUD, GLASS_F, GLASS_B = 0.07, 0.025, 0.005, -0.03
Z0, Z1 = 25.95, 27.15                     # glass, pad frame (z up); frame adds FW all round -> 25.88 .. 27.22
PANES_S = [(0.15, 0.73), (0.88, 1.46)]    # along each door facet from its outer column (mirrored on the second facet)


def build(G):
    M_paint, M_glow, _obj = G['M_paint'], G['M_glow'], G['_obj']
    R, DOOR_A, HW = G['SHIP_R'], G['DOOR_A'], G['DOOR_HW']
    MG = M_paint('LP_ShipGraphite', '#2b2f35', rough=0.5, metal=0.35, grime=0.12, grime_col='#4a4741', wear=0.2, wear_col='#6c727a', bevel=0.004)
    ON = G['A'].get('cockpit_glow', '1') == '1'
    MW = M_glow('LP_CockpitGlow', '#ffb46a', float(G['A'].get('cockpit_glow_k', 6))) if ON else \
        M_paint('LP_CockpitGlass', '#141b22', rough=0.08, metal=0.2, bevel=0.0)
    SEAMA = 0.04 / R
    facets = [(DOOR_A - HW, DOOR_A - SEAMA), (DOOR_A + SEAMA, DOOR_A + HW)]
    out, panes = [], []
    for fi, (a0, a1) in enumerate(facets):
        P0, P1 = (Vector((R * math.cos(a), R * math.sin(a), 0)) for a in (a0, a1))
        L = (P1 - P0).length; u = (P1 - P0) / L
        n = Vector((-u.y, u.x, 0)); n = n if n.dot(P0) > 0 else -n
        spans = PANES_S if fi == 0 else [(L - s1, L - s0) for s0, s1 in reversed(PANES_S)]
        def box(name, s0, s1, z0, z1, f, b, mat):
            bm = bmesh.new()
            V = [[bm.verts.new(P0 + u * s + n * o + Vector((0, 0, z))) for s in (s0, s1)] for o in (f, b) for z in (z0, z1)]
            (F0, F1, B0, B1) = V
            for q in ((F0[0], F0[1], F1[1], F1[0]), (B0[1], B0[0], B1[0], B1[1]), (F1[0], F1[1], B1[1], B1[0]), (B0[0], B0[1], F0[1], F0[0]),
                      (B0[0], F0[0], F1[0], B1[0]), (F0[1], B0[1], B1[1], F1[1])): bm.faces.new(q)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            return _obj(bm, name, mat, smooth=False, bevel=0.0)
        for s0, s1 in spans:
            out += [box('cw_frame', s0 - FW, s1 + FW, Z1, Z1 + FW, PROUD, -0.04, MG), box('cw_frame', s0 - FW, s1 + FW, Z0 - FW, Z0, PROUD, -0.04, MG),
                    box('cw_frame', s0 - FW, s0, Z0, Z1, PROUD, -0.04, MG), box('cw_frame', s1, s1 + FW, Z0, Z1, PROUD, -0.04, MG),
                    box('cw_glass', s0, s1, Z0, Z1, GLASS_F, GLASS_B, MW)]
            c = P0 + u * ((s0 + s1) / 2) + n * GLASS_F
            gv = [P0 + u * s_ + n * o_ for s_ in (s0, s1) for o_ in (GLASS_F, GLASS_B)]
            panes.append({'glass_xy': [[q.x, q.y] for q in gv], 'bearing_deg': round(math.degrees(math.atan2(c.y, c.x)) % 360, 2), 'width_m': round(s1 - s0, 3), 'height_m': round(Z1 - Z0, 3),
                          'centre_pad': [round(c.x, 3), round(c.y, 3), round((Z0 + Z1) / 2, 3)],
                          'corners_pad': [[round(q.x, 3), round(q.y, 3)] for q in (P0 + u * s0 + n * GLASS_F, P0 + u * s1 + n * GLASS_F)]})
    def gl(p): return [round(p[0], 3), round(p[2], 3), round(-p[1], 3)]   # pad frame -> Ship-node-local glTF (node origin = ship centre on the pad top frame)
    bb = []
    for p in panes:
        xs, ys = [q[0] for q in p['glass_xy']], [q[1] for q in p.pop('glass_xy')]       # all 4 plan corners of the glass box (front + back)
        lo, hi = gl((min(xs) - 0.01, max(ys) + 0.01, Z0 - 0.01)), gl((max(xs) + 0.01, min(ys) - 0.01, Z1 + 0.01))
        bb.append({'min': [min(a, b) for a, b in zip(lo, hi)], 'max': [max(a, b) for a, b in zip(lo, hi)]})
    cen = Vector([sum(p['centre_pad'][k] for p in panes) / len(panes) for k in range(3)])
    info = {'panes': len(panes), 'pane_w_m': panes[0]['width_m'], 'pane_h_m': round(Z1 - Z0, 3), 'glass_z_pad': [Z0, Z1],
            'frame_z_pad': [round(Z0 - FW, 3), round(Z1 + FW, 3)], 'bearings_deg': [p['bearing_deg'] for p in panes], 'glow_on': ON,
            'on_hex': '#ffb46a', 'off_hex': '#141b22', 'frame_material': 'LP_ShipGraphite', 'centre_pad': [round(x, 3) for x in cen],
            'glass_boxes_ship_local_gltf': bb}
    print('COCKPIT', info, flush=True)
    G['COCKPIT_INFO'] = info
    return out
