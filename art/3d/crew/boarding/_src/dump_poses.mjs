// CPU-skins crew_boarding.glb in three r186 at given global times and writes posed vertices for Blender proofs.
// Global timeline: crew_call 0-3 s, crew_walk_to_pad 3-22.3 s, crew_climb 22.3-72.533 s (clips play back to back, each from local 0).
// usage: NODE_PATH=/home/box/apps/gltftools/node_modules node dump_poses.mjs crew_boarding.glb out_prefix t1,t2,... | --every DT [T0 T1]
// writes out_prefix.json {times, nverts, ntris, crew:[visible flags per time]} + out_prefix_pos.bin (float32 T x 4 x V x 3, glTF axes)
// + out_prefix_mesh.bin (uint32 tris, then float32 rgb colours)
import fs from 'fs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
const [, , file, prefix, targ, every, tA, tB] = process.argv;
const buf = fs.readFileSync(file);
const loader = new GLTFLoader(); loader.setMeshoptDecoder(MeshoptDecoder); await MeshoptDecoder.ready;
const gltf = await new Promise((res, rej) => loader.parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength), '', res, rej));
const order = ['crew_call', 'crew_walk_to_pad', 'crew_climb'];
const clips = order.map(n => gltf.animations.find(a => a.name === n));
const starts = [0]; for (const c of clips) starts.push(starts[starts.length - 1] + c.duration);
const T_END = starts[3];
let times;
if (targ === '--every') { const dt = +every, a = tA ? +tA : 0, b = tB ? Math.min(+tB, T_END) : T_END; times = []; for (let i = 0; a + i * dt <= b + 1e-6; i++) times.push(+(a + i * dt).toFixed(4)); }
else times = targ.split(',').map(Number);
const meshes = []; gltf.scene.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
const crewOf = m => m.skeleton.bones.find(b => /^C\d_/.test(b.name)).name.slice(0, 2);
meshes.sort((a, b) => crewOf(a).localeCompare(crewOf(b)));
const roots = [1, 2, 3, 4].map(k => gltf.scene.getObjectByName(`C${k}_Root`));
const g0 = meshes[0].geometry; const V = g0.attributes.position.count;
const idx = g0.index.array; const col = g0.attributes.color;
const mixer = new THREE.AnimationMixer(gltf.scene);
const pos = new Float32Array(times.length * 4 * V * 3); const vis = [];
const v = new THREE.Vector3(), s = new THREE.Vector3();
times.forEach((t, ti) => {
  let ci = 2; for (let i = 0; i < 3; i++) if (t < starts[i + 1] - 1e-9) { ci = i; break; }
  mixer.stopAllAction(); const act = mixer.clipAction(clips[ci]); act.reset(); act.setLoop(THREE.LoopOnce); act.clampWhenFinished = true; act.play();
  mixer.setTime(Math.min(t - starts[ci], clips[ci].duration)); gltf.scene.updateMatrixWorld(true);
  vis.push(roots.map(r => { r.getWorldScale(s); return s.x > 0.01 ? 1 : 0; }));
  meshes.forEach((m, k) => { for (let i = 0; i < V; i++) { m.getVertexPosition(i, v); v.applyMatrix4(m.matrixWorld); pos.set([v.x, v.y, v.z], ((ti * 4 + k) * V + i) * 3); } });
});
fs.writeFileSync(prefix + '_pos.bin', Buffer.from(pos.buffer));
const cols = new Float32Array(V * 3); for (let i = 0; i < V; i++) { cols[i * 3] = col.getX(i); cols[i * 3 + 1] = col.getY(i); cols[i * 3 + 2] = col.getZ(i); }
fs.writeFileSync(prefix + '_mesh.bin', Buffer.concat([Buffer.from(new Uint32Array(idx).buffer), Buffer.from(cols.buffer)]));
const sj = g0.attributes.skinIndex, sw = g0.attributes.skinWeight; const vj = [];
for (let i = 0; i < V; i++) { let bi = 0, bw = -1; for (let c = 0; c < 4; c++) { const w = sw.getComponent(i, c); if (w > bw) { bw = w; bi = sj.getComponent(i, c); } } vj.push(meshes[0].skeleton.bones[bi].name.slice(3)); }
fs.writeFileSync(prefix + '.json', JSON.stringify({ vjoint: vj, times, nverts: V, ntris: idx.length / 3, visible: vis, T_END, mesh_crew: meshes.map(crewOf) }));
console.log('dumped', times.length, 'times', V, 'verts', 'T_END', T_END.toFixed(3));
