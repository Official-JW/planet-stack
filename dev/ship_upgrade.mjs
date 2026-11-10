// gc/ship-upgrade — specialist requirements + ST-10B transporter.
// Isolated module so pad/tower/crew-climb code can merge without colliding.
// Meshopt GLB: load with GLTFLoader.setMeshoptDecoder (the game loader already does).
// Look meshes up by the named parent (gltfpack adds unnamed dequantise children).
// Do not edit hull or Ship_Placeholder materials. Parent the ship with Object3D.attach
// (world-preserving). The 10:15 PM ship-bay stills (transporter_bay_2150, STILLS.md 10:12 PM)
// have no game GLB — gantries were blend-only study meshes — so the bay here is a
// stand-in apron at CFG.shipyardCrawlerStopX (700), z = Ship_Center z (−13).

export const SU_URL = '../qa3d-next/models/st10b_game_801941fd.glb?v=801941fd';

// Requirement to upgrade FROM display level N (L1 = shipLv 0) to N+1.
// weld / eng / mech. Specialists must be present on the Moon; they are not consumed.
export const SHIP_UPGRADE_REQ = {
  1: { weld: 2, eng: 1, mech: 2 },
  2: { weld: 3, eng: 2, mech: 3 },
  3: { weld: 4, eng: 2, mech: 3 },
  4: { weld: 5, eng: 3, mech: 4 },
  5: { weld: 6, eng: 3, mech: 4 },
  6: { weld: 7, eng: 4, mech: 5 },
  7: { weld: 8, eng: 4, mech: 5 },
  8: { weld: 9, eng: 5, mech: 6 },
  9: { weld: 10, eng: 5, mech: 6 },
  10: { weld: 10, eng: 6, mech: 7 },
};

export const SPEC_KEYS = [['weld', 'welder', 'welders'], ['eng', 'engineer', 'engineers'], ['mech', 'mechanic', 'mechanics']];

export const DRIVE_V = 5.0;       // m/s along the HB-1 crawler trail (z −13)
export const PICK_SEC = 2.5;
export const DROP_SEC = 2.5;
export const WORK_SEC_DEFAULT = 60;
export const BAY_X = 700;         // CFG.shipyardCrawlerStopX — park outside HB-1, never into the door
export const PATH_Z = -13;        // Ship_Center z; trail_ext_hb1 is a straight z −13 run

export function migrateShipUpgrade(sv) {
  if (!sv || typeof sv !== 'object' || Array.isArray(sv)) return sv;
  // 561a538-era and older saves have no specialist counters and no upgrade job.
  if (!sv.crewRoles || typeof sv.crewRoles !== 'object' || Array.isArray(sv.crewRoles)) sv.crewRoles = {};
  for (const [k] of SPEC_KEYS) if (!(sv.crewRoles[k] >= 0)) sv.crewRoles[k] = 0;
  if (!sv.upg || typeof sv.upg !== 'object' || Array.isArray(sv.upg)) sv.upg = { t0: 0 };
  if (!(sv.upg.t0 > 0)) sv.upg.t0 = 0;
  return sv;
}

export function shipUpgradeReq(displayLv) {
  const n = Math.max(1, Math.min(10, displayLv | 0));
  return SHIP_UPGRADE_REQ[n] || SHIP_UPGRADE_REQ[1];
}

function countOf(S, k) {
  const n = S && S.crewRoles && S.crewRoles[k];
  return n >= 0 ? (n | 0) : 0;
}

export function shipUpgradeShortfall(S, displayLv) {
  const req = shipUpgradeReq(displayLv);
  const out = {};
  for (const [k] of SPEC_KEYS) {
    const need = Math.max(0, (req[k] | 0) - countOf(S, k));
    if (need) out[k] = need;
  }
  return out;
}

export function shipUpgradeStaffed(S, displayLv) {
  return Object.keys(shipUpgradeShortfall(S, displayLv)).length === 0;
}

export function shipUpgradeShortfallText(S, displayLv) {
  const sf = shipUpgradeShortfall(S, displayLv);
  const parts = [];
  for (const [k, one, many] of SPEC_KEYS) {
    const n = sf[k];
    if (!n) continue;
    parts.push(n === 1 ? `1 more ${one}` : `${n} ${many}`);
  }
  if (!parts.length) return '';
  if (parts.length === 1) return 'Need ' + parts[0];
  if (parts.length === 2) return 'Need ' + parts[0] + ', ' + parts[1];
  return 'Need ' + parts.slice(0, -1).join(', ') + ', ' + parts[parts.length - 1];
}

export function shipUpgradeBusy(S) { return !!(S && S.upg && S.upg.t0 > 0); }

export function shipUpgradeWorkSec(QD) {
  const q = QD && QD.get && QD.get('upsec');
  if (q != null && q !== '' && isFinite(+q) && +q > 0) return Math.max(0.5, +q);
  return WORK_SEC_DEFAULT;
}

export function driveSecFor(dx) { return Math.max(0.4, Math.abs(dx) / DRIVE_V); }

function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
function smoother(u) { u = clamp(u, 0, 1); return u * u * u * (u * (u * 6 - 15) + 10); }

export function createShipUpgrade(THREE) {
  const T = {
    ready: false, failed: false, loading: false,
    root: null, seat: null, empty: null, loaded: null,
    bay: null, shipHome: null, carrying: false,
  };

  function setCradle(on) {
    if (T.loaded) T.loaded.visible = !!on;
    if (T.empty) T.empty.visible = !on;
  }

  function makeBay(scene, bayX, bayZ) {
    if (T.bay) return T.bay;
    const g = new THREE.Group();
    g.name = 'ShipBay_StandIn';
    const slabMat = new THREE.MeshStandardMaterial({ color: 0x9a958c, roughness: 0.92, metalness: 0 });
    const edgeMat = new THREE.MeshStandardMaterial({ color: 0x2fc4dc, roughness: 0.35, emissive: new THREE.Color(0x1a8aa0), emissiveIntensity: 0.6 });
    const postMat = new THREE.MeshStandardMaterial({ color: 0x4a5560, roughness: 0.45, metalness: 0.15 });
    const slab = new THREE.Mesh(new THREE.BoxGeometry(36, 0.16, 32), slabMat);
    slab.position.y = 0.08; slab.receiveShadow = true; slab.name = 'ShipBay_Slab';
    g.add(slab);
    const ring = new THREE.Mesh(new THREE.BoxGeometry(16, 0.04, 16), edgeMat);
    ring.position.y = 0.17; ring.receiveShadow = true; ring.name = 'ShipBay_Berth';
    g.add(ring);
    const hole = new THREE.Mesh(new THREE.BoxGeometry(14.5, 0.05, 14.5), slabMat);
    hole.position.y = 0.18; hole.receiveShadow = true;
    g.add(hole);
    for (const [x, z] of [[-16, -14], [16, -14], [-16, 14], [16, 14]]) {
      const p = new THREE.Mesh(new THREE.BoxGeometry(0.4, 2.2, 0.4), postMat);
      p.position.set(x, 1.1, z); p.castShadow = true;
      const cap = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.12, 0.5), edgeMat);
      cap.position.set(x, 2.22, z);
      g.add(p, cap);
    }
    g.position.set(bayX, 0, bayZ);
    scene.add(g);
    T.bay = g;
    return g;
  }

  function bind(gltf, scene, bayX, bayZ) {
    const root = gltf.scene;
    root.name = 'ST10B_Art';
    root.traverse((m) => {
      if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; }
    });
    T.root = root;
    T.seat = root.getObjectByName('Ship_Seat');
    T.empty = root.getObjectByName('Cradle_Empty');
    T.loaded = root.getObjectByName('Cradle_Loaded');
    if (!T.seat || !T.empty || !T.loaded) throw new Error('ST-10B nodes missing (Ship_Seat / cradles)');
    setCradle(false);
    scene.add(root);
    makeBay(scene, bayX, bayZ);
    T.ready = true;
    T.failed = false;
    return info();
  }

  function load(loader, scene, bayX, bayZ, onOk, onErr) {
    if (T.ready) { if (onOk) onOk(info()); return; }
    if (T.loading) return;
    T.loading = true;
    loader.load(SU_URL, (g) => {
      T.loading = false;
      try { const i = bind(g, scene, bayX, bayZ); if (onOk) onOk(i); }
      catch (e) { T.failed = true; console.warn('ST-10B bind failed', e); if (onErr) onErr(e); }
    }, undefined, (e) => {
      T.loading = false; T.failed = true;
      console.warn('ST-10B GLB failed to load', e); if (onErr) onErr(e);
    });
  }

  function info() {
    let draws = 0, tris = 0;
    if (T.root) T.root.traverse((o) => {
      if (!o.visible || !o.isMesh || !o.geometry) return;
      const g = o.geometry;
      const n = g.index ? g.index.count / 3 : (g.getAttribute('position')?.count || 0) / 3;
      tris += n;
      draws += Array.isArray(o.material) ? o.material.length : 1;
    });
    if (T.bay) T.bay.traverse((o) => {
      if (!o.visible || !o.isMesh || !o.geometry) return;
      const g = o.geometry;
      const n = g.index ? g.index.count / 3 : (g.getAttribute('position')?.count || 0) / 3;
      tris += n; draws += 1;
    });
    return { ready: T.ready, draws, tris: Math.round(tris), carrying: !!T.carrying, url: SU_URL };
  }

  function place(x, y, z) {
    if (!T.root) return;
    T.root.position.set(x, y, z);
    T.root.rotation.set(0, 0, 0);
    T.root.updateMatrixWorld(true);
  }

  function attachShip(ship) {
    if (!T.seat || !ship) return;
    if (ship.parent === T.seat) { T.carrying = true; return; }
    if (!T.shipHome) T.shipHome = { parent: ship.parent, x: ship.position.x, y: ship.position.y, z: ship.position.z };
    ship.updateWorldMatrix(true, false);
    T.seat.updateWorldMatrix(true, false);
    T.seat.attach(ship);            // world-preserving
    T.carrying = true;
  }

  function detachShip(ship, rest) {
    if (!ship) return;
    const home = T.shipHome && T.shipHome.parent;
    const dest = home || (rest && rest.parent) || ship.parent;
    if (dest && ship.parent !== dest) {
      dest.updateWorldMatrix(true, false);
      dest.attach(ship);
    }
    if (rest) ship.position.set(rest.x, rest.y, rest.z);
    ship.rotation.set(0, 0, 0);
    ship.updateMatrixWorld(true);
    T.carrying = false;
  }

  function schedule(padX, bayX, workSec) {
    const drive = driveSecFor(bayX - padX);
    const toPad = drive, pick = PICK_SEC, toBay = drive, work = workSec, back = drive, drop = DROP_SEC, home = drive;
    const t0 = 0;
    const tPick0 = t0 + toPad;
    const tToBay0 = tPick0 + pick;
    const tWork0 = tToBay0 + toBay;
    const tBack0 = tWork0 + work;
    const tDrop0 = tBack0 + back;
    const tHome0 = tDrop0 + drop;
    const tEnd = tHome0 + home;
    return { drive, toPad, pick, toBay, work, back, drop, home, tPick0, tToBay0, tWork0, tBack0, tDrop0, tHome0, tEnd };
  }

  function phaseAt(u, sch) {
    if (u < sch.tPick0) return { k: 'to_pad', s: 0, e: sch.tPick0, loaded: false, attach: false, drop: false };
    if (u < sch.tToBay0) return { k: 'pickup', s: sch.tPick0, e: sch.tToBay0, loaded: true, attach: true, drop: false };
    if (u < sch.tWork0) return { k: 'to_bay', s: sch.tToBay0, e: sch.tWork0, loaded: true, attach: true, drop: false };
    if (u < sch.tBack0) return { k: 'work', s: sch.tWork0, e: sch.tBack0, loaded: true, attach: true, drop: false };
    if (u < sch.tDrop0) return { k: 'to_pad_back', s: sch.tBack0, e: sch.tDrop0, loaded: true, attach: true, drop: false };
    if (u < sch.tHome0) return { k: 'drop', s: sch.tDrop0, e: sch.tHome0, loaded: false, attach: false, drop: true };
    if (u < sch.tEnd) return { k: 'to_bay_home', s: sch.tHome0, e: sch.tEnd, loaded: false, attach: false, drop: true };
    return { k: 'idle', s: sch.tEnd, e: sch.tEnd, loaded: false, attach: false, drop: true };
  }

  function xAlong(from, to, u) { return from + (to - from) * smoother(u); }

  // Pose from saved S.upg timestamps (offline-safe). env: { ship, shipY0, padX, padZ, bayX, rest }
  function poseAt(u, sch, env) {
    if (!T.ready) return null;
    const padX = env.padX, bayX = env.bayX, z = env.padZ, y0 = env.shipY0 != null ? env.shipY0 : 0;
    const ty = y0 - 0.45;            // Ship_Seat is (0, 0.45, 0)
    const ph = phaseAt(u, sch);
    let x = bayX, loaded = false;
    if (ph.k === 'to_pad') { x = xAlong(bayX, padX, sch.toPad > 0 ? (u - 0) / sch.toPad : 1); loaded = false; }
    else if (ph.k === 'pickup') { x = padX; loaded = true; }
    else if (ph.k === 'to_bay') { x = xAlong(padX, bayX, sch.toBay > 0 ? (u - sch.tToBay0) / sch.toBay : 1); loaded = true; }
    else if (ph.k === 'work') { x = bayX; loaded = true; }
    else if (ph.k === 'to_pad_back') { x = xAlong(bayX, padX, sch.back > 0 ? (u - sch.tBack0) / sch.back : 1); loaded = true; }
    else if (ph.k === 'drop') { x = padX; loaded = false; }
    else if (ph.k === 'to_bay_home') { x = xAlong(padX, bayX, sch.home > 0 ? (u - sch.tHome0) / sch.home : 1); loaded = false; }
    else { x = bayX; loaded = false; }
    place(x, ty, z);
    setCradle(loaded);
    if (env.ship) {
      if (ph.attach) attachShip(env.ship);
      else detachShip(env.ship, env.rest);
    }
    return { ph: ph.k, x, u, loaded, carrying: T.carrying };
  }

  function idle(env) {
    if (!T.ready) return;
    const y0 = env.shipY0 != null ? env.shipY0 : 0;
    place(env.bayX, y0 - 0.45, env.padZ);
    setCradle(false);
    if (env.ship && T.carrying) detachShip(env.ship, env.rest);
  }

  return {
    T, load, bind, info, setCradle, place, attachShip, detachShip,
    schedule, phaseAt, poseAt, idle, makeBay,
    timings: { DRIVE_V, PICK_SEC, DROP_SEC, WORK_SEC_DEFAULT, BAY_X, PATH_Z },
  };
}
