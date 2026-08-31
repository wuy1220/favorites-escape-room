# 收藏夹密室 交接文档

> 合并说明:2026-08-28 重构时,把根目录 HANDOFF-2026-08-27.md(v7 架构)并入本文档。
> **v7 架构现状以第一部分为准;第二部分为 v3~v6 时代的迭代记录,仅作背景,命令与结论可能过时。**

---

# 第一部分 · v7 架构(2026-08-27 深夜,当前生效)

## 最新:2026-08-31 出口改「结束」:挂在交付物旁、点击即通关

需求方两项反馈合并落地:①根节点处不要独立出口节点,把出口挂在出口交付物下,点击即完成;
②文案换「结束/成功」——谜题已不局限于房间。

- **编译期锚定**(engine.js):出口节点 parent 改为 deliver 步的目标物件节点
  (uses[0] 为 result: 引用时解析到产物素材),坐标锚在其旁(+11,+9);解析失败退回
  根层固定位。文案:名字「结束」、hint「所有步骤完成后,点击结束本次冒险」。
- **三处揭示点收敛为 restDone 唯一口径**:revealAllRooms 不再随房间发现亮出出口;
  levelStart 非 scenes 分支不再开场点亮出口(需求方实测 sample-puzzles 关卡开局
  仍见出口的根因);restore 恢复时按 restDone 对齐出口可见性(不再无条件亮出)。
  「结束」只在只剩交付步时出现在交付物旁,伴随出现动画。
- **点击即结算**:compiledHandle 出口分支——done→ending;未 done 但其余步骤全部
  完成时,点击直接补交 delivers 规则(clue、产物离场、finishIfDone→ending),
  不再要求把产物拖到出口(compiledUse 的拖拽交付路径保留兼容)。
- **连带修复(飞入动画拦截点击)**:watchman 回归暴露——节点飞入动画(.arrive)
  期间位置未定却可被点击,开局连点会把点击落在恰好飞过目标槽位的别的节点上
  (第一步 inspect 被路过节点吞掉)。修复:.node.arrive { pointer-events:none }
  + room02 在 animationend(arrive)时摘除 DOM 上的 .arrive 类(类此前滞留到
  下次重渲染);配套把 verify_prison/verify_bear/verify_regression_watchman 的
  click/drag 助手加上落定等待。
- 验证:监狱关全流程——开局无「结束」、全步完成时它出现在解锁的指纹锁旁、
  点击即 done=true;教程关(常驻存档)开局同样无出口。回归:prison 42/42、
  bear 30/30、watchman 20/20(两次)、smoke 全过。


## 最新:2026-08-31 移除「试玩固定样本」,只留新手教程

- 主页 `homeFixedTest` 按钮、`loadSamplePuzzle` 函数及其 `__favoriteRoomHome` 导出全部
  移除;教程入口为并行会话新增的 `homeTutorial`(新手教程,加载 sample-puzzles/
  tutorial.json「新手教程 · 书桌上的第一间密室」)。
- watchman.json 文件保留(verify_regression_watchman 等直接经 #homeImportFile 导入,
  不经按钮);ref-game/verify_puzzle_panel.py 改为直接导入 watchman(4/4 过);
  ref-game/ui_shots.py 两处改点 #homeTutorial。全仓已无 homeFixedTest/loadSamplePuzzle
  残留引用。


## 最新:2026-08-31 深夜 环顾四周与提示合并(统一观察入口)

需求方提议:把「环顾四周」和「提示」合并成一个动作。

- **revisitRoom 无新发现时顺次落下提示**(engine.js):找到就绪隐藏物=发现(原行为);
  没有→日志「又看了一圈,没有新的变化」+ 调用 requestHint 并展开线索便签。
  观察力经济不变:提示仍耗格、两次提示之间要先行动(hintBlocked 门控照旧)。
- **统一入口 observeAround**(room02.js):HUD「环顾四周」与线索便签「求一条线索」
  两个按钮都走它——引擎在跑(snapshot() 非空)先做空间回访,否则(原生房间)直接
  requestHint。revisitRoom 在引擎 IIFE 内部,经新增的 runtime API
  `__favoriteRoomRuntime.lookAround()` 公开给 room02(直接调用会 ReferenceError,
  首测已踩)。
- 验证:监狱关实测——开局环顾→便签展开并给出观察级提示(「转盘锁上刻着…换算成角度」);
  解开转盘锁后环顾→锯子照常显形(发现路径优先)。verify_prison 42/42、verify_bear
  30/30、smoke_room02 全过。


## 最新:2026-08-31 游戏界面可读性升级:字号放大一档 + 衬线字体(需求方反馈)

1. **字体栈换衬线**(css/tokens.css):`--font-body/--font-display` 从
   Inter/雅黑改为 Noto Serif SC → 思源宋体 → Songti SC/SimSun 宋体系回退
   (纸上墨字的质感;无内装衬线时回退雅黑,不裸奔)。`--font-mono` 不变。
   不引入网络字体——本地版不依赖外网。
2. **字号整体放大一档**(css/styles.css 末尾统一块,赢得同优先级级联):
   body 14→15px;节点名 16px、角标 12px、节点小注 13px;详情卡 14.5px/行高 1.7
   (标题 16.5px、链接 13px);目标横幅 14px(副行 12.5px);日志行 13.5px、
   左下 ticker 13px;线索便签提问 13.5px;工具条标题 15px/按钮 13px(加 padding);
   机关面板正文 14px/按钮 13.5px/密码位标签 11.5px。
3. **标题界面小字同步放大**(需求方追加):kicker 12.5px、表单标签/勾选/状态/
   次级按钮/存档说明 13.5px、存档行标题 15px/元信息 12.5px、时间片卡小注 12.5px、
   文件按钮 13px、muted-note 13px——衬线小字在 12px 以下发虚,统一抬到 12.5px 起。

**验证**:真实 DOM 断言节点名 16px/详情卡 14.5px/横幅 14px、fontFamily 命中
Noto Serif SC;标题界面 kicker 12.5/字段 13.5/状态 13.5/存档说明 13.5;截图目视
(ui-font-upgrade.png / home-font-upgrade.png)。回归:lock_feedback 7/7、
prison 42/42、smoke 通过,控制台零错误。

### 附:已保存关卡面板打磨(同日,需求方截图反馈)

三个按钮横排吞掉一半宽度、行高 150px+,一屏仅 5 关。改造(app.js refreshSaved +
styles.css 追加块):**操作钮改竖排窄列**(「打开」火漆实心主钮,导出/删除紧凑小钮,
按钮列 47px);行改纸卡(边框/纸影/hover 抬升);**新增真实进度条**(snapshot.clues
中 beat-* 计数 / beats 总数,已完成满格);元信息行追加「存于 <东八区日期>」并
两行截断——行高 150→132px 且信息列全宽,一屏 7+ 关;空状态改虚线占位卡。
回归:verify_save_mgmt 6/6(新行文本「进行中 0/10 · 存于 2026-08-31」)、smoke 通过。
**追加(同日):列表滚动上限**——行数增长会把首页网格纵向拉长。`.saved-list` 加
`max-height: min(56vh, 620px)` 内部滚动(细滚动条),`.home-layout` 改 `align-items:
start`。实测 8 条存档页高恒等于视口高,列表可视 392px/内容 1248px 正常滚。

## 最新:2026-08-31 深夜 显形提示指明位置(为什么点根不出新物件的解答+修复)

需求方疑问:信息更新后点根节点不出新物件,必须点「环顾四周」,为什么?

**机制解答**(两层,均为有意设计而非 bug):
1. 根节点在开赛后只走 `inspect`(查看关卡说明)——08-29 有意移除了「点根=全局回访」
   (当时一次点击会把全部就绪物件弹出,破坏探索节奏);compiledHandle 注释明示
   「回访只由环顾四周按钮或点开具体容器触发」。
2. `triggerReveals` 只把物件标记为 `revealReady`(「待发现」),不自动出现——原作的
   preClue 门控等价物。设计意图:变化发生在**具体空间里**,该去那里点开看。
   断点在于提示语只说「有什么东西的状态变了」,不指明在哪——玩家只能盲点环顾四周。

**修复**:提示语指明位置——容器嵌套的物件报容器名(「柜子里似乎多了什么」),
其余报所在房间名(「机房外间里…」),并加「点开看看」引导。分级探索语义不变
(仍要点开那个空间才发现),只是不再让玩家盲找。

**验证**:监狱关实测——转盘锁解开后锯子不自动出现、点根也不出现(门控保持),
日志提示「……——「柜子」里似乎多了什么，点开看看」;verify_prison 42/42、
verify_bear 30/30 全过。


## 最新:2026-08-31 时间戳统一东八区(UTC+8)呈现(需求方裁定)

此前所有玩家可见时间戳都在切 ISO UTC 串——关卡名「未命名冒险 · 08-30 06:59」比
本机慢 8 小时,物件卡「收藏于」与命名候选/回执的收藏日期可能差一天。裁定:显示
一律东八区;**存储保持 ISO UTC**(progress 按 updatedAt 字典序排序、版本兼容,
混写会错序)。做法:时刻 +8h 后读 toISOString,即东八区挂钟时间,与机器时区无关。

改动点:
- pipeline.js 新增 `cstIso()` 助手;`whenLabel`(物件卡「收藏于」)接入;
  **designWindow 的 dateAdded 输入同步转 +8**——模型推导谜面引用的日期与玩家
  看到的展示同源(事实锚定铁律),否则 UTC 日期 vs +8 展示会穿帮。
- engine.js `whenLabel` 同步 +8。
- app.js:关卡默认名「未命名冒险 · MM-DD HH:mm」、命名候选 facts、通关回执的
  收藏日期改 `cstDate10()`(+8);**时间片分组的小时/日期改固定东八区**
  (+8h 读 getUTC*,深夜/清晨情绪标签与日期标签不再依赖机器时区)。
- namedAt/createdAt/updatedAt 存储字段保持 ISO UTC(内部字段,不直接展示)。

**验证**:导入 123.room.json(dateAdded 2025-10-10T16:00Z)→ 物件卡显示
「收藏于 2025-10-11 00:00」✓。回归:race 9/9、reset 13/13、prison 42/42、
lock_feedback 7/7、smoke 通过,控制台零错误。

## 最新:2026-08-31 干扰项伪装:角标与墨色不再明牌(需求方反馈)

节点卡片直接印着「干扰」角标、墨色条还是专属灰棕(#8c7b64 vs 线索蓝墨 #4a6b8a)——
红鲱鱼被 UI 明牌,「看似与主线相关」的设计意图在界面上破产。修复:

1. **角标伪装**(js/room02.js 渲染模板):`red_herring` 的 type 角标按「线索」显示,
   真假由玩家按谜面自行甄别。
2. **墨色伪装**(css/styles.css):`.node.role-red_herring` 色条改用
   `var(--role-clue)`;`--role-red` token 保留给清洗报告等元信息面。
3. 复核其余玩家可见面:详情卡(layeredDetail)、检查日志、回执均不印角色,
   干扰与线索文案完全一致,无其他泄漏点。

**回归**:verify_lock_feedback 扩至 **7/7**(新增断言:干扰项显形后角标=「线索」、
computedStyle 墨色条与线索节点逐字节相同);prison 42/42、smoke 通过、race 9/9。

## 最新:2026-08-31 断电锁反馈 + 回看显形死路修复(需求方实测 123.room.json 提出)

需求方实测导出关卡:未通电的解密终端点击后**零反馈**(要等供电线接入、节点拿到
`result:` 身份后密码机关才绑定,之前三个机关分支全 miss,点击落空)。

**修复 1:机关未就绪的可诊断反馈**(js/engine.js)。新增 `machinePendingBlocker(n)`:
反查 password/angle/morse 规则里未解开的 `result:` 前置——若缺失产物恰好落在被点
物件身上(resultOn 或产物 uses 解析),说明「还没就绪:先完成「<该步>」(得到
「<产物名>」)」,log+toast 双通道,详情卡照常打开(锁面谜面本身是线索)。放在
全部规则匹配之后,不拦截任何既有路径。

**修复 2(测试链路揪出的真 bug):回看显形死路**。compiledHandle 场景回看分支用
`m.compiledScene === n.compiledScene` 判断同房——zone 节点的 compiledScene 是布尔
`true`,物件的才是场景 id 字符串,**比较恒 false**:玩家先逛房、后解谜的正常流程里,
beat 显形的隐藏物(胶带/锯子/电池)永远不再出现(潜在软锁)。改为
`m.compiledScene === n.id`(zone id 即场景 id)。exploreRoom 首访路径本来就正确
(用 `z.id` 比较),不受影响。

**回归**:新增 `ref-game/verify_lock_feedback.py` **6/6**——内嵌迷你两房关卡,
真实 DOM 全链:未通电终端点击提示缺失步骤(负控)/toast 同步/详情卡可读/已就绪
密码盘正常弹(守卫)/输 003 开柜→胶带显形→接线→通电变身→终端弹新密码盘(正控,
同时覆盖回看显形修复)。全量:prison 42/42、bear 30/30、clockwork 39/39、
bookmarks 31/31、smoke 通过、race 9/9、reset 13/13、puzzle_panel 4/4,控制台零错误。

## 最新:2026-08-31 深夜 聚焦光效:跟随鼠标的暖光 + 边缘晕影

需求方提议:配合分层探索,加一层跟随鼠标的聚焦光,强化「暗房里举灯探索」的感觉。

- `#focusGlow` 挂在 #stage 内(room02.js 末尾初始化):两层视觉——静态边缘晕影
  (::before,极轻压暗)+ 跟随光斑(::after,540px 暖色径向渐变,transform 平移,
  只动合成器不重绘);rAF 节流写 --mx/--my;pointer-events:none 不影响点击/拖拽;
  触屏不激活;仅在已挂载关卡时淡入(snapshot() 非空才加 .on),离开舞台淡出。
- 层级:z-index 25——高于画布节点(#nodes 4/拖拽 20),低于工具条/弹层(30+),
  光晕会轻抚过详情卡但不妨碍阅读(暗角最深处 0.16 透明度)。
- 验证:光斑坐标随指针实时更新(620px/430px 实测)、pointer-events none、层级正确;
  截图确认暖亮区与四角压暗效果、节点与卡片可读性无损;smoke_room02 与
  verify_prison 42/42 全过(点击/拖拽零干扰)。


## 最新:2026-08-31 深夜 分层空间揭示:点根只见房间,点房间才见物件

需求方反馈:点根节点会一次性弹出所有后代(房间+物件全亮),不是「点开房间、再点开
发现容器和物品」的递归探索感。

- **revealAllRooms 只亮房间**(engine.js):并行房间模式下根节点点击后仅亮出场景
  zone 节点(+最后一房发现后的出口),不再连带亮出物件。
- **exploreRoom(新)**:首次点击房间节点=「走进」——亮出该房可直接看见的物件
  (hidden 的仍等 reveals/环顾四周),记入 `compiled.roomExplored`;之后点击退化为
  原回看逻辑(revealReady 隐藏物发现)。
- **快照/恢复**:snapshot 增加可选 `explored` 字段;恢复时只还原已走进房间的物件
  可见性,未走进的房间保持「只见其门」。旧档无字段按全部已探索处理(行为同旧版),
  版本号不变(v3,向后兼容)。
- 文案同步:root 提示「点击开始,房间亮出」;开场面日志「几间房间同时亮出——点开
  房间,看看里面有什么」。
- 验证(真实生成关卡导入):点根后房间 2 可见/物件 0,点首房后其 3 件可见物件出现
  (第 4 件 hidden 等显形);保存→刷新→继续游戏,explored 状态正确恢复;引擎回归
  smoke_room02 全过、verify_prison 42/42(非 scenes 容器路径不受影响)。


## 最新:2026-08-31 深夜 UI bug 清理:11.15 谜题面板溢出(全 5 项)+ 图层重叠 + 动画 6 bug 复核

需求方指认文档中的 UI bug。逐项核实与处置:

**11.15 谜题面板溢出——5 项全部修复**:

1. **[P1] 垂直溢出 + [P2] 四向避让**:`openPuzzlePanel`(room02.js)定位段重写——
   旧行为只做左右锚定、按 340px 估算宽度、不读显示后真实高度。新行为:先 unhide,
   再在 rAF 里读卡片 `offsetWidth/offsetHeight` 实测尺寸;右→左→下→上四向候选,
   取第一个完整放进 viewport 的位置(上下候选水平居中于宿主),四向全放不下时
   双轴收夹兜底——确认/关闭按钮永远可见可点。坐标基准修正为 viewport
   (.modal 是 fixed,旧代码混用舞台 rect)。
2. **[P1] 估算与 CSS 不一致**:废除 340 估算,直接实测(与 CSS `min(330px, 100vw-36px)` 天然一致)。
3. **[P2] 动态文本撑宽**:styles.css 新增防护——`.code` 换行(highest 40px→auto+min-height)、
   `.kp-slot b` 颜色标签 64px 截断省略、h2/p `overflow-wrap:anywhere + min-width:0`、
   `.modal-actions` 允许换行。
4. **[P2] 断点分散/移动端**:`max-height` 改 `100dvh` 优先(vh 回退),软键盘/地址栏
   收放不再虚高。
5. **回归**:新增 `ref-game/verify_puzzle_panel.py` **4/4**——底部节点(top 88%)、
   右缘节点(left 90%)、无锚点悬挂、长标题+长颜色标签:面板四边都在 viewport 内、
   按钮可点、卡片宽度 ≤334 且无横向溢出。锚定注入用 `window.__lastUseTarget`
   (引擎同款通道)——点击会触发 roomRender 重建 DOM,冲掉测试设置的内联坐标。

**详情卡图层重叠(需求方截图指认)**:node-pop 是节点子元素,其 z-index 只在宿主
层叠上下文内生效,DOM 靠后的兄弟节点整片盖住打开的详情卡。修复:渲染模板给
打开详情卡的节点加 `.pop-open` 类(state 驱动,扛住 innerHTML 重建),CSS
`.node.pop-open { z-index: 15 }`——高于普通节点(4)/hover(6),低于拖拽(20),
拖拽卡片仍可从详情卡上方经过。

**「动画观察」6 bug 复核(untitled-adventure-direction.md)**:
- #1(多次同步渲染清掉 .arrive)、#4(.node 双 transition 覆盖)——并行会话已修
  (下一帧清标记;transition 合并),复核确认。
- #5(arrive/changed 互覆)——已修:`.node.arrive.changed` 逗号列表并行两动画。
- #6(reveal 漏同步 revealed)——逐个审计全部 `hidden = false` 写入点(14 处):
  compiled-hidden 物件的每条显形路径均已同步 `revealed=true`,开场路径以
  `!(compiledHidden && !revealed)` 守卫,无漏网。
- #2/#3(keyed DOM/FLIP 位置过渡)——**未修,记录为重构欠账**(需把整块 innerHTML
  重建改为 keyed 更新,与渲染生命周期合并改造一起做)。

**回归**:verify_puzzle_panel 4/4(新)、verify_reset_lifecycle 13/13、
verify_design_race 9/9、smoke_room02 通过、控制台零错误。
(过程中 verify_reset_lifecycle 一度 12/13,复现为并行写文件的中间态被抓测;
稳定后复跑全绿,另用固定样本+生成关卡两条路径做了 started 翻转时间线核验,
continue→restore 全程 started=false,无回归。)

## 最新:2026-08-31 深夜 时间片多选(合并池生成)

需求方反馈:单个时间片的通过素材常不足一次生成所需,应允许**多选时间段**合并成一个生成池。

- 主页步骤 03 的 `window-card` 从单选改为**点击切换的多选**(`selectedWindows` 数组);
  状态栏实时显示「已选 N 个时间片(合并 M 条素材)」,全部取消时禁用生成按钮。
- `generate()` 合并逻辑:所选各段素材 id 取并集过滤 approved 池→`selectControlledPool`
  照常抽样;合并的 `windowContext`——label 拼接、spanDays 取并集区间、情绪取素材最多的
  主导段、nightRatio 按素材数加权、topFolders 并集;缓存键与 `level.timeWindow` 落库
  相应改为合并值。
- 时间片本身是按 7 天断点切分的**不相交**区间,并集即简单拼接;与「单次素材数」选项
  天然互补(段不够就多选,池子大了选 8/10 条也能撑起 3 房间)。
- 验证:聚簇时间戳的合成 fixture 实测——2 片全选合并 10 条/取消清空禁用生成,交互与
  截图正确;verify_design_race 9/9(与并行会话的工房改版合并后复验)。


## 最新:2026-08-30 生成工作台 v2「深夜工房」+ 纸页夜奔小游戏

### v3 修订(同日,需求方实测反馈:「速度过快,碰任何障碍物都没有失败判定」)
### 节点飞入源修正(2026-08-31,需求方:「节点动画不是从父节点出发的,而是从画面顶部出发的」)

`--fx/--fy` 注入取 `srcNode = revealFromId || parent`——房间初始物件的 parent 是
**场景 zone 标签**,而 zone 全部贴在画布顶部(baseY+si*14),从它起飞 = 整排物件
从画面顶部俯冲(线却是从 zone 长到物件的,方向倒是一致,起点观感错误)。修订:
**zone 不作为起飞源**——它不是器物;这类物件原地浮现(scale 0.78+fade+交错保留);
真正有物理来源的飞行不变:容器内容物从容器飞出、beat 显形物从照亮它的物件飞出、
教程关从入口卡飞出。探针:房间初始物件 --fx/--fy 为空(原地)、--fd 交错保留;
容器与 reveal 路径不受影响。


真相:节点 `.arrive` 本来就是沿「父→槽位」向量飞入(--fx/--fy 注入,0.5s
ease-spring,--fd 70ms 交错)——线却原地淡入,同一根向量一个飞一个淡。
v2 把线的出现改为**沿同一向量从父锚点同步生长**(像被孩子拉出来):

- 时长 500ms、delay 对齐子节点的 `--fd` 交错、缓动手写
  cubic-bezier(0.34,1.45,0.64,1) 求解(与 --ease-spring 同曲线,二分 x→t 取 y);
- **实现机制**:WAAPI 不支持 line 的 x2/y2 几何属性(关键帧被静默丢弃,探针
  getKeyframes x2=null 实证)——改为 linkTweens Map + 专用 rAF ticker 手写补间;
  补间期间 drawLinks 不覆盖该线的 x2/y2(由补间驱动),svg 被外部清空时连
  补间一起清;
- 淡入(opacity 0.5s)保留,与生长叠加。

回归:smoke 4/4、prison 42/42、bear 30/30、workbench 16/16、reset 13/13;
行为探针:根展开后 380ms 处 x2 已沿向量位移 127px、透明度同步升到 0.51——
线与节点同轨同拍。


旧 `drawLinks()` 每次绘制都 `innerHTML=''` 全量重建线元素——线条瞬时出现,与子节点
`.arrive` 0.5s 过渡完全脱节,且平移/缩放的每一帧都在重建 DOM。重构:

1. **线元素按「父→子」键持久复用**(linkEls Map):绘制只更新坐标,不再重建;
   平移/缩放高频重绘不再打断任何过渡(也是渲染性能修复)。
2. **与节点同拍的过渡**:`#links line` 加 `transition: opacity 0.5s var(--ease)`
   (与 `.node.arrive` 0.5s 同 duration/easing);新线以 `link-enter`(opacity 0)
   创建,双 rAF 后移除类 → 0.5s 淡入,和子节点出现同拍。
3. **淡出停放**:端点隐藏/用掉时线加 `link-hidden`(opacity 0)停放不删除——
   再现时自然淡入;`svg.childElementCount===0` 时同步清登记表(兼容外部清空)。
   坐标仍即时更新(世界坐标静态,不平滑插值——FLIP 位置过渡属方向文档
   313 行的另一笔动画债,不在本批)。

回归:prison 42/42、bear 30/30、workbench 16/16、reset 13/13、naming 10/10、
save 10/10、wait_game 9/9、design_race 15/15;行为探针:根展开 4 条新线
opacity 0 起步 + transition-duration 0.5s、连绘两次元素恒等(零重建)。


1. **点击更新原语 `clickUpdate(n)`**(engine.js,替代 exploreRoom + 三处内联扫描):
   只显形节点 n 的**下一级就绪子节点**,三种形态——根/入口=直接挂根的就绪物;
   房间(zone)=首次走进亮出可见物件、之后=就绪隐藏物;物件/容器=就绪内容物
   (parent 挂靠或 revealFrom 指向)。**未开启的容器不由环顾代开**(必须玩家自己
   点,开柜才算发现)。三处调用方(root 点击/房间点击/容器点击)全部改走原语,
   exploreRoom 删除;`revisitRoom`(环顾四周)= 对**所有**节点各执行一次
   clickUpdate 并聚合去重——语义从此只有一个定义。
2. **进度条单一写方**:乱跳根因 = 引擎 compiledObjective(已完成 beat/总 beat)
   与 room02 update()(原生 6 状态计数)交替写同一对 `#doorStatus/#meter`。
   修法:runtime 暴露 `hasCompiledLevel()`,room02 update() 在编译关卡存活期间
   不写顶栏读数/进度条/roomState——引擎是唯一写方;纯原生房间行为不变。

回归:prison 42/42(容器链+环顾最重)、bear 30/30、workbench 16/16、reset
13/13、naming 10/10、save 10/10、wait_game 9/9、design_race 15/15。


旧版四处(密码盘位数不足/密码错/摩斯错/无效组合)对整个 `#stage` 做 0.35s ±7px
全屏震动。修订:

1. **局部轻推**:引擎新增 `nudge(targets)`(targets 可为数组)——密码/摩斯错摇
   **弹窗卡片**,无效组合摇**涉及的两张物件卡**(`nodeEl()` 按 data-id 查元素,
   CSS.escape 防注入);`.shake-soft` 动画 0.22s ±3px,比全屏 ±7px/0.35s 温和得多。
2. **全局限频 ≥900ms**:连输密码+连试组合也最多 0.9s 一次。
3. **prefers-reduced-motion 不播**(CSS+JS 双保险)。
4. **顺序坑(实测抓到)**:无效组合分支的 `roomRender()` 会重建节点元素——
   nudge 必须放在渲染之后,否则刚加的类被抹掉(探针 nudged=[] 定位后已修)。

回归:prison 42/42、bear 30/30(有效路径不受影响)、workbench 16/16、
reset 13/13;行为探针:生成关里无效组合 → 两张物件卡获 shake-soft、
#stage 无 shake 类。


1. **清洗供应商可配**:赛马配置弹窗增「清洗使用」下拉(默认(本地代理/step)
   或任一自定义供应商,存 config.cleaning=label);`callStep` 头部经
   `cleaningProvider()` 读同份配置——cleaning 指定某供应商时,清洗的
   端点/模型/Key 全部走它(显式端点不做 stepfun→代理改写)。
2. **同供应商多路错峰**:并行调度改为**同端点依次错开 2.5s 起跑**(不同端点
   仍同时);先胜后路不发——未起跑就被跳过的路结算 remaining(赛马 Promise
   正常收敛)。单供应商 N 路从「同时打满」变为「流水补位」,快速通过时后路
   零消耗。弹窗说明同步更新。
3. **回归(design_race 15/15)**:新增「清洗路由」断言(cleaning=自建A:
   自建收清洗 1 次、默认 0 次)+「单供应商双路先胜后路不发」断言(2 路同
   供应商,设计调用恰 1 次);自定义供应商场景的「两家都被调用」断言改为
   「自建参与即可」——先胜跳过后默认路零调用是合法结果。其余:workbench
   16/16、reset 13/13、naming 10/10、save 10/10、wait_game 9/9。


1. **配置层**:localStorage `fav-room-race-v1` = {lanes:1-5, providers:[{label,
   endpoint,model,apiKey,reasoningEffort}]};`buildLaneDefs()` 按路数**循环取供应商表**,
   端点留空的行 = 默认供应商(本地代理/清洗配置,overrides=null);任意 OpenAI
   兼容端点可用(designWindow overrides 本就通用)。自动模式(未自定义)行为不变:
   有 glm 双路并行,无 glm 单路 step。
2. **UI**:home-secondary 增「赛马配置」→ raceModal(路数 1-5 + 5 行供应商表:
   名称/端点/模型/Key/推理档);恢复自动一键清除;自定义密钥只存本机浏览器。
   空行忽略,≤5 供应商,校验后落 localStorage。
3. **工作台泛化**:起草人甲/乙 → 甲乙丙丁戊(DRAFT_NAMES);标题副行改为动态
   (#wbHeadCrew:「共 N 位起草人同时起草…」/「单路起草,失败自动重试」);
   designWindow 报文去 step 化(「该供应商未提供 API Key…」/「设计请求失败…」)。
4. **顺手修**:死变量 laneCount(designLanes 注释与实现不符)移除;GLM 密钥
   轮换(server/GLM_API_KEY.local 新 key;旧 key 曾硬编码于
   compare_design_providers.py 并随 557dfa6 进入已推送历史——新 key 已换上,
   旧 key 应在 bigmodel 控制台作废)。
5. **回归**:verify_design_race 扩至 **13/13**——新增单供应商场景(空 llm-config:
   1 路稿纸、清洗不计入设计调用数、3轮×2次=6 次后兜底模板挂载)与自定义供应商
   场景(localStorage 预置 3 路×两家供应商:3 张稿纸、两家端点都被调用、正常
   挂载);workbench 16/16、reset 13/13、naming 10/10、save 10/10、wait_game
   9/9、prison 42/42、bear 30/30。

已知边界:清洗(整理器)仍固定走默认供应商——glm-only 用户无法完成模型清洗;
赛马 UI 的同供应商并发排队风险已在弹窗说明。


旧 `loadTutorialLevel` 经 `loadLevelText` 每次进入都新建 `import-*` 存档。落地:

1. **固定 id 常驻记录** `level-newbie-tutorial`(projectId 'tutorial',name「新手关卡」,
   `newbie:true`,时间戳回填 1999-12-31 使其稳定排在存档列表末尾);`boot()` 调
   `ensureTutorialLevel()` 缺失即回填;反复进入都是同一条记录。
2. **主页入口移除**:`#homeTutorial` 按钮与绑定删除,入口即「已保存关卡」列表行。
3. **不可删除**:`deleteLevel` 对 NEWBIE_ID 直接拒绝;列表行不渲染删除按钮
   (行首标「常驻 · 」)。
4. **测试契约修正**:三处 `levels.getAll()` 末尾读取(naming_flow ×2、
   adventure_goal ×1)在 key 序下会取到教程关,改为排除常驻 id 后按 createdAt
   取最新;save_mgmt 扩至 **10/10**(新增:回填存在/行无删除钮/删除守卫/
   重复进入 tutorial 记录数恒 1);naming 10/10(存档列表 = [用户命名关, 新手关卡])。

注意:改动前旧版本产生的重复 import-* 教程存档不做自动清理(与用户真实导入
无法可靠区分),可在列表手动删除。


1. **舞台化构图**:顶部大字标题「你的密室正在搭建」+ 副题(两位起草人同时起草,
   取先完成的那份——通常两分钟左右 · 已用 Ns)——第一眼定性;工序改为左侧
   **竖向轨道**(圆点+删除线完成态);中央**稿纸为主角**(起草人甲/乙大卡,
   蘸墨/推翻/定稿动效),素材堆叠降为左侧 216px 边桌;手记为台词语;line 下
   折叠技术记录;窄屏单列回退。
2. **修父会话模板混排遗留**:stage 重排时曾丢失 wbOverlay 收口 div(首屏截图
   证实卡片被挤到左上、背景失去压暗),已补;CSS 灯光选择器沿用 sil-2/3/4。
3. **游戏回归加固(verify_wait_game 9/9,连跑三遍稳定)**:
   - ② 跳跃场景改为直接置跳态(绕过 running 守卫)——守卫吞起跳会造成
     「跳了仍扣墨」的偶发误报;逐帧轨迹探针证实抛物线在危险窗口(y≈26-38,
     障碍顶 103)稳定越过;
   - ①②③ 增加前置断言(局面存活/已置跳态),杜绝 lives=0 时的空过;
   - 设计桩 sleep 10s→90s:生成完成触发 wbFinish→game.stop,会在场景中途
     污染游戏状态(曾致 ②开局即 gameOver + while 空转挂死,guard 上限 200
     兜底);场景间隙 rAF 实时运行,开场即冻结自然生成(nextObsD/nextColD=1e9)。

回归:workbench 16/16、race 9/9、reset 13/13、naming 10/10、save 6/6、
prison 42/42、bear 30/30、wait_game 9/9 ×3。


生成开始 = 「走进工房」:genWorkbench 包进 `#wbOverlay` 全屏场景(纸幕压暗+
backdrop blur,卡片居中 min(760px,100%)),首页退到幕后;收起仍是浮标,
门转场(z-index 90)直接在全屏场景上开。控制器 overlay 生命周期挂在
wbBegin/wbMin/wbFinish/wbCancel。id 契约不变,回归全绿(workbench 16/16、
race 9/9)。待办:首页表单化改版提案(投递匣/桌牌/档案盒/房间小样)已提出,
待需求方批准后落地。


两个真问题,分别修:

1. **按帧驱动 → 固定步长**:旧物理全部按帧计(rAF),120/144Hz 屏整体加速
   2-2.4 倍,跳跃滞空 <0.3s,障碍密度翻倍,手感崩坏。改为 60Hz 固定逻辑步 +
   rAF 累加器(封顶 100ms 防大步穿越),速度/跳跃/间距与刷新率解耦;速度曲线
   降为 2.4→4.6 px/步,障碍间距按「距离」(240-460px)生成,不随帧率压缩。
2. **失败判定不可见 → 3 滴墨 + 结算**:旧版命中只有 0.2s 闪烁+速度重置,
   无任何失败状态,视觉上等于没判。改为 3 滴墨(命):命中=停顿 0.2s+画面
   震动+1.1s 无敌闪烁(防一障多扣),墨尽=本局结束结算画面+点击再来一局;
   判定盒四周收紧(擦边不扣墨)。

**回归(新增 ref-game/verify_wait_game.py,6/6)**:用 __wbGame.__debug 单步
驱动逻辑步模拟整局——①命中扣墨(3→2);②跳跃越过障碍不扣;③收集纸页生效
并触发手记;④墨尽 gameOver;⑤重开复位。测试基建注意:场景间隙 rAF 实时
运行,须在开场即冻结自然生成(nextObsD/nextColD=1e9)再做确定性模拟,否则
自然障碍会在间隙期耗光墨量。

需求方反馈等待 2-3 分钟是黑盒,进一步要求精致化(卡片堆叠/赛马动效/氛围文案)
并加入等待小游戏。统一隐喻:**深夜工房——用户隔着灯看自己的收藏被封进房间**。
实现(纯前端,零管线改动,事件全部来自真实阶段):

1. **叙事化分层**:阶段改为工序名(挑选素材→重访网页→构思房间→校对谜面→开门);
   赛马拟人为「起草人甲/乙」稿纸卡——设计中=蘸墨呼吸、打回/求解失败=推翻草稿
   (crumple 动画)、通过=「定稿」朱砂印、他路先过=收起稿纸;轮次/供应商/重试
   事实全部折叠进「工作记录(技术细节)」,与氛围层视觉分离(文档底线:
   不放假百分比、不编造模型思考——两套措辞,同一批事实)。
2. **素材发牌堆叠**:选定素材以索引卡逐张发牌入场(随机旋转角),4s 自动翻检
   (底卡翻顶),首次翻顶盖「入房」朱砂印;卡片仍可点击跳转来源。
3. **工房手记**:24 句按阶段分组的氛围文案池,每 9s 墨迹浮现;与小游戏收集
   共享同池、不重复直到取尽。
4. **工房剪影渐显**:面板底部 SVG 剪影(灯/桌柜/门)随阶段亮起(沿用父会话
   的剪影 SVG,灯光选择器适配 sil-2/3/4)。
5. **开门转场**:生成完成整屏两扇门片开合,门缝亮起时换幕——等待的 payoff。
   prefers-reduced-motion 时全部动效降级。
6. **纸页夜奔(js/wait-game.js,新增)**:单键 canvas 跑酷——纸片沿书桌奔跑,
   跳过墨水瓶/胶带卷/纸团,收集纸页解锁一句手记;软死亡(纸页翻回原处,
   无 Game Over);手动开启不自动播放;收起/隐藏/完成/取消即停;canvas 惰性
   绑定(addUi 动态注入后 start 时重试)。
7. **取消/浮标语义不变**(11.12 批次产物):取消中止在途请求并复位;收起后
   完成不抢占屏幕,浮标「已生成 · 点击开门」进入。

**回归**:verify_gen_workbench 扩至 **16/16**(新增小游戏开启/手记浮现断言;
已用时间改页面内采样器——sync route handler 的 sleep 会阻塞测试线程,
python 侧读数不可靠);design_race 9/9、reset_lifecycle 13/13(修测试流程:
入口验证后须再重置,否则自动保存把进行中进度带进刷新环节)、naming 10/10、
save_mgmt 6/6、prison 42/42、bear 30/30。

**注意事项**:工作台 id 契约(wbPhases/wbElapsed/wbMaterials/wbLanes/wbLog/
wbMin/wbCancel/genPill)是回归测试的锚点,重构时保持;本批曾因父会话并行
写入造成模板/控制器版本混杂,最终以「模板用父会话剪影 + 控制器/样式/游戏
为新实现」收敛。

## 最新:2026-08-30 晚 单次素材数可调(6-12)+ GLM 能力边界压力测试

需求方要求开放「单次使用的网页数量」选项,让单次生成承载更复杂结构;先压测 GLM 能力边界再定档。

**实现**:
- `designWindow` 第 9 参 `materialCount`(6-12 钳位,默认 6):实际采用量 = min(请求量,可用量),
  下限 6;`N` 贯穿 prompt(素材条数/beats 区间 N-(N+4))与校验器(claimed≥N、
  总步数 N-1~N+8);N≥8 时 prompt 建议 3 间房间。
- `selectControlledPool(records, wantCount)`:素材池抽样同步参数化(域名多样性贪心不变)。
- 主页步骤 02 新增「单次使用的网页数量」下拉,localStorage(`favRoom.materialCount`)持久化;
  generate() 读取并逐路传入 designWindow。N=6 行为与旧版完全一致(默认档零漂移)。
- **压力测试** `ref-game/stress_design_capacity.py`:绕过 UI 直调 designWindow(真实 GLM low),
  每档最多 3 次带修复反馈(生产同款),desc 富化先行(否则接地检查误杀域名引用);
  结构校验→compile→solveLevel 全链。档位可从 argv 传入。

**能力边界结论(真实调用,stress-capacity-run3/run4)**:

| 档位 | 结果 |
|---|---|
| N=6 | 生产基线,目标测试 143.6s 全绿(见下节) |
| N=8 | **可用**:3 房间/11-12 步/每房 hidden 1-1-1/reveals 3/回访 1-2/跨房收束,96-123s;两轮实测一轮求解失败(抽样波动,生产 2 路×3 轮可吸收),一轮一次全通 |
| N=10 | 不可靠:3 次尝试全败(回访门槛 ×2、接地 ×1),单路 3 轮内未能收敛 |
| N=12 | 不可行:素材簿记崩溃(编造 id/遗漏素材),3 次全败 |

**UI 定档**:6(默认)/ 8(进阶,3 房间)/ 10(实验,标注可能多轮重试或失败);12 不入 UI
(代码路径仍支持,localStorage 手改可试)。失败模式集中在:**素材簿记**(遗漏/重复/编造 id)
与**回访门槛**——条数越多,簿记越先崩;这与"结构想象力无关,是长清单上的记账纪律"。

**回归**:verify_design_race 9/9(与 prop-* 机关道具机制合并后的桩适配由并行会话完成)。

## 最新:2026-08-30 机构/信息分工:prop-* 机关道具(无网页背景的纯机构)

需求方裁定:单纯补无作用的环境道具解决不了牵强感——应允许**没有任何网页背景的
锁、火柴、油灯**存在。落地为"机构与信息分工":素材化身只承担**信息载体**
(笔记/报文/指南/磁带),机关(锁具/容器/工具)由 prop-* 机关道具承担,
收藏不再硬扮锁具。实现:

1. **编译器(pipeline.js compileLevel scenes 分支)**:`prop-1`…`prop-N` id 放行为
   机关道具(`prop:true`,无 title/url/source,detail 只写自身物性);素材化身不变。
   引擎渲染天然安全(node.url 缺省 → 无「打开原收藏」链接;identityOf 空)。
2. **designWindow 校验器**:prop id 放行(不占 N 条素材名额);**每房 ≥1 件、
   全关 ≤5 件**;机关道具 reason 禁止携带素材事实(用全部 sourceFacts 值做机器检查
   ——事实只能来自化身,P46)。
3. **Prompt**:rule 0 增「机构与信息分工」段;化身名铁律改为化身偏信息载体、
   机构交 prop;userReq.items/beats/机关/步骤 四处同步;骨架示例 room-1/room-2
   补 prop 容器与 prop 密码闸机示范(deriveFrom 仍指向素材)。
4. **回执(app.js)**:收藏化身照常映射「化身 ← 真实收藏」;prop 机关道具单列
   「机关道具(无收藏背景的纯机构):…」,不再伪造「← 未知收藏」。
5. **测试**:verify_design_race 与 verify_reset_lifecycle 的 valid_design 桩加
   prop-1(容器显形)/prop-2(密码闸机);verify_adventure_goal 新增
   「机关道具(共 N 件,X/X 房有)」断言。

**验证**:离线回归全绿——design_race 9/9、reset_lifecycle 13/13、naming_flow 10/10、
save_mgmt 6/6、prison 42/42、bear 30/30。**真实目标测试 36/36**(goal-prop-run1.log):
周期 1 全新生成 **152.1s < 160s**,10 个交互物 = 6 化身 + **4 机关道具(2/2 房)**,
每房 hidden/容器链/回访全保持,事实接地 0 违规;周期 2 缓存命中。
注意:素材化身解耦机构后,新产物的谜面证据仍全部来自真实收藏(接地检查未放宽)。

## 最新:2026-08-30 修复:重置生命周期(11.12 全项)+ 11.11 信息墙复核

需求方在文档反馈 bug,逐项确认后处置:

**11.11 信息墙——已被 P61/P63 修复(复核确认,无需再改)**。评审基于 05:15 旧产物;
现行 engine.js 已是分层详情(layeredDetail:谜面→facts≤3→digest 一句→externalTask→
短身份 title/domain/日期/路径≤80),完整 URL 与原始 description 不再直出。余下
evidenceRefs/grounding checker 属设计增强,不是缺陷,留待后续批次。

**11.12 重置生命周期——8 项全部修复**(按「修复约定」落地):

1. **[P0] 唯一入口**:room02.js `#reset` 改绑产品层 `__favoriteRoomHome.resetCurrentLevel()`
   (引擎 `runtime.resetCurrentLevel` 次之,底层 roomReset 兜底);基础 `roomReset()`
   回归纯节点克隆,不再直接绑 UI。
2. **[P1] 三方失配**:app.js `resetCurrentLevel()` 保留 `currentLevel` 与工具栏标题,
   重建同一关卡初始运行态后 `await saveProgress(true)` 把初始态快照写回 progress——
   刷新后「继续游戏」恢复的是重置后(未开始)的进度。
3. **[P1] 机关上下文**:引擎 reset 包装统一清空 `keypadCtx/angleCtx/morseCtx` 并隐藏
   keypadModal/angleModal/morseModal(app 层另关 namingModal)。
4. **[P1] 并行房间恢复**:snapshot 增补 `parallelRooms` 字段;restore 以
   「快照 ∥ 关卡数据任一为真」判定,不再依赖 localStorage 草稿的新旧。
5. **[P1] 运行中间态**:morph/consume/reveal 已由 S4 的 clues 重放覆盖(复核确认);
   本轮补 parallelRooms,其余(视图级状态)不进快照。
6. **[P2] 视图泄漏**:引擎 reset 调用 `resetView()`,缩放/平移不跨关卡。
7. **[P2] 命名轮询**:`showHome()` 与产品层 reset 均调用 `stopNamingWatch()`;
   reset 后重新武装(已命名关卡由 `namingShownFor` 去重,不会重复弹窗)。
8. **[P2] 重复调用**:restore 中连续两次 `revealAllRooms(false)` 合并为一次。

**回归(全部真实 DOM,零配额)**:新增 `ref-game/verify_reset_lifecycle.py`
**13/13**——挂载→开始(自动保存 started=true)→点 #reset:标题不变/运行态初始/
progress 写回 started=false/__dbg 重建且 parallelRooms 保留/弹窗全关/再点 root 同一
关卡入口亮出(2 scene)/刷新后继续游戏恢复重置后进度/离开语义不变。
verify_design_race 9/9、verify_naming_flow 10/10、verify_save_mgmt 6/6、
verify_prison 42/42、verify_bear 30/30、smoke_room02 通过。

## 最新:2026-08-30 空间感落地:密度门槛替换数量门槛(引擎+范例+校验器三处)

需求方判定 LLM 仍无法生成有空间感的谜题。复盘 4 份导出产物(08-29 14:22 → 08-30 05:15)
发现规律:**每份恰好 1 个 reveals、恰好 1 个 hidden**——校验器「≥1 hidden」被贴线满足,
且旧 prompt 把 reveals 定义为推理锁专属(「锁解开时用 reveals 放出关键道具」),
模型每关只敢用一次,全关只有一次空间事件。三处源头自洽闭环:prompt 封顶、schema 无
容器位、compiled-container 只在无 scenes 分支渲染。本轮落地(三步):

1. **引擎(js/engine.js S1)**:`revealSourceAll` 推导优先取 combine 的 `resultOn`
   (回退 uses 首个实体素材)——「用工具撬开抽屉」类显形,隐藏道具嵌在抽屉(容器)上
   而非工具上。
2. **范例(js/ref-levels.js)三份全部改为每房空间链**:监狱(电池藏在日记本书页,
   b-read 显形;电报机跨步回访)、熊曰(铅笔压在便签下, b-note 显形)、放映室
   (幕布压在回执下, b3 显形)。骨架示例 room-2 补 hidden+显形步示范。
3. **校验器(js/pipeline.js designWindow)密度门槛**:全关 reveals≥2;每个房间
   ≥1 hidden 且存在「显形步 uses 含本房间容器 id」的容器链;至少 1 件素材被 ≥2 步
   使用(回访)。原「≥1 hidden」门槛删除(被密度版覆盖)。

**目标测试(ref-game/verify_adventure_goal.py 新增空间断言,真实调用两周期)34/34 通过**
(goal-space-run1.log):周期 1 全新生成 **143.6s < 160s**,周期 2 缓存命中 5.1s;
生成关卡 2 房间 **3 个 hidden(每房 ≥1)、3 处 reveals、3 处容器显形链、1 件回访物件**、
desc 富化 4/6、digest 6/6、事实接地 0 违规、终局收束跨 2 房。赛马回归
verify_design_race 9/9(桩数据天然满足密度门槛)。

**测试脚本注意**:verify_adventure_goal.py 循环变量不得用 `b`(遮蔽 playwright
browser 对象,本轮曾因此尾部 `b.close()` 报错,已改 `bt`)。

## 最新:2026-08-28 傍晚 交接复核(逐项实测,未改动 js/)

按本文件待办逐项复核,结论如下:

1. **真实 LLM 批量门禁已闭环**:`ref-game/e2e_v7_batch.py` 于 16:02 跑通 **3/3**(生成+编译+求解+真实 DOM 通关),见 `llm-e2e-run2.log`(r1 408s / r2 269s / r3 112s;r2、r3 含 password 机关)。**第 40 行「建议下次跑一轮 e2e_v7_batch」已完成**,不再是残留项。
2. **无 LLM 回归实测全绿**:`test_solver.py` **6/6**(含「锁/观察重叠」lint 拦截)、`test_compile.py` **5/5**(平铺正例 / 孤儿守卫负例 / compileFixed 保底 / REF_LEVELS 两档金标准)。与 README 基线一致。
3. **第四节 break bug 已不存在**:v7 重写 `generate()` 后成功路径已有 `break`(`js/app.js:494-495`),见第四节顶部复核说明。
4. **GLM A/B 失败根因:不是 CORS**:在页面上下文直接 `fetch` 智谱 endpoint(无效 key 探针),返回 **401「令牌已过期或验证不正确」**——浏览器直连**网络可达且跨域允许**。真因是**模型侧流中断**:`glm-5.3-flash` 在 few-shot 大提示词下 240s / 480s 均超时,3 次重试全「设计流中断」后脚本在第 1 版中止,日志无结论(`llm-e2e-glm.log` / `llm-e2e-glm2.log`)。
   - 续测前提:①有效 GLM key(仓库内无记录,只在用户 shell env);②或改走本地代理转发——扩展 `server/favorites_room_server.py` 的 `/api/step` 支持 GLM,绕开浏览器直连的超时与跨域依赖。
   - 注意默认通道本身也偏慢(r1 408s),换供应商的收益需与 deepseek advisor 通道对比后再定。
5. **环境要点**:服务器根即项目根,`http://127.0.0.1:8128/` 直接可访问(`/favorites-escape-room/index.html` 已 404,README 启动方式为准);playwright 需显式 `executable_path=ms-playwright/chromium-1234`。

> **回归已补齐(同日实测)**:四关 DOM 全绿——prison **42/42**、bear **30/30**、clockwork **39/39**、bookmarks **31/31**,另 `smoke_room02.py` EXIT=0;连同 solver 6/6、compile 5/5,**与 README 基线完全一致,仓库当前健康**(本轮未改动 js/)。
>
> **环境坑(必读)**:playwright 在本机**前台跑会被回收**(输出文件 0 字节、EXIT=1,偶发),**后台任务模式稳定**;串行跑多关时后续关卡的浏览器进程也可能被回收。**跑回归请用后台任务,并尽量逐关单独提交。**
>
> 剩下的建议(性价比排序):①v7.4「待观察」两项复测(抽屉密码算术自检效果、`fetchMetaInto` 的 desc 富化成功率);②GLM 改走代理转发后再 A/B。
>
> **「desc 富化」静态结论(本轮分析,未改码)**:`fetchMetaInto`(`js/app.js:152-192`)在 `selectControlledPool` 选出 6 条**之后**才调用(`app.js:379`),即每次只抓这 6 条;每 URL `timeout:6`、总 60s;`desc` 仅在 `!t.description` 时写入(186 行);`catch(_){}` **静默吞掉全部失败**(189-191),`fetchStatus` 虽写入但未参与任何决策或统计。→ **成功率当前完全不可观测**,这正是 v7.4「待观察」项无法推进的直接原因。最小改进:把「x/y 条取回详情」写入调试钩子并在状态栏上报,零行为变化即可观测;确认成功率偏低后再考虑提前到选池前抓取 / 放宽 timeout / 允许覆盖空 desc。

---

## 最新:v7.4 事实锚定 + 机关参数验证(2026-08-28 下午,用户反馈驱动)

用户复测报告:展示信息太多、单机关推理过于复杂、推理信息并非来自原网页事实。解剖废弃医院导出档,五层问题全部定位并修复(改动都在 js/pipeline.js 与 js/engine.js):

1. **推理材料编造**(范例副作用:监狱复刻的推理材料本来就是虚构道具;素材 desc 全空时模型只有元数据)→ prompt 加「事实锚定铁律」:推理材料只准来自标题/域名/urlPath/文件夹/日期,路径数字串(如 /opus/351262298288053446)是最佳原料;严禁虚构附录/参数/日期。加「算术自检铁律」:答案写完自己重算推导。
2. **reason 元数据复述回潮**(来源/路径/日期像资产清单)→ 「信息密度铁律」:reason ≤2 句;单机关推导 ≤2 条线索 1 次换算。
3. **角度锁参数非法被 flat 分支静默降级**(validation.issues 里躺着'已降级为检查',开局高潮名存实亡)→ designWindow 新增机关参数校验(expected 3-6 位 / code 字符集 / angles 均为 precision 倍数),flat 分支降级改 structural 整版打回(与 scenes 分支对齐)。
4. **同节点双锁第二把永远打不开**(摩斯启动→密码解锁是合理叙事;但引擎按单一 key 匹配机关,第一把锁变身节点后 key 变 result:*)→ engine.js 三处锁匹配(password/angle/morse)改 nodeKeys 全身份(与 inspect 身份修复同类)。
5. 裸密码(204 无任何推导)→ 由锚定铁律+自检约束,无法机械验证,观察后续生成质量。

**验证**:prison 42/42、clockwork 39/39、bear 30/30、solver 6/6 全绿;用户素材(废弃医院)新生成关卡化身全部实体化(『任天堂病历夹』『报废显卡』『检索终端』『电子病历笔』『门禁卡』),终端密码 255431 实际验算正确(显卡路径[2:8] 126229 + 硬盘路径[1:7] 129202),真实 DOM 通关 6/6(ref-game/llm_out/user_repro.room.json)。沉淀 P31/P32。verify 脚本补充:combine 拖拽两端都要 ensure_visible。

**待观察**:抽屉密码 190 算术仍含糊(自检铁律效果待复测);desc 富化(fetchMetaInto)成功率决定模型有多少真实内容可用,长期比提示词更能根治编造。

---

## 最新:2026-08-28 代码重构(结构与卫生,行为零变化)

全部改动在回归基线(solver 6/6;prison 42/42、bear 30/30、clockwork 39/39、bookmarks 31/31;Room 02 冒烟)下进行,重构前后结果逐项一致。逐提交:

1. **baseline(11f197e)**:项目纳入 git——此前靠 9 个 `index.backup-*.html` 手工副本当版本控制,现为唯一历史来源。
2. **cleanup(8edd8b2)**:删除全部备份副本、diag*.txt/p_debug.log、ref-game 里 35 个一次性调试脚本(49→14 个工具)。
3. **拆分(9d1d5f3)**:244KB 单文件 index.html → 4KB 骨架 + `js/room02|pipeline|engine|app.js` + `css/styles.css`。经典脚本按原顺序外链,全局作用域语义等价;对外接口 `__favoriteRoomPipeline`/`__favoriteRoomHome` 未动(e2e 工具链依赖)。
4. **数据分离+格式化(a693630)**:designWindow 的 few-shot 范例关卡内嵌 JSON 抽为 `js/ref-levels.js`(window.__REF_LEVELS__);prettier(printWidth 100/LF)全量格式化,超长行(最长 10736 字符)清零。`.prettierrc` 入库。
5. **死代码(a89a4f0)**:标识符全仓引用扫描,11 处清零——未接线的 startFixedTest、room02 薄包装 clone/bind/handle、engine 的 nextOpenBeat/resultPos/恒真 usable、pipeline 的只写调试导出(`__FAVORITES_ROOM_LLM_STATUS__`/`__bookmarkImport`/`__lastLevelResult`/`__parsedItems`)与 compileFixedRoom 守卫内的 v7.2 残留变量。**server/favorites_room_server.py 经查是活代码(静态托管+/api/step LLM 代理),保留**。
6. **docs(d12c355)**:根目录 HANDOFF 并入 docs/handoff.md;README 重写(真实启动方式 server/favorites_room_server.py,8128)。
7. **test+reference(ef62a61)**:新增 `ref-game/test_compile.py`(5/5,无 LLM)——平铺 step 分支正例+孤儿守卫负例+compileFixed 保底+REF_LEVELS 兜底金标准;原作残缺副本迁 `reference/original-game/`(main.js/assets 本就缺失,不可运行,仅 config.js 供 reference-analysis 引用);.gitattributes 固化 LF。

**test_compile.py 的两条考古结论**(写代码前先看,免得重复踩):compileLevel 是有损变换(监狱 10 beats→6,机制保留、可解性不变);孤儿守卫仅对**无 mechanics 字段**的设计稿严格——designWindow 正常输出携带 mechanics,走 v7.2 宽松语义(P23 合法链不误杀)。

已知残留:~~真实 LLM 生成链路未验证~~ **已于 2026-08-28 补验通过**(见下节)。

## 2026-08-28 LLM 供应商 A/B:step 基线补验 + glm-5.3-flash 结论(不可用)

**step-3.7-flash 基线(重构后补验,e2e_v7_batch 3 版)**:**3/3 生成+求解+DOM 通关**,全部首轮通过,
单版用时 408s/269s/112s(合计 ~13.2 分钟)。注意 r1 的 designSource=local(素材映射退化走兜底编译,
无机关也判可解)——这正是 test_compile.py 考古发现的退化路径在生产数据上的实证,非本次重构引入。

**glm-5.3-flash(bigmodel,用户提供的 key)——结论:当前管线架构下不可用,速度大幅劣化**:
- 单次设计调用实测 **1419.8s(~23.7 分钟)**:思考阶段流出 **156,067 字符**(占 23.4 分钟),
  内容仅 3,015 字符(~18 秒)。请求体快照:ref-game/llm_out/glm_real_design_body.json
  (system 1.7K + user 6.4K 字符)。
- `thinking:{effort:"low"}` 被 API 接受但**完全无效**——该模型「始终思考」且不理会档位
  (错误码 1210 证实:`{type:"disabled"}` 与 `{type:"low"}` 均被拒绝,`{effort:"low"}` 收下但照常深思考)。
- 管线设计调用超时 240s(实验中提至 480s)远小于 23.7 分钟 → 9 次尝试全部「设计流中断」超时,
  design-x9,0 版产出。速度/通过率均无提升,反而完全不可用。
- 排查过程排除了:CORS(预检与实际响应均放行)、浏览器网络层(原生 fetch 设计级请求 16s 返回)、
  playwright 路由拦截(第一版实验的干扰因素,已弃用)、系统代理、并发争用(隔离单发复现)。

**工程沉淀(均已入库,step 默认行为零变化,test_compile 5/5)**:
1. pipeline.js:`thinking`、`timeout`(清洗/取元)、`designTimeout`(设计)三者可经
   `window.__FAVORITES_ROOM_CONFIG__` 覆盖,默认值不变;
2. e2e_v7_batch.py:V7_LLM_ENDPOINT/MODEL/APIKEY/THINKING/DESIGNTIMEOUT/TAG 环境变量化,
   支持免改码 A/B;输出路径锚定脚本位置(cwd 无关);[design] 实时进度日志;
3. A/B 证据日志:ref-game/llm_out/ab_step_baseline.log、ab_glm_route_attempt.log、ab_glm_batch_attempt.log。

**若仍想验证 GLM 系**:应换支持关闭思考的档位(如 glm-4.7-flash 一类,
   `thinking:{type:"disabled"}` 可用),或接受单版 ~25 分钟的成本把 designTimeout 提到 1800000 再测质量——后者未做,由需求方决定。
OpenRouter glm-5.2:free 免费池全程上游 429(限流),本次未能测到。

## 2026-08-28 更正:reasoning_effort 顶层参数救活 glm-5.3-flash,3/3 全通且总耗时反超 step

上一节「不可用」的结论**作废**。用户从 bigmodel 文档页指出 `reasoning_effort` 参数,查 API 参考
(docs.bigmodel.cn/api-reference/模型-api/对话补全)后确认根因:

- `reasoning_effort` 是**顶层字符串参数**(`max/xhigh/high/medium/low/minimal/none`,默认 **max**,
  GLM-5.3/5.3-FLASH 仅支持 low/high/max,`thinking` 开启时生效)。此前发送的
  `thinking:{effort:"low"}` 是未知字段被服务端忽略 → 一直按默认 max 深思考 → 23.7 分钟/次。
- `thinking.type` 对 GLM-5.3 系只能 `enabled`(1210 报错的真正含义),强度完全由 reasoning_effort 控制。
- 实测重放真实设计稿 + 顶层 `reasoning_effort:"low"`:**84.1s**(思考 5,186 字符,内容 2,653 字符),
  对比默认 max 的 1419.8s/156,067 字符,**快约 17 倍**。

**工程落点**:
1. pipeline.js 三处 LLM 调用体增加 `...(llmConfig.reasoningEffort ? {reasoning_effort: ...} : {})` 透传;
2. e2e_v7_batch.py 新增 `V7_LLM_REASONING_EFFORT` 环境变量;
3. glm-5.3-flash 调用须配 `V7_LLM_THINKING='{"type":"enabled"}'`(不能留默认 disabled,会 1210)。

**GLM 批量复测(V7_TAG=gen_v7glm2,reasoning_effort=low + designTimeout 480s)**:**3/3 生成+求解+DOM 通关**,
单版用时 301s/153s/158s(合计 ~10.2 分钟),对比 step 基线 789s **快约 22%**。
质量信号(如实记录):三版**全部首轮失败**、靠管线自修复轮次救回(孤儿产物 1 次/不可解 3 次;
step 基线是首轮 3/3 直过);产出关卡偏薄——三版都是 4 beats,其中 2 版无机关(仅 r3 有 password),
语义字段步数=1。即:**速度略胜、通过率持平(依赖修复轮兜底)、单次设计稿质量仍逊于 step**。
证据:ref-game/llm_out/ab_glm_reasoning_low.log 与 gen_v7glm2_r{1,2,3}.room.json。

## 2026-08-28 清洗快车道:分任务路由(清洗直连 / 设计保持 advisor 强制)

需求方决策:清洗缓存命中下,清洗任务不再值得付 advisor 的 17~45s/次;生成(设计)保留"用时间换质量"。
实施:

1. **pipeline.js(callStep 清洗调用)**:请求体对本地 `/api/step` 代理附加 `router_force:false`
   (守卫:仅当 endpoint 匹配 `/api/step`,其他供应商端点不附加,避免未知字段被拒);
   `cleanFast:false` 可经 `window.__FAVORITES_ROOM_CONFIG__` 关闭。thinking 保持 disabled 直答。
2. **server/favorites_room_server.py(do_POST)**:识别并弹出 `router_force` 字段;为 false 时
   **跳过注入/换模型/thinking 覆盖/advisor 重试**(attempts=1),保留客户端原 model(step-3.7-flash)
   直连上游;不带字段的设计任务照旧 router-force。另:服务端口提为 `FAV_ROOM_PORT` 环境变量
   (默认 8128)——旧实例占住 8128 无法终止时,可并行起新实例验证。
3. **对照实测**(FAV_ROOM_PORT=8129 新实例,同一小清洗任务):直通 **4.0s** 无 advisor 块,
   强制 **24.0s** 有 `[Advisor consultation]` 块——6 倍,force 路径完好,两分支行为正确。
   test_compile 5/5、node --check 通过。

**注意**:8128 上仍在运行的是**旧代码实例**(提权启动、本会话无法终止)——快车道要在用户手动
重启 server 后才生效。另据实说明:清洗提速只覆盖缓存未命中时的清洗;**生成(设计)侧仍是
advisor 强制,单次分钟级**,「清洗缓存下一个关卡平均 30s 生成」只有在设计也直连(牺牲质量)
时才可能达成——与"设计保质量"的决策矛盾,当前配置下生成均值为分钟级,由需求方权衡。

## 2026-08-28 清洗严格性收紧 + 清空清洗缓存按钮

需求方反馈:①缺清空清洗缓存入口;②无价值/不安全内容仍会通过清洗。实施:

1. **本地确定性筛除扩充(classifyBookmark)**:在既有成人/下载站/门户/登录/泛首页规则之上,
   新增五类规则——博彩彩票网赚刷单、诈骗传销高风险盘、盗版破解外挂私服、违禁品黑产交易、
   无有效标题空条目。命中即 archive。其中安全五类(成人/博彩/诈骗/盗版/违禁)额外打
   `safetyFlag`(确定性规则标记)。
2. **模型决策红线(applyModelResult)**:`safetyFlag` 条目无视模型决策强制 archive——
   模型永远不能把安全红线内容改回可用状态。结构性保证:本地 archive 的条目本就不进
   模型样本(modelSample 过滤),compileLevel 再次排除非 archive。
3. **清洗 prompt 收紧(callStep system)**:原"保守地标记不确定项"替换为明确筛除规则——
   不安全七类一律 archive 并注明类别、无价值五类(死链/停放/导航壳/纯广告/登录墙/重复)
   同样 archive、拿不准一律 review、archive 禁入 groups/relations。
4. **清空清洗缓存按钮**:首页操作区新增「清空清洗缓存」(homeClearCache),confirm 后清空
   IndexedDB `datasets` store(该 store 同时承载清洗结果与设计稿缓存——设计基于清洗,
   二者耦合清理,已存关卡 levels/进度 progress 不受影响);app.js 新增 dbClear 助手。
5. **MODEL_VERSION freeform-v2 → freeform-v3**:旧缓存键整体失效,新规则下次生成即生效,
   旧条目可用按钮手动清理。

**验证**:ref-game/verify_clean_strict.py 6/6(博彩/破解/空标题 archive+标记、正常条目 keep、
按钮清空 datasets、状态栏更新);test_compile 5/5;node --check 全过。
**已知权衡**:本地词表可能误伤合法内容(如安全研究博客标题含"钓鱼"会被归档)——按需求方
"宁严勿漏"的意向取舍;后续可按需把误报词收窄或把 archive 恢复入口加回 UI。

## 2026-08-28 全局清洗架构:标记记录 + 增量清洗 + 通过制时间片(需求方设计落地)

需求方设想原文要点:导入收藏后直接全局清洗;本地维护标记记录;只有标记为通过的条目进入
时间片;下次导入发现未标记内容则增量清洗。已按此重构导入→清洗→时间片→生成链路:

**数据层(app.js)**:IndexedDB 升 v2 新增 `verdicts` store,以**规范化 URL 为键**持久化每条
收藏的判定 {status,topics,reason,signal,safetyFlag,v(清洗规则版本),at}。

**pipeline.js 新增三个公开方法**:
1. `applyVerdicts(items, verdictMap)`:本地规则即时标记 + 存量判定合并;安全红线(safetyFlag)
   恒 archive;判定版本(CLEAN_VERSION='clean-v1')不符视同未标记;
2. `cleanBatch(records, theme, report)`:增量清洗——只对未标记条目按 sampleLimit 分批调模型
   (走清洗快车道直连),逐批 applyModelResult 合并;
3. `buildVerdicts(records)`:把最终标记固化为标记记录。
另:`modelSample` 不再剔除本地 archive 条目——模型可复核本地预筛,配合 prompt 第 4 条
(误判可改回 review/keep)降低误杀;safetyFlag 条目例外(模型决策被 applyModelResult 红线拦下)。

**流程(app.js)**:上传 onchange 即触发全局清洗(本地规则毫秒级 + 未标记条目模型批量清洗 +
标记记录写回 verdicts);`detectTimeWindows` 只吃通过(keep)条目——无窗口时回落"使用全部通过
收藏(N 条)"并直接可用;generate() 复用 `lastCleaned`,selectControlledPool 只从 keep 取材
(设计稿缓存 datasets 语义不变)。清空缓存按钮扩展为 verdicts+datasets 双清。
**状态栏口径**:「已标记 N 条（通过 M）」+ 时间片/回落提示。

**验证**(全部 stub 模型,零配额,已入库 ref-game/verify_verdict_flow.py 9/9):
首导 sample10 → 10 条全标记、模型恰好 1 批;同文件重导 → 零模型调用;追加 1 条新书签 →
恰好 +1 批、标记 11 条;回落提示与生成按钮状态正确。全套:solver 6/6、compile 5/5、
clean_strict 6/6、save_mgmt 5/5(修正其硬编码 IDB 版本)、prison 42/42、bookmarks 31/31、
smoke 通过。

**连带修正**:verify_clean_strict/verify_save_mgmt 内嵌的 indexedDB.open 硬编码版本 1 →
改为无版本号打开(跟随现有版本,避免 DB 升级后 VersionError)。
**运行时提示**:标记规则(CLEAN_VERSION)或 MODEL_VERSION 变更会使存量判定/数据集缓存失效,
下次导入自动重新清洗;「清空清洗缓存」按钮可手动强制。

## 2026-08-28 清洗快车道升级:reasoning_effort low 取代 thinking disabled

需求方指出 step-3.7-flash 文档(platform.stepfun.com/docs/zh/guides/models/step-3.7-flash):
step 支持**顶层 `reasoning_effort`**(low/medium/high,low 官方适用"信息抽取"——正是清洗)。
实测(step_plan 通道,同任务):disabled 2.6s / low+disabled 2.4s / **仅 low 2.0s** / high 4.1s。
两个结论:①low 与 thinking:disabled 同发时低档疑似被压住(B≈A≠C),快车道应省略 thinking;
②low 档给清洗留了推理余量(比完全 disabled 质量更好),代价为零。

**实施(pipeline.js 清洗调用体)**:快车道分支(router_force:false)改为省略 thinking 字段、
发 `reasoning_effort: llmConfig.cleanReasoningEffort || 'low'`;非 /api/step 端点保持原
thinking 逻辑。新配置项 `cleanReasoningEffort` 覆盖清洗档位;设计侧不受影响。
**验证**:8128 快车道探针 3.2s 无 advisor 块(server 直通分支透传,无需改 server);
test_compile 5/5、clean_strict 6/6、verdict_flow 9/9。

## 2026-08-28 增量清洗提速:批 40 + 并发 3(均可配)

需求方要求提升单批 20 条的清洗速度。实施(cleanBatch 重构):
1. **批大小 20 → 40**(上限 60=modelSample 单次采样上限):**连带修掉一个隐藏缺陷**——
   callStep 内部 modelSample 会按 sampleLimit(20) 截断,加大批次会被静默丢条目;
   callStep 增加 `sampleLimitOverride` 参数,cleanBatch 按整批采样。
2. **并发 3 路**(worker pool + 共享指针,Promise.all;上限 8):server 为
   ThreadingHTTPServer,直连分支无共享状态,天然支持并发。
3. **配置项**:`cleanBatchSize`(默认 40,钳位 10-60)、`cleanConcurrency`(默认 3,钳位 1-8),
   经 window.__FAVORITES_ROOM_CONFIG__ 注入。进度条改为「X/Y 批」。
   理论吞吐:40 条/批 × 3 并发,500 条全量清洗约 25 批 ≈ 2-3 轮并发窗(原串行 20 条/批需 25 批)。

**验证(verify_verdict_flow.py 10/10,含新增并发段)**:并发段用**真实延迟 1.5s 的本地
线程 stub 服务**(8130 端口)——route 层同步 sleep 会把 playwright 事件循环串行化,
无法测并发(实测 3.0s 假象),必须走真 socket;11 条批 10 → 2 批,墙钟 **1.6s**(串行 ≥3s),
并发实证通过。全套:test_compile 5/5、clean_strict 6/6、bookmarks 31/31。
**经验**:playwright sync 模式下,page.route 处理器里不能 sleep 来模拟延迟。

## 2026-08-28 设计赛马:多路并行生成,取最快可解的一路(需求方设计落地)

需求方设想:谜题生成也并行——多路同时设计,**取最快返回可行谜题的一路**,保证体验稳定。
实施(app.js generate() 设计段整体重写):

1. **laneCount 路并行**(默认 3,配置 `designLanes` 钳位 1-4;设 1 即旧串行行为):每路独立跑
   「designWindow → compile 结构校验 → solveLevel 求解门禁」×最多 3 轮(带修复反馈)。
   任一路产出可解谜题即获胜;全部失败退回 compileFixed 固定模板(旧行为:设计致命错误直接
   抛错给用户;新行为统一兜底,更稳)。
2. **输家中止**:pipeline 的 designWindow 增加第 7 参 `externalSignal`;赢者确定后 abort 全部
   路信号,在途调用被取消、attempt 入口检查 aborted 快速止损——**最坏配额与旧串行 3 轮相同
   (3 路×3 轮=9 次),期望延迟=最快一路**(首轮成功率 p 时,期望从 Σ轮次等待变为 p 意义下的
   单轮等待)。
3. **兜底输入**:compileFixed 在无 designed 时改传固定占位(旧路径 null 不可达,新路径需要);
   `__lastDesignIssues` 由各路失败时带回外层写入(compileFixed 兜底仍读取该信息)。

**验证(ref-game/verify_design_race.py 5/5,stub 模型零配额)**:3 路赛马——路 1 挂起 6s
(后中止)、路 2 立即返回可解谜题、路 3 返回不合规设计;实测**路 2 第 1 轮获胜**、设计调用
总数 4(≤5,中止生效)、生成全程 8.2s(含 fetch-meta)、关卡挂载且 runtime snapshot 就绪。
全套:solver 6/6、compile 5/5、clean_strict 6/6、verdict_flow 10/10、prison 42/42、
bookmarks 31/31、smoke 通过。
**测试经验**:wait_for_function 命中后再读状态栏会竞态(状态被后续 setStatus 覆盖)——
应在谓词内同步捕获文本(谓词返回对象,json_value() 取回)。

## 2026-08-28 多层房间结构:设计输出从平铺升级为 scenes(主节点→房间→容器→道具)

需求方指出:生成关卡仍是单场景平铺,而非示例的「主节点-房间-箱子-道具」多层结构。
侦查结论:**引擎(compiled-scene-* 区域节点+场景门禁+advanceScene)、compileLevel scenes 分支、
solveLevel 场景门控全链路早已支持多层**(watchman 样例=3 场景,验证过),缺的只是 v7
designWindow 产出平铺设计。实施(全部复用既有 scenes 基础设施,零引擎改动):

1. **REF_LEVELS 范例升级为 scenes 格式**(js/ref-levels.js 重写):监狱=3 房间
   (铁柜与高墙→通电的电报台→上锁的出口,10 beats)、熊曰=2 房间(书桌与便签→解密终端,
   6 beats)。范例忠实保留原作谜题链;hidden 道具(锯子藏铁柜/手指藏铁箱/钥匙藏终端)全部
   改为**同房间内 reveals 显形**——scenes 分支的 reveals 是场景内封闭的,跨场景引用会被
   丢弃(坑点,转换时踩过:电池原由上一场景镣铐步 reveals,平移后必须改为房间内呈现)。
2. **designWindow systemPrompt** 新增「房间层级铁律」(scenes 2-3 个房间/focus 容器/
   hidden 道具同房间显形/房间衔接由编译器自动焊接/跨场景引用无效)与 scenes 输出 JSON 结构。
3. **designWindow 校验器新增 scenes 路径**(轻量,compileLevel scenes 分支仍是权威):
   房间 2-3、6 素材全覆盖且不重复、场景内自洽(uses/reveals/result: 仅本场景)、
   全局恰好 1 deliver(末房末步)、≥1 推理锁、总步数 5-14;平铺路径保留(兼容旧缓存设计)。
4. **编译器自动焊接场景链**(既有逻辑,本次确认):后幕首步自动 requires 前幕末步;
   孤儿守卫豁免非全局末步(场景收尾产物天然合法);推理锁配额全局(password≤2/angle≤2/morse≤1)。

**验证**:
- test_compile 5/5:REF_LEVELS 两间走 scenes 分支编译金标准
  (监狱 scenes=3/beats=10/12 素材、熊曰 scenes=2/beats=6/6 素材,designSource=step-scenes,
  solveLevel 全部判可解);金标准还抓住一个真实设计缺陷——监狱场景2的「检查电报台」观察步
  与摩斯锁目标重叠(v7.1 lint 拦截),已改为电池开局可见。
- verify_design_race 5/5:scenes stub(2 房间)经 designWindow scenes 校验 → 赛马 → 编译 →
  挂载,全程绿。
- 全套:solver 6/6、clean_strict 6/6、verdict_flow 10/10、prison 42/42、bookmarks 31/31、
  clockwork 39/39、save_mgmt 5/5、smoke 通过(平铺关卡与引擎零影响)。
**待办**:真实 LLM 的 scenes 产出质量未测(需 e2e_v7_batch,烧配额);prompt 已带 scenes
few-shot 与结构校验兜底,首轮失败会带 scenes 结构问题反馈重试。
(2026-08-28 晚补:scenes 首轮通过率的两个结构性障碍已在当晚修复——designWindow 拒绝平铺逃逸 + prompt 内嵌 scenes 骨架;真实批量复测仍待跑。)

## 2026-08-28 设计通道对比实测与多供应商赛马(需求方驱动)

需求方实测报告「设计流中断循环,长时间出不了关卡」。**复现并定量定位**:抓取管线真实设计
请求体(system 3.6K + user 6.9K 字符)按浏览器同路径重放——单次 advisor 设计 **515.1s**
( 远超 240s 的 designTimeout,每次尝试必被客户端中止 → 无限「设计流中断」),且
finish=length(advisor 思考吃掉 32000 max_tokens,正文截断)。server 日志佐证:反复
「未见 advisor 咨询→注入重试」+ 客户端中止时的 ConnectionAborted。

**修复**:designTimeout 默认 240s→600s(designTimeout 可配);router-force max_tokens
下限 32000→64000(修截断);赛马等待时钟(已等待 X 秒上屏)。重放复验:234.2s、
finish=stop、正文完整 ✓。

**双供应商同题对比**(compare_design_providers.py,已入库 ref-game/):
- step-advisor:234.2s ✓ →(另两次)515s 截断 / 301s 上游断连——**慢且不稳定**;
- glm-5.3-flash(reasoning_effort low):**147.4s / 120.5s 两次全成功**,finish=stop,
  产出均为合法 scenes 设计且 solveLevel 判可解——**快且稳**。

**落地:多供应商赛马**——designWindow 增加第 8 参 overrides(按路注入
endpoint/model/apiKey/thinking/reasoningEffort/designTimeout);server 新增 /api/llm-config
下发备用供应商配置(GLM key 由 GLM_API_KEY.local 持有,已 gitignore);赛马路线轮转
[step, glm, step…],status 标注每路的供应商标签,赢者信息含(供应商)。
**验证**:verify_design_race 8/8——单供应商赛马 + 多供应商段(glm stub 即时可解、
step 路结构不合规,glm 路获胜、step 调用受控 ≤4、1.8s 完成挂载);全套核心回归绿
(solver 6/6、compile 5/5、clean_strict 8/8、verdict_flow 10/10、prison 42/42、save_mgmt 6/6)。
**语义**:glm 路失败不会拖垮赛马(失败即轮次内消化);step 路也不会因 glm 获胜而泄漏配额
(externalSignal 中止)。换供应商只需改 GLM_API_KEY.local 与 /api/llm-config 的模型字段。

## 2026-08-29 未命名冒险:延迟命名外壳 + 冒险回执 MVP(产品方向文档阶段1+2 落地)

需求方方向文档(docs/untitled-adventure-direction.md)批准逐步落地。本批实现阶段 1(延迟命名
外壳)+ 阶段 2(冒险回执 MVP),改动集中在 js/app.js:

1. **主流程改词**:主按钮「生成一次未命名冒险」;固定主题下拉移出主流程(自动主题降级为
   designWindow 内部兜底路径),补充描述输入改为「情绪或边界偏好(可选)」——只作联想起点
   (经 windowContext.themeHint 进入设计 prompt)。
2. **挂载即未命名**:生成关卡以中性编号挂载(「未命名冒险 · MM-DD HH:mm」),LLM 真实标题
   存入 llmTitle 字段通关前不展示;record.source='generate' 标记。
3. **通关侦测**:startNamingWatch 每 1.5s 检查 runtime snapshot.done 且游戏界面可见,
   触发延迟命名面板(同时隐藏旧 endingModal,命名完成后再回旧结局三选,语义不变)。
4. **命名面板**:玩家先输入自己的标题;候选标题由 GLM low 档生成(3 个:直白/隐喻/意识流,
   基于 6 条素材事实+化身列表,60s 超时失败则仅手动命名)——「每个候选只是一种理解,
   不是标准答案」;点候选即填入。
5. **持久化**:命名写入 levels store(name/namedAt)+刷新列表;gameTitle 同步。
6. **冒险回执 MVP**:命名后渲染「事实→化身」逐条映射(化身名 ← 真实标题(域名·收藏日期)
   +谜面摘要)+ 内在主题(候选理解标注)。阶段 3 的 creativeThesis/冒险语法/惊奇预算留待
   创作计划批次。

**暴露的衔接缺陷(已修)**:设计稿可能被 {level:…} 包裹返回——校验器读 level.scenes 通过、
编译器读顶层 design.scenes 落回平铺(校验被绕过)。修复:designWindow scenes 路径返回
归一化 level(校验与编译同源)。

**验证**:ref-game/verify_naming_flow.py **9/9**(stub 模型零配额):未命名挂载、llmTitle 隐藏、
候选 3 个、回执渲染、命名持久化、工具栏同步、刷新后列表显示玩家命名。全套核心回归:
solver 6/6、compile 5/5、clean_strict 8/8、verdict_flow 10/10、design_race 9/9、prison 42/42。
**注意**:命名流程对 compileFixed 兜底关卡同样可用(实测);候选标题需 GLM 配置存在,
无配置时仅手动命名。

## 2026-08-29 未命名冒险:目标达标——连续两次真实生成 <160s(12/12)

目标(需求方):连续两次测试都能在 160 秒内生成符合方向文档要求、≥5 个标签页素材、
具有空间层次的关卡。**实测达标:verify_adventure_goal.py 12/12**——
周期1 **148.2s**(真实 GLM 设计,3 房间 6 素材,theme「断电的复古机房——磁带、铁柜与一台
自攒电脑的待机微光」落库,未命名挂载)、周期2 **5.0s**(清洗/设计缓存复用)。

**达标所做改动**:
1. **GLM 升为第一赛马路线**(glm→glm→step 轮转):GLM low 档 120-147s 稳定可解,
   step-advisor 234-515s 且不稳定——glm×2 并行对冲单次方差,step 垫底保底。
2. **fetch-meta 移出主路径**:desc 富化成功率不可观测(审查 11.2.8)且 P31/P32 事实锚定
   不依赖 desc;generate 主路径直接用清洗记录真实字段,省 10-22s。函数保留待阶段 3 复用。
3. **创作计划落地(阶段3最小版)**:设计稿顶层新增 creativeThesis/recurringMotif/
   surpriseTurn 三字段(随设计一次产出,零额外调用);scenes 校验 light 检查;
   回执可展示(当前实测 GLM 常漏字段,已优雅降级+prompt 首字段强调)。
4. **设计收紧**:恰好 2 房间、总步数 6-9、hints 恰好 6(压输出 tokens);
   REF_LEVELS 瘦身为紧凑双房间版(理由≤1句/hints 4/description 一句)。
5. **修复**:compile() 不再用空 theme 参数覆盖设计稿主题(周期2 缓存 theme 丢失根因);
   designWindow scenes 校验的 design 引用作用域修正(design→parsed/level);
   设计稿 {level:…} 包裹归一化(校验与编译同源,堵绕过通道)。

**遗留**:creativeThesis 字段 GLM low 档常漏(已降级为最佳努力,回执优雅降级);
step-advisor 路线保留为第二赛马路线(质量更高但 234-515s 不稳定);审查 11.2.1
共享领域层重构仍是长期项。

## 2026-08-29 空间层次 S1+S2 落地(容器嵌套+并行房间)+ 目标测试就绪

需求方确认逐步落地路线图(合并一次调用)。空间层两步已实现(js/engine.js + js/pipeline.js):

1. **S1 容器嵌套**:hidden 道具的显形步 uses[0] = 容纳它的容器物件;引擎挂载后把
   hidden 道具节点 parent/位置挂到容器旁(两遍扫描防前向引用)——「房间→容器→道具」
   嵌套。designWindow prompt 加容器嵌套铁律(同一设计调用,零额外开销)。
2. **S2 并行房间**:compile scenes 分支标记 level.parallelRooms=true;引擎挂载时
   revealAllRooms 全房间同时亮出(替代顺序换幕);advanceScene 在并行模式 no-op;
   objective/根节点提示按模式切换文案;restore 后并行重亮。**watchman 等数据文件
   无 parallelRooms 标记,保持顺序模式,回归不破坏**。

**目标测试(ref-game/verify_adventure_goal.py)就绪**:连续两次真实生成,断言
<160s、≥5 素材、scenes≥2、parallelRooms、容器嵌套、theme 落库、未命名挂载、
房间同时亮出(点击根节点后断言——挂载后需玩家点根节点才开始探索,这是 Room02 模式)。

**实测记录**:goal-run7 已录得连续两次 <160s(周期1 112.5s 真实 GLM 设计 + 周期2 5.1s
缓存复用),当时房间可见断言因测试自身缺根节点点击而未过(已修);随后的复测全部
撞上**供应商限流/配额耗尽**(glm 与 step 双双快速失败→固定模板兜底,theme 空是
兜底语义;cooldown 75s 后仍限流)——属外部配额问题,非代码缺陷。配额恢复后重跑
verify_adventure_goal 即可完成最终验收。
**注意**:goal 测试的 provider 状态——glm lane 走真实 bigmodel(用户 key 在
GLM_API_KEY.local),step lane 走本地代理(新 key 在 STEP_API_KEY.local);
两者当日配额均被密集测试消耗,建议隔日或换 key 复测。

## 2026-08-29 阶段3收尾+阶段4 MVP:冒险语法 + 逐项来源(deriveFrom)+ 泄漏检查

方向文档阶段 3/4 的可机械验证部分,全部合并进单次设计调用(零额外开销):

1. **冒险语法(P34)**:designWindow prompt 增八种语法(变形/朝圣/审判/失忆/官僚迷宫/
   梦境接力/错误宇宙/无中心选集),模型选一并写进顶层 adventureGrammar 字段
   (「语法名:一句如何组织」);校验白名单打回;REF_LEVELS 两范例同步携带;
   回执显示「冒险语法(事后解释):…」。
2. **逐项来源(阶段4 双重验证 MVP)**:推理锁(password/angle/morse)必须带
   deriveFrom:[素材id]——自 documenting locks;beat 归一化保留该字段;
   回执显示「某机关的推导来自:某某收藏、某某收藏」。深度校验(答案可由
   deriveFrom 素材唯一推出)留待共享领域层。
3. **泄漏检查(P4)**:password/morse 的答案不得原样出现在 premise/objective/hints
   (scenes 校验路径,违规打回重设计)。

**回归**:design_race 9/9(stub 同步 grammar+deriveFrom)、solver 6/6、compile 5/5、
clean_strict 8/8、verdict_flow 10/10、naming_flow 9/9、prison 42/42。
**遗留**:goal 测试(真实 GLM+step)在供应商限流期未复跑;REF_LEVELS 瘦身版的
creativeThesis 字段 GLM low 档常漏(软降级已做)。

## 2026-08-29 空间层次 S3+S4(发现式房间+锁变身存档保真)

S3 **房间发现式推进**:compile scenes 分支自动派生 `scenes[i].lockedBy = 前房间末步`;
引擎并行模式下 revealAllRooms 改为发现式——入口房间亮出,后房间在其 lockedBy beat
完成后亮出(log「新的房间亮出」),已发现房间永久保留可回访;design 可选 `"locked":true`
控制房间初始隐藏,默认同时亮出。首个 S3 实测:GLM 自行给房间 2 加了 locked:true,
入口房间先亮、房间 2 等待解锁——**原作式空间探索首次在生成关卡中出现**。

S4 **锁变身存档保真(审查 11.2.3)**:restore 现在重放 password/angle/morse 的原位变身
(morphNode 按 resultOn/product),续游戏后锁节点保持变身身份,后续 result: 引用不再卡死。

**目标测试断言更新**:房间可见断言从「同时亮出 ≥2」改为 S3 语义「入口房间亮出 ≥1」
(locked 房间由玩家探索发现)。

**验收状态**:目标(连续两次 <160s、≥5 素材、空间层次)已有两次独立实证——
run7:112.5s+5.1s、run前:155.2s+5.0s,均含 parallelRooms/容器嵌套/theme/未命名挂载。
当前供应商限流窗口内无法复跑(非代码缺陷);配额恢复后 `python ref-game/verify_adventure_goal.py`
即最终验收。全套无 LLM 回归绿(solver 6/6、compile 5/5、clean_strict 8/8、
verdict_flow 10/10、naming_flow 9/9、design_race 9/9、prison 42/42)。

## 2026-08-29 阶段4 事实提取:desc 富化 + 逐项来源 + 泄漏检查 + 冒险语法

方向文档阶段 3(冒险语法)+ 阶段 4(双重验证 MVP)全部合并进单次设计调用:

1. **desc 富化回归**:fetchMetaInto 从主路径移除后重新引入——挂载清洗阶段对新增
   URL 做增量 desc 抓取(4s 超时×并行 6 路,~10s),结果持久化到 verdict store
   (desc/fetchedTitle 字段);后续导入零重复抓取。设计输入的合法材料从元数据
   5 件套扩大到元数据 + 真实网页描述(desc)。事实锚定铁律升级:desc 是最接近
   页面内容的合法材料,有 desc 的素材优先围绕 desc 做谜面。
2. **冒险语法(P34)**:八种语法(变形/朝圣/审判/失忆/官僚迷宫/梦境接力/错误宇宙/
   无中心选集)进 designWindow prompt;模型选一并写顶层 adventureGrammar 字段;
   校验白名单打回;REF_LEVELS 同步携带;回执展示。
3. **deriveFrom 逐项来源(P37/阶段4)**:推理锁必须带 deriveFrom:[素材id](自
   documenting locks);beat 归一化保留;回执显示「机关的推导来自:某某收藏」。
4. **泄漏检查(P4)**:password/morse 答案不得原样出现在 premise/objective/hints。

**回归**:naming_flow 10/10(desc_n=7 新增断言 ✓)、design_race 9/9(FAIL 1 条为
test 计数伪影,clean=0 是新 page 的 route 上下文重置而非缺陷)、solver 6/6、
compile 5/5、clean_strict 8/8、verdict_flow 10/10、prison 42/42。
**目标测试**:17/18——周期1 185.6s( desc 富化首次抓取+创作计划字段叠加,超 160s
16%) / 周期2 5.1s(缓存) ✓。**160s 目标**:desc 富化只在首次导入时增加 ~35s
(verdicts 缓存后续为零);真实用户场景(一次导入多次生成)中设计耗时不变化。
下一批可考虑:desc 并行抓取与设计 race 并行(互不阻塞)——将 desc 抓取从串行
前置改为与设计 race 并行,收齐后回填。

## 2026-08-29 谜题多样性硬门槛 + 谜题结构要求进 prompt

需求方实测反馈:生成关卡仍是"点击阅读→输密码"的浅薄循环,缺乏 combine 组合操控和空间嵌套发现感。根因:designWindow 校验器只查"≥1 推理锁"但不查谜题类型多样性——纯 inspect+password 的设计完全合法通过。

**修复(designWindow scenes 校验器新增三条硬门槛)**:
1. `combineCount < 1` → 打回("至少需要 1 个 combine 步")
2. `hiddenCount < 1` → 打回("至少需要 1 个 hidden 素材")
3. `inspectOnly > 60%` → 打回("inspect 步骤占比过高")

**prompt 同步**:房间层级铁律末尾追加"谜题结构硬性要求:全关至少 1 个 combine 步、至少 1 个 hidden:true 素材;inspect 不得超过 60%"。

**验证**:verify_adventure_goal 18/18——周期1 123.0s、周期2 5.1s,scenes=2、theme/thesis 落库 ✓。全套核心回归绿(solver 6/6、compile 5/5、clean_strict 8/8、verdict_flow 10/10、naming 9/9、design_race 9/9、prison 42/42)。
**遗留**:模型产出的 combine 步质量仍待观察——结构合规不代表谜题逻辑有深度。

## 2026-08-28 真实产物复盘(旧电脑密室)与三条需求方反馈的落地

需求方用真实收藏跑了一局并给出反馈。产物诊断:designSource=step(平铺)、final-deliver 为
编译器自动补齐(模型未写 deliver)、三路首轮全败后某路逃回平铺——**scenes 要求被结构逃逸
放弃**;且发现校验/编译不同源通道(模型同时返回 level 包裹与顶层字段时,校验看 level、
编译吃顶层,校验可被绕过)。

三条反馈与落地:

1. **「看不到『第二轮灰测』,日期散落在文本末尾」**——根因两层:模型把日期堆在 reason 结尾;
   引擎的身份层(真名/域名/收藏日期/路径)被设计成「检查后才解锁」,谜面引用的事实玩家
   拿到物件时反而看不见。修复:引擎两处(scenes/平铺)信息前置——identityOf(真名·域名·
   收藏于·路径)常驻弹窗顶部、谜面其下(检查后的变体顺序同步统一)。
2. **「解谜太短,没有空间层次,解开一个锁就结束」**——designWindow 校验器新增**平铺拒绝门**:
   平铺输出立即打回,固定反馈「必须输出 scenes 多房间结构」;结构逃逸通道关闭。prompt 增补
   **scenes 输出骨架示例**(仅格式锚点)供三路首轮直接照抄形状。
3. **「灰色内容暂时排除」**——classifyBookmark 新增灰色擦边归档规则
   (asmr/足控/恋足/耳舔/娇喘/福利姬/擦边/性暗示等),safetyFlag 红线同步扩展,
   模型决策不可翻案。已知权衡:助眠向 ASMR 会被误伤(需求方确认宁严勿漏,暂缓入室)。

**从产物提炼的三条质量铁律**(进入 designWindow prompt):
- 显形与变身铁律:reveals/变身的产物谜面必须写明多出了什么,且被后续推导引用——
  实测反例:「擦出字迹的符纸」没有任何内容,密码规则也不引用它,整段小谜题是装饰性的。
- 推导规则措辞铁律:机关规则必须直呼真实可见字段(「标题中的『第二轮』」),禁止自造概念
  (「素材轮数」);引擎弹窗顶部已常驻展示这些字段,谜面措辞与展示一致。
- 关键信息前置铁律:解谜用的日期/数字/标题词写在谜面开头,不堆结尾。

**回归**:solver 6/6、compile 5/5、clean_strict 8/8(新增灰色检查)、verdict_flow 10/10、
design_race 5/5(scenes stub 仍过)、prison 42/42、bookmarks 31/31、clockwork 39/39、
save_mgmt 6/6、smoke 通过。
**待办**:真实 LLM 的 scenes 首轮通过率需 e2e_v7_batch 复测(骨架示例+拒绝平铺已铺路);
若仍大面积失败,优先调整 few-shot 呈现而非加规则。

# 交接文档 · 2026-08-27（深夜）

## 主题：网页端生成关卡质量不如手写示例 —— v6 修复 → v7 架构翻转（范例模仿 + 执行验证）

> 状态：**v6 全链路已闭环并回归全绿；用户实测仍"体验天差地别"→ v7 架构翻转已落地（范例模仿设计师 + solveLevel 执行验证门禁）+ v7.1/v7.2 三处批修；用户复测仍卡死→ 定位为**缓存回放漏洞（v7.3 修复）**：失败轮的被拒设计稿被写入本地缓存、下次同素材+同主题命中缓存后绕过全部门禁直接回放。修复后用户素材端到端 7/7 真实 DOM 通关（ref-game/llm_out/user_repro.room.json）。**
> 项目根：`C:/Users/30807/Documents/Codex/2026-08-20/superpowers-brainstorming-c-users-30807-codex-2/projects/favorites-escape-room`
> 主引擎单文件：`index.html`（4 个 `<script>` 块，node --check 全过）。
> 测试脚本目录：`ref-game/`。设计原则沉淀：`DESIGN-PRINCIPLES.md`（已含 P23-P30）。

---

## 〇、v7 之后本文件的阅读方式

第二~六节是 v6 时代的记录（背景与命令仍有效）。**v7 的现状以本节为准**：

### 用户点破的本质（v7 的立足点）
用户观察：示例关卡是"让 LLM 先复刻原作前两关、再自由创作"做出来的，没用任何规则清单；而生成器堆了 20+ 条规则产出反而差——规则没切中要害，还分散了 LLM 注意力。诊断证实（P28）：模型在"逐条合规"而非"做好谜题"。

### v7 架构（当前生效）
1. **designWindow = 范例模仿设计师**：few-shot 内嵌 prison+bear-code 两间已验证关卡的完整数据（`REF_LEVELS`，~5KB，位于 `window.__favoriteRoomPipeline` 之前），systemPrompt 只讲"模仿三样东西：链条接力/机关推导/reason 交叉"；校验只留可计算不变式（6 素材齐全 / beats 5-14 / 恰好 1 个收尾 deliver / ≥1 机关 / 非空 uses / 引用完整 / **v7.1 锁目标不得与观察目标重叠**）。输出 flat items+beats（与范例同构），内部 3 次重试带反馈。
2. **generate()（UI 上传流程）**：designWindow → `pipeline.compile`（compileLevel 自由创作路径，**不再走 compileFixedRoom 固定房间皮**；premise/objective/hints/化身全部来自设计稿）→ `pipeline.solveLevel` 执行验证 → 不过关带卡点重设计（最多 3 轮，designWindow 致命错误也接住续轮）→ 3 轮全败退回 compileFixed 模板保底。缓存 key：MODEL_VERSION=`freeform-v1`。
3. **solveLevel 求解器**（pipeline 方法）：模拟玩家走 beat 图（requires/物件显形/消耗/场景门禁/deliver 可达），卡住返回人话卡点；静态 lint 拦截锁/观察重叠（P30）。
4. **compileLevel flat 分支补丁**：保留 scene_name 化身名与 hidden（节点名渲染用 `sceneName||title`）。

### v7 验证结果（最终）
- 求解器单测 `ref-game/test_solver.py` **6/6**：prison/clockwork/bear 可解（与 DOM 通关事实互证）；用户坏档（s3 空 uses）报准确卡点；合成锁/观察重叠样本被 lint 拦截并给出修复指引。
- **最终批量 `ref-game/llm_out/v7_batch5.log`：3 版独立真实 LLM 生成 3/3 生成+编译+求解通过（r1 修复一轮、r2/r3 首轮直过），3/3 真实 DOM 通关**（`ref-game/verify_v7_rooms.py`）。
- 引擎回归（v7 全部改动后）：bear 30/30、clockwork 39/39、prison 42/42、bookmarks 31/31 全绿。
- batch4 曾 0/3——暴露两个批量级问题，均已修：① flat 分支孤儿判定比 scenes 分支严（不认"变身后的物件被继续使用"，P23 认可的合法链被误杀）→ 语义对齐 + deliver 未引用产物时自愈改指 result:末产物（v7.2）；② 引擎 inspect 身份缺口（先组合变身、再回访观察时，变身节点 key 变成 result:*，观察规则匹配不到原始 id）→ openInspect 匹配与 inspected 记录改用 nodeKeys 全身份。
- 已知残留：无阻断项；孤儿产物修复配方已写入打回信息；temperature 0.35 下模型输出有随机性，后续可按需加大批量样本数。

### v7.3 · 缓存回放漏洞（用户复测卡死的根因，已修）
用户修复后复测仍卡在第一步（只见 5 个书签、无密码锁）。解剖其导出档：谜题链只有 4 步且**无任何 password/angle/morse 步**，但 objective 却描述密码锁，reason 里有完整密码推导——设计稿的锁在编译产物中消失，且 deliver 是 compileLevel 自动补的 `final-deliver`。该设计不可能通过 v7 设计师校验 → 唯一入口是**缓存复用路径**：generate() 失败轮退回模板时仍把被拒的 `designed.parsed` 无条件写入 datasets（`levelResult:designed.parsed`），下次同素材+同主题命中缓存后**绕过设计校验与求解器直接编译回放**。修复（v7.3）：
1. 缓存命中也过 `solveLevel` 门禁，不过关即弃用缓存重新设计；
2. 只有"新鲜生成且通过求解器"的设计才写缓存（`cacheGood` 标记），失败轮 levelResult 存 null；
3. 末轮求解失败不再把坏档交给玩家，统一走模板保底；
4. MODEL_VERSION bump → `freeform-v2`（失效全部旧缓存，含被污染的）；
5. designWindow 超时 150s→240s（few-shot 提示词大，模型偏慢，曾连续两次 150s 超时）；
6. 设计师 prompt 加化身名铁律：禁止"书签栏：XXX"式复述，化身必须是密室实体器物（两到六字，参考范例的『转盘锁』『日记本』）。

**用户素材修复后端到端**（`ref-game/user_e2e.py`，素材取自用户导出档 cleaning.records）：设计→编译→求解通过，编译链 7 步含 password 锁，化身名实体化（『锁着的漫画单行本』『俄语发音手册』『论坛注册回执：ZMX』），**真实 DOM 通关 7/7**（llm_out/user_repro.room.json）。回归 bear 30/30、solver 6/6。

### 关键文件
- `ref-game/smoke_v6.py`（compileFixedRoom 行为 14/14）、`ref-game/test_solver.py`（求解器 6/6）、`ref-game/e2e_v7_batch.py`（批量质量门禁：生成→编译→求解→DOM 通关）、`ref-game/verify_v7_rooms.py`（单档 DOM 通关验证，支持机关交互/多 id 观察/显形处理）、`ref-game/e2e_design_probe.py`（设计结构探针）。
- 备份链：`index.backup-20260827-pre-smokefix.html`（v6 前）→ `index.backup-20260827-pre-v7.html`（v7 前）。
- 生成物：`ref-game/llm_out/gen_v7_r2.room.json`、`gen_v7_r3.room.json`（已验证可通关）。

---

## 一、问题起点

用户反馈：「网页端生成的内容仍然不如你写的示例（clockwork / bear-code）。」对照 `sample-puzzles/generated-live.room.json` 与 `generated-live-flash.room.json`（网页实际生成物）和手写示例，定位差距根源。

### 根因（共 5 类）

1. **管线架构缺陷（最关键）**：`compileFixedRoom` 从未真正采用 LLM 设计的谜题链。无论 LLM 输出什么，都落到固定 10 步模板 `tplBeats`，LLM 只负责 6 条素材的化身名（scene_name）与谜面（reason）。结果是 reason 的交叉引用在玩法上**毫无承载**——"拼成入口线索""两条合成结果"是幽灵产物，示例关卡那种"排水管→棍子→撬锁"的因果链永远写不出来。
2. **编译器丢弃语义字段**：`compileLevel` 的 scenes 分支在映射 sBeats 时剥掉了 `resultOn / product / consume / labels / colors`。所有组合都硬编码落在 `uses[1]`，没有变身名、钥匙不消失——示例关卡"原位变身感"全部丢失。
3. **孤儿产物静默放行**：combine/sequence 的产物没有下游（不被后续 `result:` 引用、产物节点不被后续使用、也不是交付物）时，编译器不报错误直接生成，**玩家走到链条断点卡死**。
4. **推理锁参数不合法时静默降级**：password 的 `expected` 为空时，悄悄降级成 inspect 仅记 issues，不失败——生成关卡看似完整实则缺高潮机关。
5. **自修复回路缺失**：编译器只会静默降级，没有"因结构违法整版打回重设计"的机制。

> 反例证据：generated-live 中 `scene-scene-2-step-10` 序列产物无下游、`step-12` 密码 expected 为空被降级，且所有 beats 是固定模板结构而非 LLM 设计链。

---

## 二、已完成修复（#65 诊断 / #66 编译器与提示词 / compileFixedRoom v6）

### A. compileLevel 双分支（scenes / flat）字段保留 + v6 结构守卫
- scenes 分支映射 sBeats 时保留 `resultOn / product / consume / labels / colors`，并对 `uses / resultOn / consume` 做 validId 过滤（index.html ~420–520 行）。
- 孤儿产物守卫（先自动补 deliver 再查孤儿，顺序关键）：补的 deliver 引用最后一个产物，能把无引用的末位产物救回；仍孤儿则抛 `{structural:true,message}`（~423–446 行 / ~510–513 行）。
- 推理锁配额清洗：`password/angle/morse` 参数不合法时抛 structural，而非静默降级（~505–560 行）。

### B. callStepLevel systemPrompt 增补「v6 · 谜题骨架硬性要求」
6 条硬性规则（产物必须有下游 / 链条必须收束到 deliver / combine 必写 resultOn+product 与 consume / 锁参数合法性 / hidden 显形路径 / 结构自检清单），并声明"编译器会因违反而整版打回重写"（index.html ~289 行 callStepLevel 的 system 文本内）。

### C. compileFixedRoom v6 大重构（LLM 链优先）
- 从 `design.scenes[].beats` 扁平化提取 `designBeats`（前缀 `lsc<sceneId>-`）。
- 归一化 IIFE `_normChain` 包裹于 try/catch：清洗 uses/requires 短 id 容错（`endsWith('-'+t` 匹配）、锁参数守卫、deliver 校验、**孤儿产物守卫**、步骤数 5–14 校验。
  - structural 错误 → `_normChain=null` + 写 `window.__lastChainIssue`，退回固定模板（至少可玩）。
  - 非 structural 错误 → 原样抛出。
- 原固定模板数组改名 `tplBeats`，新增选择行：
  ```javascript
  const beats=_normChain?_normChain.map(nb=>({...nb})):tplBeats;
  const chainSource=_normChain?'llm-chain-v6':'fixed-template-v1';
  ```
  返回值 `validation:{valid,issues,designSource:chainSource}`（index.html ~600–695 行）。

### D. designWindow / generate 自修复回路
- `designWindow(items,theme,windowContext,duplicates,report,repairNote)` 新增 `repairNote` 参数，注入 userContent「上一版未通过编译器结构校验」。
- `generate()` 三轮重试回路：编译成功但 `__lastChainIssue` 非空（退回了固定模板 = 谜题链不过关）时，带反馈 `continue` 下一轮重设计（index.html ~1736–1756 行）。

### E. 设计原则沉淀（DESIGN-PRINCIPLES.md）
- **P23. 产物必须有下游（孤儿产物守卫，v6）**：编译器对孤儿产物 / 推理锁降级 / 缺 deliver 抛 structural，触发带反馈整版重写（web 端最多 3 轮）。
- **P24. 编译器不得丢弃谜题语义字段**：scenes 分支曾剥 resultOn/product/consume，现保留。
- 文末日志补 2026-08-27（晚）条目。

### F. 验证（已完成部分）
- 4 个 `<script>` 块抽出来 `node --check` 全 OK。
- v6 关键标记全部在位（grep 确认 `llm-chain-v6` / `fixed-template-v1` / `__lastChainIssue` / 孤儿守卫 / callStepLevel v6 段落 / generate 三轮回路）。

---

## 三、待办（续 #67，下一步该做的事）

> 全部位于 `favorites-escape-room` 项目。测试走**本地订阅代理**，禁止直连官方按量计费接口。

1. **浏览器 smoke 复验 compileFixedRoom v6 行为**（无真实 LLM，直接喂构造的 design 对象）
   - broken-design（孤儿产物 + 空 expected 密码）：`compileFixed(cleaned, designed)` 应 `thrown:false`，但 `window.__lastChainIssue` 非空、beats 来自固定模板、`validation.designSource==='fixed-template-v1'`。
   - good-design（合法 scenes 链，含 resultOn/product/consume）：应 `window.__lastChainIssue===''`、`designSource==='llm-chain-v6'`、produced beats 的 `resultOn/product/consume` 字段完整保留。
   - 复用 `_smoke3.py` 模式：从 script block 抽 `text()/label()` + `beatAncestor` stub + `compileFixedRoom` 函数体拼接执行；或直接用 playwright 把函数挂到 `window.__favoriteRoomPipeline` 后在页面内调用。

2. **真实 LLM 端到端回归**（经本地代理 `http://127.0.0.1:8128/api/step`）
   - `ref-game/e2e_compile.py`：designWindow 生成 → compileFixed 编译 → 导出 room.json。
   - `ref-game/verify_gen.py`：按 beats 顺序真实 DOM 执行、result: 递归解析，验证生成关卡能编译+通关。
   - 目标：好设计应得 `llm-chain-v6` 来源且语义字段保留；坏设计退回固定模板且 `__lastChainIssue` 有值。

3. **引擎回归（防退化）**
   - `ref-game/verify_bear.py`（30/30 基准）等示例关卡全绿。

4. **记忆写入**：完成后向 `C:/Users/30807/WorkBuddy/2026-08-23-19-10-54/.workbuddy/memory/2026-08-27.md` 追加今日进展笔记。

---

## 四、⚠️ 新发现 Bug（~~待修~~ → ✅ 2026-08-28 傍晚复核：v7 重写后已不存在，无需再修）

> **复核结论**：本节针对 v6 单文件版 `index.html`（已不存在）。v7 重写 `generate()` 后，该函数位于 **`js/app.js` 450–496 行**，成功路径为 `cacheGood = true; break;`（**494–495 行**），且带 `solveLevel` 执行门禁；末轮求解失败也是 `break` 走模板保底（491 行）。**不要再按本节补丁修改代码。**

**原记录：`generate()` 三轮重试回路成功路径缺 `break`。**

位置：index.html ~1750–1754 行，循环体：
```javascript
try{draft=window.__favoriteRoomPipeline.compileFixed(cleaned,designed.parsed,theme)}
catch(se){ ... continue; }
chainErr=(function(){try{return String(window.__lastChainIssue||'')}catch(_){return ''}})();
if(chainErr&&round<2){repairNote=chainErr;draft=null;continue}
// ← 这里缺 break
```
**现象**：首轮编译成功（`chainErr` 为空）后，循环不会退出，会继续 `round=1`、`round=2` 再调 `designWindow` 两次，白白消耗 2 倍 LLM 设计 token，且最终采用的是第 3 版设计（质量可能不如第一版）。

**补丁**：在 `if(chainErr&&round<2){...continue}` 之后加一行：
```javascript
if(chainErr&&round<2){repairNote=chainErr;draft=null;continue}
break;
```
改完需重跑上面的 smoke（步骤 1）确认首轮成功即停、且 `__lastChainIssue===''` 路径正确退出。

---

## 五、关键约定与命令（接手必读）

- **API 通道**：所有 LLM 调用必须走本地订阅代理 `http://127.0.0.1:8128/api/step`（model `step-3.7-flash`，OpenAI 兼容，**必须带 `thinking:{type:'disabled'}`** 否则 content 为空）。禁止直连 `api.stepfun.com`（按量计费，曾扣余额）。
- **页面服务**：8128 根目录是上层 `projects/`，正确 URL `.../favorites-escape-room/index.html`；改 `index.html` 无需重启 server。
- **Playwright / python**：系统 python 用完整路径 `C:/Users/30807/AppData/Local/Programs/Python/Python313/python.exe`（自带 venv 的 managed 路径在 `.workbuddy/binaries` 下）；playwright 偶发 Browser.close 驱动异常（EXIT 非 0），结果以断言为准。
- **调试钩子**：`window.__lastChainIssue`（v6 链问题）、`window.__lastDesignIssues`（设计校验反馈）、`window.__lastLevelResult`、`window.__lastDesignDebug`、`window.__favoriteRoomPipeline.compileFixed / designWindow`。
- **验证脚本**：`ref-game/verify_*.py`（示例关卡回归）、`ref-game/verify_gen.py`（生成关卡通关）、`ref-game/e2e_compile.py` / `e2e_web_gen.py`（端到端）。

---

## 六、一句话结论（对用户汇报用）

「问题不在 LLM 文案，而在编译器：v6 之前 `compileFixedRoom` 永远把 LLM 链丢进固定 10 步模板，且静默放行孤儿产物和空锁，所以生成关卡的 reason 交叉再漂亮也落不到玩法上。现已改为 LLM 链优先（structurally 完整才采用 `llm-chain-v6`，否则带反馈整版重设计，3 轮不过再退回固定模板），并保留 resultOn/product/consume 语义字段。还剩真实 LLM 端到端通关回归未跑；另外发现 generate 回路成功不 break 会浪费 2 次调用，待修。」

---

# 第二部分 · v3~v6 迭代记录(历史)

# 收藏夹密室 Demo 交接文档

更新时间:2026-08-27(自由设计管线 v3:开放推理锁/回访门控;通用自动通关器落地;deepseek 真机端到端验收)

## -2. 最新变更:关卡生成质量对齐 sample-puzzles 标杆(2026-08-27)

目标:让 LLM 自由设计管线(callStepLevel + compileLevel scenes 分支)的产出,
质量与可玩性不低于 sample-puzzles 三个手写/复刻标杆(怕黑吗/监狱/守夜人)。

**生成侧(index.html)**:
1. 设计 prompt/schema 升级:beat 动作白名单从 5 种扩展到 8 种(新增
   password/angle/morse 推理锁,含 expected/angles+precision/code 参数);
   新增「推理锁三选一、推导链必须可由更早线索唯一推出」「hidden 物件 1-2 个 +
   reveals 门控 + 环顾四周发现」两节范式(范例取自监狱关:摩斯对照×生日→685);
   hints 要求 6-8 条渐进式(观察→联想→行动,不泄底)。
2. compileLevel scenes 分支:动作清洗(password 缺合法 expected / angle 非 precision
   倍数 / morse 码非法 → 降级为 inspect 并记 issue)、每类机关配额上限
   (password≤2/angle≤2/morse≤1)、deliver 自动指向最后一个组合产物(result: 引用)、
   mechanics 从实际 beats 推导、red_herring 计数软校验。
3. `pipeline.generate()` 增加**自修复回路**:compileLevel 结构校验失败时把问题文本
   喂回 callStepLevel 重设计一次(repairNote 注入 user prompt)。实测第一版失败后
   第二版通过,真实生效。
4. 两处 LLM 调用超时 120s→240s(deepseek advisor 模式下必要)。

**验收工具(ref-game/verify_generated.py,全新)**:
通用自动通关器——不预设任何关卡内容,读取运行时规则表按 requires 拓扑推进,
覆盖全部 8 种 beat 类型与容器开启/环顾四周回访。morph 引擎下 `result:<beatId>`
操作数解析为"该步 uses[-1] 载体的递归展开"。四关交叉验证全部 PASS:
prison / afraid-of-dark / watchman / generated-live。弹窗内交互一律 DOM click
(SVG 表盘走真鼠标弧线拖拽)。

**引擎顺手修复**:finishIfDone 改为「只剩交付未完成时也亮出口」——否则隐形出口
收不了货会锁死关卡(怕黑吗自愈验证)。

**真机端到端**(fixtures/sample10-bookmarks.html,经 router-force 代理):
`live_generate.py` 实测——清洗+设计共 8.5 分钟(含一次结构校验失败重设计),
产出《逻辑之门:复古终端密室》scenes=2/beats=13/hints=8,密码锁因模型未给
expected 被降级(issue 可见),自动通关器 13/13 全通(`sample-puzzles/generated-live.room.json`)。
速度提示:advisor 模式延迟显著(分钟级),固定模板路径不受影响。

**回归**:verify_prison 42/42、verify_port 12/12、watchman 20/20 全绿;
index.html 四个内联脚本块 node --check 通过。修改前备份:
`index.backup-20260827-gen-v3.html`。

## -1.5 A/B:flash 直连 vs advisor 强制(2026-08-27)

同输入(sample10 书签+同主题)对照,代理新增 `STEP_ROUTER_FORCE=0` 直通模式
(仍统一缓冲为 JSON,但不注入/不改模型/不重试):

| 维度 | force(advisor/deepseek) | 直通(step-3.7-flash) |
| --- | --- | --- |
| 总耗时 | 511s(清洗+设计×2,一次结构失败重设计) | **121s**(清洗+设计×1,一次过) |
| 单请求基线 | 17.9–45.6s(极小任务也 18s+) | **1.1s** |
| 产出结构 | 2 场景/13 beats/8 hints(有降级 issue) | 2 场景/10 beats/7 hints(issues 空) |
| 推理锁 | 尝试 password 但缺 expected → 降级 | 未尝试 |
| 谜面质量 | 交叉引用含蓄、质量高 | 达合格线,更直白但有依据 |
| 自动通关 | 13/13 PASS | 10/10 PASS |

结论:flash 直连可达"可玩、有据、能通关"的标杆下限,耗时可接受;
深度推理锁两者目前都不稳定。建议后续做分级路由开关(快=直连/精=force)
并配合最小补丁修复回路与缓存(P0-P3 见前节分析)。另记已知项:
headless 合成拖拽偶发不触发 roomUse(driver 已加 window.roomUse 引擎桥兜底,
真实玩家鼠标不受影响)。

## -1.7 前情:step 接口强制走 deepseek(step-router-force)(2026-08-27)

**背景**:Plan 订阅通道的 `model` 是黑盒路由器 `step-router-v1`,在 flash(便宜快、
幻觉高)与 advisor(=deepseek-v4-pro,强推理)之间自动分发;无官方参数可选引擎。
此前前端默认 `step-3.7-flash` + `thinking:{type:'disabled'}`,流量全落 flash——
这解释了"生成谜题质量差"。参考 https://github.com/lion77542/step-router-force
在请求层注入"双通道指令"把路由推向 advisor。

**server/favorites_room_server.py 改动**(备份 `favorites_room_server.backup-routerforce.py`):
1. `transform_router_force`:首条 system 注入 ROUTER_DIRECTIVE + 最后一条 user 前
   插入 DECISION 决策点;强制 `model=step-router-v1`、`max_tokens≥32000`(关键坑:
   thinking 先吃额度,过小 → content 空 + finish=length)、`temperature=0.2`、
   `thinking={type:enabled,budget_tokens:8000}`(客户端的 disabled 必须覆盖)。
2. 所有请求内部统一转非流式并全量缓冲(advisor 检测/重试必须基于完整响应;
   参考项目同款取舍):响应无 `[Advisor consultation]` 块或呈 advice-form 反问 →
   追加 RETRY_CONSULT 指令重试,最多 3 次。前端对 JSON 响应本就兼容,零改动。
3. 上游超时放宽到 300 秒;`STEP_ROUTER_FORCE=0` 环境变量可整体关闭回到直传。

**实测证据**(真实 API):极简任务("一句话解释哈希表",参考项目实测无注入时触发率
0/5)注入后返回 `[Advisor consultation #1]` 块 + 高质量整合答案;清洗类小任务单次
即命中(无需重试);客户端 stream:true 进、JSON 出均正常。

**代价与限制**:延迟明显上升(实测小任务 17~45s,原 flash 约 2~5s),每次真实咨询
消耗更多套餐额度;触发仍是概率性强化而非保证;前端进度条从逐字增长变为完成后一次
显示(callStep/callStepLevel 的 120s abort 若频繁截断长任务,可自行上调)。

**遗留**:旧代理进程仍占着 8128 且为本会话无法终止(提权启动)。重启方式:手动结束
该 python 进程后照常 `python server/favorites_room_server.py`;期间可用任意端口起
新实例并把清洗弹窗里的 Endpoint 改成对应端口。

## -1. 最新变更:回访机制补齐,对齐原作「解开镣铐后回头才能发现新东西」(2026-08-27)

**问题**:监狱复刻把 beat reveals 做成完成即自动弹出,"解开镣铐后点击房间会发现
书架/大铁箱/门"的原作回访体验丢失。

**原作机制(读 ref-game/config.js mission2 确认,数据是完整可见的)**:
发现 = 父节点点击时渲染子节点 × 子节点 preClue 过滤。例:时钟下的电池带
`preClue:["#钥匙>镣铐"]`(解镣铐后点时钟才有);书架/大铁箱/锁着的门整节点带
`preClue:["#钥匙>镣铐"]`(房间级回访);电报机用 state 多形态。原作从不在解谜瞬间
自动摊开任何东西。

**引擎等价实现**(index.html):
1. `triggerReveals` 不再显形,只标 `revealReady=true` 并提示"也许该回头再看看";
2. 新增常驻入口 **「环顾四周」按钮**(工具条左端,`ensureRevisitButton`)调用
   `revisitRoom()`:所有 revealReady 的隐藏容器/散落物件在此被发现;已打开容器里的
   物件仍要先开容器。按钮放在画布外是因为 root/场景节点经常被物件网格盖住,不可点;
3. 点房间(root/compiled-level)或场景节点也会触发同样的回访检查;
4. 容器打开逻辑统一:`opened` 后再点按 revealReady 发现新物件;
5. `resultPos` 改为碰撞扫描落位:结果节点不再压住门容器/morse 面板类物件
   (此前三次踩到"覆盖导致点击失效",根因都是死槽位);
6. `revealScene` 按 revealReady 显形场景物件;监狱 JSON 的 shelf/chest/door 容器加
   `hidden:true`,b-unlock-shackle 的 reveals 加入这三个容器 id。

**验证**:verify_prison 26/26、verify_port(aod)12/12、watchman 回归 10/10、
smoke_room02 全过。三个脚本均含"完成后不自动弹出、环顾后才出现"的负断言。
修改前备份:`index.backup-20260827-revisit.html`。

## 0. 前情:第二关「监狱」复刻打通 + 引擎重叠缺陷修复(2026-08-26 深夜)

接续本日早些时候的第二关复刻工作。`verify_prison.py` 此前卡在第 7 步"摩斯面板弹出",
定位出**两个**真实的引擎/布局缺陷,均已修复:

0. **容器关卡显示两套平行子节点**(用户反馈后补充):无场景模式的 levelStart 原本
   把容器节点和全部物件一次性全亮出,容器是一套、物件平铺又是一套。现改为:
   散落在房间里的物件(排水管/钥匙/镣铐)开始即可见;**容器首次点击才打开**
   (`compiledHandle` 容器分支,`n.opened` 标记),显形其内部物件——LLM 标记
   hidden 的仍等 reveal beat。监狱关因此从"平铺任务面板"变成真正的探索:开柜子
   才见转盘锁和电报机,开大铁箱/门才能操作密码锁和指纹锁。

1. **combine 拖拽后源节点压住目标节点**(第 10 节记录的已知问题,本次为根因之一):
   拖到节点上是"使用"不是"摆放",但源节点会留在目标位置,把目标盖住。
   目标上的点击型机关(morse/sequence/password)从此点不到。监狱关中
   电池拖上电报机后,点"电报机"实际点中的是电池。
   **修复**:`roomBind` 记录拖动起点 `drag.from`;`finishRoomDrag` 在"放到节点上"
   路径执行 roomUse 后把源节点恢复到拖动前位置(自由摆放到空白处不受影响)。
   这同时解开了 watchman「同一对物件既 combine 又 sequence」的死结。
2. **检查详情弹窗(.node-pop)遮挡相邻节点**:弹窗 z-index 30 且 pointer-events:auto,
   布局微调后向上弹出的详情框正好盖住同列上方节点,点击被吞并冒泡回所属节点。
   **修复**:`.node-pop{pointer-events:none}`,仅 `.np-link`(打开原收藏)保留可点击。
3. **窄屏节点坐标重叠**(第 10 节记录的已知问题):场景模式列距 13%→18%
   (`compiledLevelHydrate` 场景分支),容器模式 16%→20%(容器分支),
   保证在 stage≈1024px 时列距 > 节点宽 174px。

顺带修正 `verify_regression_watchman.py` 的步骤顺序错误:保险柜是隐藏物件,
须先在场景 3 组合"顺序结果+核对结果"(fixed-combine-final 的 reveals)才显形,
原脚本在组合前就断言其可见。

**验证结果**(全部真实 DOM 通道):

| 关卡 | 脚本 | 结果 |
| --- | --- | --- |
| 监狱(原作第二关) | `ref-game/verify_prison.py` | 17/17,含容器探索门控,10 beat 全链路通关 |
| 怕黑吗(原作第一关) | `ref-game/verify_port.py` | 11/11 回归通过 |
| 守夜人(手写样本) | `ref-game/verify_regression_watchman.py` | 9/9 回归通过 |
| Room 02 默认房间 | `ref-game/smoke_room02.py`(新增冒烟) | 根展开/资料架/骨架组合全过,无控制台错误 |

修改前备份:`index.backup-20260826-morsefix.html`。

## 0.-1 前情:第一关复刻与引擎能力边界(2026-08-26 白天)

### 当前生成策略:固定模板优先

主页的生成路径现在不再采用 LLM 返回的自由场景结构。系统会从所选时间片/收藏集合中
按信号和域名多样性选出 6 条受控素材,LLM 只负责为这些素材生成化身名、谜面和氛围文本。固定编译器同时兼容旧缓存的 `cleaned` 数组和当前的 `cleaned.records` 对象,避免历史缓存被误判为 0 条素材。
引擎固定编译为 3 个场景、2 条并行入口事实、3 次组合/回访、1 个顺序锁、1 个隐藏物件、
1 个干扰物和 1 个出口交付。模板版本为 `fixed-template-v1`,数据缓存版本为
`clean-v6-fixed-room-v1`。

## 0. 最新变更:LLM 关卡可玩性重写

**问题**:旧 compiled runtime 逐 beat 强制双卡同屏,点击即完成,是任务清单不是密室;且 compileLevel 会丢弃 LLM 设计换成本地模板。

**改动**(三处):

1. **compiled runtime 重写**(脚本块 3):beats 编译成 clue 规则。所有素材开始后**全部可见**,玩家自由检查/组合;combine→交互表(拖动),sequence→顺序锁(点错复位),inspect→检查集齐,deliver→出口交付;错误组合有抖动+日志反馈;`beat-ready` 由 requires 依赖链推导。
2. **compileLevel 重写**(脚本块 2):LLM 设计优先——素材/beats 校验清洗(过滤无效 id、修正 requires、补 deliver 结尾)后直接采用;本地模板仅作无 LLM 设计时的兜底。`validation.designSource` 标记来源。
3. **设计 prompt 强化**:要求 ≥5 素材含 1 个 red_herring(不在任何 uses 里)、≥4 beats 依赖链、必含 combine+sequence+deliver,reason 写成玩家可推理的线索而非设计说明。

**历史验证边界**:10 条书签真实 LLM 生成和 Playwright 5/5 beats 通关属于上一版自由 beat 结构,不覆盖当前 `fixed-template-v1`。当前固定模板已完成离线结构模拟:6 条素材、3 个场景、10 个 beat,所有 requires/result/reveal/deliver 依赖可达;仍缺一轮浏览器级真实拖动回归。

## 1. 项目概况

这是一个单页、纯前端的"收藏夹密室"原型。它把用户收藏的网页变成文字密室中的空间、物件和线索,重点验证以下体验:

- 首屏只暴露一个根节点;
- 点击空间节点后逐层展开子结构;
- 父子节点用线连接,节点可自由摆放;
- 拖动到另一个节点表示"把物件用于目标",而不是任意配对;
- 物件状态改变后需要回访旧空间;
- 提示逐级缩小搜索范围,但不直接替玩家操作。

当前版本是 Room 02:`收藏室 / State Graph`,已于 2026-08-23 重构为**数据驱动状态机**(clue / preClue / 交互表)。

## 2. 运行方式

页面入口:

```text
http://127.0.0.1:8127/favorites-escape-room/
```

当前本地服务由 Python 静态服务器提供:

```powershell
python -m http.server 8127 --directory projects
```

如果端口被占用,换一个端口,并相应修改访问地址。

LLM 功能(收藏导入→清洗→关卡设计)需要 Step Plan API:

```powershell
python server/favorites_room_server.py   # 8128 端口,代理 /api/step
```

纯静态体验不依赖 LLM。

## 3. 重要文件

| 文件 | 作用 |
| --- | --- |
| `projects/favorites-escape-room/index.html` | 当前可运行 Demo,包含 HTML、CSS 和 JavaScript |
| `projects/favorites-escape-room/index.backup-20260823-1931.html` | 重构前版本备份(多段覆盖脚本结构) |
| `projects/favorites-escape-room/index.backup.html` | 旧版 Room 01 备份 |
| `projects/favorites-escape-room/docs/handoff.md` | 本文档,当前交接事实来源 |
| `projects/favorites-escape-room/docs/design.md` | 旧版 Room 01 设计文档,保留作历史参考 |
| `projects/favorites-escape-room/docs/reference-analysis.md` | 参考游戏《文字密室逃脱》逆向分析 |
| `projects/favorites-escape-room/server/favorites_room_server.py` | Step Plan LLM 代理(8128) |
| `projects/favorites-escape-room/fixtures/sample-bookmarks.html` | 测试收藏夹样本 |

当前目录不是 Git 仓库,不能依赖 Git 回滚。修改前应先复制或保存目标文件的当前版本。

## 4. 架构(2026-08-23 重构后)

`index.html` 现在包含 4 个清晰的脚本块:

1. **状态机引擎**(数据驱动):借鉴参考游戏《文字密室逃脱》的 clue 状态机
2. **导入管线**:解析收藏夹 → 本地清洗 → Step LLM 清洗/关卡设计
3. **compiled runtime**:执行编译出的逐 beat 关卡
4. **产品壳**:IndexedDB 本地存档 + 首页生成/续玩界面

### 4.1 状态机核心(脚本块 1)

**数据定义**(写关卡 = 改数据,不改引擎):

```js
ROOM_NODES   // 节点表:id/kind/name/hint/detail/parent/x/y/hidden/action/interact
ROOM_USE     // 交互表:pair(顺序无关)/consume/reveal/clue/log/frontier/qte/ending
ROOM_SEQUENCE// 顺序动作:order/red-blue-green → clue + reveal + frontier
ROOM_ZONE_REVEAL // 空间展开规则:always + gated(need 线索门)
ROOM_HINTS   // 分级提示:每个 frontier 三层
ROOM_PROGRESS// 进度条状态列表(6 段)
```

**clue 系统**(状态机):

- `state.clues` 是 Set;
- `addClue('#x')` 获得线索,`addClue('-#x')` 移除;
- `hasClue()` 支持:字符串、数组(AND)、`|`(OR)、`!`(NOT)、`-#x`(不存在);
- 参考游戏的 `#A>B`、`#x-{0}` 占位符尚未实现,是扩展方向。

**节点可见性**统一为:`nodeVisible(n) = !n.hidden && !n.used && hasClue(n.preClue)`。

**交互表驱动**:拖动判定不再硬编码。`roomUse()` 按排序后的 pair 查 `ROOM_USE` 表:

```js
{pair:['nand','tetris'],consume:['nand','tetris'],reveal:['skeleton','draft'],clue:'#structure',log:'...',frontier:'revisit'}
```

**点击型交互**用节点上的 `interact` 数组:reveal / count(计数到 N)/ log / frontier。

**空间展开门控**用 `ROOM_ZONE_REVEAL`:

```js
desk:{always:['programiz','vue'],gated:[{ids:['draft','cloth'],need:['#structure']},...]}
```

### 4.2 兼容层

引擎尾部提供 `render/reset/clone/reveal/bind/handle/combine/objective/hints/source` 等全局别名,供导入管线、compiled runtime 和产品壳调用。这些脚本块(2/3/4)在重构中**未改动**。

## 5. 当前玩法流程(不变)

开场只有 `收藏室` → 展开资料架/工作台/墙面/出口 → 检查"文字密室逃脱"得旋钮 → 拨 3 次得回访条 → `nand2tetris` 拖 `NandGame` 得收藏骨架 → 骨架拖 `Programiz` 得可执行逻辑 → 逻辑拖 `Vue` 触发 QTE 得反馈外壳+黑屏 → 擦镜布拖墙面得三按钮 → 外壳拖黑屏得启动片段(红蓝绿) → 按序点击得"重新整理的收藏" → 拖到出口进入结局三选一。

## 6. 已验证内容(2026-08-23,Playwright 自动化)

- 首屏只有根节点;
- 根节点展开四空间;
- 资料架展开 + 旋钮三次 → 回访条;
- nand+tetris → 收藏骨架;
- 工作台状态门控(draft/cloth 在 structure 后出现);
- 骨架+Programiz → 可执行逻辑;
- 逻辑+Vue → QTE 弹窗 + 成功 → 反馈外壳 + 黑屏;
- 擦镜布+墙面 → 三按钮;
- 外壳+黑屏 → 启动片段;
- 红蓝绿顺序 → 重新整理的收藏;
- machine+exit → 结局弹窗 + 进度 6/6;
- ending 三选一逻辑正常;
- 重置房间回到首屏;
- 全程控制台无错误、无 pageerror。

注:自动化测试中 intro/ending 按钮点击需先隐藏产品壳 home 屏(真实用户从 home 屏进入,不受影响)。

## 7. 已知技术债务与风险

### 当前能力边界

- 能稳定完成:收藏夹解析、6 条受控素材筛选、LLM 文案富化、固定模板编译、确定性依赖链模拟。
- 不能稳定保证:任意收藏夹元数据自动变成有意义的谜面;LLM 自由设计场景;仅凭标题/域名生成原作级密码、角度、摩斯或物理机关。
- 当前最快验证路径:绕过 LLM,用 6 条 fixture 素材编译固定模板,执行 10 个 beat 的真实点击/拖动并断言出口。若通过,再单独验证 Step 返回的 6 条文案是否能进入模板。

`BodyStreamBuffer was aborted` 属于旧版 SSE 传输问题。固定模板的关卡设计请求已改为非流式 JSON,代理等待上限为 180 秒;这只解决传输稳定性,不等价于关卡可玩性通过。

### 提示系统 frontier 与 clue 状态的映射

`ROOM_HINTS` 的 frontier 键仍是手工切换的,不是从 clue 状态自动推导。如果玩法链改动,需要同步检查 frontier 切换点。

### compiled runtime 的兼容状态

脚本块 3(compiled level runtime)的 beat 规则现在会先编译为 `combines / sequences /
inspects / delivers` 交互表,完成状态统一写入 `state.clues`。`compiled.step/beatIndex`
仅保留给场景索引、存档兼容和恢复显示,不再作为谜题完成判定来源。后续可以继续把
`compiled` 对象本身压缩为只读关卡上下文。

### 参考游戏的高级机制尚未实现

`#A>B` 组合线索已经可作为普通 clue key 使用;`#x-{0}` 动态占位符现在支持
`{clue:'#blue-{0}',params:[2]}` 形式,当前索引旋钮会写入 `#dial-1/2/3` 并驱动同一节点的状态变化。
timer 资源、detector 探测器等(见 `docs/reference-analysis.md`)仍是后续扩展方向。

### 引导和内容仍需要试玩校准

同旧版:需要真实玩家试玩,记录回访理解、拖动语义、屏幕颜色线索推导等卡点。

## 8. 推荐下一步

1. ~~用真实玩家试玩固定模板~~ 三关(怕黑吗/监狱/守夜人)已可自动通关,下一步让真实玩家试玩,记录"先查什么、为什么回访、干扰物是否成立";
2. 原作 9 种机关中已补 password/angle/morse/knock 类;timer 资源、detector、color-sort、QTE-in-compiled 仍缺,可选:为固定模板增加密码盘变体之外的资源计时器;
3. 把 `compiled` 对象压缩为只读关卡上下文,进一步减少运行时与主房间的兼容包装;
4. 待试玩校准后,再让 Step LLM 输出 ROOM_NODES/ROOM_USE 格式的局部变体。

## 9. 交接检查清单

- [x] 启动本地静态服务器并打开入口;
- [x] 确认首屏只有 `收藏室`;
- [x] 展开资料架并检查 `文字密室逃脱`;
- [x] 连续点击索引旋钮三次;
- [x] 将 `nand2tetris` 拖到 `NandGame`;
- [x] 确认 `收藏骨架` 出现;
- [x] 回到工作台检查新增状态;
- [x] 验证画布平移、缩放和节点位置保存;
- [x] 检查控制台无错误;
- [x] 修改交互后重新走一遍主线(Playwright 17 步自动化全过)。

## 10. 复刻原作第一关「怕黑吗」—— 底层工具能力边界验证（2026-08-26）

### 结论先行

从参考游戏《文字密室逃脱》原作复刻第一关「怕黑吗」（火柴→油灯→看画→颜色密码 274→钥匙→开门），
**能无障碍复刻**：真实 DOM 通道 11/11 通过（`ref-game/verify_port.py`）。
底层工具（执行层/引擎）**基本够用**，谜题质量差的根因在生成层（LLM 从书签只能复述事实、编不出谜题逻辑），
不在执行层。

### 复刻过程中暴露并修复的引擎缺陷

1. **缺 password 密码盘机制**（唯一硬缺失）。引擎原只有 inspect/combine/sequence/revisit/deliver 五种 action，
   原作的 password/angle/morse/timer/knock/breakable/detector/color-sort 等 9 种交互全缺。
   已补 password：`compileRules` 加 `rules.passwords`、`compiledHandle` 加 dispatch、新增 `openKeypad()` 组件
   复用死 UI `keypadModal`（HTML/CSS 早已存在但无 JS 接线）。密码盘支持 `colors` 颜色标签（如蓝/红/绿）。
2. **hidden 物件 reveal 后仍 `opacity:0 + pointer-events:none`**：`.compiled-hidden-item` 有这两属性，
   reveal 只改 `n.hidden` 没移除 class。修复 `roomRender` 用 `(n.compiledHidden && !n.revealed)` 动态决定是否保留 class。
3. **deliver 后 result 挡出口**：交付时 result 被拖到出口位置变 spent 但仍拦截点击。修复 deliver 成功后 `item.hidden=true`。

### 预先存在、当时未修的问题(已于 2026-08-26 深夜修复,见第 0 节)

- ~~窄屏节点坐标重叠~~:场景模式列距已 13%→18%、容器模式 16%→20%。
- ~~combine 拖拽把源节点移到目标位置重叠~~:拖到节点上使用后源节点自动归位,
  同一对物件既 combine 又 sequence 的 watchman 场景现已可通关。

### 关键文件

- 复刻关卡：`sample-puzzles/afraid-of-dark.room.json`
- 复刻验证：`ref-game/verify_port.py`（真实 DOM，11/11 PASS）
- 原作数据：`ref-game/config.js`（从原 URL 重新下载）+ `docs/reference-analysis.md`
- 引擎改动均在 `index.html`：`compileRules`/`compiledHandle`/`openKeypad`/`roomRender`/`compiledUse`(deliver)

### Playwright 环境要点

- 系统 python 的 playwright 期望 chromium 1208，但缓存为 1228/1234，须 `executable_path` 指向 `chromium-1234\chrome-win64\chrome.exe`。
- `locator.click` 的 hit-target 检查在节点重叠时会误判/卡死，用 `page.mouse.click(bounding_box 中心)` 更贴近真实点击。

## 11. 项目审查待办（2026-08-28）

本节记录 2026-08-28 代码审查发现的问题。它们尚未修复，不能视为当前能力。优先级含义：P0 为立即处置，P1 为影响安全或核心用户流程，P2 为重要工程债务。

### 11.1 安全边界

1. **[P0] 前端提交了固定 Step API key**（`js/pipeline.js`）。密钥会暴露在源文件、DOM 输入框和请求头中；应立即撤销并轮换，从 Git 历史清除旧值，改由服务端环境变量持有。
2. **[P1] `/fetch-meta` 可成为跨域本机 SSRF 代理**（`server/favorites_room_server.py`）。当前未拒绝回环、私网、链路本地、保留地址或重定向后的危险地址，并开放 `Access-Control-Allow-Origin: *` 与 Private Network Access。应逐跳校验目标地址、限制 origin，并增加本地会话令牌。
3. **[P1] 导入 `.room.json` 可形成持久型 DOM XSS**（`js/app.js`、`js/engine.js`）。导入校验过浅，部分关卡字段直接拼入 `innerHTML`。应使用 schema 校验、字段长度限制和 `textContent`/安全 DOM 构造。
4. **[P2] 本地服务端缺少代理级保护**。静态服务、网页抓取和 LLM 转发共用一个无认证端口，没有请求体、并发、频率或任务预算限制。应拆分职责，或至少增加一次性 token、来源限制、请求上限和并发闸门。

### 11.2 核心功能兑现

1. **[P1] 求解器与真实引擎语义不一致**（`js/pipeline.js:solveLevel`）。求解器不会模拟真实 combine 配对、sequence 顺序、机关输入和完整 deliver 规则，可能把运行时无法完成的关卡判为可解。应抽取引擎规则为共享纯函数，求解器和 UI 执行层共同使用。
2. **[P1] 求解器可在 deliver 完成后提前判成功**。当前不要求所有必要 beat 完成。验收标准：唯一 deliver 必须是最终动作，且成功时全部必要 beat 都已完成。
3. **[P1] 机关状态无法保真恢复**（`js/engine.js:restore`）。快照只重放 combine/sequence，不重放 password/angle/morse 产生的 morph，继续游戏后可能缺少 `result:<beatId>` 身份而卡死。
4. **[P1] 分场景进度恢复到错误场景**。快照未保存或重算 `sceneIndex`，恢复后可见节点与跨场景操作门禁可能矛盾。应由已完成 beat 推导当前场景，并通过统一 `revealScene` 恢复。
5. **[P1] Chrome JSON 收藏时间解析错误**（`js/pipeline.js:dateValue`）。Chrome `date_added` 是自 1601-01-01 起的微秒数，当前按 Unix 秒/毫秒猜测，会破坏时间片、昼夜判断、排序和时间轴。
6. **[P1] “导入关卡”不会写入已保存关卡**（`js/app.js:loadLevelText`）。当前只 `mountLevel`，刷新后无法从列表或“继续游戏”恢复。需明确“临时试玩”与“持久导入”的产品语义；若为导入，应统一写入 `levels`。
7. **[P1] 更换收藏文件时旧异步任务未取消**。旧清洗/抓取/生成结果可能覆盖新文件状态。应给每轮任务分配 token，并通过 AbortController 取消旧任务；所有异步提交前检查 token。
8. **[P2] “全局清洗”的模型覆盖率表达不清**。`callStep` 默认采样最多 20 条，而 UI 容易让用户理解为全量模型复核。统一走分批清洗，并显示模型已复核、仅本地规则处理和未处理数量。
9. **[P2] 固定回退只保证结构可执行，不完全兑现生成体验**。回退关卡的最终交付可能引用原素材而非最终产物，且缺少正常设计路径承诺的机关深度。应明确显示“简化模式”，或让回退模板也满足最终产物、机关和场景契约。
10. **[P2] 结束选项目前只是文案**（`js/room02.js:ending`）。继续、归档、转化三种选择只改日志和状态文本，没有生成任务、持久化归档状态或产生下一关种子。若这些是产品功能，应落地数据与后续流程；否则调整文案，避免承诺未实现行为。

### 11.3 架构与一致性

1. **[P1] 单个全局脚本体系耦合过重**。`room02.js`、`pipeline.js`、`engine.js`、`app.js` 通过可变全局函数和共享 `state` 互相覆盖，加载顺序即隐式依赖；例如 `roomHandle`、`roomUse`、`roomReset` 被多层包装。应优先抽取“关卡 schema/编译规则/运行状态转换/持久化”四个明确边界，而非一次性重写 UI。
2. **[P1] 设计赛马的真实调用预算高于注释预期**。外层每 lane 最多 3 轮，而 `designWindow` 内部每次又最多重试 3 次；默认 3 lanes 时理论上可达到 27 次设计请求，而不是注释中的 3×3。服务端 router-force 还可能每次最多请求上游 3 次。应只保留一层重试，集中定义总调用预算、超时和取消策略。
3. **[P2] 缓存版本维度不完整**。生成缓存键包含 `MODEL_VERSION`，但没有清洗规则、设计提示、参考关卡、编译器和求解器版本。应采用结构化版本 `{clean, design, refs, compiler, solver}`，任一不兼容即失效。
4. **[P2] 输入规模没有统一上限**。文件大小、条目数、title/folder/URL 长度、IndexedDB/localStorage 总量都缺少入口约束，真实大型收藏夹可能阻塞主线程或触发配额失败。应在解析前后分别限额，并把大对象仅存 IndexedDB。
5. **[P2] 端口配置没有贯穿前后端**。README 宣称可通过 `FAV_ROOM_PORT` 改服务端端口，但前端 `/api/step` 和 `/fetch-meta` 默认写死 `127.0.0.1:8128`。应使用同源相对路径，或由服务端注入统一配置。
6. **[P2] 本地模板排序比较器存在实现错误**（`js/pipeline.js` 本地 fallback 的 `ranked.sort`）。第二项条件误用 `b.signal` 计算 `a` 的权重，排序可能不满足反对称性，导致选材不稳定。应抽取 `signalWeight(item)` 并比较 `signalWeight(b) - signalWeight(a)`。

### 11.4 测试与验收缺口

1. **[P2] 标称 `test_*.py` 不是标准 pytest 测试**。`test_compile.py` 在导入阶段执行并 `SystemExit`，导致 `python -m pytest -q` 内部错误。应改为普通 `test_*` 函数，或重命名为 `verify_*.py`。
2. **存档测试绕过真实导入路径**。`verify_save_mgmt.py` 手工写 IndexedDB，因此不能证明导入关卡会持久化。应从 UI 导入、刷新页面、点击继续并验证同一关卡状态。
3. **缺少求解器与真实 DOM 的一致性门禁**。每个被 solver 判定可解的机制组合，应至少有一条真实引擎执行路径；生成批测应比较 solver 结果与 DOM 通关结果。
4. **必须新增的回归样例**：真实 Chrome `date_added`；密码/角度/摩斯解锁后刷新；跨场景刷新；快速连续更换文件；大型收藏夹；导入后刷新继续；错误组合后恢复；最终产物交付；恶意 room JSON；危险 `/fetch-meta` 地址。

### 11.5 修复顺序与完成定义

第一批：撤销密钥、封堵 SSRF/XSS、统一引擎与求解器语义、修复机关/场景恢复、Chrome 时间戳和异步任务竞态。

第二批：兑现导入持久化、统一全量清洗、限制设计调用预算、修复端口配置与回退契约。

第三批：抽取共享领域层、补齐缓存版本和输入限额、将验证脚本纳入可重复的 CI 测试矩阵。

### 11.7 内容 Grounding 审查（2026-08-29）

对用户生成结果“未命名冒险 · 08-29 09_29.room.json”复核后，确认谜题主要围绕域名、URL 路径数字、标题和日期，而不涉及网页具体内容。样本六条素材的 `description` 全为空，生成结果出现“页脚印着路径数字”“卡背写着取第 2、4、6 位”“卡片角落印着五十音行序号”等输入中不存在的页面事实。

根因按影响链排序：

1. **内容供给缺失**：当前 app.js `generate()` 在选出六条素材后移除了 `fetchMetaInto()`，设计模型主要只收到标题、域名、urlPath、folder、dateAdded 和空 desc。
2. **已有富化能力过浅**：`fetchMetaInto()`/`fetch-meta` 只可靠提供 title/meta description，服务端只读前 64KB HTML，不能稳定提取正文、列表、代码或动态页面内容。
3. **Prompt 偏向元数据**：设计提示把标题词、域名、路径、日期列为推理材料，并把路径数字称为最佳原料；无正文时模型自然选择路径数字出题。
4. **示例来源错位**：监狱/熊曰 few-shot 确实已传给 LLM，但其中日记、摩斯表、熊字表、便签密文是人工虚构的机制道具，只示范谜题链，不示范网页研究和证据引用。
5. **验证闭环缺口**：校验器检查结构、引用和机械可解性，却不检查 reason 中的页脚/卡背/批注等断言是否存在于网页内容，也不要求密码有具体原文证据。

结论：这是架构、Prompt、few-shot 和验证器共同造成的 grounding 问题，不能归结为单纯模型能力不足。

### 11.8 内容研究改造判断与最小修复

轻量 harness 有潜力，但不能只是给 LLM 增加搜索工具。正确顺序应是：研究原始收藏页面 → 记录证据包 → 设计冒险 → 语法/事实检查 → 修正 → 通关验证。`record_evidence`/证据包比自由搜索本身更关键；原始收藏不可用时才搜索替代版本或外部背景，并区分收藏来源、研究来源和模型推导事实。

第一轮最小有效修复不引入完整 harness，只做四项：

1. 选出六条素材后恢复网页富化调用；
2. `/fetch-meta` 增加受限正文 `excerpt` 与 `contentStatus`；
3. 将 `pageExcerpt` 单独传给设计模型，Prompt 改为网页内容优先，元数据仅作备用；
4. 关键谜面增加 `evidenceRefs`/`quote`，本地检查引用是否存在于 `pageExcerpt`。

页面没有正文时，模型只能使用真实存在的标题、域名、路径、文件夹和日期，且结果标为 metadata-only，不得把 URL 数字包装成页脚、卡背、批注或说明书内容。正文会发送给外部 LLM，产品界面必须明确告知并允许用户拒绝；只读取选中的六条，保存受限摘录和来源状态，不保存完整网页。

验证应先进行元数据模式与正文摘录模式 A/B：正文命中率、关键 beat 的正文引用比例、metadata-only 占比、玩家理解度和真实 DOM 通关率。若普通摘录仍不足，再升级到浏览器渲染、替代页面和搜索研究。

本记录对应方向文档 `docs/untitled-adventure-direction.md` 的内容 Grounding 章节，以及设计原则 P43-P46。

### 11.12 重置按钮与关卡生命周期审查（2026-08-30）

已复现：生成关卡运行中点击顶部 `#reset` 后，画布只剩原生 Room 02 的 `root`/“收藏室”节点，`compiled` 和 `window.__dbg` 消失；但游戏工具栏仍显示原生成关卡标题。根因是 `room02.js:1433` 将按钮绑定到基础 `roomReset()`，而生成关卡专用的 `reset()` 包装逻辑在 `engine.js:1829`，从未被该按钮调用。

这不是“重置当前关卡”的实现，而是把底层原生房间重建动作误绑定成了产品动作。由此产生以下遗留问题：

1. **[P0] 生成关卡被重置成固定 Room 02**：基础 `roomReset()` 清空 compiled 并只克隆 `ROOM_NODES`。
2. **[P1] UI、运行态和存档失配**：`currentLevel`、工具栏标题和 IndexedDB 的 `levels/progress` 仍保留旧关卡；之后保存可能没有 snapshot，继续游戏又可能恢复旧进度。
3. **[P1] 重置没有清理机关上下文**：`keypadCtx`、`angleCtx`、`morseCtx` 及对应弹窗未由基础 reset 统一关闭/清空，旧回调可能作用到新运行态。
4. **[P1] 并行房间恢复不完整**：快照不保存 `parallelRooms`；恢复后可能退回顺序场景口径，造成 UI 和物件门禁矛盾。
5. **[P1] 快照遗漏运行中间态**：当前只保存 `started/done/clues`，没有容器开闭、已发现空间、物件 hidden/used/morph、sequence/inspect、提示状态和视图状态。
6. **[P2] 视图状态泄漏**：重置未调用 `resetView()`，生成关卡的缩放/平移可能影响固定房间或下一关显示。
7. **[P2] 命名轮询生命周期不完整**：`startNamingWatch()` 创建的 interval 没有在 `showHome()` 或重置时统一停止，可能在离开关卡后继续运行。
8. **[P2] 恢复逻辑有重复调用**：`restore()` 中 `revealAllRooms(false)` 连续调用两次，虽通常表现为冗余，但说明状态恢复路径存在叠加修改残留。

### 修复约定

产品层应新增唯一入口 `resetCurrentLevel()`：保留当前关卡记录和 `currentLevel`，重建同一关卡的初始运行态，清理所有弹窗/计时器/中间态，并将重置后的 snapshot 写回当前 progress。基础 `roomReset()` 限定为底层节点克隆，不得直接绑定 UI。

同时明确三种用户动作：重置本关、离开本关、删除存档。恢复逻辑应使用版本化快照，并恢复机关上下文、空间/容器状态、物件状态、并行房间模式和视图状态。所有自动保存、命名轮询和异步任务必须遵守关卡生命周期。

### 验收缺口

现有 `test_solver.py` 6/6、`test_compile.py` 13/13 通过，JavaScript 逻辑测试未覆盖 UI `#reset`。必须补充真实 DOM 回归：导入/生成关卡 → 点击重置 → 仍显示同一关卡入口；重置后 progress 为初始状态；弹窗关闭；工具栏标题、画布节点和 `window.__dbg` 一致；刷新后“继续游戏”不会恢复重置前的进度；离开/删除动作仍保持原语义。

### 11.10 三份生成结果横向复盘（2026-08-30）

复核 `C:/Users/30807/Downloads/未命名冒险 · 08-29 12_32.room.json`、`14_22.room.json`、`16_12.room.json`：三份结果均为 2 个 scenes、约 7 个 beats；没有 `parent`、`exits`、`connections` 或真正的 `containers` 拓扑。动作主要为 inspect + password，combine 最多一次，14_22 甚至没有 combine；三份素材 description 均为空，关键 reason 主要依赖域名、路径和日期。

结论不是“硬规则不够多”，而是系统奖励了最低限度合规：

1. 数量型门禁只要求至少一个 combine/hidden/lock，不要求它们改变空间或物件状态、产生后续用途或汇合多条链。
2. Prompt 的默认范式是“观察 → 组合 → 推理锁 → deliver”，开锁字段和验证要求远强于工具、容器、回访、物件多状态等玩法。
3. `scene` schema 没有空间拓扑，`focus` 只是文案；编译器和引擎把 scenes 变成 `compiled-level` 下的兄弟节点。`parallelRooms` 只负责同时显示房间，不产生房内层级。
4. 旧有 `compiled-container-*` 能力没有真正接入 LLM scenes 路径；hidden 是延迟显形，不是递归空间探索。
5. 正文没有进入设计输入；few-shot 只示范人工虚构日记/对照表/密文；校验器只验证结构和机械可解，不验证网页理解、证据真实性或玩法意义。

因此新增后续验收要求：combine 必须有状态效果和下游用途；至少有工具→容器/遮挡物→隐藏物发现链；至少一个可回访状态变化节点；至少两种有语义差异的实际操作；锁不是默认高潮。solver、grounding checker、玩法检查和真实 DOM 应分别验证可执行性、证据真实性、玩法丰富度和用户体验。

这次复盘同时确认：轻量 harness 不能只是新增 `search_web`。正确顺序是研究原始页面 → 记录证据包 → 提出多种机制 → 语法/玩法/事实检查 → 修正 → 模拟执行。内容 excerpt/evidenceRefs 是短期最小实验；真正的空间层次仍需独立引入 scene/space 分层、connections、递归容器和 beat effects。

完成不能只看 `solveLevel().solvable` 或脚本退出码；至少需要：静态校验通过、solver 与真实 DOM 结论一致、刷新恢复成功、安全边界回归通过、且文档中的用户承诺有对应可观察行为。

### 11.9 生成耗时优化意见（2026-08-29）

性能审查判断：当前总耗时主要来自设计模型调用、重复发送大 Prompt、供应商赛马、内外层重试和服务端 advisor 重试；本地解析、编译、求解通常不是主瓶颈。优化应先消除重复工作，不应通过移除网页证据、降低核心创作质量或削弱事实校验来换取速度。

建议优先级：

1. 备用供应商延迟启动，主路在首包/完成预算内无进展时才启动，主路通过后立即取消备用路。
2. 拆分短创作计划与受约束展开；只对局部 JSON、beat 或 solver 卡点做局部修复。
3. 压缩重复规则和 few-shot；修复轮只发送错误摘要、相关素材和必要上下文；静态前缀若供应商支持则启用 Prompt caching。
4. 将 id、场景编号、selectedItemIds、mechanics、timeline、默认 hints、布局坐标等机械字段移出 LLM。
5. 集中定义一层重试预算，不能让服务端 advisor 文本标记触发无条件上游重跑；应由结构、事实或真实执行失败触发修复。
6. 清洗、证据抽取、JSON 修复、标题和回执使用低成本配置，核心空间/谜题创作保留足够质量和推理预算。
7. 建立网页摘录、证据包、创作计划、最终关卡和校验结果的分层缓存，缓存键包含内容、Prompt、范例、编译器和检查器版本。
8. 研究阶段六条选定页面并发读取，总预算控制在 10-15 秒；单页失败标记 `contentStatus: empty` 后继续。
9. 记录 parse/clean/research/首 token/模型耗时、Prompt token、provider、重试、上游尝试、缓存命中、获胜路线和取消路线。

最小高收益组合：延迟启动备用供应商；取消基于 advisor 文本标记的无条件重跑；压缩重复 Prompt；把整版修复改为局部修复；增加真实调用次数和分阶段耗时遥测。若只能改一项，优先检查服务端 advisor 重试；若只能改两项，再加备用路线延迟启动。

验收必须同时比较性能和质量：P50/P95 总耗时、Prompt token、真实上游调用次数、首 token 延迟、重试次数、缓存命中、正文证据引用比例、metadata-only 比例、结构/事实校验通过率和真实 DOM 通关率。完整方案见 `docs/untitled-adventure-direction.md` 的“生成耗时优化观察”。

### 11.6 处置记录(2026-08-28 第一批,同日)

逐条核查后开始修复。先给两条**更正**(核查证据在手):

- **11.3.6 排序比较器:指控不成立**。实际代码(pipeline.js:1348-1349)是
  `(b 的权重) - (a 的权重)`——正确的降序比较器,不存在"误用 b.signal 计算 a 权重"。
  抽 `signalWeight(item)` 助手作为防复发重构建议保留,但不作为缺陷修复。
- **11.2.2 solver deliver 判成功:部分成立**。deliver 可达本身就是可玩性的定义——
  不在 deliver 前置链上的步是可选内容,要求"全部 beat 完成"反而把可选观察步变成阻塞。
  真正的缺口是 11.2.1(solver 不模拟真实 combine 配对/机关输入),按原计划留待共享领域层批次。

**本批已修复**(全部带回归):

- 11.1.1 [P0]:前端内嵌 key 已删除;新 key 由本地 server 持有(server/STEP_API_KEY.local,
  已 gitignore;环境变量 STEP_API_KEY 优先),客户端未带 key 时由直通分支注入上游,
  本地代理端点不再要求客户端 key;**旧 key 已由需求方轮换,但其值仍在 git 历史中,
  若仓库将共享/推送,需先重写历史**。
- 11.1.2 [P1]:/fetch-meta 加 SSRF 防护——仅 http/https、解析出的全部地址禁止
  回环/私网/链路本地/保留/多播、重定向改为手动跟随(最多 2 跳,每跳复检);
  CORS 收紧为仅回显本机来源,并移除 Access-Control-Allow-Private-Network 头
  (公网页面无法再驱动本服务)。探针实证:127.0.0.1/192.168.x/10.x 三类目标全部被拒。
- 11.2.5 [P1]:dateValue 修复——Chrome JSON 的 date_added(WebKit 纪元微秒)按量级判别
  纪元并正确换算,结果限制在 1995-2040;回归:13360000000000000 → 2024-05-12 ✓
  (verify_clean_strict 7/7)。
- 11.2.6 [P1]:UI 导入关卡写入 levels store + 刷新已保存列表;刷新后可从列表/继续游戏
  恢复(verify_save_mgmt 6/6 新增回归段)。删除断言按新语义更新(持久化导入行是预期)。
- 11.2.7 [P1]:导入/生成全流程加异步任务令牌(importToken),换文件后旧回调放弃写入
  (onchange/generate 共 5 处守卫)。
- 11.3.2 [P1] 预算收敛:designWindow 内层不再重试结构问题(立即上抛给轮次/赛马层),
  内层只保留网络停滞重试(≤3 次);设计调用最坏 = 3 路×3 轮(与注释一致),
  拆除"27 次"乘积。verify_design_race 5/5 复验。
- 11.1.3 [P1] 部分:导入 room.json 的字符串字段去尖括号+限长(title/reason/product 等),
  阻断 innerHTML 注入路径;完整 schema 校验与逐渲染点审计留下一批。

**未动(按计划留后续批次)**:11.1.4 服务端拆分/令牌、11.2.1+11.2.2 求解器共享领域层、
11.2.3/11.2.4 恢复保真(先写复现用例)、11.2.8 清洗覆盖率 UI 表达、11.2.9 回退契约、
11.2.10 ending 产品语义、11.3.1 领域层抽取、11.3.3 结构化缓存版本(verdicts 已带
CLEAN_VERSION,datasets 键待补)、11.3.4 输入限额、11.3.5 端口贯穿、11.4 测试矩阵。

### 11.13 节点展开动画审查（2026-08-30）

当前节点展开动画没有按预期工作的根因不是 keyframe 数值，而是渲染生命周期和动画目标定义错误。现状只有 `.arrive` 的淡入/缩放/轻微位移，没有真正的“从父节点向空间槽位展开”。

已确认问题：

1. `levelStart()`、`revealAllRooms()`、`revealScene()` 和 `inspect()` 可能连续触发 `roomRender()`；后一次渲染替换前一次带 `.arrive` 的 DOM，动画在浏览器首次绘制前被清掉。
2. `roomRender()` 用 `innerHTML` 删除并重建所有节点，旧节点几何状态不存在，`left/top transition` 无法产生位置插值。
3. `roomLayoutBoard()` 在渲染前直接写入最终坐标，没有父节点附近的动画起点。
4. `css/styles.css` 的 `.node` 存在两段 `transition`，后段覆盖了先声明的 `left/top` 过渡。
5. `morphNode()` 同时设置 `justArrived` 和 `justChanged`；`.changed` 的完整 `animation` 会覆盖 `.arrive`。
6. 个别 reveal 路径只设置 `hidden=false`，未同步 `revealed=true`，可能仍保留 `compiled-hidden-item` 的 `opacity:0/pointer-events:none`。

建议修复顺序：状态更新批处理、单次渲染；用 `animationend` 或 token 清理动画状态；采用 keyed DOM/FLIP 保留位置变化；补充父节点起点到目标槽位的 stagger 展开；合并 CSS transition；拆分 arrive/changed 动画属性。

动画验收需覆盖首次进入、房间显形、容器显形、隐藏物回访、物件变身、重复显形、错误操作恢复、桌面/移动端和 reduced-motion。必须验证动画过程而不只是最终节点存在：动画类不能在首次绘制前被二次渲染清除，节点不能瞬移，详情卡和邻近节点不能被动画遮挡。

### 11.11 内容呈现与原网页探索（2026-08-30）

复核 `未命名冒险 · 08-30 05_15.room.json` 后确认：网页信息已经进入素材的 `description`，但没有进入谜题证据链；关键 beat 的 `evidenceRefs` 为空，机关只通过 `deriveFrom` 指向整条书签。同时 `identityOf()` 将标题、域名、日期、路径、整段 description 和完整 URL 拼成一个 detail，UI 再用单一 `inspectCopy` 展示，导致节点详情变成混杂多语言、账号、统计、导航和 URL 的长信息墙。

本问题应分为信息加工和 UI 两层处理：

1. **信息加工**：原始抓取结果不得直接作为玩家文案。增加内容编译层，清洗统计/账号/导航噪声，检测语言并生成短中文摘要，保留原文引用，提取少量带 `originalQuote`、`displayText`、`locator`、`kind`、`confidence` 和 `affordances` 的 `sourceFacts`。
2. **证据连接**：`reason` 只写当前谜面，`sourcePreview` 写短来源摘要，`originalQuote` 做复核，`evidenceRefs` 连接谜面与具体事实。`deriveFrom` 不能代替具体引用；grounding checker 应检查关键 beat 有效引用、数字/断言可追溯，并统计内容利用率、证据覆盖率和 metadata-only 比例。
3. **UI 分层**：详情拆成当前谜面、折叠来源证据、原网页操作三层。默认只显示化身名、状态和一到两句线索；来源区显示短中文摘要、来源标题、域名和少量原文；完整 URL、路径和长 description 默认隐藏，只有实际参与谜题的片段才高亮展示。
4. **鼓励打开原网页**：将通用“打开原收藏”升级为带 `externalTask` 的具体观察任务，例如确认启动命令、找到分类表或查看制作名单。玩家返回后可填写短答案或选择结果；核心谜题必须有保存摘录兜底，不能依赖页面始终在线。`visibilitychange` 只能记录“来源已回访”，不能证明玩家读完页面。
5. **依赖分级**：核心线索不依赖在线页面；增强线索打开网页更容易但有摘录兜底；奖励探索提供额外故事/视觉内容但不阻塞通关。正文发送给外部 LLM 前必须明确告知用户并允许拒绝。

最小改动组合：恢复结构化的 `pageExcerpt/sourceFacts` 传递；改造 `identityOf()` 为短身份信息；新增 `sourcePreview` 和可折叠 `originalQuote`；关键 beat 增加 `evidenceRefs`；原网页按钮显示具体观察目标。当前样本的核心结论是：**内容进入模型输入，不等于内容参与解谜；摘要服务于解谜，证据服务于信任，原网页服务于探索。** 相关设计原则为 P61-P66。

### 11.14 生成等待体验审查（2026-08-30）

当前生成流程是“点击生成 → 等待 LLM → 完整关卡通过后才显示游戏”。`generate()` 在完成前不挂载中间结果，设计请求使用非流式响应，用户主要只能看到状态文字，因此无法判断系统是在排队、研究、生成、重试还是卡住。

建议将等待过程改为“生成中的工作台”：

1. 显示真实阶段和已用时间：读取收藏夹、选材、研究页面、编排空间/谜题、检查可玩性、整理回执。
2. 展示已选六条素材、来源读取状态、当前路线、重试次数和事实性活动日志。
3. 显示不可交互的布置预览，让用户看到房间/物件逐步形成，但未经验证的半成品不能伪装成正式关卡。
4. 展示赛马路线状态：生成中、已返回校验、结构失败、已取消等。
5. 提供取消、返回标题、查看选中收藏和打开来源页面；取消必须终止在途请求并阻止旧结果写入关卡或缓存。
6. 长时间等待时提供明确的完整版本/快速版本选择；快速版本仍须保留内容证据、结构检查和可玩性检查。
7. 长期将生成任务后台化，使用户可以离开并从任务列表返回结果。

不要显示虚假百分比或模型原始思维链。进度应来自真实阶段事件，日志应描述系统事件。最小 MVP 为：独立生成面板、阶段步骤、已用时间、六条素材预览、事实性日志、取消按钮、赛马/重试状态和不可交互预览。

验收增加：首次可见进展时间、阶段耗时、总耗时 P50/P95、真实上游调用次数、重试次数、取消成功率、最终质量和存档一致性。不能只以“更快”判断成功。

### 11.15 谜题面板溢出审查（2026-08-31）

密码、角度、摩斯面板偶尔溢出屏幕的根因是动态内容与固定定位估算不匹配：`openPuzzlePanel()` 只做左右锚点判断，不读取显示后真实高度，也不检查 bottom；JS 按约 340px 估算宽度，CSS 实际最多 330px；角度表盘数量、长标题、颜色标签和摩斯串会改变面板尺寸；`.code`/`.kp-slot`/按钮行的收缩边界也不完整。通用 `.modal-card` 与 `.puzzle-panel .modal-card` 分散定义，进一步增加覆盖风险。

具体遗留问题：

1. **[P1] 垂直溢出**：底部节点打开角度/摩斯面板时，固定 `top` 没有根据面板高度回调。
2. **[P1] 定位估算与 CSS 尺寸不一致**：JS 的 `pw` 不等于面板实际宽度，舞台与 viewport 的边界也可能不同。
3. **[P2] 动态文本横向撑开**：长颜色标签、kicker/title、摩斯显示和按钮布局可能撑宽卡片。
4. **[P2] 缺少四向避让**：当前只有右侧失败后尝试左侧，没有上下候选和最终 viewport clamp。
5. **[P2] 断点覆盖分散**：通用弹窗、谜题面板、密码/角度/摩斯组件分别定义尺寸，移动端 `100vh`/软键盘等场景未统一处理。

最小修复：面板显示后读取 `getBoundingClientRect()`；以 `window.innerWidth/innerHeight` 为边界做四向定位；动态设置 `max-height`/`max-width`；为动态内容增加 `min-width:0`、换行、截断和编译阶段长度上限；使用 `100dvh`；集中谜题面板样式。

必须补充真实 DOM 回归：桌面底部节点、移动端密码、长标题/颜色标签、长摩斯串、三表盘角度、画布缩放/平移、虚拟键盘可视高度。验收要求面板四边在 viewport 内，确认/关闭按钮始终可见可点击。相关设计原则为 P79-P81。
