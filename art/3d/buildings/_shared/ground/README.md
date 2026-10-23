# Shared ground tile (M_ground, real-time)

This is a seamless tiling texture set baked from the **M_ground** look in `art/3d/mine_concepts/_src/mc_common.py` at commit 269e70f (unchanged at HEAD), with concept B's cool-grey ramp override. It has the warped noise strata, the voronoi rock plates with their crack lines, and the crack and grain bump. Use it under every building instead of the procedural vertex-colour ground.

| file | what | size | encoding | colour space |
|---|---|---|---|---|
| `ground_basecolor_1024.ktx2` | detail albedo, 1024², **10 m per repeat** (9.8 mm/px) | 53,364 B | ETC1S / BasisLZ, 11 mips | **sRGB** (`SRGBColorSpace`) |
| `ground_normal_512.ktx2` | tangent-space normal, 512², **10 m per repeat** | 145,083 B | UASTC + RDO + zstd, 10 mips | **linear** (`NoColorSpace`), OpenGL convention (+Y = +v), the three.js default |
| `ground_macro_256.ktx2` | macro-variation multiplier, 256², **76 m per repeat** | 17,543 B | ETC1S / BasisLZ, 9 mips | **linear**; R = mult / 2 (0.5 = ×1.0, range ×0.66–×1.43, mean ×1.0) |
| **total** | | **215,990 B** (211 KB) | | |

- All three tiles are exactly periodic. The noise is sampled on a 4D flat torus, so there is no mirroring and no cross-fade. The mips were made with wrap edge sampling, so they are seamless too. The wrap-seam step measures 1.0–1.2× an ordinary neighbouring-pixel step (`_src/tiles_report.json`).
- **No repeat banding:** the detail tile has been high-passed. Luminance wavelengths of 2.5 m and up are removed with a periodic FFT filter, which keeps the chroma and the mean. All the large-scale variation lives in the macro tile instead. Its 76 m repeat does not share a factor with 10 m, so the combined pattern only repeats every 380 m. In the preview, the luminance autocorrelation at the 10 m lag is 0.15.
- `ground_preview_160x60m.png` is a Cycles render of a 160 × 60 m patch, shaded with the tiles *decoded from the shipped KTX2s*. It has a top-down ortho panel at 10 px/m with 10 m ticks, and an oblique game-like panel.
- The mean albedo is sRGB (124, 127, 133), which matches the concept ground.

## three.js setup

Load the files with `KTX2Loader` (basis transcoder). Apply the detail and normal maps through standard UVs with `repeat`, and sample the macro tile in world XZ at its own scale.

```js
const ktx2 = new KTX2Loader().setTranscoderPath('libs/basis/').detectSupport(renderer);
const [albedo, normal, macro] = await Promise.all([
  'ground_basecolor_1024.ktx2', 'ground_normal_512.ktx2', 'ground_macro_256.ktx2'].map(f => ktx2.loadAsync(BASE + f)));
const aniso = Math.min(8, renderer.capabilities.getMaxAnisotropy());
for (const t of [albedo, normal, macro]) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = aniso; }
albedo.colorSpace = THREE.SRGBColorSpace;            // the KTX2 already says sRGB; set it anyway for clarity
normal.colorSpace = macro.colorSpace = THREE.NoColorSpace;

const TILE_M = 10.0, MACRO_M = 76.0;
// Detail + normal: standard UVs. For a ground plane of sizeX x sizeZ metres with 0..1 UVs:
for (const t of [albedo, normal]) t.repeat.set(sizeX / TILE_M, sizeZ / TILE_M);
const mat = new THREE.MeshStandardMaterial({ map: albedo, normalMap: normal, roughness: 0.92, metalness: 0.0 });
// Macro: sampled from world XZ at its own 76 m scale, so it stays independent of mesh size and UVs.
mat.onBeforeCompile = (sh) => {
  sh.uniforms.macroMap = { value: macro };
  sh.vertexShader = sh.vertexShader
    .replace('#include <common>', '#include <common>\nvarying vec2 vGroundXZ;')
    .replace('#include <worldpos_vertex>',
             '#include <worldpos_vertex>\nvGroundXZ = (modelMatrix * vec4(transformed, 1.0)).xz;');
  sh.fragmentShader = sh.fragmentShader
    .replace('#include <common>', '#include <common>\nvarying vec2 vGroundXZ;\nuniform sampler2D macroMap;')
    .replace('#include <map_fragment>',
             '#include <map_fragment>\ndiffuseColor.rgb *= texture2D(macroMap, vGroundXZ / 76.0).r * 2.0;');
};
```

- **Standard UVs** for the albedo and the normal map: one repeat is 10 m (`repeat = size / 10`). For a non-plane ground (e.g. a terrain mesh), bake UVs = world XZ / 10. Tangent space is the three.js default (OpenGL, +Y = +v), so nothing needs flipping.
- **The macro tile** is sampled in world XZ / 76 m. Because 76 does not divide evenly into 10, it breaks the 10 m repeat.
- **The macro multiplier is linear,** so it is applied to `diffuseColor` after the sRGB decode. Use `.r * 2.0` to recover it. For a cheaper look on low tiers, skip the macro lookup and the normal map entirely. The albedo alone still tiles cleanly at 10 m.
- **Anisotropy 8** is what keeps the grazing-angle ground crisp. The ETC1S albedo stays sharp with mips plus anisotropy.

## Rebuild

```sh
B=/opt/blender-4.2.3-linux-x64/blender; cd art/3d/buildings/_shared/ground/_src
$B -b -P bake_ground.py -- --what detail --T 10 --res 1024 --out /tmp/ground/detail.npy   # ~6 min CPU
$B -b -P bake_ground.py -- --what macro  --T 76 --res 256  --out /tmp/ground/macro.npy
python3 make_tiles.py /tmp/ground ..          # PNG masters in _src/png + KTX2 (KTX-Software 4.4.2 `ktx create`,
                                              # /home/box/apps/gltftools/ktx; env KTX=, NORMAL_RES=512|1024, RDO=1.0)
K=/home/box/apps/gltftools/ktx; for f in ../*.ktx2; do LD_LIBRARY_PATH=$K/lib $K/bin/ktx extract --transcode rgba8 $f /tmp/gdec/$(basename ${f%.ktx2}).png; done
$B -b -P render_preview.py -- --tex /tmp/gdec --out /tmp/gprev          # then compose ground_preview_160x60m.png
```

`NORMAL_RES=1024` gives a 1024² normal map, but it pushes the set over the 250 KB budget. The 512 normal is used because the bump is fine grain plus crack lines, and that holds up at 19.5 mm/px.
