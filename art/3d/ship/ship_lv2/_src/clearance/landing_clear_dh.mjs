// SCRATCH Lv2 copy: every landing/hatch/ladder-top literal z in [20,25) is raised by DH (env, default 3.6); rungs follow LADT; cage hoops = Lv1 rule
// below YS 18.3, +DH above, plus the hoops of [YS-DH,YS) repeated +DH (= mk_lv2.py). Lv1 analytic solids otherwise unchanged.
// v3.1 (art lead rulings 02:15): hand grips may sink <= 5 mm into a rail/rung and the rod axis must not lie inside the hand's skin (rod-through-hand test,
//   generalized winding number); resting soles (still) on the deck or a rung top exempt within 0-5 mm sink; everything else >= 3 cm.
// v3: 3 cm rule on every Ship-node triangle (spatial grid), ladder rails/rungs/cage added; exemptions = planted soles on deck, hands gripping ladder.
// v2: per-crew phase times + hull wall / hatch jamb + sole support + sole gap.
// Clearance of the 4 skinned climbers (all clips back to back, 15 Hz, pad-local) against the hatch landing solids (analytic SDF, mirrors
// lp_stainless_ship.py), plus a check that the GLB's landing triangles sit on those solids. Usage: node landing_clear.mjs crew.glb pad.glb out.json
import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
await MeshoptDecoder.ready;
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const [crewF, padF, outF] = process.argv.slice(2);
const DH = +(process.env.DH ?? 3.6), YS = 18.3;
const pad = (await load(padF)).scene; pad.updateMatrixWorld(true);
const C = pad.getObjectByName('Ship_Center').getWorldPosition(new THREE.Vector3());
const LF = pad.getObjectByName('Ladder_Foot').getWorldPosition(new THREE.Vector3());
const LAD = 330 * Math.PI / 180, LU = [Math.cos(LAD), Math.sin(LAD)], LT = [-LU[1], LU[0]];
const toUTZ = v => { const bx = v.x - C.x, by = -(v.z - C.z); return [bx * LU[0] + by * LU[1], bx * LT[0] + by * LT[1], v.y]; };
// ---- landing solids (u, t, z)
const R = 4.0, TOP = (21.85 + DH), hu = t => Math.sqrt(R * R - t * t) - 0.03;
const boxes = [   // [name, u0 (number or 'hull'), u1, t0, t1, z0, z1]  (|t| mirrored when sym)
  ['deck_wing', 'hull', 5.45, 0.62, 1.40, (21.75 + DH), TOP, 1], ['deck_bridge', 5.15, 5.45, -0.62, 0.62, (21.75 + DH), TOP, 0],
  ['frame_side', 'hull', 5.21, 0.62, 0.68, (21.66 + DH), (21.88 + DH), 1], ['frame_outer', 5.15, 5.21, -0.62, 0.62, (21.66 + DH), (21.88 + DH), 0],
  ['beam_outer', 5.38, 5.45, -1.40, 1.40, (21.61 + DH), (21.75 + DH), 0], ['beam_side', 'hull', 5.38, 1.33, 1.40, (21.61 + DH), (21.75 + DH), 1]];
const OPEN = 100 * Math.PI / 180, HU = 5.21 + 0.035, HZ = (21.88 + DH) + 0.02, LL = 1.16, d = [Math.cos(Math.PI - OPEN), Math.sin(Math.PI - OPEN)], n = [d[1], -d[0]];
const at = (s, k = 0) => [HU + d[0] * s + n[0] * k, HZ + d[1] * s + n[1] * k];
const caps = [];  // [name, a(u,t,z), b, r]
for (const sg of [-1, 1]) {
  caps.push(['brace', [5.41, sg * 1.36, (21.63 + DH)], [hu(1.0) + 0.02, sg * 1.0, (20.50 + DH)], 0.03]);
  const A = [4.15, sg * 1.34], B = [5.40, sg * 1.34], Cc = [5.40, sg * 0.76];
  for (const p of [A, [(A[0] + B[0]) / 2, A[1]], B, Cc]) caps.push(['rail_post', [p[0], p[1], TOP], [p[0], p[1], TOP + 1.05], 0.028]);
  for (const [h, r] of [[1.05, 0.032], [0.525, 0.024]]) { caps.push(['rail', [A[0], A[1], TOP + h], [B[0], B[1], TOP + h], r]); caps.push(['rail', [B[0], B[1], TOP + h], [Cc[0], Cc[1], TOP + h], r]); }
}
caps.push(['lid_hinge', [HU, -0.62, HZ], [HU, 0.62, HZ], 0.035]);
for (const t of [-0.3, 0.3]) { const a = at(0.08, 0.035), b = at(LL - 0.08, 0.035); caps.push(['lid_rib', [a[0], t, a[1]], [b[0], t, b[1]], 0.022]); }
for (const t of [-0.52, 0.52]) { const b = at(0.62, 0.03); caps.push(['lid_strut', [5.40, t, TOP + 0.01], [b[0], t, b[1]], 0.018]); }
const sdBox = (q, h) => { const o = q.map((x, i) => Math.abs(x) - h[i]); const out = Math.hypot(...o.map(x => Math.max(x, 0))); return out + Math.min(Math.max(...o), 0); };
function sdf(u, t, z) {
  let best = 1e9, who = null;
  for (const [nm, u0_, u1, t0, t1, z0, z1, sym] of boxes) {
    const tt = sym ? Math.abs(t) : t; const u0 = u0_ === 'hull' ? hu(Math.min(Math.max(tt, t0), t1)) : u0_;
    const s = sdBox([u - (u0 + u1) / 2, tt - (t0 + t1) / 2, z - (z0 + z1) / 2], [(u1 - u0) / 2, (t1 - t0) / 2, (z1 - z0) / 2]);
    if (s < best) { best = s; who = nm; }
  }
  { const c = at(LL / 2), du = u - c[0], dz = z - c[1]; const s = sdBox([du * d[0] + dz * d[1], t, du * n[0] + dz * n[1]], [LL / 2, 0.65, 0.025]); if (s < best) { best = s; who = 'lid'; } }
  for (const [nm, a, b, r] of caps) {
    const ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], ap = [u - a[0], t - a[1], z - a[2]];
    const h = Math.max(0, Math.min(1, (ap[0] * ab[0] + ap[1] * ab[1] + ap[2] * ab[2]) / (ab[0] ** 2 + ab[1] ** 2 + ab[2] ** 2)));
    const s = Math.hypot(ap[0] - ab[0] * h, ap[1] - ab[1] * h, ap[2] - ab[2] * h) - r; if (s < best) { best = s; who = nm; }
  }
  return [best, who];
}
const res = { frame: 'pad-local; u,t,z about Ship_Center along the 330 deg ladder axis', ship_center: [C.x, C.y, C.z], ladder_foot_utz: toUTZ(LF).map(x => +x.toFixed(3)) };
// ---- GLB check: landing triangles (Ship node, inside the landing box, not hull/ladder/hatch) must lie on the solids
{ const ship = pad.getObjectByName('Ship_Placeholder'); let m = null; ship.traverse(o => { if (o.isMesh && !m) m = o; });
  const pos = m.geometry.attributes.position, v = new THREE.Vector3(); let nv = 0, maxOff = 0, oldDeck = 0;
  for (let i = 0; i < pos.count; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld); const [u, t, z] = toUTZ(v);
    if (z < (21.55 + DH) || z > (23.2 + DH) || Math.abs(t) > 1.5 || u < 4.12 || u > 5.6) continue;
    if (u < 4.6 && Math.abs(t) < 0.75 && z > (21.7 + DH)) continue;                       // ladder rail tops / hatch / cage bars
    if (Math.hypot(u - 4.45, Math.abs(t) - 0.28) < 0.06 || (Math.abs(t) < 0.45 && z < (21.86 + DH) && u < 5.25 && u > 4.6 && Math.abs(t) > 0.0 && Math.hypot(u - 4.9, Math.abs(t) - 0.4) < 0.05) || (Math.abs(t) < 0.05 && Math.abs(u - 5.2) < 0.05 && z <= (21.86 + DH))) continue; // ladder / cage bars
    const [s] = sdf(u, t, z); nv++; maxOff = Math.max(maxOff, Math.abs(s));
    if (u > 4.3 && u < 5.1 && Math.abs(t) < 0.55 && z > (21.74 + DH) && z < (21.86 + DH)) oldDeck++; }
  res.glb_landing_vertices = nv; res.glb_max_offset_from_solids_m = +maxOff.toFixed(4); res.glb_vertices_left_in_well = oldDeck; }

// ---- hull wall (real triangles from the Ship node) + hatch doorway (open: |t| < 0.652, z (21.75 + DH)-(23.75 + DH), the placeholder hatch panel is the doorway)
const DOOR = { t: 0.652, z0: (21.75 + DH), z1: (23.75 + DH) }, WALL = 0.10;
const hullTris = [];
{ const ship = pad.getObjectByName('Ship_Placeholder'); let m = null; ship.traverse(o => { if (o.isMesh && !m) m = o; });
  const pos = m.geometry.attributes.position, idx = m.geometry.index, P3 = i => { const q = new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld); return toUTZ(q); };
  for (let f = 0; f < idx.count; f += 3) { const A = P3(idx.getX(f)), B = P3(idx.getX(f + 1)), Cq = P3(idx.getX(f + 2)), V = [A, B, Cq];
    if (Math.max(...V.map(p => p[2])) < (20.6 + DH) || Math.min(...V.map(p => p[2])) > (24.6 + DH) || Math.min(...V.map(p => Math.abs(p[1]))) > 2.2 || Math.max(...V.map(p => p[0])) < 3.0) continue;
    if (!V.every(p => { const r = Math.hypot(p[0], p[1]); return r > 3.90 && r < 4.012; }) || Math.min(...V.map(p => p[0])) < 2.0) continue;            // hull skin only (rings/landing/ladder are outside)
    if (V.every(p => p[0] > 3.92 && p[0] < 4.08 && Math.abs(p[1]) < 0.665 && p[2] > (21.73 + DH) && p[2] < (23.77 + DH))) continue; // the hatch panel itself (rbox u 3.94-4.06, |t| <= 0.652) is the doorway
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
  if (Math.hypot(u, t) > 4.6 || Math.hypot(u, t) < 3.6 || z < (20.6 + DH) || z > (24.6 + DH)) return [1e9, null];
  const dOut = hullSigned([u, t, z]); const sWall = Math.max(dOut, -WALL - dOut);
  const sDoor = sdBox([u - 2.0, t, z - (DOOR.z0 + DOOR.z1) / 2], [2.3, DOOR.t, (DOOR.z1 - DOOR.z0) / 2]);   // doorway prism u -0.3..4.3
  const s = Math.max(sWall, -sDoor); const inDoorBand = z > DOOR.z0 - 0.05 && z < DOOR.z1 + 0.05 && Math.abs(Math.abs(t) - DOOR.t) < 0.25;
  return [s, inDoorBand ? 'hatch_jamb' : (z > DOOR.z1 && Math.abs(t) < DOOR.t + 0.05 ? 'hatch_lintel' : 'hull')]; }
// exact distance to the jamb edges (outer-face corner lines at |t| 0.652, u 3.90-4.06, z (21.75 + DH)-(23.75 + DH)) and lintel edge
const segD = (p, a, b) => { const ab = sub(b, a), ap = sub(p, a); const h = Math.max(0, Math.min(1, dot(ap, ab) / dot(ab, ab))); return Math.hypot(ap[0] - ab[0] * h, ap[1] - ab[1] * h, ap[2] - ab[2] * h); };
const JAMB = [[[4.06, 0.652, (21.75 + DH)], [4.06, 0.652, (23.75 + DH)]], [[4.06, -0.652, (21.75 + DH)], [4.06, -0.652, (23.75 + DH)]], [[4.06, -0.652, (23.75 + DH)], [4.06, 0.652, (23.75 + DH)]]];

// ---- ladder (placeholder geometry, unchanged): rails r 0.035 at u 4.45, t +-0.28, z 0.25-(21.85 + DH); rungs 0.05 x 0.56 x 0.05 at z 0.65 + 0.6 i; cage
const LTOP = 0.25, LADT = (21.85 + DH), ladCaps = [], rungs = [];
for (const s_ of [-0.28, 0.28]) ladCaps.push(['ladder_rail', [4.45, s_, LTOP], [4.45, s_, LADT], 0.035]);
for (let i = 0; i < Math.floor((LADT - LTOP - 0.3) / 0.6); i++) rungs.push(LTOP + 0.4 + i * 0.6);
const HOOPS = []; for (let i = 0; i < 12; i++) { const z0 = LTOP + 3.2 + i * 1.6; if (z0 < YS) HOOPS.push(z0); else HOOPS.push(z0 + DH); if (DH > 0 && z0 >= YS - DH && z0 < YS) HOOPS.push(z0 + DH); }
for (const z of HOOPS) { const pts = []; for (let k = 0; k < 7; k++) { const a = Math.PI * k / 6; pts.push([4.45 + 0.75 * Math.sin(a), 0.5 * Math.cos(a), z]); }
  for (let k = 0; k < 6; k++) ladCaps.push(['cage_hoop', pts[k], pts[k + 1], 0.025]); }
for (const s_ of [-0.4, 0, 0.4]) { const u = 4.45 + 0.75 * (s_ === 0 ? 1 : 0.6); ladCaps.push(['cage_bar', [u, s_, LTOP + 3.2], [u, s_, LADT], 0.025]); }
const capSd = (p, a, b, r) => segD(p, a, b) - r;
function sdLadder(u, t, z) { let best = 1e9, who = null;
  for (const [nm, a, b, r] of ladCaps) { if (z < Math.min(a[2], b[2]) - 0.3 || z > Math.max(a[2], b[2]) + 0.3) continue; const s = capSd([u, t, z], a, b, r); if (s < best) { best = s; who = nm; } }
  if (Math.abs(u - 4.45) < 0.4 && Math.abs(t) < 0.6) { const i = Math.round((z - LTOP - 0.4) / 0.6); if (i >= 0 && i < rungs.length) { const s = sdBox([u - 4.45, t, z - rungs[i]], [0.025, 0.28, 0.025]); if (s < best) { best = s; who = 'rung'; } } }
  return [best, who]; }
// ---- every Ship-node triangle near the boarding route, labelled, in a 0.1 m grid
const HATCH = { u0: 3.80, u1: 4.06 };
const inDoor = (u, t, z) => Math.abs(t) < DOOR.t && z > DOOR.z0 && z < DOOR.z1 && u < HATCH.u1 + 0.002;
const tris = []; const GRID = new Map(), CS = 0.1, key3 = (i, j, k) => i + ',' + j + ',' + k;
{ const ship = pad.getObjectByName('Ship_Placeholder'); let m = null; ship.traverse(o => { if (o.isMesh && !m) m = o; });
  const pos = m.geometry.attributes.position, idx = m.geometry.index, cache = new Map();
  const P3 = i => { if (!cache.has(i)) cache.set(i, toUTZ(new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld))); return cache.get(i); };
  for (let f = 0; f < idx.count; f += 3) { const V = [P3(idx.getX(f)), P3(idx.getX(f + 1)), P3(idx.getX(f + 2))];
    const lo = [0, 1, 2].map(c => Math.min(...V.map(p => p[c]))), hi = [0, 1, 2].map(c => Math.max(...V.map(p => p[c])));
    if (hi[0] < 3.0 || lo[0] > 6.2 || hi[1] < -2.4 || lo[1] > 2.4 || hi[2] < 0 || lo[2] > (24.6 + DH)) continue;
    const c = [(V[0][0] + V[1][0] + V[2][0]) / 3, (V[0][1] + V[1][1] + V[2][1]) / 3, (V[0][2] + V[1][2] + V[2][2]) / 3];
    const n = cross(sub(V[1], V[0]), sub(V[2], V[0])); const L = Math.hypot(...n); if (L < 1e-12) continue; const N = n.map(x => x / L);
    // label: hatch panel / ladder / landing part / hull / other ship
    let label = 'ship_other';
    const inPanel = V.every(p => p[0] > HATCH.u0 - 0.01 && p[0] < HATCH.u1 + 0.01 && Math.abs(p[1]) < DOOR.t + 0.01 && p[2] > DOOR.z0 - 0.01 && p[2] < DOOR.z1 + 0.01);
    if (inPanel) { label = Math.abs(N[1]) > 0.5 ? 'hatch_jamb' : Math.abs(N[2]) > 0.5 ? (c[2] > (22.7 + DH) ? 'hatch_lintel' : 'hatch_sill') : 'hatch_panel_face'; }
    else { const [sl, wl] = sdLadder(...c), [sa, wa] = sdf(...c); const rr = Math.hypot(c[0], c[1]);
      if (Math.abs(sl) < 0.015 && Math.abs(sl) <= Math.abs(sa)) label = wl; else if (Math.abs(sa) < 0.015) label = wa; else if (rr > 3.6 && rr < 4.02 && Math.abs(N[2]) < 0.3) label = 'hull'; }
    if (label === 'hatch_panel_face') continue;          // the panel's outer/inner faces are the doorway the crew walk through
    const T_ = tris.length; tris.push([V[0], V[1], V[2], label]);
    for (let i = Math.floor((lo[0] - 0.03) / CS); i <= Math.floor((hi[0] + 0.03) / CS); i++) for (let j = Math.floor((lo[1] - 0.03) / CS); j <= Math.floor((hi[1] + 0.03) / CS); j++) for (let k = Math.floor((lo[2] - 0.03) / CS); k <= Math.floor((hi[2] + 0.03) / CS); k++) {
      const kk = key3(i, j, k); let a = GRID.get(kk); if (!a) GRID.set(kk, a = []); a.push(T_); } } }
const labelCount = {}; for (const t_ of tris) labelCount[t_[3]] = (labelCount[t_[3]] || 0) + 1;
function nearTri(u, t, z) { const a = GRID.get(key3(Math.floor(u / CS), Math.floor(t / CS), Math.floor(z / CS))); if (!a) return [1e9, null]; let best = 1e9, who = null; const p = [u, t, z], door = inDoor(u, t, z);
  for (const ti of a) { const [A, B, Cq, lb] = tris[ti]; if (door && lb === 'hull') continue; const q = closestTri(p, A, B, Cq); const d = Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]); if (d < best) { best = d; who = lb; } }
  return [best, who]; }
// ---- crew sampling (30 Hz over all three clips back to back)
const g = await load(crewF); const S = g.scene; const mixer = new THREE.AnimationMixer(S);
const clips = Object.fromEntries(g.animations.map(a => [a.name, a]));
const meshes = []; S.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
// v3 (a749662) timings are the default; override with TIMINGS='{"Crew_1":{"s":..,"i":..,"side":1},...}' (climb start s, inside-hatch i, step-off side)
const PH = process.env.TIMINGS ? JSON.parse(process.env.TIMINGS) : { Crew_1: { s: 41.62, i: 47.79, side: 1 }, Crew_2: { s: 45.02, i: 51.19, side: -1 }, Crew_3: { s: 48.42, i: 54.59, side: 1 }, Crew_4: { s: 51.82, i: 57.99, side: -1 } };
const SHZ = +(process.env.HZ || 30), dt = 1 / SHZ, DECK = (21.85 + DH), KERB = (21.88 + DH);
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
const gripRods = [...ladCaps.filter(c => c[0] === 'ladder_rail').map(c => ['ladder_rail', c[1], c[2]]), ...rungs.map(z => ['rung', [4.45, -0.28, z], [4.45, 0.28, z]])];
const RULES = { min_clearance_m: 0.03, hand_grip: { applies: 'Hand_L/Hand_R vertices whose nearest part is a ladder rail or rung', max_sink_m: 0.005, rod_through_hand: 'per sample, for each rail/rung axis clipped to the hand bbox + 1 cm (so the clipped axis starts and ends outside the hand): exact segment-triangle intersection against every Hand-bone triangle, then the generalized winding number at the midpoint of each interval between crossings. FLAG if the axis crosses the hand skin at all, or any interval is inside a closed hand piece (|w| > 0.5). A wrapped grip leaves the axis in the palm/finger cavity with 0 crossings; a rod through the hand (incl. through the back of the glove) must cross the skin. Reports solid inside length and samples where only zero-thickness (double-sided) hand faces are crossed.' },
  resting_soles: { applies: 'Foot_L/Foot_R sole vertices (within 1.5 cm of that foot\'s lowest vertex) of a still foot (sole centroid moved < 5 mm and lowest z < 3 mm since the previous sample) on the deck wing/bridge top (z (21.85 + DH)) or a rung top (rung centre + 0.025)', max_sink_m: 0.005 },
  everything_else: 'any other crew vertex closer than 0.03 m to any Ship-node triangle or inside an analytic solid is flagged (ladder rails, rungs swung past, cage hoops/bars, hatch jamb/lintel, kerb, guard rail, ladder-top rails, shins over the deck, hull, other ship parts)', sample_hz: null };
const group = (part, bn, z, cat) => cat === 'hand_sink' ? 'hand_grip_sink_gt_5mm' : cat === 'rod_through' ? 'hand_grip_rod_through_hand' : cat === 'sole_sink' ? 'resting_sole_sink_gt_5mm' :
  part === 'ladder_rail' ? (z > (21.0 + DH) ? 'ladder_top_rails' : 'ladder_rails') : part === 'rung' ? 'rungs' : part && part.startsWith('cage') ? 'cage' : part && part.startsWith('hatch') ? 'hatch_jamb_lintel' :
  part === 'frame_side' || part === 'frame_outer' ? 'kerb' : part === 'rail' || part === 'rail_post' ? 'guard_rail' : part && part.startsWith('deck') ? (bn.startsWith('Shin') ? 'shins_over_deck' : 'deck_non_resting') : part === 'hull' ? 'hull' : 'other_ship';
const support = (u, t) => { const at = Math.abs(t);
  if (at < DOOR.t && u < 4.06) return 'hatch_doorway';
  if (at > 1.40 || u > 5.45) return 'off_edge';
  if (u >= 5.15 && u <= 5.21 && at <= 0.68) return 'kerb';
  if (at >= 0.62 && at <= 0.68 && u <= 5.21) return u >= hu(at) ? 'kerb' : 'inside_hull';
  if (at < 0.62) return u > 5.21 ? 'bridge' : 'well';
  return u >= hu(at) ? 'wing' : 'inside_hull'; };
const ph = (k, tm) => tm < PH[k].s ? 'before_climb_top' : tm < PH[k].i ? 'through_hole_and_walk_in' : 'hidden';
const res2 = { ...res, clip: crewF, sample_hz: SHZ, phases: PH, hull_tris: hullTris.length, frames: 0, hits: 0, minClear: 1e9, per_crew: {}, plants: {}, tri_labels: labelCount, rule: 'see rules block', flag: {}, hand_grip: {}, sole_on_deck: {}, sole_on_rung: {} };
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
        soleZ[fn] = mz; footStill[fn] = !!pr && Math.hypot(cu - pr[0], ct - pr[1]) < 0.005 && Math.abs(mz - pr[2]) < 0.003; }
      const rec = (cat, part, bn, D, u, tt, z, extra) => { const bucket = res2[cat] || (res2[cat] = {}); const kk = k + '|' + part + '|' + bn + (extra ? '|' + extra : ''); const e = bucket[kk] || (bucket[kk] = { crew: k, part, bone: bn, group: group(part, bn, z, extra), min_m: 1e9, at_s: null, utz: null, frames_n: 0, t_range: [1e9, -1e9], phase: null, penetrating_n: 0, max_depth_m: 0 });
        e.frames_n++; e.t_range[0] = Math.min(e.t_range[0], tm); e.t_range[1] = Math.max(e.t_range[1], tm); if (D < 0) { e.penetrating_n++; e.max_depth_m = Math.max(e.max_depth_m, -D); }
        if (D < e.min_m) { e.min_m = D; e.at_s = tm; e.utz = [u, tt, z]; e.phase = P; } if (cat === 'flag') { res2.hits += D < 0 ? 1 : 0; res2.minClear = Math.min(res2.minClear, D); } return e; };
      const handNearRod = { Hand_L: false, Hand_R: false };
      for (let i = 0; i < pos.count; i++) {
        const [u, tt, z] = X[i]; const bn = bones[i];
        if (u < 3.0 || u > 6.2 || Math.abs(tt) > 2.4 || z > (24.6 + DH)) continue;
        // signed (analytic) penetration test + unsigned distance to every labelled triangle
        let [s, who] = sdf(u, tt, z); { const [sw, ww] = sdWall(u, tt, z); if (sw < s) { s = sw; who = ww; } } { const [sl, wl] = sdLadder(u, tt, z); if (sl < s) { s = sl; who = wl; } }
        const [dt_, wt] = nearTri(u, tt, z); let D = s < 0 ? s : Math.min(s, dt_); const part = s < 0 || s <= dt_ ? who : wt;
        if (D > 0.03) { if (D < pc.min_m) { pc.min_m = D; pc.at_s = +tm.toFixed(3); pc.part = part; pc.bone = bn; pc.utz = [u, tt, z]; } continue; }
        const isHand = bn.startsWith('Hand_'), isFoot = bn.startsWith('Foot_');
        if (isHand && (part === 'ladder_rail' || part === 'rung')) { handNearRod[bn] = true;
          if (D >= -RULES.hand_grip.max_sink_m) rec('hand_grip', part, bn, D, u, tt, z); else rec('flag', part, bn, D, u, tt, z, 'hand_sink'); continue; }
        if (isFoot && z < soleZ[bn] + 0.015 && footStill[bn]) {
          if (part === 'deck_wing' || part === 'deck_bridge') { if (z >= DECK - RULES.resting_soles.max_sink_m) { rec('sole_on_deck', part, bn, z - DECK, u, tt, z); continue; } rec('flag', part, bn, z - DECK, u, tt, z, 'sole_sink'); continue; }
          if (part === 'rung') { const ri = Math.round((z - LTOP - 0.4) / 0.6); const top = ri >= 0 && ri < rungs.length ? rungs[ri] + 0.025 : -1e9;
            if (z >= top - 0.03 && z < top + 0.03) { if (z >= top - RULES.resting_soles.max_sink_m) { rec('sole_on_rung', part, bn, z - top, u, tt, z); continue; } rec('flag', part, bn, z - top, u, tt, z, 'sole_sink'); continue; } } }
        rec('flag', part, bn, D, u, tt, z);
      }
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
        const near = mz > (21.70 + DH) && mz < (22.00 + DH) && tm > PH[k].s - 1 && tm < PH[k].i;
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
res2.plant_summary = sumP; RULES.sample_hz = SHZ; res2.rules = RULES;
const byGroup = {}; for (const e of Object.values(res2.flag)) { const g = byGroup[e.group] || (byGroup[e.group] = { n_entries: 0, min_m: 1e9, worst: null, crews: [] }); g.n_entries++; if (!g.crews.includes(e.crew)) g.crews.push(e.crew); if (e.min_m < g.min_m) { g.min_m = e.min_m; g.worst = { crew: e.crew, part: e.part, bone: e.bone, at_s: e.at_s, utz: e.utz, max_depth_m: e.max_depth_m, axis_inside_solid_len_m: e.axis_inside_solid_len_m, max_axis_crossings: e.max_axis_crossings } } }
const allGroups = ['hand_grip_sink_gt_5mm', 'hand_grip_rod_through_hand', 'resting_sole_sink_gt_5mm', 'ladder_rails', 'ladder_top_rails', 'rungs', 'cage', 'hatch_jamb_lintel', 'kerb', 'guard_rail', 'shins_over_deck', 'deck_non_resting', 'hull', 'other_ship'];
const exStat = b => { let mn = 1e9; for (const e of Object.values(b || {})) mn = Math.min(mn, e.min_m); return { entries: Object.keys(b || {}).length, min_m: mn === 1e9 ? null : mn }; };
res2.summary = { result: Object.keys(res2.flag).length ? 'FAIL' : 'PASS', clip: crewF, pad: padF, by_category: Object.fromEntries(allGroups.map(g => [g, byGroup[g] ? { status: 'FAIL', ...byGroup[g] } : { status: 'PASS' }])),
  exempt: { hand_grip_within_5mm: exStat(res2.hand_grip), sole_on_deck_within_5mm: exStat(res2.sole_on_deck), sole_on_rung_within_5mm: exStat(res2.sole_on_rung) }, plants: { n: sumP.plants, unsupported: sumP.unsupported_plants, hover_gt_2cm: sumP.hover_gt_2cm, sinking: sumP.sinking } };
res2.summary.line = res2.summary.result + ' - ' + allGroups.map(g => g + ':' + res2.summary.by_category[g].status).join(', ');
const r3 = x => typeof x === 'number' ? +x.toFixed(4) : Array.isArray(x) ? x.map(r3) : x && typeof x === 'object' ? Object.fromEntries(Object.entries(x).map(([a, b]) => [a, r3(b)])) : x;
fs.writeFileSync(outF, JSON.stringify(r3({ summary: res2.summary, rules: res2.rules, ...res2 }), null, 1));
const brief = b => Object.values(b).sort((x, y) => x.min_m - y.min_m).map(e => [e.crew, e.part, e.bone, +e.min_m.toFixed(4), +e.at_s.toFixed(2), e.t_range.map(x => +x.toFixed(2)), e.frames_n, e.penetrating_n, +e.max_depth_m.toFixed(4), e.phase]);
console.log(res2.summary.line); console.log(JSON.stringify(r3(res2.summary.by_category))); console.log(JSON.stringify(r3(res2.summary.exempt)), JSON.stringify(r3(res2.grip_rod_checks || {})));
