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

# ============ B 春日工具箱·守库人的遗愿(拼合+电与光+台历接任) ============
# 机制族(与 A/C 零重叠):①撕信拼合(combine, m5 碎纸语法);②angle 接线台灯
#   (规则在拼好的信、数据在端子盘,P67);③灯光后文——灯亮触发房间连锁反应
#   (墙显形+标签屏通电,auto×2);④双语义锁保持 B 本色;⑤台历翻页→接任书收尾(后文 payoff)。
# 房间化:根层只露 素材夹/书桌/正门 3 个容器,单次子节点 ≤4。
items_b = [
    card("tb-clip", "素材夹", "牛皮纸夹里滑出几张打印卡,夹层里还掉出两张撕碎的纸片。"),
    card("tb-card-obs", "宣传卡 · 笔记库", "卡上印着一句英文标语。"),
    card("tb-card-js", "宣传卡 · 语言书", "卡上印着语言课程的介绍,背面空白。"),
    card("tb-paper1", "纸片 · 上", "撕碎的纸片,锯齿边缘。"),
    card("tb-paper2", "纸片 · 下", "撕碎的纸片,锯齿边缘。"),
    card("tb-letter", "完整的信", "两张纸片拼成的信。"),
    card("tb-desk", "书桌", "书房正中的旧书桌。"),
    card("tb-lamp", "台灯", "书桌上的台灯,被人剪断了线。"),
    card("tb-panelbase", "底座端子盘", "台灯底座里的三色接线和端子。"),
    card("tb-calendar", "台历", "台历停在他离开的那天。"),
    card("tb-front", "正门", "笔记库的正门,门上是库门文字屏。"),
    card("tb-gate", "库门文字屏", "库门的文字输入屏。"),
    card("tb-shelf", "书架标签屏", "书架侧面的标签屏,黑着。"),
    card("tb-wall", "守库人的墙", "灯光够到的墙面,贴着两张便签。"),
    card("tb-note-wall1", "便签 · 口令", "守库人的字。"),
    card("tb-note-wall2", "便签 · 标签", "守库人的字。"),
    card("tb-letter-final", "接任书", "折成方胜的一页信纸。"),
]
level_b = {
    "id": "level-demo-toolbox",
    "title": "春日工具箱 · 守库人的遗愿",
    "premise": "2025 年 4 月的春夜,你接手了守库人的旧书房。屋里只点着一盏昏灯——台灯的线被人剪断了,剪口很整齐,像是有意的。素材夹里是他攒下的卡片,夹层里还掉出两张撕碎的纸片。他留过一句话:库门只认原话。",
    "objective": "把撕碎的信拼起来,按信里的话把三根线接回各自的家;灯亮之后,跟着光去墙上找口令的规则,开库门、点书架,最后把台历翻到今天——接下他的委托。",
    "targetMinutes": 14,
    "selectedItemIds": [it["id"] for it in items_b],
    "containers": [
        {"id": "tb-clip", "name": "素材夹", "desc": "牛皮纸夹里滑出几张打印卡,夹层里还掉出两张撕碎的纸片。点击打开素材夹。", "hidden": False},
        {"id": "tb-desk", "name": "书桌", "desc": "书房正中的旧书桌,台面被擦得干干净净。点击走近书桌。", "hidden": False},
        {"id": "tb-front", "name": "正门", "desc": "笔记库的正门,门上是库门文字屏,侧边嵌着书架顶层标签屏。点击走近正门。", "hidden": False},
        {"id": "tb-wall", "name": "守库人的墙", "desc": "灯光够到的墙面——上面贴着两张便签,都是守库人的字。点击走近看。", "hidden": True},
    ],
    "items": [
        li("tb-card-obs", "clue", "线索", "宣传卡 · 笔记库",
           "【网页内容】卡上印着那句英文标语:Sharpen your thinking。下面还有一行中文小字:把思想磨得更锋利。",
           hidden=True, container="tb-clip"),
        li("tb-card-js", "clue", "线索", "宣传卡 · 语言书",
           "【网页内容】卡上印着:主课程包含 2 部分,涵盖 JavaScript 作为一门编程语言和使用浏览器。背面空白——信里没提这张卡。",
           hidden=True, container="tb-clip"),
        li("tb-paper1", "clue", "线索", "纸片 · 上",
           "撕碎的纸片,锯齿边缘还对得上另一半。上半写着:『三根线,三个钟面——』",
           hidden=True, container="tb-clip"),
        li("tb-paper2", "clue", "线索", "纸片 · 下",
           "撕碎的纸片。下半的字迹接着上头,末尾一行被撕去了一半,只看得出『……墙上』两个字。",
           hidden=True, container="tb-clip"),
        li("tb-letter", "clue", "线索", "完整的信",
           "『三根线,三个钟面。我把每个钟面都调过了——你只要把线接回它们的家。别问为什么剪,灯亮之前,这屋里不该被看穿。灯亮之后,替我去看看墙上。都开好了,把台历翻到今天。』",
           hidden=True, auto=True),
        li("tb-lamp", "lock", "锁", "台灯",
           "书桌上的台灯。底座敞着,红、蓝、黄三根线断在半空,线头崭新——是剪断的,不是烧断的。"),
        li("tb-panelbase", "clue", "线索", "底座端子盘",
           "台灯底座里的三色端子,每个旁边嵌着一枚手绘小钟面:红端子的钟面指着 3 点方向,蓝的指着 7 点,黄的指着 11 点。笔迹和撕碎的信是同一个人。"),
        li("tb-calendar", "clue", "线索", "台历",
           "台历停在他离开的那天。今天的页面折了一个角,像在等谁伸手。"),
        li("tb-gate", "lock", "锁", "库门文字屏",
           "笔记库的库门没有锁孔,只有一块文字输入屏,屏上闪烁着一行提示:请输入入库口令。"),
        li("tb-shelf", "lock", "锁", "书架标签屏",
           "书架侧面嵌着一块标签屏:请输入顶层标签。屋里亮起来,它才通电。",
           hidden=True, auto=True),
        li("tb-note-wall1", "clue", "线索", "便签 · 口令",
           "『口令 = 笔记库标语去掉第一个词。那句英文是我最信的一句话——就在素材夹的蓝卡上。』",
           hidden=True, container="tb-wall"),
        li("tb-note-wall2", "clue", "线索", "便签 · 标签",
           "『顶层标签 = 算法书标语的头一个词。整句我抄在下面:动画图解、一键运行的数据结构与算法教程。都开好了,把书桌上的台历翻到今天。』",
           hidden=True, container="tb-wall"),
        li("tb-letter-final", "reward", "奖励", "接任书",
           "折成方胜的一页信纸,展开来——『致接任人:这座库,从今晚起是你的了。书要一本一本读,灯要一晚一晚点。——守库人』",
           hidden=True, auto=True),
    ],
    "beats": [
        {"id": "u1", "title": "打开素材夹", "action": "inspect", "uses": ["tb-clip"],
         "reveals": ["tb-card-obs", "tb-card-js", "tb-paper1", "tb-paper2"]},
        {"id": "u2", "title": "把撕碎的信拼起来", "action": "combine", "uses": ["tb-paper1", "tb-paper2"],
         "requires": ["u1"], "resultOn": "tb-paper1", "product": "完整的信", "consume": ["tb-paper2"],
         "reveals": ["tb-letter"]},
        {"id": "u3", "title": "读完整的信", "action": "inspect", "uses": ["tb-letter"], "requires": ["u2"]},
        {"id": "u4", "title": "走近书桌", "action": "inspect", "uses": ["tb-desk"],
         "reveals": ["tb-lamp", "tb-panelbase", "tb-calendar"]},
        {"id": "u5", "title": "看底座端子盘", "action": "inspect", "uses": ["tb-panelbase"], "requires": ["u4"]},
        {"id": "u6", "title": "把线接回钟面上的家", "action": "angle", "uses": ["tb-lamp"],
         "angles": [90, 210, 330], "precision": 30, "labels": ["红线", "蓝线", "黄线"],
         "requires": ["u3", "u5"], "resultOn": "tb-lamp", "product": "亮起的台灯",
         "reveals": ["tb-wall", "tb-shelf"]},
        {"id": "u7", "title": "走到守库人的墙前", "action": "inspect", "uses": ["tb-wall"],
         "requires": ["u6"], "reveals": ["tb-note-wall1", "tb-note-wall2"]},
        {"id": "u8", "title": "读便签·口令", "action": "inspect", "uses": ["tb-note-wall1"], "requires": ["u7"]},
        {"id": "u9", "title": "读便签·标签", "action": "inspect", "uses": ["tb-note-wall2"], "requires": ["u7"]},
        {"id": "u10", "title": "输入库门口令", "action": "password", "uses": ["tb-gate"], "expected": "your thinking",
         "requires": ["u8"], "resultOn": "tb-gate", "product": "敞开的库门"},
        {"id": "u11", "title": "输入书架顶层标签", "action": "password", "uses": ["tb-shelf"], "expected": "动画图解",
         "requires": ["u9"], "resultOn": "tb-shelf", "product": "亮起顶层标签的书架"},
        {"id": "u12", "title": "把台历翻到今天", "action": "inspect", "uses": ["tb-calendar"],
         "requires": ["u10", "u11"], "resultOn": "tb-calendar", "product": "翻到今天的台历",
         "reveals": ["tb-letter-final"]},
        {"id": "u13", "title": "接下守库人的委托", "action": "deliver", "uses": ["tb-letter-final"], "requires": ["u12"]},
    ],
    "hints": [
        "素材夹的夹层里掉了东西——两张纸片,锯齿对得上。",
        "拼好的信里有灯的线索:线要接回『钟面上的家』。",
        "书桌上就有那盏被剪断的台灯,端子盘上的小钟面是数据。",
        "灯亮之后先别走——墙和标签屏,都会有反应。",
        "库门口令从笔记库卡的原话里取,取法在便签上。",
        "书架标签的头一个词,守库人替你抄好了整句。",
        "两把锁都开好了,就把台历翻到今天——信的最后一句。",
    ],
    "mechanics": ["inspect", "拼合(combine)", "angle(钟面接线)", "灯光后文(auto×2)", "password-text×2", "台历接任"],
}

# ============ C 秋末自学计划·闭馆前的资料室(借阅族:弹书+选择题扫描+NPC) ============
# 机制族:①容器弹书(绿标 3+红标干扰);②选择题扫描——扫描不消耗书(留作参照),
#   扫描台变身显示题干,auto 弹出 3 个备选节点,拖正确项到扫描台=combine 受理,
#   错误项无反应(物理 enforce);作答后备选与书一起归架(consume);③NPC 三件套。
items_c = [
    card("rc-door", "资料室门", "资料室的门虚掩着。点击推门进去。"),
    card("rc-desk", "借阅台", "借阅台空着。"),
    card("rc-manual", "守馆手册", "借阅台上的手册,翻开着。"),
    card("rc-scanner", "扫描台", "借阅台上的扫描台。"),
    card("rc-ticket", "提货单", "借阅系统的提货单。"),
    card("rc-shelfa", "还书车 · 上层", "还书车的上层书架。"),
    card("rc-shelfb", "还书车 · 下层", "还书车的下层书架。"),
    card("rc-book1", "绿标书 · JavaScript指南", "绿标书。"),
    card("rc-book2", "绿标书 · 现代JavaScript教程", "绿标书。"),
    card("rc-book3", "绿标书 · Hello 算法", "绿标书。"),
    card("rc-book4", "红标书 · 五三题库", "红标书。"),
    card("rc-kettle", "保温壶", "挂在车把上的保温壶。"),
    card("rc-o1a", "备选 · JavaScript 参考", "一张答案标签。"),
    card("rc-o1b", "备选 · JavaScript 教程", "一张答案标签。"),
    card("rc-o1c", "备选 · W3School 百科", "一张答案标签。"),
    card("rc-o2a", "备选 · 2 部分", "一张答案标签。"),
    card("rc-o2b", "备选 · 3 部分", "一张答案标签。"),
    card("rc-o2c", "备选 · 5 部分", "一张答案标签。"),
    card("rc-o3a", "备选 · 线性结构", "一张答案标签。"),
    card("rc-o3b", "备选 · 非线性结构", "一张答案标签。"),
    card("rc-o3c", "备选 · 图状结构", "一张答案标签。"),
    card("rc-npc", "值班员", "值夜班的学长。"),
    card("rc-stamp", "借阅章", "黄铜借阅章。"),
]
level_c = {
    "id": "level-demo-selfstudy",
    "title": "秋末自学计划 · 闭馆前的资料室",
    "premise": "2025 年 11 月的傍晚,资料室快闭馆了。还书车上堆着今天回流的书,提货单还没盖章,值班员不知道躲去了哪儿——借阅台后面只留着一壶还温着的茶。窗外天色暗得很快。",
    "objective": "按守馆手册的流程把本批图书逐本扫描、答对机器的校验题;全部受理后找到值班员,把章要出来盖在提货单上,赶在闭馆前交单出室。",
    "targetMinutes": 15,
    "selectedItemIds": [it["id"] for it in items_c],
    "containers": [
        {"id": "rc-shelfa", "name": "还书车 · 上层", "desc": "还书车的上层书架。点击翻一翻,书就滑出来。", "hidden": False, "auto": True},
        {"id": "rc-shelfb", "name": "还书车 · 下层", "desc": "还书车的下层书架,也塞着书。点击翻一翻。", "hidden": False, "auto": True},
        {"id": "rc-desk", "name": "借阅台", "desc": "借阅台空着,台面收拾得整整齐齐。点击走近借阅台。", "hidden": False, "auto": True},
    ],
    "items": [
        li("rc-door", "clue", "线索", "资料室门", "资料室的门虚掩着,门缝里漏出旧纸的味道。点击推门进去。"),
        li("rc-manual", "clue", "线索", "守馆手册",
           "【流程页】今晚归还批次:贴绿标的三本。流程:逐本放上扫描台——机器会出校验题,并弹出三张备选标签;把对的那张拖到扫描台上,才算受理。答案都在书自己的卡片里。受理次序就是学习的次序:概述在前,主课程在中,算法进阶在后。全部受理后系统响铃,值班员自然会来。备注:章不外借,但他那个人,只认热茶。",
           hidden=True, container="rc-desk"),
        li("rc-scanner", "tool", "工具", "扫描台",
           "借阅台上的扫描台,指示灯待机闪烁。把书平放上去就能扫——但每扫一本,它都要先考你一道题。",
           hidden=True, container="rc-desk"),
        li("rc-ticket", "transform", "结果", "提货单",
           "借阅系统的提货单,空白处等着盖章。盖了章的单子才能交出去。",
           hidden=True, container="rc-desk"),
        li("rc-book1", "clue", "线索", "绿标书 · JavaScript指南",
           "【网页内容·书脊】JavaScript 指南——向你介绍如何使用 JavaScript,并且给出了语言概述。想深入了解语言特性的详细信息?它让你去参阅 JavaScript 参考。",
           hidden=True, container="rc-shelfa"),
        li("rc-book3", "clue", "线索", "绿标书 · Hello 算法",
           "【网页内容·书脊】3.1 数据结构分类——动画图解、一键运行的数据结构与算法教程。书里把数组、链表、栈、队列都归了类。想核对答案?打开原收藏,翻到 3.1 节。",
           hidden=True, container="rc-shelfa"),
        li("rc-book2", "clue", "线索", "绿标书 · 现代JavaScript教程",
           "【网页内容·书脊】主课程包含 2 部分,涵盖 JavaScript 作为一门编程语言和使用浏览器。还有一些额外的主题文章系列。",
           hidden=True, container="rc-shelfb"),
        li("rc-book4", "clue", "线索", "红标书 · 五三题库",
           "红标。《五年高考·三年模拟》。和这个房间格格不入,像是谁忘在这儿的。手册说今晚只收绿标。",
           hidden=True, container="rc-shelfb"),
        li("rc-kettle", "tool", "工具", "保温壶",
           "挂在下层书架车把上的保温壶,摸着还温。守馆人走前泡的茶,一口没动。",
           hidden=True, container="rc-shelfb"),
        li("rc-o1a", "clue", "线索", "备选 · JavaScript 参考",
           "一张可拖动的答案标签,出自《JavaScript 指南》的指引。", hidden=True, auto=True),
        li("rc-o1b", "clue", "线索", "备选 · JavaScript 教程",
           "一张可拖动的答案标签。看着眼熟,但未必是这本指南说的那个。", hidden=True, auto=True),
        li("rc-o1c", "clue", "线索", "备选 · W3School 百科",
           "一张可拖动的答案标签。和指南没什么关系,凑数的味道。", hidden=True, auto=True),
        li("rc-o2a", "clue", "线索", "备选 · 2 部分",
           "一张可拖动的答案标签。", hidden=True, auto=True),
        li("rc-o2b", "clue", "线索", "备选 · 3 部分",
           "一张可拖动的答案标签。", hidden=True, auto=True),
        li("rc-o2c", "clue", "线索", "备选 · 5 部分",
           "一张可拖动的答案标签。", hidden=True, auto=True),
        li("rc-o3a", "clue", "线索", "备选 · 线性结构",
           "一张可拖动的答案标签。", hidden=True, auto=True),
        li("rc-o3b", "clue", "线索", "备选 · 非线性结构",
           "一张可拖动的答案标签。", hidden=True, auto=True),
        li("rc-o3c", "clue", "线索", "备选 · 图状结构",
           "一张可拖动的答案标签。", hidden=True, auto=True),
        li("rc-npc", "clue", "线索", "值班员",
           "『都扫完啦?』值夜班的学长端着茶杯,从借阅台那头踱了过来。『归架章在我身上,不外借——除非……你懂的吧?这壶茶闻着正好。』",
           hidden=True, auto=True),
        li("rc-stamp", "tool", "工具", "借阅章",
           "黄铜借阅章,章面刻着『已归架』,把手上缠着防滑绳。值班员塞给你的。", hidden=True, auto=True),
    ],
    "beats": [
        {"id": "c1", "title": "推开资料室", "action": "inspect", "uses": ["rc-door"],
         "reveals": ["rc-shelfa", "rc-shelfb", "rc-desk"]},
        {"id": "c2", "title": "读守馆手册", "action": "inspect", "uses": ["rc-manual"], "requires": ["c1"]},
        {"id": "c3", "title": "翻上层书架", "action": "inspect", "uses": ["rc-shelfa"],
         "requires": ["c1"], "reveals": ["rc-book1", "rc-book3"]},
        {"id": "c4", "title": "翻下层书架", "action": "inspect", "uses": ["rc-shelfb"],
         "requires": ["c1"], "reveals": ["rc-book2", "rc-book4", "rc-kettle"]},
        {"id": "c5", "title": "看《JavaScript 指南》卡片", "action": "inspect", "uses": ["rc-book1"], "requires": ["c3"]},
        {"id": "c6", "title": "看《现代JavaScript教程》卡片", "action": "inspect", "uses": ["rc-book2"], "requires": ["c4"]},
        {"id": "c7", "title": "看《Hello 算法》卡片", "action": "inspect", "uses": ["rc-book3"], "requires": ["c3"]},
        {"id": "c8", "title": "扫描第一本(概述)", "action": "combine", "uses": ["rc-book1", "rc-scanner"],
         "requires": ["c2", "c5"], "resultOn": "rc-scanner", "product": "校验中:该参阅什么?",
         "reveals": ["rc-o1a", "rc-o1b", "rc-o1c"]},
        {"id": "c9", "title": "拖入正确备选(一)", "action": "combine", "uses": ["rc-o1a", "rc-scanner"],
         "requires": ["c8"], "resultOn": "rc-scanner", "product": "扫描台 · 已受理 1/3",
         "consume": ["rc-o1a", "rc-o1b", "rc-o1c", "rc-book1"]},
        {"id": "c10", "title": "扫描第二本(主课程)", "action": "combine", "uses": ["rc-book2", "rc-scanner"],
         "requires": ["c9", "c6"], "resultOn": "rc-scanner", "product": "校验中:这门课分几部分?",
         "reveals": ["rc-o2a", "rc-o2b", "rc-o2c"]},
        {"id": "c11", "title": "拖入正确备选(二)", "action": "combine", "uses": ["rc-o2a", "rc-scanner"],
         "requires": ["c10"], "resultOn": "rc-scanner", "product": "扫描台 · 已受理 2/3",
         "consume": ["rc-o2a", "rc-o2b", "rc-o2c", "rc-book2"]},
        {"id": "c12", "title": "扫描第三本(算法)", "action": "combine", "uses": ["rc-book3", "rc-scanner"],
         "requires": ["c11", "c7"], "resultOn": "rc-scanner", "product": "校验中:它们归哪一类?",
         "reveals": ["rc-o3a", "rc-o3b", "rc-o3c"]},
        {"id": "c13", "title": "拖入正确备选(三)", "action": "combine", "uses": ["rc-o3a", "rc-scanner"],
         "requires": ["c12"], "resultOn": "rc-scanner", "product": "扫描台 · 已受理 3/3",
         "consume": ["rc-o3a", "rc-o3b", "rc-o3c", "rc-book3"], "reveals": ["rc-npc"]},
        {"id": "c14", "title": "和值班员搭话", "action": "inspect", "uses": ["rc-npc"], "requires": ["c13"]},
        {"id": "c15", "title": "把保温壶递给他", "action": "combine", "uses": ["rc-kettle", "rc-npc"],
         "requires": ["c14"], "resultOn": "rc-npc", "product": "捧着热茶的值班员",
         "consume": ["rc-kettle"], "reveals": ["rc-stamp"]},
        {"id": "c16", "title": "盖归架章", "action": "combine", "uses": ["rc-stamp", "rc-ticket"],
         "requires": ["c15"], "resultOn": "rc-ticket", "product": "盖章的提货单", "consume": ["rc-stamp"]},
        {"id": "c17", "title": "闭馆前交单", "action": "deliver", "uses": ["result:c16"], "requires": ["c16"]},
    ],
    "hints": [
        "推门进去,三个位置都会亮出来:两辆还书车和一张借阅台。",
        "还书车的两层都要翻——书会自己滑出来,认准绿色书标。",
        "红标那本和今晚无关;扫描的次序是学习的次序:概述、主课程、算法。",
        "扫描后书不会被收走——它就是答案的参照物,卡片读仔细。",
        "机器弹出三张备选标签,把对的拖到扫描台上;拖错的它不理你。",
        "第三题拿不准,就打开那本书的原收藏翻到 3.1 节。",
        "全部受理后系统会响铃——等等看,会有人出现。",
        "值班员的话里有话:他缺的东西,还书车车把上正好挂着。",
        "章到手,盖单,赶在闭馆前出门。",
    ],
    "mechanics": ["inspect", "容器弹书×2", "选择题扫描×3(拖备选到题干,书留作参照)", "NPC(现身/对话/交易)", "auto显形"],
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
    "demo-selfstudy": ["JavaScript 参考", "线性"],  # 答案只在书卡原话/原页面;『2』太通用不查
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
# 校验题泄漏检查(P67 同源):答案不得出现在题目卡/手册/机器上;『线性』只许来自原页面
lv_c = json.load(open(os.path.join(OUT, "demo-selfstudy.room.json"), encoding="utf-8"))["level"]
for it in lv_c["items"]:
    blob = (it.get("reason") or "") + (it.get("title") or "")
    if "线性" in blob and it["id"] not in ("rc-o3a", "rc-o3b"):  # o3b=『非线性』含子串
        leaks.append(("demo-selfstudy", "校验答案出现在文案里", it["id"], "线性"))
    if "JavaScript 参考" in blob and it["id"] not in ("rc-book1", "rc-o1a"):
        leaks.append(("demo-selfstudy", "答案出现在非数据卡", it["id"], "JavaScript 参考"))
# 容器双写检查(P83,三次踩坑后固化为机器检查):容器 id 只许出现在 containers
for fname in ("demo-gamenight", "demo-toolbox", "demo-selfstudy"):
    lv = json.load(open(os.path.join(OUT, fname + ".room.json"), encoding="utf-8"))["level"]
    cids = {c["id"] for c in lv.get("containers", [])}
    for it in lv["items"]:
        if it["id"] in cids:
            leaks.append((fname, "容器 id 双写(items)", it["id"], "双节点渲染"))
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
