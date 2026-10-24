// FB-05 dwell at the GC-1 dock stop (world 362.4, 0, 13), from the game's own flatbed kinematics.
// samplePath / kin / kinT / line / arcPts / dedupe and the constants below are copied verbatim from qa3d-next/main.js (e69ef53, 10/24 11:43)
// so the numbers are the live speed profile, not an estimate. usage: node dwell_v4.mjs  (prints the table); make_slots_v4.mjs imports dwell().
import * as THREE from 'three';
import { KT, EVENTS, STOP, SEG, DUR } from './v4_layout.mjs';
export const SRC = { file: 'qa3d-next/main.js', commit: 'e69ef53', TV: { v: 8.33, ease: 3, brake: 4, settle: 0.4 }, TURN_SPEED: 4.0, TURN_R_MAX: 25, TURN_ACC: 2.5, TURN_GAP: 22, PATH_STEP: 0.025,
  cargo: { perTrip: 2, refLoadSec: 6, padUnloadSec: 6, walkOutSec: 4.0, sealSec: 4, palletCap: 8 }, ht04_trip_s: 56.62, ht04_trip_src: 'window.__ps3d.route.tl.trip (playtest q982c3e3 logs; route code unchanged to e69ef53)', fillFloor: 15,
  route: { RX: 320, PX: 480, refLoad: 318, padUnload: 476.5, lane: 13, back: 22, padUturnX: 481, refUturnX: 295, turnR: 4.5 } };
const { TURN_SPEED, TURN_R_MAX, TURN_ACC, TURN_GAP, PATH_STEP } = SRC; const TV = SRC.TV;
function line(a, b, step = 4) { const n = Math.max(1, Math.round(Math.hypot(b[0] - a[0], b[1] - a[1]) / step)), o = []; for (let i = 1; i <= n; i++) o.push([a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n]); return o; }
function dedupe(pts) { const o = []; for (const p of pts) { const q = o[o.length - 1]; if (!q || Math.hypot(p[0] - q[0], p[1] - q[1]) > .3) o.push(p); } return o; }
function arcPts(cx, cz, r, a0, a1, step = .25) { const k = Math.max(2, Math.ceil(Math.abs(a1 - a0) * r / step)), o = []; for (let i = 1; i <= k; i++) { const a = a0 + (a1 - a0) * i / k; o.push([cx + r * Math.cos(a), cz + r * Math.sin(a)]); } return o; }
function samplePath(pts) {
  pts = dedupe(pts);
  const c = new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(p[0], 0, p[1])), false, 'centripetal'); c.arcLengthDivisions = Math.max(20000, Math.ceil(c.getLength() / PATH_STEP * 4));
  const n = Math.ceil(c.getLength() / PATH_STEP) + 1, sp = c.getSpacedPoints(n - 1), X = new Float64Array(n), Z = new Float64Array(n), C = new Float64Array(n);
  for (let i = 0; i < n; i++) { X[i] = sp[i].x; Z[i] = sp[i].z; if (i) C[i] = C[i - 1] + Math.hypot(X[i] - X[i - 1], Z[i] - Z[i - 1]); }
  return { n, X, Z, C, L: C[n - 1] };
}
function kin(P, da, dd, v) {
  const n = P.n, C = P.C, L = P.L, V = new Float64Array(n), T = new Float64Array(n), cl = new Float64Array(n).fill(v), w = Math.round(1 / PATH_STEP);
  const hd = (i) => { const a = Math.max(0, i - w), b = Math.min(n - 1, i + w); return Math.atan2(P.Z[b] - P.Z[a], P.X[b] - P.X[a]); };
  let last = -1;
  for (let i = 0; i < n; i++) {
    const a = Math.max(0, i - w), b = Math.min(n - 1, i + w); if (b - a < 2) continue;
    let dh = hd(b) - hd(a); dh = Math.atan2(Math.sin(dh), Math.cos(dh)); const ds = C[b] - C[a];
    if (ds > 1e-6 && Math.abs(dh) / ds > 1 / TURN_R_MAX) { cl[i] = Math.min(v, TURN_SPEED); if (last >= 0 && i - last > 1 && C[i] - C[last] < TURN_GAP) for (let j = last + 1; j < i; j++) cl[j] = Math.min(v, TURN_SPEED); last = i; }
  }
  const aS = Math.min(TURN_ACC, v * v / (2 * da)), aB = Math.min(TURN_ACC, v * v / (2 * dd));
  cl[0] = 0; for (let i = 1; i < n; i++) cl[i] = Math.min(cl[i], Math.sqrt(cl[i - 1] ** 2 + 2 * aS * (C[i] - C[i - 1])));
  cl[n - 1] = 0; for (let i = n - 2; i >= 0; i--) cl[i] = Math.min(cl[i], Math.sqrt(cl[i + 1] ** 2 + 2 * aB * (C[i + 1] - C[i])));
  for (let i = 0; i < n; i++) V[i] = cl[i];
  for (let i = 1; i < n; i++) { const vs = V[i - 1] + V[i]; T[i] = T[i - 1] + (vs > 1e-9 ? 2 * (C[i] - C[i - 1]) / vs : 0); }
  return { L, n, C, V, T: T[n - 1], Ts: T, aS, aB };
}
function kinT(k, s) { if (s <= 0) return 0; if (s >= k.L) return k.T; let lo = 0, hi = k.n - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (k.C[m] <= s) lo = m; else hi = m; }
  const v0 = k.V[lo], v1 = k.V[hi], ds = k.C[hi] - k.C[lo], d = s - k.C[lo]; if (ds < 1e-12) return k.Ts[lo];
  const vs = Math.sqrt(Math.max(0, v0 * v0 + (v1 * v1 - v0 * v0) * d / ds)); return k.Ts[lo] + (v0 + vs > 1e-9 ? 2 * d / (v0 + vs) : 0); }
const r3 = x => +x.toFixed(3), r2 = x => +x.toFixed(2);
export function dwell() {
  const R = SRC.route, S = [R.refLoad, R.lane], D = [STOP.world[0], R.lane], U = [R.padUnload, R.lane], L = R.lane, B = R.back, r = R.turnR;
  const kin3 = (pts) => kin(samplePath(pts), TV.ease, TV.brake, TV.v);
  const kThrough = kin3([S, ...line(S, U, 2)]), kIn = kin3([S, ...line(S, D, 2)]), kAway = kin3([D, ...line(D, U, 2)]);
  const kBack = kin3([U, ...line(U, [R.padUturnX, L], 2), ...arcPts(R.padUturnX, (L + B) / 2, r, -Math.PI / 2, Math.PI / 2), ...line([R.padUturnX, B], [R.refUturnX, B], 2), ...arcPts(R.refUturnX, (L + B) / 2, r, Math.PI / 2, 1.5 * Math.PI), ...line([R.refUturnX, L], S, 1)]);
  const a = kIn.aB, v = TV.v, tb = v / a, db = v * v / (2 * a);           // braking into the stop / pull-away (both at TURN_ACC, linear in time)
  const ta = v / kAway.aS, dA = v * v / (2 * kAway.aS);
  const tArriveBrake = kIn.T - kinT(kIn, kIn.L - db), tPull = kinT(kAway, dA);
  const st = TV.settle, c0 = st, cl = DUR;                    // first clip starts after the stop settle; clips run back to back
  const hoistEnd = SEG.hoist[1], upEnd = SEG.up[1];
  const passThrough = (db + dA) / v;                                       // the same 27.8 m driven at 8.33 m/s without the stop
  const mk = (kind, rows, departAt) => { const stationary = departAt, total = tArriveBrake + stationary + tPull;
    rows.sort((x, y) => x.t - y.t); return { case: kind, rows, stationary_s: r3(stationary), arrive_to_depart_s: r3(total), added_trip_time_s: r3(total - passThrough), crane_busy_s: r3(c0 + 2 * cl) }; };
  const store = mk('store (unload 2 boxes from FB-05 into Slot_N, Slot_N+1)', [
    { t: r3(-tArriveBrake), what: `arrive: start braking ${r2(db)} m before the stop, 8.33 -> 0 m/s at ${a} m/s^2` },
    { t: 0, what: 'stopped at Truck_Stop_Dock (362.4, 0, 13)' },
    { t: r3(c0), what: `stop settle ${st} s (TV.settle) done; Store_A_Slot_N starts` },
    { t: r3(c0 + EVENTS.pick), what: 'pick A (Bed_Slot_01)' }, { t: r3(c0 + EVENTS.set), what: 'set A in Slot_N' },
    { t: r3(c0 + cl), what: 'Store_A ends at rest; Store_B_Slot_N+1 starts' },
    { t: r3(c0 + cl + EVENTS.pick), what: 'pick B (Bed_Slot_02): bed empty' },
    { t: r3(c0 + cl + hoistEnd), what: 'box B at carry (base 4.5, clears the FB-05 cab 3.8)' },
    { t: r3(c0 + cl + hoistEnd + st), what: `depart margin ${st} s done: pull-away starts` },
    { t: r3(c0 + cl + hoistEnd + st + tPull), what: `back at 8.33 m/s, ${r2(dA)} m past the stop` },
    { t: r3(c0 + 2 * cl), what: 'GC-1 back at rest (box B set in Slot_N+1 at ' + r3(c0 + cl + EVENTS.set) + '); the truck does not wait for this' }], c0 + cl + hoistEnd + st);
  const load = mk('load (2 boxes from Slot_N, Slot_N-1 onto the empty FB-05)', [
    { t: r3(-tArriveBrake), what: `arrive: start braking ${r2(db)} m before the stop` }, { t: 0, what: 'stopped at Truck_Stop_Dock' },
    { t: r3(c0), what: `stop settle ${st} s done; Load_A_Slot_N starts (crane at rest until the truck has stopped)` },
    { t: r3(c0 + EVENTS.set), what: 'set A on Bed_Slot_01' }, { t: r3(c0 + cl), what: 'Load_A ends; Load_B_Slot_N-1 starts' },
    { t: r3(c0 + cl + EVENTS.set), what: 'set B on Bed_Slot_02: bed full' }, { t: r3(c0 + cl + upEnd), what: 'hook back at carry (6.0, 2.6 m over the box tops)' },
    { t: r3(c0 + cl + upEnd + st), what: `depart margin ${st} s done: pull-away starts` }, { t: r3(c0 + cl + upEnd + st + tPull), what: 'back at 8.33 m/s' },
    { t: r3(c0 + 2 * cl), what: 'GC-1 back at rest' }], c0 + cl + upEnd + st);
  const fbLoopNoDock = 2 * SRC.cargo.refLoadSec + kThrough.T + SRC.cargo.walkOutSec + 2 * SRC.cargo.padUnloadSec + kBack.T;
  const boxGapMin = SRC.fillFloor + SRC.ht04_trip_s, supply = 60 / boxGapMin, crane = 60 / cl;
  return {
    source: SRC, truck: { v_mps: v, brake_mps2: a, accel_mps2: kAway.aS, brake_s: r3(tb), brake_m: r3(db), brake_s_profile: r3(tArriveBrake), pull_away_s: r3(tPull), pull_away_m: r3(dA), stop_settle_s: st, depart_margin_s: st,
      leg_ref_to_dock_s: r3(kIn.T), leg_dock_to_pad_s: r3(kAway.T), leg_ref_to_pad_no_stop_s: r3(kThrough.T), stop_penalty_s: r3(kIn.T + kAway.T - kThrough.T) },
    t_zero: 'truck stopped at Truck_Stop_Dock; negative t = braking in', store, load,
    throughput: { crane_boxes_per_min: r2(crane), crane_s_per_box: cl, crane_s_per_truck: 2 * cl,
      mining_box_supply_max_per_min: r2(supply), mining_box_supply_hard_cap_per_min: r2(60 / SRC.ht04_trip_s), hard_cap_rule: 'even with a zero fill (deposit taps) one HT-04 cannot dump more than once per 56.62 s trip', mining_rule: `1 sealed box per HT-04 dump; fastest dump gap = fill floor ${SRC.fillFloor} s (Chute Lv11) + trip ${SRC.ht04_trip_s} s = ${r2(boxGapMin)} s`,
      crane_headroom_x: r2(crane / supply), crane_headroom_vs_hard_cap_x: r2(crane * SRC.ht04_trip_s / 60), crane_utilisation_at_max_supply: r3(supply / crane),
      fb05_loop_no_dock_s: r2(fbLoopNoDock), fb05_loop_with_store_s: r2(fbLoopNoDock + store.added_trip_time_s), two_box_supply_gap_s: r2(2 * boxGapMin), fb05_loop_with_load_s: r2(fbLoopNoDock + load.added_trip_time_s),
      pallet_margin_store_s: r2(2 * boxGapMin - fbLoopNoDock - store.added_trip_time_s), pallet_margin_load_s: r2(2 * boxGapMin - fbLoopNoDock - load.added_trip_time_s),
      two_box_gap_at_hard_cap_s: r2(2 * SRC.ht04_trip_s), hard_cap_store_deficit_s_per_loop: r2(fbLoopNoDock + store.added_trip_time_s - 2 * SRC.ht04_trip_s),
      hard_cap_pallet_fill_min: r2((SRC.cargo.palletCap / ((fbLoopNoDock + store.added_trip_time_s) / SRC.ht04_trip_s - 2)) * (fbLoopNoDock + store.added_trip_time_s) / 60),
      crane_done_before_next_truck: 2 * cl + c0 < fbLoopNoDock,
      verdict: `GC-1 never halts mining before storage is full: ${r2(crane)} boxes/min against at most ${r2(supply)} (hard cap ${r2(60 / SRC.ht04_trip_s)}) supplied, and it finishes each 2-box truck (${r3(c0 + 2 * cl)} s) before the next FB-05 can arrive (loop >= ${r2(fbLoopNoDock)} s). At the mining peak the FB-05 loop with a dock stop (store ${r2(fbLoopNoDock + store.added_trip_time_s)} s, load ${r2(fbLoopNoDock + load.added_trip_time_s)} s) stays under the ${r2(2 * boxGapMin)} s 2-box supply gap, so the Refinery pallet (cap 8) does not back up. Only in the theoretical zero-fill case (${r2(2 * SRC.ht04_trip_s)} s per 2 boxes) would back-to-back store stops fall ${r2(fbLoopNoDock + store.added_trip_time_s - 2 * SRC.ht04_trip_s)} s behind per loop, filling the pallet after about ${r2((SRC.cargo.palletCap / ((fbLoopNoDock + store.added_trip_time_s) / SRC.ht04_trip_s - 2)) * (fbLoopNoDock + store.added_trip_time_s) / 60)} min; that limit is the flatbed's dwell, not GC-1 capacity.` } };
}
if (import.meta.url === 'file://' + process.argv[1]) console.log(JSON.stringify(dwell(), null, 1));
