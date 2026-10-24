// Station footprints (world XZ) from the live qa3d-next GLBs, placed at x = i*160 (qa3d STATIONS / GAP).
import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
await MeshoptDecoder.ready;
const R = '/workspace/planet-stack/';
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
// v2 layout (cargo_dock/layout_v2, f3478cf): Refinery 320 | Cargo Dock 373 (z -8) | Launch Pad 457 | Habitat placeholder 800 | Shipyard 960.
// x0 is recorded only; the grid stays station-local. Shipyard = art/3d/buildings/shipyard/shipyard_game.glb (c0e9d54e, as used by layout_v2).
const ST = [['Refinery', 320, 'qa3d-next/models/refinery_93c44166.glb'], ['LaunchPad', 457, 'art/3d/buildings/launch_pad/launch_pad_game.glb'],
  ['CargoDock', 373, 'qa3d/models/dock_tankfarm_fd286b9.glb'], ['Shipyard', 960, 'art/3d/buildings/shipyard/shipyard_game.glb']];
const out = {};
for (const [n, x0, f] of ST) {
  const g = await load(R + f); const S = g.scene; S.updateMatrixWorld(true);
  const bb = new THREE.Box3(); const hi = new THREE.Box3(); const v = new THREE.Vector3();
  const grid = {}; // 2m cells with max height
  S.traverse(o => { if (!o.isMesh) return; const p = o.geometry.attributes.position;
    for (let i = 0; i < p.count; i++) { o.getVertexPosition ? o.getVertexPosition(i, v) : v.fromBufferAttribute(p, i); v.applyMatrix4(o.matrixWorld);
      bb.expandByPoint(v); if (v.y > 0.12) { hi.expandByPoint(v); const k = Math.floor(v.x / 2) + ',' + Math.floor(v.z / 2); grid[k] = Math.max(grid[k] || 0, v.y); } } });
  const nodes = {}; S.traverse(o => { if (/door|hall|cam_target|bay|truck_stop|ship|road|uturn|pipe/i.test(o.name) && !o.isMesh) { const w = o.getWorldPosition(new THREE.Vector3()); nodes[o.name] = [+w.x.toFixed(2), +w.y.toFixed(2), +w.z.toFixed(2)]; } });
  out[n] = { x0, all: [bb.min.toArray().map(a => +a.toFixed(2)), bb.max.toArray().map(a => +a.toFixed(2))], above12cm: [hi.min.toArray().map(a => +a.toFixed(2)), hi.max.toArray().map(a => +a.toFixed(2))], extras: S.children[0]?.userData, nodes, grid };
}
fs.writeFileSync(process.argv[2] || 'stations.json', JSON.stringify(out));
for (const k in out) console.log(k, out[k].x0, 'all', JSON.stringify(out[k].all), 'hi', JSON.stringify(out[k].above12cm), Object.keys(out[k].nodes).slice(0, 40).map(n => n + JSON.stringify(out[k].nodes[n])).join(' '));
