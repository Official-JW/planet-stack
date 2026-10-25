# Art Assistant 2 - restart note
Written 10/25/2026 01:25 PT. The team is pausing because Jacob's weekly usage is nearly used up.

## Live (committed on main)
- Clearance gate: `a0584fb`. `landing_clear_plate.mjs` md5 `acad33c752f06a59fe342b4775060e6c`. It matches Playtester's wb.js (within 0.24 mm on hf23b at 60 Hz), and 89/89 plate tests pass.
- `art/3d/buildings/launch_pad/launch_pad_next.glb`: md5 `a257d93023dc7d22e1c6314b21aa5aaf`, 350,104 B, 15 draws, 29,601 tris, committed in 22cdb9b. The pad is at x 640, the crane base at (640.6, 7) with 14.2 m reach, and the U-turn is r 4.5 at x 667.5.
- `launch_pad_game.glb` md5 `82131aba...`. Do not touch it.

## In progress
- Lane fix A, the only job still running. It works on launch_pad_next.glb. Plan: `/workspace/dockl/lane_fix_0125/lane_fix_0125_plan.json` (md5 `9eab7d503dae0df2922ef120294f91f0`).
  - Crane reach goes up to at least 16.1 m from (640.6, 7).
  - The U-turn becomes r 4.5 round (647, 27.5), from (647, 23) to (647, 32).
  - Truck_Stop moves to (642.85, 0, 23).
  - Draws and file size stay the same or smaller, and the deliverable is one 375 still.
  - BLOCKED at 01:25 PT, nothing built or committed. Reaching 16.1 m means the arm tip sits at about 17.2 m, but the ship's hull is only 15.95 m from the crane's centre at arm height (the current tip is 15.29 m, so 0.66 m clear). At the Hold_Door pose (slew 1.57) the longer arm would sit about 1.3 m inside the hull. The plan's other option (base at z ≥ 8.9) needs 15.4 m to reach Hold_Door, past the 14.2 m maximum.
  - 01:27 PT: Director picked (a), and A&A says do it tonight, after the cockpit still. This is the second and last try; if it still clashes with the ship, park it here. Original options: (a) move the crane base to at least about 21.6 m from the ship's centre line (it's 20.0 m now), (b) approve a hold-loading pose that doesn't swing the arm over the ship, or (c) allow a truck pull-off bay, which needs the S-bend ruling waived.
  - The U-turn and Truck_Stop move are quick on their own, but they leave the truck where the crane can't reach it. Inspection scripts are in /workspace/lane0125.
  - DONE 01:5x PT (try 2, option a). launch_pad_next.glb a257d930 -> 1b25bff22ba1e45520c5b29344b0b134, 347,760 B, 15 draws, 29,505 tris, meshopt + quantization.
    - Crane base moved to pad-local (0.6, 0, 8.8) = world (640.6, 0, 8.8), 21.81 m from the ship centre line. trolley_max 16.2 m (jib stretched past x 5 m, tip 17.28 m).
    - Reach: Pick_Point 14.243 (margin 1.957), Pick_Point_02 14.269 (1.931), Hold_Door 15.315 (0.885), bays 5.905-12.76. All 17 crane targets solve within 0.6 mm.
    - Clearance, full 360 slew, jib + glow vs every visible part: min 0.493 m (Ship_Placeholder at slew 90, the Hold_Door direction). Truck pickup slews: nothing within 0.5 m. Footing 2.65 m from the nearest part, 9.9 m from the road edge.
    - Road: spur ribbon (192 v / 96 t) and Spur_Taper_In_A/B, Spur_Taper_Out_A/B removed; r 4.5 U-turn round (647, 27.5); Truck_Stop (642.85, 0, 23) heading +X. Truck path vs pad: 9.9 m clear (nearest = crane footing), 11.05 m to Pad_Base.
    - All six crane_* clips re-keyed to the new solves. Frame at 375: worst spare 5.3 px (Ship top, same as before), Truck 150 px to HUD, Crane_Reach (360 sweep) 94.7 px.
    - Coder: game constants for the crane base need z 8.8 if they don't read the markers. Scripts: launch_pad/_src/lane_fix_a_*.mjs, proofs/lane_fix_a_*.json.

## Half done (not committed, files left in place)
- `/workspace/pad_fuelline/launch_pad_game_lv1ship.glb`, md5 `1042e76793da1f97a9837a4a823873f0`.
  - It has the cockpit window: 4 panes and a `Cockpit_Window` node.
  - Spec: `art/3d/buildings/launch_pad/lv1/SPEC_cockpit_window.md`. Engine_Ring_Mount is at ship-local (0, 2.9, 0).
  - Still to do: the glow-on and glow-off stills at 375.
- `/workspace/pad_fuelline/launch_pad_game_lv1door.glb`, md5 `2c287db2e1b1d99287a9e9614f2ac2af`.
  - It has the cargo door, the fuel line trimmed to 12 m, the plate, the west pipe and the notes at 641/592.
  - Still to do: move Pad_Base and Tier_08 at least 1 m west so crawler A clears them (see `art/3d/vehicles/ship_transporter/SPEC_A.md`), plus a 375 still.
- Ladder cage scratch files are STOPPED by Jacob (1:07 AM). Don't resume them unless Jacob says so. They are in `/workspace/pad_cage/`:
  - `launch_pad_db78a6f7_t064.glb` b9597753
  - `launch_pad_db78a6f7_t073.glb` ff2338aa
  - `launch_pad_db78a6f7_t076.glb` e158f0c2
  - `launch_pad_db78a6f7_cage60.glb` 21c553af (about +61 mm)
  - `launch_pad_db78a6f7_cage60b.glb` a31bdc99 (brackets, dropped)
  - The hit dump is `dump_hf23b_21c553af_crew1.json/csv`. The planned rung and grip gate follow-up was never made.
- Status log: `/tmp/lp_lv1/STATUS.md`. It's in /tmp, so it may not survive.

## Next, in order (after the restart)
1. Done 01:5x: cockpit glow-on still and lane fix A (see above). Send A&A the hash, md5, reach and 375 still if not already sent.
2. The cockpit window glow-on and glow-off stills at 375 (lv1ship 1042e767). They were held for Coder's crew tag.
3. The Lv1 ship aft skirt fit at Engine_Ring_Mount, using `art/vfx/engine_flame/aft_skirt/` as it is (aft_skirt_N06..N11, engine_ring_N06..N11, layout.json). A&A will shrink it for iPhone.
4. The cargo door crawler move (lv1door 2c287db2).

## Open questions
- Ladder and cage work: does it stay stopped? That's waiting on Jacob.
- Aft skirt: when does A&A's iPhone-size version arrive, and is the fit-only pass still wanted before that?

## Rules to remember
- Wrap heavy jobs as `flock /tmp/planet_stack_heavy.lock nice -n 19 ... -t 4`.
- Push with `git pull --rebase --autostash origin main`.
- Commit only my own launch_pad paths.
- When told to stop, stop only my own workers.
