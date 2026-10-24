# CV-3 Refinery Box Bridge — `refinery_bridge.glb` (v2)

A truss gantry that crosses the RD-1 haul trails at a 32° diagonal. It carries an enclosed box conveyor from a south lift tower (process side) to an open lowerator in the flatbed median. From the lowerator, a short roller chute takes each box to the RC-1 pickup table, where the crane loads it onto FB-05.

Seen from the Refinery camera, the span runs from upper-left to lower-right. Boxes come **down on screen-right**, toward the Cargo Dock and the crane.

This file stands on its own. Do not merge it into `refinery_game.glb`.

## Placement
- The root node `Refinery_Bridge` is **already at Refinery-local (0.24, 0, 5.83), yaw 0**.
- Parent the GLB scene to the Refinery root with **no extra offset**. In world terms that is (320.24, 0, 5.83) when the Refinery sits at (320, 0, 0).
- Bridge axes are the same as Refinery axes. Inside the GLB the span is yawed 32°:
  - South tower centre: Refinery (-6.90, -5.6).
  - Lowerator centre: (7.0, 17.5).
  - Tower to tower: 26.96 m. Truss: 24.99 m.
- Footprints (Refinery x/z):
  - South tower footing: x -9.59..-4.22, z -8.29..-2.91. This is outside the outbound trail toe at z -2.8.
  - Lowerator footing: x 5.4..8.6, z 15.9..19.1. This is inside the flatbed median (z 15.8..19.2).
  - Chute and pickup slab: x -1.3..5.8, z 16.35..18.65 (median). The lamp and control box reach z ≤ 19.06.
- The span crosses these lanes at deck height:
  - RD-1 outbound z 0, which includes the HT-04 tipping at Truck_Dump.
  - The U-turn.
  - Inbound z 9.
  - Flatbed lane E z 13.
- Clearance:
  - The lowest bridge vertex over any lane is **y 7.22**. The deck underside is 7.2 and the CLR plates sit on the chord face.
  - HT-04 with its bed raised reaches 5.75, plus 1 m gives 6.75 required, so the spare is ≥ 0.45 m.
  - A sweep of every clip sample found no bridge vertex below y 6.75 inside any lane.

## Crane pickup (RC-1 at world (311, 0, 17.5))
- `Pickup_Point` is the box base on the table:
  - Refinery (0.3, 1.0, 17.5)
  - World (320.3, 1.0, 17.5)
  - Crane-local (9.3, 1.0, 0)
- Box yaw is 0 (long axis +X, label +Z).
- RC-1 solve: θ 0, r 9.3 m (trolley range 2.6–10.3), L 6.2 m. **This is within reach, so nothing has to move.** The pickup is on the screen-right side of the crane. The swing to the FB-05 bed (θ about 0.66) does not cross the span.
- Every bridge part above y 3 is ≥ 12.39 m from the mast, outside the 11.25 m jib-tip radius. Inside that radius there are only the low table, chute, end stop, lamp (top y 2.53) and control box, all under the hook path.
- Path markers: `Box_Infeed`, `Bridge_Entry`, `Bridge_Exit`, `Lowerator_Bottom` and `Pickup_Point`. Each has `refinery_xyz` in its extras.

## Clips
- **`box_convey`**, 41.0 s loop. Three cargo boxes, each 13.667 s apart, at 1.5 m/s with 1 s eased starts and stops. Timeline for one box:
  - 0–5.61 s: rise, hidden in the south shaft.
  - 5.61–24.58 s: cross the bridge.
  - 24.58–30.04 s: drop in the open lowerator.
  - 30.04–31.24 s: turntable yaw -58°→0°.
  - 31.24–36.71 s: run west down the chute to the pickup.
  - 36.71–39.71 s: dwell.
  - Then the box is hidden (scale 0.001) from 39.76 s.
  - Coder: once RC-1 latches, hide the bridge box (or start the crane cycle on arrival at 36.71 s plus the box offset).
- **`box_path`**, 36.8 s, no loop. A single box (Box_1, scrubbable): set time = progress × duration. It uses the same event times as box_convey and ends on `Pickup_Point` at yaw 0. Box_2 and Box_3 are scaled to 0.
- **`roller_spin`**, 0.4 s loop. 38 roller bones (`Roller_B##` along the span at 1.2 m pitch, `Roller_T##` on the chute and table at 0.4 m pitch), about 1.4 m/s surface speed. Play it with either box clip.

## Budget
- 5,888 tris, 4 draws: `Bridge_Static` and `Bridge_Moving` with SHM_Paint + SHM_GlowCyan each.
- 100,068 B.
- Extensions: KHR_mesh_quantization and EXT_meshopt_compression only. No Draco, images, textures, transmission, clearcoat or ior.

## Safe band (Refinery camera, Cam_Target (313.1, 2.08, 13.55), frame_w 37.5)
Bridge over all clip samples:
- 393×852: top 120.2, bottom 71.5, left 157.7, right **21.3** px.
- 375×667: top 58.6, bottom **14.4**, left 151.7, right 18.5 px.

Union with the Refinery and crane (rest):
- 393: top 64.2, bottom 71.5, left 78.1, right 21.3.
- 375: top 10.2 (Refinery), bottom 14.4 (bridge), left 73.4, right 18.5.

Every value is ≥ 5 px.

## Source
- Build: `blender -b -P _src/build_bridge.py -- raw.glb [--box /tmp/cargo_box_plain.glb]`. Make the box input with `gltfpack -i art/3d/props/cargo_box/cargo_box_game.glb -o /tmp/cargo_box_plain.glb -noq -kn -ke`.
- Pack: `gltfpack -i raw.glb -o refinery_bridge.glb -cc -kn -ke -af 10`.
- Proofs: `_src/render_bridge_proofs.py` (`--clip box_convey|box_path`, `--phone` for the game camera).
  - `proofs/refinery_bridge_393x852.png` and `_375x667.png`: box_convey at t 31 s, with cyan band lines.
  - `_before_after.png`: 393 and 375, before and after, 2× size.
  - `_closeup_4k.png` is **still the v1 image**. The v2 4K close-up is queued until the shared box is free.
