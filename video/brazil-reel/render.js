// Usage:
//   node render.js preview 0.5 3 5 ...    -> writes preview_<t>.png
//   node render.js video out_silent.mp4   -> renders all frames at 30fps through ffmpeg
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const FPS = 30;
const DUR = 54.3;

(async () => {
  const [mode, ...args] = process.argv.slice(2);
  const words = JSON.parse(fs.readFileSync(path.join(__dirname, 'words.json'), 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.join(__dirname, 'render.html'));
  await page.evaluate(() => document.fonts.ready);
  const n = await page.evaluate(([w, d]) => window.setup(w, d), [words, DUR]);
  console.error('captions:', n);

  const grab = async (t) => {
    const b64 = await page.evaluate((t) => { window.renderFrame(t); return document.getElementById('c').toDataURL('image/jpeg', 0.93).split(',')[1]; }, t);
    return Buffer.from(b64, 'base64');
  };

  if (mode === 'preview') {
    for (const a of args) fs.writeFileSync(path.join(process.env.OUT || __dirname, `preview_${a}.jpg`), await grab(parseFloat(a)));
  } else {
    const out = args[0];
    const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const total = Math.round(DUR * FPS);
    for (let f = 0; f < total; f++) {
      const buf = await grab(f / FPS);
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 150 === 0) console.error(`frame ${f}/${total}`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
