// node gamecam_run.js <servedir-url> <outdir>   (serve dir holds gamecam.html, vendor/ (three r186 copy), m/ (GLBs))
const puppeteer = require('/workspace/playtest/q3d5/node_modules/puppeteer-core');
const fs = require('fs');
const [URL, OUT] = [process.argv[2] || 'http://127.0.0.1:8771', process.argv[3] || '/tmp/st_work/gc_out'];
fs.mkdirSync(OUT, { recursive: true });
const SZ = [{ w: 393, h: 852, band: [12, 381, 165, 534] }, { w: 375, h: 667, band: [12, 363, 144, 383] }];
const XT = 52;      // ship axis on the road, pad-local x (transporter spans x 38.6..67.7: clear of the pad edge 29.4)
const BASE = { G_Graphite: '#5d6880', G_Graphite2: '#6b7690', G_Steel: '#97a3bb', G_Track: '#7a808b', G_Tyre: '#6e737c', G_PadRubber: '#58606e', G_Ink: '#2a3245', G_Hazard: '#c99a3c', G_Rod: '#c3cad6', G_Pale: '#c9d3e6', G_White: '#e8edf5' };
const lift = (L) => { const o = {}; for (const [k, h] of Object.entries(BASE)) { const n = parseInt(h.slice(1), 16), c = [n >> 16, (n >> 8) & 255, n & 255].map(x => Math.round(x + (255 - x) * L)); o[k] = '#' + c.map(x => x.toString(16).padStart(2, '0')).join(''); } return o; };
const LIFTS = [0, 0.15, 0.3, 0.45, 0.6];
const PALSEL = {};
const JOBS = [];
for (const c of ['a', 'b']) for (const l of ['loaded', 'empty']) JOBS.push({ c, l });
(async () => {
  const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', protocolTimeout: 1200000,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'] });
  const res = {}; res.sweep = {};
  for (const c of ['a', 'b']) {   // palette lift sweep on the loaded 393x852 view: smallest lift with shaded p25 >= 62 (target 60-75)
    const p = await b.newPage(); await p.setViewport({ width: 393, height: 852, deviceScaleFactor: 1 });
    await p.goto(`${URL}/gamecam.html?dpr=1`); await p.waitForFunction(() => window.READY);
    await p.evaluate(o => setup(o), { pad: 'm/launch_pad_game.glb', trn: `m/st10${c}_loaded_preview.glb`, xt: XT, loaded: true });
    const pose = await p.evaluate((S) => solve(S, 5), SZ); await p.close(); let pick = LIFTS[LIFTS.length - 1];
    for (const L of LIFTS) { const q = await b.newPage(); await q.setViewport({ width: 393, height: 852, deviceScaleFactor: 1 }); await q.goto(`${URL}/gamecam.html?dpr=1`); await q.waitForFunction(() => window.READY);
      await q.evaluate(o => setup(o), { pad: 'm/launch_pad_game.glb', trn: `m/st10${c}_loaded_preview.glb`, xt: XT, loaded: true, pal: lift(L) });
      const lum = await q.evaluate((t, fw) => p25(t, fw), pose.t, pose.fw); await q.close(); res.sweep[c + '_' + L] = lum; console.log('sweep', c, L, JSON.stringify(lum));
      if (lum.shaded_p25 >= 62) { pick = L; break; } }
    PALSEL[c] = { lift: pick, pal: lift(pick) };
  }
  res.palette = PALSEL;
  for (const j of JOBS) {
    let pose = null;
    for (const dpr of [1, 2]) for (const s of SZ) {
      const p = await b.newPage(); await p.setViewport({ width: s.w, height: s.h, deviceScaleFactor: dpr });
      p.on('pageerror', e => console.log('ERR', String(e))); p.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
      await p.goto(`${URL}/gamecam.html?dpr=${dpr}`); await p.waitForFunction(() => window.READY);
      const info = await p.evaluate(o => setup(o), { pad: 'm/launch_pad_game.glb', trn: `m/st10${j.c}_${j.l}_preview.glb`, xt: XT, loaded: j.l === 'loaded', pal: PALSEL[j.c].pal });
      if (!pose) pose = await p.evaluate((S) => solve(S, 5), SZ);
      const r = pose.res.find(q => q.size === s.w + 'x' + s.h);
      const lum = await p.evaluate((t, fw) => p25(t, fw), pose.t, pose.fw);
      const lab = `ST-10${j.c.toUpperCase()} ${j.l} · ${s.w}x${s.h} · 38° vFOV / 18° down\nCam_Target (${pose.t.x.toFixed(1)}, ${pose.t.y.toFixed(1)}, ${pose.t.z.toFixed(1)}) frame_w ${pose.fw.toFixed(1)}\nspare ${r.spare.toFixed(1)} px ${r.spare >= 5 ? 'PASS' : 'FAIL'} · shaded p25 ${lum.shaded_p25}`;
      await p.evaluate((t, fw, band, lab, bb) => shot(t, fw, band, lab, bb), pose.t, pose.fw, s.band, lab, r.bb);
      const f = `${OUT}/st10${j.c}_${j.l}_gamecam_${s.w}x${s.h}${dpr > 1 ? '@2x' : ''}.png`; await p.screenshot({ path: f });
      // clean (no overlay) 1x copy for the sheet
      if (dpr === 1) { await p.evaluate(() => { const o = document.getElementById('ov'); o.getContext('2d').clearRect(0, 0, o.width, o.height); }); await p.screenshot({ path: f.replace('.png', '_clean.png') }); }
      res[`${j.c}_${j.l}_${s.w}x${s.h}${dpr > 1 ? '@2x' : ''}`] = { file: f, pose: { t: pose.t, fw: pose.fw }, bb: r.bb, spare_px: +r.spare.toFixed(1), draws: info.draws, draws_astronaut: info.draws_astronaut, palette_lift: PALSEL[j.c].lift, tris_preview: info.tris, ...lum };
      console.log(f, 'spare', r.spare.toFixed(1), 'p25', lum.shaded_p25, 'draws', info.draws);
      await p.close();
    }
  }
  fs.writeFileSync(`${OUT}/gamecam_results.json`, JSON.stringify(res, null, 1)); await b.close();
})();
