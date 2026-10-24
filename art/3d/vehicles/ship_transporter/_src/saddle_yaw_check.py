#!/usr/bin/env python3
"""ST-10A signed saddle-vs-hull check (light, numpy only). The KD clearance in clearance_st10a.py is unsigned, so a hull feature
INSIDE a saddle reads ~0 like a touching one; this check tests hull verts against the saddle volumes directly.
LOADED: saddle = r in [rin, rin+0.8] (rubber 0.35 + backing 0.45), |y-yc| <= 0.715, azimuth within +-35 deg of +-Z, plus the arm box
(|x| <= 1.1, r >= rin+0.78); hull lifted 0.45 (Ship_Seat). margin = rin - r of hull verts in that y band and sector (< 0 = penetration).
EMPTY drive-in: the open saddle sweeps the whole hull length along x, so the swept volume is |z| >= rin*cos(35 deg) in the y band (hull
standing, not lifted); margin = rin*cos(35) - |z|.  Hull verts: art/3d/ship/ship_lv2/pad_lv2.glb via ship_skirt_measure.json (read-only).
  python3 saddle_yaw_check.py measure.json out.json"""
import json, math, sys
import numpy as np
MEAS, OUT = sys.argv[1:3]
CLAMPS = [(14.4, 4.01), (24.8, 4.00), (32.4, 4.04)]; RUB = 0.03; LIFT = 0.45; HALF = math.radians(35)
S = np.array(json.load(open(MEAS))['ship']['pts']).reshape(-1, 3)
YMS = {'feet_on_deck_0.492': 0.492, 'AA_Engine_Ring_Mount_3.45': 3.45}
def yawm(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def margins(W, retract, loaded):
    out = []
    for yc, rh in CLAMPS:
        rin = rh + RUB + (0 if loaded else retract)
        b = W[np.abs(W[:, 1] - yc) <= 0.715]
        if not len(b): out.append(9.0); continue
        if loaded:
            r = np.hypot(b[:, 0], b[:, 2]); az = np.arctan2(b[:, 2], b[:, 0])
            sec = (np.abs(az - math.pi / 2) <= HALF) | (np.abs(az + math.pi / 2) <= HALF) | ((np.abs(b[:, 0]) <= 1.1) & (r >= rin + 0.78))
            out.append(float((rin - r[sec]).min()) if sec.any() else 9.0)
        else:
            out.append(float((rin * math.cos(HALF) - np.abs(b[:, 2])).min()))
    return out
res = {}
for ymn, ym in YMS.items():
    for st, retract in (('loaded', 0.0), ('empty_retract_1.6_old', 1.6), ('empty_retract_3.2', 3.2)):
        rows = []
        for yaw in range(0, 360, 5):
            W = (S + [0, ym - 0.492, 0]) @ yawm(yaw).T + ([0, LIFT, 0] if st == 'loaded' else [0, 0, 0])
            m = margins(W, retract, st == 'loaded'); rows.append((yaw, round(min(m), 3), [round(x, 3) for x in m]))
        ok = [y for y, mm, _ in rows if mm >= -0.005]
        res[f'{st}|{ymn}'] = dict(min_margin_m=min(r[1] for r in rows), worst_yaw=min(rows, key=lambda r: r[1])[0], ok_yaws=ok,
                                   per_yaw=[dict(yaw=y, min=mm, per_clamp=pc) for y, mm, pc in rows])
        print(f'{st:20s} {ymn:28s} min {res[f"{st}|{ymn}"]["min_margin_m"]:7.3f} @yaw {res[f"{st}|{ymn}"]["worst_yaw"]:3d}  ok yaws {len(ok)}/72: {ok}')
json.dump(dict(note='margin < 0 = hull vert inside saddle/arm volume; yaw = ship yaw about +Y in the transporter frame (same convention as clearance_st10a.py)', clamps=CLAMPS, results=res), open(OUT, 'w'), indent=1)
