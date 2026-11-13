// Control Tower at Launch Pad Lv20 (Art control_tower_game, md5 2ab839e0).
// Parent to LaunchPad_Art at pad-local glTF metres (23.5, 0, -18.0) — east of the deck,
// same frame as the tanks, crane, ship markers, and the Lv10 launch tower (which is
// parented to padArt at local origin). World would be (PX + 23.5, 0, -18).
// Visible only when the pad is Lv20 (bought, or loaded / ?padlv=20).
// Loops: Radar_Spin, Beacon_Blink. Airlock door clips are never played; the four
// leaves stay at their rest (shut) pose. No crew airlock walk-in.

export const CT_URL = '../dev/models/control_tower_game_2ab839e0.glb?v=2ab839e0';
export const CT_LOCAL = [23.5, 0, -18.0];
export const LOOP_CLIPS = ['Radar_Spin', 'Beacon_Blink'];
export const DOOR_LEAVES = [
  'Airlock_Door_Outer_S', 'Airlock_Door_Outer_N',
  'Airlock_Door_Inner_S', 'Airlock_Door_Inner_N',
];

export function createControlTower(THREE) {
  const T = { root: null, mixer: null, ready: false, failed: false, loading: false, active: false, actions: {}, doors: {} };

  function load(loader, pad, onOk, onErr) {
    if (T.ready || T.failed || T.loading || !pad || !loader) return;
    T.loading = true;
    loader.load(CT_URL, (g) => {
      const o = g.scene;
      o.name = 'ControlTower';
      o.position.set(CT_LOCAL[0], CT_LOCAL[1], CT_LOCAL[2]);
      o.rotation.set(0, 0, 0);
      o.scale.set(1, 1, 1);
      o.traverse((m) => {
        if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; m.frustumCulled = false; }
      });
      pad.add(o);
      T.root = o;
      T.mixer = new THREE.AnimationMixer(o);
      for (const c of (g.animations || [])) {
        if (!LOOP_CLIPS.includes(c.name)) continue;   // never play Airlock_* Open/Close
        const a = T.mixer.clipAction(c);
        a.setLoop(THREE.LoopRepeat, Infinity);
        a.clampWhenFinished = false;
        a.play();
        T.actions[c.name] = a;
      }
      for (const n of DOOR_LEAVES) {
        const d = o.getObjectByName(n);
        if (d) T.doors[n] = { pos: d.position.clone(), quat: d.quaternion.clone() };
      }
      T.ready = true;
      T.loading = false;
      o.visible = !!T.active;
      o.updateMatrixWorld(true);
      if (onOk) onOk(info());
    }, undefined, (e) => {
      T.failed = true;
      T.loading = false;
      console.warn('control tower failed to load', e);
      if (onErr) onErr(e);
    });
  }

  function setActive(on) {
    T.active = !!on;
    if (T.root) T.root.visible = T.active;
  }

  function holdDoors() {
    if (!T.root) return;
    for (const n of DOOR_LEAVES) {
      const d = T.root.getObjectByName(n), rest = T.doors[n];
      if (d && rest) { d.position.copy(rest.pos); d.quaternion.copy(rest.quat); }
    }
  }

  function update(dt) {
    if (!T.ready || !T.active || !T.mixer) return;
    T.mixer.update(dt);
    holdDoors();
  }

  function sync(lvOn) {
    setActive(!!lvOn && T.ready);
  }

  function info() {
    let box = null;
    if (T.root) {
      T.root.updateWorldMatrix(true, true);
      const b = new THREE.Box3().setFromObject(T.root);
      box = { min: b.min.toArray(), max: b.max.toArray() };
    }
    return {
      ready: T.ready, failed: T.failed, loading: !!T.loading, active: T.active,
      visible: !!(T.root && T.root.visible),
      url: CT_URL, local: CT_LOCAL.slice(),
      clips: Object.keys(T.actions),
      doors: Object.keys(T.doors),
      box,
    };
  }

  return { T, load, setActive, update, holdDoors, sync, info, CT_URL, CT_LOCAL };
}
