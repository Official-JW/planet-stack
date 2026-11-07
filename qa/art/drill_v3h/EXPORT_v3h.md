# EXPORT_v3h — game-ready replacement drill for Coder/EM

Written Saturday 7 Nov 2026, 1:49 PM PT (America/Los_Angeles).
No new art pass. Study blends were not written. Nothing was written to the repo, `/dev`, live, `qa3d`, `qa3d-next`, or any served folder.

Source opened read-only: `/workspace/art_next/mine_drill_concept_1107/mine_drill_concept_v3h.blend` md5 `88df5e7eaf93df9f27f476118f5b63f1`.
Export-prep changes live only in `mine_drill_v3h_export.blend`.

CURRENT_ASSETS.md was read at 1:42 PM PT. Fresh downloads of the live scene GLBs matched the register:

| md5 | file |
|---|---|
| b1ef349758e9e396fab630f0308088d4 | live `main.js?v=dev1308` (index base `../qa3d/`) |
| c9a9394e3635f99f59423a4630ae6ae7 | mine_revamp_c9a9394e.glb |
| a4a2a4d2cb67f89310f34005a9a40057 | mine_terrain_v3b_a4a2a4d2.glb |
| 205f8acb4897c5df312b57e2d07fb12e | all_truck_trails_205f8acb.glb |
| 76e02e8b1341c17dae0362d13eec0c74 | ht04_76e02e8b.glb |
| 2cfa57a6ec0ad8e9ca566a4e068b2310 | mine_operator_9209246.glb |

## Official GLB

| | |
|---|---|
| path | `/workspace/art_next/mine_drill_concept_1107/export_v3h/mine_drill_v3h.glb` |
| md5 | `a489aa6a3f94ac80d72c4bb61994a9be` |
| size | 141836 bytes |
| generator | gltfpack 1.3 (same as served Mine and operator) |
| compression | `EXT_meshopt_compression` + `KHR_mesh_quantization` |
| Draco | **not used** — the served Mine pipeline does not use Draco |
| triangles | 13242 |
| textures / images | 0 |
| animations | 0 (none exported) |
| materials | 31 named (see below) |
| mesh nodes | 14 named meshes (gltfpack also emits unnamed mesh children, same pattern as the served Mine) |

Uncompressed Blender export (intermediate, same geometry): `mine_drill_v3h_raw.glb` md5 `2ed01933bf41af4f1c607515c2ddbaa9`, 709536 bytes.

Export-prep copy: `mine_drill_v3h_export.blend` md5 `6e3d7dd4eda0b954b1e21c10e08476d2`.
Overlay screenshot: `mine_drill_v3h_over_mine.png` md5 `f8f948efdbc4b8ca5eaca2248da0b34f`.

## Transform and origin

- Served Mine GLB and this export are both glTF **+Y up**, same world origin.
- Blender (Z-up) ↔ glTF (+Y up): `gltf(x, y, z) = blender(x, z, −y)` and `blender(x, y, z) = gltf(x, −z, y)`.
- `Drill_Root` is at `(0, 0, 0)` with identity rotation/scale — drop the GLB in at the same transform as `mine_revamp_c9a9394e.glb` (`Mine` is also at the origin).
- Verification re-import: `Drill_Root` world `(0, 0, 0)` and `Mine` world `(0, 0, 0)` in Blender. Drill bounds overlap the Mine site (blender AABB min `[-13.17, -10.43, -2.57]`, max `[11.37, 5.03, 14.19]`).

### Anchor coordinates

| node | Blender (X, Y, Z) | glTF (X, Y-up, Z) |
|---|---|---|
| Drill_Root | 0, 0, 0 | 0, 0, 0 |
| LED_Mid_A | −6.820, 3.600, 7.350 | −6.820, 7.350, −3.600 |
| LED_Mid_B | −6.820, 3.600, 10.550 | −6.820, 10.550, −3.600 |
| LED_Crown | −7.500, 2.880, 13.870 | −7.500, 13.870, −2.880 |
| Belt_Start | −6.050, 3.200, 1.550 | −6.050, 1.550, −3.200 |
| Belt_End | 9.550, −8.480, 5.580 | 9.550, 5.580, 8.480 |
| Funnel_Spout | 10.500, −9.120, 3.220 | 10.500, 3.220, 9.120 |
| Ore_Spawn | −6.050, 3.200, 1.550 | −6.050, 1.550, −3.200 |
| Ore_Bed_Target | 10.400, −9.100, 2.160 | 10.400, 2.160, 9.100 |
| Cab_Glass | −8.550, 1.525, 2.500 | −8.550, 2.500, −1.525 |
| Operator | −8.851, 2.040, 0.585 | −8.851, 0.585, −2.040 |

`Operator` is the armature-root / mesh origin (at the character root, not eye height). The seated mesh (`Operator_Mesh`) extends up into the cab (visual torso roughly blender Z 2.06–3.06). `Ore_Spawn` coincides with `Belt_Start` (tail pulley). `Ore_Bed_Target` is the truck-bed landing point used in the v3h concept.

All of the above are direct children of `Drill_Root` (flat hierarchy so glTF local == world).

## What is in the GLB

- `Drill_Rig` — tracks, deck, mast, cab structure, cyan trim (`M_RigCyan`), stairs/rails, steel frames.
- `Cab_Glass` (empty) plus panes `Cab_Glass_Front`, `Cab_Glass_Mast`, `Cab_Glass_Rear`, `Cab_Glass_Top` — material `M_CabGlass`.
- `Operator` (empty) + `Operator_Mesh` — seated pose from v3h, baked (armature modifier applied; no skin exported).
- `LED_Mid_A`, `LED_Mid_B`, `LED_Crown` — small emissive meshes, material `M_MastLED`.
- `Conveyor_Gallery` — belt, truss, rollers, walkway, **v3g/v3h supports (bents 0–5, bent 6 absent)**, funnel/hood/spout.
- Ore variants at `Ore_Spawn`: `Ore_Variant_S` (~7 cm), `Ore_Variant_M` (~14 cm), `Ore_Variant_L` (~21 cm), material `M_OreRock`; `Ore_Variant_Glint` (~7 cm), material `M_OreGlint` (slightly metallic/specular, not neon). Coders should instance these along `Belt_Start` → `Funnel_Spout` → `Ore_Bed_Target`.

Excluded (not in the GLB): source Mine, terrain, trails, HT-04 truck, cameras, lights, sweep overlays, labels, render-only glow cards, hidden superseded `Cv_*` gallery, hidden `Oc_Fine_*` / `Oc_Ore_*` blobs, deposits.

Re-import leak check: no excluded Mine/terrain/truck/camera/deposit/sweep nodes came along. (`Conveyor_Gallery` is the new gallery name, not the served `Conveyor` node.) gltfpack added unnamed `Mesh_*` children under named parents — same convention as the served Mine.

## Materials (game-facing)

| role | material name | notes |
|---|---|---|
| cab glass | `M_CabGlass` | three-sided framed glass (+ extra top pane `Cab_Glass_Top`) |
| mast lamps | `M_MastLED` | emissive; v3h authored amber-red `#d44a1c`. Drive this at **1 Hz only while drilling**, **0.5 s on / 0.5 s off**. Game target color specified as amber `~#FFB060`. Off at idle (emission strength 0). |
| operator body | `SHM_Paint.002` | served operator paint; Blender uniquified the name because the Mine already used `SHM_Paint` |
| operator cyan accent | `SHM_GlowCyan.001` | same uniquify from served `SHM_GlowCyan` |
| ore | `M_OreRock`, `M_OreGlint` | gray-brown rough rock; glint is slightly metallic |
| cyan trim | `M_RigCyan` | |
| gallery / supports / funnel | `M_OcBelt`, `M_OcBeltRet`, `M_OcTruss`, `M_OcRoll`, `M_OcFoot`, `M_OcChute2`, `M_OcHood2`, … | |

## Cab interior light (suggestion only — not exported)

Lights were excluded from the GLB. v3h used these to make the seated operator readable:

| name | type | energy | color (linear) | Blender loc | glTF loc |
|---|---|---:|---|---|---|
| CabWarm | AREA (size 0.55) | 18 | (1.00, 0.70, 0.42) | −8.55, 2.42, 2.98 | −8.55, 2.98, −2.42 |
| CabKey | AREA (size 0.45) | 10 | (1.00, 0.78, 0.55) | −8.55, 1.15, 2.55 | −8.55, 2.55, −1.15 |
| CabFill | POINT | 6 | (1.00, 0.76, 0.52) | −8.55, 2.10, 2.30 | −8.55, 2.30, −2.10 |

## Animation timing (not baked into the GLB)

The 96-frame / 12 fps concept loop was **not exported**. Coders should drive ore and lamps in game.

Concept limits (for reference only):

- 12 fps, frames 1–96 (8.000 s).
- Idle: frames 1–12 (lamps off, ore held).
- Drilling: frames 13–96.
- Lamps: CONSTANT 1 Hz from frame 13; 6 frames on / 6 frames off = **0.5 s on / 0.5 s off**.
- Ore travel in the concept was a ~48-frame (4 s) belt → funnel → bed loop. The baked keyframes were dropped on purpose.

## Hide / remove map on served `mine_revamp_c9a9394e.glb`

Exact node names from the served GLB. Hide or remove the node and its descendants. There is **no node named `Hopper`**; the old belt/hopper assembly is `Conveyor`.

**Old rig / derrick**
- `Rig` (child mesh is the old derrick)
- `Drill_Pocket`
- `Dust` (bit-tip empty inside the old pocket)

**Old belts / hopper**
- `Conveyor`
- `OrePath_Bin_00` … `OrePath_Bin_10`

**Old chute**
- `Chute`
- `Chute_Glow`
- `Chute_Exit`

**Old silo**
- `Silo`
- `Silo_BinFill`
- `OrePath_Silo_00` … `OrePath_Silo_06`

**Deposits / Rich_Pop / glows**
- `Deposit_01`
- `Deposit_02`
- `Rich_Pop`
- Materials (do not share/drive on the new drill): `SHM_DepositGlow`, `SHM_DepositRock`, `SHM_ChuteGlow`

`Dep_01` and `Dep_02` are **empty pins** (no deposit mesh). Live code currently keeps them as pins after stripping `Deposit_*`. Leave them unless you also want those pins gone.

Do **not** hide site markers / infrastructure: `Base_Paint`, `Base_GlowCyan`, `Tier_03`, `Tier_05`, `Tier_08`, `Tier_12`, `Tier_20`, `Cam_Target`, `Path_*`, `Crew_Path_*`, `Road_Entry`, `Operator_Deck`.

## Dependencies

- **Operator source:** `mine_operator_9209246.glb` md5 `2cfa57a6ec0ad8e9ca566a4e068b2310`. The seated mesh is **embedded** in this export (pose baked in the blend only). It is not a runtime URL/reference to that GLB.
- **3D truck-sweep clearance is UNVERIFIED.** 2D heading-aware numbers from v3h (supports unchanged from v3g, bent 6 absent, 42 members):
  - 2D swept footprint: min 1.130 m (`Oc_Foot_5_R`), limit ≥ 0.30 m — pass.
  - Trail mesh: min 1.523 m (`Oc_Foot_5_R`), limit ≥ 0.04 m — pass. This is not a claim that the moving truck path is safe.
  - Parked HT-04 mesh: min 4.813 m (`Oc_Foot_5_L`) — clear.

## Verification

- Packed GLB re-imported over the served Mine (Blender 4.2 cannot decode `EXT_meshopt_compression` natively — the same limit as importing the served Mine — so the overlay used `gltfpack -noq -kn` unpacks of the official files).
- All expected named nodes present; `Drill_Root` and `Mine` share the origin.
- Overlay: `/workspace/art_next/mine_drill_concept_1107/export_v3h/mine_drill_v3h_over_mine.png`. The new crawler deck, lattice mast, cab glass, gallery and funnel sit on the Mine at the concept placement; the old white derrick/silo/hoppers remain visible because they have not been hidden in that screenshot.

## Known shortcomings carried from v3h

- Ore sizes in the concept were a 7 / 14 / 21 cm mix (inside the asked 5–25 cm range, not a full continuum). Variants match that mix. The glint variant is the small (~7 cm) metallic piece.
- Rock shapes are chunky displaced cubes — irregular gray-brown, not spheres or yellow blobs, not sharply shattered facets.
- Metallic flecks are faint.
- Crown lamp housings on the concept mast did not show a visible glow; mid-mast lamps did. The exported `LED_Crown` mesh is present for the coder to drive.
- 3/4 operator reads as a seated suited figure; face/gender detail is not sharp; a front mullion crosses mid-torso.
- Concept pour was a populated loop, not an empty bed filling from scratch. Coders own the in-game pour.
- 3D moving clearance remains UNVERIFIED.
