# -*- coding: utf-8 -*-
"""诊断 v2:节点飞入的起点 与 连接线的起点 是否同一处。

不依赖内部 state,纯 DOM 反推:
  起飞点(节点) = 槽位中心 + (--fx, --fy)          ← arrive 关键帧的 from 位移
  起飞点(连线) = 该节点对应 line 的 (x1,y1)        ← drawLinks 的父锚点
两者一致 → 同拍同向;不一致 → 观感割裂。
"""
from pathlib import Path
import time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8128/"
PUZZLE = str(Path(__file__).resolve().parents[1] / "sample-puzzles" / "prison.room.json")
CHROME = None

SAMPLER = r"""
() => {
  window.__f = [];
  let i = 0;
  const tick = () => {
    const rows = [...document.querySelectorAll('.node')].map(el => ({
      id: el.dataset.id,
      arr: el.classList.contains('arrive'),
      sx: Math.round(el.offsetLeft + el.offsetWidth / 2),
      sy: Math.round(el.offsetTop + el.offsetHeight / 2),
      w: Math.round(el.offsetWidth), h: Math.round(el.offsetHeight),
      fx: el.style.getPropertyValue('--fx').trim(),
      fy: el.style.getPropertyValue('--fy').trim(),
      fd: el.style.getPropertyValue('--fd').trim(),
      anim: el.getAnimations().map(a => (a.animationName || '?') + ':' + Math.round(a.currentTime || 0)).join(','),
    }));
    const lines = [...document.querySelectorAll('#links line')].map(l => ({
      x1: Math.round(+l.getAttribute('x1')), y1: Math.round(+l.getAttribute('y1')),
      x2: Math.round(+l.getAttribute('x2')), y2: Math.round(+l.getAttribute('y2')),
    }));
    window.__f.push({ f: i, rows, lines });
    if (++i < 30) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}
"""


def click(page, sel):
    b = page.locator(sel).first.bounding_box()
    assert b, f"不可点击 {sel}"
    page.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)


def run(page, label, sel):
    page.evaluate(SAMPLER)
    click(page, sel)
    time.sleep(0.9)
    frames = page.evaluate("() => window.__f")

    # 起飞帧 = 第一个存在「刚起步」arrive 动画的帧(currentTime 很小),
    # 忽略上一轮残留的 .arrive 类(动画已跑完,currentTime≈500)
    def fresh(f):
        return any(
            r["arr"] and (not r["anim"] or any(x.split(":")[1].isdigit() and int(x.split(":")[1]) <= 40 for x in r["anim"].split(",")))
            for r in f["rows"]
        )

    start = next((f for f in frames if fresh(f)), None)
    end = frames[-1]
    print(f"\n{'=' * 92}\n{label}  (点击 {sel})\n{'=' * 92}")
    if not start:
        print("  未捕获到 .arrive 节点")
        return
    slots = {r["id"]: (r["sx"], r["sy"]) for r in end["rows"]}

    def nearest(pt, skip):
        cands = sorted(
            (abs(v[0] - pt[0]) + abs(v[1] - pt[1]), k) for k, v in slots.items() if k != skip
        )
        return cands[0] if cands else (None, "?")

    print(f"  帧{start['f']} 起飞。节点槽位 / 起飞点 / 连线起点:")
    for r in start["rows"]:
        if not r["arr"]:
            continue
        s = slots.get(r["id"])
        if not s:
            continue
        if not r["fx"] or not r["fy"]:
            fly = s  # 未设 --fx/--fy → 原地浮现
            how = "原地浮现"
        else:
            fly = (s[0] + float(r["fx"].replace("px", "")), s[1] + float(r["fy"].replace("px", "")))
            how = "飞入"
        d, srcid = nearest(fly, r["id"])
        # 找终点落在该节点槽位上的连线
        lk = [
            l
            for l in end["lines"]
            if abs(l["x2"] - s[0]) <= 6 and abs(l["y2"] - s[1]) <= 6
        ]
        if lk:
            a = lk[0]
            lk_s = next(
                (l for l in start["lines"] if abs(l["x1"] - a["x1"]) <= 6 and abs(l["y1"] - a["y1"]) <= 6),
                None,
            )
            lstart = (a["x1"], a["y1"])
            grew = (
                round(
                    100
                    * (
                        abs(lk_s["x2"] - lk_s["x1"]) + abs(lk_s["y2"] - lk_s["y1"])
                        if lk_s
                        else 0
                    )
                    / max(1, abs(a["x2"] - a["x1"]) + abs(a["y2"] - a["y1"]))
                )
                if lk_s
                else -1
            )
            d2, aid = nearest(lstart, r["id"])
            gap = round(((fly[0] - lstart[0]) ** 2 + (fly[1] - lstart[1]) ** 2) ** 0.5)
            flag = "OK " if gap <= 8 else "★不一致"
            print(
                f"    {flag} {r['id']:<32} {how:<4} 槽位=({s[0]:>4},{s[1]:>4}) "
                f"起飞≈{srcid:<30}(d={d}) 连线起点=({lstart[0]:>4},{lstart[1]:>4})≈{aid:<28} "
                f"起点差={gap:>4}px 线起飞帧={grew}%  {r['anim']}"
            )
        else:
            print(
                f"    --- {r['id']:<32} {how:<4} 槽位=({s[0]:>4},{s[1]:>4}) "
                f"起飞≈{srcid:<30}(d={d}) 无连线  {r['anim']}"
            )
    if not any(r["arr"] for r in start["rows"]):
        print("    (无)")


with sync_playwright() as p:
    br = p.chromium.launch(headless=True, executable_path=CHROME)
    page = br.new_page(viewport={"width": 1440, "height": 1400})
    page.on("pageerror", lambda e: print("  pageerror:", e))

    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    page.evaluate(
        "() => { document.querySelector('.shell').style.display=''; "
        "document.getElementById('homeScreen').classList.add('hidden'); }"
    )
    time.sleep(0.4)
    b = page.locator("#start").first.bounding_box()
    page.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
    time.sleep(0.6)
    run(page, "A1 原生房间 · 点根展开四空间", '[data-id="root"]')
    run(page, "A2 原生房间 · 点书架展开物件", '[data-id="shelf"]')

    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    page.set_input_files("#homeImportFile", PUZZLE)
    page.wait_for_selector('[data-id="root"]', timeout=10000)
    time.sleep(0.6)
    run(page, "B1 编译关卡 · 点根开场显形", '[data-id="root"]')
    run(page, "B2 编译关卡 · 点柜子开箱", '[data-id="compiled-container-cabinet"]')
    br.close()
