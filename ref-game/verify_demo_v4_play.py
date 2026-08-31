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
    """B v3:拼信→修灯(角度)→灯光后文→双语义锁→台历接任(容器房间化)"""
    click(page, '[data-id="compiled-container-tb-clip"]')  # u1 开素材夹
    wait_visible(page, '[data-id="compiled-item-tb-card-obs"]', f"[{tag}] 开夹见卡与两张纸片")
    time.sleep(1.2)  # 飞入落定
    drag(page, '[data-id="compiled-item-tb-paper1"]', '[data-id="compiled-item-tb-paper2"]')  # u2 拼信
    check(
        f"[{tag}] 纸片拼合成「完整的信」",
        node_name(page, '[data-id="compiled-item-tb-paper1"]') == "完整的信",
        node_name(page, '[data-id="compiled-item-tb-paper1"]'),
    )
    wait_visible(page, '[data-id="compiled-item-tb-letter"]', f"[{tag}] 信文主动展开(auto)")
    click(page, '[data-id="compiled-item-tb-letter"]')  # u3 读信
    click(page, '[data-id="compiled-container-tb-desk"]')  # u4 走近书桌
    wait_visible(page, '[data-id="compiled-item-tb-lamp"]', f"[{tag}] 书桌上台灯/端子盘/台历")
    click(page, '[data-id="compiled-item-tb-panelbase"]')  # u5 读端子盘
    click(page, '[data-id="compiled-item-tb-lamp"]')  # u6 接线
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
    check(f"[{tag}] 全拨错灯不亮", s and "beat-u6" not in s.get("clues", []))
    dial(page, 0, 90)  # 红 3 点
    dial(page, 1, 210)  # 蓝 7 点
    dial(page, 2, 330)  # 黄 11 点
    time.sleep(0.5)
    s = snap(page)
    check(f"[{tag}] 按钟面接对线灯亮", s and "beat-u6" in s.get("clues", []))
    check(
        f"[{tag}] 台灯变身「亮起的台灯」",
        node_name(page, '[data-id="compiled-item-tb-lamp"]') == "亮起的台灯",
        node_name(page, '[data-id="compiled-item-tb-lamp"]'),
    )
    wait_visible(page, '[data-id="compiled-item-tb-shelf"]', f"[{tag}] 标签屏通电(灯光后文 auto)")
    click(page, '[data-id="root"]')  # 环顾:光够到的墙显形(回访语法)
    wait_visible(page, '[data-id="compiled-container-tb-wall"]', f"[{tag}] 守库人的墙显形(回访)")
    click(page, '[data-id="compiled-container-tb-wall"]')  # u7 走到墙前
    wait_visible(page, '[data-id="compiled-item-tb-note-wall1"]', f"[{tag}] 两张便签显形")
    click(page, '[data-id="compiled-item-tb-note-wall1"]')  # u8 口令规则
    click(page, '[data-id="compiled-item-tb-note-wall2"]')  # u9 标签规则
    click(page, '[data-id="compiled-item-tb-gate"]')  # u10 库门
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 库门文字屏弹出", 5000)
    keypad_text(page, "sharpen your thinking")  # 整句必须被拒
    s = snap(page)
    check(f"[{tag}] 整句标语被拒(须去掉第一个词)", s and "beat-u10" not in s.get("clues", []))
    keypad_text(page, "Your  Thinking")  # 归一化通过
    s = snap(page)
    check(f"[{tag}] 库门口令通过", s and "beat-u10" in s.get("clues", []))
    check(
        f"[{tag}] 库门变身「敞开的库门」",
        node_name(page, '[data-id="compiled-item-tb-gate"]') == "敞开的库门",
        node_name(page, '[data-id="compiled-item-tb-gate"]'),
    )
    click(page, '[data-id="compiled-item-tb-shelf"]')  # u11 书架标签
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 书架标签屏弹出", 5000)
    keypad_text(page, "一键运行")  # 错误标签必须被拒
    s = snap(page)
    check(f"[{tag}] 错误标签被拒", s and "beat-u11" not in s.get("clues", []))
    keypad_text(page, "动画图解")
    check(
        f"[{tag}] 书架变身「亮起顶层标签的书架」",
        node_name(page, '[data-id="compiled-item-tb-shelf"]') == "亮起顶层标签的书架",
        node_name(page, '[data-id="compiled-item-tb-shelf"]'),
    )
    click(page, '[data-id="compiled-item-tb-calendar"]')  # u12 翻台历
    check(
        f"[{tag}] 台历变身「翻到今天的台历」",
        node_name(page, '[data-id="compiled-item-tb-calendar"]') == "翻到今天的台历",
        node_name(page, '[data-id="compiled-item-tb-calendar"]'),
    )
    wait_visible(page, '[data-id="compiled-item-tb-letter-final"]', f"[{tag}] 接任书显形(auto 后文)")
    time.sleep(1.2)
    drag(page, '[data-id="compiled-item-tb-letter-final"]', '[data-id="compiled-exit"]')  # u13
    time.sleep(0.4)
    click(page, '[data-id="compiled-exit"]')
    time.sleep(0.6)
    s = snap(page)
    check(f"[{tag}] 通关(done=true)", bool(s and s.get("done")), f"clues={s and s.get('clues')}")


def run_c(page, tag):
    """C v5:推门 auto 亮三房间→弹书→选择题扫描(书留参照,拖备选到题干)→NPC→交单"""
    click(page, '[data-id="compiled-item-rc-door"]')  # c1 推门
    # 推门=视线进入,三个房间 auto 直接亮出(无需环顾)
    wait_visible(page, '[data-id="compiled-container-rc-shelfa"]', f"[{tag}] 推门后书架/借阅台直接亮出(auto)")
    wait_visible(page, '[data-id="compiled-container-rc-desk"]', f"[{tag}] 借阅台亮出")
    gone(page, '[data-id="compiled-item-rc-npc"]', f"[{tag}] 值班员未现身")
    gone(page, '[data-id="compiled-item-rc-book1"]', f"[{tag}] 书未翻出(容器内)")
    click(page, '[data-id="compiled-container-rc-desk"]')  # 走近借阅台
    wait_visible(page, '[data-id="compiled-item-rc-manual"]', f"[{tag}] 借阅台上手册/扫描台/提货单")
    click(page, '[data-id="compiled-item-rc-manual"]')  # c2 读手册
    click(page, '[data-id="compiled-container-rc-shelfa"]')  # c3 翻上层
    wait_visible(page, '[data-id="compiled-item-rc-book1"]', f"[{tag}] 上层滑出两本绿标书")
    click(page, '[data-id="compiled-container-rc-shelfb"]')  # c4 翻下层
    wait_visible(page, '[data-id="compiled-item-rc-book2"]', f"[{tag}] 下层滑出绿标+红标+保温壶")
    click(page, '[data-id="compiled-item-rc-book1"]')  # c5 看 MDN 卡
    click(page, '[data-id="compiled-item-rc-book2"]')  # c6 看教程卡
    click(page, '[data-id="compiled-item-rc-book3"]')  # c7 看算法卡
    time.sleep(1.2)  # 书飞入落定
    drag(page, '[data-id="compiled-item-rc-book4"]', '[data-id="compiled-item-rc-scanner"]')  # 红标书乱扫
    s = snap(page)
    check(f"[{tag}] 红标书扫描无受理", s and "beat-c8" not in s.get("clues", []))
    drag(page, '[data-id="compiled-item-rc-book2"]', '[data-id="compiled-item-rc-scanner"]')  # 乱序
    s = snap(page)
    check(
        f"[{tag}] 乱序扫描被拒(概述在前)",
        s and "beat-c8" not in s.get("clues", []) and "beat-c10" not in s.get("clues", []),
    )
    drag(page, '[data-id="compiled-item-rc-book1"]', '[data-id="compiled-item-rc-scanner"]')  # c8 扫概述
    check(
        f"[{tag}] 扫描台变身题干「校验中:该参阅什么?」",
        node_name(page, '[data-id="compiled-item-rc-scanner"]') == "校验中:该参阅什么?",
        node_name(page, '[data-id="compiled-item-rc-scanner"]'),
    )
    wait_visible(page, '[data-id="compiled-item-rc-o1a"]', f"[{tag}] 三张备选标签弹出(auto)")
    check(
        f"[{tag}] 扫描后书留作参照(不消耗)",
        page.locator('[data-id="compiled-item-rc-book1"]').is_visible(),
    )
    drag(page, '[data-id="compiled-item-rc-o1b"]', '[data-id="compiled-item-rc-scanner"]')  # 错误备选
    s = snap(page)
    check(f"[{tag}] 错误备选拖入无反应", s and "beat-c9" not in s.get("clues", []))
    drag(page, '[data-id="compiled-item-rc-o1a"]', '[data-id="compiled-item-rc-scanner"]')  # c9 正确备选
    check(
        f"[{tag}] 受理 1/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]') == "扫描台 · 已受理 1/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]'),
    )
    gone(page, '[data-id="compiled-item-rc-o1a"]', f"[{tag}] 作答后备选与书一起归架(consume)")
    drag(page, '[data-id="compiled-item-rc-book2"]', '[data-id="compiled-item-rc-scanner"]')  # c10
    wait_visible(page, '[data-id="compiled-item-rc-o2a"]', f"[{tag}] 第二题备选弹出(auto)")
    drag(page, '[data-id="compiled-item-rc-o2b"]', '[data-id="compiled-item-rc-scanner"]')  # 错误
    s = snap(page)
    check(f"[{tag}] 第二题错误备选无反应", s and "beat-c11" not in s.get("clues", []))
    drag(page, '[data-id="compiled-item-rc-o2a"]', '[data-id="compiled-item-rc-scanner"]')  # c11
    check(
        f"[{tag}] 受理 2/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]') == "扫描台 · 已受理 2/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]'),
    )
    drag(page, '[data-id="compiled-item-rc-book3"]', '[data-id="compiled-item-rc-scanner"]')  # c12
    wait_visible(page, '[data-id="compiled-item-rc-o3a"]', f"[{tag}] 第三题备选弹出(auto)")
    drag(page, '[data-id="compiled-item-rc-o3b"]', '[data-id="compiled-item-rc-scanner"]')  # 错误(非线性)
    s = snap(page)
    check(f"[{tag}] 第三题错误备选无反应", s and "beat-c13" not in s.get("clues", []))
    drag(page, '[data-id="compiled-item-rc-o3a"]', '[data-id="compiled-item-rc-scanner"]')  # c13 正确
    check(
        f"[{tag}] 受理 3/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]') == "扫描台 · 已受理 3/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]'),
    )
    wait_visible(page, '[data-id="compiled-item-rc-npc"]', f"[{tag}] 铃响后值班员现身(auto)")
    time.sleep(1.2)  # 现身动画落定
    click(page, '[data-id="compiled-item-rc-npc"]')  # c14 对话
    s = snap(page)
    check(f"[{tag}] 对话完成(c14)", s and "beat-c14" in s.get("clues", []))
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
