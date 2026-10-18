// 仮の猫アバター（本番の猫アバター画像が届くまでの代用）。透明背景の PNG を4枚出力する。
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const dir = new URL('.', import.meta.url).pathname;
const mouth = {
  closed: '<path d="M128 178 q12 10 22 0 q10 10 22 0" fill="none" stroke="#3b2a20" stroke-width="5" stroke-linecap="round"/>',
  half:   '<path d="M128 176 q22 22 44 0 z" fill="#7a2e2e" stroke="#3b2a20" stroke-width="5" stroke-linejoin="round"/>',
  open:   '<path d="M126 174 q24 40 48 0 z" fill="#7a2e2e" stroke="#3b2a20" stroke-width="5" stroke-linejoin="round"/><ellipse cx="150" cy="194" rx="12" ry="7" fill="#e88"/>',
};
const eyes = {
  open: '<ellipse cx="112" cy="140" rx="13" ry="17" fill="#2a2a2a"/><ellipse cx="188" cy="140" rx="13" ry="17" fill="#2a2a2a"/><circle cx="116" cy="134" r="5" fill="#fff"/><circle cx="192" cy="134" r="5" fill="#fff"/>',
  shut: '<path d="M98 142 q14 10 28 0" fill="none" stroke="#2a2a2a" stroke-width="6" stroke-linecap="round"/><path d="M174 142 q14 10 28 0" fill="none" stroke="#2a2a2a" stroke-width="6" stroke-linecap="round"/>',
};
const cat = (m, e) => `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300">
<path d="M58 120 L70 30 L130 82 Z" fill="#f2a65a" stroke="#3b2a20" stroke-width="6" stroke-linejoin="round"/>
<path d="M242 120 L230 30 L170 82 Z" fill="#f2a65a" stroke="#3b2a20" stroke-width="6" stroke-linejoin="round"/>
<path d="M76 104 L80 52 L114 82 Z" fill="#f7c9b5"/><path d="M224 104 L220 52 L186 82 Z" fill="#f7c9b5"/>
<ellipse cx="150" cy="160" rx="112" ry="100" fill="#f2a65a" stroke="#3b2a20" stroke-width="6"/>
<path d="M150 62 q-8 22 0 34 M128 66 q-4 18 4 28 M172 66 q4 18 -4 28" stroke="#d9823a" stroke-width="7" fill="none" stroke-linecap="round"/>
<ellipse cx="150" cy="190" rx="54" ry="40" fill="#fff4e8"/>
${e}<path d="M142 160 h16 l-8 9 z" fill="#e0707a" stroke="#3b2a20" stroke-width="3" stroke-linejoin="round"/>
<path d="M150 169 v6" stroke="#3b2a20" stroke-width="4"/>${m}
<path d="M40 168 h44 M42 186 l42 -8 M260 168 h-44 M258 186 l-42 -8" stroke="#3b2a20" stroke-width="3" stroke-linecap="round"/>
<ellipse cx="94" cy="178" rx="13" ry="7" fill="#f4a0a0" opacity=".6"/><ellipse cx="206" cy="178" rx="13" ry="7" fill="#f4a0a0" opacity=".6"/>
</svg>`;
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 300, height: 300 } });
for (const [name, m, e] of [['closed', mouth.closed, eyes.open], ['half', mouth.half, eyes.open], ['open', mouth.open, eyes.open], ['blink', mouth.closed, eyes.shut]]) {
  await p.setContent(`<html><body style="margin:0;background:transparent">${cat(m, e)}</body></html>`);
  await p.screenshot({ path: `${dir}${name}.png`, omitBackground: true });
}
await b.close();
