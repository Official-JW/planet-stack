// truck path vs pad: clearance = xz distance from the route centreline (z 23 lane x 592->647, r 4.5 U-turn about (647,27.5), z 32 back to 592) minus 2.8 m road half-width,
// against every visible non-road pad triangle (edges sampled 0.25 m, skinned crane posed at rest, y <= 5 m), plus the Road_UTurn mesh itself vs the same set.
import fs from 'fs'; const NM = process.env.NODE_PATH; const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js'); const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js'); await MeshoptDecoder.ready;
const b = fs.readFileSync(process.argv[2]); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder);
const g = await new Promise((r, j) => l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', r, j)); const S = g.scene; S.updateMatrixWorld(true); const WX = 640;
const owner = o => { let q = o; while (q.parent && q.parent !== S) q = q.parent; return q.name; };
const hid = o => { for (let q = o; q; q = q.parent) if (/^Tier_\d+/.test(q.name) || q.userData?.hidden_by_default) return true; return false; };
const cl = (x, z) => { x -= WX; let d; if (x <= 7) d = Math.min(Math.hypot(Math.max(0, -48 - x), z - 23), Math.hypot(Math.max(0, -48 - x), z - 32)); else d = Math.abs(Math.hypot(x - 7, z - 27.5) - 4.5); if (x <= 7 && x >= -48) d = Math.min(Math.abs(z - 23), Math.abs(z - 32)); return d - 2.8; };
const v = new THREE.Vector3(), w = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()]; let best = { c: 1e9 }; const per = {}; const roadPts = [];
S.traverse(o => { if (!o.isMesh || hid(o)) return; o.isSkinnedMesh && o.skeleton.update(); const a = o.geometry.attributes.position, ix = o.geometry.index; const nm = owner(o);
  const get = (i, out) => { if (o.isSkinnedMesh) o.getVertexPosition(i, out); else out.fromBufferAttribute(a, i); return out.applyMatrix4(o.matrixWorld); };
  for (let t = 0; t < ix.count; t += 3) { for (let q = 0; q < 3; q++) get(ix.getX(t + q), w[q]);
    for (let e = 0; e < 3; e++) { const A = w[e], B = w[(e + 1) % 3]; const n = Math.max(1, Math.ceil(A.distanceTo(B) / 0.25)); for (let s = 0; s <= n; s++) { v.lerpVectors(A, B, s / n); if (v.y > 5) continue;
      if (nm === 'Road_UTurn') { if (s === 0) roadPts.push([v.x + WX, v.z]); continue; } const c = cl(v.x + WX, v.z); if (c < best.c) best = { c: +c.toFixed(3), what: nm, at: [+(v.x + WX).toFixed(2), +v.y.toFixed(2), +v.z.toFixed(2)] }; if (!per[nm] || c < per[nm]) per[nm] = +c.toFixed(3); } } } });
// Road_UTurn mesh vs the non-road set (brute xz grid)
const pad = []; S.traverse(o => { if (!o.isMesh || hid(o) || owner(o) === 'Road_UTurn') return; o.isSkinnedMesh && o.skeleton.update(); const a = o.geometry.attributes.position; for (let i = 0; i < a.count; i++) { if (o.isSkinnedMesh) o.getVertexPosition(i, v); else v.fromBufferAttribute(a, i); v.applyMatrix4(o.matrixWorld); if (v.y <= 5) pad.push([v.x + WX, v.z, owner(o)]); } });
let rb = { d: 1e9 }; const rx = roadPts.map(p => p[0]), rz = roadPts.map(p => p[1]);
for (const p of pad) { if (p[0] < Math.min(...rx.slice(0, 1)) - 1e9) continue; } // no-op
const lo = [Math.min(...rx), Math.min(...rz)], hi = [Math.max(...rx), Math.max(...rz)];
for (const p of pad) { if (p[0] < lo[0] - 15 || p[0] > hi[0] + 15 || p[1] < lo[1] - 15) continue; for (const r of roadPts) { const d = Math.hypot(p[0] - r[0], p[1] - r[1]); if (d < rb.d) rb = { d: +d.toFixed(3), pad: p, road: r.map(x => +x.toFixed(2)) }; } }
const out = { route_minus_halfwidth_min_m: best, per_node_min_m: per, uturn_mesh_bbox_world_xz: [lo.map(x => +x.toFixed(2)), hi.map(x => +x.toFixed(2))], uturn_mesh_to_nearest_pad_vertex_m: rb };
console.log(JSON.stringify(out)); fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 1));
