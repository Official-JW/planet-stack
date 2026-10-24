// Proof renders from the real QA3D a25e5d0 page (served locally), camera override applied through the game's own fitSite() path.
const puppeteer = require('/workspace/playtest/q3d5/node_modules/puppeteer-core');
const fs = require('fs');
const F = JSON.parse(fs.readFileSync('final.json'));
const OUT = '/workspace/planet-stack/art/3d/_audit/';
const JOBS = [];
for (const [k, i, name] of [['mine', 1, 'mine'], ['ls', 0, 'lifesupport']]) {
  const f = F[k]; const ov = { ct: f.ct_local, frame_w: f.fw }; const cur = k === 'mine' ? null : { ct: { y: -3.1 }, frame_w: 46 };
  const lab = (o, sp) => `${name === 'mine' ? 'Mine a4f93eb' : 'Life Support adfaac9'}  ${o ? 'override' : 'current'}: Cam_Target (${o ? [o.ct.x, o.ct.y, o.ct.z].join(', ') : ''}) frame_w ${o ? o.frame_w : ''}`;
  for (const [w, h, dpr, sz, top, bot] of [[375, 667, 1, '375x667', 144, 383], [393, 852, 1, '393x852', 165, 534], [375, 667, 3, '1125x2001_3x', 144, 383]]) {
    const key = w + 'x' + h; const sp = f.spare[key];
    JOBS.push({ i, w, h, dpr, top, bot, ov, file: `${name}_override_${sz}.png`, label: `${name === 'mine' ? 'Mine (a4f93eb)' : 'Life Support (adfaac9)'} NEW Cam_Target (${f.ct_local.x}, ${f.ct_local.y}, ${f.ct_local.z}) frame_w ${f.fw}`,
      label2: `spare px @${key}: top ${sp.top.toFixed(1)}  bottom ${sp.bottom.toFixed(1)}  left ${sp.left.toFixed(1)}  right ${sp.right.toFixed(1)}  (all tiers on)` });
  }
  const c = f.current, csp = c.spare['375x667'];
  JOBS.push({ i, w: 375, h: 667, dpr: 1, top: 144, bot: 383, ov: k === 'mine' ? null : { ct: { y: -3.1 }, frame_w: 46 }, file: `${name}_override_current_375x667.png`,
    label: `${name === 'mine' ? 'Mine (a4f93eb)' : 'Life Support (adfaac9)'} CURRENT (QA3D 22:22) Cam_Target (${(c.T.x - (k === 'mine' ? 160 : 0)).toFixed(2)}, ${c.T.y}, ${c.T.z}) frame_w ${c.T.fw}`,
    label2: `spare px @375x667: top ${csp.top.toFixed(1)}  bottom ${csp.bottom.toFixed(1)}  left ${csp.left.toFixed(1)}  right ${csp.right.toFixed(1)}` });
}
(async () => {
  const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', protocolTimeout: 600000,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'] });
  for (const J of JOBS) {
    const p = await b.newPage(); await p.setViewport({ width: J.w, height: J.h, deviceScaleFactor: J.dpr, isMobile: true, hasTouch: true });
    p.on('pageerror', e => console.log('ERR', String(e)));
    await p.goto('http://127.0.0.1:18931/index.html?fresh=1');
    await p.waitForFunction((i) => { const P = window.__ps3d; return P && P.RT && P.RT.ready && P.stationObjs && P.stationObjs[i] && P.truck && document.getElementById('cover') == null; }, { timeout: 180000 }, J.i);
    await p.evaluate((J) => { const P = window.__ps3d, o = P.stationObjs[J.i];
      o.traverse(n => { if (/^Tier_\d+/.test(n.name)) { n.visible = true; n.scale.setScalar(1); } });
      if (J.ov) o.userData.camOv = Object.assign({ md5: 'audit' }, J.ov); else o.userData.camOv = null;
      dispatchEvent(new Event('resize')); P.goSite(J.i); }, J);
    await new Promise(r => setTimeout(r, 6000));
    const sc = await p.evaluate((J) => { const P = window.__ps3d; P.stationObjs[J.i].traverse(n => { if (/^Tier_\d+/.test(n.name)) { n.visible = true; n.scale.setScalar(1); } });
      const c = document.createElement('canvas'); c.width = J.w * J.dpr; c.height = J.h * J.dpr; c.style.cssText = `position:fixed;left:0;top:0;width:${J.w}px;height:${J.h}px;pointer-events:none;z-index:99999`;
      const g = c.getContext('2d'); g.scale(J.dpr, J.dpr); g.strokeStyle = '#ff3355'; g.lineWidth = 1.5; g.setLineDash([6, 4]);
      for (const y of [J.top, J.bot]) { g.beginPath(); g.moveTo(0, y); g.lineTo(J.w, y); g.stroke(); }
      g.strokeStyle = 'rgba(255,200,0,.8)'; g.lineWidth = 1; g.setLineDash([2, 3]); for (const y of [J.top + 5, J.bot - 5]) { g.beginPath(); g.moveTo(0, y); g.lineTo(J.w, y); g.stroke(); }
      g.setLineDash([]); g.font = '600 10px sans-serif'; g.fillStyle = '#ff6680'; g.fillText('band y ' + J.top, J.w - 70, J.top - 4); g.fillText('band y ' + J.bot, J.w - 70, J.bot + 12);
      g.fillStyle = 'rgba(0,0,0,.6)'; g.fillRect(0, J.bot + 16, J.w, 30); g.fillStyle = '#fff'; g.font = '600 9.5px sans-serif'; g.fillText(J.label, 4, J.bot + 28); g.fillText(J.label2, 4, J.bot + 41);
      document.body.appendChild(c); const S = P.SITECAM[J.i]; return { site: P.S.site, sc: S, cam: P.camera ? null : null }; }, J);
    await new Promise(r => setTimeout(r, 1500));
    await p.screenshot({ path: OUT + J.file }); console.log(J.file, JSON.stringify(sc)); await p.close();
  }
  await b.close();
})();
