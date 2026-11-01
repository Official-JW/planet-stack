#!/usr/bin/env node
// Planet Stack auto-check (QA_ESCAPES E1 + E2 + console / network / md5), one headless Chromium, ~1 min per viewport.
// Usage: node autocheck.js [url, default dev/] [--expect md5s.json] [--code 00000 | env PS_TESTER_CODE] [--name "QA Bot"]
//        [--viewports 393x852,375x812] [--out ./out] [--keep-shots] [--load-timeout 90] [--qa] [--ts N] [--skip] [--qa-ignored] [--max-load 10] [--load-wait 20]
// Exit: 0 = no FAIL, 1 = at least one FAIL, 2 = no FAIL but the script itself crashed / bad arguments / a hash fetch failed (ERROR row),
//       3 = load gate: the box stayed at/above --max-load (default 10) for --load-wait minutes (default 20), so no browser was started.
'use strict';
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const HERE = __dirname;
if (!process.env.PLAYWRIGHT_BROWSERS_PATH && fs.existsSync(path.join(HERE, 'browsers'))) process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(HERE, 'browsers');
const { chromium } = require('playwright');

// ---------- args ----------
function parseArgs(argv) {
  const a = { url: null, expect: null, code: process.env.PS_TESTER_CODE || '', name: process.env.PS_TESTER_NAME || 'QA Autocheck',
    viewports: '393x852,375x812', dpr: 3, out: path.join(HERE, 'out'), keepShots: false, loadTimeout: 90, maxLoad: 10, loadWait: 20 };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i], v = () => { if (i + 1 >= argv.length) throw new Error('missing value for ' + k); return argv[++i]; };
    if (k === '--expect') a.expect = v(); else if (k === '--code') a.code = v(); else if (k === '--name') a.name = v();
    else if (k === '--viewports') a.viewports = v(); else if (k === '--out') a.out = path.resolve(v());
    else if (k === '--dpr') a.dpr = +v(); else if (k === '--quiet') QUIET = true;
    else if (k === '--ts') a.ts = v(); else if (k === '--skip') a.skip = true; else if (k === '--qa') a.qa = true;
    else if (k === '--qa-ignored') a.qaIgnored = true;   // live/ (or any non-dev build): load with ?qa=1&ts=N and assert it runs at 1x with no badge and no PS_QA, then stop   // QA fast-forward (dev/ build only): ?qa=1&ts=N; --skip calls PS_QA.skipToTouchdown()
    else if (k === '--max-load') a.maxLoad = +v(); else if (k === '--load-wait') a.loadWait = +v();
    else if (k === '--keep-shots') a.keepShots = true; else if (k === '--load-timeout') a.loadTimeout = +v();
    else if (k === '-h' || k === '--help') { console.log(fs.readFileSync(__filename, 'utf8').split('\n').slice(1, 6).join('\n')); process.exit(0); }
    else if (!k.startsWith('--') && !a.url) a.url = k; else throw new Error('unknown argument ' + k);
  }
  if (!a.url) a.url = 'https://official-jw.github.io/planet-stack/dev/';   // default target: dev/ (needs a tester code)
  if ((a.qa || a.qaIgnored) && a.ts == null) a.ts = '10';   // --qa / --qa-ignored: ?qa=1&ts=10 unless --ts N overrides the 10
  if (a.ts != null) { const n = Number(a.ts); if (!isFinite(n) || n <= 0) throw new Error('--ts needs a number (the game clamps it to 1-60)');
    const u = new URL(a.url); u.searchParams.set('qa', '1'); u.searchParams.set('ts', String(n)); a.url = u.toString(); }
  else if (a.skip) { const u = new URL(a.url); u.searchParams.set('qa', '1'); a.url = u.toString(); }   // --skip alone: the hook needs ?qa=1 (scale stays 1x)
  a.vps = a.viewports.split(',').map(s => { const m = /^(\d+)x(\d+)$/.exec(s.trim()); if (!m) throw new Error('bad viewport ' + s); return { w: +m[1], h: +m[2] }; });
  return a;
}

const IPHONE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1';
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const md5 = (buf) => crypto.createHash('md5').update(buf).digest('hex');
const rows = [];   // { vp, check, res: PASS|FAIL|WARN|n/a, detail }
const T_START = Date.now(); let QUIET = false;
const log = (...m) => { if (!QUIET) process.stderr.write(`[${((Date.now() - T_START) / 1000).toFixed(1)}s] ${m.join(' ')}\n`); };
const add = (vp, check, res, detail = '') => { log(vp, res, check, res === 'FAIL' ? '— ' + String(detail).slice(0, 200) : ''); rows.push({ vp, check, res, detail: String(detail).replace(/\s+/g, ' ').slice(0, 220) }); };
const shots = [];

// page-side instrumentation (no game code is changed): counts Eve-voice-length WebAudio buffers and <audio> plays so E2 can tell when a clip ends.
const INIT = (devId) => {
  try { if (!localStorage.getItem('planetstack-dev-device')) localStorage.setItem('planetstack-dev-device', devId); } catch (e) {}   // same QA device in both viewports → the dev Worker lock never sees two devices
  const A = window.__acAudio = { active: 0, n: 0 };
  try {
    const P = window.AudioBufferSourceNode && AudioBufferSourceNode.prototype;
    if (P) { const st = P.start; P.start = function (...x) { const d = this.buffer ? this.buffer.duration : 0;
      if (d > 0.25 && d < 30) { A.active++; A.n++; let done = false; const end = () => { if (!done) { done = true; A.active--; } };
        this.addEventListener('ended', end, { once: true }); const sp = this.stop; this.stop = function (...y) { try { return sp.apply(this, y); } finally { end(); } }; }
      return st.apply(this, x); }; }
    const M = HTMLMediaElement.prototype, mp = M.play;
    M.play = function (...x) { if (/\/eve\//.test(this.currentSrc || this.src || '') && !this.__acT) { this.__acT = 1; A.active++; A.n++; let done = false;
      const end = () => { if (!done) { done = true; A.active--; } }; for (const ev of ['ended', 'pause', 'error', 'emptied']) this.addEventListener(ev, end, { once: true }); }
      return mp.apply(this, x); };
  } catch (e) {}
};

// ---------- helpers that run in the page ----------
const PAGE_STATE = () => {
  const P = window.__ps3d || {}, vis = (el) => { if (!el || el.hidden) return false; const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    return cs.display !== 'none' && cs.visibility !== 'hidden' && +cs.opacity > 0.05 && r.width * r.height > 0; };
  return { hook: !!window.__ps3d, coverGone: !!P.coverGone, site: P.S ? P.S.site : null, stations: P.STATIONS || null, name: (document.getElementById('name') || {}).textContent || '',
    gate: vis(document.getElementById('gate')), nameGate: vis(document.getElementById('nameGate')), gateMsg: P.gateMsg || '', devStop: vis(document.getElementById('devStop')),
    devStopMsg: ((document.getElementById('devStopMsg') || {}).textContent || ''),
    ui: typeof P.upRects === 'function' && document.getElementById('upPanel') ? 'new' : document.getElementById('grab') && document.getElementById('sheet') ? 'old' : document.getElementById('upPanel') ? 'new-nohook' : 'none',
    camX: typeof P.camX === 'number' ? P.camX : null, frames: typeof P.frames === 'number' ? P.frames : null,
    gap: typeof P.PX === 'number' && P.PADI > 0 ? P.PX / P.PADI : null,
    sx: Array.isArray(P.SX) ? P.SX.slice() : null, ord: Array.isArray(P.ORD) ? P.ORD.slice() : null };   // per-station x and the swipe (x) order, when the build has them (Life Support move)   // station spacing (m) = pad x / pad index; the camera rests at site * gap
};

async function touchSwipe(cdp, x0, y, dx, steps = 4, ms = 160) {   // real CDP touch events; moves are queued without waiting for each ack (a loaded box acks slowly)
  const q = [cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: x0, y }] })];
  for (let i = 1; i <= steps; i++) { await sleep(ms / steps); q.push(cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x0 + dx * i / steps, y }] })); }
  q.push(cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] })); await Promise.all(q);
}
const hitId = (page, x, y) => page.evaluate(([x, y]) => { const e = document.elementFromPoint(x, y); return e ? (e.id || e.tagName.toLowerCase()) + (e.closest('#ec') ? '@ec' : '') : 'none'; }, [x, y]);

// settle after a station switch: S.site == want, the camera within 0.5 m of its resting x (want * gap), and at least 1 more frame
// drawn after that, so projected tap rects come from a finished glide. Times out after 4 s; with vp given, a timeout adds a WARN row.
// Older builds with no frames / PX hooks: falls back to "camX stopped moving" (< 0.05 m between two reads).
async function settle(page, want, vp = null, ms = 4000) {
  const t0 = Date.now(); let last = null, f0 = null, s = null;
  while (Date.now() - t0 < ms) {
    s = await page.evaluate(PAGE_STATE);
    const atRest = s.camX !== null && (s.sx ? Math.abs(s.camX - s.sx[want]) < 0.5 : s.gap ? Math.abs(s.camX - want * s.gap) < 0.5 : last !== null && Math.abs(s.camX - last) < 0.05);
    if (s.site === want && atRest) { if (s.frames === null) return s; if (f0 === null) f0 = s.frames; else if (s.frames > f0) return s; }
    else f0 = null;
    last = s.camX; await sleep(100);
  }
  s = await page.evaluate(PAGE_STATE); s.timedOut = true;   // callers retry on this (EM 18:31)
  if (vp) add(vp, `SETTLE ${want}`, 'WARN', `timeout after ${ms / 1000} s (box 1-min load ${load1() ?? 'n/a'}): site=${s.site} (want ${want}), camX=${s.camX === null ? 'n/a' : s.camX.toFixed(2)}${s.gap ? ` (rest ${want * s.gap})` : ''}, frames=${s.frames}${f0 !== null ? ` (${s.frames - f0} since at rest)` : ''}`);
  return s;
}

// old sheet: what it shows right now
const OLD_SHEET = () => { const P = window.__ps3d || {}, rowsV = [...document.querySelectorAll('#sheet .row')].filter(r => r.style.display !== 'none' && !r.hidden && getComputedStyle(r).display !== 'none')
  .map(r => ((r.querySelector('.hl') || {}).textContent || '').trim());
  return { open: typeof P.sheetOpen === 'boolean' ? P.sheetOpen : document.body.classList.contains('sheet-open'), rows: rowsV, sum: ((document.getElementById('sum') || {}).textContent || '').trim(),
    site: P.S ? P.S.site : null, drill: P.S ? P.S.drill : null, REF: 2 }; };
// the build's own station → object mapping for the old sheet (Mine rows everywhere; Refinery rows at the Refinery once Drill > 1)
const oldExpect = (st, site, drill) => { const n = st[site] || ''; if (/refinery/i.test(n) && drill > 1) return { rows: ['Fuel Refill', 'He-3 Purity'], own: true };
  return { rows: ['Drill', 'Chute Feed Rate'], own: /^mine$/i.test(n) || /refinery/i.test(n) }; };
const sameRows = (a, b) => b.every(x => a.includes(x)) && a.filter(x => x !== 'Trucks').every(x => b.includes(x));

// old sheet: real tap on the Upgrade handle until the sheet is in the wanted state (a tap toggles; a loaded box can drop or delay one)
async function setOldSheet(page, want) {
  for (let k = 0; k < 3; k++) {
    if ((await page.evaluate(OLD_SHEET)).open === want) return k;
    await sleep(350); const g = await page.locator('#grab').boundingBox(); if (!g) return -1;   // gap so two taps on the same spot never read as a double-tap
    await page.touchscreen.tap(g.x + g.width / 2, g.y + Math.min(14, g.height / 2));
    const t = Date.now() + 2500; while (Date.now() < t) { if ((await page.evaluate(OLD_SHEET)).open === want) return k + 1; await sleep(150); }
  }
  return (await page.evaluate(OLD_SHEET)).open === want ? 3 : -1;
}
// new panel: open card state
const NEW_PANEL = () => { const P = window.__ps3d || {}, el = document.getElementById('upPanel');
  return { cur: P.upCur || null, shown: !!el && !el.hidden, name: ((document.getElementById('upName') || {}).textContent || '').trim(),
    kick: ((document.getElementById('upKick') || {}).textContent || '').trim(), site: P.S ? P.S.site : null }; };

// card title: [data-card-title] (gc-ui2 and later: its value, else its text) or, on builds without it, #upName's text (gc-ui1 7c27f98). src says which.
const CARD_TITLE = () => { const el = document.getElementById('upPanel'), open = !!el && !el.hidden && getComputedStyle(el).display !== 'none';
  const a = (el && el.querySelector('[data-card-title]')) || document.querySelector('[data-card-title]');
  const kick = ((document.getElementById('upKick') || {}).textContent || '').trim();
  if (a) return { open, kick, src: 'attr', title: ((a.getAttribute('data-card-title') || '') || a.textContent || '').trim() };
  return { open, kick, src: 'fallback #upName', title: ((document.getElementById('upName') || {}).textContent || '').trim() }; };
// what each tap should open (EM 10/31). Title match = starts with (case-insensitive), so 'Fuel' passes 'Fuel Refill'.
// padFuel = the Launch Pad fuel hoses + tanks box (Hose_LOX / Hose_LCH4; 7c27f98's pad GLB has no separate tank node). Empty stations = stations with no UPT target of their own.
// gc-ui2 gives the 5 empty stations their own 'Coming soon' targets (title = station name, kicker '<Station> · Coming soon'), so those ids are listed too.
// 'Coming soon' passes when the title OR the kicker contains it. NO CARD rows are settled at the end of each viewport: FAIL when the build has
// [data-card-title] (gc-ui2 and later), info on older builds (CV.attr).
// 75cde37+: Dock, Shipyard and Habitat start unbuilt, so a fresh save shows 'Not built yet' (GD 22:43 spec); matched like 'Coming soon'.
const CARD_EMPTY = 'Coming soon', CARD_NB = 'Not built yet', CARD_WANT = { drill: 'Drill', padFuel: 'Fuel', fuelPlant: 'Fuel', lifeSupport: CARD_EMPTY, dock: CARD_NB, shipyard: CARD_NB, habitat: CARD_NB, engineering: CARD_EMPTY };
let CV = { attr: false, nocard: [] };
const cardRow = (vp, label, c, want) => { if (c && c.src === 'attr') CV.attr = true;
  if (!c || !c.open) { add(vp, label, 'NO CARD', `no card opened (want "${want}")${c && c.why ? '; ' + c.why : ''}`); CV.nocard.push(rows[rows.length - 1]); return; }
  const lw = want.toLowerCase(), cw = lw === 'coming soon' || lw === 'not built yet', ok = cw ? (c.title + ' ' + c.kick).toLowerCase().includes(lw) : c.title.toLowerCase().startsWith(lw);
  add(vp, label, ok ? 'PASS' : 'FAIL', `title "${c.title}"${cw ? `, kicker "${c.kick}"` : ''} (${c.src})${ok ? '' : `, want "${want}"`}${c.retry ? `; opened on the settle retry (${c.retry})` : ''}`); };
// Launch Pad tanks (gc-ui2): padFuel's extra tank box (UPT padFuel.add), else a mesh named /tank/i in the pad model. Taps a point inside it where
// the canvas is on top and pickUp gives padFuel. Returns null when the build has neither (-> info row 'no pad tank meshes').
async function waitUc(page, ms = 4000) {   // gc-ui2 card camera: __ps3d.uc.w eases 1 → 0 after a card closes; measure only once it is 0 (no hook: no wait)
  const t0 = Date.now(); let w = null; while (Date.now() - t0 < ms) { w = await page.evaluate(() => { const u = window.__ps3d && window.__ps3d.uc; return u && typeof u.w === 'number' ? u.w : null; }); if (w === null || w === 0) return { ok: true, w, ms: Date.now() - t0 }; await sleep(100); }
  return { ok: false, w, ms: Date.now() - t0 }; }
async function padTankCard(page, W, H) {
  await closeCard(page); const uw = await waitUc(page);
  const pt = await page.evaluate(([W, H]) => { const P = window.__ps3d, T = P.THREE, o = P.stationObjs && P.stationObjs[P.PADI], u = (P.UPT || []).find(t => t.id === 'padFuel');
    let b = null, src = '';
    if (u && typeof u.add === 'function' && T) { b = u.add(new T.Box3()); src = 'padFuel tank box (UPT.add)'; }
    if ((!b || b.isEmpty()) && o && T) { let m = null; o.traverse(n => { if (!m && n.isMesh && /tank/i.test(n.name || '') && n.visible) m = n; }); if (m) { b = new T.Box3().setFromObject(m); src = 'mesh ' + m.name; } }
    if (!b || b.isEmpty()) return null;
    let l = Infinity, r = -Infinity, t = Infinity, bt = -Infinity;
    for (let k = 0; k < 8; k++) { const q = P.toScreen(k & 1 ? b.max.x : b.min.x, k & 2 ? b.max.y : b.min.y, k & 4 ? b.max.z : b.min.z); if (q.z > 1) continue; l = Math.min(l, q.x); r = Math.max(r, q.x); t = Math.min(t, q.y); bt = Math.max(bt, q.y); }
    l = Math.max(l, 8); r = Math.min(r, W - 8); t = Math.max(t, 8); bt = Math.min(bt, H - 8); if (!(r > l && bt > t)) return { src, why: 'tank box off screen' };
    for (const fy of [.5, .35, .65, .2, .8]) for (const fx of [.5, .3, .7, .15, .85]) { const x = l + (r - l) * fx, y = t + (bt - t) * fy, e = document.elementFromPoint(x, y), h = P.pickUp(x, y);
      if (e && e.tagName === 'CANVAS' && h && h.t.id === 'padFuel') return { x, y, src }; }
    return { src, why: 'no point on the tanks where the canvas is on top and pickUp gives padFuel' }; }, [W, H]);
  const ucNote = uw.ok ? '' : `; card camera not back after ${uw.ms} ms (uc.w ${uw.w})`;
  if (!pt) return null;
  if (pt.x == null) return { open: false, why: `${pt.src}: ${pt.why}${ucNote}` };
  await page.touchscreen.tap(pt.x, pt.y); let c = null;
  for (let k = 0; k < 8; k++) { await sleep(250); c = await page.evaluate(CARD_TITLE); if (c.open) break; }
  c.why = `tapped ${pt.src} at ${Math.round(pt.x)},${Math.round(pt.y)}${ucNote}`; if (c.open) await closeCard(page); return c;
}
async function holdStill(page, id, ms = 4000) {   // wait until the target's screen rect stops moving (centre moved < 1.5 px over 300 ms)
  const c = () => page.evaluate((id) => { const t = window.__ps3d.upRects().find(x => x.id === id); return t && t.r ? [(t.r.l + t.r.r) / 2, (t.r.t + t.r.b) / 2] : null; }, id);
  const t0 = Date.now(); let a = await c();
  while (Date.now() - t0 < ms) { await sleep(300); const b = await c(); if (a && b && Math.hypot(b[0] - a[0], b[1] - a[1]) < 1.5) return { ok: true, ms: Date.now() - t0 }; a = b; }
  return { ok: false, ms: Date.now() - t0 }; }
const load1 = () => { try { return +fs.readFileSync('/proc/loadavg', 'utf8').split(' ')[0]; } catch (e) { return null; } };
async function closeCard(page) { const x = await page.locator('#upX').boundingBox().catch(() => null); if (x && (await page.evaluate(NEW_PANEL)).cur) { await page.touchscreen.tap(x.x + x.width / 2, x.y + x.height / 2); await sleep(300); }
  if ((await page.evaluate(NEW_PANEL)).cur) await page.evaluate(() => window.__ps3d.closeUp('qa')); }
// empty station: tap the middle of the station's own model (projected world box centre, then a 5x5 grid of its rect on the canvas)
async function emptyStationCard(page, i, W, H) {
  const pt = await page.evaluate(([i, W, H]) => { const P = window.__ps3d, o = P.stationObjs && P.stationObjs[i];
    let l = Infinity, r = -Infinity, t = Infinity, bt = -Infinity, src = 'the station model';
    const b = o && P.THREE ? new P.THREE.Box3().setFromObject(o) : null;
    if (b && !b.isEmpty()) for (let k = 0; k < 8; k++) { const q = P.toScreen(k & 1 ? b.max.x : b.min.x, k & 2 ? b.max.y : b.min.y, k & 4 ? b.max.z : b.min.z); if (q.z > 1) continue; l = Math.min(l, q.x); r = Math.max(r, q.x); t = Math.min(t, q.y); bt = Math.max(bt, q.y); }
    else { src = 'mid-screen (no station model loaded)'; l = W * 0.3; r = W * 0.7; t = H * 0.3; bt = H * 0.6; }
    l = Math.max(l, 8); r = Math.min(r, W - 8); t = Math.max(t, 8); bt = Math.min(bt, H - 8); if (!(r > l && bt > t)) return { why: 'station model off screen' };
    for (const fy of [.5, .4, .6, .3, .7]) for (const fx of [.5, .4, .6, .3, .7]) { const x = l + (r - l) * fx, y = t + (bt - t) * fy, e = document.elementFromPoint(x, y), h = P.pickUp(x, y);
      if (e && e.tagName === 'CANVAS' && !h) return { x, y, src }; }
    return { why: 'no free canvas point on ' + src }; }, [i, W, H]);
  if (pt.x == null) return { open: false, why: pt.why };
  await page.touchscreen.tap(pt.x, pt.y); let c = null;
  for (let k = 0; k < 8; k++) { await sleep(250); c = await page.evaluate(CARD_TITLE); if (c.open) break; }
  c.why = `tapped ${pt.src} at ${Math.round(pt.x)},${Math.round(pt.y)}`; if (c.open) await closeCard(page); return c;
}

// ---------- Eve (E2) ----------
const EVE_SAMPLE = () => {
  const P = window.__ps3d || {}, ec = P.ec || {}, panel = document.getElementById('ecPanel'), txt = (document.getElementById('ecTxt') || {}).textContent || '';
  const vis = (el) => { if (!el || el.hidden) return false; const cs = getComputedStyle(el), r = el.getBoundingClientRect(); return cs.display !== 'none' && cs.visibility !== 'hidden' && +cs.opacity > 0.05 && r.width * r.height > 0; };
  const SEL = ['#ecNext', '#ecDone', '#ecCue', '.ec-next', '.ec-done', '.ec-cue', '[data-cue]', '[data-eve-cue]'];
  let cueEl = null, cueKnown = false;
  for (const s of SEL) { const e = document.querySelector(s); if (e) { cueKnown = true; if (vis(e)) { cueEl = e; break; } } }
  if (!cueEl && panel) for (const e of panel.querySelectorAll('button, [role=button], .ec-say *')) { const t = (e.textContent || '').trim();
    if (/^(next|done)\b/i.test(t) && !e.closest('.ec-tab')) { cueKnown = true; if (vis(e)) { cueEl = e; break; } } }
  if (typeof P.eveCue !== 'undefined') cueKnown = true;
  const PSV = window.PS_DEV && window.PS_DEV.voice;
  const voice = PSV && 'src' in PSV ? !!PSV.src || (window.__acAudio && window.__acAudio.active > 0) : !!(window.__acAudio && window.__acAudio.active > 0);
  return { t: performance.now(), ring: ec.ring || null, call: ec.call || null, open: !!ec.open, li: ec.li, txt, talking: !!panel && panel.classList.contains('is-talking'),
    waiting: !!panel && panel.classList.contains('is-waiting'), voice, cue: cueEl ? (cueEl.textContent || '').trim() || 'cue' : null, cueKnown,
    voiceOn: PSV ? PSV.on !== false : null, voiceClips: window.__acAudio ? window.__acAudio.n : 0 };
};

async function eveCheck(page, vp, shot) {
  const t0 = Date.now(); let s = await page.evaluate(EVE_SAMPLE);
  if (!(await page.evaluate(() => !!(window.__ps3d && 'ec' in window.__ps3d && document.getElementById('ecPanel'))))) return add(vp, 'E2 Eve Next/Done cue', 'n/a', 'no Earth Coms panel or __ps3d.ec hook in this build');
  while (!s.ring && !s.call && Date.now() - t0 < 12000) { await sleep(200); s = await page.evaluate(EVE_SAMPLE); }
  if (!s.ring && !s.call) return add(vp, 'E2 Eve Next/Done cue', 'n/a', 'no Eve call rang within 12 s of the cover lifting');
  const beat = s.ring || s.call;
  let toastTaps = 0;
  while (!s.call && toastTaps < 3) {   // the toast slides in; under load a tap can land mid-animation, so re-tap (not counted as a bug unless all 3 miss)
    await sleep(toastTaps ? 0 : 600); const box = await page.locator('#ecToast').boundingBox(); if (!box) return add(vp, 'E2 Eve ' + beat, 'FAIL', 'call rang but the toast has no box to tap');
    await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2); toastTaps++;
    const tw = Date.now() + 3000; while (Date.now() < tw) { s = await page.evaluate(EVE_SAMPLE); if (s.call) break; await sleep(150); }
  }
  if (!s.call) { await shot(page, 'e2-toast'); return add(vp, 'E2 Eve ' + beat, 'FAIL', `3 real taps on the ringing toast did not answer the call (ring=${s.ring})`); }
  if (toastTaps > 1) add(vp, 'E2 Eve ' + beat + ' answer', 'WARN', `toast needed ${toastTaps} taps to answer`);
  const samples = [], tEnd = Date.now() + 45000; let lastLi = -1, advAt = 0;
  while (Date.now() < tEnd) {
    s = await page.evaluate(EVE_SAMPLE); samples.push(s);
    if (!s.call && samples.some(x => x.call)) break;
    if (s.call) {
      if (s.li !== lastLi) { lastLi = s.li; advAt = 0; }
      const ready = s.cue || (!s.cueKnown && s.waiting && !s.voice);
      const stuck = s.waiting && Date.now() - (advAt || (advAt = Date.now())) > 15000;   // voice never reports an end: move on after 15 s
      if ((ready || stuck) && s.open) { const b = await page.locator('#ecTxt').boundingBox(); if (b) await page.touchscreen.tap(b.x + Math.min(40, b.width / 2), b.y + b.height / 2); await sleep(250); }
      else if (!s.waiting) advAt = 0;
    }
    await sleep(40);
  }
  if (samples.length && samples[samples.length - 1].call) add(vp, 'E2 Eve ' + beat, 'FAIL', `call did not finish within 45 s (stuck on line ${samples[samples.length - 1].li + 1}; on a heavily loaded box this can be slowness, re-run to confirm)`);
  // per-line analysis on the timeline
  const lines = {}; for (const x of samples) if (x.call) (lines[x.li] = lines[x.li] || []).push(x);
  const cueKnown = samples.some(x => x.cueKnown || x.cue);
  for (const li of Object.keys(lines).sort((a, b) => a - b)) {
    const L = lines[li], fin = L.reduce((m, x) => x.txt.length > m.length ? x.txt : m, ''), tText = (L.find(x => x.txt === fin) || {}).t;
    const voiced = L.some(x => x.voice), tVoice = voiced ? Math.max(...L.filter(x => x.voice).map(x => x.t)) : null;
    const firstCue = L.find(x => x.cue), firstWait = L.find(x => x.waiting), last = +li === Math.max(...Object.keys(lines).map(Number));
    const tag = `E2 ${beat} line ${+li + 1}`;
    const vtxt = voiced ? `voice ended +${Math.round(tVoice - L[0].t)} ms` : 'no voice clip played';
    if (!cueKnown) {
      const early = firstWait && voiced && firstWait.t < tVoice;
      add(vp, tag, 'n/a', `no Next/Done cue element in this build (E2 feature not shipped). Info: text done +${Math.round(tText - L[0].t)} ms, ${vtxt}, 'STANDING BY' +${firstWait ? Math.round(firstWait.t - L[0].t) : '?'} ms${early ? ' (BEFORE voice ended)' : ''}`);
      continue;
    }
    if (!firstCue) { add(vp, tag, 'FAIL', 'cue never showed for this line'); await shot(page, 'e2-nocue-' + li); continue; }
    const bad = L.find(x => x.cue && (x.txt !== fin || x.voice));
    const word = last ? /done/i : /next/i;
    if (bad) { add(vp, tag, 'FAIL', `cue "${bad.cue}" showed while ${bad.txt !== fin ? 'text still typing' : 'voice still playing'} (+${Math.round(bad.t - L[0].t)} ms; ${vtxt})`); await shot(page, 'e2-early-' + li); }
    else if (!word.test(firstCue.cue) && firstCue.cue !== 'cue') add(vp, tag, 'FAIL', `cue reads "${firstCue.cue}", expected ${last ? 'Done' : 'Next'}`);
    else add(vp, tag, 'PASS', `cue "${firstCue.cue}" at +${Math.round(firstCue.t - L[0].t)} ms, after text (+${Math.round(tText - L[0].t)}) and ${vtxt}`);
  }
}

// ---------- one viewport ----------
async function runViewport(browser, A, vp, served, devId) {
  const VP = `${vp.w}x${vp.h}`, t0 = Date.now(); CV = { attr: false, nocard: [] };
  const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h }, screen: { width: vp.w, height: vp.h }, deviceScaleFactor: A.dpr, isMobile: true, hasTouch: true,
    userAgent: IPHONE_UA, serviceWorkers: 'block', locale: 'en-US', timezoneId: 'America/Los_Angeles' });
  let closing = false; const consoleErr = [], netFail = [];
  const shot = async (page, tag) => { try { fs.mkdirSync(A.out, { recursive: true }); const f = path.join(A.out, `fail-${VP}-${tag}.jpg`); await page.screenshot({ path: f, type: 'jpeg', quality: 45, scale: 'css', timeout: 8000 }); shots.push(f); } catch (e) {} };
  try {
    await ctx.addInitScript(INIT, devId);
    const page = await ctx.newPage(), cdp = await ctx.newCDPSession(page);
    await cdp.send('Network.enable'); await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
    const origin = new URL(A.url).origin;
    page.on('console', (m) => { if (!closing && m.type() === 'error') consoleErr.push(m.text() + (m.location() && m.location().url ? ` @ ${m.location().url.replace(origin, '')}:${m.location().lineNumber}` : '')); });
    page.on('pageerror', (e) => { if (!closing) consoleErr.push('pageerror: ' + (e && e.message)); });
    page.on('requestfailed', (r) => { if (!closing) netFail.push(`${r.method()} ${r.url().replace(origin, '')} ${(r.failure() || {}).errorText || 'failed'}`); });
    page.on('response', async (r) => {
      if (closing) return; const u = new URL(r.url()), st = r.status();
      if (st >= 400) netFail.push(`HTTP ${st} ${r.request().method()} ${r.url().replace(origin, '')}`);
      if (/^https?:$/.test(u.protocol) && u.origin === origin && r.request().method() === 'GET' && st === 200) { try { const h = md5(await r.body()); (served[u.pathname] = served[u.pathname] || new Set()).add(h); } catch (e) {} }
    });
    // 1) fresh load + gates
    log(VP, 'loading', A.url);
    await page.goto(A.url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    let s = await page.evaluate(PAGE_STATE), tl = Date.now() + A.loadTimeout * 1000, gateDone = false, nameDone = false;
    while (Date.now() < tl) {
      s = await page.evaluate(PAGE_STATE);
      if (s.devStop) { add(VP, 'LOAD', 'FAIL', 'dev stop screen: ' + s.devStopMsg); await shot(page, 'devstop'); return; }
      if (s.gate && !gateDone) {
        if (!A.code) { add(VP, 'LOAD (tester-code gate)', 'n/a', 'build has a tester-code gate; pass --code or PS_TESTER_CODE to test it'); return; }
        await page.locator('#gateCode').tap(); await page.keyboard.type(A.code, { delay: 30 }); await page.locator('#gateGo').tap();
        const tg = Date.now() + 15000; while (Date.now() < tg) { s = await page.evaluate(PAGE_STATE); if (!s.gate || s.gateMsg) break; await sleep(200); }
        if (s.gate) { add(VP, 'LOAD (tester-code gate)', 'FAIL', 'code refused: ' + (s.gateMsg || 'gate still up after 15 s')); await shot(page, 'gate'); return; }
        gateDone = true; add(VP, 'LOAD (tester-code gate)', 'PASS', 'code accepted (code not printed)'); continue;
      }
      if (s.nameGate && !nameDone) { await page.locator('#nameIn').tap(); await page.keyboard.type(A.name, { delay: 10 }); await page.locator('#nameGo').tap(); nameDone = true; await sleep(300); continue; }
      if (s.coverGone) break;
      await sleep(250);
    }
    if (!s.hook) { add(VP, 'LOAD', 'FAIL', 'no window.__ps3d QA hook; nothing else can be checked'); return; }
    if (!s.coverGone) { add(VP, 'LOAD', 'FAIL', `loading cover still up after ${A.loadTimeout} s`); await shot(page, 'cover'); return; }
    add(VP, 'LOAD', 'PASS', `cover gone in ${((Date.now() - t0) / 1000).toFixed(1)} s; UI = ${s.ui === 'old' ? 'old drag sheet' : s.ui === 'new' ? 'new tap-to-open panel' : s.ui}${nameDone ? '; name screen filled' : ''}`);
    if (await page.evaluate(() => !!document.querySelector('[data-card-title]')).catch(() => false)) CV.attr = true;
    if (A.qaIgnored) { await qaIgnoredCheck(page, A, VP, shot); return; }   // light mode: just this check (+ console / network rows)
    // 2) E2 first: the first story call rings at the Mine right after the cover
    log(VP, 'Eve check'); await eveCheck(page, VP, shot);
    // 3) stations
    const ST = s.stations || [], N = ST.length, W = vp.w, H = vp.h;
    if (!N) { add(VP, 'NAV', 'n/a', 'no __ps3d.STATIONS hook'); return; }
    const yS = Math.round(H * 0.42);
    const swipe = async (dir) => { // dir +1 = next station (finger moves left)
      const x0 = dir > 0 ? W * 0.8 : W * 0.2, hit = await hitId(page, x0, yS);
      if (/@ec/.test(hit)) { const c = await page.locator('#ecClose').boundingBox().catch(() => null); if (c) await page.touchscreen.tap(c.x + c.width / 2, c.y + c.height / 2); await sleep(400); }
      await touchSwipe(cdp, x0, yS, -dir * W * 0.6); };
    // swipe order: the build's x order (__ps3d.ORD, Life Support move) when it has one, else index order. Walk back to the first station in it.
    const ORDV = s.ord && s.ord.length === N ? s.ord : ST.map((_, k) => k), RK = []; ORDV.forEach((st, r) => { RK[st] = r; });
    if (s.ord) add(VP, 'NAV order', 'info', 'x order from __ps3d.ORD: ' + ORDV.map(k => ST[k]).join(' > '));
    for (let k = 0; k < N && (await page.evaluate(PAGE_STATE)).site !== ORDV[0]; k++) { const cur = (await page.evaluate(PAGE_STATE)).site; await swipe(-1); await settle(page, ORDV[Math.max(0, RK[cur] - 1)], VP); }
    for (let r = 0; r < N; r++) {
      const i = ORDV[r], nx = ORDV[Math.min(N - 1, r + 1)];
      s = await settle(page, i, VP);
      const navOk = s.site === i && s.name.trim().toLowerCase() === String(ST[i]).toLowerCase();
      add(VP, `NAV ${i} ${ST[i]}`, navOk ? 'PASS' : 'FAIL', navOk ? `swipe landed; label "${s.name}"` : `site=${s.site} label="${s.name}"`);
      if (!navOk) { await shot(page, 'nav' + i); if (s.site !== i) { await page.evaluate((k) => window.__ps3d.goSite(k), i); await settle(page, i, VP); add(VP, `NAV ${i} recover`, 'WARN', 'used __ps3d.goSite to continue'); } }
      let opened = null;   // what is open going into the swipe test
      if (s.ui === 'old') {
        const taps = await setOldSheet(page, true); await sleep(250);
        const o = await page.evaluate(OLD_SHEET), ex = oldExpect(ST, i, o.drill);
        if (taps > 1) add(VP, `E1 ${ST[i]} sheet tap`, 'WARN', `took ${taps} taps on the Upgrade handle to open (first tap dropped or toggled late)`);
        if (!o.open) { add(VP, `E1 ${ST[i]} sheet`, 'FAIL', '3 taps on the Upgrade handle did not open the sheet'); await shot(page, 'sheet' + i); }
        else if (!sameRows(o.rows, ex.rows)) { add(VP, `E1 ${ST[i]} sheet`, 'FAIL', `rows [${o.rows}] / "${o.sum}" don't match ${ST[i]} (expected [${ex.rows}])`); await shot(page, 'sheet' + i); }
        else if (!ex.own) add(VP, `E1 ${ST[i]} sheet`, 'WARN', `old global sheet: shows Mine rows [${o.rows}] ("${o.sum}") here; ${ST[i]} has no upgrade object of its own in this build`);
        else add(VP, `E1 ${ST[i]} sheet`, 'PASS', `rows [${o.rows}] "${o.sum}"`);
        if (o.open) opened = 'old';
      } else if (s.ui === 'new') {
        // each target's home station from the build's own UPT list (site -1 = roams between stations, e.g. the truck)
        const all = await page.evaluate(() => { const P = window.__ps3d, home = {}; for (const t of P.UPT || []) home[t.id] = typeof t.site === 'number' ? t.site : -1;
          return P.upRects().map(t => Object.assign(t, { site: t.id in home ? home[t.id] : -1 })); });
        const other = all.filter(t => t.r && t.site >= 0 && t.site !== i);
        if (other.length) add(VP, `TAP ${ST[i]}: skipped`, 'info', `other station's target(s) on screen, not tapped: ${other.map(t => `${t.id} (${ST[t.site]})`).join(', ')}`);
        const R = all.filter(t => t.r && !(t.site >= 0 && t.site !== i));
        if (!R.length) add(VP, `TAP ${ST[i]}`, 'n/a', 'no upgradeable object of this station on screen here (upRects)');
        const card = {}, retried = {};   // card: target id -> CARD_TITLE result after its real tap (null = no card); retried: id -> note when it took the settle retry
        // moving targets (trucks) drift, so find the point and tap right away; retry up to 3 times
        // tap point: elementFromPoint must hit the 3D canvas (the browser skips pointer-events:none layers such as #hud, exactly like a
        // real tap) and the game's own pickUp must pick this target. Points below #hud's real bottom edge are tried first (not hidden
        // behind the HUD's look), then points under the HUD. hud = the 'under' count, reported as info.
        const findPt = (tid) => page.evaluate(([id, W, H]) => { const P = window.__ps3d, t = P.upRects().find(x => x.id === id); if (!t || !t.r) return null; const r = t.r;
            const hud = document.getElementById('hud'), hb = hud && getComputedStyle(hud).display !== 'none' && +getComputedStyle(hud).opacity > 0.05 ? hud.getBoundingClientRect().bottom : 0;
            const l = Math.max(r.l, 8), rr = Math.min(r.r, W - 8), tp = Math.max(r.t, 8), b = Math.min(r.b, H - 8); if (rr <= l || b <= tp) return { x: null, why: 'rect off the screen edges' };
            const pts = []; for (const fy of [.5, .35, .65, .2, .8]) for (const fx of [.5, .3, .7, .15, .85]) pts.push({ x: l + (rr - l) * fx, y: tp + (b - tp) * fy });
            pts.sort((a, c) => (a.y < hb) - (c.y < hb));   // stable: clear-of-HUD points first, grid order kept
            const seen = {};
            for (const q of pts) { const e = document.elementFromPoint(q.x, q.y), h = P.pickUp(q.x, q.y);
              if (e && e.tagName === 'CANVAS' && h && h.t.id === id) return { x: q.x, y: q.y, underHud: q.y < hb };
              const k = !e ? 'nothing' : e.tagName === 'CANVAS' ? 'canvas, pickUp=' + (h ? h.t.id : 'none') : '#' + (e.id || (e.closest('[id]') || {}).id || e.tagName.toLowerCase()); seen[k] = (seen[k] || 0) + 1; }
            return { x: null, why: Object.entries(seen).map(([k, n]) => `${k}×${n}`).join(', '), hb: Math.round(hb) }; }, [tid, W, H]);
        const tryTap = async (t) => {   // one tap attempt on target t (up to 3 taps while it moves); returns what happened
          const MOVER = t.id === 'truck' || t.id === 'ship';   // targets that drive around (EM 17:08 b)
          let held = null; if (MOVER) held = await holdStill(page, t.id);
          let pt = null, taps = 0, up = false, still = true, why = '', under = false;
          for (let k0 = 0; k0 < 3 && !up; k0++) { pt = await findPt(t.id); if (!pt || pt.x === null) { why = pt ? pt.why + (pt.hb ? `; #hud bottom ${pt.hb}px` : '') : 'target gone'; break; }
            under = pt.underHud; await page.touchscreen.tap(pt.x, pt.y); taps++;
            for (let k = 0; k < 8 && !up; k++) { await sleep(250); up = !!(await page.evaluate(NEW_PANEL)).cur; }   // poll 2 s before re-tapping so a slow open isn't closed by a second tap on the scrim
            if (!up) still = await page.evaluate(([x, y, id]) => { const h = window.__ps3d.pickUp(x, y); return !!(h && h.t.id === id); }, [pt.x, pt.y, t.id]); }
          return { MOVER, held, pt, taps, up, still, why, under }; };
        // EM 18:31: under load the camera may not have settled when a tap goes in (QA saw NO CARD rows). No card after the first attempt:
        // wait for the camera to come to rest (10 s), let the card camera ease back (uc.w 0), close any stray card, then try once more.
        const settleRetry = async () => { const s2 = await settle(page, i, VP, 10000), uw = await waitUc(page); await closeCard(page);
          return `${s2.timedOut ? 'camera still not at rest after 10 s' : 'camera at rest'}${uw.ok ? '' : `, card camera uc.w ${uw.w}`}, box load ${load1() ?? 'n/a'}`; };
        const cardRetry = async (fn, label) => { let c = await fn(); if (!c || c.open) return c;   // pad tank / empty station: same settle + one retry
          const first = c.why || 'no card', note = await settleRetry(); c = await fn(); if (!c) return c;
          if (c.open) { c.retry = note; add(VP, `${label.replace(/^CARD/, 'TAP')} retry`, 'WARN', `no card on the first try (${first}); opened after waiting for the camera (${note}) and tapping once more`); }
          else c.why = `${c.why || 'no card'}; first try: ${first}; retried after the settle wait (${note})`; return c; };
        for (const t of R) {
          card[t.id] = null; await settle(page, i, VP);   // camera at rest before every tap
          let a = await tryTap(t);
          if (!a.up) { const first = a.taps ? `${a.taps} tap(s), no card` : a.why || 'no tap point'; const note = await settleRetry(); a = await tryTap(t);
            if (a.up) { retried[t.id] = note; add(VP, `TAP ${ST[i]}: ${t.id} retry`, 'WARN', `no card on the first try (${first}); opened after waiting for the camera (${note}) and tapping once more`); } }
          const { MOVER, held, pt, taps, up, still, why, under } = a;
          const mover = MOVER && (Number(A.ts) > 1 || (held && !held.ok));   // at ts > 1 the truck and ship move N× faster, so a missed tap on them is expected: info, not WARN
          if (!taps) { add(VP, `TAP ${ST[i]}: ${t.id}`, mover && why === 'target gone' ? 'info' : 'WARN', `on screen but no clear tap point (what the 25 grid points hit: ${why})`); continue; }
          if (!up && !still) { add(VP, `TAP ${ST[i]}: ${t.id}`, mover ? 'info' : 'WARN', `moving target: ${taps} tap(s) missed because it had moved off the tap point; could not confirm${mover ? ` (${t.id} at ts=${A.ts})` : ''}`); continue; }
          if (up && taps > 1) add(VP, `TAP ${ST[i]}: ${t.id}`, mover ? 'info' : 'WARN', `needed ${taps} taps (target moving or first tap missed)${mover ? ` (${t.id} at ts=${A.ts})` : ''}`);
          if (up && under) add(VP, `TAP ${ST[i]}: ${t.id} under HUD`, 'info', 'only tap point was under #hud (pointer-events:none, so the tap still reached the canvas)');
          await sleep(200);
          const p = await page.evaluate(NEW_PANEL), want = await page.evaluate((k) => (window.__ps3d.UP[k] || {}).name, t.p);
          if (up) { card[t.id] = await page.evaluate(CARD_TITLE); if (retried[t.id]) card[t.id].retry = retried[t.id]; }
          const ok = p.shown && p.cur === t.p && p.name === want && p.kick.toLowerCase().startsWith(String(ST[i]).toLowerCase());
          if (!ok && MOVER && p.shown && p.cur && p.cur !== t.p) {   // the mover drove off and the finger landed on another object: that card opening is correct behaviour
            add(VP, `E1 ${ST[i]}: ${t.id}`, 'info', `moving target: the card under the finger opened instead (${p.cur}, "${p.name}")${held ? `; ${held.ok ? `held still ${held.ms} ms before the tap` : `never held still in ${held.ms} ms`}` : ''}`);
            await closeCard(page); continue; }
          add(VP, `E1 ${ST[i]}: ${t.id}`, ok ? 'PASS' : 'FAIL', ok ? `title "${p.name}", kicker "${p.kick}"${retried[t.id] ? ' (after the settle retry)' : ''}` : `opened=${p.cur} (last close reason: ${await page.evaluate(() => window.__ps3d.upClosed)}; lastPick ${await page.evaluate(() => window.__ps3d.lastPick)}) title="${p.name}" kicker="${p.kick}", expected "${want}" at ${ST[i]}`);
          if (!ok) await shot(page, `panel${i}-${t.id}`);
          const x = await page.locator('#upX').boundingBox().catch(() => null); if (x && p.shown) { await page.touchscreen.tap(x.x + x.width / 2, x.y + x.height / 2); await sleep(300); }
          if ((await page.evaluate(NEW_PANEL)).cur) add(VP, `E1 ${ST[i]}: ${t.id} close`, 'FAIL', 'X did not close the card');
        }
        // CARD title check (EM 10/31): each listed object at this station, plus 'Coming soon' at a station with no target of its own
        const home = await page.evaluate(() => (window.__ps3d.UPT || []).map(t => t.site));
        for (const id of Object.keys(CARD_WANT)) { const ut = all.find(t => t.id === id); if (!ut || ut.site !== i) continue;
          if (!R.some(t => t.id === id)) {   // EM 18:31: off screen at the first look (camera not settled?): wait for rest, look again, tap once
            const note = await settleRetry(), t2 = await page.evaluate((id) => (window.__ps3d.upRects() || []).find(x => x.id === id), id);
            if (t2 && t2.r) { const a = await tryTap(t2); if (a.up) { await sleep(200); card[id] = await page.evaluate(CARD_TITLE); card[id].retry = note;
                add(VP, `TAP ${ST[i]}: ${id} retry`, 'WARN', `not on screen at the first look (${ut.why || 'no rect'}); on screen and opened after waiting for the camera (${note})`); await closeCard(page); }
              else card[id] = { open: false, why: `not on screen at the first look; on screen after the settle retry (${note}) but ${a.taps ? a.taps + ' tap(s) opened no card' : a.why || 'no tap point'}` }; }
            else card[id] = { open: false, why: `not on screen (${ut.why || 'no rect'}), not tapped; still off screen after the settle retry (${note})` }; }
          cardRow(VP, `CARD ${ST[i]}: ${id}`, card[id], CARD_WANT[id]);
          if (id === 'padFuel') { await settle(page, i, VP); const c = await cardRetry(() => padTankCard(page, W, H), `CARD ${ST[i]}: pad tank`); if (c) cardRow(VP, `CARD ${ST[i]}: pad tank`, c, 'Fuel'); else add(VP, `CARD ${ST[i]}: pad tank`, 'info', 'no pad tank meshes (no padFuel tank box and no /tank/i mesh in the pad model)'); } }
        if (!home.includes(i)) { await settle(page, i, VP); await closeCard(page); cardRow(VP, `CARD ${ST[i]}: empty station`, await cardRetry(() => emptyStationCard(page, i, W, H), `CARD ${ST[i]}: empty station`), CARD_EMPTY); }
        if (R.length && r < N - 1) { const pt = R[0]; await page.evaluate((id) => window.__ps3d.openUp(id), pt.p); await sleep(300); opened = (await page.evaluate(NEW_PANEL)).cur ? 'new' : null; }   // hook only sets up the swipe test
      } else add(VP, `E1 ${ST[i]}`, 'n/a', s.ui === 'new-nohook' ? 'new panel present but no __ps3d.upRects hook to find targets' : 'no upgrade sheet or panel in this build');
      if (r === N - 1) { if (opened === 'old') await setOldSheet(page, false); break; }
      // E1 part 2: swipe with the panel open → it must close or update to the new station
      if (opened === 'old') {   // swipe on the 3D view above the open sheet
        const top = (await page.locator('#sheetWrap').boundingBox() || { y: H }).y; const y = Math.min(yS, top - 40);
        await touchSwipe(cdp, W * 0.8, y, -W * 0.6); s = await settle(page, nx, VP);
        let o = await page.evaluate(OLD_SHEET), ex = oldExpect(ST, s.site, o.drill), ok = s.site === nx && (!o.open || sameRows(o.rows, ex.rows)), late = '';
        if (!ok && s.timedOut) { s = await settle(page, nx, VP, 10000); o = await page.evaluate(OLD_SHEET); ex = oldExpect(ST, s.site, o.drill); ok = s.site === nx && (!o.open || sameRows(o.rows, ex.rows)); late = `; checked again after a 10 s settle wait (${s.timedOut ? 'still not at rest' : 'at rest'}, box load ${load1() ?? 'n/a'})`;   // EM 18:31
          if (ok) add(VP, `E1 swipe ${i}→${nx} sheet open settle`, 'WARN', 'camera not at rest within 4 s after the swipe; the row passed on the 10 s settle wait'); }
        add(VP, `E1 swipe ${i}→${nx} sheet open`, ok ? 'PASS' : 'FAIL', `site=${s.site}; sheet ${o.open ? `still open, rows [${o.rows}]` : 'closed'}${late}`);
        if (!ok) await shot(page, 'swipeopen' + i);
        if (o.open && (await setOldSheet(page, false)) < 0) add(VP, `E1 ${ST[nx]} sheet close`, 'FAIL', '3 taps on the Upgrade handle did not close the sheet');
      } else if (opened === 'new') {   // swipe on the scrim, outside the card
        const pb = await page.locator('#upPanel').boundingBox().catch(() => null); const yN = pb ? (pb.y + pb.height + 40 < H - 120 ? Math.round(pb.y + pb.height + 40) : Math.round(Math.max(60, pb.y - 40))) : yS;
        await touchSwipe(cdp, W * 0.8, yN, -W * 0.6);
        // gc-ui3 item 6 (EM 18:06): a swipe on the dim area only closes the card; the station stays put. Builds with the __ps3d.scrimSwipe hook expect that;
        // older builds (no hook) still expect the swipe to move one station.
        const stay = await page.evaluate(() => !!window.__ps3d.scrimSwipe), want = stay ? i : nx; s = await settle(page, want, VP);
        let p = await page.evaluate(NEW_PANEL), ok = !p.cur && s.site === want, late = '';
        if (!ok && s.timedOut) { s = await settle(page, want, VP, 10000); p = await page.evaluate(NEW_PANEL); ok = !p.cur && s.site === want; late = `; checked again after a 10 s settle wait (${s.timedOut ? 'still not at rest' : 'at rest'}, box load ${load1() ?? 'n/a'})`;   // EM 18:31
          if (ok) add(VP, `E1 swipe ${i}→${nx} card open settle`, 'WARN', 'camera not at rest within 4 s after the swipe; the row passed on the 10 s settle wait'); }
        add(VP, `E1 swipe ${i}→${nx} card open`, ok ? 'PASS' : 'FAIL', `${stay ? 'dim-area swipe should close the card and stay' : 'swipe should close the card and move'}: site=${s.site} (want ${want}); card ${p.cur ? `still open (${p.cur}, "${p.kick}")` : 'closed (' + (await page.evaluate(() => window.__ps3d.upClosed)) + ')'}${late}`);
        if (!ok) { await shot(page, 'swipeopen' + i); if (p.cur) await page.evaluate(() => window.__ps3d.closeUp('qa')); }
        if (s.site !== nx) await swipe(1);   // move on to the next station for the walk
      } else await swipe(1);
    }
    if (!A.qaIgnored && (A.ts != null || A.skip)) await qaCheck(page, A, VP, shot);
    if (s.ui === 'old') add(VP, 'TAP objects', 'n/a', 'old sheet build: 3D objects are not tappable (scene taps only hit ore deposits, which are off); the sheet is opened from its Upgrade handle');
    await sleep(300);
  } catch (e) { add(VP, 'SCRIPT', 'FAIL', 'exception: ' + (e && e.message)); }
  finally {
    for (const r of CV.nocard) { r.res = CV.attr ? 'FAIL' : 'info'; r.detail = `NO CARD: ${r.detail} (${CV.attr ? 'build has [data-card-title], so this is a FAIL' : 'no [data-card-title] in this build: info'})`.slice(0, 300); }
    add(VP, 'CONSOLE errors', consoleErr.length ? 'FAIL' : 'PASS', consoleErr.length ? `${consoleErr.length}: ` + [...new Set(consoleErr)].slice(0, 4).join(' | ') : 'none');
    add(VP, 'NETWORK failures', netFail.length ? 'FAIL' : 'PASS', netFail.length ? `${netFail.length}: ` + [...new Set(netFail)].slice(0, 4).join(' | ') : 'none');
    rowsFull.push({ vp: VP, consoleErr, netFail });
    closing = true;
    try { for (const p of ctx.pages()) await p.close({ runBeforeUnload: true }); await sleep(600); } catch (e) {}   // pagehide → dev Worker lock release
    await ctx.close().catch(() => {});
    add(VP, 'RUNTIME', 'info', `${((Date.now() - t0) / 1000).toFixed(1)} s`);
  }
}
const rowsFull = [];
// ---------- QA fast-forward (--ts / --skip; dev/ build with ?qa=1 only) ----------
async function qaIgnoredCheck(page, A, VP, shot) {   // the page was loaded WITH ?qa=1&ts=N: a build that must ignore it has to run at 1x
  const r0 = await page.evaluate(() => { const P = window.__ps3d || {}; return { psqa: typeof window.PS_QA, badge: !!document.getElementById('qaBadge') || /QA x\d/.test(document.body.innerText),
    spd: P.SPD === undefined ? null : P.SPD, g: typeof P.nowMs === 'function' ? P.nowMs() : null, w: Date.now() }; });
  await sleep(3000);
  const r1 = await page.evaluate(() => { const P = window.__ps3d || {}; return { g: typeof P.nowMs === 'function' ? P.nowMs() : null, w: Date.now() }; });
  const rate = r0.g === null ? null : (r1.g - r0.g) / Math.max(1, r1.w - r0.w);   // game ms per wall ms over 3 s (null if the build has no nowMs hook)
  const ok = r0.psqa === 'undefined' && !r0.badge && (r0.spd === null || r0.spd === 1) && (rate === null || Math.abs(rate - 1) < 0.05);
  add(VP, `QA flags ignored (ts=${A.ts})`, ok ? 'PASS' : 'FAIL', `window.PS_QA ${r0.psqa}; QA badge ${r0.badge ? 'PRESENT' : 'none'}; __ps3d.SPD ${r0.spd === null ? 'n/a' : r0.spd}; game clock ${rate === null ? 'n/a (no nowMs hook)' : rate.toFixed(3) + '× wall clock over 3 s'}`);
  if (!ok) await shot(page, 'qaignored');
}
async function qaCheck(page, A, VP, shot) {
  const q = await page.evaluate(() => { const Q = window.PS_QA, b = document.getElementById('qaBadge'); return { has: !!Q, scale: Q ? Q.scale : null, skip: !!(Q && typeof Q.skipToTouchdown === 'function'), badge: b ? b.textContent : null }; });
  if (A.ts != null) {
    const want = Math.min(60, Math.max(1, Number(A.ts)));
    if (!q.has) add(VP, `QA ts=${A.ts}`, 'n/a', 'no window.PS_QA in this build/path (fast-forward is dev/ only)');
    else { const ok = Math.abs(q.scale - want) < 1e-9 && (want === 1 ? !q.badge : q.badge === 'QA x' + +want.toFixed(2));
      add(VP, `QA ts=${A.ts}`, ok ? 'PASS' : 'FAIL', `PS_QA.scale ${q.scale} (want ${want}); badge ${q.badge ? '"' + q.badge + '"' : 'none'}`); if (!ok) await shot(page, 'qats'); }
  }
  if (A.skip) {
    if (!q.skip) { add(VP, 'QA skipToTouchdown', 'n/a', 'window.PS_QA.skipToTouchdown not present (only the dev/ build with ?qa=1 has it)'); return; }
    const r = await page.evaluate(() => { try { return window.PS_QA.skipToTouchdown(); } catch (e) { return { ok: false, reason: 'threw: ' + e.message }; } });
    if (r && r.ok) add(VP, 'QA skipToTouchdown', 'PASS', `${r.from} → ${r.st}; paid $${r.paid}; skipped ${r.skippedSec} s of game time`);
    else if (r && r.reason === 'no_trip') add(VP, 'QA skipToTouchdown', 'n/a', 'ship on the pad, no trip in flight to skip (launch one first)');
    else { add(VP, 'QA skipToTouchdown', 'FAIL', JSON.stringify(r)); await shot(page, 'qaskip'); }
  }
}

// URL for a listed file the page didn't load. Keys are repo paths (dev/main.js) and the target is a directory inside the repo
// (.../planet-stack/dev/), so drop the key's leading folders that the target already ends with: .../dev/ + dev/index.html -> .../dev/index.html.
// (Before 10/31 it resolved the key against .../dev/ directly, giving .../dev/dev/index.html = 404.)
function hashUrl(target, key) {
  const base = new URL(target); base.search = ''; base.hash = ''; base.pathname = base.pathname.replace(/[^/]*$/, '');
  const bs = base.pathname.split('/').filter(Boolean), ks = key.split('/').filter(Boolean).slice(0, -1);
  let n = 0; for (let k = Math.min(bs.length, ks.length); k > 0; k--) if (bs.slice(bs.length - k).join('/') === ks.slice(0, k).join('/')) { n = k; break; }
  base.pathname = '/' + bs.slice(0, bs.length - n).join('/') + (bs.length - n ? '/' : '');
  return new URL(key, base).toString();
}
async function md5Check(A, served) {
  const listed = A.expect ? JSON.parse(fs.readFileSync(A.expect, 'utf8')) : null;
  const seen = {}; for (const [p, set] of Object.entries(served)) seen[p] = [...set];
  for (const [p, hs] of Object.entries(seen)) if (hs.length > 1) add('all', 'MD5 ' + p, 'FAIL', 'served with different contents in one run: ' + hs.join(', '));
  if (!listed) {
    add('all', 'MD5 vs expected list', 'n/a', `no --expect given; ${Object.keys(seen).length} served files hashed (listed below, saved to out/md5-seen.json)`);
    return seen;
  }
  const map = listed.files && typeof listed.files === 'object' ? listed.files : listed;
  let ok = 0, bad = 0, err = 0;
  const norm = (p) => p.endsWith('/') ? p + 'index.html' : p;   // the page itself is served as .../dev/ (a directory URL): that IS dev/index.html
  for (const [k, want] of Object.entries(map)) {
    const key = k.replace(/^\.?\//, '').split('?')[0], hits = Object.keys(seen).filter(p => [p, norm(p)].some(q => q === k || q === '/' + key || q.endsWith('/' + key)));
    let got = hits.flatMap(p => seen[p]);
    if (!got.length) { const u = hashUrl(A.url, key); try { const r = await fetch(u, { cache: 'no-store' });
      got = r.ok ? [md5(Buffer.from(await r.arrayBuffer()))] : []; if (!r.ok) { add('all', 'MD5 ' + k, 'ERROR', `script error: hash fetch failed (${r.status}) for ${u}; not a build FAIL`); err++; continue; } } catch (e) { add('all', 'MD5 ' + k, 'ERROR', `script error: hash fetch failed (${e.message}) for ${u}; not a build FAIL`); err++; continue; } }
    const w = String(want).toLowerCase(), m = got.every(h => h === w || (w.length < 32 && h.startsWith(w)));
    if (m) ok++; else { bad++; add('all', 'MD5 ' + k, 'FAIL', `expected ${want}, served ${[...new Set(got)].join(', ')}`); }
  }
  add('all', 'MD5 vs expected list', bad ? 'FAIL' : err ? 'ERROR' : 'PASS', `${ok}/${ok + bad + err} match` + (err ? `, ${err} could not be fetched (script error)` : '') + (bad ? '' : ` (${Object.keys(seen).length} files served in total)`));
  return seen;
}

function printTable() {
  const head = ['VIEWPORT', 'CHECK', 'RESULT', 'DETAIL'], w = [8, 40, 7];
  const pad = (s, n) => (s.length > n ? s.slice(0, n - 1) + '…' : s.padEnd(n));
  console.log('\n' + head.map((h, i) => i < 3 ? pad(h, w[i]) : h).join(' | '));
  console.log('-'.repeat(120));
  for (const r of rows) console.log([pad(r.vp, w[0]), pad(r.check, w[1]), pad(r.res, w[2]), r.detail].join(' | '));
  const c = (x) => rows.filter(r => r.res === x).length;
  console.log('-'.repeat(120)); console.log(`PASS ${c('PASS')} · FAIL ${c('FAIL')} · WARN ${c('WARN')}  · n/a ${c('n/a')}` + (c('ERROR') ? ` · script ERROR ${c('ERROR')}` : ''));
}

(async () => {
  let A; try { A = parseArgs(process.argv.slice(2)); } catch (e) { console.error(e.message); process.exit(2); }
  const T0 = Date.now(), served = {}, devId = crypto.randomUUID();
  console.log(`Planet Stack autocheck · ${A.url} · viewports ${A.viewports} · ${new Date().toLocaleString('en-US', { timeZone: 'America/Los_Angeles' })} PT`);
  let browser = null, crashed = false;
  // load gate: the browser starts only when the box's 1-minute load is under --max-load (default 10; 0 = off). Waits up to --load-wait minutes
  // (default 20), printing what it waits for; at the ceiling it aborts the browser step (exit 3) instead of starting anyway.
  if (A.maxLoad > 0 && load1() !== null) { const tEnd = Date.now() + A.loadWait * 60000; let l = load1();
    while (l >= A.maxLoad) { if (Date.now() >= tEnd) { console.log(`LOAD GATE: 1-min load still ${l} (limit ${A.maxLoad}) after ${A.loadWait} min; browser step aborted, nothing was tested.`); process.exit(3); }
      console.log(`LOAD GATE: waiting for the 1-min load to drop under ${A.maxLoad} before starting the browser (now ${l}; ${Math.ceil((tEnd - Date.now()) / 1000)} s left of ${A.loadWait} min)`);
      await sleep(20000); l = load1(); }
    console.log(`LOAD GATE: 1-min load ${l} < ${A.maxLoad}, starting the browser`); }
  try {
    browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH || undefined,
      args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required', '--mute-audio'] });
    for (const vp of A.vps) await runViewport(browser, A, vp, served, devId);
  } catch (e) { crashed = true; add('all', 'SCRIPT', 'FAIL', e.message); }
  finally { if (browser) await browser.close().catch(() => {}); }
  const seen = await md5Check(A, served).catch(e => { add('all', 'MD5', 'FAIL', e.message); return {}; });
  add('all', 'TOTAL RUNTIME', 'info', `${((Date.now() - T0) / 1000).toFixed(1)} s`);
  printTable();
  if (!A.expect) { console.log('\nServed md5s (path → md5), for QA\'s --expect list:'); for (const p of Object.keys(seen).sort()) console.log(`  ${p}  ${seen[p].join(',')}`); }
  for (const r of rowsFull) { if (r.consoleErr.length || r.netFail.length) { console.log(`\n${r.vp} full error list:`); for (const x of [...new Set(r.consoleErr)]) console.log('  console: ' + x); for (const x of [...new Set(r.netFail)]) console.log('  network: ' + x); } }
  try { fs.mkdirSync(A.out, { recursive: true }); fs.writeFileSync(path.join(A.out, 'report.json'), JSON.stringify({ url: A.url, at: new Date().toISOString(), rows, errors: rowsFull }, null, 1));
    if (!A.expect) fs.writeFileSync(path.join(A.out, 'md5-seen.json'), JSON.stringify(Object.fromEntries(Object.entries(seen).map(([p, h]) => [p, h[0]])), null, 1)); } catch (e) {}
  if (!A.keepShots) { for (const f of shots) try { fs.unlinkSync(f); } catch (e) {} if (shots.length) console.log(`(${shots.length} failure screenshot(s) deleted after the report; use --keep-shots to keep them)`); }
  else if (shots.length) console.log('Failure screenshots:\n  ' + shots.join('\n  '));
  console.log(`Report: ${path.join(A.out, 'report.json')}`);
  process.exit(rows.some(r => r.res === 'FAIL') ? 1 : crashed || rows.some(r => r.res === 'ERROR') ? 2 : 0);
})();
