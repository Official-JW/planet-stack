import fs from 'fs'; import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { bbox, SIZES } from './ovr.mjs';
await MeshoptDecoder.ready;
const b = fs.readFileSync('/workspace/planet-stack/qa3d/models/life_support_adfaac9.glb'); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder);
const g = await new Promise((r, j) => l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', r, j));
const o = g.scene; o.traverse(n => { if (/^Tier_/.test(n.name)) n.visible = true; }); o.updateMatrixWorld(true); const v = new THREE.Vector3(); const P = [];
o.traverse(m => { if (!m.isMesh) return; const p = m.geometry.attributes.position; for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i).applyMatrix4(m.matrixWorld); P.push(v.x, v.y, v.z); } });
const sp = (T, fw) => SIZES.map(s => { const q = bbox(P, s, T, fw); return [s.w, +(q.y0 - s.top).toFixed(2), +(s.bot - q.y1).toFixed(2)]; });
console.log('apron incl, new', JSON.stringify(sp({ x: 0, y: -3.19, z: -12.5 }, 46.8)), 'cur', JSON.stringify(sp({ x: 0, y: -3.1, z: -12.5 }, 46)));
// best with apron included, target 9
const vm = (T, fw) => Math.min(...sp(T, fw).flatMap(a => [a[1], a[2]]));
const bestY = fw => { let lo = -20, hi = 15; for (let i = 0; i < 60; i++) { const a = lo + (hi - lo) / 3, c = hi - (hi - lo) / 3; if (vm({ x: 0, y: a, z: -12.5 }, fw) < vm({ x: 0, y: c, z: -12.5 }, fw)) lo = a; else hi = c; } return (lo + hi) / 2; };
let lo = 40, hi = 70; for (let i = 0; i < 40; i++) { const m = (lo + hi) / 2; if (vm({ x: 0, y: bestY(m), z: -12.5 }, m) >= 9) hi = m; else lo = m; }
const fw = Math.ceil(hi * 10) / 10, y = Math.round(bestY(fw) * 100) / 100; console.log('apron-in variant', y, fw, JSON.stringify(sp({ x: 0, y, z: -12.5 }, fw)));
// apron extent (z) of ground verts
let zmax = -1e9; for (let i = 0; i < P.length; i += 3) if (P[i + 1] <= .3) zmax = Math.max(zmax, P[i + 2]); console.log('ground zmax', zmax);
