// Renderiza o piloto quadro a quadro com Playwright e envia para o ffmpeg.
// Uso:
//   node tools/render.js preview 1 5 12 30   -> PNGs em build/preview/
//   node tools/render.js video [fps]          -> build/video_mudo.mp4
//   node tools/render.js thumb                -> build/thumbnail.jpg (1280x720)
//   node tools/render.js avatar               -> build/avatar.png (800x800)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const BUILD = path.join(ROOT, 'build');
const timeline = JSON.parse(fs.readFileSync(path.join(BUILD, 'timeline.json'), 'utf8'));

(async () => {
  const [mode = 'preview', ...args] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.addInitScript(tl => { window.TIMELINE = tl; }, timeline);
  await page.goto('file://' + path.join(ROOT, 'index.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => typeof window.renderFrame === 'function');

  if (mode === 'preview') {
    fs.mkdirSync(path.join(BUILD, 'preview'), { recursive: true });
    for (const a of args) {
      await page.evaluate(t => window.renderFrame(t), parseFloat(a));
      await page.screenshot({ path: path.join(BUILD, 'preview', `t${a}.png`) });
    }
  } else if (mode === 'thumb') {
    await page.evaluate(() => window.renderThumb());
    await page.screenshot({ path: path.join(BUILD, 'thumb_full.png') });
    await new Promise((res, rej) => spawn('ffmpeg', ['-y', '-v', 'error', '-i', path.join(BUILD, 'thumb_full.png'), '-vf', 'scale=1280:720', '-q:v', '2', path.join(BUILD, 'thumbnail.jpg')], { stdio: 'inherit' }).on('exit', c => c ? rej(c) : res()));
  } else if (mode === 'avatar') {
    await page.evaluate(() => window.renderAvatar());
    await page.screenshot({ path: path.join(BUILD, 'avatar.png'), clip: { x: 420, y: 0, width: 1080, height: 1080 } });
  } else if (mode === 'video') {
    const fps = parseInt(args[0] || '30', 10);
    const frames = Math.ceil(timeline.total * fps);
    const out = path.join(BUILD, 'video_mudo.mp4');
    const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '23', '-pix_fmt', 'yuv420p', '-r', String(fps), out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let i = 0; i < frames; i++) {
      await page.evaluate(t => window.renderFrame(t), i / fps);
      const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 150 === 0) console.log(`quadro ${i}/${frames} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('exit', r));
    console.log('ok ->', out);
  }
  await browser.close();
})();
