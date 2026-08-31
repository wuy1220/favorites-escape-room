# -*- coding: utf-8 -*-
"""探测:连线到底锚在哪个节点上,与节点的 parent 是否一致。"""
from pathlib import Path
import time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8128/"
PUZZLE = str(Path(__file__).resolve().parents[1] / "sample-puzzles" / "watchman.json")
CHROME = None

DUMP = r"""
() => {
  const slots = {};
  document.querySelectorAll('.node').forEach(el => {
    slots[el.dataset.id] = [Math.round(el.offsetLeft + el.offsetWidth/2),
                            Math.round(el.offsetTop + el.offsetHeight/2)];
  });
  const nameAt = (pt) => {
    let best = null, bd = 1e9;
    for (const k in slots) {
      const d = Math.abs(slots[k][0]-pt[0]) + Math.abs(slots[k][1]-pt[1]);
      if (d < bd) { bd = d; best = k; }
    }
    return (bd <= 8 ? best : '?') + '(d' + Math.round(bd) + ')';
  };
  const lines = [...document.querySelectorAll('#links line')].map(l => {
    const a = [Math.round(+l.getAttribute('x1')), Math.round(+l.getAttribute('y1'))];
    const b = [Math.round(+l.getAttribute('x2')), Math.round(+l.getAttribute('y2'))];
    return { from: nameAt(a), to: nameAt(b), a, b };
  });
  const nodes = state.nodes.filter(n => !n.hidden).map(n => ({
    id: n.id, kind: n.kind, parent: n.parent, x: Math.round(n.x*10)/10, y: Math.round(n.y*10)/10,
  }));
  return { slots, lines, nodes };
}
"""


def show(page, label):
    d = page.evaluate(DUMP)
    print(f"\n{'=' * 88}\n{label}\n{'=' * 88}")
    print("  可见节点(含 parent):")
    for n in d["nodes"]:
        s = d["slots"].get(n["id"])
        print(
            f"    {n['id']:<32} kind={n['kind']:<34} parent={str(n['parent']):<30} "
            f"n=({n['x']},{n['y']}) slot={s}"
        )
    print(f"  连线 {len(d['lines'])} 条:")
    for l in d["lines"]:
        print(f"    {l['from']:<38} → {l['to']}")


with sync_playwright() as p:
    br = p.chromium.launch(headless=True, executable_path=CHROME)
    page = br.new_page(viewport={"width": 1440, "height": 1400})
    page.on("pageerror", lambda e: print("  pageerror:", e))
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    page.set_input_files("#homeImportFile", PUZZLE)
    page.wait_for_selector('[data-id="root"]', timeout=10000)
    time.sleep(0.6)
    show(page, "编译关卡 · 开场前")

    def click(sel):
        b = page.locator(sel).first.bounding_box()
        page.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)

    click('[data-id="root"]')
    time.sleep(1.2)
    show(page, "编译关卡 · 点 root 之后")

    click(page.locator(".node.compiled-scene").first)
    time.sleep(1.2)
    show(page, "编译关卡 · 点柜子开箱后")
    br.close()
