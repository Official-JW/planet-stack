# Planet Stack: modular crew roles (10 roles)

Every role wears the same crew suit: a white shell, graphite, a gold visor and cyan glow lights. A role adds only three things:
- an **accent colour**, applied to the chest and arm plates, pauldrons, backpack, helmet crown stripes, badge ring and tool trim;
- a **hand tool**, held in the right hand with a power grip;
- a **helmet badge**, a medallion on both temples.

Some roles also get small extras: a headset, tool belt, accent gloves or a shoulder radio.

This builds on AA3's pass-1 kit in `art/3d/crew/roles/`. Its `_src/*.py` were copied here at commit `1d8c961` and extended; that folder was not edited.

## The roles
| # | Role | Group | Accent | Tool (GLB node) | Badge | Job line |
|---|---|---|---|---|---|---|
| 01 | **Miner** | Starting Crew | `#d68f00` | Rock pick (`Tool_miner`) | rough ore chunk (irregular lumpy rock, three chipped facets split by a vein-line gap, small chip) (`ore`) | Mines ore at the Mine. |
| 02 | **Mine Driver** | Starting Crew | `#2cffba` | Drive controller + headset (`Tool_mine_driver`) | three-spoke wheel (`wheel`) | Drives the mine truck. |
| 03 | **Mechanic** | Starting Crew | `#b81c00` | Heavy wrench + tool belt (`Tool_mechanic`) | eight-tooth gear with a round hole (`gear`) | Upgrades and builds. |
| 04 | **Cargo Manager** | Starting Crew | `#8b1fc5` | Cargo tablet + radio (`Tool_cargo_manager`) | front-on cargo crate (square frame, diagonal brace, two plank panels) (`crate`) | Runs cargo and radios the crew. |
| 05 | **Captain** | Flight Crew | `#647fff` | Flight yoke + headset (`Tool_captain`) | three stacked rank chevrons (`chevron3`) | Flies the ship once the Habitat is up. |
| 06 | **Co-Captain** | Flight Crew | `#12afc3` | Nav scope + headset (`Tool_co_captain`) | two stacked rank chevrons (`chevron2`) | Navigates and flies second seat. |
| 07 | **Engineer** | Specialist | `#b87249` | Power driver + tool belt (`Tool_engineer`) | upright rocket with two fins (`rocket`) | Builds new ships at the Shipyard. |
| 08 | **Botanist** | Specialist | `#d0ff66` | Seedling pod (`Tool_botanist`) | pointed leaf with a stem (`leaf`) | Grows food in the greenhouse. |
| 09 | **Welder** | Specialist | `#ff4993` | Weld torch (`Tool_welder`) | weld torch nozzle with five short spark lines spraying from its tip (`spark`) | Welds and repairs hull plates. |
| 10 | **Machinist** | Specialist | `#b82756` | Caliper (`Tool_machinist`) | hex nut (`nut`) | Machines parts in the workshop. |

- **Flight crew.** Captain and Co-Captain are the only roles that fly once the Habitat is built (`roles.json → flies_after_habitat`).
- **Engineer.** The job is now "builds new ships", so the badge changed from AA3's power bolt to a rocket.
- **Accents.** Pass 2 re-picked all ten accents to keep them distinct as a set of 10. See `CARD_SPEC.md`, `proofs/palette_cvd.png` and `_src/palette_check.py`.

## Files
```
roles.json                       accent hex, badge file, card file, tool / badge node names per role (generated: _src/write_json.py)
CARD_SPEC.md                     pick-screen card template spec
cards/card_<role>.png            1125x480 (375x160 pt @3x), <= 60 KB each
proofs/lineup_roles_3200x1200.png   full-res lineup of all 10
proofs/game/game_front_375x667.png  game camera, figures ~20 px tall (+ game_back, game_figures_x8nn.png = 1:1 pixels at 8x)
proofs/badges/badge_<key>_256.png   flat badge icons; badges_sheet.png also shows them at 20 and 12 px
proofs/palette_cvd.png              accents + badges under normal / protan / deutan / tritan simulation
glb/role_kit.glb                    Tool_<role> + Badge_<role> nodes, one vertex-colour material, meshopt + quantized
_src/roles_table.py   THE table (name, job, accent, tool, extras, badge, pose, group)
_src/role_kit.py      suit + kit builder (Blender); tools for all 10 roles
_src/render_roles.py  --mode portrait | lineup | game | badges | preview | card
_src/cards3x.py       card compositor (PIL)        _src/compose.py  lineup captions, game proof sheet, badges, palette sheet
_src/run_renders.sh   queued render steps, each under flock /tmp/planet_stack_heavy.lock nice -n 19 ... -t 4
_src/suit_base.py     frozen copy of the shared suit (crew_pass3.py) - not edited
```

## Attaching a tool in game
`glb/role_kit.glb` → node `Tool_<role>`. Parent it to the crew rig's `Op_Hand_R`. The node's origin is the grip centre; its local +Y (glTF) is the handle axis, pointing toward the thumb, and +X points along the fingers.

## Adding a role
1. Add an entry to `ROLES` and `ORDER` in `_src/roles_table.py`. If the role needs a new tool, add a builder to `role_kit.py`; if it needs a new badge, add a primitive list to `BADGES`.
2. Run `python3 _src/palette_check.py` and keep every simulated minimum at ΔE00 ≥ 9.
3. Run `bash _src/run_renders.sh portrait`, then `python3 _src/write_json.py roles.json`.
