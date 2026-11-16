// Mechazilla pad loader (gc/mechazilla). Node names and rest poses are from
// art_next/pad_mechazilla/r2/glb/EXPORT.md. The r2 GLB is a stand-in: A&A's
// final try-2 pad GLB is due ~6:30 PM PT. Swapping it in is a single URL / md5
// change on PAD_MZ_URL (keep the same node names). In the final design the
// crew elevator and arm sit inside the chopstick tower at pad Lv20, with no
// separate CrewTower — r2 still has a separate CrewTower (flag, do not edit
// lv10_tower / control_tower / the Launch Pad card).

export const PAD_MZ_URL = '../dev/models/pad_mechazilla_r2_bb26428b.glb?v=bb26428b';
export const PAD_MZ_MD5 = 'bb26428b9e25a270717c012682abfd05';
export const PAD_MZ_STANDIN = true;          // r2 stand-in, not the 6:30 final GLB
export const PAD_MZ_CAM = { ct: { x: 9.25, y: 56.75, z: -13.0 }, frame_w: 99.5 };
export const PAD_MZ_NODES = [
  'Tower', 'Chopsticks', 'Carriage', 'Arm_L', 'Arm_R', 'Ship_Attach',
  'Mount', 'Mount_Turntable', 'CrewTower', 'Elevator_Car', 'Car_Door_L', 'Car_Door_R',
  'CrewArm', 'Airlock_Door_L', 'Airlock_Door_R', 'Crane', 'Cam_Target', 'Ship_Track',
  'Crew_Mark_1', 'Crew_Mark_2',
];
export const PAD_MZ_CLIPS = [
  'Catch_Lift_Swing_SetDown', 'CrewArm_Extend', 'CrewArm_Retract', 'Crew_Board',
  'crane_lift', 'crane_swing', 'crane_lower',
  'crane_lift_bay', 'crane_swing_hold', 'crane_lower_hold',
];

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

export function createPadMechazilla(THREE) {
  const T = {
    ready: false, failed: false, loading: false,
    root: null, nodes: {}, mx: null, acts: {}, missing: [], clips: [],
  };

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
    root.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
    // Overlay on the live launch-pad GLB (PAD_GLB stays). Hide the stand-in's
    // Mount and Crane so they do not z-fight the current deck / PC-1.
    if (T.nodes.Mount) T.nodes.Mount.visible = false;
    if (T.nodes.Crane) T.nodes.Crane.visible = false;
    T.mx = new THREE.AnimationMixer(root);
    T.acts = {};
    T.clips = [];
    for (const c of gltf.animations || []) {
      T.clips.push(c.name);
      T.acts[c.name] = T.mx.clipAction(c);
    }
    T.ready = true;
    T.failed = false;
    return info();
  }

  function load(loader, padRoot, onOk, onErr) {
    if (T.ready) { if (onOk) onOk(info()); return; }
    if (T.loading) return;
    if (!padRoot) { const e = new Error('pad root missing'); T.failed = true; if (onErr) onErr(e); return; }
    T.loading = true;
    loader.load(PAD_MZ_URL, (g) => {
      T.loading = false;
      try { const i = bind(g, padRoot); if (onOk) onOk(i); }
      catch (e) { T.failed = true; console.warn('Pad Mechazilla bind failed', e); if (onErr) onErr(e); }
    }, undefined, (e) => {
      T.loading = false; T.failed = true;
      console.warn('Pad Mechazilla GLB failed to load', PAD_MZ_URL, e); if (onErr) onErr(e);
    });
  }

  function setActive(on) { if (T.root) T.root.visible = !!on; }

  function play(name, loopOnce) {
    const a = T.acts[name]; if (!a) return false;
    T.mx.stopAllAction();
    if (loopOnce) { a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; }
    a.reset(); a.paused = false; a.enabled = true; a.play();
    return true;
  }

  function tick(dt) { if (T.mx && T.root && T.root.visible) T.mx.update(dt); }

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
    return {
      ready: T.ready, failed: T.failed, standin: PAD_MZ_STANDIN, url: PAD_MZ_URL, md5: PAD_MZ_MD5,
      visible: !!(T.root && T.root.visible),
      draws: vis.draws, tris: vis.tris,
      drawsAll: allDraws, trisAll: Math.round(allTris),
      missing: T.missing.slice(), clips: T.clips.slice(),
      hidden: ['Mount', 'Crane'].filter((n) => T.nodes[n] && !T.nodes[n].visible),
      hasCrewTower: !!T.nodes.CrewTower,
      cam: PAD_MZ_CAM,
    };
  }

  return { T, load, bind, setActive, play, tick, info, consts: { PAD_MZ_URL, PAD_MZ_MD5, PAD_MZ_CAM, PAD_MZ_STANDIN, PAD_MZ_NODES, PAD_MZ_CLIPS } };
}
