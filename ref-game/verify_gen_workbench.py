# -*- coding: utf-8 -*-
"""生成工作台回归(2026-08-30,零配额):把黑盒等待变成可感知的工作过程。
场景:①正常生成——阶段 stepper/已用时间跳动/素材卡片(可跳源)/赛马实况/完成挂载;
②取消——中止在途请求、状态复位、按钮解禁、不挂载;
③收起胶囊——生成中收起不抢占屏幕,完成后浮标亮「已生成 · 点击进入」再进入。
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
    r = ids[:6] + ["x%d" % i for i in range(6 - min(len(ids), 6))]
    return {
        "title": "工作台冒烟关",
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


def make_handle(design_delay=0.0, hang=False, invalid=False):
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
            if invalid:
                # 立即返回坏设计:两路快速烧完 3 轮,进入「10 秒后整体重试」窗口——
                # 在该窗口内点取消,避免 sync 路由处理器的 sleep 阻塞测试主线程
                route.fulfill(status=200, content_type="application/json",
                              body=json.dumps({"choices": [{"message": {"content": json.dumps({"title": "坏设计"})}}]}))
                return
            if hang:
                time.sleep(60)  # 挂起,等取消中止
                route.fulfill(status=200, content_type="application/json", body="{}")
                return
            if design_delay:
                time.sleep(design_delay)
            user_part = body["messages"][1]["content"].split("\n\n【参考关卡A")[0]
            ids = [i for i in dict.fromkeys(re.findall(r'"id"\s*:\s*"([^"]+)"', user_part))
                   if not i.startswith("result:")][:6]
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps({"choices": [{"message": {"content": json.dumps(valid_design(ids))}}]}))
        except Exception as e:
            print("  [stub] 已忽略:", str(e)[:80])

    return handle


def boot(page):
    page.route("**/api/step**", make_handle())
    page.route("**/fetch-meta**", lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps({"results": {}})))
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    page.set_input_files("#homeFile", FIXTURE)
    page.wait_for_timeout(1200)


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)

    # ===== 场景 1:正常生成,工作台全程可见(设计延迟 2.5s 让计时器可见跳动) =====
    page = b.new_page()
    page.on("pageerror", lambda e: print("[pageerror]", str(e)[:160]))
    page.route("**/api/step**", make_handle(design_delay=2.5))
    page.route("**/fetch-meta**", lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps({"results": {}})))
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    page.set_input_files("#homeFile", FIXTURE)
    page.wait_for_timeout(1200)
    # 已用时间跳动:页面内 200ms 采样器(页面时间独立于测试线程,不受 stub 阻塞影响)
    page.evaluate(
        """() => {
          window.__wbElapsedSeen = new Set();
          window.__wbSampTimer = setInterval(() => {
            const e = document.getElementById('wbElapsed');
            if (e) window.__wbElapsedSeen.add(e.textContent);
          }, 200);
        }"""
    )
    page.click("#homeGenerate")
    page.wait_for_selector("#genWorkbench:not([hidden])", timeout=10000)
    check("工作台在生成开始时出现", True)
    phases = page.evaluate("() => document.querySelectorAll('#wbPhases .wb-phase').length")
    check("阶段 stepper 渲染(5 段)", phases == 5, f"phases={phases}")
    page.wait_for_function("() => document.querySelectorAll('#wbMaterials .wb-mat').length >= 6", timeout=15000)
    mat_n, mat_href = page.evaluate(
        "() => [document.querySelectorAll('#wbMaterials .wb-mat').length,"
        " document.querySelector('#wbMaterials .wb-mat').getAttribute('href') || '']"
    )
    check("素材卡片就位且可跳转来源(≥6,带 href)", mat_n >= 6 and bool(mat_href), f"n={mat_n} href={mat_href[:50]}")
    # 小游戏:手动开启即进入纸页夜奔;工房手记开场即浮现
    page.evaluate("() => document.getElementById('wbGameToggle').click()")
    page.wait_for_timeout(300)
    game_on = page.evaluate(
        "() => !document.getElementById('wbGame').hidden"
        " && !!(window.__wbGame && window.__wbGame.isStarted())"
    )
    check("小游戏可手动开启(纸页夜奔)", game_on)
    note_shown = page.evaluate("() => document.getElementById('wbNote').classList.contains('show')")
    check("工房手记已浮现", note_shown)
    page.evaluate("() => document.getElementById('wbGameToggle').click()")
    page.wait_for_function("() => document.querySelectorAll('#wbLanes .wb-lane').length >= 2", timeout=15000)
    check("赛马实况两路就位", True)
    page.wait_for_function(
        "() => /率先通过|通过设计与求解验证/.test(document.getElementById('wbLog').textContent)",
        timeout=30000,
    )
    log_txt = page.evaluate("() => document.getElementById('wbLog').textContent")
    check("事实性日志记录赛马结果", "率先通过" in log_txt, log_txt[-80:])
    page.wait_for_function(
        "() => { const t = document.getElementById('gameToolbar');"
        " return t && !t.hasAttribute('hidden'); }",
        timeout=30000,
    )
    wb_hidden = page.evaluate("() => document.getElementById('genWorkbench').hidden")
    check("完成后挂载进游戏,工作台收起", wb_hidden)
    seen = page.evaluate(
        "() => { clearInterval(window.__wbSampTimer); return [...window.__wbElapsedSeen]; }"
    )
    check("已用时间在跳动(采样到 ≥2 个值)", len(seen) >= 2, ",".join(sorted(seen)))
    page.close()

    # ===== 场景 2:取消生成 =====
    page2 = b.new_page()
    page2.route("**/api/step**", make_handle(invalid=True))
    # glm 路也拦成坏设计:两路同时快速烧完轮次,才能进入「整体重试」窗口
    page2.route("**open.bigmodel.cn**", make_handle(invalid=True))
    page2.route("**/fetch-meta**", lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps({"results": {}})))
    page2.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page2.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    page2.set_input_files("#homeFile", FIXTURE)
    page2.wait_for_timeout(1200)
    page2.click("#homeGenerate")
    page2.wait_for_selector("#genWorkbench:not([hidden])", timeout=10000)
    page2.wait_for_function(
        "() => /整体重试/.test(document.getElementById('homeStatus').textContent)", timeout=30000
    )
    page2.evaluate("() => document.getElementById('wbCancel').click()")
    page2.wait_for_function(
        "() => /已取消/.test(document.getElementById('homeStatus').textContent)", timeout=15000
    )
    check("取消后状态行明确提示", True)
    btn_ok = page2.evaluate("() => !document.getElementById('homeGenerate').disabled")
    log_cancel = page2.evaluate("() => /已取消生成/.test(document.getElementById('wbLog').textContent)")
    check("取消后按钮解禁且日志留痕", btn_ok and log_cancel)
    time.sleep(2)
    still_home = page2.evaluate(
        "() => { const t = document.getElementById('gameToolbar');"
        " return t.hasAttribute('hidden'); }"
    )
    check("取消后不挂载关卡(2s 复查)", still_home)
    page2.close()

    # ===== 场景 3:收起胶囊,完成后点击进入 =====
    page3 = b.new_page()
    page3.route("**/api/step**", make_handle(design_delay=2.5))
    page3.route("**/fetch-meta**", lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps({"results": {}})))
    page3.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page3.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    page3.set_input_files("#homeFile", FIXTURE)
    page3.wait_for_timeout(1200)
    page3.click("#homeGenerate")
    page3.wait_for_selector("#genWorkbench:not([hidden])", timeout=10000)
    page3.evaluate("() => document.getElementById('wbMin').click()")
    pill_up = page3.evaluate(
        "() => !document.getElementById('genPill').hidden"
        " && /生成中/.test(document.getElementById('genPillText').textContent)"
    )
    check("收起后浮标显示「生成中」", pill_up)
    page3.wait_for_function(
        "() => { const p = document.getElementById('genPill');"
        " return !p.hidden && p.classList.contains('done'); }",
        timeout=30000,
    )
    still_home3 = page3.evaluate("() => document.getElementById('gameToolbar').hasAttribute('hidden')")
    check("完成时收起状态不抢占屏幕(仍在标题页)", still_home3)
    pill_text = page3.evaluate("() => document.getElementById('genPillText').textContent")
    check("浮标亮起「已生成 · 点击进入」", "已生成" in pill_text, pill_text)
    page3.evaluate("() => document.getElementById('genPill').click()")
    page3.wait_for_function(
        "() => { const t = document.getElementById('gameToolbar');"
        " return t && !t.hasAttribute('hidden'); }",
        timeout=15000,
    )
    check("点击浮标进入冒险", True)
    page3.close()

    b.close()

print(f"\n===== verify_gen_workbench: {sum(results)}/{len(results)} 通过 =====")
raise SystemExit(0 if all(results) else 1)
