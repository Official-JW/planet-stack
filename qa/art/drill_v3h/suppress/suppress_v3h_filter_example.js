// Documentation-only reference — not a drop-in game module.
// After THREE.GLTFLoader + MeshoptDecoder have decoded mine_revamp_c9a9394e.glb,
// filter the Base_Paint / Base_GlowCyan index buffers by world-space centroid AABB.
// Boxes are glTF / Three.js (+Y up). Inclusive on all faces, matching Blender cut_faces_in_box.
//
// Do NOT ship a raw list of triangle indices: gltfpack -noq and any re-pack reorder
// vertices (this file's -noq unpack welded 7 Base_Paint verts) so those indices would
// delete the wrong triangles.

export const SUPPRESS_AABBS_GLTF = [
  // v3 plant: hopper, silo, supports, teal scrap
  { name: 'PLANT', min: [-5.40, -0.30, -10.20], max: [14.20, 9.90, 12.20] },
  { name: 'TEAL',  min: [-5.80,  0.20,  -6.60], max: [ 1.80, 2.40,  1.50] },
  // v1 + v2: old derrick, circular pad, drill-side scrap (already gone in the v3+ study)
  { name: 'DERRICK_BOX',  min: [-11.20,  0.05, -6.40], max: [-4.50, 18.5, -1.40] },
  { name: 'DERRICK_TALL', min: [-11.20,  3.80, -6.40], max: [-3.70, 18.5, -1.40] },
  { name: 'PAD_BOX',      min: [ -9.70, -0.06, -5.40], max: [-5.30, 0.85, -1.90] },
  { name: 'PAD_A',        min: [-14.70, -0.35, -6.90], max: [-5.10, 1.20,  4.40] },
  { name: 'PAD_B',        min: [-13.40, -0.35, -1.52], max: [-5.10, 1.50,  4.40] },
  { name: 'SCRAP',        min: [-12.40,  1.00, -6.80], max: [-5.20, 6.40,  1.10] },
];

function centroidInside(cx, cy, cz, box) {
  return cx >= box.min[0] && cx <= box.max[0]
      && cy >= box.min[1] && cy <= box.max[1]
      && cz >= box.min[2] && cz <= box.max[2];
}

/** Rewrite mesh.geometry.index in place, dropping triangles whose world centroid is in any AABB. */
export function filterIndexBufferByCentroidAABB(mesh, aabbs = SUPPRESS_AABBS_GLTF) {
  mesh.updateMatrixWorld(true);
  const pos = mesh.geometry.getAttribute('position');
  const idx = mesh.geometry.getIndex();
  const kept = [];
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  for (let t = 0; t < idx.count; t += 3) {
    const i0 = idx.getX(t), i1 = idx.getX(t + 1), i2 = idx.getX(t + 2);
    a.fromBufferAttribute(pos, i0).applyMatrix4(mesh.matrixWorld);
    b.fromBufferAttribute(pos, i1).applyMatrix4(mesh.matrixWorld);
    c.fromBufferAttribute(pos, i2).applyMatrix4(mesh.matrixWorld);
    const cx = (a.x + b.x + c.x) / 3;
    const cy = (a.y + b.y + c.y) / 3;
    const cz = (a.z + b.z + c.z) / 3;
    let drop = false;
    for (let i = 0; i < aabbs.length; i++) {
      if (centroidInside(cx, cy, cz, aabbs[i])) { drop = true; break; }
    }
    if (!drop) kept.push(i0, i1, i2);
  }
  mesh.geometry.setIndex(kept);
  mesh.geometry.index.needsUpdate = true;
  return kept.length / 3;
}

export function applyMergedFaceSuppression(root) {
  const paint = root.getObjectByName('Base_Paint');
  const glow = root.getObjectByName('Base_GlowCyan');
  const paintMesh = paint && paint.children.find((o) => o.isMesh);
  const glowMesh = glow && glow.children.find((o) => o.isMesh);
  const remaining = {};
  if (paintMesh) remaining.Base_Paint = filterIndexBufferByCentroidAABB(paintMesh);
  if (glowMesh) remaining.Base_GlowCyan = filterIndexBufferByCentroidAABB(glowMesh);
  // After the full union Base_GlowCyan has 0 triangles — hiding the node is equivalent:
  if (glow && remaining.Base_GlowCyan === 0) glow.visible = false;
  return remaining; // expected { Base_Paint: 315, Base_GlowCyan: 0 }
}
