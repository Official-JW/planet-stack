// ST-10B game GLB game-cam proofs.  node gamecam_b_game.js sweep|final <url> <outdir> [glb]
//  sweep: shaded-side p25 vs an sRGB COLOR_0 lift (in-page) on loaded+empty @393 -> <out>/sweep.json (pick = closest to 67 with both in 60-75)
//  final: baked GLB, no lift: loaded/empty x 393x852/375x667 x DPR 1 (+clean) and 2 -> PNGs + results.json (spare, p25, draw calls via renderer.info)
const puppeteer = require('/workspace/playtest/q3d5/node_modules/puppeteer-core'); const fs = require('fs');
const [MODE, URL, OUT, GLB] = [process.argv[2], process.argv[3], process.argv[4], process.argv[5] || 'm/st10b_game.glb'];
fs.mkdirSync(OUT, { recursive: true });
const SZ = [{ w: 393, h: 852, band: [12, 381, 165, 534] }, { w: 375, h: 667, band: [12, 363, 144, 383] }], XT = 52;
(async () => {
  const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', protocolTimeout: 1200000,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'] });
  const page = async (w, h, dpr, o) => { const p = await b.newPage(); await p.setViewport({ width: w, height: h, deviceScaleFactor: dpr });
    p.on('pageerror', e => console.log('ERR', String(e))); p.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
    await p.goto(`${URL}/gamecam.html?dpr=${dpr}`); await p.waitForFunction(() => window.READY);
    const info = await p.evaluate(o => setup(o), { pad: 'm/launch_pad_game.glb', trn: GLB, xt: XT, game: true, ...o }); return [p, info]; };
  const poses = {};
  for (const l of ['loaded', 'empty']) { const [p] = await page(393, 852, 1, { loaded: l === 'loaded' }); poses[l] = await p.evaluate(S => solve(S, 5), SZ); await p.close(); }
  if (MODE === 'sweep') {
    // rows: [lift, emis]; albedo lift alone saturates near p25 36 (hemi-only shaded side), so the sweep also varies Paint emissive
    const ROWS = JSON.parse(process.env.ROWS || '[[0,0],[0,0.06],[0,0.09],[0,0.12],[0,0.15],[0.15,0.1]]'), res = { poses, rows: [] };
    for (const [L, E] of ROWS) { const row = { lift: L, emis: E };
      for (const l of ['loaded', 'empty']) { const [p] = await page(393, 852, 1, { loaded: l === 'loaded', vlift: L, emis: E }); row[l] = await p.evaluate((t, fw) => p25(t, fw), poses[l].t, poses[l].fw); await p.close(); }
      console.log('sweep', JSON.stringify(row)); res.rows.push(row); }
    const ok = res.rows.filter(r => r.loaded.shaded_p25 >= 60 && r.loaded.shaded_p25 <= 75 && r.empty.shaded_p25 >= 60 && r.empty.shaded_p25 <= 75);
    const sc = r => Math.abs(r.loaded.shaded_p25 - 67.5) + Math.abs(r.empty.shaded_p25 - 67.5);
    res.pick = (ok.length ? ok : res.rows).sort((a, c) => sc(a) - sc(c))[0]; res.pick = { lift: res.pick.lift, emis: res.pick.emis }; res.in_range = ok.length > 0;
    fs.writeFileSync(`${OUT}/sweep.json`, JSON.stringify(res, null, 1)); console.log('PICK', JSON.stringify(res.pick), res.in_range); await b.close(); return; }
  const res = { glb: GLB, poses };
  for (const l of ['loaded', 'empty']) for (const dpr of [1, 2]) for (const s of SZ) {
    const [p, info] = await page(s.w, s.h, dpr, { loaded: l === 'loaded' }); const pose = poses[l]; const r = pose.res.find(q => q.size === s.w + 'x' + s.h);
    const lum = await p.evaluate((t, fw) => p25(t, fw), pose.t, pose.fw); const dc = await p.evaluate((t, fw) => calls(t, fw), pose.t, pose.fw);
    const lab = `ST-10B game GLB · ${l} · ${s.w}x${s.h} · 38° vFOV / 18° down\nCam_Target (${pose.t.x.toFixed(1)}, ${pose.t.y.toFixed(1)}, ${pose.t.z.toFixed(1)}) frame_w ${pose.fw.toFixed(1)}\nspare ${r.spare.toFixed(1)} px ${r.spare >= 5 ? 'PASS' : 'FAIL'} · shaded p25 ${lum.shaded_p25} ${lum.shaded_p25 >= 60 && lum.shaded_p25 <= 75 ? 'PASS' : 'FAIL'} · ${dc.calls} draws · ${dc.triangles} tris`;
    await p.evaluate((t, fw, band, lab, bb) => shot(t, fw, band, lab, bb), pose.t, pose.fw, s.band, lab, r.bb);
    const f = `${OUT}/st10b_game_${l}_gamecam_${s.w}x${s.h}${dpr > 1 ? '@2x' : ''}.png`; await p.screenshot({ path: f });
    if (dpr === 1) { await p.evaluate(() => { const o = document.getElementById('ov'); o.getContext('2d').clearRect(0, 0, o.width, o.height); }); await p.screenshot({ path: f.replace('.png', '_clean.png') }); }
    res[`${l}_${s.w}x${s.h}${dpr > 1 ? '@2x' : ''}`] = { file: f.split('/').pop(), spare_px: +r.spare.toFixed(1), bb: r.bb, draw_calls: dc.calls, triangles_drawn: dc.triangles, visible_meshes: info.names, draws_astronaut: info.draws_astronaut, ...lum };
    console.log(f, 'spare', r.spare.toFixed(1), 'p25', lum.shaded_p25, 'calls', dc.calls, 'tris', dc.triangles); await p.close(); }
  fs.writeFileSync(`${OUT}/results.json`, JSON.stringify(res, null, 1)); await b.close();
})();
