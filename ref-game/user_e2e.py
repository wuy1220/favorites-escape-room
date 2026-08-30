# -*- coding: utf-8 -*-
"""用户素材端到端(最终代码):design→compile→solve→DOM 通关。
用法: python user_e2e.py <导出的 room.json>(取其 cleaning.records 做 6 条受控素材)"""
import json, time, math, sys
from playwright.sync_api import sync_playwright

CHROME = r"C:/Users/30807/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"
src = json.load(open(sys.argv[1] if len(sys.argv) > 1 else r"C:/Users/30807/Downloads/收藏夹密室：复古电脑谜题.room.json", encoding="utf-8"))
REC = src["cleaning"]["records"][:6]
IDS = [r["id"] for r in REC]
WIN = src["level"].get("timeWindow") or {"label": "", "count": 6, "mood": "深夜"}
THEME = src["level"].get("theme") or ""

def ensure_visible(page, sel):
    for _ in range(3):
        loc = page.locator(sel).first
        if loc.count() and loc.is_visible(): return True
        page.evaluate("() => { const b = document.getElementById('revisitRoom'); if (b) b.click(); }")
        time.sleep(0.45)
    loc = page.locator(sel).first
    return bool(loc.count() and loc.is_visible())

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page(viewport={"width":1440,"height":1400})
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!(window.__favoriteRoomPipeline && window.__favoriteRoomPipeline.solveLevel)", timeout=15000)
    code = """async (payload) => {
      const pipe = window.__favoriteRoomPipeline;
      const cleaned = {records: payload.records, controlledIds: payload.ids, duplicates: [], stats:{input:15,unique:6,duplicates:0}};
      const log = [];
      let repairNote='', designed=null, draft=null;
      for (let round=0; round<3; round++) {
        try { designed = await pipe.designWindow(payload.records, payload.theme, payload.win, [], function(){}, repairNote); }
        catch(de) { log.push({round, stage:'design-fatal', err:String(de&&de.message||de).slice(0,90)});
                    if(round===2) return {ok:false, log}; repairNote=String(de&&de.message||de); continue; }
        try { draft = pipe.compile(cleaned, null, designed.parsed, payload.theme); }
        catch(se) { log.push({round, stage:'compile-throw', err:String(se&&se.message||se).slice(0,90)});
                    if(round===2) return {ok:false, log}; repairNote=String(se&&se.message||se); continue; }
        const solve = pipe.solveLevel(draft.level);
        log.push({round, stage:'compiled+solved', solvable:solve.solvable,
                  designActions: designed.parsed.beats.map(x=>x.action),
                  compiledActions: draft.level.beats.map(x=>x.action),
                  sceneNames: designed.parsed.items.map(x=>x.scene_name||x.sceneName||'?')});
        if (!solve.solvable && round<2) { repairNote='自动求解器无法通关——'+String(solve.detail||''); draft=null; continue; }
        return {ok:solve.solvable, log, level: draft.level};
      }
      return {ok:false, log};
    }"""
    t0 = time.time()
    res = page.evaluate(code, {"records": REC, "ids": IDS, "theme": THEME, "win": WIN})
    print("ROUNDS:", json.dumps(res.get("log"), ensure_ascii=False, indent=1)[:1800], flush=True)
    if not res.get("ok"):
        print("GEN-FAIL（应退回模板保底）"); b.close(); sys.exit(1)
    lv = res["level"]
    path = "ref-game/llm_out/user_repro.room.json"
    json.dump({"records":REC,"controlledIds":IDS,"items":REC,"level":lv}, open(path,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"GEN-OK 用时={time.time()-t0:.0f}s TITLE={lv.get('title')} 机关={[bt['action'] for bt in lv['beats'] if bt['action'] in ('password','angle','morse')]}", flush=True)
    print("SCENENAMES:", json.dumps([it.get("sceneName") for it in lv.get("items",[])], ensure_ascii=False), flush=True)
    # DOM 通关
    beats = lv["beats"]; by_id = {b2["id"]: b2 for b2 in beats}
    def morph(bt):
        if bt.get("resultOn"): return bt["resultOn"]
        if bt["action"] == "combine": return bt["uses"][1]
        if bt["action"] == "sequence": return bt["uses"][-1]
        return None
    def resolve(u, depth=0):
        if not u.startswith("result:"): return u
        bt = by_id.get(u[7:])
        if not bt or depth > 6: return u[7:]
        m = morph(bt)
        return resolve(m, depth+1) if m is not None else u[7:]
    def sel(u): return '[data-id="compiled-item-' + resolve(u) + '"]'
    def click(s):
        box = page.locator(s).first.bounding_box(); assert box, s
        page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2); time.sleep(0.35)
    def drag(s, d):
        sb = page.locator(s).first.bounding_box(); db = page.locator(d).first.bounding_box()
        assert sb and db, f"drag {s}->{d}"
        sx, sy = sb["x"]+sb["width"]/2, sb["y"]+sb["height"]/2
        dx, dy = db["x"]+db["width"]/2, db["y"]+db["height"]/2
        page.mouse.move(sx, sy); page.mouse.down()
        for i in range(1, 6): page.mouse.move(sx+(dx-sx)*i/5, sy+(dy-sy)*i/5); time.sleep(0.03)
        page.mouse.up(); time.sleep(0.45)
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    page.set_input_files("#homeImportFile", path)
    page.wait_for_selector('[data-id="root"]', timeout=10000)
    click('[data-id="root"]')
    ok_steps = 0
    for i, bt in enumerate(beats):
        try:
            page.evaluate("() => ['keypadModal','morseModal','angleModal'].forEach(id => { const e = document.getElementById(id); if (e) e.classList.add('hidden'); })")
            if bt["action"] in ("inspect", "revisit"):
                for u in bt["uses"]:
                    if not ensure_visible(page, sel(u)): raise Exception(f"物件 {u} 无法显形")
                    click(sel(u))
            elif bt["action"] == "combine":
                ensure_visible(page, sel(bt["uses"][0])); ensure_visible(page, sel(bt["uses"][1]))
                drag(sel(bt["uses"][0]), sel(bt["uses"][1]))
            elif bt["action"] == "sequence":
                for u in bt["uses"]: ensure_visible(page, sel(u)); click(sel(u))
            elif bt["action"] == "password":
                ensure_visible(page, sel(bt["uses"][0])); click(sel(bt["uses"][0]))
                page.wait_for_selector('#keypadModal:not(.hidden)', timeout=5000)
                for k in str(bt["expected"]): page.locator(f'#keypad [data-k="{k}"]').click(); time.sleep(0.12)
                time.sleep(0.4)
            elif bt["action"] == "morse":
                ensure_visible(page, sel(bt["uses"][0])); click(sel(bt["uses"][0]))
                page.wait_for_selector('#morseModal:not(.hidden)', timeout=5000)
                for ch in str(bt["code"]):
                    if ch == '.': page.locator('#morseDot').click()
                    elif ch == '-': page.locator('#morseDash').click()
                    elif ch == '/': page.locator('#morseSlash').click()
                    time.sleep(0.05)
                page.locator('#morseEnter').click(); time.sleep(0.4)
            elif bt["action"] == "angle":
                ensure_visible(page, sel(bt["uses"][0])); click(sel(bt["uses"][0]))
                page.wait_for_selector('#angleModal:not(.hidden)', timeout=5000)
                for di, ang in enumerate(bt["angles"]):
                    svg = page.locator(f'.angle-dial[data-i="{di}"] .ad-face').first
                    bb = svg.bounding_box(); assert bb
                    cx, cy = bb["x"]+bb["width"]/2, bb["y"]+bb["height"]/2
                    R = bb["width"]*0.38; rad = math.radians(float(ang))
                    page.mouse.click(cx + R*math.sin(rad), cy - R*math.cos(rad)); time.sleep(0.25)
                time.sleep(0.3)
            elif bt["action"] == "deliver":
                ensure_visible(page, sel(bt["uses"][0]))
                drag(sel(bt["uses"][0]), '[data-id="compiled-exit"]'); time.sleep(0.4)
            ok_steps += 1
        except Exception as e:
            print(f"PLAY-FAIL step{i+1}({bt['action']}): {str(e)[:100]}", flush=True)
            break
    else:
        snap = page.evaluate("() => (window.__favoriteRoomRuntime && window.__favoriteRoomRuntime.snapshot()) || null")
        done = bool(snap and snap.get("done"))
        print(f"PLAY: {'PASS' if done else 'FAIL'} steps={ok_steps}/{len(beats)} done={done}", flush=True)
        print("FINAL:", "ALL-PASS" if done else "PLAY-FAIL", flush=True)
        b.close(); sys.exit(0 if done else 1)
    b.close(); sys.exit(1)
