// three r186 verifier for crew_boarding.glb: loads with GLTFLoader + MeshoptDecoder, lists clips, draws, tris, extensions,
// then plays crew_call -> crew_walk_to_pad -> crew_climb back to back at 30 fps and measures contact slip against the build's reference.
// NODE_PATH=/home/box/apps/gltftools/node_modules node verify_boarding.mjs crew_boarding.glb ref.json(optional)
import fs from 'fs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
const [, , file, refFile] = process.argv;
const buf = fs.readFileSync(file);
const jl = buf.readUInt32LE(12); const J = JSON.parse(buf.slice(20, 20 + jl).toString());
const loader = new GLTFLoader(); loader.setMeshoptDecoder(MeshoptDecoder);
await MeshoptDecoder.ready;
const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
const gltf = await new Promise((res, rej) => loader.parse(ab, '', res, rej));
const out = { file, bytes: buf.length, three: THREE.REVISION, extensionsUsed: J.extensionsUsed || [], images: (J.images || []).length, textures: (J.textures || []).length };
out.forbidden = (J.extensionsUsed || []).filter(e => /draco|transmission|clearcoat|ior|texture/i.test(e));
let draws = 0, tris = 0; const mats = new Set();
gltf.scene.traverse(o => { if (o.isMesh) { draws++; tris += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3; mats.add(o.material.name); } });
out.draws = draws; out.tris = tris; out.materials = [...mats];
out.clips = gltf.animations.map(a => ({ name: a.name, duration: +a.duration.toFixed(3), tracks: a.tracks.length }));
// play back to back
const mixer = new THREE.AnimationMixer(gltf.scene);
const order = ['crew_call', 'crew_walk_to_pad', 'crew_climb'];
const clips = order.map(n => gltf.animations.find(a => a.name === n));
let ref = null;
if (refFile) ref = JSON.parse(fs.readFileSync(refFile));
const names = ['Foot_L', 'Foot_R', 'Hand_L', 'Hand_R'];
const bones = [1, 2, 3, 4].map(k => names.map(n => gltf.scene.getObjectByName(`C${k}_${n}`)));
const roots = [1, 2, 3, 4].map(k => gltf.scene.getObjectByName(`C${k}_Root`));
const fps = 30; let gf = 0; const v = new THREE.Vector3();
const where = {}; const slides = [];
const err = { foot_max_err_vs_ref_m: 0, hand_max_err_vs_ref_m: 0, planted_foot_slide_max_m: 0, gripping_hand_slip_max_m: 0 };
let prev = null;
for (const clip of clips) {
  const act = mixer.clipAction(clip); mixer.stopAllAction(); act.reset(); act.setLoop(THREE.LoopOnce); act.clampWhenFinished = true; act.play();
  const nf = Math.round(clip.duration * fps);
  for (let f = (gf === 0 ? 0 : 1); f <= nf; f++) {
    mixer.setTime(f / fps); gltf.scene.updateMatrixWorld(true);
    const cur = bones.map(bs => bs.map(b => b.getWorldPosition(v).toArray()));
    if (ref && gf < ref.P.length) {
      for (let c = 0; c < 4; c++) for (let k = 0; k < 4; k++) {
        if (roots[c].scale.x < 0.5) continue;
        const r = ref.P[gf][c][k]; const d = Math.hypot(cur[c][k][0] - r[0], cur[c][k][1] - r[1], cur[c][k][2] - r[2]);
        const key = k < 2 ? 'foot_max_err_vs_ref_m' : 'hand_max_err_vs_ref_m'; if (d > err[key]) { err[key] = d; where[key] = { t: +(gf / fps).toFixed(2), crew: c + 1, limb: names[k] }; }
        if (prev && ref.planted[gf][c][k]) {
          const p = prev[c][k]; const s = Math.hypot(cur[c][k][0] - p[0], cur[c][k][1] - p[1], cur[c][k][2] - p[2]);
          const key2 = k < 2 ? 'planted_foot_slide_max_m' : 'gripping_hand_slip_max_m'; if (k < 2) slides.push(s); if (s > err[key2]) { err[key2] = s; where[key2] = { t: +(gf / fps).toFixed(2), crew: c + 1, limb: names[k] }; }
        }
      }
    }
    prev = cur; gf++;
  }
}
slides.sort((a, b) => a - b); const q = p => +(slides[Math.floor(p * (slides.length - 1))] || 0).toFixed(4);
out.planted_foot_slide_percentiles_m = { p50: q(0.5), p95: q(0.95), p99: q(0.99), max: q(1), n_frames: slides.length, over_5mm: slides.filter(x => x > 0.005).length };
out.frames_played = gf; out.worst_at = where; out.contacts = Object.fromEntries(Object.entries(err).map(([k, x]) => [k, +x.toFixed(4)]));
console.log(JSON.stringify(out, null, 1));
