# EXPORT.md — final_export_1827

Lossless export of the exact approved `clip_channel_1720` assembly. No model-design change.
Written Saturday Nov 7, 2026, 6:42 PM America/Los_Angeles (Pacific).

**Choice: SPLIT (not both).** Two deliverable files, no duplicated hull:

| File | Role | Bytes | md5 | sha256 |
|---|---|---:|---|---|
| `out/hull_channel_relief_1720.glb` | Replacement hull (channel + ≤80 mm relief). Byte-identical to the approved 1720 study hull. | 304872 | `4700a081d9f8d662e61187537a730dc5` | `651029016e04a2290a322c9be9fdcfdc7823ee35168bf5715fbe4a52f8bb110d` |
| `out/access_platform_ladder_rails_1720.glb` | Additive animated assembly: door overlay + deck + ladder + **actual rails** (posts, top/mid rails, panels, swing bar, toe). **Contains no hull.** | 9694064 | `299f517d8caa3ebfc28283c59a374551` | `04bbe2d931fbd6c34bc09970ac2de3e684f9b7aff54c6bcd5638fa588d20a282` |

Do not import the hull out of the assembly (it is not there) and do not also overlay this hull on an intact `mesh_3`. A channel recess is a real hull replacement.

Approved clip evidence (not rewritten, not copied into this packet):

| | path | md5 | sha256 |
|---|---|---|---|
| MP4 | `clip_channel_1720/video/clip_channel_1720.mp4` | `9e42b3be130df51ca95d7d7ea84d7fb1` | `da6cbaa971c34e1cb75c2dd1bb6b7fefbb4db11403b62c12d223afa914839219` |
| Contact sheet | `clip_channel_1720/stills/contact_sheet_1720.png` | `1a1eecdc6e43983f3920bc737bfff765` | `c24ce8e8fae4ec2cfb0f538a6a502dd0d5343f62e755f0e7fc08851ada5eaff4` |

## Source / replacement mapping

| Item | Identity |
|---|---|
| Served hull to hide/replace | `launch_pad_middoor_119efbb7.glb` md5 `119efbb75a64e6c6643e2c701c8d2fb5`, node **mesh_3** (also hide served `Crew_Hatch`) |
| Study hull this replacement was cut from | `drawer_final_study_1240/out/hull_slot120_clean_aperture.glb` md5 `597821c9a2a02699ebb2825dc30694b7` (immutable; 120 mm slot kept) |
| Replacement hull nodes | `Study_1720_Hull_Channel_PROPOSAL` (6756 tris) + `Study_1240_DoorRebate` (16 tris) |
| Parent | `Ship_Placeholder`, identity inverse |
| Locked door original | `approved_art_locked/access_deployed_3a227433.glb` md5 `3a227433bcf4b1e0309b801d16f6b923` sha256 `9b2833021431fa77f61ace45238f972fd82ad706bef0e1dc89ea1967c2ee59fe` — **do not move** |
| Door overlay actually packed | `drawer_slot_1146/out/overlay_approved_door.glb` md5 `11a8b251ee82dcc72a5218f771c61a2f` sha256 `09d243a0f5a97f6e55cbb0f133ce50337560f8e44b3b7c7cd0703685c2816134` (isolate of that locked door) |
| Platform deck | 1353 `overlay_platform_deck_thin.glb` md5 `53093aaf0601226856cfc0a7a307ca9e` sha256 `4c583a0938b93b676ab273bb35c7a0d5d426646b6721ad81d00b458ce03a6b65` |
| Keep | 120 mm platform slot y 28.420–28.540, az −32.75° to +63.25° |

Door rule: the assembly includes the actual 1146 overlay (`Study_1146_Access_*` under `Study_1146_Root`). If the scene already instances locked door `3a227433`, do **not** draw both — keep one. Status/glow meshes travel with the overlay.

## Units / axes / transform

- Authoring and both GLBs: ship-local glTF **Y-up**, metres, right-handed.
- `at(az, r, y) = (r*sin(az), y, r*cos(az))`
- Blender / three preview: `g2b(x,y,z) = (x, −z, y)`; inverse `b2g(x,y,z) = (x, z, −y)`
- Drawer: built in OUT coords. `DX = (−1.50*sin(15.35°), 0, −1.50*cos(15.35°)) = (−0.397072, 0, −1.446490)`. Stowed adds `DX*(1−slide)`.
- **Playback at 16 fps.** Set fps to 16 *before* import (a 24 fps scene stretches the 10 s clip by 24/16).

## Hierarchy (assembly)

```
Assembly_1720_SPLIT                         static root
├── PackRoot                                animated translation = DX*(1−slide)
│   ├── RailsMoving                         morph weights f001…f159 (basis = frame 0)
│   ├── LadderStage_0 … LadderStage_5       animated translation = (HX, y_top(k,lt), HZ)
│   ├── LadderSleeve                        static relative to pack (clip sleeve collar)
│   └── Study_1353_Root
│       └── Study_1353_DeckThin             inherits pack slide
└── Study_1146_Root                         static door overlay (does not slide)
    ├── Study_1146_Access_PressureFrame
    ├── Study_1146_Access_OuterDoor
    ├── Study_1146_Access_InnerDoor
    ├── Study_1146_Access_Chamber
    ├── Study_1146_Access_Corridor
    ├── Study_1146_Crew_Hatch_Status
    └── Study_1146_Crew_Hatch_Status_Glow
```

Replacement hull file (separate):

```
Study_1720_Hull_Channel_PROPOSAL
Study_1240_DoorRebate
```

## Animation channels and names

Single glTF animation: **`Animation`**

| Node | Path | Samples | Meaning |
|---|---|---|---|
| `PackRoot` | translation, rotation, scale | 160 LINEAR keys, t = frame/16, t0=0, tN=9.9375 | slide only; rotation identity, scale 1 |
| `LadderStage_0` … `LadderStage_5` | translation, rotation, scale | same 160 keys | translation only along +Y; identity / unit scale |
| `RailsMoving` | **weights** | 160 keys × 159 morph targets | one-hot: frame 0 = all weights 0 (basis); frame f = weight `f00{f}` = 1 |

Morph `targetNames`: `f001` … `f159` (159 targets + basis = all 160 clip frames). Exporter stored displacements sparsely for unchanged frames.

`HX, HZ = at(−16°, 5.15) = (−1.419532, 4.950498)`
`y_top(k, lt) = lerp(28.52, 28.52 − k*(4.878333 − 0.20), lt)`

## Rails contents (exact clip geometry, not dummies)

`RailsMoving` is the clip’s procedural rail builder baked as morphs, not stand-in empties and not scaled-away nodes:

- Nested posts: three fixed-length stages per post (radii 22 / 18.5 / 15 mm) that translate along the post, then fold as a group about the deck socket (`xf_post`)
- Socket collars and hinge pins at each of the 10 posts
- Knuckle balls at `y_top(tel)` and `y_mid(tel)` (`y_top = lerp(0.40, 1.10, tel)`, `y_mid = lerp(0.20, 0.55, tel)`)
- Round light-gray top and mid rails (`RAIL_R = 0.018`, `RAIL_C`) along the outer arc, including the spans that deform during fold (hence morphs, not rigid scale)
- Radial left panel, radial right panel, and corner panel (`draw_panel2`)
- Swing bar plus knuckles
- Toe segments along the right radial / outer corner

Topology note (visual match, constant vertex slots): the clip omits the swing-end socket ball when `fold ≤ 0.97` (5512 vs 5608 authored verts). The export always reserves those 96 verts and collapses them to a point when the clip would omit the ball; when `fold > 0.97` they match the clip ball exactly. The glTF exporter then stores 7714 positions (normal splitting); every source vert still lands within **0.001 mm** of the reconstructed export cloud on all 160 frames.

No dummy nodes. No scale-to-hide.

## Deployment times (16 fps, 160 frames, 10.0 s)

Easing is per-segment smoothstep `u*u*(3−2*u)`, baked into the 160 samples. A LINEAR player reproduces the clip at integer frames.

| frames | t (s) | phase | slide | fold | tel | lt |
|---|---|---|---|---|---|---|
| 0–4 | 0.00–0.31 | hold stowed | 0 | 0 | 0 | 0 |
| 5–25 | 0.31–1.62 | slide out | 0→1 | 0 | 0 | 0 |
| 26–38 | 1.62–2.44 | unfold rails | 1 | 0→1 | 0 | 0 |
| 39–49 | 2.44–3.12 | telescope rails up | 1 | 1 | 0→1 | 0 |
| 50–74 | 3.12–4.69 | ladder extend | 1 | 1 | 1 | 0→1 |
| 75–82 | 4.69–5.19 | hold deployed | 1 | 1 | 1 | 1 |
| 83–107 | 5.19–6.75 | ladder retract | 1 | 1 | 1 | 1→0 |
| 108–118 | 6.75–7.44 | telescope rails down | 1 | 1 | 1→0 | 0 |
| 119–131 | 7.44–8.25 | fold rails | 1 | 1→0 | 0 | 0 |
| 132–152 | 8.25–9.56 | slide in | 1→0 | 0 | 0 | 0 |
| 153–159 | 9.56–10.00 | hold stowed | 0 | 0 | 0 | 0 |

`fold` and rail `tel` live in `RailsMoving` morphs. `slide` lives on `PackRoot`. Ladder `lt` lives on `LadderStage_*`.

## Triangles / draw calls / size

**Replacement hull** — 304872 bytes; 6756 + 16 rebate tris; **2** mesh draw calls.

**Assembly** — 9694064 bytes; **6608** tris; **16** mesh draw calls:

| Mesh | Tris |
|---|---:|
| RailsMoving | 2804 |
| LadderStage_0…5 | 6 × 112 = 672 |
| LadderSleeve | 28 |
| Study_1353_DeckThin | 396 |
| Study_1146_Access_OuterDoor | 1700 |
| Study_1146_Access_PressureFrame | 672 |
| Study_1146_Access_Chamber | 96 |
| Study_1146_Access_InnerDoor | 60 |
| Study_1146_Access_Corridor | 60 |
| Study_1146_Crew_Hatch_Status | 108 |
| Study_1146_Crew_Hatch_Status_Glow | 12 |

Using both files together: 6608 + 6772 = 13380 tris, 18 draw calls.

## Verification (this packet)

| Check | Result |
|---|---|
| File-native rails, all 160 frames | source verts vs reconstructed morph cloud: max nearest **0.001 mm**, max bbox **0.0009 mm** (`measures/verify_split.json`) |
| PackRoot / ladder, all 160 frames | max 0.00005 mm / 0.00094 mm |
| Blender reimport at 16 fps (endpoints + intermediates 0,6,25,32,38,44,50,62,75,83,108,125,132,159) | door move **0.0 mm**; deck follows pack **0.0 mm**; rails world bbox max **0.0008 mm** (`measures/reimport_split.json`) |
| Hull separate reimport | node `Study_1720_Hull_Channel_PROPOSAL`, 6756 tris, bytes/hash unchanged from approved 1720 |
| Assembly contains hull? | no |

## Limits / integration notes

- Play the single `Animation` clip, including `RailsMoving` morph weights. If a viewer ignores morph animations, rails will freeze on the stowed basis.
- 16 fps, frames 0–159.
- SPLIT only: replace served `mesh_3` with the hull file; add the assembly under `Ship_Placeholder`. Do not also ship/import a second hull.
- Do not instantiate the packed door overlay on top of an already-present locked `3a227433` door.
- Channel (unchanged from approved 1720 cut): y 23.6417–28.52, az −31.3136° to −22.2493° (includes 80.0 mm / 1.146° +az relief), back wall r=3.872, recess 128 mm from skin r=4.00.
- This run did not write repo / art-dev / live and did not contact Coder.

## What this packet is not

- Not a remodel or polish of the approved 1720 design
- Not a combined-only package (hull is deliberately not inside the assembly)
- Not a rewrite of the approved MP4, contact sheet, or 1720 study source hashes
