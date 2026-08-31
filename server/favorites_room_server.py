import ipaddress
import json
import os
import re
import socket
import zlib
from urllib.parse import urljoin, urlsplit
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, build_opener, urlopen
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Step Plan uses a separate API namespace and billing pool from the ordinary
# OpenAI-compatible API. Keep the Plan endpoint fixed so requests cannot
# silently fall back to account-balance billing.
STEP_URL = "https://api.stepfun.com/step_plan/v1/chat/completions"
STEP_TIMEOUT = 300
GLM_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
GLM_TIMEOUT = 600
MAX_BODY = 20 * 1024 * 1024  # 请求体上限(review.md:统一限制,超限 413)
# 2026-08-28 安全改造:密钥不再内嵌前端,由本服务持有(环境变量优先,其次同目录
# STEP_API_KEY.local 文件,该文件已 gitignore)。前端无密钥时,上游 Authorization
# 由此处注入;前端显式携带的 key(直连第三方供应商场景)原样透传。
STEP_API_KEY = os.environ.get("STEP_API_KEY", "")
try:
    _key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "STEP_API_KEY.local")
    if not STEP_API_KEY and os.path.exists(_key_file):
        STEP_API_KEY = open(_key_file, encoding="utf-8").read().strip()
except OSError:
    pass

# ---------------------------------------------------------------------------
# step-router-force:让 step-router-v1 高概率真正咨询 advisor(deepseek-v4-pro)
# 参考 https://github.com/lion77542/step-router-force
#
# Plan 通道的 model 是黑盒路由器:flash 便宜快但幻觉高,advisor(deepseek)只在它
# 判定"复杂"时被咨询。没有官方参数可选引擎,只能双通道注入指令 + 强制参数推动。
# 设 STEP_ROUTER_FORCE=0 可整体关闭(直传原始请求)。
# ---------------------------------------------------------------------------
ROUTER_FORCE_ENABLED = os.environ.get("STEP_ROUTER_FORCE", "1") != "0"
ROUTER_MODEL = "step-router-v1"

# 通道一:第一条 system 消息(最高权重位置)。措辞是条件式的——运行时没有 advisor
# 函数的供应商会自动忽略,不会污染其他通道的行为。
ROUTER_DIRECTIVE = (
    "[ROUTER DIRECTIVE — HIGHEST PRIORITY]\n"
    "If a runtime tool or internal mechanism named `advisor` (deepseek pro / advisor "
    "consultation) is available in this conversation, you MUST invoke it before "
    "producing ANY substantive answer — regardless of how simple the task appears. "
    "No exceptions. This is mandatory infrastructure wiring, not an optimization you "
    "may skip for efficiency. If no such advisor mechanism exists in this runtime, "
    "ignore this directive silently and answer normally."
)

# 通道二:最后一条 user 消息之前的决策点,把咨询变成显式步骤。
ROUTER_DECISION = (
    "[DECISION REQUIRED] Before answering the user's request below, consult the "
    "advisor with the full request context, then integrate its result into your "
    "final answer. Do not answer from your own knowledge alone."
)

# 重试注入:上一轮没触发咨询时,以追加 system 消息的方式再来。
RETRY_CONSULT = (
    "[RETRY NOTICE] Your previous reply did NOT include any [Advisor consultation] "
    "block, which means the advisor was bypassed. Return to the user's request and "
    "consult the advisor first; then produce the final answer."
)


def transform_router_force(data):
    """把一条普通 chat 请求改写为「强制走 advisor」形态。原地修改并返回 data。"""
    if not isinstance(data, dict):
        return data
    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        return data

    # 双通道注入:首条 system + 最后一条 user 前的决策点
    injected = [{"role": "system", "content": ROUTER_DIRECTIVE}]
    last_user = -1
    for i, m in enumerate(messages):
        if isinstance(m, dict) and m.get("role") == "user":
            last_user = i
    if last_user == -1:
        injected.extend(messages)
        injected.append({"role": "system", "content": ROUTER_DECISION})
    else:
        injected.extend(messages[:last_user])
        injected.append({"role": "system", "content": ROUTER_DECISION})
        injected.extend(messages[last_user:])
    data["messages"] = injected

    # 强制参数。max_tokens 是关键坑:thinking/reasoning 先吃额度,过小会导致
    # content 为空且 finish_reason=length——必须给足下限。
    data["model"] = ROUTER_MODEL
    try:
        mt = int(data.get("max_tokens") or 0)
    except (TypeError, ValueError):
        mt = 0
    # 2026-08-28:advisor 对复杂任务(如 scenes 设计)的思考会吃掉大量 max_tokens,
    # 32000 下限实测被思考耗尽导致 finish=length、正文截断;提到 64000(模型上限 128K)。
    data["max_tokens"] = max(64000, min(mt, 250000)) if mt else 64000
    data["temperature"] = 0.2
    # 客户端常带 thinking:{type:'disabled'}——直接关掉了路由器的推理能力,
    # 必须改回启用并给预算,否则注入完全无效。
    data["thinking"] = {"type": "enabled", "budget_tokens": 8000}
    return data


def response_lacks_consult(content):
    """响应层检测:advice-form 反问 或 全程没有 Advisor 块 -> 视为 flash 直接作答。"""
    text = (content or "").strip()
    has_block = "[Advisor consultation" in text
    advice_form = (
        len(text) < 200
        and ("?" in text or "？" in text)
        and any(k in text for k in ("请告诉", "请问", "请提供", "需要了解", "为了更好"))
    )
    return advice_form or not has_block


def build_retry_messages(messages):
    extra = {"role": "system", "content": RETRY_CONSULT}
    out = list(messages) + [extra]
    return out


class _NoRedirect(HTTPRedirectHandler):
    """禁用 urlopen 自动跟随重定向:每一跳都重新过 SSRF 校验。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER_NO_REDIRECT = build_opener(_NoRedirect)


def _assert_safe_url(url):
    """SSRF 防护(2026-08-28):仅 http/https,且解析出的全部地址不得为
    回环/私网/链路本地/保留/多播——/fetch-meta 由浏览器端驱动,必须防止
    被用作探测本机与内网的跳板。"""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise ValueError("仅支持 http/https")
    host = parts.hostname or ""
    if not host:
        raise ValueError("缺少主机名")
    if re.match(r"^(?:\d{1,3}\.){3}\d{1,3}$", host):
        addrs = [ipaddress.ip_address(host)]
    else:
        try:
            infos = socket.getaddrinfo(host, None)
        except OSError:
            raise ValueError("域名无法解析")
        addrs = [ipaddress.ip_address(i[4][0]) for i in infos]
    for addr in addrs:
        if (
            addr.is_loopback
            or addr.is_private
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_multicast
            or addr.is_unspecified
        ):
            raise ValueError("禁止访问内网/保留地址")
    return url


_FETCH_HEADERS = {
    # 2026-08-30:裸爬虫 UA 会被 bilibili/贴吧/Hello算法 直接 403/429 拒掉,
    # 换成带 Accept/Accept-Language 的浏览器形头,可显著提高取回率。
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6",
}

_DESC_META_KEYS = {"description", "og:description", "twitter:description", "sailthru.description"}


def _extract_meta_desc(html):
    """逐个扫 <meta> 标签取描述:兼容 name=/property=/itemprop= 三种写法与属性任意顺序。
    旧实现只匹配 name="description|og:description",漏掉了 property="og:description"
    (og 系列的事实标准写法)与 twitter:description,SPA 站点因此几乎全军覆没。"""
    fallback = ""
    for tag in re.findall(r"<meta\b[^>]*>", html, re.I)[:80]:
        key_m = re.search(r'(?:name|property|itemprop)=["\']([^"\']+)["\']', tag, re.I)
        con_m = re.search(r'content=["\'](.*?)["\']', tag, re.I | re.S)
        if not key_m or not con_m:
            continue
        if key_m.group(1).strip().lower() not in _DESC_META_KEYS:
            continue
        val = re.sub(r"\s+", " ", unescape(con_m.group(1))).strip()
        if not val:
            continue
        if len(val) >= 20:
            return val[:300]
        if not fallback:
            fallback = val
    return fallback


def _extract_jsonld_desc(html):
    """JSON-LD 结构化数据的 description(视频/商品页常把它写在这里而非 meta)。"""
    for m in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.I | re.S,
    )[:6]:
        try:
            data = json.loads(m.strip())
        except ValueError:
            continue
        for obj in data if isinstance(data, list) else [data]:
            if isinstance(obj, dict) and isinstance(obj.get("description"), str):
                val = re.sub(r"\s+", " ", unescape(obj["description"])).strip()
                if len(val) >= 20:
                    return val[:300]
    return ""


def _extract_body_desc(html):
    """正文回退:SPA 壳页没有 meta/JSON-LD,取第一段 ≥40 字的可见段落充当描述。"""
    body = re.sub(r"<(script|style|noscript)\b.*?</\1>", " ", html, flags=re.I | re.S)
    for p in re.findall(r"<p\b[^>]*>(.*?)</p>", body, re.I | re.S)[:40]:
        text = re.sub(r"<[^>]+>", " ", p)
        text = re.sub(r"\s+", " ", unescape(text)).strip()
        if len(text) >= 40:
            return text[:300]
    return ""


def _extract_state_desc(html):
    """SPA 内嵌状态回退:壳页常把数据放在 __INITIAL_STATE__ 等脚本 JSON 里,
    没有任何服务端可见文本;从内嵌 JSON 里捞 "description"/"desc" 字段。"""
    for key in ("description", "desc", "summary"):
        for m in re.finditer(r'"%s"\s*:\s*"((?:[^"\\]|\\.)*)"' % key, html):
            try:
                val = json.loads('"%s"' % m.group(1))
            except ValueError:
                continue
            val = re.sub(r"\s+", " ", unescape(val)).strip()
            if len(val) >= 20:
                return val[:300]
    return ""


def fetch_one(url, timeout):
    """抓单个页面: title + description。失败降级返回错误标记, 不抛异常。
    重定向手动跟随(最多 2 跳),每跳重新做 SSRF 校验。
    描述提取链:meta(og/twitter/description) → JSON-LD → 正文首段。"""
    try:
        current = _assert_safe_url(url)
    except ValueError as e:
        return {"title": "", "desc": "", "status": str(e)}
    chunk = b""
    charset = ""
    status = "dead"
    final_url = current
    try:
        for hop in range(3):
            request = Request(current, headers=_FETCH_HEADERS, method="GET")
            try:
                with _OPENER_NO_REDIRECT.open(request, timeout=timeout) as response:
                    status = response.status
                    # 读前 256KB:meta/JSON-LD 在头部,正文回退也需要一段实际内容。
                    # bilibili 等站点不协商、无条件回 gzip,而 urllib 不自动解压——
                    # 不处理会拿到二进制垃圾,标题描述全部提取失败(2026-08-30 实测)。
                    raw = response.read(262144)
                    encoding = (response.headers.get("Content-Encoding") or "").lower()
                    try:
                        if "gzip" in encoding:
                            raw = zlib.decompressobj(31).decompress(raw, 1048576)
                        elif "deflate" in encoding:
                            raw = zlib.decompressobj().decompress(raw, 1048576)
                    except (zlib.error, OSError):
                        pass  # 解压失败就按原文继续,可能本来就是裸内容
                    chunk = raw
                    charset = response.headers.get_content_charset() or ""
                    final_url = response.geturl()
                break
            except HTTPError as error:
                if error.code in (301, 302, 303, 307, 308) and hop < 2:
                    loc = error.headers.get("Location")
                    if loc:
                        current = _assert_safe_url(urljoin(current, loc))
                        continue
                status = error.code
                break
            except (URLError, socket.timeout, ValueError, OSError):
                status = "dead"
                break
    except ValueError as e:
        return {"title": "", "desc": "", "status": str(e)}
    if status != 200:
        return {"title": "", "desc": "", "status": status}
    _ = final_url
    if not charset:
        sniff = re.search(r'<meta[^>]+charset=["\']?([\w-]+)', chunk[:4096].decode("ascii", "ignore"), re.I)
        charset = sniff.group(1) if sniff else "utf-8"
    try:
        html = chunk.decode(charset, errors="replace")
    except LookupError:
        html = chunk.decode("utf-8", errors="replace")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    title = unescape(title_match.group(1)).strip() if title_match else ""
    if not title:
        og_title = re.search(
            r'<meta[^>]+property=["\']og:title["\'][^>]*content=["\'](.*?)["\']', html, re.I | re.S
        ) or re.search(
            r'<meta[^>]+content=["\'](.*?)["\'][^>]*property=["\']og:title["\']', html, re.I | re.S
        )
        title = unescape(og_title.group(1)).strip() if og_title else ""
    title = re.sub(r"\s+", " ", title)[:200]
    desc = (
        _extract_meta_desc(html) or _extract_jsonld_desc(html) or _extract_state_desc(html)
        or _extract_body_desc(html)
    )
    return {"title": title, "desc": desc, "status": status}


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def end_headers(self):
        # 2026-08-28 收紧:仅回显本机来源的 CORS;不再发送 Private-Network 头——
        # 公网页面由此无法驱动本服务的跨域请求(防驱动式 SSRF)。
        origin = self.headers.get("Origin") or ""
        if re.match(r"^https?://(?:127\.0\.0\.1|localhost|\[::1\])(?::\d+)?$", origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        # 静态资源禁用缓存:否则浏览器会启发式缓存 index.html, reload 拿不到新代码(信息状态机等改动"不生效"的元凶)
        if self.command == "GET" and not self.path.startswith(("/api/", "/fetch-meta")):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def _serve_llm_config(self):
        # review.md P1(2026-08-31):GLM key 不再下发到浏览器——前端拿到的是
        # 本服务代理端点 /api/glm,转发时由服务端注入密钥;其它本机页面也
        # 无法再经此接口读取密钥明文。
        cfg = {}
        key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GLM_API_KEY.local")
        if os.path.exists(key_file):
            cfg = {
                "endpoint": "/api/glm",
                "model": "glm-5.3-flash",
                "thinking": {"type": "enabled"},
                "reasoningEffort": "low",
                "designTimeout": 600000,
                "label": "glm",
                "proxy": True,
            }
        self._reply_json(cfg)

    def do_GET(self):
        # 设计赛马的备用供应商配置(GLM):key 由本地文件持有(GLM_API_KEY.local,
        # 已 gitignore),不入库、不出现在前端源码;无文件时返回空对象,赛马退化为纯 step。
        if self.path.split("?")[0] == "/api/llm-config":
            self._serve_llm_config()
            return
        super().do_GET()

    def _reply_json(self, payload, status=200):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def handle_fetch_meta(self):
        """尽力而为地抓取一批书签 URL 的页面标题与 meta 描述。
        输入: {"urls": ["...", ...], "timeout": 8}
        输出: {"results": {url: {"title": str, "desc": str, "status": int|str}}}
        单条失败不影响其他条目 —— 这层是内容层, 行为层(URL/时间戳)始终可靠。"""
        ok, raw_body = self._read_body()
        if not ok:
            return
        try:
            body = json.loads(raw_body)
            if not isinstance(body, dict):
                raise ValueError("body must be an object")
            urls = [u for u in (body.get("urls") or []) if isinstance(u, str) and u.startswith("http")][:20]
            timeout = min(10, max(3, int(body.get("timeout", 6))))
        except (ValueError, TypeError):
            self._reply_json({"error": {"message": "invalid request body"}}, 400)
            return
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = dict(pool.map(lambda u: (u, fetch_one(u, timeout)), urls))
        self._reply_json({"results": results})

    def _read_body(self):
        """统一读取请求体(review.md:限制大小,非法请求返回 400 而不是断连)。"""
        try:
            size = int(self.headers.get("Content-Length", "0") or "0")
        except (TypeError, ValueError):
            self._reply_json({"error": {"message": "invalid Content-Length"}}, 400)
            return False, None
        if size <= 0:
            self._reply_json({"error": {"message": "empty request body"}}, 400)
            return False, None
        if size > MAX_BODY:
            self._reply_json({"error": {"message": "request body too large"}}, 413)
            return False, None
        try:
            return True, self.rfile.read(size)
        except Exception:
            self._reply_json({"error": {"message": "failed to read request body"}}, 400)
            return False, None

    def handle_glm_proxy(self):
        """review.md P1:GLM 服务端代理——浏览器不持有 key,转发时注入。"""
        ok, raw_body = self._read_body()
        if not ok:
            return
        try:
            data = json.loads(raw_body)
        except (ValueError, TypeError):
            self._reply_json({"error": {"message": "invalid JSON body"}}, 400)
            return
        if not isinstance(data, dict):
            self._reply_json({"error": {"message": "JSON body must be an object"}}, 400)
            return
        key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GLM_API_KEY.local")
        api_key = ""
        if os.path.exists(key_file):
            api_key = open(key_file, encoding="utf-8").read().strip()
        if not api_key:
            self._reply_json({"error": {"message": "GLM key not configured"}}, 503)
            return
        data["stream"] = False
        request = Request(
            GLM_URL,
            data=json.dumps(data).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Connection": "close",
                "Authorization": "Bearer " + api_key,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=GLM_TIMEOUT) as response:
                payload = response.read()
                status = response.status
        except HTTPError as error:
            self._reply_json(error.read(), status=error.code)
            return
        except URLError as error:
            self._reply_json({"error": {"message": str(error.reason)}}, 502)
            return
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        if self.path == "/fetch-meta":
            self.handle_fetch_meta()
            return
        if self.path == "/api/glm":
            # review.md P1(2026-08-31):GLM 服务端代理——浏览器不再持有 key,
            # 转发时由本服务注入 GLM_API_KEY.local 的密钥。
            self.handle_glm_proxy()
            return
        if self.path != "/api/step":
            self.send_error(404)
            return
        ok, raw_body = self._read_body()
        if not ok:
            return
        headers = {"Content-Type": "application/json", "Connection": "close"}
        authorization = (self.headers.get("Authorization") or "").strip()
        # 密钥持有方是本服务:客户端未携带有效 key 时注入 STEP_API_KEY;
        # 客户端显式携带的 key(直连第三方供应商场景)原样透传。
        if authorization and authorization.lower() != "bearer":
            headers["Authorization"] = authorization
        elif STEP_API_KEY:
            headers["Authorization"] = "Bearer " + STEP_API_KEY

        # ---- 响应统一缓冲为 JSON(两种模式都适用);是否注入/强制模型由 ROUTER_FORCE_ENABLED 决定 ----
        # STEP_ROUTER_FORCE=0(直通测试):不注入指令、保留客户端原 model(step-3.7-flash 直答)、
        # 不做 advisor 检测重试;仅保持 stream=false 以便前端 readStepResponse 走 JSON 分支。
        body_bytes = raw_body
        try:
            data = json.loads(raw_body)
        except (ValueError, TypeError):
            data = None
        # review.md 健壮性:JSON 顶层不是对象(如数组)→ 400,不再抛 AttributeError
        if data is not None and not isinstance(data, dict):
            self._reply_json({"error": {"message": "JSON body must be an object"}}, 400)
            return
        direct = False
        if isinstance(data, dict):
            # 清洗快车道(2026-08-28):客户端可对单个任务显式带 router_force:false
            # (清洗是结构化抽取,不需要 advisor 深推理)。直通时保留客户端原
            # model/thinking,跳过注入与 advisor 重试;设计任务不带该字段,照旧强制。
            direct = data.pop("router_force", None) is False
            data["stream"] = False
            if ROUTER_FORCE_ENABLED and not direct:
                transform_router_force(data)
            body_bytes = json.dumps(data).encode("utf-8")

        attempts = 1 if direct else (3 if ROUTER_FORCE_ENABLED else 1)
        if direct:
            print(f"[router-force] 直通快车道: model={data.get('model') if isinstance(data, dict) else '?'}", flush=True)
        last_status, last_payload = 502, b'{"error":{"message":"step upstream unreachable"}}'
        current_body = body_bytes
        for attempt in range(attempts):
            request = Request(STEP_URL, data=current_body, headers=headers, method="POST")
            try:
                with urlopen(request, timeout=STEP_TIMEOUT) as response:
                    payload = response.read()
                    status = response.status
            except HTTPError as error:
                # 请求本身被拒(如上游不认识某字段):原样回传给前端展示
                self._reply_json(error.read(), status=error.code)
                return
            except URLError as error:
                last_status, last_payload = 502, json.dumps({"error": {"message": str(error.reason)}}).encode("utf-8")
                continue

            if attempt == attempts - 1 or not ROUTER_FORCE_ENABLED:
                self._reply_step_json(payload, status)
                return
            # 判定是否真的咨询了 advisor
            try:
                parsed = json.loads(payload)
                content = (parsed.get("choices") or [{}])[0].get("message", {}).get("content") or ""
            except (ValueError, AttributeError):
                content = ""
            if not response_lacks_consult(content):
                self._reply_step_json(payload, status)
                return
            print(f"[router-force] 第 {attempt + 1} 次响应未见 advisor 咨询,注入重试指令后再试", flush=True)
            try:
                retry_data = json.loads(current_body)
                retry_data["messages"] = build_retry_messages(retry_data["messages"])
                current_body = json.dumps(retry_data).encode("utf-8")
            except (ValueError, KeyError):
                self._reply_step_json(payload, status)
                return
            last_status, last_payload = status, payload
        self._reply_step_json(last_payload, last_status)

    def _reply_step_json(self, payload, status):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    port = int(os.environ.get("FAV_ROOM_PORT", "8128"))
    ThreadingHTTPServer(("127.0.0.1", port), lambda *args, **kwargs: Handler(*args, directory=ROOT, **kwargs)).serve_forever()
