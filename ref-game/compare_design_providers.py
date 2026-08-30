# -*- coding: utf-8 -*-
"""双路设计重放对比(同一份真实请求体):
A. step-advisor:本地 server /api/step(router-force,修复后 max_tokens 64000)
B. glm-5.3-flash:bigmodel 直连,reasoning_effort low
各自计时,返回的设计喂进 compileLevel+solveLevel 验证可解性。"""
import json
# 密钥由本地 server 持有(server/GLM_API_KEY.local),运行时从 /api/llm-config 拉取;
# 不得在代码中硬编码(公开仓库安全要求,2026-08-31)。
import urllib.request as _uq
GLM_KEY = json.loads(_uq.urlopen("http://127.0.0.1:8128/api/llm-config").read())["apiKey"]

import json
import threading
import time

import urllib.request

BODY = json.load(open("ref-game/llm_out/design_body_now.json", encoding="utf-8"))
results = {}


def post(url, body, timeout, headers):
    req = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                 headers=headers)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    return time.time() - t0, d


def extract_design(content):
    """从 content 提取设计 JSON(兼容 advisor 前缀/包裹)。"""
    try:
        d = json.loads(content)
        return d.get("level", d)
    except Exception:
        pass
    i, j = content.find("{"), content.rfind("}")
    if i >= 0 and j > i:
        try:
            d = json.loads(content[i:j + 1])
            return d.get("level", d)
        except Exception:
            return None
    return None


def lane_step():
    try:
        wall, d = post("http://127.0.0.1:8128/api/step", BODY, 900,
                       {"Content-Type": "application/json"})
        content = (d.get("choices") or [{}])[0].get("message", {}).get("content", "")
        finish = (d.get("choices") or [{}])[0].get("finish_reason")
        results["step"] = {"wall": wall, "finish": finish, "chars": len(content),
                           "content": content, "advisor": "[Advisor consultation" in content}
    except Exception as e:
        results["step"] = {"error": str(e)[:160], "wall": time.time() - t0_global}


def lane_glm():
    try:
        body = dict(BODY)
        body["model"] = "glm-5.3-flash"
        body["reasoning_effort"] = "low"
        body.pop("thinking", None)
        wall, d = post("https://open.bigmodel.cn/api/paas/v4/chat/completions", body, 900,
                       {"Content-Type": "application/json",
                        "Authorization": "Bearer " + GLM_KEY})
        content = (d.get("choices") or [{}])[0].get("message", {}).get("content", "")
        finish = (d.get("choices") or [{}])[0].get("finish_reason")
        results["glm"] = {"wall": wall, "finish": finish, "chars": len(content),
                          "content": content}
    except Exception as e:
        results["glm"] = {"error": str(e)[:160]}


t0_global = time.time()
threads = [threading.Thread(target=lane_step), threading.Thread(target=lane_glm)]
for t in threads:
    t.start()
for t in threads:
    t.join(timeout=900)

open("ref-game/llm_out/design_step_response.txt", "w", encoding="utf-8").write(
    (results.get("step") or {}).get("content", "") or str(results.get("step")))
open("ref-game/llm_out/design_glm_response.txt", "w", encoding="utf-8").write(
    (results.get("glm") or {}).get("content", "") or str(results.get("glm")))

for k in ("step", "glm"):
    r = results.get(k, {})
    if "error" in r:
        print(f"[{k}] 失败({r['wall']:.0f}s): {r['error']}")
    else:
        print(f"[{k}] {r['wall']:.1f}s finish={r['finish']} content={r['chars']} 字符"
              + (" advisor块" if r.get("advisor") else ""))

# 设计可解性验证(浏览器内 compile+solve)
designs = {k: extract_design(results[k]["content"]) for k in ("step", "glm") if results.get(k, {}).get("content")}
json.dump(designs, open("ref-game/llm_out/design_race_compare.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("designs saved: " + ", ".join(f"{k}={'有' if v else '无'}" for k, v in designs.items()))

# 可解性验证:每份设计喂进 compileLevel+solveLevel
from playwright.sync_api import sync_playwright

CHROME = r"C:/Users/30807/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    for k, d in designs.items():
        if not d:
            continue
        r = page.evaluate(
            """(design) => {
              const pipe = window.__favoriteRoomPipeline;
              const scenesIn = Array.isArray(design.scenes) ? design.scenes : null;
              const items = scenesIn
                ? scenesIn.flatMap((s) => s.items || [])
                : (design.items || []);
              const records = items.map((it) => ({
                id: it.id, title: it.scene_name || it.sceneName || it.id,
                domain: 'example.com', url: 'https://example.com/' + it.id,
                dateAdded: new Date().toISOString(), status: 'keep', folder: '对比',
              }));
              const cleaned = {records, controlledIds: records.map((r) => r.id), duplicates: [],
                               stats: {input: records.length, unique: records.length, duplicates: 0}};
              try {
                const draft = pipe.compile(cleaned, null, design, '对比');
                const solve = pipe.solveLevel(draft.level);
                return {ok: true, scenes: (draft.level.scenes || []).length,
                        beats: draft.level.beats.length,
                        designSource: draft.level.validation.designSource,
                        solvable: !!solve.solvable, detail: String(solve.detail || '').slice(0, 80)};
              } catch (e) {
                return {ok: false, err: String(e && e.message || e).slice(0, 100)};
              }
            }""",
            d,
        )
        if r.get("ok"):
            print(f"[{k}] 可解性: scenes={r['scenes']} beats={r['beats']} 来源={r['designSource']} 可解={r['solvable']} {r['detail']}")
        else:
            print(f"[{k}] 编译失败: {r.get('err')}")
    b.close()
