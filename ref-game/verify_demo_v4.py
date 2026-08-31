# -*- coding: utf-8 -*-
"""三关 v4 重设计验证:
1. solveLevel 全部可解;
2. 防跳锁:删掉任一中间 beat(或清空其 uses)后必须不可解——证明每步都在链上;
3. 链覆盖:deliver 的 requires 传递闭包必须包含全部非 reward beats。"""
import copy
import json
import os
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHROME = None
FILES = ["demo-gamenight", "demo-toolbox", "demo-selfstudy"]
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))


LEVELS = {}
for f in FILES:
    LEVELS[f] = json.load(open(os.path.join(ROOT, "sample-puzzles", f + ".room.json"), encoding="utf-8"))


def req_closure(lv):
    """deliver 的 requires 传递闭包(经 requires 边)"""
    beats = {b["id"]: b for b in lv["beats"]}
    deliver = [b for b in lv["beats"] if b["action"] == "deliver"]
    seen, stack = set(), [r for b in deliver for r in b.get("requires", [])]
    while stack:
        cur = stack.pop()
        if cur in seen or cur not in beats:
            continue
        seen.add(cur)
        stack.extend(beats[cur].get("requires", []))
    return seen


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function(
        "() => !!(window.__favoriteRoomPipeline && window.__favoriteRoomPipeline.solveLevel)",
        timeout=15000,
    )
    for name, payload in LEVELS.items():
        lv = payload["level"]
        r = page.evaluate("lv => window.__favoriteRoomPipeline.solveLevel(lv)", lv)
        check(f"{name} 可解", bool(r.get("solvable")), str(r.get("detail"))[:120])
        beats_n = len(lv["beats"])
        locks = [b for b in lv["beats"] if b["action"] == "password"]
        seqs = [b for b in lv["beats"] if b["action"] == "sequence"]
        combs = [b for b in lv["beats"] if b["action"] == "combine"]
        print(f"    beats={beats_n} password={len(locks)} sequence={len(seqs)} combine={len(combs)}")

        # 防跳锁:链上每个非 deliver 步骤都应被 deliver 闭包覆盖
        needed = {b["id"] for b in lv["beats"] if b["action"] != "deliver"}
        covered = req_closure(lv)
        uncovered = needed - covered
        check(f"{name} deliver 闭包覆盖全部前序步骤", not uncovered, "未覆盖: " + ",".join(sorted(uncovered)) if uncovered else "")

        # 防跳锁实证:逐个把中间步骤的 uses 清空,必须不可解
        all_blocked = True
        for b0 in lv["beats"]:
            if b0["action"] == "deliver":
                continue
            bad = copy.deepcopy(lv)
            tgt = next(x for x in bad["beats"] if x["id"] == b0["id"])
            tgt["uses"] = []
            rr = page.evaluate("lv => window.__favoriteRoomPipeline.solveLevel(lv)", bad)
            if rr.get("solvable"):
                all_blocked = False
                check(f"{name} 跳过 {b0['id']} 仍可解(坏!)", False, "该步不在链上")
                break
        if all_blocked:
            check(f"{name} 每个中间步骤都不可跳过", True)
    b.close()

print(f"\n===== 三关 v4 验证: {sum(results)}/{len(results)} 通过 =====")
raise SystemExit(0 if all(results) else 1)
