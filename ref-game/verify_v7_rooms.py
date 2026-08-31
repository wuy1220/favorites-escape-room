# -*- coding: utf-8 -*-
"""v7 生成关卡的真实 DOM 通关验证(可对多个 room.json 重复执行)。
用法: python verify_v7_rooms.py ref-game/llm_out/gen_v7_r1.room.json ..."""
import json, time, math, sys
from playwright.sync_api import sync_playwright

CHROME = None

def play_through(page, path):
    room = json.load(open(path, encoding="utf-8"))
    lv = room["level"]; beats = lv["beats"]
    by_id = {b["id"]: b for b in beats}
    def morph(beat):
        if beat.get("resultOn"): return beat["resultOn"]
        if beat["action"] == "combine": return beat["uses"][1]
        if beat["action"] == "sequence": return beat["uses"][-1]
        return None
    def resolve(u, depth=0):
        if not u.startswith("result:"): return u
        b = by_id.get(u[7:])
        if not b or depth > 6: return u[7:]
        m = morph(b)
        return resolve(m, depth+1) if m is not None else u[7:]
    def sel(u): return '[data-id="compiled-item-' + resolve(u) + '"]'
    def ensure_visible(u):
        s = sel(u)
        for _ in range(3):
            loc = page.locator(s).first
            if loc.count() and loc.is_visible(): return True
            page.evaluate("() => { const b = document.getElementById('revisitRoom'); if (b) b.click(); }")
            time.sleep(0.45)
        loc = page.locator(s).first
        return bool(loc.count() and loc.is_visible())
    def click(s):
        box = page.locator(s).first.bounding_box(); assert box, "不可点击 " + s
        page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2); time.sleep(0.35)
    def drag(s, d):
        sb = page.locator(s).first.bounding_box(); db = page.locator(d).first.bounding_box()
        assert sb and db, f"不可拖拽 {s}->{d}"
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
    first = beats[0]["uses"][0] if beats[0]["uses"] else None
    if first:
        ensure_visible(first)
        page.wait_for_selector(sel(first), timeout=10000)
    ok_steps = 0
    for i, b in enumerate(beats):
        try:
            # 防御:关闭残留的机关面板(避免拦截后续点击)
            page.evaluate("() => ['keypadModal','morseModal','angleModal'].forEach(id => { const e = document.getElementById(id); if (e) e.classList.add('hidden'); })")
            if b["action"] in ("inspect", "revisit"):
                for u in b["uses"]:  # 多 id 观察步:引擎要求全部点过才完成
                    if not ensure_visible(u):
                        return False, ok_steps, f"step{i+1}: 物件「{u}」无法显形"
                    click(sel(u))
            elif b["action"] == "combine":
                if not ensure_visible(b["uses"][0]): return False, ok_steps, f"step{i+1}: 拖拽源不可显形"
                if not ensure_visible(b["uses"][1]): return False, ok_steps, f"step{i+1}: 组合目标不可显形"
                drag(sel(b["uses"][0]), sel(b["uses"][1]))
            elif b["action"] == "sequence":
                for u in b["uses"]:
                    if not ensure_visible(u): return False, ok_steps, f"step{i+1}: 物件「{u}」无法显形"
                    click(sel(u))
            elif b["action"] == "password":
                if not ensure_visible(b["uses"][0]): return False, ok_steps, f"step{i+1}: 密码盘不可显形"
                click(sel(b["uses"][0]))
                page.wait_for_selector('#keypadModal:not(.hidden)', timeout=5000)
                for k in str(b["expected"]):
                    page.locator(f'#keypad [data-k="{k}"]').click(); time.sleep(0.12)
                time.sleep(0.4)
            elif b["action"] == "morse":
                if not ensure_visible(b["uses"][0]): return False, ok_steps, f"step{i+1}: 摩斯机不可显形"
                click(sel(b["uses"][0]))
                page.wait_for_selector('#morseModal:not(.hidden)', timeout=5000)
                for ch in str(b["code"]):
                    if ch == '.': page.locator('#morseDot').click()
                    elif ch == '-': page.locator('#morseDash').click()
                    elif ch == '/': page.locator('#morseSlash').click()
                    time.sleep(0.05)
                page.locator('#morseEnter').click(); time.sleep(0.4)
            elif b["action"] == "angle":
                if not ensure_visible(b["uses"][0]): return False, ok_steps, f"step{i+1}: 角度锁不可显形"
                click(sel(b["uses"][0]))
                page.wait_for_selector('#angleModal:not(.hidden)', timeout=5000)
                for di, ang in enumerate(b["angles"]):
                    svg = page.locator(f'.angle-dial[data-i="{di}"] .ad-face').first
                    bb = svg.bounding_box(); assert bb, f"表盘 {di} 不可见"
                    cx, cy = bb["x"]+bb["width"]/2, bb["y"]+bb["height"]/2
                    R = bb["width"]*0.38
                    rad = math.radians(float(ang))
                    page.mouse.click(cx + R*math.sin(rad), cy - R*math.cos(rad)); time.sleep(0.25)
                time.sleep(0.3)
            elif b["action"] == "deliver":
                if not ensure_visible(b["uses"][0]): return False, ok_steps, f"step{i+1}: 交付物不可显形"
                drag(sel(b["uses"][0]), '[data-id="compiled-exit"]'); time.sleep(0.4)
            else:
                return False, ok_steps, f"step{i+1}: 未知动作 {b['action']}"
            ok_steps += 1
        except Exception as e:
            return False, ok_steps, f"step{i+1}({b['action']}) {str(e)[:100]}"
    snap = page.evaluate("() => (window.__favoriteRoomRuntime && window.__favoriteRoomRuntime.snapshot()) || null")
    done = bool(snap and snap.get("done"))
    return done, ok_steps, f"clues={snap.get('clues') if snap else None}"

def main(paths):
    results = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, executable_path=CHROME)
        page = b.new_page(viewport={"width":1440,"height":1400})
        for path in paths:
            print(f"\n=== 通关验证: {path} ===", flush=True)
            ok, steps, detail = play_through(page, path)
            lv = json.load(open(path, encoding="utf-8"))["level"]
            print(f"标题: {lv.get('title')}", flush=True)
            print(f"机关: {[bt['action'] for bt in lv['beats'] if bt['action'] in ('password','angle','morse')]}", flush=True)
            print(f"结果: {'PASS' if ok else 'FAIL'} steps={steps}/{len(lv['beats'])} {detail}", flush=True)
            results.append((path, ok))
        b.close()
    print("\n========== 汇总 ==========", flush=True)
    for path, ok in results:
        print(f"{'PASS' if ok else 'FAIL'}  {path}", flush=True)
    sys.exit(0 if all(ok for _, ok in results) else 1)

if __name__ == "__main__":
    main(sys.argv[1:] or ["ref-game/llm_out/gen_v7_r1.room.json"])
