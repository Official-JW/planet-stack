// Scene side of the PR17 crew access (1015 bay/airlock packet). Timing and IK live in access1720.mjs.
import {
  nominalRungs, showTimes, poseShow, poseStand, outwardOf, stageRungLocals, climbDur, faceYaw,
  DEPLOY_T, BAY_DOOR_SEC, LADDER_DEPLOY_SEC, LADDER_STOW_SEC, ENTRY_DOOR_SEC,
} from './access1720.mjs';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export const HULL_URL = '../qa3d-next/models/pr17_hull_bay_1015_ee26cbd9.glb?v=ee26cbd9';
// 1015 ladder + bay door (no airlock room — that is AIRLOCK_URL).
export const ACCESS_URL = '../qa3d-next/models/pr17_access_assembly_1015_7dc4c876.glb?v=7dc4c876';
// Single swap point for the crew airlock room + entry door (1123 4-crew packet).
export const AIRLOCK_URL = '../qa3d-next/models/pr17_airlock4_assembly_1123_b1b1cad0.glb?v=b1b1cad0';

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
    const acts = A.acts; if (!acts) return { clip: 0, door: 0, entry: 0 };
    const set = (act, t, dur) => {
      if (!act) return;
      act.enabled = true;
      act.paused = true;
      act.time = Math.max(0, Math.min(dur - 1e-4, t));
      act.setEffectiveWeight(1);
    };
    const zero = (act) => { if (act) { act.time = 0; act.setEffectiveWeight(0); } };

    // BayDoor: open 0..1, hold until show.stow, then close.
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

    // Ladder: deploy after bay open; hold through climb + entry close; stow after entryClosed.
    let clipT = 0;
    const stowStart = show.entryClosed != null ? show.entryClosed : show.close;
    if (tb < BAY_DOOR_SEC) {
      set(acts.deploy, 0, LADDER_DEPLOY_SEC);
      zero(acts.stow);
      clipT = 0;
    } else if (tb < show.deploy) {
      const lt = tb - BAY_DOOR_SEC;
      set(acts.deploy, lt, LADDER_DEPLOY_SEC);
      zero(acts.stow);
      clipT = lt;
    } else if (tb < stowStart) {
      set(acts.deploy, LADDER_DEPLOY_SEC - 1e-4, LADDER_DEPLOY_SEC);
      zero(acts.stow);
      clipT = LADDER_DEPLOY_SEC;
    } else if (tb < show.stow) {
      const lt = tb - stowStart;
      zero(acts.deploy);
      set(acts.stow, lt, LADDER_STOW_SEC);
      clipT = LADDER_DEPLOY_SEC + lt;
    } else {
      zero(acts.deploy);
      set(acts.stow, LADDER_STOW_SEC - 1e-4, LADDER_STOW_SEC);
      clipT = LADDER_DEPLOY_SEC + LADDER_STOW_SEC;
    }

    // EntryDoor (1123): open after ladder deploy; hold open through climb; close after last inside.
    let entryK = 0;
    if (acts.entryOpen && acts.entryClose) {
      if (tb < show.deploy) {
        set(acts.entryOpen, 0, ENTRY_DOOR_SEC);
        zero(acts.entryClose);
        entryK = 0;
      } else if (tb < show.entryOpen) {
        const et = tb - show.deploy;
        set(acts.entryOpen, et, ENTRY_DOOR_SEC);
        zero(acts.entryClose);
        entryK = Math.max(0, Math.min(1, et / ENTRY_DOOR_SEC));
      } else if (tb < show.close) {
        set(acts.entryOpen, ENTRY_DOOR_SEC - 1e-4, ENTRY_DOOR_SEC);
        zero(acts.entryClose);
        entryK = 1;
      } else if (tb < show.entryClosed) {
        const et = tb - show.close;
        zero(acts.entryOpen);
        set(acts.entryClose, et, ENTRY_DOOR_SEC);
        entryK = 1 - Math.max(0, Math.min(1, et / ENTRY_DOOR_SEC));
      } else {
        zero(acts.entryOpen);
        set(acts.entryClose, ENTRY_DOOR_SEC - 1e-4, ENTRY_DOOR_SEC);
        entryK = 0;
      }
    }

    A.mixer.update(0);
    if (A.airMixer) A.airMixer.update(0);
    if (A._syncStages) A._syncStages();
    if (A._syncDoors) A._syncDoors();
    return { clip: clipT, door: doorK, entry: entryK };
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
    // Snap everyone into final airlock slots before EntryDoor_Close — no walk into cam.
    const parkAll = tb >= show.close - 0.15;
    people.forEach((person, i) => {
      const slot = show.finish[i];
      if (!slot) return;
      const tau = tb - slot.start;
      person.mode = 'wait';
      person.outside = false;
      if (parkAll && person.obj) {
        person.mode = 'inside';
        person.outside = false;
        person.obj.visible = true;
        if (!person._airSlot) {
          // Line toward entry; cam (-1.25, 2.45) keeps ≥0.6 m to suit AABB.
          const xs = [-0.70, -0.10, 0.50, 1.15];
          const zs = [3.20, 3.30, 3.30, 3.20];
          person._airSlot = { x: xs[i] ?? 0, y: 28.90, z: zs[i] ?? 3.25 };
        }
        person.obj.position.set(person._airSlot.x, person._airSlot.y, person._airSlot.z);
        return;
      }
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
      if (tau > show.per + 0.05) {
        // Park at final airlock spots before EntryDoor_Close (keep last enter pose — no re-IK).
        person.mode = 'inside';
        person.outside = false;
        person.obj.visible = true;
        if (!person._airSlot) {
          // Line toward entry; cam (-1.25, 2.45) keeps ≥0.6 m to suit AABB.
          const xs = [-0.70, -0.10, 0.50, 1.15];
          const zs = [3.20, 3.30, 3.30, 3.20];
          person._airSlot = { x: xs[i] ?? 0, y: 28.90, z: zs[i] ?? 3.25 };
        }
        person.obj.position.set(person._airSlot.x, person._airSlot.y, person._airSlot.z);
        return;
      }
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
    return { clip: sync.clip, door: sync.door, entry: sync.entry, info, show };
  }

  // Bake mesh local matrix into geometry, return a clone ready to merge under parent.
  function bakeGeo(mesh, parent) {
    mesh.updateWorldMatrix(true, false);
    parent.updateWorldMatrix(true, false);
    const inv = new THREE.Matrix4().copy(parent.matrixWorld).invert();
    const local = new THREE.Matrix4().multiplyMatrices(inv, mesh.matrixWorld);
    const g = mesh.geometry.clone();
    g.applyMatrix4(local);
    return g;
  }

  // Merge sibling meshes that share a material into one draw. Morph-target meshes stay
  // under their animated parent; morph attributes are preserved when every sibling has them.
  function mergeUnder(parent, THREE, { oneMaterial = null, name = null } = {}) {
    const meshes = [];
    for (const c of parent.children.slice()) {
      if (c.isMesh) meshes.push(c);
      else c.traverse((o) => { if (o.isMesh && o.parent === c) meshes.push(o); });
    }
    // Prefer direct mesh children; if parent is a Group of mesh children (multi-prim), collect those.
    const direct = parent.children.filter((c) => c.isMesh);
    const list = direct.length ? direct : meshes.filter((m) => m.parent === parent);
    if (list.length < 2 && !oneMaterial) return 0;

    const groups = new Map();
    for (const m of list) {
      const mat = oneMaterial || (Array.isArray(m.material) ? m.material[0] : m.material);
      const key = oneMaterial ? '_one' : (mat && (mat.name || mat.uuid)) || '_';
      if (!groups.has(key)) groups.set(key, { mat: oneMaterial || mat, meshes: [] });
      groups.get(key).meshes.push(m);
    }
    let saved = 0;
    for (const { mat, meshes: ms } of groups.values()) {
      if (ms.length < 1) continue;
      if (ms.length === 1 && !oneMaterial) continue;
      const geos = [];
      let morphN = null;
      let morphDict = null;
      let relative = null;
      for (const m of ms) {
        const g = bakeGeo(m, parent);
        const nMorph = m.morphTargetInfluences ? m.morphTargetInfluences.length : 0;
        if (morphN == null) {
          morphN = nMorph;
          morphDict = m.morphTargetDictionary ? { ...m.morphTargetDictionary } : null;
          relative = g.morphTargetsRelative;
        } else if (nMorph !== morphN) {
          // Incompatible morph counts — leave this group alone.
          geos.length = 0;
          break;
        }
        geos.push(g.index ? g : g);
      }
      if (geos.length < 2 && !(oneMaterial && geos.length === 1 && ms.length > 1)) {
        for (const g of geos) g.dispose?.();
        continue;
      }
      // Normalize: toNonIndexed if mixed; mergeGeometries requires consistent indexing.
      const norm = geos.map((g) => (g.index ? g.toNonIndexed() : g));
      // Drop attributes that aren't shared (colors etc.) so merge succeeds.
      const shared = new Set(Object.keys(norm[0].attributes));
      for (const g of norm) {
        for (const k of Object.keys(g.attributes)) if (!shared.has(k)) shared.delete(k);
      }
      const keep = new Set(['position', 'normal']);
      if (shared.has('uv')) keep.add('uv');
      for (const g of norm) {
        for (const k of Object.keys(g.attributes)) if (!keep.has(k)) g.deleteAttribute(k);
        // morph attrs: keep position morphs only
        if (g.morphAttributes) {
          for (const k of Object.keys(g.morphAttributes)) {
            if (k !== 'position') delete g.morphAttributes[k];
          }
        }
      }
      const merged = mergeGeometries(norm, false);
      for (const g of norm) g.dispose?.();
      if (!merged) continue;
      const mesh = new THREE.Mesh(merged, mat);
      mesh.name = name || (ms[0].name + '_merged');
      mesh.frustumCulled = false;
      mesh.castShadow = false;
      mesh.receiveShadow = true;
      if (morphN > 0) {
        mesh.morphTargetInfluences = ms[0].morphTargetInfluences.slice();
        mesh.morphTargetDictionary = morphDict || ms[0].morphTargetDictionary;
      }
      for (const m of ms) {
        if (m.parent) m.parent.remove(m);
        m.geometry?.dispose?.();
        saved++;
      }
      parent.add(mesh);
      saved--; // net: N meshes → 1
    }
    return saved;
  }

  function mergeList(list, mat, parent, nm) {
    if (!list.length || !mat) return;
    for (const m of list) m.material = mat;
    const grp = new THREE.Group(); parent.add(grp);
    for (const m of list) grp.attach(m);
    mergeUnder(grp, THREE, { oneMaterial: mat, name: nm });
    for (const c of grp.children.slice()) parent.attach(c);
    parent.remove(grp);
  }

  function consolidateMaterial(root, mat, predicate) {
    const hits = [];
    root.traverse((o) => {
      if (!o.isMesh || !o.visible) return;
      if (predicate && !predicate(o)) return;
      hits.push(o);
    });
    for (const o of hits) o.material = mat;
    return hits;
  }

  function bind(hullG, accG, airG, hullNode, hide) {
    const hullRoot = hullG.scene.getObjectByName('PR17_Hull_Replacement');
    const asm = accG.scene.getObjectByName('PR17_Access_Assembly');
    const rails = accG.scene.getObjectByName('Rails');
    const clips = accG.animations || [];
    const cDeploy = findClip(clips, 'Ladder_Deploy');
    const cStow = findClip(clips, 'Ladder_Stow');
    const cDoorOpen = findClip(clips, 'BayDoor_Open');
    const cDoorClose = findClip(clips, 'BayDoor_Close');
    if (!hullRoot || !asm || !rails || !cDeploy || !cStow || !cDoorOpen || !cDoorClose) {
      throw new Error('access 1015 nodes/clips missing');
    }
    let railsMorph = (rails.morphTargetInfluences && rails.morphTargetInfluences.length >= 24) ? rails : null;
    if (!railsMorph) {
      rails.traverse((o) => {
        if (!railsMorph && o.morphTargetInfluences && o.morphTargetInfluences.length >= 24) railsMorph = o;
      });
    }
    if (!railsMorph) throw new Error('access 1015 rails morphs missing');

    for (const scene of [hullG.scene, accG.scene, airG && airG.scene].filter(Boolean)) {
      scene.position.set(0, 0, 0); scene.quaternion.identity(); scene.scale.set(1, 1, 1);
      // No castShadow on packet meshes — pad sun already has the ship; saves shadow-pass draws.
      scene.traverse((m) => { if (m.isMesh) { m.castShadow = false; m.receiveShadow = true; m.frustumCulled = false; } });
      hullNode.add(scene);
    }
    for (const o of hide) if (o) { o.visible = false; A.old.push(o); }
    // 1015 airlock room + deck replaced by 1123 airlock packet — hide leftovers.
    for (const n of [
      'Airlock_Corridor_White', 'Airlock_GlowStrips', 'Airlock_InnerHatch_Mount',
      'Study_1353_DeckThin', 'Deck_Root', 'DeckPack', 'DeckThin',
      'Airlock_Merged', 'Airlock_Glow', 'Airlock_Light', 'Airlock_Dark',
    ]) {
      const o = accG.scene.getObjectByName(n);
      if (o) { o.visible = false; A.old.push(o); }
    }
    // Also hide any leftover Airlock_* mesh children from 1015.
    accG.scene.traverse((o) => {
      if (o.isMesh && /^Airlock_/.test(o.name || '')) { o.visible = false; A.old.push(o); }
    });

    const mixer = new THREE.AnimationMixer(accG.scene);
    const acts = {
      deploy: makeAction(mixer, cDeploy),
      stow: makeAction(mixer, cStow),
      doorOpen: makeAction(mixer, cDoorOpen),
      doorClose: makeAction(mixer, cDoorClose),
      entryOpen: null,
      entryClose: null,
    };
    let airMixer = null;
    const airRoot = airG && airG.scene.getObjectByName('PR17_Airlock4_Assembly');
    if (!airRoot) throw new Error('access 1123 airlock root missing');
    airMixer = new THREE.AnimationMixer(airG.scene);
    const airClips = airG.animations || [];
    const cEntryOpen = findClip(airClips, 'EntryDoor_Open');
    const cEntryClose = findClip(airClips, 'EntryDoor_Close');
    if (!cEntryOpen || !cEntryClose) throw new Error('access 1123 EntryDoor clips missing');
    acts.entryOpen = makeAction(airMixer, cEntryOpen);
    acts.entryClose = makeAction(airMixer, cEntryClose);
    acts.entryOpen.time = 0; acts.entryOpen.setEffectiveWeight(0);
    acts.entryClose.time = 0; acts.entryClose.setEffectiveWeight(0);
    airMixer.update(0);
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
    // Live stage-mesh samples drifted below the pad after the 1015 InstancedMesh bind
    // (LadderStage_5 world y ≈ -23). Packet authority is nominalRungs (STAGE_Y 5..28),
    // which matches Rails_Merged AABB and the bay/airlock face at local z≈+5.
    {
      const nom = nominalRungs();
      if (nom.length >= 8) {
        if (nom.length !== rungs.length) console.warn('access rungs', rungs.length, '→ nominal', nom.length);
        rungs.length = 0;
        for (const r of nom) rungs.push({ x: r.x, y: r.y, z: r.z });
      }
    }

    acts.deploy.time = 0; acts.deploy.setEffectiveWeight(0);
    acts.doorOpen.time = 0; acts.doorOpen.setEffectiveWeight(0);
    mixer.update(0);

    // ---- Draw reduction: merge static meshes; instance animated ladder stages. ----
    // Shape-keyed Rails stay as one morph mesh. LadderStage_1..5 stay as animated nodes
    // but draw through one InstancedMesh (same geo, per-stage scale). BayDoor merges to one draw.

    const doorMat = (() => {
      const d = accG.scene.getObjectByName('BayDoor');
      let m = null;
      d?.traverse((o) => { if (!m && o.isMesh && o.material) m = Array.isArray(o.material) ? o.material[0] : o.material; });
      return m;
    })();
    const bayDoor = accG.scene.getObjectByName('BayDoor');
    if (bayDoor && doorMat) {
      bayDoor.traverse((o) => { if (o.isMesh) o.material = doorMat; });
      mergeUnder(bayDoor, THREE, { oneMaterial: doorMat, name: 'BayDoor_Merged' });
    }

    const railMat = (() => {
      let m = null;
      rails.traverse((o) => {
        if (!m && o.isMesh) {
          const mat = Array.isArray(o.material) ? o.material[0] : o.material;
          if (mat && /RAIL_C|POST_C/.test(mat.name || '')) m = mat;
        }
      });
      if (!m) rails.traverse((o) => { if (!m && o.isMesh) m = Array.isArray(o.material) ? o.material[0] : o.material; });
      return m;
    })();
    if (railMat) {
      rails.traverse((o) => { if (o.isMesh) o.material = railMat; });
      mergeUnder(rails, THREE, { oneMaterial: railMat, name: 'Rails_Merged' });
    }

    // 1123 airlock: merge static room to 1 body + 1 glow; each entry leaf → 1 draw (animated).
    {
      const body = [], glow = [], doorL = [], doorR = [];
      airG.scene.traverse((o) => {
        if (!o.isMesh) return;
        let underL = false, underR = false, x = o;
        while (x) {
          if (x.name === 'EntryDoor_L') underL = true;
          if (x.name === 'EntryDoor_R') underR = true;
          x = x.parent;
        }
        const mn = (Array.isArray(o.material) ? o.material[0] : o.material)?.name || '';
        if (underL) doorL.push(o);
        else if (underR) doorR.push(o);
        else if (/Glow/.test(mn) || /Glow/.test(o.name || '')) glow.push(o);
        else body.push(o);
      });
      const bodyMat = (body[0] && (Array.isArray(body[0].material) ? body[0].material[0] : body[0].material)) || null;
      const glowMat = (glow[0] && (Array.isArray(glow[0].material) ? glow[0].material[0] : glow[0].material)) || null;
      const doorMat = (() => {
        const src = doorL[0] || doorR[0];
        return src ? (Array.isArray(src.material) ? src.material[0] : src.material) : null;
      })();
      mergeList(body, bodyMat, airRoot, 'Airlock4_Body');
      mergeList(glow, glowMat, airRoot, 'Airlock4_Glow');
      {
        const ab = airRoot.getObjectByName('Airlock4_Body');
        if (ab && ab.material) {
          ab.material.color.setHex(0xf4f7fa);
          ab.material.emissive.setHex(0xd8dde3);
          ab.material.emissiveIntensity = 0.35;
          ab.material.metalness = 0;
          ab.material.roughness = 0.62;
          ab.material.needsUpdate = true;
        }
      }
      const leafL = airG.scene.getObjectByName('EntryDoor_L');
      const leafR = airG.scene.getObjectByName('EntryDoor_R');
      if (leafL && doorMat) mergeList(doorL, doorMat, leafL, 'EntryDoor_L_Merged');
      if (leafR && doorMat) mergeList(doorR, doorMat, leafR, 'EntryDoor_R_Merged');
      // One InstancedMesh for both entry leaves (nodes keep EntryDoor_* translations).
      if (leafL && leafR && doorMat) {
        const src = leafL.getObjectByName('EntryDoor_L_Merged') || leafL.children.find((c) => c.isMesh);
        if (src && src.isMesh) {
          const im = new THREE.InstancedMesh(src.geometry.clone(), doorMat, 2);
          im.name = 'EntryDoors_IM';
          im.frustumCulled = false;
          im.castShadow = false;
          im.receiveShadow = true;
          airRoot.add(im);
          const dummy = new THREE.Object3D();
          const leaves = [leafL, leafR];
          for (const leaf of leaves) leaf.traverse((o) => { if (o.isMesh) o.visible = false; });
          const syncDoors = () => {
            airRoot.updateWorldMatrix(true, false);
            const inv = new THREE.Matrix4().copy(airRoot.matrixWorld).invert();
            for (let i = 0; i < 2; i++) {
              leaves[i].updateWorldMatrix(true, false);
              const local = new THREE.Matrix4().multiplyMatrices(inv, leaves[i].matrixWorld);
              im.setMatrixAt(i, local);
            }
            im.instanceMatrix.needsUpdate = true;
          };
          syncDoors();
          A._syncDoors = syncDoors;
        }
      }
      // Cheap interior fill so white panels read without a bloom pass (boosted for inside cam).
      const fill = new THREE.PointLight(0xf7fbff, 2.6, 11, 1.6);
      fill.name = 'Access_Airlock_Fill';
      fill.position.set(0, 29.55, 1.35);
      airRoot.add(fill);
      const fill2 = new THREE.PointLight(0xffffff, 1.1, 7, 2);
      fill2.name = 'Access_Airlock_Fill2';
      fill2.position.set(0.0, 28.9, 0.4);
      airRoot.add(fill2);
    }

    // Hull: stainless body + bay liner + glow (3 draws max).
    // Prefer SHM_Stainless_* (off-white vertex panels per A&A stills). First-hit was
    // Study1240_Rebate, which + metalness and no envMap reads solid black on device.
    let hullBody = null, hullLiner = null, hullGlow = null, hullStainless = null;
    hullRoot.traverse((o) => {
      if (!o.isMesh) return;
      const mat = Array.isArray(o.material) ? o.material[0] : o.material;
      const mn = mat?.name || '';
      if (/Glow/.test(mn)) hullGlow = hullGlow || mat;
      else if (/BayLiner|Track_Metal/.test(mn)) hullLiner = hullLiner || mat;
      else if (/SHM_Stainless|Stainless/i.test(mn)) hullStainless = hullStainless || mat;
      else hullBody = hullBody || mat;
    });
    hullBody = hullStainless || hullBody;
    const hullLists = { body: [], liner: [], glow: [] };
    hullRoot.traverse((o) => {
      if (!o.isMesh) return;
      const mat = Array.isArray(o.material) ? o.material[0] : o.material;
      const mn = mat?.name || '';
      if (/Glow/.test(mn)) hullLists.glow.push(o);
      else if (/BayLiner|Track_Metal/.test(mn)) hullLists.liner.push(o);
      else hullLists.body.push(o);
    });
    // One hull draw: body + bay liner share the panel material (saves a draw).
    const hullAll = hullLists.body.concat(hullLists.liner);
    mergeList(hullAll, hullBody || hullLiner, hullRoot, 'Hull_Body');
    mergeList(hullLists.glow, hullGlow, hullRoot, 'Hull_Glow');
    // Force A&A off-white panel look on served + replacement hull (pad/launch/zoom).
    // Material/lighting only — no geo change. Served SHM_Stainless is metalness 0.5 with no
    // envMap (reads solid black); dark COLOR_0 also crushes. Drop vertexColors so baseColor wins.
    function retintHullPanels(root) {
      if (!root) return;
      root.traverse((o) => {
        if (!o.isMesh) return;
        for (const m of [].concat(o.material || [])) {
          if (!m || !m.isMeshStandardMaterial) continue;
          const n = m.name || '';
          if (/Glow|Glass|Plume|Window|BayDoor|EntryDoor|LAD_|POST_|RAIL|Airlock_Panel/i.test(n)) continue;
          if (!(/SHM_Stainless|Stainless|Hull_Body|M_AftSkirt|Study1240|Study1353/i.test(n))) continue;
          m.color.setHex(0xe8e6df);
          m.metalness = 0.12;
          m.roughness = 0.58;
          m.envMapIntensity = 0.4;
          m.emissive.setHex(0x222220);
          m.emissiveIntensity = 0.22;
          m.vertexColors = false;
          m.needsUpdate = true;
        }
      });
    }
    retintHullPanels(hullRoot);
    retintHullPanels(hullNode);
    A._retintHullPanels = retintHullPanels;

    // One shared cyan glow draw (hull bay strips + airlock strips).
    {
      const glows = [];
      for (const root of [hullRoot, airRoot, asm]) {
        root.traverse((o) => {
          if (!o.isMesh || !o.visible) return;
          const mn = (Array.isArray(o.material) ? o.material[0] : o.material)?.name || '';
          if (/Glow/.test(mn) || /Glow/.test(o.name || '')) glows.push(o);
        });
      }
      if (glows.length) {
        const mat = Array.isArray(glows[0].material) ? glows[0].material[0] : glows[0].material;
        mergeList(glows, mat, airRoot, 'Access_Glow');
      }
    }

    // PackRoot: DeckThin already hidden. Sleeve is tiny — hide it. Stages 0..5 → one InstancedMesh.
    const pack = accG.scene.getObjectByName('PackRoot');
    if (pack) {
      pack.traverse((o) => {
        if (!o.isMesh) return;
        if (o.name === 'Ladder_Sleeve' || /Sleeve/.test(o.name || '')) o.visible = false;
      });
      // Radii mm: stage0..5 = 28/24/20/16/12/8; instance geo = stage1 (24 mm).
      const stageScales = [28, 24, 20, 16, 12, 8].map((r) => r / 24);
      const stageNodes = [];
      for (let s = 0; s <= 5; s++) {
        const node = accG.scene.getObjectByName('LadderStage_' + s);
        if (node) stageNodes.push(node);
      }
      if (stageNodes.length === 6) {
        const srcMesh = stageMesh(stageNodes[1] || stageNodes[0]);
        if (srcMesh) {
          const geo = srcMesh.geometry.clone();
          const mat = Array.isArray(srcMesh.material) ? srcMesh.material[0].clone() : srcMesh.material.clone();
          const im = new THREE.InstancedMesh(geo, mat, 6);
          im.name = 'LadderStages_IM';
          im.frustumCulled = false;
          im.castShadow = false;
          im.receiveShadow = true;
          pack.add(im);
          const dummy = new THREE.Object3D();
          const syncStages = () => {
            pack.updateWorldMatrix(true, false);
            const invP = new THREE.Matrix4().copy(pack.matrixWorld).invert();
            for (let i = 0; i < 6; i++) {
              const node = stageNodes[i];
              node.updateWorldMatrix(true, false);
              const local = new THREE.Matrix4().multiplyMatrices(invP, node.matrixWorld);
              local.decompose(dummy.position, dummy.quaternion, dummy.scale);
              const s = stageScales[i];
              dummy.scale.x *= s; dummy.scale.z *= s;
              dummy.updateMatrix();
              im.setMatrixAt(i, dummy.matrix);
            }
            im.instanceMatrix.needsUpdate = true;
          };
          for (const node of stageNodes) node.traverse((o) => { if (o.isMesh) o.visible = false; });
          syncStages();
          A._syncStages = syncStages;
          A._stageIM = im;
        }
      }
    }

    A.rungs = rungs;
    A.outward = outwardOf(rungs[Math.floor(rungs.length / 2)]);
    A.show = showTimes(4, rungs, 6);
    A.mixer = mixer;
    A.airMixer = airMixer;
    A.acts = acts;
    A.root = asm;
    A.airRoot = airRoot;
    A.ready = true;
    A.morph = true;
    return { rungs: rungs.length, climb: +climbDur(rungs).toFixed(3), launch4: +A.show.launch.toFixed(3) };
  }

  return { A, tick, bind, syncClips };
}
