// lane B clearance scan + 375x667 game-cam projection flags. node scan.mjs DOCK.glb REFINERY.glb CRANE.glb
import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules'; const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js'); const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js'); await MeshoptDecoder.ready;
const load = p => { const b = fs.readFileSync(p); return new Promise((r, j) => { const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', r, j); }); };
const [, , DK, RF, CR] = process.argv; const PAD = '/workspace/planet-stack/qa3d-next/models/launch_pad_db78a6f7.glb', FB = '/workspace/planet-stack/qa3d-next/models/fb05_195461ef.glb';
const L = JSON.parse(fs.readFileSync('lanes_B.json'));
const st = {}; for (const [k, f, o] of [['dock', DK, [480, 0, 0]], ['refinery', RF, [320, 0, 0]], ['rc1', CR, [311, 0, 17.5]], ['pad', PAD, [640, 0, 0]]]) {
  const g = await load(f); g.scene.position.set(...o); g.scene.updateMatrixWorld(true); st[k] = g.scene; st[k].userData.draws = (() => { let n = 0; g.scene.traverse(m => { if (m.isMesh) n++; }); return n; })(); }
const hid = n => { for (let q = n; q; q = q.parent) if (!q.visible) return true; return false; };
// corridor zones (world x/z rects): lane strips are road 4.6 m wide (+0.5 truck margin) + 1 m clear = band (z 19.2..35.8) as CPH.padRoad
const Z = [{ n: 'lane band x 318-641 (z 20.2-34.8 +1 m)', x: [318, 641], z: [19.2, 35.8] }, { n: 'Refinery U-turn x 287-318', x: [287.2, 318], z: [19.2, 35.8] },
  { n: 'Dock bay road strip x 464-500 (z 17.1-21.7)', x: [464, 500], z: [17.1, 21.7] }];
const res = {}; const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
for (const [k, S] of Object.entries(st)) { const hits = {};
  S.traverse(m => { if (!m.isMesh || hid(m)) return; const key = (m.parent && m.parent.name && !/^(Scene|DockTankFarm)$/.test(m.parent.name) ? m.parent.name : m.name) || m.name; const road = /road/i.test(key + m.name);
    const P = m.geometry.attributes.position, I = m.geometry.index, n = I ? I.count : P.count, ix = q => I ? I.getX(q) : q;
    for (let t = 0; t < n; t += 3) { a.fromBufferAttribute(P, ix(t)).applyMatrix4(m.matrixWorld); b.fromBufferAttribute(P, ix(t + 1)).applyMatrix4(m.matrixWorld); c.fromBufferAttribute(P, ix(t + 2)).applyMatrix4(m.matrixWorld);
      const s = Math.max(1, Math.ceil(Math.max(a.distanceTo(b), b.distanceTo(c), c.distanceTo(a)) / 0.2));
      for (let i = 0; i <= s; i++) for (let j = 0; j <= s - i; j++) { const u = i / s, v = j / s, w = 1 - u - v, x = a.x * w + b.x * u + c.x * v, z = a.z * w + b.z * u + c.z * v, y = a.y * w + b.y * u + c.y * v;
        for (const zn of Z) if (x > zn.x[0] && x < zn.x[1] && z > zn.z[0] && z < zn.z[1]) { const cls = road ? 'road' : y >= 5.0 ? 'overhead' : 'GROUND';
          const h = hits[zn.n + '|' + key + '|' + cls] || (hits[zn.n + '|' + key + '|' + cls] = { x: [1e9, -1e9], z: [1e9, -1e9], y: [1e9, -1e9] }); h.x = [Math.min(h.x[0], x), Math.max(h.x[1], x)]; h.z = [Math.min(h.z[0], z), Math.max(h.z[1], z)]; h.y = [Math.min(h.y[0], y), Math.max(h.y[1], y)]; } } } });
  res[k] = Object.fromEntries(Object.entries(hits).map(([q, h]) => [q, { x: h.x.map(v => +v.toFixed(2)), z: h.z.map(v => +v.toFixed(2)), y: h.y.map(v => +v.toFixed(2)) }])); }
// nearest non-road ground geometry to each lane edge (margins)
const draws = Object.fromEntries(Object.entries(st).map(([k, S]) => [k, S.userData.draws]));
// FB-05 box
const fb = (await load(FB)).scene; fb.updateMatrixWorld(true); const fbb = new THREE.Box3().setFromObject(fb);
const W = 375, H = 667, HUD = H * 0.82;
const CAMS = { refinery: { ct: [313.1, 2.08, 13.55], fw: 37.5 }, dock: { ct: [492, 1.5, 2], fw: 66 }, pad: { ct: [640, 4, -0.7], fw: 78.25 } };
const cam = (k) => { const C = CAMS[k], cm = new THREE.PerspectiveCamera(38, W / H, 0.5, 4000), e = THREE.MathUtils.degToRad(18), d = (C.fw / 2) / (Math.tan(THREE.MathUtils.degToRad(19)) * W / H);
  cm.position.set(C.ct[0], C.ct[1] + d * Math.sin(e), C.ct[2] + d * Math.cos(e)); cm.lookAt(...C.ct); cm.updateMatrixWorld(); cm.updateProjectionMatrix(); return { cm, d, pos: cm.position.toArray().map(v => +v.toFixed(2)) }; };
const sbox = (cm, box) => { let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9; for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) { const p = new THREE.Vector3(x, y, z).project(cm); const sx = (p.x + 1) / 2 * W, sy = (1 - p.y) / 2 * H; x0 = Math.min(x0, sx); x1 = Math.max(x1, sx); y0 = Math.min(y0, sy); y1 = Math.max(y1, sy); } return [x0, x1, y0, y1].map(v => +v.toFixed(1)); };
const truckBox = (x, z, yaw) => { const bx = fbb.clone(); if (yaw) { const c2 = bx.getCenter(new THREE.Vector3()), s2 = bx.getSize(new THREE.Vector3()); bx.setFromCenterAndSize(new THREE.Vector3(-c2.x, c2.y, -c2.z), s2); } bx.min.x += x; bx.max.x += x; bx.min.z += z; bx.max.z += z; return bx; };
const nodeBox = (S, names) => { const bx = new THREE.Box3(); for (const n of names) { const o = S.getObjectByName(n); if (o) bx.expandByObject(o); } return bx; };
const ENTR = { refinery: [['RB dump bay / intake (Truck_Dump ±4 m, y 0-6)', new THREE.Box3(new THREE.Vector3(316, 0, -3), new THREE.Vector3(328, 6, 3))], ['RC-1 pallet', new THREE.Box3(new THREE.Vector3(301.85, 0, 15.82), new THREE.Vector3(308, 3.15, 19.18))]],
  dock: [['Dock_Door', nodeBox(st.dock, ['Dock_Door'])]], pad: [['pad cargo bay + Receiver_Spot (x 628-640, z 3.6-9.2, y 0-4)', new THREE.Box3(new THREE.Vector3(628, 0, 3.6), new THREE.Vector3(640, 4, 9.2))]] };
const TR = { refinery: [['out z23 @ Truck_Park', 318, 23, 0], ['back z32', 313, 32, 1]], dock: [['bay z19.4 @ Truck_Stop_Dock', 480, 19.4, 0], ['back z32', 486, 32, 1]], pad: [['pad spur z19.75 @ Truck_Stop (proposed)', 639.5, 19.75, 0], ['back z32', 630, 32, 1]] };
const ov = (p, q) => Math.max(0, Math.min(p[1], q[1]) - Math.max(p[0], q[0])) * Math.max(0, Math.min(p[3], q[3]) - Math.max(p[2], q[2]));
const frames = {};
for (const k of Object.keys(CAMS)) { const { cm, d, pos } = cam(k); const f = frames[k] = { cam_pos: pos, ct: CAMS[k].ct, fw: CAMS[k].fw, d: +d.toFixed(2), trucks: [] };
  for (const [n, x, z, yaw] of TR[k]) { const s = truckBox(x, z, yaw), sb = sbox(cm, s), flags = [];
    if (sb[3] > HUD) flags.push(`bottom HUD: truck reaches y ${sb[3]} > ${HUD.toFixed(0)}`); if (sb[0] < 0 || sb[1] > W) flags.push('off-screen x');
    for (const [en, eb] of ENTR[k]) { const es = sbox(cm, eb), o = ov(sb, es), ar = (es[1] - es[0]) * (es[3] - es[2]); if (o > 0) { // depth test: truck in front of entrance?
        flags.push(`covers ${en}: ${(100 * o / ar).toFixed(0)}% of its screen box`); } }
    f.trucks.push({ n, root: [x, z], screen: sb, flags }); }
  f.entrances = ENTR[k].map(([en, eb]) => [en, sbox(cm, eb)]); }
const out = { scan: res, draws, fb05_bbox: [fbb.min.toArray(), fbb.max.toArray()].map(v => v.map(q => +q.toFixed(2))), frames };
fs.writeFileSync('scan_B.json', JSON.stringify(out, null, 1)); console.log(JSON.stringify(out, null, 1));
