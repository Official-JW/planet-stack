"""Game-weight stainless starter ship for the launch pad GLB (replaces the gray placeholder massing; Jacob 10/23 23:43, spec 10/24 00:06).

Built from the committed starter ship master (46a9346 starter_ship_master.glb) via starter_ship_46a9346_exterior.glb
(lp_extract_starter.py keeps the exterior parts only; the starter_ship folder is never edited or imported directly):
  * hull / steel bands / weld rings / solar band / glow rings / aft skirt + dome / nose + nose cap: their radii and heights are read
    from the starter meshes and re-lathed on a 12-sheet grid (thin vertical seams + 2.3 m course welds = panel lines);
  * engine bells, legs (pads, struts, braces, fairings, knuckles), raceways, RCS blocks, radiator + aft tiles: the starter meshes,
    decimated per group;
  * the crew ladder, cage, airlock hatch and hatch deck keep the placeholder's exact geometry and positions (crew boarding uses them).
Pad frame: starter yaw + 60 deg (cargo door 215 -> 275, airlock 275 -> ~335, ladder kept at 330), hull z + 0.5 (TOP + 0.25) so the
height, nose tip (TOP + 40.25) and leg footprint (r 9.25) match the placeholder; legs are stretched 3 % in z so the pads stay on the pad top.
Everything merges into ONE game node (Ship_Placeholder, one SHM_Stainless primitive); the face materials below pick the per-face
vertex-colour swatch in the game GLB (MT table in build_launch_pad.py) and the look in the Blender proofs.
"""
import math, os, random
from mathutils import Vector, Matrix

SRC = 'starter_ship_46a9346_exterior.glb'
DZ = 0.25                                 # on the pad the hull stands TOP + 0.25 above the starter frame (placeholder convention)

def build(G):
    import bpy, bmesh
    M_paint, _obj, lathe, rod, box, rbox, curve_tube = (G[k] for k in ('M_paint', '_obj', 'lathe', 'rod', 'box', 'rbox', 'curve_tube'))
    TOP, R, PSI, DOOR_A, LAD_A, TAU = G['TOP'], G['SHIP_R'], G['SHIP_PSI'], G['DOOR_A'], G['LAD_A'], 2 * math.pi
    SILL, DOOR_H, DOOR_HW, LAD_TOP, SATIN, CELL = G['SILL'], G['DOOR_H'], G['DOOR_HW'], G['LAD_TOP'], G['SATIN'], G['M_cell']
    LU, LT = G['LU'], G['LT']
    ZS = TOP + DZ                                                       # starter z -> pad z for hull-mounted parts
    M = {
        'A': M_paint('LP_StainlessA', '#cdd1d5', rough=0.36, metal=0.55, grime=0.10, grime_col='#8c9197', bevel=0.0),
        'B': M_paint('LP_StainlessB', '#d6dade', rough=0.42, metal=0.55, grime=0.10, grime_col='#8c9197', bevel=0.0),
        'C': M_paint('LP_StainlessC', '#c4c8cd', rough=0.48, metal=0.55, grime=0.12, grime_col='#8c9197', bevel=0.0),
        'weld': M_paint('LP_StainlessWeld', '#8d939a', rough=0.55, metal=0.5, bevel=0.0),
        'band': M_paint('LP_SteelBand', '#b3b8be', rough=0.32, metal=0.6, bevel=0.0),
        'heat': M_paint('LP_StainlessHeat', '#6d6a68', rough=0.5, metal=0.5, grime=0.3, grime_col='#3a3633', bevel=0.0),
        'dark': M_paint('LP_ShipDark', '#454b52', rough=0.45, metal=0.5, bevel=0.0),
        'bay': M_paint('LP_ShipBay', '#1c1f23', rough=0.6, metal=0.2, bevel=0.0),
        'glow': M_paint('LP_ShipGlow', '#5fd9ef', rough=0.4, metal=0.2, bevel=0.0),
        'solar': M_paint('LP_ShipSolar', '#687cc4', rough=0.35, metal=0.3, bevel=0.0),   # mid-blue solar band (Director 10/24 ship tone fix; was the navy LP_SolarCell)
    }
    SLOT = ['A', 'B', 'C', 'weld', 'band', 'heat', 'dark', 'bay', 'glow', 'solar']
    # ---- import the starter exterior parts (temp collection, removed afterwards)
    before = set(bpy.data.objects); mats0 = set(bpy.data.materials)
    bpy.ops.import_scene.gltf(filepath=os.path.join(G['HERE'], SRC))
    src = [o for o in bpy.data.objects if o not in before]
    parts = {}
    for o in src:
        if o.type != 'MESH': continue
        me = o.data.copy(); me.transform(o.matrix_world); parts.setdefault(o.name.split('.')[0], []).append(me)
    for o in src: bpy.data.objects.remove(o)
    def zr(n):   # z range + max radius of a starter part (starter frame)
        zs = [v.co.z for me in parts[n] for v in me.vertices]; rs = [math.hypot(v.co.x, v.co.y) for me in parts[n] for v in me.vertices]
        return min(zs), max(zs), max(rs)
    def rings(n):  # one entry per object (bands / welds are separate objects)
        out = []
        for me in parts[n]:
            zs = [v.co.z for v in me.vertices]; rs = [math.hypot(v.co.x, v.co.y) for v in me.vertices]
            out.append((min(zs), max(zs), max(rs)))
        return sorted(out)
    BANDS, WELDS = rings('SteelBand'), rings('WeldRing')
    SOL = zr('SolarBand'); GLOWS = [zr('SolarGlowLo')]                  # solar-band edge glow stays a hull row
    RINGS = [zr(n) for n in ('SkirtGlow', 'DeckGlow', 'BayGlow', 'UpperGlow')]   # 4 starter glow rings -> raised cyan rings (Director 10/24 00:26)
    HZ0, HZ1, _ = zr('Hull')
    # nose profile (Nose + NoseCap): max radius per z slice, resampled to 10 rows; tip clamped to the placeholder tip TOP + 40.25
    pts = [(v.co.z, math.hypot(v.co.x, v.co.y)) for n in ('Nose', 'NoseCap') for me in parts[n] for v in me.vertices]
    ztop = max(z for z, _ in pts)
    env = {}
    for zz, r in pts: k = round(zz, 2); env[k] = max(env.get(k, 0.0), r)
    env = sorted(env.items())
    def r_at(z):   # silhouette radius: linear between the nearest starter vertex rings
        lo = max((e for e in env if e[0] <= z), default=env[0]); hi = min((e for e in env if e[0] >= z), default=env[-1])
        return lo[1] if hi[0] == lo[0] else lo[1] + (hi[1] - lo[1]) * (z - lo[0]) / (hi[0] - lo[0])
    NOSE = [(r_at(HZ1 + (ztop - 0.06 - HZ1) * t), HZ1 + (ztop - 0.06 - HZ1) * t) for t in [i / 10 for i in range(1, 11)]]
    print('STARTER hull', round(HZ0, 3), round(HZ1, 3), 'bands', [tuple(round(x, 3) for x in b) for b in BANDS], 'welds', [tuple(round(x, 3) for x in w) for w in WELDS],
          'solar', tuple(round(x, 3) for x in SOL), 'nose top', round(ztop, 3), flush=True)
    # ---- hull grid: columns (16 sheets, one smooth facet each + 0.08 m vertical seam) x profile rings
    NP, SEAM = 12, 0.04 / R
    cols = []
    for p in range(NP):
        a = DOOR_A + TAU * p / NP; cols += [(a - SEAM, 'seam'), (a + SEAM, None)]
    for a in (DOOR_A - DOOR_HW, DOOR_A + DOOR_HW): cols.append((a, None))
    cols = sorted((((a - DOOR_A + SEAM * 1.5) % TAU + DOOR_A - SEAM * 1.5, t) for a, t in cols), key=lambda c: c[0])
    angs = [a for a, _ in cols]
    # rows (starter frame z): bands (relief), solar band (relief), weld rings + course welds, glow rings, door sill/top
    zband = [(z0, z1, r) for z0, z1, r in BANDS]
    ev = [HZ0, HZ1]
    for z0, z1, r in zband: ev += [z0, z0 + 0.03, z1 - 0.03, z1]
    ev += [SOL[0], SOL[0] + 0.03, SOL[1] - 0.03, SOL[1]]
    for z0, z1, r in WELDS: ev += [z0, z1]
    for z0, z1, r in GLOWS: ev += [z0, z1]
    ev += [SILL - ZS, SILL + DOOR_H - ZS]
    occupied = [(b[0] - 0.15, b[1] + 0.15) for b in zband] + [(SOL[0] - 0.15, SOL[1] + 0.15)] + [(g[0] - 0.15, g[1] + 0.15) for g in GLOWS] + [(w[0] - 0.15, w[1] + 0.15) for w in WELDS]
    lo = HZ0
    for z in sorted([b[0] for b in zband] + [SOL[0], HZ1]):
        n = max(1, round((z - lo) / 2.3))
        for i in range(1, n):
            zz = lo + (z - lo) * i / n
            if not any(a < zz < b for a, b in occupied) and min(abs(zz - (SILL - ZS)), abs(zz - (SILL + DOOR_H - ZS))) > 0.2: ev += [zz - 0.04, zz + 0.04]
        lo = z
    ev = sorted(set(round(z, 4) for z in ev if HZ0 - 1e-4 <= z <= HZ1 + 1e-4))
    def rad(z):
        for z0, z1, r in zband + [SOL]:
            if z0 + 0.03 - 1e-4 <= z <= z1 - 0.03 + 1e-4: return r
        return R
    _, sk1, skr = zr('AftSkirt'); dz0, dz1, dr = zr('AftDome'); sk0 = zr('AftSkirt')[0]
    prof = [(0.0, dz0), (dr * 0.6, dz0 + 0.12), (dr, dz1 - 0.05), (skr - 0.06, sk0 + 0.05), (skr, sk0 + 0.05), (skr, sk1 - 0.03), (R, sk1)]
    prof += [(rad(z), z) for z in ev if z > sk1 + 1e-3] + NOSE + [(0.0, TOP + 40.25 - ZS)]       # apex on the placeholder tip (starter cap 39.95 -> 40.0)
    prof = [(r, z + ZS) for r, z in prof]
    assert max(z for _, z in prof) <= TOP + 40.25 + 1e-3, 'nose tip above the placeholder tip'
    rnd = random.Random(46); tone = {}; hull_rings = []
    def ftag(z0, z1, r0, r1, ai):
        zm = (z0 + z1) / 2 - ZS; am = (angs[ai] + angs[(ai + 1) % len(angs)] + (TAU if ai == len(angs) - 1 else 0)) / 2
        if zm < HZ0 - 0.02: return 'heat' if max(r0, r1) < skr - 0.05 or zm < sk0 + 0.04 else 'dark'
        if any(b[0] <= zm <= b[1] for b in zband): return 'band'
        if SOL[0] <= zm <= SOL[1]: return 'solar'
        if any(g[0] <= zm <= g[1] for g in GLOWS): return 'glow'
        dd = (am - DOOR_A + math.pi) % TAU - math.pi
        if SILL - ZS < zm < SILL + DOOR_H - ZS and abs(dd) < DOOR_HW: return 'bay'
        if any(w[0] <= zm <= w[1] for w in WELDS) or (z1 - z0 < 0.09 and r0 > 0.5): return 'weld'
        if cols[ai][1] == 'seam': return 'weld'
        k = (int(zm / 2.3), int(((am - DOOR_A) % TAU) / (TAU / NP)))
        if k not in tone: tone[k] = rnd.choice('AABBBC')
        return tone[k]
    bm = bmesh.new(); rr = []
    for r, z in prof:
        rr.append([bm.verts.new((0, 0, z))] if r < 1e-5 else [bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for a in angs])
    nA = len(angs)
    for (ra, za), (rb, zb), A, B in zip(prof, prof[1:], rr, rr[1:]):
        for k in range(nA):
            k2 = (k + 1) % nA
            f = bm.faces.new((A[0], B[k], B[k2]) if len(A) == 1 else (A[k], A[k2], B[0]) if len(B) == 1 else (A[k], A[k2], B[k2], B[k]))
            f.material_index = SLOT.index(ftag(za, zb, ra, rb, k))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    hull = _obj(bm, 'ship_ss_hull', M[SLOT[0]], smooth=True, bevel=0.0, angle=40)
    for s in SLOT[1:]: hull.data.materials.append(M[s])
    # ---- 4 cyan glow rings: 0.18 m tall, 0.03 m proud of the steel band they sit on (outer r 4.06, 6 cm off the bare hull), 32 sides.
    # They clear the ladder (rails at u 4.42+), the hatch (z TOP+21.5..23.5) and the cargo door opening (z SILL..SILL+DOOR_H), so no breaks are needed.
    RING_H, RING_P = 0.18, 0.03
    for z0, z1, _ in RINGS:
        zc = (z0 + z1) / 2 + ZS; rb = rad(zc - ZS); ro = rb + RING_P
        assert not (SILL - 0.05 < zc + RING_H / 2 and zc - RING_H / 2 < SILL + DOOR_H + 0.05) and not (LAD_TOP - 0.2 < zc + RING_H / 2 and zc - RING_H / 2 < LAD_TOP + 2.0)
        hull_rings.append(lathe('ship_ss_glow_ring', [(rb - 0.01, zc - RING_H / 2), (ro, zc - RING_H / 2), (ro, zc + RING_H / 2), (rb - 0.01, zc + RING_H / 2)],
                                (0, 0, 0), M['glow'], segs=32, smooth=False))
    print('SHIPRINGS', [(round(o.data.vertices[0].co.z, 3)) for o in hull_rings], 'h', RING_H, 'proud', RING_P, flush=True)
    out = [hull] + hull_rings; print('SHIPHULL tris', sum(len(p.vertices) - 2 for p in hull.data.polygons), 'rows', len(prof), 'cols', nA, flush=True)
    # ---- starter meshes: rotate +60 deg, lift, merge per group, decimate to the group budget
    ROT = Matrix.Rotation(PSI, 4, 'Z')
    LEGK = 1.0 + DZ / 8.2                                             # legs: pads stay on the pad top, hips follow the hull up
    GROUPS = [  # (name, [(part, material)], z mode, target tris)
        ('ship_ss_bells', [('EngineBell', 'heat'), ('EngineBellLip', 'dark')], 'hull', 320),
        ('ship_ss_legs', [('LegPad', 'dark'), ('LegStrut_body', 'dark'), ('LegStrut_gland', 'band'), ('LegStrut_rod', 'band'),
                          ('LegBrace', 'dark'), ('LegFairing', 'B'), ('LegKnuckle', 'dark')], 'leg', 820),   # 900 -> 820: room for the hatch landing (10/24 00:32)
        ('ship_ss_raceway', [('Raceway', 'dark')], 'hull', 120),
        ('ship_ss_rcs', [('RCSBlock', 'dark')], 'hull', 120),
        ('ship_ss_tiles', [('RadiatorTiles', 'dark'), ('AftTilesBack', 'dark')], 'hull', 120),
    ]
    for name, plist, zmode, tgt in GROUPS:
        bm = bmesh.new()
        for pn, mk in plist:
            for me in parts.get(pn, []):
                t = bmesh.new(); t.from_mesh(me)
                for f in t.faces: f.material_index = SLOT.index(mk)
                for v in t.verts:
                    p = ROT @ v.co
                    v.co = Vector((p.x, p.y, TOP + p.z * LEGK if zmode == 'leg' else p.z + ZS))
                me2 = bpy.data.meshes.new('tmp'); t.to_mesh(me2); t.free(); bm.from_mesh(me2); bpy.data.meshes.remove(me2)
        o = _obj(bm, name, M[SLOT[0]], smooth=True, bevel=0.0, angle=40)
        for s in SLOT[1:]: o.data.materials.append(M[s])
        n0 = sum(len(p.vertices) - 2 for p in o.data.polygons)
        if n0 > tgt:
            md = o.modifiers.new('Dec', 'DECIMATE'); md.ratio = tgt / n0; md.use_collapse_triangulate = True
            bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name)
        print('SHIPGROUP', name, n0, '->', sum(len(p.vertices) - 2 for p in o.data.polygons), flush=True)
        out.append(o)
    for mes in parts.values():
        for me in mes: bpy.data.meshes.remove(me)
    for m in set(bpy.data.materials) - mats0:
        if m.users == 0: bpy.data.materials.remove(m)
    # ---- crew ladder + cage + airlock hatch + hatch deck: the placeholder's exact geometry and positions (crew boarding)
    for s in (-0.28, 0.28):
        q = LU * 4.45 + LT * s; out.append(rod('ship_ph_ladder', (q.x, q.y, TOP), (q.x, q.y, LAD_TOP), 0.035, SATIN, segs=6))
    for i in range(int((LAD_TOP - TOP - 0.3) / 0.6)):
        q = LU * 4.45; z = TOP + 0.4 + i * 0.6
        out.append(box('ship_ph_rung', (0.05, 0.56, 0.05), (q.x, q.y, z), SATIN, rot=(0, 0, LAD_A), bevel=0))
    for i in range(12):
        z = TOP + 3.2 + i * 1.6
        pts_ = [tuple(LU * 4.45 + LU * 0.75 * math.sin(t) + LT * 0.5 * math.cos(t) + Vector((0, 0, z))) for t in (math.pi * k / 6 for k in range(7))]
        out.append(curve_tube('ship_ph_cage', pts_, 0.025, SATIN, res=1))
    for s in (-0.4, 0, 0.4):
        a_ = LU * 4.45 + LU * 0.75 * (1 if s == 0 else 0.6) + LT * s
        out.append(rod('ship_ph_cage_bar', (a_.x, a_.y, TOP + 3.2), (a_.x, a_.y, LAD_TOP), 0.025, SATIN, segs=4))
    # hatch panel: outer face stays at u 4.06 (doorway / jamb edges unchanged); inner face pushed in to u 3.80 so the panel sits flush with the
    # faceted hull under its whole width (the flat hull sheet is at u ~3.82-3.89 at |t| 0.65; the old 0.12 m panel left a ~5 cm gap there)
    HT = 0.26; hq = LU * (R + 0.06 - HT / 2)
    out.append(rbox('ship_ph_hatch', (HT, 1.3, 2.0), (hq.x, hq.y, LAD_TOP + 0.9), M['dark'], rot=(0, 0, LAD_A), r=0.04, segs=1))
    # ---- hatch landing (art lead 10/24 00:32, option 1): the old solid 1.0 x 1.4 deck (u 4.25-5.25, t +-0.70) is replaced by a U-shaped
    # stainless landing with a ladder well cut through it. Climbers come up through the well, step off sideways onto the wings
    # (stand ~t +-0.9, u 4.3-4.7) and walk along the hull into the hatch. Deck top stays at LAD_TOP (21.85).
    W_U0, W_U1, W_T = 4.05, 5.15, 0.62           # ladder well (clear opening)
    D_U1, D_T, D_Z0 = 5.45, 1.40, LAD_TOP - 0.10  # deck outer edge, half width, underside
    FW, KZ = 0.06, LAD_TOP + 0.03                 # graphite frame width, kerb top
    hull_u = lambda t: math.sqrt(R * R - t * t) - 0.03   # tuck the inner edge 3 cm into the hull skin
    P = lambda u, t, z: tuple(LU * u + LT * t + Vector((0, 0, z)))
    def prism(name, poly, z0, z1, mat):
        bm = bmesh.new(); lo = [bm.verts.new(P(u, t, z0)) for u, t in poly]; hi = [bm.verts.new(P(u, t, z1)) for u, t in poly]
        bm.faces.new(hi); bm.faces.new(lo[::-1])
        for i in range(len(poly)): j = (i + 1) % len(poly); bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
        return _obj(bm, name, mat, smooth=False)
    for sg in (-1, 1):   # deck wings (stainless), inner edge follows the hull
        ts = [W_T + (D_T - W_T) * k / 3 for k in range(4)]
        poly = [(hull_u(t), sg * t) for t in ts] + [(D_U1, sg * D_T), (D_U1, sg * W_T)]
        out.append(prism('ship_ph_hatch_deck', poly if sg > 0 else poly[::-1], D_Z0, LAD_TOP, M['band']))
    out.append(prism('ship_ph_hatch_deck', [(W_U1, -W_T), (D_U1, -W_T), (D_U1, W_T), (W_U1, W_T)], D_Z0, LAD_TOP, M['band']))   # outer bridge
    # slim graphite well frame: kerb 3 cm proud of the deck, coaming 9 cm below it
    for sg in (-1, 1):
        out.append(prism('ship_ph_hatch_frame', [(hull_u(W_T), sg * W_T), (W_U1 + FW, sg * W_T), (W_U1 + FW, sg * (W_T + FW)), (hull_u(W_T + FW), sg * (W_T + FW))][::sg], LAD_TOP - 0.19, KZ, M['dark']))
    out.append(prism('ship_ph_hatch_frame', [(W_U1, -W_T), (W_U1 + FW, -W_T), (W_U1 + FW, W_T), (W_U1, W_T)], LAD_TOP - 0.19, KZ, M['dark']))
    # graphite edge beam under the deck perimeter + two braces back to the hull
    out.append(prism('ship_ph_hatch_beam', [(D_U1 - 0.07, -D_T), (D_U1, -D_T), (D_U1, D_T), (D_U1 - 0.07, D_T)], LAD_TOP - 0.24, D_Z0, M['dark']))
    for sg in (-1, 1):
        out.append(prism('ship_ph_hatch_beam', [(hull_u(D_T - 0.07), sg * (D_T - 0.07)), (D_U1 - 0.07, sg * (D_T - 0.07)), (D_U1 - 0.07, sg * D_T), (hull_u(D_T), sg * D_T)][::sg], LAD_TOP - 0.24, D_Z0, M['dark']))
        out.append(rod('ship_ph_hatch_brace', P(D_U1 - 0.04, sg * (D_T - 0.04), LAD_TOP - 0.22), P(hull_u(1.0) + 0.02, sg * 1.0, LAD_TOP - 1.35), 0.03, M['dark'], segs=6))
    # open lid: hinged on the outer well edge, swung 100 deg up so it leans 10 deg outboard and doubles as the back guard
    HU, HZ, LL, OPEN = W_U1 + FW + 0.035, KZ + 0.02, 1.16, math.radians(100)
    d = Vector((math.cos(math.pi - OPEN), math.sin(math.pi - OPEN)))           # (u, z) direction hinge -> free edge
    c = (HU + d.x * LL / 2, HZ + d.y * LL / 2); q = LU * c[0]
    out.append(rbox('ship_ph_hatch_lid', (LL, 1.30, 0.05), (q.x, q.y, c[1]), M['dark'], rot=(0, -(math.pi - OPEN), LAD_A), r=0.015, segs=1))
    for tt in (-0.3, 0.3):   # stainless stiffeners on the lid's outboard face
        nrm = Vector((d.y, -d.x)); a0 = Vector((HU, HZ)) + nrm * 0.035 + d * 0.08; a1 = Vector((HU, HZ)) + nrm * 0.035 + d * (LL - 0.08)
        out.append(rod('ship_ph_hatch_lid_rib', P(a0.x, tt, a0.y), P(a1.x, tt, a1.y), 0.022, M['band'], segs=4))
    out.append(rod('ship_ph_hatch_hinge', P(HU, -0.62, HZ), P(HU, 0.62, HZ), 0.035, M['band'], segs=6))
    for tt in (-0.52, 0.52):  # hold-open struts
        a1 = Vector((HU, HZ)) + Vector((d.y, -d.x)) * 0.03 + d * 0.62
        out.append(rod('ship_ph_hatch_strut', P(D_U1 - 0.05, tt, LAD_TOP + 0.01), P(a1.x, tt, a1.y), 0.018, SATIN, segs=4))
    # guard rail: two L runs (outer edge |t| 0.76-1.34 + wing ends u 4.15-5.40); step-off sides and the hull walkway stay open
    RU, RT0, RT1, RH = D_U1 - 0.05, 0.76, D_T - 0.06, 1.05
    for sg in (-1, 1):
        A_, B_, C_ = (4.15, sg * RT1), (RU, sg * RT1), (RU, sg * RT0)
        for pu, pt in (A_, ((A_[0] + B_[0]) / 2, A_[1]), B_, C_):
            out.append(rod('ship_ph_hatch_rail', P(pu, pt, LAD_TOP), P(pu, pt, LAD_TOP + RH), 0.028, SATIN, segs=6))
        for h, r_ in ((RH, 0.032), (RH * 0.5, 0.024)):
            out.append(rod('ship_ph_hatch_rail', P(A_[0], A_[1], LAD_TOP + h), P(B_[0], B_[1], LAD_TOP + h), r_, SATIN, segs=6))
            out.append(rod('ship_ph_hatch_rail', P(B_[0], B_[1], LAD_TOP + h), P(C_[0], C_[1], LAD_TOP + h), r_, SATIN, segs=6))
    LANDING = {'frame': 'pad-local, u along ladder axis LU (330 deg) from ship centre, t = LT, z up (glTF y)',
               'deck_u_t_z': [[round(hull_u(D_T), 3), D_U1], [-D_T, D_T], [round(D_Z0, 3), LAD_TOP]],
               'well_u_t_z': [[W_U0, W_U1], [-W_T, W_T], [round(D_Z0, 3), LAD_TOP]],
               'frame_u_t_z': [[round(hull_u(W_T + FW), 3), W_U1 + FW], [-(W_T + FW), W_T + FW], [round(LAD_TOP - 0.19, 3), round(KZ, 3)]],
               'stand_area_u_t_z': [[4.30, 4.70], ['+-0.75', '+-1.25'], LAD_TOP],
               'rail_u_t_z': [[4.15, RU], ['+-%.2f..%.2f' % (RT0, RT1)], [LAD_TOP, LAD_TOP + RH + 0.032]],
               'lid_hinge_u_z': [round(HU, 3), round(HZ, 3)], 'lid_open_deg': 100, 'lid_t': [-0.65, 0.65]}
    print('SHIPLANDING', LANDING, flush=True)
    POS = {'ladder_rails_xy_m': [tuple(round(c, 3) for c in (LU * 4.45 + LT * s).xy) for s in (-0.28, 0.28)], 'ladder_z_m': [TOP, LAD_TOP],
           'hatch_center_m': tuple(round(c, 3) for c in (LU * R).xy) + (round(LAD_TOP + 0.9, 3),), 'hatch_deck_m': tuple(round(c, 3) for c in (LU * 4.75).xy) + (round(LAD_TOP - 0.05, 3),), 'hatch_landing': LANDING}
    print('SHIPPOS', POS, flush=True)
    print('SHIPLADDER tris', sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in out[6:] if o.type == 'MESH'), flush=True)
    return [o.name for o in out], M
