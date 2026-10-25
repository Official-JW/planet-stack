import fs from 'fs'; const NM = process.env.NODE_PATH; const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js'); const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js'); await MeshoptDecoder.ready;
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const g = await load(process.argv[2]), S = g.scene; S.updateMatrixWorld(true); const W = n => S.getObjectByName(n).getWorldPosition(new THREE.Vector3());
const tr = (await load('/workspace/planet-stack/art/3d/props/fb05/fb05_game.glb')).scene; tr.position.copy(W('Truck_Stop')); tr.updateMatrixWorld(true);
const P = []; const v = new THREE.Vector3(); tr.traverse(o => { if (o.isMesh) { const a = o.geometry.attributes.position; for (let i = 0; i < a.count; i++) { v.fromBufferAttribute(a, i).applyMatrix4(o.matrixWorld); P.push([v.x, v.y, v.z, 'truck']); } } });
const b2 = W('Pick_Point_02'); for (const sx of [-1.2, 0, 1.2]) for (const sz of [-0.67, 0, 0.67]) P.push([b2.x + sx, b2.y + 1.5, b2.z + sz, 'box2']);
const hook = S.getObjectByName('Hook'); const out = {};
for (const name of ['crane_lift', 'crane_swing']) { const clip = g.animations.find(c => c.name === name); const mx = new THREE.AnimationMixer(S); const a = mx.clipAction(clip); a.setLoop(THREE.LoopOnce); a.clampWhenFinished = true; a.play();
  let worst = { gap: 1e9 };
  for (let t = 0.25; t <= clip.duration + 1e-6; t += 1 / 30) { mx.setTime(t); S.updateMatrixWorld(true); const h = hook.getWorldPosition(new THREE.Vector3()); const yaw = new THREE.Euler().setFromQuaternion(hook.getWorldQuaternion(new THREE.Quaternion()), 'YXZ').y;
    const bot = h.y - 1.5 - 0; const c = Math.cos(yaw), s = Math.sin(yaw);
    for (const p of P) { const dx = p[0] - h.x, dz = p[2] - h.z; const u = dx * c - dz * s, w = dx * s + dz * c; if (Math.abs(u) <= 1.2 + 0.1 && Math.abs(w) <= 0.67 + 0.1) { const gap = bot - p[1]; if (gap < worst.gap) worst = { gap: +gap.toFixed(3), t: +t.toFixed(2), what: p[3], hook: h.toArray().map(x => +x.toFixed(2)) }; } } }
  out[name] = worst; mx.uncacheRoot(S); }
console.log(JSON.stringify(out)); fs.writeFileSync(process.argv[3], JSON.stringify({ note: 'min vertical gap box bottom -> truck verts / Pick_Point_02 box top under the hanging box footprint (+0.1 m), t >= 0.25 s (box leaves the bed)', ...out }, null, 1));
