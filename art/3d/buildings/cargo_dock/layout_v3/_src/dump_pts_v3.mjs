// collect world points of dock + storage + crane envelope + FB-05 at the stop, then solve the dock camera (ct, frame_w) for 375x667 and 393x852 bands
import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js'); await MeshoptDecoder.ready;
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const SITE = '/workspace/dockl/site/', CRANE = process.argv[2];
const SL = JSON.parse(fs.readFileSync(SITE + 'slots_v3.json')); const groups = {}; const v = new THREE.Vector3();
function verts(S, key) { S.updateMatrixWorld(true); const arr = groups[key] || (groups[key] = []); S.traverse(o => { if (!o.isMesh) return; for (let q = o; q; q = q.parent) if (/^Tier_/.test(q.name)) return; if (o.isSkinnedMesh) o.skeleton.update(); const P = o.geometry.attributes.position;
  for (let i = 0; i < P.count; i++) { (o.isSkinnedMesh ? o.getVertexPosition(i, v) : v.fromBufferAttribute(P, i)).applyMatrix4(o.matrixWorld); arr.push([v.x, v.y, v.z]); } }); }
const dock = (await load(SITE + 'dock_v3.glb')).scene; dock.traverse(o => { if (/^Tier_/.test(o.name)) o.visible = false; }); dock.position.set(...SL.dock_origin_world); verts(dock, 'dock');
const fb = (await load(SITE + 'fb.glb')).scene; fb.position.set(...SL.truck_stop_dock.world); verts(fb, 'truck');
const st = groups.storage = [];
for (const s of SL.slots) for (const dx of [-1.2, 1.2]) for (const dz of [-0.67, 0.67]) for (const dy of [0, 1.5]) st.push([s.world[0] + dx, s.world[1] + dy, s.world[2] + dz]);
const ap = SL.apron, o = SL.dock_origin_world; for (const x of [ap[0], ap[1]]) for (const z of [ap[2], ap[3]]) for (const y of [0, 0.12]) st.push([o[0] + x, y, o[2] + z]);
const cg = await load(CRANE); const C = cg.scene; C.position.set(...SL.storage_crane.place_world); const mx = new THREE.AnimationMixer(C); const ha = C.getObjectByName('Hook_Attach'); const cr = groups.crane = [];
for (const c of cg.animations) { mx.stopAllAction(); mx.clipAction(c).play(); for (let t = 0; t <= 6; t += 0.1) { mx.setTime(t); verts(C, 'crane');
  if (t > 1.55 && t < 4.35) { ha.getWorldPosition(v); for (const dx of [-1.2, 1.2]) for (const dz of [-0.67, 0.67]) for (const dy of [-1.5, 0]) cr.push([v.x + dx, v.y + dy, v.z + dz]); } } }
// thin each group to its convex-ish extreme set: keep all (projection is cheap)
const ALL = Object.values(groups).flat(); console.log('points', Object.fromEntries(Object.entries(groups).map(([k, a]) => [k, a.length])));
for (const [k,a] of Object.entries(groups)) fs.writeFileSync(`/workspace/dockl/v3/pts_${k}.f32`, Buffer.from(new Float32Array(a.flat()).buffer)); process.exit(0);
const cam = new THREE.PerspectiveCamera(38, 1, 0.1, 2000);
function bounds(ct, fw, sz, pts = ALL) { cam.aspect = sz.W / sz.H; cam.updateProjectionMatrix(); const d = (fw / 2) / (Math.tan(19 * Math.PI / 180) * cam.aspect), p = 18 * Math.PI / 180;
  cam.position.set(ct[0], ct[1] + d * Math.sin(p), ct[2] + d * Math.cos(p)); cam.lookAt(ct[0], ct[1], ct[2]); cam.updateMatrixWorld(true);
  let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9; for (const q of pts) { v.set(q[0], q[1], q[2]).project(cam); const X = (v.x + 1) / 2 * sz.W, Y = (1 - v.y) / 2 * sz.H; x0 = Math.min(x0, X); x1 = Math.max(x1, X); y0 = Math.min(y0, Y); y1 = Math.max(y1, Y); }
  return { x0, x1, y0, y1, spare: { left: x0, right: sz.W - x1, top: y0 - sz.top, bottom: sz.bot - y1 } }; }
const ctz = +(process.argv[3] || -8);
function fitAt(fw) { // choose ct x,y that maximise the worst spare over both sizes (coordinate search)
  let ct = [384, 4, ctz], best = -1e9;
  const score = c => Math.min(...SIZES.flatMap(s => Object.values(bounds(c, fw, s).spare)));
  best = score(ct);
  for (let step = 8; step > 0.01; step /= 2) { let imp = true; while (imp) { imp = false; for (const [i, dlt] of [[0, step], [0, -step], [1, step], [1, -step]]) { const c = ct.slice(); c[i] += dlt; const s = score(c); if (s > best + 1e-6) { best = s; ct = c; imp = true; } } } }
  return { ct, best };
}
let lo = 40, hi = 160; for (let it = 0; it < 30; it++) { const m = (lo + hi) / 2; if (fitAt(m).best >= 5) hi = m; else lo = m; }
console.log('min fw for 5 px', hi.toFixed(3), JSON.stringify(fitAt(hi)));
const fwPick = +(process.argv[4] || Math.ceil(hi * 4) / 4 + 1); const f = fitAt(fwPick); const ct = f.ct.map(c => Math.round(c * 20) / 20);
const res = { ct, frame_w: fwPick, sizes: {} };
for (const s of SIZES) { const b = bounds(ct, fwPick, s); res.sizes[`${s.W}x${s.H}`] = { band: [s.top, s.bot], subject_px: [b.x0, b.y0, b.x1, b.y1].map(q => +q.toFixed(1)), spare_px: Object.fromEntries(Object.entries(b.spare).map(([k, q]) => [k, +q.toFixed(1)])),
  per_group: Object.fromEntries(Object.entries(groups).map(([k, a]) => { const g = bounds(ct, fwPick, s, a); return [k, [g.x0, g.y0, g.x1, g.y1].map(q => +q.toFixed(1))]; })) }; }
console.log(JSON.stringify(res, null, 1)); fs.writeFileSync('/workspace/dockl/frame_v2.json', JSON.stringify(res, null, 1));
