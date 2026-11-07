# Art cleanup manifest (candidate only)

Prepared 11/07/2026. Nothing in this list has been deleted. Removals wait for Jacob to approve the exact paths.

Scope is served copies of the v1 Mine click-rock payload, superseded Mine and Refinery building GLBs, and old launch-pad / hold door GLBs. `art/` source, proofs, `preview/`, and backups are out of scope and are not deletion candidates.

Search, 11/07 on this branch:

- Text: `rg` over `dev/`, `live/`, `qa3d/`, `qa3d-next/`, and the rest of the repo, for each filename, its stem, and (where they differ) the content md5. Types checked: `.js`, `.html`, `.json`, `.md`, `.mjs`, `.css`, `.txt`.
- Inside every `.glb` / `.gltf` under those trees: the JSON chunk, including `"uri"` fields. These GLBs embed their buffers. No candidate name appears as an external texture or buffer URI inside another GLB.
- Dynamic loads: no template or concatenated path builds `mine_`, `refinery_`, `launch_pad_`, or `part_hold_` filenames. The only `` `...door...` `` hits are `Gear_Door_${...}` bone names inside the ship gear code (`dev/main.js` ~2975, and the same line in `live/`, `qa3d-next/`). That does not select a file.

Groups:

- **KEEP** — an uncommented load in `dev/main.js`, `live/main.js`, `qa3d/main.js`, or `qa3d-next/main.js`, or the file that load resolves to. Do not delete.
- **PARK** — comment, doc, art script, or measurement script still names it; or it is a byte-identical copy under `live/models/` of a file those mains load from `qa3d-next/models/`. Not proposed for deletion.
- **SAFE** — no reference in the search above, and not the file any of those mains load. Still inside `qa3d/models/`. `qa3d/main.js` does not load them. Listed so Jacob can approve or reject them one by one.

`live/main.js` and `qa3d-next/main.js` load `../qa3d-next/models/...`. The same basename under `live/models/` is not that path. Those copies are PARK, not SAFE, and this manifest does not propose deleting anything `live/` or `qa3d/` actually loads.

## v1 Mine click rock

There is no standalone rock GLB. The click rock is `Deposit_01` / `Deposit_02` with materials `SHM_DepositRock` and `SHM_DepositGlow`, embedded in the Mine building GLBs that have those strings below. `dev/main.js` `stripClickRock` detaches those nodes after `mine_revamp_c9a9394e.glb` loads. The bytes are still in that KEEP file, so deleting only the SAFE mines does not remove the rock from what dev serves.

Older `qa3d/models/mine_*.glb` files that only say `Dep_01` have the empty marker, not the Deposit rock meshes.

## KEEP

18 files. Referenced by an uncommented load.

### `qa3d-next/models/mine_revamp_c9a9394e.glb`

- Group: **KEEP**
- Size: 132396 bytes
- md5: `c9a9394e3635f99f59423a4630ae6ae7`
- Embedded rock strings in this GLB JSON: Deposit_01,Deposit_02,SHM_DepositRock,SHM_DepositGlow,Dep_01
- Evidence: dev/main.js:287 uncommented MINE_GLB. Also contains Deposit_01/_02 and SHM_DepositRock/Glow. dev stripClickRock removes those nodes at runtime; the file is still the Mine that dev serves.

### `qa3d-next/models/mine_cap_fix_v2_a60eae4b.glb`

- Group: **KEEP**
- Size: 144056 bytes
- md5: `a60eae4b9b7195aba5ffbbe86b8a163a`
- Embedded rock strings in this GLB JSON: Deposit_01,Deposit_02,SHM_DepositRock,SHM_DepositGlow,Dep_01
- Evidence: live/main.js:286 and qa3d-next/main.js:75 uncommented MINE_GLB. dev/main.js only names it in the was-comment on line 287. Contains the v1 Deposit rock.

### `qa3d-next/models/refinery_efdf3850.glb`

- Group: **KEEP**
- Size: 279616 bytes
- md5: `efdf3850a8c78827509c76618d86a642`
- Embedded rock strings in this GLB JSON: none
- Evidence: dev/main.js:290 uncommented REFINERY_GLB. No other main assigns it.

### `qa3d-next/models/refinery_22f13a9d.glb`

- Group: **KEEP**
- Size: 250116 bytes
- md5: `22f13a9d3777a0b94b63946a618ccc84`
- Embedded rock strings in this GLB JSON: none
- Evidence: live/main.js:289 and qa3d-next/main.js:78 uncommented REFINERY_GLB. dev/main.js:290 names it only in the was-comment.

### `qa3d-next/models/refinery_bridge_5d862767.glb`

- Group: **KEEP**
- Size: 72920 bytes
- md5: `5d8627679407b5b3009a43fc53e11453`
- Embedded rock strings in this GLB JSON: none
- Evidence: dev/main.js:854, live/main.js:813, qa3d-next/main.js:510 uncommented BRIDGE_GLB.

### `qa3d-next/models/mine_terrain_v3b_a4a2a4d2.glb`

- Group: **KEEP**
- Size: 1189136 bytes
- md5: `a4a2a4d2cb67f89310f34005a9a40057`
- Embedded rock strings in this GLB JSON: none
- Evidence: dev/main.js:1009, live/main.js:881, qa3d-next/main.js:578 uncommented MINE_TERRAIN_GLB. Scenic Rock_S/Rock_M live in this mesh, not the click rock.

### `qa3d-next/models/refinery_terrain_v3_6e24037a.glb`

- Group: **KEEP**
- Size: 1306660 bytes
- md5: `6e24037ab044040933a7239d8a4bf810`
- Embedded rock strings in this GLB JSON: none
- Evidence: dev/main.js:1022 and live/main.js:894 uncommented REF_TERRAIN_GLB.

### `qa3d-next/models/launch_pad_middoor_119efbb7.glb`

- Group: **KEEP**
- Size: 303396 bytes
- md5: `119efbb75a64e6c6643e2c701c8d2fb5`
- Embedded rock strings in this GLB JSON: none
- Evidence: dev/main.js:2940 and live/main.js:2525 uncommented PAD_GLB (current mid cargo door).

### `qa3d-next/models/launch_pad_door2_c404636f.glb`

- Group: **KEEP**
- Size: 318640 bytes
- md5: `c404636fad25064e99c78d7991618460`
- Embedded rock strings in this GLB JSON: none
- Evidence: qa3d-next/main.js:1982 uncommented PAD_GLB. dev/main.js:2941 and live/main.js:2526 keep the same path commented out.

### `qa3d-next/models/part_hold_lv1_middoor_trimstrip_0fe2092a.glb`

- Group: **KEEP**
- Size: 8640 bytes
- md5: `0fe2092abdd7fecc31474fe52a0ea31a`
- Embedded rock strings in this GLB JSON: none
- Evidence: dev/main.js:2951 and live/main.js:2536 uncommented HOLD_GLB.

### `qa3d-next/models/part_hold_lv1_18b5cc6c.glb`

- Group: **KEEP**
- Size: 9228 bytes
- md5: `18b5cc6c9a5411f23e163b6aeaa8cbea`
- Embedded rock strings in this GLB JSON: none
- Evidence: qa3d-next/main.js:1992 uncommented HOLD_GLB. dev/main.js:2952 and live/main.js:2537 keep it commented.

### `qa3d/models/mine_2123a050.glb`

- Group: **KEEP**
- Size: 127620 bytes
- md5: `2123a050afc6861ca4d368089a3b3735`
- Embedded rock strings in this GLB JSON: Dep_01
- Evidence: qa3d/main.js:43 uncommented MINE_GLB (models/mine_2123a050.glb). dev/live/qa3d-next only mention it in a comment.

### `qa3d/models/refinery_b45b4649.glb`

- Group: **KEEP**
- Size: 229640 bytes
- md5: `b45b46499f8d11f0a02c78a2644b2c3f`
- Embedded rock strings in this GLB JSON: none
- Evidence: qa3d/main.js:44 uncommented REFINERY_GLB. Later mains only name b45b4649 inside was-comments.

### `qa3d/models/launch_pad_a82251e2.glb`

- Group: **KEEP**
- Size: 291024 bytes
- md5: `a82251e2e254f745237bd2591ba3e141`
- Embedded rock strings in this GLB JSON: none
- Evidence: qa3d/main.js:1309 uncommented PAD_GLB.

### `qa3d/models/mine_operator_9209246.glb`

- Group: **KEEP**
- Size: 89332 bytes
- md5: `2cfa57a6ec0ad8e9ca566a4e068b2310`
- Embedded rock strings in this GLB JSON: none
- Evidence: qa3d/main.js:402, live/main.js:1021, qa3d-next and dev load models/mine_operator_9209246.glb (base href resolves into qa3d/models/). Not the click rock.

### `qa3d/models/crane_refinery_755815ec.glb`

- Group: **KEEP**
- Size: 44744 bytes
- md5: `755815ece8a48363e6770986944bb77e`
- Embedded rock strings in this GLB JSON: none
- Evidence: dev, live, qa3d, qa3d-next uncommented CRANE_ART url models/crane_refinery_755815ec.glb. Base href serves this qa3d copy.

### `qa3d/models/crane_refinery_d98f602c.glb`

- Group: **KEEP**
- Size: 43932 bytes
- md5: `d98f602c8f8c864eb8634efff217c567`
- Embedded rock strings in this GLB JSON: none
- Evidence: Same four mains: CRANE_ART_D98F602C url, selected by ?crane=d98f602c.

### `qa3d/models/crane_refinery_d1e577ce.glb`

- Group: **KEEP**
- Size: 43924 bytes
- md5: `d1e577cef71f825d79162b107d6e16fc`
- Embedded rock strings in this GLB JSON: none
- Evidence: Same four mains: CRANE_ART_AFFEA57 url, selected by ?crane=affea57.

## SAFE

3 files. No reference found. Approval still required before any delete.

### `qa3d/models/mine_8a0bfe6.glb`

- Group: **SAFE**
- Size: 126932 bytes
- md5: `699164bb3b613bc1d7f02146fdb627de`
- Embedded rock strings in this GLB JSON: Dep_01
- Evidence: No hit for the filename, the stem 8a0bfe6, or content md5 699164bb in any .js/.html/.json/.md/.mjs/.css/.txt. No .glb/.gltf JSON uri or embedded name. qa3d/main.js loads mine_2123a050, not this file. GLB JSON has a Dep_01 marker string and no SHM_DepositRock / Deposit_01 mesh name.

### `qa3d/models/mine_99c72d9.glb`

- Group: **SAFE**
- Size: 179192 bytes
- md5: `0dcb9ef5048f828a2b43223bde1ee646`
- Embedded rock strings in this GLB JSON: Dep_01
- Evidence: No hit for mine_99c72d9, stem 99c72d9, or content md5 0dcb9ef5 in those text types, and none inside .glb/.gltf JSON. Not assigned by qa3d, live, dev, or qa3d-next. GLB JSON has Dep_01 only.

### `qa3d/models/mine_9ff63d9.glb`

- Group: **SAFE**
- Size: 176548 bytes
- md5: `a3ed7e1f1fa6440e51551a1a2a898585`
- Embedded rock strings in this GLB JSON: Dep_01
- Evidence: No hit for mine_9ff63d9, stem 9ff63d9, or content md5 a3ed7e1f in those text types, and none inside .glb/.gltf JSON. Not assigned by any main. GLB JSON has Dep_01 only.

## PARK

24 files. Uncertain, comment-only, script-referenced, or a live/ duplicate of a qa3d-next load.

### `live/models/launch_pad_5fcd4d67.glb`

- Group: **PARK**
- Size: 344940 bytes
- md5: `5fcd4d67c1bb3094d136dd8003bf9e7d`
- Embedded rock strings in this GLB JSON: none
- Evidence: Not the path live/main.js fetches (that path is under qa3d-next/models/). Filename or hash still appears in comments and/or the twin is an active load. Byte-identical to `qa3d-next/models/launch_pad_5fcd4d67.glb` (md5 5fcd4d67c1bb3094d136dd8003bf9e7d). This manifest does not propose deleting this live/ copy.

### `live/models/launch_pad_82131aba.glb`

- Group: **PARK**
- Size: 307220 bytes
- md5: `82131abae3a8e97427635fd2513155fa`
- Embedded rock strings in this GLB JSON: none
- Evidence: Not the path live/main.js fetches (that path is under qa3d-next/models/). Filename or hash still appears in comments and/or the twin is an active load. Byte-identical to `qa3d-next/models/launch_pad_82131aba.glb` (md5 82131abae3a8e97427635fd2513155fa). This manifest does not propose deleting this live/ copy.

### `live/models/launch_pad_db78a6f7.glb`

- Group: **PARK**
- Size: 346844 bytes
- md5: `db78a6f71c35df8753958a51c4d7e349`
- Embedded rock strings in this GLB JSON: none
- Evidence: Not the path live/main.js fetches (that path is under qa3d-next/models/). Filename or hash still appears in comments and/or the twin is an active load. Byte-identical to `qa3d-next/models/launch_pad_db78a6f7.glb` (md5 db78a6f71c35df8753958a51c4d7e349). This manifest does not propose deleting this live/ copy.

### `live/models/launch_pad_door2_c404636f.glb`

- Group: **PARK**
- Size: 318640 bytes
- md5: `c404636fad25064e99c78d7991618460`
- Embedded rock strings in this GLB JSON: none
- Evidence: Not the path live/main.js fetches (that path is under qa3d-next/models/). Filename or hash still appears in comments and/or the twin is an active load. Byte-identical to `qa3d-next/models/launch_pad_door2_c404636f.glb` (md5 c404636fad25064e99c78d7991618460). This manifest does not propose deleting this live/ copy.

### `live/models/mine_864fab15.glb`

- Group: **PARK**
- Size: 122540 bytes
- md5: `864fab15769f3fa097da4ae8c97e3fc2`
- Embedded rock strings in this GLB JSON: Deposit_01,Deposit_02,SHM_DepositRock,SHM_DepositGlow,Dep_01
- Evidence: Not the path live/main.js fetches (that path is under qa3d-next/models/). Filename or hash still appears in comments and/or the twin is an active load. Byte-identical to `qa3d-next/models/mine_864fab15.glb` (md5 864fab15769f3fa097da4ae8c97e3fc2). This manifest does not propose deleting this live/ copy.

### `live/models/mine_cap_fix_v2_a60eae4b.glb`

- Group: **PARK**
- Size: 144056 bytes
- md5: `a60eae4b9b7195aba5ffbbe86b8a163a`
- Embedded rock strings in this GLB JSON: Deposit_01,Deposit_02,SHM_DepositRock,SHM_DepositGlow,Dep_01
- Evidence: Not the path live/main.js fetches (that path is under qa3d-next/models/). Filename or hash still appears in comments and/or the twin is an active load. Byte-identical to `qa3d-next/models/mine_cap_fix_v2_a60eae4b.glb` (md5 a60eae4b9b7195aba5ffbbe86b8a163a). This manifest does not propose deleting this live/ copy.

### `live/models/mine_ef45f6f1.glb`

- Group: **PARK**
- Size: 134884 bytes
- md5: `ef45f6f1f5744ee45379349de81af7d3`
- Embedded rock strings in this GLB JSON: Deposit_01,Deposit_02,SHM_DepositRock,SHM_DepositGlow,Dep_01
- Evidence: Not the path live/main.js fetches (that path is under qa3d-next/models/). Filename or hash still appears in comments and/or the twin is an active load. Byte-identical to `qa3d-next/models/mine_ef45f6f1.glb` (md5 ef45f6f1f5744ee45379349de81af7d3). This manifest does not propose deleting this live/ copy.

### `live/models/mine_terrain_v3b_a4a2a4d2.glb`

- Group: **PARK**
- Size: 1189136 bytes
- md5: `a4a2a4d2cb67f89310f34005a9a40057`
- Embedded rock strings in this GLB JSON: none
- Evidence: Not the path live/main.js fetches (that path is under qa3d-next/models/). Filename or hash still appears in comments and/or the twin is an active load. Byte-identical to `qa3d-next/models/mine_terrain_v3b_a4a2a4d2.glb` (md5 a4a2a4d2cb67f89310f34005a9a40057). This manifest does not propose deleting this live/ copy.

### `live/models/part_hold_lv1_18b5cc6c.glb`

- Group: **PARK**
- Size: 9228 bytes
- md5: `18b5cc6c9a5411f23e163b6aeaa8cbea`
- Embedded rock strings in this GLB JSON: none
- Evidence: Not the path live/main.js fetches (that path is under qa3d-next/models/). Filename or hash still appears in comments and/or the twin is an active load. Byte-identical to `qa3d-next/models/part_hold_lv1_18b5cc6c.glb` (md5 18b5cc6c9a5411f23e163b6aeaa8cbea). This manifest does not propose deleting this live/ copy.

### `live/models/refinery_22f13a9d.glb`

- Group: **PARK**
- Size: 250116 bytes
- md5: `22f13a9d3777a0b94b63946a618ccc84`
- Embedded rock strings in this GLB JSON: none
- Evidence: Not the path live/main.js fetches (that path is under qa3d-next/models/). Filename or hash still appears in comments and/or the twin is an active load. Byte-identical to `qa3d-next/models/refinery_22f13a9d.glb` (md5 22f13a9d3777a0b94b63946a618ccc84). This manifest does not propose deleting this live/ copy.

### `live/models/refinery_93c44166.glb`

- Group: **PARK**
- Size: 265392 bytes
- md5: `93c44166ecc39031966a9be130dfc093`
- Embedded rock strings in this GLB JSON: none
- Evidence: Not the path live/main.js fetches (that path is under qa3d-next/models/). Filename or hash still appears in comments and/or the twin is an active load. Byte-identical to `qa3d-next/models/refinery_93c44166.glb` (md5 93c44166ecc39031966a9be130dfc093). This manifest does not propose deleting this live/ copy.

### `live/models/refinery_bridge_5d862767.glb`

- Group: **PARK**
- Size: 72920 bytes
- md5: `5d8627679407b5b3009a43fc53e11453`
- Embedded rock strings in this GLB JSON: none
- Evidence: Not the path live/main.js fetches (that path is under qa3d-next/models/). Filename or hash still appears in comments and/or the twin is an active load. Byte-identical to `qa3d-next/models/refinery_bridge_5d862767.glb` (md5 5d8627679407b5b3009a43fc53e11453). This manifest does not propose deleting this live/ copy.

### `qa3d-next/models/launch_pad_1042e767.glb`

- Group: **PARK**
- Size: 349160 bytes
- md5: `1042e76793da1f97a9837a4a823873f0`
- Embedded rock strings in this GLB JSON: none
- Evidence: Commented PAD_GLB in dev/main.js:2944, live/main.js:2529, qa3d-next/main.js:1985. Hash 1042e767 also appears in ship-fit comments.

### `qa3d-next/models/launch_pad_5fcd4d67.glb`

- Group: **PARK**
- Size: 344940 bytes
- md5: `5fcd4d67c1bb3094d136dd8003bf9e7d`
- Embedded rock strings in this GLB JSON: none
- Evidence: Commented PAD_GLB in dev/main.js:2943, live/main.js:2528, qa3d-next/main.js:1984. Also named inside the door2 comment as the pad that door2 was built from.

### `qa3d-next/models/launch_pad_82131aba.glb`

- Group: **PARK**
- Size: 307220 bytes
- md5: `82131abae3a8e97427635fd2513155fa`
- Embedded rock strings in this GLB JSON: none
- Evidence: Named in the commented was-chain (dev/main.js:2944). art/3d/buildings/launch_pad/proofs/ship_look_door.json:58 and :111 list models/launch_pad_82131aba.glb.

### `qa3d-next/models/launch_pad_db78a6f7.glb`

- Group: **PARK**
- Size: 346844 bytes
- md5: `db78a6f71c35df8753958a51c4d7e349`
- Embedded rock strings in this GLB JSON: none
- Evidence: Named in the commented was-chain. art measurement scripts and transport_road_plan.json name qa3d-next/models/launch_pad_db78a6f7.glb.

### `qa3d-next/models/mine_864fab15.glb`

- Group: **PARK**
- Size: 122540 bytes
- md5: `864fab15769f3fa097da4ae8c97e3fc2`
- Embedded rock strings in this GLB JSON: Deposit_01,Deposit_02,SHM_DepositRock,SHM_DepositGlow,Dep_01
- Evidence: Not an uncommented load. dev/main.js:287, live/main.js:286, and qa3d-next/main.js:75 name it in the was-comment on the active MINE_GLB line. Contains SHM_DepositRock. Identical md5 to live/models/mine_864fab15.glb.

### `qa3d-next/models/mine_ef45f6f1.glb`

- Group: **PARK**
- Size: 134884 bytes
- md5: `ef45f6f1f5744ee45379349de81af7d3`
- Embedded rock strings in this GLB JSON: Deposit_01,Deposit_02,SHM_DepositRock,SHM_DepositGlow,Dep_01
- Evidence: Comment-only (same was-chain as 864fab15). Contains SHM_DepositRock. Identical md5 to the live/models copy.

### `qa3d-next/models/refinery_93c44166.glb`

- Group: **PARK**
- Size: 265392 bytes
- md5: `93c44166ecc39031966a9be130dfc093`
- Embedded rock strings in this GLB JSON: none
- Evidence: Not the live/dev load. Named in was-comments (dev/main.js:290, live/main.js:289). art/3d/vehicles/ship_transporter/_src/measure_stations.mjs:12 still points a measurement script at qa3d-next/models/refinery_93c44166.glb.

### `qa3d/models/mine_219e774.glb`

- Group: **PARK**
- Size: 126600 bytes
- md5: `835e87f521c98cf242d19aa67fd63610`
- Embedded rock strings in this GLB JSON: Dep_01
- Evidence: Comment only: qa3d/main.js:43 and dev/main.js:289 say previous models/mine_219e774.glb. Content md5 is 835e87f5, which does not match the filename token. Dep_01 marker, no SHM_DepositRock.

### `qa3d/models/mine_582676b.glb`

- Group: **PARK**
- Size: 125708 bytes
- md5: `68e07c01c0e8025a73f81c8e15484553`
- Embedded rock strings in this GLB JSON: Dep_01
- Evidence: Filename token 582676b and content md5 68e07c01 are in header and Mine-section comments in dev/main.js:1 and :872, and the same comments in live, qa3d, and qa3d-next. No loader assigns this path. Dep_01 marker, no SHM_DepositRock.

### `qa3d/models/refinery_0358ffa.glb`

- Group: **PARK**
- Size: 225892 bytes
- md5: `41ac6c5a246c29bf75c75f4879622b9f`
- Embedded rock strings in this GLB JSON: none
- Evidence: Comments only: dev/main.js:297 and :711 (and the same lines in live, qa3d, qa3d-next) say Refinery GLB 0358ffa, md5 41ac6c5a, which is this file’s content md5. qa3d loads refinery_b45b4649 instead.

### `qa3d/models/refinery_4a70acf.glb`

- Group: **PARK**
- Size: 224044 bytes
- md5: `d1178fd768121029aaa577ff1abc0919`
- Embedded rock strings in this GLB JSON: none
- Evidence: Header comment in dev/main.js:2, live, qa3d, and qa3d-next: “Art's Refinery (4a70acf)”. No assignment of this path. Content md5 is d1178fd7.

### `qa3d/models/refinery_bb5eed2.glb`

- Group: **PARK**
- Size: 224812 bytes
- md5: `e65968d7f1b567c1155e0ff90e42854a`
- Embedded rock strings in this GLB JSON: none
- Evidence: Comment only: qa3d/main.js:44 and dev/main.js:291 previous models/refinery_bb5eed2.glb. Content md5 e65968d7 does not match the filename token.

## Counts

| Group | Count |
|---|---|
| KEEP | 18 |
| SAFE | 3 |
| PARK | 24 |
| Candidates in this manifest | 45 |

SAFE paths:

- `qa3d/models/mine_8a0bfe6.glb`
- `qa3d/models/mine_99c72d9.glb`
- `qa3d/models/mine_9ff63d9.glb`
