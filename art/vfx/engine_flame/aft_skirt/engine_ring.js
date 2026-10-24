// Planet Stack - parametric engine ring (Art & Animation, 10/24/2026). Original design, no logos.
// N engines (6..11) evenly spaced on ONE ring under the Lv1 hull (8.0 m dia, aft skirt R 4.18). Adding an engine re-spaces the ring.
// GLB variants engine_ring_N06.glb .. engine_ring_N11.glb (built by _src/build_engine_ring.py): 1 mesh (1 material, vertex colours,
// 1 draw call) + Engine_Nozzle_0..N-1 marker nodes at each bell exit (local -Y = thrust) + the same layout in scene/root extras.
import * as THREE from 'three';

export const ENGINE_RING = {
  HULL_R: 4.0, SKIRT_R: 4.18, RING_R: 3.05, EXIT_R0: 0.84, EXIT_Y: 0.9, MIN_N: 6, MAX_N: 11, PAD_YAW: 60,
  THRUST_STEP: 0.08,     // +8% flame brightness and length per thrust step (Lv3, 5, 7, 9)
};
// Level -> engines: Lv1 6, Lv2 7, Lv4 8, Lv6 9, Lv8 10, Lv10 11 (odd levels keep the count and add a thrust step instead).
export const engineCountForLevel = (lv) => Math.min(ENGINE_RING.MAX_N, ENGINE_RING.MIN_N + Math.floor(Math.max(1, lv) / 2));
// Level -> thrust steps: Lv1-2 0, Lv3-4 1, Lv5-6 2, Lv7-8 3, Lv9-10 4.
export const thrustLevelForLevel = (lv) => Math.min(4, Math.floor((Math.max(1, lv) - 1) / 2));
export const ringFile = (N) => `engine_ring_N${String(N).padStart(2, '0')}.glb`;

// Same maths as the builder (so code can lay out flames before / without the GLB). Ship-local, Y up, origin = ship base.
export function ringLayout(N) {
  const R = ENGINE_RING.RING_R, chord = 2 * R * Math.sin(Math.PI / N), exitR = Math.min(ENGINE_RING.EXIT_R0, 0.46 * chord);
  const ph = 90 + (N % 2 === 0 ? 90 / N : 0) - ENGINE_RING.PAD_YAW;   // no two bells line up front-to-back in the fixed pad camera
  return Array.from({ length: N }, (_, k) => { const a = THREE.MathUtils.degToRad(ph + 360 * k / N);
    return { name: `Engine_Nozzle_${k}`, pos: new THREE.Vector3(R * Math.cos(a), ENGINE_RING.EXIT_Y, -R * Math.sin(a)), dir: new THREE.Vector3(0, -1, 0), exitR }; });
}

// Mount a loaded ring GLB on a ship. shipRoot = the ship node that moves at lift-off. frame = the ring's ship-local frame
// expressed in shipRoot space: { position (ship base centre), quaternion (hull yaw) }. Returns the ring group.
export function mountEngineRing(shipRoot, ringGltf, frame = {}) {
  const ring = ringGltf.scene; ring.name = 'Engine_Ring';
  if (frame.position) ring.position.copy(frame.position); if (frame.quaternion) ring.quaternion.copy(frame.quaternion);
  ring.traverse(n => { if (n.isMesh) { n.castShadow = true; n.receiveShadow = true; if (n.material) n.material.vertexColors = true; } });
  shipRoot.add(ring); ring.updateMatrixWorld(true);
  return ring;
}

// Swap: remove the old nozzle section. In a ship GLB that keeps its bells as separate nodes, just hide/remove them.
// The current pad GLB merges the bells into the Ship_Placeholder mesh, so the render scene (preview only) collapses those
// vertices in place: every vertex within `radius` of an old bell axis and below `topY` (world) goes to a point inside the skirt.
export function collapseMergedBells(shipMeshes, axesWorld, { radius = 1.0, bottomY = -1e9, topY, sinkY }) {
  const v = new THREE.Vector3(), inv = new THREE.Matrix4(); let moved = 0;
  for (const m of shipMeshes) { m.updateMatrixWorld(true); inv.copy(m.matrixWorld).invert(); const p = m.geometry.attributes.position; let hit = false;
    for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i).applyMatrix4(m.matrixWorld); if (v.y > topY || v.y < bottomY) continue;
      const a = axesWorld.find(q => Math.hypot(v.x - q.x, v.z - q.z) < radius); if (!a) continue;
      v.set(a.x, sinkY, a.z).applyMatrix4(inv); p.setXYZ(i, v.x, v.y, v.z); moved++; hit = true; }
    if (hit) { p.needsUpdate = true; m.geometry.computeBoundingSphere(); } }
  return moved;
}
