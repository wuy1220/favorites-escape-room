# -*- coding: utf-8 -*-
"""示例收藏夹导出为 Netscape 书签 HTML(可导入浏览器/本产品导入流程)"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(ROOT, "fixtures", "demo-collection.json")
out = os.path.join(ROOT, "fixtures", "demo-collection.html")

d = json.load(open(src, encoding="utf-8"))


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


lines = [
    "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
    "<!-- This is an automatically generated file. It will be read and overwritten. DO NOT EDIT! -->",
    '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
    "<TITLE>Bookmarks</TITLE>",
    "<H1>书签栏</H1>",
    "<DL><p>",
]


def walk(node):
    if isinstance(node, dict):
        if "children" in node:
            name = node.get("name") or ""
            if name:  # 根容器(书签栏)也输出为文件夹
                lines.append(f"    <DT><H3>{esc(name)}</H3>")
                lines.append("    <DL><p>")
            for c in node["children"]:
                walk(c)
            if name:
                lines.append("    </DL><p>")
        elif node.get("type") == "url":
            lines.append(f'        <DT><A HREF="{esc(node.get("url", ""))}">{esc(node.get("name", ""))}</A>')
        else:
            for v in node.values():
                walk(v)
    elif isinstance(node, list):
        for c in node:
            walk(c)


for v in (d.get("roots") or {}).values():
    walk(v)
lines.append("</DL><p>")
open(out, "w", encoding="utf-8").write("\n".join(lines))
print("已导出:", out, f"({len(lines)} 行)")
