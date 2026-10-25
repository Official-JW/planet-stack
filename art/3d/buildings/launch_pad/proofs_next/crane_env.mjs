import fs from 'fs';
const NM = process.env.NODE_PATH;
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
const buf = fs.readFileSync(process.argv[2]); await MeshoptDecoder.ready;
const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder);
l.parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength), '', (g) => {
  const S = g.scene, crane = S.getObjectByName('Crane'), hook = S.getObjectByName('Hook'); const out = {};
  const cp = crane.getWorldPosition(new THREE.Vector3()); out.crane_origin = cp.toArray();
  const ex = crane.userData; out.limits = { trolley: [ex.trolley_min_m, ex.trolley_max_m], hoist: [ex.hoist_min_m, ex.hoist_max_m], sheave_y: ex.sheave_y, hook_drop_m: ex.hook_drop_m };
  const env = { r: [1e9, -1e9], y: [1e9, -1e9] }; out.clips = {};
  for (const clip of g.animations.filter(c => c.name.startsWith('crane'))) {
    const mx = new THREE.AnimationMixer(S); const a = mx.clipAction(clip); a.setLoop(THREE.LoopOnce); a.clampWhenFinished = true; a.play(); const pts = [];
    const n = Math.max(2, Math.round(clip.duration * 30));
    for (let i = 0; i <= n; i++) { mx.setTime(clip.duration * i / n); S.updateMatrixWorld(true);
      const h = hook.getWorldPosition(new THREE.Vector3()).sub(cp); const r = Math.hypot(h.x, h.z);
      pts.push({ t: +(clip.duration * i / n).toFixed(3), local: h.toArray().map(v => +v.toFixed(3)), r: +r.toFixed(3), y: +h.y.toFixed(3) });
      env.r[0] = Math.min(env.r[0], r); env.r[1] = Math.max(env.r[1], r); env.y[0] = Math.min(env.y[0], h.y); env.y[1] = Math.max(env.y[1], h.y); }
    a.stop(); mx.uncacheRoot(S);
    const rs = pts.map(p => p.r), ys = pts.map(p => p.y);
    out.clips[clip.name] = { duration: clip.duration, start: pts[0], end: pts[pts.length - 1], r: [Math.min(...rs), Math.max(...rs)], y: [Math.min(...ys), Math.max(...ys)] };
  }
  out.envelope_baked = { r_m: env.r.map(v => +v.toFixed(3)), hook_y_crane_local_m: env.y.map(v => +v.toFixed(3)) };
  out.envelope_rig = { r_m: out.limits.trolley, hook_y_m: [ex.sheave_y - ex.hoist_max_m - ex.hook_drop_m, ex.sheave_y - ex.hoist_min_m - ex.hook_drop_m].map(v => +v.toFixed(3)) };
  for (const nm of ['Truck_Stop', 'Pick_Point', 'Pick_Point_02']) { const p = S.getObjectByName(nm).getWorldPosition(new THREE.Vector3()); const d = p.clone().sub(cp); out[nm] = { pad: p.toArray().map(v => +v.toFixed(3)), crane_r: +Math.hypot(d.x, d.z).toFixed(3) }; }
  console.log(JSON.stringify(out, null, 1)); if (process.argv[3]) fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 1));
}, e => { console.error(e); process.exit(1); });
