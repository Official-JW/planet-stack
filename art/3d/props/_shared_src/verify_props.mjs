// three.js r186 GLTFLoader + MeshoptDecoder check for the FB-05 / cargo box / Refinery crane / receiver props.
// usage: NODE_PATH=/home/box/apps/gltftools/node_modules node verify_props.mjs KIND file.glb   (KIND = fb05 | box | crane | receiver)
import fs from 'fs';
const NM = process.env.NODE_PATH || '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
const [kind, f] = process.argv.slice(2); const buf = fs.readFileSync(f);
await MeshoptDecoder.ready;
const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder);
const BUD = { fb05: [4000, 3], box: [700, 2], crane: [3000, 3], receiver: [3000, 2] }[kind];
const fail = []; const r3 = v => v.toArray().map(x => +x.toFixed(3));
l.parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength), '', (g) => {
  let draws = 0, tris = 0; const mats = new Set();
  g.scene.traverse(o => { if (o.isMesh) { draws++; mats.add(o.material.name); tris += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3; } });
  const j = g.parser.json; const bad = (j.extensionsUsed || []).filter(e => !['EXT_meshopt_compression', 'KHR_mesh_quantization'].includes(e));
  const out = { file: f, bytes: buf.length, three: THREE.REVISION, draws, tris, materials: [...mats].sort(), ext: j.extensionsUsed, images: (j.images || []).length,
    clips: g.animations.map(a => [a.name, +a.duration.toFixed(3), a.tracks.length]) };
  if (bad.length || out.images || tris > BUD[0] || draws > BUD[1]) fail.push('budget/ext');
  const S = g.scene; S.updateMatrixWorld(true); const W = n => { const o = S.getObjectByName(n); if (!o) { fail.push('missing ' + n); return null; } o.updateWorldMatrix(true, false); return new THREE.Vector3().setFromMatrixPosition(o.matrixWorld); };
  const chk = {};
  if (kind === 'fb05') {
    const root = S.getObjectByName('FB05'); chk.root_extras = root?.userData;
    for (const s of ['FL', 'FR', 'ML', 'MR', 'RL', 'RR']) {
      const b = S.getObjectByName('FB05_Wheel_' + s); if (!b) { fail.push('wheel ' + s); continue; }
      const q0 = b.quaternion.clone(); b.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), 0.5)); b.updateMatrixWorld(true);
      const ax = new THREE.Vector3(1, 0, 0).applyQuaternion(b.getWorldQuaternion(new THREE.Quaternion())); chk['spin_axis_world_' + s] = r3(ax); b.quaternion.copy(q0);
      // a point at the tyre top must move +X (forward) for a positive spin
      const top = new THREE.Vector3(0, 0.853, 0); const pw0 = b.localToWorld(top.clone()); b.updateMatrixWorld(true);
    }
    chk.Bed_Slot_01 = r3(W('Bed_Slot_01')); chk.Bed_Slot_02 = r3(W('Bed_Slot_02'));
    // skinned check: spin FL by +0.3 rad, make sure the tyre top vertex region moves forward
    const mesh = S.getObjectByProperty('isSkinnedMesh', true); chk.skinned = !!mesh; chk.bones = mesh?.skeleton.bones.map(b => b.name);
    const fl = S.getObjectByName('FB05_Wheel_FL'); const top = new THREE.Vector3(2.4, 0.85 + 0.853, -1.5);
    const before = top.clone(); const local = fl.worldToLocal(top.clone());
    fl.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), 0.3)); fl.updateMatrixWorld(true);
    chk.FL_tyre_top_after_plus0p3rad = r3(fl.localToWorld(local.clone())); if (fl.localToWorld(local.clone()).x <= before.x) fail.push('wheel spin direction');
  }
  if (kind === 'box') { chk.Base = r3(W('Base')); chk.Hook_Point = r3(W('Hook_Point')); chk.extras = S.getObjectByName('CargoBox')?.userData;
    const bb = new THREE.Box3().setFromObject(S); chk.bbox = [r3(bb.min), r3(bb.max)]; }
  if (kind === 'crane') {
    const root = S.getObjectByName('Crane_Refinery'); const e = root.userData; chk.limits = Object.fromEntries(Object.entries(e).filter(([k]) => /_m$|_rad$|_y$/.test(k)));
    const slew = S.getObjectByName('Slew'), tro = S.getObjectByName('Trolley'), hoi = S.getObjectByName('Hoist'), hook = S.getObjectByName('Hook');
    const hook0 = hook.position.y;  // rest: L = 1
    const setJ = (th, r, L) => { slew.rotation.y = th; tro.position.x = r; hoi.scale.y = L; hook.position.y = hook0 + 1 - L; hook.rotation.y = -th; S.updateMatrixWorld(true); };
    for (const tgt of ['Pick_Point', 'Drop_Point', 'Drop_Point_02']) {
      const p = W(tgt).clone(); p.y += 1.5; const th = Math.atan2(-p.z, p.x), r = Math.hypot(p.x, p.z), L = e.sheave_y - p.y - e.hook_drop_m;
      setJ(th, r, L); const h = W('Hook'); const err = h.distanceTo(p); chk['solve_' + tgt] = { theta: +th.toFixed(4), r: +r.toFixed(3), L: +L.toFixed(3), hook: r3(h), err: +err.toFixed(4) };
      if (err > 0.01) fail.push('solve ' + tgt);
      const hx = new THREE.Vector3(1, 0, 0).applyQuaternion(hook.getWorldQuaternion(new THREE.Quaternion())); chk['solve_' + tgt].hook_x_axis = r3(hx); if (hx.x < 0.999) fail.push('rotator ' + tgt);
      if (r < e.trolley_min_m || r > e.trolley_max_m || L < e.hoist_min_m || L > e.hoist_max_m) fail.push('limits ' + tgt);
    }
    // cable end must meet the hook block top: sample the skinned cable bottom vertex after scaling
    setJ(0, 6, 5); const mesh = S.getObjectByProperty('isSkinnedMesh', true); const pos = mesh.geometry.attributes.position; let lowCable = null;
    const v = new THREE.Vector3(); const si = mesh.geometry.attributes.skinIndex; const hi = mesh.skeleton.bones.findIndex(b => b.name === 'Hoist');
    let ymin = 1e9; for (let i = 0; i < pos.count; i++) { if (si.getX(i) !== hi) continue; mesh.getVertexPosition(i, v); v.applyMatrix4(mesh.matrixWorld); ymin = Math.min(ymin, v.y); }
    chk.cable_bottom_y_at_L5 = +ymin.toFixed(3); chk.hook_block_top_y_at_L5 = +(W('Hook').y + e.hook_drop_m).toFixed(3);
    if (Math.abs(ymin - (W('Hook').y + e.hook_drop_m)) > 0.02) fail.push('cable/hook mismatch');
    setJ(0, e.trolley_min_m, 1);
    const clip = g.animations.find(a => a.name === 'crane_load');
    if (clip) { const mx = new THREE.AnimationMixer(S); const ac = mx.clipAction(clip); ac.play(); const samp = {};
      let yawmax = 0; for (const t of [0, 0.9, 1.3, 2.7, 4.1, 5.5, 6.0]) { mx.setTime(t); S.updateMatrixWorld(true); samp[t] = r3(W('Hook')); const hx = new THREE.Vector3(1, 0, 0).applyQuaternion(hook.getWorldQuaternion(new THREE.Quaternion())); yawmax = Math.max(yawmax, Math.abs(Math.atan2(-hx.z, hx.x))); }
      chk.clip_hook_world_yaw_max_rad = +yawmax.toFixed(5); if (yawmax > 0.01) fail.push('clip rotator');
      chk.clip_hook_samples = samp; const P = W('Pick_Point'), D = W('Drop_Point');
      const ok1 = new THREE.Vector3(...samp[0.9]).distanceTo(P.clone().add(new THREE.Vector3(0, 1.5, 0))), ok2 = new THREE.Vector3(...samp[4.1]).distanceTo(D.clone().add(new THREE.Vector3(0, 1.5, 0)));
      chk.clip_err_pick = +ok1.toFixed(4); chk.clip_err_drop = +ok2.toFixed(4); if (ok1 > 0.02 || ok2 > 0.02) fail.push('clip targets');
      let md = 0; for (const tr of clip.tracks) { const n = tr.getValueSize(); const a = tr.values.slice(0, n), b = tr.values.slice(-n); for (let i = 0; i < n; i++) md = Math.max(md, Math.abs(a[i] - b[i])); }
      chk.clip_first_last_maxdiff = md; if (md > 1e-4) fail.push('clip loop'); }
  }
  if (kind === 'receiver') { chk.Receive_Point = r3(W('Receive_Point')); }
  out.checks = chk; out.fail = fail; console.log(JSON.stringify(out, null, 1)); if (fail.length) process.exit(1);
}, e => { console.error('LOAD FAILED', e); process.exit(1); });
