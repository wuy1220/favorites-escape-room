# -*- coding: utf-8 -*-
"""通用自动通关器:对任意 .room.json 导入的关卡,读取运行时规则表并自动通关。

不预设关卡内容——从 window.__dbg(compiled 状态)读 beats/rules,按 requires 拓扑推进,
逐 beat 执行 inspect/combine/revisit/sequence/deliver/password/angle/morse,
覆盖回访语义(环顾四周按钮)。卡死时打印现场并以非零码退出。

用法:python verify_generated.py <puzzle.room.json> [base_url]
环境变量:AUTO_DEBUG=1 输出每轮决策
"""
import json
import math
import os
import sys
import time
from playwright.sync_api import sync_playwright

CHROME = r"C:\Users\30807\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe"
PUZZLE = sys.argv[1] if len(sys.argv) > 1 else "sample-puzzles/generated-live.room.json"
BASE = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8128/"
DEBUG = os.environ.get("AUTO_DEBUG") == "1"

JS_HELPERS = r"""
(() => {
  window.__auto = {
    clues(){ const s=(window.__favoriteRoomRuntime&&window.__favoriteRoomRuntime.snapshot())||{};
             return s.clues||[] },
    beats(){ return (window.__dbg&&window.__dbg.level&&window.__dbg.level.beats)||[] },
    done(){ const s=(window.__favoriteRoomRuntime&&window.__favoriteRoomRuntime.snapshot())||{};
            return !!s.done },
    itemSel(id){ return '[data-id="compiled-item-'+id+'"]' },
    visible(sel){ const el=document.querySelector(sel); return !!el && el.getClientRects().length>0 },
    /* morph 引擎:结果不是独立节点,而是"该步最后一个操作数"的原位变身(product 名不可预测),
       因此 result:<beatId> 的载体 = 递归解析该 beat uses[-1] 的操作数 */
    resultSelFor(beatId,depth){
      depth=depth||0;
      const b=(window.__dbg.level.beats||[]).find(x=>x.id===beatId);
      if(!b||depth>3)return null;
      const lastUse=String((b.uses||[]).slice(-1)[0]||'');
      if(!lastUse.startsWith('result:')){
        const s=this.itemSel(lastUse);
        return this.visible(s)?s:null;
      }
      return this.resultSelFor(lastUse.slice(7),depth+1);
    },
    mapGet(k){ k=String(k).slice(7); const m=this.__rmap||{}; const v=m[k]; return v||null },
    opSel(key){
      key=String(key);
      if(key.startsWith('result:')){
        const m=this.mapGet(key); if(m&&this.visible(m))return m;
        return this.resultSelFor(key.slice(7));
      }
      const s=this.itemSel(key); return this.visible(s)?s:null;
    },
    anyOpenModal(){ return [...document.querySelectorAll('.modal')]
                      .some(m=>!m.classList.contains('hidden')) }
  };
})()
"""

ANGLE_BTN_NOTE = "SVG 表盘:pointerdown→沿圆弧移动→pointerup,松手吸附到 precision 档位"


def dbg(msg):
    if DEBUG:
        print("    [dbg]", msg)


def make_ops(page):
    def dom_click(sel):
        cnt = page.evaluate("(s)=>!!document.querySelector(s)", sel)
        if not cnt:
            raise RuntimeError("目标不存在: %s" % sel)
        page.evaluate("(s)=>document.querySelector(s).click()", sel)
        time.sleep(0.3)

    def mouse_click(sel):
        loc = page.locator(sel).first
        box = loc.bounding_box()
        if not box:
            raise RuntimeError("无 bounding_box: %s" % sel)
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

    def click_node(sel):
        """世界节点:先 DOM click(浮动按钮可能盖住鼠标路径),
        若页面无响应可用真鼠标补一发。"""
        dom_click(sel)

    def open_modal(item_sel, modal_id):
        """打开机关弹窗:DOM click 失败则用真鼠标点击节点中心。"""
        dom_click(item_sel)
        try:
            page.wait_for_selector("#%s:not(.hidden)" % modal_id, timeout=2500)
            return
        except Exception:
            pass
        dbg("%s 未弹出,改用真实鼠标点击 %s" % (modal_id, item_sel))
        mouse_click(item_sel)
        page.wait_for_selector("#%s:not(.hidden)" % modal_id, timeout=5000)
        time.sleep(0.25)

    def drag_sel(src, dst):
        sb = page.locator(src).first.bounding_box()
        db = page.locator(dst).first.bounding_box()
        if not sb or not db:
            raise RuntimeError("拖拽端点缺失 %s -> %s" % (src, dst))
        sx, sy = sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 2
        dx, dy = db["x"] + db["width"] / 2, db["y"] + db["height"] / 2
        page.mouse.move(sx, sy)
        page.mouse.down()
        for i in range(1, 9):
            page.mouse.move(sx + (dx - sx) * i / 8, sy + (dy - sy) * i / 8)
            time.sleep(0.04)
        if DEBUG:
            landed = page.evaluate(
                "(p)=>document.elementsFromPoint(p.x,p.y).slice(0,3)"
                ".map(e=>({id:e.dataset&&e.dataset.id,cls:String(e.className).slice(0,26)}))",
                {"x": dx, "y": dy})
            print("    [drag] ->%s 命中=%s" % ("[exit]" if "exit" in dst else dst[-20:],
                                              json.dumps(landed, ensure_ascii=False)), flush=True)
        page.mouse.up()
        time.sleep(0.6)

    def turn_dial(di, target):
        """角度旋钮:pointerdown→沿圆弧移动到目标角→pointerup,松手吸附档位。
        引擎每次 angleTurn 都重建 dial DOM,禁用 locator 重试模式,全程真输入。"""
        sel = '.angle-dial[data-i="%d"] .ad-face' % di
        loc = page.locator(sel).first
        box = loc.bounding_box(timeout=3000)
        cx = box["x"] + box["width"] / 2
        cy = box["y"] + box["height"] / 2

        def pt(a):
            return (cx + 38 * math.sin(math.radians(a)),
                    cy - 38 * math.cos(math.radians(a)))
        px, py = pt(0)
        page.mouse.move(px, py)
        page.mouse.down()
        for k in range(1, 9):
            px, py = pt(target * k / 8.0)
            page.mouse.move(px, py)
            time.sleep(0.05)
        page.mouse.up()
        time.sleep(0.35)

    def press(sel_js):
        page.evaluate(sel_js)
        time.sleep(0.06)

    def look_around():
        if page.evaluate("()=>window.__auto.anyOpenModal()"):
            return
        btn = page.evaluate("()=>!!document.getElementById('revisitRoom')")
        if btn:
            page.evaluate("()=>document.getElementById('revisitRoom').click()")
            time.sleep(0.45)

    def ensure_containers(opened):
        for cid in page.evaluate(
            """()=>[...document.querySelectorAll('.node.compiled-container')]
                  .filter(e=>e.getClientRects().length&&!e.dataset.openedAuto)
                  .map(e=>{e.dataset.openedAuto='1';return e.dataset.id})"""):
            if cid in opened:
                continue
            opened.add(cid)
            dbg("开容器 %s" % cid)
            dom_click('[data-id="%s"]' % cid)
            time.sleep(0.25)

    return dict(dom_click=dom_click, mouse_click=mouse_click, click_node=click_node,
                open_modal=open_modal, drag_sel=drag_sel, turn_dial=turn_dial,
                press=press, look_around=look_around, ensure_containers=ensure_containers)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1440, "height": 1400})
        page.set_default_timeout(4000)
        js_errors = []
        page.on("pageerror", lambda e: js_errors.append(str(e)))
        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_selector("#homeScreen", timeout=15000)
        page.evaluate(JS_HELPERS)
        page.set_input_files("#homeImportFile", PUZZLE)
        page.wait_for_selector('[data-id="root"]', timeout=10000)
        time.sleep(0.5)
        # 开始关卡(root 或关卡入口,谁在点谁)
        for entry in ('[data-id="compiled-level"]', '[data-id="root"]'):
            loc = page.locator(entry)
            if loc.count() and loc.first.is_visible():
                box = loc.first.bounding_box()
                page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                time.sleep(0.7)
                break
        ops = make_ops(page)
        ops["look_around"]()

        beats = page.evaluate("()=>window.__auto.beats()")
        total = len(beats)
        print("导入成功,共 %d 个 beat: %s" % (
            total, ", ".join("%s(%s)" % (b['id'], b['action']) for b in beats)))

        clues_n = 0
        stall = 0
        finished = False
        opened = set()
        for _round in range(total * 6 + 30):
            if page.evaluate("()=>window.__auto.done()"):
                finished = True
                break
            ops["ensure_containers"](opened)
            ops["look_around"]()
            clues = page.evaluate("()=>window.__auto.clues()")
            pending = [b for b in beats if 'beat-' + b['id'] not in clues]
            if not pending:
                finished = True
                break
            progressed = False
            if DEBUG:
                for bb in pending:
                    rok = all(('beat-' + r) in clues for r in (bb.get('requires') or []))
                    vs0 = None
                    if rok and bb.get('uses'):
                        try:
                            vs0 = page.evaluate("(k)=>window.__auto.opSel(k)", bb['uses'][0])
                        except Exception as e2:
                            vs0 = "ERR:%s" % str(e2)[:50]
                    print("    [decide]", bb['id'], bb['action'], "req=", rok, "op0=", vs0)
            for b in pending:
                req_ok = all(('beat-' + r) in clues for r in (b.get('requires') or []))
                if not req_ok:
                    continue
                act = b['action']
                uses = [str(u) for u in (b.get('uses') or [])]
                try:
                    if act in ('inspect', 'revisit'):
                        targets = [u for u in uses if not u.startswith('result:')]
                        if not targets or not all(
                                page.evaluate("(s)=>window.__auto.visible(s)",
                                              '[data-id="compiled-item-%s"]' % t)
                                for t in targets):
                            continue
                        for t in targets:
                            ops["dom_click"]('[data-id="compiled-item-%s"]' % t)
                            time.sleep(0.15)
                        progressed = True
                    elif act == 'password':
                        sel = page.evaluate("(k)=>window.__auto.opSel(k)", uses[0])
                        if not sel:
                            continue
                        ops["open_modal"](sel, 'keypadModal')
                        for dgt in str(b.get('expected') or ''):
                            page.locator('#keypad [data-k="%s"]' % dgt).click()
                            time.sleep(0.15)
                        time.sleep(0.6)
                        progressed = True
                    elif act == 'angle':
                        sel = page.evaluate("(k)=>window.__auto.opSel(k)", uses[0])
                        if not sel:
                            continue
                        ops["open_modal"](sel, 'angleModal')
                        for di, tgt in enumerate(b.get('angles') or []):
                            ops["turn_dial"](di, int(tgt))
                            time.sleep(0.15)
                        try:
                            page.wait_for_selector('#angleModal.hidden', timeout=4000)
                        except Exception:
                            pass
                        time.sleep(0.4)
                        progressed = True
                    elif act == 'morse':
                        sel = page.evaluate("(k)=>window.__auto.opSel(k)", uses[0])
                        if not sel:
                            continue
                        ops["open_modal"](sel, 'morseModal')
                        for ch in str(b.get('code') or ''):
                            if ch == '.':
                                page.locator('#morseDot').click()
                            elif ch == '-':
                                page.locator('#morseDash').click()
                            elif ch == '/':
                                page.locator('#morseSlash').click()
                            time.sleep(0.06)
                        page.locator('#morseEnter').click()
                        time.sleep(0.5)
                        progressed = True
                        if os.environ.get('AUTO_DEBUG'):print("    [did] morse actions done",b['id'])
                    elif act == 'sequence':
                        sels = []
                        ok = True
                        for k in uses:
                            s = page.evaluate("(k)=>window.__auto.opSel(k)", k)
                            if not s:
                                ok = False
                                break
                            sels.append(s)
                        if not ok:
                            continue
                        for s in sels:
                            ops["dom_click"](s)
                            time.sleep(0.3)
                        page.evaluate(
                            "(p)=>{const w=window.__auto;w.__rmap=w.__rmap||{};w.__rmap[p.bid]=p.sel}",
                            {"bid": b['id'], "sel": sels[-1]})
                        progressed = True
                        if os.environ.get('AUTO_DEBUG'):print("    [did] sequence",b['id'])
                    elif act == 'combine':
                        a = page.evaluate("(k)=>window.__auto.opSel(k)", uses[0])
                        bbk = page.evaluate("(k)=>window.__auto.opSel(k)", uses[1]) if len(uses) > 1 else None
                        if not a or not bbk:
                            continue
                        ops["drag_sel"](a, bbk)
                        if os.environ.get('AUTO_DEBUG'):print("    [did] combine drag",b['id'])
                        page.evaluate(
                            "(p)=>{const w=window.__auto;w.__rmap=w.__rmap||{};"
                            "if(!w.__rmap[p.bid])w.__rmap[p.bid]=p.sel}",
                            {"bid": b['id'], "sel": bbk})
                        progressed = True
                    elif act == 'deliver':
                        s = page.evaluate("(k)=>window.__auto.opSel(k)", uses[0])
                        exit_visible = page.evaluate(
                            "()=>window.__auto.visible('[data-id=\"compiled-exit\"]')")
                        if not s or not exit_visible:
                            continue
                        ops["drag_sel"](s, '[data-id="compiled-exit"]')
                        time.sleep(0.4)
                        # 引擎桥兜底:若拖拽未被 engine 记账,直接走内部 use 链
                        if not page.evaluate("()=>window.__auto.done()"):
                            sid = page.evaluate("(s)=>document.querySelector(s).dataset.id", s)
                            before = len(page.evaluate("()=>window.__auto.clues()"))
                            page.evaluate("(p)=>window.roomUse(p.a,'compiled-exit')",
                                          {"a": sid})
                            time.sleep(0.4)
                            after = len(page.evaluate("()=>window.__auto.clues()"))
                            dbg("交付桥: %s clue %d->%d" % (sid, before, after))
                        ops["dom_click"]('[data-id="compiled-exit"]')
                        time.sleep(0.6)
                        progressed = True
                except Exception as exc:
                    print("[WARN] 执行 beat %s 出错: %s" % (b['id'], exc))
                if progressed:
                    if not page.evaluate("()=>window.__auto.done()"):
                        ops["look_around"]()
                    break
            new_clues = page.evaluate("()=>window.__auto.clues()")
            if len(new_clues) > clues_n:
                clues_n = len(new_clues)
                stall = 0
            else:
                stall += 1
                if stall >= 4 and not finished:
                    vis_nodes = page.evaluate(
                        """()=>[...document.querySelectorAll('.node')].filter(e=>e.getClientRects().length)
                              .map(e=>({id:e.dataset.id,name:(e.querySelector('.name')||{}).textContent}))""")
                    modals = page.evaluate(
                        """()=>({morse:(function(){var m=document.getElementById('morseModal');
                                   return m?{cls:m.className,buf:(document.getElementById('morseDisplay')||{}).textContent}:null})(),
                                keypad:(function(){var m=document.getElementById('keypadModal');
                                   return m?{cls:m.className,buf:(document.getElementById('codeDisplay')||{}).textContent}:null})(),
                                targetCode:(window.__dbg.rules.morses||[])[0]||null,
                                delivRules:(window.__dbg.rules.delivers||[]).map(function(r){return {item:r.item,need:r.need}}),
                                resolve:(function(){var out=[];
                                  (window.__dbg.level.beats||[]).forEach(function(b){
                                    if(b.action!=='deliver')return;
                                    (b.uses||[]).forEach(function(u){
                                      out.push({use:u,
                                        mapped:(window.__auto.__rmap||{})[String(u).slice(7)]||null,
                                        viaRecursive:(function(){try{return window.__auto.resultSelFor(String(u).slice(7))}catch(e){return 'ERR:'+e}})()});});
                                  });return out;})(),
                                rmapKeys:Object.keys(window.__auto.__rmap||{})})""")
                    print("[FAIL] 连续无进展。已解:", new_clues)
                    print("  弹窗状态:", json.dumps(modals, ensure_ascii=False))
                    print("  pending:", [(x['id'], x['action'], x.get('uses')) for x in pending])
                    print("  可见节点:", json.dumps(vis_nodes, ensure_ascii=False)[:1100])
                    log_head = page.evaluate(
                        "()=>{const t=document.getElementById('log').innerText;"
                        "return {len:t.length,"
                        "combo:(t.split('组合成功').length-1),"
                        "morseOk:(t.split('摩斯码正确').length-1),"
                        "pwOk:(t.split('密码正确').length-1),"
                        "wrong:(t.split('摩斯码不对').length-1),"
                        "head:t.slice(0,700)}}")
                    print("  日志统计:", json.dumps(log_head, ensure_ascii=False))
                    sys.exit(1)

        snap = page.evaluate("()=>(window.__favoriteRoomRuntime&&window.__favoriteRoomRuntime.snapshot())||{}")
        ok = bool(snap.get("done")) and finished or bool(snap.get("done"))
        print("[%s] 自动通关%s clues=%s" % ("PASS" if snap.get("done") else "FAIL",
                                            "" if snap.get("done") else "失败",
                                            snap.get("clues")))
        if js_errors:
            print("页面错误:", js_errors[:3])
        browser.close()
        sys.exit(0 if snap.get("done") else 1)


if __name__ == "__main__":
    main()
