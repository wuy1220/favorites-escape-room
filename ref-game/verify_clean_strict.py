# -*- coding: utf-8 -*-
"""清洗严格性 + 清空缓存按钮回归:
1) 本地确定性筛除(博彩/破解/空标题→archive,正常条目 keep,safetyFlag 就位);
2) 首页「清空清洗缓存」按钮:种入假 datasets 条目→点按钮(自动接受 confirm)→store 清空+状态栏更新。
在项目根运行(需 8128 静态服务)。"""
import json
from playwright.sync_api import sync_playwright

CHROME = None
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)

    # 1) 本地确定性筛除规则
    r = page.evaluate(
        """
    () => {
      const items = [
        { id: 'x1', title: '博彩平台 稳赚计划', url: 'http://bet.example.com/a', domain: 'bet.example.com', folder: '', dateAdded: '2021-07-30T09:41' },
        { id: 'x2', title: '破解版软件下载', url: 'http://crack.example.com/x', domain: 'crack.example.com', folder: '', dateAdded: '2021-07-30T09:41' },
        { id: 'x3', title: '', url: 'http://x3.example.com/', domain: 'x3.example.com', folder: '', dateAdded: '2021-07-30T09:41' },
        { id: 'x4', title: 'Python 官方教程', url: 'http://docs.example.com/py', domain: 'docs.example.com', folder: '书签栏 / 学习', dateAdded: '2021-07-30T09:41' },
        { id: 'x5', title: '【ASMR】足趾碾压 擦边耳舔助眠', url: 'https://video.example.com/av1', domain: 'video.example.com', folder: '书签栏 / 其他', dateAdded: '2021-07-30T09:41' },
      ];
      const out = window.__favoriteRoomPipeline.clean(items);
      const byId = {};
      out.records.forEach((r) => (byId[r.id] = r));
      return {
        x1: [byId.x1.status, byId.x1.safetyFlag],
        x2: [byId.x2.status, byId.x2.safetyFlag],
        x3: byId.x3.status,
        x4: byId.x4.status,
        x5: [byId.x5.status, byId.x5.safetyFlag],
        stats: out.stats,
      };
    }
    """
    )
    check("博彩条目 archive + 安全标记", r["x1"][0] == "archive" and "博彩" in r["x1"][1], str(r["x1"]))
    check("破解条目 archive + 安全标记", r["x2"][0] == "archive" and "盗版" in r["x2"][1], str(r["x2"]))
    check("空标题条目 archive", r["x3"] == "archive", r["x3"])
    check("正常条目仍 keep", r["x4"] == "keep", r["x4"])
    check("灰色擦边条目 archive + 安全标记", r["x5"][0] == "archive" and "灰色" in r["x5"][1], str(r["x5"]))

    # Chrome JSON 导出:date_added 为 WebKit 纪元微秒(1601 起),必须换算到合理年份
    # (13360000000000000 µs ≈ 2024-05);审查 11.2.5 回归
    chrome = page.evaluate(
        '''
    () => {
      const raw = JSON.stringify({
        roots: { bookmark_bar: { children: [
          { type: 'url', name: 'Python 教程', url: 'https://docs.example.com/py',
            date_added: '13360000000000000' },
        ] } },
      });
      const out = window.__favoriteRoomPipeline.parse(raw, 'bookmarks.json');
      const rec = window.__favoriteRoomPipeline.clean(out).records[0];
      return rec.dateAdded;
    }
    '''
    )
    check(
        "Chrome JSON 微秒时间戳换算到 2024",
        chrome.startswith('2024'),
        chrome or '(空)',
    )

    # 2) 清空清洗缓存按钮:先种一条假 datasets 记录,点按钮(自动接受 confirm),验证清空
    page.evaluate(
        """
    () =>
      new Promise((resolve, reject) => {
        const req = indexedDB.open('favorites-escape-room-local');
        req.onsuccess = () => {
          const db = req.result;
          const tx = db.transaction('datasets', 'readwrite');
          tx.objectStore('datasets').put({ id: 'test-cache-entry', cleaned: { records: [] } });
          tx.oncomplete = () => resolve(true);
          tx.onerror = () => reject(tx.error);
        };
        req.onerror = () => reject(req.error);
      })
    """
    )
    seeded = page.evaluate(
        """
    () =>
      new Promise((resolve) => {
        const req = indexedDB.open('favorites-escape-room-local');
        req.onsuccess = () => {
          const tx = req.result.transaction('datasets').objectStore('datasets').count();
          tx.onsuccess = () => resolve(tx.result);
        };
      })
    """
    )
    page.on("dialog", lambda d: d.accept())
    page.click("#homeClearCache")
    page.wait_for_timeout(600)
    after = page.evaluate(
        """
    () =>
      new Promise((resolve) => {
        const req = indexedDB.open('favorites-escape-room-local');
        req.onsuccess = () => {
          const tx = req.result.transaction('datasets').objectStore('datasets').count();
          tx.onsuccess = () => resolve(tx.result);
        };
      })
    """
    )
    status_text = page.evaluate("() => document.getElementById('homeStatus').textContent")
    check(f"缓存条目 {seeded} 条,点按钮后 {after} 条", seeded >= 1 and after == 0)
    check("状态栏提示已更新", "已清空" in status_text, status_text)
    b.close()

print(f"\n===== verify_clean_cache: {sum(results)}/{len(results)} 通过 =====")
raise SystemExit(0 if all(results) else 1)
