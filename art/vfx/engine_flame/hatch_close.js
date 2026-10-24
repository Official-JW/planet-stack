// Crew-hatch lid close (0.8 s, easeInOutCubic) for the cargo ship. 0 draw calls, 0 textures:
// the lid, its 2 ribs and 2 hold-open struts are islands inside the merged Ship_Placeholder mesh, so we move those vertices
// in place instead of adding a mesh. The motion comes from hatch_close.glb (node Hatch_Lid_Hinge, clip "hatch_close").
//   const hc = createHatchClose(shipMeshes, clipGltf);   // clipGltf = await loader.loadAsync('.../hatch_close.glb')
//   hc.update(secondsSinceHatchClose);                     // < 0 = open (parked/boarding), >= 0.8 = closed
import * as THREE from 'three';
export const HATCH = { CLOSE_S: 0.8, HC_AFTER_TAP_S: 53.19 };

// upload only the touched vertex range (works for plain and interleaved attributes, as GLTFLoader makes for quantized data)
function mark(a, lo, hi) { const b = a.isInterleavedBufferAttribute ? a.data : a, st = a.isInterleavedBufferAttribute ? b.stride : a.itemSize;
  b.clearUpdateRanges(); b.addUpdateRange(lo * st, (hi - lo + 1) * st); b.needsUpdate = true; }

export function createHatchClose(shipMeshes, clipGltf) {
  const hn = clipGltf.scene.getObjectByName('Hatch_Lid_Hinge'), ex = hn.userData;
  const clip = clipGltf.animations.find(a => a.name === 'hatch_close');
  const interp = clip.tracks.find(t => t.name.endsWith('.quaternion')).createInterpolant();
  const H = hn.position.clone(), AX = new THREE.Vector3().fromArray(ex.hinge_axis).normalize(), UP = new THREE.Vector3(0, 1, 0);
  const LU = new THREE.Vector3().crossVectors(AX, UP).normalize();     // outboard (u) for t = AX, z = up
  const sets = [];
  for (const m of shipMeshes) {
    const g = m.geometry, p = g.attributes.position, idx = g.index.array, n = p.count, M = m.matrix, Mi = M.clone().invert();
    const par = new Int32Array(n).map((_, i) => i); const f = i => { while (par[i] !== i) { par[i] = par[par[i]]; i = par[i]; } return i; };
    for (let i = 0; i < idx.length; i += 3) { const a = f(idx[i]); par[f(idx[i + 1])] = a; par[f(idx[i + 2])] = a; }
    const isl = new Map(), v = new THREE.Vector3();
    for (let i = 0; i < n; i++) { v.fromBufferAttribute(p, i).applyMatrix4(M).sub(H); const r = f(i); let o = isl.get(r); if (!o) isl.set(r, o = { ids: [], u: 0, t: 0, z: 0, zMax: -1e9 });
      o.ids.push(i); o.u += v.dot(LU); o.t += v.dot(AX); o.z += v.y; o.zMax = Math.max(o.zMax, v.y); }
    const lid = [], struts = [];
    for (const o of isl.values()) { const k = o.ids.length, u = o.u / k, t = o.t / k, z = o.z / k;
      if (k > 16 || Math.abs(t) >= 0.66 || u <= -0.1 || u >= 0.3 || z <= 0.15 || z >= 0.8) continue;
      (o.zMax > 0.9 ? lid : struts).push(o.ids); }
    if (!lid.length) continue;
    const nr = g.attributes.normal, P0 = (ids) => ids.map(i => ({ i, p: new THREE.Vector3().fromBufferAttribute(p, i).applyMatrix4(M), n: nr ? new THREE.Vector3().fromBufferAttribute(nr, i) : null }));
    // strut: foot = lowest end (fixed on the deck), top = end on the lid (follows the lid)
    const st = struts.map(ids => { const vs = P0(ids); let foot = vs[0].p, top = vs[0].p; for (const q of vs) { if (q.p.y < foot.y) foot = q.p; if (q.p.y > top.y) top = q.p; }
      const fc = new THREE.Vector3(), tc = new THREE.Vector3(); let nf = 0, nt = 0;
      for (const q of vs) { if (q.p.distanceTo(foot) < 0.06) { fc.add(q.p); nf++; } else if (q.p.distanceTo(top) < 0.06) { tc.add(q.p); nt++; } }
      return { vs, foot: fc.divideScalar(nf || 1), top: tc.divideScalar(nt || 1) }; });
    const all = [...lid.flat(), ...struts.flat()], lo = Math.min(...all), hi = Math.max(...all);
    sets.push({ m, p, nr, Mi, lid: P0(lid.flat()), st, lo, hi });
  }
  const q = new THREE.Quaternion(), w = new THREE.Vector3(), nq = new THREE.Quaternion();
  let last = NaN;
  return {
    found: sets.map(s => ({ mesh: s.m.name, lidVerts: s.lid.length, struts: s.st.length, range: [s.lo, s.hi] })),
    drawCallsAdded: 0,
    update(tSinceHC) {
      const tc = Math.min(Math.max(tSinceHC, 0), HATCH.CLOSE_S); if (tc === last) return; last = tc;
      q.fromArray(interp.evaluate(tc));
      for (const s of sets) { const r = q;   // the ship mesh matrix is translate + uniform scale, so normals turn by the same rotation
        for (const o of s.lid) { w.copy(o.p).sub(H).applyQuaternion(q).add(H).applyMatrix4(s.Mi); s.p.setXYZ(o.i, Math.round(w.x), Math.round(w.y), Math.round(w.z));
          if (o.n && s.nr) { const nn = o.n.clone().applyQuaternion(r); s.nr.setXYZ(o.i, nn.x, nn.y, nn.z); } }
        for (const S of s.st) { const top1 = S.top.clone().sub(H).applyQuaternion(q).add(H), a0 = S.top.clone().sub(S.foot), a1 = top1.clone().sub(S.foot);
          const k = a1.length() / a0.length(), d0 = a0.clone().normalize(); nq.setFromUnitVectors(d0, a1.clone().normalize());
          for (const o of S.vs) { const rel = o.p.clone().sub(S.foot), along = rel.dot(d0), perp = rel.clone().addScaledVector(d0, -along);
            w.copy(d0).multiplyScalar(along * k).add(perp).applyQuaternion(nq).add(S.foot).applyMatrix4(s.Mi);
            s.p.setXYZ(o.i, Math.round(w.x), Math.round(w.y), Math.round(w.z)); } }
        mark(s.p, s.lo, s.hi); if (s.nr) mark(s.nr, s.lo, s.hi); }
    },
  };
}
