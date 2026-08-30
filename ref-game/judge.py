# -*- coding: utf-8 -*-
"""LLM 生成结果评判器。

用法: python judge.py llm_out/xxx_level.json [llm_out/yyy_level.json ...]
维度(每项 0-10 分):
  1. 结构完整:items 6 条 / id 原样
  2. 角色匹配:role 与机制 positions 顺序一致
  3. 引用真实性:reason 中的数字/时刻/路径词能在素材元数据里找到
  4. 交叉密度:reason 引用其他素材 title 关键词的数量(关系层质量)
  5. 命名质量:scene_name 空洞修辞检测(黑话词库)
  6. 方向铁律:lock 是否像顺序关键 / red_herring 是否诱人但非关键
"""
import os, re, sys, json

BLACK = ["沉默", "引路", "呢喃", "低语", "宿命", "回响", "守护者", "见证者", "答案", "真相",
         "迷雾", "幽暗", "宿命", "不可名状", "凝视", "彼岸", "命运", "若隐若现", "扑朔迷离"]
TITLE_STOP = set("的是一了不在有和就都而及与或")

def load(path):
    return json.load(open(path, encoding="utf-8"))

def time_patterns(s):
    return re.findall(r'\d{1,2}[:：]\d{2}|\d{4}', s)

def title_words(title):
    words = re.findall(r'[\u4e00-\u9fa5]{2,}|[A-Za-z0-9]+', title)
    return [w for w in words if w not in TITLE_STOP and len(w) > 1]

def judge(path):
    d = load(path)
    lv = d.get("level", d)
    items = lv.get("items") or []
    meta = d.get("meta", {})
    segs = meta.get("segs", [])
    # 素材池(所有素材的真实文本,用于引用真实性检查)
    pool_txt = " ".join(f"{s.get('title','')} {s.get('host','')} {s.get('folder','')} {s.get('dateAdded','')}" for s in segs)
    pool_words = set()
    for s in segs:
        pool_words.update(title_words(s.get("title", "")))
    pool_words.discard("")

    expected_roles = ["clue", "clue", "tool", "lock", "transform", "red_herring"]
    res = {"file": os.path.basename(path), "meta": meta}
    # 1 结构
    ids = [str(x.get("id")) for x in items]
    res["结构完整"] = (len(items) == 6 and len(set(ids)) == 6 and all(i.get("scene_name") and i.get("reason") for i in items))
    # 2 角色匹配
    roles = [x.get("role") for x in items]
    res["角色匹配"] = roles == expected_roles
    # 3/4/5 每条 reason 评判
    cross_scores, truth_scores, name_scores = [], [], []
    for i, it in enumerate(items):
        reason, name = it.get("reason", ""), it.get("scene_name", "")
        # 交叉密度:引用其他素材 title 词数(子串匹配:4字词写2-3字也算)
        own = set(title_words(segs[i].get("title", ""))) if i < len(segs) else set()
        def _hit(w, text):
            if w in text: return True
            if len(w) >= 3:
                for _sub in (w[:2], w[2:], w[-2:], w[:3]):
                    if len(_sub) >= 2 and _sub in text: return True
            return False
        cross = sum(1 for w in pool_words if _hit(w, reason) and not _hit(w, own and own or reason))
        cross = sum(1 for w in pool_words if _hit(w, reason) and not _hit(w, " ".join(own)))
        cross_scores.append(min(10, cross * 2))
        # 引用真实性:reason 中的数字/时刻是否真实(或不在池中则不扣)
        bad = 0
        for t in time_patterns(reason):
            if t not in pool_txt:
                bad += 1
        truth_scores.append(max(0, 10 - bad * 3))
        # 命名质量:黑话检测
        bad_words = [b for b in BLACK if b in name]
        name_scores.append(max(0, 10 - len(bad_words) * 5))
    res["交叉密度"] = round(sum(cross_scores) / len(cross_scores), 1) if cross_scores else 0
    res["引用真实性"] = round(sum(truth_scores) / len(truth_scores), 1) if truth_scores else 0
    res["命名质量"] = round(sum(name_scores) / len(name_scores), 1) if name_scores else 0
    # 6 方向铁律
    lock = items[3].get("reason", "") if len(items) > 3 else ""
    herr = items[5].get("reason", "") if len(items) > 5 else ""
    res["lock像关键"] = any(k in lock for k in ["顺序", "先后", "第", "依次", "按", "先", "数"])
    herr_ok = True
    _NEG = ("不是", "并非", "从来", "没有", "毫无", "无关", "不需要", "未必", "从不", "没被", "从未", "不属于", "碰不到", "无法", "以为", "看似", "像是", "仿佛")
    for _k in ["最后一环", "通关", "出口", "最终答案", "关键所在", "解谜钥匙", "通关钥匙"]:
        for _m in re.finditer(re.escape(_k), herr):
            _pre = herr[max(0, _m.start() - 6):_m.start()]
            _aft = herr[_m.end():_m.end() + 6]
            if any(_n in _pre or _n in _aft for _n in _NEG):
                continue
            herr_ok = False
    res["herring非关键"] = herr_ok
    return res

def main():
    files = sys.argv[1:]
    if not files:
        base = os.path.dirname(os.path.abspath(__file__))
        files = [os.path.join(base, "llm_out", f) for f in sorted(os.listdir(os.path.join(base, "llm_out"))) if f.endswith("_level.json")]
    rows = [judge(f) for f in files]
    header = ["file", "结构完整", "角色匹配", "交叉密度", "引用真实性", "命名质量", "lock像关键", "herring非关键"]
    print(f"{'文件':<22} {'结构':<4} {'角色':<4} {'交叉':<5} {'真实':<5} {'命名':<5} {'lock':<4} {'herring':<5}")
    for r in rows:
        print(f"{r['file']:<22} {str(r['结构完整']):<4} {str(r['角色匹配']):<4} {r['交叉密度']:<5} {r['引用真实性']:<5} {r['命名质量']:<5} {str(r['lock像关键']):<4} {str(r['herring非关键']):<5}")
    # 平均值
    def avg(key):
        vals = [r[key] for r in rows if isinstance(r[key], (int, float))]
        return round(sum(vals) / len(vals), 1) if vals else "-"
    print("-" * 60)
    print(f"{'平均':<22} {'-':<4} {'-':<4} {avg('交叉密度'):<5} {avg('引用真实性'):<5} {avg('命名质量'):<5}")

if __name__ == "__main__":
    main()
