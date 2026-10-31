// Planet Stack DEV: Settings ▸ Report a bug (Code Assistant 10/31). Classic script, loaded once from dev/index.html; safe to run before or after main.js.
// Uses the game's PS_DEV contract (dev/main.js): WORKER_URL, code, build, v, mock, canvas, renderNow, toast, and (Coder 10/31, read at send time)
// playerName ('' when unset) and the deviceInfo getter {type, os, browser, browserVersion, screen, viewport, dpr, orientation, touch, userAgent}.
// Builds without those two fall back to '' and a local copy of the same device object. POST ${WORKER_URL}/bug as text/plain JSON (no CORS preflight):
// {reportId, code, deviceId, playerName, text, build, v, device, shot}. deviceId is the game's own (localStorage planetstack-dev-device), so the
// Worker's lock check sees the same device that holds the code. ?mock=… builds never touch the network (mock=down answers 'unreachable').
(function () {
  'use strict';
  const PS = window.PS_DEV = window.PS_DEV || {};
  const MAX_SHOT = 300 * 1024, TEXT_MAX = 4000;
  const lsGet = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };
  const deviceId = () => { const k = 'planetstack-dev-device'; let id = lsGet(k);
    if (!id) { id = crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2); try { localStorage.setItem(k, id); } catch (e) {} }
    return id; };
  // fallback for builds without PS_DEV.deviceInfo (same shape as the game's getter)
  function localDevice() {
    const ua = navigator.userAgent || '', tp = navigator.maxTouchPoints || 0, m = (re) => { const x = re.exec(ua); return x ? x[1] : ''; };
    const ipad = /iPad/.test(ua) || (/Macintosh/.test(ua) && tp > 1), iphone = /iPhone|iPod/.test(ua), android = /Android/.test(ua);
    const iosV = m(/OS (\d+(?:_\d+)*) like Mac/).replace(/_/g, '.') || (ipad ? m(/Version\/(\d+(?:\.\d+)*)/) : '');
    const type = ipad ? 'iPad' : iphone ? 'iPhone' : android ? (/Mobile/.test(ua) ? 'Android phone' : 'Android tablet') : /Mobi/.test(ua) ? 'mobile' : 'desktop';
    const os = ipad ? ('iPadOS ' + iosV).trim() : iphone ? ('iOS ' + iosV).trim() : android ? ('Android ' + m(/Android (\d+(?:\.\d+)*)/)).trim()
      : /Windows NT/.test(ua) ? 'Windows' : /CrOS/.test(ua) ? 'ChromeOS' : /Mac OS X/.test(ua) ? ('macOS ' + m(/Mac OS X (\d+(?:[._]\d+)*)/).replace(/_/g, '.')).trim() : /Linux/.test(ua) ? 'Linux' : 'unknown';
    const B = [['Edge', /(?:Edg|EdgiOS|EdgA)\/([\d.]+)/], ['Opera', /(?:OPR|OPiOS)\/([\d.]+)/], ['Samsung Internet', /SamsungBrowser\/([\d.]+)/], ['Firefox', /(?:FxiOS|Firefox)\/([\d.]+)/],
      ['Chrome', /(?:CriOS|Chrome|HeadlessChrome)\/([\d.]+)/], ['Safari', /Version\/([\d.]+).*Safari/]];
    let browser = 'unknown', browserVersion = ''; for (const [n, re] of B) { const v = m(re); if (v) { browser = n; browserVersion = v; break; } }
    if (browser === 'Chrome' && /HeadlessChrome/.test(ua)) browser = 'Chrome (headless)';
    const so = screen.orientation && screen.orientation.type, orientation = so ? so.split('-')[0] : (innerWidth > innerHeight ? 'landscape' : 'portrait');
    return { type, os, browser, browserVersion, screen: `${screen.width}x${screen.height}`, viewport: `${innerWidth}x${innerHeight}`, dpr: window.devicePixelRatio || 1,
      orientation, touch: tp > 0 || 'ontouchstart' in window, userAgent: ua };
  }
  // read fresh at every call (never cached at load)
  function deviceInfo() { let d = null; try { d = PS.deviceInfo; } catch (e) {} return d && typeof d === 'object' ? Object.assign({}, d) : localDevice(); }
  function playerName() { let n = ''; try { n = PS.playerName; } catch (e) {} return typeof n === 'string' ? n : ''; }
  const workerUrl = () => String(PS.WORKER_URL || '').replace(/\/+$/, '');
  const newId = () => 'r' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);

  // screenshot: render a frame and read it in the same task (no preserveDrawingBuffer); step quality, then scale, down until <= 300 KB
  function captureShot() {
    const cv = PS.canvas || document.querySelector('canvas'); if (!cv || !cv.width) return null;
    const render = () => { try { if (typeof PS.renderNow === 'function') PS.renderNow(); } catch (e) {} };
    try { for (const sc of [1, .75, .5, .35, .25]) {
      render(); let src = cv;
      if (sc < 1) { src = document.createElement('canvas'); src.width = Math.max(1, Math.round(cv.width * sc)); src.height = Math.max(1, Math.round(cv.height * sc)); src.getContext('2d').drawImage(cv, 0, 0, src.width, src.height); }
      for (const q of [.8, .65, .5, .4]) { if (sc === 1 && q !== .8) render();
        const url = src.toDataURL('image/jpeg', q), bytes = Math.floor((url.length - url.indexOf(',') - 1) * 3 / 4);
        if (url.startsWith('data:image/jpeg') && bytes <= MAX_SHOT) return { url, bytes, w: src.width, h: src.height, q, scale: sc }; } } } catch (e) {}
    return null;
  }

  const CSS = `#bugOv{position:fixed;inset:0;z-index:60;display:none;background:#04070dd9;overflow-y:auto;-webkit-overflow-scrolling:touch;touch-action:pan-y;
  padding:calc(env(safe-area-inset-top,0px) + 12px) calc(env(safe-area-inset-right,0px) + 12px) calc(env(safe-area-inset-bottom,0px) + 12px) calc(env(safe-area-inset-left,0px) + 12px);box-sizing:border-box}
#bugOv.on{display:block}
#bugF{max-width:480px;margin:0 auto;display:flex;flex-direction:column;gap:10px;padding:14px;background:linear-gradient(180deg,#0f1a2ef5,#090f1df5);box-shadow:inset 0 0 0 1px #3ad0ff66;color:#eafcff;font:600 13px/1.35 system-ui}
#bugF .k{font:700 10px/1 system-ui;letter-spacing:.24em;color:#3ad0ff;display:flex;justify-content:space-between;align-items:center}
#bugF label{display:flex;flex-direction:column;gap:6px}
#bugF textarea{font-size:16px;width:100%;box-sizing:border-box;background:#060b15;color:#eafcff;border:1px solid #3ad0ff66;border-radius:0;padding:8px;font-family:system-ui;min-height:110px;resize:vertical;-webkit-user-select:text;user-select:text;touch-action:auto}
#bugF img{width:100%;max-height:28vh;object-fit:contain;background:#000}
#bugF .meta{font:500 11px/1.4 ui-monospace,monospace;color:#c9d3e6;opacity:.8;word-break:break-word;white-space:pre-line}
#bugF .bug-act{display:flex;gap:10px}
#bugF button{flex:1;min-height:44px;border:0;border-radius:0;margin:0;padding:0 12px;font:800 13px/1 system-ui;letter-spacing:.14em;cursor:pointer}
#bugSend{background:#3ad0ff;color:#090f1d}#bugSend:disabled{opacity:.5}
#bugClose,#bugX{background:#c9d3e633;color:#eafcff}#bugF #bugX{flex:0 0 44px;width:44px;height:44px;padding:0}
#bugMsg{min-height:1.4em;font-weight:700}#bugMsg.err{color:#ffb340}#bugMsg.ok{color:#5dffa8}`;

  let ov = null, shot = null, rid = '', sentText = null, busy = false;
  const $b = (id) => ov.querySelector('#' + id);
  function msg(t, k) { const m = $b('bugMsg'); m.textContent = t; m.className = k || ''; }
  function build() {
    const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
    ov = document.createElement('div'); ov.id = 'bugOv'; ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-modal', 'true'); ov.setAttribute('aria-label', 'Report a bug');
    ov.innerHTML = `<form id="bugF" novalidate><div class="k"><span>REPORT A BUG <span class="devtag">DEV</span></span><button type="button" id="bugX" aria-label="Close">✕</button></div>
      <label>What happened?<textarea id="bugTxt" maxlength="${TEXT_MAX}" placeholder="What did you do, what did you expect, and what happened?"></textarea></label>
      <img id="bugImg" alt="Screenshot of the game"><div class="meta" id="bugMeta"></div><div id="bugMsg" role="status" aria-live="polite"></div>
      <div class="bug-act"><button type="button" id="bugClose">CANCEL</button><button type="submit" id="bugSend">SEND</button></div></form>`;
    document.body.appendChild(ov);
    for (const ev of ['pointerdown', 'pointerup', 'pointermove', 'touchstart', 'touchmove', 'touchend', 'wheel', 'keydown', 'keyup', 'click']) ov.addEventListener(ev, (e) => e.stopPropagation(), { passive: true });
    $b('bugX').onclick = $b('bugClose').onclick = close;
    $b('bugF').addEventListener('submit', (e) => { e.preventDefault(); send(); });
    $b('bugTxt').addEventListener('input', () => { if (!busy) $b('bugSend').disabled = false; if (sentText !== null && $b('bugTxt').value.trim() !== sentText) { rid = newId(); sentText = null; } });
  }
  function metaText() {
    const d = deviceInfo(), n = playerName();
    return [`Tester ${PS.code || '—'}${n ? ' · ' + n : ''}`, `Build ${PS.build || 'DEV'}${PS.v ? ' (v=' + PS.v + ')' : ''}`,
      `${[d.type, d.os, [d.browser, d.browserVersion].filter(Boolean).join(' ')].filter(Boolean).join(' · ')}`,
      `${d.viewport} @${d.dpr}x · screen ${d.screen}${d.orientation ? ' · ' + d.orientation : ''}` + (shot ? ` · shot ${Math.round(shot.bytes / 1024)} KB` : ' · no screenshot')].join('\n');
  }
  function openBugReport() {
    if (!ov) build();
    shot = captureShot(); rid = newId(); sentText = null; busy = false;
    $b('bugImg').src = shot ? shot.url : ''; $b('bugImg').style.display = shot ? '' : 'none';
    $b('bugMeta').textContent = metaText(); $b('bugSend').disabled = false;
    msg(PS.mock || workerUrl() ? '' : 'Bug server not set up yet', PS.mock || workerUrl() ? '' : 'err');
    ov.classList.add('on'); setTimeout(() => { try { $b('bugTxt').focus({ preventScroll: true }); } catch (e) {} }, 50);
    return shot;
  }
  function close() { if (!ov) return; ov.classList.remove('on'); shot = null; $b('bugImg').src = ''; }
  const ERR = { bad_code: "Your tester code wasn't accepted. Reload and enter it again.", bad_request: 'That report was not accepted. Add a description and try again.',
    bad_shot: 'The screenshot could not be read. Try again.', in_use: 'This tester code is in use on another device.', too_big: 'Screenshot too large.',
    rate_limited: 'Too many reports from this code. Wait about 10 minutes and try again.', unreachable: "Couldn't reach the bug server. Check your connection and try again." };
  async function post(body) {   // -> { status, json } or { unreachable: true }
    if (PS.mock) { await new Promise(r => setTimeout(r, 80)); if (PS.mock === 'down') return { unreachable: true };
      PS.mockBugs = PS.mockBugs || []; PS.mockBugs.push(body); return { status: 200, json: { ok: true, issue: 900 + PS.mockBugs.length, mock: true } }; }
    const W = workerUrl(); if (!W) return { unreachable: true };
    const ac = typeof AbortController === 'function' ? new AbortController() : null, to = setTimeout(() => ac && ac.abort(), 20000);
    try { const r = await fetch(W + '/bug', { method: 'POST', cache: 'no-store', signal: ac ? ac.signal : undefined, headers: { 'Content-Type': 'text/plain;charset=UTF-8' }, body: JSON.stringify(body) });
      let j = null; try { j = await r.json(); } catch (e) {} return { status: r.status, json: j || {} };
    } catch (e) { return { unreachable: true }; } finally { clearTimeout(to); }
  }
  async function send() {
    if (busy) return;
    if (!PS.mock && !workerUrl()) return msg('Bug server not set up yet', 'err');
    const text = $b('bugTxt').value.trim().slice(0, TEXT_MAX), code = PS.code || '';
    if (!text) return msg('Describe the bug first.', 'err'); if (!code) return msg('Enter your tester code first.', 'err');
    const body = { reportId: rid, code, deviceId: deviceId(), playerName: playerName(), text, build: PS.build || 'DEV', v: PS.v || '', device: deviceInfo(),
      shot: shot ? shot.url.slice(shot.url.indexOf(',') + 1) : '' };
    $b('bugMeta').textContent = metaText(); busy = true; $b('bugSend').disabled = true; msg('Sending…');
    const r = await post(body); busy = false; PS.lastBug = { body: Object.assign({}, body, { shot: body.shot.length }), res: r };
    const j = r.json || {};
    if (!r.unreachable && r.status >= 200 && r.status < 300 && j.ok) { sentText = text; msg('Sent' + (j.issue ? ` (issue #${j.issue})` : '') + '. Thank you!', 'ok');
      if (typeof PS.toast === 'function') try { PS.toast('Bug report sent. Thank you!'); } catch (e) {} return; }   // Send stays off until the text changes
    $b('bugSend').disabled = false;
    const reason = r.unreachable ? 'unreachable' : j.reason;
    msg(ERR[reason] || (r.status === 429 ? ERR.rate_limited : r.status === 409 ? ERR.in_use : `Bug server error (${r.status}). Try again later.`), 'err');
  }
  // main.js assigns a "coming soon" stub to PS_DEV.openBugReport after the game loads; keep ours whichever script runs first.
  try { Object.defineProperty(PS, 'openBugReport', { get: () => openBugReport, set: () => {}, enumerable: true, configurable: true }); } catch (e) { PS.openBugReport = openBugReport; }
  PS.bugReport = { open: openBugReport, close, captureShot, deviceInfo, playerName };
})();
