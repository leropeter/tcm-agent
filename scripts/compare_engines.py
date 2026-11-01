# -*- coding: utf-8 -*-
"""compare_engines.py — 对拍：JS 静态版 vs Python 版，Top1 与得分是否一致。

用法: python scripts/compare_engines.py
前提: 先跑 node scripts/js_engine_eval.cjs
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from src.agent import diagnose  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

js = json.load(open(os.path.join(ROOT, "docs", "_js_eval.json"), encoding="utf-8"))
cases = json.load(open(os.path.join(ROOT, "eval", "cases_oral.json"), encoding="utf-8"))["cases"]

by_id = {c["id"]: c for c in cases}
diff = []
for row in js:
    py = diagnose(row["input"])
    py_top = py[0]["证型"] if py else None
    py_score = py[0]["得分"] if py else 0

    if py_top != row["top"] or py_score != row["score"]:
        diff.append({
            "id": row["id"],
            "input": by_id[row["id"]]["input"],
            "py": (py_top, py_score),
            "js": (row["top"], row["score"]),
        })

total = len(js)
same = total - len(diff)
print(f"用例 {total} 条 | 完全一致 {same} | 不一致 {len(diff)} | 一致率 {same / total * 100:.1f}%")

if diff:
    print("\n不一致明细：")
    for d in diff[:20]:
        print(f"  #{d['id']} {d['input']}")
        print(f"     Python: {d['py'][0]} / {d['py'][1]} 分")
        print(f"     JS    : {d['js'][0]} / {d['js'][1]} 分")
    if len(diff) > 20:
        print(f"  ...另有 {len(diff) - 20} 条")

sys.exit(0 if not diff else 1)
