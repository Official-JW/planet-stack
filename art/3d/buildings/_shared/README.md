# Shared building materials (game GLBs)

A minimal shared palette for every building's **game** GLB, so that buildings batch well and look consistent.

- `shared_materials.json` holds the canonical list of 14 flat PBR materials (`SH_*`): base colour, metal and roughness, plus emissive for the glow strips and lamps. There are no textures, so the GLBs stay small and the materials stay shareable.
- **Rule:** a game GLB may only use `SH_*` materials, with one merged mesh per material. That means draw calls equal the number of materials used, and the cap is 15.
- Game GLBs use meshopt compression and quantization (`gltfpack -cc`). **No Draco.**
- A building's master .blend keeps its full procedural materials. Its game exporter (see `life_support/_src/build_game_glb.py`) remaps master materials onto this palette by name.

The first user is Life Support (`../life_support/`). Add materials here only when no existing `SH_*` material fits, and keep the total small.

## Merged set (3–6 draw calls), added for the Playtester targets

`shared_materials.json` also has `merged_materials` (`SHM_Paint`, `SHM_Metal`, `SHM_GlowCyan`, `SHM_GlowWhite`) and a `swatch_to_merged` map. The `SH_*` entries above are unchanged, and the launch pad still reads them.

To use the merged set, bake each `SH_*` swatch's `base` as a `COLOR_0` vertex colour, then merge meshes into the matching `SHM_*` material. You get 4 draw calls and the same look.

**Game GLB rules:**
- Plain metallic/roughness only (three.js `MeshStandardMaterial`). No `KHR_materials_*` extensions: no transmission, clearcoat, ior or specular.
- No textures. If one is ever needed, it must be KTX2 (`KHR_texture_basisu`), never PNG or JPG.
- meshopt compression and quantization (`gltfpack -cc`). **No Draco.**
- 10–20k triangles and 0.9 MB or less per building.

The reference implementation is `../life_support/_src/build_game_glb.py`.
