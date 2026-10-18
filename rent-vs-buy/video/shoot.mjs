// 各 HTML を 1920x1080 の PNG に撮影する
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const [dir, ...stems] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
for (const s of stems) {
  await page.goto(`file://${dir}/${s}.html`);
  await page.waitForTimeout(50);
  await page.screenshot({ path: `${dir}/${s}.png` });
}
await browser.close();
