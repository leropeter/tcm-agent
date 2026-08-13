# -*- coding: utf-8 -*-
"""test_data_lib.py — 穴位定位库 + 食疗方库自检"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src import acupoints, recipes

P = F = 0
def ck(name, cond):
    global P, F
    if cond: P += 1; print(f"  ✅ {name}")
    else: F += 1; print(f"  ❌ {name}")

print(f"== 穴位定位库（{len(acupoints.ACUPOINTS)} 穴）==")
ck("穴位字段齐全(定位/方法)", all(all(k in v for k in ["定位","方法"]) for v in acupoints.ACUPOINTS.values()))
ck("定位/方法非空", all(v["定位"] and v["方法"] for v in acupoints.ACUPOINTS.values()))
# 项目实际用到的穴位是否都有
project_points = ["足三里","涌泉","神门","内关","合谷","太冲","三阴交","血海","阴陵泉","丰隆",
                  "风池","大椎","曲池","肾俞","命门","关元","气海","中脘","天枢","太溪","照海",
                  "委中","尺泽","列缺","肺俞","心俞","脾俞","肝俞","膻中","期门","少府","劳宫",
                  "百会","四白","睛明","攒竹","安眠"]
missing = [p for p in project_points if p not in acupoints.ACUPOINTS]
ck(f"项目用到的穴位全在库（缺={missing}）", not missing)
ck("expand 能把穴位替换为带定位文本", "定位" in acupoints.expand("按揉足三里"))

print(f"== 食疗方库（{sum(len(v) for v in recipes.RECIPES.values())} 方 / {len(recipes.RECIPES)} 病症）==")
ck("每方含 名称/用料/做法", all(all(k in f for k in ["名称","用料","做法"]) for v in recipes.RECIPES.values() for f in v))
ck("用料/做法非空", all(f["用料"] and f["做法"] for v in recipes.RECIPES.values() for f in v))
def find_topic(text):
    r = recipes.find([text])
    return r[0]["病症"] if r else None
ck("失眠→匹配失眠方", find_topic("最近失眠") == "失眠")
ck("便秘→匹配便秘方", find_topic("便秘") == "便秘")
ck("风寒感冒→匹配", find_topic("怕冷 流清涕") == "感冒（风寒）")
ck("未匹配返回空", recipes.find(["量子"]) == [])

print(f"\n总计: {P} 通过 / {F} 失败")
sys.exit(1 if F else 0)
