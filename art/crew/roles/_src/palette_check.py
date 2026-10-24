"""Role accent palette check: min pairwise CIEDE2000 under normal vision + Machado-2009 (severity 1.0) protan / deutan / tritan sims,
also vs the shared suit colours (white shell, graphite, cyan glow, gold visor). Pure numpy.  python3 palette_check.py [--json]"""
import sys, os, json, itertools, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roles_table as RT
SUIT = {'shell': '#eceef1', 'graphite': '#2b3038', 'cyan_glow': '#3ad0ff', 'visor': '#ffae2e'}
MAC = {'protan': [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
       'deutan': [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
       'tritan': [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]]}
def h2s(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
def s2l(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def l2lab(l):
    X = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]) @ l
    X = X / np.array([0.95047, 1.0, 1.08883]); f = np.where(X > 0.008856, np.cbrt(X), 7.787 * X + 16 / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])
def sim(h, kind): l = s2l(h2s(h)); return l if kind == 'normal' else np.clip(np.array(MAC[kind]) @ l, 0, 1)
def de2000(a, b):
    L1, a1, b1 = a; L2, a2, b2 = b; C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2); Cb = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7))); a1p, a2p = a1 * (1 + G), a2 * (1 + G)
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2); h1p = np.degrees(np.arctan2(b1, a1p)) % 360; h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dL, dC = L2 - L1, C2p - C1p; dh = h2p - h1p
    if C1p * C2p == 0: dh = 0
    elif dh > 180: dh -= 360
    elif dh < -180: dh += 360
    dH = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2)); Lb, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    hb = (h1p + h2p) / 2 if abs(h1p - h2p) <= 180 else (h1p + h2p + 360) / 2
    if C1p * C2p == 0: hb = h1p + h2p
    T = 1 - 0.17 * np.cos(np.radians(hb - 30)) + 0.24 * np.cos(np.radians(2 * hb)) + 0.32 * np.cos(np.radians(3 * hb + 6)) - 0.20 * np.cos(np.radians(4 * hb - 63))
    SL = 1 + 0.015 * (Lb - 50) ** 2 / np.sqrt(20 + (Lb - 50) ** 2); SC = 1 + 0.045 * Cbp; SH = 1 + 0.015 * Cbp * T
    RT_ = -2 * np.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7)) * np.sin(np.radians(60 * np.exp(-((hb - 275) / 25) ** 2)))
    return float(np.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT_ * (dC / SC) * (dH / SH)))
def report(pal):
    out = {}
    for kind in ('normal', 'protan', 'deutan', 'tritan'):
        lab = {k: l2lab(sim(v, kind)) for k, v in pal.items()}; slab = {k: l2lab(sim(v, kind)) for k, v in SUIT.items()}
        pairs = sorted((de2000(lab[a], lab[b]), a, b) for a, b in itertools.combinations(pal, 2))
        vs = sorted((de2000(lab[a], slab[s]), a, s) for a in pal for s in SUIT if s in ('cyan_glow', 'visor'))
        out[kind] = dict(min_pair=round(pairs[0][0], 1), worst=[(round(d, 1), a, b) for d, a, b in pairs[:4]], min_vs_suit=[(round(d, 1), a, s) for d, a, s in vs[:2]])
    return out
if __name__ == '__main__':
    pal = {k: RT.ROLES[k]['accent'] for k in RT.ORDER}
    r = report(pal)
    if '--json' in sys.argv: print(json.dumps(r))
    else:
        for k, v in r.items(): print(k, v)
