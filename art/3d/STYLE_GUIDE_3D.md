# Planet Stack · 3D Style Guide (v1)

One page for everyone who makes or wires up 3D models. The drill rig (`drill_rig/`) is the reference model for every rule here.

## 1. Units, axes and origin
- 1 unit = 1 meter. +Y is up. The model's front faces +Z, toward the game camera.
- The origin is at the center of the base, at ground level. y = 0 is the Moon ground, so nothing sits below 0 at rest.
- Real-world scale: an astronaut is 1.8 m tall, and a big building is about 8–12 m.

## 2. Naming
- Files are lowercase snake_case: `drill_rig.glb`, `rover_bay.glb`. Put each model in its own folder under `art/3d/`, with its source next to it.
- The root node has the model's name in PascalCase (`DrillRig`). Moving parts get short PascalCase names that the code can find: `Bit`, `Carriage`, `Hopper`, `StatusLamp`, `HeliumStrip`, `OreFill`, `HopperLamp`.
- Never rename a node after Game Coder has wired it up. Add a new one instead.

## 3. Animation clips
- Clips live inside the GLB as named clips, in lowercase: `idle`, `work` or `dig`, `full`, `build`, `off`.
- Every clip loops seamlessly, with the first key equal to the last.
- Every clip keys every animated node, so switching or crossfading never leaves a part stuck in the last clip's pose.
- Use 30 fps keys. Lamps blink by scaling a glowing bulb out of a dark lens, which needs no material animation.

## 4. Compression and delivery
- Meshes use meshopt (`gltf-transform meshopt`), or Draco if needed. Three.js needs `loader.setMeshoptDecoder(MeshoptDecoder)`.
- Textures are KTX2 (`gltf-transform uastc`/`etc1s`), and only if a model really needs one. The default is **no textures**.
- Pipeline: export from Blender, then `gltf-transform prune`, `dedup`, `resample`, `meshopt`. Check the result with `gltf-transform inspect`.

## 5. Budgets (Playtester checks these on every QA3D build)
| Item | Limit |
|---|---|
| Building / hero model | ≤ 2 MB GLB (aim for under 300 KB), about 5–15k triangles |
| Prop | ≤ 300 KB GLB, under about 2k triangles |
| First playable screen | ≤ 3 MB total download |
| Whole game | ≤ 8 MB total, with the rest loading in the background |
| Textures | ≤ 1024 × 1024, KTX2 |
| Draw calls on screen | about 100 at most. Merge static parts per material, with ≤ 12 meshes or materials per model |
| Frame rate | 60 fps on iPhone Safari, and never below 55 over any 5 seconds |

## 6. Palette (sRGB hex, matches the 2D art pack)
| Role | Hex |
|---|---|
| Graphite (dark trim, hazard black) | `#2a3245` |
| Graphite 2 (pads, frames) | `#3a4258` |
| Steel (beams, braces) | `#5b667e` |
| Steel light (deck, rails, rods) | `#8794ad` |
| Pale panel | `#c9d3e6` |
| White body panel | `#e8edf5` |
| Amber accent / hazard | `#ffb020` |
| Warm orange (tappable) | `#e8701a` → `#ffb04d` |
| Cyan Helium-3 glow | `#3ad0ff` (highlight `#7ff3ff`) |
| OK green / alert red | `#6ee08a` / `#f25f5c` |
| Lunar rock / ground | `#6f6d6b`, `#7d7b79`, `#8b8987` |
| Sky | `#05070f` → `#2b3a5e` |

## 7. Shading look
- Stylized low-poly and flat cartoon. Boxes get a single 3–9 cm chamfer, and cylinders have 8–16 sides with smooth sides and crisp caps.
- Color comes from **vertex colors** multiplied by a plain material: `M_Body` (roughness about 0.7, metalness 0). Use no PBR metal, because it goes black without an environment map.
- Bake a soft gradient into the vertex colors: each part is about 15–30% darker at its base, plus a light ground-contact darkening below 0.35 m. That is our AO.
- Glows use separate emissive materials (`M_GlowCyan`, `M_GlowAmber`) with no vertex colors. Keep glows to small strips and bulbs.
- Hazard stripes are diagonal amber/graphite strips, built as geometry, never as a texture.
- Use single-sided materials (back faces culled). Close every solid, and give open containers real wall thickness.

## 8. Lighting assumptions (what the game scene provides)
- One directional "sun" with hard shadows, coming from the upper front-left (about (-0.55, 0.78, 0.6)), in warm white `#fff4e4`.
- A hemisphere fill (sky `#c9d3e6`, ground `#5b667e`), with no environment map. The renderer uses sRGB output.
- Models must read clearly with only this setup: dark parts stay separated from the gray ground, and glows still pop.

## 9. Originality
Every model, shape, stripe and decal is our own. There are no logos, real company marks, brand names, or copied or ripped assets.

## 10. Delivery checklist
- [ ] Axes, units and origin are correct (bbox min y = 0, centered on x/z).
- [ ] Key nodes are named, and the clips are named, looping and keying every animated node.
- [ ] The source is committed (a Blender file and/or a generator script) next to the GLB.
- [ ] The GLB is meshopt-compressed and within budget. Post the size, md5, triangles, meshes and materials.
- [ ] `gltf-transform inspect` is clean, and the GLB loads in three.js with the clip list printed.
- [ ] Turntable proof PNG: 8 angles plus a close-up, on gray lunar ground with a hard sun shadow and a 1.8 m astronaut.
- [ ] A short GIF per clip, rendered from the real GLB in three.js.
- [ ] Nothing touches game JS, `qa/` or `preview/`. Game Coder wires the model in on /qa3d/.
