# -*- coding: utf-8 -*-
"""诊断各条"节点展开"路径上 .arrive 动画是否被真实播放 + .node 的 transition 实况。

覆盖:
 A. 原生房间:点 root 展开 / 点 shelf(分区)展开
 B. 编译关卡(监狱):点 root(全房间显形) / 点柜子(容器开启就地显形) / 点场景回访
输出每次 roomRender 后 DOM 中的 .arrive 节点,以及逐帧采样的动画状态。
"""
from pathlib import Path
import json
from pathlib import Path
import time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8128/"
PUZZLE = str(Path(__file__).resolve().parents[1] / "sample-puzzles" / "prison.room.json")
CHROME = None

HOOK = r"""
() => {
  window.__rr = [];
  if (typeof window.roomRender !== 'function') return 'NO_ROOMRENDER';
  const orig = window.roomRender;
  window.roomRender = function () {
    const r = orig.apply(this, arguments);
    const a = [...document.querySelectorAll('.node.arrive')];
    window.__rr.push({ n: a.length, ids: a.slice(0, 6).map(e => e.dataset.id) });
    return r;
  };
  return 'OK';
}
"""

SAMPLER = r"""
() => {
  window.__frames = [];
  let i = 0;
  const tick = () => {
    const anims = document.getAnimations().filter(a => a.animationName === 'arrive');
    window.__frames.push({
      f: i,
      arr: document.querySelectorAll('.node.arrive').length,
      an: anims.length,
      t: anims.length ? Math.round(Number(anims[0].currentTime) || 0) : -1,
    });
    if (++i < 45) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}
"""


def arm(page):
    page.evaluate("() => { window.__rr = []; }")
    page.evaluate(SAMPLER)


def report(page, label):
    rr = page.evaluate("() => window.__rr")
    fr = page.evaluate("() => window.__frames")
    ran = [f for f in fr if f["an"] > 0]
    peak = max([f["t"] for f in fr] + [-1])
    print(f"\n--- {label} ---")
    print("  roomRender 次数:", len(rr), "| 各次 .arrive 数:", [r["n"] for r in rr])
    print("  出现 arrive 动画的帧数:", len(ran), "| 动画推进到的最大时间(ms):", peak)
    if rr and rr[-1]["n"] > 0:
        print("  最后一次渲染带 .arrive 的节点:", rr[-1]["ids"])
    verdict = "动画已播放" if len(ran) >= 3 and peak > 100 else "★ 动画未播放/被吃掉"
    print("  判定:", verdict)
    return len(ran) >= 3 and peak > 100


def click(page, sel):
    box = page.locator(sel).first.bounding_box()
    assert box, f"不可点击 {sel}"
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page(viewport={"width": 1440, "height": 1400})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))

    # ============ A. 原生房间 ============
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    page.evaluate(
        "() => { document.querySelector('.shell').style.display=''; "
        "document.getElementById('homeScreen').classList.add('hidden'); }"
    )
    time.sleep(0.4)
    box = page.locator("#start").first.bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    time.sleep(0.6)
    print("hook:", page.evaluate(HOOK))

    print("\n>>> .node 计算后的 transition <<<")
    print(" ", page.evaluate("() => getComputedStyle(document.querySelector('.node')).transition"))
    print("  transitionProperty:",
          page.evaluate("() => getComputedStyle(document.querySelector('.node')).transitionProperty"))

    arm(page)
    click(page, '[data-id="root"]')
    time.sleep(0.9)
    report(page, "A1 原生房间 · 点 root 展开四空间")

    arm(page)
    click(page, '[data-id="shelf"]')
    time.sleep(0.9)
    report(page, "A2 原生房间 · 点 shelf 分区展开物件")

    # ============ B. 编译关卡 ============
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    page.set_input_files("#homeImportFile", PUZZLE)
    page.wait_for_selector('[data-id="root"]', timeout=10000)
    time.sleep(0.5)
    page.evaluate(HOOK)

    arm(page)
    click(page, '[data-id="root"]')
    time.sleep(1.0)
    report(page, "B1 编译关卡 · 点 root(全房间显形)")

    arm(page)
    click(page, '[data-id="compiled-container-cabinet"]')
    time.sleep(1.0)
    report(page, "B2 编译关卡 · 点柜子(容器开启就地显形转盘锁)")

    arm(page)
    click(page, '[data-id="compiled-container-cabinet"]')
    time.sleep(1.0)
    report(page, "B3 编译关卡 · 回访柜子(发现锯子)")

    print("\npageerror:", errs[:3])
    b.close()
