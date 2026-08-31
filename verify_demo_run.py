"""演示模式(?demo=1)端到端回归:导入 → 清洗 → 设计竞速 → 挂载 → 交接。

用法: python verify_demo_run.py
退出码 0=通过,1=未通过。断言项见 CHECKS。
"""
import sys
import time

from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:8128/?demo=1'
MOUNT_BUDGET = 75  # 秒
CHECKS = {}


def main():
    errors = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: errors.append('pageerror: ' + str(e)))
        pg.goto(URL)
        pg.wait_for_selector('#demoStart', timeout=30000)
        pg.click('#demoStart')
        t0 = time.time()

        # 1) 关卡挂载(同时流式打印工房技术日志,设计被拒时这里是第一现场)
        mounted = None
        seen = set()
        while time.time() - t0 < MOUNT_BUDGET:
            time.sleep(2)
            try:
                for ln in pg.eval_on_selector_all(
                    '#wbLog > *', 'els => els.map(e => e.textContent.trim())'
                ):
                    if ln and ln not in seen:
                        seen.add(ln)
                        print('[wbLog %3ds] %s' % (int(time.time() - t0), ln[:300]))
            except Exception:
                pass
            try:
                if pg.eval_on_selector('#gameToolbar', 'e => !e.hasAttribute("hidden")'):
                    mounted = time.time() - t0
                    break
            except Exception:
                pass
        CHECKS['关卡挂载(<75s)'] = mounted
        if mounted is None:
            b.close()
            return report(errors)

        time.sleep(2.5)  # 等交接字幕与日志镜像落地

        # 2) 交接字幕
        cap = pg.eval_on_selector('#demoCaptionText', 'e => e.textContent.trim()') or ''
        CHECKS['交接字幕含提示'] = '现在交给你' in cap
        CHECKS['字幕实际内容'] = cap[:40]

        # 3) 日志镜像目标存在(#log 是 startLogMirror 的兜底锚点)
        CHECKS['日志锚点 #log 存在'] = pg.eval_on_selector_all('#log', 'e => e.length') == 1

        # 4) 房间已渲染出可交互节点
        CHECKS['已渲染节点数'] = pg.eval_on_selector_all('.node', 'e => e.length')

        # 5) 挂载的必须是预置关卡本体(demo-gamenight),不是占位设计
        try:
            lv = pg.evaluate(
                "() => { const d = JSON.parse(localStorage.getItem('favorite-room-draft')"
                " || 'null'); return d && d.level ? d.level : null; }"
            )
            CHECKS['关卡标题'] = (lv or {}).get('title')
            ids = [i.get('id') for i in (lv or {}).get('items', [])]
            CHECKS['是 gamenight 本体'] = 'ra-note' in ids and 'ra-disc' in ids
            CHECKS['关卡物件数'] = len(ids)
        except Exception as e:
            CHECKS['关卡标题'] = '读取失败(%s)' % str(e)[:40]
            CHECKS['是 gamenight 本体'] = False

        b.close()
    return report(errors)


def report(errors):
    print('=== 演示模式回归 ===')
    for k, v in CHECKS.items():
        print('  %-22s %s' % (k, v))
    # 挂载本身即意味着 compileLevel + solveLevel 都通过(app.js 只在求解验证
    # 通过后才认这一路为赢家),故不重复调用求解器。
    ok = all(
        [
            CHECKS.get('关卡挂载(<75s)') is not None,
            CHECKS.get('交接字幕含提示') is True,
            CHECKS.get('日志锚点 #log 存在') is True,
            CHECKS.get('已渲染节点数', 0) > 0,
            CHECKS.get('是 gamenight 本体') is True,
        ]
    )
    real = [e for e in errors if 'favicon' not in e]
    if real:
        print('  控制台错误:')
        for e in real[:8]:
            print('    - %s' % e[:200])
        ok = False
    print('结果: %s' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
