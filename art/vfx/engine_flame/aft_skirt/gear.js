// Planet Stack - folding landing gear of the aft skirt module (Art & Animation, 10/24/2026). Original design.
// 4 slim legs in flush bays, joints Gear_Leg_k / Gear_Knee_k / Gear_Foot_k / Gear_Door_ka|kb inside the one skinned aft-skirt mesh
// (1 draw call for ring + band + gear, so the gear adds 0 draws). Driven from the same clock as the flame:
//   gear.update('launch', tRelLiftoff, alt)   gear.update('land', tRelTouchdown, alt)
// The numbers come from the GLB (scene.extras.gear), written by _src/gear_pose.py, which also bakes the Gear_Retract / Gear_Deploy clips.
import * as THREE from 'three';

// Timeline (ms). Launch: rel lift-off LO (tap + 55.99 s). Landing: rel touchdown TD (LO + 616 s = tap + 671.99 s).
export const GEAR_T = {
  R_DOOR_OPEN: [1000, 1600], R_KNEE: [1600, 3400], R_SWING: [2200, 3400], R_SETTLE: [3400, 3600], R_DOOR_CLOSE: [3600, 4200],   // retract: LO+1.0 .. LO+4.2
  D_DOOR_OPEN: [-7000, -6400], D_KNEE: [-6400, -4400], D_SWING: [-6300, -5200], D_BOUNCE: [-4400, -4000], D_DOOR_CLOSE: [-4000, -3400],   // deploy: TD-7.0 .. TD-3.4
};
const ease = (x) => { x = Math.min(1, Math.max(0, x)); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };   // easeInOutCubic
const win = (t, [a, b]) => ease((t - a) / (b - a));
// damped settle, peak 1, zero value and speed at both ends (lock beat on deploy, seat beat at stow) - same as gear_pose.settle
const settle = (u) => (u >= 0 && u <= 1) ? Math.sin(Math.PI * u) ** 2 * Math.sin(2 * Math.PI * u) * Math.exp(-2.5 * u) / 0.2940373 : 0;
// door 0 shut..1 open, knee 0 locked..1 folded, swing 0 down..1 stowed, bounce (rad, knee lock settle), settle (rad, hip seat at stow), ext 0..1 of the 5 cm shock stroke
export function gearState(phase, t, alt = 0, meta = { stroke_m: 0.05, bounce_rad: 0.07, stow_settle_rad: 0.025 }) {
  let door, knee, swing, bounce = 0, hip = 0;
  if (phase === 'launch') { door = win(t, GEAR_T.R_DOOR_OPEN) - win(t, GEAR_T.R_DOOR_CLOSE); knee = win(t, GEAR_T.R_KNEE); swing = win(t, GEAR_T.R_SWING);
    const [a, b] = GEAR_T.R_SETTLE; hip = (meta.stow_settle_rad ?? 0.025) * settle((t - a) / (b - a)); }
  else { door = win(t, GEAR_T.D_DOOR_OPEN) - win(t, GEAR_T.D_DOOR_CLOSE); swing = 1 - win(t, GEAR_T.D_SWING); knee = 1 - win(t, GEAR_T.D_KNEE);
    const [a, b] = GEAR_T.D_BOUNCE; bounce = -meta.bounce_rad * settle((t - a) / (b - a)); }
  const S = meta.stroke_m, ext = 1 - Math.min(1, Math.max(0, (S - alt) / S));   // feet compress as the last 5 cm of altitude go (full at TD)
  return { door, knee, swing, bounce, settle: hip, ext };
}
export function createGear(aftSkirtRoot) {
  let meta = null; aftSkirtRoot.traverse(n => { if (!meta && n.userData?.gear) meta = n.userData.gear; });
  if (!meta) return null;
  const bone = (name) => aftSkirtRoot.getObjectByName(name);
  const legs = meta.legs.map(lg => ({ lg, leg: bone(`Gear_Leg_${lg.k}`), knee: bone(`Gear_Knee_${lg.k}`), foot: bone(`Gear_Foot_${lg.k}`),
    doors: lg.doors.map(d => ({ d, b: bone(`Gear_Door_${lg.k}${d.side}`) })),
    t: new THREE.Vector3(...lg.t), dvec: new THREE.Vector3(...lg.d), foot0: new THREE.Vector3(...lg.F).add(new THREE.Vector3(...lg.off)).sub(new THREE.Vector3(...lg.K)) }));
  const up = new THREE.Vector3(0, 1, 0), DOOR = THREE.MathUtils.degToRad(meta.door_open_deg);
  const api = {
    meta, legs, last: null,
    update(phase, t, alt) {
      const st = gearState(phase, t, alt, meta); api.last = st;
      for (const L of legs) {
        L.leg.quaternion.setFromAxisAngle(L.t, L.lg.hip_sign * (L.lg.theta * st.swing - st.settle));
        L.knee.quaternion.setFromAxisAngle(L.t, L.lg.knee_sign * (Math.PI * st.knee + st.bounce));
        L.foot.position.copy(L.foot0).addScaledVector(L.dvec, meta.stroke_m * st.ext);
        for (const D of L.doors) D.b.quaternion.setFromAxisAngle(up, D.d.sign * DOOR * st.door);
      }
      return st;
    },
  };
  return api;
}
