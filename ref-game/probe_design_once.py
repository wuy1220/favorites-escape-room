# -*- coding: utf-8 -*-
"""单发探针:真实调用一次 designWindow(GLM 路只此一家),计时并检查编译后结构。
回答:加硬的收束约束是否把设计调用拖过了 160s 预算。"""
import json
import os
import time

from playwright.sync_api import sync_playwright

CHROME = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "fixtures", "sample10-bookmarks.html")

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.on(
        "console",
        lambda m: print("  [rep]", m.text[:90])
        if any(k in m.text for k in ("设计", "校验", "通过", "重试", "失败"))
        else None,
    )
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    cfg = page.evaluate("() => fetch('http://127.0.0.1:8128/api/llm-config').then((r) => r.json())")
    raw = open(FIXTURE, encoding="utf-8").read()
    t0 = time.time()
    result = page.evaluate(
        """async ([raw, cfg]) => {
          const pipe = window.__favoriteRoomPipeline;
          const items = pipe.parse(raw, 'sample.html');
          const cleaned = pipe.clean(items);
          const approved = cleaned.records.filter((r) => r.status === 'keep').slice(0, 6);
          try {
            const won = await pipe.designWindow(approved, '', null, [], (m) => console.log('[rep] ' + m), '', null, cfg);
            const compiled = pipe.compile(cleaned, null, won.parsed, '');
            const lvl = compiled.level;
            const sceneOf = new Map();
            (lvl.scenes || []).forEach((sc, si) => (sc.beatIds || []).forEach((x) => sceneOf.set(x, si)));
            const del = (lvl.beats || []).find((x) => x.action === 'deliver');
            const reach = new Set(), seen = new Set(), stack = [String(del ? del.id : '')];
            while (stack.length) {
              const id = stack.pop();
              if (!id || seen.has(id)) continue;
              seen.add(id);
              if (sceneOf.has(id)) reach.add(sceneOf.get(id));
              const bb = (lvl.beats || []).find((x) => String(x.id) === id);
              ((bb && bb.requires) || []).forEach((r) => { if (sceneOf.has(String(r))) stack.push(String(r)); });
            }
            return {ok: true, title: lvl.title, theme: lvl.theme, scenes: (lvl.scenes || []).map((s) => s.title),
                    beats: (lvl.beats || []).length, closure: reach.size,
                    locked: (lvl.scenes || []).filter((s) => s.locked).length};
          } catch (e) {
            return {ok: false, error: String(e && e.message || e).slice(0, 200)};
          }
        }""",
        [raw, cfg],
    )
    print("耗时 %.0fs" % (time.time() - t0))
    print(json.dumps(result, ensure_ascii=False, indent=1))
    b.close()
