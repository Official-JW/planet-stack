// loads the packed GLB in three.js (meshopt decoder) and prints draws, tris, materials, extensions, clips, skin, markers.
import fs from 'fs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
const f = process.argv[2]; const buf = fs.readFileSync(f);
await MeshoptDecoder.ready;
const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder);
l.parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength), '', (g) => {
  let draws = 0, tris = 0; const mats = new Set(); let skinned = 0, bones = 0;
  g.scene.traverse(o => { if (o.isMesh) { draws++; mats.add(o.material.name); tris += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3;
    if (o.isSkinnedMesh) { skinned++; bones = o.skeleton.bones.length; } } });
  const j = g.parser.json;
  const bad = (j.extensionsUsed || []).filter(e => !['EXT_meshopt_compression', 'KHR_mesh_quantization'].includes(e));
  const out = { bytes: buf.length, draws, tris, skinned, bones, materials: [...mats].sort(), ext: j.extensionsUsed, banned_ext: bad, images: (j.images || []).length,
    clips: g.animations.map(a => [a.name, +a.duration.toFixed(3), a.tracks.length]), head: !!g.scene.getObjectByName('Op_Head') };
  console.log(JSON.stringify(out));
  if (bad.length || out.images || draws > 2 || tris > 3000) { console.error('BUDGET FAIL'); process.exit(1); }
}, e => { console.error('LOAD FAILED', e); process.exit(1); });
