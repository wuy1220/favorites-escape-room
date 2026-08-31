# -*- coding: utf-8 -*-
"""B v3 重做(拼信+电与光+台历接任,房间化≤4) + C 容器重构(借阅台,≤4)"""
import os

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "gen_demo_levels_v4.py")
s = open(p, encoding="utf-8").read()

# ---------- B 段整体替换 ----------
start = s.index("# ============ B 春日工具箱")
end = s.index("# ============ C 秋末自学计划")
new_b = '''# ============ B 春日工具箱·守库人的遗愿(拼合+电与光+台历接任) ============
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
        li("tb-clip", "clue", "线索", "素材夹", "牛皮纸夹里滑出几张打印卡,夹层里还掉出两张撕碎的纸片。点击打开素材夹。"),
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
        li("tb-desk", "clue", "线索", "书桌", "书房正中的旧书桌,台面被擦得干干净净——他在等谁来用这张桌子。点击走近书桌。"),
        li("tb-lamp", "lock", "锁", "台灯",
           "书桌上的台灯。底座敞着,红、蓝、黄三根线断在半空,线头崭新——是剪断的,不是烧断的。"),
        li("tb-panelbase", "clue", "线索", "底座端子盘",
           "台灯底座里的三色端子,每个旁边嵌着一枚手绘小钟面:红端子的钟面指着 3 点方向,蓝的指着 7 点,黄的指着 11 点。笔迹和撕碎的信是同一个人。"),
        li("tb-calendar", "clue", "线索", "台历",
           "台历停在他离开的那天。今天的页面折了一个角,像在等谁伸手。"),
        li("tb-front", "clue", "线索", "正门", "笔记库的正门,门上是库门文字屏,侧边嵌着书架顶层标签屏。点击走近正门。"),
        li("tb-gate", "lock", "锁", "库门文字屏",
           "笔记库的库门没有锁孔,只有一块文字输入屏,屏上闪烁着一行提示:请输入入库口令。"),
        li("tb-shelf", "lock", "锁", "书架标签屏",
           "书架侧面嵌着一块标签屏:请输入顶层标签。屋里亮起来,它才通电。",
           hidden=True, auto=True),
        li("tb-wall", "clue", "线索", "守库人的墙", "灯光够到的墙面——上面贴着两张便签,都是守库人的字。点击走近看。", hidden=True, auto=True),
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

'''
s = s[:start] + new_b + s[end:]

# ---------- C 段:借阅台容器化 + kettle 挪到下层书架 + c1 reveals 收敛 ----------
old_c_items = '''    "items": [
        li("rc-door", "clue", "线索", "资料室门", "资料室的门虚掩着,门缝里漏出旧纸的味道。点击推门进去。"),
        li("rc-manual", "clue", "线索", "守馆手册",
           "【流程页】今晚归还批次:贴绿标的三本。流程:逐本放上扫描台——机器会出校验题,答案都在书自己的卡片里,答对才算受理。受理次序就是学习的次序:概述在前,主课程在中,算法进阶在后。全部受理后系统响铃,值班员自然会来。备注:章不外借,但他那个人,只认热茶。",
           hidden=True),'''
new_c_items = '''    "items": [
        li("rc-door", "clue", "线索", "资料室门", "资料室的门虚掩着,门缝里漏出旧纸的味道。点击推门进去。"),
        li("rc-desk", "clue", "线索", "借阅台", "借阅台空着,台面收拾得整整齐齐,后面虚掩着一扇小门,门缝里透出一点灯光。点击走近借阅台。"),
        li("rc-manual", "clue", "线索", "守馆手册",
           "【流程页】今晚归还批次:贴绿标的三本。流程:逐本放上扫描台——机器会出校验题,答案都在书自己的卡片里,答对才算受理。受理次序就是学习的次序:概述在前,主课程在中,算法进阶在后。全部受理后系统响铃,值班员自然会来。备注:章不外借,但他那个人,只认热茶。",
           hidden=True, container="rc-desk"),'''
assert s.count(old_c_items) == 1
s = s.replace(old_c_items, new_c_items)

old_c_mid = '''        li("rc-scanner", "tool", "工具", "扫描台",
           "借阅台旁的扫描台,指示灯待机闪烁。把书平放上去就能扫——但每扫一本,它都要先考你一道题。"),
        li("rc-desk", "clue", "线索", "借阅台",
           "借阅台空着,台面收拾得整整齐齐,后面虚掩着一扇小门,门缝里透出一点灯光。"),
        li("rc-npc", "clue", "线索", "值班员",'''
new_c_mid = '''        li("rc-scanner", "tool", "工具", "扫描台",
           "借阅台上的扫描台,指示灯待机闪烁。把书平放上去就能扫——但每扫一本,它都要先考你一道题。",
           hidden=True, container="rc-desk"),
        li("rc-npc", "clue", "线索", "值班员",'''
assert s.count(old_c_mid) == 1
s = s.replace(old_c_mid, new_c_mid)

old_c_ticket = '''        li("rc-ticket", "transform", "结果", "提货单",
           "借阅系统的提货单,空白处等着盖章。盖了章的单子才能交出去。", hidden=True),
    ],
    "beats": [
        {"id": "c1", "title": "推开资料室", "action": "inspect", "uses": ["rc-door"],
         "reveals": ["rc-manual", "rc-scanner", "rc-desk", "rc-kettle", "rc-ticket"]},'''
new_c_ticket = '''        li("rc-ticket", "transform", "结果", "提货单",
           "借阅系统的提货单,空白处等着盖章。盖了章的单子才能交出去。",
           hidden=True, container="rc-desk"),
    ],
    "beats": [
        {"id": "c1", "title": "推开资料室", "action": "inspect", "uses": ["rc-door"],
         "reveals": ["rc-shelfa", "rc-shelfb", "rc-desk"]},'''
assert s.count(old_c_ticket) == 1
s = s.replace(old_c_ticket, new_c_ticket)

# kettle 挂到下层书架(还书车旁),不再占根层位
old_kettle = '''        li("rc-kettle", "tool", "工具", "保温壶",
           "还书车旁的保温壶,摸着还温。守馆人走前泡的茶,一口没动。"),'''
new_kettle = '''        li("rc-kettle", "tool", "工具", "保温壶",
           "挂在下层书架车把上的保温壶,摸着还温。守馆人走前泡的茶,一口没动。",
           hidden=True, container="rc-shelfb"),'''
assert s.count(old_kettle) == 1
s = s.replace(old_kettle, new_kettle)

open(p, "w", encoding="utf-8").write(s)
print("B v3 + C containers written")
