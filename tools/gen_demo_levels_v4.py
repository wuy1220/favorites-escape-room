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


def li(id, role, roleLabel, title, reason, hidden=False, container=None):
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
    return it


# ============ A 深秋游戏之夜 · 末班点播台(计量合成) ============
items_a = [
    card("ra-cabinet", "怀旧游戏柜", "玻璃柜里躺着卡带和几张卡纸。点击打开玻璃柜,取出里面的东西。"),
    card("ra-archive", "唱片档案卡", "卡片印着这首歌的实时档案:播放量与弹幕总量。数字右下角还有一行小注。"),
    card("ra-manual", "检修手册", "手册第 7 页写着点播台的调谐规则:一个数管频率,一个数管音轨。"),
    card("ra-tape", "卡带 A · Never Gonna Give You Up", "卡带标签磨得发白,还能看清歌名。装进点唱机,它才肯开口。"),
    card("ra-machine", "老点唱机", "点唱机的卡带舱积着灰,面板连着两个调谐盘:一个管频率,一个管音轨。"),
    card("ra-panel", "频率面板", "点播台的频率面板,四位数字转盘。调准了,整座城市都能听见这首老歌。"),
    card("ra-trackpanel", "音轨面板", "音轨面板,三位数字转盘。频率调准后它才通电。"),
    card("ra-disc", "MMD 光碟 · Treasure", "压轴的光碟:重巡 Pola 的「Treasure」。光碟盒上贴着投递口的标签。"),
]
level_a = {
    "id": "level-demo-gamenight",
    "title": "深秋游戏之夜 · 末班点播台",
    "premise": "2024 年 11 月的深夜,你在游戏堆里过了一整晚。今晚,你想把那段 Never Gonna Give You Up 点播给整座城市的失眠者,还要让压轴的 MMD 光碟一起出发。点播台的老机器只认数据——档案上印什么,它就要什么。",
    "objective": "打开怀旧柜,读档案卡与检修手册,把卡带装进点唱机,再按手册的规则调准两个面板,取出压轴光碟投递出去。",
    "targetMinutes": 10,
    "selectedItemIds": [it["id"] for it in items_a],
    "containers": [
        {
            "id": "ra-cabinet",
            "name": "怀旧游戏柜",
            "desc": "玻璃柜里躺着卡带和几张卡纸。点击打开它,再点一次取出来。",
            "hidden": False,
        }
    ],
    "items": [
        li("ra-cabinet", "clue", "线索", "怀旧游戏柜", "玻璃柜里躺着卡带和几张卡纸。点击打开玻璃柜,再点一次取出里面的东西。"),
        li("ra-archive", "clue", "线索", "唱片档案卡",
           "【网页内容·数据条】卡片印着这首歌的实时档案:视频播放量 104610374,弹幕总量 148416。数字右下角还有一行小注:『以档案为准。』",
           hidden=True, container="ra-cabinet"),
        li("ra-manual", "clue", "线索", "检修手册",
           "【规则页】手册第 7 页写着:点播台的热线频率 = 播放量的前四位;音轨编号 = 弹幕总量的后三位。调错一位,机器都会沉默。",
           hidden=True, container="ra-cabinet"),
        li("ra-tape", "tool", "工具", "卡带 A · Never Gonna Give You Up",
           "卡带标签磨得发白,还能看清歌名。把它装进点唱机,机器才肯工作。",
           hidden=True, container="ra-cabinet"),
        li("ra-machine", "transform", "结果", "老点唱机",
           "点唱机的卡带舱积着灰,面板连着两个调谐盘:一个管频率,一个管音轨。先给它装上卡带。"),
        li("ra-panel", "lock", "锁", "频率面板",
           "点播台的频率面板,四位数字转盘。调准了,整座城市都能听见这首老歌。"),
        li("ra-trackpanel", "lock", "锁", "音轨面板",
           "音轨面板,三位数字转盘。频率调准后它才通电,盘面泛着幽幽的绿光。", hidden=True),
        li("ra-disc", "reward", "奖励", "MMD 光碟 · Treasure",
           "压轴的光碟:重巡 Pola 的「Treasure」。光碟盒上贴着投递口的标签,像在催你快点。", hidden=True),
    ],
    "beats": [
        {"id": "a1", "title": "打开怀旧游戏柜", "action": "inspect", "uses": ["ra-cabinet"],
         "reveals": ["ra-archive", "ra-manual", "ra-tape"]},
        {"id": "a2", "title": "读唱片档案卡", "action": "inspect", "uses": ["ra-archive"], "requires": ["a1"]},
        {"id": "a3", "title": "读检修手册", "action": "inspect", "uses": ["ra-manual"], "requires": ["a1"]},
        {"id": "a4", "title": "把卡带装进点唱机", "action": "combine", "uses": ["ra-tape", "ra-machine"],
         "requires": ["a1"], "resultOn": "ra-machine", "product": "就绪的点唱机", "consume": ["ra-tape"]},
        {"id": "a5", "title": "调准频率面板", "action": "password", "uses": ["ra-panel"], "expected": "1046",
         "requires": ["a2", "a3", "a4"], "reveals": ["ra-trackpanel"]},
        {"id": "a6", "title": "选定音轨编号", "action": "password", "uses": ["ra-trackpanel"], "expected": "416",
         "requires": ["a3", "a5"], "reveals": ["ra-disc"]},
        {"id": "a7", "title": "投递压轴光碟", "action": "deliver", "uses": ["ra-disc"], "requires": ["a6"]},
    ],
    "hints": [
        "怀旧游戏柜还没打开——柜子里的东西是这一切的起点。",
        "档案卡和手册要都读一遍:一个给数据,一个给规则。",
        "光有卡带不行,点唱机得先装上它才肯工作。",
        "频率面板的数字要从档案卡里来,取法在手册上写着。",
        "音轨面板在频率调准后才会通电——同样是档案上的数字,取法不同。",
        "压轴光碟出现后,把它拖到出口投递。",
    ],
    "mechanics": ["inspect", "combine", "password×2"],
}

# ============ B 春日工具箱 · 知识库建成之夜(语义文字) ============
items_b = [
    card("tb-clip", "素材夹", "牛皮纸夹里滑出几张打印卡。点击打开素材夹。"),
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
        li("tb-clip", "clue", "线索", "素材夹", "牛皮纸夹里滑出几张打印卡。点击打开素材夹,把卡都翻一遍。"),
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
    "demo-gamenight": ["1046", "416", "104610374", "148416"],
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
if leaks:
    print("泄漏自检 FAIL:")
    for l in leaks:
        print("  ", l)
    raise SystemExit(1)
print("泄漏自检 PASS:锁答案未出现在锁自身/premise/objective/hints")
