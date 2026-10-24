// Layout v4 numbers shared by the builder, the slots JSON writer and the verifier. Dock-local metres (dock origin = world 360, 0, -8).
export const DOCK_WORLD = [360, 0, -8];
export const RIG = { bridge_rest: 9.0, bridge_min: 3.8, bridge_max: 21.0, trolley_y: 11.5, trolley_range: 5.2, hook_rest: 7.0, carry: 6.0, rope_top: 11.2 };
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
export const KT = [0, 1.40, 1.90, 2.05, 2.55, 5.15, 5.70, 5.85, 6.35, 8.00];
export const SEGMENTS = [['approach', 0, 1.40], ['lower', 1.40, 1.90], ['pick_hold', 1.90, 2.05], ['hoist', 2.05, 2.55], ['travel', 2.55, 5.15],
  ['set_lower', 5.15, 5.70], ['set_hold', 5.70, 5.85], ['up', 5.85, 6.35], ['return', 6.35, 8.00]];
export const EVENTS = { pick: 1.95, set: 5.75 };
export const CLIPS = [];
for (const s of SLOTS) for (const k of ['A', 'B']) {
  const p = PICKS[k], nn = s.name.slice(5);
  CLIPS.push({ name: `Store_${k}_Slot_${nn}`, from: { node: 'Pick_' + k, hook: p.hook }, to: { node: s.name, hook: s.hook } });
  CLIPS.push({ name: `Load_${k}_Slot_${nn}`, from: { node: s.name, hook: s.hook }, to: { node: 'Pick_' + k, hook: p.hook } }); }
// keys [bridge z, trolley x, hook y] at KT
export function clipKeys(c) { const R = [RIG.bridge_rest, 0, RIG.hook_rest], f = c.from.hook, t = c.to.hook, C = RIG.carry;
  return [R, [f[2], f[0], C], [f[2], f[0], f[1]], [f[2], f[0], f[1]], [f[2], f[0], C], [t[2], t[0], C], [t[2], t[0], t[1]], [t[2], t[0], t[1]], [t[2], t[0], C], R]; }
export const smooth = s => s * s * (3 - 2 * s);
export function sample(c, t) { const K = clipKeys(c); let i = 0; while (i < KT.length - 2 && t > KT[i + 1]) i++;
  const s = Math.min(1, Math.max(0, (t - KT[i]) / (KT[i + 1] - KT[i]))), h = smooth(s); return K[i].map((v, j) => v + (K[i + 1][j] - v) * h); }
