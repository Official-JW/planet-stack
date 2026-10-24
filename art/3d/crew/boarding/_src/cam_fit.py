# Board_Focus camera fit: game camera (38 deg vertical FOV, 18 deg look-down, game yaw = looking down -Z), aimed at a focus point.
# Measures skinned (three r186) crew vertices over every frame of crew_climb + the ladder box, at W x H, against the band y0..y1 (+spare).
#   python3 cam_fit.py POSE_PREFIX T0 T1 [W H Y0 Y1 SPARE]
import sys, json, math, numpy as np
from scipy.spatial import ConvexHull
pre = sys.argv[1]; T0, T1 = float(sys.argv[2]), float(sys.argv[3])
W, H, Y0, Y1, SP = (int(x) for x in (sys.argv[4:9] if len(sys.argv) > 8 else (375, 667, 144, 383, 5)))
m = json.load(open(pre + '.json')); V = m['nverts']; T = np.array(m['times'])
P = np.memmap(pre + '_pos.bin', np.float32, 'r', shape=(len(T), 4, V, 3))
C = np.array([0, 0, -13.0]); LU = np.array([0.8660254, 0, 0.5]); LT = np.array([0.5, 0, -0.8660254])
lad = lambda u, t, z: C + LU * u + LT * t + np.array([0, z, 0])
pts = []
for ti, t in enumerate(T):
    if t < T0 - 1e-6 or t > T1 + 1e-6: continue
    if not any(m['visible'][ti]): continue
    X = np.concatenate([np.asarray(P[ti, k], float) for k in range(4) if m['visible'][ti][k]])   # every skinned vertex of every visible climber
    pts.append(X[ConvexHull(X).vertices])
crew = np.concatenate(pts); print('hull points over all frames', len(crew), file=sys.stderr)
ladder = np.array([lad(u, tt, z) for u in (4.416, 4.486) for tt in (-0.31, 0.31) for z in np.linspace(0.251, 21.849, 30)])
ALL = np.concatenate([crew, ladder])
from scipy.spatial import ConvexHull
hullpts = lambda X: X[ConvexHull(X).vertices]   # perspective extremes of a point set lie on its convex hull
ALL = hullpts(ALL)
th = math.radians(18); tf = math.tan(math.radians(19)); asp = W / H
fwd = np.array([0, -math.sin(th), -math.cos(th)]); up = np.array([0, math.cos(th), -math.sin(th)]); rt = np.array([1.0, 0, 0])
def proj(X, F, d):
    cp = F - fwd * d; Q = X - cp; z = Q @ fwd
    return W / 2 + (Q @ rt) / (z * tf * asp) * W / 2, H / 2 - (Q @ up) / (z * tf) * H / 2
LMID = lad(4.45, 0, 0.5 * (0.251 + 21.849))
def fit(F0, d):   # slide the focus along world Y so the content is centred in the band; returns (ok, spare_top, spare_bot, F)
    lo, hi = -30.0, 30.0
    for _ in range(60):
        h = (lo + hi) / 2; F = F0 + np.array([0, h, 0]); x, y = proj(ALL, F, d)
        if (y.min() - Y0) > (Y1 - y.max()): hi = h      # more room on top -> lower the focus (content moves up on screen)
        else: lo = h
    F = F0 + np.array([0, (lo + hi) / 2, 0]); x, y = proj(ALL, F, d)
    return (y.min() - Y0 >= SP and Y1 - y.max() >= SP), y.min() - Y0, Y1 - y.max(), F, x.min(), x.max()
def crew_px(F, d, at=LMID):
    a = at.copy(); b = at + np.array([0, 1.82, 0]); _, ya = proj(a[None], F, d); _, yb = proj(b[None], F, d); return float(ya[0] - yb[0])
# (a) whole ladder + all climbers in the band: smallest distance that fits
lo, hi = 20.0, 400.0
for _ in range(50):
    d = (lo + hi) / 2; ok = fit(LMID, d)[0]
    if ok: hi = d
    else: lo = d
d_a = hi; ok, st, sb, F_a, xa0, xa1 = fit(LMID, d_a)
res = {'viewport': [W, H], 'band_y': [Y0, Y1], 'spare_req_px': SP, 'frames': int(((T >= T0 - 1e-6) & (T <= T1 + 1e-6)).sum()), 'clip_window_s': [T0, T1],
       'mid_ladder_point': [round(float(v), 3) for v in LMID]}
res['a_fit_whole'] = {'focus': [round(float(v), 3) for v in F_a], 'distance_m': round(d_a, 2), 'crew_px_at_mid_ladder': round(crew_px(F_a, d_a), 1),
                      'spare_top_px': round(float(st), 1), 'spare_bottom_px': round(float(sb), 1), 'x_px': [round(float(xa0), 1), round(float(xa1), 1)],
                      'focus_below_mid_ladder_m': round(float(LMID[1] - F_a[1]), 2)}
# same distance with the focus AT mid-ladder (what Coder gets without an offset)
x, y = proj(ALL, LMID, d_a); res['a_at_mid_ladder_focus'] = {'y_px': [round(float(y.min()), 1), round(float(y.max()), 1)], 'spare_top_px': round(float(y.min() - Y0), 1), 'spare_bottom_px': round(float(Y1 - y.max()), 1)}
# requested 40 px crew: distance, what the ladder needs, how much of it fits
lo, hi = 5.0, 400.0
for _ in range(50):
    d = (lo + hi) / 2
    if crew_px(LMID, d) > 40: lo = d
    else: hi = d
d40 = (lo + hi) / 2; x, y = proj(ladder, LMID, d40)
res['req_40px'] = {'distance_m': round(d40, 2), 'ladder_px_tall': round(float(y.max() - y.min()), 1), 'band_px': Y1 - Y0 - 2 * SP,
                   'conflict': bool(y.max() - y.min() > Y1 - Y0 - 2 * SP)}
# (b) 40 px, tracking: worst vertical spread of the 4 climbers at any frame (all crew visible & on/near the ladder), in px at d40
spread = 0; at_t = None
for ti, t in enumerate(T):
    if t < T0 or t > T1: continue
    vis = [k for k in range(4) if m['visible'][ti][k]]
    if len(vis) < 2: continue
    X = np.concatenate([np.asarray(P[ti, k][::5], float) for k in vis]); _, yy = proj(X, LMID, d40)
    if yy.max() - yy.min() > spread: spread = float(yy.max() - yy.min()); at_t = float(t)
res['b_40px_tracking'] = {'distance_m': round(d40, 2), 'max_group_spread_px': round(spread, 1), 'at_s': round(at_t, 2), 'fits_band': spread <= Y1 - Y0 - 2 * SP}
# (c) busy part only: frame the upper ladder (z >= ZC) + climbers above it at the largest scale that fits
for zc in (8.0, 11.0, 14.0):
    sel = np.concatenate([crew[crew[:, 1] >= zc], ladder[ladder[:, 1] >= zc]])
    ALLb = ALL; ALL = hullpts(sel); lo, hi = 5.0, 400.0
    for _ in range(50):
        d = (lo + hi) / 2
        if fit(LMID, d)[0]: hi = d
        else: lo = d
    okc, s1, s2, Fc, _, _ = fit(LMID, hi); res['c_busy_z>=%g' % zc] = {'focus': [round(float(v), 3) for v in Fc], 'distance_m': round(hi, 2), 'crew_px': round(crew_px(Fc, hi, lad(4.45, 0, zc + 4)), 1), 'spare_top_px': round(float(s1), 1), 'spare_bottom_px': round(float(s2), 1)}
    ALL = ALLb
print(json.dumps(res, indent=1))
