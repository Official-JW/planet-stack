// Mine / Life Support / Dock camera-override audit + search for QA3D a25e5d0.
// Camera = main.js fitSite()/poseLook(): look at T (Cam_Target world, override axes replace Art's, station-local + i*160 on X),
// 38 deg vFOV, 18 deg down, no yaw; d = (frame_w/2)/(tan19 * aspect). Spare = px from each group's screen bbox to the band
// (top/bottom) and the screen edges (left/right). Ground/road (verts y <= 0.30) left out, except the Mine's two deposit patches.
import fs from 'fs'; import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
await MeshoptDecoder.ready;
const M = '/workspace/planet-stack/qa3d/models/';
const load = f => new Promise((res, rej) => { const b = fs.readFileSync(M + f); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
export const SIZES = [{ w: 393, h: 852, top: 165, bot: 534 }, { w: 375, h: 667, top: 144, bot: 383 }];
const v = new THREE.Vector3(), TAN = Math.tan(19 * Math.PI / 180), E = 18 * Math.PI / 180, SE = Math.sin(E), CE = Math.cos(E);
function collect(o, filt) { o.updateMatrixWorld(true); const a = [];
  o.traverse(m => { if (!m.isMesh) return; for (let q = m; q; q = q.parent) if (!q.visible) return; const p = m.geometry.attributes.position;
    for (let i = 0; i < p.count; i++) { if (m.isSkinnedMesh || m.morphTargetInfluences) m.getVertexPosition(i, v); else v.fromBufferAttribute(p, i); v.applyMatrix4(m.matrixWorld); if (!filt || filt(v)) a.push(v.x, v.y, v.z); } });
  return a; }
function reduce(P, N = 3000) { const keep = new Set(), ga = Math.PI * (3 - Math.sqrt(5));
  for (let k = 0; k < N; k++) { const y = 1 - 2 * (k + .5) / N, r = Math.sqrt(1 - y * y), th = ga * k, dx = Math.cos(th) * r, dz = Math.sin(th) * r;
    let bi = 0, bv = -1e18; for (let i = 0; i < P.length; i += 3) { const d = P[i] * dx + P[i + 1] * y + P[i + 2] * dz; if (d > bv) { bv = d; bi = i; } } keep.add(bi); }
  const o = []; for (const i of keep) o.push(P[i], P[i + 1], P[i + 2]); return new Float32Array(o); }
const above = p => p.y > 0.30;
function sampleClips(root, anims, filt, names) { let pts = collect(root, filt); const mx = new THREE.AnimationMixer(root);
  for (const c of anims) { if (names && !names.includes(c.name)) continue; const a = mx.clipAction(c); a.play();
    for (let s = 0; s <= 24; s++) { mx.setTime(c.duration * s / 24); root.updateMatrixWorld(true); pts = pts.concat(collect(root, filt)); } a.stop(); mx.setTime(0); }
  return pts; }
function showTiers(o) { o.traverse(n => { if (/^Tier_\d+/.test(n.name)) { n.visible = true; for (let q = n.parent; q; q = q.parent) q.visible = true; } else if (n.userData && n.userData.hidden_by_default) n.visible = false; }); }
// ---------- scenes
export async function mineScene() {
  const G = {}, MX = 160;
  const g = await load('mine_2123a050.glb'); const o = g.scene; o.position.set(MX, 0, 0); showTiers(o); o.updateMatrixWorld(true);
  const ct = o.getObjectByName('Cam_Target'); const ctW = ct.getWorldPosition(new THREE.Vector3());
  const mAbove = p => p.y > 0.30 && !(p.x - MX > 17 && p.y < 0.5);   // + the haul-road edge berms (0.31-0.45 m, x > 17) that run off the right edge with the road
  G.mine = reduce(sampleClips(o, g.animations, mAbove));
  const mainOnly = []; o.traverse(n => { if (/^Tier_\d+/.test(n.name)) n.visible = false; }); mainOnly.push(...collect(o, mAbove)); G.mine_base = reduce(mainOnly); showTiers(o);
  // deposits: the baked patches + veins inside the game's deposit radius r = max(1.6, radius_m*1.15) around Dep_01 / Dep_02 (any height)
  const deps = ['Dep_01', 'Dep_02'].map(n => { const d = o.getObjectByName(n); const w = d.getWorldPosition(new THREE.Vector3()); return { n, x: w.x, z: w.z, r: Math.max(1.6, (d.userData.radius_m || 1.4) * 1.15) }; });
  const dp = []; for (const nm of ['Base_Paint', 'Base_DepVein', 'Base_GlowCyan']) { const nd = o.getObjectByName(nm); if (nd) dp.push(...collect(nd, p => deps.some(d => Math.hypot(p.x - d.x, p.z - d.z) <= d.r))); }
  G.deposits = reduce(dp);
  // operator at Operator_Deck, every clip
  const og = await load('mine_operator_9209246.glb'); const od = o.getObjectByName('Operator_Deck'); og.scene.position.set(MX + od.position.x, 0, od.position.z);
  G.operator = reduce(sampleClips(og.scene, og.animations, null));
  // HT-04: local hull over drive / chute_pour / truck_load_rich (+ rest) x fill morph {0, .5, .75, 1}; truck_dump only plays at the Refinery
  const tg = await load('ht04_c0452bd.glb'); const tr = tg.scene, tk = tr.getObjectByName('Truck'); const fm = []; tr.traverse(m => { if (m.morphTargetDictionary && 'fill' in m.morphTargetDictionary) fm.push([m, m.morphTargetDictionary.fill]); });
  let tl = []; for (const inf of [0, .5, .75, 1]) { for (const [m, i] of fm) m.morphTargetInfluences[i] = inf; tl = tl.concat(sampleClips(tr, tg.animations, null, ['truck_drive', 'chute_pour', 'truck_load_rich'])); }
  const TL = reduce(tl, 1500); G._truckLocal = TL;
  const R = JSON.parse(fs.readFileSync(new URL('./route.json', import.meta.url))); const full = [], lane = [];
  for (const [el, ph, x, z, yaw] of R.poses) { if (x >= 274) continue; const c = Math.cos(yaw), s = Math.sin(yaw);
    const dst = (ph === 'fill' || ph === 'revMine' || x < MX + 12.5) ? full : lane;
    for (let i = 0; i < TL.length; i += 3) dst.push(x + TL[i] * c + TL[i + 2] * s, TL[i + 1], z - TL[i] * s + TL[i + 2] * c); }
  // parked pose (fill at Path_Load) too
  { const p = R.parked; const c = Math.cos(p.yaw), s = Math.sin(p.yaw); for (let i = 0; i < TL.length; i += 3) full.push(p.x + TL[i] * c + TL[i + 2] * s, TL[i + 1], p.z - TL[i] * s + TL[i + 2] * c); }
  G.truck = reduce(full); G.truck_lane = reduce(lane);   // truck_lane: straight lanes, it drives in/out across the right edge -> top/bottom only
  return { G, ctW, fw: ct.userData.frame_w, ox: MX, yOnly: ['truck_lane'], sizeKey: 'mine' };
}
export async function lsScene() { const G = {};
  const g = await load('life_support_adfaac9.glb'); const o = g.scene; o.position.set(0, 0, 0); showTiers(o); o.updateMatrixWorld(true);
  const ct = o.getObjectByName('Cam_Target'); const ctW = ct.getWorldPosition(new THREE.Vector3());
  G.lifesupport = reduce(sampleClips(o, g.animations, above));
  o.traverse(n => { if (/^Tier_\d+/.test(n.name)) n.visible = false; }); G.ls_base = reduce(collect(o, above));
  return { G, ctW, fw: ct.userData.frame_w, ox: 0, yOnly: [], sizeKey: 'lifesupport' }; }
export async function dockScene() { const G = {};
  const g = await load('dock_tankfarm_fd286b9.glb'); const o = g.scene; o.position.set(640, 0, 0); showTiers(o); o.updateMatrixWorld(true);
  const ct = o.getObjectByName('Cam_Target'); const ctW = ct.getWorldPosition(new THREE.Vector3());
  G.dock = reduce(sampleClips(o, g.animations, above));
  const mx = new THREE.AnimationMixer(o); const shut = []; for (const c of g.animations) if (c.name !== 'dock_door_open') { const a = mx.clipAction(c); a.play(); for (let s = 0; s <= 24; s++) { mx.setTime(c.duration * s / 24); shut.push(...collect(o, above)); } a.stop(); mx.setTime(0); }
  G.dock_door_shut = reduce(shut);
  return { G, ctW, fw: ct.userData.frame_w, ox: 640, yOnly: [], sizeKey: 'dock' }; }
// ---------- camera + measure
export function cam(s, T, fw) { const a = s.w / s.h, d = (fw / 2) / (TAN * a); return { C: [T.x, T.y + d * SE, T.z + d * CE], d, f: (s.h / 2) / TAN }; }
export function bbox(P, s, T, fw, yOnly) { const { C, f } = cam(s, T, fw); let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
  for (let i = 0; i < P.length; i += 3) { const rx = P[i] - C[0], ry = P[i + 1] - C[1], rz = P[i + 2] - C[2];
    const zc = -(ry * SE + rz * CE), yc = ry * CE - rz * SE; const X = s.w / 2 + f * rx / zc, Y = s.h / 2 - f * yc / zc;
    if (X < x0) x0 = X; if (X > x1) x1 = X; if (Y < y0) y0 = Y; if (Y > y1) y1 = Y; }
  return { x0, x1, y0, y1 }; }
export function report(S, T, fw, skip = []) { const o = { sizes: {} }; let minAll = 1e9;
  for (const s of SIZES) { const r = { groups: {} }; let mn = { top: 1e9, bottom: 1e9, left: 1e9, right: 1e9 };
    for (const [k, P] of Object.entries(S.G)) { if (k[0] === '_') continue; const b = bbox(P, s, T, fw); const yo = S.yOnly.includes(k);
      const sp = { top: b.y0 - s.top, bottom: s.bot - b.y1, left: yo ? null : b.x0, right: yo ? null : s.w - b.x1 };
      r.groups[k] = { px: [b.x0, b.y0, b.x1, b.y1].map(q => +q.toFixed(1)), spare: Object.fromEntries(Object.entries(sp).map(([a, q]) => [a, q == null ? null : +q.toFixed(2)])), w: +(b.x1 - b.x0).toFixed(1), h: +(b.y1 - b.y0).toFixed(1) };
      if (k.endsWith('_base') || k === 'dock_door_shut' || skip.includes(k)) continue;
      for (const a in sp) if (sp[a] != null) mn[a] = Math.min(mn[a], sp[a]); }
    r.spare = Object.fromEntries(Object.entries(mn).map(([a, q]) => [a, +q.toFixed(2)])); r.min = Math.min(...Object.values(mn)); minAll = Math.min(minAll, r.min);
    r.d = +cam(s, T, fw).d.toFixed(2); o.sizes[s.w + 'x' + s.h] = r; }
  o.min = +minAll.toFixed(2); return o; }
export function minSpare(S, T, fw) { let m = 1e9; for (const s of SIZES) for (const [k, P] of Object.entries(S.G)) { if (k[0] === '_' || k.endsWith('_base') || k === 'dock_door_shut') continue;
  const b = bbox(P, s, T, fw); m = Math.min(m, b.y0 - s.top, s.bot - b.y1); if (!S.yOnly.includes(k)) m = Math.min(m, b.x0, s.w - b.x1); } return m; }
