# -*- coding: utf-8 -*-
"""UI 截图工具:对全部界面/弹窗截屏,用于 UI 重设计前后对比与视觉验收(零配额,不触 LLM)。
用法: python ref-game/ui_shots.py <输出目录>
截图清单:主页 / legacy 房间+intro / 样本关卡入口与节点观察 / 全部弹窗静态壳。"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8128/"
CHROME = r"C:/Users/30807/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"

out = sys.argv[1] if len(sys.argv) > 1 else "ref-game/shots"
os.makedirs(out, exist_ok=True)


def snap(page, name):
    time.sleep(0.4)  # 等 opacity 过渡/入场动画到稳定态,避免半透明叠影
    path = os.path.join(out, name + ".png")
    page.screenshot(path=path)
    print("[shot]", path)


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page(viewport={"width": 1440, "height": 960})
    page.on("pageerror", lambda e: print("[pageerror]", str(e)[:160]))
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    snap(page, "01-home")

    # legacy 路径:显示游戏壳 + intro 弹窗(boot 的 hideLegacy 会隐藏 intro,手动恢复)
    page.evaluate(
        "() => { document.querySelector('.shell').style.display='';"
        " document.getElementById('homeScreen').classList.add('hidden');"
        " document.getElementById('intro').classList.remove('hidden'); }"
    )
    snap(page, "02-legacy-intro")
    box = page.locator("#start").first.bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    time.sleep(0.8)
    snap(page, "03-legacy-room")
    # legacy 弹窗壳:密码盘 / QTE / 结局
    page.evaluate("() => document.getElementById('keypadModal').classList.remove('hidden')")
    snap(page, "04-modal-keypad-legacy")
    page.evaluate("() => document.getElementById('keypadModal').classList.add('hidden')")
    page.evaluate("() => document.getElementById('qteModal').classList.remove('hidden')")
    snap(page, "05-modal-qte")
    page.evaluate("() => document.getElementById('qteModal').classList.add('hidden')")
    page.evaluate("() => document.getElementById('endingModal').classList.remove('hidden')")
    snap(page, "06-modal-ending")
    page.evaluate("() => document.getElementById('endingModal').classList.add('hidden')")

    # 回主页,载入固定样本(watchman)进入生成关卡界面
    page.evaluate(
        "() => { document.querySelector('.shell').style.display='none';"
        " document.getElementById('homeScreen').classList.remove('hidden'); }"
    )
    time.sleep(0.4)
    page.click("#homeTutorial")
    try:
        page.wait_for_selector("#gameToolbar:not([hidden])", timeout=20000)
    except Exception:
        print("[diag] status:", page.evaluate("() => document.getElementById('homeStatus').textContent"))
        print("[diag] toolbar hidden:", page.evaluate("() => document.getElementById('gameToolbar').hasAttribute('hidden')"))
        print("[diag] console errors:", page.evaluate("() => window.__errs && window.__errs.length"))
        raise
    time.sleep(1.5)
    snap(page, "07-game-entry")
    # 点第一个可交互节点,让观察窗/日志出现内容
    try:
        page.wait_for_selector(".node", timeout=8000)
        box = page.locator(".node").first.bounding_box()
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        time.sleep(0.8)
        snap(page, "08-game-inspect")
    except Exception as e:
        print("[warn] 节点点击失败:", e)

    # 引擎机关弹窗壳:ensure* 是 IIFE 私有函数,未触发机关时弹窗不存在/按键区未填。
    # keypad 用与 engine.ensureKeypad 相同的 DOM 补齐按键后再截;angle/morse 动态创建,存在才截。
    page.evaluate(
        "() => { const kp = document.getElementById('keypad');"
        " if (kp && !kp.dataset.ready) { kp.dataset.ready = '1';"
        " kp.innerHTML = ['1','2','3','4','5','6','7','8','9','0']"
        ".map(d => '<button type=\"button\" data-k=\"' + d + '\">' + d + '</button>').join(''); } }"
    )
    for mid in ("keypadModal", "angleModal", "morseModal"):
        if page.locator("#" + mid).count():
            page.evaluate(
                f"() => document.getElementById('{mid}').classList.remove('hidden')"
            )
            snap(page, "09-modal-" + mid.replace("Modal", "").lower())
            page.evaluate(f"() => document.getElementById('{mid}').classList.add('hidden')")
        else:
            print("[skip] #" + mid, "未挂载(需真实机关流触发)")

    # 命名弹窗:静态壳没有真实 GLM 候选,注入与 renderNameCandidates 同构的假候选验证视觉
    page.evaluate(
        "() => { const box = document.getElementById('nameCandidates');"
        " box.innerHTML = ['直白式标题','隐喻式标题','意识流式标题']"
        ".map(t => '<button type=\"button\" class=\"window-card\"><strong>' + t + '</strong>"
        "<small>候选标题 · 假数据(截图壳注入)</small></button>').join(''); }"
    )
    for mid, name in (("namingModal", "12-modal-naming"),
                      ("importModal", "13-modal-import"),
                      ("cleanModal", "14-modal-clean")):
        if page.locator("#" + mid).count():
            page.evaluate(f"() => document.getElementById('{mid}').classList.remove('hidden')")
            snap(page, name)
            page.evaluate(f"() => document.getElementById('{mid}').classList.add('hidden')")
        else:
            print("[skip] #" + mid, "不存在")

    # 场景分区布局(2026-08-29 结构性重设计):导入 prison(5 容器)展开后的分区舞台
    page2 = b.new_page(viewport={"width": 1440, "height": 960})
    page2.goto(URL, wait_until="domcontentloaded")
    page2.wait_for_selector("#homeScreen", timeout=15000)
    page2.set_input_files("#homeImportFile", "sample-puzzles/prison.room.json")
    page2.wait_for_selector("[data-id='root']", timeout=15000)
    box = page2.locator("[data-id='root']").first.bounding_box()
    page2.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    time.sleep(1.2)
    snap(page2, "15-board-prison")
    page2.close()

    # 移动端视口(阶段三):390x844 主页 / 游戏开抽屉
    m = b.new_page(viewport={"width": 390, "height": 844})
    m.goto(URL, wait_until="domcontentloaded")
    m.wait_for_selector("#homeScreen", timeout=15000)
    time.sleep(0.8)
    snap(m, "16-mobile-home")
    m.click("#homeTutorial")
    m.wait_for_selector("#gameToolbar:not([hidden])", timeout=20000)
    time.sleep(1.0)
    box = m.locator("[data-id='root']").first.bounding_box()
    m.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    time.sleep(1.2)
    snap(m, "17-mobile-game")
    m.evaluate("() => window.__showHints && window.__showHints()")
    time.sleep(0.6)
    snap(m, "18-mobile-drawer")
    m.close()
    b.close()
print("done:", len(os.listdir(out)), "shots in", out)
