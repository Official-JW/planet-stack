// Crew walk-blocker raster (read-only on every GLB). For each placed GLB (world glTF metres, +X right, +Z toward camera, Y up; Lv1 = Tier_* hidden)
// sample every triangle at <= cell/2 spacing and mark a cell BLOCKED when a sample lies in the crew body band [Y0, Y1] (things lower are steps/slabs you
// walk on, things higher are overhead), and HOLE when the cell only has geometry below -HOLE (open pits / docks dug into the ground).
// Writes OUT/<id>.bin (uint8 per cell: 1 band, 2 hole) + OUT/meta.json (grid, y range per cell row-major as float32 pairs in <id>_y.bin, markers).
//   node raster.mjs cfg.json OUTDIR
import fs from 'fs'; import crypto from 'crypto'; import path from 'path';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js'); await MeshoptDecoder.ready;
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const cfg = JSON.parse(fs.readFileSync(process.argv[2])); const OUT = process.argv[3]; fs.mkdirSync(OUT, { recursive: true });
const C = cfg.cell, Y0 = cfg.band[0], Y1 = cfg.band[1], HOLE = cfg.hole, ROOT = path.dirname(path.resolve(process.argv[2]));
const meta = { cell: C, band: cfg.band, hole: HOLE, items: [] };
for (const it of cfg.items) {
  const f = path.resolve(ROOT, it.f); const buf = fs.readFileSync(f); const md5 = crypto.createHash('md5').update(buf).digest('hex');
  const g = await load(f); const S = g.scene; S.position.set(it.x || 0, 0, it.z || 0); S.rotation.y = (it.yaw_deg || 0) * Math.PI / 180; S.updateMatrixWorld(true);
  S.traverse(o => { if (o.isSkinnedMesh) o.skeleton.update(); });
  const hideRe = it.hide ? new RegExp(it.hide) : null;
  const onlyRe = it.only ? new RegExp(it.only) : null;
  const hidden = o => { if (onlyRe) { let ok = false; for (let q = o; q; q = q.parent) if (onlyRe.test(q.name)) ok = true; if (!ok) return true; } for (let q = o; q; q = q.parent) { if (hideRe && hideRe.test(q.name)) return true; if (q.userData && q.userData.hidden_by_default) return true; if (q.visible === false) return true; } return false; };
  const bb = new THREE.Box3(); const tris = [];
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  S.traverse(o => { if (!o.isMesh || hidden(o)) return; const gm = o.geometry, P = gm.attributes.position, I = gm.index; const n = I ? I.count : P.count;
    const gv = (vv, ii) => (o.isSkinnedMesh ? o.getVertexPosition(ii, vv) : vv.fromBufferAttribute(P, ii)).applyMatrix4(o.matrixWorld);
    for (let t = 0; t < n; t += 3) { gv(a, I ? I.getX(t) : t); gv(b, I ? I.getX(t + 1) : t + 1); gv(c, I ? I.getX(t + 2) : t + 2);
      bb.expandByPoint(a); bb.expandByPoint(b); bb.expandByPoint(c); tris.push(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z); } });
  const X0 = Math.floor(bb.min.x) - 2, Z0 = Math.floor(bb.min.z) - 2, NX = Math.ceil((bb.max.x + 2 - X0) / C), NZ = Math.ceil((bb.max.z + 2 - Z0) / C);
  const HI = new Float32Array(NX * NZ).fill(-1e9), LO = new Float32Array(NX * NZ).fill(1e9), BAND = new Uint8Array(NX * NZ);
  for (let t = 0; t < tris.length; t += 9) {
    const ax = tris[t], ay = tris[t + 1], az = tris[t + 2], bx = tris[t + 3], by = tris[t + 4], bz = tris[t + 5], cx = tris[t + 6], cy = tris[t + 7], cz = tris[t + 8];
    const e = Math.max(Math.hypot(bx - ax, by - ay, bz - az), Math.hypot(cx - bx, cy - by, cz - bz), Math.hypot(ax - cx, ay - cy, az - cz)); const s = Math.max(1, Math.ceil(e / (C * 0.5)));
    for (let i = 0; i <= s; i++) for (let j = 0; j <= s - i; j++) { const u = i / s, v = j / s, w = 1 - u - v;
      const x = ax * w + bx * u + cx * v, y = ay * w + by * u + cy * v, z = az * w + bz * u + cz * v;
      const qx = Math.floor((x - X0) / C), qz = Math.floor((z - Z0) / C); if (qx < 0 || qz < 0 || qx >= NX || qz >= NZ) continue; const q = qz * NX + qx;
      if (y > HI[q]) HI[q] = y; if (y < LO[q]) LO[q] = y; if (y >= Y0 && y <= Y1) BAND[q] = 1; } }
  const OUTG = new Uint8Array(NX * NZ); for (let q = 0; q < NX * NZ; q++) OUTG[q] = BAND[q] ? 1 : (HI[q] > -1e8 && HI[q] < -HOLE ? 2 : 0);
  fs.writeFileSync(path.join(OUT, it.id + '.bin'), Buffer.from(OUTG.buffer)); fs.writeFileSync(path.join(OUT, it.id + '_y.bin'), Buffer.concat([Buffer.from(LO.buffer), Buffer.from(HI.buffer)]));
  const markers = {}; if (it.markers) { const re = new RegExp(it.markers); S.traverse(o => { if (o.name && re.test(o.name) && !o.isMesh) { const p = o.getWorldPosition(new THREE.Vector3()); const q = o.getWorldQuaternion(new THREE.Quaternion()); const e = new THREE.Euler().setFromQuaternion(q, 'YXZ'); markers[o.name] = [+p.x.toFixed(3), +p.y.toFixed(3), +p.z.toFixed(3), +(typeof o.userData.yaw_deg === 'number' ? o.userData.yaw_deg : e.y * 180 / Math.PI).toFixed(2)]; } }); }
  meta.items.push({ ...it, file: it.f, md5, X0, Z0, NX, NZ, bb: [bb.min.toArray(), bb.max.toArray()].map(p => p.map(v => +v.toFixed(3))), tris: tris.length / 9, markers });
  console.log(it.id, md5.slice(0, 8), 'grid', NX, NZ, 'tris', tris.length / 9, 'band cells', BAND.reduce((s, v) => s + v, 0), 'holes', OUTG.reduce((s, v) => s + (v === 2), 0));
}
fs.writeFileSync(path.join(OUT, 'meta.json'), JSON.stringify(meta, null, 1));
