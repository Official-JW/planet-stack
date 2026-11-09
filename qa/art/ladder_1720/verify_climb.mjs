// Numeric check of the 1720 climb: rung contact error and body clearance.
// Run: node --experimental-default-type=module qa/art/ladder_1720/verify_climb.mjs
import fs from 'fs';
import {
  stageRungLocals, poseFrame, bodySpheres, poseStand, outwardOf, faceYaw, climbDur,
  showTimes, add, mul, sub, len, DEPLOY_T, STOW_T0, CLIP_END, DOOR_SEC,
} from '../../../dev/access1720.mjs';

function glb(path) {
  const data = fs.readFileSync(path);
  let off = 12;
  const chunks = [];
  while (off < data.length) {
    const clen = data.readUInt32LE(off);
    chunks.push(data.subarray(off + 8, off + 8 + clen));
    off += 8 + clen;
  }
  return { js: JSON.parse(chunks[0].toString('utf8')), bin: chunks[1] };
}
function readAcc(js, bin, ai) {
  const a = js.accessors[ai];
  const ncomp = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4 }[a.type];
  const dt = { 5126: Float32Array, 5123: Uint16Array, 5125: Uint32Array, 5121: Uint8Array }[a.componentType];
  const arr = new Float64Array(a.count * ncomp);
  if (a.bufferView !== undefined) {
    const bv = js.bufferViews[a.bufferView];
    const start = (bv.byteOffset || 0) + (a.byteOffset || 0);
    const view = new dt(bin.buffer, bin.byteOffset + start, a.count * ncomp);
    for (let i = 0; i < view.length; i++) arr[i] = view[i];
  }
  if (a.sparse) {
    const sp = a.sparse;
    const iv = sp.indices;
    const bv = js.bufferViews[iv.bufferView];
    const ist = (bv.byteOffset || 0) + (iv.byteOffset || 0);
    const idt = { 5123: Uint16Array, 5125: Uint32Array, 5121: Uint8Array }[iv.componentType];
    const idx = new idt(bin.buffer, bin.byteOffset + ist, sp.count);
    const vv = sp.values;
    const bv2 = js.bufferViews[vv.bufferView];
    const vs = (bv2.byteOffset || 0) + (vv.byteOffset || 0);
    const vals = new Float32Array(bin.buffer, bin.byteOffset + vs, sp.count * ncomp);
    for (let i = 0; i < sp.count; i++) for (let k = 0; k < ncomp; k++) arr[idx[i] * ncomp + k] = vals[i * ncomp + k];
  }
  return arr;
}

function distPointTri(p, a, b, c) {
  const ab = sub(b, a), ac = sub(c, a), ap = sub(p, a);
  const d1 = ab.x * ap.x + ab.y * ap.y + ab.z * ap.z;
  const d2 = ac.x * ap.x + ac.y * ap.y + ac.z * ap.z;
  if (d1 <= 0 && d2 <= 0) return len(ap);
  const bp = sub(p, b);
  const d3 = ab.x * bp.x + ab.y * bp.y + ab.z * bp.z;
  const d4 = ac.x * bp.x + ac.y * bp.y + ac.z * bp.z;
  if (d3 >= 0 && d4 <= d3) return len(bp);
  const vc = d1 * d4 - d3 * d2;
  if (vc <= 0 && d1 >= 0 && d3 <= 0) {
    const v = d1 / (d1 - d3);
    return len(sub(p, add(a, mul(ab, v))));
  }
  const cp = sub(p, c);
  const d5 = ab.x * cp.x + ab.y * cp.y + ab.z * cp.z;
  const d6 = ac.x * cp.x + ac.y * cp.y + ac.z * cp.z;
  if (d6 >= 0 && d5 <= d6) return len(cp);
  const vb = d5 * d2 - d1 * d6;
  if (vb <= 0 && d2 >= 0 && d6 <= 0) {
    const w = d2 / (d2 - d6);
    return len(sub(p, add(a, mul(ac, w))));
  }
  const va = d3 * d6 - d5 * d4;
  if (va <= 0 && (d4 - d3) >= 0 && (d5 - d6) >= 0) {
    const w = (d4 - d3) / ((d4 - d3) + (d5 - d6));
    return len(sub(p, add(b, mul(sub(c, b), w))));
  }
  const denom = 1 / (va + vb + vc);
  const v = vb * denom, w = vc * denom;
  const q = add(a, add(mul(ab, v), mul(ac, w)));
  return len(sub(p, q));
}

function trisOf(pos, idx, xform) {
  const out = [];
  for (let t = 0; t < idx.length; t += 3) {
    const A = [], B = [], C = [];
    for (const [id, dst] of [[idx[t], A], [idx[t + 1], B], [idx[t + 2], C]]) {
      const p = xform(pos[id * 3], pos[id * 3 + 1], pos[id * 3 + 2]);
      dst.push(p.x, p.y, p.z);
    }
    out.push(A, B, C);
  }
  return out;
}
const idn = (x, y, z) => ({ x, y, z });

const lad = glb('qa3d-next/models/pr17_access_assembly_1015_7dc4c876.glb');
const hul = glb('qa3d-next/models/hull_channel_relief_1720_4700a081.glb');

// Deployed stage origins from the clip (frame 82).
const anim = lad.js.animations[0];
const stageT = {};
for (const ch of anim.channels) {
  const name = lad.js.nodes[ch.target.node].name;
  if (ch.target.path !== 'translation' || !name.startsWith('LadderStage')) continue;
  const samp = anim.samplers[ch.sampler];
  const vals = readAcc(lad.js, lad.bin, samp.output);
  const i = 82 * 3;
  stageT[name] = { x: vals[i], y: vals[i + 1], z: vals[i + 2] };
}

const rungs = [];
const stiles = [];
for (let s = 0; s < 6; s++) {
  const mesh = lad.js.meshes[s + 1];
  const prim = mesh.primitives[0];
  const pos = readAcc(lad.js, lad.bin, prim.attributes.POSITION);
  const idx = readAcc(lad.js, lad.bin, prim.indices);
  const org = stageT['LadderStage_' + s];
  const xf = (x, y, z) => ({ x: x + org.x, y: y + org.y, z: z + org.z });
  for (const ly of stageRungLocals()) rungs.push({ x: org.x, y: org.y + ly, z: org.z, stage: s });
  // stile triangles: every vertex is out on a rail (|x| > 0.12). Cross-bars are not stiles.
  for (let t = 0; t < idx.length; t += 3) {
    const ids = [idx[t], idx[t + 1], idx[t + 2]];
    const xs = ids.map((id) => pos[id * 3]);
    const neg = xs.some((x) => x < -0.05), posi = xs.some((x) => x > 0.05);
    if (neg && posi) continue; // cross-bar: the rung the hands stand on
    const tri = ids.map((id) => xf(pos[id * 3], pos[id * 3 + 1], pos[id * 3 + 2]));
    stiles.push(tri);
  }
}
rungs.sort((a, b) => a.y - b.y);
console.log('rungs', rungs.length, 'y', rungs[0].y.toFixed(3), '→', rungs[rungs.length - 1].y.toFixed(3), 'stiles', stiles.length);

function meshTris(file, meshIndex, xf = idn) {
  const prim = file.js.meshes[meshIndex].primitives[0];
  const pos = readAcc(file.js, file.bin, prim.attributes.POSITION);
  const idx = readAcc(file.js, file.bin, prim.indices);
  const tris = [];
  for (let t = 0; t < idx.length; t += 3) {
    tris.push([idx[t], idx[t + 1], idx[t + 2]].map((id) => xf(pos[id * 3], pos[id * 3 + 1], pos[id * 3 + 2])));
  }
  return tris;
}
// rails at deployed morph (frame 82 → target index 81)
const railPrim = lad.js.meshes[7].primitives[0];
const railPos = readAcc(lad.js, lad.bin, railPrim.attributes.POSITION);
const railDelta = readAcc(lad.js, lad.bin, railPrim.targets[81].POSITION);
const railDep = new Float64Array(railPos.length);
for (let i = 0; i < railPos.length; i++) railDep[i] = railPos[i] + railDelta[i];
const railIdx = readAcc(lad.js, lad.bin, railPrim.indices);
const rails = [];
for (let t = 0; t < railIdx.length; t += 3) {
  rails.push([railIdx[t], railIdx[t + 1], railIdx[t + 2]].map((id) => ({ x: railDep[id * 3], y: railDep[id * 3 + 1], z: railDep[id * 3 + 2] })));
}
const frame = meshTris(lad, 13);
const hull = meshTris(hul, 1);
const chamber = meshTris(lad, 9);
const corridor = meshTris(lad, 10);
const openOuter = (x, y, z) => ({ x: x + 1.55, y, z: z + 0.22 });
const openInner = (x, y, z) => ({ x: x + 1.55, y, z: z - 0.18 });
const outerOpen = meshTris(lad, 12, openOuter);
const innerOpen = meshTris(lad, 11, openInner);

const obstacles = [
  ['stiles', stiles],
  ['rails', rails],
  ['frame', frame],
  ['hull', hull],
  ['chamber', chamber],
  ['corridor', corridor],
  ['outerDoor', outerOpen],
  ['innerDoor', innerOpen],
];

function clearOf(spheres) {
  let best = { d: 1e9, name: '', sphere: '' };
  for (const s of spheres) {
    for (const [name, tris] of obstacles) {
      for (const tri of tris) {
        const ax = tri[0].x, ay = tri[0].y, az = tri[0].z;
        if (Math.abs(s.p.x - ax) > 1.2 && Math.abs(s.p.y - ay) > 1.2 && Math.abs(s.p.z - az) > 1.2) {
          // still need the other verts; cheap reject only if all three are far
        }
        const far = tri.every((q) => Math.abs(q.x - s.p.x) > 0.8 && Math.abs(q.y - s.p.y) > 0.8 && Math.abs(q.z - s.p.z) > 0.8);
        if (far) continue;
        const dist = distPointTri(s.p, tri[0], tri[1], tri[2]) - s.r;
        if (dist < best.d) best = { d: dist, name, sphere: s.name };
      }
    }
  }
  return best;
}

const anchor = rungs[0];
const outward = outwardOf(anchor);
const yaw = faceYaw(outward);
const dur = climbDur(rungs);
let maxErr = 0, minClear = 1e9, minWhere = null, n = 0;
const samples = [];
function take(tag, frame, t) {
  const spheres = bodySpheres(frame);
  const c = clearOf(spheres);
  if (frame.err > maxErr) maxErr = frame.err;
  if (c.d < minClear) { minClear = c.d; minWhere = { tag, t, ...c }; }
  n++;
  samples.push({ tag, t: +t.toFixed(2), contactCm: +(frame.err * 100).toFixed(3), clearCm: +(c.d * 100).toFixed(2), hit: c.name, sphere: c.sphere });
}

for (let t = 0; t <= dur; t += 0.2) take('climb', poseFrame(rungs, t, outward), t);

// step-off and door: stand on the deck, walk inward, through the frame
const deckY = 28.54;
const inward = mul(outward, -1);
const top = rungs[rungs.length - 1];
const path = [
  ['stepoff', -0.95, 4.62, deckY, 0.78], ['stepoff', -0.70, 4.55, deckY, 0.78],
  ['door', 0.00, 4.45, deckY, 0.78], ['door', 0.00, 4.30, deckY, 0.78], ['door', 0.00, 4.18, 29.00, 0.55],
  ['door', 0.00, 4.02, 29.02, 0.50], ['door', 0.00, 3.88, 29.02, 0.50], ['entry', 0.00, 3.70, 29.00, 0.55],
  ['entry', -0.10, 3.55, 28.95, 0.58],
];
const spots = [];
for (let i = 0; i < path.length; i++) {
  spots.push({ tag: path[i][0], at: { x: path[i][1], y: path[i][3], z: path[i][2] }, hip: path[i][4] });
  if (i + 1 < path.length) {
    const a = path[i], b = path[i + 1];
    for (const u of [0.33, 0.66]) {
      const m = (k) => a[k] + (b[k] - a[k]) * u;
      spots.push({ tag: a[0], at: { x: m(1), y: m(3), z: m(2) }, hip: m(4) });
    }
  }
}
for (const s of spots) {
  const frame = poseStand(s.at, yaw, outward, s.hip || 0.78);
  const c = clearOf(bodySpheres(frame));
  console.log('SPOT', s.tag, s.at.x.toFixed(2), s.at.z.toFixed(2), 'clear', (c.d * 100).toFixed(1), c.name, c.sphere, 'hip', frame.hip.y.toFixed(2));
  take(s.tag, frame, 0);
}

const report = {
  rungs: rungs.length,
  rungY: [+rungs[0].y.toFixed(4), +rungs[rungs.length - 1].y.toFixed(4)],
  climbSec: +dur.toFixed(3),
  samples: n,
  maxContactCm: +(maxErr * 100).toFixed(3),
  minClearanceCm: +(minClear * 100).toFixed(2),
  minWhere,
  contactPass: maxErr <= 0.01,
  clearancePass: minClear >= 0.03,
  show: showTimes(4, rungs, 6),
  worst: samples.slice().sort((a, b) => a.clearCm - b.clearCm).slice(0, 8),
};
console.log(JSON.stringify({ ...report, worst: report.worst }, null, 2));
// Deck grid: stand clearance, so the step-off and the door walk can be moved onto clear floor.
const grid = [];
if (false) for (let x = -1.7; x <= 0.8; x += 0.25) {
  for (let z = 2.3; z <= 5.15; z += 0.25) {
    const at = { x, y: deckY, z };
    let frame;
    try { frame = poseStand(at, yaw, outward); } catch (e) { continue; }
    const c = clearOf(bodySpheres(frame));
    if (c.d > 0.04) grid.push({ x: +x.toFixed(2), z: +z.toFixed(2), cm: +(c.d * 100).toFixed(1), hit: c.name });
  }
}
grid.sort((a, b) => b.cm - a.cm);
report.clearDeck = grid.slice(0, 24);
console.log('clear deck', report.clearDeck.length, report.clearDeck.slice(0, 12));
fs.writeFileSync('qa/art/ladder_1720/climb_report.json', JSON.stringify(report, null, 2));
if (!report.contactPass || !report.clearancePass) process.exit(2);
