const { chromium } = require('playwright');
const fs = require('fs');

async function exportAssets() {
  const browser = await chromium.launch({ headless: true });

  const assets = [
    { file: 'x-header.html', output: 'x-header.png', width: 1500, height: 500 },
    { file: 'twitter-launch-thread.html', output: 'twitter-thread.png', width: 1200, height: 675 },
    { file: 'linkedin-announcement.html', output: 'linkedin-announcement.png', width: 1200, height: 627 },
    { file: 'linkedin-cover.html', output: 'linkedin-cover.png', width: 1128, height: 191 },
    { file: 'logo.html', output: 'logo.png', width: 400, height: 400 },
  ];

  for (const asset of assets) {
    const filePath = `/root/agentic-crm/docs/social-assets/${asset.file}`;
    const outputPath = `/root/agentic-crm/docs/social-assets/${asset.output}`;

    if (!fs.existsSync(filePath)) {
      console.log(`Skipping ${asset.file} - not found`);
      continue;
    }

    console.log(`Processing ${asset.file}...`);
    const context = await browser.newContext({
      viewport: { width: asset.width, height: asset.height }
    });
    const page = await context.newPage();
    await page.setViewportSize({ width: asset.width, height: asset.height });
    await page.goto(`file://${filePath}`, { waitUntil: 'networkidle' });
    await page.screenshot({ path: outputPath, fullPage: false });
    await page.close();
    await context.close();
    console.log(`  -> Saved to ${outputPath}`);
  }

  // Instagram icons - export from combined sheet
  const igContext = await browser.newContext({ viewport: { width: 150, height: 150 } });
  const igAssets = ['product-demo', 'culture', 'tech-insights', 'stories'];
  const igNames = ['instagram-product-demo', 'instagram-culture', 'instagram-tech-insights', 'instagram-stories'];

  for (let i = 0; i < igAssets.length; i++) {
    const page = await igContext.newPage();
    await page.setViewportSize({ width: 150, height: 150 });
    // Create a simple icon page for each
    const iconHtml = `<!DOCTYPE html><html><head><style>
      body { margin: 0; background: #0A1628; width: 150px; height: 150px; display: flex; align-items: center; justify-content: center; }
    </style></head><body>
    </body></html>`;
    // Use clipping to get each icon from the combined sheet at position (i % 2 * 155 + 10, Math.floor(i / 2) * 155 + 10)
    const igPage = await igContext.newPage();
    await igPage.setViewportSize({ width: 600, height: 600 });
    await igPage.goto(`file:///root/agentic-crm/docs/social-assets/instagram-highlights.html`, { waitUntil: 'networkidle' });
    const x = (i % 2) * 155 + 10;
    const y = Math.floor(i / 2) * 155 + 10;
    await igPage.screenshot({
      path: `/root/agentic-crm/docs/social-assets/${igNames[i]}.png`,
      clip: { x, y, width: 145, height: 145 }
    });
    console.log(`  -> Saved ${igNames[i]}.png (clip: ${x},${y},145,145)`);
    await igPage.close();
  }

  await igContext.close();
  await browser.close();
  console.log('All done!');
}

exportAssets().catch(console.error);