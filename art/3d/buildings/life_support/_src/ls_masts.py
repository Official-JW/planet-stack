"""Life Support game GLB post-pass: SA-1/SA-2 solar masts (Tier_20) moved in beside the PM-1/PM-2 main building + new Cam_Target/frame_w.
  gltfpack -i life_support_game.glb(adfaac9) -o plain.glb -noq -kn -ke
  python3 ls_masts.py plain.glb out_raw.glb CT_Y FRAME_W ; gltfpack -i out_raw.glb -o life_support_game.glb -cc -kn -ke
Masts keep their 15.5 m height (tall top-tier look). Each mast is moved as a rigid piece (split by x sign)."""
import sys, json, struct, numpy as np
sys.path.insert(0, '/workspace/planet-stack/art/3d/buildings/shipyard/_src')
from post_ship_build import read, write, acc, put, node
TIER_Z = 6.0                      # new Tier_20 pivot z (was -39.31): mast feet z 3.0..8.9, flanking PM-1 and the porch
DXL, DXR = -4.5, +3.5             # SA-1 x -8.9..-3.7 -> -13.4..-8.2 (1.2 m off PM-1's flank); SA-2 3.7..8.9 -> 7.2..12.4 (clear of the CO2 skid)
DZL = -4.0                        # SA-1 sits 4 m further back (feet z -1.0..4.9) so it clears SWG-1 (x -9..-8, z 8..10)
J, B = read(sys.argv[1]); ct_y, fw = float(sys.argv[3]), float(sys.argv[4]); ct_x = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
t = node(J, 'Tier_20'); J['nodes'][t]['translation'][2] = TIER_Z
c = J['nodes'][t]['children'][0]; cn = J['nodes'][c]; T = np.array(cn.get('translation', [0, 0, 0])); S = np.array(cn.get('scale', [1, 1, 1]))
for pr in J['meshes'][cn['mesh']]['primitives']:
    P = acc(J, B, pr['attributes']['POSITION']).astype(np.float64); q = T + S * P
    L = q[:, 0] < 0; q[:, 0] += np.where(L, DXL, DXR); q[:, 2] += np.where(L, DZL, 0.0)
    pr['attributes']['POSITION'] = put(J, B, ((q - T) / S).astype(np.float32), 'VEC3', 34962, True)
k = node(J, 'Cam_Target'); J['nodes'][k]['translation'][0] = ct_x; J['nodes'][k]['translation'][1] = ct_y; J['nodes'][k]['extras'] = {'frame_w': fw}
write(sys.argv[2], J, B); print('wrote', sys.argv[2])
