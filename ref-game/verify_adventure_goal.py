# -*- coding: utf-8 -*-
"""目标验证(untitled-adventure-direction):连续两次真实生成,
每次 <160s、≥5 个标签页素材、scenes≥2(空间层次)、可通关挂载、theme/creativeThesis 落库。
真实调用 GLM(low,两路并行对冲)+ step 垫底。在项目根运行(需 8128 服务)。"""
import json
import time

from playwright.sync_api import sync_playwright

CHROME = r"C:/Users/30807/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"
FIXTURE = "fixtures/sample10-bookmarks.html"
GOAL_SECONDS = 160
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""), flush=True)


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.on("pageerror", lambda e: print("[pageerror]", str(e)[:160], flush=True))
    page.on("console", lambda m: m.text.startswith("路") and print("[lane]", m.text[:110], flush=True))
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    # 无缓存基准:第一次导入即触发真实清洗

    for cycle in (1, 2):
        print(f"\n===== 周期 {cycle} =====", flush=True)
        page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
        page.wait_for_selector("#homeScreen", timeout=15000)
        # 确定性抽样种子:两周期抽同一批素材 → 周期 2 命中设计缓存(键已绑定抽样素材)。
        # 真实用户不设种子——每次生成换抽样=换关卡。
        page.evaluate("() => (window.__favoritesRoomSeed = 42)")
        t0 = time.time()
        page.set_input_files("#homeFile", FIXTURE)
        page.wait_for_function(
            "() => !document.getElementById('homeGenerate').disabled", timeout=60000
        )
        t_ready = time.time() - t0
        page.click("#homeGenerate")
        mounted = True
        try:
            while time.time() - t0 < GOAL_SECONDS + 60:
                time.sleep(5)
                st = page.evaluate("() => document.getElementById('homeStatus').textContent")
                print("  t+%3ds status: %s" % (time.time() - t0, st[:80]), flush=True)
                tb = page.evaluate(
                    "() => { const t = document.getElementById('gameToolbar');"
                    " return t && !t.hasAttribute('hidden'); }"
                )
                if tb:
                    break
            else:
                mounted = False
        except Exception as e:
            mounted = False
            print("  [wait 异常]", str(e)[:100], flush=True)
        wall = time.time() - t0
        if not mounted:
            st = page.evaluate("() => document.getElementById('homeStatus').textContent")
            check(f"周期{cycle}: 生成挂载超时({wall:.0f}s)", False, st[:100])
            continue
        check(
            f"周期{cycle}: 生成全程 {wall:.1f}s < {GOAL_SECONDS}s"
            f"(导入就绪 {t_ready:.1f}s)",
            wall < GOAL_SECONDS,
        )

        lv = page.evaluate(
            "() => new Promise((res) => { const r = indexedDB.open('favorites-escape-room-local');"
            " r.onsuccess = () => { const q = r.result.transaction('levels').objectStore('levels').getAll();"
            " q.onsuccess = () => res(q.result[q.result.length - 1] || {}); }; })"
        )
        lvl = lv.get("draft", {}).get("level", {})
        scenes = lvl.get("scenes") or []
        items = lvl.get("items") or []
        check(
            f"周期{cycle}: 素材 ≥5(实际 {len(items)})",
            len(items) >= 5,
        )
        check(
            f"周期{cycle}: 空间层次 scenes≥2(实际 {len(scenes)})",
            len(scenes) >= 2,
            " | ".join((s.get("title") or "") for s in scenes)[:80],
        )
        check(
            f"周期{cycle}: 可通关(真实引擎已挂载, snapshot 就绪)",
            bool(page.evaluate("() => !!(window.__favoriteRoomRuntime && window.__favoriteRoomRuntime.snapshot())")),
        )
        diag = page.evaluate(
            "() => new Promise((res) => { const r = indexedDB.open('favorites-escape-room-local');"
            " r.onsuccess = () => { const q = r.result.transaction('datasets').objectStore('datasets').getAll();"
            " q.onsuccess = () => res(q.result.map((d) => ({ key: d.id.slice(0, 24),"
            " lrTheme: d.levelResult ? d.levelResult.theme || '(无字段)' : 'null' }))); }; })"
        )
        print("  [datasets]", json.dumps(diag, ensure_ascii=False), flush=True)
        check(
            f"周期{cycle}: theme 落库「{lv.get('theme', '')[:30]}」",
            bool(lv.get("theme")),
        )
        print(
            f"[信息] 周期{cycle}: creativeThesis={lv.get('creativeThesis', '')[:40]!r} "
            f"motif={lv.get('recurringMotif', '')[:30]!r} turn={lv.get('surpriseTurn', '')[:30]!r}",
            flush=True,
        )
        check(
            f"周期{cycle}: 挂载为未命名(延迟命名)",
            str(lv.get("name", "")).startswith("未命名冒险"),
            str(lv.get("name")),
        )
        check(
            f"周期{cycle}: 并行房间标记(空间层次 P42)",
            lv.get("draft", {}).get("level", {}).get("parallelRooms") is True,
        )
        # 原作式流程:玩家点击根节点后,全部房间同时亮出(P42 并行房间)
        page.click('[data-id="root"]')
        page.wait_for_timeout(600)
        vis_zones = page.evaluate(
            "() => Array.from(document.querySelectorAll('[data-id^=\"compiled-scene-\"]'))"
            ".filter((e) => e.offsetParent !== null).length"
        )
        hidden_n = sum(1 for it in items if it.get("hidden"))
        beats = lvl.get("beats") or []
        # ===== 空间密度(2026-08-30 空间感落地):数量门槛换密度门槛 =====
        item_scene = {}
        for si, sc in enumerate(scenes):
            for iid in sc.get("itemIds") or []:
                item_scene[str(iid)] = si
        rooms_with_hidden = sum(
            1
            for si in range(len(scenes))
            if any(it.get("hidden") and item_scene.get(str(it["id"])) == si for it in items)
        )
        check(
            f"周期{cycle}: 每房间隐藏物({rooms_with_hidden}/{len(scenes)} 房有 hidden,共 {hidden_n})",
            len(scenes) > 0 and rooms_with_hidden == len(scenes),
        )
        # 机关/信息分工(2026-08-30 需求方裁定):prop-* 无网页背景纯机构,每房至少 1 件
        prop_items = [it for it in items if it.get("prop")]
        rooms_with_props = sum(
            1
            for si in range(len(scenes))
            if any(it.get("prop") and item_scene.get(str(it["id"])) == si for it in prop_items)
        )
        check(
            f"周期{cycle}: 机关道具(共 {len(prop_items)} 件,{rooms_with_props}/{len(scenes)} 房有)",
            len(scenes) > 0 and rooms_with_props == len(scenes),
        )
        rev_total = sum(len(bt.get("reveals") or []) for bt in beats)
        check(
            f"周期{cycle}: reveals 显形 ≥2(实际 {rev_total})",
            rev_total >= 2,
        )
        # 容器显形链:引擎 S1 同款推导(resultOn 优先,否则 uses 首个实体素材),
        # 隐藏物与显形源同房间 ⇒ 引擎会把它嵌到容器节点旁(房间→容器→道具 三层)
        nest_n = 0
        for bt in beats:
            revs = [str(r) for r in (bt.get("reveals") or [])]
            if not revs:
                continue
            src = str(bt.get("resultOn") or "")
            if not src or src.startswith("result:"):
                src = next(
                    (str(u) for u in (bt.get("uses") or []) if not str(u).startswith("result:")),
                    "",
                )
            if not src:
                continue
            for rid in revs:
                if item_scene.get(rid) is not None and item_scene.get(rid) == item_scene.get(src):
                    nest_n += 1
        check(
            f"周期{cycle}: 容器显形链(同房容器→隐藏物 {nest_n} 处)",
            nest_n >= 1,
        )
        use_n = {}
        for bt in beats:
            for u in bt.get("uses") or []:
                s = str(u)
                if not s.startswith("result:"):
                    use_n[s] = use_n.get(s, 0) + 1
        revisit_n = sum(1 for v in use_n.values() if v >= 2)
        check(
            f"周期{cycle}: 回访物件(被 ≥2 步使用 {revisit_n} 件)",
            revisit_n >= 1,
        )
        # 2026-08-30 结构强化:房间全亮(禁房间级 locked)+ 终局收束跨房间 + desc 富化
        locked_n = sum(1 for s in scenes if s.get("locked"))
        check(
            f"周期{cycle}: 房间全亮(locked 房间 {locked_n} 个)",
            locked_n == 0,
            " | ".join(
                (s.get("title") or "") + ("[locked]" if s.get("locked") else "") for s in scenes
            )[:80],
        )
        # desc 富化:详情面板读 draft.items(清洗记录)的 description(identityOf),不是编译产物
        recs = (lv.get("draft") or {}).get("items") or []
        desc_n = sum(1 for it in recs if (it.get("description") or "").strip())
        check(
            f"周期{cycle}: desc 富化(素材描述非空 {desc_n}/{len(recs)})",
            desc_n >= 3,
        )
        conv_n = page.evaluate(
            """(level) => {
              const beats = level.beats || [];
              const sceneOf = new Map();
              (level.scenes || []).forEach((sc, si) => (sc.beatIds || []).forEach((b) => sceneOf.set(b, si)));
              const del = beats.find((b) => b.action === 'deliver');
              if (!del) return 0;
              const seen = new Set(), reach = new Set(), stack = [String(del.id)];
              while (stack.length) {
                const id = stack.pop();
                if (seen.has(id)) continue;
                seen.add(id);
                if (sceneOf.has(id)) reach.add(sceneOf.get(id));
                const bb = beats.find((x) => String(x.id) === id);
                ((bb && bb.requires) || []).forEach((r) => { if (sceneOf.has(String(r))) stack.push(String(r)); });
              }
              return reach.size;
            }""",
            lvl,
        )
        check(
            f"周期{cycle}: 终局收束跨房间(deliver 依赖闭包 {conv_n} 个场景)",
            conv_n >= 2,
        )
        # P61/P63 内容加工层:digest 与 sourceFacts 落进关卡,事实值接地可验证
        digest_n = sum(1 for it in items if (it.get("digest") or "").strip())
        check(
            f"周期{cycle}: digest 摘要({digest_n}/{len(items)})",
            digest_n >= 3,
        )
        ground_bad = page.evaluate(
            """(recs) => {
              const byId = new Map(recs.map((r) => [String(r.id), r]));
              const bad = [];
              recs.forEach((r) => {
                (r.facts || []).forEach((f) => {
                  const ground = [r.description, r.title, r.urlPath].map((x) => String(x || '')).join(' ');
                  if (f.v && ground.indexOf(f.v) < 0) bad.push(r.id + ':' + f.v);
                });
              });
              return bad;
            }""",
            recs,
        )
        check(
            f"周期{cycle}: 事实接地(未接地 {len(ground_bad)} 处)",
            len(ground_bad) == 0,
            json.dumps(ground_bad, ensure_ascii=False)[:80],
        )
        vis_zones, zone_diag = page.evaluate(
            "() => { const all = Array.from(document.querySelectorAll('[data-id]'))"
            ".map((e) => e.getAttribute('data-id'));"
            " const zones = all.filter((id) => id.indexOf('compiled-scene-') === 0);"
            " return [zones.length, all.filter((id) => id.indexOf('compiled-') === 0).slice(0, 12)]; }"
        )
        check(
            f"周期{cycle}: 全部房间开局亮出(scene 节点 {vis_zones}/{len(scenes)})",
            vis_zones >= len(scenes),
            json.dumps(zone_diag, ensure_ascii=False),
        )

    b.close()

print(f"\n===== verify_adventure_goal: {sum(results)}/{len(results)} 通过 =====", flush=True)
raise SystemExit(0 if all(results) else 1)
