// Game-camera occlusion check (Refinery station camera = QA3D fitSite: Cam_Target + frame_w, 38 deg vFOV, 18 deg down, at 393x852 and 375x667).
// Loads the current Refinery GLB (+320, tiers hidden), the crane at world (CRANE_X, 0, 17.5), FB-05 at (318, 0, 13), 6 pallet boxes and the receiver (316.5, 0, 17.1),
// poses the crane by the solve onto Bed_Slot_01 / Bed_Slot_02 (slot 01 already loaded for slot 02), bakes all meshes (skinned too) into one BVH and
// raycasts 3x3 per pixel over the landing box: share of the box hidden, by part; plus share of the FB-05 cab / truck hidden.
// Also reports the screen bbox of the concrete pad / loaded pallet / FB-05 / landing box against the safe band (393x852: y 165-534, 375x667: y 144-383).
// usage: node gamecam_occlusion.mjs CRANE.glb CRANE_X   (needs 'three' r186 + 'three-mesh-bvh' resolvable, e.g. a dir with node_modules/three -> gltftools three, npm i three-mesh-bvh)
import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules';
import * as THREE from 'three';
import { MeshBVH } from 'three-mesh-bvh';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
await MeshoptDecoder.ready;
const R = '/workspace/planet-stack/art/3d/';
const A = process.argv.slice(2); const CRANE = A[0], CX = +A[1], CZ = 17.5;
const load = f => new Promise((res, rej) => { const b = fs.readFileSync(f); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const scene = new THREE.Scene();
const tag = (o, t) => o.traverse(n => n.userData.grp = t);
const ref = (await load(R + 'buildings/refinery/refinery_game.glb')).scene; ref.position.set(320, 0, 0);
let ct = null; ref.traverse(n => { if (n.name === 'Cam_Target') ct = n; if (/^Tier_\d+/.test(n.name) || (n.userData && n.userData.hidden_by_default)) n.visible = false; });
tag(ref, 'refinery'); scene.add(ref);
const crane = (await load(CRANE)).scene; crane.position.set(CX, 0, CZ); tag(crane, 'crane'); scene.add(crane);
const fb = (await load(R + 'props/fb05/fb05_game.glb')).scene; fb.position.set(318, 0, 13); tag(fb, 'fb05'); scene.add(fb);
const rx = (await load(R + 'crew/receiver/receiver_game.glb')).scene; rx.position.set(316.5, 0, 17.1); rx.rotation.y = Math.PI; tag(rx, 'receiver'); scene.add(rx);
const boxG = await load(R + 'props/cargo_box/cargo_box_game.glb');
scene.updateMatrixWorld(true);
const W_ = n => { const o = scene.getObjectByName(n); return o.getWorldPosition(new THREE.Vector3()); };
const addBox = (p, t) => { const b = boxG.scene.clone(true); b.position.copy(p); tag(b, t); scene.add(b); b.updateMatrixWorld(true); return b; };
const s1 = W_('Bed_Slot_01'), s2 = W_('Bed_Slot_02');
const croot = crane.getObjectByName('Crane_Refinery'), e = croot.userData;
const slew = crane.getObjectByName('Slew'), tro = crane.getObjectByName('Trolley'), hoi = crane.getObjectByName('Hoist'), hook = crane.getObjectByName('Hook'); const hook0 = hook.position.y;
const pal = []; for (let i = 1; i <= 6; i++) pal.push(addBox(W_('Pallet_Slot_0' + i), 'pallet_box'));
const MIR = croot.userData.jib_side || 1;
function aimWorld(P) { const L0 = crane.worldToLocal(P.clone()); const H = L0.clone(); H.y += 1.5;
  const th = Math.atan2(-H.z, H.x), r = Math.hypot(H.x, H.z), L = e.sheave_y - H.y - e.hook_drop_m;
  slew.rotation.y = th; tro.position.x = r; hoi.scale.y = L; hook.position.y = hook0 + 1 - L; hook.rotation.y = -th; scene.updateMatrixWorld(true);
  scene.traverse(n => { if (n.isSkinnedMesh) { n.boundingSphere = null; n.boundingBox = null; } });
  return { th: +th.toFixed(3), r: +r.toFixed(3), L: +L.toFixed(3), ok: r >= e.trolley_min_m && r <= e.trolley_max_m && L >= e.hoist_min_m && L <= e.hoist_max_m }; }
const out = {};
for (const [Wd, Hd] of [[393, 852], [375, 667]]) {
  const asp = Wd / Hd, cam = new THREE.PerspectiveCamera(38, asp, 0.5, 3000);
  const T = ct.getWorldPosition(new THREE.Vector3()), fw = ct.userData.frame_w;
  const d = (fw / 2) / (Math.tan(THREE.MathUtils.degToRad(19)) * asp), el = THREE.MathUtils.degToRad(18);
  cam.position.set(T.x, T.y + d * Math.sin(el), T.z + d * Math.cos(el)); cam.lookAt(T); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
  const BAND = Wd === 393 ? [165, 534] : [144, 383];
  const sbox = pts => { let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9; for (const p of pts) { const v = p.clone().project(cam); const px = (v.x + 1) / 2 * Wd, py = (1 - v.y) / 2 * Hd; x0 = Math.min(x0, px); x1 = Math.max(x1, px); y0 = Math.min(y0, py); y1 = Math.max(y1, py); }
    const r = [x0, y0, x1, y1].map(v => +v.toFixed(0)); return { px_bbox: r, in_band: y0 >= BAND[0] && y1 <= BAND[1], over_band_bottom_px: Math.max(0, +(y1 - BAND[1]).toFixed(0)) }; };
  const corners = (b) => { const o = []; for (const x of [b.min.x, b.max.x]) for (const y of [b.min.y, b.max.y]) for (const z of [b.min.z, b.max.z]) o.push(new THREE.Vector3(x, y, z)); return o; };
  const pad = e.concrete_pad ? corners(new THREE.Box3(new THREE.Vector3(...e.concrete_pad.min), new THREE.Vector3(...e.concrete_pad.max))).map(v => crane.localToWorld(v)) : [];
  const palB = new THREE.Box3(); for (const b of pal) palB.expandByObject(b);
  out[`${Wd}x${Hd} band`] = { band_y: BAND, concrete_pad: pad.length ? sbox(pad) : null, pallet_boxes: sbox(corners(palB)), fb05: sbox(corners(new THREE.Box3().setFromObject(fb))),
    landing_box_slot01: sbox(corners(new THREE.Box3(s1.clone().add(new THREE.Vector3(-1.2, 0, -0.7)), s1.clone().add(new THREE.Vector3(1.2, 1.5, 0.7))))) };
  for (const slot of [1, 2]) {
    const P = slot === 1 ? s1 : s2;
    const extra = slot === 2 ? [addBox(s1, 'bed_box_01')] : [];
    const tgt = addBox(P, 'TARGET'); const sol = aimWorld(P);
    // screen bbox of the target box
    const bb = new THREE.Box3().setFromObject(tgt); let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    for (const x of [bb.min.x, bb.max.x]) for (const y of [bb.min.y, bb.max.y]) for (const z of [bb.min.z, bb.max.z]) { const v = new THREE.Vector3(x, y, z).project(cam); const px = (v.x + 1) / 2 * Wd, py = (1 - v.y) / 2 * Hd; x0 = Math.min(x0, px); x1 = Math.max(x1, px); y0 = Math.min(y0, py); y1 = Math.max(y1, py); }
    // bake every visible mesh (skinned too) to world-space triangles with a group id, BVH it
    const pos = [], gid = [], G = [];
    scene.traverse(n => { if (!n.isMesh) return; for (let q = n; q; q = q.parent) if (!q.visible) return;
      let gi = G.indexOf(n.userData.grp); if (gi < 0) { G.push(n.userData.grp); gi = G.length - 1; }
      const g = n.geometry, ix = g.index, cnt = ix ? ix.count : g.attributes.position.count, v = new THREE.Vector3();
      for (let k = 0; k < cnt; k++) { n.getVertexPosition(ix ? ix.getX(k) : k, v); v.applyMatrix4(n.matrixWorld); pos.push(v.x, v.y, v.z); if (k % 3 === 0) gid.push(gi); } });
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    const bvh = new MeshBVH(geo, { indirect: true }); const TG = G.indexOf('TARGET');
    const triOf = h => h.faceIndex;
    const rc = new THREE.Raycaster(); const SS = 3; let tot = 0, vis = 0; const by = {};
    const side = THREE.DoubleSide;
    for (let py = Math.floor(y0); py <= Math.ceil(y1); py++) for (let px = Math.floor(x0); px <= Math.ceil(x1); px++) for (let a = 0; a < SS; a++) for (let b = 0; b < SS; b++) {
      const nx = ((px + (a + .5) / SS) / Wd) * 2 - 1, ny = 1 - ((py + (b + .5) / SS) / Hd) * 2;
      rc.setFromCamera(new THREE.Vector2(nx, ny), cam);
      const hs = bvh.raycast(rc.ray, side); if (!hs.length) continue; hs.sort((p, q) => p.distance - q.distance);
      if (!hs.some(h => gid[h.faceIndex] === TG)) continue;
      tot++; const h = hs[0];
      if (gid[h.faceIndex] === TG) { vis++; continue; }
      let g = G[gid[h.faceIndex]];
      if (g === 'crane') { const lp = crane.worldToLocal(h.point.clone()); const rr = Math.hypot(lp.x, lp.z);
        g = (lp.y > 2.35 && lp.y < 10.1 && rr < 1.0) ? 'crane_mast' : (lp.y >= 9.0 && rr >= 1.0) ? 'crane_jib/cab/head' : (lp.y > 1.8 && lp.y <= 2.35 && rr < 1.0) ? 'crane_turntable' : (lp.y < 1.8 && rr < 2.2) ? 'crane_pedestal' : 'crane_hook/cable/spreader'; }
      by[g] = (by[g] || 0) + 1; }
    // FB-05 cab (truck-local x > 0.9) and whole truck: share of their pixels hidden, by group
    const FB = G.indexOf('fb05'); const tb = new THREE.Box3().setFromObject(fb); let X0 = 1e9, X1 = -1e9, Y0 = 1e9, Y1 = -1e9;
    for (const x of [tb.min.x, tb.max.x]) for (const y of [tb.min.y, tb.max.y]) for (const z of [tb.min.z, tb.max.z]) { const v = new THREE.Vector3(x, y, z).project(cam); X0 = Math.min(X0, (v.x + 1) / 2 * Wd); X1 = Math.max(X1, (v.x + 1) / 2 * Wd); Y0 = Math.min(Y0, (1 - v.y) / 2 * Hd); Y1 = Math.max(Y1, (1 - v.y) / 2 * Hd); }
    const cab = { tot: 0, hid: {} }, truck = { tot: 0, hid: {} };
    for (let py = Math.floor(Y0); py <= Math.ceil(Y1); py++) for (let px = Math.floor(X0); px <= Math.ceil(X1); px++) {
      rc.setFromCamera(new THREE.Vector2(((px + .5) / Wd) * 2 - 1, 1 - ((py + .5) / Hd) * 2), cam);
      const hs = bvh.raycast(rc.ray, side); if (!hs.length) continue; hs.sort((p, q) => p.distance - q.distance);
      const fh = hs.find(h => gid[h.faceIndex] === FB); if (!fh) continue;
      const isCab = fb.worldToLocal(fh.point.clone()).x > 0.9; const g0 = G[gid[hs[0].faceIndex]];
      for (const acc of isCab ? [cab, truck] : [truck]) { acc.tot++; if (g0 !== 'fb05') acc.hid[g0] = (acc.hid[g0] || 0) + 1; } }
    const fmt = a => Object.fromEntries(Object.entries(a.hid).map(([k, v]) => [k, +(100 * v / a.tot).toFixed(1) + '%']));
    const pct = o => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, +(100 * v / tot).toFixed(1) + '%']));
    out[`${Wd}x${Hd} slot0${slot}`] = { box_px_bbox: [x0, y0, x1, y1].map(v => +v.toFixed(0)), box_px_area: +(tot / SS / SS).toFixed(0), hidden: +(100 * (tot - vis) / tot).toFixed(1) + '%', by: pct(by), cab_hidden_by: fmt(cab), truck_hidden_by: fmt(truck), solve: sol };
    scene.remove(tgt); for (const x of extra) scene.remove(x);
  }
}
console.log(JSON.stringify({ crane_x: CX, cam_target: ct.getWorldPosition(new THREE.Vector3()).toArray().map(v => +v.toFixed(2)), frame_w: ct.userData.frame_w, ...out }, null, 1));
