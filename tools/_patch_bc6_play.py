# -*- coding: utf-8 -*-
"""run_b/run_c v3 容器房间化重写"""
import os

p = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ref-game", "verify_demo_v4_play.py"
)
s = open(p, encoding="utf-8").read()
start = s.index("def run_b(page, tag):")
end = s.index("def main():")
new_runs = '''def run_b(page, tag):
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
    wait_visible(page, '[data-id="compiled-container-tb-wall"]', f"[{tag}] 守库人的墙显形(灯光后文 auto)")
    wait_visible(page, '[data-id="compiled-item-tb-shelf"]', f"[{tag}] 标签屏通电(灯光后文 auto)")
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
    """C v3:三个容器房间(书架×2+借阅台)→扫描校验题→NPC→盖章交单"""
    click(page, '[data-id="compiled-item-rc-door"]')  # c1 推门
    click(page, '[data-id="root"]')  # 环顾:三个房间
    wait_visible(page, '[data-id="compiled-container-rc-shelfa"]', f"[{tag}] 推门见书架×2+借阅台")
    gone(page, '[data-id="compiled-item-rc-npc"]', f"[{tag}] 值班员未现身")
    gone(page, '[data-id="compiled-item-rc-book1"]', f"[{tag}] 书未翻出(容器内)")
    gone(page, '[data-id="compiled-item-rc-manual"]', f"[{tag}] 手册未翻出(借阅台容器内)")
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
        f"[{tag}] 扫描台变身「出题中的扫描台」",
        node_name(page, '[data-id="compiled-item-rc-scanner"]') == "出题中的扫描台",
        node_name(page, '[data-id="compiled-item-rc-scanner"]'),
    )
    wait_visible(page, '[data-id="compiled-item-rc-q1"]', f"[{tag}] 校验题一吐出(auto)")
    click(page, '[data-id="compiled-item-rc-scanner"]')  # c9 答题
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 校验题输入面板弹出", 5000)
    check(f"[{tag}] 校验题走文字输入框", page.locator("#keypadText").is_visible())
    keypad_text(page, "JavaScript 教程")  # 错误答案
    s = snap(page)
    check(f"[{tag}] 错误答案被拒", s and "beat-c9" not in s.get("clues", []))
    keypad_text(page, "JavaScript 参考")  # 卡片原话
    check(
        f"[{tag}] 受理 1/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]') == "扫描台 · 已受理 1/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]'),
    )
    drag(page, '[data-id="compiled-item-rc-book2"]', '[data-id="compiled-item-rc-scanner"]')  # c10
    wait_visible(page, '[data-id="compiled-item-rc-q2"]', f"[{tag}] 校验题二吐出(auto)")
    click(page, '[data-id="compiled-item-rc-scanner"]')  # c11
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
    drag(page, '[data-id="compiled-item-rc-book3"]', '[data-id="compiled-item-rc-scanner"]')  # c12
    wait_visible(page, '[data-id="compiled-item-rc-q3"]', f"[{tag}] 校验题三吐出(auto)")
    click(page, '[data-id="compiled-item-rc-scanner"]')  # c13
    wait_visible(page, "#keypadModal:not(.hidden)", f"[{tag}] 第三题面板弹出", 5000)
    keypad_text(page, "非线性")  # 错误类名
    s = snap(page)
    check(f"[{tag}] 错误类名被拒", s and "beat-c13" not in s.get("clues", []))
    keypad_text(page, "线性")  # 原页面 3.1 节
    check(
        f"[{tag}] 受理 3/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]') == "扫描台 · 已受理 3/3",
        node_name(page, '[data-id="compiled-item-rc-scanner"]'),
    )
    wait_visible(page, '[data-id="compiled-item-rc-npc"]', f"[{tag}] 铃响后值班员现身(auto)")
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


'''
s = s[:start] + new_runs + s[end:]
open(p, "w", encoding="utf-8").write(s)
print("run_b/run_c v3 written")
