// Stills + full-bay walk recording for the crew-nav fix. Not part of the assert.
//   node qa/crewnav-shot.mjs unfixed /opt/cursor/artifacts/crewnav_before.png
//   node qa/crewnav-shot.mjs fixed  /opt/cursor/artifacts/crewnav_after.png /opt/cursor/artifacts/crewnav_fullbay.webm
// Camera is moved only in this capture (renderer.render wrapper). The game camera code is unchanged.
import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary', '.png': 'image/png', '.svg': 'image/svg+xml', '.mp3': 'audio/mpeg' };
const [build, stillPath, videoPath] = process.argv.slice(2);
const PORT = build === 'unfixed' ? 8766 : 8767;

function serve() {
  const server = createServer((req, res) => {
    try {
      const url = new URL(req.url, 'http://127.0.0.1');
      let p = decodeURIComponent(url.pathname);
      if (p.endsWith('/')) p += 'index.html';
      if (build === 'unfixed' && /\/dev\/main\.js$/.test(p)) {
        res.writeHead(200, { 'content-type': 'text/javascript', 'cache-control': 'no-store' });
        res.end(readFileSync('/tmp/unfixed-main.js')); return;
      }
      const file = normalize(join(ROOT, p));
      if (!file.startsWith(normalize(ROOT))) { res.writeHead(403); res.end(); return; }
      res.writeHead(200, { 'content-type': MIME[extname(file)] || 'application/octet-stream', 'cache-control': 'no-store' });
      res.end(readFileSync(file));
    } catch (e) { res.writeHead(404); res.end(); }
  });
  return new Promise(r => server.listen(PORT, '127.0.0.1', () => r(server)));
}

const LOCK = `(() => {
  const ps = window.__ps3d, cam = ps.camera, THREE = ps.THREE;
  const look = new THREE.Vector3(632.2, 1.1, 5.4);
  const eye = new THREE.Vector3(631.4, 4.8, 18.6);
  cam.fov = 42; cam.updateProjectionMatrix();
  const render = ps.renderer.render.bind(ps.renderer);
  ps.renderer.render = function () { cam.position.copy(eye); cam.lookAt(look); cam.updateMatrixWorld(); return render(ps.scene, cam); };
})()`;

async function boot(browser) {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, hasTouch: true, isMobile: true,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1' });
  const page = await context.newPage();
  page.setViewportSize({ width: 390, height: 844 });
  page.setDefaultTimeout(120000);
  await page.goto(`http://127.0.0.1:${PORT}/dev/index.html?mock=1&qa=1&fresh=1`, { waitUntil: 'domcontentloaded' });
  await page.fill('#gateCode', '00010');
  await page.click('#gateGo');
  await page.waitForSelector('#nameGate.on');
  await page.fill('#nameIn', 'Nav QA');
  await page.click('#nameGo');
  await page.waitForFunction(() => {
    const p = window.__ps3d;
    return p && p.coverGone && p.wk && p.wk.ready && p.BD && p.BD.root && p.cg3 && p.cg3.baySlots && p.cg3.boxParts && p.cg3.boxParts.some(b => b.L);
  });
  await page.evaluate(() => window.__ps3d.goSite(window.__ps3d.PADI));
  await page.waitForFunction(() => Math.abs(window.__ps3d.camX - window.__ps3d.PX) < 3);
  await page.evaluate(() => {
    const ps = window.__ps3d, c = ps.S.cg;
    c.bay = 12; c.dk = 20; c.ref = Array.from({ length: 8 }, () => 1e15); c.sh.st = 'pad'; c.sh.req = 0;
    ps.poseNow();
  });
  return { context, page };
}

async function main() {
  const server = await serve();
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--mute-audio'] });
  const { context, page } = await boot(browser);
  // Seek the boarding clip to the moment the unfixed walk is inside the bay (crew time ~7.5 s, found by the self-check).
  await page.evaluate(() => {
    const ps = window.__ps3d, now = ps.nowMs();
    ps.S.cg.sh.st = 'board'; ps.S.cg.sh.fly = 4; ps.S.cg.sh.t0 = now - 8000; ps.S.bc = { id: 1, on: 0, x: 1 };
    ps.updCrew();
  });
  await page.evaluate(LOCK);
  await page.waitForTimeout(400);
  await page.screenshot({ path: stillPath });
  console.log('STILL', stillPath);
  if (videoPath) {
    const { mkdirSync } = await import('node:fs');
    const { spawnSync } = await import('node:child_process');
    mkdirSync('/tmp/crewnav-frames', { recursive: true });
    // Step the boarding clock ourselves so the clip doesn't race ahead of the screenshots.
    for (let i = 0; i < 64; i++) {
      const tb = 3.2 + i * 0.18;
      await page.evaluate((tb) => {
        const ps = window.__ps3d;
        ps.S.cg.sh.st = 'board'; ps.S.cg.sh.fly = 4; ps.S.cg.sh.req = 0;
        ps.S.cg.sh.t0 = ps.nowMs() - tb * 1000; ps.S.bc = { id: 2, on: 0, x: 1 };
        ps.updCrew();
      }, tb);
      await page.screenshot({ path: '/tmp/crewnav-frames/f' + String(i).padStart(3, '0') + '.png' });
    }
    const mp4 = videoPath.endsWith('.mp4') ? videoPath : videoPath.replace(/\.webm$/, '.mp4');
    const ff = spawnSync('ffmpeg', ['-y', '-framerate', '8', '-i', '/tmp/crewnav-frames/f%03d.png', '-an', '-vf', 'scale=390:844', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4], { stdio: 'inherit' });
    if (ff.status) throw new Error('ffmpeg ' + ff.status);
    console.log('MP4', mp4);
  }
  await context.close();
  await browser.close();
  server.close();
}

main().catch(e => { console.error(e); process.exit(1); });
