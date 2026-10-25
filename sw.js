/* Service Worker — เกมสมุดแท็บทริปญี่ปุ่น
   เก็บทุกอย่างลง cache ตั้งแต่ครั้งแรกที่เปิดแบบมีเน็ต → เปิดซ้ำแบบออฟไลน์ได้
   (หน้าแผน 10 วันข้อมูลฝังในไฟล์อยู่แล้ว + ฟอนต์จาก Google CDN เก็บซ้ำพอเจอครั้งแรก) */
const CACHE = 'chaokuay-offline-v06';
const PRECACHE = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png'
];

self.addEventListener('install', (e) => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(PRECACHE)));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;                       /* POST ไม่แคช */
  const url = new URL(req.url);
  const same = url.origin === location.origin;
  if (!same && !/fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)) return; /* เฉพาะไฟล์เรา + ฟอนต์ */
  if (url.pathname.endsWith('docs-pack.enc') && !same) return;

  e.respondWith(
    caches.match(req).then((hit) => {
      if (hit) return hit;
      const fetchLive = fetch(req).then((res) => {
        if (res && res.status === 200) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      });
      /* ออฟไลน์ในหน้าเว็บกลับ: ถ้าเป็น navigation ให้ตกหน้า index จาก cache */
      if (req.mode === 'navigate') {
        return fetchLive.catch(() => caches.match('./index.html').then((p) => p || Response.error()));
      }
      return fetchLive;
    })
  );
});
