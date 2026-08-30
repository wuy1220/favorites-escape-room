# 收藏夹密室（favorites-escape-room）

读取 Chrome 收藏夹导出（HTML/JSON），经本地清洗与 LLM 设计管线（范例模仿设计师 →
编译 → 求解器验证 → 自修复回路）生成一个按 beat 执行的节点式密室。
不依赖 LLM 的部分（Room 02 固定房间、关卡导入试玩）可独立运行。

## 代码结构

| 文件 | 职责 |
| --- | --- |
| `index.html` | 页面骨架，按序加载下列模块（经典脚本，共享全局作用域） |
| `js/room02.js` | Room 02 固定房间状态机（内置关卡，无 LLM） |
| `js/ref-levels.js` | 范例关卡数据（designWindow 的 few-shot 素材：监狱复刻/熊曰情报） |
| `js/pipeline.js` | 生成管线：清洗 → designWindow → compileLevel → solveLevel → 自修复回路，对外接口 `window.__favoriteRoomPipeline` |
| `js/engine.js` | 编译关卡执行引擎（线索门控/组合/机关弹窗/交付通关） |
| `js/app.js` | 产品壳：IndexedDB 存档、导入导出、上传生成流程，对外接口 `window.__favoriteRoomHome` |
| `css/tokens.css` | 设计令牌:暗室+纸质档案双材质(深褐底色纵深/纸张系/火漆印强调/墨水语义色/mono 标签字体/间距/阴影/动效/纸纤维噪点) |
| `css/styles.css` | 全部组件样式(只引用令牌):基础/通用组件/主页/游戏壳/舞台/纸索引卡节点/情境抽屉/弹窗族 |
| `server/favorites_room_server.py` | 本地服务器：静态托管 + `/api/step` LLM 代理（step-router-force，127.0.0.1:8128） |
| `fixtures/` `sample-puzzles/` | 测试收藏夹样本 / 已验证关卡 JSON（回归用例） |
| `ref-game/` | 验证工具链（playwright 真实 DOM 通关、求解器单测、批量生成门禁） |

设计原则沉淀见 `DESIGN-PRINCIPLES.md`；迭代历史与架构现状见 `docs/handoff.md`。
下一阶段产品方向见 `docs/untitled-adventure-direction.md`：取消固定主题作为默认入口，允许更跳脱、意识流或无单一主题的生成，并采用“通关后命名 + 冒险回执”的体验。

## 运行

```powershell
python server/favorites_room_server.py
# 打开 http://127.0.0.1:8128/
```

该服务器同时提供静态页面与 `/api/step`（Step Plan → deepseek advisor 代理）。
**清洗任务默认走快车道**（直连 step-3.7-flash、不强制 advisor，实测约 4s/次），
设计任务保持 advisor 强制（用时间换质量）；可用 `FAV_ROOM_PORT` 环境变量换端口。
只玩不生成时，用任意静态服务器指向本目录即可（例如
`python -m http.server 8128`）。

## 回归验证

依赖 playwright 与本地 Chromium。先按上面方式启动服务器，再在项目根目录：

```powershell
python ref-game/test_solver.py      # 求解器单测
python ref-game/test_compile.py     # 编译管线无 LLM 冒烟(compile/solve/固定模板/兜底金标准)
python ref-game/verify_clean_strict.py  # 清洗严格性 + 清空缓存按钮回归
python ref-game/verify_verdict_flow.py  # 全局清洗/标记记录/增量清洗/并发清洗(stub 模型,零配额)
python ref-game/verify_design_race.py   # 设计赛马回归(多路并行,stub 模型,零配额)
python ref-game/verify_prison.py    # 四关真实 DOM 通关回归
python ref-game/verify_bear.py
python ref-game/verify_clockwork.py
python ref-game/verify_bookmarks.py
python ref-game/smoke_room02.py     # 固定房间冒烟
python ref-game/verify_naming_flow.py   # 通关延迟命名+冒险回执(stub 模型,零配额)
python ref-game/ui_shots.py ref-game/shots/current  # 全界面截图(视觉回归对比,零配额)
```

当前基线：solver 6/6、compile 5/5（含 REF_LEVELS scenes 编译金标准）、clean_strict 8/8、
verdict_flow 10/10、design_race 9/9；prison 42/42、bear 30/30、clockwork 39/39、
bookmarks 31/31、naming_flow 10/10、smoke_room02 全过。
（`verify_adventure_goal.py` 依赖真实 LLM 分钟级生成，不作为常规回归门禁。）
改动 `js/` 或 `css/` 后至少跑一遍上述套件；涉及生成管线时另跑 `ref-game/e2e_v7_batch.py`
（真实 LLM，分钟级）。UI 改动另用 `ui_shots.py` 截图与 `ref-game/shots/` 存档对比。

游戏舞台的空间模型（2026-08-29 结构性重设计）：`roomLayoutBoard()`（js/room02.js）按
场景/容器数量把舞台切成可视分区（名牌置顶 + 物件网格 + 极淡分区底板），所有节点槽位在
hydrate 时一次定死，reveal 只翻显隐不挪坐标；玩家拖拽的布局仅在原生房间持久化恢复。

游玩界面信息架构（2026-08-30 第四轮·沉浸式）：**画布是唯一主角**——观察靠节点就地详情卡；
提示是画布右上火漆封印圆钮「线索·N」（点击展开线索便签，浮层内"求一条线索"）；日志是
画布左下单行 ticker（点击展开完整记录浮层）；物品清单移出可见界面（`.offstage`，引擎照常
写入，innerText 供断言读取）。注意：stage 的画布平移 pointerdown 已排除浮层元素
（`.hint-seal/.hint-float/.log-ticker/.log-float`），新增画布内控件须同步加排除，
否则 setPointerCapture 会吞掉它们的 click。
