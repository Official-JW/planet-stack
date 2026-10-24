# v3 boarding camera fit for the two FIXED focus nodes (no setViewOffset): plain lookAt at the node, 38 deg vFOV, 18 deg look-down,
# game yaw (looking down -Z), distance from frame_w exactly as qa3d-next fitSite(): d = (frame_w / 2) / (tan(vfov / 2) * aspect).
# Finds the smallest frame_w (0.05 m steps) that keeps the content inside the HUD-free band with >= SPARE px top and bottom at every
# viewport, then reports crew px and spare px per node per viewport.
#   python3 cam_fit_v3.py POSE_PREFIX TRIGGER_ABS_S [SPARE=5]  > camfit_v3.json
#   POSE_PREFIX = dump_poses.mjs output of the packed GLB over crew_climb at 1/30 s (22.3 .. 58.5)
import sys, json, math, numpy as np
from scipy.spatial import ConvexHull
pre = sys.argv[1]; TRIG = float(sys.argv[2]); SP = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
m = json.load(open(pre + '.json')); V = m['nverts']; T = np.array(m['times'])
P = np.memmap(pre + '_pos.bin', np.float32, 'r', shape=(len(T), 4, V, 3))
C = np.array([0, 0, -13.0]); LU = np.array([0.8660254, 0, 0.5]); LT = np.array([0.5, 0, -0.8660254])
lad = lambda u, t, z: C + LU * u + LT * t + np.array([0, z, 0])
NODES = {'Board_Focus': np.array([3.854, 11.05, -10.775]), 'Board_Focus_Top': np.array([3.854, 15.861, -10.775])}
VIEWS = [  # (W, H, band_y0, band_y1, label)
    (375, 667, 144, 383, '375x667 band 144-383 (HUD bottom 120 + 24; bar)'),
    (393, 852, 184, 489, '393x852 band 184-489 (375 band scaled by 852/667)'),
    (393, 852, 165, 534, '393x852 band 165-534 (qa3d-next band() with iPhone safe-area insets 59/34)')]
hull = lambda X: X[ConvexHull(X).vertices]
ladder = np.array([lad(u, tt, z) for u in (4.416, 4.486) for tt in (-0.31, 0.31) for z in np.linspace(0.251, 21.849, 60)])
def crew_pts(t0, t1, ymin=None):
    pts = []
    for ti, t in enumerate(T):
        if t < t0 - 1e-6 or t > t1 + 1e-6: continue
        vis = [k for k in range(4) if m['visible'][ti][k]]
        if not vis: continue
        X = np.concatenate([np.asarray(P[ti, k], float) for k in vis])
        if ymin is not None: X = X[X[:, 1] >= ymin]
        if len(X) >= 4: pts.append(hull(X))
    return hull(np.concatenate(pts))
CONTENT = {
    'Board_Focus': ('whole ladder + every climber, crew_climb start .. trigger', hull(np.concatenate([crew_pts(T[0], TRIG), ladder]))),
    'Board_Focus_Top': ('ladder above 14 m + every crew vertex above 14 m + hatch landing, trigger .. end', hull(np.concatenate([crew_pts(TRIG, T[-1], 14.0), ladder[ladder[:, 1] >= 14.0]])))}
th = math.radians(18); tf = math.tan(math.radians(19))
fwd = np.array([0, -math.sin(th), -math.cos(th)]); up = np.array([0, math.cos(th), -math.sin(th)]); rt = np.array([1.0, 0, 0])
def proj(X, F, d, W, H):
    asp = W / H; Q = X - (F - fwd * d); z = Q @ fwd
    return W / 2 + (Q @ rt) / (z * tf * asp) * W / 2, H / 2 - (Q @ up) / (z * tf) * H / 2
dist = lambda fw, W, H: (fw / 2) / (tf * W / H)
def crew_px(F, d, W, H, at):   # 1.82 m standing crew at `at`
    _, ya = proj(at[None], F, d, W, H); _, yb = proj((at + np.array([0, 1.82, 0]))[None], F, d, W, H); return float(ya[0] - yb[0])
def check(F, X, fw, v):
    W, H, y0, y1, _ = v; d = dist(fw, W, H); x, y = proj(X, F, d, W, H)
    return d, float(y.min() - y0), float(y1 - y.max()), float(x.min()), float(x.max())
out = {'camera': '38 deg vFOV, 18 deg look-down, game yaw (looking down -Z), plain lookAt at the node (no setViewOffset); distance from frame_w as in qa3d-next fitSite()',
       'spare_req_px': SP, 'trigger_abs_s': TRIG, 'fit_views': [v[4] for v in VIEWS[:2]], 'nodes': {}}
for name, F in NODES.items():
    desc, X = CONTENT[name]; fw = 1.0
    while True:   # smallest frame_w that fits the first two views (the 393 safe-area band is reported, not fitted)
        if all(min(check(F, X, fw, v)[1:3]) >= SP and check(F, X, fw, v)[3] >= 0 and check(F, X, fw, v)[4] <= v[0] for v in VIEWS[:2]): break
        fw = round(fw + 0.05, 2)
    at = lad(4.45, 0, 11.05 - 0.91) if name == 'Board_Focus' else lad(4.45, 0, 15.861 - 0.91)
    r = {'translation': [float(v) for v in F], 'frame_w': fw, 'content': desc, 'views': {}}
    for v in VIEWS:
        d, st, sb, x0, x1 = check(F, X, fw, v)
        r['views'][v[4]] = {'distance_m': round(d, 2), 'crew_px': round(crew_px(F, d, v[0], v[1], at), 1), 'spare_top_px': round(st, 1), 'spare_bottom_px': round(sb, 1),
                            'content_x_px': [round(x0, 1), round(x1, 1)], 'fits': bool(st >= SP and sb >= SP)}
    out['nodes'][name] = r
print(json.dumps(out, indent=1))
