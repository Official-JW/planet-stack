# Shared building materials (game GLBs)

A minimal shared palette for every building's **game** GLB, so that buildings batch well and look consistent.

- `shared_materials.json` holds the canonical list of 14 flat PBR materials (`SH_*`): base colour, metal and roughness, plus emissive for the glow strips and lamps. There are no textures, so the GLBs stay small and the materials stay shareable.
- **Rule:** a game GLB may only use `SH_*` materials, with one merged mesh per material. That means draw calls equal the number of materials used, and the cap is 15.
- Game GLBs use meshopt compression and quantization (`gltfpack -cc`). **No Draco.**
- A building's master .blend keeps its full procedural materials. Its game exporter (see `life_support/_src/build_game_glb.py`) remaps master materials onto this palette by name.

The first user is Life Support (`../life_support/`). Add materials here only when no existing `SH_*` material fits, and keep the total small.
