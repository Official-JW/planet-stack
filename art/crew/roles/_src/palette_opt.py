"""Search a 10-colour role accent palette: maximise the worst pairwise CIEDE2000 across normal / protan / deutan (tritan weighted 0.7),
keep >= a margin from the suit's cyan glow + gold visor, keep each role near its semantic hue anchor. Writes nothing; prints the result."""
import sys, os, random, colorsys, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette_check import l2lab, sim, de2000, SUIT
random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 7)
ANCH = {'miner': 48, 'mine_driver': 160, 'mechanic': 355, 'cargo_manager': 272, 'captain': 222, 'co_captain': 195,
        'engineer': 26, 'botanist': 95, 'welder': 322, 'machinist': 30}
def hx(h, s, v): r, g, b = colorsys.hsv_to_rgb(h / 360 % 1, s, v); return '#%02x%02x%02x' % (round(r * 255), round(g * 255), round(b * 255))
KINDS = (('normal', 1.0), ('protan', 1.0), ('deutan', 1.0), ('tritan', 0.7))
def score(P):
    labs = {k: {kd: l2lab(sim(hx(*P[k]), kd)) for kd, _ in KINDS} for k in P}
    slab = {s: {kd: l2lab(sim(SUIT[s], kd)) for kd, _ in KINDS} for s in ('cyan_glow', 'visor', 'shell', 'graphite')}
    m = 1e9
    for a, b in itertools.combinations(P, 2):
        for kd, w in KINDS: m = min(m, de2000(labs[a][kd], labs[b][kd]) / w)
    sv = min(de2000(labs[a][kd], slab[s][kd]) / w for a in P for s in slab for kd, w in KINDS[:3])
    pen = sum(max(0, abs(((P[k][0] - ANCH[k] + 180) % 360) - 180) - 18) * 0.4 for k in P)
    return min(m, sv * 1.4) - pen, m, sv
P = {k: [a, 0.8, 0.95] for k, a in ANCH.items()}
best = score(P); T = 2.0; top = (best, {k: list(v) for k, v in P.items()})
for it in range(int(os.environ.get('IT', 6000))):
    k = random.choice(list(P)); old = list(P[k])
    P[k] = [P[k][0] + random.gauss(0, 8), min(1, max(0.6, P[k][1] + random.gauss(0, 0.06))), min(1, max(0.72, P[k][2] + random.gauss(0, 0.06)))]
    s = score(P)
    if s[0] >= best[0] or random.random() < 2.718 ** ((s[0] - best[0]) / T): best = s
    else: P[k] = old
    T *= 0.9993
    if best[0] > top[0][0]: top = (best, {k: list(v) for k, v in P.items()})
best, P = top; print(best)
for k in ANCH: print(k, hx(*P[k]), [round(x, 2) for x in P[k]])
