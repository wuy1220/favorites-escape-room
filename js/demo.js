/* 演示模式(?demo=1):黑客松录屏用的编舞引擎。
   生产 UI 全部真实;只有两样东西是假的——网络调用(预置数据)与节奏(编舞)。
   开场披露卡诚实说明这一点;模拟段落字幕带「预置回放」角标。
   本文件不改动任何生产逻辑:只 patch window.fetch、patch 管线的 compile 一步
   (回放预置关卡)、追加演示专用 DOM、使用既有的公开钩子
   (__favoriteRoomHome / __favoritesRoomSeed / __wbGame.__debug)。 */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  if (qs.get('demo') === null) return; /* 非演示模式:零开销退出 */
  const DEMO_SEED = 20260831;
  const FIXTURE_URL = 'fixtures/demo-collection.html';
  const PRESET_LEVEL_URL = 'sample-puzzles/demo-gamenight.room.json';
  const NAME_TEXT = '深秋游戏之夜 · 末班点播台';

  /* ---------------- 工具 ---------------- */
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const $ = (id) => document.getElementById(id);
  const esc = (s) =>
    String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  function waitFor(fn, timeout, every) {
    return new Promise((resolve, reject) => {
      const t0 = Date.now();
      const tick = () => {
        let v;
        try {
          v = fn();
        } catch (_) {}
        if (v) return resolve(v);
        if (Date.now() - t0 > (timeout || 20000))
          return reject(new Error('演示等待超时:' + (fn.name || '条件')));
        setTimeout(tick, every || 120);
      };
      tick();
    });
  }
  function jsonResp(obj) {
    return Promise.resolve(
      new Response(JSON.stringify(obj), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
  }

  /* ---------------- 字幕层(双轨 + 角标 + 浮签) ---------------- */
  let captionRoot = null;
  function ensureOverlay() {
    if (captionRoot) return;
    captionRoot = document.createElement('div');
    captionRoot.id = 'demoLayer';
    captionRoot.innerHTML =
      '<div id="demoBadge">演示预演 · 离线</div>' +
      '<button id="demoStart" type="button">开始演示</button>' +
      '<div id="demoCursor"></div>' +
      '<div id="demoChapterCard" class="demo-hidden"><h3></h3><p></p></div>' +
      '<div id="demoTag" class="demo-hidden"></div>' +
      '<div id="demoCaption" class="demo-hidden"><span id="demoCaptionText"></span><em id="demoCaptionTag" class="demo-hidden">预置回放</em></div>';
    document.body.appendChild(captionRoot);
    const st = document.createElement('style');
    st.textContent = [
      '#demoLayer{position:fixed;inset:0;z-index:900;pointer-events:none;font-family:inherit}',
      '#demoBadge{position:absolute;top:10px;right:12px;padding:4px 10px;border:1px solid rgba(178,58,44,.55);border-radius:3px;background:rgba(247,241,227,.92);color:#b23a2c;font-size:11px;letter-spacing:.12em}',
      '#demoCursor{position:absolute;left:0;top:0;width:22px;height:22px;margin:-11px 0 0 -11px;border-radius:50%;background:radial-gradient(circle,rgba(255,214,140,.95),rgba(178,58,44,.7) 60%,transparent 72%);box-shadow:0 0 12px rgba(255,214,140,.8);transition:transform .55s cubic-bezier(.22,.61,.36,1);opacity:0}',
      '#demoChapterCard{position:absolute;left:50%;top:38%;transform:translate(-50%,-50%);max-width:560px;padding:22px 30px;background:#f7f1e3;border:1px solid rgba(44,36,22,.4);border-radius:4px;box-shadow:0 14px 44px rgba(0,0,0,.45);text-align:center;transition:opacity .4s}',
      '#demoChapterCard h3{margin:0 0 8px;font-size:22px;color:#2c2a26}',
      '#demoChapterCard p{margin:0;font-size:13px;line-height:1.8;color:#5c5342}',
      '#demoStart{pointer-events:auto;position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);padding:14px 30px;border:1px solid #b23a2c;border-radius:3px;background:#f7f1e3;color:#b23a2c;font:600 16px inherit;cursor:pointer;box-shadow:0 8px 24px rgba(0,0,0,.28)}',
      '.demo-hidden{opacity:0 !important;visibility:hidden}',
      '#demoCaption{position:absolute;left:50%;bottom:26px;transform:translateX(-50%);max-width:72%;padding:10px 18px;background:rgba(247,241,227,.95);border:1px solid rgba(44,36,22,.35);border-radius:3px;box-shadow:0 6px 20px rgba(0,0,0,.35);transition:opacity .35s}',
      '#demoCaptionText{font-size:14px;line-height:1.7;color:#2c2a26}',
      '#demoCaptionTag{display:inline-block;margin-left:10px;padding:1px 8px;font-size:10px;font-style:normal;color:#b23a2c;border:1px solid rgba(178,58,44,.5);border-radius:3px;vertical-align:1px}',
      '#demoTag{position:absolute;padding:3px 10px;background:#b23a2c;color:#f7f1e3;font-size:11px;border-radius:3px;box-shadow:0 4px 14px rgba(0,0,0,.4);transition:opacity .4s}',
    ].join('\n');
    document.head.appendChild(st);
  }
  function caption(text, simulated) {
    const bar = $('demoCaption'),
      tag = $('demoCaptionTag');
    if (!bar) return;
    $('demoCaptionText').textContent = text;
    tag.classList.toggle('demo-hidden', !simulated);
    bar.classList.remove('demo-hidden');
  }
  function chapter(title, sub, hold) {
    const card = $('demoChapterCard');
    card.querySelector('h3').textContent = title;
    card.querySelector('p').textContent = sub || '';
    card.classList.remove('demo-hidden');
    return sleep(hold == null ? 2600 : hold).then(() => card.classList.add('demo-hidden'));
  }
  function floatTag(sel, text, hold) {
    const el = document.querySelector(sel);
    const tag = $('demoTag');
    if (!el || !tag) return sleep(0);
    const r = el.getBoundingClientRect();
    tag.textContent = text;
    tag.style.left = Math.max(8, r.right + 10) + 'px';
    tag.style.top = Math.max(8, r.top - 4) + 'px';
    tag.classList.remove('demo-hidden');
    return sleep(hold == null ? 2800 : hold).then(() => tag.classList.add('demo-hidden'));
  }

  /* ---------------- 虚拟光标 ---------------- */
  async function cursorGlide(x, y) {
    const cur = $('demoCursor');
    cur.style.opacity = '1';
    cur.style.transform = 'translate(' + x + 'px,' + y + 'px)';
    await sleep(560);
  }
  function fireMouse(el, type, x, y) {
    el.dispatchEvent(
      new MouseEvent(type, { bubbles: true, cancelable: true, view: window, clientX: x, clientY: y, button: 0 }),
    );
  }
  function firePointer(el, type, x, y) {
    /* room02 的拖拽走 pointer 事件(onpointerdown + 窗口 pointermove/pointerup) */
    el.dispatchEvent(
      new PointerEvent(type, {
        bubbles: true,
        cancelable: true,
        view: window,
        clientX: x,
        clientY: y,
        button: 0,
        pointerId: 1,
        pointerType: 'mouse',
        isPrimary: true,
      }),
    );
  }
  async function cursorClick(sel) {
    const el = await waitFor(() => {
      const e = document.querySelector(sel);
      return e && e.offsetParent !== null ? e : null;
    }, 15000);
    const r = el.getBoundingClientRect();
    const x = r.x + r.width / 2,
      y = r.y + r.height / 2;
    await cursorGlide(x, y);
    const t = document.elementFromPoint(x, y) || el;
    firePointer(t, 'pointerdown', x, y);
    fireMouse(t, 'mousedown', x, y);
    firePointer(t, 'pointerup', x, y);
    fireMouse(t, 'mouseup', x, y);
    fireMouse(t, 'click', x, y);
    await sleep(420);
    return el;
  }
  async function cursorDrag(srcSel, dstSel) {
    const s = document.querySelector(srcSel),
      d = document.querySelector(dstSel);
    if (!s || !d) throw new Error('拖拽目标缺失:' + srcSel + '→' + dstSel);
    const sr = s.getBoundingClientRect(),
      dr = d.getBoundingClientRect();
    const sx = sr.x + sr.width / 2,
      sy = sr.y + sr.height / 2,
      dx = dr.x + dr.width / 2,
      dy = dr.y + dr.height / 2;
    await cursorGlide(sx, sy);
    let t = document.elementFromPoint(sx, sy) || s;
    firePointer(t, 'pointerdown', sx, sy);
    fireMouse(t, 'mousedown', sx, sy);
    for (let i = 1; i <= 8; i++) {
      const x = sx + ((dx - sx) * i) / 8,
        y = sy + ((dy - sy) * i) / 8;
      firePointer(window, 'pointermove', x, y);
      fireMouse(document, 'mousemove', x, y);
      await sleep(55);
    }
    firePointer(window, 'pointerup', dx, dy);
    fireMouse(window, 'mouseup', dx, dy);
    await sleep(520);
  }

  /* ---------------- fetch 拦截(预置数据) ---------------- */
  let fixtureText = '';
  let metaMap = {}; /* url -> {title, desc} */
  const realFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    const method = ((init && init.method) || 'GET').toUpperCase();
    if (method === 'POST') {
      const body = (init && init.body ? String(init.body) : '') || '';
      if (url.indexOf('/fetch-meta') >= 0) {
        try {
          const req = JSON.parse(body);
          const results = {};
          (req.urls || []).forEach((u) => {
            const m = metaMap[u];
            if (m) results[u] = { status: 200, title: m.title, desc: m.desc };
          });
          return jsonResp({ results: results });
        } catch (_) {
          return jsonResp({ results: {} });
        }
      }
      if (body.indexOf('"messages"') >= 0) {
        if (body.indexOf('整理器') >= 0) return handleClean(body);
        if (body.indexOf('冒险命名器') >= 0)
          return sleep(1800).then(() =>
            jsonResp({
              choices: [
                {
                  message: {
                    content: JSON.stringify({
                      titles: [
                        '末班点播台',
                        '深秋游戏之夜 · 手动播出的压轴',
                        '台长藏在底座里的那张碟',
                      ],
                    }),
                  },
                },
              ],
            }),
          );
        if (body.indexOf('关卡设计师') >= 0) return handleDesign(body, url);
      }
    }
    if (url.indexOf('/api/llm-config') >= 0)
      return jsonResp({
        endpoint: location.origin + '/demo-glm-lane',
        model: 'demo-glm',
        apiKey: 'demo',
        thinking: { type: 'disabled' },
        reasoningEffort: 'low',
        designTimeout: 600000,
        label: 'glm',
      });
    return realFetch(input, init);
  };
  function parseChatBody(body) {
    /* messages[1].content = JSON(userReq) + '\n\n【参考关卡A...' ——取第一段 JSON */
    try {
      const c = JSON.parse(body).messages[1].content;
      const cut = c.indexOf('\n\n【');
      return JSON.parse(cut >= 0 ? c.slice(0, cut) : c);
    } catch (_) {
      return null;
    }
  }
  async function handleClean(body) {
    const req = parseChatBody(body);
    const items = (req && req.items) || [];
    const out = items.map(function (it, i) {
      return {
        id: it.id,
        status: 'keep',
        topics: ['示例收藏'],
        reason: ['信息量充足', '来源可查', '内容完整', '主题清晰'][i % 4],
        intent: '',
      };
    });
    await sleep(4200); /* 清洗节奏:每批 ~4.5s,两批约 9s */
    return jsonResp({ choices: [{ message: { content: JSON.stringify({ items: out }) } }] });
  }
  let designServed = 0;
  async function handleDesign(body, url) {
    const materials = (parseChatBody(body) || {}).materials || [];
    const delay = url.indexOf('demo-glm-lane') >= 0 ? 13500 : 17000;
    await sleep(delay);
    designServed++;
    /* 演示回放的关卡必须用「真实素材 id + scenes 多房间结构」作答:
       sample-puzzles/*.room.json 是编译后的平铺格式(无 scenes),管线会整版打回,
       导致两路 × 3 轮 × 2 次整体重试,演示永久停在「设计进行中」。
       所以这里用 fillDesign 按请求里的真实素材现场生成 scenes 结构。 */
    return jsonResp({
      choices: [{ message: { content: JSON.stringify(fillDesign(materials)) } }],
    });
  }

  /* ---------------- 预置关卡回放 ----------------
     演示最终挂载的必须是 sample-puzzles/demo-gamenight.room.json 本体。
     它是人工 authored 的已验收关卡(records 为空,ra-* 是虚构 id、不对应任何
     真实收藏),设计管线不可能从演示素材生成它——2026-08-31 的踩坑正是把这份
     编译产物当 LLM 设计结果返回,被校验器以「必须输出 scenes 多房间结构」整版
     打回,两路 × 3 轮 × 2 次整体重试,演示永久停在「设计进行中」。
     正确分工:设计赛马照常演出(桩返回合法 scenes 设计,通过校验与求解验证),
     编译环节把结果换成预置关卡的完整 draft。引擎、存档、命名、回执全部真实。 */
  let presetDraft = null;
  let presetLoading = null;
  function loadPresetDraft() {
    if (!presetLoading)
      presetLoading = (async function () {
        try {
          const res = await realFetch(PRESET_LEVEL_URL, { cache: 'no-store' });
          const json = await res.json();
          if (json && json.level) {
            /* 与导入关卡路径(loadLevelText)同构:补齐顶层 items,缺了引擎读不到来源 */
            const level = {
              ...json.level,
              /* 显式写 theme,否则 app.js 会拿占位设计的 theme 顶上,回执里串味 */
              theme: json.level.theme || '深夜点播台——断了电的台里,压轴要由你手动播出',
            };
            presetDraft = {
              ...json,
              level,
              items:
                json.items ||
                (json.level.items || []).map((it) => ({
                  id: it.id,
                  title: it.title || it.sceneName || '',
                  domain: '',
                  dateAdded: '',
                  url: '',
                  urlPath: '',
                })),
            };
          }
        } catch (_) {}
        return presetDraft;
      })();
    return presetLoading;
  }
  function patchCompile() {
    const P = window.__favoriteRoomPipeline;
    if (!P || !P.compile || P.__demoPatched) return;
    const real = P.compile;
    /* 关键:app.js 的赛马是**同步**调用 compile 的(app.js:1257 没有 await)。
       补丁若写成 async,laneDraft 会拿到 Promise,随后 solveLevel(laneDraft.level)
       读到 undefined,报「beats 不足 3 步」——所以这里必须同步返回。 */
    P.compile = function (cleaned, modelResult, levelResult, theme) {
      return presetDraft || real(cleaned, modelResult, levelResult, theme);
    };
    P.__demoPatched = true;
  }

  /* ---------------- 设计模板:让赛马「通过」用的合法占位设计 ----------------
     它只负责走完校验与求解验证,挂载的关卡不是它(见上方「预置关卡回放」)。
     以请求里的真实素材(标题/描述)填充骨架——谜面引用真实标题,
     机制与答案由模板预定。 */
  function fillDesign(materials) {
    const M = materials.slice(0, 6);
    while (M.length < 6) M.push({ id: 'demo-fill-' + M.length, title: '备用素材' + M.length });
    const T = M.map((m) => String(m.title || m.id).replace(/[「」『』"]/g, '').trim().slice(0, 24));
    const id = (i) => String(M[i - 1].id);
    /* sourceFacts 留空:校验器要求其值能在素材原文里逐字找到,演示桩不冒改写风险 */
    const sf = () => [];
    const dg = (i) => '示例网页「' + T[i - 1] + '」的收藏条目。';
    return {
      title: '深夜档案库 · 守库人手记',
      theme: '深夜档案库——台灯、铁皮柜与一册待完成的手记',
      adventureGrammar: '变形:卡片对上报表,报表写进手记,最终拼出完整的守库人手记',
      creativeThesis: '每一条随手收下的网页,都是守库人没写完的一页手记。',
      recurringMotif: '纸与孔位',
      surpriseTurn: '无',
      premise: '你在深夜的档案库里醒来,台灯还亮着。守库人的手记缺了最后一页——材料就散落在两间屋子里。',
      objective: '拼合档案页,补全守库人手记,在结束处完成今晚的归档。',
      targetMinutes: 10,
      mechanics: ['inspect', 'combine', 'password', 'deliver'],
      hints: [
        '先看看台签卡片和打孔报表各写了什么。',
        '铁皮柜的锁,也许台签能对上。',
        '报表的孔位连成了三个数字。',
        '闸机要三位密码——报表就是答案。',
        '拼好的档案页,要和那册手记合在一起。',
        '全都拼齐后,回到「结束」完成归档。',
      ],
      scenes: [
        {
          id: 'room-1',
          title: '档案外间',
          description: '台灯的光圈里摊着几张卡片,墙角的铁皮柜锁着什么。',
          focus: '上锁的铁皮柜',
          items: [
            { id: id(1), role: 'clue', scene_name: '台签卡片', reason: '台签卡片印着「' + T[0] + '」,背面画着一个柜子的简图。', digest: dg(1), sourceFacts: sf(1) },
            { id: id(2), role: 'tool', scene_name: '铜钥匙', reason: '柜门内侧挂着的铜钥匙,齿痕崭新。', hidden: true, digest: dg(2), sourceFacts: sf(2) },
            { id: id(3), role: 'red_herring', scene_name: '旧海报', reason: '褪色的旧海报,边角翘起,和锁没有关系。', digest: dg(3), sourceFacts: sf(3) },
            { id: 'prop-1', role: 'tool', scene_name: '铁皮柜', reason: '铁皮柜挂着小锁,缝隙里透出金属光。' },
          ],
          beats: [
            { id: 'b1', title: '读台签卡片', action: 'inspect', uses: [id(1)] },
            { id: 'b2', title: '打开铁皮柜', action: 'combine', uses: [id(1), 'prop-1'], requires: ['b1'], resultOn: 'prop-1', product: '打开的铁皮柜', reveals: [id(2)] },
            { id: 'b3', title: '取下铜钥匙', action: 'inspect', uses: [id(2)], requires: ['b2'] },
          ],
        },
        {
          id: 'room-2',
          title: '机房里间',
          description: '里间的密码闸机嗡嗡待机,桌面上摊着一张打孔报表。',
          focus: '三位密码闸机',
          items: [
            { id: id(4), role: 'clue', scene_name: '打孔报表', reason: '报表摊在闸机旁,孔位连成 3、1、4——纸角还标着「' + T[3] + '」的缩写。', digest: dg(4), sourceFacts: sf(4) },
            { id: id(5), role: 'lock', scene_name: '密码闸机', reason: '三位密码闸机,盘面刻着:密码打在报表的孔位里。', digest: dg(5), sourceFacts: sf(5) },
            { id: id(6), role: 'reward', scene_name: '守库人手记', reason: '半成品手记,最后一页是空的——等一份拼好的档案。', hidden: true, digest: dg(6), sourceFacts: sf(6) },
            { id: 'prop-2', role: 'tool', scene_name: '掉漆台座', reason: '掉漆的台座,曾经固定过什么东西。' },
          ],
          beats: [
            { id: 'b4', title: '读打孔报表', action: 'inspect', uses: [id(4)] },
            { id: 'b5', title: '输入闸机密码', action: 'password', uses: [id(5)], expected: '314', deriveFrom: [id(4)], requires: ['b1', 'b4'], reveals: [id(6)], product: '解锁的闸机' },
            { id: 'b6', title: '拼合档案页', action: 'combine', uses: ['result:b2', id(4)], requires: ['b2', 'b3', 'b5'], resultOn: id(4), product: '拼好的档案页' },
            { id: 'b7', title: '补全守库人手记', action: 'combine', uses: ['result:b6', id(6)], requires: ['b6'], resultOn: id(6), product: '完整的守库人手记' },
            /* requires 跨房间:终局交付的依赖闭包必须横跨 ≥2 个房间,否则校验器打回 */
            { id: 'b8', title: '完成今晚的归档', action: 'deliver', uses: ['result:b7'], requires: ['b7', 'b1'] },
          ],
        },
      ],
    };
  }

  /* ---------------- 清空存档(一次性,带重载) ---------------- */
  function prepareStorage() {
    if (sessionStorage.getItem('demoPrep') === '1') return Promise.resolve();
    sessionStorage.setItem('demoPrep', '1');
    return new Promise((resolve) => {
      const req = indexedDB.deleteDatabase('favorites-escape-room-local');
      req.onsuccess = req.onerror = req.onblocked = () => resolve();
      setTimeout(resolve, 1200);
    }).then(() => location.reload());
  }

  /* ---------------- 主编舞 ---------------- */
  async function run() {
    ensureOverlay();
    await chapter(
      '收藏夹密室 · 演示',
      '本视频为离线预演:模型调用以预置结果替代,生成节奏经压缩编排,\n挂载的关卡是仓库内已验收的示例关(预置回放);\n其余部分——导入、解析、时间片、解谜引擎、存档恢复、命名——均为真实运行。',
      4200,
    );
    /* ① 导入 */
    caption('第一步 · 导入示例收藏夹——一切从真实收藏的网页开始', false);
    await cursorGlide(window.innerWidth * 0.24, window.innerHeight * 0.24);
    const res = await realFetch(FIXTURE_URL, { cache: 'no-store' });
    fixtureText = await res.text();
    try {
      const doc = new DOMParser().parseFromString(fixtureText, 'text/html');
      metaMap = {};
      doc.querySelectorAll('a[href]').forEach((a) => {
        const u = a.getAttribute('href');
        if (u && /^https?:/.test(u))
          metaMap[u] = { title: (a.textContent || '').trim().slice(0, 60), desc: (a.textContent || '').trim() + '。示例收藏条目。' };
      });
    } catch (_) {}
    const dt = new DataTransfer();
    dt.items.add(new File([fixtureText], 'demo-collection.html', { type: 'text/html' }));
    const input = await waitFor(() => $('homeFile'), 15000, 120);
    input.files = dt.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
    /* ② 清洗(真实流程 + 预置判定) */
    caption('清洗:50 条收藏先过安全与价值清洗——只有通过的才有资格进密室', true);
    await waitFor(() => document.querySelector('.window-card'), 40000, 300);
    caption('清洗完成——每一条判定都有理由,通过者进入时间片', true);
    await floatTag('.window-card', '时间片 · 按收藏日期切分', 2600);
    /* ③ 点选时间片(多选) */
    caption('点选时间片——「那段时间的你」决定这间密室的样子', false);
    const cards = Array.from(document.querySelectorAll('.window-card'));
    for (const c of cards) {
      const r = c.getBoundingClientRect();
      await cursorGlide(r.x + r.width / 2, r.y + r.height / 2);
      c.click();
      await sleep(500);
    }
    const sel = $('homeMaterialCount');
    if (sel) sel.value = '6';
    /* ④ 生成:赛马(预置回放) */
    caption('生成 · 双模型并行赛马——先通过验证的方案胜出(本段为预置回放)', true);
    await cursorClick('#homeGenerate');
    await waitFor(() => $('genWorkbench') && !$('genWorkbench').hasAttribute('hidden'), 8000);
    /* 小游戏:等待期间工房里还有小游戏 */
    await sleep(2600);
    caption('等待生成期间,工房里还有小游戏可玩', false);
    const toggle = $('wbGameToggle');
    if (toggle) {
      await cursorClick('#wbGameToggle');
      miniGameAutopilot(Date.now() + 7600);
      await sleep(7800);
      caption('先通过验证的方案胜出——关卡挂载中', true);
    }
    await waitFor(
      () => ($('gameToolbar') && !$('gameToolbar').hasAttribute('hidden') ? true : null),
      45000,
    );
    await sleep(1200);
    /* 挂载完成:字幕转为跟随游戏日志的实时解说,操作交给玩家 */
    caption('现在交给你：点击根节点进入房间，依次检查物件；按线索组合/输入机关，最后点击「结束」。每次日志更新都会自动解说。', false);
    startLogMirror();
  }

  /* ---------------- 小游戏自动驾驶 ---------------- */
  function miniGameAutopilot(stopAt) {
    const iv = setInterval(function () {
      if (Date.now() > stopAt) {
        clearInterval(iv);
        return;
      }
      const g = window.__wbGame;
      if (!g || !g.__debug) return;
      const st = g.__debug.state();
      if (st.gameOver) {
        g.__debug.restart();
        return;
      }
      const near = (st.obsX || []).find((x) => x > 30 && x < 118);
      if (near !== undefined && st.runnerY > -26)
        window.dispatchEvent(new KeyboardEvent('keydown', { code: 'Space', key: ' ', bubbles: true }));
    }, 60);
    return iv;
  }

  /* ---------------- 日志镜像:玩家操作的实时解说 ---------------- */
  function startLogMirror() {
    const pick = () => {
      const t = document.getElementById('logLatest') || document.querySelector('.log-ticker');
      if (t) return (t.textContent || '').replace(/\s+/g, ' ').trim();
      const log = document.getElementById('log');
      if (log) {
        const kids = log.children;
        return kids.length ? (kids[kids.length - 1].textContent || '').replace(/\s+/g, ' ').trim() : '';
      }
      return '';
    };
    let last = '';
    const grab = () => {
      const t = pick().replace(/^记录\s*/, '');
      if (t && t !== last) {
        last = t;
        caption(t.slice(-90), false);
      }
    };
    const el = document.getElementById('log') || document.querySelector('.log-ticker, #logLatest, #logFloat');
    if (!el) return;
    new MutationObserver(grab).observe(el, { childList: true, subtree: true, characterData: true });
    /* Keep the handoff instruction visible until the player makes the first
       action; the initial log entry is not a player action and should not
       overwrite the instructions. */
  }

  let started = false;
  function startDemo() {
    if (started) return;
    started = true;
    const btn = $('demoStart');
    if (btn) btn.remove();
    run().catch(function (err) {
      console.error('[demo]', err);
      caption('演示中断:' + (err && err.message ? err.message : err), false);
    });
  }

  /* ---------------- 启动 ---------------- */
  prepareStorage().then(async function () {
    ensureOverlay();
    window.__favoritesRoomSeed = DEMO_SEED;
    patchCompile(); /* 必须在点「生成」之前换好编译结果 */
    await loadPresetDraft(); /* 预取预置关卡,让 compile 能同步返回 */
    /* A previous normal session may leave the app showing a mounted level.
       Demo playback must always begin from its title screen without deleting
       the user's saved levels or progress. */
    await waitFor(() => window.__favoriteRoomHome && $('homeScreen'), 15000, 120);
    window.__favoriteRoomHome.showHome();
    const btn = await waitFor(() => $('demoStart'), 15000, 120);
    btn.addEventListener('click', startDemo, { once: true });
  });
})();
