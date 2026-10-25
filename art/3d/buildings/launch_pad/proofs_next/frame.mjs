// light software raster (no GPU, no Cycles) of the 375x667 game frame: pad + FB-05 at Truck_Stop + boxes (one on the hook at crane_lift end) + receiver
import fs from 'fs'; import path from 'path'; const NM = process.env.NODE_PATH; const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js'); const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js'); await MeshoptDecoder.ready;
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const [F, OUTRAW, OUTJ] = process.argv.slice(2); const PROPS = '/workspace/planet-stack/art/3d/props'; const w = 375, h = 667, SS = 2, W2 = w * SS, H2 = h * SS;
const g = await load(F), S = g.scene; S.updateMatrixWorld(true); const WP = n => S.getObjectByName(n).getWorldPosition(new THREE.Vector3());
const clip = g.animations.find(c => c.name === 'crane_lift'); const mx = new THREE.AnimationMixer(S); const ac = mx.clipAction(clip); ac.setLoop(THREE.LoopOnce); ac.clampWhenFinished = true; ac.play(); mx.setTime(clip.duration); S.updateMatrixWorld(true);
const extra = new THREE.Group(); S.add(extra);
const tr = (await load(PROPS + '/fb05/fb05_game.glb')).scene; tr.position.copy(WP('Truck_Stop')); tr.name = 'TRUCK'; extra.add(tr);
const hb = (await load(PROPS + '/cargo_box/cargo_box_game.glb')).scene; const hk = WP('Hook'); hb.position.set(hk.x, hk.y - 1.5, hk.z); hb.name = 'TRUCK_BOX_HOOK'; extra.add(hb);
const b2 = (await load(PROPS + '/cargo_box/cargo_box_game.glb')).scene; b2.position.copy(WP('Pick_Point_02')); b2.name = 'TRUCK_BOX2'; extra.add(b2);
const rg = (await load(path.resolve(PROPS, '../crew/receiver/receiver_game.glb'))).scene; rg.position.copy(WP('Receiver_Spot')); rg.rotation.y = (S.getObjectByName('Receiver_Spot').userData.yaw_deg || 0) * Math.PI / 180; rg.name = 'Receiver'; extra.add(rg);
S.updateMatrixWorld(true);
const ct = S.getObjectByName('Cam_Target'), c = WP('Cam_Target'), fw = ct.userData.frame_w; const e = 18 * Math.PI / 180, d = (fw / 2) / (Math.tan(19 * Math.PI / 180) * (w / h));
const C = new THREE.PerspectiveCamera(38, w / h, 0.5, 3000); C.position.set(c.x, c.y + d * Math.sin(e), c.z + d * Math.cos(e)); C.lookAt(c); C.updateMatrixWorld(); C.updateProjectionMatrix();
const M = new THREE.Matrix4().multiplyMatrices(C.projectionMatrix, C.matrixWorldInverse);
const proj = v => { const p = v.clone().applyMatrix4(M); return [(p.x + 1) / 2 * W2, (1 - p.y) / 2 * H2, p.z]; };
const grp = o => { for (let q = o; q; q = q.parent) { if (/^TRUCK/.test(q.name)) return 'Truck'; if (q.name === 'Receiver') return 'Receiver'; if (q.name === 'Cargo_Door') return 'Cargo_Door'; } let q = o; while (q && q !== S && !q.name.replace(/^mesh_\d+(_\d+)?$/, '')) q = q.parent; return q && q !== S ? q.name : '?'; };
const ids = {}; const idOf = n => ids[n] ?? (ids[n] = Object.keys(ids).length + 1);
const col = new Float32Array(W2 * H2 * 3).fill(0.05), zb = new Float32Array(W2 * H2).fill(1e9), idb = new Uint8Array(W2 * H2), zbNT = new Float32Array(W2 * H2).fill(1e9), idNT = new Uint8Array(W2 * H2);
const L = new THREE.Vector3(-0.4, 0.8, 0.45).normalize(); const a = new THREE.Vector3(), b = new THREE.Vector3(), cc = new THREE.Vector3(), nrm = new THREE.Vector3();
S.traverse(o => { if (!o.isMesh) return; const gname = grp(o); const id = idOf(gname); const truck = gname === 'Truck'; const pos = o.geometry.attributes.position, ci = o.geometry.attributes.color, ix = o.geometry.index;
  const mc = o.material.color || new THREE.Color(1, 1, 1); const n = ix ? ix.count : pos.count; const V = i => (o.getVertexPosition ? o.getVertexPosition(i, new THREE.Vector3()) : new THREE.Vector3().fromBufferAttribute(pos, i)).applyMatrix4(o.matrixWorld);
  for (let k = 0; k < n; k += 3) { const i0 = ix ? ix.getX(k) : k, i1 = ix ? ix.getX(k + 1) : k + 1, i2 = ix ? ix.getX(k + 2) : k + 2; a.copy(V(i0)); b.copy(V(i1)); cc.copy(V(i2));
    nrm.subVectors(b, a).cross(cc.clone().sub(a)).normalize(); const sh = 0.3 + 0.7 * Math.abs(nrm.dot(L)); const base = ci ? [ci.getX(i0), ci.getY(i0), ci.getZ(i0)] : [1, 1, 1]; const em = o.material.emissive && (o.material.emissive.r + o.material.emissive.g + o.material.emissive.b) > 0.3;
    const rgb = base.map((x, j) => Math.min(1, x * [mc.r, mc.g, mc.b][j] * (em ? 1.4 : sh)));
    const P = [proj(a), proj(b), proj(cc)]; if (P.some(p => p[2] < -1 || p[2] > 1)) continue;
    const x0 = Math.max(0, Math.floor(Math.min(P[0][0], P[1][0], P[2][0]))), x1 = Math.min(W2 - 1, Math.ceil(Math.max(P[0][0], P[1][0], P[2][0]))), y0 = Math.max(0, Math.floor(Math.min(P[0][1], P[1][1], P[2][1]))), y1 = Math.min(H2 - 1, Math.ceil(Math.max(P[0][1], P[1][1], P[2][1])));
    const ar = (P[1][0] - P[0][0]) * (P[2][1] - P[0][1]) - (P[2][0] - P[0][0]) * (P[1][1] - P[0][1]); if (Math.abs(ar) < 1e-9) continue;
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) { const px = x + 0.5, py = y + 0.5;
      const w0 = ((P[1][0] - px) * (P[2][1] - py) - (P[2][0] - px) * (P[1][1] - py)) / ar, w1 = ((P[2][0] - px) * (P[0][1] - py) - (P[0][0] - px) * (P[2][1] - py)) / ar, w2 = 1 - w0 - w1; if (w0 < 0 || w1 < 0 || w2 < 0) continue;
      const z = w0 * P[0][2] + w1 * P[1][2] + w2 * P[2][2]; const q = y * W2 + x;
      if (z < zb[q]) { zb[q] = z; idb[q] = id; col[3 * q] = rgb[0]; col[3 * q + 1] = rgb[1]; col[3 * q + 2] = rgb[2]; }
      if (!truck && z < zbNT[q]) { zbNT[q] = z; idNT[q] = id; } } } });
// coverage: pixels of a group visible without the truck that the truck hides
const inv = Object.fromEntries(Object.entries(ids).map(([k, v]) => [v, k])); const tid = ids.Truck; const cov = {};
for (let q = 0; q < W2 * H2; q++) { const k = inv[idNT[q]]; if (!k) continue; const r = cov[k] || (cov[k] = [0, 0]); r[0]++; if (idb[q] === tid) r[1]++; }
const bayPts = []; for (let i = 1; i <= 12; i++) { const p = WP('Bay_Slot_' + String(i).padStart(2, '0')); for (const sx of [-1.2, 1.2]) for (const sz of [-0.67, 0.67]) bayPts.push(proj(new THREE.Vector3(p.x + sx, p.y, p.z + sz))); }
const bx = [Math.min(...bayPts.map(p => p[0])), Math.max(...bayPts.map(p => p[0])), Math.min(...bayPts.map(p => p[1])), Math.max(...bayPts.map(p => p[1]))]; let bt = 0, bc = 0;
for (let y = Math.max(0, Math.floor(bx[2])); y < Math.min(H2, bx[3]); y++) for (let x = Math.max(0, Math.floor(bx[0])); x < Math.min(W2, bx[1]); x++) { bt++; if (idb[y * W2 + x] === tid) bc++; }
const pt = n => { const p = proj(WP(n)); const x = Math.round(p[0]), y = Math.round(p[1]); const q = y * W2 + x; return { px: [+(p[0] / SS).toFixed(1), +(p[1] / SS).toFixed(1)], truck_on_top: x >= 0 && y >= 0 && x < W2 && y < H2 && idb[q] === tid && zb[q] < p[2] }; };
const tb = [1e9, -1e9, 1e9, -1e9]; for (let q = 0; q < W2 * H2; q++) if (idb[q] === tid) { const x = q % W2, y = (q / W2) | 0; tb[0] = Math.min(tb[0], x); tb[1] = Math.max(tb[1], x); tb[2] = Math.min(tb[2], y); tb[3] = Math.max(tb[3], y); }
const out = { frame: '375x667 game cam (qa3d camera math), software raster x' + SS + ' supersample, crane posed at crane_lift end (box on the hook), FB-05 at Truck_Stop, box 2 on Pick_Point_02',
  cam: [c.x, c.y, c.z, fw], truck_px_bbox: tb.map(v => +(v / SS).toFixed(1)), coverage_pct_of_group_pixels: Object.fromEntries(Object.entries(cov).filter(([k, r]) => r[1] > 0 || ['Cargo_Door', 'Receiver', 'Ship_Placeholder', 'Pad_Base'].includes(k)).map(([k, r]) => [k, { px: r[0] / SS / SS, hidden_by_truck_pct: +(100 * r[1] / r[0]).toFixed(2) }])),
  cargo_bay_slots_screen_box_hidden_pct: +(100 * bc / Math.max(1, bt)).toFixed(2), entrances: { Ladder_Foot: pt('Ladder_Foot'), Hold_Door: pt('Hold_Door'), Receiver_Spot: pt('Receiver_Spot'), Cargo_Door_node: pt('Cargo_Door') } };
const img = Buffer.alloc(w * h * 3); for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) for (let j = 0; j < 3; j++) { let s = 0; for (let dy = 0; dy < SS; dy++) for (let dx = 0; dx < SS; dx++) s += col[3 * ((y * SS + dy) * W2 + x * SS + dx) + j]; img[3 * (y * w + x) + j] = Math.round(255 * Math.pow(s / SS / SS, 1 / 2.2)); }
fs.writeFileSync(OUTRAW, img); fs.writeFileSync(OUTJ, JSON.stringify(out, null, 1)); console.log(JSON.stringify(out));
