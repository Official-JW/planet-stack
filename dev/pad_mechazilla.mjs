// Mechazilla pad loader (gc/mechazilla). r2 try-2 final pad: crew elevator and
// arm live inside the chopstick tower (no separate CrewTower). Node names,
// clips, camera and legs retarget: art_next/pad_mechazilla/r2/glb/EXPORT_r2t2.md.
// Tanks: art_next/pad_mechazilla/r2/tanks/README_tanks.md (v b).

export const PAD_MZ_URL = '../dev/models/pad_mechazilla_r2t2_3cd3ade5.glb?v=3cd3ade5';
export const PAD_MZ_MD5 = '3cd3ade5c13720331b279d63129e9622';
export const PAD_MZ_STANDIN = false;
export const PAD_MZ_LEGS_URL = '../dev/models/pad_mechazilla_r2_legs_ff11108e.glb?v=ff11108e';
export const PAD_MZ_LEGS_MD5 = 'ff11108ec8cc25040848f55be8765b29';
export const PAD_TANKS_URL = '../dev/models/pad_tanks_lox_lch4_b_711c5574.glb?v=711c5574';
export const PAD_TANKS_MD5 = '711c5574c77b83aceb7edf0d3aeaa4bf';
export const PAD_MZ_CAM = { ct: { x: 8.75, y: 51.75, z: -13.0 }, frame_w: 109.5 };
export const PAD_TANKS_POS = {
  below: { x: -16.54, y: 0, z: -6.20 },
  lv20: { x: -41.69, y: 0, z: -6.20 },
};
export const PAD_MZ_NODES = [
  'Tower', 'Chopsticks', 'Carriage', 'Arm_L', 'Arm_R', 'Ship_Attach',
  'Mount', 'Mount_Turntable',
  'TowerElevator', 'TowerCrewArm', 'TowerCrewArm_S3', 'TowerCrewArm_S4',
  'TowerCrewArm_S5', 'TowerCrewArm_S6', 'TowerCrewArm_Door_L', 'TowerCrewArm_Door_R',
  'Crane', 'Cam_Target', 'Ship_Track', 'Crew_Mark_1', 'Crew_Mark_2',
];
export const PAD_MZ_CLIPS = [
  'Catch_Lift_Swing_SetDown',
  'TowerCrewBoard_Mount', 'TowerCrewBoard_Stack',
  'TowerCrewArm_Extend', 'TowerCrewArm_Retract',
  'TowerElevator_Down_Mount', 'TowerElevator_Down_Stack',
  'crane_lift', 'crane_swing', 'crane_lower',
  'crane_lift_bay', 'crane_swing_hold', 'crane_lower_hold',
];
export const MZ_CATCH_SEC = 43;
export const MZ_BOARD_MOUNT_SEC = 52;
export const MZ_BOARD_STACK_SEC = 58;
export const MZ_ELEV_DOWN_MOUNT_SEC = 12;
export const MZ_ELEV_DOWN_STACK_SEC = 18;
export const MZ_LEGS_FOLD_AT = 7.8;
export const MZ_LEGS_DEPLOY_AT = 28.0;
export const MZ_HATCH_OPEN_MOUNT = [31.0, 32.2];
export const MZ_HATCH_CLOSE_MOUNT = [38.0, 39.2];
export const MZ_HATCH_OPEN_STACK = [37.0, 38.2];
export const MZ_HATCH_CLOSE_STACK = [44.0, 45.2];

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
    if (skip) { for (let n = o; n && n !== root; n = n.parent) if (n.name === skip) return; }
    const g = o.geometry;
    const n = g.index ? g.index.count / 3 : (g.getAttribute('position')?.count || 0) / 3;
    tris += n * (o.isInstancedMesh ? o.count : 1);
    draws += Array.isArray(o.material) ? o.material.length : 1;
  });
  return { draws, tris: Math.round(tris) };
}

// Visibility-only hide of the pre-Mechazilla pad pieces. Does not call
// setActive / setLadderVisible / attachReceptacle, and does not edit
// lv10_tower, access1720, control_tower, or the Launch Pad card.
export const HIDE_TOWER_NODES = ['Tower', 'Arm_Pivot', 'Elevator_Cab', 'QD_Pivot'];
// Pad_Base stays hidden at Lv20 (clash with the r2t2 Mount). Tanks come from
// pad_tanks_lox_lch4_b at Lv20. Below Lv20 Pad_Base (and its baked tanks) stays
// visible, so the tanks GLB is hidden then to avoid doubling.
export const HIDE_PAD_NODES = ['Pad_Base', 'Ladder_Foot', 'Hose_LOX', 'Hose_LCH4'];
export const HIDE_ACCESS_NODES = ['PackRoot', 'Ladder_FootPlate'];
// Live pad crane z-fights the r2t2 crane (hoist-fixed) at Lv20.
export const HIDE_LIVE_CRANE = ['Crane'];

function isUnder(o, root) {
  for (let n = o; n; n = n.parent) if (n === root) return true;
  return false;
}

export function shipNeedsReceptacle(ctx) {
  const rec = ctx && ctx.receptacle, ship = ctx && ctx.ship;
  if (!rec || !ship) return false;
  const hull = (ship.getObjectByName && ship.getObjectByName('Ship_Placeholder')) || ship;
  if (!isUnder(rec, hull) && rec.parent !== hull) return false;
  const st = ctx.shipState;
  return st === 'launch' || st === 'away' || st === 'land';
}

export function mzBoardSeconds(n, stack) {
  return stack ? MZ_BOARD_STACK_SEC : MZ_BOARD_MOUNT_SEC;
}
export function mzDeboardSeconds(n, stack) {
  return stack ? MZ_BOARD_STACK_SEC : MZ_BOARD_MOUNT_SEC;
}

export function createPadMechazilla(THREE) {
  const T = {
    ready: false, failed: false, loading: false,
    root: null, nodes: {}, mx: null, acts: {}, missing: [], clips: [],
    legacyOn: false, legacySaved: null, legacyHidden: [],
    tanks: null, tanksSlab: null, tanksReady: false,
    legsClips: [], legsMx: null, legsActs: {}, legsReady: false, legsMissing: [],
    cabLights: [],
    lv: 1,
    clip: '',
    hatch: null,          // { mx, ca: { crew_hatch_open, crew_hatch_close } }
  };
  const _p = new THREE.Vector3(), _q = new THREE.Quaternion(), _s = new THREE.Vector3();
  const _lp = new THREE.Vector3(), _lq = new THREE.Quaternion(), _ls = new THREE.Vector3();

  function bindMaterials(root) {
    root.traverse((m) => {
      if (!m.isMesh) return;
      m.castShadow = true;
      m.receiveShadow = true;
      const mats = [].concat(m.material || []);
      for (const mat of mats) {
        if (!mat) continue;
        if (mat.name === 'MZ_GlassClear') {
          mat.transparent = true;
          mat.depthWrite = false;
          mat.side = THREE.DoubleSide;
          if (!(mat.opacity > 0) || mat.opacity >= 1) mat.opacity = 0.08;
        }
      }
    });
  }

  function addCabLights(s6) {
    if (!s6 || T.cabLights.length) return;
    const col = new THREE.Color(1, 0.94, 0.84);
    const add = (x, y, z, intensity) => {
      const l = new THREE.PointLight(col, intensity, 4, 2);
      l.name = 'TowerCrewCabLight';
      l.position.set(x, y, z);
      s6.add(l);
      T.cabLights.push(l);
    };
    // EXPORT: ~260 W and ~160 W equivalents, range ~4 m, in S6 local space.
    add(0, 1.9, 0, 5.0);
    add(-1.6, 1.9, 0, 3.0);
  }

  function bind(gltf, padRoot) {
    const root = gltf.scene;
    root.name = 'Pad_Mechazilla';
    root.position.set(0, 0, 0);
    root.rotation.set(0, 0, 0);
    padRoot.add(root);
    root.updateMatrixWorld(true);
    T.root = root;
    T.nodes = {};
    T.missing = [];
    for (const n of PAD_MZ_NODES) {
      const o = root.getObjectByName(n);
      T.nodes[n] = o || null;
      if (!o) T.missing.push(n);
    }
    bindMaterials(root);
    addCabLights(T.nodes.TowerCrewArm_S6);
    // r2t2 Mount and Crane are the Lv20 deck + hoist-fixed PC-1. The live
    // Pad_Base / Crane are hidden only while MZ is wanted (applyLegacyHide).
    if (T.nodes.Mount) T.nodes.Mount.visible = true;
    if (T.nodes.Crane) T.nodes.Crane.visible = true;
    T.mx = new THREE.AnimationMixer(root);
    T.acts = {};
    T.clips = [];
    for (const c of gltf.animations || []) {
      T.clips.push(c.name);
      const a = T.mx.clipAction(c);
      a.setLoop(THREE.LoopOnce, 1);
      a.clampWhenFinished = true;
      a.enabled = true;
      a.paused = true;
      T.acts[c.name] = a;
    }
    T.ready = true;
    T.failed = false;
    return info();
  }

  function bindTanks(gltf, padRoot) {
    const root = gltf.scene;
    root.name = 'Pad_Tanks';
    const named = root.getObjectByName('Pad_Tanks') || root;
    T.tanks = named;
    T.tanksSlab = named.getObjectByName('Pad_Tanks_Slab') || root.getObjectByName('Pad_Tanks_Slab');
    named.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
    if (named.parent !== padRoot) padRoot.add(named);
    T.tanksReady = true;
    applyTanks();
    return named;
  }

  function bindLegsGltf(gltf) {
    T.legsClips = (gltf.animations || []).slice();
    T.legsReady = T.legsClips.length > 0;
  }

  function bindLegs(skirtRoot) {
    if (!skirtRoot || !T.legsClips.length) return { ok: false, why: 'no skirt or clips' };
    // Don't add the legs GLB mesh; retarget clips onto the live Aft_Skirt.
    let root = skirtRoot;
    const named = skirtRoot.getObjectByName && (skirtRoot.getObjectByName('Aft_Skirt') || skirtRoot.getObjectByName('Aft_Skirt_Module') || skirtRoot.getObjectByName('Aft_Skirt_Root'));
    if (named && named !== skirtRoot) {
      // mixer should own the object that holds the bones; prefer the module root
      root = skirtRoot;
    }
    T.legsMissing = [];
    const boneOf = (name) => {
      let found = null;
      root.traverse((o) => { if (!found && o.name === name) found = o; });
      return found;
    };
    const sample = T.legsClips[0];
    const names = new Set();
    for (const tr of sample.tracks) {
      const n = tr.name.split('.')[0];
      if (n) names.add(n);
    }
    for (const n of names) if (!boneOf(n)) T.legsMissing.push(n);
    if (T.legsMx) { T.legsMx.stopAllAction(); T.legsMx = null; }
    T.legsMx = new THREE.AnimationMixer(root);
    T.legsActs = {};
    for (const c of T.legsClips) {
      const a = T.legsMx.clipAction(c, root);
      a.setLoop(THREE.LoopOnce, 1);
      a.clampWhenFinished = true;
      T.legsActs[c.name] = a;
    }
    return { ok: T.legsMissing.length === 0, missing: T.legsMissing.slice(), clips: T.legsClips.map((c) => c.name) };
  }

  function bindHatch(mx, clips) {
    if (!mx || !clips) return;
    T.hatch = { mx, ca: {} };
    for (const c of clips) {
      if (c && (c.name === 'crew_hatch_open' || c.name === 'crew_hatch_close')) {
        T.hatch.ca[c.name] = mx.clipAction(c);
      }
    }
  }

  function load(loader, padRoot, onOk, onErr) {
    if (T.ready) { if (onOk) onOk(info()); return; }
    if (T.loading) return;
    if (!padRoot) { const e = new Error('pad root missing'); T.failed = true; if (onErr) onErr(e); return; }
    T.loading = true;
    let left = 3, err = null;
    const done = () => {
      left--;
      if (left > 0) return;
      T.loading = false;
      if (err && !T.ready) { T.failed = true; if (onErr) onErr(err); }
      else if (T.ready && onOk) onOk(info());
    };
    loader.load(PAD_MZ_URL, (g) => {
      try { bind(g, padRoot); }
      catch (e) { err = err || e; T.failed = true; console.warn('Pad Mechazilla bind failed', e); }
      done();
    }, undefined, (e) => { err = err || e; console.warn('Pad Mechazilla GLB failed to load', PAD_MZ_URL, e); done(); });
    loader.load(PAD_MZ_LEGS_URL, (g) => {
      try { bindLegsGltf(g); }
      catch (e) { console.warn('Pad Mechazilla legs bind failed', e); }
      done();
    }, undefined, (e) => { console.warn('Pad Mechazilla legs GLB failed to load', PAD_MZ_LEGS_URL, e); done(); });
    loader.load(PAD_TANKS_URL, (g) => {
      try { bindTanks(g, padRoot); }
      catch (e) { console.warn('Pad tanks bind failed', e); }
      done();
    }, undefined, (e) => { console.warn('Pad tanks GLB failed to load', PAD_TANKS_URL, e); done(); });
  }

  function setActive(on) { if (T.root) T.root.visible = !!on; }

  function setPadLv(lv) {
    T.lv = lv | 0;
    applyTanks();
    applyElevator();
  }

  function applyElevator() {
    const el = T.nodes.TowerElevator;
    if (el) el.visible = T.lv >= 20;
  }

  function applyTanks() {
    if (!T.tanks) return;
    const lv20 = T.lv >= 20;
    const p = lv20 ? PAD_TANKS_POS.lv20 : PAD_TANKS_POS.below;
    T.tanks.position.set(p.x, p.y, p.z);
    T.tanks.rotation.set(0, 0, 0);
    if (T.tanksSlab) T.tanksSlab.visible = !!lv20;
    // Below Lv20 the approved Pad_Base mesh already includes these tanks.
    // Showing the new GLB there would double them, so the root is hidden.
    T.tanks.visible = !!lv20;
  }

  function stopClips(except) {
    if (!T.acts) return;
    for (const [n, a] of Object.entries(T.acts)) {
      if (except && except.has(n)) continue;
      if (n.startsWith('crane_')) continue;
      a.stop();
      a.paused = true;
    }
  }

  function poseClip(name, tSec, keep) {
    const a = T.acts[name]; if (!a) return false;
    if (!keep) stopClips(new Set([name]));
    const dur = a.getClip().duration;
    const t = Math.max(0, Math.min(tSec, dur));
    if (!a.isRunning() || a.paused === false) {
      a.reset();
      a.setLoop(THREE.LoopOnce, 1);
      a.clampWhenFinished = true;
      a.enabled = true;
      a.play();
    }
    a.paused = true;
    a.time = t;
    a.enabled = true;
    T.clip = name;
    if (T.mx) T.mx.update(0);
    if (T.root) T.root.updateMatrixWorld(true);
    return true;
  }

  function play(name, loopOnce) {
    const a = T.acts[name]; if (!a) return false;
    stopClips(new Set([name]));
    if (loopOnce !== false) { a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; }
    a.reset(); a.paused = false; a.enabled = true; a.play();
    T.clip = name;
    return true;
  }

  function poseLegs(catchT) {
    if (!T.legsMx || !T.legsActs) return;
    const fold = T.legsActs.Legs_Fold, dep = T.legsActs.Legs_Deploy;
    T.legsMx.stopAllAction();
    if (catchT >= MZ_LEGS_DEPLOY_AT && dep) {
      dep.reset(); dep.play(); dep.paused = true;
      dep.time = Math.min(dep.getClip().duration, catchT - MZ_LEGS_DEPLOY_AT);
      dep.enabled = true;
    } else if (catchT >= MZ_LEGS_FOLD_AT && fold) {
      fold.reset(); fold.play(); fold.paused = true;
      fold.time = Math.min(fold.getClip().duration, catchT - MZ_LEGS_FOLD_AT);
      fold.enabled = true;
    } else if (fold) {
      // frame 0 of Legs_Fold is the deployed rest
      fold.reset(); fold.play(); fold.paused = true; fold.time = 0; fold.enabled = true;
    }
    T.legsMx.update(0);
  }

  function poseHatch(tb, stack) {
    const H = T.hatch; if (!H || !H.ca) return;
    const openW = stack ? MZ_HATCH_OPEN_STACK : MZ_HATCH_OPEN_MOUNT;
    const closeW = stack ? MZ_HATCH_CLOSE_STACK : MZ_HATCH_CLOSE_MOUNT;
    const open = H.ca.crew_hatch_open, close = H.ca.crew_hatch_close;
    const durO = open ? open.getClip().duration : 1.2;
    const durC = close ? close.getClip().duration : 1.2;
    let which = null, t = 0;
    if (tb >= closeW[0]) {
      which = close || open;
      const u = Math.max(0, Math.min(1, (tb - closeW[0]) / (durC || 1)));
      t = close ? u * durC : (1 - u) * durO;
    } else if (tb >= openW[0]) {
      which = open;
      const u = Math.max(0, Math.min(1, (tb - openW[0]) / (durO || 1)));
      t = u * durO;
    } else if (open) {
      which = open; t = 0;
    }
    if (!which) return;
    for (const a of Object.values(H.ca)) { if (a !== which) { a.stop(); a.paused = true; } }
    which.reset(); which.play(); which.paused = true; which.time = t; which.enabled = true;
    H.mx.update(0);
  }

  function followShip(ship) {
    const tr = T.nodes.Ship_Track;
    if (!tr || !ship) return false;
    tr.updateWorldMatrix(true, true);
    tr.matrixWorld.decompose(_p, _q, _s);
    const parent = ship.parent;
    if (parent) {
      parent.updateWorldMatrix(true, false);
      parent.matrixWorld.decompose(_lp, _lq, _ls);
      const inv = parent.matrixWorld.clone().invert();
      ship.position.copy(_p).applyMatrix4(inv);
      const invQ = _lq.clone().invert();
      ship.quaternion.copy(invQ.multiply(_q));
    } else {
      ship.position.copy(_p);
      ship.quaternion.copy(_q);
    }
    ship.updateMatrixWorld(true);
    return true;
  }

  function followCrew(people) {
    if (!people || !people.length || !T.root) return [];
    T.root.updateMatrixWorld(true);
    const out = [];
    for (let i = 0; i < people.length; i++) {
      const p = people[i];
      const mark = T.nodes['Crew_Mark_' + (i + 1)];
      if (!p || !p.obj || !mark) {
        if (p && p.obj) { p.mode = 'hide'; p.obj.visible = false; }
        else if (p) p.mode = 'idle';
        continue;
      }
      mark.updateWorldMatrix(true, false);
      mark.matrixWorld.decompose(_p, _q, _s);
      const sc = Math.min(_s.x, _s.y, _s.z);
      const hide = sc < 0.05;
      if (p.obj.parent !== T.root) {
        p.obj.updateWorldMatrix(true, false);
        T.root.attach(p.obj);
      }
      T.root.worldToLocal(_p);
      p.obj.position.copy(_p);
      const eul = new THREE.Euler().setFromQuaternion(_q, 'YXZ');
      p.obj.rotation.set(0, eul.y, 0);
      p.obj.visible = !hide;
      if (p.handler && p.root) p.root.visible = !hide;
      p.mode = hide ? 'hide' : 'walk';
      out.push({ i, hide, x: +_p.x.toFixed(3), y: +_p.y.toFixed(3), z: +_p.z.toFixed(3), yaw: +eul.y.toFixed(3) });
    }
    return out;
  }

  function releasePeople(people, scene) {
    if (!people || !T.root) return;
    for (const p of people) {
      if (p && p.obj && p.obj.parent === T.root) {
        (scene || T.root.parent || T.root).attach(p.obj);
      }
    }
  }

  function poseCatch(tSec) {
    const ok = poseClip('Catch_Lift_Swing_SetDown', tSec);
    poseLegs(tSec);
    return ok;
  }

  function poseBoard(tSec, stack) {
    const name = stack ? 'TowerCrewBoard_Stack' : 'TowerCrewBoard_Mount';
    const ok = poseClip(name, tSec);
    poseHatch(tSec, !!stack);
    return ok;
  }

  function poseBoardReverse(tSec, stack) {
    const name = stack ? 'TowerCrewBoard_Stack' : 'TowerCrewBoard_Mount';
    const a = T.acts[name]; if (!a) return false;
    const dur = a.getClip().duration;
    return poseBoard(Math.max(0, dur - tSec), stack);
  }

  function turntableYaw() {
    const tt = T.nodes.Mount_Turntable;
    if (!tt) return 0;
    const e = new THREE.Euler().setFromQuaternion(tt.quaternion, 'YXZ');
    return e.y;
  }

  function tickBoard(tb, people, opts) {
    if (!T.ready || !T.root || !T.root.visible) return null;
    const stack = !!(opts && opts.stack);
    poseBoard(tb, stack);
    const marks = followCrew(people);
    const ev = T.nodes.TowerElevator;
    const arm = T.nodes.TowerCrewArm;
    const tt = turntableYaw();
    return {
      clip: stack ? 'TowerCrewBoard_Stack' : 'TowerCrewBoard_Mount',
      stack, tb,
      launch: stack ? MZ_BOARD_STACK_SEC : MZ_BOARD_MOUNT_SEC,
      elevY: ev ? ev.position.y : null,
      armX: arm ? arm.position.x : null,
      turntableDeg: +(tt * 180 / Math.PI).toFixed(2),
      marks,
    };
  }

  function tickDeboard(tb, people, opts) {
    if (!T.ready || !T.root || !T.root.visible) return null;
    const stack = !!(opts && opts.stack);
    poseBoardReverse(tb, stack);
    const marks = followCrew(people);
    return {
      clip: stack ? 'TowerCrewBoard_Stack' : 'TowerCrewBoard_Mount',
      stack, tb, deboard: true, reversed: true,
      done: stack ? MZ_BOARD_STACK_SEC : MZ_BOARD_MOUNT_SEC,
      marks,
    };
  }

  function tick(dt) {
    if (!T.root || !T.root.visible) return;
    // Boarding / catch are posed with absolute time from the game clock; only
    // crane (or a free-running play()) uses mixer dt.
    if (T.mx && T.clip && T.acts[T.clip] && !T.acts[T.clip].paused) T.mx.update(dt);
    if (T.legsMx) T.legsMx.update(0);
  }

  function info() {
    const vis = T.root ? countMesh(T.root) : { draws: 0, tris: 0 };
    let allDraws = 0, allTris = 0;
    if (T.root) {
      T.root.traverse((o) => {
        if (!o.isMesh || !o.geometry) return;
        const g = o.geometry;
        const n = g.index ? g.index.count / 3 : (g.getAttribute('position')?.count || 0) / 3;
        const d = Array.isArray(o.material) ? o.material.length : 1;
        allTris += n; allDraws += d;
      });
    }
    const tanks = T.tanks ? countMesh(T.tanks) : { draws: 0, tris: 0 };
    return {
      ready: T.ready, failed: T.failed, standin: PAD_MZ_STANDIN, url: PAD_MZ_URL, md5: PAD_MZ_MD5,
      visible: !!(T.root && T.root.visible),
      draws: vis.draws, tris: vis.tris,
      drawsAll: allDraws, trisAll: Math.round(allTris),
      missing: T.missing.slice(), clips: T.clips.slice(),
      hidden: [],
      hasCrewTower: !!T.nodes.CrewTower,
      hasTowerElevator: !!T.nodes.TowerElevator,
      cam: PAD_MZ_CAM,
      legacyHide: legacyInfo(),
      tanks: T.tanksReady ? {
        ready: true, md5: PAD_TANKS_MD5, url: PAD_TANKS_URL,
        visible: !!(T.tanks && T.tanks.visible),
        slab: !!(T.tanksSlab && T.tanksSlab.visible),
        pos: T.tanks ? [+T.tanks.position.x.toFixed(2), +T.tanks.position.y.toFixed(2), +T.tanks.position.z.toFixed(2)] : null,
        draws: tanks.draws, tris: tanks.tris,
      } : { ready: false },
      legs: { ready: T.legsReady, md5: PAD_MZ_LEGS_MD5, missing: T.legsMissing.slice(), clips: T.legsClips.map((c) => c.name) },
      lights: T.cabLights.length,
      clip: T.clip,
      turntableDeg: +(turntableYaw() * 180 / Math.PI).toFixed(2),
    };
  }

  function collectLegacy(ctx) {
    const out = [];
    const add = (o) => { if (o && out.indexOf(o) < 0) out.push(o); };
    const root = ctx && ctx.towerRoot;
    if (root) {
      for (const n of HIDE_TOWER_NODES) add(root.getObjectByName(n));
    }
    if (ctx && ctx.receptacle && !shipNeedsReceptacle(ctx)) add(ctx.receptacle);
    const pad = ctx && ctx.padArt;
    if (pad) {
      for (const n of HIDE_PAD_NODES) {
        const o = pad.getObjectByName(n);
        if (o && !(T.root && isUnder(o, T.root))) add(o);
      }
      for (const n of HIDE_LIVE_CRANE) {
        const o = pad.getObjectByName(n);
        if (o && !(T.root && isUnder(o, T.root))) add(o);
      }
    }
    const acc = ctx && ctx.accRoot;
    if (acc) {
      for (const n of HIDE_ACCESS_NODES) add(acc.getObjectByName(n));
    }
    return out;
  }

  function applyLegacyHide(ctx, on) {
    if (on) {
      if (!T.legacySaved) T.legacySaved = new Map();
      const nodes = collectLegacy(ctx);
      const hidden = [];
      for (const o of nodes) {
        if (!T.legacySaved.has(o)) T.legacySaved.set(o, o.visible);
        o.visible = false;
        if (o.name) hidden.push(o.name);
      }
      if (ctx && ctx.receptacle && shipNeedsReceptacle(ctx)) ctx.receptacle.visible = true;
      T.legacyOn = true;
      T.legacyHidden = hidden;
    } else {
      const restore = new Set();
      const root = ctx && ctx.towerRoot;
      if (root) {
        for (const n of HIDE_TOWER_NODES) {
          const o = root.getObjectByName(n);
          if (o) restore.add(o);
        }
      }
      if (ctx && ctx.padArt) {
        for (const n of [...HIDE_PAD_NODES, ...HIDE_LIVE_CRANE]) {
          const o = ctx.padArt.getObjectByName(n);
          if (o && !(T.root && isUnder(o, T.root))) restore.add(o);
        }
      }
      if (T.legacySaved) {
        for (const [o, v] of T.legacySaved) {
          if (o && restore.has(o)) o.visible = v;
        }
      }
      T.legacySaved = null;
      T.legacyOn = false;
      T.legacyHidden = [];
    }
  }

  function legacyInfo() {
    return { on: !!T.legacyOn, hidden: (T.legacyHidden || []).slice() };
  }

  return {
    T, load, bind, bindLegs, bindHatch, setActive, setPadLv, play, poseClip,
    poseCatch, poseBoard, poseBoardReverse, poseLegs, followShip, followCrew, releasePeople,
    tick, tickBoard, tickDeboard, info, applyLegacyHide, legacyInfo, collectLegacy, applyTanks,
    consts: {
      PAD_MZ_URL, PAD_MZ_MD5, PAD_MZ_CAM, PAD_MZ_STANDIN, PAD_MZ_NODES, PAD_MZ_CLIPS,
      PAD_MZ_LEGS_URL, PAD_MZ_LEGS_MD5, PAD_TANKS_URL, PAD_TANKS_MD5, PAD_TANKS_POS,
      MZ_CATCH_SEC, MZ_BOARD_MOUNT_SEC, MZ_BOARD_STACK_SEC,
    },
  };
}
