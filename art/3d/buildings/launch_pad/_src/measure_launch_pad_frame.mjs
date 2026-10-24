// Spare room (px) inside the phone safe bands for the Launch Pad game camera, measured on REAL vertices through the qa3d camera math:
// PerspectiveCamera(38 deg vFOV, aspect W/H), eye = Cam_Target + d * (0, sin18, cos18), lookAt(Cam_Target), d = (frame_w/2) / (tan19 * aspect).
// Groups: every named mesh node of launch_pad_game.glb (rest pose; Road_UTurn included) + 'Truck' = FB-05 at Truck_Stop with cargo_box on
// Pick_Point and Pick_Point_02. usage:
//   node measure_launch_pad_frame.mjs ../launch_pad_game.glb [out.json] [--cam tx,ty,tz,fw] [--solve 5]
import fs from 'fs'; import path from 'path';
const NM = process.env.NODE_PATH || '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
await MeshoptDecoder.ready;
const args = process.argv.slice(2); const f = args[0]; const outp = args[1] && !args[1].startsWith('--') ? args[1] : null;
const opt = k => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
const HERE = path.dirname(new URL(import.meta.url).pathname); const PROPS = path.resolve(HERE, '../../../props');
const BANDS = { '393x852': [12, 381, 165, 534], '375x667': [12, 363, 144, 383] };
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const g = await load(f); const S = g.scene; S.updateMatrixWorld(true);
const NN = o => { while (o && o !== S && !o.name.replace(/^mesh_\d+(_\d+)?$/, '')) o = o.parent; return o && o !== S ? o.name : '?'; };
const W = n => S.getObjectByName(n).getWorldPosition(new THREE.Vector3());
const G = {}; const v = new THREE.Vector3();
const addMesh = (o, k) => { const pos = o.geometry.attributes.position; const A = G[k] || (G[k] = []);
  for (let i = 0; i < pos.count; i++) { o.getVertexPosition ? o.getVertexPosition(i, v) : v.fromBufferAttribute(pos, i); v.applyMatrix4(o.matrixWorld); A.push(v.x, v.y, v.z); } };
S.traverse(o => { if (o.isMesh) addMesh(o, NN(o)); });
const ts = W('Truck_Stop'); const ty = S.getObjectByName('Truck_Stop').userData.yaw_deg || 0;
const truck = (await load(path.join(PROPS, 'fb05/fb05_game.glb'))).scene; truck.position.copy(ts); truck.rotation.y = ty * Math.PI / 180;
const T2 = new THREE.Group(); T2.add(truck);
for (const n of ['Pick_Point', 'Pick_Point_02']) { const b = (await load(path.join(PROPS, 'cargo_box/cargo_box_game.glb'))).scene; b.position.copy(W(n)); T2.add(b); }
T2.updateMatrixWorld(true); T2.traverse(o => { if (o.isMesh) addMesh(o, 'Truck'); });
// Crane reach: the skinned PC-1 swept over the slew arc its targets use (Hold_Door 1.5732 rad -> pi -> Pick_Point -2.2896 rad), trolley at 2.6 and 14.2 m,
// hook/box hanging at the shortest hoist; plus a 2.3x1.5x1.3 box hanging at every crane_target. '--crane360' sweeps the full circle instead.
{ const cr = S.getObjectByName('Crane'), sl = S.getObjectByName('Slew'), tr = S.getObjectByName('Trolley'), ho = S.getObjectByName('Hoist'), hk = S.getObjectByName('Hook');
  const r0 = sl.rotation.y, t0 = tr.position.x, h0 = ho.scale.y, k0 = hk.position.y; const ud = cr.userData; const sk = []; cr.traverse(o => { if (o.isSkinnedMesh) sk.push(o); });
  const a0 = args.includes('--crane360') ? -Math.PI : 1.5732, a1 = args.includes('--crane360') ? Math.PI : 2 * Math.PI - 2.2896;
  for (let a = a0; a <= a1 + 1e-6; a += Math.PI / 180) for (const r of [ud.trolley_min_m, ud.trolley_max_m]) {
    sl.rotation.y = a; tr.position.x = r; ho.scale.y = ud.hoist_min_m; hk.position.y = ud.hook_rest_local_y + 1 - ud.hoist_min_m; S.updateMatrixWorld(true);
    for (const o of sk) addMesh(o, 'Crane_Reach'); }
  sl.rotation.y = r0; tr.position.x = t0; ho.scale.y = h0; hk.position.y = k0; S.updateMatrixWorld(true);
  const [bx, by, bz] = ud.box_size_m; const A = G['Crane_Reach'];
  S.traverse(o => { if (o.userData.kind === 'crane_target') { const p = o.getWorldPosition(new THREE.Vector3()); for (const sx of [-1, 1]) for (const sy of [0, 1]) for (const sz of [-1, 1]) A.push(p.x + sx * bx / 2, p.y + sy * (by + 1.5), p.z + sz * bz / 2); } });
}
// Receiving astronaut: receiver_game.glb root at Receiver_Spot with its yaw, rest pose + every frame (10 Hz) of its guide / check_in clips
{ const rs = S.getObjectByName('Receiver_Spot'); const rg = await load(path.resolve(PROPS, '../crew/receiver/receiver_game.glb')); const R = rg.scene;
  R.position.copy(W('Receiver_Spot')); R.rotation.y = (rs.userData.yaw_deg || 0) * Math.PI / 180; R.updateMatrixWorld(true);
  const grab = () => { R.updateMatrixWorld(true); R.traverse(o => { if (o.isMesh) addMesh(o, 'Receiver'); }); }; grab();
  const mx = new THREE.AnimationMixer(R); const used = [];
  for (const c of rg.animations) { if (!/guide|check/i.test(c.name)) continue; used.push(c.name); mx.stopAllAction(); const ac = mx.clipAction(c); ac.play();
    for (let t = 0; t <= c.duration + 1e-6; t += 0.1) { ac.time = t; mx.update(0); grab(); } }
  console.error('receiver clips sampled:', used.join(', ') || 'none', '| all clips:', rg.animations.map(c => c.name).join(', '));
}
// shrink every group to its convex hull (the projected extremes of a point set are always hull points) so the solver runs fast
{ const { ConvexHull } = await import(NM + '/three/examples/jsm/math/ConvexHull.js');
  for (const k in G) { const A = G[k]; if (A.length < 300) continue; const pts = []; for (let i = 0; i < A.length; i += 3) pts.push(new THREE.Vector3(A[i], A[i + 1], A[i + 2]));
    const h = new ConvexHull().setFromPoints(pts); const out = []; for (const vv of h.vertices) out.push(vv.point.x, vv.point.y, vv.point.z); G[k] = out; } }
const SKIP = (opt('--skip') || '').split(',').filter(Boolean); for (const k of SKIP) delete G[k];
const ct = S.getObjectByName('Cam_Target'); let cam = [...W('Cam_Target').toArray(), ct.userData.frame_w];
if (opt('--cam')) cam = opt('--cam').split(',').map(Number);
const e = 18 * Math.PI / 180, vt = Math.tan(19 * Math.PI / 180);
function measure(c, full) {
  const res = {}; let worst = 1e9;
  for (const [key, [x0, x1, y0, y1]] of Object.entries(BANDS)) {
    const [w, h] = key.split('x').map(Number); const C = new THREE.PerspectiveCamera(38, w / h, 0.5, 3000); const d = (c[3] / 2) / (vt * (w / h));
    C.position.set(c[0], c[1] + d * Math.sin(e), c[2] + d * Math.cos(e)); C.lookAt(c[0], c[1], c[2]); C.updateMatrixWorld(); C.updateProjectionMatrix();
    const M = new THREE.Matrix4().multiplyMatrices(C.projectionMatrix, C.matrixWorldInverse).elements; const r = { distance_m: +d.toFixed(3), groups: {} };
    for (const [k, A] of Object.entries(G)) { let a = 1e9, b = -1e9, p = 1e9, q = -1e9;
      for (let i = 0; i < A.length; i += 3) { const X = A[i], Y = A[i + 1], Z = A[i + 2]; const ww = M[3] * X + M[7] * Y + M[11] * Z + M[15];
        const sx = ((M[0] * X + M[4] * Y + M[8] * Z + M[12]) / ww + 1) / 2 * w, sy = (1 - (M[1] * X + M[5] * Y + M[9] * Z + M[13]) / ww) / 2 * h;
        if (sx < a) a = sx; if (sx > b) b = sx; if (sy < p) p = sy; if (sy > q) q = sy; }
      const sp = { left: a - x0, right: x1 - b, top: p - y0, bottom: y1 - q }; worst = Math.min(worst, sp.left, sp.right, sp.top, sp.bottom);
      if (full) r.groups[k] = { px: [+a.toFixed(1), +b.toFixed(1), +p.toFixed(1), +q.toFixed(1)], spare: Object.fromEntries(Object.entries(sp).map(([s, z]) => [s, +z.toFixed(1)])) }; }
    res[key] = r; }
  return { worst, res };
}
if (opt('--solve')) {    // smallest frame_w (whole metres / 0.5) whose best target gives >= need px everywhere; ty kept
  const need = +opt('--solve'); let best = null;
  for (let fw = cam[3]; fw <= 140 && !best; fw += +(opt('--step') || 0.5)) {
    let bx = null;
    for (let tx = cam[0]; tx <= cam[0]; tx += 1) for (let tz = -6; tz <= 16; tz += 0.25) {   /* tx only slides sideways: held, balanced below */ const m = measure([tx, cam[1], tz, fw]).worst; if (!bx || m > bx[0]) bx = [m, tx, tz]; }
    for (let tx = bx[1]; tx <= bx[1]; tx += 1) for (let tz = bx[2] - 0.5; tz <= bx[2] + 0.5; tz += 0.05) { const m = measure([tx, cam[1], tz, fw]).worst; if (m > bx[0]) bx = [m, tx, tz]; }
    console.log('fw', fw, 'best worst-spare', bx[0].toFixed(2), 'at tx', bx[1].toFixed(2), 'tz', bx[2].toFixed(2));
    if (bx[0] >= need) best = [+bx[1].toFixed(2), cam[1], +bx[2].toFixed(2), fw];
  }
  // tx only slides the picture sideways (no yaw): centre it so left and right spare are balanced
  const hmin = c => { const r = measure(c, true).res; let L = 1e9, R = 1e9; for (const k in r) for (const gg of Object.values(r[k].groups)) { L = Math.min(L, gg.spare.left); R = Math.min(R, gg.spare.right); } return Math.min(L, R); };
  let bt = [hmin(best), best[0]]; for (let tx = -10; tx <= 10; tx += 0.05) { const m = hmin([tx, best[1], best[2], best[3]]); if (m > bt[0] + 1e-9) bt = [m, tx]; }
  best[0] = +bt[1].toFixed(2); cam = best; console.log('SOLVED', JSON.stringify(best));
}
const m = measure(cam, true);
const out = { rule: 'spare px inside the safe band, per group, real vertices, qa3d camera math', bands: BANDS, cam_target: cam.slice(0, 3), frame_w: cam[3], worst_spare_px: +m.worst.toFixed(1), sizes: m.res };
console.log(JSON.stringify(out, null, 1)); if (outp) fs.writeFileSync(outp, JSON.stringify(out, null, 1));
