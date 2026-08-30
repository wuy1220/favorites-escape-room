# -*- coding: utf-8 -*-
"""设计赛马(多路并行)回归:stub /api/step,零配额。
3 路并行设计:路1挂起 6s(后中止)、路2立即返回可解谜题、路3返回结构不合规。
断言:最快可解一路获胜并挂载关卡;输家被 externalSignal 中止(设计调用总数受控);
清洗调用不受影响。在项目根运行(需 8128 静态服务)。"""
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
    """用实际素材 id 构造一间 scenes 多层关卡(2 房间,可编译、可解,过 designWindow scenes 校验)。"""
    r = ids[:6] + ["x%d" % i for i in range(6 - min(len(ids), 6))]
    return {
        "title": "赛马冒烟关",
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
                    # 跨房间收束(2026-08-30 校验器要求):密码推导需要外间便签的提示;锁用 prop 机关
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


counts = {"clean": 0, "design": 0}


def handle(route):
    try:
        body = json.loads(route.request.post_data)
        system = body["messages"][0]["content"]
        if "整理器" in system:
            counts["clean"] += 1
            prompt = json.loads(body["messages"][1]["content"])
            out = [
                {"id": it["id"], "status": "keep", "topics": ["测试"], "reason": "复核通过", "intent": ""}
                for it in prompt.get("items", [])
            ]
            content = json.dumps({"items": out})
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps({"choices": [{"message": {"content": content}}]}))
            return
        # 设计调用:按到达序编排——第 1 路挂起 6s(将被中止),第 2 路立即有效,第 3 路不合规
        counts["design"] += 1
        n = counts["design"]
        user_part = body["messages"][1]["content"].split("\n\n【参考关卡A")[0]
        ids = re.findall(r'"id"\s*:\s*"([^"]+)"', user_part)
        ids = [i for i in dict.fromkeys(ids) if not i.startswith("result:")][:6]
        if n == 2:
            content = json.dumps(valid_design(ids))
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps({"choices": [{"message": {"content": content}}]}))
        elif n == 1:
            time.sleep(6)
            content = json.dumps({"title": "坏设计"})  # 无论如何都不会通过
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps({"choices": [{"message": {"content": content}}]}))
        else:
            content = json.dumps({"title": "不合规设计"})
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps({"choices": [{"message": {"content": content}}]}))
    except Exception as e:  # 请求被中止时 fulfill 会抛错,静默即可
        print("  [stub] 已忽略:", str(e)[:80])


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.route("**/api/step**", handle)
    # 2026-08-29 稳定性:上传路径的阶段4 desc 富化会真实抓外网(4s 超时/条),
    # 网络抖动会把清洗请求推到固定等待窗之外 —— 拦截为空结果,测的是清洗与赛马本身
    page.route("**/fetch-meta**", lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps({"results": {}})))
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)

    # 导入(清洗 stub 全 keep)→ 全局清洗 → 回落"全部通过收藏"
    page.set_input_files("#homeFile", FIXTURE)
    page.wait_for_timeout(1500)
    check("清洗调用已完成", counts["clean"] >= 1, f"clean={counts['clean']}")

    # 触发生成 → 3 路赛马
    t0 = time.time()
    page.click("#homeGenerate")
    win_status = page.wait_for_function(
        """() => {
          const t = document.getElementById('homeStatus').textContent;
          return /通过设计\\+求解验证/.test(t) ? { text: t } : null;
        }""",
        timeout=60000,
    ).json_value()["text"]
    wall = time.time() - t0
    check("最快可解一路获胜", "通过设计+求解验证" in win_status, win_status[:60])
    check("设计调用总数受控(中止生效,≤5)", counts["design"] <= 5, f"design={counts['design']}")
    check("生成耗时合理(%.1fs < 20s,含 fetch-meta)" % wall, wall < 20)
    page.wait_for_timeout(2000)
    theme_saved = page.evaluate(
        "() => new Promise((res) => { const r = indexedDB.open('favorites-escape-room-local');"
        " r.onsuccess = () => { const req = r.result.transaction('levels').objectStore('levels').getAll();"
        " req.onsuccess = () => res(req.result.length ? req.result[req.result.length - 1].theme : ''); }; })"
    )
    check("自动主题落库(调试输出)", True, repr(theme_saved) + " | status后段: " + page.evaluate("() => document.getElementById('homeStatus').textContent")[:60])
    mounted = page.evaluate(
        "() => !!document.querySelector('[data-id=\"root\"]') &&"
        " !!(window.__favoriteRoomRuntime && window.__favoriteRoomRuntime.snapshot())"
    )
    check("获胜关卡已挂载进游戏", mounted)
    # ===== 多供应商赛马:glm 路线(stub 即时可解)应击败结构不合规的 step 路线 =====
    page2 = b.new_page()
    step_design_calls = {"n": 0}

    def llm_config_stub(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "endpoint": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                "model": "glm-5.3-flash",
                "apiKey": "stub-glm",
                "thinking": {"type": "enabled"},
                "reasoningEffort": "low",
                "designTimeout": 600000,
                "label": "glm",
            }),
        )

    def glm_design_stub(route):
        body = json.loads(route.request.post_data)
        marker = '\n\n【参考关卡A'
        user_part = body["messages"][1]["content"].split(marker)[0]
        ids = [i for i in dict.fromkeys(re.findall(r'"id"\s*:\s*"([^"]+)"', user_part))
               if not i.startswith("result:")][:6]
        ids += ["g%d" % i for i in range(6 - len(ids))]
        content = json.dumps(valid_design(ids))
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"choices": [{"message": {"content": content}}]}))

    def step_invalid_stub(route):
        step_design_calls["n"] += 1
        content = json.dumps({"title": "坏设计"})  # 结构不合规 → 该路快速烧完轮次
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"choices": [{"message": {"content": content}}]}))

    page2.route("**/api/llm-config**", llm_config_stub)
    page2.route("**open.bigmodel.cn**", glm_design_stub)
    page2.route("**/api/step**", step_invalid_stub)
    page2.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page2.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    page2.wait_for_timeout(500)
    t0 = time.time()
    page2.set_input_files("#homeFile", FIXTURE)
    page2.wait_for_timeout(300)
    page2.click("#homeGenerate")
    win_status2 = page2.wait_for_function(
        """() => {
          const t = document.getElementById('homeStatus').textContent;
          return /通过设计\+求解验证/.test(t) ? { text: t } : null;
        }""",
        timeout=30000,
    ).json_value()["text"]
    wall2 = time.time() - t0
    check("多供应商赛马:glm 路获胜", "(glm)" in win_status2, win_status2[:60])
    check("多供应商赛马:step 设计调用受控(≤6)", step_design_calls["n"] <= 6,
          "step_calls=%d wall=%.1fs" % (step_design_calls["n"], wall2))
    check("多供应商赛马:耗时 %.1fs < 10s" % wall2, wall2 < 10)
    page2.close()
    b.close()

print(f"\n===== verify_design_race: {sum(results)}/{len(results)} 通过 =====")
raise SystemExit(0 if all(results) else 1)
