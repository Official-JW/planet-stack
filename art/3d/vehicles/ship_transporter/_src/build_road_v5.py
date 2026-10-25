#!/usr/bin/env python3
"""ST-10A crawler transport road v5 -> raw GLB (vertex colour only, one mesh / one draw, like _shared/road/haul_road_seg.glb).
Centreline from road_v5.py (pad pick-up (640,-13) -> straight +X -> one right arc R 100 m / 40 deg -> straight to Shipyard Road_Entry (754.871, 17.604)).
Mesh = pad right edge (x 669.5) -> Road_Entry.  Cross-section (w = metres left of heading, +w = camera side at the pad):
  toe +-19.91 (y 0) | shoulder crest +-18.6 (y 0.26) | running edge +-17.31 (y 0.045) | crawler lanes |w| 9.7-13.3 (y 0.03, compacted, cleat
  imprints 0.40 m every 1.24 m = ST-10A track) | centre strip |w| < 9.7 (y 0.045).  Local origin = mesh start centre on the ground; place at
  world (669.5, 0, -13), no rotation.  End at the Shipyard: the camera side (+w) keeps the full 19.91 m to Road_Entry; the far side (-w) follows the
  prop-free envelope measured from shipyard_bcbd0934 (>= 0.5 m margin): 19.91 to s 112.3, 14.0 at s 113.5, 13.5 at s 115.3, 2.6 from s 115.7 to Road_Entry.
  python3 build_road_v5.py <road_v5_check_cl.npy> <out_raw.glb>   then  gltfpack -i raw -o st10a_transport_road.glb -cc -kn -ke -vpf"""
import json, math, struct, sys
import numpy as np
CL = np.load(sys.argv[1]); OUT = sys.argv[2]
P, H, S = CL[:, :2], CL[:, 2], CL[:, 3]
X_START = 669.5; i0 = int(np.argmax(P[:, 0] >= X_START)); P, H, S = P[i0:], H[i0:], S[i0:]
ORG = np.array([P[0, 0], P[0, 1]])
PITCH, CLEAT = 1.24, 0.40
s_rows = [S[0]]; k = math.ceil(S[0] / PITCH)
while k * PITCH < S[-1]:
    for t in (k * PITCH, k * PITCH + CLEAT):
        if S[0] < t < S[-1]: s_rows.append(t)
    k += 1
s_rows.append(S[-1]); s_rows += [112.3, 113.5, 115.3, 115.7]; s_rows = np.array(sorted(set(np.round(s_rows, 4))))
def at(s):
    x = np.interp(s, S, P[:, 0]); z = np.interp(s, S, P[:, 1]); h = np.interp(s, S, H); return np.array([x, z]), h
W = [-19.91, -18.6, -17.31, -13.3, -9.7, 9.7, 13.3, 17.31, 18.6, 19.91]
Y = [0.0, 0.26, 0.045, 0.03, 0.045, 0.045, 0.03, 0.045, 0.26, 0.0]
NEG = np.array([[0, 19.91], [112.3, 19.91], [113.5, 14.0], [115.3, 13.5], [115.7, 2.6], [1e3, 2.6]])
def hw(s, w): return 19.91 if w >= 0 else float(np.interp(s, NEG[:, 0], NEG[:, 1]))
def scale(s): return 1.0 if s <= 112.3 else 0.5
C_SURF = np.array([0.46, 0.41, 0.35]); C_LANE = np.array([0.33, 0.30, 0.27]); C_CLEAT = np.array([0.22, 0.205, 0.19]); C_BERM = np.array([0.56, 0.50, 0.43])
C_EDGE = np.array([0.62, 0.55, 0.30])          # faint survey edge line at the running edge
def hsh(a, b): return ((a * 73856093) ^ (b * 19349663)) % 1000 / 1000.0
rows = []
for s in s_rows:
    c, h = at(s); n = np.array([-math.sin(h), math.cos(h)]); sc = scale(s)
    rows.append([(c + math.copysign(min(abs(w), hw(s, w)), w) * n, y) for w, y in zip(W, Y)])
pos, col, nor, idx = [], [], [], []
for r in range(len(rows) - 1):
    s_mid = 0.5 * (s_rows[r] + s_rows[r + 1]); cleat = ((s_mid / PITCH) % 1.0) < (CLEAT / PITCH)
    for j in range(len(W) - 1):
        wm = 0.5 * (W[j] + W[j + 1]); aw = abs(wm)
        if aw > 17.31: base = C_BERM
        elif 9.7 < aw < 13.3: base = C_CLEAT if cleat else C_LANE
        else: base = C_SURF
        cc = np.clip(base * (0.94 + 0.12 * hsh(r, j)), 0, 1)
        q = [rows[r][j], rows[r][j + 1], rows[r + 1][j + 1], rows[r + 1][j]]
        V = np.array([[p[0][0] - ORG[0], p[1], p[0][1] - ORG[1]] for p in q])
        nn = np.cross(V[2] - V[0], V[1] - V[0]); nn = nn / (np.linalg.norm(nn) + 1e-12)
        if nn[1] < 0: nn = -nn
        b = len(pos); pos += V.tolist(); col += [cc.tolist()] * 4; nor += [nn.tolist()] * 4
        # winding: up-facing (CCW seen from +Y)
        tri = [(b, b + 3, b + 2), (b, b + 2, b + 1)]
        a0 = np.cross(V[3] - V[0], V[2] - V[0])
        if a0[1] < 0: tri = [(b, b + 2, b + 3), (b, b + 1, b + 2)]
        idx += tri
# running-edge survey dashes (thin quads 0.15 m wide, 2 m on / 6 m off), both sides
for side in (-1, 1):
    s = S[0] + 1.0
    while s + 2.0 < S[-1] - 1.0:
        if side < 0 and s + 2.0 > 112.3: break
        quad = []
        for ss, ww in ((s, 17.0), (s, 17.15), (s + 2.0, 17.15), (s + 2.0, 17.0)):
            c, h = at(ss); n = np.array([-math.sin(h), math.cos(h)]); p = c + side * ww * n; quad.append([p[0] - ORG[0], 0.05, p[1] - ORG[1]])
        V = np.array(quad); b = len(pos); pos += V.tolist(); col += [C_EDGE.tolist()] * 4; nor += [[0, 1, 0]] * 4
        a0 = np.cross(V[3] - V[0], V[2] - V[0]); idx += [(b, b + 3, b + 2), (b, b + 2, b + 1)] if a0[1] >= 0 else [(b, b + 2, b + 3), (b, b + 1, b + 2)]
        s += 8.0
pos = np.array(pos, np.float32); col = np.array(col, np.float32); nor = np.array(nor, np.float32); idx = np.array(idx, np.uint32).ravel()
end_local = (P[-1] - ORG).round(3).tolist()
extras = dict(version='v5 (station order d729465: Cargo Space Dock 480 | Launch Pad 640 | Shipyard 800)', place_world=[float(ORG[0]), 0.0, float(ORG[1])], rotation='none',
    road_start_world=[round(float(ORG[0]), 3), 0.0, round(float(ORG[1]), 3)], road_end_world_shipyard_road_entry=[754.871, 0.23, 17.604], road_end_local=[end_local[0], 0.0, end_local[1]],
    crawler_path='pick-up (640,-13) heading +X -> straight to x 682.0 -> right arc R 100 m / 40 deg (centre 682.0, 87.0) -> straight 11.21 m at heading 40 deg -> Road_Entry; length 123.03 m; crawler stop (ship axis) (735.42, 2.46) hdg 32.3 deg at s 98.35',
    widths='running 34.62 m, graded 39.82 m; crawler lanes |w| 9.7-13.3 (ST-10A tracks)', surface_y=0.045, style='crawler-track road: compacted regolith, dark track lanes with cleat imprints 0.40/1.24 m, dusty shoulders, survey edge dashes; vertex colour only',
    shipyard_end='far side (-w) trimmed to the prop-free envelope from s 112.3 (half width 19.91 -> 2.6 at s 115.7); camera side full to Road_Entry',
    s_frame='s = metres along the crawler path from the pad pick-up (640,-13); mesh s 29.5..123.03')
def pad4(b, c=b'\0'): return b + c * ((4 - len(b) % 4) % 4)
bins = [pos.tobytes(), nor.tobytes(), col.tobytes(), idx.tobytes()]; offs = []; blob = b''
for bb in bins: offs.append(len(blob)); blob += pad4(bb)
g = dict(asset=dict(version='2.0', generator='build_road_v5.py'), scene=0, scenes=[dict(name='Scene', nodes=[0])],
    nodes=[dict(name='ST10A_TransportRoad', mesh=0, translation=[0, 0, 0], extras=extras)],
    meshes=[dict(name='ST10A_TransportRoad', primitives=[dict(attributes=dict(POSITION=0, NORMAL=1, COLOR_0=2), indices=3, material=0)])],
    materials=[dict(name='ST10_Road', pbrMetallicRoughness=dict(metallicFactor=0, roughnessFactor=0.92))],
    buffers=[dict(byteLength=len(blob))],
    bufferViews=[dict(buffer=0, byteOffset=offs[0], byteLength=len(bins[0]), target=34962), dict(buffer=0, byteOffset=offs[1], byteLength=len(bins[1]), target=34962),
                 dict(buffer=0, byteOffset=offs[2], byteLength=len(bins[2]), target=34962), dict(buffer=0, byteOffset=offs[3], byteLength=len(bins[3]), target=34963)],
    accessors=[dict(bufferView=0, componentType=5126, count=len(pos), type='VEC3', min=pos.min(0).tolist(), max=pos.max(0).tolist()),
               dict(bufferView=1, componentType=5126, count=len(nor), type='VEC3'), dict(bufferView=2, componentType=5126, count=len(col), type='VEC3'),
               dict(bufferView=3, componentType=5125, count=len(idx), type='SCALAR')])
js = pad4(json.dumps(g, separators=(',', ':')).encode(), b' ')
out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(blob), 0x004E4942) + blob
open(OUT, 'wb').write(out)
print(json.dumps(dict(verts=len(pos), tris=len(idx) // 3, rows=len(s_rows), mesh_len=round(float(S[-1] - S[0]), 2), start=ORG.round(3).tolist(), end=P[-1].round(3).tolist(), bytes=len(out))))
