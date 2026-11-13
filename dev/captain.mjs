// Captain + Co-pilot launch boarding (Jacob via Game Director, 11/13 11:54 PT).
// Ambient: the Captain (a cloned male C-rig) walks a waypoint loop around the Launch Pad and launch-tower
// apron, stopping to inspect with a stand-in iPad. The path stays clear of the crane, tower, ship, crates,
// ladder, van/queue and the truck road.
// Launch: he walks from wherever he is to the ladder (no teleport), then climbs and boards with the approved
// 1720 poseShow / IK sequence. The Co-pilot is the existing pad crane attendant (break-room handler). If he
// is in the break room he plays the approved stand → helmet → airlock (doors, side vents) → walk-out path
// (brStep, unchanged); then he walks to the ladder and climbs the same sequence, after or alongside the
// Captain. If he is already outside, he walks from that spot (no teleport, no extra airlock).
// Visual only except: boardSec is the max of the existing climber time and "both pilots inside + doors
// stowed", so the sim stays in 'board' and the ship does not lift until they are aboard. Flyer counts,
// seats, launch costs/gating, and the Mechanic's approved climb timing are not changed. The Co-pilot is
// kept out of accessPeople until he is at the foot (so he is not lerped through the break-room walls).
// Camera is not touched. Pre-Habitat and the Lv10 tower keep the existing official boarding (no intercept).

import {
  poseShow, climbDur, deckDur, showTimes, ENTRY_DOOR_SEC, LADDER_STOW_SEC, BAY_DOOR_SEC, DEPLOY_T,
} from './access1720.mjs';

// Minimal skinned-mesh clone (same idea as three/addons/utils/SkeletonUtils.clone). The addons copy in /qa3d/vendor does not include that file.
function skelClone(source) {
  const srcOf = new Map(), cloneOf = new Map();
  const cloned = source.clone();
  (function walk(a, b) { srcOf.set(b, a); cloneOf.set(a, b); for (let i = 0; i < a.children.length; i++) walk(a.children[i], b.children[i]); })(source, cloned);
  cloned.traverse((node) => {
    if (!node.isSkinnedMesh) return;
    const src = srcOf.get(node);
    node.skeleton = src.skeleton.clone();
    node.bindMatrix.copy(src.bindMatrix);
    node.skeleton.bones = src.skeleton.bones.map((b) => cloneOf.get(b));
    node.bind(node.skeleton, node.bindMatrix);
  });
  return cloned;
}

const WALK_V = 1.4, STRIDE = 1.4, INSPECT = 5, OUT_TAU = 50.163;   // OUT_TAU = end of Handler_Ramp_Down (clears the airlock)

export function createCaptain(THREE, D) {
  const st = {
    ready: false, obj: null, mx: null, acts: {}, pad: null, hand: null, rest: {},
    trip: null,           // { t0, cap0, cp0 } snapshot for the current boarding (pure from t0 + saved cr)
  };
  const V3 = THREE.Vector3, V2 = (x, z) => [x, z];

  function PX() { return D.PX; }
  function ladder() { return D.ladder(); }   // [x, z] world
  function now() { return D.nowMs(); }

  // ---- pad graph (world XZ). Edges stay outside the ship, crane, tower, crate bay, ladder and van.
  function graph() {
    const x = PX(), L = ladder(), N = {
      W:  [x - 22, 0],
      NW: [x - 22, 10],
      SW: [x - 22, -16],
      S:  [x + 0, -23],
      SE: [x + 18, -16],
      E:  [x + 20, -4],
      NE: [x + 20, 10],
      E0: [x + 20, 0],
      AP: [x + 16, -16],
      LF: [L[0], L[1]],
      AX: [x + 10.7, 12.1],   // approved airlock exit (pad-local 10.7, 12.1)
      AE: [x + 20, 12],
      PS: [x - 7.85, 8.2],    // attendant post (pad-local -7.85, 8.2)
    };
    const E = [
      ['W', 'NW'], ['W', 'SW'], ['SW', 'S'], ['S', 'SE'], ['SE', 'E'], ['E', 'NE'],
      ['NE', 'E0'], ['E0', 'E'], ['E0', 'W'], ['SE', 'AP'], ['S', 'AP'], ['E', 'AP'],
      ['AP', 'LF'], ['AX', 'AE'], ['AE', 'NE'], ['AE', 'E0'], ['NW', 'PS'], ['PS', 'W'],
    ];
    return { N, E };
  }
  const LOOP = [          // inspect stops, in order, plus the corridor used to close the loop without crossing the crane
    { id: 'W',  look: 'bay' },
    { id: 'SW', look: 'ship' },
    { id: 'S',  look: 'ship' },
    { id: 'SE', look: 'ladder' },
    { id: 'E',  look: 'tower' },
    { id: 'NE', look: 'crane' },
    { id: 'E0', look: null },    // corridor only
    { id: 'W',  look: 'bay' },
    { id: 'NW', look: 'crane' },
  ];
  function lookAt(kind, p) {
    const x = PX(), t = kind === 'ship' ? [x, -13] : kind === 'crane' ? [x + 3.5, 8.32] : kind === 'ladder' || kind === 'tower' ? ladder() : [x - 7.5, 4.25];
    return Math.atan2(t[0] - p[0], t[1] - p[1]);
  }
  function dist(a, b) { return Math.hypot(b[0] - a[0], b[1] - a[1]); }
  function poly(pts) {
    const s = [0]; for (let i = 1; i < pts.length; i++) s.push(s[i - 1] + dist(pts[i - 1], pts[i]));
    return { pts, s, L: s[s.length - 1] };
  }
  function along(pl, d) {
    const { pts, s, L } = pl; d = Math.max(0, Math.min(L, d));
    let i = 1; while (i < s.length - 1 && s[i] < d) i++;
    const a = pts[i - 1], b = pts[i] || a, u = (d - s[i - 1]) / ((s[i] - s[i - 1]) || 1);
    return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, Math.atan2(b[0] - a[0], b[1] - a[1])];
  }
  function route(from, to) {          // shortest path on the graph, with from/to snapped in
    const { N, E } = graph();
    const nodes = { ...N, _from: from, _to: to };
    const adj = {};
    const add = (a, b) => { (adj[a] = adj[a] || []).push(b); (adj[b] = adj[b] || []).push(a); };
    for (const [a, b] of E) add(a, b);
    // snap from/to onto the nearest node; also add a temporary edge from _from/_to to their nearest 2 nodes if far
    const ids = Object.keys(N);
    const near = (p, n) => ids.map(id => [id, dist(p, N[id])]).sort((a, b) => a[1] - b[1]).slice(0, n);
    for (const [id, d] of near(from, 2)) if (d < 80) add('_from', id);
    for (const [id, d] of near(to, 2)) if (d < 80) add('_to', id);
    add('_from', '_to');   // direct if that is actually shortest and clear enough; dijkstra still prefers graph if shorter-via is better only when direct is long... 
    // Don't use a raw direct edge if it would cut through the pad (midpoint too close to ship / crane / ladder).
    const mid = [(from[0] + to[0]) / 2, (from[1] + to[1]) / 2], x = PX(), L = ladder();
    const blocked = dist(mid, [x, -13]) < 10 || dist(mid, [x + 3.5, 8.32]) < 6 || dist(mid, L) < 4 && dist(from, L) > 8 && dist(to, L) > 8;
    if (blocked) adj._from = adj._from.filter(k => k !== '_to'), adj._to = adj._to.filter(k => k !== '_from');
    const distN = (a, b) => dist(nodes[a], nodes[b]);
    const q = [['_from', 0]], prev = {}, best = { _from: 0 };
    while (q.length) {
      q.sort((a, b) => a[1] - b[1]);
      const [u, du] = q.shift(); if (du !== best[u]) continue; if (u === '_to') break;
      for (const v of (adj[u] || [])) {
        const nd = du + distN(u, v); if (best[v] != null && nd >= best[v] - 1e-9) continue;
        best[v] = nd; prev[v] = u; q.push([v, nd]);
      }
    }
    const path = [to];
    if (best._to == null) return poly([from, to]);
    let u = '_to';
    while (u && u !== '_from') { if (u !== '_to') path.push(nodes[u]); u = prev[u]; }
    path.push(from); path.reverse();
    // drop duplicates
    const pts = [path[0]]; for (let i = 1; i < path.length; i++) if (dist(pts[pts.length - 1], path[i]) > 0.05) pts.push(path[i]);
    return poly(pts);
  }
  function cycle() {                  // precompute wander cycle length from the inspect loop
    const { N } = graph();
    let L = 0; const segs = [];
    for (let i = 0; i < LOOP.length; i++) {
      const a = N[LOOP[i].id], b = N[LOOP[(i + 1) % LOOP.length].id];
      const pl = poly([a, b]), walk = pl.L / WALK_V, hold = LOOP[i].look ? INSPECT : 0;
      segs.push({ i, pl, walk, hold, look: LOOP[i].look, at: a });
      L += hold + walk;
    }
    return { T: L, segs };
  }
  function wanderAt(tMs) {
    const cyc = cycle(), u = ((tMs / 1000) % cyc.T + cyc.T) % cyc.T;
    let t = 0;
    for (const s of cyc.segs) {
      if (u < t + s.hold) return { x: s.at[0], z: s.at[1], yaw: lookAt(s.look, s.at), clip: 'idle', ct: u - t, inspect: !!s.look };
      t += s.hold;
      if (u < t + s.walk) {
        const q = along(s.pl, (u - t) * WALK_V);
        return { x: q[0], z: q[1], yaw: q[2], clip: 'walk', ct: (u - t), inspect: false };
      }
      t += s.walk;
    }
    const s = cyc.segs[0];
    return { x: s.at[0], z: s.at[1], yaw: 0, clip: 'idle', ct: 0, inspect: false };
  }

  // ---- iPad stand-in (thin tablet in the right hand; replaced if Art ships one)
  function makePad() {
    const g = new THREE.Group(); g.name = 'Captain_iPad';
    const body = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.006, 0.13), new THREE.MeshStandardMaterial({ color: 0x1a1c1e, roughness: 0.45, metalness: 0.2 }));
    const glass = new THREE.Mesh(new THREE.BoxGeometry(0.078, 0.001, 0.116), new THREE.MeshStandardMaterial({ color: 0x9ec8e6, roughness: 0.15, metalness: 0.1, emissive: 0x1a3040, emissiveIntensity: 0.35 }));
    glass.position.y = 0.0035; g.add(body, glass); g.traverse(m => { if (m.isMesh) { m.castShadow = true; m.frustumCulled = false; } });
    return g;
  }
  function bindPad(obj) {
    const hand = obj.getObjectByName('C1_Hand_R') || obj.getObjectByName('C1_RightHand'); if (!hand) return;
    const pad = makePad();
    // World-space (not bone-parented): some arm bones carry a non-1 scale that would balloon the tablet.
    D.scene.add(pad); st.pad = pad; st.hand = hand;
    st.padLocalQ = new THREE.Quaternion().setFromEuler(new THREE.Euler(1.2, 0, 1.57));
  }
  function posePad(show) {
    if (!st.pad) return;
    if (!show || !st.obj) { st.pad.visible = false; return; }
    const chest = st.obj.getObjectByName('C1_Chest') || st.obj;
    chest.updateWorldMatrix(true);
    const wp = new THREE.Vector3(), wq = new THREE.Quaternion();
    chest.getWorldPosition(wp);
    // Hold the tablet in front of the chest, facing slightly up — readable as "carrying an iPad" from the pad camera.
    const yaw = st.obj.rotation.y;
    const fwdX = Math.sin(yaw), fwdZ = Math.cos(yaw);
    if (st.pad.parent !== D.scene) D.scene.add(st.pad);
    st.pad.position.set(wp.x + fwdX * 0.28, wp.y + 0.08, wp.z + fwdZ * 0.28);
    st.pad.quaternion.setFromEuler(new THREE.Euler(-0.55, yaw, 0, 'YXZ'));
    st.pad.scale.set(1, 1, 1);
    st.pad.visible = true;
  }

  function play(name, time, loop) {
    const acts = st.acts; if (!acts) return;
    for (const n in acts) acts[n].setEffectiveWeight(0);
    const a = acts[name]; if (!a) return;
    const dur = a.getClip().duration; a.setEffectiveWeight(1); a.paused = true;
    a.time = loop ? ((time % dur) + dur) % dur : Math.max(0, Math.min(dur - 1e-4, time));
    st.mx.update(0);
  }
  function place(x, z, yaw) {
    const o = st.obj; if (!o) return;
    if (o.parent !== D.scene) D.scene.add(o);
    o.visible = true; o.position.set(x, 0, z); o.rotation.set(0, yaw, 0);
  }

  function tryBind() {
    if (D.disabled && D.disabled()) return false;
    if (st.ready) return true;
    const mech = D.mech && D.mech(); if (!mech || !mech.obj || !D.scene) return false;
    const obj = skelClone(mech.obj);
    obj.name = 'Captain'; obj.visible = true;
    obj.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; m.frustumCulled = false; } });
    const mx = new THREE.AnimationMixer(obj), acts = {};
    for (const k of ['walk', 'idle']) {
      const src = mech.acts && mech.acts[k]; if (!src) continue;
      const a = mx.clipAction(src.getClip()); a.play(); a.paused = true; a.setEffectiveWeight(0); acts[k] = a;
    }
    const rest = {};
    for (const name of ['Hips', 'Spine', 'Chest', 'Neck', 'Head']) {
      const b = obj.getObjectByName('C1_' + name); if (b) rest[name] = b.quaternion.clone();
    }
    D.scene.add(obj); st.obj = obj; st.mx = mx; st.acts = acts; st.rest = rest;
    bindPad(obj); st.ready = true;
    const w = wanderAt(now()); place(w.x, w.z, w.yaw); play(w.clip, w.ct, true);
    return true;
  }

  // ---- Co-pilot plan (pure from saved cr + t)
  function cpState(t) {
    const cr = D.crAt && D.crAt(t);
    return cr || { m: 'room', u: D.BRD.seat[0], xz: null };
  }
  function airlockLeft(u, t) {
    // game seconds from current loop time u (or from stand if seated) to the outdoor exit.
    const stand = D.BRD.stand;
    if (u == null || u < stand - 1e-6) return D.brDur(stand, OUT_TAU);
    if (u >= OUT_TAU - 1e-6) return 0;
    return D.brDur(u, OUT_TAU);
  }
  function cpStart(t) {
    const s = cpState(t);
    // If he's in the room or still inside the outbound airlock, he plays stand→exit (or the remainder) then walks.
    // If he's already outside, he walks from that world position.
    const outside = s.m === 'post' || (s.m === 'out' && s.u >= OUT_TAU - 1e-6) || (s.m === 'back' && s.u < 19.806);
    if (outside) {
      const xz = s.xz || [PX() - 7.85, 8.2];
      const pl = route(xz, ladder());
      return { kind: 'walk', from: xz, pl, air: 0, walk: pl.L / WALK_V, total: pl.L / WALK_V, u0: s.u };
    }
    const u0 = (s.m === 'room' || s.u < D.BRD.stand) ? D.BRD.stand : s.u;
    const air = airlockLeft(u0, t);
    const exit = [PX() + 10.7, 12.1];
    const pl = route(exit, ladder());
    return { kind: 'air', from: exit, pl, air, walk: pl.L / WALK_V, total: air + pl.L / WALK_V, u0 };
  }
  function capStart(t) {
    const w = wanderAt(t);
    const from = [w.x, w.z];
    const pl = route(from, ladder());
    return { from, pl, walk: pl.L / WALK_V, yaw0: w.yaw };
  }

  function climbStartTimes(t0) {
    const cap = capStart(t0), cp = cpStart(t0);
    const rungs = (D.rungs && D.rungs()) || [];
    const show = showTimes(2, rungs.length ? rungs : undefined, 0);
    const ready = show.entryOpen || (DEPLOY_T + ENTRY_DOOR_SEC);
    const s0 = Math.max(ready, cap.walk);             // Captain arrives, then climbs (first if he is first)
    const s1 = Math.max(ready, cp.total, s0 + (show.gap || 1.9));
    // If the Co-pilot arrives first, he starts first.
    const capFirst = cap.walk <= cp.total;
    const capS = capFirst ? s0 : Math.max(ready, cap.walk, (Math.max(ready, cp.total) + (show.gap || 1.9)));
    const cpS = capFirst ? s1 : Math.max(ready, cp.total);
    const per = (show.per || (climbDur(rungs) + deckDur()));
    const last = Math.max(capS + per, cpS + per);
    const close = last, entryClosed = close + ENTRY_DOOR_SEC, stow = entryClosed + LADDER_STOW_SEC, launch = stow + BAY_DOOR_SEC;
    return { cap, cp, capS, cpS, per, last, close, entryClosed, stow, launch, show };
  }

  function activeBoard(t) {
    const b = D.boardOf && D.boardOf();
    return b ? { t0: b.B, tb: (t - b.B) / 1000 } : null;
  }

  function shouldRun(t) {
    if (D.disabled && D.disabled()) return false;
    // Post-Habitat, 1720 ladder only. Pre-hab already walks everyone to the ladder; Lv10 keeps the official tower sequence.
    if (D.padUsesTower && D.padUsesTower()) return false;
    if (D.wkPreHab && D.wkPreHab()) return false;
    return true;
  }

  // ---- climber posing (same applyPose as access1720_bind, kept local so that module stays untouched)
  function applyPose(person, pose) {
    const pfx = person.pfx, q = (v) => new THREE.Quaternion(v.x, v.y, v.z, v.w), v = (p) => new V3(p.x, p.y, p.z);
    const root = person.obj.getObjectByName(pfx + '_Root'); if (!root) return;
    root.position.set(0, 0, 0); root.scale.set(1, 1, 1); root.quaternion.copy(q(pose.yawQ));
    for (const name of ['Hips', 'Spine', 'Chest']) { const b = person.obj.getObjectByName(pfx + '_' + name); if (b) b.quaternion.identity(); }
    for (const name of ['Neck', 'Head']) { const b = person.obj.getObjectByName(pfx + '_' + name); if (b && person.rest[name]) b.quaternion.copy(person.rest[name]); }
    for (const name in pose.bones) { const b = person.obj.getObjectByName(pfx + '_' + name); if (b) b.quaternion.copy(q(pose.bones[name])); }
    person.obj.position.copy(v(pose.root)); person.obj.quaternion.identity(); person.obj.updateMatrixWorld(true);
  }
  function hull() { return D.hull && D.hull(); }
  function attachHull(obj) {
    const h = hull(); if (!h || !obj) return false;
    if (obj.parent !== h) { obj.updateWorldMatrix(true, false); h.attach(obj); obj.position.y = 0; }
    return true;
  }
  function climbPose(person, tau, rungs, outward) {
    const c = climbDur(rungs), d = deckDur(), pose = poseShow(rungs, outward, Math.max(0, tau));
    if (tau <= c) { person.mode = 'climb'; applyPose(person, pose); if (person.acts) for (const n in person.acts) person.acts[n].setEffectiveWeight(0); }
    else if (tau <= c + d + 0.05) {
      const u = d > 1e-4 ? Math.min(1, (tau - c) / d) : 1;
      person.mode = u < 0.55 ? 'walk' : 'enter';
      if (person.mode === 'enter') applyPose(person, pose);
      else person.obj.position.copy(new V3(pose.root.x, pose.root.y, pose.root.z));
    } else {
      person.mode = 'inside'; person.obj.visible = true;
    }
    return person.mode;
  }

  function cmPerson() {
    const p = D.cm && D.cm(); if (!p || !p.obj) return null;
    return { obj: p.obj, pfx: 'C2', rest: p._accRest || st.cmRest || {}, acts: p.acts, mx: p.mx, handler: true, key: 'cm', root: p.root };
  }
  function capPerson() {
    if (!st.obj) return null;
    return { obj: st.obj, pfx: 'C1', rest: st.rest, acts: st.acts, key: 'cap' };
  }

  // ---- frame
  function poseWander(t) {
    if (!tryBind()) return;
    if (st.obj.parent !== D.scene) D.scene.add(st.obj);
    const w = wanderAt(t);
    place(w.x, w.z, w.yaw); play(w.clip, w.clip === 'walk' ? w.ct * (WALK_V / STRIDE) : w.ct, true);
    posePad(true);
  }
  function poseWalk(obj, pl, tau, isHandler) {
    const s = Math.min(Math.max(0, tau) * WALK_V, pl.L), q = along(pl, s);
    const done = s >= pl.L - 1e-4;
    if (isHandler) {
      const root = obj.root || obj.obj; if (!root) return done;
      // handler root is pad-local
      root.position.set(q[0] - PX(), 0, q[1]); root.rotation.set(0, q[2], 0);
      if (obj.obj) obj.obj.visible = true;
      D.wkPlay(obj, done ? 'idle' : 'walk', done ? 0 : tau, !done);
    } else {
      if (obj.parent !== D.scene) D.scene.add(obj);
      obj.visible = true; obj.position.set(q[0], 0, q[1]); obj.rotation.set(0, q[2], 0);
      play(done ? 'idle' : 'walk', done ? 0 : tau * (WALK_V / STRIDE), true);
    }
    return done;
  }

  function poseCopilotAir(times, tb) {
    const cm = D.cm && D.cm(); if (!cm) return 'gone';
    // Keep the handler under the break-room group while brStep runs (approved airlock).
    if (cm.obj && D.brkGrp && cm.obj.parent !== D.brkGrp()) { D.brkGrp().add(cm.obj); cm.obj.position.set(0, 0, 0); cm.obj.rotation.set(0, 0, 0); }
    const u = times.cp.u0 + tb;                       // brStep is posed in loop time (rate 1 over the stand→exit span)
    const uClamp = Math.min(OUT_TAU - 1e-4, Math.max(times.cp.u0, u));
    D.brStep(uClamp, 0);
    D.brHelmet(); D.brPuff(uClamp);
    return u >= OUT_TAU - 1e-4 ? 'out' : 'air';
  }

  function poseLaunch(t, b) {
    if (!tryBind()) return;
    if (!st.trip || st.trip.t0 !== b.t0) st.trip = Object.assign({ t0: b.t0 }, climbStartTimes(b.t0));
    const times = st.trip;
    const tb = b.tb, rungs = D.rungs(), outward = D.outward();
    // Captain
    const capP = capPerson();
    if (tb < times.capS) {
      if (st.obj && hull() && st.obj.parent === hull()) D.scene.attach(st.obj);
      poseWalk(st.obj, times.cap.pl, tb, false);
      posePad(true);
    } else {
      posePad(false);
      if (attachHull(st.obj)) {
        const mode = climbPose(capP, tb - times.capS, rungs, outward);
        if (mode === 'inside') st.obj.visible = false;
      }
    }
    // Co-pilot
    const cp = times.cp, cm = cmPerson();
    if (cm && cm.obj) {
      if (cp.kind === 'air' && tb < cp.air) {
        poseCopilotAir(times, tb);
      } else {
        const walkTau = cp.kind === 'air' ? tb - cp.air : tb;
        if (tb < times.cpS) {
          // leave the break-room group; walk in world / pad-local
          poseWalk(cm, cp.pl, Math.max(0, walkTau), true);
        } else {
          if (attachHull(cm.obj)) {
            D.accessPrep && D.accessPrep(cm);
            const mode = climbPose(cm, tb - times.cpS, rungs, outward);
            if (mode === 'inside') cm.obj.visible = false;
          }
        }
      }
    }
  }

  function update(t) {
    try { updateInner(t); } catch (e) { st.err = String(e && e.stack || e); }
  }
  function updateInner(t) {
    if (st.trip && !(D.boardOf && D.boardOf())) st.trip = null;   // clear snapshot when the board phase ends
    if (!shouldRun(t) && st.ready) {
      // Pre-hab / Lv10: still wander while the ship is on the pad, hide while it's away. Do not intercept boarding.
      const sh = D.shipSt && D.shipSt();
      if (sh && sh !== 'pad' && sh !== 'board') { if (st.obj) st.obj.visible = false; posePad(false); return; }
      if (sh === 'board') { /* leave official climbers alone; hide Captain so he isn't standing in the elevator */ if (st.obj) st.obj.visible = false; posePad(false); return; }
      poseWander(t); return;
    }
    const b = activeBoard(t);
    const sh = D.shipSt && D.shipSt();
    if (b && shouldRun(t)) { poseLaunch(t, b); return; }
    if (sh && (sh === 'launch' || sh === 'away' || sh === 'land' || sh === 'deboard')) {
      if (st.obj) st.obj.visible = false;
      return;
    }
    poseWander(t);
  }

  function boardExtra(sh) {
    if (!shouldRun(now())) return 0;
    // Frozen trip: already on sh.bsec. Here we compute the candidate duration at the current sim time.
    const t = (D.cgT && D.cgT()) || now();
    try { return climbStartTimes(t).launch; } catch (e) { return 0; }
  }

  function ownsCopilot() {
    if (!shouldRun(now())) return false;
    const b = activeBoard(now()); if (!b) return false;
    const times = st.trip || climbStartTimes(b.t0);
    // Own him until he starts the official-style climb (we've posed the walk). Stay owning through the climb
    // so accessPeople does not lerp him. Release when the board phase ends.
    return true;
  }
  function keepCopilotVisible() {
    if (!ownsCopilot()) return false;
    const b = activeBoard(now()); if (!b) return false;
    const times = st.trip || climbStartTimes(b.t0);
    return b.tb < times.cpS + times.per;   // visible until he is inside
  }
  function holdDoors(tb) {
    if (!shouldRun(now()) || !D.syncClips) return;
    const b = activeBoard(now()); if (!b) return;
    const times = st.trip || climbStartTimes(b.t0);
    const base = D.show && D.show(); if (!base) return;
    const show = Object.assign({}, base, {
      close: times.close, entryClosed: times.entryClosed, stow: times.stow, launch: times.launch,
    });
    D.syncClips(tb, show);
  }
  function info() {
    const t = now(), b = activeBoard(t), w = st.ready ? { x: st.obj.position.x, z: st.obj.position.z } : null;
    return { ready: st.ready, board: !!b, tb: b ? +b.tb.toFixed(2) : -1, pos: w, owns: ownsCopilot(), extra: boardExtra(), trip: st.trip && { capS: +st.trip.capS.toFixed(2), cpS: +st.trip.cpS.toFixed(2), launch: +st.trip.launch.toFixed(2), cpKind: st.trip.cp.kind } };
  }

  return { update, boardExtra, ownsCopilot, keepCopilotVisible, holdDoors, info, wanderAt, tryBind };
}
