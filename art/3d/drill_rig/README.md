# Drill Rig: 3D test model v1

- `drill_rig.glb`: final file, meshopt-compressed, no textures. Load it with `GLTFLoader` and `setMeshoptDecoder(MeshoptDecoder)`.
- `build_drill_rig.py`: the source generator for Blender 4.2 LTS. `blender -b -P build_drill_rig.py -- --glb raw.glb [--blend drill_rig.blend] [--render outdir]`, then `gltf-transform prune → dedup → resample → meshopt`.
- `drill_rig.blend`: the generated Blender scene. It includes the render stage (ground, rocks, 1.8 m astronaut), which is not exported.
- `drill_rig_turntable.png`: Cycles proof with 8 angles, a close-up, and the dig and full poses.
- `drill_rig_clips_threejs.png`, `anim/*.gif`: the real GLB playing in three.js.

Nodes: `DrillRig` > `Base` (static pad, legs, collar), `Rig` (shakes in `dig`) > `Mast`, `HeliumStrip`, `StatusLamp`, `Carriage` > `Bit`, `Hopper` > `OreFill`, `HopperLamp`.
Clips: `idle` 2.0 s (slow bit spin, status lamp pulse), `dig` 1.0 s (3 fast bit turns, carriage bobs 0.28 m, rig shake), `full` 1.0 s (bit stopped, status lamp off, amber hopper lamp flashing, ore heaped).
Tip: the code can also show how full the hopper is by moving `OreFill` between its `idle` and `full` heights.
