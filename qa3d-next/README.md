# qa3d-next — staging copy of qa3d/ for the next small build

Files here: `index.html`, `main.js`, `models/launch_pad_816f18f3.glb` (Art 62a5dcb) and `models/mine_cc084a9b.glb` (Art 12bdb4a). Those two GLBs are the only assets that differ from /qa3d/; they live here so /qa3d/ stays unchanged. Everything else loads from /qa3d/. `index.html` has `<base href="../qa3d/">`, so every relative URL
(CSS, `ui/`, the `vendor/` import map, `models/`, `audio/`, KTX2 transcoder) resolves to the shared `/qa3d/` files —
no models or audio are duplicated. The page loads its own script via `../qa3d-next/main.js`.

Differences from `qa3d/` (keep them this small so patches made against `qa3d/` apply here):
- index.html: the `<base>` line, `<title>`, `data-tag="QA3D-next · HH:MM"`, script src `../qa3d-next/main.js?v=next…`
- main.js: `SAVEKEY` = `planetstack-qa3d-next(-dev)` (own save; never touches /qa3d/'s save on the same origin), plus the build's changes.

Bring in a branch that edits `qa3d/` (e.g. Code Assistant's ca-fuel-gauge):

    git show <commit> -- qa3d/main.js qa3d/index.html | git apply -p2 --directory=qa3d-next

When this build is promoted, copy main.js/index.html back to qa3d/, revert the four index.html lines and SAVEKEY, move models/*.glb into qa3d/models/, and drop the "../qa3d-next/" prefix from PAD_GLB and MINE_GLB.

## Changes vs qa3d/ (this build)
- CAM_OVERRIDE: Mine cc084a9b (re-keyed from 2123a050) {ct.y 5.6, W 39.9}; Life Support e8427ec4 {ct.y -3.58, W 47.6}; Launch Pad 816f18f3 {ct (0,4,-0.7), W 78.25}.
- PAD_GLB = ../qa3d-next/models/launch_pad_816f18f3.glb (Art 62a5dcb, 15 draws).
- Fuel gauge from ca-fuel-gauge (11df18d, 785d9f7, 051e646).
- Offline cargo (Director 23:00): the ship never auto-launches during catch-up; a ship that fills while away waits (sh.man) for a Launch tap.
- MINE_GLB = ../qa3d-next/models/mine_cc084a9b.glb (Art 12bdb4a: Deposit_01/_02 nodes, 14 draws; 15 with the HT-04).
- Deposit fade on the real /^Deposit_\d+/ nodes, mapped through extras.marker: both materials cloned per node, opacity 0→1 over extras.fade_in_s (1.0 s, game clock), visible=false while used up. With no Deposit_ nodes, nothing fades and the baked patch stays. The old invisible stand-in fade has been removed.
