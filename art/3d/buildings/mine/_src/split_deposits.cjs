// 10/23 23:xx (Director): each deposit patch (dark ore rock decal + faint steady cyan veins) is split out of Base_Paint / Base_DepVein
// into its own node Deposit_01 / Deposit_02 (origin = the Dep_0N marker, geometry unchanged in world space) so the game can fade it in
// over 1 s when it becomes available and hide it while used up, without touching the building strips or the ground.
// Materials are SHARED across all Deposit nodes (code clones per node at runtime if it needs independent opacity):
//   SHM_DepositRock = copy of SHM_Paint (vertex colours), SHM_DepositGlow = the old SHM_DepVein (low STEADY emissive, no clip / pulse).
// Both alphaMode BLEND (alpha 1 -> looks opaque); nothing else in the file is BLEND. Primitive order per node: rock, then veins.
//   NODE_PATH=/home/box/apps/gltftools/node_modules node split_deposits.cjs raw_pruned.glb raw_split.glb [packed_pass1.glb]
// Pass 2 (packed_pass1.glb given): each Deposit origin is snapped onto gltfpack's position grid (read from pass 1, < 1.3 mm from the
// marker) so the re-packed deposit vertices quantize to exactly the same world positions as before the split (0 mm drift).
const { NodeIO } = require('@gltf-transform/core');
const { ALL_EXTENSIONS } = require('@gltf-transform/extensions');
const { MeshoptDecoder } = require('meshoptimizer');
const DEPS = [['Dep_01', 'Deposit_01'], ['Dep_02', 'Deposit_02']];
const PAD = 0.15;   // patch outer (base) ring = radius * 1.08 + 0.12
(async () => {
  const [inp, out, pass1] = process.argv.slice(2);
  await MeshoptDecoder.ready;
  const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
  let grid = null;
  if (pass1) { const q = (await io.read(pass1)).getRoot().listNodes().find(n => n.getName() === 'Base_Paint').listChildren()[0]; grid = { t: q.getTranslation(), s: q.getScale()[0] }; }
  const snap = c => grid ? c.map(v => Math.round(v / grid.s) * grid.s) : [...c];   // whole grid steps: local grid == world grid
  const doc = await io.read(inp); const root = doc.getRoot();
  const N = nm => { const n = root.listNodes().find(x => x.getName() === nm); if (!n) throw new Error('missing node ' + nm); return n; };
  const mine = N('Mine'), paintN = N('Base_Paint'), veinN = N('Base_DepVein');
  for (const n of [paintN, veinN]) if (n.getTranslation().some(v => v) || n.getRotation()[3] !== 1 || n.getScale().some(v => v !== 1)) throw new Error('expected identity ' + n.getName());
  const paintP = paintN.getMesh().listPrimitives(), veinP = veinN.getMesh().listPrimitives();
  if (paintP.length !== 1 || veinP.length !== 1) throw new Error('expected 1 prim');
  const matPaint = paintP[0].getMaterial(), matVein = veinP[0].getMaterial();
  const matRock = matPaint.clone().setName('SHM_DepositRock').setAlphaMode('BLEND').setExtras({ deposit: true, note: 'shared by all Deposit_* nodes; clone per node to fade one deposit alone' });
  matVein.setName('SHM_DepositGlow').setAlphaMode('BLEND').setExtras({ deposit: true, steady: true, note: 'faint steady cyan veins: no clip, no pulse, no animated emission; shared by all Deposit_* nodes' });
  const geo = DEPS.map(([mk]) => { const m = N(mk); const t = m.getTranslation(); return { c: snap(t), R: m.getExtras().radius_m * 1.08 + 0.12 + PAD, tri: { rock: [], vein: [] } }; });
  // split one primitive: returns the kept index list, assigns in-radius tris to deposits
  function split(prim, key) {
    const P = prim.getAttribute('POSITION'), I = prim.getIndices().getArray(), keep = []; const v = [0, 0, 0];
    for (let t = 0; t < I.length; t += 3) {
      const tri = [I[t], I[t + 1], I[t + 2]]; let hit = -1;
      geo.forEach((g, k) => { if (tri.every(i => { P.getElement(i, v); return Math.hypot(v[0] - g.c[0], v[2] - g.c[2]) < g.R; })) hit = k; });
      if (hit >= 0) geo[hit].tri[key].push(tri); else keep.push(tri);
    }
    return keep;
  }
  // new primitive from a vertex subset (positions shifted by -off); order of first use, so it stays deterministic
  function sub(prim, tris, off) {
    const map = new Map(); const order = [];
    const idx = tris.flat().map(i => { if (!map.has(i)) { map.set(i, order.length); order.push(i); } return map.get(i); });
    const np = doc.createPrimitive().setMode(prim.getMode()).setMaterial(prim.getMaterial());
    const buf = prim.getIndices().getBuffer();
    for (const s of prim.listSemantics()) {
      const a = prim.getAttribute(s), k = a.getElementSize(), src = a.getArray(), dst = new src.constructor(order.length * k);
      order.forEach((o, j) => { for (let q = 0; q < k; q++) dst[j * k + q] = src[o * k + q] - (s === 'POSITION' && off ? off[q] : 0); });
      np.setAttribute(s, doc.createAccessor().setType(a.getType()).setArray(dst).setNormalized(a.getNormalized()).setBuffer(buf));
    }
    np.setIndices(doc.createAccessor().setType('SCALAR').setArray(order.length > 65535 ? new Uint32Array(idx) : new Uint16Array(idx)).setBuffer(buf));
    return np;
  }
  const keepPaint = split(paintP[0], 'rock'), keepVein = split(veinP[0], 'vein');
  if (keepVein.length) throw new Error('vein tris outside every deposit: ' + keepVein.length);
  const oldPaint = paintP[0];
  // Base_Paint keeps every other triangle, vertex order preserved (unused patch vertices dropped)
  const used = new Set(keepPaint.flat()); const remap = new Map(); let j = 0;
  for (let i = 0; i < oldPaint.getAttribute('POSITION').getCount(); i++) if (used.has(i)) remap.set(i, j++);
  const ordered = [...remap.keys()];
  const np = doc.createPrimitive().setMode(oldPaint.getMode()).setMaterial(matPaint);
  for (const s of oldPaint.listSemantics()) {
    const a = oldPaint.getAttribute(s), k = a.getElementSize(), src = a.getArray(), dst = new src.constructor(ordered.length * k);
    ordered.forEach((o, jj) => { for (let q = 0; q < k; q++) dst[jj * k + q] = src[o * k + q]; });
    np.setAttribute(s, doc.createAccessor().setType(a.getType()).setArray(dst).setNormalized(a.getNormalized()).setBuffer(oldPaint.getIndices().getBuffer()));
  }
  np.setIndices(doc.createAccessor().setType('SCALAR').setArray(new Uint16Array(keepPaint.flat().map(i => remap.get(i)))).setBuffer(oldPaint.getIndices().getBuffer()));
  const rep = [];
  DEPS.forEach(([mk, dn], k) => {
    const g = geo[k];
    const mesh = doc.createMesh(dn + '_mesh').addPrimitive(sub(oldPaint, g.tri.rock, g.c).setMaterial(matRock)).addPrimitive(sub(veinP[0], g.tri.vein, g.c).setMaterial(matVein));
    const m = N(mk), ex = m.getExtras();
    const node = doc.createNode(dn).setTranslation([...g.c]).setMesh(mesh).setExtras({ deposit: true, fade_in_s: 1.0, marker: mk, radius_m: ex.radius_m, hide_when_used_up: true,
      materials: ['SHM_DepositRock', 'SHM_DepositGlow'], note: 'fade in over 1 s when the deposit becomes available (opacity 0 -> 1 on both primitives); hidden while it is used up. Veins are steady: no pulse.' });
    mine.addChild(node);
    m.setExtras({ ...ex, patch: `node ${dn} (origin = this marker): darker ore rock decal (SHM_DepositRock) + faint steady cyan veins (SHM_DepositGlow). Game fades ${dn} in over 1 s when available and hides it while used up`, glow: 'faint steady cyan veins only, no animation / pulse / flicker, no ring or disc' });
    rep.push({ node: dn, t: g.c, marker: m.getTranslation(), rockTris: g.tri.rock.length, veinTris: g.tri.vein.length });
  });
  paintN.getMesh().removePrimitive(oldPaint).addPrimitive(np); oldPaint.dispose();
  const vm = veinN.getMesh(); veinN.dispose(); vm.dispose();
  for (const a of root.listAccessors()) if (!a.listParents().some(p => p !== root)) a.dispose();
  await io.write(out, doc); console.log('SPLIT ->', out, JSON.stringify(rep));
})();
