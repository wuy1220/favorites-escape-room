# -*- coding: utf-8 -*-
"""未命名冒险:延迟命名流程回归(stub 模型,零配额)。
生成(即时可解 scenes 设计)→ 挂载 → 触发命名面板 → 候选标题渲染 →
玩家命名 → 持久化 + 冒险回执渲染 → 刷新后列表显示命名。"""
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
    r = ids[:6] + ["g%d" % i for i in range(6 - len(ids))]
    return {
        "title": "未命名冒险(内部标题,通关前隐藏)",
        "premise": "测试。", "objective": "测试。", "targetMinutes": 10,
        "theme": "测试主题·由素材契合",
        "adventureGrammar": "变形:一句如何组织",
        "mechanics": ["密码在说明书里。"],
        "hints": ["一", "二", "三", "四", "五", "六", "七", "八"],
        "scenes": [
            {"id": "sc-a", "title": "外间", "description": "外间。", "focus": "接线盒",
             "items": [
                 {"id": r[0], "role": "tool", "sceneName": "撬棍", "reason": "能撬开东西", "digest": "一把撬棍。", "sourceFacts": []},
                 {"id": r[1], "role": "clue", "sceneName": "便签", "reason": "写着提示", "digest": "一张便签。", "sourceFacts": []},
                 {"id": r[2], "role": "clue", "sceneName": "贴纸", "reason": "贴在墙上", "digest": "一张贴纸。", "sourceFacts": [], "hidden": True}],
             "beats": [
                 {"id": "s1", "title": "看便签", "action": "inspect", "uses": [r[1]], "reveals": [r[2]]},
                 {"id": "s2", "title": "接好线路", "action": "combine", "uses": [r[0], r[1]], "product": "组合甲"}]},
            {"id": "sc-b", "title": "里间", "description": "里间。", "focus": "密码锁终端",
             "items": [
                 {"id": r[3], "role": "clue", "sceneName": "说明书", "reason": "记录步骤", "digest": "一本说明书。", "sourceFacts": []},
                 {"id": r[4], "role": "lock", "sceneName": "密码锁", "reason": "三位数字", "digest": "一台密码锁。", "sourceFacts": []},
                 {"id": r[5], "role": "reward", "sceneName": "钥匙卡", "reason": "出口凭证", "hidden": True, "digest": "一张钥匙卡。", "sourceFacts": []}],
             "beats": [
                 {"id": "s3", "title": "读说明书", "action": "inspect", "uses": [r[3]]},
                 {"id": "s4", "title": "输密码", "action": "password", "uses": [r[4]], "expected": "123",
                  "requires": ["s1"], "reveals": [r[5]]},
                 {"id": "s5", "title": "交付离开", "action": "deliver", "uses": [r[5]], "requires": ["s4"]}]},
        ],
    }


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.on("pageerror", lambda e: print("[pageerror]", str(e)[:160]))

    def stub(route):
        body = json.loads(route.request.post_data)
        system = body["messages"][0]["content"]
        if "整理器" in system:
            prompt = json.loads(body["messages"][1]["content"])
            out = [{"id": it["id"], "status": "keep", "topics": ["t"], "reason": "r", "intent": ""}
                   for it in prompt.get("items", [])]
            content = json.dumps({"items": out})
        else:
            user_part = body["messages"][1]["content"].split("\n\n【参考关卡A")[0]
            ids = [i for i in dict.fromkeys(re.findall(r'"id"\s*:\s*"([^"]+)"', user_part))
                   if not i.startswith("result:")][:6]
            content = json.dumps(valid_design(ids))
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"choices": [{"message": {"content": content}}]}))

    def titles_stub(route):
        route.fulfill(status=200, content_type="application/json", body=json.dumps(
            {"choices": [{"message": {"content": json.dumps(
                {"titles": ["直白式标题", "隐喻式标题", "意识流式标题"]})}}]}))

    page.route("**/api/step**", stub)
    page.route("**open.bigmodel.cn**", titles_stub)
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)

    page.set_input_files("#homeFile", FIXTURE)
    page.wait_for_timeout(1500)
    page.click("#homeGenerate")
    page.wait_for_function(
        "() => document.getElementById('gameToolbar') && !document.getElementById('gameToolbar').hasAttribute('hidden')",
        timeout=30000,
    )
    check("生成并挂载(内部标题隐藏)", True)

    lv = page.evaluate(
        "() => new Promise((res) => { const r = indexedDB.open('favorites-escape-room-local');"
        " r.onsuccess = () => { const q = r.result.transaction('levels').objectStore('levels').getAll();"
        " q.onsuccess = () => res(q.result[q.result.length - 1] || {}); }; })"
    )
    check("挂载时为未命名(中性编号)", str(lv.get("name", "")).startswith("未命名冒险"),
          str(lv.get("name")))
    desc_n = page.evaluate(
        "() => new Promise((res) => { const r = indexedDB.open('favorites-escape-room-local');"
        " r.onsuccess = () => { const q = r.result.transaction('verdicts').objectStore('verdicts').getAll();"
        " q.onsuccess = () => res(q.result.filter((v) => v.desc && v.desc.trim()).length); }; })"
    )
    check("desc 富化:verdict store 有非空 desc(≥1)", desc_n >= 1, f"desc_n={desc_n}")
    check("LLM 内部标题已隐藏保存", bool(lv.get("llmTitle")), str(lv.get("llmTitle"))[:40])

    page.evaluate("(id) => window.__favoriteRoomHome.openNamingFlow(id)", lv["id"])
    page.wait_for_selector("#namingModal:not(.hidden)", timeout=5000)
    page.wait_for_timeout(400)
    cand = page.evaluate("() => document.querySelectorAll('#nameCandidates .window-card').length")
    check("候选标题渲染 3 个", cand == 3, f"cand={cand}")
    check("命名面板可见且输入框就绪",
          page.evaluate("() => document.getElementById('namingModal').classList.contains('hidden') === false"))

    page.fill("#adventureNameInput", "我的旧电脑之夜")
    page.click("#adventureNameSave")
    page.wait_for_timeout(500)
    receipt = page.evaluate(
        "() => { const r = document.getElementById('adventureReceipt');"
        " return { shown: r.style.display !== 'none', text: r.textContent.slice(0, 120) }; }"
    )
    check("冒险回执渲染(事实→化身)", receipt["shown"] and "←" in receipt["text"],
          receipt["text"][:90])
    named = page.evaluate(
        "() => new Promise((res) => { const r = indexedDB.open('favorites-escape-room-local');"
        " r.onsuccess = () => { const q = r.result.transaction('levels').objectStore('levels').getAll();"
        " q.onsuccess = () => res(q.result[q.result.length - 1].name); }; })"
    )
    check("命名已持久化", named == "我的旧电脑之夜", str(named))
    gt = page.evaluate("() => document.getElementById('gameTitle').textContent")
    check("游戏工具栏标题同步", gt == "我的旧电脑之夜", gt)

    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    page.wait_for_timeout(800)
    rows = page.evaluate(
        "() => Array.from(document.querySelectorAll('#savedList .saved-row strong')).map((e) => e.textContent)"
    )
    check("刷新后列表显示玩家命名", any("我的旧电脑之夜" in x for x in rows), json.dumps(rows, ensure_ascii=False)[:100])
    b.close()

print(f"\n===== verify_naming_flow: {sum(results)}/{len(results)} 通过 =====")
raise SystemExit(0 if all(results) else 1)
