# -*- coding: utf-8 -*-
"""探测:页面内能否直接读到 state,以及各节点的 parent / revealFromId / compiledScene。"""
from pathlib import Path
import time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8128/"
PUZZLE = str(Path(__file__).resolve().parents[1] / "sample-puzzles" / "prison.room.json")
CHROME = None

DUMP = r"""
() => {
  if (typeof state === 'undefined') return 'no state';
  return state.nodes.map(n => ({
    id: n.id, kind: n.kind, parent: n.parent, rfid: n.revealFromId || '',
    x: n.x, y: n.y,
    cs: (typeof n.compiledScene === 'boolean' ? 'bool:' + n.compiledScene : (n.compiledScene || '')),
    hid: !!n.hidden, ja: !!n.justArrived,
  }));
}
"""

with sync_playwright() as p:
    br = p.chromium.launch(headless=True, executable_path=CHROME)
    page = br.new_page(viewport={"width": 1440, "height": 1400})
    page.on("pageerror", lambda e: print("  pageerror:", e))
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    page.set_input_files("#homeImportFile", PUZZLE)
    page.wait_for_selector('[data-id="root"]', timeout=10000)
    time.sleep(0.6)
    print("typeof state =", page.evaluate("() => typeof state"))
    print("typeof roomRender =", page.evaluate("() => typeof roomRender"))
    print("typeof get =", page.evaluate("() => typeof get"))
    info = page.evaluate(DUMP)
    if isinstance(info, str):
        print(info)
    else:
        print(f"共 {len(info)} 个节点")
        for r in info:
            print(
                f"  {r['id']:<34} kind={r['kind']:<36} parent={str(r['parent']):<32} "
                f"rfid={r['rfid']:<32} x={r['x']:<6} y={r['y']:<6} cs={r['cs']:<32} hidden={r['hid']}"
            )
    br.close()
