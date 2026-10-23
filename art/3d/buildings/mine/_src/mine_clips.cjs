// Mine GLB post-process + verification (gltf-transform core).
//   NODE_PATH=/home/box/apps/gltftools/node_modules node mine_clips.cjs prune raw.glb pruned.glb
//   NODE_PATH=/home/box/apps/gltftools/node_modules node mine_clips.cjs verify mine_game.glb
// prune: each clip keeps ONLY channels on its own parts, and drops channels that never leave the rest pose
// (Blender samples every bone of the armature for each action).
const { NodeIO } = require('@gltf-transform/core');
const { ALL_EXTENSIONS } = require('@gltf-transform/extensions');
const { prune } = require('@gltf-transform/functions');
const { MeshoptDecoder } = require('meshoptimizer');
const RAM = ['L', 'R'].flatMap(s => [`Truck_Ram_${s}`, `Truck_Ram_${s}_Stage2`, `Truck_Ram_${s}_Rod`]);
const WHEELS = [1, 2, 3, 4, 5, 6].map(i => `Truck_Wheel_0${i}`);
const ALLOW = {
  dig: ['Rig'], conveyor_run: ['Conveyor'], truck_drive: WHEELS, truck_dump: ['Truck_Bed', 'Truck_Load', ...RAM],
  chute_pour: [1, 2, 3, 4].map(i => `Truck_Pour_0${i}`), truck_load_rich: [1, 2, 3, 4, 5].map(i => `Truck_Rich_0${i}`),
};
const rest = (n, p) => p === 'translation' ? n.getTranslation() : p === 'rotation' ? n.getRotation() : n.getScale();
(async () => {
  const [mode, inp, out] = process.argv.slice(2);
  await MeshoptDecoder.ready;
  const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
  const doc = await io.read(inp); const root = doc.getRoot();
  if (mode === 'prune') {
    for (const a of root.listAnimations()) {
      const allow = ALLOW[a.getName()];
      if (!allow) { console.log('UNEXPECTED clip', a.getName()); continue; }
      for (const ch of a.listChannels()) {
        const n = ch.getTargetNode(), p = ch.getTargetPath(), out_ = ch.getSampler().getOutput().getArray();
        const k = out_.length / ch.getSampler().getInput().getCount();
        const r = rest(n, p); let moves = false;
        for (let i = 0; i < out_.length && !moves; i += k) for (let j = 0; j < k; j++) if (Math.abs(out_[i + j] - r[j]) > 1e-4 && !(p === 'rotation' && Math.abs(Math.abs(out_[i + j]) - Math.abs(r[j])) < 1e-4 && false)) { moves = true; break; }
        if (!allow.includes(n.getName()) || !moves) { ch.getSampler().dispose(); ch.dispose(); }
      }
    }
    await doc.transform(prune({ keepLeaves: true, keepAttributes: true, keepExtras: true }));
    await io.write(out, doc); console.log('PRUNED ->', out); return;
  }
  // verify
  let tris = 0, draws = 0; const rep = { meshes: [], clips: {}, nodes: [], extensions: root.listExtensionsUsed().map(e => e.extensionName), images: root.listTextures().length };
  for (const n of root.listNodes()) {
    const m = n.getMesh();
    if (m) for (const p of m.listPrimitives()) {
      const t = (p.getIndices() ? p.getIndices().getCount() : p.getAttribute('POSITION').getCount()) / 3; tris += t; draws++;
      rep.meshes.push({ node: n.getName(), tris: t, material: p.getMaterial() && p.getMaterial().getName(), extras: n.getExtras() });
    }
  }
  for (const a of root.listAnimations()) {
    const tg = {}; let dur = 0;
    for (const ch of a.listChannels()) { const nm = ch.getTargetNode().getName(); (tg[nm] = tg[nm] || []).push(ch.getTargetPath()); dur = Math.max(dur, ch.getSampler().getInput().getMax([0])[0]); }
    const allow = ALLOW[a.getName()] || []; const bad = Object.keys(tg).filter(n => !allow.includes(n));
    rep.clips[a.getName()] = { duration_s: +dur.toFixed(3), targets: tg, foreign_targets: bad };
  }
  for (const n of root.listNodes()) rep.nodes.push({ name: n.getName(), t: n.getTranslation().map(v => +v.toFixed(3)), r: n.getRotation().map(v => +v.toFixed(4)), extras: n.getExtras(), mesh: !!n.getMesh(), skin: !!n.getSkin() });
  for (const m of root.listMaterials()) rep.materials = (rep.materials || []).concat([{ name: m.getName(), ext: m.listExtensions().map(e => e.extensionName), emissive: m.getEmissiveFactor() }]);
  rep.tris = tris; rep.draws_all_tiers_visible = draws; rep.skins = root.listSkins().map(s => ({ joints: s.listJoints().map(j => j.getName()) }));
  console.log(JSON.stringify(rep, null, 1));
})();
