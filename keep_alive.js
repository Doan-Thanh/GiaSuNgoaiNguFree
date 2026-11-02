const https = require('https');

const URLS = [
  'https://giasungoaingufree.onrender.com/api/ping',
  'https://giasungoaingufree.onrender.com/api/config'
];
const INTERVAL_MS = 10 * 60 * 1000; // 10 phút (Render ngủ sau 15 phút)

function pingTarget(url) {
  return new Promise((resolve) => {
    const req = https.get(url, {
      headers: { 'User-Agent': 'GiaSuKeepAlive/1.0 (PM2-Local)' },
      timeout: 35000
    }, (res) => {
      console.log(`[${new Date().toLocaleTimeString('vi-VN')}] Ping ${url} -> Status: ${res.statusCode} (SUCCESS)`);
      resolve(res.statusCode < 400);
    });

    req.on('error', (err) => {
      console.warn(`[${new Date().toLocaleTimeString('vi-VN')}] Ping ${url} -> Error: ${err.message}`);
      resolve(false);
    });

    req.on('timeout', () => {
      req.destroy();
      console.warn(`[${new Date().toLocaleTimeString('vi-VN')}] Ping ${url} -> Timeout.`);
      resolve(false);
    });
  });
}

async function doPing() {
  for (const url of URLS) {
    const ok = await pingTarget(url);
    if (ok) return;
  }
}

console.log(`[KeepAlive] Khởi động tiến trình giữ ấm cho Render (Chu kỳ: 10 phút)...`);
doPing();
setInterval(doPing, INTERVAL_MS);
