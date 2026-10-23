// Planet Stack 3D foundation (Step 2): flat ground, fixed camera, sideways swipe, lighting, placeholders, ?dev=1 fps readout.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

const Q = new URLSearchParams(location.search);
const DEV = Q.get('dev') === '1';
const SAVEKEY = DEV ? 'planetstack-qa3d-dev' : 'planetstack-qa3d';
if (Q.has('fresh')) try { localStorage.removeItem(SAVEKEY); } catch (e) {}
let S = { site: 1 };
try { Object.assign(S, JSON.parse(localStorage.getItem(SAVEKEY) || '{}')); } catch (e) {}
const save = () => { try { localStorage.setItem(SAVEKEY, JSON.stringify(S)); } catch (e) {} };

const STATIONS = ['Life Support', 'Mine', 'Takeoff & Landing', 'Cargo Space Dock', 'Habitat', 'Shipyard', 'Engineering'];
const GAP = 40;                       // meters between stations along X
const N = STATIONS.length;

// ---- renderer / scene
const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x05060b);

const camera = new THREE.PerspectiveCamera(38, 1, 0.5, 600);

// lights: hard low sun for long shadows, soft fill so shadow sides aren't black
const hemi = new THREE.HemisphereLight(0x9fb4d8, 0x2a2a30, 0.55); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff4e2, 2.6);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
sun.shadow.camera.left = -22; sun.shadow.camera.right = 22; sun.shadow.camera.top = 22; sun.shadow.camera.bottom = -22;
sun.shadow.camera.near = 1; sun.shadow.camera.far = 120;
sun.shadow.bias = -0.0005; sun.shadow.normalBias = 0.03;
scene.add(sun); scene.add(sun.target);

// ground: one flat plane with baked-in vertex-color mottling and crater rings (1 draw call)
{
  const W = GAP * (N - 1) + 200, D = 160, sx = 220, sz = 80;
  const g = new THREE.PlaneGeometry(W, D, sx, sz); g.rotateX(-Math.PI / 2);
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
  ground.position.set(GAP * (N - 1) / 2, 0, 0);
  ground.receiveShadow = true; scene.add(ground);
}
// stars (1 draw call)
{
  const n = 900, p = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const a = Math.random() * Math.PI * 2, e = .05 + Math.random() * 1.2, r = 400; p[i * 3] = GAP * 3 + Math.cos(a) * r * Math.cos(e); p[i * 3 + 1] = Math.sin(e) * r; p[i * 3 + 2] = -Math.abs(Math.sin(a)) * r * Math.cos(e) - 60; }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 1.2, sizeAttenuation: false })));
}

// gray placeholder boxes for every station except the Mine (which gets Art's drill rig)
const ph = new THREE.MeshStandardMaterial({ color: 0x8a8d94, roughness: .85, metalness: .05 });
const SIZES = [[10, 8, 8], null, [10, 1, 10], [14, 7, 9], [9, 12, 9], [12, 9, 10], [10, 10, 8]];
STATIONS.forEach((name, i) => {
  if (!SIZES[i]) return;
  const [w, h, d] = SIZES[i];
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), ph);
  m.position.set(i * GAP, h / 2, 0); m.castShadow = m.receiveShadow = true; scene.add(m);
});

// drill rig (Art 8ec3810, md5 c64f9a72…)
let mixer = null;
const loader = new GLTFLoader(); loader.setMeshoptDecoder(MeshoptDecoder);
loader.load('../art/3d/drill_rig/drill_rig.glb?v=c64f9a72', (gltf) => {
  const rig = gltf.scene; rig.position.set(1 * GAP, 0, 0);
  rig.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  scene.add(rig);
  mixer = new THREE.AnimationMixer(rig);
  const clip = THREE.AnimationClip.findByName(gltf.animations, 'dig') || gltf.animations[0];
  if (clip) mixer.clipAction(clip).play();
  window.__ps3d.rig = rig; window.__ps3d.clips = gltf.animations.map(a => a.name);
}, undefined, (e) => console.error('drill_rig load failed', e));

// ---- camera framing: keep ~18 m of width visible in portrait, rig (9.7 m) fully in frame
let camX = S.site * GAP, target = camX, W = 1, H = 1;
function resize() {
  W = innerWidth; H = innerHeight; renderer.setSize(W, H, false);
  camera.aspect = W / H;
  const halfW = 7, vt = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
  const dW = halfW / (vt * camera.aspect), dH = 7.2 / vt;        // fit width ~14 m, height ~14 m
  camera.userData.dist = Math.max(dW, dH, 16);
  camera.updateProjectionMatrix();
}
addEventListener('resize', resize); resize();
function placeCamera() {
  const d = camera.userData.dist;
  camera.position.set(camX, 3 + d * 0.12, d);
  camera.lookAt(camX, 5.2, 0);
  sun.position.set(camX - 30, 22, 18); sun.target.position.set(camX, 0, 0);
}

// ---- UI: tag, station name, dots, dev readout
document.getElementById('tag').textContent = document.body.dataset.tag + (DEV ? ' · ON' : '');
const nameEl = document.getElementById('name'), dotsEl = document.getElementById('dots');
STATIONS.forEach((n, i) => { const b = document.createElement('button'); b.setAttribute('aria-label', n); b.dataset.i = i; dotsEl.appendChild(b); });
function ui() { nameEl.textContent = STATIONS[S.site]; [...dotsEl.children].forEach((b, i) => b.classList.toggle('on', i === S.site)); }
function goSite(k) { k = Math.max(0, Math.min(N - 1, k)); if (k !== S.site) { S.site = k; save(); } target = k * GAP; ui(); }
dotsEl.addEventListener('pointerdown', (e) => {   // 44 px tap band: nearest dot wins
  e.stopPropagation(); const r = dotsEl.getBoundingClientRect(); const k = Math.round((e.clientX - r.left) / r.width * N - .5); goSite(k);
});
ui();

// ---- swipe: drag pans the camera 1:1, release snaps by distance or flick velocity
let drag = null;
canvas.addEventListener('pointerdown', (e) => { drag = { x: e.clientX, cx: camX, t: performance.now(), lx: e.clientX, lt: performance.now(), v: 0 }; canvas.setPointerCapture(e.pointerId); });
canvas.addEventListener('pointermove', (e) => {
  if (!drag) return; const now = performance.now();
  const mPerPx = (2 * camera.userData.dist * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect) / W;
  camX = Math.max(-GAP * .35, Math.min(GAP * (N - 1 + .35), drag.cx - (e.clientX - drag.x) * mPerPx)); target = camX;
  if (now > drag.lt) { drag.v = (e.clientX - drag.lx) / (now - drag.lt); drag.lx = e.clientX; drag.lt = now; }
});
const endDrag = () => {
  if (!drag) return; const moved = camX - drag.cx; let k = Math.round(camX / GAP);
  if (Math.abs(drag.v) > 0.35) k = drag.v < 0 ? Math.ceil(drag.cx / GAP + 0.01) : Math.floor(drag.cx / GAP - 0.01);
  else if (Math.abs(moved) > GAP * .18 && k === S.site) k = S.site + Math.sign(moved);
  drag = null; goSite(k);
};
canvas.addEventListener('pointerup', endDrag); canvas.addEventListener('pointercancel', endDrag);

// ---- loop + ?dev=1 readout (fps, min fps over last 5 s, draw calls, triangles)
const devEl = document.getElementById('dev'); devEl.hidden = !DEV;
const clock = new THREE.Clock(); let frames = 0, acc = 0, fps = 0; const hist = [];
renderer.info.autoReset = true;
function frame() {
  requestAnimationFrame(frame);
  const dt = Math.min(clock.getDelta(), 0.1);
  if (!drag) camX += (target - camX) * (1 - Math.exp(-dt * 9));
  placeCamera();
  if (mixer) mixer.update(dt);
  renderer.render(scene, camera);
  if (DEV) {
    frames++; acc += dt;
    if (acc >= 0.5) { fps = frames / acc; hist.push([performance.now(), fps]); frames = 0; acc = 0;
      while (hist.length && performance.now() - hist[0][0] > 5000) hist.shift();
      const mn = Math.min(...hist.map(h => h[1]));
      devEl.textContent = `${fps.toFixed(0)} fps · min5s ${mn.toFixed(0)} · ${renderer.info.render.calls} draws · ${(renderer.info.render.triangles / 1000).toFixed(1)}k tris`;
      window.__ps3d.fps = fps; window.__ps3d.min5 = mn; window.__ps3d.calls = renderer.info.render.calls;
    }
  }
}
window.__ps3d = { S, goSite, STATIONS };
frame();
