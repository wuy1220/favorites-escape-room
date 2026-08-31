# -*- coding: utf-8 -*-
"""三关谜题重设计:语义问答锁(锚定已验证的网页事实)。"""
import json


def patch(path, edits):
    d = json.load(open(path, encoding='utf-8'))
    lv = d['level']
    for it in lv['items']:
        e = edits.get(it['id'])
        if e:
            it['reason'] = e['reason']
    for b in lv['beats']:
        e = edits.get(b['id'])
        if e and 'expected' in e:
            b['expected'] = e['expected']
            if 'deriveFrom' in e:
                b['deriveFrom'] = e['deriveFrom']
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('patched:', path)


# ============ A《深秋游戏之夜》: 歌名语义锁 + sm 号数字锁 ============
patch('sample-puzzles/demo-gamenight.room.json', {
    'ra-tape': {
        'reason': "【网页内容】标签印着歌名:Never Gonna Give You Up——1987 年的老歌。点播台的歌名锁,认的就是它。",
    },
    'ra-poster': {
        'reason': "游侠网海报——坚守单机阵地。海报背面印着点播规则:歌名锁填歌名;频率锁看光碟的投稿编号。",
    },
    'ra-disc': {
        'reason': "重巡 Pola 的「Treasure」光碟,側标印着投稿编号 sm29208969。频率锁认它的后四位。",
    },
    'a5': {'expected': 'never gonna give you up', 'deriveFrom': ['ra-tape']},
    'a6': {'expected': '8969'},
})

# ============ B《春日工具箱》: 语义锁(Markdown) + 元数据锁(年份) ============
patch('sample-puzzles/demo-toolbox.room.json', {
    'rb-tutorial': {
        'reason': "【网页内容】菜鸟教程 Obsidian 篇写着:基于 Markdown 文件的个人知识库,本地文件存储。第一把锁的答案,就是这种文件格式的名字。",
    },
    'rb-clip': {
        'reason': "剪报的路径印着:/p/2026071811813643264——开头的年份,就是第二把锁的密码。",
    },
    'b4': {'expected': 'markdown', 'deriveFrom': ['rb-tutorial']},
})

# ============ C《秋末自学计划》: 保持语义接地(章节 3.1 + 教程 2 部分 → 312) ============
print('C 保持不变(已语义接地)')
