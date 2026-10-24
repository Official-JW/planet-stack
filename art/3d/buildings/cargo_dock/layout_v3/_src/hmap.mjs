// top-down max-height raster (0.5 m) of station GLBs placed in world; also per-GLB bbox + marker nodes
import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
await MeshoptDecoder.ready;
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const cfg = JSON.parse(fs.readFileSync(process.argv[2]));
const C = cfg.cell, X0 = cfg.x0, Z0 = cfg.z0, NX = Math.round((cfg.x1 - X0) / C), NZ = Math.round((cfg.z1 - Z0) / C);
const H = new Float32Array(NX * NZ).fill(-1), ID = new Int16Array(NX * NZ).fill(-1);
const info = [];
for (const [k, it] of cfg.items.entries()) {
  const g = await load(it.f); const S = g.scene; S.position.set(it.x || 0, 0, it.z || 0); S.updateMatrixWorld(true); S.traverse(o => { if (o.isSkinnedMesh) o.skeleton.update(); });
  const hideRe = it.hide ? new RegExp(it.hide) : null;
  const hidden = o => { for (let q = o; q; q = q.parent) if (hideRe && hideRe.test(q.name)) return true; return false; };
  const bb = new THREE.Box3(), hb = new THREE.Box3(); const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  S.traverse(o => { if (!o.isMesh || hidden(o)) return; const gm = o.geometry, P = gm.attributes.position, I = gm.index; const n = I ? I.count : P.count;
    for (let t = 0; t < n; t += 3) { const ia = I ? I.getX(t) : t, ib = I ? I.getX(t + 1) : t + 1, ic = I ? I.getX(t + 2) : t + 2;
      const gv = (vv, ii) => (o.isSkinnedMesh ? o.getVertexPosition(ii, vv) : vv.fromBufferAttribute(P, ii)).applyMatrix4(o.matrixWorld); gv(a, ia); gv(b, ib); gv(c, ic);
      bb.expandByPoint(a); bb.expandByPoint(b); bb.expandByPoint(c);
      const ym = Math.max(a.y, b.y, c.y); if (ym > 0.12) { hb.expandByPoint(a); hb.expandByPoint(b); hb.expandByPoint(c); }
      // rasterise: sample triangle at sub-cell density
      const e = Math.max(a.distanceTo(b), b.distanceTo(c), c.distanceTo(a)); const s = Math.max(1, Math.ceil(e / (C * 0.5)));
      for (let i = 0; i <= s; i++) for (let j = 0; j <= s - i; j++) { const u = i / s, v = j / s, w = 1 - u - v;
        const x = a.x * w + b.x * u + c.x * v, z = a.z * w + b.z * u + c.z * v, y = a.y * w + b.y * u + c.y * v;
        const cx = Math.floor((x - X0) / C), cz = Math.floor((z - Z0) / C); if (cx < 0 || cz < 0 || cx >= NX || cz >= NZ) continue;
        const q = cz * NX + cx; if (y > H[q]) { H[q] = y; ID[q] = k; } } } });
  const nodes = {}; S.traverse(o => { if (!o.isMesh && o.name && it.nodes && new RegExp(it.nodes, 'i').test(o.name)) { const w = o.getWorldPosition(new THREE.Vector3()); nodes[o.name] = [+w.x.toFixed(2), +w.y.toFixed(2), +w.z.toFixed(2)]; } });
  info.push({ name: it.name, f: it.f, x: it.x || 0, z: it.z || 0, bb: [bb.min.toArray(), bb.max.toArray()].map(p => p.map(q => +q.toFixed(2))), hi: [hb.min.toArray(), hb.max.toArray()].map(p => p.map(q => +q.toFixed(2))), nodes, anims: g.animations.map(a => a.name) });
}
fs.writeFileSync(cfg.out + '.bin', Buffer.concat([Buffer.from(H.buffer), Buffer.from(ID.buffer)]));
fs.writeFileSync(cfg.out + '.json', JSON.stringify({ C, X0, Z0, NX, NZ, info }, null, 1));
for (const i of info) console.log(i.name, 'bb', JSON.stringify(i.bb), 'hi', JSON.stringify(i.hi), Object.keys(i.nodes).length, 'nodes');
