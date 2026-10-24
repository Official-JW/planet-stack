// Transport-road clearance check v4 on REAL vertices (read only), WORLD coordinates from the approved station table
// (Cargo Dock (360, 0, -8) | Launch Pad 457 | Shipyard 960). Replaces the v1-v3 pad-local check that still assumed the old i*160 layout
// (pad 480 / Shipyard at pad +160 = 640).
// Crawler = ST-10A (picked 10/24 14:31; ST-10B shelved): body x -13.36..+15.64 rel to the ship axis, half width 13.56 (tracks |dz| 9.7-13.3,
// girders 9.5-13.5, fairings/rails to 13.56); cross girder bottom 4.2 m at rel x >= 11. Ship pick-up = pad Ship_Placeholder (457, -13).
// usage: node road_clearance.mjs out.json [pad.glb]
//   pad.glb default = AA2's Lv1 pad with the pipe end at the pad LEFT (launch_pad_game_lv1door.glb, Pipe_LaunchPad_End (430, 0.95, 2.6) world).
import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
await MeshoptDecoder.ready;
const R = '/workspace/planet-stack/';
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const crypto = await import('crypto'); const md5 = p => crypto.createHash('md5').update(fs.readFileSync(p)).digest('hex');
const ST = { CargoDock: [360, -8], LaunchPad: [457, 0], Shipyard: [960, 0] };
const PADX = ST.LaunchPad[0], ROAD_Z = -13, A = { x0: -13.36, x1: 15.64, half: 13.56, band: 9.5, cx: 11.0, cy: 4.2 };
const MARGIN = 3.75, HALF = A.half + MARGIN, SHOULDER = 2.6;            // running half width sized to ST-10A (+3.75 m each side, same margin as v3)
const PIPE_END = [430, 0.95, 2.6];
const NN = (o, S) => { while (o && o !== S && !o.name.replace(/^mesh_\d+(_\d+)?$/, '')) o = o.parent; return o && o !== S ? o.name : '?'; };
const padFile = process.argv[3] || R + 'art/3d/buildings/launch_pad/launch_pad_game_lv1door.glb';   // v4 run: snapshot of AA2's working copy bb532e07 (committed HEAD c527d5e3 still has the old +X pipe end)
const out = { version: 'v4 world', crawler: 'ST-10A', A, road: { z: ROAD_Z, half_running: +HALF.toFixed(2), shoulder: SHOULDER }, pad_file: padFile, pad_md5: md5(padFile), pad: {} };
const v = new THREE.Vector3();
// ---- pad: what the crawler swept volume meets on its way in from the road (rel x >= x0 at the pick-up), all tiers shown
const pad = await load(padFile); const S = pad.scene; S.traverse(n => { n.visible = true; }); S.updateMatrixWorld(true);
const hits = {}; let pipeNode = null;
S.traverse(o => { if (o.name === 'Pipe_LaunchPad_End') { const w = o.getWorldPosition(new THREE.Vector3()); pipeNode = [+(w.x + PADX).toFixed(2), +w.y.toFixed(2), +w.z.toFixed(2)]; }
  if (!o.isMesh) return; const nm = NN(o, S); if (nm === 'Ship_Placeholder' || nm === 'Cargo_Door') return;
  const p = o.geometry.attributes.position;
  for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i); v.applyMatrix4(o.matrixWorld); if (v.y < 0.3) continue;
    const wx = v.x + PADX, rx = v.x, dz = Math.abs(v.z - ROAD_Z); if (rx < A.x0 || dz > A.half) continue;
    const band = dz >= A.band; const cross = !band && rx >= A.cx && v.y > A.cy - 0.2; if (!band && !cross) continue;
    const key = nm + ' @ ' + (Math.floor(wx / 4) * 4) + ',' + (Math.floor(v.z / 4) * 4);
    const h = hits[key] || (hits[key] = { node: nm, x0: 1e9, x1: -1e9, z0: 1e9, z1: -1e9, ymax: 0, n: 0, where: band ? 'track/girder band' : 'cross girder' });
    h.x0 = Math.min(h.x0, wx); h.x1 = Math.max(h.x1, wx); h.z0 = Math.min(h.z0, v.z); h.z1 = Math.max(h.z1, v.z); h.ymax = Math.max(h.ymax, v.y); h.n++; } });
const L = Object.values(hits); let merged = true;
while (merged) { merged = false;
  for (let i = 0; i < L.length && !merged; i++) for (let j = i + 1; j < L.length && !merged; j++) { const a = L[i], b = L[j];
    if (a.node === b.node && a.x0 <= b.x1 + 1.0 && b.x0 <= a.x1 + 1.0 && a.z0 <= b.z1 + 1.0 && b.z0 <= a.z1 + 1.0) {
      Object.assign(a, { x0: Math.min(a.x0, b.x0), x1: Math.max(a.x1, b.x1), z0: Math.min(a.z0, b.z0), z1: Math.max(a.z1, b.z1), ymax: Math.max(a.ymax, b.ymax), n: a.n + b.n, where: a.where === b.where ? a.where : 'band + cross' }); L.splice(j, 1); merged = true; } } }
out.pad.A_world = L.map(h => ({ ...h, x0: +h.x0.toFixed(1), x1: +h.x1.toFixed(1), z0: +h.z0.toFixed(1), z1: +h.z1.toFixed(1), ymax: +h.ymax.toFixed(2) })).sort((a, b) => a.x0 - b.x0);
const pb = new THREE.Box3().setFromObject(S); out.pad.bbox_world = [[+(pb.min.x + PADX).toFixed(2), +pb.min.z.toFixed(2)], [+(pb.max.x + PADX).toFixed(2), +pb.max.z.toFixed(2)]];
out.pipe_end = { given: PIPE_END, node_in_file: pipeNode };
const fp = { x0: PADX + A.x0, x1: PADX + A.x1, z0: ROAD_Z - A.half, z1: ROAD_Z + A.half };     // crawler footprint at the pick-up
const dxp = Math.max(fp.x0 - PIPE_END[0], 0, PIPE_END[0] - fp.x1), dzp = Math.max(fp.z0 - PIPE_END[2], 0, PIPE_END[2] - fp.z1);
out.pipe_end.clear_of_crawler_at_pickup_m = +Math.hypot(dxp, dzp).toFixed(2);
// ---- Cargo Dock (compact_v3 at (360, -8)) vs the crawler's whole path (pick-up footprint east to the road)
const cd = await load(R + 'art/3d/buildings/cargo_dock/layout_v3/cargo_dock_compact_v3.glb'); cd.scene.traverse(o => { if (/^Tier_/.test(o.name)) o.visible = false; }); cd.scene.updateMatrixWorld(true);
const cb = new THREE.Box3(); cd.scene.traverseVisible(o => { if (o.isMesh) cb.expandByObject(o); });
const dock = { x0: cb.min.x + ST.CargoDock[0], x1: cb.max.x + ST.CargoDock[0], z0: cb.min.z + ST.CargoDock[1], z1: cb.max.z + ST.CargoDock[1] };
out.cargo_dock = { bbox_world: [[+dock.x0.toFixed(2), +dock.z0.toFixed(2)], [+dock.x1.toFixed(2), +dock.z1.toFixed(2)]], gap_to_crawler_path_m: +(fp.x0 - dock.x1).toFixed(2),
  gap_to_road_m: null };
// ---- Shipyard (shipyard_game.glb at 960): nothing in the road corridor west of the HB-10 apron (cells inside HB-10/RA-1 are listed by road_plan.py)
const sy = await load(R + 'art/3d/buildings/shipyard/shipyard_game.glb'); const T = sy.scene; T.traverse(n => { n.visible = true; }); T.updateMatrixWorld(true);
const padEdge = PADX + pb.max.x; out.road.pad_edge_x = +padEdge.toFixed(2); out.cargo_dock.gap_to_road_m = +(padEdge - dock.x1).toFixed(2);
const cz0 = ROAD_Z - HALF - SHOULDER, cz1 = ROAD_Z + HALF + SHOULDER; let syIn = { n: 0, xmin: 1e9 };
T.traverse(o => { if (!o.isMesh) return; const p = o.geometry.attributes.position;
  for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i); v.applyMatrix4(o.matrixWorld); if (v.y < 0.3) continue; const wx = v.x + ST.Shipyard[0];
    if (wx >= padEdge && v.z >= cz0 && v.z <= cz1) { syIn.n++; syIn.xmin = Math.min(syIn.xmin, wx); } } });
out.shipyard_in_corridor = { corridor_z: [+cz0.toFixed(2), +cz1.toFixed(2)], verts: syIn.n, first_x: syIn.n ? +syIn.xmin.toFixed(2) : null, note: 'first_x must be >= the HB-10 apron start (road_plan.py); cells beyond it are the HB-10 / RA-1 clear-out list' };
fs.writeFileSync(process.argv[2] || 'road_clearance.json', JSON.stringify(out, null, 1));
console.log('pad', out.pad_md5, 'hits', out.pad.A_world.length, 'pad bbox', JSON.stringify(out.pad.bbox_world), 'pipe', JSON.stringify(out.pipe_end), 'dock', JSON.stringify(out.cargo_dock), 'shipyard', JSON.stringify(out.shipyard_in_corridor));
for (const h of out.pad.A_world) console.log(' ', h.node, h.where, 'x', h.x0, h.x1, 'z', h.z0, h.z1, 'ymax', h.ymax, 'n', h.n);
