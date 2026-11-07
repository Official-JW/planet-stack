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
const TS = 2;   // game-clock scale. The 10-minute coast is skipped; 2x keeps the walks readable.

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
    else if (key === 'driver' && ps.S.bt && ps.S.bt.hab === 1 && par === '') phase = 'inspect';
    return { d, phase, x: +cx.toFixed(1), z: +cz.toFixed(1), y1: +y1.toFixed(1), pts, par };
  };
  ps.__distOn = (map, x, z) => {
    const ix = Math.floor(x / CELL), iz = Math.floor(z / CELL); let best = 3;
    for (let dx = -12; dx <= 12; dx++) for (let dz = -12; dz <= 12; dz++) if (map.has((ix + dx) + ',' + (iz + dz))) {
      const dd = Math.hypot((ix + dx + 0.5) * CELL - x, (iz + dz + 0.5) * CELL - z) - CELL * 0.5;
      if (dd < best) best = dd;
    }
    return best;
  };
  if (window.__measureOnly) {
    const rack = (arr) => (arr || []).filter(Boolean).map(v => [v.x, v.z]);
    const bay = rack(ps.cg3 && ps.cg3.baySlots);
    const pallet = rack(ps.cg3 && ps.cg3.RC && ps.cg3.RC.slots);
    const dock = [];
    ps.scene.traverse(n => { if (n.name && /^Slot_\d+$/.test(n.name)) { const v = new T.Vector3(); n.getWorldPosition(v); if (v.y > -1 && v.y < 6) dock.push([v.x, v.z]); } });
    const stampBox = (map, x, z) => { for (let dx = -1.2; dx <= 1.2; dx += CELL) for (let dz = -0.8; dz <= 0.8; dz += CELL) map.set(Math.floor((x + dx) / CELL) + ',' + Math.floor((z + dz) / CELL), 1); };
    const clone = (src) => { const m = new Map(); src.forEach((_, k) => m.set(k, 1)); return m; };
    const empty = clone(cells), partial = clone(cells), full = clone(cells);
    const all = bay.concat(pallet).concat(dock);
    all.forEach((p, i) => { stampBox(full, p[0], p[1]); if (i % 2 === 0) stampBox(partial, p[0], p[1]); });
    ps.__fills = { empty, partial, full };
    ps.__mins = {};
    ps.__rackN = { bay: bay.length, pallet: pallet.length, dock: dock.length, partial: all.filter((_, i) => i % 2 === 0).length, full: all.length };
    ps.__obs = { minerBed: false, ipad: false, captain0: null, mech0: null, snap: [], routes: {} };
    ps.__sample = () => {
      const legOf = () => (ps.S.wk && ps.S.wk.down > 0) ? 'return' : (ps.S.wk && ps.S.wk.go > 0) ? 'depart' : 'inspect';
      for (const k of ['miner', 'driver', 'mech', 'cm']) {
        const b = ps.__body(k); if (!b) continue;
        ps.__where = ps.__where || {}; ps.__where[k] = b;
        if (k === 'miner' && b.par === 'Truck_Bed') ps.__obs.minerBed = true;
        if (k === 'driver' && !ps.__obs.captain0) ps.__obs.captain0 = { x: b.x, z: b.z, ipad: !!(ps.wk.ipad && ps.wk.ipad.visible), phase: b.phase };
        if (k === 'mech' && !ps.__obs.mech0) ps.__obs.mech0 = { x: b.x, z: b.z, phase: b.phase };
        const leg = b.phase === 'inspect' ? 'inspect' : (b.phase === 'walk' ? legOf() : b.phase);
        const route = ps.__obs.routes[k] = ps.__obs.routes[k] || [];
        const tag = b.phase + '/' + leg;
        if (route[route.length - 1] !== tag) route.push(tag);
        if (b.phase !== 'walk' && b.phase !== 'inspect') continue;
        for (const fill of ['empty', 'partial', 'full']) {
          let dd = 99; for (const q of b.pts) { const z = ps.__distOn(ps.__fills[fill], q[0], q[1]); if (z < dd) dd = z; }
          const slot = ps.__mins[k] = ps.__mins[k] || {};
          const row = slot[fill] = slot[fill] || {};
          const prev = row[leg];
          if (!prev || dd < prev.d) row[leg] = { d: +dd.toFixed(3), at: b.x + ',' + b.z };
        }
      }
      const sec = Math.floor((window.__vclock ? window.__vclock.get() : 0) / 2000);
      if (sec !== ps.__lastSec) {
        ps.__lastSec = sec; const tk = ps.truckState || {}, cg = ps.S.cg;
        ps.__obs.snap.push({ sec, truckX: tk.x != null ? +tk.x.toFixed(2) : null, truckPh: tk.ph || '', st: ps.mineRev ? +ps.mineRev.st.toFixed(3) : null, pc: cg && cg.pc && cg.pc.k || '', away: !!ps.minerOffAt(ps.nowMs()), ship: cg && cg.sh && cg.sh.st, bed: ps.__obs.minerBed, ipad: !!(ps.wk.ipad && ps.wk.ipad.visible) });
      }
    };
    return;
  }
  ps.__mins = {};
  ps.__sample = () => {
    for (const k of ['miner', 'driver', 'mech', 'cm']) {
      const b = ps.__body(k); if (!b) continue;
      const M = ps.__mins[k] = ps.__mins[k] || { walk: 99, station: 99, ride: 99, climb: 99, at: '' };
      if (b.d < M[b.phase]) { M[b.phase] = +b.d.toFixed(3); if (b.phase === 'walk') M.at = b.x + ',' + b.z; }
      ps.__where = ps.__where || {}; ps.__where[k] = b;
    }
  };
  setInterval(ps.__sample, 250);
  const orig = ps.renderer.render.bind(ps.renderer);
  ps.renderer.render = function (scene, camera) {
    const W = ps.renderer.domElement.width, H = ps.renderer.domElement.height, look = ps.__look || { x: 640, z: 0 };
    ps.renderer.setScissorTest(true);
    const put = (vy, cam) => {
      ps.renderer.setViewport(0, vy, W, H / 2); ps.renderer.setScissor(0, vy, W, H / 2);
      camera.aspect = (W / (H / 2)); camera.position.set(cam[0], cam[1], cam[2]); camera.up.set(0, 1, 0); camera.lookAt(cam[3], cam[4], cam[5]); camera.updateProjectionMatrix();
      orig(scene, camera);
    };
    put(H / 2, look.eye || [look.x + (look.side || 16), 4.2, look.z + 8, look.x, 1.3, look.z]);
    put(0, [look.x, look.top || 22, look.z + 0.02, look.x, 0, look.z]);
    ps.renderer.setScissorTest(false); ps.renderer.setViewport(0, 0, W, H);
  };
};

const FPS = 10;   // video frames per wall-second. The game clock steps with these frames, so a slow screenshot cannot skip the walk.

async function installClock(page) {
  await page.evaluate(() => {
    if (window.__vclock) return;
    const d0 = Date.now(), p0 = performance.now();
    let elapsed = 0;
    Date.now = () => d0 + elapsed;
    performance.now = () => p0 + elapsed;
    window.__vclock = { set(ms) { elapsed = ms; }, get() { return elapsed; } };
  });
}

async function record(page, seconds) {
  const dir = path.join(tmpdir(), 'crew-frames-' + Date.now());
  mkdirSync(dir, { recursive: true });
  const n = Math.max(1, Math.round(seconds * FPS));
  const step = 1000 / FPS;
  let bed = -1;
  for (let i = 0; i < n; i++) {
    await page.evaluate((step) => {
      const c = window.__vclock; c.set(c.get() + step);
      if (window.__ps3d && window.__ps3d.__sample) window.__ps3d.__sample();
    }, step);
    await page.evaluate(() => new Promise((resolve) => {
      let done = false; const finish = () => { if (!done) { done = true; resolve(); } };
      requestAnimationFrame(() => requestAnimationFrame(finish));
      setTimeout(finish, 1200);
    }));
    const buf = await page.screenshot({ type: 'jpeg', quality: 56 });
    writeFileSync(path.join(dir, String(i).padStart(4, '0') + '.jpg'), buf);
    if (bed < 0 && i % 4 === 0) {
      const on = await page.evaluate(() => { const b = window.__ps3d.__where && window.__ps3d.__where.miner; return !!(b && b.par === 'Truck_Bed'); });
      if (on) bed = i;
    }
    if (i % 25 === 0) console.log('frame', i, '/', n);
  }
  return { dir, n, bed };
}

function encode(dir, out) {
  return new Promise((resolve, reject) => {
    const ff = spawn('ffmpeg', ['-y', '-framerate', '20', '-i', path.join(dir, '%04d.jpg'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '32', '-movflags', '+faststart', out], { stdio: 'inherit' });
    ff.on('exit', (code) => code === 0 ? resolve() : reject(new Error('ffmpeg ' + code)));
  });
}

async function bootPage(browser, code, hab, measure) {
  const page = await browser.newPage(); page.setDefaultTimeout(180000);
  const errs = []; page.on('pageerror', (e) => errs.push(e.message));
  await page.goto(BASE + '/dev/index.html?mock=1&qa=1&ts=' + TS, { waitUntil: 'domcontentloaded' });
  await page.evaluate((code, hab) => { for (const k of Object.keys(localStorage)) if (k.startsWith('planetstack')) localStorage.removeItem(k);
    const sv = { name: hab ? 'Post' : 'Pre', rt: Date.now(), ev: 1, ord: 3, tu25: 1, money: 25000 }; if (hab) sv.bt = { hab: 1 }; localStorage.setItem('planetstack-dev-' + code, JSON.stringify(sv)); }, code, hab);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#gateCode', { timeout: 20000 });
  await page.type('#gateCode', code); await page.click('#gateGo');
  await page.waitForFunction(() => window.__ps3d && window.__ps3d.wk && window.__ps3d.wk.ready, { timeout: 90000 });
  if (measure) await page.evaluate(() => { window.__measureOnly = true; });
  await page.evaluate(bootJs);
  await installClock(page);
  return { page, errs };
}

async function stepClock(page, seconds) {
  const n = Math.max(1, Math.round(seconds * 20));
  for (let i = 0; i < n; i += 40) {
    const k = Math.min(40, n - i);
    await page.evaluate(async (k) => {
      for (let i = 0; i < k; i++) {
        window.__vclock.set(window.__vclock.get() + 50);
        await new Promise((resolve) => { let done = false; const finish = () => { if (!done) { done = true; resolve(); } }; requestAnimationFrame(() => requestAnimationFrame(finish)); setTimeout(finish, 1200); });
        if (window.__ps3d.__sample) window.__ps3d.__sample();
      }
    }, k);
    if (i % 200 === 0) console.log('measure step', i, '/', n);
  }
}

async function measureScenario(browser, name, code, hab) {
  const { page, errs } = await bootPage(browser, code, hab, true);
  const info = await page.evaluate(() => ({ racks: window.__ps3d.__rackN, captain: window.__ps3d.__obs.captain0, mech: window.__ps3d.__obs.mech0 }));
  await page.evaluate(() => { if (window.__ps3d.__sample) window.__ps3d.__sample(); });
  const before = await page.evaluate(() => window.__ps3d.__obs.captain0);
  await page.evaluate(() => { const ps = window.__ps3d, c = ps.S.cg; c.sh.hold = 20; c.autoLaunch = true; c.sh.f0 = ps.nowMs() - 180000; ps.settleTo(ps.nowMs(), null); });
  const plan = await page.evaluate((ts) => {
    const ps = window.__ps3d;
    return { out: ps.wkGatherSec() / ts + 4, ret: (ps.wkDescSec() + ps.wkReturnSec()) / ts + 3, fly: ps.residentFlyers(), seats: ps.shipFreePassengerSeats() };
  }, TS);
  console.log(name, 'measure', JSON.stringify(plan), JSON.stringify(info));
  await stepClock(page, plan.out);
  const mid = await page.evaluate(() => ({ st: window.__ps3d.S.cg.sh.st, bed: window.__ps3d.__obs.minerBed, fly: window.__ps3d.S.cg.sh.fly }));
  const skipped = await page.evaluate(() => { const ps = window.__ps3d; if (ps.S.cg.sh.st !== 'pad' && window.PS_QA) return window.PS_QA.skipToTouchdown(); return { st: ps.S.cg.sh.st }; });
  await stepClock(page, plan.ret);
  const done = await page.evaluate(() => ({ mins: window.__ps3d.__mins, obs: window.__ps3d.__obs, st: window.__ps3d.S.cg.sh.st, fly: window.__ps3d.S.cg.sh.fly, res: window.__ps3d.residentFlyers(), seats: window.__ps3d.shipFreePassengerSeats(), racks: window.__ps3d.__rackN }));
  await page.close();
  return { name, hab: !!hab, plan, before, mid, skipped, errs: errs.slice(0, 6), ...done };
}

function worstWalk(mins) {
  let worst = null;
  for (const k of Object.keys(mins || {})) for (const fill of Object.keys(mins[k])) for (const leg of Object.keys(mins[k][fill])) {
    if (leg !== 'depart' && leg !== 'return' && leg !== 'inspect') continue;
    const row = mins[k][fill][leg];
    if (!worst || row.d < worst.d) worst = { who: k, fill, leg, d: row.d, at: row.at };
  }
  return worst;
}

async function run() {
  const MODE = process.env.PS_MODE || 'all';
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
    await installClock(page);
    await new Promise(r => setTimeout(r, 400));
    // stations hold, then the full-hold launch
    await page.evaluate(() => {
      const ps = window.__ps3d; if (ps.__sample) ps.__sample();
      const toast = document.getElementById('ecToast'); if (toast) toast.style.setProperty('display', 'none', 'important');
      const w = ps.__where || {};
      if (ps.S.bt.hab === 1 && w.driver) {
        const d = w.driver; ps.__look = { x: d.x, z: d.z, top: 16, eye: [d.x + 5, 2.6, d.z + 5, d.x, 1.0, d.z] };
      } else ps.__look = { x: 164, z: 8, top: 26, eye: [164, 9, 30, 164, 1.4, 8] };
    });
    const rec = await record(page, 3);
    await page.evaluate(() => { const ps = window.__ps3d, c = ps.S.cg; c.sh.hold = 20; c.autoLaunch = true; c.sh.f0 = ps.nowMs() - 180000; ps.settleTo(ps.nowMs(), null);
      const toast = document.getElementById('ecToast'); if (toast) toast.style.setProperty('display', 'none', 'important');
      ps.__cam = setInterval(() => { const w = ps.__where || {}, truck = w.driver && w.driver.phase === 'ride' ? w.driver : w.miner && w.miner.phase === 'ride' ? w.miner : null;
        const pad = w.mech || w.cm || w.driver; const focus = truck || pad || { x: 640, z: -8 };
        const eye = truck ? [focus.x - 4, 4.0, focus.z + 13, focus.x + 2, 1.4, focus.z] : [focus.x + 6, 3.0, focus.z + 6, focus.x, 1.0, focus.z];
        ps.__look = { x: focus.x, z: focus.z, top: truck ? 22 : 16, eye };
        const x = document.querySelector('#upX'); if (x && document.getElementById('upPanel') && !document.getElementById('upPanel').hidden) x.click(); }, 200); });
    const plan = await page.evaluate((ts) => {
      const ps = window.__ps3d;
      const gather = ps.wkGatherSec(), back = ps.wkDescSec() + ps.wkReturnSec(), board = ps.BOARD_SEC || 40;
      return { gather, back, board, out: gather / ts + Math.min(board, 28) / ts + 2, ret: back / ts + 3 };
    }, TS);
    console.log(name, 'plan', JSON.stringify(plan));
    const more = await record(page, plan.out);
    const { readdirSync } = await import('node:fs');
    const shots = readdirSync(more.dir).filter(f => f.endsWith('.jpg')).sort();
    const stillAt = shots[more.bed >= 0 ? Math.min(shots.length - 1, more.bed) : Math.min(shots.length - 1, Math.round(shots.length * 0.42))];
    if (stillAt) {
      await new Promise((resolve, reject) => {
        const ff = spawn('ffmpeg', ['-y', '-i', path.join(more.dir, stillAt), path.join(OUT, name + '-frame-stepped-simulation-still.png')], { stdio: 'inherit' });
        ff.on('exit', (c) => c === 0 ? resolve() : reject(new Error('still ' + c)));
      });
    }
    // skip the coast so the return walk is in this clip. The stepped clock stays put while this settles.
    await page.evaluate(() => { const ps = window.__ps3d; if (ps.S.cg.sh.st !== 'pad' && window.PS_QA) return window.PS_QA.skipToTouchdown(); return { st: ps.S.cg.sh.st }; }).then((r) => console.log(name, 'skip', JSON.stringify(r)));
    const back = await record(page, plan.ret);
    const mins = await page.evaluate(() => window.__ps3d.__mins);
    const st = await page.evaluate(() => ({ st: window.__ps3d.S.cg.sh.st, fly: window.__ps3d.S.cg.sh.fly, res: window.__ps3d.residentFlyers(), seats: window.__ps3d.shipFreePassengerSeats() }));
    report[name] = { mins, st, errs: errs.slice(0, 6), frames: [rec.dir, more.dir, back.dir] };
    await page.close();
  }
  const measured = [];
  if (MODE !== 'clips') {
    measured.push(await measureScenario(browser, 'crew-before-habitat', '00002', false));
    measured.push(await measureScenario(browser, 'crew-after-habitat', '00001', true));
    writeFileSync(path.join(OUT, 'crew-clearance.json'), JSON.stringify(measured, null, 2));
    let fail = false;
    for (const row of measured) { row.worst = worstWalk(row.mins); if (row.worst && row.worst.d < 0.5) fail = true; }
    console.log(JSON.stringify(measured.map(r => ({ name: r.name, worst: r.worst, racks: r.racks, bed: r.obs && r.obs.minerBed, routes: r.obs && r.obs.routes, captain: r.obs && r.obs.captain0, mid: r.mid, skipped: r.skipped, seats: r.seats, res: r.res })), null, 2));
    if (fail) { await browser.close(); console.error('CLEARANCE FAIL: a walking or inspecting body came within 0.5 m'); process.exit(1); }
    console.log('CLEARANCE PASS');
    if (MODE === 'measure') { await browser.close(); return; }
  }
  if (MODE === 'measure') return;
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
    const mp4 = path.join(OUT, name + '-frame-stepped-simulation.mp4');
    const font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';
    const vf = "drawtext=fontfile=" + font + ":text='FRAME-STEPPED SIMULATION PROOF — not real-time playback or a performance measurement':fontsize=12:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=4:x=8:y=h-26";
    await new Promise((resolve, reject) => {
      const ff = spawn('ffmpeg', ['-y', '-f', 'concat', '-safe', '0', '-r', String(FPS), '-i', list, '-vf', vf, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', String(FPS), '-crf', '30', '-movflags', '+faststart', mp4], { stdio: 'inherit' });
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
