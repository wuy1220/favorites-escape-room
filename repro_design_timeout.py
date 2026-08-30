# -*- coding: utf-8 -*-
"""复现「设计流中断」:抓取 designWindow 现在真实发出的请求体,
按浏览器同款路径(本地 server /api/step + router-force)重放,计时并检查 advisor 块。
客户端超时设 600s,验证「单次设计调用 > 240s 默认超时」的假设。"""
import json
import time
import urllib.request
import urllib.error

from playwright.sync_api import sync_playwright

CHROME = r"C:/Users/30807/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"

captured = {"design": None}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()

    orig_wrap = """
    () => {
      const orig = window.fetch.bind(window);
      window.__captured = null;
      window.fetch = function (url, opts) {
        const s = String(opts && opts.messages ? '' : url);
        if (String(url).includes('/api/step') && opts && opts.body) {
          const bd = JSON.parse(opts.body);
          if (bd.messages && bd.messages[0].content.indexOf('关卡设计师') >= 0 && !window.__captured) {
            window.__captured = opts.body;
            return Promise.resolve(new Response(JSON.stringify({
              choices: [{ message: { content: JSON.stringify({ scenes: [] }) } }],
            }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
          }
        }
        return orig(url, opts);
      };
    }
    """
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    page.evaluate(orig_wrap)
    page.evaluate(
        """
    async () => {
      const raw = open('__fixtures__');
      return 'skip';
    }
    """
    ) if False else None
    # 用 sample10 生成 records(清洗 stub 无法用——直接在页面里走真实清洗,无模型调用
    # 因为 cleanBatch 只在导入流程;此处手工构造 records)
    records = page.evaluate(
        """
    () => {
      const raw = document.getElementById('homeFile') ? '' : '';
      return null;
    }
    """
    )
    # 直接读 fixture 并 parse+clean
    import io as _io
    raw = _io.open("fixtures/sample10-bookmarks.html", encoding="utf-8").read()
    records = page.evaluate(
        """(raw) => {
          const pipe = window.__favoriteRoomPipeline;
          const items = pipe.parse(raw, 'sample10.html');
          const cleaned = pipe.clean(items);
          return cleaned.records.filter((r) => r.status !== 'archive').slice(0, 6);
        }""",
        raw,
    )
    page.evaluate(
        """(records) => {
        }""",
        records,
    )
    # 触发一次真实 designWindow(它会走被劫持的 fetch → 捕获请求体 → 立即被假响应打断)
    page.evaluate(
        """async (records) => {
          const pipe = window.__favoriteRoomPipeline;
          const cleaned = {records, controlledIds: records.map((r) => r.id), duplicates: [],
                           stats: {input: records.length, unique: records.length, duplicates: 0}};
          try {
            await pipe.designWindow(records, '深夜书房', null, [], function(){}, '');
          } catch (e) { /* 假响应结构不合规,忽略 */ }
        }""",
        records,
    )
    body = page.evaluate("() => window.__captured")
    b.close()

if not body:
    raise SystemExit("未捕获到设计请求体")
obj = json.loads(body)
sys_size = len(obj["messages"][0]["content"])
usr_size = len(obj["messages"][1]["content"])
print("请求体已捕获: system=%d 字符, user=%d 字符, stream=%s, model=%s" % (
    sys_size, usr_size, obj.get("stream"), obj.get("model")))
io_open = open("ref-game/llm_out/design_body_now.json", "w", encoding="utf-8")
json.dump(obj, io_open, ensure_ascii=False, indent=1)
io_open.close()

# 重放:走本地 server(router-force 与浏览器一致),超时 600s
body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(
    "http://127.0.0.1:8128/api/step",
    data=body,
    headers={"Content-Type": "application/json"},
)
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.loads(r.read())
    wall = time.time() - t0
    content = (d.get("choices") or [{}])[0].get("message", {}).get("content", "")
    has_adv = "[Advisor consultation" in content
    print("重放结果: %.1fs, advisor块=%s, content=%d 字符, finish=%s" % (
        wall, has_adv, len(content),
        (d.get("choices") or [{}])[0].get("finish_reason")))
    # 试解析设计 JSON 是否可读
    try:
        parsed = json.loads(content)
        shape = "scenes" if parsed.get("scenes") else ("flat" if parsed.get("beats") else "其他")
        print("设计形状:", shape, "| scenes 数:", len(parsed.get("scenes", []) or []))
    except Exception:
        print("content 不是纯 JSON(前 80 字):", content[:80].replace(chr(10), " "))
except urllib.error.URLError as e:
    print("重放失败: %.1fs %s" % (time.time() - t0, str(e)[:120]))
