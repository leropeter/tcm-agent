# -*- coding: utf-8 -*-
"""test_knowledge.py — 知识库与辨证引擎自检
用法: python tests/test_knowledge.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.knowledge import TCM_SYNDROMES
from src.agent import diagnose, parse_symptoms, pretty_report

PASS = FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else: FAIL += 1; print(f"  ❌ {name}")

print(f"== 证型完整性（共 {len(TCM_SYNDROMES)} 个）==")
ids = [s["id"] for s in TCM_SYNDROMES]
check("无重复ID", len(ids) == len(set(ids)))
check("字段齐全", all(all(k in s for k in ["id","category","symptoms","evidence","advice","image"]) for s in TCM_SYNDROMES))
check("每个证型症状非空", all(s["symptoms"] for s in TCM_SYNDROMES))

print("== 每个证型能自命中（用其最高权症状）==")
fail = []
for s in TCM_SYNDROMES:
    top = max(s["symptoms"].items(), key=lambda x: x[1])[0]
    r = diagnose([top])
    if not r or r[0]["证型"] != s["id"]:
        fail.append((s["id"], top, r[0]["证型"] if r else None))
check(f"自命中全部通过 {len(TCM_SYNDROMES)-len(fail)}/{len(TCM_SYNDROMES)}", not fail)
for f in fail: print("     未命中:", f)

print("== 高风险共享症状（权重>=4 被多个证型用）==")
from collections import Counter
use = Counter()
for s in TCM_SYNDROMES:
    for kw, w in s["symptoms"].items():
        if w >= 4: use[kw] += 1
check("无共享高权症状", all(c < 2 for c in use.values()))

print("== 鉴别测试（易混淆证型对）==")
tests = [
    ("发热重 咽喉肿痛 流黄涕", "风热犯表"),
    ("咳嗽 痰黄稠 咽痛", "风热犯肺"),
    ("咳嗽 痰白清稀 流清涕 恶寒", "风寒束肺"),
    ("腰膝酸软 畏寒肢冷 夜尿多", "肾阳虚"),
    ("小便频数 滑精早泄 耳鸣", "肾气虚"),
    ("盗汗 潮热 颧红", "阴虚火旺"),
    ("头晕耳鸣 潮热盗汗 遗精", "肾阴虚"),
    ("干咳无痰 口燥咽干", "肺阴虚"),
    ("心胸刺痛 唇舌紫暗", "心血瘀阻"),
    ("胸胁胀痛 刺痛 情志不畅加重", "气滞血瘀"),
    ("头晕胀痛 头重脚轻 腰膝酸软", "肝阳上亢"),
    ("头痛眩晕 急躁易怒 口苦", "肝火上炎"),
    ("反复感冒 自汗 气短", "气虚感冒"),
    ("神疲乏力 少气懒言", "气虚"),
    ("面色淡白 头晕眼花", "血虚"),
    ("乏力 气短 面色苍白", "气血两虚"),
    ("食少 便溏 食欲不振", "脾气虚"),
    ("心烦 口舌生疮 舌尖红", "心火亢盛"),
    ("心悸怔忡 畏寒肢冷 胸闷气短", "心阳虚"),
    ("身重困倦 头重如裹 舌苔白腻 大便溏泄", "寒湿困脾"),
]
ok = 0
for sym, exp in tests:
    r = diagnose(sym)
    got = r[0]["证型"] if r else None
    mark = "✅" if got == exp else "❌"
    if got == exp: ok += 1
    print(f"  {mark} {sym} -> {got} (期望 {exp})")
check(f"鉴别测试 {ok}/{len(tests)}", ok == len(tests))

print("== 边界情况 ==")
check("无匹配返回空", diagnose(["左脚麻"]) == [])
check("空输入返回空", diagnose([]) == [])
check("症状去重", parse_symptoms("头痛 怕冷，怕冷 无汗") == ["头痛","怕冷","无汗"])
check("pretty_report 输出证型", "风寒" in pretty_report("头痛 怕冷 流清涕"))

print("== 因人制宜（问诊线索加权）==")
def top_with_hint(sym, hints):
    r = diagnose(sym, hints)
    return r[0]["证型"] if r else None, (r[0]["得分"] if r else 0)

# 同一症状，不同人群得分应变化（加权生效）
base_score = diagnose(["口苦","烦躁","易怒"])[0]["得分"]
boosted = diagnose(["口苦","烦躁","易怒"], {"年轻":True,"熬夜":True,"吃辛辣":True})[0]["得分"]
check("问诊线索使得分上升", boosted > base_score)
# 女性经期失眠 → 血虚类应靠前（心血虚提升）
r = diagnose(["失眠","多梦"], {"女性":True,"经期":True})
check("女性经期失眠→心血虚靠前", r[0]["证型"] == "心血虚")
# 无问诊信息时行为不变
check("无hints行为不变", diagnose(["口苦","烦躁","易怒"])[0]["证型"] == "肝郁气滞")

print(f"\n总计: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
