# Engine flame VFX: spec for Game Coder (look proof, 10/24/2026)

Art & Animation. This is a look proof for Game Director. Don't wire it in until Director approves the look.
It doesn't touch the 4 PM build, qa3d-next, or any existing timing.

- **Effect module:** `art/vfx/engine_flame/engine_flame.js`. Plain ES module that imports `three` (r169, same as qa3d).
- **Preview:** `art/vfx/engine_flame/index.html`. Serve the repo root, then open `/art/vfx/engine_flame/index.html`. It loads the real pad GLB (md5 82131aba) with the official pad camera.
  - Query options: `?w=375&h=667&dpr=2&phase=launch|land&t=<ms>&view=pad|close|hatch`. The bottom bar has play buttons.
- **Hatch clip:** `art/vfx/engine_flame/hatch_close.glb` (animation only, 2,004 bytes, md5 `033bdb77c18939b8370bdf53ef4aa0d9`) + `hatch_close.js` (applies it, 0 draw calls). Source: `_src/build_hatch_clip.py`.
- **Proofs:** `art/vfx/engine_flame/proofs/`
  - Videos: `liftoff.mp4` (HC → LO + 8 s, i.e. tap 53.19 → 64.19 s, 331 frames) and `landing.mp4` (TD − 6 s → TD + 2.5 s, 256 frames). H.264 yuv420p, 30 fps, 375×667 CSS px at 1×, padded by 1 px to 376×668 because H.264 needs even sizes, official pad camera.

## 1. Director's rulings (firm)

| Rule | Value | How the effect obeys it |
|---|---|---|
| Timing | Hatch closes (HC). Ignition = HC + 1 s. Lift-off (LO) = HC + 3 s, so there are 2 s of ignition before lift-off. | `FLAME.HATCH_TO_LIFTOFF_MS = 3000`, `FLAME.IGN_AFTER_HATCH_MS = 1000`. The 1000 is a parameter Director can change. The ignition window `ignBeforeLiftoff() = 3000 - 1000 = 2000 ms` must stay at least 1200 ms. |
| Crew safety | No flame or dust while anyone is outside the ship. | Nothing is drawn before ignition, and ignition is after the hatch closes. Also `launchState(t, crewOutside)` returns "off" whenever `crewOutside` is true. Pass `true` while any climber is on the ladder or pad. |
| Budget | At most 4 draw calls and at most 150 dust particles. | **Actual: 4 draw calls** (measured: 11 calls → 15 with the flame on). **Actual: 150 particles max.** That's the buffer size and a hard cap. Measured peak: 149 at lift-off, 150 at landing. The hatch clip adds 0 draw calls. |
| Shake | At most 2 px. The 5 px margin must hold at 375 (top spare is 5.3 px). Never move the camera. | **The camera never moves.** The "shake" is a ship-only horizontal rumble of **±1.0 px at 375×667 and ±1.0 px at 393×852**, with 0 px vertical. The pad moves 0 px. The flicker of the pad glow and underside light carries the rest of the "rumble" feel. The top spare stays at 5.3 px, since nothing moves vertically and the camera is fixed. See `proofs/shake_worst_case_*.png`. |

## 1a. Locked timeline (Coder + Director), seconds after the Launch tap

| Tap + s | Event | Effect |
|---|---|---|
| < 53.19 | Crew boarding (anyone outside) | Lid open, no flame, no dust, light at 0. |
| **53.19** | Last climber inside, **hatch closes (HC)** | `hatch_close` clip starts (0.8 s, easeInOutCubic). |
| **53.99** | Hatch shut (HC + 0.8 s) | Lid flat over the ladder well. 0.2 s of stillness before ignition. |
| **54.19** | **Ignition** (HC + 1 s = LO − 2 s) | Flicker-on, flash, grit ring at +0.21 s, grows to full thrust. |
| **56.19** | **Lift-off (LO)** (HC + 3 s) | Existing 8 s climb (`y = 160·u³`). |
| 64.19 | Climb ends (LO + 8 s) | Flame off; ship off screen from about LO + 6 s. |
| 64.19 – 664.19 | Away 600 s | Nothing drawn. |
| 664.19 | Landing burn starts (TD − 8 s) | `landState(-8000)`: lit, wide plume, off screen. |
| **672.19** | **Touchdown (TD)** = LO + 616 s | Cut-off over 0.22 s (672.41), vapour puff to about 674.9. |

In code: `liftoffAt = tap + 56.19 s`, `touchdownAt = liftoffAt + 616 s`; call `launchState(t − liftoffAt, crewOutside)`, `landState(t − touchdownAt)`, `hatch.update((t − hatchCloseAt) / 1000)` with `hatchCloseAt = tap + 53.19 s`. The hatch stays shut for the whole trip and the landing (it only reopens when crew unload, which is not part of this clip).

## 1b. Hatch-close clip (crew hatch lid)

- **What moves:** the crew-hatch **lid** on the ladder landing (hinged at the outer edge of the ladder well), its 2 stainless ribs, and its 2 hold-open struts. Parked, the lid stands open at 100° (it doubles as the back guard). The clip swings it −100° about the hinge so it lies flat over the ladder well. The struts keep their feet on the deck and stretch to follow the lid. The airlock door panel in the hull is already modelled flush/closed in this GLB (3d0d489 flush fix), so it does not move.
- **Nodes:** in the current pad GLB (`launch_pad_game.glb` md5 **82131abae3a8e97427635fd2513155fa**, commit 6b5c76e, newer than 3d0d489 / 833a339b) there are **no hatch or lid nodes**: the lid is merged into the `Ship_Placeholder` mesh. I found it as mesh islands (vertex ranges in mesh_5: lid 8392–8399, ribs 8400–8415, struts 8428–8443, hinge rod 8416–8427 stays put). `hatch_close.js` finds them by position, not by index, so it survives a re-export as long as the landing geometry doesn't change.
- **File:** `hatch_close.glb` = 1 node `Hatch_Lid_Hinge` at the hinge, Ship_Placeholder-local (4.5423, 21.900, 2.6225), axis (0.5, 0, −0.866). 1 clip `hatch_close`: rotation, 25 LINEAR keys over 0.8 s (30 fps) with easeInOutCubic baked in, 0 → −100°. No meshes, no textures, nothing in the existing models was overwritten.
- **Runtime:** `createHatchClose(shipMeshes, clipGltf)` then `update(secondsSinceHC)` each frame (no-op once closed). It rotates 24 lid vertices + 16 strut vertices in place in the ship's existing geometry and uploads only that vertex range. **0 draw calls, 0 textures**, so the flame budget (+4) is unchanged. Negative time = open, ≥ 0.8 s = shut.
- **Proof:** `proofs/hatch_close_strip.png` (open, HC +0, +0.2, +0.4, +0.6, +0.8 s, close-up `view=hatch`). At the pad camera the lid is about 5 px across, so the strip uses a close-up.

## 2. Timeline (ms). Everything is a pure function of time, so reload, offline time and `?speed=10` work the same as today

Existing events stay exactly where they are:
- HC = hatch close.
- LO = HC + 3000.
- The existing launch climb runs over `CG.launchSec` = 8000 ms (`y = 160·u³`).
- The existing landing runs over `CG.landSec` = 8000 ms (`y = 160·(1−u)³`). TD = touchdown = the end of `land`.

### Lift-off: `launchState(t)` with t = ms relative to LO

| t (rel LO) | rel HC | Phase | What happens | Easing |
|---|---|---|---|---|
| −3000 … −2200 | 0 … +800 | hatch closes | `hatch_close` clip (0.8 s, easeInOutCubic). No flame. | easeInOutCubic |
| < −2000 | < +1000 | off | Nothing drawn. The light is at intensity 0, but stays in the scene. | – |
| −2000 … −1790 | +1000 … +1210 | flicker-on | Lit at 0–70 ms, off 70–120, lit 120–160, off 160–210, then lit from 210 on. Short flame (len 0.22→0.30), white **flash** decaying from 1 to 0 over 300 ms, throttle 0.75. | Steps, then linear flash decay |
| −1790 | +1210 | dust burst | The main grit ring (110 particles) and the radial dust sheet start when the flame catches (ign + 210 ms). | Ballistic, Moon g 1.62 |
| −1700 … −900 | +1300 … +2100 | grow | Length 0.30→1.0 (easeOutCubic over 800 ms). Throttle 0.75→1. Diamonds fade in from ign + 500 to ign + 1100 ms. | easeOutCubic / smoothstep |
| −900 … 0 | +2100 … +3000 | full thrust on pad | Full cone, white-hot core, 4 Mach diamonds per engine, slight flicker. Rumble up (smoothstep over 300 ms after ignition). | – |
| 0 | +3000 | **lift-off** (existing event) | The ship climbs on the existing curve. The second, smaller grit wave (40 particles) starts at LO + 150. | – |
| 0 … +2000 | | rumble out | The rumble fades from LO + 800 to LO + 2000 ms. | smoothstep |
| +2500 … +7500 | | vacuum widening | `expand` 0→1. The plume gets 1.6× longer and up to 7× wider at the tail. Envelope opacity ×(1 − 0.6·expand). | smoothstep |
| +3500 … +6500 | | diamonds fade | Diamonds 1→0. | smoothstep |
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
  - Starter ship (4 engines): 2 layers × 4 × 1,920 = **15,360 tris**, plus 2 for the glow quad, plus up to 150 points.
  - If the iPhone fill rate is tight, drop to 16×24 segments. It looks the same at the pad framing.
- **Textures: none (0 KB).** All the noise, the diamonds, the dust chips and the glow are procedural in the shaders, so there's nothing to load or compress. The 256 px budget isn't needed.
- **Shaders:** `ShaderMaterial` with WebGL2 / GLSL ES 3.00. It uses `gl_InstanceID` for per-engine flicker. Each fragment shader has a 4-tap value noise, and the core has a 4-iteration diamond loop.

## 4. Shader uniforms (set from the state object every frame)

| Uniform | Layers | Range | Meaning |
|---|---|---|---|
| `uTime` | plume, core | s | Scroll and flicker clock. |
| `uThrottle` | plume, core | 0–1 | Overall brightness. |
| `uLen` | plume, core | m | Length: plume `24 × len × (1 + 0.6·expand)`, core `9 × len`. |
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
- `LEN` 24 m
- `CORE_LEN` 9 m
- `DIAMOND_N` 4
- `DIAMOND_SP` 1.7 m (the first diamond sits 1.2 m below the exit)
- `DUST_CAP` 150
- `SHAKE_PX` 1.0
- `GRAV` 1.62

Colours:
- Envelope: (0.55, 0.42, 1.0) → (0.32, 0.45, 1.0) along the length.
- Core: (0.42, 0.50, 1.0) → white near the nozzle.
- Diamonds: (1.0, 0.86, 0.95).
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

- **More engines = more instances.** Pass 9 positions and you get 9 flames for the same 4 draw calls. Nothing else changes.
- **Starter ship engine positions:**
  - The pad GLB has the ship merged into one mesh, so there are no engine nodes. The preview finds the 4 bell exits from the mesh, starting from the layout in `build_starter_ship.py` (`ENG_R` 2.25 m, 45° + k·90°, pad yaw +60°).
  - Pad-local glTF positions (m), exit radius 0.87:
    - (−0.569, 1.393, −15.187)
    - (−2.222, 1.393, −12.415)
    - (0.568, 1.393, −10.824)
    - (2.226, 1.393, −13.583)
  - Ship root = `Ship_Placeholder` at (0, 0, −13).
- **Next ship export (my side):** I'll add empties named `Engine_Nozzle_01..N` at each bell exit, with −Y as the thrust axis, so the game can do `ship.traverse(n => /^Engine_Nozzle_/.test(n.name))` instead of hard-coding positions. Lv2 and later ships will carry them too.

## 6. Measurements (headless Chrome 156, SwiftShader CPU renderer, 750×1334 = 375×667 @2x, box under load from other renders)

- **Draw calls:** 11 with the effect off, 15 with it on. That's **+4**, measured at ignition, full thrust and the landing burn. After cut-off, only the dust is left, so it's **+1**.
- **Particles:** peak **149** at lift-off and **150** at landing (the 150 buffer is the hard cap).
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

- **The pad crane mast sits between the camera and the engines**, so at the pad framing it covers a thin vertical strip of the plume. That's part of the pad design and I haven't changed it.
- **The pad GLB keeps `Cargo_Door` as a pad-level node, not under `Ship_Placeholder`.** The preview re-parents it to the ship so it doesn't hang in the air after lift-off. Coder, check how the game moves it today.
- **The close-up proofs** (`*_nozzle_closeup.png`) hide the pad props (crane, tanks, hoses) so the nozzles can be seen. The pad-framing stills show everything.
- **The ground in the preview** is the qa3d vertex-colour fallback look, not the KTX2 M_ground.
