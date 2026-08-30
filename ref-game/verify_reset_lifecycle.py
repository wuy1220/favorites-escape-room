# -*- coding: utf-8 -*-
"""重置生命周期回归(handoff 11.12,零配额):
生成关卡运行中点击 #reset(重置房间)必须是产品动作「重置本关」——
仍显示同一关卡入口、progress 写回初始态、机关弹窗关闭、工具栏标题不变、
window.__dbg(编译态)存在、画布不是退回固定 Room 02;
刷新后「继续游戏」恢复的是重置后(未开始)的进度;标题界面/删除语义不变。
在项目根运行(需 8128 静态服务)。"""
import json
import re
import time

from playwright.sync_api import sync_playwright

CHROME = r"C:/Users/30807/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"
FIXTURE = "fixtures/sample10-bookmarks.html"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))


def valid_design(ids):
    """与 verify_design_race 同款:2 房间、可编译可解、满足空间密度门槛。"""
    r = ids[:6] + ["x%d" % i for i in range(6 - min(len(ids), 6))]
    return {
        "title": "重置回归关",
        "theme": "测试主题·由素材契合",
        "adventureGrammar": "变形:一句如何组织",
        "premise": "一间测试用的套房：外间和里间。",
        "objective": "解开里间的密码锁，把上膛的钥匙卡交给出口。",
        "targetMinutes": 10,
        "mechanics": ["密码在说明书里。"],
        "hints": ["一", "二", "三", "四", "五", "六", "七", "八"],
        "scenes": [
            {
                "id": "sc-a",
                "title": "外间",
                "description": "一张桌子和散乱的接线。",
                "focus": "散乱的接线盒",
                "items": [
                    {"id": r[0], "role": "tool", "sceneName": "撬棍", "reason": "能撬开东西"},
                    {"id": r[1], "role": "clue", "sceneName": "便签", "reason": "写着提示"},
                    {"id": r[2], "role": "tool", "sceneName": "接线钳", "reason": "藏在接线盒里", "hidden": True},
                    {"id": "prop-1", "role": "tool", "sceneName": "接线盒", "reason": "面板螺丝锈死,要用工具撬开"},
                ],
                "beats": [
                    {"id": "s1", "title": "看便签", "action": "inspect", "uses": [r[1]]},
                    {"id": "s1b", "title": "撬开接线盒", "action": "combine", "uses": [r[0], "prop-1"],
                     "resultOn": "prop-1", "product": "打开的接线盒", "requires": ["s1"], "reveals": [r[2]]},
                    {"id": "s2", "title": "接好线路", "action": "combine", "uses": [r[0], r[2]], "product": "组合甲"},
                ],
            },
            {
                "id": "sc-b",
                "title": "里间",
                "description": "一台终端和上锁的出口。",
                "focus": "密码锁终端",
                "items": [
                    {"id": r[3], "role": "clue", "sceneName": "说明书", "reason": "记录步骤"},
                    {"id": r[4], "role": "clue", "sceneName": "对照卡", "reason": "写着三位数字对照"},
                    {"id": r[5], "role": "reward", "sceneName": "钥匙卡", "reason": "出口凭证", "hidden": True},
                    {"id": "prop-2", "role": "lock", "sceneName": "黄铜密码闸机", "reason": "三位数字盘,盘面只有经年的锈"},
                ],
                "beats": [
                    {"id": "s3", "title": "读说明书", "action": "inspect", "uses": [r[3]]},
                    {"id": "s3b", "title": "读对照卡", "action": "inspect", "uses": [r[4]]},
                    {"id": "s4", "title": "输密码", "action": "password", "uses": ["prop-2"], "expected": "123",
                     "requires": ["s1", "s3b"], "reveals": [r[5]], "deriveFrom": [r[4]]},
                    {"id": "s5", "title": "上膛钥匙卡", "action": "combine", "uses": [r[4], r[5]],
                     "requires": ["s4"], "resultOn": r[5], "product": "上膛的钥匙卡"},
                    {"id": "s6", "title": "交付离开", "action": "deliver", "uses": ["result:s5"],
                     "requires": ["s5"]},
                ],
            },
        ],
    }


def handle(route):
    try:
        body = json.loads(route.request.post_data)
        system = body["messages"][0]["content"]
        if "整理器" in system:
            prompt = json.loads(body["messages"][1]["content"])
            out = [
                {"id": it["id"], "status": "keep", "topics": ["测试"], "reason": "复核通过", "intent": ""}
                for it in prompt.get("items", [])
            ]
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps({"choices": [{"message": {"content": json.dumps({"items": out})}}]}))
            return
        user_part = body["messages"][1]["content"].split("\n\n【参考关卡A")[0]
        ids = [i for i in dict.fromkeys(re.findall(r'"id"\s*:\s*"([^"]+)"', user_part))
               if not i.startswith("result:")][:6]
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"choices": [{"message": {"content": json.dumps(valid_design(ids))}}]}))
    except Exception as e:
        print("  [stub] 已忽略:", str(e)[:80])


READ_PROGRESS = """(key) => new Promise((res) => {
  const r = indexedDB.open('favorites-escape-room-local');
  r.onsuccess = () => {
    const q = r.result.transaction('progress').objectStore('progress').getAll();
    q.onsuccess = () => res(q.result[q.result.length - 1] || null);
  };
})"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.on("pageerror", lambda e: print("[pageerror]", str(e)[:160]))
    page.route("**/api/step**", handle)
    page.route("**/fetch-meta**", lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps({"results": {}})))
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)

    # 导入 → 生成 → 挂载
    page.set_input_files("#homeFile", FIXTURE)
    page.wait_for_timeout(1200)
    page.click("#homeGenerate")
    page.wait_for_function(
        "() => { const t = document.getElementById('gameToolbar');"
        " return t && !t.hasAttribute('hidden'); }",
        timeout=60000,
    )
    title0 = page.evaluate("() => document.getElementById('gameTitle').textContent")
    check("生成关卡已挂载,工具栏有标题", bool(title0), title0)

    # 开始关卡(rootMode:点 root 即 levelStart),等一次自动保存
    page.click('[data-id="root"]')
    page.wait_for_timeout(800)
    snap0 = page.evaluate("() => window.__favoriteRoomRuntime.snapshot()")
    check("开始后运行态 started=true", bool(snap0 and snap0.get("started")), json.dumps(snap0)[:80])
    page.wait_for_timeout(4500)  # 自动保存(4s 周期)
    prog0 = page.evaluate(READ_PROGRESS)
    check("重置前 progress 已保存且 started=true",
          bool(prog0 and prog0.get("snapshot", {}).get("started")),
          json.dumps((prog0 or {}).get("snapshot", {}))[:80])

    # ===== 产品动作:重置本关 =====
    page.click("#reset")
    page.wait_for_timeout(600)
    title1 = page.evaluate("() => document.getElementById('gameTitle').textContent")
    check("重置后工具栏标题不变(同一关卡)", title1 == title0, title1)
    snap1 = page.evaluate("() => window.__favoriteRoomRuntime.snapshot()")
    check("重置后运行态为初始(started=false, clues 空)",
          bool(snap1) and not snap1.get("started") and not (snap1.get("clues") or []),
          json.dumps(snap1)[:90])
    dbg_ok = page.evaluate("() => !!(window.__dbg && window.__dbg.level && window.__dbg.level.parallelRooms === true)")
    check("重置后编译态重建且并行房间模式保留(window.__dbg)", dbg_ok)
    modals_hidden = page.evaluate(
        "() => ['keypadModal','angleModal','morseModal','namingModal']"
        ".every((id) => { const e = document.getElementById(id);"
        " return !e || e.classList.contains('hidden'); })"
    )
    check("重置后机关/命名弹窗全部关闭", modals_hidden)
    # progress 写回初始态(产品层 reset await saveProgress,轮询等待)
    prog1 = None
    for _ in range(10):
        prog1 = page.evaluate(READ_PROGRESS)
        if prog1 and prog1.get("snapshot") and not prog1["snapshot"].get("started"):
            break
        page.wait_for_timeout(500)
    check("重置后 progress 写回初始态(started=false)",
          bool(prog1 and prog1.get("snapshot") and not prog1["snapshot"].get("started")),
          json.dumps((prog1 or {}).get("snapshot", {}))[:90])
    # 同一关卡入口仍在:再点 root,房间重新亮出(不是退回固定 Room 02)
    page.click('[data-id="root"]')
    page.wait_for_timeout(600)
    zones = page.evaluate(
        "() => Array.from(document.querySelectorAll('[data-id^=\"compiled-scene-\"]'))"
        ".filter((e) => e.offsetParent !== null).length"
    )
    check("重置后同一关卡入口可用(scene 节点 %d 个亮出)" % zones, zones >= 2)
    # 入口验证重新开始了关卡——再次重置回初始态,避免自动保存把进行中进度带进下一环节
    page.evaluate("() => window.__favoriteRoomHome.resetCurrentLevel()")
    page.wait_for_timeout(900)

    # ===== 刷新后「继续游戏」恢复的是重置后(未开始)的进度 =====
    page.reload(wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    page.wait_for_timeout(800)
    cont_disabled = page.evaluate("() => document.getElementById('homeContinue').disabled")
    check("刷新后「继续游戏」可用(有存档)", not cont_disabled)
    page.click("#homeContinue")
    page.wait_for_function(
        "() => { const t = document.getElementById('gameToolbar');"
        " return t && !t.hasAttribute('hidden'); }",
        timeout=15000,
    )
    snap2 = page.evaluate("() => window.__favoriteRoomRuntime.snapshot()")
    title2 = page.evaluate("() => document.getElementById('gameTitle').textContent")
    check("继续游戏恢复的是重置后进度(started=false)", bool(snap2) and not snap2.get("started"), json.dumps(snap2)[:80])
    check("继续游戏打开的是同一关卡", title2 == title0, title2)

    # ===== 离开语义:标题界面返回,存档仍在 =====
    page.click("#gameHome")
    page.wait_for_timeout(600)
    home_visible = page.evaluate(
        "() => !document.getElementById('homeScreen').classList.contains('hidden')"
        " && document.getElementById('gameToolbar').hasAttribute('hidden')"
    )
    saved_rows = page.evaluate("() => document.querySelectorAll('.saved-row').length")
    check("离开本关回标题界面,存档列表仍渲染(语义不变)", home_visible and saved_rows >= 1,
          f"rows={saved_rows}")

    b.close()

print(f"\n===== verify_reset_lifecycle: {sum(results)}/{len(results)} 通过 =====")
raise SystemExit(0 if all(results) else 1)
