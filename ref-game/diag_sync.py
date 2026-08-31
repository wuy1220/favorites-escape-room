# -*- coding: utf-8 -*-
"""验证:连线生长 与 节点飞入 是否同一拍子。

节点进度 = (animation.currentTime - --fd) / 500   ← CSS arrive 的真实进度
连线进度 = 当前长度 / 最终长度                     ← 手写补间的真实进度
两者应逐帧吻合。时间轴用 performance.now(),不依赖帧号(帧率不稳)。
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
    const rows = [...document.querySelectorAll('.node')].map(el => {
      const anim = el.getAnimations().find(a => a.animationName === 'arrive');
      return {
        id: el.dataset.id,
        arr: el.classList.contains('arrive'),
        ct: anim ? Math.round(anim.currentTime || 0) : -1,
        fd: parseFloat(el.style.getPropertyValue('--fd')) || 0,
        fx: parseFloat(el.style.getPropertyValue('--fx')) || 0,
        fy: parseFloat(el.style.getPropertyValue('--fy')) || 0,
      };
    });
    const lines = [...document.querySelectorAll('#links line')].map(l => ({
      x1: +l.getAttribute('x1'), y1: +l.getAttribute('y1'),
      x2: +l.getAttribute('x2'), y2: +l.getAttribute('y2'),
      op: +getComputedStyle(l).opacity,
    }));
    window.__f.push({ f: i, t: performance.now(), rows, lines });
    if (++i < 45) requestAnimationFrame(tick);
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
    time.sleep(1.2)
    frames = page.evaluate("() => window.__f")
    print(f"\n{'=' * 100}\n{label}\n{'=' * 100}")

    # 起飞帧:第一个存在 arrive 且 currentTime<=40 的帧
    k = next(
        (i for i, f in enumerate(frames) if any(r["arr"] and 0 <= r["ct"] <= 40 for r in f["rows"])),
        None,
    )
    if k is None:
        print("  未捕获到新的 arrive")
        return
    start, end = frames[k], frames[-1]
    t0 = start["t"]
    arr = [r for r in start["rows"] if r["arr"] and r["ct"] >= 0]
    print(f"  起飞帧=帧{k}  到达节点 {len(arr)} 个  连线 {len(end['lines'])} 条")
    print("  时间轴(ms) | 节点 arrive 进度%                          | 连线 长度% / 不透明度")
    for f in frames[k : k + 34 : 2]:
        cells = []
        for r in arr:
            cur = next((q for q in f["rows"] if q["id"] == r["id"]), None)
            if not cur or cur["ct"] < 0:
                continue
            p = (cur["ct"] - cur["fd"]) / 500
            cells.append(f"{r['id'][:14]}:{round(100 * max(0, min(1, p))):>3}")
        lc = []
        for a, b in zip(f["lines"], end["lines"]):
            full = abs(b["x2"] - b["x1"]) + abs(b["y2"] - b["y1"])
            now = abs(a["x2"] - a["x1"]) + abs(a["y2"] - a["y1"])
            if full < 5:
                continue
            lc.append(f"{round(100 * now / full):>3}/{a['op']:.1f}")
        print(f"    {f['t'] - t0:>6.0f}   [{' '.join(cells)}]")
        print(f"            连线[{' '.join(lc)}]")


with sync_playwright() as p:
    br = p.chromium.launch(headless=True, executable_path=CHROME)
    page = br.new_page(viewport={"width": 1440, "height": 1400})
    page.on("pageerror", lambda e: print("  pageerror:", e))

    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    page.set_input_files("#homeImportFile", PUZZLE)
    page.wait_for_selector('[data-id="root"]', timeout=10000)
    time.sleep(0.6)
    run(page, "B1 编译关卡 · 点 root 开场显形", '[data-id="root"]')
    run(page, "B2 编译关卡 · 点柜子开箱", '[data-id="compiled-container-cabinet"]')
    br.close()
