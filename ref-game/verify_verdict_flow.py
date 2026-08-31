# -*- coding: utf-8 -*-
"""全局清洗 + 标记记录 + 增量清洗 流程回归(stub 模型,零 LLM 配额):
1) 首次导入 sample10:全量条目都被标记(verdicts store 有记录),模型调用 1 批;
2) 同文件再次导入:零模型调用(增量=0);
3) 追加 1 条新书签再导入:只清洗那 1 条(模型调用恰好 +1),标记记录 +1;
4) 并发清洗:批=10、并发=4;11 条 → 2 批。模型 stub 为真实延迟 1.5s 的本地线程服务
   (8130):并行时 2 批 ≈1.5-2s,串行需 ≥3s。route 层的同步 sleep 会把 playwright
   事件循环串行化,无法测并发,故用真实 socket。
在项目根运行(需 8128 静态服务;模型响应被 stub,不消耗配额)。"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import sync_playwright

CHROME = None
FIXTURE = "fixtures/sample10-bookmarks.html"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))


def verdict_count(page):
    return page.evaluate(
        """
    () => new Promise((resolve) => {
      const req = indexedDB.open('favorites-escape-room-local');
      req.onsuccess = () => {
        const tx = req.result.transaction('verdicts').objectStore('verdicts').count();
        tx.onsuccess = () => resolve(tx.result);
      };
    })
    """
    )


def wait_verdicts(page, n, timeout=30):
    """轮询等待判定记录数达到 n(透明、可推断,不依赖 wait_for_function 语义)。"""
    t0 = time.time()
    last = -1
    while time.time() - t0 < timeout:
        last = verdict_count(page)
        if last == n:
            return True
        time.sleep(0.3)
    print(f"  [wait_verdicts 超时] 期望 {n},最后 {last}")
    return False


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    state = {"calls": 0}

    def stub(route):
        state["calls"] += 1
        body = json.loads(route.request.post_data)
        prompt = json.loads(body["messages"][1]["content"])
        out = []
        for i, it in enumerate(prompt.get("items", [])):
            out.append(
                {
                    "id": it["id"],
                    "status": "archive" if (state["calls"] == 1 and i == 0) else "keep",
                    "topics": ["测试"],
                    "reason": "模型复核通过",
                    "intent": "",
                }
            )
        payload = {"choices": [{"message": {"content": json.dumps({"items": out})}}]}
        route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))

    page.route("**/api/step**", stub)
    # 2026-08-29 稳定性:拦截阶段4 desc 富化的真实外网抓取(4s 超时/条),
    # 否则并发墙钟断言会把抓取耗时误判为清洗串行
    meta_stub = lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps({"results": {}}))
    page.route("**/fetch-meta**", meta_stub)
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)

    # 1) 首次导入 → 全量标记 + 1 批模型调用(sample10 严格清洗后簇不足 4 条,走回落)
    page.set_input_files("#homeFile", FIXTURE)
    wait_verdicts(page, 10)
    check("首次导入:标记记录覆盖全量条目", verdict_count(page) == 10, f"calls={state['calls']}")
    check("首次导入:模型调用 1 批", state["calls"] == 1, f"calls={state['calls']}")

    # 2) 同文件重导 → 零模型调用
    page.set_input_files("#homeFile", FIXTURE)
    page.wait_for_timeout(1200)
    check("同文件重导:零模型调用", state["calls"] == 1, f"calls={state['calls']}")
    check("同文件重导:标记记录不变", verdict_count(page) == 10, f"verdicts={verdict_count(page)}")

    # 3) 追加 1 条新书签 → 只清洗增量
    raw = open(FIXTURE, encoding="utf-8").read()
    extra = '<DT><A HREF="https://newitem.example.com/page" ADD_DATE="1640000000">全新增量条目</A>'
    modified = raw.replace("</DL>", extra + "</DL>", 1)
    assert extra in modified
    open("fixtures/_sample11_modified.html", "w", encoding="utf-8").write(modified)
    page.set_input_files("#homeFile", "fixtures/_sample11_modified.html")
    wait_verdicts(page, 11)
    check("增量导入:恰好 +1 次模型调用", state["calls"] == 2, f"calls={state['calls']}")
    check("增量导入:标记记录 11 条", verdict_count(page) == 11, f"verdicts={verdict_count(page)}")
    check(
        "增量导入:状态栏含通过 11 条",
        "（11 条）" in page.evaluate("() => document.getElementById('homeStatus').textContent"),
    )

    # 4) 并发清洗:批=10、并发=4;11 条 → 2 批,真实延迟 1.5s 的本地服务
    class DelayedCleanHandler(BaseHTTPRequestHandler):
        calls = 0

        def log_message(self, *a):
            pass

        def _cors(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

        def do_OPTIONS(self):
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_POST(self):
            size = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(size))
            DelayedCleanHandler.calls += 1
            prompt = json.loads(body["messages"][1]["content"])
            out = [
                {"id": it["id"], "status": "keep", "topics": ["测试"], "reason": "并发复核", "intent": ""}
                for it in prompt.get("items", [])
            ]
            payload = json.dumps(
                {"choices": [{"message": {"content": json.dumps({"items": out})}}]}
            ).encode("utf-8")
            time.sleep(1.5)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self._cors()
            self.end_headers()
            self.wfile.write(payload)

    stub_server = ThreadingHTTPServer(("127.0.0.1", 8130), DelayedCleanHandler)
    threading.Thread(target=stub_server.serve_forever, daemon=True).start()

    page2 = b.new_page()
    page2.add_init_script(
        "window.__FAVORITES_ROOM_CONFIG__ = {"
        "  endpoint: 'http://127.0.0.1:8130/clean', apiKey: 'stub',"
        "  cleanBatchSize: 10, cleanConcurrency: 4 };"
    )
    page2.route("**/fetch-meta**", meta_stub)
    page2.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page2.wait_for_function("() => !!window.__favoriteRoomPipeline", timeout=15000)
    t0 = time.time()
    page2.set_input_files("#homeFile", "fixtures/_sample11_modified.html")
    ok = wait_verdicts(page2, 11)
    wall = time.time() - t0
    check(
        "并发清洗:11 条批 10 → 2 批,调用数 2",
        ok and DelayedCleanHandler.calls == 2,
        f"calls={DelayedCleanHandler.calls} wall={wall:.1f}s",
    )
    check(
        "并发清洗:墙钟证明并行(%.1fs < 3.0s,串行需 ≥3s)" % wall,
        ok and wall < 3.0,
    )
    check("并发清洗:标记记录 11 条", verdict_count(page2) == 11, f"verdicts={verdict_count(page2)}")
    page2.close()
    stub_server.shutdown()
    b.close()

print(f"\n===== verify_verdict_flow: {sum(results)}/{len(results)} 通过 =====")
raise SystemExit(0 if all(results) else 1)
