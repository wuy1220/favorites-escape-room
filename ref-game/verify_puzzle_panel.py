# -*- coding: utf-8 -*-
"""11.15 谜题面板溢出回归(零配额,真实 DOM):
- 底部/右缘节点打开面板:四边都在 viewport 内(四向避让 + 收夹)
- 无锚点:右缘悬挂位也在 viewport 内
- 长标题/长颜色标签:卡片不横向撑开(宽度 ≤ CSS 上限 + 容差,无横向溢出)
- 确认按钮可见可点(与视口相交)
在项目根运行(需 8128 静态服务)。"""
import time

from playwright.sync_api import sync_playwright

CHROME = None
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""), flush=True)


MOVE_HOST = """(pos) => {
  const nodes = [...document.querySelectorAll('.node')].filter((n) => n.offsetParent !== null);
  if (!nodes.length) return null;
  const n = nodes[1] || nodes[0];
  n.style.left = pos[0] + '%';
  n.style.top = pos[1] + '%';
  const id = n.getAttribute('data-id');
  /* 直接以引擎同款通道指定锚点:点击会触发 roomRender 重建 DOM,冲掉内联坐标 */
  window.__lastUseTarget = id;
  return id;
}"""

OPEN_AND_MEASURE = """() => {
  const panel = document.getElementById('keypadModal');
  if (!panel) return { error: 'keypadModal 不存在' };
  panel.classList.add('hidden');
  window.__openPuzzlePanel('keypadModal');
  return new Promise((res) => {
    requestAnimationFrame(() => requestAnimationFrame(() => {
      const card = panel.querySelector('.modal-card');
      if (!card) return res({ error: 'modal-card 不存在' });
      const r = card.getBoundingClientRect();
      const btns = [...card.querySelectorAll('.modal-actions button, button')].map((b) => {
        const br = b.getBoundingClientRect();
        return { vis: br.width > 0 && br.height > 0, inVp:
          br.top >= 0 && br.left >= 0 && br.bottom <= window.innerHeight && br.right <= window.innerWidth };
      });
      res({
        vw: window.innerWidth, vh: window.innerHeight,
        left: r.left, top: r.top, right: r.right, bottom: r.bottom,
        w: r.width, scrollW: card.scrollWidth, clientW: card.clientWidth,
        btns: btns,
        panelHidden: panel.classList.contains('hidden'),
      });
    }));
  });
}"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page(viewport={"width": 900, "height": 620})
    page.on("pageerror", lambda e: print("[pageerror]", str(e)[:160], flush=True))
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    page.set_input_files("#homeImportFile", "sample-puzzles/watchman.json")
    time.sleep(2)
    page.click('[data-id="root"]')
    time.sleep(1.2)

    def panel_ok(tag, out):
        if out.get("error"):
            check(tag, False, out["error"])
            return
        m = 6  # 容差:四边允许 6px 内贴边
        inside = (
            out["left"] >= -1
            and out["top"] >= -1
            and out["right"] <= out["vw"] + m
            and out["bottom"] <= out["vh"] + m
        )
        btn_ok = out["btns"] and all(x["vis"] and x["inVp"] for x in out["btns"])
        check(tag, inside and btn_ok and not out["panelHidden"],
              f"rect=({out['left']:.0f},{out['top']:.0f})-({out['right']:.0f},{out['bottom']:.0f})"
              f" vp={out['vw']}x{out['vh']} btns={btn_ok}")

    # 1) 底部节点:top 88%(点击被移动的节点,确保锚定真实生效)
    page.evaluate(MOVE_HOST, [38, 88])
    out = page.evaluate(OPEN_AND_MEASURE)
    panel_ok("底部节点:面板四边在 viewport 内、按钮可点", out)

    # 2) 右缘节点:left 90%
    page.keyboard.press("Escape")
    page.evaluate(MOVE_HOST, [90, 40])
    out2 = page.evaluate(OPEN_AND_MEASURE)
    panel_ok("右缘节点:面板不越过右边界", out2)

    # 3) 无锚点(清除 pop 状态后直接开):默认悬挂位
    out3 = page.evaluate(
        """() => {
          const panel = document.getElementById('keypadModal');
          panel.classList.add('hidden');
          const s = window.__favoriteRoomRuntime;
          // 直接以无锚方式打开:临时移除锚点节点的 data-id 匹配——用独立面板克隆太重,
          // 改为把锚点节点藏到画布外,openPuzzlePanel 查不到 host 即走无锚分支
          const n = document.querySelector('.node[data-id]');
          if (n) n.setAttribute('data-id', 'tmp-detached');
          window.__openPuzzlePanel('keypadModal');
          return new Promise((res) => requestAnimationFrame(() => requestAnimationFrame(() => {
            const card = panel.querySelector('.modal-card');
            const r = card.getBoundingClientRect();
            if (n) n.setAttribute('data-id', 'tmp-restored');
            res({ vw: window.innerWidth, vh: window.innerHeight,
                  left: r.left, top: r.top, right: r.right, bottom: r.bottom,
                  hidden: panel.classList.contains('hidden') });
          })));
        }"""
    )
    if out3.get("error"):
        check("无锚点:默认悬挂位在 viewport 内", False, out3["error"])
    else:
        inside3 = (
            out3["right"] <= out3["vw"] + 6
            and out3["bottom"] <= out3["vh"] + 6
            and out3["left"] >= -1
            and out3["top"] >= -1
            and not out3["hidden"]
        )
        check("无锚点:默认悬挂位在 viewport 内", inside3,
              f"rect=({out3['left']:.0f},{out3['top']:.0f})-({out3['right']:.0f},{out3['bottom']:.0f})")

    # 4) 动态内容不撑宽:长标题 + 超长颜色标签
    out4 = page.evaluate(
        """() => {
          const panel = document.getElementById('keypadModal');
          const card = panel.querySelector('.modal-card');
          const h2 = card.querySelector('h2');
          const origH2 = h2.textContent;
          h2.textContent = '一个特别特别特别长的机关标题——深夜仓库最里侧的黄铜转盘密码锁';
          const disp = card.querySelector('#codeDisplay');
          let origDisp = null;
          if (disp) {
            origDisp = disp.innerHTML;
            disp.innerHTML = ['藏蓝深靛', '茜草红', '藤黄', '松绿', '绛紫', '鸦青']
              .map((c) => '<span class="kp-slot"><b>' + c + '</b><i>·</i></span>').join('');
          }
          panel.classList.remove('hidden');
          window.__openPuzzlePanel('keypadModal');
          return new Promise((res) => requestAnimationFrame(() => requestAnimationFrame(() => {
            const r = card.getBoundingClientRect();
            const overflowX = card.scrollWidth > card.clientWidth + 2;
            if (origDisp != null) disp.innerHTML = origDisp;
            h2.textContent = origH2;
            res({ w: r.width, vw: window.innerWidth, overflowX,
                  right: r.right, bottom: r.bottom, vh: window.innerHeight });
          })));
        }"""
    )
    if out4.get("error"):
        check("长标题/长颜色标签:卡片不横向撑开", False, out4["error"])
    else:
        ok4 = (not out4["overflowX"]) and out4["w"] <= 334 and out4["right"] <= out4["vw"] + 6
        check("长标题/长颜色标签:卡片不横向撑开", ok4,
              f"w={out4['w']:.0f} overflowX={out4['overflowX']} right={out4['right']:.0f}/{out4['vw']}")

    page.screenshot(path="ref-game/puzzle-panel-fix.png")
    b.close()

print(f"\n===== verify_puzzle_panel: {sum(results)}/{len(results)} 通过 =====", flush=True)
raise SystemExit(0 if all(results) else 1)
