// Headless crew-nav check. Serves the repo, loads dev/ with ?mock=1&qa=1&fresh=1,
// code 00010, name "Nav QA", and samples every crew walk at bay counts 0 / 6 / 12.
//
//   NODE_PATH=/tmp/crewnav/node_modules node qa/crewnav-check.mjs --build unfixed --expect fail
//   NODE_PATH=/tmp/crewnav/node_modules node qa/crewnav-check.mjs --build fixed --expect pass
//
// --build unfixed fulfills dev/main.js from /tmp/unfixed-main.js (commit 74e7f02).
// --build fixed uses the working tree. --expect sets the exit code: 0 when the run
// matches, 1 when it does not, 2 on a harness crash.
//
// Seeding (dev/ ignores ?fresh=1 — Q strips it — so storage is cleared here too):
//   URL  /dev/index.html?mock=1&qa=1&fresh=1   (localhost, mock codes 00000–00010)
//   code 00010, player name "Nav QA", empty localStorage
//   camera driven to the Launch Pad (boarding only poses on-site)
//   per fill: S.cg.bay = 0|6|12, S.cg.dk = 0|10|20, S.cg.ref = 0|4|8 future stamps,
//   then __ps3d.poseNow() so the crates are in the frame before the walks.
// Walks are stepped at 1/20 game-second (not wall frames) by calling the game's own
// wkUpd / updCrew / brStep. A sample counts only while the body is on the ground
// (y < 2.6) and not parented to the truck. Margin is 0.15 m outside each rack or crate.

import { createServer } from 'node:http';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary', '.png': 'image/png', '.svg': 'image/svg+xml', '.mp3': 'audio/mpeg', '.woff2': 'font/woff2' };
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const BUILD = opt('--build', 'fixed');
const EXPECT = opt('--expect', BUILD === 'unfixed' ? 'fail' : 'pass');
const PORT = +opt('--port', '8765');
const UNFIXED = opt('--unfixed', '/tmp/unfixed-main.js');
const MARGIN = 0.15;
const DT = 1 / 20;

function serve() {
  const server = createServer((req, res) => {
    try {
      const url = new URL(req.url, 'http://127.0.0.1');
      let p = decodeURIComponent(url.pathname);
      if (p.endsWith('/')) p += 'index.html';
      if (BUILD === 'unfixed' && /\/dev\/main\.js$/.test(p)) {
        const buf = readFileSync(UNFIXED);
        res.writeHead(200, { 'content-type': 'text/javascript', 'cache-control': 'no-store' });
        res.end(buf); return;
      }
      const file = normalize(join(ROOT, p));
      if (!file.startsWith(normalize(ROOT))) { res.writeHead(403); res.end(); return; }
      const buf = readFileSync(file);
      res.writeHead(200, { 'content-type': MIME[extname(file)] || 'application/octet-stream', 'cache-control': 'no-store' });
      res.end(buf);
    } catch (e) { res.writeHead(404); res.end(String(e.code || e.message)); }
  });
  return new Promise(r => server.listen(PORT, '127.0.0.1', () => r(server)));
}

const SWEEP = `(() => { const MARGIN = ${MARGIN}; const DT = ${DT};\n` + `
const ps = window.__ps3d, THREE = ps.THREE, v = new THREE.Vector3();
const footOf = () => window.__foot || { x0: -1.2, x1: 1.2, y0: 0, y1: 1.5, z0: -0.66, z1: 0.66 };
function hull(slots, k) {
  const f = footOf(); let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9, z0 = 1e9, z1 = -1e9, n = 0;
  for (const s of slots || []) { if (!s) continue; n++;
    x0 = Math.min(x0, s.x + f.x0); x1 = Math.max(x1, s.x + f.x1);
    y0 = Math.min(y0, (s.y || 0) + f.y0); y1 = Math.max(y1, (s.y || 0) + f.y1);
    z0 = Math.min(z0, s.z + f.z0); z1 = Math.max(z1, s.z + f.z1); }
  return n ? [{ k, x0, x1, y0, y1, z0, z1 }] : [];
}
function columns(slots, k) {
  const cols = [];
  for (const s of slots || []) { if (!s) continue; let c = null; for (const o of cols) if (Math.abs(o.x - s.x) < 2) c = o;
    if (!c) cols.push(c = { x: s.x, s: [] }); c.s.push(s); }
  return cols.flatMap(c => hull(c.s, k));
}
function obstacles() {
  const live = (ps.walkBoxes ? ps.walkBoxes() : []).filter(b => b.y0 < 2.6 && b.y1 > 0.15).map(b => ({ k: b.k || 'crate', x0: +b.x0, x1: +b.x1, y0: +b.y0, y1: +b.y1, z0: +b.z0, z1: +b.z1 }));
  const dock = ps.dockV4 && ps.dockV4.slots;
  const pal = ps.cg3 && ps.cg3.RC && ps.cg3.RC.slots;
  return [...hull(ps.cg3.baySlots, 'bay'), ...columns(dock, 'dock'), ...hull(pal, 'pallet'), ...live];
}
function clearance(x, z, boxes) {
  let best = 1e9, bk = '';
  for (const b of boxes) {
    const dx = Math.max(b.x0 - MARGIN - x, 0, x - (b.x1 + MARGIN));
    const dz = Math.max(b.z0 - MARGIN - z, 0, z - (b.z1 + MARGIN));
    let c; if (dx === 0 && dz === 0) c = -Math.min(x - (b.x0 - MARGIN), (b.x1 + MARGIN) - x, z - (b.z0 - MARGIN), (b.z1 + MARGIN) - z);
    else c = Math.hypot(dx, dz);
    if (c < best) { best = c; bk = b.k; }
  }
  return { c: best, k: bk };
}
function bodies() {
  const out = [];
  const add = (id, o) => {
    if (!o) return; let vis = true, ride = false;
    for (let p = o; p; p = p.parent) { if (p.visible === false) vis = false; if (/Bed|Truck/.test(p.name || '')) ride = true; }
    o.updateWorldMatrix(true, false); o.getWorldPosition(v);
    out.push({ id, x: v.x, y: v.y, z: v.z, vis, ride });
  };
  const wk = (ps.wk && ps.wk.people) || {};
  const root = (o, n) => o && (o.getObjectByName(n) || o);
  add('miner', root(wk.miner && wk.miner.obj, 'C3_Root'));
  add('driver', root(wk.driver && wk.driver.obj, 'C4_Root'));
  add('mech', root(wk.mech && wk.mech.obj, 'C1_Root'));
  if (wk.cm) add('cm', wk.cm.root || wk.cm.obj);
  return out;
}
function boardBodies() {
  const out = [], bd = ps.BD; if (!bd || !bd.crew) return out;
  for (const c of bd.crew) {
    const k = (c.name || '').split('_')[1];
    const o = (k && c.getObjectByName('C' + k + '_Root')) || c;
    let vis = true; for (let p = o; p; p = p.parent) if (p.visible === false) vis = false;
    o.updateWorldMatrix(true, false); o.getWorldPosition(v);
    out.push({ id: 'board-' + c.name, x: v.x, y: v.y, z: v.z, vis, ride: false });
  }
  return out;
}
function resetNav() {
  if (typeof ps.walkReset === 'function') ps.walkReset();
  const bd = ps.BD; if (!bd || !bd.crew) return;
  for (const c of bd.crew) { if (c.userData) c.userData._nav = null; c.position.x = 0; c.position.z = 0; }
}
const stat = () => ({ samples: 0, ground: 0, hits: 0, min: 1e9, minK: '', ex: [] });
function take(st, list, boxes) {
  for (const b of list) {
    if (!b.vis || b.ride) continue;
    st.samples++;
    if (b.y > 2.6) continue;
    st.ground++;
    const q = clearance(b.x, b.z, boxes);
    if (q.c < st.min) { st.min = q.c; st.minK = q.k + ':' + b.id; }
    if (q.c < 0) { st.hits++; if (st.ex.length < 8) st.ex.push({ id: b.id, x: +b.x.toFixed(2), y: +b.y.toFixed(2), z: +b.z.toFixed(2), k: q.k, pen: +(-q.c).toFixed(3) }); }
  }
}
function sweepWalk(dir, boxes) {
  const st = stat(); const now = ps.nowMs();
  ps.S.cg.sh.st = 'pad'; ps.S.cg.sh.req = 0; ps.S.wk = { go: 0, down: 0, cx: 0, cz: 0 };
  resetNav();
  const back0 = dir === 'back' ? ps.wkDescSec() : 0;
  const dur = dir === 'back' ? ps.wkReturnSec() : Math.max(ps.wkGatherSec(), ps.wkPersonSec('mech'), ps.wkPersonSec('cm'));
  for (let tau = 0; tau <= dur + 1e-6; tau += DT) {
    if (dir === 'back') { ps.S.wk.go = now - 1; ps.S.wk.down = now - (back0 + tau) * 1000; }
    else { ps.S.wk.go = now - tau * 1000; ps.S.wk.down = 0; }
    ps.wkUpd(now);
    take(st, bodies(), boxes);
  }
  ps.S.wk = { go: 0, down: 0, cx: 0, cz: 0 }; ps.wkUpd(now);
  st.dur = +dur.toFixed(2); st.min = st.min === 1e9 ? null : +st.min.toFixed(3); return st;
}
function sweepBoard(boxes) {
  const st = stat(); const now = ps.nowMs(); const bd = ps.BD;
  ps.S.wk = { go: 0, down: 0, cx: 0, cz: 0 };
  ps.S.cg.sh.st = 'board'; ps.S.cg.sh.fly = 4; ps.S.cg.sh.req = 0;
  if (!ps.S.bc) ps.S.bc = { id: 0, on: 0, x: 1 };
  resetNav();
  const end = (bd.pre || 2) + 24;
  for (let tb = 0; tb <= end; tb += DT) {
    ps.S.cg.sh.t0 = now - tb * 1000;
    ps.updCrew();
    take(st, boardBodies(), boxes);
  }
  ps.S.cg.sh.st = 'pad'; ps.S.cg.sh.t0 = now; ps.wkUpd(now);
  st.dur = +end.toFixed(2); st.min = st.min === 1e9 ? null : +st.min.toFixed(3); return st;
}
function sweepHandler(boxes) {
  const st = stat();
  if (typeof ps.brStep !== 'function') { st.skipped = 'brStep is not exported on this build'; st.min = null; return st; }
  ps.S.wk = { go: 0, down: 0, cx: 0, cz: 0 };
  resetNav();
  const spans = [[0.4, 19.81], [50.16, 69.57]];
  for (const [a, b] of spans) for (let t = a; t <= b; t += DT) { ps.brStep(t, DT); take(st, bodies().filter(x => x.id === 'cm'), boxes); }
  st.min = st.min === 1e9 ? null : +st.min.toFixed(3); return st;
}
function runFill(bay, dk, pallet) {
  const c = ps.S.cg; c.bay = bay; c.dk = dk; c.sh.st = 'pad'; c.sh.req = 0;
  c.ref = Array.from({ length: pallet }, () => 1e15);
  if (typeof ps.poseNow === 'function') ps.poseNow();
  const boxes = obstacles();
  const paths = {
    'pad-and-pickup-out': sweepWalk('out', boxes),
    'return-to-mine': sweepWalk('back', boxes),
    'boarding': sweepBoard(boxes),
    'handler-pad-loop': sweepHandler(boxes)
  };
  let hits = 0, ground = 0; for (const k in paths) { hits += paths[k].hits || 0; ground += paths[k].ground || 0; }
  return { bay, dk, pallet, boxes: boxes.map(b => ({ k: b.k, x0: +b.x0.toFixed(2), x1: +b.x1.toFixed(2), z0: +b.z0.toFixed(2), z1: +b.z1.toFixed(2) })), ground, hits, paths };
}
return { fills: [runFill(0, 0, 0), runFill(6, 10, 4), runFill(12, 20, 8)] };
})()`;

async function main() {
  const server = await serve();
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--mute-audio'] });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1' });
  page.setDefaultTimeout(180000);
  const url = `http://127.0.0.1:${PORT}/dev/index.html?mock=1&qa=1&fresh=1`;
  console.log('LOAD', BUILD, url);
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.fill('#gateCode', '00010');
  await page.click('#gateGo');
  await page.waitForSelector('#nameGate.on');
  await page.fill('#nameIn', 'Nav QA');
  await page.click('#nameGo');
  await page.waitForFunction(() => {
    const p = window.__ps3d;
    return p && p.coverGone && p.wk && p.wk.ready && p.cg3 && p.cg3.baySlots && p.BD && p.BD.root && p.cg3.boxParts && p.cg3.boxParts.some(b => b.L);
  });
  await page.evaluate(() => window.__ps3d.goSite(window.__ps3d.PADI));
  await page.waitForFunction(() => Math.abs(window.__ps3d.camX - window.__ps3d.PX) < 3);
  await page.waitForTimeout(1500);
  const foot = await page.evaluate(() => {
    const ps = window.__ps3d, THREE = ps.THREE;
    ps.S.cg.bay = 1; ps.S.cg.dk = 0; ps.S.cg.ref = []; ps.S.cg.sh.st = 'pad'; if (ps.poseNow) ps.poseNow();
    const s = ps.cg3.baySlots[0], v = new THREE.Vector3(), M = new THREE.Matrix4();
    let best = null, vol = -1;
    for (const part of ps.cg3.boxParts || []) { const im = part.im; if (!im || !im.count || !im.geometry) continue;
      if (!im.geometry.boundingBox) im.geometry.computeBoundingBox(); const lb = im.geometry.boundingBox;
      const size = (lb.max.x - lb.min.x) * (lb.max.y - lb.min.y) * (lb.max.z - lb.min.z); if (size <= vol) continue; vol = size;
      let pick = 0, pd = 1e9;
      for (let n = 0; n < im.count; n++) { im.getMatrixAt(n, M); v.set(0, 0, 0).applyMatrix4(M); const d = Math.hypot(v.x - s.x, v.z - s.z); if (d < pd) { pd = d; pick = n; } }
      im.getMatrixAt(pick, M);
      let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9, z0 = 1e9, z1 = -1e9;
      for (let i = 0; i < 2; i++) for (let j = 0; j < 2; j++) for (let k = 0; k < 2; k++) {
        v.set(i ? lb.max.x : lb.min.x, j ? lb.max.y : lb.min.y, k ? lb.max.z : lb.min.z).applyMatrix4(M);
        x0 = Math.min(x0, v.x); x1 = Math.max(x1, v.x); y0 = Math.min(y0, v.y); y1 = Math.max(y1, v.y); z0 = Math.min(z0, v.z); z1 = Math.max(z1, v.z);
      }
      best = { x0: +(x0 - s.x).toFixed(3), x1: +(x1 - s.x).toFixed(3), y0: +(y0 - (s.y || 0)).toFixed(3), y1: +(y1 - (s.y || 0)).toFixed(3), z0: +(z0 - s.z).toFixed(3), z1: +(z1 - s.z).toFixed(3), d: +pd.toFixed(3) };
    }
    return best;
  });
  console.log('FOOT', JSON.stringify(foot));
  if (foot) await page.evaluate(f => { window.__foot = f; }, foot);
  const t0 = Date.now();
  const report = await page.evaluate(SWEEP);
  report.build = BUILD; report.foot = foot; report.margin = MARGIN; report.dt = DT; report.ms = Date.now() - t0;
  let hits = 0;
  for (const f of report.fills) {
    console.log(`\\nFILL bay=${f.bay} dock=${f.dk} pallet=${f.pallet} ground=${f.ground} hits=${f.hits} boxes=${f.boxes.length}`);
    for (const [name, st] of Object.entries(f.paths)) {
      console.log(`  ${name}: samples=${st.samples} ground=${st.ground} hits=${st.hits || 0} minClear=${st.min} ${st.minK || ''} dur=${st.dur || ''} ${st.skipped || ''}`);
      for (const ex of st.ex || []) console.log('    HIT', JSON.stringify(ex));
    }
    hits += f.hits;
  }
  const ok = EXPECT === 'fail' ? hits > 0 : hits === 0;
  console.log(`\\n${BUILD}: ${hits} ground hits, expect ${EXPECT} -> ${ok ? 'OK' : 'UNEXPECTED'} (${(report.ms / 1000).toFixed(1)} s)`);
  mkdirSync(join(ROOT, 'qa', 'crewnav-out'), { recursive: true });
  writeFileSync(join(ROOT, 'qa', 'crewnav-out', BUILD + '.json'), JSON.stringify(report, null, 1));
  await browser.close();
  server.close();
  process.exit(ok ? 0 : 1);
}

main().catch(e => { console.error('HARNESS', e); process.exit(2); });
