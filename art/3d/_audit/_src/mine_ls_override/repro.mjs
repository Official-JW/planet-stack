import { mineScene, lsScene, dockScene, report } from './ovr.mjs';
const out = {};
for (const [k, f, ov] of [['mine', mineScene, null], ['ls', lsScene, { y: -3.1, fw: 46 }], ['dock', dockScene, { y: 2.5 }]]) {
  const S = await f(); const T = { x: S.ctW.x, y: ov && ov.y != null ? ov.y : S.ctW.y, z: S.ctW.z }; const fw = ov && ov.fw || S.fw;
  const r = report(S, T, fw); out[k] = { T, fw, ...r }; console.log('==', k, JSON.stringify(T), fw, 'min', r.min);
  for (const [sz, q] of Object.entries(r.sizes)) { console.log(' ', sz, 'spare', JSON.stringify(q.spare)); for (const [g, x] of Object.entries(q.groups)) console.log('    ', g, JSON.stringify(x.spare), 'w', x.w, 'h', x.h); } }
import fs from 'fs'; fs.writeFileSync('repro.json', JSON.stringify(out, null, 1));
