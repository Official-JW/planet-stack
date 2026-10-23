# Mine A concept masters — generators

Blender 4.2 LTS, headless. Shared helpers in `mc_common.py` (procedural Cycles materials, primitives, lunar stage, sun/sky, 1.8 m astronaut, render + GLB export).

```
blender -b -P concept_a_heavy.py -- --out ../a_heavy_industrial --only glb,blend,turn,hero
blender -b -P concept_b_sleek.py  -- --out ../b_sleek_hightech  --only glb,blend,turn,hero
# --quick 1 = low-res/low-sample preview
```

Both concepts share the same Mine A layout (Blender coords, Z-up, metres):
drill rig (-7.5, 3) → hopper (-1, 3) → conveyor → ore bin (10, 4.5); rover at (1.6, -6.6) digging a glowing He-3 deposit at (8, -6.3); astronaut at (-1.6, -8.2).
Concept B (as picked) swaps the rover for the **HT-04 dump truck** (centre (4.7, -4.5), bed under the conveyor discharge):
drill → hopper → conveyor (discharge chute over the truck bed) → truck hauls on a compacted road loop (x 2–8.5, centre y -2.5)
→ raised dump hopper (5.8, 2.4, above ground — nothing is sunk; only the bore digs in) → lift tube → ore silo. A spur road runs to the He-3 deposit at (11.2, -8.8); a small tap deposit sits at
(7.7, -8.1). The truck's loading arm takes `--arm stow` (default, hero) or `--arm reach`; `--only closeup` renders
`b_dump_truck_closeup_3840x2160.png`. The road is a Stage decal, so it is not in the GLB.
Hero camera (10, -31, 5) → (0, 1.5, 6.6), 24 mm. Turntable: 8 × 45°, 50 m, 22° elevation, target (1, 0.5, 4.5).

These are concept masters (no phone budget). The GLBs carry geometry + base colours only; the procedural shading
(grime, edge wear, hazard stripes, panel lines, glow) lives in the .blend.
Concept C (rugged frontier) is built separately under `c_rugged_frontier/`.
