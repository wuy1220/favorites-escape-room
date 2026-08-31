/* Execute the compiled level as a clue-driven room inside the graph.
   2026-08-23 重写:不再逐 beat 强制双卡同屏。所有素材始终可见,
   beats 编译成 clue 规则(前置门/组合表/顺序锁/交付),玩家自由探索,
   错误组合有反馈,依赖未满足时检查给出线索——密室而不是任务清单。 */
(function () {
  let compiled = null;
  /* 东八区显示(2026-08-31):+8h 后读 ISO,与机器时区无关;存储保持 ISO UTC */
  const whenLabel = (iso) => {
    const d = new Date(iso);
    const c = isNaN(d) ? null : new Date(d.getTime() + 8 * 3600 * 1000).toISOString();
    const m = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/.exec(String(c || ''));
    return m ? m[1] + ' ' + m[2] : iso ? String(iso).slice(0, 16).replace('T', ' ') : '';
  };

  /* ---------- 把 level.beats 编译成 clue 规则 ---------- */
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

  /* ---------- 通用密码盘(复用 keypadModal,支持颜色标签密码盘) ---------- */
  let keypadCtx = null;
  function ensureKeypad() {
    const kp = $('keypad');
    if (!kp || kp.dataset.ready) return;
    kp.dataset.ready = '1';
    /* 2026-08-29 UI 系统化:.code/.kp-slot 样式已迁入 css/styles.css */
    const digits = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'];
    kp.innerHTML = digits
      .map(function (d) {
        return '<button type="button" data-k="' + d + '">' + d + '</button>';
      })
      .join('');
    kp.querySelectorAll('button').forEach(function (b) {
      b.onclick = function () {
        keypadPress(b.dataset.k);
      };
    });
    $('keyClear').onclick = function () {
      if (!keypadCtx) return;
      /* 文字语义锁:清除 = 清空文本输入并聚焦(此前只清数字缓冲,文字模式下按钮形同禁用) */
      if (keypadCtx.textMode) {
        const kt2 = document.getElementById('keypadText');
        if (kt2) {
          kt2.value = '';
          kt2.focus();
        }
        return;
      }
      keypadCtx.buf = [];
      keypadRender();
    };
    $('keyCancel').onclick = function () {
      $('keypadModal').classList.add('hidden');
      keypadCtx = null;
    };
    $('keyEnter').onclick = function () {
      keypadCommit();
    };
    const kt = document.getElementById('keypadText');
    if (kt)
      kt.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          keypadCommit();
        }
      });
  }
  function keypadPress(d) {
    if (!keypadCtx || keypadCtx.textMode) return; /* 文字模式:数字盘已隐藏,按键兜底失效 */
    if (!keypadCtx.textMode && keypadCtx.buf.length >= keypadCtx.digits) return;
    keypadCtx.buf.push(d);
    keypadRender();
    if (!keypadCtx.textMode && keypadCtx.buf.length === keypadCtx.digits) keypadCommit();
  }
  function keypadRender() {
    const c = keypadCtx,
      disp = $('codeDisplay');
    if (!c || !disp) return;
    let inner;
    if (c.colors && c.colors.length) {
      inner = c.colors
        .map(function (col, i) {
          const v = c.buf[i];
          return (
            '<span class="kp-slot"><b>' +
            (col || '') +
            '</b><i>' +
            (v != null ? v : '·') +
            '</i></span>'
          );
        })
        .join('');
    } else {
      inner = '';
      for (let i = 0; i < c.digits; i++) inner += c.buf[i] != null ? c.buf[i] : '·';
    }
    disp.innerHTML = inner;
  }
  /* 无效交互反馈(2026-08-30 修订):旧版对整个 #stage 做 0.35s ±7px 全屏震动,
     高频触发(连输密码/连试组合)令人难受——改为局部轻推(摇弹窗卡片或涉及的
     两张物件卡),全局限频 ≥900ms 一次,prefers-reduced-motion 时不播。 */
  let lastNudgeAt = 0;
  function nudge(targets) {
    const list = (Array.isArray(targets) ? targets : [targets]).filter(Boolean);
    if (!list.length) return;
    const now = Date.now();
    if (now - lastNudgeAt < 900) return;
    lastNudgeAt = now;
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    list.forEach((el) => {
      el.classList.remove('shake-soft');
      void el.offsetWidth;
      el.classList.add('shake-soft');
    });
  }
  function nodeEl(id) {
    try {
      return document.querySelector(
        '[data-id="' + (window.CSS && CSS.escape ? CSS.escape(String(id)) : String(id)) + '"]',
      );
    } catch (_) {
      return null;
    }
  }
  function keypadCommit() {
    const c = keypadCtx;
    if (!c) return;
    /* 文字语义锁:答案取自文本输入框(数字锁仍走按键缓冲) */
    const got = c.textMode && $('keypadText') ? $('keypadText').value : c.buf.join('');
    if (!c.textMode && got.length < c.digits) {
      nudge([$('keypadModal') && $('keypadModal').querySelector('.modal-card')]);
      return;
    }
    const norm = (x) =>
      String(x || '')
        .trim()
        .toLowerCase()
        .replace(/\s+/g, ' ');
    if (c.textMode ? norm(got) === norm(c.expected) : got === c.expected) {
      $('keypadModal').classList.add('hidden');
      keypadCtx = null;
      if (c.onSuccess) c.onSuccess();
    } else {
      c.buf = [];
      keypadRender();
      nudge([$('keypadModal') && $('keypadModal').querySelector('.modal-card')]);
      if (c.onFail) c.onFail();
      toast('密码不对。机关没有反应。');
    }
  }
  function openKeypad(opts) {
    ensureKeypad();
    const expectStr = String(opts.expected || '');
    const textMode = /[^0-9]/.test(expectStr); /* 语义锁:答案是文字(歌名/格式/术语) */
    keypadCtx = {
      digits: opts.digits || 3,
      colors: opts.colors || [],
      expected: expectStr,
      textMode,
      onSuccess: opts.onSuccess,
      onFail: opts.onFail,
      buf: [],
    };
    const textInput = $('keypadText');
    if (textInput) {
      textInput.value = '';
      textInput.style.display = textMode ? '' : 'none';
      if (textMode) textInput.focus();
    }
    /* 语义锁(2026-08-31):文字答案不该看到数字键盘——位数圆点还会泄露答案长度
       (实测截图:输入"动画图解"的锁面挂着 1-9 数字盘和 4 个圆点,"清除"也只清数字缓冲) */
    const disp = $('codeDisplay'),
      pad = $('keypad');
    if (disp) disp.style.display = textMode ? 'none' : '';
    if (pad) pad.style.display = textMode ? 'none' : '';
    const card = $('keypadModal');
    const kicker = card.querySelector('.kicker'),
      h2 = card.querySelector('h2'),
      copy = $('keypadCopy');
    if (kicker) kicker.textContent = '机关 / ' + (opts.kicker || '密码锁');
    if (h2) h2.textContent = opts.title || '输入密码';
    if (copy) copy.textContent = opts.copy || '输入正确密码。';
    keypadRender();
    if (window.__openPuzzlePanel) window.__openPuzzlePanel('keypadModal');
    else card.classList.remove('hidden');
  }

  /* ---------- 角度旋钮(angle):N 个可旋转表盘,拖拽/点按转到目标角度(0°=12点,顺时针) ---------- */
  let angleCtx = null;
  function ensureAngle() {
    if (document.getElementById('angleModal')) return;
    /* 2026-08-29 UI 系统化:angle-dial/ad-label/ad-face/ad-val 与 morse 系列样式已迁入 css/styles.css */
    const m = document.createElement('div');
    m.className = 'modal hidden';
    m.id = 'angleModal';
    m.innerHTML =
      '<div class="modal-card"><div class="kicker" id="angleKicker">机关 / 角度旋钮</div><h2 id="angleTitle">转动旋钮</h2><p id="angleCopy">把每个表盘转到正确的角度。</p><div id="angleDials"></div><div class="modal-actions"><button class="reset" id="angleCancel" type="button">关闭</button></div></div>';
    document.body.appendChild(m);
    $('angleCancel').onclick = function () {
      $('angleModal').classList.add('hidden');
      angleCtx = null;
    };
  }
  /* 表盘:0°=12点,顺时针;刻度每 precision 度;0/90/180/270 标注;指针指向当前角度 */
  function angleSvg(i, cur, precision) {
    const ticks = [];
    for (let a = 0; a < 360; a += precision) {
      const x1 = 50 + 42 * Math.sin((a * Math.PI) / 180),
        y1 = 50 - 42 * Math.cos((a * Math.PI) / 180);
      const x2 = 50 + 46 * Math.sin((a * Math.PI) / 180),
        y2 = 50 - 46 * Math.cos((a * Math.PI) / 180);
      ticks.push(
        '<line x1="' +
          x1.toFixed(1) +
          '" y1="' +
          y1.toFixed(1) +
          '" x2="' +
          x2.toFixed(1) +
          '" y2="' +
          y2.toFixed(1) +
          '" stroke="currentColor" stroke-opacity="0.45" stroke-width="' +
          (a % 90 === 0 ? 2.5 : 1) +
          '"/>',
      );
    }
    const nums = [0, 90, 180, 270]
      .map(function (a) {
        const x = 50 + 34 * Math.sin((a * Math.PI) / 180),
          y = 50 - 34 * Math.cos((a * Math.PI) / 180);
        return (
          '<text x="' +
          x.toFixed(1) +
          '" y="' +
          (y + 3).toFixed(1) +
          '" text-anchor="middle" font-size="9" fill="currentColor" fill-opacity="0.65">' +
          a +
          '°</text>'
        );
      })
      .join('');
    const hx = 50 + 38 * Math.sin((cur * Math.PI) / 180),
      hy = 50 - 38 * Math.cos((cur * Math.PI) / 180);
    return (
      '<svg class="ad-face" data-i="' +
      i +
      '" viewBox="0 0 100 100"><circle cx="50" cy="50" r="47" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="2"/><circle cx="50" cy="50" r="3.5" fill="var(--seal)"/>' +
      ticks.join('') +
      nums +
      '<line data-hand="" x1="50" y1="50" x2="' +
      hx.toFixed(1) +
      '" y2="' +
      hy.toFixed(1) +
      '" stroke="var(--seal)" stroke-width="3.5" stroke-linecap="round"/></svg>'
    );
  }
  function angleRender() {
    const c = angleCtx;
    if (!c) return;
    const box = $('angleDials');
    box.innerHTML = c.angles
      .map(function (target, i) {
        const label = (c.labels && c.labels[i]) || '旋钮 ' + (i + 1);
        return (
          '<div class="angle-dial" data-i="' +
          i +
          '"><div class="ad-label">' +
          label +
          '</div>' +
          angleSvg(i, c.cur[i], c.precision) +
          '<div class="ad-val">' +
          c.cur[i] +
          '°</div></div>'
        );
      })
      .join('');
    box.querySelectorAll('.ad-face').forEach(function (svg) {
      svg.addEventListener('pointerdown', function (e) {
        anglePointer(svg, e);
      });
    });
  }
  /* 点按/拖拽表盘:指针实时跟随,松手吸附到最近档位;全部到位即解锁(不显示目标角度,不剧透) */
  function anglePointer(svg, e) {
    const c = angleCtx;
    if (!c) return;
    const i = Number(svg.dataset.i);
    const r = svg.getBoundingClientRect(),
      cx = r.left + r.width / 2,
      cy = r.top + r.height / 2;
    function toAngle(ev) {
      const dx = ev.clientX - cx,
        dy = ev.clientY - cy;
      let a = (Math.atan2(dx, -dy) * 180) / Math.PI;
      if (a < 0) a += 360;
      return (Math.round(a / c.precision) * c.precision) % 360;
    }
    function paint(ev) {
      const a = toAngle(ev);
      const line = svg.querySelector('line[data-hand]');
      if (line) {
        line.setAttribute('x2', (50 + 38 * Math.sin((a * Math.PI) / 180)).toFixed(1));
        line.setAttribute('y2', (50 - 38 * Math.cos((a * Math.PI) / 180)).toFixed(1));
      }
      const val = svg.closest('.angle-dial').querySelector('.ad-val');
      if (val) val.textContent = a + '°';
    }
    function up(ev) {
      svg.removeEventListener('pointermove', paint);
      window.removeEventListener('pointerup', up);
      c.cur[i] = toAngle(ev);
      if (
        c.angles.every(function (t, j) {
          return c.cur[j] === t;
        })
      ) {
        $('angleModal').classList.add('hidden');
        angleCtx = null;
        if (c.onSuccess) c.onSuccess();
      } else if (c.onTurn) c.onTurn();
      angleRender();
    }
    svg.addEventListener('pointermove', paint);
    window.addEventListener('pointerup', up);
    paint(e);
    e.preventDefault();
  }
  function openAngle(opts) {
    ensureAngle();
    angleCtx = {
      angles: opts.angles || [],
      precision: opts.precision || 30,
      cur: (opts.angles || []).map(function () {
        return 0;
      }),
      labels: opts.labels || [],
      onSuccess: opts.onSuccess,
      onTurn: opts.onTurn,
    };
    $('angleKicker').textContent = '机关 / ' + (opts.kicker || '角度旋钮');
    $('angleTitle').textContent = opts.title || '转动旋钮';
    $('angleCopy').textContent = opts.copy || '拖拽每个表盘,转到正确的角度。';
    angleRender();
    if (window.__openPuzzlePanel) window.__openPuzzlePanel('angleModal');
    else $('angleModal').classList.remove('hidden');
  }

  /* ---------- 摩斯码(morse):点/划输入,校验 code ---------- */
  let morseCtx = null;
  function ensureMorse() {
    if (document.getElementById('morseModal')) return;
    const m = document.createElement('div');
    m.className = 'modal hidden';
    m.id = 'morseModal';
    m.innerHTML =
      '<div class="modal-card"><div class="kicker" id="morseKicker">机关 / 摩斯电码</div><h2 id="morseTitle">输入摩斯码</h2><p id="morseCopy">用点和划输入。</p><div class="morse-display" id="morseDisplay">·</div><div class="morse-keys"><button type="button" id="morseDot">· 点</button><button type="button" id="morseDash">— 划</button><button type="button" id="morseSlash">/ 分隔</button><button type="button" id="morseClear">清除</button></div><div class="modal-actions"><button class="reset" id="morseCancel" type="button">关闭</button><button class="primary" id="morseEnter" type="button">确认</button></div></div>';
    document.body.appendChild(m);
    $('morseDot').onclick = function () {
      morseKey('.');
    };
    $('morseDash').onclick = function () {
      morseKey('-');
    };
    $('morseSlash').onclick = function () {
      morseKey('/');
    };
    $('morseClear').onclick = function () {
      if (morseCtx) {
        morseCtx.buf = [];
        morseRender();
      }
    };
    $('morseCancel').onclick = function () {
      $('morseModal').classList.add('hidden');
      morseCtx = null;
    };
    $('morseEnter').onclick = morseCommit;
  }
  function morseKey(k) {
    if (!morseCtx) return;
    morseCtx.buf.push(k);
    morseRender();
  }
  function morseRender() {
    const c = morseCtx;
    if (!c) return;
    $('morseDisplay').textContent = c.buf.join('') || '·';
  }
  function morseCommit() {
    const c = morseCtx;
    if (!c) return;
    const got = c.buf.join('');
    if (got === c.code) {
      $('morseModal').classList.add('hidden');
      morseCtx = null;
      if (c.onSuccess) c.onSuccess();
    } else {
      c.buf = [];
      morseRender();
      nudge([$('morseModal') && $('morseModal').querySelector('.modal-card')]);
      if (c.onFail) c.onFail();
      toast('摩斯码不对。');
    }
  }
  function openMorse(opts) {
    ensureMorse();
    morseCtx = { code: opts.code || '', onSuccess: opts.onSuccess, onFail: opts.onFail, buf: [] };
    $('morseKicker').textContent = '机关 / ' + (opts.kicker || '摩斯电码');
    $('morseTitle').textContent = opts.title || '输入摩斯码';
    $('morseCopy').textContent = opts.copy || '输入正确的点划序列。';
    morseRender();
    if (window.__openPuzzlePanel) window.__openPuzzlePanel('morseModal');
    else $('morseModal').classList.remove('hidden');
  }

  function compiledLevelHydrate() {
    const raw = localStorage.getItem('favorite-room-draft');
    if (!raw) return;
    let draft;
    try {
      draft = JSON.parse(raw);
    } catch (_) {
      return;
    }
    const level = draft && draft.level;
    if (!level || !Array.isArray(level.items) || !level.items.length) return;
    if (get('compiled-level')) return;
    const groups = Array.isArray(draft.groups) ? draft.groups : [],
      roleNames = {
        learn: '学习 / 参考',
        build: '构建 / 工具',
        data: '数据 / 材料',
        inspiration: '灵感 / 观察',
        other: '其他',
      };
    /* 找出某物件对应的 inspect/revisit beat id,用于把"检查/回访"绑定为信息解锁(身份层)的时机 */
    const inspectBeatFor = function (itemId) {
      const b = (level.beats || []).find(function (x) {
        return (
          (x.action === 'inspect' || x.action === 'revisit') &&
          (x.uses || []).map(String).includes(String(itemId))
        );
      });
      return b ? b.id : null;
    };
    /* 身份层文案:真名/域名/收藏时刻/路径——与谜面层(纯氛围)分离,检查或回访后才解锁。
       P63(2026-08-30):完整 URL 与网页原文不再直出——原文已由 digest/sourceFacts
       加工后分层展示;原网页通过「打开原收藏」链接按需访问。 */
    const identityOf = function (source) {
      return (
        (source.title ? '「' + source.title + '」' : '') +
        (source.domain ? ' · ' + source.domain : '') +
        (source.dateAdded ? ' · 收藏于 ' + whenLabel(source.dateAdded) : '') +
        (source.urlPath && source.urlPath.length > 1
          ? '\n路径:' + source.urlPath.slice(0, 80)
          : '')
      );
    };
    /* 详情三层(P61/P63):谜面 → 事实 → 摘要 → 身份。facts 来自设计模型的 sourceFacts
       (接地检查验证过值真实存在于素材文本),digest 是它写的一句话摘要——网页原文
       与完整 URL 不再直出进详情 */
    const layeredDetail = function (item, source) {
      const facts = (item.facts || []).map((f) => f.k + ' ' + f.v).join(' · ');
      return (
        (item.reason || '先检查这件物件') +
        (facts ? '\n事实:' + facts : '') +
        (item.digest ? '\n摘要:' + item.digest : '') +
        (item.externalTask ? '\n回访任务:打开原收藏，' + item.externalTask : '') +
        (source && (source.title || source.domain) ? '\n——\n' + identityOf(source) : '')
      );
    };
    const imported = get('imported-room') || {
      id: 'imported-room',
      kind: 'zone imported-zone',
      name: '我的收藏草案',
      hint: draft.items.length + ' 条收藏 / ' + groups.length + ' 组',
      x: 45,
      y: 87,
      parent: 'root',
      hidden: true,
      startHidden: false,
      spawned: true,
      importedRoom: true,
      detail: '由原始收藏夹解析、清洗并编译出的可探索草案。',
    };
    if (!get('imported-room')) state.nodes.push(imported);
    if (!groups.some((group) => get('imported-' + (group.id || 0))))
      groups.forEach(function (group, gi) {
        const gid = 'imported-' + (group.id || gi),
          gx = 6 + (gi % 4) * 22,
          gy = 12 + Math.floor(gi / 4) * 15;
        state.nodes.push({
          id: gid,
          kind: 'zone imported-group',
          name: group.name || '主题 ' + (gi + 1),
          hint: (group.items || []).length + ' 条 / ' + (roleNames[group.role] || roleNames.other),
          x: gx,
          y: gy,
          parent: imported.id,
          hidden: true,
          startHidden: false,
          spawned: true,
          importedGroup: true,
          detail: '先检查这一组,再进入编译出的可玩关卡。',
        });
        (group.items || []).forEach(function (item) {
          state.nodes.push({
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
            detail: item.title + '\n' + (item.url || '') + '\n这是关卡编译使用的原始素材。',
          });
        });
      });
    const levelId = 'compiled-level',
      baseX = 45,
      baseY = 70;
    const hasScenes = Array.isArray(level.scenes) && level.scenes.length > 1;
    const nodes = [
      {
        id: levelId,
        kind: 'zone compiled-level',
        name: '可玩关卡 · ' + (level.title || '收藏机器'),
        hint: hasScenes
          ? level.parallelRooms === true
            ? '分 ' + level.scenes.length + ' 个房间,同时亮出——自由探索,线索串链'
            : '分 ' + level.scenes.length + ' 个场景,依次穿过它们'
          : '所有素材都已就位,寻找它们之间的因果',
        x: baseX,
        y: baseY,
        parent: imported.id,
        hidden: true,
        startHidden: true,
        spawned: true,
        compiledLevel: true,
        detail:
          (level.premise || '把收藏变成一次可行动的探索。') +
          '\n目标:' +
          (level.objective || '完成关卡。') +
          (level.timeline ? '\n—— 本关时间轴（按收藏顺序）——\n' + level.timeline : '') +
          (hasScenes
            ? '\n关卡分为 ' + level.scenes.length + ' 个场景。解开当前场景才能进入下一个。'
            : '\n所有素材都是可见的。判断哪些相关、按什么顺序使用——错误组合不会破坏任何东西。'),
      },
    ];
    /* 容器嵌套(S1/P42):hidden 道具 → 显形其的 beat 的容器物件(两条分支通用:
       scenes 关卡锚到源物件旁,平铺关卡的容器子件仍走容器网格)。
       锚定在 roomLayoutBoard 之后按**最终**位置统一执行。 */
    const revealSourceAll = {};
    (level.beats || []).forEach(function (b) {
      (b.reveals || []).forEach(function (rid) {
        if (revealSourceAll[rid]) return;
        const ro =
          b.resultOn && !String(b.resultOn).startsWith('result:') ? String(b.resultOn) : '';
        const u = ro || (b.uses || []).find((x) => !String(x).startsWith('result:'));
        if (!u) return;
        /* via=resultOn:显形物嵌在变身容器上(S1 容器嵌叠);
           via=use:显形物落在自己的房间槽位,仅以源物件作为飞入动画起点 */
        revealSourceAll[String(rid)] = { src: String(u), via: ro ? 'resultOn' : 'use' };
      });
    });
    /* 场景幕节点 + 场景内素材(有 scenes 时用 scene_name 化身名) */
    if (hasScenes) {
      level.scenes.forEach(function (sc, si) {
        const scId = 'compiled-scene-' + (sc.id || si);
        nodes.push({
          id: scId,
          kind: 'zone compiled-scene',
          name: sc.title || '未命名房间', /* 并行房间无先后之分,不再标「场景 N」 */
          hint: sc.focus || '',
          x: baseX - 14,
          y: baseY + 3 + si * 14,
          parent: levelId,
          hidden: true,
          startHidden: true,
          spawned: true,
          compiledScene: true,
          sceneIndex: si,
          sceneTitle: sc.title || '',
          detail:
            (sc.description || '') +
            (sc.focus ? '\n核心装置:' + sc.focus : '') +
            (si > 0 ? '\n上一场景留下的线索在这里有用。' : ''),
        });
        (level.items || [])
          .filter((it) => it.scene === (sc.id || si) || sc.itemIds?.includes(it.id))
          .slice(0, 8)
          .forEach(function (item, index) {
            const source = draft.items.find((x) => x.id === item.id) || {};
            const isHidden =
              item.hidden === true; /* LLM 标记的隐藏物件:场景亮起后仍藏着,等 reveal beat */
            /* 信息前置(2026-08-28)+三层详情(2026-08-30 P61/P63):谜面引用的事实由
               facts 行前置承载(接地检查保证真实),摘要/身份行殿后;原文与裸 URL 不再直出 */
            const detailText = layeredDetail(item, source);
            const mystery = '【' + (sc.title || '场景') + '】\n' + detailText;
            const ibid = inspectBeatFor(item.id);
            const nodeBase = {
              id: 'compiled-item-' + item.id,
              kind:
                'collectible compiled-item role-' +
                item.role +
                (isHidden ? ' compiled-hidden-item' : ''),
              name: item.sceneName || item.title,
              hint: '',
              x: baseX - 10 + ((index % 2) + (si % 2)) * 18,
              y: baseY + 9 + Math.floor(index / 2) * 10 + si * 7,
              parent: scId,
              hidden: true,
              startHidden: true,
              spawned: true,
              compiledItem: true,
              compiledItemId: item.id,
              compiledScene: scId,
              sceneIndex: si,
              compiledIndex: index,
              compiledRole: item.role,
              compiledReason: item.reason || '',
              url: source.url,
              compiledHidden: isHidden,
              detail: mystery,
            };
            if (ibid)
              nodeBase.state = [{ preClue: '#beat-' + ibid, detail: mystery }];
            nodes.push(nodeBase);
          });
      });
      /* 容器嵌套定位(S1):锚定统一在 roomLayoutBoard 之后执行(见下方 anchorHiddenItems) */
    } else {
      const containers = Array.isArray(level.containers) ? level.containers : [];
      const containerMap = {};
      containers.forEach(function (c, ci) {
        const cid = 'compiled-container-' + (c.id || ci);
        containerMap[c.id || ci] = cid;
        nodes.push({
          id: cid,
          kind: 'zone compiled-container',
          name: c.name || '容器 ' + (ci + 1),
          hint: '',
          x: 8,
          y: 15 + ci * 13,
          parent: levelId,
          hidden: true,
          startHidden: true,
          spawned: true,
          compiledContainer: true,
          containerId: c.id,
          compiledHidden: c.hidden === true,
          detail: c.desc || '「' + (c.name || '容器') + '」——打开看看里面有什么。',
        });
      });
      level.items.slice(0, 12).forEach(function (item, index) {
        const source = draft.items.find((x) => x.id === item.id) || {};
        const isHidden = item.hidden === true;
        /* 信息前置+三层详情(同 scenes 分支):facts 行承载谜面引用的事实 */
        const mystery = layeredDetail(item, source);
        const ibid = inspectBeatFor(item.id);
        const parentId = (item.container && containerMap[item.container]) || levelId;
        const nodeBase = {
          id: 'compiled-item-' + item.id,
          kind:
            'collectible compiled-item role-' +
            item.role +
            (isHidden ? ' compiled-hidden-item' : ''),
          name: item.sceneName || item.title,
          hint: '',
          x: 30 + (index % 3) * 20,
          y: 13 + Math.floor(index / 3) * 15,
          parent: parentId,
          hidden: true,
          startHidden: true,
          spawned: true,
          compiledItem: true,
          compiledItemId: item.id,
          compiledIndex: index,
          compiledRole: item.role,
          compiledReason: item.reason || '',
          url: source.url,
          compiledHidden: isHidden,
          detail: mystery,
        };
        if (ibid)
          nodeBase.state = [{ preClue: '#beat-' + ibid, detail: mystery }];
        nodes.push(nodeBase);
      });
    }
    nodes.push({
      id: 'compiled-exit',
      kind: 'action compiled-exit',
      name: '关卡出口',
      hint: '把最终结果拖到这里',
      x: 76,
      y: 78,
      parent: levelId,
      hidden: true,
      startHidden: true,
      spawned: true,
      compiledExit: true,
      detail: '完成所有必要步骤后，把最后改变过状态的物件拖到这里交付。出口不会提示你还差什么。',
    });
    state.nodes.push(...nodes);
    /* 空间分区摆位(2026-08-29):所有槽位——含隐藏物、容器物件、导入组——
       在 hydrate 时一次定死,reveal 只翻显隐永不再挪坐标。
       旧索引常量公式仅作兜底初值,这里统一覆盖。 */
    if (typeof roomLayoutBoard === 'function') {
      roomLayoutBoard(imported.id);
      roomLayoutBoard(levelId);
      const exitNode = nodes.find((n) => n.compiledExit);
      if (exitNode) {
        exitNode.x = 45;
        exitNode.y = 90;
      }
    }
    /* 容器嵌套锚定(S1,2026-08-30 重构):**必须在摆板之后**执行——roomLayoutBoard
       会把 zone 网格里的容器/源物件搬到最终位置,锚定若取摆板前的旧坐标,
       内容物就会散落在随机角落(实测:指南落到底部 42%/89%)。
       同一容器的多个内容物按确定性槽位扇出(右下/左下/右侧/左侧/上方),不叠点。
       2026-08-31 泛化:两条分支都执行——平铺关卡的游离隐藏物(无容器)同样锚到
       显形源物件旁,让「再点一下源物件」的显形交互成立;容器子件跳过(网格管理)。 */
    {
      const nodeById = {};
      nodes.forEach(function (n) {
        nodeById[n.id] = n;
      });
      const sibCount = {};
      const spawnSlots = [
        [7, 10],
        [-15, 10],
        [17, 0],
        [-17, 0],
        [7, -13],
      ];
      nodes.forEach(function (n) {
        if (!n.compiledHidden || !n.compiledItemId) return;
        if (typeof n.parent === 'string' && n.parent.indexOf('compiled-container-') === 0)
          return; /* 容器子件:位置由容器分区网格管理,不重复锚定 */
        const rs = revealSourceAll[n.compiledItemId];
        if (!rs) return;
        /* 解析优先级(2026-08-31):同名容器节点 > 同名物件节点 > 原始 id——
           显形源是容器(如『打开怀旧柜』)时,内容物应挂到容器上 */
        const src = nodeById['compiled-container-' + rs.src] || nodeById[rs.src]
          || nodeById['compiled-item-' + rs.src];
        if (!src || src.id === n.id) return;
        n.revealFromId = src.id;
        if (rs.via !== 'resultOn') return; /* use 来源:物件落在自己的房间槽位,不挂到源物件上 */
        const k = sibCount[src.id] || 0;
        sibCount[src.id] = k + 1;
        const slot = spawnSlots[k % spawnSlots.length];
        n.parent = src.id;
        n.x = Math.max(2, Math.min(92, src.x + slot[0]));
        n.y = Math.max(4, Math.min(90, src.y + slot[1]));
      });
    }
    ensureRevisitButton();
    compiled = {
      level,
      rules: compileRules(level),
      step: 0,
      beatIndex: 0,
      started: false,
      done: false,
      rootMode: false,
      inspected: new Set(),
      /* 分层探索(2026-08-31 需求方反馈):房间已走进状态——点根只亮房间,
         点房间才发现其中的物件;sceneId -> true */
      roomExplored: {},
      sequence: [],
      currentSeq: 0,
      sceneIndex: hasScenes ? 0 : -1,
      hasScenes,
    };
    window.__dbg = compiled;
  }
  hydrateImportedDraft = compiledLevelHydrate;

  function levelNode(id) {
    return get(id);
  }

  /* ---------- clue 门:beat 的前置是否满足 ---------- */
  function beatReady(beatId) {
    if (!beatId) return true;
    const level = compiled.level,
      beats = level.beats || [];
    const beat = beats.find((b) => b.id === beatId);
    if (!beat) return true;
    return (beat.requires || []).every(function (req) {
      const rb = beats.find((b) => b.id === req);
      return !rb || state.clues.has('beat-' + req);
    });
  }

  /* 全部当前可做 beat(前置已满足且未完成),按顺序列出——让玩家一眼看清有哪几条路可走 */
  function openBeats() {
    const level = compiled.level,
      beats = level.beats || [];
    return beats.filter(function (b) {
      return !state.clues.has('beat-' + b.id) && beatReady(b.id);
    });
  }

  function compiledObjective() {
    if (!compiled) return;
    const items = state.nodes.filter(
      (n) => (n.compiledResult || n.compiledItem) && !n.hidden && !n.used && !n.compiledConsumed,
    );
    const inv = $('inventory');
    if (inv)
      inv.innerHTML = items.length
        ? items
            .map((n) => '<span class="active">' + String(n.name).replace(/[&<>]/g, '') + '</span>')
            .join('')
        : '<span>尚无物件</span>';
    /* 进度统一(2026-08-29):顶栏读数与进度条改用关卡真实进度(完成的 beat / 总 beat),
       不再借用原生房间的 6 状态计数;舞台左上角横幅改写为"所在位置 + 单条引导" */
    const allBeats = compiled.level.beats || [];
    const doneBeats = allBeats.filter((b) => state.clues.has('beat-' + b.id)).length;
    const ds = $('doorStatus'),
      meter = $('meter');
    if (ds) ds.textContent = doneBeats + ' / ' + allBeats.length + ' 步';
    if (meter)
      meter.style.width = (allBeats.length ? (doneBeats / allBeats.length) * 100 : 0) + '%';
    if (!compiled.rootMode) return;
    let place,
      guide = '';
    if (compiled.done) {
      place = '关卡完成';
      guide = '把最后改变过状态的物件拖到出口,交付这次冒险。';
    } else if (compiled.started) {
      if (compiled.hasScenes) {
        const scenes = compiled.level.scenes || [];
        if (compiled.parallelRooms) {
          place = '自由探索 · ' + scenes.length + ' 个房间';
        } else {
          const sc = scenes[compiled.sceneIndex];
          place = sc ? '场景 ' + (compiled.sceneIndex + 1) + '/' + scenes.length + ' · ' + (sc.title || '') : '探索中';
        }
      } else {
        place = '房间里';
      }
      const opens = openBeats();
      if (opens.length === 1 && opens[0].action === 'deliver') {
        /* 通关指引点名(2026-08-31 需求方反馈:『把木盒拖到出口讲不通』)——
           只剩交付时,明确说出拖什么、拖到哪 */
        const raw = String((opens[0].uses || [])[0] || '').replace('result:', '');
        const node = state.nodes.find((n) => n.compiledItemId === raw) ||
          state.nodes.find((n) => n.compiledResultKey === 'result:' + raw);
        guide = '最后一步:把「' + (node ? node.name : '最终结果') + '」拖到「关卡出口」,放进凹槽交付。';
      } else {
        guide = opens.length
          ? opens[0].title + (opens.length > 1 ? '(还有 ' + (opens.length - 1) + ' 件可以并行推进)' : '')
          : '把最后的结果拖到关卡出口。';
      }
    } else {
      place = '入口';
      guide = '点击关卡入口,开始这场未命名冒险。';
    }
    const rs = $('roomState');
    if (rs) rs.textContent = place;
    const obj = $('objective');
    if (obj)
      obj.innerHTML =
        '<b>' + place + '</b>' + (guide ? '<br>' + guide : '') +
        '<span>素材都能被检查、组合或按顺序操作——猜错没有惩罚。</span>';
  }

  function levelStart() {
    if (!compiled) return;
    compiled.started = true;
    const root = levelNode('root');
    if (root && compiled.rootMode) root.generatedStarted = true;
    if (compiled.hasScenes) {
      if (compiled.level.parallelRooms === true) {
        /* 2026-08-29 原作式空间层次(P42):全房间同时亮出,非线性自由探索——
           推进由线索链(requires)承担,不再顺序换幕。
           2026-08-31 分层探索:点根只亮房间,点房间才见物件(exploreRoom)。 */
        compiled.parallelRooms = true;
        revealAllRooms(true);
        log('关卡开始。几间房间同时亮出——点开房间,看看里面有什么。', 'good');
      } else {
        /* 场景模式:只亮第一幕的场景节点+其物件;出口隐藏到最后一幕 */
        compiled.sceneIndex = 0;
        revealScene(0, true);
        log('关卡开始。你站在第一个场景里。解开它,才能继续深入。', 'good');
      }
    } else {
      /* 散落在房间里的物件+出口直接可见;容器是关闭的——点开容器才显形里面的东西;
         JSON 标记 hidden 的容器(如监狱的书架/大铁箱/门)开场不存在,要等回访发现 */
      state.nodes.forEach(function (n) {
        if (n.compiledContainer && !n.compiledHidden) {
          n.hidden = false;
          n.spawned = true;
          n.justArrived = true; /* 关卡开场:可打开的容器逐个亮出 */
        }
        if (!(n.compiledItem || n.compiledExit)) return;
        const inContainer =
          typeof n.parent === 'string' && n.parent.indexOf('compiled-container-') === 0;
        if (!inContainer && !(n.compiledHidden && !n.revealed)) {
          n.hidden = false;
          n.spawned = true;
          n.justArrived = true; /* 散落物件/出口开场显形也有出现动画 */
        }
      });
      log('关卡开始。房间里的东西触手可及；能打开的地方还要自己动手。', 'good');
    }
    if (compiled.rootMode) {
      const lv = levelNode('compiled-level');
      if (lv) lv.hidden = true; /* 自由创作路径:入口牌只有 root 一张,避免双入口 */
    }
    /* 2026-08-30(需求方反馈):入口牌不再挪到角落——"点击根节点后根节点飞走"
       的退场设计被否定,root 保持初始位置不动,子节点在它周围展开 */
    inspect(levelNode('compiled-level'));
    frontier('imported');
    /* 关卡开始:线索便签自动展开(提示有节奏,先让玩家看到入口) */
    if (window.__showHints) window.__showHints();
    /* 窄屏:自动缩小初始视野,分区纵堆才放得下(画布可平移/缩放查看) */
    if (window.innerWidth < 700 && typeof resetView === 'function') {
      view.scale = 0.8;
      view.x = ($('stage').clientWidth * 0.1);
      view.y = 0;
      applyView();
    }
    action();
    update();
    compiledObjective();
    roomRender();
    drawLinks();
  }

  /* ---------- 回访房间:reveal 就绪但未显现的东西在这里被"发现" ----------
     入口是工具条上的「环顾四周」按钮(以及点房间/场景节点),因为节点经常被物件网格盖住,
     点击不可靠。容器里未开封的物件不算"发现",仍要先打开那个容器。 */
  function revisitRoom() {
    /* 环顾四周 = 对**所有**节点各执行一次点击更新(2026-08-31 语义统一):
       每个节点只贡献它的下一级就绪子节点;未开启容器不代开。 */
    const found = [];
    const seen = new Set();
    state.nodes.forEach(function (n) {
      clickUpdate(n).forEach(function (m) {
        if (seen.has(m.id)) return;
        seen.add(m.id);
        found.push(m.name);
      });
    });
    if (found.length) {
      log('你环顾四周——多了些什么:' + found.join('、') + '。', 'good');
      toast('这里有了新变化。');
    } else {
      /* 合并入口(2026-08-31 需求方提议):环顾四周没有新发现时,顺次落下一条提示
         ——观察力经济不变(提示仍耗格,两次提示之间要先行动) */
      log('又看了一圈,没有新的变化。');
      if (typeof requestHint === 'function') {
        requestHint();
        if (window.__showHints) window.__showHints();
      }
    }
    action();
    update();
    compiledObjective();
    roomRender();
    drawLinks();
  }
  function ensureRevisitButton() {
    /* 元动作归位(2026-08-29):「环顾四周」从舞台右下移到顶栏 HUD——
       与重置并排,不再挤在画布工具里;id 与可见性不变(回归依赖真实点击它) */
    let tools = document.querySelector('.hud');
    if (!tools) {
      const st = document.getElementById('stage');
      if (!st) return;
      tools = document.createElement('div');
      tools.className = 'canvas-tools';
      st.appendChild(tools);
    }
    if (document.getElementById('revisitRoom')) return;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'revisitRoom';
    btn.className = 'reset';
    btn.textContent = '环顾四周';
    btn.title = '回头检查所有探索过的地方；没有新变化时,会顺着观察给你一条提示';
    btn.onclick = function () {
      if (typeof observeAround === 'function') observeAround();
      else if (compiled && compiled.started) revisitRoom();
    };
    const resetBtn = tools.querySelector('.reset');
    if (resetBtn) tools.insertBefore(btn, resetBtn);
    else tools.appendChild(btn);
  }

  /* 2026-08-29 空间层次 S3(P40/P42):并行房间发现式推进——
     房间 1 挂载即亮出;后房间在 lockedBy beat 完成后亮出(发现式探索);
     已发现房间永久保留可回访。
     2026-08-31 分层探索(需求方反馈):这里**只亮房间节点,不再连带亮出物件**——
     点根节点看到的是几间房,点开房间才"走进去"发现里面的东西(见 exploreRoom);
     藏在容器里的物件仍由谜题节奏(reveals + 环顾四周)显形。 */
  function revealAllRooms(isFirst) {
    const scenes = compiled.level.scenes || [];
    let changed = false;
    scenes.forEach(function (sc, si) {
      const z = levelNode('compiled-scene-' + (sc.id || si));
      if (!z) return;
      const discovered = si === 0 || sc.locked !== true || state.clues.has('beat-' + sc.lockedBy);
      if (discovered && z.hidden) {
        z.hidden = false;
        z.spawned = true;
        z.justArrived = true; /* 房间亮出也有出现动画 */
        changed = true;
        if (si > 0 && isFirst === false)
          log('新的房间亮出:「' + (sc.title || '') + '」——点开看看。', 'good');
      }
    });
    /* 出口:最后一个房间发现后亮出 */
    const lastSc = scenes[scenes.length - 1];
    if (lastSc) {
      const lz = levelNode('compiled-scene-' + (lastSc.id || scenes.length - 1));
      const exit = levelNode('compiled-exit');
      if (lz && !lz.hidden && exit && exit.hidden) {
        exit.hidden = false;
        exit.spawned = true;
        exit.justArrived = true;
        changed = true;
      }
    }
    if (changed || isFirst === true) {
      action();
      update();
      compiledObjective();
      roomRender();
      drawLinks();
    }
  }

  /* 走进一间房(2026-08-31 分层探索):首次点击房间节点时亮出其中可直接看见的
     物件(hidden 的仍等 reveals);之后点击退化为回看(revealReady 的隐藏物发现)。
     返回是否是首次走进。 */
  /* 「点击更新」原语(2026-08-31 理清环顾四周/回访,需求方裁定):
     对节点 n 执行一次点击更新,只显形它的**下一级就绪子节点**,返回新现形节点。
     三种形态:根/入口=直接挂在根上的就绪物;房间(zone)=首次走进亮出可见物件、
     之后=就绪隐藏物;物件/容器=就绪内容物(parent 挂靠或 revealFrom 指向)——
     **未开启的容器不由环顾代开**,必须玩家自己点(开柜才算发现)。 */
  function clickUpdate(n) {
    const found = [];
    if (!n || !compiled) return found;
    const reveal = (m) => {
      const was = m.hidden;
      m.hidden = false;
      m.revealed = true;
      m.spawned = true;
      /* 11.13 #6:visible 必须同步 revealed=true,否则 compiled-hidden-item
         的 opacity:0/pointer-events:none 仍挂在类上,物件"显形了却看不见" */
      if (was || !m.revealed) m.revealed = true;
      if (was) m.justArrived = true;
      found.push(m);
    };
    if ((n.id === 'root' && compiled.rootMode) || n.id === 'compiled-level') {
      state.nodes.forEach((m) => {
        if (m.hidden && m.revealReady && (m.parent === n.id || m.parent === 'compiled-level'))
          reveal(m);
      });
      return found;
    }
    if (n.compiledScene && n.kind && n.kind.includes('zone')) {
      const first = !compiled.roomExplored[n.id];
      if (first) compiled.roomExplored[n.id] = true;
      state.nodes.forEach((m) => {
        if (!m.compiledItem || m.compiledResult || m.compiledScene !== n.id) return;
        if (first && !m.compiledHidden && m.hidden) {
          reveal(m);
          return;
        }
        if (m.hidden && m.revealReady) reveal(m);
      });
      return found;
    }
    if (n.compiledItem || n.compiledResult) {
      if (n.compiledContainer && !n.opened) return found; /* 环顾不代开容器 */
      state.nodes.forEach((m) => {
        if (
          m.hidden &&
          m.revealReady &&
          m.compiledHidden &&
          (m.parent === n.id || m.revealFromId === n.id)
        )
          reveal(m);
      });
    }
    return found;
  }

  /* ---------- 场景推进:亮出第 si 幕;前序幕收起 ---------- */
  function revealScene(si, isFirst) {
    const scenes = compiled.level.scenes || [];
    if (si < 0 || si >= scenes.length) return;
    compiled.sceneIndex = si;
    const scId = 'compiled-scene-' + (scenes[si].id || si);
    /* 所有场景节点先隐藏(保留已解开的物件为 used 灰化态即可);已变身的产物节点跨场景保留(跟随玩家) */
    state.nodes
      .filter((n) => n.compiledScene && n.kind.includes('zone'))
      .forEach((n) => {
        n.hidden = true;
      });
    state.nodes
      .filter((n) => n.compiledItem && !n.compiledResult)
      .forEach((n) => {
        n.hidden = true;
      });
    /* 当前场景节点 + 其物件可见;但 LLM 标记 hidden 的物件仍藏着,等 reveal beat 显形(重进场景时,已被显形的不再藏) */
    const sc = levelNode(scId);
    if (sc) {
      sc.hidden = false;
      sc.spawned = true;
      sc.justArrived = true;
    }
    state.nodes
      .filter((n) => n.compiledItem && n.compiledScene === scId)
      .forEach((n) => {
        const was = n.hidden;
        n.hidden = n.compiledHidden && !n.revealReady;
        if (!n.hidden) {
          n.revealed = true;
          n.spawned = true;
          if (was) n.justArrived = true;
        }
      });
    /* 最后一幕才亮出口 */
    const isLast = si === scenes.length - 1;
    const exit = levelNode('compiled-exit');
    if (exit) {
      exit.hidden = !isLast;
      if (isLast) exit.spawned = true;
    }
    if (!isFirst && sc) {
      inspect(sc);
      log(
        '场景切换:「' +
          (scenes[si].title || '') +
          '」' +
          (scenes[si].description ? '——' + scenes[si].description.slice(0, 60) : ''),
        'good',
      );
    }
    action();
    update();
    compiledObjective();
    roomRender();
    drawLinks();
  }

  /* 当前场景的 beats 是否全部完成 */
  function sceneCleared(si) {
    const scenes = compiled.level.scenes || [];
    if (!scenes[si]) return true;
    return (scenes[si].beatIds || []).every((bid) => state.clues.has('beat-' + bid));
  }

  /* 检查是否应该进入下一幕 */
  function advanceScene() {
    if (!compiled || !compiled.hasScenes) return;
    if (compiled.parallelRooms) return; /* 并行房间:无顺序换幕(2026-08-29 P40) */
    const scenes = compiled.level.scenes || [];
    if (compiled.sceneIndex < scenes.length - 1 && sceneCleared(compiled.sceneIndex)) {
      revealScene(compiled.sceneIndex + 1, false);
      toast('这个场景解开了。前面的路打开了。');
    }
  }

  function compiledHandle(n) {
    if (!compiled || !n) return false;
    /* 关卡入口:未开始则开始;已开始则查看关卡说明——不再触发全局回访
       (回访只由「环顾四周」按钮或点开具体容器触发,避免一次把全部就绪物件弹出) */
    if ((n.id === 'root' && compiled.rootMode) || n.id === 'compiled-level') {
      if (!compiled.started) {
        levelStart();
        return true;
      }
      inspect(n);
      /* 环视房间(2026-08-31 精确语义,需求方裁定):点节点只现形**它自己的、
         已就绪的直接子节点**——子节点的子节点(如挂钟容器里的断钟摆)与根无关,
         由回访所属容器显形。root 直接子节点:教程关的便签/抽屉等 */
      const names = clickUpdate(n).map((m) => m.name); /* 只现形自己的下一级就绪子节点 */
      if (names.length)
        log('环视「' + (n.name || '房间') + '」——多了些什么:' + names.join('、') + '。', 'good');
      action();
      update();
      compiledObjective();
      roomRender();
      drawLinks();
      return true;
    }
    /* 场景节点:首次点击=走进(亮出其中可直接看见的物件);之后=回看,
       发现 reveal 就绪的隐藏物件 */
    if (n.compiledScene && n.kind && n.kind.includes('zone')) {
      const firstStep = !compiled.roomExplored[n.id];
      const found = clickUpdate(n).map((m) => m.name); /* 首次=走进亮可见物,之后=就绪隐藏物 */
      inspect(n);
      if (found.length)
        log('回看「' + n.name + '」——多了些什么:' + found.join('、') + '。', 'good');
      if (compiled.hasScenes && !firstStep) {
        const sc = (compiled.level.scenes || [])[n.sceneIndex];
        if (sc && n.sceneIndex === compiled.sceneIndex)
          log('你环顾「' + (sc.title || '这个场景') + '」。' + (sc.description || ''), 'good');
        else toast('那个场景已经在身后了。');
      }
      action();
      update();
      compiledObjective();
      roomRender();
      return true;
    }
    if (n.compiledExit) {
      if (compiled.done) {
        ending();
      } else {
        toast('出口还没有回应。有步骤还没完成。');
        log('出口没有响应。回想哪条素材还没有被正确使用。', 'warn');
      }
      return true;
    }
    if (!n.compiledItem && !n.compiledResult) return false;
    if (!compiled.started) {
      toast('先点击当前关卡入口开始。');
      return true;
    }
    /* 场景模式:顺序换幕时非当前幕的物件不可操作(理论上已隐藏,防御);
       并行房间(P40)全房间可自由探索,守卫放行——此前 sceneIndex 恒 0
       会把第 2+ 个房间的物件全部误拦。已变身的产物跨场景可继续使用。 */
    if (
      compiled.hasScenes &&
      !compiled.parallelRooms &&
      n.compiledScene &&
      n.compiledScene !==
        'compiled-scene-' +
          ((compiled.level.scenes || [])[compiled.sceneIndex]?.id || compiled.sceneIndex) &&
      !n.compiledResult
    ) {
      toast('这个物件不在这个场景里。');
      return true;
    }
    inspect(n);
    action();
    /* 容器开启(P11/P42,原作模式 2026-08-30):点开藏有内容物的物件/容器,
       其就绪的隐藏内容物**就地显形**——内容物已被 S1 锚定在此容器旁,
       不再依赖全局「环顾四周」才能看到容器里有什么 */
    const opened = [];
    state.nodes.forEach(function (m) {
      /* revealFromId:use 来源的显形物不挂 在源物件下,但同样由『再点一下源物件』显形 */
      if (m.hidden && m.revealReady && m.compiledHidden && (m.parent === n.id || m.revealFromId === n.id)) {
        m.hidden = false;
        m.revealed = true;
        m.spawned = true;
        m.justArrived = true;
        opened.push(m.name);
      }
    });
    if (opened.length)
      log('打开「' + n.name + '」——里面藏着:' + opened.join('、') + '。', 'good');
    /* 检查素材:给角色提示,如果是锁/转化类且前置未满足,提示"还用不了" */
    if (n.compiledItem) {
      const role = n.compiledRole,
        reason = n.compiledReason;
      if (role === 'lock' || role === 'transform') {
        log('检查"' + n.name + '":' + (reason || '它需要某个前置结果才起作用。'));
      } else {
        log('观察到"' + n.name + '"。' + (reason || '记录它的事实。'));
      }
    }
    if (n.compiledResult) log('"' + n.name + '"是已完成的状态。它可能还要继续被使用。');
    update();
    roomRender();
    return true;
  }

  /* 帮助:节点 id → 素材 key;组合产物 key=result:<产出它的 beatId>,供后续 beat 的 uses 引用 */
  function itemKey(node) {
    return node.compiledResult
      ? node.compiledResultKey || '__result__' + (node.compiledIndex ?? '')
      : String(node.id).replace('compiled-item-', '');
  }

  /* 原作回访机制的核心:beat 触发后不生成新节点,而是把目标节点原位更新为产物状态——
     节点名/键/详情更新,位置不变,继续参与后续交互(原作节点 state[] + preClue 门控的等价物) */
  function morphNode(node, rule) {
    if (!node) return null;
    node.compiledResultKeys = node.compiledResultKeys || [];
    const nk = 'result:' + rule.need;
    if (!node.compiledResultKeys.includes(nk))
      node.compiledResultKeys.push(nk); /* 多身份:节点可被多次变身,中间产物不丢失 */
    node.compiledResultKey = nk;
    node.compiledResult = true;
    node.morphedFrom = node.name;
    node.justChanged = true; /* 变化过渡动画标记:roomRender 加 .changed 类后清除 */
    node.name = rule.product || '状态变化 · ' + (rule.title || '新状态');
    node.hint = '状态已更新,可能继续参与后续步骤';
    node.detail = (node.detail || '') + '\n—— 状态变化 ——\n' + (rule.title || '');
    /* 若节点有 preClue 门控的 state(如 inspect 身份层),渲染走 nodeVariant 取 state.detail——
       同步把"状态变化"追加进当前生效 state,否则 morph 的详情(含新线索)会被 state 盖住看不到 */
    if (Array.isArray(node.state)) {
      const active = node.state
        .filter(function (s) {
          return hasClue(s.preClue);
        })
        .at(-1);
      if (active && active !== node && active.detail !== undefined)
        active.detail = (active.detail || '') + '\n—— 状态变化 ——\n' + (rule.title || '');
    }
    node.justArrived = true; /* 触发一次出现动画,提示"这个节点刚刚变了" */
    return node;
  }

  /* 节点的全部身份:当前主身份 + 历史产物身份 + 原始素材 id(combine 用任一身份匹配) */
  function nodeKeys(node) {
    if (!node) return [];
    const set = new Set();
    if (Array.isArray(node.compiledResultKeys)) node.compiledResultKeys.forEach((k) => set.add(k));
    if (node.compiledResultKey) set.add(node.compiledResultKey);
    if (node.compiledItemId) set.add(String(node.compiledItemId));
    set.add(String(node.id).replace('compiled-item-', ''));
    return [...set];
  }

  function compiledUse(aid, bid) {
    if (!compiled) return false;
    const a = levelNode(aid),
      b = levelNode(bid);
    if (!a || !b) return false;
    if (
      !(a.compiledItem || a.compiledResult) ||
      !(b.compiledItem || b.compiledResult || b.compiledExit)
    )
      return false;
    if (!compiled.started) {
      toast('先点击当前关卡入口开始。');
      return true;
    }
    /* --- 出口交付 --- */
    if (aid === 'compiled-exit' || bid === 'compiled-exit') {
      const item = aid === 'compiled-exit' ? b : a;
      const key = itemKey(item);
      const rule = compiled.rules.delivers.find(function (r) {
        return (
          beatReady(r.need) &&
          !state.clues.has(r.clue) &&
          (r.item === key || item.compiledResult || key === '__result__')
        );
      });
      if (rule) {
        item.used = true;
        item.hidden = true; /* 交付后结果离场,避免 spent 节点遮挡出口 */
        state.clues.add(rule.clue);
        log('出口步骤完成:' + (rule.title || '素材已经交付。'), 'good');
        triggerReveals(rule.need);
        finishIfDone();
        action();
        update();
        compiledObjective();
        roomRender();
        return true;
      }
      if (compiled.done) {
        toast('出口已经接受过交付。点击出口离开。');
        return true;
      }
      toast('出口拒绝了这件东西。它还不是最终结果。');
      log('出口没有响应。这件素材还需要被进一步使用。', 'warn');
      action();
      return true;
    }
    /* --- 顺序锁:点击型,拖动给提示 --- */
    if (compiled.rules.sequences.length) {
      const openSeq = compiled.rules.sequences.find(function (r) {
        return beatReady(r.need) && !state.clues.has(r.clue);
      });
      const aRaw = a.compiledItemId ? String(a.compiledItemId) : null,
        bRaw = b.compiledItemId ? String(b.compiledItemId) : null;
      if (
        openSeq &&
        (openSeq.order.includes(itemKey(a)) ||
          (aRaw && openSeq.order.includes(aRaw)) ||
          openSeq.order.includes(itemKey(b)) ||
          (bRaw && openSeq.order.includes(bRaw)))
      ) {
        toast('顺序类素材:按正确顺序逐个点击检查,不是拖动。');
        return true;
      }
    }
    /* --- 组合表:按节点任意身份匹配(节点可多次变身,中间产物身份保留) --- */
    const rule = compiled.rules.combines.find(function (r) {
      if (!(beatReady(r.need) && !state.clues.has(r.clue))) return false;
      const ka = nodeKeys(a),
        kb = nodeKeys(b);
      return (
        (ka.includes(r.pair[0]) && kb.includes(r.pair[1])) ||
        (ka.includes(r.pair[1]) && kb.includes(r.pair[0]))
      );
    });
    if (rule) {
      state.clues.add(rule.clue);
      /* 目标节点原位更新为产物(原作:排水管→棍子/钥匙→钥匙/镣铐→解开的镣铐),源素材留在原地。
         resultOn 固定 morph 目标,与拖动方向无关(玩家从哪边拖都一样) */
      const target = rule.resultOn
        ? state.nodes.find(
            (x) => (x.compiledItem || x.compiledResult) && nodeKeys(x).includes(rule.resultOn),
          )
        : null;
      morphNode(target || b, rule);
      /* consume:声明消耗的源素材用完即消失(如发条),不可再拖 */
      if (rule.consume && rule.consume.length) {
        const consumed = [];
        rule.consume.forEach(function (id) {
          const node = state.nodes.find(
            (x) =>
              x.compiledItem &&
              (String(x.compiledItemId || '') === id ||
                String(x.id).replace('compiled-item-', '') === id),
          );
          if (node) {
            node.hidden = true;
            node.used = true;
            node.compiledConsumed = true;
            consumed.push(node.morphedFrom || node.name);
          }
        });
        if (consumed.length) log('用掉了:' + consumed.join('、') + '。', 'warn');
      }
      log(
        '组合成功:' +
          (rule.title || '素材关系已确认。') +
          '「' +
          String((target || b).morphedFrom) +
          '」变成了「' +
          (target || b).name +
          '」。',
        'good',
      );
      triggerReveals(rule.need);
      finishIfDone();
      action();
      update();
      compiledObjective();
      roomRender();
      drawLinks();
      return true;
    }
    /* --- 错误组合:可恢复反馈(局部轻推两张物件卡,不再全屏震动);
         轻推必须放在 roomRender 之后——重渲染会重建节点元素,先推会被抹掉 --- */
    toast('这两个东西放在一起没有反应。');
    log(
      '"' +
        a.name +
        '"和"' +
        b.name +
        '"没有产生可观察的变化。也许顺序不对,也许其中之一还不到用的时候。',
      'warn',
    );
    action();
    roomRender();
    nudge([nodeEl(a && a.id), nodeEl(b && b.id)]);
    return true;
  }

  /* ---------- 点击:处理 inspect 与 sequence ---------- */
  /* 2026-08-31 断电锁反馈(需求方实测 123.room.json):机关的目标身份还没被
     变身出来时(如终端要先通电),password/angle/morse 三分支按 nodeKeys 全部
     匹配不到,点击落空无任何反馈。这里反查机关规则的 result: 前置——若缺失的
     产物恰好落在被点物件身上,明确告诉玩家缺哪一步、会得到什么。 */
  function machinePendingBlocker(n) {
    const keys = nodeKeys(n);
    const rules = [].concat(
      compiled.rules.passwords || [],
      compiled.rules.angles || [],
      compiled.rules.morses || [],
    );
    for (let i = 0; i < rules.length; i++) {
      const r = rules[i];
      if (state.clues.has(r.clue)) continue; /* 已解开 */
      if (keys.includes(r.item)) continue; /* 已就绪(面板会正常打开) */
      const itemStr = String(r.item || '');
      if (itemStr.indexOf('result:') !== 0) continue;
      const beat = (compiled.level.beats || []).find(function (b) {
        return String(b.id) === itemStr.slice(7);
      });
      if (!beat) continue;
      /* 产物落在哪件物件上:优先非 result 的 resultOn,回退 uses 里最后一个实体素材 */
      const ro = beat.resultOn && !String(beat.resultOn).startsWith('result:') ? String(beat.resultOn) : '';
      const target =
        ro ||
        (beat.uses || [])
          .filter((u) => !String(u).startsWith('result:'))
          .slice(-1)
          .join('');
      if (target && keys.includes(target)) return { title: beat.title || '', product: beat.product || '' };
    }
    return null;
  }
  const baseHandle = compiledHandle;
  compiledHandle = function (n) {
    if (!compiled || !n) return baseHandle(n);
    if (n.compiledContainer) {
      /* 打开/回访容器:直属于容器的内容物随开启逐个发现——原作 preClue 子节点过滤的等价物。
         例外:被某个 beat 的 reveals 显形链盯上的物件(如监狱铁箱里的锯子要等转盘锁)
         仍按 revealReady 门控。2026-08-30 修复:此前一律要求 revealReady,
         导致"只藏在容器里、没有显形 beat"的内容物(bear 的熊曰工具)永远开不出来。 */
      const revealGated = new Set();
      (compiled.level.beats || []).forEach(function (b) {
        (b.reveals || []).forEach(function (r) {
          revealGated.add(String(r).replace('result:', ''));
        });
      });
      const first = !n.opened;
      n.opened = true;
      /* 容器自身的检视 beat 随开柜完成(2026-08-31):『打开怀旧柜』这类以容器为
         目标的 inspect 步,此前只在物件分支匹配——容器节点永远走不到,其 reveals
         的内容物 revealReady 永远不成立,开柜也不显形(教程关 demo 实测) */
      const selfInspect = (compiled.rules.inspects || []).find(function (r) {
        return (
          beatReady(r.need) &&
          !state.clues.has(r.clue) &&
          r.ids.some(function (id) {
            /* 容器节点 id 带 compiled-container- 前缀:裸 id 与全 id 都参与匹配 */
            const full = String(n.id);
            return nodeKeys(n).includes(String(id)) || full === 'compiled-container-' + String(id) || full === String(id);
          })
        );
      });
      if (selfInspect) {
        state.clues.add(selfInspect.clue);
        if (selfInspect.product) {
          const tn = levelNode(n.id);
          if (tn) {
            const before = tn.name;
            morphNode(tn, selfInspect);
            if (tn.name !== before) log('「' + before + '」变成了「' + tn.name + '」。', 'good');
          }
        }
        triggerReveals(selfInspect.need);
      }
      const found = [];
      state.nodes
        .filter((m) => m.compiledItem && m.parent === n.id)
        .forEach(function (m) {
          const key = itemKey(m);
          if (m.hidden && (m.revealReady || !revealGated.has(key))) {
            m.hidden = false;
            m.revealed = true;
            m.spawned = true;
            m.justArrived = true; /* 开箱/回访显形的内容物播一次出现动画 */
            found.push(m.name);
          }
        });
      if (first)
        log(
          found.length
            ? '打开了「' + n.name + '」——里面有:' + found.join('、') + '。'
            : '打开了「' + n.name + '」,里面空空如也。',
          'good',
        );
      else if (found.length)
        log('回访「' + n.name + '」——多了些什么:' + found.join('、') + '。', 'good');
      else log('「' + n.name + '」里没有新的变化。');
      inspect(n);
      action();
      update();
      compiledObjective();
      roomRender();
      return true;
    }
    if ((n.compiledItem || n.compiledResult) && compiled.started) {
      const key = itemKey(n);
      /* knock:连按计数机关(2026-08-31,原作 m4 裂缝/铁窗的等价物)——
         前置就绪后连续点击同一物件 count 次,计满即完成:原位变身+显形(reveals)。
         计数进度存 compiled.knockProgress,点别处不清零(区别于顺序锁的整组重来)。
         反馈口径(P74 修订,需求方裁定):可发现性来自物件自身(『破碎的墙』这类标题/质感),
         文案绝不提示次数——反馈用递进拟声+节点轻推,不显示 x/3 计数器 */
      const openKnock = (compiled.rules.knocks || []).find(function (r) {
        return beatReady(r.need) && !state.clues.has(r.clue) && nodeKeys(n).includes(r.item);
      });
      if (openKnock) {
        compiled.knockProgress = compiled.knockProgress || {};
        const kKey = openKnock.clue;
        compiled.knockProgress[kKey] = (compiled.knockProgress[kKey] || 0) + 1;
        const knockLadder = [
          '咚——它空空作响。',
          '咚咚——有什么东西松动了。',
          '咚咚咚——声音越来越实,它快掉了。',
        ];
        const done = compiled.knockProgress[kKey] >= openKnock.count;
        if (!done) {
          nudge([nodeEl(n.id)]);
          log(
            knockLadder[Math.min(compiled.knockProgress[kKey] - 1, knockLadder.length - 1)],
            'good',
          );
          action();
          return true;
        }
        state.clues.add(openKnock.clue);
        compiled.knockProgress[kKey] = 0;
        morphNode(n, openKnock);
        log('最后一下——' + (openKnock.title || '它弹开了。'), 'good');
        triggerReveals(openKnock.need);
        finishIfDone();
        action();
        update();
        compiledObjective();
        roomRender();
        return true;
      }
      /* password:点击密码盘物件 → 随时弹出密码盘(前置只影响线索可得性,不影响解锁——答案正确即通过) */
      const openPass = compiled.rules.passwords.find(function (r) {
        /* v7.4:全身份匹配——同一物件先被摩斯/角度变身后再上密码锁,变身后的 key 是 result:*,
           按单一 key 匹配不到原始 id,第二把锁永远打不开(废弃医院实测) */
        return !state.clues.has(r.clue) && nodeKeys(n).includes(r.item);
      });
      if (openPass) {
        openKeypad({
          digits: openPass.expected.length,
          colors: openPass.colors,
          expected: openPass.expected,
          kicker: n.name,
          title: openPass.title,
          copy: n.compiledReason || '输入密码打开' + (n.name || '它'),
          onSuccess: function () {
            state.clues.add(openPass.clue);
            morphNode(n, openPass);
            log(
              '密码正确:' +
                (openPass.title || '机关打开了。') +
                '「' +
                String(n.morphedFrom) +
                '」变成了「' +
                n.name +
                '」。',
              'good',
            );
            triggerReveals(openPass.need);
            finishIfDone();
            action();
            update();
            compiledObjective();
            roomRender();
          },
          onFail: function () {
            log('密码不对。机关没有反应。', 'warn');
          },
        });
        return true;
      }
      /* angle:点击旋钮物件 → 随时弹出角度旋钮(答案正确即通过) */
      const angleRule = compiled.rules.angles.find(function (r) {
        return !state.clues.has(r.clue) && nodeKeys(n).includes(r.item);
      });
      if (angleRule) {
        openAngle({
          angles: angleRule.angles,
          precision: angleRule.precision,
          labels: angleRule.labels,
          kicker: n.name,
          title: angleRule.title,
          copy: n.compiledReason || '把旋钮转到正确的角度。',
          onSuccess: function () {
            state.clues.add(angleRule.clue);
            morphNode(n, angleRule);
            log(
              '角度正确:' +
                (angleRule.title || '机关打开了。') +
                '「' +
                String(n.morphedFrom) +
                '」变成了「' +
                n.name +
                '」。',
              'good',
            );
            triggerReveals(angleRule.need);
            finishIfDone();
            action();
            update();
            compiledObjective();
            roomRender();
          },
        });
        return true;
      }
      /* morse:点击电报机物件 → 随时弹出摩斯输入(答案正确即通过) */
      const morseRule = compiled.rules.morses.find(function (r) {
        return !state.clues.has(r.clue) && nodeKeys(n).includes(r.item);
      });
      if (morseRule) {
        openMorse({
          code: morseRule.code,
          kicker: n.name,
          title: morseRule.title,
          copy: n.compiledReason || '输入正确的摩斯码。',
          onSuccess: function () {
            state.clues.add(morseRule.clue);
            morphNode(n, morseRule);
            log(
              '摩斯码正确:' +
                (morseRule.title || '机关打开了。') +
                '「' +
                String(n.morphedFrom) +
                '」变成了「' +
                n.name +
                '」。',
              'good',
            );
            triggerReveals(morseRule.need);
            finishIfDone();
            action();
            update();
            compiledObjective();
            roomRender();
          },
          onFail: function () {
            log('摩斯码不对。机关没有反应。', 'warn');
          },
        });
        return true;
      }
      /* sequence:开放顺序锁——按原始素材身份匹配,节点变身后仍能参与顺序(原作同节点多状态的等价物) */
      const openSeq = compiled.rules.sequences.find(function (r) {
        return beatReady(r.need) && !state.clues.has(r.clue);
      });
      const seqKey = n.compiledItemId ? String(n.compiledItemId) : key;
      if (openSeq && openSeq.order.includes(seqKey)) {
        const expected = openSeq.order[compiled.sequence.length];
        if (seqKey !== expected) {
          compiled.sequence = [];
          compiled.currentSeq = 0;
          const wantNode = state.nodes.find(
            (x) =>
              (x.compiledItemId ? String(x.compiledItemId) : itemKey(x)) === expected && !x.hidden,
          );
          log('顺序不对。这一组从第一条重新开始。', 'warn');
          toast('顺序不对，先从「' + (wantNode ? wantNode.name : expected) + '」开始回应。');
          action();
          return true;
        }
        compiled.sequence.push(seqKey);
        inspect(n);
        if (compiled.sequence.length >= openSeq.order.length) {
          state.clues.add(openSeq.clue);
          compiled.sequence = [];
          log('顺序确认:' + (openSeq.title || '这一组按正确顺序回应了。'), 'good');
          /* sequence 产物与 combine 对称:resultOn 声明时 morph 到指定节点,否则最后一个回应节点原位更新,产物可被 result:<beatId> 引用 */
          const seqTarget = openSeq.resultOn
            ? state.nodes.find(
                (x) =>
                  (x.compiledItem || x.compiledResult) && nodeKeys(x).includes(openSeq.resultOn),
              )
            : null;
          morphNode(seqTarget || n, openSeq);
          triggerReveals(openSeq.need);
          finishIfDone();
          action();
          update();
          compiledObjective();
          roomRender();
          return true;
        }
        log('"' + n.name + '"回应了。继续按顺序。');
        action();
        return true;
      }
      /* inspect/revisit beat:点击即弹详情(检查前见谜面,完成后见身份层),产生可感知的信息增量 */
      /* v7.2:观察匹配用节点全部身份(原始 id+历史产物身份)——先组合变身、再回访观察是合法链序
        (r3 实测:b4 被组合变身后 key 变成 result:*,按单一 key 匹配不到原始 id,观察步永远无法完成) */
      const openInspect = compiled.rules.inspects.find(function (r) {
        return (
          beatReady(r.need) &&
          !state.clues.has(r.clue) &&
          r.ids.some(function (id) {
            return nodeKeys(n).includes(String(id));
          })
        );
      });
      if (openInspect) {
        const firstTime = !compiled.inspected.has(key);
        inspect(n); /* 弹详情面板:此刻显示谜面层 */
        if (firstTime) {
          nodeKeys(n).forEach(function (k2) {
            compiled.inspected.add(k2);
          });
          log('观察到"' + n.name + '"。' + (openInspect.title || ''));
        } else log('已经检查过了。看看这一步还有什么没看过。');
        if (
          openInspect.ids.every(function (id) {
            return compiled.inspected.has(id);
          })
        ) {
          state.clues.add(openInspect.clue);
          compiled.inspected = new Set();
          /* 检视产物落地(2026-08-31):product 存在时物件原位变身,并像组合那样
             广播更名——否则玩家看不到『台灯』变成了『亮着的台灯』 */
          if (openInspect.product) {
            const target = levelNode('compiled-item-' + openInspect.resultOn) || n;
            const before = target.name;
            morphNode(target, openInspect);
            if (target.name !== before)
              log('「' + before + '」变成了「' + target.name + '」。', 'good');
          }
          inspect(n); /* 身份层刚解锁,立即刷新面板:真名/域名/收藏时刻 */
          log('完成:' + (openInspect.title || '观察完成。') + '', 'good');
          triggerReveals(openInspect.need);
          finishIfDone();
        }
        action();
        update();
        compiledObjective();
        roomRender();
        return true;
      }
      /* 断电锁:机关未就绪时的可诊断反馈(取代旧的静默落空) */
      const pending = machinePendingBlocker(n);
      if (pending) {
        const msg =
          '「' +
          n.name +
          '」没有反应——它还没就绪:先完成「' +
          pending.title +
          '」' +
          (pending.product ? '(得到「' + pending.product + '」)' : '') +
          '。';
        log(msg, 'warn');
        toast(msg);
        inspect(n); /* 仍打开详情:锁面的谜面/状态本身就是线索 */
        return true;
      }
    }
    return baseHandle(n);
  };

  /* beat 完成后:reveals 列表里的隐藏物件/容器只标记"就绪",不自动出现——
     玩家必须回访包含它的空间(再点房间/容器/场景)才会发现它们。
     这是原作 preClue 门控 + 父节点点击渲染子节点 的行为等价物。
     2026-08-31 体验修复(需求方反馈"只能盲点环顾四周"):提示语指明变化位置——
     容器嵌套的报容器名,其余报所在房间名,玩家知道该去哪点。 */
  function triggerReveals(beatId) {
    const ids = (compiled.rules.reveals || {})[beatId];
    if (!ids || !ids.length) return;
    const places = [];
    let readied = 0;
    ids.forEach(function (id) {
      const node = levelNode('compiled-item-' + id) || levelNode('compiled-container-' + id);
      if (!node) return;
      node.revealReady = true;
      readied++;
      let place = '';
      if (typeof node.parent === 'string' && node.parent.indexOf('compiled-') === 0) {
        const pc = levelNode(node.parent);
        if (pc && pc !== node) place = '「' + (pc.name || '') + '」里';
      }
      if (!place && node.compiledScene) {
        const z = levelNode(node.compiledScene);
        if (z) place = '「' + (z.name || '') + '」里';
      }
      if (place && places.indexOf(place) < 0) places.push(place);
    });
    if (readied)
      log(
        places.length
          ? '有什么东西的状态变了——' + places.join('、') + '似乎多了什么，点开看看。'
          : '有什么东西的状态变了。也许该回头再看看。',
        'good',
      );
  }
  function finishIfDone() {
    const beats = compiled.level.beats || [];
    const allDone = beats.every(function (b) {
      return state.clues.has('beat-' + b.id);
    });
    /* 场景模式:当前幕完成时推进下一幕 */
    if (compiled.hasScenes) {
      if (compiled.parallelRooms) revealAllRooms(false);
      else advanceScene();
    }
    /* 只剩交付未做时也应亮出口——否则"隐形出口收不了货"会把关卡锁死 */
    const exit = levelNode('compiled-exit');
    const restDone = beats
      .filter((b) => b.action !== 'deliver')
      .every((b) => state.clues.has('beat-' + b.id));
    if (exit && restDone && !compiled.done) exit.hidden = false;
    if (allDone && !compiled.done) {
      compiled.done = true;
      toast('关卡出口已开放。');
      log('所有步骤都完成了。出口亮起。', 'good');
      frontier('final');
    }
  }

  const previousHandle = roomHandle;
  roomHandle = function (n) {
    if (n && n.id === 'imported-room') {
      previousHandle(n);
      const level = levelNode('compiled-level');
      if (level) {
        level.hidden = false;
        roomArrange(level.parent);
        roomRender();
        drawLinks();
        log('可玩关卡已经出现。点击它开始。', 'good');
      }
      return;
    }
    if (compiledHandle(n)) return;
    previousHandle(n);
  };
  const previousUse = roomUse;
  roomUse = function (aid, bid) {
    window.__lastUseTarget = bid; /* 谜题面板锚定:记住被使用的目标节点 */
    if (compiledUse(aid, bid)) return;
    previousUse(aid, bid);
  };
  const previousReset = roomReset;
  roomReset = function () {
    compiled = null;
    previousReset();
    compiledLevelHydrate();
    roomRender();
    drawLinks();
  };
  roomReset();
  roomRender();

  /* 挂载即出关卡口径(2026-08-29):mountLevel 会调 frontier('imported')——
     在编译关卡存在时补触发一次 compiledObjective,让顶栏/横幅在点击入口之前
     就显示本关的步数与引导,而不是原生房间的"0/6 个状态" */
  if (typeof window.frontier === 'function') {
    const prevFrontier = window.frontier;
    window.frontier = function (id) {
      prevFrontier(id);
      if (compiled) compiledObjective();
    };
  }

  window.__favoriteRoomRuntime = {
    /* 统一观察入口(2026-08-31):revisitRoom 在 IIFE 内,room02 的 observeAround
       经此公开入口调用(环顾四周与提示合并后的唯一空间回访通道) */
    lookAround: function () {
      revisitRoom();
    },
    hasCompiledLevel: function () {
      return !!compiled; /* 进度条单一写方守卫:编译关卡在跑时原生 HUD 不再写 meter */
    },
    snapshot: function () {
      return compiled
        ? {
            version: 3,
            step: compiled.step,
            beatIndex: compiled.beatIndex,
            started: compiled.started,
            done: compiled.done,
            clues: [...state.clues],
            /* 11.12 #4:并行房间模式进快照——恢复口径不依赖 localStorage 草稿的新旧 */
            parallelRooms: compiled.level ? compiled.level.parallelRooms === true : false,
            /* 分层探索(2026-08-31):已走进的房间随档恢复;旧档无此字段,
               恢复时按全部已探索处理(与旧行为一致) */
            explored: Object.keys(compiled.roomExplored || {}),
          }
        : null;
    },
    activateRoot: function (title, detail) {
      if (!compiled) return false;
      const root = levelNode('root'),
        levelNodeValue = levelNode('compiled-level');
      if (!root) return false;
      compiled.rootMode = true;
      root.generatedRoot = true;
      root.generatedStarted = false;
      root.kind = 'zone compiled-root';
      root.name = title || compiled.level.title || '收藏关卡';
      root.hint = '点击开始,房间亮出';
      root.detail = detail || compiled.level.premise || '把收藏变成一次可行动的探索。';
      root.hidden = false;
      ['shelf', 'desk', 'wall', 'exit', 'imported-room'].forEach((id) => {
        const node = levelNode(id);
        if (node) node.hidden = true;
      });
      if (levelNodeValue) {
        levelNodeValue.hidden = true;
        levelNodeValue.parent = 'root';
      }
      return true;
    },
    restore: function (snapshot) {
      if (!compiled || !snapshot) return false;
      const compatible = snapshot.version === 3;
      compiled.started = compatible && !!snapshot.started;
      compiled.done = compatible && !!snapshot.done;
      if (compatible && Array.isArray(snapshot.clues))
        (snapshot.clues || []).forEach((c) => state.clues.add(c));
      /* 恢复组合/顺序结果:目标节点原位更新(与 morphNode 一致,幂等) */
      if (compatible) {
        compiled.rules.combines.forEach(function (r) {
          if (state.clues.has(r.clue)) {
            morphNode(levelNode('compiled-item-' + r.resultOn), r);
            (r.consume || []).forEach(function (id) {
              const node = levelNode('compiled-item-' + id);
              if (node) {
                node.hidden = true;
                node.used = true;
                node.compiledConsumed = true;
              }
            });
          }
        });
        compiled.rules.sequences.forEach(function (r) {
          if (state.clues.has(r.clue)) morphNode(levelNode('compiled-item-' + r.resultOn), r);
        });
        /* knock 完成的原位重放(与 combine/sequence 对齐,续游戏后变身不丢) */
        (compiled.rules.knocks || []).forEach(function (r) {
          if (state.clues.has(r.clue)) morphNode(levelNode('compiled-item-' + r.resultOn), r);
        });
        /* S4 存档保真(审查 11.2.3):重放 password/angle/morse 的原位变身——
           否则续游戏后锁节点缺 result:<beatId> 身份,后续引用卡死 */
        (compiled.rules.passwords || []).concat(
          compiled.rules.angles || [],
          compiled.rules.morses || []
        ).forEach(function (r) {
          if (state.clues.has(r.clue)) {
            const node = levelNode('compiled-item-' + r.item);
            if (node) morphNode(node, r);
          }
        });
        /* 恢复已显形的隐藏物件 */
        const rev = compiled.rules.reveals || {};
        Object.keys(rev).forEach(function (bid) {
          if (state.clues.has('beat-' + bid))
            rev[bid].forEach(function (id) {
              const node = levelNode('compiled-item-' + id);
              if (node) {
                node.revealed = true;
              }
            });
        });
      }
      if (compiled.started) {
        /* 分层探索恢复(2026-08-31):新档带 explored 清单——只恢复已走进房间的
           物件可见性,未走进的房间保持「只见其门」;旧档无字段按全部已探索处理
           (与旧行为一致,变身产物跨房间保留) */
        const exploredList = Array.isArray(snapshot.explored) ? snapshot.explored : null;
        if (exploredList) {
          exploredList.forEach((id) => {
            compiled.roomExplored[id] = true;
          });
        }
        state.nodes
          .filter((n) => n.compiledItem || n.compiledExit || n.compiledContainer)
          .forEach((n) => {
            if (n.compiledConsumed || (n.compiledHidden && !n.revealed)) return;
            if (
              exploredList &&
              n.compiledScene &&
              !n.compiledResult &&
              !compiled.roomExplored[n.compiledScene]
            )
              return; /* 未走进的房间:物件保持藏着 */
            n.hidden = false;
          });
        if (compiled.rootMode) {
          const lv = levelNode('compiled-level');
          if (lv) lv.hidden = true;
        }
      }
      /* 11.12 #4/#8:并行房间恢复只调一次;快照与关卡数据任一声明并行即恢复,
         消除连续两次调用造成的叠加修改残留 */
      if (
        compiled.started &&
        (snapshot.parallelRooms === true ||
          (compiled.level && compiled.level.parallelRooms === true))
      ) {
        revealAllRooms(false);
      }
      if (compiled.started) inspect(levelNode('compiled-level'));
      action();
      update();
      compiledObjective();
      roomRender();
      drawLinks();
      return true;
    },
  };

  const compiledRuntime = window.__favoriteRoomRuntime;
  const baseActivateRoot = compiledRuntime.activateRoot;
  compiledRuntime.activateRoot = function (title, detail) {
    const ok = baseActivateRoot(title, detail);
    state.nodes.forEach((n) => {
      if (
        n.id !== 'root' &&
        !n.compiledLevel &&
        !n.compiledItem &&
        !n.compiledExit &&
        !n.compiledResult
      )
        n.hidden = true;
    });
    const level = levelNode('compiled-level');
    if (level) level.hidden = true;
    const root = levelNode('root');
    if (root) root.hidden = false;
    roomRender();
    drawLinks();
    return ok;
  };
  const baseResetButton = roomReset;
  reset = function () {
    baseResetButton();
    /* 11.12 #3:重置必须清理机关上下文与弹窗——旧回调不得作用到新运行态 */
    keypadCtx = null;
    angleCtx = null;
    morseCtx = null;
    ['keypadModal', 'angleModal', 'morseModal'].forEach(function (id) {
      document.getElementById(id)?.classList.add('hidden');
    });
    /* 11.12 #6:视图状态(缩放/平移)不跨关卡泄漏 */
    if (typeof resetView === 'function') resetView();
    const c = compiled;
    if (c) {
      c.started = false;
      c.done = false;
      c.inspected = new Set();
      c.sequence = [];
      compiledRuntime.activateRoot(c.level.title, c.level.premise);
      compiledObjective();
      roomRender();
      drawLinks();
    }
    return true;
  };
  /* 11.12 修复约定:产品唯一重置入口——保留当前关卡记录,重建同一关卡初始运行态。
     room02 的 #reset 与 app.js 的产品层都只准走这里;基础 roomReset() 仅限底层克隆。 */
  compiledRuntime.resetCurrentLevel = function () {
    return reset();
  };
})();
