const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  await p.goto('file://' + path.join(__dirname, 'carrossel_semana2.html')); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(600);
  const ids = await p.$$eval('.s', els => els.map(e => e.id));
  for (const id of ids) { const el = await p.$('#' + id);
    const [, c, s] = id.match(/([cp]\d)s(\d+)/);
    await el.screenshot({ path: path.join(__dirname, 'outsemana2', `carrossel_${c}_slide${s.padStart(2,'0')}.jpg`), type: 'jpeg', quality: 92 }); }
  await b.close(); console.log('ok', ids.length);
})();
