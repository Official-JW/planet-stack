# Lv10 ship transporter

| concept | status | file | spec |
|---|---|---|---|
| **A: tracked crawler** | **ACTIVE**: picked by the Director on 10/24/2026 | `game/st10a_game.glb` | `SPEC_A.md` |
| B: wheeled straddle | **SHELVED**: kept in git at 7bd022c for reference only, don't hand it off | `game/st10b_game.glb` | `SPEC.md` |

- **Transport road v5** (10/24 station order, Coder tag d729465: Cargo Space Dock 480 | Launch Pad 640 | Shipyard 800): `game/st10a_transport_road.glb` (vertex-colour crawler-track road, one mesh; place at world (669.5, 0, −13), no rotation). Plan + clearance: `proofs/transport_road_plan.json` from `_src/road_plan_v5.py`, check from `_src/road_v5.py` (real station triangles from `_src/export_tris_v5.mjs`, footprints `_src/measure_stations_v5.mjs`), mesh from `_src/build_road_v5.py`. Path: pad pick-up (640, −13) → straight +X out of the pad's right side on the far side → one right arc R 100 m / 40° → Shipyard Road_Entry (754.871, 0.23, 17.604); 123.03 m, no S-bend. The v4 plan (`_src/road_plan.py`, pad 457) is superseded.
- Cradle and aft-skirt clearance check: `_src/clearance_st10a.py`, output in `proofs/clearance_st10a.json`.
- Game-cam shade proofs for A (`proofs/gamecam_a_game/`) and the road plan v5 top-down PNG (`_src/road_plan_v5.py --png`) are **queued, not rendered** (box hold). The queue script is `/workspace/st10a/queue_render.sh`; it runs under `flock /tmp/planet_stack_heavy.lock nice -n 19`.
