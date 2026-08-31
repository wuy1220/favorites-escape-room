# -*- coding: utf-8 -*-
"""定位 pipeline.js 语法错误行列(inline script 注入,pageerror 带行列)。"""
import json
import time

from playwright.sync_api import sync_playwright

CHROME = None
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append((str(e), (getattr(e, "stack", "") or ""))))
    page.goto("http://127.0.0.1:8128/")
    page.wait_for_timeout(300)
    src = page.evaluate("async () => await (await fetch('/js/pipeline.js')).text()")
    try:
        page.add_script_tag(content=src)
    except Exception as ex:
        print("tag fail:", str(ex)[:80])
    time.sleep(0.6)
    for msg, stack in errs:
        print("ERR:", msg)
        print("STACK:", stack[:500])
    if not errs:
        print("no syntax error?!")
    b.close()
