# Shared haul-road segment (Mine → Refinery), for Game Coder

`haul_road_seg.glb`: **4,100 B**, md5 `661e358273159d7768be39fcf8f3ee5a`, **280 tris, 180 verts, 1 mesh / 1 draw**.
- Material `SHM_Paint` (pbrMetallicRoughness only, roughness 0.42). Colours are in vertex colours (COLOR_0) only.
- No textures or images, and no transmission, clearcoat or ior.
- Packing: `EXT_meshopt_compression` + `KHR_mesh_quantization` (`gltfpack -cc -kn -ke -vpf`: float positions so the ends sit exactly at x 0 and 8.0; normals and colours quantized), no Draco.
- Node `HaulRoad_Seg` carries extras: `tile_len_m` 8.0, `axis` +X, `origin`, `lanes`, `tiling`, `surface_y`.

## Geometry (glTF, metres, y up)
- **One 8.0 m piece along +X**, from x 0 to exactly x 8.0 (verified in the packed file: POSITION min x 0, max x 8).
- **Two lanes:**
  | lane | centre line | heading | width (toe to toe) |
  | --- | --- | --- | --- |
  | **inbound** (Mine → Refinery) | **z +9** | +X | 6.2 … 11.8 |
  | **outbound** (Refinery → Mine) | **z 0** | −X | −2.8 … 2.8 |
  - There is 3.4 m of bare ground between the two berm toes.
- **Cross-section of each lane** (offset from the centre line → height y):
  - **Running surface:** 4.0 m graded, y 0.045, crown +2 cm (y 0.065).
  - **Tyre tracks:** worn bands 0.4 m wide at ±1.25…1.65 m (centred ±1.45, like the Mine stub). They sit 2 cm below the surface and are darker, with an 8 m periodic scuff pattern.
  - **Foot** at ±2.0. **Graded berm** crest at ±2.35, +25 cm above the surface (y 0.295). **Toe** buried at ±2.8 (y −0.04).
- **Colours:** the station roads' own palette:

  | part | colour |
  | --- | --- |
  | surface | `#a4a7ac` |
  | tracks | `#878a8f`, worn toward `#76797e` |
  | crown polish | toward `#adb0b5` |
  | foot | `#9da0a5` |
  | crest | `#939499` |
  | toe | `#82858a` |
- **Tiling:** put copies at `position = (x0 + 8·k, 0, 0)` with no rotation and scale 1.
  - The x 0 and x 8 rows are identical in position and colour, and were checked after quantization, so copies join with no seam.
  - Uniform `scale.x` also tiles cleanly; see below.

## Placing it between the Mine and the Refinery (GAP = 160 m, Mine = station index 1 at x 160)
- **Station spacing is 160 m (20 segment lengths), but the bare gap is only 86 m:**
  - The Mine's stub ends at Mine-local x **26** (Mine README, lane z +9).
  - The Refinery's RD-1 road starts at Refinery-local x **−48** (Truck_Path_01 / Road_Entry at −46).
  - So the gap runs from world x 160 + 26 = **186** to 320 − 48 = **272**, which is **86 m**.
- **Recommended fill:** **11 copies with scale.x = 86/88 = 0.97727**, at x = 186 + 7.8182·k (k = 0…10). That covers 186…272 exactly, with no overlap or z-fighting with the station roads.
  - Alternatively, use 10 full copies (186…266) plus one copy at scale.x 0.75 (266…272).
  - Don't lay 20 copies over the whole 160 m: they would z-fight with RD-1 and the Mine stub.
- Lanes line up with both stations: the inbound z +9 matches the Mine stub and the Refinery's Truck_Path_01/02, and the outbound z 0 matches the Refinery's Truck_Exit / Road_Exit.

## Drive timing (Lv1): 12 s each way, eased start and stop
- **Loaded run:** from Mine `Road_Entry` (Mine-local (13.5, 0, 9), world x 173.5) to Refinery `Truck_Path_01` (Refinery-local (−46, 0, 9), world x 274). That is **100.5 m** along z +9, heading +X.
- **Return run:** from Refinery `Truck_Exit` (−46, 0, 0) to Mine `Road_Entry`, **100.5 m**, heading −X. It runs on z 0; the Mine's matching z 0 return lane is coming (until then, merge to z +9 near the Mine end; see the caveats).
- **Velocity profile:** use a trapezoid with 1.5 s ease-in and 1.5 s ease-out (smoothstep on speed) and a 9 s cruise.
  - Cruise speed is v = 100.5 / (12 − 1.5) = **9.57 m/s** (about 34 km/h), with peak acceleration about 6.4 m/s².
  - Or use a single easeInOutSine over 12 s, which peaks at about 13.2 m/s.
- **Wheel spin** (HT-04 rolling radius 0.853 m): 11.2 rad/s at cruise. Use `angle += distance / 0.853`. Play `truck_drive` as a loop while moving.

## Known mismatches at the Mine end (not fixed here; mine/ is owned by another agent)
1. **Height.** The Mine GLB's stub, measured on the committed `mine_game.glb` along its centre line z +9, is not at ground level all the way to x 26:
   | Mine-local x | 12–17 | 19.8 | 22.9 | 26.0 |
   | --- | --- | --- | --- | --- |
   | y | ≈ 0.0 | +0.40 | −0.53 | **−1.97** |
   - It follows the Mine's own terrain. On the game's flat y 0 ground plane, the last ~5 m sink below the ground, which leaves a visible step or gap at the junction (see the proof).
   - The Mine stub needs to be flattened to y ≈ 0.045 from x 17 to 26.
2. **Return lane (in progress at the Mine).** Both lanes stay: inbound z +9, outbound/return z 0 (Coder, 10/23 12:24). The Mine is adding a matching
   z 0 return lane; until it lands, the Mine stub only has the z +9 lane, so the return truck needs a short z 0 → z +9 merge on the last segment.
   Once the Mine's z 0 lane is in, the return run is straight along z 0 with no lane change.
3. **Colour step at the Refinery end.** RD-1 at the Refinery start shows a slight colour step; its tracks are fainter. Positions and lanes match.

## Proof
- `haul_road_proof_1179x663.png`: 1179 px wide, Cycles, flat `M_ground` at y 0. Left to right it shows the Mine stub end at x 26 (dipping below ground, mismatch 1), **3 tiled segments** at x 26 / 34 / 42, and the Refinery's RD-1 road start at x 50.
  - For the proof the Refinery is pulled in to 24 m so all three join on screen; in the game the gap is 86 m.
  - The Refinery's Tier_ meshes are hidden.
  - The segment-to-segment joins are invisible.

## Rebuild
```
blender -b -P _src/build_haul_road_seg.py -- --out /tmp/road_raw.glb
gltfpack -i /tmp/road_raw.glb -o haul_road_seg.glb -cc -kn -ke -vpf
# proof: unpack the GLBs first (gltfpack -noq -kn -ke; Blender has no meshopt decoder)
blender -b -P _src/proof_road_tiles.py -- --mine mine_plain.glb --ref refinery_game_plain.glb --seg seg_plain.glb \
    --out haul_road_proof_1179x663.png --w 1179 --h 663 --samples 48 --cam 40,-28,18 --tgt 40,-4.5,0 --lens 24
```
