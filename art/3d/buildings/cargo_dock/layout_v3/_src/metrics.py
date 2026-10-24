import numpy as np, json, math
exec(open('frame_solve_v3.py').read().split('ctz = -8.0')[0].replace("G = {k:", "G0 = {k:").replace("H = {k:", "H0 = 0 and {k:").replace("ALL = np.concatenate(list(H.values()))", "ALL=None"), globals())
CT = [369.5, 1.5, 8.6]; FW = 48.0
S = json.load(open('slots_v3.json')); out = {}
for s in SIZES:
    key = f"{s['W']}x{s['H']}"; ws = []
    for sl in S['slots']:
        x, y, z = sl['world']; P = np.array([[x + dx, y + dy, z + dz] for dx in (-1.2, 1.2) for dy in (0, 1.5) for dz in (-0.67, 0.67)])
        X, Y = proj(CT, FW, s, P); ws.append(X.max() - X.min())
    cw = S['storage_crane']['place_world']; X, Y = proj(CT, FW, s, np.array([[cw[0], 0, cw[2]], [cw[0], 8.42, cw[2]]]))
    # jib projected length for every slew angle (slew joint y 6.3, reach 2..6.6 m used, jib tip at ~7.3 m)
    jl = []
    for a in np.radians(np.arange(0, 360, 5)):
        Q = np.array([[cw[0], 6.6, cw[2]], [cw[0] + 7.3 * math.cos(a), 6.6, cw[2] - 7.3 * math.sin(a)]]); X2, Y2 = proj(CT, FW, s, Q); jl.append(math.hypot(X2[1] - X2[0], Y2[1] - Y2[0]))
    out[key] = {'box_w_px_min': round(min(ws), 1), 'box_w_px_max': round(max(ws), 1), 'crane_h_px': round(Y.max() - Y.min(), 1), 'jib_px_min': round(min(jl), 1), 'jib_px_max': round(max(jl), 1),
                'px_per_m_at_ct': round(s['W'] / FW, 2)}
print(json.dumps(out, indent=1)); json.dump(out, open('metrics_v3.json', 'w'), indent=1)
