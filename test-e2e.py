import sys, atexit
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'https://katkanitthak.github.io/japan-trip-game/'   # ชี้ลิงก์ที่จะเทส (live หรือ localhost)
BIN = '/Users/katk./Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell'
PW = '002500'
R = []
def ok(name, cond, extra=''):
    R.append(('✓' if cond else '✗') + ' ' + name + ((' — ' + str(extra)) if extra else ''))
def _summary():
    print('\n'.join(R))
    fails = sum(1 for r in R if r.startswith('✗'))
    print(f"\nสรุป: {len(R)-fails}/{len(R)} ผ่าน")
atexit.register(_summary)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=BIN)
    pg = b.new_page(viewport={'width': 800, 'height': 900})
    errors = []
    pg.on('pageerror', lambda e: errors.append('PAGE: ' + str(e)))
    pg.on('console', lambda m: errors.append('CONSOLE: ' + m.text) if m.type == 'error' else None)
    pg.goto(URL, wait_until='load')

    # 1) ปก → ปลดล็อก → **เมนูยักษ์ 5 ปุ่ม** (ไม่ใช่แผนโดยตรง)
    ok('ปกมีปุ่ม START', pg.is_visible('#startBtn'))
    pg.click('#startBtn'); pg.wait_for_timeout(200)
    ok('START → หน้าปลดล็อก', pg.is_visible('#unlock'))
    pg.fill('#pwInput', 'wrongpass'); pg.click('#unlockBtn'); pg.wait_for_timeout(900)
    ok('รหัสผิด → แจ้งเตือน', 'รหัสไม่ถูก' in (pg.text_content('#unlockErr') or ''))
    pg.fill('#pwInput', PW); pg.click('#unlockBtn')
    pg.wait_for_function('document.querySelector("#menu") && document.querySelector("#menu").hidden === false', timeout=8000)
    ok('รหัสถูก → เข้า**เมนูยักษ์**ก่อน', pg.is_visible('#menu'))
    ok('ปุ่มยักษ์ครบ 5 (A/B/C/D/🎒)', pg.locator('#menu .mtile').count() == 5)
    ok('ไม่พาเข้าเกมก่อน', pg.get_attribute('#game', 'hidden') is not None)

    # 2) A แผนทริป
    pg.click('#tileA'); pg.wait_for_timeout(400)
    ok('A → หน้าแผน (การ์ดวัน 10 ใบ)', pg.is_visible('#home') and pg.locator('.daycard').count() == 10)
    ok('ไฮไลต์มื้อ 10 กล่อง', pg.locator('.mealbox').count() == 10)
    tl = pg.locator('.tl-row').count()
    ok('ตารางเวลารวม 65 แถว', tl == 65, tl)
    ok('ป้ายยังไม่ได้จอง 4 วัน', pg.locator('.nobook').count() == 4, pg.locator('.nobook').count())
    chip1 = pg.text_content('#hd1 .chip.hotel'); chipT = pg.text_content('#hd1 .chip:not(.hotel)')
    ok('D1 ชิปโรงแรม + บิน + รถตู้ (3 เลข)', '1622928788440748' in chip1 and '1622927736922035' in chipT and 'GC020261015081836A054841' in chipT)
    chip2 = pg.text_content('#hd2 .chip:not(.hotel)')
    ok('D2 ชิป Kagayaki (เลขใหม่)', '1622931419787889' in chip2, chip2[:60])
    ok('แถบกระโดด 15 ปุ่ม (เมนู+D1-10+C/🎒/D/เกม)', pg.locator('.jb').count() == 15, pg.locator('.jb').count())

    # 3) ชิปรหัสจองกดได้ → ตัวดูรูปใบจองจริง (รอแพ็คถอดรหัสจบ)
    pg.click('#hd2 .bk.ok'); pg.wait_for_timeout(400)
    try:
        pg.wait_for_function('window.__docsLoaded === true', timeout=25000)
        loaded = True
    except Exception:
        loaded = pg.is_visible('#viewer')
    ok('แพ็ครูปถอดรหัสสำเร็จ (แล้ว cache)', loaded and pg.is_visible('#viewer'))
    src = pg.get_attribute('#vImg', 'src') or ''
    ok('ตัวดูรูป: รูปจากแพ็ค (data:image)', src.startswith('data:image/jpeg'), src[:28])
    cnt = pg.text_content('#vCount')
    pg.click('#vNext'); pg.wait_for_timeout(150)
    ok('เลื่อนรูปถัดไปได้ (2/2)', pg.text_content('#vCount') != cnt, cnt + '→' + (pg.text_content('#vCount') or ''))
    pg.click('#vClose'); pg.wait_for_timeout(200)
    ok('ปิดตัวดูรูปแล้วกลับหน้าเดิม', pg.is_visible('#home'))

    # 4) แถบกระโดด + สลับหน้า A↔เกม↔เมนู
    pg.click('#jumpbar .jb[data-n="7"]'); pg.wait_for_timeout(400)
    ok('กด D7 → ป้ายปัจจุบันเลื่อน', 'cur' in (pg.get_attribute('#jumpbar .jb[data-n="7"]', 'class') or ''))
    pg.click('#toGameBtn'); pg.wait_for_timeout(300)
    ok('ปุ่ม 🎮 → โหมดเกม', pg.is_visible('#game'))
    ok('เกม: HUD + แท็บวัน 10', pg.is_visible('#hud') and pg.locator('.tab').count() == 10)
    before = pg.text_content('#xpText')
    pg.locator('.quest input').first.click(); pg.wait_for_timeout(300)
    ok('ติ๊กภารกิจ → XP เปลี่ยน', pg.text_content('#xpText') != before, before + '→' + (pg.text_content('#xpText') or ''))
    pg.click('#homeB'); pg.wait_for_timeout(300)
    ok('ในเกมกด 🏛 เมนู → กลับเมนูยักษ์', pg.is_visible('#menu'))

    # 5) C ญี่ปุ่นไม่งง + 🎒 เช็คลิสต์แยกหน้า
    pg.click('#tileC'); pg.wait_for_timeout(300)
    ok('C → ญี่ปุ่นไม่งง (คำ 15/อากาศ 10/กฎหาร 5)', pg.is_visible('#know') and pg.locator('.phr .th').count() == 15 and pg.locator('.wstrip .wchip').count() == 10 and 'หาร 5' in pg.text_content('.rate-rule'))
    pg.click('#secMenuBtn'); pg.wait_for_timeout(250)
    pg.click('#tileP'); pg.wait_for_timeout(300)
    ok('🎒 → หน้าเช็คลิสต์ 8 ข้อ (แยกจาก C)', pg.is_visible('#pack') and pg.locator('.packrow').count() == 8)
    pg.locator('.packrow').first.click(); pg.wait_for_timeout(200)

    # 6) D เอกสารสำคัญ — แยกหมวด + รูป
    pg.click('#packMenuBtn'); pg.wait_for_timeout(250)
    pg.click('#tileD'); pg.wait_for_timeout(300)
    ok('D → เอกสารสำคัญ 12 การ์ด', pg.is_visible('#docs') and pg.locator('.doccard[data-doc]').count() == 12, pg.locator('.doccard[data-doc]').count())
    ok('D: หัวหมวด 4 (เครื่องบิน/รถไฟ/ที่พัก/รถ)', pg.locator('.doccat-t').count() == 5)   # 4 หมวด + หมวด "ยังไม่มี"
    ok('D: แสดงจำนวนรูป (📷 2 = ตั๋วรถไฟ)', pg.text_content('.doccard[data-doc="d2train"] .tn').strip() == '📷2', (pg.text_content('.doccard[data-doc="d2train"] .tn') or '').strip())
    pg.click('.doccard[data-doc="d2train"]'); pg.wait_for_timeout(400)
    ok('D: กดใบจองรถไฟ → รูป 2 ชุดในตัวดูรูป', pg.is_visible('#viewer') and pg.text_content('#vCount') == '1 / 2')
    pg.click('#vClose'); pg.wait_for_timeout(200)
    ok('D: การ์ดพาสปอร์ต/บัส (ยังไม่มี) อยู่ครบ', pg.locator('.doccard.hold').count() == 2)

    # 7) รีเฟรช — จำปลดล็อก + จำติ๊กเช็คลิสต์ + pack cache
    pg.reload(); pg.wait_for_load_state()
    pg.click('#startBtn'); pg.wait_for_timeout(300)
    ok('รีเฟรช: เข้าเมนูเลย (จำปลดล็อก)', pg.is_visible('#menu'))
    pg.click('#tileP'); pg.wait_for_timeout(300)
    ok('รีเฟรช: ติ๊กเช็คลิสต์ยังอยู่', pg.locator('.packrow input').first.is_checked())
    pg.click('#packMenuBtn'); pg.wait_for_timeout(250)
    pg.click('#tileD'); pg.wait_for_timeout(300)
    pg.click('.doccard[data-doc="d1flight"]'); pg.wait_for_timeout(400)
    try:
        pg.wait_for_function('window.__docsLoaded === true', timeout=20000)
        cached = pg.is_visible('#viewer')
    except Exception:
        cached = pg.is_visible('#viewer')
    ok('รีเฟรช: รูปจาก cache (ไม่ต้องใส่รหัสใหม่)', cached)

    # 8) โหมดข้าม → ทุกอย่างล็อก + D บังคับปลดล็อก
    pg.evaluate("indexedDB.deleteDatabase('chaokuay-docs-v05')")
    pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_load_state()
    pg.click('#startBtn'); pg.wait_for_timeout(200)
    pg.click('#skipUnlock'); pg.wait_for_timeout(300)
    ok('โหมดข้าม → เข้าเมนูได้', pg.is_visible('#menu'))
    pg.click('#tileA'); pg.wait_for_timeout(400)
    ok('แผน: รหัสยังล็อก 🔒 ทุกการ์ด', pg.locator('.daycard .bk.locked').count() >= 10)
    ok('หัวแผนบอกว่ายังล็อก', 'ยังล็อก' in pg.text_content('#homeSub'))
    pg.click('#toMenuBtn'); pg.wait_for_timeout(250)
    pg.click('#tileD'); pg.wait_for_timeout(300)
    ok('D ยังล็อก → ปุ่มกรอกรหัส', pg.is_visible('#docsUnlockBtn'))
    pg.click('#docsUnlockBtn'); pg.wait_for_timeout(250)
    pg.fill('#pwInput', PW); pg.click('#unlockBtn'); pg.wait_for_timeout(1500)
    ok('ปลดล็อกกลาง D → เลขโชว์ + กลับเมนู', pg.is_visible('#menu'))
    pg.click('#tileD'); pg.wait_for_timeout(300)
    ok('D หลังปลด: เลขจองโชว์ในการ์ด', '1622927736922035' in pg.text_content('.doccard[data-doc="d1flight"]'))
    pg.click('.doccard[data-doc="d1flight"]'); pg.wait_for_timeout(400)
    try:
        pg.wait_for_function('window.__docsLoaded === true', timeout=25000)
        d2 = pg.is_visible('#viewer')
    except Exception:
        d2 = False
    ok('D หลังปลด: กดการ์ด → รูปโผล่', d2)
    pg.click('#vClose'); pg.wait_for_timeout(200)

    # 9) มือถือ 390
    m = b.new_page(viewport={'width': 390, 'height': 844})
    m.goto(URL, wait_until='load'); m.click('#startBtn')
    m.fill('#pwInput', PW); m.click('#unlockBtn')
    m.wait_for_function('document.querySelector("#menu") && document.querySelector("#menu").hidden === false', timeout=8000)
    sw = m.evaluate('document.scrollingElement.scrollWidth')
    ok('มือถือ 390: เมนูไม่ล้น', sw <= 390, sw)
    m.click('#tileD'); m.wait_for_timeout(300)
    sw2 = m.evaluate('document.scrollingElement.scrollWidth')
    ok('มือถือ 390: หน้า D ไม่ล้น', sw2 <= 390, sw2)
    m.click('#docsMenuBtn'); m.wait_for_timeout(200)
    m.click('#tileA'); m.wait_for_timeout(300)
    sw3 = m.evaluate('document.scrollingElement.scrollWidth')
    ok('มือถือ 390: หน้าแผนไม่ล้น', sw3 <= 390, sw3)
    ok('ไม่มี JS error', not errors, errors[:3])
    b.close()
