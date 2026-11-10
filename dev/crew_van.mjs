// Crew van (Jacob 11/10 9:07: "we need the van pickup and drop off for the crew when they land.. that van drive path also needs a trail").
// After a landing's deboarding ends (hook: the deboard → pad step in main.js), a crew van drives to the pad, the crew who landed this trip
// (the picked crew who joined the base in crewLand) walk to its side door and get in, and it drops them off: Engineers at the Shipyard
// (roles.json "Builds new ships at the Shipyard"; they walk the Shipyard's authored Crew_Path_01..05 to Hall_Door_Front), everyone else at the
// Habitat (their beds; authored Crew_Path_01..03 through the airlock). The starting crew keep their approved paths (deboard walk home, Mine taxi truck).
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
const DEST = (role, yard) => role === 'eng' && yard ? 'ship' : 'hab';   // roles.json: engineer "Builds new ships at the Shipyard" (once it is built); others live in the Habitat

export function createCrewVan(THREE, D) {
  const st = { ready: false, trip: null, sch: null, van: null, door: null, people: [], trail: null, yCache: new Map(), boxes: null, err: null, buildMs: 0 };
  try { const j = JSON.parse(localStorage.getItem(KEY) || 'null'); if (j && j.T > 0 && Array.isArray(j.roles)) st.trip = j; } catch (e) {}
  const ray = new THREE.Raycaster(), V3 = THREE.Vector3;

  // ---- ground height (station aprons sit a little above y 0): raycast once per 0.5 m cell
  function groundY(x, z) {
    const k = Math.round(x * 2) + ',' + Math.round(z * 2); if (st.yCache.has(k)) return st.yCache.get(k);
    let y = 0; if (!st.boxes) { st.boxes = D.groundRoots().filter(Boolean).map(r => [r, new THREE.Box3().setFromObject(r)]); }
    const roots = st.boxes.filter(([, b]) => x >= b.min.x && x <= b.max.x && z >= b.min.z && z <= b.max.z).map(([r]) => r);   // only the station(s) under this point
    if (roots.length) { ray.set(new V3(x, 3, z), new V3(0, -1, 0)); ray.far = 4;
      for (const h of ray.intersectObjects(roots, true)) { if (h.object.visible && h.point.y < 1.2 && h.point.y > y) y = h.point.y; } }
    st.yCache.set(k, y); return y;
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
  const poly = (pts) => { const s = [0]; for (let i = 1; i < pts.length; i++) s.push(s[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])); return { pts, s, L: s[s.length - 1] }; };
  const polyAt = (pl, d) => { const { pts, s, L } = pl; d = Math.max(0, Math.min(L, d)); let i = 1; while (i < s.length - 1 && s[i] < d) i++;
    const a = pts[i - 1], b = pts[i] || a, u = (d - s[i - 1]) / ((s[i] - s[i - 1]) || 1); return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, Math.atan2(b[0] - a[0], b[1] - a[1])]; };

  // ---- layout from the stations' authored markers (Launch Pad / Shipyard / Habitat)
  function layout() {
    const m = D.marker; const sy = (n) => m(D.SHIPI, n), hb = (n) => m(D.HABI, n);
    const yRoad = sy('Road_Entry'), y1 = sy('Crew_Path_01'), h1 = hb('Crew_Path_01');
    if (!yRoad || !y1 || !h1) return null;
    const PX = D.PX, V = [PX - 4, 26.6], S = [y1[0] - 13.6, y1[1] + 5.2], H = [h1[0] - 8, h1[1] + 3.9];   // stops: in front of the Launch Pad (east of the flatbed U-turn), Shipyard apron front, Habitat door
    const main = mkPath([V, [PX + 15, 27], [PX + 35, 27.6], [PX + 60, 26], [PX + 90, 22], yRoad, [yRoad[0] + 26, yRoad[1] + 12], [S[0] - 10, S[1] - 2], S, [S[0] + 15, S[1] + 1], [S[0] + 50, S[1]], [H[0] - 47, H[1] + 13.5], [H[0] - 17, H[1] + 2.5], H]);
    const sS = main.s[main.P.reduce((bi, p, i) => (Math.hypot(p.x - S[0], p.z - S[1]) < Math.hypot(main.P[bi].x - S[0], main.P[bi].z - S[1]) ? i : bi), 0)];
    const J = [PX + 90, 22];   // the drive-in leaves the main route here and loops round in front of the pad so the van stops heading east (door toward the camera)
    const loopPts = [J, [PX + 62, 33], [PX + 38, 35.5], [PX + 10, 35.5], [PX - 14, 34], [PX - 22, 29.5], [PX - 15, 26.7], V];
    const back = []; for (let i = main.P.length - 1; i >= 0; i--) { const p = main.P[i]; if (p.x < J[0] + 3) break; if (i % 6 === 0) back.push([p.x, p.z]); }
    const inPath = mkPath([...back, ...loopPts]);
    const loop = mkPath(loopPts);
    return { V, S, H, main, sS, inPath, loop, shipWalk: ['Crew_Path_01', 'Crew_Path_02', 'Crew_Path_03', 'Crew_Path_04', 'Crew_Path_05'].map(sy),
      habWalk: ['Crew_Path_01', 'Crew_Path_02', 'Crew_Path_03'].map(hb) };
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

  // ---- schedule (pure in the trip start T and the riders)
  function schedule(trip, Lo) {
    const yard = !!D.yardBuilt(), roles = trip.roles.slice(0, MAXP), ship = roles.map((r, i) => DEST(r, yard) === 'ship' ? i : -1).filter(i => i >= 0), hab = roles.map((r, i) => DEST(r, yard) === 'hab' ? i : -1).filter(i => i >= 0);
    const tIn = driveSec(Lo.inPath.L), V = Lo.V, Vy = along(Lo.main, 0)[2];
    const L0 = D.ladder(), rid = [];
    let tOpen = tIn;
    for (let i = 0; i < roles.length; i++) {
      const q = doorW(V[0], V[1], Vy, .9 * i + .1, 1.75 + .25 * i);
      const pl = poly([[L0[0], L0[1] + 1.2], [D.PX + 3.2, -3.4], [D.PX + 22.5, 2], [D.PX + 22.5, 22], [D.PX + 1.5, 29.4], q]);   // pad crew path to the deck's east edge, past the crane, round the van's nose
      const t0 = 1 + i * STAGGER; rid.push({ role: roles[i], dest: DEST(roles[i], yard), walk: pl, t0, tArr: t0 + pl.L / WALK_V, q });
    }
    tOpen = Math.max(tIn, rid.length ? rid[0].tArr - DOOR_SEC : 0);
    let tPrev = tOpen + DOOR_SEC - STAGGER;
    const inside = doorW(V[0], V[1], Vy, 0, .3), dpt = doorW(V[0], V[1], Vy, 0, 1.5);
    for (const r of rid) { const pl = poly([r.q, dpt, inside]); r.tIn0 = Math.max(r.tArr, tPrev + STAGGER); r.inPl = pl; r.tGone = r.tIn0 + pl.L / WALK_V; tPrev = r.tIn0; }
    const tClose = (rid.length ? Math.max(...rid.map(r => r.tGone)) : tOpen + DOOR_SEC) + .3, tGo = tClose + DOOR_SEC;
    const legs = []; let t = tGo, s0 = 0;
    const drop = (sStop, ids, walkPts, key) => {
      const L = sStop - s0; legs.push({ k: 'drive', t0: t, t1: t + driveSec(L), s0, s1: sStop }); t += driveSec(L); s0 = sStop;
      const [x, z, yaw] = along(Lo.main, sStop), ins = doorW(x, z, yaw, 0, .3), dp = doorW(x, z, yaw, 0, 1.5), dO = t; let tq = t + DOOR_SEC;
      const around = key === 'hab' ? [doorW(x, z, yaw, -3.3, 2.0)] : [doorW(x, z, yaw, -3.3, 2.0)];
      for (const i of ids) { const r = rid[i]; r.dropPl = poly([ins, dp, ...around, ...walkPts.filter(Boolean)]); r.tOut = tq; r.tDone = tq + r.dropPl.L / WALK_V; tq += STAGGER; }
      const tc = (ids.length ? tq - STAGGER + 2.4 / WALK_V : t + DOOR_SEC) + .2;
      const clear = Math.max(0, ...ids.map(i => rid[i].tOut + rid[i].dropPl.s[2 + around.length] / WALK_V + .5));   // pulls away once every rider is past its nose
      const t1 = Math.max(tc + DOOR_SEC, clear); legs.push({ k: 'stop', t0: dO, t1, s: sStop, open: dO, close: tc, key }); t = t1;
    };
    if (ship.length) drop(Lo.sS, ship, Lo.shipWalk, 'ship');
    drop(Lo.main.L, hab, Lo.habWalk, 'hab');
    const tEnd = Math.max(t, ...rid.map(r => r.tDone || 0));
    return { roles, rid, tIn, tOpen, tClose, tGo, legs, tEnd };
  }
  function vanAt(trip, sch, Lo, u) {   // van pose + door at u seconds into the trip
    if (u < sch.tIn) { const d = driveDist(Lo.inPath.L, u), p = along(Lo.inPath, d); return { p, door: 0, ph: 'in' }; }
    if (u < sch.tGo) { const p = along(Lo.main, 0); const door = u < sch.tOpen ? 0 : u < sch.tClose ? (u - sch.tOpen) / DOOR_SEC : 1 - (u - sch.tClose) / DOOR_SEC; return { p, door, ph: 'pickup' }; }
    for (const l of sch.legs) {
      if (l.k === 'drive' && u < l.t1) return { p: along(Lo.main, l.s0 + driveDist(l.s1 - l.s0, u - l.t0)), door: 0, ph: 'drive' };
      if (l.k === 'stop' && u < l.t1) { const door = u < l.close ? (u - l.open) / DOOR_SEC : 1 - (u - l.close) / DOOR_SEC; return { p: along(Lo.main, l.s), door, ph: 'drop_' + l.key }; }
    }
    return { p: along(Lo.main, Lo.main.L), door: 0, ph: 'parked' };
  }

  let Lo = null, schKey = '';
  function update(now) {
    try {
      if (!D.habBuilt()) { if (st.van) st.van.visible = false; if (st.trail) st.trail.visible = false; for (const p of st.people) if (p) p.g.visible = false; return; }
      if (!Lo) { Lo = layout(); if (!Lo) return; }
      if (!st.van) st.van = mkVan();
      if (!st.trail && D.trailOn()) { const t0 = performance.now(); if (buildTrail(Lo)) st.buildMs = Math.round(performance.now() - t0); } if (st.trail) st.trail.visible = true;
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
  return { st, update, landed, get layout() { return Lo; }, info: (now) => ({ ready: st.ready, ph: st.ph, trip: st.trip, u: st.trip ? (now - st.trip.T) / 1000 : null, tEnd: st.sch && st.sch.tEnd, legs: st.sch && st.sch.legs, rid: st.sch && st.sch.rid.map(r => ({ role: r.role, dest: r.dest, t0: r.t0, tArr: +r.tArr.toFixed(1), tGone: +r.tGone.toFixed(1), tOut: r.tOut && +r.tOut.toFixed(1), tDone: r.tDone && +r.tDone.toFixed(1) })), err: st.err }) };
}
