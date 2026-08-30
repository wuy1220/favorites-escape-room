# -*- coding: utf-8 -*-
"""compileLevel 编译路径无 LLM 冒烟(在项目根目录运行,需 8128 静态服务):

1. 平铺 'step' 分支正例:合成设计稿(素材 id=清洗记录 id,与 designWindow 输出同构)
   → compile → solveLevel 判可解,designSource='step';
2. 孤儿负例:combine 产物无人引用/目标未被复用/非末步 → 必须 structural 抛错
   (覆盖 v7.2 语义对齐后的孤儿守卫,js/pipeline.js compileLevel flat 分支);
3. compileFixed 固定模板:compileFixed → beats 齐全且可解
   (覆盖 generate() 三轮全败后的保底编译路径);
4. REF_LEVELS 兜底路径金标准:范例关卡 id 与记录不匹配,走 'local' 兜底编译,
   锁定当前输出(beats/items 数与可解性),防止该分支无声劣化。

全程不调用任何 LLM 接口。"""
import json
import os
from playwright.sync_api import sync_playwright

CHROME = r"C:/Users/30807/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))


RECORDS_JS = """
() => Array.from({length: 6}, (_, i) => ({
  id: 'rec-' + i, title: '测试素材' + i, domain: 'example.com',
  url: 'https://example.com/t' + i,
  dateAdded: new Date(1700000000000 + i * 60000).toISOString(),
  status: 'keep', folder: '编译冒烟',
}))
"""

ITEMS = [
    {'id': 'rec-0', 'role': 'tool', 'sceneName': '撬棍', 'reason': '能撬开东西'},
    {'id': 'rec-1', 'role': 'clue', 'sceneName': '便签', 'reason': '写着提示'},
    {'id': 'rec-2', 'role': 'tool', 'sceneName': '接线钳', 'reason': '能接电线'},
    {'id': 'rec-3', 'role': 'clue', 'sceneName': '说明书', 'reason': '记录步骤'},
    {'id': 'rec-4', 'role': 'lock', 'sceneName': '密码锁', 'reason': '三位数字密码'},
    {'id': 'rec-5', 'role': 'reward', 'sceneName': '钥匙卡', 'reason': '出口凭证'},
]


def design(orphan):
    beats = [
        {'id': 's1', 'title': '看便签', 'action': 'inspect', 'uses': ['rec-0'], 'reveals': ['rec-1']},
        {'id': 's2', 'title': '撬开接线盒', 'action': 'combine', 'uses': ['rec-0', 'rec-1'],
         'product': '组合甲'},
    ]
    if orphan:
        beats.append({'id': 's3', 'title': '孤立组合', 'action': 'combine',
                      'uses': ['result:s2', 'rec-3'], 'product': '无人引用的产物'})
        beats.append({'id': 's4', 'title': '输密码', 'action': 'password', 'uses': ['rec-4'],
                      'expected': '123', 'reveals': ['rec-5'], 'requires': ['s1']})
        beats.append({'id': 's5', 'title': '交付离开', 'action': 'deliver',
                      'uses': ['result:s2'], 'requires': ['s4']})
    else:
        beats.append({'id': 's3', 'title': '接好线路', 'action': 'combine',
                      'uses': ['result:s2', 'rec-2'], 'product': '终产物'})
        beats.append({'id': 's4', 'title': '输密码', 'action': 'password', 'uses': ['rec-4'],
                      'expected': '123', 'reveals': ['rec-5'], 'requires': ['s1']})
        beats.append({'id': 's5', 'title': '交付离开', 'action': 'deliver',
                      'uses': ['result:s3'], 'requires': ['s4']})
    result = {
        'title': '编译冒烟关', 'premise': '一间测试用的小房间。',
        'objective': '解开密码锁,带着终产物离开。', 'targetMinutes': 10,
        'hints': ['先观察。', '便签要配合撬棍。', '接线钳能延长组合。', '密码在说明书里。',
                  '密码锁在等着。', '带着东西从出口离开。'],
        'items': ITEMS, 'beats': beats,
    }
    # designWindow 正常输出携带 mechanics,孤儿守卫对其走宽松语义;
    # 负例刻意不带 mechanics,让孤儿守卫以严格模式生效
    if not orphan:
        result['mechanics'] = ['便签提示与撬棍组合打开接线盒,再接线通向密码锁。']
    return result


RUN_STEP = """
(payload) => {
  const pipe = window.__favoriteRoomPipeline;
  const cleaned = {records: payload.records, controlledIds: payload.records.map(r => r.id),
                   duplicates: [], stats: {input: 6, unique: 6, duplicates: 0}};
  try {
    const draft = pipe.compile(cleaned, null, payload.design, '编译冒烟');
    const solve = pipe.solveLevel(draft.level);
    return {threw: false, designSource: draft.level.validation.designSource,
            beats: draft.level.beats.length, solvable: !!solve.solvable,
            detail: String(solve.detail || '').slice(0, 100)};
  } catch (e) {
    return {threw: true, structural: e && e.structural === true,
            message: String(e && e.message || e).slice(0, 120)};
  }
}
"""

RUN_FIXED = """
(records) => {
  const pipe = window.__favoriteRoomPipeline;
  const cleaned = {records, controlledIds: records.map(r => r.id)};
  const draft = pipe.compileFixed(cleaned, {title: '固定模板冒烟', premise: '不经过 LLM 的固定关卡。'}, '固定模板');
  const solve = pipe.solveLevel(draft.level);
  return {beats: draft.level.beats.length, solvable: !!solve.solvable,
          detail: String(solve.detail || '').slice(0, 100)};
}
"""

RUN_TUTORIAL = """
(txt) => {
  const pipe = window.__favoriteRoomPipeline;
  const lvl = JSON.parse(txt).level;
  const solve = pipe.solveLevel(lvl);
  const beats = lvl.beats || [];
  const del = beats.find((b) => b.action === 'deliver');
  const reach = new Set(), stack = [String(del ? del.id : '')];
  while (stack.length) {
    const id = stack.pop();
    if (!id || reach.has(id)) continue;
    reach.add(id);
    const bb = beats.find((x) => String(x.id) === id);
    ((bb && bb.requires) || []).forEach((r) => stack.push(String(r)));
  }
  return {solvable: !!solve.solvable, beats: beats.length,
          hidden: (lvl.items || []).filter((i) => i.hidden).length,
          deliverReach: reach.size,
          detail: String(solve.detail || '').slice(0, 90)};
}
"""

RUN_REF = """
(idx) => {
  const pipe = window.__favoriteRoomPipeline;
  const lv = window.__REF_LEVELS__[idx];
  /* 素材 id 与范例 items 对齐 → 走 compileLevel scenes 分支(多层房间,权威路径) */
  const items = (lv.scenes || []).flatMap((s) => s.items || []);
  const records = items.map((it) => ({
    id: it.id, title: it.sceneName || it.id, domain: 'example.com',
    url: 'https://example.com/' + it.id, dateAdded: new Date().toISOString(),
    status: 'keep', folder: '编译冒烟',
  }));
  const cleaned = {records, controlledIds: records.map((r) => r.id), duplicates: [],
                   stats: {input: records.length, unique: records.length, duplicates: 0}};
  const draft = pipe.compile(cleaned, null, lv, '编译冒烟');
  const solve = pipe.solveLevel(draft.level);
  /* 终局收束闭包:deliver 的 requires 传递闭包必须横跨 ≥2 场景——
     跨场景 requires 在编译期曾被场景内 bMap 过滤静默剥掉(2026-08-30 实测),这里盯死 */
  const lvl = draft.level;
  const sceneOf = new Map();
  (lvl.scenes || []).forEach((sc, si) => (sc.beatIds || []).forEach((b) => sceneOf.set(b, si)));
  const del = (lvl.beats || []).find((b) => b.action === 'deliver');
  const reach = new Set();
  if (del) {
    const seen = new Set(), stack = [String(del.id)];
    while (stack.length) {
      const id = stack.pop();
      if (seen.has(id)) continue;
      seen.add(id);
      if (sceneOf.has(id)) reach.add(sceneOf.get(id));
      const bb = (lvl.beats || []).find((x) => String(x.id) === id);
      ((bb && bb.requires) || []).forEach((r) => { if (sceneOf.has(String(r))) stack.push(String(r)); });
    }
  }
  return {title: draft.level.title, scenes: (lvl.scenes || []).length,
          beats: lvl.beats.length, items: lvl.items.length,
          designSource: lvl.validation.designSource, solvable: !!solve.solvable,
          closure: reach.size, locked: (lvl.scenes || []).filter((s) => s.locked).length,
          digestN: (lvl.items || []).filter((it) => (it.digest || '').trim()).length,
          factsN: (lvl.items || []).filter((it) => (it.facts || []).length).length,
          detail: String(solve.detail || '').slice(0, 90)};
}
"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME)
    page = b.new_page()
    page.goto("http://127.0.0.1:8128/", wait_until="domcontentloaded")
    page.wait_for_function(
        "() => !!(window.__favoriteRoomPipeline && window.__REF_LEVELS__)", timeout=15000
    )

    good = page.evaluate(RUN_STEP, {"records": page.evaluate(RECORDS_JS), "design": design(False)})
    check("平铺 step 分支:合法设计编译+求解通过",
          not good["threw"] and good.get("solvable") and good.get("designSource") == "step"
          and good.get("beats", 0) >= 3,
          f"designSource={good.get('designSource')} beats={good.get('beats')}(编译有损折叠,>=3 即可) "
          f"solvable={good.get('solvable')} {good.get('detail', good.get('message', ''))}")

    bad = page.evaluate(RUN_STEP, {"records": page.evaluate(RECORDS_JS), "design": design(True)})
    check("平铺 step 分支:孤儿产物被 structural 拦截",
          bad["threw"] and bad["structural"] and "孤儿" in bad["message"], bad["message"])

    fixed = page.evaluate(RUN_FIXED, page.evaluate(RECORDS_JS))
    check("compileFixed 固定模板:编译+求解通过",
          fixed["beats"] > 0 and fixed["solvable"],
          f"beats={fixed['beats']} solvable={fixed['solvable']} {fixed['detail']}")

    for idx, want_scenes in ((0, 2), (1, 2), (2, 2)):
        r = page.evaluate(RUN_REF, idx)
        name = f"REF_LEVELS[{idx}]《{r['title']}》scenes 编译金标准"
        check(
            name,
            r["solvable"] and r["designSource"] == "step-scenes" and r["scenes"] == want_scenes,
            f"scenes={r['scenes']} beats={r['beats']} items={r['items']} "
            f"designSource={r['designSource']} solvable={r['solvable']} {r['detail']}",
        )
        check(
            f"REF_LEVELS[{idx}] 房间全亮(locked={r['locked']})",
            r["locked"] == 0,
        )
        check(
            f"REF_LEVELS[{idx}] 终局收束跨房间(闭包 {r['closure']} 场景)",
            r["closure"] >= 2,
        )

    tut_path = os.path.join(ROOT, "sample-puzzles", "tutorial.json")
    r_tut = page.evaluate(RUN_TUTORIAL, open(tut_path, encoding="utf-8").read())
    check(
        "新手教程关 求解+线性链金标准",
        r_tut["solvable"] and r_tut["beats"] >= 4 and r_tut["deliverReach"] >= 4
        and r_tut["hidden"] >= 4,
        f"beats={r_tut['beats']} solvable={r_tut['solvable']} "
        f"deliverReach={r_tut['deliverReach']} hidden={r_tut['hidden']} {r_tut['detail']}",
    )
    refc = page.evaluate(RUN_REF, 2)
    check(
        "REF_LEVELS[2] 内容接地字段透传(digest/facts)",
        refc["digestN"] >= 5 and refc["factsN"] >= 3,
        f"digest={refc['digestN']}/6 facts={refc['factsN']}/6",
    )
    b.close()

print(f"\n===== test_compile: {sum(results)}/{len(results)} 通过 =====")
raise SystemExit(0 if all(results) else 1)
