// Scene side of the PR17 crew access (1015 bay/airlock packet). Timing and IK live in access1720.mjs.
import {
  nominalRungs, showTimes, poseShow, outwardOf, stageRungLocals, climbDur,
  DEPLOY_T, BAY_DOOR_SEC, LADDER_DEPLOY_SEC, LADDER_STOW_SEC,
} from './access1720.mjs';

export const HULL_URL = '../qa3d-next/models/pr17_hull_bay_1015_ee26cbd9.glb?v=ee26cbd9';
// Single swap point when A&A ships the resized airlock. Today the airlock corridor lives
// inside the 1015 access assembly (ladder + bay door + airlock); change only this path.
export const AIRLOCK_URL = '../qa3d-next/models/pr17_access_assembly_1015_7dc4c876.glb?v=7dc4c876';
export const ACCESS_URL = AIRLOCK_URL;

export function accessSeconds(n, rungs) {
  return showTimes(Math.max(1, n | 0), rungs || nominalRungs(), 6).launch;
}

export function createAccess(THREE) {
  const A = {
    ready: false, failed: false, rungs: null, outward: null, show: null,
    mixer: null, acts: null, root: null, old: [],
  };
  const q = (v) => new THREE.Quaternion(v.x, v.y, v.z, v.w);
  const v = (p) => new THREE.Vector3(p.x, p.y, p.z);

  function findClip(clips, name) {
    return (clips || []).find((c) => c.name === name) || null;
  }

  function makeAction(mixer, clip) {
    const act = mixer.clipAction(clip);
    act.setLoop(THREE.LoopOnce, 0);
    act.clampWhenFinished = true;
    act.enabled = true;
    act.paused = true;
    act.play();
    return act;
  }

  // Scrub discrete BayDoor / Ladder clips to match show timeline.
  // Sequence: BayDoor_Open → Ladder_Deploy → (climb) → Ladder_Stow → BayDoor_Close.
  // InnerHatch_* stays unwired (empty mount; locked Access_InnerDoor stays as served).
  function syncClips(tb, show) {
    const acts = A.acts; if (!acts) return { clip: 0, door: 0 };
    const set = (act, t, dur) => {
      if (!act) return;
      act.enabled = true;
      act.paused = true;
      act.time = Math.max(0, Math.min(dur - 1e-4, t));
      act.setEffectiveWeight(1);
    };
    const zero = (act) => { if (act) { act.time = 0; act.setEffectiveWeight(0); } };

    // Door open 0..BAY_DOOR_SEC; held open until show.stow; close over BAY_DOOR_SEC after stow.
    let doorK = 0;
    if (tb < BAY_DOOR_SEC) {
      set(acts.doorOpen, tb, BAY_DOOR_SEC);
      zero(acts.doorClose);
      doorK = Math.max(0, Math.min(1, tb / BAY_DOOR_SEC));
    } else if (tb < show.stow) {
      set(acts.doorOpen, BAY_DOOR_SEC - 1e-4, BAY_DOOR_SEC);
      zero(acts.doorClose);
      doorK = 1;
    } else {
      const ct = tb - show.stow;
      zero(acts.doorOpen);
      set(acts.doorClose, ct, BAY_DOOR_SEC);
      doorK = 1 - Math.max(0, Math.min(1, ct / BAY_DOOR_SEC));
    }

    // Ladder: idle stowed until door open finishes; deploy; hold; stow after last inside (show.close).
    let clipT = 0;
    if (tb < BAY_DOOR_SEC) {
      set(acts.deploy, 0, LADDER_DEPLOY_SEC);
      zero(acts.stow);
      clipT = 0;
    } else if (tb < show.deploy) {
      const lt = tb - BAY_DOOR_SEC;
      set(acts.deploy, lt, LADDER_DEPLOY_SEC);
      zero(acts.stow);
      clipT = lt;
    } else if (tb < show.close) {
      set(acts.deploy, LADDER_DEPLOY_SEC - 1e-4, LADDER_DEPLOY_SEC);
      zero(acts.stow);
      clipT = LADDER_DEPLOY_SEC;
    } else if (tb < show.stow) {
      const lt = tb - show.close;
      zero(acts.deploy);
      set(acts.stow, lt, LADDER_STOW_SEC);
      clipT = LADDER_DEPLOY_SEC + lt;
    } else {
      zero(acts.deploy);
      set(acts.stow, LADDER_STOW_SEC - 1e-4, LADDER_STOW_SEC);
      clipT = LADDER_DEPLOY_SEC + LADDER_STOW_SEC;
    }
    A.mixer.update(0);
    return { clip: clipT, door: doorK };
  }

  function applyPose(person, pose) {
    if (typeof window !== 'undefined' && window.__ps3d && window.__ps3d.freezeClimb) return;
    const pfx = person.pfx;
    const root = person.obj.getObjectByName(pfx + '_Root');
    if (!root) return;
    root.position.set(0, 0, 0);
    root.scale.set(1, 1, 1);
    root.quaternion.copy(q(pose.yawQ));
    for (const name of ['Hips', 'Spine', 'Chest']) {
      const b = person.obj.getObjectByName(pfx + '_' + name);
      if (b) b.quaternion.identity();
    }
    for (const name of ['Neck', 'Head']) {
      const b = person.obj.getObjectByName(pfx + '_' + name);
      if (b && person.rest[name]) b.quaternion.copy(person.rest[name]);
    }
    for (const name in pose.bones) {
      const b = person.obj.getObjectByName(pfx + '_' + name);
      if (b) b.quaternion.copy(q(pose.bones[name]));
    }
    // Ship_Placeholder child: ship-local metres.
    person.obj.position.copy(v(pose.root));
    person.obj.quaternion.identity();
    person.obj.updateMatrixWorld(true);
  }

  function tick(tb, people) {
    if (!A.ready) return null;
    const show = showTimes(Math.max(1, people.length), A.rungs, 6);
    A.show = show;
    const sync = syncClips(tb, show);
    const info = [];
    const foot = A.rungs[0], out = A.outward, side = { x: out.z, y: 0, z: -out.x };
    people.forEach((person, i) => {
      const slot = show.finish[i];
      if (!slot) return;
      const tau = tb - slot.start;
      person.mode = 'wait';
      person.outside = false;
      if (tau < -0.01) {
        if (person.stand) {
          const dest = v({
            x: foot.x + out.x * 1.15 + side.x * (i - (people.length - 1) / 2) * 0.75,
            y: 0,
            z: foot.z + out.z * 1.15 + side.z * (i - (people.length - 1) / 2) * 0.75,
          });
          const u = slot.start > 0.05 ? Math.min(1, tb / slot.start) : 1;
          person.obj.position.lerpVectors(person.stand, dest, u);
          person.obj.quaternion.identity();
          person.obj.visible = true;
          person.mode = 'walk';
          person.outside = true;
        }
        return;
      }
      if (tau > show.per + 0.05) { person.obj.visible = false; person.mode = 'inside'; return; }
      person.obj.visible = true;
      const pose = poseShow(A.rungs, A.outward, Math.max(0, tau));
      if (tau <= show.climb) {
        person.mode = 'climb';
        person.outside = true;
        applyPose(person, pose);
      } else {
        const u = show.deck > 1e-4 ? Math.min(1, (tau - show.climb) / show.deck) : 1;
        person.mode = u < 0.55 ? 'walk' : 'enter';
        person.outside = u < 0.55;
        if (person.mode === 'enter') applyPose(person, pose);
        else person.obj.position.copy(v(pose.root));
      }
      info.push({ i, tau, err: pose.err || 0, contacts: (pose.contacts || []).length });
    });
    return { clip: sync.clip, door: sync.door, info, show };
  }

  function bind(hullG, accG, hullNode, hide) {
    const hullRoot = hullG.scene.getObjectByName('PR17_Hull_Replacement');
    const asm = accG.scene.getObjectByName('PR17_Access_Assembly');
    const rails = accG.scene.getObjectByName('Rails');
    const clips = accG.animations || [];
    const cDeploy = findClip(clips, 'Ladder_Deploy');
    const cStow = findClip(clips, 'Ladder_Stow');
    const cDoorOpen = findClip(clips, 'BayDoor_Open');
    const cDoorClose = findClip(clips, 'BayDoor_Close');
    // InnerHatch_* intentionally unused — mount is empty; locked Access_InnerDoor stays as served.
    if (!hullRoot || !asm || !rails || !cDeploy || !cStow || !cDoorOpen || !cDoorClose) {
      throw new Error('access 1015 nodes/clips missing');
    }
    // Rails is multi-primitive → Group; morph influences live on mesh children (24 targets).
    let railsMorph = (rails.morphTargetInfluences && rails.morphTargetInfluences.length >= 24) ? rails : null;
    if (!railsMorph) {
      rails.traverse((o) => {
        if (!railsMorph && o.morphTargetInfluences && o.morphTargetInfluences.length >= 24) railsMorph = o;
      });
    }
    if (!railsMorph) throw new Error('access 1015 rails morphs missing');
    for (const scene of [hullG.scene, accG.scene]) {
      scene.position.set(0, 0, 0); scene.quaternion.identity(); scene.scale.set(1, 1, 1);
      scene.traverse((m) => { if (m.isMesh) { m.castShadow = m.receiveShadow = true; m.frustumCulled = false; } });
      hullNode.add(scene);
    }
    for (const o of hide) if (o) { o.visible = false; A.old.push(o); }

    const mixer = new THREE.AnimationMixer(accG.scene);
    const acts = {
      deploy: makeAction(mixer, cDeploy),
      stow: makeAction(mixer, cStow),
      doorOpen: makeAction(mixer, cDoorOpen),
      doorClose: makeAction(mixer, cDoorClose),
    };
    // Sample rungs at fully deployed pose.
    acts.deploy.time = LADDER_DEPLOY_SEC - 1e-4;
    acts.deploy.setEffectiveWeight(1);
    acts.stow.setEffectiveWeight(0);
    acts.doorOpen.time = BAY_DOOR_SEC - 1e-4;
    acts.doorOpen.setEffectiveWeight(1);
    acts.doorClose.setEffectiveWeight(0);
    mixer.update(0);
    accG.scene.updateMatrixWorld(true);

    const rungs = [];
    const inv = new THREE.Matrix4().copy(hullNode.matrixWorld).invert();
    function stageMesh(stage) {
      if (!stage) return null;
      if (stage.isMesh) return stage;
      let m = null;
      stage.traverse((o) => { if (!m && o.isMesh) m = o; });
      return m;
    }
    for (let s = 0; s < 6; s++) {
      const stage = accG.scene.getObjectByName('LadderStage_' + s);
      const mesh = stageMesh(stage);
      if (!mesh) throw new Error('stage mesh ' + s);
      mesh.updateWorldMatrix(true, false);
      const toShip = new THREE.Matrix4().multiplyMatrices(inv, mesh.matrixWorld);
      for (const ly of stageRungLocals()) {
        const p = new THREE.Vector3(0, ly, 0).applyMatrix4(toShip);
        rungs.push({ x: p.x, y: p.y, z: p.z });
      }
    }
    rungs.sort((a, b) => a.y - b.y);
    if (rungs.length < 8) throw new Error('rungs missing');

    // Rest: door closed, ladder stowed.
    acts.deploy.time = 0; acts.deploy.setEffectiveWeight(0);
    acts.doorOpen.time = 0; acts.doorOpen.setEffectiveWeight(0);
    mixer.update(0);

    A.rungs = rungs;
    A.outward = outwardOf(rungs[Math.floor(rungs.length / 2)]);
    A.show = showTimes(4, rungs, 6);
    A.mixer = mixer;
    A.acts = acts;
    A.root = asm;

    // Minimal fill light so the current airlock reads in the end-shot camera (no polish).
    const airlock = accG.scene.getObjectByName('Airlock_Corridor_White');
    if (airlock) {
      const light = new THREE.PointLight(0xe8f0ff, 1.1, 8, 2);
      light.name = 'Access_Airlock_Fill';
      light.position.set(0, 30.2, 2.4);
      (asm || accG.scene).add(light);
    }

    A.ready = true;
    A.morph = true;
    return { rungs: rungs.length, climb: +climbDur(rungs).toFixed(3), launch4: +A.show.launch.toFixed(3) };
  }

  return { A, tick, bind, syncClips };
}
