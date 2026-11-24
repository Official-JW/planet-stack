// Mine-resume self-check. Serves nothing; point it at a local static server of the repo.
//
// Seeding (disclosed), every run:
//   URL: /dev/?mock=1&qa=1&ts=<n>&fresh=1 on the first boot of a context.
//   Gate code 00010 (in-page mock Worker), player name "Maren Holt".
//   After the cover is gone and the route is ready: park the Mine truck under the chute
//   with logical fill 0.6342 (S.tk.c0 = pickup - 0.6342 * fillSec, add 0, not departed),
//   bay 0, hold = holdCap(), autoLaunch on. settleTo then takes the real full-hold pickup.
//   The long away leg is skipped with PS_QA.skipToTouchdown() once the ship has left the pad
//   (WARP through board / launch / away / land, same path as live play). The walk home
//   then runs on the URL timescale.
//   Reloads drop ?fresh=1 and restore the planetstack-dev-<code> save only (not the tab lock).
//
// --expect pass  (fixed build): exit 0 only when criteria 1-4 all hold.
// --expect fail  (unfixed 74e7f02): exit 0 only when the home frame really was observed
//   and made/loads or the silo logical fill (fillAt) show the replay bug.
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW_CORE || '/tmp/pw/node_modules/playwright-core/index.js');

const CODE = process.env.PS_CODE || '00010';
const NAME = 'Maren Holt';
const FRAC = 0.6342;
const CHROME = process.env.CHROME_PATH || '/usr/bin/google-chrome';
const ignoreErr = /Failed to load because no supported source was found|play\(\) failed|AbortError|The play\(\) request was interrupted|The fetching process for the media resource was aborted|not allowed by the user agent|user gesture|WebGL/i;

const args = process.argv.slice(2);
const arg = (name, def) => {
  const i = args.indexOf('--' + name);
  return i >= 0 ? args[i + 1] : def;
};
const HOST = arg('host', process.env.PS_HOST || 'http://127.0.0.1:8795');
const EXPECT = arg('expect', 'pass');
const OUT = arg('out', '');
const CLIP = args.includes('--clip');
const HEADED = args.includes('--headed');
const GATE = args.includes('--gate');
const CLIP_DIR = arg('clip-dir', '/opt/cursor/artifacts');

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
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--use-gl=angle', '--use-angle=swiftshader', '--mute-audio', '--autoplay-policy=no-user-gesture-required', '--window-position=0,0', '--window-size=1920,1200', ...(headless ? [] : ['--kiosk'])],
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
    return !!(p && p.coverGone && p.S && p.S.cg && p.RT && p.RT.ready && p.settleTo && p.fillAt && p.nowMs && p.wkPreHab);
  }, null, { timeout: 180000 });
  const halted = await page.evaluate(() => window.__ps3d && window.__ps3d.halted);
  if (halted) throw new Error('boot halted: ' + halted + ' ' + (await page.evaluate(() => window.__ps3d.stopMsg || '')));
  await page.evaluate(() => { try { if (window.__ps3d.setMusic) window.__ps3d.setMusic(false); } catch (e) {} });
  return url;
}

async function snap(page) {
  return page.evaluate(() => {
    const p = window.__ps3d;
    if (!p || !p.S || !p.S.cg) return null;
    const S = p.S, t = p.nowMs();
    const desc = p.wkDescSec ? p.wkDescSec() : 0;
    const ret = p.wkReturnSec ? p.wkReturnSec() : 0;
    const homeAt = (S.wk && S.wk.down > 0) ? S.wk.down + (desc + ret) * 1000 : 0;
    let fillAt = null;
    try { fillAt = p.fillAt(t); } catch (e) { fillAt = null; }
    let silo = null;
    try { silo = p.mineRev ? p.mineRev.st : null; } catch (e) {}
    return {
      t, spd: p.SPD,
      go: (S.wk && S.wk.go) || 0,
      down: (S.wk && S.wk.down) || 0,
      hs: (S.wk && S.wk.hs) ? 1 : 0,
      homeAt,
      homeIn: homeAt ? (homeAt - t) / 1000 : null,
      fillAt,
      silo,
      shown: p.TS ? p.TS.shown : null,
      made: S.cg.made,
      loads: S.loads,
      money: S.money,
      hold: S.cg.sh.hold,
      st: S.cg.sh.st,
      minerOff: p.minerOffAt(t),
      cap: p.holdCap(),
      fillSec: p.fillSec(),
      dep: !!(S.tk && S.tk.dep),
      c0: S.tk && S.tk.c0,
      add: S.tk && (S.tk.add || 0),
      desc, ret,
    };
  });
}

async function waitSnap(page, pred, timeoutMs, interval = 40) {
  const t0 = Date.now();
  let last = null;
  while (Date.now() - t0 < timeoutMs) {
    last = await snap(page);
    if (last && pred(last)) return last;
    await sleep(interval);
  }
  throw new Error('timeout waiting for condition; last=' + JSON.stringify(last));
}

async function seedPickup(page, frac = FRAC) {
  const seeded = await page.evaluate((f) => {
    const p = window.__ps3d;
    const S = p.S;
    const t = p.nowMs();
    const k = S.tk;
    const fs = p.fillSec() * 1000;
    k.c0 = t - f * fs;
    k.add = 0; k.lr = 0; k.dep = 0; k.paid = false; k.val = 0;
    k.sr = 0; k.hr = 0; k.tp = 0; k.sm = 0; k.hm = 0; k.gw = 0; k.gs = 0;
    k.q = 0; k.qd = [];
    S.tz = { c: { by: 0, rel: 0 }, b: { by: -1, rel: 0 } };
    S.cg.sh.hold = p.holdCap();
    S.cg.sh.req = 0;
    if (S.cg.sh.man) S.cg.sh.man = 0;
    S.cg.bay = 0;
    S.cg.autoLaunch = true;
    S.cg.autoLoad = true;
    if (S.cg.pc) S.cg.pc = { k: '', t0: 0 };
    S.cg.rd = 0;
    p.settleTo(t, null);
    const go = (S.wk && S.wk.go) || 0;
    if (go > 0 && !k.dep) { k.c0 = go - f * fs; k.add = 0; }
    let fillAt = null;
    try { fillAt = p.fillAt(p.nowMs()); } catch (e) {}
    return {
      fillAt, hold: S.cg.sh.hold, cap: p.holdCap(), go, st: S.cg.sh.st,
      fillSec: p.fillSec(), dep: k.dep || 0, c0: k.c0, pre: p.wkPreHab(),
      made: S.cg.made, loads: S.loads,
    };
  }, frac);
  if (!(seeded.go > 0)) throw new Error('seed did not start pickup: ' + JSON.stringify(seeded));
  const pickup = await snap(page);
  return { seeded, pickup };
}

async function skipAway(page) {
  return page.evaluate(() => {
    if (!window.PS_QA || !window.PS_QA.skipToTouchdown) return { ok: false, reason: 'no_PS_QA' };
    return window.PS_QA.skipToTouchdown();
  });
}

async function watchHome(page, timeoutMs = 60000) {
  const t0 = Date.now();
  let lastBefore = null, firstAfter = null, prev = null;
  while (Date.now() - t0 < timeoutMs) {
    const s = await snap(page);
    if (!s) { await sleep(20); continue; }
    const before = s.go > 0 && (s.down <= 0 || s.homeAt <= 0 || s.t < s.homeAt);
    if (before) lastBefore = s;
    if (prev && prev.go > 0 && s.go === 0 && !firstAfter) {
      firstAfter = s;
      break;
    }
    prev = s;
    await sleep(20);
  }
  return { lastBefore, firstAfter };
}

async function captureSave(page) {
  await page.evaluate(() => window.__ps3d.save());
  return page.evaluate(() => {
    const out = {};
    for (const k of Object.keys(localStorage)) {
      if (/^planetstack-dev-\d{5}$/.test(k)) out[k] = localStorage.getItem(k);
    }
    return out;
  });
}

async function installSave(page, dump) {
  await page.addInitScript((data) => {
    try {
      for (const [k, v] of Object.entries(data || {})) localStorage.setItem(k, v);
    } catch (e) {}
  }, dump);
}

function homeOf(s) {
  return s && s.down > 0 ? s.down + (s.desc + s.ret) * 1000 : (s && s.homeAt) || 0;
}

async function fillAtTime(page, t) {
  return page.evaluate((tt) => {
    try { return window.__ps3d.fillAt(tt); } catch (e) { return null; }
  }, t);
}

async function runHomePath(page) {
  const notes = [];
  const checks = [];
  const { seeded, pickup } = await seedPickup(page);
  notes.push({ step: 'seed+pickup', seeded, pickup });
  const leftPad = await waitSnap(page, (s) => s.st && s.st !== 'pad', 90000, 80);
  notes.push({ step: 'leftPad', st: leftPad.st, made: leftPad.made, loads: leftPad.loads, fillAt: leftPad.fillAt, go: leftPad.go });
  const skip = await skipAway(page);
  const afterSkip = await snap(page);
  notes.push({ step: 'skip', skip, afterSkip });
  check(checks, 'frozen_while_away',
    pickup.made === afterSkip.made && pickup.loads === afterSkip.loads && near(afterSkip.fillAt, pickup.fillAt, 1e-3) && afterSkip.minerOff && afterSkip.go > 0,
    `pickup made=${pickup.made} loads=${pickup.loads} fill=${pickup.fillAt} money=${pickup.money} → after skip made=${afterSkip.made} loads=${afterSkip.loads} fill=${afterSkip.fillAt} money=${afterSkip.money} st=${afterSkip.st} minerOff=${afterSkip.minerOff} skippedSec=${skip && skip.skippedSec}`);
  check(checks, 'long_away',
    !!(skip && skip.ok && skip.skippedSec >= 500),
    `skip=${JSON.stringify(skip)}`);

  const landed = await snap(page);
  const { lastBefore, firstAfter } = await watchHome(page);
  notes.push({ step: 'home', landed: { t: landed.t, st: landed.st, homeIn: landed.homeIn }, lastBefore, firstAfter });
  if (!lastBefore || !firstAfter) {
    check(checks, 'home_observed', false, 'missing before/after snapshot');
    return { notes, checks, pickup, skip };
  }
  const homeAt = homeOf(lastBefore);
  const fillAtHome = await fillAtTime(page, homeAt);
  check(checks, 'home_observed', true, `before t=${lastBefore.t} homeAt=${homeAt} after t=${firstAfter.t}`);
  check(checks, 'made_loads_stable',
    lastBefore.made === firstAfter.made && lastBefore.loads === firstAfter.loads && lastBefore.made === pickup.made && lastBefore.loads === pickup.loads,
    `pickup made=${pickup.made} loads=${pickup.loads} → before made=${lastBefore.made} loads=${lastBefore.loads} → after made=${firstAfter.made} loads=${firstAfter.loads}`);
  check(checks, 'no_burst',
    (firstAfter.made - lastBefore.made) === 0 && (firstAfter.loads - lastBefore.loads) === 0,
    `Δmade=${firstAfter.made - lastBefore.made} Δloads=${firstAfter.loads - lastBefore.loads}`);
  check(checks, 'money_home_frame',
    lastBefore.money === firstAfter.money,
    `before money=${lastBefore.money} after money=${firstAfter.money} (truckLoadPay is 0; ship pay is already done by touchdown)`);
  check(checks, 'fill_resume',
    near(fillAtHome, pickup.fillAt, 1e-3) && fillAtHome > 0.2,
    `pickup fillAt=${pickup.fillAt} fillAt(home)=${fillAtHome} live fillAt=${firstAfter.fillAt}`);

  const spd = firstAfter.spd || 1;
  const fillSec = firstAfter.fillSec || 120;
  const t0 = firstAfter.t;
  const f0 = firstAfter.fillAt;
  await sleep(Math.ceil(30000 / spd) + 250);
  const risen = await snap(page);
  const dt = (risen.t - t0) / 1000;
  const expectedRise = dt / fillSec;
  const actualRise = (risen.fillAt ?? 0) - (f0 ?? 0);
  notes.push({ step: 'rise', dt, expectedRise, actualRise, risen });
  check(checks, 'fill_rise',
    !risen.dep && dt > 20 && dt < 45 && near(actualRise, expectedRise, 0.03) && risen.fillAt > f0,
    `Δt=${dt.toFixed(2)}s Δfill=${actualRise == null ? 'null' : actualRise.toFixed(4)} expected≈${expectedRise.toFixed(4)} fillNow=${risen.fillAt} dep=${risen.dep}`);

  const remain = (1 - (pickup.fillAt || FRAC)) * fillSec;
  const waitFull = Math.ceil(Math.max(5, remain - dt) * 1000 / spd) + 8000;
  let tFullAt = null, fullErr = null;
  try { tFullAt = await waitSnap(page, (s) => s.dep || (s.fillAt != null && s.fillAt >= 0.995), waitFull, 40); }
  catch (e) { fullErr = String(e.message || e).slice(0, 400); }
  if (tFullAt) {
    const fullDt = (tFullAt.t - t0) / 1000;
    notes.push({ step: 'full', fullDt, remain, st: tFullAt.st, dep: tFullAt.dep, fillAt: tFullAt.fillAt });
    check(checks, 'next_full_timing',
      Math.abs(fullDt - remain) <= 6,
      `full/dep ${fullDt.toFixed(2)}s after home snap; expected ≈${remain.toFixed(2)}s`);
  } else {
    check(checks, 'next_full_timing', false, fullErr || 'no full');
  }
  return { notes, checks, pickup, lastBefore, firstAfter, fillAtHome, skip, risen };
}

async function runIdempotent(page) {
  const checks = [];
  const { pickup } = await seedPickup(page);
  await waitSnap(page, (s) => s.st && s.st !== 'pad', 90000, 80);
  const skip = await skipAway(page);
  const before = await snap(page);
  const result = await page.evaluate((frac) => {
    const p = window.__ps3d;
    const S = p.S;
    const desc = p.wkDescSec();
    const ret = p.wkReturnSec();
    const go = S.wk.go;
    const home = S.wk.down + (desc + ret) * 1000;
    const c0 = S.tk.c0;
    const made = S.cg.made;
    const loads = S.loads;
    const money = S.money;
    const fillGo = p.fillAt(go);
    p.settleTo(home, null);
    const mid = { c0: S.tk.c0, made: S.cg.made, loads: S.loads, money: S.money, fill: p.fillAt(home), go: S.wk.go || 0, hs: S.wk.hs ? 1 : 0, dep: S.tk.dep || 0 };
    p.settleTo(home, null);
    const end = { c0: S.tk.c0, made: S.cg.made, loads: S.loads, money: S.money, fill: p.fillAt(home), go: S.wk.go || 0, hs: S.wk.hs ? 1 : 0, dep: S.tk.dep || 0 };
    return { go, home, gap: home - go, c0, made, loads, money, fillGo, frac, mid, end, now: p.nowMs() };
  }, FRAC);
  const gap = result.gap;
  const d1 = result.mid.c0 - result.c0;
  const d2 = result.end.c0 - result.c0;
  check(checks, 'home_shift_once',
    Math.abs(d1 - gap) < 2 && Math.abs(d2 - d1) < 1,
    `gap=${gap} Δc0 first=${d1} second=${d2} (second settle must not move c0 again)`);
  check(checks, 'idempotent_counts',
    result.mid.made === result.made && result.end.made === result.made && result.mid.loads === result.loads && result.end.loads === result.loads,
    `made ${result.made}→${result.mid.made}→${result.end.made} loads ${result.loads}→${result.mid.loads}→${result.end.loads}`);
  check(checks, 'idempotent_fill',
    near(result.mid.fill, result.fillGo, 1e-3) && near(result.end.fill, result.fillGo, 1e-3) && result.mid.fill > 0.2,
    `fillAt(go)=${result.fillGo} fillAt(home) after1=${result.mid.fill} after2=${result.end.fill}`);
  return { checks, pickup, before, skip, result };
}

async function runAwayReload(browser, errors) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();
  attachLogs(page, errors);
  try {
    await boot(page, { ts: 20, fresh: true });
    const { pickup } = await seedPickup(page);
    const away = await waitSnap(page, (s) => s.st === 'away' && s.minerOff && s.go > 0, 90000, 80);
    const dump = await captureSave(page);
    await boot(page, { ts: 1, fresh: false });
    const after = await snap(page);
    const checks = [];
    check(checks, 'away_reload_fill',
      near(after.fillAt, pickup.fillAt, 1e-3) && after.fillAt > 0.2,
      `pickup=${pickup.fillAt} away=${away.fillAt} reload=${after.fillAt}`);
    check(checks, 'away_reload_counts',
      after.made === away.made && after.loads === away.loads && after.made === pickup.made,
      `pickup made=${pickup.made} loads=${pickup.loads} away made=${away.made} loads=${away.loads} reload made=${after.made} loads=${after.loads}`);
    check(checks, 'away_reload_still_away',
      after.go > 0 && after.minerOff && after.t < (after.homeAt || Infinity),
      `go=${after.go} down=${after.down} st=${after.st} minerOff=${after.minerOff} homeIn=${after.homeIn}`);
    return { checks, pickup, away, after, dumpKeys: Object.keys(dump) };
  } finally {
    await page.close();
    await ctx.close();
  }
}

async function runHomeReload(browser, errors) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();
  attachLogs(page, errors);
  try {
    await boot(page, { ts: 20, fresh: true });
    const { pickup } = await seedPickup(page);
    await waitSnap(page, (s) => s.st && s.st !== 'pad', 90000, 80);
    await skipAway(page);
    const crossed = await watchHome(page, 60000);
    const justAfter = crossed.firstAfter;
    if (!justAfter) throw new Error('home reload: never crossed home');
    const dump = await captureSave(page);
    const savedFill = justAfter.fillAt;
    const savedMade = justAfter.made;
    const savedLoads = justAfter.loads;
    const saveWall = Date.now();
    await page.close();
    await ctx.close();

    const ctx2 = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page2 = await ctx2.newPage();
    attachLogs(page2, errors);
    try {
      await installSave(page2, dump);
      await boot(page2, { ts: 1, fresh: false });
      const after = await snap(page2);
      const elapsed = (Date.now() - saveWall) / 1000;
      const fillSec = after.fillSec || 120;
      const expected = savedFill + elapsed / fillSec;
      const checks = [];
      const room = (1 - savedFill) * fillSec;
      const countsOk = elapsed + 5 < room
        ? after.made === savedMade && after.loads === savedLoads
        : after.loads >= savedLoads && after.loads - savedLoads <= 1 + Math.floor(elapsed / (fillSec + 60));
      check(checks, 'home_reload_counts',
        countsOk,
        `saved made=${savedMade} loads=${savedLoads} reload made=${after.made} loads=${after.loads} elapsed≈${elapsed.toFixed(1)}s room=${room.toFixed(1)}s`);
      check(checks, 'home_reload_fill_continues',
        after.fillAt > 0.2 && (after.dep || near(after.fillAt, Math.min(1, expected), 0.15)),
        `savedFill=${savedFill} reload=${after.fillAt} expected≈${expected.toFixed(4)} dep=${after.dep} elapsed≈${elapsed.toFixed(1)}s`);
      return { checks, pickup, justAfter, after, expected, elapsed };
    } finally {
      await page2.close();
      await ctx2.close();
    }
  } catch (e) {
    try { await page.close(); await ctx.close(); } catch (e2) {}
    throw e;
  }
}

async function runSelfCheck() {
  const browser = await launchBrowser();
  const errors = [];
  const report = {
    host: HOST, expect: EXPECT, frac: FRAC, started: new Date().toISOString(),
    seeding: {
      url: '/dev/?mock=1&qa=1&ts=20&fresh=1',
      code: CODE, name: NAME, frac: FRAC,
      hold: 'holdCap()', bay: 0, autoLaunch: true,
      skip: 'PS_QA.skipToTouchdown() after the ship leaves the pad',
      reloads: 'fresh omitted; localStorage planetstack-dev-<code> only',
    },
    phases: {},
  };
  try {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await ctx.newPage();
    attachLogs(page, errors);
    log('boot home path');
    await boot(page, { ts: 20, fresh: true });
    log('home path running');
    report.phases.home = await runHomePath(page);
    log('home path done ' + (report.phases.home.checks || []).map((c) => c.name + ':' + (c.pass ? 'P' : 'F')).join(','));
    await page.close();
    await ctx.close();

    const ctxI = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const pageI = await ctxI.newPage();
    attachLogs(pageI, errors);
    log('boot idempotent');
    await boot(pageI, { ts: 20, fresh: true });
    report.phases.idempotent = await runIdempotent(pageI);
    log('idempotent done');
    await pageI.close();
    await ctxI.close();

    log('away reload');
    report.phases.awayReload = await runAwayReload(browser, errors);
    log('home reload');
    report.phases.homeReload = await runHomeReload(browser, errors);
    log('reloads done');

    const checks = [
      ...(report.phases.home.checks || []),
      ...(report.phases.idempotent.checks || []),
      ...(report.phases.awayReload.checks || []),
      ...(report.phases.homeReload.checks || []),
    ];
    report.checks = checks;
    report.pageErrors = errors;
    const coreNames = ['made_loads_stable', 'fill_resume', 'no_burst'];
    const coreFail = checks.filter((c) => coreNames.includes(c.name) && !c.pass);
    const anyFail = checks.filter((c) => !c.pass);
    const observed = checks.some((c) => c.name === 'home_observed' && c.pass);
    if (EXPECT === 'fail') {
      report.ok = observed && coreFail.length >= 1 && errors.filter((e) => e.startsWith('PAGEERROR')).length === 0;
      report.summary = report.ok
        ? `UNFIXED as expected: home frame observed and core assertions failed (${coreFail.map((c) => c.name).join(', ')})`
        : `UNFIXED unexpected: observed=${observed} coreFail=${coreFail.map((c) => c.name).join(',') || 'none'} pageErrors=${errors.length}`;
    } else {
      report.ok = anyFail.length === 0 && errors.filter((e) => e.startsWith('PAGEERROR')).length === 0;
      report.summary = report.ok ? 'FIXED: all assertions passed' : `FIXED unexpected fail: ${anyFail.map((c) => c.name).join(', ')}`;
    }
    report.coreFail = coreFail.map((c) => c.name);
    report.anyFail = anyFail.map((c) => c.name);
    return report;
  } catch (e) {
    report.ok = false;
    report.error = String(e && e.stack || e);
    report.summary = 'ERROR ' + (e && e.message || e);
    report.pageErrors = errors;
    return report;
  } finally {
    await browser.close();
  }
}

async function injectOverlay(page) {
  await page.evaluate(() => {
    if (document.getElementById('mrOverlay')) return;
    const el = document.createElement('div');
    el.id = 'mrOverlay';
    el.style.cssText = 'position:fixed;left:16px;bottom:78px;z-index:40;pointer-events:none;font:700 22px/1.35 ui-monospace,SFMono-Regular,monospace;color:#fff;background:rgba(6,10,18,0.88);padding:12px 16px;border-radius:10px;border:2px solid #7ff3ff;min-width:360px;white-space:pre;text-shadow:0 1px 2px #000';
    document.body.appendChild(el);
    const tick = () => {
      const p = window.__ps3d;
      if (!p || !p.S || !p.S.cg) { el.textContent = 'loading…'; requestAnimationFrame(tick); return; }
      const t = p.nowMs(), S = p.S;
      const desc = p.wkDescSec ? p.wkDescSec() : 0;
      const ret = p.wkReturnSec ? p.wkReturnSec() : 0;
      const homeAt = S.wk && S.wk.down > 0 ? S.wk.down + (desc + ret) * 1000 : 0;
      const go = (S.wk && S.wk.go) || 0;
      let fill = null; try { fill = p.fillAt(t); } catch (e) {}
      const homeIn = homeAt ? (homeAt - t) / 1000 : null;
      let phase = 'BEFORE PICKUP';
      if (go && (!homeAt || t < homeAt)) phase = 'FROZEN (crew away)';
      else if (go) phase = 'HOME';
      else if (S.cg.launches > 0) phase = 'RESUMED';
      const panel = document.getElementById('ecPanel');
      if (panel && panel.getBoundingClientRect().height > 80) { const b = document.getElementById('ecClose'); if (b) b.click(); }
      el.textContent = [
        'MINE  ·  SILO logicalFill',
        'phase   ' + phase,
        'fill    ' + (fill == null ? '—' : (fill * 100).toFixed(1) + '%'),
        'made ' + S.cg.made + '    loads ' + S.loads,
        'home    ' + (homeIn == null ? (go ? 'taxi out' : '—') : (homeIn >= 0 ? homeIn.toFixed(1) + 's' : 'back')),
      ].join('\n');
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
}

async function runClip() {
  fs.mkdirSync(CLIP_DIR, { recursive: true });
  const browser = await launchBrowser(!HEADED);
  const errors = [];
  try {
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1200 } });
    const page = await ctx.newPage();
    attachLogs(page, errors);
    await boot(page, { ts: 8, fresh: true });
    await page.evaluate((frac) => {
      const p = window.__ps3d;
      try { p.ecHangUp(); } catch (e) {}
      p.goSite(1);
      if (p.camera && p.camera.userData) p.camera.userData.dist = 22;
      const t = p.nowMs(), fs = p.fillSec() * 1000, k = p.S.tk;
      k.c0 = t - frac * fs; k.add = 0; k.lr = 0; k.dep = 0; k.paid = false;
      k.sr = 0; k.hr = 0; k.tp = 0; k.sm = 0; k.hm = 0; k.gw = 0; k.gs = 0;
      k.q = 0; k.qd = [];
      p.S.tz = { c: { by: 0, rel: 0 }, b: { by: -1, rel: 0 } };
      p.poseNow();
    }, 0.55);
    await injectOverlay(page);
    if (GATE) {
      fs.writeFileSync('/tmp/mr/clip-ready', String(Date.now()));
      const deadline = Date.now() + 120000;
      while (!fs.existsSync('/tmp/mr/clip-go')) {
        if (Date.now() > deadline) throw new Error('clip gate timeout');
        await sleep(80);
      }
    }
    await sleep(900);
    await page.evaluate(() => window.__ps3d.poseNow());
    const before = await snap(page);
    const still1 = path.join(CLIP_DIR, 'silo_fill_before_pickup.png');
    await page.screenshot({ path: still1, type: 'png' });
    await sleep(350);
    await page.evaluate((frac) => {
      const p = window.__ps3d, S = p.S, t = p.nowMs();
      const k = S.tk, fs = p.fillSec() * 1000;
      k.c0 = t - frac * fs; k.add = 0; k.dep = 0; k.paid = false; k.sr = 0; k.sm = 0; k.lr = 0; k.hr = 0; k.tp = 0; k.hm = 0;
      S.cg.sh.hold = p.holdCap(); S.cg.sh.req = 0; if (S.cg.sh.man) S.cg.sh.man = 0;
      S.cg.bay = 0; S.cg.autoLaunch = true; S.cg.autoLoad = true;
      if (S.cg.pc) S.cg.pc = { k: '', t0: 0 }; S.cg.rd = 0;
      p.settleTo(t, null);
      const go = (S.wk && S.wk.go) || 0;
      if (go > 0) { k.c0 = go - frac * fs; k.add = 0; k.dep = 0; k.paid = false; k.sr = 0; k.sm = 0; }
    }, 0.55);
    const pickup = await snap(page);
    await waitSnap(page, (s) => s.st && s.st !== 'pad', 90000, 80);
    const skip = await skipAway(page);
    const crossed = await watchHome(page, 90000);
    if (!crossed.firstAfter) throw new Error('clip: crew never got home');
    await sleep(800);
    await page.evaluate(() => { window.__ps3d.goSite(1); if (window.__ps3d.camera) window.__ps3d.camera.userData.dist = 22; window.__ps3d.poseNow(); });
    const atHome = await snap(page);
    const still2 = path.join(CLIP_DIR, 'silo_fill_at_home.png');
    await page.screenshot({ path: still2, type: 'png' });
    await sleep(2800);
    await page.evaluate(() => window.__ps3d.poseNow());
    const risen = await snap(page);
    const still3 = path.join(CLIP_DIR, 'silo_fill_risen.png');
    await page.screenshot({ path: still3, type: 'png' });
    await sleep(800);
    await page.close();
    await ctx.close();
    const resumed = atHome && before && near(atHome.fillAt, pickup.fillAt, 0.05) && atHome.fillAt > 0.4 && risen.fillAt > atHome.fillAt + 0.15 && atHome.made === before.made && atHome.loads === pickup.loads;
    const report = {
      ok: resumed && fs.existsSync(still1) && fs.existsSync(still2) && fs.existsSync(still3),
      before, pickup, atHome, risen, skip,
      stills: [still1, still2, still3], errors,
      note: 'ts=8, mine camera. Fill seeded near 0.55 and locked at pickup so the truck stays under the chute. Full hold + autoLaunch. PS_QA.skipToTouchdown after the ship leaves the pad. Walk home plays at 8x.',
    };
    fs.writeFileSync('/tmp/mr/clip-report.json', JSON.stringify(report, null, 2));
    console.log(JSON.stringify({ ok: report.ok, before: before && before.fillAt, pickup: pickup && pickup.fillAt, atHome: atHome && atHome.fillAt, risen: risen && risen.fillAt, made: [before && before.made, atHome && atHome.made, risen && risen.made], loads: [before && before.loads, pickup && pickup.loads, atHome && atHome.loads], skip: skip && skip.skippedSec, stills: report.stills, errors }, null, 2));
    return report.ok ? 0 : 1;
  } finally {
    await browser.close();
  }
}

const clipCode = CLIP ? await runClip() : null;
if (CLIP) process.exit(clipCode);

const report = await runSelfCheck();
const text = JSON.stringify(report, null, 2);
if (OUT) {
  fs.mkdirSync(path.dirname(path.resolve(OUT)), { recursive: true });
  fs.writeFileSync(OUT, text);
}
console.log(report.summary);
for (const c of report.checks || []) console.log(`${c.pass ? 'PASS' : 'FAIL'}  ${c.name}  ${c.detail}`);
if (report.error) console.log(report.error);
if (report.pageErrors && report.pageErrors.length) console.log('LOGS ' + report.pageErrors.slice(0, 8).join(' | '));
process.exit(report.ok ? 0 : 1);
