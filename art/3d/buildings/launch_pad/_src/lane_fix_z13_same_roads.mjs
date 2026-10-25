// proof: every node except Crane/Crane_Mesh/crane_target extras is identical to a257d930 (TRS + extras), and Road_UTurn geometry is identical after decode
import fs from 'fs'; import { NodeIO } from '@gltf-transform/core'; import { ALL_EXTENSIONS } from '@gltf-transform/extensions'; import { MeshoptDecoder } from 'meshoptimizer'; await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
const [A, B, OUT] = process.argv.slice(2); const a = await io.read(A), b = await io.read(B); const out = { a: A, b: B, differ: [], same: 0 };
const nb = new Map(b.getRoot().listNodes().map(n => [n.getName(), n]));
for (const n of a.getRoot().listNodes()) { const m = nb.get(n.getName()); if (!m) { out.differ.push(n.getName() + ' missing'); continue; }
  const ta = JSON.stringify([n.getTranslation(), n.getRotation(), n.getScale()]), tb = JSON.stringify([m.getTranslation(), m.getRotation(), m.getScale()]);
  const ea = { ...n.getExtras() }, eb = { ...m.getExtras() }; delete ea.crane_solve; delete eb.crane_solve; if (ea.baked_clips) { delete ea.baked_clips; delete eb.baked_clips; }
  if (ta !== tb || JSON.stringify(ea) !== JSON.stringify(eb)) out.differ.push(n.getName() + (ta !== tb ? ' TRS' : ' extras')); else out.same++; }
const geo = (d, nm) => { const mesh = d.getRoot().listNodes().find(x => x.getName() === nm).listChildren()[0].getMesh(); return mesh.listPrimitives().map(p => ({ v: p.getAttribute('POSITION').getCount(), pos: Array.from(p.getAttribute('POSITION').getArray()).join(','), idx: Array.from(p.getIndices().getArray()).join(',') })); };
const ga = geo(a, 'Road_UTurn'), gb = geo(b, 'Road_UTurn'); out.road_uturn = { verts: ga.map(x => x.v), identical: ga.length === gb.length && ga.every((x, i) => x.pos === gb[i].pos && x.idx === gb[i].idx) };
console.log(JSON.stringify(out)); fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
