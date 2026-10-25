# Planet Stack - Crew role system (pass 1)

One shared crew suit + a per-role **kit**. Every role wears the identical pass-3 suit
(`_src/suit_base.py` = verbatim copy of `boarding/_src/crew_pass3.py`, never edited; Mine concept B:
sleek white shell, graphite + cyan base, panel lines, light dust/edge wear). A role only adds:

| Kit piece | Where it goes |
|---|---|
| **Accent colour** | **solid** chest plate, upper-arm (bicep) plates and shoulder plates (pauldrons) + **solid** backpack shell and side tanks (clean paint: light dust/wear so the colour stays saturated at phone size), twin helmet crown stripes (brow to nape, read from behind/above), suit accent stripes (shin/thigh/boot/back-of-glove), helmet badge ring, tool trim. Pauldron lames / tank bands / the chest accent flip to white on the coloured plates. |
| **Hand tool / prop** | right hand, closed power-grip glove wrapped on a 0.0175 m handle |
| **Helmet badge** | both helmet temples (raycast onto the shell), 0.046 m medallion: accent ring, graphite disc, white symbol |
| *extras* (optional) | small role-specific add-ons (headset, radio, tool belt, accent gloves) |

Cyan stays the suit's shared glow / UI colour on every role; accents were picked to sit apart from it
(and from each other) at phone size.

## Roles

| # | Role | Accent | Tool (right hand) | Extras | Badge (original geometric symbol) | Job line |
|---|---|---|---|---|---|---|
| 1 | **Miner** | `#FFC21A` amber | Rock pick: long graphite haft, rubber grip, steel spike + chisel-adze head, accent collar | - | **Ore chunk**: irregular lumpy rock split into three chipped facets by a thin vein-line gap, plus a small chip (deliberately not gem/crystal-like: crystals are the paid currency) | Mines ore at the Mine. |
| 2 | **Mine Driver** | `#2FD36B` green | Drive controller: compact handheld twin-grip remote, white face plate with small cyan screen, two thumb sticks, accent bumper + buttons, stub antenna | headset (accent ear cup + boom mic), accent gloves | **Wheel**: three-spoke wheel | Drives the mine truck. |
| 3 | **Mechanic** | `#F0443A` red | Heavy wrench: open C-jaw top, closed ring end, accent inlay | tool belt (two hip pouches) | **Gear**: eight-tooth gear with a round hole | Upgrades and builds. |
| 4 | **Cargo Manager** | `#A066FF` violet | Cargo tablet: cyan manifest screen, accent header bar | shoulder radio w/ whip antenna (left shoulder) | **Crate**: front-on square cargo crate: frame, diagonal brace, two plank panels (no isometric / rhombus top) | Runs cargo and radios the crew. |
| 5 | Engineer *(tier 2, defined, tool not built)* | `#FF7A1F` orange | multimeter | - | Bolt (angular power bolt) | Keeps the base powered and running. |
| 6 | Botanist *(tier 2)* | `#B6E62E` lime | plant sampler | - | Leaf (pointed, with stem) | Grows food in the greenhouse. |
| 7 | Welder *(tier 2)* | `#FF4FB0` magenta | weld torch | - | Torch spray: short angled torch nozzle with five short spark lines spraying from its tip (no star shape) | Welds and repairs hull plates. |
| 8 | Machinist *(tier 2)* | `#4D6BFF` blue | caliper | - | Nut (hex nut) | Machines parts in the workshop. |
| 9 | Captain *(flight crew, in progress: Art Assistant)* | `#1F3A8A` navy + `#E8B53A` gold trim (warmer and flatter than the visor gold) | slate command tablet | slim gold shoulder boards | 3-bar chevron (no stars, no diamonds) | Flies the ship. After the Habitat is built, only a Captain and Co-Captain fly out. |
| 10 | Co-Captain *(flight crew, in progress: Art Assistant)* | `#1F3A8A` navy, lighter `#4A6BD0` arms, `#F2F3F1` white chest band, `#DFE3E8` silver-white trim (gold is Captain only) | slate command tablet | slim silver-white shoulder boards | 2-bar chevron | Second pilot on every flight after the Habitat. |

Engineer, Botanist, Welder and Machinist are Moon specialists that Eve offers on later trips. Captain and Co-Captain are flight crew (Director, 2026-10-24). The Botanist is the first female crew member: same armature, slightly shorter, contoured hard-shell chest plate, wider hips and seat (Jacob, 4:54 PM).

Badges are plain geometric primitives drawn by us (`roles_table.BADGES`) - no agency, brand or game marks, no text.
**No crystal / diamond / gem shapes anywhere in the crew kit** (crystals are the game's paid currency). No rhombus / diamond faces and no 4-point stars either.

## Files

```
roles/
  ROLES.md
  _src/roles_table.py   <- THE roles table (pure python): name, job, accent, tool, extras, badge, arm pose, wrist roll, card_az, tier
  _src/role_kit.py      <- builds a crew member + kit: role_member(key, loc, rot_z, variant)  (monkeypatches suit_base, does not edit it)
  _src/suit_base.py     <- frozen copy of crew_pass3.py
  _src/badge2d.py       <- flat badge icon (PIL) for UI: badge_icon(key, accent, size)
  _src/render_roles.py  <- --mode lineup | card | game | badges | preview  (Cycles / WORKBENCH)
                           game  : in-game-size proof (38 deg vFOV, 18 deg look-down, ~20 px figures at 375x667, front + back)
                           badges: helmet-badge close-up tiles
  _src/make_cards.py    <- composites role cards, lineup captions, badge icons (PIL + Rajdhani)
  _src/export_kit.py    <- role-kit GLB (tools + badges, vertex colours)
  proofs/lineup_roles_1920x1080.png      captioned Cycles lineup  (proofs/_raw/lineup_raw.png = uncaptioned)
  proofs/cards/card_<role>_750x1050.png   pick-screen cards
  proofs/badges/badge_<key>_256.png       flat badge icons
  proofs/game/                             20 px in-game proof (375x667 front/back + 4x nearest upscales)
  proofs/helmet_badges_1600x400.png        helmet badge close-up strip
  glb/role_kit_tier1.glb                  meshopt + quantized kit props
```

## Role card spec (Eve's pick screen)

* **750 x 1050 px** portrait PNG (5:7, = 250 x 350 pt @3x), RGBA with chamfered corners (outside = transparent).
* Graphite gradient + faint grid, accent glow behind a Cycles 3/4 hero (750x780, transparent film + shadow catcher),
  accent trim + corner ticks, badge icon top-left, "CREW ROLE / 0N" top-right, info panel with role name
  (Rajdhani Bold), job line (Rajdhani Medium) and a KIT line.

## Adding a role

1. Add an entry to `ROLES` (and `ORDER`) in `_src/roles_table.py`: accent hex, tool key, extras, badge key, `arm_r` pose, optional `roll`/`card_az`, `tier`.
2. If the tool or badge is new: add a `tool_<name>(K, M, F)` builder to `role_kit.TOOLS` (built in the grip frame: origin = grip centre,
   +Z = handle axis, use `grip_sleeve()` for the handle) and/or a badge primitive list to `roles_table.BADGES`.
3. Render: `flock /tmp/planet_stack_heavy.lock nice -n 19 blender -b -P render_roles.py -t 4 -- --mode card --roles <key> --out ../proofs/_raw`
   then `python3 make_cards.py cards ../proofs/_raw ../proofs/cards`.

## GLB (role_kit_tier1.glb)

Eight nodes: `Tool_<role>` and `Badge_<role>` for the four tier-1 roles. One shared material `RoleKit_VC` (vertex colour COLOR_0),
no textures/images, no Draco/transmission/clearcoat/ior. gltfpack `-c` (EXT_meshopt_compression + KHR_mesh_quantization).
Tool origin = grip centre; local +Z (Blender) = handle axis toward the thumb, +X = finger direction -> parent to the right-hand socket.
Suit-attached extras (headset, radio, belt) are not in the GLB yet.
