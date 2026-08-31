# -*- coding: utf-8 -*-
"""三关重设计 v4(2026-08-30 需求方裁定:推翻旧稿重做)

公理(针对旧稿三大缺陷):
1. 严格链式门控——每把锁都是链上必经节点,deliver 的 requires 传递覆盖全部前序步骤,锁跳不掉;
2. 答案不自泄漏——每把锁的答案只出现在「别的物件」的 reason 里,
   锁自身/premise/objective/hints 一律不含答案;
3. 三关各主打一种理解动作:A=计量合成(数字读数) B=语义文字(文本口令) C=排序(sequence)+组合。

事实接地(全部来自真实抓取,数据在档案卡里固化,不随实时漂移):
- A: B站 NGU MV 档案 播放量 104610374 / 弹幕 148416;压轴 MMD = 重巡Pola「Treasure」BV1Us411W7AE(收藏夹内)
- B: Obsidian 标语 "Sharpen your thinking";hello-algo 标语 "动画图解、一键运行的数据结构与算法教程";
     干扰卡 javascript.js.cn "主课程包含 2 部分……"
- C: javascript.js.cn 课程结构(语言本身→浏览器)作排序依据;MDN 指南作第二本;hello-algo 作干扰书
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "sample-puzzles")


def card(id, title, description):
    return {
        "id": id,
        "title": title,
        "domain": "demo",
        "dateAdded": "",
        "url": "",
        "urlPath": "",
        "description": description,
    }


def li(id, role, roleLabel, title, reason, hidden=False, container=None, auto=False):
    it = {
        "id": id,
        "role": role,
        "roleLabel": roleLabel,
        "title": title,
        "sceneName": title,
        "reason": reason,
        "hidden": hidden,
    }
    if container:
        it["container"] = container
    if auto:
        it["auto"] = True
    return it


# ============ A 末班点播台·停电夜(显影+检索多问+暗格敲击+计量推导) ============
# 手法对应原作:m6 药粉显键痕→n3 去污粉擦配电箱(combine 变身);
#             m6 检索 138→444 证据链→n6/n8 同一检索台双查询(461→档案提『压轴』→文字检索);
#             m6 打火机暗格连按三次→n9 底座 knock;数据推导保持计量本色(461=第3-5位,1046=前四位)。
items_a = [
    card("ra-note", "台长字条", "钉在墙上的字条,交代了今晚的任务和几条行话规则。"),
    card("ra-drawer", "工作台抽屉", "工作台的抽屉半开着,里面似乎还有东西。"),
    card("ra-cleaner", "去污粉", "一罐去污粉,标签写着:油垢克星。"),
    card("ra-tape", "旧磁带", "A 面标签磨得发白,数据条还看得清。"),
    card("ra-fusebox", "配电箱", "配电箱的面板糊着一层油垢,看不清线路。"),
    card("ra-terminal", "检索台", "曲库检索台,屏幕黑着,指示灯灭。"),
    card("ra-panel", "频率面板", "点播台的频率面板,四位数字转盘。"),
    card("ra-file-ngu", "曲库档案·A面", "曲库里这首歌的档案页。"),
    card("ra-memo", "检索结果·压轴", "台长的一条检索备忘。"),
    card("ra-base", "点播台底座", "点播台的木质底座。"),
    card("ra-board", "松动的底板", "底座侧面的一块木板,和别处声音不一样。"),
    card("ra-disc", "MMD 光碟 · Treasure", "压轴的光碟:重巡 Pola 的「Treasure」。"),
]
level_a = {
    "id": "level-demo-gamenight",
    "title": "深秋游戏之夜 · 末班点播台",
    "premise": "2024 年 11 月的深夜,点播台忽然断了电。台长的字条钉在墙上:今晚的压轴必须由你手动播出——但检索台锁着数据,频率面板死活不亮,压轴的东西,他藏在了一个『只有你知道的地方』。",
    "objective": "按字条的行话修好配电箱、查出台里曲库的档案,调准频率;再顺着档案里的线索找到台长藏压轴碟的地方,把它投递出去。",
    "targetMinutes": 12,
    "selectedItemIds": [it["id"] for it in items_a],
    "containers": [
        {
            "id": "ra-drawer",
            "name": "工作台抽屉",
            "desc": "工作台的抽屉半开着。点击拉开它。",
            "hidden": False,
        }
    ],
    "items": [
        li("ra-note", "clue", "线索", "台长字条",
           "『今晚压轴你来播。三件事记住:一、检索编号 = 曲目播放量的第 3 到第 5 位;二、热线频率 = 播放量的前四位;三、配电箱的闸被油垢糊死了,工作台抽屉里有去污粉。压轴的东西,我藏在只有你知道的地方。』"),
        li("ra-cleaner", "tool", "工具", "去污粉",
           "一罐去污粉,标签写着:油垢克星。倒一点在糊死的面板上,擦掉就见真章。",
           hidden=True, container="ra-drawer"),
        li("ra-tape", "clue", "线索", "旧磁带",
           "【网页内容·数据条】A 面标签:Never Gonna Give You Up。数据条印着:视频播放量 104610374。侧面小字:曲库数据以检索台档案为准。",
           hidden=True, container="ra-drawer"),
        li("ra-fusebox", "transform", "结果", "配电箱",
           "配电箱的面板糊着一层油垢,线路和总闸的位置都看不清。"),
        li("ra-terminal", "lock", "锁", "检索台",
           "曲库检索台,一块数字屏。通电后,输入编号就能调出曲库档案。"),
        li("ra-panel", "lock", "锁", "频率面板",
           "点播台的频率面板,四位数字转盘。调准了,整座城市都能听见这首老歌。"),
        li("ra-file-ngu", "clue", "线索", "曲库档案·A面",
           "【检索结果】A 面:Never Gonna Give You Up——播放量 104610374,弹幕总量 148416。备注:B 面是空的,压轴的碟不在曲库里,另想辙。",
           hidden=True, auto=True),
        li("ra-memo", "clue", "线索", "检索结果·压轴",
           "【检索结果·压轴】台长的备忘:『压轴碟不在曲库——我把它封进了点播台底座。当年亲手封的,之后就再没打开过。』",
           hidden=True),
        li("ra-base", "clue", "线索", "点播台底座",
           "点播台的木质底座,钉得结结实实。"),
        li("ra-board", "tool", "工具", "松动的底板",
           "被检索台的振动震松的木板——敲起来空空的,边缘有一道细缝,像被人撬开过又钉了回去。",
           hidden=True, auto=True),
        li("ra-disc", "reward", "奖励", "MMD 光碟 · Treasure",
           "从暗格里弹出来的压轴光碟:重巡 Pola 的「Treasure」。光碟盒上贴着投递口的标签。",
           hidden=True),
    ],
    "beats": [
        {"id": "n1", "title": "读台长字条", "action": "inspect", "uses": ["ra-note"]},
        {"id": "n2", "title": "拉开工作台抽屉", "action": "inspect", "uses": ["ra-drawer"],
         "reveals": ["ra-cleaner", "ra-tape"]},
        {"id": "n3", "title": "用去污粉擦配电箱", "action": "combine", "uses": ["ra-cleaner", "ra-fusebox"],
         "requires": ["n1"], "resultOn": "ra-fusebox", "product": "擦亮的配电箱", "consume": ["ra-cleaner"]},
        {"id": "n4", "title": "合上总闸", "action": "inspect", "uses": ["result:n3"],
         "requires": ["n3"], "product": "通电的配电箱"},
        {"id": "n5", "title": "读旧磁带数据条", "action": "inspect", "uses": ["ra-tape"], "requires": ["n2"]},
        {"id": "n6", "title": "检索曲目编号", "action": "password", "uses": ["ra-terminal"], "expected": "461",
         "requires": ["n1", "n4", "n5"], "product": "吐出档案的检索台", "reveals": ["ra-file-ngu"]},
        {"id": "n7", "title": "调准频率面板", "action": "password", "uses": ["ra-panel"], "expected": "1046",
         "requires": ["n6"]},
        {"id": "n8", "title": "检索『压轴』", "action": "password", "uses": ["ra-terminal"], "expected": "压轴",
         "requires": ["n7"], "resultOn": "ra-base", "product": "嗡嗡作响的检索台",
         "reveals": ["ra-memo", "ra-board"]},
        {"id": "n9", "title": "底座暗格", "action": "knock", "uses": ["ra-board"], "count": 3,
         "requires": ["n8"], "resultOn": "ra-board", "product": "撬开的暗格", "reveals": ["ra-disc"]},
        {"id": "n10", "title": "投递压轴光碟", "action": "deliver", "uses": ["ra-disc"], "requires": ["n9"]},
    ],
    "hints": [
        "墙上钉着台长的字条——行话规则都在上面,先读它。",
        "抽屉里的两样东西各有用处:数据要看,粉末要用。",
        "配电箱擦亮之后还差一步:把闸合上。",
        "检索台吃的是编号——字条说了编号怎么从播放量里取。",
        "档案的备注别跳过,『压轴』两个字本身就是一条检索词。",
        "台长说封在了底座里——再去看看底座,有什么东西和之前不一样了。",
    ],
    "mechanics": ["inspect", "combine-显影", "password×2(检索多问)", "knock", "deliver"],
}

# ============ B 春日工具箱·守库人的遗愿(电与光族:角度接线+灯光显形+语义锁) ============
# 机制族(与 A/C 零重叠):①angle 接线台灯(端子刻度=数据在底座盘,'拨回钟面上的家'=规则在皱便签,
#   m3 配电箱语法+一次钟点→角度换算);②灯光显形——修好台灯不是开门钥匙,而是信息载体:
#   光照亮墙上守库人的便签(auto,锚定灯旁),光照=叙事因果;③语义文字锁保持 B 本色。
# 叙事:守库人故意弄坏台灯——『修好它,你就看得见我想让你看见的东西』;修灯=读懂他,开库=接班。
items_b = [
    card("tb-clip", "素材夹", "牛皮纸夹里滑出几张打印卡和一张皱便签。"),
    card("tb-card-obs", "宣传卡 · 笔记库", "卡上印着一句英文标语。"),
    card("tb-card-js", "宣传卡 · 语言书", "卡上印着语言课程的介绍,背面空白。"),
    card("tb-note-folded", "皱便签", "守库人的字,折了又折。"),
    card("tb-lamp", "台灯", "书桌上的旧台灯,开关拨了没反应,底座敞着。"),
    card("tb-panelbase", "底座端子盘", "台灯底座里的三色接线和端子。"),
    card("tb-note-wall1", "灯下便签 · 口令", "灯光下显出的一张便签。"),
    card("tb-note-wall2", "灯下便签 · 标语", "灯光下显出的另一张便签。"),
    card("tb-gate", "库门文字屏", "笔记库的库门,一块文字输入屏。"),
    card("tb-shelf", "书架标签屏", "书架侧面的标签屏。"),
    card("tb-desk", "书桌", "空书桌等着建成仪式。"),
    card("tb-ticket", "藏书票", "一枚烫金藏书票。"),
]
level_b = {
    "id": "level-demo-toolbox",
    "title": "春日工具箱 · 守库人的遗愿",
    "premise": "2025 年 4 月的春夜,你接手了守库人的旧书房。他留下一句话:『这间屋子的灯,是我亲手弄坏的——修好它,你就看得见我想让你看见的东西。库门只认原话,替我把这座库建成。』",
    "objective": "读懂守库人的皱便签,把台灯的线接回各自的家;灯亮之后,顺着光显出的便签推导库门口令与书架标签,把藏书票插上书桌——替他把这座库建成。",
    "targetMinutes": 12,
    "selectedItemIds": [it["id"] for it in items_b],
    "containers": [
        {"id": "tb-clip", "name": "素材夹", "desc": "牛皮纸夹里滑出几张打印卡和一张皱便签。点击打开素材夹。", "hidden": False}
    ],
    "items": [
        li("tb-clip", "clue", "线索", "素材夹", "牛皮纸夹里滑出几张打印卡和一张皱便签。点击打开素材夹,都翻一遍。"),
        li("tb-card-obs", "clue", "线索", "宣传卡 · 笔记库",
           "【网页内容】卡上印着那句英文标语:Sharpen your thinking。下面还有一行中文小字:把思想磨得更锋利。",
           hidden=True, container="tb-clip"),
        li("tb-card-js", "clue", "线索", "宣传卡 · 语言书",
           "【网页内容】卡上印着:主课程包含 2 部分,涵盖 JavaScript 作为一门编程语言和使用浏览器。背面空白——皱便签上找不着它的名字。",
           hidden=True, container="tb-clip"),
        li("tb-note-folded", "clue", "线索", "皱便签",
           "守库人的字,折了又折:『灯是我亲手弄坏的。三根线垂着,可每根线都有家——接回它钟面上的家,灯就亮。你看得见我想让你看见的东西。』",
           hidden=True, container="tb-clip"),
        li("tb-lamp", "lock", "锁", "台灯",
           "书桌上的旧台灯。底座敞开着,红、蓝、黄三根线断在半空,线头还崭新——是剪断的,不是烧断的。"),
        li("tb-panelbase", "clue", "线索", "底座端子盘",
           "台灯底座里的三色端子,每个旁边嵌着一枚小钟面:红端子的钟面指着 3 点方向,蓝的指着 7 点,黄的指着 11 点。钟面是手绘的,和皱便签一个笔迹。"),
        li("tb-note-wall1", "clue", "线索", "灯下便签 · 口令",
           "灯光够到的地方,墙上贴着一张便签:『口令 = 笔记库标语去掉第一个词。那句英文是我最信的一句话,就在夹子的蓝卡上。』",
           hidden=True, auto=True),
        li("tb-note-wall2", "clue", "线索", "灯下便签 · 标语",
           "另一张便签,边角泛黄:『顶层标签 = 算法书标语的头一个词。整句我抄在这儿:动画图解、一键运行的数据结构与算法教程。』",
           hidden=True, auto=True),
        li("tb-gate", "lock", "锁", "库门文字屏",
           "笔记库的库门没有锁孔,只有一块文字输入屏,屏上闪烁着一行提示:请输入入库口令。"),
        li("tb-shelf", "lock", "锁", "书架标签屏",
           "书架侧面嵌着一块标签屏:请输入顶层标签。屋里亮起来,它才通电。"),
        li("tb-desk", "transform", "结果", "书桌",
           "空书桌等着建成仪式。把藏书票插上去,它就是笔记库的正门。"),
        li("tb-ticket", "tool", "工具", "藏书票",
           "一枚烫金藏书票,票面上印着『我的第一座笔记库』——守库人留到最后的东西。该把它插上书桌了。",
           hidden=True, auto=True),
    ],
    "beats": [
        {"id": "w1", "title": "打开素材夹", "action": "inspect", "uses": ["tb-clip"],
         "reveals": ["tb-card-obs", "tb-card-js", "tb-note-folded"]},
        {"id": "w2", "title": "读皱便签", "action": "inspect", "uses": ["tb-note-folded"], "requires": ["w1"]},
        {"id": "w3", "title": "看底座端子盘", "action": "inspect", "uses": ["tb-panelbase"], "requires": ["w2"]},
        {"id": "w4", "title": "把线接回钟面上的家", "action": "angle", "uses": ["tb-lamp"],
         "angles": [90, 210, 330], "precision": 30, "labels": ["红线", "蓝线", "黄线"],
         "requires": ["w2", "w3"], "resultOn": "tb-lamp", "product": "亮起的台灯",
         "reveals": ["tb-note-wall1", "tb-note-wall2"]},
        {"id": "w5", "title": "读灯下便签·口令", "action": "inspect", "uses": ["tb-note-wall1"], "requires": ["w4"]},
        {"id": "w6", "title": "读灯下便签·标语", "action": "inspect", "uses": ["tb-note-wall2"], "requires": ["w4"]},
        {"id": "w7", "title": "输入库门口令", "action": "password", "uses": ["tb-gate"], "expected": "your thinking",
         "requires": ["w5", "w1"], "resultOn": "tb-gate", "product": "敞开的库门", "reveals": ["tb-ticket"]},
        {"id": "w8", "title": "输入书架顶层标签", "action": "password", "uses": ["tb-shelf"], "expected": "动画图解",
         "requires": ["w6"]},
        {"id": "w9", "title": "插上藏书票", "action": "combine", "uses": ["tb-ticket", "tb-desk"],
         "requires": ["w7", "w8"], "resultOn": "tb-desk", "product": "建成的笔记库", "consume": ["tb-ticket"]},
        {"id": "w10", "title": "替守库人落成", "action": "deliver", "uses": ["result:w9"], "requires": ["w9"]},
    ],
    "hints": [
        "素材夹里的皱便签要展开读——台灯为什么坏,答案在里面。",
        "底座端子盘上的小钟面,是每根线的『家』的方向。",
        "红线 3 点、蓝线 7 点、黄线 11 点——钟面方向换算成表盘角度。",
        "灯亮之后别急着走,光够得到的墙上多看两眼。",
        "库门口令从笔记库卡的原话里取,取法在灯下便签上。",
        "书架标签的头一个词,守库人替你抄好了整句。",
        "藏书票插上书桌,替他把这座库建成。",
    ],
    "mechanics": ["inspect", "angle(钟点→角度接线)", "灯光显形(auto×2)", "password-text×2", "combine"],
}

# ============ C 秋末自学计划·闭馆前的资料室(借阅族:弹书+顺序扫描+NPC) ============
# 机制族(与 A/B 零重叠):①容器弹书——两个书架共弹出 4 本,绿标 3 本是本批,红标 1 本是干扰;
#   ②顺序扫描——链式组合 enforce 索书号升序(前一本没扫,后一本拖上去无反应,真顺序而非提示);
#   ③NPC——全部受理后广播响起,值班员从借阅台那头现身(节点树另一端的巧合事件,auto);
#   点击他=对话,递保温壶=交易(m4 神秘人语法),换来借阅章。
items_c = [
    card("rc-door", "资料室门", "资料室的门虚掩着。点击推门进去。"),
    card("rc-manual", "守馆手册", "借阅台上的手册,翻开着。"),
    card("rc-shelfa", "还书车 · 上层", "还书车的上层书架,塞着几本书。"),
    card("rc-shelfb", "还书车 · 下层", "还书车的下层书架,也塞着书。"),
    card("rc-book1", "绿标书 · 现代JavaScript教程", "书脊贴着绿色书标:Z-02。"),
    card("rc-book2", "绿标书 · JavaScript指南", "书脊贴着绿色书标:Z-05。"),
    card("rc-book3", "绿标书 · Hello 算法", "书脊贴着绿色书标:Z-09。"),
    card("rc-book4", "红标书 · 五三题库", "书脊贴着红色书标:R-13。"),
    card("rc-scanner", "扫描台", "借阅台旁的扫描台,指示灯待机闪烁。"),
    card("rc-desk", "借阅台", "借阅台空着,后面虚掩着一扇小门。"),
    card("rc-npc", "值班员", "值夜班的学长,抱着一只茶杯。"),
    card("rc-kettle", "保温壶", "还书车旁的保温壶,摸着还温。"),
    card("rc-stamp", "借阅章", "黄铜借阅章。"),
    card("rc-ticket", "提货单", "借阅系统的提货单。"),
]
level_c = {
    "id": "level-demo-selfstudy",
    "title": "秋末自学计划 · 闭馆前的资料室",
    "premise": "2025 年 11 月的傍晚,资料室快闭馆了。还书车上堆着今天回流的书,提货单还没盖章,值班员不知道躲去了哪儿——借阅台后面只留着一壶还温着的茶。窗外天色暗得很快。",
    "objective": "按守馆手册的流程把本批图书逐本扫描归架,等系统受理;找到值班员把章要出来,盖在提货单上,赶在闭馆前交单出室。",
    "targetMinutes": 14,
    "selectedItemIds": [it["id"] for it in items_c],
    "containers": [
        {"id": "rc-shelfa", "name": "还书车 · 上层", "desc": "还书车的上层书架。点击翻一翻。", "hidden": False},
        {"id": "rc-shelfb", "name": "还书车 · 下层", "desc": "还书车的下层书架。点击翻一翻。", "hidden": False},
    ],
    "items": [
        li("rc-door", "clue", "线索", "资料室门", "资料室的门虚掩着,门缝里漏出旧纸的味道。点击推门进去。"),
        li("rc-manual", "clue", "线索", "守馆手册",
           "【流程页】今晚归还批次:贴绿标的三本。归架流程:按索书号从小到大,逐本放上扫描台;全部受理后系统会响铃——值班员自然会来找你。备注:章不外借,但他那个人,只认热茶。",
           hidden=True),
        li("rc-shelfa", "clue", "线索", "还书车 · 上层", "还书车的上层书架,塞着几本书。点击翻一翻,书就滑出来。"),
        li("rc-book1", "clue", "线索", "绿标书 · 现代JavaScript教程",
           "【网页内容·书脊】绿标 Z-02。主课程包含 2 部分,涵盖 JavaScript 作为一门编程语言和使用浏览器。",
           hidden=True, container="rc-shelfa"),
        li("rc-book3", "clue", "线索", "绿标书 · Hello 算法",
           "【网页内容·书脊】绿标 Z-09。动画图解、一键运行的数据结构与算法教程。",
           hidden=True, container="rc-shelfa"),
        li("rc-shelfb", "clue", "线索", "还书车 · 下层", "还书车的下层书架,也塞着书。点击翻一翻。"),
        li("rc-book2", "clue", "线索", "绿标书 · JavaScript指南",
           "【网页内容·书脊】绿标 Z-05。JavaScript 指南——讲语言在浏览器里的用法。",
           hidden=True, container="rc-shelfb"),
        li("rc-book4", "clue", "线索", "红标书 · 五三题库",
           "红标 R-13。《五年高考·三年模拟》。和这个房间格格不入,像是谁忘在这儿的。手册说今晚只收绿标。",
           hidden=True, container="rc-shelfb"),
        li("rc-scanner", "tool", "工具", "扫描台",
           "借阅台旁的扫描台,指示灯待机闪烁。把书平放上去就能扫——但系统有它认的次序。"),
        li("rc-desk", "clue", "线索", "借阅台",
           "借阅台空着,台面收拾得整整齐齐,后面虚掩着一扇小门,门缝里透出一点灯光。"),
        li("rc-npc", "clue", "线索", "值班员",
           "『都扫完啦?』值夜班的学长端着茶杯,从借阅台那头踱了过来。『归架章在我身上,不外借——除非……你懂的吧?这壶茶闻着正好。』",
           hidden=True, auto=True),
        li("rc-kettle", "tool", "工具", "保温壶",
           "还书车旁的保温壶,摸着还温。守馆人走前泡的茶,一口没动。"),
        li("rc-stamp", "tool", "工具", "借阅章",
           "黄铜借阅章,章面刻着『已归架』,把手上缠着防滑绳。值班员塞给你的。", hidden=True, auto=True),
        li("rc-ticket", "transform", "结果", "提货单",
           "借阅系统的提货单,空白处等着盖章。盖了章的单子才能交出去。", hidden=True),
    ],
    "beats": [
        {"id": "c1", "title": "推开资料室", "action": "inspect", "uses": ["rc-door"],
         "reveals": ["rc-manual", "rc-shelfa", "rc-shelfb", "rc-scanner", "rc-desk", "rc-kettle", "rc-ticket"]},
        {"id": "c2", "title": "读守馆手册", "action": "inspect", "uses": ["rc-manual"], "requires": ["c1"]},
        {"id": "c3", "title": "翻上层书架", "action": "inspect", "uses": ["rc-shelfa"],
         "requires": ["c2"], "reveals": ["rc-book1", "rc-book3"]},
        {"id": "c4", "title": "翻下层书架", "action": "inspect", "uses": ["rc-shelfb"],
         "requires": ["c2"], "reveals": ["rc-book2", "rc-book4"]},
        {"id": "c5", "title": "看 Z-02 书脊", "action": "inspect", "uses": ["rc-book1"], "requires": ["c3"]},
        {"id": "c6", "title": "看 Z-05 书脊", "action": "inspect", "uses": ["rc-book2"], "requires": ["c4"]},
        {"id": "c7", "title": "看 Z-09 书脊", "action": "inspect", "uses": ["rc-book3"], "requires": ["c3"]},
        {"id": "c8", "title": "扫描第一本(Z-02)", "action": "combine", "uses": ["rc-book1", "rc-scanner"],
         "requires": ["c2", "c5"], "resultOn": "rc-scanner", "product": "扫描台 · 已受理 1/3",
         "consume": ["rc-book1"]},
        {"id": "c9", "title": "扫描第二本(Z-05)", "action": "combine", "uses": ["rc-book2", "rc-scanner"],
         "requires": ["c8", "c6"], "resultOn": "rc-scanner", "product": "扫描台 · 已受理 2/3",
         "consume": ["rc-book2"]},
        {"id": "c10", "title": "扫描第三本(Z-09)", "action": "combine", "uses": ["rc-book3", "rc-scanner"],
         "requires": ["c9", "c7"], "resultOn": "rc-scanner", "product": "扫描台 · 已受理 3/3",
         "consume": ["rc-book3"], "reveals": ["rc-npc"]},
        {"id": "c11", "title": "和值班员搭话", "action": "inspect", "uses": ["rc-npc"], "requires": ["c10"]},
        {"id": "c12", "title": "把保温壶递给他", "action": "combine", "uses": ["rc-kettle", "rc-npc"],
         "requires": ["c11"], "resultOn": "rc-npc", "product": "捧着热茶的值班员",
         "consume": ["rc-kettle"], "reveals": ["rc-stamp"]},
        {"id": "c13", "title": "盖归架章", "action": "combine", "uses": ["rc-stamp", "rc-ticket"],
         "requires": ["c12"], "resultOn": "rc-ticket", "product": "盖章的提货单", "consume": ["rc-stamp"]},
        {"id": "c14", "title": "闭馆前交单", "action": "deliver", "uses": ["result:c13"], "requires": ["c13"]},
    ],
    "hints": [
        "推门之后,借阅台上翻开着的手册就是今晚的流程说明。",
        "还书车的两层都要翻——书会自己滑出来,认准绿色书标。",
        "红标那本和今晚无关,手册说了只收绿标。",
        "扫描有次序:按索书号从小到大,一本一本放上台。",
        "全部受理后系统会响铃——等等看,会有人出现。",
        "值班员的话里有话:他缺的东西,还书车旁边正好有一只。",
        "章到手,盖单,赶在闭馆前出门。",
    ],
    "mechanics": ["inspect", "容器弹书×2", "顺序扫描(链式组合×3,索书号升序)", "NPC(现身/对话/交易)", "auto显形×2"],
}

for fname, items, level in (
    ("demo-gamenight.room.json", items_a, level_a),
    ("demo-toolbox.room.json", items_b, level_b),
    ("demo-selfstudy.room.json", items_c, level_c),
):
    payload = {
        "records": [],
        "controlledIds": [it["id"] for it in items],
        "items": items,
        "level": level,
    }
    path = os.path.join(OUT, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("已写出", path, "beats:", len(level["beats"]))

# ============ 泄漏自检:锁答案不得出现在锁自身/premise/objective/hints ============
answers = {
    "demo-gamenight": ["1046", "461", "104610374", "148416"],
    "demo-toolbox": ["your thinking", "动画图解", "90", "210", "330"],  # 口令/标签/接线角度
    "demo-selfstudy": ["Z-02", "Z-05", "Z-09", "z-02"],  # 索书号只出现在书脊数据卡,手册不得写明顺序
}
leaks = []
for fname, keys in (
    ("demo-gamenight", answers["demo-gamenight"]),
    ("demo-toolbox", answers["demo-toolbox"]),
    ("demo-selfstudy", answers["demo-selfstudy"]),
):
    lv = json.load(open(os.path.join(OUT, fname + ".room.json"), encoding="utf-8"))["level"]
    lock_ids = {b["uses"][0] for b in lv["beats"] if b["action"] == "password"}
    for it in lv["items"]:
        blob = (it.get("reason") or "")
        if it["id"] in lock_ids:
            for k in keys:
                if k in blob:
                    leaks.append((fname, "锁自身泄漏", it["id"], k))
    for field in ("premise", "objective"):
        for k in keys:
            if k in lv.get(field, ""):
                leaks.append((fname, field + "泄漏", field, k))
    for h in lv.get("hints", []):
        for k in keys:
            if k in h:
                leaks.append((fname, "hints泄漏", "", k))
# 顺序答案泄漏检查(P74 同源):排序规则的表述里不得出现具体书号次序
lv_c = json.load(open(os.path.join(OUT, "demo-selfstudy.room.json"), encoding="utf-8"))["level"]
for it in lv_c["items"]:
    blob = (it.get("reason") or "")
    if "Z-02" in blob and ("先" in blob or "第一" in blob or "从小到大" in blob and "Z-05" in blob):
        leaks.append(("demo-selfstudy", "顺序泄漏", it["id"], "具体次序"))
    for k in ("Z-02", "Z-05", "Z-09"):
        if k in blob and it["id"] in ("rc-manual", "rc-scanner", "rc-desk", "rc-npc", "rc-kettle", "rc-stamp", "rc-ticket", "rc-door"):
            leaks.append(("demo-selfstudy", "索书号出现在非书脊物件", it["id"], k))
# 敲击可供性检查(P74):文案只许暗示质感,不许给动作指令或次数
for fname in ("demo-gamenight", "demo-toolbox", "demo-selfstudy"):
    lv = json.load(open(os.path.join(OUT, fname + ".room.json"), encoding="utf-8"))["level"]
    for it in lv["items"]:
        blob = (it.get("reason") or "") + (it.get("title") or "")
        for bad in ("连敲", "三下", "连按", "多敲"):
            if bad in blob:
                leaks.append((fname, "敲击指令泄漏", it["id"], bad))
if leaks:
    print("泄漏自检 FAIL:")
    for l in leaks:
        print("  ", l)
    raise SystemExit(1)
print("泄漏自检 PASS:锁答案未出现在锁自身/premise/objective/hints")
