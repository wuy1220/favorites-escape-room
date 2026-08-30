# -*- coding: utf-8 -*-
"""生成三个演示关卡 JSON(深度电台主题,事实已实测回访验证)。"""
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
    return {"id": "", "title": "", "premise": "", "objective": "", "targetMinutes": 10,
            "selectedItemIds": [], "containers": [], "items": [], "beats": [], "scenes": [],
            "mechanics": [], "hints": [], "validation": {"valid": True, "issues": []},
            "grounding": "demo"}


LEVELS = {}

# ============ 关卡 A《深秋游戏之夜》 ============
A = base_level()
A.update({
    "id": "level-demo-gamenight",
    "title": "深秋游戏之夜 · 末班点播台",
    "premise": "2024 年 11 月的深夜,你在游戏堆里过了一整晚。今晚,你想把那段 Never Gonna Give You Up 点播给整座城市的失眠者。点播台的老机器还亮着灯——它只认数据:播放量、硬币数,一个都不能错。",
    "objective": "打开怀旧柜取出卡带与光碟,读懂卡带上的播放数据,把卡带装进点唱机,再按播放量的前四位调准频率面板,最后把光碟匣装上,完成末班点播。",
    "targetMinutes": 10,
    "selectedItemIds": ["ra-cabinet", "ra-tape", "ra-disc", "ra-machine", "ra-poster", "ra-panel"],
    "containers": [
        {"id": "ra-cabinet", "name": "怀旧游戏柜", "desc": "玻璃柜里躺着你的卡带和一张 MMD 光碟。", "hidden": False},
    ],
    "items": [
        item("ra-cabinet", "clue", "怀旧游戏柜", "玻璃柜里躺着卡带和一张 MMD 光碟。点击打开它。"),
        item("ra-tape", "clue", "卡带 A · Never Gonna Give You Up",
             "【事实·数据条】标签印着:视频播放量 104610374、投硬币枚数 1260911。这就是点播台要的点火数据。",
             hidden=True, container="ra-cabinet"),
        item("ra-disc", "reward", "MMD 光碟",
             "重巡 Pola 的「Treasure」光碟,側标印着 sm29208969。台长说,末班点播非它不可。",
             hidden=True, container="ra-cabinet"),
        item("ra-machine", "tool", "老点唱机", "老点唱机的卡带舱积着灰。把要点的卡带装进去,它才能工作。"),
        item("ra-poster", "clue", "游侠网海报",
             "海报是「游侠网——坚守单机阵地」的旧宣传画,角落印着一行小字:点播台的热线密码 = 播放量的前四位。"),
        item("ra-panel", "lock", "频率面板", "点播台的频率面板,四位数字转盘。调准了,整座城市都能听见这首老歌。"),
    ],
    "beats": [
        {"id": "a1", "title": "打开怀旧柜", "action": "inspect", "uses": ["ra-cabinet"], "requires": [],
         "reveals": ["ra-tape", "ra-disc"], "product": "敞开的怀旧柜"},
        {"id": "a2", "title": "读卡带数据条", "action": "inspect", "uses": ["ra-tape"], "requires": ["a1"],
         "product": "读过数据的卡带 A"},
        {"id": "a3", "title": "读游侠网海报", "action": "inspect", "uses": ["ra-poster"], "requires": [],
         "product": "细读过的海报"},
        {"id": "a4", "title": "卡带装进点唱机", "action": "combine", "uses": ["ra-tape", "ra-machine"],
         "requires": ["a2"], "consume": ["ra-tape"], "resultOn": "ra-machine", "product": "就绪的点唱机"},
        {"id": "a5", "title": "调准频率 1046", "action": "password", "uses": ["ra-panel"],
         "requires": ["a3", "a4"], "expected": "1046", "deriveFrom": ["ra-tape"], "product": "接通的热线"},
        {"id": "a6", "title": "光碟入匣", "action": "combine", "uses": ["result:a4", "ra-disc"],
         "requires": ["a4", "a5"], "resultOn": "ra-disc", "product": "待播的光碟匣"},
        {"id": "a7", "title": "完成末班点播", "action": "deliver", "uses": ["result:a6"], "requires": ["a6"]},
    ],
    "mechanics": ["inspect", "combine", "password", "deliver"],
    "hints": [
        "玻璃柜里有卡带和光碟,先打开它。",
        "点卡带 A,读它的数据条:播放量、硬币数。",
        "游侠网海报的角落写着热线密码的规则。",
        "把卡带装进点唱机,它才能工作。",
        "热线密码 = 播放量的前四位;调准频率后,把光碟装进匣子。",
    ],
})
LEVELS["gamenight"] = A

# ============ 关卡 B《春日工具箱》 ============
B = base_level()
B.update({
    "id": "level-demo-toolbox",
    "title": "春日工具箱 · 知识库建成之夜",
    "premise": "2025 年 4 月,你决定给自己的知识建一座房子。剪报、效率卡、教程页摊在工具桌上——两把密码锁守着最后的部件:一个数字来自剪报的路径,一个来自效率卡的编号。",
    "objective": "读剪报与效率卡拿到两组数字,打开工具桌的密码锁取出安装盘,照教程页把知识库建成,完成备份后交付。",
    "targetMinutes": 10,
    "selectedItemIds": ["rb-clip", "rb-note", "rb-tutorial", "rb-desk", "rb-installer", "rb-lock2"],
    "containers": [
        {"id": "rb-desk", "name": "工具桌", "desc": "工具桌的抽屉上挂着两把密码锁,里面锁着安装盘。", "hidden": False},
    ],
    "items": [
        item("rb-clip", "clue", "知乎专栏剪报",
             "剪报的路径印着:/p/2026071811813643264——开头的年份,就是第一把锁的密码。"),
        item("rb-note", "clue", "少数派效率卡", "效率卡的编号印着:/post/83763——后三位 763,是第二把锁的密码。"),
        item("rb-tutorial", "clue", "Obsidian 教程页",
             "菜鸟教程的 Obsidian 篇:基于 Markdown 的个人知识库,本地文件存储。装上它,知识就有了家。"),
        item("rb-installer", "tool", "Obsidian 安装盘",
             "银色安装盘,标签写着:Obsidian——Sharpen your thinking。", hidden=True, container="rb-desk"),
        item("rb-lock1", "lock", "密码锁 · 年份", "第一把锁:四位年份。剪报路径的开头就是答案。",
             hidden=True, container="rb-desk"),
        item("rb-lock2", "lock", "密码锁 · 编号", "第二把锁:三位编号。少数派效率卡的编号就是答案。",
             hidden=True, container="rb-desk"),
    ],
    "beats": [
        {"id": "b1", "title": "读知乎剪报", "action": "inspect", "uses": ["rb-clip"], "requires": [],
         "product": "细读过的剪报"},
        {"id": "b2", "title": "读少数派效率卡", "action": "inspect", "uses": ["rb-note"], "requires": [],
         "product": "细读过的效率卡"},
        {"id": "b3", "title": "读 Obsidian 教程页", "action": "inspect", "uses": ["rb-tutorial"],
         "requires": [], "product": "读过的教程页"},
        {"id": "b4", "title": "开年份锁", "action": "password", "uses": ["rb-lock1"], "requires": ["b1"],
         "expected": "2026", "deriveFrom": ["rb-clip"], "product": "开着的年份锁",
         "reveals": ["rb-installer"]},
        {"id": "b5", "title": "装上 Obsidian", "action": "combine", "uses": ["rb-installer", "rb-tutorial"],
         "requires": ["b3", "b4"], "resultOn": "rb-installer", "product": "建成的知识库"},
        {"id": "b6", "title": "开编号锁", "action": "password", "uses": ["rb-lock2"], "requires": ["b2", "b5"],
         "expected": "763", "deriveFrom": ["rb-note"], "product": "备份完成的档案"},
        {"id": "b7", "title": "备份交付", "action": "deliver", "uses": ["result:b6"], "requires": ["b6"]},
    ],
    "mechanics": ["inspect", "combine", "password", "deliver"],
    "hints": [
        "两张线索卡都在明面上:剪报和效率卡。",
        "剪报路径以年份开头;效率卡编号是三位数。",
        "先开年份锁,取出安装盘。",
        "安装盘要和教程页组合,知识库才能建成。",
        "最后把建成的档案交给出口。",
    ],
})
LEVELS["toolbox"] = B

# ============ 关卡 C《秋末自学计划》 ============
C = base_level()
C.update({
    "id": "level-demo-selfstudy",
    "title": "秋末自学计划 · 312 号学习保险箱",
    "premise": "2025 年 9 月,你决定系统自学编程。桌上摊着算法书、蓝皮手册和廖雪峰的笔记,角落立着一台学习保险箱——密码是你给自己定下的学习计划:算法书第 3.1 章,配两部分的教程。",
    "objective": "读算法书与蓝皮手册,推出保险箱密码 312,取出金色徽章,把它带出房间完成开学仪式。",
    "targetMinutes": 6,
    "selectedItemIds": ["rc-book", "rc-manual", "rc-notes", "rc-safe", "rc-badge"],
    "containers": [],
    "items": [
        item("rc-book", "clue", "图解算法书",
             "【事实】翻到 3.1 数据结构分类——动画图解,一键运行。这一章的编号,是你给自己的第一串数字。"),
        item("rc-manual", "clue", "蓝皮手册", "【事实】现代 JavaScript 教程,主课程包含 2 部分,涵盖 JavaScript 与浏览器。"),
        item("rc-notes", "clue", "廖雪峰笔记", "原创中文精品教程。笔记扉页写着:研究互联网产品和技术。"),
        item("rc-safe", "lock", "学习保险箱",
             "学习保险箱:三位密码。你早就把计划写在纸上了——算法书章节号,接上教程的部分数。"),
        item("rc-badge", "reward", "金色小徽章", "开学仪式的金色徽章。把它带出房间,自学计划就正式启动。", hidden=True),
    ],
    "beats": [
        {"id": "c1", "title": "读图解算法书", "action": "inspect", "uses": ["rc-book"], "requires": [],
         "product": "翻过的算法书"},
        {"id": "c2", "title": "读蓝皮手册", "action": "inspect", "uses": ["rc-manual"], "requires": [],
         "product": "翻过的蓝皮手册"},
        {"id": "c3", "title": "打开学习保险箱", "action": "password", "uses": ["rc-safe"],
         "requires": ["c1", "c2"], "expected": "312", "deriveFrom": ["rc-book", "rc-manual"],
         "product": "打开的学习保险箱", "reveals": ["rc-badge"]},
        {"id": "c4", "title": "带徽章离开", "action": "deliver", "uses": ["rc-badge"], "requires": ["c3"]},
    ],
    "mechanics": ["inspect", "password", "deliver"],
    "hints": [
        "两张教材摊在明面上:算法书和蓝皮手册,各藏着一段数字。",
        "算法书翻到 3.1;蓝皮手册说主课程有 2 部分。",
        "保险箱三位数:31 接 2。",
    ],
})
LEVELS["selfstudy"] = C

for key, lv in LEVELS.items():
    path = f"sample-puzzles/demo-{key}.room.json"
    puzzle = {
        "records": [],
        "controlledIds": lv["selectedItemIds"],
        "items": [draft_item(it["id"], it["sceneName"], it["reason"][:24], "demo") for it in lv["items"]],
        "level": lv,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(puzzle, f, ensure_ascii=False, indent=1)
    print(f"{path}: {len(lv['items'])} 物件, {len(lv['beats'])} beats")
