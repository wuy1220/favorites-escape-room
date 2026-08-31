# -*- coding: utf-8 -*-
"""一次性探针:真实设计一轮,转储原始设计(数据集缓存)与编译关卡的
scenes[].beatIds / beats[].requires,核对跨房间收束在编译后是否丢失。"""
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

CHROME = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "fixtures", "sample10-bookmarks.html")

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.on("pageerror", lambda e: print("[pageerror]", str(e)[:160]))
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    t0 = time.time()
    page.set_input_files("#homeFile", FIXTURE)
    page.wait_for_function(
        "() => !document.getElementById('homeGenerate').disabled", timeout=60000
    )
    # 清掉本轮设计缓存,强制真实设计
    page.evaluate(
        "() => new Promise((res) => { const r = indexedDB.open('favorites-escape-room-local');"
        " r.onsuccess = () => { const tx = r.result.transaction('datasets','readwrite');"
        " tx.objectStore('datasets').clear(); tx.oncomplete = () => res(null); }; })"
    )
    page.click("#homeGenerate")
    deadline = time.time() + 300
    while time.time() < deadline:
        time.sleep(5)
        tb = page.evaluate(
            "() => { const t = document.getElementById('gameToolbar');"
            " return t && !t.hasAttribute('hidden'); }"
        )
        if tb:
            break
    print("挂载耗时 %.0fs" % (time.time() - t0), flush=True)
    lv = page.evaluate(
        "() => new Promise((res) => { const r = indexedDB.open('favorites-escape-room-local');"
        " r.onsuccess = () => { const q = r.result.transaction('levels').objectStore('levels').getAll();"
        " q.onsuccess = () => res(q.result[q.result.length - 1] || {}); }; })"
    )
    lvl = (lv.get("draft") or {}).get("level", {})
    dump = {
        "title": lvl.get("title"),
        "designSource": (lvl.get("validation") or {}).get("designSource"),
        "scenes": [
            {"id": s.get("id"), "title": s.get("title"), "locked": s.get("locked"),
             "lockedBy": s.get("lockedBy"), "beatIds": s.get("beatIds"),
             "itemIds": s.get("itemIds")}
            for s in (lvl.get("scenes") or [])
        ],
        "beats": [
            {"id": x.get("id"), "action": x.get("action"), "uses": x.get("uses"),
             "requires": x.get("requires")}
            for x in (lvl.get("beats") or [])
        ],
        "debug": page.evaluate("() => window.__lastDesignDebug || null"),
        "items_desc": [
            {"id": it.get("id"), "desc": (it.get("description") or "")[:60]}
            for it in (lvl.get("items") or [])
        ],
    }
    out = os.path.join(ROOT, "ref-game", "llm_out", "probe_compile_dump.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(dump, f, ensure_ascii=False, indent=1)
    print("dump ->", out)
    print(json.dumps(dump["scenes"], ensure_ascii=False)[:400])
    for x in dump["beats"]:
        print(" ", x["id"], x["action"], "req=", x["requires"])
    b.close()
