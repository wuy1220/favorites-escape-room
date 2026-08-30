# 收藏夹密室 · UI 结构性重设计(第二轮:场景空间化)

上轮是换皮;本轮重做布局骨架、坐标系统、信息架构与交互反馈,并修复两个结构性 bug。已确认的硬约束:全部功能 id 与状态钩子类保留;`#revisitRoom` id 保留且可见(verify_prison 真实点击它);`#homeStatus` 现有措辞不能改(4 处测试断言);scene 节点保留 `compiled-scene-` data-id 前缀;拖拽组合测试要求节点互不遮挡。

## Stage 1 — 布局骨架 100vh 化(修 bug 2:舞台随侧栏伸缩)
- 游戏屏改为满视口应用布局:`.shell` 高 100vh、grid 行 `auto(顶栏) + 1fr(主区)`;主区 `1fr + 360px` 两列;**舞台高度恒定**(主区行高,不再受内容影响);侧栏 `overflow-y:auto` 内部滚动。
- 侧栏内容限高:`.inspect-copy`/`.inventory`/`.hint-copy` 设 max-height + 滚动,侧栏总高不再推动行高。
- 响应式:≤1000px 维持现状堆叠(本就脱耦)。
- 改动:`css/styles.css`(骨架段)+ `index.html`(如需包裹层微调)。

## Stage 2 — 场景空间分区坐标系统(修 bug 1:子节点不在父节点周围)
在 `js/room02.js` 新增全局摆位原语(渲染原语层,engine/pipeline 均可调用),替换三处索引常量公式:

- **`roomLayoutBoard()`**:舞台按场景数分区(1=全屏 / 2=左右 / 3-4=2x2 / 5-6=2x3);每个分区 = 场景名牌(zone 节点)置顶 + 物件在分区内网格流式排列(3-4 列自适应,天然零碰撞);产物落在物件流末尾;出口固定右下分区。并行房间与顺序模式统一用此布局(对齐 P39-P42)。
- **`roomPlaceAround(parentNode, children)`**:运行时新增节点(组合产物/显形隐藏物/下一批导入)围绕父/源节点摆位 + 分区边界 clamp,替换 engine.js:650-664(隐藏物件同点堆叠)、pipeline.js:1866-1873(跨批 index 重置导致重叠)、engine.js:688-722(flat 容器物件全堆画布中央)。
- **编译路径接入**:engine hydrate(489-737)不再算坐标,改为建节点后调 `roomLayoutBoard()`;删除 `spawned:true` 对摆位的阻断(保留字段语义,摆位由新函数负责)。
- **修 reveal 双轨**:room02 的 roomUse/QTE reveal(845-848、909-910)显形后调用摆位,与 zone reveal 一致。
- **savePos 只写不读**:实现读取(载入时恢复玩家拖拽布局,带版本 key 防旧数据错位)。
- **核实 engine.js:1107-1117 场景守卫**:并行房间模式下 sceneIndex 恒 0,确认该守卫是否拦截 scenes[1+] 的物件点击;若拦截则修(这可能是第三个隐藏 bug)。

## Stage 3 — 信息架构与交互修复
- **进度单一化**:删 stage-head 的 ROOM STATE 文本行(改为显示当前场景名/自由探索);顶栏 meter+数字保留;objective 不再列全部开放 beat("现在可以做:…"任务清单式),改为"场景名 + 单条下一步引导"(openBeats[0] 标题)+ 完成态提示。零测试断言,可安全重写。
- **详情就地化**:node-pop 升级为可交互卡(pointer-events:auto、可选中复制、带关闭钮、点击卡外才关闭、防舞台裁切——顶部节点气泡改下方弹出),观察窗保留同步(#inspectCopy 有断言)。
- **节点卡片升级**:渲染模板(room02.js:633)输出 role 角标(`role-<role>` 类已存在,配 CSS 色条:线索/工具/锁/产物/干扰)+ .type 小字;卡片不再只有一行名字。
- **提示内容修复**:编译关卡(frontier='imported')的 requestHint 改读 `level.hints[]` 渐进展示(现为查 ROOM_HINTS 永远返回无关的"先观察唯一的场景"),观察力 4 格机制不变。
- **拖拽组合反馈**:moveRoomDrag 实时计算 drop target,可命中的组合目标加 `.drop-ok` 高亮边框;roomDropTarget 判定复用。
- **元动作归位**:`#revisitRoom` 从舞台右下 canvas-tools 移到顶栏 hud(engine.js ensureRevisitButton 改插入点,id 不变、可见可点);缩放工具留 canvas-tools;顶栏"重置房间"保留;底部 game-toolbar 胶囊保留(关卡名/保存/导出/回主页)。

## Stage 4 — 主页信息架构重排(app.js addUi 模板 + CSS)
- 保留全部 id 与 JS 显隐钩子(windowPanel 内联 display、homeStatus 文案由 JS 写、.window-card 类名、#homeClearCache 可见可点)。
- 重排为引导式三步:**① 选择收藏夹导出文件 → ② 可选:情绪或边界偏好 → ③ 选择时间片(上传后出现)→ 生成大按钮**;次入口(试玩固定样本/导入关卡/继续游戏/清空清洗缓存)降为次级按钮组;存档面板保留右栏。
- `#homeStatus` 四处断言文案("已清空"/"(N 条)"/"通过设计+求解验证"/"(glm)")不动。

## Stage 5 — 回归 + 视觉验收 + 文档
- 全量 ref-game 回归(目标:零测试改动全绿;重点盯四关真实 DOM 通关的拖拽遮挡与 verify_prison 对 #revisitRoom 的真实点击)。
- `ui_shots.py` 截图(扩展:展开后的多场景状态一张)→ judge 视觉验收。
- README/DESIGN-PRINCIPLES 更新日志。

## 风险与对策
- 拖拽遮挡破坏组合测试 → 分区网格天然零碰撞;每改一轮跑四关通关回归。
- 移动 #revisitRoom 插入点 → 顶栏 hud 常驻可见,verify_prison 真实点击路径先手动验证。
- room02 原生关卡手写坐标保留(本就围绕父节点设计),只修 reveal 双轨。
- 引擎门禁/机关/通关逻辑(beat 校验、keypad/angle/morse、快照存档)零行为变化。