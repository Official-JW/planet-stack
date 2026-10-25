# TOP AFTER PAUSE (Director 02:17)
1. Clean Lv1 ship export without the old built-in bells and legs (AA3). Coder is using the SPEC 9.3 fold-away workaround for now.
2. Dock box visibility: the game counts 4 stored but only 2 show at 393. Slots 01-04 are in one row under the runway. Render with 4 stored, then change the fill order if they are hidden.
3. Optional: lower the leg deploy on screen (now doors at -7 s, legs locked at -4 s) if Jacob wants it.

# Art & Animation restart note (written 10/25/2026 01:25 PT)

Planet Stack is Jacob's game, and this file is about Art & Animation's work. The repo is /workspace/planet-stack, branch main. Commits are named "MM/DD/YYYY - planet-stack - HH:MM", and each agent commits only its own paths.
The helpers report to me: Art Assistant (AA), AA2 and AA3. Their notes are in this folder.

## Live, or going live tonight (Coder's builds)
- live/ = 18:44 (2b70019 copy, 02425e9). Next is the station order, 887a609 (QA3D-next 01:45).
- Mine: mine_ef45f6f1, which is cc084a9b plus the tire tracks and gray ore. No tap markers and no diamonds. Done.
- Refinery bridge v5.3: art/3d/buildings/refinery/refinery_bridge_v5_3.glb, md5 5d862767 (e661ba1). Coder has it staged as scenery only, with the boxes hidden. Director is still deciding whether to loop the clips as scenery or wire them into the cargo sim later (about 130 lines).

## Half done (in the order to resume)
1. Flatbed lane clear of the Dock (Director chose option A, to ship after the bridge).
   - Plan: /workspace/dockl/lane_fix_0125/lane_fix_0125_plan.json (md5 9eab7d50), with the picture in lane_fix_0125_topdown.png (cce0d920).
   - Lanes: out z 23, back z 32, U-turns radius 4.5. Refinery crane 838c3081 (4f71c57).
   - Blocker: the pad crane only reaches 14.2 m and needs 16.1 m or more. That's AA2's job (see AA2's note). Coder holds the lane numbers until AA2's pad hash lands.
2. Landing gear on touchdown (AA3). It's built and posed and the flame scan passes. It's uncommitted in art/vfx/engine_flame/aft_skirt/ (SPEC.md, gear_pose.py, gear.js, aft_skirt_layout.json, aft_skirt_N06-N11.glb).
   - Still to do: the stills from /workspace/aa3_gear/queue_stills.sh, then gltfpack N06-N11 with the in-page load and gearScan checks, then Director's look, then the commit.
3. Detailed ship: the engine ring, aft skirt, flame and lift-off gear are in 0d4a878 and the art/vfx/engine_flame/ files.
   - Still to do: compress the aft_skirt and engine_ring GLBs (after AA3's gear commit), have AA2 fit the Lv1 aft skirt, and make the cockpit window stills (AA2 lv1ship /workspace/pad_fuelline, md5 1042e767).
4. Cargo Dock v4 crane: commit 921f631, GLB c16d8565, dwell store 31.4 s / load 42.0 s.
   - Still to do: render the 375 still and strip (/workspace/dockl/v4/queue_render.sh). Coder needs to wire Truck_Stop_Dock and the dwell timing with the storage branch.
5. Crew roles: f40e327. All crew are male only (Jacob, 1:00 AM 10/25), and the Botanist is waiting on a ruling (see AA's note).
   - Still to do: render the cards, the lineup and the 375 still via art/crew/roles/_src/run_renders.sh with the Botanist left out. The role-kit GLB export can't leave a role out yet.
6. ST-10A Lv10 crawler: check its clearance against the aft skirt, then make game-camera frames (/workspace/st10a/queue_render.sh). Show Director the frames before giving it to Coder.
7. The ladder climb is CANCELLED by Jacob (1:07 AM 10/25). The crew legs clip the cage and each other, and that ships as a known issue.
   - Saved state: hf23e had its reach fix passing (AA3, /tmp/jwcrew and /tmp/hf23src, which are temp folders). AA2's gate is a0584fb. The scratch cages are in /workspace/pad_cage.
   - Don't restart it unless Director asks. When it comes back it gets two tries at most, per Director's rule.

## Box
- The overnight render runner (/tmp/overnight_renders.sh) was stopped at 01:25 to save usage. Nothing heavy is running from me.
- Re-run the queues one at a time: /tmp/ef_queue.sh, the dockl v4 queue, the roles renders, then the st10a queue.

## Open questions for Director
- Lane fix A is BLOCKED (AA2, 01:25; see AA2's note at 30697a4). A crane reach of 16.1 m would put the arm about 1.3 m inside the ship's hull at Hold_Door. Pick one: (a) move the crane base to at least 21.6 m from the ship's centre line (it's 20.0 now), (b) a hold-loading pose that doesn't swing over the ship, or (c) a truck pull-off bay, which needs the S-bend rule waived.
- Refinery bridge: DECIDED. It ships as scenery (looping clips if that's only a few lines), and the box riding comes after the pause.
- Botanist: drop the role, or rebuild it on the male suit?

## 02:05 update
- Crane CLOSED: pad a257d930 kept, z13 lanes kept. f6af441 (1b25bff2) and c0639c1 (903b59ba) parked in launch_pad/_parked_crane/.
- Dock v4 committed 8ca56d1 (GLB c16d8565). Coder wiring; goes to qa3d-next after bridge.
- Gear committed 8c5c7bf (AA3, art/vfx/engine_flame/aft_skirt/, 16 files). Posted to room.
- Cockpit ship committed b8dc5b1 (AA2, launch_pad_game_lv1ship.glb md5 1042e767). Posted to room. Needs ladder cage + gate a0584fb checks.
- Detailed ship = gear + cockpit; Coder must wire (live/ loads no aft_skirt/engine_ring/engine_flame).
- AA2 and AA3 stopped for the night.

## 12:31 update
- Tire-track trails (all truck routes) final try 3 sent to Jacob via Art Manager. Files in /workspace/mine_trail/ (GLB 205f8acb, 1 draw, 70 KB; notracks mine 864fab15, refinery 22f13a9d; pad still e98f89ab). NOT committed; wait for Jacob's OK, then commit + hand Coder (hide HaulRoad/HaulRoad_Tiles, CargoRoad, Road_UTurn; polygonOffset -2/-2, renderOrder 1).
- Known: Mine ruts still subtle, dust band faint.

## 12:38 update
- Trails DONE: Jacob approved (via Art Manager). Final file qa3d-next/models/all_truck_trails_205f8acb.glb, commit 01ff411 (renamed from 6916868). Both managers confirmed this name; Coder uses it. Notracks copies stay uncommitted.
