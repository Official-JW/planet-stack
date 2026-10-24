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

## Board_Focus (empty node in the GLB, child of CrewBoarding)

- world position (glTF, Y up): **[3.854, 3.017, -10.775]**; mid-ladder point [3.854, 11.05, -10.775]
- orientation: 38 deg vertical FOV, 18 deg look-down, game yaw; camera = focus + d*(0, sin18, cos18) (glTF)
- distance_m (use 109.7): `109.63`
- ease: 1.2 s ease to Board_Focus, then hold
- 375x667 (a) whole ladder + 4 climbers: `{"focus": [3.854, 3.017, -10.775], "distance_m": 109.63, "crew_px_at_mid_ladder": 16.1, "spare_top_px": 5.0, "spare_bottom_px": 5.0, "x_px": [176.1, 214.8], "focus_below_mid_ladder_m": 8.03}`
- 375x667 requested 40 px crew: `{"distance_m": 42.47, "ladder_px_tall": 474.9, "band_px": 229, "conflict": true}`
- 375x667 (b) 40 px tracking: `{"distance_m": 42.47, "max_group_spread_px": 329.2, "at_s": 40.87, "fits_band": false}`
- 375x667 aimed at mid-ladder instead: `{"y_px": [222.7, 446.7], "spare_top_px": 78.7, "spare_bottom_px": -63.7}`
- 375x667 (c) busy top only: `{"c_busy_z>=8": {"focus": [3.854, 11.096, -10.775], "distance_m": 66.8, "crew_px": 25.5, "spare_top_px": 5.0, "spare_bottom_px": 5.0}, "c_busy_z>=11": {"focus": [3.854, 13.472, -10.775], "distance_m": 54.2, "crew_px": 31.8, "spare_top_px": 5.0, "spare_bottom_px": 5.0}, "c_busy_z>=14": {"focus": [3.854, 15.861, -10.775], "distance_m": 41.54, "crew_px": 42.3, "spare_top_px": 5.0, "spare_bottom_px": 5.0}}`
- 393x852 same camera (vFOV-locked, so the image scales by 852/667): `{"content_y_px": [190.3, 482.8], "band_scaled_y_px": [183.9, 489.2], "crew_px": 20.6}`
- 393x852 own best fit (band 184-490, 6 px spare): `{"focus": [3.854, 3.093, -10.775], "distance_m": 109.09, "crew_px_at_mid_ladder": 20.7, "spare_top_px": 6.0, "spare_bottom_px": 6.0, "x_px": [181.8, 231.5], "focus_below_mid_ladder_m": 7.96}`

## Phases per crew member

| crew | role | call | walk start | at ladder / queue spot | mount (first reach) | climb start | climb top | on deck (mantle done) | inside hatch (hidden) | ladder time |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Cargo Manager | 0.00–3.00 | 3.75 | 22.29 | 23.09 | 23.99 | 41.62 | 44.59 | 47.79 | 21.50 |
| 2 | Crew 2 | 0.00–3.00 | 3.65 | 24.18 | 26.49 | 27.39 | 45.02 | 47.99 | 51.19 | 21.50 |
| 3 | Crew 3 | 0.00–3.00 | 5.20 | 24.59 | 29.89 | 30.79 | 48.42 | 51.39 | 54.59 | 21.50 |
| 4 | Crew 4 | 0.00–3.00 | 7.50 | 26.92 | 33.29 | 34.19 | 51.82 | 54.79 | 57.99 | 21.50 |

Phase notes: *call* = Cargo Manager (crew 1) hand to helmet radio 0.2–2.95 s and points to the pad 1.35–3.1 s; crew 2–4 raise a hand to acknowledge. *walk* = planted-foot gait along the shared route around the ship-leg pad; crew 2–4 wait at queue spots by the ladder and step to the ladder foot before their mount (mounts are chained: each is at least one stagger after the previous). *climb* = diagonal pairs (right hand + left foot on even rungs, left hand + right foot on odd rungs), hands swing in 0.42 of the cycle, feet 0.45. *mantle* = see the hatch landing section.

## Hatch landing: mantle + walk-in per climber (Art Assistant 2 option 1 landing)

Open well u 4.05–5.15, |t| < 0.62 (no deck in front of the hatch); kerb |t| 0.62–0.68 (top z 21.88); wing stand area u 4.3–4.7, |t| 0.75–1.25, deck top z 21.85. Each climber pulls the lead foot back off its rung, lifts it inside the cage and high-steps sideways over the kerb onto the wing, the trail foot follows, then they step toward the hull, cross the outer foot behind over the kerb and through the hatch.

| crew | step-off side | through-hole start (climb top) | through-hole end (both boots on the wing) | hands off | walk-in end (inside hatch, hidden) |
|---|---|---|---|---|---|
| 1 | +t (lead Foot_R) | 41.62 | 44.05 | 44.59 | 47.79 |
| 2 | -t (lead Foot_L) | 45.02 | 47.45 | 47.99 | 51.19 |
| 3 | +t (lead Foot_R) | 48.42 | 50.85 | 51.39 | 54.59 |
| 4 | -t (lead Foot_L) | 51.82 | 54.25 | 54.79 | 57.99 |

Foot plants at deck height (sole centre u, t, z; land time = contact). `mantle` = step-off onto the wing, `walk_in` = steps to the hatch (the last plants are inside the hatch, u < 3.9).

<details><summary>Crew 1 plants</summary>

| land s | foot | target u | target t | z | phase | measured sole box u | measured sole box t | where |
|---|---|---|---|---|---|---|---|---|
| 43.29 | Foot_R | 4.530 | 1.020 | 21.855 | mantle | 4.315–4.624 | 0.953–1.084 | wing_stand_area |
| 44.05 | Foot_L | 4.530 | 0.820 | 21.855 | mantle | 4.313–4.622 | 0.754–0.884 | wing_stand_area |
| 45.09 | Foot_L | 4.150 | 0.870 | 21.855 | walk_in | 3.927–4.256 | 0.724–0.965 | wing |
| 45.54 | Foot_R | 4.230 | 1.100 | 21.855 | walk_in | 4.007–4.336 | 0.954–1.196 | wing |
| 46.34 | Foot_R | 3.800 | 0.240 | 21.855 | walk_in | 3.594–3.906 | 0.065–0.347 | inside_hatch |
| 46.94 | Foot_L | 3.580 | 0.080 | 21.855 | walk_in | 3.363–3.672 | 0.013–0.143 | inside_hatch |
| 47.69 | Foot_R | 3.300 | -0.020 | 21.855 | walk_in | 3.083–3.392 | -0.087–0.044 | inside_hatch |

</details>

<details><summary>Crew 2 plants</summary>

| land s | foot | target u | target t | z | phase | measured sole box u | measured sole box t | where |
|---|---|---|---|---|---|---|---|---|
| 46.69 | Foot_L | 4.530 | -1.020 | 21.855 | mantle | 4.313–4.622 | -1.088–-0.957 | wing_stand_area |
| 47.45 | Foot_R | 4.530 | -0.820 | 21.855 | mantle | 4.314–4.622 | -0.888–-0.757 | wing_stand_area |
| 48.49 | Foot_R | 4.150 | -0.870 | 21.855 | walk_in | 3.945–4.257 | -0.961–-0.716 | wing |
| 48.94 | Foot_L | 4.230 | -1.100 | 21.855 | walk_in | 4.019–4.338 | -1.191–-0.947 | wing |
| 49.74 | Foot_L | 3.800 | -0.240 | 21.855 | walk_in | 3.610–3.909 | -0.344–-0.052 | inside_hatch |
| 50.34 | Foot_R | 3.580 | -0.080 | 21.855 | walk_in | 3.363–3.672 | -0.147–-0.017 | inside_hatch |
| 51.09 | Foot_L | 3.300 | 0.020 | 21.855 | walk_in | 3.083–3.392 | -0.047–0.083 | inside_hatch |

</details>

<details><summary>Crew 3 plants</summary>

| land s | foot | target u | target t | z | phase | measured sole box u | measured sole box t | where |
|---|---|---|---|---|---|---|---|---|
| 50.09 | Foot_R | 4.530 | 1.020 | 21.855 | mantle | 4.315–4.624 | 0.953–1.084 | wing_stand_area |
| 50.85 | Foot_L | 4.530 | 0.820 | 21.855 | mantle | 4.313–4.622 | 0.754–0.884 | wing_stand_area |
| 51.89 | Foot_L | 4.150 | 0.870 | 21.855 | walk_in | 3.927–4.256 | 0.724–0.965 | wing |
| 52.34 | Foot_R | 4.230 | 1.100 | 21.855 | walk_in | 4.007–4.336 | 0.954–1.196 | wing |
| 53.14 | Foot_R | 3.800 | 0.240 | 21.855 | walk_in | 3.594–3.906 | 0.065–0.347 | inside_hatch |
| 53.74 | Foot_L | 3.580 | 0.080 | 21.855 | walk_in | 3.363–3.672 | 0.013–0.143 | inside_hatch |
| 54.49 | Foot_R | 3.300 | -0.020 | 21.855 | walk_in | 3.083–3.392 | -0.087–0.044 | inside_hatch |

</details>

<details><summary>Crew 4 plants</summary>

| land s | foot | target u | target t | z | phase | measured sole box u | measured sole box t | where |
|---|---|---|---|---|---|---|---|---|
| 53.49 | Foot_L | 4.530 | -1.020 | 21.855 | mantle | 4.313–4.622 | -1.088–-0.957 | wing_stand_area |
| 54.25 | Foot_R | 4.530 | -0.820 | 21.855 | mantle | 4.314–4.622 | -0.888–-0.757 | wing_stand_area |
| 55.29 | Foot_R | 4.150 | -0.870 | 21.855 | walk_in | 3.945–4.257 | -0.961–-0.716 | wing |
| 55.74 | Foot_L | 4.230 | -1.100 | 21.855 | walk_in | 4.019–4.338 | -1.191–-0.947 | wing |
| 56.54 | Foot_L | 3.800 | -0.240 | 21.855 | walk_in | 3.610–3.909 | -0.344–-0.052 | inside_hatch |
| 57.14 | Foot_R | 3.580 | -0.080 | 21.855 | walk_in | 3.363–3.672 | -0.147–-0.017 | inside_hatch |
| 57.89 | Foot_L | 3.300 | 0.020 | 21.855 | walk_in | 3.083–3.392 | -0.047–0.083 | inside_hatch |

</details>

## Measured checks (three r186 skinned playback of the shipped GLB)

- **glb**: `{"bytes": 229132, "draws": 4, "tris": 12196, "three": "186", "clips": [["crew_call", 3], ["crew_walk_to_pad", 19.3], ["crew_climb", 36.2]]}`
- **contacts_r186**: `{"foot_max_err_vs_ref_m": 0.0325, "hand_max_err_vs_ref_m": 0.0757, "planted_foot_slide_max_m": 0.0205, "gripping_hand_slip_max_m": 0.0138}`
- **planted_foot_slide_percentiles_m**: `{"p50": 0.0013, "p95": 0.0068, "p99": 0.012, "max": 0.0205, "n_frames": 6651, "over_5mm": 936}`
- **worst_at**: `{"foot_max_err_vs_ref_m": {"t": 3.7, "crew": 1, "limb": "Foot_L"}, "hand_max_err_vs_ref_m": {"t": 51.2, "crew": 2, "limb": "Hand_R"}, "planted_foot_slide_max_m": {"t": 8.33, "crew": 3, "limb": "Foot_R"}, "gripping_hand_slip_max_m": {"t": 51.1, "crew": 4, "limb": "Hand_R"}}`
- **ik_target_reach**: `{"max_ratio": 1.0885, "at": {"crew": 1, "t": 46.333, "limb": "legL", "A": [3.72, 22.6, -11.11], "T": [4.03, 21.94, -11.68]}, "note": "IK target distance / limb length; limbs are rigid (never stretched), >1 = the target is missed by that fraction for a frame"}`
- **climber_clearance**: `{"frames": 1087, "t_range": [22.3, 58.4996], "min_mesh_gap_m": 0.069, "min_mesh_gap_at_t_crewA_crewB": [29.1666, 2, 3], "min_boot_to_glove_m": 0.254, "min_boot_to_glove_at_t_upper_lower": [49.5664, 2, 3], "frames_under_10cm": 13, "frames_touching_under_2cm": 0}`
- **climber_spacing_m**: `4.08`
- **landing_vs_wip_pad**: `{"pad_md5": "9e44959341d7f57bf1b3bd21b826b940", "min_m": 0.0, "hits": 0, "per_part_min_m": {"deck_wing": 0.007, "deck_bridge": 0.065, "frame_side": 0.013, "frame_outer": 0.065, "beam_outer": 0.295, "beam_side": 0.172, "lid": 0.144, "brace": 0.642, "rail_post": 0.111, "rail": 0.016, "lid_hinge": 0.132, "lid_rib": 0.258, "lid_strut": 0.436, "hull": 0.007, "hatch_jamb": 0.0}, "plants_in_well": 0, "plants_on_kerb": 0, "climb_min_frame_side_m": 0.188, "v1_c2d33fc_climb_frame_side_m": 0.048, "cage_min_m": 0.011, "hatch_jamb_note": "0.000 = gloves resting on the hatch jamb edge (|t| = 0.652) while stepping off: contact, no penetration"}`
- **aa2_landing_clear_mjs**: `{"minClear": 0.004, "hits": 0, "per_part": {"brace": {"min_m": 0.678, "hits": 0}, "frame_outer": {"min_m": 0.065, "hits": 0}, "beam_outer": {"min_m": 0.903, "hits": 0}, "frame_side": {"min_m": 0.013, "hits": 0}, "lid": {"min_m": 0.276, "hits": 0}, "deck_wing": {"min_m": 0.004, "hits": 0}, "rail_post": {"min_m": 0.15, "hits": 0}, "rail": {"min_m": 0.017, "hits": 0}}, "note": "its climb/after-mantle split uses v1 STAND times (hardcoded), so only min/part/hits apply to v2"}`

## Ladder occupancy (who is on the ladder when)

| crew | on ladder | overlaps with |
|---|---|---|
| 1 | 23.09–44.59 | crew 2 (26.5–44.6), crew 3 (29.9–44.6), crew 4 (33.3–44.6) |
| 2 | 26.49–47.99 | crew 1 (26.5–44.6), crew 3 (29.9–48.0), crew 4 (33.3–48.0) |
| 3 | 29.89–51.39 | crew 1 (29.9–44.6), crew 2 (29.9–48.0), crew 4 (33.3–51.4) |
| 4 | 33.29–54.79 | crew 1 (33.3–44.6), crew 2 (33.3–48.0), crew 3 (33.3–51.4) |

All four are on the ladder at once, spaced 4.08 m apart in steady climb (3.4 s stagger). Measured clearance: see *Measured checks*. Each limb moves in its own window, so climbers never move in lockstep.

## Rung timing per crew member

Each row = one limb move: lift-off → contact, target rung index (height of rung). `rail_top` = deck rail grip, `hatch_frame` = hatch frame grips during the mantle, `deck` = foot onto the deck.

<details><summary>Crew 1 — Cargo Manager (72 limb moves, 23.09–44.59 s)</summary>

| lift-off | contact | limb | target | height m |
|---|---|---|---|---|
| 23.24 | 23.69 | hand_R | rung 2 | 1.85 |
| 23.44 | 23.89 | hand_L | rung 1 | 1.25 |
| 23.64 | 24.09 | foot_L | rung 0 | 0.65 |
| 24.20 | 24.65 | foot_R | rung 1 | 1.25 |
| 24.22 | 24.64 | hand_L | rung 3 | 2.45 |
| 24.71 | 25.16 | foot_L | rung 2 | 1.85 |
| 24.74 | 25.16 | hand_R | rung 4 | 3.05 |
| 25.21 | 25.66 | foot_R | rung 3 | 2.45 |
| 25.24 | 25.66 | hand_L | rung 5 | 3.65 |
| 25.71 | 26.16 | foot_L | rung 4 | 3.05 |
| 25.74 | 26.16 | hand_R | rung 6 | 4.25 |
| 26.21 | 26.66 | foot_R | rung 5 | 3.65 |
| 26.24 | 26.66 | hand_L | rung 7 | 4.85 |
| 26.71 | 27.16 | foot_L | rung 6 | 4.25 |
| 26.74 | 27.16 | hand_R | rung 8 | 5.45 |
| 27.21 | 27.66 | foot_R | rung 7 | 4.85 |
| 27.24 | 27.66 | hand_L | rung 9 | 6.05 |
| 27.71 | 28.16 | foot_L | rung 8 | 5.45 |
| 27.74 | 28.16 | hand_R | rung 10 | 6.65 |
| 28.21 | 28.66 | foot_R | rung 9 | 6.05 |
| 28.24 | 28.66 | hand_L | rung 11 | 7.25 |
| 28.71 | 29.16 | foot_L | rung 10 | 6.65 |
| 28.74 | 29.16 | hand_R | rung 12 | 7.85 |
| 29.21 | 29.66 | foot_R | rung 11 | 7.25 |
| 29.24 | 29.66 | hand_L | rung 13 | 8.45 |
| 29.71 | 30.16 | foot_L | rung 12 | 7.85 |
| 29.74 | 30.16 | hand_R | rung 14 | 9.05 |
| 30.21 | 30.66 | foot_R | rung 13 | 8.45 |
| 30.24 | 30.66 | hand_L | rung 15 | 9.65 |
| 30.71 | 31.16 | foot_L | rung 14 | 9.05 |
| 30.74 | 31.16 | hand_R | rung 16 | 10.25 |
| 31.21 | 31.66 | foot_R | rung 15 | 9.65 |
| 31.24 | 31.66 | hand_L | rung 17 | 10.85 |
| 31.71 | 32.16 | foot_L | rung 16 | 10.25 |
| 31.74 | 32.16 | hand_R | rung 18 | 11.45 |
| 32.21 | 32.66 | foot_R | rung 17 | 10.85 |
| 32.24 | 32.66 | hand_L | rung 19 | 12.05 |
| 32.71 | 33.16 | foot_L | rung 18 | 11.45 |
| 32.74 | 33.16 | hand_R | rung 20 | 12.65 |
| 33.21 | 33.66 | foot_R | rung 19 | 12.05 |
| 33.24 | 33.66 | hand_L | rung 21 | 13.25 |
| 33.71 | 34.16 | foot_L | rung 20 | 12.65 |
| 33.74 | 34.16 | hand_R | rung 22 | 13.85 |
| 34.21 | 34.66 | foot_R | rung 21 | 13.25 |
| 34.24 | 34.66 | hand_L | rung 23 | 14.45 |
| 34.71 | 35.16 | foot_L | rung 22 | 13.85 |
| 34.74 | 35.16 | hand_R | rung 24 | 15.05 |
| 35.21 | 35.66 | foot_R | rung 23 | 14.45 |
| 35.24 | 35.66 | hand_L | rung 25 | 15.65 |
| 35.71 | 36.16 | foot_L | rung 24 | 15.05 |
| 35.74 | 36.16 | hand_R | rung 26 | 16.25 |
| 36.21 | 36.66 | foot_R | rung 25 | 15.65 |
| 36.24 | 36.66 | hand_L | rung 27 | 16.85 |
| 36.71 | 37.16 | foot_L | rung 26 | 16.25 |
| 36.74 | 37.16 | hand_R | rung 28 | 17.45 |
| 37.21 | 37.66 | foot_R | rung 27 | 16.85 |
| 37.24 | 37.66 | hand_L | rung 29 | 18.05 |
| 37.71 | 38.16 | foot_L | rung 28 | 17.45 |
| 37.74 | 38.16 | hand_R | rung 30 | 18.65 |
| 38.21 | 38.66 | foot_R | rung 29 | 18.05 |
| 38.24 | 38.66 | hand_L | rung 31 | 19.25 |
| 38.71 | 39.16 | foot_L | rung 30 | 18.65 |
| 38.74 | 39.16 | hand_R | rung 32 | 19.85 |
| 39.21 | 39.66 | foot_R | rung 31 | 19.25 |
| 39.24 | 39.66 | hand_L | rung 33 | 20.45 |
| 39.71 | 40.16 | foot_L | rung 32 | 19.85 |
| 39.74 | 40.16 | hand_R | rung 34 | 21.05 |
| 40.21 | 40.66 | foot_R | rung 33 | 20.45 |
| 40.42 | 40.84 | hand_L | rail_top | 21.87 (rail top) |
| 40.42 | 40.84 | hand_R | rail_top | 21.87 (rail top) |
| 40.71 | 41.16 | foot_L | rung 34 | 21.05 |
| 43.06 | 43.78 | hand_R | hatch_frame |  |

</details>

<details><summary>Crew 2 — Crew 2 (72 limb moves, 26.49–47.99 s)</summary>

| lift-off | contact | limb | target | height m |
|---|---|---|---|---|
| 26.64 | 27.09 | hand_R | rung 2 | 1.85 |
| 26.84 | 27.29 | hand_L | rung 1 | 1.25 |
| 27.04 | 27.49 | foot_L | rung 0 | 0.65 |
| 27.60 | 28.05 | foot_R | rung 1 | 1.25 |
| 27.62 | 28.04 | hand_L | rung 3 | 2.45 |
| 28.11 | 28.56 | foot_L | rung 2 | 1.85 |
| 28.14 | 28.56 | hand_R | rung 4 | 3.05 |
| 28.61 | 29.06 | foot_R | rung 3 | 2.45 |
| 28.64 | 29.06 | hand_L | rung 5 | 3.65 |
| 29.11 | 29.56 | foot_L | rung 4 | 3.05 |
| 29.14 | 29.56 | hand_R | rung 6 | 4.25 |
| 29.61 | 30.06 | foot_R | rung 5 | 3.65 |
| 29.64 | 30.06 | hand_L | rung 7 | 4.85 |
| 30.11 | 30.56 | foot_L | rung 6 | 4.25 |
| 30.14 | 30.56 | hand_R | rung 8 | 5.45 |
| 30.61 | 31.06 | foot_R | rung 7 | 4.85 |
| 30.64 | 31.06 | hand_L | rung 9 | 6.05 |
| 31.11 | 31.56 | foot_L | rung 8 | 5.45 |
| 31.14 | 31.56 | hand_R | rung 10 | 6.65 |
| 31.61 | 32.06 | foot_R | rung 9 | 6.05 |
| 31.64 | 32.06 | hand_L | rung 11 | 7.25 |
| 32.11 | 32.56 | foot_L | rung 10 | 6.65 |
| 32.14 | 32.56 | hand_R | rung 12 | 7.85 |
| 32.61 | 33.06 | foot_R | rung 11 | 7.25 |
| 32.64 | 33.06 | hand_L | rung 13 | 8.45 |
| 33.11 | 33.56 | foot_L | rung 12 | 7.85 |
| 33.14 | 33.56 | hand_R | rung 14 | 9.05 |
| 33.61 | 34.06 | foot_R | rung 13 | 8.45 |
| 33.64 | 34.06 | hand_L | rung 15 | 9.65 |
| 34.11 | 34.56 | foot_L | rung 14 | 9.05 |
| 34.14 | 34.56 | hand_R | rung 16 | 10.25 |
| 34.61 | 35.06 | foot_R | rung 15 | 9.65 |
| 34.64 | 35.06 | hand_L | rung 17 | 10.85 |
| 35.11 | 35.56 | foot_L | rung 16 | 10.25 |
| 35.14 | 35.56 | hand_R | rung 18 | 11.45 |
| 35.61 | 36.06 | foot_R | rung 17 | 10.85 |
| 35.64 | 36.06 | hand_L | rung 19 | 12.05 |
| 36.11 | 36.56 | foot_L | rung 18 | 11.45 |
| 36.14 | 36.56 | hand_R | rung 20 | 12.65 |
| 36.61 | 37.06 | foot_R | rung 19 | 12.05 |
| 36.64 | 37.06 | hand_L | rung 21 | 13.25 |
| 37.11 | 37.56 | foot_L | rung 20 | 12.65 |
| 37.14 | 37.56 | hand_R | rung 22 | 13.85 |
| 37.61 | 38.06 | foot_R | rung 21 | 13.25 |
| 37.64 | 38.06 | hand_L | rung 23 | 14.45 |
| 38.11 | 38.56 | foot_L | rung 22 | 13.85 |
| 38.14 | 38.56 | hand_R | rung 24 | 15.05 |
| 38.61 | 39.06 | foot_R | rung 23 | 14.45 |
| 38.64 | 39.06 | hand_L | rung 25 | 15.65 |
| 39.11 | 39.56 | foot_L | rung 24 | 15.05 |
| 39.14 | 39.56 | hand_R | rung 26 | 16.25 |
| 39.61 | 40.06 | foot_R | rung 25 | 15.65 |
| 39.64 | 40.06 | hand_L | rung 27 | 16.85 |
| 40.11 | 40.56 | foot_L | rung 26 | 16.25 |
| 40.14 | 40.56 | hand_R | rung 28 | 17.45 |
| 40.61 | 41.06 | foot_R | rung 27 | 16.85 |
| 40.64 | 41.06 | hand_L | rung 29 | 18.05 |
| 41.11 | 41.56 | foot_L | rung 28 | 17.45 |
| 41.14 | 41.56 | hand_R | rung 30 | 18.65 |
| 41.61 | 42.06 | foot_R | rung 29 | 18.05 |
| 41.64 | 42.06 | hand_L | rung 31 | 19.25 |
| 42.11 | 42.56 | foot_L | rung 30 | 18.65 |
| 42.14 | 42.56 | hand_R | rung 32 | 19.85 |
| 42.61 | 43.06 | foot_R | rung 31 | 19.25 |
| 42.64 | 43.06 | hand_L | rung 33 | 20.45 |
| 43.11 | 43.56 | foot_L | rung 32 | 19.85 |
| 43.14 | 43.56 | hand_R | rung 34 | 21.05 |
| 43.61 | 44.06 | foot_R | rung 33 | 20.45 |
| 43.82 | 44.24 | hand_L | rail_top | 21.87 (rail top) |
| 43.82 | 44.24 | hand_R | rail_top | 21.87 (rail top) |
| 44.11 | 44.56 | foot_L | rung 34 | 21.05 |
| 46.46 | 47.18 | hand_L | hatch_frame |  |

</details>

<details><summary>Crew 3 — Crew 3 (72 limb moves, 29.89–51.39 s)</summary>

| lift-off | contact | limb | target | height m |
|---|---|---|---|---|
| 30.04 | 30.49 | hand_R | rung 2 | 1.85 |
| 30.24 | 30.69 | hand_L | rung 1 | 1.25 |
| 30.44 | 30.89 | foot_L | rung 0 | 0.65 |
| 31.00 | 31.45 | foot_R | rung 1 | 1.25 |
| 31.02 | 31.44 | hand_L | rung 3 | 2.45 |
| 31.51 | 31.96 | foot_L | rung 2 | 1.85 |
| 31.54 | 31.96 | hand_R | rung 4 | 3.05 |
| 32.01 | 32.46 | foot_R | rung 3 | 2.45 |
| 32.04 | 32.46 | hand_L | rung 5 | 3.65 |
| 32.51 | 32.96 | foot_L | rung 4 | 3.05 |
| 32.54 | 32.96 | hand_R | rung 6 | 4.25 |
| 33.01 | 33.46 | foot_R | rung 5 | 3.65 |
| 33.04 | 33.46 | hand_L | rung 7 | 4.85 |
| 33.51 | 33.96 | foot_L | rung 6 | 4.25 |
| 33.54 | 33.96 | hand_R | rung 8 | 5.45 |
| 34.01 | 34.46 | foot_R | rung 7 | 4.85 |
| 34.04 | 34.46 | hand_L | rung 9 | 6.05 |
| 34.51 | 34.96 | foot_L | rung 8 | 5.45 |
| 34.54 | 34.96 | hand_R | rung 10 | 6.65 |
| 35.01 | 35.46 | foot_R | rung 9 | 6.05 |
| 35.04 | 35.46 | hand_L | rung 11 | 7.25 |
| 35.51 | 35.96 | foot_L | rung 10 | 6.65 |
| 35.54 | 35.96 | hand_R | rung 12 | 7.85 |
| 36.01 | 36.46 | foot_R | rung 11 | 7.25 |
| 36.04 | 36.46 | hand_L | rung 13 | 8.45 |
| 36.51 | 36.96 | foot_L | rung 12 | 7.85 |
| 36.54 | 36.96 | hand_R | rung 14 | 9.05 |
| 37.01 | 37.46 | foot_R | rung 13 | 8.45 |
| 37.04 | 37.46 | hand_L | rung 15 | 9.65 |
| 37.51 | 37.96 | foot_L | rung 14 | 9.05 |
| 37.54 | 37.96 | hand_R | rung 16 | 10.25 |
| 38.01 | 38.46 | foot_R | rung 15 | 9.65 |
| 38.04 | 38.46 | hand_L | rung 17 | 10.85 |
| 38.51 | 38.96 | foot_L | rung 16 | 10.25 |
| 38.54 | 38.96 | hand_R | rung 18 | 11.45 |
| 39.01 | 39.46 | foot_R | rung 17 | 10.85 |
| 39.04 | 39.46 | hand_L | rung 19 | 12.05 |
| 39.51 | 39.96 | foot_L | rung 18 | 11.45 |
| 39.54 | 39.96 | hand_R | rung 20 | 12.65 |
| 40.01 | 40.46 | foot_R | rung 19 | 12.05 |
| 40.04 | 40.46 | hand_L | rung 21 | 13.25 |
| 40.51 | 40.96 | foot_L | rung 20 | 12.65 |
| 40.54 | 40.96 | hand_R | rung 22 | 13.85 |
| 41.01 | 41.46 | foot_R | rung 21 | 13.25 |
| 41.04 | 41.46 | hand_L | rung 23 | 14.45 |
| 41.51 | 41.96 | foot_L | rung 22 | 13.85 |
| 41.54 | 41.96 | hand_R | rung 24 | 15.05 |
| 42.01 | 42.46 | foot_R | rung 23 | 14.45 |
| 42.04 | 42.46 | hand_L | rung 25 | 15.65 |
| 42.51 | 42.96 | foot_L | rung 24 | 15.05 |
| 42.54 | 42.96 | hand_R | rung 26 | 16.25 |
| 43.01 | 43.46 | foot_R | rung 25 | 15.65 |
| 43.04 | 43.46 | hand_L | rung 27 | 16.85 |
| 43.51 | 43.96 | foot_L | rung 26 | 16.25 |
| 43.54 | 43.96 | hand_R | rung 28 | 17.45 |
| 44.01 | 44.46 | foot_R | rung 27 | 16.85 |
| 44.04 | 44.46 | hand_L | rung 29 | 18.05 |
| 44.51 | 44.96 | foot_L | rung 28 | 17.45 |
| 44.54 | 44.96 | hand_R | rung 30 | 18.65 |
| 45.01 | 45.46 | foot_R | rung 29 | 18.05 |
| 45.04 | 45.46 | hand_L | rung 31 | 19.25 |
| 45.51 | 45.96 | foot_L | rung 30 | 18.65 |
| 45.54 | 45.96 | hand_R | rung 32 | 19.85 |
| 46.01 | 46.46 | foot_R | rung 31 | 19.25 |
| 46.04 | 46.46 | hand_L | rung 33 | 20.45 |
| 46.51 | 46.96 | foot_L | rung 32 | 19.85 |
| 46.54 | 46.96 | hand_R | rung 34 | 21.05 |
| 47.01 | 47.46 | foot_R | rung 33 | 20.45 |
| 47.22 | 47.64 | hand_L | rail_top | 21.87 (rail top) |
| 47.22 | 47.64 | hand_R | rail_top | 21.87 (rail top) |
| 47.51 | 47.96 | foot_L | rung 34 | 21.05 |
| 49.86 | 50.58 | hand_R | hatch_frame |  |

</details>

<details><summary>Crew 4 — Crew 4 (72 limb moves, 33.29–54.79 s)</summary>

| lift-off | contact | limb | target | height m |
|---|---|---|---|---|
| 33.44 | 33.89 | hand_R | rung 2 | 1.85 |
| 33.64 | 34.09 | hand_L | rung 1 | 1.25 |
| 33.84 | 34.29 | foot_L | rung 0 | 0.65 |
| 34.40 | 34.85 | foot_R | rung 1 | 1.25 |
| 34.42 | 34.84 | hand_L | rung 3 | 2.45 |
| 34.91 | 35.36 | foot_L | rung 2 | 1.85 |
| 34.94 | 35.36 | hand_R | rung 4 | 3.05 |
| 35.41 | 35.86 | foot_R | rung 3 | 2.45 |
| 35.44 | 35.86 | hand_L | rung 5 | 3.65 |
| 35.91 | 36.36 | foot_L | rung 4 | 3.05 |
| 35.94 | 36.36 | hand_R | rung 6 | 4.25 |
| 36.41 | 36.86 | foot_R | rung 5 | 3.65 |
| 36.44 | 36.86 | hand_L | rung 7 | 4.85 |
| 36.91 | 37.36 | foot_L | rung 6 | 4.25 |
| 36.94 | 37.36 | hand_R | rung 8 | 5.45 |
| 37.41 | 37.86 | foot_R | rung 7 | 4.85 |
| 37.44 | 37.86 | hand_L | rung 9 | 6.05 |
| 37.91 | 38.36 | foot_L | rung 8 | 5.45 |
| 37.94 | 38.36 | hand_R | rung 10 | 6.65 |
| 38.41 | 38.86 | foot_R | rung 9 | 6.05 |
| 38.44 | 38.86 | hand_L | rung 11 | 7.25 |
| 38.91 | 39.36 | foot_L | rung 10 | 6.65 |
| 38.94 | 39.36 | hand_R | rung 12 | 7.85 |
| 39.41 | 39.86 | foot_R | rung 11 | 7.25 |
| 39.44 | 39.86 | hand_L | rung 13 | 8.45 |
| 39.91 | 40.36 | foot_L | rung 12 | 7.85 |
| 39.94 | 40.36 | hand_R | rung 14 | 9.05 |
| 40.41 | 40.86 | foot_R | rung 13 | 8.45 |
| 40.44 | 40.86 | hand_L | rung 15 | 9.65 |
| 40.91 | 41.36 | foot_L | rung 14 | 9.05 |
| 40.94 | 41.36 | hand_R | rung 16 | 10.25 |
| 41.41 | 41.86 | foot_R | rung 15 | 9.65 |
| 41.44 | 41.86 | hand_L | rung 17 | 10.85 |
| 41.91 | 42.36 | foot_L | rung 16 | 10.25 |
| 41.94 | 42.36 | hand_R | rung 18 | 11.45 |
| 42.41 | 42.86 | foot_R | rung 17 | 10.85 |
| 42.44 | 42.86 | hand_L | rung 19 | 12.05 |
| 42.91 | 43.36 | foot_L | rung 18 | 11.45 |
| 42.94 | 43.36 | hand_R | rung 20 | 12.65 |
| 43.41 | 43.86 | foot_R | rung 19 | 12.05 |
| 43.44 | 43.86 | hand_L | rung 21 | 13.25 |
| 43.91 | 44.36 | foot_L | rung 20 | 12.65 |
| 43.94 | 44.36 | hand_R | rung 22 | 13.85 |
| 44.41 | 44.86 | foot_R | rung 21 | 13.25 |
| 44.44 | 44.86 | hand_L | rung 23 | 14.45 |
| 44.91 | 45.36 | foot_L | rung 22 | 13.85 |
| 44.94 | 45.36 | hand_R | rung 24 | 15.05 |
| 45.41 | 45.86 | foot_R | rung 23 | 14.45 |
| 45.44 | 45.86 | hand_L | rung 25 | 15.65 |
| 45.91 | 46.36 | foot_L | rung 24 | 15.05 |
| 45.94 | 46.36 | hand_R | rung 26 | 16.25 |
| 46.41 | 46.86 | foot_R | rung 25 | 15.65 |
| 46.44 | 46.86 | hand_L | rung 27 | 16.85 |
| 46.91 | 47.36 | foot_L | rung 26 | 16.25 |
| 46.94 | 47.36 | hand_R | rung 28 | 17.45 |
| 47.41 | 47.86 | foot_R | rung 27 | 16.85 |
| 47.44 | 47.86 | hand_L | rung 29 | 18.05 |
| 47.91 | 48.36 | foot_L | rung 28 | 17.45 |
| 47.94 | 48.36 | hand_R | rung 30 | 18.65 |
| 48.41 | 48.86 | foot_R | rung 29 | 18.05 |
| 48.44 | 48.86 | hand_L | rung 31 | 19.25 |
| 48.91 | 49.36 | foot_L | rung 30 | 18.65 |
| 48.94 | 49.36 | hand_R | rung 32 | 19.85 |
| 49.41 | 49.86 | foot_R | rung 31 | 19.25 |
| 49.44 | 49.86 | hand_L | rung 33 | 20.45 |
| 49.91 | 50.36 | foot_L | rung 32 | 19.85 |
| 49.94 | 50.36 | hand_R | rung 34 | 21.05 |
| 50.41 | 50.86 | foot_R | rung 33 | 20.45 |
| 50.62 | 51.04 | hand_L | rail_top | 21.87 (rail top) |
| 50.62 | 51.04 | hand_R | rail_top | 21.87 (rail top) |
| 50.91 | 51.36 | foot_L | rung 34 | 21.05 |
| 53.26 | 53.98 | hand_L | hatch_frame |  |

</details>

## Build checks

- `ik_max_stretch`: 1.0885
- `ik_stretch_at`: {'crew': 1, 't': 46.333, 'limb': 'legL', 'A': [3.72, 22.6, -11.11], 'T': [4.03, 21.94, -11.68]}
- `ik_evals_over_1.02`: 160
- `planted_foot_slide_max_m`: 0.01446
- `max_joint_step_per_frame_m`: 0.236
- `min_gap_upper_boots_to_lower_gloves_m`: -1.751
- `min_gap_at`: [54.43, 3, 4]
