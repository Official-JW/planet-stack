#!/usr/bin/env python3
"""ST-10A transport road plan v5 (station order d729465: Cargo Space Dock 480 | Launch Pad 640 | Shipyard 800).  Supersedes road_plan.py (v4, pad 457).
Reads the check written by road_v5.py and the packed road GLB; writes ../proofs/transport_road_plan.json and, with --png (QUEUED: box hold, runs from
/workspace/st10a/queue_inner.sh), ../proofs/transport_road_plan_topdown.png.  WORLD glTF metres, +X right, +Z toward the camera (drawn DOWN).
  python3 road_plan_v5.py <road_v5_check.json> <st10a_transport_road.glb> [--png]"""
import hashlib, json, math, os, sys
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, '..', 'proofs')
CHK = json.load(open(sys.argv[1])); GLB = sys.argv[2]; b = open(GLB, 'rb').read()
plan = dict(version='v5', date='10/24/2026', order=CHK['order'], supersedes='v4 (road_plan.py, pad 457 -> Shipyard 960)',
    glb=dict(file='game/st10a_transport_road.glb', md5=hashlib.md5(b).hexdigest(), bytes=len(b), place_world=[669.5, 0, -13.0], rotation='none'),
    endpoints=dict(crawler_pickup_pad=[640.0, 0.25, -13.0], road_mesh_start_pad_right_edge=[669.5, 0.0, -13.0], road_end_shipyard_road_entry=[754.871, 0.23, 17.604],
                   crawler_stop=CHK['crawler_stop']),
    path=dict(CHK['centerline'], segments_m=dict(straight_640_to_682=42.0, arc_R100_40deg=round(100 * math.radians(40), 2), final_straight=11.21),
              length_pickup_to_road_entry_m=CHK['centerline']['length_m'], length_pickup_to_crawler_stop_m=CHK['crawler_stop']['s_m'],
              length_road_mesh_m=CHK['road']['mesh_length_m'], min_turn_radius_m=100.0, s_bends=0),
    road=dict(CHK['road'], shipyard_props_in_graded_band_note='full 39.82 m band before the end trim; the built mesh is trimmed (see road_mesh_vs_shipyard)',
              road_mesh_vs_shipyard=dict(props_over_0p32m_under_mesh=0, min_horizontal_gap_m=0.61, method='raw mesh triangles (world) vs shipyard_bcbd0934 triangles sampled 0.5 m, y > 0.32')), obstacles=CHK['obstacles'], inputs=CHK['inputs'],
    flags=[
     'PAD (db78a6f7, owner pad/AA2): no gate on the RIGHT. Berm Pad_Base 2.5-4.5 m tall, x 656-668, z -28..-2 crosses both crawler track bands -> gate G-1 needed, 30.8 m wide, z -28.4..2.4.',
     'PAD: two Pad_Base pylon blocks 9-12 m tall at x 654-658 / z -20..-16 and x 652-656 / z -6..-2 are inside the crawler + ship skirt/gear sweep east of the ship -> move or open them.',
     'PAD: Tier_08 (x 650-656, z -26.5..-22.5, 5.25 m) in the far track band; low Pad_Base items at x 628-630 z -24..-22 (1.8 m) under the crawler at pick-up.',
     'PAD: Hose_LOX / Hose_LCH4 (y <= 4.75) cross the skirt/gear sweep -> must disconnect / retract before the move (game state, not geometry).',
     'PAD: Pipe_LaunchPad_End (660.3, 0.95, -9.6) is on the pad RIGHT inside the crawler path (between the track bands, under the body); the Dock is now WEST (x 480) so the pipe should come in from the pad LEFT.',
     'SHIPYARD (bcbd0934): props at Road_Entry (shipyard_base x 752-767.5, z -2.5..14, up to 25.5 m) -> the 27.12 m crawler stops 9.04 m short of Road_Entry (leading face (748.64, 10.81)); the Lv10 bay / wider entry still needs a Shipyard change. The road mesh reaches Road_Entry; its far side is trimmed to the prop-free envelope from s 112.3.',
     'D-10: loaded height 44.55 m (Lv2 ship) leaves 1.45 m under D-10 (46 m) - unchanged flag.'],
    other_roads_rule='no crossing: flatbed z 23 / 32 lanes + pad U-turn are on the camera side (z >= 20.2); the crawler road stays z <= 6.91 west of x 700 and only bends toward +Z east of x 682 (no other road there).')
open(os.path.join(P, 'transport_road_plan.json'), 'w').write(json.dumps(plan, indent=1))
print(json.dumps(dict(glb=plan['glb'], length=plan['path']['length_pickup_to_road_entry_m']), indent=0))
if '--png' in sys.argv:
    from PIL import Image, ImageDraw
    import numpy as np
    sc = 4.0; X0, X1, Z0, Z1 = 600, 820, -60, 60; W, Hh = int((X1 - X0) * sc), int((Z1 - Z0) * sc)
    im = Image.new('RGB', (W, Hh), (24, 24, 28)); d = ImageDraw.Draw(im); T = lambda x, z: ((x - X0) * sc, (z - Z0) * sc)
    for x0, x1, z0, z1, c in ((610.6, 669.4, -46.87, 24.8, (70, 70, 80)), (748.02, 861.94, -36.47, 46.9, (80, 70, 60))): d.rectangle([T(x0, z0), T(x1, z1)], outline=c, width=2)
    for zc in (23, 32): d.rectangle([T(600, zc - 2.8), T(641, zc + 2.8)], fill=(90, 80, 50))
    d.ellipse([T(641 - 7.3, 27.5 - 7.3), T(641 + 7.3, 27.5 + 7.3)], outline=(140, 120, 60), width=3)
    cp = np.array(CHK.get('_cp', []))
    if len(cp): d.line([T(x, z) for x, z in cp], fill=(230, 200, 80), width=2)
    st = CHK['crawler_stop']; cx, cz = st['ship_axis']; h = math.radians(st['heading_deg'])
    cor = [(u, w) for u, w in ((-13.36, -13.56), (15.64, -13.56), (15.64, 13.56), (-13.36, 13.56))]
    d.polygon([T(cx + u * math.cos(h) - w * math.sin(h), cz + u * math.sin(h) + w * math.cos(h)) for u, w in cor], outline=(80, 200, 255), width=2)
    d.ellipse([T(754.871 - 1, 17.604 - 1), T(754.871 + 1, 17.604 + 1)], fill=(255, 80, 80))
    im.save(os.path.join(P, 'transport_road_plan_topdown.png'))
