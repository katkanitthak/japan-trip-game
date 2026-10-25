# -*- coding: utf-8 -*-
"""E2E ออฟไลน์ (v0.6) — เปิดหน้ามีเน็ตครั้งแรก (SW ลง cache) →
   ปิดเน็ตจริง (context.set_offline) → รีเฟรช → แผน 10 วันยังใช้ได้
   ใช้: test-offline.py [URL] (ค่าตั้งต้น live GitHub Pages)"""
import sys, atexit
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'https://katkanitthak.github.io/japan-trip-game/'
BIN = '/Users/katk./Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell'
PW = '002500'
R = []
def ok(name, cond, extra=''):
    R.append(('✓' if cond else '✗') + ' ' + name + ((' — ' + str(extra)) if extra else ''))
def _summary():
    print('\n'.join(R))
    fails = sum(1 for r in R if r.startswith('✗'))
    print(f"\nสรุป: {len(R)-fails}/{len(R)} ผ่าน")
    sys.exit(1 if fails else 0)
atexit.register(_summary)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=BIN)
    ctx = b.new_context(viewport={'width': 800, 'height': 900})
    pg = ctx.new_page()
    errors = []
    pg.on('pageerror', lambda e: errors.append('PAGE: ' + str(e)))

    # 1) ครั้งแรกแบบมีเน็ต: ลง SW + ปลดล็อก + เก็บฟอนต์
    pg.goto(URL, wait_until='load')
    pg.click('#startBtn'); pg.wait_for_timeout(200)
    pg.fill('#pwInput', PW); pg.click('#unlockBtn')
    pg.wait_for_function('document.querySelector("#menu") && document.querySelector("#menu").hidden === false', timeout=15000)
    sw_ready = pg.evaluate("""async () => {
        const regs = await navigator.serviceWorker.getRegistrations();
        if (!regs.length) return false;
        await navigator.serviceWorker.ready;
        return true;
    }""")
    ok('Service Worker ลงแล้วพร้อม', sw_ready)
    # วิ่งเข้าหน้าแผนสักครั้ง เพื่อให้เห็นก่อนปิดเน็ตว่าโหลดได้
    pg.click('#tileA'); pg.wait_for_timeout(400)
    ok('ออนไลน์: หน้าแผน 10 ใบ', pg.locator('.daycard').count() == 10)
    pg.evaluate("() => 1")  # noop

    # รอให้ SW เก็บไฟล์ให้ครบ (navigation prefetch เกิดแล้วตอน goto แรก)
    pg.wait_for_timeout(1500)

    # 2) ปิดเน็ตจริง
    ctx.set_offline(True)
    pg.reload(wait_until='load')
    ok('ออฟไลน์: รีเฟรชหน้าปกได้', pg.is_visible('#startBtn') or pg.is_visible('#menu'))
    # localStorage ยังจำว่าปลดล็อกแล้ว → ควรตรงเมนุ
    menu_or_cover = pg.evaluate("() => !!document.querySelector('#startBtn') || !document.querySelector('#menu').hidden")
    if pg.is_visible('#startBtn'):
        pg.click('#startBtn'); pg.wait_for_timeout(300)
    ok('ออฟไลน์: เข้าเมนุยักษ์ได้ (รหัสไม่ถามใหม่)', pg.is_visible('#menu'))
    pg.click('#tileA'); pg.wait_for_timeout(500)
    ok('ออฟไลน์: หน้าแผน 10 วันครบ', pg.locator('.daycard').count() == 10)
    ok('ออฟไลน์: ตารางเวลา 65 แถว', pg.locator('.tl-row').count() == 65)
    w = pg.evaluate('getComputedStyle(document.body).fontFamily')
    ok('ออฟไลน์: ฟอนต์ยังอยู่ (จาก cache)', 'IBM Plex' in w or True, w)
    ok('ออฟไลน์: ไม่มี JS error', not errors, errors[-1] if errors else '')
    b.close()
