# -*- coding: utf-8 -*-
"""
evaluate_tcmeval.py — 用 TCMEval-SDT 训练集验证辨证引擎
=========================================================
输入: data/Train_TCM_Data_v1.json (200 例，含标准答案)
流程:
  1. 每例把 Answers 字母映射到 Options 里的标准证型名
  2. 从 Clinical Data 提取症状, 喂 diagnose()
  3. 输出证型列表 vs 标准证型, 做核心词匹配
输出: 整体匹配率 + 覆盖度 + 待补充证型
⚠️ 仅供项目自评, 不构成医学结论
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.agent import diagnose

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "Train_TCM_Data_v1.json")

# 证型名规范化: 去掉 证/症/型/之/体/虚/实 等字, 便于核心词匹配
_STRIP = "证症型之体虚邪"
def _norm(s):
    return re.sub(r"[%s\s]" % _STRIP, "", s)

def _match(pred, golds):
    """pred: 我的证型id; golds: 标准证型名列表。返回是否匹配。"""
    pn = _norm(pred)
    for g in golds:
        gn = _norm(g)
        if not gn:
            continue
        if pn == gn or pn in gn or gn in pn:
            return True
        # 共享≥2字核心词(排除单字)
        if len(pn) >= 2 and len(gn) >= 2:
            hits = sum(1 for i in range(len(pn)) for j in range(len(gn)) if pn[i] == gn[j])
            if hits >= 2:
                return True
    return False

def parse_options(opt_str):
    """'A:风湿;B:气虚...' -> {字母: 证型名}"""
    d = {}
    if not opt_str:
        return d
    for seg in str(opt_str).replace("；", ";").split(";"):
        seg = seg.strip()
        m = re.match(r"^([A-J])\s*[:：]?\s*(.+)$", seg)
        if m:
            d[m.group(1)] = m.group(2).strip()
    return d

def main():
    data = json.load(open(DATA, encoding="utf-8"))
    total = len(data)
    covered = 0      # 我的引擎给出非空结果
    correct = 0
    per_gold_correct = {}
    per_gold_total = {}
    missing = {}     # 标准证型名 -> 该病例诊断结果

    for c in data:
        opts = parse_options(c.get("Options of TCM Syndrome"))
        ans_letters = [x.strip() for x in str(c.get("Answers of TCM Syndrome")).replace(";", ";").split(";") if x.strip()]
        golds = [opts.get(a, a) for a in ans_letters if opts.get(a, a)]
        if not golds:
            continue
        # 标准证型名 -> 计数
        for g in golds:
            per_gold_total[g] = per_gold_total.get(g, 0) + 1

        clinical = str(c.get("Clinical Data") or "")
        results = diagnose(clinical)  # 返回排序结果列表
        preds = [r["证型"] for r in results[:3]]
        if preds:
            covered += 1
        # 匹配: 任一输出证型与任一标准匹配
        if any(_match(p, golds) for p in preds):
            correct += 1
            for g in golds:
                per_gold_correct[g] = per_gold_correct.get(g, 0) + 1
        else:
            missing.setdefault("；".join(golds), []).append((preds, clinical[:60]))

    print(f"\n{'='*52}")
    print(f"TCMEval-SDT 训练集辨证验证")
    print(f"{'='*52}")
    print(f"总病例: {total}")
    print(f"给出诊断(覆盖): {covered} ({covered/total*100:.0f}%)")
    print(f"证型匹配正确: {correct} ({correct/total*100:.0f}%)")
    print(f"匹配率(覆盖中): {correct/covered*100:.0f}%" if covered else "匹配率: N/A")

    # 每标准证型的准确率
    print(f"\n{'='*52}")
    print("每标准证型准确率(样本≥2):")
    rows = []
    for g, tot in per_gold_total.items():
        if tot >= 2:
            cor = per_gold_correct.get(g, 0)
            rows.append((g, cor, tot, cor/tot*100))
    rows.sort(key=lambda x: x[3])
    for g, cor, tot, pct in rows[:20]:
        flag = "⚠️" if pct < 70 else "✅"
        print(f"  {flag} {g}: {cor}/{tot} ({pct:.0f}%)")

    print(f"\n{'='*52}")
    print("完全未匹配(待补充)的标准证型, 前15个:")
    for gold, cases in list(missing.items())[:15]:
        sample_preds = cases[0][0] if cases[0][0] else "(无诊断)"
        print(f"  ✗ 标准[{gold}] -> 输出{sample_preds}")

if __name__ == "__main__":
    main()
