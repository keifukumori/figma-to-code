const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function takeScreenshot() {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  // 1280px幅に設定（Figmaデザインと同じ）
  await page.setViewport({ width: 1280, height: 800 });

  // accordion-areaのデバッグページを開く
  const htmlPath = path.resolve(__dirname, 'dist/f/debug/accordion-area.html');
  await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0' });

  // スクリーンショットを保存
  const screenshotDir = path.resolve(__dirname, 'screenshots');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  await page.screenshot({
    path: path.join(screenshotDir, 'accordion-area-output.png'),
    fullPage: true
  });

  console.log('Screenshot saved to screenshots/accordion-area-output.png');

  await browser.close();
}

takeScreenshot().catch(console.error);
