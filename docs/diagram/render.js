// Renders architecture.svg to ../architecture.png at 2x with headless Chromium.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

(async () => {
  const svg = fs.readFileSync(path.join(__dirname, 'architecture.svg'), 'utf8');
  const [, w, h] = svg.match(/width="(\d+)" height="(\d+)"/).map(Number);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
  await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(__dirname, '..', 'architecture.png'), clip: { x: 0, y: 0, width: w, height: h } });
  await browser.close();
})();
