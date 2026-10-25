# Lv1 launch VFX: engine plume (mach diamonds) + lunar dust (AA2, 10/25/2026, pass 2)

**Status: look proof, NOT approved.** Do not wire in or commit until Art Manager / Director OK it.

- **GLB:** `art/vfx/lv1_launch/lv1_launch_vfx.glb` (md5 in the hand-off message). meshopt + KHR_mesh_quantization, no Draco. 1 unit = 1 m, Y up.
- **Built for:** AA3's `aft_skirt_N06_thick.glb` (md5 63d0289d…) on hull `launch_pad_game_lv1ship_clean_v3.glb` (b24e0f08…): 6 bells, re-read from `Engine_Nozzle_0..5` (exit plane y 0.9 in skirt space, ring r 3.05, exit_r 0.84; same positions as the old 344311ab skirt). On clean v3 the skirt hangs on `Aft_Skirt_Seat` (pad-local (0, 0.492, −13)) with identity transform, with no shipSkirtPrep needed.
- **Pass 2 changes:** longer, warmer plume (20 m, orange, dimmer core), 4 big mach diamonds spaced 4.6 m so they can be counted at 393 px, and the dust is now NORMAL alpha blended (darker brown streaks with a light core, so it reads on both the dark deck and the light regolith), reaching 17 m instead of 14 m, still flat/ballistic, with no billow.
- **Budget:** 2 draw calls (1 plume mesh for all bells + 1 dust ring), 500 tris (plume 180, dust 320), 1 texture 512×512 PNG, shared by both materials (one image). Measured in three r169 with the pad + skirt: +2 calls, +500 tris.
- **Sources:** `_src/make_atlas.py` (atlas), `_src/build_vfx.mjs` (GLB). Rebuild: `node build_vfx.mjs <aft_skirt_NXX.glb> lv1_launch_atlas.png raw.glb && gltf-transform meshopt raw.glb lv1_launch_vfx.glb`.

## 1. Nodes (scene roots)

| Node | What | Where to attach |
|---|---|---|
| `Plume_Root` | Translation (0, 0.9, 0) = the nozzle exit plane. **Scale.y = plume length** (1 = 20 m). It is animated. | `cg3.skirt.add(Plume_Root)` (the skirt GLB scene; on clean v3 that's the scene added under `Aft_Skirt_Seat`). The local transform is already in skirt space, so it rides the ship and the gear. |
| `Plume_Mesh` (child) | One merged mesh: 3 crossed quads per bell (60° apart), pointing −Y from each bell. | Comes with Plume_Root. |
| `Plume_0..Plume_5` (children) | Empties at each bell's exit centre (`extras.marker` = `Engine_Nozzle_k`). For reference and lights only; the mesh does not need them. | Comes with Plume_Root. |
| `Dust_Ring` | A low, flat ring on the ground (r 3.5 → 17 m, arc at most 1.1 m, vertex alpha 0 at the inner and outer edges). **Scale x/z = reach, scale.y = arc height**, both animated. | Pad space, **not** the ship: `x/z = Ship_Center`, `y = deck top + 0.02` (0.492 + 0.02 on clean v3 = Aft_Skirt_Seat y). It must not ride the ship. |
| `Plume_Intensity`, `Dust_Intensity` | Driver empties. **scale.x = brightness 0..1**, animated by the clips. | Anywhere under the mixer root (keep them in the scene so the mixer can bind them). |

## 2. Clips (LINEAR, scale tracks only)

| Clip | t = 0 is | Length | What it does |
|---|---|---|---|
| `Plume_Takeoff` | **ignition = LO − 2.0 s** (= HC + 0.8 s in SPEC 1a) | 10 s (to LO + 8 s, end of the climb) | Flicker-on 0–0.21 s, length 0.3 → 1.0 by LO, full burn to the end; intensity drops to 0 at 10 s. |
| `Dust_Takeoff` | same as above | 10 s | Grit from 0.21 s, sheet grows to full reach by LO + 2.5 s. Full until 6.6 s, then the arc collapses (falls straight down, 6.6 → 7.4 s) and fades out by 8.3 s. |
| `Plume_Landing` | **TD − 8.0 s** (start of the `land` run) | 9.6 s | Full plume (intensity 0.85 → 0.95). Cut-off at TD (8.0 → 8.22 s). |
| `Dust_Landing` | same | 9.6 s | Starts at 3.7 s (TD − 4.3 s, ship below about 20 m), builds to full by TD − 1 s, then at TD it falls (8.0 → 8.9 s) and fades by 9.6 s. |
| `Plume_Idle_Off` | – | 0.1 s | Everything at 0 (plume and dust). Use it on the pad and while the ship is away. |

Play one Plume_* and one Dust_* together, `LoopOnce`, `clampWhenFinished = true`. Because everything is a pure function of time, set `action.time` from the cargo clock and call `mixer.update(0)` (works with reload, offline time and `?speed`), as in the preview:
```js
const tL = (t - (liftoffAt - 2000)) / 1000;   // launch clips
const tD = (t - (touchdownAt - 8000)) / 1000; // landing clips
```
**Crew safety stays in game code:** never start the takeoff clips while anyone is outside (same as SPEC §1).

## 3. Materials / per-frame code

Both materials are `KHR_materials_unlit`, `alphaMode BLEND`, double-sided. **The plume is additive (black = nothing); the dust is normal alpha** (its atlas half has a real alpha channel, and COLOR_0 is RGBA with the radial fade in alpha). glTF can't say "additive", so set it after load:
```js
plumeRoot.traverse(m => { if (!m.isMesh) return; const mt = m.material;
  mt.blending = THREE.AdditiveBlending; mt.transparent = true; mt.depthWrite = false; mt.depthTest = true;
  mt.toneMapped = false; mt.forceSinglePass = true;   // forceSinglePass: else three draws double-sided transparent twice (4 calls instead of 2)
  m.renderOrder = 11; m.frustumCulled = false; m.castShadow = m.receiveShadow = false; });
dust.traverse(m => { if (!m.isMesh) return; const mt = m.material;
  mt.blending = THREE.NormalBlending; mt.transparent = true; mt.depthWrite = false; mt.depthTest = true;
  mt.toneMapped = false; mt.forceSinglePass = true; mt.color.setScalar(1);
  m.renderOrder = 10; m.frustumCulled = false; m.castShadow = m.receiveShadow = false; });
// each frame, after mixer.update:
const flick = 1 + 0.06 * Math.sin(t * 0.113) * Math.sin(t * 0.037);           // t in ms; ±6 % shimmer
matPlume.color.setScalar(PlumeIntensity.scale.x * flick * PLUME_GAIN);        // PLUME_GAIN = 1 (Coder-tunable "Plume_Intensity" scale)
matDust.opacity = Math.min(1, DustIntensity.scale.x * DUST_GAIN);              // dust = alpha fade, NOT colour (DUST_GAIN = 1)
plumeRoot.visible = PlumeIntensity.scale.x > 0.002; dust.visible = DustIntensity.scale.x > 0.002;   // 0 draws when off
matDust.map.offset.y = (-1.6 * t / 1000) % 1;                                  // dust streaks fly outward (UV scroll)
```
- **Intensity scale Coder can drive:** `Plume_Intensity.scale.x` (and `Dust_Intensity.scale.x`) are the clip values. Multiply by your own gain (thrust level, throttle) as above. Plume length: you can also multiply `Plume_Root.scale.y` after the mixer (for example 0.8 for a lower thrust level). Keep x/z at 1, since the bells are offset from the root.
- The two materials use **different samplers** (plume clamp, dust repeat-V), so GLTFLoader gives them separate `Texture` objects on one shared image. Scrolling the dust map does not move the plume. If a loader ever merges them, `matDust.map = matDust.map.clone()`.
- **Render order:** dust 10, plume 11 (the alpha-blended dust first, the additive plume on top). depthTest stays on, so the deck hides the part of the plume below it when the ship is low (that is intended, it reads as the plume hitting the deck) and the hull hides the dust behind it.
- The dust radial fade is in COLOR_0 alpha (VEC4; GLTFLoader turns on `vertexColors` automatically and uses the alpha).

## 4. Bell count

The build script reads every `Engine_Nozzle_*` marker in the skirt GLB (N06 → 6 bells). For another ring (N07…N11), rebuild with that skirt file; Plume_0..N−1 and the merged mesh follow (30 tris per bell, still 1 draw). All bells must share one exit plane (the script checks). Proofed on 6 bells only.

## 5. Clearances (pass 2, pad-local metres, checked against the meshes, skinned meshes posed)

- **Plume volume:** per-bell half-width 0.78 + 2.2·√v (≤ 2.98 m at the 20 m tail), so the column stays within 6.03 m of the ship axis.
- **Dust volume:** r ≤ 17.85 m from Ship_Center (17 m × the 1.05 peak scale), top ≤ deck + 1.1 m.
- **Ship gear and doors (thick N06 skirt on clean v3, all gear poses through both runs):** the closest gear/door/leg/foot vertex is **1.729 m** from the plume (Gear_Knee_1, gear stowed), against AA3's 1.64 m limit, so it passes by 0.09 m. Deployed legs, doors open: 1.740 m (Gear_Door_3b). The feet below the exit plane: 1.747 m (Gear_Foot_2 at touchdown). The fixed skirt shell right next to a bell (r 1.15 m from that bell's axis, 1.25 m *above* the exit plane) is 1.30 m from the exit-disc edge. The plume only points down, so that point is bell-adjacent structure, not a plume hit. Raw: `proofs/skirtclear_launch.json`, `proofs/skirtclear_land.json`.
- **PC-1 crane, moved (AA1's `/workspace/pad_fuelline/launch_pad_game_lv1ship_v4_crane.glb`, 11:29, md5 5fcd4d67…; footing at (3.5, 0, 8.32), 21.6 m from the ship):** rest pose: plume **13.94 m**, dust **2.07 m** (footing at (2.0, 0, 6.82)). Any slew: dust clears the jib by **16.46 m**. The plume is only reached if the jib is slewed over the ship (−0.89 m at y 19.9), as before.
- PC-1 crane in clean v3 (old spot (0.6, 0, 7)), for reference: plume 12.48 m, dust **0.60 m** (the wider dust nearly reaches the old footing). Any slew: dust 16.42 m; jib over the ship −1.17 m.
- **Cargo Space Dock v4** (`cargo_dock_c16d8565.glb` at world (480, 0, −8)): plume **126.6 m**, dust **114.7 m**.
- Raw numbers: `proofs/clearance_measure.json`. Pass-1 proofs are in `proofs/pass1/`.
