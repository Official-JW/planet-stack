# Crew boarding — timing sheet

Generated from `crew_boarding_timing.json` (build_boarding.py). Global time in seconds from the start of `crew_call`; key rate in the GLB is 15 Hz, source sampled at 30 fps.

## Clips (play back to back, each clip starts at its own local 0)

| clip | global start | global end | duration |
|---|---|---|---|
| `crew_call` | 0.00 | 3.000 | 3.000 |
| `crew_walk_to_pad` | 3.00 | 22.300 | 19.300 |
| `crew_climb` | 22.30 | 58.500 | 36.200 |

Total: **58.50 s**. Rung pair cycle **1.0 s** (2 rungs = 1.2 m per cycle, 1.20 m/s). Climber stagger (mount to mount) **3.4 s**.
After `inside_hatch` the crew member's Root is scaled to 1e-4 (hidden) and holds that pose to the end of `crew_climb`.

Ladder (measured from launch_pad_game.glb, ship-leg ladder on the +X/+Z side): rungs at y = 0.65 + 0.6·i, i = 0..34 (top rung 21.05 m), stile tops / deck top 21.85 m.

Pad-local frame used for the landing (same as Art Assistant 2): u along the 330° ladder axis from Ship_Center (glTF (0, ·, −13)), t sideways (t = (p − C)·(0.5, 0, −0.866)), z = glTF y. The crew root sits at the pad origin.

## Board_Focus / Board_Focus_Top (empty nodes in the GLB, children of CrewBoarding)

- camera: plain lookAt at the node (no setViewOffset), 38 deg vFOV, 18 deg look-down, game yaw; distance from frame_w as in qa3d-next fitSite(): d = (frame_w/2) / (tan(19 deg) * aspect)
- switch: Board_Focus from crew_climb start; Board_Focus_Top once C1_Hips world y >= 14 m (fallback crew_climb clip-local 12.792 s, absolute 35.092 s)
- **Board_Focus**: translation [3.854, 11.05, -10.775], extras frame_w 105.9; trigger `{"bone": "C1_Hips", "alt_bone": "C1_Head", "threshold_y_m": 14.0, "y_space": "this GLB root space (pad-local: ladder foot 0.25, deck 21.85); add the pad root world Y if the GLB is offset", "rule": "use Board_Focus until the bone world Y >= threshold, then ease to Board_Focus_Top", "fallback_clip": "crew_climb", "fallback_clip_local_s": 12.792, "fallback_absolute_s": 35.092, "alt_bone_fallback_clip_local_s": 12.293, "alt_bone_fallback_absolute_s": 34.593, "absolute_time_base": "crew_call 0-3.0 s, crew_walk_to_pad 3.0-22.3 s, crew_climb 22.3-58.5 s played back to back"}`
- **Board_Focus_Top**: translation [3.854, 15.861, -10.775], extras frame_w 16.1; trigger `{"bone": "C1_Hips", "alt_bone": "C1_Head", "threshold_y_m": 14.0, "y_space": "this GLB root space (pad-local: ladder foot 0.25, deck 21.85); add the pad root world Y if the GLB is offset", "rule": "use Board_Focus until the bone world Y >= threshold, then ease to Board_Focus_Top", "fallback_clip": "crew_climb", "fallback_clip_local_s": 12.792, "fallback_absolute_s": 35.092, "alt_bone_fallback_clip_local_s": 12.293, "alt_bone_fallback_absolute_s": 34.593, "absolute_time_base": "crew_call 0-3.0 s, crew_walk_to_pad 3.0-22.3 s, crew_climb 22.3-58.5 s played back to back"}`

| node | viewport / band | distance m | crew px | spare top px | spare bottom px |
|---|---|---|---|---|---|
| Board_Focus | 375x667 band 144-383 (HUD bottom 120 + 24; bar) | 273.52 | 6.1 | 152.4 | 5.0 |
| Board_Focus | 393x852 band 184-489 (375 band scaled by 852/667) | 333.38 | 6.4 | 203.2 | 16.5 |
| Board_Focus | 393x852 band 165-534 (qa3d-next band() with iPhone safe-area insets 59/34) | 333.38 | 6.4 | 222.2 | 61.5 |
| Board_Focus_Top | 375x667 band 144-383 (HUD bottom 120 + 24; bar) | 41.58 | 40.3 | 5.6 | 5.1 |
| Board_Focus_Top | 393x852 band 184-489 (375 band scaled by 852/667) | 50.68 | 42.3 | 51.0 | 16.5 |
| Board_Focus_Top | 393x852 band 165-534 (qa3d-next band() with iPhone safe-area insets 59/34) | 50.68 | 42.3 | 70.0 | 61.5 |

Per-crew timings in the format landing_clear_v3.mjs takes: `{"Crew_1": {"s": 41.62, "i": 47.79, "side": 1}, "Crew_2": {"s": 45.02, "i": 51.19, "side": -1}, "Crew_3": {"s": 48.42, "i": 54.59, "side": 1}, "Crew_4": {"s": 51.82, "i": 57.99, "side": -1}}`

## Phases per crew member

| crew | role | call | walk start | at ladder / queue spot | mount (first reach) | climb start | climb top | on deck (mantle done) | inside hatch (hidden) | ladder time |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Cargo Manager | 0.00–3.00 | 3.75 | 22.29 | 23.09 | 23.99 | 41.33 | 44.33 | 47.79 | 21.24 |
| 2 | Crew 2 | 0.00–3.00 | 3.65 | 24.18 | 26.49 | 27.39 | 44.73 | 47.73 | 51.19 | 21.24 |
| 3 | Crew 3 | 0.00–3.00 | 5.20 | 24.59 | 29.89 | 30.79 | 48.13 | 51.13 | 54.59 | 21.24 |
| 4 | Crew 4 | 0.00–3.00 | 7.50 | 26.92 | 33.29 | 34.19 | 51.53 | 54.53 | 57.99 | 21.24 |

Phase notes: *call* = Cargo Manager (crew 1) hand to helmet radio 0.2–2.95 s and points to the pad 1.35–3.1 s; crew 2–4 raise a hand to acknowledge. *walk* = planted-foot gait along the shared route around the ship-leg pad; crew 2–4 wait at queue spots by the ladder and step to the ladder foot before their mount (mounts are chained: each is at least one stagger after the previous). *climb* (v3) = the arms do the climbing (hand-over-hand on the rungs, curled grip); the boots trail under the body, toes down, >= 3 cm behind the rungs (AA2 v3 gate: a boot near a rung must be still). *mantle* = see the hatch landing section.

## Hatch landing: mantle + walk-in per climber (Art Assistant 2 option 1 landing)

Open well u 4.05–5.15, |t| < 0.62 (no deck in front of the hatch); kerb |t| 0.62–0.68 (top z 21.88); wing stand area u 4.3–4.7, |t| 0.75–1.25, deck top z 21.85. v3: the climb ends low with the gloves on rungs 33/34; the hands move up onto the stiles and the climber presses up; the lead boot goes out through the cage side opening, over the kerb, and is SET DOWN slowly on the wing (still-sole rule), the trail boot follows; walk-in: each wing boot is lifted slowly, crosses the kerb >= 3 cm high and lands in the doorway (0 plants in the well, 0 on the kerb).

| crew | step-off side | through-hole start (climb top) | through-hole end (both boots on the wing) | hands off | walk-in end (inside hatch, hidden) |
|---|---|---|---|---|---|
| 1 | +t (lead Foot_R) | 41.33 | 44.72 | 44.33 | 47.79 |
| 2 | -t (lead Foot_L) | 44.73 | 48.12 | 47.73 | 51.19 |
| 3 | +t (lead Foot_R) | 48.13 | 51.52 | 51.13 | 54.59 |
| 4 | -t (lead Foot_L) | 51.53 | 54.92 | 54.53 | 57.99 |

Foot plants at deck height (sole centre u, t, z; land time = contact). `mantle` = step-off onto the wing, `walk_in` = steps to the hatch (the last plants are inside the hatch, u < 3.9).

<details><summary>Crew 1 plants</summary>

| land s | foot | target u | target t | z | phase | measured sole box u | measured sole box t | where |
|---|---|---|---|---|---|---|---|---|
| 44.16 | Foot_R | 4.520 | 0.800 | 21.852 | mantle | 4.304–4.613 | 0.732–0.863 | wing |
| 44.72 | Foot_L | 4.740 | 0.920 | 21.852 | mantle | 4.524–4.833 | 0.854–0.984 | wing |

</details>

<details><summary>Crew 2 plants</summary>

| land s | foot | target u | target t | z | phase | measured sole box u | measured sole box t | where |
|---|---|---|---|---|---|---|---|---|
| 47.56 | Foot_L | 4.520 | -0.800 | 21.852 | mantle | 4.302–4.611 | -0.866–-0.736 | wing |
| 48.12 | Foot_R | 4.740 | -0.920 | 21.852 | mantle | 4.523–4.832 | -0.986–-0.856 | wing |

</details>

<details><summary>Crew 3 plants</summary>

| land s | foot | target u | target t | z | phase | measured sole box u | measured sole box t | where |
|---|---|---|---|---|---|---|---|---|
| 50.96 | Foot_R | 4.520 | 0.800 | 21.852 | mantle | 4.304–4.613 | 0.732–0.863 | wing |
| 51.52 | Foot_L | 4.740 | 0.920 | 21.852 | mantle | 4.524–4.833 | 0.854–0.984 | wing |

</details>

<details><summary>Crew 4 plants</summary>

| land s | foot | target u | target t | z | phase | measured sole box u | measured sole box t | where |
|---|---|---|---|---|---|---|---|---|
| 54.36 | Foot_L | 4.520 | -0.800 | 21.852 | mantle | 4.302–4.611 | -0.866–-0.736 | wing |
| 54.92 | Foot_R | 4.740 | -0.920 | 21.852 | mantle | 4.523–4.832 | -0.986–-0.856 | wing |

</details>

## Measured checks (three r186 skinned playback of the shipped GLB)

- **glb**: `{"bytes": 252360, "draws": 4, "tris": 10772, "three": "186", "clips": [["crew_call", 3], ["crew_walk_to_pad", 19.3], ["crew_climb", 36.2]]}`
- **contacts_r186**: `{"foot_max_err_vs_ref_m": 0.0935, "hand_max_err_vs_ref_m": 0.0752, "planted_foot_slide_max_m": 0.0052, "gripping_hand_slip_max_m": 0.0093, "planted_foot_drift_max_m": 0.0063}`
- **planted_foot_slide_percentiles_m**: `{"p50": 0.0004, "p95": 0.0034, "p99": 0.0046, "max": 0.0052, "n_frames": 3879, "over_5mm": 4}`
- **planted_foot_drift_from_plant_start_m**: `{"p95": 0.0033, "max": 0.0063}`
- **worst_at**: `{"foot_max_err_vs_ref_m": {"t": 32.2, "crew": 4, "limb": "Foot_L"}, "hand_max_err_vs_ref_m": {"t": 32.37, "crew": 4, "limb": "Hand_R"}, "planted_foot_drift_max_m": {"t": 3.87, "crew": 1, "limb": "Foot_R"}, "planted_foot_slide_max_m": {"t": 18.77, "crew": 2, "limb": "Foot_R"}, "gripping_hand_slip_max_m": {"t": 48.53, "crew": 3, "limb": "Hand_L"}}`
- **ik_target_reach**: `{"max_ratio": 1.0501, "at": {"crew": 3, "t": 50.1, "limb": "armR", "A": [4.14, 22.33, -10.9], "T": [4.04, 21.76, -10.84]}, "note": "IK target distance / limb length; limbs are rigid (never stretched), >1 = the target is missed by that fraction for a frame"}`
- **climber_clearance**: `{"frames": 1087, "t_range": [22.3, 58.4996], "min_mesh_gap_m": 0.047, "min_mesh_gap_at_t_crewA_crewB": [25.7, 1, 2], "min_boot_to_glove_m": 0.108, "min_boot_to_glove_at_t_upper_lower": [53.1997, 3, 4], "frames_under_10cm": 28, "frames_touching_under_2cm": 0}`
- **climber_clearance_note**: `"v4: fixed. The mantle (climb top -> on deck) is 2.0 s shorter (5.0 -> 3.0 s, warped in time) and the trail boot leaves the shaft column 0.15 s (authored) earlier, so the next climber's head never rises into the upper climber's boots. Gate category 15 (crew_vs_crew) checks every pair, every 1/30 s frame of all three clips, exact triangle-triangle, no exemptions."`
- **crew_vs_crew_gate**: `{"result": "PASS", "min_required_m": 0.03, "frames": 1756, "frames_under_min": 0, "pairs": {"Crew_1-Crew_2": {"min_m": 0.047, "frames_under_min": 0, "at_s": 25.7, "parts": ["Foot_R", "Head"], "where_glTF": [4.189, 1.855, -10.735]}, "Crew_1-Crew_3": {"min_m": 0.3712, "frames_under_min": 0, "at_s": 47.733, "parts": ["bbox", "bbox"]}, "Crew_1-Crew_4": {"min_m": 1.5416, "frames_under_min": 0, "at_s": 25.867, "parts": ["bbox", "bbox"]}, "Crew_2-Crew_3": {"min_m": 0.0541, "frames_under_min": 0, "at_s": 29.067, "parts": ["Foot_L", "Head"], "where_glTF": [4.079, 1.858, -10.544]}, "Crew_2-Crew_4": {"min_m": 0.3716, "frames_under_min": 0, "at_s": 50.867, "parts": ["bbox", "bbox"]}, "Crew_3-Crew_4": {"min_m": 0.0667, "frames_under_min": 0, "at_s": 32.5, "parts": ["Foot_R", "Head"], "where_glTF": [4.189, 1.852, -10.735]}}}`
- **climber_spacing_m**: `4.08`
- **landing_vs_pad_3d0d489**: `{"pad_md5": "833a339be22b0db4b8e37eccaa838397", "min_m": 0.044, "hits": 0, "per_part_min_m": {"deck_wing": 0.063, "deck_bridge": 0.1402, "frame_side": 0.0435, "well_frame_climb": 0.0524, "frame_outer": 0.137, "beam_outer": 0.3536, "beam_side": 0.3573, "lid": 0.1214, "brace": 0.5782, "rail_post": 0.1941, "rail": 0.1705, "lid_hinge": 0.1703, "lid_rib": 0.2376, "lid_strut": 0.3446, "hull": 0.2352, "hatch_edge": 0.0801, "cage_tris": 0.033, "kerb_deck": 0.0435}, "plants_in_well": 0, "plants_on_kerb": 0, "climb_min_frame_side_m": 0.052, "cage_min_m": 0.033, "hatch_edge_note": "hatch_edge = the hatch opening edge (was hatch_jamb in v2); v3 keeps every crew vertex >= 3 cm from it"}`
- **aa2_landing_clear_v3_gate**: `{"result": "PASS", "by_category": {"hand_grip_sink_gt_5mm": "PASS", "hand_grip_rod_through_hand": "PASS", "resting_sole_sink_gt_5mm": "PASS", "ladder_rails": "PASS", "ladder_top_rails": "PASS", "rungs": "PASS", "cage": "PASS", "hatch_jamb_lintel": "PASS", "kerb": "PASS", "guard_rail": "PASS", "shins_over_deck": "PASS", "deck_non_resting": "PASS", "hull": "PASS", "other_ship": "PASS"}, "exempt": {"hand_grip_within_5mm": {"entries": 16, "min_m": -0.0038}, "sole_on_deck_within_5mm": {"entries": 8, "min_m": -0.0001}, "sole_on_rung_within_5mm": {"entries": 0, "min_m": null}}, "plants": {"n": 24, "unsupported": 0, "hover_gt_2cm": 4, "sinking": 0}, "per_crew_min_m": {"Crew_1": {"min_m": 0.03, "part": "rung", "bone": "Hand_L", "at_s": 28.833}, "Crew_2": {"min_m": 0.03, "part": "rung", "bone": "Hand_L", "at_s": 43.833}, "Crew_3": {"min_m": 0.03, "part": "rung", "bone": "Hand_R", "at_s": 46.367}, "Crew_4": {"min_m": 0.03, "part": "rung", "bone": "Hand_L", "at_s": 46.1}}, "glb_vertices_left_in_well": 0, "pad": "3d0d489 launch_pad_game.glb"}`
- **aa2_landing_clear_v2_unedited**: `{"minClear": 0, "hits": 0, "per_part": {"brace": {"min_m": 0.772, "hits": 0}, "frame_outer": {"min_m": 0.137, "hits": 0}, "beam_outer": {"min_m": 1.074, "hits": 0}, "frame_side": {"min_m": 0.045, "hits": 0}, "lid": {"min_m": 0.214, "hits": 0}, "deck_wing": {"min_m": 0, "hits": 0}, "rail": {"min_m": 0.17, "hits": 0}, "rail_post": {"min_m": 0.211, "hits": 0}}, "plant_summary": null}`

## Ladder occupancy (who is on the ladder when)

| crew | on ladder | overlaps with |
|---|---|---|
| 1 | 23.09–44.33 | crew 2 (26.5–44.3), crew 3 (29.9–44.3), crew 4 (33.3–44.3) |
| 2 | 26.49–47.73 | crew 1 (26.5–44.3), crew 3 (29.9–47.7), crew 4 (33.3–47.7) |
| 3 | 29.89–51.13 | crew 1 (29.9–44.3), crew 2 (29.9–47.7), crew 4 (33.3–51.1) |
| 4 | 33.29–54.53 | crew 1 (33.3–44.3), crew 2 (33.3–47.7), crew 3 (33.3–51.1) |

All four are on the ladder at once, spaced 4.08 m apart in steady climb (3.4 s stagger). Measured clearance: see *Measured checks*. Each limb moves in its own window, so climbers never move in lockstep.

## Rung timing per crew member

Each row = one limb move: lift-off → contact, target rung index (height of rung). `rail_top` = deck rail grip, `hatch_frame` = hatch frame grips during the mantle, `deck` = foot onto the deck.

<details><summary>Crew 1 — Cargo Manager (76 limb moves, 23.09–44.33 s)</summary>

| lift-off | contact | limb | target | height m |
|---|---|---|---|---|
| 23.24 | 23.69 | hand_R | rung 2 | 1.85 |
| 23.44 | 23.89 | hand_L | rung 1 | 1.25 |
| 23.76 | 24.68 | foot_L | rung 0 | 0.65 |
| 24.21 | 24.83 | hand_L | rung 3 | 2.45 |
| 24.27 | 25.19 | foot_R | rung 1 | 1.25 |
| 24.71 | 25.33 | hand_R | rung 4 | 3.05 |
| 24.77 | 25.69 | foot_L | rung 2 | 1.85 |
| 25.21 | 25.83 | hand_L | rung 5 | 3.65 |
| 25.27 | 26.19 | foot_R | rung 3 | 2.45 |
| 25.71 | 26.33 | hand_R | rung 6 | 4.25 |
| 25.77 | 26.69 | foot_L | rung 4 | 3.05 |
| 26.21 | 26.83 | hand_L | rung 7 | 4.85 |
| 26.27 | 27.19 | foot_R | rung 5 | 3.65 |
| 26.71 | 27.33 | hand_R | rung 8 | 5.45 |
| 26.77 | 27.69 | foot_L | rung 6 | 4.25 |
| 27.21 | 27.83 | hand_L | rung 9 | 6.05 |
| 27.27 | 28.19 | foot_R | rung 7 | 4.85 |
| 27.71 | 28.33 | hand_R | rung 10 | 6.65 |
| 27.77 | 28.69 | foot_L | rung 8 | 5.45 |
| 28.21 | 28.83 | hand_L | rung 11 | 7.25 |
| 28.27 | 29.19 | foot_R | rung 9 | 6.05 |
| 28.71 | 29.33 | hand_R | rung 12 | 7.85 |
| 28.77 | 29.69 | foot_L | rung 10 | 6.65 |
| 29.21 | 29.83 | hand_L | rung 13 | 8.45 |
| 29.27 | 30.19 | foot_R | rung 11 | 7.25 |
| 29.71 | 30.33 | hand_R | rung 14 | 9.05 |
| 29.77 | 30.69 | foot_L | rung 12 | 7.85 |
| 30.21 | 30.83 | hand_L | rung 15 | 9.65 |
| 30.27 | 31.19 | foot_R | rung 13 | 8.45 |
| 30.71 | 31.33 | hand_R | rung 16 | 10.25 |
| 30.77 | 31.69 | foot_L | rung 14 | 9.05 |
| 31.21 | 31.83 | hand_L | rung 17 | 10.85 |
| 31.27 | 32.19 | foot_R | rung 15 | 9.65 |
| 31.71 | 32.33 | hand_R | rung 18 | 11.45 |
| 31.77 | 32.69 | foot_L | rung 16 | 10.25 |
| 32.21 | 32.83 | hand_L | rung 19 | 12.05 |
| 32.27 | 33.19 | foot_R | rung 17 | 10.85 |
| 32.71 | 33.33 | hand_R | rung 20 | 12.65 |
| 32.77 | 33.69 | foot_L | rung 18 | 11.45 |
| 33.21 | 33.83 | hand_L | rung 21 | 13.25 |
| 33.27 | 34.19 | foot_R | rung 19 | 12.05 |
| 33.71 | 34.33 | hand_R | rung 22 | 13.85 |
| 33.77 | 34.69 | foot_L | rung 20 | 12.65 |
| 34.21 | 34.83 | hand_L | rung 23 | 14.45 |
| 34.27 | 35.19 | foot_R | rung 21 | 13.25 |
| 34.71 | 35.33 | hand_R | rung 24 | 15.05 |
| 34.77 | 35.69 | foot_L | rung 22 | 13.85 |
| 35.21 | 35.83 | hand_L | rung 25 | 15.65 |
| 35.27 | 36.19 | foot_R | rung 23 | 14.45 |
| 35.71 | 36.33 | hand_R | rung 26 | 16.25 |
| 35.77 | 36.69 | foot_L | rung 24 | 15.05 |
| 36.21 | 36.83 | hand_L | rung 27 | 16.85 |
| 36.27 | 37.19 | foot_R | rung 25 | 15.65 |
| 36.71 | 37.33 | hand_R | rung 28 | 17.45 |
| 36.77 | 37.69 | foot_L | rung 26 | 16.25 |
| 37.21 | 37.83 | hand_L | rung 29 | 18.05 |
| 37.27 | 38.19 | foot_R | rung 27 | 16.85 |
| 37.71 | 38.33 | hand_R | rung 30 | 18.65 |
| 37.77 | 38.69 | foot_L | rung 28 | 17.45 |
| 38.21 | 38.83 | hand_L | rung 31 | 19.25 |
| 38.27 | 39.19 | foot_R | rung 29 | 18.05 |
| 38.71 | 39.33 | hand_R | rung 32 | 19.85 |
| 38.77 | 39.69 | foot_L | rung 30 | 18.65 |
| 39.21 | 39.83 | hand_L | rung 33 | 20.45 |
| 39.27 | 40.19 | foot_R | rung 31 | 19.25 |
| 39.71 | 40.33 | hand_R | rung 34 | 21.05 |
| 39.78 | 40.70 | foot_L | rung 32 | 19.85 |
| 39.97 | 40.47 | hand_L | rung 34 | 21.05 |
| 41.33 | 41.57 | hand_L | rail_z_21.30 |  |
| 41.51 | 41.75 | hand_R | rail_z_21.30 |  |
| 41.78 | 41.99 | hand_L | rail_z_21.55 |  |
| 41.99 | 42.20 | hand_R | rail_z_21.65 |  |
| 42.20 | 42.41 | hand_L | rail_z_21.79 |  |
| 42.41 | 42.62 | hand_R | rail_z_21.79 |  |
| 43.22 | 43.46 | hand_R | release |  |
| 43.31 | 43.55 | hand_L | release |  |

</details>

<details><summary>Crew 2 — Crew 2 (76 limb moves, 26.49–47.73 s)</summary>

| lift-off | contact | limb | target | height m |
|---|---|---|---|---|
| 26.64 | 27.09 | hand_R | rung 2 | 1.85 |
| 26.84 | 27.29 | hand_L | rung 1 | 1.25 |
| 27.16 | 28.08 | foot_L | rung 0 | 0.65 |
| 27.61 | 28.23 | hand_L | rung 3 | 2.45 |
| 27.67 | 28.59 | foot_R | rung 1 | 1.25 |
| 28.11 | 28.73 | hand_R | rung 4 | 3.05 |
| 28.17 | 29.09 | foot_L | rung 2 | 1.85 |
| 28.61 | 29.23 | hand_L | rung 5 | 3.65 |
| 28.67 | 29.59 | foot_R | rung 3 | 2.45 |
| 29.11 | 29.73 | hand_R | rung 6 | 4.25 |
| 29.17 | 30.09 | foot_L | rung 4 | 3.05 |
| 29.61 | 30.23 | hand_L | rung 7 | 4.85 |
| 29.67 | 30.59 | foot_R | rung 5 | 3.65 |
| 30.11 | 30.73 | hand_R | rung 8 | 5.45 |
| 30.17 | 31.09 | foot_L | rung 6 | 4.25 |
| 30.61 | 31.23 | hand_L | rung 9 | 6.05 |
| 30.67 | 31.59 | foot_R | rung 7 | 4.85 |
| 31.11 | 31.73 | hand_R | rung 10 | 6.65 |
| 31.17 | 32.09 | foot_L | rung 8 | 5.45 |
| 31.61 | 32.23 | hand_L | rung 11 | 7.25 |
| 31.67 | 32.59 | foot_R | rung 9 | 6.05 |
| 32.11 | 32.73 | hand_R | rung 12 | 7.85 |
| 32.17 | 33.09 | foot_L | rung 10 | 6.65 |
| 32.61 | 33.23 | hand_L | rung 13 | 8.45 |
| 32.67 | 33.59 | foot_R | rung 11 | 7.25 |
| 33.11 | 33.73 | hand_R | rung 14 | 9.05 |
| 33.17 | 34.09 | foot_L | rung 12 | 7.85 |
| 33.61 | 34.23 | hand_L | rung 15 | 9.65 |
| 33.67 | 34.59 | foot_R | rung 13 | 8.45 |
| 34.11 | 34.73 | hand_R | rung 16 | 10.25 |
| 34.17 | 35.09 | foot_L | rung 14 | 9.05 |
| 34.61 | 35.23 | hand_L | rung 17 | 10.85 |
| 34.67 | 35.59 | foot_R | rung 15 | 9.65 |
| 35.11 | 35.73 | hand_R | rung 18 | 11.45 |
| 35.17 | 36.09 | foot_L | rung 16 | 10.25 |
| 35.61 | 36.23 | hand_L | rung 19 | 12.05 |
| 35.67 | 36.59 | foot_R | rung 17 | 10.85 |
| 36.11 | 36.73 | hand_R | rung 20 | 12.65 |
| 36.17 | 37.09 | foot_L | rung 18 | 11.45 |
| 36.61 | 37.23 | hand_L | rung 21 | 13.25 |
| 36.67 | 37.59 | foot_R | rung 19 | 12.05 |
| 37.11 | 37.73 | hand_R | rung 22 | 13.85 |
| 37.17 | 38.09 | foot_L | rung 20 | 12.65 |
| 37.61 | 38.23 | hand_L | rung 23 | 14.45 |
| 37.67 | 38.59 | foot_R | rung 21 | 13.25 |
| 38.11 | 38.73 | hand_R | rung 24 | 15.05 |
| 38.17 | 39.09 | foot_L | rung 22 | 13.85 |
| 38.61 | 39.23 | hand_L | rung 25 | 15.65 |
| 38.67 | 39.59 | foot_R | rung 23 | 14.45 |
| 39.11 | 39.73 | hand_R | rung 26 | 16.25 |
| 39.17 | 40.09 | foot_L | rung 24 | 15.05 |
| 39.61 | 40.23 | hand_L | rung 27 | 16.85 |
| 39.67 | 40.59 | foot_R | rung 25 | 15.65 |
| 40.11 | 40.73 | hand_R | rung 28 | 17.45 |
| 40.17 | 41.09 | foot_L | rung 26 | 16.25 |
| 40.61 | 41.23 | hand_L | rung 29 | 18.05 |
| 40.67 | 41.59 | foot_R | rung 27 | 16.85 |
| 41.11 | 41.73 | hand_R | rung 30 | 18.65 |
| 41.17 | 42.09 | foot_L | rung 28 | 17.45 |
| 41.61 | 42.23 | hand_L | rung 31 | 19.25 |
| 41.67 | 42.59 | foot_R | rung 29 | 18.05 |
| 42.11 | 42.73 | hand_R | rung 32 | 19.85 |
| 42.17 | 43.09 | foot_L | rung 30 | 18.65 |
| 42.61 | 43.23 | hand_L | rung 33 | 20.45 |
| 42.67 | 43.59 | foot_R | rung 31 | 19.25 |
| 43.11 | 43.73 | hand_R | rung 34 | 21.05 |
| 43.18 | 44.10 | foot_L | rung 32 | 19.85 |
| 43.37 | 43.87 | hand_L | rung 34 | 21.05 |
| 44.73 | 44.97 | hand_L | rail_z_21.30 |  |
| 44.91 | 45.15 | hand_R | rail_z_21.30 |  |
| 45.18 | 45.39 | hand_L | rail_z_21.55 |  |
| 45.39 | 45.60 | hand_R | rail_z_21.65 |  |
| 45.60 | 45.81 | hand_L | rail_z_21.79 |  |
| 45.81 | 46.02 | hand_R | rail_z_21.79 |  |
| 46.62 | 46.86 | hand_L | release |  |
| 46.71 | 46.95 | hand_R | release |  |

</details>

<details><summary>Crew 3 — Crew 3 (76 limb moves, 29.89–51.13 s)</summary>

| lift-off | contact | limb | target | height m |
|---|---|---|---|---|
| 30.04 | 30.49 | hand_R | rung 2 | 1.85 |
| 30.24 | 30.69 | hand_L | rung 1 | 1.25 |
| 30.56 | 31.48 | foot_L | rung 0 | 0.65 |
| 31.01 | 31.63 | hand_L | rung 3 | 2.45 |
| 31.07 | 31.99 | foot_R | rung 1 | 1.25 |
| 31.51 | 32.13 | hand_R | rung 4 | 3.05 |
| 31.57 | 32.49 | foot_L | rung 2 | 1.85 |
| 32.01 | 32.63 | hand_L | rung 5 | 3.65 |
| 32.07 | 32.99 | foot_R | rung 3 | 2.45 |
| 32.51 | 33.13 | hand_R | rung 6 | 4.25 |
| 32.57 | 33.49 | foot_L | rung 4 | 3.05 |
| 33.01 | 33.63 | hand_L | rung 7 | 4.85 |
| 33.07 | 33.99 | foot_R | rung 5 | 3.65 |
| 33.51 | 34.13 | hand_R | rung 8 | 5.45 |
| 33.57 | 34.49 | foot_L | rung 6 | 4.25 |
| 34.01 | 34.63 | hand_L | rung 9 | 6.05 |
| 34.07 | 34.99 | foot_R | rung 7 | 4.85 |
| 34.51 | 35.13 | hand_R | rung 10 | 6.65 |
| 34.57 | 35.49 | foot_L | rung 8 | 5.45 |
| 35.01 | 35.63 | hand_L | rung 11 | 7.25 |
| 35.07 | 35.99 | foot_R | rung 9 | 6.05 |
| 35.51 | 36.13 | hand_R | rung 12 | 7.85 |
| 35.57 | 36.49 | foot_L | rung 10 | 6.65 |
| 36.01 | 36.63 | hand_L | rung 13 | 8.45 |
| 36.07 | 36.99 | foot_R | rung 11 | 7.25 |
| 36.51 | 37.13 | hand_R | rung 14 | 9.05 |
| 36.57 | 37.49 | foot_L | rung 12 | 7.85 |
| 37.01 | 37.63 | hand_L | rung 15 | 9.65 |
| 37.07 | 37.99 | foot_R | rung 13 | 8.45 |
| 37.51 | 38.13 | hand_R | rung 16 | 10.25 |
| 37.57 | 38.49 | foot_L | rung 14 | 9.05 |
| 38.01 | 38.63 | hand_L | rung 17 | 10.85 |
| 38.07 | 38.99 | foot_R | rung 15 | 9.65 |
| 38.51 | 39.13 | hand_R | rung 18 | 11.45 |
| 38.57 | 39.49 | foot_L | rung 16 | 10.25 |
| 39.01 | 39.63 | hand_L | rung 19 | 12.05 |
| 39.07 | 39.99 | foot_R | rung 17 | 10.85 |
| 39.51 | 40.13 | hand_R | rung 20 | 12.65 |
| 39.57 | 40.49 | foot_L | rung 18 | 11.45 |
| 40.01 | 40.63 | hand_L | rung 21 | 13.25 |
| 40.07 | 40.99 | foot_R | rung 19 | 12.05 |
| 40.51 | 41.13 | hand_R | rung 22 | 13.85 |
| 40.57 | 41.49 | foot_L | rung 20 | 12.65 |
| 41.01 | 41.63 | hand_L | rung 23 | 14.45 |
| 41.07 | 41.99 | foot_R | rung 21 | 13.25 |
| 41.51 | 42.13 | hand_R | rung 24 | 15.05 |
| 41.57 | 42.49 | foot_L | rung 22 | 13.85 |
| 42.01 | 42.63 | hand_L | rung 25 | 15.65 |
| 42.07 | 42.99 | foot_R | rung 23 | 14.45 |
| 42.51 | 43.13 | hand_R | rung 26 | 16.25 |
| 42.57 | 43.49 | foot_L | rung 24 | 15.05 |
| 43.01 | 43.63 | hand_L | rung 27 | 16.85 |
| 43.07 | 43.99 | foot_R | rung 25 | 15.65 |
| 43.51 | 44.13 | hand_R | rung 28 | 17.45 |
| 43.57 | 44.49 | foot_L | rung 26 | 16.25 |
| 44.01 | 44.63 | hand_L | rung 29 | 18.05 |
| 44.07 | 44.99 | foot_R | rung 27 | 16.85 |
| 44.51 | 45.13 | hand_R | rung 30 | 18.65 |
| 44.57 | 45.49 | foot_L | rung 28 | 17.45 |
| 45.01 | 45.63 | hand_L | rung 31 | 19.25 |
| 45.07 | 45.99 | foot_R | rung 29 | 18.05 |
| 45.51 | 46.13 | hand_R | rung 32 | 19.85 |
| 45.57 | 46.49 | foot_L | rung 30 | 18.65 |
| 46.01 | 46.63 | hand_L | rung 33 | 20.45 |
| 46.07 | 46.99 | foot_R | rung 31 | 19.25 |
| 46.51 | 47.13 | hand_R | rung 34 | 21.05 |
| 46.58 | 47.50 | foot_L | rung 32 | 19.85 |
| 46.77 | 47.27 | hand_L | rung 34 | 21.05 |
| 48.13 | 48.37 | hand_L | rail_z_21.30 |  |
| 48.31 | 48.55 | hand_R | rail_z_21.30 |  |
| 48.58 | 48.79 | hand_L | rail_z_21.55 |  |
| 48.79 | 49.00 | hand_R | rail_z_21.65 |  |
| 49.00 | 49.21 | hand_L | rail_z_21.79 |  |
| 49.21 | 49.42 | hand_R | rail_z_21.79 |  |
| 50.02 | 50.26 | hand_R | release |  |
| 50.11 | 50.35 | hand_L | release |  |

</details>

<details><summary>Crew 4 — Crew 4 (76 limb moves, 33.29–54.53 s)</summary>

| lift-off | contact | limb | target | height m |
|---|---|---|---|---|
| 33.44 | 33.89 | hand_R | rung 2 | 1.85 |
| 33.64 | 34.09 | hand_L | rung 1 | 1.25 |
| 33.96 | 34.88 | foot_L | rung 0 | 0.65 |
| 34.41 | 35.03 | hand_L | rung 3 | 2.45 |
| 34.47 | 35.39 | foot_R | rung 1 | 1.25 |
| 34.91 | 35.53 | hand_R | rung 4 | 3.05 |
| 34.97 | 35.89 | foot_L | rung 2 | 1.85 |
| 35.41 | 36.03 | hand_L | rung 5 | 3.65 |
| 35.47 | 36.39 | foot_R | rung 3 | 2.45 |
| 35.91 | 36.53 | hand_R | rung 6 | 4.25 |
| 35.97 | 36.89 | foot_L | rung 4 | 3.05 |
| 36.41 | 37.03 | hand_L | rung 7 | 4.85 |
| 36.47 | 37.39 | foot_R | rung 5 | 3.65 |
| 36.91 | 37.53 | hand_R | rung 8 | 5.45 |
| 36.97 | 37.89 | foot_L | rung 6 | 4.25 |
| 37.41 | 38.03 | hand_L | rung 9 | 6.05 |
| 37.47 | 38.39 | foot_R | rung 7 | 4.85 |
| 37.91 | 38.53 | hand_R | rung 10 | 6.65 |
| 37.97 | 38.89 | foot_L | rung 8 | 5.45 |
| 38.41 | 39.03 | hand_L | rung 11 | 7.25 |
| 38.47 | 39.39 | foot_R | rung 9 | 6.05 |
| 38.91 | 39.53 | hand_R | rung 12 | 7.85 |
| 38.97 | 39.89 | foot_L | rung 10 | 6.65 |
| 39.41 | 40.03 | hand_L | rung 13 | 8.45 |
| 39.47 | 40.39 | foot_R | rung 11 | 7.25 |
| 39.91 | 40.53 | hand_R | rung 14 | 9.05 |
| 39.97 | 40.89 | foot_L | rung 12 | 7.85 |
| 40.41 | 41.03 | hand_L | rung 15 | 9.65 |
| 40.47 | 41.39 | foot_R | rung 13 | 8.45 |
| 40.91 | 41.53 | hand_R | rung 16 | 10.25 |
| 40.97 | 41.89 | foot_L | rung 14 | 9.05 |
| 41.41 | 42.03 | hand_L | rung 17 | 10.85 |
| 41.47 | 42.39 | foot_R | rung 15 | 9.65 |
| 41.91 | 42.53 | hand_R | rung 18 | 11.45 |
| 41.97 | 42.89 | foot_L | rung 16 | 10.25 |
| 42.41 | 43.03 | hand_L | rung 19 | 12.05 |
| 42.47 | 43.39 | foot_R | rung 17 | 10.85 |
| 42.91 | 43.53 | hand_R | rung 20 | 12.65 |
| 42.97 | 43.89 | foot_L | rung 18 | 11.45 |
| 43.41 | 44.03 | hand_L | rung 21 | 13.25 |
| 43.47 | 44.39 | foot_R | rung 19 | 12.05 |
| 43.91 | 44.53 | hand_R | rung 22 | 13.85 |
| 43.97 | 44.89 | foot_L | rung 20 | 12.65 |
| 44.41 | 45.03 | hand_L | rung 23 | 14.45 |
| 44.47 | 45.39 | foot_R | rung 21 | 13.25 |
| 44.91 | 45.53 | hand_R | rung 24 | 15.05 |
| 44.97 | 45.89 | foot_L | rung 22 | 13.85 |
| 45.41 | 46.03 | hand_L | rung 25 | 15.65 |
| 45.47 | 46.39 | foot_R | rung 23 | 14.45 |
| 45.91 | 46.53 | hand_R | rung 26 | 16.25 |
| 45.97 | 46.89 | foot_L | rung 24 | 15.05 |
| 46.41 | 47.03 | hand_L | rung 27 | 16.85 |
| 46.47 | 47.39 | foot_R | rung 25 | 15.65 |
| 46.91 | 47.53 | hand_R | rung 28 | 17.45 |
| 46.97 | 47.89 | foot_L | rung 26 | 16.25 |
| 47.41 | 48.03 | hand_L | rung 29 | 18.05 |
| 47.47 | 48.39 | foot_R | rung 27 | 16.85 |
| 47.91 | 48.53 | hand_R | rung 30 | 18.65 |
| 47.97 | 48.89 | foot_L | rung 28 | 17.45 |
| 48.41 | 49.03 | hand_L | rung 31 | 19.25 |
| 48.47 | 49.39 | foot_R | rung 29 | 18.05 |
| 48.91 | 49.53 | hand_R | rung 32 | 19.85 |
| 48.97 | 49.89 | foot_L | rung 30 | 18.65 |
| 49.41 | 50.03 | hand_L | rung 33 | 20.45 |
| 49.47 | 50.39 | foot_R | rung 31 | 19.25 |
| 49.91 | 50.53 | hand_R | rung 34 | 21.05 |
| 49.98 | 50.90 | foot_L | rung 32 | 19.85 |
| 50.17 | 50.67 | hand_L | rung 34 | 21.05 |
| 51.53 | 51.77 | hand_L | rail_z_21.30 |  |
| 51.71 | 51.95 | hand_R | rail_z_21.30 |  |
| 51.98 | 52.19 | hand_L | rail_z_21.55 |  |
| 52.19 | 52.40 | hand_R | rail_z_21.65 |  |
| 52.40 | 52.61 | hand_L | rail_z_21.79 |  |
| 52.61 | 52.82 | hand_R | rail_z_21.79 |  |
| 53.42 | 53.66 | hand_L | release |  |
| 53.51 | 53.75 | hand_R | release |  |

</details>

## Build checks

- `ik_max_stretch`: 1.0501
- `ik_stretch_at`: {'crew': 3, 't': 50.1, 'limb': 'armR', 'A': [4.14, 22.33, -10.9], 'T': [4.04, 21.76, -10.84]}
- `ik_evals_over_1.02`: 720
- `planted_foot_slide_at`: {'crew': 4, 'foot': 'R', 't': 26.7}
- `planted_foot_slide_max_m`: 0.00335
- `max_joint_step_per_frame_m`: 0.827
- `min_gap_upper_boots_to_lower_gloves_m`: -1.714
- `min_gap_at`: [54.53, 3, 4]
