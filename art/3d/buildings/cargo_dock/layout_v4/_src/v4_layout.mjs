// Layout v4 numbers shared by the builder, the slots JSON writer and the verifier. Dock-local metres (dock origin = world 360, 0, -8).
export const DOCK_WORLD = [360, 0, -8];
export const RIG = { bridge_rest: 12.4, bridge_min: 3.8, bridge_max: 21.0, trolley_y: 11.5, trolley_range: 5.2, hook_rest: 7.0, carry: 6.0, rope_top: 11.2 };
export const RUNWAY = { x: 7.2, y0: 8.95, y1: 9.61, rail: 9.75, z0: 2.0, z1: 22.9 };
export const COLS = [2.6, 7.0, 16.4];
export const STOP = { local: [2.4, 0, 21], world: [362.4, 0, 13] };
const BED = { A: -1.15, B: -3.65 }, BED_Y = 1.9;            // FB-05 Bed_Slot_01 / _02 x from the truck origin (heading +X)
export const PICKS = Object.fromEntries(Object.entries(BED).map(([k, dx]) => [k, {
  bed_slot: k === 'A' ? 'Bed_Slot_01' : 'Bed_Slot_02', box_base: [STOP.local[0] + dx, BED_Y, STOP.local[2]], hook: [STOP.local[0] + dx, BED_Y + 1.5, STOP.local[2]] }]));
export const ROWS = [3.8, 5.6, 7.4, 9.2, 11.0], BLOCK_X = { L: -4.25, R: 4.25 }, TIER_Y = [0.12, 1.62];
export const SLOTS = [];
{ let n = 1; for (const [tier, y] of TIER_Y.entries()) for (const b of ['L', 'R']) ROWS.forEach((z, r) => {
  const name = 'Slot_' + String(n++).padStart(2, '0'); SLOTS.push({ name, block: b, row: r + 1, tier: tier + 1, box_base: [BLOCK_X[b], y, z], hook: [BLOCK_X[b], y + 1.5, z] }); }); }
export const TIER03 = { Lb: [20.5, 6.0], Rf: [23.5, 6.0], Lf: [26.5, 6.0] };
// Heavy timing (10/24 2:29 PM): 22.0 s per box. Bridge/trolley travel easeInOutSine; hook lowers with a 0.25 m/s landing creep (last 0.15 m, then a
// 0.2 s touchdown) and hoists with the mirrored take-up creep; a damped sway settle at carry height before every lower; short latch holds.
export const SEGMENTS = [['approach', 0, 2.8], ['settle_pick', 2.8, 3.4], ['lower', 3.4, 5.8], ['pick_hold', 5.8, 6.2], ['hoist', 6.2, 8.6], ['travel', 8.6, 13.6],
  ['settle_set', 13.6, 14.6], ['set_lower', 14.6, 17.0], ['set_hold', 17.0, 17.4], ['up', 17.4, 19.2], ['return', 19.2, 22.0]];
export const KT = [0, ...SEGMENTS.map(s => s[2])];
export const DUR = 22.0;
export const EVENTS = { pick: 6.0, set: 17.2 };
export const SEG = Object.fromEntries(SEGMENTS.map(([n, a, b]) => [n, [a, b]]));
export const CREEP = { d: 0.15, v: 0.25, touch: 0.2 };              // landing creep distance (m), speed (m/s), touchdown decel (s)
CREEP.tc = (CREEP.d - CREEP.v * CREEP.touch / 2) / CREEP.v;          // constant-speed creep time (0.5 s)
export const SWAY = { pick: 0.04, set: 0.07, cycles: 1.0, damp: 2.0 };// damped sway amplitude (m) empty / loaded, along the last travel direction
export const easeSine = u => (1 - Math.cos(Math.PI * Math.min(1, Math.max(0, u)))) / 2;
// lower profile: distance covered (0..D) at time tau in [0,T]: main phase (0 -> peak -> creep speed), constant creep, raised-cosine touchdown to 0
export function lowerS(D, T, tau) { const { d, v, touch, tc } = CREEP, T1 = T - tc - touch, D1 = D - d; const A = (D1 - v * T1 / 2) * Math.PI / (2 * T1);
  if (tau <= 0) return 0; if (tau < T1) { const w = Math.PI / T1; return A * (1 - Math.cos(w * tau)) / w + v * (tau / 2 - Math.sin(w * tau) / (2 * w)); }
  if (tau < T1 + tc) return D1 + v * (tau - T1); const x = Math.min(touch, tau - T1 - tc); return D1 + v * tc + v * (x / 2 + Math.sin(Math.PI * x / touch) * touch / (2 * Math.PI)); }
export const lowerPhases = T => [0, T - CREEP.tc - CREEP.touch, T - CREEP.touch, T];   // piece boundaries (relative)
export const swayS = u => (u <= 0 || u >= 1) ? 0 : Math.sin(2 * Math.PI * SWAY.cycles * u) * Math.exp(-SWAY.damp * u) * (1 - u) ** 2;
export const CLIPS = [];
for (const s of SLOTS) for (const k of ['A', 'B']) {
  const p = PICKS[k], nn = s.name.slice(5);
  CLIPS.push({ name: `Store_${k}_Slot_${nn}`, from: { node: 'Pick_' + k, hook: p.hook }, to: { node: s.name, hook: s.hook } });
  CLIPS.push({ name: `Load_${k}_Slot_${nn}`, from: { node: s.name, hook: s.hook }, to: { node: 'Pick_' + k, hook: p.hook } }); }
// keys [bridge z, trolley x, hook y] at KT
export function clipKeys(c) { const R = [RIG.bridge_rest, 0, RIG.hook_rest], f = c.from.hook, t = c.to.hook, C = RIG.carry;
  return [R, [f[2], f[0], C], [f[2], f[0], f[1]], [f[2], f[0], f[1]], [f[2], f[0], C], [t[2], t[0], C], [t[2], t[0], t[1]], [t[2], t[0], t[1]], [t[2], t[0], C], R]; }
// exact pose [bridge z, trolley x, hook y, hook sway x, hook sway z] at clip time t
export function pose(c, t) { const K = clipKeys(c), [r, a1, l1, h1, h2, tr, s1, sl, sh, up] = K; const at = n => { const [a, b] = SEG[n]; return (t - a) / (b - a); };
  const mixe = (A, B, u) => A.map((v, j) => v + (B[j] - v) * easeSine(u)); const T = n => SEG[n][1] - SEG[n][0];
  let p, sw = [0, 0];
  if (t <= SEG.approach[1]) p = mixe(r, a1, at('approach'));
  else if (t <= SEG.settle_pick[1]) { p = a1.slice(); const dz = a1[0] - r[0], dx = a1[1] - r[1], n = Math.hypot(dx, dz) || 1, s = SWAY.pick * swayS(at('settle_pick')); sw = [s * dx / n, s * dz / n]; }
  else if (t <= SEG.lower[1]) { const D = a1[2] - l1[2]; p = [a1[0], a1[1], a1[2] - lowerS(D, T('lower'), t - SEG.lower[0])]; }
  else if (t <= SEG.pick_hold[1]) p = h1.slice();
  else if (t <= SEG.hoist[1]) { const D = h2[2] - h1[2], Tt = T('hoist'); p = [h1[0], h1[1], h2[2] - lowerS(D, Tt, SEG.hoist[1] - t)]; }
  else if (t <= SEG.travel[1]) p = mixe(h2, tr, at('travel'));
  else if (t <= SEG.settle_set[1]) { p = tr.slice(); const dz = tr[0] - h2[0], dx = tr[1] - h2[1], n = Math.hypot(dx, dz) || 1, s = SWAY.set * swayS(at('settle_set')); sw = [s * dx / n, s * dz / n]; }
  else if (t <= SEG.set_lower[1]) { const D = tr[2] - s1[2]; p = [tr[0], tr[1], tr[2] - lowerS(D, T('set_lower'), t - SEG.set_lower[0])]; }
  else if (t <= SEG.set_hold[1]) p = sl.slice();
  else if (t <= SEG.up[1]) p = mixe(sl, sh, at('up'));
  else p = mixe(sh, r, Math.min(1, at('return')));
  return [p[0], p[1], p[2], sw[0], sw[1]]; }
// key-time pieces per channel group: [t0, t1, subdivisions]
export function pieces(ch) { const P = []; for (const [n, a, b] of SEGMENTS) {
  const moves = { bridge: ['approach', 'travel', 'return'], hook: ['approach', 'lower', 'hoist', 'set_lower', 'up', 'return', 'settle_pick', 'settle_set'] }[ch].includes(n);
  if (!moves) { P.push([a, b, 1]); continue; }
  if (/lower/.test(n)) { const L = lowerPhases(b - a).map(x => a + x); P.push([L[0], L[1], 12], [L[1], L[2], 2], [L[2], L[3], 3]); }
  else if (n === 'hoist') { const L = lowerPhases(b - a).map(x => b - x).reverse(); P.push([L[0], L[1], 3], [L[1], L[2], 2], [L[2], L[3], 12]); }
  else if (/settle/.test(n)) P.push([a, b, 12]); else P.push([a, b, 10]); } return P; }
export const smooth = s => s * s * (3 - 2 * s);
export function sample(c, t) { const K = clipKeys(c); let i = 0; while (i < KT.length - 2 && t > KT[i + 1]) i++;
  const s = Math.min(1, Math.max(0, (t - KT[i]) / (KT[i + 1] - KT[i]))), h = smooth(s); return K[i].map((v, j) => v + (K[i + 1][j] - v) * h); }
// CUBICSPLINE bake: keys at the piece subdivisions; tangents = exact one-sided derivatives of pose() inside each piece (velocity jumps allowed at piece edges)
export function bakeTimes(ch) { const T = []; for (const [a, b, n] of pieces(ch)) for (let i = 0; i < n; i++) T.push(+(a + (b - a) * i / n).toFixed(6)); T.push(DUR); return T; }
export function bake(c, ch, f) { const T = bakeTimes(ch), h = 1e-5, out = []; const P = pieces(ch);
  const inPiece = (t, side) => P.find(([a, b]) => side < 0 ? (t > a + 1e-9 && t <= b + 1e-9) : (t >= a - 1e-9 && t < b - 1e-9));
  const d = (t, side) => { const pc = inPiece(t, side); if (!pc) return f(pose(c, t)).map(() => 0); const [a, b] = pc;
    const t0 = Math.max(a, t - h), t1 = Math.min(b, t + h); const A = f(pose(c, t0)), B = f(pose(c, t1)); return A.map((v, j) => (B[j] - v) / (t1 - t0)); };
  for (const t of T) { out.push(...d(t, -1), ...f(pose(c, t)), ...d(t, +1)); } return { T, out }; }
