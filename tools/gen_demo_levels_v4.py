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

# ============ B 春日工具箱 · 知识库建成之夜(语义文字) ============
items_b = [
    card("tb-card-obs", "宣传卡 · 笔记库", "卡上印着一句英文标语,下面还有一行中文小字。"),
    card("tb-card-algo", "宣传卡 · 算法书", "卡上印着算法教程的标语,角落画着一个会动的小人。"),
    card("tb-card-js", "宣传卡 · 语言书", "卡上印着语言课程的介绍,背面空白,像还有下文。"),
    card("tb-manual", "入库规则卡", "馆长手书:口令与标签的取法都写在上面。"),
    card("tb-gate", "库门文字屏", "笔记库的库门没有锁孔,只有一块文字输入屏。"),
    card("tb-shelf", "书架标签屏", "书架侧面嵌着一块标签屏,库门开了它才通电。"),
    card("tb-desk", "书桌", "空书桌等着建成仪式。"),
    card("tb-note", "藏书票", "一枚烫金藏书票,票面上印着『我的第一座笔记库』。"),
]
level_b = {
    "id": "level-demo-toolbox",
    "title": "春日工具箱 · 知识库建成之夜",
    "premise": "2025 年 4 月的春夜,你决定把散落各处的收藏整理成一座私人笔记库。素材夹里的几张打印卡还带着打印机的余温——库门和书架都不认钥匙,只认卡片上的原话。",
    "objective": "打开素材夹,读宣传卡与入库规则卡,推导库门口令与书架标签,取出藏书票插上书桌,建成你的笔记库。",
    "targetMinutes": 12,
    "selectedItemIds": [it["id"] for it in items_b],
    "containers": [
        {
            "id": "tb-clip",
            "name": "素材夹",
            "desc": "牛皮纸夹里滑出几张打印卡。点击打开素材夹。",
            "hidden": False,
        }
    ],
    "items": [
        li("tb-card-obs", "clue", "线索", "宣传卡 · 笔记库",
           "【网页内容】卡上印着那句英文标语:Sharpen your thinking。下面还有一行中文小字:把思想磨得更锋利。",
           hidden=True, container="tb-clip"),
        li("tb-card-algo", "clue", "线索", "宣传卡 · 算法书",
           "【网页内容】卡上印着:动画图解、一键运行的数据结构与算法教程。角落画着一个会动的小人在排序。",
           hidden=True, container="tb-clip"),
        li("tb-card-js", "clue", "线索", "宣传卡 · 语言书",
           "【网页内容】卡上印着:主课程包含 2 部分,涵盖 JavaScript 作为一门编程语言和使用浏览器。背面空白,像还有下文——可惜规则卡只提到另外两张。",
           hidden=True, container="tb-clip"),
        li("tb-manual", "clue", "线索", "入库规则卡",
           "【规则页】馆长手书:入库口令 = 笔记库标语去掉第一个词;书架顶层标签 = 算法书标语的头一个词。口令与标签都对上,库才算建成。",
           hidden=True, container="tb-clip"),
        li("tb-gate", "lock", "锁", "库门文字屏",
           "笔记库的库门没有锁孔,只有一块文字输入屏,屏上闪烁着一行提示:请输入入库口令。"),
        li("tb-shelf", "lock", "锁", "书架标签屏",
           "书架侧面嵌着一块标签屏:请输入顶层标签。库门开了它才通电。"),
        li("tb-desk", "transform", "结果", "书桌",
           "空书桌等着建成仪式。把藏书票插上去,它就是笔记库的正门。"),
        li("tb-note", "tool", "工具", "藏书票",
           "一枚烫金藏书票,票面上印着『我的第一座笔记库』。该把它插上书桌了。", hidden=True),
    ],
    "beats": [
        {"id": "t1", "title": "打开素材夹", "action": "inspect", "uses": ["tb-clip"],
         "reveals": ["tb-card-obs", "tb-card-algo", "tb-card-js", "tb-manual"]},
        {"id": "t2", "title": "读笔记库宣传卡", "action": "inspect", "uses": ["tb-card-obs"], "requires": ["t1"]},
        {"id": "t3", "title": "读入库规则卡", "action": "inspect", "uses": ["tb-manual"], "requires": ["t1"]},
        {"id": "t4", "title": "输入库门口令", "action": "password", "uses": ["tb-gate"], "expected": "your thinking",
         "requires": ["t2", "t3"]},
        {"id": "t5", "title": "读算法书宣传卡", "action": "inspect", "uses": ["tb-card-algo"], "requires": ["t4"]},
        {"id": "t6", "title": "输入书架顶层标签", "action": "password", "uses": ["tb-shelf"], "expected": "动画图解",
         "requires": ["t3", "t5"], "reveals": ["tb-note"]},
        {"id": "t7", "title": "插上藏书票", "action": "combine", "uses": ["tb-note", "tb-desk"],
         "requires": ["t6"], "resultOn": "tb-desk", "product": "建成的笔记库", "consume": ["tb-note"]},
        {"id": "t8", "title": "宣告笔记库建成", "action": "deliver", "uses": ["result:t7"], "requires": ["t7"]},
    ],
    "hints": [
        "素材夹里的卡不止一张——每张都要读。",
        "入库规则卡是两把锁的总说明,口令和标签的取法都写在上面。",
        "库门口令要从笔记库宣传卡的原话里取,注意规则卡说的取法。",
        "进了门再看算法书卡——书架标签同样从原话里取。",
        "书架通了电,藏书票才有地方放。",
        "藏书票插上书桌,笔记库就算建成,把成品交付出去。",
    ],
    "mechanics": ["inspect", "password-text×2", "combine"],
}

# ============ C 秋末自学计划 · 资料室排架日(排序 sequence) ============
items_c = [
    card("rc-door", "资料室门", "资料室的门虚掩着,门缝里能看到书车。点击推门进去。"),
    card("rc-manual", "排架规则卡", "资料室的排架次序按课程大纲来,只收一对书。"),
    card("rc-book-js", "语言书 · 现代JavaScript教程", "书脊印着课程介绍:一部分讲语言本身,一部分讲浏览器。"),
    card("rc-book-web", "手册 · JavaScript指南", "书脊印着『JavaScript 指南』,讲语言在浏览器里的用法。"),
    card("rc-book-algo", "算法书 · Hello 算法", "书脊印着:动画图解、一键运行的数据结构与算法教程。"),
    card("rc-shelf", "排架台", "排架台的凹槽刻着 ①② 两个位置,连着借阅系统。"),
    card("rc-stamp", "借阅章", "黄铜借阅章,章面刻着『已排架』。"),
    card("rc-ticket", "提货单", "借阅系统的提货单,空白处等着盖章。"),
]
level_c = {
    "id": "level-demo-selfstudy",
    "title": "秋末自学计划 · 资料室排架日",
    "premise": "2025 年 11 月,你终于腾出一个下午整理自学资料。资料室的书车停在门口,排架台连着借阅系统——它只按排架规则认书:放对了,借阅章才会从台下弹出来。",
    "objective": "推开资料室,读排架规则与书脊,把对的两本书按次序排上书架,取出借阅章盖在提货单上,交单出室。",
    "targetMinutes": 10,
    "selectedItemIds": [it["id"] for it in items_c],
    "containers": [],
    "items": [
        li("rc-door", "clue", "线索", "资料室门", "资料室的门虚掩着,门缝里漏出旧纸的味道。点击推门进去。"),
        li("rc-manual", "clue", "线索", "排架规则卡",
           "【规则页】资料室只收一对书:凹槽①放那本『先讲语言本身』的书,凹槽②放那本『讲浏览器里的用法』的书。次序放反,书会滑回来。",
           hidden=True),
        li("rc-book-js", "clue", "线索", "语言书 · 现代JavaScript教程",
           "【网页内容·书脊】主课程包含 2 部分,涵盖 JavaScript 作为一门编程语言和使用浏览器。第一部分讲语言本身,第二部分才讲浏览器。",
           hidden=True),
        li("rc-book-web", "clue", "线索", "手册 · JavaScript指南",
           "【网页内容·书脊】JavaScript 指南——讲的是这门语言在浏览器里的用法,是语言书的下一站。",
           hidden=True),
        li("rc-book-algo", "clue", "线索", "算法书 · Hello 算法",
           "【网页内容·书脊】动画图解、一键运行的数据结构与算法教程。可惜排架规则只收一对书,它今天只能留在书车上。",
           hidden=True),
        li("rc-shelf", "tool", "工具", "排架台",
           "排架台的凹槽刻着 ①② 两个位置。把书按次序放上去——点错了顺序,整组会重来。"),
        li("rc-stamp", "tool", "工具", "借阅章",
           "黄铜借阅章,章面刻着『已排架』。排架台认可之后,它才会从台下弹出来。", hidden=True),
        li("rc-ticket", "transform", "结果", "提货单",
           "借阅系统的提货单,空白处等着盖章。盖了章的单子才能交给出入口。", hidden=True),
    ],
    "beats": [
        {"id": "c1", "title": "推开资料室", "action": "inspect", "uses": ["rc-door"],
         "reveals": ["rc-manual", "rc-book-js", "rc-book-web", "rc-book-algo", "rc-ticket"]},
        {"id": "c2", "title": "读排架规则卡", "action": "inspect", "uses": ["rc-manual"], "requires": ["c1"]},
        {"id": "c3", "title": "查看语言书书脊", "action": "inspect", "uses": ["rc-book-js"], "requires": ["c1"]},
        {"id": "c4", "title": "查看手册书脊", "action": "inspect", "uses": ["rc-book-web"], "requires": ["c1"]},
        {"id": "c5", "title": "按次序排架", "action": "sequence", "uses": ["rc-book-js", "rc-book-web"],
         "requires": ["c2", "c3", "c4"], "resultOn": "rc-shelf", "product": "排好架的一对书",
         "reveals": ["rc-stamp"]},
        {"id": "c6", "title": "盖借阅章", "action": "combine", "uses": ["rc-stamp", "rc-ticket"],
         "requires": ["c5"], "resultOn": "rc-ticket", "product": "盖章的提货单", "consume": ["rc-stamp"]},
        {"id": "c7", "title": "交单出室", "action": "deliver", "uses": ["result:c6"], "requires": ["c6"]},
    ],
    "hints": [
        "资料室的门要自己推开——里面的书车和规则卡都会现身。",
        "排架规则卡说明了次序,以及『只收一对书』。",
        "两本书的书脊都读一读,才能分清哪本先讲语言、哪本讲浏览器。",
        "排架台要按次序逐个点击,点错整组重来。",
        "排对了,借阅章会从台下弹出来——把它盖到提货单上。",
        "盖章的提货单才能交给出入口。",
    ],
    "mechanics": ["inspect", "sequence", "combine"],
}

# 容器 id 约定(与教程关一致):只出现在 level.containers,不进 items/controlledIds/selectedItemIds
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
    "demo-toolbox": ["your thinking", "动画图解"],
    "demo-selfstudy": ["rc-book-js", "rc-book-web"],  # 顺序答案=两本书的出现次序
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
