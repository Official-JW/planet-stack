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
  drillScalePerLvl: 0.08, drillScaleStop: 6,   // +8%/lvl through Lv6 (1.40×), then no more growth; tier parts at Lv10/20/30/40/50 instead
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
const S = { site: 1, money: CFG.startMoney, crystals: CFG.startCrystals, drill: 1, rovers: 1, bin: 0, dep: 0, eve: [], trips: [], rt: Date.now() };
let hadRt = false;
try { const sv = JSON.parse(localStorage.getItem(SAVEKEY) || '{}'); hadRt = sv.rt > 0; Object.assign(S, sv); } catch (e) {}
if (!Array.isArray(S.eve)) S.eve = [];
if (!Array.isArray(S.trips)) S.trips = [];
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
const acts = {}; let curAct = null, rigLoaded = false, coverGone = false;
const glowMats = [];
function setClip(name) {
  const a = acts[name]; if (!a || a === curAct) return;
  a.reset(); a.setEffectiveWeight(1); a.play();
  if (curAct) curAct.crossFadeTo(a, 0.3, false);
  curAct = a;
}
function rigScale(l = S.drill) { return 1 + CFG.drillScalePerLvl * (Math.min(l, CFG.drillScaleStop) - 1); }
// ===== tier parts: cheap primitives parented to the rig (so they scale + bounce with it); 2 draws per tier (body + glow)
// all in rig-local units, inside the base footprint (|x|,|z| < 3.5) and under the Lv7 height, so they never reach the HUD,
// the deposit strip or the rover parking spots
const TIER_LV = [10, 20, 30, 40, 50];
const tierBodyMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .55, metalness: .35 });
const tierGlowMat = new THREE.MeshBasicMaterial({ vertexColors: true, toneMapped: false });
function tint(g, hex) { const c = new THREE.Color(hex), n = g.attributes.position.count, a = new Float32Array(n * 3); for (let i = 0; i < n; i++) c.toArray(a, i * 3); g.setAttribute('color', new THREE.BufferAttribute(a, 3)); return g; }
const GREY = 0x8a929e, DARK = 0x3a3f48, HAZ = 0xf2b21b;
const TIER_DEF = [
  { lv: 10, at: [0.62, 9.55, 1.3], body: () => [tint(new THREE.CylinderGeometry(.2, .26, .16, 12).translate(0, .08, 0), DARK), tint(new THREE.CylinderGeometry(.05, .05, .1, 6).translate(0, .21, 0), GREY)],
    glow: () => [tint(new THREE.SphereGeometry(.15, 12, 8).translate(0, .32, 0), 0xff5a2a)] },                                            // beacon light on the mast-top corner (kept under the mast top so the Lv7 frame holds)
  { lv: 20, at: [-1.35, 1.06, 2.35], body: () => [tint(new THREE.CylinderGeometry(.34, .38, .3, 14).translate(0, .15, 0), HAZ), tint(new THREE.CylinderGeometry(.12, .12, 2.1, 8).translate(0, 1.35, 0), GREY),
      tint(new THREE.CylinderGeometry(.3, .3, .35, 12).translate(0, 2.55, 0), DARK), tint(new THREE.ConeGeometry(.3, .5, 12).rotateX(Math.PI).translate(0, .05, 0), GREY)],
    glow: () => [tint(new THREE.TorusGeometry(.32, .04, 6, 20).rotateX(Math.PI / 2).translate(0, 2.4, 0), 0x46e6ff)] },              // second drill head beside the main bit
  { lv: 30, at: [-0.68, 7.0, 0.06], body: () => [-1, 1].flatMap(sd => { const x = sd * 1.66; return [tint(new THREE.BoxGeometry(.5, .08, .08).translate(x + sd * .2, 0, 1.3), GREY), tint(new THREE.BoxGeometry(.42, .3, .2).translate(x + sd * .45, 0, 1.42), DARK)]; }),
    glow: () => [-1, 1].map(sd => tint(new THREE.BoxGeometry(.34, .22, .04).translate(sd * 1.66 + sd * .45, 0, 1.53), 0xfff4d0)) },   // side floodlights on the mast
  { lv: 40, at: [-2.7, 1.06, 2.55], body: () => [tint(new THREE.CylinderGeometry(.55, .55, 1.8, 16).translate(0, .9, 0), 0xd9dde4), tint(new THREE.SphereGeometry(.55, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2).translate(0, 1.8, 0), 0xd9dde4),
      tint(new THREE.BoxGeometry(1.2, .14, 1.2).translate(0, .07, 0), DARK)],
    glow: () => [tint(new THREE.CylinderGeometry(.57, .57, .14, 16, 1, true).translate(0, 1.2, 0), 0x46e6ff)] },                      // second tank
  { lv: 50, at: [-0.68, 6.6, 0.06], body: () => [], glow: () => [tint(new THREE.TorusGeometry(2.55, .09, 8, 48).rotateX(Math.PI / 2), 0x46e6ff)] },   // cyan ring around the tower
];
const tiers = [];                                   // { lv, g, t } t<0: settled
function buildTiers() {
  for (const d of TIER_DEF) {
    const g = new THREE.Group(); g.position.set(...d.at); g.visible = false; g.userData.tier = d.lv;
    const b = d.body(), w = d.glow();
    if (b.length) g.add(new THREE.Mesh(mergeGeometries(b), tierBodyMat));
    if (w.length) g.add(new THREE.Mesh(mergeGeometries(w), tierGlowMat));
    rig.add(g); tiers.push({ lv: d.lv, g, t: -1 });
  }
}
function applyTiers(popLv) {                         // restore everything owned; only a tier bought just now pops in
  for (const T of tiers) { const own = S.drill >= T.lv; T.g.visible = own;
    if (own && T.lv === popLv) { T.t = 0; T.g.scale.setScalar(.01); } else if (T.t < 0) T.g.scale.setScalar(1); }
  window.__ps3d.tiers = tiers.filter(T => T.g.visible).map(T => T.lv);
}
function updTiers(dt) {
  for (const T of tiers) { if (T.t < 0) continue; T.t += dt; const u = T.t / .4;
    if (u >= 1) { T.t = -1; T.g.scale.setScalar(1); continue; }
    const c = 2.2; T.g.scale.setScalar(Math.max(.01, 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2)); }   // ease-out-back pop
}
let rigBase = null;                       // rig bounds at scale 1, relative to (MX,0,0)
function updRigBox() {                    // footprint at the current level + margin: keeps deposits / rover paths off the rig
  if (!rigBase) return; const k = rigScale();
  rigBox.min.set(MX + rigBase.min.x * k - .6, 0, rigBase.min.z * k - .6); rigBox.max.set(MX + rigBase.max.x * k + .6, rigBase.max.y * k, rigBase.max.z * k + .6);
  for (const d of [...deposits]) if (!d.claimed && d.x > rigBox.min.x - 1 && d.x < rigBox.max.x + 1 && d.z > rigBox.min.z - 1 && d.z < rigBox.max.z + 1) removeDeposit(d);
}
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
  rigBase = new THREE.Box3().setFromObject(rig); rigBase.min.x -= MX; rigBase.max.x -= MX;
  updRigBox(); rig.scale.setScalar(rigScale());
  buildTiers(); applyTiers(0);
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
  // short screens (iPhone SE): back off just enough that the full-size rig (Lv6+ incl. tier parts) tops out ≥104 px,
  // clear of the HUD / Eve band. Calibrated on 393×852 where it has no effect (rig top 108 px there). Elevation stays 18°.
  const fitTop = 12.14 * (H / 2) / Math.max(60, H / 2 - 104);
  return Math.max(CAM.halfW / (vt * aspect), 7.2 / vt, fitTop / vt, 16);
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
  else if (Math.abs(v) > 0.35 && Math.abs(dx) >= 30) dir = v < 0 ? 1 : -1;   // a flick needs speed AND ≥30 px travel
  window.__ps3d.lastSwipe = { dx, v: +v.toFixed(3), dir };
  if (!dir && d.moved < 10 && t - d.t0 < 500 && e && e.type === 'pointerup') tap(e.clientX, e.clientY);
  goSite(S.site + dir);
}
canvas.addEventListener('pointerup', endDrag); canvas.addEventListener('pointercancel', endDrag);

// ===== HUD
const moneyEl = $('money'), rateEl = $('rate'), cryEl = $('cry'), binEl = $('bin'), binFill = binEl.firstElementChild;
let lastMoneyTxt = '', lastMoneyV = 0, lastBin = -1;
moneyEl.addEventListener('animationend', (e) => { if (e.animationName === 'tick') moneyEl.classList.remove('tick'); });
function hud() {
  const mt = DEV ? '∞' : fmt(S.money); if (mt !== lastMoneyTxt) { moneyEl.textContent = mt; lastMoneyTxt = mt; moneyEl.classList.toggle('long', mt.length > 10);
    if (S.money > lastMoneyV && !moneyEl.classList.contains('bump')) moneyEl.classList.add('tick'); }   // soft tick on any increase (transform/opacity only, no forced reflow)
  lastMoneyV = S.money;
  rateEl.textContent = rate();
  cryEl.textContent = DEV ? '∞' : S.crystals;
  const bf = Math.min(1, S.bin / binCap()); if (Math.abs(bf - lastBin) > .002) { lastBin = bf; binFill.style.transform = `scaleX(${bf.toFixed(3)})`; }
  binEl.classList.toggle('full', fullT > 0);
}
// while Eve talks her card lies over the HUD band and carries a live cash badge; chunks and '+$X' pops fly to it
const eveCashEl = $('eveCash'), hudEl = $('hud'); let lastCashTxt = '';
const cashTarget = () => (eveCur ? eveCashEl : moneyEl);
function eveCash() { if (!eveCur) return; const t = DEV ? '∞' : fmt(S.money); if (t !== lastCashTxt) { eveCashEl.textContent = t; lastCashTxt = t; } }
function bumpMoney() { const el = cashTarget(); el.classList.remove('bump'); void el.offsetWidth; el.classList.add('bump'); }
function pop(text, x, y, cls = '') {
  const el = document.createElement('div'); el.className = 'pop ' + cls; el.textContent = text;
  el.style.left = x + 'px'; el.style.top = y + 'px'; document.body.appendChild(el); setTimeout(() => el.remove(), 1150);
}
function moneyXY() { const r = cashTarget().getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }

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
  window.__ps3d.lastFly = { target: cashTarget().id, ...moneyXY() };
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
    if (u >= 1) { chMesh[c.kind].setMatrixAt(c.idx, ZERO); freeIdx[c.kind].push(c.idx); const ls = toScreen(_p.x, _p.y, _p.z); window.__ps3d.lastLand = { x: Math.round(ls.x), y: Math.round(ls.y), target: cashTarget().id }; if (c.done) c.done(); chunks.splice(i, 1); }
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
  const top = Math.max(hudEl.getBoundingClientRect().bottom, 120) + 24;   // station title moved to the bottom (above the dots); top of the band = under the HUD/Eve band (unchanged 144 px)
  const sheetTop = $('sheetWrap').getBoundingClientRect().top;      // open sheet top edge
  return { top, bot: Math.min(sheetTop, dotsEl.getBoundingClientRect().top, nameEl.getBoundingClientRect().top) - 34, l: 34, r: W - 34 };
}
const homes = () => { const x = Math.min(rigBox.max.x + .4, MX + 6.3); return [new THREE.Vector3(x, 0, rigBox.max.z + .4), new THREE.Vector3(Math.min(rigBox.max.x + .5, MX + 6.3), 0, rigBox.max.z - 2.8)]; };   // right-front, by the hopper
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
    return makeDeposit(x, z);
  }
  return null;
}
function makeDeposit(x, z, claimed = false) {
  const disc = new THREE.Mesh(discGeo, discMat); disc.position.set(x, 0.04, z); disc.renderOrder = 2;
  const gem = new THREE.Mesh(gemGeo, gemMat); gem.position.set(x, 1, z); gem.castShadow = false;
  scene.add(disc, gem);
  const d = { id: ++depSeq, x, z, disc, gem, age: claimed ? 1 : 0, claimed, dig: 0 }; deposits.push(d); return d;
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
  const r = rovers.find(r => r.phase === 'idle' && r.pin >= 1 && !S.trips[r.i]); if (!r) return false;
  d.claimed = true; r.dep = d; const home = homes()[r.i];
  const path = planPath(home, new THREE.Vector3(d.x, 0, d.z));
  let len = 0; for (let i = 1; i < path.length; i++) len += path[i - 1].distanceTo(path[i]);
  const leg = +clamp(1.2 + len / 8, CFG.roverLegMin, CFG.roverLegMax).toFixed(3);
  // trip runs on wall-clock time from t0, so reload / tab-away resumes or completes it exactly once
  S.trips[r.i] = { t0: Date.now(), out: leg, dig: CFG.roverDig, back: leg, dump: CFG.roverDump, bonus: CFG.roverBonus, path: path.map(v => [+v.x.toFixed(2), +v.z.toFixed(2)]) };
  save(); return true;
}
const tripTotal = (t) => t.out + t.dig + t.back + t.dump;
function finishTrip(r, tr) {
  S.trips[r.i] = null;                          // cleared before paying: can never pay twice
  S.money += tr.bonus; S.dep++; save();
  if (r.dep) { removeDeposit(r.dep); r.dep = null; }
  r.phase = 'idle'; r.trip = null; r.g.position.copy(homes()[r.i]); r.g.rotation.set(0, r.yaw, 0);
  (window.__ps3d.trips = window.__ps3d.trips || []).push({ wall: Date.now() - tr.t0, bonus: tr.bonus });
  if (S.site === MINE && !document.hidden) {
    const sp = toScreen(r.g.position.x, 2.2, r.g.position.z);
    pop('+' + fmt(tr.bonus) + ' bonus', sp.x, sp.y, 'bonus'); flyChunks(4, r.g.position.clone().add(new THREE.Vector3(0, 1.2, 0)), tr.bonus, 'bonus');
  } else bumpMoney();
}
function restoreTrips() {          // on load: re-attach saved trips; a claimed deposit is re-shown only while the rover is still on its way / digging
  for (const r of rovers) {
    const tr = S.trips[r.i]; if (!tr) continue;
    const el = (Date.now() - tr.t0) / 1000;
    if (el >= 0 && el < tr.out + tr.dig) { const e = tr.path[tr.path.length - 1]; r.dep = makeDeposit(e[0], e[1], true); }
  }
}
const _rp = new THREE.Vector3(), _rq = new THREE.Vector3();
function updRovers(dt, time) {
  const now = Date.now();
  for (const r of rovers) {
    if (r.pin < 1) { r.pin = Math.min(1, r.pin + dt / .4); r.g.scale.setScalar(ease(r.pin)); }
    const tr = S.trips[r.i]; let show = false;
    if (!tr) {
      r.phase = 'idle';
      const h = homes()[r.i]; r.g.position.lerp(h, Math.min(1, dt * 4));
      let dy = 0 - r.yaw; dy = Math.atan2(Math.sin(dy), Math.cos(dy)); r.yaw += dy * Math.min(1, dt * 5); r.g.rotation.set(0, r.yaw, 0);
      r.ring.style.display = 'none'; continue;
    }
    if (r.trip !== tr) { r.trip = tr; r.path = tr.path.map(([x, z]) => new THREE.Vector3(x, 0, z)); }
    let el = (now - tr.t0) / 1000;
    if (el < 0) { tr.t0 = now; el = 0; }        // clock moved backward: restart the trip, never skip ahead
    if (el >= tripTotal(tr)) { finishTrip(r, tr); r.ring.style.display = 'none'; continue; }
    r.g.position.y = 0; r.g.rotation.x = 0;
    if (el < tr.out || (el >= tr.out + tr.dig && el < tr.out + tr.dig + tr.back)) {
      const outLeg = el < tr.out; r.phase = outLeg ? 'out' : 'back';
      if (!outLeg && r.dep) { removeDeposit(r.dep); r.dep = null; }
      const u = outLeg ? el / tr.out : (el - tr.out - tr.dig) / tr.back, k = ease(u), uu = outLeg ? k : 1 - k;
      pathAt(r.path, uu, _rp); pathAt(r.path, clamp(uu + (outLeg ? .02 : -.02), 0, 1), _rq);
      if (_rq.distanceToSquared(_rp) > 1e-6) { const yaw = Math.atan2(_rq.x - _rp.x, _rq.z - _rp.z); let dy = yaw - r.yaw; dy = Math.atan2(Math.sin(dy), Math.cos(dy)); r.yaw += dy * Math.min(1, dt * 10); }
      r.g.position.copy(_rp); r.g.rotation.set(0, r.yaw, 0);
    } else if (el < tr.out + tr.dig) {
      r.phase = 'dig'; const u = (el - tr.out) / tr.dig; if (r.dep) r.dep.dig = u; show = true;
      const e = r.path[r.path.length - 1]; r.g.position.set(e.x, Math.abs(Math.sin(time * 18)) * .06, e.z); r.g.rotation.set(Math.sin(time * 22) * .03, r.yaw, 0);
      r.arc.setAttribute('stroke-dashoffset', (113.1 * (1 - u)).toFixed(1));
    } else {
      r.phase = 'dump'; const u = (el - tr.out - tr.dig - tr.back) / tr.dump;
      r.g.position.copy(r.path[0]); r.g.rotation.set(-Math.sin(u * Math.PI) * .35, r.yaw, 0);
    }
    if (show) { const p = toScreen(r.g.position.x, 2.6, r.g.position.z); r.ring.style.left = p.x + 'px'; r.ring.style.top = p.y + 'px'; }
    r.ring.style.display = show ? 'block' : 'none';
  }
}

// ===== upgrade juice: spark burst (1 Points draw, ~0.5 s) + squash-and-bounce (~0.35 s)
const SPK = 48, spkPos = new Float32Array(SPK * 3), spkVel = new Float32Array(SPK * 3);
const spkGeo = new THREE.BufferGeometry(); spkGeo.setAttribute('position', new THREE.BufferAttribute(spkPos, 3));
const spkMat = new THREE.PointsMaterial({ color: 0xffe27a, size: 0.32, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending });
const sparks = new THREE.Points(spkGeo, spkMat); sparks.frustumCulled = false; sparks.visible = false; scene.add(sparks);
let spkT = -1, sqT = -1;
function upgradeFx() {
  const k = rigScale();
  for (let i = 0; i < SPK; i++) {
    const a = Math.random() * Math.PI * 2, e = Math.random() * 1.2, s = 6 + Math.random() * 7, h = (1 + Math.random() * 8) * k;
    spkPos.set([MX + Math.cos(a) * 1.2 * k, h, Math.sin(a) * 1.2 * k], i * 3);
    spkVel.set([Math.cos(a) * Math.cos(e) * s, Math.sin(e) * s + 2, Math.sin(a) * Math.cos(e) * s], i * 3);
  }
  spkGeo.attributes.position.needsUpdate = true; spkT = 0; sqT = 0; sparks.visible = true;
  window.__ps3d.fx = (window.__ps3d.fx || 0) + 1;
}
function updFx(dt) {
  if (spkT >= 0) {
    spkT += dt; const u = spkT / 0.5;
    if (u >= 1) { spkT = -1; sparks.visible = false; }
    else { for (let i = 0; i < SPK; i++) { spkVel[i * 3 + 1] -= 18 * dt; for (let j = 0; j < 3; j++) spkPos[i * 3 + j] += spkVel[i * 3 + j] * dt; }
      spkGeo.attributes.position.needsUpdate = true; spkMat.opacity = 1 - u * u; spkMat.size = 0.34 * (1 - .5 * u); }
  }
  let sy = 1;
  if (sqT >= 0) { sqT += dt; const u = sqT / 0.35; if (u >= 1) sqT = -1; else sy = 1 - 0.16 * Math.sin(u * Math.PI * 2) * (1 - u); }   // squash, stretch, settle
  if (rig) { const k = rigScale(), sxz = 1 / Math.sqrt(sy); rig.scale.set(k * sxz, k * sy, k * sxz); }
  window.__ps3d.sy = sy;
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
const closedY = () => sheet.offsetHeight - PEEK - (parseFloat(getComputedStyle(sheet).paddingBottom) || 0);   // panel runs flush to the bottom edge; peek sits above the safe-area inset
function setSheet(open) { sheetOpen = open; document.body.classList.toggle('sheet-open', open); sheet.classList.remove('dragging'); sheet.style.transform = `translateY(${open ? 0 : closedY()}px)`; if (open && eveCur && eveCur.point === 'upgrade') pointerDone = true; }
setSheet(false);
addEventListener('resize', () => { if (!sheetDrag) sheet.style.transform = `translateY(${sheetOpen ? 0 : closedY()}px)`; });   // inset can change (rotation)
grab.addEventListener('pointerdown', (e) => { e.stopPropagation(); sheetDrag = { y0: e.clientY, b: sheetOpen ? 0 : closedY(), s: [[performance.now(), e.clientY]], moved: 0 }; sheet.classList.add('dragging'); try { grab.setPointerCapture(e.pointerId); } catch (_) {} });
grab.addEventListener('pointermove', (e) => {
  if (!sheetDrag) return; const dy = e.clientY - sheetDrag.y0; sheetDrag.moved = Math.max(sheetDrag.moved, Math.abs(dy));
  let y = sheetDrag.b + dy; const c = closedY(); if (y < 0) y = y * .3; if (y > c) y = c + (y - c) * .3;
  sheet.style.transform = `translateY(${y}px)`; sheetDrag.y = y; sheetDrag.s.push([performance.now(), e.clientY]); if (sheetDrag.s.length > 8) sheetDrag.s.shift();
});
const endSheet = (e) => {
  if (!sheetDrag) return; const d = sheetDrag; sheetDrag = null;
  if (d.moved < 8) return setSheet(!sheetOpen);           // a tap on the handle toggles; drags still spring
  const a = d.s[0], b = d.s[d.s.length - 1], v = (b[1] - a[1]) / Math.max(16, b[0] - a[0]);
  if (v > 0.3) setSheet(false); else if (v < -0.3) setSheet(true); else setSheet((d.y ?? d.b) < closedY() / 2);
};
grab.addEventListener('pointerup', endSheet); grab.addEventListener('pointercancel', endSheet);
sheet.addEventListener('pointerdown', (e) => e.stopPropagation());
const bDrill = $('bDrill'), bRover = $('bRover');
const meterKeys = {};
function meter(id, n, on) { const k = n + ':' + on; if (meterKeys[id] === k) return; meterKeys[id] = k; const el = $(id);
  if (el.children.length !== n) el.innerHTML = '<i></i>'.repeat(n); [...el.children].forEach((x, i) => x.classList.toggle('on', i < on)); }
function sheetUI() {
  const c = drillCost(), ok = canPay(c);
  $('dLvl').textContent = 'LV ' + S.drill; meter('dMeter', 10, S.drill >= 50 ? 10 : (S.drill - 1) % 10 + 1);   // segments = progress through the current 10-level tier
  $('dGain').textContent = `${rate()} ore/min → next +${CFG.drillRatePerLvl} ore/min`;
  bDrill.textContent = ok ? fmt(c) : 'Need ' + fmt(c); bDrill.className = ok ? '' : 'need'; bDrill.parentNode.classList.toggle('ok', ok);
  $('rLvl').textContent = S.rovers + '/' + CFG.roverMax; meter('rMeter', CFG.roverMax, S.rovers);
  if (S.rovers >= CFG.roverMax) { $('rGain').textContent = `Max · ${fmt(CFG.roverBonus)} per deposit`; bRover.textContent = 'Max'; bRover.className = 'max'; }
  else { const ok2 = canPay(CFG.roverCost); $('rGain').textContent = `+1 rover · ${fmt(CFG.roverBonus)} per deposit`; bRover.textContent = ok2 ? fmt(CFG.roverCost) : 'Need ' + fmt(CFG.roverCost); bRover.className = ok2 ? '' : 'need'; }
  bRover.parentNode.classList.toggle('ok', bRover.className === '');
  $('sum').textContent = `Drill Lv ${S.drill} · ${S.rovers} rover${S.rovers > 1 ? 's' : ''}`;
  $('canDot').hidden = !(canPay(c) || (S.rovers < CFG.roverMax && canPay(CFG.roverCost)));
}
// buy buttons fire on pointerup (one tap = one buy even when frames lag); the trailing click is swallowed,
// keyboard / assistive clicks (no pointer press) still work
function bindBuy(el, fn) {
  let press = null, swallow = false;
  el.addEventListener('pointerdown', (e) => { e.stopPropagation(); press = { id: e.pointerId, x: e.clientX, y: e.clientY }; swallow = false; try { el.setPointerCapture(e.pointerId); } catch (_) {} });
  el.addEventListener('pointerup', (e) => { const p = press; press = null; if (!p || p.id !== e.pointerId) return; swallow = true;
    if (Math.hypot(e.clientX - p.x, e.clientY - p.y) < 24) fn(); });
  el.addEventListener('pointercancel', () => { press = null; swallow = true; });   // a cancelled press never buys, even if a stray click follows
  el.addEventListener('click', (e) => { if (swallow) { swallow = false; return; } if (!press) fn(); });
}
bindBuy(bDrill, () => {
  const c = drillCost(); if (!canPay(c)) return;
  pay(c); S.drill++; applyRigLevel(); updRigBox(); applyTiers(S.drill); upgradeFx(); save(); sheetUI(); hud();
  if (fullT > 0 && S.bin < binCap()) { fullT = 0; setClip('dig'); }
  const r = bDrill.getBoundingClientRect(); pop('Drill Lv ' + S.drill, r.left + r.width / 2, r.top - 8, 'info');
  window.__ps3d.buys = (window.__ps3d.buys || 0) + 1;
});
bindBuy(bRover, () => {
  if (S.rovers >= CFG.roverMax || !canPay(CFG.roverCost)) return;
  pay(CFG.roverCost); S.rovers++; addRover(S.rovers - 1, true); save(); sheetUI(); hud();
});

// conveyor strip on the bar creeps (CSS background-position) only while the drill runs and the sheet is closed
let convOn = null;
function updConveyor() { const on = fullT === 0 && !sheetOpen && !(sheetDrag); if (on !== convOn) { convOn = on; sheet.classList.toggle('run', on); window.__ps3d.conveyor = on; } }

// ===== Eve placeholder radio calls
const EVE_BEATS = [
  { id: 'mine_first_view', point: 'deposit', text: "Moonbase, this is Eve at Earth Coms. Good to hear you made it. First job: get that mine running. Tap where I'm pointing." },
  { id: 'first_deposit', point: null, text: "Nice haul, Commander. Your rover's digs pay a bonus on top of the drill, so keep an eye out for that glow. Over." },
  { id: 'upgrade_ready', point: 'upgrade', text: "You've got the cash for an upgrade. Bigger mine, bigger loads. Tap Upgrade." },
];
const EVE_TRIG = {
  mine_first_view: () => S.site === MINE && coverGone && Math.abs(camX - MX) < 1,
  first_deposit: () => S.dep >= 1,
  upgrade_ready: () => S.dep >= 1 && canPay(drillCost()) && !sheetOpen,
};
const eveEl = $('eve'), eveTx = $('eveTx'), pointEl = $('point');
let eveCur = null, eveTyped = 0, eveTimer = 0, pointerDone = false, pointBeat = null, evePages = [''], evePg = 0;
const eveOv = $('eveOver');
function evePaginate(text) {          // greedy word wrap into pages of at most 2 lines, measured in the real text box
  const lh = parseFloat(getComputedStyle(eveTx).lineHeight) || 17, max = lh * 2 + 2, pages = []; let cur = '';
  for (const w of text.split(' ')) { const t = cur ? cur + ' ' + w : w; eveTx.textContent = t; if (cur && eveTx.scrollHeight > max) { pages.push(cur); cur = w; } else cur = t; }
  if (cur) pages.push(cur); eveTx.textContent = ''; return pages;
}
const evePage = () => evePages[evePg] || '';
function eveShow(b) {
  eveCur = b; eveTyped = 0; eveTx.textContent = ''; eveEl.classList.add('on');
  evePages = evePaginate(b.text); evePg = 0; eveOv.textContent = evePages.length > 1 ? 'Next' : 'Over';
  hudEl.classList.add('away'); lastCashTxt = ''; eveCash();
  S.eve.push(b.id); save();                    // heard as soon as it plays: never repeats, even after reload
  pointBeat = b.point; pointerDone = false;
  if (b.point === 'deposit' && !deposits.some(d => !d.claimed)) spawnDeposit();
  window.__ps3d.eveShown = (window.__ps3d.eveShown || []).concat(b.id);
}
function eveClose() { eveEl.classList.remove('on'); eveCur = null; hudEl.classList.remove('away'); }   // HUD slides back in (0.25 s CSS)
eveOv.addEventListener('click', () => {
  if (!eveCur) return; if (eveTyped < evePage().length) { eveTyped = evePage().length; eveTx.textContent = evePage(); return; }   // first tap finishes the line
  if (evePg < evePages.length - 1) { evePg++; eveTyped = 0; eveTx.textContent = ''; eveOv.textContent = evePg < evePages.length - 1 ? 'Next' : 'Over'; } else eveClose();
});
$('eveX').addEventListener('click', eveClose);
eveEl.addEventListener('pointerdown', (e) => { e.stopPropagation(); if (eveCur && !e.target.closest('button')) eveTyped = evePage().length; });
function updEve(dt) {
  if (eveCur) { const pg = evePage(); if (eveTyped < pg.length) { eveTimer += dt; while (eveTimer > .028 && eveTyped < pg.length) { eveTimer -= .028; eveTyped++; } } if (eveTx.textContent.length !== Math.min(eveTyped, pg.length)) eveTx.textContent = pg.slice(0, eveTyped); }
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
restoreTrips();

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
    if (oreFill) oreFill.scale.y = oreBaseY * (0.06 + 0.94 * Math.min(1, S.bin / binCap()));
  }
  updDeposits(dt, time); updRovers(dt, time); updChunks(dt); updFx(dt); updTiers(dt);
  updEve(dt); eveCash(); updConveyor();
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
window.__ps3d = { renderer, scene, camera, rigScaleAt: rigScale, fxStep: updFx, tierStep: updTiers, get tierList() { return tiers; }, EVE_BEATS, get eveId() { return eveCur && eveCur.id; }, sparks, S, CFG, goSite, STATIONS, deposits, rovers, spawnDeposit, catchUp, save, toScreen, homes, drillCost, rate, binCap,
  get camX() { return camX; }, get fullT() { return fullT; }, get coverGone() { return coverGone; }, get eveOpen() { return !!eveCur; }, get evePages() { return evePages; }, get cashTarget() { return cashTarget().id; }, get evePg() { return evePg; }, get sheetOpen() { return sheetOpen; }, setSheet };
if (hadRt) catchUp(true); else S.rt = Date.now();      // credit time away since the last save
hud(); sheetUI();
frame();
