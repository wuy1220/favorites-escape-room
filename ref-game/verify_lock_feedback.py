# -*- coding: utf-8 -*-
"""断电锁反馈回归(2026-08-31,需求方实测 123.room.json 提出):
机关的目标身份还没被变身出来时(终端要先通电),点击锁定物不再静默——
必须提示缺哪一步、会得到什么;且已就绪/已通电的机器不受影响。零配额,
导入内嵌迷你关卡走真实 DOM。在项目根运行(需 8128 静态服务)。"""
import json
import os
import tempfile
import time

from playwright.sync_api import sync_playwright

CHROME = r"C:/Users/30807/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"
results = []

MINI_LEVEL = {
    "items": [
        {"id": "m-print", "title": "打印页", "url": "https://example.com/p/1", "domain": "example.com",
         "dateAdded": "2025-10-10T16:00:00.000Z", "status": "keep"},
        {"id": "m-tape", "title": "胶带说明", "url": "https://example.com/p/2", "domain": "example.com",
         "dateAdded": "2025-10-10T16:00:00.000Z", "status": "keep"},
    ],
    "level": {
        "id": "mini-lock", "title": "断电锁反馈迷你关", "theme": "测试机房",
        "adventureGrammar": "变形:通电后终端才就绪",
        "parallelRooms": True,
        "premise": "机房断电,终端黑屏。",
        "objective": "接好供电线,给终端通电,输入密码离开。",
        "targetMinutes": 8,
        "selectedItemIds": ["prop-1", "m-print", "m-tape", "prop-2", "prop-3", "prop-4", "m-herring"],
        "items": [
            {"id": "prop-1", "role": "lock", "title": "配电柜", "sceneName": "配电柜", "scene": "r1",
             "reason": "三位数字盘。", "hidden": False, "prop": True},
            {"id": "m-print", "role": "clue", "title": "打印页", "sceneName": "打印页", "scene": "r1",
             "reason": "路径末位是 3——配电柜要的就是它。", "hidden": False,
             "facts": [{"k": "路径", "v": "/p/1"}], "grounding": "metadata"},
            {"id": "m-tape", "role": "tool", "title": "胶带说明", "sceneName": "绝缘胶带", "scene": "r1",
             "reason": "一卷绝缘胶带,足以接好一处断口。", "hidden": True,
             "facts": [{"k": "路径", "v": "/p/2"}], "grounding": "metadata"},
            {"id": "prop-2", "role": "tool", "title": "断裂的供电线", "sceneName": "断裂的供电线", "scene": "r1",
             "reason": "两端铜芯裸露。", "hidden": False, "prop": True},
            {"id": "prop-3", "role": "lock", "title": "解密终端", "sceneName": "解密终端", "scene": "r2",
             "reason": "黑屏的终端,电源槽空着。", "hidden": False, "prop": True},
            {"id": "prop-4", "role": "lock", "title": "出口闸门", "sceneName": "出口闸门", "scene": "r2",
             "reason": "电磁闸门,等就绪的终端解锁。", "hidden": False, "prop": True},
            {"id": "m-herring", "role": "red_herring", "title": "旧安装手册", "sceneName": "旧安装手册",
             "scene": "r2", "reason": "另一台机器的安装说明,和这间机房无关。", "hidden": True,
             "facts": [{"k": "路径", "v": "/p/9"}], "grounding": "metadata"},
        ],
        "mechanics": ["inspect", "password", "combine", "deliver"],
        "beats": [
            {"id": "b1", "title": "读打印页", "action": "inspect", "uses": ["m-print"]},
            {"id": "b2", "title": "打开配电柜", "action": "password", "uses": ["prop-1"],
             "requires": ["b1"], "reveals": ["m-tape"], "expected": "003", "product": "打开的配电柜"},
            {"id": "b3", "title": "接好供电线", "action": "combine", "uses": ["m-tape", "prop-2"],
             "requires": ["b2"], "resultOn": "prop-2", "product": "接好的供电线"},
            {"id": "b4", "title": "给终端通电", "action": "combine", "uses": ["result:b3", "prop-3"],
             "requires": ["b3"], "resultOn": "prop-3", "reveals": ["m-herring"],
             "product": "通电的终端"},
            {"id": "b5", "title": "输入启动码", "action": "password", "uses": ["result:b4"],
             "requires": ["b4"], "expected": "123", "product": "就绪的终端"},
            {"id": "b6", "title": "解锁闸门离开", "action": "combine", "uses": ["prop-3", "prop-4"],
             "requires": ["b5"], "resultOn": "prop-4", "product": "开启的出口闸门"},
            {"id": "b7", "title": "走出机房", "action": "deliver", "uses": ["result:b6"], "requires": ["b6"]},
        ],
        "scenes": [
            {"id": "r1", "title": "机房外间", "description": "应急灯。", "focus": "配电柜",
             "itemIds": ["prop-1", "m-print", "m-tape", "prop-2"],
             "beatIds": ["b1", "b2", "b3"]},
            {"id": "r2", "title": "终端里间", "description": "黑屏终端。", "focus": "解密终端",
             "itemIds": ["prop-3", "prop-4", "m-herring"], "beatIds": ["b4", "b5", "b6", "b7"]},
        ],
        "hints": ["先读打印页。", "配电柜取路径末位。", "胶带接供电线。", "终端要先通电。"],
        "validation": {"valid": True, "issues": [], "designSource": "step-scenes"},
    },
}


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""), flush=True)


tmp = tempfile.NamedTemporaryFile(
    mode="w", suffix=".room.json", delete=False, encoding="utf-8", dir=os.getcwd())
json.dump(MINI_LEVEL, tmp, ensure_ascii=False)
tmp.close()

JS = {
    "enter_room": "(id) => document.querySelector('[data-id=\"compiled-scene-' + '%s' + '\"]').click()",
}


def js_click(page, expr):
    page.evaluate("() => " + expr)


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page(viewport={"width": 900, "height": 620})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)[:120]))
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    page.set_input_files("#homeImportFile", tmp.name)
    time.sleep(2)
    page.evaluate("() => document.querySelector('[data-id=\"root\"]').click()")
    time.sleep(1)
    page.evaluate("() => document.querySelector('[data-id=\"compiled-scene-r2\"]').click()")
    time.sleep(0.8)

    # 1) 未通电终端:点击必须有「还没就绪」反馈(旧版静默落空)
    page.evaluate("() => document.querySelector('[data-id=\"compiled-item-prop-3\"]').click()")
    time.sleep(0.6)
    msg = page.evaluate("() => (document.getElementById('logLatest')||{}).textContent || ''")
    toast = page.evaluate("() => (document.getElementById('toast')||{}).textContent || ''")
    check(
        "未通电终端:点击提示缺哪一步、得到什么",
        "还没就绪" in msg and "给终端通电" in msg and "通电的终端" in msg,
        msg[:90],
    )
    check("toast 同步反馈", "还没就绪" in toast, toast[:90])
    pop = page.evaluate("() => !!document.querySelector('[data-id=\"compiled-item-prop-3\"] .node-pop')")
    check("详情卡仍可读(不吞谜面)", pop)

    # 2) 已就绪机器不受影响(守卫):配电柜是现成密码锁,点击应直接弹键盘
    page.evaluate("() => document.querySelector('[data-id=\"compiled-scene-r1\"]').click()")
    time.sleep(0.5)
    page.evaluate("() => document.querySelector('[data-id=\"compiled-item-m-print\"]').click()")
    time.sleep(0.5)
    page.evaluate("() => document.querySelector('[data-id=\"compiled-item-prop-1\"]').click()")
    time.sleep(0.8)
    opened = page.evaluate(
        "() => { const m = document.getElementById('keypadModal'); return m && !m.classList.contains('hidden'); }")
    check("已就绪锁:密码盘正常弹出(回归守卫)", bool(opened))

    # 3) 正控:输 003 开柜 → 胶带显形 → 接线 → 通电 → 终端点击应弹新密码盘而非就绪提示
    if opened:
        for ch in "003":
            page.evaluate(
                """(ch) => document.querySelector('#keypad button[data-k="' + ch + '"]').click()""", ch)
            time.sleep(0.25)
        time.sleep(0.6)
        # 胶带 reveal 就绪:重进房间发现
        page.evaluate("() => document.querySelector('[data-id=\"compiled-scene-r1\"]').click()")
        time.sleep(0.6)
        tape_there = page.evaluate(
            "() => !!document.querySelector('[data-id=\"compiled-item-m-tape\"]')")
        if tape_there:
            page.evaluate("() => document.querySelector('[data-id=\"compiled-item-m-tape\"]').click()")
            time.sleep(0.4)
            page.evaluate(
                "() => window.roomUse('compiled-item-m-tape', 'compiled-item-prop-2')")
            time.sleep(0.8)
            page.evaluate("() => document.querySelector('[data-id=\"compiled-scene-r2\"]').click()")
            time.sleep(0.5)
            page.evaluate(
                "() => window.roomUse('compiled-item-prop-2', 'compiled-item-prop-3')")
            time.sleep(1.0)
            # 通电后终端名字应变身,点击弹 b5 密码盘
            term_name = page.evaluate(
                "() => (document.querySelector('[data-id=\"compiled-item-prop-3\"] .name')||{}).textContent || ''")
            page.evaluate("() => document.querySelector('[data-id=\"compiled-item-prop-3\"]').click()")
            time.sleep(0.8)
            opened2 = page.evaluate(
                "() => { const m = document.getElementById('keypadModal'); return m && !m.classList.contains('hidden'); }")
            ready_again = page.evaluate(
                "() => (document.getElementById('logLatest')||{}).textContent || ''")
            check(
                "通电后终端:点击弹新密码盘(不再误报未就绪)",
                bool(opened2) and "还没就绪" not in ready_again,
                "name=" + str(term_name) + " | " + ready_again[:70],
            )
            # 4) 干扰项伪装:显形后角标必须是「线索」,墨色条与线索一致(不得明牌)
            page.evaluate("() => document.querySelector('[data-id=\"compiled-scene-r2\"]').click()")
            time.sleep(0.6)
            disguise = page.evaluate(
                """() => {
                  const h = document.querySelector('[data-id="compiled-item-m-herring"]');
                  if (!h) return { there: false };
                  const c = document.querySelector('[data-id="compiled-item-m-print"]');
                  return {
                    there: true,
                    tag: (h.querySelector('.type') || {}).textContent || '',
                    ink: getComputedStyle(h).boxShadow,
                    clueInk: c ? getComputedStyle(c).boxShadow : '',
                  };
                }"""
            )
            if not disguise.get("there"):
                check("干扰项伪装:角标与墨色同线索", False, "干扰项未显形")
            else:
                same_ink = disguise["ink"] == disguise["clueInk"]
                check(
                    "干扰项伪装:角标与墨色同线索(不明牌)",
                    disguise["tag"] == "线索" and same_ink,
                    "tag=" + str(disguise["tag"]) + " sameInk=" + str(same_ink),
                )
        else:
            check("通电后终端:点击弹新密码盘(不再误报未就绪)", False, "胶带未显形,链路中断")
    else:
        check("通电后终端:点击弹新密码盘(不再误报未就绪)", False, "键盘未弹,链路中断")

    if errors:
        check("无页面错误", False, "; ".join(errors)[:140])
    else:
        check("无页面错误", True)
    page.screenshot(path="ref-game/lock-feedback.png")
    b.close()

os.unlink(tmp.name)
print(f"\n===== verify_lock_feedback: {sum(results)}/{len(results)} 通过 =====", flush=True)
raise SystemExit(0 if all(results) else 1)
