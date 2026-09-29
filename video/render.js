// Render each scene in a scenes file (default scenes.json) to a 1920x1080 PNG.
const fs = require('fs');
const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright');

const scenes = JSON.parse(fs.readFileSync(process.argv[2] || __dirname + '/scenes.json', 'utf8'));
const css = fs.readFileSync(__dirname + '/style.css', 'utf8');
const scores = [56, 59, 61, 67, 69, 72, 75, 79, 77, 82, 83, 84, 85, 85];
const bars = scores.map((s, i) =>
  `<div class="bar"><span class="bv">${s}</span><i style="height:${(s - 40) * 4.2}px"></i><span class="bl">${i + 1}</span></div>`).join('');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  fs.mkdirSync(__dirname + '/build', { recursive: true });
  for (const s of scenes) {
    const html = `<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head><body>${s.html.replace('__BARS__', bars)}</body></html>`;
    await page.setContent(html);
    await page.screenshot({ path: `${__dirname}/build/${s.id}.png` });
  }
  await browser.close();
})();
