// Renders each .s story (1080x1920) of stories_semana.html to outstories/story_NN.jpg
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
(async () => {
  const out = path.join(__dirname, 'outstories');
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + path.join(__dirname, 'stories_semana.html'));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(800);
  const els = await p.$$('.s');
  for (let i = 0; i < els.length; i++) {
    await els[i].screenshot({ path: path.join(out, `story_${String(i + 1).padStart(2, '0')}.jpg`), type: 'jpeg', quality: 90 });
  }
  console.log(els.length, 'stories');
  await b.close();
})();
