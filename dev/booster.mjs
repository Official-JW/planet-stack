// Super Heavy-style booster r2 + upright ST-10B cradle (gc/mechazilla).
// Art: art_next/booster/r2 (README.md). Booster origin = skirt-base centre.
// On the pad mount: pad-local (0, 9.8, −13), yaw −45°. On the ST-10B: parent
// the booster to Booster_Seat (0, 1.50, 0); the cradle origin is the ST-10B
// drive origin. Economy / Bay Lv30 unlock live on gc2/bay-upgrades — this
// module only places the models. Visibility: S.bay.own.booster or ?booster=1.

export const BOOSTER_URL = '../dev/models/booster_r2_bf5407b8.glb?v=bf5407b8';
export const BOOSTER_MD5 = 'bf5407b8791fb8e8100b2529704118a5';
export const CRADLE_URL = '../dev/models/booster_cradle_st10b_538047ce.glb?v=538047ce';
export const CRADLE_MD5 = '538047ce1076d6c2e54df76f596c4eac';
export const BOOSTER_PAD = { x: 0, y: 9.8, z: -13, yaw: -Math.PI / 4 };   // EXPORT / README: ring top, pins along carriage

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

  function placeOnCradle() {
    if (!T.booster || !T.seat) return false;
    T.seat.updateWorldMatrix(true, false);
    if (T.booster.parent !== T.seat) T.seat.attach(T.booster);
    T.booster.position.set(0, 0, 0);
    T.booster.rotation.set(0, 0, 0);
    T.booster.visible = true;
    if (T.cradle) T.cradle.visible = true;
    T.mode = 'st10b';
    T.carrying = true;
    return true;
  }

  function placeOnPad(padRoot) {
    if (!T.booster || !padRoot) return false;
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
    return placeOnCradle() ? 'st10b' : T.mode;
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
    };
  }

  return { T, load, attachCradle, placeOnCradle, placeOnPad, placeOnTurntable, hide, sync, info, consts: { BOOSTER_URL, BOOSTER_MD5, CRADLE_URL, CRADLE_MD5, BOOSTER_PAD } };
}
