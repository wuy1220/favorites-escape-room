# -*- coding: utf-8 -*-
"""真实端到端:示例书签 → Step 清洗 → LLM 关卡设计(经 router-force 代理)→ 导出 .room.json

用法:python live_generate.py [fixture_html] [theme]
"""
import json
import os
import sys
import time
from playwright.sync_api import sync_playwright

CHROME = r"C:\Users\30807\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "fixtures", "sample10-bookmarks.html")
THEME = sys.argv[2] if len(sys.argv) > 2 else ""
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "sample-puzzles", "generated-live.room.json")
BASE = "http://127.0.0.1:8130/"

raw = open(FIXTURE, encoding="utf-8").read()
logs = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=CHROME)
    page = browser.new_page(viewport={"width": 1440, "height": 1200})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: logs.append(m.text) if m.text.startswith("[gen]") else None)
    page.set_default_timeout(320000)
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    # 把清洗弹窗里的 endpoint 指到本实例(router-force 新代码)
    page.evaluate("(v)=>{const el=document.getElementById('cleanEndpoint'); if(el) el.value=v}",
                  BASE.rstrip('/') + "/api/step")
    t0 = time.time()
    result = page.evaluate(
        """async ([raw, theme]) => {
            try {
              const r = await window.__favoriteRoomPipeline.generate(raw, 'sample.html', theme,
                  m => console.log('[gen]', m));
              return {ok:true, draft:r.draft, model:r.model};
            } catch (e) {
              return {ok:false, error:String(e && e.message || e),
                      debug: window.__lastDesignDebug || null};
            }
        }""",
        [raw, THEME],
    )
    dt = time.time() - t0
    print(f"生成耗时 {dt:.0f}s ok={result['ok']} model={result.get('model')}")
    for line in logs:
        print("  ", line)
    if not result["ok"]:
        print("失败:", result["error"], result.get("debug"))
        browser.close()
        sys.exit(1)
    level = result["draft"]["level"]
    items = result["draft"]["items"]
    scenes = level.get("scenes") or []
    print(f"关卡《{level['title']}》 scenes={len(scenes)} beats={len(level['beats'])} "
          f"hints={len(level.get('hints') or [])}")
    print("mechanics:", level.get("mechanics"))
    print("designSource:", (level.get("validation") or {}).get("designSource"),
          "issues:", (level.get("validation") or {}).get("issues"))
    print("beats:")
    for b in level["beats"]:
        extra = {k: b[k] for k in ("expected", "angles", "precision", "code") if k in b and b[k] not in (None, "", [], 30)}
        print(f"  {b['id']} [{b['action']}] uses={b['uses']} req={b.get('requires')} "
              f"{('reveals=' + str(b.get('reveals'))) if b.get('reveals') else ''} {extra if extra else ''}")
    puzzle = {"items": items, "controlledIds": [it["id"] for it in items], "level": level}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(puzzle, f, ensure_ascii=False, indent=2)
    print("已导出:", OUT)
    if errors:
        print("页面错误:", errors[:3])
    browser.close()
