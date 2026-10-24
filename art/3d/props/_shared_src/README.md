# props/_shared_src

These are shared tools for the FB-05, cargo box, Refinery crane and receiver builds.

- `propgeo.py`: Blender mesh builder (box, cyl, quad, text, weather), the Concept B palette, SHM_Paint / SHM_GlowCyan materials, and the glTF export (vertex colours, no textures).
- `verify_props.mjs`: `node verify_props.mjs fb05|box|crane|receiver file.glb`. Loads the file with three r186 GLTFLoader + MeshoptDecoder and checks the budget, extensions, images, markers and joint behaviour. It prints JSON, and `fail` must be empty.
- `render_props_proof.py`: proof renders. `blender -b -P render_props_proof.py -- --out X.png --w W --h H --samples N [--fb --box --crane --road unpacked.glb] [--road_tiles x0,n,z,tail_scale] [--pallet N] [--rx receiver.glb --rx_at x,z,yaw_deg --rx_clip C --rx_t s] [--t clip_s] (--cam az,el,dist,tx,ty,tz --lens mm [--ortho width_m] | --phone tx,ty,tz,frame_w)`. Inputs must be unpacked first with `gltfpack -noq -kn -ke [-ac]`. The crane input is the `--proofclip` build (the shipped crane has no clips); all positions are crane-local glTF.
