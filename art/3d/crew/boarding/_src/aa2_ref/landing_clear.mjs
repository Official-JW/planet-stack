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
// ---- crew sampling
const g = await load(crewF); const S = g.scene; const mixer = new THREE.AnimationMixer(S);
const clips = Object.fromEntries(g.animations.map(a => [a.name, a]));
const meshes = []; S.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
const STAND = { Crew_1: 54.17, Crew_2: 59.67, Crew_3: 65.17, Crew_4: 70.67 };   // 'on deck (mantle done)' from CREW_BOARDING_TIMING.md
const v = new THREE.Vector3(); let T = 0; const dt = 1 / 15;
res.minClear = 1e9; res.per_crew = {}; res.per_part = {}; res.hits = 0; res.frames = 0;
for (const cn of ['crew_call', 'crew_walk_to_pad', 'crew_climb']) {
  const clip = clips[cn]; mixer.stopAllAction(); const act = mixer.clipAction(clip); act.reset(); act.setLoop(THREE.LoopOnce); act.clampWhenFinished = true; act.play();
  for (let t = 0; t <= clip.duration + 1e-6; t += dt) {
    mixer.setTime(t); S.updateMatrixWorld(true); res.frames++; const tm = T + t;
    for (const m of meshes) {
      let p = m; while (p && !/^Crew_\d$/.test(p.name)) p = p.parent; const k = p ? p.name : m.name;
      const sc = new THREE.Vector3(); m.skeleton.bones[0].getWorldScale(sc); if (sc.x < 1e-2) continue;
      const pos = m.geometry.attributes.position; let lowZ = 1e9, lowU = 0, lowT = 0;
      const pc = res.per_crew[k] || (res.per_crew[k] = { min_m: 1e9, at_s: null, part: null, hits: 0, hit_s: [1e9, -1e9], climb_min_m: 1e9, after_mantle_min_m: 1e9, over_well_after_mantle_s: [1e9, -1e9] });
      for (let i = 0; i < pos.count; i++) {
        m.getVertexPosition(i, v); v.applyMatrix4(m.matrixWorld); const [u, tt, z] = toUTZ(v);
        if (z < lowZ) { lowZ = z; lowU = u; lowT = tt; }
        if (u < 3.4 || u > 6.2 || Math.abs(tt) > 2.2 || z < 19.8 || z > 24.5) continue;
        const [s, who] = sdf(u, tt, z);
        if (s < pc.min_m) { pc.min_m = s; pc.at_s = +tm.toFixed(2); pc.part = who; }
        if (tm < STAND[k]) pc.climb_min_m = Math.min(pc.climb_min_m, s); else pc.after_mantle_min_m = Math.min(pc.after_mantle_min_m, s);
        const pp = res.per_part[who] || (res.per_part[who] = { min_m: 1e9, hits: 0 }); pp.min_m = Math.min(pp.min_m, s);
        if (s < 0) { res.hits++; pc.hits++; pp.hits++; pc.hit_s[0] = Math.min(pc.hit_s[0], tm); pc.hit_s[1] = Math.max(pc.hit_s[1], tm); }
        res.minClear = Math.min(res.minClear, s);
      }
      // feet resting at deck height while over the open well (no support) after the climb
      if (lowZ > 21.8 && lowZ < 21.95 && lowU > 4.05 && lowU < 5.15 && Math.abs(lowT) < 0.62) { pc.over_well_after_mantle_s[0] = Math.min(pc.over_well_after_mantle_s[0], tm); pc.over_well_after_mantle_s[1] = Math.max(pc.over_well_after_mantle_s[1], tm); }
    }
  }
  T += clip.duration;
}
const r3 = x => typeof x === 'number' ? +x.toFixed(3) : Array.isArray(x) ? x.map(r3) : x && typeof x === 'object' ? Object.fromEntries(Object.entries(x).map(([a, b]) => [a, r3(b)])) : x;
fs.writeFileSync(outF, JSON.stringify(r3(res), null, 1)); console.log(JSON.stringify(r3(res)));
