/* ============================================================
   Room 02 · 数据驱动状态机(clue / preClue / 交互表)
   借鉴《文字密室逃脱》参考实现:
   - clues:Set, "#x" 获得 / "-#x" 移除
   - preClue:字符串或数组;数组=AND;"|"=OR;"!"=NOT
   - 节点 state[]:获得线索后切换形态(名称/文案/样式)
   - 交互表 ROOM_USE:替代 roomUse 硬编码 if 链
   ============================================================ */
/* 素材身份角标(编译关卡的 role → 卡片上的小字) */
const ROOM_ROLE_LABELS = {
  clue: '线索',
  tool: '工具',
  lock: '锁',
  transform: '转化',
  reward: '信物',
  red_herring: '干扰',
};

const ROOM_NODES = [
  {
    id: 'root',
    kind: 'zone',
    name: '收藏室',
    hint: '唯一看得清的是一盏台灯',
    x: 43,
    y: 39,
    detail: '一间被遗忘的收藏室。门、资料架、工作台和墙面都像还在等下一次使用。',
  },
  {
    id: 'shelf',
    kind: 'zone',
    name: '资料架',
    hint: '卡片被压在一起',
    x: 7,
    y: 20,
    parent: 'root',
    detail: '几张关于计算机和交互的收藏被压在旧纸箱里。',
  },
  {
    id: 'desk',
    kind: 'zone',
    name: '工作台',
    hint: '有一块黑屏和一张草稿',
    x: 7,
    y: 68,
    parent: 'root',
    detail: '工作台上的屏幕没有亮,草稿纸只露出一角。',
  },
  {
    id: 'wall',
    kind: 'zone',
    name: '墙面',
    hint: '海报后面似乎有空间',
    x: 73,
    y: 20,
    parent: 'root',
    detail: '墙上贴着一张褪色海报,边缘有被反复掀动的痕迹。',
  },
  {
    id: 'exit',
    kind: 'zone',
    name: '出口',
    hint: '门把手没有回应',
    x: 73,
    y: 68,
    parent: 'root',
    detail: '门上没有密码盘,只有一个像收藏夹图标一样的凹槽。',
  },
  {
    id: 'escape',
    kind: 'collectible',
    name: '文字密室逃脱',
    hint: '看见,不等于完成',
    parent: 'shelf',
    x: 3,
    y: 8,
    url: 'https://nodes-escape.hzfe.org/',
    detail: '折痕里写着:看过的地方,发生变化后要再回来。',
    interact: [
      {
        type: 'reveal',
        targets: ['dial'],
        log: '折痕里露出一句话:看过的地方,发生变化后要再回来。',
        logKind: 'good',
      },
    ],
  },
  {
    id: 'nand',
    kind: 'collectible',
    name: 'NandGame',
    hint: '从最小的门开始',
    parent: 'shelf',
    x: 24,
    y: 8,
    url: 'https://nandgame.com/',
    detail: '背面写着:一半结构没有另一半就不能工作。',
  },
  {
    id: 'tetris',
    kind: 'collectible',
    name: 'nand2tetris',
    hint: '把门电路建成系统',
    parent: 'shelf',
    x: 24,
    y: 30,
    url: 'https://www.nand2tetris.org/',
    detail: '边角有一条相同的折痕,像是另一半。',
  },
  {
    id: 'dial',
    kind: 'action',
    name: '卡住的索引旋钮',
    hint: '每次只移动一格',
    action: 'dial',
    parent: 'shelf',
    x: 3,
    y: 50,
    hidden: true,
    detail: '旋钮旁写着:索引不是一次读完的。',
    state: [
      { preClue: { clue: '#dial-{0}', params: [1] }, hint: '已经转过一格,还差两格' },
      { preClue: { clue: '#dial-{0}', params: [2] }, hint: '已经转过两格,最后一格会改变资料架' },
      {
        preClue: { clue: '#dial-{0}', params: [3] },
        name: '停下的索引旋钮',
        hint: '回访条已经显形',
      },
    ],
    interact: [
      {
        type: 'count',
        need: 3,
        clue: '#loop',
        reveal: ['shelfNote'],
        log: '旋钮终于停下。资料架背面的回访条出现了。',
        logKind: 'good',
        frontier: 'revisit',
      },
    ],
  },
  {
    id: 'shelfNote',
    kind: 'result',
    name: '折叠的回访条',
    hint: '变化以后,再看一遍',
    parent: 'shelf',
    x: 25,
    y: 53,
    hidden: true,
    detail: '骨架完成后,折叠条里出现了新的字:不要只修理眼前的东西。',
  },
  {
    id: 'programiz',
    kind: 'collectible',
    name: 'Programiz',
    hint: '把结构写成动作',
    parent: 'desk',
    x: 53,
    y: 8,
    url: 'https://www.programiz.com/',
    detail: '代码入口。它需要一副已经成形的结构。',
  },
  {
    id: 'vue',
    kind: 'collectible',
    name: 'Vue SFC Playground',
    hint: '让反馈立刻出现',
    parent: 'desk',
    x: 53,
    y: 28,
    url: 'https://sfc.vuejs.org/',
    detail: '一个能立即显示结果的空白界面。',
  },
  {
    id: 'draft',
    kind: 'collectible',
    name: '旧项目草稿',
    hint: '背面有一组缺失状态',
    parent: 'desk',
    x: 32,
    y: 50,
    hidden: true,
    detail: '正面只有三行:结构、动作、反馈。背面似乎还有东西。',
    interact: [
      { type: 'log', log: '草稿背面写着:结构之后,必须让它产生一次可见反馈。', logKind: 'good' },
    ],
  },
  {
    id: 'cloth',
    kind: 'action',
    name: '擦镜布',
    hint: '可以改变墙面的状态',
    action: 'cloth',
    parent: 'desk',
    x: 53,
    y: 50,
    hidden: true,
    detail: '一块沾着灰的布,刚好能擦掉墙上的薄层。',
  },
  {
    id: 'logic',
    kind: 'result',
    name: '可执行逻辑',
    hint: '拖到即时反馈上',
    parent: 'desk',
    x: 32,
    y: 72,
    hidden: true,
    detail: '结构已经变成一段可以运行的逻辑。',
  },
  {
    id: 'shell',
    kind: 'result',
    name: '反馈外壳',
    hint: '拖到黑屏上',
    parent: 'desk',
    x: 53,
    y: 72,
    hidden: true,
    detail: 'QTE 成功后留下的可运行外壳。',
  },
  {
    id: 'screen',
    kind: 'zone',
    name: '黑掉的屏幕',
    hint: '等待一个外壳',
    parent: 'desk',
    x: 73,
    y: 72,
    hidden: true,
    detail: '屏幕边缘有一个收藏夹形状的插槽。',
    state: [
      {
        preClue: '#screen',
        name: '亮起的屏幕',
        hint: '检查启动片段',
        detail: '反馈外壳已经嵌入插槽。屏幕亮起一瞬,留下了需要回访的颜色线索。',
      },
    ],
  },
  {
    id: 'poster',
    kind: 'collectible',
    name: '褪色海报',
    hint: '颜色顺序不完整',
    parent: 'wall',
    x: 73,
    y: 8,
    hidden: true,
    detail: '海报上只有三枚箭头:红色、蓝色、绿色。顺序被灰尘遮住了。',
    interact: [{ type: 'log', log: '灰尘遮住了海报的中段,颜色顺序还不能确定。', logKind: 'warn' }],
  },
  {
    id: 'cleanWall',
    kind: 'result',
    name: '擦亮的墙面',
    hint: '海报后面露出三个按钮',
    parent: 'wall',
    x: 73,
    y: 30,
    hidden: true,
    detail: '擦掉薄层后,海报后面露出一个暗格。',
  },
  {
    id: 'red',
    kind: 'action',
    name: '红色按钮',
    hint: '第一位',
    action: 'sequence-red',
    parent: 'wall',
    x: 53,
    y: 53,
    hidden: true,
  },
  {
    id: 'blue',
    kind: 'action',
    name: '蓝色按钮',
    hint: '第二位',
    action: 'sequence-blue',
    parent: 'wall',
    x: 73,
    y: 53,
    hidden: true,
  },
  {
    id: 'green',
    kind: 'action',
    name: '第三位',
    action: 'sequence-green',
    parent: 'wall',
    x: 53,
    y: 72,
    hidden: true,
  },
  {
    id: 'screenLog',
    kind: 'result',
    name: '启动片段',
    hint: '红、蓝、绿',
    parent: 'screen',
    x: 73,
    y: 50,
    hidden: true,
    detail: '屏幕亮起一瞬,显示三段颜色:红 → 蓝 → 绿。',
    interact: [{ type: 'frontier', frontier: 'wall' }],
  },
  {
    id: 'skeleton',
    kind: 'result',
    name: '收藏骨架',
    hint: '两张底层收藏合成',
    parent: 'shelf',
    x: 3,
    y: 72,
    hidden: true,
    detail: 'NandGame 和 nand2tetris 变成一副可以承载动作的骨架。',
  },
  {
    id: 'machine',
    kind: 'result',
    name: '重新整理的收藏',
    hint: '拖到出口',
    parent: 'exit',
    x: 73,
    y: 50,
    hidden: true,
    detail: '结构、动作和反馈终于被整理成一件可以继续使用的东西。',
    state: [
      {
        preClue: '#order',
        name: '带有启动顺序的收藏',
        hint: '拖到出口',
        detail: '三个按钮的顺序已经写进收藏。它现在可以被交付。',
      },
    ],
  },
];

/* 交互表:拖 A 到 B → 效果(顺序无关,键为排序后的对) */
const ROOM_USE = [
  {
    pair: ['nand', 'tetris'],
    consume: ['nand', 'tetris'],
    reveal: ['skeleton', 'draft'],
    clue: '#structure',
    log: '两张底层收藏的折痕对上了。收藏骨架出现。',
    logKind: 'good',
    frontier: 'revisit',
  },
  {
    pair: ['skeleton', 'programiz'],
    consume: ['skeleton', 'programiz'],
    reveal: ['logic'],
    clue: '#logic',
    log: '结构被写成可执行逻辑。工作台深处传来一点反馈。',
    logKind: 'good',
    frontier: 'desk',
  },
  { pair: ['logic', 'vue'], qte: true },
  {
    pair: ['cloth', 'wall'],
    consume: ['cloth'],
    reveal: ['cleanWall', 'red', 'blue', 'green'],
    clue: '#wall',
    log: '擦镜布抹掉灰尘。海报后的三个按钮露了出来。',
    logKind: 'good',
    frontier: 'wall',
  },
  {
    pair: ['shell', 'screen'],
    consume: ['shell'],
    reveal: ['screenLog'],
    clue: '#screen',
    log: '反馈外壳嵌入黑屏。启动片段闪过:红、蓝、绿。',
    logKind: 'good',
    frontier: 'wall',
  },
  {
    pair: ['machine', 'exit'],
    consume: ['machine'],
    clue: '#delivered',
    log: '收藏被放回出口的凹槽。门锁开始松动。',
    logKind: 'good',
    ending: true,
  },
];

/* 按钮顺序:sequence 动作 */
const ROOM_SEQUENCE = {
  order: ['red', 'blue', 'green'],
  clue: '#order',
  reveal: ['machine'],
  log: '三个按钮按正确顺序回应。重新整理的收藏出现了。',
  logKind: 'good',
  frontier: 'final',
};

/* 空间展开时,preClue 门控的额外子节点 */
const ROOM_ZONE_REVEAL = {
  shelf: {
    always: ['escape', 'nand', 'tetris'],
    gated: [
      { ids: ['dial'], need: ['#escape-seen'] },
      { ids: ['shelfNote'], need: ['#loop'] },
    ],
  },
  desk: {
    always: ['programiz', 'vue'],
    gated: [
      { ids: ['draft', 'cloth'], need: ['#structure'] },
      { ids: ['screen'], need: ['#logic'] },
      { ids: ['shell'], need: ['#feedback'] },
    ],
  },
  wall: {
    always: ['poster'],
    gated: [{ ids: ['cleanWall', 'red', 'blue', 'green'], need: ['#wall'] }],
  },
  screen: { always: ['screenLog'], gated: [] },
};

/* 分级提示 */
const ROOM_HINTS = {
  explore: ['先观察唯一的场景。', '场景展开后,空间之间会保留关系。', '点击"收藏室"。'],
  shelf: ['资料架上有两张底层收藏。', '它们的折痕互相对应。', '把 nand2tetris 拖到 NandGame 上。'],
  revisit: [
    '已经看过的资料架发生了变化。',
    '变化不是新的房间,而是一个新的状态。',
    '回到资料架检查索引旋钮,再去看工作台。',
  ],
  desk: [
    '工作台需要一副结构。',
    'Programiz 只能作用于已经成形的结构。',
    '先把收藏骨架拖到 Programiz 上,再观察即时反馈。',
  ],
  wall: [
    '墙面上的海报还被灰尘遮住。',
    '擦镜布可以改变墙面状态。',
    '把擦镜布拖到墙面,再按屏幕给出的颜色顺序。',
  ],
  screen: ['黑屏不是普通收藏。', '它有一个与反馈外壳相配的插槽。', '把反馈外壳拖到黑掉的屏幕。'],
  final: [
    '出口只接受整理完成的收藏。',
    '最后的物件会在按钮顺序正确后出现。',
    '把重新整理的收藏拖到出口。',
  ],
};

/* 进度条状态(6 段) */
const ROOM_PROGRESS = ['structure', 'logic', 'feedback', 'wall', 'order', 'delivered'];

/* ---------------- 状态机核心 ---------------- */
const state = {
  nodes: [],
  clues: new Set(),
  frontier: 'explore',
  hintLevel: 0,
  hintBlocked: false,
  hintMark: 0,
  hintCharges: 4,
  dial: 0,
  sequence: [],
  actions: 0,
  ending: false,
  activePop: null,
};
const $ = (id) => document.getElementById(id),
  get = (id) => state.nodes.find((n) => n.id === id);
var drag = null,
  toastTimer = null,
  qteTimer = null;
/* 动态 clue:支持 #blue-{0} + params:[2] => blue-2。对象形式可用于
   preClue/interact:{clue:'#blue-{0}',params:[2]}，保持静态字符串兼容。 */
function resolveClue(c, params) {
  if (typeof c !== 'string') return c;
  const values = Array.isArray(params) ? params : params || [];
  return c.replace(/\{(\d+)\}/g, function (_, i) {
    return values[i] ?? '';
  });
}
function clueArgs(c) {
  return c && typeof c === 'object' && !Array.isArray(c)
    ? [c.clue || c.key, c.params || c.values]
    : [c, undefined];
}
/* clue 判定:支持 "#x"(有) "-#x"(无) 数组 AND "|" OR "!" NOT */
function hasClue(c, params) {
  if (c == null) return true;
  if (Array.isArray(c)) return c.every((x) => hasClue(x, params));
  if (c && typeof c === 'object' && !Array.isArray(c)) {
    const [key, args] = clueArgs(c);
    return hasClue(key, args);
  }
  if (typeof c !== 'string') return !!c;
  if (c.includes('|')) return c.split('|').some((x) => hasClue(x, params));
  if (c.startsWith('!')) return !hasClue(c.slice(1), params);
  c = resolveClue(c, params);
  if (c.startsWith('-#')) return !state.clues.has(c.slice(2));
  if (c.startsWith('#')) return state.clues.has(c.slice(1));
  return true;
}

function addClue(c, params) {
  if (Array.isArray(c)) {
    c.forEach((x) => addClue(x, params));
    return;
  }
  if (c && typeof c === 'object' && !Array.isArray(c)) {
    const [key, args] = clueArgs(c);
    addClue(key, args);
    return;
  }
  if (typeof c !== 'string' || !c) return;
  c = resolveClue(c, params);
  if (c.startsWith('-#')) state.clues.delete(c.slice(2));
  else if (c.startsWith('#')) state.clues.add(c.slice(1));
  applyClueEffects();
}

function nodeVariant(n) {
  if (!n || !Array.isArray(n.state)) return n;
  const variant = n.state.filter((s) => hasClue(s.preClue)).at(-1);
  return variant ? { ...n, ...variant } : n;
}

function applyClueEffects() {
  state.nodes.forEach((n) => {
    if (!n.gates) return;
    n.gates.forEach((g) => {
      if (hasClue(g.need) && !g.applied) {
        g.applied = true;
        g.ids.forEach((id) => {
          const t = get(id);
          if (t) {
            t.hidden = false;
            roomArrange(t.parent); /* 显形即归位到父节点周围(reveal 双轨修复) */
          }
        });
      }
    });
  });
}

/* 节点可见性:hidden + used + preClue 门;编译关卡的物件 used 后仍留在画布(灰化),因为后续 beat 可能还要引用它 */
function nodeVisible(n) {
  if ((n.compiledItem || n.compiledResult) && !n.hidden) return true;
  return !n.hidden && !n.used && hasClue(n.preClue);
}

function roomClone() {
  state.nodes = ROOM_NODES.map((n) => ({
    ...n,
    hidden: n.id !== 'root',
    used: false,
    spawned: false,
    startHidden: !!n.hidden,
  }));
  state.nodes.forEach((n) => {
    if (n.id === 'root') {
      n.x = 43;
      n.y = 39;
    }
  });
  /* 恢复玩家拖拽过的布局(savePos 此前只写不读);仅原生房间——
     编译关卡的槽位由分区摆位统一管理,不受存档影响 */
  try {
    if (!localStorage.getItem('favorite-room-draft')) {
      const saved = JSON.parse(localStorage.getItem('fav-room-pos') || 'null');
      if (saved && typeof saved === 'object')
        state.nodes.forEach((n) => {
          const p = saved[n.id];
          if (p && Number.isFinite(p.x) && Number.isFinite(p.y)) {
            n.x = Math.max(-10, Math.min(100, p.x));
            n.y = Math.max(-10, Math.min(100, p.y));
          }
        });
    }
  } catch (_) {}
}

function roomArrange(parentId) {
  const p = get(parentId);
  if (!p) return;
  state.nodes
    .filter((n) => n.parent === parentId)
    .forEach((n, i) => {
      if (n.spawned) return;
      const col = i % 2,
        row = Math.floor(i / 2);
      n.x = Math.max(2, Math.min(84, p.x - 10 + col * 20));
      n.y = Math.max(8, Math.min(90, p.y + (p.y > 55 ? -20 - row * 17 : 20 + row * 17)));
      n.spawned = true;
    });
}

function roomReveal(ids) {
  ids.forEach((id) => {
    const n = get(id);
    if (n) {
      n.hidden = false;
      n.justArrived = true; /* 显形即有一次出现动画,玩家能看见"多了什么" */
      roomArrange(n.parent);
    }
  });
}

/* ---------------- 空间分区摆位(2026-08-29 结构性重设计) ----------------
   旧实现:编译关卡/导入草案的节点坐标在 hydrate 时按索引常量公式散布在
   全局网格,与父节点无关——"子节点不出现在父节点周围"的结构性根因。
   新模型:舞台按分区容器(compiled-level / imported-room)的 zone 子节点
   数切成网格分区;每个分区顶部是场景名牌,物件在其下方流式排布,槽位
   在 hydrate 时一次定死(含隐藏物件),reveal 只翻显隐、永不再挪坐标。
   → 零碰撞(拖拽组合测试依赖)、子节点恒在自己分区内、跨批导入不重叠。 */

/* 把 count 个节点铺进矩形区(舞台百分比),返回每个节点的槽位中心 */
function roomGridSlots(count, x0, y0, w, h, colsOverride) {
  const cols = Math.max(1, colsOverride || (count <= 3 ? count : count <= 8 ? 3 : 4));
  const rows = Math.max(1, Math.ceil(count / cols));
  const slots = [];
  for (let i = 0; i < count; i++) {
    const cx = i % cols,
      cy = Math.floor(i / cols);
    slots.push({
      x: x0 + (cx + 0.5) * (w / cols),
      y: y0 + cy * (h / rows),
    });
  }
  return slots;
}

/* 对一个分区容器(board)做空间分区:
   - zone 子节点(compiled-scene / compiled-container / imported-group)各占一个分区;
   - 名牌置分区顶部居中,其子物件(含隐藏物、继续搜索按钮)在名牌下方网格;
   - board 自身节点(如 compiled-level)若存在则挪到顶部中央作入口牌。 */
/* 已摆位的分区容器(窗口尺寸变化时整体重排) */
const roomLayoutBoards = new Set();
let roomLayoutResizeTimer = 0;
window.addEventListener('resize', () => {
  if (!roomLayoutBoards.size) return;
  clearTimeout(roomLayoutResizeTimer);
  roomLayoutResizeTimer = setTimeout(() => {
    roomLayoutBoards.forEach((id) => roomLayoutBoard(id));
    if (typeof drawLinks === 'function') drawLinks();
  }, 180);
});

function roomLayoutBoard(boardId) {
  const clampP = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const board = get(boardId);
  if (!board) return;
  roomLayoutBoards.add(boardId);
  /* 窄屏(手机):分区纵向堆叠、物件少列。用窗口宽度判定——
     hydrate 时舞台还在隐藏的壳里,clientWidth 恒为 0 会误判 */
  const narrow = window.innerWidth < 700;
  const zones = state.nodes.filter(
    (n) =>
      n.parent === boardId &&
      /zone/.test(n.kind || '') &&
      !n.compiledExit &&
      !n.compiledLevel,
  );
  /* 挂在 board 下、不属于任何分区容器的散件(flat 关卡无容器物件)占用最后一个伪分区 */
  const loose = state.nodes.filter(
    (n) => n.parent === boardId && !/zone/.test(n.kind || '') && !n.compiledExit,
  );
  const cells = [];
  zones.forEach((z) => cells.push({ zone: z }));
  if (loose.length) cells.push({ loose });
  const count = Math.max(1, cells.length);
  const cols = narrow ? 1 : count <= 2 ? count : count <= 4 ? 2 : 3;
  const rows = Math.ceil(count / cols);
  /* 画布可用区:顶部留引导横幅与入口牌行,四周留边 */
  const bx = 3,
    by = 15,
    bw = 94,
    bh = 78;
  cells.forEach((cell, i) => {
    const cx = i % cols,
      cy = Math.floor(i / cols);
    const cw = bw / cols,
      ch = bh / rows;
    const x0 = bx + cx * cw,
      y0 = by + cy * ch;
    const z = cell.zone;
    if (z) {
      z.x = clampP(x0 + cw / 2 - 8, x0, x0 + cw - 18);
      z.y = y0 + 1;
    }
    const kids = z
      ? state.nodes.filter((k) => k.parent === z.id)
      : cell.loose;
    const kidCols = narrow ? 1 : kids.length <= 4 ? 2 : kids.length <= 8 ? 3 : 4;
    const slots = roomGridSlots(
      kids.length,
      x0 + 2,
      z ? y0 + 8 : y0 + 3,
      cw - 6,
      z ? ch - 10 : ch - 6,
      kidCols,
    );
    kids.forEach((k, ki) => {
      const s = slots[ki];
      k.x = clampP(s.x - 7, x0, x0 + cw - 17);
      /* 窄屏单列允许探出分区底缘(超出部分靠画布平移/缩放查看),
         换取不越左右视口边缘——竖屏放不下完整分区网格 */
      k.y = clampP(s.y, y0 + 6, narrow ? y0 + ch + 14 : y0 + ch - 13);
    });
  });
  /* 入口牌(board 本身):顶部中央,root 之下第一层 */
  if (board.compiledLevel) {
    board.x = 40;
    board.y = 2;
  }
  /* 分区底板:给每个分区画一层极淡的空间框(不可交互)——
     舞台从“节点图”变成可感知的“房间分区” */
  let layer = document.getElementById('zonePlates');
  const stageEl = $('stage');
  if (!stageEl) return;
  if (!layer) {
    layer = document.createElement('div');
    layer.id = 'zonePlates';
    stageEl.insertBefore(layer, stageEl.firstChild);
  }
  layer.innerHTML = cells
    .map((cell, i) => {
      const cx = i % cols,
        cy = Math.floor(i / cols);
      const cw = bw / cols,
        ch = bh / rows;
      const x0 = bx + cx * cw,
        y0 = by + cy * ch;
      const label = cell.zone ? '' : '散落素材';
      return (
        '<div class="zone-plate" style="left:' +
        x0 +
        '%;top:' +
        y0 +
        '%;width:' +
        cw +
        '%;height:' +
        ch +
        '%"><span>' +
        label +
        '</span></div>'
      );
    })
    .join('');
}

function roomReset() {
  if (qteTimer) {
    clearInterval(qteTimer);
    qteTimer = null;
  }
  $('qteModal').classList.add('hidden');
  $('endingModal').classList.add('hidden');
  document.getElementById('zonePlates')?.replaceChildren();
  roomClone();
  state.clues = new Set();
  state.frontier = 'explore';
  state.hintLevel = 0;
  state.hintBlocked = false;
  state.hintMark = 0;
  state.hintCharges = 4;
  state.dial = 0;
  state.sequence = [];
  state.actions = 0;
  state.ending = false;
  $('log').innerHTML = '<div class="event">房间里只有一盏台灯。先观察它把什么照亮了。</div>';
  inspect(get('root'));
  update();
  render();
}

/* 父子链锚点(2026-08-30 修复):**连线与出现动画共用同一支解析**。
   此前两边各算各的——
     · drawLinks 取「父子链上第一个**可见**的祖先」
     · 飞入起点直接取 n.revealFromId || n.parent
   编译关卡里所有物件的 parent 都是 compiled-level 标题板(常态 hidden,
   摆在画布顶边 y=2),于是连线锚到了 root(画布中心),物件却从顶边飞出,
   实测两端起点相差约 450px——「线从中间长出来、卡片从顶上砸下来」的割裂感。
   现在统一走这里:先认显形源物件(照亮/再点一下源物件显形的物件从源物件飞出),
   否则沿父子链上溯到第一个可见祖先;两边取到的一定是同一个节点。 */
function originOf(n) {
  if (!n) return null;
  const rf = n.revealFromId && get(n.revealFromId);
  if (rf && !rf.hidden && rf !== n) return rf;
  let a = n.parent,
    guard = 0;
  while (a && guard++ < 16) {
    const p = get(a);
    if (!p) return null;
    if (!p.hidden && p !== n) return p;
    a = p.parent;
  }
  return null;
}

function roomRender() {
  const box = $('nodes');
  box.innerHTML = state.nodes
    .filter(nodeVisible)
    .map((n) => {
      const v = nodeVariant(n),
        name = n.id === 'dial' ? '卡住的索引旋钮 · ' + state.dial + ' / 3' : v.name;
      const spent = (n.compiledItem || n.compiledResult) && n.used ? ' compiled-spent' : '';
      /* 变化过渡(2026-08-30):原位变身的这一帧加 .changed 脉冲,玩家能看见"哪个物件变了" */
      const changedCls = n.justChanged ? ' changed' : '';
      const kindCls =
        n.compiledHidden && !n.revealed ? v.kind : v.kind.replace(' compiled-hidden-item', '');
      const webMark = v.url ? '<span class="web-mark" title="收藏网页">↗</span>' : '';
      /* 角色角标(2026-08-29):卡片上直接标出素材身份,卡片不再只有一行名字。
         2026-08-31 伪装(需求方反馈):干扰项印着「干扰」等于明牌——它必须
         看似与主线相关的线索,角标与色条都按线索显示,真假由玩家自己甄别 */
      const typeHtml = n.compiledRole
        ? '<i class="type">' +
          (ROOM_ROLE_LABELS[n.compiledRole === 'red_herring' ? 'clue' : n.compiledRole] || '') +
          '</i>'
        : '';
      let pop = '';
      if (state.activePop === n.id) {
        const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
        const detail = esc(v.detail || v.hint || '').replace(/\n/g, '<br>');
        const link = v.url
          ? '<a class="np-link" href="' +
            esc(v.url) +
            '" target="_blank" rel="noreferrer">打开原收藏 ↗</a>'
          : '';
        /* 位置由 placePops 在渲染后按遮挡情况四向避让,这里不预设方向 */
        pop =
          '<div class="node-pop"><button class="np-close" type="button" title="关闭">×</button><div class="np-title">' +
          esc(name) +
          '</div><div class="np-copy">' +
          detail +
          '</div>' +
          link +
          '</div>';
      }
      /* pop-open(2026-08-30 修复):详情卡是节点的子元素,z-index 只在父节点的
         层叠上下文内生效——DOM 靠后的兄弟节点会整片盖住打开的详情卡。
         打开时把宿主节点抬到普通节点(4)与 hover(6)之上,盖回它的卡才不会被打断 */
      return `<div class="node ${kindCls}${spent}${n.justArrived ? ' arrive' : ''}${changedCls}${state.activePop === n.id ? ' pop-open' : ''}" data-id="${n.id}" style="left:${n.x}%;top:${n.y}%" role="button" tabindex="0">${webMark}<span class="node-main">${typeHtml}<span class="name">${name}</span></span>${pop}</div>`;
    })
    .join('');
  /* 展开起点(11.13 #3):容器/父物件的内容物从父节点位置飞入自己的槽位,
     同容器兄弟按序交错出现;--fx/--fy/--fd 由 arrive 关键帧消费 */
  let arriveIdx = 0;
  let anyArrived = false;
  state.nodes.forEach((n) => {
    if (!n.justArrived) return;
    anyArrived = true;
    const el = document.querySelector('.node[data-id="' + n.id + '"]');
    if (!el) return;
    /* 起飞点 = 连线的父端锚点(见 originOf 注释)。位移按两端**实测盒心**相减,
       不再用百分比乘舞台尺寸——与连线端点(offsetLeft + 宽/2)逐像素对齐,
       平移缩放、边界内缩都不会让两者错开。取不到锚点(如房间根)时原地浮现。 */
    const srcNode = originOf(n);
    const srcEl = srcNode && document.querySelector('.node[data-id="' + srcNode.id + '"]');
    if (srcEl && srcEl !== el) {
      const dx = srcEl.offsetLeft + srcEl.offsetWidth / 2 - (el.offsetLeft + el.offsetWidth / 2);
      const dy = srcEl.offsetTop + srcEl.offsetHeight / 2 - (el.offsetTop + el.offsetHeight / 2);
      el.style.setProperty('--fx', dx + 'px');
      el.style.setProperty('--fy', dy + 'px');
    }
    el.style.setProperty('--fd', arriveIdx * 70 + 'ms');
    arriveIdx++;
  });
  /* 新物件显形时收起线索便签浮层(2026-08-31):浮层悬在画布右上,
     恰好盖住飞入的节点——玩家点节点实际点到浮层,点击被吞(教程关实测)。
     显形本身也意味着提示上下文更新了,收起让位给新内容。 */
  if (anyArrived) {
    const hf = document.getElementById('hintFloat');
    if (hf) hf.classList.add('hidden');
    /* 新显形物件可能落在已打开的详情卡下方(2026-08-31):开卡时的四向避让只看过
       当时的节点,后显形的物件恰好被卡片盖住时,点击会先命中卡片宿主——入口卡
       还会把它当成环视,物件的响应被吞(资料室关实测:规则卡落在入口卡下)。
       飞入动画落定后复检一次,有覆盖就清掉该宿主的方向记忆并重新避让;
       重避让后仍覆盖则收卡兜底。不在动画中途测量(transform 未归零,盒坐标不可信)——
       复检延时取 1500ms:飞入动画 0.7s + 每节点 70ms 交错,12 物件内必然全部落定。 */
    if (state.activePop) {
      const hostId = state.activePop;
      setTimeout(() => {
        if (state.activePop !== hostId) return;
        const host = document.querySelector('.node[data-id="' + hostId + '"]');
        const pop = host && host.querySelector('.node-pop');
        if (!host || !pop) return;
        const coversNode = () => {
          const pr = pop.getBoundingClientRect();
          return state.nodes.some((n) => {
            if (n.hidden || n.id === hostId) return false;
            const el = document.querySelector('.node[data-id="' + n.id + '"]');
            if (!el) return false;
            const nr = el.getBoundingClientRect();
            return (
              nr.left < pr.right && nr.right > pr.left && nr.top < pr.bottom && nr.bottom > pr.top
            );
          });
        };
        if (!coversNode()) return;
        state.popSide = state.popSide || {};
        delete state.popSide[hostId];
        placePops();
        if (coversNode()) {
          state.activePop = null;
          roomRender();
        }
      }, 1500);
    }
  }
  /* 出现/变化标记延到下一帧再清(2026-08-30 修复):
     一次点击里 roomRender 常被连续调用 2~3 次(inspect() 内部一次 + 末尾再显式
     调用一次),每次都用 innerHTML 重建全部节点。此前在渲染末尾**立即**清标记,
     导致 .arrive / .changed 只落在随后被整块丢弃的中间那次 DOM 上,最终留在
     页面上的元素反而没有动画类——"展开动画不生效"的结构性根因。
     改为下一帧清除:同一任务内的多次重渲染都带着类,只有真正上屏的那份 DOM
     播动画,动画起始时刻与浏览器绘制对齐。 */
  const dirty = state.nodes.filter((n) => n.justArrived || n.justChanged);
  if (dirty.length) {
    requestAnimationFrame(() => {
      dirty.forEach((n) => {
        n.justArrived = false;
        n.justChanged = false;
        /* 2026-08-31 修复:.arrive 类此前一直滞留到下一次重渲染——飞入中的节点
           位置未定却可被点击,开局连点会把点击落在恰好飞过的别的节点上
           (实测 watchman 按序检查三件素材,第一步点击落到路过节点,inspect
           缺步、组合失败)。改为 arrive 动画结束(animationend)即摘类,
           配合 CSS 的 .node.arrive { pointer-events:none }:飞行中不可点、
           落定即可点。changed 脉冲与点击无关,保持原样。 */
        const el = document.querySelector('.node[data-id="' + n.id + '"]');
        if (el && el.classList.contains('arrive')) {
          el.addEventListener('animationend', function h(e) {
            if (e.animationName === 'arrive') {
              el.classList.remove('arrive');
              el.removeEventListener('animationend', h);
            }
          });
        }
      });
    });
  }
  document.querySelectorAll('.node').forEach(roomBind);
  placePops();
  drawLinks();
}

/* 详情卡四向避让(2026-08-29):上/下/右/左四个候选位置里挑一个
   不遮挡任何节点的;全部冲突时取重叠最小的——就地上卡永不吞掉
   邻近节点的点击(分区网格中名牌与物件间距小,固定方向必然误伤) */
function placePops() {
  const nodes = [...document.querySelectorAll('.node')];
  /* 方向记忆(2026-08-30):每个节点的详情卡只在**首次打开**时做一次四向避让,
     之后记住方向复用——节点 hydrate 后位置不再变,反复避让只会让卡片在
     点击之间来回翻面,观感即"乱跳" */
  state.popSide = state.popSide || {};
  document.querySelectorAll('.node-pop').forEach((pop) => {
    pop.classList.remove('below', 'side-right', 'side-left');
    const host = pop.closest('.node');
    if (!host) return;
    const hostId = host.getAttribute('data-id');
    const remembered = state.popSide[hostId];
    if (remembered !== undefined) {
      if (remembered) pop.classList.add(remembered);
      return;
    }
    const pr = pop.getBoundingClientRect(),
      hr = host.getBoundingClientRect(),
      stage = $('stage').getBoundingClientRect(),
      popW = Math.max(pr.width, 200),
      popH = Math.max(pr.height, 80);
    const others = nodes.filter((n) => n !== host).map((n) => n.getBoundingClientRect());
    const overlap = (x, y) =>
      others.reduce((sum, r) => {
        const ix = Math.max(0, Math.min(x + popW, r.right) - Math.max(x, r.left));
        const iy = Math.max(0, Math.min(y + popH, r.bottom) - Math.max(y, r.top));
        return sum + ix * iy;
      }, 0);
    const cands = [
      ['', hr.left + hr.width / 2 - popW / 2, hr.top - 12 - popH],
      ['below', hr.left + hr.width / 2 - popW / 2, hr.bottom + 12],
      ['side-right', hr.right + 12, hr.top + hr.height / 2 - popH / 2],
      ['side-left', hr.left - 12 - popW, hr.top + hr.height / 2 - popH / 2],
    ];
    let best = '',
      bestScore = Infinity;
    cands.forEach(([cls, x, y]) => {
      let score = overlap(x, y);
      if (x < stage.left + 4 || x + popW > stage.right - 4) score += 8000;
      if (y < stage.top + 4 || y + popH > stage.bottom - 4) score += 8000;
      if (score < bestScore) {
        bestScore = score;
        best = cls;
      }
    });
    state.popSide[hostId] = best;
    if (best) pop.classList.add(best);
  });
}

/* ---------------- 拖动(合并 3 版覆盖) ---------------- */
function roomDropTarget(x, y, sourceEl) {
  const stack = document.elementsFromPoint?.(x, y) || [];
  /* 详情卡视为透明(2026-08-29):它不透明但永远不该替宿主接住拖放,
     否则 placePops 避让不到的角落会让组合悄悄落到错误目标 */
  const direct = stack
    .filter((el) => !el.closest('.node-pop'))
    .map((el) => el.closest?.('.node'))
    .find((node) => node && node !== sourceEl);
  if (direct) return direct;
  const nodes = [...document.querySelectorAll('.node')].filter((el) => el !== sourceEl);
  for (let i = nodes.length - 1; i >= 0; i--) {
    const r = nodes[i].getBoundingClientRect();
    if (x >= r.left && x <= r.right && y >= r.top && y <= r.bottom) return nodes[i];
  }
  return null;
}
let roomClickBlockUntil = 0;
function clearDropHints() {
  document.querySelectorAll('.node.drop-ok').forEach((el) => el.classList.remove('drop-ok'));
}
function finishRoomDrag(e) {
  const d = drag;
  if (!d) return;
  const x = e?.clientX ?? d.lastX,
    y = e?.clientY ?? d.lastY;
  clearDropHints();
  if (d.moved) {
    roomClickBlockUntil = performance.now() + 350;
    const t = roomDropTarget(x, y, d.el);
    if (t) {
      roomUse(d.n.id, t.dataset.id);
      /* 拖到节点上是"使用"不是"摆放":作用后回到拖动前的位置,避免源物件压住目标、挡住目标上的点击型机关(如摩斯/顺序) */ if (
        get(d.n.id)
      ) {
        d.n.x = d.from.x;
        d.n.y = d.from.y;
        const el = document.querySelector('.node[data-id="' + d.n.id + '"]');
        if (el) {
          el.style.left = d.n.x + '%';
          el.style.top = d.n.y + '%';
        }
      }
      drawLinks();
    } else savePos();
  }
  d.el.classList.remove('dragging');
  drag = null;
}
function moveRoomDrag(e) {
  const d = drag;
  if (!d) return;
  const dx = e.clientX - d.lastX,
    dy = e.clientY - d.lastY;
  if (Math.abs(dx) + Math.abs(dy) > 1) d.moved = true;
  d.lastX = e.clientX;
  d.lastY = e.clientY;
  if (!d.moved) return;
  const r = $('stage').getBoundingClientRect(),
    scale = view.scale || 1;
  d.n.x = Math.max(-60, Math.min(160, d.n.x + (dx / scale / r.width) * 100));
  d.n.y = Math.max(-40, Math.min(140, d.n.y + (dy / scale / r.height) * 100));
  d.el.style.left = d.n.x + '%';
  d.el.style.top = d.n.y + '%';
  /* 拖拽组合反馈(2026-08-29):落点目标实时高亮,松手前就知道会作用于谁 */
  const t = roomDropTarget(e.clientX, e.clientY, d.el);
  document.querySelectorAll('.node.drop-ok').forEach((el) => {
    if (el !== t) el.classList.remove('drop-ok');
  });
  if (t && t !== d.el) t.classList.add('drop-ok');
  drawLinks();
}

function roomBind(el) {
  const n = get(el.dataset.id);
  el.onpointerdown = (e) => {
    if (e.button !== 0 || drag) return;
    /* 详情卡内(文本选择/链接/关闭)不触发拖拽 */
    if (e.target.closest('.node-pop')) return;
    e.stopPropagation();
    drag = { n, el, moved: false, lastX: e.clientX, lastY: e.clientY, from: { x: n.x, y: n.y } };
    el.classList.add('dragging');
  };
  el.onpointerup = (e) => {
    e.stopPropagation();
    finishRoomDrag(e);
  };
  el.onpointercancel = () => finishRoomDrag();
  el.onclick = (e) => {
    if (drag) return;
    if (performance.now() < roomClickBlockUntil) return;
    /* 就地详情卡(2026-08-29):卡内点击不冒泡成节点操作;× 关闭 */
    if (e.target.closest('.np-close')) {
      state.activePop = null;
      roomRender();
      return;
    }
    if (e.target.closest('.node-pop')) {
      /* 入口卡例外(2026-08-31):root/compiled-level 挂载时详情卡常开且覆盖整卡,
         点击卡内任意处都应视为点击入口(开始/环视)——否则新手在存档路径上
         点入口卡毫无反应(实测 started 恒 false) */
      if (n.id !== 'root' && n.id !== 'compiled-level') return;
    }
    roomHandle(n);
  };
  el.onkeydown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      roomHandle(n);
    }
  };
}
if (!window.__roomDragBound) {
  window.addEventListener('pointermove', moveRoomDrag);
  window.addEventListener('pointerup', finishRoomDrag);
  window.addEventListener('pointercancel', finishRoomDrag);
  window.__roomDragBound = true;
}

function savePos() {
  const o = {};
  state.nodes.forEach((n) => (o[n.id] = { x: n.x, y: n.y }));
  localStorage.setItem('fav-room-pos', JSON.stringify(o));
}

/* ---------------- 点击处理(数据驱动) ---------------- */
function roomHandle(n) {
  if (!n) return;
  /* 编译关卡物件:used 后仍可点击(检查/顺序),由 compiledHandle 判定;非编译物件维持 used 即失效 */
  if (!n.used || n.compiledItem || n.compiledResult) {
  } else return;
  if (n.id === 'root') {
    roomReveal(['shelf', 'desk', 'wall', 'exit']);
    log('台灯照出三个空间。出口也在,但门把手没有回应。', 'good');
    action();
    update();
    render();
    return;
  }
  if (n.id === 'exit') {
    if (state.clues.has('delivered')) ending();
    else {
      inspect(n);
      frontier('final');
      toast('出口只接受已经改变过状态的收藏。');
    }
    return;
  }
  if (n.kind.includes('zone')) {
    const zr = ROOM_ZONE_REVEAL[n.id];
    let ids = zr ? [...zr.always] : [];
    if (zr)
      zr.gated.forEach((g) => {
        if (hasClue(g.need)) ids.push(...g.ids);
      });
    if (n.id === 'shelf') state.clues.add('escape-seen');
    roomReveal([...new Set(ids)]);
    if (n.id === 'shelf') frontier(state.clues.has('structure') ? 'revisit' : 'shelf');
    if (n.id === 'desk') frontier(state.clues.has('logic') ? 'screen' : 'desk');
    if (n.id === 'wall') frontier('wall');
    log('"' + n.name + '"展开了。先观察物件,再决定是否使用。');
    action();
    update();
    render();
    return;
  }
  inspect(n);
  /* interact 数组:点击型交互 */
  if (n.interact) {
    n.interact.forEach((it) => {
      if (it.type === 'reveal') {
        roomReveal(it.targets || []);
        if (it.log) log(it.log, it.logKind || '');
      } else if (it.type === 'count') {
        if (state.dial < it.need) {
          state.dial++;
          addClue({ clue: '#dial-{0}', params: [state.dial] });
          if (state.dial < it.need) {
            log('索引旋钮移动到第 ' + state.dial + ' 格。');
          } else {
            addClue(it.clue);
            roomReveal(it.reveal || []);
            if (it.log) log(it.log, it.logKind || '');
            if (it.frontier) frontier(it.frontier);
          }
        }
      } else if (it.type === 'log') {
        log(it.log, it.logKind || '');
      } else if (it.type === 'frontier') {
        frontier(it.frontier);
      }
    });
    action();
    update();
    render();
    return;
  }
  if (n.action?.startsWith('sequence-')) roomSequence(n);
  if (n.id === 'screenLog') frontier('wall');
  action();
  update();
  render();
}

/* ---------------- 拖动使用(交互表驱动) ---------------- */
function roomUse(aid, bid) {
  const s = get(aid),
    t = get(bid);
  if (!s || !t) return;
  /* 编译关卡物件 used 后仍可参与拖动(组合/交付),由 compiledUse 判定;非编译物件维持 used 即失效 */
  if (s.used && !(s.compiledItem || s.compiledResult)) return;
  const key = [aid, bid].sort().join('+');
  const rule = ROOM_USE.find((r) => r.pair.slice().sort().join('+') === key);
  if (!rule) {
    $('stage').classList.remove('shake');
    void $('stage').offsetWidth;
    $('stage').classList.add('shake');
    log('"' + s.name + '"靠近"' + t.name + '",但状态没有改变。', 'warn');
    toast('这个物件应该用于别的地方。');
    action();
    render();
    return;
  }
  if (rule.qte) {
    roomQte();
    return;
  }
  (rule.consume || []).forEach((id) => {
    const x = get(id);
    if (x) x.used = true;
  });
  (rule.reveal || []).forEach((id) => {
    const x = get(id);
    if (x) {
      x.hidden = false;
      roomArrange(x.parent); /* 显形即归位(reveal 双轨修复:组合显形此前用旧手写坐标) */
    }
  });
  if (rule.clue) addClue(rule.clue);
  if (rule.log) log(rule.log, rule.logKind || '');
  if (rule.frontier) frontier(rule.frontier);
  action();
  update();
  render();
  if (rule.ending) ending();
}

function roomSequence(n) {
  const want = ROOM_SEQUENCE.order;
  if (n.id !== want[state.sequence.length]) {
    state.sequence = [];
    log('按钮发出一声短促的拒绝。顺序重新开始。', 'warn');
    toast('顺序不对,按钮已复位。');
    action();
    render();
    return;
  }
  state.sequence.push(n.id);
  log(n.name + ' 亮了一下。');
  action();
  if (state.sequence.length === want.length) {
    state.clues.add('loop-done');
    addClue(ROOM_SEQUENCE.clue);
    roomReveal(ROOM_SEQUENCE.reveal || []);
    log(ROOM_SEQUENCE.log, ROOM_SEQUENCE.logKind || '');
    frontier(ROOM_SEQUENCE.frontier);
  }
  update();
  render();
}

/* ---------------- QTE ---------------- */
function roomQte() {
  if (state.clues.has('feedback')) return;
  const m = $('qteModal'),
    target = $('qteTarget');
  m.classList.remove('hidden');
  let left = 7;
  target.style.left = '42%';
  target.style.top = '35%';
  $('qteTime').textContent = left.toFixed(1);
  qteTimer = setInterval(() => {
    left -= 0.1;
    $('qteTime').textContent = Math.max(0, left).toFixed(1);
    if (left <= 0) {
      clearInterval(qteTimer);
      qteTimer = null;
      m.classList.add('hidden');
      log('亮点消失了,但逻辑还在。可以再次尝试。', 'warn');
      toast('QTE 失败,重新拖动逻辑即可重试。');
    }
  }, 100);
  target.onclick = () => {
    clearInterval(qteTimer);
    qteTimer = null;
    target.onclick = null;
    m.classList.add('hidden');
    addClue('#feedback');
    get('shell').hidden = false;
    get('screen').hidden = false;
    roomArrange('shell');
    roomArrange('screen');
    log('你把移动的亮点接回反馈外壳。', 'good');
    frontier('screen');
    action();
    update();
    render();
  };
}

/* ---------------- 提示 / 目标 / HUD ---------------- */
function action() {
  state.actions++;
  state.hintBlocked = false;
  state.hintMark = state.actions;
  updateHint();
}
function frontier(id) {
  state.frontier = id;
  state.hintLevel = 0;
  state.hintBlocked = false;
  state.hintMark = state.actions;
  updateHint();
  roomObjective();
}
/* 统一观察入口(2026-08-31 需求方提议):环顾四周与提示合并——
   有关卡在跑时先做空间回访(发现就绪的隐藏物);没有新变化则顺次落下一条提示。
   HUD 的「环顾四周」与线索便签的「求一条线索」都走这里。 */
function observeAround() {
  const rt = window.__favoriteRoomRuntime;
  if (rt && rt.snapshot && rt.snapshot()) {
    /* 引擎在跑:走空间回访(revisitRoom 是引擎 IIFE 内部函数,经 lookAround 公开入口) */
    if (typeof rt.lookAround === 'function') rt.lookAround();
    return;
  }
  requestHint();
}
function requestHint() {
  if (state.hintBlocked && state.hintMark === state.actions) {
    toast('先让刚才的线索发生一点作用。');
    return;
  }
  /* 编译关卡(2026-08-29 提示修复):旧逻辑查 ROOM_HINTS[state.frontier],
     而 frontier 恒为 'imported',永远回落到原生房间的无关提示;
     现在优先用关卡自身的 hints 渐进展开,观察力 4 格机制不变 */
  const lv = window.__dbg && window.__dbg.level;
  if (lv && Array.isArray(lv.hints) && lv.hints.length) {
    const cost = Math.min(2, state.hintLevel);
    if (state.hintCharges < cost) {
      $('hintCopy').textContent = '观察力暂时不足。完成一个局部谜题后会恢复。';
      return;
    }
    state.hintCharges -= cost;
    $('hintCopy').textContent = lv.hints[Math.min(state.hintLevel, lv.hints.length - 1)];
    state.hintLevel = Math.min(3, state.hintLevel + 1);
    state.hintBlocked = true;
    updateHint();
    toast(state.hintLevel <= 1 ? '提示:从收藏事实入手。' : '提示已展开一层,但下一层要先行动。');
    return;
  }
  const list = ROOM_HINTS[state.frontier] || ROOM_HINTS.explore,
    level = Math.min(2, state.hintLevel),
    cost = level;
  if (state.hintCharges < cost) {
    $('hintCopy').textContent = '观察力暂时不足。完成一个局部谜题后会恢复。';
    return;
  }
  state.hintCharges -= cost;
  $('hintCopy').textContent = list[level];
  state.hintLevel = Math.min(3, state.hintLevel + 1);
  state.hintBlocked = true;
  updateHint();
  toast(level === 0 ? '提示:先观察房间。' : '提示已展开一层,但下一层要先行动。');
}
function updateHint() {
  /* 火漆封印按钮(画布右上常驻):数字=剩余观察力 */
  const sealNum = document.querySelector('.hint-seal b');
  if (sealNum) sealNum.textContent = '· ' + state.hintCharges;
  const askBtn = document.getElementById('hintAsk');
  if (askBtn) askBtn.disabled = state.hintBlocked && state.hintMark === state.actions;
  [...$('hintMeter').children].forEach((x, i) => x.classList.toggle('full', i < state.hintCharges));
}
function roomObjective() {
  let t = '目标:';
  const c = (k) => state.clues.has(k);
  if (get('shelf')?.hidden) t += '先找到收藏室的空间';
  else if (!c('structure')) t += '让两张底层收藏对上折痕';
  else if (!c('loop')) t += '拨动资料架的索引旋钮';
  else if (!c('logic')) t += '回到工作台,让结构产生动作';
  else if (!c('feedback')) t += '让逻辑在即时界面里活起来';
  else if (!c('screen')) t += '把反馈外壳带回黑屏';
  else if (!c('order')) t += '读懂屏幕后面的按钮顺序';
  else if (!c('delivered')) t += '把重新整理的收藏交给出口';
  else t += '回到出口做最后选择';
  $('objective').innerHTML = t + '<br><span>提示只会缩小观察范围,不会替你操作。</span>';
}
function update() {
  const count = ROOM_PROGRESS.filter((x) => state.clues.has(x)).length;
  /* 进度条单一写方(2026-08-31):编译关卡在跑时,顶栏读数/进度条/房间状态由引擎
     (已完成 beat / 总 beat)唯一负责——原生 6 状态计数不再插写,消灭两套数值跳变 */
  const compiledLive = !!(
    window.__favoriteRoomRuntime &&
    window.__favoriteRoomRuntime.hasCompiledLevel &&
    window.__favoriteRoomRuntime.hasCompiledLevel()
  );
  if (!compiledLive) {
    $('doorStatus').textContent = count + ' / 6 个状态';
    $('meter').style.width = (count / 6) * 100 + '%';
    $('roomState').textContent = count === 6 ? '出口已响应' : count ? '房间在变化' : '静止';
  }
  [...$('door').querySelectorAll('.door-locks i')].forEach((x, i) =>
    x.classList.toggle('on', i < count),
  );
  const items = ['skeleton', 'logic', 'shell', 'cleanWall', 'screenLog', 'machine']
    .map(get)
    .filter((n) => n && !n.hidden && !n.used);
  $('inventory').innerHTML = items.length
    ? items.map((n) => `<span class="active">${n.name}</span>`).join('')
    : '<span>尚无物件</span>';
  updateHint();
  roomObjective();
}
function inspect(n) {
  if (!n) return;
  state.activePop = n.id;
  const v = nodeVariant(n),
    it = $('inspectTitle'),
    ic = $('inspectCopy'),
    sr = $('source');
  if (it) it.textContent = v.name;
  if (ic) ic.textContent = v.detail || v.hint || '';
  if (sr) {
    sr.hidden = !v.url;
    sr.href = v.url || '#';
  }
  /* 详情唯一出口 = 节点就地详情卡(node-pop,2026-08-30 定稿):
     曾加画布角落 detailFloat 造成一节点两套详情"随机弹出",已撤——
     详情只出现在被点节点旁,不再有第二处远角内容。 */
  roomRender();
}
/* 谜题面板(2026-08-30 需求方反馈):与节点详情卡同一套纸质 UI,锚定在被点的
   锁节点旁而非固定右缘;📌 可固定——固定后不随点击画布空处关闭。
   打开新面板时,未固定的旧面板自动收起。 */
function openPuzzlePanel(id) {
  const panel = document.getElementById(id);
  if (!panel) return;
  /* 自动升级:keypad 在 index.html,morse/angle 由 engine 动态创建——
     统一在这里补 puzzle-panel 类与 📌 固定钮,不依赖各自的创建代码 */
  if (!panel.classList.contains('puzzle-panel')) {
    panel.classList.add('puzzle-panel');
    const card = panel.querySelector('.modal-card');
    if (card && !card.querySelector('.puzzle-pin')) {
      const pin = document.createElement('button');
      pin.type = 'button';
      pin.className = 'puzzle-pin';
      pin.title = '固定面板(不随点击关闭)';
      pin.textContent = '📌';
      pin.onclick = () => {
        const pinned = panel.dataset.pinned ? '' : '1';
        if (pinned) panel.dataset.pinned = pinned;
        else delete panel.dataset.pinned;
        pin.classList.toggle('pinned', !!pinned);
        pin.title = pinned ? '已固定:点击画布空处不再自动收起' : '固定面板(不随点击关闭)';
      };
      card.appendChild(pin);
    }
  }
  document.querySelectorAll('.puzzle-panel:not(.hidden)').forEach((p) => {
    if (p.id !== id && !p.dataset.pinned) p.classList.add('hidden');
  });
  panel.classList.remove('hidden');
  /* 定位(11.15 复审重写,2026-08-31):.modal 是 fixed——坐标基准是 viewport,
     不是舞台;面板宽度不按 340 估算,直接读显示后卡片真实 rect。
     四向候选(右→左→下→上)取第一个完整放进 viewport 的位置,最后兜底收夹,
     保证确认/关闭按钮永远可见可点。 */
  const card = panel.querySelector('.modal-card');
  requestAnimationFrame(function () {
    const vw = window.innerWidth,
      vh = window.innerHeight,
      M = 8,
      GAP = 14;
    const cw = card ? card.offsetWidth : Math.min(330, vw - 24);
    const ch = card ? card.offsetHeight : 220;
    const anchorId = window.__lastUseTarget || state.activePop;
    const host = anchorId ? document.querySelector('.node[data-id="' + anchorId + '"]') : null;
    let x,
      y;
    if (host) {
      const hr = host.getBoundingClientRect();
      /* 四向候选:每项给出完整放进 viewport 的坐标,放不下则 null */
      const cand = [];
      const rightX = hr.right + GAP;
      if (rightX + cw + M <= vw)
        cand.push([rightX, Math.min(Math.max(M, hr.top - 8), vh - ch - M)]);
      const leftX = hr.left - GAP - cw;
      if (leftX - M >= 0) cand.push([leftX, Math.min(Math.max(M, hr.top - 8), vh - ch - M)]);
      const belowY = hr.bottom + GAP;
      if (belowY + ch + M <= vh)
        cand.push([Math.min(Math.max(M, hr.left + hr.width / 2 - cw / 2), vw - cw - M), belowY]);
      const aboveY = hr.top - GAP - ch;
      if (aboveY - M >= 0)
        cand.push([Math.min(Math.max(M, hr.left + hr.width / 2 - cw / 2), vw - cw - M), aboveY]);
      if (cand.length) {
        x = cand[0][0];
        y = cand[0][1];
      } else {
        /* 四向都放不下(卡片比 viewport 还大或锚点居中):兜底右贴 + 双轴收夹 */
        x = Math.max(M, Math.min(vw - cw - M, hr.right + GAP));
        y = Math.max(M, Math.min(vh - ch - M, hr.top - 8));
      }
    } else {
      /* 无锚点:右缘悬挂(默认位),垂直也按内容收夹 */
      x = Math.max(M, vw - cw - 18);
      y = Math.max(M, Math.min(vh - ch - M, 84));
    }
    panel.style.left = Math.round(x) + 'px';
    panel.style.top = Math.round(y) + 'px';
    panel.style.right = 'auto';
    panel.style.bottom = 'auto';
  });
}
window.__openPuzzlePanel = openPuzzlePanel;
document.querySelectorAll('.puzzle-panel .puzzle-pin').forEach((btn) => {
  btn.onclick = () => {
    const panel = btn.closest('.puzzle-panel');
    if (!panel) return;
    const pinned = panel.dataset.pinned ? '' : '1';
    if (pinned) panel.dataset.pinned = pinned;
    else delete panel.dataset.pinned;
    btn.classList.toggle('pinned', !!pinned);
    btn.title = pinned ? '已固定:点击画布空处不再自动收起' : '固定面板(不随点击关闭)';
  };
});

function log(t, k = '') {
  const d = document.createElement('div');
  d.className = 'event ' + k;
  d.textContent = t;
  $('log').prepend(d);
  /* 画布左下的记录 ticker 同步最新一条(沉浸式:日志不再占常驻面板) */
  const latest = document.getElementById('logLatest');
  if (latest) {
    latest.textContent = t;
    const tick = document.getElementById('logTicker');
    if (tick) {
      tick.classList.remove('flash');
      void tick.offsetWidth;
      tick.classList.add('flash');
    }
  }
}
function toast(t) {
  clearTimeout(toastTimer);
  $('toast').textContent = t;
  $('toast').classList.add('show');
  toastTimer = setTimeout(() => $('toast').classList.remove('show'), 2400);
}
function ending() {
  if (state.ending) return;
  state.ending = true;
  $('endingModal').classList.remove('hidden');
  $('door').classList.add('open');
}
document.querySelectorAll('[data-ending]').forEach(
  (b) =>
    (b.onclick = () => {
      $('endingModal').classList.add('hidden');
      const t = b.dataset.ending;
      const text =
        t === 'continue'
          ? '你把机器留下,下一步任务已经写在外壳里。'
          : t === 'archive'
            ? '你把机器关掉,但保留了完整的构造记录。'
            : '你把这间房的规则封装成了下一间房的种子。';
      log(text, 'good');
      $('roomState').textContent = t === 'archive' ? '已归档' : '出口之后';
      toast(text);
    }),
);

/* 引导线(2026-08-31 重构):线元素按「父→子」键持久复用,不再每次绘制全量重建——
   新线淡入 0.5s(与子节点 .arrive 0.5s 同拍),端点隐藏/用掉时淡出;平移缩放的
   高频重绘只更新坐标,不再打断过渡。 */
const linkEls = new Map();
const linkTweens = new Map();
let linkTicker = 0;
function drawLinks() {
  const svg = $('links');
  if (!svg) return;
  if (svg.childElementCount === 0) {
    linkEls.clear();
    linkTweens.clear();
  } /* 外部清空画布时同步登记表 */
  const want = new Map();
  state.nodes.forEach((n) => {
    if (n.hidden || n.used) return;
    /* 父端锚点与物件飞入起点同为 originOf(2026-08-30):见函数处注释 */
    const p = originOf(n);
    if (!p) return;
    const a = p.id;
    const x = document.querySelector(`.node[data-id="${a}"]`),
      y = document.querySelector(`.node[data-id="${n.id}"]`);
    if (!x || !y) return;
    want.set(a + '→' + n.id, {
      x1: x.offsetLeft + x.offsetWidth / 2,
      y1: x.offsetTop + x.offsetHeight / 2,
      x2: y.offsetLeft + y.offsetWidth / 2,
      y2: y.offsetTop + y.offsetHeight / 2,
      /* 子节点的交错延迟:线的生长与节点飞入同时开始、同拍结束 */
      fd: parseFloat((y.style && y.style.getPropertyValue('--fd')) || '0') || 0,
    });
  });
  linkEls.forEach((el, key) => {
    if (!want.has(key)) el.classList.add('link-hidden'); /* 淡出停放,再现时淡入 */
  });
  want.forEach((w, key) => {
    let el = linkEls.get(key);
    const isNew = !el;
    if (!el) {
      el = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      /* 新生连线不再淡入(2026-08-30):它的起始长度就是 0(端点停在父锚点),
         本身不存在"凭空出现"的突兀;再叠一层 0.5s 淡入,恰好把"从父锚点被孩子
         拉出来"的这 0.5s 盖住——实测 144ms 时线只有 0.3 不透明度,玩家看到的
         就只剩淡入,和节点飞入对不上拍。淡入只留给 link-hidden 后重新出现的线。 */
      svg.appendChild(el);
      linkEls.set(key, el);
    }
    el.classList.remove('link-hidden');
    el.setAttribute('x1', w.x1);
    el.setAttribute('y1', w.y1);
    if (!linkTweens.has(el)) {
      el.setAttribute('x2', w.x2);
      el.setAttribute('y2', w.y2);
    }
    if (isNew && typeof w.fd === 'number') {
      /* 生长同步(2026-08-31):子节点沿「父→槽位」向量飞入(0.5s spring,
         --fd 交错)——线沿**同一向量**从父锚点同步生长,像被孩子拉出来。
         WAAPI 不支持 line 的 x2/y2 几何属性(关键帧被静默丢弃),故手写补间。 */
      linkTweens.set(el, {
        fx: w.x1,
        fy: w.y1,
        tx: w.x2,
        ty: w.y2,
        start: performance.now(),
        delay: w.fd,
        dur: 500,
      });
      el.setAttribute('x2', w.x1);
      el.setAttribute('y2', w.y1); /* delay 段停在父锚点 */
      startLinkTicker();
    }
  });
  /* --ease-spring 同款缓动:cubic-bezier(0.34,1.45,0.64,1) 求解(二分 x→t,取 y) */
  function springAt(k) {
    const x1 = 0.34,
      y1 = 1.45,
      x2 = 0.64,
      y2 = 1;
    const bx = (t) => 3 * t * (1 - t) * (1 - t) * x1 + 3 * t * t * (1 - t) * x2 + t * t * t;
    const by = (t) => 3 * t * (1 - t) * (1 - t) * y1 + 3 * t * t * (1 - t) * y2 + t * t * t;
    let lo = 0,
      hi = 1,
      t = k;
    for (let i = 0; i < 14; i++) {
      t = (lo + hi) / 2;
      if (bx(t) < k) lo = t;
      else hi = t;
    }
    return by(t);
  }
  function startLinkTicker() {
    if (linkTicker) return;
    const step = () => {
      const now = performance.now();
      linkTweens.forEach((t, el) => {
        const elapsed = now - t.start - t.delay;
        if (elapsed <= 0) {
          el.setAttribute('x2', t.fx);
          el.setAttribute('y2', t.fy);
          return;
        }
        const k = Math.min(1, elapsed / t.dur),
          e = springAt(k);
        el.setAttribute('x2', t.fx + (t.tx - t.fx) * e);
        el.setAttribute('y2', t.fy + (t.ty - t.fy) * e);
        if (k >= 1) linkTweens.delete(el);
      });
      linkTicker = linkTweens.size ? requestAnimationFrame(step) : 0;
    };
    linkTicker = requestAnimationFrame(step);
  }
}

/* ---------------- 画布视图 ---------------- */
const view = { x: 0, y: 0, scale: 1 };
function applyView() {
  const transform = `translate(${view.x}px,${view.y}px) scale(${view.scale})`;
  $('nodes').style.transform = transform;
  $('links').style.transform = transform;
  $('door').style.transform = transform;
  $('zoomReadout')?.replaceChildren(document.createTextNode(Math.round(view.scale * 100) + '%'));
  drawLinks();
}
function resetView() {
  view.x = 0;
  view.y = 0;
  view.scale = 1;
  applyView();
}
function zoomAt(next, cx, cy) {
  const stage = $('stage'),
    r = stage.getBoundingClientRect(),
    beforeX = (cx - r.left - view.x) / view.scale,
    beforeY = (cy - r.top - view.y) / view.scale;
  view.scale = Math.max(0.55, Math.min(1.8, next));
  view.x = cx - r.left - beforeX * view.scale;
  view.y = cy - r.top - beforeY * view.scale;
  applyView();
}
function installCanvasTools() {
  const stage = $('stage'),
    tools = document.createElement('div');
  tools.className = 'canvas-tools';
  tools.innerHTML =
    '<button id="zoomOut" type="button" title="缩小画布">−</button><span class="zoom-readout" id="zoomReadout">100%</span><button id="zoomIn" type="button" title="放大画布">+</button><button id="zoomReset" type="button" title="重置画布位置和缩放">重置</button>';
  stage.appendChild(tools);
  $('zoomOut').onclick = () =>
    zoomAt(view.scale - 0.1, stage.clientWidth / 2, stage.clientHeight / 2);
  $('zoomIn').onclick = () =>
    zoomAt(view.scale + 0.1, stage.clientWidth / 2, stage.clientHeight / 2);
  $('zoomReset').onclick = resetView;
  stage.addEventListener(
    'wheel',
    (e) => {
      e.preventDefault();
      zoomAt(view.scale + (e.deltaY < 0 ? 0.08 : -0.08), e.clientX, e.clientY);
    },
    { passive: false },
  );
  let pan = null;
  stage.addEventListener('pointerdown', (e) => {
    /* 画布浮层(封印/便签/记录)不是平移把手,也不得被指针捕获吞掉 click */
    if (e.target.closest('.node,.canvas-tools,.hint-seal,.hint-float,.log-ticker,.log-float')) return;
    if (state.activePop) {
      state.activePop = null;
      roomRender();
    }
    /* 点击画布空处:未固定的谜题面板随之收起(固定的📌保留) */
    document.querySelectorAll('.puzzle-panel:not(.hidden)').forEach((p) => {
      if (!p.dataset.pinned) p.classList.add('hidden');
    });
    pan = { x: e.clientX, y: e.clientY, px: view.x, py: view.y };
    stage.setPointerCapture(e.pointerId);
    stage.classList.add('panning');
  });
  stage.addEventListener('pointermove', (e) => {
    if (!pan) return;
    view.x = pan.px + e.clientX - pan.x;
    view.y = pan.py + e.clientY - pan.y;
    applyView();
  });
  stage.addEventListener('pointerup', () => {
    pan = null;
    stage.classList.remove('panning');
  });
  stage.addEventListener('pointercancel', () => {
    pan = null;
    stage.classList.remove('panning');
  });
}

/* ---------------- 启动 ---------------- */
$('start').onclick = () => $('intro').classList.add('hidden');
const hintAskBtn = document.getElementById('hintAsk');
if (hintAskBtn) hintAskBtn.onclick = observeAround;
/* 11.12:#reset 是产品动作「重置本关」——优先产品层 __favoriteRoomHome.resetCurrentLevel
   (保留关卡记录、重建初始运行态、把初始态快照写回 progress),引擎运行时入口次之,
   底层 roomReset 兜底。此前直接绑 roomReset() 会把生成关卡重置成固定 Room 02
   (UI/运行态/存档三方失配)。 */
$('reset').onclick = () => {
  const home = window.__favoriteRoomHome;
  if (home && home.resetCurrentLevel) return void home.resetCurrentLevel();
  if (window.__favoriteRoomRuntime && window.__favoriteRoomRuntime.resetCurrentLevel)
    return void window.__favoriteRoomRuntime.resetCurrentLevel();
  roomReset();
};
window.addEventListener('resize', drawLinks);
/* 兼容层:供 import 管线 / compiled runtime / 产品壳调用 */
var hints = ROOM_HINTS;
function render() {
  roomRender();
}
function reset() {
  roomReset();
}
function reveal(ids) {
  roomReveal(ids);
}
function combine(a, b) {
  roomUse(a, b);
}
function objective() {
  roomObjective();
}
installCanvasTools();
roomReset();
render();
applyView();

/* ---------- 聚焦光效(2026-08-31 需求方反馈) ----------
   跟随鼠标的暖光斑 + 边缘晕影,强化「暗房里举灯探索」的空间感。
   纯视觉:pointer-events:none,不影响点击/拖拽;rAF 节流,只写自定义属性
   (transform 平移在合成器层完成);触屏不激活;仅在有已挂载关卡时淡入。 */
(function initFocusGlow() {
  const stage = document.getElementById('stage');
  if (!stage) return;
  let glow = document.getElementById('focusGlow');
  if (!glow) {
    glow = document.createElement('div');
    glow.id = 'focusGlow';
    stage.appendChild(glow);
  }
  let raf = 0,
    mx = 0,
    my = 0;
  const apply = function () {
    raf = 0;
    glow.style.setProperty('--mx', mx + 'px');
    glow.style.setProperty('--my', my + 'px');
  };
  stage.addEventListener(
    'pointermove',
    function (e) {
      if (e.pointerType === 'touch') return;
      const r = stage.getBoundingClientRect();
      mx = e.clientX - r.left;
      my = e.clientY - r.top;
      if (!raf) raf = requestAnimationFrame(apply);
      /* 只在关卡已挂载时点亮(首页/工房不散光) */
      if (
        !glow.classList.contains('on') &&
        window.__favoriteRoomRuntime &&
        window.__favoriteRoomRuntime.snapshot()
      )
        glow.classList.add('on');
    },
    { passive: true },
  );
  stage.addEventListener('pointerleave', function () {
    glow.classList.remove('on');
  });
})();
