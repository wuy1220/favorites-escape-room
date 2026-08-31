# -*- coding: utf-8 -*-
"""诊断:节点出现动画的起飞点到底在哪儿。

每帧记录 .arrive 节点的**真实渲染中心**(getBoundingClientRect,含 transform)
与它自己的**槽位中心**(offsetLeft/Top,不含 transform),以及各父节点的槽位中心。
起飞帧若渲染中心≈父节点中心 → 从父节点飞出;
             ≈自己槽位     → 原地浮现;
             在自己槽位正上方 → 从顶上飞出。
同时记录连接线端点,看线是"生长"还是"淡入"。
"""
from pathlib import Path
import json
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
      cx: Math.round(el.getBoundingClientRect().left + el.getBoundingClientRect().width / 2),
      cy: Math.round(el.getBoundingClientRect().top + el.getBoundingClientRect().height / 2),
      sx: Math.round(el.offsetLeft + el.offsetWidth / 2),
      sy: Math.round(el.offsetTop + el.offsetHeight / 2),
      fx: el.style.getPropertyValue('--fx'),
      fy: el.style.getPropertyValue('--fy'),
    }));
    const lines = [...document.querySelectorAll('#links line')].map(l => ({
      x1: Math.round(+l.getAttribute('x1')), y1: Math.round(+l.getAttribute('y1')),
      x2: Math.round(+l.getAttribute('x2')), y2: Math.round(+l.getAttribute('y2')),
    }));
    window.__f.push({ f: i, rows, lines });
    if (++i < 24) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}
"""

# 舞台内的坐标要减去 nodes 容器的视口偏移
OFFSET = r"""() => {
  const r = document.getElementById('nodes').getBoundingClientRect();
  return { ox: r.left, oy: r.top };
}"""


def click(page, sel):
    b = page.locator(sel).first.bounding_box()
    assert b, f"不可点击 {sel}"
    page.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)


def run(page, label, sel):
    page.evaluate("() => { window.__pre = null; }")
    page.evaluate(SAMPLER)
    click(page, sel)
    time.sleep(0.8)
    frames = page.evaluate("() => window.__f")
    off = page.evaluate(OFFSET)

    # 起飞帧 = 第一个包含 arrive 节点的帧
    start = next((f for f in frames if any(r["arr"] for r in f["rows"])), None)
    end = frames[-1]
    print(f"\n{'='*74}\n{label}\n{'='*74}")
    if not start:
        print("  未捕获到 .arrive 节点")
        return
    slots = {r["id"]: (r["sx"], r["sy"]) for r in end["rows"]}
    print(f"  舞台偏移 ox={off['ox']:.0f} oy={off['oy']:.0f}")
    print("  起飞帧各节点(渲染中心 → 槽位中心, 位移向量 --fx/--fy):")
    for r in start["rows"]:
        if not r["arr"]:
            continue
        s = slots.get(r["id"])
        if not s:
            continue
        # 渲染中心换算到舞台坐标
        rx = r["cx"] - off["ox"]
        ry = r["cy"] - off["oy"]
        dx, dy = rx - s[0], ry - s[1]
        # 找最近的其它节点(潜在起飞源)
        near = sorted(
            ((abs(v[0] - rx) + abs(v[1] - ry), k) for k, v in slots.items() if k != r["id"])
        )[:1]
        print(
            f"    {r['id']:<34} 渲染=({rx:>4},{ry:>4}) 槽位=({s[0]:>4},{s[1]:>4}) "
            f"偏离=({dx:>+4},{dy:>+4}) --fx={r['fx'] or '-':>9} --fy={r['fy'] or '-':>9} "
            f"最近节点={near[0][1] if near else '?'}"
        )
    print("  连接线端点(起飞帧 → 末帧):")
    for a, b in list(zip(start["lines"], end["lines"]))[:6]:
        grew = abs(a["x2"] - a["x1"]) + abs(a["y2"] - a["y1"])
        full = abs(b["x2"] - b["x1"]) + abs(b["y2"] - b["y1"])
        pct = round(100 * grew / full) if full else -1
        print(f"    起飞帧长度占比 {pct:>3}%  ({a['x1']},{a['y1']})→({a['x2']},{a['y2']})  末帧→({b['x2']},{b['y2']})")


with sync_playwright() as p:
    br = p.chromium.launch(headless=True, executable_path=CHROME)
    page = br.new_page(viewport={"width": 1440, "height": 1400})
    page.on("pageerror", lambda e: print("  pageerror:", e))

    # A. 原生房间
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
    run(page, "A1 原生房间 · 点 root 展开四空间", '[data-id="root"]')
    run(page, "A2 原生房间 · 点 shelf 展开物件", '[data-id="shelf"]')

    # B. 编译关卡
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    page.set_input_files("#homeImportFile", PUZZLE)
    page.wait_for_selector('[data-id="root"]', timeout=10000)
    time.sleep(0.6)
    run(page, "B1 编译关卡 · 点 root 开场显形", '[data-id="root"]')
    run(page, "B2 编译关卡 · 点柜子开箱", '[data-id="compiled-container-cabinet"]')
    br.close()
