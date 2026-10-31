# -*- coding: utf-8 -*-
"""对比同一句症状在不同人设下的建议差异（验证"根据不同情况给不同建议"）

用法: python scripts/show_advice_diff.py
"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.agent import diagnose
from src.advice import build_plan, render_text

SYM = ["吃不下饭", "人也没劲", "大便稀"]

PROFILES = [
    ("20岁男·无线索", {"男性": True, "年轻": True}),
    ("45岁女·夜班熬夜", {"女性": True, "中老年": True, "熬夜": True, "思虑多": True}),
    ("孕期女性", {"女性": True, "孕期": True}),
    ("夏季·吃生冷", {"男性": True, "吃生冷": True}),
]

print("=" * 74)
print("同一句症状：「吃不下饭，人也没劲，大便稀」")
print("=" * 74)
base = diagnose(SYM, PROFILES[0][1])
print(f"证型 TOP1 = {base[0]['证型']}（固定建议 4 条：饮食/茶饮/穴位/生活）\n")
print(f"{'人设':26}{'证型':10}{'差异化行数':>10}{'字数':>8}")
print("-" * 74)
plans = {}
for name, hints in PROFILES:
    r = diagnose(SYM, hints)
    t = render_text(build_plan(r, hints, SYM))
    plans[name] = t
    lines = [x for x in t.splitlines() if x.strip()]
    print(f"{name:26}{r[0]['证型']:10}{len(lines):>10}{len(t):>8}")

print("\n" + "=" * 74)
print("差异对照（只列各自独有的行）")
print("=" * 74)
cases = list(plans.items())
for i in range(len(cases)):
    for j in range(i + 1, len(cases)):
        n1, t1 = cases[i]
        n2, t2 = cases[j]
        only1 = [x for x in t1.splitlines() if x.strip() and x not in t2]
        only2 = [x for x in t2.splitlines() if x.strip() and x not in t1]
        same = len([x for x in t1.splitlines() if x.strip() and x in t2])
        print(f"\n【{n1}】 vs 【{n2}】  共同 {same} 行 / 各独有 {len(only1)} 与 {len(only2)} 行")
        if only1:
            print(f"  仅 {n1}: {only1[0][:70]}")
        if only2:
            print(f"  仅 {n2}: {only2[0][:70]}")

print("\n" + "=" * 74)
print("完整输出示例：45岁女·夜班熬夜")
print("=" * 74)
print(plans["45岁女·夜班熬夜"])
