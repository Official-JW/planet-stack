# v5 climb check (Director 1:42): per rung per crew, the planted boot (< 0.15 m/s) vs the rung top it stands on (lowest sole vertex over the
# rung, sink <= 0.5 cm / float <= 2 cm); every frame: penetration of boot / shin / glove vertices into any rung (r 25 mm, |t| < 0.28);
# planted gloves: distance to the rung; top: planted boots vs the doorway sill 21.748 / wing deck 21.849. Board time = crew time + 2.0 s.
#   python3 climb_check.py POSE_PREFIX [out.json]
import sys, json, numpy as np
pre = sys.argv[1]; J = json.load(open(pre + '.json')); T = np.array(J['times']); V = J['nverts']; vj = np.array(J['vjoint'])
P = np.fromfile(pre + '_pos.bin', np.float32).reshape(len(T), 4, V, 3); vis = np.array(J['visible'])
C0 = np.array([0.0, 0.0, -13.0]); LU = np.array([0.8660254, 0, 0.5]); LT = np.array([0.5, 0, -0.8660254]); LADR = 4.45; RR = float(__import__('os').environ.get('RUNG_R', 0.025)); HW = 0.28
RY = 0.65 + 0.6 * np.arange(35); dt = T[1] - T[0]
def rung_rel(q):   # per vertex: (u - LADR, t, y) in ladder coords
    w = q - C0; return np.stack([w @ LU - LADR, w @ LT, w[:, 1]], 1)
def pen(q):   # max penetration (m, > 0 = inside a rung) and which rung
    r = rung_rel(q); best = (-9.0, -1)
    m = np.abs(r[:, 1]) < HW
    if not m.any(): return best
    r = r[m]; i = np.clip(np.round((r[:, 2] - 0.65) / 0.6).astype(int), 0, 34)
    d = np.hypot(r[:, 0], r[:, 2] - RY[i]); k = int(np.argmin(d)); return (RR - float(d[k]), int(i[k]))
out = {'crew': {}, 'rungs': {}}
for c in range(4):
    cn = 'Crew_%d' % (c + 1); R = {}; W = dict(foot_pen=(-9, None), shin_pen=(-9, None), hand_pen=(-9, None), hand_planted_gap=(-9, None), sill=(9, -9, None)); prev = {}
    for ti, t in enumerate(T):
        if not vis[ti][c]: continue
        X = P[ti, c]
        for s in 'LR':
            q = X[vj == 'Foot_' + s]; qs = X[vj == 'Shin_' + s]; qh = X[vj == 'Hand_' + s]
            ce = q.mean(0); sp = np.linalg.norm(ce - prev[s]) / dt if s in prev else 9.0; prev[s] = ce
            ch = qh.mean(0); sh = np.linalg.norm(ch - prev.get('h' + s, ch + 9)) / dt; prev['h' + s] = ch
            r = rung_rel(q); onlad = np.abs(r[:, 0]).min() < 0.30 and 0.4 < q[:, 1].min() < 21.4
            if onlad:
                p_, i_ = pen(q)
                if p_ > W['foot_pen'][0]: W['foot_pen'] = (p_, (round(float(t) + 2, 2), s, i_))
                if sp < 0.15:   # planted on a rung: lowest vertex over the rung (|u| < 3 cm) vs the rung top
                    m = (np.abs(r[:, 0]) < 0.03) & (np.abs(r[:, 1]) < HW)
                    if m.any():
                        y = r[m, 2]; i = int(np.clip(np.round((y.min() - 0.03 - 0.65) / 0.6), 0, 34)); g = float(y.min() - (RY[i] + RR))
                        e = R.setdefault(str(i), dict(min_gap_m=9.0, max_gap_m=-9.0, frames=0)); e['frames'] += 1
                        e['min_gap_m'] = round(min(e['min_gap_m'], g), 4); e['max_gap_m'] = round(max(e['max_gap_m'], g), 4)
                    else:
                        e = R.setdefault('not_over_rung', dict(frames=0, t=[])); e['frames'] += 1; e['t'].append(round(float(t) + 2, 2)) if len(e['t']) < 8 else None
            if np.abs(rung_rel(qs)[:, 0]).min() < 0.3:
                p_, i_ = pen(qs)
                if p_ > W['shin_pen'][0]: W['shin_pen'] = (p_, (round(float(t) + 2, 2), s, i_))
            rh = rung_rel(qh)
            if np.abs(rh[:, 0]).min() < 0.3 and qh[:, 1].min() < 21.3:
                p_, i_ = pen(qh)
                if p_ > W['hand_pen'][0]: W['hand_pen'] = (p_, (round(float(t) + 2, 2), s, i_))
                if sh < 0.15 and qh[:, 1].min() > 1.2 and abs(float(rung_rel(ch[None])[0, 1])) > 0.20: W['stile_holds'] = W.get('stile_holds', 0) + 1
                elif sh < 0.15 and qh[:, 1].min() > 1.2:
                    if -p_ > W['hand_planted_gap'][0]: W['hand_planted_gap'] = (-p_, (round(float(t) + 2, 2), s, i_))
            if q[:, 1].min() > 21.5 and sp < 0.15:
                u = (q - C0) @ LU; deck = np.where(u < 4.05, 21.748, 21.849); g = q[:, 1] - deck; gm = float(g.min())
                if gm < W['sill'][0]: W['sill'] = (gm, W['sill'][1], W['sill'][2])
                if gm > W['sill'][1]: W['sill'] = (W['sill'][0], gm, (round(float(t) + 2, 2), s, round(float(u.mean()), 2)))
    # gate 4: both boots rising together (vertical speed > 5 cm/s each), longest continuous run on the ladder
    yL = np.array([P[i, c][vj == 'Foot_L'][:, 1].mean() for i in range(len(T))]); yR = np.array([P[i, c][vj == 'Foot_R'][:, 1].mean() for i in range(len(T))])
    up = (np.gradient(yL, T) > 0.05) & (np.gradient(yR, T) > 0.05) & (np.minimum(yL, yR) > 0.3) & vis[:, c]
    run = best = 0; bt = None
    for i in range(len(T)):
        run = run + 1 if up[i] else 0
        if run > best: best = run; bt = round(float(T[i]) + 2, 2)
    W['rise'] = (round(best * dt, 3), bt)
    out['rungs'][cn] = R
    rg = [v for k, v in R.items() if k != 'not_over_rung']
    out['crew'][cn] = dict(rung_worst_sink_m=round(min([0.0] + [v['min_gap_m'] for v in rg]), 4), rung_worst_float_m=round(max([-9] + [v['max_gap_m'] for v in rg]), 4), rungs_planted=len(rg),
                           planted_not_over_rung=R.get('not_over_rung', {}).get('frames', 0),
                           foot_rung_pen_max_m=round(W['foot_pen'][0], 4), foot_pen_at=W['foot_pen'][1], shin_rung_pen_max_m=round(W['shin_pen'][0], 4), shin_pen_at=W['shin_pen'][1],
                           hand_rung_pen_max_m=round(W['hand_pen'][0], 4), hand_pen_at=W['hand_pen'][1], planted_hand_max_gap_m=round(W['hand_planted_gap'][0], 4), hand_gap_at=W['hand_planted_gap'][1],
                           top_planted_sole_min_gap_m=round(W['sill'][0], 4), top_planted_sole_max_gap_m=round(W['sill'][1], 4), top_max_at=W['sill'][2], stile_hold_frames=W.get('stile_holds', 0), both_feet_rising_max_s=W['rise'][0], rising_end_at=W['rise'][1])
print(json.dumps(out['crew'], indent=1))
if len(sys.argv) > 2: json.dump(out, open(sys.argv[2], 'w'), indent=1)
