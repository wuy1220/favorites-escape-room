# -*- coding: utf-8 -*-
"""三关 v4 真实 DOM 实玩:导入 → 点击/拖拽/输密码 → 通关(done=true)。

A 计量+检索+敲击 / B 电与光族(角度接线→灯光显形→语义锁) / C 借阅族(弹书→顺序扫描→NPC)。
含错误答案被拒、乱序被拒、红标干扰、归一化、计数、auto/回访两种显形语法的断言。
"""
import math
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
    for k in code:
        page.locator(f'#keypad [data-k="{k}"]').click()
        time.sleep(0.15)
    time.sleep(0.5)


def keypad_text(page, text):
    page.fill("#keypadText", text)
    page.press("#keypadText", "Enter")
    time.sleep(0.5)


def dial(page, i, angle):
    """点按表盘上 angle° 的位置(0°=12点,顺时针)"""
    svg = page.locator(f'.angle-dial[data-i="{i}"] .ad-face').first
    b = svg.bounding_box()
    assert b, f"表盘 {i} 不可见"
    cx, cy = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
    R = b["width"] * 0.38
    rad = math.radians(angle)
    page.mouse.click(cx + R * math.sin(rad), cy - R * math.cos(rad))
    time.sleep(0.25)


def play_level(page, fname, run):
    page.goto(URL, wait_until="domcontentloaded")
    wait_visible(page, "#homeScreen", f"[{fname}] 首页加载", 15000)
    page.set_input_files("#homeImportFile", ROOT + "\\sample-puzzles\\" + fname + ".room.json")
    wait_visible(page, '[data-id="root"]', f"[{fname}] 导入后根节点出现", 10000)
    click(page, '[data-id="root"]')
    run(page, fname)


def run_a(page, tag):
    """A 计量+检索多问+暗格敲击"""
    click(page, '[data-id="compiled-item-ra-note"]')  # n1 读字条
    click(page, '[data-id="compiled-container-ra-drawer"]')  # n2 开抽屉
    wait_visible(page, '[data-id="compiled-item-ra-cleaner"]', f"[{tag}] 抽屉见去污粉+磁带")
    click(page, '[data-id="compiled-item-ra-base"]')  # 底座惰性:早敲不推进
    s0 = snap(page)
    check(f"[{tag}] 开局底座惰性(无暗格暗示)", bool(s0) and "beat-n9" not in s0.get("clues", []))
    drag(page, '[data-id="compiled-item-ra-cleaner"]', '[data-id="compiled-item-ra-fusebox"]')  # n3 显影
    check(
        f"[{tag}] 配电箱显影变身「擦亮的配电箱」",
        node_name(page, '[data-id="compiled-item-ra-fusebox"]') == "擦亮的配电箱",
        node_name(page, '[data-id="compiled-item-ra-fusebox"]'),
    )
    click(page, '[data-id="compiled-item-ra-fusebox"]')  # n4 合闸
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
    wait_visible(page, '[data-id="compiled-item-ra-file-ngu"]', f"[{tag}] 档案主动弹出(auto)")
    check(
        f"[{tag}] 检索台变身「吐出档案的检索台」",
        node_name(page, '[data-id="compiled-item-ra-terminal"]') == "吐出档案的检索台",
        node_name(page, '[data-id="compiled-item-ra-terminal"]'),
    )
    click(page, '[data-id="compiled-item-ra-file-ngu"]')  # 读档案
    click(page, '[data-id="compiled-item-ra-panel"]')  # n7 频率
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 频率面板弹出", 5000)
    keypad_digits(page, "1046")  # 播放量前四位
    click(page, '[data-id="compiled-item-ra-terminal"]')  # n8 检索二(文字)
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 检索台弹出(文字)", 5000)
    check(f"[{tag}] 第二次查询走文字输入框", page.locator("#keypadText").is_visible())
    keypad_text(page, "压轴")
    wait_visible(page, '[data-id="compiled-item-ra-board"]', f"[{tag}] 底板被振动震出(auto)")
    check(
        f"[{tag}] 检索台变身「嗡嗡作响的检索台」",
        node_name(page, '[data-id="compiled-item-ra-terminal"]') == "嗡嗡作响的检索台",
        node_name(page, '[data-id="compiled-item-ra-terminal"]'),
    )
    click(page, '[data-id="compiled-item-ra-base"]')  # 回访底座:备忘(回访语法)
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
    click(page, '[data-id="compiled-item-ra-board"]')  # 再点暗格:光碟飞出
    wait_visible(page, '[data-id="compiled-item-ra-disc"]', f"[{tag}] 压轴光碟显形")
    time.sleep(1.2)
    drag(page, '[data-id="compiled-item-ra-disc"]', '[data-id="compiled-exit"]')  # n10
    time.sleep(0.4)
    click(page, '[data-id="compiled-exit"]')
    time.sleep(0.6)
    s = snap(page)
    check(f"[{tag}] 通关(done=true)", bool(s and s.get("done")), f"clues={s and s.get('clues')}")


def run_b(page, tag):
    """B 电与光族:角度接线→灯光显形→语义锁"""
    click(page, '[data-id="compiled-container-tb-clip"]')  # w1 开素材夹
    wait_visible(page, '[data-id="compiled-item-tb-card-obs"]', f"[{tag}] 开夹见卡与皱便签")
    click(page, '[data-id="compiled-item-tb-note-folded"]')  # w2 读皱便签
    click(page, '[data-id="compiled-item-tb-panelbase"]')  # w3 看端子盘
    click(page, '[data-id="compiled-item-tb-lamp"]')  # w4 接线
    wait_visible(page, "#angleModal:not(.hidden)", f"[{tag}] 台灯表盘弹出", 5000)
    modal_txt = page.evaluate("() => document.getElementById('angleModal').innerText")
    check(
        f"[{tag}] 表盘显示红线/蓝线/黄线(不显示目标角度)",
        ("红线" in modal_txt) and ("蓝线" in modal_txt) and ("黄线" in modal_txt) and ("目标" not in modal_txt),
    )
    dial(page, 0, 0)  # 全拨错
    dial(page, 1, 0)
    dial(page, 2, 0)
    time.sleep(0.4)
    s = snap(page)
    check(f"[{tag}] 全拨错灯不亮", s and "beat-w4" not in s.get("clues", []))
    dial(page, 0, 90)  # 红 3 点
    dial(page, 1, 210)  # 蓝 7 点
    dial(page, 2, 330)  # 黄 11 点
    time.sleep(0.5)
    s = snap(page)
    check(f"[{tag}] 按钟面接对线灯亮", s and "beat-w4" in s.get("clues", []))
    check(
        f"[{tag}] 台灯变身「亮起的台灯」",
        node_name(page, '[data-id="compiled-item-tb-lamp"]') == "亮起的台灯",
        node_name(page, '[data-id="compiled-item-tb-lamp"]'),
    )
    wait_visible(page, '[data-id="compiled-item-tb-note-wall1"]', f"[{tag}] 灯下便签显形(auto 灯光显形)")
    wait_visible(page, '[data-id="compiled-item-tb-note-wall2"]', f"[{tag}] 第二张便签显形")
    click(page, '[data-id="compiled-item-tb-note-wall1"]')  # w5 口令规则
    click(page, '[data-id="compiled-item-tb-note-wall2"]')  # w6 算法标语
    click(page, '[data-id="compiled-item-tb-gate"]')  # w7 库门
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 库门文字屏弹出", 5000)
    keypad_text(page, "sharpen your thinking")  # 整句必须被拒
    s = snap(page)
    check(f"[{tag}] 整句标语被拒(须去掉第一个词)", s and "beat-w7" not in s.get("clues", []))
    keypad_text(page, "Your  Thinking")  # 归一化通过
    s = snap(page)
    check(f"[{tag}] 库门口令通过", s and "beat-w7" in s.get("clues", []))
    wait_visible(page, '[data-id="compiled-item-tb-ticket"]', f"[{tag}] 藏书票滑出(auto)")
    click(page, '[data-id="compiled-item-tb-shelf"]')  # w8 书架标签
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 书架标签屏弹出", 5000)
    keypad_text(page, "一键运行")  # 错误标签必须被拒
    s = snap(page)
    check(f"[{tag}] 错误标签被拒", s and "beat-w8" not in s.get("clues", []))
    keypad_text(page, "动画图解")
    time.sleep(1.2)  # 藏书票飞入落定
    drag(page, '[data-id="compiled-item-tb-ticket"]', '[data-id="compiled-item-tb-desk"]')  # w9
    check(
        f"[{tag}] 书桌变身「建成的笔记库」",
        node_name(page, '[data-id="compiled-item-tb-desk"]') == "建成的笔记库",
        node_name(page, '[data-id="compiled-item-tb-desk"]'),
    )
    drag(page, '[data-id="compiled-item-tb-desk"]', '[data-id="compiled-exit"]')  # w10
    time.sleep(0.4)
    click(page, '[data-id="compiled-exit"]')
    time.sleep(0.6)
    s = snap(page)
    check(f"[{tag}] 通关(done=true)", bool(s and s.get("done")), f"clues={s and s.get('clues')}")


def run_c(page, tag):
    """C 借阅族 v4:容器弹书→扫描出题→卡片原话/回访页面答题→NPC 现身/对话/交易→盖章交单"""
    click(page, '[data-id="compiled-item-rc-door"]')  # c1 推门
    click(page, '[data-id="root"]')  # 环顾
    wait_visible(page, '[data-id="compiled-item-rc-manual"]', f"[{tag}] 推门见手册/扫描台/提货单")
    gone(page, '[data-id="compiled-item-rc-npc"]', f"[{tag}] 值班员未现身")
    gone(page, '[data-id="compiled-item-rc-book1"]', f"[{tag}] 书未翻出(容器内)")
    # 书架不依赖手册即可点击(P74 修订:c3/c4 只挂推门前置)
    click(page, '[data-id="compiled-container-rc-shelfa"]')  # c3 翻上层
    wait_visible(page, '[data-id="compiled-item-rc-book1"]', f"[{tag}] 上层滑出两本绿标书")
    click(page, '[data-id="compiled-container-rc-shelfb"]')  # c4 翻下层
    wait_visible(page, '[data-id="compiled-item-rc-book2"]', f"[{tag}] 下层滑出绿标+红标")
    # 容器去重:书架节点应只有一个
    n_shelf = page.evaluate(
        "() => document.querySelectorAll('[data-id=\"compiled-container-rc-shelfa\"],[data-id=\"compiled-item-rc-shelfa\"]').length"
    )
    check(f"[{tag}] 上层书架无重复节点", n_shelf == 1, f"count={n_shelf}")
    click(page, '[data-id="compiled-item-rc-manual"]')  # c2 读手册
    click(page, '[data-id="compiled-item-rc-book1"]')  # c5 看 MDN 卡
    click(page, '[data-id="compiled-item-rc-book2"]')  # c6 看教程卡
    click(page, '[data-id="compiled-item-rc-book3"]')  # c7 看算法卡
    time.sleep(1.2)  # 书飞入落定
    drag(page, '[data-id="compiled-item-rc-book4"]', '[data-id="compiled-item-rc-scanner"]')  # 红标书乱扫
    s = snap(page)
    check(f"[{tag}] 红标书扫描无受理", s and "beat-c8" not in s.get("clues", []))
    drag(page, '[data-id="compiled-item-rc-book2"]', '[data-id="compiled-item-rc-scanner"]')  # 乱序:先扫主课程
    s = snap(page)
    check(
        f"[{tag}] 乱序扫描被拒(概述在前)",
        s and "beat-c8" not in s.get("clues", []) and "beat-c10" not in s.get("clues", []),
    )
    drag(page, '[data-id="compiled-item-rc-book1"]', '[data-id="compiled-item-rc-scanner"]')  # c8 扫概述
    check(
        f"[{tag}] 扫描台变身「出题中的扫描台」",
        node_name(page, '[data-id="compiled-item-rc-scanner"]') == "出题中的扫描台",
        node_name(page, '[data-id="compiled-item-rc-scanner"]'),
    )
    wait_visible(page, '[data-id="compiled-item-rc-q1"]', f"[{tag}] 校验题一吐出(auto)")
    click(page, '[data-id="compiled-item-rc-scanner"]')  # c9 答题
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 校验题输入面板弹出", 5000)
    check(f"[{tag}] 校验题走文字输入框", page.locator("#keypadText").is_visible())
    keypad_text(page, "JavaScript 教程")  # 错误答案必须被拒
    s = snap(page)
    check(f"[{tag}] 错误答案被拒", s and "beat-c9" not in s.get("clues", []))
    keypad_text(page, "JavaScript 参考")  # 卡片原话
    check(
        f"[{tag}] 受理 1/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]') == "扫描台 · 已受理 1/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]'),
    )
    drag(page, '[data-id="compiled-item-rc-book2"]', '[data-id="compiled-item-rc-scanner"]')  # c10 扫主课程
    wait_visible(page, '[data-id="compiled-item-rc-q2"]', f"[{tag}] 校验题二吐出(auto)")
    click(page, '[data-id="compiled-item-rc-scanner"]')  # c11 答题
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 第二题面板弹出", 5000)
    keypad_digits(page, "3")  # 错误数字
    s = snap(page)
    check(f"[{tag}] 错误数字被拒", s and "beat-c11" not in s.get("clues", []))
    keypad_digits(page, "2")  # 主课程包含 2 部分
    check(
        f"[{tag}] 受理 2/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]') == "扫描台 · 已受理 2/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]'),
    )
    drag(page, '[data-id="compiled-item-rc-book3"]', '[data-id="compiled-item-rc-scanner"]')  # c12 扫算法
    wait_visible(page, '[data-id="compiled-item-rc-q3"]', f"[{tag}] 校验题三吐出(auto)")
    click(page, '[data-id="compiled-item-rc-scanner"]')  # c13 答题
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 第三题面板弹出", 5000)
    keypad_text(page, "非线性")  # 错误类名
    s = snap(page)
    check(f"[{tag}] 错误类名被拒", s and "beat-c13" not in s.get("clues", []))
    keypad_text(page, "线性")  # 原页面 3.1 节的分类
    check(
        f"[{tag}] 受理 3/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]') == "扫描台 · 已受理 3/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]'),
    )
    wait_visible(page, '[data-id="compiled-item-rc-npc"]', f"[{tag}] 铃响后值班员现身(auto 巧合事件)")
    click(page, '[data-id="compiled-item-rc-npc"]')  # c14 对话
    time.sleep(1.2)
    drag(page, '[data-id="compiled-item-rc-kettle"]', '[data-id="compiled-item-rc-npc"]')  # c15 交易
    check(
        f"[{tag}] 值班员变身「捧着热茶的值班员」",
        node_name(page, '[data-id="compiled-item-rc-npc"]') == "捧着热茶的值班员",
        node_name(page, '[data-id="compiled-item-rc-npc"]'),
    )
    wait_visible(page, '[data-id="compiled-item-rc-stamp"]', f"[{tag}] 借阅章递出(auto)")
    time.sleep(1.2)
    drag(page, '[data-id="compiled-item-rc-stamp"]', '[data-id="compiled-item-rc-ticket"]')  # c16
    check(
        f"[{tag}] 提货单变身「盖章的提货单」",
        node_name(page, '[data-id="compiled-item-rc-ticket"]') == "盖章的提货单",
        node_name(page, '[data-id="compiled-item-rc-ticket"]'),
    )
    drag(page, '[data-id="compiled-item-rc-ticket"]', '[data-id="compiled-exit"]')  # c17
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
