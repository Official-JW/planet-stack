# Game Coder - restart notes (10/25/2026 1:20 PM PT)

## Where things stand
- origin/main = 7f55a03. qa3d-next has served it since 1:15:29 PM PT: main.js ab601737c57f1601611674222b38bdaa, index.html 57b9f59a0dfa0bea8892e7b0d0a0df32, label "QA3D-next · 12:45".
- What it contains: the pad camera (rest/load fit, Aft_Skirt_Seat attach with the thick skirt), the Lv1 launch VFX (Art a422b9c/f87f42f, loaded from art/vfx/lv1_launch/), bridge cargo (c961698), tire-track trails (TRAIL_GLB all_truck_trails_205f8acb, old roads off, ?trail=off restores them), and the no-track Mine/Refinery (mine_864fab15, refinery_22f13a9d, camera overrides re-keyed).
- live/ = f265aaf code with the 815a287 LIVE tag. None of the above is on live/ yet.
- Working branch: /workspace/ps-padcam (gc-padcam), clean, at 7f55a03.

## Known issues
- Bridge crane: the flatbed crane lifts each crate from the turntable while its box is still crossing the bridge, on every trip. The bridge boxes are display only, and credit and Dock timing are unchanged. Parked: Director's one-try fix wasn't possible without moving the Dock chain (the lift at main.js c.rc is what loads the flatbed).
- The faint Mine trail at phone size is an art issue, with no code workaround.
- Scene-wide draws are around 28 to 34 a frame. Pad assets at launch are 13 (cap 15). No culling work until Director says so.

## Held / parked
- a2c81f4 (ps-baylabel, ?dockfill=N): parked, don't push.
- Ship live copy (/workspace/ps-live-ship, gc-live-ship 9fca764): held for Jacob's art.

## Next (queued, don't start until EM says)
- Crew boarding with AA3's access tower (lift car + arm, crew_tower.glb, final hash with the plate pass). Jacob approved the tower and the top door near the nose (via Art Manager, 12:53). Load it next to pad 5fcd4d67 and play the lift/arm/hatch clips. Move lift-off back about 3 s so it waits for the arm (VFX ignition moves with it). The camera follows the lift car, then C1_Hips. Separate local commit. Not for live/ until Jacob approves the animation and QA's quick check passes.
- Possibly the hull middle door removal (art side).

## Rules I follow
- Push only on EM's "push now". Commit name "mm/dd/yyyy - planet-stack - HH:MM" PT, author and committer Game Coder via -c. Explicit paths only, never art/ or the qa3d WIP files. Merge only. Kill only my own PIDs (not ports 8731/18931). No headless browser while testers are active. Two tries per fix.
- Tools: /workspace/padcam_work (padfit, roadchk, routecheck, drawcount, sweep3, truegap).

## Live status (10/25/2026 13:35 PT)
- live/ serves 6df2e40 (trails commit 6920b45 merged with 0f46d3f), on Pages since 13:35:07. live/main.js 214a66a8aaa2d2ec7cb4db92cd39eb77, live/index.html 1877e39edacaf3a28d65a532b861b042, tag LIVE · 13:22.
- That is 49f9def (live copy 44623ca, 13:20:28) plus the 7f55a03 trails: all_truck_trails_205f8acb, mine_864fab15, refinery_22f13a9d, camera keys and road hiding. Save key planetstack-live.
- Known issues: the nose is cut off under the Eve banner in the load camera; the flatbed crane lifts each crate while its box is still on the bridge; the old ladder climb is still in use; the Mine trail is faint.
- Boarding (access tower) is PARKED. No @Jacob notes: Director tells Jacob.
