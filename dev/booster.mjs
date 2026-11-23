// Super Heavy-style booster r2 + upright ST-10B cradle (gc/mechazilla).
// Art: art_next/booster/r2 (README.md). Booster origin = skirt-base centre.
// On the pad mount: pad-local (0, 9.8, −13), yaw −45°. On the ST-10B: parent
// the booster to Booster_Seat (0, 1.50, 0); the cradle origin is the ST-10B
// drive origin. Economy / Bay Lv30 unlock live on gc2/bay-upgrades — this
// module only places the models. Visibility: S.bay.own.booster or ?booster=1.

export const BOOSTER_URL = '../dev/models/booster_r2_bf5407b8.glb?v=bf5407b8';
export const BOOSTER_MD5 = 'bf5407b8791fb8e8100b2529704118a5';
export const CRADLE_URL = '../dev/models/booster_cradle_st10b_9015e139.glb?v=9015e139';
export const CRADLE_MD5 = '9015e13976e763bc12f263b20264c07a';
export const BOOSTER_PAD = { x: 0, y: 9.8, z: -13, yaw: -Math.PI / 4 };   // EXPORT / README: ring top, pins along carriage
// gc/cradle6: r6 split collar (art_next/booster_staging/r6/glb/README_glb_r6.md). CS_CollarHalf_A slides 0 -> 3.85 m along
// +COLLAR_AXIS in cradle-local glTF space, CS_CollarHalf_B the opposite way; CS_CollarRails stay fixed. Seat-in: collar opens,
// the booster drops vertically SEAT_DROP_M onto Booster_Seat, then the collar closes (only at yaw 0 mod 30, the r6 seat sweep).
export const COLLAR_AXIS = [0.965926, 0, -0.258819];
export const COLLAR_TRAVEL = 3.85;
export const COLLAR_SEC = 1.5;        // = lv10_tower DOOR_SEC (cab / arm slide doors); bay & entry doors are 1.0, shipyard DoorFrontB 3.0
export const SEAT_DROP_M = 4.5;       // r6 Y3 drop-in sweep: lift 4.5 -> 0 with the collar open
export const SEAT_DROP_SEC = 2.0;
const ease = (u) => (u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u));

function isShown(o, root) {
  for (let n = o; n; n = n.parent) { if (n.visible === false) return false; if (n === root) break; }
  return true;
}
function countMesh(root, skip) {
  let draws = 0, tris = 0;
  if (!root) return { draws, tris };
  root.traverse((o) => {
    if (skip && o.name === skip) return;
    if (!isShown(o, root) || !o.isMesh || !o.geometry) return;
    let top = o;
    if (skip) { for (let n = o; n && n !== root; n = n.parent) if (n.name === skip) return; }
    const g = o.geometry;
    const n = g.index ? g.index.count / 3 : (g.getAttribute('position')?.count || 0) / 3;
    tris += n * (o.isInstancedMesh ? o.count : 1);
    draws += Array.isArray(o.material) ? o.material.length : 1;
  });
  return { draws, tris: Math.round(tris) };
}

export function createBooster(THREE) {
  const T = {
    ready: false, failed: false, loading: 0,
    booster: null, cradle: null, seat: null,
    mode: 'hidden',          // hidden | st10b | pad
    carrying: false,
    collar: null,            // { a, b, a0, b0, k: 0 closed .. 1 open }
    seq: null,               // seat-in { t, phase: 'open' | 'drop' | 'close' | 'held' }
  };

  function bindBooster(gltf) {
    const root = gltf.scene;
    root.name = 'Booster';
    root.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
    T.booster = root;
    root.visible = false;
    return root;
  }
  function bindCradle(gltf, st10bRoot) {
    const root = gltf.scene;
    root.name = 'Booster_Cradle_ST10B';
    root.position.set(0, 0, 0);
    root.rotation.set(0, 0, 0);
    root.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
    T.cradle = root;
    const ca = root.getObjectByName('CS_CollarHalf_A'), cb = root.getObjectByName('CS_CollarHalf_B');
    T.collar = (ca && cb) ? { a: ca, b: cb, a0: ca.position.clone(), b0: cb.position.clone(), k: 0 } : null;
    T.seat = root.getObjectByName('Booster_Seat');
    if (!T.seat) {
      T.seat = new THREE.Object3D();
      T.seat.name = 'Booster_Seat';
      T.seat.position.set(0, 1.5, 0);
      root.add(T.seat);
    }
    if (st10bRoot) st10bRoot.add(root);
    root.visible = false;
    return root;
  }

  function load(loader, scene, st10bRoot, onOk, onErr) {
    if (T.ready) { if (onOk) onOk(info()); return; }
    if (T.loading) return;
    T.loading = 2;
    const fail = (e) => { T.failed = true; T.loading = 0; console.warn('booster/cradle load failed', e); if (onErr) onErr(e); };
    const done = () => {
      if (T.loading > 0) return;
      if (!T.booster || !T.cradle) return;
      T.ready = !T.failed;
      if (T.booster.parent == null) scene.add(T.booster);
      if (onOk) onOk(info());
    };
    loader.load(BOOSTER_URL, (g) => { try { bindBooster(g); } catch (e) { return fail(e); } T.loading--; done(); }, undefined, fail);
    loader.load(CRADLE_URL, (g) => { try { bindCradle(g, st10bRoot); } catch (e) { return fail(e); } T.loading--; done(); }, undefined, fail);
  }

  function attachCradle(st10bRoot) {
    if (!T.cradle || !st10bRoot) return;
    if (T.cradle.parent !== st10bRoot) st10bRoot.add(T.cradle);
    T.cradle.position.set(0, 0, 0);
    T.cradle.rotation.set(0, 0, 0);
  }

  function setCollar(k) {
    const C = T.collar;
    if (!C) return;
    C.k = Math.max(0, Math.min(1, k));
    const d = C.k * COLLAR_TRAVEL;
    C.a.position.set(C.a0.x + COLLAR_AXIS[0] * d, C.a0.y + COLLAR_AXIS[1] * d, C.a0.z + COLLAR_AXIS[2] * d);
    C.b.position.set(C.b0.x - COLLAR_AXIS[0] * d, C.b0.y - COLLAR_AXIS[1] * d, C.b0.z - COLLAR_AXIS[2] * d);
  }
  function seatYawDeg() {        // booster yaw about the seat's vertical, in the cradle frame
    if (!T.booster || T.booster.parent !== T.seat) return null;
    return T.booster.rotation.y * 180 / Math.PI;
  }
  function yawSeatable() {       // r6 Y3: only yaw 0 mod 30 drops clean onto the seat ring
    const y = seatYawDeg();
    if (y == null) return false;
    const m = ((y % 30) + 30) % 30;
    return Math.min(m, 30 - m) < 0.5;
  }
  function endSeq(closed) {
    T.seq = null;
    if (T.booster && T.booster.parent === T.seat) T.booster.position.y = 0;
    setCollar(closed ? 0 : 1);
  }
  // Advance the seat-in (game seconds). Collar opens (COLLAR_SEC), booster drops SEAT_DROP_M (SEAT_DROP_SEC), collar closes
  // (COLLAR_SEC) once seated at yaw 0 mod 30; any other yaw holds the collar open ('held').
  function tick(dt) {
    const q = T.seq;
    if (!q || !T.booster) return;
    q.t += Math.max(0, +dt || 0);
    if (q.phase === 'open') {
      setCollar(ease(q.t / COLLAR_SEC));
      T.booster.position.y = SEAT_DROP_M;
      if (q.t >= COLLAR_SEC) { q.phase = 'drop'; q.t -= COLLAR_SEC; }
    }
    if (q.phase === 'drop') {
      setCollar(1);
      T.booster.position.y = SEAT_DROP_M * (1 - ease(q.t / SEAT_DROP_SEC));
      if (q.t >= SEAT_DROP_SEC) { T.booster.position.y = 0; q.t -= SEAT_DROP_SEC; q.phase = yawSeatable() ? 'close' : 'held'; }
    }
    if (q.phase === 'close') {
      setCollar(1 - ease(q.t / COLLAR_SEC));
      if (q.t >= COLLAR_SEC) endSeq(true);
    } else if (q.phase === 'held') {
      setCollar(1);
      if (yawSeatable()) { q.phase = 'close'; q.t = 0; }
    }
  }
  // QA / stills: run the seat-in from t (s since start), or pose a fixed collar k with the booster lift y.
  function seatInAt(t) { if (!T.booster || T.booster.parent !== T.seat) return false; T.seq = { t: 0, phase: 'open' }; setCollar(0); tick(t); return true; }
  function poseCollar(k, lift) {
    if (T.booster && T.booster.parent === T.seat) T.booster.position.y = Math.max(0, +lift || 0);
    T.seq = null; setCollar(k);
  }

  function placeOnCradle(opts) {
    if (!T.booster || !T.seat) return false;
    const from = T.mode;
    T.seat.updateWorldMatrix(true, false);
    if (T.booster.parent !== T.seat) T.seat.attach(T.booster);
    T.booster.position.set(0, 0, 0);
    T.booster.rotation.set(0, 0, 0);
    // Seated = collar closed. Only a live return from the pad (this session) plays the seat-in; a load / reload derives
    // "seated, closed" from the saved staging state (S.bay.own.booster, S.cg.sh) — no collar save field.
    if (opts && opts.animate && from === 'pad' && T.collar) { T.seq = { t: 0, phase: 'open' }; setCollar(0); T.booster.position.y = SEAT_DROP_M; }
    else endSeq(true);
    T.booster.visible = true;
    if (T.cradle) T.cradle.visible = true;
    T.mode = 'st10b';
    T.carrying = true;
    return true;
  }

  function placeOnPad(padRoot) {
    if (!T.booster || !padRoot) return false;
    T.seq = null; setCollar(0);
    if (T.booster.parent !== padRoot) padRoot.add(T.booster);
    T.booster.position.set(BOOSTER_PAD.x, BOOSTER_PAD.y, BOOSTER_PAD.z);
    T.booster.rotation.set(0, BOOSTER_PAD.yaw, 0);
    T.booster.visible = true;
    if (T.cradle) T.cradle.visible = false;
    T.mode = 'pad';
    T.carrying = false;
    return true;
  }

  // Stacked catch / TowerCrewBoard_Stack: parent to Mount_Turntable so the
  // booster turns with the +135° boarding yaw. Local yaw stays -45°; world yaw
  // is -45° + turntable (EXPORT_r2t2.md). Ring sits 0.8 m above the turntable (y 9).
  function placeOnTurntable(tt) {
    if (!T.booster || !tt) return false;
    T.seq = null; setCollar(0);
    if (T.booster.parent !== tt) tt.add(T.booster);
    T.booster.position.set(0, BOOSTER_PAD.y - 9, 0);
    T.booster.rotation.set(0, BOOSTER_PAD.yaw, 0);
    T.booster.visible = true;
    if (T.cradle) T.cradle.visible = false;
    T.mode = 'pad';
    T.carrying = false;
    return true;
  }

  function hide() {
    T.seq = null; setCollar(0);
    if (T.booster) T.booster.visible = false;
    if (T.cradle) T.cradle.visible = false;
    T.mode = 'hidden';
    T.carrying = false;
  }

  // Default park: upright on the ST-10B when the booster is owned / QA-forced.
  // Pad-mount placement is opt-in (placeOnPad) — the live ship already sits at
  // Ship_Center (0, —, −13) and would intersect the 9.8 m ring pose.
  function sync(opts) {
    const show = !!(opts && opts.show);
    const st10b = opts && opts.st10b;
    if (st10b) attachCradle(st10b);
    if (!show) { hide(); return T.mode; }
    if (opts.mode === 'pad' && opts.turntable) return placeOnTurntable(opts.turntable) ? 'pad' : T.mode;
    if (opts.mode === 'pad' && opts.pad) return placeOnPad(opts.pad) ? 'pad' : T.mode;
    return placeOnCradle({ animate: !!opts.animate }) ? 'st10b' : T.mode;
  }

  function info() {
    const b = countMesh(T.booster);
    const c = countMesh(T.cradle, 'Booster');
    return {
      ready: T.ready, failed: T.failed, url: BOOSTER_URL, cradleUrl: CRADLE_URL,
      md5: BOOSTER_MD5, cradleMd5: CRADLE_MD5,
      mode: T.mode, carrying: T.carrying,
      visible: !!(T.booster && T.booster.visible),
      booster: b, cradle: c,
      draws: b.draws + c.draws, tris: b.tris + c.tris,
      seat: !!T.seat,
      collar: T.collar ? {
        k: +T.collar.k.toFixed(4), closed: T.collar.k === 0, phase: T.seq ? T.seq.phase : 'idle',
        yaw: seatYawDeg(), yawOk: yawSeatable(), lift: T.booster && T.booster.parent === T.seat ? +T.booster.position.y.toFixed(3) : null,
      } : null,
    };
  }

  return { T, load, attachCradle, placeOnCradle, placeOnPad, placeOnTurntable, hide, sync, info, tick, seatInAt, poseCollar, setCollar,
    consts: { BOOSTER_URL, BOOSTER_MD5, CRADLE_URL, CRADLE_MD5, BOOSTER_PAD, COLLAR_AXIS, COLLAR_TRAVEL, COLLAR_SEC, SEAT_DROP_M, SEAT_DROP_SEC } };
}
