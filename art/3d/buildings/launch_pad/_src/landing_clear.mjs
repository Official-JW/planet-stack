// v2: per-crew phase times + hull wall / hatch jamb + sole support + sole gap.
// Clearance of the 4 skinned climbers (all clips back to back, 15 Hz, pad-local) against the hatch landing solids (analytic SDF, mirrors
// lp_stainless_ship.py), plus a check that the GLB's landing triangles sit on those solids. Usage: node landing_clear.mjs crew.glb pad.glb out.json  (HZ=30 default)
import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
await MeshoptDecoder.ready;
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const [crewF, padF, outF] = process.argv.slice(2);
const pad = (await load(padF)).scene; pad.updateMatrixWorld(true);
const C = pad.getObjectByName('Ship_Center').getWorldPosition(new THREE.Vector3());
const LF = pad.getObjectByName('Ladder_Foot').getWorldPosition(new THREE.Vector3());
const LAD = 330 * Math.PI / 180, LU = [Math.cos(LAD), Math.sin(LAD)], LT = [-LU[1], LU[0]];
const toUTZ = v => { const bx = v.x - C.x, by = -(v.z - C.z); return [bx * LU[0] + by * LU[1], bx * LT[0] + by * LT[1], v.y]; };
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
    if (z < 21.55 || z > 23.2 || Math.abs(t) > 1.5 || u < 4.12 || u > 5.6) continue;
    if (u < 4.6 && Math.abs(t) < 0.75 && z > 21.7) continue;                       // ladder rail tops / hatch / cage bars
    if (Math.hypot(u - 4.45, Math.abs(t) - 0.28) < 0.06 || (Math.abs(t) < 0.45 && z < 21.86 && u < 5.25 && u > 4.6 && Math.abs(t) > 0.0 && Math.hypot(u - 4.9, Math.abs(t) - 0.4) < 0.05) || (Math.abs(t) < 0.05 && Math.abs(u - 5.2) < 0.05 && z <= 21.86)) continue; // ladder / cage bars
    const [s] = sdf(u, t, z); nv++; maxOff = Math.max(maxOff, Math.abs(s));
    if (u > 4.3 && u < 5.1 && Math.abs(t) < 0.55 && z > 21.74 && z < 21.86) oldDeck++; }
  res.glb_landing_vertices = nv; res.glb_max_offset_from_solids_m = +maxOff.toFixed(4); res.glb_vertices_left_in_well = oldDeck; }

// ---- hull wall (real triangles from the Ship node) + hatch doorway (open: |t| < 0.652, z 21.75-23.75, the placeholder hatch panel is the doorway)
const DOOR = { t: 0.652, z0: 21.75, z1: 23.75 }, WALL = 0.10;
const hullTris = [];
{ const ship = pad.getObjectByName('Ship_Placeholder'); let m = null; ship.traverse(o => { if (o.isMesh && !m) m = o; });
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
// ---- crew sampling (30 Hz over all three clips back to back)
const g = await load(crewF); const S = g.scene; const mixer = new THREE.AnimationMixer(S);
const clips = Object.fromEntries(g.animations.map(a => [a.name, a]));
const meshes = []; S.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
// Art Assistant 3 v2 (3a9718a): through-hole climb start, inside hatch (hidden), step-off side
const PH = { Crew_1: { s: 41.62, i: 47.79, side: 1 }, Crew_2: { s: 45.02, i: 51.19, side: -1 }, Crew_3: { s: 48.42, i: 54.59, side: 1 }, Crew_4: { s: 51.82, i: 57.99, side: -1 } };
const SHZ = +(process.env.HZ || 30), dt = 1 / SHZ, DECK = 21.85, KERB = 21.88;
const crewOf = m => { let p = m; while (p && !/^Crew_\d$/.test(p.name)) p = p.parent; return p ? p.name : m.name; };
const boneOf = {}; for (const m of meshes) { const si = m.geometry.attributes.skinIndex, sw = m.geometry.attributes.skinWeight, names = m.skeleton.bones.map(b => b.name.replace(/^C\d_/, ''));
  boneOf[m.uuid] = new Array(si.count); for (let i = 0; i < si.count; i++) { let bi = 0, bw = -1; for (let c = 0; c < 4; c++) { const w = sw.getComponent(i, c); if (w > bw) { bw = w; bi = si.getComponent(i, c); } } boneOf[m.uuid][i] = names[bi]; } }
const support = (u, t) => { const at = Math.abs(t);
  if (at < DOOR.t && u < 4.06) return 'hatch_doorway';
  if (at > 1.40 || u > 5.45) return 'off_edge';
  if (u >= 5.15 && u <= 5.21 && at <= 0.68) return 'kerb';
  if (at >= 0.62 && at <= 0.68 && u <= 5.21) return u >= hu(at) ? 'kerb' : 'inside_hull';
  if (at < 0.62) return u > 5.21 ? 'bridge' : 'well';
  return u >= hu(at) ? 'wing' : 'inside_hull'; };
const ph = (k, tm) => tm < PH[k].s ? 'before_climb_top' : tm < PH[k].i ? 'through_hole_and_walk_in' : 'hidden';
const res2 = { ...res, clip: crewF, sample_hz: SHZ, phases: PH, hull_tris: hullTris.length, frames: 0, hits: 0, minClear: 1e9, per_crew: {}, per_part: {}, worst_hits: {}, plants: {} };
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
      const pos = m.geometry.attributes.position, bones = boneOf[m.uuid]; const feet = { Foot_L: [], Foot_R: [] };
      for (let i = 0; i < pos.count; i++) {
        m.getVertexPosition(i, v); v.applyMatrix4(m.matrixWorld); const [u, tt, z] = toUTZ(v); const bn = bones[i];
        if (feet[bn]) feet[bn].push([u, tt, z]);
        if (u < 3.0 || u > 6.2 || Math.abs(tt) > 2.2 || z < 19.8 || z > 24.6) continue;
        let [s, who] = sdf(u, tt, z); const [sw, ww] = sdWall(u, tt, z); if (sw < s) { s = sw; who = ww; }
        if (ww) { const dh = hullSigned([u, tt, z]); if (Math.abs(tt) > DOOR.t || z < DOOR.z0 || z > DOOR.z1) { if (sw < pc.hull_min_m) { pc.hull_min_m = sw; pc.hull_at_s = +tm.toFixed(3); } } }
        if (u > 3.7 && u < 4.4 && z > 21.5 && z < 24.0) { let dj = 1e9; for (const [a, b] of JAMB) dj = Math.min(dj, segD([u, tt, z], a, b)); if (dj < pc.jamb_edge_min_m) { pc.jamb_edge_min_m = dj; pc.jamb_edge_at_s = +tm.toFixed(3); pc.jamb_edge_bone = bn; pc.jamb_edge_utz = [u, tt, z]; } }
        if (s < pc.min_m) { pc.min_m = s; pc.at_s = +tm.toFixed(3); pc.part = who; pc.bone = bn; pc.utz = [u, tt, z]; }
        if (s < bp.min_m) { bp.min_m = s; bp.at_s = +tm.toFixed(3); bp.part = who; }
        const pp = res2.per_part[who] || (res2.per_part[who] = { min_m: 1e9, hits: 0, at_s: null, crew: null }); if (s < pp.min_m) { pp.min_m = s; pp.at_s = +tm.toFixed(3); pp.crew = k; }
        if (s < -1e-4) { res2.hits++; pc.hits++; pp.hits++; const key = k + ':' + who; const w = res2.worst_hits[key] || (res2.worst_hits[key] = { depth_m: 0, at_s: null, bone: null, utz: null, n: 0, t_range: [1e9, -1e9] });
          w.n++; w.t_range[0] = Math.min(w.t_range[0], tm); w.t_range[1] = Math.max(w.t_range[1], tm); if (-s > w.depth_m) { w.depth_m = -s; w.at_s = tm; w.bone = bn; w.utz = [u, tt, z]; } }
        res2.minClear = Math.min(res2.minClear, s);
      }
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
res2.plant_summary = sumP;
const r3 = x => typeof x === 'number' ? +x.toFixed(4) : Array.isArray(x) ? x.map(r3) : x && typeof x === 'object' ? Object.fromEntries(Object.entries(x).map(([a, b]) => [a, r3(b)])) : x;
fs.writeFileSync(outF, JSON.stringify(r3(res2), null, 1));
console.log(JSON.stringify(r3({ minClear: res2.minClear, hits: res2.hits, worst_hits: res2.worst_hits, per_part: res2.per_part, plant_summary: { ...sumP, walk_in_wing_plants: sumP.walk_in_wing_plants.length } })));
