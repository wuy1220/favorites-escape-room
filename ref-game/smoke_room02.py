# -*- coding: utf-8 -*-
"""冒烟:默认房间(Room 02)加载无错误、根节点展开、拖动组合仍工作。"""
import time
from playwright.sync_api import sync_playwright
URL = "http://127.0.0.1:8128/"
CHROME = r"C:/Users/30807/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"
errors = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page(viewport={"width": 1440, "height": 1400})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    # 走产品壳入口:隐藏 home 屏显示游戏层 + intro「进入房间」
    page.evaluate("() => { document.querySelector('.shell').style.display=''; document.getElementById('homeScreen').classList.add('hidden'); }")
    time.sleep(0.5)
    box = page.locator('#start').first.bounding_box()
    page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2); time.sleep(0.6)
    def click(sel):
        box = page.locator(sel).first.bounding_box()
        assert box, f"不可点击 {sel}"
        page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2); time.sleep(0.4)
    def visible(sel):
        return page.locator(sel).first.is_visible()
    ok_root = visible('[data-id="root"]')
    print("[{}] 首屏只有收藏室(root)".format("PASS" if ok_root else "FAIL"))
    click('[data-id="root"]')
    time.sleep(0.4)
    has_shelf = visible('[data-id="shelf"]') and visible('[data-id="desk"]') and visible('[data-id="exit"]')
    print("[{}] 点击 root 展开四空间".format("PASS" if has_shelf else "FAIL"))
    click('[data-id="shelf"]')
    time.sleep(0.4)
    # nand2tetris 拖到 NandGame(走新的拖动归位路径)
    drag_ok, restored = False, False
    try:
        sb = page.locator('[data-id="nand"]').first.bounding_box()
        db = page.locator('[data-id="tetris"]').first.bounding_box()
        assert sb and db, "拖拽端点缺失"
        sx, sy = sb["x"]+sb["width"]/2, sb["y"]+sb["height"]/2
        dx, dy = db["x"]+db["width"]/2, db["y"]+db["height"]/2
        page.mouse.move(sx, sy); page.mouse.down()
        for i in range(1, 6): page.mouse.move(sx+(dx-sx)*i/5, sy+(dy-sy)*i/5); time.sleep(0.03)
        page.mouse.up(); time.sleep(0.6)
        drag_ok = bool(page.evaluate("() => [...document.querySelectorAll('.node')].some(e=>e.className.includes('result')&&e.textContent.includes('骨架'))"))
        restored = drag_ok and bool(page.evaluate("""() => {
            const el=document.querySelector('.node[data-id=\"tetris\"]');
            return el && Math.abs(parseFloat(el.style.top)-13)<1;  /* tetris 初始 y=13% */
        }"""))
    except Exception as e:
        print("  拖动异常:", e)
    print("[{}] nand+tetris 组合出收藏骨架".format("PASS" if drag_ok else "FAIL"))
    print("[{}] 目标节点未被源节点压住(拖后归位)".format("PASS" if restored else "WARN"))
    real_errors=[e for e in errors if "Failed to load resource" not in e]
    print("[{}] 控制台错误(除 favicon): {}".format("PASS" if not real_errors else "FAIL", real_errors[:3]))
    b.close()
