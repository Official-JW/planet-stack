# Flatbed road, Refinery → Launch Pad (layout doc, no new mesh)

The flatbed road is built from the shared 8 m road tile `art/3d/buildings/_shared/road/haul_road_seg.glb` (4,100 B, md5 `661e358273159d7768be39fcf8f3ee5a`, 280 tris, 1 draw). I only use it here and don't modify it. This road is **separate from the haul lanes at z 9 / z 0**.

## Lanes (Director layout, world coordinates; Refinery x 320, Launch Pad x 480)
| Lane | World centre line | Heading | Toe-to-toe | From the tile |
|---|---|---|---|---|
| Eastbound (Refinery → Launch Pad) | **z 13** | +X | z 10.2 … 15.8 | tile lane z 0 |
| Westbound (Launch Pad → Refinery) | **z 22** | −X | z 19.2 … 24.8 | tile lane z +9 |
| Median (crane + pallet) | z 15.8 … 19.2 (centre 17.5) | — | 3.4 m bare ground | — |

The tile's own extras call its lanes inbound/outbound (Mine haul road). Ignore those labels here: the tile has no direction markings, so either lane can run either way.

Each lane is a 4 m running surface (y 0.045, crown 0.065) with tyre tracks at ±1.45, berm crests at ±2.35 (y 0.295) and toes at ±2.8.

## Tiles: `position = (x, 0, 13)`, no rotation; covers world x 307 … 481
| k | position | scale.x | world x |
|---|---|---|---|
| 0 | (307, 0, 13) | 1 | 307…315 |
| 1 | (315, 0, 13) | 1 | 315…323 |
| 2 | (323, 0, 13) | 1 | 323…331 |
| 3 | (331, 0, 13) | 1 | 331…339 |
| 4 | (339, 0, 13) | 1 | 339…347 |
| 5 | (347, 0, 13) | 1 | 347…355 |
| 6 | (355, 0, 13) | 1 | 355…363 |
| 7 | (363, 0, 13) | 1 | 363…371 |
| 8 | (371, 0, 13) | 1 | 371…379 |
| 9 | (379, 0, 13) | 1 | 379…387 |
| 10 | (387, 0, 13) | 1 | 387…395 |
| 11 | (395, 0, 13) | 1 | 395…403 |
| 12 | (403, 0, 13) | 1 | 403…411 |
| 13 | (411, 0, 13) | 1 | 411…419 |
| 14 | (419, 0, 13) | 1 | 419…427 |
| 15 | (427, 0, 13) | 1 | 427…435 |
| 16 | (435, 0, 13) | 1 | 435…443 |
| 17 | (443, 0, 13) | 1 | 443…451 |
| 18 | (451, 0, 13) | 1 | 451…459 |
| 19 | (459, 0, 13) | 1 | 459…467 |
| 20 | (467, 0, 13) | 1 | 467…475 |
| 21 | (475, 0, 13) | **0.75** | 475…481 (partial tail; uniform scale.x tiles cleanly) |

That's 22 instances (21 full tiles plus one 0.75 tile), 6,160 tris and 22 draws if they aren't merged. Instancing or merging is Coder's call.

## Loading spot
FB-05 loads at **world x 318** on the eastbound lane: FB-05 root (318, 0, 13), heading +X = crane `Truck_Park`. The RC-1 crane root and its 8-box pallet sit in the median at **(318, 0, 17.5)** (see `../crane_refinery/README.md`). The pedestal footprint (x 316.3…319.7, z 15.8…19.2) exactly fills the median between the berm toes. The truck (half-width 1.9) clears it by 0.9 m.

## Collision check against the station GLBs (vertex level, reported only, nothing moved)
I tested `refinery_game.glb` at +320 and `launch_pad_game.glb` at +480 for any vertex above y 0.12 inside x 307…481 for the lane E corridor (z 10.2…15.8), the median (15.8…19.2) and lane W (19.2…24.8). I also tested the crane slew envelope (r < 11.25 around (318, 17.5), y 9.3…10.9).
- **Refinery:** the RD-1 inbound-lane berm/toe (haul lane z 9, toe to z 11.8) reaches into the eastbound flatbed corridor at **x 308…319.4, z 10.4…11.4, up to y 0.28**. The two roads' berm toes overlap there by ~1.6 m (z 10.2…11.8). Nothing from the Refinery is in the median, lane W or the crane envelope (Refinery max z 11.8).
- **Launch Pad (from x ≈ 453):**
  - lane E: structures/berm at x 453.6…467.8, z 10.2…15.7, up to **y 3.7**; low apron at x 472…481, z 10.3…13.6, y ≤ 0.37;
  - median: x 456.4…462.5, z 15.8…18.3, y 1.22;
  - lane W: x 464.8…466.3, z 20.2…23.7, y 1.15, and x 475.7…475.9, z 24.1…24.3, y 1.15.

  **The last ~28 m of the road (x 453…481) runs into Launch Pad geometry.** Either the road ends at about x 453 (the tile at 451 scaled 0.25 gives 451…453), or the Launch Pad opens a gap. Director/Launch Pad owner to decide.

## Proof
`proofs/flatbed_road_topdown.png`: top-down ortho of the full run from x 307 to 481, with tile origins labelled, the crane, pallet and FB-05 at the loading spot, and the receiver. Stations are not rendered.
