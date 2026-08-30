# 参考游戏《文字密室逃脱》逆向分析

> 来源:https://assets.easygame.tw/site_media/games/5769/index.html
> 分析日期:2026-08-23
> 本地资源:`reference/original-game/`(残缺副本,2026-08-28 自 ref-game/ 迁入):`config.js`(完整关卡数据)
> 与 `index.html`(页面骨架);`main.js`(引擎 bundle,3MB)、`style.css`、`assets/` 不在仓库中,页面不可运行。

## 1. 技术栈

- **Vite 构建**的纯前端 Web 游戏(非 Flash),入口是 `<canvas>` + Phaser 3 引擎
- 自定义手写字体 `jiangxizhuokai.woff2`(江西卓楷),营造纸面/手写质感
- 全 Canvas 渲染;节点支持拖动、滚轮缩放、场景平移
- 完整音频系统:背景音多轨混音(`bgm:{雨,风,雷雨,滴水}`)+ 数百个音效(火柴点火、开门、锯木头、解锁、敲铁、丧尸…)
- 全局禁用右键菜单;有 Cloudflare 保护(资源本身可直接下载)

## 2. 关卡构成

正式关卡 6 个(home 场景显示通关率 66%~82%):

| 关卡 | 主题 | 核心谜题 |
|---|---|---|
| 第一关 | 怕黑吗(破屋) | 油灯照明 → 看画 → 颜色密码 274 → 钥匙开门 |
| 第二关 | 监狱 | 锯子→棍子→钥匙;时钟 3:30 → 转盘 90°/180°;摩斯+日记 → 大铁箱 685 → 尸体手指 → 指纹锁 |
| 第三关 | 实验室 | 配电箱连线角度 → 终端图形密码 714 → 保险柜 → 紫外线灯 → 药水调配 → 解药 → ID卡 996 → 门禁 |
| 第四关 | 牢房 | 墙壁 1/3/2 → 铁窗敲击;金币→神秘人→钳子;木床→铁箱→宝石/怀表 02:45;磁铁铁棍→老鼠洞→钥匙 |
| 第五关 | 炸弹房 | **5 分钟倒计时**;碎纸→电脑密码;邮件→行动代号 134;铅笔显影→引爆装置 431;暗室→海报/平面图→保险柜 536→ID卡→门禁 605 |
| 第六关 | 地下室失忆特工 | 档案生日 512→手机;药品→键盘 702;U盘→内部数据→检索 996;排水口→纸条 35-42-03→铁盒;打火机暗格×3 |

另有约 14 个自由主题关卡嵌在 bundle 里:逃离密室、逃离二次元房间、恶魔仪式、关于游戏这件事、第七关、时间迷宫、镜中世界、致命巨物、蝴蝶效应、虚拟接入、UCP-1、活埋、逃离恶魔小屋、坠落。

## 3. 核心数据模型(最重要)

纯数据驱动:`config.js` 只描述关卡,**引擎解释执行**,写关 = 写 JSON。

### 3.1 场景树

```js
{ name:"mission1", missionName:"第一关", nextMission:"mission2",
  bgm:{雨:.3,风:.5},
  mask:[{ type:"foreground", background:"#000000", alpha:.5, showClue:["-#油灯"] }],  // 黑暗遮罩
  nodes:[{
    point:"center", name:"黑暗", desc:"...",
    state:[{ name:"破屋", preClue:["#油灯"] }],          // 节点多形态
    nodes:[{ name:"地板", nodes:[{ name:"火柴", interact:[...] }] }],  // 无限嵌套
    ...
  }]
}
```

### 3.2 线索系统 clue(状态机核心)

| 前缀 | 含义 | 示例 |
|---|---|---|
| `#xxx` | 获得线索 | `clue:"#油灯"` |
| `-#xxx` | 移除线索 | `preClue:["-#__subscribe"]` |
| `#A>B` | 组合线索(A 作用于 B) | `clue:"#钥匙>镣铐"` |
| `#x-{0}` | 动态占位符 | 密码盘 `#blue-{0}` → 拨到 2 得 `#blue-2` |
| `@事件` | 全局事件(通关/失败/重试) | `clue:"@通关"`、`"@失败"` |
| `$关卡` | 跳转关卡 | `clue:"$mission1"` |
| `%成就` | 解锁标记 | `checkClue:"%mission1"` |
| `*xxx` / `-*xxx` | 开关状态(夜视仪) | `startClue:"*夜视仪"`, `stopClue:"-*夜视仪"` |
| `^A/B` | 顺序组合(combineClue) | `"#顺序交互操作":["蓝色按钮","红色按钮","绿色按钮"]` |
| `?参数` | 带参事件 | `"@Switch-夜视仪?isOpen=false"` |

### 3.3 前置条件 preClue(可见性门)

- 字符串或数组;数组 = **全部满足**(AND)
- 支持 `|`(OR)、`!`(否定)、`-`(不存在)组合

### 3.4 节点字段

```js
{
  name, desc, tip,             // tip 是给玩家的提示(谜题几乎都带 tip 引导)
  key, type, data,             // 类型化节点
  state:[{name,desc,preClue,data}],  // 获得线索后切换形态(油灯→点亮)
  nodes:[...],                 // 子节点(展开进入)
  interact:[{type,target,clue,audio,preClue,params}],
  preClue,                     // 可见性
  data: {
    lockClue, clue, color, image, text,
    autoAdd:true,              // 拾取即入背包
    isOnce:true,               // 一次性
    noRefreshData:true,        // 刷新页面状态保持
    independent:true,          // 独立节点(不随场景移动)
    stealthUntilClue:"#隐藏门", // 隐形直到获得线索
    removeIfClue, checkClue,
    distance,                  // 探测器距离
    precision:30,              // 角度档位(12 格)
    needInteractCount:5,       // 可破坏需点 N 次
    knockCount, time, target, forColorSort
  }
}
```

## 4. 交互类型(引擎内置)

| type | 玩法 | 例子 |
|---|---|---|
| `click` | 点击检查/解锁 | 门、密码锁确认 |
| `use` | 物品作用于目标(组合) | 火柴→油灯;锯子→排水管 |
| `password` | 多位密码盘(数字/颜色/图形) | 274、685、714、605 |
| `angle` | 角度旋钮(12 档) | 时钟 3:30 → 90°/180° |
| `morse` | 摩斯密码输入 | `...--/--.../.----` → 371 |
| `knock` | 敲击计数序列 | 铁窗 1-3-2;暗格连点 3 次 |
| `breakable` | 可破坏(点 N 次) | 裂缝×5、木床×3 |
| `timer` | 倒计时/资源耗尽 | 炸弹 5min;夜视仪电量 4min |
| `detector` | 金属探测器(距离反馈) | 找隐形「隐藏门」 |
| `color-sort` | 颜色排序 | 药水调配(蓝绿红黄) |
| `switch` | 开关切换 | 夜视仪 |
| `image`/`text` | 线索载体 | 碎纸、实验日记、邮件、平面图 |
| `custom` | 自定义函数 | 订阅按钮 |

## 5. 值得借鉴的设计(对照收藏夹密室项目)

1. **纯数据驱动关卡**:写关卡=写 JSON,引擎解释。收藏夹密室的 `roomUse()` 硬编码条件应改为交互表/线索状态机。
2. **动态线索 + preClue 前置门**:`#blue-{0}` 占位符把"密码盘拨号"变成一条线索;`preClue` 数组统一控制所有可见性。收藏夹密室的 `state.progress` Set + 分散判断可统一成 clue 系统。
3. **节点多形态 state**:同一节点获得线索后改名改描述(油灯→点亮、黑屏→启动画面),正是"回访旧节点"的教科书实现。
4. **资源型道具**:手电筒/夜视仪 = timer 倒计时,耗尽触发 `overClue`(失败或降级),收藏夹密室的 flashlight 电量 3 可照搬。
5. **失败可恢复**:失败场景带 `canResurrect` + 线索快照恢复,不制造死局——与 design.md 的"错误可恢复"原则一致。
6. **顺序组合 combineClue**:按序点击(蓝→红→绿)得线索,与 Room 02 墙面三色按钮完全同构。
7. **隐藏节点 + 探测器**:`stealthUntilClue` 隐形 + detector 距离反馈,比收藏夹密室"拖开遮挡物"更系统化。
8. **tip 引导字段**:每个谜题带 tip(如"根据时钟三点半,将旋钮转至 90° 和 180°"),替代收藏夹密室的人工分级提示,更轻量。

## 6. 与收藏夹密室当前实现的差距

| 维度 | 参考游戏 | 收藏夹密室现状 |
|---|---|---|
| 关卡定义 | config.js 纯 JSON | `source` 数组 + 多段覆盖脚本 |
| 状态判定 | clue + preClue 统一门 | `state.progress` Set + roomUse 硬编码 if |
| 节点形态 | state 多形态切换 | 隐藏/新增节点模拟 |
| 类型化交互 | 引擎内置 14 种 | click/drag/QTE 手工实现 |
| 存档 | noRefreshData + 通关率 | IndexedDB(localStorage 位置) |

## 7. 结论

这是一个**节点树 + 线索状态机**驱动的文字密室游戏,6+14 个关卡全部由数据描述。收藏夹密室若想扩展到多房间,最佳路径是把引擎改成"clue 状态机 + 数据驱动交互表"——直接借鉴其 `clue`/`preClue`/`state`/`combineClue` 四个概念即可覆盖现有全部玩法,并为 LLM 生成关卡(Step Plan 管线)提供更稳定的输出契约。
