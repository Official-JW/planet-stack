// GATE FINAL (A&A 00:31), from 24620c3e: ladder rails + rungs are the real mesh too (wb.js pieces; no capsules / boxes); rails (incl. ladder_top_rails) FAIL only on
//   depth > 5 mm (= wb.js), the 3 cm clearance on rails is a report-only WARNING (summary.warnings near-miss list); wb_equivalent rung = every vertex, rung_nonhand = non-hand (= wb.js).
// WB-MESH (A&A 00:15): Playtester wb.js 0cc51f8d is the official check. Built from committed a7cb359 (5bbc2f66) + the A&A 11:50 rail-top / hidden-node fixes (2ceab7e2).
//   Cage hoops + verticals, kerb frame, gate, both landing braces and the guard posts/top rails (incl. the fused post) are scored against the REAL mesh
//   (wb.js/bars2.py geometry: convex pieces; inside = -depth to the nearest face, outside = exact point-to-triangle distance). No cage capsules; analytic
//   frame_side/frame_outer/lid*/brace/rail/rail_post are dropped when the mesh has those parts. summary.wb_equivalent = wb.js metric (depth > 5 mm) per crew x label.
// PLATE (A&A / Director 10/24 21:47-21:48): copy of landing_clear.mjs 50dd4b68 + the hatch floor plate as a resting surface for still soles ONLY inside the plate's
//   real footprint (point-in-polygon on the sole vertex u,t = pad xz, footprint taken from the mesh), same 0-5 mm sink allowance as the deck. Off the plate,
//   or for any other geometry (hatch sill, jambs, hull, ...), the 3 cm rule is unchanged. PLATE_TEST=1 runs the planted-sole/hand harness and exits.
// CAGE FROM MESH (A&A 22:50): the 12 hoops + 3 verticals are read from the pad's Ship_Placeholder mesh every run (connected components around the ladder;
//   fails loudly unless exactly 12 hoops x 7 ring stations and 3 verticals). Capsules = consecutive ring-station centroids, radius = max ring-vertex distance;
//   cage triangles are labelled cage_hoop / cage_bar only (never hull / other_ship). No hard-coded cage size.
// CREW=1,2 (A&A 21:51): score only those crew (all crew still simulated); summary.all_crew always has the all-crew score.
// HELD GRIP (A&A 22:23, = Playtester frozen wb.js 0e8a30b7 gradeHands): a hand/finger vertex (bone /(^|_)(Hand|Finger|Thumb|Index|Middle|Ring|Pinky|Palm)/i) may sink
//   <= 10 mm into a rung ONLY if it is the rung that hand holds (rung nearest the centroid of that hand's vertices) and the hand is HELD: max distance between any two
//   hand-bone positions over +-0.1 s (+-HOLD_HALF samples, same clip run, all present) <= 5 mm, and the held rung is the same throughout. Else 5 mm. Feet keep isStill.
// v3.1 (art lead rulings 02:15): hand grips may sink <= 5 mm into a rail/rung and the rod axis must not lie inside the hand's skin (rod-through-hand test,
//   generalized winding number); resting soles (still) on the deck or a rung top exempt within 0-5 mm sink; everything else >= 3 cm.
// v3: 3 cm rule on every Ship-node triangle (spatial grid), ladder rails/rungs/cage added; exemptions = planted soles on deck, hands gripping ladder.
// v2: per-crew phase times + hull wall / hatch jamb + sole support + sole gap.
// Clearance of the 4 skinned climbers (all clips back to back, 15 Hz, pad-local) against the hatch landing solids (analytic SDF, mirrors
// lp_stainless_ship.py), plus a check that the GLB's landing triangles sit on those solids. Usage: node landing_clear.mjs crew.glb pad.glb out.json
//   or env CREW_GLB= PAD_GLB= OUT= (args win; defaults: repo crew_boarding.glb, launch_pad_next.glb, ./landing_clear_out.json); NODE_MODULES= (three), HZ= (sample rate, default 30; HZ=1 = smoke test), TIMINGS=
import fs from 'fs';
const NM = process.env.NODE_MODULES || '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
await MeshoptDecoder.ready;
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const HERE = new URL('.', import.meta.url).pathname, A_ = process.argv.slice(2);
const crewF = A_[0] || process.env.CREW_GLB || HERE + '../../../crew/boarding/crew_boarding.glb', padF = A_[1] || process.env.PAD_GLB || HERE + '../launch_pad_next.glb', outF = A_[2] || process.env.OUT || 'landing_clear_out.json';
console.error('landing_clear: crew', crewF, '| pad', padF, '| out', outF, '| hz', process.env.HZ || 30);
const pad = (await load(padF)).scene; pad.updateMatrixWorld(true);
// ---- hidden-node skip (A&A 11:50): any node with extras.hidden_by_default === true or a name matching /^Tier_\d+/, and everything under it, wherever it sits, is never read
const SKIP_RE = /^Tier_\d+/, SKIP = new Set(), SKIPPED = [];
{ const triN = o => o.isMesh ? (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3 : 0;
  const walk = (o, why, path) => { const p = path ? path + '/' + o.name : o.name; const own = o.userData && o.userData.hidden_by_default === true ? 'extras.hidden_by_default' : SKIP_RE.test(o.name || '') ? 'name /^Tier_\\d+/' : null; const w = why || own;
    if (w && o !== pad) { SKIP.add(o); SKIPPED.push({ node: o.name, type: o.type, tris: triN(o), path: p, reason: own && !why ? own : 'under ' + why.split(' (')[0] }); }
    for (const c of o.children) walk(c, w && o !== pad ? (why || o.name + ' (' + own + ')') : null, o === pad ? '' : p); };
  walk(pad, null, ''); }
const padGet = nm => { let r = null; pad.traverse(o => { if (!r && o.name === nm && !SKIP.has(o)) r = o; }); if (!r) throw new Error('node ' + nm + ' not found (or only under a skipped hidden node) in ' + padF); return r; };
const SHIP_NODE = padGet('Ship_Placeholder'); let SHIP_MESH = null; SHIP_NODE.traverse(o => { if (o.isMesh && !SHIP_MESH && !SKIP.has(o)) SHIP_MESH = o; });
if (!SHIP_MESH) throw new Error('no visible mesh under Ship_Placeholder in ' + padF);
console.error('landing_clear: skipped hidden nodes: ' + SKIPPED.length + (SKIPPED.length ? ' (' + SKIPPED.filter(x => !x.reason.startsWith('under')).map(x => x.node).join(', ') + ' and their subtrees)' : '') + '; scored mesh ' + SHIP_MESH.name);
const C = padGet('Ship_Center').getWorldPosition(new THREE.Vector3());
const LF = padGet('Ladder_Foot').getWorldPosition(new THREE.Vector3());
const LAD = 330 * Math.PI / 180, LU = [Math.cos(LAD), Math.sin(LAD)], LT = [-LU[1], LU[0]];
const toUTZ = v => { const bx = v.x - C.x, by = -(v.z - C.z); return [bx * LU[0] + by * LU[1], bx * LT[0] + by * LT[1], v.y]; };
// ---- cage from the mesh (12 hoops, 3 verticals): connected components of the Ship_Placeholder mesh in the ladder-cage box
const CAGE = (() => { const ship = SHIP_NODE, m = SHIP_MESH;
  const pos = m.geometry.attributes.position, idx = m.geometry.index, X = [], v = new THREE.Vector3(); for (let i = 0; i < pos.count; i++) X.push(toUTZ(v.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld)));
  const P = Int32Array.from({ length: pos.count }, (_, i) => i); const fd = i => { while (P[i] !== i) { P[i] = P[P[i]]; i = P[i]; } return i; };
  for (let k = 0; k < idx.count; k += 3) { const a = fd(idx.getX(k)); P[fd(idx.getX(k + 1))] = a; P[fd(idx.getX(k + 2))] = a; }
  const comps = new Map(); for (let i = 0; i < pos.count; i++) { const r = fd(i); (comps.get(r) || comps.set(r, []).get(r)).push(i); }
  const hoops = [], bars = [], verts = new Map();   // verts: vertex index -> 'cage_hoop' | 'cage_bar'
  for (const vs of comps.values()) { const lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9]; for (const i of vs) for (let c = 0; c < 3; c++) { lo[c] = Math.min(lo[c], X[i][c]); hi[c] = Math.max(hi[c], X[i][c]); }
    if (lo[0] < 4.3 || hi[0] > 5.6 || Math.max(-lo[1], hi[1]) > 0.8 || hi[2] < 1) continue;   // ladder-cage box (outboard of the ladder axis u 4.45)
    if (hi[2] - lo[2] < 0.1 && hi[1] - lo[1] > 0.8 && hi[0] - lo[0] > 0.6) {   // hoop: flat ring spanning the ladder; stations = clusters of ring vertices (< 8 cm of the first; stations are >= 25 cm apart)
      const st = []; for (const i of vs) { const q = X[i]; let s_ = st.find(s => Math.hypot(q[0] - s.seed[0], q[1] - s.seed[1], q[2] - s.seed[2]) < 0.08); if (!s_) st.push(s_ = { seed: q, ix: [] }); s_.ix.push(i); }
      for (const s_ of st) { s_.c = [0, 1, 2].map(c => s_.ix.reduce((a, i) => a + X[i][c], 0) / s_.ix.length); s_.r = Math.max(...s_.ix.map(i => Math.hypot(X[i][0] - s_.c[0], X[i][1] - s_.c[1], X[i][2] - s_.c[2]))); }
      st.sort((a, b) => b.c[1] - a.c[1]); const ord = [st.shift()]; while (st.length) { const l = ord[ord.length - 1].c; let bi = 0, bd = 1e9; st.forEach((s_, k) => { const d = Math.hypot(s_.c[0] - l[0], s_.c[1] - l[1]); if (d < bd) { bd = d; bi = k; } }); ord.push(st.splice(bi, 1)[0]); }   // chain from the +t end
      hoops.push({ z: ord.reduce((a, s_) => a + s_.c[2], 0) / ord.length, st: ord.map(s_ => s_.c), r: Math.max(...ord.map(s_ => s_.r)), n_st: ord.map(s_ => s_.ix.length), vs }); vs.forEach(i => verts.set(i, 'cage_hoop')); }
    else if (hi[2] - lo[2] > 10 && hi[0] - lo[0] < 0.08 && hi[1] - lo[1] < 0.08 && lo[0] > 4.6) {   // vertical: long thin prism outboard of the ladder
      const cu = vs.reduce((a, i) => a + X[i][0], 0) / vs.length, ct = vs.reduce((a, i) => a + X[i][1], 0) / vs.length; bars.push({ u: cu, t: ct, z0: lo[2], z1: hi[2], r: Math.max(...vs.map(i => Math.hypot(X[i][0] - cu, X[i][1] - ct))), vs }); vs.forEach(i => verts.set(i, 'cage_bar')); } }
  hoops.sort((a, b) => a.z - b.z); bars.sort((a, b) => a.t - b.t);
  if (hoops.length !== 12 || bars.length !== 3 || hoops.some(h => h.st.length !== 7)) throw new Error('CAGE NOT FOUND in ' + padF + ': hoops ' + hoops.length + ' (stations ' + hoops.map(h => h.st.length) + '), verticals ' + bars.length + ' - expected 12 hoops x 7 stations and 3 verticals');
  return { hoops, bars, verts, index_range: [Math.min(...verts.keys()), Math.max(...verts.keys())] }; })();
console.error('landing_clear: cage from mesh: 12 hoops z ' + CAGE.hoops[0].z.toFixed(3) + '..' + CAGE.hoops[11].z.toFixed(3) + ', 3 verticals, ' + CAGE.verts.size + ' verts (index ' + CAGE.index_range.join('-') + ')');
// ---- ladder rails from the mesh (A&A 11:50): the rail capsule ends FLUSH at the real rail top (flat cut, no hemispherical end cap); bottom unchanged (capsule from LTOP)
const RAIL = (() => { const m = SHIP_MESH, pos = m.geometry.attributes.position, idx = m.geometry.index, v = new THREE.Vector3(), X = []; for (let i = 0; i < pos.count; i++) X.push(toUTZ(v.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld)));
  const P = Int32Array.from({ length: pos.count }, (_, i) => i); const fd = i => { while (P[i] !== i) { P[i] = P[P[i]]; i = P[i]; } return i; };
  for (let k = 0; k < idx.count; k += 3) { const a = fd(idx.getX(k)); P[fd(idx.getX(k + 1))] = a; P[fd(idx.getX(k + 2))] = a; }
  const comps = new Map(); for (let i = 0; i < pos.count; i++) { const r = fd(i); (comps.get(r) || comps.set(r, []).get(r)).push(i); }
  const out = {}; for (const vs of comps.values()) { const lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9]; for (const i of vs) for (let c = 0; c < 3; c++) { lo[c] = Math.min(lo[c], X[i][c]); hi[c] = Math.max(hi[c], X[i][c]); }
    const cu = (lo[0] + hi[0]) / 2, ct = (lo[1] + hi[1]) / 2; if (hi[2] - lo[2] < 10 || hi[0] - lo[0] > 0.08 || hi[1] - lo[1] > 0.08 || Math.abs(cu - 4.45) > 0.03 || Math.abs(Math.abs(ct) - 0.28) > 0.03) continue;
    const k = ct > 0 ? '+t' : '-t'; if (out[k]) throw new Error('two ladder rails on ' + k + ' in ' + padF); out[k] = { top: hi[2], bottom: lo[2], u: cu, t: ct, verts: vs.length }; }
  if (!out['+t'] || !out['-t']) throw new Error('LADDER RAILS NOT FOUND in ' + padF + ' (expected 2 long thin prisms at u 4.45, t +-0.28)'); return out; })();
console.error('landing_clear: ladder rail tops from the mesh: +t ' + RAIL['+t'].top.toFixed(4) + ', -t ' + RAIL['-t'].top.toFixed(4) + ' (flat cut; was capsule to 21.85 + r)');
// ---- REAL-MESH CONVEX PIECES (A&A 00:15: Playtester wb.js 0cc51f8d is the official check; pre-check must agree within 1 mm). Same geometry as wb.js + bars2.py:
//   triangles of the scored Ship mesh whose centroid is within +-2.6 m (xz) of Ladder_Foot and Ladder_Foot.y-0.1 .. +23 m up, welded at 1 mm (world) into components,
//   labelled as bars2.py (rail, rung, cage_hoop, cage_bar, hatch_plate, top_guard_rail, landing_brace, gate, kerb), split into convex pieces (exact hull planes;
//   hoops = 6 segments between their 7 ring stations; kerb U = 3 strips; fused guard post + top rail = 2 pieces). Signed distance to a piece = max(n.p + d) over its
//   planes: <= 0 inside (= -depth, the exact distance to the nearest face of a convex solid); outside, the gate uses the exact point-to-triangle distance (nearTri).
const MESHP = (() => { const m = SHIP_MESH, pos = m.geometry.attributes.position, idx = m.geometry.index, v = new THREE.Vector3();
  const Wv = [], Xv = []; for (let i = 0; i < pos.count; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld); Wv.push([v.x, v.y, v.z]); Xv.push(toUTZ(v)); }
  const key = i => Math.round(Wv[i][0] * 1000) + ',' + Math.round(Wv[i][1] * 1000) + ',' + Math.round(Wv[i][2] * 1000);
  const kid = new Map(), kpt = [], kof = new Int32Array(pos.count).fill(-1), par = [];
  const fd = a => { while (par[a] !== a) { par[a] = par[par[a]]; a = par[a]; } return a; };
  const nt = (idx ? idx.count : pos.count) / 3; let kept = 0;
  for (let f = 0; f < nt; f++) { const I = [0, 1, 2].map(c => idx ? idx.getX(3 * f + c) : 3 * f + c); const cx = (Wv[I[0]][0] + Wv[I[1]][0] + Wv[I[2]][0]) / 3, cy = (Wv[I[0]][1] + Wv[I[1]][1] + Wv[I[2]][1]) / 3, cz = (Wv[I[0]][2] + Wv[I[1]][2] + Wv[I[2]][2]) / 3;
    if (Math.abs(cx - LF.x) > 2.6 || Math.abs(cz - LF.z) > 2.6 || cy < LF.y - 0.1 || cy > LF.y + 23) continue; kept++;
    const K = I.map(i => { const k = key(i); let j = kid.get(k); if (j === undefined) { j = kid.size; kid.set(k, j); kpt.push(i); par.push(j); } kof[i] = j; return j; });
    const a = fd(K[0]); par[fd(K[1])] = a; par[fd(K[2])] = fd(a); }
  const comps = new Map(); for (let j = 0; j < kpt.length; j++) { const r = fd(j); (comps.get(r) || comps.set(r, []).get(r)).push(j); }
  // exact convex hull planes by brute force over vertex triples (pieces have <= 24 vertices); n.p + d <= 0 inside
  const hullPlanes = Q => { const pl = [], n_ = Q.length; for (let a = 0; a < n_; a++) for (let b = a + 1; b < n_; b++) for (let c = b + 1; c < n_; c++) {
      const N = cross(sub(Q[b], Q[a]), sub(Q[c], Q[a])), L = Math.hypot(...N); if (L < 1e-9) continue; let n = N.map(x => x / L), d = -dot(n, Q[a]);
      let mx = -1e9, mn = 1e9; for (const q of Q) { const s = dot(n, q) + d; mx = Math.max(mx, s); mn = Math.min(mn, s); } if (mx > 1e-6 && mn < -1e-6) continue; if (mx > 1e-6) { n = n.map(x => -x); d = -d; }
      if (!pl.some(p => Math.abs(p[0] - n[0]) < 1e-6 && Math.abs(p[1] - n[1]) < 1e-6 && Math.abs(p[2] - n[2]) < 1e-6 && Math.abs(p[3] - d) < 1e-6)) pl.push([n[0], n[1], n[2], d]); } return pl; };
  // bars2.py convex(): every vertex is a hull corner or on a hull edge within 0.5 mm  (here: on >= 2 non-parallel hull planes within 0.5 mm)
  const convex = Q => { const pl = hullPlanes(Q); if (pl.length < 4) return false; return Q.every(q => { const on = pl.filter(p => Math.abs(dot(p, q) + p[3]) < 0.0005); return on.some((p, i) => on.some((r, j) => j > i && Math.abs(dot(p, r)) < 0.999)); }); };
  const pcaExt = Q => { const c = [0, 1, 2].map(k => Q.reduce((a, q) => a + q[k], 0) / Q.length); const A = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]; for (const q of Q) for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) A[i][j] += (q[i] - c[i]) * (q[j] - c[j]);
    const V = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]; for (let sw = 0; sw < 60; sw++) for (let p = 0; p < 2; p++) for (let q = p + 1; q < 3; q++) { if (Math.abs(A[p][q]) < 1e-15) continue; const th = (A[q][q] - A[p][p]) / (2 * A[p][q]), t = Math.sign(th || 1) / (Math.abs(th) + Math.sqrt(th * th + 1)), cs = 1 / Math.sqrt(t * t + 1), sn = t * cs;
      for (let k = 0; k < 3; k++) { const akp = A[k][p], akq = A[k][q]; A[k][p] = cs * akp - sn * akq; A[k][q] = sn * akp + cs * akq; } for (let k = 0; k < 3; k++) { const apk = A[p][k], aqk = A[q][k]; A[p][k] = cs * apk - sn * aqk; A[q][k] = sn * apk + cs * aqk; }
      for (let k = 0; k < 3; k++) { const vkp = V[k][p], vkq = V[k][q]; V[k][p] = cs * vkp - sn * vkq; V[k][q] = sn * vkp + cs * vkq; } }
    return [0, 1, 2].map(e => { const pr = Q.map(q => (q[0] - c[0]) * V[0][e] + (q[1] - c[1]) * V[1][e] + (q[2] - c[2]) * V[2][e]); return Math.max(...pr) - Math.min(...pr); }).sort((a, b) => a - b); };
  const pieces = [], info = [], vlab = new Map(); let ci = 0;
  const add = (lab, Q, part, c, extra) => { const lo = [0, 1, 2].map(k => Math.min(...Q.map(q => q[k]))), hi = [0, 1, 2].map(k => Math.max(...Q.map(q => q[k]))); pieces.push({ lab, part, c, pl: hullPlanes(Q), lo, hi, cen: [0, 1, 2].map(k => Q.reduce((a, q) => a + q[k], 0) / Q.length), nv: Q.length, pts: Q, ...extra }); };
  for (const js of comps.values()) { const c = ci++; const Wq = js.map(j => Wv[kpt[j]]), U = js.map(j => Xv[kpt[j]]), nv = js.length;
    const wlo = [0, 1, 2].map(k => Math.min(...Wq.map(q => q[k]))), whi = [0, 1, 2].map(k => Math.max(...Wq.map(q => q[k]))), ext = whi.map((x, k) => x - wlo[k]);
    const lo = [0, 1, 2].map(k => Math.min(...U.map(q => q[k]))), hi = [0, 1, 2].map(k => Math.max(...U.map(q => q[k]))), uext = hi.map((x, k) => x - lo[k]);
    let lab = null, why = '';
    if (nv === 12 && ext[1] > 20) lab = 'rail';
    else if (nv === 8 && uext[2] < 0.06 && uext[1] > 0.5 && uext[1] < 0.62 && uext[0] < 0.08) lab = 'rung';   // bars2: world ext 0.3-0.35 x 0.5-0.52 (= this box at 330 deg)
    else if (nv === 42) lab = 'cage_hoop';
    else if (nv === 8 && ext[1] > 18 && ext[1] < 19) lab = 'cage_bar';
    else if (nv <= 8 && Math.abs(wlo[1] + ext[1] - 21.7485) < 0.003 && ext[1] < 0.05) lab = 'hatch_plate';
    else if (wlo[1] >= 21.5 && nv <= 100 && pcaExt(U)[1] <= 0.08) lab = 'top_guard_rail';
    const mark = l => js.forEach(j => vlab.set(j, l));
    if (lab === 'cage_hoop') { const st = []; for (const q of U) { let s_ = st.find(s => Math.hypot(q[0] - s.seed[0], q[1] - s.seed[1], q[2] - s.seed[2]) < 0.08); if (!s_) st.push(s_ = { seed: q, P: [] }); s_.P.push(q); }
      if (st.length !== 7 || st.some(s => s.P.length !== 6)) throw new Error('hoop comp ' + c + ': ' + st.length + ' stations ' + st.map(s => s.P.length));
      st.forEach(s => s.c = [0, 1, 2].map(k => s.P.reduce((a, q) => a + q[k], 0) / 6)); st.sort((a, b) => b.c[1] - a.c[1]); const ord = [st.shift()]; while (st.length) { const l = ord[ord.length - 1].c; let bi = 0, bd = 1e9; st.forEach((s_, k) => { const d = Math.hypot(s_.c[0] - l[0], s_.c[1] - l[1]); if (d < bd) { bd = d; bi = k; } }); ord.push(st.splice(bi, 1)[0]); }
      for (let k = 0; k < 6; k++) add('cage_hoop', [...ord[k].P, ...ord[k + 1].P], 'seg' + k, c, { seg: k, z: ord[k].c[2] }); mark('cage_hoop'); info.push({ c, lab, nv }); continue; }
    if (lab) { if (!convex(U)) { info.push({ c, lab: null, nv, why: 'not convex' }); continue; } add(lab, U, lab, c); mark(lab); info.push({ c, lab, nv }); continue; }
    if (hi[2] < 20.4 || lo[2] > 24.6 || hi[0] < 3.6 || lo[0] > 5.7 || lo[1] > 1.5 || hi[1] < -1.5) continue;   // outside the landing zone (not graded, as bars2.py)
    if (nv === 8 && convex(U) && Math.abs(lo[2] - 21.7484) < 0.003 && uext[2] > 1.8 && uext[0] < 0.3 && hi[0] < 4.1) { info.push({ c, lab: null, nv, why: 'doorway box (walk-through)' }); continue; }
    if (nv > 100) { info.push({ c, lab: null, nv, why: 'ship body' }); continue; }
    if (nv >= 40 && uext[2] < 0.3 && Math.abs(hi[2] - 21.849) < 0.005) { info.push({ c, lab: null, nv, why: 'deck floor (soles graded by the deck rule)' }); continue; }
    if (convex(U)) { const l = hi[2] < 21.7 ? 'landing_brace' : (lo[0] > 5.2 && uext[2] > 0.5 ? 'gate' : 'kerb'); add(l, U, l, c); mark(l); info.push({ c, lab: l, nv, why: 'convex landing part' }); continue; }
    if (nv === 20 && uext[2] < 0.3 && hi[0] > 5.15 && hi[0] < 5.25 && lo[1] < -0.6 && hi[1] > 0.6) { const G_ = [q => q[1] <= -0.60, q => q[1] >= 0.60, q => q[0] >= 5.14];
      if (G_.every(g => convex(U.filter(g))) && U.every(q => G_.some(g => g(q)))) { ['frame_side_-t', 'frame_side_+t', 'frame_outer'].forEach((nm, k) => add('kerb', U.filter(G_[k]), nm, c)); mark('kerb'); info.push({ c, lab: 'kerb', nv, why: 'kerb U = 3 strips' }); continue; } }
    { const bot = U.map(q => q[2] < lo[2] + 0.002), post = U.map(q => U.some((b, k) => bot[k] && Math.hypot(b[0] - q[0], b[1] - q[1]) < 0.001)), rail = U.map((q, k) => !post[k] && q[2] > hi[2] - 0.07);
      const Pp = U.filter((q, k) => post[k]), Rr = U.filter((q, k) => rail[k]);
      if (Pp.length >= 8 && Rr.length >= 8 && U.every((q, k) => post[k] || rail[k]) && convex(Pp) && convex(Rr)) { add('top_guard_rail', Pp, 'fused_post', c); add('top_guard_rail', Rr, 'fused_top_rail', c); mark('top_guard_rail'); info.push({ c, lab: 'top_guard_rail', nv, why: 'fused guard post + top rail = 2 pieces' }); continue; } }
    info.push({ c, lab: null, nv, why: 'UNGRADED landing part (no rule)', lo, hi }); }
  for (const p of pieces) { p.lo = p.lo.map(x => x - 1e-4); p.hi = p.hi.map(x => x + 1e-4); }
  // vertex index -> label (for the triangle labels) and a 0.1 m piece grid
  const vix = new Map(); for (let i = 0; i < pos.count; i++) if (kof[i] >= 0 && vlab.has(kof[i])) vix.set(i, vlab.get(kof[i]));
  const grid = new Map(); pieces.forEach((p, pi) => { for (let a = Math.floor(p.lo[0] / 0.1); a <= Math.floor(p.hi[0] / 0.1); a++) for (let b = Math.floor(p.lo[1] / 0.1); b <= Math.floor(p.hi[1] / 0.1); b++) for (let e = Math.floor(p.lo[2] / 0.1); e <= Math.floor(p.hi[2] / 0.1); e++) { const k = a + ',' + b + ',' + e; (grid.get(k) || grid.set(k, []).get(k)).push(pi); } });
  const count = {}; for (const p of pieces) count[p.lab] = (count[p.lab] || 0) + 1; const ccount = {}; for (const x of info) ccount[String(x.lab)] = (ccount[String(x.lab)] || 0) + 1;
  return { pieces, info, vix, grid, count, ccount, kept_tris: kept, welded_verts: kpt.length, ungraded: info.filter(x => x.why && x.why.startsWith('UNGRADED')) }; })();
const pieceSd = (p, u, t, z) => { let s = -1e9; for (const q of p.pl) { const x = q[0] * u + q[1] * t + q[2] * z + q[3]; if (x > s) s = x; } return s; };
// deepest penetration over the mesh pieces (labels L or all): [sd (< 0 inside, 1e9 outside every piece), label, piece index]
function sdMesh(u, t, z, L) { const a = MESHP.grid.get(Math.floor(u / 0.1) + ',' + Math.floor(t / 0.1) + ',' + Math.floor(z / 0.1)); if (!a) return [1e9, null, -1]; let best = 1e9, who = null, bi = -1;
  for (const pi of a) { const p = MESHP.pieces[pi]; if (L && !L.has(p.lab)) continue; if (u < p.lo[0] || u > p.hi[0] || t < p.lo[1] || t > p.hi[1] || z < p.lo[2] || z > p.hi[2]) continue; const s = pieceSd(p, u, t, z); if (s < 0 && s < best) { best = s; who = p.lab; bi = pi; } } return [best, who, bi]; }
// gate parts scored from the mesh pieces (their analytic stand-ins are dropped from the gate solids when the mesh has them)
const GATE_MESH = new Set(['rail', 'rung', 'cage_hoop', 'cage_bar', 'kerb', 'gate', 'landing_brace', 'top_guard_rail']);
const RUNGP = MESHP.pieces.filter(p => p.lab === 'rung').map(p => ({ z: p.cen[2], u: p.cen[0], top: Math.max(...p.pts.map(q => q[2])), bottom: Math.min(...p.pts.map(q => q[2])) })).sort((a, b) => a.z - b.z);
if (MESHP.count.rail !== 2 || !RUNGP.length) throw new Error('ladder rails/rungs not found as mesh pieces in ' + padF);
const MISSING = [...GATE_MESH].filter(l => !MESHP.count[l]); if (['cage_hoop', 'cage_bar'].some(l => MISSING.includes(l))) throw new Error('cage pieces not found in ' + padF + ': ' + MISSING);
const DROP_ANALYTIC = new Set([...(MESHP.count.kerb >= 3 ? ['frame_side', 'frame_outer'] : []), ...(MESHP.count.gate ? ['lid', 'lid_hinge', 'lid_rib', 'lid_strut'] : []), ...(MESHP.count.landing_brace >= 2 ? ['brace'] : []), ...(MESHP.count.top_guard_rail ? ['rail_post', 'rail'] : [])]);
console.error('landing_clear: mesh pieces ' + JSON.stringify(MESHP.count) + ' from ' + MESHP.kept_tris + ' tris / ' + MESHP.welded_verts + ' welded verts; comps ' + JSON.stringify(MESHP.ccount) + (MESHP.ungraded.length ? '; UNGRADED landing comps ' + MESHP.ungraded.map(x => x.c) : '') + '; analytic solids dropped (mesh has them): ' + [...DROP_ANALYTIC].join(','));
// ---- landing solids (u, t, z)
const R = 4.0, TOP = 21.85, hu = t => Math.sqrt(R * R - t * t) - 0.03;
const boxes = [   // [name, u0 (number or 'hull'), u1, t0, t1, z0, z1]  (|t| mirrored when sym)
  ['deck_wing', 'hull', 5.45, 0.62, 1.40, 21.75, TOP, 1], ['deck_bridge', 5.15, 5.45, -0.62, 0.62, 21.75, TOP, 0],
  ['frame_side', 'hull', 5.21, 0.62, 0.68, 21.66, 21.88, 1], ['frame_outer', 5.15, 5.21, -0.62, 0.62, 21.66, 21.88, 0],
  ['beam_outer', 5.38, 5.45, -1.40, 1.40, 21.61, 21.75, 0], ['beam_side', 'hull', 5.38, 1.33, 1.40, 21.61, 21.75, 1]];
const OPEN = 100 * Math.PI / 180, HU = 5.21 + 0.035, HZ = 21.88 + 0.02, LL = 1.16, d = [Math.cos(Math.PI - OPEN), Math.sin(Math.PI - OPEN)], n = [d[1], -d[0]];
const at = (s, k = 0) => [HU + d[0] * s + n[0] * k, HZ + d[1] * s + n[1] * k];
const caps = [];  // [name, a(u,t,z), b, r]
for (const sg of [-1, 1]) {
  caps.push(['brace', [5.41, sg * 1.36, 21.63], [hu(1.0) + 0.02, sg * 1.0, 20.50], 0.03]);
  const A = [4.15, sg * 1.34], B = [5.40, sg * 1.34], Cc = [5.40, sg * 0.76];
  for (const p of [A, [(A[0] + B[0]) / 2, A[1]], B, Cc]) caps.push(['rail_post', [p[0], p[1], TOP], [p[0], p[1], TOP + 1.05], 0.028]);
  for (const [h, r] of [[1.05, 0.032], [0.525, 0.024]]) { caps.push(['rail', [A[0], A[1], TOP + h], [B[0], B[1], TOP + h], r]); caps.push(['rail', [B[0], B[1], TOP + h], [Cc[0], Cc[1], TOP + h], r]); }
}
caps.push(['lid_hinge', [HU, -0.62, HZ], [HU, 0.62, HZ], 0.035]);
for (const t of [-0.3, 0.3]) { const a = at(0.08, 0.035), b = at(LL - 0.08, 0.035); caps.push(['lid_rib', [a[0], t, a[1]], [b[0], t, b[1]], 0.022]); }
for (const t of [-0.52, 0.52]) { const b = at(0.62, 0.03); caps.push(['lid_strut', [5.40, t, TOP + 0.01], [b[0], t, b[1]], 0.018]); }
const sdBox = (q, h) => { const o = q.map((x, i) => Math.abs(x) - h[i]); const out = Math.hypot(...o.map(x => Math.max(x, 0))); return out + Math.min(Math.max(...o), 0); };
function sdf(u, t, z, gate) {   // gate = true: the gate's solids (analytic parts the mesh pieces replace are skipped); false: all analytic solids (GLB check, triangle labels)
  let best = 1e9, who = null;
  for (const [nm, u0_, u1, t0, t1, z0, z1, sym] of boxes) { if (gate && DROP_ANALYTIC.has(nm)) continue;
    const tt = sym ? Math.abs(t) : t; const u0 = u0_ === 'hull' ? hu(Math.min(Math.max(tt, t0), t1)) : u0_;
    const s = sdBox([u - (u0 + u1) / 2, tt - (t0 + t1) / 2, z - (z0 + z1) / 2], [(u1 - u0) / 2, (t1 - t0) / 2, (z1 - z0) / 2]);
    if (s < best) { best = s; who = nm; }
  }
  if (!(gate && DROP_ANALYTIC.has('lid'))) { const c = at(LL / 2), du = u - c[0], dz = z - c[1]; const s = sdBox([du * d[0] + dz * d[1], t, du * n[0] + dz * n[1]], [LL / 2, 0.65, 0.025]); if (s < best) { best = s; who = 'lid'; } }
  for (const [nm, a, b, r] of caps) { if (gate && DROP_ANALYTIC.has(nm)) continue;
    const ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], ap = [u - a[0], t - a[1], z - a[2]];
    const h = Math.max(0, Math.min(1, (ap[0] * ab[0] + ap[1] * ab[1] + ap[2] * ab[2]) / (ab[0] ** 2 + ab[1] ** 2 + ab[2] ** 2)));
    const s = Math.hypot(ap[0] - ab[0] * h, ap[1] - ab[1] * h, ap[2] - ab[2] * h) - r; if (s < best) { best = s; who = nm; }
  }
  return [best, who];
}
const meshInfo = () => ({ source: 'wb.js 0cc51f8d geometry + bars2.py labels/pieces, from ' + SHIP_MESH.name, kept_tris: MESHP.kept_tris, welded_verts: MESHP.welded_verts, pieces: MESHP.count, comps: MESHP.ccount, ungraded_landing: MESHP.ungraded, analytic_dropped: [...DROP_ANALYTIC], gate_mesh_labels: [...GATE_MESH] });
const res = { mesh_pieces: meshInfo(), skipped_hidden_nodes: SKIPPED, scored_mesh: SHIP_MESH.name, ladder_rails_from_mesh: RAIL, frame: 'pad-local; u,t,z about Ship_Center along the 330 deg ladder axis', ship_center: [C.x, C.y, C.z], ladder_foot_utz: toUTZ(LF).map(x => +x.toFixed(3)) };
// ---- GLB check: landing triangles (Ship node, inside the landing box, not hull/ladder/hatch) must lie on the solids
{ const ship = SHIP_NODE, m = SHIP_MESH;
  const pos = m.geometry.attributes.position, v = new THREE.Vector3(); let nv = 0, maxOff = 0, oldDeck = 0;
  for (let i = 0; i < pos.count; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld); const [u, t, z] = toUTZ(v);
    if (z < 21.55 || z > 23.2 || Math.abs(t) > 1.5 || u < 4.12 || u > 5.6) continue;
    if (u < 4.6 && Math.abs(t) < 0.75 && z > 21.7) continue;                       // ladder rail tops / hatch / cage bars
    if (Math.hypot(u - 4.45, Math.abs(t) - 0.28) < 0.06 || CAGE.verts.has(i)) continue; // ladder rails / cage (from the mesh)
    const [s] = sdf(u, t, z); nv++; maxOff = Math.max(maxOff, Math.abs(s));
    if (u > 4.3 && u < 5.1 && Math.abs(t) < 0.55 && z > 21.74 && z < 21.86) oldDeck++; }
  res.glb_landing_vertices = nv; res.glb_max_offset_from_solids_m = +maxOff.toFixed(4); res.glb_vertices_left_in_well = oldDeck; }

// ---- hull wall (real triangles from the Ship node) + hatch doorway (open: |t| < 0.652, z 21.75-23.75, the placeholder hatch panel is the doorway)
const DOOR = { t: 0.652, z0: 21.75, z1: 23.75 }, WALL = 0.10;
const hullTris = [];
{ const ship = SHIP_NODE, m = SHIP_MESH;
  const pos = m.geometry.attributes.position, idx = m.geometry.index, P3 = i => { const q = new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld); return toUTZ(q); };
  for (let f = 0; f < idx.count; f += 3) { const A = P3(idx.getX(f)), B = P3(idx.getX(f + 1)), Cq = P3(idx.getX(f + 2)), V = [A, B, Cq];
    if (Math.max(...V.map(p => p[2])) < 20.6 || Math.min(...V.map(p => p[2])) > 24.6 || Math.min(...V.map(p => Math.abs(p[1]))) > 2.2 || Math.max(...V.map(p => p[0])) < 3.0) continue;
    if (!V.every(p => { const r = Math.hypot(p[0], p[1]); return r > 3.90 && r < 4.012; }) || Math.min(...V.map(p => p[0])) < 2.0) continue;            // hull skin only (rings/landing/ladder are outside)
    if (V.every(p => p[0] > 3.92 && p[0] < 4.08 && Math.abs(p[1]) < 0.665 && p[2] > 21.73 && p[2] < 23.77)) continue; // the hatch panel itself (rbox u 3.94-4.06, |t| <= 0.652) is the doorway
    const n = cross(sub(B, A), sub(Cq, A)); const L = Math.hypot(...n); if (L < 1e-9) continue; let N = n.map(x => x / L);
    const c = [(A[0] + B[0] + Cq[0]) / 3, (A[1] + B[1] + Cq[1]) / 3]; if (N[0] * c[0] + N[1] * c[1] < 0) N = N.map(x => -x);
    hullTris.push([A, B, Cq, N]); } }
function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
function closestTri(p, a, b, c) { // Ericson
  const ab = sub(b, a), ac = sub(c, a), ap = sub(p, a), d1 = dot(ab, ap), d2 = dot(ac, ap); if (d1 <= 0 && d2 <= 0) return a;
  const bp = sub(p, b), d3 = dot(ab, bp), d4 = dot(ac, bp); if (d3 >= 0 && d4 <= d3) return b;
  const vc = d1 * d4 - d3 * d2; if (vc <= 0 && d1 >= 0 && d3 <= 0) { const v = d1 / (d1 - d3); return [a[0] + ab[0] * v, a[1] + ab[1] * v, a[2] + ab[2] * v]; }
  const cp = sub(p, c), d5 = dot(ab, cp), d6 = dot(ac, cp); if (d6 >= 0 && d5 <= d6) return c;
  const vb = d5 * d2 - d1 * d6; if (vb <= 0 && d2 >= 0 && d6 <= 0) { const w = d2 / (d2 - d6); return [a[0] + ac[0] * w, a[1] + ac[1] * w, a[2] + ac[2] * w]; }
  const va = d3 * d6 - d5 * d4; if (va <= 0 && d4 - d3 >= 0 && d5 - d6 >= 0) { const w = (d4 - d3) / ((d4 - d3) + (d5 - d6)); return [b[0] + (c[0] - b[0]) * w, b[1] + (c[1] - b[1]) * w, b[2] + (c[2] - b[2]) * w]; }
  const den = 1 / (va + vb + vc), v = vb * den, w = vc * den; return [a[0] + ab[0] * v + ac[0] * w, a[1] + ab[1] * v + ac[1] * w, a[2] + ab[2] * v + ac[2] * w]; }
function hullSigned(p) { let best = 1e9, sgn = 1; for (const [a, b, c, N] of hullTris) { const q = closestTri(p, a, b, c), d = sub(p, q), L = Math.hypot(...d); if (L < best) { best = L; sgn = dot(d, N) >= 0 ? 1 : -1; } } return best * sgn; }
// wall solid = between the hull surface and 0.10 m inside it, minus the doorway prism. Returns [sdf, part]
function sdWall(u, t, z) {
  if (Math.hypot(u, t) > 4.6 || Math.hypot(u, t) < 3.6 || z < 20.6 || z > 24.6) return [1e9, null];
  const dOut = hullSigned([u, t, z]); const sWall = Math.max(dOut, -WALL - dOut);
  const sDoor = sdBox([u - 2.0, t, z - (DOOR.z0 + DOOR.z1) / 2], [2.3, DOOR.t, (DOOR.z1 - DOOR.z0) / 2]);   // doorway prism u -0.3..4.3
  const s = Math.max(sWall, -sDoor); const inDoorBand = z > DOOR.z0 - 0.05 && z < DOOR.z1 + 0.05 && Math.abs(Math.abs(t) - DOOR.t) < 0.25;
  return [s, inDoorBand ? 'hatch_jamb' : (z > DOOR.z1 && Math.abs(t) < DOOR.t + 0.05 ? 'hatch_lintel' : 'hull')]; }
// exact distance to the jamb edges (outer-face corner lines at |t| 0.652, u 3.90-4.06, z 21.75-23.75) and lintel edge
const segD = (p, a, b) => { const ab = sub(b, a), ap = sub(p, a); const h = Math.max(0, Math.min(1, dot(ap, ab) / dot(ab, ab))); return Math.hypot(ap[0] - ab[0] * h, ap[1] - ab[1] * h, ap[2] - ab[2] * h); };
const JAMB = [[[4.06, 0.652, 21.75], [4.06, 0.652, 23.75]], [[4.06, -0.652, 21.75], [4.06, -0.652, 23.75]], [[4.06, -0.652, 23.75], [4.06, 0.652, 23.75]]];

// ---- ladder (placeholder geometry, unchanged): rails r 0.035 at u 4.45, t +-0.28, z 0.25-21.85; rungs 0.05 x 0.56 x 0.05 at z 0.65 + 0.6 i; cage = CAGE (from the mesh, above);
// GATE FINAL: rails + rungs = real mesh pieces (MESHP, labels rail -> ladder_rail, rung); no capsules / boxes. rungs[] = mesh rung centre z (bottom to top)
const LTOP = 0.25, LADT = 21.85, ladCaps = [], rungs = RUNGP.map(r => r.z);
// cage hoops/verticals: NO capsules any more (A&A 00:15) - scored as the real mesh (convex pieces inside, exact triangle distance outside), see MESHP / clearOf
const capSd = (p, a, b, r) => segD(p, a, b) - r;
const flatTopSd = (p, a, b, r) => { if (p[2] < a[2]) return capSd(p, a, b, r);   // vertical rod: capsule below the bottom point (unchanged); flat cut at the top b[2]
  const dr = Math.hypot(p[0] - a[0], p[1] - a[1]) - r, dz = p[2] - b[2]; return Math.min(Math.max(dr, dz), 0) + Math.hypot(Math.max(dr, 0), Math.max(dz, 0)); };
function sdLadder(u, t, z) { let best = 1e9, who = null;
  for (const [nm, a, b, r, ft] of ladCaps) { if (z < Math.min(a[2], b[2]) - 0.3 || z > Math.max(a[2], b[2]) + 0.3) continue; const s = ft === 'flat_top' ? flatTopSd([u, t, z], a, b, r) : capSd([u, t, z], a, b, r); if (s < best) { best = s; who = nm; } }
  return [best, who]; }
// ---- every Ship-node triangle near the boarding route, labelled, in a 0.1 m grid
// ---- hatch floor plate (from the mesh): top faces = Ship tris with all 3 vertices on y 21.7484 +- 1 mm whose centroid lies in the seed outline (A&A corners,
//   pad xz, ALL 3 vertices within 1 mm of the outline); footprint = convex hull (xz) of those faces' vertices; plate faces = every Ship tri with all 3 vertices inside the footprint (1 mm tol)
//   and y in [top - 5 cm, top + 1 mm] (top, bottom and the 4 sides)
const PLATE_TOP_Y = 21.7484, PLATE_SEED = [[2.3065, -10.9526], [3.199, -10.4364], [3.8158, -11.5125], [2.9234, -12.0287]];
const polySd = (x, y, P) => { let inside = true, dmin = 1e9; for (let i = 0; i < P.length; i++) { const [ax, ay] = P[i], [bx, by] = P[(i + 1) % P.length];
  const ex = bx - ax, ey = by - ay, h = Math.max(0, Math.min(1, ((x - ax) * ex + (y - ay) * ey) / (ex * ex + ey * ey))); dmin = Math.min(dmin, Math.hypot(x - ax - ex * h, y - ay - ey * h));
  if (ex * (y - ay) - ey * (x - ax) < 0) inside = false; } return inside ? -dmin : dmin; };   // signed 2D distance, P convex CCW
const ccw = P => { let a = 0; for (let i = 0; i < P.length; i++) { const [x0, y0] = P[i], [x1, y1] = P[(i + 1) % P.length]; a += x0 * y1 - x1 * y0; } return a < 0 ? P.slice().reverse() : P; };
const hull2 = pts => { const q = [...new Map(pts.map(p => [p[0].toFixed(5) + ',' + p[1].toFixed(5), p])).values()].sort((a, b) => a[0] - b[0] || a[1] - b[1]); const cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [], up = []; for (const p of q) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], p) <= 1e-12) lo.pop(); lo.push(p); } for (const p of q.slice().reverse()) { while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], p) <= 1e-12) up.pop(); up.push(p); } return lo.slice(0, -1).concat(up.slice(0, -1)); };
const PLATE = (() => { const ship = SHIP_NODE, m = SHIP_MESH;
  const pos = m.geometry.attributes.position, idx = m.geometry.index, Pw = i => new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld); const seed = ccw(PLATE_SEED);
  const top = [], pts = []; for (let f = 0; f < idx.count; f += 3) { const V = [0, 1, 2].map(c => Pw(idx.getX(f + c))); if (!V.every(p => Math.abs(p.y - PLATE_TOP_Y) <= 0.001)) continue;
    if (!V.every(p => polySd(p.x, p.z, seed) <= 0.001)) continue; top.push(f / 3); V.forEach(p => pts.push([p.x, p.z])); }
  if (!top.length) return null; const fp = ccw(hull2(pts)); const faces = new Set(); let ymin = 1e9, ymax = -1e9;
  for (let f = 0; f < idx.count; f += 3) { const V = [0, 1, 2].map(c => Pw(idx.getX(f + c))); if (V.every(p => polySd(p.x, p.z, fp) <= 0.001 && p.y >= PLATE_TOP_Y - 0.05 && p.y <= PLATE_TOP_Y + 0.001)) { faces.add(f / 3); V.forEach(p => { ymin = Math.min(ymin, p.y); ymax = Math.max(ymax, p.y); }); } }
  const fpUT = ccw(fp.map(([x, z]) => toUTZ(new THREE.Vector3(x, PLATE_TOP_Y, z)).slice(0, 2)));
  return { mesh: m.name, top_tris: top, faces, top: ymax, bottom: ymin, fp_xz: fp, fp_ut: fpUT }; })();
const onPlate = (u, t) => !!PLATE && polySd(u, t, PLATE.fp_ut) <= 0;            // strict: the sole vertex must be inside (or on) the real outline
const PLATE_T = new Set();                                                       // indices into tris[] of the plate faces
const HATCH = { u0: 3.80, u1: 4.06 };
const inDoor = (u, t, z) => Math.abs(t) < DOOR.t && z > DOOR.z0 && z < DOOR.z1 && u < HATCH.u1 + 0.002;
const tris = []; const GRID = new Map(), CS = 0.1, key3 = (i, j, k) => i + ',' + j + ',' + k;
{ const ship = SHIP_NODE, m = SHIP_MESH;
  const pos = m.geometry.attributes.position, idx = m.geometry.index, cache = new Map();
  const P3 = i => { if (!cache.has(i)) cache.set(i, toUTZ(new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld))); return cache.get(i); };
  for (let f = 0; f < idx.count; f += 3) { const V = [P3(idx.getX(f)), P3(idx.getX(f + 1)), P3(idx.getX(f + 2))]; const isPlate = !!PLATE && PLATE.faces.has(f / 3);
    const lo = [0, 1, 2].map(c => Math.min(...V.map(p => p[c]))), hi = [0, 1, 2].map(c => Math.max(...V.map(p => p[c])));
    if (hi[0] < 3.0 || lo[0] > 6.2 || hi[1] < -2.4 || lo[1] > 2.4 || hi[2] < 0 || lo[2] > 24.6) continue;
    const c = [(V[0][0] + V[1][0] + V[2][0]) / 3, (V[0][1] + V[1][1] + V[2][1]) / 3, (V[0][2] + V[1][2] + V[2][2]) / 3];
    const n = cross(sub(V[1], V[0]), sub(V[2], V[0])); const L = Math.hypot(...n); if (L < 1e-12) continue; const N = n.map(x => x / L);
    // label: hatch panel / ladder / landing part / hull / other ship
    let label = 'ship_other';
    const inPanel = V.every(p => p[0] > HATCH.u0 - 0.01 && p[0] < HATCH.u1 + 0.01 && Math.abs(p[1]) < DOOR.t + 0.01 && p[2] > DOOR.z0 - 0.01 && p[2] < DOOR.z1 + 0.01);
    if (inPanel) { label = Math.abs(N[1]) > 0.5 ? 'hatch_jamb' : Math.abs(N[2]) > 0.5 ? (c[2] > 22.7 ? 'hatch_lintel' : 'hatch_sill') : 'hatch_panel_face'; }
    else { const [sl, wl] = sdLadder(...c), [sa, wa] = sdf(...c); const rr = Math.hypot(c[0], c[1]);
      if (Math.abs(sl) < 0.015 && Math.abs(sl) <= Math.abs(sa)) label = wl; else if (Math.abs(sa) < 0.015) label = wa; else if (rr > 3.6 && rr < 4.02 && Math.abs(N[2]) < 0.3) label = 'hull'; }
    { const cl = [idx.getX(f), idx.getX(f + 1), idx.getX(f + 2)].map(x => CAGE.verts.get(x)); if (cl.some(Boolean)) label = cl.find(Boolean); }   // cage verts: scored only as cage
    { const ml = [idx.getX(f), idx.getX(f + 1), idx.getX(f + 2)].map(x => MESHP.vix.get(x)).find(l => l && GATE_MESH.has(l) && !l.startsWith('cage')); if (ml) label = ml === 'rail' ? 'ladder_rail' : ml; }   // kerb / gate / landing_brace / top_guard_rail triangles: the mesh-piece label
    if (isPlate) label = 'hatch_plate';
    if (label === 'hatch_panel_face') continue;          // the panel's outer/inner faces are the doorway the crew walk through
    const T_ = tris.length; tris.push([V[0], V[1], V[2], label]); if (isPlate) PLATE_T.add(T_);
    for (let i = Math.floor((lo[0] - 0.03) / CS); i <= Math.floor((hi[0] + 0.03) / CS); i++) for (let j = Math.floor((lo[1] - 0.03) / CS); j <= Math.floor((hi[1] + 0.03) / CS); j++) for (let k = Math.floor((lo[2] - 0.03) / CS); k <= Math.floor((hi[2] + 0.03) / CS); k++) {
      const kk = key3(i, j, k); let a = GRID.get(kk); if (!a) GRID.set(kk, a = []); a.push(T_); } } }
const labelCount = {}; for (const t_ of tris) labelCount[t_[3]] = (labelCount[t_[3]] || 0) + 1;
function nearTri(u, t, z, skipPlate) { const a = GRID.get(key3(Math.floor(u / CS), Math.floor(t / CS), Math.floor(z / CS))); if (!a) return [1e9, null]; let best = 1e9, who = null; const p = [u, t, z], door = inDoor(u, t, z);
  for (const ti of a) { const [A, B, Cq, lb] = tris[ti]; if (door && lb === 'hull') continue; if (skipPlate && PLATE_T.has(ti)) continue; const q = closestTri(p, A, B, Cq); const d = Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]); if (d < best) { best = d; who = lb; } }
  return [best, who]; }
// ---- crew sampling (30 Hz over all three clips back to back)
const g = await load(crewF); const S = g.scene; const mixer = new THREE.AnimationMixer(S);
const clips = Object.fromEntries(g.animations.map(a => [a.name, a]));
const meshes = []; S.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
// v3 (a749662) timings are the default; override with TIMINGS='{"Crew_1":{"s":..,"i":..,"side":1},...}' (climb start s, inside-hatch i, step-off side)
const PH = process.env.TIMINGS ? JSON.parse(process.env.TIMINGS) : { Crew_1: { s: 41.62, i: 47.79, side: 1 }, Crew_2: { s: 45.02, i: 51.19, side: -1 }, Crew_3: { s: 48.42, i: 54.59, side: 1 }, Crew_4: { s: 51.82, i: 57.99, side: -1 } };
const SHZ = +(process.env.HZ || 30), dt = 1 / SHZ, DECK = 21.85, KERB = 21.88;
const crewOf = m => { let p = m; while (p && !/^Crew_\d$/.test(p.name)) p = p.parent; return p ? p.name : m.name; };
const boneOf = {}; for (const m of meshes) { const si = m.geometry.attributes.skinIndex, sw = m.geometry.attributes.skinWeight, names = m.skeleton.bones.map(b => b.name.replace(/^C\d_/, ''));
  boneOf[m.uuid] = new Array(si.count); for (let i = 0; i < si.count; i++) { let bi = 0, bw = -1; for (let c = 0; c < 4; c++) { const w = sw.getComponent(i, c); if (w > bw) { bw = w; bi = si.getComponent(i, c); } } boneOf[m.uuid][i] = names[bi]; } }
const handTris = {}; for (const m of meshes) { const idx = m.geometry.index, bo = boneOf[m.uuid]; const H = { Hand_L: [], Hand_R: [] };
  for (let f = 0; f < idx.count; f += 3) { const a = [idx.getX(f), idx.getX(f + 1), idx.getX(f + 2)]; for (const h in H) if (a.every(i => bo[i] === h)) H[h].push(a); } handTris[m.uuid] = H; }
// generalized winding number of a closed triangle set about point p (|w| ~ 1 inside, ~ 0 outside); Van Oosterom-Strackee solid angle
function winding(p, T, X) { let w = 0; for (const [a, b, c] of T) { const A = sub(X[a], p), B = sub(X[b], p), Cc = sub(X[c], p); const la = Math.hypot(...A), lb = Math.hypot(...B), lc = Math.hypot(...Cc);
  const num = A[0] * (B[1] * Cc[2] - B[2] * Cc[1]) - A[1] * (B[0] * Cc[2] - B[2] * Cc[0]) + A[2] * (B[0] * Cc[1] - B[1] * Cc[0]);
  const den = la * lb * lc + (A[0] * B[0] + A[1] * B[1] + A[2] * B[2]) * lc + (B[0] * Cc[0] + B[1] * Cc[1] + B[2] * Cc[2]) * la + (Cc[0] * A[0] + Cc[1] * A[1] + Cc[2] * A[2]) * lb;
  w += 2 * Math.atan2(num, den); } return w / (4 * Math.PI); }
// rod axes that hands may grip: the 2 rails + every rung (rung axis runs along t at u 4.45, z = rung centre)
const gripRods = [...Object.values(RAIL).map(r => ['ladder_rail', [r.u, r.t, r.bottom], [r.u, r.t, r.top]]), ...RUNGP.map(r => ['rung', [r.u, -0.28, r.z], [r.u, 0.28, r.z]])];
const RULES = { rails_depth: { applies: 'ladder rails (ladder_rails + ladder_top_rails), any bone: FAIL only if deeper than max_depth_m inside the real rail mesh (= wb.js 0cc51f8d LIMIT); closer than 3 cm but not deeper than 5 mm = report-only WARNING (summary.warnings, never fails)', max_depth_m: 0.005 }, min_clearance_m: 0.03, hand_grip_resting: { applies: 'HELD hand (wb.js 0e8a30b7): hand/finger vertices inside the rung that hand holds (rung nearest the hand-vertex centroid, no distance cap) while held: max pairwise distance of the hand-bone world position over +-0.1 s (+-hold_half_samples, within one clip run, hand present in every sample) <= 5 mm and the held rung unchanged in the window; rails, cage, plate, other rungs and non-held hands stay at 5 mm', max_sink_m: 0.010, hold_still_m: 0.005, hold_window_s: 0.1, source: 'playtest/qnext_frozen_hf23/wbody/wb.js md5 0e8a30b7 gradeHands()' }, hand_grip: { applies: 'Hand_L/Hand_R vertices whose nearest part is a ladder rail or rung', max_sink_m: 0.005, rod_through_hand: 'per sample, for each rail/rung axis clipped to the hand bbox + 1 cm (so the clipped axis starts and ends outside the hand): exact segment-triangle intersection against every Hand-bone triangle, then the generalized winding number at the midpoint of each interval between crossings. FLAG if the axis crosses the hand skin at all, or any interval is inside a closed hand piece (|w| > 0.5). A wrapped grip leaves the axis in the palm/finger cavity with 0 crossings; a rod through the hand (incl. through the back of the glove) must cross the skin. Reports solid inside length and samples where only zero-thickness (double-sided) hand faces are crossed.' },
  resting_soles: { applies: 'Foot_L/Foot_R sole vertices (within 1.5 cm of that foot\'s lowest vertex) of a still foot (sole centroid moved < 5 mm and lowest z < 3 mm since the previous sample) on the deck wing/bridge top (z 21.85) or a rung top (rung centre + 0.025)', max_sink_m: 0.005 },
  everything_else: 'any other crew vertex closer than 0.03 m to any Ship-node triangle or inside a solid (real-mesh pieces or analytic deck/wall) is flagged (rails: see rails_depth; rungs swung past, cage hoops/bars, hatch jamb/lintel, kerb, guard rail, ladder-top rails, shins over the deck, hull, other ship parts)', sample_hz: null };
const group = (part, bn, z, cat) => cat === 'hand_sink' ? 'hand_grip_sink_gt_5mm' : cat === 'rod_through' ? 'hand_grip_rod_through_hand' : cat === 'sole_sink' ? 'resting_sole_sink_gt_5mm' :
  part === 'ladder_rail' ? (z > 21.0 ? 'ladder_top_rails' : 'ladder_rails') : part === 'rung' ? 'rungs' : part && part.startsWith('cage') ? 'cage' : part === 'hatch_plate' ? 'other_ship' : part && part.startsWith('hatch') ? 'hatch_jamb_lintel' :
  part === 'frame_side' || part === 'frame_outer' || part === 'kerb' ? 'kerb' : part === 'rail' || part === 'rail_post' || part === 'top_guard_rail' ? 'guard_rail' : part === 'gate' ? 'gate' : part === 'landing_brace' || part === 'brace' ? 'landing_brace' : part && part.startsWith('deck') ? (bn.startsWith('Shin') ? 'shins_over_deck' : 'deck_non_resting') : part === 'hull' ? 'hull' : 'other_ship';
const support = (u, t) => { const at = Math.abs(t);
  if (at < DOOR.t && u < 4.06) return 'hatch_doorway';
  if (at > 1.40 || u > 5.45) return 'off_edge';
  if (u >= 5.15 && u <= 5.21 && at <= 0.68) return 'kerb';
  if (at >= 0.62 && at <= 0.68 && u <= 5.21) return u >= hu(at) ? 'kerb' : 'inside_hull';
  if (at < 0.62) return u > 5.21 ? 'bridge' : 'well';
  return u >= hu(at) ? 'wing' : 'inside_hull'; };
const ph = (k, tm) => tm < PH[k].s ? 'before_climb_top' : tm < PH[k].i ? 'through_hole_and_walk_in' : 'hidden';
// ---- per-vertex verdict (same rules as 50dd4b68; the plate branch is the only addition). Returns {cat:'clear'|'flag'|'hand_grip'|'sole_on_deck'|'sole_on_rung'|'sole_on_plate', part, D, extra, grip}
const isStill = (pr, cu, ct, mz) => !!pr && Math.hypot(cu - pr[0], ct - pr[1]) < 0.005 && Math.abs(mz - pr[2]) < 0.003;   // unchanged resting test (< 5 mm sideways, < 3 mm vertical)
function clearOf(u, tt, z, plateFloor) {   // plateFloor: the sole vertex is inside the plate outline -> the plate faces and the analytic doorway floor under it are the plate
  let [s, who] = sdf(u, tt, z, true); { const [sm, wm] = sdMesh(u, tt, z, GATE_MESH); if (sm < 0 && (sm < s || /^(deck|beam)_/.test(who))) { s = sm; who = wm === 'rail' ? 'ladder_rail' : wm; } }   /* inside a real part: it wins over the analytic deck slab it is set into */ { const [sw, ww] = sdWall(u, tt, plateFloor ? Math.max(z, DOOR.z0 + 1e-4) : z); if (sw < s) { s = sw; who = ww; } } { const [sl, wl] = sdLadder(u, tt, z); if (sl < s) { s = sl; who = wl; } }
  const [dt_, wt] = nearTri(u, tt, z, plateFloor); const D = s < 0 ? s : Math.min(s, dt_); const part = s < 0 || s <= dt_ ? who : wt; return [D, part]; }
const HANDRE = /(^|_)(Hand|Finger|Thumb|Index|Middle|Ring|Pinky|Palm)/i, isHandBone = bn => HANDRE.test(bn);
const handKey = bn => !isHandBone(bn) ? null : /_L(\b|$|_)/.test(bn) ? 'Hand_L' : /_R(\b|$|_)/.test(bn) ? 'Hand_R' : null;   // side, as wb.js
const rungIdx = z => { let bi = -1, bd = 0.3; rungs.forEach((r, i) => { if (Math.abs(z - r) < bd) { bd = Math.abs(z - r); bi = i; } }); return bi; };
function gripRungOf(c) { let best = 1e9, bi = -1; for (let i = 0; i < rungs.length; i++) { const d = segD(c, [RUNGP[i].u, -0.28, rungs[i]], [RUNGP[i].u, 0.28, rungs[i]]); if (d < best) { best = d; bi = i; } } return bi; }   // wb.js: nearest rung, no cap
const HOLD_STILL_M = RULES.hand_grip_resting.hold_still_m, HOLD_HALF = Math.max(1, Math.round(RULES.hand_grip_resting.hold_window_s * SHZ)); RULES.hand_grip_resting.hold_half_samples = HOLD_HALF;
function heldOf(W, i) {   // W[j] = { bp: hand-bone position, rung } or null (hand not drawn), one clip run; = wb.js gradeHands
  if (i - HOLD_HALF < 0 || i + HOLD_HALF >= W.length) return { held: false, why: 'window incomplete (run edge)', move_m: 0 };
  let why = null; const P = []; for (let j = i - HOLD_HALF; j <= i + HOLD_HALF; j++) { const q = W[j]; if (!q) return { held: false, why: 'hand not visible in window', move_m: 0 }; if (q.rung !== W[i].rung) why = 'held rung changes in window'; P.push(q.bp); }
  let mv = 0; for (let a = 0; a < P.length; a++) for (let b = a + 1; b < P.length; b++) mv = Math.max(mv, Math.hypot(P[a][0] - P[b][0], P[a][1] - P[b][1], P[a][2] - P[b][2]));
  if (!why && mv > HOLD_STILL_M + 1e-9) why = 'hand moved ' + (mv * 1000).toFixed(2) + ' mm'; return { held: !why, why, move_m: mv }; }
function judge(u, tt, z, bn, soleBand, still, hc) {   // hc = { held, rung } for this vertex's hand (held-grip rule)
  const [D, part] = clearOf(u, tt, z, false);
  if (D > 0.03) return { cat: 'clear', part, D };
  const isHand = isHandBone(bn), isFoot = bn.startsWith('Foot_');
  if (isHand && (part === 'ladder_rail' || part === 'rung')) { if (D >= -RULES.hand_grip.max_sink_m) return { cat: 'hand_grip', part, D, grip: true };
    if (part === 'rung' && hc && hc.held && hc.rung >= 0 && rungIdx(z) === hc.rung && D >= -RULES.hand_grip_resting.max_sink_m) return { cat: 'hand_grip_resting', part, D, grip: true };
    return { cat: 'flag', part, D, extra: 'hand_sink', grip: true }; }
  if (isFoot && soleBand && still) {
    if (onPlate(u, tt) && z < PLATE.top + 0.03) {   // resting sole over the plate's real footprint
      const sink = z - PLATE.top; if (sink < -RULES.resting_soles.max_sink_m) return { cat: 'flag', part: 'hatch_plate', D: sink, extra: 'sole_sink' };
      const [Do, po] = clearOf(u, tt, z, true); if (Do > 0.03) return { cat: 'sole_on_plate', part: 'hatch_plate', D: sink };
      return { cat: 'flag', part: po, D: Do }; }      // something other than the plate (sill, jamb, hull, ...) is within 3 cm: normal rule
    if (part === 'deck_wing' || part === 'deck_bridge') { if (z >= DECK - RULES.resting_soles.max_sink_m) return { cat: 'sole_on_deck', part, D: z - DECK }; return { cat: 'flag', part, D: z - DECK, extra: 'sole_sink' }; }
    if (part === 'rung') { const ri = rungIdx(z); const top = ri >= 0 ? RUNGP[ri].top : -1e9;
      if (z >= top - 0.03 && z < top + 0.03) { if (z >= top - RULES.resting_soles.max_sink_m) return { cat: 'sole_on_rung', part, D: z - top }; return { cat: 'flag', part, D: z - top, extra: 'sole_sink' }; } } }
  if (part === 'ladder_rail' && D >= -RULES.rails_depth.max_depth_m) return { cat: 'near_miss', part, D };   // GATE FINAL: rails fail on depth > 5 mm only (= wb.js); 3 cm = warning
  return { cat: 'flag', part, D }; }
const cageInfo = () => ({ source: 'Ship_Placeholder mesh, connected components', verts: CAGE.verts.size, index_range: CAGE.index_range, hoops: CAGE.hoops.map(h => ({ z: +h.z.toFixed(4), r: +h.r.toFixed(4), outer_u: +Math.max(...h.st.map(c => c[0])).toFixed(4), t_ends: [+h.st[0][1].toFixed(4), +h.st[6][1].toFixed(4)], stations: h.st.map(c => c.map(x => +x.toFixed(4))) })), verticals: CAGE.bars.map(b => ({ u: +b.u.toFixed(4), t: +b.t.toFixed(4), z0: +b.z0.toFixed(4), z1: +b.z1.toFixed(4), r: +b.r.toFixed(4) })) });
// ---- PLATE_TEST=1: planted-sole harness (synthetic sole patches pushed through judge() + isStill(), the same code the crew vertices use), then exit
if (process.env.PLATE_TEST) {
  const fp = PLATE.fp_ut, cen = fp.reduce((a, p) => [a[0] + p[0] / fp.length, a[1] + p[1] / fp.length], [0, 0]);
  const patch = (cu, ct, z, du = [1, 0], dt2 = [0, 1]) => { const P = []; for (let i = -2; i <= 2; i++) for (let j = -1; j <= 1; j++) P.push([cu + du[0] * 0.02 * i + dt2[0] * 0.01 * j, ct + du[1] * 0.02 * i + dt2[1] * 0.01 * j, z]); return P; };
  const run = (name, pts, moving, expect) => { const z = pts[0][2], cu = pts.reduce((a, p) => a + p[0], 0) / pts.length, ct = pts.reduce((a, p) => a + p[1], 0) / pts.length;
    const prev = moving ? [cu - 0.01, ct, z] : [cu, ct, z]; const still = isStill(prev, cu, ct, z); const cats = {}; let worst = null;
    for (const [u, t, zz] of pts) { const J = judge(u, t, zz, 'Foot_L', true, still); cats[J.cat + (J.extra ? ':' + J.extra : '') + '@' + J.part] = (cats[J.cat + (J.extra ? ':' + J.extra : '') + '@' + J.part] || 0) + 1; if (J.cat === 'flag' && (!worst || J.D < worst.D)) worst = { part: J.part, D: +J.D.toFixed(4), extra: J.extra || null, group: group(J.part, 'Foot_L', zz, J.extra) }; }
    const plateEx = Object.entries(cats).filter(([k]) => k.startsWith('sole_on_plate')).reduce((a, [, n]) => a + n, 0); const got = expect === 'NO_PLATE_EXEMPTION' ? (plateEx ? 'EXEMPTED' : 'NO_PLATE_EXEMPTION') : Object.keys(cats).some(k => k.startsWith('flag')) ? 'FAIL' : 'PASS'; return { case: name, plate_exempt_vertices: plateEx, still, inside_outline: pts.map(p => onPlate(p[0], p[1])).every(Boolean), outside_outline: pts.every(p => !onPlate(p[0], p[1])), expect, got, ok: got === expect, verdicts: cats, worst_flag: worst }; };
  const cases = []; for (const mm of [0, 3, 5]) cases.push(run('on plate, still, sink ' + mm + ' mm', patch(cen[0], cen[1], PLATE.top - mm / 1000), false, 'PASS'));
  cases.push(run('on plate, still, sink 6 mm', patch(cen[0], cen[1], PLATE.top - 0.006), false, 'FAIL'));
  cases.push(run('on plate, MOVING (10 mm/sample), sink 0', patch(cen[0], cen[1], PLATE.top), true, 'FAIL'));
  for (let i = 0; i < fp.length; i++) { const a = fp[i], b = fp[(i + 1) % fp.length], e = [b[0] - a[0], b[1] - a[1]], L = Math.hypot(...e), dn = [e[0] / L, e[1] / L], nO = [dn[1], -dn[0]];   // outward normal (CCW)
    const m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], side = Math.abs(nO[0]) > Math.abs(nO[1]) ? (nO[0] > 0 ? '+u (outboard, ladder-well side, u ' + m[0].toFixed(2) + ')' : '-u (inboard, u ' + m[0].toFixed(2) + ')') : (nO[1] > 0 ? '+t edge (t ' + m[1].toFixed(2) + ')' : '-t edge (t ' + m[1].toFixed(2) + ')');
    cases.push(run('plate height, still, 2 cm OUTSIDE edge ' + i + ' ' + side, patch(m[0] + nO[0] * 0.03, m[1] + nO[1] * 0.03, PLATE.top, dn, nO), false, 'FAIL'));   // rows at 2, 3, 4 cm out
    for (const off of [0.002, 0.05]) cases.push(run('plate height, still, ' + (off * 100) + ' cm outside edge ' + i + ' ' + side + ': not exempt (normal 3 cm rule only)', patch(m[0] + nO[0] * (off + 0.01), m[1] + nO[1] * (off + 0.01), PLATE.top, dn, nO), false, 'NO_PLATE_EXEMPTION')); }
  { const a = fp.find(p => p[0] === Math.max(...fp.map(q => q[0]))); const outU = Math.max(...fp.map(q => q[0])) + 0.03;
    cases.push(run('2 cm ABOVE plate height, still, just off the outboard edge over the hatch sill (u ' + outU.toFixed(3) + ', t 0) - normal rules', patch(outU + 0.01, 0, PLATE.top + 0.02), false, 'FAIL')); }
  // ---- held-grip hand cases (vertices pushed into a rung/rail; hand ctx = heldOf over a synthetic +-HOLD_HALF window, the same function the crew loop uses)
  const RI = 5, rz = rungs[RI], STEP = 0.002 * 60 / SHZ;   // moving = wb.js plant: slides 2 mm per 1/60 s along the rung axis (t)
  const hand = (pts, moving, centroid, name, expect, rungSwap) => { const c = centroid || pts.reduce((a, p) => [a[0] + p[0] / pts.length, a[1] + p[1] / pts.length, a[2] + p[2] / pts.length], [0, 0, 0]);
      const W = []; for (let k = -HOLD_HALF; k <= HOLD_HALF; k++) { const ck = [c[0], c[1] + (moving ? k * STEP : 0), c[2]]; W.push({ bp: ck, rung: rungSwap && k === HOLD_HALF ? gripRungOf(c) + 1 : gripRungOf(ck) }); }
      const H_ = heldOf(W, HOLD_HALF); const hc = { held: H_.held, rung: W[HOLD_HALF].rung }; const cats = {}; let worst = null;
      for (const [u, t, z] of pts) { const J = judge(u, t, z, 'Hand_R', false, false, hc); const kk = J.cat + (J.extra ? ':' + J.extra : '') + '@' + J.part; cats[kk] = (cats[kk] || 0) + 1; if (J.cat === 'flag' && (!worst || J.D < worst.D)) worst = { part: J.part, D: +J.D.toFixed(4), extra: J.extra || null, group: group(J.part, 'Hand_R', z, J.extra) }; }
      const got = Object.keys(cats).some(k => k.startsWith('flag')) ? 'FAIL' : 'PASS'; return { case: name, hand_held: hc.held, not_held_why: H_.why, window_move_mm: +(H_.move_m * 1000).toFixed(2), held_rung: hc.rung, expect, got, ok: got === expect, verdicts: cats, worst_flag: worst }; };
  const onRung = (sink, i = RI) => { const P = []; for (const du of [-0.008, 0, 0.008]) for (const t of [-0.06, -0.03, 0, 0.03, 0.06]) P.push([RUNGP[i].u + du, t, RUNGP[i].top - sink]); return P; };   // real rung top face
  const railP = k => MESHP.pieces.find(p => p.lab === 'rail' && Math.sign(p.cen[1]) === (k === '+t' ? 1 : -1));
  const plantDir = (p, a, dir, mm) => { let lo = 0, hi = 0.2; for (let it = 0; it < 60; it++) { const m_ = (lo + hi) / 2, q = a.map((x, c) => x + dir[c] * m_); if (-pieceSd(p, ...q) > mm / 1000) lo = m_; else hi = m_; } return a.map((x, c) => x + dir[c] * lo); };   // from axis point a along dir to depth mm
  for (const [mm, mv, ex, pt] of [[8, false, 'PASS', 'PT'], [12, false, 'FAIL', 'PT'], [8, true, 'FAIL', 'PT'], [3, false, 'PASS'], [10, false, 'PASS'], [11, false, 'FAIL']]) cases.push(hand(onRung(mm / 1000), mv, null, (pt ? '[Playtester] ' : '') + (mv ? 'MOVING hand (2 mm per 1/60 s along the rung)' : 'held hand') + ', ' + mm + ' mm into its own rung ' + RI + ' (z ' + rz.toFixed(2) + ')', ex));
  { const zr = (rungs[RI] + rungs[RI + 1]) / 2, rp = railP('+t'), P = []; for (const dz of [-0.01, 0, 0.01]) P.push(plantDir(rp, [RAIL['+t'].u, RAIL['+t'].t, zr + dz], [0, 1, 0], 8)); cases.push(hand(P, false, [4.45, 0.0, RUNGP[RI].top - 0.005], '[Playtester] held hand (holding rung ' + RI + '), 8 mm into the ladder RAIL', 'FAIL')); }
  cases.push(hand(onRung(0.008), false, null, 'held hand still, 8 mm into its rung ' + RI + ' but held rung changes at the window edge', 'FAIL', true));
  // ---- rail-top cases (A&A 11:50): real rail top from the mesh; 5 mm ABOVE it must be outside the rail solid, 5 mm INSIDE the rail tube must FAIL
  for (const k of ['+t', '-t']) { const R_ = RAIL[k], s_ = k === '+t' ? 0.28 : -0.28, top = R_.top;
    const rp = railP(k), ax = [R_.u, R_.t], railOnly = p => pieceSd(rp, ...p);   // real rail mesh piece (hex prism, flat top)
    for (const [nm, p, ex, bn] of [['5 mm ABOVE the real rail top, on the axis', [ax[0], ax[1], top + 0.005], 'PASS', null], ['5 mm above the real rail top, 2 cm off axis (inside the old cap)', [ax[0] + 0.02, ax[1], top + 0.005], 'PASS', null],
      ['6 mm INSIDE the rail mesh (radial +u), 0.5 m below the top', plantDir(rp, [ax[0], ax[1], top - 0.5], [1, 0, 0], 6), 'FAIL', 'Shin_R'], ['6 mm INSIDE the rail mesh (radial +u), 10 mm below the top', plantDir(rp, [ax[0], ax[1], top - 0.01], [1, 0, 0], 6), 'FAIL', 'Shin_R'], ['6 mm INSIDE through the flat top (axis, 6 mm below the top)', [ax[0], ax[1], top - 0.006], 'FAIL', 'Shin_R']]) {
      const sd = railOnly(p), solid = sd < 0 ? 'FAIL' : 'PASS'; const Jb = judge(...p, 'Shin_R', false, false, null), Jh = judge(...p, 'Hand_R', false, false, { held: false, rung: -1 });
      cases.push({ case: 'rail ' + k + ' (top z ' + top.toFixed(4) + ' from the mesh): ' + nm, test: 'ladder-rail real mesh piece signed distance (inside < 0)', rail_sd_m: +sd.toFixed(4), expect: ex, got: solid, ok: solid === ex,
        verdicts: { ['Shin_R:' + Jb.cat + (Jb.extra ? ':' + Jb.extra : '') + '@' + Jb.part]: 1, ['Hand_R:' + Jh.cat + (Jh.extra ? ':' + Jh.extra : '') + '@' + Jh.part]: 1 }, judge_Shin_R: { cat: Jb.cat, part: Jb.part, D_m: +Jb.D.toFixed(4) }, judge_Hand_R: { cat: Jh.cat, part: Jh.part, D_m: +Jh.D.toFixed(4) }, at_utz: p.map(x => +x.toFixed(4)) });
      if (bn) { const got = Jb.cat === 'flag' && Jb.part === 'ladder_rail' && Jb.D < 0 ? 'FAIL' : 'PASS'; cases.push({ case: 'rail ' + k + ': judge(Shin_R) ' + nm, expect: 'FAIL', got, ok: got === 'FAIL', verdicts: { [Jb.cat + '@' + Jb.part]: 1 }, D_m: +Jb.D.toFixed(4), at_utz: p.map(x => +x.toFixed(4)) }); } } }
  cases.push(hand(onRung(0.008, RI), false, [4.45, 0, RUNGP[RI + 1].top - 0.005], 'held hand on rung ' + (RI + 1) + ', a vertex 8 mm into a DIFFERENT rung ' + RI, 'FAIL'));
  { const h0 = CAGE.hoops[0], c3 = h0.st[3], P = []; for (const dz of [-0.004, 0, 0.004]) P.push([c3[0] + h0.r - 0.008, c3[1], c3[2] + dz]); cases.push(hand(P, false, null, 'held hand, 8 mm into a cage hoop (mesh hoop 1, front station, z ' + c3[2].toFixed(3) + ')', 'FAIL')); }
  // ---- cage cases: a body vertex 2 cm inside the OLD (pre-widening, 0.75 x 0.5 design) hoop tube, 5 mm inboard of its old centreline; must FAIL while the mesh hoop
  //      is still there (db78a6f7 / next) and PASS once the mesh hoop has moved >= 5 cm outboard (cage60). Expectation is taken from the mesh, not the file name.
  { const HI = 9, OLD = k => [4.45 + 0.75 * Math.sin(Math.PI * k / 6), 0.5 * Math.cos(Math.PI * k / 6), LTOP + 3.2 + 1.6 * HI], h = CAGE.hoops[HI];
    for (const [nm, k0, k1] of [['front station (90 deg)', 3, 3], ['side chord mid (30-60 deg, +t)', 1, 2], ['side chord mid (120-150 deg, -t)', 4, 5]]) {
      const a = OLD(k0), b = OLD(k1), oc = a.map((x, c) => (x + b[c]) / 2); const ax = [oc[0] - 4.45, oc[1], 0], L = Math.hypot(ax[0], ax[1]); const pt = [oc[0] - 0.005 * ax[0] / L, oc[1] - 0.005 * ax[1] / L, oc[2]];
      const mc = h.st[k0].map((x, c) => (x + h.st[k1][c]) / 2), moved = Math.hypot(mc[0] - oc[0], mc[1] - oc[1]); const expect = moved < 0.01 ? 'FAIL' : moved >= 0.05 ? 'PASS' : 'UNDEFINED';
      for (const bn of ['Thigh_R', 'Foot_L']) { const J = judge(pt[0], pt[1], pt[2], bn, false, false, null); const got = J.cat === 'flag' ? 'FAIL' : 'PASS';
        cases.push({ case: 'cage: ' + bn + ' 2 cm inside the OLD hoop ' + (HI + 1) + ' tube, ' + nm, mesh_hoop_moved_m: +moved.toFixed(4), expect, got, ok: got === expect, verdicts: { [J.cat + '@' + J.part]: 1 }, D_m: +J.D.toFixed(4), at_utz: pt.map(x => +x.toFixed(4)) }); } } }
  // ---- real-mesh cases (A&A 00:15): for one piece of every scored mesh label, a point planted 4 mm / 6 mm INSIDE its nearest face (from the piece centroid, along that face normal)
  //      and 5 mm OUTSIDE it. wb metric: depth > 5 mm = FAIL. Gate: signed distance (inside = -depth from the pieces, outside = exact triangle distance) must equal the planted value.
  { const pick = []; const seen = new Set(); for (const [pi, p] of MESHP.pieces.entries()) { const k = p.lab + '|' + (p.lab === 'kerb' || p.part.startsWith('fused') ? p.part : ''); if (seen.has(k)) continue; seen.add(k); pick.push(pi); }
    for (const pi of pick) { const p = MESHP.pieces[pi], only = q => MESHP.pieces.every((o, oi) => oi === pi || pieceSd(o, ...q) > 0.002) && sdWall(...q)[0] > 0.002;   /* base point inside this piece only (e.g. the old pads' middle cage vertical runs up into the kerb frame_outer at t 0) */
      const cands = [p.cen, ...p.pts.map(v => p.cen.map((x, k) => (x + v[k]) / 2))], c = cands.find(q => only(q) && -pieceSd(p, ...q) > 0.008) || p.cen, dc = -pieceSd(p, ...c); let j = 0, bv = -1e9; p.pl.forEach((q, k) => { const x = q[0] * c[0] + q[1] * c[1] + q[2] * c[2] + q[3]; if (x > bv) { bv = x; j = k; } }); const n = p.pl[j].slice(0, 3);
      // outside case: the nearest face whose 5 mm-outside point is not inside another solid (e.g. kerb faces buried in the deck slab are skipped)
      const fo = p.pl.map((q, k) => [k, q[0] * c[0] + q[1] * c[1] + q[2] * c[2] + q[3]]).sort((x, y) => y[1] - x[1]).map(([k, x]) => [p.pl[k], -x]).find(([q, dq]) => { const o = c.map((x, k) => x + q[k] * (dq + 0.005)); return sdf(...o, true)[0] > 0.004 && sdWall(...o)[0] > 0.004 && sdLadder(...o)[0] > 0.004 && sdMesh(...o)[0] > 0; });
      for (const [mm, exWb] of [[4, 'PASS'], [6, 'FAIL'], [-5, 'PASS']]) { if (mm < 0 && !fo) continue; const [nn, dd] = mm < 0 ? [fo[0], fo[1]] : [n, dc]; const pt = c.map((x, k) => x + nn[k] * (dd - mm / 1000)); const [sm, wl] = sdMesh(...pt); const depth = sm < 0 ? -sm : 0; const gotWb = depth > 0.005 + 1e-9 ? 'FAIL' : 'PASS';
        const [D, part] = clearOf(...pt, false); const inGate = GATE_MESH.has(p.lab), okD = !inGate || (Math.abs(D - (-mm / 1000)) < 0.0002 && (mm < 0 || part === (p.lab === 'rail' ? 'ladder_rail' : p.lab)));   /* outside: exact distance; part = nearest-triangle label (ties with coplanar deck faces allowed) */ const J = judge(...pt, 'Shin_R', false, false, null);
        cases.push({ case: 'mesh ' + p.lab + ' (' + p.part + ', piece ' + pi + ', ' + p.pl.length + ' planes, centroid depth ' + (dc * 1000).toFixed(2) + ' mm): Shin_R vertex ' + (mm > 0 ? mm + ' mm INSIDE' : (-mm) + ' mm OUTSIDE') + ' its nearest face', expect: exWb + ' (wb depth>5mm)' + (inGate ? ', gate D = ' + (-mm) + ' mm @' + p.lab : ' [wb metric only: the gate scores ' + p.lab + ' analytically/by its own rule]'), got: gotWb + ', D ' + (D * 1000).toFixed(2) + ' mm @' + part, ok: gotWb === exWb && okD, wb_depth_mm: +(depth * 1000).toFixed(3), wb_label: wl, gate_D_mm: +(D * 1000).toFixed(3), gate_part: part, verdicts: { [J.cat + '@' + J.part + ' (3 cm rule)']: 1 }, at_utz: pt.map(x => +x.toFixed(4)) }); } } }
  const out = { mode: 'PLATE_TEST', mesh_pieces: meshInfo(), skipped_hidden_nodes: SKIPPED, scored_mesh: SHIP_MESH.name, ladder_rails_from_mesh: RAIL, cage: cageInfo(), script_md5_note: 'see the md5 of landing_clear_plate.mjs that produced this file', pad: padF, plate: { mesh: PLATE.mesh, top_y: PLATE.top, bottom_y: PLATE.bottom, top_tris: PLATE.top_tris, plate_faces: [...PLATE.faces], plate_faces_in_tri_grid: PLATE_T.size, footprint_pad_xz: PLATE.fp_xz, footprint_ut: PLATE.fp_ut },
    patch: '5 x 3 sole vertices, 8 x 2 cm, flat at the given z; resting test = isStill(prev, cur) with prev = cur (still) or 10 mm back (moving); hands: heldOf over +-' + HOLD_HALF + ' samples at ' + SHZ + ' Hz', hold_half_samples: HOLD_HALF, sample_hz: SHZ, all_ok: cases.every(c => c.ok), cases };
  fs.writeFileSync(outF, JSON.stringify(out, null, 1)); for (const c of cases) console.log((c.ok ? 'ok  ' : 'BAD ') + c.got.padEnd(5) + c.case + '  ' + JSON.stringify(c.verdicts)); console.log('all_ok', out.all_ok); process.exit(out.all_ok ? 0 : 1); }
const res2 = { ...res, clip: crewF, sample_hz: SHZ, phases: PH, hull_tris: hullTris.length, frames: 0, hits: 0, minClear: 1e9, per_crew: {}, plants: {}, tri_labels: labelCount, rule: 'see rules block', flag: {}, hand_grip: {}, sole_on_deck: {}, sole_on_rung: {} };
// held-grip pre-pass: per clip run, per skinned mesh and hand: hand-bone position + held rung at every sample (needed for the +-0.1 s window)
const HB = {}; for (const m of meshes) { const bo = boneOf[m.uuid], H = {}; for (const hn of ['Hand_L', 'Hand_R']) { const ix = []; for (let i = 0; i < bo.length; i++) if (handKey(bo[i]) === hn) ix.push(i); const b = m.skeleton.bones.find(x => x.name.replace(/^C\d_/, '') === hn); if (ix.length && b) H[hn] = { ix, b }; } HB[m.uuid] = H; }
const HOLDW = {}; { const v2 = new THREE.Vector3(); for (const cn of ['crew_call', 'crew_walk_to_pad', 'crew_climb']) { const clip = clips[cn]; mixer.stopAllAction(); const act = mixer.clipAction(clip); act.reset(); act.setLoop(THREE.LoopOnce); act.clampWhenFinished = true; act.play();
  const N = Math.round(clip.duration * SHZ); const W = HOLDW[cn] = {}; for (const m of meshes) for (const hn in HB[m.uuid]) W[m.uuid + ':' + hn] = new Array(N + 1).fill(null);
  for (let fi = 0; fi <= N; fi++) { mixer.setTime(Math.min(fi * dt, clip.duration)); S.updateMatrixWorld(true);
    for (const m of meshes) { const sc = new THREE.Vector3(); m.skeleton.bones[0].getWorldScale(sc); if (sc.x < 1e-2) continue;
      for (const hn in HB[m.uuid]) { const { ix, b } = HB[m.uuid][hn]; const c = [0, 0, 0]; for (const i of ix) { m.getVertexPosition(i, v2); v2.applyMatrix4(m.matrixWorld); const q = toUTZ(v2); c[0] += q[0] / ix.length; c[1] += q[1] / ix.length; c[2] += q[2] / ix.length; }
        W[m.uuid + ':' + hn][fi] = { bp: toUTZ(b.getWorldPosition(v2)), rung: gripRungOf(c) }; } } } } }
const holdStat = { samples: 0, held: 0, why: {} };
const v = new THREE.Vector3(); let T = 0; const prevSole = {}, open = {};
for (const cn of ['crew_call', 'crew_walk_to_pad', 'crew_climb']) {
  const clip = clips[cn]; mixer.stopAllAction(); const act = mixer.clipAction(clip); act.reset(); act.setLoop(THREE.LoopOnce); act.clampWhenFinished = true; act.play();
  const N = Math.round(clip.duration * SHZ);
  for (let fi = 0; fi <= N; fi++) { const t = Math.min(fi * dt, clip.duration);
    mixer.setTime(t); S.updateMatrixWorld(true); res2.frames++; const tm = T + t;
    for (const m of meshes) {
      const k = crewOf(m); const sc = new THREE.Vector3(); m.skeleton.bones[0].getWorldScale(sc); if (sc.x < 1e-2) continue;
      const P = ph(k, tm); const pc = res2.per_crew[k] || (res2.per_crew[k] = { side: PH[k].side, min_m: 1e9, at_s: null, part: null, bone: null, hits: 0, by_phase: {}, jamb_edge_min_m: 1e9, jamb_edge_at_s: null, jamb_edge_bone: null, hull_min_m: 1e9, hull_at_s: null });
      const bp = pc.by_phase[P] || (pc.by_phase[P] = { min_m: 1e9, at_s: null, part: null });
      const pos = m.geometry.attributes.position, bones = boneOf[m.uuid]; const feet = { Foot_L: [], Foot_R: [] }; const X = new Array(pos.count);
      for (let i = 0; i < pos.count; i++) { m.getVertexPosition(i, v); v.applyMatrix4(m.matrixWorld); X[i] = toUTZ(v); if (feet[bones[i]]) feet[bones[i]].push(X[i]); }
      // resting-sole state per foot (needs the previous sample; prevSole is updated in the plant block below)
      const soleZ = {}, footStill = {};
      for (const fn of ['Foot_L', 'Foot_R']) { const F = feet[fn]; let mz = 1e9; for (const p of F) mz = Math.min(mz, p[2]); const so = F.filter(p => p[2] < mz + 0.015);
        const cu = so.reduce((q, p) => q + p[0], 0) / so.length, ct = so.reduce((q, p) => q + p[1], 0) / so.length; const pr = prevSole[k + ':' + fn];
        soleZ[fn] = mz; footStill[fn] = isStill(pr, cu, ct, mz); }
      const handCtx = {}; for (const hn in HB[m.uuid]) { const W = HOLDW[cn][m.uuid + ':' + hn]; if (!W[fi]) continue; const h = heldOf(W, fi); handCtx[hn] = { held: h.held, rung: W[fi].rung };
        holdStat.samples++; if (h.held) holdStat.held++; else { const w = h.why.startsWith('hand moved') ? 'hand moved > 5 mm' : h.why; holdStat.why[w] = (holdStat.why[w] || 0) + 1; } }
      const rec = (cat, part, bn, D, u, tt, z, extra) => { const bucket = res2[cat] || (res2[cat] = {}); const kk = k + '|' + part + '|' + bn + (extra ? '|' + extra : ''); const e = bucket[kk] || (bucket[kk] = { crew: k, part, bone: bn, group: group(part, bn, z, extra), min_m: 1e9, at_s: null, utz: null, frames_n: 0, t_range: [1e9, -1e9], phase: null, penetrating_n: 0, max_depth_m: 0 });
        e.frames_n++; e.t_range[0] = Math.min(e.t_range[0], tm); e.t_range[1] = Math.max(e.t_range[1], tm); if (D < 0) { e.penetrating_n++; e.max_depth_m = Math.max(e.max_depth_m, -D); }
        if (D < e.min_m) { e.min_m = D; e.at_s = tm; e.utz = [u, tt, z]; e.phase = P; } if (cat === 'flag') { res2.hits += D < 0 ? 1 : 0; res2.minClear = Math.min(res2.minClear, D); } return e; };
      const handNearRod = { Hand_L: false, Hand_R: false }; const wbF = {};
      for (let i = 0; i < pos.count; i++) {
        const [u, tt, z] = X[i]; const bn = bones[i];
        if (u < 3.0 || u > 6.2 || Math.abs(tt) > 2.4 || z > 24.6) continue;
        { const [sm, wl, pi] = sdMesh(u, tt, z); if (pi >= 0) { for (const lb of wl === 'rung' && !isHandBone(bn) ? ['rung', 'rung_nonhand'] : [wl]) if (!wbF[lb] || -sm > wbF[lb][0]) wbF[lb] = [-sm, bn, pi, u, tt, z];   /* = wb.js: rung = every vertex, rung_nonhand = non-hand */ } }
        const J = judge(u, tt, z, bn, bn.startsWith('Foot_') && z < soleZ[bn] + 0.015, !!footStill[bn], handCtx[handKey(bn)]);
        if (J.cat === 'clear') { if (J.D < pc.min_m) { pc.min_m = J.D; pc.at_s = +tm.toFixed(3); pc.part = J.part; pc.bone = bn; pc.utz = [u, tt, z]; } continue; }
        if (J.grip) handNearRod[bn] = true;
        rec(J.cat, J.part, bn, J.D, u, tt, z, J.extra);
      }
      { const W_ = res2.wb_frames || (res2.wb_frames = {}); for (const lb in wbF) { const e = W_[k + '|' + lb] || (W_[k + '|' + lb] = []); const [d_, b_, pi_] = wbF[lb]; e.push([+tm.toFixed(4), +(d_ * 1000).toFixed(2), b_, pi_, MESHP.pieces[pi_].part]); } }
      // rod-through-hand: rod-axis samples inside the closed hand skin
      for (const h of ['Hand_L', 'Hand_R']) { if (!handNearRod[h]) continue; const T = handTris[m.uuid][h]; const lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
        for (const tr of T) for (const vi of tr) for (let c = 0; c < 3; c++) { lo[c] = Math.min(lo[c], X[vi][c] - 0.01); hi[c] = Math.max(hi[c], X[vi][c] + 0.01); }
        for (const [rn, A, B] of gripRods) { const dir = sub(B, A), L = Math.hypot(...dir); let s0 = 0, s1 = L; const dn = dir.map(x => x / L);
          for (let c = 0; c < 3 && s0 <= s1; c++) { if (Math.abs(dn[c]) < 1e-9) { if (A[c] < lo[c] || A[c] > hi[c]) s1 = -1; continue; } let q0 = (lo[c] - A[c]) / dn[c], q1 = (hi[c] - A[c]) / dn[c]; if (q0 > q1) [q0, q1] = [q1, q0]; s0 = Math.max(s0, q0); s1 = Math.min(s1, q1); }
          if (s0 > s1) continue; let inside = 0, first = null;
          // exact: every crossing of the axis segment with the hand skin, then the winding number at each interval midpoint
          const hits = [s0, s1]; for (const [a_, b_, c_] of T) { const e1 = sub(X[b_], X[a_]), e2 = sub(X[c_], X[a_]), pv = cross(dn, e2), det = e1[0] * pv[0] + e1[1] * pv[1] + e1[2] * pv[2]; if (Math.abs(det) < 1e-14) continue;
            const tv = sub(A, X[a_]), uu = (tv[0] * pv[0] + tv[1] * pv[1] + tv[2] * pv[2]) / det; if (uu < 0 || uu > 1) continue; const qv = cross(tv, e1), vv = (dn[0] * qv[0] + dn[1] * qv[1] + dn[2] * qv[2]) / det; if (vv < 0 || uu + vv > 1) continue;
            const q = (e2[0] * qv[0] + e2[1] * qv[1] + e2[2] * qv[2]) / det; if (q > s0 && q < s1) hits.push(q); }
          hits.sort((x, y) => x - y); let inLen = 0, mw = 0;
          for (let hI = 0; hI + 1 < hits.length; hI++) { const len = hits[hI + 1] - hits[hI]; if (len < 1e-5) continue; const qm = (hits[hI] + hits[hI + 1]) / 2, pt = [A[0] + dn[0] * qm, A[1] + dn[1] * qm, A[2] + dn[2] * qm]; const w = Math.abs(winding(pt, T, X)); mw = Math.max(mw, w);
            if (w > 0.5) { inLen += len; if (!first) first = pt; } }
          const crossings = hits.length - 2; inside = crossings > 0 || inLen > 0 ? 1 : 0;
          if (inside && !first) { const qm = hits[1]; first = [A[0] + dn[0] * qm, A[1] + dn[1] * qm, A[2] + dn[2] * qm]; }
          if (process.env.DEBUG_T && Math.abs(tm - +process.env.DEBUG_T) < 0.02 && k === process.env.DEBUG_K && h === process.env.DEBUG_H) console.error('DEBUG_T', k, h, rn, A[2].toFixed(2), 'crossings', hits.length - 2, 'max|w|', mw.toFixed(3), 'inside len', inLen.toFixed(4));
          if (inside) { const e = rec('flag', rn, h, -inLen, ...first, 'rod_through'); e.axis_inside_solid_len_m = Math.max(e.axis_inside_solid_len_m || 0, inLen); e.max_axis_crossings = Math.max(e.max_axis_crossings || 0, crossings);
            if (inLen === 0) e.samples_crossing_only_zero_thickness_skin = (e.samples_crossing_only_zero_thickness_skin || 0) + 1; else e.samples_axis_inside_solid = (e.samples_axis_inside_solid || 0) + 1; }
          else { const g = res2.grip_rod_checks || (res2.grip_rod_checks = {}); const kk = k + '|' + rn + '|' + h; g[kk] = (g[kk] || 0) + 1; } } }
      // ---- soles + plants (near deck height, from 1 s before the climb top to inside_hatch)
      for (const fn of ['Foot_L', 'Foot_R']) {
        const F = feet[fn]; const key = k + ':' + fn; let mz = 1e9; for (const p of F) mz = Math.min(mz, p[2]);
        const sole = F.filter(p => p[2] < mz + 0.015); const cu = sole.reduce((a, p) => a + p[0], 0) / sole.length, ct = sole.reduce((a, p) => a + p[1], 0) / sole.length;
        const pr = prevSole[key]; prevSole[key] = [cu, ct, mz];
        const near = mz > 21.70 && mz < 22.00 && tm > PH[k].s - 1 && tm < PH[k].i;
        const still = pr && Math.hypot(cu - pr[0], ct - pr[1]) < 0.004 && Math.abs(mz - pr[2]) < 0.003;
        if (near && still) {
          const o = open[key] || (open[key] = { crew: k, foot: fn, land_s: +(tm - dt).toFixed(3), end_s: null, u: [1e9, -1e9], t: [1e9, -1e9], sole_min_z: 1e9, sole_max_z_of_contact: -1e9, where: {}, unsupported_vertex_frames: 0, frames: 0 });
          o.frames++; o.end_s = +tm.toFixed(3); o.sole_min_z = Math.min(o.sole_min_z, mz);
          for (const p of sole) { o.u[0] = Math.min(o.u[0], p[0]); o.u[1] = Math.max(o.u[1], p[0]); o.t[0] = Math.min(o.t[0], p[1]); o.t[1] = Math.max(o.t[1], p[1]);
            const w = support(p[0], p[1]); o.where[w] = (o.where[w] || 0) + 1; if (w === 'well' || w === 'off_edge' || w === 'inside_hull') o.unsupported_vertex_frames++; }
        } else if (open[key]) { (res2.plants[k] || (res2.plants[k] = [])).push(open[key]); delete open[key]; }
      }
    }
  }
  T += clip.duration;
}
for (const key in open) (res2.plants[open[key].crew] || (res2.plants[open[key].crew] = [])).push(open[key]);
// plant summary: surface + gap to the surface it rests on
const sumP = { plants: 0, unsupported_plants: 0, hover_gt_2cm: 0, sinking: 0, gap_m: [1e9, -1e9], walk_in_wing_plants: [] };
for (const k in res2.plants) for (const p of res2.plants[k]) {
  const w = Object.entries(p.where).sort((a, b) => b[1] - a[1]); p.surface = w[0][0]; const top = p.surface === 'kerb' ? KERB : DECK;
  p.gap_to_surface_m = p.sole_min_z - top; p.where_counts = p.where; delete p.where; sumP.plants++;
  if (p.unsupported_vertex_frames > 0) sumP.unsupported_plants++;
  if (p.surface !== 'hatch_doorway') { sumP.gap_m[0] = Math.min(sumP.gap_m[0], p.gap_to_surface_m); sumP.gap_m[1] = Math.max(sumP.gap_m[1], p.gap_to_surface_m); if (p.gap_to_surface_m > 0.02) sumP.hover_gt_2cm++; if (p.gap_to_surface_m < -0.002) sumP.sinking++; }
  if (p.land_s > PH[k].s && p.u[0] < 4.4 && p.u[0] > 3.85 && Math.abs(p.t[0] + p.t[1]) / 2 > 0.6) sumP.walk_in_wing_plants.push({ crew: k, foot: p.foot, land_s: p.land_s, u: p.u, t: p.t, surface: p.surface, unsupported_vertex_frames: p.unsupported_vertex_frames, gap_m: p.gap_to_surface_m }); }
res2.plant_summary = sumP; RULES.sample_hz = SHZ; res2.hand_hold_samples = holdStat; res2.rules = RULES;
const CREW_SEL = process.env.CREW ? process.env.CREW.split(',').map(x => 'Crew_' + x.trim().replace(/^Crew_/, '')) : null;   // scoring filter only; all crew are still simulated
const scoreOf = flags => { const byGroup = {}; for (const e of Object.values(flags)) { const g = byGroup[e.group] || (byGroup[e.group] = { n_entries: 0, min_m: 1e9, worst: null, crews: [] }); g.n_entries++; if (!g.crews.includes(e.crew)) g.crews.push(e.crew); if (e.min_m < g.min_m) { g.min_m = e.min_m; g.worst = { crew: e.crew, part: e.part, bone: e.bone, at_s: e.at_s, utz: e.utz, max_depth_m: e.max_depth_m, axis_inside_solid_len_m: e.axis_inside_solid_len_m, max_axis_crossings: e.max_axis_crossings } } } return byGroup; };
const allGroups = ['hand_grip_sink_gt_5mm', 'hand_grip_rod_through_hand', 'resting_sole_sink_gt_5mm', 'ladder_rails', 'ladder_top_rails', 'rungs', 'cage', 'hatch_jamb_lintel', 'kerb', 'gate', 'landing_brace', 'guard_rail', 'shins_over_deck', 'deck_non_resting', 'hull', 'other_ship'];
const exStat = b => { let mn = 1e9; for (const e of Object.values(b || {})) mn = Math.min(mn, e.min_m); return { entries: Object.keys(b || {}).length, min_m: mn === 1e9 ? null : mn }; };
const allFlags = res2.flag || {}, selFlags = CREW_SEL ? Object.fromEntries(Object.entries(allFlags).filter(([, e]) => CREW_SEL.includes(e.crew))) : allFlags;
const catsOf = bg => Object.fromEntries(allGroups.map(g => [g, bg[g] ? { status: 'FAIL', ...bg[g] } : { status: 'PASS' }])); const byGroup = scoreOf(selFlags), byGroupAll = scoreOf(allFlags);
const nPass = bg => allGroups.filter(g => !bg[g]).length;
res2.summary = { scored_crew: CREW_SEL || 'all (Crew_1-4)', result: Object.keys(selFlags).length ? 'FAIL' : 'PASS', pass_n: nPass(byGroup) + '/' + allGroups.length, clip: crewF, pad: padF, by_category: catsOf(byGroup),
  all_crew: { result: Object.keys(allFlags).length ? 'FAIL' : 'PASS', pass_n: nPass(byGroupAll) + '/' + allGroups.length, by_category: catsOf(byGroupAll) },
  exempt: { hand_grip_within_5mm: exStat(res2.hand_grip), hand_grip_resting_within_10mm: exStat(res2.hand_grip_resting), hand_hold_samples: holdStat, sole_on_deck_within_5mm: exStat(res2.sole_on_deck), sole_on_rung_within_5mm: exStat(res2.sole_on_rung), sole_on_plate_within_5mm: exStat(res2.sole_on_plate) }, plate: PLATE ? { top_y: PLATE.top, footprint_pad_xz: PLATE.fp_xz, faces: PLATE.faces.size } : null, plants: { n: sumP.plants, unsupported: sumP.unsupported_plants, hover_gt_2cm: sumP.hover_gt_2cm, sinking: sumP.sinking } };
res2.summary.line = 'scored ' + (CREW_SEL ? CREW_SEL.join(',') : 'all crew') + ': ' + res2.summary.result + ' ' + res2.summary.pass_n + ' - ' + allGroups.map(g => g + ':' + res2.summary.by_category[g].status).join(', ');
res2.summary.all_crew.line = 'all crew: ' + res2.summary.all_crew.result + ' ' + res2.summary.all_crew.pass_n;
{ const W_ = res2.wb_frames || {}, S_ = {}; for (const kk in W_) { const a = W_[kk]; let w = a[0]; for (const x of a) if (x[1] > w[1]) w = x; S_[kk] = { worst_mm: w[1], at_s: w[0], bone: w[2], piece: w[4], frames_over_5mm: a.filter(x => x[1] > 5 + 1e-9).length }; }
  res2.summary.wb_equivalent = { rule: 'wb.js 0cc51f8d metric: per crew x label, deepest vertex inside a real-mesh convex piece per frame; FAIL > 5 mm (held-hand-on-own-rung 10 mm allowance not applied here: see rung)', by: S_, fails: Object.entries(S_).filter(([k, x]) => x.frames_over_5mm && (!CREW_SEL || CREW_SEL.includes(k.split('|')[0]))).map(([k, x]) => k + ' ' + x.worst_mm + 'mm@' + x.at_s) }; }
{ const nm = Object.values(res2.near_miss || {}).filter(e => !CREW_SEL || CREW_SEL.includes(e.crew)).sort((a, b) => a.min_m - b.min_m);
  res2.summary.warnings = { rule: 'REPORT ONLY (never fails): ladder-rail vertices closer than 3 cm but not deeper than 5 mm', n_entries: nm.length, near_miss: nm.map(e => ({ crew: e.crew, group: e.group, bone: e.bone, min_m: e.min_m, at_s: e.at_s, frames_n: e.frames_n, penetrating_n: e.penetrating_n, max_depth_m: e.max_depth_m })) }; }
const r3 = x => typeof x === 'number' ? +x.toFixed(4) : Array.isArray(x) ? x.map(r3) : x && typeof x === 'object' ? Object.fromEntries(Object.entries(x).map(([a, b]) => [a, r3(b)])) : x;
fs.writeFileSync(outF, JSON.stringify(r3({ summary: res2.summary, rules: res2.rules, ...res2 }), null, 1));
const brief = b => Object.values(b).sort((x, y) => x.min_m - y.min_m).map(e => [e.crew, e.part, e.bone, +e.min_m.toFixed(4), +e.at_s.toFixed(2), e.t_range.map(x => +x.toFixed(2)), e.frames_n, e.penetrating_n, +e.max_depth_m.toFixed(4), e.phase]);
console.log(res2.summary.line); console.log(res2.summary.all_crew.line); console.log('wb_equivalent FAIL (>5 mm):', JSON.stringify(res2.summary.wb_equivalent.fails)); console.log('WARNING (report only):', JSON.stringify(res2.summary.warnings.near_miss.map(e => [e.crew, e.group, e.bone, +(e.min_m * 1000).toFixed(1), +e.at_s.toFixed(2)]))); console.log(JSON.stringify(r3(res2.summary.by_category))); console.log(JSON.stringify(r3(res2.summary.exempt)), JSON.stringify(r3(res2.grip_rod_checks || {})));
