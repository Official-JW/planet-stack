import numpy as np, json, sys
from scipy.spatial import ConvexHull
G = {k: np.fromfile(f'/workspace/dockl/v3/pts_{k}.f32', 'f4').reshape(-1, 3).astype('f8') for k in ['dock', 'truck', 'storage', 'crane']}
H = {k: (a[ConvexHull(a).vertices] if len(a) > 10 else a) for k, a in G.items()}
ALL = np.concatenate(list(H.values()))
SIZES = [dict(W=375, H=667, top=144, bot=383), dict(W=393, H=852, top=165, bot=534)]
t19, p = np.tan(np.radians(19)), np.radians(18)
def proj(ct, fw, s, P):
    asp = s['W'] / s['H']; d = fw / 2 / (t19 * asp); ct = np.array(ct, float)
    C = ct + d * np.array([0, np.sin(p), np.cos(p)]); f = (ct - C) / d; r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r); u = np.cross(r, f)
    q = P - C; xc, yc, zc = q @ r, q @ u, q @ f
    X = (xc / (zc * t19 * asp) + 1) / 2 * s['W']; Y = (1 - yc / (zc * t19)) / 2 * s['H']; return X, Y
def spare(ct, fw, s, P=ALL):
    X, Y = proj(ct, fw, s, P); return dict(left=X.min(), right=s['W'] - X.max(), top=Y.min() - s['top'], bottom=s['bot'] - Y.max()), (X.min(), Y.min(), X.max(), Y.max())
def fit(fw, ctz, ref=0):
    ct = [385.0, CTY, ctz]; s = SIZES[ref]
    for _ in range(60):
        sp, _b = spare(ct, fw, s); ct[0] -= (sp['right'] - sp['left']) / 2 * fw / s['W'] * 0.7; ct[2] -= (sp['bottom'] - sp['top']) / 2 * fw / s['W'] * 1.2
    return ct
def worst(ct, fw): return min(min(spare(ct, fw, s)[0].values()) for s in SIZES)
ctz = -8.0
CTY = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
lo, hi = 20, 150
for _ in range(40):
    m = (lo + hi) / 2; (lo, hi) = (lo, m) if worst(fit(m, ctz), m) >= 5 else (m, hi)
print('ct y', CTY, 'min fw', round(hi, 3), 'ct', [round(c, 3) for c in fit(hi, ctz)])
fw = float(sys.argv[2]) if len(sys.argv) > 2 else np.ceil(hi * 2) / 2 + 1
ct = [round(c * 20) / 20 for c in fit(fw, ctz)]
out = {'ct': ct, 'frame_w': fw, 'sizes': {}}
for s in SIZES:
    sp, b = spare(ct, fw, s)
    out['sizes'][f"{s['W']}x{s['H']}"] = {'band_y': [s['top'], s['bot']], 'subject_px': [round(x, 1) for x in b], 'spare_px': {k: round(v, 1) for k, v in sp.items()},
        'per_group_px': {k: [round(x, 1) for x in spare(ct, fw, s, a)[1]] for k, a in H.items()}}
print(json.dumps(out, indent=1)); json.dump(out, open('/workspace/dockl/v3/frame_v3.json', 'w'), indent=1)
