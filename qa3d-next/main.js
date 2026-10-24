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
  fill0: 120, chuteMul: 0.80, fillFloor: 15, chuteMax: 11,   // fill s at Lv1; Chute Feed Rate ×0.80/level (Director 20:58 B8); 15 s floor (reached at Lv11 = max)
  chuteCost0: 10, chuteCostGrowth: 1.5,                      // Director 20:58 B8: $10, ×1.5 per level
  load0: 12, loadPerLvl: 6,             // base load value: fixed $ per load ($12 at drill Lv1, +$6 per drill level); independent of the fill time, so Chute Feed Rate = more loads/h at the same value
  richFill: 0.25, richBonus: 8, richPayDelay: 1.0,            // deposit tap: +25% bed (tweened over the 1 s truck_load_rich), bonus pays ~1 s later
  roverBonus: 8, roverMax: 2, roverCost: 60,
  crew0: 4,                             // starting crew; the Mine operator (Operator_Deck) is one of them
  depositMax: 2, depositEvery: 8,
  offlineRate: 0.5, offlineCapSec: 4 * 3600, awayCardMin: 5, offlineAfterSec: 300,   // Director 10/23: the 50% cut + away card only after 5 min away; shorter locks catch up at full rate
  saveEvery: 3,
  hallDoor: { clip: 'hall_door_open', openSec: 1.2 },   // Director 20:58: open once and stay open; longer clips (8c9cee7 3.6 s loop) use 0–openSec
  // He-3 cargo loop (Director 10/23 spec). ALL numbers below are PLACEHOLDERS pending Director sign-off (see the cargo note in the commit report)
  // Director 20:34: boxValue 36 (full hold $360), fuel 180 s, away 600 s, launch/land 8 s, bay 12, pallet 8; partial launch from the Launch button
  cargo: { sealSec: 4, perTrip: 2, refLoadSec: 6, padUnloadSec: 6, checkSec: 2, walkOutSec: 4.0, walkBackSec: 4.4, holdLoadSec: 5, bayCap: 12, holdCap: 10, palletCap: 8,
           fuelFillSec: 180, launchSec: 8, awaySec: 600, landSec: 8, boxValue: 36 },
  // music (Director 20:35): Every Day Stuff sources CC0 tracks, Jacob picks; list file names found in qa3d/audio/music/ here. Empty = silent.
  music: { dir: 'audio/music/', tracks: ['outer_space_loop.mp3', 'space_flight.mp3', 'devonair.mp3', 'freame.mp3'],   // rotates; outer_space_loop = main track (Jacob 20:56)
           vol: 0.28, duckTo: 0.35, dwellSec: 150, xfadeSec: 4 },
  // Eve stays text-only (no TTS). Optional recorded line audio: { beatId: ['file_for_line_0.mp3', null, …] } under audio/eve/; plays only if listed here.
  eveVoice: { dir: 'audio/eve/', lines: {} },
};
const CAM = { halfW: 7.5, elev: 18, lookY: 2.5 };   // fixed camera: ~15 m wide in portrait, 18° down

const Q = new URLSearchParams(location.search);
// ---- Swappable art (pending Director review). The filename carries the commit hash, so it is also the cache-buster.
const MINE_GLB = '../qa3d-next/models/mine_ef45f6f1.glb?v=ef45f6f1';   // Art 449757b (Director 01:18): painted tire tracks, mid-gray ore/deposits (100,97,92), 14 draws; was cc084a9b
//  // Art 12bdb4a (Director 23:10): Deposit_01/_02 split into their own fadeable nodes (look unchanged), own copy under qa3d-next/; was 'models/mine_2123a050.glb'
//  // Art a4f93eb (Director 21:17): ore patches + veins baked, 2-lane haul road, fewer Path_* legs; previous: 'models/mine_219e774.glb'
const REFINERY_GLB = '../qa3d-next/models/refinery_93c44166.glb?v=93c44166';   // Art d6389a7 (Director 00:51): 13 draws, conveyors merged into skinned Base_Paint, sizer_spin, dump_dust opacity_curve, white/cyan posts, painted ruts; was b45b4649
//   // Art f4d4a2c (Director 21:17): dump bay, r 4.5 U-turn at x −3.5, 3.5 m reverse, dump_dust; previous: 'models/refinery_bb5eed2.glb'
const TURN_SPEED = 4.0;   // m/s through curves (Mine 4.5 m arcs on Path_Out_*/Path_Ret_*, Refinery U-turn Truck_Path_01..07); straights stay TV.v = 8.33
const TURN_R_MAX = 25;    // m: any stretch turning tighter than this radius counts as a curve
const TURN_ACC = 2.5;     // m/s²: max acceleration AND braking anywhere (pull-away, curves, stops, reverse moves) — Playtester B2/B3 20:58
const TURN_GAP = 22;      // m: a straight shorter than this between two bends holds TURN_SPEED through both (Director 20:58 B4)
const ROAD_LAST_SCALE = 1.0;   // haul road: 10 full 8 m tiles + a last tile scaled along X only. 1.0 = 11 full tiles ending at world x 274 (Art's trimmed Refinery road);
                               // 0.75 = ends at x 272, where Refinery 0358ffa's own road starts
const DEV = Q.get('dev') === '1';
const SAVEKEY = DEV ? 'planetstack-qa3d-next-dev' : 'planetstack-qa3d-next';   // qa3d-next: own save so it never touches /qa3d/'s save on the same origin
if (Q.has('fresh')) try { localStorage.removeItem(SAVEKEY); } catch (e) {}
const SPD = Math.max(1, Math.min(100, +Q.get('speed') || 1)), T0 = Date.now();   // ?speed=N (QA only): the game clock (truck loop, fill, deposits, 3D anims) runs N×
let WARP = 0;   // QA only (__ps3d.warpTo): jumps the game clock forward as live play (no offline rate)
let HOLD = null; // QA only (__ps3d.hold): freezes the game clock so slow test boxes can screenshot an exact pose
const rawMs = () => (SPD === 1 ? Date.now() : T0 + (Date.now() - T0) * SPD) + WARP;
const nowMs = () => (HOLD !== null ? HOLD : rawMs());
const S = { site: 1, money: CFG.startMoney, crystals: CFG.startCrystals, drill: 1, chute: 1, rovers: 1, dep: 0, loads: 0, eve: [], calls: [], log: [], missed: 0, tk: null, pend: [], trips: [], set: { music: true }, rt: nowMs() };
let hadRt = false;
try { const sv = JSON.parse(localStorage.getItem(SAVEKEY) || '{}'); hadRt = sv.rt > 0;
  if (hadRt && !('chute' in sv) && sv.site >= 2) sv.site++;   // 11:12 and older saves: the Refinery slot (index 2) shifts the later stations by one
  Object.assign(S, sv); } catch (e) {}
for (const k of ['eve', 'calls', 'log', 'pend', 'trips']) if (!Array.isArray(S[k])) S[k] = [];
if (!(S.chute >= 1)) S.chute = 1; if (!(S.loads >= 0)) S.loads = 0; if (!(S.missed >= 0)) S.missed = 0;
if (!(S.rt > 0)) S.rt = nowMs();
if (!S.set || typeof S.set !== 'object') S.set = { music: true };
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
const fillSec = (lv = S.chute) => Math.max(CFG.fillFloor, CFG.fill0 * CFG.chuteMul ** (lv - 1));   // Lv2 96 s, Lv5 49 s, Lv10 16.1 s, Lv11 15 s (floor)
const chuteCost = () => Math.round(CFG.chuteCost0 * CFG.chuteCostGrowth ** (S.chute - 1));
// ORE/MIN (Director 20:58): real throughput over the full cycle = ore per load / (fill + trip incl. reverse/dump/settle) — ≈4 at Lv1; drill and chute upgrades move it
const oreMin = (dl = S.drill, cl = S.chute) => (loadValue(dl) / CFG.oreValue) * 60 / (fillSec(cl) + (R.tl ? R.tl.trip : 60));
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
    loops: ['Beacon_Lights_Blink', 'conveyor_fuel_run', 'conveyor_he3_run', 'kiln_spin', 'sizer_spin'], onLoad: (o, mx, g) => refineryLoaded(o, mx, g) },
  { i: 4, url: 'models/dock_tankfarm_fd286b9.glb?v=7959ae74', loops: ['Beacon_Lights_Blink', 'crane_gantry_move'], onLoad: (o) => {   // Cam_Target (12, 6, 2), frame_w 64; dock door stays shut
    const pl = o.getObjectByName('Pipe_LaunchPad'); if (pl) DOCK.pipeLaunchPad = pl.position.toArray(); window.__ps3d.dock = DOCK; } },
  { i: 6, url: '../qa3d-next/models/shipyard_bcbd0934.glb?v=bcbd0934', loops: ['Beacon_Lights_Blink'], onLoad: (o, mx, g) => hallDoor(mx, g) },   // Shipyard f2ebfe6 (Director 00:25 cleared; own Cam_Target (7.7, 23.5, 84.55) frame_w 100). Its crane_jib_swing is still the old 6 s idle loop (snaps), so the jib stays held in its GLB rest pose until the ship-build Shipyard bcbd0934 replaces it
];
// Shipyard hall door (Director 20:58): plays hall_door_open once and holds it open (LoopOnce + clampWhenFinished). 2d57b95's clip is 1.2 s;
// 8c9cee7's is a 3.6 s loop — only its first CFG.hallDoor.openSec (the open move) is used, so it works unchanged with either GLB.
function hallDoor(mx, g) {
  let c = g.animations.find(a => a.name === CFG.hallDoor.clip); if (!c) return;
  const end = CFG.hallDoor.openSec; if (c.duration > end + 1e-3) c = THREE.AnimationUtils.subclip(c, c.name + '_open', 0, Math.round(end * 1000), 1000);
  const a = mx.clipAction(c); a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; a.play(); window.__ps3d.hallDoor = { clip: c.name, dur: +c.duration.toFixed(3), action: a };
}
const SITECAM = STATIONS.map(() => ({ k: 1, dx: 0, dz: 0, ly: CAM.lookY }));   // per-station framing; the Mine keeps k=1, dx=dz=0 until its GLB (with Cam_Target) is in
const stationMixers = [], stationObjs = {};
const _ct = new THREE.Vector3();
// ===== per-station camera overrides (Director 21:25): ONE table, keyed by the exact GLB's md5 (first 8 hex, = the ?v= in its URL), so Art can bake
// the numbers into Cam_Target later and the entry then simply stops matching. ct = Cam_Target replacement in station-local glTF metres (only the
// given axes; the rest stay Art's), frame_w = replacement width. Any other GLB (or a new export of these) is untouched.
const FW_REF = 37.5;   // Refinery W: Art 3c5e6f8 final (Director 21:42 asked for ≥ 5 px; Art: ≥ 10 px spare at both sizes with Cam_Target z 13.55)
const CAM_OVERRIDE = {
  'ef45f6f1': { glb: 'mine 449757b (re-keyed from cc084a9b, Cam_Target unchanged)', ct: { y: 5.6 }, frame_w: 39.9 },
  'cc084a9b': { glb: 'mine 12bdb4a (re-keyed from 2123a050, same framing)', ct: { y: 5.6 }, frame_w: 39.9 },                            // Art 5d16bad: Cam_Target y 6.0 → 5.6 (x, z unchanged), W 37.6 → 39.9; ~9 px spare top+bottom at 375×667 (drill rig / Dep_01)
  '7959ae74': { glb: 'dock_tankfarm fd286b9', ct: { y: 1.5 }, frame_w: 66 },   // 03:4x (Director): Cam_Target y 2.5 → 1.5 and frame_w 64 → 66 so the footing clears 5 px at 375 with footings counted
  'e8427ec4': { glb: 'life_support adfaac9', ct: { y: -3.58 }, frame_w: 47.6 },                  // Art 5d16bad (was y -3.1 / W 46, Director 21:25): ~9 px spare top+bottom at 375×667 incl. the paint apron
  '4020a073': { glb: 'shipyard 2d57b95', ct: { x: 7.7, y: 6.2, z: 9.5 }, frame_w: 150, temporary: true },   // Director 21:25: TEMPORARY, testing only
  '82131aba': { glb: 'launch_pad 6b5c76e (flush hatch + ship tone; same Cam_Target/frame_w)', ct: { x: 0, y: 4, z: -0.7 }, frame_w: 78.25 },
  '0a5806f4': { glb: 'launch_pad 97763ba (detailed starter ship, thick cyan rings; same Cam_Target/frame_w)', ct: { x: 0, y: 4, z: -0.7 }, frame_w: 78.25 },
  '816f18f3': { glb: 'launch_pad 62a5dcb', ct: { x: 0, y: 4, z: -0.7 }, frame_w: 78.25 },   // re-keyed from a82251e2 (4017f16): Art 62a5dcb GLB carries the same Cam_Target/frame_w in its extras;        // Art final (Director: U-turn may sit off-screen): Cam_Target world (480, 4, −0.7) = pad-local (0, 4, −0.7), W 78.25; was z 9.5 / W 82 (Director 21:50)
  '93c44166': { glb: 'refinery d6389a7 (re-keyed from b45b4649, same 3c5e6f8 framing)', ct: { x: -6.9, y: 2.08, z: 13.55 }, frame_w: FW_REF },
  'b45b4649': { glb: 'refinery f4d4a2c', ct: { x: -6.9, y: 2.08, z: 13.55 }, frame_w: FW_REF },   // Art 3c5e6f8 final: Cam_Target world (313.1, 2.08, 13.55), W 37.5
};
const camOvFor = (url) => { const m = /[?&]v=([0-9a-f]{8})/.exec(url || ''); return m && CAM_OVERRIDE[m[1]] ? Object.assign({ md5: m[1] }, CAM_OVERRIDE[m[1]]) : null; };
function camTargetOf(o) { let t = null; o.traverse(n => { if (!t && n.name === 'Cam_Target' && n.userData && n.userData.frame_w > 0) t = n; }); return t; }
// ===== Refinery (index 2): Art's Refinery GLB 0358ffa (md5 41ac6c5a…), origin = Truck_Dump, Cam_Target (-5.9, 8.5, 3.36) frame_w 30.8.
// The shared HT-04 drives its Truck_Path_01..07 → reverse 4 m → Truck_Dump → Truck_Exit markers (Refinery-local). Values below are the
// README fallback so the truck timeline exists before the GLB is in; the GLB's own markers replace them on load.
const RMK = {};               // Refinery markers, Refinery-local { x, z }
(function refineryMarkerFallback() {
  RMK.Truck_Path_01 = { x: -46, z: 9 }; RMK.Truck_Path_02 = { x: -14, z: 9 };
  for (let k = 0; k <= 4; k++) { const p = -Math.PI / 2 + Math.PI * k / 4; RMK['Truck_Path_0' + (3 + k)] = { x: -3.5 + 4.5 * Math.cos(p), z: 4.5 - 4.5 * Math.sin(p) }; }   // U-turn r 4.5 about (−3.5, 4.5) (f4d4a2c)
  RMK.Truck_Dump = { x: 0, z: 0 }; RMK.Truck_Exit = { x: -46, z: 0 };
})();
const refActs = {}, refDust = { node: null, curve: null, mats: [], a: 0 };
function curveAt(cv, t) { if (t <= cv[0][0]) return cv[0][1]; for (let i = 1; i < cv.length; i++) if (t <= cv[i][0]) { const [t0, a0] = cv[i - 1], [t1, a1] = cv[i]; return t1 > t0 ? a0 + (a1 - a0) * (t - t0) / (t1 - t0) : a1; } return cv[cv.length - 1][1]; }
function updRefDust() {               // after the mixers: visible only while dump_dust plays; opacity from the extras curve (else the material's own alpha)
  const n = refDust.node, a = refActs.dump_dust; if (!n) return;
  const on = !!(a && a.isRunning()); n.visible = on; if (!on) { refDust.a = 0; return; }
  const k = refDust.curve ? clamp(curveAt(refDust.curve, a.time), 0, 1) : 1; refDust.a = k; for (const e of refDust.mats) e.m.opacity = e.a0 * k;
}
function refineryLoaded(o, mx, gltf) {
  o.traverse(n => { if (n !== o && /^(Truck|HT04|HT-04)($|_Mesh|_Root)/i.test(n.name)) n.visible = false; });   // hide any baked truck (none in 4a70acf)
  let moved = false;
  o.traverse(n => { if (RMK[n.name]) { const p = RMK[n.name]; if (Math.hypot(p.x - n.position.x, p.z - n.position.z) > .01) moved = true; RMK[n.name] = { x: n.position.x, z: n.position.z }; } });
  for (const c of gltf.animations) if (c.name === 'intake_shake' || c.name === 'dump_dust') { const a = refActs[c.name] = mx.clipAction(c); a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = false; }   // dump_dust: once per tip (rest scale 0.001 = hidden)
  // Director 21:17: Art's path-marker debug spheres must never show. Any small, roughly round mesh sitting on a Truck_* marker (or a red one near the road) is hidden + reported
  const mkW = Object.entries(RMK).map(([n, p]) => [n, p.x, p.z]), sus = []; const bb = new THREE.Box3(), c3 = new THREE.Vector3(), sz = new THREE.Vector3();
  o.updateMatrixWorld(true);
  o.traverse(n => { if (!n.isMesh || /^Tier_|Base_/.test(n.name) || /^Tier_|Base_/.test(n.parent && n.parent.name || '')) return; bb.setFromObject(n); bb.getCenter(c3); bb.getSize(sz);
    const lx = c3.x - o.position.x, lz = c3.z, mx3 = Math.max(sz.x, sz.y, sz.z), mn3 = Math.min(sz.x, sz.y, sz.z), round = mx3 < 2.5 && mn3 > .5 * mx3;
    const near = mkW.find(([nm, x, z]) => Math.hypot(lx - x, lz - z) < 1.2);
    const red = [].concat(n.material).some(m => m && m.color && m.color.r > .5 && m.color.g < .3 && m.color.b < .3);
    if (round && (near || red)) { n.visible = false; sus.push({ name: n.name || '(unnamed)', parent: n.parent && n.parent.name, at: [+lx.toFixed(2), +c3.y.toFixed(2), +lz.toFixed(2)], size: +mx3.toFixed(2), near: near && near[0], red }); } });
  // Art 9db5b33: Dump_Dust (8 puffs, clip dump_dust 1.5 s once per tip, rest scale 0.001) — hidden while idle; extras.opacity_curve [[t, a], …] honoured if present
  refDust.node = o.getObjectByName('Dump_Dust'); refDust.curve = null; refDust.mats = [];
  if (refDust.node) { const cv = refDust.node.userData && refDust.node.userData.opacity_curve;
    if (Array.isArray(cv) && cv.length >= 2 && cv.every(k => Array.isArray(k) && isFinite(k[0]) && isFinite(k[1]))) refDust.curve = cv.map(k => [+k[0], +k[1]]).sort((a, b) => a[0] - b[0]);
    refDust.node.traverse(m => { if (!m.isMesh) return; m.material = m.material.clone(); m.material.transparent = true; refDust.mats.push({ m: m.material, a0: m.material.opacity }); });
    refDust.node.visible = false; }
  Object.assign(window.__ps3d, { refDust, refActs, refMixer: mx, refSizer: mx.existingAction && (gltf.animations.find(c => c.name === 'sizer_spin') ? mx.existingAction(gltf.animations.find(c => c.name === 'sizer_spin')) : null) });
  window.__ps3d.refMarkerSpheres = sus; if (sus.length) console.warn('Refinery: hid marker-like spheres (ask Art to re-export without them)', JSON.stringify(sus));
  if (moved) buildRoute();             // the GLB's own markers replace the README fallback (before anything has settled: B1)
  window.__ps3d.refinery = o; routeReady('ref');
}
function fitSite(i) {
  const o = stationObjs[i]; if (!o || !camera.userData.dist) return;
  const ct = o.userData.camTarget, ov0 = o.userData.camOv, ovFull = ov0 && ov0.frame_w > 0 && ov0.ct && ov0.ct.x != null && ov0.ct.y != null && ov0.ct.z != null;
  if (ct || ovFull) {   // (a full CAM_OVERRIDE entry also frames a GLB that has no usable Cam_Target, e.g. Shipyard 2d57b95)   // Art's station camera: aim at Cam_Target (incl. its y), frame_w metres span the screen width at its depth; 38° vFOV, 18° down; edges may crop
    o.updateMatrixWorld(true); if (ct) ct.getWorldPosition(_ct); else _ct.copy(o.position); const ov = ov0, fw = ov && ov.frame_w || ct.userData.frame_w;
    if (ov && ov.ct) { if (ov.ct.x != null) _ct.x = o.position.x + ov.ct.x; if (ov.ct.y != null) _ct.y = o.position.y + ov.ct.y; if (ov.ct.z != null) _ct.z = o.position.z + ov.ct.z; }
    const d = (fw / 2) / (Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect);
    SITECAM[i] = { k: d / camera.userData.dist, dx: _ct.x - i * GAP, dz: _ct.z, ly: _ct.y, ct: true, d, fw, ov: ov ? ov.md5 : null };
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
    if (n.isMesh) { n.castShadow = true; n.receiveShadow = true; if (n.isSkinnedMesh) n.frustumCulled = false; }   // Refinery 93c44166: Base_Paint is skinned
    if (/^Tier_\d+/.test(n.name) || (n.userData && n.userData.hidden_by_default)) n.visible = false;
  });
  scene.add(o); o.updateMatrixWorld(true); stationObjs[G.i] = o; o.userData.camTarget = camTargetOf(o); o.userData.camOv = camOvFor(G.url);
  if (phBox[G.i]) { scene.remove(phBox[G.i]); phBox[G.i].geometry.dispose(); phBox[G.i] = null; }
  const mx = new THREE.AnimationMixer(o); stationMixers.push(mx);
  for (const c of gltf.animations) if (G.loops.includes(c.name)) { const a = mx.clipAction(c); if ((G.pingPong || []).includes(c.name)) a.setLoop(THREE.LoopPingPong, Infinity); a.play(); }
  if (G.onLoad) G.onLoad(o, mx, gltf);
  fitSite(G.i);
  (window.__ps3d.stationsLoaded = window.__ps3d.stationsLoaded || []).push(STATIONS[G.i]);
}, undefined, (e) => { console.warn('station GLB failed, keeping gray box', G.url, e); if (G.i === 2) routeReady('ref'); });

// ===== B1 (Playtester 20:58): the truck timeline is final only once BOTH marker sets are in (Mine Path_Out_*/Path_Ret_*, Refinery Truck_*), or
// their GLB failed (then the README fallback stands). Until then nothing settles: no offline catch-up, no dumps, no cargo sim on the temp route.
const RT = { mine: false, ref: false, ready: false, card: false, at: 0 };
function routeReady(which) {
  if (which) RT[which] = true; if (RT.ready || !RT.mine || !RT.ref) return;
  RT.ready = true; RT.at = Math.round(performance.now()); window.__ps3d.routeReadyAt = RT.at;
  if (hadRt) catchUp(true); else { const t = nowMs(); settleTo(t, null); S.rt = t; }   // credit time away since the last save, on the final route
  hud(); sheetUI();
}
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
  stationObjs[MINE] = mine; mine.userData.camTarget = camTargetOf(mine); mine.userData.camOv = camOvFor(MINE_GLB);
  buildTiers(); applyTiers(0);
  mixer = new THREE.AnimationMixer(mine);
  for (const c of gltf.animations) acts[c.name] = mixer.clipAction(c);
  for (const n of ['dig', 'conveyor_run']) if (acts[n]) acts[n].play();
  digOn = null;
  if (Object.keys(MK).some(n => /^Path_(Out|Ret)_/.test(n))) moved.push('Path_Out_*/Path_Ret_*');   // Art's out/return route markers: marker-driven route
  if (moved.length) { buildRoute(); window.__ps3d.routeMoved = moved; }   // marker-driven route, built before anything settles (B1)
  routeReady('mine');
  applyRigLevel(); fitSite(MINE); bindDepNodes(); restoreDeposits();
  if (op) { const d = MK.Operator_Deck; op.position.set(MX + d.x, 0, d.z); }
  rigLoaded = true; maybeReady();
  Object.assign(window.__ps3d, { mine, rig, MK, bindDepNodes, depNodesRaw: depNodes, deposits, spawnDeposit, removeDeposit, clips: gltf.animations.map(a => a.name + ':' + a.duration.toFixed(2)) });
}, undefined, (e) => {
  console.error('Mine GLB load failed', e); clearTimeout(coverTimer); coverTimer = 0; routeReady('mine');   // fallback route stands
  $('coverTx').textContent = "Couldn't load the Mine"; $('coverSp').hidden = true; $('coverRetry').hidden = false;
}); }
$('coverRetry').addEventListener('click', () => {
  $('coverRetry').hidden = true; $('coverSp').hidden = false; $('coverTx').textContent = 'Loading Moonbase…'; armCoverTimer(); loadRig();
});

// ===== HT-04 haul truck prop (Art c0452bd, md5 16eccb4d…): root 'Truck' at the ground centre, +X forward at yaw 0; world-space object
let truck = null, truckRoot = null, truckDone = false, tMixer = null, fillArcNode = null;
const tActs = {}, wheels = [], fillMeshes = [];
function loadTruck() { loader.load('../qa3d-next/models/ht04_71fe624e.glb?v=71fe624e', (gltf) => {
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
// Crew roster (Director 10:55): 4 people. The Miner (Mine operator prop) and the Mine Driver (HT-04; no figure drawn) stay at the Mine; the Cargo Manager
// (the Launch Pad Receiver figure) and the Mechanic (no ground figure) fly: they board, are away with the ship and come back after it lands.
// board = the crew_boarding GLB climber they play (the Mechanic = Crew_2: no GLB/doc names a Mechanic; Crew_2 is the next one in the stagger).
const CREW = [{ role: 'Miner', station: MINE, prop: 'mine_operator' }, { role: 'Mine Driver', station: MINE, prop: 'ht04' },
  { role: 'Cargo Manager', station: 'pad', prop: 'receiver', flies: 1, board: 'Crew_1' }, { role: 'Mechanic', station: 'pad', flies: 1, board: 'Crew_2' }].slice(0, CFG.crew0);
// ===== FollowCam: a generic eased, damped follow camera (Director 10:25: one module; today the ladder, a later Lv1 elevator car points the same camera
// at the car). It follows a target (pure: cfg.sample(t, v) = target world position at time t; or live: cfg.target = an Object3D or () => Vector3), frames
// it at the HUD-free band centre with plain lookAt + the station elevation, sizes the shot by the min-px rule (fw = W·subjectH / (minPx·margin): the
// subject stays ≥ minPx tall at any phone width), then once the target passes handY eases (cfg.hand s) to the final framing node (cfg.final + finalFw,
// the art's extras frame_w). Weight eases in from t0 (cfg.in), out after release + hold (cfg.out); cancel() eases out over cfg.cancel s (wall clock).
// Pure mode precomputes the track (cfg.dt) and damps it with a Gaussian (σ cfg.sig), and measures the handY crossing on the raw track, so the camera is a
// pure function of t: reload / lock land on the same shot. Live mode damps per frame (critically damped, ~σ) and keeps no saved state.
function makeFollowCam(cfg) {
  const c = Object.assign({ dt: 1 / 30, sig: .5, t0: 0, t1: 60, handY: Infinity, handAfter: -Infinity, handT: Infinity, final: null, finalFw: 16,
    minPx: 20, subjectH: 1.8, margin: 1.3, in: 2, hand: 2, release: 60, hold: .8, out: 2, cancel: .6 }, cfg);
  const fc = { cfg: c, trk: null, hand: c.handT, handSrc: 'fallback', fin: new THREE.Vector3(), live: null, rel: null }, v = new THREE.Vector3(), tv = new THREE.Vector3();
  fc.build = () => {
    if (c.final) { c.final.updateMatrixWorld(true); c.final.getWorldPosition(fc.fin); }
    if (!c.sample) return fc;
    const dt = c.dt, n = Math.ceil(c.t1 / dt) + 1, X = new Float32Array(n), Y = new Float32Array(n), Z = new Float32Array(n);
    for (let i = 0; i < n; i++) { c.sample(Math.min(i * dt, c.t1), v); X[i] = v.x; Y[i] = v.y; Z[i] = v.z;
      if (fc.handSrc !== 'measured' && i && i * dt >= c.handAfter && v.y >= c.handY) { fc.hand = (i - 1 + (c.handY - Y[i - 1]) / Math.max(1e-6, v.y - Y[i - 1])) * dt; fc.handSrc = 'measured'; } }
    const r = Math.ceil(3 * c.sig / dt), gw = []; for (let q = -r; q <= r; q++) gw.push(Math.exp(-0.5 * (q * dt / c.sig) ** 2));
    const sm = (A) => { const o = new Float32Array(n); for (let i = 0; i < n; i++) { let s = 0, ws = 0; for (let q = -r; q <= r; q++) { const k = i + q; if (k < 0 || k >= n) continue; s += A[k] * gw[q + r]; ws += gw[q + r]; } o[i] = s / ws; } return o; };
    fc.trk = { dt, n, X: sm(X), Y: sm(Y), Z: sm(Z), rawY: Y }; return fc; };
  fc.targetAt = (t, o) => {                          // damped target position
    if (fc.trk) { const T = fc.trk, f = clamp(t / T.dt, 0, T.n - 1), i = Math.floor(f), j = Math.min(T.n - 1, i + 1), u = f - i; return o.set(lerp(T.X[i], T.X[j], u), lerp(T.Y[i], T.Y[j], u), lerp(T.Z[i], T.Z[j], u)); }
    const g = c.target; if (g && g.isObject3D) g.getWorldPosition(tv); else if (g) tv.copy(g()); else return o.copy(fc.fin);
    const L = fc.live; if (!L || t < L.t || t - L.t > 1) { fc.live = { t, p: tv.clone(), vel: new THREE.Vector3() }; if (tv.y >= c.handY && t >= c.handAfter && fc.hand === Infinity) fc.hand = t; return o.copy(tv); }
    const h = t - L.t, w = 2 / c.sig, x = w * h, e = 1 / (1 + x + .48 * x * x + .235 * x * x * x);      // critically damped spring (Game Programming Gems 4)
    v.subVectors(L.p, tv); const tmp = L.vel.clone().addScaledVector(v, w).multiplyScalar(h);
    L.vel.sub(tmp.clone().multiplyScalar(w)).multiplyScalar(e); L.p.copy(tv).add(v.add(tmp).multiplyScalar(e)); L.t = t;
    if (fc.handSrc !== 'measured' && t >= c.handAfter && tv.y >= c.handY) { fc.hand = t; fc.handSrc = 'live'; }
    return o.copy(L.p); };
  fc.fw = () => W * c.subjectH / (c.minPx * c.margin);                                                        // the min-px rule
  const fwK = (fw) => (fw / 2) / (Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect) / camera.userData.dist;   // fitSite's distance, as a k
  fc.at = (t, o) => {                                // look point + k at t (before the blend with the station camera)
    const kF = fwK(fc.fw()), kT = fwK(c.finalFw), e = THREE.MathUtils.degToRad(CAM.elev), bd = band();
    const pxm = (H / 2) / (camera.userData.dist * kF * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))), off = (H / 2 - (bd.top + bd.bot) / 2) / pxm;   // target at the band centre
    fc.targetAt(t, v); const fx = v.x, fy = v.y - Math.cos(e) * off, fz = v.z + Math.sin(e) * off;
    const h = c.final ? fss((t - fc.hand) / c.hand) : 0; o.ph = t < c.t0 ? 'pre' : h <= 0 ? 'follow' : h < 1 ? 'handoff' : 'final';
    o.lx = lerp(fx, fc.fin.x, h); o.ly = lerp(fy, fc.fin.y, h); o.lz = lerp(fz, fc.fin.z, h); o.k = kF * Math.pow(kT / kF, h); return o; };
  fc.w = (t) => fss((t - c.t0) / c.in) * (1 - fss((t - c.release - c.hold) / c.out));
  fc.end = () => c.release + c.hold + c.out;
  fc.cancel = (w0) => { fc.rel = w0 > 0 ? { t0: performance.now(), w0 } : null; };
  fc.cancelW = () => { if (!fc.rel) return 0; const u = (performance.now() - fc.rel.t0) / 1000 / c.cancel; if (u >= 1) { fc.rel = null; return 0; } return fc.rel.w0 * (1 - fss(u)); };
  return fc;
}

// ===== crew boarding v4 (Art 8d2c18d: crew_boarding.glb md5 b989de5a…, 4 skinned crew C1_…C4_, 4 draws, 10,772 tris). Pad-local glTF: the root sits at
// the Launch Pad root (PX, 0, 0). Clips play back to back from CrewBoarding extras.clips: crew_call 0–3 → crew_walk_to_pad 3–22.3 → crew_climb 22.3–58.5 s
// (3.4 s stagger); Crew_k hides after extras.inside_hatch_s. Boarding time tb = now − launch start, read from S.cg.sh only (boardOf), so a reload, a
// lock or ?speed=N lands on the exact pose (pure function of state + now, like the Receiver). The cargo sim is untouched (sale at launch + 8 s, away,
// landing): only the ship's VISUAL lift-off waits until the crew are aboard and the camera is home (BD.lift). ?board=off = no crew, old lift-off.
// Climbers = the flying crew (CREW[].flies → their GLB climber): 2 (Crew_1 Cargo Manager, Crew_2 Mechanic); the other GLB climbers are removed.
// Camera (Director 05:01 stage 1) = the ladder adapter for FollowCam: target = the lead climber's pelvis (C1_Hips) sampled from the clips, from the
// walk-in; hand-off at the trigger's threshold_y_m (14 m) to Board_Focus_Top + its frame_w; release when the last climber is inside. Gate: only if the
// player is on the Launch Pad when the boarding starts; any tap / swipe / dot eases back to the station camera for the rest of that boarding (S.bc, saved).
const CREW_GLB = '../qa3d-next/models/crew_boarding_b989de5a.glb?v=b989de5a';
const BD = { on: Q.get('board') !== 'off', root: null, mx: null, acts: {}, clips: [], end: 58.5, crew: [], n: 0, inside: [], lead: null, fc: null,
  trig: 35.092, trigSrc: 'extras', walkIn: 3, lift: 58.5, pre: 2, cur: '' };   // trig / lift in board time (tb); clips + inside in crew time (tb − pre)
const BCAM = { minPx: 20, subjectH: 1.8, margin: 1.3, sig: .5, in: 2.0, hand: 2.0, hold: .8, out: 2.0, cancel: .6, fadeIn: .5, rxFade: 1.0 };   // ladder adapter config
function fadeObj(o, a) {              // whole-object opacity (own material copies, made once); a ≤ 0 → hidden, 1 → opaque (no transparency cost)
  if (!o) return; o.visible = a > .003; if (o.userData._fa === a) return; o.userData._fa = a; const tr = a < .999;
  o.traverse(m => { if (!m.isMesh) return; if (!m.userData._fm) { m.material = Array.isArray(m.material) ? m.material.map(x => x.clone()) : m.material.clone(); m.userData._fm = 1; }
    for (const x of [].concat(m.material)) { if (x.transparent !== tr) { x.transparent = tr; x.needsUpdate = true; } x.opacity = tr ? a : 1; } });
}
// The Cargo Manager's pad figure (Receiver): on the pad only while the ship is; fades out over the first rxFade s of the boarding (the camera is still
// easing in, his climber appears at BCAM.in), hidden through launch / away / landing, fades back in at his usual spot from touchdown.
function rxAlpha(c = S.cg, t = nowMs()) { const s = c.sh; if (!BOARD_SEC) return 1;
  return s.st === 'pad' ? (c.launches ? fss((t - s.t0) / (BCAM.rxFade * 1000)) : 1) : s.st === 'board' ? 1 - fss((t - s.t0) / (BCAM.rxFade * 1000)) : 0; }
function crewOnPad() { if (cg3 && cg3.astro) fadeObj(cg3.astro, rxAlpha()); }
function crewCount(t = nowMs()) {     // people drawn per role (tests): Miner = Mine operator, Cargo Manager = Receiver + Crew_1, Mechanic = Crew_2
  const vis = (o) => { if (!o) return false; for (let p = o; p; p = p.parent) if (!p.visible) return false; return true; };
  const cl = (n) => { const x = BD.root && BD.root.getObjectByName(n); return x && vis(x) && BD.root.userData._fa > .003 ? 1 : 0; };
  return { Miner: vis(op) ? 1 : 0, 'Mine Driver': 0, 'Cargo Manager': (vis(cg3.astro) ? 1 : 0) + cl('Crew_1'), Mechanic: cl('Crew_2'),
    extraClimbers: BD.root ? ['Crew_3', 'Crew_4'].filter(n => BD.root.getObjectByName(n)).length : 0, rxA: +rxAlpha().toFixed(3), ship: S.cg.sh.st }; }
const BC = { w: 0, tb: -1, lx: 0, ly: 0, lz: 0, k: 1, ph: 'off' };
const CAMLOOK = { lx: 0, ly: 0, lz: 0, k: 1 };
// Sim boarding phase (Director 10:55): Launch tap / auto-launch → sh.st 'board' (sh.t0 = its start, shifted by cgShift like every sh timestamp); at
// sh.t0 + BOARD_SEC the existing launch starts (burn, sale at +launchSec, away, land). BOARD_SEC is a constant of the art timing (not of the GLB load),
// so the sim, offline catch-up and reload never depend on the art: lead-in (camera ease-in) + last flying climber inside + hold + ease-out.
const BOARD_INSIDE = { Crew_1: 47.79, Crew_2: 51.19, Crew_3: 54.59, Crew_4: 57.99 };   // crew_boarding.glb extras.inside_hatch_s (checked on load)
const BOARD_FLY = CREW.filter(c => c.flies && c.board);
const BOARD_SEC = BD.on && BOARD_FLY.length ? BCAM.in + Math.max(...BOARD_FLY.map(c => BOARD_INSIDE[c.board])) + BCAM.hold + BCAM.out : 0;
function boardOf(c = S.cg) { const s = c && c.sh; return s && s.st === 'board' ? { B: s.t0, id: c.launches + 1 } : null; }   // the boarding in progress
function crewPose(tb) {                // pure: tb seconds since the launch
  const C = BD.clips; let k = 0; while (k < C.length - 1 && tb >= C[k + 1].t0) k++;
  const c = C[k], a = BD.acts[c.name];
  if (BD.cur !== c.name) { BD.mx.stopAllAction(); a.play(); a.setEffectiveWeight(1); BD.cur = c.name; }
  a.time = clamp(tb - c.t0, 0, c.dur - 1e-4); BD.mx.update(0);
  for (let i = 0; i < BD.n; i++) BD.crew[i].visible = tb < BD.inside[i];
}
// Lead-in: the crew timeline starts BD.pre (= the camera's ease-in, BCAM.in) after the launch, so the follow framing is reached before the first crew
// frame is drawn (every climber ≥ minPx from their first visible frame); clip timing relative to each other is unchanged.
const crewCamAt = (tb, o = BC) => BD.fc.at(tb - BD.pre, o), crewCamW = (tb) => BD.fc.w(tb - BD.pre), crewPoseB = (tb) => crewPose(tb - BD.pre);
const viewingPad = () => S.site === PADI && Math.abs(camX - PX) < 3 && !drag;
function updCrew() {
  if (!BD.root) { crewOnPad(); return; }
  const b = boardOf(), tb = b ? (nowMs() - b.B) / 1000 : -1, act = !!b && tb >= 0 && tb < BD.lift;
  const cv = act && tb >= BD.pre && tb - BD.pre < BD.end && Math.abs(camX - PX) < GAP * .75;   // off-site / lead-in: no draws
  fadeObj(BD.root, cv ? fss((tb - BD.pre) / BCAM.fadeIn) : 0);   // the climbers fade in at full follow framing (no pop)
  if (cv) crewPose(tb - BD.pre);
  crewOnPad();
  if (act && (!S.bc || S.bc.id !== b.id)) { S.bc = { id: b.id, on: viewingPad() ? 1 : 0, x: 0 }; save(); }   // gate: decided once per boarding, saved
  let w = 0;
  if (act && S.bc.on) { crewCamAt(tb, BC); w = S.bc.x ? BD.fc.cancelW() : crewCamW(tb); }
  else BC.ph = 'off';
  if (!act) BD.fc.rel = null;
  BC.w = w; BC.tb = tb;
}
function crewCancel(by) {             // any tap / swipe / dot: ease back to the station camera, stays there for this boarding
  const b = boardOf(); if (!BD.root || !b || !S.bc || S.bc.id !== b.id || !S.bc.on || S.bc.x) return;
  S.bc.x = 1; save(); BD.fc.cancel(BC.w);
  window.__ps3d.crewCanceled = { by, tb: +BC.tb.toFixed(2), w: +BC.w.toFixed(3) };
}
function loadCrew() { if (!BD.on) return; loader.load(CREW_GLB, (g) => {
  const o = g.scene, root = o.getObjectByName('CrewBoarding'), ex = (root && root.userData) || {}; o.name = 'CrewBoarding_Art'; o.position.set(PX, 0, 0);
  o.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = false; m.frustumCulled = false; } });
  const cl = ex.clips || { crew_call: [0, 3], crew_walk_to_pad: [3, 22.3], crew_climb: [22.3, 58.5] };
  BD.mx = new THREE.AnimationMixer(o);
  for (const c of g.animations) if (cl[c.name]) { BD.acts[c.name] = BD.mx.clipAction(c); BD.clips.push({ name: c.name, t0: +cl[c.name][0], dur: c.duration }); }
  if (BD.clips.length !== 3) throw new Error('crew boarding clips missing');
  BD.clips.sort((a, b) => a.t0 - b.t0); BD.end = BD.clips[2].t0 + BD.clips[2].dur; BD.walkIn = BD.clips[1].t0;
  const all = []; for (let k = 1; o.getObjectByName('Crew_' + k); k++) all.push(o.getObjectByName('Crew_' + k));
  BD.crew = BOARD_FLY.map(c => o.getObjectByName(c.board)).filter(Boolean); BD.n = BD.crew.length;
  for (const x of all) if (!BD.crew.includes(x)) x.parent.remove(x);   // not flying: out of the scene (no draws)
  const ins = ex.inside_hatch_s || {}; BD.inside = BD.crew.map((c, i) => +ins[c.name] || BD.end);
  BD.lead = o.getObjectByName('C1_Hips');
  const ft = o.getObjectByName('Board_Focus_Top'), tr = (ft && ft.userData.trigger) || {};
  if (!ft || !BD.lead) throw new Error('Board_Focus_Top / C1_Hips missing');
  o.updateMatrixWorld(true);
  BD.fc = makeFollowCam({ ...BCAM, sample: (t, v) => { crewPose(t); o.updateMatrixWorld(true); return BD.lead.getWorldPosition(v); },
    t0: -BCAM.in, t1: BD.end, handY: +tr.threshold_y_m || 14, handAfter: BD.clips[2].t0, handT: +tr.fallback_absolute_s || 35.092,
    final: ft, finalFw: +ft.userData.frame_w || 16.1, release: BD.inside[BD.n - 1] }).build();
  BD.pre = BCAM.in; BD.trig = BD.pre + BD.fc.hand; BD.trigSrc = BD.fc.handSrc; BD.lift = BD.pre + BD.fc.end();   // board time: crew inside, camera home = the sim's lift-off
  if (Math.abs(BD.lift - BOARD_SEC) > .01) console.warn('crew boarding: GLB inside_hatch_s gives lift-off ' + BD.lift + ' s, sim BOARD_SEC ' + BOARD_SEC);
  BD.cur = ''; o.visible = false; scene.add(o); BD.root = o;
  window.__ps3d.crewBoarding = { n: BD.n, end: BD.end, trig: +BD.trig.toFixed(3), trigSrc: BD.trigSrc, topFw: BD.fc.cfg.finalFw, followFw: +BD.fc.fw().toFixed(2), lift: +BD.lift.toFixed(2), pre: BD.pre, end: BD.pre + BD.end, inside: BD.inside.map(x => +(x + BD.pre).toFixed(3)) };
}, undefined, (e) => console.warn('crew boarding GLB failed (ship launches without crew)', e)); }

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
  if (cam === camera && BC.w > 0) { const w = BC.w; lx += (BC.lx - lx) * w; lyy += (BC.ly - lyy) * w; lz += (BC.lz - lz) * w; kk *= Math.pow(BC.k / kk, w); }   // crew boarding camera blend (k in log space)
  if (cam === camera) { CAMLOOK.lx = lx; CAMLOOK.ly = lyy; CAMLOOK.lz = lz; CAMLOOK.k = kk; }
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
  e.stopPropagation(); cancelFocus('dot'); crewCancel('dot'); const r = dotsEl.getBoundingClientRect(); goSite(Math.round((e.clientX - r.left) / r.width * N - .5));
});
ui();

// ===== swipe: always exactly one station from S.site; tiny drags spring back; taps go to deposits
let drag = null;
canvas.addEventListener('pointerdown', (e) => {
  crewCancel('tap');                                              // any tap or swipe ends the boarding camera
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
  const om = oreMin(); rateEl.textContent = om < 10 ? om.toFixed(1) : Math.round(om);
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
  el.style.left = x + 'px'; el.style.top = y + 'px'; document.body.appendChild(el); el.addEventListener('animationend', () => el.remove(), { once: true }); setTimeout(() => el.remove(), 4000);   // remove when the fade has really finished (a hitch can't cut it short); 4 s fallback if animations never run
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


// ===== deposits (Director 21:17): the ore patches + faint cyan veins are Art's, baked in the Mine GLB (a4f93eb: dep_patch in Base_Paint, Base_DepVein).
// The game draws NOTHING at Dep_01 / Dep_02 any more (no disc, decal, glow, pulse or fade): a deposit is just a tap target (max 2, respawn ~8 s).
// Director 23:00 (B): the 1 s fade-in (and hidden while used up) runs on Art's real patch nodes, /^Deposit_\d+/ in the Mine GLB, one material clone per
// deposit (never Base_GlowCyan or the building strips). No Deposit_ nodes (a4f93eb: patches merged into Base_Paint) → nothing to fade, the baked patch stays.
// The old invisible stand-in fade is gone; d.disc is now a plain position/scale stub so old QA reads stay valid.
const depStub = () => { const o = new THREE.Object3D(); o.visible = false; o.material = { opacity: 1, dispose() {} }; return o; };
const DEP_RE = /^Deposit_(\d+)/, depNodes = {};   // depNodes[Dep_0N] = { node, mats: [cloned materials] }
function bindDepNodes() {
  for (const k in depNodes) delete depNodes[k];
  if (!mine) return 0; const found = [];
  mine.traverse(o => { if (DEP_RE.test(o.name) && !(o.parent && DEP_RE.test(o.parent.name))) found.push(o); });
  for (const o of found) {
    const ex = o.userData || {}; let mk = DEP_NAMES.includes(ex.marker) ? ex.marker : 'Dep_' + String(+o.name.match(DEP_RE)[1]).padStart(2, '0');   // Art 12bdb4a extras: {deposit, fade_in_s, marker}
    if (!DEP_NAMES.includes(mk) || depNodes[mk]) {   // unnumbered match: nearest free Dep_ marker
      const w = o.getWorldPosition(new THREE.Vector3()); let best = null, bd = Infinity;
      for (const n of DEP_NAMES) { if (!MK[n] || depNodes[n]) continue; const dd = Math.hypot(MX + MK[n].x - w.x, MK[n].z - w.z); if (dd < bd) { bd = dd; best = n; } }
      if (!best) continue; mk = best; }
    const mats = [];
    o.traverse(m => { if (!m.isMesh) return; m.material = Array.isArray(m.material) ? m.material.map(x => { const c = x.clone(); mats.push(c); return c; }) : (mats.push(m.material = m.material.clone()), m.material); });
    depNodes[mk] = { node: o, mats, name: o.name, fade: ex.fade_in_s > 0 ? +ex.fade_in_s : 1 };
  }
  for (const mk in depNodes) depShow(mk, null);
  window.__ps3d.depNodes = Object.fromEntries(Object.entries(depNodes).map(([k, v]) => [k, v.name]));
  return found.length;
}
function depShow(mk, a) {             // a = opacity 0..1, null = used up (hidden)
  const n = depNodes[mk]; if (!n) return;
  n.node.visible = a != null && a > 0.001;
  for (const m of n.mats) m.opacity = a == null ? 1 : a;   // SHM_DepositRock/Glow are alphaMode BLEND at alpha 1 already (transparent): only opacity moves
}
const DEP_MIN_PX = 44;               // patch ≥ 44 CSS px across at any camera distance (tap target)
const _dw = new THREE.Vector3();
const DEP_NAMES = ['Dep_01', 'Dep_02'], DISC_Y = 0.1;
const deposits = []; let depTimer = 0, depSeq = 0;
const SA = { el: null };   // safe-area insets as the CSS sees them (env(safe-area-inset-*)), read off a hidden probe
function safeArea() { if (!SA.el) { SA.el = document.createElement('div'); SA.el.style.cssText = 'position:fixed;left:0;top:0;width:0;height:0;visibility:hidden;pointer-events:none;padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px) 0'; document.body.appendChild(SA.el); }
  const cs = getComputedStyle(SA.el); return { t: parseFloat(cs.paddingTop) || 0, b: parseFloat(cs.paddingBottom) || 0 }; }
function band() {                     // Playtester 20:58: the safe-area insets are part of the band (59/34 px on a 393×852 iPhone → y 165–534)
  const sa = safeArea(), top = Math.max(hudEl.getBoundingClientRect().bottom, 120, sa.t) + 24;   // station title moved to the bottom (above the dots); top of the band = under the HUD/Eve band (unchanged 144 px)
  const sheetTop = $('sheetWrap').getBoundingClientRect().top;      // open sheet top edge
  return { top, bot: Math.min(sheetTop, dotsEl.getBoundingClientRect().top, nameEl.getBoundingClientRect().top, innerHeight - sa.b) - 34, l: 34, r: W - 34, sat: sa.t, sab: sa.b };
}
function spawnDeposit(name) {
  if (!mine || deposits.length >= CFG.depositMax) return null;
  const free = DEP_NAMES.filter(n => MK[n] && !deposits.some(d => d.mk === n)); if (!free.length) return null;
  return makeDeposit(name && free.includes(name) ? name : free[Math.floor(Math.random() * free.length)]);
}
function makeDeposit(mk, claimed = false) {
  const m = MK[mk], x = MX + m.x, z = m.z, r = Math.max(1.6, (m.e.radius_m || 1.4) * 1.15);
  const disc = depStub(); disc.position.set(x, DISC_Y, z);   // invisible: the GLB patch is the deposit
  const gem = new THREE.Object3D(); gem.visible = false;   // no gem (Jacob 10/23, Director 20:35); kept as an empty stub so old QA reads of d.gem stay valid
  const d = { id: ++depSeq, mk, x, z, r, rs: r, disc, gem, age: claimed ? 1 : 0, claimed, dig: 0 }; deposits.push(d); return d;
}
function removeDeposit(d) { if (!d || !deposits.includes(d)) return; deposits.splice(deposits.indexOf(d), 1); depShow(d.mk, null); }   // used up: patch hidden
function restoreDeposits() {          // rich loads queued while the truck was away (saved in S.tk.qd) re-show with their ring until the truck is back
  for (const mk of S.tk.qd) if (MK[mk] && !MK[mk].fb && !deposits.some(d => d.mk === mk)) { const d = makeDeposit(mk, true); d.tkq = true; }
}
// queued deposits (tapped while the truck is away) get no ring any more (Director 10/24 00:00): the queue (S.tk.q / S.tk.qd) still drops into the next fill; QA reads stay
function updQueued() {
  for (const d of deposits) d.queued = !!d.tkq;
  window.__ps3d.queued = deposits.filter(d => d.queued).map(d => d.mk);
}
function updDeposits(dt, time) {
  depTimer += dt;
  if (deposits.length < CFG.depositMax && depTimer >= CFG.depositEvery) { depTimer = 0; spawnDeposit(); }
  if (deposits.length >= CFG.depositMax) depTimer = 0;
  const tn = nowMs();
  for (const d of [...deposits]) {
    if (d.claimed && d.at) { d.dig = clamp((tn - d.at) / 1000, 0, 1); if (d.dig >= 1) { removeDeposit(d); continue; } }   // drill taps it: shrinks over the 1 s rich drop
    d.age += dt;                       // static (no pulse): a new patch fades in over 1 s (no pop); only the drill tap digs it out (shrinks over the 1 s rich drop)
    depShow(d.mk, d.claimed && d.dig > 0 ? 1 - d.dig : clamp(d.age / ((depNodes[d.mk] && depNodes[d.mk].fade) || 1), 0, 1));   // real Deposit_ node (no-op without one)
    const shrink = d.claimed ? 1 - .85 * d.dig : 1;
    const pxm = (H / 2) / (Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * Math.max(1, camera.position.distanceTo(_dw.set(d.x, 0, d.z))));
    d.rs = Math.max(d.r, DEP_MIN_PX / 2 / pxm);
    d.disc.scale.setScalar(Math.max(.01, shrink * d.rs));
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
const TV = { v: 8.33, ease: 3, brake: 4, revRef: 1.5, dump: 3.0, settle: 0.4, revMine: 2.0, wheelR: 0.853 };   // revRef/revMine are recomputed in buildRoute from the reverse distance at ≤ TURN_ACC
const revSec = (d) => Math.max(1, Math.sqrt(6 * d / TURN_ACC));   // smoothstep move of d metres: peak accel 6d/T² = TURN_ACC
const R = { pOut: null, pBack: null, kOut: null, kBack: null, legOut: 0, legBack: 0, tl: null, mode: '' };
const mw = (n) => [MX + MK[n].x, MK[n].z], rw = (n) => [RX + RMK[n].x, RMK[n].z];
function line(a, b, step = 4) { const n = Math.max(1, Math.round(Math.hypot(b[0] - a[0], b[1] - a[1]) / step)), o = []; for (let i = 1; i <= n; i++) o.push([a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n]); return o; }
function dedupe(pts) { const o = []; for (const p of pts) { const q = o[o.length - 1]; if (!q || Math.hypot(p[0] - q[0], p[1] - q[1]) > .3) o.push(p); } return o; }
const PATH_STEP = .025;             // B2/B3 (21:2x): 2.5 cm samples — at 0.2 m the polyline corners in the r 4.5 turns read as ±0.3 m/s² speed ripple in pose-sampled accel
function samplePath(pts) {          // centripetal Catmull-Rom through the markers, resampled every ~PATH_STEP m by arc length
  pts = dedupe(pts);
  const c = new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(p[0], 0, p[1])), false, 'centripetal'); c.arcLengthDivisions = Math.max(20000, Math.ceil(c.getLength() / PATH_STEP * 4));
  const n = Math.ceil(c.getLength() / PATH_STEP) + 1, sp = c.getSpacedPoints(n - 1), X = new Float64Array(n), Z = new Float64Array(n), C = new Float64Array(n);
  for (let i = 0; i < n; i++) { X[i] = sp[i].x; Z[i] = sp[i].z; if (i) C[i] = C[i - 1] + Math.hypot(X[i] - X[i - 1], Z[i] - Z[i - 1]); }
  return { n, X, Z, C, L: C[n - 1] };
}
function sOf(P, p) { let b = 0, bd = Infinity; for (let i = 0; i < P.n; i++) { const d = (P.X[i] - p[0]) ** 2 + (P.Z[i] - p[1]) ** 2; if (d < bd) { bd = d; b = i; } } return P.C[b]; }
function pathAt(P, s, o) { s = clamp(s, 0, P.L); let lo = 0, hi = P.n - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (P.C[m] <= s) lo = m; else hi = m; }
  const u = (s - P.C[lo]) / Math.max(1e-9, P.C[hi] - P.C[lo]); o.x = P.X[lo] + (P.X[hi] - P.X[lo]) * u; o.z = P.Z[lo] + (P.Z[hi] - P.Z[lo]) * u;
  if (!P.H) { P.H = new Float64Array(P.n); const hw = Math.round(.6 / PATH_STEP); for (let i = 0; i < P.n; i++) { const a = Math.max(0, i - hw), b = Math.min(P.n - 1, i + hw); P.H[i] = Math.atan2(-(P.Z[b] - P.Z[a]), P.X[b] - P.X[a]); } }
  o.yaw = lerpA(P.H[lo], P.H[hi], clamp(u, 0, 1)); return o; }   // B5: tangent per sample, blended between samples (no per-sample heading steps)
// Speed profile (Director 10/23 evening): 8.33 m/s on straights, TURN_SPEED through curves, eased between them.
// Built per sample of the path P: limit(s) = min( curve limit, start ease (0→v over da, as before), stop ease (v→0 over the last dd, as before) ),
// where the curve limit is TURN_SPEED wherever the heading turns tighter than TURN_R_MAX, smoothed by forward/backward passes at TURN_ACC m/s².
// Each sample-to-sample step has constant acceleration, so position and speed are exact closed forms of time (no jumps, timeline = pure function of t).
function kin(P, da, dd, v) {
  // Playtester B2/B3 + Director B4 (20:58): starts and ends at 0, |accel| ≤ TURN_ACC everywhere (da/dd only shorten it further); bends closer
  // than TURN_GAP m (straight between them) hold TURN_SPEED through the gap instead of a short speed-up.
  const n = P.n, C = P.C, L = P.L, V = new Float64Array(n), T = new Float64Array(n), cl = new Float64Array(n).fill(v), w = Math.round(1 / PATH_STEP);
  const hd = (i) => { const a = Math.max(0, i - w), b = Math.min(n - 1, i + w); return Math.atan2(P.Z[b] - P.Z[a], P.X[b] - P.X[a]); };
  let last = -1, bends = 0;
  for (let i = 0; i < n; i++) {                 // curvature from heading change over ±1 m
    const a = Math.max(0, i - w), b = Math.min(n - 1, i + w); if (b - a < 2) continue;
    let dh = hd(b) - hd(a); dh = Math.atan2(Math.sin(dh), Math.cos(dh)); const ds = C[b] - C[a];
    if (ds > 1e-6 && Math.abs(dh) / ds > 1 / TURN_R_MAX) {
      cl[i] = Math.min(v, TURN_SPEED);
      if (last >= 0 && i - last > 1) { if (C[i] - C[last] < TURN_GAP) for (let j = last + 1; j < i; j++) cl[j] = Math.min(v, TURN_SPEED); else bends++; }
      if (last < 0) bends++; last = i;
    }
  }
  const aS = Math.min(TURN_ACC, v * v / (2 * da)), aB = Math.min(TURN_ACC, v * v / (2 * dd));
  cl[0] = 0; for (let i = 1; i < n; i++) cl[i] = Math.min(cl[i], Math.sqrt(cl[i - 1] ** 2 + 2 * aS * (C[i] - C[i - 1])));          // forward: from rest, ≤ aS
  cl[n - 1] = 0; for (let i = n - 2; i >= 0; i--) cl[i] = Math.min(cl[i], Math.sqrt(cl[i + 1] ** 2 + 2 * aB * (C[i + 1] - C[i])));   // backward: to rest, ≤ aB
  for (let i = 0; i < n; i++) V[i] = cl[i];
  for (let i = 1; i < n; i++) { const vs = V[i - 1] + V[i]; T[i] = T[i - 1] + (vs > 1e-9 ? 2 * (C[i] - C[i - 1]) / vs : 0); }
  let vmin = v, amax = 0, dmax = 0; for (let i = 1; i < n; i++) { const ds = C[i] - C[i - 1]; if (ds < 1e-9) continue; const ac = (V[i] ** 2 - V[i - 1] ** 2) / (2 * ds); amax = Math.max(amax, ac); dmax = Math.max(dmax, -ac); }
  for (let i = 1; i < n - 1; i++) if (V[i] > 1e-3 && C[i] > 6 && C[i] < L - 6) vmin = Math.min(vmin, V[i]);
  return { L, n, C, V, T: T[n - 1], Ts: T, v, da, dd, vmin, amax, dmax, bends };
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
  { const a = rw('Truck_Path_07'), b = rw('Truck_Dump'), c = mw('Path_Load_Approach'), d = mw('Path_Load');
    TV.revRef = +revSec(Math.hypot(b[0] - a[0], b[1] - a[1])).toFixed(3); TV.revMine = +revSec(Math.hypot(d[0] - c[0], d[1] - c[1])).toFixed(3);
    R.yRev = Math.atan2(-(a[1] - b[1]), a[0] - b[0]); R.yMine = Math.atan2(-(c[1] - d[1]), c[0] - d[0]);   // reversing: the nose points back along the move
    const _ye = {}; R.yOutEnd = R.pOut.n > 4 ? pathAt(R.pOut, R.pOut.L, _ye).yaw : R.yRev;   // = the path's own end tangent (pathAt), so the reverse starts with no yaw step
    R.yBackEnd = R.pBack.n > 4 ? pathAt(R.pBack, R.pBack.L, _ye).yaw : R.yMine; }
  const sA = sOf(R.pOut, legA), sB = sOf(R.pOut, legB), sU = sOf(R.pOut, tp(3));
  R.legOut = sB - sA; const v = TV.v;                                   // 8.33 m/s on straights, TURN_SPEED through curves (Director 10/23)
  R.kOut = kin(R.pOut, TV.ease, TV.brake, v);                          // eased only where the truck stops: away from the chute, into the stop before the intake reverse
  const sC = sOf(R.pBack, legC), sD = sOf(R.pBack, legD);
  R.legBack = sD - sC; R.kBack = kin(R.pBack, TV.ease, TV.brake, v);  // eased away from the dump, 8.33 m/s straights / TURN_SPEED curves, eased stop at Path_Load_Approach
  const t1 = R.kOut.T, t2 = t1 + TV.revRef, t3 = t2 + TV.dump, t4 = t3 + TV.settle, t5 = t4 + R.kBack.T, t6 = t5 + TV.revMine;
  R.tl = { t1, t2, tDump: t2, t3, t4, t5, t6, trip: t6 };
  const f = (x) => +x.toFixed(2), tC = kinT(R.kBack, sC), tD = kinT(R.kBack, sD);
  window.__ps3d.route = { mode: R.mode, legOut: f(R.legOut), legBack: f(R.legBack), v: f(v), vTurn: TURN_SPEED, vMinOut: f(R.kOut.vmin), vMinBack: f(R.kBack.vmin), amax: f(Math.max(R.kOut.amax, R.kBack.amax)), dmax: f(Math.max(R.kOut.dmax, R.kBack.dmax)), revRef: TV.revRef, revMine: TV.revMine, Lout: f(R.pOut.L), Lback: f(R.pBack.L), tl: Object.fromEntries(Object.entries(R.tl).map(([k, x]) => [k, f(x)])),
    phases: { mineOut: f(kinT(R.kOut, sA)), legOut: f(kinT(R.kOut, sB) - kinT(R.kOut, sA)), refIn: f(t1 - kinT(R.kOut, sB)), revRef: TV.revRef, dump: TV.dump, settle: TV.settle,
      refOut: f(tC), legBack: f(tD - tC), mineReturn: f(R.kBack.T - tD), mineReturnM: f(R.pBack.L - sD), revMine: TV.revMine, trip: f(t6) } };
  buildTempRoad();
}
let roadMesh = null;
// Art's 8 m haul-road strip (shared/road 6f06c39, md5 661e3582…, pending Director review): 11 unscaled tiles at Mine-local x 26 + 8i, both lanes (z +9 / z 0).
// Swap back to the flat temp tiles with ?road=temp (or set ROAD_GLB to null).
const ROAD_GLB = Q.get('road') === 'temp' ? null : '../qa3d-next/models/haul_road_seg_b3c636f9.glb?v=b3c636f9';
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
const _ka = [0, 0], YAW_BLEND = 3;
function poseAt(t, o = TS) {
  const k = S.tk, tl = R.tl;
  if (!k.dep || t < k.dep) { const p = mw('Path_Load'); o.ph = 'fill'; o.x = p[0]; o.z = p[1]; o.yaw = R.yMine != null ? R.yMine : 0; o.v = 0; o.fill = fillAt(t); o.el = 0; return o; }
  const el = o.el = (t - k.dep) / 1000; o.fill = 1;
  // B5 (20:58): heading is continuous through every phase change — the reverse moves blend from the path's end tangent into the reverse
  // heading, and pull-aways blend from the parked heading into the path tangent over the first YAW_BLEND m (no snaps)
  if (el < tl.t1) { kinAt(R.kOut, el, _ka); pathAt(R.pOut, _ka[0], o); o.v = _ka[1]; o.ph = 'out'; if (_ka[0] < YAW_BLEND) o.yaw = lerpA(R.yMine, o.yaw, fss(_ka[0] / YAW_BLEND)); }
  else if (el < tl.t2) { const u = fss((el - tl.t1) / TV.revRef), a = rw('Truck_Path_07'), b = rw('Truck_Dump'); o.x = a[0] + (b[0] - a[0]) * u; o.z = a[1] + (b[1] - a[1]) * u; o.yaw = lerpA(R.yOutEnd, R.yRev, u); o.v = -1; o.ph = 'rev'; }
  else if (el < tl.t4) { const b = rw('Truck_Dump'); o.x = b[0]; o.z = b[1]; o.yaw = R.yRev; o.v = 0; o.ph = el < tl.t3 ? 'dump' : 'settle'; if (el >= tl.t3) o.fill = 0; }
  else if (el < tl.t5) { kinAt(R.kBack, el - tl.t4, _ka); pathAt(R.pBack, _ka[0], o); o.v = _ka[1]; o.ph = 'back'; o.fill = 0; if (_ka[0] < YAW_BLEND) o.yaw = lerpA(R.yRev, o.yaw, fss(_ka[0] / YAW_BLEND)); }
  else { const u = fss((el - tl.t5) / TV.revMine), a = mw('Path_Load_Approach'), b = mw('Path_Load'); o.x = a[0] + (b[0] - a[0]) * u; o.z = a[1] + (b[1] - a[1]) * u; o.yaw = lerpA(R.yBackEnd, R.yMine, u); o.v = -1; o.ph = 'revMine'; o.fill = 0; }
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
  if (refActs.dump_dust) refActs.dump_dust.reset().play();   // Art f4d4a2c: once at the start of each tip
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
  const k = S.tk, tl = R.tl; if (!tl || !RT.ready) return;          // B1: nothing settles on the temporary route
  payPend(T, acc);
  for (let g = 0; g < 20000; g++) {
    if (!k.dep) { const tf = tFull(); if (tf > T) break; k.dep = tf; k.paid = false; k.val = loadValue(); continue; }   // full: depart (value frozen now)
    if (!k.paid) { if (k.dep + tl.tDump * 1000 > T) break; k.paid = true; payBase(k.val, acc); cgSettle(k.dep + tl.tDump * 1000, acc); cgMake(k.dep + tl.tDump * 1000); }
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
setInterval(() => { if (document.hidden || !RT.ready) return; const t = nowMs(); if (t - S.rt < 60000 && t >= S.rt - 1000) { settleTo(t, null); S.rt = t; } }, 200);   // payouts keep wall-clock time even when frames stall
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
  receive: ['Receiver_Spot', 'Receive_Point', 'Hand_Point'],   // Receiver_Spot = Art Assistant 2's Launch Pad marker (when it exists)
  palletSlot: (i) => ['Pallet_Slot_' + String(i).padStart(2, '0')], drop2: ['Drop_Point_02'], wheelNames: ['FL', 'FR', 'ML', 'MR', 'RL', 'RR'].map(k => 'FB05_Wheel_' + k),
  signClips: ['sign_for_delivery', 'astro_sign_delivery', 'sign', 'check_in'], walkClips: ['walk', 'astro_walk'], idleClips: ['idle', 'astro_idle'],
};
// Placeholder layout, station-local metres (x from the station origin i·160, z world). Swap a GLB in and its markers replace these.
const CPH = {
  lanes: { out: 13, back: 22 }, road: { x0: RX - 24, n: 23, tile: 8 },                       // 23 strip tiles, world x 296–480, lanes z 13 / 22
  // Refinery side sits inside Art's Cam_Target frame (x ≈ 300–330): FB-05 loads at x 318; the crane + sealed-box pallet stand in the median between the lanes
  // Art affea57 RC-1: crane root world (318, 0, 17.5), Truck_Park (318, 0, 13) heading +X, Pallet_Slot_01..08 (Pick_Point = 01), Drop_Point/_02 over FB-05's bed slots
  // Art 014d751 RC-1 (Director-cleared 21:10, default): root world (311, 0, 17.5), jib mirrored, pallet WEST of the mast (x 302.25–307.65) so the mast
  // never hides a box landing on FB-05; the flatbed's west U-turn moves to x 295 (r 4.5, around the whole median island: pallet + concrete pad + pedestal)
  ref: { load: [-2, 13], uturn: [-25, 17.5], crane: [-9, 17.5], mast: 10, jib: 10.3, rmin: 2.6, rest: [-1.2, 0] },   // rest = yaw offset from the pick direction
  // Jacob rule (via Art, 21:20): the flatbed never runs over or into the Launch Pad. The whole pad footprint (slab, ship, fuel tank, bay, crane foot)
  // stays off the road band (world z 10.2–24.8) with ≥ 1 m clear ground (z ≤ 9.2); the bay sits at that roadside edge (z 3.6–9.2) so the pad crane
  // (foot z 5, reach 15) still picks off FB-05 on the z 13 lane. These are placeholder numbers only: padFromMarkers() reads Truck_Stop / Bay_Slot_01..12 /
  // Receiver_Spot / Receiver_Home / Ship_Center / Turn_Start from whatever stands at the pad (placeholder empties now, Art's new pad GLB later).
  // Art 4017f16 Launch Pad (Director-cleared 21:50, md5 a82251e2…) numbers, so the flatbed route is final before the GLB is in (offline catch-up is
  // deterministic): Truck_Stop (−3.5, 13), Turn_Start x 1 (U-turn r 4.5 about (1, 17.5) = its Road_UTurn), Ship_Center (0, −13), PC-1 at (0.6, 7),
  // Receiver_Spot (−7.85, 8.2) / Receiver_Home (−11.19, 7.94). The gray placeholder (GLB failed) stands on the same numbers.
  pad: { unload: [-3.5, 13], uturn: [1, 17.5], crane: [0.6, 7], mast: 19, jib: 14.2, bay: [-7.5, 4.25], ship: [0, -13], padTop: 1,
         home: [-11.194, 7.939], receive: [-7.85, 8.2], fuel: [4.4, -8] },
  padRoad: { z0: 10.2, z1: 24.8, clear: 1 },
  turnR: 4.5, hookHi: 6.4,   // carry height: box bottom 4.9 clears the FB-05 cab (3.8) and a full pallet (3.15)
};
const PADI = 3, PX = PADI * GAP;
// Refinery crane GLBs. CRANE_ART is the default (Art 014d751, md5 d98f602c…); CRANE_ART_AFFEA57 (md5 d1e577ce…, root x 318, pallet east) is kept as the
// fallback const: ?crane=affea57 swaps it back (its layout numbers included). A GLB's own markers replace these placeholder numbers on load.
// Art 93590a0 (Director-cleared 21:42, md5 755815ec…): same layout as 014d751 + the concrete pallet pad baked into Crane_Mesh (6.15×3.36×0.12 m, x 301.85–308.0,
// z 15.82–19.18); pallet markers +0.12 m. bakedPad: no code pad. 014d751 (d98f602c) stays as ?crane=d98f602c, affea57 as ?crane=affea57.
const CRANE_ART = { url: 'models/crane_refinery_755815ec.glb?v=755815ec', crane: [-9, 17.5], sx: -1, uturn: [-25, 17.5], drop: [5.85, -4.5], drop2: [3.35, -4.5], park: [7, -4.5], bakedPad: true };
const CRANE_ART_D98F602C = Object.assign({}, CRANE_ART, { url: 'models/crane_refinery_d98f602c.glb?v=d98f602c', bakedPad: false });
const CRANE_ART_AFFEA57 = { url: 'models/crane_refinery_d1e577ce.glb?v=d1e577ce', crane: [-2, 17.5], sx: 1, uturn: [-8, 17.5], drop: [-1.15, -4.5], drop2: [-3.65, -4.5], park: [0, -4.5] };
const CRANE = Q.get('crane') === 'affea57' ? CRANE_ART_AFFEA57 : Q.get('crane') === 'd98f602c' ? CRANE_ART_D98F602C : CRANE_ART;
CPH.ref.crane = CRANE.crane; CPH.ref.uturn = CRANE.uturn; if (CRANE.sx > 0) { CPH.road.x0 = RX - 8; CPH.road.n = 21; }
const RC_SLOTS = [[4.8, .15, -.725], [7.3, .15, -.725], [4.8, .15, .725], [7.3, .15, .725], [4.8, 1.65, -.725], [7.3, 1.65, -.725], [4.8, 1.65, .725], [7.3, 1.65, .725]].map(([x, y, z]) => [x * CRANE.sx, y, z]);   // crane-local
// Concrete pad under the pallet (Director 21:10: plain, ≤ 0.15 m). Art will likely add it to the crane GLB; until a mesh named like 'Pallet_Pad' /
// 'Concrete' is in the GLB this gray 0.12 m placeholder stands under the pallet (+0.5 m in x; z held inside the 3.4 m median, clear of both lanes).
const PALLET_PAD = { placeholder: !CRANE.bakedPad && Q.get('pad') !== 'off', h: 0.12, margin: 0.5, zMin: 15.8, zMax: 19.2, re: /pallet_?pad|concrete|^pad$/i };
const findA = (root, names) => { for (const n of names) { const o = root.getObjectByName(n); if (o) return o; } return null; };
const CG_LOG = [];
function cgEv(e, t, x) { CG_LOG.push(Object.assign({ e, at: t }, x || {})); if (CG_LOG.length > 200) CG_LOG.shift(); }
// ref = boxes on the Refinery pallet (sealing or sealed: their ready times), full = dumps that made no box because the pallet was full,
// sh.req = Launch button tap time (partial launch; 0 = none)
function cgInit(t) { return { v: 1, t, ref: [], made: 0, full: 0, sold: 0, launches: 0, earned: 0, rc: 0, fb: { st: 'load', t0: t, bed: 0 }, pc: { k: '', t0: 0 }, as: { st: 'home', t0: t }, bay: 0,
  sh: { st: 'pad', t0: t, hold: 0, f0: t, req: 0 } }; }
if (!S.cg || S.cg.v !== 1) S.cg = cgInit(S.rt);   // saves from before the cargo loop: it starts empty at the last save time (no back-pay for old dumps)
if (!(S.cg.full >= 0)) S.cg.full = 0; if (!(S.cg.sh.req >= 0)) S.cg.sh.req = 0;   // a6a00d3 saves

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
function cgMake(tDump) {           // called at the dump time, after the cargo sim has been settled up to it (so the pallet count is exact)
  const c = S.cg; if (c.ref.length >= CG.palletCap) { c.full++; cgEv('dump_pallet_full', tDump, { full: c.full }); return; }   // truck still pays; no box
  c.ref.push(tDump + CG.sealSec * 1000); c.made++; cgEv('box_made', tDump);
}
function cgDecide(c, t, acc) {      // acc = away catch-up (Director 23:00): the ship never auto-launches while the player is away; a full ship waits for a Launch tap (sh.man)
  for (let g = 0; g < 50; g++) {
    let ch = false; const f = c.fb, s = c.sh;
    if (!c.rc && f.st === 'load' && f.bed < CG.perTrip && c.ref.length && c.ref[0] <= t) { c.ref.shift(); c.rc = t; ch = true; cgEv('ref_crane_lift', t, { slot: f.bed + 1 }); }
    if (!c.rc && f.st === 'load' && f.bed >= CG.perTrip && c.bay + f.bed <= CG.bayCap) { c.fb = { st: 'out', t0: t, bed: f.bed }; ch = true; cgEv('fb_depart', t, { bed: f.bed }); }
    if (!c.pc.k) {
      if (c.fb.st === 'unload' && c.as.st === 'ready' && c.fb.bed > 0 && c.bay < CG.bayCap) { c.fb.bed--; c.pc = { k: 'unload', t0: t }; ch = true; cgEv('pad_crane_unload', t, { slot: c.fb.bed + 1 }); }
      else if (s.st === 'pad' && !s.req && c.bay > 0 && s.hold < CG.holdCap) { c.bay--; c.pc = { k: 'hold', t0: t }; ch = true; cgEv('pad_crane_hold', t, { slot: s.hold + 1 }); }
    }
    if (c.fb.st === 'unload' && c.fb.bed === 0 && c.pc.k !== 'unload' && c.as.st === 'ready') { c.fb = { st: 'back', t0: t, bed: 0 }; c.as = { st: 'walk_back', t0: t }; ch = true; cgEv('fb_return', t); }
    if (acc && s.st === 'pad' && s.hold >= CG.holdCap && !s.man) { s.man = 1; ch = true; cgEv('full_wait_manual', t, { hold: s.hold }); }   // came full while away: stays on the pad until tapped (also after the return)
    if (s.st === 'pad' && c.pc.k !== 'hold' && t >= s.f0 + CG.fuelFillSec * 1000 && ((s.hold >= CG.holdCap && !acc && !s.man) || (s.req && t >= s.req && s.hold >= 1))) {   // full hold (live only), or the Launch button (partial or a full ship that waited)
      c.sh = Object.assign({}, s, { st: BOARD_SEC ? 'board' : 'launch', t0: t, req: 0, man: 0 }); ch = true; cgEv(BOARD_SEC ? 'board' : 'launch', t, { hold: s.hold, partial: s.hold < CG.holdCap }); }   // the crew boards first (BOARD_SEC), then the launch
    else if (s.st === 'pad' && s.req && t >= s.req && s.hold < 1) { s.req = 0; ch = true; }
    if (!ch) break;
  }
}
function cgNext(c) {
  let n = Infinity; const T = (x) => { if (x < n) n = x; }, s = c.sh;
  if (c.rc) T(c.rc + CG.refLoadSec * 1000); else if (c.fb.st === 'load' && c.fb.bed < CG.perTrip && c.ref.length && c.ref[0] > c.t) T(c.ref[0]);
  if (c.fb.st === 'out') T(c.fb.t0 + FB.kOut.T * 1000); else if (c.fb.st === 'back') T(c.fb.t0 + FB.kBack.T * 1000);
  if (c.as.st === 'walk_out' || c.as.st === 'walk_back') T(c.as.t0 + (c.as.st === 'walk_out' ? CG.walkOutSec : CG.walkBackSec) * 1000);
  if (c.pc.k) T(c.pc.t0 + (c.pc.k === 'unload' ? CG.padUnloadSec : CG.holdLoadSec) * 1000);
  if (s.st === 'board') T(s.t0 + BOARD_SEC * 1000); else if (s.st === 'launch') T(s.t0 + CG.launchSec * 1000); else if (s.st === 'away') T(s.t0 + CG.awaySec * 1000); else if (s.st === 'land') T(s.t0 + CG.landSec * 1000);
  else { if (s.hold >= CG.holdCap && c.pc.k !== 'hold' && s.f0 + CG.fuelFillSec * 1000 > c.t) T(s.f0 + CG.fuelFillSec * 1000); if (s.req > c.t) T(s.req); }
  return n;
}
function cgComplete(c, t, acc) {
  if (c.rc && c.rc + CG.refLoadSec * 1000 <= t) { c.rc = 0; c.fb.bed++; cgEv('bed_loaded', t, { bed: c.fb.bed }); }
  if (c.fb.st === 'out' && c.fb.t0 + FB.kOut.T * 1000 <= t) { c.fb = { st: 'unload', t0: t, bed: c.fb.bed }; c.as = { st: 'walk_out', t0: t }; cgEv('fb_at_pad', t, { bed: c.fb.bed }); }
  else if (c.fb.st === 'back' && c.fb.t0 + FB.kBack.T * 1000 <= t) { c.fb = { st: 'load', t0: t, bed: 0 }; cgEv('fb_at_refinery', t); }
  if (c.as.st === 'walk_out' && c.as.t0 + CG.walkOutSec * 1000 <= t) { c.as = { st: 'ready', t0: t }; cgEv('astro_ready', t); }
  else if (c.as.st === 'walk_back' && c.as.t0 + CG.walkBackSec * 1000 <= t) { c.as = { st: 'home', t0: t }; cgEv('astro_home', t); }
  if (c.pc.k && c.pc.t0 + (c.pc.k === 'unload' ? CG.padUnloadSec : CG.holdLoadSec) * 1000 <= t) {
    if (c.pc.k === 'unload') { c.bay++; cgEv('checked_in_bay', t, { bay: c.bay }); } else { c.sh.hold++; cgEv('hold_loaded', t, { hold: c.sh.hold }); }
    c.pc = { k: '', t0: 0 };
  }
  const s = c.sh;
  if (s.st === 'board' && s.t0 + BOARD_SEC * 1000 <= t) { c.sh = Object.assign({}, s, { st: 'launch', t0: s.t0 + BOARD_SEC * 1000 }); cgEv('launch', s.t0 + BOARD_SEC * 1000, { hold: s.hold, partial: s.hold < CG.holdCap, board: BOARD_SEC }); }   // crew inside: lift-off
  else if (s.st === 'launch' && s.t0 + CG.launchSec * 1000 <= t) {        // top of the climb: the hold sells
    const v = s.hold * CG.boxValue, amt = acc && !acc.full ? v * CFG.offlineRate : v; S.money += amt; c.sold += s.hold; c.earned += amt; c.launches++;
    cgEv('sold', t, { boxes: s.hold, amt }); logU('truck', `Cargo ship sold ${s.hold} He-3 boxes, +${fmt(amt)}`);
    if (acc) acc.cargo = (acc.cargo || 0) + amt; else cargoPop(amt);
    c.sh = { st: 'away', t0: t, hold: 0, f0: s.f0, req: 0 };
  } else if (s.st === 'away' && s.t0 + CG.awaySec * 1000 <= t) { c.sh = { st: 'land', t0: t, hold: 0, f0: s.f0, req: 0 }; cgEv('landing', t); }
  else if (s.st === 'land' && s.t0 + CG.landSec * 1000 <= t) { c.sh = { st: 'pad', t0: t, hold: 0, f0: t, req: 0 }; cgEv('landed', t); }   // refuelling starts on touchdown
}
function cgSettle(T, acc) {
  const c = S.cg; if (!FB.kOut) return;
  for (let g = 0; g < 200000; g++) {
    cgDecide(c, c.t, acc);
    const nx = cgNext(c); if (!(nx <= T)) break;
    c.t = Math.max(c.t, nx); cgComplete(c, c.t, acc);
  }
}
function cgShift(d) { const c = S.cg; c.t += d; c.ref = c.ref.map(x => x + d); if (c.rc) c.rc += d; c.fb.t0 += d; if (c.pc.k) c.pc.t0 += d; c.as.t0 += d; c.sh.t0 += d; c.sh.f0 += d; if (c.sh.req) c.sh.req += d; }
const fuelAt = (t) => { const s = S.cg.sh; return s.st === 'pad' ? clamp((t - s.f0) / (CG.fuelFillSec * 1000), 0, 1) : s.st === 'launch' ? 1 : 0; };   // PLACEHOLDER fuel: fills over fuelFillSec from touchdown
const fuelGauge = (t) => { const s = S.cg.sh; return s.st === 'pad' ? fuelAt(t) : s.st === 'board' ? 1 : s.st === 'launch' ? clamp(1 - (t - s.t0) / (CG.launchSec * 1000), 0, 1) : 0; };   // HUD fuel gauge: fuelAt on the pad (f0 = touchdown), drains over the climb, empty while away/landing
const canLaunch = (t = nowMs()) => { const s = S.cg.sh; return s.st === 'pad' && !s.req && s.hold >= 1 && fuelAt(t) >= 1; };
function cgLaunch() {                 // Launch button: stored as a timestamp in S.cg (sh.req); the sim launches at it (after a lift into the hold finishes)
  const t = nowMs(); if (RT.ready && t >= S.rt - 1000 && t - S.rt < 60000) { settleTo(t, null); S.rt = t; }
  if (!canLaunch(t)) return false;
  S.cg.sh.req = Math.max(t, S.cg.t); cgEv('launch_tap', t, { hold: S.cg.sh.hold }); settleTo(t, null); save();
  if (pointBeat === 'launch') pointerDone = true; return true;
}
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
  const b = new THREE.Object3D(); b.name = 'Base'; const h = new THREE.Object3D(); h.name = 'Hook_Point'; h.position.y = 1.5; g.add(b, h); return g;
}
function phFlatbed() {
  const g = new THREE.Group(); g.name = 'FB05'; g.userData.wheel_radius = 0.5;
  const body = shadowy(new THREE.Mesh(merged([geoAt(new THREE.BoxGeometry(7.4, .45, 2.3), 0, .75, 0), geoAt(new THREE.BoxGeometry(1.9, 1.8, 2.4), 2.65, 1.85, 0),
    geoAt(new THREE.BoxGeometry(5.3, .2, 2.6), -1.0, 1.08, 0)]), fbMat)); body.name = 'FB05_Body'; g.add(body);
  const wg = new THREE.CylinderGeometry(.5, .5, .42, 14).rotateX(Math.PI / 2), wm = new THREE.InstancedMesh(wg, cgDark, 6); wm.name = 'Wheel_All'; wm.castShadow = true; g.add(wm);
  g.userData.wheelPos = [[2.6, .5, 1.2], [2.6, .5, -1.2], [-.7, .5, 1.2], [-.7, .5, -1.2], [-2.5, .5, 1.2], [-2.5, .5, -1.2]];
  const s1 = new THREE.Object3D(); s1.name = 'Bed_Slot_01'; s1.position.set(-1.15, 1.18, 0); const s2 = new THREE.Object3D(); s2.name = 'Bed_Slot_02'; s2.position.set(-3.65, 1.18, 0); g.add(s1, s2);
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
  for (const [n, p] of Object.entries(markers)) { const m = new THREE.Object3D(); m.name = n; if (p.length === 3) m.position.set(p[0], p[1], p[2]); else m.position.set(p[0], 0, p[1]); g.add(m); }
  return g;
}
function phShip() {
  const g = new THREE.Group(); g.name = 'Ship_Placeholder';
  const parts = [geoAt(new THREE.CylinderGeometry(2, 2, 7, 20), 0, 4.1, 0), geoAt(new THREE.ConeGeometry(2, 2.4, 20), 0, 8.8, 0), geoAt(new THREE.BoxGeometry(3.4, .3, 7.8), -3.9, .3, 0)];
  for (const [x, z] of [[1.7, 1.7], [-1.7, 1.7], [1.7, -1.7], [-1.7, -1.7]]) parts.push(geoAt(new THREE.BoxGeometry(.35, 1.2, .35), x, .6, z));
  g.add(shadowy(new THREE.Mesh(merged(parts), cgMat)));
  for (let i = 0; i < 10; i++) { const m = new THREE.Object3D(), w = i % 6; m.name = 'Hold_' + String(i + 1).padStart(2, '0');   // He-3 boxes (2.3 × 1.5 × 1.3) long axis along z: 2 × 3 × 2 layers
    m.position.set(w % 2 ? -4.65 : -3.2, .45 + Math.floor(i / 6) * 1.5, (Math.floor(w / 2) - 1) * 2.5); m.rotation.y = Math.PI / 2; g.add(m); }
  return g;
}
function buildCargoProps() {
  // Refinery crane + box pallet
  const rp = CPH.ref, rcm = { Pick_Point: RC_SLOTS[0], Drop_Point: [CRANE.drop[0], 1.18, CRANE.drop[1]], Drop_Point_02: [CRANE.drop2[0], 1.18, CRANE.drop2[1]], Truck_Park: [CRANE.park[0], 0, CRANE.park[1]] }; RC_SLOTS.forEach((p, i) => rcm['Pallet_Slot_0' + (i + 1)] = p);
  const rc = phCrane('Crane_Refinery', rp.mast, rp.jib, rcm);
  rc.position.set(RX + rp.crane[0], 0, rp.crane[1]); scene.add(rc);
  const pal = shadowy(new THREE.Mesh(geoAt(new THREE.BoxGeometry(5.4, .15, 3.2), 0, .075, 0), cgDark)); pal.position.set(RX + rp.crane[0] + 6.05 * CRANE.sx, 0, rp.crane[1]); pal.name = 'Pallet_PLACEHOLDER'; scene.add(pal);
  // Launch Pad group (gray slab from the station placeholders + bay + crane + ship + astronaut + fuel gauge); bounds-fit framing
  const pp = CPH.pad, pg = new THREE.Group(); pg.name = 'LaunchPad_Placeholder'; pg.position.set(PX, 0, 0); scene.add(pg);
  if (phBox[PADI]) { scene.remove(phBox[PADI]); phBox[PADI].position.set(0, .5, 0); pg.add(phBox[PADI]); }
  const bay = shadowy(new THREE.Mesh(merged([geoAt(new THREE.BoxGeometry(7.6, .25, 6.2), 0, .125, 0), geoAt(new THREE.BoxGeometry(7.6, 1.2, .25), 0, .6, -3.1),
    geoAt(new THREE.BoxGeometry(.25, 1.2, 6.2), -3.8, .6, 0)]), cgMat)); bay.name = 'Cargo_Bay'; bay.position.set(pp.bay[0], 0, pp.bay[1]); pg.add(bay);
  const pc = phCrane('Crane_Pad', pp.mast, pp.jib, { Pick_Point: [pp.unload[0] - pp.crane[0], pp.unload[1] - pp.crane[1]], Drop_Point: [pp.bay[0] - pp.crane[0], pp.bay[1] - pp.crane[1]] });
  pc.position.set(pp.crane[0], 0, pp.crane[1]); pg.add(pc);
  const ship = phShip(); ship.position.set(PX + pp.ship[0], pp.padTop, pp.ship[1]); scene.add(ship);
  // marker empties named like Art's Launch Pad GLB (verify json, 92bb381 — not wired: being redone), so its drop-in takes the same path
  const emp = (n, x, y, z) => { const m = new THREE.Object3D(); m.name = n; m.position.set(x, y, z); pg.add(m); return m; };
  emp('Receiver_Spot', pp.receive[0], 0, pp.receive[1]); emp('Receiver_Home', pp.home[0], 0, pp.home[1]);
  emp('Truck_Stop', pp.unload[0], 0, pp.unload[1]); emp('Turn_Start', pp.uturn[0], 0, CPH.lanes.out); emp('Ship_Center', pp.ship[0], pp.padTop, pp.ship[1]);
  for (let i = 0; i < 12; i++) emp('Bay_Slot_' + String(i + 1).padStart(2, '0'), -10.1 + (i % 3) * 2.6, .3, 6.65 - Math.floor(i / 3) * 1.6);   // = Art 4017f16 CB-1 grid
  const astro = new THREE.Group(); astro.name = 'Astronaut_Placeholder';
  astro.add(shadowy(new THREE.Mesh(merged([geoAt(new THREE.CapsuleGeometry(.36, 1.0, 4, 10), 0, .86, 0), geoAt(new THREE.BoxGeometry(.4, .22, .3), .22, 1.42, 0)]),
    new THREE.MeshStandardMaterial({ color: 0xf2f2ee, roughness: .6 })))); scene.add(astro);
  const fuelBack = new THREE.Mesh(geoAt(new THREE.BoxGeometry(.6, 6, .5), 0, 3, 0), cgDark); fuelBack.position.set(pp.fuel[0], 0, pp.fuel[1]); pg.add(fuelBack);
  const fuelFill = new THREE.Mesh(geoAt(new THREE.BoxGeometry(.45, 1, .56), 0, .5, 0), new THREE.MeshStandardMaterial({ color: 0xffb340, emissive: 0xff7a00, emissiveIntensity: .9 }));
  fuelFill.name = 'Fuel_Gauge_PLACEHOLDER'; fuelFill.position.set(pp.fuel[0], .05, pp.fuel[1]); pg.add(fuelFill);
  const frame = new THREE.Mesh(geoAt(new THREE.BoxGeometry(24, 11, 19), -6, 5.5, 4.6), new THREE.MeshBasicMaterial({ visible: false })); frame.name = 'PadFrame'; pg.add(frame);   // framing incl. the ship on the pad and FB-05 at the unload spot
  // flatbed + boxes
  const fb = phFlatbed(); scene.add(fb);
  const boxes = new THREE.InstancedMesh(new THREE.BoxGeometry(2.3, 1.5, 1.3).translate(0, .75, 0), boxMat, 64); boxes.name = 'CargoBoxes'; boxes.castShadow = true; boxes.count = 0; scene.add(boxes);
  Object.assign(cg3, { rc, pc, pg, ship, astro, fuelFill, fb, pal, boxParts: [{ im: boxes, L: null }], bay });
  padFromMarkers(pg); cgBind(); stationObjs[PADI] = pg; fitSite(PADI); padRoadCheck();
}
// Launch Pad markers → layout + flatbed route (the placeholder's empties now; Art's pad GLB later, same names). World x is PX-relative, z is world.
const PAD_ALIAS = { stop: ['Truck_Stop', 'Truck_Park'], turn: ['Turn_Start'], ship: ['Ship_Center'], recv: ['Receiver_Spot', 'Receive_Point'], home: ['Receiver_Home', 'Astro_Home'],
  bay: (i) => ['Bay_Slot_' + String(i).padStart(2, '0')] };
function padFromMarkers(root) {
  root.updateMatrixWorld(true); const wp = (names) => { const o = findA(root, names); return o ? o.getWorldPosition(new THREE.Vector3()) : null; }, pp = CPH.pad, got = [];
  const st = wp(PAD_ALIAS.stop); if (st) { pp.unload = [st.x - PX, st.z]; got.push('Truck_Stop'); }
  const tu = wp(PAD_ALIAS.turn); if (tu) { pp.uturn = [tu.x - PX, pp.uturn[1]]; got.push('Turn_Start'); }
  const sc = wp(PAD_ALIAS.ship); if (sc) { pp.ship = [sc.x - PX, sc.z]; got.push('Ship_Center'); }
  const sl = []; for (let i = 1; i <= 12; i++) { const p = wp(PAD_ALIAS.bay(i)); if (p) sl.push(p); }
  cg3.baySlots = sl.length === 12 ? sl : null; if (cg3.baySlots) got.push('Bay_Slot_01..12');
  buildCargoRoute(); (window.__ps3d = window.__ps3d || {}).padMarkers = got; return got;
}
// Jacob rule: nothing of the pad stands in the road band (+ 1 m). Every ground-level mesh of the pad group, the ship and the station-3 slab is checked;
// the crane's slewing jib / trolley / hook are overhead (they must swing over FB-05) and are skipped. Result in __ps3d.padRoad; violations are console errors.
function padRoadCheck() {
  const B = CPH.padRoad, z0 = B.z0 - B.clear, z1 = B.z1 + B.clear, bb = new THREE.Box3(), hits = [], roots = [cg3.pg, cg3.padArt ? null : cg3.ship, phBox[PADI]].filter(Boolean);
  const skip = (n) => { for (let q = n; q; q = q.parent) if (q.name === 'Slew' || q.name === 'Road_UTurn' || !q.visible) return true; return false; };   // overhead jib / the road's own U-turn / hidden tiers
  for (const r of roots) { r.updateMatrixWorld(true); r.traverse(n => { if (!n.isMesh || n.material.visible === false || skip(n)) return;
    bb.setFromObject(n); if (bb.min.y > 2.5) return; if (bb.max.z > z0 && bb.min.z < z1) hits.push({ name: n.name || (n.parent && n.parent.name) || '?', z: [+bb.min.z.toFixed(2), +bb.max.z.toFixed(2)], x: [+bb.min.x.toFixed(1), +bb.max.x.toFixed(1)] }); }); }
  let zMax = -Infinity; for (const r of roots) r.traverse(n => { if (!n.isMesh || n.material.visible === false || skip(n)) return; bb.setFromObject(n); if (bb.min.y <= 2.5) zMax = Math.max(zMax, bb.max.z); });
  const res = { ok: !hits.length, hits, padZMax: +zMax.toFixed(2), band: [B.z0, B.z1], clear: B.clear };
  window.__ps3d.padRoad = res; if (hits.length) console.error('Launch Pad intrudes on the flatbed road band', JSON.stringify(hits)); return res;
}
// read every joint / marker through the alias table (the placeholders above are named like the art, so this is the same path a GLB takes)
const BOXP = { hookY: 1.5 };
function cgBind() {
  const A = CARGO_ALIAS, bp = cg3.boxRoot || phBoxProp(), hp = findA(bp, A.boxHook), bb = findA(bp, A.boxBase); BOXP.hookY = hp && bb ? hp.position.y - bb.position.y : 1.5;
  const crane = (root, mast, jib) => { root.updateMatrixWorld(true); const sl = findA(root, A.slew), tr = findA(root, A.trolley), ho = findA(root, A.hoist), hk = findA(root, A.hook), pk = findA(root, A.pick), dp = findA(root, A.drop);
    const wp = (o) => o ? o.getWorldPosition(new THREE.Vector3()) : null, base = root.getWorldPosition(new THREE.Vector3());
    let u = null; root.traverse(n => { if (!u && n.userData && n.userData.sheave_y > 0) u = n.userData; });
    const glb = u ? { sheave: u.sheave_y, drop: u.hook_drop_m, rest: u.hook_rest_local_y, rmin: u.trolley_min_m, rmax: u.trolley_max_m, hmin: u.hoist_min_m || .6, hmax: u.hoist_max_m || 8.3 } : null;
    const slots = []; for (let i = 1; i <= 8; i++) { const o = findA(root, A.palletSlot(i)); if (o) slots.push(wp(o)); }
    if (glb) for (const o of [sl, tr, ho, hk]) if (o) o.userData.q0 = o.userData.q0 || o.quaternion.clone();
    return { root, sl, tr, ho, hk, cable: tr && tr.userData.cable, base, top: wp(sl).y, jib: glb ? glb.rmax : jib, rmin: glb ? glb.rmin : (root === cg3.rc ? CPH.ref.rmin : 1.2), glb, slots: slots.length === 8 ? slots : null, pick: wp(pk), drop: wp(dp) }; };
  cg3.RC = crane(cg3.rc, CPH.ref.mast, CPH.ref.jib); cg3.PC = crane(cg3.pc, CPH.pad.mast, CPH.pad.jib);
  if (cg3.padArt) { const w = (n) => { const o = cg3.pg.getObjectByName(n); return o ? o.getWorldPosition(new THREE.Vector3()) : null; };   // PC-1's targets are pad markers
    cg3.PC.pick = w('Pick_Point'); cg3.PC.drop = w('Drop_Point'); cg3.PC.hiUnload = CPH.pad.hiUnload; cg3.PC.hiHold = CPH.pad.hiHold; }
  const fb = cg3.fb, s1 = findA(fb, A.bedSlot1), s2 = findA(fb, A.bedSlot2);
  fb.position.set(0, 0, 0); fb.rotation.set(0, 0, 0); fb.updateMatrixWorld(true); const loc = (o) => o.getWorldPosition(new THREE.Vector3());   // slots in the flatbed root's space
  cg3.slots = [s1 ? loc(s1) : new THREE.Vector3(0, 1.2, 0), s2 ? loc(s2) : (s1 ? loc(s1).add(new THREE.Vector3(...A.bedSlot2Offset)) : new THREE.Vector3(-1.7, 1.2, 0))];
  const fr = findA(fb, A.flatbed) || fb; cg3.wheelR = fr.userData[A.wheelRadius] || fb.userData[A.wheelRadius] || 0.5; cg3.wheels = null; cg3.wheelNodes = null;
  fb.traverse(o => { if (o.isInstancedMesh && A.wheel.test(o.name)) cg3.wheels = o; });
  const wn = A.wheelNames.map(n => fb.getObjectByName(n)).filter(Boolean); if (wn.length) cg3.wheelNodes = wn.map(b => ({ b, q0: b.quaternion.clone() }));   // FB-05: spin about local +X
  cg3.holds = []; cg3.holdYaw = []; for (let i = 1; i <= CG.holdCap; i++) { const h = findA(cg3.ship, A.hold(i)); cg3.holds.push(h ? h.position.clone() : new THREE.Vector3(-3.5, .45, 0)); cg3.holdYaw.push(h ? h.rotation.y : 0); }
  cg3.pg.updateMatrixWorld(true); const rv = findA(cg3.pg, A.receive), hm = findA(cg3.pg, PAD_ALIAS.home);
  cg3.receive = rv.getWorldPosition(new THREE.Vector3()); cg3.home = hm.getWorldPosition(new THREE.Vector3());
}
// ---- per-frame poses (pure functions of S.cg and now)
const _Y = new THREE.Vector3(0, 1, 0), _cq2 = new THREE.Quaternion(), _cq = new THREE.Quaternion(), _cs = new THREE.Vector3(1, 1, 1), _cp = new THREE.Vector3(), _cm = new THREE.Matrix4(), _cv = new THREE.Vector3();
const FBS = { x: 0, z: 0, yaw: 0, v: 0, ph: 'load', wa: 0, wx: null, wz: 0 };
const lerp = (a, b, k) => a + (b - a) * k;
const lerpA = (a, b, k) => { let d = b - a; d = Math.atan2(Math.sin(d), Math.cos(d)); return a + d * k; };
function polar(C, p) { const dx = p.x - C.base.x, dz = p.z - C.base.z; return { a: Math.atan2(-dz, dx), r: clamp(Math.hypot(dx, dz), C.rmin || 1.2, C.jib) }; }
// crane cycle u 0..1: reach the pick (0–.15), lower (.15–.3), lift (.3–.45), slew + trolley to the drop (.45–.7), lower (.7–.85), let go, raise and go home (.85–1)
function cranePose(C, u, P, D, rest, hi = CPH.hookHi, hi0 = hi) {   // hi = carry hook height of this job, hi0 = rest hook height (PC-1: 4.4 rest/truck→bay, 15.7 bay→hold)
  let a, r, y, carry = false, k;
  const seg = (u0, u1) => fss((u - u0) / (u1 - u0));
  if (u < 0 || u >= 1 || !P) { a = rest.a; r = rest.r; y = hi0; }
  else { const p = polar(C, P), d = polar(C, D), py = P.y + BOXP.hookY, dy = D.y + BOXP.hookY;
    if (u < .15) { k = seg(0, .15); a = lerpA(rest.a, p.a, k); r = lerp(rest.r, p.r, k); y = lerp(hi0, hi, k); }
    else if (u < .3) { a = p.a; r = p.r; y = lerp(hi, py, seg(.15, .3)); }
    else if (u < .45) { a = p.a; r = p.r; y = lerp(py, hi, seg(.3, .45)); carry = true; }
    else if (u < .7) { k = seg(.45, .7); a = lerpA(p.a, d.a, k); r = lerp(p.r, d.r, k); y = hi; carry = true; }
    else if (u < .85) { a = d.a; r = d.r; y = lerp(hi, dy, seg(.7, .85)); carry = true; }
    else { k = seg(.85, 1); a = lerpA(d.a, rest.a, k); r = lerp(d.r, rest.r, k); y = lerp(dy, hi0, Math.min(1, k * 2)); } }
  if (C.glb) { const g = C.glb, L = clamp(g.sheave - y - g.drop, g.hmin, g.hmax);   // Art RC-1 solve (README): Slew θ, Trolley r, Hoist scale L, Hook y = rest + 1 − L, hook rotator keeps box yaw 0
    C.sl.quaternion.copy(C.sl.userData.q0).multiply(_cq2.setFromAxisAngle(_Y, a)); C.tr.position.x = r; C.ho.scale.y = L; C.hk.position.y = g.rest + 1 - L;
    C.hk.quaternion.copy(C.hk.userData.q0).multiply(_cq2.setFromAxisAngle(_Y, -a)); y = g.sheave - L - g.drop; }
  else { C.sl.rotation.y = a; C.tr.position.x = r; const drop = C.top - y; C.ho.position.y = -drop; if (C.cable) C.cable.scale.y = Math.max(.01, drop); }
  C.hookW = C.hookW || new THREE.Vector3(); C.hookW.set(C.base.x + r * Math.cos(a), y, C.base.z - r * Math.sin(a)); C.u = u;
  return carry;
}
let nBox = 0;
const _cm2 = new THREE.Matrix4();
function boxAt(p, yaw = 0) { if (nBox >= 64) return; _cq.setFromAxisAngle(_Y, yaw); _cm.compose(p, _cq, _cs);   // every part of the box (Art: SHM_Paint + SHM_GlowCyan) shares the instance index
  for (const b of cg3.boxParts) b.im.setMatrixAt(nBox, b.L ? _cm2.multiplyMatrices(_cm, b.L) : _cm); nBox++; }
const carryYaw = (u, y0, y1) => u < .45 ? y0 : u < .7 ? lerpA(y0, y1, fss((u - .45) / .25)) : y1;
const stackPos = (i, o = new THREE.Vector3()) => cg3.RC.slots ? o.copy(cg3.RC.slots[Math.min(i, 7)]) : o.set(cg3.RC.base.x + RC_SLOTS[i & 7][0], RC_SLOTS[i & 7][1], cg3.RC.base.z + RC_SLOTS[i & 7][2]);   // fill 01→08, pick 08→01
const bayPos = (i, o = new THREE.Vector3()) => { if (cg3.baySlots) return o.copy(cg3.baySlots[i % 12]).setY(cg3.baySlots[i % 12].y + Math.floor(i / 12) * 1.5); const b = cg3.PC.drop, w = i % 6; return o.set(b.x + (w % 2 ? 1.25 : -1.25), .25 + Math.floor(i / 6) * 1.5, b.z + (Math.floor(w / 2) - 1) * 1.45); };   // 2 × 3 × 2 = bayCap 12
function slotW(i, o = new THREE.Vector3()) { return o.copy(cg3.slots[i]).applyMatrix4(cg3.fb.matrixWorld); }
const _pk = new THREE.Vector3(), _dp = new THREE.Vector3(), _hw = new THREE.Vector3();
function fbPoseAt(c, t, o) {
  const f = c.fb; o.ph = f.st;
  if (f.st === 'load' || f.st === 'unload') { const p = f.st === 'load' ? FB.S : FB.U; o.x = p[0]; o.z = p[1]; o.yaw = 0; o.v = 0; return o; }
  const K = f.st === 'out' ? FB.kOut : FB.kBack, P = f.st === 'out' ? FB.pOut : FB.pBack; kinAt(K, (t - f.t0) / 1000, _ka); pathAt(P, _ka[0], o); o.v = _ka[1]; return o;
}
// ===== Art affea57 cargo props (Director-cleared 20:51): FB-05, HELIUM-3 box, RC-1 Refinery crane, Receiver. Each swaps its gray placeholder
// on load (same alias table / markers, so the sim and poses don't change); a GLB that fails keeps its placeholder.
const CART = { ok: { fb05: false, box: false, crane: false, receiver: false, pad: false }, err: [] };
// ===== Art 4017f16 Launch Pad (Director-cleared 21:50, md5 a82251e2…): pad origin = station origin (480, 0, 0). Everything comes from its empties:
// Truck_Stop / Turn_Start (+ Road_UTurn mesh), Ship_Center, Pick_Point(_02) / Drop_Point / Pick_Point_Bay / Bay_Slot_01..12, Hold_Door + Hold_01..10 (2 decks of 5),
// Receiver_Spot / Receiver_Home, PC-1 'Crane' (Slew/Trolley/Hoist/Hook, 360° slew, joint extras), cargo_door_open/close (2.0 s). The crane_* clips are proof-only.
const PAD_GLB = '../qa3d-next/models/launch_pad_82131aba.glb?v=82131aba';   // Art 6b5c76e (Director 06:02): flush hatch 833a339b + ship tone fix (stainless shadow #3a3e44, mid-blue stripe); was 0a5806f4
//   // Art 62a5dcb (md5 816f18f3…): own copy under qa3d-next/ so /qa3d/ keeps loading a82251e2
function padLoaded(g) {
  const o = g.scene; o.name = 'LaunchPad_Art'; o.position.set(PX, 0, 0);
  o.traverse(n => { if (n.isMesh) { n.castShadow = true; n.receiveShadow = true; } if (/^Tier_\d+/.test(n.name) || (n.userData && n.userData.hidden_by_default)) n.visible = false; });
  for (const n of ['Crane', 'Slew', 'Trolley', 'Hoist', 'Hook', 'Ship_Placeholder', 'Cargo_Door', 'Hold_Door', 'Truck_Stop', 'Receiver_Spot', 'Receiver_Home', 'Bay_Slot_12', 'Hold_10'])
    if (!o.getObjectByName(n)) throw new Error('pad marker ' + n + ' missing');
  scene.add(o); o.updateMatrixWorld(true);
  // the ship rig: hull + cargo door + door shelf + hold slots move together on launch / landing
  const hull = o.getObjectByName('Ship_Placeholder'), rig = new THREE.Group(); rig.name = 'Ship_Rig'; rig.position.copy(hull.position); o.add(rig); rig.updateMatrixWorld(true);
  for (const n of ['Ship_Placeholder', 'Cargo_Door', 'Hold_Door', ...Array.from({ length: CG.holdCap }, (_, i) => 'Hold_' + String(i + 1).padStart(2, '0'))]) rig.attach(o.getObjectByName(n));
  rig.traverse(m => { if (m.isMesh) m.frustumCulled = false; });
  const crane = o.getObjectByName('Crane'); crane.traverse(m => { if (m.isMesh) m.frustumCulled = false; });
  for (const n of ['Slew', 'Trolley', 'Hoist', 'Hook']) { const j = crane.getObjectByName(n); j.userData.q0 = j.quaternion.clone(); }
  // swap the gray placeholder group (slab, bay, crane, ship, gauge) out
  scene.remove(cg3.pg); scene.remove(cg3.ship); if (phBox[PADI]) phBox[PADI] = null;
  cg3.pg = o; cg3.pc = crane; cg3.ship = rig; cg3.shipY0 = rig.position.y; cg3.padArt = o;
  const hd = rig.getObjectByName('Hold_Door'); cg3.holdDoor = hd.position.clone(); cg3.holdDoorYaw = new THREE.Euler().setFromQuaternion(hd.quaternion, 'YXZ').y;
  // PC-1 heights from Art's poses (hook y = sheave − hoist − drop): rest / truck→bay carry at hoist 14.3 (hook 4.4), bay→hold carry at hoist 3.042 (hook 15.66)
  const cu = crane.userData; let poses = {}; try { poses = JSON.parse(cu.poses || '{}'); } catch (e) {}
  const hy = (L) => cu.sheave_y - L - cu.hook_drop_m; CPH.pad.hiUnload = hy(poses.pick_high ? poses.pick_high[2] : 14.3); CPH.pad.hiHold = hy(poses.hold_high ? poses.hold_high[2] : 3.042);
  // cargo door: open / close clips sampled from a 0..1 state (2.0 s each way)
  const mx = new THREE.AnimationMixer(o), ca = {}; for (const c of g.animations) if (/^cargo_door_(open|close)$/.test(c.name)) ca[c.name] = mx.clipAction(c);
  if (ca.cargo_door_open) cg3.door = { mx, ca, k: 0, last: 0, cur: '' };
  const before = CPH.pad.unload.join() + CPH.pad.uturn.join(); padFromMarkers(o);
  window.__ps3d.padRouteChanged = before !== CPH.pad.unload.join() + CPH.pad.uturn.join();   // false: the defaults already are this GLB's markers
  if (cg3.rx) { const rv = findA(o, CARGO_ALIAS.receive); cg3.rx.root.position.copy(rv.getWorldPosition(new THREE.Vector3())); cg3.rx.root.quaternion.copy(rv.getWorldQuaternion(new THREE.Quaternion())); }
  stationObjs[PADI] = o; o.userData.camTarget = camTargetOf(o); o.userData.camOv = camOvFor(PAD_GLB); fitSite(PADI); padRoadCheck(); window.__ps3d.pad = o;
}
function padDoor(open) {               // 2.0 s each way; open while PC-1 is on a bay→hold lift (the shelf takes the box), closes after
  const D = cg3.door, now = performance.now(), dt = D.last ? Math.min(.25, (now - D.last) / 1000) : 0; D.last = now;
  const k0 = D.k; D.k = clamp(D.k + (open ? dt : -dt) / 2, 0, 1); if (D.k === k0 && D.cur) return;
  const n = open || !D.ca.cargo_door_close ? 'cargo_door_open' : 'cargo_door_close', a = D.ca[n], dur = a.getClip().duration;
  if (D.cur !== n) { D.mx.stopAllAction(); a.play(); D.cur = n; }
  a.time = n === 'cargo_door_open' ? D.k * dur : (1 - D.k) * dur; D.mx.update(0);
}
function cartSwap(oldO, newO) { if (oldO && oldO.parent) oldO.parent.remove(oldO); scene.add(newO); }
function loadCargoArt() {
  const L = (key, url, fn) => loader.load(url, (g) => { try { fn(g); CART.ok[key] = true; cgBind(); } catch (e) { CART.err.push(key + ': ' + e.message); console.warn('cargo art ' + key + ' bind failed (placeholder stays)', e); } },
    undefined, (e) => { CART.err.push(key + ': load'); console.warn('cargo art ' + key + ' failed to load (placeholder stays)', e); });
  L('fb05', '../qa3d-next/models/fb05_195461ef.glb?v=195461ef', (g) => { const o = g.scene; o.name = 'FB05_Art'; o.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
    o.position.copy(cg3.fb.position); o.rotation.copy(cg3.fb.rotation); cartSwap(cg3.fb, o); cg3.fb = o; FBS.wx = null; });
  L('box', 'models/cargo_box_66a3a00c.glb?v=66a3a00c', (g) => { const o = g.scene; o.updateMatrixWorld(true); const parts = [];
    o.traverse(m => { if (m.isMesh) { const im = new THREE.InstancedMesh(m.geometry, m.material, 64); im.name = 'CargoBoxes_' + (m.material.name || parts.length); im.castShadow = true; im.receiveShadow = true; im.count = 0;
      parts.push({ im, L: m.matrixWorld.clone() }); } });
    if (!parts.length) throw new Error('no box mesh');
    for (const b of cg3.boxParts) scene.remove(b.im); for (const b of parts) scene.add(b.im); cg3.boxParts = parts; cg3.boxRoot = o; });
  L('crane', CRANE.url, (g) => { const o = g.scene; o.name = 'Crane_Refinery_Art'; o.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; m.frustumCulled = false; } });
    if (!o.getObjectByName('Slew') || !o.getObjectByName('Hook')) throw new Error('crane joints missing');
    o.position.set(RX + CPH.ref.crane[0], 0, CPH.ref.crane[1]); cartSwap(cg3.rc, o); cg3.rc = o; if (cg3.pal) { scene.remove(cg3.pal); cg3.pal = null; }   // the pallet is in the crane GLB
    let artPad = null; o.traverse(n => { if (!artPad && PALLET_PAD.re.test(n.name)) artPad = n; }); cg3.artPad = !!artPad; if (artPad && cg3.pad) { scene.remove(cg3.pad); cg3.pad.geometry.dispose(); cg3.pad = null; } cgPad(); });
  if (Q.get('launchpad') !== 'gray') L('pad', PAD_GLB, (g) => padLoaded(g));   // ?launchpad=gray keeps the gray placeholder pad (same markers)
  L('receiver', 'models/receiver_8c49ee31.glb?v=8c49ee31', (g) => { const o = g.scene; o.name = 'Receiver_Art'; o.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; m.frustumCulled = false; } });
    const mx = new THREE.AnimationMixer(o), acts = {}; for (const c of g.animations) acts[c.name] = mx.clipAction(c);
    for (const n of ['walk_out', 'guide', 'check_in', 'walk_back']) if (!acts[n]) throw new Error('clip ' + n + ' missing');
    cg3.pg.updateMatrixWorld(true); const rv = findA(cg3.pg, CARGO_ALIAS.receive), p = rv.getWorldPosition(new THREE.Vector3()), q = rv.getWorldQuaternion(new THREE.Quaternion());
    o.position.copy(p); o.quaternion.copy(q);   // Receive_Point at the bay (faces +Z: the flatbed on the z 13 lane); Home_Point = (−3, −1.5) from it
    cartSwap(cg3.astro, o); cg3.astro = o; cg3.rx = { root: o, mx, acts, cur: '' }; });
}
function rxPose(c, t, ap) {           // Receiver clips are sampled from S.cg timestamps (no drift, right after reloads/catch-up): walk_out 4.0 → guide loop → check_in 2.0 → walk_back 4.4
  const X = cg3.rx, a = c.as, el = (t - a.t0) / 1000; let n, x;
  if (a.st === 'walk_out') { n = 'walk_out'; x = el; }
  else if (a.st === 'walk_back') { n = 'walk_back'; x = el; }
  else if (a.st === 'ready') { if (ap === 'check_in') { n = 'check_in'; x = (t - c.pc.t0) / 1000 - (CG.padUnloadSec - CG.checkSec); } else { n = 'guide'; x = el % X.acts.guide.getClip().duration; } }
  else { n = 'walk_out'; x = 0; }         // home: walk_out frame 0 = walk_back's last frame (at the Home_Point)
  const act = X.acts[n], d = act.getClip().duration; x = clamp(x, 0, d - 1e-3);
  if (X.cur !== n) { X.mx.stopAllAction(); act.play(); act.setEffectiveWeight(1); X.cur = n; }
  act.time = x; X.mx.update(0);
}
function updCargo() {
  if (!cg3.fb || !FB.kOut) return; const c = S.cg, t = nowMs();
  fbPoseAt(c, t, FBS); const fb = cg3.fb; fb.position.set(FBS.x, 0, FBS.z); fb.rotation.set(0, FBS.yaw, 0); fb.updateMatrixWorld(true);
  if (FBS.wx !== null) { const dx = FBS.x - FBS.wx, dz = FBS.z - FBS.wz; if (Math.hypot(dx, dz) < 20) FBS.wa += (dx * Math.cos(FBS.yaw) - dz * Math.sin(FBS.yaw)) / cg3.wheelR; }   // roll by real distance
  FBS.wx = FBS.x; FBS.wz = FBS.z;
  if (cg3.wheelNodes) for (const w of cg3.wheelNodes) w.b.quaternion.copy(w.q0).multiply(_cq2.setFromAxisAngle(_X, FBS.wa));
  else if (cg3.wheels) { const W = cg3.wheels; fb.userData.wheelPos.forEach((p, i) => { _cq.setFromAxisAngle(_cv.set(0, 0, 1), -FBS.wa); W.setMatrixAt(i, _cm.compose(_cp.set(p[0], p[1], p[2]), _cq, _cs)); }); W.instanceMatrix.needsUpdate = true; }
  // ship
  const s = c.sh, sh = cg3.ship, pp = CPH.pad; let sy = cg3.shipY0 != null ? cg3.shipY0 : pp.padTop, vis = true;
  if (s.st === 'launch') { const u = clamp((t - s.t0) / (CG.launchSec * 1000), 0, 1); sy += 160 * u * u * u; }
  else if (s.st === 'away') vis = false;
  else if (s.st === 'land') { const u = clamp((t - s.t0) / (CG.landSec * 1000), 0, 1); sy += 160 * (1 - u) ** 3; }
  sh.visible = vis; sh.position.y = sy; sh.updateMatrixWorld(true);
  cg3.fuelFill.scale.y = Math.max(.01, 5.9 * fuelAt(t));
  // astronaut
  const ap = astroPhase(c, t), as = cg3.astro, H = cg3.home, Rv = cg3.receive; let ax, az, ay = 0, ayaw;
  if (cg3.rx) rxPose(c, t, ap); else {
  if (c.as.st === 'walk_out' || c.as.st === 'walk_back') { const out = c.as.st === 'walk_out', u = fss((t - c.as.t0) / ((out ? CG.walkOutSec : CG.walkBackSec) * 1000)); const A = out ? H : Rv, B = out ? Rv : H;
    ax = lerp(A.x, B.x, u); az = lerp(A.z, B.z, u); ay = .12 * Math.abs(Math.sin(u * Math.PI * 6)); ayaw = Math.atan2(-(B.z - A.z), B.x - A.x); }
  else if (c.as.st === 'ready') { ax = Rv.x; az = Rv.z; ayaw = Math.PI / 2 * -1; if (ap === 'check_in') ay = .05 * Math.sin(t / 90); }   // faces the bed (+z)
  else { ax = H.x; az = H.z; ayaw = Math.PI / 2 * -1; }
  as.position.set(ax, ay, az); as.rotation.y = ayaw; }
  // cranes + boxes
  nBox = 0; const RC = cg3.RC, PC = cg3.PC, now = t;
  const restR = { a: polar(RC, RC.pick).a + CPH.ref.rest[0], r: 3 }, restP = { a: polar(PC, PC.drop).a, r: PC.glb ? 6 : 5 };
  const ready = c.ref.length;           // the pallet shows every box on it (sealing ones included): up to palletCap, 2 layers of 4
  for (let i = 0; i < Math.min(ready, 8); i++) boxAt(stackPos(i, _cp));
  let u = -1; if (c.rc) { u = (now - c.rc) / (CG.refLoadSec * 1000); stackPos(ready, _pk); slotW(c.fb.bed, _dp); }
  const carryR = cranePose(RC, u, c.rc ? _pk : null, _dp, restR);
  if (c.rc && u >= 0) boxAt(u < .3 ? _pk : carryR ? _hw.copy(RC.hookW).setY(RC.hookW.y - BOXP.hookY) : _dp);
  for (let i = 0; i < c.fb.bed; i++) boxAt(slotW(i, _cp), FBS.yaw);
  for (let i = 0; i < c.bay; i++) boxAt(bayPos(i, _cp));
  if (vis) for (let i = 0; i < s.hold; i++) boxAt(_cp.copy(cg3.holds[i]).applyMatrix4(sh.matrixWorld), cg3.holdYaw[i]);
  let v = -1, P = null;
  if (c.pc.k) { v = (now - c.pc.t0) / ((c.pc.k === 'unload' ? CG.padUnloadSec : CG.holdLoadSec) * 1000);
    if (c.pc.k === 'unload') { slotW(c.fb.bed, _pk); bayPos(c.bay, _dp); } else { bayPos(c.bay, _pk); _dp.copy(cg3.holdDoor || cg3.holds[s.hold]).applyMatrix4(sh.matrixWorld); } P = _pk; }   // Art pad: onto the open door shelf (Hold_Door), lands in Hold_NN at the end
  const carryP = PC.hiUnload ? cranePose(PC, v, P, _dp, restP, c.pc.k === 'hold' ? PC.hiHold : PC.hiUnload, PC.hiUnload) : cranePose(PC, v, P, _dp, restP);
  if (cg3.door) padDoor(c.pc.k === 'hold' && s.st === 'pad');
  const py0 = c.pc.k === 'unload' ? FBS.yaw : 0, py1 = c.pc.k === 'unload' ? 0 : cg3.holdDoor ? cg3.holdDoorYaw : cg3.holdYaw[s.hold] || 0;
  if (P && v >= 0) boxAt(v < .3 ? _pk : carryP ? _hw.copy(PC.hookW).setY(PC.hookW.y - BOXP.hookY) : _dp, carryYaw(v, py0, py1));
  for (const b of cg3.boxParts) { b.im.count = nBox; b.im.instanceMatrix.needsUpdate = true; if (nBox) b.im.computeBoundingSphere(); }   // culled with the camera off-site
  window.__ps3d.cargoFrame = { boxes: nBox, astro: ap, rxClip: cg3.rx ? cg3.rx.cur : null, fb: FBS.ph, v: +FBS.v.toFixed(2), art: Object.keys(CART.ok).filter(k => CART.ok[k]) };
}
let cargoRoadMesh = null;
function buildCargoRoad() {         // Art's haul-road strip tiles (same as the Mine↔Refinery road), lanes z 13 / 22; flat temp tiles if the strip is not in
  if (cargoRoadMesh) scene.remove(cargoRoadMesh);
  const R0 = CPH.road, M = (i) => new THREE.Matrix4().makeTranslation(R0.x0 + R0.tile * i, 0, CPH.lanes.out);
  // the strip ends at x0 + n·tile (480); Art's pad Road_UTurn starts at Turn_Start (481): a 1 m filler (one tile scaled in x) closes the gap
  const xe = R0.x0 + R0.tile * R0.n, fill = Math.max(0, PX + CPH.pad.uturn[0] - xe), F = (z) => new THREE.Matrix4().makeTranslation(xe, 0, z).multiply(new THREE.Matrix4().makeScale(fill / R0.tile, 1, 1));
  if (roadSeg) { const nf = fill > .01 ? 1 : 0, im = new THREE.InstancedMesh(roadSeg.geo, roadSeg.mat, R0.n + nf); for (let i = 0; i < R0.n; i++) im.setMatrixAt(i, M(i).multiply(roadSeg.m));
    if (nf) im.setMatrixAt(R0.n, F(CPH.lanes.out).multiply(roadSeg.m)); im.receiveShadow = true; cargoRoadMesh = im; }
  else { const g = new THREE.PlaneGeometry(R0.tile, 4.6).rotateX(-Math.PI / 2).translate(R0.tile / 2, .03, 0), im = new THREE.InstancedMesh(g, new THREE.MeshStandardMaterial({ color: 0x55575c, roughness: .95 }), R0.n * 2);
    for (let i = 0; i < R0.n; i++) { im.setMatrixAt(2 * i, M(i)); im.setMatrixAt(2 * i + 1, M(i).premultiply(new THREE.Matrix4().makeTranslation(0, 0, CPH.lanes.back - CPH.lanes.out))); } im.receiveShadow = true; cargoRoadMesh = im; }
  cargoRoadMesh.computeBoundingSphere(); cargoRoadMesh.name = 'CargoRoad'; scene.add(cargoRoadMesh);
}
function cgMakeDue() {}   // (boxes are made inside settleTo at the exact dump time)
function cargoState() { const c = S.cg, t = nowMs(); return { made: c.made, dumpsFull: c.full, stack: c.ref.length, palletFull: c.ref.length >= CG.palletCap, bayFull: c.bay >= CG.bayCap,
  req: c.sh.req, canLaunch: canLaunch(t), launchBtn: !!(launchEl && launchEl.classList.contains('on')), storeChip: !!(storeEl && storeEl.classList.contains('on')), sold: c.sold, launches: c.launches, earned: +c.earned.toFixed(2), refReady: c.ref.filter(x => x <= t).length, refSealing: c.ref.filter(x => x > t).length,
  refCrane: c.rc ? 'loading' : 'idle', bed: c.fb.bed, flatbed: c.fb.st, astro: astroPhase(c, t), padCrane: c.pc.k || 'idle', bay: c.bay, ship: c.sh.st, hold: c.sh.hold, fuel: +fuelAt(t).toFixed(3), gauge: +fuelGauge(t).toFixed(4), gaugeOn: !!(fgEl && fgEl.classList.contains('on')),
  simT: c.t, tripOut: FB.kOut && +FB.kOut.T.toFixed(2), tripBack: FB.kBack && +FB.kBack.T.toFixed(2), last: CG_LOG.slice(-6).map(e => e.e) }; }
function cgPad() {                    // placeholder concrete pad under the pallet (see PALLET_PAD); skipped when the crane GLB brings its own
  if (cg3.pad || cg3.artPad || !PALLET_PAD.placeholder) return;
  let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity; const v = new THREE.Vector3();
  for (let i = 0; i < 4; i++) { stackPos(i, v); x0 = Math.min(x0, v.x - 1.15); x1 = Math.max(x1, v.x + 1.15); z0 = Math.min(z0, v.z - .65); z1 = Math.max(z1, v.z + .65); }
  x0 -= PALLET_PAD.margin; x1 += PALLET_PAD.margin; z0 = Math.max(PALLET_PAD.zMin, z0 - PALLET_PAD.margin); z1 = Math.min(PALLET_PAD.zMax, z1 + PALLET_PAD.margin);
  const g = new THREE.BoxGeometry(x1 - x0, PALLET_PAD.h, z1 - z0); g.translate(0, PALLET_PAD.h / 2 - .005, 0);
  const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: 0x8a8c90, roughness: .97 })); m.position.set((x0 + x1) / 2, 0, (z0 + z1) / 2); m.receiveShadow = true; m.name = 'Pallet_Pad_PLACEHOLDER';
  scene.add(m); cg3.pad = m; cg3.padBox = { x0: +x0.toFixed(2), x1: +x1.toFixed(2), z0: +z0.toFixed(2), z1: +z1.toFixed(2), h: PALLET_PAD.h };
}
buildCargoRoute(); buildCargoProps(); buildCargoRoad(); loadCargoArt(); cgPad();
const launchEl = $('launchBtn'), storeEl = $('storeChip');
const fgEl = $('fuelG'), fgFill = fgEl.querySelector('.tr i'), fgLbl = fgEl.querySelector('b'), fgPct = fgEl.querySelector('em');
const FG = { on: false, x: -1, y: -1, q: -1, p: -1, k: '' };   // last written values: the gauge touches the DOM only when what it shows changes (no layout reads)
for (const el of [launchEl, storeEl]) el.addEventListener('pointerdown', (e) => e.stopPropagation());
launchEl.addEventListener('click', (e) => { e.stopPropagation(); if (cgLaunch()) { launchEl.classList.remove('on'); window.__ps3d.launchTaps = (window.__ps3d.launchTaps || 0) + 1; } });
const _sp = {};
function cargoUI() {                  // Launch button (bottom-right of the safe band, Launch Pad only) and the Storage full chip (over the Refinery pallet)
  const t = nowMs(), c = S.cg, live = !document.hidden && !sheetOpen && !document.body.classList.contains('sheet-drag'), bd = band();
  const onPad = live && S.site === PADI && Math.abs(camX - PX) < 3 && canLaunch(t);
  if (onPad) { const v = c.sh.hold * CG.boxValue; launchEl.querySelector('small').textContent = `${c.sh.hold}/${CG.holdCap} BOXES · +${fmt(v)}`;
    launchEl.style.top = Math.round(bd.bot - launchEl.offsetHeight) + 'px'; }
  launchEl.classList.toggle('on', onPad);
  const full = live && S.site === REF && Math.abs(camX - RX) < 3 && c.ref.length >= CG.palletCap;
  if (full && cg3.RC) { const p = toScreen(cg3.RC.pick.x, 2.6, cg3.RC.pick.z, camera, _sp), w = storeEl.offsetWidth || 120;
    storeEl.style.left = Math.round(clamp(p.x - w / 2, bd.l - 22, W - w - 12)) + 'px'; storeEl.style.top = Math.round(clamp(p.y - 34, bd.top, bd.bot - 30)) + 'px'; }
  storeEl.classList.toggle('on', !!full);
  // fuel gauge (Launch Pad only, top-left of the band): fill from S.cg.sh timestamps via fuelAt (same as the sim / canLaunch), so reload, away and ?speed=N stay exact
  const gOn = live && S.site === PADI && Math.abs(camX - PX) < 3;
  if (gOn !== FG.on) { FG.on = gOn; fgEl.classList.toggle('on', gOn); }
  if (!gOn) return;
  const x = Math.round(bd.l + 6), y = Math.round(bd.top + 6);
  if (x !== FG.x || y !== FG.y) { FG.x = x; FG.y = y; fgEl.style.transform = 'translate(' + x + 'px,' + y + 'px)'; }
  const f = fuelGauge(t), q = Math.round(f * 400), pc = Math.floor(f * 100 + 1e-9), st = c.sh.st;
  const k = st === 'pad' ? (f >= 1 ? (c.sh.hold >= 1 ? 'full' : 'wait') : 'fuel') : st;   // fuel / full / wait (full, 0 boxes: same S.cg.sh.hold as canLaunch) / launch / away / land
  if (q !== FG.q) { FG.q = q; fgFill.style.transform = 'scaleX(' + (q / 400) + ')'; }
  if (k !== FG.k) { FG.k = k; fgEl.classList.toggle('full', k === 'full' || k === 'wait'); fgEl.classList.toggle('wait', k === 'wait'); fgLbl.textContent = k === 'full' ? 'FUEL FULL' : k === 'wait' ? 'AWAITING CARGO' : k === 'board' ? 'BOARDING' : k === 'launch' ? 'BURN' : k === 'away' ? 'SHIP AWAY' : k === 'land' ? 'LANDING' : 'FUEL'; FG.p = -1; }
  if (pc !== FG.p) { FG.p = pc; fgPct.textContent = k === 'away' || k === 'land' ? '—' : pc + '%'; }
}

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
  { id: 'mine_first_view', tut: true, point: null, lines: ["Moonbase, this is Eve at Earth Coms. Good to hear you made it. Your truck is filling under the chute.",
    "Tap the dark ore patch and the drill drops a rich load into the bed. Over."] },
  { id: 'first_deposit', tut: false, point: null, lines: ["Rich load, nice. Once that truck is full it hauls to the Refinery and pays as the bed tips. Over."] },
  { id: 'upgrade_ready', tut: true, point: null, lines: ["You've got the cash for an upgrade. Bigger mine, bigger loads. Tap Upgrade."] },
  // Director 20:34: first launch only. Rings once the first flatbed trip (2 boxes) is in the hold and the tanks are full; points at Launch
  { id: 'cargo_early', tut: true, point: 'launch', lines: ["Moonbase, Eve here. Your first He-3 boxes are in the ship's hold and the tanks are full.",
    "Earth needs that shipment now. Don't wait for a full hold: tap Launch and send what's aboard. Over."] },
];
const EVE_TRIG = {
  mine_first_view: () => S.site === MINE && coverGone && Math.abs(camX - MX) < 1,
  first_deposit: () => S.dep >= 1,
  upgrade_ready: () => S.dep >= 1 && canPay(drillCost()) && !sheetOpen,
  cargo_early: () => S.cg.launches === 0 && S.cg.sh.hold >= CG.perTrip && canLaunch(),
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
  const g = !S.dep ? ['Send a rich load', 'Tap the dark ore patch', S.dep, 1] : S.loads < 3 ? ['Haul 3 loads to the Refinery', 'Loads delivered', S.loads, 3]
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
// optional recorded line audio (text stays the call; no TTS): plays CFG.eveVoice.lines[beat][line] only if a file is listed there
const EVA = { el: null };
function eveVoiceStop() { if (EVA.el) { EVA.el.pause(); EVA.el.onended = EVA.el.onerror = null; EVA.el = null; musicDuck(false); } }
function eveVoice(id, li) {
  eveVoiceStop(); const f = ((CFG.eveVoice.lines || {})[id] || [])[li]; if (!f) return;
  const a = new Audio(CFG.eveVoice.dir + f); a.volume = .9; EVA.el = a; musicDuck(true);
  a.onended = a.onerror = () => { if (EVA.el === a) { EVA.el = null; musicDuck(false); } };
  a.play().catch(() => { if (EVA.el === a) { EVA.el = null; musicDuck(false); } });
}
function sayLine(s) {
  if (!EC.call || s == null) return; EC.full = s; eveVoice(EC.call.id, EC.li); ecTxt.textContent = ''; ecPanel.classList.remove('is-waiting');
  if (ecReduced()) return lineDone();
  ecPanel.classList.add('is-talking'); ecTx.textContent = 'TRANSMITTING'; let i = 0;
  const step = () => { ecTxt.textContent = s.slice(0, ++i); if (i >= s.length) return lineDone(); const c = s[i - 1];
    EC.typing = setTimeout(step, /[.!?]/.test(c) && s[i] === ' ' ? ECM.stopMs : c === ',' ? ECM.commaMs : ECM.charMs); };
  step();
}
function lineDone() { clearTimeout(EC.typing); ecTxt.textContent = EC.full; ecPanel.classList.remove('is-talking'); ecPanel.classList.add('is-waiting'); ecTx.textContent = 'STANDING BY'; }
function ecHangUp() {
  const b = EC.call; clearTimeout(EC.typing); EC.call = null; eveVoiceStop();
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
  if (EC.ring && EC.ring.id === 'cargo_early' && S.cg.launches > 0) { ecResetUI(); EC.ring = null; hudDim(false); if (!S.eve.includes('cargo_early')) S.eve.push('cargo_early'); save(); }   // shipped before the call was answered
  if (!EC.ring && !EC.call && !ecIsOpen()) for (const b of EVE_BEATS) if (!S.eve.includes(b.id) && EVE_TRIG[b.id]()) { ecRing(b); break; }
  let p = null;
  if (pointBeat && !pointerDone) {
    if (pointBeat === 'launch') { if (S.cg.launches > 0) pointerDone = true; else if (launchEl.classList.contains('on')) { const r = launchEl.getBoundingClientRect(); p = _pt; p.x = r.left + r.width / 2; p.y = r.top + 2; p.l = 'LAUNCH'; p.up = false; } }
    if (pointBeat === 'upgrade') { const r = grab.getBoundingClientRect(); p = _pt; p.x = r.left + r.width / 2; p.y = r.top + 4; p.l = 'UPGRADE'; p.up = false; }
  }
  pointEl.style.display = p ? 'block' : 'none';
  if (p) { pointEl.style.left = p.x + 'px'; pointEl.style.top = p.y + 'px'; if (pointEl.firstChild.textContent !== p.l) pointEl.firstChild.textContent = p.l; if (pointEl._up !== p.up) { pointEl._up = p.up; pointEl.classList.toggle('up', p.up); } }
}

// ===== music (Director 20:35; tracks picked by Jacob 20:56, CC0, credits in audio/CREDITS.txt). Web Audio: unlocked on the first tap; each track is
// a buffer loop (sample-exact, gapless: the mp3s are LAME-tagged so decodeAudioData trims encoder delay/padding), played for whole loops ≈ dwellSec
// (2–3 min) and then crossfaded (xfadeSec) into the next; the list rotates and wraps. Only track 1 loads on the first tap; each next one loads while
// the current one plays. Quiet under SFX/Eve audio (musicDuck), Settings ▸ Music on/off is saved, suspended while hidden. Empty list = silent.
const MUS = { ctx: null, gain: null, bufs: [], cur: -1, v: null, switchAt: 0, loading: {}, ducked: false, err: [], started: false, plays: [] };
const musTracks = () => (CFG.music.tracks || []).filter(Boolean);
const musVol = () => (S.set.music === false ? 0 : CFG.music.vol * (MUS.ducked ? CFG.music.duckTo : 1));
function musSetGain(sec = .25) { if (!MUS.gain) return; const g = MUS.gain.gain, t = MUS.ctx.currentTime; g.cancelScheduledValues(t); g.setValueAtTime(g.value, t); g.linearRampToValueAtTime(musVol(), t + sec); }
function musLoad(i) {
  if (MUS.bufs[i] || MUS.loading[i]) return MUS.loading[i] || Promise.resolve(MUS.bufs[i]);
  return MUS.loading[i] = (async () => { try { const r = await fetch(CFG.music.dir + musTracks()[i]); if (!r.ok) throw new Error('HTTP ' + r.status);
    MUS.bufs[i] = await MUS.ctx.decodeAudioData(await r.arrayBuffer()); return MUS.bufs[i]; }
    catch (e) { MUS.err.push(musTracks()[i]); console.warn('music: skipped', musTracks()[i], e.message); return null; } finally { MUS.loading[i] = null; } })();
}
const musLoops = (d) => Math.max(1, Math.round(CFG.music.dwellSec / d));     // whole loops ≈ dwellSec
function musStart(i) {                // fade the current voice out and this one in over xfadeSec; the new one loops until its switch time
  const C = MUS.ctx, b = MUS.bufs[i], t = C.currentTime + .03, xf = MUS.v ? CFG.music.xfadeSec : .05;
  const src = C.createBufferSource(), g = C.createGain(); src.buffer = b; src.loop = true; src.connect(g); g.connect(MUS.gain);
  g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(1, t + xf); src.start(t);
  if (MUS.v) { const o = MUS.v; o.g.gain.cancelScheduledValues(t); o.g.gain.setValueAtTime(o.g.gain.value, t); o.g.gain.linearRampToValueAtTime(0, t + xf); o.src.stop(t + xf + .05); }
  MUS.v = { src, g, i, t0: t }; MUS.cur = i; MUS.plays.push(musTracks()[i]); if (MUS.plays.length > 12) MUS.plays.shift();
  MUS.switchAt = musTracks().length > 1 ? t + musLoops(b.duration) * b.duration - CFG.music.xfadeSec : Infinity;   // crossfade over the end of the last loop
  const n = musTracks().length; if (n > 1) musLoad((i + 1) % n);           // lazy: the next track loads while this one plays
}
function musTick() {
  if (!MUS.ctx || !MUS.v || MUS.ctx.state !== 'running' || MUS.ctx.currentTime < MUS.switchAt) return;
  const n = musTracks().length; let j = (MUS.cur + 1) % n;
  for (let k = 0; k < n && MUS.err.includes(musTracks()[j]); k++) j = (j + 1) % n;
  if (j === MUS.cur) { MUS.switchAt = Infinity; return; }
  if (MUS.bufs[j]) musStart(j); else { musLoad(j); MUS.switchAt += MUS.bufs[MUS.cur].duration; }   // not loaded yet: one more loop of the current track
}
setInterval(musTick, 250);
async function musPlay(i) {
  const n = musTracks().length;
  for (let k = 0; k < n; k++) { const j = (i + k) % n, b = await musLoad(j); if (b) { musStart(j); return; } }
}
function musUnlock() {                // first tap anywhere: create/resume the context inside the gesture (iOS)
  if (!musTracks().length || S.set.music === false || document.hidden) return;
  try { if (!MUS.ctx) { const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return; MUS.ctx = new AC(); MUS.gain = MUS.ctx.createGain(); MUS.gain.gain.value = 0; MUS.gain.connect(MUS.ctx.destination); }
    if (MUS.ctx.state !== 'running') MUS.ctx.resume();
    if (!MUS.started) { MUS.started = true; musPlay(0); } musSetGain(1.2); } catch (e) { console.warn('music unavailable', e.message); }
}
for (const ev of ['pointerdown', 'touchend', 'keydown']) addEventListener(ev, musUnlock, { capture: true, passive: true });
function musicDuck(on) { MUS.ducked = !!on; musSetGain(on ? .12 : .6); }   // SFX / Eve line audio call this
function setMusic(on) { S.set.music = !!on; save(); if (on) musUnlock(); else if (MUS.ctx) { musSetGain(.2); setTimeout(() => { if (S.set.music === false && MUS.ctx) MUS.ctx.suspend(); }, 260); } renderSettings(); }
document.addEventListener('visibilitychange', () => { if (!MUS.ctx) return; if (document.hidden) MUS.ctx.suspend(); else if (S.set.music !== false) { MUS.ctx.resume(); musSetGain(.6); } });
addEventListener('pagehide', () => { if (MUS.ctx) MUS.ctx.suspend(); });
// settings (gear under the Eve bubble): Music on/off
const setBtn = $('setBtn'), setPop = $('setPop'), musTgl = $('musTgl');
function renderSettings() { const on = S.set.music !== false; musTgl.setAttribute('aria-checked', on); musTgl.querySelector('b').textContent = on ? 'ON' : 'OFF';
  $('musNote').textContent = musTracks().length ? '' : 'No tracks yet'; }
for (const el of [setBtn, setPop]) el.addEventListener('pointerdown', (e) => e.stopPropagation());
setBtn.addEventListener('click', (e) => { e.stopPropagation(); renderSettings(); setPop.classList.toggle('on'); setBtn.setAttribute('aria-expanded', setPop.classList.contains('on')); });
musTgl.addEventListener('click', (e) => { e.stopPropagation(); setMusic(S.set.music === false); });
document.addEventListener('pointerdown', (e) => { if (setPop.classList.contains('on') && !e.target.closest('#setPop,#setBtn')) { setPop.classList.remove('on'); setBtn.setAttribute('aria-expanded', false); } });
renderSettings();

// ===== away catch-up: the truck loop is replayed from its timestamps; loads that tipped while away pay 50%, capped at 4 h
const awayEl = $('away');
$('awayOk').addEventListener('click', () => awayEl.classList.remove('on'));
awayEl.addEventListener('pointerdown', (e) => e.stopPropagation());
function catchUp(card) {
  if (!RT.ready) { RT.card = RT.card || card; return 0; }             // B1: replayed once the marker route is final (routeReady)
  const now = nowMs(), el = (now - S.rt) / 1000;
  if (!(el > 0)) { S.rt = now; window.__ps3d.lastAway = { sec: Math.round(el), X: 0 }; return 0; }   // clock set backward: nothing
  const acc = { base: 0, rich: 0, n: 0, full: el < CFG.offlineAfterSec }, capEnd = S.rt + CFG.offlineCapSec * 1000;
  if (now > capEnd) { settleTo(capEnd, acc); shiftTk(now - capEnd); } else settleTo(now, acc);   // past the cap the loop just resumes from where it stood
  S.rt = now; save();
  const X = acc.base + acc.rich + (acc.cargo || 0);
  if (card && !acc.full && Math.floor(X) >= 1) { $('awayAmt').textContent = '+' + fmt(X); awayEl.classList.add('on'); clearTimeout(catchUp.t);
    const arm = () => { if (!coverGone) { catchUp.t = setTimeout(arm, 100); return; } catchUp.t = setTimeout(() => awayEl.classList.remove('on'), 9000); }; arm(); }   // B9: 9 s counted from when the card can be seen
  window.__ps3d.lastAway = { sec: Math.round(el), X: +X.toFixed(2), loads: acc.n, cargo: +(acc.cargo || 0).toFixed(2), full: acc.full };
  return X;
}
function resync() {                   // bring the loop up to now before anything reads or draws it (frozen page, slow resume, QA reads)
  if (document.hidden || !RT.ready) return; const t = nowMs(); if (t < S.rt - 1000) { S.rt = t; return; }
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
  if (!document.hidden && RT.ready) { if ((now - S.rt) / 1000 > 60) catchUp(true); else { settleTo(now, null); S.rt = now; } }   // frozen page without a visibilitychange: away rules
  if (!drag) camX += (target - camX) * (1 - Math.exp(-dt * 9));
  updFocus(); updViewShift(); updCrew(); placeCamera();
  updCargo();
  updTruck();                         // poses the truck + sets its clips, then its mixer applies them this frame
  if (tMixer) tMixer.update(gdt);
  if (mixer) mixer.update(gdt);
  updOperator(gdt);
  for (const m of stationMixers) m.update(gdt);
  updFillArc();
  updDeposits(gdt, time); updRefDust(); updQueued(); updChunks(dt); updFx(dt); updTiers(dt);
  updEve(); updConveyor();
  uiT += dt; if (uiT > .1) { uiT = 0; hud(); sheetUI(); cargoUI(); }
  saveT += dt; if (saveT > CFG.saveEvery) { saveT = 0; save(); }
  renderer.render(scene, camera);
  if (DEV) {
    frames++; acc += dt;
    if (acc >= 0.5) { fps = frames / acc; hist.push([performance.now(), fps]); frames = 0; acc = 0;
      while (hist.length && performance.now() - hist[0][0] > 5000) hist.shift();
      const mn = Math.min(...hist.map(h => h[1]));
      devEl.textContent = `${fps.toFixed(0)}fps min${mn.toFixed(0)} · ${renderer.info.render.calls}dc · ${(renderer.info.render.triangles / 1000).toFixed(0)}k · ${TS.ph}`;
      const tg = $('tag').getBoundingClientRect(); devEl.style.left = (tg.width ? tg.right + 6 : 10) + 'px';   // B10: sits right of the version tag, never over it
      Object.assign(window.__ps3d, { fps, min5: mn, calls: renderer.info.render.calls, tris: renderer.info.render.triangles });
    }
  }
}
Object.defineProperties(window.__ps3d, Object.getOwnPropertyDescriptors({ renderer, scene, camera, rigScaleAt: rigScale, fxStep: updFx, tierStep: updTiers, get tierList() { return tiers; }, EVE_BEATS,
  get eveId() { return (EC.call || EC.ring || {}).id; }, get ec() { return { ring: EC.ring && EC.ring.id, call: EC.call && EC.call.id, open: ecIsOpen(), missed: S.missed, dim: hudEl.classList.contains('ec-hud-dim'), li: EC.li }; },
  ecAnswer: () => ecAnswer(), ecHangUp, ecOpen, sparks, S, CFG, goSite, STATIONS, deposits, spawnDeposit, catchUp, settleTo, tapDeposit, save, toScreen, drillCost, chuteCost, rate, fmt, depTapR, fillSec, fillAt, loadValue, oreMin, RT, R, TV, safeArea, band, poseAt, fbPoseAt, kinAt, pathAt, oreMinOf: oreMin, hallDoorCfg: CFG.hallDoor,
  buildRoute, MK, poseNow: () => { resync(); updTruck(); updCargo(); if (tMixer) tMixer.update(0); },
  get cargo() { return cargoState(); }, shiftTk, cgLaunch, cargoUI, setMusic, get music() { return { on: S.set.music !== false, tracks: musTracks().length, ctx: MUS.ctx ? MUS.ctx.state : 'none', cur: MUS.cur, ducked: MUS.ducked, plays: MUS.plays.slice(), switchIn: MUS.ctx && MUS.v ? +(MUS.switchAt - MUS.ctx.currentTime).toFixed(1) : null, loaded: MUS.bufs.map(b => !!b), gain: MUS.gain ? +MUS.gain.gain.value.toFixed(3) : 0, err: MUS.err.slice() }; }, musicDuck, musNext() { MUS.switchAt = 0; }, get eveVoice() { return EVA.el ? EVA.el.src : null; }, cg3, CART, FB, CPH, CARGO_ALIAS, get cargoLog() { return CG_LOG.slice(); },
  warpTo: (t) => { if (t > nowMs()) { if (HOLD !== null) HOLD = t; else WARP += t - nowMs(); settleTo(t, null); S.rt = nowMs(); } },
  hold: (on) => { if (on && HOLD === null) HOLD = rawMs(); else if (!on && HOLD !== null) { WARP += HOLD - rawMs(); HOLD = null; } return HOLD; }, TS, truckState: TS, poseAt, R, TV, RMK, get wheel() { return { ang: WH.a, dist: WH.d }; }, OP, CREW, SITECAM, CAM_OVERRIDE, stationObjs, tap, focusTier, FOCT, THREE, popXY, SPD, nowMs,
  get focus() { return { i: FOC.i, w: +FOC.w.toFixed(3), ph: FOC.ph, q: FOC.q.length, to: FOC.to && FOC.to.name, t: FOC.i < 0 ? 0 : +((performance.now() - FOC.seg0) / 1000).toFixed(2) }; },
  get stationLoops() { return stationMixers.flatMap(m => m._actions.map(a => a.getClip().name + ':' + (a.loop === THREE.LoopPingPong ? 'pingpong' : a.loop === THREE.LoopRepeat ? 'repeat' : a.loop))); },
  get camX() { return camX; }, get coverGone() { return coverGone; }, get eveOpen() { return ecIsOpen(); }, get cashTarget() { return cashTarget().id; }, get sheetOpen() { return sheetOpen; }, setSheet }));
buildRoute();                         // temporary (README fallback) route: drawn under the cover only; nothing settles on it (B1)
setTimeout(() => { if (!RT.ready) { console.warn('route markers still loading after 30 s: settling on the fallback route'); RT.mine = RT.ref = true; routeReady(); } }, 30000);
Object.defineProperties(window.__ps3d, Object.getOwnPropertyDescriptors({ BD, BC, BCAM, CAMLOOK, BOARD_SEC, crewCount, rxAlpha, makeFollowCam, boardOf, crewPose: crewPoseB, crewCamAt, crewCamW, updCrew, placeCamera, band,
  get crew() { return { tb: +BC.tb.toFixed(3), w: +BC.w.toFixed(4), ph: BC.ph, bc: S.bc || null, vis: !!(BD.root && BD.root.visible), cur: BD.cur }; } }));
hud(); sheetUI();
loadRig(); loadTruck(); loadOperator(); loadCrew();
frame();
