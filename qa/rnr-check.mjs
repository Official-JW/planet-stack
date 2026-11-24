// R&R self-check (gc/rnr). Serves nothing; point it at a local static server of the repo.
//
// Seeding (disclosed), every run:
//   URL: /dev/?mock=1&qa=1&ts=<n>&fresh=1 on the first boot of a context.
//   Gate code 00010 (in-page mock Worker), player name "Riley Nash".
//   After the cover is gone and the route is ready: Habitat + Dock marked built,
//   every ground cargo store filled (pallet, bay, Dock), Mine truck parked under
//   the chute at logical fill 0.6342, ship set to 'away' with 2 flyers (Habitat built).
//   settleTo then starts the R&R pickup (S.rnr.go). Van trips run on the URL timescale;
//   PS_QA.warp jumps the game clock as live play for the long drives.
//   Reloads drop ?fresh=1 and restore the planetstack-dev-<code> save only (not the tab lock).
//
// Covers: trigger, pickup, no production while resting, return and resume, reload mid-rest.
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';

const require = createRequire(import.meta.url);
const pwCore = process.env.PW_CORE || ['/workspace/mineresume/node_modules/playwright-core/index.js','/tmp/pw/node_modules/playwright-core/index.js'].find(f => { try { return require('fs').existsSync(f); } catch (e) { return false; } }) || 'playwright-core';
const { chromium } = require(pwCore);

const CODE = process.env.PS_CODE || '00010';
const NAME = 'Riley Nash';
const FRAC = 0.6342;
const CHROME = process.env.CHROME_PATH || '/usr/bin/google-chrome';
const ignoreErr = /Failed to load because no supported source was found|play\(\) failed|AbortError|The play\(\) request was interrupted|The fetching process for the media resource was aborted|not allowed by the user agent|user gesture|WebGL/i;

const args = process.argv.slice(2);
const arg = (name, def) => {
  const i = args.indexOf('--' + name);
  return i >= 0 ? args[i + 1] : def;
};
const HOST = arg('host', process.env.PS_HOST || 'http://127.0.0.1:8996');
const OUT = arg('out', '');
const STILL_DIR = arg('stills', '/workspace/rnr/stills');
const TS = Number(arg('ts', '10')) || 10;
const HEADED = args.includes('--headed');

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const LOG = process.env.PS_LOG || '';
function log(msg) {
  const line = new Date().toISOString() + ' ' + msg;
  console.log(line);
  if (LOG) fs.appendFileSync(LOG, line + '\n');
}

function check(list, name, pass, detail) {
  list.push({ name, pass: !!pass, detail });
  return !!pass;
}
function near(a, b, eps) { return Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) <= eps; }

async function launchBrowser(headless = true) {
  return chromium.launch({
    executablePath: CHROME,
    headless,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--use-gl=angle', '--use-angle=swiftshader', '--mute-audio', '--autoplay-policy=no-user-gesture-required', '--window-position=0,0', '--window-size=1280,800', ...(headless ? [] : ['--kiosk'])],
  });
}

function attachLogs(page, errors) {
  page.on('pageerror', (e) => errors.push('PAGEERROR ' + e.message));
  page.on('console', (msg) => {
    if (msg.type() === 'error' && !ignoreErr.test(msg.text())) errors.push('CONSOLE ' + msg.text().slice(0, 300));
  });
}

async function boot(page, { ts, fresh }) {
  const q = new URLSearchParams({ mock: '1', qa: '1', ts: String(ts) });
  if (fresh) q.set('fresh', '1');
  const url = `${HOST.replace(/\/$/, '')}/dev/?${q.toString()}`;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('#gateCode', { timeout: 30000 });
  await page.fill('#gateCode', CODE);
  await page.click('#gateGo');
  const nameIn = await page.waitForSelector('#nameIn', { state: 'visible', timeout: 8000 }).catch(() => null);
  if (nameIn) {
    await page.fill('#nameIn', NAME);
    await page.click('#nameGo');
  }
  await page.waitForFunction(() => {
    const p = window.__ps3d;
    if (p && p.halted) return true;
    return !!(p && p.coverGone && p.S && p.S.cg && p.RT && p.RT.ready && p.settleTo && p.fillAt && p.nowMs && p.cargoStoresFull);
  }, null, { timeout: 180000 });
  const halted = await page.evaluate(() => window.__ps3d && window.__ps3d.halted);
  if (halted) throw new Error('boot halted: ' + halted + ' ' + (await page.evaluate(() => window.__ps3d.stopMsg || '')));
  await page.evaluate(() => { try { if (window.__ps3d.setMusic) window.__ps3d.setMusic(false); } catch (e) {} });
  await page.waitForFunction(() => {
    const p = window.__ps3d;
    return !!(p && p.stationObjs && p.stationObjs[p.HABI] && p.crewVan);
  }, null, { timeout: 120000 }).catch(() => {});
  return url;
}

async function snap(page) {
  return page.evaluate(() => {
    const p = window.__ps3d;
    if (!p || !p.S || !p.S.cg) return null;
    const S = p.S, t = p.nowMs(), r = S.rnr || {};
    let fillAt = null;
    try { fillAt = p.fillAt(t); } catch (e) { fillAt = null; }
    let cv = null;
    try { if (p.crewVan && p.crewVan.update) p.crewVan.update(t); cv = p.crewVan && p.crewVan.info(t); } catch (e) {}
    return {
      t, spd: p.SPD,
      go: r.go || 0, outT: r.outT || 0, back: r.back || 0, hs: r.hs ? 1 : 0,
      homeAt: p.rnrHomeAt ? p.rnrHomeAt() : 0,
      workAt: p.rnrWorkAt ? p.rnrWorkAt() : 0,
      endAt: p.rnrEndAt ? p.rnrEndAt() : 0,
      fillAt, shown: p.TS ? p.TS.shown : null,
      made: S.cg.made, loads: S.loads, money: S.money,
      hold: S.cg.sh.hold, st: S.cg.sh.st, fly: S.cg.sh.fly,
      storesFull: p.cargoStoresFull(), shipLeft: p.shipLeft(), shipBack: p.shipBack(),
      minerOff: p.minerOffAt(t), rnrOff: p.rnrOffAt && p.rnrOffAt(t),
      pallet: S.cg.ref.length, bay: S.cg.bay, dk: S.cg.dk,
      palletCap: p.CFG.cargo.palletCap, bayCap: p.CFG.cargo.bayCap, dockCap: p.CFG.dock.cap,
      hab: !!(S.bt && S.bt.hab === 1), dock: !!(S.bt && S.bt.dock === 1),
      dep: !!(S.tk && S.tk.dep), c0: S.tk && S.tk.c0, add: S.tk && (S.tk.add || 0),
      clock: p.truckClock(t), fillSec: p.fillSec(),
      cvPh: cv && cv.ph, cvU: cv && cv.u, cvEnd: cv && cv.tEnd, cvPick: cv && cv.tPick, cvDrop: cv && cv.tDrop, cvMode: cv && cv.mode,
      vanReady: !!(p.crewVan && p.crewVan.layout && p.crewVan.layout.mineH),
    };
  });
}

async function waitSnap(page, pred, timeoutMs, interval = 50) {
  const t0 = Date.now();
  let last = null;
  while (Date.now() - t0 < timeoutMs) {
    last = await snap(page);
    if (last && pred(last)) return last;
    await sleep(interval);
  }
  throw new Error('timeout waiting for condition; last=' + JSON.stringify(last));
}

async function warp(page, ms) {
  return page.evaluate((ms) => {
    const p = window.__ps3d;
    if (!window.PS_QA || !window.PS_QA.warp) return { ok: false, reason: 'no_warp' };
    window.PS_QA.warp(ms);
    const t = p.nowMs();
    p.settleTo(t, null);
    p.S.rt = t;
    try { p.crewVan && p.crewVan.update(t); } catch (e) {}
    if (p.poseNow) p.poseNow();
    return { ok: true, t };
  }, ms);
}

async function still(page, name) {
  fs.mkdirSync(STILL_DIR, { recursive: true });
  const file = path.join(STILL_DIR, name + '.jpg');
  await page.evaluate(() => {
    const p = window.__ps3d, t = p.nowMs();
    try { p.crewVan && p.crewVan.update(t); } catch (e) {}
    try { p.poseNow && p.poseNow(); } catch (e) {}
    try { p.PS_DEV && p.PS_DEV.renderNow && p.PS_DEV.renderNow(); } catch (e) {}
    try { window.PS_DEV && window.PS_DEV.renderNow && window.PS_DEV.renderNow(); } catch (e) {}
  });
  await sleep(80);
  await page.screenshot({ path: file, type: 'jpeg', quality: 80 });
  log('still ' + file);
  return file;
}

async function closeUi(page) {
  await page.evaluate(() => {
    const p = window.__ps3d;
    try { p.closeUp && p.closeUp('x'); } catch (e) {}
    try { p.ecHangUp && p.ecHangUp(); } catch (e) {}
    if (p.S && p.S.cg && p.S.cg.sh) p.S.cg.sh.cp = 1;
  });
}

async function goSiteNow(page, i, lookVan) {
  await closeUi(page);
  await page.evaluate(({ i, lookVan }) => {
    const p = window.__ps3d, t = p.nowMs();
    try { p.crewVan && p.crewVan.update(t); } catch (e) {}
    if (p.ZOOM) { p.ZOOM.z = 1; p.ZOOM.ox = 0; p.ZOOM.oz = 0; p.ZOOM.pinching = false; }
    p.goSite(i);
    let x = p.SX ? p.SX[i] : p.camX;
    const van = lookVan && p.crewVan && p.crewVan.st && p.crewVan.st.van;
    if (van && Math.abs(van.position.x - x) < 50) x = van.position.x;
    p.camX = x;
    if (p.placeCamera) p.placeCamera();
    if (p.poseNow) p.poseNow();
    try { window.PS_DEV && window.PS_DEV.renderNow && window.PS_DEV.renderNow(); } catch (e) {}
  }, { i, lookVan: !!lookVan });
  await sleep(200);
}

async function waitVanReady(page, timeoutMs = 90000) {
  try {
    await page.waitForFunction(() => {
      const p = window.__ps3d;
      if (!p || !p.crewVan) return false;
      try { p.crewVan.update(p.nowMs()); } catch (e) {}
      return !!(p.crewVan.layout && p.crewVan.layout.mineH);
    }, null, { timeout: timeoutMs });
    return true;
  } catch (e) {
    const info = await page.evaluate(() => {
      const p = window.__ps3d || {};
      const hab = p.stationObjs && p.stationObjs[p.HABI];
      const sy = p.stationObjs && p.stationObjs[p.SHIPI];
      return {
        habBuilt: !!(p.S && p.S.bt && p.S.bt.hab === 1),
        hasVan: !!p.crewVan,
        layout: !!(p.crewVan && p.crewVan.layout),
        mineH: !!(p.crewVan && p.crewVan.layout && p.crewVan.layout.mineH),
        habObj: !!hab,
        habPath: !!(hab && hab.getObjectByName && hab.getObjectByName('Crew_Path_01')),
        syRoad: !!(sy && sy.getObjectByName && sy.getObjectByName('Road_Entry')),
        err: p.crewVan && p.crewVan.st && p.crewVan.st.err,
      };
    });
    log('waitVanReady failed ' + JSON.stringify(info) + ' ' + e.message);
    return false;
  }
}

async function seedRnr(page, frac = FRAC) {
  const seeded = await page.evaluate((f) => {
    const p = window.__ps3d, S = p.S, t = p.nowMs();
    S.money = Math.max(S.money || 0, 5000000);
    S.bt = S.bt || {};
    S.bt.hab = 1; S.bt.dock = 1;
    if (p.bldApply) { p.bldApply(p.HABI); p.bldApply(p.DOCKI); }
    if (p.nbUI) p.nbUI();
    const k = S.tk, fs = p.fillSec() * 1000;
    k.c0 = t - f * fs;
    k.add = 0; k.lr = 0; k.dep = 0; k.paid = false; k.val = 0;
    k.sr = 0; k.hr = 0; k.tp = 0; k.sm = 0; k.hm = 0; k.gw = 0; k.gs = 0;
    k.q = 0; k.qd = [];
    S.tz = { c: { by: 0, rel: 0 }, b: { by: -1, rel: 0 } };
    const pal = p.CFG.cargo.palletCap, bay = p.CFG.cargo.bayCap, dock = p.CFG.dock.cap;
    S.cg.ref = [];
    for (let i = 0; i < pal; i++) S.cg.ref.push(t - 10000);
    S.cg.bay = bay;
    S.cg.dk = dock;
    S.cg.autoLaunch = false;
    S.cg.autoLoad = false;
    if (S.cg.pc) S.cg.pc = { k: '', t0: 0 };
    S.cg.rd = 0; S.cg.rc = 0;
    S.cg.fb = { st: 'load', t0: t, bed: 0 };
    S.cg.sh = { st: 'away', t0: t, hold: 0, f0: t, req: 0, fly: 2, left: 0, cargo: 0, fm: 1, cp: 1 };
    S.rnr = { go: 0, outT: 0, back: 0, hs: 0 };
    try { p.closeUp && p.closeUp('x'); p.ecHangUp && p.ecHangUp(); } catch (e) {}
    p.settleTo(t, null);
    S.rt = t;
    let fillAt = null;
    try { fillAt = p.fillAt(p.nowMs()); } catch (e) {}
    return {
      fillAt, go: (S.rnr && S.rnr.go) || 0, outT: (S.rnr && S.rnr.outT) || 0,
      st: S.cg.sh.st, fly: S.cg.sh.fly, hab: S.bt.hab, dock: S.bt.dock,
      full: p.cargoStoresFull(), left: p.shipLeft(),
      pallet: S.cg.ref.length, bay: S.cg.bay, dk: S.cg.dk,
      made: S.cg.made, loads: S.loads, minerOff: p.minerOffAt(p.nowMs()),
    };
  }, frac);
  return seeded;
}


async function run() {
  const checks = [];
  const errors = [];
  const stills = [];
  fs.mkdirSync(STILL_DIR, { recursive: true });
  const browser = await launchBrowser(!HEADED);
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  let page = await context.newPage();
  attachLogs(page, errors);

  try {
    log('boot');
    await boot(page, { ts: TS, fresh: true });

    const seeded = await seedRnr(page);
    log('seeded ' + JSON.stringify(seeded));
    check(checks, 'trigger: ship away and stores full starts R&R', seeded.go > 0 && seeded.left && seeded.hab === 1, seeded);

    await waitVanReady(page);
    await page.evaluate(() => {
      const p = window.__ps3d, t = p.nowMs();
      p.settleTo(t, null); p.S.rt = t;
    });
    let atGo = await waitSnap(page, (s) => s.go > 0 && s.outT > 0, 20000);
    check(checks, 'pickup trip stamps (outT set once the van path is ready)', atGo && atGo.go > 0 && atGo.outT > 0, atGo);

    const fill0 = atGo.fillAt;
    const made0 = atGo.made;
    const loads0 = atGo.loads;
    check(checks, 'seeded mid-fill is held at pickup', near(fill0, FRAC, 0.02), { fill0, FRAC });

    // Still 1: warp to the Mine pickup (door open / workers boarding).
    const pickMs = (atGo.cvPick || atGo.homeAt && atGo.outT ? 95 : 95) * 1000;
    const toPick = (atGo.outT + (atGo.cvPick || 95) * 1000) - atGo.t;
    if (toPick > 0) await warp(page, toPick + 400);
    const atPick = await snap(page);
    log('at pick ' + JSON.stringify({ fillAt: atPick.fillAt, cvPh: atPick.cvPh, cvU: atPick.cvU, cvPick: atPick.cvPick, rnrOff: atPick.rnrOff }));
    await goSiteNow(page, 1, true);
    stills.push(await still(page, '01_mine_pickup'));

    // Mid-rest: warp toward Habitat arrival, still frozen.
    const homeIn = atPick.homeAt > atPick.t ? atPick.homeAt - atPick.t : 120000;
    await warp(page, Math.max(500, homeIn - 2000));
    const mid = await snap(page);
    log('mid-rest ' + JSON.stringify({ fillAt: mid.fillAt, made: mid.made, loads: mid.loads, go: mid.go, outT: mid.outT, clock: mid.clock, cvPh: mid.cvPh, cvU: mid.cvU }));
    check(checks, 'no production while resting (fill / made / loads held)',
      mid.go > 0 && mid.rnrOff && near(mid.fillAt, fill0, 0.015) && mid.made === made0 && mid.loads === loads0,
      { mid: { fillAt: mid.fillAt, made: mid.made, loads: mid.loads, go: mid.go, clock: mid.clock, rnrOff: mid.rnrOff }, fill0, made0, loads0 });
    check(checks, 'truckClock frozen at go', mid.clock === mid.go || near(mid.clock, mid.go, 2), { clock: mid.clock, go: mid.go });

    // Arrive home at Habitat, still mid-rest (ship still away).
    if (mid.homeAt > mid.t) await warp(page, mid.homeAt - mid.t + 800);
    await goSiteNow(page, 6, true);
    stills.push(await still(page, '02_habitat_rest'));

    // Reload mid-rest (workers are home). Re-anchor the away stamp so catch-up cannot land the ship before we check the freeze.
    await page.evaluate(() => {
      const p = window.__ps3d, t = p.nowMs();
      if (p.S.cg && p.S.cg.sh && p.S.cg.sh.st === 'away') p.S.cg.sh.t0 = t;
      p.S.rt = t;
      try { p.save(); } catch (e) {}
    });
    await page.close();
    page = await context.newPage();
    attachLogs(page, errors);
    await boot(page, { ts: TS, fresh: false });
    await waitVanReady(page);
    const re = await snap(page);
    log('reload ' + JSON.stringify({ fillAt: re.fillAt, made: re.made, loads: re.loads, go: re.go, outT: re.outT, hs: re.hs, st: re.st, vanReady: re.vanReady }));
    check(checks, 'reload mid-rest keeps freeze and fill',
      re.go > 0 && !re.hs && re.rnrOff && near(re.fillAt, fill0, 0.02) && re.made === made0 && re.loads === loads0 && re.st === 'away',
      { re: { fillAt: re.fillAt, made: re.made, loads: re.loads, go: re.go, hs: re.hs, st: re.st, rnrOff: re.rnrOff }, fill0, made0, loads0 });

    // Return: ship back on the pad, one Dock slot frees, van drives workers back.
    const returned = await page.evaluate(() => {
      const p = window.__ps3d, S = p.S, t = p.nowMs();
      try { p.crewVan && p.crewVan.update(t); } catch (e) {}
      S.cg.sh = { st: 'pad', t0: t, hold: 0, f0: t, req: 0, cp: 1 };
      if (S.cg.dk > 0) S.cg.dk -= 1;
      S.cg.autoLaunch = false;
      S.cg.autoLoad = false;
      p.settleTo(t, null);
      S.rt = t;
      return { back: S.rnr && S.rnr.back, go: S.rnr && S.rnr.go, full: p.cargoStoresFull(), space: p.rnrSpaceFree(t), shipBack: p.shipBack(), van: !!(p.crewVan && p.crewVan.layout && p.crewVan.layout.mineH), homeAt: p.rnrHomeAt && p.rnrHomeAt(), t };
    });
    log('return start ' + JSON.stringify(returned));

    let afterBack = await snap(page);
    if (!(afterBack.back > 0)) {
      const homeIn2 = afterBack.homeAt && afterBack.homeAt > afterBack.t ? afterBack.homeAt - afterBack.t : 1000;
      await warp(page, homeIn2 + 500);
      await page.evaluate(() => {
        const p = window.__ps3d, t = p.nowMs();
        try { p.crewVan && p.crewVan.update(t); } catch (e) {}
        p.S.cg.sh.st = 'pad';
        p.S.cg.sh.cp = 1;
        if (p.S.cg.dk >= p.CFG.dock.cap) p.S.cg.dk = p.CFG.dock.cap - 1;
        p.S.cg.autoLoad = false;
        p.settleTo(t, null); p.S.rt = t;
      });
      afterBack = await snap(page);
    }
    check(checks, 'return trip starts when ship is back and space opens', afterBack.back > 0 && afterBack.shipBack, { back: afterBack.back, shipBack: afterBack.shipBack, homeAt: afterBack.homeAt, t: afterBack.t, vanReady: afterBack.vanReady });

    const dropAt = afterBack.workAt > 0 ? afterBack.workAt : afterBack.back + (afterBack.cvDrop || 150) * 1000;
    const dropIn = dropAt > afterBack.t ? dropAt - afterBack.t : 1000;
    await warp(page, dropIn + 600);
    const atWork = await snap(page);
    log('at work ' + JSON.stringify({ fillAt: atWork.fillAt, hs: atWork.hs, go: atWork.go, back: atWork.back, rnrOff: atWork.rnrOff, clock: atWork.clock, cvPh: atWork.cvPh, cvU: atWork.cvU }));
    check(checks, 'resume: Mine unfreezes at the drop with the same fill (no catch-up)',
      !atWork.rnrOff && (atWork.hs === 1 || atWork.go === 0) && near(atWork.fillAt, fill0, 0.025) && atWork.made === made0 && atWork.loads === loads0,
      { atWork: { fillAt: atWork.fillAt, hs: atWork.hs, go: atWork.go, rnrOff: atWork.rnrOff, made: atWork.made, loads: atWork.loads }, fill0, made0, loads0 });

    await goSiteNow(page, 1, true);
    stills.push(await still(page, '03_mine_return_drop'));

    // After resume, production should advance again (fill climbs).
    await warp(page, Math.max(4000, (1 - fill0) * atWork.fillSec * 250));
    const after = await snap(page);
    check(checks, 'production resumes after return (fill advances)',
      after.fillAt > fill0 + 0.02 || after.dep === true || after.loads > loads0,
      { fillAt: after.fillAt, fill0, dep: after.dep, loads: after.loads, loads0 });

    await goSiteNow(page, 1, false);
    stills.push(await still(page, '04_mine_resumed'));

    const fatal = errors.filter((e) => /PAGEERROR/.test(e));
    check(checks, 'no page errors', fatal.length === 0, fatal);
  } finally {
    await browser.close().catch(() => {});
  }

  const passed = checks.filter((c) => c.pass).length;
  const report = { ok: checks.length > 0 && checks.every((c) => c.pass), passed, total: checks.length, checks, stills, errors };
  const text = checks.map((c) => `${c.pass ? 'PASS' : 'FAIL'}  ${c.name}${c.detail ? ' — ' + (typeof c.detail === 'string' ? c.detail : JSON.stringify(c.detail)) : ''}`).join('\n');
  console.log(text);
  console.log('\n==== SUMMARY ====');
  console.log('passed', passed, '/', checks.length, 'ok=', report.ok);
  if (OUT) fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
  fs.writeFileSync(path.join(STILL_DIR, 'captions.json'), JSON.stringify({
    '01_mine_pickup': 'Habitat van at the Mine picking up workers after cargo stores filled and the ship left.',
    '02_habitat_rest': 'Workers resting at the Habitat; Mine production stays frozen.',
    '03_mine_return_drop': 'Van drops the workers back at the Mine after the ship returns and storage frees up.',
    '04_mine_resumed': 'Mine production resumes from the frozen fill, no catch-up credit.',
  }, null, 2));
  if (!report.ok) process.exit(1);
}

run().catch((e) => { console.error(e); process.exit(2); });
