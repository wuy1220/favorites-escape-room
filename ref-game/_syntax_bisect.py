# -*- coding: utf-8 -*-
"""二分定位 pipeline.js 语法错误:前缀编译,比较报错行号与切片行数。"""
import json

from playwright.sync_api import sync_playwright

CHROME = None
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.goto("http://127.0.0.1:8128/")
    page.wait_for_timeout(300)
    src = page.evaluate("async () => await (await fetch('/js/pipeline.js')).text()")
    lines = src.split("\n")
    offs = [0]
    for ln in lines:
        offs.append(offs[-1] + len(ln) + 1)

    def try_compile(nchars):
        return page.evaluate(
            """(src) => {
              try { new Function(src); return { line: 0, msg: 'OK' }; }
              catch (e) {
                const m = /<anonymous>:(\\d+):(\\d+)/.exec(e.stack || '');
                return { line: m ? Number(m[1]) : -1, msg: e.message };
              }
            }""",
            src[:nchars],
        )

    lo, hi = 1, len(lines)  # 疑似行号范围 [lo, hi]
    while lo < hi:
        mid = (lo + hi) // 2
        r = try_compile(offs[mid])
        err_line = r["line"]
        if err_line == 0:
            # 前缀编译通过 → 问题在后面
            lo = mid + 1
            continue
        # 有语法错误:报错行 < 切片行数 ⇒ 问题在 [lo, mid];否则(EOF 型,行号=末行)在后面
        if err_line < mid:
            hi = mid
        else:
            lo = mid + 1
    print("疑似行号:", lo)
    print(" 现场:", json.dumps(lines[lo - 1], ensure_ascii=False))
    print(" 前一行:", json.dumps(lines[lo - 2] if lo >= 2 else "", ensure_ascii=False))
    print(" 后一行:", json.dumps(lines[lo] if lo < len(lines) else "", ensure_ascii=False))
    b.close()
