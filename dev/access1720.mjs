// Crew access for the PR17 channel ladder (1015 packet). Pure timing / IK. The scene binder is access1720_bind.mjs.
// Rungs are read from the deployed ladder meshes (centers of the cross-bars). Feet plant on those
// centers; hands grip the side rails via gripAt. The rail fold is a rotation plus a bend, so the shipped clip keeps its morphs.

// 1015 packet: BayDoor_Open/Close 1.0s, Ladder_Deploy/Stow 4.375s (LINEAR clamp).
export const BAY_DOOR_SEC = 1.0;
// 1015 packet: Ladder_Deploy/Stow are 4.375s (restored from 78c19d1; v10 solid had shortened to 3.0 and truncated telescope).
export const LADDER_DEPLOY_SEC = 4.375;
export const LADDER_STOW_SEC = 4.375;
export const ENTRY_DOOR_SEC = 1.0; // EntryDoor_Open/Close (1123 airlock)
export const DEPLOY_T = BAY_DOOR_SEC + LADDER_DEPLOY_SEC; // when ladder is fully out
export const DOOR_SEC = BAY_DOOR_SEC; // alias used by show/camera timing
// Legacy single-clip scrub constants (1827). Kept so older verify scripts import cleanly.
export const STOW_T0 = LADDER_DEPLOY_SEC;
export const CLIP_END = LADDER_DEPLOY_SEC + LADDER_STOW_SEC;
export const STOW_TEL_T1 = LADDER_DEPLOY_SEC;
export const STOW_TEL_SEC = LADDER_STOW_SEC;
export const STOW_SLIDE_SEC = BAY_DOOR_SEC;
export const CLIMB_V = 0.8;                // m/s up the rungs
export const STAGE_TRAVEL = 4.678333;
export const RUNGS_PER_STAGE = 16;
export const RUNG_PITCH = STAGE_TRAVEL / RUNGS_PER_STAGE;
export const RUNG_LY0 = -0.25;
export const HAND_SPAN = 5;
export const STEP_SEC = 0.50;
export function stageRungLocals() {
  const out = [];
  for (let i = 0; i < RUNGS_PER_STAGE; i++) out.push(RUNG_LY0 - i * RUNG_PITCH);
  return out;
}
export function climbSteps(rungs) { return Math.max(1, rungs.length - 1); }
export const CLIMB_GAP_M = 1.5;            // next climber starts when previous is ~1.5 m up
export const GAP = 1.5;                   // fallback seconds if rung dy missing
export const WALK_V = 1.4;
export const PALM = 0.10;                 // wrist → palm, along the forearm. Fingers wrap the rung.
export const RAIL_CTC = 0.50;
export const RAIL_HALF = 0.25;
export const GRIP_OUT = 0.11;
export function sideDir(outward) { return { x: outward.z, y: 0, z: -outward.x }; }
export function gripAt(rung, limb, outward) {
  if (limb[1] !== 'H') return rung;
  const sign = limb[0] === 'L' ? -1 : 1;
  return add(rung, add(mul(sideDir(outward), sign * RAIL_HALF), mul(outward, GRIP_OUT)));
}
export const SOLE = 0.07;                 // ankle → sole, world down
export const UPPER = Math.hypot(0.0654689, 0.290664, 0.035048);
export const FORE = Math.hypot(0.0335623, 0.225372, 0.114481);
export const THIGH = Math.hypot(0, 0.429914, 0.00859942);
export const SHIN = Math.hypot(0, 0.424915, 0.00849942);
export const HIP_Y = 0.936829;
export const SHOULDER_L = { x: 0.20, y: 0.135 + 0.13 + 0.215, z: 0 };
export const SHOULDER_R = { x: -0.20, y: SHOULDER_L.y, z: 0 };
export const HIP_L = { x: 0.10, y: 0, z: 0 };
export const HIP_R = { x: -0.10, y: 0, z: 0 };
export const add = (a, b) => ({ x: a.x + b.x, y: a.y + b.y, z: a.z + b.z });
export const sub = (a, b) => ({ x: a.x - b.x, y: a.y - b.y, z: a.z - b.z });
export const mul = (a, s) => ({ x: a.x * s, y: a.y * s, z: a.z * s });
export const dot = (a, b) => a.x * b.x + a.y * b.y + a.z * b.z;
export const cross = (a, b) => ({ x: a.y * b.z - a.z * b.y, y: a.z * b.x - a.x * b.z, z: a.x * b.y - a.y * b.x });
export const len = (a) => Math.hypot(a.x, a.y, a.z);
export function norm(a) { const L = len(a) || 1; return mul(a, 1 / L); }
export const U_FORE = norm({ x: 0.0654689, y: -0.290664, z: 0.035048 });
export const U_HAND = norm({ x: 0.0335623, y: -0.225372, z: 0.114481 });
export const U_SHIN = norm({ x: 0, y: -0.429914, z: 0.00859942 });
export const U_FOOT = norm({ x: 0, y: -0.424915, z: -0.00849942 });
export const U_FORE_R = { x: -U_FORE.x, y: U_FORE.y, z: U_FORE.z };
export const U_HAND_R = { x: -U_HAND.x, y: U_HAND.y, z: U_HAND.z };
export function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
export function lerp(a, b, t) { return a + (b - a) * t; }
export function lerp3(a, b, t) { return add(a, mul(sub(b, a), t)); }
export function quatNorm(q) { const L = Math.hypot(q.x, q.y, q.z, q.w) || 1; return { x: q.x / L, y: q.y / L, z: q.z / L, w: q.w / L }; }
export function quatMul(a, b) {
  return {
    x: a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
    y: a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
    z: a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
    w: a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
  };
}
export function quatInv(q) { return { x: -q.x, y: -q.y, z: -q.z, w: q.w }; }
export function quatRotate(q, v) {
  const r = quatMul(quatMul(q, { x: v.x, y: v.y, z: v.z, w: 0 }), quatInv(q));
  return { x: r.x, y: r.y, z: r.z };
}
export function quatFromTo(u, v) {
  const c = cross(u, v), d = dot(u, v);
  if (d >= 0.999999) return { x: 0, y: 0, z: 0, w: 1 };
  if (d <= -0.999999) {
    let ax = cross(u, { x: 1, y: 0, z: 0 });
    if (len(ax) < 1e-4) ax = cross(u, { x: 0, y: 1, z: 0 });
    ax = norm(ax);
    return { x: ax.x, y: ax.y, z: ax.z, w: 0 };
  }
  return quatNorm({ x: c.x, y: c.y, z: c.z, w: 1 + d });
}
export function yawQuat(yaw) { const h = yaw * 0.5; return { x: 0, y: Math.sin(h), z: 0, w: Math.cos(h) }; }
export function yawOf(forward) { return Math.atan2(forward.x, forward.z); }

// Stage-local rung centers: cross-bars (both rails, not the end caps).
export function rungsLocal(positions) {
  const pos = positions;
  const ys = [];
  for (let i = 0; i < pos.length; i += 3) ys.push(pos[i + 1]);
  const yMin = Math.min(...ys), yMax = Math.max(...ys);
  const used = new Uint8Array(pos.length / 3);
  const out = [];
  const seeds = [];
  for (let i = 0; i < ys.length; i++) seeds.push(Math.round(ys[i] * 50) / 50);
  const uniq = [...new Set(seeds)].sort((a, b) => a - b);
  for (const s of uniq) {
    const ids = [];
    for (let i = 0; i < ys.length; i++) if (!used[i] && Math.abs(ys[i] - s) < 0.03) ids.push(i);
    if (ids.length < 6) continue;
    let x0 = 1e9, x1 = -1e9, y = 0, z = 0;
    for (const i of ids) { const x = pos[i * 3]; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y += pos[i * 3 + 1]; z += pos[i * 3 + 2]; }
    y /= ids.length; z /= ids.length;
    if (x0 > -0.05 || x1 < 0.05) continue;
    if (y > yMax - 0.2 || y < yMin + 0.2) continue;
    for (const i of ids) used[i] = 1;
    out.push({ x: 0, y, z: 0 });
  }
  out.sort((a, b) => a.y - b.y);
  return out;
}

export function smooth(u) { u = clamp(u, 0, 1); return u * u * (3 - 2 * u); }

function solve2(S, T, L1, L2, pole) {
  let dir = sub(T, S);
  let dist = len(dir);
  const max = L1 + L2 - 1e-4, min = Math.abs(L1 - L2) + 1e-4;
  if (dist < 1e-6) dir = { x: 0, y: 1, z: 0 };
  else dir = mul(dir, 1 / dist);
  dist = clamp(dist, min, max);
  const adj = (L1 * L1 + dist * dist - L2 * L2) / (2 * dist);
  const h = Math.sqrt(Math.max(0, L1 * L1 - adj * adj));
  let side = sub(pole, S);
  side = sub(side, mul(dir, dot(side, dir)));
  if (len(side) < 1e-5) side = cross(dir, { x: 0, y: 0, z: 1 });
  side = norm(side);
  const elbow = add(S, add(mul(dir, adj), mul(side, h)));
  const wrist = add(S, mul(dir, dist));
  return { elbow, wrist, reach: dist, wanted: len(sub(T, S)) };
}

function armWorld(hip, yawQ, side) {
  const off = side === 'L' ? SHOULDER_L : SHOULDER_R;
  return add(hip, quatRotate(yawQ, off));
}
function hipJoint(hip, yawQ, side) {
  const off = side === 'L' ? HIP_L : HIP_R;
  return add(hip, quatRotate(yawQ, off));
}

// Place the palm (or sole) on the target. Returns joint positions and the contact point.
export function plantArm(hip, yawQ, side, target, outward) {
  const S = armWorld(hip, yawQ, side);
  let u = norm(sub(target, S));
  let wristT = sub(target, mul(u, PALM));
  let solved = null;
  for (let i = 0; i < 4; i++) {
    const pole = add(S, add(mul(outward, 0.45), { x: 0, y: -0.15, z: 0 }));
    solved = solve2(S, wristT, UPPER, FORE, pole);
    const fore = norm(sub(solved.wrist, solved.elbow));
    u = fore;
    wristT = sub(target, mul(fore, PALM));
  }
  const fore = norm(sub(solved.wrist, solved.elbow));
  const palm = add(solved.wrist, mul(fore, PALM));
  return { S, elbow: solved.elbow, wrist: solved.wrist, contact: palm, err: len(sub(palm, target)) };
}
export function plantLeg(hip, yawQ, side, target, outward) {
  const H = hipJoint(hip, yawQ, side);
  const ankleT = add(target, { x: 0, y: SOLE, z: 0 });
  const bend = target.y > 27.4 ? 0.25 : -0.35;
  const pole = add(H, add(mul(outward, bend), { x: 0, y: 0.05, z: 0 }));
  const solved = solve2(H, ankleT, THIGH, SHIN, pole);
  const contact = add(solved.wrist, { x: 0, y: -SOLE, z: 0 });
  return { H, knee: solved.elbow, ankle: solved.wrist, contact, err: len(sub(contact, target)) };
}

const REST = {
  UpperArm_L: { x: 0.146052, y: -0.0929851, z: 0.0383383, w: 0.984151 },
  Forearm_L: { x: -0.19279, y: -0.0480038, z: -0.0379819, w: 0.979329 },
  Thigh_L: { x: -0.0919095, y: 0.0590934, z: 0.0102073, w: 0.99396 },
  Shin_L: { x: 0.164049, y: 0, z: 0, w: 0.986452 },
  UpperArm_R: { x: 0.146052, y: 0.0929851, z: -0.0383383, w: 0.984151 },
  Forearm_R: { x: -0.19279, y: 0.0480038, z: 0.0379819, w: 0.979329 },
  Thigh_R: { x: -0.0919095, y: -0.0590934, z: -0.0102073, w: 0.99396 },
  Shin_R: { x: 0.164049, y: 0, z: 0, w: 0.986452 },
};
function boneQuat(parentQ, restDir, worldDir, qRest) {
  const localDir = norm(quatRotate(quatInv(parentQ), worldDir));
  const bindLocal = quatRotate(qRest, restDir);
  return quatMul(quatFromTo(bindLocal, localDir), qRest);
}

// hip position search so every planted contact can be reached.
export function posePlants(plants, outward, faceYaw, hipMin = 0.05, prefer = 'high') {
  const yawQ = yawQuat(faceYaw);
  let best = null;
  let base = plants[0] ? plants[0].at : { x: 0, y: 0, z: 0 };
  for (const p of plants) if (p.at.y < base.y) base = p.at;
  for (let oy = hipMin; oy <= 1.45; oy += 0.02) {
    for (const oz of [0.16, 0.20, 0.24, 0.28]) {
      const y = base.y + oy;
      const hip = add(base, add(mul(outward, oz), { x: 0, y: y - base.y, z: 0 }));
      // keep the hip over the rung line in the across-ladder direction
      hip.x = base.x + outward.x * oz;
      hip.z = base.z + outward.z * oz;
      let err = 0;
      const hits = [];
      for (const p of plants) {
        const hit = p.limb[1] === 'H' ? plantArm(hip, yawQ, p.limb[0], p.at, outward) : plantLeg(hip, yawQ, p.limb[0], p.at, outward);
        err = Math.max(err, hit.err);
        hits.push(hit);
      }
      const ok = err <= 0.01;
      const better = !best || (ok && !best.ok) || (ok && best.ok && (prefer === 'high' ? oy > best.oy : oy < best.oy)) || (!ok && !best.ok && err < best.err);
      if (better) best = { err, hip, oz, hits, ok, oy };
    }
  }
  return best;
}

export function quatsFromPose(hip, yawQ, outward, plants) {
  const yaw = yawQ;
  const bones = {};
  const contacts = [];
  const joints = { hip, yawQ };
  for (const p of plants) {
    if (p.limb[1] === 'H') {
      const hit = plantArm(hip, yaw, p.limb[0], p.at, outward);
      const side = p.limb[0];
      const uArm = side === 'L' ? U_FORE : U_FORE_R;
      const uHand = side === 'L' ? U_HAND : U_HAND_R;
      const upName = side === 'L' ? 'UpperArm_L' : 'UpperArm_R';
      const frName = side === 'L' ? 'Forearm_L' : 'Forearm_R';
      const qU = boneQuat(yaw, uArm, norm(sub(hit.elbow, hit.S)), REST[upName]);
      const armWorldQ = quatMul(yaw, qU);
      const qF = boneQuat(armWorldQ, uHand, norm(sub(hit.wrist, hit.elbow)), REST[frName]);
      bones[upName] = qU;
      bones[frName] = qF;
      contacts.push({ limb: p.limb, at: hit.contact, target: p.at, err: hit.err });
      joints[p.limb] = hit;
    } else {
      const hit = plantLeg(hip, yaw, p.limb[0], p.at, outward);
      const thigh = p.limb[0] === 'L' ? 'Thigh_L' : 'Thigh_R';
      const shin = p.limb[0] === 'L' ? 'Shin_L' : 'Shin_R';
      const qT = boneQuat(yaw, U_SHIN, norm(sub(hit.knee, hit.H)), REST[thigh]);
      const thighWorld = quatMul(yaw, qT);
      const qS = boneQuat(thighWorld, U_FOOT, norm(sub(hit.ankle, hit.knee)), REST[shin]);
      bones[thigh] = qT;
      bones[shin] = qS;
      contacts.push({ limb: p.limb, at: hit.contact, target: p.at, err: hit.err });
      joints[p.limb] = hit;
    }
  }
  return { bones, contacts, joints, root: sub(hip, { x: 0, y: HIP_Y, z: 0 }), yawQ: yaw };
}

// --- show timeline -------------------------------------------------------
// One climber, rung list in ship space (already transformed), foot xz on the pad, deck point, door point.

export function rungSpacing(rungs) {
  if (rungs.length < 2) return 1.12;
  let s = 0;
  for (let i = 1; i < rungs.length; i++) s += rungs[i].y - rungs[i - 1].y;
  return s / (rungs.length - 1);
}

// Duration of one person's rung climb (not including the walk or the door).
export function stepDur(rungs, k) {
  if (!rungs[k + 1]) return STEP_SEC;
  const dy = Math.max(1e-4, rungs[k + 1].y - rungs[k].y);
  return Math.max(0.40, Math.min(0.70, dy / (RUNG_PITCH / STEP_SEC)));
}
export function climbDur(rungs) {
  let t = 0;
  const n = climbSteps(rungs);
  for (let k = 0; k < n; k++) t += stepDur(rungs, k);
  return t + 0.6;
}
/** Seconds for a climber to rise ~CLIMB_GAP_M on the ladder (spacing so two never overlap). */
export function climbGapSec(rungs) {
  let t = 0, rise = 0;
  const n = climbSteps(rungs);
  for (let k = 0; k < n && rise < CLIMB_GAP_M; k++) {
    t += stepDur(rungs, k);
    rise += Math.max(0, (rungs[k + 1] ? rungs[k + 1].y : 0) - (rungs[k] ? rungs[k].y : 0));
  }
  return Math.max(1.0, t || GAP);
}

export const DECK_PATH = [
  { x: -0.95, z: 4.62, y: 28.54, hip: 0.78 },
  { x: -0.70, z: 4.55, y: 28.54, hip: 0.78 },
  { x: 0.00, z: 4.45, y: 28.54, hip: 0.78 },
  { x: 0.00, z: 4.30, y: 28.54, hip: 0.78 },
  { x: 0.00, z: 4.18, y: 29.00, hip: 0.55 },
  { x: 0.00, z: 4.02, y: 29.02, hip: 0.50 },
  { x: 0.00, z: 3.88, y: 29.02, hip: 0.50 },
  { x: 0.00, z: 3.70, y: 29.00, hip: 0.55 },
  { x: -0.10, z: 3.55, y: 28.95, hip: 0.58 },
];
export function deckLength() {
  let L = 0;
  for (let i = 1; i < DECK_PATH.length; i++) L += Math.hypot(DECK_PATH[i].x - DECK_PATH[i - 1].x, DECK_PATH[i].z - DECK_PATH[i - 1].z);
  return L;
}
export function deckDur() { return deckLength() / CLIMB_V; }
export function deckPoint(u) {
  const P = DECK_PATH;
  let left = deckLength() * clamp(u, 0, 1);
  for (let i = 1; i < P.length; i++) {
    const d = Math.hypot(P[i].x - P[i - 1].x, P[i].z - P[i - 1].z);
    if (left <= d || i === P.length - 1) {
      const t = d > 1e-6 ? clamp(left / d, 0, 1) : 1;
      const a = P[i - 1], b = P[i];
      return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, z: a.z + (b.z - a.z) * t, hip: a.hip + (b.hip - a.hip) * t };
    }
    left -= d;
  }
  return P[P.length - 1];
}
export function poseShow(rungs, outward, tau) {
  const c = climbDur(rungs);
  if (tau <= c) return poseFrame(rungs, Math.max(0, tau), outward);
  const u = clamp((tau - c) / deckDur(), 0, 1);
  const at = deckPoint(u);
  return poseStand(at, faceYaw(outward), outward, at.hip);
}

const STAGE_Y = [28.52, 23.841667, 19.163334, 14.485, 9.806666, 5.128334];
export function nominalRungs() {
  const x = -1.419532, z = 4.950498, out = [];
  const lys = stageRungLocals();
  for (const oy of STAGE_Y) for (const ly of lys) out.push({ x, y: oy + ly, z });
  out.sort((a, b) => a.y - b.y);
  return out;
}

export function showTimes(n, rungs, walkDist) {
  const deploy = DEPLOY_T;
  const entryOpen = deploy + ENTRY_DOOR_SEC;  // EntryDoor_Open finishes
  const walk = walkDist / WALK_V;
  const climb = climbDur(rungs);
  const deck = deckDur();
  const per = climb + deck;
  const gap = climbGapSec(rungs);
  // Ladder ready → first climber starts ASAP (pad crew already at foot do not wait on others).
  // Later climbers start when the previous is ~1.5 m up (gap), or when they themselves arrive.
  const ready = Math.max(entryOpen, deploy);
  const finish = [];
  let prevStart = null;
  for (let i = 0; i < n; i++) {
    const arrive = walk; // walk-from-stand; pad crew stand near foot so lerp is short
    let t = Math.max(ready, arrive);
    if (prevStart != null) t = Math.max(t, prevStart + gap);
    finish.push({ start: t, inside: t + per });
    prevStart = t;
  }
  const start0 = finish.length ? finish[0].start : ready;
  const last = finish.length ? finish[finish.length - 1].inside : start0;
  const close = last;                            // EntryDoor_Close starts (all inside)
  const entryClosed = close + ENTRY_DOOR_SEC;    // then Ladder_Stow
  const stow = entryClosed + LADDER_STOW_SEC;    // then BayDoor_Close
  const launch = stow + BAY_DOOR_SEC;
  return { deploy, entryOpen, walk, climb, deck, per, start0, finish, close, entryClosed, stow, launch, gap };
}

// Plants for climber-local time tau in [0, climbDur].
// Diagonal shuffle: (foot on k, opposite hand on k+1) then both hands, then the foot replaces the lower hand.
function parkLimbs(rungs, planted, outward) {
  const names = ['LH', 'RH', 'LF', 'RF'];
  const have = new Set(planted.map((p) => p.limb));
  const lo = planted.reduce((a, p) => (p.at.y < a.y ? p.at : a), planted[0].at);
  const extra = [];
  for (const limb of names) {
    if (have.has(limb)) continue;
    const hand = limb[1] === 'H';
    const at = add(lo, add(mul(outward, hand ? 0.46 : 0.40), { x: 0, y: hand ? 1.05 : 0.25, z: 0 }));
    extra.push({ limb, at, park: true });
  }
  return planted.map((p) => ({ ...p, park: false })).concat(extra);
}

// Only diagonals (foot + opposite hand on adjacent rungs). Two hands cannot span the
// 1.32 m stage-joint gap. A step is: hold the diagonal, release to one hand, arrive on the next diagonal.
export function plantsAt(rungs, tau) {
  const nAdv = climbSteps(rungs);
  let t = tau;
  let k = 0;
  for (; k < nAdv - 1; k++) {
    const d = stepDur(rungs, k);
    if (t < d) break;
    t -= d;
  }
  if (k > nAdv - 1) k = nAdv - 1;
  const dur = stepDur(rungs, k);
  const f = clamp(t / dur, 0, 0.999);
  const last = rungs.length - 1;
  const lo = rungs[k], hi = rungs[Math.min(last, k + 1)];
  const handLo = rungs[Math.min(last, k + HAND_SPAN)];
  const handHi = rungs[Math.min(last, k + HAND_SPAN + 1)];
  const footA = k % 2 === 0 ? 'RF' : 'LF';
  const handA = k % 2 === 0 ? 'LH' : 'RH';
  const footB = footA === 'RF' ? 'LF' : 'RF';
  const handB = handA === 'LH' ? 'RH' : 'LH';
  if (f < 0.82) return [{ limb: footA, at: lo }, { limb: handA, at: handLo }];
  return [{ limb: footB, at: hi }, { limb: handB, at: handHi }];
}

export function framePlants(rungs, tau, outward) {
  return parkLimbs(rungs, plantsAt(rungs, tau), outward);
}

export function movingLimbsAt(rungs, tau) {
  const nAdv = climbSteps(rungs);
  let t = tau;
  let k = 0;
  for (; k < nAdv - 1; k++) {
    const d = stepDur(rungs, k);
    if (t < d) break;
    t -= d;
  }
  if (k > nAdv - 1) k = nAdv - 1;
  const dur = stepDur(rungs, k);
  const f = clamp(t / dur, 0, 0.999);
  const last = rungs.length - 1;
  const lo = rungs[k], hi = rungs[Math.min(last, k + 1)];
  const handLo = rungs[Math.min(last, k + HAND_SPAN)];
  const handHi = rungs[Math.min(last, k + HAND_SPAN + 1)];
  const footA = k % 2 === 0 ? 'RF' : 'LF';
  const handA = k % 2 === 0 ? 'LH' : 'RH';
  const footB = footA === 'RF' ? 'LF' : 'RF';
  const handB = handA === 'LH' ? 'RH' : 'LH';
  const u = smooth(clamp((f - 0.12) / 0.70, 0, 1));
  return [
    { limb: footB, at: lerp3(lo, hi, u) },
    { limb: handB, at: lerp3(handLo, handHi, u) },
  ];
}
export function poseFrame(rungs, tau, outward) {
  const yaw = faceYaw(outward);
  const yawQ = yawQuat(yaw);
  const planted = plantsAt(rungs, tau).map((p) => ({ ...p, at: gripAt(p.at, p.limb, outward), park: false }));
  const found = posePlants(planted, outward, yaw);
  const extra = movingLimbsAt(rungs, tau).map((p) => ({ ...p, at: gripAt(p.at, p.limb, outward), park: true }));
  const posed = quatsFromPose(found.hip, yawQ, outward, planted.concat(extra));
  const contacts = posed.contacts.filter((c) => !extra.find((p) => p.limb === c.limb));
  return { ...posed, hip: found.hip, err: Math.max(...contacts.map((c) => c.err), 0), contacts, outward, yaw };
}

export function bodySpheres(frame) {
  const j = frame.joints;
  const hip = frame.hip;
  const up = { x: 0, y: 1, z: 0 };
  const chest = add(hip, { x: 0, y: 0.40, z: 0 });
  const head = add(hip, { x: 0, y: 0.72, z: 0 });
  const s = [
    { name: 'hip', p: hip, r: 0.15 },
    { name: 'chest', p: chest, r: 0.17 },
    { name: 'head', p: head, r: 0.13 },
  ];
  for (const limb of ['LH', 'RH', 'LF', 'RF']) {
    const h = j[limb];
    if (!h) continue;
    if (h.S) {
      s.push({ name: limb + 'sh', p: h.S, r: 0.07 });
      s.push({ name: limb + 'el', p: h.elbow, r: 0.055 });
      s.push({ name: limb + 'wr', p: h.wrist, r: 0.045 });
      s.push({ name: limb + 'palm', p: h.contact, r: 0.04 });
    } else {
      s.push({ name: limb + 'hip', p: h.H, r: 0.08 });
      s.push({ name: limb + 'kn', p: h.knee, r: 0.06 });
      s.push({ name: limb + 'an', p: h.ankle, r: 0.05 });
      s.push({ name: limb + 'sole', p: h.contact, r: 0.04 });
    }
  }
  return s;
}

export function poseStand(at, yaw, outward, hipMin = 0.78) {
  const yawQ = yawQuat(yaw);
  const fwd = quatRotate(yawQ, { x: 0, y: 0, z: 1 });
  const plants = [
    { limb: 'LF', at: add(at, mul(fwd, 0.04)) },
    { limb: 'RF', at: add(at, mul(fwd, -0.04)) },
    { limb: 'LH', at: add(at, add(mul(quatRotate(yawQ, { x: 0.18, y: 0, z: 0 }), 1), { x: 0, y: 1.00, z: 0 })) },
    { limb: 'RH', at: add(at, add(mul(quatRotate(yawQ, { x: -0.18, y: 0, z: 0 }), 1), { x: 0, y: 1.00, z: 0 })) },
  ];
  const found = posePlants(plants.filter((p) => p.limb[1] === 'F'), outward, yaw, hipMin, 'low');
  const posed = quatsFromPose(found.hip, yawQ, outward, plants);
  return { ...posed, hip: found.hip, err: 0, contacts: [], outward, yaw };
}

export function outwardOf(anchor) {
  const h = Math.hypot(anchor.x, anchor.z) || 1;
  return { x: anchor.x / h, y: 0, z: anchor.z / h };
}

export function faceYaw(outward) {
  const face = mul(outward, -1);
  return yawOf(face);
}
