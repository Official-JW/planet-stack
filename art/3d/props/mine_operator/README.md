# Mine operator on a raised control deck (scenery prop)

A mining operator at a small steel control deck beside the Mine. The look is Mine concept B: white and graphite hulls, cyan light strips, weathered vertex-colour detail. The operator wears the astronaut suit (white and graphite armour, gold visor, cyan accents) and stands 1.8 m tall. This is an original design with no logos. It is scenery only, with no tap target.

## Files
| file | what it is |
|---|---|
| `mine_operator_game.glb` | in-game asset (meshopt + quantization) |
| `proofs/mine_operator_hero_3840x2160.png` | hero shot, in the Mine scene |
| `proofs/mine_operator_phone_1179x2556.png` | Mine phone view with the deck composited at Operator_Deck |
| `proofs/mine_operator_phone_393x852.png` | Lanczos downscale of the above |
| `proofs/mine_operator_clips_sheet.png` | 4 chain clips x 6 frames |
| `_src/build_mine_operator.py` | generator (Python + numpy, writes the raw GLB, no Blender needed) |
| `_src/pack_mine_operator.sh` | build -> gltfpack -> verify |
| `_src/verify_mine_operator.mjs` | three.js load check (fails on banned extensions, images, more than 2 draws or 3,000 tris) |
| `_src/render_sheet.py`, `_src/render_mine_view.py`, `_src/op_blender_common.py` | proof renders |

## Specs (shipped GLB)
- **2 draw calls**: one skinned mesh `Op_Mesh` with 2 primitives on one skin.
  - `SHM_Paint`: metal 0, roughness 0.42, colour from vertex colours (COLOR_0).
  - `SHM_GlowCyan`: base and emissive [0.0284, 0.768, 1.0].
  - Both are the exact material names and values used by the Mine GLB, so the Mine's shared materials can be reused.
- **2,584 triangles** (budget 3,000): deck 1,458 and operator 1,126; paint 2,276 and glow 308.
- **19 joints**:
  - `Op_Root`, `Op_Chair` (swivel seat), `Op_Body`, `Op_Pelvis`, `Op_Spine`, `Op_Chest`, `Op_Head`.
  - Arms: `Op_UpperArm_L/R`, `Op_Forearm_L/R`, `Op_Hand_L/R`.
  - Legs: `Op_Thigh_L/R`, `Op_Shin_L/R`, `Op_Foot_L/R`.
  - The static deck is weighted 100% to `Op_Root`, so the whole asset is one draw per material.
- Extensions: `KHR_mesh_quantization` and `EXT_meshopt_compression` only.
  - No Draco, no images, no transmission, clearcoat or ior.
- Packed with `gltfpack -cc -kn -ke -ac`. `-ac` keeps constant tracks, so every clip keys all 38 channels and crossfades never drop a bone back to bind pose.
- Units are metres, +Y up, front is +Z.
  - Deck top is at y 2.2. The footprint is about 2.8 x 2.9 m: the deck is x ±1.42, z −1.05..+1.05, plus the stair along the back edge (z −1.75).
  - The stair goes up along the back (−Z) side and lands at the rear-left gap in the rail.
- Deck contents:
  - Steel deck with tread plate, amber hazard band on the front fascia, cyan under-edge strips.
  - White top rails, mid rails and kick plates; 4 braced legs; under-deck power unit.
  - Console with a glowing monitor (haul-loop map with an amber truck dot) and a side screen; swivel chair.
  - Beacon mast and antenna.

## Clips (30 fps) and the chain
Play order: `op_sit_type` → `op_stand_walk_to_rail` → `op_watch_rail` → `op_walk_back_sit` → back to `op_sit_type`.

| clip | length | mode | what happens |
|---|---|---|---|
| `op_sit_type` | 4.0 s | loop (seamless) | Seated at the console, typing. Glances at the side screen (1.4–3.4 s) and reaches for the trackpad. |
| `op_stand_walk_to_rail` | 1.6 s | play once (LoopOnce + clampWhenFinished) | Swivels the chair (0–0.35 s), stands up (0.35–0.75 s), then takes 4 steps to the front rail (0.75–1.6 s). Hands settle on the rail. |
| `op_watch_rail` | 3.0 s | loop (seamless) | Hands on the rail, watching the haul road. The head sweeps left and right (`Op_Head` yaw +0.62 → −0.53 → 0 rad) with a slight weight sway. |
| `op_walk_back_sit` | 1.6 s | play once (LoopOnce + clampWhenFinished) | Takes 4 steps back (0–0.85 s), sits (0.85–1.25 s, the stand-up played in reverse), swivels back to the desk (1.25–1.6 s). |
| `op_cycle` | 10.2 s | loop | Test clip: all four clips chained once (4.0 + 1.6 + 3.0 + 1.6). |

- **Matching poses:**
  - The last frame of each clip is exactly the first frame of the next clip in the chain (max joint error ~1e-15).
  - Each looping clip (`op_sit_type`, `op_watch_rail`, `op_cycle`) ends on its own first frame.
  - So in-chain switches can be hard cuts or short crossfades (0.15–0.25 s) and nothing snaps.
- **Motion quality:**
  - Every pose change eases in and out (smootherstep).
  - Walks are footstep based: a planted foot never moves (measured slide ≤ 0.5 mm per frame), and swing feet travel on eased arcs.
  - Arm and leg IK never over-extends (max stretch 0.992).
- **Suggested driver** (three.js):
  - Loop `op_sit_type` 2–4 times, then play `op_stand_walk_to_rail` once.
  - Loop `op_watch_rail` while a truck is on the road (or for 1–3 loops), then play `op_walk_back_sit` once and return to `op_sit_type`.
  - Start each clip when the previous one finishes (`mixer` `finished` event, or after a whole number of loops).
- The root node `MineOperator` carries `extras.clip_chain` and `extras.head_bone`.

## Head tracking: `Op_Head` (for Coder)
`op_watch_rail` already contains a gentle head sweep. To make the operator follow the truck in code, override `Op_Head` after `mixer.update()` each frame:

```js
const head = op.getObjectByName('Op_Head');          // parent is Op_Chest
// truckPos: world position of the truck (e.g. the HT-04 body)
const p = head.parent.worldToLocal(truckPos.clone()).sub(head.position);
const yaw = THREE.MathUtils.clamp(Math.atan2(p.x, p.z), -1.2, 1.2);     // about local +Y, ±70°
const pitch = THREE.MathUtils.clamp(-Math.atan2(p.y, Math.hypot(p.x, p.z)), -0.35, 0.25);
head.quaternion.setFromEuler(new THREE.Euler(pitch, yaw, 0, 'YXZ'));    // ease toward it (slerp ~0.1/frame) for smooth turns
```

- At rest `Op_Head` looks along its local +Z, which is the operator's facing direction.
- Only apply the override during `op_watch_rail`. Fade it in and out over about 0.3 s at the clip edges, so the hand-off to `op_walk_back_sit` stays smooth.
- `Op_Head` also carries `extras.look_at` with this rule.

## Placement: `Operator_Deck` (Mine glTF coordinates)
- **position (14.0, 0.0, 1.2)**, **rotation quaternion [0, 0, 0, 1]** (yaw 0).
  - The deck front and the operator at the rail face +Z, toward the east hairpin of the haul road and the camera.
  - Place the GLB root (`MineOperator`) at this transform, as a sibling of the Mine root. Scale 1.
- The Mine GLB is not edited. Coder adds the marker or uses these numbers directly.
- **Clearances** (measured against the Mine GLB at HEAD and the haul-loop layout):
  - East hairpin, centre (9, 9) r 4.5, berm toe at r 7.3: nearest deck corner is 7.6 m from the centre, so it clears the toe.
  - North road and load bay (z 4.5, x ≤ 10): the deck is behind and east of it, so it never hides the truck at Path_Load (4.7, 0, 4.5).
  - `Dep_01` (8.65, 8.65) r 2.2 and `Dep_02` (−1.2, 10.4) r 1.05: more than 6 m away.
  - Tiers: Tier_12 (10.6, −9.11) is about 10 m away and Tier_05 (3.6, −4.36) about 11 m. There is no Mine geometry above 8 cm inside the footprint.
  - Haul road to the Refinery station: the Refinery is now its own station, one swipe right, and its road leaves the Mine's right edge. The stub runs from Road_Entry (13.5, 0, 9.0) toward +X along z 9.0, with its berm toe at z 6.2. The deck's nearest edge (front legs, z 2.25) is 3.9 m north of the toe, and the deck stands behind the road as seen from the camera, so the road and trucks leaving on it are never hidden.
  - The old dump stub and REFINERY_ANCHOR are gone (Mine layout 10/23), so nothing else is near the spot.
  - The ground at the spot is flat (−0.005 to −0.018). Leg footings sink 8 cm, so y 0 sits correctly.
- **Phone frame** (HEAD camera: Cam_Target (0.06, −2.36, 1.00), frame_w 37, distance 116.48, 38° vertical FOV, tilt −18°, focus box cy 380):
  - On 393x852 the whole asset projects to x 329–364, y 352–406. That is inside the frame, with 29 px to the right edge.
  - It is away from the tap circles (22 px radius). The Dep_01 circle at (295, 427) ends at x 317, which leaves 12 px to the deck box. Dep_02 (182, 434) is far away. The truck at Path_Load (248, 413) is uncovered.
  - The new +X road stub projects just below the deck box, at y 419–439 on 393x852 (berm toe to berm toe). The deck box ends at y 406, 13 px above it, so the deck does not cover it.
  - It reads as a small control tower beside the ore bin, looking over the east hairpin and the road out to the Refinery.
  - The phone proof is composited onto the committed Mine phone render. That render predates the road-stub re-route, which is still an uncommitted edit by the Mine job, so the old access road still shows at the bottom right of the proof.

## Rebuild
```bash
bash art/3d/props/mine_operator/_src/pack_mine_operator.sh /tmp/op/raw.glb art/3d/props/mine_operator/mine_operator_game.glb
# contact sheet
blender -b -P art/3d/props/mine_operator/_src/render_sheet.py -- /tmp/op/raw.glb /tmp/op/sheet 10 640
```
- Mine-view proofs: run `render_mine_view.py` as a hook inside the Mine phone build: concept_b_sleek.py, then build_mine.py `--mode phone`, with `OP_HOOK` exec'd just before the render. A copy of build_mine.py was used, so the Mine folder was not touched.
  - Phone: border-render the deck region at 64 samples and composite it onto the shipped Mine phone render.
  - Hero: 3840x2160 at 6 samples with denoising. It shows the committed Mine scene.

## Validation
- three.js GLTFLoader + MeshoptDecoder: 2 draws, 2,584 tris, 2 skinned primitives, 19 bones, 5 clips x 38 tracks, 0 images, no banned extensions.
- gltf-validator: 0 errors. Warnings only:
  - The skinned mesh is not at the root, which is harmless in three.js.
  - The validator does not support meshopt decoding.
