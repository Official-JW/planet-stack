// Control Tower crew airlock walk-in / walk-out (Jacob approved clip r4, 11/14 2:02 PM PT:
// art_next/control_tower_1156/fix2/clip/control_tower_airlock_r4.mp4, md5 c2bbefed; HANDOFF_r4.md).
// Lv20 only (runs from ControlTower.update, which only ticks while the tower is active). Visual only:
// no sim state, no save, no taps (every mesh / sprite here has a no-op raycast).
//
// Order (clip r4): outer opens → crewman walks in to mid-vestibule → outer shuts → both side vents
// puff soft mist that fades in and out (1.7 s) → 0.3 s beat → inner opens → he walks through → inner
// shuts. Leaving is the same steps in reverse. Doors: the fix2 GLB's own Airlock_{Outer,Inner}_{Open,Close}
// clips (1.5 s, 0.66 m bi-parting slide, md5 2ab839e0), sampled as-is on the existing four leaves.
// Walker: a clone of the in-game male crew rig (Crew_2, same suit as the crew van) driven by the
// in-game crew walk: upper body = crew_walk_to_pad (crew_boarding_137a3b11.glb) bone tracks, phase-locked
// to the steps; feet = the clip r4 plan (port of build_boarding.py WALK rules: Ls 0.55 m, Tst 0.40 s,
// swing 0.8, lift 0.11, hip -0.065, heel-rise toe pivot, straddle rule, solved sill step, 2-plant turn,
// pelvis 0.8 lower + 0.2 upper boot) with 2-bone leg IK, at the game rig's own scale (k = 1).
// Trigger (HANDOFF r1-r4 do not say who or when): one ambient tower crewman on a fixed loop of game
// time (AL.period s) while the Lv20 tower is shown — enter, AL.dwellIn s inside (hidden), exit, stand on
// the apron, turn to the door, repeat. Not a sim crew member.

export const AL = {
  xOut: 4.40,      // apron stand (tower-local x; clip r4 start 27.95 / end 27.90 with the tower at x 23.5)
  xMid: 2.65,      // mid-vestibule (clip 26.15)
  xIn: 0.75,       // past the inner door (leaves at x 1.32-1.40; backer 1.20-1.28)
  vent: 1.7, beat: 0.3, closeLead: 0.4,   // clip r1-r4 vent window, beat, door-close lead before a walk ends
  outCloseLead: 0.2,                      // outer close lead on the way out (fix2 leaves close slower than the clip's 0.8 s)
  dwellIn: 12, outIdle: 2.5, period: 46,  // ambient loop (game seconds)
  startAt: 42,                            // loop time when the tower first shows (4 s before the walk-in)
};
const PI = Math.PI;
const sstep = (x) => { x = Math.min(Math.max(x, 0), 1); return x * x * (3 - 2 * x); };
const s5 = (x) => { x = Math.min(Math.max(x, 0), 1); return x * x * x * (x * (6 * x - 15) + 10); };
const tri = (t, a, b) => (t <= a ? 0 : t >= b ? 1 : (t - a) / (b - a));
const angdiff = (a, b) => ((((b - a + PI) % (2 * PI)) + 2 * PI) % (2 * PI)) - PI;
function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

// ---- floor under the walker (tower-local, ray-measured on the fix2 GLB at z 0 / ±0.3) ----
export function ground(x) {
  if (x < 1.20) return 0.321;   // tower floor past the inner door
  if (x < 1.30) return 0.359;
  if (x < 1.41) return 0.376;   // inner sill
  if (x < 3.63) return 0.359;   // vestibule floor
  if (x < 3.75) return 0.376;   // outer sill
  return 0.025;                 // apron
}

// ---- in-game WALK rules (build_boarding.py, as ported for clip r4) at the game rig scale ----
const W = { Ls: 0.55, Tst: 0.40, sw: 0.80, lift: 0.11, hip: -0.065 };
const HALF = 0.11, ANK = 0.0965, LEG = [0.4300, 0.4250];   // C2 rig: ankle above sole, thigh, shin
const TOE = [0, -ANK, 0.200];
const SOLE = [0.225, 0.15, 0.05, -0.05, -0.092].map((f) => [0, -ANK, f]);
const SIDE = { L: 1, R: -1 };
// foot-local (x left, y up, z forward) → tower-local, yaw about +Y (yaw 0 faces +Z), pitch about +X (+ = toe down)
function rot(v, yaw, pitch) {
  const cp = Math.cos(pitch), sp = Math.sin(pitch), y = v[1] * cp - v[2] * sp, z = v[1] * sp + v[2] * cp;
  const cy = Math.cos(yaw), sy = Math.sin(yaw); return [v[0] * cy + z * sy, y, -v[0] * sy + z * cy];
}
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const lerp3 = (a, b, h) => [a[0] + (b[0] - a[0]) * h, a[1] + (b[1] - a[1]) * h, a[2] + (b[2] - a[2]) * h];
const leftv = (yaw) => [Math.cos(yaw), 0, -Math.sin(yaw)];
const plant = (p) => [p[0], ground(p[0]) + ANK, p[2]];

function soleOk(p, yaw, pitch, margin) {
  for (const q of SOLE.concat([[0, -ANK + 0.01, 0.229], [0, -ANK + 0.02, -0.093]])) {
    const w = add(p, rot(q, yaw, pitch)); if (w[1] < ground(w[0]) + margin - 1e-6) return false;
  }
  return true;
}
function stepProf(pr, p0, p1, u) {
  const [u0, ud] = pr, up = p1[1] > p0[1], zU = Math.max(p0[1], p1[1]) + 0.05;
  const h = u > u0 ? sstep((u - u0) / (1 - u0)) : 0; const p = lerp3(p0, p1, h); let z;
  if (up) { z = u < ud ? p0[1] + (zU - p0[1]) * sstep(u / Math.max(1e-3, ud)) : zU; z -= (zU - p1[1]) * sstep((u - 0.85) / 0.15); }
  else z = u < ud ? p0[1] + (zU - p0[1]) * sstep(u / 0.2) : zU - (zU - p1[1]) * sstep((u - ud) / (1 - ud));
  p[1] = z; return p;
}
function solveStep(p0, p1, y0, y1) {
  const up = p1[1] > p0[1], c = [];
  if (up) { for (const u0 of [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]) for (const ud of [0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]) c.push([u0, ud]); }
  else for (const ud of [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75]) c.push([0, ud]);
  for (const pr of c) {
    let ok = true;
    for (let i = 0; i <= 40 && ok; i++) {
      const u = i / 40, p = stepProf(pr, p0, p1, u);
      const pitch = 0.28 * (1 - sstep(u * 2.2)) - 0.22 * Math.sin(PI * Math.min(1, Math.max(0, (u - 0.35) / 0.65))) * 0.9;
      if (!soleOk(p, y0 + angdiff(y0, y1) * s5(u), pitch, (u > 0.12 && u < 0.9) ? 0.01 : -0.015)) ok = false;
    }
    if (ok) return pr;
  }
  return c[c.length - 1];
}

class Plan {
  constructor(x, z, yaw) {
    this.pos = [x, 0, z]; this.yaw = yaw; this.t = 0; this.segs = []; this.feet = { L: [], R: [] };
    this.init = {}; for (const s of 'LR') this.init[s] = [plant(add(this.pos, leftv(yaw).map((v) => v * HALF * SIDE[s]))), yaw];
  }
  last(s) { const f = this.feet[s]; return f.length ? [f[f.length - 1].pos, f[f.length - 1].yaw] : this.init[s]; }
  idle(t1) { if (t1 > this.t) { this.segs.push([this.t, t1, 'idle', { pos: this.pos.slice(), yaw: this.yaw }]); this.t = t1; } }
  snap(x, yaw) {   // hidden re-plant (inside the tower, behind the shut inner door)
    this.pos = [x, 0, this.pos[2]]; this.yaw = yaw;
    for (const s of 'LR') this.feet[s].push({ t0: this.t, t1: this.t, pos: plant(add(this.pos, leftv(yaw).map((v) => v * HALF * SIDE[s]))), yaw, kind: 'snap', arc: 0 });
  }
  turn(d, each = 0.75) {   // two in-game turn() calls back to back (2 plants each, one boot always down), body yaw one s5 curve
    const t0 = this.t, y0 = this.yaw, first = d > 0 ? 'L' : 'R', second = first === 'L' ? 'R' : 'L';
    for (let h = 0; h < 2; h++) {
      const y1 = y0 + d * (h + 1) / 2, th = t0 + h * each;
      [first, second].forEach((s, i) => { const a = th + i * each * 0.5;
        this.feet[s].push({ t0: a, t1: a + each * 0.5, pos: plant(add(this.pos, leftv(y1).map((v) => v * HALF * SIDE[s]))), yaw: y1, kind: 'turn', arc: 0.06 }); });
    }
    this.segs.push([t0, t0 + 2 * each, 'turn', { pos: this.pos.slice(), y0, y1: y0 + d }]); this.yaw = y0 + d; this.t = t0 + 2 * each;
  }
  walk(x1) {
    const x0 = this.pos[0], z0 = this.pos[2], L = Math.abs(x1 - x0), dirn = x1 > x0 ? 1 : -1, yaw = dirn > 0 ? PI / 2 : -PI / 2;
    const N = Math.max(1, Math.ceil(L / W.Ls - 1e-9)), Ls = L / N, Tst = W.Tst * Math.sqrt(Ls / W.Ls), Tsw = W.sw * Tst;
    const t0 = this.t, st = [0]; for (let j = 1; j <= N; j++) st.push(j * Ls); st.push(L);
    const steps = [];
    for (let j = 1; j <= N + 1; j++) {
      const s = (j - 1) % 2 === 0 ? 'L' : 'R', a = t0 + (j - 1) * Tst, b = a + Tsw; let sj = st[j];
      for (const ds of [0, -0.05, 0.05, -0.1, 0.1, -0.15, 0.15, -0.2, 0.2, -0.25, 0.25]) {   // straddle rule: whole sole on one level
        const pq = add([x0 + dirn * (sj + ds), 0, z0], leftv(yaw).map((v) => v * HALF * SIDE[s])), pa = add(pq, [0, ANK, 0]);
        const gs = SOLE.map((q) => ground(add(pa, rot(q, yaw, 0))[0])).concat([0.29, -0.15].map((f) => ground(add(pq, rot([0, 0, f], yaw, 0))[0])));
        if (Math.max(...gs) - Math.min(...gs) < 0.01 && sj + ds <= L + 1e-6) { sj += ds; break; }
      }
      const p = plant(add([x0 + dirn * sj, 0, z0], leftv(yaw).map((v) => v * HALF * SIDE[s])));
      this.feet[s].push({ t0: a, t1: b, pos: p, yaw, kind: 'walk', arc: W.lift }); steps.push([a, b, s, sj]);
    }
    const t1 = t0 + N * Tst + Tsw;
    this.segs.push([t0, t1, 'walk', { x0, z0, dirn, yaw, steps, Tst, Tsw, N, Ls }]);
    this.pos = [x1, 0, z0]; this.yaw = yaw; this.t = t1;
  }
  seg(t) { for (const g of this.segs) if (g[0] <= t && t < g[1]) return g; return this.segs[this.segs.length - 1]; }
  foot(s, t) {
    let prev = this.init[s];
    for (const e of this.feet[s]) {
      if (t < e.t0) {
        if (e.kind === 'walk') { const hr = 0.28 * tri(t, e.t0 - 0.16, e.t0);
          if (hr > 0) { const toe = add(prev[0], rot(TOE, prev[1], 0)); return [add(toe, rot(TOE.map((v) => -v), prev[1], hr)), prev[1], hr]; } }
        return [prev[0], prev[1], 0];
      }
      if (t < e.t1) {
        const u = (t - e.t0) / (e.t1 - e.t0), y0 = prev[1]; let p0 = prev[0], pitch0 = 0;
        if (e.kind === 'walk') { pitch0 = 0.28; const toe = add(p0, rot(TOE, y0, 0)); p0 = add(toe, rot(TOE.map((v) => -v), y0, 0.28)); }
        const h = sstep(u), ua = e.kind === 'walk' ? Math.min(1, u / 0.85) : u;
        let p = lerp3(p0, e.pos, h); p[1] += e.arc * Math.pow(Math.sin(PI * ua), 1.2);
        if (e.kind === 'walk' && Math.abs(e.pos[1] - prev[0][1]) > 0.05) { if (!e.prof) e.prof = solveStep(p0, e.pos, y0, e.yaw); p = stepProf(e.prof, p0, e.pos, u); }
        const yw = y0 + angdiff(y0, e.yaw) * s5(u);
        const pitch = e.kind === 'walk' ? pitch0 * (1 - sstep(u * 2.2)) - 0.22 * Math.sin(PI * Math.min(1, Math.max(0, (u - 0.35) / 0.65))) * 0.9 : 0;
        return [p, yw, pitch];
      }
      prev = [e.pos, e.yaw];
    }
    return [prev[0], prev[1], 0];
  }
  footFinal(s, t) {   // no toe / heel below the floor (raise the ankle)
    const [p, yw, pt] = this.foot(s, t); let low = 1e9;
    for (const q of SOLE) { const w = add(p, rot(q, yw, pt)); low = Math.min(low, w[1] - ground(w[0])); }
    return low < 0.0015 ? [[p[0], p[1] + 0.0015 - low, p[2]], yw, pt] : [p, yw, pt];
  }
  body(t) {
    const g = this.seg(t), kind = g[2], D = g[3]; let pos, yaw, amp = 0, hips = -0.012, walkSeg = null;
    if (kind === 'idle') { pos = D.pos.slice(); yaw = D.yaw; }
    else if (kind === 'turn') { const u = s5((t - g[0]) / (g[1] - g[0])); pos = D.pos.slice(); yaw = D.y0 + (D.y1 - D.y0) * u; }
    else {
      const ss = [];
      for (const s of 'LR') { let sv = 0;
        for (const [a, b, fs, sj] of D.steps) { if (fs !== s) continue; if (t >= b) sv = sj; else if (t > a) { sv += (sj - sv) * s5((t - a) / (b - a)); break; } else break; }
        ss.push(sv); }
      const sb = (ss[0] + ss[1]) / 2; pos = [D.x0 + D.dirn * sb, 0, D.z0]; yaw = D.yaw; walkSeg = g;
      const x = (t - g[0]) / D.Tst; amp = tri(t, g[0], g[0] + D.Tst * 1.2) * (1 - tri(t, g[1] - D.Tst * 1.2, g[1]));
      hips = -0.012 + (W.hip + 0.012 + 0.016 * Math.pow(Math.sin(PI * x), 2)) * amp;
    }
    const dys = [];   // pelvis rides with the plants: 0.8 lower boot + 0.2 upper boot
    for (const s of 'LR') { let dv = this.init[s][0][1] - ANK;
      for (const e of this.feet[s]) { const g1 = e.pos[1] - ANK; if (e.t1 <= t) dv = g1; else if (e.t0 < t) { dv += (g1 - dv) * s5((t - e.t0) / (e.t1 - e.t0)); break; } else break; }
      dys.push(dv); }
    pos[1] = 0.8 * Math.min(...dys) + 0.2 * Math.max(...dys);
    return { pos, yaw, amp, hips, kind, walkSeg };
  }
}

// ---- the loop: plan + door / vent events (cycle-local seconds) ----
export function buildLoop(DS) {
  const P = new Plan(AL.xOut, 0, -PI / 2), ev = [], vents = [], mark = {};
  ev.push(['outer', 'open', 0]); P.idle(DS); mark.walkIn0 = P.t;
  P.walk(AL.xMid); mark.walkIn1 = P.t;
  const oc = P.t - AL.closeLead; ev.push(['outer', 'close', oc]); vents.push([oc + DS, oc + DS + AL.vent]);
  const io = oc + DS + AL.vent + AL.beat; ev.push(['inner', 'open', io]); P.idle(io + DS); mark.through0 = P.t;
  P.walk(AL.xIn); mark.through1 = P.t; ev.push(['inner', 'close', P.t]); mark.hide = P.t + DS;
  const tx = mark.hide + AL.dwellIn; P.idle(tx); P.snap(AL.xIn, PI / 2); mark.show = tx;
  ev.push(['inner', 'open', tx]); P.idle(tx + DS); mark.back0 = P.t;
  P.walk(AL.xMid); mark.back1 = P.t;
  const ic = P.t - AL.closeLead; ev.push(['inner', 'close', ic]); vents.push([ic + DS, ic + DS + AL.vent]);
  const oo = ic + DS + AL.vent + AL.beat; ev.push(['outer', 'open', oo]); P.idle(oo + DS); mark.out0 = P.t;
  P.walk(AL.xOut); mark.out1 = P.t; ev.push(['outer', 'close', P.t - AL.outCloseLead]);
  P.idle(P.t + AL.outIdle); mark.turn0 = P.t; P.turn(PI); mark.turn1 = P.t;
  const period = Math.max(AL.period, P.t + 2); P.idle(period + 1);
  ev.sort((a, b) => a[2] - b[2]);
  return { P, ev, vents, mark, period, DS };
}

// ---- soft mist: camera-facing sprites, radial falloff (clip r4 FX recipe), both side vents ----
function mistTexture(THREE, seed) {
  const n = 64, c = document.createElement('canvas'); c.width = c.height = n; const g = c.getContext('2d'), r = rng(seed);
  const im = g.createImageData(n, n);
  const blobs = []; for (let i = 0; i < 7; i++) blobs.push([n * (0.3 + 0.4 * r()), n * (0.3 + 0.4 * r()), n * (0.12 + 0.14 * r()), 0.5 + 0.5 * r()]);
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    const dx = (x + 0.5) / n * 2 - 1, dy = (y + 0.5) / n * 2 - 1, d = Math.sqrt(dx * dx + dy * dy);
    let a = Math.pow(Math.max(0, 1 - d), 1.4);
    let nz = 0; for (const [bx, by, br, bw] of blobs) { const e = ((x - bx) ** 2 + (y - by) ** 2) / (br * br); nz += bw * Math.exp(-e); }
    a *= 0.25 + 0.75 * Math.min(1, 0.45 + nz * 0.6);
    const k = (y * n + x) * 4; im.data[k] = 255; im.data[k + 1] = 255; im.data[k + 2] = 255; im.data[k + 3] = Math.round(255 * Math.min(1, a));
  }
  g.putImageData(im, 0, 0); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
// emitters (tower-local): interior grills as in the clip (S blows north, N angled to the inner door),
// plus the vent outlets on both outside walls (z ±1.25) so the purge reads with the vestibule shut.
const EMIT = [
  { k: 'in_S', c: [2.05, 1.45, 1.16], sx: 0.22, sy: 0.12, dir: [0, 0.18, -1], v: [0.95, 1.45], r1: [0.24, 0.36], n: 14 },
  { k: 'in_N', c: [1.80, 1.45, -1.16], sx: 0.22, sy: 0.12, dir: [-0.80, 0.15, 0.55], v: [2.3, 3.4], r1: [0.29, 0.43], n: 14 },
  { k: 'out_S', c: [2.50, 1.50, 1.28], sx: 0.70, sy: 0.30, dir: [0, 0.30, 1], v: [1.2, 1.9], r1: [0.55, 0.85], n: 18 },
  { k: 'out_N', c: [2.50, 1.50, -1.28], sx: 0.70, sy: 0.30, dir: [0, 0.30, -1], v: [1.2, 1.9], r1: [0.55, 0.85], n: 18 },
];
function buildMist(vents) {
  const r = rng(4104), parts = [];
  vents.forEach(([w0, w1], wi) => {
    for (const E of EMIT) {
      const dn = Math.hypot(...E.dir), dv = E.dir.map((v) => v / dn), side = Math.abs(dv[2]) > 0.9 ? [1, 0, 0] : [0, 0, 1];
      for (let i = 0; i < E.n; i++) {
        const tb = w0 + 0.05 + 1.0 * (i + r() * 0.8) / E.n;
        const life = Math.min(0.75 + r() * 0.4, w1 + 0.35 - tb);
        const p0 = [E.c[0] + side[0] * (r() * 2 - 1) * E.sx, E.c[1] + (r() * 2 - 1) * E.sy, E.c[2] + side[2] * (r() * 2 - 1) * E.sx];
        const j = [side[0] * (r() - 0.5) * 0.5, -0.12 + r() * 0.32, side[2] * (r() - 0.5) * 0.5];
        let v0 = [dv[0] + j[0], dv[1] + j[1], dv[2] + j[2]]; const vn = Math.hypot(...v0), sp = E.v[0] + r() * (E.v[1] - E.v[0]); v0 = v0.map((v) => v / vn * sp);
        parts.push({ w: wi, k: E.k, tb, life, p0, v0, r0: 0.045 + r() * 0.025, r1: E.r1[0] + r() * (E.r1[1] - E.r1[0]), peak: 0.70 + r() * 0.20, tex: i % 3 });
      }
    }
  });
  return parts;
}

export function createCtAirlock(THREE, D) {
  const A = { ready: false, failed: '', root: null, t: AL.startAt, hold: false, loop: null, doors: {}, dclips: {}, walker: null, bones: {}, mist: [], visible: false, ik: {} };
  const _v1 = new THREE.Vector3(), _v2 = new THREE.Vector3(), _v3 = new THREE.Vector3(), _q1 = new THREE.Quaternion(), _q2 = new THREE.Quaternion(), _q3 = new THREE.Quaternion();
  const UPPER = ['C2_Hips', 'C2_Spine', 'C2_Chest', 'C2_Neck', 'C2_Head', 'C2_UpperArm_L', 'C2_Forearm_L', 'C2_Hand_L', 'C2_UpperArm_R', 'C2_Forearm_R', 'C2_Hand_R'];
  const LEGS = ['C2_Thigh_L', 'C2_Shin_L', 'C2_Foot_L', 'C2_Thigh_R', 'C2_Shin_R', 'C2_Foot_R'];
  const G0 = 2.067, GP = 0.8, IDLE_T = 0.2;   // crew_walk_to_pad: C2 steady cycle from the left ankle rise at 2.067 s (0.8 s, 2 steps); standing at 0.2 s
  const noRay = () => {};

  function setup(ctRoot, animations) {   // once the fix2 GLB is in
    A.root = ctRoot;
    for (const n of ['Airlock_Door_Outer_S', 'Airlock_Door_Outer_N', 'Airlock_Door_Inner_S', 'Airlock_Door_Inner_N']) {
      const o = ctRoot.getObjectByName(n); if (o) A.doors[n] = { o, rest: o.position.clone() };
    }
    for (const c of animations || []) {
      const m = /^Airlock_(Outer|Inner)_(Open|Close)$/.exec(c.name); if (!m) continue;
      const tr = {}; for (const t of c.tracks) { const [node, prop] = t.name.split('.'); if (prop === 'position') tr[node] = t.createInterpolant(); }
      A.dclips[m[1].toLowerCase() + '_' + m[2].toLowerCase()] = { dur: c.duration, tr };
    }
    if (Object.keys(A.dclips).length !== 4 || Object.keys(A.doors).length !== 4) { A.failed = 'airlock clips / leaves missing'; return; }
    A.loop = buildLoop(A.dclips.outer_open.dur);
    A.grp = new THREE.Group(); A.grp.name = 'CT_Airlock_FX'; ctRoot.add(A.grp);
    const tex = [mistTexture(THREE, 11), mistTexture(THREE, 23), mistTexture(THREE, 37)];
    for (const p of buildMist(A.loop.vents)) {
      const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex[p.tex], color: 0xe6efff, transparent: true, opacity: 0, depthWrite: false, fog: false }));
      s.name = 'CT_Mist_' + p.k; s.visible = false; s.raycast = noRay; s.renderOrder = 3; s.castShadow = false;
      s.material.rotation = (p.tb * 7.3) % (2 * PI);
      A.grp.add(s); A.mist.push({ s, p });
    }
  }

  function cloneRig(src) {   // same skinned clone as the crew van (bones rebound by name)
    const c = src.clone(true), by = {}; c.traverse((o) => { if (o.isBone || o.type === 'Bone') by[o.name] = o; });
    c.traverse((o) => { if (!o.isSkinnedMesh) return; const sk = o.skeleton;
      o.bind(new THREE.Skeleton(sk.bones.map((b) => by[b.name] || b), sk.boneInverses.map((m) => m.clone())), o.bindMatrix.clone());
      o.material = [].concat(o.material).map((m) => { const n = m.clone(); n.transparent = false; n.opacity = 1; n.depthWrite = true; return n; }); if (o.material.length === 1) o.material = o.material[0];
      o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; o.visible = true; });
    c.position.set(0, 0, 0); c.rotation.set(0, 0, 0); c.scale.set(1, 1, 1); c.visible = true;
    c.traverse((o) => { o.raycast = noRay; if (/_Root$/.test(o.name) && Math.min(o.scale.x, o.scale.y, o.scale.z) < .01) o.scale.set(1, 1, 1); });
    return c;
  }

  function tryBind() {   // crew rig + crew_walk_to_pad come from the crew boarding GLB (loaded by main.js)
    if (A.walker || !A.loop || A.failed) return;
    const src = D && D.crewTemplate && D.crewTemplate(), clip = D && D.walkClip && D.walkClip();
    if (!src || !clip) return;
    const rig = cloneRig(src); rig.name = 'CT_Airlock_Crew';
    const B = {}; rig.traverse((o) => { if (o.isBone) B[o.name] = o; });
    if (!B.C2_Root || LEGS.some((n) => !B[n]) || UPPER.some((n) => !B[n])) { A.failed = 'crew rig bones missing'; return; }
    const ip = {}; for (const t of clip.tracks) { const [node, prop] = t.name.split('.'); if (prop === 'quaternion' && (UPPER.includes(node) || LEGS.includes(node))) ip[node] = t.createInterpolant(); }
    if (UPPER.some((n) => !ip[n])) { A.failed = 'crew_walk_to_pad tracks missing'; return; }
    const at = (n, t) => new THREE.Quaternion().fromArray(ip[n].evaluate(t));
    A.idle = {}; for (const n of UPPER.concat(LEGS)) A.idle[n] = ip[n] ? at(n, IDLE_T) : B[n].quaternion.clone();
    A.ip = ip; A.bones = B; A.walker = rig; A.grp.add(rig);
    // foot rest orientation (tower frame) at yaw 0 in the standing pose
    B.C2_Root.position.set(0, 0, 0); B.C2_Root.quaternion.identity(); for (const n in A.idle) B[n].quaternion.copy(A.idle[n]);
    A.grp.updateMatrixWorld(true); const ctq = A.root.getWorldQuaternion(new THREE.Quaternion()).invert();
    for (const s of 'LR') { const f = B['C2_Foot_' + s]; A.ik[s] = { foot0: ctq.clone().multiply(f.getWorldQuaternion(new THREE.Quaternion())) }; }
    A.dip = buildDip(); A.ready = true; pose(A.t);
  }

  function buildDip() {   // pelvis dip where a leg can't reach (smooth ±15-frame envelope; clip r4 / in-game hf22 idea)
    const P = A.loop.P, N = Math.ceil(A.loop.period * 60) + 1, reach = (LEG[0] + LEG[1]) * 0.985, short = new Float32Array(N), dip = new Float32Array(N);
    for (let i = 0; i < N; i++) { const t = i / 60, b = P.body(t); let sh = 0;
      for (const s of 'LR') { const [p] = P.footFinal(s, t), l = leftv(b.yaw), hp = [b.pos[0] + l[0] * 0.1 * SIDE[s], b.pos[1] + b.hips + 0.9368, b.pos[2] + l[2] * 0.1 * SIDE[s]];
        sh = Math.max(sh, Math.hypot(p[0] - hp[0], p[1] - hp[1], p[2] - hp[2]) - reach); }
      short[i] = Math.max(0, sh); }
    for (let i = 0; i < N; i++) { let d = 0; for (let j = Math.max(0, i - 15); j < Math.min(N, i + 16); j++) if (short[j] > 0) d = Math.max(d, (short[j] + 0.004) * (1 - ((j - i) / 15) ** 2) ** 2); dip[i] = d; }
    return dip;
  }

  function doorsAt(t) {
    const L = A.loop, last = {};
    for (const [k, a, t0] of L.ev) if (t0 <= t) last[k] = [a, t0];
    for (const k of ['outer', 'inner']) {
      const cap = k[0].toUpperCase() + k.slice(1);
      for (const s of ['S', 'N']) {
        const n = 'Airlock_Door_' + cap + '_' + s, d = A.doors[n]; if (!d) continue;
        if (!last[k]) { d.o.position.copy(d.rest); continue; }
        const c = A.dclips[k + '_' + last[k][0]], it = c.tr[n];
        if (!it) { d.o.position.copy(d.rest); continue; }
        d.o.position.fromArray(it.evaluate(Math.min(c.dur, Math.max(0, t - last[k][1]))));
      }
    }
  }

  function mistAt(t) {
    for (const { s, p } of A.mist) {
      const tau = t - p.tb;
      if (tau < 0 || tau > p.life) { s.visible = false; continue; }
      const a = p.peak * sstep(tau / 0.16) * (1 - sstep((tau - 0.30 * p.life) / (0.70 * p.life)));
      const dr = (1 - Math.exp(-2.3 * tau)) / 2.3, r = p.r0 + (p.r1 - p.r0) * (1 - Math.exp(-2.4 * tau));
      s.position.set(p.p0[0] + p.v0[0] * dr, p.p0[1] + p.v0[1] * dr + 0.06 * tau * tau, p.p0[2] + p.v0[2] * dr);
      s.scale.set(2 * r, 2 * r, 1); s.material.opacity = a; s.visible = a > 0.003;
    }
  }

  function legIK(s, target, fyaw, fpitch, fwd) {
    const B = A.bones, th = B['C2_Thigh_' + s], sh = B['C2_Shin_' + s], ft = B['C2_Foot_' + s];
    const H = th.getWorldPosition(new THREE.Vector3()), K = sh.getWorldPosition(new THREE.Vector3()), Ak = ft.getWorldPosition(new THREE.Vector3());
    const l1 = K.distanceTo(H), l2 = Ak.distanceTo(K), T = target;
    const d = _v1.subVectors(T, H), dl = d.length(), r = Math.min(dl, (l1 + l2) * 0.9995), e = d.clone().normalize();
    const n = fwd.clone().addScaledVector(e, -fwd.dot(e)); if (n.lengthSq() < 1e-8) n.set(0, 0, 1); n.normalize();
    const a = (l1 * l1 - l2 * l2 + r * r) / (2 * r), h = Math.sqrt(Math.max(0, l1 * l1 - a * a));
    const K2 = H.clone().addScaledVector(e, a).addScaledVector(n, h), A2 = H.clone().addScaledVector(e, r);
    const rotate = (bone, from, to) => {
      _q1.setFromUnitVectors(from.normalize(), to.normalize());
      bone.getWorldQuaternion(_q2); _q2.premultiply(_q1); bone.parent.getWorldQuaternion(_q3); bone.quaternion.copy(_q3.invert().multiply(_q2)); bone.updateMatrixWorld(true);
    };
    rotate(th, _v2.subVectors(K, H), _v3.subVectors(K2, H));
    const K3 = sh.getWorldPosition(new THREE.Vector3()), A3 = ft.getWorldPosition(new THREE.Vector3());
    rotate(sh, _v2.subVectors(A3, K3), _v3.subVectors(A2, K3));
    // foot: plan yaw / pitch on the standing foot orientation
    const ctq = A.root.getWorldQuaternion(new THREE.Quaternion());
    const want = ctq.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), fyaw)).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), fpitch)).multiply(A.ik[s].foot0);
    ft.parent.getWorldQuaternion(_q3); ft.quaternion.copy(_q3.invert().multiply(want)); ft.updateMatrixWorld(true);
    return dl - r;
  }

  function walkerAt(t) {
    const L = A.loop, m = L.mark, B = A.bones, w = A.walker; if (!w) return;
    const hidden = t >= m.hide && t < m.show; w.visible = !hidden; if (hidden) return;
    const P = L.P, b = P.body(t), dip = A.dip[Math.min(A.dip.length - 1, Math.max(0, Math.round(t * 60)))] || 0;
    B.C2_Root.position.set(b.pos[0], b.pos[1] + b.hips - dip, b.pos[2]); B.C2_Root.quaternion.setFromAxisAngle(_v1.set(0, 1, 0), b.yaw);
    // upper body: crew_walk_to_pad, phase-locked to this walk's steps (left ankle rise ↔ 2.067 s), blended from standing by the walk amp
    let g = -1; if (b.walkSeg && b.amp > 0) { const S = b.walkSeg, Tst = S[3].Tst; g = G0 + ((((t - (S[0] - 0.16)) / Tst * (GP / 2)) % GP) + GP) % GP; }
    for (const n of UPPER) { const q = B[n].quaternion.copy(A.idle[n]); if (g >= 0) q.slerp(_q1.fromArray(A.ip[n].evaluate(g)), b.amp); }
    for (const n of LEGS) B[n].quaternion.copy(A.idle[n]);
    w.updateMatrixWorld(true);
    const fwd = new THREE.Vector3(Math.sin(b.yaw), 0, Math.cos(b.yaw)).transformDirection(A.root.matrixWorld);
    let worst = 0;
    for (const s of 'LR') { const [p, yw, pt] = P.footFinal(s, t); const T = new THREE.Vector3(p[0], p[1], p[2]).applyMatrix4(A.root.matrixWorld); worst = Math.max(worst, legIK(s, T, yw, pt, fwd)); }
    A.reachShort = worst;
  }

  function pose(t) {
    if (!A.loop) return;
    A.root.updateMatrixWorld(true);
    doorsAt(t); mistAt(t); if (A.walker) walkerAt(t);
  }

  function update(dt) {
    if (!A.loop || A.failed) return false;
    if (!A.walker) tryBind();
    if (!A.ready) return false;   // doors stay shut (ControlTower.holdDoors) until the crew rig is in
    if (!A.hold) A.t = (A.t + dt) % A.loop.period;
    pose(A.t); return true;
  }
  function seek(t) { A.t = ((t % A.loop.period) + A.loop.period) % A.loop.period; if (A.ready) pose(A.t); return A.t; }
  function setVisible(on) { if (A.grp) A.grp.visible = !!on; }
  function info() {
    const L = A.loop; if (!L) return { ready: false, failed: A.failed };
    return { ready: A.ready, failed: A.failed, t: +A.t.toFixed(3), period: L.period, doorSec: L.DS, ev: L.ev.map(([k, a, t]) => [k, a, +t.toFixed(3)]), vents: L.vents.map((v) => v.map((x) => +x.toFixed(3))),
      mark: Object.fromEntries(Object.entries(L.mark).map(([k, v]) => [k, +v.toFixed(3)])), segs: L.P.segs.map((g) => [+g[0].toFixed(3), +g[1].toFixed(3), g[2]]), mist: A.mist.length, reachShort: A.reachShort };
  }
  return { A, AL, setup, update, seek, pose, tryBind, setVisible, info };
}
