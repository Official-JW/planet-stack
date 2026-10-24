// Refinery station camera override search (Game Coder's per-station Cam_Target / frame_w table; no GLB re-export).
// Camera = QA3D main.js fitSite()/poseLook(): look at Cam_Target, 38 deg vFOV, 18 deg down, d = (frame_w/2)/(tan 19 deg * aspect).
// Scene (world): refinery_game.glb at +320 with ALL tiers shown and every clip sampled (25 steps each; ground/road verts y <= 0.30 left out,
// they run off both screen edges by design), crane at (311, 0, 17.5) with its concrete pad, FB-05 parked at Truck_Park (318, 0, 13),
// a full 8-box pallet, boxes on both bed slots, and the crane posed through every real load cycle: for each Pallet_Slot_01..08 x each
// Drop_Point / Drop_Point_02: hoist up from the slot to carry height (box bottom 4.7), swing over the far (-Z) side while the trolley
// runs, lower onto the drop point; then the empty hook back the same way. Each pose is sampled with and without a box on the hook.
// Spare = px from each group's screen bbox to the safe band (top/bottom) and to the screen edges (left/right).
// usage: node refinery_override_search.mjs search [fw_min] | node refinery_override_search.mjs check X Y Z FW
//   (needs 'three' r186 resolvable, e.g. run from a dir whose node_modules/three -> /home/box/apps/gltftools/node_modules/three)
import fs from 'fs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
await MeshoptDecoder.ready;
const R = '/workspace/planet-stack/art/3d/';
const load = f => new Promise((res, rej) => { const b = fs.readFileSync(f); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
export const SIZES = [{ w: 393, h: 852, top: 165, bot: 534 }, { w: 375, h: 667, top: 144, bot: 383 }];
export const MARGIN = 5;
const v = new THREE.Vector3();
const HULL = new WeakMap(); // per-mesh local support points (affine joint/clip transforms keep hull extremes; no skinned meshes here)
function collect(o, filt) { o.updateMatrixWorld(true); const a = [];
  o.traverse(m => { if (!m.isMesh) return; for (let q = m; q; q = q.parent) if (!q.visible) return;
    if (m.isSkinnedMesh || m.morphTargetInfluences) { const p = m.geometry.attributes.position; // skinned/morphed: every vertex, posed
      for (let i = 0; i < p.count; i++) { m.getVertexPosition(i, v); v.applyMatrix4(m.matrixWorld); if (!filt || filt(v)) a.push(v.x, v.y, v.z); } return; }
    let L = filt ? null : HULL.get(m.geometry);
    if (filt) { const p = m.geometry.attributes.position; L = new Float32Array(p.count * 3); for (let i = 0; i < p.count; i++) { L[3 * i] = p.getX(i); L[3 * i + 1] = p.getY(i); L[3 * i + 2] = p.getZ(i); } }
    else if (!L) { const p = m.geometry.attributes.position, raw = [];
      for (let i = 0; i < p.count; i++) raw.push(p.getX(i), p.getY(i), p.getZ(i)); L = raw.length > 3000 ? reduce(raw, 1500) : new Float32Array(raw); HULL.set(m.geometry, L); }
    for (let i = 0; i < L.length; i += 3) { v.set(L[i], L[i + 1], L[i + 2]).applyMatrix4(m.matrixWorld); if (!filt || filt(v)) a.push(v.x, v.y, v.z); } });
  return a; }
function reduce(P, N = 4000) { // support points over a dense direction set (perspective extremes lie on the convex hull)
  const keep = new Set(), ga = Math.PI * (3 - Math.sqrt(5));
  for (let k = 0; k < N; k++) { const y = 1 - 2 * (k + .5) / N, r = Math.sqrt(1 - y * y), th = ga * k, dx = Math.cos(th) * r, dz = Math.sin(th) * r;
    let bi = 0, bv = -1e18; for (let i = 0; i < P.length; i += 3) { const d = P[i] * dx + P[i + 1] * y + P[i + 2] * dz; if (d > bv) { bv = d; bi = i; } } keep.add(bi); }
  const o = []; for (const i of keep) o.push(P[i], P[i + 1], P[i + 2]); return new Float32Array(o); }

export async function buildScene() {
  const scene = new THREE.Scene(), G = {};
  const rg = await load(R + 'buildings/refinery/refinery_game.glb'); const ref = rg.scene; ref.position.set(320, 0, 0);
  let ct = null; ref.traverse(n => { if (n.name === 'Cam_Target') ct = n; if (/^Tier_\d+/.test(n.name)) { n.visible = true; } });
  scene.add(ref); ref.updateMatrixWorld(true);
  const ctW = ct.getWorldPosition(new THREE.Vector3());
  // refinery: rest + every clip sampled
  const above = p => p.y > 0.30; let rp = collect(ref, above); const mx = new THREE.AnimationMixer(ref);
  for (const c of rg.animations) { const a = mx.clipAction(c); a.play(); const tn = new Set(c.tracks.map(t => t.name.split('.')[0])); const tg = [];
    ref.traverse(m => { if (!m.isMesh) return; let hit = false; for (let q = m; q && !hit; q = q.parent) if (tn.has(q.name)) hit = true;
      if (!hit && m.isSkinnedMesh) hit = m.skeleton.bones.some(b => { for (let q = b; q; q = q.parent) if (tn.has(q.name)) return true; return false; });
      if (hit) tg.push(m); });
    if (!tg.length) throw new Error('clip ' + c.name + ': no animated mesh found');
    for (let s = 0; s <= 24; s++) { mx.setTime(c.duration * s / 24); for (const n of tg) rp = rp.concat(collect(n, above)); } a.stop(); mx.setTime(0); }
  G.refinery = reduce(rp);
  // main building only (Base_Paint above ground + tiers) for the size-on-screen comparison
  const mb = []; for (const n of ['Base_Paint', 'Tier_03', 'Tier_05', 'Tier_08', 'Tier_12', 'Tier_20']) mb.push(...collect(ref.getObjectByName(n), above));
  G.refinery_main = reduce(mb);
  const crane = (await load(R + 'props/crane_refinery/crane_refinery_game.glb')).scene; crane.position.set(311, 0, 17.5); scene.add(crane);
  const fb = (await load(R + 'props/fb05/fb05_game.glb')).scene; fb.position.set(318, 0, 13); scene.add(fb);
  const boxG = await load(R + 'props/cargo_box/cargo_box_game.glb');
  scene.updateMatrixWorld(true);
  const W_ = n => scene.getObjectByName(n).getWorldPosition(new THREE.Vector3());
  G.fb05 = reduce(collect(fb));
  const croot = crane.getObjectByName('Crane_Refinery'), e = croot.userData;
  const padB = new THREE.Box3(new THREE.Vector3(...e.concrete_pad.min), new THREE.Vector3(...e.concrete_pad.max));
  const pc = []; for (const x of [padB.min.x, padB.max.x]) for (const y of [padB.min.y, padB.max.y]) for (const z of [padB.min.z, padB.max.z]) { const q = crane.localToWorld(new THREE.Vector3(x, y, z)); pc.push(q.x, q.y, q.z); }
  G.concrete_pad = new Float32Array(pc);
  const boxPts = (p) => { const b = boxG.scene.clone(true); b.position.copy(p); b.updateMatrixWorld(true); return collect(b); };
  const slots = []; for (let i = 1; i <= 8; i++) slots.push(W_('Pallet_Slot_0' + i));
  const drops = [W_('Drop_Point'), W_('Drop_Point_02')]; const bed = [W_('Bed_Slot_01'), W_('Bed_Slot_02')];
  let pb = []; for (const s of slots) pb = pb.concat(boxPts(s)); G.pallet_boxes = reduce(pb);
  // pallet deck + guides are part of the crane mesh; the crane group below covers them at every pose
  let bb = []; for (const s of bed) bb = bb.concat(boxPts(s)); G.bed_boxes = reduce(bb);
  // crane poses
  const slew = crane.getObjectByName('Slew'), tro = crane.getObjectByName('Trolley'), hoi = crane.getObjectByName('Hoist'), hook = crane.getObjectByName('Hook'); const hook0 = hook.position.y;
  const hookBox = boxG.scene.clone(true); hook.add(hookBox); hookBox.position.set(0, -1.5, 0);
  const solve = (P) => { const L0 = crane.worldToLocal(P.clone()); const H = L0.clone(); H.y += 1.5; return { th: Math.atan2(-H.z, H.x), r: Math.hypot(H.x, H.z), L: e.sheave_y - H.y - e.hook_drop_m }; };
  const setJ = ({ th, r, L }, withBox) => { slew.rotation.y = th; tro.position.x = r; hoi.scale.y = L; hook.position.y = hook0 + 1 - L; hook.rotation.y = -th; hookBox.visible = withBox; crane.updateMatrixWorld(true); };
  const Lc = e.sheave_y - 6.2 - e.hook_drop_m; // carry: hook target y 6.2 (box bottom 4.7)
  const poses = []; const lerp = (a, b, t) => a + (b - a) * t;
  const nth = (t) => (t <= 0.66 ? t + 2 * Math.PI : t); // swing via the far side: pallet theta (~2.8..3.5) down to drop (~0.6), through pi/2
  for (const s of slots) for (const d of drops) { const A = solve(s), B = solve(d); const tA = A.th < 0 ? A.th + 2 * Math.PI : A.th, tB = B.th;
    for (let k = 0; k <= 6; k++) poses.push({ th: A.th, r: A.r, L: lerp(A.L, Lc, k / 6) });
    for (let k = 0; k <= 16; k++) poses.push({ th: lerp(tA, tB, k / 16), r: lerp(A.r, B.r, k / 16), L: Lc });
    for (let k = 0; k <= 6; k++) poses.push({ th: B.th, r: B.r, L: lerp(Lc, B.L, k / 6) }); }
  let cp = [], cpPose = []; const PER = [];
  for (const p of poses) for (const wb of [true, false]) { setJ(p, wb); const pts = collect(crane); cp = cp.concat(pts); }
  G.crane_all_poses = reduce(cp);
  return { scene, ref, crane, fb, boxG, ct, ctW, G, nposes: poses.length, setJ, solve, slots, drops, bed, hookBox, e };
}
export function camFor(w, h, T, fw) { const a = w / h, cam = new THREE.PerspectiveCamera(38, a, 0.5, 3000);
  const d = (fw / 2) / (Math.tan(THREE.MathUtils.degToRad(19)) * a), el = THREE.MathUtils.degToRad(18);
  cam.position.set(T.x, T.y + d * Math.sin(el), T.z + d * Math.cos(el)); cam.lookAt(T.x, T.y, T.z); cam.updateMatrixWorld(); cam.updateProjectionMatrix(); return { cam, d }; }
export function bbox(P, cam, w, h) { let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
  for (let i = 0; i < P.length; i += 3) { v.set(P[i], P[i + 1], P[i + 2]).project(cam); const x = (v.x + 1) / 2 * w, y = (1 - v.y) / 2 * h; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  return { x0, y0, x1, y1 }; }
export function report(G, T, fw) { const o = {};
  for (const s of SIZES) { const { cam, d } = camFor(s.w, s.h, T, fw); const r = { d: +d.toFixed(2), groups: {} }; let minS = 1e9;
    for (const [k, P] of Object.entries(G)) { const b = bbox(P, cam, s.w, s.h);
      const sp = { top: b.y0 - s.top, bottom: s.bot - b.y1, left: b.x0, right: s.w - b.x1 };
      r.groups[k] = { px: [b.x0, b.y0, b.x1, b.y1].map(q => +q.toFixed(1)), spare: Object.fromEntries(Object.entries(sp).map(([a, q]) => [a, +q.toFixed(1)])), h_px: +(b.y1 - b.y0).toFixed(1), w_px: +(b.x1 - b.x0).toFixed(1) };
      if (k !== 'refinery_main') minS = Math.min(minS, ...Object.values(sp)); }
    // whole-station envelope (all groups)
    const all = Object.entries(r.groups).filter(([k]) => k !== 'refinery_main').map(([, g]) => g.px);
    const A = [Math.min(...all.map(q => q[0])), Math.min(...all.map(q => q[1])), Math.max(...all.map(q => q[2])), Math.max(...all.map(q => q[3]))];
    r.envelope = { px: A, spare: { top: +(A[1] - s.top).toFixed(1), bottom: +(s.bot - A[3]).toFixed(1), left: +A[0].toFixed(1), right: +(s.w - A[2]).toFixed(1) } };
    r.min_spare = +minS.toFixed(2); o[s.w + 'x' + s.h] = r; }
  o.min_spare = Math.min(...SIZES.map(s => o[s.w + 'x' + s.h].min_spare)); return o; }

if (import.meta.url === 'file://' + process.argv[1]) {
  const S = await buildScene(); const mode = process.argv[2] || 'search';
  if (mode === 'check') { const [x, y, z, fw] = process.argv.slice(3).map(Number);
    console.log(JSON.stringify({ cam_target: [x, y, z], frame_w: fw, crane_poses: S.nposes, ...report(S.G, new THREE.Vector3(x, y, z), fw) }, null, 1)); }
  else { const fwMin = +(process.argv[3] || 37.5); const X = S.ctW.x, Y = S.ctW.y; const res = [];
    for (let fw = fwMin; fw <= fwMin + 6; fw = +(fw + 0.1).toFixed(1)) { let best = null;
      for (let z = 5; z <= 18; z = +(z + 0.05).toFixed(2)) { const r = report(S.G, new THREE.Vector3(X, Y, z), fw); if (!best || r.min_spare > best.min) best = { z, min: r.min_spare }; }
      res.push({ fw, ...best }); console.error(fw, JSON.stringify(best)); if (best.min >= MARGIN) break; }
    console.log(JSON.stringify({ cam_target_xy: [X, Y], glb_cam_target: S.ctW.toArray(), glb_frame_w: S.ct.userData.frame_w, crane_poses: S.nposes, search: res }, null, 1)); }
}
