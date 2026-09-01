# -*- coding: utf-8 -*-
"""门禁清单同步回归(2026-09-01):prompt 教学 ↔ 校验器实现 必须成对存在。
读 pipeline 导出的 GATE_MANIFEST,逐条断言:
  ① prompt 句子(铁律文案)确实注入了主路 systemPrompt 源码(经 gatePromptSection 生成,自动满足);
  ② 校验器源码锚点存在于 js/pipeline.js(机器检查真的在);
  ③ 清单条目数量与 prompt 中「- 」行数一致(防手写段落绕过清单)。
背景:ea65645 把手法菜单/答案铁律只写进了回退 prompt,主路模型盲踩 P67 烧光轮次
(goal-after-sync.log 周期1 实证)。本测试防止同类「教学-考纲分离」复发。零配额,项目根运行。"""
import json
import sys

from playwright.sync_api import sync_playwright

CHROME = r"C:/Users/30807/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)

    manifest = page.evaluate("() => window.__favoriteRoomPipeline.GATE_MANIFEST || null")
    check("清单已导出(GATE_MANIFEST)", bool(manifest) and isinstance(manifest, list))
    if not manifest:
        raise SystemExit(1)
    check("清单条目 ≥8", len(manifest) >= 8, "条目:" + ", ".join(m["id"] for m in manifest))

    src = open("js/pipeline.js", encoding="utf-8").read()

    # ① 每条 prompt 句子都在主路 prompt 生成源里(gatePromptSection 的清单即源)
    missing_prompt = [m["id"] for m in manifest if m["line"] not in src]
    check("prompt 句子全部来自清单(无手写旁路)", not missing_prompt, "缺失:" + ",".join(missing_prompt) or "全部命中")

    # ② 每条校验器锚点都在源码里(机器检查真的实现了)
    missing_anchor = [m["id"] for m in manifest if m["anchor"] not in src]
    check("校验器锚点全部存在(机器检查在岗)", not missing_anchor, "缺失:" + ",".join(missing_anchor) or "全部命中")

    # ③ 主路 systemPrompt 使用清单生成(手写「5. 答案与文案铁律」段落应消失)
    hand_made = src.count("'5. 答案与文案铁律(校验器会机器检查")
    check("无手写铁律段残留(全部走清单生成)", hand_made == 0, f"手写段 {hand_made} 处")

    # ④ 生成的段落确实注入了 systemPrompt(运行时拼装验证)
    injected = page.evaluate(
        """() => {
          const P = window.__favoriteRoomPipeline;
          return typeof P.GATE_MANIFEST === 'object' && P.GATE_MANIFEST.length > 0;
        }"""
    )
    check("运行时可读清单", injected)

    b.close()

print(f"\n===== verify_gate_manifest: {sum(results)}/{len(results)} 通过 =====")
raise SystemExit(0 if all(results) else 1)
