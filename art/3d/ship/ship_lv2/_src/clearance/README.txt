SCRATCH clearance for Lv2 (not the game checker).
landing_clear_dh.mjs: copy of the checker; Lv1 landing/kerb/rung/hoop literals raised by DH=3.6 to match the stretched ship.
extend.mjs: makes crew_lv2.glb, adding a periodic 3.0 s climb span per crew (+6 rungs at 1.2 m/s). Run with TIMINGS shifted +3 s.
Lv1+door (DH=0): ALL PASS (proofs/clearance_lv1d.json). Lv2 (DH 3.6, crew_lv2 via extend.mjs, TIMINGS +3 s): ALL 14 PASS incl. other_ship (proofs/clearance_lv2_tall.json).
extend.mjs fix 13:27: gltfpack shares sampler time accessors; the old version extended the shared array once per crew (climb 66.2 s, run hung) -> per-sampler accessors, climb 39.2 s.
The real crew clips need a re-key (+3.0 s climb) before Lv2 ships.
