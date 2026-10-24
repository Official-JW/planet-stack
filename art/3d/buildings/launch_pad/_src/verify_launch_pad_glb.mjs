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
  // ROAD vs PAD footprint check in XZ (world, rest pose). Road = toe-to-toe band world z 10.2..24.8 for x 307..481 (shared road tiles)
  // + every triangle of Road_UTurn. Pad = every other mesh. Need: zero overlap AND >= 1 m of plain ground between them.
  const v = new THREE.Vector3(); const GAP = 1.0;
  const triPolys = (o) => { const pos = o.geometry.attributes.position, idx = o.geometry.index; const P = [];
    for (let i = 0; i < pos.count; i++) { o.getVertexPosition ? o.getVertexPosition(i, v) : v.fromBufferAttribute(pos, i); v.applyMatrix4(o.matrixWorld); P.push([v.x + WX, v.z, v.y]); }
    const T = []; const n = idx ? idx.count : pos.count; for (let k = 0; k < n; k += 3) { const a = idx ? idx.getX(k) : k, b = idx ? idx.getX(k + 1) : k + 1, c = idx ? idx.getX(k + 2) : k + 2; T.push([P[a], P[b], P[c]]); }
    return { P, T }; };
  const bbOf = (pg) => { let x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9; for (const p of pg) { x0 = Math.min(x0, p[0]); x1 = Math.max(x1, p[0]); z0 = Math.min(z0, p[1]); z1 = Math.max(z1, p[1]); } return [x0, x1, z0, z1]; };
  const segD = (p, a, b) => { const dx = b[0] - a[0], dz = b[1] - a[1], L = dx * dx + dz * dz; let t = L ? ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / L : 0; t = Math.max(0, Math.min(1, t)); return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dz); };
  const sat = (A, B) => { for (const Q of [A, B]) for (let i = 0; i < Q.length; i++) { const a = Q[i], b = Q[(i + 1) % Q.length]; const nx = b[1] - a[1], nz = a[0] - b[0]; if (!nx && !nz) continue;
      let a0 = 1e18, a1 = -1e18, b0 = 1e18, b1 = -1e18; for (const p of A) { const d = p[0] * nx + p[1] * nz; a0 = Math.min(a0, d); a1 = Math.max(a1, d); } for (const p of B) { const d = p[0] * nx + p[1] * nz; b0 = Math.min(b0, d); b1 = Math.max(b1, d); }
      if (a1 < b0 || b1 < a0) return false; } return true; };
  const dist = (A, B) => { if (sat(A, B)) return 0; let d = 1e9; for (const p of A) for (let i = 0; i < B.length; i++) d = Math.min(d, segD(p, B[i], B[(i + 1) % B.length])); for (const p of B) for (let i = 0; i < A.length; i++) d = Math.min(d, segD(p, A[i], A[(i + 1) % A.length])); return d; };
  const road = [{ name: 'road band (tiles, toe-to-toe)', poly: [[307, 10.2], [481, 10.2], [481, 24.8], [307, 24.8]] }];
  const pads = [];
  S.traverse(o => { if (!o.isMesh) return; const { T } = triPolys(o); const nn = NN(o);
    if (nn === 'Road_UTurn') T.forEach((t, k) => road.push({ name: 'Road_UTurn tri ' + k, poly: t.map(p => [p[0], p[1]]) })); else pads.push({ mesh: o.name, node: nn, T }); });
  road.forEach(r => r.bb = bbOf(r.poly));
  out.overlap = { rule: 'XZ footprint of every pad mesh vs road band (world x 307-481, z 10.2-24.8) and every Road_UTurn triangle: 0 overlaps, min gap >= ' + GAP + ' m',
                  road_pieces: road.length, pad_meshes: pads.length, pad_tris: 0, overlaps: 0, under_gap: 0, min_gap_m: 1e9, nearest: null, per_node: {} };
  for (const m of pads) { let md = 1e9, near = null;
    for (const t of m.T) { out.overlap.pad_tris++; const tp = t.map(p => [p[0], p[1]]); const tb = bbOf(tp);
      for (const r of road) { if (tb[0] > r.bb[1] + 3 || tb[1] < r.bb[0] - 3 || tb[2] > r.bb[3] + 3 || tb[3] < r.bb[2] - 3) continue;
        const d = dist(tp, r.poly); if (d === 0) out.overlap.overlaps++; if (d < GAP) out.overlap.under_gap++; if (d < md) { md = d; near = [r.name, tp.map(p => [+p[0].toFixed(2), +p[1].toFixed(2)])]; } } }
    const k = m.node; const pn = out.overlap.per_node[k] || { min_gap_m: 1e9 }; if (md < pn.min_gap_m) { pn.min_gap_m = +md.toFixed(3); pn.nearest = near; } out.overlap.per_node[k] = pn;
    if (md < out.overlap.min_gap_m) { out.overlap.min_gap_m = +md.toFixed(3); out.overlap.nearest = { node: k, mesh: m.mesh, road: near && near[0], tri_xz: near && near[1] }; } }
  for (const k in out.overlap.per_node) if (out.overlap.per_node[k].min_gap_m > 1e8) out.overlap.per_node[k] = { min_gap_m: 'none within 3 m bbox' };
  if (out.overlap.overlaps) fail.push('pad overlaps road: ' + out.overlap.overlaps); if (out.overlap.under_gap) fail.push('pad closer than 1 m to road: ' + out.overlap.under_gap);
  // node bounds (world) - e.g. proves no backdrop hills are in the GLB
  out.node_bounds = {}; S.traverse(o => { if (!o.isMesh) return; const k = NN(o); const b = out.node_bounds[k] || { min: [1e9, 1e9, 1e9], max: [-1e9, -1e9, -1e9] };
    const pos = o.geometry.attributes.position; for (let i = 0; i < pos.count; i++) { o.getVertexPosition ? o.getVertexPosition(i, v) : v.fromBufferAttribute(pos, i); v.applyMatrix4(o.matrixWorld); const w = [v.x + WX, v.y, v.z];
      for (let a = 0; a < 3; a++) { b.min[a] = Math.min(b.min[a], +w[a].toFixed(2)); b.max[a] = Math.max(b.max[a], +w[a].toFixed(2)); } } out.node_bounds[k] = b; });
  // also sweep the crane clips: lowest point of the crane mesh inside the strip (the hook / box over the truck bed is expected)
  out.fail = fail; out.pass = !fail.length;
  const s = JSON.stringify(out, null, 1); if (outp) fs.writeFileSync(outp, s);
  console.log(JSON.stringify({ ...out, clips: out.clips.map(c => [c.name, c.duration_s, c.tracks.length]), overlap: { ...out.overlap, per_node: undefined }, node_bounds: out.node_bounds }, null, 1));
  process.exit(fail.length ? 1 : 0);
}, err => { console.error(err); process.exit(2); });
