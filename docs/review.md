# 项目审查记录

审查日期：2026-08-31

## 高风险问题

### [P1] 导入关卡存在 XSS 注入面

涉及：`js/room02.js:824-844`、`js/engine.js:716-786`、`js/app.js:1738-1753`

节点渲染使用字符串拼接生成 HTML。`kindCls`、`n.id`、`name` 和 URL 等字段来自导入关卡或素材，但没有统一做 HTML/属性转义和协议校验。导入文件可构造恶意 `role`/`id` 注入属性，也可提供 `javascript:` URL，在点击“打开原收藏”时执行脚本。

建议：节点全部改用 DOM API 或统一的完整转义函数；`role`、`id` 按白名单/字符集校验；外链仅允许 `http:`/`https:`，拒绝 `javascript:`、`data:` 等协议。

### [P1] `/api/llm-config` 向浏览器公开 API key

涉及：`server/favorites_room_server.py:326-358`

服务端从本地文件读取 GLM key 后直接放入 `/api/llm-config` 响应，同时对任意 localhost 端口开放 CORS（`server/favorites_room_server.py:330-333`）。本机其他网页可直接读取该密钥。

建议：由服务端代理 GLM 请求，不把密钥下发到前端；若必须保留配置接口，应至少增加一次性令牌或严格来源校验。

### [P1] 导入 JSON 缺少 schema 校验，畸形数据可导致挂载失败

涉及：`js/app.js:1763-1767`、`js/engine.js:30-37`

导入流程只验证 `level.items` 和 `level.beats` 是数组，但编译器直接对 `beat.uses`、`beat.requires` 调用 `.map()`。例如 `uses: {}`、beat 为 `null` 或 items 含 `null`，会在挂载阶段抛出异常，导致关卡无法载入。

建议：在写入 IndexedDB 前完成完整 schema 校验（字段类型、动作枚举、引用存在性、参数范围），失败时返回可理解的导入错误。

### [P1] 飞入动画期间禁用指针事件造成交互回归

涉及：`css/styles.css:1249-1254`、`ref-game/verify_clockwork.py:133-135`

`.node.arrive { pointer-events: none }` 会让节点在动画结束前完全不可操作。`verify_clockwork.py` 已复现失败：完成一次变身后立即拖拽，后续节点无法操作。prison、bear、watchman 测试增加了等待，但 clockwork 等路径仍未同步，用户快速连续操作也会丢失输入。

建议：统一交互助手等待动画结束，或仅禁用位置尚未稳定的节点；同时为所有回归脚本补充一致的 settle 逻辑。

## 其他健壮性风险

`server/favorites_room_server.py:382-400` 对请求体和 `Content-Length` 的异常处理不完整。JSON 顶层为数组时会触发未捕获的 `AttributeError`，非数字 `Content-Length` 会触发 `ValueError` 并直接断开请求。建议统一限制请求体大小并将非法请求返回 400。

## 验证记录

- 通过：`test_compile.py` 14/14
- 通过：`verify_prison.py` 42/42
- 通过：`verify_bear.py` 30/30
- 通过：`verify_bookmarks.py` 31/31
- 通过：`verify_regression_watchman.py` 20/20
- 通过：`verify_reset_lifecycle.py` 13/13
- 失败：`verify_clockwork.py`（飞入动画期间节点不可操作）
- 备注：直接运行 `pytest` 会在收集阶段遇到测试脚本主动 `SystemExit`，因此不能作为总测试入口。
