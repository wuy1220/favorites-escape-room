# -*- coding: utf-8 -*-
"""回归验证:引擎改为「节点原位变身」后,原有手写样本 watchman 仍能通关。

断言对齐新机制(原作 state[]+preClue 语义):
- beat 触发后目标节点原位变身(名字更新),画布不出现 compiled-result- 新节点;
- 变身后的产物节点跨场景保留(跟随玩家),可继续组合/交付。
"""
import sys, time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8128/"
PUZZLE = r"C:\Users\30807\Documents\Codex\2026-08-20\superpowers-brainstorming-c-users-30807-codex-2\projects\favorites-escape-room\sample-puzzles\watchman.json"
CHROME = r"C:\Users\30807\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe"

results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        raise SystemExit(f"中断于: {name}")

def wait_visible(page, sel, name, timeout=8000):
    try:
        page.wait_for_selector(sel, state="visible", timeout=timeout); check(name, True); return
    except Exception as e:
        check(name, False, str(e))

def click(page, sel):
    box = page.locator(sel).first.bounding_box()
    assert box, f"不可点击 {sel}"
    cx = box["x"] + box["width"]/2
    cy = box["y"] + box["height"]/2
    page.mouse.click(cx, cy); time.sleep(0.4)

def drag(page, src_sel, dst_sel):
    src = page.locator(src_sel).first; dst = page.locator(dst_sel).first
    sb = src.bounding_box(); db = dst.bounding_box()
    assert sb and db, f"不可拖拽 {src_sel} -> {dst_sel}"
    sx, sy = sb["x"]+sb["width"]/2, sb["y"]+sb["height"]/2
    dx, dy = db["x"]+db["width"]/2, db["y"]+db["height"]/2
    page.mouse.move(sx, sy); page.mouse.down()
    for i in range(1, 6):
        page.mouse.move(sx+(dx-sx)*i/5, sy+(dy-sy)*i/5); time.sleep(0.03)
    page.mouse.up(); time.sleep(0.5)

def node_name(page, sel):
    return page.locator(sel + " .name").first.inner_text()

def no_result_nodes(page, step):
    count = page.evaluate("() => document.querySelectorAll('[data-id^=\"compiled-result-\"]').length")
    check(f"[{step}] 画布无新节点弹出", count == 0, f"compiled-result- 节点数={count}")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 2000, "height": 1400})
        page.goto(URL, wait_until="domcontentloaded")
        wait_visible(page, "#homeScreen", "首页加载", 15000)
        page.set_input_files("#homeImportFile", PUZZLE)
        wait_visible(page, '[data-id="root"]', "根节点出现", 10000)
        click(page, '[data-id="root"]')
        no_result_nodes(page, "开局")

        # scene-1 值班台: 检查三件 + 组合 + 顺序
        wait_visible(page, '[data-id="compiled-item-watch-chen"]', "场景1:值班证陈可见")
        click(page, '[data-id="compiled-item-watch-chen"]')
        click(page, '[data-id="compiled-item-watch-wang"]')
        click(page, '[data-id="compiled-item-watch-lock"]')
        drag(page, '[data-id="compiled-item-watch-chen"]', '[data-id="compiled-item-watch-wang"]')
        check("王的值班证原位变身「核对过的名单」",
              node_name(page, '[data-id="compiled-item-watch-wang"]') == "核对过的名单",
              node_name(page, '[data-id="compiled-item-watch-wang"]'))
        no_result_nodes(page, "核对名单")
        # sequence: 依次点 chen 再 wang -> 王再变身为「已输入的交接顺序」
        click(page, '[data-id="compiled-item-watch-chen"]')
        click(page, '[data-id="compiled-item-watch-wang"]')
        check("王的节点再变身「已输入的交接顺序」",
              node_name(page, '[data-id="compiled-item-watch-wang"]') == "已输入的交接顺序",
              node_name(page, '[data-id="compiled-item-watch-wang"]'))
        no_result_nodes(page, "交接顺序")

        # scene-2 门房: 检查钥匙盒 + 把核对结果交给门房 -> 收纳盒原位变身「门房钥匙」
        wait_visible(page, '[data-id="compiled-item-watch-box"]', "场景2:钥匙盒可见")
        click(page, '[data-id="compiled-item-watch-box"]')
        drag(page, '[data-id="compiled-item-watch-wang"]', '[data-id="compiled-item-watch-box"]')
        check("收纳盒原位变身「门房钥匙」",
              node_name(page, '[data-id="compiled-item-watch-box"]') == "门房钥匙",
              node_name(page, '[data-id="compiled-item-watch-box"]'))
        no_result_nodes(page, "门房")

        # scene-3 墙角: 组合两产物 -> 收纳盒再变身为「出口钥匙」;保险柜不自动弹出,须回访
        wait_visible(page, '[data-id="compiled-scene-fixed-scene-3"]', "场景3:墙角亮起", 8000)
        # 变身节点跨场景保留:王(顺序)+盒(门房钥匙)仍可见可拖
        check("王(已变身)跨场景保留", page.locator('[data-id="compiled-item-watch-wang"]').first.is_visible())
        check("盒(门房钥匙)跨场景保留", page.locator('[data-id="compiled-item-watch-box"]').first.is_visible())
        drag(page, '[data-id="compiled-item-watch-wang"]', '[data-id="compiled-item-watch-box"]')
        check("收纳盒再变身「出口钥匙」",
              node_name(page, '[data-id="compiled-item-watch-box"]') == "出口钥匙",
              node_name(page, '[data-id="compiled-item-watch-box"]'))
        vault_now = page.locator('[data-id="compiled-item-watch-vault"]').first.is_visible()
        check("组合后保险柜不自动弹出(须回访)", not vault_now)
        page.locator('#revisitRoom').click(); time.sleep(0.4)
        wait_visible(page, '[data-id="compiled-item-watch-vault"]', "回看墙角:保险柜显形")
        click(page, '[data-id="compiled-item-watch-vault"]')
        no_result_nodes(page, "保险柜")
        # 交付:把出口钥匙(收纳盒变身节点)交给出口
        drag(page, '[data-id="compiled-item-watch-box"]', '[data-id="compiled-exit"]')
        time.sleep(0.5)
        click(page, '[data-id="compiled-exit"]')
        time.sleep(0.5)
        no_result_nodes(page, "通关")
        snap = page.evaluate("() => (window.__favoriteRoomRuntime && window.__favoriteRoomRuntime.snapshot()) || null")
        done = bool(snap and snap.get("done"))
        check("watchman 通关(done=true)", done, f"clues={snap and snap.get('clues')}")

        passed = sum(1 for _, ok, _ in results if ok)
        print(f"\n===== watchman 回归: {passed}/{len(results)} 通过 =====")
        browser.close()
        if passed != len(results):
            sys.exit(1)

if __name__ == "__main__":
    main()
