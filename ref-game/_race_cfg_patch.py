# -*- coding: utf-8 -*-
"""赛马配置化:供应商与路数可自定义(1-5 路),管线/工作台去 step+glm 耦合。"""
import io

s = io.open('js/app.js', encoding='utf-8').read()

# ===== 1) 配置层 + 弹窗逻辑:插在 generate() 之前 =====
anchor = '  async function generate() {'
cfg_layer = '''  /* ===== 赛马配置(2026-08-30):供应商与路数可自定义,管线不再耦合 step/glm =====
     localStorage fav-room-race-v1 = {lanes:1-5, providers:[{label,endpoint,model,apiKey,reasoningEffort}]}。
     端点留空的行 = 默认供应商(本地代理 / 清洗配置);各路按顺序循环取供应商。
     未自定义时走自动模式:有 glm 配置双路并行,否则单路 step。 */
  const RACE_CFG_KEY = 'fav-room-race-v1';
  const DRAFT_NAMES = ['甲', '乙', '丙', '丁', '戊'];
  function readRaceConfig() {
    try {
      const raw = JSON.parse(localStorage.getItem(RACE_CFG_KEY) || 'null');
      if (!raw) return null;
      const lanes = Math.max(1, Math.min(5, Number(raw.lanes) || 1));
      const providers = (Array.isArray(raw.providers) ? raw.providers : [])
        .slice(0, 5)
        .map(function (p, i) {
          return {
            label: String((p && p.label) || '').trim() || '供应商' + (i + 1),
            endpoint: String((p && p.endpoint) || '').trim(),
            model: String((p && p.model) || '').trim(),
            apiKey: String((p && p.apiKey) || '').trim(),
            reasoningEffort: String((p && p.reasoningEffort) || '').trim(),
          };
        })
        .filter((p) => p.endpoint || p.model || p.apiKey);
      if (!providers.length) return null;
      return { lanes, providers };
    } catch (_) {
      return null;
    }
  }
  function buildLaneDefs() {
    const glmLane = window.__GLM_LANE__ || null;
    const cfg = readRaceConfig();
    if (cfg) {
      const defs = [];
      for (let i = 0; i < cfg.lanes; i++) {
        const p = cfg.providers[i % cfg.providers.length];
        if (p.endpoint) {
          defs.push({
            overrides: {
              endpoint: p.endpoint,
              ...(p.model ? { model: p.model } : {}),
              ...(p.apiKey ? { apiKey: p.apiKey } : {}),
              ...(p.reasoningEffort
                ? { reasoningEffort: p.reasoningEffort, thinking: { type: 'enabled' } }
                : {}),
              label: p.label,
            },
            label: p.label,
          });
        } else {
          defs.push({ overrides: null, label: p.label === '供应商1' ? '默认' : p.label });
        }
      }
      return defs;
    }
    return glmLane
      ? [
          { overrides: null, label: 'step' },
          { overrides: glmLane, label: 'glm' },
        ]
      : [{ overrides: null, label: 'step' }];
  }
  function raceModalOpen() {
    const cfg = readRaceConfig();
    const glm = window.__GLM_LANE__ || null;
    const auto = glm
      ? [
          { label: '默认(step 代理)', endpoint: '', model: '', apiKey: '', reasoningEffort: '' },
          {
            label: 'glm',
            endpoint: glm.endpoint,
            model: glm.model,
            apiKey: glm.apiKey || '',
            reasoningEffort: glm.reasoningEffort || 'low',
          },
        ]
      : [{ label: '默认(step 代理)', endpoint: '', model: '', apiKey: '', reasoningEffort: '' }];
    const providers = (cfg && cfg.providers.length ? cfg.providers : auto).slice(0, 5);
    $('raceLanes').value = cfg ? cfg.lanes : glm ? 2 : 1;
    const box = $('raceProviders');
    const rows = [];
    for (let i = 0; i < 5; i++) {
      rows.push(
        '<div class="race-row">' +
          '<input data-f="label" placeholder="名称">' +
          '<input data-f="endpoint" placeholder="端点(留空=默认)">' +
          '<input data-f="model" placeholder="模型">' +
          '<input data-f="apiKey" type="password" placeholder="Key">' +
          '<select data-f="reasoningEffort"><option value="">档位</option><option value="high">high</option><option value="low">low</option><option value="max">max</option></select>' +
        '</div>',
      );
    }
    box.innerHTML = rows.join('');
    Array.from(box.children).forEach((row, i) => {
      const p = providers[i] || {};
      row.querySelectorAll('[data-f]').forEach((inp) => {
        const f = inp.dataset.f;
        inp.value = f === 'reasoningEffort' ? p.reasoningEffort || '' : p[f] || '';
      });
    });
    $('raceModal').classList.remove('hidden');
  }
  function raceModalSave() {
    const lanes = Math.max(1, Math.min(5, Number($('raceLanes').value) || 1));
    const providers = [];
    Array.from($('raceProviders').children).forEach((row, i) => {
      const get = (f) => {
        const el = row.querySelector('[data-f="' + f + '"]');
        return el ? String(el.value).trim() : '';
      };
      if (get('endpoint') || get('model') || get('apiKey'))
        providers.push({
          label: get('label') || '供应商' + (i + 1),
          endpoint: get('endpoint'),
          model: get('model'),
          apiKey: get('apiKey'),
          reasoningEffort: get('reasoningEffort'),
        });
    });
    if (!providers.length) {
      setStatus('至少要有一个供应商(端点/模型/Key 任一非空)。', 'error');
      return;
    }
    localStorage.setItem(RACE_CFG_KEY, JSON.stringify({ lanes, providers }));
    $('raceModal').classList.add('hidden');
    setStatus(
      '赛马配置已保存:' + lanes + ' 路循环使用 ' + providers.length + ' 个供应商。',
      'good',
    );
  }
  function raceModalReset() {
    localStorage.removeItem(RACE_CFG_KEY);
    $('raceModal').classList.add('hidden');
    setStatus('已恢复自动赛马配置。', 'good');
  }
  async function generate() {'''
assert anchor in s, 'generate anchor missing'
s = s.replace(anchor, cfg_layer, 1)

# ===== 2) generate():laneDefs 走配置层 =====
old_lanes = '''        /* 赛马路由(2026-08-30 单供应商退化):配置了 GLM(/api/llm-config 下发)时
           双供应商并行——glm(快,~1-2.5min)+ step advisor(质量兜底),每供应商
           各一路(同供应商并发会被平台排队,glm×2 实测反而更慢),整体失败自动
           重试一轮,两轮全败退回固定模板。没有 glm 配置(使用者只有一把 step key)
           时只跑**单路** step——旧实现退化成 [step, step] 双同源路:同 key 并发被
           平台排队,赛马塌回串行还双倍消耗限流配额。 */
        const glmLane = window.__GLM_LANE__ || null;
        const laneDefs = glmLane
          ? [
              { overrides: null, label: 'step' },
              { overrides: glmLane, label: 'glm' },
            ]
          : [{ overrides: null, label: 'step' }];'''
new_lanes = '''        /* 赛马路由(2026-08-30 供应商/路数可自定义):见 buildLaneDefs——
           自动模式(未自定义)有 glm 双路并行、无 glm 单路 step;
           自定义模式按「路数循环取供应商表」,最多 5 路,任意 OpenAI 兼容端点。 */
        const laneDefs = buildLaneDefs();'''
assert old_lanes in s, 'laneDefs block missing'
s = s.replace(old_lanes, new_lanes)

# ===== 3) 工作台泛化:起草人甲~戊 + 副行动态 =====
old_init = "  function wbLanesInit(defs) {\n    const lbox = wbEl('wbLanes');\n    if (lbox) lbox.innerHTML = '';\n    const dbox = wbEl('wbDrafts');\n    if (dbox) dbox.innerHTML = '';"
new_init = ("  function wbLanesInit(defs) {\n    const lbox = wbEl('wbLanes');\n    if (lbox) lbox.innerHTML = '';\n"
            "    const dbox = wbEl('wbDrafts');\n    if (dbox) dbox.innerHTML = '';\n"
            "    const crew = wbEl('wbHeadCrew');\n    if (crew)\n"
            "      crew.textContent =\n"
            "        defs.length > 1\n"
            "          ? '共 ' + defs.length + ' 位起草人同时起草,取先完成的那份'\n"
            "          : '单路起草,失败自动重试';")
assert old_init in s, 'wbLanesInit head missing'
s = s.replace(old_init, new_init)

old_name = """'<span class=\"wb-draft-name\">起草人 · ' + (i === 0 ? '甲' : '乙') + '</span>' +"""
new_name = """'<span class=\"wb-draft-name\">起草人 · ' + (DRAFT_NAMES[i] || i + 1) + '</span>' +"""
assert old_name in s, 'draft name missing'
s = s.replace(old_name, new_name)

# ===== 4) 模板:副行 crew span + 赛马配置按钮 + raceModal =====
old_head = '<div class="wb-headline"><h3>你的密室正在搭建</h3><p>两位起草人正在同时起草,取先完成的那份——通常两分钟左右。'
new_head = '<div class="wb-headline"><h3>你的密室正在搭建</h3><p><span id="wbHeadCrew">起草人准备中</span>——通常两分钟左右。'
assert old_head in s, 'headline missing'
s = s.replace(old_head, new_head)

old_sec = '<div class="home-secondary"><button id="homeImport" type="button">导入关卡</button>'
new_sec = '<div class="home-secondary"><button id="homeImport" type="button">导入关卡</button><button id="raceConfigBtn" type="button">赛马配置</button>'
assert old_sec in s, 'home-secondary missing'
s = s.replace(old_sec, new_sec)

old_pill = '<div class="gen-pill" id="genPill" hidden>'
assert s.count(old_pill) == 1, s.count(old_pill)
race_modal = ('<div class="modal hidden" id="raceModal"><div class="modal-card">'
              '<div class="kicker">赛马配置(可选)</div><h2>设计竞速的供应商与路数</h2>'
              '<p class="race-note">路数 1-5,各路按顺序循环使用下方供应商;端点留空 = 默认(本地代理 / 清洗配置)。'
              '同一家供应商并发可能被平台排队。空行忽略。自定义密钥只保存在本机浏览器,不上传、不入仓库。</p>'
              '<label class="race-lanes">赛马路数 <input id="raceLanes" type="number" min="1" max="5" value="2"></label>'
              '<div id="raceProviders"></div>'
              '<div class="modal-actions"><button class="reset" id="raceReset" type="button">恢复自动</button>'
              '<button class="primary" id="raceSave" type="button">保存配置</button></div>'
              '</div></div>')
s = s.replace(old_pill, race_modal + old_pill)

# ===== 5) boot 绑定 =====
old_bootb = "    $('logTicker').onclick = () => {"
new_bootb = ("    $('raceConfigBtn').onclick = raceModalOpen;\n"
             "    $('raceSave').onclick = raceModalSave;\n"
             "    $('raceReset').onclick = raceModalReset;\n"
             "    $('logTicker').onclick = () => {")
assert old_bootb in s, 'boot binding anchor missing'
s = s.replace(old_bootb, new_bootb)

io.open('js/app.js', 'w', encoding='utf-8', newline='').write(s)
print('app.js: config layer + UI wired, len', len(s))

# ===== 6) designWindow 报文去 step 化 =====
p2 = 'js/pipeline.js'
s2 = io.open(p2, encoding='utf-8').read()
msg_pairs = [
    ("          throw new Error('未提供 Step API Key，无法设计关卡');  // 本地 /api/step 代理由服务端注入密钥",
     "          throw new Error('该供应商未提供 API Key,无法设计关卡(' + endpoint + ')');  // 本地 /api/step 代理由服务端注入密钥"),
    ("          : 'Step 关卡设计请求失败：' + err.message,",
     "          : '设计请求失败：' + err.message,"),
    ("            throw new Error('Step 关卡设计 API ' + response.status + detail);",
     "            throw new Error('设计 API ' + response.status + detail);"),
]
for o, n in msg_pairs:
    assert o in s2, o[:50]
    s2 = s2.replace(o, n)
io.open(p2, 'w', encoding='utf-8', newline='').write(s2)
print('pipeline.js messages genericized')

# ===== 7) CSS =====
c = io.open('css/styles.css', encoding='utf-8').read()
c += '''
/* ===== 赛马配置弹窗(2026-08-30) ===== */
.race-note {
  font-size: 11.5px;
  color: var(--paper-ink-mid);
  margin: 6px 0;
}
.race-lanes {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  margin: 8px 0;
}
.race-lanes input {
  width: 60px;
  border: 1px solid rgba(44, 36, 22, 0.3);
  border-radius: 3px;
  padding: 4px 6px;
  background: rgba(255, 255, 255, 0.7);
}
.race-row {
  display: grid;
  grid-template-columns: 70px 1fr 110px 130px 74px;
  gap: 4px;
  margin-bottom: 4px;
}
.race-row input,
.race-row select {
  border: 1px solid rgba(44, 36, 22, 0.3);
  border-radius: 3px;
  padding: 4px 6px;
  font-size: 11px;
  background: rgba(255, 255, 255, 0.7);
  min-width: 0;
}
'''
io.open('css/styles.css', 'w', encoding='utf-8', newline='').write(c)
print('css appended')
