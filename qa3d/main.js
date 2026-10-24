// Planet Stack QA3D: Mine A truck loop on Art's Mine GLB (582676b) + HT-04 truck prop (c0452bd) + Mine operator (9209246).
// The drill fills the truck under the chute; full trucks haul to Art's Refinery (4a70acf) and pay as the bed tips.
// Fixed camera, one-station swipes, upgrade sheet, offline catch-up, Earth Coms (Eve) kit, ?dev=1 readout, ?speed=N (QA clock).
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';

window.__ps3d = window.__ps3d || {};   // QA hooks (filled in as modules load; see the end of the file)
// ===== balance: all tuning lives here (Director may retune) =====
const CFG = {
  startMoney: 500, startCrystals: 0, showCrystals: false,   // Jacob 10/23: crystals are a paid currency (shop later); counter hidden, nothing grants them
  oreValue: 1,                          // $ per ore
  drillRate0: 6, drillRatePerLvl: 3,    // ore/min at Lv1, + per level
  drillCost0: 15, drillCostGrowth: 1.65,// Lv1→2 costs $15, then ×1.65 per level
  drillScalePerLvl: 0.08, drillScaleStop: 6,
  // HT-04 truck loop (Director 10/23): park under the chute, fill, auto-depart when full, 12 s haul leg, tip at the Refinery, 12 s back
  fill0: 120, chuteMul: 0.89, fillFloor: 15, chuteMax: 19,   // fill s at Lv1; Chute Feed Rate ×0.89/level; 15 s floor (reached at Lv19)
  chuteCost0: 25, chuteCostGrowth: 1.6,                      // PLACEHOLDER price: not in the Director's numbers
  load0: 12, loadPerLvl: 6,             // base load value: fixed $ per load ($12 at drill Lv1, +$6 per drill level); independent of the fill time, so Chute Feed Rate = more loads/h at the same value
  richFill: 0.25, richBonus: 8, richPayDelay: 1.0,            // deposit tap: +25% bed (tweened over the 1 s truck_load_rich), bonus pays ~1 s later
  roverBonus: 8, roverMax: 2, roverCost: 60,
  crew0: 4,                             // starting crew; the Mine operator (Operator_Deck) is one of them
  depositMax: 2, depositEvery: 8,
  offlineRate: 0.5, offlineCapSec: 4 * 3600, awayCardMin: 5, offlineAfterSec: 300,   // Director 10/23: the 50% cut + away card only after 5 min away; shorter locks catch up at full rate
  saveEvery: 3,
  // He-3 cargo loop (Director 10/23 spec). ALL numbers below are PLACEHOLDERS pending Director sign-off (see the cargo note in the commit report)
  cargo: { sealSec: 4, perTrip: 2, refLoadSec: 6, padUnloadSec: 6, checkSec: 2, walkSec: 3, holdLoadSec: 5, bayCap: 12, holdCap: 10,
           fuelFillSec: 300, launchSec: 8, awaySec: 600, landSec: 8, boxValue: 25 },
};
const CAM = { halfW: 7.5, elev: 18, lookY: 2.5 };   // fixed camera: ~15 m wide in portrait, 18° down

const Q = new URLSearchParams(location.search);
// ---- Swappable art (pending Director review). The filename carries the commit hash, so it is also the cache-buster.
const MINE_GLB = 'models/mine_219e774.glb';             // Art 219e774 levelled road end; previous: 'models/mine_8a0bfe6.glb'
const REFINERY_GLB = 'models/refinery_bb5eed2.glb';     // Art bb5eed2 road starts at world x 274; previous: 'models/refinery_0358ffa.glb'
const TURN_SPEED = 4.0;   // m/s through curves (Mine 4.5 m arcs on Path_Out_*/Path_Ret_*, Refinery U-turn Truck_Path_01..07); straights stay TV.v = 8.33
const TURN_R_MAX = 25;    // m: any stretch turning tighter than this radius counts as a curve
const TURN_ACC = 2.5;     // m/s²: braking into / speeding out of a curve
const ROAD_LAST_SCALE = 1.0;   // haul road: 10 full 8 m tiles + a last tile scaled along X only. 1.0 = 11 full tiles ending at world x 274 (Art's trimmed Refinery road);
                               // 0.75 = ends at x 272, where Refinery 0358ffa's own road starts
const DEV = Q.get('dev') === '1';
const SAVEKEY = DEV ? 'planetstack-qa3d-dev' : 'planetstack-qa3d';
if (Q.has('fresh')) try { localStorage.removeItem(SAVEKEY); } catch (e) {}
const SPD = Math.max(1, Math.min(100, +Q.get('speed') || 1)), T0 = Date.now();   // ?speed=N (QA only): the game clock (truck loop, fill, deposits, 3D anims) runs N×
let WARP = 0;   // QA only (__ps3d.warpTo): jumps the game clock forward as live play (no offline rate)
let HOLD = null; // QA only (__ps3d.hold): freezes the game clock so slow test boxes can screenshot an exact pose
const rawMs = () => (SPD === 1 ? Date.now() : T0 + (Date.now() - T0) * SPD) + WARP;
const nowMs = () => (HOLD !== null ? HOLD : rawMs());
const S = { site: 1, money: CFG.startMoney, crystals: CFG.startCrystals, drill: 1, chute: 1, rovers: 1, dep: 0, loads: 0, eve: [], calls: [], log: [], missed: 0, tk: null, pend: [], trips: [], rt: nowMs() };
let hadRt = false;
try { const sv = JSON.parse(localStorage.getItem(SAVEKEY) || '{}'); hadRt = sv.rt > 0;
  if (hadRt && !('chute' in sv) && sv.site >= 2) sv.site++;   // 11:12 and older saves: the Refinery slot (index 2) shifts the later stations by one
  Object.assign(S, sv); } catch (e) {}
for (const k of ['eve', 'calls', 'log', 'pend', 'trips']) if (!Array.isArray(S[k])) S[k] = [];
if (!(S.chute >= 1)) S.chute = 1; if (!(S.loads >= 0)) S.loads = 0; if (!(S.missed >= 0)) S.missed = 0;
if (!(S.rt > 0)) S.rt = nowMs();
// legacy saves: ore left in the old bin and unpaid deposit trips settle exactly once, then the new truck loop starts
if (S.bin > 0) S.money += Math.floor(S.bin) * CFG.oreValue; delete S.bin;
for (const tr of S.trips) if (tr && !tr.paid && tr.bonus > 0) { S.money += tr.bonus; S.dep++; }
S.trips = [];
// truck loop state (all timestamps, ms): c0 fill start, add pre-filled fraction, lr last rich drop, dep departure (0 = parked under the chute),
// paid base load paid for this trip, val base load value frozen at departure, q / qd rich loads queued while the truck is away
if (!S.tk || typeof S.tk !== 'object') S.tk = { c0: nowMs(), add: 0, lr: 0, dep: 0, paid: false, val: 0, q: 0, qd: [] };
if (!Array.isArray(S.tk.qd)) S.tk.qd = [];
const save = () => { try { localStorage.setItem(SAVEKEY, JSON.stringify(S)); } catch (e) {} };

const STATIONS = ['Life Support', 'Mine', 'Refinery', 'Takeoff & Landing', 'Cargo Space Dock', 'Habitat', 'Shipyard', 'Engineering'];
const GAP = 160, N = STATIONS.length, MINE = 1, MX = MINE * GAP, REF = 2, RX = REF * GAP;   // stations 160 m apart, origin = i·160 on X
const $ = (id) => document.getElementById(id);
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const ease = (t) => t < .5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;

// ===== economy helpers
const rate = () => CFG.drillRate0 + CFG.drillRatePerLvl * (S.drill - 1);           // ore/min
const drillCost = () => Math.round(CFG.drillCost0 * CFG.drillCostGrowth ** (S.drill - 1));
const fillSec = (lv = S.chute) => Math.max(CFG.fillFloor, CFG.fill0 * CFG.chuteMul ** (lv - 1));   // Lv7 = 59.6 s, Lv19 = 15 s
const chuteCost = () => Math.round(CFG.chuteCost0 * CFG.chuteCostGrowth ** (S.chute - 1));
const loadValue = (lv = S.drill) => CFG.load0 + CFG.loadPerLvl * (lv - 1);   // Director 10/23: fixed per load, scales with drill level only
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
const SIZES = [[10, 8, 8], null, null, [10, 1, 10], [14, 7, 9], [9, 12, 9], [12, 9, 10], [10, 10, 8]];   // Mine: Art's GLB; Refinery: Art's GLB (STATION_GLB)
const phBox = [];
STATIONS.forEach((name, i) => {
  if (!SIZES[i]) return; const [w, h, d] = SIZES[i];
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), ph);
  m.position.set(i * GAP, h / 2, 0); m.castShadow = m.receiveShadow = true; scene.add(m); phBox[i] = m;
});
// ===== passed station GLBs (Art): swap in for the gray box once loaded; tiers hidden; idle loops play; doors stay shut
const DOCK = { pipeLaunchPad: [37.70, 0.66, 7.30] };   // Dock-local glTF; read from the GLB on load (the Launch Pad pipe joins here)
const STATION_GLB = [
  { i: 0, url: 'models/life_support_adfaac9.glb?v=e8427ec4', loops: ['Beacon_Lights_Blink', 'Fan_Scrubber_Spin'] },   // Cam_Target (0, 2.5, -12.5), frame_w 34
  { i: 2, url: REFINERY_GLB,   // see REFINERY_GLB at the top
    loops: ['Beacon_Lights_Blink', 'conveyor_fuel_run', 'conveyor_he3_run', 'kiln_spin'], onLoad: (o, mx, g) => refineryLoaded(o, mx, g) },
  { i: 4, url: 'models/dock_tankfarm_fd286b9.glb?v=7959ae74', loops: ['Beacon_Lights_Blink', 'crane_gantry_move'], onLoad: (o) => {   // Cam_Target (12, 6, 2), frame_w 64; dock door stays shut
    const pl = o.getObjectByName('Pipe_LaunchPad'); if (pl) DOCK.pipeLaunchPad = pl.position.toArray(); window.__ps3d.dock = DOCK; } },
  { i: 6, url: 'models/shipyard_2d57b95.glb?v=4020a073', loops: ['Beacon_Lights_Blink', 'crane_jib_swing'], pingPong: ['crane_jib_swing'] },   // jib clip is one-way 90°→0°: ping-pong so it swings back instead of snapping
];
const SITECAM = STATIONS.map(() => ({ k: 1, dx: 0, dz: 0, ly: CAM.lookY }));   // per-station framing; the Mine keeps k=1, dx=dz=0 until its GLB (with Cam_Target) is in
const stationMixers = [], stationObjs = {};
const _ct = new THREE.Vector3();
function camTargetOf(o) { let t = null; o.traverse(n => { if (!t && n.name === 'Cam_Target' && n.userData && n.userData.frame_w > 0) t = n; }); return t; }
// ===== Refinery (index 2): Art's Refinery GLB 0358ffa (md5 41ac6c5a…), origin = Truck_Dump, Cam_Target (-5.9, 8.5, 3.36) frame_w 30.8.
// The shared HT-04 drives its Truck_Path_01..07 → reverse 4 m → Truck_Dump → Truck_Exit markers (Refinery-local). Values below are the
// README fallback so the truck timeline exists before the GLB is in; the GLB's own markers replace them on load.
const RMK = {};               // Refinery markers, Refinery-local { x, z }
(function refineryMarkerFallback() {
  RMK.Truck_Path_01 = { x: -46, z: 9 }; RMK.Truck_Path_02 = { x: -14, z: 9 };
  for (let k = 0; k <= 4; k++) { const p = -Math.PI / 2 + Math.PI * k / 4; RMK['Truck_Path_0' + (3 + k)] = { x: -4 + 4.5 * Math.cos(p), z: 4.5 - 4.5 * Math.sin(p) }; }   // U-turn r 4.5 about (−4, 4.5)
  RMK.Truck_Dump = { x: 0, z: 0 }; RMK.Truck_Exit = { x: -46, z: 0 };
})();
const refActs = {};
function refineryLoaded(o, mx, gltf) {
  o.traverse(n => { if (n !== o && /^(Truck|HT04|HT-04)($|_Mesh|_Root)/i.test(n.name)) n.visible = false; });   // hide any baked truck (none in 4a70acf)
  let moved = false;
  o.traverse(n => { if (RMK[n.name]) { const p = RMK[n.name]; if (Math.hypot(p.x - n.position.x, p.z - n.position.z) > .01) moved = true; RMK[n.name] = { x: n.position.x, z: n.position.z }; } });
  for (const c of gltf.animations) if (c.name === 'intake_shake') { const a = refActs.intake_shake = mx.clipAction(c); a.setLoop(THREE.LoopOnce, 1); }
  if (moved) { console.warn('Refinery truck markers differ from the README fallback: route rebuilt'); buildRoute(); }
  window.__ps3d.refinery = o;
}
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
  const c = [], mc = camera.clone(), bd = band(), top = bd.top, bot = bd.bot; mc.clearViewOffset();
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
  for (const c of gltf.animations) if (G.loops.includes(c.name)) { const a = mx.clipAction(c); if ((G.pingPong || []).includes(c.name)) a.setLoop(THREE.LoopPingPong, Infinity); a.play(); }
  if (G.onLoad) G.onLoad(o, mx, gltf);
  fitSite(G.i);
  (window.__ps3d.stationsLoaded = window.__ps3d.stationsLoaded || []).push(STATIONS[G.i]);
}, undefined, (e) => console.warn('station GLB failed, keeping gray box', G.url, e));

// ===== Mine station GLB (Art 582676b, md5 68e07c01…): rig + conveyor + chute, haul-loop markers, deposits, tiers, Cam_Target. No truck inside.
let mixer = null, mine = null, rig = null, rigLoaded = false, coverGone = false;
const acts = {}, MK = {};                  // MK: markers by name, Mine-local { x, y, z, e: extras }
// README fallback (582676b) so the truck timeline exists before the GLB is in (offline catch-up on load); the GLB's own markers replace it
const MK0 = { Path_Load: [4.7, 4.5], Path_Load_Approach: [9, 4.5], Path_01: [5, 4.5], Path_02: [8, 4.5], Path_03: [11.18, 5.06], Path_04: [13.25, 7.51], Road_Entry: [13.5, 9],
  Path_05: [13.16, 10.72], Path_06: [10.95, 13.05], Path_07: [7.75, 13.5], Path_08: [4.75, 13.5], Path_09: [1.75, 13.5], Path_10: [-1.25, 13.5], Path_11: [-4.25, 13.5],
  Path_12: [-7.35, 12.74], Path_13: [-8.97, 10], Path_14: [-8.08, 6.95], Path_15: [-5.25, 5.51], Rich_Pop: [3.1, 4.5, 4.88], Operator_Deck: [14, 1.2], Dep_01: [8.65, 8.65], Dep_02: [-1.2, 10.4] };
for (const n in MK0) MK[n] = { x: MK0[n][0], y: MK0[n][2] || 0, z: MK0[n][1], e: {}, fb: true };
const glowMats = [];
let digOn = null;
function setDigging(on) { if (on === digOn) return; digOn = on; for (const n of ['dig', 'conveyor_run']) { const a = acts[n]; if (a) a.paused = !on; } }   // rig + belt run only while the truck fills under the chute
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
// the cover never fades onto empty ground: it stays until the Mine (and the truck, or its failure) is in the scene
let coverTimer = 0;
function armCoverTimer() { clearTimeout(coverTimer); coverTimer = setTimeout(() => { coverTimer = 0; if (!rigLoaded) { console.warn('Mine GLB still loading after 15 s'); $('coverTx').textContent = 'Still loading…'; } }, 15000); }
armCoverTimer();
function hideCover() {
  const c = $('cover'); if (!c || c.classList.contains('off')) return; clearTimeout(coverTimer); c.classList.add('off');
  setTimeout(() => { c.remove(); coverGone = true; }, 420);
}
function maybeReady() {
  if (!rigLoaded || !truckDone) return;
  renderer.compile(scene, camera);
  requestAnimationFrame(() => requestAnimationFrame(hideCover));   // fade only once the Mine has been drawn
}
const loader = loader0();
function loadRig() { loader.load(MINE_GLB, (gltf) => {
  clearTimeout(coverTimer); coverTimer = 0;            // loaded: the 15 s 'still loading' warning can never fire late
  mine = gltf.scene; mine.position.set(MX, 0, 0);
  const moved = [];
  mine.traverse(o => {
    if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; if (o.isSkinnedMesh) o.frustumCulled = false;
      const m = o.material; if (m && m.emissive && m.emissive.getHex() && !glowMats.includes(m)) { m.userData.ei0 = m.emissiveIntensity; glowMats.push(m); } }
    if ((o.userData && o.userData.kind) || /^Path_(Out|Ret)_/.test(o.name)) { const old = MK[o.name], p = { x: o.position.x, y: o.position.y, z: o.position.z, e: o.userData };
      if (old && /^Path_|^Road_/.test(o.name) && Math.hypot(old.x - p.x, old.z - p.z) > .01) moved.push(o.name); MK[o.name] = p; }
  });
  scene.add(mine); mine.updateMatrixWorld(true);
  rig = mine.getObjectByName('Rig');
  stationObjs[MINE] = mine; mine.userData.camTarget = camTargetOf(mine);
  buildTiers(); applyTiers(0);
  mixer = new THREE.AnimationMixer(mine);
  for (const c of gltf.animations) acts[c.name] = mixer.clipAction(c);
  for (const n of ['dig', 'conveyor_run']) if (acts[n]) acts[n].play();
  digOn = null;
  if (Object.keys(MK).some(n => /^Path_(Out|Ret)_/.test(n))) moved.push('Path_Out_*/Path_Ret_*');   // Art's out/return route markers: marker-driven route
  if (moved.length) { console.warn('Mine haul markers differ from the README fallback: route rebuilt', moved); buildRoute(); }
  applyRigLevel(); fitSite(MINE); restoreDeposits();
  if (op) { const d = MK.Operator_Deck; op.position.set(MX + d.x, 0, d.z); }
  rigLoaded = true; maybeReady();
  Object.assign(window.__ps3d, { mine, rig, MK, clips: gltf.animations.map(a => a.name + ':' + a.duration.toFixed(2)) });
}, undefined, (e) => {
  console.error('Mine GLB load failed', e); clearTimeout(coverTimer); coverTimer = 0;
  $('coverTx').textContent = "Couldn't load the Mine"; $('coverSp').hidden = true; $('coverRetry').hidden = false;
}); }
$('coverRetry').addEventListener('click', () => {
  $('coverRetry').hidden = true; $('coverSp').hidden = false; $('coverTx').textContent = 'Loading Moonbase…'; armCoverTimer(); loadRig();
});

// ===== HT-04 haul truck prop (Art c0452bd, md5 16eccb4d…): root 'Truck' at the ground centre, +X forward at yaw 0; world-space object
let truck = null, truckRoot = null, truckDone = false, tMixer = null, fillArcNode = null;
const tActs = {}, wheels = [], fillMeshes = [];
function loadTruck() { loader.load('models/ht04_c0452bd.glb?v=16eccb4d', (gltf) => {
  truckRoot = gltf.scene; truck = truckRoot.getObjectByName('Truck') || truckRoot;
  truckRoot.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false;
    if (o.morphTargetDictionary && 'fill' in o.morphTargetDictionary) fillMeshes.push([o, o.morphTargetDictionary.fill]); } });
  for (const n of ['FL', 'FR', 'ML', 'MR', 'RL', 'RR']) { const b = truckRoot.getObjectByName('HT04_Wheel_' + n); if (b) wheels.push({ b, q0: b.quaternion.clone() }); }   // rest (0, .7071, 0, .7071)
  fillArcNode = truckRoot.getObjectByName('Fill_Arc');
  TV.wheelR = (truck.userData && truck.userData.wheel_radius) || 0.853;
  scene.add(truckRoot);
  tMixer = new THREE.AnimationMixer(truckRoot);
  for (const c of gltf.animations) tActs[c.name] = tMixer.clipAction(c);
  if (tActs.truck_load_rich) { tActs.truck_load_rich.setLoop(THREE.LoopOnce, 1); tActs.truck_load_rich.clampWhenFinished = false; }
  if (tActs.truck_dump) { tActs.truck_dump.setLoop(THREE.LoopOnce, 1); tActs.truck_dump.clampWhenFinished = true; }
  truckDone = true; maybeReady();
  Object.assign(window.__ps3d, { truck, truckRoot, wheels, truckClips: gltf.animations.map(a => a.name + ':' + a.duration.toFixed(2)) });
}, undefined, (e) => { console.error('HT-04 truck GLB load failed', e); truckDone = true; maybeReady(); }); }

// ===== Mine operator prop (Art 9209246, md5 2cfa57a6…): at Operator_Deck, facing +Z, sibling of the Mine at scale 1.
// Chain (no snaps): op_sit_type ×2–4 → op_stand_walk_to_rail (once, clamp) → op_watch_rail (while the truck is on the road, 1–3 loops) → op_walk_back_sit → …
// Head look-at on Op_Head after mixer.update, only in op_watch_rail (0.3 s fade). Purely visual: never part of any tap test.
let op = null, opMx = null, opHead = null;
const opActs = {}, OP = { cur: '', n: 0, need: 2, w: 0, look: new THREE.Quaternion(), seen: [] };
function opGo(name, fade = 0.2) {
  const a = opActs[name]; if (!a) return; const prev = opActs[OP.cur];
  a.reset(); a.setEffectiveTimeScale(1); a.setEffectiveWeight(1); a.play();
  if (prev && prev !== a) prev.crossFadeTo(a, fade, false);
  OP.cur = name; OP.n = 0;
  OP.need = name === 'op_sit_type' ? 2 + Math.floor(Math.random() * 3) : name === 'op_watch_rail' ? 1 + Math.floor(Math.random() * 3) : 1;
  OP.seen.push(name); if (OP.seen.length > 16) OP.seen.shift();
}
function loadOperator() { loader.load('models/mine_operator_9209246.glb?v=2cfa57a6', (gltf) => {
  op = gltf.scene; const d = MK.Operator_Deck; op.position.set(MX + d.x, 0, d.z);
  op.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; } });
  opHead = op.getObjectByName((op.getObjectByName('MineOperator') || {}).userData?.head_bone || 'Op_Head') || op.getObjectByName('Op_Head');
  scene.add(op);
  opMx = new THREE.AnimationMixer(op);
  for (const c of gltf.animations) opActs[c.name] = opMx.clipAction(c);
  for (const n of ['op_stand_walk_to_rail', 'op_walk_back_sit']) { const a = opActs[n]; if (a) { a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; } }
  opMx.addEventListener('loop', (e) => { if (e.action === opActs[OP.cur]) OP.n++; });
  opMx.addEventListener('finished', (e) => { if (e.action !== opActs[OP.cur]) return; opGo(OP.cur === 'op_stand_walk_to_rail' ? 'op_watch_rail' : 'op_sit_type'); });
  opGo('op_sit_type', 0);
  Object.assign(window.__ps3d, { op, opHead });
}, undefined, (e) => console.warn('Mine operator GLB failed (crew member stays off-screen)', e)); }
const _hp = new THREE.Vector3(), _hq = new THREE.Quaternion(), _he = new THREE.Euler();
function updOperator(dt) {
  if (!opMx) return;
  if (OP.cur === 'op_sit_type' && OP.n >= OP.need) opGo('op_stand_walk_to_rail');
  else if (OP.cur === 'op_watch_rail' && OP.n >= OP.need && !truckOnRoad()) opGo('op_walk_back_sit');
  opMx.update(dt);
  const want = OP.cur === 'op_watch_rail' ? 1 : 0; OP.w = clamp(OP.w + clamp(want - OP.w, -dt / .3, dt / .3), 0, 1);
  if (!opHead || !truck) return;
  if (OP.w <= 0) { OP.look.copy(opHead.quaternion); return; }
  _hp.set(TS.x, 2.2, TS.z); opHead.parent.worldToLocal(_hp).sub(opHead.position);
  const yaw = clamp(Math.atan2(_hp.x, _hp.z), -1.2, 1.2), pitch = clamp(-Math.atan2(_hp.y, Math.hypot(_hp.x, _hp.z)), -.35, .25);
  _hq.setFromEuler(_he.set(pitch, yaw, 0, 'YXZ'));
  OP.look.slerp(_hq, 1 - Math.pow(0.9, dt * 60));              // ~0.1 per frame at 60 fps
  opHead.quaternion.slerp(OP.look, OP.w);
  OP.yaw = yaw; OP.pitch = pitch;
}
const CREW = [{ role: 'Mine operator', station: MINE, prop: 'mine_operator' }, { role: 'unassigned' }, { role: 'unassigned' }, { role: 'unassigned' }].slice(0, CFG.crew0);

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
  const C = SITECAM[i], hm = focusHome(i), mc = camera.clone(); mc.clearViewOffset();
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
  if (ecIsOpen()) { ecHangUp(); return; }                       // a tap on the scene first closes the Earth Coms panel
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
if (CFG.showCrystals) $('cry').closest('.cell').hidden = false;
const moneyEl = $('money'), rateEl = $('rate'), cryEl = $('cry'), binEl = $('bin'), binFill = binEl.firstElementChild;
let lastMoneyTxt = '', lastMoneyV = 0, lastBin = -1;
moneyEl.addEventListener('animationend', (e) => { if (e.animationName === 'tick') moneyEl.classList.remove('tick'); });
function hud() {
  const mt = DEV ? '∞' : fmt(S.money); if (mt !== lastMoneyTxt) { moneyEl.textContent = mt; lastMoneyTxt = mt; moneyEl.classList.toggle('long', mt.length > 10);
    if (S.money > lastMoneyV && !moneyEl.classList.contains('bump')) moneyEl.classList.add('tick'); }   // soft tick on any increase (transform/opacity only, no forced reflow)
  lastMoneyV = S.money;
  rateEl.textContent = rate();
  if (CFG.showCrystals) cryEl.textContent = S.crystals;   // paid currency (real money only); hidden until the shop lands
  const bf = TS.shown; if (Math.abs(bf - lastBin) > .002) { lastBin = bf; binFill.style.transform = `scaleX(${bf.toFixed(3)})`; }   // bar = the truck bed
  binEl.classList.toggle('full', TS.ph !== 'fill' && TS.shown >= 1);
}
// money pops: chunks and '+$X' fly to the HUD money counter (the HUD dims while an Earth Coms toast rings; the counter stays the target)
const hudEl = $('hud');
const cashTarget = () => moneyEl;
function bumpMoney() { const el = cashTarget(); el.classList.remove('bump'); void el.offsetWidth; el.classList.add('bump'); }
function pop(text, x, y, cls = '') {
  const el = document.createElement('div'); el.className = 'pop ' + cls; el.textContent = text;
  el.style.left = x + 'px'; el.style.top = y + 'px'; document.body.appendChild(el); setTimeout(() => el.remove(), 1150);
}
function moneyXY() { const r = cashTarget().getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }
function popXY() { const m = moneyXY(); return { x: m.x, y: m.y + 30 }; }   // under the HUD money
function smallPop(v) {                 // off-screen payouts: a small '+$' next to the HUD money counter
  const r = moneyEl.parentNode.getBoundingClientRect(); pop('+' + fmt(v), Math.min(W - 30, r.right - 18), r.bottom + 10, 'small'); bumpMoney();
  window.__ps3d.lastSmallPop = { v, at: nowMs() };
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
function flyChunks(n, from, value, cls, noPop) {   // noPop: the caller already showed '+$X' in the world
  window.__ps3d.lastFly = { target: cashTarget().id, ...moneyXY() };
  n = Math.min(n, 12); let first = true;
  for (let i = 0; i < n; i++) {
    const kind = i % 3 === 2 ? 1 : 0; const idx = freeIdx[kind].pop(); if (idx === undefined) continue;
    chunks.push({ kind, idx, t: -i * 0.07, dur: 0.75 + Math.random() * .15, p0: from.clone().add(new THREE.Vector3((Math.random() - .5) * .8 * CHK, Math.random() * .4 * CHK, (Math.random() - .5) * .6 * CHK)),
      up: 2.5 + Math.random() * 2, spin: Math.random() * 6, done: first ? () => { if (noPop) return bumpMoney(); const m = popXY(); pop('+' + fmt(value), m.x, m.y, cls); bumpMoney(); } : null });
    first = false;
  }
  if (!n || first) { if (noPop) return bumpMoney(); const m = popXY(); pop('+' + fmt(value), m.x, m.y, cls); bumpMoney(); }
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
  const gem = new THREE.Mesh(gemGeo, gemMat); gem.position.set(x, GEMY, z); gem.castShadow = false; gem.visible = false;   // Jacob 10/23: no floating diamonds on the Mine; the glowing ground disc is the tap target
  scene.add(disc, gem);
  const d = { id: ++depSeq, mk, x, z, r, rs: r, disc, gem, age: claimed ? 1 : 0, claimed, dig: 0 }; deposits.push(d); return d;
}
function removeDeposit(d) { if (!d || !deposits.includes(d)) return; scene.remove(d.disc, d.gem); if (d.qr) d.qr.style.display = 'none'; deposits.splice(deposits.indexOf(d), 1); }
function restoreDeposits() {          // rich loads queued while the truck was away (saved in S.tk.qd) re-show with their ring until the truck is back
  for (const mk of S.tk.qd) if (MK[mk] && !MK[mk].fb && !deposits.some(d => d.mk === mk)) { const d = makeDeposit(mk, true); d.tkq = true; }
}
// 'queued' ring: a deposit tapped while the truck is away; its rich load drops into the next fill the moment the truck is back under the chute
const qRings = [];
function qRingEl(k) { let el = qRings[k]; if (!el) { el = qRings[k] = document.createElement('div'); el.className = 'qring'; el.innerHTML = '<b>QUEUED</b>'; document.body.appendChild(el); } return el; }
function updQueued() {
  let k = 0; const live = S.site === MINE && Math.abs(camX - MX) < 3 && !document.hidden;
  for (const d of deposits) {
    d.queued = !!d.tkq; if (!d.queued || !live) continue;
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
  const tn = nowMs();
  for (const d of [...deposits]) {
    if (d.claimed && d.at) { d.dig = clamp((tn - d.at) / 1000, 0, 1); if (d.dig >= 1) { removeDeposit(d); continue; } }   // drill taps it: shrinks over the 1 s rich drop
    d.age += dt; const pin = d.age < .35 ? 1 - (1 - d.age / .35) ** 3 * (1 - 1.7 * (d.age / .35)) : 1;
    const shrink = d.claimed ? 1 - .85 * d.dig : 1, ph = .5 + .5 * Math.sin(time * 4 + d.id), pulse = 1 + .25 * ph;   // 1.0 → 1.25
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
// ===== HT-04 haul loop (no scoop). The truck's state is purely its position along the whole loop, computed from saved timestamps (S.tk),
// so it is right on any station, after a reload and after time away; every load pays exactly once.
//   fill under the chute (Path_Load) → auto-depart when full → Path_Out_01..04 (exact next_leg arcs) → temp haul road (z 9)
//   → Refinery Truck_Path_01..07 (U-turn) → reverse 4 m → Truck_Dump → truck_dump 3 s (base load pays as the tip starts)
//   → Truck_Exit → temp road (z 0) → Path_Ret_01..08 (exact arcs) → Path_Load_Approach → reverse 4.3 m under the chute
//   The lanes cross at Path_Ret_04 (Mine x 19.5, z 9). One truck today; with more trucks the loaded (outbound) truck must get priority there.
const ROAD = { tile: 8, x0: MX + 26, n: 11, zIn: 9, zOut: 0, last: ROAD_LAST_SCALE };   // tiles at world x = 160 + 26 + 8i (i 0..10); tile 10 scaled ROAD_LAST_SCALE along X
const roadTileM = (i, z = 0) => new THREE.Matrix4().makeTranslation(ROAD.x0 + ROAD.tile * i, 0, z).multiply(new THREE.Matrix4().makeScale(i === ROAD.n - 1 ? ROAD.last : 1, 1, 1));
const TV = { v: 8.33, ease: 3, brake: 4, revRef: 1.5, dump: 3.0, settle: 0.4, revMine: 2.0, wheelR: 0.853 };
const R = { pOut: null, pBack: null, kOut: null, kBack: null, legOut: 0, legBack: 0, tl: null, mode: '' };
const mw = (n) => [MX + MK[n].x, MK[n].z], rw = (n) => [RX + RMK[n].x, RMK[n].z];
function line(a, b, step = 4) { const n = Math.max(1, Math.round(Math.hypot(b[0] - a[0], b[1] - a[1]) / step)), o = []; for (let i = 1; i <= n; i++) o.push([a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n]); return o; }
function dedupe(pts) { const o = []; for (const p of pts) { const q = o[o.length - 1]; if (!q || Math.hypot(p[0] - q[0], p[1] - q[1]) > .3) o.push(p); } return o; }
function samplePath(pts) {          // centripetal Catmull-Rom through the markers, resampled every ~0.2 m by arc length
  pts = dedupe(pts);
  const c = new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(p[0], 0, p[1])), false, 'centripetal'); c.arcLengthDivisions = 6000;
  const n = Math.ceil(c.getLength() / .2) + 1, sp = c.getSpacedPoints(n - 1), X = new Float64Array(n), Z = new Float64Array(n), C = new Float64Array(n);
  for (let i = 0; i < n; i++) { X[i] = sp[i].x; Z[i] = sp[i].z; if (i) C[i] = C[i - 1] + Math.hypot(X[i] - X[i - 1], Z[i] - Z[i - 1]); }
  return { n, X, Z, C, L: C[n - 1] };
}
function sOf(P, p) { let b = 0, bd = Infinity; for (let i = 0; i < P.n; i++) { const d = (P.X[i] - p[0]) ** 2 + (P.Z[i] - p[1]) ** 2; if (d < bd) { bd = d; b = i; } } return P.C[b]; }
function pathAt(P, s, o) { s = clamp(s, 0, P.L); let lo = 0, hi = P.n - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (P.C[m] <= s) lo = m; else hi = m; }
  const u = (s - P.C[lo]) / Math.max(1e-9, P.C[hi] - P.C[lo]); o.x = P.X[lo] + (P.X[hi] - P.X[lo]) * u; o.z = P.Z[lo] + (P.Z[hi] - P.Z[lo]) * u;
  const a = Math.max(0, lo - 3), b = Math.min(P.n - 1, hi + 3); o.yaw = Math.atan2(-(P.Z[b] - P.Z[a]), P.X[b] - P.X[a]); return o; }
// Speed profile (Director 10/23 evening): 8.33 m/s on straights, TURN_SPEED through curves, eased between them.
// Built per sample of the path P: limit(s) = min( curve limit, start ease (0→v over da, as before), stop ease (v→0 over the last dd, as before) ),
// where the curve limit is TURN_SPEED wherever the heading turns tighter than TURN_R_MAX, smoothed by forward/backward passes at TURN_ACC m/s².
// Each sample-to-sample step has constant acceleration, so position and speed are exact closed forms of time (no jumps, timeline = pure function of t).
function kin(P, da, dd, v) {
  const n = P.n, C = P.C, L = P.L, V = new Float64Array(n), T = new Float64Array(n), cl = new Float64Array(n).fill(v), w = 5;
  const hd = (i) => { const a = Math.max(0, i - w), b = Math.min(n - 1, i + w); return Math.atan2(P.Z[b] - P.Z[a], P.X[b] - P.X[a]); };
  for (let i = 0; i < n; i++) {                 // curvature from heading change over ±1 m
    const a = Math.max(0, i - w), b = Math.min(n - 1, i + w); if (b - a < 2) continue;
    let dh = hd(b) - hd(a); dh = Math.atan2(Math.sin(dh), Math.cos(dh)); const ds = C[b] - C[a];
    if (ds > 1e-6 && Math.abs(dh) / ds > 1 / TURN_R_MAX) cl[i] = Math.min(v, TURN_SPEED);
  }
  for (let i = 1; i < n; i++) cl[i] = Math.min(cl[i], Math.sqrt(cl[i - 1] ** 2 + 2 * TURN_ACC * (C[i] - C[i - 1])));        // ease out of turns
  for (let i = n - 2; i >= 0; i--) cl[i] = Math.min(cl[i], Math.sqrt(cl[i + 1] ** 2 + 2 * TURN_ACC * (C[i + 1] - C[i])));    // ease into turns
  const aS = v * v / (2 * da), aB = v * v / (2 * dd);
  for (let i = 0; i < n; i++) V[i] = Math.min(cl[i], Math.sqrt(2 * aS * C[i]), Math.sqrt(2 * aB * Math.max(0, L - C[i])));
  V[0] = 0; V[n - 1] = 0;
  for (let i = 1; i < n; i++) { const vs = V[i - 1] + V[i]; T[i] = T[i - 1] + (vs > 1e-9 ? 2 * (C[i] - C[i - 1]) / vs : 0); }
  let vmin = v; for (let i = 1; i < n - 1; i++) if (C[i] > da && C[i] < L - dd) vmin = Math.min(vmin, V[i]);
  return { L, n, C, V, T: T[n - 1], Ts: T, v, da, dd, vmin };
}
function kinAt(k, t, o) {
  if (t <= 0) { o[0] = 0; o[1] = 0; return o; }
  if (t >= k.T) { o[0] = k.L; o[1] = 0; return o; }
  let lo = 0, hi = k.n - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (k.Ts[m] <= t) lo = m; else hi = m; }
  const dt = k.Ts[hi] - k.Ts[lo], v0 = k.V[lo], v1 = k.V[hi], a = dt > 1e-12 ? (v1 - v0) / dt : 0, u = t - k.Ts[lo];
  o[0] = Math.min(k.C[hi], k.C[lo] + v0 * u + .5 * a * u * u); o[1] = v0 + a * u; return o;
}
function kinT(k, s) {               // time at which the profile reaches arc length s
  if (s <= 0) return 0; if (s >= k.L) return k.T;
  let lo = 0, hi = k.n - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (k.C[m] <= s) lo = m; else hi = m; }
  const v0 = k.V[lo], v1 = k.V[hi], ds = k.C[hi] - k.C[lo], d = s - k.C[lo]; if (ds < 1e-12) return k.Ts[lo];
  const vs = Math.sqrt(Math.max(0, v0 * v0 + (v1 * v1 - v0 * v0) * d / ds)); return k.Ts[lo] + (v0 + vs > 1e-9 ? 2 * d / (v0 + vs) : 0);
}
// Dense centre line from a marker to the next one, following its extras.next_leg exactly (straight, or arc about centre_glTF with sweep_deg).
// Arc direction comes from the marker's heading (extras.yaw_deg about +Y: 0 = +X, -90 = +Z), so it does not depend on the left/right convention.
function legPts(n, nx, step = 0.25) {
  const m = MK[n], a = [MX + m.x, m.z], b = nx; let L = m.e && m.e.next_leg; try { if (typeof L === 'string') L = JSON.parse(L); } catch (e) { L = null; }
  if (!L || L.type !== 'arc' || !L.centre_glTF) return line(a, b, step);
  const cx = MX + L.centre_glTF[0], cz = L.centre_glTF[2], r = Math.hypot(a[0] - cx, a[1] - cz), a0 = Math.atan2(a[1] - cz, a[0] - cx);
  const yw = ((m.e.yaw_deg != null ? m.e.yaw_deg : 0) * Math.PI) / 180, hx = Math.cos(yw), hz = -Math.sin(yw);
  const sg = (-Math.sin(a0) * hx + Math.cos(a0) * hz) >= 0 ? 1 : -1, sw = ((L.sweep_deg || 90) * Math.PI) / 180, k = Math.max(2, Math.ceil(r * sw / step)), o = [];
  for (let i = 1; i <= k; i++) { const t = a0 + sg * sw * i / k; o.push([cx + r * Math.cos(t), cz + r * Math.sin(t)]); }
  o[o.length - 1] = b; return o;
}
function chainPts(names, end) { const o = [mw(names[0])]; for (let i = 0; i < names.length; i++) { const nx = i + 1 < names.length ? mw(names[i + 1]) : end; if (nx) o.push(...legPts(names[i], nx)); } return o; }
const sortedMk = (re) => Object.keys(MK).filter(n => re.test(n) && !MK[n].fb).sort((a, b) => { const x = a.match(/(\d+)$/), y = b.match(/(\d+)$/); return x && y ? +x[1] - +y[1] : a < b ? -1 : 1; });
// Route. Marker-driven when the Mine GLB has Path_Out_* / Path_Ret_* (sorted by suffix): out on the inbound lane (z +9), return on the z 0 lane.
// Otherwise the INTERIM route: z +9 lane both ways across the gap (lane change on the Refinery's own road apron, no S-curve in the gap),
// back into the Mine's loop (Path_05..15) at the same flat speed → Path_Load_Approach → 2 s reverse under the chute.
function buildRoute() {
  const TP1 = rw('Truck_Path_01'), tp = (n) => rw('Truck_Path_0' + n), dp = rw('Truck_Dump'), ex = rw('Truck_Exit'), AP = mw('Path_Load_Approach');
  const outN = sortedMk(/^Path_Out_/), retN = sortedMk(/^Path_Ret_/);
  const uturn = [tp(3), tp(4), tp(5), tp(6), tp(7)];
  let out, back, legA, legB, legC, legD;           // haul leg out: legA → legB; back: legC → legD
  if (outN.length >= 2 && retN.length >= 2) {
    R.mode = 'markers';
    const O = outN.map(mw), Rt = retN.map(mw);
    legA = O[O.length - 1]; legD = Rt[0]; legB = TP1; legC = ex;
    out = [...chainPts(['Path_Load', ...outN.filter(n => n !== outN[outN.length - 1])], legA), ...line(legA, TP1, 2), ...line(TP1, tp(2), 2), ...uturn];   // Path_Load's next_leg is the 4.3 m straight
    back = [dp, ...line(dp, ex, 2), ...line(ex, legD, 2), ...chainPts(retN, AP)];
  } else {
    R.mode = 'interim';
    const RE = mw('Road_Entry'), RJ = [MX + 17, ROAD.zIn], lc = [];
    for (let i = 0; i <= 8; i++) { const u = i / 8; lc.push([RX - 20 - 18 * u, ROAD.zIn * u * u * (3 - 2 * u)]); }   // lane change z 0 → z 9 on the Refinery road (x −20 … −38 local)
    legA = RE; legB = TP1; legC = [RX - 46, ROAD.zIn]; legD = RJ;
    out = [mw('Path_Load'), mw('Path_01'), mw('Path_02'), mw('Path_03'), mw('Path_04'), RE, ...line(RE, TP1, 8), ...line(TP1, tp(2), 8), ...uturn];
    back = [dp, ...line(dp, lc[0], 6), ...lc.slice(1), ...line(lc[8], RJ, 8),
      ...['05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15'].map(k => mw('Path_' + k)), [MX - 2, 4.6], [MX + 2, 4.5], [MX + 5.5, 4.5], AP];
  }
  R.pOut = samplePath(out); R.pBack = samplePath(back);
  const sA = sOf(R.pOut, legA), sB = sOf(R.pOut, legB), sU = sOf(R.pOut, tp(3));
  R.legOut = sB - sA; const v = TV.v;                                   // 8.33 m/s on straights, TURN_SPEED through curves (Director 10/23)
  R.kOut = kin(R.pOut, TV.ease, TV.brake, v);                          // eased only where the truck stops: away from the chute, into the stop before the intake reverse
  const sC = sOf(R.pBack, legC), sD = sOf(R.pBack, legD);
  R.legBack = sD - sC; R.kBack = kin(R.pBack, TV.ease, TV.brake, v);  // eased away from the dump, 8.33 m/s straights / TURN_SPEED curves, eased stop at Path_Load_Approach
  const t1 = R.kOut.T, t2 = t1 + TV.revRef, t3 = t2 + TV.dump, t4 = t3 + TV.settle, t5 = t4 + R.kBack.T, t6 = t5 + TV.revMine;
  R.tl = { t1, t2, tDump: t2, t3, t4, t5, t6, trip: t6 };
  const f = (x) => +x.toFixed(2), tC = kinT(R.kBack, sC), tD = kinT(R.kBack, sD);
  window.__ps3d.route = { mode: R.mode, legOut: f(R.legOut), legBack: f(R.legBack), v: f(v), vTurn: TURN_SPEED, vMinOut: f(R.kOut.vmin), vMinBack: f(R.kBack.vmin), Lout: f(R.pOut.L), Lback: f(R.pBack.L), tl: Object.fromEntries(Object.entries(R.tl).map(([k, x]) => [k, f(x)])),
    phases: { mineOut: f(kinT(R.kOut, sA)), legOut: f(kinT(R.kOut, sB) - kinT(R.kOut, sA)), refIn: f(t1 - kinT(R.kOut, sB)), revRef: TV.revRef, dump: TV.dump, settle: TV.settle,
      refOut: f(tC), legBack: f(tD - tC), mineReturn: f(R.kBack.T - tD), mineReturnM: f(R.pBack.L - sD), revMine: TV.revMine, trip: f(t6) } };
  buildTempRoad();
}
let roadMesh = null;
// Art's 8 m haul-road strip (shared/road 6f06c39, md5 661e3582…, pending Director review): 11 unscaled tiles at Mine-local x 26 + 8i, both lanes (z +9 / z 0).
// Swap back to the flat temp tiles with ?road=temp (or set ROAD_GLB to null).
const ROAD_GLB = Q.get('road') === 'temp' ? null : 'models/haul_road_seg_661e358.glb?v=661e3582';
let roadSeg = null;
if (ROAD_GLB) loader.load(ROAD_GLB, (g) => { g.scene.updateMatrixWorld(true); g.scene.traverse(o => { if (!roadSeg && o.isMesh) roadSeg = { geo: o.geometry, mat: o.material, m: o.matrixWorld.clone() }; }); buildTempRoad(); },
  undefined, (e) => console.warn('haul road strip failed, keeping the temp road', e));
function buildTempRoad() {            // haul road across the gap: Art's strip when loaded, else TEMP flat tiles (same layout; z 0 lane only once the Mine has a return lane)
  if (roadMesh) { scene.remove(roadMesh); roadMesh.traverse(o => o.geometry && o.geometry !== (roadSeg && roadSeg.geo) && o.geometry.dispose()); }
  if (roadSeg) {
    roadMesh = new THREE.Group(); roadMesh.name = 'HaulRoad';
    const im = new THREE.InstancedMesh(roadSeg.geo, roadSeg.mat, ROAD.n); im.name = 'HaulRoad_Tiles';
    for (let i = 0; i < ROAD.n; i++) im.setMatrixAt(i, roadTileM(i).multiply(roadSeg.m));
    im.receiveShadow = true; im.frustumCulled = false; roadMesh.add(im); scene.add(roadMesh); window.__ps3d && (window.__ps3d.road = 'strip'); if (typeof buildCargoRoad === 'function') buildCargoRoad(); return;
  }
  if (window.__ps3d) window.__ps3d.road = 'temp';
  roadMesh = new THREE.Group(); roadMesh.name = 'TempRoad';
  const mat = new THREE.MeshStandardMaterial({ color: 0x55575c, roughness: .95, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  const lanes = []; for (let i = 0; i < ROAD.n; i++) { const x = ROAD.x0 + ROAD.tile * i; lanes.push([i, ROAD.zIn]); if (R.mode === 'markers') lanes.push([i, ROAD.zOut]); }
  const tile = new THREE.PlaneGeometry(ROAD.tile, 4.6).rotateX(-Math.PI / 2).translate(ROAD.tile / 2, .03, 0);
  const im = new THREE.InstancedMesh(tile, mat, lanes.length); lanes.forEach((l, i) => im.setMatrixAt(i, roadTileM(l[0], l[1]))); im.receiveShadow = true; roadMesh.add(im);
  scene.add(roadMesh); if (typeof buildCargoRoad === 'function') buildCargoRoad();
}
const fillAt = (t) => { const k = S.tk; if (k.dep) return 1; return clamp((t - k.c0) / (fillSec() * 1000) + k.add, 0, 1); };
const tFull = () => { const k = S.tk; return Math.max(k.c0 + (1 - Math.min(1, k.add)) * fillSec() * 1000, k.lr ? k.lr + CFG.richPayDelay * 1000 : 0); };   // never drive while truck_load_rich runs
const TS = { ph: 'fill', x: MX + 4.7, z: 4.5, yaw: 0, v: 0, fill: 0, shown: 0, el: 0 };
const _ka = [0, 0];
function poseAt(t, o = TS) {
  const k = S.tk, tl = R.tl;
  if (!k.dep || t < k.dep) { const p = mw('Path_Load'); o.ph = 'fill'; o.x = p[0]; o.z = p[1]; o.yaw = 0; o.v = 0; o.fill = fillAt(t); o.el = 0; return o; }
  const el = o.el = (t - k.dep) / 1000; o.fill = 1;
  if (el < tl.t1) { kinAt(R.kOut, el, _ka); pathAt(R.pOut, _ka[0], o); o.v = _ka[1]; o.ph = 'out'; }
  else if (el < tl.t2) { const u = fss((el - tl.t1) / TV.revRef), a = rw('Truck_Path_07'), b = rw('Truck_Dump'); o.x = a[0] + (b[0] - a[0]) * u; o.z = a[1] + (b[1] - a[1]) * u; o.yaw = Math.PI; o.v = -1; o.ph = 'rev'; }
  else if (el < tl.t4) { const b = rw('Truck_Dump'); o.x = b[0]; o.z = b[1]; o.yaw = Math.PI; o.v = 0; o.ph = el < tl.t3 ? 'dump' : 'settle'; if (el >= tl.t3) o.fill = 0; }
  else if (el < tl.t5) { kinAt(R.kBack, el - tl.t4, _ka); pathAt(R.pBack, _ka[0], o); o.v = _ka[1]; o.ph = 'back'; o.fill = 0; }
  else { const u = fss((el - tl.t5) / TV.revMine), a = mw('Path_Load_Approach'), b = mw('Path_Load'); o.x = a[0] + (b[0] - a[0]) * u; o.z = a[1] + (b[1] - a[1]) * u; o.yaw = 0; o.v = -1; o.ph = 'revMine'; o.fill = 0; }
  return o;
}
const truckOnRoad = () => (TS.ph === 'out' || TS.ph === 'back') && TS.x > MX + 13.5 && TS.x < RX - 46;
// ---- settling: everything due up to time T happens exactly once (acc = away accumulator → offline 50%, no pops)
function payPend(T, acc) {
  for (let i = S.pend.length - 1; i >= 0; i--) { const p = S.pend[i]; if (p.at > T) continue; S.pend.splice(i, 1); S.money += p.v; if (acc) acc.rich += p.v; else richPop(p.v); window.__ps3d.richPaid = (window.__ps3d.richPaid || []).concat({ at: p.at, paidAt: nowMs(), v: p.v }).slice(-10); }
}
function payBase(v, acc) {
  const amt = acc && !acc.full ? v * CFG.offlineRate : v; S.money += amt; S.loads++;
  logU('truck', `Truck dropped a load at the Refinery, +${fmt(amt)}`);
  window.__ps3d.dumps = (window.__ps3d.dumps || []).concat({ at: nowMs(), amt, off: !!acc }).slice(-20);
  if (acc) { acc.base += amt; acc.n++; return; }
  if (S.site === REF && Math.abs(camX - RX) < 3 && !document.hidden) { const b = rw('Truck_Dump'), w = new THREE.Vector3(b[0] + 3, 3.5, b[1]), sp = toScreen(w.x, w.y, w.z);
    pop('+' + fmt(amt), sp.x, sp.y - 24, 'bonus big'); flyChunks(8, w, amt, '', true); }   // full pop on the Refinery screen
  else smallPop(amt);
  if (refActs.intake_shake) refActs.intake_shake.reset().play();
}
function richPop(v) {
  if (S.site === MINE && Math.abs(camX - MX) < 3 && !document.hidden) { const r = MK.Rich_Pop, w = new THREE.Vector3(MX + r.x, r.y, r.z), sp = toScreen(w.x, w.y, w.z);
    pop('+' + fmt(v), sp.x, sp.y - 10, 'bonus'); flyChunks(4, w, v, 'bonus', true); }
  else smallPop(v);
}
let richTw = null;
function playRich() { const a = tActs.truck_load_rich; if (a) { a.reset(); a.play(); } }
function arrive(t, acc) {             // back under the chute: the next fill starts; rich loads queued while away drop in now
  const k = S.tk, q = Math.min(k.q || 0, 4);
  k.c0 = t; k.add = Math.min(1, q * CFG.richFill); k.lr = q ? t : 0; k.dep = 0; k.paid = false; k.val = 0; k.q = 0; k.qd = [];
  for (let i = 0; i < q; i++) S.pend.push({ at: t + CFG.richPayDelay * 1000, v: CFG.richBonus });
  for (const d of deposits) if (d.tkq) { d.tkq = false; d.at = t; }
  if (q && !acc) { richTw = { at: t, amt: k.add }; playRich(); }
}
function settleTo(T, acc) {
  const k = S.tk, tl = R.tl; if (!tl) return;
  payPend(T, acc);
  for (let g = 0; g < 20000; g++) {
    if (!k.dep) { const tf = tFull(); if (tf > T) break; k.dep = tf; k.paid = false; k.val = loadValue(); continue; }   // full: depart (value frozen now)
    if (!k.paid) { if (k.dep + tl.tDump * 1000 > T) break; k.paid = true; payBase(k.val, acc); cgMake(k.dep + tl.tDump * 1000); }
    const end = k.dep + tl.trip * 1000; if (end > T) break;
    arrive(end, acc); payPend(T, acc);
  }
  cgMakeDue(T); cgSettle(T, acc);     // cargo loop: same clock, same exactly-once rule
}
function shiftTk(d) { const k = S.tk; k.c0 += d; if (k.lr) k.lr += d; if (k.dep) k.dep += d; for (const p of S.pend) p.at += d; cgShift(d); }
function tapDeposit(d) {
  const t = nowMs(), k = S.tk; settleTo(t, null);
  let res;
  if (!k.dep && fillAt(t) < 1) {         // parked and filling: the drill sends a rich load down the chute now (+25%, capped at 100%; overflow is lost)
    const amt = Math.min(CFG.richFill, 1 - fillAt(t)); k.add += amt; k.lr = t;
    S.pend.push({ at: t + CFG.richPayDelay * 1000, v: CFG.richBonus });
    richTw = { at: t, amt }; playRich(); d.claimed = true; d.at = t; res = 'rich';
  } else { k.q = Math.min(4, (k.q || 0) + 1); k.qd.push(d.mk); d.claimed = true; d.tkq = true; res = 'queued'; }   // truck away: queued into the next fill
  S.dep++; save(); window.__ps3d.lastTap = { at: t, res, mk: d.mk };
  return res;
}
// ---- per-frame pose, wheels, clips, fill morph, arc gauge
const _X = new THREE.Vector3(1, 0, 0), _wq = new THREE.Quaternion(), _fa = new THREE.Vector3();
const WH = { a: 0, d: 0, x: null, z: 0 };
const farc = $('farc'), farcV = $('farcV'), farcT = $('farcT'); let farcK = '';
function setAct(a, on) { if (!a) return; if (on) { if (!a.isRunning()) { a.reset(); a.play(); } } else if (a.isRunning() || a.enabled && a.getEffectiveWeight() > 0 && a.time > 0) a.stop(); }
function updTruck() {
  if (!R.tl) return; const t = nowMs(); poseAt(t, TS);
  let shown = TS.fill; if (TS.ph === 'fill' && richTw) { const u = (t - richTw.at) / 1000; if (u >= 1 || u < 0) richTw = null; else shown -= richTw.amt * (1 - fss(u)); }
  TS.shown = clamp(shown, 0, 1);
  setDigging(TS.ph === 'fill' && TS.fill < 1);
  if (TS.ph !== TS.last) { (window.__ps3d.phases = window.__ps3d.phases || []).push({ ph: TS.ph, at: t }); if (window.__ps3d.phases.length > 40) window.__ps3d.phases.shift(); TS.last = TS.ph; }
  if (!truck) return;
  truck.position.set(TS.x, 0, TS.z); truck.rotation.set(0, TS.yaw, 0);
  if (WH.x !== null) { const dx = TS.x - WH.x, dz = TS.z - WH.z; if (Math.hypot(dx, dz) < 20) { const ds = dx * Math.cos(TS.yaw) - dz * Math.sin(TS.yaw); WH.a += ds / TV.wheelR; WH.d += ds; } }   // roll by the real distance (no skating)
  WH.x = TS.x; WH.z = TS.z;
  for (const w of wheels) w.b.quaternion.copy(w.q0).multiply(_wq.setFromAxisAngle(_X, WH.a));   // rest × rotX(angle), + = forward
  const moving = TS.ph === 'out' || TS.ph === 'back' || TS.ph === 'rev' || TS.ph === 'revMine';
  setAct(tActs.truck_drive, moving);                         // bed rattle only while moving (never with truck_dump)
  setAct(tActs.chute_pour, TS.ph === 'fill' && TS.fill < 1);  // only parked at Path_Load
  const dA = tActs.truck_dump;
  if (dA) { if (TS.ph === 'dump') { dA.enabled = true; if (!dA.isScheduled()) dA.play(); dA.paused = true; dA.setEffectiveWeight(1); dA.time = Math.min(TS.el - R.tl.t2, dA.getClip().duration - 1e-3); } else if (dA.isScheduled()) dA.stop(); }
  const pct = TS.ph === 'fill' ? TS.shown : TS.fill, inf = pct > 0 ? .5 + .5 * pct ** .8 : 0;
  for (const [m, i] of fillMeshes) m.morphTargetInfluences[i] = inf;
}
function updFillArc() {                // slim cyan fill-% arc at Fill_Arc while the truck is under the chute (hidden once it leaves)
  let on = !!(fillArcNode && TS.ph === 'fill' && S.site === MINE && Math.abs(camX - MX) < 3 && !document.hidden);
  if (on) { truckRoot.updateMatrixWorld(); fillArcNode.getWorldPosition(_fa); const p = toScreen(_fa.x, _fa.y, _fa.z, camera, _scr); on = p.z < 1;
    if (on) { farc.style.left = p.x.toFixed(1) + 'px'; farc.style.top = p.y.toFixed(1) + 'px'; const pc = Math.floor(TS.shown * 100), k = pc + '';
      if (k !== farcK) { farcK = k; farcV.setAttribute('stroke-dasharray', (62.83 * TS.shown).toFixed(2) + ' 999'); farcT.textContent = pc + '%'; } } }
  if (farc._on !== on) { farc._on = on; farc.style.display = on ? 'block' : 'none'; }
}
setInterval(() => { if (document.hidden) return; const t = nowMs(); if (t - S.rt < 60000 && t >= S.rt - 1000) { settleTo(t, null); S.rt = t; } }, 200);   // payouts keep wall-clock time even when frames stall
// ===== CARGO LOOP (Director spec 10/23, Jacob's request). GRAY-BOX PLACEHOLDERS until Art's GLBs land; every joint/marker is read by name
// through CARGO_ALIAS, so the GLBs drop in with the same code path.
//   Refinery dump → 1 sealed He-3 box at the Refinery crane's Pick_Point (after sealSec) → Refinery crane loads 2 onto flatbed FB-05 (Bed_Slot_01/02)
//   → FB-05 drives the Refinery↔Launch Pad road: lane z 13 east (loaded), U-turn past the pad, lane z 22 west (empty), U-turn back into the
//     loading spot. Lane choice: both cargo lanes are on the camera side (+z) of the Refinery, z 13 / 22, world x 307–481; the Mine↔Refinery haul road and
//     HT-04's Refinery U-turn stay at z ≤ 9 (truck body ≤ z 10.3, FB-05 body ≥ z 11.7), so the two loops never cross or share a lane.
//   → at the pad the astronaut walks out to Receive_Point (walk_out), guides each lift (guide), checks each box in (check_in), walks back (walk_back)
//   → pad crane sets each box in the cargo bay → while a ship is on the pad the pad crane moves bay boxes into Hold_01..10
//   → the ship launches when the hold is full AND the fuel is full; the boxes sell at the top of the climb; the ship is away, lands, refuels.
// State is S.cg (timestamps only). A small event simulation inside settleTo advances it, so every step happens exactly once whether the game is
// open, locked, frozen or closed (catchUp: 50% sale value after 5 min away, nothing past the 4 h cap). Poses are pure functions of S.cg + now.
const CG = CFG.cargo;
const CARGO_ALIAS = {        // one table for every name the code looks up (first match wins)
  flatbed: ['FB05', 'FB-05', 'Flatbed', 'Truck'], wheelRadius: 'wheel_radius', wheel: /^(FB05_)?Wheel/,   // root +X forward at yaw 0
  bedSlot1: ['Bed_Slot_01', 'Bed_Socket'], bedSlot2: ['Bed_Slot_02'], bedSlot2Offset: [-1.7, 0, 0],      // only Bed_Socket? slot 2 = socket + offset (root-local m)
  slew: ['Slew'], trolley: ['Trolley'], hoist: ['Hoist'], hook: ['Hook'], pick: ['Pick_Point'], drop: ['Drop_Point'],   // cranes: no baked clips, code drives the joints
  boxHook: ['Hook_Point'], boxBase: ['Base'],
  hold: (i) => ['Hold_' + String(i).padStart(2, '0')],
  receive: ['Receive_Point', 'Hand_Point'],
  signClips: ['sign_for_delivery', 'astro_sign_delivery', 'sign', 'check_in'], walkClips: ['walk', 'astro_walk'], idleClips: ['idle', 'astro_idle'],
};
// Placeholder layout, station-local metres (x from the station origin i·160, z world). Swap a GLB in and its markers replace these.
const CPH = {
  lanes: { out: 13, back: 22 }, road: { x0: RX - 8, n: 21, tile: 8 },                        // 21 strip tiles, world x 312–480, lanes z 13 / 22
  // Refinery side sits inside Art's Cam_Target frame (x ≈ 300–330): FB-05 loads at x 318; the crane + sealed-box pallet stand in the median between the lanes
  ref: { load: [-2, 13], uturn: [-8, 17.5], crane: [1.5, 17.5], pick: [5.5, 17.5], mast: 9, jib: 8, rest: [-1.2, 0] },   // rest = yaw offset from the pick direction
  pad: { unload: [-14, 13], uturn: [-4, 17.5], crane: [-7, 5], mast: 12, jib: 12, bay: [-12, 3], ship: [1, 0], padTop: 1,
         home: [-16.5, 4], receive: [-13.5, 10.8], fuel: [4.4, 4.2] },
  turnR: 4.5, hookHi: 5.5,
};
const PADI = 3, PX = PADI * GAP;
const findA = (root, names) => { for (const n of names) { const o = root.getObjectByName(n); if (o) return o; } return null; };
const CG_LOG = [];
function cgEv(e, t, x) { CG_LOG.push(Object.assign({ e, at: t }, x || {})); if (CG_LOG.length > 200) CG_LOG.shift(); }
function cgInit(t) { return { v: 1, t, ref: [], made: 0, sold: 0, launches: 0, earned: 0, rc: 0, fb: { st: 'load', t0: t, bed: 0 }, pc: { k: '', t0: 0 }, as: { st: 'home', t0: t }, bay: 0,
  sh: { st: 'pad', t0: t, hold: 0, f0: t } }; }
if (!S.cg || S.cg.v !== 1) S.cg = cgInit(S.rt);   // saves from before the cargo loop: it starts empty at the last save time (no back-pay for old dumps)

// ---- flatbed route (same speed profile as HT-04: 8.33 m/s straights, TURN_SPEED in the 4.5 m U-turns, same 3 m pull-away / 4 m brake)
const FB = { pOut: null, pBack: null, kOut: null, kBack: null, S: null, U: null };
function arcPts(cx, cz, r, a0, a1, step = .25) { const k = Math.max(2, Math.ceil(Math.abs(a1 - a0) * r / step)), o = []; for (let i = 1; i <= k; i++) { const a = a0 + (a1 - a0) * i / k; o.push([cx + r * Math.cos(a), cz + r * Math.sin(a)]); } return o; }
function buildCargoRoute() {
  const L = CPH.lanes, r = CPH.turnR, Sx = RX + CPH.ref.load[0], Ux = PX + CPH.pad.unload[0], ex = PX + CPH.pad.uturn[0], wx = RX + CPH.ref.uturn[0];
  FB.S = [Sx, L.out]; FB.U = [Ux, L.out];
  FB.pOut = samplePath([FB.S, ...line(FB.S, FB.U, 2)]);
  FB.pBack = samplePath([FB.U, ...line(FB.U, [ex, L.out], 2), ...arcPts(ex, (L.out + L.back) / 2, r, -Math.PI / 2, Math.PI / 2),
    ...line([ex, L.back], [wx, L.back], 2), ...arcPts(wx, (L.out + L.back) / 2, r, Math.PI / 2, 1.5 * Math.PI), ...line([wx, L.out], FB.S, 1)]);
  FB.kOut = kin(FB.pOut, TV.ease, TV.brake, TV.v); FB.kBack = kin(FB.pBack, TV.ease, TV.brake, TV.v);
}

// ---- event simulation (exactly once). Activities start at an event time; their end is the next event. Box counts move at the start of a
// lift (off the stack / bed / bay) and land at its end (bed / bay / hold), so one crane never double-counts a box.
function cgMake(tDump) { const c = S.cg; c.ref.push(tDump + CG.sealSec * 1000); c.made++; cgEv('box_made', tDump); }
function cgDecide(c, t) {
  for (let g = 0; g < 50; g++) {
    let ch = false; const f = c.fb, s = c.sh;
    if (!c.rc && f.st === 'load' && f.bed < CG.perTrip && c.ref.length && c.ref[0] <= t) { c.ref.shift(); c.rc = t; ch = true; cgEv('ref_crane_lift', t, { slot: f.bed + 1 }); }
    if (!c.rc && f.st === 'load' && f.bed >= CG.perTrip) { c.fb = { st: 'out', t0: t, bed: f.bed }; ch = true; cgEv('fb_depart', t, { bed: f.bed }); }
    if (!c.pc.k) {
      if (c.fb.st === 'unload' && c.as.st === 'ready' && c.fb.bed > 0 && c.bay < CG.bayCap) { c.fb.bed--; c.pc = { k: 'unload', t0: t }; ch = true; cgEv('pad_crane_unload', t, { slot: c.fb.bed + 1 }); }
      else if (s.st === 'pad' && c.bay > 0 && s.hold < CG.holdCap) { c.bay--; c.pc = { k: 'hold', t0: t }; ch = true; cgEv('pad_crane_hold', t, { slot: s.hold + 1 }); }
    }
    if (c.fb.st === 'unload' && c.fb.bed === 0 && c.pc.k !== 'unload' && c.as.st === 'ready') { c.fb = { st: 'back', t0: t, bed: 0 }; c.as = { st: 'walk_back', t0: t }; ch = true; cgEv('fb_return', t); }
    if (s.st === 'pad' && s.hold >= CG.holdCap && c.pc.k !== 'hold' && t >= s.f0 + CG.fuelFillSec * 1000) { c.sh = Object.assign({}, s, { st: 'launch', t0: t }); ch = true; cgEv('launch', t, { hold: s.hold }); }
    if (!ch) break;
  }
}
function cgNext(c) {
  let n = Infinity; const T = (x) => { if (x < n) n = x; }, s = c.sh;
  if (c.rc) T(c.rc + CG.refLoadSec * 1000); else if (c.fb.st === 'load' && c.fb.bed < CG.perTrip && c.ref.length && c.ref[0] > c.t) T(c.ref[0]);
  if (c.fb.st === 'out') T(c.fb.t0 + FB.kOut.T * 1000); else if (c.fb.st === 'back') T(c.fb.t0 + FB.kBack.T * 1000);
  if (c.as.st === 'walk_out' || c.as.st === 'walk_back') T(c.as.t0 + CG.walkSec * 1000);
  if (c.pc.k) T(c.pc.t0 + (c.pc.k === 'unload' ? CG.padUnloadSec : CG.holdLoadSec) * 1000);
  if (s.st === 'launch') T(s.t0 + CG.launchSec * 1000); else if (s.st === 'away') T(s.t0 + CG.awaySec * 1000); else if (s.st === 'land') T(s.t0 + CG.landSec * 1000);
  else if (s.hold >= CG.holdCap && c.pc.k !== 'hold' && s.f0 + CG.fuelFillSec * 1000 > c.t) T(s.f0 + CG.fuelFillSec * 1000);
  return n;
}
function cgComplete(c, t, acc) {
  if (c.rc && c.rc + CG.refLoadSec * 1000 <= t) { c.rc = 0; c.fb.bed++; cgEv('bed_loaded', t, { bed: c.fb.bed }); }
  if (c.fb.st === 'out' && c.fb.t0 + FB.kOut.T * 1000 <= t) { c.fb = { st: 'unload', t0: t, bed: c.fb.bed }; c.as = { st: 'walk_out', t0: t }; cgEv('fb_at_pad', t, { bed: c.fb.bed }); }
  else if (c.fb.st === 'back' && c.fb.t0 + FB.kBack.T * 1000 <= t) { c.fb = { st: 'load', t0: t, bed: 0 }; cgEv('fb_at_refinery', t); }
  if (c.as.st === 'walk_out' && c.as.t0 + CG.walkSec * 1000 <= t) { c.as = { st: 'ready', t0: t }; cgEv('astro_ready', t); }
  else if (c.as.st === 'walk_back' && c.as.t0 + CG.walkSec * 1000 <= t) { c.as = { st: 'home', t0: t }; cgEv('astro_home', t); }
  if (c.pc.k && c.pc.t0 + (c.pc.k === 'unload' ? CG.padUnloadSec : CG.holdLoadSec) * 1000 <= t) {
    if (c.pc.k === 'unload') { c.bay++; cgEv('checked_in_bay', t, { bay: c.bay }); } else { c.sh.hold++; cgEv('hold_loaded', t, { hold: c.sh.hold }); }
    c.pc = { k: '', t0: 0 };
  }
  const s = c.sh;
  if (s.st === 'launch' && s.t0 + CG.launchSec * 1000 <= t) {        // top of the climb: the hold sells
    const v = s.hold * CG.boxValue, amt = acc && !acc.full ? v * CFG.offlineRate : v; S.money += amt; c.sold += s.hold; c.earned += amt; c.launches++;
    cgEv('sold', t, { boxes: s.hold, amt }); logU('truck', `Cargo ship sold ${s.hold} He-3 boxes, +${fmt(amt)}`);
    if (acc) acc.cargo = (acc.cargo || 0) + amt; else cargoPop(amt);
    c.sh = { st: 'away', t0: t, hold: 0, f0: s.f0 };
  } else if (s.st === 'away' && s.t0 + CG.awaySec * 1000 <= t) { c.sh = { st: 'land', t0: t, hold: 0, f0: s.f0 }; cgEv('landing', t); }
  else if (s.st === 'land' && s.t0 + CG.landSec * 1000 <= t) { c.sh = { st: 'pad', t0: t, hold: 0, f0: t }; cgEv('landed', t); }   // refuelling starts on touchdown
}
function cgSettle(T, acc) {
  const c = S.cg; if (!FB.kOut) return;
  for (let g = 0; g < 200000; g++) {
    cgDecide(c, c.t);
    const nx = cgNext(c); if (!(nx <= T)) break;
    c.t = Math.max(c.t, nx); cgComplete(c, c.t, acc);
  }
}
function cgShift(d) { const c = S.cg; c.t += d; c.ref = c.ref.map(x => x + d); if (c.rc) c.rc += d; c.fb.t0 += d; if (c.pc.k) c.pc.t0 += d; c.as.t0 += d; c.sh.t0 += d; c.sh.f0 += d; }
const fuelAt = (t) => { const s = S.cg.sh; return s.st === 'pad' ? clamp((t - s.f0) / (CG.fuelFillSec * 1000), 0, 1) : s.st === 'launch' ? 1 : 0; };   // PLACEHOLDER fuel: fills over fuelFillSec from touchdown
function astroPhase(c, t) {
  const a = c.as; if (a.st !== 'ready') return a.st;
  if (c.pc.k === 'unload') { const u = (t - c.pc.t0) / (CG.padUnloadSec * 1000); return u >= 1 - CG.checkSec / CG.padUnloadSec ? 'check_in' : 'guide'; }
  return 'guide';
}
function cargoPop(amt) {
  if (S.site === PADI && Math.abs(camX - PX) < 3 && !document.hidden && cg3.ship) { const sp = toScreen(cg3.ship.position.x, cg3.ship.position.y + 6, cg3.ship.position.z); pop('+' + fmt(amt), sp.x, sp.y, 'bonus big'); bumpMoney(); }
  else smallPop(amt);
}

// ---- gray-box placeholders (named exactly like the art will be)
const cgMat = new THREE.MeshStandardMaterial({ color: 0x9a9ea6, roughness: .8, metalness: .1 });
const fbMat = new THREE.MeshStandardMaterial({ color: 0x6c7f95, roughness: .7, metalness: .15 });   // FB-05 placeholder: blue-gray so it reads against the gray props
const cgDark = new THREE.MeshStandardMaterial({ color: 0x3a3d44, roughness: .9 });
const boxMat = new THREE.MeshStandardMaterial({ color: 0xc9d3dc, roughness: .55, metalness: .2, emissive: 0x0c4458, emissiveIntensity: .6 });
const geoAt = (g, x, y, z) => g.translate(x, y, z);
const merged = (gs) => mergeGeometries(gs.map(g => g.index ? g.toNonIndexed() : g));
const shadowy = (m) => { m.castShadow = m.receiveShadow = true; return m; };
const cg3 = {};
function phBoxProp() {     // He-3 cargo box: origin = Base (bottom centre), Hook_Point on top
  const g = new THREE.Group(); g.name = 'CargoBox_He3';
  const b = new THREE.Object3D(); b.name = 'Base'; const h = new THREE.Object3D(); h.name = 'Hook_Point'; h.position.y = 1.0; g.add(b, h); return g;
}
function phFlatbed() {
  const g = new THREE.Group(); g.name = 'FB05'; g.userData.wheel_radius = 0.5;
  const body = shadowy(new THREE.Mesh(merged([geoAt(new THREE.BoxGeometry(7.4, .45, 2.3), 0, .75, 0), geoAt(new THREE.BoxGeometry(1.9, 1.8, 2.4), 2.65, 1.85, 0),
    geoAt(new THREE.BoxGeometry(5.3, .2, 2.6), -1.0, 1.08, 0)]), fbMat)); body.name = 'FB05_Body'; g.add(body);
  const wg = new THREE.CylinderGeometry(.5, .5, .42, 14).rotateX(Math.PI / 2), wm = new THREE.InstancedMesh(wg, cgDark, 6); wm.name = 'Wheel_All'; wm.castShadow = true; g.add(wm);
  g.userData.wheelPos = [[2.6, .5, 1.2], [2.6, .5, -1.2], [-.7, .5, 1.2], [-.7, .5, -1.2], [-2.5, .5, 1.2], [-2.5, .5, -1.2]];
  const s1 = new THREE.Object3D(); s1.name = 'Bed_Slot_01'; s1.position.set(-.15, 1.18, 0); const s2 = new THREE.Object3D(); s2.name = 'Bed_Slot_02'; s2.position.set(-1.85, 1.18, 0); g.add(s1, s2);
  return g;
}
function phCrane(name, mastH, jib, markers) {   // root at the mast foot; Slew (yaw) at the mast top → Trolley (+X along the jib) → Hoist (−Y, hook height) → Hook
  const g = new THREE.Group(); g.name = name;
  g.add(shadowy(new THREE.Mesh(merged([geoAt(new THREE.BoxGeometry(.6, mastH, .6), 0, mastH / 2, 0), geoAt(new THREE.BoxGeometry(2, .3, 2), 0, .15, 0)]), cgMat)));
  const slew = new THREE.Object3D(); slew.name = 'Slew'; slew.position.y = mastH; g.add(slew);
  slew.add(shadowy(new THREE.Mesh(merged([geoAt(new THREE.BoxGeometry(jib + 2.5, .4, .45), (jib - 2.5) / 2, .2, 0), geoAt(new THREE.BoxGeometry(1.2, .9, .9), -2.2, -.2, 0)]), cgMat)));
  const tr = new THREE.Object3D(); tr.name = 'Trolley'; tr.position.x = jib * .5; slew.add(tr);
  const cable = new THREE.Mesh(geoAt(new THREE.BoxGeometry(.06, 1, .06), 0, -.5, 0), cgDark); cable.name = 'Cable'; tr.add(cable); tr.userData.cable = cable;
  tr.add(new THREE.Mesh(geoAt(new THREE.BoxGeometry(.6, .3, .55), 0, -.1, 0), cgDark));
  const ho = new THREE.Object3D(); ho.name = 'Hoist'; ho.position.y = -3; tr.add(ho);
  const hk = new THREE.Mesh(geoAt(new THREE.BoxGeometry(.5, .35, .5), 0, .18, 0), cgDark); hk.name = 'Hook'; ho.add(hk);
  for (const [n, p] of Object.entries(markers)) { const m = new THREE.Object3D(); m.name = n; m.position.set(p[0], 0, p[1]); g.add(m); }
  return g;
}
function phShip() {
  const g = new THREE.Group(); g.name = 'Ship_Placeholder';
  const parts = [geoAt(new THREE.CylinderGeometry(2, 2, 7, 20), 0, 4.1, 0), geoAt(new THREE.ConeGeometry(2, 2.4, 20), 0, 8.8, 0), geoAt(new THREE.BoxGeometry(3.2, .3, 6.2), -3.9, .3, 0)];
  for (const [x, z] of [[1.7, 1.7], [-1.7, 1.7], [1.7, -1.7], [-1.7, -1.7]]) parts.push(geoAt(new THREE.BoxGeometry(.35, 1.2, .35), x, .6, z));
  g.add(shadowy(new THREE.Mesh(merged(parts), cgMat)));
  for (let i = 0; i < 10; i++) { const m = new THREE.Object3D(); m.name = 'Hold_' + String(i + 1).padStart(2, '0'); m.position.set(i < 5 ? -3.15 : -4.65, .45, -2.3 + 1.15 * (i % 5)); g.add(m); }
  return g;
}
function buildCargoProps() {
  // Refinery crane + box pallet
  const rp = CPH.ref, rc = phCrane('Crane_Refinery', rp.mast, rp.jib, { Pick_Point: [rp.pick[0] - rp.crane[0], rp.pick[1] - rp.crane[1]], Drop_Point: [rp.load[0] - rp.crane[0], rp.load[1] - rp.crane[1]] });
  rc.position.set(RX + rp.crane[0], 0, rp.crane[1]); scene.add(rc);
  const pal = shadowy(new THREE.Mesh(geoAt(new THREE.BoxGeometry(3.4, .15, 2.6), 0, .075, 0), cgDark)); pal.position.set(RX + rp.pick[0], 0, rp.pick[1]); scene.add(pal);
  // Launch Pad group (gray slab from the station placeholders + bay + crane + ship + astronaut + fuel gauge); bounds-fit framing
  const pp = CPH.pad, pg = new THREE.Group(); pg.name = 'LaunchPad_Placeholder'; pg.position.set(PX, 0, 0); scene.add(pg);
  if (phBox[PADI]) { scene.remove(phBox[PADI]); phBox[PADI].position.set(0, .5, 0); pg.add(phBox[PADI]); }
  const bay = shadowy(new THREE.Mesh(merged([geoAt(new THREE.BoxGeometry(5.6, .25, 5.6), 0, .125, 0), geoAt(new THREE.BoxGeometry(5.6, 1.2, .25), 0, .6, -2.8),
    geoAt(new THREE.BoxGeometry(.25, 1.2, 5.6), -2.8, .6, 0), geoAt(new THREE.BoxGeometry(.25, 1.2, 5.6), 2.8, .6, 0)]), cgMat)); bay.name = 'Cargo_Bay'; bay.position.set(pp.bay[0], 0, pp.bay[1]); pg.add(bay);
  const pc = phCrane('Crane_Pad', pp.mast, pp.jib, { Pick_Point: [pp.unload[0] - pp.crane[0], pp.unload[1] - pp.crane[1]], Drop_Point: [pp.bay[0] - pp.crane[0], pp.bay[1] - pp.crane[1]] });
  pc.position.set(pp.crane[0], 0, pp.crane[1]); pg.add(pc);
  const ship = phShip(); ship.position.set(PX + pp.ship[0], pp.padTop, pp.ship[1]); scene.add(ship);
  const rcv = new THREE.Object3D(); rcv.name = 'Receive_Point'; rcv.position.set(pp.receive[0], 0, pp.receive[1]); pg.add(rcv);
  const home = new THREE.Object3D(); home.name = 'Astro_Home'; home.position.set(pp.home[0], 0, pp.home[1]); pg.add(home);
  const astro = new THREE.Group(); astro.name = 'Astronaut_Placeholder';
  astro.add(shadowy(new THREE.Mesh(merged([geoAt(new THREE.CapsuleGeometry(.36, 1.0, 4, 10), 0, .86, 0), geoAt(new THREE.BoxGeometry(.4, .22, .3), .22, 1.42, 0)]),
    new THREE.MeshStandardMaterial({ color: 0xf2f2ee, roughness: .6 })))); scene.add(astro);
  const fuelBack = new THREE.Mesh(geoAt(new THREE.BoxGeometry(.6, 6, .5), 0, 3, 0), cgDark); fuelBack.position.set(pp.fuel[0], 0, pp.fuel[1]); pg.add(fuelBack);
  const fuelFill = new THREE.Mesh(geoAt(new THREE.BoxGeometry(.45, 1, .56), 0, .5, 0), new THREE.MeshStandardMaterial({ color: 0xffb340, emissive: 0xff7a00, emissiveIntensity: .9 }));
  fuelFill.name = 'Fuel_Gauge_PLACEHOLDER'; fuelFill.position.set(pp.fuel[0], .05, pp.fuel[1]); pg.add(fuelFill);
  const frame = new THREE.Mesh(geoAt(new THREE.BoxGeometry(24, 11, 19), -6, 5.5, 4.6), new THREE.MeshBasicMaterial({ visible: false })); frame.name = 'PadFrame'; pg.add(frame);   // framing incl. the ship on the pad and FB-05 at the unload spot
  // flatbed + boxes
  const fb = phFlatbed(); scene.add(fb);
  const boxes = new THREE.InstancedMesh(new THREE.BoxGeometry(1.4, 1.0, 1.0).translate(0, .5, 0), boxMat, 64); boxes.name = 'CargoBoxes'; boxes.castShadow = true; boxes.count = 0; scene.add(boxes);
  Object.assign(cg3, { rc, pc, pg, ship, astro, fuelFill, fb, boxes, bay });
  cgBind(); stationObjs[PADI] = pg; fitSite(PADI);
}
// read every joint / marker through the alias table (the placeholders above are named like the art, so this is the same path a GLB takes)
const BOXP = { hookY: 1.0 };
function cgBind() {
  const A = CARGO_ALIAS, bp = phBoxProp(), hp = findA(bp, A.boxHook), bb = findA(bp, A.boxBase); BOXP.hookY = hp && bb ? hp.position.y - bb.position.y : 1.0;
  const crane = (root, mast, jib) => { root.updateMatrixWorld(true); const sl = findA(root, A.slew), tr = findA(root, A.trolley), ho = findA(root, A.hoist), hk = findA(root, A.hook), pk = findA(root, A.pick), dp = findA(root, A.drop);
    const wp = (o) => o ? o.getWorldPosition(new THREE.Vector3()) : null, base = root.getWorldPosition(new THREE.Vector3());
    return { root, sl, tr, ho, hk, cable: tr && tr.userData.cable, base, top: wp(sl).y, jib, pick: wp(pk), drop: wp(dp) }; };
  cg3.RC = crane(cg3.rc, CPH.ref.mast, CPH.ref.jib); cg3.PC = crane(cg3.pc, CPH.pad.mast, CPH.pad.jib);
  const fb = cg3.fb, s1 = findA(fb, A.bedSlot1), s2 = findA(fb, A.bedSlot2);
  cg3.slots = [s1 ? s1.position.clone() : new THREE.Vector3(0, 1.2, 0), s2 ? s2.position.clone() : (s1 ? s1.position.clone().add(new THREE.Vector3(...A.bedSlot2Offset)) : new THREE.Vector3(-1.7, 1.2, 0))];
  cg3.wheelR = fb.userData[A.wheelRadius] || 0.5; fb.traverse(o => { if (o.isInstancedMesh && A.wheel.test(o.name)) cg3.wheels = o; });
  cg3.holds = []; for (let i = 1; i <= CG.holdCap; i++) { const h = findA(cg3.ship, A.hold(i)); cg3.holds.push(h ? h.position.clone() : new THREE.Vector3(-3.5, .45, 0)); }
  cg3.pg.updateMatrixWorld(true); const rv = findA(cg3.pg, A.receive), hm = cg3.pg.getObjectByName('Astro_Home');
  cg3.receive = rv.getWorldPosition(new THREE.Vector3()); cg3.home = hm.getWorldPosition(new THREE.Vector3());
}
// ---- per-frame poses (pure functions of S.cg and now)
const _Y = new THREE.Vector3(0, 1, 0), _cq = new THREE.Quaternion(), _cs = new THREE.Vector3(1, 1, 1), _cp = new THREE.Vector3(), _cm = new THREE.Matrix4(), _cv = new THREE.Vector3();
const FBS = { x: 0, z: 0, yaw: 0, v: 0, ph: 'load', wa: 0, wx: null, wz: 0 };
const lerp = (a, b, k) => a + (b - a) * k;
const lerpA = (a, b, k) => { let d = b - a; d = Math.atan2(Math.sin(d), Math.cos(d)); return a + d * k; };
function polar(C, p) { const dx = p.x - C.base.x, dz = p.z - C.base.z; return { a: Math.atan2(-dz, dx), r: clamp(Math.hypot(dx, dz), 1.2, C.jib) }; }
// crane cycle u 0..1: reach the pick (0–.15), lower (.15–.3), lift (.3–.45), slew + trolley to the drop (.45–.7), lower (.7–.85), let go, raise and go home (.85–1)
function cranePose(C, u, P, D, rest) {
  const hi = CPH.hookHi; let a, r, y, carry = false, k;
  const seg = (u0, u1) => fss((u - u0) / (u1 - u0));
  if (u < 0 || u >= 1 || !P) { a = rest.a; r = rest.r; y = hi; }
  else { const p = polar(C, P), d = polar(C, D), py = P.y + BOXP.hookY, dy = D.y + BOXP.hookY;
    if (u < .15) { k = seg(0, .15); a = lerpA(rest.a, p.a, k); r = lerp(rest.r, p.r, k); y = hi; }
    else if (u < .3) { a = p.a; r = p.r; y = lerp(hi, py, seg(.15, .3)); }
    else if (u < .45) { a = p.a; r = p.r; y = lerp(py, hi, seg(.3, .45)); carry = true; }
    else if (u < .7) { k = seg(.45, .7); a = lerpA(p.a, d.a, k); r = lerp(p.r, d.r, k); y = hi; carry = true; }
    else if (u < .85) { a = d.a; r = d.r; y = lerp(hi, dy, seg(.7, .85)); carry = true; }
    else { k = seg(.85, 1); a = lerpA(d.a, rest.a, k); r = lerp(d.r, rest.r, k); y = lerp(dy, hi, Math.min(1, k * 2)); } }
  C.sl.rotation.y = a; C.tr.position.x = r; const drop = C.top - y; C.ho.position.y = -drop; if (C.cable) C.cable.scale.y = Math.max(.01, drop);
  C.hookW = C.hookW || new THREE.Vector3(); C.hookW.set(C.base.x + r * Math.cos(a), y, C.base.z - r * Math.sin(a)); C.u = u;
  return carry;
}
let nBox = 0;
function boxAt(p, yaw = 0) { if (nBox >= 64) return; _cq.setFromAxisAngle(_Y, yaw); cg3.boxes.setMatrixAt(nBox++, _cm.compose(p, _cq, _cs)); }
const stackPos = (i, o = new THREE.Vector3()) => o.set(cg3.RC.pick.x + (i % 2 ? .75 : -.75), Math.floor(i / 4) * 1.0 + .15, cg3.RC.pick.z + ((i >> 1) % 2 ? .55 : -.55));
const bayPos = (i, o = new THREE.Vector3()) => { const b = cg3.PC.drop; return o.set(b.x + ((i % 3) - 1) * 1.6, .25 + Math.floor(i / 12) * 1.0, b.z + (Math.floor(i / 3) % 4 - 1.5) * 1.15); };
function slotW(i, o = new THREE.Vector3()) { return o.copy(cg3.slots[i]).applyMatrix4(cg3.fb.matrixWorld); }
const _pk = new THREE.Vector3(), _dp = new THREE.Vector3(), _hw = new THREE.Vector3();
function fbPoseAt(c, t, o) {
  const f = c.fb; o.ph = f.st;
  if (f.st === 'load' || f.st === 'unload') { const p = f.st === 'load' ? FB.S : FB.U; o.x = p[0]; o.z = p[1]; o.yaw = 0; o.v = 0; return o; }
  const K = f.st === 'out' ? FB.kOut : FB.kBack, P = f.st === 'out' ? FB.pOut : FB.pBack; kinAt(K, (t - f.t0) / 1000, _ka); pathAt(P, _ka[0], o); o.v = _ka[1]; return o;
}
function updCargo() {
  if (!cg3.fb || !FB.kOut) return; const c = S.cg, t = nowMs();
  fbPoseAt(c, t, FBS); const fb = cg3.fb; fb.position.set(FBS.x, 0, FBS.z); fb.rotation.set(0, FBS.yaw, 0); fb.updateMatrixWorld(true);
  if (FBS.wx !== null) { const dx = FBS.x - FBS.wx, dz = FBS.z - FBS.wz; if (Math.hypot(dx, dz) < 20) FBS.wa += (dx * Math.cos(FBS.yaw) - dz * Math.sin(FBS.yaw)) / cg3.wheelR; }   // roll by real distance
  FBS.wx = FBS.x; FBS.wz = FBS.z;
  if (cg3.wheels) { const W = cg3.wheels; fb.userData.wheelPos.forEach((p, i) => { _cq.setFromAxisAngle(_cv.set(0, 0, 1), -FBS.wa); W.setMatrixAt(i, _cm.compose(_cp.set(p[0], p[1], p[2]), _cq, _cs)); }); W.instanceMatrix.needsUpdate = true; }
  // ship
  const s = c.sh, sh = cg3.ship, pp = CPH.pad; let sy = pp.padTop, vis = true;
  if (s.st === 'launch') { const u = clamp((t - s.t0) / (CG.launchSec * 1000), 0, 1); sy += 160 * u * u * u; }
  else if (s.st === 'away') vis = false;
  else if (s.st === 'land') { const u = clamp((t - s.t0) / (CG.landSec * 1000), 0, 1); sy += 160 * (1 - u) ** 3; }
  sh.visible = vis; sh.position.y = sy; sh.updateMatrixWorld(true);
  cg3.fuelFill.scale.y = Math.max(.01, 5.9 * fuelAt(t));
  // astronaut
  const ap = astroPhase(c, t), as = cg3.astro, H = cg3.home, Rv = cg3.receive; let ax, az, ay = 0, ayaw;
  if (c.as.st === 'walk_out' || c.as.st === 'walk_back') { const u = fss((t - c.as.t0) / (CG.walkSec * 1000)), out = c.as.st === 'walk_out'; const A = out ? H : Rv, B = out ? Rv : H;
    ax = lerp(A.x, B.x, u); az = lerp(A.z, B.z, u); ay = .12 * Math.abs(Math.sin(u * Math.PI * 6)); ayaw = Math.atan2(-(B.z - A.z), B.x - A.x); }
  else if (c.as.st === 'ready') { ax = Rv.x; az = Rv.z; ayaw = Math.PI / 2 * -1; if (ap === 'check_in') ay = .05 * Math.sin(t / 90); }   // faces the bed (+z)
  else { ax = H.x; az = H.z; ayaw = Math.PI / 2 * -1; }
  as.position.set(ax, ay, az); as.rotation.y = ayaw;
  // cranes + boxes
  nBox = 0; const RC = cg3.RC, PC = cg3.PC, now = t;
  const restR = { a: polar(RC, RC.pick).a + CPH.ref.rest[0], r: 3 }, restP = { a: polar(PC, PC.drop).a, r: 5 };
  const ready = c.ref.filter(x => x <= now).length;
  for (let i = 0; i < Math.min(ready, 16); i++) boxAt(stackPos(i, _cp));
  let u = -1; if (c.rc) { u = (now - c.rc) / (CG.refLoadSec * 1000); stackPos(ready, _pk); slotW(c.fb.bed, _dp); }
  const carryR = cranePose(RC, u, c.rc ? _pk : null, _dp, restR);
  if (c.rc && u >= 0) boxAt(u < .3 ? _pk : carryR ? _hw.copy(RC.hookW).setY(RC.hookW.y - BOXP.hookY) : _dp);
  for (let i = 0; i < c.fb.bed; i++) boxAt(slotW(i, _cp), FBS.yaw);
  for (let i = 0; i < c.bay; i++) boxAt(bayPos(i, _cp));
  if (vis) for (let i = 0; i < s.hold; i++) boxAt(_cp.copy(cg3.holds[i]).applyMatrix4(sh.matrixWorld));
  let v = -1, P = null;
  if (c.pc.k) { v = (now - c.pc.t0) / ((c.pc.k === 'unload' ? CG.padUnloadSec : CG.holdLoadSec) * 1000);
    if (c.pc.k === 'unload') { slotW(c.fb.bed, _pk); bayPos(c.bay, _dp); } else { bayPos(c.bay, _pk); _dp.copy(cg3.holds[s.hold]).applyMatrix4(sh.matrixWorld); } P = _pk; }
  const carryP = cranePose(PC, v, P, _dp, restP);
  if (P && v >= 0) boxAt(v < .3 ? _pk : carryP ? _hw.copy(PC.hookW).setY(PC.hookW.y - BOXP.hookY) : _dp);
  cg3.boxes.count = nBox; cg3.boxes.instanceMatrix.needsUpdate = true; if (nBox) cg3.boxes.computeBoundingSphere();   // culled with the camera off-site
  window.__ps3d.cargoFrame = { boxes: nBox, astro: ap, fb: FBS.ph, v: +FBS.v.toFixed(2) };
}
let cargoRoadMesh = null;
function buildCargoRoad() {         // Art's haul-road strip tiles (same as the Mine↔Refinery road), lanes z 13 / 22; flat temp tiles if the strip is not in
  if (cargoRoadMesh) scene.remove(cargoRoadMesh);
  const R0 = CPH.road, M = (i) => new THREE.Matrix4().makeTranslation(R0.x0 + R0.tile * i, 0, CPH.lanes.out);
  if (roadSeg) { const im = new THREE.InstancedMesh(roadSeg.geo, roadSeg.mat, R0.n); for (let i = 0; i < R0.n; i++) im.setMatrixAt(i, M(i).multiply(roadSeg.m)); im.receiveShadow = true; cargoRoadMesh = im; }
  else { const g = new THREE.PlaneGeometry(R0.tile, 4.6).rotateX(-Math.PI / 2).translate(R0.tile / 2, .03, 0), im = new THREE.InstancedMesh(g, new THREE.MeshStandardMaterial({ color: 0x55575c, roughness: .95 }), R0.n * 2);
    for (let i = 0; i < R0.n; i++) { im.setMatrixAt(2 * i, M(i)); im.setMatrixAt(2 * i + 1, M(i).premultiply(new THREE.Matrix4().makeTranslation(0, 0, CPH.lanes.back - CPH.lanes.out))); } im.receiveShadow = true; cargoRoadMesh = im; }
  cargoRoadMesh.computeBoundingSphere(); cargoRoadMesh.name = 'CargoRoad'; scene.add(cargoRoadMesh);
}
function cgMakeDue() {}   // (boxes are made inside settleTo at the exact dump time)
function cargoState() { const c = S.cg, t = nowMs(); return { made: c.made, sold: c.sold, launches: c.launches, earned: +c.earned.toFixed(2), refReady: c.ref.filter(x => x <= t).length, refSealing: c.ref.filter(x => x > t).length,
  refCrane: c.rc ? 'loading' : 'idle', bed: c.fb.bed, flatbed: c.fb.st, astro: astroPhase(c, t), padCrane: c.pc.k || 'idle', bay: c.bay, ship: c.sh.st, hold: c.sh.hold, fuel: +fuelAt(t).toFixed(3),
  simT: c.t, tripOut: FB.kOut && +FB.kOut.T.toFixed(2), tripBack: FB.kBack && +FB.kBack.T.toFixed(2), last: CG_LOG.slice(-6).map(e => e.e) }; }
buildCargoRoute(); buildCargoProps(); buildCargoRoad();

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
  const r = tapDeposit(best);
  if (r === 'queued') pop('Queued for the next load', x, y - 20, 'info');
  if (pointBeat === 'deposit') pointerDone = true;
}

// ===== upgrade sheet (drag up/down, springs to open or closed)
const sheet = $('sheet'), grab = $('grab'), PEEK = 46;
let sheetOpen = false, sheetDrag = null;
const closedY = () => sheet.offsetHeight - PEEK - (parseFloat(getComputedStyle(sheet).paddingBottom) || 0);   // panel runs flush to the bottom edge; peek sits above the safe-area inset
function setSheet(open) { sheetOpen = open; document.body.classList.toggle('sheet-open', open); sheet.classList.remove('dragging'); sheet.style.transform = `translateY(${open ? 0 : closedY()}px)`; if (open && pointBeat === 'upgrade') pointerDone = true; }
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
const bDrill = $('bDrill'), bRover = $('bRover'), bChute = $('bChute');
const meterKeys = {};
function meter(id, n, on) { const k = n + ':' + on; if (meterKeys[id] === k) return; meterKeys[id] = k; const el = $(id);
  if (el.children.length !== n) el.innerHTML = '<i></i>'.repeat(n); [...el.children].forEach((x, i) => x.classList.toggle('on', i < on)); }
function sheetUI() {
  const c = drillCost(), ok = canPay(c);
  $('dLvl').textContent = 'LV ' + S.drill; meter('dMeter', 10, S.drill >= 50 ? 10 : (S.drill - 1) % 10 + 1);   // segments = progress through the current 10-level tier
  $('dGain').textContent = `${fmt(loadValue())} per load → ${fmt(loadValue(S.drill + 1))}`;
  bDrill.textContent = ok ? fmt(c) : 'Need ' + fmt(c); bDrill.className = ok ? '' : 'need'; bDrill.parentNode.classList.toggle('ok', ok);
  const cc = chuteCost(), cmax = S.chute >= CFG.chuteMax, cok = !cmax && canPay(cc);
  $('chLvl').textContent = 'LV ' + S.chute; meter('chMeter', 10, cmax ? 10 : (S.chute - 1) % 10 + 1);
  $('chGain').textContent = cmax ? `Fill ${Math.round(fillSec())} s · Max` : `Fill ${Math.round(fillSec())} s → ${Math.round(fillSec(S.chute + 1))} s`;
  if (cmax) { bChute.textContent = 'Max'; bChute.className = 'max'; } else { bChute.textContent = cok ? fmt(cc) : 'Need ' + fmt(cc); bChute.className = cok ? '' : 'need'; }
  bChute.parentNode.classList.toggle('ok', cok);
  $('rLvl').textContent = S.rovers + '/' + CFG.roverMax; meter('rMeter', CFG.roverMax, S.rovers);
  $('rGain').textContent = 'HT-04 haul truck · more trucks soon'; bRover.textContent = ''; bRover.className = 'off';
  bRover.parentNode.hidden = true; bRover.parentNode.classList.toggle('ok', false);
  $('sum').textContent = `Drill Lv ${S.drill} · Chute Lv ${S.chute}`;
  $('canDot').hidden = !(ok || cok);
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
  const r = bDrill.getBoundingClientRect(); pop('Drill Lv ' + S.drill, r.left + r.width / 2, r.top - 8, 'info');
  logU('upgrade', `Drill upgraded to Lv ${S.drill}`);
  window.__ps3d.buys = (window.__ps3d.buys || 0) + 1;
});
bindBuy(bChute, () => {
  const c = chuteCost(); if (S.chute >= CFG.chuteMax || !canPay(c)) return;
  const t = nowMs(); settleTo(t, null); const k = S.tk;
  if (!k.dep) { k.add = fillAt(t); k.c0 = t; }          // rebase so the bed level never jumps; the new rate applies from now
  pay(c); S.chute++; save(); sheetUI(); hud();
  const r = bChute.getBoundingClientRect(); pop('Chute Lv ' + S.chute, r.left + r.width / 2, r.top - 8, 'info');
  logU('upgrade', `Chute Feed Rate Lv ${S.chute}: fills in ${Math.round(fillSec())} s`);
  window.__ps3d.buys = (window.__ps3d.buys || 0) + 1;
});
const TRUCK_SALE = false;   // extra trucks come later: the button is hidden and a stray click can't buy
bindBuy(bRover, () => { if (!TRUCK_SALE) return; });

// conveyor strip on the bar creeps (CSS background-position) only while the truck fills and the sheet is closed
let convOn = null;
function updConveyor() { const on = TS.ph === 'fill' && TS.fill < 1 && !sheetOpen && !(sheetDrag); if (on !== convOn) { convOn = on; sheet.classList.toggle('run', on); window.__ps3d.conveyor = on; } }

// ===== Earth Coms (Art's kit, art/ui/earth_coms): bubble + incoming-call toast + panel (Task / Updates / Calls) + call view.
// Tutorial calls ring until opened; story calls time out after 8 s and leave a missed-call badge. Motion constants mirror MOTION.md.
const EVE_BEATS = [
  { id: 'mine_first_view', tut: true, point: 'deposit', lines: ["Moonbase, this is Eve at Earth Coms. Good to hear you made it. Your truck is filling under the chute.",
    "Tap the glowing deposit and the drill drops a rich load into the bed. Over."] },
  { id: 'first_deposit', tut: false, point: null, lines: ["Rich load, nice. Once that truck is full it hauls to the Refinery and pays as the bed tips. Over."] },
  { id: 'upgrade_ready', tut: true, point: 'upgrade', lines: ["You've got the cash for an upgrade. Bigger mine, bigger loads. Tap Upgrade."] },
];
const EVE_TRIG = {
  mine_first_view: () => S.site === MINE && coverGone && Math.abs(camX - MX) < 1,
  first_deposit: () => S.dep >= 1,
  upgrade_ready: () => S.dep >= 1 && canPay(drillCost()) && !sheetOpen,
};
const ECM = { toastIn: 420, tapOut: 160, typeStart: 420, charMs: 30, commaMs: 120, stopMs: 240, closeCrt: 120, closeSlide: 260, toastTimeout: 8000, rmFade: 150 };
const ecRoot = $('ec'), ecToast = $('ecToast'), ecPanel = $('ecPanel'), ecTxt = $('ecTxt'), ecTx = $('ecTx'), ecBubble = $('ecBubble'), ecBadge = $('ecBadge');
const pointEl = $('point'), POINT_UP_H = 40;
if (matchMedia('(prefers-reduced-motion: reduce)').matches || Q.get('rm') === '1') ecRoot.classList.add('ec-reduced');
const ecReduced = () => ecRoot.classList.contains('ec-reduced');
const EC = { ring: null, call: null, lines: [], li: 0, typing: 0, toastT: 0, full: '' };
let pointerDone = false, pointBeat = null;
const hudDim = (on) => hudEl.classList.toggle('ec-hud-dim', on);
const ICO = { call: '<svg viewBox="0 0 16 16"><path d="M4 3h2l1 3-1.5 1a7 7 0 0 0 3.5 3.5L10 9l3 1v2a1 1 0 0 1-1 1A10 10 0 0 1 3 4a1 1 0 0 1 1-1z"/></svg>',
  truck: '<svg viewBox="0 0 16 16"><path d="M2 5h7v6H2zM9 7h3l2 2v2H9z"/><circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/></svg>',
  upgrade: '<svg viewBox="0 0 16 16"><path d="M8 13V3M4 7l4-4 4 4"/></svg>' };
const esc = (s) => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const ago = (t) => { const m = Math.max(0, Math.round((nowMs() - t) / 60000)); return m < 1 ? 'now' : m < 60 ? m + 'm' : Math.round(m / 60) + 'h'; };
function logU(type, text) { S.log.unshift({ type, text, at: nowMs() }); if (S.log.length > 20) S.log.length = 20; if (ecPanel.classList.contains('is-open')) renderUpd(); }
function addCall(id, missed) { S.calls.unshift({ id, at: nowMs(), missed: !!missed }); if (S.calls.length > 20) S.calls.length = 20; renderCalls(); }
function setMissed(n) { S.missed = n; ecBadge.dataset.count = n; ecBadge.textContent = n || '';
  const tb = ecPanel.querySelector('.ec-tab[data-tab="calls"] .ec-badge'); tb.dataset.count = n; tb.textContent = n || ''; }
function renderTask() {
  const g = !S.dep ? ['Send a rich load', 'Tap a glowing deposit', S.dep, 1] : S.loads < 3 ? ['Haul 3 loads to the Refinery', 'Loads delivered', S.loads, 3]
    : S.chute < 3 ? ['Upgrade the Chute Feed Rate to Lv 3', 'Chute level', S.chute, 3] : ["Fill the ship's tanks", 'Oxygen + methane loads', 0, 3];
  $('ecTask').innerHTML = `<div class="ec-kicker">CURRENT GOAL</div><div class="ec-goal">${esc(g[0])}</div><div class="ec-prog"><span>${esc(g[1])}</span><b>${Math.min(g[2], g[3])}/${g[3]}</b></div>`
    + `<div class="ec-bar"><i style="width:${Math.round(100 * Math.min(1, g[2] / g[3]))}%"></i></div><div class="ec-tip">A full truck leaves on its own. Rich loads tapped while it's away drop in when it's back.</div>`;
}
function renderUpd() { $('ecUpd').innerHTML = S.log.length ? S.log.map(u => `<li><span class="ec-ico"${u.type === 'upgrade' ? ' data-type="unlock"' : ''}>${ICO[u.type] || ICO.truck}</span><span>${esc(u.text)}</span><time>${ago(u.at)}</time></li>`).join('') : '<li><span>No updates yet.</span></li>'; }
function renderCalls() { $('ecCalls').innerHTML = S.calls.map(c => { const b = EVE_BEATS.find(x => x.id === c.id); if (!b) return '';
  return `<li><span class="ec-ico">${ICO.call}</span><span>${c.missed ? 'Missed call' : 'Eve'}<span class="ec-sub">Eve · ${ago(c.at)} ago</span></span><button class="ec-replay" data-beat="${esc(c.id)}">▶ REPLAY</button></li>`; }).join('') || '<li><span>No calls yet.</span></li>'; }
function showTab(t) {
  ecPanel.querySelectorAll('.ec-tab').forEach(b => b.setAttribute('aria-selected', b.dataset.tab === t || (t === 'call' && b.dataset.tab === 'calls')));
  ecPanel.querySelectorAll('.ec-view').forEach(v => v.classList.toggle('is-on', v.dataset.view === t));
  if (t === 'task') renderTask(); if (t === 'updates') renderUpd(); if (t === 'calls') renderCalls();
}
function ecResetUI() { clearTimeout(EC.toastT); clearTimeout(EC.typing); ecToast.className = 'ec-toast'; ecPanel.className = 'ec-panel'; ecBubble.classList.remove('is-ringing'); ecTxt.textContent = ''; ecTx.textContent = 'STANDING BY'; }
function ecRing(b) {
  ecResetUI(); EC.ring = b; void ecToast.offsetWidth; ecToast.classList.add('is-in'); hudDim(true); ecBubble.classList.add('is-ringing');
  if (b.tut) { ecToast.dataset.tutorial = ''; ecBubble.dataset.tutorial = ''; return; }     // tutorial: no timeout, pulses until opened
  delete ecToast.dataset.tutorial; delete ecBubble.dataset.tutorial;
  S.eve.push(b.id); save();                                                                   // story beat: rings once, never repeats
  EC.toastT = setTimeout(() => { if (EC.ring !== b) return; ecToast.classList.replace('is-in', 'is-out'); setTimeout(() => hudDim(false), ECM.closeSlide); ecBubble.classList.remove('is-ringing');
    EC.ring = null; setMissed(S.missed + 1); addCall(b.id, true); save(); }, ECM.toastTimeout);
  window.__ps3d.eveShown = (window.__ps3d.eveShown || []).concat(b.id);
}
function ecAnswer(b = EC.ring) {
  if (!b) return; clearTimeout(EC.toastT); EC.ring = null; EC.call = b; EC.lines = b.lines; EC.li = 0;
  ecBubble.classList.remove('is-ringing'); showTab('call');
  if (ecToast.classList.contains('is-in')) { ecToast.classList.replace('is-in', 'is-tapped'); setTimeout(() => hudDim(false), ECM.tapOut); } else hudDim(false);
  ecPanel.classList.remove('is-closing', 'is-out'); ecPanel.classList.add('is-open');
  if (b.tut && !S.eve.includes(b.id)) { S.eve.push(b.id); addCall(b.id, false); save(); window.__ps3d.eveShown = (window.__ps3d.eveShown || []).concat(b.id); }
  setTimeout(() => sayLine(EC.lines[0]), ecReduced() ? ECM.rmFade : ECM.typeStart);
}
function sayLine(s) {
  if (!EC.call || s == null) return; EC.full = s; ecTxt.textContent = ''; ecPanel.classList.remove('is-waiting');
  if (ecReduced()) return lineDone();
  ecPanel.classList.add('is-talking'); ecTx.textContent = 'TRANSMITTING'; let i = 0;
  const step = () => { ecTxt.textContent = s.slice(0, ++i); if (i >= s.length) return lineDone(); const c = s[i - 1];
    EC.typing = setTimeout(step, /[.!?]/.test(c) && s[i] === ' ' ? ECM.stopMs : c === ',' ? ECM.commaMs : ECM.charMs); };
  step();
}
function lineDone() { clearTimeout(EC.typing); ecTxt.textContent = EC.full; ecPanel.classList.remove('is-talking'); ecPanel.classList.add('is-waiting'); ecTx.textContent = 'STANDING BY'; }
function ecHangUp() {
  const b = EC.call; clearTimeout(EC.typing); EC.call = null;
  ecPanel.classList.remove('is-talking', 'is-waiting'); ecPanel.classList.add('is-closing');
  setTimeout(() => { ecPanel.classList.remove('is-open'); ecPanel.classList.add('is-out'); }, 0);
  setTimeout(() => { if (!EC.call && !EC.ring) ecResetUI(); }, (ecReduced() ? ECM.rmFade : ECM.closeCrt + ECM.closeSlide) + 30);
  if (b && b.point) { pointBeat = b.point; pointerDone = false; if (b.point === 'deposit' && !deposits.some(d => !d.claimed)) spawnDeposit('Dep_02'); }
}
function ecOpen(tab) { clearTimeout(EC.toastT); EC.ring = null; ecToast.className = 'ec-toast'; hudDim(false); ecBubble.classList.remove('is-ringing');
  showTab(tab || 'task'); ecPanel.className = 'ec-panel is-open'; }
const ecIsOpen = () => ecPanel.classList.contains('is-open');
ecBubble.addEventListener('click', (e) => { e.stopPropagation(); EC.ring ? ecAnswer() : ecIsOpen() ? ecHangUp() : ecOpen('task'); });
ecToast.addEventListener('click', (e) => { e.stopPropagation(); ecAnswer(); });
ecRoot.addEventListener('pointerdown', (e) => e.stopPropagation());
ecPanel.addEventListener('click', (e) => {
  e.stopPropagation();
  const tb = e.target.closest('.ec-tab'); if (tb) { showTab(tb.dataset.tab); if (tb.dataset.tab === 'calls') { setMissed(0); save(); } return; }
  const rp = e.target.closest('.ec-replay'); if (rp) { const b = EVE_BEATS.find(x => x.id === rp.dataset.beat); if (b) ecAnswer(b); return; }
  if (e.target.closest('.ec-close')) return ecHangUp();
  if (!ecPanel.querySelector('.ec-view[data-view="call"]').classList.contains('is-on')) return;
  if (ecPanel.classList.contains('is-talking')) return lineDone();
  if (++EC.li < EC.lines.length) return sayLine(EC.lines[EC.li]);
  ecHangUp();
});
let ecSy = null; ecPanel.addEventListener('touchstart', e => ecSy = e.touches[0].clientY, { passive: true });
ecPanel.addEventListener('touchend', e => { if (ecSy !== null && ecSy - e.changedTouches[0].clientY > 40) ecHangUp(); ecSy = null; });
document.addEventListener('pointerdown', (e) => { if (ecIsOpen() && !e.target.closest('.ec-panel, .ec-bubble, .ec-toast') && e.target !== canvas) ecHangUp(); });
setMissed(S.missed); renderCalls();
// the 3D view slides down by the panel's height while it's open (setViewOffset), eased 300 ms
const VS = { cur: 0, from: 0, to: 0, t0: 0 };
function updViewShift() {
  let want = 0; if (ecIsOpen()) { const r = ecPanel.getBoundingClientRect(); want = Math.round(Math.max(r.height, ecPanel.offsetHeight)); }
  const now = performance.now();
  if (want !== VS.to) { VS.from = VS.cur; VS.to = want; VS.t0 = now; }
  const dur = ecReduced() ? 1 : 300, u = clamp((now - VS.t0) / dur, 0, 1), k = VS.to > VS.from ? 1 - Math.pow(2, -10 * u) : u * u * u;
  VS.cur = u >= 1 ? VS.to : VS.from + (VS.to - VS.from) * k;
  if (VS.cur > .5) camera.setViewOffset(W, H, 0, -VS.cur, W, H); else if (camera.view && camera.view.enabled) camera.clearViewOffset();
  window.__ps3d.viewShift = Math.round(VS.cur);
}
function updEve() {
  if (!EC.ring && !EC.call && !ecIsOpen()) for (const b of EVE_BEATS) if (!S.eve.includes(b.id) && EVE_TRIG[b.id]()) { ecRing(b); break; }
  let p = null;
  if (pointBeat && !pointerDone) {
    if (pointBeat === 'deposit' && S.site === MINE) { const d = deposits.find(d => !d.claimed); if (d) {
      const h = depTapR(d); p = _pt; p.x = h.x; p.l = 'TAP HERE'; p.up = true;
      const lim = nameEl.getBoundingClientRect().top - POINT_UP_H - 12; p.y = Math.min(h.y + h.glow + 6, lim); } }
    if (pointBeat === 'upgrade') { const r = grab.getBoundingClientRect(); p = _pt; p.x = r.left + r.width / 2; p.y = r.top + 4; p.l = 'UPGRADE'; p.up = false; }
  }
  pointEl.style.display = p ? 'block' : 'none';
  if (p) { pointEl.style.left = p.x + 'px'; pointEl.style.top = p.y + 'px'; if (pointEl.firstChild.textContent !== p.l) pointEl.firstChild.textContent = p.l; if (pointEl._up !== p.up) { pointEl._up = p.up; pointEl.classList.toggle('up', p.up); } }
}

// ===== away catch-up: the truck loop is replayed from its timestamps; loads that tipped while away pay 50%, capped at 4 h
const awayEl = $('away');
$('awayOk').addEventListener('click', () => awayEl.classList.remove('on'));
awayEl.addEventListener('pointerdown', (e) => e.stopPropagation());
function catchUp(card) {
  const now = nowMs(), el = (now - S.rt) / 1000;
  if (!(el > 0)) { S.rt = now; window.__ps3d.lastAway = { sec: Math.round(el), X: 0 }; return 0; }   // clock set backward: nothing
  const acc = { base: 0, rich: 0, n: 0, full: el < CFG.offlineAfterSec }, capEnd = S.rt + CFG.offlineCapSec * 1000;
  if (now > capEnd) { settleTo(capEnd, acc); shiftTk(now - capEnd); } else settleTo(now, acc);   // past the cap the loop just resumes from where it stood
  S.rt = now; save();
  const X = acc.base + acc.rich + (acc.cargo || 0);
  if (card && !acc.full && Math.floor(X) >= 1) { $('awayAmt').textContent = '+' + fmt(X); awayEl.classList.add('on'); clearTimeout(catchUp.t); catchUp.t = setTimeout(() => awayEl.classList.remove('on'), 9000); }
  window.__ps3d.lastAway = { sec: Math.round(el), X: +X.toFixed(2), loads: acc.n, cargo: +(acc.cargo || 0).toFixed(2), full: acc.full };
  return X;
}
function resync() {                   // bring the loop up to now before anything reads or draws it (frozen page, slow resume, QA reads)
  if (document.hidden) return; const t = nowMs(); if (t < S.rt - 1000) { S.rt = t; return; }
  if ((t - S.rt) / 1000 > 60) catchUp(true); else { settleTo(t, null); S.rt = t; }
}
for (const ev of ['resume', 'pageshow', 'focus']) (ev === 'resume' ? document : window).addEventListener(ev, resync);   // iOS freeze/thaw and bfcache restores
document.addEventListener('visibilitychange', () => {
  if (document.hidden) save(); else { catchUp(true); clock.getDelta(); }
});
addEventListener('pagehide', save);

// ===== loop + ?dev=1 readout (fps, min fps over last 5 s, draws, tris)
const devEl = $('dev'); devEl.hidden = !DEV; if (DEV) devEl.textContent = 'measuring…';
const clock = new THREE.Clock(); let frames = 0, acc = 0, fps = 0, saveT = 0, uiT = 0, time = 0; const hist = [];
renderer.info.autoReset = true;
function frame() {
  requestAnimationFrame(frame);
  const dt = Math.min(clock.getDelta(), document.hidden ? 0.1 : 0.25), gdt = dt * SPD; time += gdt; window.__ps3d.frames = (window.__ps3d.frames || 0) + 1;
  const now = nowMs();
  if (now < S.rt - 1000) S.rt = now;                              // clock went backward mid-session: credit nothing
  if (!document.hidden) { if ((now - S.rt) / 1000 > 60) catchUp(true); else { settleTo(now, null); S.rt = now; } }   // frozen page without a visibilitychange: away rules
  if (!drag) camX += (target - camX) * (1 - Math.exp(-dt * 9));
  updFocus(); updViewShift(); placeCamera();
  updCargo();
  updTruck();                         // poses the truck + sets its clips, then its mixer applies them this frame
  if (tMixer) tMixer.update(gdt);
  if (mixer) mixer.update(gdt);
  updOperator(gdt);
  for (const m of stationMixers) m.update(gdt);
  updFillArc();
  updDeposits(gdt, time); updQueued(); updChunks(dt); updFx(dt); updTiers(dt);
  updEve(); updConveyor();
  uiT += dt; if (uiT > .1) { uiT = 0; hud(); sheetUI(); }
  saveT += dt; if (saveT > CFG.saveEvery) { saveT = 0; save(); }
  renderer.render(scene, camera);
  if (DEV) {
    frames++; acc += dt;
    if (acc >= 0.5) { fps = frames / acc; hist.push([performance.now(), fps]); frames = 0; acc = 0;
      while (hist.length && performance.now() - hist[0][0] > 5000) hist.shift();
      const mn = Math.min(...hist.map(h => h[1]));
      devEl.textContent = `${fps.toFixed(0)} fps · min5s ${mn.toFixed(0)} · ${renderer.info.render.calls} draws · ${(renderer.info.render.triangles / 1000).toFixed(1)}k tris · ${TS.ph}`;
      Object.assign(window.__ps3d, { fps, min5: mn, calls: renderer.info.render.calls, tris: renderer.info.render.triangles });
    }
  }
}
Object.defineProperties(window.__ps3d, Object.getOwnPropertyDescriptors({ renderer, scene, camera, rigScaleAt: rigScale, fxStep: updFx, tierStep: updTiers, get tierList() { return tiers; }, EVE_BEATS,
  get eveId() { return (EC.call || EC.ring || {}).id; }, get ec() { return { ring: EC.ring && EC.ring.id, call: EC.call && EC.call.id, open: ecIsOpen(), missed: S.missed, dim: hudEl.classList.contains('ec-hud-dim'), li: EC.li }; },
  ecAnswer: () => ecAnswer(), ecHangUp, ecOpen, sparks, S, CFG, goSite, STATIONS, deposits, spawnDeposit, catchUp, settleTo, tapDeposit, save, toScreen, drillCost, chuteCost, rate, fmt, depTapR, fillSec, fillAt, loadValue,
  buildRoute, MK, poseNow: () => { resync(); updTruck(); updCargo(); if (tMixer) tMixer.update(0); },
  get cargo() { return cargoState(); }, shiftTk, cg3, FB, CPH, CARGO_ALIAS, get cargoLog() { return CG_LOG.slice(); },
  warpTo: (t) => { if (t > nowMs()) { if (HOLD !== null) HOLD = t; else WARP += t - nowMs(); settleTo(t, null); S.rt = nowMs(); } },
  hold: (on) => { if (on && HOLD === null) HOLD = rawMs(); else if (!on && HOLD !== null) { WARP += HOLD - rawMs(); HOLD = null; } return HOLD; }, TS, truckState: TS, poseAt, R, TV, RMK, get wheel() { return { ang: WH.a, dist: WH.d }; }, OP, CREW, SITECAM, tap, focusTier, FOCT, THREE, popXY, SPD, nowMs,
  get focus() { return { i: FOC.i, w: +FOC.w.toFixed(3), ph: FOC.ph, q: FOC.q.length, to: FOC.to && FOC.to.name, t: FOC.i < 0 ? 0 : +((performance.now() - FOC.seg0) / 1000).toFixed(2) }; },
  get stationLoops() { return stationMixers.flatMap(m => m._actions.map(a => a.getClip().name + ':' + (a.loop === THREE.LoopPingPong ? 'pingpong' : a.loop === THREE.LoopRepeat ? 'repeat' : a.loop))); },
  get camX() { return camX; }, get coverGone() { return coverGone; }, get eveOpen() { return ecIsOpen(); }, get cashTarget() { return cashTarget().id; }, get sheetOpen() { return sheetOpen; }, setSheet }));
buildRoute();
if (hadRt) catchUp(true); else S.rt = nowMs();      // credit time away since the last save
hud(); sheetUI();
loadRig(); loadTruck(); loadOperator();
frame();
