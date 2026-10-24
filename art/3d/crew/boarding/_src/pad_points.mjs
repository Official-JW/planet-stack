// Sample the launch pad Ship_Placeholder triangles (plus the analytic ladder rails / rungs) as a 1.5 cm point cloud in the
// pad-local ladder frame (u, t, z), used by build_boarding.py --key-tol to keep keys dense wherever the crew is near the ship.
// usage: node pad_points.mjs launch_pad_game.glb out.f32   (float32 triples)
import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
await MeshoptDecoder.ready;
const [padF, outF] = process.argv.slice(2);
const b = fs.readFileSync(padF); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder);
const pad = (await new Promise((r, j) => l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', r, j))).scene; pad.updateMatrixWorld(true);
const C = pad.getObjectByName('Ship_Center').getWorldPosition(new THREE.Vector3());
const LAD = 330 * Math.PI / 180, LU = [Math.cos(LAD), Math.sin(LAD)], LT = [-LU[1], LU[0]];
const toUTZ = v => { const bx = v.x - C.x, by = -(v.z - C.z); return [bx * LU[0] + by * LU[1], bx * LT[0] + by * LT[1], v.y]; };
const out = []; const H = 0.015; const inReg = p => p[0] > 2.8 && p[0] < 6.4 && Math.abs(p[1]) < 2.6 && p[2] < 24.8;
pad.getObjectByName('Ship_Placeholder').traverse(o => { if (!o.isMesh) return; const pos = o.geometry.attributes.position, idx = o.geometry.index, v = new THREE.Vector3();
  const P = i => toUTZ(v.fromBufferAttribute(pos, i).applyMatrix4(o.matrixWorld));
  const n = idx ? idx.count : pos.count;
  for (let f = 0; f < n; f += 3) { const [A, B, Cc] = [0, 1, 2].map(k => P(idx ? idx.getX(f + k) : f + k)); if (![A, B, Cc].some(inReg)) continue;
    const e1 = Math.hypot(B[0] - A[0], B[1] - A[1], B[2] - A[2]), e2 = Math.hypot(Cc[0] - A[0], Cc[1] - A[1], Cc[2] - A[2]); const na = Math.max(1, Math.ceil(e1 / H)), nb = Math.max(1, Math.ceil(e2 / H));
    for (let i = 0; i <= na; i++) for (let j = 0; j <= nb; j++) { const a = i / na, c = j / nb; if (a + c > 1) continue; const p = [0, 1, 2].map(k => A[k] + (B[k] - A[k]) * a + (Cc[k] - A[k]) * c); if (inReg(p)) out.push(...p); } } });
// analytic ladder (as the gate models it): rails r 0.035 at u 4.45, t +-0.28, z 0.25-21.85; rungs 0.05 box x 0.56 at z 0.65 + 0.6 i
for (const s of [-1, 1]) for (let z = 0.25; z <= 21.85; z += H) for (let a = 0; a < 2 * Math.PI; a += H / 0.035) out.push(4.45 + 0.035 * Math.cos(a), s * 0.28 + 0.035 * Math.sin(a), z);
for (let i = 0; i < 35; i++) { const zc = 0.65 + 0.6 * i; if (zc > 21.6) break; for (let t = -0.28; t <= 0.28; t += H) for (let q = -0.025; q <= 0.025; q += 0.0125) { out.push(4.425, t, zc + q, 4.475, t, zc + q, 4.45 + q, t, zc - 0.025, 4.45 + q, t, zc + 0.025); } }
fs.writeFileSync(outF, Buffer.from(new Float32Array(out).buffer)); console.log('points', out.length / 3);
