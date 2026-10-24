// Sample the 4 skinned climbers over all three clips (back to back, 15 Hz) in the pad-local frame and measure them against the hatch deck.
import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
await MeshoptDecoder.ready;
const load = p => new Promise((res, rej) => { const b = fs.readFileSync(p); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej); });
const [crewF, padF, outF] = process.argv.slice(2);
const pad = (await load(padF)).scene; pad.updateMatrixWorld(true);
const C = pad.getObjectByName('Ship_Center').getWorldPosition(new THREE.Vector3());
const LF = pad.getObjectByName('Ladder_Foot').getWorldPosition(new THREE.Vector3());
const g = await load(crewF); const S = g.scene; const mixer = new THREE.AnimationMixer(S);
const clips = Object.fromEntries(g.animations.map(a => [a.name, a]));
const order = ['crew_call', 'crew_walk_to_pad', 'crew_climb'];
const LAD = 330 * Math.PI / 180, LU = [Math.cos(LAD), Math.sin(LAD)], LT = [-LU[1], LU[0]];
// pad-local glTF (x, y up, z) -> ship frame: bx = x - C.x, by = -(z - C.z), bz = y
const toUTZ = v => { const bx = v.x - C.x, by = -(v.z - C.z); return [bx * LU[0] + by * LU[1], bx * LT[0] + by * LT[1], v.y]; };
const meshes = []; S.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
const SLAB = { u: [4.249, 5.251], t: [-0.702, 0.702], z: [21.748, 21.849] };
const ZB = [21.6, 22.0];
const res = { ship_center: [C.x, C.y, C.z], ladder_foot: [LF.x, LF.y, LF.z], ladder_foot_utz: toUTZ(LF), frames: 0, cross: {}, inSlab: 0, minClear: 1e9, minClearAt: null };
const v = new THREE.Vector3(); let T = 0; const dt = 1 / 15;
for (const cn of order) {
  const clip = clips[cn]; mixer.stopAllAction(); const act = mixer.clipAction(clip); act.reset(); act.setLoop(THREE.LoopOnce); act.clampWhenFinished = true; act.play();
  for (let t = 0; t <= clip.duration + 1e-6; t += dt) {
    mixer.setTime(t); S.updateMatrixWorld(true); res.frames++;
    for (const m of meshes) {
      const crew = m.parent && m.parent.name || m.name; let k = crew; let p = m; while (p && !/^Crew_\d$/.test(p.name)) p = p.parent; if (p) k = p.name;
      const pos = m.geometry.attributes.position;
      // skip hidden crew (root scaled to 1e-4 after inside_hatch)
      const sc = new THREE.Vector3(); m.skeleton.bones[0].getWorldScale(sc); if (sc.x < 1e-2) continue;
      for (let i = 0; i < pos.count; i++) {
        m.getVertexPosition(i, v); v.applyMatrix4(m.matrixWorld); const [u, tt, z] = toUTZ(v);
        if (z > ZB[0] && z < ZB[1] && Math.abs(tt) < 2 && u > 3.5 && u < 6.5) { const c = res.cross[k] || (res.cross[k] = { u: [1e9, -1e9], t: [1e9, -1e9], time: [1e9, -1e9] });
          c.u[0] = Math.min(c.u[0], u); c.u[1] = Math.max(c.u[1], u); c.t[0] = Math.min(c.t[0], tt); c.t[1] = Math.max(c.t[1], tt); c.time[0] = Math.min(c.time[0], T + t); c.time[1] = Math.max(c.time[1], T + t); }
        if (u > SLAB.u[0] && u < SLAB.u[1] && Math.abs(tt) < SLAB.t[1] && z > SLAB.z[0] && z < SLAB.z[1]) { res.inSlab++;
          const q = res.slab || (res.slab = { u: [1e9, -1e9], t: [1e9, -1e9], times: {} }); q.u[0] = Math.min(q.u[0], u); q.u[1] = Math.max(q.u[1], u); q.t[0] = Math.min(q.t[0], tt); q.t[1] = Math.max(q.t[1], tt);
          const key = k + '@' + (T + t).toFixed(1); q.times[k] = q.times[k] || [1e9, -1e9]; q.times[k][0] = Math.min(q.times[k][0], T + t); q.times[k][1] = Math.max(q.times[k][1], T + t); }
        if (u > 4.33 && u < 4.74 && Math.abs(tt) < 0.23 && z > 21.748 && z < 21.849) { const q = res.tread || (res.tread = {}); q[k] = q[k] || [1e9, -1e9, 0]; q[k][0] = Math.min(q[k][0], T + t); q[k][1] = Math.max(q[k][1], T + t); q[k][2]++; }
        { const STAND = { Crew_1: 53.45, Crew_2: 58.95, Crew_3: 64.45, Crew_4: 69.95 }; if (T + t < STAND[k] && z > 21.6 && z < 22.0 && u > 3.9 && u < 6.5 && Math.abs(tt) < 2) { const q = res.climbx || (res.climbx = { u: [1e9, -1e9], t: [1e9, -1e9] }); q.u[0] = Math.min(q.u[0], u); q.u[1] = Math.max(q.u[1], u); q.t[0] = Math.min(q.t[0], tt); q.t[1] = Math.max(q.t[1], tt); } }
        if (k === 'Crew_1' && z < 21.95 && z > 21.7 && T + t > 53.2) { const f = res.feet || (res.feet = {}); const fk = (T + t).toFixed(1); const e = f[fk] || (f[fk] = [1e9, -1e9, 1e9, -1e9, 1e9]); e[0] = Math.min(e[0], u); e[1] = Math.max(e[1], u); e[2] = Math.min(e[2], tt); e[3] = Math.max(e[3], tt); e[4] = Math.min(e[4], z); }
        if (k === 'Crew_1' && Math.abs(tt) < 2 && u > 3 && u < 6.5 && z > 19 && z < 24.5) { const fk = (T + t).toFixed(2); const f = res.c1 || (res.c1 = {}); const e = f[fk] || (f[fk] = [1e9, -1e9, 1e9, -1e9]); e[0] = Math.min(e[0], z); e[1] = Math.max(e[1], z); e[2] = Math.min(e[2], u); e[3] = Math.max(e[3], u); }
      }
    }
  }
  T += clip.duration;
}
fs.writeFileSync(outF, JSON.stringify(res, null, 1)); console.log(JSON.stringify(res));
