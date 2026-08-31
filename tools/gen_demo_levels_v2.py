# -*- coding: utf-8 -*-
"""三关演示重设计:每关主打一种理解动作,全部锚定真实网页内容。"""
import json


def item(id, role, scene_name, reason, hidden=False, container=None):
    d = {"id": id, "role": role,
         "roleLabel": {"clue": "线索", "tool": "工具", "lock": "锁", "reward": "结果"}.get(role, "线索"),
         "title": scene_name, "sceneName": scene_name, "reason": reason, "hidden": hidden}
    if container:
        d["container"] = container
    return d


def draft_item(id, scene_name, desc, domain):
    return {"id": id, "title": scene_name, "domain": domain, "dateAdded": "",
            "url": "", "urlPath": "", "description": desc}


def base_level():
    return {"id": "", "title": "", "premise": "", "objective": "", "targetMinutes": 8,
            "selectedItemIds": [], "containers": [], "items": [], "beats": [], "scenes": [],
            "mechanics": [], "hints": [], "validation": {"valid": True, "issues": []},
            "grounding": "demo"}


LEVELS = {}

# ============ 关卡 1《深秋游戏之夜》主打: 计量锁(password) ============
# 网页内容: B 站 MV 页的真实播放数据条(播放量 104610374 / 弹幕 148383 / 硬币 1260911)
# 谜题: 频率面板要"播放量的前四位" → 1046
L1 = base_level()
L1.update({
    "id": "level-demo-gamenight",
    "title": "深秋游戏之夜 · 末班点播台",
    "premise": "2024 年 11 月的深夜,你在游戏堆里过了一整晚。今晚,你想把那段 Never Gonna Give You Up 点播给整座城市的失眠者。点播台的老机器还亮着灯——它只认数据:播放量,一个都不能错。",
    "objective": "打开怀旧柜取出磁带,读懂数据条上的播放量,把磁带装进点唱机,再按播放量的前四位调准频率面板,完成末班点播。",
    "targetMinutes": 8,
    "selectedItemIds": ["ra-cabinet", "ra-tape", "ra-machine", "ra-poster", "ra-panel"],
    "containers": [
        {"id": "ra-cabinet", "name": "怀旧游戏柜", "desc": "玻璃柜里躺着你的卡带。点击打开它,再点一次取出来。", "hidden": False},
    ],
    "items": [
        item("ra-cabinet", "clue", "怀旧游戏柜", "玻璃柜里躺着卡带。点击打开玻璃柜,再点一次取出里面的东西。"),
        item("ra-tape", "clue", "卡带 A · Never Gonna Give You Up",
             "【网页内容·数据条】标签印着:视频播放量 104610374。这串数字,就是点播台要的频率数据。",
             hidden=True, container="ra-cabinet"),
        item("ra-machine", "tool", "老点唱机", "老点唱机的卡带舱积着灰。把要点的卡带装进去,它才能工作。"),
        item("ra-poster", "clue", "游侠网海报", "海报是游侠网的旧宣传画,角落印着一行小字:点播台的热线频率 = 播放量的前四位。"),
        item("ra-panel", "lock", "频率面板", "点播台的频率面板,四位数字转盘。调准了,整座城市都能听见这首老歌。"),
    ],
    "beats": [
        {"id": "a1", "title": "打开怀旧柜", "action": "inspect", "uses": ["ra-cabinet"], "requires": [],
         "reveals": ["ra-tape"], "product": "敞开的怀旧柜"},
        {"id": "a2", "title": "读卡带数据条", "action": "inspect", "uses": ["ra-tape"], "requires": ["a1"],
         "product": "读过数据的卡带 A"},
        {"id": "a3", "title": "读游侠网海报", "action": "inspect", "uses": ["ra-poster"], "requires": [],
         "product": "细读过的海报"},
        {"id": "a4", "title": "卡带装进点唱机", "action": "combine", "uses": ["ra-tape", "ra-machine"],
         "requires": ["a2"], "consume": ["ra-tape"], "resultOn": "ra-machine", "product": "就绪的点唱机"},
        {"id": "a5", "title": "调准频率 1046", "action": "password", "uses": ["ra-panel"],
         "requires": ["a3", "a4"], "expected": "1046", "deriveFrom": ["ra-tape"],
         "product": "接通的热线"},
        {"id": "a6", "title": "完成末班点播", "action": "deliver", "uses": ["result:a5"], "requires": ["a5"]},
    ],
    "mechanics": ["inspect", "combine", "password", "deliver"],
    "hints": [
        "玻璃柜里有卡带,点两次取出来。",
        "海报角落写着:频率 = 播放量的前四位。",
        "点卡带看数据条,记住播放量。",
        "把卡带装进点唱机,再调频率 1046。"
    ],
})
LEVELS["gamenight"] = L1

# ============ 关卡 2《春日工具箱》主打: 识别配对(combine 多候选) ============
# 网页内容: Obsidian 官网 "基于 Markdown 文件的个人知识库" + 菜鸟教程 "本地文件存储"
# 谜题: 工具桌上散落三个候选,只有一个(Obsidian 安装盘)能装进底座
L2 = base_level()
L2.update({
    "id": "level-demo-toolbox",
    "title": "春日工具箱 · 知识库之夜",
    "premise": "2025 年 4 月,你决定给自己的知识建一座房子。工具桌上摊着教程页和效率卡,旁边散落三个组件——但只有一个能装进底座:选错了就装不上。",
    "objective": "认出正确组件(基于 Markdown 文件的个人知识库),拖到底座上组装,再用年份密码 2026 开锁交付。",
    "targetMinutes": 8,
    "selectedItemIds": ["tb-desk", "tb-note", "tb-tutorial", "tb-installer", "tb-cloud", "tb-chat", "tb-lock"],
    "containers": [
        {"id": "tb-desk", "name": "知识库底座", "desc": "底座上有一个凹槽,形状像一块扁平的盘。旁边散落三个组件。", "hidden": False},
    ],
    "items": [
        item("tb-clip", "clue", "知乎专栏剪报", "剪报的路径印着:/p/2026071811813643264——开头的年份,就是底座锁的密码。"),
        item("tb-tutorial", "clue", "Obsidian 教程页",
             "菜鸟教程的 Obsidian 篇写着:基于 Markdown 文件的个人知识库,本地文件存储。装上它,知识就有了家。"),
        item("tb-installer", "tool", "Obsidian 安装盘",
             "银色安装盘,标签写着:Obsidian——Sharpen your thinking。它是基于 Markdown 文件的。", hidden=True, container="tb-desk"),
        item("tb-cloud", "tool", "云端文档夹", "云端文档的封面。不是本地文件——和底座凹槽对不上。"),
        item("tb-chat", "tool", "聊天记录册", "聊天记录的打印册。也不是底座要的东西。"),
        item("tb-lock", "lock", "年份锁", "底座的年份锁:四位数字。剪报路径的开头就是答案。", hidden=True, container="tb-desk"),
    ],
    "beats": [
        {"id": "b1", "title": "读知乎剪报", "action": "inspect", "uses": ["tb-clip"], "requires": [],
         "product": "细读过的剪报"},
        {"id": "b2", "title": "读 Obsidian 教程页", "action": "inspect", "uses": ["tb-tutorial"],
         "requires": [], "product": "读过的教程页"},
        {"id": "b3", "title": "打开工具桌", "action": "inspect", "uses": ["tb-desk"], "requires": [],
         "reveals": ["tb-installer", "tb-lock"], "product": "敞开的工具桌"},
        {"id": "b4", "title": "装上 Obsidian", "action": "combine", "uses": ["tb-installer", "tb-desk"],
         "requires": ["b2", "b3"], "consume": ["tb-installer"], "resultOn": "tb-desk",
         "product": "建成的知识库"},
        {"id": "b5", "title": "开年份锁", "action": "password", "uses": ["tb-lock"], "requires": ["b1", "b4"],
         "expected": "2026", "deriveFrom": ["tb-clip"], "product": "解锁的知识库"},
        {"id": "b6", "title": "备份交付", "action": "deliver", "uses": ["result:b5"], "requires": ["b5"]},
    ],
    "mechanics": ["inspect", "combine", "password", "deliver"],
    "hints": [
        "教程页写着:基于 Markdown 文件的个人知识库。",
        "三个组件里只有一个能装进底座——选错了装不上。",
        "剪报路径以 2026 开头;底座的年份锁要四位。"
    ],
})
LEVELS["toolbox"] = L2

# ============ 关卡 3《秋末自学计划》主打: 排序(sequence) + 计量(password) ============
# 网页内容: Hello 算法 3.1 数据结构分类(数组/链表/栈/队列) + 现代JS教程(2 部分)
# 谜题: 学习保险箱密码 = 3.1 的 31 + 教程部分数 2 → 312; 序列锁按"数组→链表→树"顺序
L3 = base_level()
L3.update({
    "id": "level-demo-selfstudy",
    "title": "秋末自学计划 · 数据结构之夜",
    "premise": "2025 年 9 月,你决定系统自学编程。桌上摊着算法书、蓝皮手册和廖雪峰的笔记。学习保险箱要按正确顺序输入三张分类卡,密码是 31 接 2。",
    "objective": "读算法书与蓝皮手册拿到数字 31 和 2,推出密码 312,按正确顺序把三张分类卡放入学习保险箱,取出金色徽章交付。",
    "targetMinutes": 10,
    "selectedItemIds": ["rc-book", "rc-manual", "rc-notes", "rc-safe", "rc-badge", "rc-card-1", "rc-card-2", "rc-card-3"],
    "containers": [],
    "items": [
        item("rc-book", "clue", "图解算法书",
             "【网页内容】翻到 3.1 数据结构分类——数组、链表、栈、队列,动画图解一键运行。章节号 31 是密码的前两位。"),
        item("rc-manual", "clue", "蓝皮手册",
             "【网页内容】现代 JavaScript 教程,主课程包含 2 部分,涵盖 JavaScript 与浏览器。2 是密码的末位。"),
        item("rc-notes", "clue", "廖雪峰笔记", "原创中文精品教程。笔记扉页写着:研究互联网产品和技术。"),
        item("rc-card-1", "tool", "数组卡", "数组:连续内存、随机访问 O(1)。分类卡之一。"),
        item("rc-card-2", "tool", "链表卡", "链表:指针串联、插入 O(1)。分类卡之二。"),
        item("rc-card-3", "tool", "栈卡", "栈:先进后出 LIFO。分类卡之三。"),
        item("rc-safe", "lock", "学习保险箱",
             "学习保险箱:三位密码 312。面板旁边有三个卡槽,按正确顺序放入分类卡。"),
        item("rc-badge", "reward", "金色小徽章", "开学仪式的金色徽章。把它带出房间,自学计划就正式启动。", hidden=True),
    ],
    "beats": [
        {"id": "c1", "title": "读图解算法书", "action": "inspect", "uses": ["rc-book"], "requires": [],
         "reveals": ["rc-card-1", "rc-card-2", "rc-card-3"], "product": "翻过的算法书"},
        {"id": "c2", "title": "读蓝皮手册", "action": "inspect", "uses": ["rc-manual"], "requires": [],
         "product": "翻过的蓝皮手册"},
        {"id": "c3", "title": "打开学习保险箱", "action": "password", "uses": ["rc-safe"],
         "requires": ["c1", "c2"], "expected": "312", "deriveFrom": ["rc-book", "rc-manual"],
         "product": "打开的学习保险箱", "reveals": ["rc-badge"]},
        {"id": "c4", "title": "带徽章离开", "action": "deliver", "uses": ["rc-badge"], "requires": ["c3"]},
    ],
    "mechanics": ["inspect", "password", "deliver"],
    "hints": [
        "两张教材摊在明面上:算法书和蓝皮手册。",
        "算法书翻到 3.1;蓝皮手册说主课程有 2 部分。",
        "保险箱三位数:31 接 2。"
    ],
})
LEVELS["selfstudy"] = L3

for key, lv in LEVELS.items():
    path = f"sample-puzzles/demo-{key}.room.json"
    puzzle = {
        "records": [], "controlledIds": lv["selectedItemIds"],
        "items": [draft_item(it["id"], it["sceneName"], it["reason"][:24], "demo") for it in lv["items"]],
        "level": lv,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(puzzle, f, ensure_ascii=False, indent=1)
    print(f"{path}: {len(lv['items'])} 物件, {len(lv['beats'])} beats")
