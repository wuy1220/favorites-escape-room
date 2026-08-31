# -*- coding: utf-8 -*-
"""真实 DOM 通道验证:原创关卡「书签之屋」(真实书签素材 + 可旋转表盘 UI)。

设计验证点:
1. 三支线并行无前置:看计算器(486) / 读红石电路(300/240/180) / 读假名表(从右往左),任意顺序;
2. 表盘 UI:不显示目标角度(防剧透),显示旋钮名(红线/黄线/蓝线),点按/拖拽旋转、吸附到档位;
3. 密码不是直给:屏幕 486 → 假名表"从右往左" → 684;先输 486 被拒;
4. 回访机制:假名表/登录界面/钥匙均须回访具体容器才出现;全程零 compiled-result- 新节点;
5. consume:钥匙开门后消失。
"""
from pathlib import Path
import sys, time, math
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8128/"
PUZZLE = str(Path(__file__).resolve().parents[1] / "sample-puzzles" / "bookmark-room.room.json")
CHROME = None

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

def dial(page, i, angle):
    """点按表盘上 angle° 的位置(0°=12点,顺时针)"""
    svg = page.locator(f'.angle-dial[data-i="{i}"] .ad-face').first
    b = svg.bounding_box(); assert b, f"表盘 {i} 不可见"
    cx, cy = b["x"]+b["width"]/2, b["y"]+b["height"]/2
    R = b["width"]*0.38
    rad = math.radians(angle)
    page.mouse.click(cx + R*math.sin(rad), cy - R*math.cos(rad))
    time.sleep(0.25)

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

        click(page, '[data-id="root"]')
        wait_visible(page, '[data-id="compiled-item-bk-bar"]', "地址栏直接可见")
        wait_visible(page, '[data-id="compiled-container-fold-dev"]', "开发/技术文件夹可见")
        gone(page, '[data-id="compiled-item-bk-nand"]', "NandGame 藏于文件夹")
        gone(page, '[data-id="compiled-item-bk-kana"]', "假名表初始隐藏")

        # 支线A:开开发文件夹 -> 计算器屏幕 486;红石电路笔记直接可见(角度线索道具)
        click(page, '[data-id="compiled-container-fold-dev"]')
        wait_visible(page, '[data-id="compiled-item-bk-991"]', "开文件夹见计算器")
        wait_visible(page, '[data-id="compiled-item-bk-wiring"]', "红石电路笔记可见(角度线索道具)")
        click(page, '[data-id="compiled-item-bk-991"]')
        no_result_nodes(page, "看计算器")

        # 支线B:读红石电路笔记 -> 三根线角度线索(环境看不出的信息由道具揭示)
        click(page, '[data-id="compiled-item-bk-wiring"]')
        no_result_nodes(page, "读红石电路")

        # 支线C:读假名表(回访日语文件夹) -> 从右往左
        click(page, '[data-id="compiled-container-fold-jp"]')
        wait_visible(page, '[data-id="compiled-item-bk-kana"]', "回访日语文件夹发现假名表")
        click(page, '[data-id="compiled-item-bk-kana"]')
        no_result_nodes(page, "读假名表")

        # 接线:表盘 UI 不剧透(无"目标"字样)、显示旋钮名;点按表盘 300/240/180 -> 主机原位变身
        click(page, '[data-id="compiled-container-fold-dev"]')
        click(page, '[data-id="compiled-item-bk-nand"]')
        wait_visible(page, '#angleModal:not(.hidden)', "角度表盘弹出", 5000)
        modal_txt = page.evaluate("() => document.getElementById('angleModal').innerText")
        check("表盘不显示目标角度(防剧透)", "目标" not in modal_txt, "无『目标 X°』字样")
        check("表盘显示旋钮名(红线/黄线/蓝线)", ("红线" in modal_txt) and ("黄线" in modal_txt) and ("蓝线" in modal_txt),
              "旋钮名可辨识")
        dial(page, 0, 300); dial(page, 1, 240); dial(page, 2, 180)
        time.sleep(0.4)
        check("NandGame 原位变身「接好线的电脑」", node_name(page, '[data-id="compiled-item-bk-nand"]') == "接好线的电脑",
              node_name(page, '[data-id="compiled-item-bk-nand"]'))
        gone(page, '[data-id="compiled-item-bk-login"]', "供电后登录界面不自动弹出(须回访)")
        no_result_nodes(page, "接线")
        click(page, '[data-id="compiled-container-fold-dev"]')
        wait_visible(page, '[data-id="compiled-item-bk-login"]', "回访文件夹发现登录界面")

        # 汇聚:登录界面——先试屏幕直读的 486 被拒,再输 684 成功
        click(page, '[data-id="compiled-item-bk-login"]')
        wait_visible(page, '#keypadModal:not(.hidden)', "密码盘弹出(登录界面随时可用)", 5000)
        keypad_input(page, "486")
        time.sleep(0.4)
        snap = snapshot_done(page)
        check("屏幕直读的 486 被拒(必须按假名表读法转换)", "beat-b-login" not in (snap or {}).get("clues", []), "486 不是正确密码")
        keypad_input(page, "684")
        time.sleep(0.4)
        check("登录界面原位变身「登录成功的电脑」", node_name(page, '[data-id="compiled-item-bk-login"]') == "登录成功的电脑",
              node_name(page, '[data-id="compiled-item-bk-login"]'))
        gone(page, '[data-id="compiled-item-bk-key"]', "钥匙不自动弹出(须回访)")
        no_result_nodes(page, "登录")
        click(page, '[data-id="compiled-container-fold-dev"]')
        wait_visible(page, '[data-id="compiled-item-bk-key"]', "回访文件夹发现钥匙")

        # 出口:钥匙+地址栏 -> 变身 + 钥匙消失;拖到出口交付
        drag(page, '[data-id="compiled-item-bk-key"]', '[data-id="compiled-item-bk-bar"]')
        check("地址栏原位变身「打开的地址栏」", node_name(page, '[data-id="compiled-item-bk-bar"]') == "打开的地址栏",
              node_name(page, '[data-id="compiled-item-bk-bar"]'))
        gone(page, '[data-id="compiled-item-bk-key"]', "钥匙用完消失(consume)")
        no_result_nodes(page, "开地址栏")
        drag(page, '[data-id="compiled-item-bk-bar"]', '[data-id="compiled-exit"]')
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
