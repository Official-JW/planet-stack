// launch_pad_next.glb lane fix A option (a), direct GLB edit of a257d930 (Director pick 10/25 01:28):
//  PC-1 base (0.6,7) -> (0.6,8.8) pad-local (21.81 m from the ship axis); jib stretched +2.0 m (Slew-bound verts beyond 5 m), trolley_max 14.2 -> 16.2;
//  Truck_Stop (2.85,0,23) yaw 0; Pick_Point/_02 on the bed (1.70 / -0.80, 1.9, 23); r 4.5 U-turn about (7,27.5) pad = world (647,27.5); spur ribbon + Spur_Taper_* removed;
//  all crane_solve extras + poses recomputed; crane clips re-keyed (Slew/Trolley/Hook yaw remapped between the new endpoint solves, heights untouched). meshopt QUANTIZE.
// z13 variant (Director 10/25 01:57: lanes stay, lane move parked): ONLY the crane changes (base z 8.8, jib +2.0, trolley 16.2, solves/poses/clips re-keyed);
// Pick_Point/_02, Truck_Stop, spur ribbon + Spur_Taper_*, U-turn and every other marker are left byte-for-byte as a257d930.
// usage: node build_lane_fix_z13.mjs IN.glb OUT.glb REPORT.json
import fs from 'fs';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS, EXTMeshoptCompression } from '@gltf-transform/extensions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';
await MeshoptDecoder.ready; await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });
const [IN, OUT, REP] = process.argv.slice(2);
const CX = 0.6, CZ = 8.8, TMAX = 16.2, TS = [2.85, 23], PP1 = [1.70, 1.9, 23], PP2 = [-0.80, 1.9, 23], UC = [7, 27.5], UR = 4.5, PWX = 640;
const doc = await io.read(IN); const R = doc.getRoot(); const N = n => R.listNodes().find(x => x.getName() === n); const rep = { in: IN };
const r4 = x => +(+x).toFixed(4), r3 = x => +(+x).toFixed(3);
const crane = N('Crane'), cx0 = crane.getTranslation(), ex = { ...crane.getExtras() }; const T0 = ex.trolley_max_m, SH = ex.sheave_y, HD = ex.hook_drop_m, BOXH = ex.box_hook_offset_y;
const C0 = [cx0[0], cx0[2]];
// ---- 1. jib stretch (both crane prims, Slew-bound verts with jib-local x > 5 m)
{ const mn = N('Crane_Mesh').listChildren()[0]; const T = mn.getTranslation(), S = mn.getScale()[0]; const DX = TMAX - T0, X0 = 5, L0 = 15.287, k = (L0 + DX - X0) / (L0 - X0); let n = 0, tip = 0;
  for (const p of mn.getMesh().listPrimitives()) { const P = p.getAttribute('POSITION'), J = p.getAttribute('JOINTS_0'), A = P.getArray(), q = [];
    for (let i = 0; i < P.getCount(); i++) { J.getElement(i, q); if (q[0] !== 1) continue; const sx = C0[0] + T[0] + S * A[3 * i]; const lx = sx - 2 * C0[0]; if (lx <= X0) continue;
      const nx = X0 + (lx - X0) * k; A[3 * i] += Math.round((nx - lx) / S); n++; tip = Math.max(tip, T[0] + S * A[3 * i] - C0[0]); }
    P.setArray(A); }
  rep.jib = { stretched_verts: n, k: r4(k), dx_m: DX, tip_local_x_m: r3(tip) }; }
// ---- 2. crane base + solves
crane.setTranslation([CX, 0, CZ]);
const solve = (p, yawDeg = 0) => { const dx = p[0] - CX, dz = p[2] - CZ; const th = Math.atan2(-dz, dx); return { slew_rad: r4(th), trolley_m: r3(Math.hypot(dx, dz)), hoist_m: r3(SH - (p[1] + BOXH) - HD), hook_yaw_rad: r4(yawDeg * Math.PI / 180 - th) }; };
const solveOld = (p, yawDeg = 0) => { const dx = p[0] - C0[0], dz = p[2] - C0[1]; const th = Math.atan2(-dz, dx); return [th, Math.hypot(dx, dz)]; };
const oldPos = {}; for (const n of R.listNodes()) if (n.getExtras().kind === 'crane_target') oldPos[n.getName()] = n.getTranslation().slice();
rep.solves = {};
for (const n of R.listNodes()) { const e = n.getExtras(); if (e.kind !== 'crane_target') continue; const s = solve(n.getTranslation(), e.box_yaw_deg || 0); n.setExtras({ ...e, crane_solve: s }); rep.solves[n.getName()] = s;
  if (s.trolley_m > TMAX || s.trolley_m < ex.trolley_min_m) throw new Error('out of reach ' + n.getName() + ' ' + s.trolley_m); }
{ const e = { ...N('Pick_Point').getExtras(), baked_clips: 'crane_lift + crane_swing land here (re-keyed 10/25)' }; N('Pick_Point').setExtras(e); }
// ---- 3. clips: remap Slew / Trolley / Hook yaw keys between new endpoint solves (targets matched on the old solves)
const TG = { Pick_Point: null, Drop_Point: null, Pick_Point_Bay: null, Hold_Door: null };
const oldS = {}, newS = {}; for (const k of Object.keys(TG)) { oldS[k] = solveOld(oldPos[k]); const s = rep.solves[k]; newS[k] = [s.slew_rad, s.trolley_m]; }
const angOf = q => 2 * Math.atan2(q[1], q[3]); const qOf = a => [0, Math.sin(a / 2), 0, Math.cos(a / 2)];
const wrap = a => { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; };
const match = (th, r) => { let best = null, bd = 1e9; for (const k in oldS) { const d = Math.abs(wrap(th - oldS[k][0])) * 10 + Math.abs(r - oldS[k][1]); if (d < bd) { bd = d; best = k; } } if (bd > 0.3) throw new Error('no target match ' + th + ' ' + r); return best; };
const ch = (an, node, path) => an.listChannels().find(c => c.getTargetNode().getName() === node && c.getTargetPath() === path)?.getSampler();
const rd = acc => { const n = acc.getCount(), o = []; for (let i = 0; i < n; i++) { const e = acc.getElement(i, []); o.push(e); } return o; };
const wr = (acc, vals) => { vals.forEach((v, i) => acc.setElement(i, v)); };
rep.clips = {};
for (const an of R.listAnimations().filter(a => a.getName().startsWith('crane'))) {
  const sS = ch(an, 'Slew', 'rotation'), sT = ch(an, 'Trolley', 'translation'), sH = ch(an, 'Hook', 'rotation');
  const SL = rd(sS.getOutput()), TR = rd(sT.getOutput()), HK = rd(sH.getOutput());
  const a0 = angOf(SL[0]), a1 = angOf(SL[SL.length - 1]), t0 = TR[0][0], t1 = TR[TR.length - 1][0];
  const k0 = match(a0, t0), k1 = match(a1, t1);
  // unwrapped old slew sequence
  const ua = []; let prev = a0; for (const q of SL) { let a = angOf(q); while (a - prev > Math.PI) a -= 2 * Math.PI; while (a - prev < -Math.PI) a += 2 * Math.PI; ua.push(a); prev = a; }
  const dOld = ua[ua.length - 1] - ua[0]; const n0 = newS[k0][0]; let n1 = newS[k1][0]; while (n1 - n0 - dOld > Math.PI) n1 -= 2 * Math.PI; while (n1 - n0 - dOld < -Math.PI) n1 += 2 * Math.PI;
  const newSL = ua.map(a => { const s = Math.abs(dOld) > 1e-6 ? (a - ua[0]) / dOld : 0; return n0 + s * (n1 - n0); });
  const newTR = TR.map(t => { const s = Math.abs(t1 - t0) > 1e-6 ? (t[0] - t0) / (t1 - t0) : 0; return [newS[k0][1] + s * (newS[k1][1] - newS[k0][1]), t[1], t[2]]; });
  // hook yaw keeps the box yaw: hook = old_hook + old_slew - new_slew (slew sampler and hook sampler may differ in key count)
  const slewAt = (arr, i, n) => arr[Math.min(arr.length - 1, Math.round(i * (arr.length - 1) / Math.max(1, n - 1)))];
  const newHK = HK.map((q, i) => qOf(angOf(q) + slewAt(ua, i, HK.length) - slewAt(newSL, i, HK.length)));
  wr(sS.getOutput(), newSL.map(qOf)); wr(sT.getOutput(), newTR); wr(sH.getOutput(), newHK);
  rep.clips[an.getName()] = { from: k0, to: k1, slew_old: [r4(ua[0]), r4(ua[ua.length - 1])], slew_new: [r4(n0), r4(n1)], trolley_new: [r3(newTR[0][0]), r3(newTR[newTR.length - 1][0])],
    trolley_range: [r3(Math.min(...newTR.map(t => t[0]))), r3(Math.max(...newTR.map(t => t[0])))] }; }
// poses
{ const poses = JSON.parse(ex.poses); const map = { pick: 'Pick_Point', drop: 'Drop_Point', bay: 'Pick_Point_Bay', hold: 'Hold_Door' };
  for (const k of Object.keys(poses)) { const s = rep.solves[map[k.split('_')[0]]]; poses[k] = [s.slew_rad, s.trolley_m, poses[k][2], s.hook_yaw_rad]; }
  ex.poses = JSON.stringify(poses); rep.poses = poses; }
const dShip = Math.hypot(CX - 0, CZ - (-13));
Object.assign(ex, { origin: `footing ground centre, pad-local (${CX}, 0, ${CZ}) = world (${r3(CX + PWX)}, 0, ${CZ}); jib +X at Slew 0`, trolley_max_m: TMAX,
  slew_note: `free 360: ${dShip.toFixed(2)} m off ship axis, tip 17.29 m, hull gap 0.49 m (10/25)`,
  clips: ex.clips.split(' | ')[0] + ' | re-keyed 10/25 (base z 8.8)' });
crane.setExtras(ex);
R.listAccessors().forEach(a => { if (a.listParents().length === 1) a.dispose(); });
R.listExtensionsUsed().find(e => e.extensionName === 'EXT_meshopt_compression').setEncoderOptions({ method: EXTMeshoptCompression.EncoderMethod.QUANTIZE });
await io.write(OUT, doc); fs.writeFileSync(REP, JSON.stringify(rep, null, 1)); console.log(JSON.stringify(rep.jib), JSON.stringify(rep.clips));
