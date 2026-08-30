# -*- coding: utf-8 -*-
"""v7 批量质量门禁:真实 LLM 独立生成 3 版关卡。
每版:designWindow(范例模仿)→compileLevel→solveLevel(求解器)→导出 room.json→真实 DOM 通关验证。
统计通过率——生成质量是分布,单点通过不算数。"""
import json, time, math, os, sys
from playwright.sync_api import sync_playwright

CHROME = r"C:/Users/30807/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"
# 输出目录锚定脚本自身位置,与启动 cwd 无关(2026-08-28 从 ref-game/ 内启动时曾因相对路径崩溃)
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "llm_out")
# 可选:经环境变量切换 LLM 供应商做 A/B(默认走页面内置 step 配置)。
# V7_LLM_ENDPOINT / V7_LLM_MODEL / V7_LLM_APIKEY / V7_TAG,例如 OpenRouter:
#   V7_LLM_ENDPOINT=https://openrouter.ai/api/v1/chat/completions \
#   V7_LLM_MODEL=z-ai/glm-5.2:free V7_LLM_APIKEY=sk-or-... V7_TAG=gen_v7or
ENV_ENDPOINT = os.environ.get("V7_LLM_ENDPOINT", "")
ENV_MODEL = os.environ.get("V7_LLM_MODEL", "")
ENV_APIKEY = os.environ.get("V7_LLM_APIKEY", "")
ENV_THINKING = os.environ.get("V7_LLM_THINKING", "")
ENV_REASONING = os.environ.get("V7_LLM_REASONING_EFFORT", "")
ENV_DESIGN_TIMEOUT = os.environ.get("V7_LLM_DESIGNTIMEOUT", "")
TAG_PREFIX = os.environ.get("V7_TAG", "gen_v7")
INIT_CFG = ""
if ENV_ENDPOINT:
    import json as _json

    _cfg = {
        "endpoint": ENV_ENDPOINT,
        "model": ENV_MODEL or "step-3.7-flash",
        "apiKey": ENV_APIKEY,
    }
    if ENV_THINKING:
        # 2026-08-28 起 pipeline 支持 llmConfig.thinking 可配置;
        # glm-5.3-flash 等强制思考模型拒绝 {type:"disabled"},需显式给档位
        _cfg["thinking"] = _json.loads(ENV_THINKING)
    if ENV_REASONING:
        # GLM-5.2+/5.3 系列:顶层 reasoning_effort 控制思考强度,默认 max(慢到不可用);
        # GLM-5.3/5.3-FLASH 仅支持 low/high/max
        _cfg["reasoningEffort"] = ENV_REASONING
    if ENV_DESIGN_TIMEOUT:
        _cfg["designTimeout"] = int(ENV_DESIGN_TIMEOUT)
    INIT_CFG = "window.__FAVORITES_ROOM_CONFIG__ = " + _json.dumps(_cfg) + ";"
    print(
        f"[A/B] 覆盖 LLM 配置: endpoint={ENV_ENDPOINT} model={ENV_MODEL} "
        f"thinking={ENV_THINKING or '(默认)'} reasoningEffort={ENV_REASONING or '(默认)'} "
        f"designTimeout={ENV_DESIGN_TIMEOUT or '(默认)'}",
        flush=True,
    )
ITEMS = [
    {"id":"b0","title":"维基百科，自由的百科全书","domain":"zh.baidu.wikimirror.net","urlPath":"zh.baidu.wikimirror.net","folder":"书签栏 / AI/大模型","dateAdded":"2021-02-15T22:41","desc":"","fetchStatus":""},
    {"id":"b1","title":"蔚蓝主页","domain":"www.weilanzy.com","urlPath":"www.weilanzy.com","folder":"书签栏 / 其他","dateAdded":"2021-07-23T17:28","desc":"","fetchStatus":""},
    {"id":"b2","title":"台风路径","domain":"typhoon.zjwater.gov.cn","urlPath":"typhoon.zjwater.gov.cn","folder":"书签栏 / 其他","dateAdded":"2021-07-30T09:41","desc":"","fetchStatus":""},
    {"id":"b3","title":"关于本计划 | The No More Ransom Project","domain":"www.nomoreransom.org","urlPath":"www.nomoreransom.org","folder":"书签栏 / 其他","dateAdded":"2021-07-30T09:41","desc":"","fetchStatus":""},
    {"id":"b4","title":"VirSCAN.org - Free Multi-Engine Online Virus Scanner v1.02, Supports 47 AntiVirus Engines!","domain":"www.virscan.org","urlPath":"www.virscan.org","folder":"书签栏 / 其他","dateAdded":"2021-07-30T16:03","desc":"","fetchStatus":""},
    {"id":"b5","title":"VirusTotal","domain":"www.virustotal.com","urlPath":"www.virustotal.com","folder":"书签栏 / 安全/工具","dateAdded":"2021-07-30T17:02","desc":"","fetchStatus":""},
]
WIN = {"label":"2021-02-15 ~ 2021-07-30","count":6,"mood":"深夜"}
THEME = "深夜书房"
def enrich(it):
    return {"id":it["id"],"title":it["title"],"domain":it["domain"],"url":"http://"+it["domain"],
            "dateAdded":it["dateAdded"],"status":"keep","urlPath":it["urlPath"],"folder":it.get("folder","")}
REC = [enrich(it) for it in ITEMS]
IDS = [it["id"] for it in ITEMS]

def gen_one(page, idx):
    code = """async (payload) => {
      const pipe = window.__favoriteRoomPipeline;
      const cleaned = {records: payload.records, controlledIds: payload.ids, duplicates: [], stats:{input:6,unique:6,duplicates:0}};
      const log = [];
      let repairNote = '', designed = null, draft = null;
      for (let round = 0; round < 3; round++) {
        try {
          designed = await pipe.designWindow(payload.records, payload.theme, payload.win, [], function(m){ console.log('[design] ' + m); }, repairNote);
        } catch(de) {
          log.push({round, stage:'design-fatal', err:String(de && de.message || de).slice(0,120)});
          if (round === 2) return {ok:false, log, why:'design-x9'};
          repairNote = String(de && de.message || de); continue;
        }
        try { draft = pipe.compile(cleaned, null, designed.parsed, payload.theme); }
        catch(se) {
          log.push({round, stage:'compile-throw', err:String(se && se.message || se).slice(0,120)});
          if (round === 2) return {ok:false, log, why:'structural-x3'};
          repairNote = String(se && se.message || se); continue;
        }
        const solve = pipe.solveLevel(draft.level);
        log.push({round, stage:'compiled+solved', solvable: solve.solvable, detail: String(solve.detail||'').slice(0,120),
                  designSource: draft.level.validation.designSource, beats: draft.level.beats.length});
        if (!solve.solvable && round < 2) { repairNote = '自动求解器无法通关——' + String(solve.detail||''); draft = null; continue; }
        return {ok: solve.solvable, log, level: draft.level, roundsUsed: round+1, designSource: draft.level.validation.designSource};
      }
      return {ok:false, log, why:'unsolvable-x3'};
    }"""
    res = page.evaluate(code, {"records": REC, "ids": IDS, "theme": THEME, "win": WIN})
    return res

def play_through(page, path):
    """真实 DOM 通关(同 verify_gen.py 逻辑)。"""
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
        """目标物件不可见时,按 flat 关卡的显形路径触发(环顾四周),JS click 绕过按钮可见性检查。"""
        s = sel(u)
        if page.locator(s).first.count() and page.locator(s).first.is_visible():
            return
        for _ in range(2):
            page.evaluate("() => { const b = document.getElementById('revisitRoom'); if (b) b.click(); }")
            time.sleep(0.4)
            if page.locator(s).first.count() and page.locator(s).first.is_visible():
                return
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
    page.wait_for_selector(sel(beats[0]["uses"][0]) if beats[0]["uses"] else '[data-id="root"]', timeout=10000)
    ok_steps = 0
    for i, b in enumerate(beats):
        try:
            # 防御:关闭残留的机关面板(避免拦截后续点击)
            page.evaluate("() => ['keypadModal','morseModal','angleModal'].forEach(id => { const e = document.getElementById(id); if (e) e.classList.add('hidden'); })")
            if b["action"] in ("inspect", "revisit"):
                for u in b["uses"]:  # 多 id 观察步:引擎要求全部点过才完成
                    ensure_visible(u)
                    click(sel(u))
            elif b["action"] == "combine":
                ensure_visible(b["uses"][1])
                drag(sel(b["uses"][0]), sel(b["uses"][1]))
            elif b["action"] == "sequence":
                for u in b["uses"]:
                    ensure_visible(u); click(sel(u))
            elif b["action"] == "password":
                ensure_visible(b["uses"][0])
                click(sel(b["uses"][0]))
                page.wait_for_selector('#keypadModal:not(.hidden)', timeout=5000)
                for k in str(b["expected"]):
                    page.locator(f'#keypad [data-k="{k}"]').click(); time.sleep(0.12)
                time.sleep(0.4)
            elif b["action"] == "morse":
                ensure_visible(b["uses"][0])
                click(sel(b["uses"][0]))
                page.wait_for_selector('#morseModal:not(.hidden)', timeout=5000)
                for ch in str(b["code"]):
                    if ch == '.': page.locator('#morseDot').click()
                    elif ch == '-': page.locator('#morseDash').click()
                    elif ch == '/': page.locator('#morseSlash').click()
                    time.sleep(0.05)
                page.locator('#morseEnter').click(); time.sleep(0.4)
            elif b["action"] == "angle":
                ensure_visible(b["uses"][0])
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
                ensure_visible(b["uses"][0])
                drag(sel(b["uses"][0]), '[data-id="compiled-exit"]'); time.sleep(0.3)
            ok_steps += 1
        except Exception as e:
            return False, ok_steps, f"step{i+1}({b['action']}) {str(e)[:90]}"
    snap = page.evaluate("() => (window.__favoriteRoomRuntime && window.__favoriteRoomRuntime.snapshot()) || null")
    done = bool(snap and snap.get("done"))
    return done, ok_steps, f"clues={snap.get('clues') if snap else None}"

summary = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page(viewport={"width": 1440, "height": 1400})
    if INIT_CFG:
        page.add_init_script(INIT_CFG)
    page.on(
        "console",
        lambda m: m.text.startswith("[design]")
        and print("[design]", m.text[8:], flush=True),
    )
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!(window.__favoriteRoomPipeline && window.__favoriteRoomPipeline.solveLevel)", timeout=15000)
    for i in (1, 2, 3):
        print(f"\n########## 第 {i} 版生成 ##########", flush=True)
        t0 = time.time()
        r = gen_one(page, i)
        print("ROUNDS:", json.dumps(r.get("log"), ensure_ascii=False), flush=True)
        tag = f"{TAG_PREFIX}_r{i}"
        if r.get("ok"):
            lv = r["level"]
            locks = [bt["action"] for bt in lv["beats"] if bt["action"] in ("password","angle","morse")]
            sem = sum(1 for bt in lv["beats"] if bt.get("product") or bt.get("resultOn") or bt.get("consume"))
            room = {"records": REC, "controlledIds": IDS, "items": REC, "level": lv}
            path = os.path.join(OUT_DIR, f"{tag}.room.json")
            json.dump(room, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"GEN-OK 轮次={r['roundsUsed']} 来源={r['designSource']} beats={len(lv['beats'])} 机关={locks} 语义字段步数={sem} 导出={path} 用时={time.time()-t0:.0f}s", flush=True)
            print("TITLE:", lv.get("title"), flush=True)
            print("OBJECTIVE:", (lv.get("objective") or "")[:100], flush=True)
            ok, steps, detail = play_through(page, path)
            print(f"PLAY: {'PASS' if ok else 'FAIL'} steps={steps}/{len(lv['beats'])} {detail}", flush=True)
            summary.append((tag, r["ok"], r["designSource"], locks, ok))
        else:
            print(f"GEN-FAIL: {r.get('why')}", flush=True)
            summary.append((tag, False, "-", [], False))
    b.close()

print("\n========== v7 批量质量门禁汇总 ==========", flush=True)
for tag, gen_ok, src, locks, play_ok in summary:
    print(f"{tag}: 生成+求解={'PASS' if gen_ok else 'FAIL'} 来源={src} 机关={locks} DOM通关={'PASS' if play_ok else 'FAIL'}")
total = sum(1 for _, g, _, _, pl in summary if g and pl)
print(f"通过率: {total}/{len(summary)}")
sys.exit(0 if total == len(summary) else 1)
