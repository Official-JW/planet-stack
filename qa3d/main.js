// Planet Stack QA3D: Mine A loop on placeholders (drill mines on its own + rover deposit bonus).
// Fixed camera, one-station swipes, upgrade sheet, offline catch-up, Eve placeholder, ?dev=1 readout.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// ===== balance: all tuning lives here (Director may retune) =====
const CFG = {
  startMoney: 500, startCrystals: 0,
  oreValue: 1,                          // $ per ore
  drillRate0: 6, drillRatePerLvl: 3,    // ore/min at Lv1, + per level
  drillCost0: 15, drillCostGrowth: 1.65,// Lv1→2 costs $15, then ×1.65 per level
  drillScalePerLvl: 0.04, drillScaleMax: 1.2,
  binCap0: 3, binCapPerLvl: 1,          // ore per load (bin capacity)
  fullHold: 1.6,                        // s the rig shows 'full' before the load auto-sells
  roverBonus: 8, roverMax: 2, roverCost: 60,          // 2nd rover price
  roverDig: 1.5, roverDump: 0.6, roverLegMin: 1.6, roverLegMax: 2.7,   // round trip 5.3–7.5 s
  depositMax: 2, depositEvery: 8,
  offlineRate: 0.5, offlineCapSec: 4 * 3600, awayCardMin: 5,
  saveEvery: 3,
};
const CAM = { halfW: 7.5, elev: 18, lookY: 2.5 };   // fixed camera: ~15 m wide in portrait, 18° down

const Q = new URLSearchParams(location.search);
const DEV = Q.get('dev') === '1';
const SAVEKEY = DEV ? 'planetstack-qa3d-dev' : 'planetstack-qa3d';
if (Q.has('fresh')) try { localStorage.removeItem(SAVEKEY); } catch (e) {}
const S = { site: 1, money: CFG.startMoney, crystals: CFG.startCrystals, drill: 1, rovers: 1, bin: 0, dep: 0, eve: [], rt: Date.now() };
let hadRt = false;
try { const sv = JSON.parse(localStorage.getItem(SAVEKEY) || '{}'); hadRt = sv.rt > 0; Object.assign(S, sv); } catch (e) {}
if (!Array.isArray(S.eve)) S.eve = [];
if (!(S.rt > 0)) S.rt = Date.now();
const save = () => { try { localStorage.setItem(SAVEKEY, JSON.stringify(S)); } catch (e) {} };

const STATIONS = ['Life Support', 'Mine', 'Takeoff & Landing', 'Cargo Space Dock', 'Habitat', 'Shipyard', 'Engineering'];
const GAP = 40, N = STATIONS.length, MINE = 1, MX = MINE * GAP;
const $ = (id) => document.getElementById(id);
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const ease = (t) => t < .5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;

// ===== economy helpers
const rate = () => CFG.drillRate0 + CFG.drillRatePerLvl * (S.drill - 1);           // ore/min
const binCap = () => CFG.binCap0 + CFG.binCapPerLvl * (S.drill - 1);
const drillCost = () => Math.round(CFG.drillCost0 * CFG.drillCostGrowth ** (S.drill - 1));
const canPay = (c) => DEV || S.money >= c;
const pay = (c) => { if (!DEV) S.money -= c; };
const fmt = (v) => '$' + Math.floor(v).toLocaleString('en-US');

// ===== renderer / scene
const canvas = $('c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));     // capped at 2 (Director OK'd)
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x05060b);
const camera = new THREE.PerspectiveCamera(38, 1, 0.5, 600);

const hemi = new THREE.HemisphereLight(0x9fb4d8, 0x2a2a30, 0.55); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff4e2, 2.6);
sun.castShadow = true; sun.shadow.mapSize.set(1024, 1024);
Object.assign(sun.shadow.camera, { left: -22, right: 22, top: 22, bottom: -22, near: 1, far: 120 });
sun.shadow.bias = -0.0005; sun.shadow.normalBias = 0.03;
scene.add(sun); scene.add(sun.target);

// ground (1 draw)
{
  const W = GAP * (N - 1) + 200, D = 160;
  const g = new THREE.PlaneGeometry(W, D, 220, 80); g.rotateX(-Math.PI / 2);
  const pos = g.attributes.position, col = new Float32Array(pos.count * 3);
  const rnd = (a) => { const s = Math.sin(a * 127.1) * 43758.5453; return s - Math.floor(s); };
  const craters = []; for (let i = 0; i < 70; i++) craters.push([(rnd(i + .3) - .5) * W, (rnd(i + 7.7) - .5) * D - 20, 1.5 + rnd(i + 3.1) * 6]);
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i), z = pos.getZ(i);
    let v = 0.42 + 0.05 * Math.sin(x * .23 + z * .11) + 0.04 * Math.sin(x * .07 - z * .19) + (rnd(x * 3.1 + z * 7.3) - .5) * 0.05;
    for (const [cx, cz, r] of craters) { const d = Math.hypot(x - cx, z - cz) / r; if (d < 1.25) v += d < 1 ? -0.10 * (1 - d * d) : 0.07 * (1.25 - d) * 4 * (d - 1); }
    col[i * 3] = v; col[i * 3 + 1] = v; col[i * 3 + 2] = v * 1.03;
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const ground = new THREE.Mesh(g, new THREE.MeshLambertMaterial({ vertexColors: true }));
  ground.position.set(GAP * (N - 1) / 2, 0, 0); ground.receiveShadow = true; scene.add(ground);
}
// stars (1 draw)
{
  const n = 900, p = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const a = Math.random() * Math.PI * 2, e = .05 + Math.random() * 1.2, r = 400; p[i * 3] = GAP * 3 + Math.cos(a) * r * Math.cos(e); p[i * 3 + 1] = Math.sin(e) * r; p[i * 3 + 2] = -Math.abs(Math.sin(a)) * r * Math.cos(e) - 60; }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 1.2, sizeAttenuation: false })));
}
// gray placeholders for the other stations
const ph = new THREE.MeshStandardMaterial({ color: 0x8a8d94, roughness: .85, metalness: .05 });
const SIZES = [[10, 8, 8], null, [10, 1, 10], [14, 7, 9], [9, 12, 9], [12, 9, 10], [10, 10, 8]];
STATIONS.forEach((name, i) => {
  if (!SIZES[i]) return; const [w, h, d] = SIZES[i];
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), ph);
  m.position.set(i * GAP, h / 2, 0); m.castShadow = m.receiveShadow = true; scene.add(m);
});

// ===== drill rig (Art 8ec3810, md5 c64f9a72…)
let mixer = null, rig = null, oreFill = null, oreBaseY = 1, rigBox = new THREE.Box3(new THREE.Vector3(MX - 3, 0, -3), new THREE.Vector3(MX + 3.2, 10, 3));
const acts = {}; let curAct = null, rigLoaded = false, coverGone = false, rigBump = 0;
const glowMats = [];
function setClip(name) {
  const a = acts[name]; if (!a || a === curAct) return;
  a.reset(); a.setEffectiveWeight(1); a.play();
  if (curAct) curAct.crossFadeTo(a, 0.3, false);
  curAct = a;
}
function rigScale() { return Math.min(1 + CFG.drillScalePerLvl * (S.drill - 1), CFG.drillScaleMax); }
function applyRigLevel() {
  if (!rig) return;
  glowMats.forEach(m => m.emissiveIntensity = m.userData.ei0 * (1 + 0.12 * Math.min(S.drill - 1, 8)));
}
// the cover never fades onto empty ground: it stays until the rig is in the scene
let coverTimer = 0;
function armCoverTimer() { clearTimeout(coverTimer); coverTimer = setTimeout(() => { if (!rigLoaded) { console.warn('drill_rig still loading after 15 s'); $('coverTx').textContent = 'Still loading…'; } }, 15000); }
armCoverTimer();
function hideCover() {
  const c = $('cover'); if (!c || c.classList.contains('off')) return; clearTimeout(coverTimer); c.classList.add('off');
  setTimeout(() => { c.remove(); coverGone = true; }, 420);
}
const loader = new GLTFLoader(); loader.setMeshoptDecoder(MeshoptDecoder);
function loadRig() { loader.load('../art/3d/drill_rig/drill_rig.glb?v=c64f9a72', (gltf) => {
  rig = gltf.scene; rig.position.set(MX, 0, 0);
  rig.traverse(o => {
    if (o.isMesh) { o.castShadow = true; o.receiveShadow = true;
      const m = o.material; if (m && m.emissive && m.emissive.getHex() && !glowMats.includes(m)) { m.userData.ei0 = m.emissiveIntensity; glowMats.push(m); } }
  });
  scene.add(rig);
  rig.updateMatrixWorld(true);
  rigBox = new THREE.Box3().setFromObject(rig);
  // footprint at the largest rig scale, + margin, used to keep deposits and rover paths off the rig
  const k = CFG.drillScaleMax;
  rigBox.min.x = MX + (rigBox.min.x - MX) * k - .6; rigBox.max.x = MX + (rigBox.max.x - MX) * k + .6;
  rigBox.min.z = rigBox.min.z * k - .6; rigBox.max.z = rigBox.max.z * k + .6;
  rig.scale.setScalar(rigScale());
  oreFill = rig.getObjectByName('OreFill'); if (oreFill) oreBaseY = oreFill.scale.y;
  mixer = new THREE.AnimationMixer(rig);
  for (const c of gltf.animations) acts[c.name] = mixer.clipAction(c);
  setClip(S.bin >= binCap() ? 'full' : 'dig');
  applyRigLevel();
  rigLoaded = true;
  renderer.compile(scene, camera);
  requestAnimationFrame(() => requestAnimationFrame(hideCover));   // fade only once the rig has been drawn
  Object.assign(window.__ps3d, { rig, clips: gltf.animations.map(a => a.name), rigBox });
}, undefined, (e) => {
  console.error('drill_rig load failed', e); clearTimeout(coverTimer);
  $('coverTx').textContent = "Couldn't load the Mine"; $('coverSp').hidden = true; $('coverRetry').hidden = false;
}); }
$('coverRetry').addEventListener('click', () => {
  $('coverRetry').hidden = true; $('coverSp').hidden = false; $('coverTx').textContent = 'Loading Moonbase…'; armCoverTimer(); loadRig();
});
loadRig();

// ===== camera framing (fixed camera, ~14 m wide in portrait)
let camX = S.site * GAP, target = camX, W = 1, H = 1;
function camDist(aspect) {
  const vt = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
  return Math.max(CAM.halfW / (vt * aspect), 7.2 / vt, 16);
}
function resize() {
  W = innerWidth; H = innerHeight; renderer.setSize(W, H, false);
  camera.aspect = W / H; camera.userData.dist = camDist(camera.aspect); camera.updateProjectionMatrix();
}
addEventListener('resize', resize); resize();
function poseCam(cam, x) {
  const d = camera.userData.dist, e = THREE.MathUtils.degToRad(CAM.elev);
  cam.position.set(x, CAM.lookY + d * Math.sin(e), d * Math.cos(e)); cam.lookAt(x, CAM.lookY, 0); cam.updateMatrixWorld();
}
function placeCamera() { poseCam(camera, camX); sun.position.set(camX - 30, 22, 18); sun.target.position.set(camX, 0, 0); }
const _v = new THREE.Vector3();
function toScreen(x, y, z, cam = camera) { _v.set(x, y, z).project(cam); return { x: (_v.x + 1) / 2 * W, y: (1 - _v.y) / 2 * H, z: _v.z }; }
const mPerPx = () => (2 * camera.userData.dist * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect) / W;

// ===== UI: tag, name, dots
$('tag').textContent = document.body.dataset.tag + (DEV ? ' · DEV' : '');
const nameEl = $('name'), dotsEl = $('dots');
STATIONS.forEach((n, i) => { const b = document.createElement('button'); b.setAttribute('aria-label', n); dotsEl.appendChild(b); });
function ui() { nameEl.textContent = STATIONS[S.site]; [...dotsEl.children].forEach((b, i) => b.classList.toggle('on', i === S.site)); }
function goSite(k) { k = clamp(k, 0, N - 1); if (k !== S.site) { S.site = k; save(); } target = k * GAP; ui(); }
dotsEl.addEventListener('pointerdown', (e) => {   // 44 px tap band: nearest dot wins
  e.stopPropagation(); const r = dotsEl.getBoundingClientRect(); goSite(Math.round((e.clientX - r.left) / r.width * N - .5));
});
ui();

// ===== swipe: always exactly one station from S.site; tiny drags spring back; taps go to deposits
let drag = null;
canvas.addEventListener('pointerdown', (e) => {
  if (drag) return; const t = e.timeStamp || performance.now();     // event time, so a busy frame can't distort the flick speed
  drag = { id: e.pointerId, x0: e.clientX, y0: e.clientY, t0: t, cx: camX, s: [[t, e.clientX]], moved: 0 };
  try { canvas.setPointerCapture(e.pointerId); } catch (_) {}
});
canvas.addEventListener('pointermove', (e) => {
  if (!drag || e.pointerId !== drag.id) return; const t = e.timeStamp || performance.now();
  const dx = e.clientX - drag.x0; drag.moved = Math.max(drag.moved, Math.hypot(dx, e.clientY - drag.y0));
  const lo = Math.max((S.site - 1) * GAP, -GAP * .3), hi = Math.min((S.site + 1) * GAP, GAP * (N - 1 + .3));
  camX = clamp(drag.cx - dx * mPerPx(), lo, hi);
  drag.s.push([t, e.clientX]); while (drag.s.length > 2 && t - drag.s[1][0] > 250) drag.s.shift();
});
function releaseVelocity(d, t, x) {        // average px/ms over the last 80 ms (position held between samples)
  const w0 = t - 80; let base = null;
  for (const s of d.s) if (s[0] <= w0) base = s;
  if (!base) return (x - d.x0) / Math.max(t - d.t0, 16);
  return (x - base[1]) / 80;
}
function endDrag(e) {
  if (!drag || (e && e.pointerId !== drag.id)) return;
  const t = (e && e.timeStamp) || performance.now(), x = e ? e.clientX : drag.s[drag.s.length - 1][1];
  const dx = x - drag.x0, v = releaseVelocity(drag, t, x), d = drag; drag = null;
  let dir = 0;
  if (Math.abs(dx) > 0.15 * W) dir = dx < 0 ? 1 : -1;
  else if (Math.abs(v) > 0.35 && Math.abs(dx) > 8) dir = v < 0 ? 1 : -1;
  window.__ps3d.lastSwipe = { dx, v: +v.toFixed(3), dir };
  if (!dir && d.moved < 10 && t - d.t0 < 500 && e && e.type === 'pointerup') tap(e.clientX, e.clientY);
  goSite(S.site + dir);
}
canvas.addEventListener('pointerup', endDrag); canvas.addEventListener('pointercancel', endDrag);

// ===== HUD
const moneyEl = $('money'), rateEl = $('rate'), cryEl = $('cry'), binEl = $('bin'), binFill = binEl.firstElementChild;
let lastMoneyTxt = '';
function hud() {
  const mt = DEV ? '∞' : fmt(S.money); if (mt !== lastMoneyTxt) { moneyEl.textContent = mt; lastMoneyTxt = mt; }
  rateEl.textContent = rate();
  cryEl.textContent = DEV ? '∞' : S.crystals;
  binFill.style.width = (100 * Math.min(1, S.bin / binCap())).toFixed(1) + '%';
  binEl.classList.toggle('full', fullT > 0);
}
function bumpMoney() { moneyEl.classList.remove('bump'); void moneyEl.offsetWidth; moneyEl.classList.add('bump'); }
function pop(text, x, y, cls = '') {
  const el = document.createElement('div'); el.className = 'pop ' + cls; el.textContent = text;
  el.style.left = x + 'px'; el.style.top = y + 'px'; document.body.appendChild(el); setTimeout(() => el.remove(), 1150);
}
function moneyXY() { const r = moneyEl.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }

// ===== ore chunks: 2 instanced meshes (He-3 cyan glow, platinum silver), fly from the hopper to the money counter
const CH_MAX = 32;
const chGeo = new THREE.BoxGeometry(.34, .34, .34);
const chMesh = [
  new THREE.InstancedMesh(chGeo, new THREE.MeshStandardMaterial({ color: 0x46e6ff, emissive: 0x20c8ff, emissiveIntensity: 1.6, roughness: .4 }), CH_MAX),
  new THREE.InstancedMesh(chGeo, new THREE.MeshStandardMaterial({ color: 0xdfe4ec, metalness: .9, roughness: .28, emissive: 0x30343a }), CH_MAX),
];
const ZERO = new THREE.Matrix4().makeScale(0, 0, 0);
chMesh.forEach(m => { m.frustumCulled = false; for (let i = 0; i < CH_MAX; i++) m.setMatrixAt(i, ZERO); scene.add(m); });
const chunks = []; const freeIdx = [[...Array(CH_MAX).keys()], [...Array(CH_MAX).keys()]];
const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _e = new THREE.Euler(), _s = new THREE.Vector3(), _p = new THREE.Vector3(), _t = new THREE.Vector3();
function counterWorld(out) {         // money counter's screen point, 12 m in front of the camera
  const m = moneyXY(); out.set(m.x / W * 2 - 1, -(m.y / H) * 2 + 1, 0.5).unproject(camera);
  return out.sub(camera.position).normalize().multiplyScalar(12).add(camera.position);
}
function flyChunks(n, from, value, cls) {
  n = Math.min(n, 12); let first = true;
  for (let i = 0; i < n; i++) {
    const kind = i % 3 === 2 ? 1 : 0; const idx = freeIdx[kind].pop(); if (idx === undefined) continue;
    chunks.push({ kind, idx, t: -i * 0.07, dur: 0.75 + Math.random() * .15, p0: from.clone().add(new THREE.Vector3((Math.random() - .5) * .8, Math.random() * .4, (Math.random() - .5) * .6)),
      up: 2.5 + Math.random() * 2, spin: Math.random() * 6, done: first ? () => { const m = moneyXY(); pop('+' + fmt(value), m.x, m.y + 30, cls); bumpMoney(); } : null });
    first = false;
  }
  if (!n || first) { const m = moneyXY(); pop('+' + fmt(value), m.x, m.y + 30, cls); bumpMoney(); }
}
function updChunks(dt) {
  if (!chunks.length) return; counterWorld(_t);
  for (let i = chunks.length - 1; i >= 0; i--) {
    const c = chunks[i]; c.t += dt; const u = clamp(c.t / c.dur, 0, 1), k = ease(u);
    if (c.t < 0) { chMesh[c.kind].setMatrixAt(c.idx, ZERO); continue; }
    _p.copy(c.p0).lerp(_t, k); _p.y += Math.sin(u * Math.PI) * c.up * (1 - u * .5);
    _s.setScalar(1 - .55 * u); _q.setFromEuler(_e.set(c.spin * u, c.spin * .7 * u, 0));
    chMesh[c.kind].setMatrixAt(c.idx, _m.compose(_p, _q, _s));
    if (u >= 1) { chMesh[c.kind].setMatrixAt(c.idx, ZERO); freeIdx[c.kind].push(c.idx); if (c.done) c.done(); chunks.splice(i, 1); }
  }
  chMesh.forEach(m => m.instanceMatrix.needsUpdate = true);
}

// ===== mine sim: drill fills the bin; when full it shows 'full', then the load auto-sells
let fullT = 0;
const hopperPos = () => new THREE.Vector3(MX + 1.85 * rigScale(), 4.4 * rigScale(), -.35);
function sellLoad() {
  const n = Math.floor(S.bin + 1e-6); S.bin = Math.max(0, S.bin - n);
  const value = n * CFG.oreValue; S.money += value; setClip('dig');
  window.__ps3d.loads = (window.__ps3d.loads || 0) + 1;
  if (S.site === MINE) flyChunks(Math.max(3, n * 2), hopperPos(), value); else bumpMoney();
}
function simMine(dt) {
  if (fullT > 0) { fullT -= dt; if (fullT <= 0) { fullT = 0; sellLoad(); } return; }
  S.bin += rate() / 60 * dt;
  if (S.bin >= binCap()) { S.bin = binCap(); fullT = CFG.fullHold; setClip('full'); }
}

// ===== deposits: glowing cyan disc + floating gem, max 2, respawn every ~8 s, only inside the middle screen band
const glowTex = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
  const r = g.createRadialGradient(64, 64, 4, 64, 64, 64);
  r.addColorStop(0, '#e8ffffff'); r.addColorStop(.35, '#58ecffdd'); r.addColorStop(.7, '#1fb8ff66'); r.addColorStop(1, '#1fb8ff00');
  g.fillStyle = r; g.fillRect(0, 0, 128, 128); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
})();
const discGeo = new THREE.CircleGeometry(1.5, 32).rotateX(-Math.PI / 2);
const discMat = new THREE.MeshBasicMaterial({ map: glowTex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
const gemGeo = new THREE.OctahedronGeometry(.42, 0); gemGeo.scale(1, 1.5, 1);
const gemMat = new THREE.MeshStandardMaterial({ color: 0x5ff0ff, emissive: 0x22d0ff, emissiveIntensity: 1.8, roughness: .3, flatShading: true });
const deposits = []; let depTimer = 0, depSeq = 0;
function band() {
  const eveR = $('eve').getBoundingClientRect();
  const top = Math.max(eveR.top + Math.max(eveR.height, 120), $('name').getBoundingClientRect().bottom) + 24;
  const sheetTop = $('sheetWrap').getBoundingClientRect().top;      // open sheet top edge
  return { top, bot: Math.min(sheetTop, dotsEl.getBoundingClientRect().top) - 34, l: 34, r: W - 34 };
}
const homes = () => [new THREE.Vector3(rigBox.max.x + .4, 0, rigBox.max.z + .4), new THREE.Vector3(rigBox.max.x + .5, 0, rigBox.max.z - 2.8)];   // right-front, by the hopper
function spawnDeposit() {
  if (deposits.length >= CFG.depositMax) return null;
  const mc = camera.clone(); poseCam(mc, MX); const b = band(); const hs = homes();
  for (let tries = 0; tries < 60; tries++) {
    // front strip (between the rig and the sheet) or behind-left/right of the tower
    let x, z; if (Math.random() < .75) { x = MX + (Math.random() * 2 - 1) * 6.2; z = rigBox.max.z + .6 + Math.random() * 4.5; }
    else { x = MX + (Math.random() < .5 ? -1 : 1) * (4.2 + Math.random() * 2); z = -11 + Math.random() * 5; }
    if (x > rigBox.min.x - 1 && x < rigBox.max.x + 1 && z > rigBox.min.z - 1 && z < rigBox.max.z + 1) continue;
    if (hs.some(h => Math.hypot(h.x - x, h.z - z) < 2.6)) continue;
    if (deposits.some(d => Math.hypot(d.x - x, d.z - z) < 3.5)) continue;
    const p = toScreen(x, 0.6, z, mc), e1 = toScreen(x - 1.5, 0, z, mc), e2 = toScreen(x + 1.5, 0, z, mc);
    if (p.x < b.l || p.x > b.r || e1.x < 8 || e2.x > W - 8 || p.y - 40 < b.top || p.y + 22 > b.bot) continue;
    const disc = new THREE.Mesh(discGeo, discMat); disc.position.set(x, 0.04, z); disc.renderOrder = 2;
    const gem = new THREE.Mesh(gemGeo, gemMat); gem.position.set(x, 1, z); gem.castShadow = false;
    scene.add(disc, gem);
    const d = { id: ++depSeq, x, z, disc, gem, age: 0, claimed: false, dig: 0 }; deposits.push(d); return d;
  }
  return null;
}
function removeDeposit(d) { scene.remove(d.disc, d.gem); deposits.splice(deposits.indexOf(d), 1); }
function updDeposits(dt, time) {
  depTimer += dt;
  if (deposits.length < CFG.depositMax && depTimer >= CFG.depositEvery) { depTimer = 0; spawnDeposit(); }
  if (deposits.length >= CFG.depositMax) depTimer = 0;
  for (const d of deposits) {
    d.age += dt; const pin = d.age < .35 ? 1 - (1 - d.age / .35) ** 3 * (1 - 1.7 * (d.age / .35)) : 1;
    const shrink = d.claimed ? 1 - .85 * d.dig : 1, pulse = 1 + .1 * Math.sin(time * 4 + d.id);
    d.disc.scale.setScalar(Math.max(.01, pin * pulse * shrink));
    d.gem.scale.setScalar(Math.max(.01, pin * shrink)); d.gem.rotation.y = time * 1.6 + d.id;
    d.gem.position.y = 1 + .18 * Math.sin(time * 2.6 + d.id);
  }
}

// ===== rovers: placeholder box body + 4 cylinder wheels (2 draws each)
const roverBodyGeo = mergeGeometries([
  new THREE.BoxGeometry(1.5, .55, 2.3).translate(0, .78, 0),
  new THREE.BoxGeometry(1.2, .5, .9).translate(0, 1.3, -.45),
  new THREE.BoxGeometry(1.3, .35, .5).translate(0, .7, 1.35),
]);
const roverWheelGeo = mergeGeometries([[-.78, .8], [.78, .8], [-.78, -.8], [.78, -.8]].map(([x, z]) => new THREE.CylinderGeometry(.4, .4, .32, 14).rotateZ(Math.PI / 2).translate(x, .4, z)));
const roverBodyMat = new THREE.MeshStandardMaterial({ color: 0xe6e9ef, roughness: .6, metalness: .1 });
const roverWheelMat = new THREE.MeshStandardMaterial({ color: 0x2b2f38, roughness: .9 });
const rovers = [];
const ringTpl = $('ring');
function addRover(i, popIn) {
  const g = new THREE.Group(); const body = new THREE.Mesh(roverBodyGeo, roverBodyMat); body.castShadow = true;
  const wheels = new THREE.Mesh(roverWheelGeo, roverWheelMat); g.add(body, wheels);
  const h = homes()[i]; g.position.copy(h); g.rotation.y = 0; scene.add(g);
  const ring = ringTpl.cloneNode(true); ring.id = ''; document.body.appendChild(ring);
  const r = { i, g, body, ring, arc: ring.querySelector('circle:last-child'), phase: 'idle', t: 0, path: null, len: 0, leg: 0, dep: null, yaw: 0, pin: popIn ? 0 : 1, t0: 0 };
  rovers.push(r); return r;
}
function segHitsBox(a, b, bx) {      // 2D (x,z) segment vs rect, Liang–Barsky
  let t0 = 0, t1 = 1; const dx = b.x - a.x, dz = b.z - a.z;
  for (const [p, q] of [[-dx, a.x - bx.min.x], [dx, bx.max.x - a.x], [-dz, a.z - bx.min.z], [dz, bx.max.z - a.z]]) {
    if (p === 0) { if (q < 0) return false; continue; }
    const r = q / p; if (p < 0) { if (r > t1) return false; if (r > t0) t0 = r; } else { if (r < t0) return false; if (r < t1) t1 = r; }
  }
  return true;
}
function planPath(a, b) {
  const F = rigBox.max.z + 1.4, B = rigBox.min.z - 1.4, L = rigBox.min.x - 1, R = rigBox.max.x + 1;
  const v = (x, z) => new THREE.Vector3(x, 0, z);
  const opts = [[a, b], [a, v(L, F), b], [a, v(L, F), v(R, F), b], [a, v(L, B), b], [a, v(L, B), v(R, B), b]];
  let best = null, bl = Infinity;
  for (const p of opts) {
    let ok = true, len = 0; for (let i = 1; i < p.length; i++) { if (segHitsBox(p[i - 1], p[i], rigBox)) ok = false; len += p[i - 1].distanceTo(p[i]); }
    if (ok && len < bl) { bl = len; best = p; }
  }
  return best || [a, b];
}
function pathAt(path, u, out) {
  let total = 0; for (let i = 1; i < path.length; i++) total += path[i - 1].distanceTo(path[i]);
  let d = u * total;
  for (let i = 1; i < path.length; i++) { const s = path[i - 1].distanceTo(path[i]); if (d <= s || i === path.length - 1) return out.copy(path[i - 1]).lerp(path[i], s ? clamp(d / s, 0, 1) : 1); d -= s; }
  return out.copy(path[path.length - 1]);
}
function sendRover(d) {
  const r = rovers.find(r => r.phase === 'idle' && r.pin >= 1); if (!r) return false;
  d.claimed = true; r.dep = d; const home = homes()[r.i];
  r.path = planPath(home, new THREE.Vector3(d.x, 0, d.z));
  let len = 0; for (let i = 1; i < r.path.length; i++) len += r.path[i - 1].distanceTo(r.path[i]);
  r.len = len; r.leg = clamp(1.2 + len / 8, CFG.roverLegMin, CFG.roverLegMax);
  r.phase = 'out'; r.t = 0; r.t0 = performance.now(); r.sim = 0; return true;
}
const _rp = new THREE.Vector3(), _rq = new THREE.Vector3();
function updRovers(dt, time) {
  for (const r of rovers) {
    if (r.pin < 1) { r.pin = Math.min(1, r.pin + dt / .4); r.g.scale.setScalar(ease(r.pin)); }
    r.t += dt; if (r.phase !== 'idle') r.sim += dt; let show = false;
    if (r.phase === 'out' || r.phase === 'back') {
      const u = clamp(r.t / r.leg, 0, 1), k = ease(u), uu = r.phase === 'out' ? k : 1 - k;
      pathAt(r.path, uu, _rp); pathAt(r.path, clamp(uu + (r.phase === 'out' ? .02 : -.02), 0, 1), _rq);
      if (_rq.distanceToSquared(_rp) > 1e-6) { const yaw = Math.atan2(_rq.x - _rp.x, _rq.z - _rp.z); let dy = yaw - r.yaw; dy = Math.atan2(Math.sin(dy), Math.cos(dy)); r.yaw += dy * Math.min(1, dt * 10); }
      r.g.position.copy(_rp); r.g.rotation.set(0, r.yaw, 0);
      if (u >= 1) { r.t = 0; if (r.phase === 'out') r.phase = 'dig'; else { r.phase = 'dump'; } }
    } else if (r.phase === 'dig') {
      const u = clamp(r.t / CFG.roverDig, 0, 1); if (r.dep) r.dep.dig = u; show = true;
      r.g.position.y = Math.abs(Math.sin(time * 18)) * .06; r.g.rotation.x = Math.sin(time * 22) * .03;
      r.arc.setAttribute('stroke-dashoffset', (113.1 * (1 - u)).toFixed(1));
      if (u >= 1) { if (r.dep) removeDeposit(r.dep); r.dep = null; r.phase = 'back'; r.t = 0; r.g.position.y = 0; r.g.rotation.x = 0; }
    } else if (r.phase === 'dump') {
      const u = clamp(r.t / CFG.roverDump, 0, 1);
      r.g.rotation.set(-Math.sin(u * Math.PI) * .35, r.yaw, 0);
      if (u >= 1) {
        r.phase = 'idle'; r.g.rotation.set(0, r.yaw, 0);
        S.money += CFG.roverBonus; S.dep++; save();
        const ms = performance.now() - r.t0; (window.__ps3d.trips = window.__ps3d.trips || []).push({ wall: Math.round(ms), sim: Math.round(r.sim * 1000) });
        const sp = toScreen(r.g.position.x, 2.2, r.g.position.z);
        if (S.site === MINE) { pop('+' + fmt(CFG.roverBonus) + ' bonus', sp.x, sp.y, 'bonus'); flyChunks(4, r.g.position.clone().add(new THREE.Vector3(0, 1.2, 0)), CFG.roverBonus, 'bonus'); }
      }
    } else if (r.phase === 'idle') {
      const h = homes()[r.i]; r.g.position.lerp(h, Math.min(1, dt * 4));
      let dy = 0 - r.yaw; dy = Math.atan2(Math.sin(dy), Math.cos(dy)); r.yaw += dy * Math.min(1, dt * 5); r.g.rotation.set(0, r.yaw, 0);
    }
    if (show) { const p = toScreen(r.g.position.x, 2.6, r.g.position.z); r.ring.style.left = p.x + 'px'; r.ring.style.top = p.y + 'px'; }
    r.ring.style.display = show ? 'block' : 'none';
  }
}

// ===== taps on the 3D scene (deposits): screen-space hit test, radius ≥ 44 px
function tap(x, y) {
  if (S.site !== MINE || Math.abs(camX - MX) > 3) return;
  let best = null, bd = Infinity;
  for (const d of deposits) {
    if (d.claimed) continue;
    const c = toScreen(d.x, 0.6, d.z), e = toScreen(d.x + 1.5, 0, d.z);
    const R = Math.max(44, Math.abs(e.x - c.x) * 1.1), dist = Math.hypot(x - c.x, y - c.y);
    if (dist < R && dist < bd) { bd = dist; best = d; }
  }
  if (!best) return;
  if (sendRover(best)) { if (eveCur && eveCur.point === 'deposit') pointerDone = true; }
  else pop('Rovers busy', x, y - 20, 'info');
}

// ===== upgrade sheet (drag up/down, springs to open or closed)
const sheet = $('sheet'), grab = $('grab'), PEEK = 46;
let sheetOpen = false, sheetDrag = null;
const closedY = () => sheet.offsetHeight - PEEK;
function setSheet(open) { sheetOpen = open; sheet.classList.remove('dragging'); sheet.style.transform = `translateY(${open ? 0 : closedY()}px)`; if (open && eveCur && eveCur.point === 'upgrade') pointerDone = true; }
setSheet(false);
grab.addEventListener('pointerdown', (e) => { e.stopPropagation(); sheetDrag = { y0: e.clientY, b: sheetOpen ? 0 : closedY(), s: [[performance.now(), e.clientY]], moved: 0 }; sheet.classList.add('dragging'); try { grab.setPointerCapture(e.pointerId); } catch (_) {} });
grab.addEventListener('pointermove', (e) => {
  if (!sheetDrag) return; const dy = e.clientY - sheetDrag.y0; sheetDrag.moved = Math.max(sheetDrag.moved, Math.abs(dy));
  let y = sheetDrag.b + dy; const c = closedY(); if (y < 0) y = y * .3; if (y > c) y = c + (y - c) * .3;
  sheet.style.transform = `translateY(${y}px)`; sheetDrag.y = y; sheetDrag.s.push([performance.now(), e.clientY]); if (sheetDrag.s.length > 8) sheetDrag.s.shift();
});
const endSheet = (e) => {
  if (!sheetDrag) return; const d = sheetDrag; sheetDrag = null;
  if (d.moved < 6) return setSheet(!sheetOpen);
  const a = d.s[0], b = d.s[d.s.length - 1], v = (b[1] - a[1]) / Math.max(16, b[0] - a[0]);
  if (v > 0.3) setSheet(false); else if (v < -0.3) setSheet(true); else setSheet((d.y ?? d.b) < closedY() / 2);
};
grab.addEventListener('pointerup', endSheet); grab.addEventListener('pointercancel', endSheet);
sheet.addEventListener('pointerdown', (e) => e.stopPropagation());
const bDrill = $('bDrill'), bRover = $('bRover');
function sheetUI() {
  const c = drillCost(), ok = canPay(c);
  $('dLvl').textContent = 'Lv ' + S.drill; $('dGain').textContent = `${rate()} ore/min → next +${CFG.drillRatePerLvl} ore/min`;
  bDrill.textContent = ok ? fmt(c) : 'need ' + fmt(c); bDrill.className = ok ? '' : 'need';
  $('rLvl').textContent = S.rovers + '/' + CFG.roverMax;
  if (S.rovers >= CFG.roverMax) { $('rGain').textContent = `Max · ${fmt(CFG.roverBonus)} per deposit`; bRover.textContent = 'Max'; bRover.className = 'max'; }
  else { const ok2 = canPay(CFG.roverCost); $('rGain').textContent = `+1 rover · ${fmt(CFG.roverBonus)} per deposit`; bRover.textContent = ok2 ? fmt(CFG.roverCost) : 'need ' + fmt(CFG.roverCost); bRover.className = ok2 ? '' : 'need'; }
  $('sum').textContent = `Drill Lv ${S.drill} · ${S.rovers} rover${S.rovers > 1 ? 's' : ''}`;
  $('canDot').hidden = !(canPay(c) || (S.rovers < CFG.roverMax && canPay(CFG.roverCost)));
}
bDrill.addEventListener('click', () => {
  const c = drillCost(); if (!canPay(c)) return;
  pay(c); S.drill++; rigBump = 1; applyRigLevel(); save(); sheetUI(); hud();
  if (fullT > 0 && S.bin < binCap()) { fullT = 0; setClip('dig'); }
  const r = bDrill.getBoundingClientRect(); pop('Drill Lv ' + S.drill, r.left + r.width / 2, r.top - 8, 'info');
});
bRover.addEventListener('click', () => {
  if (S.rovers >= CFG.roverMax || !canPay(CFG.roverCost)) return;
  pay(CFG.roverCost); S.rovers++; addRover(S.rovers - 1, true); save(); sheetUI(); hud();
});

// ===== Eve placeholder radio calls
const EVE_BEATS = [
  { id: 'mine_first_view', point: 'deposit', text: "Moonbase, this is Eve at Earth Coms. Good to hear you made it. First job: get that mine running. Tap where I'm pointing." },
  { id: 'first_deposit', point: null, text: "Nice haul. Every deposit your rover digs pays a bonus on top of the drill. Watch for the glow." },
  { id: 'upgrade_ready', point: 'upgrade', text: "You've got the cash for an upgrade. Bigger mine, bigger loads. Tap Upgrade." },
];
const EVE_TRIG = {
  mine_first_view: () => S.site === MINE && coverGone && Math.abs(camX - MX) < 1,
  first_deposit: () => S.dep >= 1,
  upgrade_ready: () => S.dep >= 1 && canPay(drillCost()) && !sheetOpen,
};
const eveEl = $('eve'), eveTx = $('eveTx'), pointEl = $('point');
let eveCur = null, eveTyped = 0, eveTimer = 0, pointerDone = false, pointBeat = null;
function eveShow(b) {
  eveCur = b; eveTyped = 0; eveTx.textContent = ''; eveEl.classList.add('on');
  S.eve.push(b.id); save();                    // heard as soon as it plays: never repeats, even after reload
  pointBeat = b.point; pointerDone = false;
  if (b.point === 'deposit' && !deposits.some(d => !d.claimed)) spawnDeposit();
  window.__ps3d.eveShown = (window.__ps3d.eveShown || []).concat(b.id);
}
function eveClose() { eveEl.classList.remove('on'); eveCur = null; }
$('eveOver').addEventListener('click', eveClose); $('eveX').addEventListener('click', eveClose);
eveEl.addEventListener('pointerdown', (e) => { e.stopPropagation(); if (eveCur) eveTyped = eveCur.text.length; });
function updEve(dt) {
  if (eveCur && eveTyped < eveCur.text.length) { eveTimer += dt; while (eveTimer > .028 && eveTyped < eveCur.text.length) { eveTimer -= .028; eveTyped++; } eveTx.textContent = eveCur.text.slice(0, eveTyped); }
  if (!eveCur) for (const b of EVE_BEATS) if (!S.eve.includes(b.id) && EVE_TRIG[b.id]()) { eveShow(b); break; }
  // pointer arrow
  let p = null;
  if (pointBeat && !pointerDone) {
    if (pointBeat === 'deposit' && S.site === MINE) { const d = deposits.find(d => !d.claimed); if (d) { const s = toScreen(d.x, 1.3, d.z); p = { x: s.x, y: s.y - 4, l: 'TAP HERE' }; } }
    if (pointBeat === 'upgrade') { const r = grab.getBoundingClientRect(); p = { x: r.left + r.width / 2, y: r.top + 4, l: 'UPGRADE' }; }
  }
  pointEl.style.display = p ? 'block' : 'none';
  if (p) { pointEl.style.left = p.x + 'px'; pointEl.style.top = p.y + 'px'; pointEl.firstChild.textContent = p.l; }
}

// ===== away catch-up: 50% drill rate for time since S.rt, capped 4 h, never for negative time
const awayEl = $('away');
$('awayOk').addEventListener('click', () => awayEl.classList.remove('on'));
awayEl.addEventListener('pointerdown', (e) => e.stopPropagation());
function catchUp(card) {
  const now = Date.now(), el = (now - S.rt) / 1000; S.rt = now;
  if (!(el > 0)) { window.__ps3d.lastAway = { sec: Math.round(el), X: 0 }; return 0; }   // clock set backward or no time: nothing
  const sec = Math.min(el, CFG.offlineCapSec), X = rate() / 60 * CFG.oreValue * CFG.offlineRate * sec;
  S.money += X; save();
  if (card && el > CFG.awayCardMin && Math.floor(X) >= 1) { $('awayAmt').textContent = '+' + fmt(X); awayEl.classList.add('on'); clearTimeout(catchUp.t); catchUp.t = setTimeout(() => awayEl.classList.remove('on'), 9000); }
  window.__ps3d.lastAway = { sec: Math.round(el), X: +X.toFixed(2) };
  return X;
}
document.addEventListener('visibilitychange', () => {
  if (document.hidden) save(); else { catchUp(true); clock.getDelta(); }
});
addEventListener('pagehide', save);

// ===== starting rovers
for (let i = 0; i < S.rovers; i++) addRover(i, false);

// ===== loop + ?dev=1 readout (fps, min fps over last 5 s, draws, tris)
const devEl = $('dev'); devEl.hidden = !DEV; if (DEV) devEl.textContent = 'measuring…';
const clock = new THREE.Clock(); let frames = 0, acc = 0, fps = 0, saveT = 0, uiT = 0, time = 0; const hist = [];
renderer.info.autoReset = true;
function frame() {
  requestAnimationFrame(frame);
  const dt = Math.min(clock.getDelta(), document.hidden ? 0.1 : 0.25); time += dt; window.__ps3d.frames = (window.__ps3d.frames || 0) + 1;
  // simulated-time bookkeeping: S.rt advances only by what we simulate; anything bigger is paid by catchUp()
  const now = Date.now();
  if (now < S.rt - 1000) S.rt = now;                              // clock went backward mid-session: credit nothing
  if (!document.hidden) {
    const lag = (now - S.rt) / 1000;
    if (lag > 60) catchUp(true);                                  // page was frozen without a visibilitychange
    else { let left = Math.max(0, lag); while (left > 1e-4) { const st = Math.min(.1, left); simMine(st); left -= st; } S.rt = now; }   // slow frames: full-rate sim in ≤0.1 s steps
  } else { simMine(dt); S.rt = Math.min(now, S.rt + dt * 1000); } // hidden-tab trickle: only clamped dt; the rest is paid by catchUp() at 50%
  if (!drag) camX += (target - camX) * (1 - Math.exp(-dt * 9));
  placeCamera();
  if (mixer) mixer.update(dt);
  if (rig) {
    if (rigBump > 0) rigBump = Math.max(0, rigBump - dt * 2.2);
    rig.scale.setScalar(rigScale() * (1 + 0.1 * Math.sin(rigBump * Math.PI) * rigBump));
    if (oreFill) oreFill.scale.y = oreBaseY * (0.06 + 0.94 * Math.min(1, S.bin / binCap()));
  }
  updDeposits(dt, time); updRovers(dt, time); updChunks(dt);
  updEve(dt);
  uiT += dt; if (uiT > .1) { uiT = 0; hud(); sheetUI(); }
  saveT += dt; if (saveT > CFG.saveEvery) { saveT = 0; save(); }
  renderer.render(scene, camera);
  if (DEV) {
    frames++; acc += dt;
    if (acc >= 0.5) { fps = frames / acc; hist.push([performance.now(), fps]); frames = 0; acc = 0;
      while (hist.length && performance.now() - hist[0][0] > 5000) hist.shift();
      const mn = Math.min(...hist.map(h => h[1]));
      devEl.textContent = `${fps.toFixed(0)} fps · min5s ${mn.toFixed(0)} · ${renderer.info.render.calls} draws · ${(renderer.info.render.triangles / 1000).toFixed(1)}k tris`;
      Object.assign(window.__ps3d, { fps, min5: mn, calls: renderer.info.render.calls, tris: renderer.info.render.triangles });
    }
  }
}
window.__ps3d = { S, CFG, goSite, STATIONS, deposits, rovers, spawnDeposit, catchUp, save, toScreen, drillCost, rate, binCap,
  get camX() { return camX; }, get fullT() { return fullT; }, get coverGone() { return coverGone; }, get eveOpen() { return !!eveCur; }, get sheetOpen() { return sheetOpen; }, setSheet };
if (hadRt) catchUp(true); else S.rt = Date.now();      // credit time away since the last save
hud(); sheetUI();
frame();
