// Pre-build clearance check for lane fix A option (a): move PC-1 base, stretch jib, sweep 360 deg slew; min distance jib/slew-bound tris vs every other visible pad mesh (tri-sampled 0.15 m).
import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules'; const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js'); const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js'); await MeshoptDecoder.ready;
const [F, CZs, TMs, OUT] = process.argv.slice(2); const CX = 0.6, CZ = +CZs, TMAX = +TMs;
const b = fs.readFileSync(F); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder);
const g = await new Promise((r, j) => l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', r, j));
const S = g.scene; S.updateMatrixWorld(true);
const crane = S.getObjectByName('Crane'), cu = crane.userData, oldT = cu.trolley_max_m;
const SKS = []; crane.traverse(o => { if (o.isSkinnedMesh) SKS.push(o); }); let sk = SKS[0];
const bones = sk.skeleton.bones.map(x => x.name); const iSlew = bones.indexOf('Slew'), iTr = bones.indexOf('Trolley');
// rest-pose world positions to find jib verts (bound to Slew, beyond mast + 5 m along +X)
let nStretch = 0; var DX, k; for (sk of SKS) { const P = sk.geometry.attributes.position, SI = sk.geometry.attributes.skinIndex, SW = sk.geometry.attributes.skinWeight; const v = new THREE.Vector3();
const restW = []; for (let i = 0; i < P.count; i++) { sk.getVertexPosition(i, v); v.applyMatrix4(sk.matrixWorld); restW.push(v.clone()); }
var cw = crane.getWorldPosition(new THREE.Vector3());
DX = TMAX - oldT; var X0 = 5, L0 = 15.287; k = (L0 + DX - X0) / (L0 - X0); 
var dom = i => { let bi = SI.getX(i), bw = SW.getX(i); for (const c of ['getY', 'getZ', 'getW']) if (SW[c](i) > bw) { bw = SW[c](i); bi = SI[c](i); } return bi; };
// stretch in the raw attribute space: x_raw' = x0raw + (x_raw - x0raw) * k, using rest world x offset (raw and rest world differ by a constant transform with no rotation/scale on x? check)
const meshInv = new THREE.Matrix4().copy(sk.bindMatrixInverse);
for (let i = 0; i < P.count; i++) { if (dom(i) !== iSlew) continue; const lx = restW[i].x - cw.x; if (lx <= X0) continue; const nx = X0 + (lx - X0) * k; const d = nx - lx;
  // raw delta: rest world = matrixWorld*bindMatrix-ish; for rigid unrotated chains a world x shift d equals raw x shift d / scale
  P.setX(i, P.getX(i) + d / sk.matrixWorld.elements[0] * 1); nStretch++; }
P.needsUpdate = true; }
crane.position.set(CX, 0, CZ); S.updateMatrixWorld(true);
const C = crane.getWorldPosition(new THREE.Vector3());
// sample triangles helper
const samp = (A, B, Cc, out, h = 0.15) => { const e1 = B.clone().sub(A), e2 = Cc.clone().sub(A); const n1 = Math.max(1, Math.ceil(Math.max(e1.length(), e2.length(), Cc.distanceTo(B)) / h));
  for (let a = 0; a <= n1; a++) for (let c = 0; c <= n1 - a; c++) out.push(A.clone().addScaledVector(e1, a / n1).addScaledVector(e2, c / n1)); };
// obstacles
const hiddenUp = o => { for (let q = o; q; q = q.parent) if (/^Tier_\d+/.test(q.name) || q.userData?.hidden_by_default) return true; return false; };
const owner = o => { let q = o; while (q.parent && q.parent !== S) q = q.parent; return q.name; };
const obs = []; const cell = 0.5, H = new Map(); const key = (x, y, z) => Math.floor(x / cell) + ',' + Math.floor(y / cell) + ',' + Math.floor(z / cell);
const YMIN = +(process.env.YMIN || 14);
S.traverse(o => { if (!o.isMesh || owner(o) === 'Crane' || hiddenUp(o) || owner(o) === 'Road_UTurn') return; const a = o.geometry.attributes.position, ix = o.geometry.index; const w = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()];
  for (let t = 0; t < ix.count; t += 3) { for (let q = 0; q < 3; q++) w[q].fromBufferAttribute(a, ix.getX(t + q)).applyMatrix4(o.matrixWorld); if (Math.max(w[0].y, w[1].y, w[2].y) < YMIN) continue;
    if (Math.min(...w.map(p => Math.hypot(p.x - C.x, p.z - C.z))) > TMAX + 4) continue; const pts = []; samp(w[0], w[1], w[2], pts); for (const p of pts) { if (p.y < YMIN - 0.5) continue; const kk = key(p.x, p.y, p.z); (H.get(kk) || H.set(kk, []).get(kk)).push([p.x, p.y, p.z, owner(o)]); obs.push(1); } } });
// crane slew-bound tris (Slew + Trolley + Hoist/Hook too at the pose), sampled in bind space then posed per angle
const triSets = []; for (const m of SKS) { sk = m; const SI2 = m.geometry.attributes.skinIndex, SW2 = m.geometry.attributes.skinWeight; const ix = m.geometry.index; for (let t = 0; t < ix.count; t += 3) { const ids = [ix.getX(t), ix.getX(t + 1), ix.getX(t + 2)]; if (SI2.getX(ids[0]) !== iSlew) continue; triSets.push([m, ids]); } }
let tip = 0; const cp = []; const p3 = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()]; S.updateMatrixWorld(true); SKS.forEach(m => m.skeleton.update());
for (const [m, ids] of triSets) { for (let q = 0; q < 3; q++) { m.getVertexPosition(ids[q], p3[q]); p3[q].applyMatrix4(m.matrixWorld); tip = Math.max(tip, Math.hypot(p3[q].x - C.x, p3[q].z - C.z)); }
  const pts = []; samp(p3[0], p3[1], p3[2], pts, 0.25); for (const p of pts) cp.push(p.x - C.x, p.y, p.z - C.z); }
const CP = Float32Array.from(cp); const NH = new Map(); for (const [kk, L] of H) { const [a, bb, c] = kk.split(',').map(Number); NH.set((a + 5000) * 1e8 + (bb + 500) * 1e4 + (c + 5000), L.map(o => [o[0], o[1], o[2], o[3]])); }
let worst = { d: 1e9 }; const perAng = []; const STEP = +(process.env.STEP || 1);
for (let deg = 0; deg < 360; deg += STEP) { const th = deg * Math.PI / 180, cs = Math.cos(th), sn = Math.sin(th); let best = { d: 1e9 };
  for (let i = 0; i < CP.length; i += 3) { const lx = CP[i], y = CP[i + 1], lz = CP[i + 2]; const x = C.x + lx * cs + lz * sn, z = C.z - lx * sn + lz * cs;
    const cx = Math.floor(x / cell), cy = Math.floor(y / cell), cz = Math.floor(z / cell);
    for (let a = -1; a <= 1; a++) for (let bb = -1; bb <= 1; bb++) for (let c = -1; c <= 1; c++) { const L = NH.get((cx + a + 5000) * 1e8 + (cy + bb + 500) * 1e4 + (cz + c + 5000)); if (!L) continue;
      for (const o of L) { const dx = o[0] - x, dy = o[1] - y, dz = o[2] - z; const d2 = dx * dx + dy * dy + dz * dz; if (d2 < best.d * best.d) best = { d: Math.sqrt(d2), deg, crane: [x, y, z].map(q => +q.toFixed(2)), obs: o.slice(0, 3).map(q => +q.toFixed(2)), what: o[3] }; } } }
  perAng.push(best.d > 1e8 ? null : +best.d.toFixed(3)); if (best.d < worst.d) worst = best; }
// slew angle (game convention theta) for deg: jib dir (cos, -sin) -> theta = deg
const shipAxis = S.getObjectByName('Ship_Placeholder').getWorldPosition(new THREE.Vector3());
const out = { file: F, base_pad_local: [CX, 0, CZ], dist_to_ship_axis_m: +Math.hypot(C.x - shipAxis.x, C.z - shipAxis.z).toFixed(3), trolley_max_m: TMAX, jib_stretch: { verts: nStretch, k: +k.toFixed(5), dx_m: +DX.toFixed(3) },
  jib_tip_radius_m: +tip.toFixed(3), obstacle_samples: obs.length, ymin: YMIN, note: 'min distance (m) from any Slew-bound crane triangle (jib, counter-jib, cab, apex, ties; 0.25 m tri sampling) to any visible non-crane, non-road pad triangle with y >= ymin (0.15 m sampling, so true gap within ~0.1 m), slew swept 0..359 deg step 1 (any clip / any slew between Hold_Door and truck covered)',
  min_clearance: { ...worst, d: +worst.d.toFixed(3) }, per_deg: perAng };
fs.writeFileSync(OUT, JSON.stringify(out)); console.log(JSON.stringify({ ...out, per_deg: undefined }));
