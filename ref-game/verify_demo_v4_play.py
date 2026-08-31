# -*- coding: utf-8 -*-
"""三关 v4 真实 DOM 实玩:导入 → 点击/拖拽/输密码 → 通关(done=true)。

覆盖全部三种理解动作:
- A 计量:开柜→读档案/手册→装卡带→数字锁 1046→数字锁 416→投递光碟
- B 语义:开夹→读卡/规则→文字锁 "your thinking"→读算法卡→文字锁 "动画图解"→藏书票上桌→交付
- C 排序:推门→读规则/书脊→sequence 排架→借阅章盖章→交付提货单
同时验证防自泄漏的镜像面:错误答案必须被拒(A 先输 4160 再输对)。
"""
import sys
import time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8128/"
ROOT = r"C:\Users\30807\Documents\Codex\2026-08-20\superpowers-brainstorming-c-users-30807-codex-2\projects\favorites-escape-room"
CHROME = r"C:\Users\30807\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe"

results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        raise SystemExit(f"中断于: {name}")


def wait_visible(page, sel, name, timeout=9000):
    try:
        page.wait_for_selector(sel, state="visible", timeout=timeout)
        check(name, True)
    except Exception as e:
        check(name, False, str(e)[:100])


def gone(page, sel, name):
    vis = page.locator(sel).first.is_visible()
    check(name, not vis)


def click(page, sel):
    box = page.locator(sel).first.bounding_box()
    assert box, f"不可点击 {sel}"
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    time.sleep(0.9)


def drag(page, src_sel, dst_sel):
    src = page.locator(src_sel).first
    dst = page.locator(dst_sel).first
    sb = src.bounding_box()
    db = dst.bounding_box()
    assert sb and db, f"不可拖拽 {src_sel}->{dst_sel}"
    sx, sy = sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 2
    dx, dy = db["x"] + db["width"] / 2, db["y"] + db["height"] / 2
    page.mouse.move(sx, sy)
    page.mouse.down()
    for i in range(1, 6):
        page.mouse.move(sx + (dx - sx) * i / 5, sy + (dy - sy) * i / 5)
        time.sleep(0.03)
    page.mouse.up()
    time.sleep(0.6)


def node_name(page, sel):
    return page.locator(sel + " .name").first.inner_text()


def snap(page):
    return page.evaluate(
        "() => (window.__favoriteRoomRuntime && window.__favoriteRoomRuntime.snapshot()) || null"
    )


def keypad_digits(page, code):
    """数字密码盘:补满位数自动提交"""
    for k in code:
        page.locator(f'#keypad [data-k="{k}"]').click()
        time.sleep(0.15)
    time.sleep(0.5)


def keypad_text(page, text):
    """文字语义锁:#keypadText + Enter 提交"""
    page.fill("#keypadText", text)
    page.press("#keypadText", "Enter")
    time.sleep(0.5)


def play_level(page, fname, run):
    page.goto(URL, wait_until="domcontentloaded")
    wait_visible(page, "#homeScreen", f"[{fname}] 首页加载", 15000)
    page.set_input_files("#homeImportFile", ROOT + "\\sample-puzzles\\" + fname + ".room.json")
    wait_visible(page, '[data-id="root"]', f"[{fname}] 导入后根节点出现", 10000)
    click(page, '[data-id="root"]')
    run(page, fname)


def run_a(page, tag):
    """A 显影+检索多问+暗格敲击+计量推导"""
    # 可供性与知识分离(P74 修订):底座前期是惰性物件,早敲不推进
    click(page, '[data-id="compiled-item-ra-base"]')
    s0 = snap(page)
    check(f"[{tag}] 开局底座惰性(无暗格暗示)", bool(s0) and "beat-n9" not in s0.get("clues", []))
    click(page, '[data-id="compiled-item-ra-note"]')  # n1 读字条
    click(page, '[data-id="compiled-container-ra-drawer"]')  # n2 开抽屉
    wait_visible(page, '[data-id="compiled-item-ra-cleaner"]', f"[{tag}] 抽屉见去污粉+磁带")
    drag(page, '[data-id="compiled-item-ra-cleaner"]', '[data-id="compiled-item-ra-fusebox"]')  # n3 显影
    check(
        f"[{tag}] 配电箱显影变身「擦亮的配电箱」",
        node_name(page, '[data-id="compiled-item-ra-fusebox"]') == "擦亮的配电箱",
        node_name(page, '[data-id="compiled-item-ra-fusebox"]'),
    )
    click(page, '[data-id="compiled-item-ra-fusebox"]')  # n4 合闸(检视产物)
    check(
        f"[{tag}] 配电箱再变身「通电的配电箱」",
        node_name(page, '[data-id="compiled-item-ra-fusebox"]') == "通电的配电箱",
        node_name(page, '[data-id="compiled-item-ra-fusebox"]'),
    )
    click(page, '[data-id="compiled-item-ra-tape"]')  # n5 读数据条
    click(page, '[data-id="compiled-item-ra-terminal"]')  # n6 检索一
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 检索台弹出(数字)", 5000)
    keypad_digits(page, "104")  # 错误编号必须被拒
    s = snap(page)
    check(f"[{tag}] 错误编号 104 被拒", s and "beat-n6" not in s.get("clues", []))
    keypad_digits(page, "461")  # 播放量 104610374 第 3-5 位
    wait_visible(page, '[data-id="compiled-item-ra-file-ngu"]', f"[{tag}] 档案从检索台主动弹出(auto)")
    check(
        f"[{tag}] 检索台变身「吐出档案的检索台」",
        node_name(page, '[data-id="compiled-item-ra-terminal"]') == "吐出档案的检索台",
        node_name(page, '[data-id="compiled-item-ra-terminal"]'),
    )
    click(page, '[data-id="compiled-item-ra-file-ngu"]')  # 读档案(压轴线索来源)
    click(page, '[data-id="compiled-item-ra-panel"]')  # n7 频率
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 频率面板弹出", 5000)
    keypad_digits(page, "1046")  # 播放量前四位
    click(page, '[data-id="compiled-item-ra-terminal"]')  # n8 检索二(文字)
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 检索台弹出(文字)", 5000)
    check(f"[{tag}] 第二次查询走文字输入框", page.locator("#keypadText").is_visible())
    keypad_text(page, "压轴")
    wait_visible(page, '[data-id="compiled-item-ra-board"]', f"[{tag}] 底板被振动震出(主动弹出)")
    check(
        f"[{tag}] 检索台变身「嗡嗡作响的检索台」(振动因果)",
        node_name(page, '[data-id="compiled-item-ra-terminal"]') == "嗡嗡作响的检索台",
        node_name(page, '[data-id="compiled-item-ra-terminal"]'),
    )
    click(page, '[data-id="compiled-item-ra-base"]')  # 回访底座:备忘是被动发现(回访语法)
    wait_visible(page, '[data-id="compiled-item-ra-memo"]', f"[{tag}] 底座旁发现台长备忘(回访)")
    click(page, '[data-id="compiled-item-ra-board"]')  # n9 knock 1/3
    click(page, '[data-id="compiled-item-ra-board"]')  # 2/3
    s = snap(page)
    check(f"[{tag}] 敲两下暗格未开(计数生效)", s and "beat-n9" not in s.get("clues", []))
    click(page, '[data-id="compiled-item-ra-board"]')  # 3/3
    s = snap(page)
    check(f"[{tag}] 第三下暗格弹开", s and "beat-n9" in s.get("clues", []))
    check(
        f"[{tag}] 底板变身「撬开的暗格」",
        node_name(page, '[data-id="compiled-item-ra-board"]') == "撬开的暗格",
        node_name(page, '[data-id="compiled-item-ra-board"]'),
    )
    click(page, '[data-id="compiled-item-ra-board"]')  # 再点暗格:光碟飞出(P70 锚定显形)
    wait_visible(page, '[data-id="compiled-item-ra-disc"]', f"[{tag}] 压轴光碟显形")
    time.sleep(1.2)  # 飞入动画落定再拖
    drag(page, '[data-id="compiled-item-ra-disc"]', '[data-id="compiled-exit"]')  # n10
    time.sleep(0.4)
    click(page, '[data-id="compiled-exit"]')
    time.sleep(0.6)
    s = snap(page)
    check(f"[{tag}] 通关(done=true)", bool(s and s.get("done")), f"clues={s and s.get('clues')}")


def run_b(page, tag):
    """B 语义文字"""
    click(page, '[data-id="compiled-container-tb-clip"]')  # t1 开素材夹
    wait_visible(page, '[data-id="compiled-item-tb-card-obs"]', f"[{tag}] 开夹见三张卡+规则卡")
    click(page, '[data-id="compiled-item-tb-card-obs"]')  # t2
    click(page, '[data-id="compiled-item-tb-manual"]')  # t3
    click(page, '[data-id="compiled-item-tb-gate"]')  # t4 开库门文字屏
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 库门文字屏弹出", 5000)
    vis = page.locator("#keypadText").is_visible()
    check(f"[{tag}] 文字输入框可见(textMode)", vis)
    keypad_text(page, "sharpen your thinking")  # 错误答案(整句)必须被拒
    s = snap(page)
    check(f"[{tag}] 整句标语被拒(须去掉第一个词)", s and "beat-t4" not in s.get("clues", []))
    keypad_text(page, "Your  Thinking")  # 大小写/空格归一化也必须通过
    s = snap(page)
    check(f"[{tag}] 库门口令通过(归一化比较)", s and "beat-t4" in s.get("clues", []))
    click(page, '[data-id="compiled-item-tb-card-algo"]')  # t5
    click(page, '[data-id="compiled-item-tb-shelf"]')  # t6 书架标签屏
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 书架标签屏弹出", 5000)
    keypad_text(page, "一键运行")  # 错误答案必须被拒
    s = snap(page)
    check(f"[{tag}] 错误标签被拒", s and "beat-t6" not in s.get("clues", []))
    keypad_text(page, "动画图解")
    click(page, '[data-id="root"]')  # 环顾
    wait_visible(page, '[data-id="compiled-item-tb-note"]', f"[{tag}] 藏书票显形")
    time.sleep(1.2)  # 飞入动画落定再拖
    drag(page, '[data-id="compiled-item-tb-note"]', '[data-id="compiled-item-tb-desk"]')  # t7
    check(
        f"[{tag}] 书桌变身「建成的笔记库」",
        node_name(page, '[data-id="compiled-item-tb-desk"]') == "建成的笔记库",
        node_name(page, '[data-id="compiled-item-tb-desk"]'),
    )
    drag(page, '[data-id="compiled-item-tb-desk"]', '[data-id="compiled-exit"]')  # t8
    time.sleep(0.4)
    click(page, '[data-id="compiled-exit"]')
    time.sleep(0.6)
    s = snap(page)
    check(f"[{tag}] 通关(done=true)", bool(s and s.get("done")), f"clues={s and s.get('clues')}")


def run_c(page, tag):
    """C 排序 sequence"""
    click(page, '[data-id="compiled-item-rc-door"]')  # c1 推门
    click(page, '[data-id="root"]')  # 环顾:门后显形的物件飞入
    time.sleep(1.6)  # 等入口卡避让复检(1500ms)落定,规则卡不再被盖
    wait_visible(page, '[data-id="compiled-item-rc-manual"]', f"[{tag}] 推门见规则卡/书堆/提货单")
    gone(page, '[data-id="compiled-item-rc-stamp"]', f"[{tag}] 借阅章未排架不显形")
    click(page, '[data-id="compiled-item-rc-manual"]')  # c2
    click(page, '[data-id="compiled-item-rc-book-js"]')  # c3
    click(page, '[data-id="compiled-item-rc-book-web"]')  # c4
    click(page, '[data-id="compiled-item-rc-book-web"]')  # 顺序错误:先点②书,整组应重来
    click(page, '[data-id="compiled-item-rc-book-js"]')  # ①
    click(page, '[data-id="compiled-item-rc-book-web"]')  # ②
    s = snap(page)
    check(f"[{tag}] 排架完成(含错误顺序重开)", s and "beat-c5" in s.get("clues", []), f"clues={s and s.get('clues')}")
    check(
        f"[{tag}] 排架台变身「排好架的一对书」",
        node_name(page, '[data-id="compiled-item-rc-shelf"]') == "排好架的一对书",
        node_name(page, '[data-id="compiled-item-rc-shelf"]'),
    )
    click(page, '[data-id="compiled-item-rc-shelf"]')  # 再点变化的节点:借阅章从排架台里飞出(锚定显形)
    wait_visible(page, '[data-id="compiled-item-rc-stamp"]', f"[{tag}] 借阅章弹出")
    time.sleep(1.2)  # 飞入动画落定再拖
    drag(page, '[data-id="compiled-item-rc-stamp"]', '[data-id="compiled-item-rc-ticket"]')  # c6
    check(
        f"[{tag}] 提货单变身「盖章的提货单」",
        node_name(page, '[data-id="compiled-item-rc-ticket"]') == "盖章的提货单",
        node_name(page, '[data-id="compiled-item-rc-ticket"]'),
    )
    drag(page, '[data-id="compiled-item-rc-ticket"]', '[data-id="compiled-exit"]')  # c7
    time.sleep(0.4)
    click(page, '[data-id="compiled-exit"]')
    time.sleep(0.6)
    s = snap(page)
    check(f"[{tag}] 通关(done=true)", bool(s and s.get("done")), f"clues={s and s.get('clues')}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1440, "height": 1400})
        play_level(page, "demo-gamenight", run_a)
        play_level(page, "demo-toolbox", run_b)
        play_level(page, "demo-selfstudy", run_c)
        browser.close()
    passed = sum(results)
    print(f"\n===== 三关实玩: {passed}/{len(results)} 通过 =====")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
