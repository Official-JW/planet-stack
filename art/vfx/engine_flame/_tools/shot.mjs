// usage: PW=/path/to/playwright-core node shot.mjs '<query>' out.png ['js to eval after ready']
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW || 'playwright-core');
const [q, out, js] = process.argv.slice(2);
const P = new URLSearchParams(q); const w = +(P.get('w') || 375), h = +(P.get('h') || 667), dpr = +(P.get('dpr') || 1);
const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const pg = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: dpr });
pg.on('console', m => console.log('[page]', m.text())); pg.on('pageerror', e => console.log('[err]', e.message));
await pg.goto(`http://127.0.0.1:${process.env.PORT || 8731}/art/vfx/engine_flame/index.html?ui=0&${q}`);
await pg.waitForFunction(() => window.__ef && window.__ef.ready, null, { timeout: 120000 });
if (js) console.log(JSON.stringify(await pg.evaluate(js)));
await pg.screenshot({ path: out });
await b.close();
