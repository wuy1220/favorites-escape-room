# -*- coding: utf-8 -*-
"""三关演示重设计(最终版):线性抽屉流,语义/数字混合锚定。"""
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


def write_level(key, lv, draft_items):
    lv["selectedItemIds"] = [it["id"] for it in lv["items"]]
    puzzle = {"records": [], "controlledIds": lv["selectedItemIds"],
              "items": [draft_item(it["id"], it["sceneName"], it["reason"][:24], "demo") for it in lv["items"]],
              "level": lv}
    path = f"sample-puzzles/demo-{key}.room.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(puzzle, f, ensure_ascii=False, indent=1)
    print(f"{path}: {len(lv['items'])} 物件, {len(lv['beats'])} beats")


# ============ A《深秋游戏之夜》: 计量锁 ============
A = base_level()
A.update({
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
write_level("gamenight", A, [])

# ============ B《春日工具箱》: 语义文字锁 + 元数据锁 ============
B = base_level()
B.update({
    "id": "level-demo-toolbox",
    "title": "春日工具箱 · 知识库建成之夜",
    "premise": "2025 年 4 月,你决定给自己的知识建一座房子。工具桌上摊着教程页和效率卡,底座上挂着两把密码锁——一个数字来自剪报的路径,一个来自效率卡的编号。",
    "objective": "读剪报与效率卡拿数字;开年份锁取安装盘;装上 Obsidian 建成知识库;开编号锁完成备份;把备份档案拖到出口交付。",
    "targetMinutes": 8,
    "selectedItemIds": ["tb-clip", "tb-note", "tb-tutorial", "tb-desk", "tb-lock1", "tb-lock2", "tb-installer", "tb-badge"],
    "containers": [],
    "items": [
        item("tb-clip", "clue", "知乎专栏剪报",
             "【事实】剪报路径印着:/p/2026071811813643264——开头的年份 2026,是年份锁的密码。"),
        item("tb-note", "clue", "少数派效率卡",
             "【事实】效率卡编号印着:/post/83763——后三位 763,是编号锁的密码。"),
        item("tb-tutorial", "clue", "Obsidian 教程页",
             "【网页内容】菜鸟教程写着:Obsidian 基于 Markdown 文件构建个人知识库,本地存储。教程页就是安装指南。"),
        item("tb-desk", "clue", "知识库底座", "底座上有一个凹槽。把安装盘放进去,知识库就建成了。"),
        item("tb-lock1", "lock", "年份锁", "底座的年份锁:四位数字。剪报路径的开头就是答案。"),
        item("tb-lock2", "lock", "编号锁", "底座的编号锁:三位数字。效率卡的编号就是答案。"),
        item("tb-installer", "tool", "Obsidian 安装盘",
             "银色安装盘:Obsidian——Sharpen your thinking。装上教程页,知识库就建成了。",
             hidden=True, container="tb-desk"),
        item("tb-badge", "reward", "金色档案盒", "备份完成的金色档案盒。把它带出房间,交付给出口。", hidden=True),
    ],
    "beats": [
        {"id": "t1", "title": "读知乎剪报", "action": "inspect", "uses": ["tb-clip"], "requires": [],
         "product": "细读过的剪报"},
        {"id": "t2", "title": "读少数派效率卡", "action": "inspect", "uses": ["tb-note"],
         "requires": [], "product": "细读过的效率卡"},
        {"id": "t3", "title": "读 Obsidian 教程页", "action": "inspect", "uses": ["tb-tutorial"],
         "requires": [], "product": "读过的教程页"},
        {"id": "t4", "title": "开年份锁", "action": "password", "uses": ["tb-lock1"],
         "requires": ["t1"], "expected": "2026", "deriveFrom": ["tb-clip"],
         "product": "开着的年份锁", "reveals": ["tb-installer"]},
        {"id": "t5", "title": "装上安装盘", "action": "combine", "uses": ["tb-installer", "tb-desk"],
         "requires": ["t3", "t4"], "consume": ["tb-installer"], "resultOn": "tb-desk",
         "product": "装好的底座"},
        {"id": "t6", "title": "开编号锁", "action": "password", "uses": ["tb-lock2"],
         "requires": ["t2", "t5"], "expected": "763", "deriveFrom": ["tb-note"],
         "product": "完成的备份"},
        {"id": "t7", "title": "备份交付", "action": "deliver", "uses": ["result:t6"],
         "requires": ["t6"]},
    ],
    "mechanics": ["inspect", "combine", "password", "deliver"],
    "hints": [
        "两张线索卡在明面上:剪报和效率卡。",
        "剪报路径开头 2026 是年份锁密码;效率卡编号 763 是编号锁密码。",
        "先开年份锁,取出安装盘;装上底座后,再开编号锁。",
        "全部完成后,把备份档案拖到出口。"
    ],
})
write_level("toolbox", B, [])

# ============ C《秋末自学计划》: 语义密码 + 组合 ============
C = base_level()
C.update({
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
write_level("selfstudy", C, [])
