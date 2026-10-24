// Height trigger for the boarding camera: samples a bone's world Y (three r186, GLB as shipped) at 30 Hz through crew_climb and
// reports the first time it reaches the threshold, clip-local and absolute (crew_call + crew_walk_to_pad + local).
// usage: NODE_PATH=/home/box/apps/gltftools/node_modules node focus_trigger.mjs crew_boarding.glb [Y=14] [bones=C1_Hips,C1_Head]
import fs from 'fs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
const [, , file, yArg, bArg] = process.argv; const Y = yArg ? +yArg : 14; const bones = (bArg || 'C1_Hips,C1_Head').split(',');
const buf = fs.readFileSync(file); const loader = new GLTFLoader(); loader.setMeshoptDecoder(MeshoptDecoder); await MeshoptDecoder.ready;
const gltf = await new Promise((res, rej) => loader.parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength), '', res, rej));
const clip = n => gltf.animations.find(a => a.name === n); const climb = clip('crew_climb');
const off = clip('crew_call').duration + clip('crew_walk_to_pad').duration;
const mixer = new THREE.AnimationMixer(gltf.scene); const act = mixer.clipAction(climb); act.play();
const out = { threshold_y_m: Y, clip: 'crew_climb', clip_offset_s: +off.toFixed(4), clip_duration_s: +climb.duration.toFixed(4), bones: {} };
const v = new THREE.Vector3();
for (const bn of bones) {
  const b = gltf.scene.getObjectByName(bn); if (!b) { out.bones[bn] = null; continue; }
  let prev = null, hit = null;
  for (let i = 0; i <= Math.round(climb.duration * 30); i++) {
    const t = Math.min(i / 30, climb.duration); mixer.setTime(t); gltf.scene.updateMatrixWorld(true); b.getWorldPosition(v);
    if (hit === null && v.y >= Y) { const a = prev ? prev.t + (t - prev.t) * (Y - prev.y) / (v.y - prev.y) : t; hit = { first_frame_s: +t.toFixed(4), interp_s: +a.toFixed(3) }; }
    prev = { t, y: v.y };
  }
  out.bones[bn] = hit ? { clip_local_s: hit.interp_s, absolute_s: +(hit.interp_s + off).toFixed(3), first_30hz_frame_clip_local_s: hit.first_frame_s } : 'never';
}
console.log(JSON.stringify(out, null, 1));
