import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const b = fs.readFileSync(process.argv[2]); const g = await new Promise((r, j) => new GLTFLoader().parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', r, j));
// usage: node verify_storage_crane.mjs CRANE.glb SLOTS.json [DOCK_HMAP_PREFIX]   (placement read from SLOTS.json)
const SJ = JSON.parse(fs.readFileSync(process.argv[3])); const CW = SJ.storage_crane.place_world, STOPX = SJ.truck_stop_dock.world[0], DO = SJ.dock_origin_world;
let HM = null; if (process.argv[4]) { const J = JSON.parse(fs.readFileSync(process.argv[4] + '.json')); HM = { ...J, H: new Float32Array(fs.readFileSync(process.argv[4] + '.bin').buffer.slice(0, J.NX * J.NZ * 4)) }; }
const hAt = (wx, wz) => { if (!HM) return -1; const i = Math.floor((wx - DO[0] - HM.X0) / HM.C), j = Math.floor((wz - DO[2] - HM.Z0) / HM.C); return (i < 0 || j < 0 || i >= HM.NX || j >= HM.NZ) ? -1 : HM.H[j * HM.NX + i]; };
const S = g.scene; S.position.set(CW[0], CW[1], CW[2]); S.updateMatrixWorld(true);
const ex = S.getObjectByName('StorageCrane').userData; const slots = SJ.slots;
const mx = new THREE.AnimationMixer(S); const ha = S.getObjectByName('Hook_Attach'); const v = new THREE.Vector3(); const q = new THREE.Quaternion();
const truck = { x0: STOPX - 5.09, x1: STOPX + 3.69, z0: 11.1, z1: 14.9, top: 3.79 };
let worst = { pick: 0, set: 0, yaw: 0, clearStack: 1e9, clearTruck: 1e9, clearPillar: 1e9, clearDock: 1e9, jibOverDock: 1e9 };
const jib = ['SC_Slew', 'SC_Trolley'].map(n => S.getObjectByName(n));
for (const c of g.animations) {
  mx.stopAllAction(); const a = mx.clipAction(c); a.play();
  const pk = ex.pick[c.name.split('_')[1]]; const slotName = c.extras ? null : null; const sn = c.name.slice(-7); const si = +sn.slice(5) - 1; const sw = slots[si].world;
  const pw = S.getObjectByName(c.name.includes('_A_') ? 'Pick_A' : 'Pick_B').getWorldPosition(new THREE.Vector3());
  for (let t = 0; t <= 6.0001; t += 1 / 60) {
    mx.setTime(t); S.updateMatrixWorld(true); ha.getWorldPosition(v); ha.getWorldQuaternion(q);
    const yaw = Math.abs(new THREE.Euler().setFromQuaternion(q, 'YXZ').y) * 180 / Math.PI; worst.yaw = Math.max(worst.yaw, Math.min(yaw, 180 - yaw));
    if (Math.abs(t - 1.55) < 1e-3) worst.pick = Math.max(worst.pick, v.distanceTo(pw.clone().add(new THREE.Vector3(0, 1.5, 0))));
    if (Math.abs(t - 4.35) < 1e-3) worst.set = Math.max(worst.set, v.distanceTo(new THREE.Vector3(sw[0], sw[1] + 1.5, sw[2])));
    { // whole jib (slew centre -> 7.5 m along the jib and 2.5 m counter-jib) at its height vs dock heights
      const o = jib[0].getWorldPosition(new THREE.Vector3()), tp = jib[1].getWorldPosition(new THREE.Vector3()); const dir = tp.clone().sub(o).setY(0).normalize();
      for (let r = -2.5; r <= 7.5; r += 0.25) { const h = hAt(o.x + dir.x * r, o.z + dir.z * r); if (h > -0.5) worst.jibOverDock = Math.min(worst.jibOverDock, o.y - 0.3 - h); } }
    if (t > 2.15 && t < 3.75) {   // carried box: base = v - 1.5, size 2.4 x 1.5 x 1.34 (yaw 0)
      const bx0 = v.x - 1.2, bx1 = v.x + 1.2, bz0 = v.z - 0.67, bz1 = v.z + 0.67, by0 = v.y - 1.5;
      for (let k = 0; k < si; k++) { const s = slots[k].world; const ox = Math.min(bx1, s[0] + 1.2) - Math.max(bx0, s[0] - 1.2), oz = Math.min(bz1, s[2] + 0.67) - Math.max(bz0, s[2] - 0.67);
        if (ox > 0.01 && oz > 0.01) worst.clearStack = Math.min(worst.clearStack, by0 - (s[1] + 1.5)); }
      const ox = Math.min(bx1, truck.x1) - Math.max(bx0, truck.x0), oz = Math.min(bz1, truck.z1) - Math.max(bz0, truck.z0);
      if (ox > 0 && oz > 0 && t > 2.2) worst.clearTruck = Math.min(worst.clearTruck, by0 - truck.top);
      for (let x = bx0; x <= bx1 + 1e-6; x += 0.25) for (let z = bz0; z <= bz1 + 1e-6; z += 0.25) { const h = hAt(x, z); if (h > -0.5) worst.clearDock = Math.min(worst.clearDock, by0 - h); }
      const dx = Math.max(0, Math.abs(v.x - CW[0]) - 1.2), dz = Math.max(0, Math.abs(v.z - CW[2]) - 0.67); worst.clearPillar = Math.min(worst.clearPillar, Math.hypot(dx, dz) - 0.34);
    }
  }
}
console.log(JSON.stringify(worst));
