# Receiver astronaut (`receiver_game.glb`)

The ground hand at the Refinery cargo hand-off. He walks out of the airlock, marshals the flatbed/crane, checks the box in on his wrist pad, and walks back. I built him on the **Mine operator rig and suit** (`art/3d/props/mine_operator`, commit `9209246`): same `Op_*` joints, geometry helpers, IK solver and GLB writer. The deck and `Op_Chair` are removed and he stands on the ground (DH = 0).

| | |
|---|---|
| File | `receiver_game.glb`: **60,324 B**, md5 `8c49ee3168cc513558207d93e0c9b249`, meshopt + quantization (`gltfpack -cc -kn -ke -ac`), no Draco, no images |
| Budget | **1,126 tris / 2 draws** (SHM_Paint + SHM_GlowCyan) on one skin. Limit ≤3k / ≤2 |
| Root | `Receiver`. Origin = `Receive_Point` on the ground; he faces +Z while guiding |
| Default pose | `guide` frame 0 |

## Joints (18, all from the operator rig)
`Op_Root` → `Op_Body` → `Op_Pelvis` → `Op_Spine` → `Op_Chest` → `Op_Head`, `Op_UpperArm_L/R` → `Op_Forearm_L/R` → `Op_Hand_L/R`; `Op_Pelvis` → `Op_Thigh_L/R` → `Op_Shin_L/R` → `Op_Foot_L/R`.
`Op_Head` extras: `look_at`. Yaw it about local +Y toward the truck or crane (clamp to about ±70°); at rest it looks along body +Z. The clips don't key head yaw beyond the body motion, so Coder can add it on top.

## Markers (asset-local glTF)
| Empty | Position | Use |
|---|---|---|
| `Receive_Point` | (0, 0, 0) | where he stands for `guide` + `check_in` (feet centred, facing +Z); `walk_out` ends here, `walk_back` starts here |
| `Home_Point` | (−3, 0, −1.5), yaw 1.107 rad | airlock/door spot: `walk_out` starts and `walk_back` ends here, facing Receive_Point |

Place the root so Receive_Point sits where he should stand. The walk is baked as root motion inside the clips: the `Receiver` node never moves, and the body travels between Home_Point and Receive_Point. The Home_Point offset then has to land on walkable ground. In the crane proofs he stands in the median at world (316.5, 0, 17.1), yaw 180°, facing FB-05 on the z 13 lane. That is crane-local (5.5, 0, −0.4) with the crane root at (311, 0, 17.5). That puts Home_Point at world (319.5, 18.6), clear of the pedestal (x ≤ 312.7), the pallet and the lanes. That placement is only a suggestion; the airlock location is the Director's call.

## Clips (30 fps; chain walk_out → guide (loop) → check_in → walk_back → walk_out)
| Clip | Duration | Content |
|---|---|---|
| `walk_out` | **4.0 s** | 10-step walk Home → Receive (3.4 s), turn to face +Z, raise the arms into the guide pose |
| `guide` | **2.0 s, loop** | marshalling "come ahead" beckon with both arms, weight shift |
| `check_in` | **2.0 s** | left forearm raised to read the wrist pad; the right glove taps it at 0.82 s and 1.18 s; ends back in the guide pose |
| `walk_back` | **4.4 s** | walk Receive → Home (3.4 s), then a 3-step 180° turn on the spot so the last frame equals `walk_out` frame 0 |

Root extras carry `clip_chain`, `home_point` and `home_yaw_rad`.

## Verified in three r186 (GLTFLoader + MeshoptDecoder, `../../props/_shared_src/verify_props.mjs receiver`)
- Chain seams (end pose of one clip vs. start of the next, all joints): walk_out>guide 1e-5 m, guide>guide 0, guide>check_in 1e-5, check_in>walk_back 0, walk_back>walk_out 0. **No pops.**
- Planted-foot slide max: walk_out 0.9 mm, guide 0.8 mm, check_in 0, walk_back 1.1 mm (that's quantization). **No foot sliding.**
- Max joint step per frame: 0.123 / 0.016 / 0.110 / 0.118 m (a hand in a normal walk arm swing). Leg IK max stretch 0.984 (no knee snap). Ankle lift ≤ 0.15 m.

## Proofs
- `proofs/receiver_clips_sheet.png`: 4 clips × 6 frames (CPU Cycles, OIDN).
- In scene: `../../props/crane_refinery/proofs/crane_layout_*` (guide pose beside the truck).

## Rebuild
```
python3 _src/build_receiver.py /tmp/rx_raw.glb            # pure Python + numpy, deterministic
gltfpack -i /tmp/rx_raw.glb -o receiver_game.glb -cc -kn -ke -ac
node ../../props/_shared_src/verify_props.mjs receiver receiver_game.glb
blender -b -P _src/render_receiver_sheet.py -- ...         # sheet (needs gltfpack -noq unpack first)
```
