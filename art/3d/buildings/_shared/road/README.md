# Shared haul-road segment (Mine → Refinery), for Game Coder

`haul_road_seg.glb`: **16,540 B**, md5 `b3c636f90b06e1c50c8f2edda37e68e3`, **2,240 tris, 1 mesh / 1 draw** (v2 10/23 PM tyre-track trail; v1 was 4,100 B / 280 tris).
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
- **Station spacing is 160 m (20 segment lengths); the bare gap is exactly 88 m = 11 full tiles:**
  - The Mine's stub ends at Mine-local x **26** (both lanes, z +9 and z 0) → world **186**.
  - The Refinery's RD-1 road starts at Refinery-local x **−46** (= `Truck_Path_01` / `Truck_Exit`) → world 320 − 46 = **274**.
- **Fill: 11 copies, scale 1, at x = 186 + 8·k (k = 0…10)**, covering 186…274 exactly. No partial tile, no overlap with either station road.
  - Don't lay 20 copies over the whole 160 m: they would z-fight with RD-1 and the Mine stub.
- Lanes line up with both stations: the inbound z +9 matches the Mine stub and the Refinery's Truck_Path_01/02, and the outbound z 0 matches the Mine's
  z 0 return lane and the Refinery's Truck_Exit / Road_Exit.

## Drive timing (Lv1): 12 s each way, eased start and stop
- **Loaded run:** from Mine `Road_Entry` (Mine-local (13.5, 0, 9), world x 173.5) to Refinery `Truck_Path_01` (Refinery-local (−46, 0, 9), world x 274). That is **100.5 m** along z +9, heading +X.
- **Return run:** from Refinery `Truck_Exit` (−46, 0, 0) to Mine `Road_Entry`, **100.5 m**, heading −X. It runs on z 0 all the way, onto the Mine's z 0 return lane (no lane change).
- **Velocity profile:** use a trapezoid with 1.5 s ease-in and 1.5 s ease-out (smoothstep on speed) and a 9 s cruise.
  - Cruise speed is v = 100.5 / (12 − 1.5) = **9.57 m/s** (about 34 km/h), with peak acceleration about 6.4 m/s².
  - Or use a single easeInOutSine over 12 s, which peaks at about 13.2 m/s.
- **Wheel spin** (HT-04 rolling radius 0.853 m): 11.2 rad/s at cruise. Use `angle += distance / 0.853`. Play `truck_drive` as a loop while moving.

## Seams at both joins (fixed 10/23: Mine `219e774`, Refinery `bb5eed2`)
Both station roads now ease into the strip's x 0 / x 8 cross-section and colours over their last metres, so the joins are flush on the game's flat y 0 ground.
Checked by sampling the decoded GLBs at the join (Mine x 25.99, Refinery x −45.99) on both lanes: surface 0.045, crown 0.065, tracks (±1.45) 0.026,
berm crest 0.293, toe (±2.8) −0.039, all within 2 mm of the strip; widths 4.0 m surface, toes ±2.8, tracks ±1.45 on both sides.
Track colours match the strip's end rows exactly: z +9 #797c81 / #7d8085, z 0 #7d8085 / #7a7d82; crown #a6a9ae (z +9) / #a4a7ac (z 0).

| join | before | after |
| --- | --- | --- |
| Mine x 26, z +9 | stub followed the terrain: y +0.40 at x 20, −1.2 at x 24, **−1.97** at x 26 (sank below the ground) | flush (eases to y 0 over x 17–22, profile/colour over x 21–25) |
| Mine x 26, z 0 | crossfall tilted **+0.82 / −0.80 m** across the lane | level, flush |
| Mine both lanes | tracks #6a6e73 (darker than the strip), surface 0.065 on z 0 | strip colours, surface 0.045 |
| Refinery x −46, z +9 | surface 0.025 vs 0.045 (**2 cm step**), tracks at 0.009, #8d9094 | flush, strip colours (ease over x −34 → −46) |
| Refinery z 0 / z +9 | road ran to x −48: **2 m overlap** with the last tile (z-fighting on z 0) | road trimmed to start at x −46 |

## Proof
- `haul_road_seams_proof.png` (2358×1326, Cycles CPU 16 samples, no denoiser, flat `M_ground` at y 0, real spacing: Mine at 160, 11 tiles at 186 + 8k, Refinery at 320, Tier_ meshes hidden; rendered 10/23 PM with the redesigned Mine):
  top-down and low oblique of the Mine join (world 186) and of the Refinery join (world 274). No step, gap or z-fighting at either join and the lane, crown and
  track colours carry through. One cosmetic difference: on the Mine side a thin darker band along each outer berm toe stops at the join (toe shading, ~0.3 m wide, top-down only).
- `haul_road_proof_1179x663.png` is the older pulled-in proof (before the seam fix: Mine stub dipping, Refinery at 24 m); kept for history.

## Rebuild
```
blender -b -P _src/build_haul_road_seg.py -- --out /tmp/road_raw.glb
gltfpack -i /tmp/road_raw.glb -o haul_road_seg.glb -cc -kn -ke -vpf
# proof: unpack the GLBs first (gltfpack -noq -kn -ke; Blender has no meshopt decoder)
blender -b -P _src/proof_road_tiles.py -- --mine mine_plain.glb --ref refinery_game_plain.glb --seg seg_plain.glb \
    --out haul_road_proof_1179x663.png --w 1179 --h 663 --samples 48 --cam 40,-28,18 --tgt 40,-4.5,0 --lens 24
# seam proof (real spacing, both joins): writes mine_top / mine_low / ref_top / ref_low, then composite 2x2
blender -b -P _src/proof_seams.py -- --mine mine_plain.glb --ref refinery_game_plain.glb --seg seg_plain.glb --outdir /tmp/seams --samples 16
```

## v2 look (10/23 PM, Jacob: "make the truck path more like tire track trails with better texturing")
- Two dark compacted wheel ruts per lane with **tread chevrons** in vertex colour (rut rows every 0.19 m = half the HT-04 tread pitch, alternating dark/light, rut centre row shifted 0.09 m so each band reads as a V pointing the lane heading).
- Dusty, lighter scuffed berms and shoulders, compacted crown, low-frequency 8 m-periodic colour variation; 92 low pebbles (≤ 7 cm proud, max y 0.30, ≥ 0.4 m from both ends, never on the ruts).
- Still flat and still ≤ 0.30 m (POSITION y −0.040…0.300), so it stays out of the framing band check.
- **Seams unchanged:** the cross-section heights are v1's and the x 0 / x 8 rows carry exactly the v1 positions and colours (checked on the decoded GLB: 60/60 end vertices identical; 8 extra rut-centre end vertices sit on the same −2 cm line with the average rut colour), so the Mine x 26 and Refinery x −46 joins stay flush.
- The station roads themselves (Mine stub in mine_game.glb, Refinery RD-1) still have the v1 look; the chevron rows would add ~1–2k tris to stations at their budgets, so that is a follow-up.
- Proofs: `proofs/haul_road_before_393x852.png` / `proofs/haul_road_after_393x852.png` (game camera, with both trucks), `proofs/haul_road_before_close_1600x900.png` / `proofs/haul_road_after_close_1600x900.png`.


## Station roads (10/24 00:40)
`_src/paint_station_roads.py mine|refinery IN_plain OUT_raw [--skin-merge A,B]` paints this segment's rut / tread / dust palette onto the roads already inside `mine_game.glb` and `refinery_game.glb` (vertex colour only; lane centre lines and rut columns per station in the script). Tread only reads where the station road rows are ≤ 0.6 m apart; see the Mine and Refinery READMEs.

## Mine straights tread resample (10/24 01:00)
`_src/resample_mine_ruts.py IN_plain OUT_plain` (unpacked GLB): conforming splits of the Mine's `Base_Paint` longitudinal road edges on the visible rut rows so rows are ≤ 0.6 m apart, then `paint_station_roads.py` paints the tread. Mine: +550 tris, 0 draws.
