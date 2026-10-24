// Verify cargo_dock_overhead_v4.glb in three.js playback. usage: node verify_v4.mjs DOCK_V4.glb FB05.glb OUT.json
import fs from 'fs';
import { RIG, STOP, PICKS, SLOTS, CLIPS, KT, EVENTS, DOCK_WORLD } from './v4_layout.mjs';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js'); await MeshoptDecoder.ready;
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const [,, DOCK, FB, OUT] = process.argv; const O = DOCK_WORLD; const W = p => [p[0] + O[0], p[1] + O[1], p[2] + O[2]];
const g = await load(DOCK); const S = g.scene; S.position.set(...O); S.traverse(o => { if (/^Tier_/.test(o.name)) o.visible = false; }); S.updateMatrixWorld(true);
const isTier = o => { for (let q = o; q; q = q.parent) if (/^Tier_/.test(q.name)) return true; return false; };
const isRig = o => { for (let q = o; q; q = q.parent) if (q.name === 'GC_Rig') return true; return false; };
// draws at Lv1 (visible meshes x primitives; three splits multi-material meshes into children)
let draws = 0; const drawList = []; S.traverse(o => { if (o.isMesh && !isTier(o)) { draws++; drawList.push(o.name); } });
// static Lv1 dock height raster (0.1 m) over the crane work area, local x -8..8, z 1..24; plus all static points for the camera + road checks
const C = 0.1, X0 = -8, Z0 = 1, NX = 160, NZ = 230; const H = new Float32Array(NX * NZ).fill(-1); const statPts = []; let roadMinY = 1e9, roadMinYGround = 1e9, roadItems = [];
const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
S.traverse(o => { if (!o.isMesh || isTier(o) || isRig(o)) return; const P = o.geometry.attributes.position, I = o.geometry.index;
  for (let i = 0; i < P.count; i++) { a.fromBufferAttribute(P, i).applyMatrix4(o.matrixWorld); statPts.push([a.x, a.y, a.z]); const lz = a.z - O[2];
    if (lz > 17.2 + 1e-4) { roadMinY = Math.min(roadMinY, a.y); } }
  for (let t = 0; t < I.count; t += 3) { a.fromBufferAttribute(P, I.getX(t)).applyMatrix4(o.matrixWorld); b.fromBufferAttribute(P, I.getX(t + 1)).applyMatrix4(o.matrixWorld); c.fromBufferAttribute(P, I.getX(t + 2)).applyMatrix4(o.matrixWorld);
    const zmax = Math.max(a.z, b.z, c.z) - O[2]; if (zmax > 17.2 + 1e-4) { const ymin = Math.min(a.y, b.y, c.y); if (ymin < roadMinYGround) roadMinYGround = ymin; }
    const e = Math.max(a.distanceTo(b), b.distanceTo(c), c.distanceTo(a)); const s = Math.max(1, Math.ceil(e / (C * 0.5)));
    for (let i = 0; i <= s; i++) for (let j = 0; j <= s - i; j++) { const u = i / s, v = j / s, w = 1 - u - v; const x = a.x * w + b.x * u + c.x * v - O[0], z = a.z * w + b.z * u + c.z * v - O[2], y = a.y * w + b.y * u + c.y * v;
      const cx = Math.floor((x - X0) / C), cz = Math.floor((z - Z0) / C); if (cx < 0 || cz < 0 || cx >= NX || cz >= NZ) continue; const q = cz * NX + cx; if (y > H[q]) H[q] = y; } } });
// road: min y of the actual surfaces at local z > 17.2 (dense samples, 2 cm)
let roadSurfMinY = 1e9; S.traverse(o => { if (!o.isMesh || isTier(o) || isRig(o)) return; const P = o.geometry.attributes.position, I = o.geometry.index;
  for (let t = 0; t < I.count; t += 3) { a.fromBufferAttribute(P, I.getX(t)).applyMatrix4(o.matrixWorld); b.fromBufferAttribute(P, I.getX(t + 1)).applyMatrix4(o.matrixWorld); c.fromBufferAttribute(P, I.getX(t + 2)).applyMatrix4(o.matrixWorld);
    if (Math.max(a.z, b.z, c.z) - O[2] <= 17.2) continue; const e = Math.max(a.distanceTo(b), b.distanceTo(c), c.distanceTo(a)); const s = Math.max(1, Math.ceil(e / 0.02));
    for (let i = 0; i <= s; i++) for (let j = 0; j <= s - i; j++) { const u = i / s, v = j / s, w = 1 - u - v; const z = a.z * w + b.z * u + c.z * v - O[2]; if (z > 17.2) roadSurfMinY = Math.min(roadSurfMinY, a.y * w + b.y * u + c.y * v); } } });
const hMax = (x0, x1, z0, z1) => { let m = -1; for (let i = Math.max(0, Math.floor((x0 - X0) / C)); i <= Math.min(NX - 1, Math.floor((x1 - X0) / C)); i++) for (let j = Math.max(0, Math.floor((z0 - Z0) / C)); j <= Math.min(NZ - 1, Math.floor((z1 - Z0) / C)); j++) m = Math.max(m, H[j * NX + i]); return m; };
// FB-05 at the new stop
const fbg = await load(FB); const F = fbg.scene; F.position.set(...STOP.world); F.updateMatrixWorld(true); const truckPts = []; F.traverse(o => { if (!o.isMesh) return; const P = o.geometry.attributes.position; for (let i = 0; i < P.count; i++) { a.fromBufferAttribute(P, i).applyMatrix4(o.matrixWorld); truckPts.push([a.x - O[0], a.y, a.z - O[2]]); } });
const BX = 1.2, BZ = 0.67, BH = 1.5;  // CargoBox bbox half-x, half-z, height (2.4 x 1.5 x 1.34, as SC-1 verify)
const boxPts = (base) => { const r = []; for (const dx of [-BX, BX]) for (const dz of [-BZ, BZ]) for (const dy of [0, BH]) r.push([base[0] + dx, base[1] + dy, base[2] + dz]); return r; };
// truck clearance: min vertical gap between carried box bottom and truck points under its footprint (excluding the bed slot being worked + the other bed box handled separately)
const truckUnder = (bx, bz, y0) => { let m = 1e9; for (const p of truckPts) if (Math.abs(p[0] - bx) <= BX && Math.abs(p[2] - bz) <= BZ) m = Math.min(m, y0 - p[1]); return m; };
// exact double-precision Hermite eval of the GLB keyframes (independent of three.js)
const J = JSON.parse(fs.readFileSync(DOCK).subarray(20, 20 + fs.readFileSync(DOCK).readUInt32LE(12)).toString());
const mx = new THREE.AnimationMixer(S); const ha = S.getObjectByName('Hook_Attach'); const v = new THREE.Vector3(), q = new THREE.Quaternion();
const joints = ['GC_Bridge', 'GC_Trolley', 'GC_Hook', 'Hook_Attach'].map(n => S.getObjectByName(n));
const R = { pick_err_max_m: 0, set_err_max_m: 0, yaw_max_deg: 0, rot_channels: 0, clear_stack_travel_m: 1e9, gap_neighbour_set_m: 1e9, clear_truck_m: 1e9, clear_otherbed_m: 1e9, clear_dock_travel_m: 1e9,
  bridge_sweep_clear_m: 1e9, stack_penetration_m: 0, tier2_unsupported: 0, hook_block_over_truck_m: 1e9, rig_pts: [] };
const fill = n => SLOTS.slice(0, n);  // Store_*_Slot_N: slots 1..N-1 occupied; Load_*_Slot_N (LIFO): slots 1..N-1 occupied
const envPts = [];
for (const clip of g.animations) {
  const meta = CLIPS.find(c => c.name === clip.name); if (!meta) continue; for (const tr of clip.tracks) if (/quaternion/.test(tr.name)) R.rot_channels++;
  const store = clip.name.startsWith('Store'), k = clip.name[store ? 6 : 5], N = +clip.name.slice(-2), slot = SLOTS[N - 1], pick = PICKS[k]; const stored = fill(N - 1);
  const other = k === 'A' ? PICKS.B : PICKS.A; const otherOnBed = store ? k === 'A' : k === 'B';   // Store A first (B still on bed); Load A first (empty bed), then B (A on bed)
  if (slot.tier === 2 && !stored.some(s => s.block === slot.block && s.row === slot.row && s.tier === 1)) R.tier2_unsupported++;
  mx.stopAllAction(); mx.clipAction(clip).play();
  for (let i = 0; i <= 480; i++) { const t = i / 60; mx.setTime(t); S.updateMatrixWorld(true); ha.getWorldPosition(v); ha.getWorldQuaternion(q);
    const yaw = Math.abs(new THREE.Euler().setFromQuaternion(q, 'YXZ').y) * 180 / Math.PI; R.yaw_max_deg = Math.max(R.yaw_max_deg, yaw);
    const L = [v.x - O[0], v.y, v.z - O[2]];
    if (Math.abs(t - EVENTS.pick) < 1e-6 || Math.abs(t - 1.9) < 1e-6 || Math.abs(t - 2.05) < 1e-6) { const tg = meta.from.hook; R.pick_err_max_m = Math.max(R.pick_err_max_m, Math.hypot(L[0] - tg[0], L[1] - tg[1], L[2] - tg[2])); }
    if (Math.abs(t - EVENTS.set) < 1e-6 || Math.abs(t - 5.7) < 1e-6 || Math.abs(t - 5.85) < 1e-6) { const tg = meta.to.hook; R.set_err_max_m = Math.max(R.set_err_max_m, Math.hypot(L[0] - tg[0], L[1] - tg[1], L[2] - tg[2])); }
    // rig envelope (bridge + trolley + hook block) for the camera
    const bz = joints[0].position.z, tx = joints[1].position.x; for (const x of [-7.9, 7.9]) for (const z of [-1.5, 2.3]) envPts.push([x + O[0], 11.5, bz + z + O[2]]); for (const z of [-1.4, 1.4]) envPts.push([tx + 1.45 + O[0], 12.4, bz + z + O[2]], [tx - 1.45 + O[0], 12.4, bz + z + O[2]]);
    envPts.push([v.x, v.y, v.z]);
    // bridge sweep: girder bottom 9.925 over x -7.9..7.9 (excluding the runway |x| > 6.8), cab bottom 8.15 over x 4.75..6.45, z bz+0.6..bz+2.3
    R.bridge_sweep_clear_m = Math.min(R.bridge_sweep_clear_m, 9.925 - hMax(-6.8, 6.8, bz - 1.25, bz + 1.25), 8.15 - hMax(4.75, 6.45, bz + 0.6, bz + 2.3));
    const carried = t > EVENTS.pick && t < EVENTS.set; const base = [L[0], L[1] - 1.5, L[2]];
    if (!carried) { // empty hook block (bottom = Hook_Attach) over the truck
      const atOwnPick = Math.hypot(L[0] - pick.hook[0], L[2] - pick.hook[2]) < 0.01;
      if (!atOwnPick && Math.abs(L[2] - STOP.local[2]) < 2.5) { let top = Math.max(-1, ...truckPts.filter(p => Math.abs(p[0] - L[0]) <= 0.45 && Math.abs(p[2] - L[2]) <= 0.3).map(p => p[1]));
        for (const pb of Object.values(PICKS)) if (Math.abs(pb.box_base[0] - L[0]) <= BX + 0.45 && Math.abs(pb.box_base[2] - L[2]) <= BZ + 0.3) top = Math.max(top, pb.box_base[1] + BH);
        R.hook_block_over_truck_m = Math.min(R.hook_block_over_truck_m, L[1] - top); }
      continue; }
    for (const p of boxPts(base)) envPts.push([p[0] + O[0], p[1], p[2] + O[2]]);
    const travel = t >= 2.55 && t <= 5.15;
    for (const s of stored) { if (!store && s.name === slot.name) continue; const sb = s.box_base; const ox = Math.min(base[0] + BX, sb[0] + BX) - Math.max(base[0] - BX, sb[0] - BX), oz = Math.min(base[2] + BZ, sb[2] + BZ) - Math.max(base[2] - BZ, sb[2] - BZ);
      if (ox > 0 && oz > 0) { if (travel) R.clear_stack_travel_m = Math.min(R.clear_stack_travel_m, base[1] - (sb[1] + BH)); else if (base[1] < sb[1] + BH - 1e-6) R.stack_penetration_m = Math.max(R.stack_penetration_m, sb[1] + BH - base[1]); }
      else if (base[1] < sb[1] + BH && base[1] + BH > sb[1]) R.gap_neighbour_set_m = Math.min(R.gap_neighbour_set_m, Math.max(-ox, -oz)); }
    if (otherOnBed) { const ob = other.box_base; const ox = Math.min(base[0] + BX, ob[0] + BX) - Math.max(base[0] - BX, ob[0] - BX), oz = Math.min(base[2] + BZ, ob[2] + BZ) - Math.max(base[2] - BZ, ob[2] - BZ);
      if (ox > 0 && oz > 0) R.clear_otherbed_m = Math.min(R.clear_otherbed_m, base[1] - (ob[1] + BH)); else if (base[1] < ob[1] + BH) R.clear_otherbed_m = Math.min(R.clear_otherbed_m, Math.max(-ox, -oz)); }
    // truck: only when not sitting on its own bed slot
    if (Math.hypot(base[0] - pick.box_base[0], base[2] - pick.box_base[2]) > 0.01) R.clear_truck_m = Math.min(R.clear_truck_m, truckUnder(base[0], base[2], base[1]));
    if (travel) R.clear_dock_travel_m = Math.min(R.clear_dock_travel_m, base[1] - hMax(base[0] - BX, base[0] + BX, base[2] - BZ, base[2] + BZ)); } }
// camera spare (same rule as v3)
const SIZES = [{ W: 375, H: 667, top: 144, bot: 383 }, { W: 393, H: 852, top: 165, bot: 534 }]; const CT = [369.5, 1.5, 8.6], FW = 48;
const cam = new THREE.PerspectiveCamera(38, 1, 0.1, 2000);
function px(sz, pts) { cam.aspect = sz.W / sz.H; cam.updateProjectionMatrix(); const d = (FW / 2) / (Math.tan(19 * Math.PI / 180) * cam.aspect), p = 18 * Math.PI / 180;
  cam.position.set(CT[0], CT[1] + d * Math.sin(p), CT[2] + d * Math.cos(p)); cam.lookAt(...CT); cam.updateMatrixWorld(true);
  let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9; for (const q of pts) { v.set(q[0], q[1], q[2]).project(cam); const X = (v.x + 1) / 2 * sz.W, Y = (1 - v.y) / 2 * sz.H; x0 = Math.min(x0, X); x1 = Math.max(x1, X); y0 = Math.min(y0, Y); y1 = Math.max(y1, Y); }
  return { px: [x0, y0, x1, y1].map(z => +z.toFixed(1)), spare: { left: +x0.toFixed(1), right: +(sz.W - x1).toFixed(1), top: +(y0 - sz.top).toFixed(1), bottom: +(sz.bot - y1).toFixed(1) } }; }
const storagePts = SLOTS.flatMap(s => boxPts(s.box_base).map(p => [p[0] + O[0], p[1], p[2] + O[2]]));
const truckW = truckPts.map(p => [p[0] + O[0], p[1], p[2] + O[2]]);
const groups = { dock: statPts, truck: truckW, storage: storagePts, crane_env: envPts };
const cams = {}; for (const sz of SIZES) { const all = Object.values(groups).flat(); const r = px(sz, all); const per = {}; for (const [k, p] of Object.entries(groups)) per[k] = px(sz, p).px;
  const bw = SLOTS.map(s => { const P = boxPts(s.box_base).map(p => [p[0] + O[0], p[1], p[2] + O[2]]); const r2 = px(sz, P); return r2.px[2] - r2.px[0]; });
  cams[`${sz.W}x${sz.H}`] = { band_y: [sz.top, sz.bot], subject_px: r.px, spare_px: r.spare, per_group_px: per, box_w_px_min: +Math.min(...bw).toFixed(1), box_w_px_max: +Math.max(...bw).toFixed(1) }; }
delete R.rig_pts;
const res = { glb: DOCK, draws_lv1: draws, draw_nodes: drawList, road: { static_min_y_over_local_z_gt_17_2: +roadMinY.toFixed(3), static_tri_min_y_reaching_z_gt_17_2: +roadMinYGround.toFixed(3), static_surface_min_y_at_z_gt_17_2: +roadSurfMinY.toFixed(3), rule: 'no dock ground geometry at local z > 17.2 (world z > 9.2); overhead only' },
  checks: Object.fromEntries(Object.entries(R).map(([k, x]) => [k, typeof x === 'number' ? +x.toPrecision(4) : x])), camera: cams, clips: g.animations.filter(c => CLIPS.some(m => m.name === c.name)).length };
const ok = res.checks.pick_err_max_m < 1e-6 && res.checks.set_err_max_m < 1e-6 && res.checks.yaw_max_deg < 1e-6 && res.checks.rot_channels === 0 && res.checks.clear_stack_travel_m > 0.5 && res.checks.clear_truck_m > 0.3
  && res.checks.clear_dock_travel_m > 0.5 && res.checks.bridge_sweep_clear_m > 0.2 && res.checks.gap_neighbour_set_m > 0.2 && res.road.static_surface_min_y_at_z_gt_17_2 >= 6.3 && res.checks.stack_penetration_m < 1e-6 && res.checks.tier2_unsupported === 0 && res.checks.hook_block_over_truck_m > 0.5 && res.clips === 80
  && Object.values(cams).every(c => Object.values(c.spare_px).every(s => s >= 5) && c.box_w_px_min >= 8) && draws <= 11;
res.pass = ok; fs.writeFileSync(OUT, JSON.stringify(res, null, 1)); console.log(JSON.stringify({ pass: ok, draws, road: res.road, checks: res.checks, cam: Object.fromEntries(Object.entries(cams).map(([k, c]) => [k, { spare: c.spare_px, box: c.box_w_px_min }])) }, null, 0));
