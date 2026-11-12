const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const FRAMES_DIR = path.resolve(__dirname, 'frames');
if (!fs.existsSync(FRAMES_DIR)) {
  fs.mkdirSync(FRAMES_DIR, { recursive: true });
}

(async () => {
  console.log('Starting Headless Chromium for cloud rendering...');
  const candidatePaths = [
    '/usr/bin/chromium-browser',
    '/usr/bin/chromium',
    '/snap/bin/chromium',
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
  ];
  const execPath = candidatePaths.find(p => fs.existsSync(p)) || '/usr/bin/chromium-browser';
  console.log('Using browser executable at:', execPath);

  const browser = await puppeteer.launch({
    executablePath: execPath,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--enable-unsafe-swiftshader',
      '--use-gl=swiftshader',
      '--window-size=720,1280'
    ]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 720, height: 1280, deviceScaleFactor: 1 });

  const htmlUrl = 'file://' + path.resolve(__dirname, 'demo.html');
  console.log('Loading page:', htmlUrl);
  await page.goto(htmlUrl);

  // Wait for map readiness
  await page.waitForFunction('window.__READY === true', { timeout: 35000 });
  console.log('MapLibre GL initialized successfully in cloud runner!');

  // Query duration from SUB_CHUNKS or default 36.3s
  const duration = await page.evaluate(() => {
    if (window.SUB_CHUNKS && window.SUB_CHUNKS.length > 0) {
      return window.SUB_CHUNKS[window.SUB_CHUNKS.length - 1].end + 0.5;
    }
    return 36.3;
  });

  const fps = 30;
  const totalFrames = Math.ceil(duration * fps);
  console.log(`Rendering ${totalFrames} frames at ${fps} FPS (Duration: ${duration}s)...`);

  for (let f = 0; f < totalFrames; f++) {
    const t = Math.round((f / fps) * 1000) / 1000;
    await page.evaluate((currT) => window.renderAt(currT), t);

    const frameFile = path.join(FRAMES_DIR, `frame_${String(f).padStart(4, '0')}.jpg`);
    await page.screenshot({ path: frameFile, type: 'jpeg', quality: 90 });

    if (f % 150 === 0 || f === totalFrames - 1) {
      console.log(`Rendered frame ${f} / ${totalFrames} (${Math.round((f / totalFrames) * 100)}%)`);
    }
  }

  console.log('All frames captured successfully!');
  await browser.close();
})();
