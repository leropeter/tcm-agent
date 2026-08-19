# -*- coding: utf-8 -*-
"""test_constitution.py — 体质识别自检"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.constitution import assess, best_constitution, CONSTITUTIONS

P = F = 0
def ck(name, cond):
    global P, F
    if cond: P += 1; print(f"  ✅ {name}")
    else: F += 1; print(f"  ❌ {name}")

print("== 九种体质定义 ==")
ck("包含9种体质", len(CONSTITUTIONS) == 9)
names = [c["name"] for c in CONSTITUTIONS]
for n in ["气虚质","阳虚质","阴虚质","痰湿质","湿热质","血瘀质","气郁质","特禀质","平和质"]:
    ck(f"含{n}", n in names)

print("== 识别功能 ==")
ck("怕冷→阳虚质", "阳虚质" in [c["name"] for c in assess(["怕冷","手脚冰凉"])])
ck("乏力→气虚质", "气虚质" in [c["name"] for c in assess(["乏力","气短","自汗"])])
ck("口苦+舌苔黄腻→湿热质", "湿热质" in [c["name"] for c in assess(["口苦","舌苔黄腻","小便黄"])])
ck("口干+失眠→阴虚质", "阴虚质" in [c["name"] for c in assess(["口干","五心烦热","盗汗"])])
ck("情绪抑郁→气郁质", "气郁质" in [c["name"] for c in assess(["情绪抑郁","胸胁胀满"])])
ck("空列表→无结果", assess([]) == [])
ck("无命中→空", assess(["头痛"]) == [])
ck("best: 怕冷→阳虚质", best_constitution(["怕冷","手脚冰凉","夜尿多"]) == "阳虚质")
ck("每个体质有 advice", all(c.get("advice") for c in CONSTITUTIONS))

print(f"\n总计: {P} 通过 / {F} 失败")
sys.exit(1 if F else 0)
