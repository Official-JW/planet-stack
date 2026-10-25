// launch_pad_next.glb: direct edit of the db78a6f7-based pad (pad_west) -> lane option B (out z 23 / back z 32) + crane pick spur,
// U-turn re-laid, pipe end + riser/elbow/flange moved to the WEST side, old-frame notes to the 640 frame. Re-encoded meshopt QUANTIZE.
// usage: node next.mjs IN.glb OUT.glb REPORT.json   env: SPUR_Z 19.5 TS_X 3 BAY_X0 -3 BAY_X1 8 TAPER 17.5 LANE_OUT 23 LANE_BACK 32 TURN_STRAIGHT 2 ENTRY_X -48 EXIT_X -48 PAD_WX 640
import fs from 'fs';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS, EXTMeshoptCompression } from '@gltf-transform/extensions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';
await MeshoptDecoder.ready; await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });
const [IN, OUT, REP] = process.argv.slice(2, 5); const E = (k, d) => +(process.env[k] ?? d);
const SZ = E('SPUR_Z', 19.5), TSX = E('TS_X', 3), BX0 = E('BAY_X0', -3), BX1 = E('BAY_X1', 8), TL = E('TAPER', 17.5), ZO = E('LANE_OUT', 23), ZB = E('LANE_BACK', 32);
const TSTR = E('TURN_STRAIGHT', 2), ENX = E('ENTRY_X', -48), EXX = E('EXIT_X', -48), PWX = E('PAD_WX', 640);
const PIPE_FROM = [20.3, -9.6], PIPE_TO = [-27, 2.6], RISER_BOTTOM_Y = E('RISER_BOTTOM_Y', -0.1);
const r3 = v => +(+v).toFixed(3), W = (x, z) => [r3(x + PWX), r3(z)];
const doc = await io.read(IN); const R = doc.getRoot(); const N = n => R.listNodes().find(x => x.getName() === n); const rep = { in: IN, params: { SZ, TSX, BX0, BX1, TL, ZO, ZB, TSTR, ENX, EXX, PWX } };
const deqf = (T, S) => q => q.map((v, k) => T[k] + S * v), qzf = (T, S) => p => p.map((v, k) => Math.round((v - T[k]) / S));
const grow = (acc, add) => { const old = acc.getArray(); const nw = new old.constructor(old.length + add.length); nw.set(old); nw.set(add, old.length); acc.setArray(nw); };
// ---------------------------------------------------------------- 1. pipe end hardware (riser, elbow, flange) -> west
{ const mn = N('Pad_Base').listChildren().find(c => c.getMesh()); const T = mn.getTranslation(), S = mn.getScale()[0], deq = deqf(T, S);
  const prims = mn.getMesh().listPrimitives(); const found = [];
  prims.forEach((p, pi) => { const P = p.getAttribute('POSITION'), I = p.getIndices().getArray(), n = P.getCount(); const par = new Int32Array(n).map((_, i) => i);
    const f = i => { while (par[i] !== i) i = par[i] = par[par[i]]; return i; }; for (let t = 0; t < I.length; t += 3) { const a = f(I[t]), b = f(I[t + 1]), c = f(I[t + 2]); par[b] = a; par[f(c)] = a; }
    const comp = new Map(), q = []; for (let i = 0; i < n; i++) { const r = f(i); (comp.get(r) || comp.set(r, []).get(r)).push(i); }
    for (const [r, vs] of comp) { let ok = true, lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
      for (const i of vs) { P.getElement(i, q); const v = deq(q); for (let k = 0; k < 3; k++) { lo[k] = Math.min(lo[k], v[k]); hi[k] = Math.max(hi[k], v[k]); }
        if (Math.hypot(v[0] - PIPE_FROM[0], v[2] - PIPE_FROM[1]) > 0.42 || v[1] < 0.85 || v[1] > 1.9) { ok = false; break; } }
      if (ok) found.push({ prim: pi, verts: vs, lo, hi }); } });
  const D = [Math.round((PIPE_TO[0] - PIPE_FROM[0]) / S), 0, Math.round((PIPE_TO[1] - PIPE_FROM[1]) / S)];
  rep.pipe_hw = { components: found.map(c => ({ prim: c.prim, material: prims[c.prim].getMaterial().getName(), verts: c.verts.length, bbox_before: [c.lo.map(r3), c.hi.map(r3)] })), shift_quanta: D, shift_m: D.map(d => +(d * S).toFixed(5)) };
  const nv = found.reduce((a, c) => a + c.verts.length, 0); rep.pipe_hw.total_verts = nv; if (found.length < 3 || nv > 400) throw new Error('pipe-end selection looks wrong ' + JSON.stringify(rep.pipe_hw.components));
  const qb = Math.round((RISER_BOTTOM_Y - T[1]) / S); let ext = 0;
  for (const c of found) { const P = prims[c.prim].getAttribute('POSITION'); const A = P.getArray(); const riser = c.lo[1] < 0.91;
    for (const i of c.verts) { A[3 * i] += D[0]; A[3 * i + 2] += D[2]; if (riser && T[1] + S * A[3 * i + 1] < 0.91) { A[3 * i + 1] = qb; ext++; } } P.setArray(A);
    const q = [], lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9]; for (const i of c.verts) { P.getElement(i, q); const v = deq(q); for (let k = 0; k < 3; k++) { lo[k] = Math.min(lo[k], v[k]); hi[k] = Math.max(hi[k], v[k]); } }
    c.after = [lo.map(r3), hi.map(r3)]; c.riser = riser; }
  rep.pipe_hw.components.forEach((c, i) => { c.bbox_after = found[i].after; c.riser = found[i].riser; }); rep.pipe_hw.riser_bottom_verts_dropped_to_y = [ext, RISER_BOTTOM_Y];
  const pe = N('Pipe_LaunchPad_End'); rep.pipe_end_before = { t: pe.getTranslation(), r: pe.getRotation(), extras: pe.getExtras() };
  pe.setTranslation([PIPE_TO[0], 0.95, PIPE_TO[1]]).setRotation([0, 1, 0, 0]).setExtras({ ...pe.getExtras(), from: 'Dock Pipe_LaunchPad (buried, -X)' });
  rep.pipe_end_after = { t: pe.getTranslation(), r: pe.getRotation(), facing_world: [-1, 0, 0], world: [r3(PIPE_TO[0] + PWX), 0.95, r3(PIPE_TO[1])], extras: pe.getExtras() }; }
// ---------------------------------------------------------------- 2. road: U-turn re-laid + spur ribbon (same prim, +0 draws)
const TURN_X = BX1 + TL + TSTR, CZ = (ZO + ZB) / 2, RT = (ZB - ZO) / 2;
const path = [[ENX, ZO], [BX0 - TL, ZO], [BX0, SZ], [TSX, SZ], [BX1, SZ], [BX1 + TL, ZO], [TURN_X, ZO]];
{ const un = N('Road_UTurn'), mn = un.listChildren()[0]; const T = mn.getTranslation(), S = mn.getScale()[0], deq = deqf(T, S), qz = qzf(T, S);
  const p = mn.getMesh().listPrimitives()[0]; const P = p.getAttribute('POSITION'), NO = p.getAttribute('NORMAL'), CO = p.getAttribute('COLOR_0'), IX = p.getIndices();
  const ex0 = N('Turn_Start').getExtras().turn; const r0 = ex0.radius_m; if (Math.abs(r0 - RT) > 1e-9) throw new Error('U-turn radius would change ' + r0 + ' -> ' + RT + ' (needs a rebuild)');
  const D = [Math.round((TURN_X - ex0.center_gltf[0]) / S), 0, Math.round((CZ - ex0.center_gltf[2]) / S)]; const A = P.getArray(); const n0 = P.getCount();
  for (let i = 0; i < n0; i++) { A[3 * i] += D[0]; A[3 * i + 2] += D[2]; } P.setArray(A);
  rep.uturn = { shift_quanta: D, shift_m: D.map(d => +(d * S).toFixed(5)), centre_gltf: [TURN_X, 0, CZ], radius_m: RT, verts: n0 };
  // spur ribbon: same cross-section as the U-turn road (5.6 m, berm on the pad / -Z side only; lane side flat so it opens onto the z 23 lane)
  const C = (r, g, b) => [r, g, b, 1].map(x => Math.round(x * 255));
  const PROF = [[-2.8, -0.042, C(.224, .235, .255)], [-2.35, 0.295, C(.29, .298, .318)], [-2.0, 0.046, C(.337, .353, .376)], [-1.8, 0.046, C(.373, .388, .412)], [-1.63, 0.024, C(.212, .224, .243)],
    [-1.24, 0.024, C(.212, .224, .243)], [-1.09, 0.046, C(.392, .408, .435)], [0.07, 0.063, C(.392, .408, .435)], [1.11, 0.046, C(.392, .408, .435)], [1.25, 0.024, C(.212, .224, .243)],
    [1.67, 0.024, C(.212, .224, .243)], [1.8, 0.046, C(.373, .388, .412)], [2.8, 0.046, C(.373, .388, .412)]];
  const sp = path.slice(1, 6);   // ribbon from taper-in start to taper-out end
  const dir = (a, b) => { const dx = b[0] - a[0], dz = b[1] - a[1], l = Math.hypot(dx, dz); return [dx / l, dz / l]; };
  // offset direction o>0 = +Z side for a +X heading: perp = (-dz, dx)... heading (dx,dz): +Z-side normal = (-dz, dx) rotated so that for (1,0) -> (0,1)
  const perp = d => [-d[1], d[0]];
  const offs = sp.map((pt, i) => { const dp = i > 0 ? perp(dir(sp[i - 1], pt)) : null, dn = i < sp.length - 1 ? perp(dir(pt, sp[i + 1])) : null;
    if (!dp) return dn; if (!dn) return dp; const m = [dp[0] + dn[0], dp[1] + dn[1]], l = Math.hypot(...m), cs = (m[0] * dp[0] + m[1] * dp[1]) / l; return [m[0] / l / cs, m[1] / l / cs]; });
  const Pn = [], Nn = [], Cn = [], In = []; let nv = n0;
  for (let s = 0; s < sp.length - 1; s++) for (let b = 0; b < PROF.length - 1; b++) {
    const [o0, y0, c0] = PROF[b], [o1, y1, c1] = PROF[b + 1]; const pd = perp(dir(sp[s], sp[s + 1])); const sl = (y1 - y0) / (o1 - o0);
    let nn = [-sl * pd[0], 1, -sl * pd[1]]; const L = Math.hypot(...nn); nn = nn.map(x => Math.round(x / L * 127));
    const V = (k, o, y) => [sp[k][0] + offs[k][0] * o, y, sp[k][1] + offs[k][1] * o];
    const quad = [[V(s, o0, y0), c0], [V(s + 1, o0, y0), c0], [V(s + 1, o1, y1), c1], [V(s, o1, y1), c1]];
    for (const [v, c] of quad) { Pn.push(...qz(v)); Nn.push(...nn); Cn.push(...c); }
    const a = deq(Pn.slice(-12, -9)), bq = deq(Pn.slice(-9, -6)), cq = deq(Pn.slice(-6, -3)); const e1 = bq.map((x, k) => x - a[k]), e2 = cq.map((x, k) => x - a[k]);
    const up = e1[2] * e2[0] - e1[0] * e2[2] > 0; In.push(...(up ? [nv, nv + 1, nv + 2, nv, nv + 2, nv + 3] : [nv, nv + 2, nv + 1, nv, nv + 3, nv + 2])); nv += 4; }
  grow(P, Pn); grow(NO, Nn); grow(CO, Cn); grow(IX, In);
  const lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9]; for (let i = 0; i < Pn.length; i += 3) { const v = deq(Pn.slice(i, i + 3)); for (let k = 0; k < 3; k++) { lo[k] = Math.min(lo[k], v[k]); hi[k] = Math.max(hi[k], v[k]); } }
  rep.spur_ribbon = { verts: Pn.length / 3, tris: In.length / 3, bbox_pad: [lo.map(r3), hi.map(r3)], centreline_pad: sp, south_edge_min_z: r3(lo[2]) };
  un.setExtras({ road: `U-turn at the east end of the flatbed road (not pad surface): joins the z ${ZO} / z ${ZB} road tiles at world x ${r3(TURN_X + PWX)}, centre world (${r3(TURN_X + PWX)}, ${CZ}), r ${RT}`,
    spur: `crane pick spur (same mesh): off the eastbound z ${ZO} lane, 1:${r3(TL / (ZO - SZ))} straight tapers world x ${r3(BX0 - TL + PWX)} -> ${r3(BX0 + PWX)} (in) and ${r3(BX1 + PWX)} -> ${r3(BX1 + TL + PWX)} (out), bay z ${SZ} from world x ${r3(BX0 + PWX)} to ${r3(BX1 + PWX)}; berm on the pad side only` }); }
// ---------------------------------------------------------------- 3. markers + notes
const yawq = d => { const a = d * Math.PI / 360; return [0, Math.sin(a), 0, Math.cos(a)]; };
const legYaw = (a, b) => r3(Math.atan2(-(b[1] - a[1]), b[0] - a[0]) * 180 / Math.PI);
const before = {}; const MK = ['Truck_Stop', 'Pick_Point', 'Pick_Point_02', 'Road_Entry', 'Turn_Start', 'Turn_End', 'Road_Exit', 'Crane'];
for (const k of MK) before[k] = { t: N(k).getTranslation(), extras: N(k).getExtras() };
const scene = R.getDefaultScene() || R.listScenes()[0]; const mk = (name, xz, yaw, ex) => { const n = doc.createNode(name).setTranslation([xz[0], 0, xz[1]]); if (yaw) n.setRotation(yawq(yaw)); n.setExtras(ex); scene.addChild(n); return n; };
const ts0 = N('Truck_Stop').getTranslation(), dTS = [TSX - ts0[0], SZ - ts0[2]];
N('Road_Entry').setTranslation([ENX, 0, ZO]).setExtras({ ...N('Road_Entry').getExtras(), next: 'Spur_Taper_In_A', world_xz: W(ENX, ZO) });
const L = { In_A: path[1], In_B: path[2], Out_A: path[4], Out_B: path[5] };
mk('Spur_Taper_In_A', L.In_A, 0, { kind: 'road_leg', yaw_deg: 0, next: 'Spur_Taper_In_B', world_xz: W(...L.In_A), note: `pick spur: straight taper south off the z ${ZO} lane` });
mk('Spur_Taper_In_B', L.In_B, 0, { kind: 'road_leg', yaw_deg: 0, next: 'Truck_Stop', world_xz: W(...L.In_B), taper_in_yaw_deg: legYaw(L.In_A, L.In_B), note: `end of the in-taper; bay z ${SZ} straight from here` });
const ts = N('Truck_Stop'); ts.setTranslation([TSX, 0, SZ]).setExtras({ ...ts.getExtras(), lane: `crane pick spur bay world z ${SZ} (off the eastbound z ${ZO} lane)`, next: 'Spur_Taper_Out_A', world_xz: W(TSX, SZ) });
mk('Spur_Taper_Out_A', L.Out_A, 0, { kind: 'road_leg', yaw_deg: 0, next: 'Spur_Taper_Out_B', world_xz: W(...L.Out_A), taper_out_yaw_deg: legYaw(L.Out_A, L.Out_B), note: `straight taper back north to the z ${ZO} lane` });
mk('Spur_Taper_Out_B', L.Out_B, 0, { kind: 'road_leg', yaw_deg: 0, next: 'Turn_Start', world_xz: W(...L.Out_B), note: `back on the z ${ZO} lane` });
const tsn = N('Turn_Start'); const tex = tsn.getExtras(); tsn.setTranslation([TURN_X, 0, ZO]).setExtras({ ...tex, world_xz: W(TURN_X, ZO), turn: { ...tex.turn, center_gltf: [TURN_X, 0, CZ], radius_m: RT } });
N('Turn_End').setTranslation([TURN_X, 0, ZB]).setExtras({ ...N('Turn_End').getExtras(), world_xz: W(TURN_X, ZB) });
N('Road_Exit').setTranslation([EXX, 0, ZB]).setExtras({ ...N('Road_Exit').getExtras(), world_xz: W(EXX, ZB) });
const cr = N('Crane'), cT = cr.getTranslation(), cx = cr.getExtras(); rep.reach = {};
for (const k of ['Pick_Point', 'Pick_Point_02']) { const n = N(k), p = n.getTranslation(); const np = [p[0] + dTS[0], p[1], p[2] + dTS[1]]; n.setTranslation(np);
  const lx = np[0] - cT[0], lz = np[2] - cT[2], r = Math.hypot(lx, lz), th = Math.atan2(-lz, lx); const ex = n.getExtras();
  n.setExtras({ ...ex, crane_solve: { ...ex.crane_solve, slew_rad: +th.toFixed(4), trolley_m: +r.toFixed(3), hook_yaw_rad: +(-th).toFixed(4) },
    baked_clips: 'crane untouched (A&A 8:31 PM): crane_lift / crane_swing keys still hang the hook over the old z 13 slot; drive the joints from crane_solve' });
  rep.reach[k] = { pad: np.map(r3), world: [r3(np[0] + PWX), r3(np[1]), r3(np[2])], crane_r_m: r3(r), trolley_max_m: cx.trolley_max_m, margin_m: r3(cx.trolley_max_m - r) }; }
cr.setExtras({ ...cx, origin: cx.origin.replace('world (480.6, 0, 7.0)', `world (${r3(cT[0] + PWX)}, 0, ${r3(cT[2])})`) });
const after = {}; for (const k of MK.concat(['Spur_Taper_In_A', 'Spur_Taper_In_B', 'Spur_Taper_Out_A', 'Spur_Taper_Out_B'])) after[k] = { t: N(k).getTranslation().map(r3), world: W(N(k).getTranslation()[0], N(k).getTranslation()[2]), extras: N(k).getExtras() };
rep.markers_before = before; rep.markers_after = after; rep.path_pad = path; rep.path_world = path.map(p => W(...p));
const ext = R.listExtensionsUsed().find(e => e.extensionName === 'EXT_meshopt_compression'); ext.setEncoderOptions({ method: EXTMeshoptCompression.EncoderMethod.QUANTIZE });
await io.write(OUT, doc); fs.writeFileSync(REP, JSON.stringify(rep, null, 1));
console.log(JSON.stringify({ pipe_hw: rep.pipe_hw, pipe_end_after: rep.pipe_end_after, uturn: rep.uturn, spur: rep.spur_ribbon, reach: rep.reach, path_world: rep.path_world }, null, 0));
