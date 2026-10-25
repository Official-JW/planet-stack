// v5 (10/24 Coder order d729465: Cargo Space Dock 480 | Launch Pad 640 | Shipyard 800): world footprints of the GLBs qa3d-next loads,
// 1 m cells with max height (y > 0.12), mesh boxes for road-like meshes, and marker nodes. Light: node, single thread.
//   node measure_stations_v5.mjs out.json
import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
await MeshoptDecoder.ready;
const R = '/workspace/planet-stack/';
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const ST = [['CargoDock', 480, 'qa3d/models/dock_tankfarm_fd286b9.glb'], ['LaunchPad', 640, 'qa3d-next/models/launch_pad_db78a6f7.glb'], ['Shipyard', 800, 'qa3d-next/models/shipyard_bcbd0934.glb']];
const out = {};
for (const [n, x0, f] of ST) {
  const md5 = (await import('crypto')).createHash('md5').update(fs.readFileSync(R + f)).digest('hex');
  const g = await load(R + f); const S = g.scene; S.position.set(x0, 0, 0); S.traverse(o => { if (/^Tier_/.test(o.name)) o.visible = false; }); S.updateMatrixWorld(true);
  const bb = new THREE.Box3(), v = new THREE.Vector3(), grid = {}, roads = [];
  S.traverseVisible(o => { if (!o.isMesh) return; const p = o.geometry.attributes.position; const mb = new THREE.Box3();
    for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i); v.applyMatrix4(o.matrixWorld); bb.expandByPoint(v); mb.expandByPoint(v);
      if (v.y > 0.12) { const k = Math.floor(v.x) + ',' + Math.floor(v.z); grid[k] = Math.max(grid[k] || 0, +v.y.toFixed(2)); } }
    const nm = (o.parent && o.parent.name ? o.parent.name + '/' : '') + o.name;
    if (/road|uturn|apron|path|lane|track/i.test(nm)) roads.push({ name: nm, min: mb.min.toArray().map(a => +a.toFixed(2)), max: mb.max.toArray().map(a => +a.toFixed(2)) }); });
  const nodes = {}; S.traverse(o => { if (!o.isMesh && o.name && o !== S) { const w = o.getWorldPosition(new THREE.Vector3()); if (/door|hall|road|turn|truck|ship|pipe|entry|exit|stop|cam_target|gate/i.test(o.name)) nodes[o.name] = [+w.x.toFixed(3), +w.y.toFixed(3), +w.z.toFixed(3)]; } });
  out[n] = { x0, file: f, md5, all: [bb.min.toArray().map(a => +a.toFixed(2)), bb.max.toArray().map(a => +a.toFixed(2))], nodes, roads, grid };
  console.log(n, x0, md5.slice(0, 8), 'bbox', JSON.stringify(out[n].all), 'cells', Object.keys(grid).length, 'roads', roads.map(r => r.name).join(','));
  console.log('   ', Object.entries(nodes).map(([k, p]) => k + JSON.stringify(p)).join(' '));
}
fs.writeFileSync(process.argv[2] || 'stations_v5.json', JSON.stringify(out));
