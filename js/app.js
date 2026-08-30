/* Product shell: local projects, cached cleaning results, levels and progress. */
(function () {
  const DB_NAME = 'favorites-escape-room-local',
    DB_VERSION = 2,
    MODEL_VERSION = 'freeform-v3';
  let dbPromise = null,
    currentLevel = null,
    autoTimer = null,
    pendingWindows = [],
    selectedWindow = null,
    lastCleaned = null,
    /* 异步任务令牌(审查 11.2.7):换文件/换窗口时递增,旧回调检查到令牌变化即放弃写入 */
    importToken = 0;
  const $ = (id) => document.getElementById(id),
    esc = (value) =>
      String(value ?? '').replace(
        /[&<>"']/g,
        (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
      );
  function openDb() {
    if (dbPromise) return dbPromise;
    dbPromise = new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = () => {
        const db = req.result;
        ['projects', 'datasets', 'levels', 'progress', 'verdicts'].forEach((name) => {
          if (!db.objectStoreNames.contains(name)) db.createObjectStore(name, { keyPath: 'id' });
        });
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error || new Error('本地存档初始化失败'));
    });
    return dbPromise;
  }
  function dbPut(store, value) {
    return openDb().then(
      (db) =>
        new Promise((resolve, reject) => {
          let done = false;
          const fin = (ok, v) => {
            if (done) return;
            done = true;
            ok ? resolve(v) : reject(v);
          };
          const tx = db.transaction(store, 'readwrite');
          tx.objectStore(store).put(value);
          tx.oncomplete = () => fin(true, value);
          tx.onerror = () => fin(false, tx.error || new Error('本地存档写入失败'));
          tx.onabort = () => fin(false, tx.error || new Error('本地存档写入中止'));
          /* 兜底:事务停滞(竞争/配额)时 15 秒后放行,不让生成流程永久卡死 */ setTimeout(
            () => fin(false, new Error('本地存档写入超时')),
            15000,
          );
        }),
    );
  }
  function dbGet(store, id) {
    return openDb().then(
      (db) =>
        new Promise((resolve, reject) => {
          const req = db.transaction(store).objectStore(store).get(id);
          req.onsuccess = () => resolve(req.result || null);
          req.onerror = () => reject(req.error || new Error('本地存档读取失败'));
        }),
    );
  }
  function dbDelete(store, id) {
    return openDb().then(
      (db) =>
        new Promise((resolve, reject) => {
          const tx = db.transaction(store, 'readwrite');
          tx.objectStore(store).delete(id);
          tx.oncomplete = () => resolve(true);
          tx.onerror = () => reject(tx.error || new Error('本地存档删除失败'));
          tx.onabort = () => reject(tx.error || new Error('本地存档删除中止'));
        }),
    );
  }
  function dbAll(store) {
    return openDb().then(
      (db) =>
        new Promise((resolve, reject) => {
          const req = db.transaction(store).objectStore(store).getAll();
          req.onsuccess = () => resolve(req.result || []);
          req.onerror = () => reject(req.error || new Error('本地存档读取失败'));
        }),
    );
  }
  function dbClear(store) {
    return openDb().then(
      (db) =>
        new Promise((resolve, reject) => {
          const tx = db.transaction(store, 'readwrite');
          tx.objectStore(store).clear();
          tx.oncomplete = () => resolve(true);
          tx.onerror = () => reject(tx.error || new Error('本地存档清空失败'));
          tx.onabort = () => reject(tx.error || new Error('本地存档清空中止'));
        }),
    );
  }
  async function hashText(raw) {
    const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(raw));
    return [...new Uint8Array(bytes)].map((x) => x.toString(16).padStart(2, '0')).join('');
  }
  /* ---------- 时间窗检测:把收藏按时间戳切成"心绪切片" ---------- */
  function detectTimeWindows(items) {
    const GAP = 7 * 24 * 3600 * 1000,
      MIN_WINDOW = 4;
    const timed = items
      .filter((it) => it.dateAdded)
      .map((it) => ({ ...it, _t: new Date(it.dateAdded).getTime() }))
      .sort((a, b) => a._t - b._t);
    if (!timed.length) return [];
    const windows = [];
    let cur = [timed[0]];
    for (let i = 1; i < timed.length; i++) {
      if (timed[i]._t - cur[cur.length - 1]._t > GAP) {
        windows.push(cur);
        cur = [];
      }
      cur.push(timed[i]);
    }
    windows.push(cur);
    return windows
      .filter((w) => w.length >= MIN_WINDOW)
      .map(function (w, wi) {
        const hours = w.map((x) => new Date(x._t).getHours());
        const night = hours.filter((h) => h < 6 || h >= 23).length / w.length;
        const folders = {};
        w.forEach((x) => {
          if (x.folder) folders[x.folder] = (folders[x.folder] || 0) + 1;
        });
        const topFolders = Object.entries(folders)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 2)
          .map((e) => e[0]);
        const day = new Date(w[0]._t),
          last = new Date(w[w.length - 1]._t);
        const span = w[w.length - 1]._t - w[0]._t;
        const fmt = (d) => d.getFullYear() + '年' + (d.getMonth() + 1) + '月' + d.getDate() + '日';
        return {
          index: wi,
          from: w[0]._t,
          to: w[w.length - 1]._t,
          count: w.length,
          label:
            span < 36 * 3600 * 1000
              ? fmt(day) + ' 的深夜到清晨'
              : span < 8 * 24 * 3600 * 1000
                ? fmt(day) + ' 起的一周'
                : fmt(day) + ' — ' + fmt(last),
          spanDays: Math.round(span / 86400000) + 1,
          moodPref:
            night >= 0.5
              ? '深夜'
              : hours.filter((h) => h >= 9 && h < 18).length / w.length >= 0.6
                ? '白天'
                : '夜晚',
          nightRatio: night,
          topFolders,
          items: w.map((x) => x.id),
        };
      })
      .sort((a, b) => b.from - a.from);
  }
  /* ---------- 内容层富化:服务端尽力抓取 ---------- */
  async function fetchMetaInto(items, report) {
    /* 上限 64:全量导入(数百条)时被选中入谜的素材必须被覆盖;服务端 6 并发×4s
       超时,64 条最坏 ~43s,与清洗并行不增加导入墙钟 */
    const targets = items.filter((it) => it.url && /^https?:/.test(it.url)).slice(0, 64);
    if (!targets.length) return;
    report && report('正在回访 ' + targets.length + ' 个页面，取回当时的细节……');
    try {
      const controller = new AbortController(),
        /* 75s:64 条 × 4s 超时 ÷ 服务端 6 并发 ≈ 43s 最坏情况,30s 会提前掐断整批 */
        timer = setTimeout(() => controller.abort(), 75000);
      let res;
      try {
        res = await fetch('http://127.0.0.1:8128/fetch-meta', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ urls: targets.map((t) => t.url), timeout: 4 }),
          signal: controller.signal,
        });
      } finally {
        clearTimeout(timer);
      }
      const data = await res.json();
      const results = data.results || {};
      /* 可观测性(交接复核建议):desc 富化成功率此前完全不可观测,
         先上报再谈优化——零行为变化,只记录与展示。 */
      const entries = targets.map((t) => results[t.url]).filter(Boolean);
      const ok200 = entries.filter((m) => m.status === 200).length;
      const withTitle = entries.filter((m) => m.title && m.title.trim()).length;
      const withDesc = entries.filter((m) => m.desc && m.desc.trim()).length;
      window.__lastFetchMeta = {
        total: targets.length,
        ok200,
        withTitle,
        withDesc,
        at: new Date().toISOString(),
      };
      report &&
        report(
          '页面回访完成:' + ok200 + '/' + targets.length + ' 条取回成功(含标题 ' + withTitle + ' 条)。',
        );
      targets.forEach(function (t) {
        const m = results[t.url];
        if (!m) return;
        /* 身份层优先:页面真实标题 > 书签标题; 站点级书签标题且抓到页面级标题时升级 */
        if (m.title && m.title.trim()) {
          const siteLevel =
            /^(?:首页|主页|home|homepage|welcome|index)$/i.test(t.title) ||
            t.title.trim() === t.domain ||
            (t.title.length <= 6 && m.title.length > t.title.length * 2);
          if (siteLevel || !/\s/.test(t.title)) {
            t.fetchedTitle = m.title;
            t.title = m.title;
          }
        }
        if (m.desc && !t.description) t.description = m.desc.slice(0, 300);
        t.fetchStatus = m.status;
      });
    } catch (_) {
      /* 抓取失败完全无害:行为层仍然完整 */
    }
  }
  function themeValue() {
    /* 2026-08-28:自动主题(默认)——返回 '' 表示由 LLM 依据素材自行决定;
       选择固定风格时返回风格名,补充描述作为倾向合并。 */
    const sel = $('homeTheme')?.value || '';
    const hint = ($('homeThemeCustom')?.value || '').replace(/\s+/g, ' ').trim();
    if (!sel) return '';
    return (sel + ' ' + hint).trim();
  }
  function setStatus(message, kind) {
    const el = $('homeStatus');
    if (el) {
      el.textContent = message;
      el.dataset.kind = kind || '';
    }
  }
  function hideLegacy() {
    document.querySelector('.shell')?.style.setProperty('display', 'none');
    $('intro')?.classList.add('hidden');
    $('importModal')?.classList.add('hidden');
    $('cleanModal')?.classList.add('hidden');
    $('importBookmarks')?.style.setProperty('display', 'none');
  }
  function showGame() {
    document.querySelector('.shell')?.style.setProperty('display', '');
    $('homeScreen')?.classList.add('hidden');
    $('gameToolbar')?.removeAttribute('hidden');
    $('intro')?.classList.add('hidden');
  }
  function showHome() {
    if (autoTimer) {
      clearInterval(autoTimer);
      autoTimer = null;
    }
    /* 11.12 #7:离开关卡即停命名轮询,不得在标题页空转 */
    stopNamingWatch();
    document.querySelector('.shell')?.style.setProperty('display', 'none');
    $('gameToolbar')?.setAttribute('hidden', '');
    $('homeScreen')?.classList.remove('hidden');
    $('intro')?.classList.add('hidden');
    refreshSaved();
  }
  function mountLevel(record, snapshot) {
    currentLevel = record;
    localStorage.setItem('favorite-room-draft', JSON.stringify(record.draft));
    localStorage.setItem('favorite-room-current', record.id);
    roomReset();
    if (window.__favoriteRoomRuntime)
      window.__favoriteRoomRuntime.activateRoot(
        record.name || record.draft?.level?.title || '收藏关卡',
        record.draft?.level?.premise,
      );
    if (typeof render === 'function') render();
    if (typeof applyView === 'function') applyView();
    roomRender();
    drawLinks();
    inspect(get('root'));
    frontier('imported'); /* frontier 覆写(engine)会补触发 compiledObjective:横幅+步数即出关卡口径 */
    showGame();
    /* 顶栏随关卡切换:内部标题在通关命名前不展示(P37 延迟命名),kicker 只标注进行中状态 */
    const topKick = document.querySelector('.topbar .kicker');
    if (topKick) topKick.textContent = '收藏夹密室 / 未命名冒险';
    $('gameTitle').textContent = record.name || record.draft?.level?.title || '收藏关卡';
    if (snapshot && window.__favoriteRoomRuntime) window.__favoriteRoomRuntime.restore(snapshot);
    startAutoSave();
  }
  async function saveProgress(silent) {
    if (!currentLevel || !window.__favoriteRoomRuntime) return;
    const snapshot = window.__favoriteRoomRuntime.snapshot();
    if (!snapshot) return;
    try {
      await dbPut('progress', {
        id: currentLevel.id,
        levelId: currentLevel.id,
        snapshot,
        updatedAt: new Date().toISOString(),
      });
      if (!silent) setStatus('进度已保存', 'good');
    } catch (err) {
      if (!silent) setStatus(err.message, 'error');
    }
  }
  function startAutoSave() {
    if (autoTimer) clearInterval(autoTimer);
    if ($('homeAutoSave')?.checked !== false)
      autoTimer = setInterval(() => saveProgress(true), 4000);
  }
  /* 11.12 产品动作「重置本关」(唯一入口):保留关卡记录与工具栏标题,重建同一关卡
     初始运行态(引擎 resetCurrentLevel:底座重建+activateRoot+机关上下文/弹窗/视图清理),
     并把初始态快照写回 progress——刷新后「继续游戏」恢复的是重置后(未开始)的进度,
     不再出现 UI/运行态/存档三方失配。 */
  async function resetCurrentLevel() {
    $('namingModal')?.classList.add('hidden');
    stopNamingWatch();
    if (window.__favoriteRoomRuntime && window.__favoriteRoomRuntime.resetCurrentLevel)
      window.__favoriteRoomRuntime.resetCurrentLevel();
    if (!currentLevel) return;
    $('gameTitle').textContent =
      currentLevel.name || currentLevel.draft?.level?.title || '收藏关卡';
    if (typeof inspect === 'function' && typeof get === 'function') inspect(get('root'));
    if (typeof frontier === 'function') frontier('imported');
    showGame();
    startNamingWatch(currentLevel.id);
    await saveProgress(true);
  }
  async function refreshSaved() {
    const list = $('savedList'),
      continueBtn = $('homeContinue');
    if (!list) return;
    try {
      const levels = (await dbAll('levels')).sort((a, b) =>
          String(b.updatedAt || b.createdAt).localeCompare(String(a.updatedAt || a.createdAt)),
        ),
        progress = await dbAll('progress'),
        pm = new Map(progress.map((x) => [x.levelId, x]));
      continueBtn.disabled = !progress.length;
      list.innerHTML = levels.length
        ? levels
            .map((level) => {
              const p = pm.get(level.id),
                pct = p?.snapshot?.done ? '已完成' : p?.snapshot?.started ? '进行中' : '未开始';
              return (
                '<div class="saved-row"><div><strong>' +
                esc(level.name || level.draft?.level?.title || '未命名关卡') +
                '</strong><small>' +
                esc(level.theme || '未指定风格') +
                ' · ' +
                pct +
                '</small></div><div class="saved-actions"><button class="saved-open" data-level="' +
                esc(level.id) +
                '">打开</button><button class="saved-export" data-level="' +
                esc(level.id) +
                '">导出</button><button class="saved-del" data-level="' +
                esc(level.id) +
                '">删除</button></div></div>'
              );
            })
            .join('')
        : '<div class="saved-empty">还没有保存的关卡。</div>';
      list.querySelectorAll('.saved-open').forEach(
        (btn) =>
          (btn.onclick = async () => {
            const level = await dbGet('levels', btn.dataset.level),
              p = await dbGet('progress', btn.dataset.level);
            if (level) mountLevel(level, p?.snapshot);
          }),
      );
      list.querySelectorAll('.saved-export').forEach(
        (btn) =>
          (btn.onclick = async () => {
            const level = await dbGet('levels', btn.dataset.level);
            if (level) exportLevelRecord(level, setStatus);
          }),
      );
      list
        .querySelectorAll('.saved-del')
        .forEach((btn) => (btn.onclick = () => deleteLevel(btn.dataset.level)));
    } catch (err) {
      list.innerHTML = '<div class="saved-empty">' + esc(err.message) + '</div>';
      continueBtn.disabled = true;
    }
  }
  function selectControlledPool(records, wantCount) {
    /* wantCount(2026-08-30):单次素材条数 6-12,默认 6;越高结构越复杂 */
    const wantN = Math.max(6, Math.min(12, Number(wantCount) || 6));
    const candidates = (records || []).filter((it) => it.status === 'keep');
    /* 随机抽样(2026-08-30 需求方工作流):点生成后在时间片内随机选一批标签页,
       每次生成的素材组合都不同;洗牌后按域名多样性贪心取 6(多样性保留,
       顺序随机化),最后仍按收藏时间升序排入(机制链=时间链)。
       验收测试可注入 window.__favoritesRoomSeed(有限数)获得确定性抽样。 */
    let rnd = Math.random;
    const seed = Number(window.__favoritesRoomSeed);
    if (Number.isFinite(seed)) {
      let s = seed >>> 0 || 1;
      rnd = () => {
        s = (s + 0x6d2b79f5) | 0;
        let t = Math.imul(s ^ (s >>> 15), 1 | s);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
      };
    }
    for (let i = candidates.length - 1; i > 0; i--) {
      const j = Math.floor(rnd() * (i + 1));
      [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
    }
    const picked = [],
      domains = new Set();
    candidates.forEach((it) => {
      if (picked.length >= wantN || domains.has(it.domain)) return;
      picked.push(it);
      if (it.domain) domains.add(it.domain);
    });
    candidates.forEach((it) => {
      if (picked.length < wantN && !picked.includes(it)) picked.push(it);
    });
    const pool = picked.slice(0, wantN);
    /* 机制链=时间链:按收藏时间升序排入模板,让"从最早两条开始、按时间推进"成为真实通关逻辑 */ const t =
      (it) => {
        const n = Date.parse(it.dateAdded);
        return Number.isFinite(n) ? n : Number.MAX_SAFE_INTEGER;
      };
    return pool
      .slice()
      .sort((a, b) => t(a) - t(b) || String(a.title).localeCompare(String(b.title)));
  }
  /* ===== 生成工作台(2026-08-30):把黑盒等待变成可感知的工作过程 =====
     底线(方向文档):进度只来自真实阶段事件——不放假百分比,不展示模型思维链;
     形成中的设计不进面板(那是管线内部状态),面板只呈现阶段/素材/赛马/日志这些事实。
     收起为浮标时,完成不抢占屏幕,由用户点击「已生成 · 点击进入」再挂载。 */
  const WB_PHASES = ['选出素材', '读取来源', '设计竞速', '整理回执', '进入冒险'];
  const wbState = {
    running: false,
    t0: 0,
    timer: null,
    collapsed: false,
    cancelled: false,
    pendingRecord: null,
    laneSignals: [],
    laneRows: [],
  };
  function wbEl(id) {
    return document.getElementById(id);
  }
  function wbSecs() {
    return Math.round((Date.now() - wbState.t0) / 1000);
  }
  function wbTick() {
    const t = wbSecs() + 's';
    const e = wbEl('wbElapsed');
    if (e) e.textContent = t;
    if (wbState.collapsed && wbState.running) {
      const p = wbEl('genPillText');
      if (p) p.textContent = '生成中 · ' + t;
    }
  }
  function wbPhasesRender(cur) {
    const box = wbEl('wbPhases');
    if (!box) return;
    box.innerHTML = WB_PHASES.map(
      (p, i) =>
        '<span class="wb-phase' +
        (i < cur ? ' done' : i === cur ? ' active' : '') +
        '">' +
        p +
        '</span>',
    ).join('');
  }
  function wbPhase(i) {
    wbPhasesRender(i);
  }
  function wbLog(text, kind) {
    const box = wbEl('wbLog');
    if (!box) return;
    const line = document.createElement('div');
    line.className = 'wb-logline' + (kind ? ' ' + kind : '');
    line.textContent = '[+' + wbSecs() + 's] ' + text;
    box.prepend(line);
    while (box.children.length > 50) box.removeChild(box.lastChild);
  }
  function wbLanesInit(defs) {
    const box = wbEl('wbLanes');
    if (!box) return;
    box.innerHTML = '';
    wbState.laneRows = defs.map((d, i) => {
      const row = document.createElement('div');
      row.className = 'wb-lane';
      row.innerHTML =
        '<span class="wb-lane-label">路' + (i + 1) + '(' + esc(d.label) + ')</span>' +
        '<span class="wb-lane-status">排队中</span>';
      box.appendChild(row);
      return row;
    });
  }
  function wbLane(i, status, cls) {
    const row = wbState.laneRows[i];
    if (!row) return;
    row.querySelector('.wb-lane-status').textContent = status;
    row.className = 'wb-lane' + (cls ? ' ' + cls : '');
  }
  function wbMaterials(items) {
    const box = wbEl('wbMaterials');
    if (!box) return;
    box.innerHTML = items
      .map((it) => {
        const url = String(it.canonicalUrl || it.url || '');
        return (
          '<a class="wb-mat" href="' + esc(url) + '" target="_blank" rel="noreferrer" title="打开原网页">' +
          '<b>' + esc(String(it.title || '').slice(0, 30)) + '</b><small>' + esc(it.domain || '') + '</small></a>'
        );
      })
      .join('');
  }
  function wbPillHide() {
    const p = wbEl('genPill');
    if (p) {
      p.hidden = true;
      p.classList.remove('done');
    }
  }
  function wbPillDone() {
    const p = wbEl('genPill');
    if (!p) return;
    p.hidden = false;
    p.classList.add('done');
    wbEl('genPillText').textContent = '已生成 · 点击进入';
  }
  function wbFinish() {
    wbState.running = false;
    if (wbState.timer) {
      clearInterval(wbState.timer);
      wbState.timer = null;
    }
    const panel = wbEl('genWorkbench');
    if (panel) panel.hidden = true;
  }
  function wbCancel() {
    if (!wbState.running || wbState.cancelled) return;
    wbState.cancelled = true;
    (wbState.laneSignals || []).forEach((s) => {
      try {
        s.abort();
      } catch (_) {}
    });
    (wbState.laneRows || []).forEach((row, i) => {
      const st = row.querySelector('.wb-lane-status');
      if (st && st.textContent.indexOf('✓') < 0) wbLane(i, '已取消', 'bad');
    });
    wbLog('已取消生成——在途请求已中止。', 'bad');
    wbPillHide();
    wbFinish();
  }
  function wbBegin() {
    wbState.running = true;
    wbState.cancelled = false;
    wbState.pendingRecord = null;
    wbState.collapsed = false;
    wbState.laneRows = [];
    wbState.laneSignals = [];
    wbState.t0 = Date.now();
    const panel = wbEl('genWorkbench');
    if (panel) {
      panel.hidden = false;
      wbEl('wbLanes').innerHTML = '';
      wbEl('wbLog').innerHTML = '';
      wbEl('wbMaterials').innerHTML = '';
      wbEl('wbMin').textContent = '收起';
    }
    wbPillHide();
    wbPhase(0);
    if (wbState.timer) clearInterval(wbState.timer);
    wbState.timer = setInterval(wbTick, 1000);
    wbTick();
    wbEl('wbMin').onclick = function () {
      wbState.collapsed = !wbState.collapsed;
      if (wbEl('genWorkbench')) wbEl('genWorkbench').hidden = wbState.collapsed;
      const pill = wbEl('genPill');
      if (pill && wbState.running) {
        pill.hidden = !wbState.collapsed;
        if (wbState.collapsed) wbEl('genPillText').textContent = '生成中 · ' + wbSecs() + 's';
      }
    };
    wbEl('wbCancel').onclick = function () {
      wbCancel();
    };
    wbEl('genPill').onclick = function () {
      if (wbState.pendingRecord) {
        const rec = wbState.pendingRecord;
        wbState.pendingRecord = null;
        wbPillHide();
        setStatus('进入已生成的冒险……', 'good');
        mountLevel(rec);
        startNamingWatch(rec.id);
      } else if (wbState.running) {
        wbEl('wbMin').onclick();
      }
    };
  }
  async function generate() {
    const file = $('homeFile')?.files?.[0];
    if (!file) return;
    const button = $('homeGenerate');
    button.disabled = true;
    setStatus('正在读取收藏夹……', 'busy');
    wbBegin();
    const token = ++importToken;
    try {
      const raw = await file.text(),
        sourceHash = await hashText(raw);
      if (token !== importToken) return;
      /* ===== 时间窗管线 v4:选窗 → 本地初筛 → 服务端抓取 → 设计 LLM ===== */
      const theme = themeValue(),
        win = selectedWindow;
      const themeHint = ($('homeThemeCustom')?.value || '').replace(/\s+/g, ' ').trim();
      const materialCount = Math.max(
        6,
        Math.min(12, Number($('homeMaterialCount')?.value) || 6),
      );
      if (!lastCleaned) throw new Error('请先上传收藏夹完成全局清洗');
      const approved = lastCleaned.records.filter((r) => r.status === 'keep');
      const items = win ? approved.filter((it) => win.items.includes(it.id)) : approved;
      if (items.length < 6)
        throw new Error('这段时间片内通过清洗的素材不足 6 条，换一个时间片试试');
      const kept = selectControlledPool(items, materialCount);
      if (kept.length < 6)
        throw new Error('清洗后只有 ' + kept.length + ' 条通过素材,固定密室需要 6 条');
      setStatus('时间片「' + (win ? win.label : '全部收藏') + '」: 已随机选定 ' + kept.length + ' 条受控素材。', 'busy');
      wbPhase(1);
      wbLog('已随机选定 ' + kept.length + ' 条素材(时间片「' + (win ? win.label : '全部收藏') + '」),点击卡片可查看来源。');
      wbMaterials(kept);
      /* 内容层富化(2026-08-30,按需求方工作流回归生成路径):点生成后先回访这批
         随机素材的网页,取回真实 desc 再交给设计 LLM——谜面得以引用页面内容而非
         只玩域名数字。desc 经 buildVerdicts 写回标记记录,下次导入/生成零重复抓取;
         6 条 × 4s 超时 ÷ 服务端 6 并发,墙钟 ≲6s,不威胁 160s 预算。 */
      try {
        await fetchMetaInto(kept, (m) => setStatus(m, 'busy'));
        for (const v of window.__favoriteRoomPipeline.buildVerdicts(kept))
          await dbPut('verdicts', v);
      } catch (fe) {
        console.warn('desc 富化失败:', fe && fe.message);
      }
      if (wbState.cancelled) throw new Error('已取消生成');
      wbPhase(2);
      /* 组装设计输入:行为层+内容层事实都在手 */
      const enriched = kept.map(function (it) {
        let path = '';
        try {
          const u = new URL(it.url);
          path = decodeURIComponent(u.pathname).replace(/\+/g, ' ');
        } catch (_) {}
        return { ...it, urlPath: path };
      });
      const duplicates = lastCleaned.duplicates || [];
      const windowContext = win
        ? {
            label: win.label,
            count: win.count,
            spanDays: win.spanDays,
            mood: win.moodPref,
            nightRatio: Math.round(win.nightRatio * 100),
            topFolders: win.topFolders,
            themeHint,
          }
        : themeHint
        ? { themeHint }
        : null;
      /* 缓存键纳入本次抽样(2026-08-30):此前键=时间窗+文件哈希+主题,同一文件
         再点生成会**直接回放同一关**(设计调用都不发生)——随机抽样形同虚设,
         用户视角即"总是生成相同的关卡"。现在键绑定被抽中的 6 条素材:
         同抽样复用设计(快),换抽样必走新设计(有变化)。 */
      const cacheKey = [
        'tw',
        win ? String(win.from) : 'all',
        win ? String(win.to) : '',
        sourceHash.slice(0, 16),
        theme,
        MODEL_VERSION,
        kept
          .map((it) => it.id)
          .sort()
          .join('|'),
      ].join('::');
      const existing = await dbGet('datasets', cacheKey);
      let draft;
      let cacheGood = false; /* v7.2:只有"新鲜生成且通过求解器"的设计才允许写缓存——失败轮的被拒设计稿绝不能入缓存 */
      if (existing && existing.levelResult) {
        setStatus('这个时间片的关卡已生成过，正在复用（换主题词可重新设计）……', 'busy');
        const cachedClean = Array.isArray(existing.cleaned)
          ? {
              records: existing.cleaned,
              controlledIds: existing.controlledIds || existing.cleaned.map((item) => item.id),
            }
          : {
              ...existing.cleaned,
              controlledIds: existing.controlledIds || existing.cleaned?.controlledIds,
            };
        try {
          draft = window.__favoriteRoomPipeline.compile(
            cachedClean,
            null,
            existing.levelResult,
            theme,
          );
        } catch (_) {
          draft = null;
        }
        /* v7.2:缓存复用也要过求解器——旧版本代码/失败轮写入的坏设计稿不允许直接回放 */
        if (draft && !window.__favoriteRoomPipeline.solveLevel(draft.level).solvable) {
          draft = null;
          setStatus('缓存里的旧设计无法通关，重新设计……', 'busy');
        }
        if (draft) cacheGood = true;
        if (draft) {
          wbLog('缓存命中:本批素材的既有设计通过求解复核,直接复用。');
          wbPhase(4);
        }
      }
      let outerWinner = null;
      if (!draft) {
        /* v7:范例模仿设计→编译→solveLevel 执行验证。结构错误与"求解器卡住"都带反馈重新设计(最多 3 轮);
         3 轮全败退回固定结构模板(至少可玩)。 */
        const cleaned = {
          records: enriched,
          controlledIds: enriched.map((item) => item.id),
          duplicates,
          stats: { input: items.length, unique: enriched.length, duplicates: duplicates.length },
        };
        /* v8 多路赛马(2026-08-28):laneCount 路并行设计,每路独立带修复轮(compile 结构校验 +
           solveLevel 求解门禁),取最先产出可解谜题的一路;赢者确定后经 externalSignal 掐掉
           其余各路的在途调用。最坏配额与旧串行 3 轮相同(3×3),期望延迟 = 最快一路。
           配置:designLanes(默认 3,钳位 1-4;设 1 即旧串行行为)。全部失败退回固定模板。 */
        const laneCount = Math.max(
          1,
          Math.min(4, Number(window.__FAVORITES_ROOM_CONFIG__?.designLanes) || 3),
        );
        /* 多供应商赛马(2026-08-28):备用路线(glm)由 /api/llm-config 提供,
           路线轮转 [step, glm, step, ...],取最先产出可解谜题的一路。 */
        /* 双供应商并行赛马(2026-08-29):glm(快,~1-2.5min)+step advisor(质量兜底)。
           每供应商各一路——同供应商并发会被平台排队(glm×2 实测反而更慢)。
           整体失败自动重试一轮(对抗限流),两轮全败退回固定模板。 */
        const glmLane = window.__GLM_LANE__ || null;
        const laneDefs = glmLane
          ? [
              { overrides: null, label: 'step' },
              { overrides: glmLane, label: 'glm' },
            ]
          : [
              { overrides: null, label: 'step' },
              { overrides: null, label: 'step' },
            ];
        setStatus(
          '设计进行中:' + laneDefs.map((l) => l.label).join(' + ') + '……',
          'busy',
        );
        const raceState = { won: false, remaining: laneDefs.length };
        const laneSignals = [];
        wbState.laneSignals = laneSignals;
        wbLanesInit(laneDefs);
        wbLog('设计竞速开始:' + laneDefs.map((l) => l.label).join(' + ') + ' 并行,取最先通过求解验证的一路。');
        const raceT0 = Date.now();
        const raceClock = setInterval(function () {
          if (raceState.won) return;
          setStatus(
            '设计进行中……已等待 ' + Math.round((Date.now() - raceT0) / 1000) + ' 秒',
            'busy',
          );
        }, 5000);
        const winner = await (async function runRace() {
          for (let raceAttempt = 0; raceAttempt < 2; raceAttempt++) {
            if (wbState.cancelled) return null;
            if (raceAttempt) {
              setStatus('各路均未通过，10 秒后整体重试……', 'busy');
              wbLog('各路均未通过,10 秒后整体重试。', 'bad');
              await new Promise((r) => setTimeout(r, 10000));
              if (wbState.cancelled) return null;
            }
            raceState.won = false;
            raceState.remaining = laneDefs.length;
            const res = await new Promise((resolveRace) => {
              const lane = async function (laneIdx) {
                const signal = new AbortController();
                laneSignals.push(signal);
                let note = '';
                const providerLabel = laneDefs[laneIdx].label;
                for (let round = 0; round < 3; round++) {
                  if (raceState.won || wbState.cancelled) return { failNote: note };
                  wbLane(laneIdx, '第' + (round + 1) + '轮 · 设计中');
                  let laneDesigned = null;
                  try {
                    laneDesigned = await window.__favoriteRoomPipeline.designWindow(
                      enriched,
                      theme,
                      windowContext,
                      duplicates,
                      (msg) => {
                        if (raceState.won) return;
                        setStatus('路' + (laneIdx + 1) + '(' + providerLabel + '): ' + msg, 'busy');
                        wbLog('路' + (laneIdx + 1) + '(' + providerLabel + '): ' + msg);
                      },
                      note,
                      signal.signal,
                      laneDefs[laneIdx].overrides,
                      materialCount,
                    );
                  } catch (de) {
                    if (raceState.won) return { failNote: note };
                    note = (de && de.message) || String(de);
                    if (wbState.cancelled) return { failNote: note };
                    setStatus(
                      '路' + (laneIdx + 1) + '(' + providerLabel + ') 第' + (round + 1) + ' 轮未通过(' + note.slice(0, 50) + ')……',
                      'busy',
                    );
                    wbLog('路' + (laneIdx + 1) + '(' + providerLabel + ') 第' + (round + 1) + ' 轮未通过:' + note.slice(0, 80), 'bad');
                    wbLane(laneIdx, '第' + (round + 1) + '轮被拒 · 重试', 'bad');
                    continue;
                  }
                  let laneDraft = null;
                  try {
                    laneDraft = window.__favoriteRoomPipeline.compile(
                      cleaned,
                      null,
                      laneDesigned.parsed,
                      theme,
                    );
                  } catch (se) {
                    note = (se && se.message) || String(se);
                    if (wbState.cancelled) return { failNote: note };
                    setStatus(
                      '路' + (laneIdx + 1) + '(' + providerLabel + ') 第' + (round + 1) + ' 轮结构不合规(' + note.slice(0, 50) + ')……',
                      'busy',
                    );
                    wbLog('路' + (laneIdx + 1) + '(' + providerLabel + ') 第' + (round + 1) + ' 轮结构不合规:' + note.slice(0, 80), 'bad');
                    wbLane(laneIdx, '第' + (round + 1) + '轮结构打回 · 重试', 'bad');
                    continue;
                  }
                  const solve = window.__favoriteRoomPipeline.solveLevel(laneDraft.level);
                  if (!solve.solvable) {
                    note = '自动求解器无法通关——' + (solve.detail || '未知卡点');
                    if (wbState.cancelled) return { failNote: note };
                    setStatus(
                      '路' + (laneIdx + 1) + '(' + providerLabel + ') 第' + (round + 1) + ' 轮求解失败(' + note.slice(0, 50) + ')……',
                      'busy',
                    );
                    wbLog('路' + (laneIdx + 1) + '(' + providerLabel + ') 第' + (round + 1) + ' 轮求解失败:' + note.slice(0, 80), 'bad');
                    wbLane(laneIdx, '第' + (round + 1) + '轮求解失败 · 重试', 'bad');
                    continue;
                  }
                  wbLane(laneIdx, '✓ 第' + (round + 1) + '轮通过设计与求解验证', 'ok');
                  return {
                    draft: laneDraft,
                    parsed: laneDesigned.parsed,
                    laneIdx,
                    providerLabel,
                    rounds: round + 1,
                  };
                }
                wbLane(laneIdx, '三轮均未通过', 'bad');
                return { failNote: note };
              };
              for (let i = 0; i < laneDefs.length; i++) {
                lane(i).then((res) => {
                  if (res && res.draft && !raceState.won) {
                    raceState.won = true;
                    laneSignals.forEach((s) => s.abort());
                    laneDefs.forEach((d, i2) => {
                      if (i2 !== res.laneIdx) wbLane(i2, '已中止(他路先过)');
                    });
                    wbLog(
                      '路' + (res.laneIdx + 1) + '(' + (res.providerLabel || 'step') + ')率先通过,其余各路已中止。',
                      'ok',
                    );
                    resolveRace(res);
                    return;
                  }
                  if (res && res.failNote) {
                    try {
                      window.__lastDesignIssues = res.failNote;
                    } catch (_) {}
                  }
                  if (--raceState.remaining === 0 && !raceState.won) resolveRace(null);
                });
              }
            });
            if (res) return res;
          }
          return null;
        })();
        draft = null;
        clearInterval(raceClock);
        if (wbState.cancelled) throw new Error('已取消生成');
        wbPhase(3);
        if (winner) {
          outerWinner = winner;
          draft = winner.draft;
          designed = { parsed: winner.parsed };
          cacheGood = true;
          setStatus(
            '第 ' + (winner.laneIdx + 1) + ' 路(' + (winner.providerLabel || 'step') + ') 第 ' + winner.rounds + ' 轮通过设计+求解验证。',
            'good',
          );
        } else {
          setStatus('各路设计均未通过，退回固定结构模板(保证可玩)……', 'busy');
          wbLog('各路设计均未通过,退回固定结构模板(保证可玩)。', 'bad');
          draft = window.__favoriteRoomPipeline.compileFixed(
            cleaned,
            {
              title: '收藏夹密室 · 固定模板',
              premise: 'LLM 设计未通过验证，已退回固定结构。',
              theme: '收藏夹密室 · 固定结构兜底',
            },
            theme,
          );
        }
        /* 持久化非致命:写档失败只提示,不阻断进入游戏。
         v7.2:只有通过求解器的新鲜设计才入缓存(levelResult=null 的记录下次会被重新设计覆盖) */
        try {
          await dbPut('datasets', {
            id: cacheKey,
            sourceHash,
            theme,
            promptVersion: MODEL_VERSION,
            cleaned,
            controlledIds: cleaned.controlledIds,
            modelResult: null,
            levelResult: cacheGood && designed ? designed.parsed : null,
            windowContext,
            createdAt: new Date().toISOString(),
          });
        } catch (pe) {
          console.warn('数据集存档失败:', pe && pe.message);
        }
      }
      const projectId = 'project-' + sourceHash.slice(0, 16);
      try {
        await dbPut('projects', {
          id: projectId,
          name: file.name.replace(/\.(html?|json)$/i, ''),
          sourceName: file.name,
          sourceHash,
          theme,
          createdAt: new Date().toISOString(),
        });
      } catch (pe) {
        console.warn('项目存档失败:', pe && pe.message);
      }
      draft.level.timeWindow = win
        ? { label: win.label, count: win.count, mood: win.moodPref }
        : null;
      const levelId =
        'level-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 7);
      draft.level.id = levelId;
      /* 自动主题:优先用 LLM 在设计稿里写明的 theme(契合素材),否则回退用户选择 */
      draft.level.theme =
        draft.level.theme ||
        (outerWinner && outerWinner.parsed && (outerWinner.parsed.theme || (outerWinner.parsed.level || {}).theme)) ||
        theme ||
        '';
      const record = {
        id: levelId,
        projectId,
        cacheKey,
        name:
          '未命名冒险 · ' + new Date().toISOString().slice(5, 16).replace('T', ' '),
        llmTitle: draft.level.title || '',
        source: 'generate',
        theme: draft.level.theme || theme || '',
        draft,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      try {
        await dbPut('levels', record);
      } catch (pe) {
        console.warn('关卡存档失败:', pe && pe.message);
      }
      if (token !== importToken) return;
      wbLog('关卡编译与求解验证全部通过,写入存档完成。', 'ok');
      if (wbState.collapsed) {
        /* 收起状态不抢占屏幕:记录已落库,浮标亮「已生成 · 点击进入」 */
        wbState.pendingRecord = record;
        setStatus('生成完成。浮标已亮起,点击进入冒险。', 'good');
        wbFinish();
        wbPillDone();
      } else {
        setStatus('生成完成，正在进入游戏……', 'good');
        wbFinish();
        mountLevel(record);
        startNamingWatch(record.id);
      }
    } catch (err) {
      if (wbState.cancelled) setStatus('已取消生成。', 'busy');
      else setStatus(err.message || '生成失败', 'error');
    } finally {
      button.disabled = false;
      refreshSaved();
      wbFinish();
    }
  }
  function addUi() {
    /* 2026-08-29 UI 系统化:主页/工具栏/命名弹窗的样式全部迁入 css/styles.css
       (设计令牌见 css/tokens.css),此处只注入 DOM 结构;功能 id 与
       JS 切换的内联 display 钩子原样保留。 */
    if (document.getElementById('homeScreen')) return; /* 幂等:openDb 失败兜底会二次调用,重复注入会让两层卡片互相拦截点击 */
    document.body.insertAdjacentHTML(
      'beforeend',
      '<div class="product-home" id="homeScreen"><div class="home-card"><div class="home-layout"><section><div class="home-kicker">收藏夹密室 / LOCAL EDITION</div><h2>把收藏变成一间<em>可以玩的房间</em>。</h2><p>上传一次收藏夹，选择一段时间片。那 6 条受控素材会填入多房间回访结构(条数可在下方调整),成为一间只属于你的密室。中间结果保存在当前浏览器，下一次生成可以复用。</p><div class="home-steps"><div class="home-step"><div class="step-no">01</div><div class="step-body"><label class="home-field">选择收藏夹导出文件（Chrome 书签 HTML / Bookmarks JSON）<input class="home-file" id="homeFile" type="file" accept=".html,.htm,.json,text/html,application/json"></label></div></div><div class="home-step"><div class="step-no">02</div><div class="step-body"><label class="home-field">情绪或边界偏好（可选）<textarea id="homeThemeCustom" placeholder="例如：深夜、克制、不要恐怖元素——只作为联想起点，不预设主题"></textarea></label><label class="home-field">单次使用的网页数量（素材越多，房间与谜题链越复杂，生成也越慢）<select id="homeMaterialCount"><option value="6" selected>6 条 · 默认（约 2 分钟）</option><option value="8">8 条 · 进阶（3 间房间，实测约 2-3 分钟）</option><option value="10">10 条 · 实验（结构门槛常打回，可能多轮重试或失败）</option></select></label><label class="home-check"><input id="homeAutoSave" type="checkbox" checked> 自动保存游玩进度</label></div></div><div class="home-step" id="windowPanel" style="display:none"><div class="step-no">03</div><div class="step-body"><div class="home-kicker">选择一段时间片 —— 那段时间的你，将变成一间密室</div><div id="windowList" class="window-list"></div></div></div></div><div class="home-actions"><button class="primary" id="homeGenerate" disabled>生成一次未命名冒险</button></div><div class="gen-workbench" id="genWorkbench" hidden data-phase="0"><svg class="wb-sil" viewBox="0 0 420 170" aria-hidden="true"><g class="sil-g sil-1" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M30 150 H390"/><path d="M38 150 V46"/><path d="M382 150 V52"/><path d="M38 46 H180"/><path d="M382 52 H300"/></g><g class="sil-g sil-2" fill="none" stroke="currentColor" stroke-width="1.3"><rect x="252" y="96" width="86" height="54" rx="2"/><path d="M252 116 h86 M295 96 v54"/><path d="M120 118 h110 v32 h-110 z"/><path d="M130 150 v-8 M220 150 v-8"/></g><g class="sil-g sil-3" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M160 118 v-20 h24 v20"/><path d="M172 98 v-10"/><circle cx="172" cy="84" r="5"/><path d="M150 66 L172 78 M194 66 L172 78 M172 60 v16"/></g><g class="sil-g sil-4" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="46" y="70" width="52" height="80" rx="2"/><circle cx="92" cy="112" r="2.5"/></g></svg><div class="wb-head"><div class="wb-title">深夜工房——你的密室正在搭建</div><div class="wb-actions"><span class="wb-elapsed" id="wbElapsed" title="已用时间">0s</span><button id="wbMin" type="button" title="收起为浮标,生成在后台继续">收起</button><button id="wbCancel" type="button">取消生成</button></div></div><div class="wb-phases" id="wbPhases"></div><div class="wb-stage"><div class="wb-deck" id="wbDeck"></div><div class="wb-drafts" id="wbLanes"></div></div><div class="wb-notes" id="wbNotes"></div><details class="wb-facts"><summary>工作记录(技术细节)</summary><div class="wb-log" id="wbLog"></div></details></div><div class="home-secondary"><button id="homeImport" type="button">导入关卡</button><input id="homeImportFile" type="file" accept=".json,application/json" style="display:none"><button id="homeFixedTest" type="button">试玩固定样本</button><button id="homeContinue" disabled>继续游戏</button><button id="homeClearCache" type="button">清空清洗缓存</button></div><div class="home-status" id="homeStatus">等待上传收藏夹。</div></section><section class="saved-panel"><h3>已保存关卡</h3><p>关卡和清洗结果都保存在当前浏览器。原始收藏夹不会上传保存。</p><div id="savedList" class="saved-list"><div class="saved-empty">正在读取本地存档……</div></div></section></div></div></div><div class="modal hidden" id="namingModal"><div class="modal-card"><div class="kicker">通关 / 延迟命名</div><h2>这场冒险还没有名字。</h2><p>先给它起一个只属于你的名字——下方候选标题由你的收藏事实生成，每一个都只是一种理解，不是标准答案。</p><input id="adventureNameInput" class="naming-input" placeholder="为这场冒险命名……"><div id="nameCandidates" class="name-candidates"></div><div class="modal-actions"><button class="primary" id="adventureNameSave" type="button">以此命名</button><button id="adventureNameDone" type="button" style="display:none">查看回执并结束</button></div><div id="adventureReceipt" class="adventure-receipt" style="display:none"></div></div></div><div class="game-toolbar" id="gameToolbar" hidden><strong id="gameTitle">收藏关卡</strong><button id="gameSave" type="button">保存进度</button><button id="gameExport" type="button">导出关卡</button><button id="gameHome" type="button">标题界面</button></div><div class="gen-pill" id="genPill" hidden><span id="genPillText">生成中…</span></div>',
    );
  }
  async function boot() {
    addUi();
    hideLegacy();
    /* 沉浸式画布浮层(2026-08-30):线索便签 + 工作记录,均挂在画布上按需展开 */
    const hintFloat = $('hintFloat');
    const logFloat = $('logFloat');
    $('hintBtn').onclick = () => {
      hintFloat.classList.toggle('hidden');
      logFloat.classList.add('hidden');
    };
    $('logTicker').onclick = () => {
      logFloat.classList.toggle('hidden');
      hintFloat.classList.add('hidden');
    };
    $('logFloatClose').onclick = () => logFloat.classList.add('hidden');
    /* engine levelStart 自动展开线索便签(新手引导) */
    window.__showHints = () => {
      hintFloat.classList.remove('hidden');
      logFloat.classList.add('hidden');
    };
    /* 单次素材数(2026-08-30):6-12 条,越高结构越复杂;选择持久化在 localStorage */
    const materialSel = $('homeMaterialCount');
    if (materialSel) {
      const savedN = Number(localStorage.getItem('favRoom.materialCount'));
      if (savedN >= 6 && savedN <= 12) materialSel.value = String(savedN);
      materialSel.onchange = () =>
        localStorage.setItem('favRoom.materialCount', materialSel.value);
    }
    $('homeFile').onchange = async () => {
      const file = $('homeFile').files?.[0];
      $('homeGenerate').disabled = true;
      pendingWindows = [];
      selectedWindow = null;
      const panel = $('windowPanel'),
        list = $('windowList');
      panel.style.display = 'none';
      list.innerHTML = '';
      if (!file) {
        setStatus('等待上传收藏夹。', '');
        return;
      }
      setStatus('正在解析 ' + file.name + ' 的时间戳……', 'busy');
      const token = ++importToken;
      try {
        const raw = await file.text();
        if (token !== importToken) return;
        const items = window.__favoriteRoomPipeline.parse(raw, file.name);
        if (token !== importToken) return;
        /* 全局清洗(2026-08-28):导入即清洗全量——本地规则即时标记 + 存量判定合并,
           未标记条目走模型增量清洗(快车道直连);时间片只从通过(keep)条目中选取 */
        setStatus('正在全局清洗（本地规则 + 存量标记合并）……', 'busy');
        const verdictMap = {};
        (await dbAll('verdicts')).forEach((v) => (verdictMap[v.id] = v));
        let cleaned = window.__favoriteRoomPipeline.applyVerdicts(items, verdictMap);
        const fresh = cleaned.records.filter((r) => !r.verdict && !r.safetyFlag);
        /* desc 富化不在导入路径(2026-08-30 需求方工作流):生成时对随机选定的
           素材批回访(见 generate),导入只做清洗,保持导入快速就绪 */
        if (fresh.length) {
          try {
            const merged = await window.__favoriteRoomPipeline.cleanBatch(fresh, '', (m) =>
              setStatus(m, 'busy'),
            );
            const byUrl = {};
            merged.forEach((r) => (byUrl[r.canonicalUrl] = r));
            cleaned = {
              ...cleaned,
              records: cleaned.records.map((r) => byUrl[r.canonicalUrl] || r),
            };
          } catch (ce) {
            setStatus('增量清洗失败（' + (ce.message || ce) + '），先用本地标记继续。', 'error');
          }
        }
        try {
          for (const v of window.__favoriteRoomPipeline.buildVerdicts(cleaned.records))
            await dbPut('verdicts', v);
        } catch (pe) {
          console.warn('标记记录写入失败:', pe && pe.message);
        }
        if (token !== importToken) return;
        lastCleaned = cleaned;
        const approved = cleaned.records.filter((r) => r.status === 'keep');
        pendingWindows = detectTimeWindows(approved);
        if (pendingWindows.length) {
          panel.style.display = '';
          list.innerHTML = pendingWindows
            .map(function (w, i) {
              const mood =
                w.moodPref === '深夜'
                  ? ' restless-night'
                  : w.moodPref === '夜晚'
                    ? ' evening'
                    : ' day';
              return (
                '<button type="button" class="window-card' +
                mood +
                '" data-wi="' +
                i +
                '"><strong>' +
                w.label +
                '</strong><small>' +
                w.count +
                ' 条收藏 · ' +
                w.spanDays +
                ' 天' +
                (w.topFolders.length ? ' · ' + w.topFolders.map(esc).join(' / ') : '') +
                '</small><small>' +
                (w.moodPref === '深夜'
                  ? '深夜收藏占 ' + Math.round(w.nightRatio * 100) + '% —— 那段时间睡得不好'
                  : w.moodPref === '白天'
                    ? '多半在工作时间收下'
                    : '多在夜晚收下') +
                '</small></button>'
              );
            })
            .join('');
          list.querySelectorAll('.window-card').forEach(
            (btn) =>
              (btn.onclick = () => {
                list.querySelectorAll('.window-card').forEach((b) => b.classList.remove('picked'));
                btn.classList.add('picked');
                selectedWindow = pendingWindows[Number(btn.dataset.wi)];
                $('homeGenerate').disabled = false;
                setStatus('已选择「' + selectedWindow.label + '」这一时间片。点击生成。', 'good');
              }),
          );
          setStatus(
            '已标记 ' +
              cleaned.records.length +
              ' 条（通过 ' +
              approved.length +
              '）。发现 ' +
              pendingWindows.length +
              ' 个时间片，选一个做成密室。',
            '',
          );
        } else {
          /* 没有可成窗的时间戳:退回全量模式(仅通过条目) */
          $('homeGenerate').disabled = false;
          setStatus(
            '时间戳不足以切分时间片，将使用全部通过收藏（' + approved.length + ' 条）。',
            '',
          );
        }
      } catch (err) {
        setStatus(err.message || '解析失败', 'error');
      }
    };
    $('homeGenerate').onclick = generate;
    $('gameSave').onclick = () => saveProgress(false);
    $('gameHome').onclick = async () => {
      await saveProgress(true);
      showHome();
    };
    $('homeContinue').onclick = async () => {
      const progress = (await dbAll('progress')).sort((a, b) =>
        String(b.updatedAt).localeCompare(String(a.updatedAt)),
      )[0];
      if (progress) {
        const level = await dbGet('levels', progress.levelId);
        if (level) mountLevel(level, progress.snapshot);
      }
    };
    $('gameExport').onclick = exportCurrentLevel;
    $('homeImport').onclick = () => $('homeImportFile').click();
    $('homeImportFile').onchange = (e) => {
      const f = e.target.files && e.target.files[0];
      if (f) importLevelFile(f);
      e.target.value = '';
    };
    $('homeFixedTest').onclick = loadSamplePuzzle;
    $('homeClearCache').onclick = async () => {
      if (
        !confirm('清空清洗标记与生成缓存？已保存的关卡和进度不受影响，下次导入会重新全局清洗。')
      )
        return;
      try {
        await dbClear('verdicts');
        await dbClear('datasets');
        lastCleaned = null;
        setStatus('清洗标记与生成缓存已清空。', 'good');
      } catch (e) {
        setStatus('清空失败：' + (e && e.message), 'error');
      }
    };
    await refreshSaved();
    $('homeScreen').classList.remove('hidden');
  }

  /* ---------- 关卡导入/导出:让手写谜题脱离书签管线独立加载 ---------- */
  function exportLevelRecord(level, statusFn) {
    const raw = JSON.stringify(level && level.draft ? level.draft : level);
    const blob = new Blob([raw], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = ((level && level.name) || 'level').replace(/[\\/:*?"<>|]/g, '_') + '.room.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    if (statusFn) statusFn('关卡已导出为 JSON 文件。', 'good');
  }
  function exportCurrentLevel() {
    if (!currentLevel) {
      setStatus('当前没有可导出的关卡。先打开一关。', 'error');
      return;
    }
    exportLevelRecord(currentLevel, setStatus);
  }
  async function deleteLevel(id) {
    if (!id) return;
    let name = '该关卡';
    try {
      const level = await dbGet('levels', id);
      if (level) name = level.name || level.draft?.level?.title || name;
    } catch (_) {}
    if (
      typeof confirm === 'function' &&
      !confirm('删除存档「' + name + '」？\n游玩进度也会一并删除，且不可恢复。')
    )
      return;
    /* 连带清除 datasets 缓存(2026-08-29 需求方反馈):删除存档后重新生成,
       不应命中同一 cacheKey 的设计缓存——否则用户看到的是被删存档的相同内容 */
    const deadLevel = await dbGet('levels', id);
    if (deadLevel && deadLevel.cacheKey) await dbDelete('datasets', deadLevel.cacheKey);
    await dbDelete('levels', id);
    await dbDelete('progress', id);
    if (currentLevel && currentLevel.id === id) {
      currentLevel = null;
      localStorage.removeItem('favorite-room-current');
    }
    refreshSaved();
    setStatus('已删除存档「' + name + '」。', 'good');
  }
  /* 导入关卡加固(2026-08-28 审查 11.1.3):导入文件是外部输入,字符串字段
     去除尖括号并限长,阻断经 innerHTML 渲染路径的注入;完整 schema 校验留待后续批次。 */
  function sanitizeImportedDraft(draft) {
    const cap = (v, n) => String(v == null ? '' : v).replace(/[<>]/g, '').slice(0, n);
    const lv = draft && draft.level;
    if (!lv || !Array.isArray(lv.items) || !lv.items.length) return draft;
    lv.title = cap(lv.title, 200);
    lv.premise = cap(lv.premise, 2000);
    lv.objective = cap(lv.objective, 2000);
    lv.items.forEach((it) => {
      it.title = cap(it.title, 200);
      it.sceneName = cap(it.sceneName, 120);
      it.reason = cap(it.reason, 800);
    });
    (lv.beats || []).forEach((b) => {
      b.title = cap(b.title, 200);
      b.product = cap(b.product, 200);
    });
    return draft;
  }
  async function loadLevelText(txt) {
    let draft;
    try {
      draft = JSON.parse(txt);
    } catch (_) {
      throw new Error('不是有效的 JSON 文件');
    }
    if (!draft || !draft.level || !Array.isArray(draft.level.items) || !draft.level.items.length)
      throw new Error('关卡文件缺少 level.items');
    draft = sanitizeImportedDraft(draft);
    if (!Array.isArray(draft.level.beats) || !draft.level.beats.length)
      throw new Error('关卡文件缺少 level.beats');
    if (!Array.isArray(draft.items))
      draft.items = (draft.level.items || []).map(function (it) {
        return {
          id: it.id,
          title: it.title || it.sceneName || '',
          domain: '',
          dateAdded: '',
          url: '',
          urlPath: '',
        };
      });
    const record = {
      id: 'import-' + Date.now().toString(36),
      projectId: 'import',
      cacheKey: 'import',
      name: draft.level.title || '导入关卡',
      theme: draft.level.theme || '',
      draft: draft,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    /* 审查 11.2.6:导入关卡写入 levels,刷新后可从列表/继续游戏恢复 */
    try {
      await dbPut('levels', record);
      refreshSaved();
    } catch (pe) {
      console.warn('导入关卡存档失败:', pe && pe.message);
    }
    mountLevel(record);
    setStatus('已载入关卡「' + record.name + '」。', 'good');
  }
  function importLevelFile(file) {
    if (!file) {
      setStatus('没有选择文件。', 'error');
      return;
    }
    file
      .text()
      .then(loadLevelText)
      .catch(function (err) {
        setStatus(err.message || '导入失败', 'error');
      });
  }
  function loadSamplePuzzle() {
    setStatus('正在载入手写谜题样本……', 'busy');
    fetch('sample-puzzles/watchman.json', { cache: 'no-store' })
      .then(function (r) {
        if (!r.ok) throw new Error('样本文件加载失败 HTTP ' + r.status);
        return r.text();
      })
      .then(loadLevelText)
      .catch(function (err) {
        setStatus(err.message || '样本加载失败', 'error');
      });
  }
  window.__favoriteRoomHome = {
    showHome,
    showGame,
    saveProgress,
    refreshSaved,
    exportCurrentLevel,
    exportLevelRecord,
    deleteLevel,
    importLevelFile,
    loadSamplePuzzle,
    openNamingFlow,
    resetCurrentLevel,
  };
  /* ===== 未命名冒险:延迟命名(2026-08-29 产品方向,阶段1+2 MVP) ===== */
  let namingWatchTimer = null,
    namingShownFor = null;
  function stopNamingWatch() {
    if (namingWatchTimer) {
      clearInterval(namingWatchTimer);
      namingWatchTimer = null;
    }
  }
  function startNamingWatch(levelId) {
    stopNamingWatch();
    namingWatchTimer = setInterval(function () {
      if (namingShownFor === levelId) return;
      const tb = document.getElementById('gameToolbar');
      if (!tb || tb.hasAttribute('hidden')) return;
      const snap = window.__favoriteRoomRuntime && window.__favoriteRoomRuntime.snapshot();
      if (!snap || !snap.done) return;
      namingShownFor = levelId;
      stopNamingWatch();
      openNamingFlow(levelId);
    }, 1500);
  }
  async function openNamingFlow(levelId) {
    const modal = $('namingModal');
    if (!modal || !currentLevel) return;
    $('endingModal').classList.add('hidden');
    modal.classList.remove('hidden');
    $('adventureNameInput').value = '';
    $('adventureReceipt').style.display = 'none';
    $('adventureReceipt').innerHTML = '';
    $('adventureNameDone').style.display = 'none';
    const saveBtn = $('adventureNameSave');
    saveBtn.disabled = false;
    saveBtn.style.display = '';
    saveBtn.onclick = function () {
      saveAdventureName(levelId);
    };
    $('adventureNameDone').onclick = async function () {
      $('namingModal').classList.add('hidden');
      await saveProgress(true);
      showHome();
    };
    renderNameCandidates(currentLevel);
  }
  async function renderNameCandidates(record) {
    const box = $('nameCandidates');
    box.innerHTML = '<small class="muted-note">正在构思候选标题……</small>';
    const facts = ((record.draft && record.draft.items) || [])
      .slice(0, 6)
      .map(function (it) {
        return (
          '「' + (it.title || '') + '」(' + (it.domain || '') + ',' +
          String(it.dateAdded || '').slice(0, 10) + ')'
        );
      });
    const avatars = ((record.draft && record.draft.level) ? record.draft.level.items : []).map(
      function (it) {
        return it.sceneName || it.title || '';
      },
    );
    const glm = window.__GLM_LANE__;
    let titles = [];
    if (glm && glm.endpoint) {
      try {
        const body = {
          model: glm.model,
          messages: [
            {
              role: 'system',
              content:
                '你是冒险命名器。基于事实清单与化身列表,给出 3 个差异化的候选标题:第一个直白、第二个隐喻、第三个意识流。只依据给定事实,不虚构页面内容。输出严格 JSON {"titles":["","",""]}。',
            },
            {
              role: 'user',
              content:
                '事实清单:' +
                facts.join(';') +
                '\n化身:' +
                avatars.join('、') +
                '\n内在主题(一种理解):' +
                ((record.draft && record.draft.level && record.draft.level.theme) || ''),
            },
          ],
          temperature: 0.9,
          thinking: glm.thinking || { type: 'enabled' },
          stream: false,
        };
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 60000);
        const res = await fetch(glm.endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer ' + glm.apiKey,
          },
          body: JSON.stringify(body),
          signal: controller.signal,
        });
        clearTimeout(timer);
        const d = await res.json();
        const c = (d.choices || [{}])[0].message.content;
        const m = c.match(/\{[\s\S]*\}/);
        titles = (m && JSON.parse(m[0]).titles) || [];
      } catch (e) {
        titles = [];
      }
    }
    box.innerHTML = '';
    if (!titles.length) {
      box.innerHTML = '<small class="muted-note">候选标题不可用，请手动命名。</small>';
      return;
    }
    titles.forEach(function (t) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'window-card';
      btn.textContent = t;
      btn.onclick = function () {
        $('adventureNameInput').value = t;
      };
      box.appendChild(btn);
    });
  }
  async function saveAdventureName(levelId) {
    const name = ($('adventureNameInput')?.value || '').trim();
    if (!name) {
      setStatus('先起一个名字，或点一个候选标题。', 'error');
      return;
    }
    const record = await dbGet('levels', levelId);
    if (!record) return;
    record.name = name;
    record.namedAt = new Date().toISOString();
    try {
      await dbPut('levels', record);
      await refreshSaved();
    } catch (e) {
      setStatus('命名保存失败:' + (e.message || e), 'error');
      return;
    }
    if (currentLevel && currentLevel.id === levelId) {
      currentLevel.name = name;
      currentLevel.namedAt = record.namedAt;
      const gt = $('gameTitle');
      if (gt) gt.textContent = name;
    }
    const lv = record.draft && record.draft.level;
    /* 机关/信息分工(2026-08-30):回执只把**收藏化身**映射回真实收藏;
       prop-* 机关道具没有网页背景,单列一行,不伪造「← 未知收藏」 */
    const lvlItems = (lv && lv.items) || [];
    const propNames = lvlItems
      .filter((av) => av.prop)
      .map((av) => av.sceneName || av.title || '')
      .filter(Boolean);
    const rows = lvlItems
      .filter((av) => !av.prop)
      .map(function (av) {
      const src = ((record.draft && record.draft.items) || []).find(function (x) {
        return x.id === av.id;
      }) || {};
      return (
        '<div class="receipt-row"><b>' + esc(av.sceneName || av.title || '?') + '</b> ← ' +
        esc(src.title || '未知收藏') + ' <small>(' + esc(src.domain || '') + ' · ' +
        String(src.dateAdded || '').slice(0, 10) + ')</small><br><small>谜面:' +
        esc((av.reason || '').slice(0, 90)) + '</small></div>'
      );
    });
    const rec = $('adventureReceipt');
    const theme = (lv && lv.theme) || '';
    const grammar = (lv && lv.adventureGrammar) || '';
    const locks = ((lv && lv.beats) || []).filter((b) => b.deriveFrom && b.deriveFrom.length);
    const lockRows = locks
      .map(function (b) {
        const names = (b.deriveFrom || []).map(function (id) {
          const src = ((record.draft && record.draft.items) || []).find(function (x) {
            return x.id === id;
          });
          return esc((src && src.title) || id);
        });
        return (
          '<div class="receipt-row"><b>' + esc(b.title || b.action) + '</b> 的推导来自:' +
          names.join('、') + '</div>'
        );
      })
      .join('');
    rec.style.display = '';
    rec.innerHTML =
      '<div class="kicker">冒险回执 · 一种事后理解</div>' +
      rows.join('') +
      (propNames.length
        ? '<p style="margin:10px 0 0"><small>机关道具(无收藏背景的纯机构):' +
          esc(propNames.join('、')) +
          '</small></p>'
        : '') +
      (grammar
        ? '<p style="margin:10px 0 0"><small>冒险语法(事后解释):' + esc(grammar) + '</small></p>'
        : '') +
      (lockRows ? '<div style="margin-top:8px">' + lockRows + '</div>' : '') +
      (theme
        ? '<p style="margin:10px 0 0"><small>这场冒险的内在主题(候选理解,不是标准答案):' +
          esc(theme) +
          '</small></p>'
        : '');
    $('adventureNameSave').style.display = 'none';
    const doneBtn = $('adventureNameDone');
    doneBtn.style.display = '';
    doneBtn.onclick = async function () {
      $('namingModal').classList.add('hidden');
      await saveProgress(true);
      showHome();
    };
  }
  /* 备用设计供应商(glm)配置:由本地服务端下发,key 不入库 */
  fetch('/api/llm-config')
    .then((r) => (r.ok ? r.json() : {}))
    .then((cfg) => {
      if (cfg && cfg.endpoint) window.__GLM_LANE__ = cfg;
    })
    .catch(function () {});
  openDb()
    .then(boot)
    .catch((err) => {
      addUi();
      hideLegacy();
      $('homeStatus')?.replaceChildren(document.createTextNode(err.message));
    });
})();
