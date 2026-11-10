// Lv10 launch tower (A&A lv10_tower_export_0735 merged pack).
// Replaces the 1720 ladder at Launch Pad level 10 only. Levels 1–9 keep the ladder.
// Meshopt-compressed; load with GLTFLoader.setMeshoptDecoder(MeshoptDecoder).
// Look meshes up by the named parent (gltfpack adds unnamed dequantise children).

export const TOWER_URL = '../qa3d-next/models/lv10_tower_game_merged_v2_ea9c895d.glb?v=ea9c895d';

export const ARM_RETRACT_SEC = 6.0;
export const ARM_EXTEND_SEC = 6.0;
export const QD_RELEASE_SEC = 2.5;
export const QD_CONNECT_SEC = 2.5;
export const ELEV_UP_SEC = 10.0;
export const ELEV_DOWN_SEC = 8.0;
export const DOOR_SEC = 1.5;
export const WALK_V = 1.4;          // same as access1720
export const CAB_CAP = 2;
export const ENTER_SEC = 1.2;       // last steps through the hatch
export const STAGGER_SEC = 0.7;     // second crew into / out of the cab
export const APPROACH_M = 3.2;      // pad walk to the ground doors
export const ARM_WALK_M = 11.2;     // cab floor to hatch sill along the arm
export const CAB_FLOOR_Y = 0.31;    // Lift_Bottom / Lift_Top floor height (glTF y)

const CLIP_DUR = {
  Arm_Retract: ARM_RETRACT_SEC,
  Arm_Extend: ARM_EXTEND_SEC,
  QD_Release: QD_RELEASE_SEC,
  QD_Connect: QD_CONNECT_SEC,
  Elevator_Up: ELEV_UP_SEC,
  Elevator_Down: ELEV_DOWN_SEC,
  Cab_Doors_Open: DOOR_SEC,
  Cab_Doors_Close: DOOR_SEC,
  Arm_Doors_Open: DOOR_SEC,
  Arm_Doors_Close: DOOR_SEC,
};

const PAIR = {
  Arm_Retract: 'Arm_Extend', Arm_Extend: 'Arm_Retract',
  QD_Release: 'QD_Connect', QD_Connect: 'QD_Release',
  Elevator_Up: 'Elevator_Down', Elevator_Down: 'Elevator_Up',
  Cab_Doors_Open: 'Cab_Doors_Close', Cab_Doors_Close: 'Cab_Doors_Open',
  Arm_Doors_Open: 'Arm_Doors_Close', Arm_Doors_Close: 'Arm_Doors_Open',
};

function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
function walkSec(m) { return Math.max(0.4, m / WALK_V); }

// One elevator trip (n = 1..CAB_CAP people): doors, walk in, ride, walk the arm, enter hatch.
function tripBoardSec(nIn) {
  const inWalk = walkSec(APPROACH_M) + (nIn > 1 ? STAGGER_SEC : 0);
  const armWalk = walkSec(ARM_WALK_M) + (nIn > 1 ? STAGGER_SEC : 0);
  // Cab doors open, walk in, close, ride up, cab+arm doors open (overlap), walk arm, enter, doors close.
  return DOOR_SEC + inWalk + DOOR_SEC + ELEV_UP_SEC + DOOR_SEC + armWalk + ENTER_SEC + DOOR_SEC;
}

function tripDeboardSec(nOut) {
  const armWalk = walkSec(ARM_WALK_M) + (nOut > 1 ? STAGGER_SEC : 0);
  const outWalk = walkSec(APPROACH_M) + (nOut > 1 ? STAGGER_SEC : 0);
  // Doors open at top, walk arm into cab, close, ride down, open, walk out, close.
  return DOOR_SEC + armWalk + ENTER_SEC + DOOR_SEC + ELEV_DOWN_SEC + DOOR_SEC + outWalk + DOOR_SEC;
}

function tripsOf(n) { return Math.max(1, Math.ceil(Math.max(1, n | 0) / CAB_CAP)); }

// Sim duration: art-independent, frozen onto the trip as sh.bsec / sh.dsec.
export function towerBoardSeconds(n) {
  n = Math.max(1, n | 0);
  const trips = tripsOf(n);
  // Rest is cab at the hatch: first send it down. After the last crew is inside: QD_Release, Arm_Retract.
  let t = ELEV_DOWN_SEC;
  let left = n;
  for (let i = 0; i < trips; i++) {
    const k = Math.min(CAB_CAP, left);
    t += tripBoardSec(k);
    left -= k;
    if (i < trips - 1) t += ELEV_DOWN_SEC; // empty cab returns for the next group
  }
  t += QD_RELEASE_SEC + ARM_RETRACT_SEC;
  return t;
}

export function towerDeboardSeconds(n) {
  n = Math.max(1, n | 0);
  const trips = tripsOf(n);
  // After landing the arm is retracted: Arm_Extend, QD_Connect, then reverse trips.
  // Cab starts at the hatch (it stayed there through the flight). Empty cab returns to the hatch at the end.
  let t = ARM_EXTEND_SEC + QD_CONNECT_SEC;
  let left = n;
  for (let i = 0; i < trips; i++) {
    const k = Math.min(CAB_CAP, left);
    t += tripDeboardSec(k);
    left -= k;
    if (i < trips - 1) t += ELEV_UP_SEC;
  }
  t += ELEV_UP_SEC; // empty cab back to the hatch landing (rest pose)
  return t;
}

export function towerResetSeconds() { return ARM_EXTEND_SEC + QD_CONNECT_SEC; }

function findClip(clips, name) {
  return (clips || []).find((c) => c.name === name) || null;
}

function makeAction(mixer, clip, THREE) {
  const act = mixer.clipAction(clip);
  act.setLoop(THREE.LoopOnce, 0);
  act.clampWhenFinished = true;
  act.enabled = true;
  act.paused = true;
  act.play();
  act.setEffectiveWeight(0);
  return act;
}

function underName(o, re) {
  for (let n = o; n; n = n.parent) if (re.test(n.name || '')) return true;
  return false;
}

// Hide the 1720 telescoping ladder (and foot) at L10. Bay door + airlock stay so the hatch opening remains.
export function setLadderVisible(accRoot, on) {
  if (!accRoot) return;
  accRoot.traverse((o) => {
    const n = o.name || '';
    const isLadder = underName(o, /^(LadderStage_|Rails|Ladder_Sleeve|Ladder_Foot|PackRoot|Study_1353_DeckThin|Deck_Root|DeckPack|DeckThin)/)
      || /Rung/i.test(n) || n === 'Ladder_FootPlate' || n === 'Rails';
    if (isLadder && (o.isMesh || o.isInstancedMesh || o.isGroup || o.isObject3D)) {
      if (o.isMesh || o.isInstancedMesh) o.visible = !!on;
    }
  });
  // Named roots: if present, hide the whole pack when off.
  for (const n of ['PackRoot', 'Ladder_FootPlate']) {
    const o = accRoot.getObjectByName(n);
    if (o) o.visible = !!on;
  }
}

function fixBlendMats(root) {
  // Tw_MainBlend is used on whole Arm_Body / Cab_Body / cab leaves (not just glass).
  // depthWrite + a stable renderOrder avoids alpha sort holes from some pad cameras.
  const seen = new Set();
  root.traverse((o) => {
    if (!o.isMesh) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of mats) {
      if (!m || seen.has(m)) continue;
      seen.add(m);
      const n = m.name || '';
      if (n === 'Tw_MainBlend' || (m.transparent && /^Tw_/.test(n))) {
        m.depthWrite = true;
        m.transparent = true;
        m.needsUpdate = true;
      }
    }
    const mn = (Array.isArray(o.material) ? o.material[0] : o.material);
    if (mn && (mn.name === 'Tw_MainBlend' || mn.transparent)) o.renderOrder = 2;
  });
}

export function createLv10Tower(THREE) {
  const T = {
    ready: false, failed: false, loading: false, active: false,
    root: null, mixer: null, acts: null, nodes: {},
    receptacle: null, receptacleHome: null, ship: null, retracted: false, resetT0: 0,
  };

  function byName(n) { return T.root && T.root.getObjectByName(n); }

  function zero(act) { if (act) { act.time = 0; act.setEffectiveWeight(0); } }

  function play(name, t) {
    const acts = T.acts; if (!acts || !acts[name]) return;
    const dur = CLIP_DUR[name];
    const mate = PAIR[name];
    if (mate) zero(acts[mate]);
    const act = acts[name];
    act.enabled = true;
    act.paused = true;
    act.time = clamp(t, 0, Math.max(0, dur - 1e-4));
    act.setEffectiveWeight(1);
  }

  // Drive a pair so k=0 is the rest/bind end and k=1 is the "done" end of the named clip.
  function playK(name, k) {
    play(name, clamp(k, 0, 1) * CLIP_DUR[name]);
  }

  function poseRest() {
    if (!T.acts) return;
    play('Arm_Retract', 0);
    play('QD_Release', 0);
    play('Elevator_Down', 0); // t=0 = hatch landing
    play('Cab_Doors_Open', 0);
    play('Arm_Doors_Open', 0);
    T.mixer.update(0);
    T.retracted = false;
  }

  function poseRetracted() {
    if (!T.acts) return;
    play('Arm_Retract', ARM_RETRACT_SEC);
    play('QD_Release', QD_RELEASE_SEC);
    play('Elevator_Down', 0);
    play('Cab_Doors_Open', 0);
    play('Arm_Doors_Open', 0);
    T.mixer.update(0);
    T.retracted = true;
  }

  function poseReset(u) {
    // u seconds since landing/reset: Arm_Extend then QD_Connect.
    if (u < ARM_EXTEND_SEC) {
      play('Arm_Extend', u);
      play('QD_Release', QD_RELEASE_SEC); // still unplugged until connect starts
    } else {
      play('Arm_Extend', ARM_EXTEND_SEC);
      play('QD_Connect', u - ARM_EXTEND_SEC);
    }
    play('Elevator_Down', 0);
    play('Cab_Doors_Open', 0);
    play('Arm_Doors_Open', 0);
    T.mixer.update(0);
    T.retracted = u < ARM_EXTEND_SEC + QD_CONNECT_SEC - 1e-3;
  }

  function attachReceptacle(ship) {
    ship = ship || T.ship;
    if (ship) T.ship = ship;
    if (!T.receptacle || !ship) return;
    const hull = ship.getObjectByName('Ship_Placeholder') || ship;
    if (T.receptacle.parent === hull) return;
    T.receptacle.updateWorldMatrix(true, false);
    hull.updateWorldMatrix(true, false);
    hull.attach(T.receptacle);   // world-preserving: port stays on the hull skin
  }

  function returnReceptacle() {
    if (!T.receptacle || !T.receptacleHome) return;
    if (T.receptacle.parent === T.receptacleHome) return;
    T.receptacle.updateWorldMatrix(true, false);
    T.receptacleHome.updateWorldMatrix(true, false);
    T.receptacleHome.attach(T.receptacle);   // world-preserving return to the tower
  }

  function bind(gltf, pad, ship) {
    const scene = gltf.scene;
    scene.name = 'Lv10_Tower_Art';
    // Markers that would clash with the pad's own empties (especially Ship_Placeholder).
    const sp = scene.getObjectByName('Ship_Placeholder');
    if (sp) sp.name = 'Lv10_Ship_Placeholder';
    const po = scene.getObjectByName('Pad_Origin');
    if (po) po.name = 'Lv10_Pad_Origin';

    scene.position.set(0, 0, 0);
    scene.quaternion.identity();
    scene.scale.set(1, 1, 1);
    scene.traverse((m) => {
      if (m.isMesh) {
        m.castShadow = true;
        m.receiveShadow = true;
        m.frustumCulled = false;
      }
    });
    pad.add(scene);
    scene.updateMatrixWorld(true);
    T.root = scene;

    const clips = gltf.animations || [];
    for (const n of Object.keys(CLIP_DUR)) {
      if (!findClip(clips, n)) throw new Error('lv10 tower clip missing: ' + n);
    }
    const mixer = new THREE.AnimationMixer(scene);
    const acts = {};
    for (const n of Object.keys(CLIP_DUR)) acts[n] = makeAction(mixer, findClip(clips, n), THREE);
    T.mixer = mixer;
    T.acts = acts;

    T.nodes = {
      tower: byName('Tower'),
      cab: byName('Elevator_Cab'),
      armPivot: byName('Arm_Pivot'),
      armBody: byName('Arm_Body'),
      qdPivot: byName('QD_Pivot'),
      hatch: byName('Hatch_Target'),
      sill: byName('Hatch_Sill'),
      liftBottom: byName('Lift_Bottom'),
      liftTop: byName('Lift_Top'),
      receptacle: byName('QD_Receptacle'),
    };
    if (!T.nodes.tower || !T.nodes.cab || !T.nodes.armPivot || !T.nodes.qdPivot || !T.nodes.receptacle) {
      throw new Error('lv10 tower nodes missing');
    }

    fixBlendMats(scene);
    // v2 pack: QD_Receptacle is its own named mesh (gltfpack puts the tris on the
    // unnamed dequantise child). Look it up by name and keep it on the tower until
    // liftoff, then world-preserving attach to the hull; return it on reset / landing.
    T.receptacle = T.nodes.receptacle;
    if (!T.receptacle) throw new Error('lv10 tower QD_Receptacle missing');
    T.receptacleHome = T.receptacle.parent;
    T.ship = ship || T.ship || null;

    poseRest();
    T.ready = true;
    T.failed = false;
    T.active = true;
    scene.visible = true;
    return info();
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
    return {
      ready: T.ready, draws, tris: Math.round(tris),
      clips: T.acts ? Object.keys(T.acts) : [],
      board2: towerBoardSeconds(2), deboard2: towerDeboardSeconds(2),
      retracted: !!T.retracted,
    };
  }

  function load(loader, pad, ship, onOk, onErr) {
    if (T.ready) {
      T.root.visible = true;
      T.active = true;
      if (ship) T.ship = ship;
      returnReceptacle();
      poseRest();
      if (onOk) onOk(info());
      return;
    }
    if (T.loading) return;
    T.loading = true;
    loader.load(TOWER_URL, (g) => {
      T.loading = false;
      try {
        const i = bind(g, pad, ship);
        if (onOk) onOk(i);
      } catch (e) {
        T.failed = true;
        console.warn('lv10 tower bind failed', e);
        if (onErr) onErr(e);
      }
    }, undefined, (e) => {
      T.loading = false;
      T.failed = true;
      console.warn('lv10 tower GLB failed to load', e);
      if (onErr) onErr(e);
    });
  }

  function setActive(on) {
    T.active = !!on;
    if (T.root) T.root.visible = !!on;
    if (T.receptacle) T.receptacle.visible = !!on;
  }

  // ---- Boarding / deboard timelines (tb = seconds since phase start) ----

  function buildBoardShow(n) {
    n = Math.max(1, n | 0);
    const trips = [];
    let t = 0;
    const cabDown0 = t; t += ELEV_DOWN_SEC;
    let left = n, i0 = 0;
    for (let tr = 0; tr < tripsOf(n); tr++) {
      const k = Math.min(CAB_CAP, left);
      const who = [];
      for (let i = 0; i < k; i++) who.push(i0 + i);
      const inWalk = walkSec(APPROACH_M);
      const armWalk = walkSec(ARM_WALK_M);
      const open1 = t; t += DOOR_SEC;
      const walkIn0 = t; t += inWalk + (k > 1 ? STAGGER_SEC : 0);
      const close1 = t; t += DOOR_SEC;
      const rideUp = t; t += ELEV_UP_SEC;
      const open2 = t; t += DOOR_SEC;           // cab + arm doors (overlap)
      const walkArm0 = t; t += armWalk + (k > 1 ? STAGGER_SEC : 0);
      const enter0 = t; t += ENTER_SEC;
      const close2 = t; t += DOOR_SEC;
      trips.push({ who, open1, walkIn0, inWalk, close1, rideUp, open2, walkArm0, armWalk, enter0, close2, k });
      i0 += k; left -= k;
      if (left > 0) { const down = t; t += ELEV_DOWN_SEC; trips[trips.length - 1].nextDown = down; }
    }
    const qd0 = t; t += QD_RELEASE_SEC;
    const arm0 = t; t += ARM_RETRACT_SEC;
    return { cabDown0, trips, qd0, arm0, launch: t, n };
  }

  function buildDeboardShow(n) {
    n = Math.max(1, n | 0);
    const trips = [];
    let t = 0;
    const extend0 = t; t += ARM_EXTEND_SEC;
    const connect0 = t; t += QD_CONNECT_SEC;
    let left = n, i0 = 0;
    for (let tr = 0; tr < tripsOf(n); tr++) {
      const k = Math.min(CAB_CAP, left);
      const who = [];
      for (let i = 0; i < k; i++) who.push(i0 + i);
      const armWalk = walkSec(ARM_WALK_M);
      const outWalk = walkSec(APPROACH_M);
      const open1 = t; t += DOOR_SEC;
      const walkArm0 = t; t += armWalk + (k > 1 ? STAGGER_SEC : 0);
      const enter0 = t; t += ENTER_SEC;         // into the cab from the arm
      const close1 = t; t += DOOR_SEC;
      const rideDown = t; t += ELEV_DOWN_SEC;
      const open2 = t; t += DOOR_SEC;
      const walkOut0 = t; t += outWalk + (k > 1 ? STAGGER_SEC : 0);
      const close2 = t; t += DOOR_SEC;
      trips.push({ who, open1, walkArm0, armWalk, enter0, close1, rideDown, open2, walkOut0, outWalk, close2, k });
      i0 += k; left -= k;
      if (left > 0) { const up = t; t += ELEV_UP_SEC; trips[trips.length - 1].nextUp = up; }
    }
    const cabUp0 = t; t += ELEV_UP_SEC;
    return { extend0, connect0, trips, cabUp0, done: t, n };
  }

  function driveBoardClips(tb, show) {
    // Default: cab at top, doors closed, arm docked, QD plugged — then overwrite from the show.
    play('Arm_Retract', 0);
    play('QD_Release', 0);
    play('Elevator_Down', 0);
    play('Cab_Doors_Open', 0);
    play('Arm_Doors_Open', 0);

    if (tb < show.cabDown0 + ELEV_DOWN_SEC) {
      play('Elevator_Down', tb - show.cabDown0);
    } else {
      play('Elevator_Down', ELEV_DOWN_SEC);
    }

    for (const tr of show.trips) {
      if (tb >= tr.rideUp) {
        if (tb < tr.rideUp + ELEV_UP_SEC) play('Elevator_Up', tb - tr.rideUp);
        else play('Elevator_Up', ELEV_UP_SEC);
      }
      if (tr.nextDown != null && tb >= tr.nextDown) {
        if (tb < tr.nextDown + ELEV_DOWN_SEC) play('Elevator_Down', tb - tr.nextDown);
        else play('Elevator_Down', ELEV_DOWN_SEC);
      }
      // Cab doors
      if (tb >= tr.open1 && tb < tr.close1) {
        if (tb < tr.open1 + DOOR_SEC) play('Cab_Doors_Open', tb - tr.open1);
        else play('Cab_Doors_Open', DOOR_SEC);
      } else if (tb >= tr.close1 && tb < tr.open2) {
        play('Cab_Doors_Close', Math.min(DOOR_SEC, tb - tr.close1));
      } else if (tb >= tr.open2 && tb < tr.close2) {
        if (tb < tr.open2 + DOOR_SEC) play('Cab_Doors_Open', tb - tr.open2);
        else play('Cab_Doors_Open', DOOR_SEC);
        if (tb < tr.open2 + DOOR_SEC) play('Arm_Doors_Open', tb - tr.open2);
        else play('Arm_Doors_Open', DOOR_SEC);
      } else if (tb >= tr.close2) {
        play('Cab_Doors_Close', Math.min(DOOR_SEC, tb - tr.close2));
        play('Arm_Doors_Close', Math.min(DOOR_SEC, tb - tr.close2));
      }
    }

    if (tb >= show.qd0) {
      if (tb < show.qd0 + QD_RELEASE_SEC) play('QD_Release', tb - show.qd0);
      else play('QD_Release', QD_RELEASE_SEC);
    }
    if (tb >= show.arm0) {
      if (tb < show.arm0 + ARM_RETRACT_SEC) play('Arm_Retract', tb - show.arm0);
      else play('Arm_Retract', ARM_RETRACT_SEC);
    }
    T.mixer.update(0);
    T.retracted = tb >= show.launch - 1e-3;
  }

  function driveDeboardClips(tb, show) {
    play('Arm_Retract', ARM_RETRACT_SEC);
    play('QD_Release', QD_RELEASE_SEC);
    play('Elevator_Down', 0);
    play('Cab_Doors_Open', 0);
    play('Arm_Doors_Open', 0);

    if (tb < show.connect0) play('Arm_Extend', tb - show.extend0);
    else {
      play('Arm_Extend', ARM_EXTEND_SEC);
      play('QD_Connect', Math.min(QD_CONNECT_SEC, tb - show.connect0));
    }

    for (const tr of show.trips) {
      if (tb >= tr.rideDown) {
        if (tb < tr.rideDown + ELEV_DOWN_SEC) play('Elevator_Down', tb - tr.rideDown);
        else play('Elevator_Down', ELEV_DOWN_SEC);
      }
      if (tr.nextUp != null && tb >= tr.nextUp) {
        if (tb < tr.nextUp + ELEV_UP_SEC) play('Elevator_Up', tb - tr.nextUp);
        else play('Elevator_Up', ELEV_UP_SEC);
      }
      if (tb >= tr.open1 && tb < tr.close1) {
        if (tb < tr.open1 + DOOR_SEC) {
          play('Cab_Doors_Open', tb - tr.open1);
          play('Arm_Doors_Open', tb - tr.open1);
        } else {
          play('Cab_Doors_Open', DOOR_SEC);
          play('Arm_Doors_Open', DOOR_SEC);
        }
      } else if (tb >= tr.close1 && tb < tr.open2) {
        play('Cab_Doors_Close', Math.min(DOOR_SEC, tb - tr.close1));
        play('Arm_Doors_Close', Math.min(DOOR_SEC, tb - tr.close1));
      } else if (tb >= tr.open2 && tb < tr.close2) {
        if (tb < tr.open2 + DOOR_SEC) play('Cab_Doors_Open', tb - tr.open2);
        else play('Cab_Doors_Open', DOOR_SEC);
      } else if (tb >= tr.close2) {
        play('Cab_Doors_Close', Math.min(DOOR_SEC, tb - tr.close2));
      }
    }
    if (tb >= show.cabUp0) play('Elevator_Up', Math.min(ELEV_UP_SEC, tb - show.cabUp0));
    T.mixer.update(0);
    T.retracted = tb < show.connect0 + QD_CONNECT_SEC - 1e-3;
  }

  // Path helpers in pad-local (root local) space.
  function localOf(node, target) {
    const w = node.getWorldPosition(new THREE.Vector3());
    T.root.worldToLocal(w);
    if (target) { target.copy(w); return target; }
    return w;
  }

  function approachPt() {
    // Just outside the ground cab doors, facing +X into the cab.
    const p = localOf(T.nodes.liftBottom);
    p.x -= APPROACH_M;
    p.y = CAB_FLOOR_Y;
    return p;
  }
  function cabPt(slot) {
    // Elevator_Cab rest is identity (floor at Lift_Top y 28.5916). Elevator_Down ends at y -28.2816.
    const dy = T.nodes.cab.position.y || 0;
    return new THREE.Vector3(11.44 + 0.05, 28.5916 + dy, -8.6 + (slot === 0 ? -0.32 : 0.32));
  }
  function hatchPt() {
    const p = localOf(T.nodes.sill || T.nodes.hatch);
    p.y = (T.nodes.sill || T.nodes.hatch).position.y; // sill height
    return localOf(T.nodes.sill || T.nodes.hatch);
  }

  function lerp3(a, b, k) {
    k = clamp(k, 0, 1);
    return new THREE.Vector3(a.x + (b.x - a.x) * k, a.y + (b.y - a.y) * k, a.z + (b.z - a.z) * k);
  }

  function yawToward(from, to) {
    return Math.atan2(to.x - from.x, to.z - from.z);
  }

  function worldFromLocal(p) {
    const w = p.clone();
    T.root.localToWorld(w);
    return w;
  }

  function posePerson(person, world, yaw, mode, tb) {
    const obj = person.obj;
    if (!obj) return;
    // Keep the body under the pad (not the hull) so a rising ship doesn't take mid-walk crew.
    if (obj.parent !== T.root) {
      obj.updateWorldMatrix(true, false);
      T.root.attach(obj);
    }
    T.root.worldToLocal(world);
    obj.position.copy(world);
    obj.rotation.set(0, yaw, 0);
    obj.visible = mode !== 'hide';
    if (person.handler && person.root) person.root.visible = mode !== 'hide';
    person.mode = mode;
  }

  function tickBoard(tb, people) {
    if (!T.ready || !T.active) return null;
    const show = buildBoardShow(Math.max(1, people.length));
    driveBoardClips(tb, show);
    T.root.updateMatrixWorld(true);

    const ap = approachPt();
    const hatch = hatchPt();

    for (let i = 0; i < people.length; i++) {
      const p = people[i];
      let mode = 'idle', pos = ap.clone(), yaw = Math.PI / 2, placed = false;
      for (const tr of show.trips) {
        if (!tr.who.includes(i)) continue;
        const slot = tr.who.indexOf(i);
        const delay = slot * STAGGER_SEC;
        const cab = cabPt(slot);

        if (tb < tr.walkIn0 + delay) {
          pos = ap.clone(); yaw = Math.PI / 2; mode = 'idle';
        } else if (tb < tr.walkIn0 + delay + tr.inWalk) {
          const k = (tb - tr.walkIn0 - delay) / tr.inWalk;
          pos = lerp3(ap, cab, k); yaw = yawToward(ap, cab); mode = 'walk';
        } else if (tb < tr.open2) {
          // In the cab, including the ride up: parent follows Elevator_Cab by using the live cab floor.
          const live = cabPt(slot);
          pos = live; yaw = -Math.PI / 2; mode = 'idle';
        } else if (tb < tr.walkArm0 + delay) {
          pos = cabPt(slot); yaw = -Math.PI / 2; mode = 'idle';
        } else if (tb < tr.walkArm0 + delay + tr.armWalk) {
          const k = (tb - tr.walkArm0 - delay) / tr.armWalk;
          const from = cabPt(slot);
          pos = lerp3(from, hatch, k); yaw = yawToward(from, hatch); mode = 'walk';
        } else if (tb < tr.enter0 + ENTER_SEC) {
          const k = (tb - tr.enter0) / ENTER_SEC;
          const inside = hatch.clone(); inside.z -= 0.8; // step into the hull
          pos = lerp3(hatch, inside, k); yaw = yawToward(hatch, inside); mode = 'walk';
        } else {
          mode = 'hide'; pos = hatch.clone();
        }
        placed = true;
        break;
      }
      if (!placed) { mode = 'idle'; pos = ap.clone(); }
      const w = worldFromLocal(pos);
      posePerson(p, w, yaw, mode, tb);
    }

    return { show, launch: show.launch, retracted: T.retracted };
  }

  function tickDeboard(tb, people) {
    if (!T.ready || !T.active) return null;
    returnReceptacle();   // touchdown: port returns to the tower before Arm_Extend / QD_Connect
    const show = buildDeboardShow(Math.max(1, people.length));
    driveDeboardClips(tb, show);
    T.root.updateMatrixWorld(true);

    const ap = approachPt();
    const hatch = hatchPt();
    const inside = hatch.clone(); inside.z -= 0.8;

    for (let i = 0; i < people.length; i++) {
      const p = people[i];
      let mode = 'hide', pos = inside.clone(), yaw = Math.PI;
      for (const tr of show.trips) {
        if (!tr.who.includes(i)) continue;
        const slot = tr.who.indexOf(i);
        const delay = slot * STAGGER_SEC;
        const cab = cabPt(slot);
        if (tb < tr.open1) {
          mode = 'hide'; pos = inside.clone();
        } else if (tb < tr.walkArm0 + delay) {
          mode = 'idle'; pos = inside.clone(); yaw = yawToward(inside, hatch);
        } else if (tb < tr.walkArm0 + delay + tr.armWalk) {
          // walk hatch → cab (reverse of boarding arm walk, which was cab → hatch)
          const k = (tb - tr.walkArm0 - delay) / tr.armWalk;
          pos = lerp3(hatch, cab, k); yaw = yawToward(hatch, cab); mode = 'walk';
        } else if (tb < tr.open2) {
          pos = cabPt(slot); yaw = Math.PI / 2; mode = 'idle';
        } else if (tb < tr.walkOut0 + delay) {
          pos = cabPt(slot); yaw = Math.PI / 2; mode = 'idle';
        } else if (tb < tr.walkOut0 + delay + tr.outWalk) {
          const k = (tb - tr.walkOut0 - delay) / tr.outWalk;
          const from = cabPt(slot);
          pos = lerp3(from, ap, k); yaw = yawToward(from, ap); mode = 'walk';
        } else {
          pos = ap.clone(); yaw = Math.PI / 2; mode = 'idle';
        }
        break;
      }
      const w = worldFromLocal(pos);
      posePerson(p, w, yaw, mode, tb);
    }
    return { show, done: show.done, retracted: T.retracted, deboard: true };
  }

  function tickIdle(st) {
    if (!T.ready || !T.active) return;
    if (st === 'launch' || st === 'away' || st === 'land') {
      poseRetracted();
      attachReceptacle(T.ship);   // ride the hull; stays attached through away + landing descent
    } else if (T.resetT0) {
      // handled by the caller via tickReset
    } else {
      returnReceptacle();
      if (st === 'pad' || !st) poseRest();
    }
  }

  function tickReset(u) {
    if (!T.ready || !T.active) return false;
    returnReceptacle();   // ship is on the pad; port goes back to the tower before Arm_Extend / QD_Connect
    poseReset(u);
    if (u >= ARM_EXTEND_SEC + QD_CONNECT_SEC) { T.resetT0 = 0; T.retracted = false; return true; }
    return false;
  }

  return {
    T, load, bind, setActive, attachReceptacle, returnReceptacle, poseRest, poseRetracted, poseReset,
    tickBoard, tickDeboard, tickIdle, tickReset, info, play, playK,
    buildBoardShow, buildDeboardShow,
  };
}
