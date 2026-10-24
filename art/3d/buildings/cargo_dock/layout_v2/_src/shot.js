const puppeteer = require('/workspace/playtest/qnext/node_modules/puppeteer-core');
(async () => {
  const [, , port, ct, out, w = 375, h = 667, dpr = 2, extra = ''] = process.argv;
  const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', protocolTimeout: 900000, userDataDir: '/tmp/dockl_prof', args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage', '--enable-webgl'] }); console.log('launched');
  const p = await b.newPage(); await p.setViewport({ width: +w, height: +h, deviceScaleFactor: +dpr });
  p.on('console', m => console.log('page:', m.text())); p.on('pageerror', e => console.log('ERR', e.message));
  console.log('goto'); await p.goto(`http://127.0.0.1:${port}/index.html?ct=${ct}${extra}`); console.log('loaded page'); await p.waitForFunction('window.DONE === true', { timeout: 800000, polling: 2000 });
  await p.screenshot({ path: out }); await b.close(); console.log('wrote', out);
})();
