# -*- coding: utf-8 -*-
"""存档管理端到端验证:导入关卡 -> 列表三按钮 -> 导出下载 -> 删除清空。"""
import json, time
from playwright.sync_api import sync_playwright
URL = "http://127.0.0.1:8128/"
CHROME = r"C:/Users/30807/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"
PUZZLE = r"C:/Users/30807/Documents/Codex/2026-08-20/superpowers-brainstorming-c-users-30807-codex-2/projects/favorites-escape-room/ref-game/llm_out/gen_s0.room.json"
results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail)); print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))
    if not ok: raise SystemExit("中断于: " + name)
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    ctx = b.new_context(viewport={"width":1440,"height":1000}, accept_downloads=True)
    page = ctx.new_page()
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    # 1) 通过导入关卡建立存档(loadLevelText -> mountLevel),并手动写入 levels/progress
    page.set_input_files("#homeImportFile", PUZZLE)
    page.wait_for_function("() => document.getElementById('gameToolbar') && !document.getElementById('gameToolbar').hasAttribute('hidden')", timeout=10000)
    check("导入关卡进入游戏", True)
    st = page.evaluate("""async () => {
        const lv = await window.__favoriteRoomHome ? null : null;
        // 取当前 draft 存为 levels 记录
        const raw = localStorage.getItem('favorite-room-draft');
        const draft = JSON.parse(raw);
        const record = {id:'save-test-1', projectId:'save-test', cacheKey:'save-test', name:draft.level.title||'测试关卡', theme:'测试', draft, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString()};
        await window.__favoriteRoomHome ? null : null;
        return {name:record.name};
    }""")
    # 用 dbPut 写入 levels + progress(通过页面内部函数不可直接访问,改从 home 对象拿)
    st2 = page.evaluate("""async () => {
        const raw = localStorage.getItem('favorite-room-draft');
        const draft = JSON.parse(raw);
        const record = {id:'save-test-1', projectId:'save-test', cacheKey:'save-test', name:draft.level.title||'测试关卡', theme:'测试', draft, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString()};
        // dbPut/dbDelete 在闭包内;通过 UI 流程:直接写 localStorage 不行,需要 IndexedDB。
        // 用生成流程写入:调用 pipeline 存? 简化:页面有 dbPut 吗?没有公开。
        return {ok:false};
    }""")
    # 改为:直接用页面闭包不可行,通过重新导入触发 mountLevel 已够;删除/导出测试改用 __favoriteRoomHome 公开函数 + 手动 IndexedDB 写入
    res = page.evaluate("""async () => {
        // 手动写 IndexedDB(复制 dbPut 逻辑)
        const open = () => new Promise((res,rej)=>{const r=indexedDB.open('favorites-escape-room-local');r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)});
        const db = await open();
        const put = (store,val) => new Promise((res,rej)=>{const tx=db.transaction(store,'readwrite');tx.objectStore(store).put(val);tx.oncomplete=()=>res(true);tx.onerror=()=>rej(tx.error)});
        const raw = localStorage.getItem('favorite-room-draft');
        const draft = JSON.parse(raw);
        const record = {id:'save-test-1', projectId:'save-test', cacheKey:'save-test', name:draft.level.title||'测试关卡', theme:'测试', draft, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString()};
        await put('levels', record);
        await put('progress', {id:'save-test-1', levelId:'save-test-1', snapshot:{version:3,started:true,done:false,clues:[]}, updatedAt:new Date().toISOString()});
        // 回首页刷新列表
        document.getElementById('gameHome').click();
        await new Promise(r=>setTimeout(r,400));
        return {ok:true};
    }""")
    check("写入测试存档", bool(res.get("ok")))
    # 2) 列表三按钮
    time.sleep(0.5)
    btns = page.evaluate("""() => {
        const rows = document.querySelectorAll('.saved-row');
        if (!rows.length) return {count:0, opens:0, exports:0, dels:0, html:''};
        const row = rows[0];
        return {count:rows.length, opens:row.querySelectorAll('.saved-open').length,
                exports:row.querySelectorAll('.saved-export').length,
                dels:row.querySelectorAll('.saved-del').length,
                text: row.innerText};
    }""")
    check("列表每行含 打开/导出/删除 三按钮", btns.get("count")>=1 and btns["opens"]==1 and btns["exports"]==1 and btns["dels"]==1, json.dumps(btns, ensure_ascii=False)[:200])
    # 3) 导出下载
    dl = None
    with page.expect_download(timeout=8000) as dl_info:
        page.evaluate("() => document.querySelector('.saved-export').click()")
    dl = dl_info.value
    check("导出触发下载(.room.json)", dl is not None and dl.suggested_filename.endswith('.room.json'), dl.suggested_filename if dl else '')
    # 4) 删除(覆盖 confirm)
    page.evaluate("() => { window.confirm = () => true }")
    page.evaluate("async () => { await window.__favoriteRoomHome.deleteLevel('save-test-1'); return true }")
    time.sleep(0.5)  # 等 IndexedDB 提交完成,避免读事务快照竞态
    after = page.evaluate("""() => new Promise((res) => {
        const r = indexedDB.open('favorites-escape-room-local');
        r.onsuccess = () => { const db=r.result;
            const tx=db.transaction(['levels','progress']); 
            const g1=tx.objectStore('levels').getAll(), g2=tx.objectStore('progress').getAll();
            tx.oncomplete = () => res({
                levels: g1.result.length, progress: g2.result.length,
                hasLevel: g1.result.some(x=>x.id==='save-test-1'),
                hasProgress: g2.result.some(x=>x.id==='save-test-1'),
                rows: document.querySelectorAll('.saved-row').length});
        };
    })""")
    # 2026-08-28 语义更新:UI 导入的关卡现在会持久化(审查 11.2.6 修复),删除 save-test-1 后列表中剩下的是那条持久化的导入关卡
    check("删除后 save-test-1 的 levels/progress 清空", (not after["hasLevel"]) and (not after["hasProgress"]), json.dumps(after, ensure_ascii=False))
    # ===== 追加(2026-08-28 审查 11.2.6):UI 导入持久化回归 =====
    # UI 导入关卡 → 刷新页面 → 已保存列表必须出现该关卡(旧实现只 mount 不写库)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    page.set_input_files("#homeImportFile", PUZZLE)
    page.wait_for_function(
        "() => document.getElementById('gameToolbar') && !document.getElementById('gameToolbar').hasAttribute('hidden')",
        timeout=10000,
    )
    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#homeScreen", timeout=15000)
    page.wait_for_timeout(800)
    rows = page.evaluate(
        "() => Array.from(document.querySelectorAll('#savedList .saved-row strong')).map((e) => e.textContent)"
    )
    check(
        "UI 导入持久化:刷新后已保存列表出现导入关卡",
        len(rows) >= 1,
        "rows=" + json.dumps(rows, ensure_ascii=False)[:120],
    )
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n===== 结果: {passed}/{len(results)} 通过 =====")
    b.close()
