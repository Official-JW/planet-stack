// Transport-road clearance check on REAL vertices (read only): launch_pad_game.glb (82131aba, Lv1 + every tier shown) and
// shipyard_bcbd0934.glb, against the ST-10 transporter swept volume on the proposed straight road (pad-local z = -13, heading -X in / +X out).
// Transporter frame: ship axis at the pick-up spot (0, -13); body x -13.4..+15.7 rel, track/deck bands 9.7 <= |dz| <= 13.7 (A) / 14.2 (B).
// Sweep = everything the body passes on its way in from the road (rel x >= -13.4). Members: bands = ground to top (A 32.5 m / B 25.2 m);
// the gap |dz| < 9.7 only meets the cross member (A: bottom 4.2 m at rel x >= 11; B: portal beam bottom 11.3 m at rel x >= 12.5).
// usage: node road_clearance.mjs out.json
import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
await MeshoptDecoder.ready;
const R = '/workspace/planet-stack/';
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(R + p); new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const C = { A: { x0: -13.4, half: 13.7, cx: 11.0, cy: 4.2 }, B: { x0: -12.6, half: 14.2, cx: 12.5, cy: 11.3 } };
const NN = (o, S) => { while (o && o !== S && !o.name.replace(/^mesh_\d+(_\d+)?$/, '')) o = o.parent; return o && o !== S ? o.name : '?'; };
const out = { pad: {}, road: {} };
const pad = await load('art/3d/buildings/launch_pad/launch_pad_game.glb'); const S = pad.scene;
S.traverse(n => { n.visible = true; }); S.updateMatrixWorld(true);
const v = new THREE.Vector3();
for (const k of ['A', 'B']) {
  const c = C[k]; const hits = {};
  S.traverse(o => { if (!o.isMesh) return; const nm = NN(o, S); if (nm === 'Ship_Placeholder' || nm === 'Cargo_Door') return;
    const p = o.geometry.attributes.position;
    for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i); v.applyMatrix4(o.matrixWorld); if (v.y < 0.3) continue;
      const rx = v.x, dz = Math.abs(v.z + 13); if (rx < c.x0 || dz > c.half) continue;
      const band = dz >= 9.7; const cross = !band && rx >= c.cx && v.y > c.cy - 0.2;
      if (!band && !cross) continue;
      const key = nm + ' @ ' + (Math.floor(rx / 4) * 4) + ',' + (Math.floor(v.z / 4) * 4);
      const h = hits[key] || (hits[key] = { node: nm, x0: 1e9, x1: -1e9, z0: 1e9, z1: -1e9, ymax: 0, n: 0, where: band ? 'track/deck band' : 'cross member' });
      h.x0 = Math.min(h.x0, v.x); h.x1 = Math.max(h.x1, v.x); h.z0 = Math.min(h.z0, v.z); h.z1 = Math.max(h.z1, v.z); h.ymax = Math.max(h.ymax, v.y); h.n++; } });
  // merge cells into clusters (touching boxes, same node)
  const L = Object.values(hits); let merged = true;
  while (merged) { merged = false;
    for (let i = 0; i < L.length && !merged; i++) for (let j = i + 1; j < L.length && !merged; j++) { const a = L[i], b = L[j];
      if (a.node === b.node && a.x0 <= b.x1 + 1.0 && b.x0 <= a.x1 + 1.0 && a.z0 <= b.z1 + 1.0 && b.z0 <= a.z1 + 1.0) {
        Object.assign(a, { x0: Math.min(a.x0, b.x0), x1: Math.max(a.x1, b.x1), z0: Math.min(a.z0, b.z0), z1: Math.max(a.z1, b.z1), ymax: Math.max(a.ymax, b.ymax), n: a.n + b.n, where: a.where === b.where ? a.where : 'band + cross' }); L.splice(j, 1); merged = true; } } }
  out.pad[k] = L.map(h => ({ ...h, x0: +h.x0.toFixed(1), x1: +h.x1.toFixed(1), z0: +h.z0.toFixed(1), z1: +h.z1.toFixed(1), ymax: +h.ymax.toFixed(2) })).sort((a, b) => a.x0 - b.x0);
}
// shipyard: anything inside the road corridor between the pad gate and the transfer apron end (pad-local x 29.5 .. 112, z -31 .. +5)
const sy = await load('qa3d-next/models/shipyard_bcbd0934.glb'); const T = sy.scene; T.traverse(n => { n.visible = true; }); T.updateMatrixWorld(true);
let syHits = { n: 0, x0: 1e9 };
T.traverse(o => { if (!o.isMesh) return; const p = o.geometry.attributes.position;
  for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i); v.applyMatrix4(o.matrixWorld); const px = v.x + 160; if (v.y < 0.3) continue;
    if (px <= 112 && v.z >= -33.6 && v.z <= 7.6) { syHits.n++; syHits.x0 = Math.min(syHits.x0, px); } } });
out.shipyard_in_corridor = syHits;
fs.writeFileSync(process.argv[2] || 'road_clearance.json', JSON.stringify(out, null, 1));
for (const k of ['A', 'B']) { console.log('PAD vs', k); for (const h of out.pad[k]) console.log(' ', h.node, h.where, 'x', h.x0, h.x1, 'z', h.z0, h.z1, 'ymax', h.ymax, 'n', h.n); }
console.log('shipyard verts in corridor/apron (pad-local x<=112):', JSON.stringify(syHits));
