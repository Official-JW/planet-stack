// Planet Stack QA3D: Mine A loop on Art's Mine GLB (drill mines on its own + HT-04 truck deposit bonus).
// Fixed camera, one-station swipes, upgrade sheet, offline catch-up, Eve placeholder, ?dev=1 readout.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';

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
const GAP = 160, N = STATIONS.length, MINE = 1, MX = MINE * GAP;
const $ = (id) => document.getElementById(id);
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const ease = (t) => t < .5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;

// ===== economy helpers
const rate = () => CFG.drillRate0 + CFG.drillRatePerLvl * (S.drill - 1);           // ore/min
const binCap = () => CFG.binCap0 + CFG.binCapPerLvl * (S.drill - 1);
const drillCost = () => Math.round(CFG.drillCost0 * CFG.drillCostGrowth ** (S.drill - 1));
const canPay = (c) => DEV || S.money >= c;
const pay = (c) => { if (!DEV) S.money -= c; };
const SUF = [[1e15, 'Qa'], [1e12, 'T'], [1e9, 'B'], [1e6, 'M']];
function fmt(v) {                       // $999,999 then 3 significant digits: $8.32M, $83.2M, $832M, $8.32B, $8.32T (floored: never shows more than you have)
  v = Math.floor(v); const a = Math.abs(v);
  for (let i = 0; i < SUF.length; i++) { const d = SUF[i][0]; if (a < d) continue;
    const q = v / d, dp = q >= 100 ? 0 : q >= 10 ? 1 : 2, m = 10 ** dp; return '$' + (Math.floor(q * m + 1e-7) / m).toFixed(dp) + SUF[i][1]; }
  return '$' + v.toLocaleString('en-US');
}

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
const camera = new THREE.PerspectiveCamera(38, 1, 0.5, 3000);

const hemi = new THREE.HemisphereLight(0x9fb4d8, 0x2a2a30, 0.55); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff4e2, 2.6);
sun.castShadow = true; sun.shadow.mapSize.set(1024, 1024);
Object.assign(sun.shadow.camera, { left: -22, right: 22, top: 22, bottom: -22, near: 1, far: 120 });
sun.shadow.bias = -0.0005; sun.shadow.normalBias = 0.03;
scene.add(sun); scene.add(sun.target);

// ground (1 draw)
const GROUND_MESHES = [];
{
  const W = GAP * (N - 1) + 600, D = 1400;   // deep enough in +z for the farthest bounds-fit camera (Shipyard, k≈9)
  const g = new THREE.PlaneGeometry(W, D, 260, 110); g.rotateX(-Math.PI / 2);
  const pos = g.attributes.position, col = new Float32Array(pos.count * 3);
  const rnd = (a) => { const s = Math.sin(a * 127.1) * 43758.5453; return s - Math.floor(s); };
  const craters = []; for (let i = 0; i < 260; i++) craters.push([(rnd(i + .3) - .5) * W, (rnd(i + 7.7) - .5) * D - 20, 1.5 + rnd(i + 3.1) * 6]);
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i), z = pos.getZ(i);
    let v = 0.42 + 0.05 * Math.sin(x * .23 + z * .11) + 0.04 * Math.sin(x * .07 - z * .19) + (rnd(x * 3.1 + z * 7.3) - .5) * 0.05;
    for (const [cx, cz, r] of craters) { const d = Math.hypot(x - cx, z - cz) / r; if (d < 1.25) v += d < 1 ? -0.10 * (1 - d * d) : 0.07 * (1.25 - d) * 4 * (d - 1); }
    col[i * 3] = v; col[i * 3 + 1] = v; col[i * 3 + 2] = v * 1.03;
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const GX = GAP * (N - 1) / 2, GZ = -100;
  const ground = new THREE.Mesh(g, new THREE.MeshLambertMaterial({ vertexColors: true }));   // fallback look until (or if) the KTX2 tiles load
  ground.position.set(GX, 0, GZ); ground.receiveShadow = true; scene.add(ground);
  const FW = 8000, FD = 6000, FX = GX, FZ = -2400;
  const fg = new THREE.PlaneGeometry(FW, FD).rotateX(-Math.PI / 2);
  { const uv = fg.attributes.uv, ps = fg.attributes.position;   // apron UVs in the ground's own UV space (world-aligned): the 10 m tiles run on across the seam, no visible edge
    for (let i = 0; i < uv.count; i++) { const wx = FX + ps.getX(i), wz = FZ + ps.getZ(i); uv.setXY(i, (wx - (GX - W / 2)) / W, 1 - (wz - (GZ - D / 2)) / D); } }
  const far = new THREE.Mesh(fg, new THREE.MeshLambertMaterial({ color: new THREE.Color().setRGB(.42, .42, .433) }));   // flat apron to the horizon so wide station frames never show the ground's edge (1 draw)
  far.position.set(FX, -0.06, FZ); scene.add(far);
  // ===== shared M_ground (Art b422778): KTX2 detail albedo + normal (10 m repeat, standard UVs), macro multiplier in world XZ (76 m), one material for every station
  const TILE_M = 10, MACRO_M = 76, GB = 'models/ground/', GV = '?v=b422778';
  const ktx2 = new KTX2Loader().setTranscoderPath('vendor/addons/libs/basis/').detectSupport(renderer);
  Promise.all(['ground_basecolor_1024.ktx2', 'ground_normal_512.ktx2', 'ground_macro_256.ktx2'].map(f => ktx2.loadAsync(GB + f + GV))).then(([albedo, normal, macro]) => {
    const aniso = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    for (const t of [albedo, normal, macro]) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = aniso; t.needsUpdate = true; }
    albedo.colorSpace = THREE.SRGBColorSpace; normal.colorSpace = macro.colorSpace = THREE.NoColorSpace;
    for (const t of [albedo, normal]) t.repeat.set(W / TILE_M, D / TILE_M);   // repeat = size / 10 (the apron's UVs share the ground's UV space)
    const M = new THREE.MeshStandardMaterial({ name: 'M_ground', map: albedo, normalMap: normal, roughness: 0.92, metalness: 0 });
    M.onBeforeCompile = (sh) => {
      sh.uniforms.macroMap = { value: macro };
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec2 vGroundXZ;')
        .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvGroundXZ = (modelMatrix * vec4(transformed, 1.0)).xz;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec2 vGroundXZ;\nuniform sampler2D macroMap;')
        .replace('#include <map_fragment>', '#include <map_fragment>\ndiffuseColor.rgb *= texture2D(macroMap, vGroundXZ / ' + MACRO_M.toFixed(1) + ').r * 2.0;');
    };
    M.customProgramCacheKey = () => 'M_ground_macro';
    const old = [ground.material, far.material]; ground.material = M; far.material = M; old.forEach(m => m.dispose());
    window.__ps3d.ground = { ktx2: true, aniso, mat: M.name, shared: ground.material === far.material, repeat: albedo.repeat.toArray() };
  }).catch((e) => { console.warn('KTX2 ground failed, keeping the vertex-colour ground', e); window.__ps3d.ground = { ktx2: false, err: String(e) }; });
  GROUND_MESHES.push(ground, far);
}
// stars (1 draw)
{
  const n = 900, p = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const a = Math.random() * Math.PI * 2, e = .05 + Math.random() * 1.2, r = 1800; p[i * 3] = GAP * 3 + Math.cos(a) * r * Math.cos(e); p[i * 3 + 1] = Math.sin(e) * r; p[i * 3 + 2] = -Math.abs(Math.sin(a)) * r * Math.cos(e) - 60; }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 1.2, sizeAttenuation: false })));
}
// gray placeholders for the other stations
let _ldr = null; function loader0() { if (!_ldr) { _ldr = new GLTFLoader(); _ldr.setMeshoptDecoder(MeshoptDecoder); } return _ldr; }
const ph = new THREE.MeshStandardMaterial({ color: 0x8a8d94, roughness: .85, metalness: .05 });
const SIZES = [[10, 8, 8], null, [10, 1, 10], [14, 7, 9], [9, 12, 9], [12, 9, 10], [10, 10, 8]];
const phBox = [];
STATIONS.forEach((name, i) => {
  if (!SIZES[i]) return; const [w, h, d] = SIZES[i];
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), ph);
  m.position.set(i * GAP, h / 2, 0); m.castShadow = m.receiveShadow = true; scene.add(m); phBox[i] = m;
});
// ===== passed station GLBs (Art): swap in for the gray box once loaded; tiers hidden; idle loops play; doors stay shut
const STATION_GLB = [
  { i: 0, url: 'models/life_support_adfaac9.glb?v=e8427ec4', loops: ['Beacon_Lights_Blink', 'Fan_Scrubber_Spin'] },   // Cam_Target (0, 2.5, -12.5), frame_w 34
  { i: 3, url: 'models/dock_tankfarm_fb99e50.glb?v=364bb07f', loops: ['Beacon_Lights_Blink', 'crane_gantry_move'] },     // Cam_Target (9, 3, 2), frame_w 40; dock door stays shut
  { i: 5, url: 'models/shipyard_2d57b95.glb?v=4020a073', loops: ['Beacon_Lights_Blink', 'crane_jib_swing'] },
];
const SITECAM = STATIONS.map(() => ({ k: 1, dx: 0, dz: 0, ly: CAM.lookY }));   // per-station framing; the Mine keeps k=1, dx=dz=0 until its GLB (with Cam_Target) is in
const stationMixers = [], stationObjs = {};
const _ct = new THREE.Vector3();
function camTargetOf(o) { let t = null; o.traverse(n => { if (!t && n.name === 'Cam_Target' && n.userData && n.userData.frame_w > 0) t = n; }); return t; }
function fitSite(i) {
  const o = stationObjs[i]; if (!o || !camera.userData.dist) return;
  const ct = o.userData.camTarget;
  if (ct) {   // Art's station camera: aim at Cam_Target (incl. its y), frame_w metres span the screen width at its depth; 38° vFOV, 18° down; edges may crop
    o.updateMatrixWorld(true); ct.getWorldPosition(_ct);
    const d = (ct.userData.frame_w / 2) / (Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect);
    SITECAM[i] = { k: d / camera.userData.dist, dx: _ct.x - i * GAP, dz: _ct.z, ly: _ct.y, ct: true, d };
    return;
  }
  // no Cam_Target yet: fit the visible bounds whole inside the band between the HUD and the bar
  const bx = new THREE.Box3(); o.traverse(m => { if (!m.isMesh) return; for (let q = m; q; q = q.parent) if (!q.visible) return; bx.expandByObject(m); });
  const cx = (bx.min.x + bx.max.x) / 2, cz = (bx.min.z + bx.max.z) / 2, cy = (bx.min.y + bx.max.y) / 2;
  const c = [], mc = camera.clone(), bd = band(), top = bd.top, bot = bd.bot;
  for (const x of [bx.min.x, bx.max.x]) for (const y of [bx.min.y, bx.max.y]) for (const z of [bx.min.z, bx.max.z]) c.push([x, y, z]);
  const e = THREE.MathUtils.degToRad(CAM.elev);
  for (let k = 1; k < 24; k += .02) for (const ly of [CAM.lookY, (CAM.lookY + cy) / 2, cy]) {
    const d = camera.userData.dist * k; mc.position.set(cx, ly + d * Math.sin(e), cz + d * Math.cos(e)); mc.lookAt(cx, ly, cz); mc.updateMatrixWorld();
    const ps = c.map(p => toScreen(p[0], p[1], p[2], mc));
    if (ps.every(p => p.x >= 12 && p.x <= W - 12 && p.y >= top && p.y <= bot)) { SITECAM[i] = { k, dx: cx - i * GAP, dz: cz, ly, ct: false }; return; }
  }
  console.warn('fitSite: no fit for', STATIONS[i]); SITECAM[i] = { k: 24, dx: cx - i * GAP, dz: cz, ly: cy, ct: false };
}
for (const G of STATION_GLB) loader0().load(G.url, (gltf) => {
  const o = gltf.scene; o.position.set(G.i * GAP, 0, 0);
  o.traverse(n => {
    if (n.isMesh) { n.castShadow = true; n.receiveShadow = true; }
    if (/^Tier_\d+/.test(n.name) || (n.userData && n.userData.hidden_by_default)) n.visible = false;
  });
  scene.add(o); o.updateMatrixWorld(true); stationObjs[G.i] = o; o.userData.camTarget = camTargetOf(o);
  if (phBox[G.i]) { scene.remove(phBox[G.i]); phBox[G.i].geometry.dispose(); phBox[G.i] = null; }
  const mx = new THREE.AnimationMixer(o); stationMixers.push(mx);
  for (const c of gltf.animations) if (G.loops.includes(c.name)) mx.clipAction(c).play();
  fitSite(G.i);
  (window.__ps3d.stationsLoaded = window.__ps3d.stationsLoaded || []).push(STATIONS[G.i]);
}, undefined, (e) => console.warn('station GLB failed, keeping gray box', G.url, e));

// ===== Mine station GLB (Art 9ff63d9, md5 a3ed7e1f…): rig + conveyor + silo + HT-04 truck (1 skinned mesh), markers, tiers, Cam_Target
let mixer = null, mine = null, rig = null, truck = null, rigLoaded = false, coverGone = false;
const acts = {}, MK = {};                  // MK: markers by name, Mine-local { x, y, z, e: extras }
const glowMats = [];
function setDigging(on) { for (const n of ['dig', 'conveyor_run']) { const a = acts[n]; if (a) a.paused = !on; } }   // rig + belt stop while the bin shows 'full'
function rigScale() { return 1; }          // the GLB station keeps true scale; growth shows as tier parts
// ===== tier parts: Art's Tier_NN nodes (extras tier N) shown by drill level, ease-out-back pop-in when bought
const tiers = [];                                   // { lv, g, t } t<0: settled
function buildTiers() {
  mine.traverse(n => { const lv = n.userData && n.userData.tier; if (/^Tier_\d+/.test(n.name) && lv > 0) { n.visible = false; n.userData.tier = lv; tiers.push({ lv, g: n, t: -1 }); } });
  tiers.sort((a, b) => a.lv - b.lv);
}
function applyTiers(popLv) {                         // restore everything owned; only a tier bought just now pops in
  for (const T of tiers) { const own = S.drill >= T.lv; T.g.visible = own;
    if (own && T.lv === popLv) { T.t = 0; T.g.scale.setScalar(.01); T.wait = focusTier(MINE, T.g); } else if (T.t < 0) T.g.scale.setScalar(1); }
  window.__ps3d.tiers = tiers.filter(T => T.g.visible).map(T => T.lv);
}
function updTiers(dt) {
  for (const T of tiers) { if (T.t < 0) continue; if (T.wait > 0) { T.wait -= dt; continue; } T.t += dt; const u = T.t / .4;
    if (u >= 1) { T.t = -1; T.g.scale.setScalar(1); continue; }
    const c = 2.2; T.g.scale.setScalar(Math.max(.01, 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2)); }   // ease-out-back pop
}
function applyRigLevel() {
  if (!mine) return;
  glowMats.forEach(m => m.emissiveIntensity = m.userData.ei0 * (1 + 0.12 * Math.min(S.drill - 1, 8)));
}
// the cover never fades onto empty ground: it stays until the Mine is in the scene
let coverTimer = 0;
function armCoverTimer() { clearTimeout(coverTimer); coverTimer = setTimeout(() => { coverTimer = 0; if (!rigLoaded) { console.warn('Mine GLB still loading after 15 s'); $('coverTx').textContent = 'Still loading…'; } }, 15000); }
armCoverTimer();
function hideCover() {
  const c = $('cover'); if (!c || c.classList.contains('off')) return; clearTimeout(coverTimer); c.classList.add('off');
  setTimeout(() => { c.remove(); coverGone = true; }, 420);
}
const loader = loader0();
function loadRig() { loader.load('models/mine_9ff63d9.glb?v=a3ed7e1f', (gltf) => {
  clearTimeout(coverTimer); coverTimer = 0;            // loaded: the 15 s 'still loading' warning can never fire late
  mine = gltf.scene; mine.position.set(MX, 0, 0);
  mine.traverse(o => {
    if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; if (o.isSkinnedMesh) o.frustumCulled = false;
      const m = o.material; if (m && m.emissive && m.emissive.getHex() && !glowMats.includes(m)) { m.userData.ei0 = m.emissiveIntensity; glowMats.push(m); } }
    if (o.userData && o.userData.kind) MK[o.name] = { x: o.position.x, y: o.position.y, z: o.position.z, e: o.userData };
  });
  scene.add(mine); mine.updateMatrixWorld(true);
  rig = mine.getObjectByName('Rig'); truck = mine.getObjectByName('Truck');
  stationObjs[MINE] = mine; mine.userData.camTarget = camTargetOf(mine);
  buildTiers(); applyTiers(0);
  mixer = new THREE.AnimationMixer(mine);
  for (const c of gltf.animations) acts[c.name] = mixer.clipAction(c);
  for (const n of ['dig', 'conveyor_run']) if (acts[n]) acts[n].play();
  for (const n of ['truck_drive', 'truck_load', 'truck_dump', 'truck_scoop']) { const a = acts[n]; if (!a) continue; a.play(); a.paused = true; a.time = 0; a.setEffectiveWeight(0); }   // truck clips are scrubbed from the trip clock, never free-running
  setDigging(!(S.bin >= binCap()));
  applyRigLevel(); buildTrack(); fitSite(MINE); restoreTrips();
  rigLoaded = true;
  renderer.compile(scene, camera);
  requestAnimationFrame(() => requestAnimationFrame(hideCover));   // fade only once the Mine has been drawn
  Object.assign(window.__ps3d, { mine, rig, truck, MK, clips: gltf.animations.map(a => a.name + ':' + a.duration.toFixed(2)) });
}, undefined, (e) => {
  console.error('Mine GLB load failed', e); clearTimeout(coverTimer); coverTimer = 0;
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
  camera.aspect = W / H; camera.userData.dist = camDist(camera.aspect); camera.updateProjectionMatrix(); if (typeof fitSite === 'function') for (const k in stationObjs) fitSite(+k);
}
addEventListener('resize', resize); resize();
function poseCam(cam, x) {
  const f = clamp(x / GAP, 0, N - 1), i0 = Math.floor(f), i1 = Math.min(N - 1, i0 + 1), u = f - i0, sm = u * u * (3 - 2 * u);
  const A = SITECAM[i0], B = SITECAM[i1], k = A.k + (B.k - A.k) * sm, dx = A.dx + (B.dx - A.dx) * sm, dz = A.dz + (B.dz - A.dz) * sm, ly = A.ly + (B.ly - A.ly) * sm;
  let lx = x + dx, lyy = ly, lz = dz, kk = k;
  if (cam === camera && FOC.w > 0) { const w = FOC.w; lx += (FOC.lx - lx) * w; lyy += (FOC.ly - lyy) * w; lz += (FOC.lz - lz) * w; kk += (FOC.k - kk) * w; }   // tier focus blend
  poseLook(cam, lx, lyy, lz, kk);
}
function poseLook(cam, lx, ly, lz, k) {
  const d = camera.userData.dist * k, e = THREE.MathUtils.degToRad(CAM.elev);
  cam.position.set(lx, ly + d * Math.sin(e), lz + d * Math.cos(e)); cam.lookAt(lx, ly, lz); cam.updateMatrixWorld();
}
// ===== tier focus (generic, any station; never saved): a revealed tier part whose world bounds fall outside the station frame
// gets a camera visit: ease the look point (and distance only if the part needs it) to the node 0.6 s, hold 1.5 s while it pops
// in, ease home 0.6 s. A 2nd off-frame tier revealed mid-visit is queued: after the current hold, ease straight to it (0.6 s),
// hold 1.5 s, then go home once. Swipe / dot tap cancels the visit and the queue (0.2 s release; the new station's normal frame
// takes over). Sheet open/close doesn't interrupt. If a visit outlives its expected end + 0.5 s it eases home anyway.
const FOC = { i: -1, ph: 'idle', w: 0, seg0: 0, end: 0, from: null, to: null, cur: { lx: 0, ly: 0, lz: 0, k: 1 }, q: [], rel: null, lx: 0, ly: 0, lz: 0, k: 1 };
const FOCT = { in: .6, hold: 1.5, out: .6, cancel: .2, safety: .6, grace: .5 };   // seconds, wall clock (not frame dt): slow frames can't stretch a visit
const _fb = new THREE.Box3(), _fcs = [];
for (let q = 0; q < 8; q++) _fcs.push(new THREE.Vector3());
const fss = (u) => { u = clamp(u, 0, 1); return u * u * (3 - 2 * u); };
function boxInFrame(cam, b, i) {
  const bd = band(), m = SITECAM[i].ct ? 0 : 12;     // Cam_Target stations: frame_w spans the full width; bounds-fit stations: the fit's 12 px margin
  let q = 0; for (const x of [b.min.x, b.max.x]) for (const y of [b.min.y, b.max.y]) for (const z of [b.min.z, b.max.z]) _fcs[q++].set(x, y, z);
  for (const c of _fcs) { const p = toScreen(c.x, c.y, c.z, cam, _scr); if (p.z > 1 || p.x < m || p.x > W - m || p.y < bd.top || p.y > bd.bot) return false; }
  return true;
}
// fit a world box whole inside the band between the HUD and the bar (12 px side margin), straight down -Z at the fixed 18° tilt / 38° vFOV, no azimuth:
// start at the station's own distance (never closer), re-centre the look point on the box's screen extent, back off 3% a step until it fits
const _fp = { x: 0, y: 0, z: 0 };
function boxScreen(cam, b) { let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9, behind = false;
  for (const x of [b.min.x, b.max.x]) for (const y of [b.min.y, b.max.y]) for (const z of [b.min.z, b.max.z]) { const p = toScreen(x, y, z, cam, _fp); if (p.z > 1) behind = true; x0 = Math.min(x0, p.x); x1 = Math.max(x1, p.x); y0 = Math.min(y0, p.y); y1 = Math.max(y1, p.y); }
  return { x0, x1, y0, y1, behind }; }
function fitBox(mc, b, k0) {
  const bd = band(), M = 12, e = THREE.MathUtils.degToRad(CAM.elev), ue = [0, Math.cos(e), -Math.sin(e)], vt = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
  const t = { lx: (b.min.x + b.max.x) / 2, ly: Math.max(0, (b.min.y + b.max.y) / 2), lz: (b.min.z + b.max.z) / 2, k: k0 };
  for (let n = 0; n < 200; n++) {
    for (let it = 0; it < 4; it++) {         // re-centre: box centre → band centre
      poseLook(mc, t.lx, t.ly, t.lz, t.k); const s = boxScreen(mc, b); if (s.behind) break;
      const pxm = (H / 2) / (camera.userData.dist * t.k * vt), dx = W / 2 - (s.x0 + s.x1) / 2, dy = (bd.top + bd.bot) / 2 - (s.y0 + s.y1) / 2;
      t.lx -= dx / pxm; t.ly += ue[1] * dy / pxm; t.lz += ue[2] * dy / pxm;
    }
    poseLook(mc, t.lx, t.ly, t.lz, t.k); const s = boxScreen(mc, b);
    if (!s.behind && s.x0 >= M && s.x1 <= W - M && s.y0 >= bd.top && s.y1 <= bd.bot) { t.fit = true; return t; }
    t.k *= 1.03;
  }
  t.fit = false; return t;
}
function focusHome(i) { const C = SITECAM[i]; return { lx: i * GAP + C.dx, ly: C.ly, lz: C.dz, k: C.k }; }
function focusTier(i, node) {
  if (!node || !camera.userData.dist || S.site !== i || drag) return 0;
  const vis = node.visible, sc = node.scale.x; node.visible = true; node.scale.setScalar(1); node.updateMatrixWorld(true);
  _fb.setFromObject(node); node.visible = vis; node.scale.setScalar(sc); node.updateMatrixWorld(true);
  if (_fb.isEmpty()) return 0;
  const C = SITECAM[i], hm = focusHome(i), mc = camera.clone();
  poseLook(mc, hm.lx, hm.ly, hm.lz, hm.k);
  const inside = boxInFrame(mc, _fb, i);
  const info = window.__ps3d.lastFocus = { i, node: node.name, inside, box: [_fb.min.toArray().map(v => +v.toFixed(1)), _fb.max.toArray().map(v => +v.toFixed(1))] };
  if (inside) return 0;                              // already in frame: no camera move
  const tg = fitBox(mc, _fb, C.k); tg.name = node.name;   // frame the part's whole world bounds in the HUD–bar band (pull back as far as it needs)
  Object.assign(info, { look: [+tg.lx.toFixed(1), +tg.ly.toFixed(1), +tg.lz.toFixed(1)], k: +tg.k.toFixed(3), k0: +C.k.toFixed(3), fit: tg.fit });
  const now = performance.now(), T = FOCT; let delay;
  if (FOC.i === i && (FOC.ph === 'in' || FOC.ph === 'move' || FOC.ph === 'hold')) {        // mid-visit: queue it
    FOC.q.push(tg); const holdEnd = FOC.seg0 + (T.in + T.hold) * 1000;
    delay = (holdEnd - now) / 1000 + (FOC.q.length - 1) * (T.in + T.hold) + T.in; info.queued = FOC.q.length;
  } else {
    if (FOC.i === i && FOC.w > 0 && !FOC.rel) {   // easing home: move on from where the camera is now, no jump
      FOC.from = { lx: FOC.lx, ly: FOC.ly, lz: FOC.lz, k: FOC.k }; FOC.ph = 'move'; FOC.w = 1;
    } else { FOC.from = null; FOC.ph = 'in'; FOC.w = 0; }
    Object.assign(FOC, { i, to: tg, seg0: now, q: [], rel: null }); delay = T.in;
  }
  FOC.end = FOC.seg0 + (T.in + T.hold + FOC.q.length * (T.in + T.hold) + T.out) * 1000;   // expected end of the whole visit
  info.delay = +delay.toFixed(2); return Math.max(0, delay);  // the caller delays the pop-in until the camera has arrived
}
function releaseFocus(by, dur) { if (FOC.i < 0 || FOC.rel) return; FOC.q.length = 0; FOC.rel = { t0: performance.now(), w0: FOC.w, dur, by }; FOC.ph = by === 'safety' ? 'safety' : 'cancel'; }
function cancelFocus(by) { if (FOC.i < 0 || FOC.rel) return; window.__ps3d.focusCanceled = { by, ph: FOC.ph, w: +FOC.w.toFixed(3), q: FOC.q.length }; releaseFocus(by, FOCT.cancel); }
function updFocus() {
  if (FOC.i < 0) return;
  if (S.site !== FOC.i) cancelFocus('site');
  const now = performance.now(), T = FOCT;
  if (!FOC.rel && now > FOC.end + T.grace * 1000) { window.__ps3d.focusSafety = (window.__ps3d.focusSafety || 0) + 1; releaseFocus('safety', T.safety); }
  if (FOC.rel) { const u = (now - FOC.rel.t0) / 1000 / FOC.rel.dur; FOC.w = FOC.rel.w0 * (1 - fss(u)); if (u >= 1) { FOC.w = 0; FOC.i = -1; FOC.ph = 'idle'; FOC.rel = null; return; } }
  else {
    let t = (now - FOC.seg0) / 1000;
    if (t >= T.in + T.hold && FOC.q.length) {      // hold done, next queued tier: ease straight there
      FOC.from = { lx: FOC.to.lx, ly: FOC.to.ly, lz: FOC.to.lz, k: FOC.to.k }; FOC.to = FOC.q.shift(); FOC.seg0 += (T.in + T.hold) * 1000; FOC.ph = 'move'; t = (now - FOC.seg0) / 1000;
    }
    if (t < T.in) { if (FOC.from) { FOC.w = 1; FOC.ph = 'move'; } else { FOC.w = fss(t / T.in); FOC.ph = 'in'; } }
    else if (t < T.in + T.hold) { FOC.w = 1; FOC.ph = 'hold'; }
    else { FOC.w = 1 - fss((t - T.in - T.hold) / T.out); FOC.ph = 'out'; if (t >= T.in + T.hold + T.out) { FOC.w = 0; FOC.i = -1; FOC.ph = 'idle'; return; } }
    // the blend target: the current stop, or a straight ease from the previous stop during a move
    const to = FOC.to, f = FOC.from, u = f && t < T.in ? fss(t / T.in) : 1;
    FOC.lx = f && u < 1 ? f.lx + (to.lx - f.lx) * u : to.lx; FOC.ly = f && u < 1 ? f.ly + (to.ly - f.ly) * u : to.ly;
    FOC.lz = f && u < 1 ? f.lz + (to.lz - f.lz) * u : to.lz; FOC.k = f && u < 1 ? f.k + (to.k - f.k) * u : to.k;
    if (t >= T.in && f) FOC.from = null;
  }
}
let shK = 1;
function placeCamera() { poseCam(camera, camX);
  const f = clamp(camX / GAP, 0, N - 1), i0 = Math.floor(f), A = SITECAM[i0], B = SITECAM[Math.min(N - 1, i0 + 1)], u = f - i0, k = A.k + (B.k - A.k) * u, dx = A.dx + (B.dx - A.dx) * u, dz = A.dz + (B.dz - A.dz) * u;
  if (Math.abs(k - shK) > .01) { shK = k; Object.assign(sun.shadow.camera, { left: -22 * k, right: 22 * k, top: 22 * k, bottom: -22 * k, far: 120 * k }); sun.shadow.camera.updateProjectionMatrix(); }
  sun.position.set(camX + dx - 30 * k, 22 * k, dz + 18 * k); sun.target.position.set(camX + dx, 0, dz); }
const _v = new THREE.Vector3();
function toScreen(x, y, z, cam = camera, o = {}) { _v.set(x, y, z).project(cam); o.x = (_v.x + 1) / 2 * W; o.y = (1 - _v.y) / 2 * H; o.z = _v.z; return o; }
const _scr = { x: 0, y: 0, z: 0 }, _pt = { x: 0, y: 0, l: '' };   // reused by per-frame overlays (no per-frame allocations)
const mPerPx = () => (2 * camera.userData.dist * SITECAM[S.site].k * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect) / W;   // finger tracks the ground 1:1 at the current station's framing

// ===== UI: tag, name, dots
$('tag').textContent = document.body.dataset.tag + (DEV ? ' · DEV' : '');
const nameEl = $('name'), dotsEl = $('dots');
STATIONS.forEach((n, i) => { const b = document.createElement('button'); b.setAttribute('aria-label', n); dotsEl.appendChild(b); });
function ui() { nameEl.textContent = STATIONS[S.site]; [...dotsEl.children].forEach((b, i) => b.classList.toggle('on', i === S.site)); }
function goSite(k) { k = clamp(k, 0, N - 1); if (k !== S.site) { S.site = k; save(); } target = k * GAP; ui(); }
dotsEl.addEventListener('pointerdown', (e) => {   // 44 px tap band: nearest dot wins
  e.stopPropagation(); cancelFocus('dot'); const r = dotsEl.getBoundingClientRect(); goSite(Math.round((e.clientX - r.left) / r.width * N - .5));
});
ui();

// ===== swipe: always exactly one station from S.site; tiny drags spring back; taps go to deposits
let drag = null;
canvas.addEventListener('pointerdown', (e) => {
  if (drag) return; const t = e.timeStamp || performance.now();     // event time, so a busy frame can't distort the flick speed
  if (e.isPrimary === false) return;
  drag = { id: e.pointerId, x0: e.clientX, y0: e.clientY, t0: t, cx: camX, base: S.site, s: [[t, e.clientX]], moved: 0 };
  try { canvas.setPointerCapture(e.pointerId); } catch (_) {}
});
canvas.addEventListener('pointermove', (e) => {
  if (!drag || e.pointerId !== drag.id) return; const t = e.timeStamp || performance.now();
  const dx = e.clientX - drag.x0; drag.moved = Math.max(drag.moved, Math.hypot(dx, e.clientY - drag.y0));
  if (drag.moved > 10 && FOC.i >= 0) cancelFocus('swipe');              // a swipe cancels a tier focus and takes over
  const lo = Math.max((drag.base - 1) * GAP, -GAP * .3), hi = Math.min((drag.base + 1) * GAP, GAP * (N - 1 + .3));
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
  const d = drag; drag = null; try { canvas.releasePointerCapture(d.id); } catch (_) {}
  const cancel = !e || e.type !== 'pointerup';                    // pointercancel / lost capture: coordinates can't be trusted → spring back
  const dx = cancel ? 0 : x - d.x0, v = cancel ? 0 : releaseVelocity(d, t, x);
  let dir = 0;                                                     // velocity only picks the direction; the step is always exactly 1
  if (Math.abs(dx) > 0.15 * W) dir = dx < 0 ? 1 : -1;
  else if (Math.abs(v) > 0.35 && Math.abs(dx) >= 30) dir = v < 0 ? 1 : -1;   // a flick needs speed AND ≥30 px travel
  window.__ps3d.lastSwipe = { dx, v: +v.toFixed(3), dir, from: d.base };
  if (!dir && d.moved < 10 && t - d.t0 < 500 && !cancel) tap(e.clientX, e.clientY);
  goSite(d.base + dir);
}
canvas.addEventListener('pointerup', endDrag); canvas.addEventListener('pointercancel', endDrag); canvas.addEventListener('lostpointercapture', endDrag);

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
function popXY() {                    // where '+$X' pops: under the HUD money, or under Eve's card while she talks (never on her text)
  const m = moneyXY(); if (!eveCur) return { x: m.x, y: m.y + 30 };
  const r = eveEl.getBoundingClientRect(); return { x: clamp(m.x, 50, W - 50), y: r.bottom + 36 };
}

// ===== ore chunks: 2 instanced meshes (He-3 cyan glow, platinum silver), fly from the hopper to the money counter
const CH_MAX = 32, CHK = 3;          // CHK: chunk start scale (readable at the Mine's 37 m frame), 1 at the counter
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
    chunks.push({ kind, idx, t: -i * 0.07, dur: 0.75 + Math.random() * .15, p0: from.clone().add(new THREE.Vector3((Math.random() - .5) * .8 * CHK, Math.random() * .4 * CHK, (Math.random() - .5) * .6 * CHK)),
      up: 2.5 + Math.random() * 2, spin: Math.random() * 6, done: first ? () => { const m = popXY(); pop('+' + fmt(value), m.x, m.y, cls); bumpMoney(); } : null });
    first = false;
  }
  if (!n || first) { const m = popXY(); pop('+' + fmt(value), m.x, m.y, cls); bumpMoney(); }
}
function updChunks(dt) {
  if (!chunks.length) return; counterWorld(_t);
  for (let i = chunks.length - 1; i >= 0; i--) {
    const c = chunks[i]; c.t += dt; const u = clamp(c.t / c.dur, 0, 1), k = ease(u);
    if (c.t < 0) { chMesh[c.kind].setMatrixAt(c.idx, ZERO); continue; }
    _p.copy(c.p0).lerp(_t, k); _p.y += Math.sin(u * Math.PI) * c.up * (1 - u * .5);
    _s.setScalar((1 - .55 * u) * (CHK - (CHK - 1) * u)); _q.setFromEuler(_e.set(c.spin * u, c.spin * .7 * u, 0));
    chMesh[c.kind].setMatrixAt(c.idx, _m.compose(_p, _q, _s));
    if (u >= 1) { chMesh[c.kind].setMatrixAt(c.idx, ZERO); freeIdx[c.kind].push(c.idx); const ls = toScreen(_p.x, _p.y, _p.z); window.__ps3d.lastLand = { x: Math.round(ls.x), y: Math.round(ls.y), target: cashTarget().id }; if (c.done) c.done(); chunks.splice(i, 1); }
  }
  chMesh.forEach(m => m.instanceMatrix.needsUpdate = true);
}

// ===== mine sim: drill fills the bin; when full it shows 'full', then the load auto-sells
let fullT = 0;
const CHUTE = [3.1, 4.35, 4.5];   // conveyor discharge chute (Path_Load extras.chute_glTF)
const hopperPos = () => new THREE.Vector3(MX + CHUTE[0], CHUTE[1], CHUTE[2]);
function sellLoad() {
  const n = Math.floor(S.bin + 1e-6); S.bin = Math.max(0, S.bin - n);
  const value = n * CFG.oreValue; S.money += value; setDigging(true);
  window.__ps3d.loads = (window.__ps3d.loads || 0) + 1;
  if (S.site === MINE) flyChunks(Math.max(3, n * 2), hopperPos(), value); else bumpMoney();
}
function simMine(dt) {
  if (fullT > 0) { fullT -= dt; if (fullT <= 0) { fullT = 0; sellLoad(); } return; }
  S.bin += rate() / 60 * dt;
  if (S.bin >= binCap()) { S.bin = binCap(); fullT = CFG.fullHold; setDigging(false); }
}

// ===== deposits: glowing cyan disc + floating gem at Art's Dep_01 / Dep_02 markers (max 2), respawn every ~8 s
const glowTex = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
  const r = g.createRadialGradient(64, 64, 4, 64, 64, 64);
  r.addColorStop(0, '#e8ffffff'); r.addColorStop(.35, '#58ecffdd'); r.addColorStop(.7, '#1fb8ff66'); r.addColorStop(1, '#1fb8ff00');
  g.fillStyle = r; g.fillRect(0, 0, 128, 128); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
})();
const discGeo = new THREE.CircleGeometry(1, 32).rotateX(-Math.PI / 2);
const discMat = new THREE.MeshBasicMaterial({ map: glowTex, transparent: true, opacity: 1, depthWrite: false, blending: THREE.AdditiveBlending, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 });   // y 0.1 + offset: no z-fighting with the road
discMat.color.setScalar(1.7);           // additive glow pushed past 1.0 so it reads on the bright regolith
const GEM = 2.2, GEMY = 2.4;          // gem scale / float height: readable at the Mine's ~116 m camera
const gemGeo = new THREE.OctahedronGeometry(.42, 0); gemGeo.scale(1, 1.5, 1);
const gemMat = new THREE.MeshStandardMaterial({ color: 0x5ff0ff, emissive: 0x22d0ff, emissiveIntensity: 2.6, roughness: .3, flatShading: true });
const DEP_MIN_PX = 44, GEM_MIN_PX = 26, GEM_W = 0.84;   // disc ≥ 44 CSS px across (at the pulse low point), gem ≥ 26 px wide; GEM_W = gem width at scale 1 (m)
const _dw = new THREE.Vector3();
const DEP_NAMES = ['Dep_01', 'Dep_02'], DISC_Y = 0.1;
const deposits = []; let depTimer = 0, depSeq = 0;
function band() {
  const top = Math.max(hudEl.getBoundingClientRect().bottom, 120) + 24;   // station title moved to the bottom (above the dots); top of the band = under the HUD/Eve band (unchanged 144 px)
  const sheetTop = $('sheetWrap').getBoundingClientRect().top;      // open sheet top edge
  return { top, bot: Math.min(sheetTop, dotsEl.getBoundingClientRect().top, nameEl.getBoundingClientRect().top) - 34, l: 34, r: W - 34 };
}
function spawnDeposit(name) {
  if (!mine || deposits.length >= CFG.depositMax) return null;
  const free = DEP_NAMES.filter(n => MK[n] && !deposits.some(d => d.mk === n)); if (!free.length) return null;
  return makeDeposit(name && free.includes(name) ? name : free[Math.floor(Math.random() * free.length)]);
}
function makeDeposit(mk, claimed = false) {
  const m = MK[mk], x = MX + m.x, z = m.z, r = Math.max(1.6, (m.e.radius_m || 1.4) * 1.15);
  const disc = new THREE.Mesh(discGeo, discMat); disc.position.set(x, DISC_Y, z); disc.renderOrder = 2;
  const gem = new THREE.Mesh(gemGeo, gemMat); gem.position.set(x, GEMY, z); gem.castShadow = false;
  scene.add(disc, gem);
  const d = { id: ++depSeq, mk, spur: m.e.scoop_from || nearestSpur(m), x, z, r, rs: r, disc, gem, age: claimed ? 1 : 0, claimed, dig: 0 }; deposits.push(d); return d;
}
function nearestSpur(m) { let b = null, bd = Infinity; for (const n in MK) if (/^Path_Spur_/.test(n)) { const q = MK[n], dd = Math.hypot(q.x - m.x, q.z - m.z); if (dd < bd) { bd = dd; b = n; } } return b; }
function removeDeposit(d) { if (!d || !deposits.includes(d)) return; scene.remove(d.disc, d.gem); if (d.qr) d.qr.style.display = 'none'; deposits.splice(deposits.indexOf(d), 1); }
// 'queued' ring: a deposit tapped while the truck is busy (its trip has no start time yet) shows it until the truck leaves for it
const qRings = [];
function qRingEl(k) { let el = qRings[k]; if (!el) { el = qRings[k] = document.createElement('div'); el.className = 'qring'; el.innerHTML = '<b>QUEUED</b>'; document.body.appendChild(el); } return el; }
function updQueued() {
  let k = 0; const live = S.site === MINE && Math.abs(camX - MX) < 3 && !document.hidden;
  for (const d of deposits) {
    const tr = d.trip && S.trips.find(t => t && t.id === d.trip), q = !!(tr && tr.t0 == null);
    d.queued = q; if (!q || !live) continue;
    const el = d.qr = qRingEl(k++), h = depTapR(d), r = Math.round(Math.max(30, h.glow * 1.05));
    el.style.display = 'block'; el.style.left = h.x.toFixed(1) + 'px'; el.style.top = h.y.toFixed(1) + 'px'; el.style.width = el.style.height = 2 * r + 'px'; el.style.margin = -r + 'px 0 0 ' + -r + 'px';
  }
  for (; k < qRings.length; k++) qRings[k].style.display = 'none';
  window.__ps3d.queued = deposits.filter(d => d.queued).map(d => d.mk);
}
function updDeposits(dt, time) {
  depTimer += dt;
  if (deposits.length < CFG.depositMax && depTimer >= CFG.depositEvery) { depTimer = 0; spawnDeposit(); }
  if (deposits.length >= CFG.depositMax) depTimer = 0;
  discMat.color.setScalar(1.5 + .5 * (.5 + .5 * Math.sin(time * 4)));   // shared glow brightens with the pulse
  for (const d of deposits) {
    d.age += dt; const pin = d.age < .35 ? 1 - (1 - d.age / .35) ** 3 * (1 - 1.7 * (d.age / .35)) : 1;
    const shrink = d.claimed ? 1 - .85 * d.dig : 1, ph = .5 + .5 * Math.sin(time * 4 + d.id), pulse = 1 + .25 * ph;   // 1.0 → 1.25
    // on-screen size floor: scale with camera distance so the deposit never reads smaller than ~44 px across
    const pxm = (H / 2) / (Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * Math.max(1, camera.position.distanceTo(_dw.set(d.x, 0, d.z))));
    d.rs = Math.max(d.r, DEP_MIN_PX / 2 / pxm); const gs = Math.max(GEM, GEM_MIN_PX / (GEM_W * pxm));
    d.disc.scale.setScalar(Math.max(.01, pin * pulse * shrink * d.rs));
    d.gem.scale.setScalar(Math.max(.01, pin * shrink * gs)); d.gem.rotation.y = time * 1.6 + d.id;
    d.gem.position.y = GEMY + .4 * Math.sin(time * 2.6 + d.id);
  }
}
// on-screen tap circle for a deposit: ≥ 44 CSS px radius whatever the camera distance, else 1.1× the projected glow
function depTapR(d) {
  const c = toScreen(d.x, 0.6, d.z), cx = c.x, cy = c.y; let rr = 0;
  for (let k = 0; k < 8; k++) { const a = k / 8 * Math.PI * 2, p = toScreen(d.x + (d.rs || d.r) * Math.cos(a), 0, d.z + (d.rs || d.r) * Math.sin(a)); rr = Math.max(rr, Math.hypot(p.x - cx, p.y - cy)); }
  return { x: cx, y: cy, R: Math.max(44, rr * 1.1), glow: rr };
}

// ===== HT-04 haul truck (Art's skinned Truck node). Everything is a pure function of the trip's wall clock, so a reload
// or a locked phone resumes mid-trip and pays exactly once. Route (forward only, wide arcs on the loop):
//   Path_Load → loop → Path_Spur (stop, truck_scoop, arm stowed) → loop → Path_Dump_Approach → reverse 1.5 s → Path_Dump
//   → truck_dump 3 s (bonus pays as the bed starts tipping) → drive off east → Path_02 → reverse 1.5 s under the chute → truck_load
const TRK = { n: 0, x: null, z: null, c: null, L: 0 };      // closed haul loop, sampled (Mine-local metres)
const TV = { a: 18, vMin: 7, vMax: 16, vRet: 9, target: 7.0, rev: 1.5, scoop: 1.2, dump: 3.0, load: 0.8, wheelC: 2 * Math.PI * 0.85 };
function buildTrack() {
  const names = ['Path_Load']; for (let i = 1; i < 40; i++) { const n = 'Path_' + String(i).padStart(2, '0'); if (MK[n]) names.push(n); }
  const curve = new THREE.CatmullRomCurve3(names.map(n => new THREE.Vector3(MK[n].x, 0, MK[n].z)), true, 'centripetal');
  const n = 900, x = new Float32Array(n + 1), z = new Float32Array(n + 1), c = new Float32Array(n + 1), v = new THREE.Vector3();
  for (let i = 0; i <= n; i++) { curve.getPoint(i / n, v); x[i] = v.x; z[i] = v.z; if (i) c[i] = c[i - 1] + Math.hypot(x[i] - x[i - 1], z[i] - z[i - 1]); }
  Object.assign(TRK, { n, x, z, c, L: c[n] });
  TRK.sLoad = 0; TRK.sApp = sAt(MK.Path_Dump_Approach); TRK.sPull = sAt(MK.Path_02);
  window.__ps3d.track = { L: +TRK.L.toFixed(2), sApp: +TRK.sApp.toFixed(2), sPull: +TRK.sPull.toFixed(2), spur: DEP_NAMES.map(n => MK[n] && +sAt(MK[MK[n].e.scoop_from]).toFixed(2)) };
}
function sAt(m) { let b = 0, bd = Infinity; for (let i = 0; i < TRK.n; i++) { const d = (TRK.x[i] - m.x) ** 2 + (TRK.z[i] - m.z) ** 2; if (d < bd) { bd = d; b = i; } } return TRK.c[b]; }
function loopXZ(s, o) { s = ((s % TRK.L) + TRK.L) % TRK.L; let lo = 0, hi = TRK.n; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (TRK.c[m] <= s) lo = m; else hi = m; }
  const u = (s - TRK.c[lo]) / Math.max(1e-6, TRK.c[hi] - TRK.c[lo]); o[0] = TRK.x[lo] + (TRK.x[hi] - TRK.x[lo]) * u; o[1] = TRK.z[lo] + (TRK.z[hi] - TRK.z[lo]) * u; return o; }
// a driving path = polyline (optional straight lead-in) + the loop from s0 forward to s1; sampled once at plan time
function mkPath(lead, s0, s1) {
  const xs = [], zs = [], o = [0, 0]; if (lead) for (const p of lead) { xs.push(p[0]); zs.push(p[1]); }
  let len = s1 - s0; if (len < 0) len += TRK.L; const k = Math.max(2, Math.ceil(len / 0.25));
  for (let i = 0; i <= k; i++) { loopXZ(s0 + len * i / k, o); if (i === 0 && xs.length && Math.hypot(o[0] - xs[xs.length - 1], o[1] - zs[zs.length - 1]) < .05) continue; xs.push(o[0]); zs.push(o[1]); }
  const n = xs.length, X = Float32Array.from(xs), Z = Float32Array.from(zs), C = new Float32Array(n);
  for (let i = 1; i < n; i++) C[i] = C[i - 1] + Math.hypot(X[i] - X[i - 1], Z[i] - Z[i - 1]);
  return { n, X, Z, C, L: C[n - 1] };
}
function pathXZ(P, s, o) { s = clamp(s, 0, P.L); let lo = 0, hi = P.n - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (P.C[m] <= s) lo = m; else hi = m; }
  const u = (s - P.C[lo]) / Math.max(1e-6, P.C[hi] - P.C[lo]); o[0] = P.X[lo] + (P.X[hi] - P.X[lo]) * u; o[1] = P.Z[lo] + (P.Z[hi] - P.Z[lo]) * u; return o; }
function prof(L, v0, v, a) {                 // accelerate v0→v, cruise, brake to a stop exactly at L
  v = Math.max(v, v0); let d0 = (v * v - v0 * v0) / (2 * a), d1 = v * v / (2 * a);
  if (d0 + d1 > L) { v = Math.max(v0, Math.sqrt((2 * a * L + v0 * v0) / 2)); d0 = (v * v - v0 * v0) / (2 * a); d1 = v * v / (2 * a); if (d0 + d1 > L) { a = v0 * v0 / (2 * L); v = v0; d0 = 0; d1 = L; } }
  const t0 = (v - v0) / a, t1 = v / a, tc = Math.max(0, (L - d0 - d1) / v);
  return { L, v0, v, a, t0, tc, t1, d0, d1, T: t0 + tc + t1 };
}
function profAt(p, t, o) {
  if (t < p.t0) { o[0] = p.v0 * t + .5 * p.a * t * t; o[1] = p.v0 + p.a * t; }
  else if (t < p.t0 + p.tc) { o[0] = p.d0 + p.v * (t - p.t0); o[1] = p.v; }
  else { const u = clamp(t - p.t0 - p.tc, 0, p.t1); o[0] = Math.min(p.L, p.L - p.d1 + p.v * u - .5 * p.a * u * u); o[1] = Math.max(0, p.v - p.a * u); }
  return o;
}
const planCache = new Map();
function buildPlan(tr, v) {
  const D = MK.Path_Dump, A = MK.Path_Dump_Approach, Ld = MK.Path_Load, Pu = MK.Path_02, sp = MK[tr.spur], sS = sAt(sp);
  const st = []; let t = 0; const add = (o) => { o.ts = t; t += o.T; st.push(o); return o; };
  const f = tr.from || { k: 'load' }; let pa, v0 = 0, full = true;
  if (f.k === 'dump') { pa = mkPath([[D.x, D.z]], TRK.sApp, sS); full = false; }
  else if (f.k === 'ret') { full = false; v0 = f.v || 0;
    if (f.d < 4) pa = mkPath([[D.x + f.d, D.z]], TRK.sApp, sS); else pa = mkPath(null, TRK.sApp + (f.d - 4), sS); }
  else pa = mkPath(null, TRK.sLoad, sS);
  const pA = prof(pa.L, v0, v, TV.a); add({ k: 'drive', P: pa, p: pA, T: pA.T, full });
  add({ k: 'scoop', T: TV.scoop, x: sp.x, z: sp.z, yaw: THREE.MathUtils.degToRad(sp.e.yaw_deg || 0), full });
  const scoopEnd = t;
  const pb = mkPath(null, sS, TRK.sApp), pB = prof(pb.L, 0, v, TV.a); add({ k: 'drive', P: pb, p: pB, T: pB.T, full: true });
  add({ k: 'rev', T: TV.rev, ax: A.x, az: A.z, bx: D.x, bz: D.z, full: true });
  const payAt = t; add({ k: 'dump', T: TV.dump, x: D.x, z: D.z });
  const dumpEnd = t;
  const pc = mkPath([[D.x, D.z]], TRK.sApp, TRK.sPull), pC = prof(pc.L, 0, TV.vRet, TV.a); add({ k: 'drive', P: pc, p: pC, T: pC.T, full: false, ret: true });
  const retEnd = t;
  add({ k: 'rev', T: TV.rev, ax: Pu.x, az: Pu.z, bx: Ld.x, bz: Ld.z, full: false });
  add({ k: 'load', T: TV.load, x: Ld.x, z: Ld.z });
  return { st, v, scoopEnd, payAt, dumpEnd, retEnd, total: t };
}
function planOf(tr) {
  let P = planCache.get(tr.id); if (P) return P;
  let lo = TV.vMin, hi = TV.vMax;               // cruise speed so tap → payout lands on TV.target (5–8 s rule), clamped
  for (let i = 0; i < 24; i++) { const m = (lo + hi) / 2; if (buildPlan(tr, m).payAt > TV.target) lo = m; else hi = m; }
  P = buildPlan(tr, hi); planCache.set(tr.id, P); return P;
}
let truckRing = null, wheelPh = 0, tripSeq = 0;
const _o = [0, 0], _o2 = [0, 0], _pf = [0, 0];
function truckBusy() {   // trips that hold a truck: queued ones, and the live one until its dump starts (1 truck: a tap mid-dump queues one trip); legacy 2-truck saves keep the old rule
  const two = S.rovers >= 2; let n = 0;
  for (const tr of S.trips) { if (!tr || !tr.v2) continue; if (tr.t0 == null) { n++; continue; } const P = planOf(tr), el = (Date.now() - tr.t0) / 1000; if (el < (two ? P.dumpEnd : P.payAt)) n++; }
  return n;
}
function sendTruck(d) {
  if (!mine || !TRK.n) return false;
  advanceTrips(Date.now());                                     // settle the current trip first (pays it if due) before re-routing
  if (truckBusy() >= Math.max(1, S.rovers)) return false;     // 1 truck on the loop; a 2nd truck purchase lets a 2nd deposit queue
  const now = Date.now(), tr = { v2: 1, id: ++tripSeq + '-' + now, dep: d.mk, spur: d.spur, bonus: CFG.roverBonus, t0: now, tapAt: now, from: { k: 'load' }, paid: false };
  const cur = S.trips[0];
  if (cur && cur.t0 != null) {
    const P = planOf(cur), el = (now - cur.t0) / 1000;
    if (el < P.dumpEnd) { tr.t0 = null; tr.after = 'dump'; }                       // after the dump already underway, straight from Path_Dump
    else if (el < P.retEnd) {                                                    // driving back: carry on through the next marker to the spur, no stop at the load bay
      const c = P.st.find(o => o.ret), lt = el - c.ts; profAt(c.p, lt, _pf);
      tr.from = { k: 'ret', d: +_pf[0].toFixed(3), v: +_pf[1].toFixed(3) }; S.trips.shift(); planCache.delete(cur.id);
    } else { tr.t0 = null; tr.after = 'end'; }                                  // backing under the chute / loading: ≤ 2.3 s, then go
  }
  d.claimed = true; d.trip = tr.id; S.trips.push(tr); save();
  window.__ps3d.lastSend = { at: now, dep: d.mk, after: tr.after || tr.from.k };
  return true;
}
function payTrip(tr, P, live) {
  tr.paid = true; S.money += tr.bonus; S.dep++; save();     // flagged before anything else: can never pay twice
  (window.__ps3d.trips = window.__ps3d.trips || []).push({ wall: Date.now() - (tr.tapAt || tr.t0), bonus: tr.bonus, dep: tr.dep });
  if (live && S.site === MINE && !document.hidden) {
    const D = MK.Path_Dump, w = new THREE.Vector3(MX + D.x - 3.3, 3.2, D.z), sp = toScreen(w.x, w.y, w.z);
    pop('+' + fmt(tr.bonus) + ' bonus', sp.x, sp.y - 20, 'bonus'); flyChunks(4, w, tr.bonus, 'bonus');
  } else bumpMoney();
}
function advanceTrips(now) {
  for (let guard = 0; guard < 8; guard++) {
    const tr = S.trips[0]; if (!tr) return;
    if (tr.t0 == null) { tr.t0 = now; tr.from = { k: 'load' }; save(); }
    let el = (now - tr.t0) / 1000; if (el < 0) { tr.t0 = now; el = 0; }      // clock moved backward: restart the trip, never skip ahead
    const P = planOf(tr);
    if (!tr.paid && el >= P.payAt) payTrip(tr, P, el - P.payAt < 1);
    if (el >= P.scoopEnd && !tr.ate) { tr.ate = true; const d = deposits.find(d => d.trip === tr.id); if (d) removeDeposit(d); }
    const nx = S.trips[1];
    if (nx && nx.t0 == null && nx.after === 'dump' && el >= P.dumpEnd) { nx.t0 = tr.t0 + P.dumpEnd * 1000; nx.from = { k: 'dump' }; nx.tapAt = nx.tapAt || nx.t0; S.trips.shift(); planCache.delete(tr.id); save(); continue; }
    if (el >= P.total) { S.trips.shift(); planCache.delete(tr.id); if (nx && nx.t0 == null) { nx.t0 = tr.t0 + P.total * 1000; nx.from = { k: 'load' }; } save(); continue; }
    return;
  }
}
setInterval(() => { if (mine && TRK.n && S.trips.length) advanceTrips(Date.now()); }, 200);   // payouts keep wall-clock time even when frames stall (GPU-bound / throttled rAF)
function restoreTrips() {          // on load: legacy rover trips pay once; claimed deposits re-show until their scoop is done
  const keep = [];
  for (const tr of S.trips) {
    if (!tr) continue;
    if (!tr.v2) { if (tr.bonus > 0) { S.money += tr.bonus; S.dep++; } continue; }   // pre-truck save (S.trips[i] per rover): settle it, exactly once
    keep.push(tr);
  }
  S.trips = keep; save();
  for (const tr of S.trips) {
    if (tr.ate || !MK[tr.dep]) continue;
    if (tr.t0 != null && (Date.now() - tr.t0) / 1000 >= planOf(tr).scoopEnd) continue;
    const d = makeDeposit(tr.dep, true); d.trip = tr.id;
  }
}
function setTruckClips(load, loadT, dump, dumpT, scoopT, wheelT) {
  const L = acts.truck_load, Dp = acts.truck_dump, Sc = acts.truck_scoop, Dr = acts.truck_drive;
  if (L) { L.setEffectiveWeight(load ? 1 : 0); L.time = loadT; }
  if (Dp) { Dp.setEffectiveWeight(dump ? 1 : 0); Dp.time = dumpT; }
  if (Sc) { Sc.setEffectiveWeight(1); Sc.time = scoopT; }
  if (Dr) { Dr.setEffectiveWeight(1); Dr.time = wheelT; }
}
function updTruck(dt) {
  if (!truck || !TRK.n) return;
  const now = Date.now(); advanceTrips(now);
  const tr = S.trips[0], Ld = MK.Path_Load, dDur = acts.truck_dump ? acts.truck_dump.getClip().duration : 3, lDur = acts.truck_load ? acts.truck_load.getClip().duration : .8;
  let x = Ld.x, z = Ld.z, yaw = 0, sp = 0, phase = 'idle', showRing = false, ringU = 0;
  let loadOn = false, loadT = 0, dumpT = 0, scoopT = 0;           // default: parked under the chute with a full bed (dump clip at 0 = bed down, heap full)
  if (tr && tr.t0 != null) {
    const P = planOf(tr), el = (now - tr.t0) / 1000; let o = P.st[P.st.length - 1];
    for (let i = 0; i < P.st.length; i++) if (el < P.st[i].ts + P.st[i].T) { o = P.st[i]; break; }
    const lt = clamp(el - o.ts, 0, o.T); phase = o.k;
    if (o.k === 'drive') {
      profAt(o.p, lt, _pf); pathXZ(o.P, _pf[0], _o); pathXZ(o.P, _pf[0] + 0.8, _o2);
      if (_pf[0] + 0.8 > o.P.L) { pathXZ(o.P, _pf[0] - 0.8, _o2); yaw = Math.atan2(-(_o[1] - _o2[1]), _o[0] - _o2[0]); } else yaw = Math.atan2(-(_o2[1] - _o[1]), _o2[0] - _o[0]);
      x = _o[0]; z = _o[1]; sp = _pf[1]; dumpT = o.full ? 0 : dDur - 1e-3;
    } else if (o.k === 'rev') {
      const u = lt / o.T, e = u * u * (3 - 2 * u), L = Math.hypot(o.bx - o.ax, o.bz - o.az);
      x = o.ax + (o.bx - o.ax) * e; z = o.az + (o.bz - o.az) * e; yaw = Math.atan2(-(o.az - o.bz), o.ax - o.bx); sp = -L * 6 * u * (1 - u) / o.T; dumpT = o.full ? 0 : dDur - 1e-3;
    } else if (o.k === 'scoop') {
      x = o.x; z = o.z; yaw = o.yaw; scoopT = Math.min(lt, acts.truck_scoop ? acts.truck_scoop.getClip().duration - 1e-3 : lt);
      dumpT = o.full ? 0 : dDur - 1e-3; if (lt > o.T * .55) dumpT = 0;     // the scoop's lift drops ore in the bed
      for (let i = 0; i < deposits.length; i++) if (deposits[i].trip === tr.id) deposits[i].dig = clamp(lt / o.T, 0, 1); showRing = true; ringU = lt / o.T;
    } else if (o.k === 'dump') { x = o.x; z = o.z; yaw = 0; dumpT = Math.min(lt, dDur - 1e-3); }
    else if (o.k === 'load') { x = o.x; z = o.z; yaw = 0; loadOn = true; loadT = Math.min(lt, lDur - 1e-3); }
  }
  wheelPh = (wheelPh + sp * dt / TV.wheelC) % 1; if (wheelPh < 0) wheelPh += 1;
  truck.position.set(x, 0, z); truck.rotation.set(0, yaw, 0);
  setTruckClips(loadOn, loadT, !loadOn, dumpT, scoopT, wheelPh);
  if (!truckRing) { truckRing = $('ring').cloneNode(true); truckRing.id = ''; truckRing.arc = truckRing.querySelector('circle:last-child'); document.body.appendChild(truckRing); }
  if (showRing && S.site === MINE) { const p = toScreen(MX + x, 5.5, z, camera, _scr); truckRing.style.left = p.x + 'px'; truckRing.style.top = p.y + 'px'; truckRing.arc.setAttribute('stroke-dashoffset', (113.1 * (1 - ringU)).toFixed(1)); }
  if (showRing !== truckRing._on) { truckRing._on = showRing; truckRing.style.display = showRing ? 'block' : 'none'; }
  truckState.phase = phase; truckState.x = x; truckState.z = z; truckState.yaw = yaw; truckState.v = sp; truckState.bed = dumpT;
}
const truckState = { phase: 'idle', x: 0, z: 0, yaw: 0, v: 0, bed: 0 };

// ===== upgrade juice: spark burst (1 Points draw, ~0.5 s) + squash-and-bounce (~0.35 s)
const SPK = 48, spkPos = new Float32Array(SPK * 3), spkVel = new Float32Array(SPK * 3);
const spkGeo = new THREE.BufferGeometry(); spkGeo.setAttribute('position', new THREE.BufferAttribute(spkPos, 3));
const spkMat = new THREE.PointsMaterial({ color: 0xffe27a, size: 0.32, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending });
const sparks = new THREE.Points(spkGeo, spkMat); sparks.frustumCulled = false; sparks.visible = false; scene.add(sparks);
let spkT = -1, sqT = -1;
const RIGXZ = [-7.5, -3.6], FXK = 2.6;   // rig mast (Rig pivot) in Mine-local metres; sparks scaled for the 37 m frame
function upgradeFx() {
  const k = FXK;
  for (let i = 0; i < SPK; i++) {
    const a = Math.random() * Math.PI * 2, e = Math.random() * 1.2, s = 6 + Math.random() * 7, h = (1 + Math.random() * 8) * k;
    spkPos.set([MX + RIGXZ[0] + Math.cos(a) * 1.2 * k, h, RIGXZ[1] + Math.sin(a) * 1.2 * k], i * 3);
    spkVel.set([Math.cos(a) * Math.cos(e) * s, Math.sin(e) * s + 2, Math.sin(a) * Math.cos(e) * s], i * 3);
  }
  spkGeo.attributes.position.needsUpdate = true; spkT = 0; sqT = 0; sparks.visible = true;
  window.__ps3d.fx = (window.__ps3d.fx || 0) + 1;
}
function updFx(dt) {
  if (spkT >= 0) {
    spkT += dt; const u = spkT / 0.5;
    if (u >= 1) { spkT = -1; sparks.visible = false; }
    else { for (let i = 0; i < SPK; i++) { spkVel[i * 3 + 1] -= 18 * FXK * dt; for (let j = 0; j < 3; j++) spkPos[i * 3 + j] += spkVel[i * 3 + j] * FXK * dt; }
      spkGeo.attributes.position.needsUpdate = true; spkMat.opacity = 1 - u * u; spkMat.size = 0.34 * FXK * (1 - .5 * u); }
  }
  let sy = 1;
  if (sqT >= 0) { sqT += dt; const u = sqT / 0.35; if (u >= 1) sqT = -1; else sy = 1 - 0.16 * Math.sin(u * Math.PI * 2) * (1 - u); }   // squash, stretch, settle
  if (rig) { const sxz = 1 / Math.sqrt(sy); rig.scale.set(sxz, sy, sxz); }      // squash-and-bounce on the bore head
  window.__ps3d.sy = sy;
}

// ===== taps on the 3D scene (deposits): screen-space hit test, radius ≥ 44 CSS px whatever the camera distance
function tap(x, y) {
  if (S.site !== MINE || Math.abs(camX - MX) > 3 || !mine) return;
  let best = null, bd = Infinity;
  for (const d of deposits) {
    if (d.claimed) continue;
    const h = depTapR(d), dist = Math.hypot(x - h.x, y - h.y);
    if (dist < h.R && dist < bd) { bd = dist; best = d; }
  }
  if (!best) return;
  if (sendTruck(best)) { if (eveCur && eveCur.point === 'deposit') pointerDone = true; }
  else pop('Truck busy', x, y - 20, 'info');
}

// ===== upgrade sheet (drag up/down, springs to open or closed)
const sheet = $('sheet'), grab = $('grab'), PEEK = 46;
let sheetOpen = false, sheetDrag = null;
const closedY = () => sheet.offsetHeight - PEEK - (parseFloat(getComputedStyle(sheet).paddingBottom) || 0);   // panel runs flush to the bottom edge; peek sits above the safe-area inset
function setSheet(open) { sheetOpen = open; document.body.classList.toggle('sheet-open', open); sheet.classList.remove('dragging'); sheet.style.transform = `translateY(${open ? 0 : closedY()}px)`; if (open && eveCur && eveCur.point === 'upgrade') pointerDone = true; }
setSheet(false);
addEventListener('resize', () => { if (!sheetDrag) sheet.style.transform = `translateY(${sheetOpen ? 0 : closedY()}px)`; });   // inset can change (rotation)
grab.addEventListener('pointerdown', (e) => { e.stopPropagation(); sheetDrag = { y0: e.clientY, b: sheetOpen ? 0 : closedY(), s: [[performance.now(), e.clientY]], moved: 0 }; sheet.classList.add('dragging'); document.body.classList.add('sheet-drag'); try { grab.setPointerCapture(e.pointerId); } catch (_) {} });
grab.addEventListener('pointermove', (e) => {
  if (!sheetDrag) return; const dy = e.clientY - sheetDrag.y0; sheetDrag.moved = Math.max(sheetDrag.moved, Math.abs(dy));
  let y = sheetDrag.b + dy; const c = closedY(); if (y < 0) y = y * .3; if (y > c) y = c + (y - c) * .3;
  sheet.style.transform = `translateY(${y}px)`; sheetDrag.y = y; sheetDrag.s.push([performance.now(), e.clientY]); if (sheetDrag.s.length > 8) sheetDrag.s.shift();
});
const endSheet = (e) => {
  if (!sheetDrag) return; const d = sheetDrag; sheetDrag = null;
  if (d.moved < 8) { document.body.classList.remove('sheet-drag'); return setSheet(!sheetOpen); }           // a tap on the handle toggles; drags still spring
  const a = d.s[0], b = d.s[d.s.length - 1], v = (b[1] - a[1]) / Math.max(16, b[0] - a[0]);
  document.body.classList.remove('sheet-drag');
  const c = closedY(), y = d.y ?? d.b, FLICK = 0.5;            // px/ms: a fast flick wins; otherwise it needs 30% of the travel or it springs back
  if (v > FLICK) setSheet(false); else if (v < -FLICK) setSheet(true);
  else if (d.b > 0) setSheet(y < c * 0.7);                     // from closed: open only past 30% of the way up
  else setSheet(y < c * 0.3);                                  // from open: close only past 30% of the way down
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
  else { $('rGain').textContent = `${fmt(CFG.roverBonus)} per deposit · more trucks soon`; bRover.textContent = ''; bRover.className = 'off'; }   // truck 2+ isn't for sale yet (real extra trucks come later): no Buy button
  bRover.parentNode.hidden = S.rovers < CFG.roverMax; bRover.parentNode.classList.toggle('ok', false);
  $('sum').textContent = `Drill Lv ${S.drill} · ${S.rovers} truck${S.rovers > 1 ? 's' : ''}`;
  $('canDot').hidden = !canPay(c);
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
  pay(c); S.drill++; applyRigLevel(); applyTiers(S.drill); upgradeFx(); save(); sheetUI(); hud();
  if (fullT > 0 && S.bin < binCap()) { fullT = 0; setDigging(true); }
  const r = bDrill.getBoundingClientRect(); pop('Drill Lv ' + S.drill, r.left + r.width / 2, r.top - 8, 'info');
  window.__ps3d.buys = (window.__ps3d.buys || 0) + 1;
});
const TRUCK_SALE = false;   // extra trucks come later: the button is hidden and a stray click can't buy
bindBuy(bRover, () => {
  if (!TRUCK_SALE || S.rovers >= CFG.roverMax || !canPay(CFG.roverCost)) return;
  pay(CFG.roverCost); S.rovers++; save(); sheetUI(); hud();     // one truck on the loop (see sendTruck): the 2nd lets a 2nd deposit queue
});

// conveyor strip on the bar creeps (CSS background-position) only while the drill runs and the sheet is closed
let convOn = null;
function updConveyor() { const on = fullT === 0 && !sheetOpen && !(sheetDrag); if (on !== convOn) { convOn = on; sheet.classList.toggle('run', on); window.__ps3d.conveyor = on; } }

// ===== Eve placeholder radio calls
const EVE_BEATS = [
  { id: 'mine_first_view', point: 'deposit', text: "Moonbase, this is Eve at Earth Coms. Good to hear you made it. First job: get that mine running. Tap where I'm pointing." },
  { id: 'first_deposit', point: null, text: "Nice haul, Commander. Your truck's hauls pay a bonus on top of the drill, so keep an eye out for that glow. Over." },
  { id: 'upgrade_ready', point: 'upgrade', text: "You've got the cash for an upgrade. Bigger mine, bigger loads. Tap Upgrade." },
];
const EVE_TRIG = {
  mine_first_view: () => S.site === MINE && coverGone && Math.abs(camX - MX) < 1,
  first_deposit: () => S.dep >= 1,
  upgrade_ready: () => S.dep >= 1 && canPay(drillCost()) && !sheetOpen,
};
const eveEl = $('eve'), eveTx = $('eveTx'), pointEl = $('point'), POINT_UP_H = 40;   // 'up' arrow: tip → bottom of the label in px (CSS #point.up: arrow 0–18, label 26–38, +2)
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
  if (b.point === 'deposit' && !deposits.some(d => !d.claimed)) spawnDeposit('Dep_02');   // Art's 'tap deposit'
  window.__ps3d.eveShown = (window.__ps3d.eveShown || []).concat(b.id);
}
function eveClose() { eveEl.classList.remove('on'); eveCur = null; hudEl.classList.remove('away'); lastMoneyTxt = ''; hud(); }   // HUD slides back in (0.25 s CSS)
function eveNext() {                 // a tap while typing completes the line; after that Next turns the page; the last page closes the card
  if (!eveCur) return; const pg = evePage();
  if (eveTyped < pg.length) { eveTyped = pg.length; eveTx.textContent = pg; window.__ps3d.eveTap = 'complete'; return; }
  if (evePg < evePages.length - 1) { evePg++; eveTyped = 0; eveTimer = 0; eveTx.textContent = ''; eveOv.textContent = evePg < evePages.length - 1 ? 'Next' : 'Over'; window.__ps3d.eveTap = 'next'; }
  else { window.__ps3d.eveTap = 'close'; eveClose(); }
}
bindBuy(eveOv, eveNext);              // pointerup (one tap = one step even when frames lag; the trailing click is swallowed)
bindBuy($('eveX'), eveClose);
eveEl.addEventListener('pointerdown', (e) => { e.stopPropagation(); if (eveCur && !e.target.closest('button')) { const pg = evePage(); eveTyped = pg.length; eveTx.textContent = pg; } });
function updEve(dt) {
  if (eveCur) { const pg = evePage(); if (eveTyped < pg.length) { eveTimer += dt; while (eveTimer > .028 && eveTyped < pg.length) { eveTimer -= .028; eveTyped++; } } if (eveTx.textContent.length !== Math.min(eveTyped, pg.length)) eveTx.textContent = pg.slice(0, eveTyped); }
  if (!eveCur) for (const b of EVE_BEATS) if (!S.eve.includes(b.id) && EVE_TRIG[b.id]()) { eveShow(b); break; }
  // pointer arrow
  let p = null;
  if (pointBeat && !pointerDone) {
    if (pointBeat === 'deposit' && S.site === MINE) { const d = deposits.find(d => !d.claimed); if (d) {   // from below: the tip sits just under the glow disc, the label under the arrow, ≥ 12 px clear of the station label
      const h = depTapR(d); p = _pt; p.x = h.x; p.l = 'TAP HERE'; p.up = true;
      const lim = nameEl.getBoundingClientRect().top - POINT_UP_H - 12; p.y = Math.min(h.y + h.glow + 6, lim); } }
    if (pointBeat === 'upgrade') { const r = grab.getBoundingClientRect(); p = _pt; p.x = r.left + r.width / 2; p.y = r.top + 4; p.l = 'UPGRADE'; p.up = false; }
  }
  pointEl.style.display = p ? 'block' : 'none';
  if (p) { pointEl.style.left = p.x + 'px'; pointEl.style.top = p.y + 'px'; if (pointEl.firstChild.textContent !== p.l) pointEl.firstChild.textContent = p.l; if (pointEl._up !== p.up) { pointEl._up = p.up; pointEl.classList.toggle('up', p.up); } }
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

// trips are restored once the Mine GLB (track + markers) is in: see loadRig()

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
  updFocus(); placeCamera();
  updTruck(dt);                       // poses the truck + scrubs its clips, then the mixer applies them this frame
  if (mixer) mixer.update(dt);
  for (const m of stationMixers) m.update(dt);
  updDeposits(dt, time); updQueued(); updChunks(dt); updFx(dt); updTiers(dt);
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
window.__ps3d = { renderer, scene, camera, rigScaleAt: rigScale, fxStep: updFx, tierStep: updTiers, get tierList() { return tiers; }, EVE_BEATS, get eveId() { return eveCur && eveCur.id; }, sparks, S, CFG, goSite, STATIONS, deposits, spawnDeposit, catchUp, save, toScreen, drillCost, rate, binCap, fmt, depTapR, sendTruck, planOf, truckState, SITECAM, TV, tap, focusTier, FOCT, THREE, popXY, get focus() { return { i: FOC.i, w: +FOC.w.toFixed(3), ph: FOC.ph, q: FOC.q.length, to: FOC.to && FOC.to.name, t: FOC.i < 0 ? 0 : +((performance.now() - FOC.seg0) / 1000).toFixed(2) }; },
  get camX() { return camX; }, get fullT() { return fullT; }, get coverGone() { return coverGone; }, get eveOpen() { return !!eveCur; }, get evePages() { return evePages; }, get cashTarget() { return cashTarget().id; }, get evePg() { return evePg; }, get sheetOpen() { return sheetOpen; }, setSheet };
if (hadRt) catchUp(true); else S.rt = Date.now();      // credit time away since the last save
hud(); sheetUI();
frame();
