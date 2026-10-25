// v5: world triangles (visible meshes, Tier_* included and flagged) of the GLBs qa3d-next loads in the 10/24 Coder order d729465
// (Cargo Space Dock 480 | Launch Pad 640 | Shipyard 800) -> <outdir>/tris_<Station>.bin (float32 xyz per vertex, 9 per tri) + tris_meta.json
//   node export_tris_v5.mjs <outdir>
import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
await MeshoptDecoder.ready;
const R = '/workspace/planet-stack/', OUT = process.argv[2];
const crypto = await import('crypto'); const md5 = p => crypto.createHash('md5').update(fs.readFileSync(p)).digest('hex');
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const ST = [['CargoDock', 480, 'qa3d/models/dock_tankfarm_fd286b9.glb'], ['LaunchPad', 640, 'qa3d-next/models/launch_pad_db78a6f7.glb'], ['Shipyard', 800, 'qa3d-next/models/shipyard_bcbd0934.glb']];
const NN = (o, S) => { while (o && o !== S && !o.name.replace(/^mesh_\d+(_\d+)?$/, '')) o = o.parent; return o && o !== S ? o.name : '?'; };
const meta = {};
for (const [n, x0, f] of ST) {
  const g = await load(R + f); const S = g.scene; S.position.set(x0, 0, 0); S.updateMatrixWorld(true);
  const hid = (q) => { for (; q; q = q.parent) if (!q.visible) return true; return false; };
  const arr = [], names = [], triName = []; const v = new THREE.Vector3();
  S.traverse(o => { if (!o.isMesh || hid(o)) return; const nm = NN(o, S); let ni = names.indexOf(nm); if (ni < 0) { names.push(nm); ni = names.length - 1; }
    const p = o.geometry.attributes.position, ix = o.geometry.index; const cnt = ix ? ix.count : p.count;
    for (let k = 0; k < cnt; k++) { const i = ix ? ix.getX(k) : k; v.fromBufferAttribute(p, i); v.applyMatrix4(o.matrixWorld); arr.push(v.x, v.y, v.z); if (k % 3 === 0) triName.push(ni); } });
  fs.writeFileSync(`${OUT}/tris_${n}.bin`, Buffer.from(new Float32Array(arr).buffer)); fs.writeFileSync(`${OUT}/trin_${n}.bin`, Buffer.from(new Uint16Array(triName).buffer));
  meta[n] = { x0, file: f, md5: md5(R + f), tris: arr.length / 9, names };
  console.log(n, x0, meta[n].md5.slice(0, 8), 'tris', arr.length / 9, 'nodes', names.length);
}
fs.writeFileSync(`${OUT}/tris_meta.json`, JSON.stringify(meta));
