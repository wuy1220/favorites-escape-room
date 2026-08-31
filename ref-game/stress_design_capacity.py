# -*- coding: utf-8 -*-
"""GLM 结构复杂度压力测试:绕过 UI 直接调 designWindow(真实供应商),
素材 8/10/12 三档,验证「结构校验(designWindow 内置密度门槛)→ compile →
solveLevel 可解」全链。输出各档耗时/房间/步数/hidden/reveals/回访,
用于确定主页「单次素材数」选项的可用档位。项目根运行(需 8128 服务)。"""
import io
import json
import time

from playwright.sync_api import sync_playwright

CHROME = None
FIXTURES = [("fixtures/sample10-bookmarks.html", "sample10-bookmarks.html")]
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""), flush=True)


IN_PAGE = """
async (args) => {
  const { raws, tier, note } = args;
  const pl = window.__favoriteRoomPipeline;
  let items = [];
  for (const r of raws) {
    try { items = items.concat(pl.parse(r.html, r.name)); } catch (e) {}
  }
  const seen = new Set();
  items = items.filter((it) => {
    if (!it || !it.id || seen.has(String(it.id))) return false;
    seen.add(String(it.id));
    return true;
  });
  if (items.length < tier) return { error: '素材不足: 仅 ' + items.length + ' 条', wall: 0 };
  items = items.slice(0, tier);
  /* desc 富化(与生产 generate 同协议):接地检查(P46/P62)要求 sourceFacts 能在
     desc/标题/路径里原样找到——压力脚本必须先取回网页描述,否则模型引用域名等
     真实事实会被误判为编造 */
  try {
    const urls = items.map((it) => it.url).filter((u) => /^https?:/.test(u || ''));
    const res = await fetch('http://127.0.0.1:8128/fetch-meta', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ urls: urls, timeout: 4 }),
    });
    const data = await res.json();
    let descN = 0;
    items.forEach((it) => {
      const m = (data.results || {})[it.url];
      if (m && m.desc && String(m.desc).trim()) {
        it.description = String(m.desc).slice(0, 300);
        descN++;
      }
    });
    if (descN < Math.ceil(tier * 0.5))
      return { error: 'desc 富化不足: 仅 ' + descN + '/' + tier + ' 条取回描述' };
  } catch (e) { /* 富化失败继续,接地错误会如实暴露 */ }
  const cfg = await (await fetch('/api/llm-config')).json();
  const overrides = {
    endpoint: cfg.endpoint, model: cfg.model, apiKey: cfg.apiKey,
    thinking: cfg.thinking, reasoningEffort: cfg.reasoningEffort,
    designTimeout: cfg.designTimeout || 600000,
  };
  const t0 = Date.now();
  let designed;
  try {
    designed = await pl.designWindow(items, '', null, [], null, note || null, null, overrides, tier);
  } catch (e) {
    return { error: '设计校验: ' + ((e && (e.message || e.msg)) || JSON.stringify(e)).slice(0, 300),
             wall: (Date.now() - t0) / 1000 };
  }
  const cleaned = {
    records: items.map((it) => Object.assign({}, it, { status: 'keep' })),
    controlledIds: items.map((it) => it.id),
    duplicates: [],
    stats: { input: items.length, unique: items.length, duplicates: 0 },
  };
  let draft;
  try { draft = pl.compile(cleaned, null, designed.parsed, ''); }
  catch (e) {
    return { error: 'compile: ' + ((e && e.message) || String(e)).slice(0, 300),
             wall: (Date.now() - t0) / 1000 };
  }
  const solve = pl.solveLevel(draft.level);
  const lv = draft.level;
  const scenes = lv.scenes || [];
  const beats = lv.beats || [];
  const itemScene = {};
  scenes.forEach((sc, si) => (sc.itemIds || []).forEach((id) => (itemScene[String(id)] = si)));
  const perRoomHidden = scenes.map(
    (sc, si) => (sc.itemIds || []).filter((id) => {
      const it = lv.items.find((x) => String(x.id) === String(id));
      return it && it.hidden;
    }).length
  );
  const revTotal = beats.reduce((n, b) => n + ((b.reveals || []).length), 0);
  const useN = {};
  beats.forEach((b) => (b.uses || []).forEach((u) => {
    const s = String(u);
    if (!s.startsWith('result:')) useN[s] = (useN[s] || 0) + 1;
  }));
  const convReach = (() => {
    const sceneOf = {};
    scenes.forEach((sc, si) => (sc.beatIds || []).forEach((b) => (sceneOf[String(b)] = si)));
    const del = beats.find((b) => b.action === 'deliver');
    if (!del) return 0;
    const seenB = new Set(), reach = new Set(), stack = [String(del.id)];
    while (stack.length) {
      const id = stack.pop();
      if (seenB.has(id)) continue;
      seenB.add(id);
      if (sceneOf[id] !== undefined) reach.add(sceneOf[id]);
      const bb = beats.find((x) => String(x.id) === id);
      ((bb && bb.requires) || []).forEach((r) => { if (sceneOf[String(r)] !== undefined) stack.push(String(r)); });
    }
    return reach.size;
  })();
  if (!solve.solvable)
    return {
      error: '自动求解器无法通关——' + (solve.detail || '未知卡点'),
      wall: (Date.now() - t0) / 1000,
      structure: { rooms: scenes.length, beats: beats.length, hidden: lv.items.filter((it) => it.hidden).length },
    };
  return {
    wall: (Date.now() - t0) / 1000,
    rooms: scenes.length,
    roomTitles: scenes.map((s) => s.title || '').join('|'),
    beats: beats.length,
    hidden: lv.items.filter((it) => it.hidden).length,
    perRoomHidden: perRoomHidden.join('/'),
    reveals: revTotal,
    revisit: Object.keys(useN).filter((k) => useN[k] >= 2).length,
    closure: convReach,
    mechanics: (lv.mechanics || []).join(','),
    solvable: !!solve.solvable,
    solveDetail: solve.detail || '',
    theme: (lv.theme || '').slice(0, 50),
  };
}
"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.on("pageerror", lambda e: print("[pageerror]", str(e)[:160], flush=True))
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)

    raws = []
    for path, name in FIXTURES:
        raws.append({"html": io.open(path, encoding="utf-8").read(), "name": name})
    # 12 档素材:追加 user6 JSON(如解析失败自动降档)
    try:
        raws.append({
            "html": io.open("fixtures/user6-bookmarks.json", encoding="utf-8").read(),
            "name": "user6-bookmarks.json",
        })
    except OSError:
        pass

    summary = {}
    for tier in ([int(a) for a in __import__('sys').argv[1:]] or [8, 10, 12]):
        print(f"\n===== 档位 N={tier} =====", flush=True)
        note = ""
        t_tier0 = time.time()
        out = {}
        for attempt_i in range(3):
            # 生产同款修复轮:每档最多 3 次,失败带错误反馈重试(设计窗 repairNote)
            out = page.evaluate(IN_PAGE, {"raws": raws, "tier": tier, "note": note})
            if not out.get("error"):
                break
            note = out["error"]
            print(
                f"  [尝试 {attempt_i + 1}/3 失败] {out['error'][:150]}",
                flush=True,
            )
        out["wall"] = out.get("wall", 0) or (time.time() - t_tier0)
        summary[tier] = out
        if out.get("error"):
            check(f"N={tier}: 3 次尝试均失败(共 {out['wall']:.0f}s)", False, out["error"][:200])
            continue
        check(
            f"N={tier}: 全链通过 {out['wall']:.0f}s | 房间 {out['rooms']}({out['roomTitles']})"
            f" | 步数 {out['beats']} | hidden {out['hidden']}(每房 {out['perRoomHidden']})"
            f" | reveals {out['reveals']} | 回访 {out['revisit']} | 收束 {out['closure']} 房"
            f" | 可解 {out['solvable']}",
            out["solvable"] and out["rooms"] >= 2 and out["hidden"] >= out["rooms"],
            "mechanics=" + out["mechanics"] + " theme=" + out["theme"],
        )

    b.close()

print("\n===== 压力测试汇总 =====", flush=True)
for tier, out in summary.items():
    if out.get("error"):
        print(f"N={tier}: FAIL — {out['error'][:120]} (wall={out.get('wall', 0):.0f}s)", flush=True)
    else:
        print(
            f"N={tier}: PASS — {out['wall']:.0f}s, rooms={out['rooms']}, beats={out['beats']}, "
            f"hidden={out['hidden']}({out['perRoomHidden']}), reveals={out['reveals']}, "
            f"revisit={out['revisit']}, solvable={out['solvable']}",
            flush=True,
        )
ok_tiers = [t for t, o in summary.items() if not o.get("error") and o.get("solvable")]
print("可用档位:", ok_tiers or "无", flush=True)
raise SystemExit(0 if ok_tiers else 1)
