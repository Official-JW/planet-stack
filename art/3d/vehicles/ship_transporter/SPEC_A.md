# ST-10A game GLB (Lv10 ship transporter, tracked crawler): ACTIVE concept

**Status:** the Director picked concept A on 10/24/2026. Concept B (`st10b_game.glb`, `SPEC.md`) is **SHELVED** (commit 7bd022c).

**File:** `art/3d/vehicles/ship_transporter/game/st10a_game.glb`
- md5 **934e9c9f0350f539b99ca99e4c23fa0c**, 135,104 bytes.
- gltfpack `-c -kn -km`, so it uses EXT_meshopt_compression, KHR_mesh_quantization and KHR_materials_emissive_strength. Load it with `GLTFLoader.setMeshoptDecoder(MeshoptDecoder)`.
- Source: `_src/build_st10a_game.py` (pure numpy, about 0.4 s; `--emis k` sets the Paint emissive). Build log: `game/st10a_game_build.json`.
- Astronaut mesh: `_src/astronaut_tender_game.npz` (taken from the ST-10B tender astronaut).

## Nodes (glTF metres, +X = direction of travel toward the Shipyard, +Y up, +Z toward the camera; origin = ground centre under the ship axis)
```
ST10A
├─ Body_Paint      4 twin-track trucks (crawler tread: shoes with cleats on a stadium belt, 12-side sprockets, roller boxes,
│                  truck frames, levelling jacks), 2 box girders (z ±9.7..13.3), 2 cradle towers (35.5 m) with bracing,
│                  rear cross girder (x 11..15.5), power modules + radiator fins, autonomous control pod (NO cab), antennas
├─ Body_GlowCyan   running lights                                   (ST10A_GlowCyan, emissive strength 2.5)
├─ Body_GlowAmber  tower beacons + antenna tips                     (ST10A_GlowAmber, emissive strength 2.5)
├─ Cradle_Loaded   3 clamp rows of arms + pistons + 70° saddles closed on the hull, front gate beam closed at x -12.5
├─ Cradle_Empty    saddles opened 3.2 m; gate as two leaves folded against the inner girder faces (open for drive-in)
├─ Astronaut       one tender astronaut, on foot, at Tender_Spot
├─ Ship_Seat       empty node (0, 0.45, 0): ship origin when loaded (jacks lift the ship 0.45 m)
└─ Tender_Spot     empty node (-8.57013226, 0, 16.5): where the astronaut stands
```
gltfpack adds an unnamed dequantise child under each mesh node, so look meshes up by the **parent** name.

**Cradle state (Coder): show exactly ONE of `Cradle_Loaded` / `Cradle_Empty`.** Loaded means the ship sits at Ship_Seat, 0.45 m up. Empty means the ship has been set down or is gone. The crawler drives in along +X with its open end (x −12.5, gate folded) first: it backs over the standing ship.

## Draws and tris (5 draws per state, 6 primitives in the file, budget ≤ 8)
| node | material | tris |
|---|---|---|
| `Body_Paint` | ST10A_Paint (rough 0.7, metal 0, COLOR_0, emissive (0.3467, 0.4564, 0.6867) × k, k = 0.09) | 8,688 |
| `Body_GlowCyan` | ST10A_GlowCyan | 144 |
| `Body_GlowAmber` | ST10A_GlowAmber | 48 |
| `Cradle_Loaded` | ST10A_Paint | 1,932 |
| `Cradle_Empty` | ST10A_Paint | 1,968 |
| `Astronaut` | ST10A_Paint | 899 |
| **visible, loaded / empty** | | **11,711 / 11,747** (13,679 in the file) |

Bounds: body x −12.64..15.64, y 0..35.5 (beacons 36.5), z ±13.56 (27.12 m wide, 29.0 m long, about 28.3 m with the loaded gate). Loaded height with the Lv2 ship is 44.55 m.

## Game-cam shade (target: shaded side p25 60–75 at 375 and 393, ≥ 5 px spare at 375): PENDING, QUEUED
B was measured at k = 0.09 (p25 65–67.8). A uses the same paint, emissive and method; `_src/gamecam.html` now matches `ST10[AB]_Paint`, and `_src/gamecam_b_game.js` takes `TAG=st10a`. Box hold: nothing has been rendered.
- **Queue:** `/workspace/st10a/queue_render.sh`. It runs `queue_inner.sh` under `flock /tmp/planet_stack_heavy.lock nice -n 19 … -t 4`, after any Playtester or crew job.
- **What it does:**
  - sweeps k 0.06–0.12;
  - if k ≠ 0.09, rebuilds and repacks, **which changes the md5 above**;
  - renders 12 frames to `proofs/gamecam_a_game/` (loaded and empty at 375 and 393, as in `proofs/gamecam_b_game`);
  - redraws `proofs/transport_road_plan_topdown.png` (v5: `_src/road_plan_v5.py --png`).
- **Run time:** about 2.5–3 min on an idle box, up to about 6 min under load.

## Clearance (light check, no renders): `_src/clearance_st10a.py` → `proofs/clearance_st10a.json`; `_src/saddle_yaw_check.py` → `proofs/saddle_yaw_check_st10a.json`
- **Inputs (read-only):**
  - aft skirt `art/vfx/engine_flame/aft_skirt/aft_skirt_N11.glb` (md5 2be354a3ab28eff1cb24c9abe5c8872b) and `aft_skirt_N06.glb` (02b52680304aa9ed80962b5bd3c71d96), skinned per pose: rest (deployed), retracted, deploy_end, and every 0.1 s of Gear_Retract (3.2 s) and Gear_Deploy (3.6 s);
  - hull `art/3d/ship/ship_lv2/pad_lv2.glb`.
- **Sweep:** ship yaw 0–75 in 15° steps (the gear is 4-fold and the crawler is mirror-symmetric); module height Y_M 0.492 (feet on the 0.25 deck) and 3.45 (AA Engine_Ring_Mount); empty drive-in at ship x −32..0 in 2 m steps.
- **Precision:** transporter surfaces sampled at 0.4 m, so ±0.3 m (box hold: light check). "≥ 4" = beyond the 4 m search radius.

| check | min clearance (m) | where |
|---|---|---|
| Loaded: aft skirt band vs cradle | **2.96** | Y_M 3.45, yaw 30 |
| Loaded: gear doors vs cradle | 3.45 | Gear_Retract@0.6 s |
| Loaded: gear legs vs cradle (all clip frames) | 3.31 | Gear_Deploy@2.0 s |
| Loaded: engine ring + nozzles vs cradle and body | ≥ 4 | |
| Loaded: gear legs vs body | **0.71** | Gear_Foot mid-deploy (2.0 s, r about 8.8) vs girder inner face z 9.5; deployed or retracted legs ≥ 2.9 |
| Loaded: skirt, doors, ring vs body | ≥ 4 | |
| Empty drive-in: gear legs vs cradle (folded gate leaves) | **2.50** | Y_M 3.45, yaw 30, x −4 |
| Empty drive-in: gear legs vs body | 2.97 | x −12 |
| Empty drive-in: gear doors / skirt band vs cradle | 3.80 / 3.51 | |
| Empty drive-in: engine ring + nozzles | ≥ 4 | |
| Empty drive-in: hull vs open saddles (KD) | **0.32** | yaw 75, x −4 |
| Empty drive-in: hull vs open saddles (signed, all 72 yaws in 5° steps) | **0.29** (Y_M 0.492) / 0.70 (Y_M 3.45) | ladder/box features r 5.63 at hull y 24.5–26.8 |
| Loaded: hull vs saddles | 0.025–0.039 **design contact** (RUB 0.03) | Y_M 0.492 |
| Loaded: hull vs body (towers, girders) | ≥ 4 | |

**The cradle clears the aft skirt, the gear (retracted, deployed and every clip frame), the ring and the nozzles by at least 2.50 m. The body clears them by at least 0.71 m** (mid-deploy foot vs girder; ≥ 2.9 m at rest).

### Constraints and flags
1. **Ship yaw on the crawler.** The Lv2 hull has a ladder cage / box cluster at hull azimuth 10–50° (r 5.22–5.63) that must not face a saddle.
   - Loaded fits at ship yaw **345–75° or 165–255°** (yaw about +Y, same convention as the check). Pad yaw 60 is inside the first range, with 15° to spare.
   - At other yaws a saddle cuts into those features by up to 1.19 m.
   - No hull row above y 31 is clean all the way round, so this limit is inherent to a 3-row side clamp.
2. **Module frame.** The clamp radii fit the 0.492 frame: ship base on the 0.25 deck, gear feet at −0.242, the same as B.
   - With AA's scratch Lv2 Engine_Ring_Mount at y 3.45, the hull rides 2.96 m higher and all three loaded saddles cut in by 0.10–0.23 m at every yaw.
   - If AA keeps 3.45, rebuild with the new radii (`CLAMPS` in the build script). It's a one-line change, about 0.4 s.
3. **Ship height.** There is no Lv10 ship yet, so the Lv2 ship (43.85 m) was used. Loaded top 44.55 m leaves 1.45 m under D-10 (46 m). Flagged in the road plan as well.
4. The Lv2 committed files still carry the Lv1 legs; the skirt modules N06/N11 were used for the gear.
5. **Shade numbers are pending** until the queue runs. If the sweep picks k ≠ 0.09, the GLB md5 changes.

## Transport road v5 (10/24/2026, station order d729465: Cargo Space Dock 480 | Launch Pad 640 | Shipyard 800)
- **GLB:** `game/st10a_transport_road.glb`, one mesh `ST10A_TransportRoad`, material `ST10_Road` (roughness 0.92), vertex colour only (gltfpack `-cc -kn -ke -vpf`, like `_shared/road/haul_road_seg.glb`). Place at world (669.5, 0, −13), no rotation.
- **Look:** compacted regolith, 34.62 m running width (ST-10A 27.12 m + 3.75 m each side), 2.6 m dusty shoulders (39.82 m graded), surface y 0.045. Two dark crawler lanes at |w| 9.7–13.3 m with track-cleat imprints 0.40 m every 1.24 m, and survey edge dashes.
- **Path (crawler ship axis):**
  - pick-up at the pad Ship_Center (640, −13), heading +X;
  - straight to x 682.0 (42.0 m), leaving the pad's right side on the far side (−Z);
  - one right arc, R 100 m through 40° (69.81 m), centre (682.0, 87.0);
  - straight 11.21 m at heading 40° into Shipyard Road_Entry (754.871, 0.23, 17.604).
  - **Length 123.03 m.** One turn, no S-bend, minimum radius 100 m.
  - The road mesh runs from the pad edge x 669.5 to Road_Entry (93.53 m).
- **Crawler stop:** Shipyard props sit at the entry (x 752–767.5, z −2.5..14, up to 25.5 m). The last pose with ≥ 2 m gap from the footprint is at s 98.35 m: ship axis (735.42, 2.46), heading 32.3°, gap 2.22 m, leading face 9.04 m short of Road_Entry. The far side of the road end is trimmed to the prop-free envelope from s 112.3; the camera side runs full width to Road_Entry.
- **Other roads:** none crossed.
  - Flatbed lanes z 23 and z 32 (toes z 20.2–34.8): 29.9 and 35.2 m clear.
  - Their pad U-turn (x ≤ 648.3, z ≥ 20.2): 27.9 m clear.
  - Haul road: 391 m clear.
  - **Near x 640 the road uses z −32.91..6.91** (running −30.31..4.31; crawler footprint −26.56..0.56; ship skirt/gear −19.6..−6.4).
- **Cargo Space Dock (x 480, bbox x ≤ 519.5):** 107 m west of the crawler's rear at pick-up and 150 m from the road mesh; the road never passes it.
- **Pad flags (owner pad/AA2; db78a6f7 is not edited):** see `proofs/transport_road_plan.json` → flags.
  - No right-side gate: berm 2.5–4.5 m, x 656–668, z −28..−2. Needs G-1, 30.8 m wide, z −28.4..2.4.
  - Pylon blocks 9–12 m at x 654–658 / z −20..−16 and x 652–656 / z −6..−2.
  - Tier_08.
  - Hoses must disconnect before the move.
  - Pipe_LaunchPad_End (660.3, −9.6) is on the right under the crawler.
- **Aft skirt / gear:** in the crawler frame this is unchanged (see Clearance). Along the road, the skirt/gear (r 6.6) and hull (r 5.7) sweep only meet pad-owner items (above) and nothing beyond the pad edge before the stop pose.
