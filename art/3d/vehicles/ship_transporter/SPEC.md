# ST-10B game GLB (Lv10 ship transporter, wheeled straddle)

**File:** `art/3d/vehicles/ship_transporter/game/st10b_game.glb`
- md5 **801941fdd5d399510107b675fc788a42**, 157,728 bytes.
- gltfpack `-c -kn -km`, so it uses EXT_meshopt_compression, KHR_mesh_quantization and KHR_materials_emissive_strength. Load it with `GLTFLoader.setMeshoptDecoder(MeshoptDecoder)`.
- Build log: `game/st10b_game_build.json`.

## Nodes (glTF metres, +X right / direction of travel toward the Shipyard, +Y up, +Z toward the camera; origin = ground centre under the ship axis)
```
ST10B
├─ Body_Paint        frame, legs, wheels, deck, Cab-less pods        (ST10B_Paint, vertex colours)
├─ Body_GlowCyan     running lights                                  (ST10B_GlowCyan, emissive 2.5)
├─ Body_GlowAmber    warning lights                                  (ST10B_GlowAmber, emissive 2.5)
├─ Cradle_Loaded     cradle jacks closed on the ship                 (ST10B_Paint)
├─ Cradle_Empty      cradle open, clamp ring raised                  (ST10B_Paint)
├─ Astronaut         tender astronaut, on foot, at Tender_Spot       (ST10B_Paint; visor/suit glows baked into COLOR_0)
├─ Ship_Seat         empty node (0, 0.45, 0): ship origin when loaded (jacks lift 0.45 m)
└─ Tender_Spot       empty node (-8.57, 0, 16.5): where the astronaut stands
```
gltfpack adds an unnamed dequantise child under each mesh node, so look meshes up by the **parent** name.

**Cradle state (Coder): show exactly ONE of `Cradle_Loaded` / `Cradle_Empty`.** Loaded means the ship sits at Ship_Seat, 0.45 m up. Empty means the ship is gone.

## Draws and tris
| node | material | tris | tris before decimation |
|---|---|---|---|
| `Body_Paint` | ST10B_Paint | 8,148 | 20,228 |
| `Body_GlowCyan` | ST10B_GlowCyan | 132 | 132 |
| `Body_GlowAmber` | ST10B_GlowAmber | 320 | 320 |
| `Cradle_Loaded` | ST10B_Paint | 2,699 | 11,696 |
| `Cradle_Empty` | ST10B_Paint | 2,700 | 11,696 |
| `Astronaut` | ST10B_Paint | 899 | 3,360 |

- **Draws: 5 visible** in either state: Body_Paint, GlowCyan, GlowAmber, one cradle, Astronaut. The astronaut counts as **1** of them. Budget is 8 or fewer. The file holds 6 meshes, 3 materials.
- **Tris visible:** 12,198 loaded / 12,199 empty (budget about 13k). The file holds 14,898 because both cradles are in it.
- Measured in-page with `renderer.info.render` and only the transporter visible: **calls 5, triangles 12,198 / 12,199** in all 8 frames.
- Changes from the hero mesh:
  - Paint colours are baked to COLOR_0 under one material.
  - Wheels are rebuilt as a 12-side tyre plus an 8-side hub.
  - Removed: grousers, spokes, rims, hubcaps, labels, ladder rungs, rail posts, deck ribs, pad edges, eyes, glands, lidar bands and vents.
  - Then quadric decimation per node, and smooth-by-angle at 35°.

## Shaded side (game-cam lighting unchanged: Hemi 0x9fb4d8/0x2a2a30 at 0.55, Dir 0xfff4e2 at 2.6 from (-30k, 22k, 18k), ACES, sRGB)
- The fix is a **material value, not lighting.** `ST10B_Paint` gets emissiveFactor = sky tint 0x9fb4d8 (linear) × **0.09**, which is [0.0312, 0.0411, 0.0618].
- Why: the shaded side gets only hemisphere light. An albedo lift saturates at p25 ≈ 36 (sweep: +0.45 lift gives 36.2). Emissive k: 0 → 33.2 / 31.5, 0.06 → 57 / 56, **0.09 → 67 / 66**, 0.12 → 76.6 / 75.8, 0.15 → 85.5 / 84.7 (loaded / empty). See `proofs/gamecam_b_game/sweep.json`.
- Measurement (`_src/gamecam.html` `p25()`): sRGB luminance of transporter pixels whose world normal faces away from the sun (N·L < 0.05). Glow meshes are excluded.
- **Fix 10/24:** p25() never placed the sun, so it measured under the default overhead light, which gave a bogus ≈ 36 everywhere. `light(t)` is now called in shot(), p25() and calls(). The @2x frames are now true 2x (setSize updates the canvas style); before, they were a magnified crop.

## Frames (`proofs/gamecam_b_game/`): 38° vFOV, 18° down, Cam_Target from the joint solve, spare ≥ 5 px in both safe bands
| frame | spare px | draw calls | tris | shaded p25 | shaded p50 | lit p50 |
|---|---|---|---|---|---|---|
| loaded_393x852 | 63 | 5 | 12198 | 67 | 69.8 | 169.9 |
| loaded_375x667 | 6 | 5 | 12198 | 67.8 | 69.8 | 169.1 |
| loaded_393x852@2x | 63 | 5 | 12198 | 66 | 69.8 | 171.1 |
| loaded_375x667@2x | 6 | 5 | 12198 | 66 | 69.8 | 171 |
| empty_393x852 | 63.4 | 5 | 12199 | 66 | 69.8 | 168.8 |
| empty_375x667 | 6 | 5 | 12199 | 67 | 69.8 | 169 |
| empty_393x852@2x | 63.4 | 5 | 12199 | 65 | 69.8 | 169.9 |
| empty_375x667@2x | 6 | 5 | 12199 | 65 | 69.8 | 169.8 |

- Shaded p25 is **65–67.8** in all 8 frames (target 60–75). **Spare at 375 is 6.0 px** for both states (≥ 5).
- Safe bands: 393 = [12, 381, 165, 534]; 375 = [12, 363, 144, 383].
- Poses (Cam_Target, frame_w):
  - loaded: (53.5, 3.8, -11.6), fw 77.0
  - empty: (53.5, 0.8, -11.6), fw 52.7
  - (transporter at pad-local x 52, z -13)
- Files: `st10b_game_{loaded,empty}_gamecam_{393x852,375x667}[@2x][_clean].png`. The non-clean frames carry the overlay (safe band red, bbox cyan, label). Numbers are in `results.json`.

## Build (heavy steps under `_src/run_heavy.sh` = `flock /tmp/planet_stack_heavy.lock nice -n 19 …`)
```
blender -b -t 4 -P _src/build_st10b_game.py -- --loaded st10b_loaded_preview.glb --empty st10b_empty_preview.glb --out raw.glb --lift 0
python3 _src/set_paint_emissive.py raw.glb raw_e.glb 0.09
gltfpack -i raw_e.glb -o game/st10b_game.glb -c -kn -km
node _src/gamecam_b_game.js sweep|final http://127.0.0.1:8771 <out> m/st10b_game.glb   # server started OUTSIDE the lock
```
