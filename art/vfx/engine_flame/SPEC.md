# Engine flame VFX: spec for Game Coder (look proof, 10/24/2026)

Art & Animation. This is a look proof for Game Director. Don't wire it in until Director approves the look.
It doesn't touch the 4 PM build, qa3d-next, or any existing timing.

- **Effect module:** `art/vfx/engine_flame/engine_flame.js`. Plain ES module that imports `three` (r169, same as qa3d).
- **Preview:** `art/vfx/engine_flame/index.html`. Serve the repo root, then open `/art/vfx/engine_flame/index.html`. It loads the real pad GLB (md5 82131aba) with the official pad camera.
  - Query options: `?w=375&h=667&dpr=2&phase=launch|land&t=<ms>&view=pad|close|hatch|gear&lv=1..10&n=6..11&thrust=k&gear=0|1`. The bottom bar has play buttons.
- **Hatch clip:** `art/vfx/engine_flame/hatch_close.glb` (animation only, 2,088 bytes, md5 `d16578c32490c560de4c52f0724e99e0`) + `hatch_close.js` (applies it, 0 draw calls). Source: `_src/build_hatch_clip.py`.
- **Proofs:** `art/vfx/engine_flame/proofs/`
  - **Pending render (box held for the crew GLB, 2:22 PM):** the Lv10 11-engine budget close-up, the re-rendered lift-off/landing strips and both mp4s, and the gear retract/deploy strips + close-ups. The queue is ready (`_tools/capture_all.mjs ONLY=…gear…`, `_tools/compose_gear.py`). Until then the strips and mp4s in proofs/ are the earlier 4-engine renders.
  - Videos: `liftoff.mp4` (LO − 3.0 s → LO + 8 s, i.e. tap 52.99 → 63.99 s: 0.2 s parked, HC at 53.19, 331 frames) and `landing.mp4` (TD − 6 s → TD + 2.5 s, 256 frames). H.264 yuv420p, 30 fps, 375×667 CSS px at 1×, padded by 1 px to 376×668 because H.264 needs even sizes, official pad camera.

## 1. Director's rulings (firm)

| Rule | Value | How the effect obeys it |
|---|---|---|
| Timing (revised 1:38 PM) | Hatch closes (HC) 53.19 → shut 53.99. Ignition = HC + 0.8 s = 53.99, as the lid seats. Lift-off (LO) = HC + 2.8 s = 55.99 (already in the crew tag, does not move), so there are 2 s of ignition before lift-off. | `FLAME.HATCH_TO_LIFTOFF_MS = 2800`, `FLAME.IGN_AFTER_HATCH_MS = 800`. The 800 is a parameter Director can change. The ignition window `ignBeforeLiftoff() = max(1200, 2800 - 800) = 2000 ms` (never under 1200 ms). |
| Crew safety | No flame or dust while anyone is outside the ship. | Nothing is drawn before ignition, and ignition is after the hatch closes. Also `launchState(t, crewOutside)` returns "off" whenever `crewOutside` is true. Pass `true` while any climber is on the ladder or pad. |
| Budget | At most 4 draw calls and at most 150 dust particles. | **Actual: 4 draw calls at any engine count** (measured with the aft skirt mounted: 12 calls → 16 with the flame on, at 6 engines and at 11 engines, at ignition, full thrust and the landing burn). **Actual: 150 particles max.** That's the buffer size and a hard cap. Measured peak: 149 at lift-off (6 and 11 engines), ≤ 150 at landing. The hatch clip and the landing gear add 0 draw calls. |
| Shake | At most 2 px. The 5 px margin must hold at 375 (top spare is 5.3 px). Never move the camera. | **The camera never moves.** The "shake" is a ship-only horizontal rumble of **±1.0 px at 375×667 and ±1.0 px at 393×852**, with 0 px vertical. The pad moves 0 px. The flicker of the pad glow and underside light carries the rest of the "rumble" feel. The top spare stays at 5.3 px, since nothing moves vertically and the camera is fixed. See `proofs/shake_worst_case_*.png`. |

## 1a. Locked timeline (Coder + Director), seconds after the Launch tap

| Tap + s | Event | Effect |
|---|---|---|
| < 53.19 | Crew boarding (anyone outside) | Lid open, no flame, no dust, light at 0. |
| **53.19** | Last climber inside, **hatch closes (HC)** | `hatch_close` clip starts (0.8 s, easeInOutCubic). |
| **53.99** | Hatch shut (HC + 0.8 s) = **Ignition** (LO − 2 s) | The lid seats on the same frame the engines flicker on. Flash, grit ring at +0.21 s (54.20), grows to full thrust. |
| **55.99** | **Lift-off (LO)** (HC + 2.8 s) | Existing 8 s climb (`y = 160·u³`). Unchanged crew-tag time. |
| 63.99 | Climb ends (LO + 8 s) | Flame off; ship off screen from about LO + 6 s. |
| 63.99 – 663.99 | Away 600 s | Nothing drawn. |
| 663.99 | Landing burn starts (TD − 8 s) | `landState(-8000)`: lit, wide plume, off screen. |
| **671.99** | **Touchdown (TD)** = LO + 616 s | Cut-off over 0.22 s (672.21), vapour puff to about 674.7. |

In code: `liftoffAt = tap + 55.99 s`, `touchdownAt = liftoffAt + 616 s`; call `launchState(t − liftoffAt, crewOutside)`, `landState(t − touchdownAt)`, `hatch.update((t − hatchCloseAt) / 1000)` with `hatchCloseAt = tap + 53.19 s`. The hatch stays shut for the whole trip and the landing (it only reopens when crew unload, which is not part of this clip).

## 1b. Hatch-close clip (crew hatch lid)

- **What moves:** the crew-hatch **lid** on the ladder landing (hinged at the outer edge of the ladder well), its 2 stainless ribs, and its 2 hold-open struts. Parked, the lid stands open at 100° (it doubles as the back guard). The clip swings it −100° about the hinge so it lies flat over the ladder well. The struts keep their feet on the deck and stretch to follow the lid. The airlock door panel in the hull is already modelled flush/closed in this GLB (3d0d489 flush fix), so it does not move.
- **Nodes:** in the current pad GLB (`launch_pad_game.glb` md5 **82131abae3a8e97427635fd2513155fa**, commit 6b5c76e, newer than 3d0d489 / 833a339b) there are **no hatch or lid nodes**: the lid is merged into the `Ship_Placeholder` mesh. I found it as mesh islands (vertex ranges in mesh_5: lid 8392–8399, ribs 8400–8415, struts 8428–8443, hinge rod 8416–8427 stays put). `hatch_close.js` finds them by position, not by index, so it survives a re-export as long as the landing geometry doesn't change.
- **File:** `hatch_close.glb` = 1 node `Hatch_Lid_Hinge` at the hinge, Ship_Placeholder-local (4.5423, 21.900, 2.6225), axis (0.5, 0, −0.866). 1 clip `hatch_close`: rotation, 25 LINEAR keys over 0.8 s (30 fps) with easeInOutCubic baked in, 0 → −100°. No meshes, no textures, nothing in the existing models was overwritten.
- **Runtime:** `createHatchClose(shipMeshes, clipGltf)` then `update(secondsSinceHC)` each frame (no-op once closed). It rotates 24 lid vertices + 16 strut vertices in place in the ship's existing geometry and uploads only that vertex range. **0 draw calls, 0 textures**, so the flame budget (+4) is unchanged. Negative time = open, ≥ 0.8 s = shut.
- **Proof:** `proofs/hatch_close_strip.png` (open, HC +0, +0.2, +0.4, +0.6, +0.8 s, close-up `view=hatch`). At the pad camera the lid is about 5 px across, so the strip uses a close-up.

## 2. Timeline (ms). Everything is a pure function of time, so reload, offline time and `?speed=10` work the same as today

Existing events stay exactly where they are:
- HC = hatch close.
- LO = HC + 2800. Ignition = HC + 800 = LO − 2000.
- The existing launch climb runs over `CG.launchSec` = 8000 ms (`y = 160·u³`).
- The existing landing runs over `CG.landSec` = 8000 ms (`y = 160·(1−u)³`). TD = touchdown = the end of `land`.

### Lift-off: `launchState(t)` with t = ms relative to LO

| t (rel LO) | rel HC | Phase | What happens | Easing |
|---|---|---|---|---|
| −2800 … −2000 | 0 … +800 | hatch closes | `hatch_close` clip (0.8 s, easeInOutCubic). No flame. | easeInOutCubic |
| < −2000 | < +800 | off | Nothing drawn. The light is at intensity 0, but stays in the scene. | – |
| −2000 … −1790 | +800 … +1010 | flicker-on | Lit at 0–70 ms, off 70–120, lit 120–160, off 160–210, then lit from 210 on. Short flame (len 0.22→0.30), white **flash** decaying from 1 to 0 over 300 ms, throttle 0.75. | Steps, then linear flash decay |
| −1790 | +1010 | dust burst | The main grit ring (110 particles) and the radial dust sheet start when the flame catches (ign + 210 ms). | Ballistic, Moon g 1.62 |
| −1700 … −900 | +1100 … +1900 | grow | Length 0.30→1.0 (easeOutCubic over 800 ms). Throttle 0.75→1. Diamonds fade in from ign + 500 to ign + 1100 ms. | easeOutCubic / smoothstep |
| −900 … 0 | +1900 … +2800 | full thrust on pad | Full cone, white-hot core, 4 Mach diamonds per engine, slight flicker. Rumble up (smoothstep over 300 ms after ignition). | – |
| 0 | +2800 | **lift-off** (existing event) | The ship climbs on the existing curve. The second, smaller grit wave (40 particles) starts at LO + 150. | – |
| 0 … +2000 | | rumble out | The rumble fades from LO + 800 to LO + 2000 ms. | smoothstep |
| +3500 … +8000 | | vacuum widening | `expand` 0→1. The plume gets 1.6× longer and up to 7× wider at the tail. Envelope opacity ×(1 − 0.6·expand). | smoothstep |
| +5000 … +7500 | | diamonds fade | Diamonds 1→0 (held to +5 s so the full-thrust still at +4.4 s shows the whole train). | smoothstep |
| 0 … ~+5500 | | pad glow dies | Glow and light × (1 − smoothstep(2 m, 35 m, altitude)). | smoothstep on altitude |
| > +8000 | | off | End of the existing climb. The ship is off screen by about +6 s. | – |

### Landing: `landState(t)` with t = ms relative to TD

| t (rel TD) | Phase | What happens |
|---|---|---|
| −8000 | burn lit | The burn is lit for the whole `land` state. The ship starts 160 m up, off screen. Throttle 1.0. Plume is wide (expand 1). |
| −6000 … −2500 | narrowing | `expand` 1→0 as the ship nears the pad (the reverse of the climb). |
| −5000 … −2500 | diamonds back | Diamonds 0→1 (× throttle). |
| −4000 … 0 | throttle-down | Throttle 1.0 → 0.45 at touchdown (smoothstep). Length follows the throttle. |
| −2400 | dust ring | A smaller ring (100 particles, 0.6× speed) plus the dust sheet, at about 5 m altitude. |
| −2500 … −800 | rumble in | Ship-only ±1 px, as above. |
| 0 | **touchdown** (existing event) | Still lit at 45%. |
| 0 … +220 | cut-off | Throttle, length and diamonds go to 0 linearly over 220 ms (`CUTOFF_MS`). |
| +220 … +2700 | vapour puff | 50 soft white particles spread out from the bells and fade (exp, τ 450 ms). |
| > +220 | off | No flame. The particles finish on their own. |

The particle bursts are also pure functions of time: `launchBursts(t)` and `landBursts(t)`. A reload in the middle of a launch rebuilds the exact same frame. There's no particle state to save.

## 3. Layers and draw calls (4 total, at any number of engines)

| # | Object (name) | Type | Blend | Notes |
|---|---|---|---|---|
| 1 | `Flame_Plume` | `InstancedMesh`, 1 instance per engine | additive, depthWrite off, double-sided, toneMapped off | See-through blue-violet envelope. Procedural scrolling value noise, hot near the bell, splays flat across the pad deck when it hits it (in the vertex shader). |
| 2 | `Flame_Core` | `InstancedMesh`, 1 instance per engine | additive, same flags | White-hot core near the nozzle plus a train of 4 Mach diamonds. The radius pinches at each diamond and there's a bright band at each shock. Heat shimmer at the nozzle lip (radius wobble). |
| 3 | `Flame_Dust` | `Points`, fixed buffer of **150** | normal alpha, depthWrite off | Grit: hard-edged flat chips on ballistic arcs (Moon g, no drag, no clouds). They land, lie there for 0.5 s, and fade. The same buffer carries the landing vapour puff (soft white). |
| 4 | `Flame_PadGlow` | one 90 m quad on the deck | additive, polygonOffset | A warm glow (17 m radius) plus the **radial dust sheet**: a hard leading edge, 72 angular streaks, moving at 26 m/s and thinning behind the front. |
| – | `Flame_UndersideLight` | `PointLight` (0xffa860, distance 45, decay 1.6) | – | Warm flickering glow on the ship's underside and the pad. **No draw call.** Keep it in the scene from load at intensity 0, so turning it on never recompiles shaders. Shadows off. |

- **Geometry:** one shared open cylinder, 24 radial × 40 height segments, which is 1,920 triangles per layer per engine.
  - Lv1 (6 engines): 2 layers × 6 × 1,920 = **23,040 tris**. Lv10 (11 engines): 2 × 11 × 1,920 = **42,240 tris**. Plus 2 for the glow quad and up to 150 points.
  - Instance capacity is 12, so a level-up only changes `count` and the matrices; the shaders never recompile.
  - If the iPhone fill rate is tight, drop to 16×24 segments. It looks the same at the pad framing.
- **Textures: none (0 KB).** All the noise, the diamonds, the dust chips and the glow are procedural in the shaders, so there's nothing to load or compress. The 256 px budget isn't needed.
- **Shaders:** `ShaderMaterial` with WebGL2 / GLSL ES 3.00. It uses `gl_InstanceID` for per-engine flicker. Each fragment shader has a 4-tap value noise, and the core has a 4-iteration diamond loop.

## 4. Shader uniforms (set from the state object every frame)

| Uniform | Layers | Range | Meaning |
|---|---|---|---|
| `uTime` | plume, core | s | Scroll and flicker clock. |
| `uThrottle` | plume, core | 0–1 | Overall brightness. |
| `uLen` | plume, core | m | Length: plume `30 × len × (1 + 0.6·expand)`, core `13 × len`. |
| `uExpand` | plume, core | 0–1 | Vacuum widening on the climb. Narrowing on landing. |
| `uDiamonds` | plume (shape), core | 0–1 | Mach diamond strength. |
| `uFlash` | plume, core | 0–1 | Ignition flash. |
| `uFlick` | core | ~0.8–1 | Shared flicker, `0.9 + 0.1·sin(53t)·sin(31t+1.3)`. |
| `uGround` | plume, core | m (world y) | Pad deck height. Below it, the plume splays flat (0.251 on pad 82131aba). |
| `uRexit` | plume, core | m | Bell exit radius, 0.86. |
| `uGain` | plume, core | 0.5–1 | Brightness against on-screen size. `setScreenScale(pxPerMetre)` → `clamp(10 / pxPerM, 0.5, 1)`. It's 1.0 at the pad camera. Call it once per framing. |
| `uOpacity` | plume | 0.9 | Envelope opacity. |
| `uI` | glow | 0–2 | Glow = throttle × near-ground factor × flicker × (1 + flash) × 0.9. |
| `uRingR`, `uRingA`, `uSeed` | glow | m, 0–1.1 | Dust sheet radius `2.5 + 26·speed·t`, alpha `1.1·speed·(1 − smoothstep(0.15, 1.5, t))`. |
| `uPxScale`, `uMaxPx` | dust | – | Point size = `aSize · uPxScale / depth`, clamped to `uMaxPx` (7 CSS px). |

Fixed constants (in `FLAME`):
- `R_EXIT` 0.86 m
- `LEN` 30 m (was 24)
- `CORE_LEN` 13 m (was 9)
- `DIAMOND_N` 4
- `DIAMOND_SP` 2.4 m (was 1.7) and `DIAMOND_X0` 1.0: diamonds sit at (k + 1)·2.4 m = 2.4, 4.8, 7.2, 9.6 m below the exit, about 11 px apart at 375
- `DUST_CAP` 150
- `SHAKE_PX` 1.0
- `GRAV` 1.62

Colours:
- Envelope: (0.55, 0.42, 1.0) → (0.32, 0.45, 1.0) along the length.
- Core: (0.42, 0.50, 1.0) → white near the nozzle.
- Diamonds: (1.0, 0.96, 1.0), near-white, ×6 brightness over a gap darkened to 10% (core) and a sheath darkened to 25% along the diamond train.
- Glow: (1.0, 0.62, 0.32).
- Dust: (0.80, 0.76, 0.70).
- Vapour: (0.86, 0.90, 1.0).

## 5. Attaching it to N engines

```js
import { createEngineFlames, launchState, landState, launchBursts, landBursts } from './engine_flame.js';
// engines: bell-exit centres in the SHIP ROOT's local space; dir = thrust axis (defaults to straight down)
const fx = createEngineFlames(engines.map(p => ({ pos: p })), { groundY: padDeckY });
fx.attach(shipRoot, padRoot);          // plume + core ride on the ship; dust, glow and light stay on the pad
fx.setScreenScale(pxPerMetreAtShip);   // once per station framing
// every frame while on the Launch Pad station:
const st = phase === 'land' ? landState(t - touchdownAt) : launchState(t - liftoffAt, crewOutside);
const bursts = phase === 'land' ? landBursts(t - touchdownAt) : launchBursts(t - liftoffAt);
fx.update(st, t / 1000, bursts, pxScale, 7 * dpr);
shipRoot.position.x += SHAKE_PX * metresPerPx * st.shake * noise(t);   // optional ship-only rumble, never the camera
```

- **More engines = more instances.** Pass 6–11 positions and you get 6–11 flames for the same 4 draw calls. `fx.setEngines(list)` re-spaces on a level-up. Above 6 engines each plume is dimmed by `uCrowd = min(1, 6/N)` (core by its square root) so the cluster doesn't turn into one white column.
- **Thrust steps:** `fx.setThrustLevel(k)` gives ×1.08^k brightness and length and ×0.95^k diamond spacing (tighter). Use `thrustLevelForLevel(lv)` from `aft_skirt/engine_ring.js`.
- **Starter ship engine positions:**
  - The pad GLB has the ship merged into one mesh, so there are no engine nodes. The preview finds the 4 bell exits from the mesh, starting from the layout in `build_starter_ship.py` (`ENG_R` 2.25 m, 45° + k·90°, pad yaw +60°).
  - Pad-local glTF positions (m), exit radius 0.87:
    - (−0.569, 1.393, −15.187)
    - (−2.222, 1.393, −12.415)
    - (0.568, 1.393, −10.824)
    - (2.226, 1.393, −13.583)
  - Ship root = `Ship_Placeholder` at (0, 0, −13).
- **Markers:** the aft skirt GLBs carry empties `Engine_Nozzle_0..N-1` at each bell exit (local −Y = thrust, `extras.exit_r`). `findEngineNozzles(shipRoot)` finds them (regex `/^Engine_Nozzle_\d+$/`, numeric sort). The 4-bell list above is only the fallback for the old pad GLB.

## 6. Measurements (headless Chrome 156, SwiftShader CPU renderer, 750×1334 = 375×667 @2x, box under load from other renders)

- **Draw calls:** 12 with the effect off, 16 with it on (aft skirt mounted, 6 engines and 11 engines alike). That's **+4**, measured at ignition, full thrust and the landing burn. The aft skirt is 1 draw (ring + band + gear in one skinned mesh); with the bare ring instead it is also 12 → 16, so **the gear adds 0**.
- **Mach diamonds** (`_tools/diamond_count.py`, threshold runs along each projected plume axis, `proofs/diamond_count_full_thrust.json`): 375×667 full thrust **[4, 3, 4, 4, 4, 4]** per engine (all within 3–5; knots at about 1.6–2.9, 4.1–5.3, 6.4–7.7, 8.9–10.0 m below the exit); 393×852 [4, 3, 4, 4, 5, 3]. After cut-off, only the dust is left, so it's **+1**.
- **Particles:** peak **149** at lift-off at 6 and at 11 engines (the 150 buffer is the hard cap; dust doesn't scale with N).
- **Hatch clip:** +0 draw calls (11 → 11 parked and during the close); it edits 40 vertices of the existing ship mesh for 0.8 s, then stops.
- **Frame time:** SwiftShader is a CPU rasterizer, so treat these only as relative numbers. Median frame, synced with readPixels:

  | Frame | Median |
  |---|---|
  | Parked | 184.8 ms |
  | Ignition with dust | 219.6 ms |
  | Full thrust | 204.9 ms |
  | Landing | 207.1 ms |

  That's +11–19% on a CPU rasterizer, where the cost is mostly fill from the additive overdraw.
- **JS cost of `fx.update`:** ~0.0 ms median and 0.3 ms p99 for 150 particles.
- **Still to do: a real iPhone Safari check.** Playtester should check 60 fps on the device once Coder wires it in. If the GPU is short, the first things to drop are the cone segments (24×40 → 16×24) and the glow quad size (90 m → 60 m).

## 7. Notes for Director and Coder

- The pad crane mast sits between the camera and the engines, so at the pad framing it covers a thin vertical strip of the plume.
- **The pad crane mast crossing the plume is fine** (Director, 1:38 PM). Leave it as it is.
- `Cargo_Door`: see Coder task (a) below.
- **The close-up proofs** (`*_nozzle_closeup.png`) hide the pad props (crane, tanks, hoses) so the nozzles can be seen. The pad-framing stills show everything.
- **The ground in the preview** is the qa3d vertex-colour fallback look, not the KTX2 M_ground.

## 8. Coder tasks

**(a) Re-parent `Cargo_Door` to the ship node.** In the pad GLB (`launch_pad_game.glb` 82131aba) `Cargo_Door` is a pad-level node, not a child of `Ship_Placeholder`, so if only the ship node is moved at lift-off the door stays hanging in the air at the old height. Once, after load, before any animation:

```js
const ship = gltf.scene.getObjectByName('Ship_Placeholder');
const door = gltf.scene.getObjectByName('Cargo_Door');
if (door && door.parent !== ship) ship.attach(door);   // attach() keeps its world transform
```

Then the door lifts off, rumbles and lands with the ship. The preview (`index.html`) already does this. No new draw calls.

**(b) Engine positions: prefer `Engine_Nozzle_0..N-1` markers.** The aft skirt module (section 9) carries empties `Engine_Nozzle_0` … `Engine_Nozzle_{N-1}` at each bell exit, local −Y = thrust direction. `engine_flame.js` now exports `findEngineNozzles(shipRoot)`, which returns `[{ pos, dir, name }]` in ship-local space, sorted by name, or `null` when the GLB has no markers. Use it first and only fall back to positions worked out from the mesh (or the hard-coded list in section 5) when it returns `null`:

```js
import { findEngineNozzles, createEngineFlames } from './engine_flame.js';
const engines = findEngineNozzles(ship) || meshDerivedEngines;   // current pad GLB: null → fallback
const fx = createEngineFlames(engines, { groundY: padTopY });   // the flame uses pos; it fires along ship −Y (dir is there for a check)
```

`index.html` already does this (`S.engineSource` shows which path was used; today it reads "mesh (no markers in this GLB)"). The engine count follows the number of markers, and the +4 draw calls stay +4 for any count because each layer is one InstancedMesh.

## 9. Engine ring / aft skirt module (`aft_skirt/`, mine)

- **What it is:** the ship's whole aft section as one swappable module: thrust plate, N bells on one ring, the outer skirt band (R 4.45 m) with 4 landing-gear bays, doors and folding legs. Files `aft_skirt/aft_skirt_N06.glb` … `aft_skirt_N11.glb` (6–11 engines), built by `aft_skirt/_src/build_aft_skirt.py` + `_src/gear_pose.py`. The bare ring without gear (`engine_ring_N06..N11.glb`, `_src/build_engine_ring.py`) is kept only as a reference for the draw-call check.
- **Engine count by ship level** (`engineCountForLevel`, `thrustLevelForLevel` in `aft_skirt/engine_ring.js`):

  | Level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | Engines | 6 | 7 | 7 | 8 | 8 | 9 | 9 | 10 | 10 | 11 |
  | Thrust step | 0 | 0 | 1 | 1 | 2 | 2 | 3 | 3 | 4 | 4 |

  Odd levels 3/5/7/9 add a thrust step (+8% flame brightness and length, diamonds 5% closer) instead of an engine.
- **Layout:** bells evenly spaced on a ring of R 3.05 m, exit plane 0.9 m above the module origin, exit radius min(0.84, 0.46 × chord) (0.84 m up to 9 engines, 0.79 m at 11). The ring is clocked by `90 + (N even ? 90/N : 0) − 60` build degrees so that, in the fixed pad camera, no two bells line up front to back and their diamonds never stack. Adding an engine rebuilds the ring evenly spaced; don't add one beside the others.
- **Frame:** the ship build frame in glTF axes, Y up, origin = ship base centre on the axis = **`Engine_Ring_Mount`**, metres. Outer diameter of the skirt matches the Lv1 hull base (8 m hull, band 8.9 m). The module is yaw-neutral: the pad's +60° yaw comes from the ship root.
- **How a ship swaps its nozzle section for the module:**
  1. The ship GLB keeps (or gets) an empty `Engine_Ring_Mount` at its base centre and drops its own bells, aft skirt and legs. (Starter ship and ship_lv2 belong to AA2/AA; they add the empty and remove those parts on their next export. I don't edit those files.)
  2. Game: `const sk = await loader.loadAsync(`aft_skirt/aft_skirt_N${String(n).padStart(2,'0')}.glb`); ship.getObjectByName('Engine_Ring_Mount').add(sk.scene);` On a level-up that changes N, remove the old one and add the new one. The flame follows: `fx.setEngines(findEngineNozzles(ship))`, `fx.setThrustLevel(thrustLevelForLevel(lv))`.
  3. Until the ship exports carry the mount, the preview does the swap in the render scene only: `collapseMergedBells` and `collapseOldLegs` (in `index.html`) move the Lv1 hull's merged bell and leg triangles to a point inside the hull, and the module is mounted 0.9 m below the old exit plane. **This is a preview hack, not for the game.**
- **Cost:** one mesh, one material (`M_AftSkirt`, vertex colours from the hull-white / steel / graphite sets, metallic 0.35, roughness 0.5), no textures. 8,657 verts / 10,688 tris at N = 6, 11,672 verts / 15,008 tris at N = 11 (float32, unpacked: 0.46–0.60 MB; run gltfpack/meshopt before it ships).

## 10. Landing gear (in the aft skirt module)

- **Layout:** 4 slim legs at build 60 / 150 / 240 / 330°, one bay each in the band (0.84 m wide, sill y 2.50 to header y 6.35 = 3.85 m tall; sill raised 5 cm from 2.45 on 10/24 so the closed doors' bottom edge clears the plume at every level), each closed by a pair of flush doors hinged on the bay's vertical edges (open 100°, outward). The leg angles miss the ladder (270°) and the cargo hoist (215°). With 6 engines at 45 + 60k°, each leg sits **15° from the nearest bell**; 4 legs can't sit exactly between 6 bells, and the plume never comes near a leg anyway (clearance below). The same 4 legs serve every level (Lv1–9 rule; the module is the same up to 11 engines).
- **Leg:** hip pivot inside the bay top (R 4.19, y 6.05), upper strut 17 cm with a fairing sleeve, knee block, shock body 14 cm with an amber lock collar, chrome piston, 38 cm foot pad. Foot pad centre at R 6.4 m; pad bottom on the Lv1 contact plane (1.142 m below the nozzle exit plane, `extras.gear.contact_y`). The doors have a notch round the locked upper strut, so they close flush round a deployed leg.
- **Nodes (joints of the one skinned mesh):** `Aft_Skirt_Root`; per leg k = 0..3: `Gear_Leg_k` (hip swing), `Gear_Knee_k` (fold), `Gear_Foot_k` (shock slide), `Gear_Door_ka` and `Gear_Door_kb`. Rest pose = legs down and locked, shocks compressed, doors shut.
- **Clips (baked, 30 fps, from `gear_pose.py`):** `Gear_Retract` (3.2 s, clip t 0 = LO + 1.0 s) and `Gear_Deploy` (3.6 s, clip t 0 = TD − 7.0 s). Preferred runtime is `aft_skirt/gear.js`: `const gear = createGear(skirtRoot); gear.update('launch', t − liftoffAt, alt)` / `gear.update('land', t − touchdownAt, alt)` every frame, on the **same clock as the flame**. It reads its numbers from the GLB (`scene.extras.gear`), so it matches the clips exactly and also does the 5 cm compression from altitude.
- **Timeline** (easeInOutCubic everywhere; LO = tap + 55.99 s, TD = tap + 671.99 s):

  | Phase | Step | Time | Tap + s |
  |---|---|---|---|
  | Lift-off | legs down, locked | until LO + 1.0 | – 56.99 |
  | | doors open | LO + 1.0 → 1.6 | 56.99 → 57.59 |
  | | knee folds | LO + 1.6 → 3.4 | 57.59 → 59.39 |
  | | leg swings in (overlaps the fold; both finish together) | LO + 2.2 → 3.4 | 58.19 → 59.39 |
  | | stow settle as the leg seats (`R_SETTLE`, hip 0.025 rad peak, out toward the doors first, damped) | LO + 3.4 → 3.6 | 59.39 → 59.59 |
  | | doors close (flush) | LO + 3.6 → 4.2 | 59.59 → 60.19 |
  | Trip | stowed, doors shut | | 60.19 → 664.99 |
  | Landing | doors open | TD − 7.0 → 6.4 | 664.99 → 665.59 |
  | | knee extends and locks | TD − 6.4 → 4.4 | 665.59 → 667.59 |
  | | leg swings out (overlaps the knee; both start together) | TD − 6.3 → 5.2 | 665.69 → 666.79 |
  | | lock beat (`D_BOUNCE`, knee 0.07 rad peak, damped, 43 % rebound) | TD − 4.4 → 4.0 | 667.59 → 667.99 |
  | | doors close round the legs | TD − 4.0 → 3.4 | 667.99 → 668.59 |
  | | feet compress 5 cm (last 5 cm of altitude) | ≈ TD − 0.55 → TD | 671.44 → 671.99 |

  Constants: `GEAR_T` in `aft_skirt/gear.js` and `T` in `_src/gear_pose.py` (same numbers). The knee may only reach fully folded once the swing is ≥ 0.9 stowed: folded any earlier, the foot-pad rim cuts up to 4 cm into the bay back wall (60 Hz scan, 10/24). Settle and lock beats are sin²(πu)·sin(2πu)·e^(−2.5u), normalised to peak 1: zero value and zero speed at both ends, so there are no snaps. 60 Hz scan of both clips at 6–11 engines: no interpenetration, no pops, no velocity jumps.
- **Budget:** +0 draw calls (measured 12 → 12 vs the bare ring), 0 textures; per frame, 20 bone transforms.
- **Flames never touch the gear (measured):** `S.gearScan()` in the preview takes every frame at 30 fps (lift-off −2.0 … +8.0 s, landing −8.0 … +0.22 s), skins every leg and door vertex to world space, and measures it against the plume as the vertex shader builds it (cone r(x) with wobble and lip shimmer, the exit disk, and the deck splash sheet). To keep the splash off the feet, the splash sheet is now clamped to `FLAME.SPLASH_R = 5.6 m` from the cluster centre and fades over its last 1.5 m (`uSplashR`, `uCenter`). **Minimum clearance (10/24, every frame at 60 Hz, 2.50 sill): plume 1.710 m at 6 engines, 1.671 m at 7 / 9 / 10, 1.752 m at 8, 1.686 m at 11 (closed-door bottom edge; limit 1.64 m). Deck splash 0.613 m at every level (foot pads, at ignition and touchdown; limit 0.61 m).**
- **Splash margin is only about 3 mm (0.613 m against the 0.61 m limit).** Do not move the feet inward (`R_FOOT` 6.4 m), enlarge the pads (`PAD_R` 0.19 m), or grow `SPLASH_R` without re-running the gear scan.
