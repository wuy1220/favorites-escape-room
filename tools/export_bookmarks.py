# -*- coding: utf-8 -*-
"""一键导出 Chrome / Edge 浏览器收藏,供收藏夹密室直接导入。

Chromium 系浏览器(Chrome/Edge)把收藏存在 User Data/<profile>/Bookmarks 的
纯 JSON 文件里,运行中也可安全读取(无需关闭浏览器)。

用法:
  python tools/export_bookmarks.py --list              # 列出所有浏览器档案
  python tools/export_bookmarks.py                     # 交互选择并导出
  python tools/export_bookmarks.py --browser edge      # 只看 Edge
  python tools/export_bookmarks.py --profile 2 --out . # 导出指定档案到当前目录

导出物是与浏览器一致的 Chrome Bookmarks JSON,可直接上传到
127.0.0.1:8128 的「选择收藏夹导出文件」。只读浏览器文件,不做任何修改。
"""
import argparse
import json
import os
import shutil
import time

LOCAL = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")


def user_data_dirs():
    """各浏览器的 User Data 目录(Windows 优先,兼顾 macOS/Linux 惯例路径)。"""
    home = os.path.expanduser("~")
    return {
        "chrome": [
            os.path.join(LOCAL, "Google", "Chrome", "User Data"),
            os.path.join(home, "Library", "Application Support", "Google", "Chrome"),
            os.path.join(home, ".config", "google-chrome"),
        ],
        "edge": [
            os.path.join(LOCAL, "Microsoft", "Edge", "User Data"),
            os.path.join(home, "Library", "Application Support", "Microsoft Edge"),
            os.path.join(home, ".config", "microsoft-edge"),
        ],
    }


def profile_label(user_data, profile_dir):
    """从 Local State 读档案显示名;读不到就用目录名。"""
    try:
        with open(os.path.join(user_data, "Local State"), encoding="utf-8") as f:
            info = json.load(f).get("profile", {}).get("info_cache", {}).get(profile_dir, {})
        name = info.get("name") or ""
        user = (info.get("user_name") or "").split("@")[0]
        label = " / ".join(x for x in (name, user) if x)
        if label:
            return label
    except (OSError, ValueError, AttributeError):
        pass
    return profile_dir


def count_urls(node):
    if not isinstance(node, dict):
        return 0
    if node.get("type") == "url":
        return 1
    return sum(count_urls(c) for c in node.get("children", []) or [])


def scan(browser):
    """返回 [{browser, user_data, profile_dir, label, bookmarks_path, mtime, count}],含书签的档案在前。"""
    found = []
    for user_data in user_data_dirs()[browser]:
        if not os.path.isdir(user_data):
            continue
        for entry in os.listdir(user_data):
            profile_dir = os.path.join(user_data, entry)
            bookmarks = os.path.join(profile_dir, "Bookmarks")
            if not (os.path.isdir(profile_dir) and os.path.isfile(bookmarks)):
                continue
            try:
                with open(bookmarks, encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, ValueError):
                continue  # 损坏/半写入的档案跳过
            roots = data.get("roots", {})
            count = sum(count_urls(roots.get(k)) for k in ("bookmark_bar", "other", "synced"))
            found.append(
                {
                    "browser": browser,
                    "user_data": user_data,
                    "profile_dir": entry,
                    "label": profile_label(user_data, entry),
                    "bookmarks_path": bookmarks,
                    "mtime": os.path.getmtime(bookmarks),
                    "count": count,
                }
            )
    found.sort(key=lambda p: (-p["count"], p["browser"], p["profile_dir"]))
    return found


def export(profile, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(profile["mtime"]))
    safe_label = re_sub(r'[\\/:*?"<>| ]+', "_", profile["label"])[:40] or profile["profile_dir"]
    name = f"收藏夹导出_{profile['browser']}_{safe_label}_{stamp}.json"
    dest = os.path.join(out_dir, name)
    shutil.copyfile(profile["bookmarks_path"], dest)
    return dest


def re_sub(pattern, repl, s):
    import re

    return re.sub(pattern, repl, s)


def main():
    ap = argparse.ArgumentParser(description="导出 Chrome/Edge 收藏为可导入的 JSON")
    ap.add_argument("--list", action="store_true", help="只列出档案,不导出")
    ap.add_argument("--browser", choices=["chrome", "edge", "all"], default="all")
    ap.add_argument("--profile", help="按档案目录名或显示名模糊匹配(如 Default / 2)")
    ap.add_argument("--out", default=os.path.join(LOCAL or "~", "Downloads")
                    if LOCAL else os.path.expanduser("~"), help="导出目录")
    args = ap.parse_args()

    browsers = ["chrome", "edge"] if args.browser == "all" else [args.browser]
    profiles = [p for b in browsers for p in scan(b)]
    if args.profile:
        needle = args.profile.lower()
        profiles = [p for p in profiles if needle in p["profile_dir"].lower() or needle in p["label"].lower()]
    if not profiles:
        print("没有找到含收藏的 Chrome/Edge 档案。检查浏览器是否安装过、是否收藏过任何页面。")
        return 1

    print(f"{'#':<3}{'浏览器':<8}{'档案':<28}{'书签数':<8}最后修改")
    for i, p in enumerate(profiles):
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(p["mtime"]))
        print(f"{i:<3}{p['browser']:<8}{(p['profile_dir'] + ' (' + p['label'] + ')')[:26]:<28}{p['count']:<8}{when}")

    if args.list:
        return 0
    picks = input("\n要导出哪些?(回车=全部;或输入序号,如 0,2):").strip()
    if picks:
        chosen = [profiles[int(x)] for x in re_split_commas(picks) if int(x) < len(profiles)]
    else:
        chosen = profiles
    for p in chosen:
        dest = export(p, args.out)
        print(f"已导出 {p['browser']}/{p['profile_dir']} ({p['count']} 条) → {dest}")
    print("\n到 127.0.0.1:8128 上传上面任一 .json 文件即可生成密室。")
    return 0


def re_split_commas(s):
    return [x.strip() for x in s.split(",") if x.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
