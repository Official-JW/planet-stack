# Refinery bridge v5.3: open-front lowerator

`refinery_bridge_v5_3.glb` is a new file. `refinery_bridge.glb` (v5.2, md5 bc081489…) is left untouched.

- Source: `_src/build_bridge_v5_3_open.py`. It builds on the ideas in `_src/build_bridge_v5_3_next.py` (the v8 candidate). v8 still measured box 61.5 % and carriage 66.9 %.
- Build: `blender -b -P _src/build_bridge_v5_3_open.py -- raw.glb --box cargo_box_plain.glb`, then `gltfpack -cc -kn -ke -af 10`.
- Check: `node _src/bridge_visibility_check.mjs refinery_bridge_v5_3.glb out.json`. This replicates the Coder's raycast metric: 121 samples, official camera, 393x852 and 375x667.

## What changed (lowerator only)

- **Mast moved to the back.** The full-height mast, rack, hoist head, sheave, cable and CV-3 sign move from the camera-side corner to the back-left corner, behind the carriage. The carriage now hangs forward off the mast.
- **Camera side of the top bay is open.** The static end-stop bar and its tie are gone. A 2 cm amber nose lip on the carriage stops the box instead.
- **West guide rails on the back half only.** They run from y 3.6 to 9.0 and tie back to the mast. The static top-level west guide is removed. The span's west guide extension now stops 0.45 m short of the mast.
- **Ground conveyor.** The camera-side guide wall, its cap and its cyan strip now start 1.7 m west of the lift.
- **Carriage.** The slats, the under-deck arm and brace, and the wrap-around clamps are removed (all of them sat behind the box). One shoe plate and a bracket ride on the rack. A white front and east skirt sits below the deck top, with a cyan strip and amber/graphite chevrons.

## Results

- **Visibility, 393x852 and 375x667:** the box is 100 % visible at all 39 on-carriage samples. The carriage is at least 80.6 % visible at every one of the 121 samples (393: 83.0 %; 375: 80.6 %). Data: `proofs/refinery_bridge_v5_3_visibility.json`.
- **Clips (box_path / box_convey):**
  - 0 touching frames.
  - Box clearance is at least 0.119 m.
  - Carriage-to-static gap is at least 0.022 m (the shoe at the rack, same as v5.2).
- **Footprint:** the bbox xz is -1.925..18.249 by 4.313..19.164. That is within v5.2 (19.181).
- **Unchanged from v5.2:**
  - root pivot (12.28, 0, 12.25)
  - 4 draws (2 meshes × SHM_Paint + SHM_GlowCyan)
  - clips box_convey 44.0 s, box_path 33.9 s, roller_spin
  - lane E is still clear
