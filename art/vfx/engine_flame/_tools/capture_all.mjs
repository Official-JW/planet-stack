// Renders every proof frame + metrics. Run from art/vfx/engine_flame:  PW=<playwright-core dir> node _tools/capture_all.mjs <outdir>
import { createRequire } from 'module'; import fs from 'fs';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW || 'playwright-core');
const OUT = process.argv[2] || '/tmp/ef_out'; fs.mkdirSync(OUT, { recursive: true }); fs.mkdirSync(OUT + '/video', { recursive: true });
const only = (process.env.ONLY || 'stills,strips,video,metrics').split(',');
const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
async function page(q, w, h, dpr) {
  const pg = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: dpr });
  pg.on('pageerror', e => console.log('[err]', e.message));
  await pg.goto(`http://127.0.0.1:${process.env.PORT || 8731}/art/vfx/engine_flame/index.html?ui=0&w=${w}&h=${h}&dpr=${dpr}&${q}`);
  await pg.waitForFunction(() => window.__ef && window.__ef.ready, null, { timeout: 120000 }); return pg;
}
const M = {};
const shot = async (pg, t, ph, file) => { const r = await pg.evaluate(([t, ph]) => window.__ef.frame(t, ph), [t, ph]); await pg.screenshot({ path: `${OUT}/${file}` }); return r; };
if (only.includes('stills')) for (const [w, h] of [[375, 667], [393, 852]]) for (const dpr of [1, 2]) {
  const pg = await page('view=pad', w, h, dpr), sfx = dpr === 2 ? '@2x' : '';
  M[`full_thrust_${w}x${h}${sfx}`] = await shot(pg, 3800, 'launch', `full_thrust_${w}x${h}${sfx}.png`);
  M[`ignition_dust_${w}x${h}${sfx}`] = await shot(pg, -1300, 'launch', `ignition_dust_${w}x${h}${sfx}.png`);
  // worst-case rumble frame: ship pushed to +SHAKE_PX and -SHAKE_PX at full rumble; pad/camera bbox measured
  if (dpr === 1) { await pg.evaluate(() => window.__ef.frame(-3500)); const rest = await pg.evaluate(() => ({ pad: window.__ef.bbox('pad'), ship: window.__ef.bbox('ship') }));
    const res = { rest };
    for (const s of [1, -1]) { await pg.evaluate((s) => { window.__ef.setShake(s); }, s); const f = await shot(pg, -200, 'launch', `shake_worst_${s > 0 ? 'R' : 'L'}_${w}x${h}.png`);
      res[s > 0 ? 'R' : 'L'] = { frame: f, pad: await pg.evaluate(() => window.__ef.bbox('pad')), ship: await pg.evaluate(() => window.__ef.bbox('ship')) }; }
    await pg.evaluate(() => window.__ef.setShake(0)); M[`shake_${w}x${h}`] = res; }
  await pg.close();
}
if (only.includes('stills')) { const pg = await page('view=close', 600, 600, 2); M.closeup = await shot(pg, 3500, 'launch', 'nozzle_closeup.png');
  M.closeup_ign = await shot(pg, -1500, 'launch', 'nozzle_closeup_ignition.png'); M.closeup_land = await shot(pg, -1200, 'land', 'nozzle_closeup_landing.png'); await pg.close(); }
if (only.includes('strips')) { const pg = await page('view=pad', 375, 667, 2);
  M.strip_launch = []; for (const t of [-2100, -1960, -1800, -1300, -800, 0, 1000, 2500, 3800, 5000, 6500]) M.strip_launch.push(await shot(pg, t, 'launch', `strip_L_${t}.png`));
  M.strip_land = []; for (const t of [-6000, -4000, -2600, -1800, -1000, -300, 0, 120, 300, 700, 1500]) M.strip_land.push(await shot(pg, t, 'land', `strip_D_${t}.png`));
  await pg.close(); }
if (only.includes('video')) { const pg = await page('view=pad', 375, 667, 2); let i = 0;
  for (let t = -3000; t <= 8000; t += 1000 / 30) { await pg.evaluate((t) => window.__ef.frame(Math.round(t), 'launch'), t); await pg.screenshot({ path: `${OUT}/video/L_${String(i++).padStart(4, '0')}.png` }); }
  i = 0; for (let t = -6000; t <= 2500; t += 1000 / 30) { await pg.evaluate((t) => window.__ef.frame(Math.round(t), 'land'), t); await pg.screenshot({ path: `${OUT}/video/D_${String(i++).padStart(4, '0')}.png` }); }
  await pg.close(); }
if (only.includes('metrics')) { const pg = await page('view=pad', 375, 667, 2);
  M.calls = await pg.evaluate(() => [window.__ef.countCalls(3800, 'launch'), window.__ef.countCalls(-1300, 'launch'), window.__ef.countCalls(400, 'land')]);
  M.timing = await pg.evaluate(() => { const S = window.__ef, gl = S.renderer.getContext(); const run = (on, n) => { const ts = []; for (let i = 0; i < n; i++) { const t = -1300 + (i % 40) * 10;
      const a = performance.now(); if (on) S.frame(t, 'launch'); else { S.frame(-3500, 'launch'); } gl.finish(); ts.push(performance.now() - a); } ts.sort((x, y) => x - y); return { median: ts[n >> 1], p90: ts[Math.floor(n * 0.9)] }; };
    run(true, 10); const off = run(false, 60), on = run(true, 60);
    const u = []; for (let i = 0; i < 400; i++) { const a = performance.now(); S.fx.update(window.__ef.last.st, i / 60, [{ kind: 'ring', t: 0.5, n: 110, o: { speed: 1 } }, { kind: 'ring', t: 0.3, n: 40, seed: 500, o: { speed: 0.7 } }], 400, 14); u.push(performance.now() - a); }
    u.sort((x, y) => x - y); return { swiftshader_frame_ms_effect_off: off, swiftshader_frame_ms_effect_on: on, fx_update_cpu_ms_median: u[200], fx_update_cpu_ms_p99: u[396], renderer_info: S.renderer.info.render, maxParticles: Math.max(...[...Array(200)].map((_, i) => S.frame(-2200 + i * 60, 'launch').particles)), maxParticlesLand: Math.max(...[...Array(200)].map((_, i) => S.frame(-6000 + i * 45, 'land').particles)) }; });
  M.engines = await pg.evaluate(() => window.__ef.engines); M.padTopY = await pg.evaluate(() => window.__ef.padTopY); await pg.close(); }
fs.writeFileSync(`${OUT}/metrics_${only.join('_')}.json`, JSON.stringify(M, null, 1));
await b.close(); console.log('done', OUT);
