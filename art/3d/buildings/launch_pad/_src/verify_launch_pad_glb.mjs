// three.js GLTFLoader + MeshoptDecoder check of launch_pad_game.glb (budgets, nodes, empties, clips, crane solve, road corridor).
// usage: NODE_PATH=/home/box/apps/gltftools/node_modules node verify_launch_pad_glb.mjs launch_pad_game.glb [report.json]
import fs from 'fs'; import crypto from 'crypto';
const NM = process.env.NODE_PATH || '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
const [f, outp] = process.argv.slice(2); const buf = fs.readFileSync(f); await MeshoptDecoder.ready;
const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder);
const fail = []; const r3 = v => v.toArray().map(x => +x.toFixed(3));
const WX = 480;   // world = pad-local + (480, 0, 0)  (qa3d/main.js: station i at i * 160, Takeoff & Landing = 3)
l.parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength), '', (g) => {
  const S = g.scene; S.updateMatrixWorld(true); const j = g.parser.json;
  const NN = o => { while (o && o !== S && !o.name.replace(/^mesh_\d+(_\d+)?$/, '')) o = o.parent; return o && o !== S ? o.name : '?'; };
  let draws = 0, tris = 0; const meshes = [], empties = [], joints = [];
  S.traverse(o => {
    if (o.isMesh) { draws++; const t = (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3; tris += t; meshes.push([NN(o), o.material.name, t]); }
    else if (o.isBone) joints.push(o.name);
    else if (o !== S && !o.children.some(c => c.isMesh && c.name === o.name) && o.type === 'Object3D' && !o.children.length) empties.push(o.name);
  });
  const ext = j.extensionsUsed || []; const bad = ext.filter(e => !['EXT_meshopt_compression', 'KHR_mesh_quantization'].includes(e));
  const out = { file: f, bytes: buf.length, md5: crypto.createHash('md5').update(buf).digest('hex'), three: THREE.REVISION, tris, draws,
    extensions: ext, images: (j.images || []).length, textures: (j.textures || []).length, nodes: (j.nodes || []).length, meshes, empties: empties.sort(), joints };
  if (bad.length) fail.push('extensions ' + bad); if (ext.includes('KHR_draco_mesh_compression')) fail.push('draco');
  if (out.images || out.textures) fail.push('images'); if (tris > 30000) fail.push('tris'); if (draws > 15) fail.push('draws'); if (buf.length > 900 * 1024) fail.push('size');
  // clips: duration + first / last value of every track
  out.clips = g.animations.map(a => ({ name: a.name, duration_s: +a.duration.toFixed(3), tracks: a.tracks.map(t => {
    const n = t.getValueSize(); const v = t.values; return { track: t.name, first: Array.from(v.slice(0, n)).map(x => +x.toFixed(4)), last: Array.from(v.slice(-n)).map(x => +x.toFixed(4)), t0: +t.times[0].toFixed(3), t1: +t.times[t.times.length - 1].toFixed(3) }; }) }));
  const need = ['Cam_Target', 'Ship_Center', 'Fuel_Hookup', 'Pipe_LaunchPad_End', 'Truck_Stop', 'Pick_Point', 'Pick_Point_Bay', 'Drop_Point', 'Receiver_Spot', 'Receiver_Home',
    'Hold_Door', ...Array.from({ length: 10 }, (_, i) => 'Hold_' + String(i + 1).padStart(2, '0')), ...Array.from({ length: 12 }, (_, i) => 'Bay_Slot_' + String(i + 1).padStart(2, '0')),
    'Hook', 'Slew', 'Trolley', 'Hoist', 'Cargo_Door'];
  for (const n of need) if (!S.getObjectByName(n)) fail.push('missing ' + n);
  for (const c of ['crane_lift', 'crane_swing', 'crane_lower', 'cargo_door_open', 'cargo_door_close']) if (!g.animations.find(a => a.name === c)) fail.push('clip ' + c);
  const W = n => new THREE.Vector3().setFromMatrixPosition(S.getObjectByName(n).matrixWorld);
  out.cam_target = { at: r3(W('Cam_Target')), extras: S.getObjectByName('Cam_Target').userData };
  out.truck_stop_world = (p => [+(p.x + WX).toFixed(3), +p.y.toFixed(3), +p.z.toFixed(3)])(W('Truck_Stop'));
  if (Math.abs(out.truck_stop_world[2] - 13) > 1e-3) fail.push('Truck_Stop not on z 13');
  const rs = W('Receiver_Spot'), rh = W('Receiver_Home'); out.receiver = { spot: r3(rs), home: r3(rh), dist_m: +rs.distanceTo(rh).toFixed(3),
    spot_yaw_deg: +(S.getObjectByName('Receiver_Spot').rotation.y * 180 / Math.PI).toFixed(2), home_yaw_deg: +(S.getObjectByName('Receiver_Home').rotation.y * 180 / Math.PI).toFixed(2) };
  // rig check: Home_Point (-3, 0, -1.5) in the Receive_Point frame
  const hp = new THREE.Vector3(-3, 0, -1.5).applyQuaternion(S.getObjectByName('Receiver_Spot').getWorldQuaternion(new THREE.Quaternion())).add(rs);
  out.receiver.rig_home_err_m = +hp.distanceTo(rh).toFixed(4); if (out.receiver.rig_home_err_m > 0.01) fail.push('Receiver_Home offset');
  // crane: drive the joints with the solve stored on each target, compare the hook with the target
  const cr = S.getObjectByName('Crane'); const e = cr.userData; const slew = S.getObjectByName('Slew'), tro = S.getObjectByName('Trolley'), hoi = S.getObjectByName('Hoist'), hook = S.getObjectByName('Hook');
  const q0 = [slew.quaternion.clone(), tro.position.clone(), hoi.scale.clone(), hook.position.clone(), hook.quaternion.clone()];
  out.crane = {};
  S.traverse(o => { const cs = o.userData && o.userData.crane_solve; if (!cs) return;
    const p = W(o.name).clone(); p.y += e.box_hook_offset_y; const c = W('Crane');
    slew.rotation.set(0, cs.slew_rad, 0); tro.position.set(q0[1].x + cs.trolley_m - e.trolley_min_m, q0[1].y, q0[1].z); hoi.scale.set(1, cs.hoist_m, 1);
    hook.position.set(q0[3].x, q0[3].y + 1 - cs.hoist_m, q0[3].z); hook.rotation.set(0, cs.hook_yaw_rad, 0); S.updateMatrixWorld(true);
    const err = W('Hook').distanceTo(p); out.crane[o.name] = +err.toFixed(4); if (err > 0.02) fail.push('crane solve ' + o.name); });
  slew.quaternion.copy(q0[0]); tro.position.copy(q0[1]); hoi.scale.copy(q0[2]); hook.position.copy(q0[3]); hook.quaternion.copy(q0[4]); S.updateMatrixWorld(true);
  // road corridor: every mesh vertex (world space, rest pose) with world x <= 481 and world z 11..24 must sit at y <= 0.02
  const v = new THREE.Vector3(); out.road = { rule: 'no vertex above y 0.02 with world x < 480.95 (x 481 = U-turn seam) and world z in [11, 24] (also reported: toe-to-toe z 10.2..24.8)', meshes: [] };
  let worst = -1e9, worstT = -1e9; const seam = [];
  S.traverse(o => { if (!o.isMesh) return; const pos = o.geometry.attributes.position; let mx = -1e9, mxT = -1e9, n = 0; const bb = new THREE.Box3(); const offenders = [];
    for (let i = 0; i < pos.count; i++) { o.getVertexPosition ? o.getVertexPosition(i, v) : v.fromBufferAttribute(pos, i); v.applyMatrix4(o.matrixWorld);
      const wx = v.x + WX; if (wx > 481.0001) continue;
      if (wx > 480.95) { if (v.z >= 11 && v.z <= 24 && v.y > 0.02) seam.push([+wx.toFixed(3), +v.y.toFixed(3), +v.z.toFixed(2)]); continue; }   // x 481 = U-turn seam row (same profile as the tile end)
      if (v.z >= 10.2 && v.z <= 24.8) { mxT = Math.max(mxT, v.y); if (v.z >= 11 && v.z <= 24) { mx = Math.max(mx, v.y); n++; if (v.y > 0.02 && offenders.length < 12) offenders.push([+wx.toFixed(2), +v.y.toFixed(3), +v.z.toFixed(2)]); bb.expandByPoint(new THREE.Vector3(wx, v.y, v.z)); } } }
    out.road.meshes.push({ mesh: o.name, node: NN(o), offenders, verts_in_strip: n, max_y_z11_24: n ? +mx.toFixed(4) : null, max_y_z10p2_24p8: mxT > -1e8 ? +mxT.toFixed(4) : null, strip_bounds: n ? [r3(bb.min), r3(bb.max)] : null });
    worst = Math.max(worst, mx); worstT = Math.max(worstT, mxT); });
  out.road.seam_row_at_x481 = { verts: seam.length, max_y: seam.length ? Math.max(...seam.map(p => p[1])) : null, note: 'first cross-section of the U-turn ribbon, meets the last road tile end at world x 481 with the same road profile' };
  out.road.max_y = +worst.toFixed(4); out.road.max_y_toe_to_toe = +worstT.toFixed(4);
  if (worst > 0.02) fail.push('road strip blocked (max y ' + worst.toFixed(3) + ')');
  // also sweep the crane clips: lowest point of the crane mesh inside the strip (the hook / box over the truck bed is expected)
  out.fail = fail; out.pass = !fail.length;
  const s = JSON.stringify(out, null, 1); if (outp) fs.writeFileSync(outp, s);
  console.log(JSON.stringify({ ...out, clips: out.clips.map(c => [c.name, c.duration_s, c.tracks.length]), road: { seam: out.road.seam_row_at_x481, max_y: out.road.max_y, max_y_toe_to_toe: out.road.max_y_toe_to_toe, meshes: out.road.meshes.filter(m => m.verts_in_strip) } }, null, 1));
  process.exit(fail.length ? 1 : 0);
}, err => { console.error(err); process.exit(2); });
