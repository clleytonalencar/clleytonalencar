// Renders motion_data.html (10 s, 30 fps, 1080x1920) to a silent MP4.
// Usage: node rendermotion.js <out.mp4> <v> <day> <WEEKDAY> [preview]
// With "preview", writes a few PNG frames next to <out> instead of the video.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
(async () => {
  const [out, v, d, wd, preview] = process.argv.slice(2);
  const FPS = 30, DUR = 10, W = 1080, H = 1920;
  const frames = path.join(path.dirname(out), `frames_${v}`);
  fs.rmSync(frames, { recursive: true, force: true });
  fs.mkdirSync(frames, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: W, height: H } });
  await p.goto('file://' + path.join(__dirname, 'motion_data.html') + `?v=${v}&d=${d}&wd=${encodeURIComponent(wd)}`);
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(500);
  const times = preview ? [0, 1500, 4500, 6000, 9000] : [...Array(FPS * DUR).keys()].map((i) => (i * 1000) / FPS);
  for (const [i, t] of times.entries()) {
    await p.evaluate((ms) => window.seek(ms), t);
    await p.screenshot({ path: path.join(frames, preview ? `p_${t}.png` : `${String(i).padStart(4, '0')}.jpg`), type: preview ? 'png' : 'jpeg', quality: preview ? undefined : 92 });
  }
  await b.close();
  if (!preview) {
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(frames, '%04d.jpg'),
      '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-crf', '20', '-movflags', '+faststart', out]);
    fs.rmSync(frames, { recursive: true, force: true });
  }
  console.log('done', out);
})();
