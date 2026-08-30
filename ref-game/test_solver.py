# -*- coding: utf-8 -*-
"""solveLevel 求解器单元测试:
- prison/clockwork/bear-code(手写范例,真实 DOM 已知可通关)→ 求解器必须判可解;
- 坏档(某步 uses:[])→ 求解器必须判不可解并指出卡点。"""
import json
import os
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHROME = r"C:/Users/30807/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"
results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))

LEVELS = {}
for f in ('prison', 'clockwork', 'bear-code'):
    path = os.path.join(ROOT, 'sample-puzzles', f'{f}.room.json')
    LEVELS[f] = json.load(open(path, encoding='utf-8'))['level']
# 坏档:优先用历史用户生成物;不存在就现合一个等价坏档(把 prison 的一个中间步 uses 清空),
# 不再依赖易变的下载目录文件。
broken = os.path.join(os.path.expanduser('~'), 'Downloads',
                      '折镜蝶与计算器代码：2024年春末的深夜收藏卷宗.room.json')
if os.path.exists(broken):
    LEVELS['user-broken'] = json.load(open(broken, encoding='utf-8'))['level']
else:
    import copy
    synth = copy.deepcopy(LEVELS['prison'])
    mid = next(b for b in synth['beats'] if b['action'] not in ('deliver',))
    mid['uses'] = []
    LEVELS['user-broken'] = synth
# 合成的锁/观察重叠样本(不依赖易变的生成物文件):morse 锁装在被观察的 b0 上
LEVELS['v7-r1-lockconflict'] = {
    "items": [{"id": f"b{i}"} for i in range(6)],
    "beats": [
        {"id": "s1", "title": "看b0", "action": "inspect", "uses": ["b0"]},
        {"id": "s2", "title": "摩斯锁", "action": "morse", "uses": ["b0"], "code": "...--", "requires": ["s1"]},
        {"id": "s3", "title": "交付", "action": "deliver", "uses": ["b1"], "requires": ["s2"]},
    ],
}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!(window.__favoriteRoomPipeline && window.__favoriteRoomPipeline.solveLevel)", timeout=15000)
    for name, lv in LEVELS.items():
        r = page.evaluate("lv => window.__favoriteRoomPipeline.solveLevel(lv)", lv)
        if name == 'v7-r1-lockconflict':
            check(f"{name} 判不可解(锁/观察重叠)", not r.get("solvable"), str(r.get("detail"))[:110])
        elif name == 'user-broken':
            check(f"{name} 判不可解", not r.get("solvable"), str(r.get("detail"))[:110])
            check(f"{name} 卡点指向空 uses 步", '没有交互物件' in str(r.get("detail", "")), str(r.get("detail"))[:110])
        else:
            check(f"{name} 判可解", bool(r.get("solvable")), f"steps={r.get('steps')} {r.get('detail','')}"[:110])
    b.close()
print(f"\n===== test_solver: {sum(results)}/{len(results)} 通过 =====")
raise SystemExit(0 if all(results) else 1)
