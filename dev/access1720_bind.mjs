// Scene side of the 1720 crew access. Timing and IK live in access1720.mjs.
import {
  nominalRungs, showTimes, poseShow, outwardOf, stageRungLocals, climbDur,
  DEPLOY_T, STOW_T0, CLIP_END, DOOR_SEC, STOW_TEL_T1, STOW_TEL_SEC, STOW_SLIDE_SEC,
} from './access1720.mjs';

export const HULL_URL = '../qa3d-next/models/hull_channel_relief_1720_4700a081.glb?v=4700a081';
export const ACCESS_URL = '../qa3d-next/models/access_platform_ladder_rails_1720_b8bed28c.glb?v=b8bed28c';
const OPEN_OUTER = { x: 1.55, y: 0, z: 0.22 };
const OPEN_INNER = { x: 1.55, y: 0, z: -0.18 };

export function accessSeconds(n, rungs) {
  return showTimes(Math.max(1, n | 0), rungs || nominalRungs(), 6).launch;
}

export function createAccess(THREE) {
  const A = {
    ready: false, failed: false, rungs: null, outward: null, show: null,
    mixer: null, act: null, doors: null, root: null, old: [],
  };
  const q = (v) => new THREE.Quaternion(v.x, v.y, v.z, v.w);
  const v = (p) => new THREE.Vector3(p.x, p.y, p.z);

  function clipAt(tb, show) {
    if (tb < show.deploy) return (tb / show.deploy) * DEPLOY_T;
    if (tb < show.stow) return DEPLOY_T;
    const dt = tb - show.stow;
    if (dt < STOW_TEL_SEC) return STOW_T0 + (dt / STOW_TEL_SEC) * (STOW_TEL_T1 - STOW_T0);
    const u = Math.min(1, (dt - STOW_TEL_SEC) / STOW_SLIDE_SEC);
    return STOW_TEL_T1 + u * (CLIP_END - STOW_TEL_T1);
  }
  function doorAt(tb, show) {
    let k = 1;
    if (tb < show.deploy) k = Math.max(0, (tb - (show.deploy - DOOR_SEC)) / DOOR_SEC);
    else if (tb >= show.close) k = 1 - Math.min(1, (tb - show.close) / DOOR_SEC);
    return k;
  }
  function applyDoor(k) {
    const d = A.doors; if (!d) return;
    const oz = (d.outer.userData && d.outer.userData.baseZ) || 0;
    d.outer.position.set(OPEN_OUTER.x * k, 0, OPEN_OUTER.z * k + oz);
    d.inner.position.set(OPEN_INNER.x * k, 0, OPEN_INNER.z * k);
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
    const ct = Math.min(CLIP_END - 1e-4, Math.max(0, clipAt(tb, show)));
    A.act.time = ct;
    A.mixer.update(0);
    applyDoor(doorAt(tb, show));
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
    return { clip: ct, door: doorAt(tb, show), info, show };
  }

  function bind(hullG, accG, hullNode, hide) {
    const proposal = hullG.scene.getObjectByName('Study_1720_Hull_Channel_PROPOSAL');
    const asm = accG.scene.getObjectByName('Assembly_1720_SPLIT');
    const rails = accG.scene.getObjectByName('RailsMoving');
    const clip = (accG.animations || []).find((c) => c.name === 'Animation');
    if (!proposal || !asm || !rails || !clip || !(rails.morphTargetInfluences && rails.morphTargetInfluences.length >= 159)) {
      throw new Error('access 1720 nodes missing');
    }
    for (const scene of [hullG.scene, accG.scene]) {
      scene.position.set(0, 0, 0); scene.quaternion.identity(); scene.scale.set(1, 1, 1);
      scene.traverse((m) => { if (m.isMesh) { m.castShadow = m.receiveShadow = true; m.frustumCulled = false; } });
      hullNode.add(scene);
    }
    for (const o of hide) if (o) { o.visible = false; A.old.push(o); }
    const mixer = new THREE.AnimationMixer(accG.scene);
    const act = mixer.clipAction(clip);
    act.play(); act.paused = true; act.clampWhenFinished = true;
    act.time = DEPLOY_T; mixer.update(0); accG.scene.updateMatrixWorld(true);
    const rungs = [];
    // Rungs from each stage's geometry, transformed by the deployed world matrix into ship space.
    const inv = new THREE.Matrix4().copy(hullNode.matrixWorld).invert();
    for (let s = 0; s < 6; s++) {
      const stage = accG.scene.getObjectByName('LadderStage_' + s);
      const mesh = stage.isMesh ? stage : null;
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
    act.time = 0; mixer.update(0);
    A.rungs = rungs;
    A.outward = outwardOf(rungs[Math.floor(rungs.length / 2)]);
    A.show = showTimes(4, rungs, 6);
    A.mixer = mixer; A.act = act; A.root = asm;
    A.doors = {
      outer: accG.scene.getObjectByName('Study_1146_Access_OuterDoor'),
      inner: accG.scene.getObjectByName('Study_1146_Access_InnerDoor'),
    };
    if (A.doors.outer) A.doors.outer.userData.baseZ = 0.10;
    const white = new THREE.MeshStandardMaterial({ color: 0xf3f6fa, metalness: 0.22, roughness: 0.16 });
    for (const name of ['Study_1146_Access_Chamber', 'Study_1146_Access_Corridor']) {
      const mesh = accG.scene.getObjectByName(name);
      if (mesh) { mesh.material = white; mesh.castShadow = false; }
    }
    const hatchMat = new THREE.MeshStandardMaterial({ color: 0xb7c0c8, metalness: 0.4, roughness: 0.3 });
    for (const name of ['Study_1146_Access_InnerDoor', 'Study_1146_Access_OuterDoor', 'Study_1146_Access_PressureFrame']) {
      const mesh = accG.scene.getObjectByName(name);
      if (mesh) mesh.material = hatchMat;
    }
    const stripMat = new THREE.MeshStandardMaterial({ color: 0x9aefff, emissive: 0x2ad0ff, emissiveIntensity: 1.8, roughness: 0.35, metalness: 0.05 });
    const stripBoxes = [
      { x: -0.62, y: 30.62, z: 2.75, sx: 0.045, sy: 0.03, sz: 1.7 },
      { x: 0.62, y: 30.62, z: 2.75, sx: 0.045, sy: 0.03, sz: 1.7 },
      { x: -0.50, y: 30.60, z: 0.78, sx: 0.045, sy: 0.03, sz: 1.2 },
      { x: 0.50, y: 30.60, z: 0.78, sx: 0.045, sy: 0.03, sz: 1.2 },
      { x: -0.62, y: 29.65, z: 3.68, sx: 0.04, sy: 1.9, sz: 0.035 },
      { x: 0.62, y: 29.65, z: 3.68, sx: 0.04, sy: 1.9, sz: 0.035 },
    ];
    const stripIM = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), stripMat, stripBoxes.length);
    stripIM.name = 'Access_Airlock_Strips';
    stripIM.frustumCulled = false;
    const dummy = new THREE.Object3D();
    for (let i = 0; i < stripBoxes.length; i++) {
      const s = stripBoxes[i];
      dummy.position.set(s.x, s.y, s.z);
      dummy.scale.set(s.sx, s.sy, s.sz);
      dummy.updateMatrix();
      stripIM.setMatrixAt(i, dummy.matrix);
    }
    stripIM.instanceMatrix.needsUpdate = true;
    (accG.scene.getObjectByName('Study_1146_Root') || accG.scene).add(stripIM);
    const out = A.outward;
    const side = { x: out.z, y: 0, z: -out.x };
    const bay = new THREE.Group();
    bay.name = 'LadderBay_1720';
    bay.position.set(-1.419532, 28.52, 4.950498);
    bay.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(
      new THREE.Vector3(side.x, 0, side.z),
      new THREE.Vector3(0, 1, 0),
      new THREE.Vector3(out.x, 0, out.z),
    ));
    const dark = new THREE.MeshStandardMaterial({ color: 0x14161a, metalness: 0.15, roughness: 0.85 });
    let hullMat = null;
    hullG.scene.traverse((m) => { if (!hullMat && m.isMesh && m.material) hullMat = m.material; });
    const lipMat = hullMat ? hullMat.clone() : new THREE.MeshStandardMaterial({ color: 0x6b7380, metalness: 0.45, roughness: 0.48 });
    const unit = new THREE.BoxGeometry(1, 1, 1);
    const fillIM = (im, boxes) => {
      const d2 = new THREE.Object3D();
      for (let i = 0; i < boxes.length; i++) {
        const b = boxes[i];
        d2.position.set(b[0], b[1], b[2]);
        d2.scale.set(b[3], b[4], b[5]);
        d2.updateMatrix();
        im.setMatrixAt(i, d2.matrix);
      }
      im.instanceMatrix.needsUpdate = true;
      im.frustumCulled = false;
      return im;
    };
    const interior = [
      [0, -2.50, -0.34, 0.76, 5.10, 0.04],
      [-0.38, -2.50, -0.16, 0.04, 5.10, 0.40],
      [0.38, -2.50, -0.16, 0.04, 5.10, 0.40],
      [0, 0.06, -0.16, 0.80, 0.06, 0.40],
    ];
    const lips = [
      [-0.42, -2.50, 0.06, 0.06, 5.14, 0.08],
      [0.42, -2.50, 0.06, 0.06, 5.14, 0.08],
      [0, 0.10, 0.06, 0.90, 0.08, 0.08],
      [0, -5.08, 0.02, 0.90, 0.06, 0.16],
    ];
    const imDark = fillIM(new THREE.InstancedMesh(unit, dark, interior.length), interior);
    const imLip = fillIM(new THREE.InstancedMesh(unit, lipMat, lips.length), lips);
    imDark.name = 'LadderBay_Interior';
    imLip.name = 'LadderBay_Lip';
    bay.add(imDark, imLip);
    accG.scene.add(bay);
    if (proposal && proposal.geometry && proposal.geometry.index && proposal.geometry.attributes.position) {
      const pos = proposal.geometry.attributes.position;
      const src = proposal.geometry.index;
      const keep = [];
      for (let t = 0; t < src.count; t += 3) {
        const ia = src.getX(t), ib = src.getX(t + 1), ic = src.getX(t + 2);
        const cx = (pos.getX(ia) + pos.getX(ib) + pos.getX(ic)) / 3;
        const cy = (pos.getY(ia) + pos.getY(ib) + pos.getY(ic)) / 3;
        const cz = (pos.getZ(ia) + pos.getZ(ib) + pos.getZ(ic)) / 3;
        if (cx >= -0.50 && cx <= 0.50 && cy >= 28.78 && cy <= 30.50 && cz >= 3.90 && cz <= 4.15) continue;
        keep.push(ia, ib, ic);
      }
      proposal.geometry.setIndex(keep);
      proposal.geometry.computeVertexNormals();
      const mats = proposal.material ? [].concat(proposal.material) : [];
      for (const mat of mats) {
        if (!mat) continue;
        mat.polygonOffset = true;
        mat.polygonOffsetFactor = 1;
        mat.polygonOffsetUnits = 1;
      }
    }
    applyDoor(0);
    A.ready = true;
    A.morph = true;
    return { rungs: rungs.length, climb: +climbDur(rungs).toFixed(3), launch4: +A.show.launch.toFixed(3) };
  }

  return { A, tick, bind, clipAt, doorAt };
}
