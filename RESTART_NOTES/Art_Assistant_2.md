# Art Assistant 2 - restart note

## 10/29/2026 10:48 PM PT: Eve voice clips (hibernating again)
- Voice samples are in AUDIO/eve_voice_samples/; Jacob picked A (Kokoro af_heart, speed 0.95). The tool runs from /workspace/tts (venv plus model).
- All 8 game clips are made in AUDIO/eve_clips/ as mp3 files; md5s, Whisper results and flags are in eve_clips/notes.md.
- Open item: cargo_full_0 ("boxes" heard as "box is") and cargo_delivered_0 ("has" heard as "is") need a human listen. Each has one try left. Nothing is running and nothing is committed.
Written 10/29/2026 9:55 PM PT. Hibernating on Jacob's order (low usage), relayed by Art Manager. Nothing is running: no Blender jobs and no workers. Not committed.

## Habitat v2 (latest work, delivered)
- Jacob rejected v1 and wants a "super futuristic" tall oval tower. The ref /workspace/habitat_concept/v2/jacob_ref.jpg (ffed3529) was lost in the 3:28 PM box restart.
- Locked size (Art Manager and A&A agreed): a 30x26 m oval tower, 40 m tall, on a 34x30x6 m podium at slot x 960. Cam_Target (960, 21.25, 0), frame width 48, 38 deg FOV, 18 deg pitch. Max safe height 45.5 m, with 375 as the limit.
- A&A's final massing: /workspace/habitat_concept/v2/exterior/_src/habitat_v2_massing.glb, md5 7ba33b955865d5afa8e3337a01acb05d (locked).
- Delivered to Art Manager at 3:50 PM, in /workspace/habitat_concept/v2/placement/:
  - habitat_v2_placement_393x852.png 1bb10f992eeeef3e347d065f50d2bdd1
  - habitat_v2_placement_393x852_guides.png af4c193edb0aaf11bbe6441a0946c377
  - habitat_v2_placement.blend 91054ba805ff9d3c9dbe3a39fc2470a3
  - Top at 267 px at 393 (102 px under the 165 px safe band); base at 676 px.
  - The stand-in is kept as *_standin.*. Scripts: hab2_swap.py, comp2_swap.py. Fit diagrams: hab_v2_fit_test_393x852.png f2ffbc3b, hab_v2_fit_test_375x667.png 302b83a0.
- Known gaps: the glass and atrium emission render white in my Eevee pass, so the look comes from A&A's render. 375 isn't rendered (math says top about 171-185 px).
- Next step: none. Wait for Art Manager or Director feedback. All tries are used (plus the one approved swap).

## Habitat v1 (accepted then superseded)
- /workspace/habitat_concept/placement/habitat_placement_393x852.png 5afc3403a8ab08d070c651a16d1a3126.
- Open flag for Director: in code the Pad (640) sits between the Dock (480) and the Shipyard (800), so the Shipyard isn't directly right of the Dock.

## Lv1 launch VFX
- art/vfx/lv1_launch/lv1_launch_vfx.glb b6d5beb7256d8a48b1c183967cab7761; NOTES_for_Coder.md 4659c1d6.
- Local commits a422b9c and f87f42f. Pushing them needs Jacob's direct OK. Check whether origin already has them before pushing.

---
## Older note (10/25 01:25 PT) below
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
  - 01:57 PT Director: the z 13 lanes stay, the lane move is PARKED. f6af441 (lane fix A, 1b25bff2, z 23 lane + U-turn at x 647) is kept in git for if the lanes ever move; numbers below.
  - NOW LIVE in launch_pad_next.glb (z 13 version, commit see git log 10/25 ~02:0x): md5 903b59baca55b844ae82c869efe2b9f7, 350,088 B, 15 draws, 29,601 tris. Crane base (640.6, 0, 8.8), trolley_max 16.2; roads/Truck_Stop/spur/tapers/U-turn byte-identical to a257d930 (proofs/lane_fix_z13_same_roads_as_a257d930.json). Picks 10.773 m (margin 5.427), Hold_Door 15.315 (0.885), min clearance 0.493 m (Ship, slew 90), road mesh 6.46 m from the crane footing. Scripts _src/lane_fix_z13_*.mjs, proofs/lane_fix_z13_*.json.
  - PARKED f6af441 (try 2, option a). launch_pad_next.glb a257d930 -> 1b25bff22ba1e45520c5b29344b0b134, 347,760 B, 15 draws, 29,505 tris, meshopt + quantization.
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
1. Done 02:0x: cockpit glow-on still and the crane base move with z 13 lanes kept (see above; lane move parked). Send A&A the hash, md5, reach and 375 still if not already sent.
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


## Update 10/25/2026 02:10 PT (final before the stop)
- Director: the pad keeps a257d930. launch_pad_next.glb is restored to a257d930 in the repo.
- PARKED crane moves, kept for if the lanes ever move or the crane is revisited. Both are in `art/3d/buildings/launch_pad/_parked_crane/`:
  - c0639c1: md5 903b59ba. Crane base at z 8.8 with the z 13 roads; both picks 10.77 m and Hold_Door 0.885 m spare; 0.493 m hull clearance.
  - f6af441: md5 1b25bff2. Crane base at z 8.8 with the z 23 lane and the new U-turn.
- COMMITTED for Coder: `art/3d/buildings/launch_pad/launch_pad_game_lv1ship.glb`, md5 1042e767 (cockpit window, Cockpit_Window and Engine_Ring_Mount nodes, plus the Lv1 door changes). The note is `lv1/CHANGES_lv1ship_1042e767.md` and the still is `lv1/proofs/lv1ship_1042e767_cockpit_glow_on_375.png`. It hasn't been re-checked against the live cage or gate.
- I added a line about the verifier change to LESSONS.md (untracked, approved by Director).
- After the pause: (1) the aft skirt fit, (2) the cockpit glow-off still, (3) the cargo door crawler move. The ladder and cage stay stopped.
