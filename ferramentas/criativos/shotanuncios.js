// Renders anuncios_consulta.html for each date and format.
// Usage: node shotanuncios.js <outDir> <day> <WEEKDAY>
// Output: <outDir>/<day>dez_<id>_feed.jpg (1080x1350) and _story.jpg (1080x1920)
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
(async () => {
  const [out, d, wd] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  for (const fmt of ['feed', 'story']) {
    const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
    const url = 'file://' + path.join(__dirname, 'anuncios_consulta.html') + `?d=${d}&wd=${encodeURIComponent(wd)}&fmt=${fmt}`;
    await p.goto(url);
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(800);
    const ids = await p.$$eval('.a', (els) => els.map((e) => e.id));
    for (const id of ids) {
      await (await p.$(`[id="${id}"]`)).screenshot({ path: path.join(out, `${d}dez_${id}_${fmt}.jpg`), type: 'jpeg', quality: 92 });
    }
    await p.close();
  }
  await b.close();
  console.log('ok');
})();
