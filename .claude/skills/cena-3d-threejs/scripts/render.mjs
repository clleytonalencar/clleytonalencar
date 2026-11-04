#!/usr/bin/env node
// Renderiza uma página Three.js determinística quadro a quadro (Playwright) e envia ao ffmpeg.
//
// Uso:
//   node render.mjs --page <pasta-do-episodio>/index.html --timeline <timeline.json> --preview 2 10 30
//   node render.mjs --page ... --timeline ... --video saida.mp4 [--fps 30] [--crf 20]
//   node render.mjs --page ... --timeline ... --still 12.5 --out quadro.png
//
// A página é servida por um servidor HTTP local (módulos ES não carregam via file://):
//   /            -> pasta da página
//   /engine/     -> engine/ desta skill
//   /three/      -> pacote "three" (node_modules mais próximo da página)
import { createServer } from 'node:http';
import { readFileSync, existsSync, mkdirSync, statSync } from 'node:fs';
import { dirname, join, resolve, extname } from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const HERE = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const PAGE = resolve(opt('page', 'index.html'));
const ROOT = dirname(PAGE);
const timeline = JSON.parse(readFileSync(resolve(opt('timeline', join(ROOT, 'build/timeline.json'))), 'utf8'));
const FPS = +opt('fps', 30);

function findThree(start) {
  let d = start; while (d !== dirname(d)) { const p = join(d, 'node_modules', 'three'); if (existsSync(p)) return p; d = dirname(d); }
  throw new Error('pacote "three" não encontrado: rode `npm install three` perto da página');
}
const MOUNTS = { '/engine/': join(HERE, '..', 'engine'), '/three/': findThree(ROOT), '/': ROOT };
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg' };
const server = createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  for (const [m, dir] of Object.entries(MOUNTS)) if (url.startsWith(m)) {
    const f = join(dir, url.slice(m.length) || 'index.html');
    if (existsSync(f) && statSync(f).isFile()) { res.writeHead(200, { 'content-type': MIME[extname(f)] || 'application/octet-stream' }); return res.end(readFileSync(f)); }
  }
  res.writeHead(404); res.end();
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('ERRO NA PÁGINA:', e.message));
await page.addInitScript(tl => { window.TIMELINE = tl; }, timeline);
await page.goto(`http://127.0.0.1:${port}/${PAGE.slice(ROOT.length + 1)}`);
await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
await page.evaluate(() => document.fonts.ready);
const frame = t => page.evaluate(t => window.renderFrame(t), t);

if (args.includes('--preview')) {
  const i = args.indexOf('--preview'); const times = args.slice(i + 1).filter(a => !a.startsWith('--')).map(Number);
  const dir = join(ROOT, 'build', 'preview'); mkdirSync(dir, { recursive: true });
  for (const t of times) { await frame(t); await page.screenshot({ path: join(dir, `t${t}.png`) }); console.log('preview', t); }
} else if (opt('thumb')) { // a página deve definir window.renderThumb() (cena + texto grande)
  await page.evaluate(() => window.renderThumb()); const png = resolve(opt('thumb')).replace(/\.jpe?g$/, '') + '_full.png';
  await page.screenshot({ path: png });
  await new Promise((res, rej) => spawn('ffmpeg', ['-y', '-v', 'error', '-i', png, '-vf', 'scale=1280:720', '-q:v', '2', resolve(opt('thumb'))], { stdio: 'inherit' }).on('exit', c => c ? rej(c) : res()));
  console.log('thumb ->', opt('thumb'));
} else if (opt('still')) {
  await frame(+opt('still')); await page.screenshot({ path: resolve(opt('out', 'quadro.png')) });
} else if (opt('video')) {
  const out = resolve(opt('video')); const frames = Math.ceil(timeline.total * FPS);
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', opt('crf', '20'), '-pix_fmt', 'yuv420p', '-r', String(FPS), out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = 0; i < frames; i++) {
    await frame(i / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 94 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) { const el = (Date.now() - t0) / 1000; console.log(`quadro ${i}/${frames}  ${el.toFixed(0)}s  (~${(el / Math.max(1, i) * (frames - i) / 60).toFixed(1)} min restantes)`); }
  }
  ff.stdin.end(); await new Promise(r => ff.on('exit', r)); console.log('ok ->', out);
}
await browser.close(); server.close();
