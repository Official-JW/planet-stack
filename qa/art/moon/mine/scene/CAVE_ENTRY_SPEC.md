# Gate A – cave entry spec (2026-10-22)

Fixes Playtester run-1 item 1 (QA 19:01/19:05): the truck floated over the black mouth at mid-height, shrank in place,
was never behind the rim, and its wheels were not on a tunnel floor.

## Art (locked after this commit)
| file | md5 | notes |
|---|---|---|
| `road-1125.png` | `b75f9a191e24c6ca1db3c037495b78ff` (was `d11cbaf9…`) | repainted ONLY inside x1100–1369, y240–429. Every pixel outside that box is byte-identical to `d11cbaf9` (27,143 px changed, bbox x1100–1340 y280–413). The last road stretch now bends down into the bottom-left of the mouth and runs onto a perspective tunnel floor (vanishing point ≈ (1300,330)) that darkens with depth. The old bottom sill between the jambs is now a lit apron; the edge lamp at (1128,377) moved to (1163,401) so no lamp sits on the road. |
| `cave_rim_overlay.png` | `467248ec20074fc88ba807e895455331` | 1500×488, same canvas as the road. Opaque only on the mouth's arch, hazard bar, lamp, side jambs and the rock just around them, cut pixel-exact from the new road sheet. 1–2 px soft alpha into the opening. The opening interior, the road and the apron are transparent. Replaces the old `tunnel_front_lip` pack sprite (mine_starter, 260×130; loaded but never drawn; `softCaveLip()` is never called) for Gate A. Leave that sprite unused. |

## gateA_centerline.json (new/changed fields only)
- `centerline_px` P9 `(1180,335)` → `(1155,364)`, P10 `(1240,330)` → `(1214,386)` (ends on the tunnel floor, wheel contact). P0–P8 unchanged.
- `cave_floor_px`: `{x:1253,y:361}`: deep wheel-contact point on the floor. Truck total scale here = 0.55× its scale at P10.
- `cave_floor_line_px`: `[{x:1214,y:386},{x:1253,y:361}]`: wheel baseline from the mouth (P10) to the deep point.
- `cave_rim_overlay`: `"cave_rim_overlay.png"`
- `cave_notes`: free text.
- `cave_mouth_rect_px`, `bay_door_rect_px`, `ore_bin_rect_px`, `dump_stop_px`: unchanged.

## Draw order (Mine stop)
1. road sheet `road-1125.png` (drawApprovedYard)
2. truck (drawYardTruck), with **no clip rect** at the cave
3. `cave_rim_overlay.png` drawn right after the truck, in the same parallax transform, at the same place/size as the road sheet. Drawing only the sub-rect x1100–1369, y238–429 is enough.

## Motion
- **C (road out):** follows the centerline to P10. The last stretch dips down off the road into the mouth, and wheels stay on the painted road.
- **D (in, ~3 s):** wheel point moves along `cave_floor_line_px` from P10 to `cave_floor_px`. Yaw eases (first 35 %) from the road heading to the floor-line heading, so you see the rear going away into the hill. Scale goes 1 → 0.55 (total, including scAt). Brightness goes 1 → 0.25 (multiply face shade). Alpha holds at 1, then fades to 0 over the last 45 %. The rim overlay hides the parts behind the arch and jambs.
- **E (hold):** the truck is not drawn. The 180° turnaround happens only here, while hidden.
- **F (out, ~3 s):** exact reverse, nose-first toward camera. `cave_floor_px` → P10, scale 0.55 → 1, brightness 0.25 → 1, alpha 0 → 1 over the first 45 %. Yaw turns to the homebound road heading over the last 35 %. Then G continues home from P10.
- No spin in place anywhere, and no tipping outside the bay.

## Code
`art/moon/mine/cave_entry_gamejs.patch` (against live `qa/game-1905.js`, md5 `8afc1ca6…`). Apply from the repo root: `git apply art/moon/mine/cave_entry_gamejs.patch`.
- bumps `YARD.src` cache key to `?v=b75f9a19`
- reads `cave_floor_px`, `cave_floor_line_px`, `cave_rim_overlay` in `gateABuild` and loads `CAVE_RIM`
- K = `cave_floor_px`, and D/F run along the floor line with shrink/dim/alpha as above (old `clip=G.cave` removed)
- `ROVER_DIM` multiplier on face shade inside `drawRover3D`, set only for the yard truck and reset to 1 after it
- draws the overlay sub-rect after the truck and pour

Proofs: `_proofs_gateA/cave_entry_proof.png` (before vs after, 1:1 crops of headless Chrome @2x) and `_proofs_gateA/road_diffbox_proof.png` (before / after / diff with the allowed box outlined in green).
