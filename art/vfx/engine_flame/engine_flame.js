// Planet Stack - engine flame VFX (LOX/CH4 in vacuum). Look proof by Art & Animation, 10/24/2026.
// Reusable: one flame per engine, any number of engines, fixed 4 draw calls total:
//   1 plume envelope (InstancedMesh, N instances)   2 core + Mach diamonds (InstancedMesh, N instances)
//   3 dust + vapour (one Points, hard cap DUST_CAP)  4 pad glow decal (one quad)
//   + 1 PointLight for the warm underside glow (no draw call; keep it in the scene at intensity 0 so no shader recompiles).
// No textures: the flame noise, diamonds, dust discs and glow are all procedural in tiny shaders.
import * as THREE from 'three';

export const FLAME = {
  R_EXIT: 0.86,          // m, bell exit radius (starter ship BELL_PROF)
  LEN: 30.0,             // m, plume envelope length at full thrust (24 -> 30, Director 10/24 13:38: run a bit longer)
  CORE_LEN: 13.0,        // m, white-hot core + diamond train length (9 -> 13 so the 4 diamonds sit inside it)
  DIAMOND_N: 4,          // Mach diamonds (3-5)
  DIAMOND_X0: 1.0,       // first knot at X0 * SP = 2.4 m below the exit (clear of the white-hot nozzle zone)
  DIAMOND_SP: 2.4,       // m between diamonds (1.7 -> 2.4: ~11 px apart at the 375 pad framing, so they read as separate knots)
  CROWD_REF: 6,          // engine count the look is tuned for (Lv1 ring); above it each plume is dimmed by 6/N (core sqrt)
  MAX_ENGINES: 12,       // instance capacity: Lv10 has 11; more engines never add draw calls (one InstancedMesh per layer)
  THRUST_STEP: 0.08,     // thrustLevel k: flame brightness and length x (1 + 0.08)^k (Lv3, 5, 7, 9 each add a step)
  DIAMOND_TIGHTEN: 0.95, // thrustLevel k: diamond spacing x 0.95^k (higher chamber pressure -> tighter knots)
  DUST_CAP: 150,         // hard particle cap (Director: <= 150)
  SPLASH_R: 5.6,         // deck splash sheet ends 5.6 m from the cluster centre (gear feet at 6.4 m, pad rim 6.21 m)
  SHAKE_PX: 1.0,         // ship-only horizontal rumble in screen px (camera never moves; Director: <= 2 px)
  HATCH_TO_LIFTOFF_MS: 2800,  // locked 10/24 13:38: hatch close 53.19 s, lift-off 55.99 s (tap-relative)
  IGN_AFTER_HATCH_MS: 800,    // ignition the moment the 0.8 s hatch clip ends (53.99 s). Parameter; must leave >= 1200 ms before lift-off.
  LAUNCH_MS: 8000, LAND_MS: 8000,   // existing CG.launchSec / CG.landSec (not changed)
  CLIMB_M: 160,          // existing climb: y = 160 * u^3 (launch), 160 * (1-u)^3 (land)
  GRAV: 1.62,            // Moon g for the grit
};

const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const sstep = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const easeOutCubic = (t) => 1 - Math.pow(1 - clamp(t, 0, 1), 3);
export const climbAlt = (tLift) => FLAME.CLIMB_M * Math.pow(clamp(tLift / FLAME.LAUNCH_MS, 0, 1), 3);
export const landAlt = (tTouch) => FLAME.CLIMB_M * Math.pow(1 - clamp((tTouch + FLAME.LAND_MS) / FLAME.LAND_MS, 0, 1), 3);

// ---------------------------------------------------------------- timelines (pure functions of time; reload-safe)
// launchState(t): t = ms relative to the existing lift-off event (negative = before). Ignition = -ignBeforeLiftoff()
// = hatch close + IGN_AFTER_HATCH_MS. Nothing shows before ignition, so the flame never exists while crew are outside.
export const ignBeforeLiftoff = () => Math.max(1200, FLAME.HATCH_TO_LIFTOFF_MS - FLAME.IGN_AFTER_HATCH_MS);   // 2000 ms with the locked numbers (2800 - 800)
export function launchState(t, crewOutside = false) {
  const I = -ignBeforeLiftoff(), alt = climbAlt(t);
  const s = { on: false, throttle: 0, len: 0, diamonds: 0, expand: 0, flash: 0, alt, shake: 0 };
  if (crewOutside || t < I || t > FLAME.LAUNCH_MS) return s;   // hard guard: never lit while anyone is outside the ship
  const k = t - I;                                   // ms since ignition
  // flicker-on: on 0-70, off 70-120, on 120-160, off 160-210, on from 210
  const lit = k < 70 || (k >= 120 && k < 160) || k >= 210;
  if (!lit) return s;
  s.on = true;
  s.flash = k < 300 ? 1 - k / 300 : 0;                // short bright flash
  s.len = k < 300 ? 0.22 + 0.08 * (k / 300) : 0.30 + 0.70 * easeOutCubic((k - 300) / 800);   // short -> full by ign+1100
  s.throttle = k < 300 ? 0.75 : 0.75 + 0.25 * sstep(300, 1100, k);
  s.diamonds = sstep(500, 1100, k) * (1 - sstep(5000, 7500, t));   // fade in with full length; fade out 5.0-7.5 s into the climb
  s.expand = sstep(3500, 8000, t);                   // vacuum widening as it climbs
  s.shake = sstep(0, 300, k) * (1 - sstep(800, 2000, t));   // rumble only near the pad
  return s;
}
// landState(t): t = ms relative to the existing touchdown event. The burn is lit for the whole landing (ship starts 160 m up,
// off screen), throttles 100% -> 45% at touchdown, cut-off at +220 ms, vapour puff at cut-off.
export const CUTOFF_MS = 220;
export function landState(t) {
  const alt = landAlt(t), s = { on: false, throttle: 0, len: 0, diamonds: 0, expand: 0, flash: 0, alt, shake: 0 };
  if (t < -FLAME.LAND_MS || t > CUTOFF_MS) return s;
  s.on = true;
  const thr = 1 - 0.55 * sstep(-4000, 0, t);
  const cut = t > 0 ? 1 - t / CUTOFF_MS : 1;
  s.throttle = thr * cut;
  s.len = (0.55 + 0.45 * thr) * (0.35 + 0.65 * cut);
  s.expand = 1 - sstep(-6000, -2500, t);
  s.diamonds = sstep(-5000, -2500, t) * (0.5 + 0.5 * thr) * cut;
  s.shake = sstep(-2500, -800, t) * cut;
  return s;
}

// ---------------------------------------------------------------- shaders
const NOISE = `
float h21(vec2 p){ p = fract(p*vec2(123.34,456.21)); p += dot(p,p+45.32); return fract(p.x*p.y); }
float vn(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(h21(i),h21(i+vec2(1,0)),f.x), mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x), f.y); }`;
const VERT = `
uniform float uTime, uLen, uExpand, uDiamonds, uGround, uRexit, uThrottle, uSp, uSplashR; uniform vec2 uCenter;
varying float vS, vX, vFace, vAng, vSplash, vInst, vEdge;
${NOISE}
void main(){
  float s = -position.y;                 // 0 at the bell exit, 1 at the tail
  float ang = atan(position.z, position.x);
  float L = uLen; float x = s * L;
#ifdef CORE
  float sp = uSp;
  float train = 1. - smoothstep(${(FLAME.DIAMOND_N - 1 + FLAME.DIAMOND_X0 + 0.3).toFixed(2)}*sp, ${(FLAME.DIAMOND_N - 1 + FLAME.DIAMOND_X0 + 0.9).toFixed(2)}*sp, x);
  float pinch = 1. - 0.38 * uDiamonds * train * smoothstep(0.15, 0.6, x) * (0.5 - 0.5*cos(6.2831853*(x/sp - ${FLAME.DIAMOND_X0.toFixed(2)})));   // waist between knots, full width at each knot
  float r = uRexit * (0.58 - 0.26*s) * pinch * (1. + uExpand*2.0*s);
#else
  float r = uRexit * (1.0 + s*(1.25 + 6.0*uExpand)) * (1. + 0.05*sin(x*0.9 - uTime*31.));
#endif
  // heat shimmer at the nozzle lip
  r *= 1. + 0.05 * smoothstep(0.10, 0., s) * (vn(vec2(ang*4., uTime*35.)) - .5) * 2.;
  vec3 p = vec3(cos(ang)*r, -x, sin(ang)*r);
  vec4 wp = modelMatrix * instanceMatrix * vec4(p, 1.);
  vec4 wa = modelMatrix * instanceMatrix * vec4(0., -x, 0., 1.);
  vSplash = 0.; vEdge = 0.;
  if (wp.y < uGround) {                  // the plume hits the pad deck and splays out flat
    float d = uGround - wp.y; vec2 dir = wp.xz - wa.xz; float l = length(dir); dir = l > 1e-4 ? dir/l : vec2(1.,0.);
    wp.y = uGround + 0.04; wp.xz += dir * d * 1.35; vSplash = d;
    // splash sheet stops short of the landing-gear feet: clamped to uSplashR from the cluster centre, faded over its last 1.5 m
    vec2 cc = wp.xz - uCenter; float lc = length(cc); vEdge = smoothstep(uSplashR - 1.5, uSplashR, lc); if (lc > uSplashR) wp.xz = uCenter + cc / lc * uSplashR;
  }
  vec3 n = normalize(mat3(modelMatrix * instanceMatrix) * vec3(cos(ang), 0.25, sin(ang)));
  vec3 v = normalize(cameraPosition - wp.xyz);
  vFace = abs(dot(n, v)); vS = s; vX = x; vAng = ang; vInst = float(gl_InstanceID);
  gl_Position = projectionMatrix * viewMatrix * wp;
}`;
const FRAG_OUTER = `
uniform float uTime, uThrottle, uOpacity, uFlash, uExpand, uLen, uGain, uDiamonds, uSp, uThrust, uCrowd;
varying float vS, vX, vFace, vAng, vSplash, vInst, vEdge;
${NOISE}
void main(){
  float n = vn(vec2(vAng*2.5 + vInst*7., vX*0.55 - uTime*22.)) * 0.6 + vn(vec2(vAng*6., vX*1.7 - uTime*47.)) * 0.4;
  float body = pow(vFace, 1.3) * pow(1. - vS, 1.6) * smoothstep(0., 0.02, vS);
  float a = body * (0.55 + 0.75*n) * uOpacity * uThrottle * (1. - 0.6*uExpand);
  a *= (1. - smoothstep(0.3, 6.0, vSplash)) * (vSplash > 0. ? 0.55 : 1.) * (1. - vEdge);   // splash sheet thins out across the deck
  a *= 1. - 0.75 * uDiamonds * smoothstep(0.4, 1.2, vX) * (1. - smoothstep(${(FLAME.DIAMOND_N - 0.5 + FLAME.DIAMOND_X0).toFixed(2)}*uSp, ${(FLAME.DIAMOND_N - 0.5 + FLAME.DIAMOND_X0).toFixed(2)}*uSp + 4., vX));   // darker sheath around the knots
  vec3 col = mix(vec3(0.55, 0.42, 1.0), vec3(0.32, 0.45, 1.0), vS);   // blue-violet, see-through
  col += vec3(0.5, 0.5, 0.7) * exp(-vX*1.4) * 0.35;                    // hot near the bell
  col += vec3(1.0) * uFlash * 0.8;
  gl_FragColor = vec4(col * a * 0.8 * uGain * uThrust * uCrowd, 1.);
}`;
const FRAG_CORE = `
uniform float uTime, uThrottle, uDiamonds, uFlash, uFlick, uExpand, uGain, uSp, uThrust, uCrowd;
varying float vS, vX, vFace, vAng, vSplash, vInst, vEdge;
${NOISE}
void main(){
  float sp = uSp;
  float hot = exp(-vX / 0.5);    // short white-hot zone so the first knot stands clear of it
  float d = 0.;
  for (int k = 0; k < ${FLAME.DIAMOND_N}; k++) { float xk = (float(k) + ${FLAME.DIAMOND_X0.toFixed(2)}) * sp; float w = 0.15*sp + 0.03*float(k);
    d += exp(-pow((vX - xk)/w, 2.)) * (1. - 0.10*float(k)); }
  float train = 1. - smoothstep(${(FLAME.DIAMOND_N - 1 + FLAME.DIAMOND_X0 + 0.3).toFixed(2)}*sp, ${(FLAME.DIAMOND_N - 1 + FLAME.DIAMOND_X0 + 0.9).toFixed(2)}*sp, vX);
  float gap = 1. - 0.90 * uDiamonds * train * smoothstep(0.25*sp, 0.55*sp, vX) * (1. - clamp(d*1.6, 0., 1.));   // dark gap between knots
  float flick = 0.92 + 0.08 * vn(vec2(uTime*30. + vInst*13., vInst));
  float tail = pow(1. - vS, 1.0) * smoothstep(0., 0.015, vS);
  float face = pow(vFace, 0.7);
  float i = face * tail * ((hot*1.6 + 0.12*uGain) * gap + d*6.0*uDiamonds*flick) * uThrottle * uFlick * mix(0.85, 1., uGain);
  i *= (1. - smoothstep(0.2, 2.5, vSplash)) * (1. - vEdge);
  i *= 1. - 0.5*uExpand;
  vec3 coreCol = mix(vec3(0.42, 0.50, 1.0), vec3(1.0, 0.98, 1.0), clamp(hot*1.4, 0., 1.));
  vec3 diaCol = vec3(1.0, 0.96, 1.0);   // near-white knots
  vec3 col = mix(coreCol, diaCol, clamp(d*uDiamonds*1.5, 0., 1.)) + vec3(1.)*uFlash;
  gl_FragColor = vec4(col * i * uThrust * sqrt(uCrowd), 1.);
}`;
const DUST_VERT = `
attribute float aSize, aAlpha, aKind; uniform float uPxScale, uMaxPx; varying float vA, vK;
void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.); gl_Position = projectionMatrix * mv;
  gl_PointSize = clamp(aSize * uPxScale / -mv.z, 1.0, uMaxPx); vA = aAlpha; vK = aKind; }`;
const DUST_FRAG = `
varying float vA, vK;
void main(){ vec2 q = gl_PointCoord*2.-1.; float r = dot(q,q); if (r > 1.) discard;
  if (vK < 0.5) { if (abs(q.y) > 0.55) discard; gl_FragColor = vec4(vec3(0.80,0.76,0.70), vA); }   // grit: hard-edged flat chips
  else gl_FragColor = vec4(vec3(0.86,0.90,1.0), vA * (1. - r)); }`;
const GLOW_FRAG = `
uniform float uI, uHalf, uRingR, uRingA, uSeed; varying vec2 vUv;
float hh(float n){ return fract(sin(n*91.345 + uSeed)*43758.5453); }
void main(){ vec2 q = (vUv*2.-1.)*uHalf; float r = length(q);           // metres from the engine cluster
  float rg = r / 17.;                                                    // warm pad glow, 17 m radius
  float g = pow(max(0., 1.-rg), 2.4) + 0.6*pow(max(0., 1.-rg*2.2), 3.);
  vec3 col = vec3(1.0, 0.62, 0.32) * g * uI;
  // dust sheet: hard leading edge, radial streaks (sheets), thins behind the front. Vacuum: no billowing.
  if (uRingA > 0.001) { float a = atan(q.y, q.x) / 6.2831853 + .5; float k = floor(a*72.);
    float streak = step(0.35, hh(k)) * (0.55 + 0.45*hh(k+7.));
    float front = uRingR * (0.86 + 0.14*hh(k+3.));
    float band = step(r, front) * smoothstep(front*0.45, front, r) * step(1.5, r);
    col += vec3(0.62, 0.58, 0.52) * band * streak * uRingA; }
  gl_FragColor = vec4(col, 1.); }`;

// ---------------------------------------------------------------- engine positions
// Prefer Engine_Nozzle_0..N-1 marker nodes (aft_skirt/engine_ring_N*.glb, and later ship exports: one per bell exit, local -Y = thrust axis).
// Returns [{ pos, dir }] in shipRoot-local space, or null when the ship has no markers (then use positions found from the mesh).
export function findEngineNozzles(shipRoot) {
  const out = [], inv = new THREE.Matrix4(); shipRoot.updateMatrixWorld(true); inv.copy(shipRoot.matrixWorld).invert();
  const nodes = []; shipRoot.traverse(n => { if (/^Engine_Nozzle_\d+$/.test(n.name)) nodes.push(n); });
  const num = (n) => +n.name.match(/\d+$/)[0]; nodes.sort((a, b) => num(a) - num(b));
  for (const n of nodes) { const m = new THREE.Matrix4().multiplyMatrices(inv, n.matrixWorld);
    const pos = new THREE.Vector3().setFromMatrixPosition(m), dir = new THREE.Vector3(0, -1, 0).transformDirection(m);
    out.push({ pos, dir, name: n.name, exitR: n.userData?.exit_r ?? FLAME.R_EXIT }); }
  return out.length ? out : null;
}

// ---------------------------------------------------------------- factory
// engines: [{ pos: Vector3, dir?: Vector3 }] in the ship root's local space (pos = centre of the bell exit plane, dir = thrust
// axis pointing away from the ship, default (0,-1,0)). Call attach(shipRoot, worldRoot) once, then update(state, t, ...) each frame.
export function createEngineFlames(engines, opt = {}) {
  let N = engines.length; const CAPN = Math.max(FLAME.MAX_ENGINES, N), geo = new THREE.CylinderGeometry(1, 1, 1, 24, 40, true); geo.translate(0, -0.5, 0);
  const common = { uTime: { value: 0 }, uThrottle: { value: 0 }, uExpand: { value: 0 }, uDiamonds: { value: 0 }, uGround: { value: opt.groundY ?? 0.26 },
    uRexit: { value: FLAME.R_EXIT }, uFlash: { value: 0 }, uSp: { value: FLAME.DIAMOND_SP }, uThrust: { value: 1 }, uCrowd: { value: 1 },
    uSplashR: { value: opt.splashR ?? FLAME.SPLASH_R }, uCenter: { value: new THREE.Vector2() } };
  const mk = (frag, core, len) => new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: frag, defines: core ? { CORE: 1 } : {},
    uniforms: { ...THREE.UniformsUtils.clone(common), uLen: { value: len }, uOpacity: { value: 0.9 }, uFlick: { value: 1 }, uGain: { value: 1 } },
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, toneMapped: false });
  const outer = new THREE.InstancedMesh(geo, mk(FRAG_OUTER, false, FLAME.LEN), CAPN);
  const core = new THREE.InstancedMesh(geo, mk(FRAG_CORE, true, FLAME.CORE_LEN), CAPN);
  outer.name = 'Flame_Plume'; core.name = 'Flame_Core'; outer.renderOrder = 10; core.renderOrder = 11;
  const m = new THREE.Matrix4(), qd = new THREE.Quaternion(), down = new THREE.Vector3(0, -1, 0), one = new THREE.Vector3(1, 1, 1);
  const engC = new THREE.Vector3(), sc3 = new THREE.Vector3();
  function placeEngines(list) {   // re-spacing / level-up: same 2 InstancedMeshes, only the matrices and count change
    N = list.length; engC.set(0, 0, 0);
    list.forEach((e, i) => { qd.setFromUnitVectors(down, (e.dir || down).clone().normalize()); const k = (e.exitR ?? FLAME.R_EXIT) / FLAME.R_EXIT;
      m.compose(e.pos, qd, sc3.set(k, 1, k)); outer.setMatrixAt(i, m); core.setMatrixAt(i, m); engC.add(e.pos); });
    engC.divideScalar(Math.max(1, N));
    // crowding: more plumes overlap in screen, so each envelope gets 6/N of the light (core sqrt(6/N)) and the cluster doesn't wash out
    for (const o of [outer, core]) { o.count = N; o.instanceMatrix.needsUpdate = true; o.material.uniforms.uCrowd.value = Math.min(1, FLAME.CROWD_REF / Math.max(1, N)); }
  }
  placeEngines(engines);
  for (const o of [outer, core]) { o.frustumCulled = false; o.visible = false; }
  const group = new THREE.Group(); group.name = 'EngineFlames'; group.add(outer, core);

  // dust + vapour (world space, pad-local), one Points, fixed buffer of DUST_CAP
  const CAP = FLAME.DUST_CAP, pos = new Float32Array(CAP * 3), size = new Float32Array(CAP), alpha = new Float32Array(CAP), kind = new Float32Array(CAP);
  const dg = new THREE.BufferGeometry();
  dg.setAttribute('position', new THREE.BufferAttribute(pos, 3)); dg.setAttribute('aSize', new THREE.BufferAttribute(size, 1));
  dg.setAttribute('aAlpha', new THREE.BufferAttribute(alpha, 1)); dg.setAttribute('aKind', new THREE.BufferAttribute(kind, 1));
  const dust = new THREE.Points(dg, new THREE.ShaderMaterial({ vertexShader: DUST_VERT, fragmentShader: DUST_FRAG, uniforms: { uPxScale: { value: 600 }, uMaxPx: { value: 16 } },
    transparent: true, depthWrite: false }));
  dust.name = 'Flame_Dust'; dust.frustumCulled = false; dust.renderOrder = 9;
  const glow = new THREE.Mesh(new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2), new THREE.ShaderMaterial({
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.); }',
    fragmentShader: GLOW_FRAG, uniforms: { uI: { value: 0 }, uHalf: { value: 45 }, uRingR: { value: 0 }, uRingA: { value: 0 }, uSeed: { value: 0 } }, transparent: true, depthWrite: false,
    blending: THREE.AdditiveBlending, polygonOffset: true, polygonOffsetFactor: -4, toneMapped: false }));
  glow.name = 'Flame_PadGlow'; glow.scale.setScalar(90); glow.material.uniforms.uHalf.value = 45;   // 90 m quad: glow (17 m) + dust sheet (to ~44 m) glow.renderOrder = 8;
  const light = new THREE.PointLight(0xffa860, 0, 45, 1.6); light.name = 'Flame_UndersideLight';

  // deterministic particles: a burst is a pure function of (time since burst), so seeking / reload gives the same frame
  const rnd = (i, k) => { const s = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return s - Math.floor(s); };
  function burstParticle(i, tb, out, o) {     // grit chip i of a ring burst, tb seconds after the burst
    const sheets = 9, sh = i % sheets, a = (sh + 0.5) / sheets * Math.PI * 2 + (rnd(i, 1) - .5) * 0.5 + o.rot;
    const v = (9 + 6 * rnd(sh, 2) + 7 * rnd(i, 3)) * o.speed, vy = (3.2 + 2.6 * rnd(sh, 4) + 0.8 * rnd(i, 5)) * o.speed;
    const delay = rnd(i, 6) * 0.18; let t = tb - delay; if (t < 0) return false;
    const tl = 2 * vy / FLAME.GRAV, tf = Math.min(t, tl), r0 = o.r0 + rnd(i, 7) * 1.2;
    const rr = r0 + v * tf, y = Math.max(0, vy * tf - 0.5 * FLAME.GRAV * tf * tf);
    out.set(o.cx + Math.cos(a) * rr, o.gy + 0.05 + y, o.cz + Math.sin(a) * rr);
    const settle = (t > tl ? 1 - clamp((t - tl) / 0.5, 0, 1) : 1) * (1 - sstep(25, 45, rr));   // lands hard, lies there, then fades into the regolith
    return { a: 0.95 * settle * sstep(0, 0.05, t), s: 1.0 + 1.2 * rnd(i, 8) };
  }
  function vapourParticle(i, tb, out, o) {
    const a = rnd(i, 11) * Math.PI * 2, up = rnd(i, 12), v = 1.2 + 2.0 * rnd(i, 13);
    if (tb < 0) return false; const t = tb;
    out.set(o.cx + Math.cos(a) * (0.6 + v * t), o.ey + (up - 0.3) * v * t * 0.6, o.cz + Math.sin(a) * (0.6 + v * t));
    return { a: 0.55 * Math.exp(-t / 0.45) * sstep(0, 0.05, t), s: 1.2 + 3.0 * t };
  }
  const tmp = new THREE.Vector3(), engW = new THREE.Vector3();
  let shipRoot = null, worldRoot = null;
  const api = {
    group, outer, core, dust, glow, light, get N() { return N; }, drawCalls: 4, thrustLevel: 0,
    setEngines(list) { placeEngines(list); },
    // thrustLevel k (0 = Lv1): brightness and length x 1.08^k, diamonds x 0.95^k spacing. Lv3/5/7/9 add one step each.
    setThrustLevel(k) { api.thrustLevel = k; const f = Math.pow(1 + FLAME.THRUST_STEP, k), sp = FLAME.DIAMOND_SP * Math.pow(FLAME.DIAMOND_TIGHTEN, k);
      for (const o of [outer, core]) { o.material.uniforms.uThrust.value = f; o.material.uniforms.uSp.value = sp; } return { gain: f, len: f, diamondSp: sp }; },
    // Brightness vs on-screen size: a thin plume a few px wide needs more gain than a close-up. Call once per camera framing
    // with screen px per metre at the ship (device px). The fixed station camera -> one call. gain = clamp(10 / pxPerM, 0.5, 1).
    setScreenScale(pxPerM) { const g = clamp(10 / pxPerM, 0.5, 1); outer.material.uniforms.uGain.value = g; core.material.uniforms.uGain.value = g; return g; },
    attach(ship, world) { shipRoot = ship; worldRoot = world; ship.add(group); world.add(dust); world.add(glow); world.add(light); },
    // st: launchState()/landState(); tSec: clock (s); bursts: [{t: seconds since burst, kind:'ring'|'vapour', speed, n}]
    update(st, tSec, bursts = [], pxScale = 600, maxPx = 16) {
      dust.material.uniforms.uMaxPx.value = maxPx;
      const fl = 0.9 + 0.1 * Math.sin(tSec * 53) * Math.sin(tSec * 31 + 1.3);
      for (const o of [outer, core]) { const u = o.material.uniforms; o.visible = st.on;
        u.uTime.value = tSec; u.uThrottle.value = st.throttle; u.uExpand.value = st.expand; u.uDiamonds.value = st.diamonds; u.uFlash.value = st.flash;
        const tl = Math.pow(1 + FLAME.THRUST_STEP, api.thrustLevel);
        u.uLen.value = tl * (o === outer ? FLAME.LEN * (1 + 0.6 * st.expand) : FLAME.CORE_LEN) * st.len * (o === core ? 1 : (0.94 + 0.06 * fl)); u.uFlick.value = fl; }
      shipRoot.updateMatrixWorld(true); engW.copy(engC); shipRoot.localToWorld(engW);
      for (const o of [outer, core]) o.material.uniforms.uCenter.value.set(engW.x, engW.z);   // splash clamp centre (world)
      worldRoot.worldToLocal(engW);
      const gy = core.material.uniforms.uGround.value, near = 1 - sstep(2, 35, st.alt);
      const gI = st.on ? st.throttle * near * fl * (1 + st.flash) : 0;
      glow.position.set(engW.x, gy + 0.02, engW.z); glow.material.uniforms.uI.value = gI * 0.9;
      const rb = bursts.find(b => b.kind === 'ring'), gu = glow.material.uniforms;
      if (rb) { const sp = rb.o.speed ?? 1; gu.uRingR.value = 2.5 + 26 * sp * rb.t; gu.uRingA.value = 1.1 * sp * (1 - sstep(0.15, 1.5, rb.t)) * sstep(0, 0.04, rb.t); gu.uSeed.value = rb.seed || 0; }
      else gu.uRingA.value = 0;
      glow.visible = gI > 0.002 || gu.uRingA.value > 0.001;
      light.position.set(engW.x, Math.max(engW.y - 1.6, gy + 0.6), engW.z); light.intensity = st.on ? 260 * st.throttle * fl * (1 + st.flash) * (0.35 + 0.65 * near) : 0;
      // particles
      let n = 0; const o0 = { cx: engW.x, cz: engW.z, gy, ey: engW.y, r0: 2.0, rot: 0, speed: 1 };
      for (const b of bursts) {
        const o = { ...o0, ...b.o }, f = b.kind === 'vapour' ? vapourParticle : burstParticle;
        for (let i = 0; i < b.n && n < CAP; i++) { const r = f(i + (b.seed || 0), b.t, tmp, o); if (!r || r.a <= 0.003) continue;
          pos[n * 3] = tmp.x; pos[n * 3 + 1] = tmp.y; pos[n * 3 + 2] = tmp.z; size[n] = r.s * (b.kind === 'vapour' ? 1 : 1); alpha[n] = r.a; kind[n] = b.kind === 'vapour' ? 1 : 0; n++; }
      }
      dg.setDrawRange(0, n); dg.attributes.position.needsUpdate = dg.attributes.aSize.needsUpdate = dg.attributes.aAlpha.needsUpdate = dg.attributes.aKind.needsUpdate = true;
      dust.material.uniforms.uPxScale.value = pxScale; dust.visible = n > 0;
      return n;
    },
  };
  return api;
}

// Which particle bursts are alive at a moment (pure function of time -> reload-safe). Sizes stay within DUST_CAP (110 + 40 = 150; 100 + 50 = 150).
export function launchBursts(t) {   // t ms rel lift-off
  const out = [], tI = -ignBeforeLiftoff() + 210;     // main ring when the flame catches for good
  if (t >= tI && t < tI + 10000) out.push({ kind: 'ring', t: (t - tI) / 1000, n: 110, o: { speed: 1 } });
  if (t >= 150 && t < 10000) out.push({ kind: 'ring', t: (t - 150) / 1000, n: 40, seed: 500, o: { speed: 0.7, rot: 0.35 } });
  return out;
}
export function landBursts(t) {     // t ms rel touchdown
  const out = [], tR = -2400;   // ~5 m up
  if (t >= tR && t < tR + 10000) out.push({ kind: 'ring', t: (t - tR) / 1000, n: 100, o: { speed: 0.6 } });
  if (t >= CUTOFF_MS && t < CUTOFF_MS + 2500) out.push({ kind: 'vapour', t: (t - CUTOFF_MS) / 1000, n: 50, seed: 900 });
  return out;
}
