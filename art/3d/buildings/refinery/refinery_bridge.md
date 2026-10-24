# CV-3 Refinery Box Bridge — `refinery_bridge.glb`

A truss gantry over the RD-1 haul trails at the Refinery. It carries an enclosed box conveyor that delivers cargo boxes to the RC-1 crane pickup table, where the crane loads them onto FB-05.

This file stands on its own. Do not merge it into `refinery_game.glb`.

## Placement
- The root node `Refinery_Bridge` is **already at Refinery-local (-22, 0, 4.8), yaw 0**.
- Parent the GLB scene to the Refinery root with **no extra offset**. In world terms that is (298, 0, 4.8) when the Refinery station sits at (320, 0, 0).
- Bridge axes are the same as Refinery axes. The span runs along +Z, south tower at z -4.6 and north lowerator at z 14.2. The pickup station sits on the +X side (Cargo Dock / Launch Pad side).
- Footings are outside both truck lanes:
  - South: x -23.95..-20.05, z -6.55..-2.65.
  - North: same x, z 12.25..16.15.
  - Chute and table: x -20.65..-16.5, z 13.05..15.35. This stays clear of the crane pad (x ≥ -18.15 for the table edge) and the flatbed road (x ≥ -13).
- Clearance: the deck underside is at **y 7.2**. HT-04 with its bed raised reaches 5.75, plus 1 m gives 6.75, so there is 0.45 m spare.

## Crane pickup
- `Pickup_Point` is the box base on the table:
  - Refinery (-18.3, 1.0, 14.2)
  - World (301.7, 1.0, 14.2)
  - Crane-local (-9.3, 1.0, -3.3)
- Box yaw is 0 (long axis +X), which matches the RC-1 hook convention.
- RC-1 solve: θ 2.8006 rad, r 9.868 m, L 6.2 m. All within limits.
- Other path markers: `Box_Infeed`, `Bridge_Entry`, `Bridge_Exit`, `Lowerator_Bottom`. Each has `refinery_xyz` in its extras.

## Clips
- **`box_convey`**, 33.0 s loop. Three cargo boxes, each 11 s apart, at 1.5 m/s with 1.0 s eased starts and stops. Timeline for one box:
  - 0–5.61 s: lift up the south shaft.
  - 5.61–19.14 s: cross the bridge.
  - 19.14–24.61 s: lowerator descent.
  - 24.61–25.81 s: turntable yaw 90°→0°.
  - 25.81–29.29 s: down the chute, arriving at the pickup.
  - 29.29–32.29 s: dwell at the pickup.
  - Then the box is hidden (scale 0.001) until its next cycle.
  - Coder: once RC-1 latches, hide the bridge box (or start the crane cycle on arrival at 29.29 s plus box offset) so the crane carries the visible copy.
- **`roller_spin`**, 0.4 s loop. 44 roller bones (`Roller_B##` along the bridge, `Roller_T##` on the chute and table), about 1.4 m/s surface speed. Play it alongside box_convey.

## Budget
- 5462 tris, 4 draws: `Bridge_Static` and `Bridge_Moving` with SHM_Paint + SHM_GlowCyan each.
- 94,880 B.
- Extensions: KHR_mesh_quantization and EXT_meshopt_compression only. No Draco, images, transmission, clearcoat or ior.

## Safe band (Refinery camera, Cam_Target (313.1, 2.08, 13.55), frame_w 37.5)
Bridge over all clip samples:
- 393×852: top 122.4, bottom 81.6, left **13.3**, right 298.9 px.
- 375×667: top 60.1, bottom 24.2, left **11.0**, right 285.1 px.

Union with the Refinery and crane:
- 393: left 13.3, top 64.2, bottom 72.5, right 22.9.
- 375: left 11.0, top 10.2, bottom 15.3, right 29.1.

Every value is ≥ 5 px. The bridge is now the left-edge binder.

## Source
- Build: `blender -b -P _src/build_bridge.py -- raw.glb [--box /tmp/cargo_box_plain.glb]`. Make the box input with `gltfpack -i art/3d/props/cargo_box/cargo_box_game.glb -o /tmp/cargo_box_plain.glb -noq -kn -ke`.
- Pack: `gltfpack -i raw.glb -o refinery_bridge.glb -cc -kn -ke -af 10`.
- Proofs: `_src/render_bridge_proofs.py`. The outputs are `proofs/refinery_bridge_393x852.png`, `_375x667.png`, `_before_after.png` (before / after 393 / after 375, with band lines) and `_closeup_4k.png`.

The camera looks along the span end-on, so the north lowerator is an open frame. That lets the span and the boxes dropping and turning show through it.
