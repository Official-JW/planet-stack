# Count Mach diamonds in a pad still by measurement: sample luminance along each engine's projected thrust axis
# (points from window.__ef.axisPx(), every 0.1 m from the bell exit), max over +-1 px across the axis, 3-tap smoothed.
# A diamond = a bright run (>= threshold) starting below the nozzle hot zone (x >= 1.3 m) and inside the train (x <= 11.5 m),
# separated from the next by a darker gap. threshold = gap level + 60% of (peak - gap level), gap level = 20th percentile.
# usage: python3 diamond_count.py still.png axis.json [scale] > result.json
import sys, json
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB'); px = im.load(); W, H = im.size
ax = json.load(open(sys.argv[2])); sc = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
lum = lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
X0, X1 = 1.3, 11.5
res = []
for k, pts in enumerate(ax):
    prof = []
    for x, u, v in pts:
        u, v = u * sc, v * sc; best = 0
        for du in (-1, 0, 1):
            iu, iv = int(round(u + du * sc)), int(round(v))
            if 0 <= iu < W and 0 <= iv < H: best = max(best, lum(px[iu, iv]))
        prof.append((x, best))
    ys = [p[1] for p in prof]
    sm = [sum(ys[max(0, i - 1):i + 2]) / len(ys[max(0, i - 1):i + 2]) for i in range(len(ys))]
    idx = [i for i, p in enumerate(prof) if X0 <= p[0] <= X1]
    vals = sorted(sm[i] for i in idx); gap = vals[int(0.2 * len(vals))]; top = vals[-1]; thr = gap + 0.6 * (top - gap)
    runs, cur = [], None
    for i in idx:
        if sm[i] >= thr: cur = cur or [prof[i][0], prof[i][0], sm[i]]; cur[1] = prof[i][0]; cur[2] = max(cur[2], sm[i])
        elif cur: runs.append(cur); cur = None
    if cur: runs.append(cur)
    runs = [r for r in runs if r[1] - r[0] >= 0.15 and r[0] > X0]       # drop slivers and anything still attached to the nozzle zone
    res.append({'engine': k, 'diamonds': len(runs), 'gap_lum': round(gap), 'peak_lum': round(top), 'contrast': round((top - gap) / max(gap, 1), 2),
                'knots_m': [[round(r[0], 1), round(r[1], 1)] for r in runs], 'profile_every_0.5m': [round(sm[i]) for i in range(0, len(sm), 5)]})
print(json.dumps({'still': sys.argv[1], 'engines': res, 'count_per_engine': [r['diamonds'] for r in res]}, indent=1))
