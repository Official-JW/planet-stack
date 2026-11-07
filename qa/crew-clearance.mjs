// Clearance + proof clips for the crew-from-stations rework.
// Headless Chrome, dev/index.html?mock=1, 390x844. Logs the minimum distance from each
// crew body to crate stacks, buildings, the crane and the refinery-bridge supports.
// A walking frame under 0.5 m fails. Ride (truck cab / flatbed) and the top-door climb
// are reported separately: those poses are on the vehicle or the ladder on purpose.
//
//   CHROME=/usr/local/bin/google-chrome node qa/crew-clearance.mjs
// Writes MP4 + one still per clip under /opt/cursor/artifacts when that directory exists,
// otherwise under qa/crew-clearance-out/.
import puppeteer from 'puppeteer-core';
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

const CHROME = process.env.CHROME || '/usr/local/bin/google-chrome';
const BASE = process.env.PS_BASE || 'http://127.0.0.1:8765';
const OUT = existsSync('/opt/cursor/artifacts') ? '/opt/cursor/artifacts' : path.resolve('qa/crew-clearance-out');
mkdirSync(OUT, { recursive: true });
const TS = 3;   // game-clock scale. 1x makes the away leg a 10-minute wait; 3x still reads as a walk.

const bootJs = () => {
  const ps = window.__ps3d, T = ps.THREE, WK = ps.wk;
  if (ps.__proof) return;
  ps.__proof = 1;
  const CELL = 0.25, cells = new Map();
  const stamp = (x, z) => { cells.set(Math.floor(x / CELL) + ',' + Math.floor(z / CELL), 1); };
  const consider = (root) => {
    if (!root) return; root.updateWorldMatrix(true, true);
    root.traverse(n => {
      if (!n.isMesh || !n.geometry || n.material?.visible === false) return;
      let vis = true; for (let p = n; p; p = p.parent) if (p.visible === false) vis = false; if (!vis) return;
      const nm = (n.name || '') + (n.parent ? n.parent.name : '');
      if (/Terrain|Tire_Trail|Dust|Plume|Ground|Crew/.test(nm)) return;
      const pos = n.geometry.attributes.position; if (!pos) return;
      const v = new T.Vector3(), step = Math.max(1, Math.floor(pos.count / 2500));
      for (let i = 0; i < pos.count; i += step) {
        v.fromBufferAttribute(pos, i); if (n.isSkinnedMesh) n.applyBoneTransform(i, v); v.applyMatrix4(n.matrixWorld);
        if (v.y < 0.75 || v.y > 2.4) continue;   // floors and ankle-high plates are not obstacles a walker passes through
        stamp(v.x, v.z);
      }
    });
  };
  consider(ps.pad); consider(ps.stationObjs && ps.stationObjs[1]); consider(ps.stationObjs && ps.stationObjs[2]);
  consider(ps.stationObjs && ps.stationObjs[3]); consider(ps.bridge && ps.bridge.obj); consider(ps.br && ps.br.grp);
  // crate stacks: every posed instance, inflated by the body of the box
  const im = ps.boxIM; if (im) { const q = new T.Vector3(); for (let i = 0; i < im.count; i++) { im.getMatrixAt(i, ps.__cm = ps.__cm || new T.Matrix4()); q.setFromMatrixPosition(ps.__cm); if (q.y > 0.2 && q.y < 4) { for (let dx = -1.2; dx <= 1.2; dx += CELL) for (let dz = -0.8; dz <= 0.8; dz += CELL) stamp(q.x + dx, q.z + dz); } } }
  ps.__cells = cells; ps.__CELL = CELL;
  ps.__dist = (x, z) => {
    const ix = Math.floor(x / CELL), iz = Math.floor(z / CELL); let best = 3;
    for (let dx = -12; dx <= 12; dx++) for (let dz = -12; dz <= 12; dz++) if (cells.has((ix + dx) + ',' + (iz + dz))) {
      const d = Math.hypot((ix + dx + 0.5) * CELL - x, (iz + dz + 0.5) * CELL - z) - CELL * 0.5;
      if (d < best) best = d;
    }
    return best;
  };
  ps.__body = (key) => {
    const p = WK.people[key]; if (!p) return null; const o = p.obj; o.updateWorldMatrix(true, true);
    let mesh = null; o.traverse(m => { if (m.isSkinnedMesh) mesh = m; }); if (!mesh) return null; mesh.skeleton.update();
    const pos = mesh.geometry.attributes.position, v = new T.Vector3();
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9, z0 = 1e9, z1 = -1e9;
    for (let i = 0; i < pos.count; i += 30) { v.fromBufferAttribute(pos, i); mesh.applyBoneTransform(i, v); v.applyMatrix4(mesh.matrixWorld);
      if (v.x < x0) x0 = v.x; if (v.x > x1) x1 = v.x; if (v.y < y0) y0 = v.y; if (v.y > y1) y1 = v.y; if (v.z < z0) z0 = v.z; if (v.z > z1) z1 = v.z; }
    if (x1 - x0 > 3 || z1 - z0 > 3 || y1 - y0 > 3) return null;   // a one-frame skeleton glitch, not a body
    const pts = [[x0, z0], [x0, z1], [x1, z0], [x1, z1], [(x0 + x1) / 2, (z0 + z1) / 2]];
    let d = 99; for (const q of pts) { const dd = ps.__dist(q[0], q[1]); if (dd < d) d = dd; }
    const par = o.parent && o.parent.name || '';
    const map = { miner: 'Crew_3', driver: 'Crew_4', mech: 'Crew_1', cm: 'Crew_2' };
    const flying = ps.flyCrew().some(c => c.board === map[key]);
    const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
    let phase = 'station';
    if (!flying) phase = 'station';
    else if (par === 'Truck_Chassis' || par === 'Truck_Bed') phase = 'ride';
    else if (o.parent === ps.BD.root || (key === 'cm' && ps.br && ps.br.h && ps.br.h.scene.parent === ps.BD.root)) phase = 'climb';
    else if (y1 > 2.4 && Math.hypot(cx - 644, cz + 10.6) < 8) phase = 'climb';
    else if (ps.S.wk && ps.S.wk.go > 0) phase = Math.hypot(cx - 644, cz + 10) < 3 ? 'climb' : 'walk';
    return { d, phase, x: +cx.toFixed(1), z: +cz.toFixed(1), y1: +y1.toFixed(1) };
  };
  ps.__mins = {};
  setInterval(() => {
    for (const k of ['miner', 'driver', 'mech', 'cm']) {
      const b = ps.__body(k); if (!b) continue;
      const M = ps.__mins[k] = ps.__mins[k] || { walk: 99, station: 99, ride: 99, climb: 99, at: '' };
      if (b.d < M[b.phase]) { M[b.phase] = +b.d.toFixed(3); if (b.phase === 'walk') M.at = b.x + ',' + b.z; }
      ps.__where = ps.__where || {}; ps.__where[k] = b;
    }
  }, 250);
  const orig = ps.renderer.render.bind(ps.renderer);
  ps.renderer.render = function (scene, camera) {
    const W = ps.renderer.domElement.width, H = ps.renderer.domElement.height, look = ps.__look || { x: 640, z: 0 };
    ps.renderer.setScissorTest(true);
    const put = (vy, cam) => {
      ps.renderer.setViewport(0, vy, W, H / 2); ps.renderer.setScissor(0, vy, W, H / 2);
      camera.aspect = (W / (H / 2)); camera.position.set(cam[0], cam[1], cam[2]); camera.up.set(0, 1, 0); camera.lookAt(cam[3], cam[4], cam[5]); camera.updateProjectionMatrix();
      orig(scene, camera);
    };
    put(H / 2, [look.x + (look.side || 16), 4.2, look.z, look.x, 1.3, look.z]);
    put(0, [look.x, 32, look.z + 0.02, look.x, 0, look.z]);
    ps.renderer.setScissorTest(false); ps.renderer.setViewport(0, 0, W, H);
  };
};

async function record(page, frames, ms) {
  const dir = path.join(tmpdir(), 'crew-frames-' + Date.now());
  mkdirSync(dir, { recursive: true });
  const fps = 8, n = Math.min(frames, Math.round(ms / 1000 * fps));
  for (let i = 0; i < n; i++) {
    const t = Date.now();
    const buf = await page.screenshot({ type: 'jpeg', quality: 60 });
    writeFileSync(path.join(dir, String(i).padStart(4, '0') + '.jpg'), buf);
    const wait = 1000 / fps - (Date.now() - t);
    if (wait > 0) await new Promise(r => setTimeout(r, wait));
  }
  return { dir, n };
}

function encode(dir, out) {
  return new Promise((resolve, reject) => {
    const ff = spawn('ffmpeg', ['-y', '-framerate', '20', '-i', path.join(dir, '%04d.jpg'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '32', '-movflags', '+faststart', out], { stdio: 'inherit' });
    ff.on('exit', (code) => code === 0 ? resolve() : reject(new Error('ffmpeg ' + code)));
  });
}

async function run() {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox', '--disable-gpu', '--use-gl=angle', '--use-angle=swiftshader', '--ignore-gpu-blocklist', '--window-size=390,844'], defaultViewport: { width: 390, height: 844, deviceScaleFactor: 1 } });
  const report = {};
  async function scenario(name, code, hab) {
    const page = await browser.newPage(); page.setDefaultTimeout(180000);
    const errs = []; page.on('pageerror', (e) => errs.push(e.message));
    await page.goto(BASE + '/dev/index.html?mock=1&qa=1&ts=' + TS, { waitUntil: 'domcontentloaded' });
    await page.evaluate((code, hab) => { for (const k of Object.keys(localStorage)) if (k.startsWith('planetstack')) localStorage.removeItem(k);
      const sv = { name: hab ? 'Post' : 'Pre', rt: Date.now(), ev: 1, ord: 3, tu25: 1, money: 25000 }; if (hab) sv.bt = { hab: 1 }; localStorage.setItem('planetstack-dev-' + code, JSON.stringify(sv)); }, code, hab);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#gateCode', { timeout: 20000 });
    await page.type('#gateCode', code); await page.click('#gateGo');
    await page.waitForFunction(() => window.__ps3d && window.__ps3d.wk && window.__ps3d.wk.ready, { timeout: 90000 });
    await page.evaluate(bootJs);
    await new Promise(r => setTimeout(r, 500));
    // stations hold, then the full-hold launch
    await page.evaluate(() => { window.__ps3d.__look = habLook(); function habLook() { return window.__ps3d.S.bt.hab === 1 ? { x: 640, z: -14, side: 18 } : { x: 171, z: 9, side: 14 }; } window.__ps3d.__look = (window.__ps3d.S.bt.hab === 1) ? { x: 642, z: -16, side: 18 } : { x: 168, z: 8, side: 14 }; });
    const rec = await record(page, 12, 1500);
    await page.evaluate(() => { const ps = window.__ps3d, c = ps.S.cg; c.sh.hold = 20; c.autoLaunch = true; c.sh.f0 = ps.nowMs() - 180000; ps.settleTo(ps.nowMs(), null);
      ps.__cam = setInterval(() => { const w = ps.__where || {}, truck = w.driver && w.driver.phase === 'ride' ? w.driver : w.miner && w.miner.phase === 'ride' ? w.miner : null;
        const pad = w.mech || w.cm || w.driver; const focus = truck || pad || { x: 640, z: -8 };
        ps.__look = { x: focus.x, z: focus.z, side: truck ? 18 : 14 };
        const x = document.querySelector('#upX'); if (x && !document.getElementById('upPanel').hidden) x.click(); }, 200); });
    const more = await record(page, 200, 24000);
    await page.screenshot({ path: path.join(OUT, name + '-still.png') });
    // if the ship is away, skip the 10-minute coast so the return walk is in this clip
    await page.evaluate(() => { const ps = window.__ps3d; if (ps.S.cg.sh.st !== 'pad' && window.PS_QA) window.PS_QA.skipToTouchdown(); });
    const back = await record(page, 120, 14000);
    const mins = await page.evaluate(() => window.__ps3d.__mins);
    const st = await page.evaluate(() => ({ st: window.__ps3d.S.cg.sh.st, fly: window.__ps3d.S.cg.sh.fly, res: window.__ps3d.residentFlyers(), seats: window.__ps3d.shipFreePassengerSeats() }));
    report[name] = { mins, st, errs: errs.slice(0, 6), frames: [rec.dir, more.dir, back.dir] };
    await page.close();
  }
  await scenario('crew-before-habitat', '00002', false);
  await scenario('crew-after-habitat', '00001', true);
  await browser.close();
  for (const name of Object.keys(report)) {
    const dirs = report[name].frames, list = path.join(tmpdir(), name + '.txt');
    const lines = [];
    for (const d of dirs) {
      const { readdirSync } = await import('node:fs');
      for (const f of readdirSync(d).filter(f => f.endsWith('.jpg')).sort()) lines.push("file '" + path.join(d, f) + "'");
    }
    writeFileSync(list, lines.join('\n'));
    const mp4 = path.join(OUT, name + '.mp4');
    await new Promise((resolve, reject) => {
      const ff = spawn('ffmpeg', ['-y', '-f', 'concat', '-safe', '0', '-r', '8', '-i', list, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', '8', '-crf', '30', '-movflags', '+faststart', mp4], { stdio: 'inherit' });
      ff.on('exit', (c) => c === 0 ? resolve() : reject(new Error('ffmpeg ' + c)));
    });
    report[name].mp4 = mp4;
    delete report[name].frames;
  }
  // fail the walk phase under 0.5 m
  let fail = false;
  for (const name of Object.keys(report)) for (const k of Object.keys(report[name].mins || {})) {
    const w = report[name].mins[k].walk; if (w < 0.5) fail = true;
  }
  console.log(JSON.stringify(report, null, 2));
  if (fail) { console.error('CLEARANCE FAIL: a walking body came within 0.5 m of an obstacle'); process.exit(1); }
  console.log('CLEARANCE PASS');
}
run().catch((e) => { console.error(e); process.exit(1); });
