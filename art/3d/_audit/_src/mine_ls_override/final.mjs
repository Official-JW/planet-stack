import fs from 'fs';
import { mineScene, lsScene, dockScene, report, bbox, SIZES } from './ovr.mjs';
const out = {};
const sc = { mine: await mineScene(), ls: await lsScene() };
const cur = { mine: { x: 160.62, y: 6.0, z: 17.72, fw: 37.6 }, ls: { x: 0, y: -3.1, z: -12.5, fw: 46 } };
const env = { mine: 'mine', ls: 'lifesupport' }, base = { mine: 'mine_base', ls: 'ls_base' };
function vmin(S, T, fw) { const r = report(S, T, fw); return Math.min(...Object.values(r.sizes).map(s => Math.min(s.spare.top, s.spare.bottom))); }
function allmin(S, T, fw) { return report(S, T, fw).min; }
for (const k of ['mine', 'ls']) { const S = sc[k], c = cur[k], TGT = +(process.argv[2] || 9);
  const bestY = (fw) => { let lo = c.y - 15, hi = c.y + 15; for (let i = 0; i < 60; i++) { const a = lo + (hi - lo) / 3, b = hi - (hi - lo) / 3; if (vmin(S, { x: c.x, y: a, z: c.z }, fw) < vmin(S, { x: c.x, y: b, z: c.z }, fw)) lo = a; else hi = b; } return (lo + hi) / 2; };
  let lo = c.fw * .7, hi = c.fw * 1.6; for (let i = 0; i < 40; i++) { const m = (lo + hi) / 2; const y = bestY(m); if (allmin(S, { x: c.x, y, z: c.z }, m) >= TGT) hi = m; else lo = m; }
  const fw = Math.ceil(hi * 10) / 10, y = Math.round(bestY(fw) * 100) / 100; const T = { x: c.x, y, z: c.z };
  const r = report(S, T, fw), r0 = report(S, { x: c.x, y: c.y, z: c.z }, c.fw);
  const size = SIZES.map(s => { const k2 = s.w + 'x' + s.h; const n = r.sizes[k2].groups, o = r0.sizes[k2].groups;
    return { size: k2, env_new: [n[env[k]].w, n[env[k]].h], env_cur: [o[env[k]].w, o[env[k]].h], base_new: [n[base[k]].w, n[base[k]].h], base_cur: [o[base[k]].w, o[base[k]].h], ratio: +(n[env[k]].w / o[env[k]].w).toFixed(4), d_new: r.sizes[k2].d, d_cur: r0.sizes[k2].d }; });
  out[k] = { T_world: T, ct_local: { x: +(c.x - (k === 'mine' ? 160 : 0)).toFixed(2), y, z: c.z }, fw, min: r.min, spare: Object.fromEntries(Object.entries(r.sizes).map(([a, q]) => [a, q.spare])), groups: Object.fromEntries(Object.entries(r.sizes).map(([a, q]) => [a, Object.fromEntries(Object.entries(q.groups).map(([g, x]) => [g, x.spare]))])), current: { T: c, min: r0.min, spare: Object.fromEntries(Object.entries(r0.sizes).map(([a, q]) => [a, q.spare])) }, size };
  console.log(k, JSON.stringify(out[k], null, 1)); }
fs.writeFileSync('final.json', JSON.stringify(out, null, 1));
