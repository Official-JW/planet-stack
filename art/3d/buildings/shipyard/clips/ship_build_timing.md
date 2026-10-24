# Shipyard — SN-07 staged ship build: game clip timing sheet

GLB: `art/3d/buildings/shipyard/shipyard_game.glb` (built by `_src/build_shipyard.py --only game` → `_src/post_ship_build.py` → `gltfpack -cc -kn -ke`).
Every build clip drives exactly two channels on ONE node, **`Crane_Jib`**: `rotation` (slew about +Y, pivot = the IS-1 slewing ring)
and `weights` (14 morph targets on all 3 of its primitives). Keys are sampled at 30 Hz with LINEAR interpolation; the easing is baked into the keys.
Every clip keys the jib angle and **all** 14 weights, so a clip fully defines the pose. Each clip's first key is exactly the previous clip's last key.

| # | clip | dur (s) | type | easing / content | jib angle | peak jib °/s | peak ring m/s |
|---|------|---------|------|------------------|-----------|--------------|---------------|
| 1 | `ring_lift`    | 9.0  | one-shot | smoothstep hoist from the yard floor (`load_low` 1→0); pendulum sway (`sway_*`, ≤0.35 m) enveloped by sin(πt/9), so it is 0 at both ends | 140° fixed | 0 | 7.8 |
| 2 | `jib_swing_in` | 4.0  | one-shot | smoothstep slew 140→0°; the load lags the angular acceleration (≤0.45 m, 0 at both ends); hoist hop ≤0.8 m mid-swing clears the z30 handrail | 140→0 | **53.0** | 13.1 |
| 3 | `ring_lower`   | 6.0  | one-shot | smoothstep 12.2 m descent (`load_seat` 0→0.9242), centred, no sway | 0 | 0 | 3.1 |
| 4 | `ring_settle`  | 3.0  | one-shot | last 1 m (ease, touch-down at 1.8 s); 4 cm damped rebound 1.8–2.6 s; line-up nudge ≤6 cm (0 by 1.8 s); arc strike `bead_white` 0→1 from 2.5 to 3.0 s | 0 | 0 | 1.6 |
| 5 | `ring_weld`    | 16.0 | **LOOP** | 3 orbital weld heads sweep ±0.6 m along the seam (sin, 2 cycles); spark bursts `sparks_a` (14) and `sparks_b` (13) with one-frame ramps; white bead pulses 0.96–1.0. First key == last key (checked: Δ 0.00000) | 0 | 0 | 0 |
| 6 | `seam_cool`    | 6.0  | one-shot | 0–0.4 s red-orange bead `bead_red` 0→1 (sits inside the white tube); 0.3–2.6 s white tube shrinks 1→0 (white → red-orange); 2.6–5.6 s red tube 1→0 (→ bare steel/graphite seam frame) | 0 | 0 | 0 |
| 7 | `jib_return`   | 9.0  | one-shot | frame 1: `stow` 0→1 (the jib's ring copy collapses into the hook, see chaining); 0.1–2.5 s hook rises out of the stack; 2.5–6.5 s smoothstep slew 0→140°; 6.5–8.5 s hook down to the pick-up spot; last frame: `stow` 1→0 = next ring on the floor (== `ring_lift` t=0) | 0→140 | **53.0** | (swap frames) |

Unchanged: `hall_door_open` (3.6 s, one-shot; now drives the morph `open` on the single merged node `Hall_Door_Leaves`, see below) and `Beacon_Lights_Blink` (1.0 s, loop, scale STEP).
**`crane_jib_swing` is REPLACED** (removed). The jib's rest pose is now 140° (pick-up), and the old idle swing would have
fought the build clips on the same node. `jib_swing_in` and `jib_return` take over its motion.

## Rest / default pose
`Crane_Jib` node rotation = 140° about +Y. `mesh.weights` = `load_low` 1, all others 0: the ring rests on the yard floor at the pick-up
spot behind FAB-01. This is `ring_lift` t=0.

## Morph targets (`Crane_Jib` mesh `extras.targetNames`, same order on all 3 primitives)
`load_low, load_seat, hop, sway_px, sway_nx, sway_pz, sway_nz, sweep_p, sweep_n, sparks_a, sparks_b, bead_white, bead_red, stow`

Primitives: `SH_White` (jib, hoist, ring, lift frame, weld heads), `SH_GlowWhite` (sparks and the hot bead), `SH_GlowRed` (the cooling bead).
All weights are in [0, 1]. gltfpack clamps animated weights to [0, 1], so every signed motion is split into a +/- target pair, and gltfpack quantizes weights to about 1/512 (≤ 2.6 cm on the 13.2 m seat travel).

### Why the cooling is morph geometry, not an animated emissive colour
Animating the emissive colour or strength needs `KHR_animation_pointer`. gltfpack drops it, and three.js GLTFLoader does not play it. Swapping
materials per frame would also need game code. Core-glTF morph-weight animation survives gltfpack (verified: raw→packed max weight error 0.002)
and plays in three.js through `AnimationMixer` with no code. So the hot bead is a torus tube in `SH_GlowWhite` (r 0.16 m). The cooling bead is a slightly
thinner coincident torus in `SH_GlowRed` (r 0.14 m). At weight 0 each collapses to a zero-area circle and is invisible. White → red-orange happens by
shrinking the white tube below the red one; red-orange → steel happens by shrinking the red tube to reveal the seam frame. The palette has no orange,
so `SH_GlowRed` (#f25f5c) is the red-orange step. This adds 2 draws (the GlowWhite and GlowRed primitives). They are paid for by: base `SH_Solar` → `SH_Graphite` (one 158-tri panel)
and the two hall-door leaves merged into one node.

## Chaining recipe (Coder)
```js
const mixer = new THREE.AnimationMixer(gltf.scene);
const A = n => mixer.clipAction(THREE.AnimationClip.findByName(gltf.animations, n));
const seq = ['ring_lift','jib_swing_in','ring_lower','ring_settle','ring_weld','seam_cool','jib_return'];
for (const n of seq) { const a = A(n); a.setLoop(n === 'ring_weld' ? THREE.LoopRepeat : THREE.LoopOnce, Infinity); a.clampWhenFinished = true; }
// play ONE Crane_Jib clip at a time, hard cut (no crossfade needed: start keys == previous end keys):
function go(n) { if (cur) cur.stop(); cur = A(n).reset().play(); }
mixer.addEventListener('finished', e => { const i = seq.indexOf(e.action.getClip().name); go(seq[(i + 1) % seq.length]); });
// ring_weld loops: leave it only on a loop boundary, so the sweep/sparks/bead are at their t=0 values (== seam_cool start):
mixer.addEventListener('loop', e => { if (e.action.getClip().name === 'ring_weld' && weldDone()) go('seam_cool'); });
```
Per ring k = 1..N: `ring_lift → jib_swing_in → ring_lower → ring_settle → ring_weld ×m (m ≥ 1 loops = 16 s each) → seam_cool → jib_return`.
`jib_return` ends exactly at `ring_lift` t=0, so the cycle repeats for ring k+1 with the same clips, unchanged. Durations: 37 s + 16·m s per ring.

**The installed ring (needed for N > 1, or for showing the finished ring after `seam_cool`).** The GLB contains ONE ring mesh, and it lives in
`Crane_Jib`. When `jib_return` starts, the game must reveal a static copy of the finished ring on the stack in that pose (stage swap). On frame 1 of
`jib_return` the jib's copy collapses into the hook (`stow`). For the SN-07 crew-deck ring that copy is the next stack stage. For rings 2..N it is AA2's ring
sections (one per seat height). If those seat higher than the first ring, the `load_seat` travel (13.2 m) has to be shortened per ring: either a per-seat
`load_seat_k` target, or a node offset on the game side. The clips themselves need no change. With N = 1 and no stage swap, stop the chain after `seam_cool`
and don't play `jib_return`.

## Hall door contract change
`Hall_Door_L` and `Hall_Door_R` are now ONE node, `Hall_Door_Leaves` (child of `Hall_Door`), with morph `open` (L −10.25 m / R +10.25 m in x).
`hall_door_open` keeps its name, its 3.6 s length and its timing, but drives `weights` instead of the two translations. Code that looked up `Hall_Door_L/R` by name must use
`Hall_Door_Leaves`. Playing the clip is unchanged.

## Checks (three.js r169 GLTFLoader + AnimationMixer on the packed GLB; sampled at 120 Hz for speeds, 30 Hz for the gap)
See `ship_build_check.txt` for the raw output. Summary:
- 15 draws, 28,174 tris. Every clip's start key matches the previous clip's end key (jump 0.0000° / 0.0000 weight), including `jib_return → ring_lift`.
  `ring_weld` first key == last key.
- Peak jib angular speed: 53.0 °/s (`jib_swing_in`, `jib_return`). The ring never spins about its own axis.
- Gap (BVH closest point, load verts = ring + lift frame + rigging + hoist end vs. base + tiers + doors): ≥ 1.29 m on `ring_lower` (z21/z30 platforms
  widened to an inner radius of 6.95 m), 1.80 m on `jib_swing_in`, and 1.50 m from the floor once the ring is ≥ 1.5 m up on `ring_lift`.
  **Exclusions, contact by design:** the weld heads, sparks and bead; the open stack top (tris with centroid r < 5.4 m and y < 20.08); the
  yard floor while the ring rests on it at pick-up. Seated (`ring_settle` end, `ring_weld`, `seam_cool`), the nearest non-excluded part is SN-07's
  own open cargo door at 0.988 m: it is the same ship, directly under the new ring.
- Nothing floats: at pick-up the ring bottom is at y 0.20 on the 0.12 slab, and seated it is at 19.88 = the stack top.
