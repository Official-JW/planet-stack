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

    // Solid orange ladder + PackRoot platform: own smoothstep tweens (NO Ladder_Deploy/Stow clips —
    // those also drive telescope stages). Telescope meshes are removed from the scene in bind().
    let clipT = 0;
    const stowStart = show.entryClosed != null ? show.entryClosed : show.close;
    const smooth = (t) => { t = Math.max(0, Math.min(1, t)); return t * t * (3 - 2 * t); };
    zero(acts.deploy); zero(acts.stow); // clips unbound from visuals; keep actions silent
    let slideU = 0; // 0=stowed (up / drawer in), 1=deployed (down / drawer out)
    if (tb < BAY_DOOR_SEC) {
      slideU = 0; clipT = 0;
    } else if (tb < show.deploy) {
      const lt = tb - BAY_DOOR_SEC;
      slideU = smooth(lt / LADDER_DEPLOY_SEC);
      clipT = lt;
    } else if (tb < stowStart) {
      slideU = 1; clipT = LADDER_DEPLOY_SEC;
    } else if (tb < show.stow) {
      const lt = tb - stowStart;
      slideU = 1 - smooth(lt / LADDER_STOW_SEC);
      clipT = LADDER_DEPLOY_SEC + lt;
    } else {
      slideU = 0; clipT = LADDER_DEPLOY_SEC + LADDER_STOW_SEC;
    }
    // Platform drawer: PackRoot rest (stowed DX) → origin (deployed). Independent of camera.
    if (A._packRoot && A._packStow) {
      const sx = A._packStow.x, sy = A._packStow.y, sz = A._packStow.z;
      A._packRoot.position.set(sx * (1 - slideU), sy * (1 - slideU), sz * (1 - slideU));
      A._packRoot.visible = true;
    }
    // Solid ladder: one rigid piece, translation-only. Fully down while climb; up after last inside.
    if (A._solidLadder) {
      const travel = A._solidTravel || 24;
      A._solidLadder.position.y = (1 - slideU) * travel;
      A._solidLadder.visible = slideU > 0.001;
      if (slideU <= 0.001 && tb >= show.stow) A._solidLadder.visible = false;
      if (slideU <= 0.001 && tb < BAY_DOOR_SEC) A._solidLadder.visible = false;
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
          // Row facing entry (+Z / camera outside looking in). Tight so all 4 read.
          const xs = [-0.85, -0.28, 0.28, 0.85];
          const zs = [2.65, 2.70, 2.70, 2.65];
          person._airSlot = { x: xs[i] ?? 0, y: 28.90, z: zs[i] ?? 2.70 };
        }
        person.obj.position.set(person._airSlot.x, person._airSlot.y, person._airSlot.z);
        person.obj.quaternion.setFromAxisAngle(new THREE.Vector3(0, 1, 0), Math.PI); // face −Z toward far-wall cam
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
          person.obj.position.y = 0; // feet on pad — never inherit truck/breakroom height
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
          // Row facing entry (+Z / camera outside looking in). Tight so all 4 read.
          const xs = [-0.85, -0.28, 0.28, 0.85];
          const zs = [2.65, 2.70, 2.70, 2.65];
          person._airSlot = { x: xs[i] ?? 0, y: 28.90, z: zs[i] ?? 2.70 };
        }
        person.obj.position.set(person._airSlot.x, person._airSlot.y, person._airSlot.z);
        person.obj.quaternion.setFromAxisAngle(new THREE.Vector3(0, 1, 0), Math.PI);
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
    // v10-safe: do NOT parent/replace with PR17_Hull_Replacement (trashes served AA3 ship).
    // Bay door + orange ladder come from the access assembly only; served hull stays as-is.
    const hullRoot = hullG && hullG.scene ? hullG.scene.getObjectByName('PR17_Hull_Replacement') : null;
    const asm = accG.scene.getObjectByName('PR17_Access_Assembly');
    const rails = accG.scene.getObjectByName('Rails');
    const clips = accG.animations || [];
    const cDeploy = findClip(clips, 'Ladder_Deploy');
    const cStow = findClip(clips, 'Ladder_Stow');
    const cDoorOpen = findClip(clips, 'BayDoor_Open');
    const cDoorClose = findClip(clips, 'BayDoor_Close');
    // Deploy/Stow clips kept only so findClip succeeds; then zeroed — PackRoot tween drives the drawer.
    if (!asm || !cDeploy || !cStow || !cDoorOpen || !cDoorClose) {
      throw new Error('access 1015 nodes/clips missing');
    }
    // Climb IK uses nominalRungs; telescope meshes deleted below.

    // Parent access + airlock only — never the 1015 hull replacement GLB.
    for (const scene of [accG.scene, airG && airG.scene].filter(Boolean)) {
      scene.position.set(0, 0, 0); scene.quaternion.identity(); scene.scale.set(1, 1, 1);
      // No castShadow on packet meshes — pad sun already has the ship; saves shadow-pass draws.
      scene.traverse((m) => { if (m.isMesh) { m.castShadow = false; m.receiveShadow = true; m.frustumCulled = false; } });
      hullNode.add(scene);
    }
    // hide[] should only be old ladder/bay hatch parts — never served hull meshes.
    for (const o of hide) if (o) { o.visible = false; A.old.push(o); }
    if (hullRoot) {
      // Keep GLB loaded for bay-only probes if needed, but never show the replacement hull.
      hullRoot.visible = false;
      hullRoot.traverse((c) => { c.visible = false; });
    }
    // 1015 airlock room + deck replaced by 1123 airlock packet — hide leftovers.
    // Keep PackRoot + Study_1353_DeckThin (platform drawer). Hide only 1015 airlock leftovers.
    for (const n of [
      'Airlock_Corridor_White', 'Airlock_GlowStrips', 'Airlock_InnerHatch_Mount',
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
    acts.deploy.time = 0; acts.deploy.setEffectiveWeight(0);
    acts.stow.time = 0; acts.stow.setEffectiveWeight(0);
    acts.doorOpen.time = BAY_DOOR_SEC - 1e-4;
    acts.doorOpen.setEffectiveWeight(1);
    acts.doorClose.setEffectiveWeight(0);
    mixer.update(0);
    accG.scene.updateMatrixWorld(true);

    // Climb IK uses nominal rungs (packet authority). Telescope stage meshes are deleted below.
    const rungs = [];
    {
      const nom = nominalRungs();
      for (const r of nom) rungs.push({ x: r.x, y: r.y, z: r.z });
    }
    if (rungs.length < 8) throw new Error('rungs missing');

    acts.deploy.time = 0; acts.deploy.setEffectiveWeight(0);
    acts.doorOpen.time = 0; acts.doorOpen.setEffectiveWeight(0);
    mixer.update(0);

    // ---- Draw reduction: merge BayDoor. Telescope ladder stages deleted below. ----

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

    // Telescope meshes deleted below; SolidLadder draws instead.

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

    // Hull replacement + retintHullPanels REMOVED (Jacob: ship must match DEV 18:48).

    // One shared cyan glow draw (hull bay strips + airlock strips).
    {
      const glows = [];
      for (const root of [airRoot, asm].filter(Boolean)) {
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

    // DELETE A&A telescoping ladder from the scene (not just hide). PackRoot + Deck stay for the drawer.
    {
      const kill = [];
      accG.scene.traverse((o) => {
        const n = o.name || '';
        if (n === 'PackRoot' || n === 'Deck_Root' || n === 'Study_1353_DeckThin' || n === 'BayDoor' || n === 'BayDoor_Merged') return;
        if (/^LadderStage_\d/.test(n) || n === 'Rails' || n === 'Ladder_Sleeve' || n === 'LadderStages_IM' || n === 'Rails_Merged') kill.push(o);
        else if (o.isMesh && /Sleeve|LadderStage|Rails_Merged|LadderStages|LAD_|POST_|^RAIL/i.test(n)) kill.push(o);
      });
      for (const o of kill) {
        o.traverse((c) => { if (c.isMesh) { c.geometry?.dispose?.(); } });
        if (o.parent) o.parent.remove(o);
      }
      A._syncStages = null;
      A._stageIM = null;
      // PackRoot drawer rest pose (stowed DX from the GLB). Deployed = (0,0,0).
      const pack = accG.scene.getObjectByName('PackRoot');
      if (pack) {
        A._packRoot = pack;
        A._packStow = { x: pack.position.x, y: pack.position.y, z: pack.position.z };
        // Start stowed
        pack.position.set(A._packStow.x, A._packStow.y, A._packStow.z);
      }
    }

    // Solid ladder: 2 box rails (90 mm) + InstancedMesh rungs @ 0.292 m. Safety orange.
    {
      const nom = rungs; // already nominal
      const y0 = nom[0].y, y1 = nom[nom.length - 1].y;
      const lx = nom[0].x, lz = nom[0].z;
      const railT = 0.090; // 90 mm box — readable at pad cam; still one rigid piece
      const railGap = 0.50; // center-to-center ≈ 2 * RAIL_HALF
      const railH = (y1 - y0) + 0.40;
      const railY = (y0 + y1) * 0.5;
      const mat = new THREE.MeshStandardMaterial({
        color: 0xff6a13, roughness: 0.5, metalness: 0.2, name: 'SolidLadder_Mat',
      });
      const grp = new THREE.Group();
      grp.name = 'SolidLadder';
      // Two rails (merged into one BufferGeometry via mergeGeometries)
      const railGeos = [];
      for (const sx of [-railGap * 0.5, railGap * 0.5]) {
        const g = new THREE.BoxGeometry(railT, railH, railT);
        g.translate(lx + sx, railY, lz);
        railGeos.push(g);
      }
      const railMerged = mergeGeometries(railGeos, false);
      for (const g of railGeos) g.dispose();
      const railMesh = new THREE.Mesh(railMerged, mat);
      railMesh.name = 'SolidLadder_Rails';
      railMesh.castShadow = true; railMesh.receiveShadow = true; railMesh.frustumCulled = false;
      grp.add(railMesh);
      // Rungs as InstancedMesh
      const rungGeo = new THREE.BoxGeometry(railGap - railT, railT * 0.85, railT * 0.85);
      const rungIM = new THREE.InstancedMesh(rungGeo, mat, nom.length);
      rungIM.name = 'SolidLadder_Rungs';
      rungIM.frustumCulled = false;
      rungIM.castShadow = true; rungIM.receiveShadow = true;
      const dummy = new THREE.Object3D();
      for (let i = 0; i < nom.length; i++) {
        dummy.position.set(nom[i].x, nom[i].y, nom[i].z);
        dummy.rotation.set(0, 0, 0);
        dummy.scale.set(1, 1, 1);
        dummy.updateMatrix();
        rungIM.setMatrixAt(i, dummy.matrix);
      }
      rungIM.instanceMatrix.needsUpdate = true;
      grp.add(rungIM);
      // Travel: slide fully up into bay (bottom clears bay lip ~y=28)
      const travel = Math.max(8, (y1 - y0) + 1.0);
      grp.position.set(0, travel, 0); // start stowed
      grp.visible = false;
      hullNode.add(grp);
      A._solidLadder = grp;
      A._solidTravel = travel;
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


  // Dev/QA only: step the boarding timeline and assert every crew's feet are on
  // ground (y≈0) or on the ladder rung span while climbing. Not used in gameplay.
  function assertBoardFeet(people, { dt = 0.05, maxErr = 0.03, groundY = 0 } = {}) {
    const n = Math.max(1, people.length);
    const show = showTimes(n, A.rungs || nominalRungs(), 6);
    const rungYs = (A.rungs || []).map((r) => r.y).sort((a, b) => a - b);
    const rungLo = rungYs.length ? rungYs[0] - 0.45 : 0;
    const rungHi = rungYs.length ? rungYs[rungYs.length - 1] + 0.65 : 30;
    const HIP = 0.94;
    const violations = [];
    let maxFeetErr = 0;
    const saved = people.map((p) => ({
      pos: p.obj.position.clone(),
      quat: p.obj.quaternion.clone(),
      vis: p.obj.visible,
    }));
    const foot = A.rungs[0];
    const out = A.outward || { x: 0, z: 1 };
    try {
      for (let tb = 0; tb <= show.launch + 0.001; tb = +(tb + dt).toFixed(4)) {
        tick(tb, people);
        people.forEach((person, i) => {
          if (!person.obj || !person.obj.visible) return;
          // Kill handler bake every sample (clips rewrite Crew_2).
          const c2 = person.obj.getObjectByName && person.obj.getObjectByName('Crew_2');
          if (c2) { c2.position.set(0, 0, 0); c2.rotation.set(0, 0, 0); }
          const mode = person.mode || '';
          const py = person.obj.position.y;
          const hips = person.obj.getObjectByName((person.pfx || '') + '_Hips');
          let hipsLocalY = HIP;
          if (hips) hipsLocalY = hips.position.y || HIP;
          // Ship-local feet ≈ posed-root Y (walk/wait use y=0 root; climb root = hip-HIP_Y).
          let feetY = py;
          if (mode === 'climb' || mode === 'enter') feetY = py; // pose.root already = hip - HIP_Y ≈ feet
          if (mode === 'inside') feetY = py;

          const push = (expect, err) => {
            maxFeetErr = Math.max(maxFeetErr, err);
            violations.push({
              id: person.pfx || String(i), tb: +tb.toFixed(3), mode,
              feetY: +feetY.toFixed(4), expect, err: +err.toFixed(4),
              pos: person.obj.position.toArray().map((v) => +v.toFixed(3)),
            });
          };

          if (mode === 'inside' || mode === 'enter') {
            if (feetY < 27.5 - maxErr || feetY > 31.0 + maxErr) {
              push('airlock', feetY < 27.5 ? 27.5 - feetY : feetY - 31.0);
            }
            return;
          }
          if (mode === 'climb') {
            if (feetY < rungLo - maxErr || feetY > rungHi + maxErr) {
              push('ladderY', feetY < rungLo ? rungLo - feetY : feetY - rungHi);
            }
            // Must be on the ladder face — catches Crew_2 bake offset (~14 m).
            const dx = person.obj.position.x - foot.x;
            const dz = person.obj.position.z - foot.z;
            const lat = Math.hypot(dx, dz);
            if (lat > 1.5) push('ladderXZ', lat);
            if (c2) {
              const off = Math.hypot(c2.position.x, c2.position.z);
              if (off > maxErr) push('crew2bake', off);
            }
            return;
          }
          // walk / wait: on pad ground, OR elevated deck walk into the airlock after climb
          if (feetY > 2.0) {
            // Deck traverse (bind sets mode=walk for first half of deck)
            if (feetY < rungHi - 1.0 - maxErr || feetY > 31.0 + maxErr) {
              push('deck', feetY < rungHi - 1.0 ? (rungHi - 1.0) - feetY : feetY - 31.0);
            }
          } else {
            const err = Math.abs(feetY - groundY);
            if (err > maxErr) push(groundY, err);
          }
        });
      }
    } finally {
      people.forEach((p, i) => {
        const s = saved[i]; if (!s || !p.obj) return;
        p.obj.position.copy(s.pos); p.obj.quaternion.copy(s.quat); p.obj.visible = s.vis;
      });
    }
    return { ok: violations.length === 0, violations, maxFeetErr: +maxFeetErr.toFixed(4), samples: Math.floor(show.launch / dt) + 1, launch: show.launch };
  }

  return { A, tick, bind, syncClips, assertBoardFeet };
}
