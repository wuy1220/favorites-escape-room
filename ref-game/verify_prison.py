# -*- coding: utf-8 -*-
"""真实 DOM 通道验证:原作第二关「监狱」复刻是否再现原作回访机制。

核心断言(与原作 state[]+preClue 语义对齐):
1. beat 触发后,目标节点【原位变身】——名字/键更新,位置不变,不生成新节点;
2. 全程画布上不存在任何 data-id^="compiled-result-" 的新节点(旧状态不与新状态共存);
3. 解镣铐不会自动弹出书架/大铁箱/门——必须再点一次房间(回访)才发现。
"""
import sys, time, math
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8128/"
PUZZLE = r"C:\Users\30807\Documents\Codex\2026-08-20\superpowers-brainstorming-c-users-30807-codex-2\projects\favorites-escape-room\sample-puzzles\prison.room.json"
CHROME = r"C:\Users\30807\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe"

results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        raise SystemExit(f"中断于: {name}")

def wait_visible(page, sel, name, timeout=8000):
    try:
        page.wait_for_selector(sel, state="visible", timeout=timeout); check(name, True); return True
    except Exception as e:
        check(name, False, str(e)); return False

def gone(page, sel, name):
    vis = page.locator(sel).first.is_visible()
    check(name, not vis)


def dial(page, i, angle):
    svg = page.locator(f'.angle-dial[data-i="{i}"] .ad-face').first
    b = svg.bounding_box(); assert b, f"表盘 {i} 不可见"
    cx, cy = b["x"]+b["width"]/2, b["y"]+b["height"]/2
    R = b["width"]*0.38
    rad = math.radians(angle)
    page.mouse.click(cx + R*math.sin(rad), cy - R*math.cos(rad))
    time.sleep(0.25)

def settle(page):
    # 2026-08-31:节点飞入动画期间不可点击(.node.arrive pe:none),交互前等全部落定
    page.wait_for_function("() => !document.querySelector('.node.arrive')", timeout=5000)

def click(page, sel):
    settle(page)
    box = page.locator(sel).first.bounding_box(); assert box, f"不可点击 {sel}"
    page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2); time.sleep(0.9)

def drag(page, src_sel, dst_sel):
    settle(page)
    src = page.locator(src_sel).first; dst = page.locator(dst_sel).first
    sb = src.bounding_box(); db = dst.bounding_box(); assert sb and db, f"不可拖拽 {src_sel}->{dst_sel}"
    sx, sy = sb["x"]+sb["width"]/2, sb["y"]+sb["height"]/2
    dx, dy = db["x"]+db["width"]/2, db["y"]+db["height"]/2
    page.mouse.move(sx, sy); page.mouse.down()
    for i in range(1, 6):
        page.mouse.move(sx+(dx-sx)*i/5, sy+(dy-sy)*i/5); time.sleep(0.03)
    page.mouse.up(); time.sleep(0.4)

def node_name(page, sel):
    return page.locator(sel + " .name").first.inner_text()

def no_result_nodes(page, step):
    count = page.evaluate("() => document.querySelectorAll('[data-id^=\"compiled-result-\"]').length")
    check(f"[{step}] 画布无新节点弹出(回访机制)", count == 0, f"compiled-result- 节点数={count}")

def snapshot_done(page):
    return page.evaluate("() => (window.__favoriteRoomRuntime && window.__favoriteRoomRuntime.snapshot()) || null")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1440, "height": 1400})
        page.goto(URL, wait_until="domcontentloaded")
        wait_visible(page, "#homeScreen", "首页加载", 15000)
        page.set_input_files("#homeImportFile", PUZZLE)
        wait_visible(page, '[data-id="root"]', "导入后根节点出现", 10000)
        no_result_nodes(page, "开局")

        # 开始:散落物件可见,书架/大铁箱/门不存在(原作:它们要等回访)
        click(page, '[data-id="root"]')
        wait_visible(page, '[data-id="compiled-item-pr-pipe"]', "散落物件(排水管)直接可见")
        gone(page, '[data-id="compiled-container-shelf"]', "书架初始不存在(等回访)")
        gone(page, '[data-id="compiled-container-door"]', "门初始不存在(等回访)")

        # 开柜子 -> 转盘锁;锯子仍藏
        gone(page, '[data-id="compiled-item-pr-dial"]', "转盘锁初始隐藏")
        click(page, '[data-id="compiled-container-cabinet"]')
        wait_visible(page, '[data-id="compiled-item-pr-dial"]', "开柜后转盘锁可见")

        # 角度旋钮 90°/180°:转盘锁原位变身为「打开的转盘锁」;锯子不自动弹出
        click(page, '[data-id="compiled-item-pr-dial"]')
        wait_visible(page, '#angleModal:not(.hidden)', "角度旋钮弹出", 5000)
        dial(page, 0, 90); dial(page, 1, 180)
        time.sleep(0.4)
        check("转盘锁原位变身", node_name(page, '[data-id="compiled-item-pr-dial"]') == "打开的转盘锁",
              node_name(page, '[data-id="compiled-item-pr-dial"]'))
        gone(page, '[data-id="compiled-item-pr-saw"]', "解锁后锯子不自动弹出(须回访)")
        no_result_nodes(page, "转盘锁")

        # 回访柜子 -> 发现锯子
        click(page, '[data-id="compiled-container-cabinet"]')
        wait_visible(page, '[data-id="compiled-item-pr-saw"]', "回访柜子发现锯子")

        # 组合链:锯子+排水管 -> 排水管原位变身「棍子」;棍子+钥匙 -> 钥匙变身;钥匙+镣铐 -> 镣铐变身
        drag(page, '[data-id="compiled-item-pr-saw"]', '[data-id="compiled-item-pr-pipe"]')
        check("排水管原位变身「棍子」", node_name(page, '[data-id="compiled-item-pr-pipe"]') == "棍子",
              node_name(page, '[data-id="compiled-item-pr-pipe"]'))
        no_result_nodes(page, "锯管")
        drag(page, '[data-id="compiled-item-pr-pipe"]', '[data-id="compiled-item-pr-key"]')
        check("钥匙原位变身「钥匙」", node_name(page, '[data-id="compiled-item-pr-key"]') == "钥匙",
              node_name(page, '[data-id="compiled-item-pr-key"]'))
        no_result_nodes(page, "勾钥匙")
        drag(page, '[data-id="compiled-item-pr-key"]', '[data-id="compiled-item-pr-shackle"]')
        check("镣铐原位变身「解开的镣铐」", node_name(page, '[data-id="compiled-item-pr-shackle"]') == "解开的镣铐",
              node_name(page, '[data-id="compiled-item-pr-shackle"]'))
        no_result_nodes(page, "解镣铐")

        # 核心回访断言:解镣铐后「环顾四周」才发现 书架/大铁箱/门
        gone(page, '[data-id="compiled-container-shelf"]', "解镣铐后书架仍未自动出现")
        page.locator('#revisitRoom').click(); time.sleep(0.4)
        wait_visible(page, '[data-id="compiled-container-shelf"]', "回访房间发现书架")
        wait_visible(page, '[data-id="compiled-container-chest"]', "回访房间发现大铁箱")
        wait_visible(page, '[data-id="compiled-container-door"]', "回访房间发现门")
        no_result_nodes(page, "回访房间")

        # 回访时钟发现电池;开书架发现笔记+日记
        click(page, '[data-id="compiled-container-clock"]')
        wait_visible(page, '[data-id="compiled-item-pr-battery"]', "回访时钟发现电池")
        click(page, '[data-id="compiled-container-shelf"]')
        wait_visible(page, '[data-id="compiled-item-pr-note"]', "开书架发现笔记")
        wait_visible(page, '[data-id="compiled-item-pr-diary"]', "开书架发现日记本")

        # 电池+电报机 -> 电报机原位变身「通电的电报机」;读笔记和日记;摩斯输入 371 -> 电报机再变身
        drag(page, '[data-id="compiled-item-pr-battery"]', '[data-id="compiled-item-pr-telegraph"]')
        check("电报机原位变身「通电的电报机」", node_name(page, '[data-id="compiled-item-pr-telegraph"]') == "通电的电报机",
              node_name(page, '[data-id="compiled-item-pr-telegraph"]'))
        no_result_nodes(page, "装电池")
        click(page, '[data-id="compiled-item-pr-note"]')
        click(page, '[data-id="compiled-item-pr-diary"]')
        click(page, '[data-id="compiled-item-pr-telegraph"]')
        wait_visible(page, '#morseModal:not(.hidden)', "摩斯面板弹出(点击变身后的电报机)", 5000)
        for ch in "...--/--.../.----":
            if ch == '.': page.locator('#morseDot').click()
            elif ch == '-': page.locator('#morseDash').click()
            elif ch == '/': page.locator('#morseSlash').click()
            time.sleep(0.05)
        page.locator('#morseEnter').click(); time.sleep(0.3)
        check("电报机再次原位变身「记下密码的电报机」", node_name(page, '[data-id="compiled-item-pr-telegraph"]') == "记下密码的电报机",
              node_name(page, '[data-id="compiled-item-pr-telegraph"]'))
        no_result_nodes(page, "摩斯")

        # 开大铁箱 -> 密码锁 685 -> 密码锁原位变身;手指就绪;回访箱子发现手指
        click(page, '[data-id="compiled-container-chest"]')
        click(page, '[data-id="compiled-item-pr-chest"]')
        wait_visible(page, '#keypadModal:not(.hidden)', "密码盘弹出", 5000)
        for k in ("6", "8", "5"):
            page.locator(f'#keypad [data-k="{k}"]').click(); time.sleep(0.12)
        time.sleep(0.4)
        check("密码锁原位变身「打开的密码锁」", node_name(page, '[data-id="compiled-item-pr-chest"]') == "打开的密码锁",
              node_name(page, '[data-id="compiled-item-pr-chest"]'))
        gone(page, '[data-id="compiled-item-pr-finger"]', "开箱后手指不自动弹出(须回访)")
        no_result_nodes(page, "密码")
        click(page, '[data-id="compiled-container-chest"]')
        wait_visible(page, '[data-id="compiled-item-pr-finger"]', "回访铁箱发现手指")

        # 开门 -> 指纹锁;手指+指纹锁 -> 指纹锁原位变身「解锁的指纹锁」;拖到出口交付
        click(page, '[data-id="compiled-container-door"]')
        wait_visible(page, '[data-id="compiled-item-pr-fp-lock"]', "开门见指纹锁")
        drag(page, '[data-id="compiled-item-pr-finger"]', '[data-id="compiled-item-pr-fp-lock"]')
        check("指纹锁原位变身「解锁的指纹锁」", node_name(page, '[data-id="compiled-item-pr-fp-lock"]') == "解锁的指纹锁",
              node_name(page, '[data-id="compiled-item-pr-fp-lock"]'))
        no_result_nodes(page, "指纹锁")
        drag(page, '[data-id="compiled-item-pr-fp-lock"]', '[data-id="compiled-exit"]')
        time.sleep(0.4)
        click(page, '[data-id="compiled-exit"]')
        time.sleep(0.4)
        no_result_nodes(page, "通关")
        snap = snapshot_done(page)
        check("关卡通关(done=true)", bool(snap and snap.get("done")), f"clues={snap and snap.get('clues')}")

        passed = sum(1 for _, ok, _ in results if ok)
        print(f"\n===== 结果: {passed}/{len(results)} 通过 =====")
        browser.close()
        if passed != len(results):
            sys.exit(1)

if __name__ == "__main__":
    main()
