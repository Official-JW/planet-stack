# Cycles close-ups, v3 cleared set (10/24/2026)

Blender 4.2.3, Cycles CPU, 64 samples + OIDN, AgX Medium High Contrast, 3840x2160, rendered with render_truck_proof.py.
GLBs unchanged: ht04_game.glb md5 4222799b..., mine_game.glb ef45f6f1..., haul_road_seg.glb b3c636f9... (unpacked with gltfpack -noq for Blender).
The SHM_DepositGlow cracks use their own glTF base + emissive factors (strength 1), not the proof #2fe3ff x6 glow.

- props/ht04/proofs/ht04_ore_v3_closeup_3840x2160.png: --glb mine.glb --glb ht.glb@11,9,0 --fill 1 --anim chute_pour@18 --cam 35,40,7.5,7.6,2.4,10.6 --lens 30
- buildings/mine/proofs/mine_deposits_v3_closeup_3840x2160.png: --glb mine.glb --glb ht.glb@11,9,0 --fill 1 --cam 20,45,9,1.2,0,11.5 --lens 30
- buildings/_shared/road/proofs/haul_road_tread_closeup_3840x2160.png: --road seg.glb --road_tiles 0,6,0 --glb ht.glb@14,9,0 --glb fb.glb@24,0,180 --fill 1 --cam 20,32,24,18,0.8,4.5 --lens 35

Measured (sRGB): heap mean about (97,98,96); deposits (109,113,113) and (121,124,126) against the proof ground (137,142,147); cracks about (146,203,216).
