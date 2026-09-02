/* Import personal bookmarks into a secondary, inspectable room graph. */
(function () {
  const llmConfig = Object.assign(
    {
      endpoint: 'http://127.0.0.1:8128/api/step',
      model: 'step-3.7-flash',
      /* 密钥由本地 server 持有(server/STEP_API_KEY.local 或环境变量,已 gitignore)。
         此处留空:走本地 /api/step 代理时由服务端注入;直连第三方供应商时才需要在此填 key。 */
      apiKey: '',
      sampleLimit: 20,
    },
    window.__FAVORITES_ROOM_CONFIG__ || {},
  );
  const genericFolders = new Set([
    'bookmarks bar',
    'other bookmarks',
    'mobile bookmarks',
    '收藏夹',
    '书签栏',
    '其他书签',
    '移动书签',
    '其他',
    '未分类',
    '默认',
  ]);
  /* 标记记录版本:筛除规则/词表变动时递增,旧判定自动失效重新清洗 */
  const CLEAN_VERSION = 'clean-v1';
  const roleLabels = {
    learn: '学习 / 参考',
    build: '构建 / 工具',
    data: '数据 / 材料',
    inspiration: '灵感 / 观察',
    other: '其他',
  };
  const roleWords = {
    learn: '教程 文档 docs documentation wiki guide course learn 学习 教程 参考 mdn nand',
    build: 'github code coding playground tool 工具 npm vue react programiz game 开发',
    data: 'kaggle data dataset 数据 csv analytics 模型 machine learning',
    inspiration: 'design inspiration article blog visual 设计 灵感 文章 博客',
  };
  const $import = (id) => document.getElementById(id);
  const importButton = document.createElement('button');
  importButton.className = 'reset';
  importButton.id = 'importBookmarks';
  importButton.type = 'button';
  importButton.textContent = '导入收藏';
  document.querySelector('.hud')?.insertBefore(importButton, document.querySelector('.hud .reset'));
  const importModal = document.createElement('div');
  importModal.className = 'modal hidden';
  importModal.id = 'importModal';
  importModal.innerHTML =
    '<div class="import-card"><div class="kicker">个人收藏 / 草案室</div><h2>把收藏变成一间可探索的房间</h2><p>选择 Chrome 导出的书签 HTML 或 Bookmarks JSON。分组和关系只是建议，生成后仍然可以在画布上重新整理。每组首次只展开一小批，继续搜索才能看到更深处。</p><input class="import-file" id="importFile" type="file" accept=".html,.htm,.json,text/html,application/json"><div class="import-summary" id="importSummary">还没有读取文件。</div><div class="import-groups" id="importGroups"><div class="import-empty">导入后会在这里显示收藏分组。</div></div><div class="import-relations" id="importRelations">关系建议会标记为“可能相关”，不会替你断言收藏之间的真实联系。</div><div class="modal-actions"><button class="reset" id="importClose" type="button">关闭</button><button class="reset" id="importClean" type="button" disabled>智能清洗</button><button class="primary" id="importGenerate" type="button" disabled>生成房间草案</button></div></div>';
  document.body.appendChild(importModal);
  const levelPlanEl = document.createElement('div');
  levelPlanEl.className = 'level-plan';
  levelPlanEl.id = 'importLevelPlan';
  levelPlanEl.hidden = true;
  importModal.querySelector('.modal-actions').before(levelPlanEl);
  let currentDraft = null;
  const cleanState = { analysis: null, provider: null };
  const cleanModal = document.createElement('div');
  cleanModal.className = 'modal hidden';
  cleanModal.id = 'cleanModal';
  cleanModal.innerHTML =
    '<div class="clean-card"><div class="kicker">素材层 / 清洗</div><h2>先把收藏整理成可用素材</h2><p>清洗不会直接生成谜题。它会识别重复、低信号入口、主题和可能的用途，再把可解释的中间结果交给房间编排。</p><div class="clean-fields"><label class="clean-field">Step API Endpoint<input id="cleanEndpoint" value="http://127.0.0.1:8128/api/step"></label><label class="clean-field">Model<input id="cleanModel" value="step-3.7-flash"></label><label class="clean-field">API Key（仅本次使用，不保存）<input id="cleanApiKey" type="password" placeholder="已内置默认密钥"></label><label class="clean-field">发送样本上限<input id="cleanLimit" type="number" min="20" max="60" value="20"></label></div><div class="clean-note">默认只发送标题、域名和收藏夹路径，不发送完整 URL。Step 是生成关卡所必需的；调用失败时不会生成关卡。</div><div class="clean-report" id="cleanReport">点击“运行清洗”开始分析。</div><div class="modal-actions"><button class="reset" id="cleanClose" type="button">关闭</button><button class="reset" id="cleanRun" type="button">运行清洗</button><button class="primary" id="cleanApply" type="button" disabled>应用清洗结果</button></div></div>';
  document.body.appendChild(cleanModal);
  $import('cleanEndpoint').value = llmConfig.endpoint;
  $import('cleanModel').value = llmConfig.model;
  $import('cleanApiKey').value = llmConfig.apiKey;
  $import('cleanLimit').value = llmConfig.sampleLimit;
  function text(value) {
    return String(value ?? '')
      .replace(/\s+/g, ' ')
      .trim();
  }
  function label(value) {
    return text(value).replace(/[<>]/g, '');
  }
  function canonicalUrl(value) {
    try {
      const u = new URL(value);
      u.hash = '';
      [...u.searchParams.keys()].forEach((k) => {
        if (
          /^utm_/i.test(k) ||
          ['spm', 'from', 'source', 'ref', 'referrer', 'share_source'].includes(k.toLowerCase())
        )
          u.searchParams.delete(k);
      });
      u.pathname = u.pathname.replace(/\/+$/, '') || '/';
      return u.toString();
    } catch (_) {
      return text(value);
    }
  }
  const archiveHostRules =
    /^(?:gmgard\.com|lspgal\.top|lspgal\.us|touchgal\.(?:com|org)|edddm\.com|edddh4\.com|omofun\.in|senfun\.in|yhdmz\.org|88dm\.fans|857yhdm\.com|70kankan\.com|2cycd\.com|cometbbs\.com)$/i;
  function classifyBookmark(item) {
    const title = text(item.title),
      url = canonicalUrl(item.url),
      hay = (title + ' ' + url + ' ' + item.domain + ' ' + item.folder).toLowerCase();
    let reason = '';
    if (
      archiveHostRules.test(item.domain) ||
      /(成人|绅士|里番|本子|色情|hentai|nsfw|18禁|galgame|黄油|淫|エロ|lspgal|gmgard)/i.test(hay)
    )
      reason = '成人、NSFW 或资源社区入口';
    else if (
      /(赌博|博彩|彩票|六合彩|棋牌|德州扑克|押注|下注|盘口|casino|betting|网赚|刷单|兼职日结|返利|稳赚|代理返佣)/i.test(
        hay,
      )
    )
      reason = '博彩、彩票或网赚刷单';
    else if (
      /(诈骗|钓鱼|仿冒|假官网|中奖|内部消息|内幕消息|老师带单|跟单|资金盘|传销|空气币|杠杆炒币|合约交易所)/i.test(
        hay,
      )
    )
      reason = '诈骗、传销或高风险盘';
    else if (
      /(破解版|注册机|keygen|cracked|外挂|游戏辅助|私服|激活工具|盗版|无限资源版)/i.test(hay)
    )
      reason = '盗版、破解或外挂私服';
    else if (
      /(毒品|大麻|迷药|代购药品|枪支|弹药|代办证件|代开发票|银行卡收购|身份证办理)/i.test(hay)
    )
      reason = '违禁品或黑产交易';
    else if (
      /(asmr|耳舔|舔耳|足控|恋足|足趾|娇喘|福利姬|擦边|性暗示|性玩具|魅惑写真|福利站)/i.test(hay)
    )
      reason = '灰色擦边内容(暂缓入室)';
    else if (
      /(磁力|种子|ed2k|bt下载|资源搜索|资源分享|在线观看|免费观看|在线播放|第\\s*\\d+\\s*集|影视|动漫视频|file download|download page)/i.test(
        hay,
      )
    )
      reason = '下载、在线播放或资源入口';
    else if (
      /(首页|主页|门户网站|网站导航|发布页|powered by|论坛首页|bbs\\b|\\bforum\\b|注册考试|认证登录|登录页|login page)/i.test(
        hay,
      )
    )
      reason = '门户、论坛、导航或认证入口';
    else if (
      /(^|[?&=\\/])(login|signin|register|auth|account)([?&=\\/]|$)/i.test(url) ||
      /(登录|注册|校园网认证|web user login)/i.test(title)
    )
      reason = '登录、注册或一次性认证页面';
    else if (
      /^(?:实验|home|homepage|welcome|index|首页|主页)$/i.test(title) &&
      /^https?:\/\/[^/]+\/?(?:[?#].*)?$/i.test(url)
    )
      reason = '泛化首页，缺少可用内容';
    else if (
      !title.trim() ||
      /^(?:无标题|未命名|untitled|new tab|新建标签页|about:blank|about:home)$/i.test(title.trim())
    )
      reason = '无有效标题的空条目';
    const topics = [];
    if (/ai|模型|llm|人工智能|大模型|ollama|openrouter/.test(hay)) topics.push('AI / 模型');
    if (/代码|开发|github|程序|算法|api|技术|编程|nand/.test(hay)) topics.push('开发 / 技术');
    if (/学习|教程|文档|课程|日语|数学|wiki|mdn/.test(hay)) topics.push('学习 / 参考');
    if (/设计|灵感|文章|博客|visual|创作/.test(hay)) topics.push('创作 / 观察');
    if (/动漫|漫画|游戏|minecraft|二次元|视频|音乐/.test(hay)) topics.push('娱乐 / 文化');
    return {
      ...item,
      canonicalUrl: url,
      signal: reason ? 'low' : topics.length ? 'high' : 'medium',
      status: reason ? 'archive' : 'keep',
      /* 安全红线标记:成人/博彩/诈骗/盗版/违禁五类为确定性规则命中,模型决策不得改回 */
      safetyFlag: reason && /^(?:成人|博彩|诈骗|盗版|违禁|灰色)/.test(reason) ? reason : '',
      reason:
        reason || (topics.length ? '标题、域名或路径包含稳定主题' : '缺少足够主题词，建议模型复查'),
      topics,
    };
  }
  function localClean(items) {
    const unique = new Map(),
      duplicates = [];
    (items || []).forEach((item) => {
      const key = canonicalUrl(item.url);
      if (unique.has(key)) {
        duplicates.push(item);
        return;
      }
      unique.set(key, item);
    });
    const records = [...unique.values()].map(classifyBookmark);
    return {
      records,
      duplicates,
      stats: {
        input: (items || []).length,
        unique: records.length,
        duplicates: duplicates.length,
        keep: records.filter((x) => x.status === 'keep').length,
        review: records.filter((x) => x.status === 'review').length,
        archive: records.filter((x) => x.status === 'archive').length,
      },
    };
  }
  function modelSample(items, limit) {
    const max = Math.max(20, Math.min(60, Number(limit) || 20)),
      review = (items || []).filter((item) => item.status === 'review'),
      high = (items || []).filter((item) => item.status === 'keep' && item.signal === 'high'),
      medium = (items || []).filter((item) => item.status === 'keep' && item.signal !== 'high'),
      reviewCap = Math.max(4, Math.ceil(max * 0.5)),
      ranked = [
        ...review.slice(0, reviewCap),
        ...high,
        ...medium,
        ...review.slice(reviewCap),
        ...(items || []),
      ],
      seen = new Set();
    return ranked
      .filter((item) => {
        if (seen.has(item.id)) return false;
        seen.add(item.id);
        return true;
      })
      .slice(0, max)
      .map(function (item) {
        return {
          id: item.id,
          title: item.title,
          domain: item.domain,
          folder: item.folder,
          desc: (item.description || '').slice(0, 300),
          localStatus: item.status,
          localTopics: item.topics,
        };
      });
  }
  function applyModelResult(base, result) {
    const decisions = new Map(
      (result && Array.isArray(result.items) ? result.items : [])
        .filter((item) => item && item.id != null)
        .map((item) => [String(item.id), item]),
    );
      const records = base.records.map(function (item) {
        const d = decisions.get(String(item.id));
        if (item.safetyFlag)
          /* 安全红线:确定性规则命中的不安全内容,不允许模型决策改回可用状态 */
          return { ...item, status: 'archive', modelStatus: 'archive', modelReason: item.reason };
        if (!d) return item;
        const status = ['keep', 'review', 'archive'].includes(d.status) ? d.status : item.status,
          topics = Array.isArray(d.topics) && d.topics.length ? d.topics : item.topics,
          reason = text(d.reason) || item.reason;
        return {
          ...item,
          status,
          topics,
          reason,
          modelStatus: status,
          modelTopics: topics,
          modelIntent: text(d.intent),
          modelReason: reason,
        };
      }),
      stats = {
        ...base.stats,
        keep: records.filter((x) => x.status === 'keep').length,
        review: records.filter((x) => x.status === 'review').length,
        archive: records.filter((x) => x.status === 'archive').length,
        modelDecisions: records.filter((x) => x.modelStatus).length,
      };
    return { ...base, records, stats };
  }
  function parseModelJson(content) {
    let raw =
      (content &&
        content.choices &&
        content.choices[0] &&
        content.choices[0].message &&
        content.choices[0].message.content) ||
      content;
    if (Array.isArray(raw)) raw = raw.map((x) => x.text || '').join('');
    raw = String(raw || '').trim();
    /* 2026-08-23 容错:模型偶尔输出 Markdown 围栏,或超长被截断。剥围栏;整体解析失败时截取最外层 {...};截断时补闭合括号再试。 */
    raw = raw
      .replace(/^```(?:json)?\s*/i, '')
      .replace(/```\s*$/, '')
      .trim();
    try {
      return JSON.parse(raw);
    } catch (_) {}
    const start = raw.indexOf('{'),
      end = raw.lastIndexOf('}');
    if (start >= 0 && end > start) {
      const body = raw.slice(start, end + 1);
      try {
        return JSON.parse(body);
      } catch (_) {}
      let fixed = body.replace(/,\s*$/, '');
      if ((fixed.match(/"/g) || []).length % 2 === 1) fixed += '"';
      const ob = (fixed.match(/\{/g) || []).length - (fixed.match(/\}/g) || []).length;
      const os = (fixed.match(/\[/g) || []).length - (fixed.match(/\]/g) || []).length;
      if (os > 0) fixed += ']'.repeat(os);
      if (ob > 0) fixed += '}'.repeat(ob);
      try {
        return JSON.parse(fixed);
      } catch (_) {}
    }
    return null;
  }
  async function readStepResponse(response, report) {
    const type = (response.headers.get('content-type') || '').toLowerCase();
    if (!type.includes('text/event-stream')) return parseModelJson(await response.json());
    const reader = response.body.getReader(),
      decoder = new TextDecoder(),
      parts = [];
    let buffer = '',
      chars = 0;
    for (;;) {
      const chunk = await reader.read();
      if (chunk.done) break;
      buffer += decoder.decode(chunk.value, { stream: true });
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (!line.startsWith('data:')) continue;
        const raw = line.slice(5).trim();
        if (!raw || raw === '[DONE]') continue;
        try {
          const event = JSON.parse(raw),
            delta =
              event.choices &&
              event.choices[0] &&
              event.choices[0].delta &&
              event.choices[0].delta.content;
          if (delta) {
            parts.push(delta);
            chars += delta.length;
            if (report) report.textContent = 'Step 正在生成…… 已接收 ' + chars + ' 个字符';
          }
        } catch (_) {}
      }
    }
    if (buffer.trim()) {
      const raw = buffer.trim().replace(/^data:\s*/, '');
      if (raw && raw !== '[DONE]')
        try {
          const event = JSON.parse(raw),
            delta =
              event.choices &&
              event.choices[0] &&
              event.choices[0].delta &&
              event.choices[0].delta.content;
          if (delta) {
            parts.push(delta);
            chars += delta.length;
            if (report) report.textContent = 'Step 正在生成…… 已接收 ' + chars + ' 个字符';
          }
        } catch (_) {}
    }
    return parseModelJson(parts.join(''));
  }
  /* 清洗供应商可配(2026-08-30):赛马配置里 cleaning=某供应商 label 时,
     清洗走该供应商;未指定/未匹配则走默认(本地代理 / 清洗配置)。 */
  function cleaningProvider() {
    try {
      const raw = JSON.parse(localStorage.getItem('fav-room-race-v1') || 'null');
      const label = raw && raw.cleaning;
      if (!label) return {};
      const p = (raw.providers || []).find((x) => x && x.label === label) || {};
      return {
        endpoint: String(p.endpoint || '').trim(),
        model: String(p.model || '').trim(),
        apiKey: String(p.apiKey || '').trim(),
      };
    } catch (_) {
      return {};
    }
  }
  async function callStep(items, theme = '', sampleLimitOverride) {
    const prov = cleaningProvider();
    let configuredEndpoint = prov.endpoint || $import('cleanEndpoint').value.trim() || llmConfig.endpoint;
    if (!prov.endpoint && (/api\.stepfun\.com/i.test(configuredEndpoint) || !configuredEndpoint))
      configuredEndpoint = 'http://127.0.0.1:8128/api/step';
    const endpoint = configuredEndpoint,
      model = prov.model || $import('cleanModel').value.trim() || llmConfig.model,
      key = prov.apiKey || $import('cleanApiKey').value.trim() || llmConfig.apiKey;
    if (!key && !/api\/(step|glm)/.test(endpoint))
      throw new Error('该供应商未提供 API Key,无法生成关卡(' + endpoint + ')');  // 本地 /api/step 代理由服务端注入密钥
    const prompt = {
      /* sampleLimitOverride:cleanBatch 分批调用时按整批采样,避免被 sampleLimit 截断丢条目 */
      items: modelSample(
        items,
        sampleLimitOverride ?? ($import('cleanLimit').value || llmConfig.sampleLimit),
      ),
      schema: {
        items: [
          {
            id: '原 id',
            status: 'keep|review|archive',
            topics: ['主题'],
            intent: '收藏用途',
            reason: '一句话依据',
          },
        ],
        groups: [
          {
            name: '主题名',
            itemIds: ['原 id'],
            role: 'learn|build|data|inspiration|other',
            reason: '分组依据',
          },
        ],
        relations: [{ from: '组名', to: '组名', reason: '可复查关系', confidence: 'low|medium' }],
      },
    };
    const controller = new AbortController(),
      timer = setTimeout(() => controller.abort(), 120000);
    let response;
    try {
      response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + key },
        body: JSON.stringify({
          model: model,
          messages: [
            {
              role: 'system',
              content:
                '你是个人收藏素材整理器。只基于输入的标题、域名和文件夹推断，不编造网页正文。输出严格 JSON，不要 Markdown。\n\n【筛除规则,严格执行】\n1. 不安全内容——色情成人、赌博博彩彩票、诈骗钓鱼传销资金盘、盗版破解外挂私服、毒品违禁品武器交易、血腥暴力恐怖、仇恨极端——一律 status:"archive"，reason 注明类别（如"赌博站点"），禁止进入 groups 与 relations。\n2. 无价值内容——死链或停放域名、空壳导航门户页、纯广告页、登录墙后无实际内容、与其他条目完全重复（仅保留一条）——同样 status:"archive"。\n3. 只有信息量充足且来源正当的才 "keep"；价值拿不准一律 "review"。\n4. 输入中 localStatus:"archive" 的是本地规则预筛条目——请复核：确属无价值/不安全则维持 archive；若本地误判且确有实际内容，可改回 "review" 或 "keep"。\n每条 reason 不超过 20 字，topics 最多 2 个，groups 最多 6 个，relations 最多 6 个。用户希望关卡风格为：' +
                label(theme || '未指定') +
                '。风格只影响命名、氛围和谜题包装，不得改变素材事实。',
            },
            { role: 'user', content: JSON.stringify(prompt) },
          ],
          temperature: 0.1,
          ...(llmConfig.reasoningEffort ? { reasoning_effort: llmConfig.reasoningEffort } : {}),
          // 清洗快车道(2026-08-28):清洗是结构化抽取——对本代理跳过 advisor 强制,改用
          // reasoning_effort:'low'(step 文档:low 适用于信息抽取;实测 2.0s vs high 4.1s,
          // 且与 thinking:disabled 同发时低档会被压住,故快车道省略 thinking 字段)。
          // 其他供应商端点不附加 router_force(避免未知字段被拒)。
          // 配置项:cleanFast:false 关闭快车道;cleanReasoningEffort 覆盖档位。
          ...(llmConfig.cleanFast !== false && /\/api\/step/.test(endpoint)
            ? {
                router_force: false,
                reasoning_effort: llmConfig.cleanReasoningEffort || 'low',
              }
            : { thinking: llmConfig.thinking || { type: 'disabled' } }),
          stream: true,
        }),
        signal: controller.signal,
      });
    } catch (err) {
      throw new Error(
        err.name === 'AbortError'
          ? 'Step 请求超时（120 秒），未生成关卡'
          : 'Step 请求失败：' + err.message,
      );
    } finally {
      clearTimeout(timer);
    }
    if (!response.ok) {
      let detail = '';
      try {
        const body = await response.json();
        detail = body.error && body.error.message ? '：' + body.error.message : '';
      } catch (_) {}
      throw new Error('Step API ' + response.status + detail);
    }
    const parsed = await readStepResponse(response, $import('cleanReport')),
      sampleIds = new Set(
        modelSample(items, $import('cleanLimit').value || llmConfig.sampleLimit).map((item) =>
          String(item.id),
        ),
      );
    if (!parsed || !Array.isArray(parsed.items) || !Array.isArray(parsed.groups))
      throw new Error('模型返回缺少 items 或 groups，未生成关卡');
    parsed.items = parsed.items.filter((item) => item && sampleIds.has(String(item.id)));
    if (!parsed.items.length) throw new Error('模型没有返回可对应的素材 ID，未生成关卡');
    if (
      !parsed.groups.some(
        (group) =>
          Array.isArray(group.itemIds) && group.itemIds.some((id) => sampleIds.has(String(id))),
      )
    )
      throw new Error('模型没有返回有效分组，未生成关卡');
    return { model: model, parsed: parsed };
  }
  async function callStepLevel(draft, theme = '', repairNote = '') {
    const getEl = (id) => document.getElementById(id),
      configuredEndpoint = getEl('cleanEndpoint').value.trim() || llmConfig.endpoint,
      endpoint =
        /api\.stepfun\.com/i.test(configuredEndpoint) || !configuredEndpoint
          ? 'http://127.0.0.1:8128/api/step'
          : configuredEndpoint,
      model = getEl('cleanModel').value.trim() || llmConfig.model,
      key = getEl('cleanApiKey').value.trim() || llmConfig.apiKey;
    if (!key && !/api\/(step|glm)/.test(endpoint)) throw new Error('该供应商未提供 API Key,无法设计关卡(' + endpoint + ')');
    const candidates = (draft.items || [])
      .filter((item) => item.status !== 'archive')
      .slice(0, 18)
      .map((item) => ({
        id: item.id,
        title: item.title,
        domain: item.domain,
        desc: (item.description || '').slice(0, 300),
        topics: item.topics,
        intent: item.modelIntent || '',
        reason: item.modelReason || item.reason || '',
      }));
    if (candidates.length < 4) throw new Error('清洗后可用素材少于 4 条，无法设计有意义的关卡');
    const prompt = {
      theme: theme || '', /* P33:不再默认锚定「复古电脑密室」——主题空缺时由素材自由联想 */
      groups: (draft.groups || [])
        .filter((g) => g.name !== '待编排素材')
        .slice(0, 8)
        .map((g) => ({
          name: g.name,
          role: g.role,
          itemIds: g.items.map((x) => x.id),
          reason: g.reason,
        })),
      items: candidates,
      schema: {
        level: {
          title: '关卡标题',
          premise: '与素材有关的处境，不得泛泛而谈',
          objective: '玩家要完成的具体目标',
          targetMinutes: '8-15',
          scenes: [
            {
              id: 'scene id',
              title: '场景名(如:积灰的资料架)',
              description: '玩家站在这个场景里看到/听到什么,2-3 句感官描写(灯光/声音/气味/触感)',
              focus: '场景核心装置或空间特征(如:一台老式检索机)',
              items: [
                {
                  id: '素材 id',
                  role: 'clue|tool|lock|transform|reward|red_herring',
                  scene_name:
                    '素材在此场景中的化身名(具体的物件,如"贴满便签的索引抽屉",不要直接用网站名)',
                  reason:
                    '印在化身上的谜面,引用本场景或前一场景其他化身的具体事实,让玩家能交叉推理',
                },
              ],
              beats: [
                {
                  id: 'step id',
                  title: '可观察的步骤',
                  action: 'inspect|combine|revisit|sequence|deliver|password|angle|morse|knock',
                  uses: ['素材 id 或 result:前置组合步id'],
                  requires: ['前置 step id'],
                  reveals: ['本步完成后显形的隐藏素材 id;标了 auto:true 的当场弹出,其余待回访'],
                  'password专用 expected': '3-6位数字,如 685',
                  'angle专用 angles': [90, 180],
                  'angle专用 precision': 30,
                  'morse专用 code': '...--/--.../.----',
                  'knock专用 count': 3,
                  '物件专用 auto': 'true=本步完成时该隐藏素材当场弹出(机关的现实后果);缺省=待回访发现',
                  '物件专用 arrive_text': 'auto 物件的到场文案,≤40字;人物到场必写(如「端着茶杯从借阅台踱来」)',
                },
              ],
            },
          ],
          hints: ['6-8 条渐进提示:先观察级、再联想级、最后行动级,绝不直接给密码或顺序'],
        },
      },
    };
    const controller = new AbortController(),
      timer = setTimeout(() => controller.abort(), llmConfig.timeout || 240000);
    let response;
    try {
      response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + key },
        body: JSON.stringify({
          model,
          messages: [
            {
              role: 'system',
              content:
                '你是收藏夹密室的关卡设计师。这关是一间**分场景**的密室:关卡由 2-3 个 scene(场景)组成,所有场景开局同时亮出,玩家自由往返探索;每个场景有自己的可交互物件和谜题,最后一个房间的锁需要前面房间读到的线索才能解开。\n\n【场景结构】\n每个 scene 是密室里的一个具体位置(资料架/工作台/储藏室/墙角……),必须包含:\n- description:2-3 句感官描写(灯光/声音/气味/触感),让玩家"站在那里"\n- focus:这个场景的核心装置(检索机/保险柜/通风管……),谜题围绕它展开\n- items:素材的化身——每个素材化身为场景里的一件具体物件(scene_name,如"贴满便签的索引抽屉"),不要直接用网站名;卡片上显示化身名+reason 谜面\n- beats:本场景内的解谜步骤\n场景之间的收束要有因果:最后场景的推理锁(或交付前的关键步)用 requires 引用前面场景读线索的步骤,答案必须拼合多个场景的事实才能推出。\n\n【reason 写法,最重要】\nreason 是印在化身物件上的谜面,不是设计说明。合格标准:它必须引用同场景或前一场景其他化身的具体事实,制造玩家可以动手验证的交叉关系。对比:\n- 坏:"这是代码托管平台,需要和前端工具组合" ← 复述说明\n- 好:"抽屉里的便签只写了『协作』,但检索机上的铭牌写着『把成果交上来』——两件东西谁先动?" ← 玩家要对比两件物件才能确定\n禁止:复述单卡 desc、编用途、"系统会提示"话术。\n\n【谜题原型,每场景至少用一个】\nA. 排除法:多个化身部分相似,找关键差异排干扰\nB. 接力法:一个化身的末尾动作是另一个的开头(交/发/存 ↔ 收/取)\nC. 配对法:两个化身各持一半信息,合起来才指向下一件\n\n【手法菜单(2026-08-31 示例关沉淀,任选 2-3 种构成机制族,同一手法全关只用一次)】\n1. 显影:combine(工具,目标)让目标原位变身露出信息。信息必须被物理遮蔽(油垢/胶带/撕碎),工具在更早步骤可得。范例:去污粉擦配电箱、镊子揭胶带。\n2. 检索多问:同一 lock 物件挂多把 password(引擎按完成顺序逐个弹出);前一份档案的 reason 自然提及下一个检索词,证据链两跳以上。范例:检索 461→档案备注『压轴不在曲库』→再检索『压轴』。\n3. 敲击:beat 写 action 为 knock、uses 为该物件、count 为 2 到 5(建议 3)——连点 count 次完成。**任何文案禁止出现次数与『连敲/连按/多敲』字样(校验器会打回)**;可发现性只靠物件质感(『空响的底板』『破碎的墙』);知识分离:知识物件(备忘)到来前,物件描述完全惰性。\n4. 主动显形:隐藏素材标 auto:true,且显形它的 beat 写 product 交代因果来源(如检索台变身『嗡嗡作响的检索台』,底板『被振动震出』)——新物件当场弹出;未标 auto 的维持回访。人物到场用 arrive_text 写到场文案(『端着茶杯从借阅台踱来』)。\n5. 顺序扫描:链式 combine(书A,机器)requires 上一步→(书B,机器)→…次序被物理 enforce(乱序拖上去无反应);机器连续变身写受理进度(『已受理 1/3』);次序依据写在规则物件里(按索书号/按学习次序)。\n6. NPC:一个 role=clue 的 auto 素材当角色,reason 直接写台词(含下一步钩子);combine(信物,NPC)=交易,NPC 原位变身+reveals 奖励。现身时机=某机关完成后的巧合事件(广播响,人从另一头走来)。信物早在场且当时无用途。\n7. 环境线索:场景 description 与物件 desc 里的『闲笔』必须参与推理(落日→房间朝西),与图纸/文件拼合才出答案;纯氛围不接线=浪费字数。\n8. 校验题:password 的 expected 来自页面内容本身(简介里的数字/术语),或经 external_task 引导玩家打开原收藏查证(如『翻到 3.1 节看分类』)。\n\n【答案与文案铁律(校验器会机器检查,违反即打回)】\n- 答案分布:锁的答案只许出现在**别的物件**的 reason 里;锁自身/premise/objective/hints 一律零答案。多把锁的答案来自不同物件的不同字段。\n- 页面内容出谜面:元数据(标题/域名/日期)负责接地与引路,页面讲的内容负责谜面本身;禁止编造编号/索书号充数。\n- 交付即叙事收束:deliver 的目标是有情感重量的产物(一封接任书/一份盖章的提货单),不是裸道具;最后一个 reveal 给玩家『后文』。\n- 结构密度:每场景开局可见物件 ≤4(其余藏进容器/hidden),场景之间的收束用产物与巧合事件衔接。\n\n【硬性规则】只使用输入素材 id;不得编造 desc 之外的事实;scenes 2-4 个;全部 scenes 的 items 合计至少 5 个,恰好 1 个 red_herring(化身看似与主线相关但不进任何 uses,其 reason 也要写成谜面);每个 scene 的 beats 至少 2 个且依赖成链;全部 scenes 合计必含 combine(恰好 2 id)、sequence(2-3 id,顺序依据写在相关 reason 里)、恰好 1 个 deliver(最后一个 beat,uses 1 id);第一步不能是 deliver。role 语义:clue 起点信息、tool 拖到别的物件上、lock 等正确组合来找它、transform 把中间结果变成可交付物、reward 不进入 uses、red_herring 不进入任何 uses。\n\n【推理锁:全关 1-2 个,password/angle/morse 三选一;检索多问手法可用两把 password 挂同一 lock】\n这是关卡的收束机关,必须与素材气质匹配:\n- password(数字密码锁):某物件的 reason 给出计算规则或对照规则,另一物件 reason 提供原始数据,expected 必须能被玩家唯一推导出来。范例:笔记写「3 是 ...--,7 是 --...」,日记写「生日是 3 月 14 日」,锁面刻「把电报机数字和生日加在一起」→ expected 取 685。\n- angle(角度旋钮):angles 是各旋钮目标角度,必须是 precision 的倍数。范例:「时钟停在三点三十分」→ angles=[90,180]。\n- morse(电码输入):code 用点.划-/分隔。必须有一个物件充当对照表。\n硬规则:锁的 uses[0] 是本场景 role=lock 的素材;推导依据必须完整出现在更早步骤可检查的物件 reason 里(用 requires 保证先读线索再碰锁);绝不允许出现无推导依据的裸数字/角度。锁解开时用 reveals 放出后续关键道具。\n\n【隐藏物件与回访】hidden:true 的素材开局不可见;某个非 deliver 步骤的 reveals 列出它后,它进入「待发现」——玩家点击环顾四周才显形,然后才能被后续步骤使用。全关 hidden 物件 1-2 个,reveals 它的步骤必须在 requires 上先于使用它的步骤(引擎会自动修正顺序)。\n\n【v6 · 谜题骨架硬性要求(编译器会因违反而整版打回重写)】\n1. 每个组合/顺序/锁的结果必须有下游:combine 的产物要么被后续 beat 用 "result:该步id" 引用参与下一步组合,要么产物节点(uses[1],即变身后的物件)本身被后续步骤继续检查/组合——像原作"排水管→棍子→撬锁"那样链条不断。产物悬空=不可玩。\n2. 全关链条必须收束:最后可玩的组合/顺序步的产物 → deliver 交付;或者用 password 解锁后 reveals 出 reward 再由其开启终局。绝不允许密码解完直接没有后续。\n3. combine 必须写 resultOn(结果落在哪个物件上)和 product(变身后叫什么);一次性道具(钥匙类)在用它的那一步加 consume:[道具id]。\n4. 推理锁(password/angle/morse)必须给出合法参数:password 的 expected 是 3-6 位数字且推导规则完整写在更早物件的 reason 里;angle 的 angles 都是 precision 的倍数;morse 的 code 只含 .-/ 。缺参数会被整版打回。\n5. 隐藏素材(hidden)至少一个显形路径:某个 beat 的 reveals 里要有它,并且显形后有 beat 使用它(reward 型除外)。\n6. 结构自检清单:每个 scene 的 beats 至少 2 步且首尾相接;scene 之间靠产物/状态衔接;总步数 6-12。\n\n【hints 写法】6-8 条渐进提示:前 1-2 条观察级(哪里值得再看一眼);中间 2-3 条联想级(哪些物件之间可能有关系);最后 2-3 条行动级(该尝试什么动作方向),绝不直接给出密码、角度或顺序答案。\n\n输出严格 JSON,不要 Markdown。用户指定风格为：' +
                label(theme || '未指定') +
                '。风格只影响叙事包装，不改变素材事实。',
            },
            {
              role: 'user',
              content: JSON.stringify(
                repairNote
                  ? {
                      ...prompt,
                      __上一版设计未通过结构校验__: repairNote,
                      __修复要求__: '严格修正以上问题后重新输出完整关卡 JSON',
                    }
                  : prompt,
              ),
            },
          ],
          temperature: 0.2,
          thinking: llmConfig.thinking || { type: 'disabled' },
          ...(llmConfig.reasoningEffort ? { reasoning_effort: llmConfig.reasoningEffort } : {}),
          stream: true,
        }),
        signal: controller.signal,
      });
    } catch (err) {
      throw new Error(
        err.name === 'AbortError'
          ? '关卡设计请求超时,未生成关卡'
          : '设计请求失败：' + err.message,
      );
    } finally {
      clearTimeout(timer);
    }
    if (!response.ok) {
      let detail = '';
      try {
        const body = await response.json();
        detail = body.error && body.error.message ? '：' + body.error.message : '';
      } catch (_) {}
      throw new Error('设计 API ' + response.status + detail);
    }
    const parsed = await readStepResponse(response, getEl('cleanReport')),
      allowed = new Set(candidates.map((x) => String(x.id)));
    let level = parsed && parsed.level;
    /* 2026-08-23 容错:模型有时把关卡对象直接放在顶层(不带 level 包装);scenes 结构也接受 */ if (
      (!level || !Array.isArray(level.items)) &&
      parsed &&
      Array.isArray(parsed.items) &&
      Array.isArray(parsed.beats)
    )
      level = parsed;
    if (!level && parsed && Array.isArray(parsed.scenes) && parsed.scenes.length) level = parsed;
    if (
      level &&
      Array.isArray(level.scenes) &&
      level.scenes.length &&
      !Array.isArray(level.items)
    ) {
      /* scenes 结构:合成顶层 items/beats 供校验,compileLevel 优先读 scenes */ const its = [],
        bs = [];
      level.scenes.forEach(function (sc, si) {
        (sc.items || []).forEach(function (x) {
          if (x && x.id != null) its.push(x);
        });
        (sc.beats || []).forEach(function (b) {
          if (b && b.id != null) bs.push(b);
        });
      });
      level = { ...level, items: its, beats: bs };
    }
    if (!level || !Array.isArray(level.items) || !Array.isArray(level.beats)) {
      window.__lastDesignDebug = {
        parsedNull: !parsed,
        parsedKeys: parsed ? Object.keys(parsed) : null,
        levelNull: !level,
        levelItems: level && Array.isArray(level.items) ? level.items.length : 'missing',
        levelBeats: level && Array.isArray(level.beats) ? level.beats.length : 'missing',
      };
      throw new Error('模型返回缺少有效关卡结构，未生成关卡');
    }
    const levelItems = level.items.filter((item) => item && allowed.has(String(item.id)));
    if (levelItems.length < 4) throw new Error('模型选用的有效素材少于 4 条，未生成关卡');
    return {
      model,
      parsed: { ...level, items: levelItems, beats: Array.isArray(level.beats) ? level.beats : [] },
    };
  }
  function draftFromClean(base, modelResult) {
    const records = base.records.map((item) => ({ ...item, url: item.canonicalUrl || item.url })),
      byId = new Map(records.map((item) => [item.id, item])),
      rawGroups = modelResult && Array.isArray(modelResult.groups) ? modelResult.groups : [],
      groups = rawGroups
        .filter(Boolean)
        .map(function (g, index) {
          const its = (Array.isArray(g.itemIds) ? g.itemIds : [])
            .map(function (id) {
              return byId.get(id);
            })
            .filter(Boolean);
          return its.length
            ? {
                id: 'group-' + index,
                name: label(g.name) || '主题 ' + (index + 1),
                items: its,
                role: ['learn', 'build', 'data', 'inspiration', 'other'].includes(g.role)
                  ? g.role
                  : dominantRole(its),
                reason: label(g.reason),
              }
            : null;
        })
        .filter(Boolean);
    const used = new Set(
        groups.flatMap(function (g) {
          return g.items.map(function (item) {
            return item.id;
          });
        }),
      ),
      rest = records.filter(function (item) {
        return item.status !== 'archive' && !used.has(item.id);
      });
    if (rest.length)
      groups.push({
        id: 'group-' + groups.length,
        name: '待编排素材',
        items: rest,
        role: 'other',
        reason: '模型没有足够把握归入已有主题',
      });
    return {
      items: records,
      groups: groups,
      relations: ((modelResult && modelResult.relations) || []).slice(0, 12),
      puzzles: [
        { type: 'observe', label: '先展开一个高信号主题' },
        { type: 'combine', label: '复查模型建议的关系' },
        { type: 'revisit', label: '清洗后重新查看旧分组' },
      ],
      createdAt: new Date().toISOString(),
      cleaning: base,
    };
  }
  /* beat 依赖可达性:rid 是否是 bid 的祖先(直接或经 requires 链) */
  function beatAncestor(beats, rid, bid) {
    if (rid === bid) return true;
    const bMap = new Map(beats.map((b) => [b.id, b]));
    const seen = new Set();
    const stack = [...(bMap.get(bid)?.requires || [])];
    while (stack.length) {
      const cur = stack.pop();
      if (cur === rid) return true;
      if (seen.has(cur)) continue;
      seen.add(cur);
      const nb = bMap.get(cur);
      if (nb) stack.push(...(nb.requires || []));
    }
    return false;
  }
  /* ---------------- 门禁清单(GATE_MANIFEST,2026-09-01)----------------
     「教学-考纲」同源:每条机器检查配一句注入 prompt 的铁律文案 + 校验器源码锚点。
     新增门禁时在这里加一条——prompt 段落自动生成,verify_gate_manifest.py 会
     逐条断言「prompt 里有话 + 校验器里有锚」,再也不会出现「模型不知道的门」。 */
  const GATE_MANIFEST = [
    { id: 'P67', line: '答案分布:锁的答案只许出现在**别的物件**的 reason 里;锁自身/premise/objective/hints 一律零答案——机器逐字扫描,把答案写在锁自己的铭牌上是最常见的打回原因。', anchor: 'P67 答案分布铁律' },
    { id: 'P62', line: 'sourceFacts 接地:每个 sourceFacts 的值必须能在该素材的 desc/标题/路径/域名/日期里原样找到——编造或改写页面事实会被逐字比对拒绝。', anchor: '接地检查(P46/P62)' },
    { id: 'P4', line: '答案泄漏:机关答案不得原样出现在 premise/objective/hints 里。', anchor: '泄漏检查(P4/审查 11.2)' },
    { id: 'P55', line: '机关摆放:password/angle/morse 的目标物件不得同时是任何 inspect/revisit 步骤的目标——否则观察步永远无法完成。', anchor: 'v7.1 静态 lint' },
    { id: 'P40', line: '空间密度:每个房间至少 1 件 hidden 素材并有「容器显形」链,全关 reveals ≥2,至少 1 件物件被两个步骤使用(回访)。', anchor: '空间密度硬门槛' },
    { id: 'P46', line: '机构/信息分工:每个房间至少 1 件 prop-* 机关道具(全关 ≤5),机关道具 reason 只写自身物性;素材化身只做信息载体。', anchor: '机关道具配额' },
    { id: 'P42', line: '终局收束:交付的依赖闭包必须横跨至少 2 个房间——两间屋的事实要拼合才能通关。', anchor: '房间全亮后的收束检查' },
    { id: 'P74', line: '敲击可发现性:knock 手法的文案禁止出现动作/次数指令(如「连敲三下」),可发现性只写物件质感;全关 knock 不超过 1 次。', anchor: 'P74:敲击可发现性' },
  ];
  function gatePromptSection() {
    return (
      '5. 答案与文案铁律(每条都有对应的机器检查,违反即整版打回):\n' +
      GATE_MANIFEST.map(function (g) { return '- ' + g.line; }).join('\n')
    );
  }

  /* ---------- 共享领域层(2026-09-01,P1.4):规则归一化的唯一来源 ----------
     引擎运行时(compiledUse)与求解器(solveLevel)都消费同一份 compileRules 产物,
     消除「result 解析/规则语义」在两处各自维护的漂移风险。原实现自 engine.js 原样上移。 */
  function compileRules(level) {
    const rules = {
      combines: [],
      sequences: [],
      inspects: [],
      delivers: [],
      passwords: [],
      angles: [],
      morses: [],
      knocks: [],
      beatCount: 0,
      reveals: {},
      beatMeta: {},
    };
    (level.beats || []).forEach(function (beat, index) {
      const ids = (beat.uses || []).map(String);
      rules.beatCount++;
      rules.beatMeta[beat.id] = {
        title: beat.title || '步骤 ' + (index + 1),
        requires: (beat.requires || []).map(String),
      };
      if (beat.reveals && beat.reveals.length) rules.reveals[beat.id] = beat.reveals;
      if (beat.action === 'combine' && ids.length >= 2) {
        /* 组合:uses[1] 是被加工的目标(原作中它变身成产物,如 排水管→棍子);product 是产物名 */
        rules.combines.push({
          pair: [ids[0], ids[1]],
          need: beat.id,
          clue: 'beat-' + beat.id,
          title: beat.title || '组合 ' + (index + 1),
          resultOn: beat.resultOn || ids[1],
          product: String(beat.product || ''),
          consume: Array.isArray(beat.consume) ? beat.consume.slice() : [],
        });
      } else if (beat.action === 'sequence' && ids.length >= 2) {
        rules.sequences.push({
          order: ids,
          need: beat.id,
          clue: 'beat-' + beat.id,
          title: beat.title || '顺序 ' + (index + 1),
          resultOn: beat.resultOn || ids[ids.length - 1],
          product: String(beat.product || ''),
        });
      } else if (beat.action === 'deliver' && ids.length >= 1) {
        rules.delivers.push({
          item: ids[0],
          need: beat.id,
          clue: 'beat-' + beat.id,
          title: beat.title || '交付 ' + (index + 1),
        });
      } else if ((beat.action === 'inspect' || beat.action === 'revisit') && ids.length >= 1) {
        rules.inspects.push({
          ids: ids,
          need: beat.id,
          clue: 'beat-' + beat.id,
          title: beat.title || '观察 ' + (index + 1),
          /* 检视产物(2026-08-31):inspect 的 product 让物件原位变身并广播更名,
             与组合的变身反馈对齐(『台灯』变成了『亮着的台灯』) */
          resultOn: ids[0],
          product: String(beat.product || ''),
        });
      } else if (beat.action === 'password' && ids.length >= 1) {
        /* 密码盘:uses[0] 是被点击的密码盘物件;expected 为正确密码;colors 给每位上色标签(如颜色密码) */
        rules.passwords.push({
          item: ids[0],
          expected: String(beat.expected || ''),
          colors: Array.isArray(beat.colors) ? beat.colors : [],
          need: beat.id,
          clue: 'beat-' + beat.id,
          title: beat.title || '密码 ' + (index + 1),
          resultOn: ids[0],
          product: String(beat.product || ''),
        });
      } else if (beat.action === 'knock' && ids.length >= 1) {
        /* 连按计数机关:同一物件连敲 count 次完成,原作暗格/铁窗的等价物 */
        rules.knocks.push({
          item: ids[0],
          count: Math.max(1, Number(beat.count) || 3),
          need: beat.id,
          clue: 'beat-' + beat.id,
          title: beat.title || '敲击 ' + (index + 1),
          resultOn: beat.resultOn || ids[0],
          product: String(beat.product || ''),
        });
      } else if (beat.action === 'angle' && ids.length >= 1) {
        /* 角度旋钮:uses[0] 是旋钮物件;angles 各旋钮目标角度;precision 每档角度 */
        rules.angles.push({
          item: ids[0],
          angles: Array.isArray(beat.angles) ? beat.angles : [],
          precision: Number(beat.precision) || 30,
          need: beat.id,
          clue: 'beat-' + beat.id,
          title: beat.title || '角度 ' + (index + 1),
          resultOn: ids[0],
          product: String(beat.product || ''),
          labels: Array.isArray(beat.labels) ? beat.labels.slice() : [],
        });
      } else if (beat.action === 'morse' && ids.length >= 1) {
        /* 摩斯码:uses[0] 是电报机物件;code 为目标点划序列 */
        rules.morses.push({
          item: ids[0],
          code: String(beat.code || ''),
          need: beat.id,
          clue: 'beat-' + beat.id,
          title: beat.title || '摩斯 ' + (index + 1),
          resultOn: ids[0],
          product: String(beat.product || ''),
        });
      }
    });
    /* deliver 没有 uses 时,接受任意已完成结果 */
    return rules;
  }

  function compileLevel(draft, design) {
    /* 2026-08-23 重写:LLM 设计优先。编译器只做校验/补全,不再用本地模板覆盖 LLM 的关卡设计。
       v2:支持 scenes 结构(场景分幕)。LLM 返回 scenes 时归一化为 items+beats+scenes;
       旧的平铺 items/beats 仍兼容(包装为单场景)。 */
    const all = ((draft && draft.items) || []).filter((item) => item.status !== 'archive');
    if (all.length < 4) throw new Error('清洗后可用素材少于 4 条，无法设计有意义的关卡');
    const byId = new Map(all.map((item) => [String(item.id), item]));
    const fact = (item) => {
      const bits = ['标题：' + text(item.title)];
      if (item.domain) bits.push('域名：' + item.domain);
      if (item.folder) bits.push('路径：' + item.folder);
      if (item.topics?.length) bits.push('主题：' + item.topics.join('、'));
      if (item.description) bits.push('描述：' + text(item.description).slice(0, 120));
      return bits.join(' · ');
    };
    const roleLabels = {
      clue: '线索',
      tool: '工具',
      lock: '锁',
      transform: '转化',
      reward: '结果',
      red_herring: '干扰',
    };
    const normalizeRole = (r) =>
      ['clue', 'tool', 'lock', 'transform', 'reward', 'red_herring'].includes(r) ? r : 'clue';

    /* --- 场景结构优先:LLM 返回 scenes --- */
    if (design && Array.isArray(design.scenes) && design.scenes.length) {
      const issues = [];
      const sceneItems = [],
        sceneBeats = [],
        scenes = [];
      const claimed = new Set(); /* 素材全局归属:一个 id 只进一个场景,防重复节点 */
      const RESULT_PREFIX = 'result:'; /* uses 里引用组合产物:key = result:<beatId> */
      /* 跨场景 requires 解析表(2026-08-30):编译把 beat id 重写为 sId+'-'+raw,而终局收束
         要求 requires 允许跨场景引用其他房间读线索的步骤——先建立「设计空间 beat id →
         编译后全 id」的全局映射;设计空间 raw id 重复时先到先得。 */
      const designBeatId = new Map();
      const designProducerRaws = new Set(); /* 全局 combine/sequence 产物表(支持跨房间 result:) */
      design.scenes.slice(0, 4).forEach(function (sc, si) {
        const sid = 'scene-' + (text(sc.id) || si + 1);
        (Array.isArray(sc.beats) ? sc.beats : []).filter(Boolean).forEach(function (b, i) {
          const raw = text(b.id) || String(i + 1);
          const full = sid + '-' + raw;
          if (!designBeatId.has(raw)) designBeatId.set(raw, full);
          designBeatId.set(full, full);
          if (b.action === 'combine' || b.action === 'sequence') {
            designProducerRaws.add(raw);
            designProducerRaws.add(full);
          }
        });
      });
      design.scenes.slice(0, 4).forEach(function (sc, si) {
        const sId = 'scene-' + (text(sc.id) || si + 1);
        /* 场景内素材:化身名+role+谜面+hidden;已被前面场景用过的素材跳过。
           机关道具(2026-08-30 需求方裁定):id 以 prop- 开头的**无网页背景纯机构**
           (锁具/火柴/油灯/铁柜/抽屉)——机构与信息分工:素材化身承担谜面证据,
           机关道具只承担机构与空间,不再让收藏硬扮锁具(牵强感根因)。 */
        const isPropId = (id) => /^prop-[a-z0-9_-]{0,24}$/i.test(String(id));
        const sItems = (Array.isArray(sc.items) ? sc.items : [])
          .filter((it) => {
            if (!it || !it.id) return false;
            const id = String(it.id);
            return !claimed.has(id) && (byId.has(id) || isPropId(id));
          })
          .slice(0, 9)
          .map(function (it) {
            const id = String(it.id),
              role = normalizeRole(it.role);
            if (!byId.has(id)) {
              return {
                id,
                role,
                roleLabel: roleLabels[role] || '装置',
                title: label(it.scene_name || it.sceneName) || '机关道具',
                sceneName: label(it.scene_name || it.sceneName) || '机关道具',
                scene: sId,
                reason: text(it.reason) || '一件沉默的机构,等一次正确的操作。',
                hidden: it.hidden === true || it.start_hidden === true,
                auto: it.auto === true,
                arriveText: text(it.arrive_text || it.arriveText).slice(0, 40),
                prop: true,
              };
            }
            const src = byId.get(id);
            claimed.add(id);
            return {
              id,
              role,
              roleLabel: roleLabels[role] || '线索',
              title: src.title,
              sceneName: label(it.scene_name || it.sceneName) || src.title,
              scene: sId,
              reason: text(it.reason) || fact(src),
              hidden: it.hidden === true || it.start_hidden === true,
              /* 内容加工层(P61):digest=设计模型写的一句话中文摘要;facts=原样抄录的
                 事实键值(接地检查已验证值真实存在于素材文本);grounding 标记素材
                 谜题材料来源(content=有网页描述/metadata=仅元数据,P44/P65) */
              digest: text(it.digest).slice(0, 80),
              facts: (Array.isArray(it.sourceFacts) ? it.sourceFacts : [])
                .slice(0, 3)
                .map((f) => ({ k: text(f && f.k).slice(0, 10), v: text(f && f.v).slice(0, 20) }))
                .filter((f) => f.k && f.v),
              grounding: (src.description || '').trim() ? 'content' : 'metadata',
              externalTask: text(it.externalTask).slice(0, 40),
              auto: it.auto === true,
              arriveText: text(it.arrive_text || it.arriveText).slice(0, 40),
              prop: false,
            };
          });
        /* 场景内 beats;uses 支持本场景素材 id 与 result:<本场景 combine/sequence beat 短id>;
           reveals: 完成该 beat 时本场景内显形的素材 id 列表 */
        const sValid = new Set(sItems.map((x) => x.id));
        const rawBeats = (Array.isArray(sc.beats) ? sc.beats : []).filter(Boolean);
        const producerIds = new Set(
          rawBeats
            .filter((b) => b && (b.action === 'combine' || b.action === 'sequence'))
            .map((b) => sId + '-' + (text(b.id) || '')),
        );
        const normUse = (id) => {
          id = String(id);
          if (id.startsWith(RESULT_PREFIX)) {
            const pid = id.slice(RESULT_PREFIX.length);
            if (producerIds.has(sId + '-' + pid)) return RESULT_PREFIX + sId + '-' + pid;
            /* 跨房间产物(2026-08-30):把其他房间做好的成品拿到本房间用——
               引擎在并行房间模式下支持产物跨场景使用;收束由 requires 闭包保证 */
            if (designProducerRaws.has(pid) && designBeatId.has(pid))
              return RESULT_PREFIX + designBeatId.get(pid);
            return null;
          }
          return sValid.has(id) ? id : null;
        };
        let sBeats = rawBeats
          .map(function (b, i) {
            /* v6:保留 resultOn/product/consume——原位变身与消耗语义是示例关卡的灵魂,之前被丢弃导致所有组合都落在 uses[1]、无变身名 */
            const rawResultOn = text(b.resultOn);
            return {
              id: sId + '-' + (text(b.id) || i + 1),
              title: text(b.title) || '步骤 ' + (i + 1),
              action: [
                'inspect',
                'combine',
                'revisit',
                'sequence',
                'deliver',
                'password',
                'angle',
                'morse',
                'knock',
              ].includes(b.action)
                ? b.action
                : 'inspect',
              count: Math.min(5, Math.max(2, Number(b.count) || 3)),
              uses: (Array.isArray(b.uses) ? b.uses : []).map(normUse).filter(Boolean),
              requires: (Array.isArray(b.requires) ? b.requires : []).map(String),
              reveals: (Array.isArray(b.reveals) ? b.reveals : [])
                .map(String)
                .filter((id) => sValid.has(id)),
              expected: text(b.expected),
              angles: Array.isArray(b.angles) ? b.angles.slice(0, 3) : [],
              precision: Number(b.precision) || 30,
              code: text(b.code),
              labels: Array.isArray(b.labels) ? b.labels.slice() : [],
              colors: Array.isArray(b.colors) ? b.colors.slice() : [],
              resultOn:
                rawResultOn && sValid.has(rawResultOn)
                  ? rawResultOn
                  : rawResultOn && producerIds.has(sId + '-' + rawResultOn)
                    ? RESULT_PREFIX + sId + '-' + rawResultOn
                    : '',
              product: text(b.product),
              consume: (Array.isArray(b.consume) ? b.consume : []).filter((id) => sValid.has(id)),
              deriveFrom: (Array.isArray(b.deriveFrom) ? b.deriveFrom : []).map(String),
            };
          })
          .filter((b) =>
            b.action === 'combine' || b.action === 'sequence'
              ? b.uses.length >= 2
              : b.uses.length >= 1,
          );
        /* 推理锁参数清洗与全局配额:参数不合法降级为 inspect;password≤2/angle≤2/morse≤1/knock≤1 防滥用 */
        const seen = { password: 0, angle: 0, morse: 0, knock: 0 };
        sBeats.forEach(function (b) {
          if (b.action === 'knock') {
            /* P74:敲击可发现性内嵌于物件质感——文案出现动作/次数指令即降级 */
            const badKnock = sItems.some(function (it) {
              return /(连敲|三下|连按|多敲)/.test(it.reason || '');
            });
            if (badKnock || seen.knock >= 1) {
              issues.push(
                badKnock
                  ? '敲击的次数/动作写进了文案(P74 禁止),「' + b.title + '」已降级为检查步骤'
                  : '敲击机关「' + b.title + '」超出配额,已降级为检查步骤',
              );
              b.action = 'inspect';
              return;
            }
            seen.knock++;
            return;
          }
          if (!['password', 'angle', 'morse'].includes(b.action)) return;
          if (seen[b.action] >= { password: 2, angle: 2, morse: 1 }[b.action]) {
            issues.push('机关「' + b.title + '」超出该类型配额,已降级为检查步骤');
            b.action = 'inspect';
            return;
          }
          if (b.action === 'password') {
            b.expected = String(b.expected || '').replace(/\D/g, '');
            if (!b.expected || b.expected.length > 6) {
              issues.push('密码锁「' + b.title + '」缺少合法 expected,已降级为检查');
              b.action = 'inspect';
            }
          } else if (b.action === 'angle') {
            const p = [10, 15, 30, 45].includes(b.precision) ? b.precision : 30;
            b.angles = b.angles
              .map(Number)
              .filter((v) => Number.isFinite(v) && v > 0 && v < 360 && v % p === 0);
            b.precision = p;
            if (!b.angles.length) {
              issues.push('角度锁「' + b.title + '」缺少合法 angles,已降级为检查');
              b.action = 'inspect';
            }
          } else if (b.action === 'morse') {
            if (!/^[.\-/]{1,24}$/.test(b.code)) {
              issues.push('摩斯锁「' + b.title + '」缺少合法 code,已降级为检查');
              b.action = 'inspect';
            }
          }
          if (['password', 'angle', 'morse'].includes(b.action)) seen[b.action]++;
        });
        /* v5 稳定收敛:某产物步被过滤后,引用它的 result:<id> 悬空——迭代剔除直到不再变化 */
        for (;;) {
          const live = new Set(
            sBeats
              .filter((b) => b.action === 'combine' || b.action === 'sequence')
              .map((b) => b.id),
          );
          let changed = false;
          sBeats.forEach((b) => {
            const before = b.uses.length;
            b.uses = b.uses.filter(
              (u) =>
                !String(u).startsWith(RESULT_PREFIX) ||
                live.has(String(u).slice(RESULT_PREFIX.length)) ||
                /* 跨房间产物引用(2026-08-30):本场景内不认得,交给编译后的全局悬空清理兜底 */
                designProducerRaws.has(String(u).slice(RESULT_PREFIX.length)),
            );
            if (b.uses.length !== before) changed = true;
          });
          const kept = sBeats.filter((b) =>
            b.action === 'combine' || b.action === 'sequence'
              ? b.uses.length >= 2
              : b.uses.length >= 1,
          );
          if (kept.length !== sBeats.length) {
            changed = true;
            sBeats = kept;
          }
          if (!changed) break;
        }
        /* requires 修正:本场景引用转全 id;跨场景引用经全局映射解析——终局收束
           (校验器强制 deliver 闭包 ≥2 场景)依赖这些边,不得因场景内 miss 而丢弃。
           2026-08-30 实测:旧实现按本场景 bMap 过滤,跨房间 requires 全部静默剥掉,
           编译后收束闭包塌缩回单场景。解析优先级:本场景全 id > 本场景短 id > 全局映射
           (设计空间 raw id 可能跨场景重名,本地优先)。 */
        const bMap = new Map(sBeats.map((b) => [b.id, b]));
        sBeats.forEach((b) => {
          b.requires = b.requires
            .map((r) => {
              if (bMap.has(r)) return r;
              const local = sBeats.find((x) => x.id === sId + '-' + r);
              if (local) return local.id;
              if (designBeatId.has(r)) return designBeatId.get(r);
              return r;
            })
            .filter((r) => bMap.has(r) || designBeatId.has(String(r)));
        });
        if (sItems.length && sBeats.length) {
          scenes.push({
            id: sId,
            title: label(sc.title) || '场景 ' + (si + 1),
            description: text(sc.description),
            focus: label(sc.focus) || '',
            locked: sc.locked === true,
            itemIds: sItems.map((x) => x.id),
            beatIds: sBeats.map((x) => x.id),
          });
          sceneItems.push(...sItems);
          sceneBeats.push(...sBeats);
        }
      });
      /* requires 断环:按 beats 顺序增量接受边,加边前查 r 是否已沿 requires 可达 b(会成环则丢弃该边) */
      const accReq = new Map(sceneBeats.map((b) => [b.id, []]));
      const reachReq = function (start) {
        const seen = new Set(),
          st = [start];
        while (st.length) {
          const cur = st.pop();
          if (seen.has(cur)) continue;
          seen.add(cur);
          const rs = accReq.get(cur);
          if (rs) st.push(...rs);
        }
        return seen;
      };
      sceneBeats.forEach(function (b) {
        const keep = [];
        (b.requires || []).forEach(function (r) {
          if (r === b.id || !accReq.has(r)) return;
          if (reachReq(r).has(b.id)) {
            issues.push('步骤「' + b.title + '」与前置 ' + r + ' 构成依赖环,已断开');
            return;
          }
          keep.push(r);
        });
        accReq.set(b.id, keep);
        b.requires = keep;
      });
      /* 隐藏守卫 v5.1:被某 beat uses 的隐藏素材,其使用步必须能到达某个 reveals 它的 beat;
         若不可达,优先把显形步注入为该使用步的前置(保住隐藏特性,且不成环才注);
         注入不了才强制可见(防运行时死锁)。不被任何 beat 使用的隐藏素材保持隐藏(显形即奖励)。 */
      const revealedBy = {};
      sceneBeats.forEach((b) =>
        (b.reveals || []).forEach((id) => {
          revealedBy[id] = revealedBy[id] || [];
          revealedBy[id].push(b.id);
        }),
      );
      sceneItems.forEach((it) => {
        if (!it.hidden) return;
        const usedIn = sceneBeats.filter((b) => (b.uses || []).includes(it.id));
        if (!usedIn.length) return;
        const revs = revealedBy[it.id] || [];
        let allOk = true;
        usedIn.forEach((b) => {
          if (revs.some((rid) => rid !== b.id && beatAncestor(sceneBeats, rid, b.id))) return;
          const rid = revs.find((r) => r !== b.id && accReq.has(r) && !reachReq(b.id).has(r));
          if (rid) {
            b.requires.push(rid);
            accReq.set(b.id, b.requires.slice());
            issues.push('显形顺序修正:「' + it.title + '」的使用步骤已补前置 ' + rid);
          } else allOk = false;
        });
        if (!allOk) {
          it.hidden = false;
          issues.push('素材 ' + it.title + ' 被隐藏但无祖先显形路径,已改为初始可见');
        }
      });
      /* result 守卫:result:<beatId> 只能指向同场景的 combine/sequence beat,且引用它的 beat 必须在其后(由 requires 或顺序保证)——编译期不判环,运行时 beatReady 门控 */
      /* 房间全亮(2026-08-30 需求方反馈):旧编译器把「后一场景第一 beat requires
         前一场景最后 beat」硬注入,房间 2 开局就是死局,并行结构名存实亡——
         现已删除。房间之间的收束由设计负责:最后房间的推理锁/关键 combine
         用 requires 引用前面房间读线索的步骤(校验器强制 ≥2 场景)。 */
      /* lockedBy 仅在 design 显式写 locked:true 时由前一房间最后一步兜底接线;
         正常设计不允许房间级锁(校验器拒绝),上锁放在容器(hidden 素材)与推理锁上。 */
      for (let i = 1; i < scenes.length; i++) {
        const sc = scenes[i];
        if (sc.locked === true) {
          const prevLast2 = scenes[i - 1].beatIds[scenes[i - 1].beatIds.length - 1];
          sc.lockedBy = prevLast2 || null;
        } else {
          sc.lockedBy = null;
        }
      }
      if (scenes.length >= 1 && sceneItems.length >= 4 && sceneBeats.length >= 3) {
        /* v6:先补 deliver 再查孤儿,顺序很关键——补的 deliver 引用最后一个产物,能把无引用的末位产物救回来 */
        const producersPre = sceneBeats.filter(
          (b) => b.action === 'combine' || b.action === 'sequence',
        );
        if (!sceneBeats.some((b) => b.action === 'deliver')) {
          const finalRef = producersPre.length
            ? RESULT_PREFIX + producersPre[producersPre.length - 1].id
            : sceneBeats[sceneBeats.length - 1].uses[0] || sceneItems[0].id;
          const last = sceneBeats[sceneBeats.length - 1];
          sceneBeats.push({
            id: scenes[scenes.length - 1].id + '-final',
            title: '把最终结果交给出口',
            action: 'deliver',
            uses: [finalRef],
            requires: [last.id],
            reveals: [],
          });
        }
        /* v6:孤儿产物守卫——combine/sequence 的产物必须有"下游":被后续 beat 用 result: 引用,
           或产物目标节点(uses[1]/resultOn)被后续步骤直接使用(原作模式:变形后的物件继续参与解谜),
           或它 requires 了后一个 beat 所依赖的前置链(产物的存在性被引用)。
           全不满足才是真孤儿(变身完没有下文)。致命:整个 scenes 设计作废走重试。 */
        const producerBeats = sceneBeats.filter(
          (b) => b.action === 'combine' || b.action === 'sequence',
        );
        const orphanProducers = [];
        producerBeats.forEach((pb) => {
          if (
            sceneBeats.some(
              (b) =>
                b.id !== pb.id && (b.uses || []).some((u) => String(u) === RESULT_PREFIX + pb.id),
            )
          )
            return;
          /* resultOn 显式指定:该节点被任何后续 beat 使用即不算孤儿 */
          const targets = new Set(
            [pb.resultOn, pb.uses[pb.uses.length - 1]].filter(Boolean).map(String),
          );
          const consumed = sceneBeats.some(
            (b) => b.id !== pb.id && (b.uses || []).some((u) => targets.has(String(u))),
          );
          /* 兜底语义:只要不是最后一个 beat,后面总还有 beat 在它之后推进(requires 链会经过它),
             真孤儿的定义是"没有任何后续 beat 依赖它的结果或它变身的节点" */
          const hasLaterBeat = sceneBeats[sceneBeats.length - 1].id !== pb.id;
          if (!consumed && !hasLaterBeat) orphanProducers.push(pb.title || pb.id);
        });
        if (orphanProducers.length)
          throw {
            structural: true,
            message:
              '存在孤儿组合产物(' +
              orphanProducers.join('、') +
              ')——每个组合/顺序结果都必须被后续步骤或交付使用。修复方法:在 deliver 的 uses 里写 result:该组合步id 把产物交给出口,或让后续组合/顺序步用 result:该组合步id 引用它继续推进',
          };
        /* v6:推理锁降级守卫——模型给了 password/angle/morse 但参数不合法被降级时,说明结构不过关,不能静默放行 */
        const demoted = issues.filter((msg) => /已降级为检查/.test(msg)).length;
        if (demoted > 0)
          throw {
            structural: true,
            message:
              demoted +
              ' 个推理锁参数不合法(password 缺 expected / angle 缺 angles / morse 缺 code),已降级为检查步骤',
          };
        if (
          sceneBeats.every(
            (b) => b.action !== 'password' && b.action !== 'angle' && b.action !== 'morse',
          )
        )
          issues.push('全关没有任何推理锁(password/angle/morse),解谜深度不足');
        /* 干扰物件计数提示(软校验):0 或多个都提示给 UI 复查 */
        const herrings = sceneItems.filter((it) => it.role === 'red_herring').length;
        if (herrings !== 1) issues.push('干扰物料件为 ' + herrings + ' 个(期望恰好 1 个)');
        /* P67 答案分布铁律(2026-08-31 示例关三审沉淀):锁的答案只许在**别的物件**的 reason 里;
           锁自身/premise/objective/hints 一律零答案(校验不过→打回重写) */
        const narrativeBlobs = [design.premise, design.objective]
          .concat(Array.isArray(design.hints) ? design.hints : [])
          .map(text);
        sceneBeats.forEach(function (b) {
          if (b.action !== 'password' || !b.expected || b.expected.length < 2) return;
          const expected = String(b.expected);
          const lockItem = sceneItems.find(function (it) {
            return (b.uses || []).includes(it.id);
          });
          if (lockItem && (lockItem.reason || '').includes(expected))
            issues.push(
              'P67 答案自泄漏:密码「' + expected + '」出现在锁「' + (lockItem.sceneName || lockItem.id) + '」自己的谜面里',
            );
          narrativeBlobs.forEach(function (blob, bi) {
            if (blob && blob.includes(expected))
              issues.push(
                'P67 答案泄漏:' + expected + ' 出现在' + ['premise', 'objective', 'hints'][bi] + '里',
              );
          });
        });
        return {
          ...draft,
          level: {
            id: 'level-' + Date.now(),
            title: label(design.title) || '收藏关系调查',
            theme: text(design.theme) || '',
            adventureGrammar: text(design.adventureGrammar) || '',
            parallelRooms: true,
            creativeThesis: text(design.creativeThesis) || '',
            recurringMotif: text(design.recurringMotif) || '',
            surpriseTurn: text(design.surpriseTurn) || '无',
            premise:
              text(design.premise) ||
              '房间不会替你解释收藏。你要从素材事实中找出一条可复查的因果链。',
            objective: text(design.objective) || '穿过每个场景,把最终结果交给出口。',
            targetMinutes: Math.max(5, Math.min(20, Number(design.targetMinutes) || 10)),
            selectedItemIds: sceneItems.map((it) => it.id),
            items: sceneItems,
            mechanics: [...new Set(sceneBeats.map((b) => b.action))],
            beats: sceneBeats,
            scenes,
            hints: (Array.isArray(design.hints)
              ? design.hints.map(label)
              : [
                  '先检查场景里的物件。',
                  '组合失败不会破坏任何东西,大胆尝试。',
                  '有些物件要等前置状态变化后才有用。',
                ]
            ).slice(0, 8),
            validation: { valid: true, issues, designSource: 'step-scenes' },
          },
        };
      }
      throw {
        structural: true,
        message:
          'scenes 结构不完整(scenes=' +
          scenes.length +
          ' items=' +
          sceneItems.length +
          ' beats=' +
          sceneBeats.length +
          ')',
      };
    }

    /* --- 兼容:旧的平铺 items/beats 设计 --- */
    if (
      design &&
      Array.isArray(design.items) &&
      design.items.length >= 4 &&
      Array.isArray(design.beats) &&
      design.beats.length >= 3
    ) {
      const issues = [];
      /* 素材:过滤掉不存在的 id */
      const items = design.items
        .filter((it) => it && byId.has(String(it.id)))
        .slice(0, 12)
        .map((it) => {
          const src = byId.get(String(it.id));
          /* v7:保留化身名与 hidden——平铺关卡同样需要原位变身前的化身叙事与显形机制 */
          return {
            id: src.id,
            role: ['clue', 'tool', 'lock', 'transform', 'reward', 'red_herring'].includes(it.role)
              ? it.role
              : 'clue',
            roleLabel: roleLabels[it.role] || '线索',
            title: src.title,
            sceneName: label(it.scene_name || it.sceneName) || src.title,
            reason: text(it.reason) || fact(src),
            hidden: it.hidden === true || it.start_hidden === true,
            auto: it.auto === true,
            arriveText: text(it.arrive_text || it.arriveText).slice(0, 40),
          };
        });
      /* beats:uses 必须指向存在的素材 id;丢弃引用无效 id 的 beat;v6 保留 resultOn/product/consume */
      const validIds = new Set(items.map((it) => it.id));
      let beats = design.beats
        .filter(Boolean)
        .map((b, i) => ({
          id: text(b.id) || 'step-' + (i + 1),
          title: text(b.title) || '步骤 ' + (i + 1),
          action: [
            'inspect',
            'combine',
            'revisit',
            'sequence',
            'deliver',
            'password',
            'angle',
            'morse',
            'knock',
          ].includes(b.action)
            ? b.action
            : 'inspect',
          uses: (Array.isArray(b.uses) ? b.uses : []).map(String).filter((id) => validIds.has(id)),
          requires: (Array.isArray(b.requires) ? b.requires : []).map(String),
          reveals: (Array.isArray(b.reveals) ? b.reveals : []).filter((id) =>
            validIds.has(String(id)),
          ),
          expected: text(b.expected),
          angles: Array.isArray(b.angles) ? b.angles.slice(0, 3) : [],
          precision: Number(b.precision) || 30,
          code: text(b.code),
          labels: Array.isArray(b.labels) ? b.labels.slice() : [],
          colors: Array.isArray(b.colors) ? b.colors.slice() : [],
          resultOn: text(b.resultOn) && validIds.has(text(b.resultOn)) ? text(b.resultOn) : '',
          product: text(b.product),
          consume: (Array.isArray(b.consume) ? b.consume : []).filter((id) => validIds.has(id)),
        }))
        .filter((b) =>
          b.action === 'combine' || b.action === 'sequence'
            ? b.uses.length >= 2
            : b.uses.length >= 1,
        );
      /* 修正 requires:丢弃指向不存在 beat 的引用 */
      const beatIds = new Set(beats.map((b) => b.id));
      beats.forEach((b) => {
        b.requires = b.requires.filter((r) => beatIds.has(r));
      });
      /* v5:迭代清洗悬空 result 引用(只保留指向本关 combine/sequence 步的),并补 reveals 字段 */
      for (;;) {
        const flatProducers = new Set(
          beats.filter((b) => b.action === 'combine' || b.action === 'sequence').map((b) => b.id),
        );
        let changed = false;
        beats.forEach((b) => {
          const before = b.uses.length;
          b.uses = b.uses.filter(
            (u) => !String(u).startsWith('result:') || flatProducers.has(String(u).slice(7)),
          );
          if (b.uses.length !== before) changed = true;
        });
        const kept = beats.filter((b) =>
          b.action === 'combine' || b.action === 'sequence'
            ? b.uses.length >= 2
            : b.uses.length >= 1,
        );
        if (kept.length !== beats.length) {
          changed = true;
          beats = kept;
        }
        if (!changed) break;
      }
      beats.forEach((b) => {
        if (!Array.isArray(b.reveals)) b.reveals = [];
      });
      /* v6:推理锁参数清洗(password/angle/morse),降级计入 issues */
      const seenLock = { password: 0, angle: 0, morse: 0 };
      beats.forEach(function (b) {
        if (!['password', 'angle', 'morse'].includes(b.action)) return;
        if (seenLock[b.action] >= { password: 2, angle: 2, morse: 1 }[b.action]) {
          issues.push('机关「' + b.title + '」超出配额,已降级为检查');
          b.action = 'inspect';
          return;
        }
        if (b.action === 'password') {
          b.expected = String(b.expected || '').replace(/\D/g, '');
          if (!b.expected || b.expected.length > 6) {
            issues.push('密码锁「' + b.title + '」缺少合法 expected,已降级为检查');
            b.action = 'inspect';
          }
        } else if (b.action === 'angle') {
          const p = [10, 15, 30, 45].includes(b.precision) ? b.precision : 30;
          b.angles = b.angles
            .map(Number)
            .filter((v) => Number.isFinite(v) && v > 0 && v < 360 && v % p === 0);
          b.precision = p;
          if (!b.angles.length) {
            issues.push('角度锁「' + b.title + '」缺少合法 angles,已降级为检查');
            b.action = 'inspect';
          }
        } else if (b.action === 'morse') {
          if (!/^[.\-/]{1,24}$/.test(b.code)) {
            issues.push('摩斯锁「' + b.title + '」缺少合法 code,已降级为检查');
            b.action = 'inspect';
          }
        }
        if (['password', 'angle', 'morse'].includes(b.action)) seenLock[b.action]++;
      });
      /* v7.4:降级锁 = 高潮凭空消失('调整海报角度'名存实亡),与 scenes 分支同语义整版打回,
         让设计师把参数修对,而不是静默放行一个没有机关的关卡 */
      const flatDemoted = issues.filter((msg) => /已降级为检查/.test(msg)).length;
      if (flatDemoted > 0)
        throw {
          structural: true,
          message:
            flatDemoted +
            ' 个推理锁参数不合法被降级(password 缺 expected / angle 的 angles 不是 precision 倍数 / morse 缺 code),已整版打回',
        };
      /* 兜底:如果过滤后素材不足 4 或 beats 不足 3,走本地模板 */
      if (items.length >= 4 && beats.length >= 3) {
        /* v7.2 自愈:deliver 未引用任何产物时,改指最后一个组合/顺序步的 result——
           最常见的孤儿形态是"模型交付素材本身而非产物"。节点同时携带原始与产物身份,两种引用等价。 */
        const flatDel = beats.find((b) => b.action === 'deliver');
        const flatLastProd = beats
          .filter((b) => b.action === 'combine' || b.action === 'sequence')
          .pop();
        if (
          flatDel &&
          flatLastProd &&
          !(flatDel.uses || []).some((u) => String(u).startsWith('result:'))
        ) {
          flatDel.uses = ['result:' + flatLastProd.id];
          issues.push('自动修复:交付步已改用 result:' + flatLastProd.id + '(最终产物)');
        }
        /* v6 孤儿产物守卫·v7.2 语义对齐 scenes 分支:被后续 result: 引用 / 产物节点(uses[末位]或 resultOn)被继续使用 /
           是最后一个 beat,三者满足其一即非孤儿——"变形后的物件继续参与解谜"是 P23 认可的合法链 */
        const flatProducers = beats.filter(
          (b) => b.action === 'combine' || b.action === 'sequence',
        );
        const flatOrphan = [];
        flatProducers.forEach(function (pb) {
          if (
            beats.some(
              (b) => b.id !== pb.id && (b.uses || []).some((u) => String(u) === 'result:' + pb.id),
            )
          )
            return;
          const targets = new Set(
            [pb.resultOn, (pb.uses || [])[(pb.uses || []).length - 1]].filter(Boolean).map(String),
          );
          if (
            beats.some((b) => b.id !== pb.id && (b.uses || []).some((u) => targets.has(String(u))))
          )
            return;
          if (beats[beats.length - 1].id === pb.id) return;
          flatOrphan.push(pb.title || pb.id);
        });
        if (flatOrphan.length && !design.mechanics)
          throw {
            structural: true,
            message:
              '存在孤儿组合产物(' +
              flatOrphan.join('、') +
              ')——每个组合/顺序结果都必须被后续步骤或交付使用。修复方法:在 deliver 的 uses 里写 result:该组合步id 把产物交给出口,或让后续组合/顺序步用 result:该组合步id 引用它继续推进',
          };
        /* 补一个 deliver 结尾(如果没有) */
        if (!beats.some((b) => b.action === 'deliver')) {
          const last = beats[beats.length - 1];
          beats.push({
            id: 'final-deliver',
            title: '把最终结果交给出口',
            action: 'deliver',
            uses: [last.uses[0] || items[0].id],
            requires: [last.id],
          });
        }
        if (items.length < 6) issues.push('收藏事实不足 6 条,流程偏短');
        return {
          ...draft,
          level: {
            id: 'level-' + Date.now(),
            title: label(design.title) || '收藏关系调查',
            theme: text(design.theme) || '',
            creativeThesis: text(design.creativeThesis) || '',
            recurringMotif: text(design.recurringMotif) || '',
            surpriseTurn: text(design.surpriseTurn) || '无',
            premise:
              text(design.premise) ||
              '房间不会替你解释收藏。你要从素材事实中找出一条可复查的因果链。',
            objective: text(design.objective) || '找出素材之间的正确使用顺序,把最终结果交给出口。',
            targetMinutes: Math.max(5, Math.min(20, Number(design.targetMinutes) || 10)),
            selectedItemIds: items.map((it) => it.id),
            items,
            mechanics: (design.mechanics || ['inspect', 'combine']).map(String).slice(0, 6),
            beats,
            hints: (Array.isArray(design.hints)
              ? design.hints.map(label)
              : [
                  '先检查素材上的事实。',
                  '组合失败不会破坏任何东西,大胆尝试。',
                  '有些素材要等前置状态变化后才有用。',
                ]
            ).slice(0, 5),
            validation: { valid: true, issues, designSource: 'step' },
            grounding: { designModel: 'step' },
          },
        };
      }
    }

    /* --- 本地模板兜底(无有效 LLM 设计时) --- */
    const words = (item) =>
      new Set(
        (
          text(item.title) +
          ' ' +
          text(item.domain) +
          ' ' +
          text(item.folder) +
          ' ' +
          (item.topics || []).join(' ')
        )
          .toLowerCase()
          .split(/[^a-z0-9\u4e00-\u9fff]+/)
          .filter((w) => w.length > 1),
      );
    const overlap = (a, b) => {
      const aa = words(a),
        bb = words(b),
        out = [...aa].filter(
          (x) => bb.has(x) && !['com', 'org', 'www', 'http', 'https'].includes(x),
        );
      return out;
    };
    const pairScore = (a, b) => {
      const shared = overlap(a, b),
        sameDomain = a.domain && b.domain && a.domain === b.domain,
        sameFolder = a.folder && b.folder && a.folder === b.folder;
      return (sameDomain ? 5 : 0) + (sameFolder ? 3 : 0) + shared.length;
    };
    const ranked = [...all].sort(
      (a, b) =>
        (b.signal === 'high' ? 2 : b.signal === 'medium' ? 1 : 0) -
        (a.signal === 'high' ? 2 : b.signal === 'medium' ? 1 : 0),
    );
    const sourceItems = ranked.slice(0, Math.min(8, ranked.length));
    let best = null;
    for (let i = 0; i < sourceItems.length; i++)
      for (let j = i + 1; j < sourceItems.length; j++) {
        const score = pairScore(sourceItems[i], sourceItems[j]);
        if (!best || score > best.score)
          best = {
            a: sourceItems[i],
            b: sourceItems[j],
            score,
            shared: overlap(sourceItems[i], sourceItems[j]),
          };
      }
    if (!best) best = { a: sourceItems[0], b: sourceItems[1], score: 0, shared: [] };
    const third =
        sourceItems.find((item) => item.id !== best.a.id && item.id !== best.b.id) ||
        sourceItems[2],
      fourth =
        sourceItems.find((item) => ![best.a.id, best.b.id, third.id].includes(item.id)) ||
        sourceItems[3];
    const relation = best.shared.length
      ? '共同标记：' + best.shared.slice(0, 3).join('、')
      : best.a.domain && best.a.domain === best.b.domain
        ? '同一域名：' + best.a.domain
        : '标题、域名和路径需要交叉比对';
    const chosen = [best.a, best.b, third, fourth].filter(Boolean),
      itemRole = (item, index) => ({
        id: item.id,
        role: index < 2 ? 'clue' : index === 2 ? 'tool' : 'reward',
        roleLabel: index < 2 ? '线索' : index === 2 ? '工具' : '结果',
        title: item.title,
        reason: fact(item),
      });
    const levelItems = chosen.map(itemRole);
    const beats = [
      {
        id: 'inspect-anchor',
        title: '读取第一张卡片的事实',
        action: 'inspect',
        uses: [best.a.id],
        requires: [],
      },
      {
        id: 'inspect-pair',
        title: '交叉检查两条可能相关的收藏',
        action: 'inspect',
        uses: [best.b.id],
        requires: ['inspect-anchor'],
      },
      {
        id: 'combine-pair',
        title: '按共同关系组合两条收藏',
        action: 'combine',
        uses: [best.a.id, best.b.id],
        requires: ['inspect-pair'],
        /* 回退契约(2026-09-01,审查 11.2.9):组合必须有产物,交付引用最终产物而非裸素材 */
        resultOn: best.b.id,
        product: '核对过关系的结果',
      },
      {
        id: 'inspect-third',
        title: '检查组合结果指向的下一条素材',
        action: 'inspect',
        uses: [third.id],
        requires: ['combine-pair'],
      },
      {
        id: 'combine-result',
        title: '把关系结果接到下一条素材',
        action: 'combine',
        uses: [third.id, fourth ? fourth.id : third.id],
        requires: ['inspect-third'],
      },
      {
        id: 'deliver',
        title: '把完成的关系链交给出口',
        action: 'deliver',
        uses: ['result:combine-result'],
        requires: ['combine-result'],
      },
    ];
    const issues = [];
    if (chosen.length < 6) issues.push('当前收藏事实不足 6 条，采用短流程');
    if (best.score === 0)
      issues.push('没有发现明确的共同域名、路径或关键词，第一组关系需要玩家自行核对');
    return {
      ...draft,
      level: {
        id: 'level-' + Date.now(),
        title: label(design?.title) || '收藏关系调查',
        premise: '房间不会替你解释收藏。你要从标题、域名、路径和主题中找出一条可复查的关系链。',
        objective: '找出两条收藏的共同关系，将关系结果接到下一条素材，最后交付完整关系链。',
        targetMinutes: Math.max(8, Math.min(15, Number(design?.targetMinutes) || 10)),
        selectedItemIds: levelItems.map((item) => item.id),
        items: levelItems,
        mechanics: ['inspect', 'combine', 'revisit'],
        beats,
        hints: [
          '先记录卡片上的事实，不要根据氛围猜内容。',
          '共同域名、路径或关键词是组合依据。',
          '组合结果出现后，重新检查下一条素材。',
        ],
        validation: { valid: true, issues, designSource: 'local' },
        grounding: { relation, anchor: fact(best.a), pair: fact(best.b), next: fact(third) },
      },
    };
  }
  function renderLevelPlan(draft) {
    const level = draft && draft.level;
    if (!level) {
      levelPlanEl.hidden = true;
      levelPlanEl.innerHTML = '';
      return;
    }
    levelPlanEl.hidden = false;
    const issue = level.validation.issues.length
      ? '<div class="level-issues">待复查：' +
        level.validation.issues.map(label).join('；') +
        '</div>'
      : '<div class="level-meta">结构检查通过：有起点、组合、回访和出口步骤。</div>';
    levelPlanEl.innerHTML =
      '<strong>关卡编排 / ' +
      label(level.title) +
      '</strong><div class="level-meta">目标时长 ' +
      level.targetMinutes +
      ' 分钟 · 机制：' +
      level.mechanics.join(' / ') +
      '</div><div class="level-beats">' +
      level.beats
        .map(function (b, i) {
          return (
            '<div class="level-beat"><b>' +
            (i + 1) +
            '. ' +
            label(b.title) +
            '</b> · ' +
            label(b.action) +
            '</div>'
          );
        })
        .join('') +
      '</div>' +
      issue;
  }
  function renderCleanReport(analysis) {
    const s = analysis.base.stats,
      provider = analysis.failed
        ? 'Step 错误'
        : analysis.provider === 'step'
          ? 'Step ' + analysis.model
          : 'Step 未运行',
      coverage = s.modelDecisions ? ' · Step 已判断 ' + s.modelDecisions + ' 条' : '',
      rows = analysis.base.records
        .filter(function (item) {
          return item.status === 'review';
        })
        .slice(0, 8);
    $import('cleanReport').innerHTML =
      '<strong>' +
      provider +
      coverage +
      (analysis.failed ? '，未完成' : ' 清洗完成') +
      '</strong><div class="clean-grid"><div class="clean-stat"><b>' +
      s.input +
      '</b><span>输入收藏</span></div><div class="clean-stat"><b>' +
      s.duplicates +
      '</b><span>可合并重复</span></div><div class="clean-stat"><b>' +
      s.review +
      '</b><span>建议复查</span></div><div class="clean-stat"><b>' +
      s.archive +
      '</b><span>已排除低价值</span></div></div><div class="clean-list">' +
      (rows.length
        ? rows
            .map(function (item) {
              return (
                '<div class="clean-row"><span>' +
                label(item.title) +
                '</span><small>' +
                label(item.reason) +
                '</small></div>'
              );
            })
            .join('')
        : '<div class="clean-note">没有明显的低信号入口。</div>') +
      '</div>' +
      (analysis.error
        ? '<div class="clean-note">Step 清洗失败：' + label(analysis.error) + '</div>'
        : '');
    $import('cleanApply').disabled =
      !!analysis.failed || analysis.provider !== 'step' || !analysis.modelResult;
  }
  function dateValue(value) {
    /* 2026-08-28 修复:Chrome JSON 导出的 date_added 是 WebKit 纪元(1601-01-01)微秒,
       旧逻辑误当 Unix 毫秒,时间片/昼夜/排序全错。现在按量级判别纪元,
       并把换算结果限制在 1995-2040 的合理区间,判别失败返回空。 */
    const n = Number(value);
    if (!Number.isFinite(n) || n <= 0) return '';
    let ms;
    if (n >= 1e16) ms = n / 1000 - 11644473600000;
    else if (n >= 1e12) ms = n;
    else if (n >= 1e10) ms = n * 1000 - 11644473600000;
    else ms = n * 1000;
    const d = new Date(ms);
    if (Number.isNaN(d.getTime())) return '';
    const y = d.getFullYear();
    return y >= 1995 && y <= 2040 ? d.toISOString() : '';
  }
  function domainOf(url) {
    try {
      return new URL(url).hostname.replace(/^www\./, '');
    } catch (_) {
      return '';
    }
  }
  /* UTC+8 显示时间(2026-08-31 需求方裁定):书签与关卡的时间戳一律按东八区呈现。
     存储仍用 ISO UTC(排序/版本兼容);把时刻 +8h 后读 ISO,即得东八区挂钟时间,
     与机器时区无关。设计输入(dateAdded)同样转换——谜面引用的日期必须与玩家
     在物件卡上看到的「收藏于」一致(事实锚定铁律)。 */
  function cstIso(v) {
    const d = v instanceof Date ? v : new Date(v);
    return isNaN(d) ? null : new Date(d.getTime() + 8 * 3600 * 1000).toISOString();
  }
  function whenLabel(iso) {
    const m = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/.exec(String(cstIso(iso) || ''));
    return m ? m[1] + ' ' + m[2] : iso ? String(iso).slice(0, 16).replace('T', ' ') : '';
  }
  function stableId(url, index) {
    let h = 2166136261;
    for (const c of url) {
      h ^= c.charCodeAt(0);
      h = Math.imul(h, 16777619);
    }
    return 'bookmark-' + (h >>> 0).toString(36) + '-' + index;
  }
  function normalize(items) {
    const out = [],
      meta = (typeof window !== 'undefined' && window.__bookmarkMeta) || {};
    (items || []).forEach((raw, index) => {
      const url = text(raw.url || raw.href);
      if (!url) return;
      /* 不按 URL 去重:同一页面被收藏多次是行为层证据(遗忘幽灵素材),去重交给 localClean 生成 duplicates */ const title =
        label(raw.title || raw.name) || domainOf(url) || '未命名收藏';
      const cu = canonicalUrl(url),
        metaDesc = meta[cu] || meta[url] || '';
      out.push({
        id: String(raw.id || stableId(url, index)).slice(0, 80),
        title: title.slice(0, 200),
        url: url.slice(0, 2048),
        folder: label(raw.folder || raw.path).slice(0, 300),
        domain: domainOf(url),
        description: label(raw.description || raw.desc || metaDesc || '').slice(0, 300),
        dateAdded: dateValue(raw.dateAdded || raw.add_date || raw.date_added),
        source: 'chrome',
      });
    });
    /* 输入限额(审查 11.3.4):条目数上限 2000,超出截断并告警 */
    if (out.length > 2000) {
      console.warn('[pipeline] 收藏条目 ' + out.length + ' 条超过 2000 上限,已截断');
      out.length = 2000;
    }
    return out;
  }
  function parseHtml(raw) {
    const doc = new DOMParser().parseFromString(raw, 'text/html'),
      items = [];
    const roots = [...doc.querySelectorAll('dl')];
    function walk(dl, path) {
      [...dl.children].forEach((dt) => {
        if (dt.tagName !== 'DT') {
          if (dt.tagName === 'DL') walk(dt, path);
          return;
        }
        const h3 = [...dt.children].find((x) => x.tagName === 'H3'),
          a = [...dt.children].find((x) => x.tagName === 'A'),
          nested = [...dt.children].find((x) => x.tagName === 'DL');
        if (a)
          items.push({
            title: a.textContent,
            url: a.getAttribute('href'),
            folder: path.join(' / '),
            dateAdded: a.getAttribute('add_date'),
          });
        if (nested) walk(nested, h3 ? [...path, text(h3.textContent)] : path);
      });
    }
    if (roots[0]) walk(roots[0], []);
    if (!items.length)
      doc.querySelectorAll('a[href]').forEach((a) =>
        items.push({
          title: a.textContent,
          url: a.getAttribute('href'),
          folder: '',
          dateAdded: a.getAttribute('add_date'),
        }),
      );
    return normalize(items);
  }
  function parseJson(raw) {
    let data;
    try {
      data = typeof raw === 'string' ? JSON.parse(raw) : raw;
    } catch (_) {
      throw new Error('JSON 解析失败，请选择 Chrome Bookmarks 文件。');
    }
    const items = [];
    function walk(node, path) {
      if (!node || typeof node !== 'object') return;
      if (node.type === 'url' || node.url) {
        items.push({
          title: node.name || node.title,
          url: node.url,
          folder: path.join(' / '),
          dateAdded: node.date_added || node.dateAdded,
        });
        return;
      }
      const next = node.name ? path.concat(text(node.name)) : path;
      (node.children || []).forEach((child) => walk(child, next));
      Object.keys(node)
        .filter((k) => k !== 'children' && k !== 'name')
        .forEach((k) => {
          if (node[k] && typeof node[k] === 'object' && !Array.isArray(node[k]))
            walk(node[k], path);
        });
    }
    walk(data, []);
    return normalize(items);
  }
  hints.imported = [
    '草案已经挂回画布，先展开一个收藏分组。',
    '大组会分批显示，先检查眼前的 12 条。',
    '如果某条收藏让你想到另一条，可以拖动它们靠近并观察关系。',
  ];
  function roleFor(item) {
    const hay = (item.title + ' ' + item.domain).toLowerCase();
    let best = 'other',
      score = 0;
    for (const role of ['learn', 'build', 'data', 'inspiration']) {
      const value = roleWords[role]
        .split(' ')
        .reduce((n, w) => n + (w && hay.includes(w.toLowerCase()) ? 1 : 0), 0);
      if (value > score) {
        best = role;
        score = value;
      }
    }
    return best;
  }
  function groupName(item, domainCounts) {
    const folder = label(item.folder).split(' / ').filter(Boolean).pop() || '';
    if (folder && !genericFolders.has(folder.toLowerCase())) return folder;
    const role = roleFor(item);
    if (role !== 'other') return '推断 · ' + roleLabels[role];
    if (item.domain && domainCounts[item.domain] >= 3) return '站点 · ' + item.domain;
    return '推断 · 其他';
  }
  function dominantRole(items) {
    const counts = { learn: 0, build: 0, data: 0, inspiration: 0, other: 0 };
    items.forEach((item) => counts[roleFor(item)]++);
    return Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0] || 'other';
  }
  function buildDraft(items) {
    const domainCounts = {};
    items.forEach((item) => {
      if (item.domain) domainCounts[item.domain] = (domainCounts[item.domain] || 0) + 1;
    });
    const groupsMap = new Map();
    items.forEach((item) => {
      const name = groupName(item, domainCounts);
      if (!groupsMap.has(name))
        groupsMap.set(name, { id: 'group-' + groupsMap.size, name, items: [], role: 'other' });
      groupsMap.get(name).items.push(item);
    });
    const groups = [...groupsMap.values()];
    groups.forEach((group) => {
      group.role = dominantRole(group.items);
    });
    groups.sort((a, b) => b.items.length - a.items.length);
    const relations = [];
    for (let i = 0; i < groups.length; i++)
      for (let j = i + 1; j < groups.length; j++) {
        const a = groups[i],
          b = groups[j],
          domains = new Set(a.items.map((x) => x.domain).filter(Boolean)),
          shared = b.items.some((x) => domains.has(x.domain));
        const words = new Set(
          a.items.flatMap((x) =>
            x.title
              .toLowerCase()
              .split(/[^a-z0-9\\u4e00-\\u9fff]+/)
              .filter((w) => w.length > 2),
          ),
        );
        const overlap = b.items.some((x) =>
          x.title
            .toLowerCase()
            .split(/[^a-z0-9\\u4e00-\\u9fff]+/)
            .some((w) => words.has(w)),
        );
        if (shared || overlap)
          relations.push({
            from: a.id,
            to: b.id,
            label: shared ? '同一站点 / 可能互相引用' : '标题词重叠 / 值得复查',
            confidence: shared ? 'medium' : 'low',
          });
      }
    return {
      items,
      groups,
      relations: relations.slice(0, 10),
      puzzles: [
        { type: 'observe', label: '先展开一个收藏分组' },
        { type: 'combine', label: '尝试把一组可能相关的收藏放在一起' },
        { type: 'revisit', label: '状态改变后重新检查旧分组' },
      ],
      createdAt: new Date().toISOString(),
    };
  }
  function renderDraft(draft) {
    $import('importSummary').textContent =
      `已读取 ${draft.items.length} 条收藏，整理为 ${draft.groups.length} 组，发现 ${draft.relations.length} 条可能关系。`;
    $import('importGroups').innerHTML = draft.groups.length
      ? draft.groups
          .map(
            (g) =>
              `<div class="import-group"><strong>${g.name}</strong><span>${g.items.length} 条 · ${roleLabels[g.role] || roleLabels.other}</span></div>`,
          )
          .join('')
      : '<div class="import-empty">没有可用的网页收藏。</div>';
    $import('importRelations').innerHTML = draft.relations.length
      ? '<strong>关系建议 / 仅供复查</strong><br>' +
        draft.relations
          .map((r) => {
            const a = draft.groups.find((g) => g.id === r.from),
              b = draft.groups.find((g) => g.id === r.to);
            return `${a?.name || r.from} ↔ ${b?.name || r.to}：${r.label}`;
          })
          .join('<br>')
      : '<strong>关系建议</strong><br>当前样本还没有明显的交叉关系，可以在画布上自行寻找。';
    renderLevelPlan(draft);
    $import('importGenerate').disabled = !draft.items.length || !draft.level;
  }
  function hydrateImportedDraft() {
    const raw = localStorage.getItem('favorite-room-draft');
    if (!raw) return;
    let draft;
    try {
      draft = JSON.parse(raw);
    } catch (_) {
      return;
    }
    if (!draft?.items?.length) return;
    const room = {
      id: 'imported-room',
      kind: 'zone imported-zone',
      name: '我的收藏草案',
      hint: `${draft.items.length} 条收藏 / ${draft.groups.length} 组`,
      x: 45,
      y: 87,
      parent: 'root',
      hidden: true,
      startHidden: false,
      spawned: true,
      detail: '由你的浏览器收藏生成的可探索草案。分组与关系都只是建议。',
    };
    const nodes = [room];
    draft.groups.forEach((g, gi) => {
      const gid = 'imported-' + g.id;
      nodes.push({
        id: gid,
        kind: 'zone imported-group',
        name: g.name,
        hint: `${g.items.length} 条 / ${roleLabels[g.role] || roleLabels.other}`,
        x: room.x - 18 + (gi % 3) * 18,
        y: room.y - 21 - Math.floor(gi / 3) * 16,
        parent: room.id,
        hidden: true,
        startHidden: false,
        spawned: true,
        detail: '这一组由收藏夹路径或域名归并而来。展开后逐条检查。',
      });
      g.items.forEach((item, ii) =>
        nodes.push({
          id: 'imported-item-' + item.id,
          kind: 'collectible imported-item',
          name: item.title,
          hint: item.domain || item.url,
          parent: gid,
          x: room.x - 18 + (gi % 3) * 18 + (ii % 2) * 10,
          y: room.y - 6 - Math.floor(ii / 2) * 12 - Math.floor(gi / 3) * 16,
          hidden: true,
          startHidden: false,
          spawned: true,
          url: item.url,
          detail: `${item.title}\n${item.url}\n分组：${g.name}\n这是关卡素材，不会自动改变主谜题。关卡编译器会把它转成线索、工具、锁或状态转换。`,
        }),
      );
    });
    state.nodes.push(...nodes);
  }
  function revealImportedBatch(group) {
    const items = state.nodes.filter((n) => n.importedItem && n.parent === group.id),
      start = group.importedOffset || 0,
      end = Math.min(items.length, start + (group.batchSize || 12));
    /* 槽位已由 roomLayoutBoard 在 hydrate 时定死;批次只翻显隐,不再改坐标
       (旧实现每批 index 从 0 重算,第 2+ 批与第 1 批坐标完全相同、直接叠死) */
    items.slice(start, end).forEach((item) => {
      item.hidden = false;
      item.spawned = true;
    });
    group.importedOffset = end;
    const more = state.nodes.find((n) => n.importedMore && n.groupId === group.id);
    if (more) {
      more.hidden = end >= items.length;
      more.hint =
        end < items.length
          ? '已显示 ' + end + ' / ' + items.length + '，继续搜索'
          : '这一组已经检查完';
    }
    action();
    update();
    roomRender();
  }
  hydrateImportedDraft = function () {
    const raw = localStorage.getItem('favorite-room-draft');
    if (!raw) return;
    let draft;
    try {
      draft = JSON.parse(raw);
    } catch (_) {
      return;
    }
    if (!draft?.items?.length) return;
    const room = {
      id: 'imported-room',
      kind: 'zone imported-zone',
      name: '我的收藏草案',
      hint: draft.items.length + ' 条收藏 / ' + (draft.groups || []).length + ' 组',
      x: 45,
      y: 87,
      parent: 'root',
      hidden: true,
      startHidden: false,
      spawned: true,
      importedRoom: true,
      detail: '由你的浏览器收藏生成的可探索草案。分组与关系都只是建议。',
    };
    const nodes = [room],
      batchSize = 12;
    (draft.groups || []).forEach((g, gi) => {
      const gid = 'imported-' + g.id,
        gx = 6 + (gi % 4) * 22,
        gy = 12 + Math.floor(gi / 4) * 15;
      nodes.push({
        id: gid,
        kind: 'zone imported-group',
        name: g.name,
        hint: g.items.length + ' 条 / ' + (roleLabels[g.role] || roleLabels.other),
        x: gx,
        y: gy,
        parent: room.id,
        hidden: true,
        startHidden: false,
        spawned: true,
        importedGroup: true,
        importedOffset: 0,
        batchSize,
        detail: '这一组由收藏夹路径、域名或标题主题归并而来。先检查一小批，再决定是否继续搜索。',
      });
      g.items.forEach((item) =>
        nodes.push({
          id: 'imported-item-' + item.id,
          kind: 'collectible imported-item',
          name: item.title,
          hint: item.domain || item.url,
          parent: gid,
          x: gx,
          y: gy,
          hidden: true,
          startHidden: true,
          spawned: true,
          importedItem: true,
          url: item.url,
          detail:
            item.title +
            '\\n' +
            item.url +
            '\\n分组：' +
            g.name +
            '\\n这是关卡素材，不会自动改变主谜题。关卡编译器会把它转成线索、工具、锁或状态转换。',
        }),
      );
      nodes.push({
        id: 'imported-more-' + g.id,
        kind: 'action imported-more',
        name: '继续搜索这一组',
        hint: '先展开分组查看前 ' + batchSize + ' 条',
        action: 'import-more',
        groupId: gid,
        parent: gid,
        x: gx + 13,
        y: gy + 14,
        hidden: true,
        startHidden: true,
        spawned: true,
        importedMore: true,
      });
    });
    state.nodes.push(...nodes);
    /* 空间分区摆位(2026-08-29):分组与物件槽位一次定死,
       “继续搜索”只翻显隐——跨批坐标重叠在此修掉 */
    if (typeof roomLayoutBoard === 'function') roomLayoutBoard('imported-room');
  };
  if (typeof roomClone === 'function') {
    const oldRoomClone = roomClone;
    roomClone = function () {
      oldRoomClone();
      hydrateImportedDraft();
    };
  }
  if (typeof roomHandle === 'function') {
    const oldRoomHandle = roomHandle;
    roomHandle = function (n) {
      oldRoomHandle(n);
      const imported = get('imported-room');
      if (n?.id === 'root' && imported && !get('shelf')?.hidden) {
        imported.hidden = false;
        update();
        roomRender();
      }
      if (n?.importedGroup) revealImportedBatch(n);
      if (n?.importedMore) {
        const group = get(n.groupId);
        if (group) revealImportedBatch(group);
      }
      if (n?.importedRoom) {
        frontier('imported');
        $('objective').innerHTML =
          '目标：展开“我的收藏草案”，先检查一组收藏<br><span>每组首次只显示一小批，可以继续搜索。</span>';
      }
      if (n?.importedGroup) {
        frontier('imported');
        $('objective').innerHTML =
          '目标：检查这一组中的收藏，寻找值得重新使用的页面<br><span>继续搜索会显示下一批。</span>';
      }
    };
  }
  $import('importClean').onclick = () => {
    if (!currentDraft) return;
    cleanModal.classList.remove('hidden');
    $import('cleanReport').textContent = '点击“运行清洗”开始分析。';
  };
  $import('cleanClose').onclick = () => cleanModal.classList.add('hidden');
  cleanModal.addEventListener('click', function (e) {
    if (e.target === cleanModal) cleanModal.classList.add('hidden');
  });
  $import('cleanRun').onclick = async () => {
    if (!currentDraft) return;
    const base = localClean(currentDraft.items);
    $import('cleanRun').disabled = true;
    $import('cleanRun').textContent = '分析中…';
    let analysis = {
      base: base,
      provider: 'step',
      model: '',
      modelResult: null,
      error: '',
      failed: false,
    };
    try {
      const remote = await callStep(base.records);
      analysis.model = remote.model;
      analysis.modelResult = remote.parsed;
      analysis.base = applyModelResult(base, remote.parsed);
    } catch (err) {
      analysis.error = err.message || 'Step 调用失败';
      analysis.failed = true;
    }
    cleanState.analysis = analysis;
    cleanState.provider = analysis.failed ? null : 'step';
    renderCleanReport(analysis);
    $import('cleanRun').disabled = false;
    $import('cleanRun').textContent = '重新运行';
  };
  function launchDraft(draft, message) {
    currentDraft = draft;
    renderDraft(currentDraft);
    localStorage.setItem('favorite-room-draft', JSON.stringify(currentDraft));
    importModal.classList.add('hidden');
    cleanModal.classList.add('hidden');
    roomReset();
    const root = get('root');
    if (root && typeof roomHandle === 'function') roomHandle(root);
    const imported = get('imported-room');
    if (imported) {
      imported.hidden = false;
      roomRender();
      drawLinks();
      inspect(imported);
      frontier('imported');
      $('objective').innerHTML =
        '目标：展开“我的收藏草案”，先检查一组收藏<br><span>每组首次只显示一小批，可以继续搜索。</span>';
      log('收藏关卡已经挂回房间。先展开“我的收藏草案”，再选择一个分组。', 'good');
    }
    toast(message);
  }
  $import('cleanApply').onclick = () => {
    const analysis = cleanState.analysis;
    if (!analysis || analysis.failed || analysis.provider !== 'step' || !analysis.modelResult) {
      $import('cleanReport').insertAdjacentHTML(
        'beforeend',
        '<div class="clean-note">没有有效的 Step 清洗结果，不能生成关卡。</div>',
      );
      $import('cleanApply').disabled = true;
      return;
    }
    const draft = compileLevel(draftFromClean(analysis.base, analysis.modelResult));
    draft.cleaningProvider = 'step';
    launchDraft(draft, 'Step 清洗完成，关卡已经生成并挂回画布。点击“我的收藏草案”开始。');
  };
  importButton.onclick = () => {
    importModal.classList.remove('hidden');
    $import('importFile').focus();
  };
  $import('importClose').onclick = () => importModal.classList.add('hidden');
  importModal.addEventListener('click', (e) => {
    if (e.target === importModal) importModal.classList.add('hidden');
  });
  $import('importFile').onchange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const raw = await file.text();
      const items = String(file.name).toLowerCase().endsWith('.json')
        ? parseJson(raw)
        : parseHtml(raw);
      currentDraft = buildDraft(items);
      renderDraft(currentDraft);
      $import('importClean').disabled = false;
    } catch (err) {
      currentDraft = null;
      $import('importSummary').textContent = err.message || '读取失败';
      $import('importGenerate').disabled = true;
      $import('importClean').disabled = true;
    }
  };
  $import('importGenerate').onclick = () => {
    if (!currentDraft) return;
    launchDraft(compileLevel(currentDraft), '收藏草案已经生成并挂回画布。点击“我的收藏草案”开始。');
  };
  function compileFixedRoom(draft, design, theme) {
    const sourceItems = Array.isArray(draft)
        ? draft
        : draft && Array.isArray(draft.items)
          ? draft.items
          : (draft && draft.records) || [],
      all = sourceItems.filter((item) => item.status !== 'archive'),
      wanted = ((draft && draft.controlledIds) || all.map((item) => item.id)).map(String),
      byId = new Map(all.map((item) => [String(item.id), item]));
    /* 机制链=时间链:无论 controlledIds 来自何种路径(含缓存旧档),都按收藏时间升序重排,保证角色指派与"从最早两条开始"的叙事一致 */
    const tv = (item) => {
      const n = Date.parse(item && item.dateAdded);
      return Number.isFinite(n) ? n : Number.MAX_SAFE_INTEGER;
    };
    const ids = wanted
      .map((id) => byId.get(id))
      .filter(Boolean)
      .slice(0, 6)
      .sort((x, y) => tv(x) - tv(y) || String(x.title).localeCompare(String(y.title)))
      .map((item) => item.id);
    if (ids.length < 6) throw new Error('固定密室需要 6 条受控素材,当前只有 ' + ids.length + ' 条');
    const modelItems = [];
    (design && Array.isArray(design.items) ? design.items : []).forEach((item) =>
      modelItems.push(item),
    );
    (design && Array.isArray(design.scenes) ? design.scenes : []).forEach((scene) =>
      (scene.items || []).forEach((item) => modelItems.push(item)),
    );
    const modelById = new Map(
      modelItems.filter((item) => item && item.id != null).map((item) => [String(item.id), item]),
    );
    /* v6:LLM 若给出了完整谜题链(scenes.beats 合计 >=5 且含收尾),走「LLM 链 + 固定场景皮」路径:
       把模型 beats 归一化后直接采用,失败/不完整才退回下面的固定 10 步模板。
       这是修复"生成关卡不可玩"的关键——模板替模型写链,永远写不出匹配 reason 的链条。 */
    const designBeats = (function () {
      const out = [];
      (design && Array.isArray(design.scenes) ? design.scenes : []).forEach(function (sc, si) {
        const sid = 'lsc' + (text(sc.id) || si);
        (Array.isArray(sc.beats) ? sc.beats : []).forEach(function (b, bi) {
          if (!b) return;
          const act = text(b.action) || 'inspect';
          out.push({
            id: sid + '-' + (text(b.id) || bi + 1),
            title: text(b.title),
            action: act,
            uses: (Array.isArray(b.uses) ? b.uses : []).map(String),
            requires: (Array.isArray(b.requires) ? b.requires : []).map(String),
            reveals: (Array.isArray(b.reveals) ? b.reveals : []).map(String),
            expected: text(b.expected),
            angles: Array.isArray(b.angles) ? b.angles.slice(0, 3) : [],
            precision: Number(b.precision) || 30,
            code: text(b.code),
            labels: Array.isArray(b.labels) ? b.labels.slice() : [],
            colors: Array.isArray(b.colors) ? b.colors.slice() : [],
            resultOn: text(b.resultOn),
            product: text(b.product),
            consume: (Array.isArray(b.consume) ? b.consume : []).map(String),
          });
        });
      });
      if (!out.length && design && Array.isArray(design.beats))
        return JSON.parse(JSON.stringify(design.beats));
      return out;
    })();
    let chainIssue = '';
    let _normChain = null;
    try {
      _normChain = (function () {
        if (designBeats.length < 5) {
          chainIssue = 'LLM 谜题链不完整(' + designBeats.length + ' 步<5),退回固定模板';
          return null;
        }
        /* 清洗:uses/requires/result 指向存在的素材或本组 beat */
        const idset = new Set(ids);
        const bids = new Set(designBeats.map((b) => b.id));
        const u2map = {};
        let bs = designBeats.map(function (b) {
          const action = [
            'inspect',
            'combine',
            'revisit',
            'sequence',
            'deliver',
            'password',
            'angle',
            'morse',
          ].includes(b.action)
            ? b.action
            : 'inspect';
          let uses = b.uses.filter((u) => {
            if (idset.has(u)) return true;
            if (String(u).startsWith('result:')) {
              const t = String(u).slice(7);
              if (bids.has(t)) return true;
              /* v6 短 id 容错 */ const hit = [...bids].find((x) => x.endsWith('-' + t));
              if (hit) {
                u2map[String(u)] = 'result:' + hit;
                return true;
              }
            }
            return false;
          });
          return { ...b, action, uses };
        });
        // second pass resolve short-id result refs collected above
        bs.forEach((b) => {
          b.uses = b.uses.map((u) =>
            String(u).startsWith('result:') && u2map[String(u)] ? u2map[String(u)] : u,
          );
        });
        /* requires 指向存在的 beat(短 id 容错) */
        bs.forEach((b) => {
          b.requires = (b.requires || [])
            .map((r) => (bids.has(r) ? r : [...bids].find((x) => x.endsWith('-' + r)) || r))
            .filter((r) => bids.has(r));
        });
        /* 推理锁参数清洗 */
        const seenLock = { password: 0, angle: 0, morse: 0 },
          lockIssues = [];
        bs.forEach(function (b) {
          if (!['password', 'angle', 'morse'].includes(b.action)) return;
          if (seenLock[b.action] >= { password: 2, angle: 2, morse: 1 }[b.action]) {
            lockIssues.push('机关「' + b.title + '」超配额');
            b.action = 'inspect';
            return;
          }
          if (b.action === 'password') {
            b.expected = String(b.expected || '').replace(/\D/g, '');
            if (!b.expected || b.expected.length > 6) {
              lockIssues.push('密码锁「' + b.title + '」缺 expected');
              b.action = 'inspect';
            }
          } else if (b.action === 'angle') {
            const p = [10, 15, 30, 45].includes(b.precision) ? b.precision : 30;
            b.angles = b.angles
              .map(Number)
              .filter((v) => Number.isFinite(v) && v > 0 && v < 360 && v % p === 0);
            b.precision = p;
            if (!b.angles.length) {
              lockIssues.push('角度锁「' + b.title + '」缺 angles');
              b.action = 'inspect';
            }
          } else if (b.action === 'morse') {
            if (!/^[.\-/]{1,24}$/.test(b.code)) {
              lockIssues.push('摩斯锁「' + b.title + '」缺 code');
              b.action = 'inspect';
            }
          }
          if (['password', 'angle', 'morse'].includes(b.action)) seenLock[b.action]++;
        });
        if (lockIssues.length)
          throw { structural: true, message: '推理锁参数不合法: ' + lockIssues.join('; ') };
        /* deliver 校验 */
        if (!bs.some((b) => b.action === 'deliver'))
          throw { structural: true, message: '缺少 deliver 步骤' };
        /* 孤儿产物守卫(与 compileLevel scenes 分支同语义):每个 combine/sequence 产物要有下游 */
        const prodBeats = bs.filter((b) => b.action === 'combine' || b.action === 'sequence');
        for (const pb of prodBeats) {
          const referenced = bs.some(
            (b) => b.id !== pb.id && (b.uses || []).some((u) => String(u) === 'result:' + pb.id),
          );
          const targetUsed = (function () {
            const targets = new Set(
              [pb.resultOn, pb.uses[pb.uses.length - 1]].filter(Boolean).map(String),
            );
            if (!targets.size) return false;
            return bs.some(
              (b) => b.id !== pb.id && (b.uses || []).some((u) => targets.has(String(u))),
            );
          })();
          if (!referenced && !targetUsed && !(pb.id === bs[bs.length - 1].id)) {
            throw {
              structural: true,
              message:
                '存在孤儿产物「' +
                (pb.title || pb.id) +
                '」——组合/顺序结果必须被后续步骤或交付使用。修复方法:在 deliver 的 uses 里写 result:该组合步id,或让后续组合/顺序步用 result:该组合步id 引用它继续推进',
            };
          }
        }
        /* resultOn/product/consume 清洗:必须指向素材或已知 beat */
        bs.forEach((b) => {
          if (
            b.resultOn &&
            !(
              idset.has(b.resultOn) ||
              (b.resultOn.startsWith('result:') && bids.has(b.resultOn.slice(7)))
            )
          ) {
            const rawId = b.resultOn.replace(/^.*-/, '');
            if (idset.has(rawId)) b.resultOn = rawId;
            else delete b.resultOn;
          }
        });
        /* 收尾保障:最后一个非 revisit/inspect beat 若不是 deliver,补一个 deliver 引用最后产物的结果 */
        if (bs[bs.length - 1].action !== 'deliver') {
          const prods = bs.filter(
            (b) =>
              b.action === 'combine' ||
              b.action === 'sequence' ||
              b.action === 'password' ||
              b.action === 'angle' ||
              b.action === 'morse',
          );
          const lastProd = prods[prods.length - 1];
          bs.push({
            id: 'chain-final',
            title: '把完成的结果交给出口',
            action: 'deliver',
            uses: [
              lastProd ? 'result:' + lastProd.id : last(lastProd, bs, bs[bs.length - 1]) || ids[0],
            ],
            requires: [bs[bs.length - 1].id],
          });
        }
        function last(lp, arr, fallback) {
          return null;
        }
        if (bs.length < 5 || bs.length > 14)
          throw { structural: true, message: '步骤数异常(' + bs.length + ')' };
        /* hidden 守卫(复用运行时逻辑思路):被 uses 的隐藏素材必须有显形来源,否则强制可见 */
        /* v6.1 场景归属:运行时靠 scenes[si].beatIds 全部完成来切场景(sceneCleared)。
         LLM 链的 beat id 带 lsc 前缀,固定三场景必须按真实链重排 beatIds,否则场景 1 永远不成立。
         分层依据=beat 操作的素材所在固定场景(入口 a/b/red=0 层,工作台 c/d=1 层,暗格 e=2 层),
         result: 引用递归取产出 beat 的层,再按链序做前缀最大值保证单调不回退。 */
        const tierByItem = new Map();
        ids.forEach(function (id, i) {
          tierByItem.set(String(id), i < 2 || i === 5 ? 0 : i < 4 ? 1 : 2);
        }); /* 与下方 items 场景指派同语义,但此处 items 尚未解构 */
        function tierOfBeat(bm, depth) {
          let t = 0;
          (bm.uses || []).forEach(function (u) {
            t = Math.max(t, tierOfUse(u, depth));
          });
          return t;
        }
        function tierOfUse(u, depth) {
          const s = String(u);
          if (s.startsWith('result:')) {
            if (depth < 8) {
              const pb = bs.find((x) => x.id === s.slice(7));
              if (pb) return tierOfBeat(pb, depth + 1);
            }
            return 0;
          }
          return tierByItem.has(s) ? tierByItem.get(s) : 0;
        }
        let runMax = 0;
        bs.forEach(function (bm) {
          runMax = Math.max(runMax, tierOfBeat(bm, 0));
          bm.__s = Math.min(runMax, 2);
        });
        /* 收尾 beat(deliver/终局)强制落在场景 3(暗格与出口):其交付源是 result:* 产物节点或场景 3 素材,
         引擎对 compiledResult 节点豁免跨场景限制(line ~1303),故安全 */
        if (bs.length) bs[bs.length - 1].__s = 2;
        const gs = [[], [], []];
        bs.forEach(function (bm) {
          gs[bm.__s || 0].push(bm.id);
        });
        for (let gi = 0; gi < 2; gi++) {
          for (let gj = gi + 1; gj < 3 && !gs[gi].length; gj++) {
            while (gs[gj].length && !gs[gi].length) gs[gi].push(gs[gj].shift());
          }
        } /* 每个固定场景至少 1 步 */
        return { chain: bs, groups: gs };
      })();
    } catch (ce) {
      if (ce && ce.structural) {
        chainIssue = ce.message || String(ce);
        try {
          window.__lastChainIssue = chainIssue;
        } catch (_) {}
        _normChain =
          null; /* 退回固定模板:至少可玩;generate 重试回路会读到 __lastChainIssue 决定是否重新设计 */
      } else throw ce;
    }
    /* 两条回退路径(结构性 throw / 链不完整 return null)都必须把问题暴露给重试回路,否则静默降级;
       链被采纳时清空——本字段永远只反映"最近一次编译"的结果,不带上一轮残留 */
    if (_normChain) {
      try {
        window.__lastChainIssue = '';
      } catch (_) {}
    } else if (chainIssue) {
      try {
        window.__lastChainIssue = chainIssue;
      } catch (_) {}
    }
    const fallbackNames = [
      '带日期的索引卡',
      '反复打开的网页终端',
      '折叠的工具纸',
      '密码片段',
      '暗格里的回访条',
      '看似相关的旧收藏',
    ];
    const roles = ['clue', 'clue', 'tool', 'lock', 'transform', 'red_herring'],
      roleLabels = {
        clue: '线索',
        tool: '工具',
        lock: '锁',
        transform: '转化',
        reward: '结果',
        red_herring: '干扰',
      };
    const items = ids.map(function (id, index) {
      const src = byId.get(String(id)),
        model = modelById.get(String(id)) || {};
      return {
        id: src.id,
        role: roles[index],
        roleLabel: roleLabels[roles[index]],
        title: src.title,
        sceneName: label(model.scene_name || model.sceneName) || fallbackNames[index],
        reason:
          text(model.reason) || '从「' + src.title + '」的标题、域名和收藏路径中寻找下一条事实。',
        scene:
          index < 2 || index === 5
            ? 'fixed-scene-1'
            : index < 4
              ? 'fixed-scene-2'
              : 'fixed-scene-3',
        hidden: index === 4,
      };
    });
    const [a, b, c, d, e, red] = items;
    const sn = (s) => {
      const t = String(s || '');
      return t.length > 14 ? t.slice(0, 13) + '…' : t;
    };
    /* 目标文案用素材 sceneName 动态生成——消灭"索引卡/密码片段/刻度盘"这类画面里不存在的幽灵词汇 */
    const tplBeats = [
      {
        id: 'fixed-inspect-a',
        title: '检查「' + sn(a.sceneName) + '」上的事实',
        action: 'inspect',
        uses: [a.id],
        requires: [],
      },
      {
        id: 'fixed-inspect-b',
        title: '检查「' + sn(b.sceneName) + '」的痕迹',
        action: 'inspect',
        uses: [b.id],
        requires: [],
      },
      {
        id: 'fixed-combine-core',
        title: '把「' + sn(a.sceneName) + '」和「' + sn(b.sceneName) + '」拼成入口线索',
        action: 'combine',
        uses: [a.id, b.id],
        resultOn: b.id,
        requires: ['fixed-inspect-a', 'fixed-inspect-b'],
      },
      {
        id: 'fixed-inspect-c',
        title: '回访「' + sn(c.sceneName) + '」',
        action: 'revisit',
        uses: [c.id],
        requires: ['fixed-combine-core'],
      },
      {
        id: 'fixed-inspect-d',
        title: '检查「' + sn(d.sceneName) + '」的记录顺序',
        action: 'inspect',
        uses: [d.id],
        requires: ['fixed-combine-core'],
      },
      {
        id: 'fixed-combine-clue',
        title: '把入口线索接到「' + sn(c.sceneName) + '」',
        action: 'combine',
        uses: ['result:fixed-combine-core', c.id],
        resultOn: c.id,
        requires: ['fixed-combine-core', 'fixed-inspect-c'],
      },
      {
        id: 'fixed-sequence',
        title: '按顺序回应：先点「' + sn(d.sceneName) + '」，再点合成线索',
        action: 'sequence',
        uses: [d.id, c.id],
        resultOn: d.id,
        requires: ['fixed-inspect-d', 'fixed-combine-clue'],
      },
      {
        id: 'fixed-combine-final',
        title: '把两条合成结果拼起来，打开最后的暗格',
        action: 'combine',
        uses: ['result:fixed-sequence', 'result:fixed-combine-clue'],
        resultOn: 'result:fixed-combine-clue',
        requires: ['fixed-sequence'],
        reveals: [e.id],
      },
      {
        id: 'fixed-inspect-e',
        title: '回访刚出现的「' + sn(e.sceneName) + '」',
        action: 'revisit',
        uses: [e.id],
        requires: ['fixed-combine-final'],
      },
      {
        id: 'fixed-deliver',
        title: '把完成的结果交给出口',
        action: 'deliver',
        uses: ['result:fixed-combine-final'],
        requires: ['fixed-inspect-e'],
      },
    ];
    const beats = _normChain
      ? _normChain.chain.map(function (nb) {
          const o = { ...nb };
          delete o.__s;
          return o;
        })
      : tplBeats;
    const chainSource = _normChain ? 'llm-chain-v6' : 'fixed-template-v1';
    /* v6.1:LLM 链时场景 beatIds 必须来自真实链的分桶,固定模板路径保持原值 */
    const g1 = _normChain
      ? _normChain.groups[0]
      : ['fixed-inspect-a', 'fixed-inspect-b', 'fixed-combine-core'];
    const g2 = _normChain
      ? _normChain.groups[1]
      : ['fixed-inspect-c', 'fixed-inspect-d', 'fixed-combine-clue', 'fixed-sequence'];
    const g3 = _normChain
      ? _normChain.groups[2]
      : ['fixed-combine-final', 'fixed-inspect-e', 'fixed-deliver'];
    const scenes = [
      {
        id: 'fixed-scene-1',
        title: '时间片入口',
        description:
          '「' +
          sn(a.sceneName) +
          '」和「' +
          sn(b.sceneName) +
          '」并排放在积灰的检索台上。旁边那条「' +
          sn(red.sceneName) +
          '」看起来也相关，但也许只是诱饵。',
        focus: '检索台',
        itemIds: [a.id, b.id, red.id],
        beatIds: g1,
      },
      {
        id: 'fixed-scene-2',
        title: '回访工作台',
        description:
          '入口线索把你带到另一张工作台。「' +
          sn(c.sceneName) +
          '」和「' +
          sn(d.sceneName) +
          '」分别藏着两条可以并行的线索，最后要合成一个顺序。',
        focus: '工作台',
        itemIds: [c.id, d.id],
        beatIds: g2,
      },
      {
        id: 'fixed-scene-3',
        title: '暗格出口',
        description: '顺序结果打开了最后一个暗格。里面藏着最后一件东西，它决定什么能交给出口。',
        focus: '暗格与出口',
        itemIds: [e.id],
        beatIds: g3,
      },
    ];
    /* 时间轴一览:把推理原料(时刻)真正交到玩家手里,与谜面引用的时刻对齐 */
    const timeline = items
      .map(function (it, i) {
        const src = byId.get(String(it.id)) || {},
          when = whenLabel(src.dateAdded);
        return (
          i +
          1 +
          '. ' +
          (when ? when + ' · ' : '') +
          it.sceneName +
          (it.role === 'red_herring' ? '（干扰）' : '')
        );
      })
      .join('\n');
    return {
      ...draft,
      controlledIds: ids,
      items: ids.map((id) => byId.get(String(id))).filter(Boolean),
      level: {
        id: 'level-' + Date.now(),
        title: label(design && design.title) || '收藏时间片 · 三段回访',
        premise:
          text(design && design.premise) ||
          '六条收藏被固定进一间有三个场景的时间片密室。你需要从两条并行事实线索开始,让组合产物带你回访下一处。',
        objective:
          '按收藏时间顺序推进:先检查最早的两条并拼成入口线索,一路回访到最后的暗格,把最终结果交给出口。',
        targetMinutes: 10,
        selectedItemIds: ids,
        items,
        mechanics: ['inspect', 'combine', 'revisit', 'sequence', 'deliver'],
        beats,
        scenes,
        timeline,
        hints: [
          '先分别检查入口场景的两条事实线索。',
          '收藏时间越早,越可能是链条的起点;组合产物会带你进入下一处。',
          '隐藏物件出现后,回访它和最后的结果。',
        ],
        validation: { valid: true, issues: [], designSource: chainSource },
        grounding: { controlledIds: ids, redHerring: red.id, theme: theme || '未指定' },
      },
    };
  }

  /* v7 范例库:两间已通过玩家验证的完整关卡(监狱复刻/熊曰情报),作为设计师的 few-shot 范例。
   规则教不会的谜题质感(链条接力/机关推导/reason 交叉),范例可以直接示范。 */
  const REF_LEVELS = window.__REF_LEVELS__;

  window.__favoriteRoomPipeline = {
    parse: (raw, name) => {
      /* 输入限额(2026-09-01,审查 11.3.4):解析前拦文件体积;条目数与字段长度在 normalize 拦 */
      if (typeof raw === 'string' && raw.length > 30000000)
        throw new Error('收藏夹文件过大（超过 3000 万字符），请精简后再导入');
      return String(name || 'bookmarks.html')
        .toLowerCase()
        .endsWith('.json')
        ? parseJson(raw)
        : parseHtml(raw);
    },
    async generate(raw, name, theme, report) {
      const items = this.parse(raw, name);
      if (!items.length) throw new Error('收藏文件中没有可用网页');
      const source = localClean(items);
      if (report) report('已读取 ' + source.stats.input + ' 条收藏，准备请求 Step');
      const remote = await callStep(source.records, theme || '');
      if (report) report('Step 清洗完成，正在设计关卡');
      const cleaned = applyModelResult(source, remote.parsed);
      const baseDraft = draftFromClean(cleaned, remote.parsed);
      /* 设计→结构校验,失败把校验问题喂回去重设计一次(自修复回路) */
      let designed, draft;
      for (let attempt = 0; attempt < 2; attempt++) {
        try {
          if (attempt) if (report) report('第一版结构未通过校验，已带反馈重新设计……');
          designed = await callStepLevel(
            baseDraft,
            theme || '',
            attempt ? window.__lastDesignIssues || '' : '',
          );
          if (report) report('Step 关卡设计完成，正在校验结构');
          draft = compileLevel(baseDraft, designed.parsed);
          break;
        } catch (designErr) {
          window.__lastDesignIssues = (designErr && designErr.message) || String(designErr);
          if (attempt) throw designErr;
        }
      }
      const level = draft.level;
      level.cleaningProvider = 'step';
      level.theme = theme || '';
      level.model = remote.model;
      level.designModel = designed.model;
      return {
        items,
        source,
        cleaned,
        modelResult: remote.parsed,
        levelResult: designed.parsed,
        draft,
        model: remote.model,
      };
    },
    compile(cleaned, modelResult, levelResult, theme) {
      if (!levelResult) throw new Error('保存的清洗结果缺少关卡设计结果，请重新生成');
      const draft = draftFromClean(cleaned, modelResult);
      const levelDraft = compileLevel(draft, levelResult);
      levelDraft.level.cleaningProvider = 'step';
      levelDraft.level.theme = theme || levelDraft.level.theme || '';
      return levelDraft;
    },
    compileFixed(cleaned, levelResult, theme) {
      const draft = {
        ...cleaned,
        controlledIds: cleaned.controlledIds || cleaned.records?.slice(0, 6).map((item) => item.id),
      };
      return compileFixedRoom(draft, levelResult, theme);
    },
    /* ===== v7 执行验证:与其用更多规则预判失败,不如让求解器模拟玩家把 beat 图走一遍。
       可计算的不变式交给编译器,"玩家能否通关"交给这里——卡住即不可玩,卡点喂回重设计。
       求解器只验证机制可解性(requires 顺序/物件可用性/reveals/consume/场景门禁),
       不评判谜面质量——那是范例模仿的职责。 ===== */
    solveLevel(level) {
      try {
        const beats = ((level && Array.isArray(level.beats) ? level.beats : []) || []).map((b) => ({
          ...b,
        }));
        if (beats.length < 3) return { solvable: false, detail: 'beats 不足 3 步' };

        /* 共享领域层(2026-09-01):规则归一化交给 compileRules——result 解析、
           reveals、requires 与引擎运行时消费同一份产物,不再各自维护 */
        const rules = compileRules(level);
        const resultOnByNeed = {};
        ['combines', 'sequences', 'inspects', 'delivers', 'passwords', 'angles', 'morses', 'knocks'].forEach(
          function (k) {
            (rules[k] || []).forEach(function (r) {
              if (r.resultOn) resultOnByNeed[r.need] = String(r.resultOn);
            });
          },
        );
        const resolveResult = function (u) {
          let s = String(u),
            d = 0;
          while (s.startsWith('result:') && d < 8) {
            const m = resultOnByNeed[s.slice(7)];
            if (!m) return s.slice(7);
            s = m;
            d++;
          }
          return s;
        };
        /* 容器可达性(2026-08-31):藏在容器里的物件,只要容器本身可见、或容器/物件
            会被某个 beat 显形,玩家开启容器即可取得——求解器按可达处理,
            否则『点开容器』这类无显形 beat 的交互会被误判成永久不可用 */
        const containerById = new Map(
          ((level && Array.isArray(level.containers) ? level.containers : []) || []).map((c) => [
            String(c.id),
            c,
          ]),
        );
        const revealedByBeat = new Set(
          Object.values(rules.reveals)
            .flat()
            .map(String),
        );
        const st = new Map(
          ((level && Array.isArray(level.items) ? level.items : []) || []).map((it) => {
            let shown = !(it && it.hidden === true);
            const cid = it && it.container ? String(it.container) : null;
            const c = cid ? containerById.get(cid) : null;
            if (!shown && c) {
              const containerVisible =
                c.hidden !== true || revealedByBeat.has(String(c.id));
              const itemRevealable = revealedByBeat.has(String(it.id));
              shown = containerVisible || itemRevealable;
            }
            return [String(it.id), { shown, consumed: false }];
          }),
        );
        /* 容器节点也可被 beat 使用(打开工具桌等):可见容器按可用处理 */
        ((level && Array.isArray(level.containers) ? level.containers : []) || []).forEach(
          function (c) {
            const cid = String(c.id || '');
            if (cid && !st.has(cid)) st.set(cid, { shown: !c.hidden, consumed: false });
          },
        );
        const clues = new Set();
        const deliverTotal = beats.filter((b) => b.action === 'deliver').length;
        if (!deliverTotal) return { solvable: false, detail: '缺少 deliver 步骤' };
        const scenes = level && Array.isArray(level.scenes) ? level.scenes : [];
        const hasScenes = scenes.length > 1;
        const sceneOf = new Map();
        scenes.forEach(function (sc, si) {
          (sc.beatIds || []).forEach((bid) => sceneOf.set(bid, si));
        });
        const byId = new Map(beats.map((b) => [String(b.id), b]));
        /* v7.1 静态 lint:机关目标与观察目标重叠 → 玩家点击会被"随时可弹"的机关面板拦截,观察步永远完不成 */
        const isLockAction = (a) => a === 'password' || a === 'angle' || a === 'morse';
        const resolv0 = resolveResult;
        const inspectT = new Set();
        beats.forEach(function (b) {
          if (b.action === 'inspect' || b.action === 'revisit')
            (b.uses || []).forEach(function (u) {
              if (!String(u).startsWith('result:')) inspectT.add(String(u));
            });
        });
        for (const lb of beats) {
          if (!isLockAction(lb.action)) continue;
          const tgt = resolv0((lb.uses || [])[0] || '');
          if (inspectT.has(tgt) || inspectT.has(String((lb.uses || [])[0] || ''))) {
            const victim = beats.find(
              (b2) =>
                (b2.action === 'inspect' || b2.action === 'revisit') &&
                ((b2.uses || []).map(String).includes(tgt) ||
                  (b2.uses || []).map(String).includes(String((lb.uses || [])[0] || ''))),
            );
            return {
              solvable: false,
              detail:
                '机关「' +
                (lb.title || lb.id) +
                '」的目标物件同时被观察步「' +
                ((victim && (victim.title || victim.id)) || '?') +
                '」使用——引擎的机关面板随时可弹,会拦截该物件的一切点击,观察步永远无法完成。把锁装在 result: 组合产物上,或换一件没有被观察过的物件当锁',
            };
          }
        }
        const resolve = resolveResult;
        const free = function (id) {
          const s = st.get(String(id));
          return !!s && s.shown && !s.consumed;
        };
        for (let round = 0; round < 40; round++) {
          let maxScene = 0;
          if (hasScenes) {
            while (
              maxScene < scenes.length - 1 &&
              (scenes[maxScene].beatIds || []).every((bid) => clues.has('beat-' + bid))
            )
              maxScene++;
          }
          let progressed = false;
          for (const b of beats) {
            const bid = String(b.id);
            if (clues.has('beat-' + bid)) continue;
            if (hasScenes && (sceneOf.get(bid) || 0) > maxScene) continue;
            if (!(b.requires || []).every((r) => clues.has('beat-' + r))) continue;
            const uses = (b.uses || []).map(resolve);
            if (!uses.length || !uses.every(free)) continue;
            clues.add('beat-' + bid);
            (b.consume || []).forEach(function (id) {
              const s = st.get(String(id));
              if (s) s.consumed = true;
            });
            (b.reveals || []).forEach(function (id) {
              const s = st.get(String(id));
              if (s) s.shown = true;
            });
            progressed = true;
          }
          if (
            [...clues].filter((c) =>
              beats.some((b) => b.action === 'deliver' && 'beat-' + String(b.id) === c),
            ).length >= deliverTotal
          )
            return { solvable: true, steps: clues.size };
          if (!progressed) break;
        }
        /* 诊断卡点:第一个未完成且前置已齐的 beat,说清为什么走不通 */
        let detail = '未知卡点';
        for (const b of beats) {
          const bid = String(b.id);
          if (clues.has('beat-' + bid)) continue;
          const missing = (b.requires || []).filter((r) => !clues.has('beat-' + r));
          if (missing.length) continue;
          const uses = (b.uses || []).map(resolve);
          const blocked = uses.filter((u) => !free(u));
          if (!uses.length) {
            detail =
              '步骤「' + (b.title || bid) + '」(' + (b.action || '?') + ')没有交互物件(uses 为空)';
            break;
          }
          if (blocked.length) {
            detail =
              '步骤「' +
              (b.title || bid) +
              '」的物件不可用:' +
              blocked
                .map(function (u) {
                  const s = st.get(String(u));
                  return (
                    '「' + u + '」' + (s ? (s.consumed ? '已被消耗' : '仍隐藏未显形') : '不存在')
                  );
                })
                .join('、');
            break;
          }
        }
        return {
          solvable: false,
          detail: detail + '(已完成 ' + clues.size + '/' + beats.length + ' 步)',
        };
      } catch (e) {
        return { solvable: false, detail: '求解器异常:' + String((e && e.message) || e) };
      }
    },
    /* ===== v7 范例模仿设计:与其堆 20 条规则分散注意力,不如给两间已验证的完整关卡当范例。
       设计师模仿三样东西:谜题链写法(result:引用/原位变身/consume)、机关推导方式(对照表+规则写在 reason 里)、
       reason 交叉笔法;输出与范例同构的 flat items+beats,compileLevel 直接编译执行。
       校验只保留可计算的不变式(引用完整性/deliver/锁/空 uses),其余交给 solveLevel 执行验证。 ===== */
    GATE_MANIFEST,
    CLEAN_VERSION,
    compileRules,
    async designWindow(items, theme, windowContext, duplicates, report, repairNote, externalSignal, overrides, materialCount) {
      /* overrides:赛马按路注入供应商配置(endpoint/model/apiKey/thinking/reasoningEffort/
         designTimeout),不传则用默认 step 配置。
         materialCount(2026-08-30):单次使用的素材条数(6-12,默认 6)。条数越多,
         房间数与谜题链越长(8+ 建议 3 房间)。实际采用量 = min(请求量, 可用量),
         下限 6——不足 6 时报错(时间片太薄,撑不起多层结构)。 */
      const eff = Object.assign({}, llmConfig, overrides || {});
      const getEl = (id) => document.getElementById(id),
        configuredEndpoint =
          (overrides && overrides.endpoint) ||
          getEl('cleanEndpoint').value.trim() ||
          eff.endpoint,
        endpoint =
          /api\.stepfun\.com/i.test(configuredEndpoint) || !configuredEndpoint
            ? 'http://127.0.0.1:8128/api/step'
            : configuredEndpoint,
        model = (overrides && overrides.model) || getEl('cleanModel').value.trim() || eff.model,
        key = (overrides && overrides.apiKey) || getEl('cleanApiKey').value.trim() || eff.apiKey;
      if (!key && !/api\/(step|glm)/.test(endpoint))
        throw new Error('该供应商未提供 API Key,无法设计关卡(' + endpoint + ')');  // 本地 /api/step 代理由服务端注入密钥
      const wantN = Math.max(6, Math.min(12, Number(materialCount) || 6));
      const candidates = items.slice(0, wantN).map(function (it) {
        return {
          id: it.id,
          title: it.title,
          domain: it.domain,
          urlPath: (it.urlPath || '').slice(0, 200),
          folder: it.folder || '',
          /* 东八区呈现(2026-08-31):模型引用的收藏日期与玩家看到的「收藏于」同源 */
          dateAdded: cstIso(it.dateAdded) || it.dateAdded || '',
          desc: (it.description || '').slice(0, 300),
        };
      });
      if (candidates.length < 6) throw new Error('时间片内可用素材少于 6 条');
      const N = candidates.length; /* 实际素材量:校验与 prompt 全部以它为准 */
      const dupNote = (duplicates || []).slice(0, 4).map(function (d) {
        return {
          title: d.title || '',
          url: (d.url || '').slice(0, 120),
          dateAdded: d.dateAdded || '',
        };
      });
      const userReq = {
        theme: theme || '', /* P33:默认主题锚定已移除——同一批收藏反复生成不再是同一个机房 */
        timeWindow: windowContext || null,
        repeats: dupNote,
        materials: candidates,
        输出要求: {
          格式: '与参考关卡同构:顶层 level 对象,含 title/premise/objective/targetMinutes/hints/items/beats',
          items:
            '恰好 ' + N + ' 条素材化身,每条 {id,role,scene_name,reason,hidden,digest,sourceFacts};id 原样使用 materials 里的 id;恰好 1 条 role=red_herring,它不进入任何 combine/sequence 的 uses;digest 是这条网页的一句话中文摘要(≤40字:它是什么+关键点,外文内容转述成中文);sourceFacts 是从该素材 desc/标题/路径中原样抄录的事实键值(≤3 个,如 [{"k":"弹幕量","v":"8"}]),值必须能在素材文本里原样找到。另加机关道具 2-5 件(每个房间至少 1 件):{"id":"prop-1","role","scene_name","reason","hidden"}——机关道具是**没有网页背景的纯机构**(转盘锁/火柴/油灯/撬棍/铁柜/抽屉/闸刀),id 一律 prop-1、prop-2…递增;它的 reason 只写自身的物性与状态(「黄铜火柴,只剩三根」「柜门挂着小锁」),禁止携带任何素材事实',
          beats:
            N + '-' + (N + 4) + ' 步,每步 {id,title,action,uses,requires,reveals};combine/sequence 必写 resultOn(产物落在哪件素材上,写素材 id)和 product(变身后叫什么),一次性道具写 consume:[素材id];最后一步是 deliver,恰好 1 个,uses 恰好 1 个;uses 里的 result:<id> 只能引用本次输出中真实存在的 combine/sequence 步骤 id——不许引用 inspect 步、不许编造示例里的 id;requires 与 result: 可跨房间引用(收束另一房间的线索或成品);素材 id 与 reveals 绝不跨房间',
          机关: '至少 1 个 password/angle/morse;答案必须能从更早物件的 reason 推导(对照表/换算规则/顺序依据完整写明),绝不裸密码。password 的 expected 3-6 位数字;angle 的 angles 都是 precision 的倍数;morse 的 code 只含 .-/ 且必须有对照表物件。锁具物件优先用 prop-* 机关道具(密码答案仍由素材化身的 reason 推导,deriveFrom 指向素材)',
          步骤: '每个 beat 的 uses 至少 1 个目标物件(不许写空);uses 只能是素材 id、prop-* 机关道具 id 或 result:前置组合步 id',
        },
      };
      const systemPrompt = [
        '你是收藏夹密室的关卡设计师。给你三间已通过玩家验证的完整关卡数据(参考A:监狱复刻;参考B:熊曰情报;参考C:内容接地示范),和 6 条真实浏览器收藏素材。',
        '模仿参考关卡的三样东西,用新素材设计一间新密室。三间参考关卡本身就是多层结构的范本:主节点(入口)下分 2 个房间(scene),每间房间有自己的容器与道具,所有房间开局同时亮出,两个房间的线索在终局收束汇合;参考C 是**内容接地**的示范——它的 sourceFacts 与谜面事实逐字来自网页描述里的真实读数(播放量/硬币数),你写 digest 和 sourceFacts 时照它做;',
        '0. 房间层级铁律(结构必须遵守):输出 scenes 数组,' +
          (N >= 8
            ? '2-3 个房间——素材有 ' + N + ' 条,建议用 3 间房间分担,每间 3-4 件素材,探索面更宽'
            : '恰好 2 个房间') +
          ';每个房间 = {id,title,description,focus,items,beats}。title 是这个房间的**场所名**(两到六个字,像「放映间」「档案室」「锅炉房」「机房外间」)——禁止罗列家具当房间名(「检索台与磁带座」「XX与XX」都是废名),家具与装置写进 description 和 focus。description 用两句感官描写让玩家"站在那里",focus 是该房间的核心容器或装置(如「上锁的铁柜」「黑屏的解密终端」);禁止给任何房间写 "locked":true——房间门永远不上锁,上锁放在容器与机关上(校验器会拒绝房间级 locked)。每个房间至少 2 件素材、2 个步骤,且至少一步开局就能动手(不依赖另一房间)。空间嵌套是本关的灵魂,每个房间都必须有:每个房间至少 1 件素材 hidden:true,由**本房间**某个非 deliver 步骤的 reveals 显形(像参考A的锯子锁在转盘锁后、电池夹在日记本书页间),显形步的 uses[0](或 combine 的 resultOn)必须是容纳它的容器物件——引擎会把显形的道具生成在容器旁,形成「房间→容器→道具」的空间嵌套;显形出来的东西要立刻进入链条(参考A:锯子显形→马上锯管)。机构与信息分工(2026-08-30 裁定,解决"收藏硬扮机关"的牵强):每个房间至少 1 件 **prop-* 机关道具**——id 以 prop- 开头、没有网页背景的纯机构(转盘锁/火柴/油灯/撬棍/铁柜/抽屉/闸刀);锁具、容器、工具优先用机关道具承担,素材化身只做**信息载体**(笔记/报文/指南/磁带/照片),不再让一条收藏去硬扮一把锁;机关道具的 reason 只写自身物性与状态,禁止携带任何素材事实(校验器会拒绝)。两个房间必须互相成就,玩家必须跑通两个房间才能通关。跨房间引用只有两种合法形式:①requires 引用其他房间读线索步骤的 id;②uses 里用 result: 引用其他房间组合步的产物(把那个房间做好的成品拿到本房间用)。唯一禁止的是把其他房间的素材 id 写进本房间的 items 或 reveals(素材实体只属于一个房间)。照抄这个收束模式:房间2的锁写 {"id":"b7","action":"password","uses":["result:房间1组合步id"],"requires":["房间1读线索步骤的id"],"expected":"…"}——推导规则写在房间1那件物件的 reason 里。谜题结构硬性要求:全关至少 1 个 combine 步(道具组合原位变身);每个房间至少 1 个 hidden 素材、全关 ≥2 处 reveals 显形;至少 1 件物件跨步骤回访(先观察/改造,之后再次被使用——像参考A的电报机:装电池变身,最后还拿它按指纹锁);inspect 步骤不得超过总步数的 60%。',
        '1. 谜题链的写法:观察→发现(容器显形隐藏物,reveals 是空间的钥匙)→组合(原位变身,resultOn 指定产物落在哪件物件上,product 是变身后叫什么)→用 result:步骤id 引用产物继续推进→回访旧物件(它已变身/状态已变,再核一次)→推理锁收束→deliver 交付。链条要像参考A那样层层接力(转盘锁后显形锯子→锯排水管→棍子→勾下钥匙→解开镣铐;日记本里显形电池→装进电报机)。',
        '2. 机关答案的推导方式:参考A的密码 685 = 笔记的摩斯对照表(3 是 ...--,7 是 --...)+日记的生日(3月14日);参考B的 246 = 熊字表+倒序规则。推导依据必须完整写进更早物件的 reason,玩家核对两件物件就能唯一算出答案。绝不允许无推导依据的裸密码/角度/电码。',
        '3. reason 的笔法:印在物件上的谜面,引用其他素材的具体事实(标题词/路径词/日期/域名)制造可验证的交叉;不写设计说明,不复述素材介绍,不写"它知道答案"这类修辞黑话。',
        '4. 手法菜单(任选 2-3 种构成机制族,同一手法全关只用一次):\n① 显影:combine(工具,目标)让目标原位变身露出信息;信息必须被物理遮蔽(油垢/胶带/撕碎),工具在更早步骤可得。\n② 检索多问:同一 lock 物件挂多把 password(全关 password 最多 2 把,引擎按完成顺序逐个弹出);前一份档案的 reason 自然提及下一个检索词,证据链两跳以上。\n③ 敲击:beat 写 action 为 knock、uses 为该物件、count 为 2 到 5(建议 3)——连点 count 次完成;任何文案禁止出现次数与「连敲/连按/多敲」字样(校验器会打回),可发现性只靠物件质感(「空响的底板」);知识物件到来前,物件描述保持惰性。\n④ 主动显形:隐藏素材标 auto:true,且显形它的 beat 写 product 交代因果来源(如检索台变身「嗡嗡作响的检索台」,底板被振动震出)——新物件当场弹出;未标 auto 的维持回访;人物到场用 arrive_text 写到场文案。\n⑤ 顺序扫描:链式 combine(书A,机器)requires 上一步→(书B,机器)→…次序被物理 enforce;机器连续变身写受理进度(「已受理 1/3」),次序依据写在规则物件里。\n⑥ NPC:一个 role=clue 的 auto 素材当角色,reason 直接写台词(含下一步钩子);combine(信物,NPC)=交易,NPC 原位变身+reveals 奖励。\n⑦ 环境线索:场景 description 与物件 desc 里的「闲笔」必须参与推理(落日→房间朝西),与图纸/文件拼合才出答案;纯氛围不接线=浪费字数。\n⑧ 校验题:password 的 expected 来自页面内容本身(简介里的数字/术语),让玩家对照原收藏即可验证。',
        gatePromptSection(),
        '化身名铁律:scene_name 是密室里的实体物件,不是网址或收藏条的复述——禁止"书签栏:XXX""XXX页面"这类写法。看参考关卡怎么命名:『转盘锁』『锯子』『日记本』『解密终端』『铅笔』。素材化身偏**信息载体**:一台老旧检索机、一张打印出来的报文、一盘刻着字样的磁带、一册贴满标签的相簿——名字两到六个字,能一眼看出它是什么器物;机构类的物件(锁具/抽屉/铁柜/火柴/油灯)交给 prop-* 机关道具,不要占素材化身的名额。',
        '其余自由发挥:化身名(scene_name)要具体、可触摸、视觉呼应素材真实内容;premise 贴合素材与时间窗;hints 6-8 条渐进(先观察、再联想、最后行动,绝不直接给答案)。red_herring 化身要有诱惑力但不进任何组合。hidden:true 的素材开局不可见,由**本房间**某个非 deliver 步骤的 reveals 列出后显形(生成在容器旁),之后必须有步骤使用它(reward/干扰型除外);两个房间各藏至少一件。',
        '机关摆放铁律:password/angle/morse 的目标物件,绝不能同时是任何 inspect/revisit 步骤的目标——玩家一点它就会弹出机关面板,观察步永远无法完成。最安全的做法:把锁装在某个 combine 的 result: 产物上(像参考A把摩斯锁装在通电后的电报机上),或装在一件没有任何观察步指向的物件上。',
        'deliver 交付的必须是链条的最终产物:uses 写 result:最后一个组合/顺序步的 id(除非交付的是一件从未被组合过的物件)。每个组合/顺序步的产物都必须被后续步骤用 result: 引用,不许悬空。',
        '事实锚定铁律(最容易违反,写完逐条自检):推理材料只允许来自 materials 的真实字段——标题词、域名、urlPath(路径里的数字串是最佳原料,如 /opus/351262298288053446 可以取位/分段/求和)、文件夹名、收藏日期、网页描述(desc)。desc 是真实网页描述,是最接近页面内容的合法材料——有 desc 的素材优先围绕 desc 做谜面。sourceFacts 只能从该素材的 desc/标题/路径里**原样抄录**(接地检查会验证每个值都真实出现,改写或编造会被整版打回);desc 为空的素材 sourceFacts 留空数组,只准引用标题/域名/路径/日期。严禁虚构页面内容:「附录里有摩斯对照表」「页面写着跳跃高度1.8米」「发布于2016年3月14日」这类字段里不存在的"页面事实"一律禁止——玩家检查物件时引擎只展示真名/域名/路径/日期,虚构立即穿帮。机关答案必须能由玩家从这些真实字段口算导出。',
        '算术自检铁律:每个机关答案写完后,把推导链的每一步算术自己重算一遍(取位从第几位数起、求和是否等于答案),必须唯一且正确——你算错了,玩家会永远卡在正确的推理上却输错密码。推导描述要精确到"第几位到第几位""哪一天的哪部分",不许含糊。',
        '信息密度铁律:每条 reason 最多两句话——第一句说这是什么物件,第二句是谜面。禁止罗列"来源X、路径末尾Y、打印日期Z、归类在W文件夹"这类元数据(玩家检查时引擎自动展示它们)。单个机关的推导链最多用两条线索、一次换算(对照/数位/相加),让玩家三分钟内能走完一步;整关推理难度要像参考B那样直白,不要像考卷。',
        '创作计划铁律(随设计稿一起输出,玩家通关前不可见):输出 JSON 顶层添加三个字段——"creativeThesis"(一句内在命题:这场冒险在暗中讨论什么)、"recurringMotif"(一个贯穿各房间的反复母题:声音/动作/材质/数字)、"surpriseTurn"(至多一个转折:重新解释玩家已做过的某步;没有可信转折就写「无」)。creativeThesis 必须是输出 JSON 的第一个字段,不要遗漏。母题要在至少两个房间的 reason 里埋下回响;惊奇预算=至多一个转折,其余规则保持稳定可学习。',
        '输出 JSON 结构:{title,premise,objective,targetMinutes,theme:"一句主题描述",adventureGrammar:"语法名:一句如何组织",creativeThesis:"…",recurringMotif:"…",surpriseTurn:"…",mechanics:[字符串],hints:[恰好6条],scenes:[{id,title,description,focus,items:[{id,role,scene_name,reason,hidden,digest,sourceFacts}],beats:[{id,title,action,uses,requires,reveals,expected,angles,precision,code,product,resultOn,consume}]}]}。硬性约束:' + N + ' 条素材全部分配进场景且每条恰好一次(每条都写成素材化身);机关道具 prop-* 另计,每个房间至少 1 件、全关 2-5 件;uses/reveals/result: 只引用本场景内的物件;requires 可引用其他房间的步骤 id(终局收束必须用到);全局恰好 1 个 deliver 且必须是最后一个房间的最后一步;每个房间至少 2 件素材 2 步;组合步产物不许悬空(被后步 result: 引用或交付)。只使用 materials 里的 id——唯一例外是 prop-* 机关道具(无网页背景的纯机构,其 reason 禁止引用素材事实);不编造素材之外的事实。输出严格 JSON,不要 Markdown。主题由你决定——收藏标签页常常是无逻辑的拼贴,所以主题允许跳脱、意识流:从素材的内容、情绪或收藏行为本身的氛围(深夜的猎奇、拖延、好奇心、收藏癖)自由联想,写实或超现实皆可(「凌晨三点的自助洗衣店与会说话的烘干机」「台风眼的航海档案馆」)。' +
            label((windowContext && windowContext.mood) || '未指定') +
            '的时间窗情绪可以作为联想起点,但不必被素材的"主题类别"束缚——把不相关的收藏解释成同一个梦境的碎片,反而是好设计。两条底线:①主题一旦定下就要自洽——所有房间、化身、机关严格长在它上面,不许拼贴感泄漏进关卡内部;②主题要具体到能一眼想象出房间的样子,写进输出的 theme 字段(一句话)。' +
            ((windowContext && windowContext.themeHint)
              ? '用户倾向:' + label(windowContext.themeHint) + '——同样只作联想起点。'
              : '') +
            '(主题只影响叙事包装与机关形态,不改变素材事实)。' +
            (theme
              ? '【注意:用户已指定主题 ' + label(theme) + '——以它为准,忽略上面的自动推断。】'
              : ''),
        '输出骨架示例(仅为格式锚点,素材内容必须来自 materials;prop-* 是无网页背景的机关道具):\n{"title":"…","premise":"…","objective":"…","targetMinutes":12,"theme":"…","creativeThesis":"…","recurringMotif":"…","surpriseTurn":"…","adventureGrammar":"变形:一句如何组织","mechanics":["…"],"hints":["…"],"scenes":[\n  {"id":"room-1","title":"外间","description":"两句感官描写","focus":"上锁的铁柜",\n   "items":[{"id":"prop-1","role":"tool","scene_name":"上锁的铁柜","reason":"柜门挂着小锁,锁孔内缘有新鲜的划痕"},{"id":"素材id","role":"clue","scene_name":"化身名","reason":"关键信息前置:日期/数字/标题词写在开头","digest":"这个网页是什么,一句话中文","sourceFacts":[{"k":"弹幕量","v":"8"},{"k":"点赞数","v":"53"}]},{"id":"素材id","role":"tool","scene_name":"…","reason":"…","hidden":true,"digest":"…","sourceFacts":[]}],\n   "beats":[{"id":"b1","title":"撬开铁柜","action":"combine","uses":["素材id(撬棍类化身)","prop-1"],"resultOn":"prop-1","product":"打开的铁柜","reveals":["hidden素材id"]}(机关步可加 "deriveFrom":["推导所用素材id"]),{"id":"b2","title":"…","action":"combine","uses":["素材id","素材id"],"resultOn":"素材id","product":"…"}]},\n  {"id":"room-2","title":"里间","description":"…","focus":"…","items":[…,{"id":"prop-2","role":"lock","scene_name":"黄铜密码闸机","reason":"三位数字盘,盘面只有经年的锈"},{"id":"素材id","role":"reward","scene_name":"…","reason":"…","hidden":true,"digest":"…","sourceFacts":[]}],"beats":[…,{"id":"bK","title":"…","action":"inspect","uses":["本房间容器(prop-* 或化身)id"],"reveals":["本房间hidden素材id"]},{"id":"bL","title":"开锁","action":"password","uses":["prop-2"],"requires":["房间1读线索步骤id"],"deriveFrom":["素材id"](跨房间收束:锁是 prop 机关,但密码答案从素材化身的 reason 推导)},{"id":"bN","title":"交给出口","action":"deliver","uses":["result:前一个组合步id"]}]}]}',
        '显形与变身铁律:凡 reveals 显形或 combine 变身,产物的谜面必须写明多出了什么信息或物品,且该信息/物品必须被后续步骤的推导或组合引用——像参考A开转盘锁显形锯子后,锯子立刻进入链条。绝不允许「擦出字迹却不写擦出了什么」的装饰步,也不允许谜面指向一个从未被显形步骤交代的线索。',
        '推导规则措辞铁律:机关规则引用素材字段时,必须指向真实可见的字段并直呼其名(「标题中的『第二轮』」「收藏日期 8 月 24 日」「路径里的数字 9」);引擎会在物件弹窗顶部常驻展示真名·域名·收藏日期·路径,谜面措辞必须与展示一致。禁止自造概念(如「素材轮数」)。',
        '关键信息前置铁律:reason 里承担解谜的日期/数字/标题词写在谜面开头一两句,不要堆在结尾——玩家第一眼要能看到谜面所引用的事实。',
        '冒险语法铁律(隐藏创作结构,玩家不可见):从八种语法中选一种组织本次冒险——变形(每件收藏使用后变成另一件,最终形成完整物品)/朝圣(场景跳跃但各留同一种符号)/审判(收藏分别成为证人、证词、伪证)/失忆(完成一步后旧物件的意义改变)/官僚迷宫(盖章归档退件构成谜题动作)/梦境接力(上一场景的动作成为下一场景的规则)/错误宇宙(无关收藏被误认为同一项目)/无中心选集(局部两两成对,结局才暴露共同轨迹)。写进输出的 adventureGrammar 字段(格式「语法名:一句如何组织」);语法对玩家隐藏,只影响房间与谜面的隐性呼应。',
        '逐项来源铁律(可追溯):每个推理锁(password/angle/morse)必须带 deriveFrom:[素材id]——列出推导答案所用的素材;引擎会在冒险回执里展示「答案的推导来自哪些收藏」。deriveFrom 里的素材必须是真实素材 id,且其中至少一个的 reason 包含推导规则。',
      ].join('\n');
      const attempt = async function (prevErrorNote) {
        /* 多路赛马(2026-08-28):externalSignal 被中止 = 别的路已产出可解谜题,本路立即止损,
           不再消耗配额;不匹配重试分支的关键词,保证直接致命退出本路。 */
        if (externalSignal && externalSignal.aborted)
          throw { noretry: true, message: '本路已被取消(另一路率先通过)' };
        /* 超时定时器必须覆盖到读流结束:fetch 只等响应头,body 可能中途停滞 */
        const controller = new AbortController(),
          /* 2026-08-28 实测:scenes 设计经 advisor 单次可达 ~515s,240s 必超时(设计流中断循环)。
             默认提到 600s;designTimeout 可配。 */
          timer = setTimeout(() => controller.abort(), eff.designTimeout || 600000);
        if (externalSignal)
          externalSignal.addEventListener('abort', () => controller.abort(), { once: true });
        try {
          let response;
          try {
            const _repair = repairNote
              ? '【上一版未通过验证】' + repairNote + '\n请严格修正以上问题后重新输出完整设计。'
              : '';
            const userContent =
              JSON.stringify(userReq) +
              '\n\n【参考关卡A·监狱复刻(机关链示范)】\n' +
              JSON.stringify(REF_LEVELS[0]) +
              '\n\n【参考关卡B·熊曰情报(机关链示范)】\n' +
              JSON.stringify(REF_LEVELS[1]) +
              '\n\n【参考关卡C·内容接地示范(digest/sourceFacts 照它写)】\n' +
              JSON.stringify(REF_LEVELS[2]) +
              (_repair ? '\n\n' + _repair : '') +
              (prevErrorNote
                ? '\n\n【上次尝试失败】' + prevErrorNote + '\n请修正后重新输出完整 JSON。'
                : '');
            response = await fetch(endpoint, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + key },
              body: JSON.stringify({
                model,
                messages: [
                  { role: 'system', content: systemPrompt },
                  { role: 'user', content: userContent },
                ],
                temperature: 0.35,
                thinking: eff.thinking || { type: 'disabled' },
                ...(eff.reasoningEffort ? { reasoning_effort: eff.reasoningEffort } : {}),
                stream: false,
              }),
              signal: controller.signal,
            });
          } catch (err) {
            throw new Error(
              err.name === 'AbortError'
                ? 'Step 关卡设计超时（240 秒）'
                : '设计请求失败：' + err.message,
            );
          }
          if (!response.ok) {
            let detail = '';
            try {
              const body = await response.json();
              detail = body.error && body.error.message ? '：' + body.error.message : '';
            } catch (_) {}
            throw new Error('设计 API ' + response.status + detail);
          }
          report && report('设计完成，正在校验结构');
          const parsed = await readStepResponse(response, getEl('cleanReport'));
          const allowed = new Set(candidates.map((x) => String(x.id)));
          let level = parsed && parsed.level;
          if (
            (!level || !Array.isArray(level.items)) &&
            parsed &&
            Array.isArray(parsed.items) &&
            Array.isArray(parsed.beats)
          )
            level = parsed;
          /* scenes 多层结构(2026-08-28):轻量校验后直接交 compileLevel scenes 分支(权威校验)。
             场景内自洽(uses/reveals/result: 仅本场景)、素材全覆盖、全局 1 deliver、≥1 推理锁。 */
          const scenesIn =
            parsed && Array.isArray(parsed.scenes)
              ? parsed.scenes
              : level && Array.isArray(level.scenes)
                ? level.scenes
                : null;
          if (scenesIn) {
            const errs = [];
            /* 全局产物表(2026-08-30):跨房间 result: 引用合法——把其他房间做好的成品
               拿到本房间用(引擎支持产物跨场景使用),收束仍由 requires 闭包保证 */
            const gProducers = new Set(
              scenesIn
                .flatMap((s) => (s.beats || []).filter(Boolean))
                .filter((b) => b.action === 'combine' || b.action === 'sequence')
                .map((b) => String(b.id)),
            );
            if (scenesIn.length < 2 || scenesIn.length > 3)
              errs.push('scenes 需 2-3 个房间(当前 ' + scenesIn.length + ')');
            const claimed = new Set();
            let gBeats = 0,
              gDels = 0,
              gLocks = 0;
            /* 机关道具(2026-08-30 需求方裁定):prop-* 无网页背景纯机构。
               factValues 收集模型自己申报的全部 sourceFacts 值,用于检查机关道具
               reason 没有携带素材事实——机构与信息分工的机器可验证面。 */
            const isPropId = (id) => /^prop-[a-z0-9_-]{0,24}$/i.test(String(id));
            const factValues = scenesIn
              .flatMap((s) => (Array.isArray(s.items) ? s.items : []))
              .flatMap((it) => (Array.isArray(it && it.sourceFacts) ? it.sourceFacts : []))
              .map((f) => String((f && f.v) || '').trim())
              .filter((v) => v.length >= 2);
            const propPerRoom = [];
            scenesIn.forEach(function (sc, si) {
              const items = Array.isArray(sc.items) ? sc.items : [];
              const beats = (Array.isArray(sc.beats) ? sc.beats : []).filter(Boolean);
              if (sc && sc.locked === true)
                errs.push(
                  '房间' +
                    (si + 1) +
                    ' 不允许 locked:true——所有房间开局同时亮出供自由探索,上锁放在容器(hidden 素材)与推理锁上,不放在房间门口',
                );
              if (items.length < 2 || beats.length < 2)
                errs.push(
                  '房间' +
                    (si + 1) +
                    ' 需至少 2 素材与 2 步(当前 ' +
                    items.length +
                    '/' +
                    beats.length +
                    ')——单物件房间是过渡通道,不是可探索的空间',
                );
              const local = new Set();
              let roomProps = 0;
              items.forEach(function (it) {
                const id = String(it && it.id);
                local.add(id);
                /* 机关道具(prop-*):无网页背景的纯机构。不占素材名额,但有自己的规矩:
                   reason 只写自身物性,禁止携带任何素材事实(P46——事实只能来自化身) */
                if (isPropId(id)) {
                  roomProps++;
                  const reasonTxt = String((it && it.reason) || '');
                  const misused = factValues.find((v) => v && reasonTxt.indexOf(v) >= 0);
                  if (misused)
                    errs.push(
                      '机关道具 ' +
                        id +
                        ' 的 reason 携带了素材事实「' +
                        misused +
                        '」——机关道具只写自身物性与状态,谜面证据只能来自素材化身',
                    );
                  return;
                }
                if (!allowed.has(id))
                  errs.push(
                    '素材 ' + id + ' 不在本次素材表(无收藏背景的机关道具 id 必须以 prop- 开头)',
                  );
                else if (claimed.has(id)) errs.push('素材 ' + id + ' 被分配到多个房间');
                else claimed.add(id);
                /* 接地检查(P46/P62):sourceFacts 的值必须能在该素材的可核查文本
                   (desc/标题/路径/域名/日期)里原样找到——把"内容参与解谜"变成机器可验证,
                   防止模型改写/编造页面事实(P31 老毛病)。
                   2026-09-01:补入 domain 与 dateAdded——两者是物件弹窗常驻展示的真实字段
                   (P67 措辞铁律要求谜面与展示一致),此前遗漏导致「域名:xxx」类合法引用
                   被误判为编造,实测烧光赛马轮次(goal-after-sync.log 周期1) */
                const src = candidates.find((c) => String(c.id) === id) || {};
                const ground = (
                  String(src.desc || '') +
                  ' ' + String(src.title || '') +
                  ' ' + String(src.urlPath || '') +
                  ' ' + String(src.domain || '') +
                  ' ' + String(src.dateAdded || '')
                ).trim();
                (Array.isArray(it && it.sourceFacts) ? it.sourceFacts : []).forEach(function (f) {
                  const v = String(f && f.v || '').trim();
                  if (v && ground && ground.indexOf(v) < 0)
                    errs.push(
                      '素材 ' +
                        id +
                        ' 的 sourceFacts「' +
                        ((f && f.k) || '?') +
                        ':' +
                        v +
                        '」在它的网页描述/标题/路径里找不到——sourceFacts 只能原样抄录素材文本中真实存在的内容(数字/词句逐字取自原文),不得改写或编造',
                    );
                });
              });
              propPerRoom.push(roomProps);
              const producers = new Set(
                beats
                  .filter((b) => b && (b.action === 'combine' || b.action === 'sequence'))
                  .map((b) => String(b.id)),
              );
              beats.forEach(function (b) {
                if (!b) return;
                gBeats++;
                if (b.action === 'deliver') gDels++;
                if (['password', 'angle', 'morse'].includes(b.action)) gLocks++;
                if (b.action !== 'deliver' && (!Array.isArray(b.uses) || !b.uses.length))
                  errs.push('房间' + (si + 1) + ' 步骤「' + (b.title || b.id) + '」uses 为空');
                if (
                  (b.action === 'combine' || b.action === 'sequence') &&
                  (!Array.isArray(b.uses) || b.uses.length < 2)
                )
                  errs.push('「' + (b.title || b.id) + '」的 uses 需 ≥2 个');
                (b.uses || []).forEach(function (u) {
                  const s = String(u);
                  if (s.startsWith('result:')) {
                    if (!producers.has(s.slice(7)) && !gProducers.has(s.slice(7)))
                      errs.push(
                        '「' +
                          (b.title || b.id) +
                          '」引用了不存在的产物 ' +
                          s +
                          '——本关没有任何 id 为「' +
                          s.slice(7) +
                          '」的组合步。result: 只能引用你自己输出里真实存在的 combine/sequence 步骤 id(改引用正确的那步,或把该步改成 combine)',
                      );
                  } else if (!local.has(s)) {
                    errs.push(
                      '「' + (b.title || b.id) + '」引用非本场景素材 ' + s + '(素材实体不能跨房间)',
                    );
                  }
                });
              });
            });
            if (claimed.size < N)
              errs.push('必须为全部 ' + N + ' 条素材各写化身并分配房间(仅 ' + claimed.size + ' 条)');
            /* 机关道具配额(2026-08-30 机构/信息分工):每房至少 1 件,全关 ≤5。
               不设下限会回到最低限度合规——模型一条都不放,收藏继续硬扮锁具。 */
            const propTotal = propPerRoom.reduce((a, b) => a + b, 0);
            propPerRoom.forEach(function (n, i) {
              if (n < 1)
                errs.push(
                  '房间' +
                    (i + 1) +
                    ' 没有机关道具——至少 1 件 prop-*(锁具/火柴/油灯/铁柜/抽屉等无网页背景的纯机构),收藏化身只做信息载体',
                );
            });
            if (propTotal > 5)
              errs.push(
                '机关道具过多(' +
                  propTotal +
                  ' 件)——全关 2-5 件就够,空间感靠容器嵌套而不是堆道具',
              );
            /* 谜题多样性硬门槛(2026-08-29 需求方反馈):禁止全部 inspect+password 的浅薄结构 */
            const allDesignBeats = scenesIn.flatMap((s) => (s.beats || []).filter(Boolean));
            const combineCount = allDesignBeats.filter((b) => b.action === 'combine').length;
            const inspectOnly = allDesignBeats.filter((b) => ['inspect', 'revisit'].includes(b.action)).length;
            if (combineCount < 1)
              errs.push('至少需要 1 个 combine 步(道具组合/原位变身)——纯 inspect+password 的关卡缺乏谜题操控感');
            /* 空间密度硬门槛(2026-08-30 空间感落地):数量门槛换密度门槛——
               每房间 hidden+容器显形链、全关 reveals≥2、至少 1 件回访物件。
               旧「≥1 hidden」只换来贴线的一件(四份实测产物全部恰好 1),换成密度门槛。 */
            const revealTotal = allDesignBeats.reduce(
              (n, b) => n + (Array.isArray(b.reveals) ? b.reveals.length : 0),
              0,
            );
            if (revealTotal < 2)
              errs.push(
                '全关 reveals 显形仅 ' +
                  revealTotal +
                  ' 处——每个房间都要有一处「容器显形隐藏物」的空间发现(共 ≥2 处)',
              );
            scenesIn.forEach(function (sc, si) {
              const scItems = (Array.isArray(sc.items) ? sc.items : []).filter(Boolean);
              const hidIds = new Set(
                scItems.filter((it) => it && it.hidden === true).map((it) => String(it.id)),
              );
              if (!hidIds.size) {
                errs.push(
                  '房间' +
                    (si + 1) +
                    ' 没有任何 hidden 素材——每个房间都要藏一件「容器/暗格里的东西」,由本房间某个步骤的 reveals 显形',
                );
                return;
              }
              const scBeatList = (Array.isArray(sc.beats) ? sc.beats : []).filter(Boolean);
              const hasChain = scBeatList.some(
                (b) =>
                  (Array.isArray(b.reveals) ? b.reveals : []).some((r) => hidIds.has(String(r))) &&
                  (Array.isArray(b.uses) ? b.uses : []).some((u) => !String(u).startsWith('result:')),
              );
              if (!hasChain)
                errs.push(
                  '房间' +
                    (si + 1) +
                    ' 的 hidden 素材缺少「容器显形步」——某个步骤的 reveals 里要有它,且该步的 uses 含本房间的容器物件 id(引擎据此把道具嵌进容器)',
                );
            });
            const revisitUse = {};
            allDesignBeats.forEach((b) =>
              (Array.isArray(b.uses) ? b.uses : []).forEach((u) => {
                const s = String(u);
                if (!s.startsWith('result:')) revisitUse[s] = (revisitUse[s] || 0) + 1;
              }),
            );
            if (!Object.keys(revisitUse).some((k) => revisitUse[k] >= 2))
              errs.push(
                '没有回访物件——至少 1 件素材要被 ≥2 个步骤使用(先观察/改造,之后回访再用,像参考A的电报机:装电池变身→最后拿它按指纹锁)',
              );
            if (inspectOnly > allDesignBeats.length * 0.6)
              errs.push('inspect 步骤占比过高(' + inspectOnly + '/' + allDesignBeats.length + ')——谜题需要 combine/password/angle/morse 的操控感');
            /* 房间全亮后的收束检查(2026-08-30):并行不等于割裂——终局交付的依赖
               闭包必须横跨至少 2 个场景,迫使玩家拼合两个房间的事实才能通关;
               否则「并行房间」退化为互不相干的密室拼接。 */
            if (scenesIn.length >= 2) {
              const sceneOfBeat = {};
              scenesIn.forEach(function (sc, si) {
                (sc.beats || []).filter(Boolean).forEach((b) => (sceneOfBeat[String(b.id)] = si));
              });
              const deliverBeat = allDesignBeats.filter(Boolean).find((b) => b.action === 'deliver');
              if (deliverBeat) {
                const seen = new Set(),
                  reachScenes = new Set(),
                  stack = [String(deliverBeat.id)];
                while (stack.length) {
                  const bid = stack.pop();
                  if (seen.has(bid)) continue;
                  seen.add(bid);
                  if (sceneOfBeat[bid] !== undefined) reachScenes.add(sceneOfBeat[bid]);
                  const bb = allDesignBeats.find((x) => x && String(x.id) === bid);
                  ((bb && Array.isArray(bb.requires) ? bb.requires : []) || []).forEach((r) => {
                    const rs = String(r);
                    if (sceneOfBeat[rs] !== undefined) stack.push(rs);
                  });
                }
                if (reachScenes.size < 2)
                  errs.push(
                    '终局交付的依赖必须收束至少 2 个房间——给最后一个房间交付前的关键步(推理锁或 combine)加跨房间 requires,引用前面房间读线索的步骤 id(跨房间 requires 合法,uses 仍限本场景)',
                  );
              }
            }
            const themeSrc =
              String((parsed && parsed.theme) || (level && level.theme) || '').trim();
            if (!themeSrc)
              errs.push('顶层需要 theme(一句主题描述——延迟命名在通关后展示它)');
            const grammars = ['变形', '朝圣', '审判', '失忆', '官僚迷宫', '梦境接力', '错误宇宙', '无中心选集'];
            const gRaw = String((parsed && parsed.adventureGrammar) || (level && level.adventureGrammar) || '');
            if (!grammars.some((g) => gRaw.indexOf(g) >= 0))
              errs.push(
                'adventureGrammar 需从八种语法中选一(变形/朝圣/审判/失忆/官僚迷宫/梦境接力/错误宇宙/无中心选集),格式「语法名:一句如何组织」(当前「' + gRaw.slice(0, 40) + '」)',
              );
            /* 泄漏检查(P4/审查 11.2):答案不得原样出现在 premise/objective/hints */
            const leakScan = [parsed.premise, parsed.objective]
              .concat(parsed.hints || [])
              .filter(Boolean)
              .join('\n');
            scenesIn.forEach(function (sc) {
              (sc.beats || []).forEach(function (b) {
                if (!b) return;
                const ans =
                  b.action === 'password'
                    ? String(b.expected || '')
                    : b.action === 'morse'
                      ? String(b.code || '').replace(/[^\d]/g, '')
                      : '';
                if (ans && ans.length >= 3 && leakScan.indexOf(ans) >= 0)
                  errs.push(
                    '机关「' + (b.title || b.id) + '」的答案 ' + ans + ' 泄漏在 premise/objective/hints 里(P4)',
                  );
              });
            });
            /* creativeThesis 缺失不硬拒(2026-08-29 实测:GLM low 常漏该字段,硬拒会烧光
               赛马轮次)——回执对缺失优雅降级;prompt 仍要求且置于输出首字段。 */
            if (gDels !== 1) errs.push('deliver 恰好 1 个且在最后一个房间(当前 ' + gDels + ')');
            if (!gLocks) errs.push('缺少推理锁(至少 1 个 password/angle/morse)');
            if (gBeats < N - 1 || gBeats > N + 8)
              errs.push('总步数需 ' + (N - 1) + '-' + (N + 8) + '(当前 ' + gBeats + ')——素材 ' + N + ' 条时谜题链要撑满更多步骤');
            if (errs.length)
              throw { retry: true, message: 'scenes 结构问题:' + errs.slice(0, 3).join(';') };
            window.__lastDesignDebug = { scenes: scenesIn.length, beats: gBeats };
            /* 归一化:模型/桩可能把 scenes 包在 level 里返回——编译器读顶层 design.scenes,
               这里统一提升,避免校验与编译看到不同形状(2026-08-28 旧电脑密室复盘发现的绕过通道)。 */
            return { parsed: level && level.scenes ? level : parsed };
          }
          /* 2026-08-28:scenes 成为唯一设计结构——平铺输出打回重设计。结构逃逸会绕开
             多层房间要求(实测:旧电脑密室三路首轮全败后逃回平铺)。以下平铺校验保留
             作平铺模式回退参考,当前不可达。 */
          if (!scenesIn)
            throw {
              retry: true,
              message:
                '必须输出 scenes 多房间结构(主节点→房间→容器→道具;2-3 个房间、6 条素材全分配、最后一个房间的最后一步是全局唯一 deliver)。平铺 items/beats 是已废弃的旧格式',
            };
          if (!level || !Array.isArray(level.items) || !Array.isArray(level.beats)) {
            window.__lastDesignDebug = {
              parsedNull: !parsed,
              parsedKeys: parsed ? Object.keys(parsed) : null,
            };
            throw { retry: true, message: '模型返回缺少有效关卡结构' };
          }
          const levelItems = level.items.filter((it) => it && allowed.has(String(it.id)));
          if (levelItems.length < 6)
            throw {
              retry: true,
              message: '必须为全部 6 条素材各写一条化身(仅得到 ' + levelItems.length + ' 条)',
            };
          const beats = level.beats.filter(Boolean);
          if (beats.length < 5 || beats.length > 14)
            throw { retry: true, message: 'beats 需 6-10 步(当前 ' + beats.length + ')' };
          const dels = beats.filter((b) => b.action === 'deliver');
          if (dels.length !== 1)
            throw { retry: true, message: 'deliver 恰好 1 个(当前 ' + dels.length + ')' };
          if (beats[beats.length - 1] !== dels[0])
            throw { retry: true, message: 'deliver 必须是最后一步' };
          if (!beats.some((b) => ['password', 'angle', 'morse'].includes(b.action)))
            throw { retry: true, message: '缺少推理锁(至少 1 个 password/angle/morse,参数写全)' };
          const emptyUse = beats.filter(
            (b) => b.action !== 'deliver' && (!Array.isArray(b.uses) || !b.uses.length),
          );
          if (emptyUse.length)
            throw {
              retry: true,
              message:
                '这些步骤没有交互物件(uses 为空):' +
                emptyUse.map((b) => String(b.title || b.id)).join('、') +
                '——每个 beat 必须落在至少一个素材上',
            };
          const badLen = beats.filter(
            (b) =>
              (b.action === 'combine' || b.action === 'sequence') &&
              (!Array.isArray(b.uses) || b.uses.length < 2),
          );
          if (badLen.length)
            throw {
              retry: true,
              message:
                'combine/sequence 的 uses 必须 2 个以上:' +
                badLen.map((b) => String(b.title || b.id)).join('、'),
            };
          const bidSet = new Set(beats.map((b) => String(b.id))),
            iidSet = new Set(levelItems.map((it) => String(it.id)));
          const bad = beats.filter((b) =>
            (b.uses || []).some(function (u) {
              const s = String(u);
              return s.startsWith('result:') ? !bidSet.has(s.slice(7)) : !iidSet.has(s);
            }),
          );
          if (bad.length)
            throw {
              retry: true,
              message:
                '引用了不存在的素材或产物:' + bad.map((b) => String(b.title || b.id)).join('、'),
            };
          /* v7.1:锁的目标物件不得同时被观察步使用——引擎的机关面板"随时可弹"会拦截该物件的一切点击,
             观察步将永远无法完成(范例均遵守:prison 的摩斯锁装在变身后的电报机上,而非被观察的笔记/日记) */
          const inspectTargets = new Set();
          beats.forEach(function (b) {
            if (b.action === 'inspect' || b.action === 'revisit')
              (b.uses || []).forEach(function (u) {
                if (!String(u).startsWith('result:')) inspectTargets.add(String(u));
              });
          });
          const conflict = beats.filter(function (b) {
            return (
              ['password', 'angle', 'morse'].includes(b.action) &&
              (b.uses || []).some(function (u) {
                return inspectTargets.has(String(u));
              })
            );
          });
          if (conflict.length)
            throw {
              retry: true,
              message:
                '机关「' +
                conflict.map((b) => String(b.title || b.id)).join('、') +
                '」的目标物件同时被观察步使用——点击会被机关面板拦截,观察步永远完不成。把锁装在 result: 组合产物上(像参考A把摩斯锁装在通电后的电报机上),或换一件没有被观察过的物件当锁',
            };
          /* v7.4:机关参数在设计环节验证——编译器对非法参数的降级会让高潮凭空消失
            (废弃医院实测:角度锁 angles 不是 precision 倍数,被降级成普通点击,'调整海报角度'名存实亡) */
          const badLock = [];
          beats.forEach(function (b) {
            if (!['password', 'angle', 'morse'].includes(b.action)) return;
            const name = '「' + String(b.title || b.id) + '」';
            if (b.action === 'password') {
              const e = String(b.expected || '').replace(/\D/g, '');
              if (!e || e.length < 3 || e.length > 6)
                badLock.push('密码锁' + name + '的 expected 需 3-6 位数字(当前「' + String(b.expected || '') + '」)');
            } else if (b.action === 'morse') {
              if (!/^[.\-/]{1,24}$/.test(String(b.code || '')))
                badLock.push('摩斯锁' + name + '的 code 只能含 .-/ 与分隔(当前「' + String(b.code || '') + '」)');
            } else if (b.action === 'angle') {
              const p = [10, 15, 30, 45].includes(Number(b.precision)) ? Number(b.precision) : 30;
              const as = (Array.isArray(b.angles) ? b.angles : [])
                .map(Number)
                .filter((v) => Number.isFinite(v) && v > 0 && v < 360 && v % p === 0);
              if (!as.length)
                badLock.push(
                  '角度锁' +
                    name +
                    '的 angles 必须非空且都是 precision(' +
                    p +
                    ') 的倍数(当前「' +
                    JSON.stringify(b.angles || []) +
                    '」)',
                );
            }
          });
          if (badLock.length)
            throw {
              retry: true,
              message:
                badLock.join('; ') +
                '——参数不合法的机关会在编译时被降级成普通点击,高潮凭空消失',
            };
          return { model, parsed: { ...level, items: levelItems, beats } };
        } finally {
          clearTimeout(timer);
        }
      };
      /* 预算收敛(审查 11.3.2):内层只处理网络停滞/流中断重试(最多 3 次,同一提示词);
         结构问题立即上抛,由外层轮次/赛马层带修复反馈重试——双层相乘会把最坏
         设计调用推到 27 次(3 路×3 轮×3 内层),现在收敛回 3 路×3 轮。 */
      let result = null,
        lastErr = '';
      for (let i = 0; i < 3; i++) {
        try {
          result = await attempt(lastErr);
          break;
        } catch (err) {
          const msg = (err && (err.message || err.msg)) || String(err);
          if (err && err.retry) throw err;
          if (/abort|超时|请求失败|BodyStreamBuffer/i.test(msg) && i < 2) {
            lastErr = '网络停滞:' + msg;
            report && report('设计流中断，正在重试 ' + (i + 1) + '/2');
            continue;
          }
          throw err;
        }
      }
      if (!result) throw new Error('设计连续 3 次网络失败：' + lastErr);
      return result;
    },
    async design(cleaned, modelResult, theme) {
      const draft = draftFromClean(cleaned, modelResult);
      return callStepLevel(draft, theme || '');
    },
    clean: localClean,
    /* ===== 全局清洗与标记记录(2026-08-28):导入即清洗,时间片只取通过条目,增量维护 ===== */
    /* 把存量判定合并到本地清洗结果上;verdicts 形如 { 规范化URL: {status,topics,reason,signal,v} }。
       安全红线(safetyFlag)恒为 archive;判定版本不符视同未标记。返回记录带 verdict 字段(命中的版本)。 */
    applyVerdicts(items, verdicts) {
      const base = localClean(items);
      const records = base.records.map(function (item) {
        if (item.safetyFlag) return { ...item, status: 'archive', verdict: null };
        const v = verdicts && verdicts[item.canonicalUrl];
        if (!v || v.v !== CLEAN_VERSION) return { ...item, verdict: null };
        return {
          ...item,
          status: ['keep', 'review', 'archive'].includes(v.status) ? v.status : item.status,
          topics: Array.isArray(v.topics) && v.topics.length ? v.topics : item.topics,
          reason: v.reason || item.reason,
          signal: v.signal || item.signal,
          /* desc 富化(阶段4 事实提取):存量网页描述回填到素材,设计输入的内容来源 */
          description: item.description || v.desc || '',
          verdict: v.v,
        };
      });
      return { ...base, records };
    },
    /* 增量清洗:只对传入的未标记条目分批并发调模型(快车道直连),逐批合并后返回。
       批大小/并发度可配:cleanBatchSize(默认 40,上限 60=modelSample 单次采样上限)、
       cleanConcurrency(默认 3,上限 8)。server 为 ThreadingHTTPServer,直连分支无共享状态。 */
    async cleanBatch(records, theme, report) {
      const CHUNK = Math.max(10, Math.min(60, Number(llmConfig.cleanBatchSize) || 40));
      const CONC = Math.max(1, Math.min(8, Number(llmConfig.cleanConcurrency) || 3));
      const merged = records.map((r) => ({ ...r }));
      const chunks = [];
      for (let i = 0; i < merged.length; i += CHUNK) chunks.push(merged.slice(i, i + CHUNK));
      let done = 0;
      const reportOnce = () => report && report('增量清洗 ' + done + '/' + chunks.length + ' 批……');
      reportOnce();
      let ptr = 0;
      async function worker() {
        while (ptr < chunks.length) {
          const idx = ptr++;
          const chunk = chunks[idx];
          const remote = await callStep(chunk, theme || '', chunk.length);
          const applied = applyModelResult(
            { records: chunk, stats: { input: chunk.length, unique: chunk.length, duplicates: 0 } },
            remote.parsed,
          );
          applied.records.forEach((r, j) => {
            Object.assign(chunk[j], {
              status: r.status,
              topics: r.topics,
              reason: r.reason,
              signal: r.signal,
            });
          });
          done++;
          reportOnce();
        }
      }
      await Promise.all(Array.from({ length: Math.min(CONC, chunks.length) }, worker));
      return merged;
    },
    /* 把最终标记固化为标记记录(以规范化 URL 为键) */
    buildVerdicts(records) {
      const at = new Date().toISOString();
      return (records || []).map((r) => ({
        id: r.canonicalUrl,
        url: r.url,
        title: r.title,
        status: r.status,
        topics: r.topics || [],
        reason: r.reason || '',
        signal: r.signal || '',
        safetyFlag: r.safetyFlag || '',
        desc: String(r.description || '').slice(0, 300),
        fetchedTitle: String(r.fetchedTitle || ''),
        v: CLEAN_VERSION,
        at,
      }));
    },
  };
  if (typeof roomReset === 'function') roomReset();
  if (typeof render === 'function') render();
  if (typeof applyView === 'function') applyView();
})();
