"""Closed cargo door CD-1 for the stainless pad ship (Director 10/24 11:22, agreed with Art Assistant for the Lv2 ship).
Used when build_launch_pad.py runs with --door 1 (default for --level >= 1). Keeps the Lv0 opening exactly: DOOR_A 275 deg (pad frame),
half-width DOOR_HW 23.8 deg on the R 4.0 hull, z SILL .. SILL + DOOR_H. The hull's opening faces (LP_ShipBay) are not built at --door 1.
Geometry follows the real hull facets (two 23.2 deg sheets + the 0.08 m weld seam at DOOR_A), offsets along each facet normal:
  panel   LP_DoorPanel   #8a9097, weathered (grime + edge wear), front 2 cm INSIDE the hull skin, one 2 cm horizontal seam at mid-height
  frame   LP_ShipGraphite #2b2f35, 8 cm wide all round, front 2 cm PROUD of the hull                         (ship node, static)
  hinges  LP_ShipGraphite, 3 barrels d 6 cm x 18 cm on the LEFT edge seen from outside, 15 cm in from top/bottom (ship node, static)
  light   LP_ShipGlow (the ring material, painted, game swatch #2fe3ff), 3 cm wide, top + both sides just inside the frame, front 1 cm proud of the frame
  latch   LP_ShipGraphite recessed handle on the RIGHT edge at mid-height, 20 x 6 cm pocket, 1.5 cm deep
  liner   LP_ShipDark hold back wall 0.6 m inside (only seen when the door is open)                         (ship node)
"""
import math
import bmesh, bpy
from mathutils import Vector

FW, CW, INSET, PROUD, LIGHT_P = 0.08, 0.03, 0.02, 0.02, 0.01
HINGE_D, HINGE_L, HINGE_IN = 0.06, 0.18, 0.15
LATCH_H, LATCH_W, LATCH_D, LATCH_IN = 0.20, 0.06, 0.015, 0.05
SEAM_W = 0.02


def build(G):
    M_paint, _obj = G['M_paint'], G['_obj']
    R, DOOR_A, HW, SILL, DH, SSM = G['SHIP_R'], G['DOOR_A'], G['DOOR_HW'], G['SILL'], G['DOOR_H'], G['SSM']
    MP = M_paint('LP_DoorPanel', '#8a9097', rough=0.55, metal=0.4, grime=0.28, grime_col='#6d6962', wear=0.35, wear_col='#b9bec4', bevel=0.004)
    MG = M_paint('LP_ShipGraphite', '#2b2f35', rough=0.5, metal=0.35, grime=0.12, grime_col='#4a4741', wear=0.2, wear_col='#6c727a', bevel=0.004)
    MGL = SSM['glow']
    SEAMA = 0.04 / R
    angs = [DOOR_A - HW, DOOR_A - SEAMA, DOOR_A + SEAMA, DOOR_A + HW]            # the hull's own columns across the opening
    P = [Vector((R * math.cos(a), R * math.sin(a), 0)) for a in angs]
    seg = list(zip(P, P[1:])); L = [(b - a).length for a, b in seg]; S = sum(L)
    nrm = [Vector((-(b - a).y, (b - a).x, 0)).normalized() for a, b in seg]
    nrm = [n if n.dot(a) > 0 else -n for n, (a, b) in zip(nrm, seg)]          # outward
    cum = [0.0]
    for l in L: cum.append(cum[-1] + l)
    def pt(s, off):
        s = min(max(s, 0.0), S)
        i = min(len(L) - 1, max(k for k in range(len(L)) if cum[k] <= s + 1e-9))
        t = (s - cum[i]) / L[i]; p = seg[i][0].lerp(seg[i][1], t)
        if abs(s - cum[i]) < 1e-6 and i > 0: n = (nrm[i] + nrm[i - 1]).normalized(); n = n / n.dot(nrm[i])
        elif abs(s - cum[i + 1]) < 1e-6 and i < len(L) - 1: n = (nrm[i] + nrm[i + 1]).normalized(); n = n / n.dot(nrm[i])
        else: n = nrm[i]
        return p + n * off
    def slab(name, s0, s1, z0, z1, off_f, off_b, mat):
        ss = [s0] + [c for c in cum if s0 + 1e-4 < c < s1 - 1e-4] + [s1]
        bm = bmesh.new()
        F = [[bm.verts.new(pt(s, off_f) + Vector((0, 0, z))) for s in ss] for z in (z0, z1)]
        B = [[bm.verts.new(pt(s, off_b) + Vector((0, 0, z))) for s in ss] for z in (z0, z1)]
        n = len(ss)
        for k in range(n - 1):
            bm.faces.new((F[0][k], F[0][k + 1], F[1][k + 1], F[1][k]))      # front
            bm.faces.new((B[0][k + 1], B[0][k], B[1][k], B[1][k + 1]))      # back
            bm.faces.new((F[1][k], F[1][k + 1], B[1][k + 1], B[1][k]))      # top
            bm.faces.new((B[0][k], B[0][k + 1], F[0][k + 1], F[0][k]))      # bottom
        bm.faces.new((B[0][0], F[0][0], F[1][0], B[1][0])); bm.faces.new((F[0][-1], B[0][-1], B[1][-1], F[1][-1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return _obj(bm, name, mat, smooth=False, bevel=0.0)
    zb, zt = SILL, SILL + DH; zm = (zb + zt) / 2
    door, ship = [], []
    # ---- static (ship node): frame, hinge barrels, hold liner
    ship.append(slab('cd_frame', 0, FW, zb, zt, PROUD, -0.06, MG)); ship.append(slab('cd_frame', S - FW, S, zb, zt, PROUD, -0.06, MG))
    ship.append(slab('cd_frame', FW, S - FW, zt - FW, zt, PROUD, -0.06, MG)); ship.append(slab('cd_frame', FW, S - FW, zb, zb + FW, PROUD, -0.06, MG))
    ship.append(slab('cd_liner', FW, S - FW, zb + FW, zt - FW, -0.60, -0.64, SSM['dark']))
    hz = [zb + HINGE_IN + HINGE_L / 2, zm, zt - HINGE_IN - HINGE_L / 2]
    hp = pt(FW / 2, PROUD + HINGE_D / 2)
    for z in hz: ship.append(G['cyl']('cd_hinge', HINGE_D / 2, HINGE_L, (hp.x, hp.y, z), MG, segs=8, bevel=0.0))
    # ---- door node: back plate, two leaves (seam), latch pocket, cyan edge light
    door.append(slab('cd_panel_back', FW, S - FW, zb + FW, zt - FW, -INSET - LATCH_D, -0.07, MP))
    ls1 = S - FW - LATCH_IN; ls0 = ls1 - LATCH_W; lz0, lz1 = zm - LATCH_H / 2, zm + LATCH_H / 2
    for z0, z1 in ((zb + FW, zm - SEAM_W / 2), (zm + SEAM_W / 2, zt - FW)):
        door.append(slab('cd_panel', FW, ls0, z0, z1, -INSET, -INSET - LATCH_D, MP))
        door.append(slab('cd_panel', ls1, S - FW, z0, z1, -INSET, -INSET - LATCH_D, MP))
        a_, b_ = (z0, lz0) if z1 <= zm else (lz1, z1)
        door.append(slab('cd_panel', ls0, ls1, a_, b_, -INSET, -INSET - LATCH_D, MP))
    door.append(slab('cd_latch_pocket', ls0, ls1, lz0, lz1, -INSET - LATCH_D + 0.001, -INSET - LATCH_D - 0.002, MG))
    door.append(slab('cd_latch_grip', ls0 + 0.015, ls1 - 0.015, lz0 + 0.03, lz1 - 0.03, -INSET - 0.005, -INSET - LATCH_D + 0.001, MG))
    lf = PROUD + LIGHT_P
    door.append(slab('cd_light', FW, FW + CW, zb + FW, zt - FW, lf, -INSET, MGL))
    door.append(slab('cd_light', S - FW - CW, S - FW, zb + FW, zt - FW, lf, -INSET, MGL))
    door.append(slab('cd_light', FW + CW, S - FW - CW, zt - FW - CW, zt - FW, lf, -INSET, MGL))
    chord = (P[-1] - P[0]).length
    info = {'angle_deg_pad_frame': round(math.degrees(DOOR_A), 2), 'half_angle_deg': round(math.degrees(HW), 3),
            'width_chord_m': round(chord, 3), 'width_along_hull_m': round(S, 3), 'height_m': DH, 'sill_z_m': round(SILL, 3),
            'top_z_m': round(zt, 3), 'centre_z_m': round(zm, 3), 'hull_r_m': R,
            'panel_clear_m': [round(S - 2 * FW, 3), round(DH - 2 * FW, 3)], 'hinge_z_m': [round(z, 3) for z in hz],
            'latch_centre_z_m': round(zm, 3), 'glow_emission_strength': None}
    try:
        b = MGL.node_tree.nodes.get('Principled BSDF'); info['glow_emission_strength'] = round(b.inputs['Emission Strength'].default_value, 3)
        info['glow_material'] = MGL.name; info['glow_master_rgb'] = [round(x, 4) for x in b.inputs['Base Color'].default_value[:3]] if not b.inputs['Base Color'].is_linked else 'node'
    except Exception as e: info['glow_err'] = str(e)
    print('CARGODOOR', info, flush=True)
    G['CARGO_DOOR_INFO'] = info
    return door, ship
