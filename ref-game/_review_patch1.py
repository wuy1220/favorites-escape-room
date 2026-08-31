# -*- coding: utf-8 -*-
"""review.md 修复 P1-XSS:engine role 白名单(两处)+ room02 转义(接 patch1)"""
import io

s = io.open('js/engine.js', encoding='utf-8').read()

# ROLE_OK 顶层常量
old_head = "(function () {\n  let compiled = null;"
if 'ROLE_OK' not in s:
    assert old_head in s
    s = s.replace(
        old_head,
        "(function () {\n  let compiled = null;\n"
        "  /* review.md P1:导入物件 role 白名单(_kind 类名拼接注入面) */\n"
        "  const ROLE_OK = ['clue', 'tool', 'lock', 'transform', 'reward', 'red_herring'];",
        1,
    )

# 两处 kind 拼接(缩进不同)统一替换
for indent in ('              ', '            '):
    old = (
        "kind:\n"
        + indent
        + "'collectible compiled-item role-' +\n"
        + indent
        + "        item.role +\n"
        + indent
        + "(isHidden ? ' compiled-hidden-item' : ''),"
    )
    new = (
        "kind:\n"
        + indent
        + "'collectible compiled-item role-' +\n"
        + indent
        + "        (ROLE_OK.includes(item.role) ? item.role : 'clue') +\n"
        + indent
        + "(isHidden ? ' compiled-hidden-item' : ''),"
    )
    if old in s:
        s = s.replace(old, new)

io.open('js/engine.js', 'w', encoding='utf-8', newline='').write(s)
print('engine role whitelist:', s.count('ROLE_OK.includes'), 'sites')
