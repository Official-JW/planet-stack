# Lv10 ship transporter

| concept | status | file | spec |
|---|---|---|---|
| **A: tracked crawler** | **ACTIVE**: picked by the Director on 10/24/2026 | `game/st10a_game.glb` | `SPEC_A.md` |
| B: wheeled straddle | **SHELVED**: kept in git at 7bd022c for reference only, don't hand it off | `game/st10b_game.glb` | `SPEC.md` |

- Transport road plan (pad → Shipyard), re-based on the approved station table and sized for crawler A: `proofs/transport_road_plan.json`, made by `_src/road_plan.py`, which reads `_src/road_clearance.json` from `_src/road_clearance.mjs`.
- Cradle and aft-skirt clearance check: `_src/clearance_st10a.py`, output in `proofs/clearance_st10a.json`.
- Game-cam shade proofs for A (`proofs/gamecam_a_game/`) and the road plan top-down PNG are **queued, not rendered** (box hold). The queue script is `/workspace/st10a/queue_render.sh`; it runs under `flock /tmp/planet_stack_heavy.lock nice -n 19`.
