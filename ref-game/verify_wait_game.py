# -*- coding: utf-8 -*-
"""纸页夜奔碰撞回归(2026-08-30,零配额):
用 __wbGame.__debug 单步驱动逻辑步,证明失败判定真实生效——
①撞上障碍扣墨;②跳跃可越过障碍(不扣);③收集纸页生效并解锁手记;
④三滴墨耗尽 → 本局结束;⑤重开恢复初始。
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
        "title": "夜奔冒烟关",
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
        if "整理器" in body["messages"][0]["content"]:
            prompt = json.loads(body["messages"][1]["content"])
            out = [
                {"id": it["id"], "status": "keep", "topics": ["测试"], "reason": "复核通过", "intent": ""}
                for it in prompt.get("items", [])
            ]
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps({"choices": [{"message": {"content": json.dumps({"items": out})}}]}))
            return
        time.sleep(90)  # 比全部游戏场景更久:防止 wbFinish 在场景中途停掉游戏
        user_part = body["messages"][1]["content"].split("\n\n【参考关卡A")[0]
        ids = [i for i in dict.fromkeys(re.findall(r'"id"\s*:\s*"([^"]+)"', user_part))
               if not i.startswith("result:")][:6]
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"choices": [{"message": {"content": json.dumps(valid_design(ids))}}]}))
    except Exception as e:
        print("  [stub] 已忽略:", str(e)[:80])


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.on("pageerror", lambda e: print("[pageerror]", str(e)[:160]))
    page.route("**/api/step**", handle)
    page.route("**/fetch-meta**", lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps({"results": {}})))
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    page.set_input_files("#homeFile", FIXTURE)
    page.wait_for_timeout(1200)
    page.evaluate("() => document.getElementById('homeGenerate').click()")
    page.wait_for_selector("#genWorkbench:not([hidden])", timeout=10000)
    page.evaluate("() => document.getElementById('wbGameToggle').click()")
    page.wait_for_function("() => window.__wbGame && window.__wbGame.isStarted()", timeout=10000)
    # 开场即冻结自然生成:场景间隙 rAF 实时运行,自然障碍会干扰确定性模拟
    page.evaluate(
        """() => {
          const D = window.__wbGame.__debug;
          if (D.S.gameOver) D.restart();
          D.S.nextObsD = 1e9;
          D.S.nextColD = 1e9;
        }"""
    )
    check("游戏已开启(工作台内)", True)

    # ===== ① 命中判定:障碍推到跑者正前方,驱动 80 逻辑步必须扣墨 =====
    st = page.evaluate(
        """() => {
          const D = window.__wbGame.__debug, S = D.S;
          S.obs.length = 0; S.cols.length = 0; S.inv = 0; S.runner.dead = 0; S.nextObsD = 1e9; S.nextColD = 1e9;
          D.spawnObstacle(); S.obs[0].k = 'ink'; S.obs[0].x = S.runner.x + 40;
          const lives0 = S.lives;
          D.run(80);
          return { lives0, ...D.state() };
        }"""
    )
    check("① 前置:局面存活", st["lives0"] == 3 and not st["gameOver"], json.dumps(st))
    check("① 撞上障碍扣墨(%d→%d)" % (st["lives0"], st["lives"]), st["lives"] < st["lives0"], json.dumps(st))

    # ===== ② 跳跃可越过障碍:等无敌帧结束,障碍放 70px 前方,起跳后 140 步不扣墨 =====
    st = page.evaluate(
        """() => {
          const D = window.__wbGame.__debug, S = D.S;
          let guard = 0;
          while ((S.inv > 0 || S.runner.dead > 0) && guard++ < 200) D.logicStep();
          S.obs.length = 0; S.cols.length = 0; S.nextObsD = 1e9; S.nextColD = 1e9;
          D.spawnObstacle(); S.obs[0].k = 'ink'; S.obs[0].x = S.runner.x + 70;
          const lives0 = S.lives;
          /* 直接置跳态:本场景验证抛物线几何能否越过障碍,不经 running 守卫 */
          S.runner.vy = -7.8;
          S.runner.onGround = false;
          D.run(140);
          return { lives0, ...D.state(), guard };
        }"""
    )
    check("② 前置:局面存活且已置跳态", st["lives0"] > 0 and not st["gameOver"] and st["guard"] < 200, json.dumps(st))
    check("② 跳跃越过障碍不扣墨(墨量保持 %d)" % st["lives0"], st["lives"] == st["lives0"], json.dumps(st))

    # ===== ③ 收集纸页:纸页放在脚下,30 步内收集并解锁手记 =====
    st = page.evaluate(
        """() => {
          const D = window.__wbGame.__debug, S = D.S;
          S.obs.length = 0; S.cols.length = 0; S.nextObsD = 1e9; S.nextColD = 1e9;
          D.spawnCollectible(); S.cols[0].x = S.runner.x + 10; S.cols[0].y = S.groundY - 14;
          const pages0 = S.pages;
          D.run(30);
          return { pages0, ...D.state() };
        }"""
    )
    check("③ 前置:局面存活", not st["gameOver"], json.dumps(st))
    check("③ 收集纸页生效(%d→%d)" % (st["pages0"], st["pages"]), st["pages"] > st["pages0"], json.dumps(st))

    # ===== ④ 墨尽本局结束:只剩一滴墨时命中 → gameOver =====
    st = page.evaluate(
        """() => {
          const D = window.__wbGame.__debug, S = D.S;
          while (S.inv > 0 || S.runner.dead > 0) D.logicStep();
          S.obs.length = 0; S.cols.length = 0; S.lives = 1; S.inv = 0; S.nextObsD = 1e9; S.nextColD = 1e9;
          D.spawnObstacle(); S.obs[0].k = 'tape'; S.obs[0].x = S.runner.x + 30;
          D.run(60);
          return D.state();
        }"""
    )
    check("④ 墨尽本局结束(gameOver)", st["gameOver"] and st["lives"] == 0, json.dumps(st))

    # ===== ⑤ 重开恢复初始 =====
    st = page.evaluate(
        """() => {
          const D = window.__wbGame.__debug;
          D.restart();
          return D.state();
        }"""
    )
    check("⑤ 重开恢复初始(3 滴墨,非结束)", st["lives"] == 3 and not st["gameOver"], json.dumps(st))

    b.close()

print(f"\n===== verify_wait_game: {sum(results)}/{len(results)} 通过 =====")
raise SystemExit(0 if all(results) else 1)
