# -*- coding: utf-8 -*-
"""真实 DOM 通道验证:原创关卡「深夜情报 · 熊曰」。

设计验证点(原作复盘 R1 叙事 / R3 显影 / R4 反转解码):
1. 真实素材:熊曰加密工具说明含真实算法(整体倒序)与真实字典(很2 既4 和6);
2. R3 显影:combine 铅笔+便签 -> 便签原位变身「显出字迹的情报」,密文出现;
3. R4 反转:密文『和既很』倒序为『很既和』-> 字典索引 2-4-6 -> 密码 246(直读 264 被拒);
4. 回访机制:终端/钥匙须回访容器;全程零 compiled-result- 新节点;
5. consume:钥匙开门后消失。
"""
import sys, time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8128/"
PUZZLE = r"C:\Users\30807\Documents\Codex\2026-08-20\superpowers-brainstorming-c-users-30807-codex-2\projects\favorites-escape-room\sample-puzzles\bear-code.room.json"
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

def keypad_input(page, code):
    for k in code:
        page.locator(f'#keypad [data-k="{k}"]').click(); time.sleep(0.12)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1440, "height": 1400})
        page.goto(URL, wait_until="domcontentloaded")
        wait_visible(page, "#homeScreen", "首页加载", 15000)
        page.set_input_files("#homeImportFile", PUZZLE)
        wait_visible(page, '[data-id="root"]', "导入后根节点出现", 10000)
        no_result_nodes(page, "开局")

        # 静态断言:熊曰工具说明是真实内容(含"倒序"规则与真实字典索引)
        bear_reason = page.evaluate("""() => {
            const items = window.__dbg && window.__dbg.level.items;
            return (items && items.find(i => i.id === 'bd-bear') || {}).reason || '';
        }""")
        check("熊曰说明含真实算法(整体倒序)", "倒序" in bear_reason and "呋" in bear_reason, bear_reason[-60:])
        check("熊曰说明含真实字典索引", ("很2" in bear_reason) and ("既4" in bear_reason) and ("和6" in bear_reason), "字典节选可用")

        click(page, '[data-id="root"]')
        wait_visible(page, '[data-id="compiled-item-bd-door"]', "地址栏直接可见")
        wait_visible(page, '[data-id="compiled-item-bd-note"]', "加密便签直接可见")
        wait_visible(page, '[data-id="compiled-container-fold-sec"]', "安全/工具文件夹可见")
        gone(page, '[data-id="compiled-item-bd-bear"]', "熊曰工具藏于文件夹")

        # 开文件夹 -> 熊曰工具 + 铅笔;读熊曰(算法)与便签(剧情)
        click(page, '[data-id="compiled-container-fold-sec"]')
        wait_visible(page, '[data-id="compiled-item-bd-bear"]', "开文件夹见熊曰工具")
        wait_visible(page, '[data-id="compiled-item-bd-pencil"]', "开文件夹见铅笔")
        click(page, '[data-id="compiled-item-bd-bear"]')
        no_result_nodes(page, "读熊曰")
        click(page, '[data-id="compiled-item-bd-note"]')
        no_result_nodes(page, "读便签")
        gone(page, '[data-id="compiled-item-bd-term"]', "解密终端不自动弹出(须回访)")

        # R3 显影:铅笔+便签 -> 便签原位变身「显出字迹的情报」,密文出现在详情
        drag(page, '[data-id="compiled-item-bd-pencil"]', '[data-id="compiled-item-bd-note"]')
        check("便签原位变身「显出字迹的情报」", node_name(page, '[data-id="compiled-item-bd-note"]') == "显出字迹的情报",
              node_name(page, '[data-id="compiled-item-bd-note"]'))
        no_result_nodes(page, "显影")
        # 密文必须可见:点开变身后的便签,节点详情卡应显示密文「和既很」
        click(page, '[data-id="compiled-item-bd-note"]')
        detail_txt = page.evaluate(
            "() => { const p = document.querySelector('.node-pop .np-copy'); return p ? p.textContent : ''; }"
        )
        check("显影后详情显示密文『和既很』", "和既很" in detail_txt, detail_txt[-50:])

        # 回访文件夹 -> 解密终端
        click(page, '[data-id="compiled-container-fold-sec"]')
        wait_visible(page, '[data-id="compiled-item-bd-term"]', "回访文件夹发现解密终端")

        # R4 反转:密文『和既很』倒序『很既和』-> 2-4-6;直读 264 被拒
        click(page, '[data-id="compiled-item-bd-term"]')
        wait_visible(page, '#keypadModal:not(.hidden)', "解密终端密码盘弹出(随时可用)", 5000)
        keypad_input(page, "264")
        time.sleep(0.4)
        snap = snapshot_done(page)
        check("直读密文 264 被拒(必须先倒序)", "beat-b-term" not in (snap or {}).get("clues", []), "264 不是正确密码")
        keypad_input(page, "246")
        time.sleep(0.4)
        check("解密终端原位变身「解密的情报」", node_name(page, '[data-id="compiled-item-bd-term"]') == "解密的情报",
              node_name(page, '[data-id="compiled-item-bd-term"]'))
        gone(page, '[data-id="compiled-item-bd-key"]', "钥匙不自动弹出(须回访)")
        no_result_nodes(page, "解码")
        click(page, '[data-id="compiled-container-fold-sec"]')
        wait_visible(page, '[data-id="compiled-item-bd-key"]', "回访文件夹发现钥匙")

        # 出口:钥匙+地址栏 -> 变身 + 钥匙消失;拖到出口交付
        drag(page, '[data-id="compiled-item-bd-key"]', '[data-id="compiled-item-bd-door"]')
        check("地址栏原位变身「打开的地址栏」", node_name(page, '[data-id="compiled-item-bd-door"]') == "打开的地址栏",
              node_name(page, '[data-id="compiled-item-bd-door"]'))
        gone(page, '[data-id="compiled-item-bd-key"]', "钥匙用完消失(consume)")
        no_result_nodes(page, "开地址栏")
        drag(page, '[data-id="compiled-item-bd-door"]', '[data-id="compiled-exit"]')
        time.sleep(0.4)
        click(page, '[data-id="compiled-exit"]')
        time.sleep(0.4)
        no_result_nodes(page, "通关")
        snap = snapshot_done(page)
        check("关卡通关(done=true)", bool(snap and snap.get("done")), f"clues={snap and snap.get('clues')}")
        log_all = page.evaluate("() => document.getElementById('log').innerText")
        check("日志无残余文案『认出它的真身』", "认出它的真身" not in log_all and "再仔细看" not in log_all, "编译关卡文案已清理")

        passed = sum(1 for _, ok, _ in results if ok)
        print(f"\n===== 结果: {passed}/{len(results)} 通过 =====")
        browser.close()
        if passed != len(results):
            sys.exit(1)

if __name__ == "__main__":
    main()
