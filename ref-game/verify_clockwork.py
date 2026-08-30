# -*- coding: utf-8 -*-
"""真实 DOM 通道验证:原创关卡「钟表铺」。

核心断言(复刻经验 + 设计原则):
1. beat 触发后目标节点【原位变身】,全程零 compiled-result- 新节点;
2. 非线性:角度线索在钟面磨损(环境),不读修钟记录也能拨指针;记录与角度两条支线互不依赖;
3. 修钟记录只承载"配件在抽屉里"这一条环境看不到的信息,不含角度/密码;
4. 消耗品:发条接完钟摆后消失(consume),不可再拖;
5. 回访机制:断钟摆/发条/金钥匙须回访所属容器才出现;点根节点只现形根的直接子节点,不越级。
"""
import sys, time, math
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8128/"
PUZZLE = r"C:\Users\30807\Documents\Codex\2026-08-20\superpowers-brainstorming-c-users-30807-codex-2\projects\favorites-escape-room\sample-puzzles\clockwork.room.json"
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

def click(page, sel):
    box = page.locator(sel).first.bounding_box(); assert box, f"不可点击 {sel}"
    page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2); time.sleep(0.9)

def drag(page, src_sel, dst_sel):
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

        # 开局:挂钟容器/店门直接可见;挂钟物件藏于挂钟内
        click(page, '[data-id="root"]')
        wait_visible(page, '[data-id="compiled-container-wallclock"]', "挂钟容器直接可见")
        wait_visible(page, '[data-id="compiled-item-cw-door"]', "店门直接可见")
        gone(page, '[data-id="compiled-item-cw-clock"]', "挂钟物件初始藏于挂钟内")
        gone(page, '[data-id="compiled-item-cw-manual"]', "修钟记录初始隐藏(在容器里)")

        # 交互道具随时可用:未完成任何前置,展柜密码锁也能点开(答案正确才解锁)
        click(page, '[data-id="compiled-container-showcase"]')
        wait_visible(page, '[data-id="compiled-item-cw-lock"]', "开局开展柜见密码锁")
        click(page, '[data-id="compiled-item-cw-lock"]')
        wait_visible(page, '#keypadModal:not(.hidden)', "前置未完成时密码盘也能弹出(随时可用)", 5000)
        page.locator('#keyCancel').click(); time.sleep(0.3)

        # 非线性①:不读记录,先开挂钟拨指针——角度线索在钟面磨损(环境),不依赖记录
        click(page, '[data-id="compiled-container-wallclock"]')
        wait_visible(page, '[data-id="compiled-item-cw-clock"]', "开挂钟见挂钟")
        click(page, '[data-id="compiled-item-cw-clock"]')
        wait_visible(page, '#angleModal:not(.hidden)', "角度旋钮弹出", 5000)
        dial(page, 0, 90); dial(page, 1, 180)
        time.sleep(0.4)
        check("未读记录也能拨指针(非线性)", "beat-b-read" not in (snapshot_done(page) or {}).get("clues", []),
              "b-read 未完成时 b-angle 已生效")
        check("挂钟原位变身「打开后盖的挂钟」", node_name(page, '[data-id="compiled-item-cw-clock"]') == "打开后盖的挂钟",
              node_name(page, '[data-id="compiled-item-cw-clock"]'))
        gone(page, '[data-id="compiled-item-cw-pend"]', "开后盖后断钟摆不自动弹出(须回访挂钟)")
        no_result_nodes(page, "开后盖")
        click(page, '[data-id="root"]')
        time.sleep(0.4)
        # 精确语义(2026-08-31):点根节点只现形 root 的**直接**就绪子节点;
        # 断钟摆是挂钟容器的子节点,由回访挂钟显形,root 无权越级
        gone(page, '[data-id="compiled-item-cw-pend"]', "点根节点不越级显形(断钟摆仍归挂钟管)")
        click(page, '[data-id="compiled-container-wallclock"]')
        wait_visible(page, '[data-id="compiled-item-cw-pend"]', "回访挂钟发现断钟摆")

        # 非线性②:记录与角度互不依赖——现在读记录,拿抽屉里的发条
        click(page, '[data-id="compiled-container-workbench"]')
        wait_visible(page, '[data-id="compiled-item-cw-manual"]', "开工作台见修钟记录")
        gone(page, '[data-id="compiled-item-cw-spring"]', "发条初始隐藏")
        manual_reason = page.evaluate("""() => (window.__dbg && window.__dbg.level.items.find(i=>i.id==='cw-manual')||{}).reason || ''""")
        check("修钟记录只指配件位置,不给角度/密码", ("抽屉" in manual_reason) and ("90" not in manual_reason) and ("180" not in manual_reason) and ("4:35" not in manual_reason) and ("密码" not in manual_reason), manual_reason[-60:])
        click(page, '[data-id="compiled-item-cw-manual"]')
        no_result_nodes(page, "读记录")
        click(page, '[data-id="compiled-container-workbench"]')
        wait_visible(page, '[data-id="compiled-item-cw-spring"]', "回访工作台发现发条")

        # 组合链:发条+断钟摆 -> 钟摆变身「修好的钟摆」;发条用完消失(consume)
        drag(page, '[data-id="compiled-item-cw-spring"]', '[data-id="compiled-item-cw-pend"]')
        check("断钟摆原位变身「修好的钟摆」", node_name(page, '[data-id="compiled-item-cw-pend"]') == "修好的钟摆",
              node_name(page, '[data-id="compiled-item-cw-pend"]'))
        gone(page, '[data-id="compiled-item-cw-spring"]', "发条用完消失(consume)")
        inv_txt = page.evaluate("() => document.getElementById('inventory') ? document.getElementById('inventory').innerText : ''")
        check("已发现面板不再列出已消耗的发条", "生锈的发条" not in inv_txt, inv_txt.replace("\n"," | "))
        no_result_nodes(page, "接钟摆")
        drag(page, '[data-id="compiled-item-cw-pend"]', '[data-id="compiled-item-cw-clock"]')
        check("挂钟再次原位变身「走动的挂钟」", node_name(page, '[data-id="compiled-item-cw-clock"]') == "走动的挂钟",
              node_name(page, '[data-id="compiled-item-cw-clock"]'))
        no_result_nodes(page, "装回钟摆")
        logtxt = page.evaluate("() => document.getElementById('log').innerText")
        check("装回钟摆后钟面 4:35 出现在日志", "4:35" in logtxt, (logtxt.splitlines() or ["?"])[-1])

        # 展柜密码 435 -> 密码锁原位变身;金钥匙待回访
        click(page, '[data-id="compiled-container-showcase"]')
        wait_visible(page, '[data-id="compiled-item-cw-lock"]', "开展柜见密码锁")
        click(page, '[data-id="compiled-item-cw-lock"]')
        wait_visible(page, '#keypadModal:not(.hidden)', "密码盘弹出", 5000)
        for k in ("4", "3", "5"):
            page.locator(f'#keypad [data-k="{k}"]').click(); time.sleep(0.12)
        time.sleep(0.4)
        check("密码锁原位变身「打开的密码锁」", node_name(page, '[data-id="compiled-item-cw-lock"]') == "打开的密码锁",
              node_name(page, '[data-id="compiled-item-cw-lock"]'))
        gone(page, '[data-id="compiled-item-cw-gkey"]', "开柜后金钥匙不自动弹出(须回访)")
        no_result_nodes(page, "开密码")
        click(page, '[data-id="compiled-container-showcase"]')
        wait_visible(page, '[data-id="compiled-item-cw-gkey"]', "回访展柜发现金钥匙")

        # 金钥匙+店门 -> 店门原位变身「打开的门」;拖到出口交付
        drag(page, '[data-id="compiled-item-cw-gkey"]', '[data-id="compiled-item-cw-door"]')
        check("店门原位变身「打开的门」", node_name(page, '[data-id="compiled-item-cw-door"]') == "打开的门",
              node_name(page, '[data-id="compiled-item-cw-door"]'))
        no_result_nodes(page, "开门")
        drag(page, '[data-id="compiled-item-cw-door"]', '[data-id="compiled-exit"]')
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
