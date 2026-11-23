// Minimal CDP driver (Node 22 stdlib only — global WebSocket) for capturing
// deterministic gameplay frames of Neon Dodger in headless Chromium.
//
// Usage:
//   node cdp-drive.mjs --url file:///path/game/index.html --out /dir/frames \
//       --width 1920 --height 1080 --seconds 14 --fps 30
//   node cdp-drive.mjs --url ... --out /dir/stills --width 1280 --height 720 \
//       --stills 0,4,8,13 --seconds 14
//
// The game is stepped with a fixed dt (1/fps) and driven by a deterministic
// greedy policy (dodge the lowest threatening asteroid, chase the lowest star,
// else drift to centre), so re-running with the same inputs yields the same
// frames byte for byte.

import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const args = Object.fromEntries(
  process.argv.slice(2).map((a, i, arr) => {
    if (a.startsWith('--')) return [a.slice(2), arr[i + 1]];
    return [];
  }).filter(([k]) => k)
);

const URL = args.url;
const OUT = args.out;
const WIDTH = parseInt(args.width || '1920', 10);
const HEIGHT = parseInt(args.height || '1080', 10);
const SECONDS = parseFloat(args.seconds || '14');
const FPS = parseInt(args.fps || '30', 10);
const STILLS = args.stills ? args.stills.split(',').map(Number) : null;
const CHROME = process.env.CHROME_BIN ||
  `${process.env.HOME}/.cache/ms-playwright/chromium_headless_shell-1255/chrome-headless-shell-linux64/chrome-headless-shell`;

if (!URL || !OUT) { console.error('need --url and --out'); process.exit(2); }
mkdirSync(OUT, { recursive: true });

const PORT = 9333 + Math.floor(Math.random() * 500);
const chrome = spawn(CHROME, [
  '--headless=new', '--disable-gpu', '--no-sandbox',
  `--remote-debugging-port=${PORT}`, '--hide-scrollbars',
  `--window-size=${WIDTH},${HEIGHT}`, 'about:blank',
], { stdio: 'ignore' });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function getWsUrl() {
  for (let i = 0; i < 50; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      const targets = await res.json();
      const page = targets.find((t) => t.type === 'page');
      if (page) return page.webSocketDebuggerUrl;
    } catch { /* not up yet */ }
    await sleep(200);
  }
  throw new Error('devtools not reachable');
}

let idSeq = 0;
const pending = new Map();
let ws;
function send(method, params = {}) {
  const id = ++idSeq;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function evalJs(expression) {
  const r = await send('Runtime.evaluate', { expression, returnByValue: true });
  if (r.exceptionDetails) throw new Error('eval failed: ' + JSON.stringify(r.exceptionDetails).slice(0, 400));
  return r.result.value;
}
async function shot(name) {
  const r = await send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(join(OUT, name), Buffer.from(r.data, 'base64'));
}

async function main() {
  const wsUrl = await getWsUrl();
  ws = new WebSocket(wsUrl);
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(msg.error.message));
      else resolve(msg.result);
    }
  };
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: HEIGHT, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: URL });
  await sleep(1500);
  await evalJs(`window.NEON && window.NEON.pause(true)`);

  const totalFrames = Math.round(SECONDS * FPS);
  const dt = 1 / FPS;
  const log = [];
  let endedLogged = false;
  const stillSet = new Set((STILLS || []).map((s) => Math.round(s * FPS)));

  if (STILLS && STILLS.includes(0)) await shot('shot-1-title.png');

  await evalJs('window.NEON.start()');
  let shotIdx = 2;
  for (let f = 0; f < totalFrames; f++) {
    // Greedy policy: dodge lowest threatening asteroid, else chase lowest star, else centre.
    const policy = await evalJs(`(() => {
      const g = window.NEON.game;
      const ship = g.ship;
      const threats = g.asteroids.filter(a => a.y > ship.y - 0.38 && a.y < ship.y + 0.05)
        .sort((a, b) => b.y - a.y);
      let dir = 0;
      const near = threats.find(a => Math.abs(a.x - ship.x) < 0.10);
      if (near) {
        dir = near.x >= ship.x ? -1 : 1;
      } else {
        const stars = g.pickups.filter(s => s.y < 0.8).sort((a, b) => b.y - a.y);
        if (stars.length) {
          const dx = stars[0].x - ship.x;
          if (Math.abs(dx) > 0.02) dir = dx > 0 ? 1 : -1;
        } else if (Math.abs(ship.x - 0.5) > 0.03) {
          dir = ship.x < 0.5 ? 1 : -1;
        }
      }
      window.NEON.setKeys({ left: dir < 0, right: dir > 0, up: false, down: false });
      return dir;
    })()`);
    await evalJs(`window.NEON.step(${dt}); window.NEON.render();`);
    if (STILLS) {
      if (stillSet.has(f)) {
        await shot(`shot-${shotIdx}.png`);
        shotIdx++;
      }
    } else {
      await shot(`frame-${String(f).padStart(4, '0')}.png`);
    }
    if (f % 30 === 0 || f === totalFrames - 1) {
      const snap = await evalJs('window.NEON.snapshot()');
      log.push({ frame: f, ...snap });
      console.log(JSON.stringify({ frame: f, ...snap }));
    }
    const snap = await evalJs('window.NEON.snapshot()');
    if ((snap.status === 'won' || snap.status === 'lost') && !endedLogged) {
      endedLogged = true;
      console.log('ENDED', JSON.stringify(snap));
      if (STILLS) await shot(`shot-${shotIdx}.png`);
    }
  }
  const final = await evalJs('window.NEON.snapshot()');
  console.log('FINAL ' + JSON.stringify(final));
  ws.close();
  chrome.kill();
  process.exit(0);
}

main().catch((e) => { console.error('DRIVER ERROR', e.message); chrome.kill(); process.exit(1); });
