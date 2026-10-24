# Crew boarding — timing sheet

Generated from `crew_boarding_timing.json` (build_boarding.py). Global time in seconds from the start of `crew_call`; key rate in the GLB is 15 Hz, source sampled at 30 fps.

## Clips (play back to back, each clip starts at its own local 0)

| clip | global start | global end | duration |
|---|---|---|---|
| `crew_call` | 0.00 | 3.000 | 3.000 |
| `crew_walk_to_pad` | 3.00 | 22.300 | 19.300 |
| `crew_climb` | 22.30 | 72.533 | 50.233 |

Total: **72.53 s**. Rung pair cycle **1.6 s** (2 rungs = 1.2 m per cycle, 0.75 m/s). Climber stagger (mount to mount) **5.5 s**.
After `inside_hatch` the crew member's Root is scaled to 1e-4 (hidden) and holds that pose to the end of `crew_climb`.

Ladder (measured from launch_pad_game.glb, ship-leg ladder on the +X/+Z side): rungs at y = 0.65 + 0.6·i, i = 0..34 (top rung 21.05 m), deck/rail top 21.85 m, hatch frame grips at 22.55 / 23.2 m.

## Phases per crew member

| crew | role | call | walk start | at ladder / queue spot | mount (first reach) | climb start | climb top | on deck (mantle done) | inside hatch (hidden) | ladder time |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Cargo Manager | 0.00–3.00 | 3.75 | 22.29 | 22.29 | 23.19 | 50.92 | 54.17 | 55.53 | 31.88 |
| 2 | Crew 2 | 0.00–3.00 | 3.65 | 23.89 | 27.79 | 28.69 | 56.42 | 59.67 | 61.03 | 31.88 |
| 3 | Crew 3 | 0.00–3.00 | 5.20 | 24.59 | 33.29 | 34.19 | 61.92 | 65.17 | 66.53 | 31.88 |
| 4 | Crew 4 | 0.00–3.00 | 7.50 | 26.92 | 38.79 | 39.69 | 67.42 | 70.67 | 72.03 | 31.88 |

Phase notes: *call* = Cargo Manager (crew 1) hand to helmet radio 0.2–2.95 s and points to the pad 1.35–3.1 s; crew 2–4 raise a hand to acknowledge. *walk* = planted-foot gait along the shared route around the ship-leg pad; crew 2–4 wait at queue spots by the ladder and step to the ladder foot 3.0 s before their mount. *climb* = diagonal pairs (right hand + left foot on even rungs, left hand + right foot on odd rungs), hands swing in 0.42 of the cycle, feet 0.45. *mantle* (≈3.25 s) = grips on the hatch frame, step onto the deck, then walk ≈1.4 s into the hatch.

## Ladder occupancy (who is on the ladder when)

| crew | on ladder | overlaps with |
|---|---|---|
| 1 | 22.29–54.17 | crew 2 (27.8–54.2), crew 3 (33.3–54.2), crew 4 (38.8–54.2) |
| 2 | 27.79–59.67 | crew 1 (27.8–54.2), crew 3 (33.3–59.7), crew 4 (38.8–59.7) |
| 3 | 33.29–65.17 | crew 1 (33.3–54.2), crew 2 (33.3–59.7), crew 4 (38.8–65.2) |
| 4 | 38.79–70.67 | crew 1 (38.8–54.2), crew 2 (38.8–59.7), crew 3 (38.8–65.2) |

Several crew are on the ladder at once (it is 21.6 m tall), spaced about 4.1 m (≈7 rungs) apart body to body: min clearance upper boots → lower gloves 0.925 m (at 54.17 s, crew 1 above crew 2). Each limb moves in its own window, so climbers never move in lockstep.

## Rung timing per crew member

Each row = one limb move: lift-off → contact, target rung index (height of rung). `rail_top` = deck rail grip, `hatch_frame` = hatch frame grips during the mantle, `deck` = foot onto the deck.

<details><summary>Crew 1 — Cargo Manager (75 limb moves, 22.29–54.17 s)</summary>

| lift-off | contact | limb | target | height m |
|---|---|---|---|---|
| 22.44 | 22.89 | hand_R | rung 2 | 1.85 |
| 22.64 | 23.09 | hand_L | rung 1 | 1.25 |
| 22.84 | 23.29 | foot_L | rung 0 | 0.65 |
| 23.31 | 24.03 | foot_R | rung 1 | 1.25 |
| 23.35 | 24.02 | hand_L | rung 3 | 2.45 |
| 24.11 | 24.83 | foot_L | rung 2 | 1.85 |
| 24.15 | 24.82 | hand_R | rung 4 | 3.05 |
| 24.91 | 25.63 | foot_R | rung 3 | 2.45 |
| 24.95 | 25.62 | hand_L | rung 5 | 3.65 |
| 25.71 | 26.43 | foot_L | rung 4 | 3.05 |
| 25.75 | 26.42 | hand_R | rung 6 | 4.25 |
| 26.51 | 27.23 | foot_R | rung 5 | 3.65 |
| 26.55 | 27.22 | hand_L | rung 7 | 4.85 |
| 27.31 | 28.03 | foot_L | rung 6 | 4.25 |
| 27.35 | 28.02 | hand_R | rung 8 | 5.45 |
| 28.11 | 28.83 | foot_R | rung 7 | 4.85 |
| 28.15 | 28.82 | hand_L | rung 9 | 6.05 |
| 28.91 | 29.63 | foot_L | rung 8 | 5.45 |
| 28.95 | 29.62 | hand_R | rung 10 | 6.65 |
| 29.71 | 30.43 | foot_R | rung 9 | 6.05 |
| 29.75 | 30.42 | hand_L | rung 11 | 7.25 |
| 30.51 | 31.23 | foot_L | rung 10 | 6.65 |
| 30.55 | 31.22 | hand_R | rung 12 | 7.85 |
| 31.31 | 32.03 | foot_R | rung 11 | 7.25 |
| 31.35 | 32.02 | hand_L | rung 13 | 8.45 |
| 32.11 | 32.83 | foot_L | rung 12 | 7.85 |
| 32.15 | 32.82 | hand_R | rung 14 | 9.05 |
| 32.91 | 33.63 | foot_R | rung 13 | 8.45 |
| 32.95 | 33.62 | hand_L | rung 15 | 9.65 |
| 33.71 | 34.43 | foot_L | rung 14 | 9.05 |
| 33.75 | 34.42 | hand_R | rung 16 | 10.25 |
| 34.51 | 35.23 | foot_R | rung 15 | 9.65 |
| 34.55 | 35.22 | hand_L | rung 17 | 10.85 |
| 35.31 | 36.03 | foot_L | rung 16 | 10.25 |
| 35.35 | 36.02 | hand_R | rung 18 | 11.45 |
| 36.11 | 36.83 | foot_R | rung 17 | 10.85 |
| 36.15 | 36.82 | hand_L | rung 19 | 12.05 |
| 36.91 | 37.63 | foot_L | rung 18 | 11.45 |
| 36.95 | 37.62 | hand_R | rung 20 | 12.65 |
| 37.71 | 38.43 | foot_R | rung 19 | 12.05 |
| 37.75 | 38.42 | hand_L | rung 21 | 13.25 |
| 38.51 | 39.23 | foot_L | rung 20 | 12.65 |
| 38.55 | 39.22 | hand_R | rung 22 | 13.85 |
| 39.31 | 40.03 | foot_R | rung 21 | 13.25 |
| 39.35 | 40.02 | hand_L | rung 23 | 14.45 |
| 40.11 | 40.83 | foot_L | rung 22 | 13.85 |
| 40.15 | 40.82 | hand_R | rung 24 | 15.05 |
| 40.91 | 41.63 | foot_R | rung 23 | 14.45 |
| 40.95 | 41.62 | hand_L | rung 25 | 15.65 |
| 41.71 | 42.43 | foot_L | rung 24 | 15.05 |
| 41.75 | 42.42 | hand_R | rung 26 | 16.25 |
| 42.51 | 43.23 | foot_R | rung 25 | 15.65 |
| 42.55 | 43.22 | hand_L | rung 27 | 16.85 |
| 43.31 | 44.03 | foot_L | rung 26 | 16.25 |
| 43.35 | 44.02 | hand_R | rung 28 | 17.45 |
| 44.11 | 44.83 | foot_R | rung 27 | 16.85 |
| 44.15 | 44.82 | hand_L | rung 29 | 18.05 |
| 44.91 | 45.63 | foot_L | rung 28 | 17.45 |
| 44.95 | 45.62 | hand_R | rung 30 | 18.65 |
| 45.71 | 46.43 | foot_R | rung 29 | 18.05 |
| 45.75 | 46.42 | hand_L | rung 31 | 19.25 |
| 46.51 | 47.23 | foot_L | rung 30 | 18.65 |
| 46.55 | 47.22 | hand_R | rung 32 | 19.85 |
| 47.31 | 48.03 | foot_R | rung 31 | 19.25 |
| 47.35 | 48.02 | hand_L | rung 33 | 20.45 |
| 48.11 | 48.83 | foot_L | rung 32 | 19.85 |
| 48.15 | 48.82 | hand_R | rung 34 | 21.05 |
| 48.91 | 49.63 | foot_R | rung 33 | 20.45 |
| 49.24 | 49.91 | hand_L | rail_top | 21.87 (rail top) |
| 49.24 | 49.91 | hand_R | rail_top | 21.87 (rail top) |
| 49.81 | 50.53 | foot_L | rung 34 | 21.05 |
| 51.82 | 52.32 | hand_L | hatch_frame |  |
| 52.02 | 52.52 | hand_R | hatch_frame |  |
| 53.07 | 53.47 | hand_L | hatch_frame |  |
| 53.27 | 53.67 | hand_R | hatch_frame |  |

</details>

<details><summary>Crew 2 — Crew 2 (75 limb moves, 27.79–59.67 s)</summary>

| lift-off | contact | limb | target | height m |
|---|---|---|---|---|
| 27.94 | 28.39 | hand_R | rung 2 | 1.85 |
| 28.14 | 28.59 | hand_L | rung 1 | 1.25 |
| 28.34 | 28.79 | foot_L | rung 0 | 0.65 |
| 28.81 | 29.53 | foot_R | rung 1 | 1.25 |
| 28.85 | 29.52 | hand_L | rung 3 | 2.45 |
| 29.61 | 30.33 | foot_L | rung 2 | 1.85 |
| 29.65 | 30.32 | hand_R | rung 4 | 3.05 |
| 30.41 | 31.13 | foot_R | rung 3 | 2.45 |
| 30.45 | 31.12 | hand_L | rung 5 | 3.65 |
| 31.21 | 31.93 | foot_L | rung 4 | 3.05 |
| 31.25 | 31.92 | hand_R | rung 6 | 4.25 |
| 32.01 | 32.73 | foot_R | rung 5 | 3.65 |
| 32.05 | 32.72 | hand_L | rung 7 | 4.85 |
| 32.81 | 33.53 | foot_L | rung 6 | 4.25 |
| 32.85 | 33.52 | hand_R | rung 8 | 5.45 |
| 33.61 | 34.33 | foot_R | rung 7 | 4.85 |
| 33.65 | 34.32 | hand_L | rung 9 | 6.05 |
| 34.41 | 35.13 | foot_L | rung 8 | 5.45 |
| 34.45 | 35.12 | hand_R | rung 10 | 6.65 |
| 35.21 | 35.93 | foot_R | rung 9 | 6.05 |
| 35.25 | 35.92 | hand_L | rung 11 | 7.25 |
| 36.01 | 36.73 | foot_L | rung 10 | 6.65 |
| 36.05 | 36.72 | hand_R | rung 12 | 7.85 |
| 36.81 | 37.53 | foot_R | rung 11 | 7.25 |
| 36.85 | 37.52 | hand_L | rung 13 | 8.45 |
| 37.61 | 38.33 | foot_L | rung 12 | 7.85 |
| 37.65 | 38.32 | hand_R | rung 14 | 9.05 |
| 38.41 | 39.13 | foot_R | rung 13 | 8.45 |
| 38.45 | 39.12 | hand_L | rung 15 | 9.65 |
| 39.21 | 39.93 | foot_L | rung 14 | 9.05 |
| 39.25 | 39.92 | hand_R | rung 16 | 10.25 |
| 40.01 | 40.73 | foot_R | rung 15 | 9.65 |
| 40.05 | 40.72 | hand_L | rung 17 | 10.85 |
| 40.81 | 41.53 | foot_L | rung 16 | 10.25 |
| 40.85 | 41.52 | hand_R | rung 18 | 11.45 |
| 41.61 | 42.33 | foot_R | rung 17 | 10.85 |
| 41.65 | 42.32 | hand_L | rung 19 | 12.05 |
| 42.41 | 43.13 | foot_L | rung 18 | 11.45 |
| 42.45 | 43.12 | hand_R | rung 20 | 12.65 |
| 43.21 | 43.93 | foot_R | rung 19 | 12.05 |
| 43.25 | 43.92 | hand_L | rung 21 | 13.25 |
| 44.01 | 44.73 | foot_L | rung 20 | 12.65 |
| 44.05 | 44.72 | hand_R | rung 22 | 13.85 |
| 44.81 | 45.53 | foot_R | rung 21 | 13.25 |
| 44.85 | 45.52 | hand_L | rung 23 | 14.45 |
| 45.61 | 46.33 | foot_L | rung 22 | 13.85 |
| 45.65 | 46.32 | hand_R | rung 24 | 15.05 |
| 46.41 | 47.13 | foot_R | rung 23 | 14.45 |
| 46.45 | 47.12 | hand_L | rung 25 | 15.65 |
| 47.21 | 47.93 | foot_L | rung 24 | 15.05 |
| 47.25 | 47.92 | hand_R | rung 26 | 16.25 |
| 48.01 | 48.73 | foot_R | rung 25 | 15.65 |
| 48.05 | 48.72 | hand_L | rung 27 | 16.85 |
| 48.81 | 49.53 | foot_L | rung 26 | 16.25 |
| 48.85 | 49.52 | hand_R | rung 28 | 17.45 |
| 49.61 | 50.33 | foot_R | rung 27 | 16.85 |
| 49.65 | 50.32 | hand_L | rung 29 | 18.05 |
| 50.41 | 51.13 | foot_L | rung 28 | 17.45 |
| 50.45 | 51.12 | hand_R | rung 30 | 18.65 |
| 51.21 | 51.93 | foot_R | rung 29 | 18.05 |
| 51.25 | 51.92 | hand_L | rung 31 | 19.25 |
| 52.01 | 52.73 | foot_L | rung 30 | 18.65 |
| 52.05 | 52.72 | hand_R | rung 32 | 19.85 |
| 52.81 | 53.53 | foot_R | rung 31 | 19.25 |
| 52.85 | 53.52 | hand_L | rung 33 | 20.45 |
| 53.61 | 54.33 | foot_L | rung 32 | 19.85 |
| 53.65 | 54.32 | hand_R | rung 34 | 21.05 |
| 54.41 | 55.13 | foot_R | rung 33 | 20.45 |
| 54.74 | 55.41 | hand_L | rail_top | 21.87 (rail top) |
| 54.74 | 55.41 | hand_R | rail_top | 21.87 (rail top) |
| 55.31 | 56.03 | foot_L | rung 34 | 21.05 |
| 57.32 | 57.82 | hand_L | hatch_frame |  |
| 57.52 | 58.02 | hand_R | hatch_frame |  |
| 58.57 | 58.97 | hand_L | hatch_frame |  |
| 58.77 | 59.17 | hand_R | hatch_frame |  |

</details>

<details><summary>Crew 3 — Crew 3 (75 limb moves, 33.29–65.17 s)</summary>

| lift-off | contact | limb | target | height m |
|---|---|---|---|---|
| 33.44 | 33.89 | hand_R | rung 2 | 1.85 |
| 33.64 | 34.09 | hand_L | rung 1 | 1.25 |
| 33.84 | 34.29 | foot_L | rung 0 | 0.65 |
| 34.31 | 35.03 | foot_R | rung 1 | 1.25 |
| 34.35 | 35.02 | hand_L | rung 3 | 2.45 |
| 35.11 | 35.83 | foot_L | rung 2 | 1.85 |
| 35.15 | 35.82 | hand_R | rung 4 | 3.05 |
| 35.91 | 36.63 | foot_R | rung 3 | 2.45 |
| 35.95 | 36.62 | hand_L | rung 5 | 3.65 |
| 36.71 | 37.43 | foot_L | rung 4 | 3.05 |
| 36.75 | 37.42 | hand_R | rung 6 | 4.25 |
| 37.51 | 38.23 | foot_R | rung 5 | 3.65 |
| 37.55 | 38.22 | hand_L | rung 7 | 4.85 |
| 38.31 | 39.03 | foot_L | rung 6 | 4.25 |
| 38.35 | 39.02 | hand_R | rung 8 | 5.45 |
| 39.11 | 39.83 | foot_R | rung 7 | 4.85 |
| 39.15 | 39.82 | hand_L | rung 9 | 6.05 |
| 39.91 | 40.63 | foot_L | rung 8 | 5.45 |
| 39.95 | 40.62 | hand_R | rung 10 | 6.65 |
| 40.71 | 41.43 | foot_R | rung 9 | 6.05 |
| 40.75 | 41.42 | hand_L | rung 11 | 7.25 |
| 41.51 | 42.23 | foot_L | rung 10 | 6.65 |
| 41.55 | 42.22 | hand_R | rung 12 | 7.85 |
| 42.31 | 43.03 | foot_R | rung 11 | 7.25 |
| 42.35 | 43.02 | hand_L | rung 13 | 8.45 |
| 43.11 | 43.83 | foot_L | rung 12 | 7.85 |
| 43.15 | 43.82 | hand_R | rung 14 | 9.05 |
| 43.91 | 44.63 | foot_R | rung 13 | 8.45 |
| 43.95 | 44.62 | hand_L | rung 15 | 9.65 |
| 44.71 | 45.43 | foot_L | rung 14 | 9.05 |
| 44.75 | 45.42 | hand_R | rung 16 | 10.25 |
| 45.51 | 46.23 | foot_R | rung 15 | 9.65 |
| 45.55 | 46.22 | hand_L | rung 17 | 10.85 |
| 46.31 | 47.03 | foot_L | rung 16 | 10.25 |
| 46.35 | 47.02 | hand_R | rung 18 | 11.45 |
| 47.11 | 47.83 | foot_R | rung 17 | 10.85 |
| 47.15 | 47.82 | hand_L | rung 19 | 12.05 |
| 47.91 | 48.63 | foot_L | rung 18 | 11.45 |
| 47.95 | 48.62 | hand_R | rung 20 | 12.65 |
| 48.71 | 49.43 | foot_R | rung 19 | 12.05 |
| 48.75 | 49.42 | hand_L | rung 21 | 13.25 |
| 49.51 | 50.23 | foot_L | rung 20 | 12.65 |
| 49.55 | 50.22 | hand_R | rung 22 | 13.85 |
| 50.31 | 51.03 | foot_R | rung 21 | 13.25 |
| 50.35 | 51.02 | hand_L | rung 23 | 14.45 |
| 51.11 | 51.83 | foot_L | rung 22 | 13.85 |
| 51.15 | 51.82 | hand_R | rung 24 | 15.05 |
| 51.91 | 52.63 | foot_R | rung 23 | 14.45 |
| 51.95 | 52.62 | hand_L | rung 25 | 15.65 |
| 52.71 | 53.43 | foot_L | rung 24 | 15.05 |
| 52.75 | 53.42 | hand_R | rung 26 | 16.25 |
| 53.51 | 54.23 | foot_R | rung 25 | 15.65 |
| 53.55 | 54.22 | hand_L | rung 27 | 16.85 |
| 54.31 | 55.03 | foot_L | rung 26 | 16.25 |
| 54.35 | 55.02 | hand_R | rung 28 | 17.45 |
| 55.11 | 55.83 | foot_R | rung 27 | 16.85 |
| 55.15 | 55.82 | hand_L | rung 29 | 18.05 |
| 55.91 | 56.63 | foot_L | rung 28 | 17.45 |
| 55.95 | 56.62 | hand_R | rung 30 | 18.65 |
| 56.71 | 57.43 | foot_R | rung 29 | 18.05 |
| 56.75 | 57.42 | hand_L | rung 31 | 19.25 |
| 57.51 | 58.23 | foot_L | rung 30 | 18.65 |
| 57.55 | 58.22 | hand_R | rung 32 | 19.85 |
| 58.31 | 59.03 | foot_R | rung 31 | 19.25 |
| 58.35 | 59.02 | hand_L | rung 33 | 20.45 |
| 59.11 | 59.83 | foot_L | rung 32 | 19.85 |
| 59.15 | 59.82 | hand_R | rung 34 | 21.05 |
| 59.91 | 60.63 | foot_R | rung 33 | 20.45 |
| 60.24 | 60.91 | hand_L | rail_top | 21.87 (rail top) |
| 60.24 | 60.91 | hand_R | rail_top | 21.87 (rail top) |
| 60.81 | 61.53 | foot_L | rung 34 | 21.05 |
| 62.82 | 63.32 | hand_L | hatch_frame |  |
| 63.02 | 63.52 | hand_R | hatch_frame |  |
| 64.07 | 64.47 | hand_L | hatch_frame |  |
| 64.27 | 64.67 | hand_R | hatch_frame |  |

</details>

<details><summary>Crew 4 — Crew 4 (75 limb moves, 38.79–70.67 s)</summary>

| lift-off | contact | limb | target | height m |
|---|---|---|---|---|
| 38.94 | 39.39 | hand_R | rung 2 | 1.85 |
| 39.14 | 39.59 | hand_L | rung 1 | 1.25 |
| 39.34 | 39.79 | foot_L | rung 0 | 0.65 |
| 39.81 | 40.53 | foot_R | rung 1 | 1.25 |
| 39.85 | 40.52 | hand_L | rung 3 | 2.45 |
| 40.61 | 41.33 | foot_L | rung 2 | 1.85 |
| 40.65 | 41.32 | hand_R | rung 4 | 3.05 |
| 41.41 | 42.13 | foot_R | rung 3 | 2.45 |
| 41.45 | 42.12 | hand_L | rung 5 | 3.65 |
| 42.21 | 42.93 | foot_L | rung 4 | 3.05 |
| 42.25 | 42.92 | hand_R | rung 6 | 4.25 |
| 43.01 | 43.73 | foot_R | rung 5 | 3.65 |
| 43.05 | 43.72 | hand_L | rung 7 | 4.85 |
| 43.81 | 44.53 | foot_L | rung 6 | 4.25 |
| 43.85 | 44.52 | hand_R | rung 8 | 5.45 |
| 44.61 | 45.33 | foot_R | rung 7 | 4.85 |
| 44.65 | 45.32 | hand_L | rung 9 | 6.05 |
| 45.41 | 46.13 | foot_L | rung 8 | 5.45 |
| 45.45 | 46.12 | hand_R | rung 10 | 6.65 |
| 46.21 | 46.93 | foot_R | rung 9 | 6.05 |
| 46.25 | 46.92 | hand_L | rung 11 | 7.25 |
| 47.01 | 47.73 | foot_L | rung 10 | 6.65 |
| 47.05 | 47.72 | hand_R | rung 12 | 7.85 |
| 47.81 | 48.53 | foot_R | rung 11 | 7.25 |
| 47.85 | 48.52 | hand_L | rung 13 | 8.45 |
| 48.61 | 49.33 | foot_L | rung 12 | 7.85 |
| 48.65 | 49.32 | hand_R | rung 14 | 9.05 |
| 49.41 | 50.13 | foot_R | rung 13 | 8.45 |
| 49.45 | 50.12 | hand_L | rung 15 | 9.65 |
| 50.21 | 50.93 | foot_L | rung 14 | 9.05 |
| 50.25 | 50.92 | hand_R | rung 16 | 10.25 |
| 51.01 | 51.73 | foot_R | rung 15 | 9.65 |
| 51.05 | 51.72 | hand_L | rung 17 | 10.85 |
| 51.81 | 52.53 | foot_L | rung 16 | 10.25 |
| 51.85 | 52.52 | hand_R | rung 18 | 11.45 |
| 52.61 | 53.33 | foot_R | rung 17 | 10.85 |
| 52.65 | 53.32 | hand_L | rung 19 | 12.05 |
| 53.41 | 54.13 | foot_L | rung 18 | 11.45 |
| 53.45 | 54.12 | hand_R | rung 20 | 12.65 |
| 54.21 | 54.93 | foot_R | rung 19 | 12.05 |
| 54.25 | 54.92 | hand_L | rung 21 | 13.25 |
| 55.01 | 55.73 | foot_L | rung 20 | 12.65 |
| 55.05 | 55.72 | hand_R | rung 22 | 13.85 |
| 55.81 | 56.53 | foot_R | rung 21 | 13.25 |
| 55.85 | 56.52 | hand_L | rung 23 | 14.45 |
| 56.61 | 57.33 | foot_L | rung 22 | 13.85 |
| 56.65 | 57.32 | hand_R | rung 24 | 15.05 |
| 57.41 | 58.13 | foot_R | rung 23 | 14.45 |
| 57.45 | 58.12 | hand_L | rung 25 | 15.65 |
| 58.21 | 58.93 | foot_L | rung 24 | 15.05 |
| 58.25 | 58.92 | hand_R | rung 26 | 16.25 |
| 59.01 | 59.73 | foot_R | rung 25 | 15.65 |
| 59.05 | 59.72 | hand_L | rung 27 | 16.85 |
| 59.81 | 60.53 | foot_L | rung 26 | 16.25 |
| 59.85 | 60.52 | hand_R | rung 28 | 17.45 |
| 60.61 | 61.33 | foot_R | rung 27 | 16.85 |
| 60.65 | 61.32 | hand_L | rung 29 | 18.05 |
| 61.41 | 62.13 | foot_L | rung 28 | 17.45 |
| 61.45 | 62.12 | hand_R | rung 30 | 18.65 |
| 62.21 | 62.93 | foot_R | rung 29 | 18.05 |
| 62.25 | 62.92 | hand_L | rung 31 | 19.25 |
| 63.01 | 63.73 | foot_L | rung 30 | 18.65 |
| 63.05 | 63.72 | hand_R | rung 32 | 19.85 |
| 63.81 | 64.53 | foot_R | rung 31 | 19.25 |
| 63.85 | 64.52 | hand_L | rung 33 | 20.45 |
| 64.61 | 65.33 | foot_L | rung 32 | 19.85 |
| 64.65 | 65.32 | hand_R | rung 34 | 21.05 |
| 65.41 | 66.13 | foot_R | rung 33 | 20.45 |
| 65.74 | 66.41 | hand_L | rail_top | 21.87 (rail top) |
| 65.74 | 66.41 | hand_R | rail_top | 21.87 (rail top) |
| 66.31 | 67.03 | foot_L | rung 34 | 21.05 |
| 68.32 | 68.82 | hand_L | hatch_frame |  |
| 68.52 | 69.02 | hand_R | hatch_frame |  |
| 69.57 | 69.97 | hand_L | hatch_frame |  |
| 69.77 | 70.17 | hand_R | hatch_frame |  |

</details>

## Build checks

- `ik_max_stretch`: 1.0847
- `planted_foot_slide_max_m`: 0.01609
- `max_joint_step_per_frame_m`: 0.215
- `min_gap_upper_boots_to_lower_gloves_m`: 0.925
- `min_gap_at`: [54.17, 1, 2]
