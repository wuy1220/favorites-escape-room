# -*- coding: utf-8 -*-
"""用户素材探针:6 条真实书签 → 服务端 desc 回访 → 真实 designWindow。
检查:谜面(reason)是否引用网页真实内容、房间 title 是否为场所名。"""
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

CHROME = r"C:/Users/30807/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "fixtures", "user6-bookmarks.json")

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    cfg = page.evaluate("() => fetch('http://127.0.0.1:8128/api/llm-config').then((r) => r.json())")
    raw = open(FIXTURE, encoding="utf-8").read()
    t0 = time.time()
    result = page.evaluate(
        """async ([raw, cfg]) => {
          const pipe = window.__favoriteRoomPipeline;
          const items = pipe.parse(raw, 'user6.json');
          const cleaned = pipe.clean(items);
          const approved = cleaned.records.filter((r) => r.status === 'keep').slice(0, 6);
          /* 与 app.js 同款 desc 回访:服务端 /fetch-meta,结果写进 records.description */
          try {
            const res = await fetch('http://127.0.0.1:8128/fetch-meta', {
              method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ urls: approved.map((t) => t.url), timeout: 6 }),
            });
            const data = await res.json();
            approved.forEach((t) => {
              const m = (data.results || {})[t.url];
              if (m && m.desc) t.description = m.desc.slice(0, 300);
            });
          } catch (e) { /* 忽略:与产品一致,抓取失败无害 */ }
          const descN = approved.filter((r) => (r.description || '').trim()).length;
          let won = null, note = '', lastErr = null;
          for (let round = 0; round < 3 && !won; round++) {
            try {
              won = await pipe.designWindow(approved, '', null, [], null, note, null, cfg);
            } catch (e) {
              lastErr = String(e && e.message || e);
              if (/重试|retry/.test(lastErr)) break;
              note = lastErr;
            }
          }
          if (!won) return {ok: false, descN, error: (lastErr || '设计失败').slice(0, 220)};
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
          return {ok: true, descN,
            sceneTitles: (lvl.scenes || []).map((s) => s.title),
            reasons: (lvl.items || []).map((it) => ({n: it.sceneName, r: it.reason,
              d: it.digest || '', f: it.facts || [], g: it.grounding || ''})),
            objective: lvl.objective, closure: reach.size,
            locked: (lvl.scenes || []).filter((s) => s.locked).length};
        }""",
        [raw, cfg],
    )
    print("耗时 %.0fs" % (time.time() - t0))
    print(json.dumps(result, ensure_ascii=False, indent=1))
    b.close()
