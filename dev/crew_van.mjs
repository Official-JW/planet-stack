// Crew van (Jacob 11/10 9:07: "we need the van pickup and drop off for the crew when they land.. that van drive path also needs a trail").
// After a landing's deboarding ends (hook: the deboard → pad step in main.js), a crew van drives to the pad, the crew who landed this trip
// (the picked crew who joined the base in crewLand) walk to its side door and get in, and it drops them off: Engineers at the Shipyard
// (roles.json "Builds new ships at the Shipyard"; they walk the Shipyard's authored Crew_Path_01..05 to Hall_Door_Front), everyone else at the
// Habitat (their beds; authored Crew_Path_01..03 through the airlock). The starting crew keep their approved paths (deboard walk home, Mine taxi truck).
// Jacob 11/10 1:02 PM ("miners go to the mine and mechanics go to the shipyard... the van should do the drop off at both those locations"):
// Mechanics now get off at the Shipyard with the Engineers, and Miners ride on after the Habitat stop to a Mine stop (van road out of every approved
// framing: z 96 behind the Refinery/Dock views, a rock-free gap at x 212-246 down to the Mine, a U-turn so the van stops heading east with the door
// toward the camera), get out and walk the Mine's authored Dep_02 → Crew_Path_04..01. The van then drives back to the pad and home to the Habitat stop.
// Clear of: Art's truck trails, the Refinery bridge, every rock (≥ 1.9 m from the van's centre line), and the ST-10B transporter lane (z −13, x 640-700).
// Purely visual: no sim, money, population or role-counter changes. Everything is a pure function of the trip start time, so a reload mid-trip resumes.
// STAND-IN VAN: the van model is NOT approved (the glass van stills had seating problems). This is a primitive stand-in (boxes + cylinders) with one
// sliding side door (all doors slide); replace with Art's van when approved. Crew are hidden once inside (no seats shown).
// The drive path gets a tire-track trail built like Art's truck trails: same material instance (M_TireTrail texture, vertex colour + alpha), same
// cross-section (9 columns, darker wheel ruts at u .174 / .826), same 4 m texture repeat along the path, scaled to the van's wheel gauge.

const VMAX = 9, ACC = 2.5;            // van m/s, m/s² (trapezoid speed profile)
const WALK_V = 1.4, WALK_ANIM = 0.85;  // same walk speed / clip rate as the 1720 ladder walkers
const DOOR_SEC = 1.2, STAGGER = 1.1, MAXP = 8;   // door slide time, gap between crew at the door, people drawn (van seats)
const GAUGE = 2.0, TRAIL_W = GAUGE / 0.652, TRAIL_V = 0.249, FADE_M = 4;   // truck trail: ruts 0.652 of the width apart; v 0.249 per m
const TRAIL_U = [0, .076, .174, .272, .5, .728, .826, .924, 1], TRAIL_R = [1, 1, .59, 1, 1, 1, .59, 1, 1], TRAIL_A = .98;
const KEY = 'ps3d_crewvan';
const DEST = (role, yard) => role === 'miner' ? 'mine' : (role === 'eng' || role === 'mech') && yard ? 'ship' : 'hab';   // Jacob 1:02 PM: miners → Mine, mechanics (+ engineers) → Shipyard once built; others live in the Habitat
const VHAUL = 14, ALAT = 2.5;          // Mine run only: top speed on the long road (off-screen) and the corner limit (lateral m/s²), so it slows for the U-turn
const TERR = [100, 420, -10, 94];      // x0 x1 z0 z1 where the Mine/Refinery terrain is not flat (probed heights, 5 m grid); rays elsewhere skip it

export function createCrewVan(THREE, D) {
  const st = { ready: false, trip: null, sch: null, van: null, door: null, people: [], trail: null, yCache: new Map(), boxes: null, err: null, buildMs: 0 };
  try { const j = JSON.parse(localStorage.getItem(KEY) || 'null'); if (j && j.T > 0 && Array.isArray(j.roles)) st.trip = j; } catch (e) {}
  const ray = new THREE.Raycaster(), V3 = THREE.Vector3;

  // ---- ground height (station aprons sit a little above y 0): raycast once per 0.5 m cell
  function groundY(x, z) {
    const k = Math.round(x * 2) + ',' + Math.round(z * 2); if (st.yCache.has(k)) return st.yCache.get(k);
    let y = 0; if (!st.boxes) { st.boxes = D.groundRoots().filter(Boolean).map(r => [r, new THREE.Box3().setFromObject(r)]); }
    const roots = st.boxes.filter(([, b]) => x >= b.min.x && x <= b.max.x && z >= b.min.z && z <= b.max.z).map(([r]) => r);   // only the station(s) under this point
    let keep = true; if (x > TERR[0] && x < TERR[1] && z > TERR[2] && z < TERR[3]) { const t = D.terrainRoots ? D.terrainRoots() : []; if (t) roots.push(...t); else keep = false; }   // terrain not loaded yet: don't cache
    if (roots.length) { ray.set(new V3(x, 3, z), new V3(0, -1, 0)); ray.far = 4; let hy = -1e9;
      for (const h of ray.intersectObjects(roots, true)) { if (h.object.visible && h.point.y < 1.2 && h.point.y > hy) hy = h.point.y; } if (hy > -1e9) y = hy; }
    if (keep) st.yCache.set(k, y); return y;
  }
  // ---- smooth path through way points, sampled every 0.5 m
  function mkPath(pts) {
    const c = new THREE.CatmullRomCurve3(pts.map(p => new V3(p[0], 0, p[1])), false, 'centripetal');
    const n = Math.max(8, Math.ceil(c.getLength() / 0.5)), P = c.getSpacedPoints(n), s = [0];
    for (let i = 1; i < P.length; i++) s.push(s[i - 1] + P[i].distanceTo(P[i - 1]));
    return { P, s, L: s[s.length - 1] };
  }
  function along(path, d) {   // [x, z, yaw] at arc length d
    const { P, s, L } = path; d = Math.max(0, Math.min(L, d)); let lo = 0, hi = s.length - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (s[m] <= d) lo = m; else hi = m; }
    const a = P[lo], b = P[hi], u = (d - s[lo]) / ((s[hi] - s[lo]) || 1);
    return [a.x + (b.x - a.x) * u, a.z + (b.z - a.z) * u, Math.atan2(b.x - a.x, b.z - a.z)];
  }
  const driveSec = (L) => { const da = VMAX * VMAX / ACC; return L >= da ? 2 * VMAX / ACC + (L - da) / VMAX : 2 * Math.sqrt(L / ACC); };
  const driveDist = (L, t) => { const T = driveSec(L), ta = Math.min(VMAX / ACC, T / 2), vp = ACC * ta;
    if (t <= 0) return 0; if (t >= T) return L; if (t < ta) return .5 * ACC * t * t; if (t < T - ta) return .5 * ACC * ta * ta + vp * (t - ta);
    const r = T - t; return L - .5 * ACC * r * r; };
  function prof(path, vmax) {   // Mine run: speed limited by vmax, corner radius (ALAT) and ACC, from 0 to 0; time table along the path's samples
    const { P, s } = path, n = P.length, vl = new Float64Array(n), v = new Float64Array(n), t = new Float64Array(n), W = 4;
    for (let i = 0; i < n; i++) { const a = P[Math.max(0, i - W)], b = P[i], c = P[Math.min(n - 1, i + W)];
      const h1 = Math.atan2(b.z - a.z, b.x - a.x), h2 = Math.atan2(c.z - b.z, c.x - b.x); let dh = Math.abs(h2 - h1); if (dh > Math.PI) dh = 2 * Math.PI - dh;
      const k = dh / Math.max(.5, (Math.hypot(b.x - a.x, b.z - a.z) + Math.hypot(c.x - b.x, c.z - b.z)) / 2); vl[i] = Math.min(vmax, Math.sqrt(ALAT / Math.max(k, 1e-6))); }
    v[0] = 0; for (let i = 1; i < n; i++) v[i] = Math.min(vl[i], Math.sqrt(v[i - 1] * v[i - 1] + 2 * ACC * (s[i] - s[i - 1])));
    v[n - 1] = 0; for (let i = n - 2; i >= 0; i--) v[i] = Math.min(v[i], Math.sqrt(v[i + 1] * v[i + 1] + 2 * ACC * (s[i + 1] - s[i])));
    for (let i = 1; i < n; i++) t[i] = t[i - 1] + (s[i] - s[i - 1]) / Math.max(.3, (v[i] + v[i - 1]) / 2);
    return { t, T: t[n - 1] };
  }
  const profDist = (path, pr, u) => { const { t } = pr; if (u <= 0) return 0; if (u >= pr.T) return path.L; let lo = 0, hi = t.length - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (t[m] <= u) lo = m; else hi = m; } return path.s[lo] + (path.s[hi] - path.s[lo]) * (u - t[lo]) / ((t[hi] - t[lo]) || 1); };
  const poly = (pts) => { const s = [0]; for (let i = 1; i < pts.length; i++) s.push(s[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])); return { pts, s, L: s[s.length - 1] }; };
  const polyAt = (pl, d) => { const { pts, s, L } = pl; d = Math.max(0, Math.min(L, d)); let i = 1; while (i < s.length - 1 && s[i] < d) i++;
    const a = pts[i - 1], b = pts[i] || a, u = (d - s[i - 1]) / ((s[i] - s[i - 1]) || 1); return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, Math.atan2(b[0] - a[0], b[1] - a[1])]; };

  // ---- layout from the stations' authored markers (Launch Pad / Shipyard / Habitat)
  function layout() {
    const m = D.marker; const sy = (n) => m(D.SHIPI, n), hb = (n) => m(D.HABI, n);
    const yRoad = sy('Road_Entry'), y1 = sy('Crew_Path_01'), h1 = hb('Crew_Path_01');
    if (!yRoad || !y1 || !h1) return null;
    const PX = D.PX, V = [PX - 4, 26.6], S = [y1[0] - 13.6, y1[1] + 5.2], H = [h1[0] - 8, h1[1] + 3.9];   // stops: in front of the Launch Pad (east of the flatbed U-turn), Shipyard apron front, Habitat door
    // Issue 24: do not use Road_Entry (≈ 749, 21) or a diagonal across the Shipyard base
    // (shipyard_base / SH_Rock ≈ x 748–862, z −36–47). Stay west of x 742 until z ≥ 54, then
    // run along the camera-side front (z ≈ 53–54) to the existing apron stop S. The pad loop
    // still leaves the main route at (PX+90, 22). Clear of the ST-10B lane (z −13, x 640–700)
    // and of the Habitat / Life Support footprints east of the yard.
    const YW = 742, YF = 54;
    const main = mkPath([V, [PX + 15, 27], [PX + 35, 27.6], [PX + 60, 26], [PX + 90, 22],
      [YW, 22], [YW, 36], [YW, YF], [YW + 18, YF], [S[0] - 20, YF - 1], S,
      [S[0] + 15, S[1] + 1], [S[0] + 50, YF - 1], [866, YF - 1], [H[0] - 47, H[1] + 13.5], [H[0] - 17, H[1] + 2.5], H]);
    const sS = main.s[main.P.reduce((bi, p, i) => (Math.hypot(p.x - S[0], p.z - S[1]) < Math.hypot(main.P[bi].x - S[0], main.P[bi].z - S[1]) ? i : bi), 0)];
    const J = [PX + 90, 22];   // the drive-in leaves the main route here and loops round in front of the pad so the van stops heading east (door toward the camera)
    const loopPts = [J, [PX + 62, 33], [PX + 38, 35.5], [PX + 10, 35.5], [PX - 14, 34], [PX - 22, 29.5], [PX - 15, 26.7], V];
    const back = []; for (let i = main.P.length - 1; i >= 0; i--) { const p = main.P[i]; if (p.x < J[0] + 3) break; if (i % 6 === 0) back.push([p.x, p.z]); }
    const inPath = mkPath([...back, ...loopPts]);
    const loop = mkPath(loopPts);
    const Lo = { V, S, H, main, sS, inPath, loop, shipWalk: ['Crew_Path_01', 'Crew_Path_02', 'Crew_Path_03', 'Crew_Path_04', 'Crew_Path_05'].map(sy),
      habWalk: ['Crew_Path_01', 'Crew_Path_02', 'Crew_Path_03'].map(hb) };
    // Mine run (world x/z; stations sit at i·160). Lane z 96 is past the bottom of the Refinery (z 76) and Dock (z 88) framings; x 212-246 is the
    // rock-free gap down to the Mine; west on z 36 into the Mine framing, U-turn (r 9.25) round x 154, stop M heading east on z 17.5 (Art's Mine
    // truck trail ends at z 12 and the loading truck at z ~13.5; rocks start at z 20.9 east of x 173). Out leaves the pad loop at (PX+10, 35.5); back joins the loop tail just before V.
    const mn = (n) => D.MINEI != null ? m(D.MINEI, n) : null, mw = ['Dep_02', 'Crew_Path_04', 'Crew_Path_03', 'Crew_Path_02', 'Crew_Path_01'].map(mn);
    if (mw.every(Boolean)) {
      const M = [167, 17.5], lead = loopPts.slice(0, 4);
      const out = [[PX - 10, 38], [PX - 28, 46], [PX - 42, 58], [PX - 56, 74], [PX - 75, 90], [PX - 100, 96], [400, 96], [300, 96], [236, 96], [222, 90], [217, 75], [217, 50], [212, 40], [200, 36.2], [180, 36], [163, 36], [156.5, 33.3], [153.75, 26.75], [156.5, 20.2], [163, 17.5], M];
      const ret = [M, [185, 17], [200, 15.4], [215, 15.5], [232, 20], [240, 32], [241, 60], [244, 82], [256, 93], [275, 96.3], [300, 96], [400, 96], [PX - 140, 96], [PX - 122, 93], [PX - 95, 78], [PX - 65, 52], [PX - 40, 34], [PX - 22, 28.2], [PX - 12, 26.6], V];
      Lo.M = M; Lo.mineWalk = mw; Lo.mineH = mkPath([...back, ...lead, ...out]); Lo.ret = mkPath(ret);
      Lo.mineTrail = [[mkPath([lead[3], ...out]), true, false], [mkPath(ret.slice(0, 11)), false, true], [mkPath(ret.slice(11, 19)), true, true]];   // drawn once each: the shared z 96 stretch and the loop tail only once
      Lo.prof = { mineH: prof(Lo.mineH, VHAUL), ret: prof(Lo.ret, VHAUL) };
    }
    return Lo;
  }

  // ---- stand-in van (primitives). Local frame: forward +z, right side (door) = −x, so heading +x world puts the door toward the camera (+z).
  function mkVan() {
    const g = new THREE.Group(); g.name = 'CrewVan_StandIn';
    const body = new THREE.MeshStandardMaterial({ name: 'Van_StandIn_Body', color: 0xd9dde3, roughness: .55, metalness: .1 });
    const dark = new THREE.MeshStandardMaterial({ name: 'Van_StandIn_Dark', color: 0x2b3038, roughness: .7 });
    const glass = new THREE.MeshStandardMaterial({ name: 'Van_StandIn_Glass', color: 0x1d2a36, roughness: .2, metalness: .3 });
    const cyan = new THREE.MeshStandardMaterial({ name: 'Van_StandIn_Stripe', color: 0x3ad0ff, emissive: 0x3ad0ff, emissiveIntensity: .6 });
    const box = (w, h, d, mat, x, y, z, n) => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); o.position.set(x, y, z); o.name = n || ''; o.castShadow = true; o.receiveShadow = true; g.add(o); return o; };
    box(2.2, 1.7, 5.0, body, 0, 1.45, 0, 'Van_Body');
    box(2.24, .35, 5.04, dark, 0, .55, 0, 'Van_Skirt');
    box(2.0, .9, .06, glass, 0, 1.75, 2.52, 'Van_Windshield');
    box(.06, .6, 1.1, glass, 1.11, 1.85, 1.8, 'Van_Window_L'); box(.06, .6, 1.1, glass, -1.11, 1.85, 1.8, 'Van_Window_R');
    box(2.26, .12, 5.06, cyan, 0, 1.05, 0, 'Van_Stripe');
    box(.04, 1.45, 1.4, dark, -1.105, 1.3, .35, 'Van_DoorGap');   // the opening behind the sliding door
    const wg = new THREE.CylinderGeometry(.4, .4, .3, 16); wg.rotateZ(Math.PI / 2);
    for (const [x, z] of [[1, 1.65], [-1, 1.65], [1, -1.65], [-1, -1.65]]) { const w = new THREE.Mesh(wg, dark); w.position.set(x, .4, z); w.castShadow = true; w.name = 'Van_Wheel'; g.add(w); }
    const door = new THREE.Mesh(new THREE.BoxGeometry(.06, 1.42, 1.38), body); door.name = 'Van_SlideDoor'; door.castShadow = true; g.add(door);
    const ds = new THREE.Mesh(new THREE.BoxGeometry(.065, .12, 1.38), cyan); ds.position.set(0, -.4, 0); door.add(ds);
    st.door = door; setDoor(0); g.visible = false; D.scene.add(g); return g;
  }
  function setDoor(u) {   // 0 closed (flush over the opening) → 1 open (stepped out 0.1 m and slid back 1.45 m along the side)
    u = Math.max(0, Math.min(1, u)); const e = u * u * (3 - 2 * u), out = Math.min(1, e * 4);
    st.door.position.set(-1.13 - .1 * out, 1.3, .35 - 1.45 * Math.max(0, (e - .1) / .9));
  }
  const doorW = (x, z, yaw, back = 0, side = 1.75) => {   // world point beside the door (side m out from the van's centre line), `back` m toward the rear
    const lx = -side, lz = .35 - back; return [x + lx * Math.cos(yaw) + lz * Math.sin(yaw), z - lx * Math.sin(yaw) + lz * Math.cos(yaw)]; };

  // ---- crew (clones of the crew rig the base already uses, so the same male suit; skinned clone rebinds bones by name)
  function cloneRig(src) {
    const c = src.clone(true), by = {}; c.traverse(o => { if (o.isBone || o.type === 'Bone') by[o.name] = o; });
    c.traverse(o => { if (!o.isSkinnedMesh) return; const sk = o.skeleton; o.bind(new THREE.Skeleton(sk.bones.map(b => by[b.name] || b), sk.boneInverses.map(m => m.clone())), o.bindMatrix.clone());
      o.material = [].concat(o.material).map(m => { const n = m.clone(); n.transparent = false; n.opacity = 1; n.depthWrite = true; return n; }); if (o.material.length === 1) o.material = o.material[0];
      o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; o.visible = true; });
    c.position.set(0, 0, 0); c.rotation.set(0, 0, 0); c.visible = true;
    c.traverse(o => { if (/_Root$/.test(o.name) && Math.min(o.scale.x, o.scale.y, o.scale.z) < .01) o.scale.set(1, 1, 1); });
    return c;
  }
  function person(i) {
    if (st.people[i]) return st.people[i];
    const src = D.crewTemplate(), walk = D.walkClip(), idle = D.idleClip(); if (!src || !walk) return null;
    const g = new THREE.Group(); g.name = 'CrewVan_Rider_' + i; const rig = cloneRig(src); g.add(rig); g.visible = false; D.scene.add(g);
    const mx = new THREE.AnimationMixer(rig), acts = {};
    for (const [k, c] of [['walk', walk], ['idle', idle]]) if (c) { const a = mx.clipAction(c); a.play(); a.paused = true; a.setEffectiveWeight(0); acts[k] = a; }
    return (st.people[i] = { g, rig, mx, acts });
  }
  function pose(p, x, z, yaw, mode, tm) {
    p.g.visible = true; p.g.position.set(x, groundY(x, z), z); p.g.rotation.set(0, yaw, 0);
    for (const k in p.acts) p.acts[k].setEffectiveWeight(0);
    const a = p.acts[mode] || p.acts.walk; if (a) { const d = a.getClip().duration; a.setEffectiveWeight(1); a.time = ((tm % d) + d) % d; p.mx.update(0); }
  }

  // ---- trail ribbon (same build as Art's truck trails; material shared with Truck_Trails_Art)
  function ribbon(path, fadeIn, fadeOut) {
    const { P, s, L } = path, n = P.length, C = TRAIL_U.length, pos = [], uv = [], col = [], nor = [], idx = [];
    const K = 4, ys = []; for (let i = 0; i < n; i += K) ys.push(groundY(P[i].x, P[i].z));   // centre-line ground height every 2 m (one raycast per sample), lerped per row
    const yRow = (i) => { const k = i / K, a = Math.floor(k), b = Math.min(ys.length - 1, a + 1); return ys[a] + (ys[b] - ys[a]) * (k - a); };
    for (let i = 0; i < n; i++) {
      const a = P[Math.max(0, i - 1)], b = P[Math.min(n - 1, i + 1)], tx = b.x - a.x, tz = b.z - a.z, tl = Math.hypot(tx, tz) || 1, nx = -tz / tl, nz = tx / tl;
      const al = TRAIL_A * Math.min(1, fadeIn ? s[i] / FADE_M : 1, fadeOut ? (L - s[i]) / FADE_M : 1);
      for (let j = 0; j < C; j++) { const o = (TRAIL_U[j] - .5) * TRAIL_W, x = P[i].x + nx * o, z = P[i].z + nz * o;
        pos.push(x, yRow(i) + .02, z); uv.push(TRAIL_U[j], s[i] * TRAIL_V); col.push(TRAIL_R[j], TRAIL_R[j], TRAIL_R[j], al); nor.push(0, 1, 0); }
      if (i) for (let j = 0; j < C - 1; j++) { const p0 = (i - 1) * C + j, p1 = p0 + 1, q0 = i * C + j, q1 = q0 + 1; idx.push(p0, p1, q0, p1, q1, q0); /* counter-clockwise from above: faces +y */ }
    }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setAttribute('color', new THREE.Float32BufferAttribute(col, 4)); g.setIndex(idx); g.computeBoundingSphere();
    return g;
  }
  function buildTrail(Lo) {
    const mat = D.trailMaterial(); if (!mat) return false;
    const geo = (() => { const a = ribbon(Lo.main, false, true), b = ribbon(Lo.loop, true, false); return D.mergeGeometries ? D.mergeGeometries([a, b]) : a; })();
    const m = new THREE.Mesh(geo, mat); m.name = 'CrewVan_Trail'; m.renderOrder = 1; m.castShadow = false; m.receiveShadow = true;
    D.scene.add(m); st.trail = m; return true;
  }
  function buildMineTrail(Lo) {   // its own frame after the pad/Shipyard/Habitat trail (terrain rays cost more); waits for the terrain GLBs
    const mat = D.trailMaterial(); if (!mat || !Lo.mineTrail || (D.terrainRoots && !D.terrainRoots())) return false;
    if (!st.warm) st.warm = Lo.mineTrail.flatMap(([p]) => p.P.filter((_, i) => i % 4 === 0)).filter(v => v.x > TERR[0] && v.x < TERR[1] && v.z > TERR[2] && v.z < TERR[3]);
    for (let n = 0; st.warm.length && n < 8; n++) { const v = st.warm.pop(); groundY(v.x, v.z); }   // terrain rays (~1.5 ms each) spread 8 per frame; the ribbon then reads the cache
    if (st.warm.length) return false;
    const gs = Lo.mineTrail.map(([p, a, b]) => ribbon(p, a, b)), geo = D.mergeGeometries ? D.mergeGeometries(gs) : gs[0];
    const m = new THREE.Mesh(geo, mat); m.name = 'CrewVan_Trail_Mine'; m.renderOrder = 1; m.castShadow = false; m.receiveShadow = true;
    D.scene.add(m); st.trail2 = m; return true;
  }

  // ---- schedule (pure in the trip start T and the riders)
  function schedule(trip, Lo) {
    const yard = !!D.yardBuilt(), roles = trip.roles.slice(0, MAXP), dst = (k) => roles.map((r, i) => DEST(r, yard) === k && (k !== 'mine' || Lo.mineH) ? i : -1).filter(i => i >= 0);
    const mine = dst('mine'), ship = dst('ship'), hab = roles.map((r, i) => mine.includes(i) || ship.includes(i) ? -1 : i).filter(i => i >= 0);   // no Mine road (markers missing): miners ride to the Habitat
    const tIn = driveSec(Lo.inPath.L), V = Lo.V, Vy = along(Lo.main, 0)[2];
    const L0 = D.ladder(), rid = [];
    let tOpen = tIn;
    for (let i = 0; i < roles.length; i++) {
      const q = doorW(V[0], V[1], Vy, .85 * i + .1, 1.55);   // queue in a line along the van's side toward its tail (was fanning out toward the camera, under the TAKEOFF & LANDING label)
      // After deboard (ladder foot / L10 cab approach = D.ladder()): walk a visible path around
      // the ship, tower, crane, break-room and crate bay (west apron), then around the van's nose
      // to the sliding door. No teleport; t0 is a short beat after deboard_done (cvLanded).
      const east = D.PX + 26;   // x 666: east of the pad deck (665), crane jib (660) and break-room (655)
      // North out of the L10 cab doors / ladder foot (do not step east into the elevator at
      // x 651.44), easing 1.4 m east so the path clears the hull AABB, then around the crane
      // and break-room to the van nose.
      const pl = poly([[L0[0], L0[1]], [L0[0] + 1.4, -3.8], [east, 2], [east, 24], [D.PX + 2, 28.3], q]);
      const t0 = 0.25 + i * STAGGER; rid.push({ role: roles[i], dest: mine.includes(i) ? 'mine' : ship.includes(i) ? 'ship' : 'hab', walk: pl, t0, tArr: t0 + pl.L / WALK_V, q });
    }
    tOpen = Math.max(tIn, rid.length ? rid[0].tArr - DOOR_SEC : 0);
    let tPrev = tOpen + DOOR_SEC - STAGGER;
    const inside = doorW(V[0], V[1], Vy, 0, .3), dpt = doorW(V[0], V[1], Vy, 0, 1.5);
    for (const r of rid) { const pl = poly([r.q, dpt, inside]); r.tIn0 = Math.max(r.tArr, tPrev + STAGGER); r.inPl = pl; r.tGone = r.tIn0 + pl.L / WALK_V; tPrev = r.tIn0; }
    const tClose = (rid.length ? Math.max(...rid.map(r => r.tGone)) : tOpen + DOOR_SEC) + .3, tGo = tClose + DOOR_SEC;
    const legs = []; let t = tGo, s0 = 0;
    const drop = (sStop, ids, walkPts, key, P = 'main') => {
      if (P === 'main') { const L = sStop - s0; legs.push({ k: 'drive', P, t0: t, t1: t + driveSec(L), s0, s1: sStop }); t += driveSec(L); s0 = sStop; }
      const [x, z, yaw] = along(Lo[P], sStop), ins = doorW(x, z, yaw, 0, .3), dp = doorW(x, z, yaw, 0, 1.5), dO = t; let tq = t + DOOR_SEC;
      const around = key === 'mine' ? [doorW(x, z, yaw, 3.6, 1.6), doorW(x, z, yaw, 3.6, -1.6)] : [doorW(x, z, yaw, -3.3, 2.0)];   // Mine: round the van's tail to the Mine side
      for (const i of ids) { const r = rid[i]; r.dropPl = poly([ins, dp, ...around, ...walkPts.filter(Boolean)]); r.tOut = tq; r.tDone = tq + r.dropPl.L / WALK_V; tq += STAGGER; }
      const tc = (ids.length ? tq - STAGGER + 2.4 / WALK_V : t + DOOR_SEC) + .2;
      const clear = Math.max(0, ...ids.map(i => rid[i].tOut + rid[i].dropPl.s[2 + around.length] / WALK_V + .5));   // pulls away once every rider is past its nose
      const t1 = Math.max(tc + DOOR_SEC, clear); legs.push({ k: 'stop', P, t0: dO, t1, s: sStop, open: dO, close: tc, key }); t = t1;
    };
    const run = (P) => { const T = Lo.prof[P].T; legs.push({ k: 'run', P, t0: t, t1: t + T }); t += T; };
    if (ship.length) drop(Lo.sS, ship, Lo.shipWalk, 'ship');
    if (hab.length || !mine.length) drop(Lo.main.L, hab, Lo.habWalk, 'hab');
    else { const L = Lo.main.L - s0; legs.push({ k: 'drive', P: 'main', t0: t, t1: t + driveSec(L), s0, s1: Lo.main.L }); t += driveSec(L); }   // miners only: past the Habitat stop without stopping
    if (mine.length) { run('mineH'); drop(Lo.mineH.L, mine, Lo.mineWalk, 'mine', 'mineH'); run('ret');
      legs.push({ k: 'drive', P: 'main', t0: t, t1: t + driveSec(Lo.main.L), s0: 0, s1: Lo.main.L }); t += driveSec(Lo.main.L); }   // back past the pad, home to the Habitat stop
    const tEnd = Math.max(t, ...rid.map(r => r.tDone || 0));
    return { roles, rid, tIn, tOpen, tClose, tGo, legs, tEnd };
  }
  function vanAt(trip, sch, Lo, u) {   // van pose + door at u seconds into the trip
    if (u < sch.tIn) { const d = driveDist(Lo.inPath.L, u), p = along(Lo.inPath, d); return { p, door: 0, ph: 'in' }; }
    if (u < sch.tGo) { const p = along(Lo.main, 0); const door = u < sch.tOpen ? 0 : u < sch.tClose ? (u - sch.tOpen) / DOOR_SEC : 1 - (u - sch.tClose) / DOOR_SEC; return { p, door, ph: 'pickup' }; }
    for (const l of sch.legs) {
      if (l.k === 'drive' && u < l.t1) return { p: along(Lo[l.P], l.s0 + driveDist(l.s1 - l.s0, u - l.t0)), door: 0, ph: l.P === 'main' ? 'drive' : 'drive_' + l.P };
      if (l.k === 'run' && u < l.t1) return { p: along(Lo[l.P], profDist(Lo[l.P], Lo.prof[l.P], u - l.t0)), door: 0, ph: 'drive_' + l.P };
      if (l.k === 'stop' && u < l.t1) { const door = u < l.close ? (u - l.open) / DOOR_SEC : 1 - (u - l.close) / DOOR_SEC; return { p: along(Lo[l.P], l.s), door, ph: 'drop_' + l.key }; }
    }
    return { p: along(Lo.main, Lo.main.L), door: 0, ph: 'parked' };
  }

  let Lo = null, schKey = '';
  function update(now) {
    try {
      if (!D.habBuilt()) { if (st.van) st.van.visible = false; if (st.trail) st.trail.visible = false; if (st.trail2) st.trail2.visible = false; for (const p of st.people) if (p) p.g.visible = false; return; }
      if (!Lo) { Lo = layout(); if (!Lo) return; }
      if (!st.van) st.van = mkVan();
      if (!st.trail && D.trailOn()) { const t0 = performance.now(); if (buildTrail(Lo)) { st.buildMs = Math.round(performance.now() - t0); st.defer = true; } } if (st.trail) st.trail.visible = true;
      if (st.defer) st.defer = false; else if (st.trail && !st.trail2 && Lo.mineTrail) { const t0 = performance.now(); if (buildMineTrail(Lo)) st.buildMs2 = Math.round(performance.now() - t0); } if (st.trail2) st.trail2.visible = true;
      st.ready = true;
      const trip = st.trip; let u = trip ? (now - trip.T) / 1000 : 1e9;
      const key = trip && trip.T + '|' + trip.roles.join() + '|' + !!D.yardBuilt(); if (trip && (!st.sch || schKey !== key)) { st.sch = schedule(trip, Lo); schKey = key; }
      const sch = st.sch;
      if (!trip || u < 0 || u > sch.tEnd + 1) {   // idle: parked at the Habitat stop
        const p = along(Lo.main, Lo.main.L); st.van.visible = true; st.van.position.set(p[0], groundY(p[0], p[1]), p[1]); st.van.rotation.set(0, p[2], 0); setDoor(0);
        for (const q of st.people) if (q) q.g.visible = false; st.ph = 'parked'; return;
      }
      const v = vanAt(trip, sch, Lo, u); st.ph = v.ph;
      st.van.visible = true; st.van.position.set(v.p[0], groundY(v.p[0], v.p[1]), v.p[1]); st.van.rotation.set(0, v.p[2], 0); setDoor(v.door);
      sch.rid.forEach((r, i) => {
        const p = person(i); if (!p) return;
        if (u < r.t0) { p.g.visible = false; return; }
        if (u < r.tArr) { const a = polyAt(r.walk, (u - r.t0) * WALK_V); pose(p, a[0], a[1], a[2], 'walk', (u - r.t0) * WALK_ANIM); return; }
        if (u < r.tIn0) { const yaw = v.p[2] - Math.PI / 2; pose(p, r.q[0], r.q[1], yaw + Math.PI, 'idle', u - r.tArr); return; }
        if (u < r.tGone) { const a = polyAt(r.inPl, (u - r.tIn0) * WALK_V); pose(p, a[0], a[1], a[2], 'walk', (u - r.tIn0) * WALK_ANIM); return; }
        if (!(r.tOut >= 0) || u < r.tOut) { p.g.visible = false; return; }   // inside the van (hidden)
        if (u < r.tDone) { const a = polyAt(r.dropPl, (u - r.tOut) * WALK_V); pose(p, a[0], a[1], a[2], 'walk', (u - r.tOut) * WALK_ANIM); return; }
        p.g.visible = false;   // through the Shipyard hall door / Habitat airlock
      });
      for (let i = sch.rid.length; i < st.people.length; i++) if (st.people[i]) st.people[i].g.visible = false;
    } catch (e) { if (!st.err) { st.err = String(e && e.message || e); console.warn('crew van', e); } }
  }
  function landed(T, roles) {   // a deboard just ended at T (game ms); roles = the picked crew who joined this landing
    roles = (roles || []).filter(Boolean); if (!roles.length) return;
    st.trip = { T, roles }; st.sch = null; try { localStorage.setItem(KEY, JSON.stringify(st.trip)); } catch (e) {}
  }
  return { st, update, landed, get layout() { return Lo; }, info: (now) => ({ ready: st.ready, ph: st.ph, trip: st.trip, u: st.trip ? (now - st.trip.T) / 1000 : null, tEnd: st.sch && st.sch.tEnd, legs: st.sch && st.sch.legs, rid: st.sch && st.sch.rid.map(r => ({ role: r.role, dest: r.dest, t0: r.t0, tArr: +r.tArr.toFixed(1), tGone: +r.tGone.toFixed(1), tOut: r.tOut && +r.tOut.toFixed(1), tDone: r.tDone && +r.tDone.toFixed(1) })), err: st.err, buildMs: st.buildMs, buildMs2: st.buildMs2 }) };
}
